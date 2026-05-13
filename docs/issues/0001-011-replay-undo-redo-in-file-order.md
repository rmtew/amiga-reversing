# 0001-011 Replay Undo Redo In File Order

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make Manual Action Log undo and redo projection obey file-order replay exactly. Undo and redo actions must only affect actions that have already been encountered during replay, so the projected manual state is always a state that could be reached by reading the log from top to bottom.

This preserves the Manual Action Log as both durable state and an audit trail, with sequence metadata remaining diagnostic rather than authoritative.

## Acceptance criteria

- [ ] Undo can deactivate an earlier active action without deleting history.
- [ ] Redo can reactivate an earlier undone action when replay order permits it.
- [ ] Undo cannot deactivate a later action that has not been replayed yet.
- [ ] Redo cannot reactivate an action before the referenced undo exists in replay order.
- [ ] Sequence inconsistencies are reported without changing file-order replay semantics.
- [ ] Projection exposes active and inactive action state consistently after ordered undo/redo.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-001 Manual Action Log Projection

