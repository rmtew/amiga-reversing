# 0001-002 Stop Requiring Legacy Entity State

## Parent

PRD 0001: Manual Review Workflow

## What to build

Stop treating `entities.jsonl` and `overrides.json` as required project files. Project creation, imports, server APIs, documentation, and tests should no longer require empty entity files before the full deletion slice removes all legacy support.

## Acceptance criteria

- [x] New project and import flows no longer create or require empty `entities.jsonl`.
- [x] Project and listing load paths tolerate targets with no `entities.jsonl` or `overrides.json`.
- [x] Rendering/listing paths prefer C analysis facts and projected manual state rather than entity overlays where replacements already exist.
- [x] Docs and CLI help no longer instruct users or agents to build entity databases.
- [x] Tests that only assert old entity-file existence are removed or rewritten around the new model.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Implementation evidence

- Project records and project path resolution now treat `entities.jsonl` as optional.
- `create_project` and disk import materialization no longer create empty `entities.jsonl` files.
- Listing annotation reads missing entity files as empty optional legacy overlays.
- Current disassembly CLI help points at binary analysis; remaining entity/progress tools are marked legacy.
- Fixed startup-sequence `s:Run` parsing while validating import behavior.
- Covered by `tests/test_disasm_projects.py`, `tests/test_import_adf.py`, `tests/test_disasm_annotations.py`, `tests/test_disasm_cli.py`, and `tests/test_build_entities.py::test_build_entities_help_loads_cleanly`.
- Verified with focused pytest, ruff, mypy, `cmd /c src\precommit.bat`, and `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`.

## Blocked by

- 0001-001 Manual Action Log Projection
