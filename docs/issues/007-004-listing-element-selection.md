# 007-004: Listing Element Selection

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

done

## What to build

Add optional **Listing Element** targeting inside the selected row so operand, symbol, value, equate, comment, and literal actions can address the right semantic element.

## Acceptance criteria

- [x] Selectable elements expose stable semantic ids or fallback identity.
- [x] Element selection feeds row/element **Manual Action Catalog** context.
- [x] Actions that need element precision do not silently run against the wrong row-level target.
- [x] If a selected element disappears after refresh, selection falls back to row and reports precision loss.
- [x] Tests cover selecting at least operand/value and symbol/equate-style elements.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-001: Listing Row Selection](007-001-listing-row-selection.md)
- [006-003: Target and Listing Action Contexts](006-003-target-and-listing-action-contexts.md)
