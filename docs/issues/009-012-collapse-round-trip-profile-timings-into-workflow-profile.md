# 009-012 Collapse Round-Trip Profile Timings Into Workflow Profile

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## Problem

Round-trip verification now has phase helpers, but `run_reproduction()` still
maintains a large mutable `profile_timings` dict beside the shared workflow
profile model. This keeps the old profiling contract alive and makes profile
ownership unclear.

## Scope

- Make round-trip verification record phase timings through the shared workflow
  profile contract.
- Keep the existing report payload stable only where current consumers require
  it.
- Move timing merge logic out of the main reproduction orchestration path.
- Keep phase result objects responsible for returning their own profile details.

## Acceptance Criteria

- `run_reproduction()` no longer owns a broad mutable `profile_timings` dict.
- Round-trip phase timing appears in the shared workflow profile.
- Existing CLI and API reports still expose the timing fields consumed by tests
  or UI, derived from the shared profile where needed.
- The reproduction path remains fully round-trip verified.

## Blocked by

- None - can start immediately.

## Required tests

```powershell
uv run python -m pytest tests\test_reproduction.py tests\test_disasm_server.py tests\test_api_workflow_harness.py tests\test_web_app_source.py -q
```

## Cleanup / deletion

- Delete obsolete ad hoc profile merging helpers after their data comes from
  workflow profile spans.

## Implementation notes

- Replaced the local mutable `profile_timings` dict in `run_reproduction()` with
  `RoundTripProfileTimings`, which owns the legacy report payload values.
- `RoundTripProfileTimings` mirrors scalar timing/counter values into
  `workflow_profile.counters`, so round-trip timing is now present in the shared
  workflow profile contract while preserving existing report fields.
- Kept the existing span names stable for current consumers.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_reproduction.py tests\test_disasm_server.py tests\test_api_workflow_harness.py tests\test_web_app_source.py -q
uv run ruff check amiga_reversing\disasm\reproduction.py tests\test_reproduction.py
```

Checked:

```powershell
uv run mypy
```

Mypy still reports existing unrelated project errors; the previous
source-rendering boundary errors remain absent.
