# 018-001: Executable-Format KB Schema Gate

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: shared executable/container format schema and authority files
- Blocked by: none
- Current proposal state: 018 defines the need for one top-down executable
  format authority, but no schema or canonical KB files exist yet.
- Desired proposal state after this issue: later 018 issues have a concrete
  schema, source policy, fact state model, and thin Mac proof record to work
  against. No later issue may commit accepted KB records or parser changes before
  this gate is complete.

## Knowledge Delta

- Adds: shared schema shape, canonical KB file locations, fact states, source
  policy, citation/assertion rules, unknown/conflict/deferred handling, typed
  entrypoint vocabulary, and a thin Mac proof record.
- Changes: 018 becomes executable by workers rather than only a narrative
  proposal.
- Replaces: ad hoc parser facts embedded directly in platform code.
- Deletes: none.
- Leaves out of scope: full Mac/Amiga/Atari records, parser migrations,
  generated C metadata, and renderer changes.

## Default Behavior

- No parser behavior changes.
- No renderer behavior changes.
- No accepted platform facts beyond the thin proof record.
- Existing Mac heuristic code remains candidate behavior and must not be
  promoted by this issue.

## Evidence Standard

The schema must represent:

- platforms, format ids, archetype ids, producer/variant scope, and applies-to
  relationships;
- identification signatures, containers, regions, relocations, symbols, BSS,
  loader model, runtime model, analysis model, and renderer expectations;
- typed entrypoints: file, segment, runtime, exported, callback, and analysis
  seed;
- fact states: `validated`, `parser_asserted`, `candidate`, `deferred`,
  `unsupported`;
- source types: `old_out_of_print`, `modern_compatible`, `project_observed`,
  `parser_asserted`;
- unknowns, conflicts, deferred areas, unsupported areas, and required parser
  behavior;
- citations and parser assertions with reason, citation context, standard
  interpretation, and review status.

## Thin Proof

Add the smallest Mac proof record needed to prove the schema can express the 012
blocker:

- platform `macos`;
- format/archetype for HFS resource-fork CODE resources;
- `CODE 0` as metadata candidate/known role without overclaiming;
- nonzero `CODE` resources as segment-resource candidates;
- current `movea.l (a7)+,a0` boundary as candidate analysis seed evidence only.

## Implementation Slice

- Documentation: create/update `docs/platform-executable-formats.md`.
- KB schema: create `knowledge/platform_executable_formats.schema.json`.
- KB data: create `knowledge/platform_executable_formats.json`.
- Tests: add schema/fixture validation in the existing Python test style.
- Proposal: update 018 if schema decisions change during implementation.

## Research Completion Standard

Record trace blocks for existing knowledge file conventions, JSON schema/test
patterns, generated metadata patterns, source policy vocabulary, entrypoint
terminology, and the thin Mac proof record.

## Research Coverage

- [x] Existing `knowledge/` schema/data conventions checked.
- [x] Existing generated metadata conventions checked.
- [x] Existing docs citation/provenance conventions checked.
- [x] JSON schema validation/test pattern checked.
- [x] Mac proof record scope checked against 012 blocker text.
- [x] Source policy and fact state vocabulary checked against proposal 018.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Schema checked against Mac, Amiga, and Atari needs at a representative
  level.
- [x] Thin Mac proof record checked to avoid promoting heuristic evidence.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Canonical docs/schema/data files created.
- [x] Thin Mac proof record included.
- [x] Candidate facts cannot be consumed as accepted parser facts by schema
  design.
- [x] Unknown/conflict/deferred/unsupported states represented.
- [x] Tests validate schema and proof record.
- [x] No parser or renderer behavior changed.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Created `docs/platform-executable-formats.md`.
- Created `knowledge/platform_executable_formats.schema.json`.
- Created `knowledge/platform_executable_formats.json`.
- Added `amiga_reversing.tools.platform_executable_formats` validation.
- Added `tests/test_platform_executable_formats.py`.
- `uv run python -m pytest tests\test_platform_executable_formats.py -q`
  passed: 6 tests.
- `uv run ruff check amiga_reversing\tools\platform_executable_formats.py tests\test_platform_executable_formats.py`
  passed.
- Parser and renderer code paths were not changed.
