"""Smoke tests confirming the package + toolchain are wired up."""

import fcall


def test_version_exposed() -> None:
    assert isinstance(fcall.__version__, str)


def test_polars_importable() -> None:
    import polars as pl

    df = pl.DataFrame({"a": [1, 2, 3]})
    assert df.height == 3
