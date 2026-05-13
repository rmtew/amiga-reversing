# 0001-011 Replay Undo Redo In File Order

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make Manual Action Log undo and redo projection obey file-order replay exactly. Undo and redo actions must only affect actions that have already been encountered during replay, so the projected manual state is always a state that could be reached by reading the log from top to bottom.

This preserves the Manual Action Log as both durable state and an audit trail, with sequence metadata remaining diagnostic rather than authoritative.

## Acceptance criteria

- [x] Undo can deactivate an earlier active action without deleting history.
- [x] Redo can reactivate an earlier undone action when replay order permits it.
- [x] Undo cannot deactivate a later action that has not been replayed yet.
- [x] Redo cannot reactivate an action before the referenced undo exists in replay order.
- [x] Sequence inconsistencies are reported without changing file-order replay semantics.
- [x] Projection exposes active and inactive action state consistently after ordered undo/redo.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completed

- Undo and redo effects are now computed while walking the Manual Action Log in file order.
- Future action references no longer affect later actions.
- Tests cover normal undo/redo, future undo references, redo-before-undo ordering, and sequence inconsistency behavior.

## Verification

- `uv run python -m pytest tests\test_manual_action_log.py -q`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py tests\test_manual_action_log.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-001 Manual Action Log Projection
