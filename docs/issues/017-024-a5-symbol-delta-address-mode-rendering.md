Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: 017-015 and 017-019 blocked A5 refs

Scope:
Add exact address-mode-preserving rendering for A5 hardware refs whose accepted
evidence has zero displacement or a non-zero `_custom` base offset.

Problem:
017 correctly blocked refs such as the `s0:0000045C` `dmaconr` case because
A5 already points at `_custom+dmaconr`; naively rendering `(a5)` as
`dmaconr(a5)` changes the encoded address mode. Remaining blocked A5 refs are
semantic-only until the renderer can express the symbol/delta without changing
bytes.

Required work:
- Define the render form for zero-displacement and non-zero custom-base-offset
  A5 hardware refs that preserves exact encoding.
- Extend rendered-source projection and verifier checks for that form.
- Keep command/report gates blocked for these refs until exact render support
  exists.
- Validate on the known Pandora `s0:0000045C` style case if still present.
- If exact rendering cannot be implemented cleanly, document the precise
  renderer, assembler, or verifier limitation and leave a narrower issue-ready
  blocker. Do not treat the existing rerun report alone as resolution.

Acceptance:
- The renderer can show the accepted hardware-register semantic without
  changing instruction length or bytes.
- The verifier rejects any render that changes the address mode or fails exact
  round-trip.
- Previously blocked A5 symbol-delta candidates either become safe mutations or
  remain explicitly blocked with a narrower reason.

Depends on:
- 017-015 and 017-019 provide the blocked candidate context. They are not
  current blockers for this issue.

Resolution:
- Implemented address-mode-preserving A5 rendering as a generated entry comment
  for accepted hardware refs whose symbolic operand would change encoding.
- The existing Pandora `s0:0000045C` accepted ref now renders the semantic as
  `A5 hardware ref: dmaconr at _custom+$0002; operand kept as (a5)` while the
  instruction remains `move.w (a5),d0`.
- The verifier now accepts this render mode only when the generated source
  contains the entry comment and does not contain a symbolic A5 operand such as
  `dmaconr(a5)`.
- Normal render-safe A5 refs still use symbolic operand projection. The report
  marks address-mode-preserving cases as `render_mode=entry_comment`.
