# 008-005 Reject Flat Or Unknown Tool Registry Shapes

Status: Done
Source proposal: `docs/proposals/008-tool-runtime-capability-graph.md`
Created: 2026-05-17

## Problem

The registry loader defaults a missing `version` to version 2 and preserves
unknown top-level keys. A flat legacy payload such as:

```json
{"tools": {"vasm": {"path": "x"}}}
```

loads as a version-2 registry instead of failing clearly. No backwards
compatibility is required.

## Scope

- Require an explicit `version: 2` in persisted registry files.
- Reject legacy flat `tools` payloads.
- Reject unknown top-level keys unless deliberately added to the v2 schema.
- Keep missing registry file behavior as an empty v2 registry.
- Keep setters writing only the v2 shape.

## Acceptance Criteria

- Missing registry file returns an empty v2 registry.
- Persisted registry without `version` fails.
- Persisted registry with `version: 1` fails.
- Persisted registry with top-level `tools` fails.
- Persisted registry with unknown top-level keys fails.
- Set-path writes only `version`, `runtime_tools`, and `functional_tools`.

## Verification

```text
focused registry validation tests
uv run python -m pytest tests\test_tool_graph.py tests\test_tool_registry_cli.py -q
```

## Implementation notes

- Persisted registry payloads now require explicit `version: 2`.
- Unknown top-level keys, including legacy flat `tools`, are rejected.
- Missing registry files still return the empty v2 registry.
- `set-path` persists only `version`, `runtime_tools`, and
  `functional_tools`.

## Verification result

Passed:

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_tool_registry_cli.py -q
uv run ruff check amiga_reversing\disasm\tool_graph.py tests\test_tool_graph.py tests\test_tool_registry_cli.py
```
