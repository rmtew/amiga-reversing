Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-002 blocker

Scope:
Add a safe mutation path for operand-level interpreted immediate references
that were discovered by `immediate-ref-report`.

Problem:
Pandora has conflict-free immediate-reference candidates, including
`s0:00006138` / `addi.l #458752,d0`, which computes `app_text_cursor_ptr` from
a runtime-address base. The report can classify the candidate, but promotion is
blocked because there is no command to record the interpreted immediate
reference and no verifier for the rendered/projection result.

Required work:
- Define a durable operand-level command for accepted interpreted immediate
  references.
- Preserve source family, selected operand identity, source/runtime target,
  conflict status, path/scope if needed, and owning action id.
- Add semantic reload/projection verification that the selected immediate
  renders or projects to the intended target reference.
- Keep report-only candidates blocked until the command and verifier consume
  accepted evidence.
- Validate on the Pandora `s0:00006138` candidate if it remains the strongest
  safe source-quality improvement.

Acceptance:
- A conflict-free immediate-reference candidate can be promoted only through
  accepted evidence, command support, verifier support, and exact round-trip.
- The verifier rejects stale selected operands, mismatched source family, and
  mismatched rendered target.
- Proposal 017 records the Pandora candidate result, including timing and
  exact round-trip status when output-affecting.

Current result:
- Added `immediate_ref.interpret` as a durable operand-level command backed by
  `interpret_manual_immediate_ref` log projection, effective metadata projection,
  target equate rendering, selected-operand representation, and runtime xref
  projection.
- `immediate-ref-report` now advertises mutation only for accepted,
  conflict-free runtime-address candidates whose immediate value fits the
  selected operand width. Plain source-offset matches and invalid-width
  candidates remain report-only because address-shaped constants can also be
  masks or counts.
- The verifier checks manual-log append, semantic reload under
  `immediate_interpreted_refs`, selected rendered operand symbol, projected xref
  owner/target identity, and exact round-trip. Regression tests reject stale
  selected operands, sparse payloads, mismatched xrefs, and byte-width overflow
  candidates.
- Pandora validation promoted `s0:00006138` / `addi.l #458752,d0`: runtime
  `$70000` now renders as `#imm_ref_h0_00050000_rt_00070000`, targeting section
  0 source offset `$50000`. Manual Action Log count advanced from 37 to 38 at
  head hash
  `924b8bd47d84ad8aabb01484808bf54f2e3434540480dd1b6fd1583f3cf5fa60`.
- Final verification passed after reopening the listing cache: manual log,
  semantic reload, rendered source, xref projection, and round-trip all passed;
  round-trip status was exact.

Deferred follow-up:
- The command invalidates the listing cache after append, so verifier callers
  must reopen the listing before render/xref checks. Persisting a refreshed
  tracked `.s` export remains separate from the local Manual Action Log state.
