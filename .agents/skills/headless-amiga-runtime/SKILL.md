---
name: headless-amiga-runtime
description: Operate, diagnose, and improve the repository's strictly headless WinUAE/GDB runtime harness for Amiga reversing. Use when observing a target at runtime, mapping runtime PCs to reconstructed source, setting bounded source-key breakpoints, debugging the harness, rebuilding the pinned WinUAE fork, or verifying runtime-tool changes. Never use it to launch visible WinUAE.
---

# Headless Amiga Runtime

Use runtime evidence to resolve a concrete reversing ambiguity. Static analysis and the normal reversing loop remain the primary source of reconstructed source facts.

## Non-negotiable constraints

- Never launch a visible WinUAE window. This applies locally and in CI.
- Use the public target-aware session interface; do not give an agent arbitrary GDB commands or write target facts directly.
- Use a legal user-supplied Kickstart ROM by explicit path. Do not add ROM images to the repository.
- Do not edit exported target `.s` files. Record target discoveries through normal framework commands/manual actions, then render and round-trip verify.
- Treat a runtime mapping as an observation, not proof of a loader, copy routine, or static control-flow edge.

## Owned implementation surface

Read the relevant implementation before changing it.

| Path | Responsibility |
| --- | --- |
| `tools/run_winuae_headless.ps1` | Strict headless launcher, A500/Kickstart 1.3 profile, GDB process management. |
| `tools/winuae_gdb_session.py` | WinUAE/GDB MI protocol, pause/continue, bounded breakpoint handling, observation capture. |
| `amiga_reversing/tools/winuae_session.py` | Restricted target-aware agent API: stable source keys, observation views, structured results. |
| `amiga_reversing/tools/gdb_symbols.py` | Disposable M68K ELF/DWARF artifacts from canonical function facts. |
| `tests/test_winuae_session.py`, `tests/test_gdb_symbols.py` | Focused public-session and symbol-generation contracts. |
| `ext/tools/winuae/windows-x64/` | Committed Windows WinUAE and m68k GDB binaries used by the harness. |
| `resources/clone_amiga/WinUAE/` | Local Bartman-derived WinUAE fork, on `codex/local-workspace-build`. |
| `docs/proposals/036-agent-operable-winuae-runtime-harness.md` | Architecture, decisions, limitations, and environment notes. |

The fork has a local breakpoint fix in `od-win32/barto_gdbserver.cpp`: reused GDB breakpoint slots must reset `cnt` and `chain`. Preserve that behavior when rebasing or updating the fork.

## Run a target observation

1. Follow `docs/agents/reversing-loop.md` and the relevant parts of Proposal 010 before target work.
2. Establish static evidence first: inspect labels, xrefs, the target entry/load behavior, and candidate source offsets.
3. Invoke `amiga_reversing.tools.winuae_session` with a target id, legal ROM, disk/image input, and a bounded `--continue-seconds` value.
4. Read its structured observation. A valid target mapping requires a uniquely matched payload PC; do not infer it from a guessed base address.
5. If the observation answers the question, express the resulting source-quality fact through the normal framework command path and exact round-trip verification.

The current intended machine profile is A500/Kickstart 1.3 with 512 KiB chip RAM and 512 KiB slow RAM, OCS/68000-compatible behavior, and accelerated floppy reads. Keep profile changes explicit and justified by the target.

## Breakpoint workflow

Use canonical stable source keys such as `s0:00000BA8:instruction:755`, never a hand-derived runtime address in the public interface.

1. Boot normally and allow the target payload to become uniquely observable.
2. Pause in the confirmed target state.
3. Arm a bounded stable-key breakpoint through `amiga_reversing.tools.winuae_session`.
4. Continue only for the configured wait period; consume `hit` or `not_hit` plus PC, SP, stop reason, and stack return address.
5. Use the stack return address to inspect static predecessors and justify labels or reachability facts.

