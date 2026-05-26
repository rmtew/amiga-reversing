# 017-098: Apply Verifier-Safe Cascade Render Effects

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-097` must be complete first.
- Protocol area: writing only verifier-safe cascade effects.
- Current proposal state: `cascade-report` is read-only and can expose pending/verified effects only after `017-097`.
- Desired proposal state after this issue: verified cascade render effects can be applied through the normal source/metadata pipeline with exact round-trip and no timestamp-only or broad target churn.

## Protocol Delta

- Adds: apply/stage path for verified cascade render effects.
- Changes: cascade exhaustion can move from report-only to source-improving when verifier gates pass.
- Replaces: manual selected-row mutation as the only practical application route.
- Leaves out of scope: applying unverified pending effects, speculative auto-acceptance, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Apply only `verified_delta` effects from `017-097`.
- Write only conventional tracked artifacts required for the accepted render effect.
- Every write must be attributable to parent and derived child fact ids.
- Exact round-trip must pass after write.
- Already-represented effects must not be rewritten as progress.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Use a real verified cascade effect from `017-097` if available.
- Expected result: either a narrow source/metadata change with exact round-trip, or a precise "no verified effects to apply" blocker.

## Implementation Slice

- C fact graph/query work: consume verified cascade render effects through existing source-render metadata paths where possible.
- Python/API/report work: add dry-run-first apply command/API and report written/skipped effects.
- Journal/replay work: preserve parent/child provenance through application.
- Renderer/verifier work: regenerate affected source and exact-round-trip after write.
- Tests: dry-run no write, apply writes only expected files, already-represented no-op, stale verifier blocks, exact-round-trip failure blocks.

## Research Coverage

- [x] `017-097` verifier output checked.
- [x] Apply path is dry-run-first.
- [x] Written files are narrowly scoped and attributed.
- [x] Already-represented effects remain no-ops.
- [x] Exact round-trip is enforced after any write.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This applies only verifier-safe cascade effects.
- [x] No selected-row shortcut or legacy workaround is added.
- [x] Failed writes leave target state unchanged.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-097` complete.
- [x] Focused cascade apply tests pass.
- [x] Real Pandora apply dry-run reviewed.
- [x] Exact round-trip passes for any write.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added `cascade-apply` and `apply_verified_cascade_effects()` with dry-run
  default, stale verifier checks, already-represented no-op handling, staged
  exact round-trip before real writes, and post-write exact round-trip for any
  write.
- The apply path writes only a verified effect's attributed Decision Journal
  record for supported `verified_delta` effects. The real Pandora run produced
  no verified deltas, so no files were written.

## Cascade Evidence

- Real Pandora dry-run result:
  `planned_count=0`, `applied_count=0`, `no_op_count=21`,
  `blocked_count=0`, `status=passed`.
