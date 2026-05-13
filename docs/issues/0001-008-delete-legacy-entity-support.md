# 0001-008 Delete Legacy Entity Support

## Parent

PRD 0001: Manual Review Workflow

## What to build

Delete `entities.jsonl`, `overrides.json`, entity confidence, and entity verification status as supported project state. Replace the remaining useful behavior with C analysis facts and Manual Action Log projections. This is not a compatibility migration; existing local targets can be regenerated or reimported.

## Acceptance criteria

- [ ] Entity override APIs and storage are removed or replaced by Manual Action Log actions.
- [ ] Rendering/listing paths no longer depend on entity overlays.
- [ ] Obsolete entity-building and entity-progress commands are removed or replaced with current analysis/review commands.
- [ ] Tests that cover entity APIs are deleted or rewritten against Manual Action Log projections and C analysis facts.
- [ ] No supported workflow requires `entities.jsonl`, `overrides.json`, entity confidence, or entity verification status.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-003 Manual Seeds In Analysis
- 0001-005 Manual Labels Comments And Label Scope
- 0001-007 Review State Rendering Export Warnings
