# 017-075: Pandora Callback Candidate Triage

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: converting resolved Pandora callback-slot evidence into either a real callback-derived source improvement or a precise implemented blocker.
- Current proposal state: `017-074` resolved the disk/container listing blocker. `callback-report --target amiga_disk_pandora-1988-firebird` now opens the raw payload subtarget listing, but mutation remains blocked with no ready callback review item.
- Desired proposal state after this issue: the strongest current Pandora callback candidates are triaged through code-backed evidence. If the blockers are caused by missing extraction/report support, implement that support. If no candidate is safely actionable, record the exact blocker with fixture proof and no source mutation.

## Protocol Delta

- Adds: code-backed triage for the blockers now exposed by the resolved Pandora callback report.
- Changes: `target_row_missing`, `missing_stored_source_offset`, `missing_callback_consumer`, and `missing_target_bytes` must be treated as implementation questions to answer, not as final documentation-only endpoints.
- Replaces: stopping at `ready_callback_review_item` missing without determining whether a fixable report/dataflow/listing gap is hiding an actionable candidate.
- Leaves out of scope: speculative broad code seeding, manual acceptance without verifier proof, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- The disk target may be used as the user-facing command target, but all source-affecting callback work must use the resolved `listing_target_id` from the report.
- `callback-decision` and `decision-verifier-artifact` must operate on the concrete resolved subtarget when a candidate becomes actionable.
- Unsafe or incomplete candidates must stay non-mutating.
- If a blocker is due to missing extraction or report logic and can be fixed generally, fix it in the normal code path with focused tests.
- If a blocker is factual for the current binary, expose that fact as a structured blocker with enough evidence for the next worker to continue.

## Pandora Proof

- Container target: `amiga_disk_pandora-1988-firebird`
- Resolved listing target:
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Starting report state: listing opens, `slot_count=92`, `callback_orphan_code_signals=[]`, `safe_to_mutate=false`, and `missing_gates=["ready_callback_review_item"]`.
- Candidate families to inspect first:
  - `target_row_missing`
  - `missing_stored_source_offset`
  - `missing_callback_consumer`
  - `missing_target_bytes`
- Evidence packet expected: for each inspected family, structured current report evidence showing whether the blocker is fixable extraction/report debt, factual non-actionability, or a narrower follow-up.
- Decision behavior: no Decision Journal write unless one candidate passes the existing callback gates.
- Render effect: if one candidate becomes accepted, normal C backend source rendering must change only through effective metadata and pass verifier/round-trip.
- Verifier/round-trip: mandatory for any output change.

## Implementation Slice

- C fact graph/query work: if callback target rows, consumers, stored source offsets, or target bytes are missing because C/export data is incomplete, extend the C-owned data/query/export path rather than papering over it in Python.
- Python/API/report work: improve callback report triage so the strongest current Pandora blockers are separated into actionable extraction gaps, factual non-actionable cases, and verifier-ready candidates.
- Journal/replay work: if a verifier-ready candidate appears, run `callback-decision` against the resolved `listing_target_id`; otherwise do not write a journal record.
- Renderer/verifier work: if a decision is accepted, run `decision-verifier-artifact` against the resolved `listing_target_id` and require generated-source and exact-round-trip success.
- Tests: add focused fixture tests for any new extraction/report behavior, plus a real Pandora command rerun proving the final blocker or source change.

## Research Coverage

- [ ] `017-074` completion evidence checked before work.
- [ ] Current `callback-report --target amiga_disk_pandora-1988-firebird` rerun and summarized.
- [ ] Resolved `listing_target_id` used for any decision/verifier/source-affecting command.
- [ ] At least the strongest current `target_row_missing` candidates inspected and classified.
- [ ] At least the strongest current `missing_stored_source_offset` candidates inspected and classified.
- [ ] At least the strongest current `missing_callback_consumer` candidates inspected and classified.
- [ ] At least the strongest current `missing_target_bytes` candidates inspected and classified.
- [ ] Any fixable extraction/report blocker implemented in code with focused tests.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] The result is not documentation-only if a fixable extraction/report gap exists.
- [ ] Any real Pandora candidate exposed by this work is either processed through the existing callback gates or explicitly blocked by those gates.
- [ ] No Decision Journal write occurs on the disk/container target when the resolved subtarget is the source owner.
- [ ] No source write occurs without verifier artifact and exact round-trip success.
- [ ] Proposal 017 living notes updated with the real outcome.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-074` completion notes checked before work.
- [ ] Focused tests cover any new code path.
- [ ] Real Pandora callback report rerun.
- [ ] If a candidate becomes actionable, `callback-decision` uses the resolved `listing_target_id`.
- [ ] If a candidate becomes accepted, `decision-verifier-artifact` uses the resolved `listing_target_id`.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

