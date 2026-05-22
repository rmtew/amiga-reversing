Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: 017-020 report-only immediate candidates

Scope:
Define whether and how source-offset immediate-reference candidates can become
safe interpreted references.

Problem:
After the runtime-address immediate at `s0:00006138` was promoted, remaining
`immediate-ref-report` candidates are source-offset or ambiguous byte-sized
matches. The report now correctly keeps them report-only, but the next rerun
needs a policy/verifier path if any source-offset immediate should be promoted.

Required work:
- Classify remaining immediate candidates by source family, width, context,
  operand role, and ambiguity with masks/counts.
- Define the evidence threshold for source-offset immediates, or state that
  they remain report-only for Pandora.
- If promotion is allowed, extend command payloads and verifier checks beyond
  the current runtime-address-backed path.
- Preserve report-only policy for ambiguous or width-mismatched constants.

Acceptance:
- Source-offset immediate candidates have an explicit promote/block policy.
- Any promoted source-offset immediate has command support, semantic reload or
  projection verification, and exact round-trip.
- Ambiguous address-shaped constants remain report-only with concrete reasons.

Blocked by:
- 017-020.

Resolution:
- Rerun `immediate-ref-report` reports 9 candidates, all `source_offset`, with
  `safe_to_mutate=false`, `command_candidate_count=0`, and
  `report_only_candidate_count=9`.
- Pandora policy remains: source-offset immediate matches are report-only until
  accepted runtime-address provenance exists. Width-mismatched or ambiguous
  constants also remain report-only.
- No immediate-reference command payload or verifier path is exposed for these
  candidates, so no mutation was performed.
