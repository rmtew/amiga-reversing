# 007-003: Selection Preserved Across Reloads

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## What to build

Preserve **Listing Selection** across virtual listing fetches and reanalysis refreshes when the selected row can still be identified.

## Acceptance criteria

- [ ] Selection persists across listing window reloads using stable row identity where available.
- [ ] Selection falls back predictably when the row no longer exists.
- [ ] Manual action refreshes preserve selection when possible.
- [ ] Tests cover virtual reload and reanalysis refresh behavior.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-001: Listing Row Selection](007-001-listing-row-selection.md)
