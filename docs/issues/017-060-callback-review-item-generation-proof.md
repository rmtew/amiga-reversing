# 017-060: Callback Review Item Generation Proof

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback/orphan-code review-item generation.
- Current proposal state: 017-056 found 5 callback missed-code-target assignments where a target row exists and is currently data, but no matching orphan/code review item exists.
- Desired proposal state after this issue: the missing review-item reason is proven for those rows, and the next safe path is either a read-only review-item-generation fix or an explicit blocker.

## Protocol Delta

- Adds: read-only proof explaining why the 5 callback target rows do not produce orphan/code review items.
- Changes: Proposal 017 living notes with exact findings and next action.
- Replaces: no protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, generated output, target metadata, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: callback review-item handling remains read-only.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: no callback seed/mutation command may become enabled.

## Pandora Proof

- Target candidates:
  - `app_020C` store `s0:000094D0` to `s0:0004D5DE`
  - `app_0210` store `s0:000094D4` to `s0:0004D5DE`
  - `app_027C` store `s0:00000730` to `s0:0004D5DE`
  - `app_0280` store `s0:00000F66` to `s0:00000B28`
  - `app_0280` store `s0:00001026` to `s0:00000B28`
- Evidence packet expected: callback slot, store row, stored source value, target row, target row classification, orphan-code signal presence/absence, review-item generation inputs, and exact missing condition.
- Decision behavior: no accept/defer/reject write; document blocker or recommend a later implementation issue.
- Command gate behavior: `review.seed.code` remains blocked by missing ready callback review item.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless current read-only row/signal data is missing a required field.
- Python/API/report work: trace `manual_review_items` orphan-code item generation and `callback_slot_report` lookup logic; add read-only diagnostic fields only if needed.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: focused read-only report/review-item tests if output shape changes; otherwise document current commands.

## Research Coverage

- [ ] Current callback report rerun for Pandora.
- [ ] Current manual review item generation inspected for the 5 target rows.
- [ ] Orphan-code signals checked for `s0:0004D5DE` and `s0:00000B28`.
- [ ] Review-item generation thresholds and filters checked.
- [ ] Exact missing condition recorded for each row.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed no mutation path was exposed.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Confirmed each row has a next action or explicit blocker.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] 017-056 completion evidence used as the starting point.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete read-only correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
