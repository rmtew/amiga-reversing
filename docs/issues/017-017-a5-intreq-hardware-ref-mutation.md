Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: 017-016 follow-up mutation

Scope:
Record the next render-safe Pandora A5 hardware reference from accepted
path/lifetime evidence.

Problem:
After 017-016, the A5 command/verifier path could fully accept
`source_evidence_status=accepted`. The next unrecorded command-backed Pandora
A5 candidate was `s0:000004AE`, a normal non-zero displacement use that should
render exactly as a custom register operand.

Required work:
- Select the next unrecorded command-backed A5 candidate from
  `a5-hardware-report`.
- Execute only that focused mutation.
- Verify manual-log, provenance, semantic-reload, rendered-source, and exact
  round-trip layers.

Acceptance:
- `s0:000004AE` records durable A5 hardware-ref state from
  `a5-custom-cfg:h0:00000498->000004AE:op1:d009C`.
- The rendered source contains `move.w d0,intreq(a5)`.
- Exact round-trip remains passed.

Result:
- Action `manual-c2202ab8723a407eb25ebccbfdf48476` recorded the Pandora
  `intreq(a5)` hardware reference.
- Verification passed manual-log, provenance, semantic-reload, rendered-source,
  and exact round-trip layers.
