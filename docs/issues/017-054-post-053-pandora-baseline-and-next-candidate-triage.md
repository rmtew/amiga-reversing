# 017-054: Post-053 Pandora Baseline and Next-Candidate Triage

Status: active

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

- [ ] Current Pandora inspect state captured after 017-053.
- [ ] RSSET no-write verifier producer rerun.
- [ ] Decision Journal audit rerun.
- [ ] Source-offset immediate packet rerun.
- [ ] A5 path/lifetime packet rerun.
- [ ] Orphan/data-range packet rerun.
- [ ] Manual log repair command post-repair blocked/no-op state checked.
- [ ] No unintended file diffs checked.
- [ ] Next-candidate decision recorded.

## Research Review

- [ ] Second pass checked the baseline against `017-053` completion evidence.
- [ ] Stale tracked `.s` and historical artifact assumptions reviewed.
- [ ] Candidate selection checked against durable evidence and verifier gates.
- [ ] Proposal updated with baseline result and next-step conclusion.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Baseline commands and outputs summarized.
- [ ] Any generated/local file changes explained or reverted.
- [ ] Next mutation candidate either defined in a follow-up issue or explicitly
  rejected/deferred.
- [ ] 017 pause/resume recommendation recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
