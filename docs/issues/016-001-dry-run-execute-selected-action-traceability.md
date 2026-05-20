Status: implemented
Source proposal: docs/proposals/016-pandora-reversing-loop-hardening.md
Moved from: docs/proposals/015-agent-reversing-pandora-target.md D008

Scope:
Make `reversing_loop run-one --dry-run` and non-dry `run-one` selection
auditable and stable for the same target state.

Problem:
During 015, a Pandora dry run reported one selected action, while the execute
pass recomputed and applied a different valid action. The executed action was
verified, but the drift weakens operator trust: the user reviews one candidate
and the loop may execute another.

Required work:
- Record a selected-action trace after ranking and command availability checks.
- Include skipped candidate ids, skip reasons, and unavailable command errors.
- In non-dry mode, report when the executed candidate differs from the latest
  dry-run-equivalent candidate and why.
- Prefer deterministic candidate ordering when input state is unchanged.
- Add focused tests for stale candidate availability, alternate command
  fallback, and drift reporting.

Acceptance:
- A dry-run report contains enough information to explain the eventual execute
  choice.
- Execute either applies the same selected candidate for unchanged state or
  reports the precise skip/fallback that changed selection.
- No output-affecting Pandora action is required unless needed for repro.

Implementation:
- `run-one --dry-run` now runs the same command-catalog availability resolution
  used by execute, without executing the command.
- Planner reports include selected-before-availability,
  selected-after-availability, availability checks, skipped candidate ids, and
  stable/changed selection drift.
- Stale locator availability failures and alternate command fallback are covered
  by focused tests.
