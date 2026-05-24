# 017-057: Source-Offset Immediate Provenance Unblocker

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: source-offset immediate provenance.
- Current proposal state: 9 source-offset-looking immediate candidates remain report-only; `s0:000009A6:op0` is durably deferred by the Decision Journal lane added in the historical 017 sequence.
- Desired proposal state after this issue: one exact source-offset immediate is re-evaluated from current evidence, and the missing proof for promotion is explicit.

## Protocol Delta

- Adds: a current read-only provenance packet review for one exact source-offset immediate, preferably `s0:000009A6:op0`.
- Changes: proposal living notes with whether the blocker is policy, missing runtime-address provenance, missing dataflow, width/signedness ambiguity, landing-range ambiguity, or verifier/render support.
- Replaces: no existing protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: source-offset immediate packets remain read-only unless a later issue proves accepted evidence and adds gates.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: current report-only behavior must remain unless a separate mutation issue is created later.

## Pandora Proof

- Target candidate: `s0:000009A6:op0` / `addi.w #4224,d1`, unless current reports show a stronger exact candidate.
- Evidence packet expected: selected operand identity, literal value, width, signedness, possible source-offset interpretation, landing range, dataflow use, conflicts, current Decision Journal lane, blockers, and render/verifier readiness.
- Decision behavior: no accept decision in this issue; update only blocker/defer explanation.
- Command gate behavior: `immediate_ref.interpret` must remain disabled for same-literal/source-offset-only evidence.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless current row/dataflow lookup is demonstrably incomplete for this packet.
- Python/API/report work: inspect existing `source-offset-immediate-packet` and immediate-reference report output; add only read-only blocker detail if needed.
- Journal/replay work: inspect existing deferred lane; do not append.
- Renderer/verifier work: none.
- Tests: focused packet/report tests if output shape changes; otherwise document the current evidence.

## Research Coverage

- [ ] Current immediate-reference report rerun for Pandora.
- [ ] Current `source-offset-immediate-packet` inspected for the selected candidate.
- [ ] Current Decision Journal lane checked without appending.
- [ ] Landing/dataflow evidence checked.
- [ ] Conflict state checked.
- [ ] Render/verifier readiness checked as read-only.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed source-offset-only evidence remains non-accepting unless stronger provenance exists.
- [ ] Confirmed command gate remains disabled.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] One exact operand selected.
- [ ] Blockers/conflicts recorded explicitly.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete packet/report correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
