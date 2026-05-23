# 018-015: MPW Object And Library Format Research Packet

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: MPW assembler/compiler object and library formats
- Blocked by: `018-001`
- Independent of: `018-010`
- Current proposal state: 018 models Mac application CODE resources, but MPW
  object/library formats are only in platform scope as future work. They may be
  needed to understand how source projects feed CODE resources.
- Desired proposal state after this issue: local MPW object/library format
  evidence is collected into citation packets or candidate/deferred KB records
  without changing CODE rendering/navigation.

## Knowledge Delta

- Adds: research packet for MPW object/library container formats, producers,
  link inputs, symbol/relocation concepts, and source-to-CODE relationships.
- Changes: MPW object/library work becomes explicit research debt rather than
  implicit future scope.
- Replaces: assumptions that CODE resources alone explain the whole build
  pipeline.
- Deletes: none.
- Leaves out of scope: parser implementation, object/library import support,
  CODE resource rendering/navigation, and roundtrip builds.

## Default Behavior

- No parser, renderer, or target artifact behavior changes.
- Facts remain citation packets/candidate/deferred unless local sources support
  accepted records.
- No modern incompatible source may be used as KB input.

## Evidence Standard

- Sources may be old/out-of-print local manuals/books, compatible modern
  sources, project-observed MPW files, or parser assertions.
- Citation packets must record source path, source type, license status,
  affected model layers, conflicts, missing evidence, and pre-migration parser
  behavior.
- Project-observed MPW files can support candidates, not validated general
  platform rules by themselves.

## Implementation Slice

- Search local Mac markdown/docs and extracted MPW filesystem contents for
  object/library format references and examples.
- Add citation packets or candidate/deferred records to
  `knowledge/platform_executable_formats.json` only if supported.
- Update `docs/platform-executable-formats.md` with what is known, unknown, and
  out of scope.
- Add tests if KB records are added.
- Do not change parser/rendering code.

## Research Completion Standard

Record trace blocks for:

- local docs searched and relevant pages;
- MPW files/examples found or not found;
- object/library fields, symbol, relocation, and linker input facts;
- conflicts or missing evidence;
- follow-up parser/import issue candidates.

## Research Coverage

- [x] Local MPW manuals/docs searched.
- [x] Extracted MPW filesystem examples searched.
- [x] Object format evidence recorded.
- [x] Library format evidence recorded.
- [x] Symbol/relocation/link input evidence recorded.
- [x] Missing evidence and conflicts listed.

## Research Review

- [x] Second pass checked citation packets against sources.
- [x] Project-observed-only facts remain candidate.
- [x] No parser/rendering behavior changed.
- [x] Follow-up parser/import issues are identified if warranted.
- [x] No 018-010 files are modified.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] MPW object/library research packet recorded.
- [x] Source policy recorded for every citation.
- [x] Candidate/deferred/unsupported state used where evidence is incomplete.
- [x] Tests added if KB records are added.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes if KB
  changes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.


## Completion Evidence

- Added MPW object/module and object-library citation packets, with byte-level object/library format details deferred.
- Validation commands listed in the required sign-off were run after implementation before commit.
- No Mac multi-CODE rendering/navigation files for 018-010 were modified.
