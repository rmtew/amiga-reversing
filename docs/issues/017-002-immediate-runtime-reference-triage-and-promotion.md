Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

Scope:
Use `immediate-ref-report` to find immediate constants that can become
verified symbolic references or data-block interpreted references.

Problem:
016 added a read-only report for immediate values that fall inside known
source/runtime ranges. The next step is to determine which reported candidates
are useful Pandora source facts, and which still need verifier or command
support.

Required work:
- Inspect `immediate-ref-report` candidates and surrounding listing/xrefs.
- Classify candidates by source family, conflict status, target data/code role,
  and whether rendering would improve source clarity.
- If a candidate has durable identity, command support, and verifier support,
  execute the smallest safe source-converging action.
- If support is missing, add the precise command/verifier/report gap to
  proposal 017 instead of bypassing the loop.
- Preserve exact round-trip for output-affecting changes.

Acceptance:
- At least one immediate-reference candidate is either safely promoted through
  a supported verified action or documented as blocked with exact missing
  support.
- No immediate value is rendered symbolically from report-only evidence alone.
- Proposal 017 records source family, conflicts, command/verifier result, and
  timing for the attempted candidate.

Blocked by:
- 017-001.

Implementation notes:
- Current `immediate-ref-report` returns 10 accepted, conflict-free Pandora
  candidates and no writable policy.
- Candidate triaged first: `s0:00006138` / `addi.l #458752,d0`, family
  `runtime_address`, target `section_index=0`, `source_offset=327680`,
  `runtime_address=458752`. Local context stores the result in
  `app_text_cursor_ptr(a6)`, so symbolic rendering could improve source clarity
  once verified.
- Promotion remains blocked. Missing support is now explicit in the report:
  an operand-level command that records a verified interpreted immediate
  reference, plus a projection/semantic reload verifier for the rendered target.
- No immediate is rendered symbolically from report-only evidence.

Verification:
- `reversing_loop immediate-ref-report --target ...`
- `pytest tests/test_reversing_loop.py -q`
