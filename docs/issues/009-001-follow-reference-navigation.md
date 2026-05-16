# 009-001: Follow Reference Navigation

## Parent

[PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## Labels

done

## What to build

Add palette-visible and key-bindable follow/back navigation for clear label and equate references from the current **Listing Selection** or **Listing Element**.

## Acceptance criteria

- [x] Follow-reference command appears in the catalog/palette when selection has one clear target.
- [x] Back command returns through the navigation stack.
- [x] Commands show assigned key-binding badges when bound.
- [x] Existing Ctrl-click navigation remains compatible.
- [x] CDP/e2e tests cover follow and back for label/equate references.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-004: Listing Element Selection](007-004-listing-element-selection.md)
- [008-001: Key Binding Registry](008-001-key-binding-registry.md)
