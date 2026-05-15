# 009-001: Follow Reference Navigation

## Parent

[PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## What to build

Add palette-visible and key-bindable follow/back navigation for clear label and equate references from the current **Listing Selection** or **Listing Element**.

## Acceptance criteria

- [ ] Follow-reference command appears in the catalog/palette when selection has one clear target.
- [ ] Back command returns through the navigation stack.
- [ ] Commands show assigned key-binding badges when bound.
- [ ] Existing Ctrl-click navigation remains compatible.
- [ ] CDP/e2e tests cover follow and back for label/equate references.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [007-004: Listing Element Selection](007-004-listing-element-selection.md)
- [008-001: Key Binding Registry](008-001-key-binding-registry.md)
