# 009-002 Add Manual Edit Latency Trace

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Add backend workflow spans to a representative manual edit command so a developer
can see where backend time went for a user-visible mutation.

The slice should use the normal command route and Authoritative Mutation Result,
not a parallel profiling-only API.

## Scope

- Attach workflow profile spans to manual command execution responses.
- Cover command context construction, locator resolution, command catalog lookup,
  Manual Action Log append, manual action application, invalidation, and response
  construction.
- Extend the API workflow harness to assert the manual mutation profile shape.
- Keep Manual Action Log as the durable source of manual review state.

## Out of scope

- Browser debug-state correlation.
- Replacing all-row locator materialization.
- Refactoring command catalog internals beyond what is needed for spans.
- Timing thresholds.

## Files likely touched

- `amiga_reversing/disasm/server.py`
- `amiga_reversing/disasm/workflow_profile.py`
- `tests/workflow_harness.py`
- `tests/test_api_workflow_harness.py`
- `tests/test_disasm_server.py`

## Acceptance criteria

- A representative row or element manual edit response includes
  `workflow_profile`.
- The profile includes `locator_resolution` and `manual_action_append` spans.
- The mutation result still includes durable action id, Manual Action Log count
  and head hash, projection hash, and affected locators.
- Tests verify profile shape through the normal command route.
- No Manual Action Log replacement state is introduced.

## Required tests

```powershell
uv run python -m pytest tests\test_api_workflow_harness.py tests\test_disasm_server.py -q
```

## Cleanup / deletion

- Remove any local profiling helpers that become redundant after command
  execution uses the shared workflow profile module.

## Notes for agents

- This is measurement first. Do not hide observed slow paths with speculative
  caching in this slice.

## Implementation notes

- Manual command execution responses now include `workflow_profile`.
- The normal command route records spans for `command_context`,
  `locator_resolution`, `command_catalog`, `manual_action_append`,
  `manual_action_application`, `listing_cache_invalidation`, and
  `response_build`.
- The API workflow harness can require workflow spans as part of manual mutation
  durability snapshots.
- Focused verification passed:
  `uv run python -m pytest tests\test_api_workflow_harness.py tests\test_disasm_server.py -q`.
