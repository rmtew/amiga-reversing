# 007-002: Selection Keyboard Navigation

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## What to build

Make keyboard movement operate on **Listing Selection**: Up/Down moves the selected row, while Home/End/PageUp/PageDown move the viewport without changing selection.

## Acceptance criteria

- [ ] Up and Down move selected row by one listing row.
- [ ] Home, End, PageUp, and PageDown preserve selected row while moving the viewport.
- [ ] Keyboard handling does not steal input from editable controls or open dialogs.
- [ ] CDP/e2e tests cover row movement and viewport-only movement.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-001: Listing Row Selection](007-001-listing-row-selection.md)
