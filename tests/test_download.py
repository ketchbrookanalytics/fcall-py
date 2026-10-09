"""Tests for download_data URL logic (no network calls)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

import fcall
from fcall._download import _build_url, _resolve_month


def _make_zip(*names: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name in names:
            zf.writestr(name, "")
    return buf.getvalue()


def _mock_response(zip_bytes: bytes) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.content = zip_bytes
    resp.raise_for_status = MagicMock()
    return resp


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


class TestDownloadFilesValidation:
    _ZIP = _make_zip("INST_Q202603_G20260401.TXT", "D_INST.TXT")

    def test_bad_file_raises_key_error(self, tmp_path: Path) -> None:
        with (
            patch("httpx.get", return_value=_mock_response(self._ZIP)),
            pytest.raises(KeyError, match="INST"),
        ):
            fcall.download_data(year=2026, month=3, dest=tmp_path, files=["INST"])

    def test_bad_file_message_hints_exact_name(self, tmp_path: Path) -> None:
        with (
            patch("httpx.get", return_value=_mock_response(self._ZIP)),
            pytest.raises(KeyError, match="exact file name"),
        ):
            fcall.download_data(year=2026, month=3, dest=tmp_path, files=["INST"])

    def test_bare_string_treated_as_single_file(self, tmp_path: Path) -> None:
        with (
            patch("httpx.get", return_value=_mock_response(self._ZIP)),
            pytest.raises(KeyError, match="INST"),
        ):
            fcall.download_data(year=2026, month=3, dest=tmp_path, files="INST")

    def test_valid_files_extracts_successfully(self, tmp_path: Path) -> None:
        with patch("httpx.get", return_value=_mock_response(self._ZIP)):
            out = fcall.download_data(
                year=2026, month=3, dest=tmp_path,
                files=["INST_Q202603_G20260401.TXT"], quiet=True,
            )
        assert out is True
        assert [p.name for p in tmp_path.iterdir()] == ["INST_Q202603_G20260401.TXT"]


class TestDownloadFailsGracefully:
    """Download/unzip failures print a message and return False (fcall#47)."""

    _URL = "https://fca-call-report-data.s3.us-east-1.amazonaws.com/raw/2099March.zip"

    def _http_status_error(self, status: int) -> MagicMock:
        request = httpx.Request("GET", self._URL)
        response = httpx.Response(status, request=request)
        resp = MagicMock(spec=httpx.Response)
        resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "boom", request=request, response=response
            )
        )
        return resp

    def test_http_error_returns_false(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("httpx.get", return_value=self._http_status_error(404)):
            out = fcall.download_data(year=2099, month=3, dest=tmp_path, quiet=True)
        assert out is False
        err = capsys.readouterr().err
        assert f"Could not download {self._URL}" in err
        assert "no data for the requested `year` and `month`" in err
        assert list(tmp_path.iterdir()) == []

    def test_connection_error_returns_false(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("httpx.get", side_effect=httpx.ConnectError("no internet")):
            out = fcall.download_data(year=2099, month=3, dest=tmp_path, quiet=True)
        assert out is False
        err = capsys.readouterr().err
        assert "Could not download" in err
        assert "no internet" in err

    def test_bad_zip_returns_false(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("httpx.get", return_value=_mock_response(b"not a zip file")):
            out = fcall.download_data(year=2099, month=3, dest=tmp_path, quiet=True)
        assert out is False
        assert "Could not unzip" in capsys.readouterr().err
        assert list(tmp_path.iterdir()) == []

    def test_invalid_arguments_still_raise(self, tmp_path: Path) -> None:
        with patch("httpx.get") as mock_get:
            with pytest.raises(ValueError, match="between 1 and 12"):
                fcall.download_data(year=2025, month=13, dest=tmp_path)
            with pytest.raises(ValueError, match="single year"):
                fcall.download_data(year="2025", month=9, dest=tmp_path)  # type: ignore[arg-type]
        mock_get.assert_not_called()
