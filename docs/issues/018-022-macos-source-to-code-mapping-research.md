# 018-022: Mac OS Source-To-CODE Mapping Research

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS MPW source/build products to CODE resource mapping
- Blocked by: `018-001`
- Work order: batch-safe with `018-021` and `018-025`; research/docs only.
- Current proposal state: source examples and MPW `Asm` executable container are
  both visible, but the project does not claim source segments map to observed
  CODE resources.
- Desired proposal state after this issue: source/build/CODE mapping evidence is
  researched and recorded as accepted, candidate, deferred, unsupported, or
  conflict facts without changing parser/rendering behavior.

## Knowledge Delta

- Adds: source-to-CODE mapping research packet for MPW examples and tools.
- Changes: current "not inferred" boundary gains concrete evidence and
  documented next constraints.
- Replaces: vague future source-to-CODE mapping note.
- Deletes: no boundary safeguards.
- Leaves out of scope: automatic source recovery, linker reconstruction,
  roundtrip, parser behavior, web behavior.

## Default Behavior

- `source_segments_map_to_observed_code_resources` remains false unless a
  separate implementation issue changes it.
- Project-observed correlations are candidate at most.
- Build/source claims must be separated from executable-container facts.
- No parser or UI behavior changes.

## Evidence Standard

- Research must compare source files, MPW build recipes, object/library mentions,
  resource declarations, and observed CODE resources.
- It must state which example source projects are suitable for future mapping
  work and which are not.
- It must distinguish MPW `Asm` executable evidence from separate sample source
  evidence.

## Implementation Slice

- Inspect existing `ext/macos_tools/mpw_gm` source/build metadata.
- Inspect relevant MPW docs/markdown for build/link/source segment behavior.
- Add a concise research section to `docs/platform-executable-formats.md` or a
  linked Mac research doc.
- Update Proposal 012/018 notes with the remaining mapping boundary.
- Do not change parser/payload/web output.

## Research Completion Standard

Record trace blocks for:

- source/build files inspected;
- CODE resources compared;
- mapping claims accepted/candidate/deferred;
- future implementation prerequisites;
- explicit non-goals.

## Research Coverage

- [x] MPW source metadata inspected.
- [x] MPW build recipes inspected.
- [x] Observed CODE resources compared.
- [x] Relevant docs searched.
- [x] Mapping claims classified.
- [x] Parser/UI non-change checked.

## Research Review

- [x] Second pass checked Sample/source facts are not conflated with Asm binary
  facts.
- [x] Project-observed-only claims remain candidate.
- [x] Parser/payload/web output remains unchanged.
- [x] Proposal/docs updated with exact mapping boundary.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Source-to-CODE research packet added.
- [x] Mapping claims classified by evidence strength.
- [x] Existing source/binary boundary remains safe.
- [x] Parser/UI behavior remains unchanged.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Inspected MPW tool/source metadata, observed MPW `Asm` CODE resource
  inventory, and existing Mac initial-analysis research notes.
- Searched local MPW documentation for Asm/Link, segment, CODE resource, and
  source-build mapping evidence.
- Added validated source-mapping packet
  `macos.packet.mpw.source_segment_to_code_resource_names`.
- Classified current Sample/Count/Memory to MPW/Tools/Asm mapping as deferred:
  the source fixtures and observed executable are different targets.
- Preserved the current safe boundary:
  `source_segments_map_to_observed_code_resources` remains false.
- Updated `docs/platform-executable-formats.md` and Proposal 018 notes.
- Issue validation run:
  `uv run python -m amiga_reversing.tools.validate_018_issues`
