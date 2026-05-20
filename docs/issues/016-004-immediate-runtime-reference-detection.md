Status: proposed
Source proposal: docs/proposals/016-pandora-reversing-loop-hardening.md
Moved from: docs/proposals/015-agent-reversing-pandora-target.md D006

Scope:
Detect immediate constants that likely reference known source/runtime ranges.

Problem:
Pandora contains immediates such as `$5C72A` stored to absolute locations, where
the immediate falls inside known source/runtime address space. These can expose
data, code, or runtime-reference facts, but need source-family and conflict
reporting before writes.

Required work:
- Build a read-only report for immediate values that fall in known
  source/runtime ranges.
- Include source family, target section/offset, runtime address, instruction
  context, conflicts, and current render state.
- Define when an immediate may become a symbolic/interpreted reference versus
  remaining report-only.
- Add focused tests for accepted, conflicting, and out-of-range constants.

Acceptance:
- The report surfaces actionable Pandora immediate-reference candidates without
  mutating metadata.
- Planner writes remain blocked until verifier-backed interpretation exists.
