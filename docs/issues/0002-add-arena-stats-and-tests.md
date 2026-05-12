# Add arena stats and tests

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Extend the core arena with minimal memory counters and focused tests while preserving the current linked-block growth model. This gives later workflow/result migrations evidence about arena sizing and waste.

## Acceptance criteria

- [ ] Arena exposes current usage, peak usage, and block allocation counters.
- [ ] Arena allocation still returns `NULL` on failure and does not own diagnostics.
- [ ] Tests cover stats, mark/rewind, reset, destroy, and block growth.
- [ ] Existing C precommit or build tests pass.

## Blocked by

- [0001-classify-c-allocation-lifetimes.md](0001-classify-c-allocation-lifetimes.md)
