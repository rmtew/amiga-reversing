# 009-005 Add Round-Trip Verification Phase Module

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Refactor Round-Trip Verification internals into named phases while preserving
the user-facing workflow and report semantics.

The direct Project Rebuild plus Reproduction Comparison path remains the normal
path. Source assembly remains a source gate or debug/comparison path.

## Scope

- Introduce explicit Round-Trip Verification phase ownership.
- Keep one small workflow entrypoint for callers.
- Make direct rebuild, source gate, source assembly debug path, comparison, and
  report construction testable through named workflow seams.
- Preserve C-owned Reproduction Comparison and Python-owned orchestration/report
  responsibilities.
- Preserve workflow profile spans from earlier slices.

## Out of scope

- Changing Reproduction Exactness semantics.
- Making source assembly the normal exactness gate.
- Tool graph or oracle workflow changes.
- Public compatibility layers.

## Files likely touched

- `amiga_reversing/disasm/reproduction.py`
- `amiga_reversing/disasm/reproduction_report.py`
- `amiga_reversing/disasm/source_rendering.py`
- `tests/test_reproduction.py`

## Acceptance criteria

- Callers can still run Round-Trip Verification through one workflow call.
- Tests can exercise direct rebuild, source gate, assembly debug path, and
  comparison/report behavior through named phases or workflow seams.
- Direct Project Rebuild plus Reproduction Comparison remains the normal path.
- Existing reproduction reports remain understandable at the browser edge.
- No external compatibility bridge is added.

## Required tests

```powershell
uv run python -m pytest tests\test_reproduction.py tests\test_disasm_server.py -q
```

## Cleanup / deletion

- Delete phase-local duplicate timing/profile merge code made obsolete by
  workflow profiles.
- Delete dead helper functions after the new phase module owns their behavior.

## Notes for agents

- Respect ADR-0001: C owns Reproduction Comparison; Python owns orchestration,
  reporting, and UI row mapping.

## Implementation notes

- Added named phase result records for direct rebuild, source rendering, source
  assembly, and Reproduction Comparison.
- `run_reproduction()` now calls `run_direct_rebuild_phase()`,
  `run_source_rendering_phase()`, `run_source_assembly_phase()`, and
  `run_reproduction_comparison_phase()`.
- The direct Project Rebuild plus Reproduction Comparison path remains the
  normal path; source assembly remains the debug/source path.
- Focused tests exercise the named phases directly.
- Focused verification passed:
  `uv run python -m pytest tests\test_reproduction.py tests\test_disasm_server.py -q`.
- Lint passed:
  `uv run ruff check amiga_reversing\disasm\reproduction.py tests\test_reproduction.py`.
