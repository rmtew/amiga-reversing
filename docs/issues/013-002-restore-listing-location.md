# 013-002: Restore Listing Location

## Parent

[PRD 013: UI Preference State and Entrypoint Open](../prd/013-ui-preference-state-and-entrypoint-open.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Restore **Listing Selection** and scroll anchor from **UI Preference State** when opening a project target.

## Acceptance criteria

- [ ] Opening a target restores the last selected row when it can still be resolved.
- [ ] The virtual listing viewport restores the saved scroll anchor.
- [ ] Stale row identity falls back without breaking listing load.
- [ ] Restore behavior uses row identity before row index fallback.
- [ ] Web/CDP tests cover restore after reload.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [013-001: UI Preference State Storage](013-001-ui-preference-state-storage.md)
