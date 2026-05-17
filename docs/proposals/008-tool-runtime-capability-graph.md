# Proposal 008: Tool Runtime Capability Graph

Status: Draft for implementation issue.
Status changed: 2026-05-17.

Proposal 002 made external assembler checks explicit, but the tool model is
still flat. GenAm shows the missing abstraction: some useful tools are not
native host executables. They are functional tools that require a runtime such
as `vamos` before they can be probed or used.

This proposal replaces the flat tool registry with a runtime-aware capability
graph. The immediate goal is clean GenAm-through-vamos modeling. The larger
goal is to make future assembler/compiler comparison and fingerprinting fit the
same architecture.

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Decisions Already Made
- [ ] Integration Findings
  - [ ] 1. Availability Is Currently Path-Centric
  - [ ] 2. GenAm Is A Functional Tool, Not A Native Tool
  - [ ] 3. `available` Must Mean Runnable
  - [ ] 4. Version Probing Needs Evidence, Not One Nullable String
  - [ ] 5. Proposal 007 Does Not Own Tool Query Routes
  - [ ] 6. Compiler Fingerprinting Wants The Same Model
  - [ ] 7. Oracles Should Resolve Invocation Chains
- [ ] Tutorial: Runtime And Functional Tool Inventory
  - [ ] Step 1: Split Runtime Tools From Functional Tools
  - [ ] Step 2: Move The Registry To Version 2
  - [ ] Step 3: Describe Capabilities In A Python Catalog
  - [ ] Step 4: Resolve Runnable Invocation Chains
  - [ ] Step 5: Stamp Probe Evidence
- [ ] Larger Architecture Observations
  - [ ] 1. Tool Discovery Should Be A Deep Module
  - [ ] 2. Tool Identity Is More Than Version Text
  - [ ] 3. Fingerprinting Is An Oracle Workflow
- [ ] Forward Implementation Model
  - [ ] `tool_graph.py`
  - [ ] Runtime Tool Registry
  - [ ] Functional Tool Registry
  - [ ] Capability Model
  - [ ] Probe Strategies
  - [ ] Invocation Chains
  - [ ] Resource Routes And Command Mutations
  - [ ] Fingerprint Fixtures
- [ ] Non-Goals
- [ ] Proposed Rewrite
  - [ ] Slice 1: Replace Flat Registry With Tool Graph
  - [ ] Slice 2: GenAm Through Vamos As The First Runtime Chain
  - [ ] Slice 3: Capability Queries For Oracle Workflows
  - [ ] Slice 4: Probe Evidence And Identity Stamps
  - [ ] Slice 5: Compiler Fingerprint Fixtures
- [ ] Acceptance Criteria
- [ ] Rewrite Acceptance Tests
- [ ] Verification

## Why This Exists

External tools are useful for more than "can this source assemble?". They can
answer questions about compatibility, original toolchains, compiler idioms,
startup code, OS call conventions, object layout, and app framework boilerplate.

The current implementation can discover `vasm`, `genam`, and `vamos`, and can
run GenAm through `vamos` for the DevPac oracle. That works, but the model is
too shallow:

```text
tool id -> path -> available/missing
```

That is enough for native `vasm`. It is not enough for GenAm, SAS/C, Aztec C,
DICE, or other Amiga-hosted tools that need an emulator/runtime before they are
runnable.

## Mental Model

Think of tools as a graph:

```text
runtime tool
  provides an execution environment
  examples: host, vamos, WinUAE

functional tool
  performs a domain task
  examples: vasm, GenAm, SAS/C, Aztec C, DICE, DevPac

capability
  describes what the functional tool can do
  examples: assemble source, compile C, link hunk, emit listing, probe version

invocation chain
  binds a functional tool to a runtime that can execute it
  examples:
    vasm -> host
    GenAm -> vamos
    SAS/C -> vamos
```

Availability has two layers:

```text
artifact status
  Did we find the functional tool file or configured path?

runnable status
  Can we execute it through one supported runtime chain?
```

For GenAm, `bin/GenAm` can be artifact-available while not runnable because
`vamos` is missing. User-facing availability should mean runnable. Diagnostics
should show both artifact and runtime status.

## Current State Read

Current implementation:

- `amiga_reversing/disasm/tool_registry.py` defines flat tool ids:
  `vasm`, `genam`, `vamos`.
- `.amiga_reversing/tool_registry.json` stores one `tools` map.
- Tool availability checks configured path, bundled path, then PATH lookup.
- `genam` has a bundled path at `bin/GenAm`.
- `vamos` is discovered from PATH or configured path.
- Version probing uses a generic native-host command:

```text
<path> --version
```

- On Windows, version probing skips paths without `.exe`, `.bat`, or `.cmd`.
  Bundled `bin/GenAm` therefore has no version text.
