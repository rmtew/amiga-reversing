Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

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
- Do not mutate target state while establishing the baseline.
- After the baseline, proceed directly into the best safe mutation if durable
  evidence, command support, verifier support, and exact round-trip gates are
  present; stop for human review only when the top candidate is ambiguous,
  report-only, or needs new policy/tooling.

Acceptance:
- Proposal 017 has a baseline entry naming the selected next candidate family.
- The report distinguishes actionable candidates from report-only guidance.
- A5 hardware candidates are explicitly marked non-durable unless path/lifetime
  evidence exists outside `a5-hardware-report`.
- Baseline collection itself does not mutate the target.

Blocked by:
None - can start immediately.

Implementation notes:
- Read-only hygiene and inspect were clean for the Pandora sub-target:
  review state clear, no Review Items, project available, and round-trip exact.
- `immediate-ref-report` produced concrete reference candidates, but they remain
  report-only because verifier-backed immediate reference interpretation is not
  available for planner writes yet.
- `a5-hardware-report` produced probable custom-base candidates only. They are
  non-durable listing-state evidence and cannot be used for hardware rendering
  until `017-003` proves accepted path/lifetime scope.
- Selected next candidate family: `017-002` immediate runtime-reference triage.
- Baseline collection did not intentionally mutate target state; timestamp-only
  target metadata churn remains outside this issue.

Verification:
- `reversing_loop hygiene --target ...`
- `reversing_loop inspect --target ...`
- `reversing_loop immediate-ref-report --target ...`
- `reversing_loop a5-hardware-report --target ...`
- `reversing_loop run-one --target ... --dry-run`
