"""``tools/migrate_legacy.py`` reproduces the canonical documents from git history."""

from __future__ import annotations

import subprocess
import sys

import pytest
from conftest import CANONICAL_DIR, ROOT

from state_owned_ases import canonical

pytestmark = pytest.mark.behavior

sys.path.insert(0, str(ROOT / "tools"))
import migrate_legacy  # noqa: E402


def legacy_ref_available() -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{migrate_legacy.LEGACY_REF}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def test_migration_reproduces_canonical() -> None:
    # CI checks out full history (fetch-depth: 0); fail loudly rather than skip if not.
    assert legacy_ref_available(), "legacy commit missing: fetch full git history"
    for name, filename in zip(migrate_legacy.LEGACY, canonical.DATASET_FILES, strict=True):
        migrated = canonical.dumps(migrate_legacy.migrate(name))
        assert migrated == (CANONICAL_DIR / filename).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("G, E, W, O", ("G", "E", "O", "W")), ("E, E, W, W, O, O", ("E", "O", "W")), ("C", ("C",))],
)
def test_parse_inputs(raw: str, expected: tuple[str, ...]) -> None:
    assert migrate_legacy.parse_inputs(raw) == expected


def test_parse_inputs_rejects_unknown_code() -> None:
    with pytest.raises(ValueError, match="unknown input codes"):
        migrate_legacy.parse_inputs("G, X")
