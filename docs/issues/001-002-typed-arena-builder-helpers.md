# Typed Arena Builder Helpers

Type: AFK

## Parent

[001 Arena Builder Primitives](../prd/001-arena-builder-primitives.md)

## Candidate files

- `src/util_arena.h`
- `src/util_arena.c`
- focused C tests for typed helper usage

## What to build

Add typed helper coverage around the generic **Arena Builder** so struct-array users can adopt it without repeating size, alignment, and length bookkeeping.

## Acceptance criteria

- [x] Typed helpers preserve explicit arena ownership and do not hide heap allocation.
- [x] Helpers support common append and finalize patterns needed by result and workflow migrations.
- [x] Tests cover at least two typed element shapes and zero-element finalize.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Added typed macros in `src/util_arena.h`: `ARENA_BUILDER_INIT_TYPED`, `ARENA_BUILDER_APPEND_TYPED`, and `ARENA_BUILDER_FINALIZE_TYPED`.
- Typed tests cover `uint32_t`, `TestPair`, and zero-element finalize.
- Raw heap allocation sites in `src/util_arena.c`: unchanged core arena backing allocations only.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

- [001-001 Generic Arena Builder](001-001-generic-arena-builder.md)
