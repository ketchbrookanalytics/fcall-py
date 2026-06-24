"""Network integration tests — require real S3 access.

Run with:  uv run pytest -m network
Skip with: uv run pytest -m 'not network'   (default)
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import fcall
from fcall._process import get_codes_dict

# Quarter to use for integration tests: September 2025 is stable and non-2024.
_YEAR = 2025
_MONTH = 9

# All root names expected in a Sep-2025 archive (36 datasets)
_EXPECTED_ROOTS = {
    "INST", "RC", "RC1",
    "RCB", "RCB2", "RCB3", "RCB4", "RCB5",
    "RCF", "RCF1", "RCG", "RCH",
    "RCI1", "RCI2A", "RCI2B", "RCI2C", "RCI2D",
    "RCK", "RCL", "RCM", "RCO",
    "RCR1", "RCR2", "RCR3", "RCR4", "RCR5", "RCR6", "RCR7",
    "RI", "RIA", "RIB", "RIC", "RIC1", "RID", "RIE1", "RIE2",
}


@pytest.fixture(scope="module")
def downloaded_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Download Sep-2025 data once for all tests in this module."""
    dest = tmp_path_factory.mktemp("fcadata_sep2025")
    fcall.download_data(year=_YEAR, month=_MONTH, dest=dest, quiet=True)
    return dest


@pytest.fixture(scope="module")
def processed(downloaded_dir: Path) -> dict:
    return fcall.process_data(downloaded_dir)


# ---------------------------------------------------------------------------
# download_data
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_download_creates_files(downloaded_dir: Path) -> None:
    files = list(downloaded_dir.iterdir())
    assert len(files) > 0, "No files downloaded"


@pytest.mark.network
def test_download_has_metadata_files(downloaded_dir: Path) -> None:
    meta_files = [f for f in downloaded_dir.iterdir() if f.name.startswith("D_")]
    assert len(meta_files) > 0, "No D_*.TXT metadata files found"


@pytest.mark.network
def test_download_txt_extension(downloaded_dir: Path) -> None:
    txt_files = [f for f in downloaded_dir.iterdir() if f.suffix == ".TXT"]
    assert len(txt_files) > 0


@pytest.mark.network
def test_download_selective_files(tmp_path: Path) -> None:
    """Selective extract: only the INST files."""
    inst_dest = tmp_path / "inst_only"
    inst_dest.mkdir()

    # Get the full listing first to find INST filenames
    full_dest = tmp_path / "full"
    full_dest.mkdir()
    fcall.download_data(year=_YEAR, month=_MONTH, dest=full_dest, quiet=True)

    inst_files = [
        f.name
        for f in full_dest.iterdir()
        if f.name.startswith("INST") or f.name == "D_INST.TXT"
    ]
    assert inst_files, "No INST files found in archive"

    fcall.download_data(
        year=_YEAR, month=_MONTH, dest=inst_dest, files=inst_files, quiet=True
    )
    extracted = [f.name for f in inst_dest.iterdir()]
    assert set(extracted) == set(inst_files)


# ---------------------------------------------------------------------------
# process_data — top-level structure
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_process_returns_data_and_metadata_keys(processed: dict) -> None:
    assert set(processed.keys()) == {"data", "metadata"}


@pytest.mark.network
def test_process_data_metadata_same_keys(processed: dict) -> None:
    assert set(processed["data"].keys()) == set(processed["metadata"].keys())


@pytest.mark.network
def test_process_all_expected_roots_present(processed: dict) -> None:
    actual = set(processed["data"].keys())
    missing = _EXPECTED_ROOTS - actual
    assert not missing, f"Missing datasets: {missing}"


@pytest.mark.network
def test_process_all_data_frames_nonempty(processed: dict) -> None:
    for root, df in processed["data"].items():
        assert isinstance(df, pl.DataFrame), f"{root}: not a DataFrame"
        assert df.height >= 1, f"{root}: empty DataFrame"


