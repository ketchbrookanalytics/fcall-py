# CLAUDE.md

Guidance for working in this repository.

## What this is

`fcall-py` is a **Python re-implementation of the R package
[{fcall}](https://github.com/ketchbrookanalytics/fcall)** by Ketchbrook
Analytics. The goal is feature parity with the R package, published to **PyPI**
as `fcall`, using **Polars** as the data-wrangling engine (the R package uses
the tidyverse: dplyr / tidyr / purrr / stringr).

The package parses Farm Credit Administration ("FCA") Call Report data — a set
of quarterly `.TXT` files — into tidy data frames.

- R source of truth: `ketchbrookanalytics/fcall` (use `gh` to read it).
- Data lives in a public S3 bucket:
  `https://fca-call-report-data.s3.us-east-1.amazonaws.com/raw/`
- FCA's own publication page:
  <https://www.fca.gov/bank-oversight/call-report-data-for-download>

## Development environment

- **uv** for everything (`uv sync`, `uv run pytest`, `uv add <pkg>`).
- **Polars** is the primary data engine — prefer it over pandas. Only reach for
  pandas if a hard requirement appears (none is expected).
- A devcontainer (`.devcontainer/devcontainer.json`) provisions uv (installed
  from Astral's official image via `.devcontainer/Dockerfile`) + Python 3.12,
  plus the **GitHub CLI** (`gh`). The host's `.gitconfig`, `gh` config
  (`~/.config/gh`), and `~/.claude` are bind-mounted in, so git, `gh`, and
  Claude Code credentials carry over — `gh` is ready for reading the R source.
- Lint/format with **ruff**; type-check with **mypy**; test with **pytest**.
- Source layout is `src/fcall/`; tests in `tests/`.

```bash
uv sync --all-extras --dev   # set up
uv run pytest                # test
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy src              # type-check
```

## Public API to port (3 functions)

The R package exports three user-facing functions. Match these signatures
(adapted to Python conventions):

1. **`download_data(year, month, dest, files=None, quiet=False)`**
   Downloads a quarter's `.zip` from S3 and unzips into `dest`.
   - `month` accepts a name (`"September"`) **or** an int (`9`).
   - Valid quarters are months `3, 6, 9, 12`.
   - `files` optionally restricts which members are extracted.
   - Python: use `httpx` to download, `zipfile` (stdlib) to extract.

2. **`process_data(dir)`**
   Reads the downloaded `.TXT` files into tidy frames. Returns a dict:
   `{"data": {root_name: DataFrame, ...}, "metadata": {root_name: {...}, ...}}`.
   - Internally mirrors the R helpers: `process_metadata_file`,
     `process_data_file`, `read_data_file`, `get_codes_dict`.

3. **`compare_metadata(dir1, dir2)`**
   Diffs the metadata (`D_*`) files between two quarters. Returns differences in
   file count/names/order and per-file content diffs.

## How the data is structured (the core of the port)

A quarter's archive contains pairs of files sharing a **root name** (everything
up to the first `_`):

- `D_<ROOT>.TXT` — **metadata**: column names, types, decimal positions,
  definitions (Windows-1252 encoded, free-text-ish layout).
- `<ROOT>_Q<YYYYMM>_G<YYYYMMDD>.TXT` — **data**: raw, header-less,
  comma-separated values.

As of Sep 2025 there are ~72 files = 36 datasets. Match a metadata file to its
data file by the root name (strip `D_` and the `.TXT`). **Caveat:** some `D_`
files (the `RCI2*` family) carry an extra `_<YEAR>` suffix that is *not* present
in the data filename — strip everything after the first `_` of the root when
matching (R does this with `str_replace("^(.*?)_.*$", "\\1")`).

### Metadata parsing (`process_metadata_file`)

The R version does heavy regex munging. Replicate carefully:

1. Read all lines, join with single spaces, **decode `windows-1252` → utf-8**.
2. Replace literal tabs with spaces.
3. Normalize `" numeric "` → `" Numeric "` (one file uses lowercase).
4. Strip a trailing `** NOTE...` block.
5. Collapse `**` + whitespace before a variable name into `**name` (the `**`
   prefix marks a *multiple-occurrence* column).
6. Insert a newline before each token followed by `Numeric` or `Alphanum.`
   (perl regex with lookahead — Python `re` supports this directly).
7. Split into rows; parse 4 columns: `ColumnName`, `ColumnType`,
   `DecimalPosition`, `Definition`.
8. Derive:
   - `MultipleOccurrenceColumn` = name started with `**`
   - `CodeColumn` = the *first* multiple-occurrence column
     (`cumsum(MultipleOccurrenceColumn) == 1`)
   - `ColumnTypeSQL`: `Alphanum.`→`text`, `Numeric`+dec 0→`integer`,
     `Numeric`+dec>0→`float`

The **scenario** is decided by the run-length encoding of the
`MultipleOccurrenceColumn` boolean sequence:
- 1 run → `"single"`
- 2 runs → `"single_multiple"`
- 3 runs → `"single_multiple_single"`

### Data parsing (`process_data_file` / `read_data_file`)

- **`single`**: plain CSV read; assign column names from metadata. (R uses
  `read.csv` defaults for type inference — Polars `read_csv` with schema
  inference is the analog. Decide deliberately whether to honor
  `ColumnTypeSQL` or let Polars infer; the R package effectively *infers*.)
- **`single_multiple`**: CSV read, then **pivot**. The multiple-occurrence
  columns repeat once per code in the dataset's code dictionary. Column names
  are built as `expand.grid(multi_cols, "__1..n_codes")`. Then unpivot the
  multi columns, extract the trailing `__<id>` as a per-row code index, and
  re-pivot so each multi column becomes a single column with one row per
  (entity, code).
- **`single_multiple_single`**: the data file wraps each record across
  `n_codes + 2` physical lines — read line-by-line, collapse every
  `n_codes + 2` lines into one, then CSV-parse. Then the same pivot as above,
  with single columns on *both* sides of the multi block.

Polars mapping for the pivot: `pivot_longer`→`DataFrame.unpivot`,
`pivot_wider`→`DataFrame.pivot`. `str_extract(name, "\\d+$")` → Polars string
expr. The grouping key in R is `UNINUM` (the institution id) plus the other
single-occurrence columns — preserve that.

## Data assets to port

The R package ships internal data (`.rda`). In Python, ship these packaged with
the wheel (e.g. as a `data/` dir of `.csv`/`.parquet`, or as plain Python
dicts/`importlib.resources`). Recreate the contents from the R `data-raw/`
scripts, **not** the binary `.rda`:

- **`file_metadata`** — 36 rows mapping `file_prefix` → `description`
  (from `data-raw/file_metadata.R`).
- **13 code dictionaries** (`<ROOT>__<VARNAME>`), each a `code` → `value`
  lookup, from `data-raw/codes.R`:
  `RCB__INV_CODE`, `RCB2__AssetCodeRCB2`, `RCB3__DebtMaturityCode`,
  `RCF__LOANSTATUS`, `RCF1__LOANSTATUS`, `RCI2B__DerivCode`,
  `RCI2C__ExposureCode`, `RCI2D__DerivRMCode`, `RCO__ASSET_CODE`,
  `RCR3__RegCapCode`, `RCR7__RegCapCode`, `RID__CAP_CODE`, `RIE1__ACLCode`.

`get_codes_dict(root_name)` looks up the dict whose name starts with
`"<root>__"`; the `n_codes` count (number of rows in that dict) drives the
multi-column expansion above. Datasets with no matching dict have no codes.

## Caveats & gotchas

- **2024 FCA data is broken.** FCA's posted 2024 files have a known defect; the
  R package catches processing errors and points users to
  `ketchbrookanalytics/fcall` issue #23. Replicate a clear, similar warning.
- **Encoding is Windows-1252**, not UTF-8. Always decode explicitly when reading
  both metadata and (for `compare_metadata`) raw content. Several code-dictionary
  `value` strings contain mojibake (`?` standing in for `≥`/`≤`/curly quotes)
  carried over from the R source — port them **verbatim** for parity unless we
  deliberately decide to clean them (document the decision either way).
- **URL convention changed in 2015.**
  - `year >= 2015`: `<base>/<year><MonthName>.zip` e.g. `2020March.zip`.
  - `year < 2015`: abbreviated month + year, e.g. `Sept2011.zip`
    (`March→Mar`, `June→Jun`, `September→Sept`, `December→Dec`).
- **`waldo::compare` has no Polars/Python equivalent.** `compare_metadata` will
  need a hand-rolled diff (line-level for content; set/order diff for filenames).
  Keep the returned structure usefully introspectable.
- **PyPI name.** Confirm `fcall` is available on PyPI before first publish; pick
  a fallback (e.g. `fcall-py`) if taken. The import name should stay `fcall`.
- **Don't commit downloaded data** — `.TXT`/`.zip`/`fcadata*/` are gitignored.

## Conventions

- Keep the public API surface identical in spirit to R; translate idioms, not
  line-by-line code.
- Type-hint everything; functions return `polars.DataFrame` / dicts thereof.
- Write tests against small fixture files (a trimmed `D_*`/data pair per
  scenario) rather than hitting the network. Mark any network test accordingly.
- When in doubt about behavior, read the R source with
  `gh api repos/ketchbrookanalytics/fcall/contents/<path> --jq .content | base64 -d`.

## Documentation

We are using [Great Docs](https://posit-dev.github.io/great-docs/) for the package's documentation site, which has AI-friendly documentation [here](https://posit-dev.github.io/great-docs/llms-full.txt).