# 009-003: Relative Navigation Commands

## Parent

[PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## What to build

Add palette-visible previous/next label and previous/next hunk navigation commands with optional default key bindings.

## Acceptance criteria

- [ ] Previous/next label commands move selection and viewport to the expected label rows.
- [ ] Previous/next hunk commands move selection and viewport to the expected hunk boundaries.
- [ ] Commands are filterable in the command palette and show binding badges when bound.
- [ ] Tests cover relative movement from middle, first, and last eligible positions.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [009-001: Follow Reference Navigation](009-001-follow-reference-navigation.md)
