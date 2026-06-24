"""Tests for compare_metadata and compare_files_content."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from fcall._compare import compare_files_content, compare_metadata


class TestCompareMetadata:
    def test_same_dir_raises(self, compare_a_dir: Path) -> None:
        with pytest.raises(ValueError, match="identical"):
            compare_metadata(compare_a_dir, compare_a_dir)

    def test_returns_expected_keys(
        self, compare_a_dir: Path, compare_b_dir: Path
    ) -> None:
        result = compare_metadata(compare_a_dir, compare_b_dir)
        assert set(result.keys()) == {"file_differences", "content_differences"}
        fd = result["file_differences"]
        assert set(fd.keys()) == {"only_in_dir1", "only_in_dir2", "order_different"}

    def test_extra_file_detected(
        self, compare_a_dir: Path, compare_b_dir: Path
    ) -> None:
        result = compare_metadata(compare_a_dir, compare_b_dir)
        # compare_a has D_EXTRA.TXT which compare_b does not
        assert "D_EXTRA.TXT" in result["file_differences"]["only_in_dir1"]
        assert result["file_differences"]["only_in_dir2"] == []

    def test_content_differences_detected(
        self, compare_a_dir: Path, compare_b_dir: Path
    ) -> None:
        result = compare_metadata(compare_a_dir, compare_b_dir)
        # D_SINGLETEST.TXT differs between a and b
        assert "D_SINGLETEST.TXT" in result["content_differences"]

    def test_identical_dirs_no_differences(self, compare_a_dir: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "copy"
            shutil.copytree(compare_a_dir, copy)
            result = compare_metadata(compare_a_dir, copy)
        assert result["file_differences"]["only_in_dir1"] == []
        assert result["file_differences"]["only_in_dir2"] == []
        assert result["content_differences"] == {}


class TestCompareFilesContent:
    def test_identical_files_empty_diff(
        self, compare_a_dir: Path, compare_b_dir: Path
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            shutil.copy(compare_a_dir / "D_SINGLETEST.TXT", copy / "D_SINGLETEST.TXT")
            diff = compare_files_content("D_SINGLETEST.TXT", compare_a_dir, copy)
        assert diff == []

    def test_different_files_have_diff(
        self, compare_a_dir: Path, compare_b_dir: Path
    ) -> None:
        diff = compare_files_content("D_SINGLETEST.TXT", compare_a_dir, compare_b_dir)
        assert len(diff) > 0
        # Unified diff format: should contain --- and +++
        assert any(line.startswith("---") for line in diff)
        assert any(line.startswith("+++") for line in diff)
