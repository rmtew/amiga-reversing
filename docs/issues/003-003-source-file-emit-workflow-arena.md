# Source File Emit Workflow Arena

Type: AFK

## Parent

[003 Rendering Workflow Arenas](../prd/003-rendering-workflow-arenas.md)

## Candidate files

- `src/m68k_source_file_emit.c`
- source file emit tests in `src/test_m68k_ir.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Move source file emission temporary layout arrays, logical offsets, section writers, and intermediate writer buffers into **Workflow Arena** ownership while preserving final caller-owned output behavior.

## Acceptance criteria

- [x] Source file emit temporary collections use Workflow Arena ownership.
- [x] Intermediate writer buffers are not individually heap-freed after migration.
- [x] Public output remains a valid Caller-Freed Output Buffer where required.
- [x] Before/after notes report raw heap allocation site count changes in touched source emit code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `m68k_source_file_layout` now uses a local Workflow Arena for physical and logical section offsets.
- `m68k_source_file_emit_object` now uses a local Workflow Arena for section writer slots; flattened section data is built directly into the output object arena.
- `append_data_ir_statement` now flattens temporary writer bytes directly into the destination source IR section arena.
- Added `m68k_writer_build_arena` for arena-owned flattened writer output while keeping `m68k_writer_build` as the public caller-freed output path.
- Raw heap allocation sites in `src/m68k_source_file_emit.c`: before 27 direct sites (`calloc`, `free`); after 0 direct raw heap sites. Remaining workflow ownership enters through `arena_create` and `arena_calloc`.
- Arena stats: not separately exposed by this workflow; ownership is covered by the local Workflow Arena lifetime and existing source/object emission tests.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
