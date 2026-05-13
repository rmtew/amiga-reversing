# 0001-002 Stop Requiring Legacy Entity State

## Parent

PRD 0001: Manual Review Workflow

## What to build

Stop treating `entities.jsonl` and `overrides.json` as required project files. Project creation, imports, server APIs, documentation, and tests should no longer require empty entity files before the full deletion slice removes all legacy support.

## Acceptance criteria

- [ ] New project and import flows no longer create or require empty `entities.jsonl`.
- [ ] Project and listing load paths tolerate targets with no `entities.jsonl` or `overrides.json`.
- [ ] Rendering/listing paths prefer C analysis facts and projected manual state rather than entity overlays where replacements already exist.
- [ ] Docs and CLI help no longer instruct users or agents to build entity databases.
- [ ] Tests that only assert old entity-file existence are removed or rewritten around the new model.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-001 Manual Action Log Projection
