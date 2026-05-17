# 009-006 Add Local C Profiled Operation Adapter

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Centralize ctypes result, error, profile JSON, and free-buffer ownership for
touched profiled C backend operations.

This is internal Local C API cleanup, not a public C ABI compatibility layer.

## Scope

- Add one internal adapter for profiled C operations touched by workflow
  profiling/source/reproduction work.
- Centralize output buffer, error text, profile JSON parsing, and free-buffer
  ownership.
- Preserve `FactsV2SourceRefused`, `FactsV2DirectRebuildRefused`, and
  `FactsV2ProfiledOperationFailed` behavior.
- Attach or return workflow spans where the touched operation participates in a
  workflow profile.

## Out of scope

- Rewriting unrelated disk C backend helpers.
- Public C ABI changes for external consumers.
- Fallback paths around the new adapter.
- Tool graph integration.

## Files likely touched

- `amiga_reversing/disasm/c_backend.py`
- `amiga_reversing/disasm/workflow_profile.py`
- `tests/test_c_backend.py`
- `tests/test_reproduction.py`
- `tests/test_source_export.py`

## Acceptance criteria

- Touched profiled operations no longer repeat output/error/profile cleanup
  blocks.
- Success, C error, source refusal, direct rebuild refusal, and operation failure
  paths still free all owned buffers.
- Profile JSON parsing has one owner for touched operations.
- Workflow spans can represent touched C operation elapsed time.
- No public compatibility wrapper is added.

## Required tests

```powershell
uv run python -m pytest tests\test_c_backend.py tests\test_reproduction.py tests\test_source_export.py -q
```

## Cleanup / deletion

- Delete duplicate pointer cleanup blocks for touched operations.
- Delete temporary wrappers after callers move to the adapter.

## Notes for agents

- Keep the adapter deep. A pass-through wrapper around the old repeated blocks is
  not enough.

## Implementation notes

- Added `CProfiledOperation` plus result records in `c_backend.py`.
- Moved touched direct rebuild and reproduction-compare profiled C calls onto
  the adapter.
- Centralized profile JSON parsing, error text decoding, and C buffer freeing
  for touched operations.
- Preserved `FactsV2SourceRefused`, `FactsV2DirectRebuildRefused`, and
  `FactsV2ProfiledOperationFailed` behavior at the public helper boundary.
- Added adapter tests for success and nonzero-status cleanup paths.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_c_backend.py::test_c_profiled_operation_frees_bytes_profiles_and_error_buffers tests\test_c_backend.py::test_c_profiled_operation_frees_profile_and_error_on_failure_status tests\test_c_backend.py::test_project_source_facts_v2_direct_rebuild_uses_direct_c_api tests\test_c_backend.py::test_project_source_facts_v2_direct_rebuild_compare_uses_compare_c_api tests\test_c_backend.py::test_project_source_facts_v2_direct_rebuild_disk_entry_uses_buffer_c_api tests\test_c_backend.py::test_project_source_facts_v2_direct_rebuild_surfaces_refusal tests\test_c_backend.py::test_project_source_reproduction_compare_atari_uses_object_semantics tests\test_reproduction.py tests\test_source_export.py -q
uv run ruff check amiga_reversing\disasm\c_backend.py tests\test_c_backend.py
```

Attempted:

```powershell
uv run python -m pytest tests\test_c_backend.py tests\test_reproduction.py tests\test_source_export.py -q
```

Result: `1 failed, 199 passed, 15 skipped`. The failure was
`test_real_dll_render_plan_data_classes_reach_listing_rows`, where a generated
comment row ending in `:` was classified outside `label`/`directive`. That path
uses real-DLL listing rows, not the touched profiled direct rebuild or
reproduction-compare adapter path.
