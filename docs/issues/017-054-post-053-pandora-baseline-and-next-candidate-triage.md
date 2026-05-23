# 017-054: Post-053 Pandora Baseline and Next-Candidate Triage

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: post-repair target readiness, verifier continuity, and next
  evidence-review candidate selection.
- Blocked by: none.
- Current proposal state: `017-053` repaired the exact Pandora Manual Action Log
  final-record skipped sequence and made mutation readiness block while an open
  Manual Action Log sequence inconsistency exists.
- Desired proposal state after this issue: Pandora has a fresh post-repair
  baseline proving the target is clean, verifier-backed, exact-round-trip, and
  either has a specific safe next 017 candidate or an explicit no-useful-017-work
  conclusion that justifies pausing 017 before resuming 012.

## Protocol Delta

- Adds: a required post-repair baseline and triage step after target-local manual
  state repair.
- Changes: further Pandora mutation work must be selected from current durable
  evidence packets, Decision Journal/verifier state, and exact round-trip gates,
  not from stale pre-repair candidate assumptions.
- Replaces: assuming `017-053` completion itself proves the next mutation is
  available.
- Deletes: none.
- Leaves out of scope: broad Pandora mutation runs, cosmetic label cleanup,
  historical tracked `.s` refresh, and 012 work unless this issue concludes 017
  has no useful unblocked work.

## Default Behavior

- Default commands remain read-only unless this issue identifies a separately
  issue-scoped safe mutation with durable accepted evidence and explicit write
  gates.
- The post-repair baseline must not rewrite source, Decision Journal, verifier
  artifacts, generated output, or target metadata as part of measurement.
- If command execution discovers local generated-output drift, report it as a
  blocker or follow-up rather than silently refreshing historical artifacts.

## Required Baseline Actions

- Reproduce current Pandora `inspect` state and record:
  - `candidate_work`
  - `mutation_readiness`
  - `review_state`
  - target hygiene unknown files
  - round-trip status
- Rerun the RSSET no-write verifier artifact producer for
  `decision-rsset-022e-accept-017-040`.
- Rerun `decision-journal-report` and confirm the RSSET audit still passes every
  current verifier layer or records exact blockers.
- Requery the current read-only packet surfaces:
  - source-offset immediate packet from `017-046`
  - A5 path/lifetime packet from `017-047`
  - orphan/data-range packet from `017-048`
- Confirm `repair-manual-action-log-sequence` now blocks/no-ops because there is
  no open final-record sequence inconsistency.
- Confirm no source, Decision Journal, Manual Action Log, verifier artifact,
  generated-output, or metadata diff is produced by the baseline commands.

## Required Triage Actions

- Identify the best next 017 candidate only if all of these are true:
  - current evidence is durable and source-quality
  - command/API support exists or can be cleanly added in one issue
  - verifier support exists or can be cleanly added in one issue
  - exact round-trip remains available
  - mutation would visibly improve Pandora source quality
- If a candidate is report-only, ambiguous, cosmetic, blocked by missing render
  support, or dependent on stale tracked `.s` state, record the blocker and do
  not mutate it.
- If no useful 017 candidate remains, update the proposal with that conclusion
  and recommend pausing 017 so 012 can resume.
- If a useful candidate remains, create or update the next issue with exact
  evidence, command gates, verifier gates, and expected visible source
  improvement.

## Research Coverage

- [x] Current Pandora inspect state captured after 017-053.
- [x] RSSET no-write verifier producer rerun.
- [x] Decision Journal audit rerun.
- [x] Source-offset immediate packet rerun.
- [x] A5 path/lifetime packet rerun.
- [x] Orphan/data-range packet rerun.
- [x] Manual log repair command post-repair blocked/no-op state checked.
- [x] No unintended file diffs checked.
- [x] Next-candidate decision recorded.

## Research Review

- [x] Second pass checked the baseline against `017-053` completion evidence.
- [x] Stale tracked `.s` and historical artifact assumptions reviewed.
- [x] Candidate selection checked against durable evidence and verifier gates.
- [x] Proposal updated with baseline result and next-step conclusion.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Baseline commands and outputs summarized.
- [x] Any generated/local file changes explained or reverted.
- [x] Next mutation candidate either defined in a follow-up issue or explicitly
  rejected/deferred.
- [x] 017 pause/resume recommendation recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only `inspect` after `017-053` reported:

- `safe_to_mutate=true`.
- `candidate_work=[]`.
- `mutation_readiness.safe_to_mutate=true`, `blockers=[]`.
- target hygiene unknown files: `[]`.

`decision-verifier-artifact --decision-id
decision-rsset-022e-accept-017-040` was rerun without `--write` and returned
`status=passed`, `written=false`. Current verifier results passed:

- `semantic_reload`.
- `generated_source`.
- `negative_safety`.
- `exact_round_trip`, with `round_trip.status=exact`.

`decision-journal-report --current-verifier-artifact
decision-rsset-022e-accept-017-040` consumes that fresh verifier proof in
memory and does not write `decision_verifier_artifacts.json`. The RSSET audit
reported `blockers=[]`, `replay.status=source_effective`, and passed
`decision_journal`, `semantic_reload`, `generated_source`, `negative_safety`,
and `exact_round_trip`.

Read-only packet requery results:

- `source-offset-immediate-packet` for
  `immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080`:
  `safe_to_mutate=false`, `mutation_policy=read_only`,
  `decision_lane.status=deferred`, command gate disabled. Blockers remain
  same-literal/non-durable provenance plus missing accepted runtime-address,
  decision replay, and render/verifier gates.
- `a5-path-lifetime-packet` for `s0:0000045C:op0`:
  `safe_to_mutate=false`, `mutation_policy=read_only`,
  `decision_lane.status=deferred`, command gate disabled. Blockers remain
  `already_recorded_in_manual_state` and `missing_command_candidate`.
- `orphan-code-island-packet` for
  `data-class-symbol:s0:000010F3:data:1111:0:000010F3:string_000210F3`:
  `safe_to_mutate=false`, `mutation_policy=read_only`,
  `decision_lane.status=deferred`. `data_symbol.rename` remains blocked by
  `missing_direct_xref_evidence` and `missing_exact_round_trip_gate`.

`repair-manual-action-log-sequence` now no-ops/blocks post-repair:
`status=blocked`, `written=false`, `inconsistency_count=0`, no `proposed_edit`.
This confirms there is no remaining final-record sequence inconsistency to
repair.

`git diff --name-only -- targets docs/validation
docs/proposals/017-evidence-driven-analysis-protocol.md` was empty before this
issue/proposal documentation update, proving the baseline commands did not
rewrite target source, Decision Journal, Manual Action Log, verifier artifacts,
generated output, or metadata.

Triage conclusion: no useful unblocked 017 mutation remains. The current
candidate list is empty, the three known packet lanes are explicitly
deferred/read-only or blocked, and the only active accepted RSSET decision is
already source-effective and verifier-backed. Pause 017 and resume 012 rather
than forcing a cosmetic or stale-artifact-dependent Pandora mutation.
