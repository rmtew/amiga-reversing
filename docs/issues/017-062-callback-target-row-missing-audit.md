# 017-062: Callback Target Row Missing Audit

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback target row lookup and value-source audit.
- Current proposal state: 017-056 found 173 broader callback assignments blocked by `target_row_missing`; they are not among the 7 concrete missed-code-target assignments.
- Desired proposal state after this issue: `target_row_missing` is classified as expected non-source-offset/value absence or as a concrete lookup/data extraction blocker with next action.

## Protocol Delta

- Adds: read-only audit of the `target_row_missing` callback assignment class.
- Changes: Proposal 017 living notes with representative causes and whether a later implementation issue is warranted.
- Replaces: no protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, generated output, target metadata, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: missing target rows remain non-actionable.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: no callback seed/mutation command may become enabled.

## Pandora Proof

- Target candidate family: the 173 current callback assignments with `target_row_missing`.
- Evidence packet expected: representative assignments grouped by missing cause: non-source-offset stored value, out-of-range value, no stored source value, row lookup limitation, artifact coverage gap, or unknown.
- Decision behavior: no accept/defer/reject write; document family-level blocker only.
- Command gate behavior: `review.seed.code` remains blocked.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless row lookup lacks required read-only diagnostics.
- Python/API/report work: inspect callback report target row lookup; add grouping diagnostics only if needed.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: focused read-only callback report tests if output shape changes.

## Research Coverage

- [ ] Current callback report rerun for Pandora.
- [ ] All `target_row_missing` assignments counted.
- [ ] Representative sample selected across slots/stored-value shapes.
- [ ] Missing cause taxonomy recorded.
- [ ] Determined whether missing rows are expected or indicate a lookup/data extraction bug.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed no mutation path was exposed.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Confirmed any implementation follow-up is grounded in a concrete lookup/data extraction blocker.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] 017-056 completion evidence used as the starting point.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete read-only correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