- `oracle_tool_ids_for_modes(["devpac"])` maps DevPac oracle mode to both
  `genam` and `vamos`.
- `amiga_reversing/disasm/oracle_compatibility.py` requires both `genam` and
  `vamos` before running the GenAm oracle.
- `CONTEXT.md` already says built-in GenAm oracle support requires a runnable
  GenAm path through `vamos`.
- Proposal 007 has moved target UI workflows toward command routes, but it does
  not require ordinary domain query resources to become commands.

The current code has the GenAm-through-vamos concept in behavior, but not in
the data model.

## Decisions Already Made

These decisions are part of the proposal, not open questions:

- `available` means runnable for the requested functional behavior.
- Artifact presence is separate from runnable availability.
- Internal ids are typed: runtime ids and functional tool ids are not peers.
- `host` is an explicit synthetic runtime. It is not persisted.
- The persisted registry moves to version 2; no legacy compatibility layer is
  required.
- Capability definitions live in typed Python data for now, not JSON/YAML.
- Slice 1 includes minimal capability resolution, not only richer records.
- The resolver returns all candidate chains plus one deterministic selected
  chain.
- Missing runtime makes the chain unavailable, not the functional tool artifact.
- Structured probe evidence is included in Slice 1; emulator-assisted GenAm
  version probing is deferred.
- Production callers stop manually modeling GenAm as `("genam", "vamos")`.
- CLI uses explicit concepts such as `tools`, `runtimes`, and `capability`.
- Read/query API routes are resource routes. User-triggered path configuration
  is a command-style mutation when exposed in the browser.
- The implementation target is a new deep module,
  `amiga_reversing/disasm/tool_graph.py`, replacing `tool_registry.py` in
  touched production code.

## Integration Findings

### 1. Availability Is Currently Path-Centric

`tool_availability_record("genam")` reports whether the GenAm artifact exists.
That is useful, but it is not the same as "GenAm can run". The meaningful oracle
question is whether the GenAm-through-vamos chain is available.

### 2. GenAm Is A Functional Tool, Not A Native Tool

GenAm should not be modeled like `vasm`. `vasm` is a native host executable.
GenAm is an Amiga-hosted functional assembler that currently runs through
`vamos`. That dependency belongs in the tool graph rather than inside the oracle
implementation.

### 3. `available` Must Mean Runnable

The user-facing status should answer "can this tool do the requested job now?".
That means:

```text
genam artifact found + vamos missing
  artifact_status: available
  runnable_status: missing
  missing_runtime_ids: [vamos]
```

Summaries should use runnable status. Diagnostics should expose artifact status.

### 4. Version Probing Needs Evidence, Not One Nullable String

The generic `--version` probe is a reasonable cheap probe for native host tools.
It does not work for classic Amiga tools. For those, identity may come from:

- executable hash, size, and timestamp
- emulator-assisted banner capture
- known fixture output
- explicit user-supplied version label

The registry should record probe method and evidence, not just a nullable
`version` string.

### 5. Proposal 007 Does Not Own Tool Query Routes

Proposal 007's command route work is for target UI workflows: locator-based
manual mutations, command availability, durable mutation results, and browser
state verification. Tool graph queries are resource reads. They should remain
clear resource routes. Only path configuration or other user-triggered durable
mutations should use command-style mutation handling in the browser.

### 6. Compiler Fingerprinting Wants The Same Model

C compiler comparison and fingerprinting need the same machinery:

- run compiler under an emulator/runtime
- compile small fixtures
- compare startup stubs and emitted idioms
- identify OS call thunking
- inspect data layout and library call conventions
- classify likely compiler family for target code

That should not become a separate special-case framework. It is another oracle
workflow over functional tools and runtime chains.

### 7. Oracles Should Resolve Invocation Chains

Oracle code should ask for a capability, not manually know every runtime
dependency:

```text
find runnable tool with capability assemble_devpac_source
  -> GenAm via vamos
```

Later:

```text
find runnable tool with capability compile_amiga_c
  -> SAS/C via vamos
  -> Aztec C via vamos
  -> DICE via vamos
```

## Tutorial: Runtime And Functional Tool Inventory

### Step 1: Split Runtime Tools From Functional Tools

Introduce two record types:

```text
runtime_tool:
  runtime_tool_id: host | vamos | winuae
  tool_kind: runtime
  availability: path/status/probe evidence

functional_tool:
  functional_tool_id: vasm | genam | sasc | aztec_c | dice_c
  tool_kind: functional
  artifact: path/status/probe evidence
  supported_runtimes: [...]
```

`host` is synthetic and explicitly available unless platform constraints later
say otherwise.

### Step 2: Move The Registry To Version 2

Persist configured paths by typed bucket:

