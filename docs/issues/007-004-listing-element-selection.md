# 007-004: Listing Element Selection

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## What to build

Add optional **Listing Element** targeting inside the selected row so operand, symbol, value, equate, comment, and literal actions can address the right semantic element.

## Acceptance criteria

- [ ] Selectable elements expose stable semantic ids or fallback identity.
- [ ] Element selection feeds row/element **Manual Action Catalog** context.
- [ ] Actions that need element precision do not silently run against the wrong row-level target.
- [ ] If a selected element disappears after refresh, selection falls back to row and reports precision loss.
- [ ] Tests cover selecting at least operand/value and symbol/equate-style elements.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-001: Listing Row Selection](007-001-listing-row-selection.md)
- [006-003: Target and Listing Action Contexts](006-003-target-and-listing-action-contexts.md)
