> Current setup and shared UI/CLI/MCP restoration validation: [2026-10-12 report](validation/restoration-framework-2026-10-12.md). The absent local wheel and full-target C include-path limitations below are now resolved.

> Initial assessment at the pre-migration baseline. The authorized follow-up replaces the active runtime with Copperline; see [current runtime and validation](copperline-runtime.md). Kickstart and the decoded Pandora payload were subsequently found in the existing environment, so earlier missing-input claims below are superseded.

# Linux baseline and Copperline assessment — 2026-10-11

Baseline: public `master` at `1c50d3e764f7a20715d99f719dc363af2fdda757`
(2026-08-04, “Record canonical reducer layering decision”). Work is isolated in
`/workspace/amiga-reversing`, branch `codex/linux-baseline`. The separate tennis
checkout was only consulted for environment/tool setup instructions; no files,
inputs, branches, builds or running tasks there were changed. Its documented
`.tools` caches were not present in this fresh environment.

## What is implemented

This is a substantial, locally developed reversing workbench, not just a
scaffold. The package still calls itself version 0.1.0 and its setup is strongly
Windows-specific. README's “C99 scaffold” and 36-target reproduction summary
understate the current code. Conversely, tracked historical reports are not
proof of a passing fresh-checkout gate.

| Layer | Current implementation |
| --- | --- |
| Knowledge | Motorola PDF/Amiga manuals/NDK extraction into committed JSON; Amiga, Atari ST and Classic Mac OS platform metadata; generated C tables. External source documents are needed for re-extraction, not ordinary compilation of committed generated code. |
| Instruction model | `src/scripts/m68k_canonical_model.py` normalizes instruction forms into canonical identities; assembler/disassembler/simulator generators consume these. Tables encode operands, CPU applicability, effective-address forms, encoding and semantic metadata. C runtimes implement generic encoding/decoding and semantic operations. This is data-driven, but not a claim that every runtime operation is generated or every CPU feature implemented. |
| Assembly | `m68k_instruction_spec`, source parsers/models/pipeline, policy and assembler APIs support structured IR, symbolic source, labels, directives, container output and reproduction policies. A complete Amiga HUNK was assembled on Linux. |
| Disassembly and analysis | Decode IR → facts-v2 fixed-point analysis → render IR/plan/source. Tracks code/data, relocations, labels, xrefs, API/library semantics, typed structures, runtime views and source-quality evidence. Platform loaders handle Amiga HUNK/raw/ADF, Atari PRG/disks and Mac HFS/resource/CODE data. |
| Simulator | Abstract register/memory values and joins support static propagation, reachability and address provenance; concrete bounded execution supports unpacking and related analysis. It is not a full Amiga chipset emulator. Unsupported concrete operations explicitly return diagnostics. |
| Python | `amiga_reversing/disasm/c_backend.py` owns ctypes/native calls and DTO translation. Project/source descriptors, manual action logs, listing projection, reproduction, corpus and import workflows orchestrate the C authority. Manual actions regenerate facts/review state; exported `.s` is not the authoritative edit surface. |
| UI | Standard-library `ThreadingHTTPServer`, static HTML/CSS/JavaScript under `amiga_reversing/web`, asynchronous jobs/SSE, project/disk browser, windowed listing, navigation, review/commands and reproduction. No Node build or external web framework is required. API requests use contract header `X-Amiga-Web-App-Contract: 2`. |
| Runtime | `winuae_session.py` is the restricted target-aware public API; PowerShell launcher starts committed Windows WinUAE/GDB binaries; `tools/winuae_gdb_session.py` drives GDB/MI and custom monitor input. Runtime is an observation mechanism, not the source of static truth. |

Fresh canonical coverage check reports 300 assembler forms, 313 disassembler
forms, 299 matched; 293 executor semantics available, five missing and two
intentionally unsupported. These inventories are not independent oracle proof.
Remaining classified gaps include MOVE16 semantics, FSAVE/FRESTORE oracle
coverage, PMMU decode/render/sample/oracle work and generic coprocessor schema.
The generated corpus directory is absent; a direct `verify-manifest` attempt
therefore could not run. The pinned development machine68k wheel is an absent
Windows CPython 3.14 wheel, so Musashi/machine68k oracle coverage was not run.

Important unfinished work is explicit in the repository:

- Proposal 041's native corpus projection migration has R0/R1 complete and R2
  in progress. Its predecessor reports a project-phase performance miss and
  substantial memory usage. This assessment did not launch a full corpus build.
