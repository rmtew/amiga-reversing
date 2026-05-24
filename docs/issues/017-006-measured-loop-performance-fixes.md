Status: deferred
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

Current state:
This is the only remaining local `017-*` issue after completed 017 issue files
were deleted from `docs/issues`. It is a conditional sentinel, not an active
worker assignment. Do not pick it up unless a current 017 Pandora task produces
a measured slow phase that meets the trigger below.

Scope:
Fix only measured loop-performance bottlenecks encountered during active
Pandora work.

Problem:
Slow listing projection, command discovery, semantic reload, C rebuild, or
round-trip spans can make the reversing loop inefficient. These should be
profiled and fixed when they block the current Pandora candidate, not ignored
or optimized speculatively.

Required work:
- Capture wall-clock timing and `workflow_profile` spans for slow active
  Pandora iterations.
- Investigate phases over 30 seconds, repeated dominant spans, or latency that
  blocks interactive reversing flow.
- Diagnose before refactoring and fix only the measured bottleneck.
- Rerun the original Pandora action or report to prove the improvement.
- Record before/after timing and verification in proposal 017.

Acceptance:
- A concrete slow span is named with before/after timing.
- The fix has focused tests or an equivalent reproducible verification.
- The original Pandora workflow still produces the same source-converging
  result and preserves required verification.

Blocked by:
- A measured slow phase from 017 work.

Trigger:
- A current 017 Pandora command, report, verifier, semantic reload, C rebuild,
  listing projection, or exact round-trip phase repeatedly exceeds 30 seconds;
  or
- a shorter repeated phase is the dominant blocker to interactive 017 protocol
  work and has wall-clock/profile evidence.

Out of scope:
- speculative optimization;
- cleanup unrelated to a measured 017 bottleneck;
- Proposal 012/018 work;
- Mac OS/platform executable format docs, KB, targets, or parser work.

Implementation notes:
- No measured slow phase blocked the active 017 Pandora work.
- `immediate-ref-report`, `a5-hardware-report`, and `run-one --dry-run` were
  observed around 8-9 seconds for this target, below the 30 second threshold in
  this issue.
- No performance refactor was started because there is no concrete bottleneck
  to prove before/after.

Verification:
- Timed active Pandora report/dry-run commands from 017-001 through 017-005.
