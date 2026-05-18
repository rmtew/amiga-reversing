Status: Complete
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Expose every source-rendered data role that the C backend can consume through
durable Manual Action Log payloads and command catalog entries.

Current evidence:
- `platform_file_lib.c` recognizes data roles beyond the current command set:
  `copper_list`, `palette`, `pointer_table`, `lookup_table`/`scalar_table`,
  `length_prefixed_string`, `bitmap`, `sound_sample`, `string`,
  `audio_table`, `sprite`, and `string_control_stream`.
- The catalog currently exposes only raw/string/scalar_table/pointer_table plus
  byte/word/long unit choices.

Acceptance criteria:
- Row, range, and relevant review-item seed commands cover all supported
  source-rendered data roles.
- Each role has required parameters, durable identity, and projected metadata.
- Verifiers prove semantic reload, rendered-source effect, and round-trip
  exactness for every exposed role. If roles share one verifier implementation,
  the issue must name the equivalence class and include at least one rendering
  fixture per role.

Required tests:
Focused catalog availability/execution tests and role-specific rendering tests.

Result:
- Row, range, and unreconciled-data review catalogs now expose every C-backed
  source-rendered data role: `string`, `length_prefixed_string`,
  `string_control_stream`, `scalar_table`, `lookup_table`, `pointer_table`,
  `copper_list`, `palette`, `bitmap`, `sound_sample`, `audio_table`, and
  `sprite`.
- Role commands emit durable `create_manual_seed` payloads with hunk/range,
  `data_role`, `unit`, and `encoding` where required.
- Rendering coverage loads the Manual Action Log through effective metadata and
  proves each role projects into source text and direct-rebuilds exactly.
- Loop planner support is intentionally narrow here: `014-006` now mines obvious
  null-terminated printable ASCII data rows into `row.seed.data.string`
  candidates, while broader autonomous role inference remains a planner issue.

Verification:
- `uv run python -m pytest tests\test_disasm_server.py::test_route_project_overlays_cached_analysis_review_state tests\test_disasm_server.py::test_route_manual_action_catalog_returns_review_item_actions tests\test_disasm_server.py::test_route_manual_action_catalog_returns_row_and_element_actions tests\test_disasm_server.py::test_route_manual_action_catalog_returns_range_actions_with_mixed_eligibility tests\test_disasm_server.py::test_route_manual_action_catalog_execute_appends_row_data_type_helper_action tests\test_disasm_server.py::test_route_manual_action_catalog_execute_appends_valid_log_action -q`
- `uv run python -m pytest tests\test_c_backend.py::test_real_dll_required_manual_data_roles_render_source -q`
- `uv run ruff check amiga_reversing\disasm\manual_action_catalog.py tests\test_disasm_server.py tests\test_c_backend.py`
- `cmd /c src\precommit.bat`
