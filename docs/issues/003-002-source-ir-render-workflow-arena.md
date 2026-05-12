# Source IR Render Workflow Arena

Type: AFK

## Parent

[003 Rendering Workflow Arenas](../prd/003-rendering-workflow-arenas.md)

## Candidate files

- `src/m68k_source_ir_render.c`
- source rendering tests in `src/test_m68k_ir.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Move source IR render temporary indexes, include caches, and section counters into **Workflow Arena** ownership while preserving source rendering output.

## Acceptance criteria

- [x] Source IR render temporary collections use Workflow Arena ownership.
- [x] Scratch Marks bound nested temporary render passes where practical.
- [x] Rendered source behavior remains unchanged.
- [x] Before/after notes report raw heap allocation site count changes in touched source render code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `m68k_source_ir_render_text_with_policy` now creates a local Workflow Arena for render label indexes and symbol include cache storage.
- Temporary label index tables, section label counts, and include cache growth now use `arena_calloc`; destroy paths no longer free migrated temporary arrays individually.
- No public rendered text points into the Workflow Arena: final text is still built through `json_builder_build`.
- Raw heap allocation sites in `src/m68k_source_ir_render.c`: before 10 direct sites (`calloc`, `free`); after 0 direct raw heap sites. Remaining workflow ownership enters through `arena_create` and `arena_calloc`.
- Scratch Mark use: not added in this slice because the migrated temporaries share the full render workflow lifetime and are released by destroying the local Workflow Arena.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
