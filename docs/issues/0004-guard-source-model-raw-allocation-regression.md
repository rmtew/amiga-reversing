# Guard source model raw allocation regression

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Add a staged source-scan guard for the migrated source model so new raw allocation calls cannot silently re-enter result-owned code.

## Acceptance criteria

- [ ] The guard checks migrated source model files for unapproved raw allocation calls.
- [ ] The guard is narrow and does not globally ban heap allocation.
- [ ] Approved output-edge or test-only exceptions are documented in the guard.
- [ ] The guard runs in the normal C precommit/build workflow.

## Blocked by

- [0003-migrate-source-model-to-result-arena.md](0003-migrate-source-model-to-result-arena.md)
