# Migrate source model to Result Arena

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Convert the source model to explicit **Result Arena** ownership. Source model arrays, statements, symbols, data items, and metadata buffers should be owned by one result lifetime instead of separate allocation/free paths.

## Acceptance criteria

- [x] Source model construction requires explicit result ownership.
- [x] Source model append paths use arena-backed growth or equivalent result-owned storage.
- [x] Deep per-field cleanup is removed where the **Result Arena** owns the memory.
- [x] No compatibility/fallback ownership path remains for old internal callers.
- [x] Existing source parsing, assembly, and C tests pass.

## Blocked by

- [0002-add-arena-stats-and-tests.md](0002-add-arena-stats-and-tests.md)
