# 017-056: Callback Orphan Review Item Unblocker

Status: completed
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

- [x] Current callback-slot report rerun for the Pandora target.
- [x] All 7 missed-code-target assignments listed with stable identity.
- [x] `missing_orphan_code_review_item` cases traced to review item generation or true absence.
- [x] `review_item_is_not_code_classification` cases traced to the current item kind/classification.
- [x] `target_row_missing` cases traced to row lookup, source offset, or artifact limits.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed no mutation path was exposed.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Confirmed each blocker has a next action or a defer reason.
- [x] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] 017-055 discovery findings used as the starting point.
- [x] Output remains read-only.
- [x] Any support-code change is tied to a concrete report correctness blocker.
- [x] Focused tests pass if code changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only command rerun:

- `uv run python -m amiga_reversing.reversing_loop callback-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Current report summary:

- 92 callback/app slots, 191 assignments, 3 consumers.
- Assignment readiness: 180 blocked, 11 already-code, 0 ready.
- Blocker counts: 173 `target_row_missing`, 5 `missing_orphan_code_review_item`, 2 `review_item_is_not_code_classification`.
- Mutation gate stays blocked: `safe_to_mutate=false`, command
  `review.seed.code`, missing gate `ready_callback_review_item`, exact
  round-trip verifier available but not sufficient without a ready callback
  review item.

The 7 concrete missed-code-target assignments from `017-055` are:

| Slot | Store | Stored source | Target row | Target kind | Review item | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| `app_020C` | `s0:000094D0:instruction:6835` | `316894` / `abs_0_0005D5DE` | `s0:0004D5DE:data:26379` | data | none | `missing_orphan_code_review_item` |
| `app_0210` | `s0:000094D4:instruction:6836` | `316894` / `abs_0_0005D5DE` | `s0:0004D5DE:data:26379` | data | none | `missing_orphan_code_review_item` |
| `app_027C` | `s0:00000542:instruction:350` | `1902` / `abs_0_0001076E` | `s0:0000076E:data:493` | data | `unreconciled_data_range` | `review_item_is_not_code_classification` |
| `app_027C` | `s0:00000730:instruction:471` | `316894` / `abs_0_0005D5DE` | `s0:0004D5DE:data:26379` | data | none | `missing_orphan_code_review_item` |
| `app_027C` | `s0:00000D4E:instruction:909` | `2760` / `abs_0_00010AC8` | `s0:00000AC8:data:743` | data | `unreconciled_data_range` | `review_item_is_not_code_classification` |
| `app_0280` | `s0:00000F66:instruction:1017` | `2856` / `abs_0_00010B28` | `s0:00000B28:data:749` | data | none | `missing_orphan_code_review_item` |
| `app_0280` | `s0:00001026:instruction:1071` | `2856` / `abs_0_00010B28` | `s0:00000B28:data:749` | data | none | `missing_orphan_code_review_item` |

Blocker classification:

- `missing_orphan_code_review_item`: target row exists and is data, but there
  is no matching orphan/code review item identity to promote. Next action would
  be a separate read-only review-item generation issue; mutation remains
  unsafe here.
- `review_item_is_not_code_classification`: matching review item exists, but it
  is `unreconciled_data_range`, not a code classification. Next action is a
  data/code classification proof issue, not a callback seed.
- `target_row_missing`: 173 broader callback assignments do not resolve to a
  target row or source offset. They are not among the 7 concrete missed-code
  targets and remain deferred as row/value-source absence.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
