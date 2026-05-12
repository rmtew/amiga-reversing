# Decode IR Result Arena

Type: AFK

## Parent

[002 Decode and Facts Result Arenas](../prd/002-decode-facts-result-arena.md)

## Candidate files

- `src/m68k_decode_ir.c`
- decode IR tests in `src/test_m68k_ir.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Move decode IR returned internals to **Result Arena** ownership, using **Arena Builder** growth where decode result construction appends durable arrays.

## Acceptance criteria

- [ ] Decode IR returned arrays are owned by a Result Arena.
- [ ] Destroy tears down the result arena rather than freeing migrated arrays piecemeal.
- [ ] No decode IR returned pointer depends on a Workflow Arena.
- [ ] Before/after notes report raw heap allocation site count changes in touched decode code.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
