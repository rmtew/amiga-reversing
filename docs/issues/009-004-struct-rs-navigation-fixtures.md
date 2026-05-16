# 009-004: Struct and RS Navigation Fixtures

## Parent

[PRD 009: Symbol, Equate, and Struct Navigation](../prd/009-symbol-equate-struct-navigation.md)

## Type

AFK

## Labels

done

## What to build

Cover struct and RS-style references in navigation fixtures so the keyboard and palette navigation paths are verified beyond labels and equates.

## Acceptance criteria

- [x] Test fixtures include at least one struct or RS-style reference when supported by current analysis output.
- [x] Navigation commands can identify and follow or open details for the fixture reference.
- [x] If current fixtures cannot support this honestly, document the missing analysis prerequisite and create a follow-up issue.
- [x] Tests cover the supported struct/RS-style path or the documented prerequisite.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [009-001: Follow Reference Navigation](009-001-follow-reference-navigation.md)