```json
{
  "version": 2,
  "runtime_tools": {
    "vamos": {"path": "C:/tools/vamos.exe"},
    "winuae": {"path": "C:/tools/winuae.exe"}
  },
  "functional_tools": {
    "vasm": {"path": "tools/vasmm68k_mot.exe"},
    "genam": {"path": "bin/GenAm"}
  }
}
```

`host` is not stored. If an old version-1 registry is found, fail clearly or
replace it through the new setter. Do not add compatibility behavior.

### Step 3: Describe Capabilities In A Python Catalog

Capabilities and tool definitions are project implementation data, not
PRM-derived M68K knowledge. Keep them in typed Python definitions for now:

```python
FUNCTIONAL_TOOL_DEFINITIONS = {
    "vasm": {
        "supported_runtimes": ["host"],
        "capabilities": ["assemble_vasm_source", "assemble_m68k_source"],
    },
    "genam": {
        "supported_runtimes": ["vamos"],
        "capabilities": ["assemble_devpac_source", "assemble_m68k_source"],
    },
}
```

Move to data files only when users need to add tools without code changes.

### Step 4: Resolve Runnable Invocation Chains

Capability resolution returns all candidates and a deterministic selected
candidate:

```json
{
  "capability_id": "assemble_devpac_source",
  "selected": {
    "functional_tool_id": "genam",
    "runtime_tool_id": "vamos",
    "tool_chain": ["vamos", "genam"],
    "runnable_status": "available"
  },
  "candidates": []
}
```

For GenAm:

```text
functional_tool_id: genam
runtime_tool_id: vamos
tool_chain: [vamos, genam]
```

For vasm:

```text
functional_tool_id: vasm
runtime_tool_id: host
tool_chain: [vasm]
```

Preference order lives in the capability catalog, not in callers.

### Step 5: Stamp Probe Evidence

Reports should stamp how the tool identity was established:

```text
identity:
  version_text: optional
  executable_stamp: sha256/size/mtime
  probe_method: native_version | emulator_banner | fixture_output | hash_only
  probe_status: available | missing | unsupported | error
```

For Slice 1, `vasm` can use `native_version`. GenAm can use `hash_only`.
Emulator-assisted GenAm version probing is later work.

## Larger Architecture Observations

### 1. Tool Discovery Should Be A Deep Module

Tool/runtime resolution should become a small deep module that owns discovery,
capability matching, and invocation-chain construction. Oracle code should not
reimplement dependency logic.

### 2. Tool Identity Is More Than Version Text

Old Amiga tools may not expose a version string in a scriptable way. The system
should treat version text as one identity source, not the only source.

### 3. Fingerprinting Is An Oracle Workflow

Compiler fingerprinting should be modeled like other oracle workflows:

```text
fixture input
  -> external tool chain output
  -> comparison/fingerprint classifier
  -> report with scoped result labels
```

It should not affect reproduction exactness.

## Forward Implementation Model

### `tool_graph.py`

Create `amiga_reversing/disasm/tool_graph.py` as the replacement deep module for
`tool_registry.py`.

It owns:

- registry load/save v2
- runtime definitions
- functional tool definitions
- artifact discovery
- runtime discovery
- capability resolution
- selected/candidate invocation chains
- probe evidence
- path configuration service functions

Delete `tool_registry.py` after production callers move, unless a tiny temporary
test-only shim is needed during the same issue.

### Runtime Tool Registry

Runtime tools provide execution environments. Initial runtime ids:

```text
host
vamos
winuae
```

`host` is synthetic. `vamos` starts as the only emulated runtime used by
automated oracle workflows. `winuae` remains future-facing until there is a
clean non-interactive fixture path.

### Functional Tool Registry

Functional tools describe domain behavior. Initial functional ids:

```text
vasm
genam
```

Future ids:

```text
sasc
aztec_c
dice_c
devpac
```

`devpac` remains family/profile wording until a directly runnable DevPac
artifact is supported.

### Capability Model

Initial capabilities:

```text
assemble_vasm_source
assemble_devpac_source
assemble_m68k_source
```

Future capabilities:

```text
compile_amiga_c
link_amiga_hunk
emit_listing
run_fingerprint_fixture
```

### Probe Strategies

Probe strategies are per tool/runtime pair:

```text
native_version:
  run <tool> --version

emulator_fixture:
  run tool under runtime with a minimal fixture

hash_only:
  record executable stamp without claiming version text
```

### Invocation Chains

The resolver returns a command chain and evidence. Callers consume that chain
instead of rebuilding it from tool ids.

### Resource Routes And Command Mutations

Read/query API routes should be resource-style:

```text
GET /api/tools/runtimes
GET /api/tools/functional
GET /api/tools/capabilities/{capability_id}
GET /api/projects/{project}/tool-capabilities/{capability_id}
```

CLI should use the same concepts:

```powershell
uv run amiga-tool-registry runtimes
uv run amiga-tool-registry tools
uv run amiga-tool-registry capability assemble_devpac_source
```

