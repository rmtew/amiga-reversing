# Render Lookup Workflow Arena

Type: AFK

## Parent

[003 Rendering Workflow Arenas](../prd/003-rendering-workflow-arenas.md)

## Candidate files

- `src/m68k_analysis_render_lookup.c`
- render lookup tests in `src/test_m68k_ir.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Move render lookup temporary graph, index, queue, and pass-local storage into a **Workflow Arena** with **Scratch Mark** boundaries where nested passes can rewind.

## Acceptance criteria

- [ ] Render lookup temporary collections use Workflow Arena ownership.
- [ ] Nested pass storage is released by scratch rewind where practical.
- [ ] No render lookup output depends on rewound scratch storage.
- [ ] Before/after notes report raw heap allocation site count changes in touched render lookup code.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
