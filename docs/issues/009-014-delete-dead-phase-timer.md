# 009-014 Delete Dead PhaseTimer

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## Problem

`PhaseTimer` remains in the codebase after `workflow_profile.py` landed, but it
has no production callers. The Proposal 009 deletion checklist explicitly calls
for removing unused timer helpers after the shared workflow profile exists.

## Scope

- Delete the dead `PhaseTimer` helper.
- Remove stale imports or references if any appear during cleanup.
- Keep workflow timing on the shared workflow profile model.

## Acceptance Criteria

- No production module or test imports `PhaseTimer`.
- The dead timer helper file is deleted or reduced only if another live helper
  remains in the same module.
- Workflow profile tests still cover timing behavior.

## Blocked by

- None - can start immediately.

## Required tests

```powershell
uv run python -m pytest tests\test_workflow_profile.py tests\test_reproduction.py -q
```

## Cleanup / deletion

- Delete `PhaseTimer` and any stale docs that describe it as active code.

## Implementation notes

- Deleted the unused `amiga_reversing.disasm.phase_timing` module.
- Updated Proposal 009 so it describes `PhaseTimer` as deleted rather than as a
  possible active adapter.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_workflow_profile.py tests\test_reproduction.py -q
uv run ruff check amiga_reversing\disasm\workflow_profile.py tests\test_workflow_profile.py tests\test_reproduction.py
```
