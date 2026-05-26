# 017-097: Implement Cascade Baseline-Delta Verifier

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-090` through `017-092` must be complete; `017-093` is superseded by this issue.
- Protocol area: proving that a parent fact causes bounded derived source effects.
- Current proposal state: cascade facts carry verifier-delta fields, but pending output effects still have `baseline_state=not_run` and `effective_state=not_run`.
- Desired proposal state after this issue: cascade verifier artifacts render baseline without the selected parent fact, render effective state with it, attribute changed rows to derived children, and block already-represented false positives.

## Protocol Delta

- Adds: real baseline-without-parent versus effective-with-parent verifier execution.
- Changes: `pending_baseline_delta_verifier` can become `verified_delta` only after actual render comparison.
- Replaces: verifier-delta state-only closeout from superseded `017-093`.
- Leaves out of scope: writing source output, bulk accepting parent facts, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Baseline render must exclude exactly the selected parent fact and derived children.
- Effective render must include the selected parent fact and derived children.
- Changed rows must be attributed to derived child fact ids.
- Already-represented legacy/manual state must not pass as source progress.
- Broad, unattributed, stale, or non-round-tripping deltas must fail closed.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Use the current pending cascade render effect if it remains available.
- Expected result: either a passing `verified_delta` with changed rows and exact round-trip, or a precise blocker explaining why no decision-caused source effect can be proven.

## Implementation Slice

- C fact graph/query work: expose render-effect identity and enough source rendering state for baseline/effective comparison.
- Python/API/report work: add cascade verifier command/API or extend `cascade-report` with explicit verifier execution.
- Journal/replay work: support excluding one parent fact for baseline rendering.
- Renderer/verifier work: implement baseline render, effective render, changed-row attribution, negative safety, fixed-point stability, and exact round-trip.
- Tests: already-represented false-positive regression, passing fixture delta, out-of-scope change failure, stale parent failure, exact-round-trip failure.

## Research Coverage

- [x] Superseded `017-093` reviewed before implementation.
- [x] Baseline excludes only the selected parent fact.
- [x] Effective render includes selected parent and derived children.
- [x] Changed rows are attributed to derived child fact ids.
- [x] Already-represented manual/legacy state blocks source-progress claims.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This implements verifier execution, not just verifier-delta data fields.
- [x] Verifier blocks broad or unexplained changes.
- [x] Verifier proves fixed-point cascade semantics before write.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-090` through `017-092` complete.
- [x] Focused cascade verifier tests pass.
- [x] Real Pandora verifier result reviewed.
- [x] Exact round-trip layer included for any output-affecting verified delta.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added `cascade-verify` and `verify_cascade_effects()` with real staged
  baseline/effective source rendering, changed-row attribution to child fact
  ids, stale-parent checks, false-positive blocking for already-represented
  effects, and exact round-trip enforcement for any `verified_delta`.
- Added regression coverage for already-represented no-delta, attributed fixture
  deltas, broad/unattributed deltas, stale parent state, and apply-time exact
  round-trip failures.

## Cascade Evidence

- Real Pandora verifier result:
  `checked_count=21`, `already_represented_count=21`,
  `verified_delta_count=0`, `blocked_count=0`, `status=passed`.