@pytest.mark.network
def test_process_all_scenarios_valid(processed: dict) -> None:
    valid = {"single", "single_multiple", "single_multiple_single"}
    for root, meta in processed["metadata"].items():
        assert meta["scenario"] in valid, (
            f"{root}: unknown scenario {meta['scenario']!r}"
        )


@pytest.mark.network
def test_process_metadata_vars_info_nonempty(processed: dict) -> None:
    for root, meta in processed["metadata"].items():
        vi = meta["vars_info"]
        assert isinstance(vi, pl.DataFrame), f"{root}: vars_info not a DataFrame"
        assert vi.height >= 1, f"{root}: vars_info is empty"


# ---------------------------------------------------------------------------
# process_data — per-scenario spot checks
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_inst_single_scenario(processed: dict) -> None:
    """INST is always a 'single' scenario dataset."""
    meta = processed["metadata"]["INST"]
    assert meta["scenario"] == "single"
    df = processed["data"]["INST"]
    assert "UNINUM" in df.columns


@pytest.mark.network
def test_rcb_single_multiple_scenario(processed: dict) -> None:
    """RCB uses a code dict → single_multiple."""
    meta = processed["metadata"]["RCB"]
    assert meta["scenario"] == "single_multiple"
    df = processed["data"]["RCB"]
    assert "UNINUM" in df.columns
    # After pivot there should be one row per institution per code
    assert df.height > 0
    n_codes = get_codes_dict("RCB")["codes_dict"]
    assert n_codes is not None
    # All institutions × codes should produce more rows than institutions
    n_inst = processed["data"]["INST"].height
    assert df.height >= n_inst  # at least as many rows as institutions


@pytest.mark.network
def test_rid_single_multiple_single_scenario(processed: dict) -> None:
    """RID uses a code dict and has trailing single cols → single_multiple_single."""
    meta = processed["metadata"]["RID"]
    assert meta["scenario"] == "single_multiple_single"
    df = processed["data"]["RID"]
    assert "UNINUM" in df.columns
    assert df.height > 0


@pytest.mark.network
def test_uninum_is_integer_in_inst(processed: dict) -> None:
    """UNINUM should be numeric (institution identifier)."""
    inst_df = processed["data"]["INST"]
    # UNINUM should be castable to integer
    try:
        inst_df["UNINUM"].cast(pl.Int64)
    except Exception as e:
        pytest.fail(f"UNINUM is not numeric: {e}")


# ---------------------------------------------------------------------------
# compare_metadata — same quarter has no differences
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_compare_same_quarter_no_diffs(tmp_path: Path) -> None:
    """Two downloads of the same quarter should produce zero differences."""
    dir1 = tmp_path / "q1"
    dir2 = tmp_path / "q2"
    dir1.mkdir()
    dir2.mkdir()

    fcall.download_data(year=_YEAR, month=_MONTH, dest=dir1, quiet=True)
    fcall.download_data(year=_YEAR, month=_MONTH, dest=dir2, quiet=True)

    result = fcall.compare_metadata(dir1, dir2)
    assert result["file_differences"]["only_in_dir1"] == []
    assert result["file_differences"]["only_in_dir2"] == []
    assert result["content_differences"] == {}


@pytest.mark.network
def test_compare_different_years_has_diffs(tmp_path: Path) -> None:
    """Jun-2011 vs Sep-2025 should report file differences (schema changed a lot)."""
    dir_old = tmp_path / "jun2011"
    dir_new = tmp_path / "sep2025"
    dir_old.mkdir()
    dir_new.mkdir()

    fcall.download_data(year=2011, month=6, dest=dir_old, quiet=True)
    fcall.download_data(year=_YEAR, month=_MONTH, dest=dir_new, quiet=True)

    result = fcall.compare_metadata(dir_old, dir_new)
    fd = result["file_differences"]
    assert fd["only_in_dir1"] or fd["only_in_dir2"] or result["content_differences"], (
        "Expected differences between 2011 and 2025 metadata"
    )
