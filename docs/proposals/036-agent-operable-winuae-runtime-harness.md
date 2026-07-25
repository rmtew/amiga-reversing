# Proposal 036: Agent-Operable WinUAE Runtime Harness

Status: Proposed.

## Why This Exists

Static reconstruction and the framework round-trip gate answer an essential but
limited question: whether the reconstructed source rebuilds the original bytes
under the project-owned reproduction policy. Static analysis also has real
blind spots: a range may be convincingly classified as code while no static
predecessor explains how it is reached. Indirect dispatch, jump tables,
callbacks, exception vectors, loaders, relocation, copied code, and
decompression can leave such gaps even in an otherwise reproducible target.

The initial purpose of emulator control is therefore coverage-guided
reachability investigation in support of human-quality source convergence. It
is not to run gameplay regression tests after every label or type improvement.
Behaviour-preservation testing becomes the main use once the project begins
intentional changes to a target and needs to protect documented game semantics.

This proposal adds a Windows-first runtime debugging harness around WinUAE. Its
first product is a local, agent-operable workspace that helps complete a
reversing target; non-interactive CI execution is a later hardening and
packaging step. It is not a proposal to replace static analysis, the exactness
gate, or the existing Manual Action Log workflow.

The desired outcome is a controlled experiment:

```text
original or rebuilt target + deterministic machine profile + scenario
    -> emulator session
    -> debugger-controlled execution and observations
    -> structured runtime report
    -> comparison/oracle result and trace-derived candidate facts
```

The agent should be able to ask meaningful questions such as:

- Did execution reach this named reconstructed routine?
- Did this loader copy/decompress code into the expected range?
- Did the rebuilt target and original target agree at a stable checkpoint?
- Which CPU, RAM, and custom-chip state differs when they do not agree?
- Did a run terminate due to a timeout, an exception, an expected breakpoint,
  or an explicit test completion signal?

## Operating Priorities

For an exactly reproducible target such as `amiga_disk_pandora-1988-firebird`,
the source-quality loop remains primary:

```text
analysis facts and xrefs
  -> labels, types, tables, globals, and structured ranges
  -> symbolic, human-readable rendered source
  -> framework exactness gate
  -> unresolved source-quality review
```

Runtime work enters that loop only when it answers a concrete unresolved
question that static analysis cannot presently answer, for example a suspected
code range with no known incoming edge. The desired first runtime report is an
observed path into that range, not a generic "game launched" result.

The later behaviour-preservation loop is separate:

```text
original target -> document stable observable checkpoints
intentional code/data change -> rebuilt target -> same scenarios -> comparison
```

It protects documented title, input, state-transition, collision, scoring,
loading, or game-over behaviour after a change. It does not define whether
ordinary reversing annotations are accepted.

## Relationship To Existing Work

This proposal composes existing architecture; it does not reopen it.

| Existing proposal | Relationship |
| --- | --- |
| Proposal 002, reproduction profiles and oracles | Framework byte-exactness remains the authoritative reproduction gate. Emulator results are runtime evidence and must never silently upgrade a non-exact target to reproduced. |
| Proposal 003, runtime tracing | This proposal supplies the controlled WinUAE producer and debugger transport for the general trace-import model. Trace facts remain conservative and provenance-bearing. |
| Proposal 008, tool runtime capability graph | WinUAE is a runtime tool with a runnable invocation chain, identity stamp, probe evidence, and configured resources. |
| Proposal 009, workflow profiling | Emulator runs need their own profile spans and artifacts, but should use the same durable reporting principles. |
| Proposal 010, agentic reversing loop | The agent invokes a normal harness and receives stable reports. It must not acquire a private emulator-only mutation path. |
| Proposal 013, LLM web UI verification loop | Browser/UI automation is not the emulator oracle. The runtime harness offers an API/CLI surface that is deterministic enough for tests and agents. |

## Current Landscape And Candidate Starting Points

The normal UAE console debugger is valuable for a human, but an interactive
prompt and hotkeys are not a CI or agent-control contract. A machine-readable
debugger transport is required.

Two external candidates make this practical enough to investigate:

