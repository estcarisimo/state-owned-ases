"""Documentation is executed: every Python block runs, and quoted figures are real."""

from __future__ import annotations

import re

import pytest
from conftest import ROOT

from state_owned_ases.manifest import dataset_summary
from state_owned_ases.schema import COLUMNS, Dataset

pytestmark = pytest.mark.behavior

DOC_FILES = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
PYTHON_BLOCK = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)


def python_blocks() -> list[tuple[str, str]]:
    return [
        (f"{path.name}#{i}", block)
        for path in DOC_FILES
        for i, block in enumerate(PYTHON_BLOCK.findall(path.read_text(encoding="utf-8")))
    ]


def test_docs_have_python_examples() -> None:
    assert len(python_blocks()) >= 4


@pytest.mark.parametrize(("where", "code"), python_blocks(), ids=lambda v: v[:20])
def test_python_block_runs(
    where: str, code: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(ROOT)
    exec(compile(code, where, "exec"), {"__name__": "__docs__"})  # noqa: S102
    assert capsys.readouterr().out, f"{where} printed nothing"


def test_readme_dictionary_lists_every_column() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    documented = re.findall(r"^\| `(\w+)` \|", readme, re.MULTILINE)
    assert tuple(documented) == COLUMNS


def test_quoted_figures_match_data(majority: Dataset, minority: Dataset) -> None:
    big, small = dataset_summary(majority), dataset_summary(minority)
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    for label, key in [
        ("ASes", "records"),
        ("Organizations (AS2Org IDs)", "organizations"),
        ("Owning countries", "ownership_countries"),
        ("ASes of foreign subsidiaries", "foreign_subsidiary_ases"),
    ]:
        assert f"| {label} | {big[key]} | {small[key]} |" in index
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{big['records']} ASes of companies" in readme
    assert f"partial list of {small['records']} minority" in readme
    assert f"{big['foreign_subsidiary_ases']} ASes of state-owned operators" in readme


def test_no_python_blocks_left_unexecuted() -> None:
    # Guard against blocks the regex would miss (e.g. "```py" or indented fences).
    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^\s*```py(?!thon)", text, re.MULTILINE), path
