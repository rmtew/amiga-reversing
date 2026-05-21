Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-009 report-only RSSET candidates

Scope:
Turn the RSSET candidate report for remaining raw A6 operands into accepted
app-base evidence where safe.

Problem:
017 added `rsset-candidate-report` and found 125 grouped A6 displacement
candidates, with top group `rsset-raw-a6:022E`, but all remain report-only
because accepted app-base/source evidence is missing. Existing RSSET command
and verifier plumbing cannot safely bind or refine fields without that base
evidence.

Required work:
- Identify what evidence would prove the selected A6 app-base lifetime/scope
  for a raw A6 candidate group.
- Add or use a report that exposes accepted base evidence, source family,
  path/lifetime scope, conflicts, and ownership/cleanup requirements.
- Actively inspect xrefs, nearby setup code, existing Manual Action Log state,
  and target source context for the top RSSET candidate groups instead of only
  rerunning the report.
- Allow RSSET bind/refine only when the accepted evidence is present and the
  command/verifier can consume it.
- Keep adjacency-only or generic app-slot names blocked.

Acceptance:
- At least one raw A6 candidate group is either promoted through accepted
  RSSET/app-base evidence or documented with the exact missing proof.
- `rsset.binding.*` or `target.rsset_region.*` actions do not execute from
  report-only same-displacement evidence.
- Exact round-trip passes for any output-affecting RSSET mutation.

Depends on:
- 017-009 provides the report surface and candidate groups. It is not a current
  blocker for this issue.

Pre-implementation state:
- Rerun `rsset-candidate-report` reported 125 candidates with
  `safe_to_mutate=false` and `mutation_policy=report_only`.
- No accepted app-base/source evidence was found by the report itself for the
  raw A6 candidate groups, so `rsset.binding.*` and `target.rsset_region.*`
  actions remain blocked.
- Same-displacement adjacency and generic app-slot names are not durable
  evidence and were not promoted.
- Next action is to investigate whether accepted evidence can be established
  from flow/xrefs/manual state for the top candidate groups. If not, record the
  concrete searched locations and missing proof.

Result:
- `rsset-candidate-report` now searches selected-use source evidence,
  same-displacement app-slot context, and existing Manual Action Log
  `rsset_use_site_bindings` before classifying a candidate.
- Accepted evidence must match the selected use and include
  `source_family=rsset_app_base`, an accepted status, `path_lifetime_scope`,
  empty conflicts, and a selected A6 `base_evidence_id`; generic app-slot
  context and same-displacement evidence are reported as rejected, not promoted.
- Pandora validation reports 125 grouped candidates from 994 A6 uses:
  124 remain blocked, and the only accepted-evidence group, `rsset-raw-a6:01AD`,
  is already recorded in manual state and therefore non-actionable.
- The top active group remains `rsset-raw-a6:022E` with 66 uses. Its exact
  missing proof is accepted `rsset_app_base` evidence, an accepted status,
  selected-use path/lifetime scope, empty conflicts, and a selected A6 base id.
- No output-affecting RSSET mutation was performed, so no round-trip-changing
  source update was needed.

Verification:
- `uv run python -m pytest tests\test_reversing_loop.py -q`
- Focused Pandora `rsset-candidate-report` summary:
  `candidate_count=125`, `use_count=994`, status counts
  `blocked=124`, `already_recorded=1`.

Post-review hardening:
- Tightened accepted RSSET/app-base evidence matching so report candidates only
  accept manual evidence with selected-use identity (`addr`, `operand_index`,
  `base_register`, `displacement`, and `hunk` when present) and a
  `selected_use` path/lifetime scope covering that exact use.
- Added regression tests for missing selected-use identity and non-selected-use
  scopes so consumers cannot treat broad or sparse base evidence as durable
  mutation evidence.
