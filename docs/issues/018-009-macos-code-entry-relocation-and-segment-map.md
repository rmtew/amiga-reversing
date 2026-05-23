# 018-009: Mac OS CODE Entry, Relocation, And Segment Map

Status: completed

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

- [x] Local Mac MD/docs searched for Segment Loader relocation/fixup semantics.
- [x] Local Mac MD/docs searched for CODE 0 jump-table-to-segment mapping.
- [x] Local Mac MD/docs searched for byte-level CODE entry conventions.
- [x] MPW Asm CODE 0 fields and nonzero CODE headers inventoried.
- [x] Orphan code/data island examples sampled and recorded with offsets.
- [x] Existing Mac parser/listing/project payload paths traced.
- [x] 012 blocker wording checked before implementation.

## Research Review

- [x] Second pass checked every accepted fact against citations.
- [x] Second pass checked parser assertions include reason and standard
  interpretation.
- [x] Segment/routine map distinguishes accepted metadata from candidate entry
  offsets.
- [x] Relocation/fixup gaps are deferred or placeholder output, not accepted.
- [x] Orphan code islands are surfaced with structured evidence.
- [x] Parser output passes 018-008 fact-reference validation.
- [x] Proposal 012 updated with exact accepted/candidate/deferred state.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Mac CODE KB facts updated with citations or parser assertions.
- [x] CODE 0 jump-table/segment map is exposed where evidence supports it.
- [x] Byte-entry rule is accepted only if cited/asserted; otherwise remains
  candidate/deferred with evidence.
- [x] Relocation/fixup semantics are accepted only if cited/asserted; otherwise
  structured deferred/placeholder output exists.
- [x] Orphan code/data islands are not dropped.
- [x] MPW Asm fixture tests cover segment/routine mapping and orphan evidence.
- [x] Parser fact output passes 018-008 validation.
- [x] Mac target artifact regenerated if output changes.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Relevant Mac parser/listing/project tests pass.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Local evidence checked: `Inside_Macintosh_Volume_II_1985.md` source-pages
  70-72 for jump-table entries, nonzero segment headers, CODE 0 metadata, CODE
  1 startup, and `_LoadSeg` stack input; Proposal 012 blocker/future scope for
  deferred relocation/fixup and byte-entry state.
- KB/doc updates: `knowledge/platform_executable_formats.json` and
  `docs/platform-executable-formats.md` now include accepted
  `macos.code_resource.segment_jump_table_span.accepted`, candidate
  `macos.code_resource.jump_table.routine_offsets.candidate`, candidate
  `macos.code_resource.orphan_layout_ranges.candidate`, and deferred
  relocation placeholder output under
  `macos.segment_loader.relocation_fixups.deferred`.
- Parser/project/artifact updates: `src/platform_file_lib.c` emits CODE 0
  jump-table spans, `resource_fork.code_segment_map`, candidate routine entry
  offsets where CODE 0 supports them, `orphan_ranges`, and deferred
  `relocation_fixups`; `macos_project_payload.py` passes those fields through;
  `macos_target_artifact.py` renders them in the committed MPW `Asm` artifact.
- Preserved candidate/deferred state: `movea.l (a7)+,a0` remains
  `candidate_only`; byte-level entry and relocation/fixup interpretation are
  not accepted.
- Tests/validation run:
  `cmd /c src\build.bat`;
  `uv run python -m amiga_reversing.tools.platform_executable_formats validate`;
  `uv run python -m amiga_reversing.tools.validate_018_issues`;
  `uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_asm_container.py tests\test_platform_executable_formats.py -q`
  passed with 33 tests; `uv run ruff check` on changed Python/test files
  passed; `git diff --check` passed.
