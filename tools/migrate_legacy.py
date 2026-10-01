"""One-off migration of the 2021 legacy files into the canonical JSON documents.

Kept for provenance: it documents exactly how ``data/canonical/`` was derived from the
files the IMC 2021 release published. It reads the legacy single-table CSVs straight
from git history, so it still runs after those files were removed from the tree::

    uv run python tools/migrate_legacy.py

Why the single-table CSVs: they are the most recent legacy files. The October 2021
community fixes (Namibia's ``NA`` country code, five duplicated rows) were applied only
to ``data/state-owned-ases/csv/state_owned_ases.csv``, and the per-organization tables
(CSV, JSON, SQLite) keep one confirmation quote per organization, while the single-table
files keep the evidence recorded for each AS (it differs between ASes of the same
organization for 27 organizations).

Two kinds of change are applied, and CHANGELOG.md lists them separately:

* Representation only: types (``asn`` as an integer, ``ownership_percentage`` as a
  number, empty strings as ``null``), surrounding whitespace stripped, ``inputs`` as a
  deduplicated list in canonical order, records sorted by ASN, exact duplicate rows
  dropped.
* Content fixes, each listed in :data:`CORRECTIONS` with its reason. They touch only
  country codes and names and one typo; no AS, organization, quote or URL changes.
  Without them the data does not pass the canonical schema.
"""

from __future__ import annotations

import csv
import io
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from state_owned_ases import canonical
from state_owned_ases.schema import INPUT_CODES, ASRecord, Dataset

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
LEGACY_REF = "a4d6136"  # last commit with the 2021 layout (README edit, 2022-02-11)
REFERENCE_PERIOD = ("2019-06", "2020-11")

LEGACY = {
    "state-owned-ases": "data/state-owned-ases/csv/state_owned_ases.csv",
    "minority-state-owned-ases": "data/minority-state-owned-ases/csv/minority_state_owned_ases.csv",
}

DATASET_INFO: dict[str, dict[str, Any]] = {
    "state-owned-ases": {
        "title": "ASes of majority state-owned Internet operators",
        "ownership": "majority",
        "description": (
            "Autonomous Systems operated by Internet operators in which a national "
            "(federal-level) government holds more than 50% of the equity, directly or "
            "through state-controlled companies and funds, including foreign subsidiaries. "
            "Main dataset of Carisimo, Gamero-Garrido, Snoeren and Dainotti, 'Identifying "
            "ASes of State-Owned Internet Operators', ACM IMC 2021 "
            "(doi:10.1145/3487552.3487822). Ownership reflects June 2019 to November 2020 "
            "and has not been re-verified since."
        ),
    },
    "minority-state-owned-ases": {
        "title": "ASes of minority state-owned Internet operators (partial)",
        "ownership": "minority",
        "description": (
            "Autonomous Systems of Internet operators with state participation below 50%, "
            "found incidentally while building the majority dataset. Not searched for "
            "systematically: coverage is unknown and subsidiaries were not followed. "
            "Companion to Carisimo et al., ACM IMC 2021 (doi:10.1145/3487552.3487822). "
            "Ownership reflects June 2019 to November 2020 and has not been re-verified "
            "since."
        ),
    },
}


@dataclass(frozen=True)
class Correction:
    """A content fix: set ``field`` from ``old`` to ``new`` on the listed ASes.

    ``asns`` lists every AS the fix applies to. The migration fails if any of them does
    not hold ``old``, or, when ``exhaustive`` is set, if any AS still holds ``old`` in
    ``field`` once all fixes ran (so a fix cannot silently miss a row).
    """

    dataset: str
    asns: tuple[int, ...]
    field: str
    old: str
    new: str
    reason: str
    exhaustive: bool = True


MAJORITY = "state-owned-ases"
_ETISALAT_TARGETS = {
    16058: "Gabon",
    21271: "Mali",
    25543: "Burkina Faso",
    29544: "Mauritania",
    6713: "Morocco",
    36903: "Morocco",
    36956: "Morocco",
    37190: "Côte d'Ivoire",
    37205: "Niger",
    37229: "Togo",
    131284: "Afghanistan",
    37136: "Benin",
    36992: "Egypt",
    327802: "Chad",
}
_RUSSIA_SHORT_NAME = (
    8439, 48753, 50514, 28812, 28881, 48302, 30733, 44982, 50565, 51804, 34892, 49291, 21127,
    44733, 31436, 44927, 41024, 44587, 31257, 50427, 8470, 204137, 8342, 57107, 60388, 15638,
)  # fmt: skip

