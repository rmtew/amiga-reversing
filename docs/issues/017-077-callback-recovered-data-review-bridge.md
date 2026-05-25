# 017-077: Callback Recovered Data Review Bridge

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: deciding whether recovered callback target data rows can become real review-backed code candidates.
- Current proposal state: `017-076` recovered 19 callback stored source offsets. Twelve recovered targets are already code. The remaining recovered data rows still do not become actionable because they lack callback consumers, lack an `orphan_code_candidate`, or are classified as `unreconciled_data_range`, with six also blocked by all-zero/data-like evidence.
- Desired proposal state after this issue: every recovered Pandora data target is classified with code-backed evidence as real data, already represented elsewhere, a missed code island that should produce an orphan-code review item/signal, or a precise non-actionable blocker.

## Protocol Delta

- Adds: a bridge from recovered callback data targets to review-item/orphan-code signal generation when evidence supports code.
- Changes: recovered data targets must not stop at `missing_orphan_code_review_item` or `review_item_is_not_code_classification` without explaining why the review state is correct or fixing the signal generation.
- Replaces: treating recovered data rows as terminally blocked just because no current review item can seed code.
- Leaves out of scope: speculative broad code seeding, manual acceptance without verifier proof, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unsafe recovered data rows must remain non-mutating.
- Already-code targets remain satisfied and must not generate duplicate review items.
- All-zero and data-like targets must fail closed unless stronger code evidence exists.
- If a recovered data row has credible callback-code evidence and lacks a matching `orphan_code_candidate`, implement the normal signal/report generation path that would create or surface one.
- If a recovered data row is covered by an `unreconciled_data_range`, classify whether that range is correctly data or whether it should be bridgeable to a code-review candidate.
- Any candidate that becomes actionable must still use `callback-decision`, effective metadata replay, verifier artifact, and exact round-trip on the resolved `listing_target_id`.

## Pandora Proof

- Container target: `amiga_disk_pandora-1988-firebird`
- Resolved listing target:
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Starting report state from `017-076`: 19 recovered stored offsets; 12 already code; the remaining recovered data targets blocked by `missing_callback_consumer`, `missing_orphan_code_review_item` or `review_item_is_not_code_classification`, with six all-zero/data-like rows.
- Candidate set: the recovered Pandora data rows only, not the whole callback report.
- Evidence packet expected: for each recovered data row, structured classification as `real_data`, `already_represented`, `missed_code_candidate`, or `blocked_non_code`, with cited row bytes, review item state, callback store provenance, and consumer state.
- Decision behavior: no Decision Journal write unless one candidate passes the existing callback gates.
- Render effect: if one candidate becomes accepted, normal C backend source rendering must change only through effective metadata and pass verifier/round-trip.
- Verifier/round-trip: mandatory for any output change.

## Implementation Slice

- C fact graph/query work: if recovered data-row classification needs existing C-owned code/data/string/table facts, xrefs, byte ranges, or review-item generation inputs, expose those through the normal analysis/export path rather than ad hoc Python-only inference.
- Python/API/report work: add recovered-data target classification to callback reports and generate/surface orphan-code signals only when byte/content/review evidence supports code.
- Journal/replay work: unchanged unless a candidate becomes actionable; then use `callback-decision` against the resolved `listing_target_id`.
- Renderer/verifier work: unchanged unless a candidate becomes accepted; then use `decision-verifier-artifact` against the resolved `listing_target_id`.
- Tests: add focused fixtures for already-code target, all-zero data target, data-like directive target, unreconciled-data-range target, missing-review missed-code target, and already-represented target.

## Research Coverage

- [x] `017-076` completion evidence checked before work.
- [x] Current Pandora callback report rerun and recovered data target set summarized.
- [x] Each recovered data row classified with structured evidence.
- [x] All-zero/data-like rows fail closed unless stronger code evidence is present.
- [x] `unreconciled_data_range` rows are either confirmed as data-like or bridged to a code-review candidate with proof.
- [x] Missing-review rows either generate/surface an orphan-code signal or record a precise reason they cannot.
- [x] Any newly actionable candidate still passes existing callback gates. No newly actionable candidate was found.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] The result is not documentation-only if a fixable review/signal generation gap exists.
- [x] Recovered data classifications are visible in report/evidence output.
- [x] Unsafe or ambiguous recovered data rows fail closed with structured reasons.
- [x] Any real Pandora candidate exposed by this work is either processed through the existing callback gates or explicitly blocked by those gates.
- [x] No Decision Journal write occurs on the disk/container target when the resolved subtarget is the source owner.
- [x] No source write occurs without verifier artifact and exact round-trip success.
- [x] Proposal 017 living notes updated with the real outcome.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-076` completion notes checked before work.
- [x] Focused tests cover each recovered-data classification case.
- [x] Real Pandora callback report rerun.
- [x] If a candidate becomes actionable, `callback-decision` uses the resolved `listing_target_id`. No candidate became actionable.
- [x] If a candidate becomes accepted, `decision-verifier-artifact` uses the resolved `listing_target_id`. No candidate became accepted.
- [x] Exact round-trip passes for any source change. No source change occurred.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Callback evidence packets now include `recovered_target_classification`, and
  the report summary includes `recovered_target_classification` counts.
- Focused fixture coverage proves already-code targets, all-zero data,
  data-like directives, unreconciled data ranges, missing-review missed-code
  signal surfacing, and existing orphan-code review item classification.
- Current Pandora rerun still resolves to
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
  with no source mutation and `callback_orphan_code_signals=[]`.
- Current recovered target classification summary:
  `already_represented=12` and `real_data=7`.
- The seven recovered data assignments are all non-actionable:
  six are zero-fill/data-like directives, and one unreconciled data range has
  bytes `$08,$88,$06,$66`, which do not look like terminal callback code. None
  has a callback consumer.
- No Decision Journal, target metadata, generated source, verifier artifact,
  012, 018, Mac, or platform-format files were written.
