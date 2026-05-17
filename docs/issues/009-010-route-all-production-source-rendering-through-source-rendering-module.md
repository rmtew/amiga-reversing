# 009-010 Route All Production Source Rendering Through Source Rendering Module

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## Problem

Proposal 009 introduced a source-rendering workflow module, but some production
paths still call the low-level C backend source renderer directly. That keeps
refusal handling, profile shaping, and source-rendering ownership split across
multiple callers.

## Scope

- Route Facts v2 source-gate rendering through the source-rendering module.
- Route oracle compatibility source rendering through the source-rendering
  module where it is part of workflow reporting.
- Route the standalone vasm round-trip tool through the same module or document
  why it is intentionally a lower-level C backend test harness.
- Keep direct low-level calls in C backend tests where they are testing the C
  binding itself.

## Acceptance Criteria

- Production source-rendering callers use the shared source-rendering result
  contract.
- Source-rendering refusal and profile payload shaping have one production
  owner.
- Oracle and source-gate reports preserve their current behavior while using
  the shared module.
- No compatibility adapter is kept for old direct production callers.

## Blocked by

- None - can start immediately.

## Required tests

```powershell
uv run python -m pytest tests\test_source_rendering.py tests\test_source_export.py tests\test_reproduction.py tests\test_oracle_compatibility.py tests\test_vasm_roundtrip.py -q
```

## Cleanup / deletion

- Delete duplicate production source-rendering refusal/profile handling.
- Keep only C backend unit tests calling the low-level renderer directly.

## Implementation notes

- Facts v2 source gate, vasm oracle rendering, and the standalone vasm
  round-trip tool now call the shared source-rendering module.
- Oracle and vasm round-trip paths use the raising source-rendering helper to
  keep refusal-as-failure behavior.
- Source gate uses the non-raising helper so refused source still becomes a gate
  report instead of duplicate exception handling.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_source_rendering.py tests\test_source_export.py tests\test_reproduction.py tests\test_oracle_compatibility.py tests\test_vasm_roundtrip.py -q
uv run ruff check amiga_reversing\disasm\facts_v2_source_gate.py amiga_reversing\disasm\oracle_compatibility.py amiga_reversing\tools\vasm_roundtrip.py tests\test_vasm_roundtrip.py
```
