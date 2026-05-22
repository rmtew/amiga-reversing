Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: post-017-019 Pandora report review

Scope:
Make candidate-level `immediate-ref-report` write policy match the report's
actual mutation gate.

Problem:
After the command-backed Pandora immediate-reference candidate was promoted,
the remaining candidates were source-offset or otherwise report-only matches.
The top-level mutation gate correctly reported `safe_to_mutate=false`, but each
candidate still advertised `write_policy.status=supported` with command and
verifier support available. Consumers could over-read those candidate payloads
as durable, command-backed evidence.

Required work:
- Keep source-offset immediate matches report-only at the candidate level.
- Keep width-mismatch and conflicting matches report-only at the candidate
  level.
- Only advertise command/verifier support on candidates that actually carry an
  `immediate_ref.interpret` command payload.
- Re-run the Pandora report that exposed the inconsistency.

Acceptance:
- Runtime-address candidates with command payloads keep reporting supported
  write policy.
- Source-offset-only candidates expose blocked/report-only candidate policy.
- Width-mismatch and conflicting candidates do not advertise command support.
- Pandora `immediate-ref-report` has zero command-backed candidates and no
  report-only candidate claims available write support.

Result:
- Candidate-level write policy now defaults to report-only and is upgraded to
  supported only when the command payload is present.
- Regression tests cover source-offset, width-mismatch, and conflicting
  immediate-reference candidates.
