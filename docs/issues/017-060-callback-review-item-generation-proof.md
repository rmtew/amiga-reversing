# 017-060: Callback Review Item Generation Proof

Status: completed
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

- [x] Current callback report rerun for Pandora.
- [x] Current manual review item generation inspected for the 5 target rows.
- [x] Orphan-code signals checked for `s0:0004D5DE` and `s0:00000B28`.
- [x] Review-item generation thresholds and filters checked.
- [x] Exact missing condition recorded for each row.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed no mutation path was exposed.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Confirmed each row has a next action or explicit blocker.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] 017-056 completion evidence used as the starting point.
- [x] Output remains read-only.
- [x] Any support-code change is tied to a concrete read-only correctness blocker.
- [x] Focused tests pass if code changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only evidence commands:

- `uv run python -m amiga_reversing.reversing_loop callback-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Read-only server/project review-item inspection after listing open.

Current callback evidence for the five rows:

| Slot | Store | Value source | Target | Current review evidence | Missing condition |
| --- | --- | --- | --- | --- | --- |
| `app_020C` | `s0:000094D0:instruction:6835` | `lea.l abs_0_0005D5DE.l,a0` | `s0:0004D5DE:data:26379` / `dcb.b $200,$00` | covered by `unreconciled_data_range:h0:$0004d37e-$0004d7de`, not exact start | no `orphan_code_candidate` item at target start |
| `app_0210` | `s0:000094D4:instruction:6836` | `lea.l abs_0_0005D5DE.l,a0` | `s0:0004D5DE:data:26379` / `dcb.b $200,$00` | covered by `unreconciled_data_range:h0:$0004d37e-$0004d7de`, not exact start | no `orphan_code_candidate` item at target start |
| `app_027C` | `s0:00000730:instruction:471` | `lea.l abs_0_0005D5DE.l,a0` | `s0:0004D5DE:data:26379` / `dcb.b $200,$00` | covered by `unreconciled_data_range:h0:$0004d37e-$0004d7de`, not exact start | no `orphan_code_candidate` item at target start |
| `app_0280` | `s0:00000F66:instruction:1017` | `lea.l abs_0_00010B28(pc),a0` | `s0:00000B28:data:749` / `dcb.b $40,$00` | covered by `unreconciled_data_range:h0:$00000ac8-$00000ba8`, not exact start | no `orphan_code_candidate` item at target start |
| `app_0280` | `s0:00001026:instruction:1071` | `lea.l abs_0_00010B28(pc),a0` | `s0:00000B28:data:749` / `dcb.b $40,$00` | covered by `unreconciled_data_range:h0:$00000ac8-$00000ba8`, not exact start | no `orphan_code_candidate` item at target start |

Review-item generation proof:

- `manual_review_items._orphan_code_items(...)` emits orphan/code review items
  only from `section.orphan_code_signals`.
- The live review-item set has no `orphan_code_candidate` covering
  `s0:0004D5DE` or `s0:00000B28`.
- Both target rows are zero-fill data rows. They are covered only by low
  confidence `unreconciled_data_range` review items with `has_xrefs=false` and
  no `orphan_code_score`.
- `callback_slot_report` indexes review items by exact `start`; the covering
  data ranges start at `s0:0004D37E` and `s0:00000AC8`, not at the callback
  target starts. Even if the range-start mismatch were relaxed, these are data
  review items, not code-classification items.

Conclusion: the blocker is expected under the current generation model, not a
row lookup failure. A later implementation issue would need a read-only
callback-derived orphan-code signal model with false-positive checks for
zero-fill targets before any `review.seed.code` gate could be considered.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
