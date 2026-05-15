# 009-002: Ambiguous Reference Navigation

## Parent

[PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## What to build

Handle ambiguous reference navigation by opening or focusing the relevant Navigate dialog detail list instead of silently choosing the wrong target.

## Acceptance criteria

- [ ] Ambiguous references expose a catalog navigation action distinct from direct follow.
- [ ] Ctrl-modified navigation opens or focuses the matching Navigate detail list.
- [ ] The selected reference context is preserved in the detail list where possible.
- [ ] Tests cover ambiguous reference behavior and Escape dismissal compatibility.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [009-001: Follow Reference Navigation](009-001-follow-reference-navigation.md)
