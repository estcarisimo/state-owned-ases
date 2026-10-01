"""Machine-readable manifest and checksums for the exported files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from state_owned_ases.exporters import ExportFormat
from state_owned_ases.schema import SCHEMA_VERSION, Dataset

MANIFEST_NAME = "MANIFEST.json"
CHECKSUMS_NAME = "SHA256SUMS"


def sha256(path: Path) -> str:
    """Hex SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dataset_summary(dataset: Dataset) -> dict[str, Any]:
    """Counts that describe a dataset's contents, independent of any file format.

    Parameters
    ----------
    dataset
        The dataset to summarize.

    Returns
    -------
    dict[str, Any]
        Name, ownership, reference period and record, organization, conglomerate and
        country counts.
    """
    records = dataset.records
    return {
        "name": dataset.name,
        "title": dataset.title,
        "ownership": dataset.ownership,
        "reference_period": list(dataset.reference_period),
        "records": len(records),
        "organizations": len({r.org_id for r in records}),
        "conglomerates": len({r.conglomerate for r in records}),
        "ownership_countries": len({r.ownership_cc for r in records}),
        "foreign_subsidiary_ases": sum(r.target_cc is not None for r in records),
    }


def build_manifest(
    datasets: list[Dataset],
    canonical_files: list[Path],
    exported: list[list[tuple[ExportFormat, Path]]],
    root: Path,
) -> dict[str, Any]:
    """Build the manifest describing every exported file.

    Parameters
    ----------
    datasets
        Canonical datasets, in export order.
    canonical_files
        Canonical JSON file of each dataset, used for its checksum.
    exported
        For each dataset, the ``(format, path)`` pairs written by the exporter.
    root
        Export root; file paths in the manifest are relative to it.

    Returns
    -------
    dict[str, Any]
        JSON-serializable manifest. It contains no timestamps, so it only changes when
        the data or the file set changes.
    """
    entries = []
    for dataset, canonical_file, files in zip(datasets, canonical_files, exported, strict=True):
        entry = dataset_summary(dataset)
        entry["canonical"] = {
            "path": f"data/canonical/{canonical_file.name}",
            "sha256": sha256(canonical_file),
        }
        entry["files"] = [
            {
                "path": path.relative_to(root).as_posix(),
                "format": fmt.name,
                "binary": fmt.binary,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for fmt, path in files
        ]
        entries.append(entry)
    return {"schema_version": SCHEMA_VERSION, "datasets": entries}


def dumps_manifest(manifest: dict[str, Any]) -> str:
    """Serialize a manifest deterministically."""
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def checksums_text(manifest: dict[str, Any]) -> str:
    """``sha256sum``-compatible checksum list of every file in the manifest.

    Verify with ``sha256sum -c SHA256SUMS`` from the export directory.
    """
    lines = [
        f"{item['sha256']}  {item['path']}"
        for entry in manifest["datasets"]
        for item in entry["files"]
    ]
    return "\n".join(lines) + "\n"
