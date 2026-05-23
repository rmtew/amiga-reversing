# 018-010: Mac OS Multi-CODE Resource Rendering And Navigation

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS multi-CODE source rendering, navigation payloads, and
  target artifact usefulness
- Blocked by: `018-009`
- Current proposal state: Mac parser output exposes CODE 0 jump-table spans,
  nonzero CODE segment map entries, candidate routine offsets, orphan ranges,
  and deferred relocation/fixup placeholders. The committed MPW `Asm` artifact
  still renders only one selected CODE resource listing in detail.
- Desired proposal state after this issue: every CODE resource in the Mac
  target can be inspected as a structured source/navigation subview, with
  CODE 0, nonzero CODE segment metadata, candidate routine entries, orphan
  ranges, and deferred relocation state visible without pretending unresolved
  byte-entry or relocation semantics are accepted.

## Knowledge Delta

- Adds: rendering/navigation obligations for multi-CODE Mac targets.
- Changes: Mac output becomes a resource-oriented project view rather than a
  single selected CODE listing plus summary comments.
- Replaces: single-CODE selected-resource rendering as the only detailed Mac
  source view.
- Deletes: no candidate/deferred evidence; unresolved areas must stay visible.
- Leaves out of scope: byte-for-byte MPW roundtrip, accepted relocation/fixup
  interpretation, accepted byte-entry validation, complete source recovery, and
  Amiga/Atari parser migration.

## Default Behavior

- Existing accepted/candidate/deferred fact states from 018-009 remain
  unchanged.
- `movea.l (a7)+,a0` remains candidate-only.
- Relocation/fixup output remains deferred-only unless a separate KB issue
  validates it.
- Multi-CODE rendering must not produce Amiga-only source syntax for Mac paths.
- UI/source payload changes should be additive and structured; do not hide
  existing evidence to make output look cleaner.

## Evidence Standard

- Each rendered CODE resource/subview must carry source provenance:
  resource id, name, payload range/hash, CODE kind, KB record id, fact ids,
  fact statuses, parser-use values, and unsupported/deferred reasons.
- CODE 0 should render as jump-table/application metadata, not as raw m68k code.
- Nonzero CODE resources should render:
  - accepted segment-header/jump-table-span metadata;
  - candidate routine entries where available;
  - candidate/deferred code/data/orphan ranges;
  - deferred relocation/fixup state;
  - a bounded disassembly preview or structured placeholder when full listing is
    still unsupported.
- Navigation rows/symbols must distinguish accepted metadata anchors from
  candidate routine/code anchors.
- Parser output fact ids/status/parser-use must pass 018-008 validation.

## Implementation Slice

- Extend Mac project payloads so every CODE resource has a structured detail
  object suitable for UI/source navigation, not just the selected CODE segment.
- Extend listing/artifact generation so the committed MPW `Asm` artifact
  includes useful per-CODE sections or subviews for all CODE resources:
  metadata, candidate routines, orphan ranges, deferred relocation status, and
  listing preview/placeholder.
- Expose CODE 0 jump-table entries and candidate routine entries as navigable
  anchors/rows where current UI payload conventions support it.
- Preserve existing selected CODE 1 listing behavior, but make it one subview
  within the full CODE-resource project view.
- Add tests proving:
  - every CODE resource appears in the project payload/detail model;
  - every CODE resource appears in the committed target artifact;
  - CODE 0 is rendered as metadata/jump table, not disassembled as ordinary
    code;
  - candidate routine anchors are labelled candidate, not accepted;
  - deferred relocation/fixup state remains visible;
  - parser fact output passes 018-008 validation.
- Update Proposal 012 and Proposal 018 notes with the new rendering/navigation
  state.

## Research Completion Standard

Record trace blocks for:

- current web/source payload routes used for Mac projects;
- existing target artifact generation path and selected CODE listing path;
- current UI expectations for navigation rows, symbols, or anchors;
- the chosen shape for per-CODE detail objects;
- any CODE resource that cannot receive a preview and why.

