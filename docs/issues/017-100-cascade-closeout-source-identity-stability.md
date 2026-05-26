# 017-100: Fix Cascade Closeout Source Identity Stability

Status: active
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

- [ ] `017-099` closeout reviewed before implementation.
- [ ] Real Pandora source identity mismatch reproduced.
- [ ] Volatile fields identified and documented.
- [ ] Semantic identity canonicalization preserves stale-state detection.
- [ ] Closeout blocks on unexplained identity changes.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This fixes closeout stability, not a cosmetic report mismatch.
- [ ] The fix does not hide real stale-state changes.
- [ ] Real Pandora no longer passes with unstable source identity.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Focused cascade identity tests pass.
- [ ] Focused closeout tests pass.
- [ ] Real Pandora closeout rerun reviewed.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

