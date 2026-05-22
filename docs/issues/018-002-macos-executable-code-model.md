# 018-002: Mac OS Executable Citation Packet

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: cited Mac OS executable/CODE facts
- Blocked by: `018-001` for final schema shape
- Current proposal state: 012 is blocked because current Mac CODE entry handling
  is heuristic. Local docs/MD/KB and MPW examples have not been mined into a
  fact packet.
- Desired proposal state after this issue: Mac CODE/resource/Segment Loader
  facts needed by 012 are collected as cited evidence packets, with unresolved
  areas explicitly marked candidate/deferred/unknown.

## Knowledge Delta

- Adds: citation packets for Mac resource fork, CODE resources, Segment Loader,
  A5 world, jump table, relocation/fixup, entrypoint, and MPW Link/Rez output
  facts where available.
- Changes: the current `movea.l (a7)+,a0` boundary is treated as candidate
  observed fixture evidence unless cited facts validate it.
- Replaces: fixture-pattern-only reasoning for Mac CODE entry.
- Deletes: none.
- Leaves out of scope: committing final KB records, parser changes, renderer
  changes, and full desk accessory/INIT/cdev/driver coverage unless shared facts
  are required.

## Default Behavior

- No parser behavior changes.
- No renderer behavior changes.
- No accepted KB records unless 018-001 schema exists and this issue explicitly
  records them as citation packets only.
- Current artifact may remain as-is; this issue is evidence collection.

## Evidence Standard

Each packet must record:

- fact candidate id and wording;
- source type and license status;
- citation target: local MD path/page/section, KB path, or committed fixture;
- whether the fact is `validated`, `parser_asserted`, `candidate`, `deferred`,
  or `unsupported`;
- whether it affects file structure, loader model, runtime entry model,
  analysis model, renderer expectation, or archetype identity;
- conflicts or missing evidence;
- parser behavior allowed before validation.

Observed fixture bytes alone can support only candidates or parser assertions.
They cannot validate a general platform rule.

## Mac Proof

Focus first on MPW `Asm` / application-style CODE resources:

- HFS file and resource fork relationship.
- `CODE 0` role.
- nonzero `CODE` resource role.
- A5 world / jump table / Segment Loader entry facts.
- MPW producer/variant scope.
- current observed `movea.l (a7)+,a0` boundary and whether sources explain it.

## Implementation Slice

- Research docs: mine local Mac MD/docs/KB and committed MPW metadata.
- Evidence packet: record fact packets in the location chosen by 018-001.
- Proposal: update 012 and 018 if evidence changes dependency or scope.
- No C/Python parser work in this issue.

## Research Completion Standard

Record trace blocks for local Mac docs searched, terms searched, MPW examples
checked, citation anchors found, facts accepted, facts rejected, conflicts, and
unknowns.

## Research Coverage

- [x] Local Mac MD/docs inventory checked.
- [x] Existing Mac KB/generated metadata checked.
- [x] MPW `Asm` resource metadata checked.
- [x] Segment Loader / CODE terms searched.
- [x] A5 world / jump table terms searched.
- [x] relocation/fixup terms searched.
- [x] MPW Link/Rez producer facts searched.
- [x] Current `movea.l (a7)+,a0` heuristic reviewed against sources.

## Research Review

- [x] Second pass checked trace blocks against named files.
- [x] Citation packet distinguishes validated, parser_asserted, candidate,
  deferred, and unsupported facts.
- [x] Fixture-only evidence did not become validated fact.
- [x] Proposal 012 blocker text updated if needed.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] 018-001 schema/output shape respected.
- [x] Citation packets created with source policy fields.
- [x] Mac `movea.l (a7)+,a0` heuristic remains candidate unless cited.
- [x] Unknowns/conflicts/deferred areas recorded.
- [x] No parser or renderer behavior changed.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added `citation_packets` to
  `knowledge/platform_executable_formats.schema.json`.
- Added Mac citation packets to
  `knowledge/platform_executable_formats.json`.
- Added packet validation to
  `amiga_reversing.tools.platform_executable_formats`.
- Added packet tests to `tests/test_platform_executable_formats.py`.
- Updated `docs/platform-executable-formats.md` trace blocks.
- Updated Proposal 012 status text to reflect that citation packets now exist
  but parser/listing migration still remains.
- `uv run python -m pytest tests\test_platform_executable_formats.py -q`
  passed: 9 tests.
- `uv run python -m amiga_reversing.tools.platform_executable_formats` passed.
- `uv run ruff check amiga_reversing\tools\platform_executable_formats.py tests\test_platform_executable_formats.py`
  passed.
- Parser and renderer code paths were not changed.
