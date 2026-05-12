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

- [x] Render lookup temporary collections use Workflow Arena ownership.
- [x] Nested pass storage is released by scratch rewind where practical.
- [x] No render lookup output depends on rewound scratch storage.
- [x] Before/after notes report raw heap allocation site count changes in touched render lookup code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Typed-flow graph nodes, offset indexes, graph arrays, and global-base observation arrays now allocate from local Workflow Arenas.
- Per-root incoming counts and per-section typed-flow work queues use Scratch Mark rewinds inside the Workflow Arena.
- No render lookup output points into rewound scratch storage; durable lookup output still uses `M68kRenderLookup` result arena helpers.
- Raw heap allocation sites in `src/m68k_analysis_render_lookup.c`: before 17 direct sites (`malloc`, `calloc`, `realloc`, `free`); after 0 direct raw heap sites.
- Regression fixed during migration: zero-candidate typed-flow sections now allocate a one-element arena placeholder so `arena_calloc(0, ...)` cannot be misread as OOM.
- Arena stats: not separately exposed by this workflow; ownership is covered by local Workflow Arena lifetime and existing render/facts tests.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` -> 29 passed.
- Precommit: `cmd /c src\precommit.bat` -> passed.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
