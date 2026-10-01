"""The command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import CANONICAL_DIR, EXPORTS_DIR
from typer.testing import CliRunner

from state_owned_ases import __version__
from state_owned_ases.cli import app

pytestmark = pytest.mark.behavior

runner = CliRunner()


def run(*args: str) -> tuple[int, str]:
    result = runner.invoke(app, list(args))
    return result.exit_code, result.output


def test_validate() -> None:
    code, out = run("validate", "--canonical", str(CANONICAL_DIR))
    assert code == 0
    assert "state-owned-ases: 984 records" in out


def test_check_passes_on_committed_exports() -> None:
    code, out = run("check", "-c", str(CANONICAL_DIR), "-e", str(EXPORTS_DIR))
    assert code == 0, out


def test_check_fails_on_empty_directory(tmp_path: Path) -> None:
    code, out = run("check", "-c", str(CANONICAL_DIR), "-e", str(tmp_path))
    assert code == 1
    assert "missing export" in out


def test_export_selected_formats(tmp_path: Path) -> None:
    code, out = run(
        "export", "-c", str(CANONICAL_DIR), "-o", str(tmp_path), "-f", "csv", "-f", "parquet"
    )
    assert code == 0, out
    assert "wrote 4 files" in out
    written = sorted(p.name for p in (tmp_path / "state-owned-ases").iterdir())
    assert written == ["state_owned_ases.csv", "state_owned_ases.parquet"]
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert [f["format"] for f in manifest["datasets"][0]["files"]] == ["csv", "parquet"]


def test_export_rejects_unknown_format(tmp_path: Path) -> None:
    code, out = run("export", "-o", str(tmp_path), "-f", "xlsx")
    assert code == 2
    assert "unknown format" in out


def test_summary_and_schema_and_version() -> None:
    code, out = run("summary", "-c", str(CANONICAL_DIR))
    assert code == 0
    assert [s["records"] for s in json.loads(out)] == [984, 301]
    code, out = run("schema")
    assert code == 0
    assert "ASRecord" in json.loads(out)["$defs"]
    assert run("version") == (0, f"{__version__}\n")


@pytest.mark.parametrize("command", ["validate", "export", "check", "summary"])
def test_missing_canonical_data_is_a_clean_error(
    command: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)  # as after a pip install, outside a clone
    result = runner.invoke(app, [command])
    assert result.exit_code == 2
    assert "Run from the root of a clone" in result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)
