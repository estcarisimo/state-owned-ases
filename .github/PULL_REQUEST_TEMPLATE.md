## Summary

<!-- What does this PR change and why? Link the issue if there is one. -->

## Data impact

<!-- "None" if the canonical data is untouched. Otherwise list every changed AS/field
     with old and new values and the evidence, and confirm tests/golden was updated. -->

## Checklist

- [ ] CI is green (lint, tests on all Python versions, data, docs, build)
- [ ] Independent review (`.github/REVIEW.md`, fresh session) returned `APPROVE` on the latest push; every earlier finding fixed or rebutted with evidence. **Required before merge.**
- [ ] Tests added or updated for behavior changes
- [ ] `data/exports/` regenerated with `uv run state-owned-ases export` if `data/canonical/` changed
- [ ] Docs updated (`README.md`, `docs/`) when user-facing behavior changed
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]` (data content changes under *Fixed (data content)*)
