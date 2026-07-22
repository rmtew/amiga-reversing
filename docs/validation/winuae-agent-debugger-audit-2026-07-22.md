# WinUAE Agent Debugger Candidate Audit — 2026-07-22

Scope: read-only external-source audit for Proposal 036, Slice 1. This audit
did not download, run, build, or add any emulator binary. It does not prove
the mandatory local headless agent-controlled operation. GitHub Actions is a
later consumer of that same required capability.

## Decision

Do not adopt a prebuilt emulator binary or the MCP server as a project runtime
dependency yet.

Use the GDB-enabled WinUAE work as the reference for a small, project-owned
spike. The likely route is to fork/adapt the minimal WinUAE GDB server patch,
pin it to a reviewed source commit, and place a project-owned typed client/CLI
over GDB RSP. `mcp-winuae-emu` is a useful reference and optional later adapter,
not the core harness.

This is an **investigate/fork** recommendation conditional on source-level
patch review and reproducible Windows build. It is not an adoption approval.

## Sources Audited

| Candidate | Audited source | Observed identity | Role |
| --- | --- | --- | --- |
| Bartman Amiga Debug | [BartmanAbyss/vscode-amiga-debug](https://github.com/BartmanAbyss/vscode-amiga-debug) | 1.8.2 release dated 2026-04-26; modified WinUAE 4.9.0 declared | Original practical GDB-enabled WinUAE lineage and VS Code integration. |
| Bartman WinUAE fork | `https://github.com/BartmanAbyss/WinUAE` | `HEAD` was `b34884cc25e561eecac5dcec70cac97d6b12b2d9` on 2026-07-22 | GDB-server fork named by both other projects. |
| axewater MCP bridge | [axewater/mcp-winuae-emu](https://github.com/axewater/mcp-winuae-emu) | v1.0.0 dated 2026-02-10; 7 commits; MIT | Agent-facing GDB RSP bridge and launch/config reference. |
| axewater WinUAE fork | `https://github.com/axewater/WinUAE`, branch `gdb-write-commands` | branch tip was `9d7baae3eeadf189b03d8848ff7520a3f1b7afe2` on 2026-07-22 | Claimed Bartman extension with memory/register writes. |

The commit IDs are remote branch tips seen during the audit. They are not
vendored sources and must be resolved again and pinned by implementation.

## Established Facts

### axewater Patch Scope: Source Review Follow-Up

Source was inspected locally at tag `v1.0.0`, commit
`9d7baae3eeadf189b03d8848ff7520a3f1b7afe2`. Its direct parent is
`b34884cc25e561eecac5dcec70cac97d6b12b2d9`, the observed Bartman fork head.
It is therefore not a separately diverged emulator: it is one small commit on
top of Bartman's current fork.

```text
5 files changed, 161 insertions, 5 deletions

92 additions, 2 deletions  od-win32/barto_gdbserver.cpp
 3 additions, 3 deletions  od-win32/winuae_msvc15/winuae_msvc.vcxproj
52 additions               HANDOVER.md
 8 additions               build.bat
 6 additions               build_with_nasm.bat
```

The functional change is limited to `barto_gdbserver.cpp`:

- receive/GDB advertised packet size changes from 512 to 65,536 bytes;
- `P` writes one register (D0-D7, A0-A7, SR, or PC);
- `G` writes all 18 registers in the existing readback order;
- `M` writes bytes through `debug_safe_addr()` and the relevant memory bank's
  `bput()` method.

The register order is consistent with the existing `g` response: D0-D7,
A0-A7, SR, then PC. `SR` writes call `MakeFromSR()` to synchronize internal
condition state. The project-file changes replace one contributor's hardcoded
output directory with a path relative to the solution; the two build scripts
still contain fixed `C:\Scripts\WinUAE`, Visual Studio Build Tools, NASM, and
dependency-directory assumptions.

This is exactly the kind of small patch that is practical to own, but it needs
hardening before it is a project runtime dependency:

- the new `M` path does not check that the request contains `2 * length` hex
  characters before indexing it; malformed/truncated input can read beyond the
  request payload;
- non-hex characters silently contribute zero nibbles instead of returning an
  error;
- the 64 KiB packet-size increase needs bounded packet framing and allocation
  review under partial/multiple TCP receives, rather than assuming one `recv()`
  call equals one complete GDB packet;
- PC/SR and memory-write semantics need an actual target smoke test, including
  writes to ordinary RAM versus memory-mapped/custom-chip space.

Conclusion: axewater is the correct single candidate to inspect and adapt. Do
not build a second Bartman-based implementation. Retain Bartman only as its
direct parent/reference, and carry forward a reviewed, hardened version of this
one patch when the local headless spike begins.

### Bartman GDB Lineage

The extension documents a GDB-enabled WinUAE with source/assembly debugging,
call stacks, breakpoints, data breakpoints/watchpoints, watches, registers,
memory view, a mounted host directory, warp controls, and frame/DMA profiling.
See its [feature list](https://github.com/BartmanAbyss/vscode-amiga-debug#features).

Its README identifies the bundled emulator as modified WinUAE 4.9.0. It says
WinUAE builds with Visual Studio 2022, but the audited material does not provide
a complete reproducible fork build recipe or a source-to-release binary hash.

An older project description says roughly 99% of the WinUAE changes reside in
`od-win32/barto_gdbserver.cpp|h`. That suggests a narrow patch boundary, but is
not a substitute for a source diff against the pinned upstream base. The actual
diff, build inputs, and changes outside these files remain unverified.

Documented caveats include debugger exception handling needing improvement,
one unreliable Kickstart step-out path, A4000 execution described as flaky, and
target-specific saved-state graphics-debugger limitations. Start with a pinned
A500/68000 OCS/ECS profile and basic PC/memory/breakpoint operations.

### axewater MCP Bridge

The bridge explicitly uses GDB Remote Serial Protocol to launch/control a
custom WinUAE fork. Its [README](https://github.com/axewater/mcp-winuae-emu)
documents:

| Group | Operations |
| --- | --- |
| Lifecycle | launch/connect, status, disconnect/stop |
| CPU | register read/write, step, continue, pause, reset |
| Memory | read, write, dump, load binary |
| Control | software breakpoint and read/write/access watchpoint set/clear |
| Hardware | custom-register decode and Copper-list decode |

It launches:

```text
winuae-gdb.exe -portable -G -s debugging_features=gdbserver -s debugging_trigger=
```

and retries localhost TCP port 2345. Its README says that in its WinUAE v4.10.1
build, `-G` and debugger overrides must be command-line arguments because
config-file `use_gui` and `debugging_features` are ignored.

This is positive evidence for programmatic launch and debugger connection. It
is not headless evidence: the audit found no invisible-window/no-display proof
or bounded shutdown demonstration. Local headlessness must be proven before the
runtime is useful to the agent; runner execution is a later concern.

Documented limitations are Windows-only operation, one GDB client, no CIA
register reads through GDB memory, zero ECS/AGA-only register values on OCS, and
an intentionally minimal m68k disassembler. CIA state therefore cannot be a
general initial checkpoint assertion; the project knowledge/disassembler tools
remain authoritative for M68K interpretation.

## Coverage-Guided Reachability Suitability

The documented operations are enough for the smallest useful experiment:

```text
launch original target
  -> break at suspected code-range entry
  -> continue with a bounded timeout
  -> capture PC, D0-D7, A0-A7, SR, stack memory, selected RAM
  -> map address to target listing/source locator
```

That proves a range executes and preserves stop context. Watchpoints may help
investigate tables, subject to real behavior testing.

It does not provide the predecessor history needed to recover a missing edge.
The audit found no documented executed-PC coverage bitmap, bounded recent-PC or
branch ring buffer, or source-locator mapping. Before claiming coverage support
the project must prove either:

1. an emulator-side bounded PC/control-transfer ring buffer; or
2. a bounded host-driven probe using breakpoints at candidate indirect branches
   and candidate entries, suitable only for one concrete analysis gap.

Do not use an unbounded host-side single-step trace as the normal solution. It
is likely too slow and voluminous for game execution.

## Reproducibility And Licensing

| Area | Assessment | Required before adoption |
| --- | --- | --- |
| Source provenance | Partial: remote refs and documented relationship, but no source diff review. | Clone pinned forks, identify upstream base, and create a reviewed patch series/source manifest. |
| Binary provenance | Insufficient: MCP README instructs users to download a prebuilt `winuae-gdb.exe`. | Do not make an opaque release binary the local harness foundation; build pinned source and record SHA-256, compiler versions, and command. |
| WinUAE build | Insufficient: no complete fork recipe in audited docs. | Demonstrate clean Windows build in disposable workspace, then automate it. |
| MCP bridge | MIT according to its repository. | Pin its dependencies if used as an optional adapter; MIT does not relicense the emulator. |
| Emulator/fork licence | Not established here. The extension is GPL-3.0 and identifies modified WinUAE, but distribution duties need primary-source verification. | Review upstream/fork licence files and notices before distributing a modified binary or CI artifact. |
| ROM/media | Valid Kickstart ROM and config are required. | Keep ROM/media out of git/public artifacts unless licensed; return classified missing-resource results. |

## MCP Assessment

The bridge proves an AI client can issue GDB operations through MCP and is a
useful reference for launch arguments, RSP handling, and the claimed
register/memory-write patch. It should not be the authoritative project
interface because CI and tests need a direct typed JSON-reporting CLI/library;
it is small and depends on a separately downloaded binary; its default tool set
includes unrestricted writes; and it does not supply Proposal 036's coverage,
locator, scenario, provenance, artifact, or comparison contracts.

Recommended role: later optional adapter over project-owned semantic operations
such as `investigate_reachability` and `inspect_checkpoint`. Do not vendor or
adopt it in Slice 2.

## Mandatory Local Headlessness And Save States

The next Windows experiment is local agent operation, not GitHub Actions. It
must prove a genuinely headless run: no visible window, no display/input-device
dependency, no manual hotkeys, and no GUI scraping. It must also launch or
attach, connect within a fixed budget, hit a breakpoint, capture diagnostics on
timeout, terminate its process tree, and avoid leaking ports/configuration
across repeated sessions.

No audited source proves this mandatory headless contract. CI promotion is
deferred, but must reuse the locally proven headless implementation.

The Bartman extension's saved-state notes establish only that save states exist
in broader tooling. They do not establish a portable CI warm-start contract.
Treat warm-starts as later optimization after a cold-boot reachability test;
stamp them with emulator, ROM, machine, media, and configuration identity, and
create them before target-specific code is launched or injected.

## Recommended Slice 2 Spike

After source review, run only this bounded proof:

```text
Input: pinned reviewed WinUAE fork source; legal external Kickstart ROM;
       legal minimal 68000 fixture; fixed A500/68000/OCS(or ECS) profile.

Proof: launch with GDB; connect on localhost; set one known breakpoint;
       continue; read PC, complete CPU registers, and a small RAM range;
       record executable/config/ROM/fixture hashes; terminate by timeout.

Artifacts: one JSON capability/probe report and bounded emulator/debugger logs.
           Commit no binary, ROM, or game media.
```

Only after it passes should the project investigate a real Pandora static
analysis gap. The next decision is whether GDB stop context suffices or needs a
small reviewed bounded control-flow-history patch.

## Audit Limits

This audit used public repository documentation and remote-ref queries on
2026-07-22. Until source checkout and opt-in Windows execution, the following
remain unverified: fork diff and exact upstream ancestry; reproducible build
and release equivalence; GDB packet/watchpoint behavior; mandatory local
headless operation and later CI operation; timeout/process-tree teardown;
save-state validity; and target-address-to-listing mapping.
