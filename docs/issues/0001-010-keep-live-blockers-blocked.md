# 0001-010 Keep Live Blockers Blocked

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make hard-blocking Manual Review Items stay blocking while the underlying contradiction is still present. A user may acknowledge that a conflict was seen, but an unchanged live blocker must not be projected as resolved or allow the target to become `clear`.

This should cover the end-to-end path from regenerated review items through manual resolution actions and the checklist UI, so the visible Review State matches the actual blocker state.

## Acceptance criteria

- [x] A Manual Resolution for a non-blocking item can still mark the matching Evidence Fingerprint as resolved.
- [x] A Manual Resolution for a hard-blocking item records the acknowledgement but leaves the item open while the same blocker evidence is still present.
- [x] When the underlying blocker evidence changes or disappears, prior acknowledgement does not hide the new state.
- [x] Checklist UI actions for conflicts make clear that acknowledgement does not clear a live blocker.
- [x] A target with any live hard-blocking Manual Review Item cannot be rated `clear`.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completed

- Manual seed conflicts now explicitly carry `review_blocker`.
- Manual Resolutions mark live blockers as acknowledged while leaving them open.
- Non-blocking review items still resolve normally by matching Evidence Fingerprint.
- The checklist UI labels blocker acknowledgement distinctly and shows acknowledged blockers.

## Verification

- `uv run python -m pytest tests\test_manual_action_log.py -q`
- `node --check amiga_reversing\web\app.js`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py tests\test_manual_action_log.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-004 Manual Review Item Generation
- 0001-006 Checklist Review UI And Suggested Actions
- 0001-007 Review State Rendering Export Warnings
