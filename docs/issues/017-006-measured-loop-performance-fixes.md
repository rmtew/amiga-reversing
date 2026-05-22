Status: deferred
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

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

Implementation notes:
- No measured slow phase blocked the active 017 Pandora work.
- `immediate-ref-report`, `a5-hardware-report`, and `run-one --dry-run` were
  observed around 8-9 seconds for this target, below the 30 second threshold in
  this issue.
- No performance refactor was started because there is no concrete bottleneck
  to prove before/after.

Verification:
- Timed active Pandora report/dry-run commands from 017-001 through 017-005.
