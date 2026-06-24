"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def single_dir() -> Path:
    return FIXTURES / "single"


@pytest.fixture
def single_multiple_dir() -> Path:
    return FIXTURES / "single_multiple"


@pytest.fixture
def single_multiple_single_dir() -> Path:
    return FIXTURES / "single_multiple_single"


@pytest.fixture
def compare_a_dir() -> Path:
    return FIXTURES / "compare_a"


@pytest.fixture
def compare_b_dir() -> Path:
    return FIXTURES / "compare_b"
