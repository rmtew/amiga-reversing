# 018-011: Amiga HUNK Accepted Format Records

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Amiga HUNK executable/object/library format facts
- Blocked by: `018-001`
- Independent of: `018-010`
- Current proposal state: `amiga.hunk.load_file.basic_backfill` is report-only
  and candidate/deferred. Existing Amiga parser behavior is not yet backed by
  accepted executable-format KB facts.
- Desired proposal state after this issue: selected high-confidence Amiga HUNK
  file-structure facts are represented as `validated` or `parser_asserted`
  records without changing parser behavior.

## Knowledge Delta

- Adds: accepted/parser-asserted Amiga HUNK facts for core executable-bearing
  structures.
- Changes: Amiga backfill moves from pure candidate inventory to cited accepted
  KB facts for a narrow, reviewed slice.
- Replaces: undocumented reliance on project-local HUNK metadata for accepted
  parser claims.
- Deletes: none.
- Leaves out of scope: Amiga parser migration, roundtrip changes, loader edge
  cases not cited, overlays unless directly supported by sources.

## Default Behavior

- Existing Amiga parser/rendering behavior remains unchanged.
- New records may be `kb_backed: false` unless they are only reference facts.
- No parser area may claim KB-backed output from these records until a separate
  parser migration issue opts in.

## Evidence Standard

- Accepted facts require old/out-of-print or compatible cited sources, or
  `parser_asserted` facts with explicit reason, citation context, standard
  interpretation, and review status.
- Project-observed facts alone may support candidates, not validated general
  platform rules.
- Version scope must be recorded.
- Accepted facts must clearly distinguish executable load files, object files,
  libraries, resident/device structures, symbols, relocations, BSS, and loader
  behavior.

## Implementation Slice

- Review existing `knowledge/amiga_hunk_file.json`, current Amiga HUNK parser
  code, and allowed Amiga documentation sources.
- Add or update Amiga HUNK records in
  `knowledge/platform_executable_formats.json`.
- Update `docs/platform-executable-formats.md` with citation notes and any
  deferred/conflict areas.
- Add tests proving accepted facts are cited/parser-asserted and candidate facts
  do not authorize accepted parser output.
- Do not touch Mac CODE rendering/navigation files.

## Research Completion Standard

Record trace blocks for:

- source documents used and source policy classification;
- HUNK record kinds accepted in this slice;
- relocation/symbol/BSS facts accepted or deferred;
- parser assumptions left as candidate/deferred;
- explicit non-goals for parser migration.

## Research Coverage

- [ ] Existing Amiga HUNK KB reviewed.
- [ ] Current Amiga HUNK parser assumptions inventoried.
- [ ] Allowed Amiga source documents identified.
- [ ] Version/toolchain scope recorded.
- [ ] First accepted HUNK fact slice selected.
- [ ] Deferred/conflict areas listed.

## Research Review

- [ ] Second pass checked every accepted fact against citations.
- [ ] Parser assertions include reason and standard interpretation.
- [ ] Project-observed-only facts remain candidate.
- [ ] Parser behavior remains unchanged.
- [ ] No Mac files are modified.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Amiga HUNK accepted/parser-asserted facts added.
- [ ] Citation/source policy recorded for every accepted fact.
- [ ] Candidate/deferred facts cannot authorize accepted parser output.
- [ ] Tests cover accepted and candidate fact states.
- [ ] Existing Amiga parser behavior remains unchanged.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
