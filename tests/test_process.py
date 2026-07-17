"""Tests for process_metadata_file, process_data_file, process_data."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import fcall
from fcall._process import (
    _expand_multi_cols,
    get_codes_dict,
    process_data,
    process_data_file,
    process_metadata_file,
    read_data_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# process_metadata_file
# ---------------------------------------------------------------------------


class TestProcessMetadataFile:
    def test_single_scenario(self, single_dir: Path) -> None:
        meta = process_metadata_file(single_dir / "D_SINGLETEST.TXT")
        assert meta["scenario"] == "single"
        vi = meta["vars_info"]
        assert list(vi["ColumnName"]) == ["UNINUM", "NAME", "STATE"]
        assert list(vi["ColumnType"]) == ["Numeric", "Alphanum.", "Alphanum."]
        assert list(vi["MultipleOccurrenceColumn"]) == [False, False, False]
        assert list(vi["CodeColumn"]) == [False, False, False]
        assert list(vi["ColumnTypeSQL"]) == ["integer", "text", "text"]

    def test_single_multiple_scenario(self, single_multiple_dir: Path) -> None:
        meta = process_metadata_file(single_multiple_dir / "D_SMTEST.TXT")
        assert meta["scenario"] == "single_multiple"
        vi = meta["vars_info"]
        assert list(vi["ColumnName"]) == ["UNINUM", "REPDATE", "INV_CODE", "AMOUNT"]
        multi = list(vi["MultipleOccurrenceColumn"])
        assert multi == [False, False, True, True]
        code_col = list(vi["CodeColumn"])
        # Only the first multi-occurrence column gets CodeColumn=True
        assert code_col == [False, False, True, False]

    def test_single_multiple_single_scenario(
        self, single_multiple_single_dir: Path
    ) -> None:
        meta = process_metadata_file(single_multiple_single_dir / "D_SMSTEST.TXT")
        assert meta["scenario"] == "single_multiple_single"
        vi = meta["vars_info"]
        assert list(vi["ColumnName"]) == [
            "UNINUM",
            "REPDATE",
            "CAP_CODE",
            "AMOUNT",
            "TOTAL",
        ]
        multi = list(vi["MultipleOccurrenceColumn"])
        assert multi == [False, False, True, True, False]

    def test_decimal_position_integer(self, single_dir: Path) -> None:
        meta = process_metadata_file(single_dir / "D_SINGLETEST.TXT")
        vi = meta["vars_info"]
        assert vi["DecimalPosition"].dtype == pl.Int64

    def test_vars_info_columns(self, single_dir: Path) -> None:
        meta = process_metadata_file(single_dir / "D_SINGLETEST.TXT")
        expected_cols = {
            "ColumnName",
            "ColumnType",
            "DecimalPosition",
            "Definition",
            "MultipleOccurrenceColumn",
            "CodeColumn",
            "ColumnTypeSQL",
        }
        assert set(meta["vars_info"].columns) == expected_cols


# ---------------------------------------------------------------------------
# process_data_file
# ---------------------------------------------------------------------------


@pytest.fixture
def two_code_dict() -> pl.DataFrame:
    return pl.DataFrame({"code": [10, 15], "value": ["Code A", "Code B"]})


class TestProcessDataFile:
    def test_single(self, single_dir: Path) -> None:
        meta = process_metadata_file(single_dir / "D_SINGLETEST.TXT")
        df = process_data_file(single_dir / "SINGLETEST_Q202312_G20240115.TXT", meta)
        assert df.columns == ["UNINUM", "NAME", "STATE"]
        assert df.height == 2
        assert df["UNINUM"].to_list() == [12345, 23456]
        assert df["STATE"].to_list() == ["CA", "TX"]

    def test_single_multiple(
        self, single_multiple_dir: Path, two_code_dict: pl.DataFrame
    ) -> None:
        meta = process_metadata_file(single_multiple_dir / "D_SMTEST.TXT")
        df = process_data_file(
            single_multiple_dir / "SMTEST_Q202312_G20240115.TXT",
            meta,
            two_code_dict,
        )
        # After pivot: 2 institutions x 2 codes = 4 rows
        assert df.height == 4
        assert set(df.columns) == {"UNINUM", "REPDATE", "INV_CODE", "AMOUNT"}
        # Each institution should appear twice (once per code)
        assert sorted(df["UNINUM"].cast(pl.Int64).to_list()) == [
            12345,
            12345,
            23456,
            23456,
        ]

    def test_single_multiple_single(
        self, single_multiple_single_dir: Path, two_code_dict: pl.DataFrame
    ) -> None:
        meta = process_metadata_file(single_multiple_single_dir / "D_SMSTEST.TXT")
        df = process_data_file(
            single_multiple_single_dir / "SMSTEST_Q202312_G20240115.TXT",
            meta,
            two_code_dict,
        )
        # 2 institutions x 2 codes = 4 rows
        assert df.height == 4
        assert set(df.columns) == {"UNINUM", "REPDATE", "CAP_CODE", "AMOUNT", "TOTAL"}

    def test_single_multiple_single_values(
        self, single_multiple_single_dir: Path, two_code_dict: pl.DataFrame
    ) -> None:
        meta = process_metadata_file(single_multiple_single_dir / "D_SMSTEST.TXT")
        df = process_data_file(
            single_multiple_single_dir / "SMSTEST_Q202312_G20240115.TXT",
            meta,
            two_code_dict,
        )
        df = df.sort(["UNINUM", "CAP_CODE"])
        uninum = df["UNINUM"].cast(pl.Int64).to_list()
        cap_code = df["CAP_CODE"].cast(pl.Int64).to_list()
        assert uninum == [12345, 12345, 23456, 23456]
        assert cap_code == [10, 20, 30, 40]

    def test_missing_codes_dict_raises(self, single_multiple_dir: Path) -> None:
        meta = process_metadata_file(single_multiple_dir / "D_SMTEST.TXT")
        with pytest.raises(ValueError, match="`codes_dict` is required"):
            process_data_file(
                single_multiple_dir / "SMTEST_Q202312_G20240115.TXT", meta
            )


# ---------------------------------------------------------------------------
# read_data_file
# ---------------------------------------------------------------------------


class TestReadDataFile:
    def test_missing_codes_dict_raises(
        self, single_multiple_single_dir: Path
    ) -> None:
        meta = process_metadata_file(single_multiple_single_dir / "D_SMSTEST.TXT")
        with pytest.raises(ValueError, match="`codes_dict` is required"):
            read_data_file(
                single_multiple_single_dir / "SMSTEST_Q202312_G20240115.TXT",
                meta,
                None,
            )


# ---------------------------------------------------------------------------
# process_data (integrated)
# ---------------------------------------------------------------------------


class TestProcessData:
    def test_returns_correct_keys(self, single_dir: Path) -> None:
        result = process_data(single_dir)
        assert set(result.keys()) == {"data", "metadata"}

    def test_data_and_metadata_match(self, single_dir: Path) -> None:
        result = process_data(single_dir)
        assert set(result["data"].keys()) == set(result["metadata"].keys())

    def test_data_frames_not_empty(self, single_dir: Path) -> None:
        result = process_data(single_dir)
        for df in result["data"].values():
            assert df.height >= 1

    def test_metadata_has_correct_structure(self, single_dir: Path) -> None:
        result = process_data(single_dir)
        for meta in result["metadata"].values():
            assert set(meta.keys()) == {"scenario", "vars_info"}
            assert meta["scenario"] in {
                "single",
                "single_multiple",
                "single_multiple_single",
            }

    def test_nonexistent_directory_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            process_data("/nonexistent/path/that/does/not/exist")


# ---------------------------------------------------------------------------
# get_codes_dict
# ---------------------------------------------------------------------------


class TestGetCodesDict:
    def test_known_root(self) -> None:
        result = get_codes_dict("RCB")
        assert result["codes_dict"] is not None
        assert result["codes_varname"] == "INV_CODE"
        df = result["codes_dict"]
        assert set(df.columns) == {"code", "value"}
        assert df.height == 35  # RCB__INV_CODE has 35 entries

    def test_unknown_root_returns_none(self) -> None:
        result = get_codes_dict("NONEXISTENT")
        assert result["codes_dict"] is None
        assert result["codes_varname"] is None

    def test_all_known_roots(self) -> None:
        known = [
            "RCB",
            "RCB2",
            "RCB3",
            "RCF",
            "RCF1",
            "RCI2B",
            "RCI2C",
            "RCI2D",
            "RCO",
            "RCR3",
            "RCR7",
            "RID",
            "RIE1",
        ]
        for root in known:
            r = get_codes_dict(root)
            assert r["codes_dict"] is not None, f"Missing dict for {root}"
            assert r["codes_dict"].height > 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_rle_count_single(self) -> None:
        assert len(pl.Series([False, False, False]).rle()) == 1

    def test_rle_count_two_runs(self) -> None:
        assert len(pl.Series([False, False, True, True]).rle()) == 2

    def test_rle_count_three_runs(self) -> None:
        assert len(pl.Series([False, True, True, False]).rle()) == 3

    def test_expand_multi_cols(self) -> None:
        result = _expand_multi_cols(["A", "B"], 2)
        assert result == ["A__1", "B__1", "A__2", "B__2"]

    def test_expand_multi_cols_single_col(self) -> None:
        result = _expand_multi_cols(["CODE"], 3)
        assert result == ["CODE__1", "CODE__2", "CODE__3"]


# ---------------------------------------------------------------------------
# Public API re-exports
# ---------------------------------------------------------------------------


def test_public_api_importable() -> None:
    assert callable(fcall.download_data)
    assert callable(fcall.process_data)
    assert callable(fcall.compare_metadata)
    assert callable(fcall.process_metadata_file)
    assert callable(fcall.get_codes_dict)
    assert isinstance(fcall.file_metadata, pl.DataFrame)


def test_file_metadata_shape() -> None:
    df = fcall.file_metadata
    assert df.columns == ["file_prefix", "description"]
    assert df.height == 36
