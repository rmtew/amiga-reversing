Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md

Scope:
Establish the post-016 Pandora baseline and produce a small, evidence-ranked
candidate queue before any new target mutation.

Problem:
Pandora should not restart as an open-ended loop. The next pass needs a clear
baseline, current hygiene state, available reports, Review Items, and command
availability before choosing a candidate family.

Required work:
- Run read-only hygiene and listing/report inspection for the Pandora
  sub-target.
- Collect current Review Items, selected-action traceability output,
  `immediate-ref-report`, and `a5-hardware-report`.
- Rank candidate families by visible source-quality value, evidence strength,
  command availability, verifier availability, and expected round-trip safety.
- Record blockers and deferred findings in proposal 017.
- Do not mutate target state in this slice.

Acceptance:
- Proposal 017 has a baseline entry naming the selected next candidate family.
- The report distinguishes actionable candidates from report-only guidance.
- A5 hardware candidates are explicitly marked non-durable unless path/lifetime
  evidence exists outside `a5-hardware-report`.
- No target Manual Action Log or rendered source mutation is required.

Blocked by:
None - can start immediately.
