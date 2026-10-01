"""Shared fixtures: repository paths and the canonical datasets."""

from __future__ import annotations

from pathlib import Path

import pytest

from state_owned_ases import canonical
from state_owned_ases.schema import Dataset

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = ROOT / "data" / "canonical"
EXPORTS_DIR = ROOT / "data" / "exports"


@pytest.fixture(scope="session")
def datasets() -> list[Dataset]:
    """Both canonical datasets, validated."""
    return canonical.load_all(CANONICAL_DIR)


@pytest.fixture(scope="session")
def majority(datasets: list[Dataset]) -> Dataset:
    """The main (majority state-owned) dataset."""
    return datasets[0]


@pytest.fixture(scope="session")
def minority(datasets: list[Dataset]) -> Dataset:
    """The partial minority state-owned dataset."""
    return datasets[1]
