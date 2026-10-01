"""Schema constraints reject the defects found in the legacy files."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from state_owned_ases.schema import COLUMNS, SCHEMA_VERSION, ASRecord, Dataset

pytestmark = pytest.mark.behavior

VALID: dict[str, Any] = {
    "asn": 2119,
    "conglomerate": "NO-TELENOR",
    "org_id": "ORG-NA38-RIPE",
    "org_name": "Telenor Norge AS",
    "ownership_cc": "NO",
    "ownership_country_name": "Norway",
    "rir": "RIPE",
    "source": "Company's website",
    "quote": "Major Shareholdings: Government of Norway (54,7%)",
    "quote_lang": "English",
    "url": "https://www.telenor.com/investors/share-information/major-shareholdings/",
    "inputs": ["G", "E", "O", "W"],
}


def make_dataset(records: list[dict[str, Any]], ownership: str = "majority") -> Dataset:
    return Dataset.model_validate(
        {
            "name": "test",
            "title": "t",
            "ownership": ownership,
            "reference_period": ["2019-06", "2020-11"],
            "description": "d",
            "records": records,
        }
    )


def test_valid_record_round_trips() -> None:
    record = ASRecord.model_validate(VALID)
    assert ASRecord.model_validate(record.model_dump()) == record
    assert tuple(record.model_dump()) == COLUMNS


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("asn", 0),
        ("asn", 2**32),
        ("ownership_cc", "Norway"),
        ("ownership_cc", "no"),
        ("rir", "RIPENCC"),
        ("inputs", []),
        ("inputs", ["E", "G"]),  # not canonical order
        ("inputs", ["G", "G"]),  # duplicate
        ("inputs", ["X"]),
        ("quote", ""),
        ("ownership_percentage", 0),
        ("ownership_percentage", 101),
    ],
)
def test_invalid_field_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        ASRecord.model_validate({**VALID, field: value})


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        ASRecord.model_validate({**VALID, "conglomerate_name": "x"})


@pytest.mark.parametrize(
    "subsidiary",
    [
        {"parent_org": "ORG-X", "target_cc": "SE"},
        {"target_cc": "SE", "target_country_name": "Sweden"},
        {"target_cc": "Maldives", "target_country_name": "MV", "parent_org": "ORG-X"},
    ],
)
def test_incomplete_or_swapped_subsidiary_rejected(subsidiary: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        ASRecord.model_validate({**VALID, **subsidiary})


def test_schema_version_default_matches_constant() -> None:
    assert make_dataset([VALID]).schema_version == SCHEMA_VERSION


def test_dataset_rejects_duplicate_and_unsorted_asns() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        make_dataset([VALID, VALID])
    with pytest.raises(ValidationError, match="sorted"):
        make_dataset([{**VALID, "asn": 3}, {**VALID, "asn": 2}])


def test_dataset_ownership_percentage_rules() -> None:
    with pytest.raises(ValidationError, match="minority records need"):
        make_dataset([VALID], ownership="minority")
    with pytest.raises(ValidationError, match="majority records have no"):
        make_dataset([{**VALID, "ownership_percentage": 54.7}])
    assert make_dataset([{**VALID, "ownership_percentage": 30.0}], ownership="minority")
