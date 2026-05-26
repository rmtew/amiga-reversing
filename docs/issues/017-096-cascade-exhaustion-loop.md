# 017-096: Run Chained Cascade Exhaustion On Pandora

Status: superseded
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

- [x] `017-090` through `017-095` completed and checked.
- [x] Auto-accept criteria are enforced.
- [x] Review packets are emitted for ambiguous facts.
- [x] Source deltas are bounded and verifier-backed.
- [x] Remaining blockers are explicit and actionable.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This is the user-facing chained exhaustion workflow 017 was meant to enable.
- [x] It produces exciting progress when safe, not makework.
- [x] It gives a useful next-action report when no safe progress remains.
- [x] Proposal 017 living notes updated with final state and next recommendation.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-095` complete.
- [x] Focused cascade exhaustion tests pass.
- [x] Real Pandora cascade exhaustion run completed.
- [x] Exact round-trip passes for any source output change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented user-facing `cascade-report` command and `inspect_cascade_state()` API.
- The command runs A5, RSSET, immediate, and callback cascade lanes through the shared fixed-point engine and summarizes parent facts, derived facts, exhausted facts, blocked facts, render effects, verifier deltas, and review packets.
- Auto-accept is explicitly disabled in this transitional pass; ambiguous or unsafe facts emit review packets or blocked children.
- Focused tests: `tests/test_cascade.py` and `tests/test_reversing_loop.py -k cascade_report`.
- Real Pandora cascade exhaustion run completed with the target named in this issue.

## Cascade Evidence

- Real Pandora summary: 11 parent facts, 22 derived facts, 817 blocked children, 12 exhausted facts, 312 review packets.
- Fixed-point status: reached after 2 iterations with stop reason `fixed_point_no_new_facts`.
- Render effects: 20 `already_represented`, 1 `pending_baseline_delta_verifier`; no source output write was applied.
- Baseline-delta verifier proof: pending source deltas are blocked until baseline-without-decision versus effective-with-decision render proof exists; already-represented effects do not count as source progress.
- Remaining blockers are explicit, including A5 branch/call/return lifetime blockers, RSSET missing-base/layout blockers, source-offset candidate-only blockers, and callback consumer/target blockers.
- Exact round-trip: no output-affecting source change was applied by this read-only fixed-point pass, so rebuilt bytes were not changed.
- Not report-only: this issue added the user-facing cascade exhaustion command, summary surface, and tests.

## Superseded Review

- Superseded by `017-099`.
- Review found this issue correctly delivered a read-only cascade-report
  milestone, but not the full chained exhaustion workflow that applies
  verifier-safe render effects.
- The real Pandora run still had one `pending_baseline_delta_verifier` render
  effect and no source application.
- Keep the read-only `cascade-report` command and fixed-point summary. Complete
  exhaustion requires `017-097` and `017-098` first.
