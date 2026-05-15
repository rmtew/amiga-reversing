# 009-005: PRD 009 Review and Tightening

## Parent

[PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## What to build

Review the completed PRD 009 navigation work, identify missed reference types, confusing key behavior, over-complicated navigation state, or weak fixtures, and address them directly or split follow-up issues.

## Acceptance criteria

- [ ] Review follow/back, ambiguous references, relative navigation, struct/RS fixtures, palette visibility, and tests against PRD 009.
- [ ] Simplify duplicated or fragile navigation behavior found during review.
- [ ] Add missing tests or issue follow-ups for broader gaps.
- [ ] PRD 009 links and issue statuses remain accurate after review.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [009-001: Follow Reference Navigation](009-001-follow-reference-navigation.md)
- [009-002: Ambiguous Reference Navigation](009-002-ambiguous-reference-navigation.md)
- [009-003: Relative Navigation Commands](009-003-relative-navigation-commands.md)
- [009-004: Struct and RS Navigation Fixtures](009-004-struct-rs-navigation-fixtures.md)
