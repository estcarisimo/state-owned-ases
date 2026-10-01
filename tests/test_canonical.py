"""The canonical documents are valid, normalized, and serialize deterministically."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import CANONICAL_DIR

from state_owned_ases import canonical
from state_owned_ases.schema import Dataset

pytestmark = pytest.mark.behavior


def test_canonical_files_are_in_canonical_form(datasets: list[Dataset]) -> None:
    for name, dataset in zip(canonical.DATASET_FILES, datasets, strict=True):
        assert (CANONICAL_DIR / name).read_text(encoding="utf-8") == canonical.dumps(dataset)


def test_save_then_load_round_trips(tmp_path: Path, majority: Dataset) -> None:
    path = tmp_path / "nested" / "x.json"
    canonical.save(majority, path)
    assert canonical.load(path) == majority


def test_namibia_country_code_is_not_null(majority: Dataset) -> None:
    namibia = [r for r in majority.records if r.ownership_country_name == "Namibia"]
    assert namibia
    assert {r.ownership_cc for r in namibia} == {"NA"}


def test_one_country_name_per_code(datasets: list[Dataset]) -> None:
    names: dict[str, set[str]] = {}
    for dataset in datasets:
        for r in dataset.records:
            names.setdefault(r.ownership_cc, set()).add(r.ownership_country_name)
            if r.target_cc is not None and r.target_country_name is not None:
                names.setdefault(r.target_cc, set()).add(r.target_country_name)
    assert {cc: n for cc, n in names.items() if len(n) > 1} == {}
