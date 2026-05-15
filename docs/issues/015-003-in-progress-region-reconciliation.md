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

- [x] Pending affected rows or ranges render as change-in-progress without blocking viewport navigation.
- [x] Server-produced replacement rows reconcile into the existing virtual listing position when available.
- [x] **Listing Selection** and scroll anchor are preserved where still valid.
- [x] Lost selection precision is reported rather than silently retargeted.
- [x] Tests cover a pending range that later receives replacement listing rows.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Pending ranges render with `listing-row-manual-pending` while existing listing
refresh reconciliation keeps the current virtual window and selection model.

## Blocked by

- [015-002: Local-First Visible Action Application](015-002-local-first-visible-action-application.md)
