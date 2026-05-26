# 017-100: Fix Cascade Closeout Source Identity Stability

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-097` through `017-099` must be reviewed first.
- Protocol area: fixed-point closeout stability and semantic source-state identity.
- Current proposal state: `cascade-closeout` can return `status=passed` while `fixed_point.source_state_identity_stable=false`.
- Desired proposal state after this issue: closeout identity is deterministic for semantically identical read-only runs, and closeout fails closed on unexplained identity changes.

## Protocol Delta

- Adds: stable semantic source-state identity for cascade inputs.
- Changes: `cascade-closeout` pass/fail must include source identity stability, not only summary stability.
- Replaces: summary-only closeout stability from `017-099`.
- Leaves out of scope: adding new cascade lanes, applying unverified effects, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Reproduce the real Pandora mismatch before changing code.
- Identify which fields make `source_state_identity` change between read-only runs.
- Canonicalize cascade identity inputs by stripping volatile fields while retaining semantic stale-state detection.
- `cascade-closeout` must return `status=blocked` with a precise blocker if source identity changes unexpectedly.
- Real Pandora closeout must not pass with `source_state_identity_stable=false`.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Required reproduction: before the fix, show read-only `cascade-closeout` can pass while source identity differs.
- Required result: after the fix, read-only `cascade-closeout` either has both `summary_stable=true` and `source_state_identity_stable=true`, or blocks with a precise volatile-field/stale-state diagnosis.

## Implementation Slice

- C fact graph/query work: unchanged unless the instability originates in C-owned semantic report fields.
- Python/API/report work: canonicalize cascade source identity inputs and expose identity diagnostics when unstable.
- Journal/replay work: unchanged unless Decision Journal projection includes volatile fields in identity.
- Renderer/verifier work: closeout pass/fail must account for identity stability.
- Tests: identity canonicalization, closeout fail-closed on identity mismatch, real or fixture read-only rerun stability.

## Research Coverage

- [x] `017-099` closeout reviewed before implementation.
- [x] Real Pandora source identity mismatch reproduced.
- [x] Volatile fields identified and documented.
- [x] Semantic identity canonicalization preserves stale-state detection.
- [x] Closeout blocks on unexplained identity changes.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This fixes closeout stability, not a cosmetic report mismatch.
- [x] The fix does not hide real stale-state changes.
- [x] Real Pandora no longer passes with unstable source identity.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Focused cascade identity tests pass.
- [x] Focused closeout tests pass.
- [x] Real Pandora closeout rerun reviewed.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added semantic source-state identity canonicalization for cascade input
  reports.
- Added closeout fail-closed behavior for unexplained identity drift.
- Added focused regression tests for volatile stripping, semantic job-field
  retention, and closeout blocking on identity mismatch.

## Cascade Evidence

- Reproduced the pre-fix Pandora defect: read-only `cascade-closeout` returned
  `status=passed` while `fixed_point.source_state_identity_stable=false`.
- Identified volatile identity inputs as listing-open job metadata:
  `listing_open.job.created_at`, `listing_open.job.finished_at`, and
  `listing_open.job.job_id` across A5, RSSET, immediate, and callback reports.
- Implemented semantic source-state identity canonicalization that strips only
  those volatile job fields while keeping semantic job status/error fields.
- Added closeout fail-closed behavior for unexplained identity drift:
  `source_state_identity_changed_without_summary_change`.
- Real Pandora post-fix closeout result:
  `status=passed`, `summary_stable=true`,
  `source_state_identity_stable=true`, and matching before/after
  `cascade-state:f21ad9827d8a4ac2773f0d3a`.
