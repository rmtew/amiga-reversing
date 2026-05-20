Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-005 blocker

Scope:
Expose RSSET/app-slot candidates for remaining raw or weak A6-relative
operands when the generic planner has no RSSET work.

Problem:
The current Pandora planner selected unrelated representation work and exposed
no `target.rsset_region.*` or `rsset.binding.*` candidate. Existing RSSET
command/verifier plumbing exists, but the target currently lacks accepted
source evidence for new bindings or field refinements.

Required work:
- Add or extend a read-only RSSET candidate report for remaining raw/weak A6
  operands.
- Group same-displacement and same-flow uses, xrefs, widths, access kinds, and
  adjacent accepted app-slot context.
- Explain whether each candidate is actionable, report-only, or blocked by
  missing base evidence, source family, ownership, cleanup, or verifier.
- Surface command catalog availability for the selected row/element/range.
- Do not generate generic adjacency names or class/address names as target
  progress.

Acceptance:
- Pandora gets a ranked RSSET/app-slot candidate report even when ordinary
  `inspect` has no candidate work.
- Each candidate states the exact missing gate or supported command path.
- A safe accepted candidate can proceed to mutation; otherwise proposal 017
  records the best blocker without target mutation.

Blocked by:
- 017-005.

Result:
- Added a read-only `rsset-candidate-report` command that scans listing rows
  for A6 displacement uses, groups same-displacement uses, reports access/width
  counts, selected-use identity, nearby app-slot/layout context, and
  `rsset.binding.report` / `rsset.binding.bind` command support.
- Pandora validation found 125 grouped candidates and 994 A6 uses. The top
  group is `rsset-raw-a6:022E`, but it remains blocked with
  `missing_accepted_base_evidence`; `rsset.binding.bind` is only catalog-visible
  from selected app-slot context and the report keeps `safe_to_mutate=false`.
- No target mutation was performed. A later source-changing action still needs
  accepted app-base evidence, the normal verifier path, and exact round-trip.
