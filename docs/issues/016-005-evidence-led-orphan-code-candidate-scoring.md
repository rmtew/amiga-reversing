Status: proposed
Source proposal: docs/proposals/016-pandora-reversing-loop-hardening.md
Moved from: docs/proposals/015-agent-reversing-pandora-target.md D002

Scope:
Improve orphan-code candidate scoring from durable evidence rather than decode
plausibility alone.

Problem:
Proposal 015 proved that callback-slot evidence can safely expose missed code,
but remaining orphan-code candidates often had only terminal-decode evidence.
Broad code conversion from decodable bytes is too risky.

Required work:
- Score orphan-code candidates from accepted control/data-flow evidence first:
  callback slots, dispatch tables, stored code pointers, inbound control refs,
  and same-family evidence.
- Use decode plausibility only as supporting evidence.
- Add false-positive checks for all-zero data, post-68000-only instructions,
  unexpected A-line/F-line use, and suspicious register state.
- Keep candidates report-only unless durable identity, command support,
  type-specific verifier, and exact round-trip are available.

Acceptance:
- Review output distinguishes evidence-led missed-code candidates from
  terminal-decode-only candidates.
- The planner cannot clear orphan-code review items just to reduce count.
- Pandora follow-up work can choose concrete missed-code candidates with a
  reason chain.
