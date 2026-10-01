# 🏛️ State-Owned ASes

A dataset of the Autonomous Systems (ASes) run by **state-owned Internet operators** around the world: 984 ASes of companies in which a national government holds a majority stake, plus a partial list of 301 minority state-owned ASes. Each AS comes with the quote and source URL that confirmed the state's ownership. It is the dataset of the ACM IMC 2021 paper [*Identifying ASes of State-Owned Internet Operators*](https://doi.org/10.1145/3487552.3487822).

[![CI](https://github.com/estcarisimo/state-owned-ases/actions/workflows/ci.yml/badge.svg)](https://github.com/estcarisimo/state-owned-ases/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-estcarisimo.github.io%2Fstate--owned--ases-blue.svg)](https://estcarisimo.github.io/state-owned-ases/)
[![Paper](https://img.shields.io/badge/DOI-10.1145%2F3487552.3487822-informational.svg)](https://doi.org/10.1145/3487552.3487822)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE)
[![Code: MIT](https://img.shields.io/badge/code-MIT-yellow.svg)](LICENSE-CODE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> [!WARNING]
> **This is an archive. The data is not maintained.** Ownership was verified between
> **June 2019 and November 2020**. The dataset was last corrected in October 2021 and has
> not been re-checked since. Since then, operators have been privatized, nationalized,
> merged and renamed. ASNs have changed hands, and many evidence URLs no longer resolve.
> Use it as a **baseline** for that period, not as a picture of today's Internet. The
> 2026 restructuring changed only the file formats and fixed a few country codes and
> names (see [CHANGELOG.md](CHANGELOG.md)). No ownership was re-verified.

## ✨ Features

- 🗂️ **One canonical source**: one validated JSON document per dataset in [`data/canonical/`](data/canonical/). Every other file is generated from it.
- 📦 **Ready-made exports**: CSV, TSV, JSON, JSON Lines, Parquet and SQLite, plus gzip and Zstandard-compressed CSV and JSON Lines, all in [`data/exports/`](data/exports/)
- 🧾 **Evidence for every AS**: the quote, its language, the kind of source and the URL that confirmed state ownership
- 🌍 **Foreign subsidiaries**: 193 ASes of state-owned operators running networks in other countries, with the parent organization and the target country
- 🔏 **Integrity checks**: `MANIFEST.json` (row counts, schema version, SHA-256 of every file) and a `sha256sum`-compatible `SHA256SUMS`
- ✅ **Validated in CI**: schema checks, cross-format round-trip tests (pandas, DuckDB, sqlite3), a golden-value test that fails on any unintended data change, and a stale-export check

## 🚀 Quick Start

### Just the data

You do not need Python. Download a file from [`data/exports/`](data/exports/):

| Dataset | CSV | Parquet | JSON Lines | SQLite |
|---|---|---|---|---|
| Majority state-owned (main, 984 ASes) | [csv](data/exports/state-owned-ases/state_owned_ases.csv) | [parquet](data/exports/state-owned-ases/state_owned_ases.parquet) | [jsonl](data/exports/state-owned-ases/state_owned_ases.jsonl) | [sqlite](data/exports/state-owned-ases/state_owned_ases.sqlite) |
| Minority state-owned (partial, 301 ASes) | [csv](data/exports/minority-state-owned-ases/minority_state_owned_ases.csv) | [parquet](data/exports/minority-state-owned-ases/minority_state_owned_ases.parquet) | [jsonl](data/exports/minority-state-owned-ases/minority_state_owned_ases.jsonl) | [sqlite](data/exports/minority-state-owned-ases/minority_state_owned_ases.sqlite) |

TSV, JSON, `.gz` and `.zst` variants sit next to them. Verify a download with:

```bash
cd data/exports && sha256sum -c SHA256SUMS
```

### The tooling

Clone the repository and install it with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/estcarisimo/state-owned-ases.git
cd state-owned-ases
uv sync
```

The package is not on PyPI. To install the CLI without cloning:

```bash
pip install "git+https://github.com/estcarisimo/state-owned-ases.git"
```

## 📖 Usage

<!-- --8<-- [start:loading] -->
### Load the data

With pandas. Pass `keep_default_na=False`, because `NA` is Namibia's country code, not a missing value:

```python
import pandas as pd

ases = pd.read_csv(
    "data/exports/state-owned-ases/state_owned_ases.csv",
    keep_default_na=False,
    na_values=[""],
)
print(len(ases), "ASes in", ases["ownership_cc"].nunique(), "owner countries")
foreign = ases[ases["target_cc"].notna()]
print(foreign.groupby("ownership_cc")["target_cc"].nunique().nlargest(3))
```

Parquet keeps the types: `asn` is an integer and `inputs` is a list:

```python
import pandas as pd

ases = pd.read_parquet("data/exports/state-owned-ases/state_owned_ases.parquet")
print(ases.loc[ases["asn"] == 2119, ["org_name", "ownership_cc", "inputs"]])
```

With DuckDB, straight from the file:

```python
import duckdb

print(
    duckdb.sql(
        """
        SELECT ownership_country_name, count(*) AS ases
        FROM 'data/exports/state-owned-ases/state_owned_ases.parquet'
        GROUP BY ALL ORDER BY ases DESC LIMIT 5
        """
    )
)
```

With SQLite (also from the `sqlite3` shell):

```python
import sqlite3

with sqlite3.connect("data/exports/state-owned-ases/state_owned_ases.sqlite") as db:
    print(db.execute("SELECT asn, org_name FROM ases WHERE ownership_cc = 'NO' LIMIT 3").fetchall())
```
<!-- --8<-- [end:loading] -->

<!-- --8<-- [start:cli] -->
### Command-line tool

```bash
uv run state-owned-ases validate                  # validate data/canonical/ against the schema
uv run state-owned-ases export                    # regenerate data/exports/ (all formats)
uv run state-owned-ases export -f csv -f parquet -o /tmp/out   # selected formats elsewhere
uv run state-owned-ases check                     # fail if data/exports/ is stale
uv run state-owned-ases summary                   # record/organization/country counts
uv run state-owned-ases schema                    # JSON Schema of a canonical document
```
<!-- --8<-- [end:cli] -->

## 🗃️ Data

### Files

| Path | What it is |
|---|---|
| `data/canonical/state_owned_ases.json` | **Canonical.** Majority state-owned dataset: metadata and one record per AS |
| `data/canonical/minority_state_owned_ases.json` | **Canonical.** Minority state-owned dataset (partial) |
| `data/exports/<dataset>/*` | Generated by `state-owned-ases export`. Do not edit by hand |
| `data/exports/MANIFEST.json`, `SHA256SUMS` | Row counts, schema version and checksums of the exports |

Edit only the canonical files. CI fails if the exports do not match them.

<!-- --8<-- [start:dictionary] -->
### Data dictionary

One record per AS. Both datasets share the same columns. Empty or `null` means not recorded.

| Field | Type | Description |
|---|---|---|
| `asn` | integer | Autonomous System Number (unique within a dataset) |
| `conglomerate` | string | State-owned group the operator belongs to, `<CC>-<NAME>` (e.g. `NO-TELENOR`) |
| `org_id` | string | CAIDA AS2Org organization ID (RIR `ORG-…` handle, or CAIDA's `@aut-…`/`@family-…`) |
| `org_name` | string? | Organization name in AS2Org |
| `ownership_percentage` | number? | State equity in percent. **Minority dataset only**; `null` in the majority dataset |
| `ownership_cc` | string | ISO 3166-1 alpha-2 code of the owning state (for foreign subsidiaries, the parent's country) |
| `ownership_country_name` | string | Name of the owning state |
| `rir` | string | RIR of the owning country: `AFRINIC`, `APNIC`, `ARIN`, `LACNIC`, `RIPE` |
| `source` | string | Kind of confirmation source (`Company's website`, `Freedom House`, `World Bank`, …) |
| `quote` | string | Exact quote used to establish state ownership |
| `quote_lang` | string | Language of the quote |
| `url` | string | Where the quote was found (recorded 2019–2020; many links have since broken) |
| `additional_info` | string? | Extra context, e.g. that a shareholder fund is itself state-owned |
| `inputs` | list of codes | Which input sources first put the organization on the candidate list (see below). In CSV, TSV and SQLite, joined with `;` |
| `parent_org` | string? | Foreign subsidiaries only: AS2Org ID of the state-owned parent |
| `target_cc` | string? | Foreign subsidiaries only: country code where the subsidiary operates |
| `target_country_name` | string? | Foreign subsidiaries only: name of that country |

`inputs` codes: **G** country-level AS geolocation · **E** APNIC eyeballs · **C** Country-level Transit Influence · **O** Orbis · **W** Wikipedia and Freedom House.

Two things about record granularity to keep in mind:

- **Evidence is per AS, not per organization.** For 27 organizations, different ASes cite different quotes or URLs. Do not assume one quote per `org_id`.
- **The two datasets can share an AS.** AS6713 (Maroc Telecom) is in the majority dataset because the UAE's Etisalat controls it, and in the minority dataset because Morocco holds 30%.

The [documentation site](https://estcarisimo.github.io/state-owned-ases/) has the full schema, the format details, and every 2026 correction.
<!-- --8<-- [end:dictionary] -->

<!-- --8<-- [start:methodology] -->
## 🔬 Methodology (brief)

The full method is in the [paper](https://doi.org/10.1145/3487552.3487822) ([PDF](https://cseweb.ucsd.edu/~snoeren/papers/state-imc21.pdf)). In short:

- **Definition.** An AS is *state-owned* if the operator that holds it is majority-owned (more than 50% of equity, directly or through state-controlled companies and funds) by a **national** government, following the IMF's definition of a state-owned enterprise. Operators owned by provinces or cities are excluded. So are networks restricted to one sector, such as research and education networks.
- **Stage 1: candidates.** Five input sources produced a candidate list:
  - **Technical** (lists of ASes):
    - *G* — country-level AS geolocation: CAIDA prefix-to-AS (July 2019) plus NetAcuity geolocation; ASes originating at least 5% of a country's addresses.
    - *E* — APNIC eyeball estimates; ASes with at least 5% of a country's users.
    - *C* — Country-level Transit Influence; the top two transit ASes in each of 75 countries.

    ASes were mapped to companies through CAIDA AS2Org, WHOIS and PeeringDB.
  - **Non-technical** (company names):
    - *O* — Orbis (Bureau van Dijk): telecom firms more than 50% owned by a sovereign state.
    - *W* — Freedom House's *Freedom on the Net* reports and Wikipedia articles.
- **Stage 2: manual confirmation.** Each candidate company was checked by hand against authoritative sources:
  - company websites and annual reports, and government sites;
  - regulators and agencies (SEC, FCC, national regulators, ITU), and TeleGeography's CommsUpdate;
  - World Bank and IMF reports.

  The quote, URL and language behind each decision are in the data. Parent companies were followed to find subsidiaries, including **foreign subsidiaries**. Minority stakes found along the way were set aside into the minority list.
- **Stage 3: expansion.** Confirmed companies were mapped back to ASes, and sibling ASes were added from CAIDA AS2Org. Siblings that AS2Org missed were added by hand and reported to CAIDA.
- **Validation.** Regional experts reviewed the Latin American ASes and the French companies.

### 🤖 A pre-AI dataset

This dataset was built **before large language models**, almost entirely by hand. The paper (§9) estimates about 4.6 months of one person's time to inspect candidates. That meant reading annual reports, shareholder disclosures and regulator filings in several languages, then mapping company names to AS2Org organizations. Most of the reading was limited to documents in English or Spanish.

Anyone restarting or taking over this work today should expect AI to be a major source of improvement:

- triaging candidates;
- extracting and translating ownership statements from long reports in any language;
- matching brand names to registry names;
- flagging ownership changes since 2020.

Every inference should still be checked by a person, with evidence recorded as it is here. This archive's records, each backed by a quote and a URL, also make a labeled baseline for evaluating such a pipeline.

### ⚠️ Known limitations

- **Frozen in 2019–2020** (see the archive notice). Ownership is dynamic, and the paper lists privatizations, nationalizations and new foreign subsidiaries as expected sources of change.
- **Coverage favors large operators.** The 5% thresholds and the inputs used target major access and transit networks. Small state-owned operators are less likely to be included.
- **The minority list is incidental.** It was not searched for systematically and does not follow subsidiaries. Its coverage is unknown.
- **The paper's counts differ slightly.** The paper reports 989 and 302 ASes. Six repeated AS rows were removed later: five in October 2021 and one exact duplicate in 2026. The 193 foreign-subsidiary ASes match.
- **Country codes are as recorded.** `KV` is used for Kosovo. It is not an assigned ISO 3166-1 code; `XK` is the common user-assigned code.
<!-- --8<-- [end:methodology] -->

## 🏗️ Architecture

```
data/
├── canonical/                  # source of truth: one validated JSON document per dataset
└── exports/                    # generated: <dataset>/<file>.{csv,tsv,json,jsonl,parquet,sqlite,…}
    ├── MANIFEST.json           # counts, schema version, sizes and SHA-256 per file
    └── SHA256SUMS
src/state_owned_ases/
├── schema.py                   # Pydantic models: ASRecord, Dataset (fields, types, constraints)
├── canonical.py                # load/validate/save the canonical JSON deterministically
├── exporters.py                # one writer per format; deterministic (no timestamps)
├── manifest.py                 # MANIFEST.json and SHA256SUMS
├── build.py                    # export_all() and check_exports() (stale-export detection)
└── cli.py                      # Typer CLI: validate | export | check | summary | schema | version
tools/migrate_legacy.py         # provenance: how data/canonical/ was derived from the 2021 files
tests/                          # schema, round-trip per format, golden values, migration, docs
docs/                           # MkDocs site
```

## 🧪 Development

```bash
uv sync                                   # runtime + dev tools
uv run pre-commit install                 # git hooks (ruff, file hygiene)
uv run ruff check src tests tools
uv run ruff format --check src tests tools
uv run mypy src/state_owned_ases tools tests
uv run pytest --cov                       # includes running the Python examples in README and docs
uv run state-owned-ases check             # exports up to date with data/canonical/
uv run --group docs mkdocs build --strict
```

To change the data: edit `data/canonical/*.json`, run `uv run state-owned-ases export`, update `tests/golden/canonical.json`, and explain the change in `CHANGELOG.md` and in the PR.

## 📊 Example Output

```
$ uv run state-owned-ases check
ok  data/exports is up to date with data/canonical

$ uv run state-owned-ases summary
[
  {
    "name": "state-owned-ases",
    "title": "ASes of majority state-owned Internet operators",
    "ownership": "majority",
    "reference_period": [
      "2019-06",
      "2020-11"
    ],
    "records": 984,
    "organizations": 467,
    "conglomerates": 176,
    "ownership_countries": 125,
    "foreign_subsidiary_ases": 193
  },
  ...
]
```

## 🤝 Contributing

This is an archive. Fixes to the tooling, the documentation, or clear transcription errors are welcome. Updating ownership would be a new project; please open an issue first. See [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b fix/my-fix`)
3. Commit your changes (`git commit -m 'Fix …'`)
4. Push to the branch (`git push origin fix/my-fix`)
5. Open a Pull Request

## 📄 License

The **data** (`data/`) is licensed under [CC BY 4.0](LICENSE). The **code** (`src/`, `tests/`, `tools/`) is licensed under the [MIT License](LICENSE-CODE).

## 📝 Citation

If you use this dataset, please cite the paper (also in [CITATION.cff](CITATION.cff)):

<!-- --8<-- [start:bibtex] -->
```bibtex
@inproceedings{10.1145/3487552.3487822,
  author    = {Carisimo, Esteban and Gamero-Garrido, Alexander and Snoeren, Alex C. and Dainotti, Alberto},
  title     = {Identifying ASes of State-Owned Internet Operators},
  year      = {2021},
  isbn      = {9781450391290},
  publisher = {Association for Computing Machinery},
  address   = {New York, NY, USA},
  url       = {https://doi.org/10.1145/3487552.3487822},
  doi       = {10.1145/3487552.3487822},
  booktitle = {Proceedings of the 21st ACM Internet Measurement Conference},
  pages     = {687--702},
  numpages  = {16},
  location  = {Virtual Event},
  series    = {IMC '21}
}
```
<!-- --8<-- [end:bibtex] -->

## 🔗 Related Resources

- **Paper**: [ACM Digital Library](https://doi.org/10.1145/3487552.3487822) · [PDF](https://cseweb.ucsd.edu/~snoeren/papers/state-imc21.pdf)
- **CAIDA AS2Org**: [AS-to-Organization dataset](https://www.caida.org/catalog/datasets/as-organizations/), the source of `org_id`
- **Freedom House**: [Freedom on the Net](https://freedomhouse.org/report/freedom-net)
- **Borges**: [NU-AquaLab/borges](https://github.com/NU-AquaLab/borges), an LLM-assisted AS-to-organization mapping framework, a newer take on one of the manual steps above

## 🙏 Acknowledgements

- **Paper**: *Identifying ASes of State-Owned Internet Operators*
- **Authors**: Esteban Carisimo, Alexander Gamero-Garrido, Alex C. Snoeren, Alberto Dainotti
- **Conference**: ACM Internet Measurement Conference (IMC) 2021, Virtual Event
- **Link**: https://doi.org/10.1145/3487552.3487822

Thanks to Balakrishnan Chandrasekaran and Zhiyi Chen for the October 2021 data fixes, and to the regional experts who reviewed the dataset.
