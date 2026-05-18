Status: Open
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
