# 017-076: Callback Stored Source Offset Recovery

Status: active
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

- [ ] `017-075` completion evidence checked before work.
- [ ] Current Pandora callback report rerun and summarized before changing code.
- [ ] Existing source-offset/runtime-address metadata inspected before choosing implementation location.
- [ ] Direct immediate stores classified into source offset, runtime address, absolute label, or non-code constant.
- [ ] Register stores classified with clobber-aware local provenance where safe.
- [ ] Any recovered target row still goes through existing callback review and verifier gates.
- [ ] If no target row is recovered, report the narrower implemented blocker.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] The result is not documentation-only if a fixable address/dataflow recovery gap exists.
- [ ] Recovered offsets carry provenance in evidence packets.
- [ ] Unsafe or ambiguous values fail closed with structured reasons.
- [ ] Any real Pandora candidate exposed by this work is either processed through the existing callback gates or explicitly blocked by those gates.
- [ ] No Decision Journal write occurs on the disk/container target when the resolved subtarget is the source owner.
- [ ] No source write occurs without verifier artifact and exact round-trip success.
- [ ] Proposal 017 living notes updated with the real outcome.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-075` completion notes checked before work.
- [ ] Focused tests cover each new source-offset recovery case.
- [ ] Real Pandora callback report rerun.
- [ ] If a candidate becomes actionable, `callback-decision` uses the resolved `listing_target_id`.
- [ ] If a candidate becomes accepted, `decision-verifier-artifact` uses the resolved `listing_target_id`.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

