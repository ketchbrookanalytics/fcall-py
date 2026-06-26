"""Download and unzip FCA Call Report quarterly archives from S3."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx

_BASE_URL = "https://fca-call-report-data.s3.us-east-1.amazonaws.com/raw/"

_VALID_MONTHS = {3, 6, 9, 12}

_ABBREV: dict[str, str] = {
    "March": "Mar",
    "June": "Jun",
    "September": "Sept",
    "December": "Dec",
}

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def download_data(
    year: int,
    month: int | str,
    dest: str | Path,
    files: list[str] | None = None,
    quiet: bool = False,
) -> None:
    """Download a quarter's FCA Call Report archive and unzip into *dest*.

    Parameters
    ----------
    year:
        Four-digit year (e.g. 2025).
    month:
        Month name (e.g. ``"September"``) or integer (e.g. ``9``).
        Valid quarters are 3, 6, 9, 12.
    dest:
        Directory to extract files into (created if it does not exist).
    files:
        Optional list of file names to extract; ``None`` extracts all.
    quiet:
        Suppress progress messages when ``True``.
    """
    if isinstance(year, (list, tuple)) or not isinstance(year, int):
        raise ValueError("You can only specify a single year (integer).")

    month_name = _resolve_month(month)

    url = _build_url(year, month_name)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    if not quiet:
        print(f"Downloading {url} …")

    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()

    # BytesIO avoids writing a temp file to disk before unzipping
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        if files is not None:
            if isinstance(files, str):
                files = [files]
            available = set(zf.namelist())
            missing = [f for f in files if f not in available]
            if missing:
                raise KeyError(
                    f"There is no item named {missing[0]!r} in the archive.  "
                    "Please pass the exact file name(s) you want to download to "
                    "the `files` argument of `download_data()`."
                )
            members = files
        else:
            members = zf.namelist()
        zf.extractall(path=dest, members=members)

    if not quiet:
        print(f"Files successfully downloaded into {dest}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_month(month: int | str) -> str:
    """Return the full month name for *month* (name or 1-12 integer/string)."""
    if isinstance(month, str) and month in MONTH_NAMES:
        idx = MONTH_NAMES.index(month) + 1
        if idx not in _VALID_MONTHS:
            raise ValueError(
                f"`month` must be a valid quarter "
                f"(March, June, September, or December), got {month!r}"
            )
        return month

    # Try interpreting as an integer (handles both "9" and 9)
    try:
        idx = int(month)
    except (ValueError, TypeError):
        raise ValueError(
            f"`month` must be a month name or an integer 1-12, got {month!r}"
        ) from None

    if not (1 <= idx <= 12):
        raise ValueError(f"`month` must be between 1 and 12, got {idx}")

    if idx not in _VALID_MONTHS:
        raise ValueError(f"`month` must be a valid quarter (3, 6, 9, or 12), got {idx}")

    return MONTH_NAMES[idx - 1]


def _build_url(year: int, month_name: str) -> str:
    if year >= 2015:
        return f"{_BASE_URL}{year}{month_name}.zip"
    abbrev = _ABBREV.get(month_name)
    if abbrev is None:
        raise ValueError(
            f"Pre-2015 URL convention only supports quarterly months "
            f"(March/June/September/December), got {month_name!r}"
        )
    return f"{_BASE_URL}{abbrev}{year}.zip"
