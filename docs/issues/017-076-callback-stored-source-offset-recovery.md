# 017-076: Callback Stored Source Offset Recovery

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: converting the `017-075` `missing_stored_source_offset` bucket into either real callback candidates or precise non-candidate evidence.
- Current proposal state: Pandora callback reporting resolves the disk target to the raw payload listing and classifies current blockers. The largest useful follow-up is `narrower_follow_up=173`, all from missing stored source offsets.
- Desired proposal state after this issue: callback stored-source-offset recovery understands the safe address/dataflow cases currently hidden behind `missing_stored_source_offset`, and rerunning Pandora either promotes candidates to known target rows or records a narrower, implemented blocker.

## Protocol Delta

- Adds: source-offset recovery for callback slot stores whose stored value is currently unresolved.
- Changes: direct immediate stores and register stores must be classified by address semantics, not left as generic missing source offsets.
- Replaces: treating `direct_immediate_store_requires_address_model_proof` and `stored_register_has_no_nearby_symbol_load` as terminal states.
- Leaves out of scope: speculative callback acceptance, broad code seeding, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unsafe address interpretation must fail closed.
- Direct immediates must be separated into source offsets, runtime addresses that can be mapped to source offsets, absolute labels, and non-code constants.
- Register stores may use a broader value-source proof only when the dataflow remains local, unambiguous, and clobber-aware.
- Any recovered offset must still pass the existing callback report, review-item, Decision Journal, verifier, and exact round-trip gates before it can affect source.
- If a candidate becomes actionable, use the resolved `listing_target_id`, not the disk/container target, for `callback-decision` and `decision-verifier-artifact`.

## Pandora Proof

- Container target: `amiga_disk_pandora-1988-firebird`
- Resolved listing target:
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Starting report state from `017-075`: `missing_stored_source_offset=173`, with current reasons split between direct immediate stores needing address-model proof and register stores without a nearby symbol-backed value source.
- Candidate families to inspect first:
  - direct immediate stores such as `move.l #$1A7E2,app_xxxx(a6)`
  - register stores such as `move.l a0,app_xxxx(a6)` where `a0` may have a recoverable source value outside the current tiny lookback window
- Evidence packet expected: recovered stored source offset with provenance when safe, or a structured reason when unsafe.
- Decision behavior: no Decision Journal write unless one candidate passes the existing callback gates.
- Render effect: if one candidate becomes accepted, normal C backend source rendering must change only through effective metadata and pass verifier/round-trip.
- Verifier/round-trip: mandatory for any output change.

## Implementation Slice

- C fact graph/query work: if runtime-address/source-offset mapping, row address metadata, or local register value provenance belongs in C-owned analysis/export data, implement or extend it there rather than embedding platform facts in Python.
- Python/API/report work: extend callback report source-offset recovery to classify direct immediates and safe register-store value sources with explicit provenance.
- Journal/replay work: unchanged unless a candidate becomes actionable; then use `callback-decision` against the resolved `listing_target_id`.
- Renderer/verifier work: unchanged unless a candidate becomes accepted; then use `decision-verifier-artifact` against the resolved `listing_target_id`.
- Tests: add focused fixtures for direct source offset, runtime-address-to-source-offset mapping, absolute label, non-code constant, safe register provenance, and clobbered/ambiguous register provenance.

## Research Coverage

- [x] `017-075` completion evidence checked before work.
- [x] Current Pandora callback report rerun and summarized before changing code.
- [x] Existing source-offset/runtime-address metadata inspected before choosing implementation location.
- [x] Direct immediate stores classified into source offset, runtime address, absolute label, or non-code constant.
- [x] Register stores classified with clobber-aware local provenance where safe.
- [x] Any recovered target row still goes through existing callback review and verifier gates.
- [x] If no target row is recovered, report the narrower implemented blocker. Target rows were recovered; none became actionable.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] The result is not documentation-only if a fixable address/dataflow recovery gap exists.
- [x] Recovered offsets carry provenance in evidence packets.
- [x] Unsafe or ambiguous values fail closed with structured reasons.
- [x] Any real Pandora candidate exposed by this work is either processed through the existing callback gates or explicitly blocked by those gates.
- [x] No Decision Journal write occurs on the disk/container target when the resolved subtarget is the source owner.
- [x] No source write occurs without verifier artifact and exact round-trip success.
- [x] Proposal 017 living notes updated with the real outcome.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-075` completion notes checked before work.
- [x] Focused tests cover each new source-offset recovery case.
- [x] Real Pandora callback report rerun.
- [x] If a candidate becomes actionable, `callback-decision` uses the resolved `listing_target_id`. No candidate became actionable.
- [x] If a candidate becomes accepted, `decision-verifier-artifact` uses the resolved `listing_target_id`. No candidate became accepted.
- [x] Exact round-trip passes for any source change. No source change occurred.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- The callback report now recovers stored source offsets from existing listing
  metadata instead of embedding platform facts: source-offset rows,
  `runtime_address` rows, labels, and clobber-aware local register provenance.
- Focused tests cover direct source offsets, runtime-address-to-source-offset
  mapping, absolute labels, non-code constants, small immediate constants,
  safe wider register provenance, clobbered register provenance, and register
  provenance crossing a label boundary.
- Current Pandora rerun still resolves to
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
  with `slot_count=92`, `assignment_count=191`, and `safe_to_mutate=false`.
- The rerun recovered 19 stored source offsets with provenance. The recovered
  rows did not become source candidates: 12 are already code and the remaining
  recovered data rows are blocked by `missing_callback_consumer`, with six also
  blocked by `all_zero_data`/`data_like_directive`.
- Remaining missing source offsets are now narrower structured blockers:
  `store_does_not_write_an_address_register_value=117`,
  `direct_immediate_below_address_threshold=37`,
  `direct_immediate_not_listing_source_or_runtime_address=4`,
  `stored_register_clobbered_before_store=6`,
  `local_register_symbol_load_missing_listing_offset=6`,
  `register_symbol_load_crosses_label_boundary=1`, and
  `stored_register_has_no_nearby_symbol_load=1`.
- No Decision Journal, target metadata, generated source, verifier artifact,
  012, 018, Mac, or platform-format files were written.
