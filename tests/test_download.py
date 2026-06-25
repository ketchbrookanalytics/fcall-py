"""Tests for download_data URL logic (no network calls)."""

from __future__ import annotations

import pytest

from fcall._download import _build_url, _resolve_month


class TestResolveMonth:
    def test_full_name(self) -> None:
        assert _resolve_month("March") == "March"
        assert _resolve_month("September") == "September"
        assert _resolve_month("December") == "December"

    def test_integer(self) -> None:
        assert _resolve_month(3) == "March"
        assert _resolve_month(9) == "September"
        assert _resolve_month(12) == "December"

    def test_string_integer(self) -> None:
        assert _resolve_month("9") == "September"
        assert _resolve_month("12") == "December"

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValueError, match="month name or an integer"):
            _resolve_month("Octember")

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 12"):
            _resolve_month(13)
        with pytest.raises(ValueError, match="between 1 and 12"):
            _resolve_month(0)

    def test_non_quarter_integer_raises(self) -> None:
        with pytest.raises(ValueError, match="valid quarter"):
            _resolve_month(1)
        with pytest.raises(ValueError, match="valid quarter"):
            _resolve_month(7)

    def test_non_quarter_name_raises(self) -> None:
        with pytest.raises(ValueError, match="valid quarter"):
            _resolve_month("January")
        with pytest.raises(ValueError, match="valid quarter"):
            _resolve_month("July")


class TestBuildUrl:
    BASE = "https://fca-call-report-data.s3.us-east-1.amazonaws.com/raw/"

    def test_post_2015_url(self) -> None:
        url = _build_url(2020, "March")
        assert url == f"{self.BASE}2020March.zip"

    def test_post_2015_september(self) -> None:
        url = _build_url(2025, "September")
        assert url == f"{self.BASE}2025September.zip"

    def test_pre_2015_march(self) -> None:
        url = _build_url(2011, "September")
        assert url == f"{self.BASE}Sept2011.zip"

    def test_pre_2015_march_abbrev(self) -> None:
        url = _build_url(2014, "March")
        assert url == f"{self.BASE}Mar2014.zip"

    def test_pre_2015_december(self) -> None:
        url = _build_url(2012, "December")
        assert url == f"{self.BASE}Dec2012.zip"

    def test_boundary_2015(self) -> None:
        url = _build_url(2015, "March")
        assert url == f"{self.BASE}2015March.zip"

    def test_pre_2015_non_quarterly_raises(self) -> None:
        with pytest.raises(ValueError, match="only supports quarterly months"):
            _build_url(2010, "January")
