# Render Output Boundary Guards

Type: AFK

## Parent

[003 Rendering Workflow Arenas](../prd/003-rendering-workflow-arenas.md)

## Candidate files

- `src/m68k_source_ir_api.c`
- `src/m68k_source_ir_render.c`
- `src/m68k_source_file_emit.c`
- source rendering tests in `src/test_m68k_ir.c`

## What to build

Add regression coverage or assertions that rendered public outputs remain **Caller-Freed Output Buffers** and never point into a **Workflow Arena** after rendering migrations.

## Acceptance criteria

- [x] Output boundary tests or assertions cover at least one migrated render path.
- [x] Workflow Arena reset/destroy cannot invalidate public render output.
- [x] Source rendering, project rebuild, and round-trip behavior remain unchanged.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Added `test_source_file_renderer_output_survives_source_destroy` in `src/test_m68k_ir.c`.
  The test renders a full source file through `m68k_source_ir_render_text_with_policy`, destroys the
  source-file result arena, then verifies and frees the returned text.
- Raw heap allocation sites before/after:
  - `src/m68k_source_ir_render.c`: unchanged, 0 direct raw heap sites in the migrated render path.
  - `src/m68k_source_file_emit.c`: unchanged, 0 direct raw heap sites.
  - `src/m68k_source_ir_api.c`: unchanged, caller-freed output boundary remains at `m68k_source_ir_free_text`.
  - `src/test_m68k_ir.c`: test-only caller output cleanup adds one `free(text)` site.
- Arena stats: none exposed by the source IR render workflow; coverage verifies lifetime by destroying
  the source-file arena before inspecting returned text.
- `cmd /c src\precommit.bat`: passed. Summary: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: passed, `29 passed in 93.06s`.

## Blocked by

- [003-001 Render Lookup Workflow Arena](003-001-render-lookup-workflow-arena.md)
- [003-002 Source IR Render Workflow Arena](003-002-source-ir-render-workflow-arena.md)
- [003-003 Source File Emit Workflow Arena](003-003-source-file-emit-workflow-arena.md)
