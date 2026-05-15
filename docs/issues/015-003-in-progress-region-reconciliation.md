# 015-003: In-Progress Region Reconciliation

## Parent

[PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

For manual edits whose final listing shape needs server processing, keep the affected visible rows or ranges in place as change-in-progress and reconcile replacement rows in situ when analysis/rendering returns.

## Acceptance criteria

- [ ] Pending affected rows or ranges render as change-in-progress without blocking viewport navigation.
- [ ] Server-produced replacement rows reconcile into the existing virtual listing position when available.
- [ ] **Listing Selection** and scroll anchor are preserved where still valid.
- [ ] Lost selection precision is reported rather than silently retargeted.
- [ ] Tests cover a pending range that later receives replacement listing rows.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [015-002: Local-First Visible Action Application](015-002-local-first-visible-action-application.md)
