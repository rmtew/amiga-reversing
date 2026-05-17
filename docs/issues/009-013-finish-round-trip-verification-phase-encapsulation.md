# 009-013 Finish Round-Trip Verification Phase Encapsulation

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## Problem

Proposal 009 wanted round-trip verification to be a deeper workflow module.
Named phase helpers exist, but the main reproduction function still owns most
control flow, report assembly, and phase coordination. That leaves the workflow
only partially encapsulated.

## Scope

- Introduce a round-trip verification workflow object or module boundary around
  direct rebuild, source rendering, source assembly, and comparison.
- Move phase coordination and common report construction out of the large
  reproduction function.
- Keep target metadata, source paths, and binary comparison behavior unchanged.
- Do not preserve internal compatibility layers for old reproduction structure.

## Acceptance Criteria

- The main reproduction entrypoint delegates to a cohesive round-trip workflow
  module.
- Each phase has a small result contract and the workflow owns phase ordering.
- Early-exit and error reports remain behaviorally equivalent.
- Reproduction tests cover direct rebuild, source rendering refusal, assembly
  failure, exact match, and mismatch paths.

## Blocked by

- `docs/issues/009-012-collapse-round-trip-profile-timings-into-workflow-profile.md`

## Required tests

```powershell
uv run python -m pytest tests\test_reproduction.py tests\test_source_rendering.py tests\test_source_export.py -q
```

## Cleanup / deletion

- Delete phase coordination helpers left behind in the old reproduction module
  once the workflow module owns them.

## Implementation notes

- Added `RoundTripVerificationWorkflow` as the owner of the round-trip phase
  ordering body.
- Changed the public `run_reproduction()` entrypoint into a thin delegate to
  the workflow object.
- Kept existing phase helper/result contracts and report behavior intact.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_reproduction.py tests\test_source_rendering.py tests\test_source_export.py -q
uv run python -m pytest tests\test_reproduction.py tests\test_disasm_server.py tests\test_api_workflow_harness.py tests\test_web_app_source.py -q
uv run ruff check amiga_reversing\disasm\reproduction.py tests\test_reproduction.py
```
