Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: post-closeout review

Scope:
Rerun the current 017 reports and focused regression checks after any reopened
017 work, then close the proposal only when the gates agree.

Problem:
The focused 017 pass changed core reversing-loop support code and target-local
manual state. A rerun should not rely only on issue notes; it needs an explicit
gate that rechecks immediate refs, A5 refs, RSSET candidates, planner output,
and exact round-trip status.

Required work:
- Rerun the current 017 report surfaces after completing any reopened 017
  issue: `immediate-ref-report`, `a5-hardware-report`,
  `rsset-candidate-report`, `inspect`, and `run-one --dry-run`.
- Run focused tests for any touched support code, plus the strongest available
  end-to-end/precommit gate when the other active work permits it.
- Update proposal 017 with current counts, remaining blockers, and whether a
  safe source-converging mutation remains.
- Do not close 017 while a command-backed, verifier-backed Pandora candidate
  remains untried.

Acceptance:
- Proposal 017 has a fresh rerun summary with report counts and verifier/test
  results.
- Any remaining work is either represented by proposed issues or explicitly
  deferred as report-only/out-of-scope.
- No pure timestamp churn is committed.

Blocked by:
- Any reopened 017 implementation issue.
