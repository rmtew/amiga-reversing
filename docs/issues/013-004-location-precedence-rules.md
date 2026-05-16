# 013-004: Location Precedence Rules

## Parent

[PRD 013: UI Preference State and Entrypoint Open](../prd/013-ui-preference-state-and-entrypoint-open.md)

## Related PRDs

- [PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## Labels

done

## What to build

Apply deterministic location precedence so explicit URL anchors and navigation commands win over restored preferences, which win over first-open entrypoint fallback.

## Acceptance criteria

- [x] URL or route anchors override restored **UI Preference State**.
- [x] Explicit navigation commands override restored preference state.
- [x] Restored preference state overrides entrypoint fallback.
- [x] Entrypoint fallback runs only when no explicit or persisted location exists.
- [x] Tests cover all precedence branches.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Progress

Completed 2026-05-16. Web logic applies explicit URL location, saved preference, then entrypoint fallback; navigation commands remain explicit runtime actions.

## Blocked by

- [013-003: First Open Entrypoint Selection](013-003-first-open-entrypoint-selection.md)
