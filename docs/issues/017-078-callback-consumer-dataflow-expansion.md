# 017-078: Callback Consumer Dataflow Expansion

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: improving callback consumer proof so recovered target rows are not blocked by an overly narrow consumer detector.
- Current proposal state: `017-077` classified all recovered Pandora callback targets. Twelve are already represented as code and seven are real data under current evidence. The seven recovered data rows all lack callback consumers, so no source mutation is justified.
- Desired proposal state after this issue: callback consumer detection handles safe local dataflow beyond the current direct slot-read-to-immediate-indirect-call pattern, or records narrower fail-closed blockers proving the current Pandora recovered rows are still non-actionable.

## Protocol Delta

- Adds: clobber-aware local callback consumer dataflow expansion.
- Changes: `missing_callback_consumer` must distinguish between no consumer, unsupported-but-local consumer shape, and unsafe/ambiguous dataflow.
- Replaces: treating absence of the one narrow direct consumer pattern as final evidence.
- Leaves out of scope: speculative broad interprocedural analysis, manual acceptance without verifier proof, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Safe consumer detection must still fail closed at branches, labels, register clobbers, unknown control-flow transfers, or ambiguous register moves.
- Supported consumer shapes should include:
  - app slot read into address register followed by `jsr`/`jmp (aN)`;
  - short clobber-aware delay between read and indirect call;
  - simple address-register move before the indirect call, such as `movea.l a0,a1` then `jsr (a1)`.
- Unsupported consumer shapes must be surfaced as structured blockers, not silently counted as no consumer.
- Any candidate that becomes actionable must still use `callback-decision`, effective metadata replay, verifier artifact, and exact round-trip on the resolved `listing_target_id`.

## Pandora Proof

- Container target: `amiga_disk_pandora-1988-firebird`
- Resolved listing target:
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Starting report state from `017-077`: recovered target classification summary is `already_represented=12`, `real_data=7`, with `callback_orphan_code_signals=[]` and no source mutation.
- Candidate set: recovered Pandora data rows plus any callback assignment currently blocked by `missing_callback_consumer`.
- Evidence packet expected: consumer dataflow proof when safe, or a structured blocker such as `consumer_not_found`, `consumer_register_clobbered`, `consumer_crosses_label_boundary`, `consumer_crosses_branch`, or `consumer_shape_unsupported`.
- Decision behavior: no Decision Journal write unless one candidate passes the existing callback gates.
- Render effect: if one candidate becomes accepted, normal C backend source rendering must change only through effective metadata and pass verifier/round-trip.
- Verifier/round-trip: mandatory for any output change.

## Implementation Slice

- C fact graph/query work: if branch/control-flow, register use/def, or instruction category facts are already C-owned or exported elsewhere, reuse or expose them through the normal analysis/export path rather than duplicating logic ad hoc.
- Python/API/report work: expand callback consumer detection with local clobber-aware dataflow and structured fail-closed blocker reasons.
- Journal/replay work: unchanged unless a candidate becomes actionable; then use `callback-decision` against the resolved `listing_target_id`.
- Renderer/verifier work: unchanged unless a candidate becomes accepted; then use `decision-verifier-artifact` against the resolved `listing_target_id`.
- Tests: add focused fixtures for direct consumer, delayed consumer, address-register move consumer, clobbered register, branch boundary, label boundary, unsupported consumer shape, and non-call slot read.

## Research Coverage

- [ ] `017-077` completion evidence checked before work.
- [ ] Current Pandora callback report rerun before changing code.
- [ ] Direct consumer detection preserved.
- [ ] Delayed clobber-aware consumer detection implemented or explicitly blocked.
- [ ] Address-register move consumer detection implemented or explicitly blocked.
- [ ] Branch, label, clobber, and unsupported-shape cases fail closed with structured reasons.
- [ ] Real Pandora rerun reports whether any recovered data target gains a consumer.
- [ ] Any newly actionable candidate still passes existing callback gates.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] The result is not documentation-only if a fixable local consumer dataflow gap exists.
- [ ] Consumer proof is visible in callback evidence packets.
- [ ] Unsafe or ambiguous consumer paths fail closed with structured reasons.
- [ ] Any real Pandora candidate exposed by this work is either processed through the existing callback gates or explicitly blocked by those gates.
- [ ] No Decision Journal write occurs on the disk/container target when the resolved subtarget is the source owner.
- [ ] No source write occurs without verifier artifact and exact round-trip success.
- [ ] Proposal 017 living notes updated with the real outcome.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-077` completion notes checked before work.
- [ ] Focused tests cover each consumer dataflow case.
- [ ] Real Pandora callback report rerun.
- [ ] If a candidate becomes actionable, `callback-decision` uses the resolved `listing_target_id`.
- [ ] If a candidate becomes accepted, `decision-verifier-artifact` uses the resolved `listing_target_id`.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

