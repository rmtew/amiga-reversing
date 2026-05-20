Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-011 follow-up

Scope:
Add a durable command/verifier path for A5 hardware-register references backed
by accepted path/lifetime evidence.

Problem:
017-008 can produce accepted straight-line A5 `_custom` evidence and 017-011
exposes the render gate, but no consumer could record that evidence as durable
manual state. Treating report output itself as durable hardware-base evidence
would bypass the accepted path/lifetime provenance boundary.

Required work:
- Add `a5_hardware_ref.interpret` command support only for accepted A5
  path/lifetime candidates.
- Store accepted A5 hardware refs in Manual Action Log projection state.
- Verify semantic reload, rendered symbolic operand state, and exact round-trip.
- Keep report-only/linear A5 candidates non-durable.

Acceptance:
- Accepted CFG A5 candidates advertise `a5_hardware_ref.interpret` and
  `a5_hardware_ref_state`.
- The command payload carries source family/status, source evidence id, and
  accepted path/lifetime scope.
- Tests prove durable A5 hardware state is required before the verifier passes.

Result:
- `a5-hardware-report` now attaches command-backed payloads to accepted
  `accepted_custom_base` uses and keeps exact round-trip as required for the
  output-affecting path.
- Manual Action Log projection now has `a5_hardware_refs`, projected to a
  symbolic operand representation only after the command records accepted
  path/lifetime evidence.
- The A5 verifier checks manual-log append, semantic reload from
  `a5_hardware_refs`, rendered `dmacon(a5)`-style operand state, and exact
  round-trip.
