"""fcall: parse FCA Call Report data into tidy Polars data frames.

Python re-implementation of the R package {fcall}
(https://github.com/ketchbrookanalytics/fcall).

Public API:

- :func:`download_data`    -- download & unzip a quarter's Call Report archive
- :func:`process_data`     -- parse the .TXT files into tidy Polars frames
- :func:`compare_metadata` -- diff metadata files between two quarters
- :func:`print_diff`      -- pretty-print the result of compare_metadata
"""

from fcall._compare import compare_files_content, compare_metadata, print_diff
from fcall._data import file_metadata, get_code_df
from fcall._download import download_data
from fcall._process import (
    get_codes_dict,
    process_data,
    process_data_file,
    process_metadata_file,
    read_data_file,
)

__version__ = "0.1.0"

__all__ = [
    # Core public API
    "download_data",
    "process_data",
    "compare_metadata",
    "print_diff",
    # Lower-level helpers (exported for power users)
    "process_metadata_file",
    "process_data_file",
    "read_data_file",
    "get_codes_dict",
    "compare_files_content",
    # Data assets
    "file_metadata",
    "get_code_df",
]
