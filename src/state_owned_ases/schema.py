"""Canonical schema of the state-owned ASes datasets.

Every dataset in this repository is one JSON document (see ``data/canonical/``) holding a
small metadata header and a list of :class:`ASRecord`, one per Autonomous System. Every
export format is generated from that document, so this module is the single definition
of field names, types, and constraints.
"""

from __future__ import annotations

import re
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION: Final = "1.0.0"

#: Input sources that put an organization on the candidate list, in the order the paper
#: lists them: G = country-level AS geolocation, E = APNIC eyeballs, C = Country-level
#: Transit Influence, O = Orbis, W = Wikipedia and Freedom House.
INPUT_CODES: tuple[str, ...] = ("G", "E", "C", "O", "W")
InputCode = Literal["G", "E", "C", "O", "W"]

RIR = Literal["AFRINIC", "APNIC", "ARIN", "LACNIC", "RIPE"]
Ownership = Literal["majority", "minority"]

_COUNTRY_CODE = re.compile(r"^[A-Z]{2}$")
_MAX_ASN = 2**32 - 1


class ASRecord(BaseModel):
    """One Autonomous System operated by a (majority or minority) state-owned operator.

    Attributes
    ----------
    asn
        Autonomous System Number.
    conglomerate
        Identifier of the state-owned group the operator belongs to, ``<CC>-<NAME>``.
    org_id
        Organization identifier from CAIDA's AS2Org dataset (``ORG-…`` handles from RIR
        WHOIS, or CAIDA's synthetic ``@aut-…`` / ``@family-…`` identifiers).
    org_name
        Organization name as recorded in AS2Org; ``None`` when it was not recorded.
    ownership_percentage
        State equity in percent. Recorded for the minority dataset only; ``None`` in the
        majority dataset, where ownership is above 50% by definition.
    ownership_cc, ownership_country_name
        ISO 3166-1 alpha-2 code and name of the state that owns the operator. For
        foreign subsidiaries this is the country of the parent company.
    rir
        Regional Internet Registry of the owning country.
    source, quote, quote_lang, url, additional_info
        Evidence: the kind of confirmation source, the exact quote used to establish
        state ownership, the language of that quote, where it was found, and optional
        context (for example, that a shareholder fund is itself state-owned). URLs were
        recorded in 2019-2020 and many no longer resolve.
    inputs
        Candidate-list input sources (see :data:`INPUT_CODES`), deduplicated, in
        canonical order.
    parent_org, target_cc, target_country_name
        Foreign subsidiaries only: the parent's AS2Org identifier and the country the
        subsidiary operates in. The three fields are either all set or all ``None``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    asn: int = Field(ge=1, le=_MAX_ASN)
    conglomerate: str = Field(min_length=1)
    org_id: str = Field(min_length=1)
    org_name: str | None = None
    ownership_percentage: float | None = Field(default=None, gt=0, le=100)
    ownership_cc: str
    ownership_country_name: str = Field(min_length=1)
    rir: RIR
    source: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    quote_lang: str = Field(min_length=1)
    url: str = Field(min_length=1)
    additional_info: str | None = None
    inputs: tuple[InputCode, ...] = Field(min_length=1)
    parent_org: str | None = None
    target_cc: str | None = None
    target_country_name: str | None = None

    @field_validator("ownership_cc", "target_cc")
    @classmethod
    def _check_country_code(cls, value: str | None) -> str | None:
        if value is not None and not _COUNTRY_CODE.fullmatch(value):
            raise ValueError(f"not a two-letter upper-case country code: {value!r}")
        return value

    @field_validator("inputs")
    @classmethod
    def _check_inputs_canonical(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        canonical = tuple(code for code in INPUT_CODES if code in value)
        if value != canonical:
            raise ValueError(f"inputs must be unique and ordered as {INPUT_CODES}: {value}")
        return value

    @model_validator(mode="after")
    def _check_target_pair(self) -> ASRecord:
        subsidiary = (self.parent_org, self.target_cc, self.target_country_name)
        if any(v is None for v in subsidiary) and any(v is not None for v in subsidiary):
            raise ValueError("parent_org, target_cc and target_country_name are set together")
        return self


class Dataset(BaseModel):
    """A canonical dataset: metadata plus the list of AS records.

    Attributes
    ----------
    schema_version
        Version of this schema (:data:`SCHEMA_VERSION`).
    name
        Short identifier, also the export directory name.
    title
        Human-readable title.
    ownership
        ``"majority"`` (state owns more than 50%, the paper's main dataset) or
        ``"minority"`` (incidental, partial list).
    reference_period
        Months during which candidate lists were built and ownership verified.
    description
        One-paragraph description, copied into export metadata.
    records
        AS records, sorted by ASN, unique by ASN.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = "1.0.0"
    name: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str
    ownership: Ownership
    reference_period: tuple[str, str]
    description: str
    records: tuple[ASRecord, ...]

    @model_validator(mode="after")
    def _check_records(self) -> Dataset:
        asns = [record.asn for record in self.records]
        if asns != sorted(asns):
            raise ValueError("records must be sorted by asn")
        if len(asns) != len(set(asns)):
            raise ValueError("duplicate asn in records")
        for record in self.records:
            has_percentage = record.ownership_percentage is not None
            if self.ownership == "minority" and not has_percentage:
                raise ValueError(f"AS{record.asn}: minority records need ownership_percentage")
            if self.ownership == "majority" and has_percentage:
                raise ValueError(f"AS{record.asn}: majority records have no ownership_percentage")
        return self


#: Column order of every flat export (CSV, TSV, SQLite, Parquet).
COLUMNS: tuple[str, ...] = tuple(ASRecord.model_fields)
