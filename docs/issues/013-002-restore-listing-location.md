# 013-002: Restore Listing Location

## Parent

[PRD 013: UI Preference State and Entrypoint Open](../prd/013-ui-preference-state-and-entrypoint-open.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

done

## What to build

Restore **Listing Selection** and scroll anchor from **UI Preference State** when opening a project target.

## Acceptance criteria

- [x] Opening a target restores the last selected row when it can still be resolved.
- [x] The virtual listing viewport restores the saved scroll anchor.
- [x] Stale row identity falls back without breaking listing load.
- [x] Restore behavior uses row identity before row index fallback.
- [x] Web/CDP tests cover restore after reload.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Progress

Completed 2026-05-16. CDP covers selecting a row, saving UI preference state, and restoring it after reload.

## Blocked by

- [013-001: UI Preference State Storage](013-001-ui-preference-state-storage.md)
