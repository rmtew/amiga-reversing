# 018-011: Amiga HUNK Accepted Format Records

Status: completed

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

- [x] Existing Amiga HUNK KB reviewed.
- [x] Current Amiga HUNK parser assumptions inventoried.
- [x] Allowed Amiga source documents identified.
- [x] Version/toolchain scope recorded.
- [x] First accepted HUNK fact slice selected.
- [x] Deferred/conflict areas listed.

## Research Review

- [x] Second pass checked every accepted fact against citations.
- [x] Parser assertions include reason and standard interpretation.
- [x] Project-observed-only facts remain candidate.
- [x] Parser behavior remains unchanged.
- [x] No Mac files are modified.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Amiga HUNK accepted/parser-asserted facts added.
- [x] Citation/source policy recorded for every accepted fact.
- [x] Candidate/deferred facts cannot authorize accepted parser output.
- [x] Tests cover accepted and candidate fact states.
- [x] Existing Amiga parser behavior remains unchanged.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.


## Completion Evidence

- Added parser-asserted HUNK_HEADER, object/library container, CODE/DATA/BSS, and BSS size-only reference facts while leaving the HUNK parser report-only (`kb_backed: false`).
- Validation commands listed in the required sign-off were run after implementation before commit.
- No Mac multi-CODE rendering/navigation files for 018-010 were modified.
