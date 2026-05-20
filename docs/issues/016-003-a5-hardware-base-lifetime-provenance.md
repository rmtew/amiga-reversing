Status: implemented
Source proposal: docs/proposals/016-pandora-reversing-loop-hardening.md
Moved from: docs/proposals/015-agent-reversing-pandora-target.md D007

Scope:
Add a read-only listing-state report for A5 hardware-base candidates before any
hardware register rendering pass.

Problem:
Pandora has many A5-relative operands. Some are `_custom` hardware accesses,
but A5 is also used for non-hardware pointers in other routines. Offset matching
alone is unsafe.

Required work:
- Report definitions, uses, clobbers, save/restore boundaries, and conflicts
  for candidate A5 hardware-base lifetimes.
- Distinguish probable `_custom` base candidates from unknown or conflicting
  ranges.
- Keep raw A5 displacements report-only until a lifetime is accepted.
- Define the verifier gate for rendering hardware register names from accepted
  lifetime evidence.

Acceptance:
- The report can explain why a selected A5-relative operand is a probable
  hardware-base candidate, unknown, or conflicting.
- No A5 hardware register naming action executes from offset match alone.
- Pandora can use the report to choose a safe next hardware/custom-register
  candidate family.

Implementation:
- Added `a5-hardware-report`, a read-only listing-backed report for A5
  definitions, uses, clobbers, save/restore boundaries, and lifetime status.
- A5-relative uses are classified as probable `_custom` candidates, unknown, or
  conflicting; raw displacement rendering remains blocked by an explicit
  verifier gate.
- The probable status is linear listing-state evidence only, not durable
  accepted path/lifetime evidence.
- Focused tests cover probable custom-base candidate use, unknown use, clobber
  reporting, save/restore boundaries, out-of-range custom-register conflicts,
  and the blocked rendering gate.
