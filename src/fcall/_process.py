"""Parse FCA Call Report .TXT files into tidy Polars DataFrames.

Mirrors the R helpers: process_metadata_file, read_data_file,
process_data_file, get_codes_dict, and the top-level process_data.
"""

from __future__ import annotations

import csv
import io
import re
import warnings
from pathlib import Path
from typing import Any

import polars as pl

from fcall._data import _CODE_DICT_REGISTRY, _make_code_df

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_data(dir: str | Path) -> dict[str, Any]:
    """Read a quarter's downloaded .TXT files into tidy Polars DataFrames.

    Parameters
    ----------
    dir:
        Path to a directory containing FCA Call Report .TXT files for one
        quarter (as produced by :func:`download_data`).

    Returns
    -------
    dict with keys ``"data"`` and ``"metadata"``, each a dict keyed by
    dataset root name (e.g. ``"RCB"``).
    """
    dir = Path(dir)
    if not dir.exists():
        raise FileNotFoundError(f'Directory "{dir}" does not exist.')

    try:
        return _process_data_all(dir)
    except Exception as exc:
        warnings.warn(
            f"Error processing data: {exc}\n\n"
            "NOTE: There is an outstanding issue with the 2024 files posted "
            "by FCA. If you are trying to process 2024 data, please refer to "
            "https://github.com/ketchbrookanalytics/fcall-py/issues/1 "
            "for more information and solutions while FCA works on fixing the files.",
            stacklevel=2,
        )
        raise


def process_metadata_file(file: str | Path) -> dict[str, Any]:
    """Parse a metadata (D_*.TXT) file into a scenario + vars_info dict.

    Parameters
    ----------
    file:
        Path to a ``D_<ROOT>.TXT`` metadata file.

    Returns
    -------
    ``{"scenario": str, "vars_info": polars.DataFrame}``
    The scenario is one of ``"single"``, ``"single_multiple"``, or
    ``"single_multiple_single"``.
    """
    raw_bytes = Path(file).read_bytes()
    raw_text = raw_bytes.decode("windows-1252")

    # Join all lines into one string
    lines = raw_text.splitlines()
    raw_text = " ".join(lines)

    # Replace literal tab characters with a space
    raw_text = raw_text.replace("\t", " ")

    # Normalise lowercase "numeric" → "Numeric" (one known file anomaly)
    raw_text = raw_text.replace(" numeric ", " Numeric ")

    # Strip trailing ** NOTE ... block
    raw_text = re.sub(r"\*\*\s+NOTE.*$", "", raw_text)

    # Collapse "** <name>" → "**<name>" (** is a temporary name prefix marker)
    raw_text = re.sub(r"\*\*\s+", "**", raw_text)

    # Insert newline before each variable name followed by a type token
    raw_text = re.sub(
        r"(\*\*)?\b(\w+)(?=(\s+Alphanum\.|\s+Numeric))",
        r"\n\1\2",
        raw_text,
    )

    # The regex above inserts \n before every variable token, so split("\n")[0]
    # is always the header/preamble fragment before the first variable — skip it.
    var_lines = [ln for ln in raw_text.split("\n")[1:] if ln.strip()]

    rows: list[dict[str, Any]] = []
    for ln in var_lines:
        parts = ln.split(None, 3)
        if len(parts) < 3:
            continue
        col_name = parts[0]
        col_type = parts[1]
        dec_pos_str = parts[2] if len(parts) > 2 else "0"
        definition = parts[3].strip() if len(parts) > 3 else ""
        definition = re.sub(r"\s+", " ", definition).strip()

        is_multi = col_name.startswith("**")
        clean_name = col_name.lstrip("*")

        try:
            dec_pos = int(dec_pos_str)
        except ValueError:
            dec_pos = 0

        rows.append(
            {
                "ColumnName": clean_name,
                "ColumnType": col_type,
                "DecimalPosition": dec_pos,
                "Definition": definition,
                "_multi": is_multi,
            }
        )

    multi_flags: list[bool] = [r["_multi"] for r in rows]

    # CodeColumn: True only for the very first ** row — that column identifies
    # which code-dictionary entry each data row belongs to (R: cumsum == 1).
    cumsum = 0
    code_col_flags: list[bool] = []
    for m in multi_flags:
        if m:
            cumsum += 1
        code_col_flags.append(cumsum == 1)

    col_type_sql: list[str | None] = []
    for r in rows:
        ct, dp = r["ColumnType"], r["DecimalPosition"]
        if ct == "Alphanum.":
            col_type_sql.append("text")
        elif ct == "Numeric" and dp == 0:
            col_type_sql.append("integer")
        elif ct == "Numeric" and dp > 0:
            col_type_sql.append("float")
        else:
            col_type_sql.append(None)

    vars_info = pl.DataFrame(
        {
            "ColumnName": [r["ColumnName"] for r in rows],
            "ColumnType": [r["ColumnType"] for r in rows],
            "DecimalPosition": [r["DecimalPosition"] for r in rows],
            "Definition": [r["Definition"] for r in rows],
            "MultipleOccurrenceColumn": multi_flags,
            "CodeColumn": code_col_flags,
            "ColumnTypeSQL": col_type_sql,
        }
    )

    rle_count = len(pl.Series(multi_flags).rle())
    scenario_map = {1: "single", 2: "single_multiple", 3: "single_multiple_single"}
    scenario = scenario_map.get(rle_count)
    if scenario is None:
        raise ValueError(
            f"Unexpected MultipleOccurrenceColumn pattern "
            f"(RLE length {rle_count}) in {file}"
        )

    return {"scenario": scenario, "vars_info": vars_info}


