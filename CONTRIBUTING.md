# Contributing

Thanks for your interest. This repository is an **archive**: the data describes state
ownership of Internet operators from June 2019 to November 2020 and is not being
updated. Contributions are welcome when they:

- fix a clear transcription error in the data (a wrong country code, a broken field),
  with evidence from the original source or the paper;
- improve the tooling, the formats, the tests, or the documentation.

Re-verifying or updating ownership would be a new dataset, not a fix to this one. If you
plan to start that work, please open an issue first: we would be glad to point to it.

## Development setup

The project uses [uv](https://docs.astral.sh/uv/) for environments and dependencies.

```bash
git clone git@github.com:estcarisimo/state-owned-ases.git
cd state-owned-ases
uv sync                       # runtime + dev tools
uv run pre-commit install     # git hooks: ruff, file hygiene
```

Run the same checks as CI:

```bash
uv run ruff check src tests tools
uv run ruff format --check src tests tools
uv run mypy src/state_owned_ases tools tests
uv run pytest --cov --cov-fail-under=90
uv run state-owned-ases check
uv run --group docs mkdocs build --strict
uvx cffconvert --validate
```

`tests/test_migration.py` reads the 2021 files from git history, so it needs a full clone
(not `--depth 1`).

## Changing the data

1. Edit the canonical document in `data/canonical/`. Never edit `data/exports/`.
2. If the change corrects a value inherited from the 2021 files, add it to
   `CORRECTIONS` in `tools/migrate_legacy.py` with a reason, and run
   `uv run python tools/migrate_legacy.py`.
3. Run `uv run state-owned-ases export` to regenerate every format, the manifest and the
   checksums.
4. Update `tests/golden/canonical.json`, and put the old-vs-new values in the PR
   description.
5. Add a bullet under `[Unreleased]` → `Fixed (data content)` in `CHANGELOG.md`.

## Conventions

- Python 3.10+, ruff for lint and format (line length 100), mypy blocking.
- `pathlib.Path`; `logging` in library code, output only in `cli.py`.
- NumPy-style docstrings and type hints on public functions.
- American English in code, docs, the changelog, commit messages and PR text.
- Tests are plain pytest functions, each with exactly one marker: `math` or `behavior`.
- The Python examples in `README.md` and `docs/` are executed by the test suite.

## Pull requests

- Branch from `main` (`fix/…`, `feat/…`, `docs/…`, `data/…`, `chore/…`). `main` is
  protected: no direct pushes.
- CI must be green: lint, type check, tests on Python 3.10–3.13, exports check, docs
  build.
- Every PR receives an independent review (the brief is `.github/REVIEW.md`). It is
  merged only after that review approves the final commit.
- Update `CHANGELOG.md` for any user-visible change.

## Releasing

1. Move the `[Unreleased]` entries under a new version and date in `CHANGELOG.md`.
2. Bump `version` in `pyproject.toml`, and `version` and `date-released` in
   `CITATION.cff`, in the same commit. Run `uvx cffconvert --validate`.
3. Merge, then tag `vX.Y.Z` on `main` and create a GitHub release. The package is not
   published to PyPI.