#: Every content fix, also listed in CHANGELOG.md under 2.0.0 → Fixed.
CORRECTIONS: tuple[Correction, ...] = (
    *(
        Correction(MAJORITY, (asn,), "target_country_name", "AE", name,
                   "UAE's country code was recorded as the target country name of "
                   "Etisalat's foreign subsidiaries; the name of target_cc is used instead")
        for asn, name in _ETISALAT_TARGETS.items()
    ),
    Correction(MAJORITY, (7642, 135053), "target_cc", "Maldives", "MV",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (7642, 135053), "target_country_name", "MV", "Maldives",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (9038,), "target_cc", "Jordan", "JO",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (9038,), "target_country_name", "JO", "Jordan",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (17458,), "target_cc", "Diego Garcia", "IO",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (17458,), "target_country_name", "IO", "Diego Garcia",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (12874,), "target_cc", "Italy", "IT",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (12874,), "target_country_name", "IT", "Italy",
               "target_cc and target_country_name were swapped"),
    Correction(MAJORITY, (200724,), "target_cc", "AU", "AT",
               "Austria is AT (AU is Australia); the paper's Table 3 lists AT for Serbia",
               exhaustive=False),
    Correction(MAJORITY, (44218, 49209, 197407), "target_cc", "UK", "GB",
               "ISO 3166-1 alpha-2 code of the United Kingdom is GB (UK is only reserved)"),
    Correction(MAJORITY, _RUSSIA_SHORT_NAME, "ownership_country_name", "Russia",
               "Russian Federation",
               "one name per country code; 155 of 181 RU rows already used this one"),
    Correction(MAJORITY, (15720, 43976), "ownership_country_name", "Italia", "Italy",
               "English country names throughout; AS12874 already used Italy for IT"),
    Correction(MAJORITY, (131267,), "target_country_name", "Laos",
               "Lao People's Democratic Republic",
               "one name per country code; matches the ownership name used for LA"),
    Correction(MAJORITY, (136167,), "target_country_name", "Macau", "Macao",
               "one name per country code; matches the ownership name used for MO"),
    Correction(MAJORITY, (59974,), "source", "Comapny's website", "Company's website",
               "typo"),
)  # fmt: skip


def read_legacy_csv(path: str, ref: str = LEGACY_REF) -> list[dict[str, str]]:
    """Read a legacy CSV from git history, keeping ``NA`` (Namibia) as a string."""
    text = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return list(csv.DictReader(io.StringIO(text)))


def parse_inputs(raw: str) -> tuple[str, ...]:
    """Parse ``"G, E, W, O"`` into a deduplicated tuple in canonical order."""
    codes = {code.strip() for code in raw.split(",") if code.strip()}
    unknown = codes - set(INPUT_CODES)
    if unknown:
        raise ValueError(f"unknown input codes {sorted(unknown)} in {raw!r}")
    return tuple(code for code in INPUT_CODES if code in codes)


def convert_row(row: dict[str, str]) -> dict[str, Any]:
    """Convert one legacy CSV row to canonical field types."""
    out: dict[str, Any] = {k: (v.strip() or None) for k, v in row.items()}
    out["asn"] = int(row["asn"])
    out["inputs"] = parse_inputs(row["inputs"])
    if "ownership_percentage" in row:
        out["ownership_percentage"] = float(row["ownership_percentage"])
    return out


def migrate(name: str) -> Dataset:
    """Build one canonical dataset from its legacy CSV."""
    rows = [convert_row(row) for row in read_legacy_csv(LEGACY[name])]
    unique: dict[int, dict[str, Any]] = {}
    for row in rows:
        previous = unique.setdefault(row["asn"], row)
        if previous is not row:
            if previous != row:
                raise ValueError(f"AS{row['asn']} appears twice with different content")
            logger.warning("%s: dropping exact duplicate row for AS%d", name, row["asn"])
    for fix in (c for c in CORRECTIONS if c.dataset == name):
        for asn in fix.asns:
            if unique[asn][fix.field] != fix.old:
                found = unique[asn][fix.field]
                raise ValueError(f"AS{asn}.{fix.field}: expected {fix.old!r}, found {found!r}")
            unique[asn][fix.field] = fix.new
        logger.info("%s: %s %r -> %r on %d ASes", name, fix.field, fix.old, fix.new, len(fix.asns))
    for fix in (c for c in CORRECTIONS if c.dataset == name and c.exhaustive):
        leftover = sorted(asn for asn, row in unique.items() if row[fix.field] == fix.old)
        if leftover:
            raise ValueError(f"{fix.field}={fix.old!r} still present on AS{leftover}")
    records = tuple(ASRecord.model_validate(unique[asn]) for asn in sorted(unique))
    return Dataset(
        name=name,
        reference_period=REFERENCE_PERIOD,
        records=records,
        **DATASET_INFO[name],
    )


def main(
    out_dir: Path = typer.Option(ROOT / "data" / "canonical", help="Output directory."),
) -> None:
    """Write the canonical JSON documents from the legacy CSVs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for name, filename in zip(LEGACY, canonical.DATASET_FILES, strict=True):
        dataset = migrate(name)
        canonical.save(dataset, out_dir / filename)
        logger.info("%s: %d records -> %s", name, len(dataset.records), out_dir / filename)


if __name__ == "__main__":
    typer.run(main)
