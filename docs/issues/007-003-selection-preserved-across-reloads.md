# 007-003: Selection Preserved Across Reloads

## Parent

[PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

done

## What to build

Preserve **Listing Selection** across virtual listing fetches and reanalysis refreshes when the selected row can still be identified.

## Acceptance criteria

- [x] Selection persists across listing window reloads using stable row identity where available.
- [x] Selection falls back predictably when the row no longer exists.
- [x] Manual action refreshes preserve selection when possible.
- [x] Tests cover virtual reload and reanalysis refresh behavior.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-001: Listing Row Selection](007-001-listing-row-selection.md)
