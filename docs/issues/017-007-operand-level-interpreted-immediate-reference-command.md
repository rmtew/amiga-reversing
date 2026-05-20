Status: blocked
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
- 2026-05-20 baseline is clean for
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`:
  hygiene has no unknown files, Review Items are clear, and round-trip status
  is exact.
- `immediate-ref-report` still finds 10 accepted conflict-free candidates. The
  strongest observed candidate remains `s0:00006138` / `addi.l #458752,d0`,
  mapping runtime address `$70000` to section 0 source offset `$50000`.
- No mutation was performed. The report policy remains `report_only` with
  `safe_to_mutate=false`, `symbolic_reference_allowed=false`, and
  `rendering_allowed=false` because command support and verifier support are
  both still missing.

Deferred follow-up:
- Implement the operand-level manual action, catalog command, projection, and
  semantic/render verifier before this candidate can be promoted.
