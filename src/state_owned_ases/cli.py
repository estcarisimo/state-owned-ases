"""Command-line interface: ``state-owned-ases validate|export|check|summary|schema|version``."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import typer

from state_owned_ases import __version__, canonical
from state_owned_ases.build import check_exports, export_all
from state_owned_ases.exporters import FORMAT_NAMES, FORMATS
from state_owned_ases.manifest import dataset_summary
from state_owned_ases.schema import Dataset

app = typer.Typer(
    help="Validate the canonical state-owned ASes data and export it to other formats.",
    no_args_is_help=True,
    add_completion=False,
)

CANONICAL_DIR = Path("data/canonical")
EXPORTS_DIR = Path("data/exports")

CanonicalOption = typer.Option(
    CANONICAL_DIR, "--canonical", "-c", help="Directory with the canonical JSON documents."
)


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Log every file.")) -> None:
    """Configure logging for all commands."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING, format="%(levelname)s %(message)s"
    )


@app.command()
def validate(canonical_dir: Path = CanonicalOption) -> None:
    """Validate the canonical datasets against the schema."""
    for dataset in canonical.load_all(canonical_dir):
        typer.echo(f"ok  {dataset.name}: {len(dataset.records)} records")


@app.command()
def export(
    canonical_dir: Path = CanonicalOption,
    out_dir: Path = typer.Option(EXPORTS_DIR, "--out", "-o", help="Export root directory."),
    formats: list[str] = typer.Option(
        [],
        "--format",
        "-f",
        help=f"Format to write (repeatable; default: all). One of: {', '.join(FORMAT_NAMES)}.",
    ),
) -> None:
    """Write every dataset in every format, plus MANIFEST.json and SHA256SUMS."""
    unknown = sorted(set(formats) - set(FORMAT_NAMES))
    if unknown:
        raise typer.BadParameter(f"unknown format(s): {', '.join(unknown)}", param_hint="--format")
    selected = tuple(fmt for fmt in FORMATS if not formats or fmt.name in formats)
    manifest = export_all(canonical_dir, out_dir, selected)
    count = sum(len(entry["files"]) for entry in manifest["datasets"])
    typer.echo(f"wrote {count} files to {out_dir}")


@app.command()
def check(
    canonical_dir: Path = CanonicalOption,
    exports_dir: Path = typer.Option(EXPORTS_DIR, "--exports", "-e", help="Committed exports."),
) -> None:
    """Fail if the committed exports are stale or inconsistent with the canonical data."""
    problems = check_exports(canonical_dir, exports_dir)
    for problem in problems:
        typer.echo(f"FAIL {problem}", err=True)
    if problems:
        typer.echo("Regenerate with: uv run state-owned-ases export", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"ok  {exports_dir} is up to date with {canonical_dir}")


@app.command()
def summary(canonical_dir: Path = CanonicalOption) -> None:
    """Print record, organization and country counts as JSON."""
    summaries = [dataset_summary(d) for d in canonical.load_all(canonical_dir)]
    typer.echo(json.dumps(summaries, indent=2))


@app.command()
def schema() -> None:
    """Print the JSON Schema of a canonical dataset document."""
    typer.echo(json.dumps(Dataset.model_json_schema(), indent=2))


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)
