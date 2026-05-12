# Builder Stats and Scratch Contract

Type: AFK

## Parent

[001 Arena Builder Primitives](../prd/001-arena-builder-primitives.md)

## Candidate files

- `CONTEXT.md`
- `docs/c-arena-allocation-inventory.md`
- `src/util_arena.c`
- `src/util_arena.h`

## What to build

Document and test the **Arena Builder** contract for allocation stats visibility and **Scratch Mark** conflict avoidance so later migrations share the same ownership rules.

## Acceptance criteria

- [x] Builder use remains visible through arena allocation stats.
- [x] Documentation states how builders interact with Workflow Arenas, Result Arenas, and Scratch Marks.
- [x] Tests or assertions cover the expected finalize and rewind behavior.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `CONTEXT.md` defines Arena Builder and records the no-compatibility-shim rule.
- Builder stats visibility is covered by `test_builder_zero_length_finalize_is_arena_owned`.
- Scratch/rewind behavior is covered by `test_builder_rewind_discards_chunks_and_finalized_storage`.
- Raw heap allocation sites in `src/util_arena.c`: unchanged core arena backing allocations only.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

- [001-001 Generic Arena Builder](001-001-generic-arena-builder.md)
