# 0001-013 Normalize Blocked Review State Projection

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make Review State calculation consistent at the manual projection, project payload, listing, rendering, and export levels. Any live hard-blocking Manual Review Item should produce `blocked` wherever Review State is exposed, not only after a later project-level combination step.

This keeps direct manual-state consumers and project UI consumers from disagreeing about the same target.

## Acceptance criteria

- [x] Manual projection returns `blocked` when any live hard-blocking Manual Review Item exists.
- [x] Manual projection returns `needs_review` when open non-blocking Manual Review Items exist and no live blockers exist.
- [x] Manual projection returns `clear` only when no open review work remains.
- [x] Project listing, detail, rendering, and export warnings agree with manual projection Review State.
- [x] Tests cover direct manual-state payloads and project-level payloads for `clear`, `needs_review`, and `blocked`.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completed

- Manual projection Review State is now calculated from finalized open items with blocker precedence.
- Direct projection tests cover `clear`, `needs_review`, and `blocked`.
- Project payload tests assert blocked manual state is exposed consistently at project level.

## Verification

- `uv run python -m pytest tests\test_manual_action_log.py tests\test_disasm_projects.py -q`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py tests\test_manual_action_log.py tests\test_disasm_projects.py`
- `uv run python -m pytest tests\test_disasm_server.py -q`
- `node --check amiga_reversing\web\app.js`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-010 Keep Live Blockers Blocked
