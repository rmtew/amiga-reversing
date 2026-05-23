# 018-028: Mac OS Source-To-CODE Fixture Strategy

Status: open

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

## Research Coverage

- [ ] Available Mac source fixtures inventoried.
- [ ] Build recipes/products checked.
- [ ] CODE resource inventories compared where available.
- [ ] Preferred fixture strategy selected.
- [ ] Missing artifacts listed.
- [ ] No-code-change boundary checked.

## Research Review

- [ ] Second pass checked no unrelated source/binary mapping is implied.
- [ ] Fixture ranking is evidence-backed.
- [ ] Future acceptance criteria are concrete.
- [ ] Proposal/docs updated.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Fixture strategy recorded.
- [ ] Candidate fixtures ranked or blocker recorded.
- [ ] Source/binary boundary remains safe.
- [ ] No code files modified.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
