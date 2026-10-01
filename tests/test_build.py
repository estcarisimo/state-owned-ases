"""Export, manifest and staleness check."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import zstandard
from conftest import CANONICAL_DIR, EXPORTS_DIR

from state_owned_ases.build import check_exports, export_all
from state_owned_ases.exporters import FORMATS, gzip_bytes, zstd_bytes
from state_owned_ases.manifest import CHECKSUMS_NAME, MANIFEST_NAME

pytestmark = pytest.mark.behavior


@pytest.fixture
def exports(tmp_path: Path) -> Path:
    """A private copy of the committed exports that a test may tamper with."""
    target = tmp_path / "exports"
    shutil.copytree(EXPORTS_DIR, target)
    return target


def test_committed_exports_are_up_to_date() -> None:
    assert check_exports(CANONICAL_DIR, EXPORTS_DIR) == []


def test_export_is_byte_reproducible(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    export_all(CANONICAL_DIR, first)
    export_all(CANONICAL_DIR, second)
    binary = {fmt.suffix for fmt in FORMATS if fmt.binary}
    for path in first.rglob("*"):
        if path.is_file() and not any(path.name.endswith(s) for s in binary):
            assert path.read_bytes() == (second / path.relative_to(first)).read_bytes(), path


def test_check_reports_tampered_text_export(exports: Path) -> None:
    csv = exports / "state-owned-ases" / "state_owned_ases.csv"
    csv.write_text(csv.read_text(encoding="utf-8").replace("Telenor", "Telen0r"), "utf-8")
    problems = check_exports(CANONICAL_DIR, exports)
    assert "stale export (csv): state-owned-ases/state_owned_ases.csv" in problems
    assert "checksum mismatch: state-owned-ases/state_owned_ases.csv" in problems


def test_check_reports_missing_extra_and_stale_manifest(exports: Path) -> None:
    (exports / "minority-state-owned-ases" / "minority_state_owned_ases.parquet").unlink()
    (exports / "notes.txt").write_text("x")
    manifest = json.loads((exports / MANIFEST_NAME).read_text())
    manifest["datasets"][0]["records"] += 1
    (exports / MANIFEST_NAME).write_text(json.dumps(manifest))
    problems = check_exports(CANONICAL_DIR, exports)
    assert "missing export: minority-state-owned-ases/minority_state_owned_ases.parquet" in problems
    assert "unexpected file in exports: notes.txt" in problems
    assert any(p.startswith(f"stale {MANIFEST_NAME}") for p in problems)


def test_check_reports_tampered_checksums(exports: Path) -> None:
    sums = exports / CHECKSUMS_NAME
    sums.write_text(sums.read_text().replace("0", "1", 1))
    assert check_exports(CANONICAL_DIR, exports) == [
        f"{CHECKSUMS_NAME} does not match {MANIFEST_NAME}"
    ]


def test_check_reports_changed_binary_content(exports: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    export_all(CANONICAL_DIR, other)
    swapped = "state-owned-ases/state_owned_ases.sqlite"
    shutil.copy(
        other / "minority-state-owned-ases/minority_state_owned_ases.sqlite", exports / swapped
    )
    assert f"stale export (sqlite): {swapped}" in check_exports(CANONICAL_DIR, exports)


def test_checksums_match_files() -> None:
    lines = (EXPORTS_DIR / CHECKSUMS_NAME).read_text().splitlines()
    assert len(lines) == 2 * len(FORMATS)
    for line in lines:
        digest, rel = line.split("  ")
        assert hashlib.sha256((EXPORTS_DIR / rel).read_bytes()).hexdigest() == digest


def test_compression_is_reproducible() -> None:
    data = b"asn,org_id\n2119,ORG-NA38-RIPE\n" * 50
    assert gzip_bytes(data) == gzip_bytes(data)
    assert gzip.decompress(gzip_bytes(data)) == data
    assert zstandard.ZstdDecompressor().decompress(zstd_bytes(data)) == data
