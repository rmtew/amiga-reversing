# 0001-007 Review State Rendering Export Warnings

## Parent

PRD 0001: Manual Review Workflow

## What to build

Carry Review State through listing, rendering, reproduction, and export workflows. `blocked` prevents the target from being rated `clear`, but it is not a generic UI or export lock. Viewing, analysis, rendering, and export remain available when meaningful, with warnings explaining live blockers.

## Acceptance criteria

- [x] Listing and project views show Review State consistently.
- [x] Blocked targets can still be viewed and rendered when target identity is valid.
- [x] Exports and reports include warnings for blocked or needs-review targets.
- [x] Target identity mismatch remains fatal for that project target and prevents applying manual state.
- [x] Round-trip verification output feeds reproduction mismatch review state.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completed

- Review State badges render on project list and project detail views.
- Listing, project, and reproduction payloads include `review_warnings` for `blocked` and `needs_review` targets.
- Manual Action Log appends now reject stale target identity instead of adding actions to the wrong target log.
- Blocked targets with valid identity remain viewable/renderable; target-identity mismatch remains a blocking review item and does not project manual state.

## Verification

- `node --check amiga_reversing\web\app.js`
- `uv run python -m pytest tests\test_manual_action_log.py::test_append_manual_action_rejects_target_identity_mismatch tests\test_disasm_server.py::test_route_project_reproduction_and_listing_include_review_warnings -q`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\api.py amiga_reversing\disasm\server.py tests\test_manual_action_log.py tests\test_disasm_server.py tests\test_web_e2e_cdp.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-004 Manual Review Item Generation
- 0001-006 Checklist Review UI And Suggested Actions
