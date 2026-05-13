# 0001-004 Manual Review Item Generation

## Parent

PRD 0001: Manual Review Workflow

## What to build

Generate base Manual Review Items from current analysis facts and projected manual state. Items have stable ids, Evidence Fingerprints, range or target scope, Review Confidence, state, and structured Suggested Review Actions. Apply Manual Resolutions by matching Evidence Fingerprints, reopening changed evidence as needed. Compute Review State as `clear`, `needs_review`, or `blocked`.

## Acceptance criteria

- [x] Review item ids are stable for target, kind, and normalized scope.
- [x] Evidence Fingerprints change when supporting facts change.
- [x] Resolutions close matching current evidence but changed evidence reopens review work.
- [x] Review item kinds include reproduction mismatch, unsupported container shape, orphan code candidate, unreconciled data range, suspicious instruction decode, manual seed conflict, manual action log inconsistency, and manual action log target mismatch.
- [x] `manual_action_log_target_mismatch` can be emitted from log/header validation even when normal manual projection is skipped.
- [x] Content Exactness failures or uncheckable content comparison set Review State to `blocked`.
- [x] Container-only differences create review work without necessarily blocking.
- [x] `clear` means no known actionable manual work remains, not full understanding.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completion

Completed on 2026-05-13.

Implemented finalized Manual Review Items with stable ids, Evidence Fingerprints, Review Confidence, state, Suggested Review Actions, and fingerprint-matched Manual Resolutions. Review item generation now covers Manual Action Log diagnostics/conflicts, reproduction mismatch and unsupported container-shape review work, and analysis-derived orphan code candidates, unreconciled data ranges, and suspicious instruction decodes. Project detail and listing navigation expose generated review work, and cached analysis review items update project Review State without making project listing run analysis.

Verification:

- `uv run python -m pytest tests\test_manual_action_log.py tests\test_manual_review_items.py tests\test_manual_seed_effective_metadata.py tests\test_disasm_projects.py::test_get_project_exposes_manual_action_log_projection tests\test_disasm_projects.py::test_get_project_reports_manual_seed_conflict_with_target_metadata tests\test_disasm_projects.py::test_get_project_blocks_on_reproduction_content_mismatch tests\test_disasm_projects.py::test_get_project_reports_container_only_reproduction_difference_without_blocking tests\test_disasm_server.py::test_route_project_overlays_cached_analysis_review_state tests\test_disasm_server.py::test_route_listing_navigation_uses_c_artifact_cache -q`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\manual_review_items.py amiga_reversing\disasm\projects.py amiga_reversing\disasm\server.py tests\test_manual_action_log.py tests\test_manual_review_items.py tests\test_disasm_projects.py tests\test_disasm_server.py`
- `uv run mypy amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\manual_review_items.py amiga_reversing\disasm\projects.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-001 Manual Action Log Projection
- 0001-003 Manual Seeds In Analysis
