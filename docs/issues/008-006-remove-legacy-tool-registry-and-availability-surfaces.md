# 008-006 Remove Legacy Tool Registry And Availability Surfaces

Status: Done
Source proposal: `docs/proposals/008-tool-runtime-capability-graph.md`
Created: 2026-05-17

## Problem

The runtime-aware graph exists, but old naming still leaks through API, CLI,
and tests:

- `GET/PUT /api/tool-registry`
- project `tool-availability`
- CLI `registry`
- CLI `project-availability`
- tests named around old registry/availability concepts

Because this repo is the only consumer, no backwards-compatible route or CLI
surface is needed.

## Scope

- Replace `/api/tool-registry` with graph-shaped registry/configuration routes
  or remove the read route if unused.
- Replace project `tool-availability` with capability-oriented route naming.
- Rename CLI commands to graph concepts only.
- Update tests to assert the new route/CLI vocabulary.
- Keep the installed entry point name `amiga-tool-registry` only if desired,
  but not old command names.
- Remove docs/tests that describe flat registry compatibility.

## Acceptance Criteria

- No production route exposes `/api/tool-registry`.
- No production route exposes project `tool-availability`.
- CLI has no `registry` or `project-availability` command.
- Tests assert `runtimes`, `tools`, `capability`, and capability-oriented
  project route names.
- Web code consumes the new payload names.
- Search for old route/command names returns only historical proposal text or
  none, as decided during implementation.

## Verification

```text
focused server route tests
focused CLI tests
focused web source tests
uv run python -m pytest tests\test_disasm_server.py tests\test_tool_registry_cli.py tests\test_web_app_source.py -q
```

## Implementation notes

- Removed production `/api/tool-registry` read/write routes.
- Replaced `/api/tools/path` with `/api/tools/configuration/path`.
- Replaced project `/tool-availability` with `/tool-capabilities`.
- Removed CLI `registry`, `project-availability`, and `set-path`; the CLI now
  uses graph/configuration vocabulary.
- Updated the web policy summary to consume `tool_capabilities`.

## Verification result

Passed:

```powershell
uv run python -m pytest tests\test_disasm_server.py tests\test_tool_registry_cli.py tests\test_web_app_source.py -q
uv run ruff check amiga_reversing\disasm\server.py amiga_reversing\tools\tool_registry.py tests\test_disasm_server.py tests\test_tool_registry_cli.py tests\test_web_app_source.py
search production/tests for old route and CLI names
```
