# 018-012: Atari ST PRG Accepted Format Records

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Atari ST GEMDOS PRG/TOS/TTP executable facts
- Blocked by: `018-001`
- Independent of: `018-010`
- Current proposal state: `atari_st.prg.gemdos_basic_backfill` is report-only
  and candidate/deferred. Existing Atari ST parser behavior is not yet backed
  by accepted executable-format KB facts.
- Desired proposal state after this issue: selected high-confidence Atari ST
  PRG/TOS/TTP file-structure facts are represented as `validated` or
  `parser_asserted` records without changing parser behavior.

## Knowledge Delta

- Adds: accepted/parser-asserted Atari ST executable facts for GEMDOS
  PRG/TOS/TTP basics.
- Changes: Atari ST backfill moves from pure candidate inventory to cited
  accepted KB facts for a narrow, reviewed slice.
- Replaces: undocumented reliance on project-local PRG metadata for accepted
  parser claims.
- Deletes: none.
- Leaves out of scope: Atari parser migration, trap ABI modelling beyond cited
  context, TOS/GEMDOS runtime details not supported by sources.

## Default Behavior

- Existing Atari ST parser/rendering behavior remains unchanged.
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
- Accepted facts must distinguish header fields, TEXT/DATA/BSS, symbols,
  relocation stream, basepage/runtime entry, and file variants.

## Implementation Slice

- Review existing `knowledge/atari_st_prg_file.json`, current Atari ST parser
  code, and allowed Atari ST documentation sources.
- Add or update Atari ST records in
  `knowledge/platform_executable_formats.json`.
- Update `docs/platform-executable-formats.md` with citation notes and any
  deferred/conflict areas.
- Add tests proving accepted facts are cited/parser-asserted and candidate facts
  do not authorize accepted parser output.
- Do not touch Mac CODE rendering/navigation files.

## Research Completion Standard

Record trace blocks for:

- source documents used and source policy classification;
- PRG/TOS/TTP fields accepted in this slice;
- relocation/symbol/BSS facts accepted or deferred;
- parser assumptions left as candidate/deferred;
- explicit non-goals for parser migration.

## Research Coverage

- [x] Existing Atari ST PRG KB reviewed.
- [x] Current Atari ST parser assumptions inventoried.
- [x] Allowed Atari ST source documents identified.
- [x] Version/toolchain scope recorded.
- [x] First accepted Atari ST fact slice selected.
- [x] Deferred/conflict areas listed.

## Research Review

- [x] Second pass checked every accepted fact against citations.
- [x] Parser assertions include reason and standard interpretation.
- [x] Project-observed-only facts remain candidate.
- [x] Parser behavior remains unchanged.
- [x] No Mac files are modified.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Atari ST PRG/TOS/TTP accepted/parser-asserted facts added.
- [x] Citation/source policy recorded for every accepted fact.
- [x] Candidate/deferred facts cannot authorize accepted parser output.
- [x] Tests cover accepted and candidate fact states.
- [x] Existing Atari ST parser behavior remains unchanged.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.


## Completion Evidence

- Added parser-asserted PRG magic, container sequence, TEXT/DATA/BSS, and TEXT+DATA loaded-image reference facts while leaving the Atari parser report-only (`kb_backed: false`).
- Validation commands listed in the required sign-off were run after implementation before commit.
- No Mac multi-CODE rendering/navigation files for 018-010 were modified.
