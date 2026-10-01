"""Every committed export holds exactly the canonical records.

Each format is read back with an independent reader (pandas, DuckDB, the standard
library) rather than with this package's own code, and compared with the canonical
JSON document.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pytest
import zstandard
from conftest import EXPORTS_DIR

from state_owned_ases.exporters import FORMAT_NAMES
from state_owned_ases.schema import COLUMNS, Dataset

pytestmark = pytest.mark.math


def expected_rows(dataset: Dataset) -> list[dict[str, Any]]:
    """Canonical records as plain dicts, ``inputs`` as a list."""
    return [r.model_dump(mode="json") for r in dataset.records]


def from_flat(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Normalize a flat (CSV/TSV/SQLite) frame back to canonical dicts."""
    frame = frame.astype(object).where(frame.notna(), None)
    rows = [{str(k): v for k, v in row.items()} for row in frame.to_dict(orient="records")]
    for row in rows:
        row["asn"] = int(row["asn"])
        row["inputs"] = row["inputs"].split(";")
        if row["ownership_percentage"] is not None:
            row["ownership_percentage"] = float(row["ownership_percentage"])
    return rows


def path_of(dataset: Dataset, suffix: str) -> Path:
    return EXPORTS_DIR / dataset.name / f"{dataset.name.replace('-', '_')}{suffix}"


# keep_default_na=False: "NA" is Namibia's country code, not a missing value.
CSV_KW: dict[str, Any] = {"dtype": str, "keep_default_na": False, "na_values": [""]}


@pytest.mark.parametrize(("suffix", "sep"), [(".csv", ","), (".tsv", "\t")])
def test_delimited(datasets: list[Dataset], suffix: str, sep: str) -> None:
    for dataset in datasets:
        frame = pd.read_csv(path_of(dataset, suffix), sep=sep, **CSV_KW)
        assert tuple(frame.columns) == COLUMNS
        assert from_flat(frame) == expected_rows(dataset)


@pytest.mark.parametrize("suffix", [".csv.gz", ".csv.zst"])
def test_compressed_csv(datasets: list[Dataset], suffix: str) -> None:
    for dataset in datasets:
        frame = pd.read_csv(path_of(dataset, suffix), **CSV_KW)
        assert from_flat(frame) == expected_rows(dataset)


def test_json_array(datasets: list[Dataset]) -> None:
    for dataset in datasets:
        rows = json.loads(path_of(dataset, ".json").read_text(encoding="utf-8"))
        assert rows == expected_rows(dataset)


@pytest.mark.parametrize("suffix", [".jsonl", ".jsonl.gz", ".jsonl.zst"])
def test_json_lines(datasets: list[Dataset], suffix: str) -> None:
    for dataset in datasets:
        raw = path_of(dataset, suffix).read_bytes()
        if suffix.endswith(".gz"):
            raw = gzip.decompress(raw)
        elif suffix.endswith(".zst"):
            raw = zstandard.ZstdDecompressor().decompress(raw)
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        assert rows == expected_rows(dataset)


def test_parquet_with_duckdb(datasets: list[Dataset]) -> None:
    for dataset in datasets:
        path = path_of(dataset, ".parquet")
        result = duckdb.sql(f"SELECT * FROM read_parquet('{path}') ORDER BY asn")
        assert tuple(result.columns) == COLUMNS
        rows = [dict(zip(COLUMNS, row, strict=True)) for row in result.fetchall()]
        assert rows == expected_rows(dataset)


def test_parquet_with_pandas(datasets: list[Dataset]) -> None:
    for dataset in datasets:
        frame = pd.read_parquet(path_of(dataset, ".parquet"))
        assert frame["asn"].dtype == "int64"
        assert frame["asn"].tolist() == [r.asn for r in dataset.records]
        assert [list(v) for v in frame["inputs"]] == [list(r.inputs) for r in dataset.records]


def test_sqlite(datasets: list[Dataset]) -> None:
    for dataset in datasets:
        connection = sqlite3.connect(path_of(dataset, ".sqlite"))
        try:
            frame = pd.read_sql("SELECT * FROM ases ORDER BY asn", connection)
            metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
        finally:
            connection.close()
        assert from_flat(frame) == expected_rows(dataset)
        assert metadata["dataset"] == dataset.name
        assert metadata["schema_version"] == dataset.schema_version


def test_every_format_is_tested() -> None:
    tested = {"csv", "tsv", "csv.gz", "csv.zst", "json", "jsonl", "jsonl.gz", "jsonl.zst"}
    assert set(FORMAT_NAMES) == tested | {"parquet", "sqlite"}
