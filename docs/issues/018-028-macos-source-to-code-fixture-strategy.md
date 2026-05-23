# 018-028: Mac OS Source-To-CODE Fixture Strategy

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS source-to-CODE mapping fixture selection
- Blocked by: `018-022`, `018-025`
- Work order: batch-safe research/docs issue. Do not change parser/payload/web
  behavior.
- Current proposal state: MPW segment names to CODE resource names are cited,
  but the available Sample/Count/Memory source fixtures do not map to the
  observed MPW/Tools/Asm executable.
- Desired proposal state after this issue: the project has a concrete fixture
  strategy for future source-to-CODE validation: selected candidate fixture(s),
  required source/build/product evidence, missing artifacts, and acceptance
  criteria.

## Knowledge Delta

- Adds: fixture strategy for source-to-CODE mapping work.
- Changes: source-to-CODE closeout becomes an assignable path instead of a broad
  future item.
- Replaces: generic "map a source fixture to its own built binary" note.
- Deletes: no current source/binary boundary safeguards.
- Leaves out of scope: automatic mapping implementation, linker reconstruction,
  parser behavior, web behavior, and roundtrip.

## Default Behavior

- Keep `source_segments_map_to_observed_code_resources` false for MPW/Tools/Asm.
- Do not conflate example source with unrelated executable containers.
- Project-observed correlations remain candidate unless matching source/build
  product evidence exists.
- No code changes.

## Evidence Standard

- Strategy must compare available source fixtures, build recipes, generated
  products if present, CODE resource inventories, and docs.
- It must identify at least one preferred fixture or state why none is currently
  adequate.
- It must define what evidence is required before implementation can claim a
  source-to-CODE mapping.

## Implementation Slice

- Inspect `ext/macos_tools/mpw_gm`, extracted files, and docs for candidate
  source/build/product pairs.
- Rank fixture candidates.
- Add strategy text to Proposal 012 or a linked Mac research doc.
- Update Proposal 018 relationship notes if useful.
- Do not alter parser/payload/web output.

## Research Completion Standard

Record trace blocks for:

- candidate fixtures inspected;
- build/product evidence found;
- missing artifacts;
- selected strategy;
- acceptance criteria for future implementation.

## Resolution

Decision: docs-only fixture strategy selected; no parser/payload/web behavior
changed.

Trace blocks:

- Candidate fixtures inspected:
  `MPW-GM/Interfaces&Libraries/Interfaces/AStructMacs/Sample`,
  `MPW-GM/MPW/Examples/AExamples/Sample`, `Count`, and `Memory`.
- Build/product evidence found: AStructMacs/Sample has `Sample.a`,
  `Sample.make`, and `Sample.r`; AExamples/Sample has source/resource/make
  files; Count has source/resource plus MakeFile recipe; Memory has a DRVR/data
  file recipe.
- Missing artifacts: no captured or reproduced built product resource fork,
  CODE inventory, symbol/list map, or byte correspondence exists for those
  source fixtures in this repo.
- Selected strategy: use AStructMacs/Sample first after capturing/reproducing
  its own product because it is the narrowest APPL source/build/product
  fixture. Use AExamples/Sample as the semantic follow-up, Count as a small
  secondary smoke fixture, and defer Memory until non-APPL/DRVR mapping is in
  scope.
- Boundary: MPW/Tools/Asm remains a separate executable/container fixture;
  `source_segments_map_to_observed_code_resources` remains false.
- Future acceptance criteria: same-fixture source, build recipe, object/library
  inputs, Link/Rez commands, Finder type/creator, product hashes, extracted
  resource-fork/CODE inventory, symbol/segment map, and source-to-CODE byte
  validation.

## Research Coverage

- [x] Available Mac source fixtures inventoried.
- [x] Build recipes/products checked.
- [x] CODE resource inventories compared where available.
- [x] Preferred fixture strategy selected.
- [x] Missing artifacts listed.
- [x] No-code-change boundary checked.

## Research Review

- [x] Second pass checked no unrelated source/binary mapping is implied.
- [x] Fixture ranking is evidence-backed.
- [x] Future acceptance criteria are concrete.
- [x] Proposal/docs updated.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Fixture strategy recorded.
- [x] Candidate fixtures ranked or blocker recorded.
- [x] Source/binary boundary remains safe.
- [x] No code files modified.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

```text
Docs/research-only issue. No parser/payload/web behavior changes were made for
018-028.
uv run python -m amiga_reversing.tools.validate_018_issues
```