Path configuration is durable project/workspace mutation. The service function
should be explicit:

```text
set_tool_artifact_path(kind, tool_id, path)
```

CLI can expose that directly. Browser UI should expose it through command-style
mutation if/when tool configuration becomes a user workflow.

### Fingerprint Fixtures

Compiler fingerprinting can start with tiny fixtures:

```text
empty main
library call
global data
function pointer dispatch
small struct copy
```

Outputs become comparison evidence against target code patterns.

## Non-Goals

- Do not make external tools part of the reproduction exactness gate.
- Do not build a generic package manager for old toolchains.
- Do not preserve flat tool-registry APIs for compatibility.
- Do not add compatibility code for version-1 registry files.
- Do not require version text for old Amiga tools when executable stamp or
  fixture evidence is stronger.
- Do not add WinUAE automation until there is a clean non-interactive workflow.
- Do not hide tool graph queries inside Proposal 007 command routes.

## Proposed Rewrite

### Slice 1: Replace Flat Registry With Tool Graph

Replace `tool_registry.py` with `tool_graph.py`.

Implement:

- registry version 2
- typed runtime and functional configured paths
- synthetic `host` runtime
- functional tool definitions in Python
- artifact status and runnable status
- structured probe evidence
- CLI concepts: `runtimes`, `tools`, `capability`
- resource routes for runtime, functional, and capability queries

Exit condition:

```text
genam artifact can be available while genam runnable status is missing because
vamos is missing
```

### Slice 2: GenAm Through Vamos As The First Runtime Chain

Move GenAm's `vamos` dependency out of `oracle_compatibility.py` and into the
resolver. The DevPac oracle should request `assemble_devpac_source` and receive
the GenAm-through-vamos chain.

### Slice 3: Capability Queries For Oracle Workflows

Update oracle and source-export workflows to ask for capabilities:

```text
assemble_vasm_source
assemble_devpac_source
```

The code should stop manually mapping profile names to tool dependencies except
inside the tool graph.

### Slice 4: Probe Evidence And Identity Stamps

Replace the single generic `version` assumption with structured probe evidence.
Keep executable stamps as first-class identity, especially for GenAm.

### Slice 5: Compiler Fingerprint Fixtures

Add a disabled-by-default fingerprint fixture runner that can execute one
compiler tool chain and write a report. Start with fixture shape and report
schema before adding many compilers.

## Acceptance Criteria

- `available` means runnable in user-facing summaries.
- `genam` can be artifact-available but not runnable when `vamos` is missing.
- DevPac oracle availability reports the selected chain and missing runtime
  requirements clearly.
- `vasm` remains a simple native-host chain through synthetic `host`.
- Tool reports distinguish version text from identity evidence.
- Oracle code requests capabilities rather than hardcoding GenAm runtime
  dependencies.
- Existing Proposal 002 behavior remains: external tool results do not affect
  reproduction exactness.
- Registry version 2 stores runtime and functional tool paths separately.
- No production caller models GenAm availability by manually requesting
  `("genam", "vamos")`.
- The model can represent at least one future Amiga C compiler without adding a
  second registry concept.

## Rewrite Acceptance Tests

- Unit test: GenAm artifact found plus missing `vamos` yields
  `artifact_status=available`, `runnable_status=missing`, and
  `missing_runtime_ids=["vamos"]`.
- Unit test: `assemble_devpac_source` resolves to `genam` through `vamos` when
  both are available.
- Unit test: `assemble_vasm_source` resolves to `vasm` through `host`.
- Unit test: GenAm identity can be `hash_only` without version text.
- Unit test: version-2 registry stores `runtime_tools` and `functional_tools`
  separately.
- Route/CLI test: project capability query shows runtime-chain status for
  `assemble_devpac_source`.
- Oracle test: GenAm oracle consumes a resolved invocation chain rather than
  calling `tool_availability_records(("genam", "vamos"))` directly.

## Verification

Initial implementation should run:

```powershell
uv run python -m pytest tests\test_tool_registry.py tests\test_oracle_compatibility.py tests\test_disasm_server.py -q
```

If the test module is renamed with the implementation:

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_oracle_compatibility.py tests\test_disasm_server.py -q
```

If compiler fingerprint fixtures are added:

```powershell
uv run python -m pytest tests\test_tool_fingerprinting.py -q
```

## Review Notes

This proposal intentionally builds on Proposal 002 rather than replacing it.
Proposal 002 established strict exactness-vs-oracle separation. Proposal 008
deepens the oracle side so external assemblers and future compilers can be
modeled cleanly.

Proposal 007 was reviewed while resolving route shape. Its command routes are
for target workflow commands and durable user mutations. Tool graph query
routes remain resource routes; browser path configuration can become a command
mutation only when there is a browser workflow for it.
