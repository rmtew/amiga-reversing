Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-014 focused Pandora mutation

Scope:
Block unsafe projected rendering for durable A5 hardware refs whose symbolic
operand would not preserve the encoded A5 displacement.

Problem:
After 017-014, Pandora `s0:0000045C` produced accepted durable state for
`dmaconr`, but verification failed rendered-source projection: the C renderer
kept `move.w (a5),d0` instead of applying the operand-level symbolic
representation. A first implementation attempt proved that forcing
`move.w dmaconr(a5),d0` changes the 68k addressing mode and breaks exact
round-trip because A5 already points at `_custom+dmaconr`.

Required work:
- Keep accepted A5 state durable, but do not project symbolic operand text when
  the source operand has zero displacement.
- Do not advertise output-affecting `a5_hardware_ref.interpret` candidates when
  the rendered symbol would require custom-base delta expression support.
- Preserve exact round-trip.
- Add focused regressions proving unsafe A5 refs remain semantic-only.

Acceptance:
- Durable A5 hardware refs with zero displacement or non-zero custom-base
  offsets do not create manual symbolic operand representations.
- The A5 rendered-source verifier reports those refs as blocked, not passed.
- Render-safe A5 refs with normal non-zero displacement remain command-backed.

Result:
- Zero-displacement and non-zero custom-base-offset A5 refs are now
  semantic-only until an exact address-mode-preserving render expression exists.
- The Pandora `s0:0000045C` candidate remains durable evidence but is blocked
  from rendered-source mutation; the next safe mutation must use an A5 ref whose
  source displacement can be rendered exactly.
- Focused Pandora validation now reports `s0:0000045C` with
  `zero_displacement_a5_operand_requires_address_mode_preserving_rendering` and
  keeps `s0:000004A6` as command-backed `dmacon`.
