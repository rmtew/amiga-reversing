# 018-001: Executable-Format KB Schema Gate

Status: open

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

- [ ] Existing `knowledge/` schema/data conventions checked.
- [ ] Existing generated metadata conventions checked.
- [ ] Existing docs citation/provenance conventions checked.
- [ ] JSON schema validation/test pattern checked.
- [ ] Mac proof record scope checked against 012 blocker text.
- [ ] Source policy and fact state vocabulary checked against proposal 018.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Schema checked against Mac, Amiga, and Atari needs at a representative
  level.
- [ ] Thin Mac proof record checked to avoid promoting heuristic evidence.
- [ ] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Canonical docs/schema/data files created.
- [ ] Thin Mac proof record included.
- [ ] Candidate facts cannot be consumed as accepted parser facts by schema
  design.
- [ ] Unknown/conflict/deferred/unsupported states represented.
- [ ] Tests validate schema and proof record.
- [ ] No parser or renderer behavior changed.
- [ ] Post-commit review found no unresolved worthwhile findings.
