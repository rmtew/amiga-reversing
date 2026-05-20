Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-009 report-only RSSET candidates

Scope:
Turn the RSSET candidate report for remaining raw A6 operands into accepted
app-base evidence where safe.

Problem:
017 added `rsset-candidate-report` and found 125 grouped A6 displacement
candidates, with top group `rsset-raw-a6:022E`, but all remain report-only
because accepted app-base/source evidence is missing. Existing RSSET command
and verifier plumbing cannot safely bind or refine fields without that base
evidence.

Required work:
- Identify what evidence would prove the selected A6 app-base lifetime/scope
  for a raw A6 candidate group.
- Add or use a report that exposes accepted base evidence, source family,
  path/lifetime scope, conflicts, and ownership/cleanup requirements.
- Allow RSSET bind/refine only when the accepted evidence is present and the
  command/verifier can consume it.
- Keep adjacency-only or generic app-slot names blocked.

Acceptance:
- At least one raw A6 candidate group is either promoted through accepted
  RSSET/app-base evidence or documented with the exact missing proof.
- `rsset.binding.*` or `target.rsset_region.*` actions do not execute from
  report-only same-displacement evidence.
- Exact round-trip passes for any output-affecting RSSET mutation.

Blocked by:
- 017-009.
