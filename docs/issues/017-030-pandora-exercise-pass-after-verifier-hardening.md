Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: review request after 017-024/017-025 closeout

Scope:
Use the real Pandora sub-target for a demonstrable editing pass over the
related source-converging surfaces after the 017 verifier hardening, not only
unit tests and compact gate summaries.

Problem:
017-024 and 017-025 changed important source-converging surfaces, then 017 was
closed from report summaries. Before final closeout, the agent should exercise
the related Pandora editing workflow enough to prove the loop helps or
correctly blocks real target work. This is broader than testing only the new
verifier changes.

Required work:
- Reproduce the current Pandora target state without committing timestamp-only
  `.project.json` churn.
- Exercise the related editing features used by this proposal on the real
  target: review/action discovery, immediate-reference report policy, A5
  hardware-ref editing/projection, RSSET report/bind blocking, command catalog
  availability, already-satisfied detection, verifier layers, and source
  evidence capture.
- Exercise the A5 entry-comment path as one case, recording the exact source
  location, generated-source evidence, and round-trip result.
- Exercise RSSET evidence search as one case, starting with
  `rsset-raw-a6:022E`; inspect flow/xrefs/source context enough to either find
  accepted base evidence or document the exact missing proof.
- Pick at least one additional concrete Pandora candidate or editing surface
  from inspect/reports/review context, even if the result is a justified block,
  so the pass is not limited to the two review findings.
- Use query/report APIs first. Render or inspect the full `.s` only where it
  answers a concrete evidence question or provides final review evidence.
- If a command-backed, verifier-backed, exact-round-trip mutation appears,
  execute it and verify it. If not, record why each inspected family remains
  blocked.
- Update proposal 017 and validation evidence with the inspected locations,
  report counts, timings if slow, and visible source/result summary.

Acceptance:
- The pass includes concrete Pandora locations inspected, not only aggregate
  counts.
- A5 entry-comment generated-source behavior is proven on Pandora after
  `017-028`.
- RSSET top active group evidence search is demonstrated beyond report-only
  summary after `017-029`.
- At least one other related editing surface is exercised and recorded with a
  concrete Pandora location/result.
- Any output-affecting change has exact round-trip verification.
- Final 017 closeout is deferred to `017-027` after this issue is complete.

Resolution:
- Added `docs/validation/pandora-017-exercise-2026-05-22.md` as the tracked
  evidence boundary for the real-target exercise pass.
- Reproduced current Pandora state with exact round-trip available, no inspect
  candidate work, and dry-run planner status `no_candidate`.
- Verified the real Pandora A5 entry-comment action
  `manual-964aee63919e438880d1f5e7670ef95d` at `s0:0000045C` through
  manual-log, semantic-reload, generated-source, and round-trip layers.
- Inspected RSSET `rsset-raw-a6:022E` at `s0:000006E4`; source context and
  manual state show no accepted `$022E` app-base evidence, so bind remains
  blocked by `missing_accepted_base_evidence`.
- Exercised the immediate-reference surface at `s0:000009A6`; the remaining
  source-offset candidates remain report-only with no command/verifier path.

Verification:
- `inspect_target(...)`
- `run_one_iteration(..., dry_run=True)`
- `inspect_a5_hardware_lifetimes(...)`
- `_verify_a5_hardware_ref_mutation(...)` for
  `manual-964aee63919e438880d1f5e7670ef95d`
- `inspect_rsset_candidates(...)`
- `inspect_immediate_runtime_refs(...)`
