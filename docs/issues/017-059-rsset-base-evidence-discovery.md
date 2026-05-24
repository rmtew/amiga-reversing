# 017-059: RSSET Accepted-Base Evidence Discovery

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: RSSET/app-base accepted evidence.
- Current proposal state: RSSET discovery reports 123 missing-base-evidence candidates and 2 already-recorded candidates. The historical top candidate is `rsset-raw-a6:022E` at `s0:000006E4`, blocked by missing accepted base evidence.
- Desired proposal state after this issue: one RSSET candidate or small family has a current accepted-base evidence path or an exact blocker explaining why the path cannot yet be proven.

## Protocol Delta

- Adds: a read-only accepted-base evidence discovery packet for one RSSET candidate or small related family.
- Changes: proposal living notes with selected candidate, selected-use identity, base-evidence status, conflicts, and next safe issue if any.
- Replaces: no existing protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: RSSET mutation remains disabled without accepted selected-use base evidence, explicit `conflicts: []`, verifier support, and exact round-trip.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: no new RSSET bind/mutation command may be exposed by this issue.

## Pandora Proof

- Target candidate: `rsset-raw-a6:022E` at `s0:000006E4`, unless current RSSET reports show a stronger candidate family.
- Evidence packet expected: selected use, displacement, candidate group, current report state, accepted-base evidence count, possible base setup, path/lifetime scope, selected-use identity, conflicts, existing already-recorded comparison, blocker, and render/verifier readiness.
- Decision behavior: no accept decision; record only evidence path or blocker.
- Command gate behavior: `rsset.binding.bind` remains blocked unless a later issue adds accepted base evidence and gates.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless a read-only base-evidence query is demonstrably missing required blocker information.
- Python/API/report work: inspect `rsset-candidate-report`, Decision Journal audit state, and current verifier artifact consumption as read-only evidence.
- Journal/replay work: inspect existing accepted/deferred records; do not append.
- Renderer/verifier work: none.
- Tests: focused report/audit tests if output shape changes; otherwise document current report outputs.

## Research Coverage

- [x] Current RSSET candidate report rerun for Pandora.
- [x] Selected candidate or family justified.
- [x] Selected-use identity checked.
- [x] Accepted-base evidence count and source checked.
- [x] Possible base setup/path/lifetime evidence checked.
- [x] Conflict state checked, including explicit empty-conflict requirement.
- [x] Existing already-recorded RSSET candidates compared to avoid duplicate work.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed RSSET mutation remains blocked without accepted base evidence.
- [x] Confirmed no command candidate was exposed.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] One candidate or small family selected.
- [x] Accepted-base evidence path or exact blocker recorded.
- [x] Output remains read-only.
- [x] Any support-code change is tied to a concrete packet/report correctness blocker.
- [x] Focused tests pass if code changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only commands rerun:

- `uv run python -m amiga_reversing.reversing_loop rsset-candidate-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- `uv run python -m amiga_reversing.reversing_loop decision-journal-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Current RSSET report summary:

- 125 candidates.
- Status counts: 123 `blocked`, 2 `already_recorded`.
- No new RSSET command candidate was exposed.
- Unrecorded candidates remain blocked by missing accepted base evidence.

Selected candidate:

- Candidate: `rsset-raw-a6:022E`.
- Selected use: `s0:000006E4:op1`, hunk 0, addr 1764,
  operand index 1.
- Row text: `bclr.b #1,app_022E(a6)`.
- Displacement: `$022E` / 558.
- Same-displacement use count: 66.
- Current candidate status: `already_recorded`.

Accepted-base evidence path:

- `accepted_base_evidence_count=1`.
- Evidence source:
  `decision-rsset-022e-accept-017-040`.
- Source family/status: `rsset_app_base` / `accepted`.
- Base evidence id: `selected-base:A6:__amiga_app_base__`.
- Scope: selected-use path/lifetime, hunk 0, addr 1764,
  operand index 1.
- Conflict state: explicit empty `conflicts: []`.
- Existing manual binding owner:
  `manual-6e574feccab748359c7577833fa718ba`.

Readiness/current blocker state:

- `rsset.binding.report` remains available.
- `rsset.binding.bind` for `022E` is `already_satisfied`; this issue must not
  create a duplicate mutation.
- The journal mutation gate reports `ready_for_039=true` but
  `mutation_enabled=false`, matching the read-only policy.
- `decision-journal-report` shows the accepted RSSET decision is active and
  source-effective through current semantic reload/report matching.
- Current verifier artifact consumption reports generated-source,
  negative-safety, and exact-round-trip layers as `not_checked` because the
  local artifact is stale; no artifact was regenerated or written here.

Conclusion:

- The historical issue premise is stale for `rsset-raw-a6:022E`: accepted-base
  evidence is now present and already recorded from earlier 017 work.
- The useful current blocker is for new/unrecorded RSSET candidates: without
  accepted selected-use base evidence, explicit empty conflicts, and verifier
  readiness, mutation remains blocked.
- No RSSET mutation or duplicate command candidate was exposed.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
