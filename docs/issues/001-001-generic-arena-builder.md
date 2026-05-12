# Generic Arena Builder

Type: AFK

## Parent

[001 Arena Builder Primitives](../prd/001-arena-builder-primitives.md)

## Candidate files

- `src/util_arena.c`
- `src/util_arena.h`
- `src/test_m68k_ir.c` or a focused C test file

## What to build

Add a generic **Arena Builder** for append-style collection growth that allocates only from an explicit arena and finalizes into arena-owned contiguous storage. Use the PRD's append-chunks with flatten-on-finalize model.

## Acceptance criteria

- [x] Builder supports append, growth, zero-length finalize, and bulk copy into arena-owned storage.
- [x] Builder uses append chunks with flatten-on-finalize unless the PRD is updated.
- [x] Finalized storage has no per-buffer free path.
- [x] Tests cover growth and reset/destroy behavior with both workflow-style and result-style arenas.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Implemented in `src/util_arena.c` and `src/util_arena.h`.
- Raw heap allocation sites in `src/util_arena.c`: unchanged core arena backing allocations only; builder chunks and finalized arrays allocate through `arena_alloc`.
- Arena stats visibility: `test_builder_zero_length_finalize_is_arena_owned` asserts builder finalize increases `arena_stats(...).current_used`; rewind/reset tests assert arena-owned lifetime.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

None - can start immediately.
