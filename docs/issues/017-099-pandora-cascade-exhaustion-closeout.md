# 017-099: Rerun Pandora Cascade Exhaustion Closeout

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-098` must be complete first.
- Protocol area: final real-target cascade exhaustion proof.
- Current proposal state: superseded `017-096` delivered read-only `cascade-report`, but did not apply verified effects.
- Desired proposal state after this issue: Pandora cascade exhaustion either produces verifier-safe source progress or a precise fixed-point blocker report after verifier/apply paths are available.

## Protocol Delta

- Adds: final post-verifier/post-apply real Pandora cascade closeout.
- Changes: 017 closeout must be based on executable cascade exhaustion, not pending verifier state.
- Replaces: superseded read-only `017-096` closeout.
- Leaves out of scope: unsafe bulk acceptance, speculative facts, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Run the full cascade report to fixed point.
- Verify pending output-affecting effects with `017-097`.
- Apply only verifier-safe effects through `017-098`.
- Rerun cascade after any application and prove fixed-point stability.
- If no source progress is possible, report remaining blockers precisely and do not mark them as completed work.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Expected result: visible source-quality progress with exact round-trip, or a precise final blocker report explaining why the current evidence cannot safely progress.

## Implementation Slice

- C fact graph/query work: fix any general cascade-state gaps found by the real closeout run.
- Python/API/report work: produce concise closeout report with parents, derived children, applied effects, pending effects, exhausted facts, review packets, and blockers.
- Journal/replay work: preserve accepted parent facts and derived child provenance.
- Renderer/verifier work: verify, apply, rerun, and exact-round-trip.
- Tests: real-target smoke or fixture equivalent for post-apply rerun stability and blocker reporting.

## Research Coverage

- [ ] `017-097` and `017-098` completed and checked.
- [ ] Full Pandora cascade run reached fixed point.
- [ ] Verified effects were applied or precisely blocked.
- [ ] Rerun after application is stable.
- [ ] Remaining blockers are explicit and actionable.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This is the real replacement for superseded `017-096`.
- [ ] It does not treat pending verifier state as completed source progress.
- [ ] It gives a useful next-action report when safe progress is exhausted.
- [ ] Proposal 017 living notes updated with final state and next recommendation.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-098` complete.
- [ ] Focused closeout tests pass.
- [ ] Real Pandora cascade exhaustion run completed.
- [ ] Exact round-trip passes for any source output change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

