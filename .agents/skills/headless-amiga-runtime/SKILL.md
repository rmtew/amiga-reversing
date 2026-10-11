---
name: headless-amiga-runtime
description: Operate and diagnose the strictly headless Copperline runtime through canonical target-aware observations and bounded scenarios.
---

# Headless Amiga Runtime

Use runtime evidence to resolve a concrete reversing ambiguity. Static analysis
and the normal reversing loop remain the source of reconstructed source facts.
Read `docs/agents/reversing-loop.md` before target interpretation work.

## Constraints

- Use `amiga_reversing.tools.copperline_session`; never launch a visible emulator
  or expose arbitrary control commands to an agent.
- Supply a legal Kickstart ROM by explicit path; never add ROMs to the repository.
- Keep A500OCS, PAL, 68000, 512 KiB chip + 512 KiB slow RAM explicit.
- Require payload-byte identity and canonical source-offset agreement before
  treating a runtime PC as target evidence. A configured address alone is not proof.
- Runtime mappings remain observations, not proof of a loader or static edge.
- Record useful discoveries through normal manual actions, then render and
  exact-round-trip verify. Never directly edit exported `.s` files.

## Implementation

- `amiga_reversing/tools/copperline_control.py`: pinned Copperline 1.0.0 native
  JSON-RPC, authenticated ephemeral loopback endpoint, owned process lifecycle.
- `amiga_reversing/tools/copperline_runtime.py`: bounded observations, marker
  verification, scenario execution, capture and joystick state cleanup.
- `amiga_reversing/tools/copperline_session.py`: restricted target-aware CLI,
  canonical stable keys and declarative scenario validation.
- `amiga_reversing/tools/runtime_symbols.py`: disposable JSON metadata from
  canonical accepted contiguous named function facts, without target bytes.
- `docs/copperline-runtime.md`: installation provenance, reproduction and limits.

The old patched WinUAE, PowerShell and GDB transport is retired. Proposal 036
records historical evidence only; do not revive it as a second runtime backend.

## Bounded workflow

1. Inspect static labels, xrefs and candidate source offsets first.
2. Invoke the public CLI with a target, ROM, explicit Copperline executable and
   original media or a validated direct-payload contract.
3. Use canonical stable keys for breakpoints. Confirm payload identity and
   mapping; reject unexpected stops, stale views and ambiguous byte samples.
4. Consume status, PC, SP and stack return address. Negative results apply only
   to the observed time window. Input holds are bounded by named phases and
   released on completion or failure.
5. For `enter_function`, require an accepted exact function entry, unique name
   and contiguous owned range. Do not approximate disjoint or ambiguous facts.

Direct contracts in `runtime/direct_payload_contracts/` declare target identity,
SHA256, load address, entrypoint/registers and a four-byte handoff marker. The
shared builder creates an isolated boot ADF; the runtime verifies loaded bytes
before releasing the marker. The debugger memory write is followed by a new
reverse-history anchor; replay across that injected write is not evidence.

```sh
python -m amiga_reversing.tools.copperline_session \
  --target <target-id> --rom <legal-rom> --copperline <binary> \
  --direct-payload-contract <contract> --state-directory <isolated-run-dir> \
  --scenario <scenario.json> --continue-seconds 60 --run
```

## Verification

Run focused control/session/runtime/symbol tests, real strictly headless target
scenarios for changed behaviors, and exact target round trip when source output
is affected. Keep logs bounded and record unavailable inputs precisely. Transport
synthetic tests alone do not establish original-loader or gameplay parity.
