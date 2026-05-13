# 0001-003 Manual Seeds In Analysis

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make projected Manual Seeds participate in analysis. Entrypoint evidence remains primary, then metadata or policy, then required Manual Seeds, then suggested Manual Seeds. Code Manual Seeds run the normal analysis discovery loop for the target or runtime view and may cascade through real control-flow, table, and data evidence. Data Manual Seeds classify ranges using role, unit, and encoding fields.

## Acceptance criteria

- [x] Required code Manual Seeds can seed code analysis without unrelated whole-file speculative scanning.
- [x] Required data Manual Seeds can classify range data role, unit, and encoding.
- [x] Suggested Manual Seeds may be rejected when stronger evidence contradicts them.
- [x] Required Manual Seeds that conflict with entrypoint-proven or stronger facts produce manual seed conflict review work rather than overriding those facts.
- [x] Manual Seeds may target subranges and cause normalized block splitting where valid.
- [x] Analysis output preserves manual provenance distinctly from metadata, policy, and tool-inferred evidence.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completion

Completed on 2026-05-13.

Implemented Manual Seed projection into effective metadata, C backend policy consumption for code and data seeds, subrange rendering, provenance fields, stale-log blocking, and conflict review work for manual/manual, metadata/policy, project-visible, and explicit raw entrypoint conflicts.

Verification:

- `uv run python -m pytest tests\test_manual_action_log.py tests\test_manual_seed_effective_metadata.py tests\test_disasm_projects.py::test_get_project_exposes_manual_action_log_projection tests\test_disasm_projects.py::test_get_project_reports_manual_seed_conflict_with_target_metadata tests\test_c_backend.py::test_real_dll_seeded_entities_become_structured_data_policy_items tests\test_c_backend.py::test_real_dll_required_manual_code_seed_drives_c_analysis_without_implicit_scan tests\test_c_backend.py::test_real_dll_required_manual_data_seed_splits_rendered_subrange -q`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-001 Manual Action Log Projection
