# 007-001: Listing Row Selection

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

done

## What to build

Introduce durable selected-row state for the listing so Review and Navigate jumps set **Listing Selection** instead of only applying a temporary highlight.

## Acceptance criteria

- [x] The listing tracks one selected row independently from transient focus/highlight.
- [x] Review item navigation sets selected row.
- [x] Navigate dialog activation sets selected row.
- [x] Selected row styling is distinct from temporary jump focus.
- [x] Web tests cover selection state transitions.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

None - can start immediately
