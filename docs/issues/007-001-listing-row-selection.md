# 007-001: Listing Row Selection

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## What to build

Introduce durable selected-row state for the listing so Review and Navigate jumps set **Listing Selection** instead of only applying a temporary highlight.

## Acceptance criteria

- [ ] The listing tracks one selected row independently from transient focus/highlight.
- [ ] Review item navigation sets selected row.
- [ ] Navigate dialog activation sets selected row.
- [ ] Selected row styling is distinct from temporary jump focus.
- [ ] Web tests cover selection state transitions.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

None - can start immediately
