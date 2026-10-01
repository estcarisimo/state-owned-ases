"""Golden values: any change to the archival data must be deliberate.

``tests/golden/canonical.json`` was generated on 2026-09-30 from the canonical documents
produced by ``tools/migrate_legacy.py`` (legacy commit a4d6136 plus the corrections
listed in CHANGELOG.md 2.0.0). If this test fails, the data changed: update the golden
file only on purpose, and put the old-vs-new comparison in the PR description.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from conftest import CANONICAL_DIR

from state_owned_ases import canonical
from state_owned_ases.manifest import dataset_summary
from state_owned_ases.schema import Dataset

pytestmark = pytest.mark.behavior

GOLDEN = Path(__file__).parent / "golden" / "canonical.json"


def current() -> dict[str, object]:
    return {
        name: {
            "sha256": hashlib.sha256((CANONICAL_DIR / name).read_bytes()).hexdigest(),
            "summary": dataset_summary(dataset),
        }
        for name, dataset in zip(
            canonical.DATASET_FILES, canonical.load_all(CANONICAL_DIR), strict=True
        )
    }


def test_canonical_data_matches_golden() -> None:
    assert current() == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_paper_figures(majority: Dataset, minority: Dataset) -> None:
    """Regression against the IMC 2021 paper (Section 7).

    The paper reports 989 state-owned ASes including 193 of foreign subsidiaries, and
    302 minority state-owned ASes. The repository has 984 and 301: five duplicated rows
    were removed from the majority list in October 2021 (commit 6b8fb8f) and one from
    the minority list in 2026; the foreign-subsidiary count is unchanged.
    """
    assert len(majority.records) == 989 - 5
    assert sum(r.target_cc is not None for r in majority.records) == 193
    assert len(minority.records) == 302 - 1
