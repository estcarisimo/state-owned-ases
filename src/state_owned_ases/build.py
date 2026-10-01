"""Export all datasets and verify that committed exports are up to date."""

from __future__ import annotations

import json
import logging
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from state_owned_ases import canonical
from state_owned_ases.exporters import (
    FORMATS,
    SQLITE_SELECT,
    ExportFormat,
    arrow_table,
    dataset_metadata,
    export_dataset,
    flat_row,
)
from state_owned_ases.manifest import (
    CHECKSUMS_NAME,
    MANIFEST_NAME,
    build_manifest,
    checksums_text,
    dumps_manifest,
    sha256,
)
from state_owned_ases.schema import COLUMNS, Dataset

logger = logging.getLogger(__name__)


def export_all(
    canonical_dir: Path, out_dir: Path, formats: tuple[ExportFormat, ...] = FORMATS
) -> dict[str, Any]:
    """Validate every canonical dataset and write all exports, the manifest and checksums.

    Parameters
    ----------
    canonical_dir
        Directory with the canonical JSON documents.
    out_dir
        Export root, e.g. ``data/exports``.
    formats
        Formats to write; all by default. The manifest lists only what was written.

    Returns
    -------
    dict[str, Any]
        The manifest that was written.
    """
    paths = [canonical_dir / name for name in canonical.DATASET_FILES]
    datasets = [canonical.load(path) for path in paths]
    exported = [list(export_dataset(dataset, out_dir, formats)) for dataset in datasets]
    manifest = build_manifest(datasets, paths, exported, out_dir)
    (out_dir / MANIFEST_NAME).write_text(dumps_manifest(manifest), encoding="utf-8")
    (out_dir / CHECKSUMS_NAME).write_text(checksums_text(manifest), encoding="utf-8")
    return manifest


def _parquet_matches(dataset: Dataset, path: Path) -> bool:
    table = pq.read_table(path)
    expected = arrow_table(dataset)
    # Compare metadata as dicts: Parquet round-trips can reorder the key/value pairs.
    return (
        table.schema.equals(expected.schema)
        and table.schema.metadata == expected.schema.metadata
        and table.to_pylist() == expected.to_pylist()
    )


def _sqlite_matches(dataset: Dataset, path: Path) -> bool:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = connection.execute(SQLITE_SELECT).fetchall()
        metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
    finally:
        connection.close()
    expected = [tuple(flat_row(record)[c] for c in COLUMNS) for record in dataset.records]
    return rows == expected and metadata == dataset_metadata(dataset)


def _strip_binary_hashes(manifest: dict[str, Any]) -> dict[str, Any]:
    stripped: dict[str, Any] = json.loads(json.dumps(manifest))
    for entry in stripped["datasets"]:
        for item in entry["files"]:
            if item["binary"]:
                item.pop("bytes")
                item.pop("sha256")
    return stripped


def check_exports(canonical_dir: Path, exports_dir: Path) -> list[str]:
    """Compare committed exports with a fresh export of the canonical data.

    Text formats must be byte-identical. Parquet and SQLite embed library versions, so
    they must hold the same schema, rows and metadata. The committed manifest must match
    the regenerated one (ignoring binary file sizes and hashes), and every committed file
    must match the checksum the committed manifest records for it.

    Parameters
    ----------
    canonical_dir
        Directory with the canonical JSON documents.
    exports_dir
        Committed export root.

    Returns
    -------
    list[str]
        Human-readable problems; empty when the exports are up to date.
    """
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        fresh_dir = Path(tmp)
        fresh = export_all(canonical_dir, fresh_dir)
        datasets = {d.name: d for d in canonical.load_all(canonical_dir)}

        expected_files = {MANIFEST_NAME, CHECKSUMS_NAME}
        formats = {fmt.name: fmt for fmt in FORMATS}
        for entry in fresh["datasets"]:
            for item in entry["files"]:
                rel = item["path"]
                expected_files.add(rel)
                committed = exports_dir / rel
                if not committed.is_file():
                    problems.append(f"missing export: {rel}")
                    continue
                dataset = datasets[entry["name"]]
                if item["format"] == "parquet":
                    same = _parquet_matches(dataset, committed)
                elif item["format"] == "sqlite":
                    same = _sqlite_matches(dataset, committed)
                else:
                    same = committed.read_bytes() == (fresh_dir / rel).read_bytes()
                if not same:
                    problems.append(f"stale export ({formats[item['format']].name}): {rel}")

        present = {
            p.relative_to(exports_dir).as_posix() for p in exports_dir.rglob("*") if p.is_file()
        }
        problems += [
            f"unexpected file in exports: {rel}" for rel in sorted(present - expected_files)
        ]

        manifest_path = exports_dir / MANIFEST_NAME
        if not manifest_path.is_file():
            problems.append(f"missing {MANIFEST_NAME}")
            return problems
        committed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _strip_binary_hashes(committed_manifest) != _strip_binary_hashes(fresh):
            problems.append(f"stale {MANIFEST_NAME}: regenerate with `state-owned-ases export`")
        for entry in committed_manifest["datasets"]:
            for item in entry["files"]:
                path = exports_dir / item["path"]
                if path.is_file() and sha256(path) != item["sha256"]:
                    problems.append(f"checksum mismatch: {item['path']}")
        checksums = exports_dir / CHECKSUMS_NAME
        if not checksums.is_file() or checksums.read_text(encoding="utf-8") != checksums_text(
            committed_manifest
        ):
            problems.append(f"{CHECKSUMS_NAME} does not match {MANIFEST_NAME}")
    return problems