- Proposal 033 and TODO describe false-code/boundary decisions, source-quality
  closure, renderer-side semantic work, typing/naming propagation, strings,
  decompression and target-specific unresolved behavior.
- The committed rendered-source report records **38 full-file exact, 15
  content-exact, one unsupported, zero failures across 54 targets**. It was not
  reproduced here: original binaries/images are absent. Mac source assembly is
  still a reported unsupported path. Full-file exactness and content exactness
  must remain distinct.

## Reproduce the Linux baseline

Verified host: Debian x86_64, GCC 14.2.0, GNU Make, OpenSSL development headers
and libcrypto already installed. Python 3.14.7 was installed with the existing
`uv` into writable tool storage; no global environment or credentials changed.

```sh
cd /workspace/amiga-reversing
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/.tools/python
uv python install 3.14.7
uv venv --python 3.14.7 .venv
uv pip install --python .venv/bin/python -e . \
  pymupdf==1.28.2 pytest==9.1.1 ruff==0.16.10
make -j4
make -C ext/vasm CPU=m68k SYNTAX=mot -j4
cp ext/vasm/vasmm68k_mot tools/vasmm68k_mot.exe
.venv/bin/python -m amiga_reversing.tools.disasm_server --host 127.0.0.1 --port 8123
```

Use `uv pip` here, not `uv sync --dev`: the latter resolves the missing local
Windows machine68k wheel from `pyproject.toml`. This does not establish a
portable full development lockfile. Other installed Python dependencies were
iniconfig 2.3.0, packaging 26.3, pluggy 1.6.0 and pygments 2.21.0.

The Linux Makefile compiles committed generated C and links libcrypto. Native
ELF binaries retain legacy `.exe`/`.dll` path names so existing Python/tool
contracts work; no Wine is involved. One common ELF backend supplies the four
library aliases. This is a Linux baseline, not a Windows build-system rewrite.
`make test` runs all available C suites and currently exits nonzero on the
external decompression-provider failure below.

Live local service: **http://127.0.0.1:8123/**. Verified demonstration:
**http://127.0.0.1:8123/amiga_hunk_cloud-smoke-5**. These are environment-local
URLs, not externally hosted sites. No port-forwarding/public hosting capability
was supplied for a shareable browser URL. Most historical project entries
cannot open their original media until their recorded inputs are supplied.

The reproducible browser/native smoke creates only a small synthetic input and
local project, checks fixed expected bytes, reassembles rendered source using
both C and vasm, opens the real HTTP UI in Chromium, asserts actual listing rows
and no page errors, and saves a screenshot/result under ignored runtime state:

```sh
mkdir -p .runtime-state/baseline
cat > .runtime-state/baseline/chromium <<'SCRIPT'
#!/bin/sh
exec /usr/bin/chromium --no-sandbox --disable-dev-shm-usage "$@"
SCRIPT
chmod +x .runtime-state/baseline/chromium
M68K_RUN_BRAVE_CDP=1 BRAVE_PATH="$PWD/.runtime-state/baseline/chromium" \
  PYTHONPATH=. .venv/bin/python tools/linux_smoke.py
```

The Chromium wrapper is specific to this restricted cloud sandbox. Screenshot:
`.runtime-state/linux-smoke/ui.png`; result: `result.json` alongside it.
Synthetic HUNK SHA256 (44 bytes):
`fb088eb881bf57086e49d309b3b2adc0a4346354d3ac05971f88356af55dc90b`.
C rendered-source output matches exactly; vasm 2.0e matches with `-Fhunkexe
-nosym` (otherwise it adds a symbol record). The normal framework reproduction
also returns `exact` with identical original/rebuilt hashes.

## Fresh tests and limits

Logs are bounded under `.runtime-state/baseline/`; no full instruction traces
or proprietary inputs were retained.

