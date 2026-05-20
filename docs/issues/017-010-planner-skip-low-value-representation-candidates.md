Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017 baseline observation

Scope:
Make planner/report output stop treating low-value mechanical representation
changes as the effective next Pandora action when higher-value evidence
families are blocked.

Problem:
The current dry run selected an available `representation.character` action
after no higher-value candidate work was exposed. That may be mechanically safe
but lower value than immediate-reference, A5 path/lifetime, RSSET, or Review
Item work. If repeated, it can make the loop appear actionable while real
source-quality work is blocked by missing tooling.

Required work:
- Identify when representation candidates are syntax-led or low semantic value
  for Pandora.
- Report higher-value blocked families and their missing gates before selecting
  low-value representation work as progress.
- Keep genuinely semantic representation actions available when surrounding
  context supports them.
- Add planner tests for low-value representation ranking/skip behavior.

Acceptance:
- The planner distinguishes safe-but-low-value representation candidates from
  source-converging Pandora progress.
- Higher-value blocked families remain visible with actionable blocker reasons.
- Existing valid semantic representation actions are not disabled broadly.

Blocked by:
- 017-001.
