Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md

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
