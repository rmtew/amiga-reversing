# 008-004 Make Runnable Availability Mean Executable

Status: Done
Source proposal: `docs/proposals/008-tool-runtime-capability-graph.md`
Created: 2026-05-17

## Problem

The tool graph marks any existing non-directory file as `available`. That is
artifact presence, not runnable availability.

For native-host tools and runtime tools, user-facing availability must mean the
tool can be executed enough for the requested capability or runtime role.

## Scope

- Split artifact presence from executable/runnable validation.
- For host-native functional tools, require executable/probe success before
  runnable status becomes `available`.
- For runtime tools such as `vamos`, require executable/probe success before
  runtime status becomes `available`.
- Keep Amiga-hosted GenAm artifact validation as hash/stamp only, with runnable
  status depending on its runtime chain.
- Preserve diagnostics for found-but-not-executable files.

## Acceptance Criteria

- Existing but non-executable native tool files do not produce runnable
  `available`.
- Existing but invalid runtime files make dependent chains unavailable.
- GenAm can be artifact-available via hash/stamp while runnable availability is
  determined by `vamos`.
- `assemble_vasm_source` is unavailable if the selected vasm artifact cannot be
  executed/probed.
- `assemble_devpac_source` is unavailable if `vamos` cannot be executed/probed.

## Verification

```text
focused tool graph runnable-status tests
focused oracle missing-tool tests
uv run python -m pytest tests\test_tool_graph.py tests\test_oracle_compatibility.py -q
```

## Implementation notes

- Tool records now distinguish `artifact_status` from `runnable_status`.
- Native tools remain artifact-available when the file exists and can be
  stamped, but runnable availability depends on the native launch/probe result.
- Unsupported native version probes with output still count as runnable; timeout
  or `OSError` probe failures do not.
- Capability candidates now propagate the functional tool's runnable status
  instead of recomputing availability from artifact presence alone.

## Verification result

Passed:

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_oracle_compatibility.py -q
uv run ruff check amiga_reversing\disasm\tool_graph.py tests\test_tool_graph.py tests\test_oracle_compatibility.py
```
