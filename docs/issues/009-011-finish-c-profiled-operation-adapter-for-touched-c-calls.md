# 009-011 Finish C Profiled Operation Adapter For Touched C Calls

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## Problem

`CProfiledOperation` centralizes some profiled C operations, but source assembly
and source text rendering still contain repeated ctypes output, error, profile
JSON, and free handling. Proposal 009 intended these touched profiled operations
to use one local C API adapter without preserving legacy patterns.

## Scope

- Extend the local C profiled operation adapter to cover text result and
  assembly result shapes.
- Move source text rendering profile parsing into the adapter.
- Move source assembly from path and text profile parsing into the adapter.
- Preserve existing error messages and profile keys where callers consume them.

## Acceptance Criteria

- Touched profiled C calls no longer manually repeat output/error/profile JSON
  cleanup.
- Adapter tests cover bytes, text, profile-only, and assembly result shapes.
- Existing source rendering, source assembly, reproduction, and C backend tests
  pass without compatibility shims.
- C pointer ownership remains local and visibly single-owner.

## Blocked by

- None - can start immediately.

## Required tests

```powershell
uv run python -m pytest tests\test_c_backend.py tests\test_source_rendering.py tests\test_reproduction.py -q
```

## Cleanup / deletion

- Delete repeated `out_profile_json` parsing/free blocks for touched profiled C
  calls.
- Delete helper code made redundant by the adapter.

## Implementation notes

- Added explicit profiled C result shapes for single-profile bytes results and
  text-with-profile results.
- Source path assembly, source text assembly, and listing source rendering now
  route pointer/profile ownership through `CProfiledOperation`.
- The touched duplicate `out_profile_json` cleanup blocks were deleted.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_c_backend.py tests\test_source_rendering.py tests\test_reproduction.py -q
uv run ruff check amiga_reversing\disasm\c_backend.py tests\test_c_backend.py
```
