# 017-089: Prove Pandora A5 End-To-End Source Progress

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-088` must be complete first.
- Protocol area: proving the A5 implementation path improves real target source output.
- Current proposal state: A5 support has been implemented only in pieces after `017-085` through `017-088`.
- Desired proposal state after this issue: one real Pandora A5 hardware-reference candidate is carried through candidate generation, decision replay, rendering, verifier artifact, and exact round-trip.

## Protocol Delta

- Adds: real-target tracer-bullet proof for the A5 lane.
- Changes: Proposal 017 progress is measured by source output improvement, not by report availability alone.
- Replaces: report-only A5 closure.
- Leaves out of scope: bulk accepting A5 candidates, speculative unknown-use promotion, unrelated target cleanup, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Use one clearly accepted A5 command candidate from the real Pandora target.
- Do not bulk mutate all A5 candidates.
- If the first candidate fails verification, record the blocker and choose another only if the failure is candidate-specific rather than framework-wide.
- Commit only code/docs and any project-conventional tracked artifacts explicitly required by the verifier; do not commit timestamp-only target churn.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Required path: A5 report candidate -> Decision Journal accepted fact -> effective metadata replay -> normal source render -> verifier artifact -> exact round-trip.
- Expected result: a narrow, reviewable source improvement for one A5 hardware-reference use, with all safety gates passing.

## Implementation Slice

- C fact graph/query work: only fix gaps discovered by the real end-to-end path.
- Python/API/report work: ensure the real report links candidate, decision, render state, and verifier result.
- Journal/replay work: accept only the selected tracer-bullet fact if all gates pass.
- Renderer/verifier work: prove the rendered output effect and exact round-trip.
- Tests: focused real-target or fixture regression for every bug fixed during the tracer bullet.

## Research Coverage

- [x] `017-085` through `017-088` completed and checked.
- [x] Selected real candidate recorded with stable identity and parent evidence.
- [x] Accepted fact replays into effective metadata.
- [x] Source render diff is narrow and meaningful.
- [x] Verifier artifact passes semantic reload, generated-source effect, negative safety, and exact round-trip.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This proves useful source progress, not just plumbing.
- [x] Any blocker is fixed in the framework if it is general, not worked around in Pandora.
- [x] Bulk acceptance is deferred until the tracer bullet proves safe.
- [x] Proposal 017 living notes updated with the implementation result and next lane recommendation.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-088` complete.
- [x] Real Pandora A5 end-to-end path demonstrated.
- [x] Focused regressions pass.
- [x] Exact round-trip passes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Real Pandora tracer bullet selected `a5-custom-cfg:h0:00000498->000004A6:op1:d0096` at `s0:000004A6:op1`, accepted as `decision-a5-dmacon-000004a6-accept-017-089`.
- `decision-verifier-artifact --write` passed all layers; generated source shows `move.w d0,dmacon(a5)`, negative safety found one same-decision A5 ref and no unexpected refs, and `reproduction.json` reports `status=exact`.
