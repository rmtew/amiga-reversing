# 009-001 Add Shared Workflow Profile Records

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Add the shared workflow profile contract and prove it on the smallest useful
end-to-end paths: Source Export and the normal Round-Trip Verification direct
path.

This should make workflow spans a stable report/API shape without adding
unrelated timer dictionaries or compatibility wrappers.

## Scope

- Add a Python-owned workflow profile module for stable span records.
- Add a source-rendering span to Source Export results.
- Add direct rebuild and Reproduction Comparison spans to Round-Trip
  Verification reports for the direct path.
- Keep detailed C profile payloads as detail under the shared workflow envelope
  where useful.
- Update in-repo callers/tests that inspect the new profile shape.

## Out of scope

- Refactoring Source Rendering into its own workflow module.
- Splitting `run_reproduction()` internals.
- Browser/backend request correlation.
- Hard timing thresholds.
- Tool graph or oracle capability spans.

## Files likely touched

- `amiga_reversing/disasm/workflow_profile.py`
- `amiga_reversing/disasm/source_export.py`
- `amiga_reversing/disasm/reproduction.py`
- `tests/test_source_export.py`
- `tests/test_reproduction.py`

## Acceptance criteria

- Source Export payloads include `workflow_profile` with a `source_rendering`
  span.
- Round-Trip Verification direct-path reports include `workflow_profile` with
  direct rebuild and Reproduction Comparison spans.
- Workflow profile serialization is stable and covered by tests.
- Existing in-repo report consumers are updated directly; no external
  compatibility bridge is added.
- Tests assert span shape and attribution, not wall-clock thresholds.

## Required tests

```powershell
uv run python -m pytest tests\test_source_export.py tests\test_reproduction.py -q
```

## Cleanup / deletion

- Delete or fold unused `PhaseTimer` behavior if the new module replaces it.
- Remove ad hoc profile merging helpers only when their replacement is covered.

## Notes for agents

- Keep this slice small. Do not start the larger Source Rendering or
  Round-Trip Verification refactor here.
- The profile is observability, not a second control interface.

## Implementation notes

- Added `amiga_reversing/disasm/workflow_profile.py` with stable
  `WorkflowProfile` / `WorkflowSpan` serialization.
- Source Export now returns `workflow_profile` with a `source_rendering` span.
- Round-Trip Verification direct rebuild reports now include `workflow_profile`
  spans for `direct_rebuild` and `reproduction_compare`.
- Focused verification passed:
  `uv run python -m pytest tests\test_workflow_profile.py tests\test_source_export.py tests\test_reproduction.py -q`.
