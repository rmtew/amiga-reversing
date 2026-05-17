# 009-004 Add Source Rendering Workflow Module

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Move Source Rendering result, refusal, and profile ownership behind a dedicated
workflow module consumed by Source Export and the Round-Trip Verification source
gate.

Source Export should still own export filenames and headers; the rendering
module should own renderer invocation, source-rendering spans, and refusal
interpretation.

## Scope

- Add a Source Rendering workflow module returning a structured rendering
  result.
- Route Source Export through the new module.
- Route the Round-Trip Verification source gate through the new module.
- Preserve target identity and metadata hash reporting.
- Preserve facts-v2 source refusal behavior through one owner.

## Out of scope

- Splitting all Round-Trip Verification phases.
- Local C API adapter cleanup beyond renderer calls touched here.
- Browser save-flow changes.
- Tool graph integration.

## Files likely touched

- `amiga_reversing/disasm/source_rendering.py`
- `amiga_reversing/disasm/source_export.py`
- `amiga_reversing/disasm/reproduction.py`
- `tests/test_source_export.py`
- `tests/test_reproduction.py`

## Acceptance criteria

- `source_export.py` no longer calls C backend source rendering directly.
- The Round-Trip Verification source gate no longer calls C backend source
  rendering directly.
- Renderer refusal/profile parsing has one owner.
- Source Export still returns its non-verification header and browser-delivered
  source text.
- Source-rendering workflow profiles remain available to callers.

## Required tests

```powershell
uv run python -m pytest tests\test_source_export.py tests\test_reproduction.py -q
```

## Cleanup / deletion

- Delete duplicate Source Rendering refusal/profile handling from callers.
- Keep Source Export-specific header/filename logic in Source Export.

## Notes for agents

- Do not turn this into a broad reproduction rewrite. This issue deepens Source
  Rendering only.

## Implementation notes

- Added `amiga_reversing/disasm/source_rendering.py` with
  `SourceRenderingResult` and source-rendering helpers.
- Source Rendering now owns the C renderer call, listing profile, refusal
  interpretation, metadata hash, target identity hash, and `source_rendering`
  workflow span.
- `source_export.py` no longer calls C backend source rendering directly.
- `reproduction.py` source rendering paths no longer call C backend source
  rendering directly.
- Focused verification passed:
  `uv run python -m pytest tests\test_source_rendering.py tests\test_source_export.py tests\test_reproduction.py -q`.
- Lint passed:
  `uv run ruff check amiga_reversing\disasm\source_rendering.py amiga_reversing\disasm\source_export.py amiga_reversing\disasm\reproduction.py tests\test_source_rendering.py tests\test_source_export.py tests\test_reproduction.py`.
