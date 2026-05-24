# 017-056: Callback Orphan Review Item Unblocker

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: orphan/code-island acceptance and callback-slot evidence.
- Current proposal state: 017-055 found 7 concrete callback-slot missed-code-target assignments, but all remain blocked by `missing_orphan_code_review_item`, `review_item_is_not_code_classification`, or `target_row_missing`.
- Desired proposal state after this issue: each callback blocker is explained with stable evidence, and the next safe unblocker is either identified or explicitly deferred.

## Protocol Delta

- Adds: a current read-only classification of every callback-slot missed-code-target assignment from 017-055.
- Changes: proposal living notes with the exact blocker pattern and recommended follow-up.
- Replaces: no existing protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: callback-slot discovery remains read-only.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: no mutation authority may be exposed by this issue.

## Pandora Proof

- Target candidate: the 7 callback-slot missed-code-target assignments reported by current Pandora callback-slot discovery.
- Evidence packet expected: for each assignment, record callback slot, stored source offset, target row lookup state, matching review item state, blocker, and whether the blocker is data absence, review-item classification, or report/query mismatch.
- Decision behavior: no accept decision; record only a recommended next issue or defer reason.
- Command gate behavior: `safe_to_mutate=false` must remain true for this surface unless a later issue adds durable evidence and verifier gates.
- Render effect: none.
- Verifier/round-trip: run read-only report checks and exact round-trip only if any source-affecting support code is changed.

## Implementation Slice

- C fact graph/query work: none unless a read-only row lookup bug is proven and fixed.
- Python/API/report work: inspect `callback_slot_report` and related orphan/code review item generation; add only read-only classification if needed.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: focused report tests if report classification changes; otherwise document command outputs and proposal notes.

## Research Coverage

- [ ] Current callback-slot report rerun for the Pandora target.
- [ ] All 7 missed-code-target assignments listed with stable identity.
- [ ] `missing_orphan_code_review_item` cases traced to review item generation or true absence.
- [ ] `review_item_is_not_code_classification` cases traced to the current item kind/classification.
- [ ] `target_row_missing` cases traced to row lookup, source offset, or artifact limits.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed no mutation path was exposed.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Confirmed each blocker has a next action or a defer reason.
- [ ] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] 017-055 discovery findings used as the starting point.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete report correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
