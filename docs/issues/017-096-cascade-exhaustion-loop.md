# 017-096: Run Chained Cascade Exhaustion On Pandora

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-095` must be complete first.
- Protocol area: whole-target chained analysis exhaustion.
- Current proposal state: individual cascade lanes exist only after `017-090` through `017-095`.
- Desired proposal state after this issue: Pandora can run a deterministic cascade pass that exhausts all currently viable parent and derived facts, applies verifier-safe source improvements, and reports remaining blockers.

## Protocol Delta

- Adds: one user-facing cascade exhaustion command/report for Pandora-style target work.
- Changes: progress is measured by fixed-point source-quality improvement and explicit remaining blockers.
- Replaces: manually choosing isolated report packets as the main workflow.
- Leaves out of scope: unsafe bulk acceptance, speculative facts, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- The command must run deterministic analysis to fixed point.
- It may auto-accept only protocol-decidable facts.
- It must stop and emit review packets for ambiguous facts.
- It must apply or stage only verifier-safe render effects.
- It must summarize source deltas, derived facts, exhausted facts, blocked facts, and next review packets.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Expected result: visible source-quality progress where current evidence allows it, or a precise fixed-point blocker report if no safe progress remains.
- The report must be useful to a human continuing Pandora reversal.

## Implementation Slice

- C fact graph/query work: run cascade rules to fixed point over current analysis state.
- Python/API/report work: expose CLI/API report with concise source delta and blocker summary.
- Journal/replay work: apply accepted parent facts and auto-accepted decidable facts through the same path.
- Renderer/verifier work: verify every output-affecting cascade and exact-round-trip the final result.
- Tests: deterministic rerun, fixed-point stability, staged/source write scope, blocker summary, real Pandora smoke.

## Research Coverage

- [ ] `017-090` through `017-095` completed and checked.
- [ ] Auto-accept criteria are enforced.
- [ ] Review packets are emitted for ambiguous facts.
- [ ] Source deltas are bounded and verifier-backed.
- [ ] Remaining blockers are explicit and actionable.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This is the user-facing chained exhaustion workflow 017 was meant to enable.
- [ ] It produces exciting progress when safe, not makework.
- [ ] It gives a useful next-action report when no safe progress remains.
- [ ] Proposal 017 living notes updated with final state and next recommendation.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-095` complete.
- [ ] Focused cascade exhaustion tests pass.
- [ ] Real Pandora cascade exhaustion run completed.
- [ ] Exact round-trip passes for any source output change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

