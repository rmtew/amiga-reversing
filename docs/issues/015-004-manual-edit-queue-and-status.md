# 015-004: Manual Edit Queue and Status

## Parent

[PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Keep manual edit concurrency simple by allowing one in-flight manual action per target, with later edits queued or explicitly blocked while navigation remains usable.

## Acceptance criteria

- [ ] The UI tracks one in-flight manual edit per target.
- [ ] A second manual edit is queued or blocked with clear status rather than racing the first edit.
- [ ] Pending work can expose cancel, pause, or retry only where the backend can honor that state.
- [ ] Navigation through the listing remains available while an edit is pending.
- [ ] Tests cover second-action behavior while a first action is pending.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [015-003: In-Progress Region Reconciliation](015-003-in-progress-region-reconciliation.md)
