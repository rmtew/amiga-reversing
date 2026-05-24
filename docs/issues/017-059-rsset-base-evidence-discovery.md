# 017-059: RSSET Accepted-Base Evidence Discovery

Status: active
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

- [ ] Current RSSET candidate report rerun for Pandora.
- [ ] Selected candidate or family justified.
- [ ] Selected-use identity checked.
- [ ] Accepted-base evidence count and source checked.
- [ ] Possible base setup/path/lifetime evidence checked.
- [ ] Conflict state checked, including explicit empty-conflict requirement.
- [ ] Existing already-recorded RSSET candidates compared to avoid duplicate work.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed RSSET mutation remains blocked without accepted base evidence.
- [ ] Confirmed no command candidate was exposed.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] One candidate or small family selected.
- [ ] Accepted-base evidence path or exact blocker recorded.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete packet/report correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