| Command/check | Result |
| --- | --- |
| `make -j4` | Native tools/libraries build. GCC reports existing warning categories; this is not an MSVC `/WX` or sanitizers pass. |
| `.venv/bin/python -m pytest -q --maxfail=3` | Final: **1382 passed, 62 skipped, 355 deselected, one failed**, 6.59 s. Failure: `test_020_006_macos_listing_requires_shared_executable_ranges` accesses absent `resources/platform_macos/MPW-GM.img.bin` before its expected validation. |
| Focused WinUAE/session, GDB-symbol, direct-payload, project and tool tests | 80 passed before the new state regression; mocks/contracts, not actual WinUAE execution. |
| `pytest tests/test_disasm_projects.py -q` | 45 passed including new atomic-publication regression. |
| `src/build/m68k_c_unit_tests.exe` | 771 passed, one failed in external Ancient identification/hash expectations; one Windows-only VirtualAlloc prototype test excluded. Includes 634 IR and 28 simulator cases. |
| `pytest tests/test_api_workflow_harness.py -m route_integration -q` | Five passed. |
| Two selected browser tests | Two passed: project/listing opening and command-palette execution (fixture-backed UI tests). |
| `tools/linux_smoke.py` | Real native assembly, HTTP upload, rendered listing and independent vasm round trip pass. |
| `m68k_coverage check --phase canonical` | Pass with explicitly classified coverage gaps described above. |
| `pytest tests/test_c_backend.py -m 'c_backend and not real_integration' -q --maxfail=6` | 81 passed, one skipped, 126 deselected, stopped at six failures. Two concern unavailable Ancient; two concern Tetragon/adjacent-control-stub analysis expectations; two expect an older include-directory path. These need triage, not blanket dismissal as platform failures. |
| `ruff check` on changed Python files; `git diff --check` | Pass. |

An earlier broad C-backend selection also reached missing GenAm/Magicland
originals. The Windows Ancient executable is committed, but its native Linux
provider/source is not supplied. Non-Windows file-hash support in that provider
path remains a stub; decompression is not validated by this baseline. Do not
substitute an arbitrary upstream Ancient executable: the repository expects a
specific JSON-capable provider contract.

Scoped changes: Linux build recipe; OpenSSL SHA1 disk-ID/SHA256 support; POSIX
case-insensitive comparisons and temporary paths; missing limits include;
portable checked string append; Windows-only allocator-prototype test guard;
and atomic browser-state publication. The last change fixes an observed
GET-project versus POST-open race that produced an empty-JSON error in the real
browser. Instruction tables, semantic algorithms, target facts and emulator
harness were not migrated. Windows recompilation has not been performed.

## Copperline assessment

The official latest release resolved to **1.0.0**, newer than the environment's
old tennis setup recipe (1.0.0-rc.1). Its official AppImage SHA256 was verified
against its published SHA256SUMS before extraction/execution:
`9ab3e2ecc89beb25344bd1b0d8aa3dcf9370ade8f3b08fdec2fb37e59461f55d`.
Tool storage is `/workspace/copperline-assessment`; the extracted binary reports
`copperline 1.0.0`. It runs here without additional system libraries. No
proprietary ROM was downloaded: the probes used bundled AROS.

```sh
cd /workspace/copperline-assessment
touch squashfs-root/usr/bin/portable.txt
RUST_LOG=warn COPPERLINE_DBG_RR_BUDGET_MB=32 \
  ./squashfs-root/usr/bin/copperline --factory --model A500OCS \
  --chip 512K --slow 512K --fast 0 --noaudio \
  --control 127.0.0.1:0 --control-info "$PWD/control-info.json"
```

The currently paused local control server is `127.0.0.1:34605`; its local info
file contains its session token (not copied into this report). It is a separate
assessment process, not connected to the web app. `probe.py` and
`probe_control.py` in that directory retain the exact probes; `probe-result.json`
and `control-proof.json` retain results. Actual checks covered authentication,
register reads/writes, stepping, bounded frame advance, memory reads/writes,
joystick press/release acceptance, PC breakpoint hit, save/restore. A synthetic
instruction sequence in slow RAM set D0 to 42, incremented it to 43 at a
breakpoint, advanced it to 44, then restored PC and D0=43 from a snapshot.
This proves those controls on this machine profile; it does not prove a game
boot, Kickstart 1.3 compatibility, input-driven gameplay or old scenario parity.

