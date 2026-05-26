# 017-106: Pandora Base Context Closeout

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Current 017 priority: base/context cascades.
- This is the closeout issue for the first base/context implementation batch.
- It should run only after the A5 child rendering and callback context issues
  have completed or explicitly deferred their blockers.

## Protocol Delta

- Adds: closeout proof for the base/context cascade lane.
- Changes: source-quality progress is judged by fixed-point verifier evidence,
  not report-only counts.
- Replaces: informal inspection of regenerated Pandora source.
- Leaves out of scope: unrelated Pandora reversing and new platform proposals.

## Default Behavior

- Run only after dependency issues complete or explicitly defer blockers.
- Apply only verifier-safe source deltas.
- If source progress is blocked, record exact blocker families and next work.
- Delete completed issue files only after durable outcomes are captured in
  Proposal 017.
- Closeout is not allowed to end the lane with generic blockers. Any remaining
  non-contradictory blocker must become a concrete implementation issue.

## What To Build

Run a full real-Pandora closeout for the base/context cascade lane. The closeout
must prove whether the new model produces source-quality progress, and it must
leave precise blockers for anything still not safe.

## Acceptance Criteria

- [ ] Real Pandora cascade/report output reaches a stable fixed point.
- [ ] The rendered Pandora source is refreshed if verifier-safe source deltas
      exist.
- [ ] The `$009C(a5)` regression is either rendered symbolically or blocked with
      a precise, evidence-backed reason.
- [ ] If `$009C(a5)` is not rendered symbolically, the closeout identifies the
      concrete contradiction or creates/updates the issue that implements the
      missing foundation.
- [ ] All derived A5 hardware children are classified as verified delta,
      already represented, exhausted, or blocked.
- [ ] Callback inherited register context around `app_0364(a6)` is classified
      as verified, exhausted, or blocked.
- [ ] `cascade-verify`, `cascade-apply --dry-run`, and `cascade-closeout` pass
      for the lane, or fail closed with actionable blocker names.
- [ ] Exact round-trip passes for any output-affecting target source change.
- [ ] Proposal 017 living notes summarize final counts, changed rows, blockers,
      and remaining next work.
- [ ] Completed issue files in this batch can be deleted only after their
      durable outcomes are captured in Proposal 017.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Blocked By

- docs/issues/017-103-a5-hardware-child-cascade-rendering.md
- docs/issues/017-104-callback-inherited-register-context.md
- docs/issues/017-105-cross-platform-base-context-rule-shape.md

## Research Coverage

- [ ] Dependency issue outcomes checked.
- [ ] Real Pandora cascade/report output rerun.
- [ ] Source export diff reviewed.
- [ ] Verifier/apply/closeout outputs captured.

## Research Review

- [ ] The `$009C(a5)` regression is resolved or precisely blocked.
- [ ] All A5 children are classified.
- [ ] Callback inherited context is classified.
- [ ] Remaining blockers are actionable, not vague.

## Required Sign-Off

- [ ] Proposal 017 checked before work.
- [ ] Dependency issue evidence checked before work.
- [ ] No report-only or generic-blocked closeout is used as completion.
- [ ] Real Pandora closeout command passes or fails closed.
- [ ] Exact round-trip passes for output-affecting changes.
- [ ] Refreshed source artifacts reviewed if changed.
- [ ] Proposal 017 living notes updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Out Of Scope

- Starting a new platform proposal.
- Reversing unrelated Pandora gameplay code without a base/context cascade
  connection.

## Anti-Bypass Rule

This closeout must either show verifier-backed source progress or leave the next
worker with specific implementation issues that remove the remaining blocker.
"Current analysis cannot prove it" is not a valid final state unless the issue
also explains the exact binary contradiction or unresolvable ambiguity.
