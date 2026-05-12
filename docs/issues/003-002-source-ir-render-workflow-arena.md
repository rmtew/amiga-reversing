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

- [ ] Source IR render temporary collections use Workflow Arena ownership.
- [ ] Scratch Marks bound nested temporary render passes where practical.
- [ ] Rendered source behavior remains unchanged.
- [ ] Before/after notes report raw heap allocation site count changes in touched source render code.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
