# 009-008 Add LLM-Operable Profiling Harness

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Extend the existing API/CDP workflow harness so a representative manual edit can
be driven through normal routes and reported with semantic state, durable stamps,
browser/backend debug state, and workflow spans.

The harness should report missing observability as a workflow defect.

## Scope

- Extend existing workflow harness helpers to collect workflow profiles.
- Drive one representative command through command discovery and command
  execution using locators.
- Assert durable state, projection state, server debug state, browser debug
  state, and workflow spans.
- Avoid DOM text, row index, screenshots, sleeps, or private live globals as the
  authority for correctness.

## Out of scope

- A separate agent-only API.
- Broad browser coverage for every manual command.
- Tool graph profiling.
- Visible UI profiling features.

## Files likely touched

- `tests/workflow_harness.py`
- `tests/test_api_workflow_harness.py`
- `tests/test_web_e2e_cdp.py`
- `amiga_reversing/disasm/server.py`
- `amiga_reversing/web/app.js`

## Acceptance criteria

- One representative manual edit workflow can be driven through API and CDP
  helpers.
- The report includes semantic assertions, durable stamps, and workflow spans.
- The harness identifies missing workflow profiles as a test failure.
- The workflow does not scrape DOM text as authority.
- Existing durability assertions remain in place.

## Required tests

```powershell
uv run python -m pytest tests\test_api_workflow_harness.py -q
$env:M68K_RUN_BRAVE_CDP='1'
uv run python -m pytest tests\test_web_e2e_cdp.py -q
```

## Cleanup / deletion

- Remove test-only helpers that duplicate semantic assertions already available
  through the workflow harness.

## Notes for agents

- Build on Proposal 007's harness shape. Do not create a parallel LLM interface.

## Implementation notes

- Extended `assert_manual_workflow_snapshot()` so expected workflow spans require
  a `workflow_profile` payload.
- Added optional `profile_debug_state` assertions for browser/CDP debug state:
  profiled request id, browser workflow profile identity, and listing fetch
  sample timing shape.
- Updated the representative CDP manual command smoke to pass the command
  workflow profile and browser profile debug state through the shared harness.
- Added API harness coverage proving missing workflow profiles fail as workflow
  observability defects.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_api_workflow_harness.py -q
$env:M68K_RUN_BRAVE_CDP='1'; uv run python -m pytest tests\test_web_e2e_cdp.py::test_brave_cdp_llm_operable_command_smoke_uses_debug_state_and_locators -q
uv run ruff check tests\workflow_harness.py tests\test_api_workflow_harness.py tests\test_web_e2e_cdp.py
$env:M68K_RUN_BRAVE_CDP='1'; uv run python -m pytest tests\test_web_e2e_cdp.py -q
uv run ruff check tests\cdp_brave.py tests\test_web_e2e_cdp.py
```

Audit note: the full CDP command initially exposed stale command-palette test
paths and one timeout without artifacts. The tests now wait for palette loading
before switching to global command mode, assert durable review/source-export
state, and the CDP helper captures timeout artifacts.
