Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Add shared workflow helpers that prove persistent UI workflows through durable state reload and listing projection without a browser. The helpers must also be usable by later CDP tests and LLM-driven browser verification after browser actions.

## Acceptance criteria

- [x] API helpers can run representative mutation/preference workflows from action through project reload and projection assertion.
- [x] Assertions cover Manual Action Log count/head hash, effective metadata, projected listing rows, review state where relevant, and repaired/stale locator behavior.
- [x] Tests use `ListingProjectionService` helpers instead of patching private server globals.
- [x] Failures identify whether durable state, projection, or locator recovery diverged.
- [x] Assertion helpers are not tied to direct API calls; CDP tests can reuse the same semantic assertions with browser-collected debug state.
- [x] Assertion helpers can consume server debug state plus browser debug state snapshots so an LLM-driven verification flow can reuse the same checks instead of inventing a DOM-only oracle.

## Files likely touched

- `tests/` workflow helper module
- API workflow tests
- service/debug helper tests

## Blocked by

- docs/issues/028-006-delete-target-ui-edits-and-unify-mutation-execution.md

## Required tests

- Representative API workflow tests for mutation and preference workflows.
- Helper-level test using debug-state-shaped input rather than direct route return payloads.

## Implementation

- Added `tests/workflow_harness.py` semantic assertion helpers for manual mutation and preference snapshots.
- Added API workflow coverage for Manual Action Log mutation, stale locator recovery, project reload, listing projection, review state, UI preference reload, and debug-state-shaped snapshots.
