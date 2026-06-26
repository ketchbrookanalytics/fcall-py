"""Compare FCA Call Report metadata files between two quarters."""

from __future__ import annotations

import difflib
import sys
from pathlib import Path
from typing import Any

_RESET = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"


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

    # Retrieve a list of file names in each directory
    files1 = sorted(f.name for f in dir1.iterdir() if f.is_file())
    files2 = sorted(f.name for f in dir2.iterdir() if f.is_file())

    # Filter the files in each directory to just those that represent the metadata
    meta1 = [f for f in files1 if f.startswith("D_")]
    meta2 = [f for f in files2 if f.startswith("D_")]

    # Define sets for downstream comparison
    set1, set2 = (
        set(meta1),
        set(meta2),
    )  # sets for O(1) membership; lists preserve order

    # Identify difference (in both directions) between the file names in the two
    # directories
    only_in_dir1 = sorted(set1 - set2)
    only_in_dir2 = sorted(set2 - set1)

    # Build shared lists from each dir's own sorted sequence so the order
    # comparison reflects each quarter's actual file ordering, not a merged sort.
    shared = [f for f in meta1 if f in set2]
    shared2_order = [f for f in meta2 if f in set1]
    order_different = shared != shared2_order

    # Create a dictionary of the file differences
    file_differences: dict[str, Any] = {
        "only_in_dir1": only_in_dir1,
        "only_in_dir2": only_in_dir2,
        "order_different": order_different,
    }

    # Compare the *content* of each "matched" file across the two directories and create
    # a dictionary to hold the content differences
    content_differences: dict[str, list[str]] = {}
    for filename in shared:
        diff = compare_files_content(filename, dir1, dir2)
        if diff:  # identical files are omitted from the result
            content_differences[filename] = diff

    # Return both file & content differences
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


def print_diff(lines: list[str], *, color: bool | None = None) -> None:
    """Pretty-print unified-diff lines returned by :func:`compare_files_content`.

    Parameters
    ----------
    lines:
        The list of unified-diff lines returned by :func:`compare_files_content`.
    color:
        Whether to emit ANSI color codes.  Defaults to ``True`` when stdout is
        a TTY, ``False`` otherwise (e.g. when piped to a file).

    Examples
    --------
    Print the diff for a single file::

        lines = fc.compare_files_content("D_RCB.TXT", "q3_2010/", "q3_2025/")
        fc.print_diff(lines)

    Iterate over all content differences from :func:`compare_metadata`::

        diffs = fc.compare_metadata("q3_2010/", "q3_2025/")
        for filename, lines in diffs["content_differences"].items():
            print(filename)
            fc.print_diff(lines)
    """
    use_color = sys.stdout.isatty() if color is None else color

    def _c(code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if use_color else text

    for line in lines:
        if line.startswith("---") or line.startswith("+++"):
            print(_c(_BOLD, line))
        elif line.startswith("@@"):
            print(_c(_CYAN, line))
        elif line.startswith("-"):
            print(_c(_RED, line))
        elif line.startswith("+"):
            print(_c(_GREEN, line))
        else:
            print(line)


# Define an internal helper function for cleaning up Windows-1252 encodings
def _read_meta_lines(path: Path) -> list[str]:
    """Read a metadata file decoded from windows-1252, returning stripped lines."""
    raw = path.read_bytes().decode("windows-1252", errors="replace")
    return raw.splitlines()
