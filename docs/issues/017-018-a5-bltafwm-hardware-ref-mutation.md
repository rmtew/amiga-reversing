Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-017 follow-up mutation

Scope:
Record the next render-safe Pandora A5 hardware reference from accepted
path/lifetime evidence.

Problem:
After the `intreq(a5)` mutation passed all verifier layers, the A5 report still
had unrecorded command-backed non-zero displacement candidates with durable
path/lifetime evidence and exact round-trip support.

Required work:
- Select the next unrecorded command-backed A5 candidate from
  `a5-hardware-report`.
- Execute only that focused mutation.
- Verify manual-log, provenance, semantic-reload, rendered-source, and exact
  round-trip layers.

Acceptance:
- `s0:000004C0` records durable A5 hardware-ref state from
  `a5-custom-cfg:h0:00000498->000004C0:op1:d0044`.
- The rendered source contains `move.w d0,bltafwm(a5)`.
- Exact round-trip remains passed.

Result:
- Action `manual-fa2c2e177ce645968850a0e8c3779158` recorded the Pandora
  `bltafwm(a5)` hardware reference.
- Verification passed manual-log, provenance, semantic-reload, rendered-source,
  and exact round-trip layers.
