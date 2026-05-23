# 018-024: Mac OS CODE 0 Jump Table Drilldown

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS CODE 0 jump-table visibility and navigation
- Blocked by: `018-010`
- Work order: avoid concurrent edits with `018-023` because both touch Mac web
  container UI; can run after `018-019` if preview/web code is changing.
- Current proposal state: CODE 0 is correctly metadata-only and exposes summary
  jump-table spans plus candidate routine mapping, but artifact/web output does
  not provide a compact drilldown table of CODE 0 entries.
- Desired proposal state after this issue: CODE 0 jump-table entries are visible
  as structured artifact/web rows, with accepted jump-table metadata separated
  from candidate routine/segment interpretations.

## Knowledge Delta

- Adds: CODE 0 jump-table drilldown rendering obligations.
- Changes: jump-table evidence becomes inspectable entry-by-entry.
- Replaces: summary-only CODE 0 jump-table output.
- Deletes: no candidate/deferred evidence.
- Leaves out of scope: accepted routine entry validation, relocation/fixup
  interpretation, and full control-flow recovery.

## Default Behavior

- CODE 0 remains metadata/jump-table-only, not ordinary m68k.
- Jump-table byte layout facts may be accepted where KB-backed.
- Routine/segment interpretation remains candidate unless separately validated.
- UI/artifact must clearly distinguish accepted entry layout from candidate
  target meaning.

## Evidence Standard

- Rows must include entry index, CODE 0 payload offset, raw entry bytes or fields
  if available, target CODE resource where known, routine offset where known,
  fact id, fact status, parser-use.
- Candidate routine mappings must be visibly candidate.
- CDP or artifact tests must prove CODE 0 is not decoded as ordinary code.

## Implementation Slice

- Trace current `jump_table` and `code_segment_map.routine_entry_candidates`
  payload shapes.
- Add structured CODE 0 entry rows to payload if needed.
- Render rows in the committed artifact and Mac web UI.
- Add tests proving accepted/candidate distinction.
- Update docs with CODE 0 drilldown state.

## Research Completion Standard

Record trace blocks for:

- source payload fields consumed;
- accepted vs candidate row fields;
- artifact/web rendering shape;
- tests verifying metadata-only behavior;
- deferred areas.

## Research Notes

Trace blocks:

```text
Source payload fields consumed:
  CODE 0 code.jump_table supplies accepted layout start/entry_size/fact state.
  code_segment_map[].routine_entry_candidates supplies candidate
  code0_payload_offset, target resource, jump_table_offset, and routine offset.

Accepted vs candidate row fields:
  jump_table_rows[].accepted_layout carries macos.jump_table.entries.accepted
  with validated/accepted_parser_output state. jump_table_rows[].candidate_target
  carries macos.code_resource.jump_table.routine_offsets.candidate with
  candidate/candidate_only state.

Artifact/web rendering:
  The committed MPW artifact prints jump_table_rows under CODE 0 details. The
  web CODE 0 metadata block renders data-macos-code0-jump-row rows with accepted
  and candidate status columns.

Metadata-only behavior:
  CODE 0 listing remains kind=metadata, preview_windows remains empty, and tests
  keep asserting CODE 0 is not decoded as ordinary code.

Deferred areas:
  Routine/segment target meaning, relocation/fixup application, and full
  control-flow recovery remain outside this slice.
```

## Completion Evidence

```text
uv run python -m pytest tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_web_app_source.py -q
27 passed
uv run ruff check amiga_reversing\disasm\macos_project_payload.py amiga_reversing\disasm\macos_target_artifact.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_web_app_source.py tests\test_web_e2e_cdp.py
All checks passed!
node --check amiga_reversing\web\app.js
uv run python -m pytest tests\test_web_e2e_cdp.py::test_brave_cdp_macos_code_details_show_candidate_previews -q
1 passed
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.validate_018_issues
```

## Research Coverage

- [x] CODE 0 jump-table payload traced.
- [x] Routine candidate mapping traced.
- [x] Row schema selected.
- [x] Artifact rendering plan selected.
- [x] Web/CDP rendering plan selected.
- [x] 012/018 wording checked.

## Research Review

- [x] Second pass checked CODE 0 is not ordinary code.
- [x] Accepted layout facts separated from candidate target facts.
- [x] Candidate routine mappings are not promoted.
- [x] Artifact/web tests cover drilldown rows.
- [x] Proposal/docs updated.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] CODE 0 jump-table drilldown rows added.
- [x] Accepted/candidate distinction visible.
- [x] CODE 0 remains metadata-only.
- [x] MPW `Asm` artifact regenerated if output changes.
- [x] CDP browser verification passes if web output changes.
- [x] Relevant payload/artifact/web tests pass.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.
