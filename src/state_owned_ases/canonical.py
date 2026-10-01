"""Read and write the canonical JSON documents in ``data/canonical/``."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from state_owned_ases.schema import Dataset

logger = logging.getLogger(__name__)

#: Canonical file names, in the order datasets are exported and documented.
DATASET_FILES: tuple[str, ...] = (
    "state_owned_ases.json",
    "minority_state_owned_ases.json",
)


def dumps(dataset: Dataset) -> str:
    """Serialize a dataset to the canonical JSON text.

    The output is deterministic: two-space indentation, keys in schema order, non-ASCII
    characters kept as-is, ``null`` for missing values, and a trailing newline.

    Parameters
    ----------
    dataset
        The dataset to serialize.

    Returns
    -------
    str
        Canonical JSON text.
    """
    return json.dumps(dataset.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"


def load(path: Path) -> Dataset:
    """Load and validate one canonical dataset.

    Parameters
    ----------
    path
        Path to a canonical JSON document.

    Returns
    -------
    Dataset
        The validated dataset.

    Raises
    ------
    pydantic.ValidationError
        If the document does not satisfy the schema.
    """
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    dataset = Dataset.model_validate(raw)
    logger.debug("loaded %s: %d records", path, len(dataset.records))
    return dataset


def load_all(directory: Path) -> list[Dataset]:
    """Load every canonical dataset in ``directory``.

    Parameters
    ----------
    directory
        Directory holding the files listed in :data:`DATASET_FILES`.

    Returns
    -------
    list[Dataset]
        Datasets in :data:`DATASET_FILES` order.
    """
    return [load(directory / name) for name in DATASET_FILES]


def save(dataset: Dataset, path: Path) -> None:
    """Write a dataset as canonical JSON.

    Parameters
    ----------
    dataset
        The dataset to write.
    path
        Destination file; parent directories are created.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(dataset), encoding="utf-8")
