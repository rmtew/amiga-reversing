Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
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

Resolution:
- RSSET accepted base-evidence classification now requires `conflicts` to be
  present as an explicit non-string sequence and empty.
- Rejected evidence now reports distinct conflict-shape reasons for missing,
  malformed, and non-empty conflict state when the evidence otherwise claims
  accepted `rsset_app_base` provenance.
- Focused regression tests cover missing, string, non-sequence, and non-empty
  conflict state. Pandora `rsset-candidate-report` still reports
  `rsset-raw-a6:022E` as blocked with `accepted_base_evidence_count=0`.

Verification:
- `uv run python -m pytest tests\test_reversing_loop.py::test_rsset_candidate_report_groups_raw_a6_operands tests\test_reversing_loop.py::test_rsset_candidate_report_exposes_catalog_path_without_mutating tests\test_reversing_loop.py::test_rsset_candidate_report_requires_explicit_conflicts_for_base_evidence tests\test_reversing_loop.py::test_rsset_candidate_report_rejects_malformed_conflicts_for_base_evidence tests\test_reversing_loop.py::test_rsset_candidate_report_keeps_existing_manual_binding_non_actionable -q`
- `uv run python -m pytest tests\test_reversing_loop.py -k rsset_candidate_report -q`
- `uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py`