## Research Coverage

- [x] Current Mac project payload shape traced.
- [x] Current Mac listing/artifact route traced.
- [x] Existing UI navigation/symbol payload conventions checked.
- [x] MPW `Asm` CODE resource inventory checked against current parser output.
- [x] CODE 0 metadata rendering requirements checked.
- [x] Nonzero CODE preview/placeholder policy selected.
- [x] 012/018 blocker wording checked before implementation.

## Research Review

- [x] Second pass checked every CODE resource appears in payload/artifact.
- [x] Second pass checked CODE 0 is not rendered as ordinary code.
- [x] Candidate routine/code anchors are not labelled accepted.
- [x] Deferred relocation/fixup state remains visible in every relevant subview.
- [x] Full selected CODE 1 listing still works.
- [x] Parser output passes 018-008 fact-reference validation.
- [x] Proposal 012/018 docs updated with exact accepted/candidate/deferred
  state.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Per-CODE resource detail model added to Mac project payloads.
- [x] All CODE resources are represented in source/navigation output.
- [x] CODE 0 renders as metadata/jump table.
- [x] Nonzero CODE resources expose segment metadata, candidate routines,
  orphan ranges, and deferred relocation state.
- [x] Selected CODE 1 detailed listing remains available.
- [x] Candidate/deferred facts are not promoted to accepted output.
- [x] MPW `Asm` target artifact regenerated if output changes.
- [x] Parser fact output passes 018-008 validation.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Relevant Mac parser/listing/project/web tests pass.
- [x] Final review found no unresolved worthwhile findings.

## Trace Blocks

Current Mac project payload shape:

```text
amiga_reversing/disasm/macos_project_payload.py
  build_macos_project_payload(...)
    source_view
    binary_container_view
      code_resources
      code_segment_map
      code_resource_details
      navigation.groups[macos-code-resources, macos-code-anchors]
      selected_code_segment.listing
```

Current Mac listing/artifact route:

```text
amiga_reversing/disasm/macos_target_artifact.py
  render_macos_example_asm(...)
    builds the committed targets/macos_hfs_mpw_gm/.../asm.s artifact from
    build_macos_project_payload(...)

amiga_reversing/disasm/server.py
  existing Mac listing flow continues to use the selected CODE 1 listing route.
```

Per-CODE detail object shape:

```json
{
  "resource_type": "CODE",
  "id": 1,
  "role": "code_segment",
  "payload_size": 29024,
  "payload_sha256": "...",
  "code_kind": "code_segment",
  "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
  "fact_id": "macos.resource_fork.code_resources.accepted",
  "fact_status": "validated",
  "parser_use": "accepted_parser_output",
  "segment_map": {},
  "code_layout": [],
  "orphan_ranges": [],
  "relocation_fixups": {},
  "navigation_anchors": [],
  "listing": {}
}
```

Preview/placeholder policy:

```text
CODE 0:
  listing.kind = metadata
  available = false
  reason = CODE 0 is jump-table/application metadata, not ordinary m68k code

selected CODE 1:
  listing.kind = full_listing
  available = true
  route = listing

other nonzero CODE resources:
  listing.kind = structured_placeholder
  available = false
  reason = full per-resource listing deferred until relocation/source-boundary
           context is represented
```

## Completion Evidence

```text
uv run ruff check amiga_reversing\disasm\macos_project_payload.py amiga_reversing\disasm\macos_target_artifact.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py
  All checks passed

uv run python -m pytest tests\test_macos_project_payload.py tests\test_macos_target_artifact.py -q
  7 passed

uv run python -m amiga_reversing.tools.platform_executable_formats validate
  passed

uv run python -m amiga_reversing.tools.validate_018_issues
  passed

uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_asm_container.py tests\test_platform_executable_formats.py -q
  38 passed

cmd /c src\build.bat
  passed
```