def get_codes_dict(data_name: str) -> dict[str, Any]:
    """Return the codes dictionary for *data_name*, or ``None`` values if none.

    Parameters
    ----------
    data_name:
        Root name of the dataset (e.g. ``"RCB"``).

    Returns
    -------
    ``{"codes_dict": polars.DataFrame | None, "codes_varname": str | None}``
    """
    prefix = f"{data_name}__"
    matched_key = next((k for k in _CODE_DICT_REGISTRY if k.startswith(prefix)), None)

    if matched_key is None:
        return {"codes_dict": None, "codes_varname": None}

    codes_varname = matched_key.split("__", 1)[1]
    return {
        "codes_dict": _make_code_df(_CODE_DICT_REGISTRY[matched_key]),
        "codes_varname": codes_varname,
    }


def process_data_file(
    file: str | Path,
    metadata: dict[str, Any],
    codes_dict: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Read *file* and return a tidy DataFrame using *metadata* and *codes_dict*.

    Parameters
    ----------
    file:
        Path to a ``<ROOT>_Q<YYYYMM>_G<YYYYMMDD>.TXT`` data file.
    metadata:
        Output of :func:`process_metadata_file`.
    codes_dict:
        Code dictionary DataFrame from :func:`get_codes_dict`.
        Pass ``None`` for datasets with no codes.
    """
    data = read_data_file(file, metadata, codes_dict)
    scenario: str = metadata["scenario"]
    vars_info: pl.DataFrame = metadata["vars_info"]

    if scenario == "single":
        col_names = vars_info["ColumnName"].to_list()
        return data.rename(
            {old: new for old, new in zip(data.columns, col_names, strict=True)}
        )

    # --- multi-occurrence scenarios ---
    single_cols: list[str] = vars_info.filter(
        ~pl.col("MultipleOccurrenceColumn")
    )["ColumnName"].to_list()
    multi_cols: list[str] = vars_info.filter(
        pl.col("MultipleOccurrenceColumn")
    )["ColumnName"].to_list()

    assert codes_dict is not None, "codes_dict required for multi-occurrence scenarios"
    n_codes: int = len(codes_dict)
    expanded = _expand_multi_cols(multi_cols, n_codes)

    if scenario == "single_multiple":
        col_names = single_cols + expanded
        data = data.rename(
            {old: new for old, new in zip(data.columns, col_names, strict=True)}
        )

    elif scenario == "single_multiple_single":
        # Annotate vars_info with cumulative sum of CodeColumn to split single blocks
        vi = vars_info.with_columns(
            pl.col("CodeColumn").cast(pl.Int32).cum_sum().alias("__cs")
        )

        leading_single: list[str] = vi.filter(
            ~pl.col("MultipleOccurrenceColumn") & (pl.col("__cs") == 0)
        )["ColumnName"].to_list()
        trailing_single: list[str] = vi.filter(
            ~pl.col("MultipleOccurrenceColumn") & (pl.col("__cs") > 0)
        )["ColumnName"].to_list()
        col_names = leading_single + expanded + trailing_single
        data = data.rename(
            {old: new for old, new in zip(data.columns, col_names, strict=True)}
        )
        single_cols = leading_single + trailing_single

    else:
        raise ValueError(f"Unknown scenario: {scenario!r}")

    # Unpivot expanded cols (e.g. FIELD__1, FIELD__2) → extract the trailing
    # code index as __code_id → strip it from the name → pivot back wide so
    # each unique FIELD becomes one column with one row per (entity, code slot).
    data = (
        data.unpivot(on=expanded, index=single_cols)
        .with_columns(
            pl.col("variable").str.extract(r"(\d+)$").alias("__code_id"),
            pl.col("variable").str.replace(r"__\d+$", "").alias("variable"),
        )
        .pivot(
            on="variable",
            index=[*single_cols, "__code_id"],
            values="value",
            aggregate_function="first",
        )
        .drop("__code_id")  # index used only for alignment; not meaningful after pivot
    )

    return data


def read_data_file(
    file: str | Path,
    metadata: dict[str, Any],
    codes_dict: pl.DataFrame | None,
) -> pl.DataFrame:
    """Low-level reader: returns an unnamed DataFrame matching the raw CSV shape."""
    scenario: str = metadata["scenario"]
    file = Path(file)

    if scenario in ("single", "single_multiple"):
        return pl.scan_csv(
            file,
            has_header=False,
            infer_schema_length=10000,
            encoding="utf8-lossy",
        ).collect()

    # single_multiple_single: each logical record spans n_codes multi-occurrence
    # lines wrapped by 1 leading + 1 trailing single-occurrence line → +2.
    assert codes_dict is not None
    n_codes = len(codes_dict)
    chunk_size = n_codes + 2

    raw = file.read_bytes().decode("windows-1252", errors="replace")
    lines = raw.splitlines()

    collapsed: list[str] = []
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i : i + chunk_size]
        collapsed.append("".join(chunk))

    text = "\n".join(collapsed)
    reader = csv.reader(io.StringIO(text))
    raw_rows = list(reader)

    if not raw_rows:
        return pl.DataFrame()

    n_cols = len(raw_rows[0])
    col_data: list[list[str]] = [[] for _ in range(n_cols)]
    for row in raw_rows:
        for j, val in enumerate(row):
            col_data[j].append(val.strip())

    str_df = pl.DataFrame({f"column_{j}": col_data[j] for j in range(n_cols)})
    cast_exprs = []
    for col in str_df.columns:
        s = str_df[col]
        base_nulls = s.null_count()
        if s.cast(pl.Int64, strict=False).null_count() == base_nulls:
            cast_exprs.append(pl.col(col).cast(pl.Int64, strict=False))
        elif s.cast(pl.Float64, strict=False).null_count() == base_nulls:
            cast_exprs.append(pl.col(col).cast(pl.Float64, strict=False))
        else:
            cast_exprs.append(pl.col(col))
    return str_df.with_columns(cast_exprs)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _process_data_all(dir: Path) -> dict[str, Any]:
    files = [f.name for f in sorted(dir.iterdir()) if f.is_file()]
    metadata_files = [f for f in files if f.startswith("D_")]

    # RCI2* metadata files carry an extra _<YEAR> suffix (e.g. D_RCI2B_2024.TXT)
    # that data filenames omit — strip everything after the first "_" to match.
    data_root_names = [
        re.sub(r"^(.*?)_.*$", r"\1", f.removeprefix("D_").removesuffix(".TXT"))
        for f in metadata_files
    ]

    metadata: dict[str, Any] = {}
    for mf, root in zip(metadata_files, data_root_names, strict=True):
        metadata[root] = process_metadata_file(dir / mf)

    data: dict[str, pl.DataFrame] = {}
    for root, meta in metadata.items():
        data_filename = next(
            (f for f in files if re.match(rf"^{re.escape(root)}_", f)), None
        )
        if data_filename is None:
            continue
        codes = get_codes_dict(root)
        data[root] = process_data_file(dir / data_filename, meta, codes["codes_dict"])

    return {"data": data, "metadata": metadata}


def _expand_multi_cols(multi_cols: list[str], n_codes: int) -> list[str]:
    """Expand like R's expand.grid(multi_cols, paste0('__', 1:n_codes)).

    Result order: for each code index (outer), for each column name (inner).
    E.g. multi_cols=[A, B], n_codes=2 → [A__1, B__1, A__2, B__2].
    """
    return [f"{col}__{i}" for i in range(1, n_codes + 1) for col in multi_cols]


