Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md

Scope:
Upgrade A5 hardware-base work from non-durable listing-state candidates to
accepted path/lifetime evidence before any custom register rendering.

Problem:
`a5-hardware-report` is useful for candidate selection but deliberately
non-durable. Pandora has many A5-relative operands, and offset matching alone
is unsafe because A5 is also used for non-hardware pointers.

Required work:
- Pick a narrow A5 candidate family from the report and inspect definitions,
  uses, clobbers, save/restore boundaries, and control-flow lifetime.
- Define or use a report/query that can identify path/lifetime scope for the
  selected A5 base, including conflicts.
- Keep hardware register rendering blocked unless the selected lifetime has
  accepted evidence, command support, verifier support, and cleanup scope.
- If accepted evidence cannot be established, record the blocker and next
  required tooling in proposal 017.

Acceptance:
- The selected A5 use is classified as accepted hardware-base evidence,
  unknown, or conflicting for a concrete path/lifetime scope.
- No hardware register rendering executes from linear listing-state evidence.
- Any rendered hardware register name has an action-specific verifier and exact
  round-trip proof.

Blocked by:
- 017-001.
