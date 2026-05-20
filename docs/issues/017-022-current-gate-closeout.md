Status: implemented
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md

Scope:
Reconcile Proposal 017 with the current post-hardening Pandora gate state after
the focused mutation pass.

Problem:
The proposal still had `Status: proposed` after the command-backed immediate
and A5 work was exhausted. Current reports show no safe source-converging
mutation remains: immediate-reference candidates are report-only, accepted A5
evidence is already recorded or blocked by rendering semantics, RSSET
candidates remain report-only, and the autonomous planner returns no action.

Acceptance:
- The proposal status reflects that the focused pass is complete until new
  evidence or tooling exists.
- The issues list includes this closeout item.
- Current blocked/report-only gates are summarized with concrete counts.
- Deferred 017-006 remains documented as no measured performance blocker, not
  hidden as unfinished implementation work.

Result:
- Proposal 017 now records the current gate summary and the boundary for future
  work without changing target state or performing a broad Pandora mutation run.
