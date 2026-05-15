# Proposal 003: Runtime Tracing

## TODO Coverage

- `TODO.md` Tracing.
- `TODO.md` Phase 6: Emulation-Guided Coverage.
- `TODO.md` Compiler Fingerprinting: run under vamos and extract signatures.

## Current State

- `amiga_reversing.tools.winuae_session` can build a WinUAE command line, write a `.cmd` launcher, and write an Amiga `S/startup-sequence`.
- `resources/clone_common/WinUAE` contains source, but no accessible `winuae64.exe` was found in the expected path.
- C static analysis already has internal trace-state concepts for copied code, indirect stubs, relocation provenance, and decompression writes, but that is not emulator-driven runtime tracing.
- `amiga_reversing.tools.genam_roundtrip` already uses `vamos` for a specific DevPac/GenAm round-trip workflow.

## Clean Near-Term Work

1. Keep WinUAE tracing deferred until a runnable executable path is configured.
   - Add an explicit tool availability check for WinUAE.
   - Report `source_present_but_executable_missing` for the current checkout.
   - Do not add fragile debugger scripting around a missing tool.

2. Turn `winuae_session` into a deterministic session builder.
   - Generate `.uae` configs from structured options.
   - Mount a host directory as an Amiga volume.
   - Generate startup-sequence scripts.
   - Write expected output paths for debugger logs and memory dumps.

3. Add a trace import format before adding multiple tracers.
   - Common fields: target id, tool, CPU, initial PC, breakpoints, executed PCs, memory writes, register snapshots, and captured symbols if available.
   - Store trace artifacts under `bin/rebuilt` or another generated-artifact directory, not in target source.

4. Start with `vamos` where it is already viable.
   - For GenAm and compiler fingerprinting, `vamos` can run AmigaDOS-style binaries without requiring a full emulator GUI/debugger path.
   - Use it for coverage and startup/prologue signature extraction before tackling WinUAE debugger automation.

5. Build compiler fingerprinting as a small corpus first.
   - Inventory SAS/C, Lattice, DICE, Aztec/Manx, GCC, and any project-local examples.
   - Record compiler version, input source, invocation, startup bytes, prologue/epilogue shapes, and runtime library calls.
   - Keep signatures descriptive until repeated examples justify automatic classification.

6. Feed traces back into analysis conservatively.
   - Runtime PCs can propose entrypoints, but should enter as reviewed/trace-derived facts.
   - Memory writes can identify copied/decompressed code ranges.
   - Do not let one trace mark unexecuted code dead without scenario coverage evidence.

## Better Version

- A generic trace ingestion pipeline accepts WinUAE, vamos, or future emulator output through the same schema.
- The static analyzer consumes trace facts through existing policy/metadata paths rather than bespoke side channels.
- Coverage reports show static-known, trace-executed, trace-suggested, and still-unresolved ranges separately.
- WinUAE debugger control should be scripted only after the debugger command set is pinned with examples and tests.

## Larger Architecture Notes

- Static analysis and emulator tracing should remain separate evidence sources.
- Trace-derived facts need provenance and confidence so they can be reviewed and superseded.
- A complete dynamic coverage story needs scenario management: input scripts, save states, disk state, and repeatable timing.
- Compiler fingerprinting should use trace and static signatures together; startup/prologue bytes alone will be too brittle.

## Verification

- Unit tests for WinUAE command/config generation.
- Tool availability tests for missing executable and configured executable cases.
- Fixture trace import tests that produce candidate entrypoints and write ranges.
- Vamos smoke test for a controlled GenAm/AmigaDOS fixture when the environment has vamos.
- No WinUAE integration gate until a runnable `winuae64.exe` path is available.

## Review Sign-Off

Reviewed against `TODO.md` and current code on 2026-05-16. Scope is coherent as proposal work; no implementation is claimed here.
