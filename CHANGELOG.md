# Changelog

All notable changes to this project are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org).
Changes to the data's content are listed separately from changes to its representation.

## [Unreleased]

## [2.0.0] - 2026-09-30

Restructured as an archive with one canonical data source. No ownership was re-verified:
the data still describes June 2019 to November 2020.

### Added

- Canonical JSON documents in `data/canonical/`, one per dataset, validated by a
  Pydantic schema (`src/state_owned_ases/schema.py`, schema version 1.0.0). Both
  datasets now share the same fields; `ownership_percentage` is `null` in the majority
  dataset.
- Generated exports in `data/exports/`: CSV, TSV, JSON, JSON Lines, Parquet, SQLite,
  and gzip/Zstandard-compressed CSV and JSON Lines, with `MANIFEST.json` (counts,
  schema version, sizes, SHA-256) and `SHA256SUMS`.
- `state-owned-ases` command-line tool (`validate`, `export`, `check`, `summary`,
  `schema`, `version`) and a `pyproject.toml`/uv project.
- `tools/migrate_legacy.py`, which derives the canonical documents from the 2021 files
  in git history; a test checks that it still reproduces them.
- Tests: schema constraints, a round trip of every format through independent readers
  (pandas, DuckDB, sqlite3), golden values for the canonical data, stale-export
  detection, regression against the paper's counts, and execution of the Python
  examples in the README and docs.
- CI (lint, mypy, tests on Python 3.10–3.13, exports check, docs build, `pip-audit`,
  `bandit`), CodeQL, Dependabot, pre-commit, a MkDocs documentation site, and community
  files (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff`,
  `AGENTS.md`, issue forms, PR template, `.github/REVIEW.md`).
- README: archival notice, data dictionary, loading examples, a brief methodology, known
  limitations, and a note on how AI could help a future version of this work.

### Changed (representation only)

- Records are one per AS, sorted by ASN. The single-table CSVs, the most up-to-date
  legacy files, are the source: the October 2021 fixes were applied only there.
- `asn` is an integer, `ownership_percentage` a number, empty strings are `null`, and
  surrounding whitespace is stripped (two quotes had trailing spaces).
- `inputs` is a list of codes, deduplicated and in canonical order (G, E, C, O, W); for
  example `"E, E, W, W, O, O"` became `["E", "O", "W"]`. Flat formats join it with `;`.
- The SQLite databases have a single `ases` table (primary key `asn`) and a `metadata`
  table.
- The code is licensed under MIT (`LICENSE-CODE`); the data remains CC BY 4.0.

### Removed

- The per-organization tables (`*_table_organizations.*` and `*_table_ases.*` in CSV,
  JSON and SQLite). They kept one confirmation quote per organization, while 27
  organizations have different evidence for different ASes. They also predated the
  October 2021 fixes. Every field they held is in the new exports. The 2021 files
  remain in git history; the last commit with them is `a4d6136`.
- The Jupyter notebooks in `examples/` and the pinned `requirements.txt` (2021
  versions). They are replaced by the tested loading examples in the README and docs.

### Fixed (data content)

All fixes are in `tools/migrate_legacy.py` (`CORRECTIONS`) with their reasons. No AS,
organization, quote or URL changed.

- Minority dataset: removed an exact duplicate row for AS35819.
- `target_country_name` held `AE` (the owner's code) for 14 ASes of Etisalat's foreign
  subsidiaries; set to the name of each `target_cc` (Afghanistan, Benin, Burkina Faso,
  Chad, Côte d'Ivoire, Egypt, Gabon, Mali, Mauritania, Morocco, Niger, Togo).
- `target_cc` and `target_country_name` were swapped for AS7642 and AS135053 (Maldives),
  AS9038 (Jordan), AS17458 (Diego Garcia, `IO`) and AS12874 (Italy).
- AS200724: `target_cc` `AU` → `AT` (Austria; the paper's Table 3 lists AT for Serbia).
- AS44218, AS49209, AS197407: `target_cc` `UK` → `GB` (the ISO 3166-1 code).
- One name per country code: `Russia` → `Russian Federation` (26 ASes; 155 already used
  it), `Italia` → `Italy` (2), `Laos` → `Lao People's Democratic Republic` (1), `Macau`
  → `Macao` (1).
- AS59974: `source` typo `Comapny's website` → `Company's website`.

### Security

- Removed `requirements.txt`, whose 2021 pins (IPython, jupyter-core, NumPy, Pygments, tornado) had 27
  open Dependabot alerts (13 high, 11 moderate, 3 low). Dependencies now live in
  `pyproject.toml`/`uv.lock` and are audited with `pip-audit` in CI.

## [1.0.0] - 2021-10-17

The dataset as released with the IMC 2021 paper, including community fixes.

### Added

- Majority and minority state-owned ASes in CSV (single table and per-organization
  tables), JSON and SQLite, with example notebooks (2021-09-29).

### Fixed

- `ownership_cc` was empty for Namibia's three ASes; set to `NA` (2021-10-14, Balakrishnan
  Chandrasekaran).
- Removed five duplicated AS rows from the majority single-table CSV (2021-10-17, Zhiyi
  Chen).
