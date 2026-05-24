# 017-062: Callback Target Row Missing Audit

Status: completed
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

- [x] Current callback report rerun for Pandora.
- [x] All `target_row_missing` assignments counted.
- [x] Representative sample selected across slots/stored-value shapes.
- [x] Missing cause taxonomy recorded.
- [x] Determined whether missing rows are expected or indicate a lookup/data extraction bug.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed no mutation path was exposed.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Confirmed any implementation follow-up is grounded in a concrete lookup/data extraction blocker.
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

Read-only command:

- `uv run python -m amiga_reversing.reversing_loop callback-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Current count:

- 173 callback assignments have `target_row_missing`.
- None are ready for `review.seed.code`.
- Callback mutation remains blocked by `ready_callback_review_item`.

Cause taxonomy:

| Cause | Count | Representative evidence | Classification |
| --- | ---: | --- | --- |
| Non-source-offset store | 155 | byte/word/clear/status/data-register writes such as `move.b d7,app_020B(a6)`, `clr.w app_01F4(a6)`, `move.l d0,app_029A(a6)` | expected non-code-pointer writes to app slots |
| No stored source value | 9 | `move.l a0,app_01EC(a6)` and similar address-register stores where the lookback window finds no preceding symbol load into that register | expected evidence absence; needs stronger dataflow before lookup |
| Lookup gap / non-label symbol | 6 | stores from symbols such as `app_0232`, `app_nearest_object_ptr`, and `runtime_address_00065370` | not source labels for callback targets; do not auto-promote |
| Row lookup limitation | 3 | immediate long stores `#$1A7E2`, `#$1AAFE`, `#$1309A` are inside binary bounds but not recovered by the current symbol-load path | possible later read-only enhancement, still not enough for mutation |
| Out-of-range value | 0 | none in current report | no issue |
| Artifact gap | 0 | none with a stored source offset but missing row | no issue |
| Unknown | 0 | none after store-shape classification | no issue |

Representative rows checked:

- Non-source-offset: `s0:00007034:instruction:4585`
  `clr.w app_01F4(a6)`, `s0:0000703A:instruction:4587`
  `move.w d3,app_01F6(a6)`, `s0:0000A24E:instruction:7424`
  `move.l d0,app_029A(a6)`.
- No stored source value: `s0:00006204:instruction:3558`
  `move.l a0,app_01EC(a6)`, plus three same-slot repeats and other address
  register stores without a nearby symbol-load source.
- Lookup gap: `s0:00002C66:instruction:2300` stores `app_0232`,
  `s0:00008366:instruction:6019` stores `app_nearest_object_ptr`, and
  `s0:000094EC:instruction:6844` stores `runtime_address_00065370`.
- Row lookup limitation: `s0:00009FE0:instruction:7242`,
  `s0:00009FE8:instruction:7243`, and `s0:0000A0A4:instruction:7288`
  store immediate long values that are not represented as prior symbol-load
  rows.

Conclusion:

- 170 of 173 cases are expected report blockers: scalar/non-source-offset app
  slot writes, address-register stores without a recoverable value source, or
  non-label symbols that do not identify source rows.
- The only concrete follow-up candidate is a read-only diagnostic enhancement
  for the 3 immediate long stores, to classify whether immediate values should
  ever be interpreted as callback target source offsets. Even there, mutation
  must remain blocked until code/data classification, review item identity,
  false-positive checks, and verifier gates exist.
- There is no current artifact coverage gap and no row exists that was missed
  after a valid stored source offset was resolved.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
