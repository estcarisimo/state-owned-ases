# Data and formats

## Canonical source and exports

The data has **one source of truth**: one JSON document per dataset in
[`data/canonical/`](https://github.com/estcarisimo/state-owned-ases/tree/main/data/canonical).
Each document holds a short metadata header (name, title, ownership type, reference
period, description, schema version) and the list of records, sorted by ASN. The
[`ASRecord` and `Dataset` models](https://github.com/estcarisimo/state-owned-ases/blob/main/src/state_owned_ases/schema.py)
define the schema. `uv run state-owned-ases schema` prints it as JSON Schema.

Every file in [`data/exports/`](https://github.com/estcarisimo/state-owned-ases/tree/main/data/exports)
is generated from the canonical documents by `uv run state-owned-ases export`. CI fails
if the committed exports differ from a fresh export.

| Format | File suffix | Notes |
|---|---|---|
| CSV | `.csv` | RFC 4180, UTF-8, `\n` line endings, header row; empty field = null; `inputs` joined with `;` |
| TSV | `.tsv` | Same as CSV, tab-delimited |
| JSON | `.json` | Array of records; `inputs` is a list; `null` for missing values |
| JSON Lines | `.jsonl` | One record per line, same fields as JSON |
| Parquet | `.parquet` | Typed (`asn` int64, `ownership_percentage` float64, `inputs` list&lt;string&gt;); Zstandard-compressed; dataset metadata in the schema's key/value metadata |
| SQLite | `.sqlite` | Table `ases` (`asn` primary key, indexes on `org_id` and `ownership_cc`; `inputs` joined with `;`), table `metadata` (key/value) |
| Compressed | `.csv.gz`, `.csv.zst`, `.jsonl.gz`, `.jsonl.zst` | gzip for compatibility, Zstandard for size; pandas reads both directly |

`data/exports/MANIFEST.json` records the schema version, the per-dataset counts, the
SHA-256 of each canonical document, and the size and SHA-256 of every export.
`data/exports/SHA256SUMS` holds the same checksums in `sha256sum -c` format. The text
formats are byte-reproducible. Parquet and SQLite embed library versions, so they are
checked by content instead.

!!! note "`NA` is Namibia"
    Tools that treat the string `NA` as missing (pandas by default, R's `read.csv`)
    will drop Namibia's country code. Use `keep_default_na=False, na_values=[""]` in
    pandas, `na = ""` in readr, or read the Parquet file.

--8<-- "README.md:dictionary"

## Corrections made in 2026

The canonical documents were derived from the legacy single-table CSVs by
[`tools/migrate_legacy.py`](https://github.com/estcarisimo/state-owned-ases/blob/main/tools/migrate_legacy.py).
A test re-runs that script against git history and checks that it reproduces the
canonical files. The script lists every content correction with its reason, and the
[changelog](changelog.md) summarizes them. They touch only country codes and names and
one typo. No AS, organization, quote or URL changed.
