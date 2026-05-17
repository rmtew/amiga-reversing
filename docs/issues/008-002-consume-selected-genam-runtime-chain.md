# 008-002 Consume Selected GenAm Runtime Chain

Status: Implemented
Source proposal: `docs/proposals/008-tool-runtime-capability-graph.md`
Created: 2026-05-17

## Problem

Slice 1 moved GenAm/vamos availability into the tool graph, but the oracle run
path still pulled executable paths out of the flattened availability diagnostic
record. That kept diagnostics and execution coupled.

## Scope

- Keep GenAm/vamos capability resolution in `tool_graph.py`.
- Make `oracle_compatibility.py` run the selected capability chain paths
  directly.
- Keep availability records as report diagnostics only.
- Do not start compiler fingerprinting or emulator-assisted version probing.

## Acceptance Criteria

- GenAm oracle command uses the selected `vamos` and `genam` paths from the
  resolved capability.
- Vasm oracle command uses the selected native-host functional path.
- Missing capability paths fail as tool errors instead of falling through to a
  malformed command.
- Tests cover the selected GenAm chain command shape.

## Verification

```powershell
uv run python -m pytest tests\test_oracle_compatibility.py tests\test_tool_graph.py -q
uv run ruff check amiga_reversing\disasm\oracle_compatibility.py tests\test_oracle_compatibility.py tests\test_tool_graph.py
cmd /c src\precommit.bat
```

## Implementation Notes

- `run_genam_oracle` now consumes `selected.runtime_resolved_path` and
  `selected.functional_resolved_path` from the capability result.
- `run_vasm_oracle` follows the same pattern for its selected functional path.
- Availability payloads remain in reports but are no longer the execution path
  source of truth.
