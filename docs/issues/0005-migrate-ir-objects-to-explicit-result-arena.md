# Migrate IR objects to explicit Result Arena

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Refactor existing arena-backed IR result objects so their ownership is explicit at the interface. Remove surprise nested arenas and update internal callers directly rather than preserving compatibility wrappers.

## Acceptance criteria

- [ ] IR result objects receive or clearly own a **Result Arena** at creation.
- [ ] Internal callers are updated to the new ownership model.
- [ ] Old internal compatibility/fallback create paths are removed.
- [ ] Returned Python/CLI text and byte buffers remain independently freeable.
- [ ] Existing IR/render/source-analysis tests pass.

## Blocked by

- [0002-add-arena-stats-and-tests.md](0002-add-arena-stats-and-tests.md)
