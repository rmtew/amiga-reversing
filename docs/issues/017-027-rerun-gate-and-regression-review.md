Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: post-closeout review

Scope:
Rerun the current 017 reports and focused regression checks after any reopened
017 work, then close the proposal only when the gates agree.

Problem:
The focused 017 pass changed core reversing-loop support code and target-local
manual state. A rerun should not rely only on issue notes; it needs an explicit
gate that rechecks immediate refs, A5 refs, RSSET candidates, planner output,
and exact round-trip status.

Required work:
- Rerun the current 017 report surfaces after completing any reopened 017
  issue: `immediate-ref-report`, `a5-hardware-report`,
  `rsset-candidate-report`, `inspect`, and `run-one --dry-run`.
- Run focused tests for any touched support code, plus the strongest available
  end-to-end/precommit gate when the other active work permits it.
- Update proposal 017 with current counts, remaining blockers, and whether a
  safe source-converging mutation remains.
- Do not close 017 while a command-backed, verifier-backed Pandora candidate
  remains untried.

Acceptance:
- Proposal 017 has a fresh rerun summary with report counts and verifier/test
  results.
- Any remaining work is either represented by proposed issues or explicitly
  deferred as report-only/out-of-scope.
- No pure timestamp churn is committed.

Blocked by:
- Resolved by completing and reviewing reopened blocker-removal issues
  `017-024` and `017-025`.
- Reopened again by review findings `017-028`, `017-029`, and the required
  Pandora exercise pass `017-030`.

Previous rerun:
- Reran `immediate-ref-report`, `a5-hardware-report`,
  `rsset-candidate-report`, `inspect`, and `run-one --dry-run` for the Pandora
  sub-target.
- Added the current counts and closeout decision to
  `docs/validation/pandora-017-rerun-2026-05-21.md` and proposal 017.
- No command-backed, verifier-backed Pandora mutation remained untried at that
  snapshot.
- This issue is blocked again until active 017 blocker-removal issues
  (`017-024`, `017-025`) are implemented or proven non-viable.

Result:
- Reran `immediate-ref-report`, `a5-hardware-report`,
  `rsset-candidate-report`, `inspect`, and `run-one --dry-run` for the Pandora
  sub-target after `017-024` and `017-025`.
- `immediate-ref-report`: 9 candidates, 0 command candidates, all report-only
  source-offset candidates.
- `a5-hardware-report`: 20 accepted path/lifetime evidence entries, all 20
  already present in manual state, 0 fresh command candidates, and 1
  address-mode-preserving entry-comment render.
- `rsset-candidate-report`: 125 grouped candidates from 994 A6 uses; 124
  blocked and 1 already recorded. The top active group is
  `rsset-raw-a6:022E`, blocked by missing accepted app-base evidence.
- `inspect`: no candidate work, verification paths available, round-trip
  status `exact`.
- `run-one --dry-run`: `action=null`, planner status `no_candidate`; remaining
  ranked candidates are 221 generic class/address data-symbol names and 4
  low-value literal representations.
- Proposal 017 was closed because no command-backed, verifier-backed,
  exact-round-trip Pandora source-converging mutation remains.

Verification:
- `cmd /c src\precommit.bat`
- Focused 017-027 report rerun through the Python report APIs.

Post-review rerun:
- Reran the focused gates again after `7756d772` tightened `017-025` RSSET
  selected-use evidence matching.
- `immediate-ref-report`: 9 candidates, 0 command candidates, all report-only
  source-offset candidates.
- `a5-hardware-report`: 20 accepted path/lifetime evidence entries, all 20
  already present in manual state, 0 fresh command candidates, and 1
  address-mode-preserving entry-comment render.
- `rsset-candidate-report`: 125 grouped candidates from 994 A6 uses; 124
  blocked and 1 already recorded. The top active group remains
  `rsset-raw-a6:022E`, with `accepted_base_evidence_count=0` and
  `missing_accepted_base_evidence`.
- `inspect`: no candidate work, verification paths available, round-trip
  status `exact`.
- `run-one --dry-run`: `action=null`, planner status `no_candidate`.
- This was a snapshot result, not final closeout. Reopened 017-025 review found
  an app-slot catalog fallback that still needed hardening before 017-027 could
  rerun as the closeout gate.

Reopened result:
- Reran the gate after the 017-025 catalog hardening that removed synthetic
  `selected-app-slot:*` base evidence for RSSET binds.
- `immediate-ref-report`: 9 candidates, 0 command candidates, all report-only
  source-offset candidates.
- `a5-hardware-report`: 20 accepted path/lifetime evidence entries already in
  manual state, 0 fresh command candidates, and 1 address-mode-preserving
  entry-comment render.
- `rsset-candidate-report`: 125 candidates from 994 A6 uses. Top active
  `rsset-raw-a6:022E` remains blocked with
  `accepted_base_evidence_count=0` and
  `catalog_state=report_only_same_displacement_app_slot_not_base_evidence`.
- `inspect`: Review state is clear, no candidate work is present, and
  round-trip status is exact.
- `run-one --dry-run`: `action=null`,
  `planner.status=no_candidate`, and planner message is
  `no supported source-converging command candidate`.

Reopened verification:
- Focused RSSET report/API tests for the 017-025 hardening.
- `cmd /c src\precommit.bat`
- Compact 017-027 Pandora rerun through the Python report APIs.

Current state:
- Final rerun after `017-028`, `017-029`, and `017-030` is complete.
- `immediate-ref-report`: 9 candidates, 0 command candidates, all report-only
  source-offset candidates.
- `a5-hardware-report`: 20 accepted path/lifetime evidence entries, 0 fresh
  command candidates, blocked only by missing command candidate after already
  recorded manual-state refs.
- `rsset-candidate-report`: 125 candidates from 994 A6 uses; status counts are
  `blocked=124` and `already_recorded=1`. Top active `rsset-raw-a6:022E`
  remains blocked with `accepted_base_evidence_count=0` and
  `catalog_state=report_only_same_displacement_app_slot_not_base_evidence`.
- `inspect`: no candidate work, verification paths available, and round-trip
  status `exact`.
- `run-one --dry-run`: `action=null`, `planner.status=no_candidate`, and
  `planner.message=no supported source-converging command candidate`.
- Dry-run ranked candidates are 221 generic class/address data-symbol names and
  4 low-value literal representation candidates; these remain non-progress
  under 017 rules.
- Proposal 017 is closed because no command-backed, verifier-backed,
  exact-round-trip Pandora source-converging mutation remains.

Final verification:
- Focused A5 entry-comment verifier tests: 3 passed.
- Focused RSSET candidate-report tests: 10 passed.
- `cmd /c src\precommit.bat`: passed.
