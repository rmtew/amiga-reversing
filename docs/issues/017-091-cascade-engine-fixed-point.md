# 017-091: Implement Cascade Engine Fixed-Point Core

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-090` must be complete first.
- Protocol area: deterministic cascade execution and fixed-point exhaustion.
- Current proposal state: accepted facts replay into effective metadata, but derived analysis is report-local and not exhausted generically.
- Desired proposal state after this issue: accepted parent facts can run deterministic derivation rules to fixed point and expose derived/blocked child facts with provenance.

## Protocol Delta

- Adds: a reusable cascade engine entry point.
- Changes: reports can consume cascade state instead of reimplementing propagation.
- Replaces: one-off candidate mutation paths as the only way to get source progress.
- Leaves out of scope: full A5/RSSET/immediate/callback domain rules, source rendering changes, target state mutation, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- The engine must be deterministic and repeatable from current binary, metadata, Decision Journal, platform knowledge, and analysis code.
- It must emit parent facts, derived child facts, blocked child facts, and rule execution summaries.
- It must stop at fixed point and report why no more facts can be derived.
- It must fail closed on ambiguous identity, missing parent scope, missing rule support, or unstable source state.

## Pandora Proof

- Use fixture parent facts for at least two domains, preferably A5 lifetime and source/runtime address.
- Real Pandora can be read-only in this issue; the proof is engine correctness, not target mutation.

## Implementation Slice

- C fact graph/query work: put the durable analysis/cascade state in C where it overlaps existing C-owned facts, or explicitly document any temporary Python wrapper boundary.
- Python/API/report work: expose an inspection API/CLI for cascade state.
- Journal/replay work: feed accepted parent facts into cascade input.
- Renderer/verifier work: no source mutation yet; report candidate render effects only.
- Tests: fixed-point convergence, provenance, invalidation, deterministic rerun, blocked child emission.

## Research Coverage

- [x] `017-090` schema used directly.
- [x] Engine rerun is deterministic.
- [x] Parent-to-child provenance is preserved.
- [x] Invalid/stale parent facts do not produce children.
- [x] Fixed-point stop condition is explicit.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This implements reusable cascade infrastructure, not a domain-specific shortcut.
- [x] Any Python wrapper is justified and does not duplicate C-owned analysis logic.
- [x] The engine can be reused by A5, RSSET, immediate, and callback lanes.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-090` complete.
- [x] Focused cascade engine tests pass.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented reusable `run_cascade()` fixed-point execution in `amiga_reversing.disasm.cascade`.
- Added deterministic rule dispatch with `CascadeRule`, skipped-parent diagnostics, missing-rule blockers, and explicit stop reasons: `fixed_point_no_new_facts`, `no_rules`, and `max_iterations`.
- Added `inspect_cascade_state()` and CLI `cascade-report` as the read-only inspection API.
- Focused tests: `uv run python -m pytest tests/test_cascade.py -q`.
- Validation commands run after the full 017-090 through 017-096 batch: `uv run python -m amiga_reversing.tools.validate_017_issues` and `git diff --check`.

## Cascade Evidence

- Parent facts feed deterministic rules by `fact_type`; children retain `parent_fact_ids` and deterministic `rule_id`.
- Fixed point behavior checked with two fixture domains, A5 lifetime and runtime address, in `test_cascade_engine_runs_deterministic_fixed_point_for_two_domains`.
- Stale/invalid parents fail closed in `test_cascade_engine_fails_closed_for_stale_or_incomplete_parent`.
- Missing rule support emits structured blocked children in `test_cascade_engine_reports_missing_rule_support`.
- Baseline-delta verifier proof fields are preserved on derived facts; no source output write occurs from the engine.
- Not report-only: this issue added the reusable engine and public inspection command.
