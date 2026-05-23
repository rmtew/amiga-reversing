# 018-009: Mac OS CODE Entry, Relocation, And Segment Map

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS CODE byte-entry grounding, Segment Loader
  relocation/fixup semantics, and CODE 0 jump-table to segment/routine mapping
- Blocked by: `018-008`
- Current proposal state: Mac parser output is validated against executable
  KB fact ids, and the current `movea.l (a7)+,a0` boundary is honestly marked
  candidate-only. However, exact byte-level CODE entry rules, relocation/fixup
  interpretation, and full CODE segment/routine mapping remain deferred.
- Desired proposal state after this issue: Mac CODE rendering can enumerate and
  classify CODE resources from cited KB facts rather than from local
  `movea.l` scanning alone, with unresolved byte-entry or relocation questions
  explicitly deferred instead of silently guessed.

## Knowledge Delta

- Adds: cited or parser-asserted facts for Mac CODE byte-entry rules,
  Segment Loader relocation/fixup semantics, and CODE 0 jump-table mapping to
  CODE segment/routine candidates.
- Changes: Mac CODE analysis should use CODE 0/jump-table/segment metadata as
  primary evidence where the KB supports it.
- Replaces: any undocumented reliance on first observed
  `movea.l (a7)+,a0` as the only segment-entry discovery mechanism.
- Deletes: no current candidate output unless a cited rule replaces it.
- Leaves out of scope: byte-for-byte MPW roundtrip, complete source
  reconstruction, non-CODE resource semantics, Amiga/Atari migrations, and
  generated C tables beyond the Mac facts needed here.

## Default Behavior

- `movea.l (a7)+,a0` remains candidate-only unless a cited source validates it
  as an accepted byte-entry rule.
- If byte-level entry cannot be validated, the parser must keep candidate
  ranges and record what evidence is missing.
- If relocation/fixup semantics are only partly understood, emit structured
  deferred or placeholder data rather than accepted relocation output.
- Mac target output must improve toward day-appropriate Classic Mac OS assembly
  project structure, but roundtrip is not a requirement.

## Evidence Standard

- Every accepted Mac CODE fact must cite local MD/docs/KB or be
  `parser_asserted` with reason, citation context, standard interpretation, and
  review status.
- CODE 0 jump-table fields must be tied to concrete parser output fields and
  offsets where used.
- A segment/routine map must distinguish:
  - accepted segment metadata;
  - candidate routine entry addresses;
  - deferred relocation/fixup interpretation;
  - unsupported or out-of-scope resource behavior.
- Orphan code islands must not be ignored. They must be classified as accepted,
  candidate, deferred, unsupported, or conflict evidence with offsets and
  reason.
- Parser output fact ids/status/parser-use must pass 018-008 validation.

## Implementation Slice

- Research local Mac markdown/docs and existing extracted MPW data for:
  CODE 0 jump-table layout, nonzero CODE segment headers, Segment Loader
  relocation/fixup records, inter-segment calls, startup entry, and routine
  entry conventions.
- Update `docs/platform-executable-formats.md` and
  `knowledge/platform_executable_formats.json` with accepted/candidate/deferred
  facts.
- Extend Mac parser summary to expose CODE 0 jump-table entries and a
  segment/routine map where facts support it.
- Update listing/project payloads so selected and non-selected CODE resources
  can be represented as structured segment/routine candidates, not just one
  rendered candidate range.
- Add tests using the MPW Asm fixture proving:
  - CODE 0 metadata drives the segment/routine map where accepted;
  - `movea.l` scanning is not promoted to accepted entry evidence;
  - orphan code/data islands are reported as candidate/deferred/conflict
    evidence rather than dropped;
  - parser fact ids pass 018-008 validation.
- Update Proposal 012 blocker text with the new accepted/deferred state.

## Research Completion Standard

Record trace blocks for:

- Mac manual/document pages used for CODE 0, jump-table, Segment Loader,
  relocation/fixup, and entry conventions;
- existing parser fields and byte offsets for CODE 0 and nonzero CODE
  resources;
- observed MPW Asm CODE resources with selected examples of candidate entry
  points and orphan islands;
- any rule that remains candidate/deferred and why;
- tests that prove the parser no longer silently drops relevant CODE evidence.

## Research Coverage

- [ ] Local Mac MD/docs searched for Segment Loader relocation/fixup semantics.
- [ ] Local Mac MD/docs searched for CODE 0 jump-table-to-segment mapping.
- [ ] Local Mac MD/docs searched for byte-level CODE entry conventions.
- [ ] MPW Asm CODE 0 fields and nonzero CODE headers inventoried.
- [ ] Orphan code/data island examples sampled and recorded with offsets.
- [ ] Existing Mac parser/listing/project payload paths traced.
- [ ] 012 blocker wording checked before implementation.

## Research Review

- [ ] Second pass checked every accepted fact against citations.
- [ ] Second pass checked parser assertions include reason and standard
  interpretation.
- [ ] Segment/routine map distinguishes accepted metadata from candidate entry
  offsets.
- [ ] Relocation/fixup gaps are deferred or placeholder output, not accepted.
- [ ] Orphan code islands are surfaced with structured evidence.
- [ ] Parser output passes 018-008 fact-reference validation.
- [ ] Proposal 012 updated with exact accepted/candidate/deferred state.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Mac CODE KB facts updated with citations or parser assertions.
- [ ] CODE 0 jump-table/segment map is exposed where evidence supports it.
- [ ] Byte-entry rule is accepted only if cited/asserted; otherwise remains
  candidate/deferred with evidence.
- [ ] Relocation/fixup semantics are accepted only if cited/asserted; otherwise
  structured deferred/placeholder output exists.
- [ ] Orphan code/data islands are not dropped.
- [ ] MPW Asm fixture tests cover segment/routine mapping and orphan evidence.
- [ ] Parser fact output passes 018-008 validation.
- [ ] Mac target artifact regenerated if output changes.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Relevant Mac parser/listing/project tests pass.
- [ ] Post-commit review found no unresolved worthwhile findings.
