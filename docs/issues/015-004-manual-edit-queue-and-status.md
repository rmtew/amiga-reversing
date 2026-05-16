# 015-004: Manual Edit Queue and Status

## Parent

[PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

done

## What to build

Keep manual edit concurrency simple by allowing one in-flight manual action per target, with later edits queued or explicitly blocked while navigation remains usable.

## Acceptance criteria

- [x] The UI tracks one in-flight manual edit per target.
- [x] A second manual edit is queued or blocked with clear status rather than racing the first edit.
- [x] Pending work can expose cancel, pause, or retry only where the backend can honor that state.
- [x] Navigation through the listing remains available while an edit is pending.
- [x] Tests cover second-action behavior while a first action is pending.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

The first slice blocks a second manual edit with `Manual edit already in
progress`; no unsupported cancel/pause/retry controls are exposed.

## Blocked by

- [015-003: In-Progress Region Reconciliation](015-003-in-progress-region-reconciliation.md)
