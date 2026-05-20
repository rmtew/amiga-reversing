Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: post-closeout review

Scope:
Record durable, reviewable evidence of the visible Pandora source improvements
made during the 017 focused pass.

Problem:
017 documented verified immediate-reference and A5 hardware-reference source
improvements, but the committed changes did not include a tracked refreshed
Pandora `.s` render or an explicit canonical-state decision. Current git status
only shows `.project.json` timestamp churn. That makes later review and rerun
harder because source-quality changes live in local target/manual state rather
than in a tracked evidence artifact.

Required work:
- Decide whether 017 should promote a tracked rendered `.s` artifact, a tracked
  source-quality report, or an explicit "local target state only" boundary.
- If promoting the `.s` render, regenerate it from current accepted Manual
  Action Log state and commit only meaningful source evidence, excluding
  timestamp-only `.project.json` churn.
- If not promoting the `.s` render, add a proposal note explaining how a rerun
  should reproduce the visible source state and what local state is required.
- Verify exact round-trip still passes after the evidence artifact is produced.

Acceptance:
- Reviewers can see or reproduce the 017 visible source improvements without
  relying on unstated local state.
- Timestamp-only target metadata churn is not committed as progress.
- Proposal 017 records the chosen evidence boundary.
- Resolving the evidence boundary is not a closeout by itself; continue to the
  next 017 rerun issue unless the proposal records a fundamental blocker.

Blocked by:
- 017-022.
