# 015-005: PRD 015 Review and Tightening

## Parent

[PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Review local-first manual edit behavior against PRD 015, ensuring durable log append remains the boundary for visible local updates and asynchronous server work reconciles in place.

## Acceptance criteria

- [ ] No visible local application occurs before successful **Manual Action Log** append.
- [ ] Every manual edit either applies a known local effect or marks an affected region as pending.
- [ ] Asynchronous reconciliation replaces affected rows in place without disruptive loading overlays.
- [ ] Selection, scroll, command, and dialog state are preserved where valid.
- [ ] One-action-at-a-time queue or blocking behavior is clear and tested.
- [ ] Round-trip verification requirements remain intact for source-affecting actions.
- [ ] PRD 015 issue links are accurate.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [015-001: Manual Edit Application Contract](015-001-manual-edit-application-contract.md)
- [015-002: Local-First Visible Action Application](015-002-local-first-visible-action-application.md)
- [015-003: In-Progress Region Reconciliation](015-003-in-progress-region-reconciliation.md)
- [015-004: Manual Edit Queue and Status](015-004-manual-edit-queue-and-status.md)
