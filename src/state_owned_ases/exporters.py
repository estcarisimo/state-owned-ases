"""Generate every distribution format from a canonical :class:`~state_owned_ases.schema.Dataset`.

All writers are deterministic for a given dependency set: no timestamps, fixed row and
column order, fixed compression levels. Text formats are therefore byte-reproducible;
SQLite and Parquet embed library versions in their headers and are compared logically
instead (see :mod:`state_owned_ases.check`).
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import logging
import sqlite3
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import zstandard

from state_owned_ases.schema import COLUMNS, ASRecord, Dataset

logger = logging.getLogger(__name__)

#: Separator used for the multi-valued ``inputs`` field in flat text formats and SQLite.
INPUTS_SEPARATOR = ";"
ZSTD_LEVEL = 19

Row = dict[str, Any]


def flat_row(record: ASRecord) -> Row:
    """Flatten a record for tabular formats (``inputs`` joined with ``;``).

    Parameters
    ----------
    record
        The record to flatten.

    Returns
    -------
    dict[str, Any]
        Column name to value, in :data:`~state_owned_ases.schema.COLUMNS` order.
    """
    row = record.model_dump(mode="json")
    row["inputs"] = INPUTS_SEPARATOR.join(record.inputs)
    return row


def _delimited(dataset: Dataset, delimiter: str) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerow(COLUMNS)
    for record in dataset.records:
        row = flat_row(record)
        writer.writerow("" if row[column] is None else row[column] for column in COLUMNS)
    return buffer.getvalue().encode("utf-8")


def to_csv(dataset: Dataset) -> bytes:
    """Render the dataset as RFC 4180 CSV (UTF-8, ``\\n`` line endings, empty = null)."""
    return _delimited(dataset, ",")


def to_tsv(dataset: Dataset) -> bytes:
    """Render the dataset as TSV (tab-delimited, CSV quoting rules for embedded tabs)."""
    return _delimited(dataset, "\t")


def _records_json(dataset: Dataset) -> list[Row]:
    return [record.model_dump(mode="json") for record in dataset.records]


def to_json(dataset: Dataset) -> bytes:
    """Render the dataset as a JSON array of records (``inputs`` stays a list)."""
    return (json.dumps(_records_json(dataset), indent=2, ensure_ascii=False) + "\n").encode()


def to_jsonl(dataset: Dataset) -> bytes:
    """Render the dataset as newline-delimited JSON, one record per line."""
    lines = (json.dumps(row, ensure_ascii=False) for row in _records_json(dataset))
    return ("\n".join(lines) + "\n").encode("utf-8")


def gzip_bytes(data: bytes) -> bytes:
    """Compress with gzip, with a zero timestamp and no file name, for reproducibility."""
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=9) as gz:
        gz.write(data)
    return buffer.getvalue()


def zstd_bytes(data: bytes) -> bytes:
    """Compress with Zstandard at :data:`ZSTD_LEVEL`, recording the content size."""
    return zstandard.ZstdCompressor(level=ZSTD_LEVEL, write_content_size=True).compress(data)


def dataset_metadata(dataset: Dataset) -> dict[str, str]:
    """Key/value metadata embedded in Parquet and SQLite exports."""
    return {
        "dataset": dataset.name,
        "title": dataset.title,
        "ownership": dataset.ownership,
        "schema_version": dataset.schema_version,
        "reference_period": "/".join(dataset.reference_period),
        "description": dataset.description,
    }


def arrow_schema(dataset: Dataset) -> pa.Schema:
    """Arrow schema used for Parquet: typed columns, ``inputs`` as ``list<string>``."""
    fields = [
        pa.field(column, pa.int64(), nullable=False)
        if column == "asn"
        else pa.field(column, pa.float64())
        if column == "ownership_percentage"
        else pa.field(column, pa.list_(pa.string()), nullable=False)
        if column == "inputs"
        else pa.field(column, pa.string())
        for column in COLUMNS
    ]
    metadata: dict[bytes | str, bytes | str] = {k: v for k, v in dataset_metadata(dataset).items()}
    return pa.schema(fields, metadata=metadata)


def arrow_table(dataset: Dataset) -> pa.Table:
    """Build the typed Arrow table for ``dataset``."""
    rows = _records_json(dataset)
    columns = {column: [row[column] for row in rows] for column in COLUMNS}
    return pa.Table.from_pydict(columns, schema=arrow_schema(dataset))


def write_parquet(dataset: Dataset, path: Path) -> None:
    """Write a Zstandard-compressed Parquet file with dataset metadata in the schema."""
    pq.write_table(arrow_table(dataset), path, compression="zstd", compression_level=ZSTD_LEVEL)


SQLITE_DDL = """\
CREATE TABLE ases (
    asn INTEGER PRIMARY KEY,
    conglomerate TEXT NOT NULL,
    org_id TEXT NOT NULL,
    org_name TEXT,
    ownership_percentage REAL,
    ownership_cc TEXT NOT NULL,
    ownership_country_name TEXT NOT NULL,
    rir TEXT NOT NULL,
    source TEXT NOT NULL,
    quote TEXT NOT NULL,
    quote_lang TEXT NOT NULL,
    url TEXT NOT NULL,
    additional_info TEXT,
    inputs TEXT NOT NULL,
    parent_org TEXT,
    target_cc TEXT,
    target_country_name TEXT
);
CREATE INDEX ases_org_id ON ases (org_id);
CREATE INDEX ases_ownership_cc ON ases (ownership_cc);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def write_sqlite(dataset: Dataset, path: Path) -> None:
    """Write a SQLite database with an ``ases`` table and a ``metadata`` key/value table.

    ``inputs`` is stored as ``;``-joined text, as in CSV.
    """
    path.unlink(missing_ok=True)
    connection = sqlite3.connect(path)
    try:
        with connection:
            connection.executescript(SQLITE_DDL)
            placeholders = ", ".join("?" for _ in COLUMNS)
            connection.executemany(
                f"INSERT INTO ases ({', '.join(COLUMNS)}) VALUES ({placeholders})",
                ([flat_row(record)[column] for column in COLUMNS] for record in dataset.records),
            )
            connection.executemany(
                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                sorted(dataset_metadata(dataset).items()),
            )
        connection.execute("VACUUM")
    finally:
        connection.close()


