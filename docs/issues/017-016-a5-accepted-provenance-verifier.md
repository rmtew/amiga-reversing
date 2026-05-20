Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-015 follow-up mutation

Scope:
Accept command-backed A5 `accepted` provenance in the generic provenance
verification wrapper.

Problem:
The next focused Pandora A5 mutation after 017-015 recorded
`s0:000004AA` as durable `intena(a5)` state and passed manual-log,
semantic-reload, rendered-source, and exact round-trip checks. The generic
provenance wrapper still failed because it did not include the A5 report's
`source_evidence_status=accepted` value in its accepted status set.

Required work:
- Treat `accepted` as accepted provenance for command-backed A5 path/lifetime
  evidence.
- Add a regression so `a5_hardware_ref.interpret` does not fail provenance
  verification after the action-specific verifier passes.

Acceptance:
- An A5 hardware-ref mutation with `source_evidence_status=accepted` passes the
  provenance wrapper when the durable payload matches the command evidence.
- Other provenance mismatch checks remain unchanged.

Result:
- The generic provenance verifier now accepts the A5 report's `accepted`
  status.
- Focused Pandora mutation `s0:000004AA` revalidated as action
  `manual-5f2c6ead224244dabec3cadaff7d2d98`, rendering
  `move.w d0,intena(a5)` with manual-log, provenance, semantic-reload,
  rendered-source, and exact round-trip layers all passed.
