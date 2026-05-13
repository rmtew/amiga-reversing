# 0001-006 Checklist Review UI And Suggested Actions

## Parent

PRD 0001: Manual Review Workflow

## What to build

Build the checklist-first Manual Review UI. The primary workflow is an ordered list of Manual Review Items with facets for kind, confidence, state, section, source, and range. Each item can navigate to evidence and can offer structured Suggested Review Actions that either stay transient or append domain actions to the Manual Action Log.

## Acceptance criteria

- [x] Users can view Manual Review Items as a checklist sorted by severity, scope, and range.
- [x] Users can filter by kind, confidence, state, section, source, and range.
- [x] Users can navigate from a Manual Review Item to the relevant listing range without appending log actions.
- [x] Users can create Manual Seeds from structured suggested actions.
- [x] Users can resolve or acknowledge review items through Manual Action Log actions.
- [x] Orphan code candidates offer navigate, create required code Manual Seed, and resolve as data or padding actions.
- [x] Unreconciled data ranges offer navigate, create data Manual Seed as string/scalar table/pointer table/raw unit, and resolve as opaque data actions.
- [x] Suspicious instruction decodes offer navigate, create data Manual Seed, and acknowledge actions.
- [x] Manual label/comment unreconciled items offer create Manual Seed, remove annotation, and acknowledge actions.
- [x] Reproduction mismatches offer open comparison, rerun Round-Trip Verification, and acknowledge container-only difference actions when Content Exactness is preserved.
- [x] The UI distinguishes normal open work, resolved work, changed-since-resolution work, and live blockers.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completion

Completed on 2026-05-13.

Implemented a checklist-first Manual Review panel with severity/range sorting, filters for kind/confidence/state/section/source/range, non-mutating navigation, visible state/blocker/changed-since-resolution badges, and structured action buttons. Added a Manual Action Log append endpoint so the UI can create Manual Seeds, remove manual annotations, and resolve/acknowledge review items while invalidating analysis when needed.

Verification:

- `node --check amiga_reversing\web\app.js`
- `uv run python -m pytest tests\test_manual_action_log.py tests\test_manual_review_items.py tests\test_disasm_server.py::test_manual_action_route_appends_action_and_invalidates_analysis -q`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\server.py tests\test_manual_action_log.py tests\test_manual_review_items.py tests\test_disasm_server.py tests\test_web_e2e_cdp.py`
- `uv run mypy amiga_reversing\disasm\manual_actions.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-004 Manual Review Item Generation
- 0001-005 Manual Labels Comments And Label Scope
