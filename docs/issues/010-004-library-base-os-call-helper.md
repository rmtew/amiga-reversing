# 010-004: Library Base OS Call Helper

## Parent

[PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Type

AFK

## What to build

Add helper actions for library-base and OS-call intent so an LVO-style access can drive analysis propagation and symbolic rendering through facts.

## Acceptance criteria

- [ ] Catalog offers OS-call/library-base helper actions only when context evidence is sufficient or explicitly selectable.
- [ ] Chosen action records intent in the **Manual Action Log** and triggers relevant reanalysis.
- [ ] Analysis propagation updates facts consumed by source rendering rather than substituting text directly.
- [ ] Tests cover at least one library-base call path and one rejected/ambiguous path.
- [ ] Round-trip verification is required before review can be marked clear for rendered-source changes.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [010-003: Equate, LVO, and Struct Helper Matching](010-003-equate-lvo-struct-helper-matching.md)
