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

- [ ] Output boundary tests or assertions cover at least one migrated render path.
- [ ] Workflow Arena reset/destroy cannot invalidate public render output.
- [ ] Source rendering, project rebuild, and round-trip behavior remain unchanged.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [003-001 Render Lookup Workflow Arena](003-001-render-lookup-workflow-arena.md)
- [003-002 Source IR Render Workflow Arena](003-002-source-ir-render-workflow-arena.md)
- [003-003 Source File Emit Workflow Arena](003-003-source-file-emit-workflow-arena.md)
