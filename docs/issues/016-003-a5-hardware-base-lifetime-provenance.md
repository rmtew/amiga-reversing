Status: proposed
Source proposal: docs/proposals/016-pandora-reversing-loop-hardening.md
Moved from: docs/proposals/015-agent-reversing-pandora-target.md D007

Scope:
Add read-only lifetime provenance for A5 hardware-base use before any hardware
register rendering pass.

Problem:
Pandora has many A5-relative operands. Some are `_custom` hardware accesses,
but A5 is also used for non-hardware pointers in other routines. Offset matching
alone is unsafe.

Required work:
- Report definitions, uses, clobbers, save/restore boundaries, and conflicts
  for candidate A5 hardware-base lifetimes.
- Distinguish proven `_custom` base ranges from unknown or conflicting ranges.
- Keep raw A5 displacements report-only until a lifetime is accepted.
- Define the verifier gate for rendering hardware register names from accepted
  lifetime evidence.

Acceptance:
- The report can explain why a selected A5-relative operand is proven hardware,
  unknown, or conflicting.
- No A5 hardware register naming action executes from offset match alone.
- Pandora can use the report to choose a safe next hardware/custom-register
  candidate family.