@dataclass(frozen=True)
class ExportFormat:
    """One distribution format.

    Attributes
    ----------
    name
        Short format identifier used by the CLI (``--format``).
    suffix
        File suffix appended to the dataset's file stem.
    binary
        ``True`` when the file embeds library versions and is compared logically rather
        than byte-for-byte.
    write
        Callable that writes ``dataset`` to ``path``.
    """

    name: str
    suffix: str
    binary: bool
    write: Callable[[Dataset, Path], None]


def _bytes_writer(render: Callable[[Dataset], bytes]) -> Callable[[Dataset, Path], None]:
    def write(dataset: Dataset, path: Path) -> None:
        path.write_bytes(render(dataset))

    return write


FORMATS: tuple[ExportFormat, ...] = (
    ExportFormat("csv", ".csv", False, _bytes_writer(to_csv)),
    ExportFormat("csv.gz", ".csv.gz", False, _bytes_writer(lambda d: gzip_bytes(to_csv(d)))),
    ExportFormat("csv.zst", ".csv.zst", False, _bytes_writer(lambda d: zstd_bytes(to_csv(d)))),
    ExportFormat("tsv", ".tsv", False, _bytes_writer(to_tsv)),
    ExportFormat("json", ".json", False, _bytes_writer(to_json)),
    ExportFormat("jsonl", ".jsonl", False, _bytes_writer(to_jsonl)),
    ExportFormat("jsonl.gz", ".jsonl.gz", False, _bytes_writer(lambda d: gzip_bytes(to_jsonl(d)))),
    ExportFormat(
        "jsonl.zst", ".jsonl.zst", False, _bytes_writer(lambda d: zstd_bytes(to_jsonl(d)))
    ),
    ExportFormat("parquet", ".parquet", True, write_parquet),
    ExportFormat("sqlite", ".sqlite", True, write_sqlite),
)
FORMAT_NAMES: tuple[str, ...] = tuple(fmt.name for fmt in FORMATS)


def file_stem(dataset: Dataset) -> str:
    """File stem of a dataset's exports, e.g. ``state_owned_ases``."""
    return dataset.name.replace("-", "_")


def export_dataset(
    dataset: Dataset, out_dir: Path, formats: tuple[ExportFormat, ...] = FORMATS
) -> Iterator[tuple[ExportFormat, Path]]:
    """Write ``dataset`` in each format under ``out_dir/<dataset.name>/``.

    Parameters
    ----------
    dataset
        Validated canonical dataset.
    out_dir
        Root export directory.
    formats
        Formats to write; all by default.

    Yields
    ------
    tuple[ExportFormat, Path]
        Each format and the file written for it.
    """
    target = out_dir / dataset.name
    target.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        path = target / f"{file_stem(dataset)}{fmt.suffix}"
        fmt.write(dataset, path)
        logger.info("wrote %s", path)
        yield fmt, path
