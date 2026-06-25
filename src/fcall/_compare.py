"""Compare FCA Call Report metadata files between two quarters."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any


def compare_metadata(dir1: str | Path, dir2: str | Path) -> dict[str, Any]:
    """Diff the metadata (D_*.TXT) files between two quarter directories.

    Parameters
    ----------
    dir1, dir2:
        Paths to directories produced by :func:`download_data`.

    Returns
    -------
    A dict with two keys:

    ``"file_differences"``
        Sub-dict describing count/name/order differences:

        - ``"only_in_dir1"`` - filenames present in *dir1* but not *dir2*
        - ``"only_in_dir2"`` - filenames present in *dir2* but not *dir1*
        - ``"order_different"`` - ``True`` if the shared files appear in a
          different order across the two directories

    ``"content_differences"``
        Dict keyed by filename (shared files only).  Each value is a list of
        unified-diff lines for files that differ; files with identical content
        are omitted.
    """
    dir1, dir2 = Path(dir1), Path(dir2)

    if dir1.resolve() == dir2.resolve():
        raise ValueError("`dir1` and `dir2` are identical; nothing to compare")

    files1 = sorted(f.name for f in dir1.iterdir() if f.is_file())
    files2 = sorted(f.name for f in dir2.iterdir() if f.is_file())

    meta1 = [f for f in files1 if f.startswith("D_")]
    meta2 = [f for f in files2 if f.startswith("D_")]

    set1, set2 = set(meta1), set(meta2)
    only_in_dir1 = sorted(set1 - set2)
    only_in_dir2 = sorted(set2 - set1)

    shared = [f for f in meta1 if f in set2]
    shared2_order = [f for f in meta2 if f in set1]
    order_different = shared != shared2_order

    file_differences: dict[str, Any] = {
        "only_in_dir1": only_in_dir1,
        "only_in_dir2": only_in_dir2,
        "order_different": order_different,
    }

    content_differences: dict[str, list[str]] = {}
    for filename in shared:
        diff = compare_files_content(filename, dir1, dir2)
        if diff:
            content_differences[filename] = diff

    return {
        "file_differences": file_differences,
        "content_differences": content_differences,
    }


def compare_files_content(
    filename: str, dir1: str | Path, dir2: str | Path
) -> list[str]:
    """Return unified-diff lines between *filename* in *dir1* and *dir2*.

    Returns an empty list when the files are identical.
    """
    dir1, dir2 = Path(dir1), Path(dir2)

    content1 = _read_meta_lines(dir1 / filename)
    content2 = _read_meta_lines(dir2 / filename)

    diff = list(
        difflib.unified_diff(
            content1,
            content2,
            fromfile=f"dir1/{filename}",
            tofile=f"dir2/{filename}",
            lineterm="",
        )
    )
    return diff


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _read_meta_lines(path: Path) -> list[str]:
    """Read a metadata file decoded from windows-1252, returning stripped lines."""
    raw = path.read_bytes().decode("windows-1252", errors="replace")
    return raw.splitlines()
