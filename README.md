# fcall (Python)

Python re-implementation of the R package
[**{fcall}**](https://github.com/ketchbrookanalytics/fcall) — tools for parsing
Farm Credit Administration ("FCA") Call Report data into tidy
[Polars](https://pola.rs/) data frames.

> 🚧 **Work in progress.** See [CLAUDE.md](CLAUDE.md) for the porting plan,
> architecture, and caveats.

## Background

FCA publishes Call Report data quarterly at
<https://www.fca.gov/bank-oversight/call-report-data-for-download>. Ketchbrook
Analytics mirrors these files in a public AWS S3 bucket, which this package
downloads from.

## Planned API

```python
import fcall

# Download & unzip a quarter into a directory
fcall.download_data(year=2025, month="September", dest="./fcadata")

# Parse the .TXT files into tidy Polars frames + metadata
result = fcall.process_data("./fcadata")
result["data"]["RCB"]      # a polars.DataFrame
result["metadata"]["RCB"]  # parsed schema for RCB

# Compare metadata between two quarters
fcall.compare_metadata("./fcadata_q1", "./fcadata_q2")
```

## Development

This repo ships a [devcontainer](.devcontainer/devcontainer.json) (uv + Polars).
Open it in VS Code / GitHub Codespaces, or locally:

```bash
uv sync --all-extras --dev
uv run pytest
```
