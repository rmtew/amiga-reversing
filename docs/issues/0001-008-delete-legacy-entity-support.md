# 0001-008 Delete Legacy Entity Support

## Parent

PRD 0001: Manual Review Workflow

## What to build

Delete `entities.jsonl`, `overrides.json`, entity confidence, and entity verification status as supported project state. Replace the remaining useful behavior with C analysis facts and Manual Action Log projections. This is not a compatibility migration; existing local targets can be regenerated or reimported.

## Acceptance criteria

- [x] Entity override APIs and storage are removed or replaced by Manual Action Log actions.
- [x] Rendering/listing paths no longer depend on entity overlays.
- [x] Obsolete entity-building and entity-progress commands are removed or replaced with current analysis/review commands.
- [x] Tests that cover entity APIs are deleted or rewritten against Manual Action Log projections and C analysis facts.
- [x] No supported workflow requires `entities.jsonl`, `overrides.json`, entity confidence, or entity verification status.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-003 Manual Seeds In Analysis
- 0001-005 Manual Labels Comments And Label Scope
- 0001-007 Review State Rendering Export Warnings

## Completed

2026-05-13

## Verification

- `uv run python -m pytest tests\test_active_imports.py tests\test_benchmark_target.py tests\test_disasm_cli.py tests\test_disasm_projects.py tests\test_disasm_server.py::test_route_listing_returns_cached_window tests\test_genam_roundtrip.py -q`
- `uv run ruff check amiga_reversing\disasm amiga_reversing\tools tests\test_active_imports.py tests\test_benchmark_target.py tests\test_disasm_cli.py tests\test_disasm_projects.py tests\test_disasm_server.py tests\test_genam_roundtrip.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`
