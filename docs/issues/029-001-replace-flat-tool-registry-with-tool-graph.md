Status: Ready
Parent proposal: docs/proposals/008-tool-runtime-capability-graph.md

## What to build

Replace the flat external tool registry with a runtime-aware tool graph.

This is Proposal 008 Slice 1. It should make the current GenAm/vamos dependency
explicit without adding compiler fingerprinting yet.

## Scope

- Create `amiga_reversing/disasm/tool_graph.py` as the new deep module for tool
  discovery, configured paths, capability resolution, and probe evidence.
- Replace `amiga_reversing/disasm/tool_registry.py` production callers with the
  new `tool_graph.py` model.
- Move persisted registry shape to version 2:

```json
{
  "version": 2,
  "runtime_tools": {
    "vamos": {"path": "C:/tools/vamos.exe"}
  },
  "functional_tools": {
    "vasm": {"path": "tools/vasmm68k_mot.exe"},
    "genam": {"path": "bin/GenAm"}
  }
}
```

- Model `host` as an explicit synthetic runtime that is not persisted.
- Keep capability definitions in typed Python data.
- Implement minimal capabilities:

```text
assemble_vasm_source
assemble_devpac_source
assemble_m68k_source
```

- Resolve all candidate chains plus one deterministic selected chain.
- Make user-facing `available` mean runnable for the requested capability.
- Report artifact status separately from runnable status.
- Include structured probe evidence:

```text
probe_method: native_version | hash_only
probe_status: available | missing | unsupported | error
version_text: optional
executable_stamp: optional
```

## Out of scope

- Compiler fingerprint fixtures.
- Emulator-assisted GenAm version probing.
- WinUAE automation.
- Legacy compatibility for version-1 `tool_registry.json`.
- Making external tools part of reproduction exactness.
- Browser UI for configuring tool paths.

## Files likely touched

- `amiga_reversing/disasm/tool_graph.py`
- `amiga_reversing/disasm/tool_registry.py`
- `amiga_reversing/disasm/oracle_compatibility.py`
- `amiga_reversing/disasm/reproduction.py`
- `amiga_reversing/disasm/server.py`
- `amiga_reversing/tools/tool_registry.py`
- `tests/test_tool_registry.py`
- `tests/test_oracle_compatibility.py`
- `tests/test_disasm_server.py`
- `tests/test_tool_registry_cli.py`

Rename tests to `test_tool_graph*` if the implementation fully deletes the old
registry module.

## API / CLI shape

Resource routes:

```text
GET /api/tools/runtimes
GET /api/tools/functional
GET /api/tools/capabilities/{capability_id}
GET /api/projects/{project}/tool-capabilities/{capability_id}
```

CLI concepts:

```powershell
uv run amiga-tool-registry runtimes
uv run amiga-tool-registry tools
uv run amiga-tool-registry capability assemble_devpac_source
uv run amiga-tool-registry set-path runtime vamos C:\tools\vamos.exe
uv run amiga-tool-registry set-path functional genam bin\GenAm
```

Browser path configuration can become a Proposal 007 command-style mutation only
when there is a browser workflow for it. Do not hide tool graph read queries
inside command routes.

## Acceptance criteria

- `genam` artifact can be available while `genam` runnable status is missing
  because `vamos` is missing.
- `assemble_devpac_source` resolves to GenAm through `vamos` when both are
  available.
- `assemble_vasm_source` resolves to vasm through synthetic `host`.
- Capability resolution returns all candidates plus a deterministic selected
  chain.
- User-facing availability summaries use runnable status.
- Diagnostic payloads expose artifact status, runtime status, missing runtime
  ids, and probe evidence.
- GenAm identity can be `hash_only` without version text.
- Registry version 2 stores runtime and functional configured paths separately.
- Old version-1 registry files fail clearly or are replaced through the new
  setter; no compatibility reader is kept.
- No production caller models GenAm availability by manually requesting
  `("genam", "vamos")`.
- Oracle code consumes resolved invocation chains rather than reconstructing
  runtime dependencies.

## Required tests

- Unit test: GenAm artifact found plus missing `vamos` yields
  `artifact_status=available`, `runnable_status=missing`, and
  `missing_runtime_ids=["vamos"]`.
- Unit test: `assemble_devpac_source` resolves to `genam` through `vamos`.
- Unit test: `assemble_vasm_source` resolves to `vasm` through `host`.
- Unit test: GenAm probe evidence supports `hash_only`.
- Unit test: registry version 2 separates `runtime_tools` and
  `functional_tools`.
- Route test: capability query shows runtime-chain status.
- CLI test: `runtimes`, `tools`, `capability`, and typed `set-path` commands
  call the new routes/service shape.
- Oracle test: GenAm oracle consumes a resolved invocation chain.

## Verification

Run focused tests:

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_oracle_compatibility.py tests\test_disasm_server.py tests\test_tool_registry_cli.py -q
```

If test files keep old names during the slice:

```powershell
uv run python -m pytest tests\test_tool_registry.py tests\test_oracle_compatibility.py tests\test_disasm_server.py tests\test_tool_registry_cli.py -q
```

## Cleanup / deletion

- Delete `tool_registry.py` after production imports move, unless the issue
  keeps a small temporary shim only for same-slice test migration.
- Delete or rewrite tests that assert the old flat `availability` payload.
- Remove old route handling for `/api/tools/availability` if no production
  caller remains.
- Update docs that mention flat tool ids as a registry peer set.

## Notes for agents

- Keep this issue focused on runtime-aware availability and capability
  resolution. Do not start compiler fingerprinting here.
- No external compatibility is required. Prefer the clean model over wrappers.
- Preserve Proposal 002's exactness rule: external tools are oracle inputs, not
  the reproduction gate.
