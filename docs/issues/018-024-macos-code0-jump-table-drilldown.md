# 018-024: Mac OS CODE 0 Jump Table Drilldown

Status: open

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

## Research Coverage

- [ ] CODE 0 jump-table payload traced.
- [ ] Routine candidate mapping traced.
- [ ] Row schema selected.
- [ ] Artifact rendering plan selected.
- [ ] Web/CDP rendering plan selected.
- [ ] 012/018 wording checked.

## Research Review

- [ ] Second pass checked CODE 0 is not ordinary code.
- [ ] Accepted layout facts separated from candidate target facts.
- [ ] Candidate routine mappings are not promoted.
- [ ] Artifact/web tests cover drilldown rows.
- [ ] Proposal/docs updated.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] CODE 0 jump-table drilldown rows added.
- [ ] Accepted/candidate distinction visible.
- [ ] CODE 0 remains metadata-only.
- [ ] MPW `Asm` artifact regenerated if output changes.
- [ ] CDP browser verification passes if web output changes.
- [ ] Relevant payload/artifact/web tests pass.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
