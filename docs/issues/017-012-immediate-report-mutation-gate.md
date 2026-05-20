Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017 post-commit review

Scope:
Make `immediate-ref-report` expose mutation safety based on command-backed
candidates, not merely on clean target hygiene.

Problem:
After the 017-007 Pandora promotion, the remaining immediate-reference
candidates are accepted source-offset matches without `immediate_ref.interpret`
command payloads. The report still exposed top-level `safe_to_mutate=true`,
which could let consumers over-read report-only candidates as safe durable
mutations.

Required work:
- Keep source-offset immediate matches report-only.
- Expose command-backed and report-only candidate counts.
- Make top-level report mutation safety require a command-backed candidate.

Acceptance:
- Runtime-address candidates with command payloads keep reporting safe mutation
  availability.
- Source-offset-only reports expose `safe_to_mutate=false`.
- Tests prove accepted source-offset evidence is not enough for mutation.

Result:
- `immediate-ref-report` now includes a `mutation_gate` with
  `command_candidate_count`, `report_only_candidate_count`, and a blocked
  reason when only report-only candidates remain.
- Top-level `safe_to_mutate` now requires clean hygiene and at least one
  command-backed immediate-reference candidate.
