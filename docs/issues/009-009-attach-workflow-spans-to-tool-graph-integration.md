# 009-009 Attach Workflow Spans To Tool Graph Integration

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Attach workflow spans to tool capability resolution and oracle invocation chains
using the completed Proposal 008 Slice 1 tool graph capability-resolution
surface.

This issue does not wait on the rest of Proposal 008. It depends only on the
completed `008-001` surface and on Proposal 009's shared workflow profile
records.

## Scope

- Add workflow profile spans around capability resolution.
- Add workflow profile spans around oracle invocation chains.
- Include tool graph input stamps or probe evidence summaries in workflow
  profile detail where useful.
- Keep tool graph query routes as resource routes.

## Out of scope

- Designing or replacing the tool graph.
- Browser tool path configuration.
- Making external tools part of Reproduction Exactness.
- WinUAE automation.

## Files likely touched

- `amiga_reversing/disasm/tool_graph.py`
- `amiga_reversing/disasm/oracle_compatibility.py`
- `amiga_reversing/disasm/reproduction.py`
- `amiga_reversing/disasm/workflow_profile.py`
- `tests/test_tool_graph.py`
- `tests/test_oracle_compatibility.py`

## Acceptance criteria

- Oracle reports can show tool capability resolution and invocation timing
  through the shared workflow profile contract.
- Capability resolution spans include enough detail to distinguish missing
  artifact, missing runtime, unsupported, and error states.
- Oracle invocation spans include selected functional tool and runtime chain
  identity where available.
- Tool graph query routes remain resource routes.

## Blocked by

- Completed `docs/issues/008-001-replace-flat-tool-registry-with-tool-graph.md`
  capability-resolution surface:
  - stable capability ids
  - deterministic selected chain plus candidates
  - runnable/artifact status
  - missing runtime ids
  - probe evidence
  - oracle code able to consume resolved invocation chains
- `docs/issues/009-001-add-shared-workflow-profile-records.md`

## Required tests

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_oracle_compatibility.py tests\test_reproduction.py -q
```

## Cleanup / deletion

- Delete ad hoc oracle/tool timing once the shared workflow profile covers it.

## Notes for agents

- Do not wait on compiler fingerprint fixtures, WinUAE automation, browser tool
  path configuration, or other later Proposal 008 scope.

## Implementation notes

- Confirmed blocker `008-001` is implemented and `008-002` already has oracle
  code consuming selected invocation chains.
- Oracle compatibility reports now include `workflow_profile`.
- Capability resolution is timed as `tool_capability_resolution` with selected
  and candidate status summaries from the tool graph.
- Actual oracle runs add `oracle_invocation` spans with oracle id, source
  profile, selected functional tool, runtime tool, and chain identity.
- Missing capability/runtime reports include the resolution span and no
  invocation span.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_oracle_compatibility.py tests\test_reproduction.py -q
uv run ruff check amiga_reversing\disasm\oracle_compatibility.py tests\test_oracle_compatibility.py
```
