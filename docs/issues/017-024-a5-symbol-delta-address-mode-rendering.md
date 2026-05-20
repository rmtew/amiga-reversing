Status: deferred
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
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

Acceptance:
- The renderer can show the accepted hardware-register semantic without
  changing instruction length or bytes.
- The verifier rejects any render that changes the address mode or fails exact
  round-trip.
- Previously blocked A5 symbol-delta candidates either become safe mutations or
  remain explicitly blocked with a narrower reason.

Blocked by:
- 017-015.
- 017-019.

Resolution:
- Rerun `a5-hardware-report` still finds one accepted A5 use blocked by
  `zero_displacement_a5_operand_requires_address_mode_preserving_rendering`.
- No source-changing mutation was taken. A zero-displacement `(a5)` operand
  cannot be replaced with a symbolic displacement form without changing the
  encoded 68000 address mode; exact symbolic source would need new
  address-mode-preserving annotation/render support, not an operand rewrite.
- Existing command/verifier gates remain blocked for this family, so the
  accepted semantic evidence stays local/manual and non-rendered.
