# fcall

<!-- badges: start -->

[![PyPI version](https://img.shields.io/pypi/v/fcall)](https://pypi.org/project/fcall/)
[![PyPI downloads](https://img.shields.io/pypi/dm/fcall)](https://pypi.org/project/fcall/)
[![CI](https://github.com/ketchbrookanalytics/fcall-py/actions/workflows/ci.yaml/badge.svg)](https://github.com/ketchbrookanalytics/fcall-py/actions/workflows/ci.yaml)

<!-- badges: end -->

Python package for parsing Farm Credit Administration ("FCA") Call Report data into [tidy](https://vita.had.co.nz/papers/tidy-data.html) [Polars](https://pola.rs/) DataFrames.

> There is also an equivalent R package {fcall} at <https://github.com/ketchbrookanalytics/fcall>.

## Installation

`fcall` can be installed from PyPI:

```bash
# using pip
pip install fcall

# using uv
uv add fcall
```

Alternatively, install the development version directly from GitHub:

```bash
# using pip
pip install git+https://github.com/ketchbrookanalytics/fcall-py.git

# using uv
uv add git+https://github.com/ketchbrookanalytics/fcall-py.git
```

## Background

FCA publishes Call Report data on a quarterly basis at <https://www.fca.gov/bank-oversight/call-report-data-for-download>. Ketchbrook Analytics replicates these files in a public AWS S3 bucket, which `fcall` interacts with via its `download_data()` function.

As of September 2025, this data represents a set of 72 *.TXT* files. These files represent 36 datasets. The files prefixed with "D\_" contain *metadata* (the column names, data types, etc.) of the associated file containing the raw, header-less comma-separated data. For example, the file that starts with *"D_INST"* contains the metadata for the file that starts with *"INST\_"*.

Further, some of these datasets are structured in a way that makes data analysis difficult. In these cases, we chose to pivot the data to make it more analysis-friendly.

This package provides 3 utility functions:

1. `download_data()` allows users to programmatically download (and unzip) data from a specific quarter
2. `process_data()` parses the data from these unzipped *.TXT* files into a dict of Polars DataFrames containing the Call Report data and file metadata
3. `compare_metadata()` compares two sets of Call Report data from different quarters

## Usage

```python
import fcall as fc

# Download & unzip a quarter into a directory
fc.download_data(
  year = 2025,
  month = "September",
  dest = "./fcadata"
)

# Parse the .TXT files into tidy Polars DataFrames + metadata
result = fc.process_data("./fcadata")
result["data"]["RCB"]      # a polars.DataFrame
result["metadata"]["RCB"]  # parsed schema for RCB

# Compare metadata between two quarters
fc.download_data(
  year = 2022,
  month = "September",
  dest = "./fcadata2"
)
fc.compare_metadata(
  dir1 = "./fcadata",
  dir2 = "./fcadata2"
)
```

## Database

[Ketchbrook Analytics](https://www.ketchbrookanalytics.com/) has also created a PostgreSQL database to store historical FCA Call Report data in a traditional, relational schema that aligns with the output DataFrame structure resulting from running `process_data()`. This database allows users to execute SQL queries to easily analyze Call Report data across multiple quarters.

Please reach out to [info@ketchbrookanalytics.com](mailto:info@ketchbrookanalytics.com?subject=FCA%20Call%20Report%20Database) if you would like access to this database.
