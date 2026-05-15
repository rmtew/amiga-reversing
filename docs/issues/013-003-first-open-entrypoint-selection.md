# 013-003: First Open Entrypoint Selection

## Parent

[PRD 013: UI Preference State and Entrypoint Open](../prd/013-ui-preference-state-and-entrypoint-open.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Select and center the source entrypoint row on first open when no explicit anchor or stored **UI Preference State** location exists.

## Acceptance criteria

- [ ] First open reads the source entrypoint from the target source descriptor.
- [ ] The matching listing row is selected and centered in the virtual viewport.
- [ ] Missing entrypoint row falls back safely to current listing start behavior.
- [ ] The selected entrypoint is UI state only, not a **Manual Action Log** entry.
- [ ] CDP coverage proves first-open selection and centering.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [013-002: Restore Listing Location](013-002-restore-listing-location.md)