| Requirement from existing harness | Copperline 1.0.0 mapping / remaining work |
| --- | --- |
| Strictly headless startup and lifecycle | Native `--control` or `--gdb`, both start paused. Replace PowerShell/UAE configuration and Windows process management with explicit A500/OCS/68000/PAL/512K chip+512K slow profile, isolated writable paths, endpoint discovery, bounded waits and cleanup. |
| Pause/resume/step, registers and RAM | CCP JSON-RPC methods provide these; core probes pass. Normalize register arrays versus GDB expressions, stop reasons and exceptions. Test pause during outstanding execution and reconnect separately. |
| Stable-key breakpoint and payload matching | Retain public source-key resolution, unique byte-match/runtime-base checks, observation schemas and conservative provenance. Use `break.add/remove` after identity is established; repeat-hit/rearm/timeout behavior still needs scenario tests. Never infer identity merely from a runtime address. |
| Input bridge | Replace fork-specific `monitor input port1 fire press/release` with CCP `input.joy`. Existing ports are zero-based; CCP ports are 1–4, `fire` maps to `red`, and omitted buttons are released. Preserve a full held-button state and explicit timing; test actual guest response. |
| Symbolic function entry | GDB supports ELF/DWARF, but headless `--gdb` and `--control` cannot coexist. CCP does not document arbitrary user ELF loading. Prefer retaining canonical host-side function facts and resolving bounded function-entry breakpoints through them; use a separate GDB backend only if symbolic GDB behavior is essential. Do not silently weaken `enter_function` acceptance rules. |
| Amiga process/LoadSeg context | GDB memory reads can retain NDK-based inspection; CCP also exposes segments, loadseg catches and OS queries. Validate equivalent output against a legal Kickstart target; do not treat AROS introspection as parity evidence. |
| Snapshots/reverse/capture | CCP documents save/load, reverse execution, bounded trace/profile and screen capture; snapshot restore was actually checked. Manual memory edits are marked replay-unsafe; host filesystem effects are not rolled back. Avoid unbounded trace/profile defaults. |
| Direct-payload contracts | Existing validated ADF builder can remain. Recheck ROM, memory layout, handoff marker, initial registers and payload hash per contract; migration does not authorize deriving new contracts from decompression metadata alone. |

Recommended implementation order:

1. Keep this Linux work reviewable separately. Define a small emulator-neutral
   session boundary returning existing target observations and structured errors.
2. Implement one native Copperline CCP adapter with pinned version/hash,
   loopback token authentication, explicit profile and isolated lifecycle.
   Preserve the restricted target-facing API; do not expose arbitrary debugger
   commands to the reversing loop.
3. Run the transport acceptance matrix: pause/timeout, reconnect, reset,
   repeated breakpoints, register/stack/memory capture, held inputs and
   snapshot restore. Use synthetic probes first, without saving derived facts.
4. Supply an explicit legitimate Kickstart 1.3 path and one original target
   input, then reproduce an existing bounded Pandora or Magicland scenario.
   Require payload identity, stable-key hit, stack return address, input phase
   behavior and exact source round trip. Compare semantics, not identical
   instruction/frame timings between different emulators.
5. Only after parity, make Copperline the supported runtime and retire the
   patched WinUAE binaries/PowerShell path deliberately. This is a moderate
   adapter/lifecycle/scenario-validation project, not an assembler rewrite or a
   drop-in executable swap. No broad migration was performed here.

Sources: [Copperline release](https://github.com/CopperlineHQ/Copperline/releases/tag/v1.0.0),
[pinned control protocol](https://github.com/CopperlineHQ/Copperline/blob/v1.0.0/docs/debugger/control.md),
[pinned GDB protocol](https://github.com/CopperlineHQ/Copperline/blob/v1.0.0/docs/debugger/gdb.md),
plus repository Proposal 036 and `.agents/skills/headless-amiga-runtime/SKILL.md`.

## Follow-up review: Windows open-reader sharing

Independent review identified a source-level portability risk in the original
atomic publication fix: Windows can reject replacement while another server
request holds the destination open. A shared process-local `RLock` now covers
complete `_load_state` reads (including closing their handles) and `_save_state`
publication. Atomic JSON replacement remains in place.

The added regression holds a real read handle open, simulates Windows'
deny-delete sharing behavior, verifies the writer waits, then verifies it
publishes successfully after the reader closes. Disabling the lock in an
isolated test run makes that regression fail with the modeled `PermissionError`.
This is simulated Windows sharing behavior, not native Windows execution.

Follow-up checks: **51 project/API workflow tests passed**, changed Python lint
and diff checks passed, and the real native/HTTP/Chromium/C-and-vasm smoke passed
again (`amiga_hunk_cloud-smoke-6`). An independent reviewer found no blocking
issues and separately ran the two browser-state regressions successfully.

Scope: synchronization covers threads in this server process. Separate server
processes, external readers, and the pre-existing possibility of lost updates
between separate load/save transactions are not solved by this change. The
full-suite counts above describe the preceding baseline, not a rerun after this
follow-up. No emulator behavior or generated instruction data changed.
