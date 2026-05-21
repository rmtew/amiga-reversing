Status: active
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: review of 017-025 closeout

Scope:
Harden RSSET accepted base-evidence classification so conflict state is
explicit and empty.

Problem:
017-025 says accepted RSSET app-base evidence requires empty conflicts, but the
current accepted-evidence helper treats missing or malformed `conflicts` as an
empty list. That weakens the evidence boundary and can make incomplete evidence
look acceptable.

Required work:
- Require `conflicts` to be present as a sequence and empty for accepted
  `rsset_app_base` evidence.
- Reject missing, string, non-sequence, or non-empty conflict state with a clear
  report reason.
- Add focused regression tests for missing conflict state and malformed conflict
  state.
- Ensure the Pandora top active RSSET group remains blocked for missing
  accepted base evidence after this hardening.

Acceptance:
- Accepted RSSET base evidence cannot omit conflict state.
- Report output names the conflict-shape reason for rejected evidence where
  applicable.
- Focused tests pass.
