# Facts IR Result Arena

Type: AFK

## Parent

[002 Decode and Facts Result Arenas](../prd/002-decode-facts-result-arena.md)

## Candidate files

- `src/m68k_fact_ir.c`
- facts IR tests in `src/test_m68k_ir.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Move facts IR append storage to **Result Arena** ownership, replacing heap-owned growth with the shared **Arena Builder** pattern.

## Acceptance criteria

- [x] Facts IR returned arrays are owned by a Result Arena.
- [x] Destroy tears down the result arena rather than freeing migrated arrays piecemeal.
- [x] No facts IR returned pointer depends on a Workflow Arena.
- [x] Before/after notes report raw heap allocation site count changes in touched facts code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `M68kFactIR` now owns a result arena; fact append storage grows with arena-owned copies.
- Destroy now tears down the result arena and no longer frees the fact array individually.
- Raw heap allocation sites in `src/m68k_fact_ir.c`: before 2 direct sites (`realloc`, `free`); after 0 direct raw heap sites. Remaining result ownership enters through `arena_create` and `arena_realloc_copy`.
- Arena stats: `test_fact_ir_result_arrays_use_result_arena` asserts non-zero `arena_stats(facts.arena).current_used` after appending a fact.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
