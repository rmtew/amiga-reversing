# 009-007 Correlate Browser And Backend Workflow Profiles

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Connect browser fetch/render timing to the backend workflow profile for a
user-visible action.

The first target is a representative manual edit or listing refresh path where
backend spans and browser queue/fetch/render samples can be inspected together
through debug state.

## Scope

- Add request or workflow ids that connect API responses to browser timing
  samples.
- Expose the last correlated workflow profile through browser debug state.
- Keep visible UI text unchanged; this is debug/test observability.
- Add focused source and CDP coverage for the debug-state shape.

## Out of scope

- A visible performance dashboard.
- Hard timing thresholds.
- Tool graph spans.
- Reworking all browser fetch paths at once.

## Files likely touched

- `amiga_reversing/disasm/server.py`
- `amiga_reversing/web/app.js`
- `tests/test_web_app_source.py`
- `tests/test_web_e2e_cdp.py`
- `tests/workflow_harness.py`

## Acceptance criteria

- Browser debug state can expose the last API request or workflow id for a
  profiled action.
- Browser debug state can expose the last backend workflow profile for that
  action.
- Listing fetch/render samples remain available with queue, fetch, render, and
  total timing fields.
- Focused tests assert correlation shape, not timing thresholds.
- No visible feature text is added only to explain profiling.

## Required tests

```powershell
uv run python -m pytest tests\test_web_app_source.py -q
$env:M68K_RUN_BRAVE_CDP='1'
uv run python -m pytest tests\test_web_e2e_cdp.py -q
```

## Cleanup / deletion

- Remove browser-only timing samples that cannot be correlated after the new
  path exists.

## Notes for agents

- `window.__amigaDebugState()` is the browser debug entrypoint.
- Keep LLM operability as a consumer of the same debug contract, not a separate
  automation interface.

## Implementation notes

- Browser API calls now get a browser request id sent as
  `X-Amiga-Browser-Request-Id`.
- `fetchJson()` records the last API request, and records the last profiled API
  request when the response data carries `workflow_profile`.
- `window.__amigaDebugState()` exposes top-level `last_api_request_id`,
  `last_profiled_api_request_id`, `last_workflow_profile`, and
  `last_listing_fetch_sample`.
- The debug-state `profiling` layer mirrors the same correlation payload for
  LLM and CDP consumers.
- Listing fetch samples retain queue/fetch/render/total timing fields and now
  carry the browser API request id that produced the listing payload.

## Verification

Passed:

```powershell
uv run python -m pytest tests\test_web_app_source.py -q
$env:M68K_RUN_BRAVE_CDP='1'; uv run python -m pytest tests\test_web_e2e_cdp.py::test_brave_cdp_llm_operable_command_smoke_uses_debug_state_and_locators -q
uv run ruff check tests\test_web_app_source.py tests\test_web_e2e_cdp.py
```