Do not set target code breakpoints from reset: WinUAE checks them while executing Kickstart and this is prohibitively slow. The supported pattern is boot, confirm, pause, arm, continue.

## Canonical GDB symbols

Use generated symbols when a bounded scenario must resolve or enter a reconstructed function. Generate the disposable artifact through the public scenario path; never accept a user-managed symbol file or raw GDB symbol command.

- Derive each function only from a canonical accepted named label whose entry exactly matches an accepted code run. Omit missing, duplicate, or unsupported ranges.
- Generate an M68K ELF/DWARF artifact into the isolated session state directory. It must contain no target bytes and must not alter exported source.
- Load it only after a scenario phase uniquely confirms the payload runtime base. Map source offsets through that confirmed observation view.
- Use `enter_function` for an adjacent call that must enter a named callee. It is a symbolic GDB breakpoint transition, not an instruction-step fallback; do not invent a caller name merely to make native GDB stepping work.
- Include the resolved function and accepted source range in phase results when the hit lies in an emitted function.

For symbol-path changes, test accepted emission and ambiguous omission, non-default runtime-base planning, public-session loading, a real strictly headless scenario, and exact target round trip.

## Improve the harness only when needed

Make a runtime-tool change only for a concrete reversing blocker: a missing observation, a reproducible protocol failure, an unsafe headless behavior, or a required verification contract.

For a change in `resources/clone_amiga/WinUAE/`:

1. Preserve unrelated clone changes; work on `codex/local-workspace-build`.
2. Build `od-win32/winuae_msvc15/winuae_msvc.vcxproj` as `FullRelease|x64` with the installed Visual Studio MSBuild.
3. Ensure the post-build artifact updates `ext/tools/winuae/windows-x64/winuae-gdb.exe` deliberately; committed binaries are a permanent Windows resource, not an ignored post-step.
4. Commit fork-source changes in the clone separately from repository harness changes when appropriate.

For every harness change, run:

1. `uv run pytest tests/test_winuae_session.py -q`
2. Python/PowerShell syntax checks for touched scripts.
3. A real strictly headless target smoke session.
4. A bounded target-aware breakpoint probe when breakpoint behavior changed.

Do not add GUI fallbacks, hidden interactive prompts, raw agent GDB consoles, or untracked dependency locations.

## Direct-payload contracts

When static and runtime evidence prove that a decoded payload can be entered
without reproducing its original loader, create a generic direct-payload
contract instead of a target-specific launcher. Contracts live in
`runtime/direct_payload_contracts/`; the shared builder is
`amiga_reversing.tools.direct_payload_adapter`.

Each contract must declare the target id, decoded-payload SHA-256, load
address, entrypoint, and a four-byte handoff marker. Build and launch it only
through the public session interface:

```text
python -m amiga_reversing.tools.winuae_session --target <target> --rom <legal-rom> \
  --direct-payload-contract <contract> --state-directory <isolated-run-dir> --run
```

This selection creates a disposable raw boot ADF, embeds the validated target
payload, and stops at the declared marker. It has no fallback to original
media. Do not create a contract from decompression metadata alone: prove the
load/entry contract, cold-boot marker, and byte-identified payload execution.
Keep a contract only when it provides a required observation or improves the
measured original-media path; otherwise retain the evidence in Proposal 036
and do not keep an adapter.

## Interpret outcomes

- `pc_matched`: useful runtime/source observation; still not a loader claim.
- `breakpoint.status = hit`: combine the PC and stack return address with static xrefs before creating a source fact.
- `breakpoint.status = timeout` or `not_hit`: negative evidence only for that bounded, observed execution window.
- crash/minidump: preserve the diagnostic path, reproduce with the same headless command, and inspect the harness/fork before attributing the fault to target code.

Consult Proposal 036 for environment recreation details and historical failure modes. Update that proposal when a material harness decision, dependency requirement, or reproducible limitation changes.