1. [BartmanAbyss/vscode-amiga-debug](https://github.com/BartmanAbyss/vscode-amiga-debug)
   ships a GDB-enabled WinUAE and uses it for source/assembly debugging,
   breakpoints, data breakpoints, registers, memory, and a host-mounted Amiga
   directory. Its repository is active and has CI material. The documented
   bundled emulator base is modified WinUAE 4.9.0, so the extension's activity
   must not be confused with tracking current upstream WinUAE.
2. [axewater/mcp-winuae-emu](https://github.com/axewater/mcp-winuae-emu)
   is an agent-facing proof of concept built on that GDB path. Its stated
   additions include memory/register writes, breakpoints, watchpoints,
   stepping, custom-chip register inspection, Copper-list decoding, and
   automatic launch. It is evidence that the desired agent interaction is
   technically achievable, not yet an adopted project dependency.

The first investigation must establish exact source provenance, licence terms,
patch boundary against upstream WinUAE, version pinning, reproducible build
story, and whether the local session is genuinely headless. CI runner behavior
is a separate later question, but it reuses the same headless contract. Neither
a bundled executable nor an MCP server must be accepted solely because it works
on one developer workstation.

## Design Decisions

The following are proposed constraints, not implementation claims.

### 1. Windows Is An Explicit Supported Runtime

The initial implementation targets the developer's local Windows workspace.
GitHub Actions Windows runners are a later delivery target once the local
agent/debugger loop is useful and stable. Cross-platform support is welcome
later, but must not delay local Windows work. All reports and scenario formats
remain host-neutral where practical so a future FS-UAE or other compatible
runtime can implement the same contract.

### 2. Debug Transport Is A Boundary, Not The Public Model

GDB remote protocol is the preferred initial transport because it has an
existing WinUAE implementation and mature client libraries. UAE debugger text
commands may be used for exploration, but must not leak throughout project
callers or scenario definitions.

The project-facing interface uses named operations, for example:

```text
launch(profile, image, scenario)
continue_until(checkpoint)
step(count)
read_registers()
read_memory(range)
write_memory(range, bytes)              # debug-only, explicitly reported
set_breakpoint(address or symbol)
set_watchpoint(range, access)
inject_input(event sequence)
capture_frame()
stop_and_collect()
```

An implementation may translate these to GDB packets or another debugger
transport. The transport client owns packet details, reconnect rules, timeouts,
and emulator process lifetime.

### 3. Coverage-Guided Reachability Is The First Runtime Feature

For a candidate code range with no statically proven incoming edge, the harness
must support a bounded investigation:

```text
run original target through a named scenario
  -> detect execution in candidate range
  -> capture current PC, registers, stack, and selected memory
  -> retain a bounded recent-PC/control-transfer history
  -> map the predecessor and hit range to target locators
  -> emit a reviewed candidate edge/fact
```

The minimal useful collection is executed PC coverage as ranges plus
breakpoints at selected candidate blocks. A full instruction trace or
single-step trace may be too slow for normal runs; if needed, an
emulator-side bounded ring buffer or range-hit instrumentation is preferable
to sending an unbounded debugger transcript to the host.

Coverage reports distinguish:

```text
statically proven edge
dynamically observed edge
candidate range observed as executed
candidate range not observed in these scenarios
```

The final state means only that the supplied scenarios did not reach it. It
must never be converted to "unreachable", dead code, or a negative
classification result. An observed edge is evidence to review, not an automatic
rewrite of analysis facts.

### 4. Runtime Evidence Does Not Replace Static Evidence

An observed PC, memory write, or screen hash is trace-derived evidence. It can
support a reviewed entrypoint, data classification, relocation/decompression
fact, or semantic comment. It cannot by itself classify unexecuted code as
dead, establish universal behavior, or override contradictory static facts.

Runtime-derived facts record at least:

```text
target identity
emulator/runtime identity and patch identity
machine profile and ROM identity
input media and input-script hashes
scenario/checkpoint id
observation type and values/ranges
capture time and emulator-time/cycle position when available
confidence and provenance
```

### 5. Rebuilt, Original, And Hybrid Modes Are Separate

The harness must make the artifact under test unambiguous.

```text
original
  Boots original media or executable without replacement.

rebuilt
  Boots the fully rebuilt output produced by the framework.

hybrid
  Boots original media while replacing one named executable, hunk/segment,
  disk block, or loaded memory range using a target-specific adapter.
```

Hybrid mode is powerful for incremental reversing but cannot have a universal
injection implementation. Loader behavior, packed executables, checksums,
relocations, self-modification, and protection systems are target-specific.
Every hybrid adapter must declare its injection point, prerequisites, bytes
replaced, and validation. A hybrid success is not full reproduction proof.

#### Direct decompressed-payload launch is not an implicit hybrid adapter

A diagnostic bootblock which reads a decompressed raw image to its declared
load address and transfers to its declared entrypoint is tempting, but those
two fields alone do not prove the image is independently bootable.  Pandora
provided a concrete counterexample on 2026-07-26: a disposable custom boot disk
was built from the byte-identified ByteKiller output, loaded it at `$20000`,
and returned its declared `$20000` entrypoint.  The headless WinUAE process
exited before its GDB listener became available.  The experiment is therefore
not an adopted adapter and does not establish whether the missing prerequisite
is parent-loader state, a bootstrap ABI detail, or an emulator/media defect.

Do not retain a generic direct-payload option after such a result.  A future
adapter must first capture the original handoff state, declare every required
register, memory range, interrupt/vector condition, and media prerequisite,
then prove a headless cold boot reaches the byte-identified payload before it
is exposed through the public runtime interface.

### 6. Scenario And Checkpoint, Not Screenshots, Define Tests

A scenario specifies the controlled starting condition, input, stopping
condition, observations, and expected result. Checkpoints should prefer stable
machine-level facts: named PC ranges, selected registers, RAM ranges, chip
registers, explicit debug markers, disk/serial output, or deterministic
completion events.

Frame and audio capture are valuable diagnostics and may be compared as hashes
when the machine profile guarantees stable timing. They are not the sole
pass/fail oracle: display cropping, raster timing, palette interpretation, and
host scheduling make image-only tests brittle.

Illustrative scenario shape:

```json
{
  "id": "boot-to-title",
  "machine_profile": "amiga500-ks13-pal",
  "mode": "rebuilt",
  "input": [{"at_frame": 0, "event": "start"}],
  "stop": {"kind": "breakpoint", "symbol": "title_screen_ready"},
  "assertions": [
    {"kind": "pc_in_symbol", "symbol": "title_screen_ready"},
    {"kind": "memory_equals", "address": "0x0000f000", "bytes": "..."},
    {"kind": "no_exception"}
  ],
  "artifacts": ["registers", "selected_memory", "frame_png", "debug_log"]
}
```

The final schema should be typed and validated; this JSON is explanatory only.

### 7. Differential Comparison Is A Later Behaviour Oracle

Differential comparison is valuable when intentional changes need regression
protection. It is not a prerequisite for source-quality convergence or
coverage-guided reachability work. The original-only mode is normally the
starting point for discovering dynamic edges.

For a given pinned profile and scenario, the harness may execute original and
rebuilt sessions and compare named observations at equivalent checkpoints.

```text
original session ─┐
                  ├─> normalized checkpoint observations ─> state diff
rebuilt session  ─┘
```

Normalization removes nondeterministic host metadata and permits explicit
ignore/mask ranges. Masks must be narrow, documented, and part of the scenario
identity; an unconstrained "ignore differing memory" mechanism would destroy
the oracle's value.

The resulting status is scoped, for example:

```text
runtime.pass
runtime.assertion_failed
runtime.state_mismatch
runtime.timeout
runtime.exception
runtime.tool_unavailable
runtime.not_comparable
runtime.not_run
```

These statuses are never reproduction statuses.

### 8. Headless Operation Is Required Locally And In CI

The first local agent contract is headless operation: the harness launches or
attaches without a visible emulator window, accepts scripted debugger control,
produces bounded artifacts, and shuts down cleanly. It must not require a
usable display, keyboard, mouse, manual debugger hotkeys, or GUI scraping.

CI is a later consumer of this same contract, not the point at which
headlessness is introduced. An emulator implementation may internally create a
hidden window only if it remains invisible and does not require display
hardware or user interaction.

Each scenario has explicit host-wall-time and emulated-time/frame/cycle
budgets. A timeout is a useful classified result that triggers log, register,
and selected-memory capture before termination.

## Architecture

```text
tool capability graph
  └─ WinUAE runtime capability
       ├─ executable/config/ROM availability
       ├─ executable, patch, and probe identity
       └─ debugger-transport capability

runtime harness
  ├─ profile resolver and session builder
  ├─ process lifecycle and bounded launch
  ├─ debugger transport adapter
  ├─ scenario executor and input scheduler
  ├─ checkpoint/assertion evaluator
  ├─ original/rebuilt/hybrid artifact resolver
  ├─ differential comparator
  └─ artifact and structured-report writer

consumers
  ├─ local human/agent debugging workspace
  ├─ later CI workflow
  ├─ human CLI/debug session
  ├─ agentic reversing loop
  └─ trace-import pipeline
```

Suggested ownership:

```text
amiga_reversing/disasm/tool_graph.py
  WinUAE capability definition, probe evidence, and invocation chain selection.

amiga_reversing/runtime/winuae.py
  WinUAE-specific config/session construction and lifecycle.

amiga_reversing/runtime/debug_transport.py
  Protocol-neutral debugger operations and result types.

amiga_reversing/runtime/gdb_remote.py
  GDB-remote implementation, if selected.

amiga_reversing/runtime/scenarios.py
  Typed scenario, checkpoint, assertion, and comparison schema.

amiga_reversing/runtime/reports.py
  Stable JSON report/artifact manifest and status classification.

amiga_reversing/runtime/trace_export.py
  Conversion into the trace-import format from Proposal 003.

targets/<target>/runtime/
  Target-owned scenario declarations and only explicitly accepted baselines.

bin/rebuilt/runtime/<run-id>/
  Generated images, dumps, logs, frame captures, and reports; gitignored.
```

Exact paths remain implementation decisions. The boundary rule matters more:
target source and durable analysis facts must not be polluted by disposable
emulator dumps or per-run screenshots.

## Machine Profiles And Reproducibility

Runtime observations are meaningful only relative to a fully described Amiga
machine. A profile must pin, or identify by content hash:

- emulator executable and project patch/source revision;
- Kickstart ROM and any expansion/CPU-board ROM;
- model, CPU, chipset, PAL/NTSC, RAM, floppy/drive configuration;
- JIT, cycle-exactness, warp, sound, display, input, and filesystem settings;
- disk/HDF/executable inputs and mounted host directories;
- initial save-state when one is deliberately used;
- launch/startup command and input-script identity.

ROMs and third-party game images are normally redistributable neither in the
repository nor public artifacts. Local configuration, and later CI
configuration, must use legal resources; capability probes must report
`runtime.tool_unavailable` or a more specific missing-resource result rather
than silently substituting another ROM.

Save states can accelerate scenarios but are emulator-version-sensitive. They
must include profile and emulator identity stamps, and a scenario should retain
a cold-boot validation path when it relies on a saved state.

Warm-start save states are an optimization, not an opaque new baseline. A
target may define a save state at a named checkpoint after the operating system
and common loader state are ready but before the rebuilt executable is loaded
or hybrid replacement occurs. This can remove repeated boot and disk-loading
cost during coverage investigations and regression runs without retaining old
target code in memory. Each warm-start scenario must retain a slower cold-boot
scenario that proves the checkpoint remains reachable under the same pinned
profile. The project should measure the time saving before adding a
version-sensitive save state to CI.

## Agent Interface And Safety

The agent should consume a small stable CLI/API that returns structured reports
and named artifacts. It should not scrape a WinUAE UI, parse arbitrary debugger
transcripts as its only state source, or depend on an MCP server as the sole
project interface.

MCP is useful as an optional thin adapter for interactive agent clients, not as
the runtime harness foundation. The project-owned typed library and JSON CLI
remain the authority used by CI, focused tests, humans, and MCP alike. An MCP
adapter may expose a deliberately small semantic tool set such as
`run_scenario`, `inspect_checkpoint`, `compare_original_rebuilt`, and
`investigate_reachability`; it must not expose an unrestricted raw GDB console
as the normal agent surface.

Useful agent operations are read-heavy:

```text
runtime probe
runtime run --target <target> --scenario <id> --mode original|rebuilt|hybrid
runtime compare --target <target> --scenario <id>
runtime inspect --run <id>
runtime debug --target <target> --scenario <id>  # bounded interactive aid
```

Memory/register writes and arbitrary debugger evaluation are permitted only in
an explicit debug-experiment mode. Reports must record all writes and label
the resulting run non-comparable unless the scenario explicitly allows them.
An agent must never modify `bin/` originals, silently update a runtime baseline,
or use a successful hybrid experiment as grounds to mark full reproduction
complete.

## Rollout Plan

### Slice 1: External Candidate Audit

Read-only investigation of the Bartman and axewater repositories.

Deliverable:

```text
docs/validation/winuae-agent-debugger-audit-<date>.md
```

It records versions, licences, patch files, build/release provenance, debugger
operations, launch options, dependencies, known limitations, and a clear
adopt/fork/reimplement recommendation. No binary is checked in.

Exit condition: the project can name a reproducible candidate and its known
unsupported operations.

Audit result: [WinUAE Agent Debugger Candidate Audit — 2026-07-22](../validation/winuae-agent-debugger-audit-2026-07-22.md)
found a credible GDB path but insufficient source/build/headless evidence for
adoption. Its recommendation is a reviewed, pinned fork/adaptation and a small
project-owned Windows spike; it explicitly rejects adopting an opaque prebuilt
binary or MCP server as the harness foundation.

### Slice 2: Capability Probe And Non-Interactive Smoke

Add a WinUAE runtime capability that proves a configured executable, selected
ROM, debugger transport, and headless launch are usable in the local Windows
workspace. Run a minimal legal fixture under a bounded agent-controlled session.

Exit condition: success and each expected missing-resource failure produce a
classified report and clean teardown.

### Slice 3: Read-Only Debugger Contract

Implement the minimal debugger adapter: connect, pause/continue, single step,
breakpoint, registers, memory read, process status, and graceful shutdown.

Exit condition: focused tests use a fake GDB server for protocol behavior; one
opt-in integration smoke proves a real WinUAE session.

### Slice 4: Coverage And Reachability Investigation

Add executed-PC range coverage, selected-range breakpoints, bounded recent-PC
or control-transfer history, and source-locator mapping. Start with an
original-only target session and one known static-analysis gap.

Exit condition: a candidate code range can produce either an observed entry
path with its predecessor context or a clear `not_observed` result scoped to
the named scenarios. The report must not infer that the latter is unreachable.

### Slice 5: Trace Import And Agent Loop Consumption

Export coverage, observed transfers, breakpoints, writes, and snapshots through
the Proposal 003 trace schema. Let the agentic reversing loop surface
trace-backed candidate xrefs, entrypoints, and classification evidence without
auto-accepting them.

Exit condition: one documented original-target run yields a reviewed,
provenance-bearing dynamic fact that helps resolve a real source-quality gap,
or an explicit no-action result. It does not create free-form notes merely to
exercise the loop.

### Slice 6: Scenario, Warm-Start, And Artifact Contract

Add a typed scenario parser, deterministic input scheduling, timeout capture,
checkpoint evaluation, cold-boot/warm-start identity rules, and gitignored
artifact manifest. Start with a small project-owned fixture, not a protected or
complex game target.

Exit condition: an intentional assertion failure produces a readable state
diff and artifacts, while a success has stable normalized report content. A
warm-start run is rejected when its emulator/profile/media stamp differs and
has a linked cold-boot validation path.

### Slice 7: Original/Rebuilt Behaviour-Preservation Test

When an intentional target change needs protection, integrate a target whose
image and ROM prerequisites are available. First document a small set of stable
original behaviour checkpoints, then compare the modified rebuilt target at
those checkpoints. Keep the framework round-trip gate separate in reports and
CI summaries.

Exit condition: the local report distinguishes byte reproduction from runtime
equivalence and names the exact observation that diverged. CI promotion is a
later follow-up after local scenarios have stable evidence and legal resources.

### Slice 8: Target-Specific Hybrid Adapters

Only after rebuilt-mode testing is useful, introduce a hybrid adapter for a
specific target/loader. Treat each adapter as a small, highly verified
integration with its own test matrix.

Exit condition: adapter injection has an auditable report and demonstrates a
reversing use case that full rebuilt mode cannot yet provide.

## Non-Goals

This proposal does not:

- make WinUAE or an external debugger the authority for M68K instruction facts;
- replace spec-driven M68K tooling or its independent oracle checks;
- require every target to run in an emulator;
- require screenshot-perfect output for every runtime test;
- redistribute Kickstart ROMs, game images, or proprietary emulator binaries;
- make GDB protocol itself a durable public schema;
- grant agents hidden UI automation or a private mutation channel;
- treat a runtime pass as byte-exact reproduction;
- implement universal original-media code injection.

## Acceptance Criteria

The proposal is ready to close only when all implemented slices demonstrate:

```text
WinUAE capability reports artifact presence, runnable status, identity, and
missing-resource diagnostics through the project tool graph.

One locally headless Windows session can be launched, debugger-controlled,
bounded, and torn down without a visible emulator window, manual UI input, or
display/input hardware.

The debugger interface supports the minimum read-only diagnostic operations and
is covered by protocol fakes plus an opt-in real-emulator smoke.

Coverage-guided reachability reports executed ranges, selected range hits, and
bounded predecessor context mapped to target locators. They distinguish a
dynamically observed edge from a static proof and never treat `not_observed` as
unreachable code.

One original-target coverage investigation produces a reviewed,
provenance-bearing candidate fact that resolves a real source-quality question,
or correctly records that the supplied scenarios gave no evidence.

Scenarios are typed, versioned, content-stamped, and yield structured statuses
and gitignored artifacts.

Original, rebuilt, and hybrid modes are explicit and never conflated.

Warm-start states, if introduced, are strictly identity-stamped accelerators
with a cold-boot validation path; they are not opaque test baselines.

When behaviour-preservation testing is introduced for an intentional target
change, differential comparison reports normalized observation-level
differences and does not weaken the framework exactness gate.

Runtime facts enter analysis only through the existing provenance-aware trace
path and remain conservative.

When CI is later introduced, it can skip with a clear capability/resource
diagnosis when legal ROM/media resources are unavailable; it must not silently
pass an unexecuted test.

Agent use follows the same harness/CLI and report contracts as humans and CI.
MCP, if offered, is a thin semantic adapter over those contracts.
```

## Verification Strategy

Tests should be layered:

```text
unit: profile resolution, coverage-range normalization, scenario validation,
      status mapping, and source-locator mapping
unit: fake debugger server protocol and timeout/teardown paths
fixture: legal minimal Amiga executable under pinned profile
local integration: configured WinUAE plus legal Kickstart resource and
                   invisible/non-interactive session proof
local target integration: original-only missing-edge/coverage investigation
later local integration: original/rebuilt checkpoint comparison for an
                         intentional behaviour-affecting change
later CI: Windows runner non-interactive smoke and selected stable scenarios
```

For every integration failure, upload a manifest plus bounded diagnostics:
emulator log, debugger transcript, profile identity, register snapshot,
selected-memory dumps, and optional frame/audio captures. Avoid unbounded dump
sizes and never upload proprietary ROM/media unless repository policy permits
it.

## Open Investigation Questions

These must be answered by the candidate audit rather than assumed:

1. Which exact WinUAE build and patch set offers GDB control, and can it be
   rebuilt reproducibly from pinned sources on Windows?
2. Does local scripted operation reliably launch/connect/terminate headlessly
   on the intended Windows workstation, with no visible window or display/input
   dependency?
3. Which GDB remote operations actually work for 68000 registers, memory
   reads/writes, execution control, hardware/custom-chip state, and watchpoints?
4. What prevents deterministic comparison: JIT, host filesystem timestamps,
   RTC, input timing, audio/display threads, drive state, or save-state format?
5. Can emulator time/frame progression be controlled or observed precisely
   enough for scenario scheduling?
6. Is the MCP proof of concept a useful reference implementation, a vendorable
   component, or only a source of patch ideas?
7. What legal resource-provisioning mechanism can support the local workspace,
   and later public CI, without committing ROMs or protected media?
8. Can the selected WinUAE build expose a bounded recent-PC/control-transfer
   history efficiently, or does that require a small reproducible emulator
   patch beyond GDB breakpoints and reads?
9. At which loader/operating-system checkpoint can a warm-start state be saved
   without retaining target-specific code or stale data, and does it produce a
   material speedup over cold boot?

## Working Notes: Local Bartman Build Probe (2026-07-22)

These notes record an exploratory build setup only. They do not select Bartman
WinUAE as the runtime baseline, establish headless operation, or make the
unversioned dependency bundle acceptable for a reproducible implementation.

- Clone location: `resources/clone_amiga/WinUAE`, based on Bartman commit
  `b34884cc25e561eecac5dcec70cac97d6b12b2d9`. Its publish remote is now the
  project fork `https://github.com/rmtew/WinUAE`.
- The headless-runtime work is published as
  `origin/codex/local-workspace-build` at `e53b7a8e8210b57b00675bff5a4c45086ed59331`,
  five commits ahead of `origin/master` and with no upstream-master divergence
  at the time of publication. This branch contains the portable build paths,
  strict headless startup, committed runtime-bundle output, first-run hardening,
  and GDB breakpoint-slot initialization fix.
- The clone's Visual Studio project is
  `od-win32/winuae_msvc15/winuae_msvc.vcxproj`. Its historical `C:\dev`
  dependency references were changed to the project-local default
  `resources/clone_amiga/WinUAE/winuae-deps`. The MSBuild property
  `WinUaeDepsDir` permits an explicit local override without restoring
  `C:\dev`. Its historical user-specific output paths likewise now default to
  `resources/clone_amiga/WinUAE/build/<platform>/<configuration>` via
  `WinUaeOutputDir`.
- The currently tested dependency input is the Bartman workflow's
  `winuaeinclibs.zip`, downloaded on 2026-07-22. Its SHA-256 is
  `19C39817FE7D92704980291714ACDE5ADD798151338695C3A0450C51F7C4B7B1`.
  It is an unversioned external archive and therefore evidence of the old build
  arrangement, not a pinned dependency source for this project.
- Extract that archive into `winuae-deps`. The following x64 compatibility
  copies were accepted by the linker:

  ```text
  zs.lib         -> zlibstat.lib
  enet.lib       -> enet_x64.lib
  prowizard.lib  -> prowizard_x64.lib
  FLAC.lib       -> libFLAC_static.lib
  ```

  `softfloat.lib` is not supplied by the archive. The selected project already
  compiles the SoftFloat implementation sources, so the redundant
  `softfloat.lib` dependency was removed from `FullRelease|x64`; the link then
  succeeded. Treat these mappings as verified only for this exact archive and
  configuration; record any further mapping with its source filename and link
  result.
- Source review of this fork's runtime flags found that `use_gui=no` disables
  the configuration GUI, and `headless=yes` suppresses `ShowWindow` calls for
  the emulation window. It is **not** hardware-free headless operation:
  `graphics_setup()` still runs and `win32gfx.cpp` still calls `CreateWindowEx`
  for an invisible popup. Therefore these flags are insufficient for the
  proposal's local no-display/no-window-creation contract. A viable Bartman
  path requires a bounded source patch and a real invisible-session proof, not
  merely a configuration profile.
- The same tree contains `od-win32/win32_nogui.cpp`, which supplies stub
  graphics setup/initialization functions. The current GDB Visual Studio
  project instead compiles `win32gfx.cpp`, `win32gui.cpp`, `direct3d.cpp`, and
  `direct3d11.cpp`; no existing project configuration selects the no-GUI
  translation unit. It also contains 32-bit-only MSVC inline assembly, so it
  cannot simply be selected by the current x64 project. This is still the
  clearest seam, but the work is a small modern x64 headless backend (or a
  deliberate port of this file), plus a separate build target and compile/link
  probe—not merely an item-list switch.
- A first x64 probe that replaced only `win32gfx.cpp` compiled but produced 75
  unresolved graphics/monitor/vblank/input symbols. This is useful interface
  inventory, not evidence that a clean local solution is impossible: those
  symbols form the host-video boundary currently provided by `win32gfx.cpp`.
  The acceptable implementation is a named null-video backend with defined
  semantics for each supported operation and explicit `unsupported` behaviour
  for capture/display features. Do not add ad-hoc no-op stubs merely to satisfy
  the linker. Its completion gate is a separate build target, no `CreateWindow`
  or Direct3D initialization on the runtime path, and a bounded GDB smoke.
- The GDB service is selected by `debugging_features=gdbserver`. It binds only
  to `127.0.0.1:2345` and waits for a TCP debugger connection during its debug
  loop. Bartman's prebuilt client is available from the local clone of
  `vscode-amiga-debug` at commit
  `055097bba74dd1b2f764dcb90781d2017bd1d499`:
  `bin/win32/opt/bin/m68k-amiga-elf-gdb.exe` (GDB
  `17.0.50.20250202-git`, SHA-256
  `D423D93677EE0E718282765161F7F55352A8E8709B3BD03AE43409BCE1717BC9`).
  Use this prebuilt client as the local external-tool dependency; do not
  rebuild it or install WSL merely for the initial runtime probe.
- A local source-level headless path was then added on branch
  `codex/local-workspace-build`. An explicit `-s headless=yes` is detected
  before host initialization, so WinUAE skips its otherwise-created `Useless`
  helper window, physical display enumeration, display-mode sorting, and the
  initial Direct3D probe. The same early request is carried into target option
  fixup before any display lookup; this avoids the legacy `no display
  adapters!` GUI error when the deliberately empty display list is used.
  Parsed headless mode also bypasses display-dependent preference fixup,
  renderer/window initialization, and graphics-buffer updates. This is a
  direct source patch to the existing x64 build, not the rejected collection
  of linker stubs or a claim that `win32_nogui.cpp` is usable as-is.
- A bounded local smoke test on 2026-07-22 launched the rebuilt executable
  with `-portable -s use_gui=no -s headless=yes -s
  debugging_features=gdbserver`, ran it for five seconds without a ROM, and
  terminated that exact process. It was alive after five seconds, had a zero
  main-window handle, and owned no top-level windows. The earlier no-adapter
  popup exposed an option-ordering bug in the first patch and did not recur
  after the early headless request was made authoritative. This proves only
  no-ROM host startup; it does not yet prove boot, debugger connection,
  target execution, capture, or a display-less Windows runner.
- A second bounded test on 2026-07-22 supplied the legal local Kickstart 1.3
  ROM and explicit `68000`, `ECS`, `1 MB chip`, no-slow/no-fast-RAM, no-media,
  no-sound settings. The process remained headless and Bartman's prebuilt GDB
  attached conventionally with `target remote 127.0.0.1:2345`. It read
  `pc=0x00fc00d2`, `sp=0x11114ef9`, and the first 16 bytes at `0x00fc0000`
  (`11 11 4e f9 00 fc 00 d2`) before sending GDB's standard `kill` request,
  which Bartman's server maps to `uae_quit()`. This proves local agent-relevant
  register and bounded-memory introspection against a live headless ROM boot.
  It does not yet prove target-media boot, breakpoints, execution control,
  watchpoints, or save states.
- The validated Windows x64 executables are now intentional checked-in
  resources at `ext/tools/winuae/windows-x64/`, with hashes and provenance in
  `manifest.json`. The WinUAE project writes its `FullRelease|x64` executable
  directly to that directory; the related local fork history is on branch
  `codex/local-workspace-build`. The bundle excludes
  ROMs, target media, user paths, PDBs, logs, and generated configuration.
- `tools/run_winuae_headless.ps1` is the local agent-facing launcher. It takes
  an explicit legal ROM path, stores mutable INI/data state under the caller's
  temporary directory by default, waits for loopback GDB, runs an optional GDB
  command array, returns JSON, and ends through GDB `kill`. Both GDB launches
  use hidden console windows; this is part of the local headless contract.
- The first target-media smoke mounted the imported original
  `Pandora (1988)(Firebird).adf` as `DF0:` and completed the same hidden
  GDB/clean-shutdown path. GDB initially stops at the Kickstart reset vector
  (`pc=0x00fc00d2`), so this proves media attachment only. It does not yet
  prove Pandora execution, a loaded-program address, or a target breakpoint;
  those require a controlled continue/pause checkpoint in the next slice.
- A bounded persistent MI-mode GDB session is now available through
  `tools/run_winuae_headless.ps1 -ContinueSeconds <n>`. It retains one hidden
  GDB connection through continue, interrupt, PC/SP and bounded-memory
  inspection, and GDB `kill`; WinUAE state is isolated beneath `C:\tmp` per
  invocation. An eight-second cold boot with the original Pandora ADF paused
  at `pc=0x00fc0f90`, still in Kickstart ROM. This proves controlled execution
  and pause, but not DOS completion, the `startup-sequence` `wait 5`, or
  Pandora's executable entry. The next observation must identify the active
  Exec task/process or an OS loader event before claiming target reachability.
- The next NDK-backed observation reads ExecBase's current task plus capped
  `TaskReady` and `TaskWait` lists. At twelve seconds it found the `Initial
  CLI`, `CON`, and two `File System` processes, but no `pandora` process; the
  current task at that sample was `input.device`. This establishes a DOS-stage
  boot checkpoint while leaving the startup-sequence and executable-load
  transition unproven. Persistent-session results are returned as nested JSON
  observations rather than an escaped debugger transcript.
- A second persistent-session phase can now resolve `dos.library` through the
  live Exec library list and derive `LoadSeg` from the parsed NDK. With the
  twelve-second DOS checkpoint plus a thirty-second loader watch, the resolved
  base was `0x00005d20` and `LoadSeg` was `0x00005c8a`; its breakpoint did not
  fire before the bounded timeout. The breakpoint was accepted, so this is a
  valid negative result for this one cold-boot timing window, not evidence that
  Pandora is absent or unreachable. The next investigation should identify the
  command/segment currently associated with `Initial CLI` or establish whether
  the headless profile advances the startup delay at the expected rate.
- Process inspection now reports a process's `pr_SegList` BPTR, live code
  address, and a 16-byte prefix. At the twelve-second checkpoint `Initial CLI`
  pointed to code at `0x00005ed8` with prefix
  `003fcf86003fd3e8003fe0b500000000`, which does not match the imported
  Pandora payload prefix `33fc7fff00dff09a33fc7fff00dff096`. Thus Pandora had
  not been loaded at that checkpoint. A normal visible WinUAE run has since
  been observed reaching a starfield title state, so the next comparison must
  use its exact saved machine profile; do not infer that profile merely from
  an old configuration-list screenshot.
- The visible reference run was confirmed as WinUAE's
  `a500_13_512_512.uae`: OCS, 512K chip RAM, and 512K slow RAM. The headless
  runner now uses those values rather than its earlier ECS/1MB-chip/no-slow
  probe profile. Its manually selected maximum floppy slider maps to
  `floppy_speed=800`, which the headless runner also sets explicitly. The title
  progression requires mapped joystick input; mouse clicks are not a valid
  scenario action. Input injection remains a later, explicitly documented
  capability after this matching cold-boot profile is observed reaching the
  same state.
- A payload-identity observation accepts an explicit decoded target artifact,
  reads 16 bytes at the paused PC, and reports a match only when that sequence
  has one exact payload offset. With the matched profile at sixty seconds, the
  live PC was `0x00010c84`; its bytes matched the Pandora decoded payload only
  at offset `0xC84`, establishing runtime base `0x00010000`. This proves that
  Pandora code is executing within the `Initial CLI` process. Runtime reports
  therefore distinguish Exec's `active_task`/`active_process` from
  `active_execution.payload`; a process name alone is not a program identity.
  It does not yet identify the starfield checkpoint or inject the required
  joystick action.
- The exploratory command is:

  ```text
  MSBuild.exe od-win32\winuae_msvc15\winuae_msvc.vcxproj /m \
    /p:Configuration=FullRelease /p:Platform=x64 /nologo
  ```

  It currently requires the installed Visual Studio C++ toolchain and normal
  Windows access to its per-user SDK metadata. On 2026-07-22 it successfully
  produced `ext/tools/winuae/windows-x64/winuae-gdb.exe` (28,682,752 bytes), with only
  the project's existing x64 base-address warning. This is a build probe only;
  it neither launches WinUAE nor proves the required invisible/headless
  contract.
- Runtime-PC attribution must be a first-class projection of target analysis,
  not a byte scan over rendered assembly. A Pandora probe proved the wrapper
  executing at `$00010BC6` from decoded source offset `$00000BC6`; the
  canonical listing currently maps that source row only through the initial
  `$00020000` decompression-load view. Adding a confirmed `$00010000`
  source-zero copy view correctly passed fact seeding after temporal-overlay
  support was added, but exposed an existing source-render provenance invariant
  at `$00006138`. The attempted source-rendering view was removed through the
  command API so the target remains renderable. Instead, the manual-action
  model now has a separate runtime-observation view: it is persisted with its
  debugger evidence, emitted only for the listing artifact, and is never
  supplied to C source rendering. The corrected Pandora observation maps
  runtime PC `$00010BC6` to canonical row
  `s0:00000BC6:instruction:766` while retaining the initial `$00020000`
  rendering view. This is the right boundary for debugger attribution. A
  future confirmed copy that must change rendered source still needs explicit
  temporal source-provenance support; do not promote a debugger observation
  automatically. Do not substitute rendered-source parsing or add joystick
  injection first.
- The public `amiga-winuae-session` entrypoint is now a strict read-only
  wrapper around `tools/run_winuae_headless.ps1`, replacing its former
  GUI/debugger-session model and stale clone path. Its default operation prints
  an explicit launch plan; `--run` invokes the already-bounded headless runner
  with the target's decoded payload, then returns `mapped`,
  `mapped_with_runtime_view`, `unmapped_runtime_address`, or
  `not_target_payload` PC attribution. The second status means a repeated byte
  sample was disambiguated only by an already-reviewed observation view; it
  does not create that view. The entrypoint does not accept arbitrary GDB
  commands and does not append target facts. This is the minimal agent-facing
  observation contract; selected evidence remains a reviewed Manual Action Log
  decision.
- Code breakpoints are a usable checkpoint primitive after a normal boot and
  a controlled pause. The initial failure at runtime `$00010BA8` was a fork
  defect: the GDB `Z0` handler reused a disabled WinUAE breakpoint slot without
  resetting its `cnt` hit counter or `chain` field. WinUAE's own
  `instruction_breakpoint()` constructor resets both. The pinned fork now does
  the same. On 2026-07-23, the strictly headless Pandora runner booted for 60
  seconds, paused at `$00010C9C`, installed `$00010BA8`, continued, and
  received GDB `breakpoint-hit` with `pc=0x10ba8`. Do not arm ordinary code
  breakpoints from the reset vector: WinUAE's trace-check path then evaluates
  each Kickstart instruction and makes boot impractically slow. The harness
  therefore follows the extension's operational model: reach a known target
  checkpoint first, then arm bounded code breakpoints.
- The public `amiga_reversing.tools.winuae_session` wrapper accepts a canonical
  `--breakpoint-stable-key`, never a raw GDB address. It validates the current
  listing row, uses a reviewed runtime-observation view when one covers that
  row, otherwise requires a uniquely matched live payload checkpoint, and
  reports the requested row plus the observed breakpoint result. The same
  Pandora run verified `s0:00000BA8:instruction:755` at `$00010BA8`.
- A breakpoint result also records the paused 68K stack return address. This
  turned the first reachability probe into a control-flow result: title-state
  execution reached `s0:00000E14:instruction:967`, returning to `$00010904`.
  Static inspection identifies the preceding `$00010902` instruction as
  `jsr (app_0360)`, after the Copper interrupt bit is tested. That evidence
  supports the rendered label `handle_copper_interrupt_palette_effect`; it
  does not itself make the generic app slot name authoritative.

## Decision Record

Do not begin implementation merely because a headless-looking command line
exists. Begin after Slice 1 answers source provenance and after Slice 2 proves
the local **headless** agent/debugger contract on the intended Windows
workstation. CI promotion comes only after the local coverage-guided reversing
workflow has demonstrated value, but it must reuse that already-headless
implementation. This proposal then provides the architecture and acceptance
conditions for a small, evidence-producing integration rather than a
speculative emulator subsystem.
