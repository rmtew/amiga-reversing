# 013-005: PRD 013 Review and Tightening

## Parent

[PRD 013: UI Preference State and Entrypoint Open](../prd/013-ui-preference-state-and-entrypoint-open.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## Labels

done

## What to build

Review **UI Preference State** and first-open entrypoint behavior against PRD 013, then close gaps or create follow-up issues.

## Acceptance criteria

- [x] Preference state remains separate from **Manual Action Log** and analysis metadata.
- [x] Listing restore and first-open entrypoint behavior match the precedence rules.
- [x] Stale preference handling is tested.
- [x] CDP coverage proves entrypoint centering.
- [x] PRD 013 issue links are accurate.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Progress

Completed 2026-05-16. Review found and fixed an explicit-location parsing bug where missing URL parameters were treated as row `0`.

## Blocked by

- [013-001: UI Preference State Storage](013-001-ui-preference-state-storage.md)
- [013-002: Restore Listing Location](013-002-restore-listing-location.md)
- [013-003: First Open Entrypoint Selection](013-003-first-open-entrypoint-selection.md)
- [013-004: Location Precedence Rules](013-004-location-precedence-rules.md)
