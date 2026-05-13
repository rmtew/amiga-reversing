# 0001-001 Manual Action Log Projection

## Parent

PRD 0001: Manual Review Workflow

## What to build

Build the first end-to-end Manual Action Log path. A target with no log has empty manual state. A target with a header-only log has empty manual state with pinned Target Identity. Ordered log actions project into current Manual Seeds, Manual Resolutions, Manual Labels, and Manual Comments. Sequence metadata is diagnostic only; file order is replay order.

This slice should expose projected manual state through the same project/listing path that analysis and UI will later consume, even if most action kinds initially project to inert state.

## Acceptance criteria

- [ ] Missing Manual Action Log loads as empty manual state.
- [ ] Header-only Manual Action Log loads as empty manual state with pinned Target Identity.
- [ ] Action entries carry action id, sequence, timestamp, and optional undo relationship metadata.
- [ ] Replay follows file order and reports sequence inconsistencies without changing replay order.
- [ ] Undo actions project the prior action as inactive without deleting history.
- [ ] Redo or compensating actions can restore a previously undone effect.
- [ ] Projection exposes active and inactive action state for audit/debug output.
- [ ] Malformed or unprojectable logs set Review State to `blocked`.
- [ ] Target Identity mismatch is detected during log/header validation, prevents log projection, and emits a target-level `manual_action_log_target_mismatch` item from validation.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

None - can start immediately
