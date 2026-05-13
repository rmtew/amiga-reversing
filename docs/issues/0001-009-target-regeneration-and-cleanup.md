# 0001-009 Target Regeneration And Cleanup

## Parent

PRD 0001: Manual Review Workflow

## What to build

Regenerate or reimport local target projects so stale `entities.jsonl`, `overrides.json`, and old generated project state no longer define behavior. Remove obsolete commands, docs, tests, and target artifacts tied only to the retired model.

This slice finishes the cleanup once replacement behavior is in place.

## Acceptance criteria

- [ ] Local target projects no longer rely on stale entity files or overrides.
- [ ] Obsolete entity-building commands are removed or replaced with current analysis/review commands.
- [ ] Generated or checked-in stale entity artifacts are deleted where they are no longer needed.
- [ ] Documentation reflects the Manual Review workflow as the supported path.
- [ ] Full test suite behavior is green after target regeneration/reimport.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-008 Delete Legacy Entity Support
