# Platform Executable Format Knowledge

This document is the human-readable authority for
`knowledge/platform_executable_formats.json`. The JSON is the executable
authority used by tests and later generated checks; this document explains the
model, source policy, and current limits.

Proposal 018 owns this knowledge area. Platform parsers must not promote
standard executable/container facts from local heuristics into accepted parser
behavior. Accepted parser output requires either a `validated` fact or a
`parser_asserted` fact with assertion context.

## Canonical Files

```text
docs/platform-executable-formats.md
knowledge/platform_executable_formats.schema.json
knowledge/platform_executable_formats.json
tests/test_platform_executable_formats.py
```

`amiga_reversing.tools.platform_executable_formats` performs local validation
without adding a third-party JSON Schema dependency.

## Record Shape

Each record describes one platform executable/container archetype:

```text
platform_id
format_id
archetype_id
producer_variant_scope
applies_to
identification
containers
regions
relocations
symbols
bss
loader_model
runtime_model
analysis_model
renderer_expectations
entrypoints
facts
unknowns / conflicts / deferred / unsupported
required_parser_behavior
```

The model deliberately separates file structure, loader behavior, runtime entry
state, analysis seeds, and renderer obligations. Target-specific analysis may
use platform facts, but it must not become the place where standard executable
format rules are invented.

## Fact States

`validated`
: Directly supported by allowed cited sources. Accepted parser output may use
  these facts.

`parser_asserted`
: A project-maintained standard interpretation when direct documentation is
  indirect or unavailable. Accepted parser output may use these only when the
  record includes reason, citation context, standard interpretation, and review
  status.

`candidate`
: Research/report evidence only. Candidate facts may produce candidate ranges,
  reports, or review items, but not accepted code/data/entry classification.

`deferred`
: Known required area that is not yet implemented or cited enough. Parser output
  must fail closed, emit a placeholder, or block closeout as the record says.

`unsupported`
: Intentionally outside current scope. Parsers may ignore safely or emit a
  placeholder only when the record says so.

## Source Policy

Allowed source types:

```text
old_out_of_print
modern_compatible
project_observed
parser_asserted
```

Fixture bytes and current parser behavior are `project_observed`. They can
support candidates and sometimes parser assertions, but fixture bytes alone do
not validate a general platform rule.

Excluded inputs:

```text
modern incompatible sources
uncited generalization
large copied source text
undocumented facts marked validated
```

## Parser Use

Every fact-like item has a `parser_use`:

```text
accepted_parser_output
candidate_only
deferred_only
unsupported_only
```

The validator rejects `accepted_parser_output` unless the fact status is
`validated` or `parser_asserted`. Candidate, deferred, and unsupported facts are
therefore mechanically separated from accepted parser output.

## Entrypoints

Entrypoints use explicit typed vocabulary:

```text
file_entrypoint
segment_entrypoint
runtime_entrypoint
exported_entrypoint
callback_entrypoint
analysis_seed_entrypoint
```

The current Mac `movea.l (a7)+,a0` boundary is represented only as an
`analysis_seed_entrypoint` with `candidate_only` parser use.

## Thin Mac Proof Record

The first KB record is
`macos.hfs_resource_fork.code_resources.thin_proof`.

It exists only to prove the schema can represent the Proposal 012 blocker:

```text
platform: macos
format: macos.hfs_resource_fork.code_resources
archetype: macos.application_code_resources
CODE 0: candidate metadata/jump-table role
nonzero CODE resources: candidate segment-resource role
movea.l (a7)+,a0 boundary: candidate analysis seed only
```

The record intentionally contains no accepted Mac executable facts. Segment
Loader behavior, A5 world, relocation/fixup handling, jump-table semantics, and
runtime entry rules remain deferred to 018-002 and 018-003.

## Mac Citation Packets

018-002 records source evidence in top-level `citation_packets`. These packets
are not accepted parser records. They are evidence inputs for 018-003.

Current Mac packets:

```text
macos.packet.hfs_resource_fork.application_code
macos.packet.segment_loader.code_resources
macos.packet.nonzero_code.segment_header
macos.packet.code0.jump_table_metadata
macos.packet.code1.main_startup
macos.packet.a5_jump_table_offset
macos.packet.mpw_link_application_output
macos.packet.mpw_asm_fixture_code_inventory
macos.packet.movea_stack_a0_boundary
macos.packet.segment_relocation_fixups.deferred
```

Validated packets cite local old out-of-print markdown sources. Project-observed
packets stay candidate-only. The current `movea.l (a7)+,a0` boundary remains a
candidate packet because no cited Segment Loader or MPW runtime startup source
currently explains that exact instruction as the accepted runtime entry rule.

## Trace Blocks

### Existing Knowledge Conventions

Checked:

```text
knowledge/mac_os.json
knowledge/amiga_hunk_file.json
knowledge/platform_source_inventory.json
tests/test_platform_kb.py
```

Observed convention:

```text
KB files keep source/provenance metadata near facts.
Tests validate vocabularies and debt conditions with focused Python assertions.
Existing executable-format files are data-specific; 018 adds the shared
cross-platform authority above them.
```

### Generated Metadata Conventions

Checked:

```text
src/generated/
tests/test_macos_c_backend.py
tests/test_macos_asm_container.py
docs/proposals/018-platform-executable-format-knowledge.md
```

Observed convention:

```text
Generated/runtime consumers should use structured facts or generated tables.
018-001 does not generate C metadata yet; it fixes the schema and validation
surface later issues can consume.
```

### Citation And Provenance Conventions

Checked:

```text
knowledge/mac_os.json
docs/macos-file-structure.md
docs/macos-targets.md
docs/proposals/012-classic-mac-os-m68k-platform.md
```

Observed convention:

```text
Local markdown and JSON records cite project-local paths, pages, sections, or
metadata files. The executable-format KB follows that path/source-id pattern and
keeps citation context short.
```

### JSON Validation Pattern

Checked:

```text
tests/test_platform_kb.py
tests/test_validate_017_issues.py
pyproject.toml
```

Decision:

```text
No project dependency on jsonschema exists. 018-001 adds a schema document plus
a small project validator that checks the required vocabularies, record shape,
citations, parser assertions, and candidate/accepted parser-use boundary.
```

### Mac Proof Scope

Checked:

```text
docs/proposals/012-classic-mac-os-m68k-platform.md
docs/proposals/018-platform-executable-format-knowledge.md
docs/macos-file-structure.md
ext/macos_tools/mpw_gm/asm_code_resources.json
tests/test_macos_c_backend.py
```

Decision:

```text
The proof record is deliberately candidate-only. It names the observed CODE 0,
nonzero CODE resources, and movea.l boundary, but blocks accepted parser closeout
until cited Segment Loader facts exist.
```

### Mac Citation Packet Research

Checked:

```text
ext/docs_macos/Inside_Macintosh_Volume_I_1985.md source-page 117
ext/docs_macos/Inside_Macintosh_Volume_II_1985.md source-pages 64, 70-71
ext/docs_macos/MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md source-pages 37-39
ext/docs_macos/Programming_With_Macintosh_Programmers_Workshop_1987.md source-page 69
docs/macos-initial-analysis-research.md
ext/macos_tools/mpw_gm/source.json
ext/macos_tools/mpw_gm/asm_code_resources.json
```

Accepted packet scope:

```text
HFS file/resource fork application-code relationship
Segment Loader CODE resource model
nonzero CODE segment-header layout
CODE 0 jump-table/A5 metadata
CODE 1 main-segment startup relationship
A5 jump-table offset relationship
MPW Asm/Link object-to-application workflow and Link progress segment counts
```

Candidate/deferred packet scope:

```text
MPW Asm fixture CODE inventory: project-observed candidate only.
movea.l (a7)+,a0 boundary: project-observed candidate only.
Segment relocation/fixup semantics: deferred pending direct citations.
```

## Accepted Mac Record

018-003 adds
`macos.hfs_resource_fork.code_resources.mpw_application` as the first accepted
Mac executable-format record. It promotes only facts backed by validated
018-002 packets:

```text
HFS application resource-fork code relationship
Segment Loader CODE resource container model
CODE 0 jump-table/A5 metadata
nonzero CODE four-byte segment header
CODE 1 main-segment startup relationship
A5 jump-table offset relationship
MPW Link object-to-application output and progress segment counts
```

The record deliberately does not accept the current byte-entry heuristic:

```text
macos.code_resource.movea_stack_a0.boundary.candidate
macos.code_resource.movea_stack_a0.entry_candidate
```

Relocation/fixup semantics and byte-level executable-entry boundaries remain
deferred. Parser/listing code must not treat those areas as accepted until later
KB-backed migration work consumes or replaces them.

## Guardrail Report

018-004 adds a local guardrail report:

```text
python -m amiga_reversing.tools.platform_executable_formats guardrails
```

The report separates KB-backed records from report-only records and lists fact
ids by accepted, candidate-only, deferred, and unsupported parser use. Current
state:

```text
kb_backed_records:
  macos.hfs_resource_fork.code_resources.mpw_application

report_only_records:
  macos.hfs_resource_fork.code_resources.thin_proof
  amiga.hunk.load_file.basic_backfill
  atari_st.prg.gemdos_basic_backfill
```

The validator fails if a candidate such as
`macos.code_resource.movea_stack_a0.boundary.candidate` is marked as accepted
parser output.

## Mac Parser And Listing Consumption

018-005 wires the accepted Mac record into the current C/Python/listing surface:

```text
src/platform_macos_resource.c
src/platform_file_lib.c
amiga_reversing/disasm/macos_listing_source.py
amiga_reversing/disasm/macos_target_artifact.py
targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s
```

Accepted structural parser output now carries fact ids and parser use:

```text
CODE 0 metadata -> macos.code_resource.0.jump_table_metadata / validated
nonzero CODE segment header -> macos.code_resource.nonzero.segment_header / validated
```

The observed `movea.l (a7)+,a0` byte boundary is still rendered for the MPW Asm
starter target, but only as `candidate_code` with
`macos.code_resource.movea_stack_a0.boundary.candidate`. Missing byte-entry
evidence is emitted as deferred. The committed listing labels fact/status fields
and still omits Amiga raw `SECTION code,code`.

018-008 adds parser-output validation over actual Mac summaries and payloads.
Every emitted `kb_record_id`, `fact_id`, `fact_status`, and `parser_use` must
resolve to an item in the referenced KB record with matching status/parser-use
semantics. Citation packet `fact_candidate_id` values are not valid parser
facts unless the same id exists as a KB record item.

Current Mac emitted ids:

```text
macos.hfs_resource_fork.code_resources.mpw_application
macos.resource_fork.code_resources.accepted
macos.code_resource.0.jump_table_metadata
macos.code_resource.nonzero.segment_header
macos.jump_table.entries.accepted
macos.code_resource.segment_jump_table_span.accepted
macos.code_resource.jump_table.routine_offsets.candidate
macos.code_resource.movea_stack_a0.boundary.candidate
macos.code_resource.orphan_layout_ranges.candidate
macos.code_resource.byte_entry_rule.unknown
macos.segment_loader.relocation_fixups.deferred
```

`macos.segment_loader.code_resources` remains only a citation-packet candidate
id and must not be emitted as parser fact output.

018-009 extends the Mac parser/listing output without promoting the byte-entry
heuristic:

```text
CODE 0 now emits a jump_table object with start=16, byte length, eight-byte
entry size, and entry count under macos.jump_table.entries.accepted.

resource_fork.code_segment_map now emits every nonzero CODE resource's
accepted segment-header jump-table span under
macos.code_resource.segment_jump_table_span.accepted.

Where CODE 0 bytes and segment headers support it, jump-table routine offsets
are emitted as candidate routine_entry_candidates under
macos.code_resource.jump_table.routine_offsets.candidate.

Bytes outside accepted metadata and candidate code ranges are emitted as
orphan_ranges. Prefix bytes before the current movea.l boundary are candidate
data islands under macos.code_resource.orphan_layout_ranges.candidate; missing
entry evidence remains deferred under macos.code_resource.byte_entry_rule.unknown.

Every CODE resource carries a relocation_fixups placeholder under
macos.segment_loader.relocation_fixups.deferred. No relocation/fixup output is
accepted yet.
```

018-010 makes that structure visible as source/navigation output:

```text
binary_container_view.code_resource_details
binary_container_view.navigation.groups[macos-code-resources]
binary_container_view.navigation.groups[macos-code-anchors]
targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s
```

Every CODE resource has a detail subview with resource id/name, payload
size/hash, code kind, KB fact identity, layout ranges, orphan ranges,
relocation/fixup state, navigation anchors, and listing availability. CODE 0 is
metadata/jump-table output. Selected CODE 1 keeps the full listing route. Other
nonzero CODE resources expose structured placeholders until relocation and
source-boundary context can justify fuller previews.

Trace blocks for 018-009:

```text
Local docs searched:
  ext/docs_macos/Inside_Macintosh_Volume_II_1985.md source-pages 70-72
  docs/proposals/012-classic-mac-os-m68k-platform.md blocked/future scope

Accepted citations:
  source-page 70: jump table entries are eight bytes, grouped contiguously by
  segment; segment headers contain first jump-table-entry offset and count.
  source-page 71: CODE 0 contains A5 sizes, jump-table length, jump-table
  offset, and the jump table; the first entry loads CODE 1.

Deferred/candidate state:
  No local citation was found that validates movea.l (a7)+,a0 as the general
  byte-level CODE entry rule. It remains candidate-only.
  Relocation/fixup interpretation remains deferred and is now emitted as a
  structured placeholder instead of only prose unsupported state.
```

### Representative Amiga And Atari Needs

Checked:

```text
knowledge/amiga_hunk_file.json
knowledge/atari_st_prg_file.json
docs/proposals/018-platform-executable-format-knowledge.md
```

Decision:

```text
The schema has shared fields for signatures, containers, regions, relocations,
symbols, BSS, loader/runtime/analysis model, renderer expectations, typed
entrypoints, and unknown/deferred/unsupported areas. 018-006 uses that shape for
first report-only Amiga/Atari backfill records.
```

## Amiga/Atari Backfill Register

018-006 adds two schema-valid report-only records:

```text
amiga.hunk.load_file.basic_backfill
atari_st.prg.gemdos_basic_backfill
```

They cite the existing normalized KB files:

```text
knowledge/amiga_hunk_file.json
knowledge/atari_st_prg_file.json
```

Both records set `kb_backed: false`; they do not change parser behavior and do
not authorize accepted parser output.

Backfill-required parser assumptions:

```text
Amiga HUNK:
- accepted runtime entry policy for imported HUNK files
- LoadSeg edge cases and overlay/loader variants
- relocation record grouping/preservation policy
- object/library HUNK support boundaries

Atari ST PRG:
- accepted GEMDOS runtime entry/basepage state
- TEXT-start analysis seed vs accepted runtime entrypoint
- relocation-stream EOF and zero-byte terminator variants
- relocation flag and program flag parser/rendering policy
```

## Amiga HUNK Accepted Reference Slice

018-011 promotes a narrow Amiga HUNK reference slice to `parser_asserted`
record items while keeping `amiga.hunk.load_file.basic_backfill`
`kb_backed: false`.

Accepted reference facts:

```text
amiga.hunk.header.identifies_load_file.accepted
amiga.hunk.unit_library.containers.accepted
amiga.hunk.code_data_bss.sections.accepted
amiga.hunk.bss.size_only.accepted
```

Checked:

```text
knowledge/amiga_hunk_file.json
src/platform_amiga_hunk.c
docs/proposals/018-platform-executable-format-knowledge.md
```

The parser-asserted facts cite the normalized HUNK KB and carry assertion
context. Current parser assumptions, entry policy, overlay variants, and full
object/library importer behavior remain candidate or deferred.

## Atari ST PRG Accepted Reference Slice

018-012 promotes a narrow Atari ST PRG/TOS/TTP reference slice to
`parser_asserted` record items while keeping
`atari_st.prg.gemdos_basic_backfill` `kb_backed: false`.

Accepted reference facts:

```text
atari_st.prg.magic_601a.accepted
atari_st.prg.container_sequence.accepted
atari_st.prg.text_data_bss_regions.accepted
atari_st.prg.text_data_loaded_image.accepted
```

Checked:

```text
knowledge/atari_st_prg_file.json
src/platform_atari_st.c
docs/proposals/018-platform-executable-format-knowledge.md
```

Runtime/basepage entry state and relocation terminator variants remain deferred;
the TEXT-start parser analysis seed is still candidate-only.

## Generated C Fact Table

018-013 extends `src/scripts/generate_platform_format_runtime.py` to generate:

```text
src/generated/platform_executable_formats.h
src/generated/platform_executable_formats.c
```

The generated table is derived from
`knowledge/platform_executable_formats.json` and preserves record id, item id,
section, status, and parser use. Tests regenerate into a temporary directory and
compare the committed generated files, so stale generated output fails.

Current Mac C fact string literals in `src/platform_file_lib.c` and
`src/platform_macos_resource.c` are deliberately left unchanged in this issue:
018-013 adds the generated drift surface without changing parser output or Mac
CODE rendering/navigation behavior.

## Mac Non-CODE Resource Metadata Inventory

018-014 records non-CODE resource metadata as candidate-only inventory:

```text
macos.resource_fork.non_code_metadata.inventory.candidate
macos.packet.mpw_asm.non_code_resource_metadata_inventory
```

Checked:

```text
ext/macos_tools/mpw_gm/asm_code_resources.json
ext/macos_includes/mpw_gm/inventory.json
ext/docs_macos/Inside_Macintosh_Volume_III_1985.md source-pages 17-20
```

The committed MPW Asm resource extraction contains only CODE resources. The
requested non-CODE type names `acur`, `CURS`, `cmdo`, and `vers` therefore stay
candidate/deferred for this target; no non-CODE resource is presented as
executable CODE.

## MPW Object And Library Packet

018-015 adds MPW object/library citation packets:

```text
macos.packet.mpw.object_modules
macos.packet.mpw.object_libraries
macos.packet.mpw.object_library_format.deferred
```

Checked:

```text
ext/docs_macos/Programming_With_Macintosh_Programmers_Workshop_1987.md source-pages 565-570
ext/macos_includes/mpw_gm/inventory.json
```

The accepted packet scope covers MPW object modules, object-file main-entry
metadata, library creation from object files, and Link treating object files and
libraries as module inputs. Byte-level object/library container layout remains
deferred.

## Source Citation Audit

018-016 audited accepted and parser-asserted executable-format facts. The weak
Mac renderer rule
`macos.renderer.accepted_vs_candidate_labeling.accepted` is now
`parser_asserted` rather than project-observed validated, because it is a
project renderer contract derived from Proposal 018 fact-state policy.

Project-observed-only general claims remain candidate or deferred. The new
Amiga/Atari accepted reference slices are parser assertions with reason,
citation context, standard interpretation, and review status.

## Mac Nonselected CODE Preview Windows

018-017 adds bounded preview descriptors for non-selected nonzero Mac CODE
resources when the current C-backed classifier exposes a `candidate_code`
range.

Preview policy:

```text
CODE 0: metadata/jump-table only; no preview.
Selected CODE 1: existing full listing route.
Other nonzero CODE resources with candidate_code ranges: candidate preview,
bounded to the classified candidate range and capped at 64 bytes.
Other nonzero CODE resources without candidate_code ranges: structured
placeholder with the classifier evidence explaining why no preview is safe.
```

Preview rows inherit the candidate fact
`macos.code_resource.movea_stack_a0.boundary.candidate` and
`candidate_only` parser use. Relocation/fixup interpretation remains deferred
through `macos.segment_loader.relocation_fixups.deferred`; preview windows do
not promote byte-entry or relocation semantics to accepted output.

## Mac CODE Preview Web UI

018-018 makes those Mac CODE detail records browser-visible in the normal
project page. The web UI now consumes `code_resource_details` and
`preview_windows` instead of showing only raw CODE inventory plus the selected
listing panel.

Browser-visible state:

```text
CODE 0: metadata/jump-table-only detail row, no preview.
Selected CODE 1: full_listing route remains visible and the selected listing
panel still renders through the existing listing path.
Non-selected candidate previews: visible bounded preview rows labelled
candidate/candidate_only.
No-preview resources: visible structured reason from the classifier.
Relocation/fixup state: visible deferred/deferred_only state.
```

CDP verification opens the rendered Mac project page and checks the visible
CODE 0, CODE 1, candidate preview, no-preview, and deferred relocation text in
the browser DOM.

## Mac Candidate Preview Decode Rows

018-019 changes non-selected CODE preview rows from unconditional data-word
rendering to bounded decode-first rendering.

```text
Input: existing candidate_code preview byte window only.
Decode path: temporary raw local-offset binary through the same shared m68k
listing backend used by the selected Mac CODE adapter.
Decoded rows: instruction/data rows with offset, bytes, text, range/fact state,
decode_status, and row_kind.
Fallback rows: dc.w/dc.b rows only when the preview is too short, decode fails,
or no instruction row is produced; fallback_reason is visible.
```

All rows keep the candidate fact
`macos.code_resource.movea_stack_a0.boundary.candidate` and `candidate_only`
parser use inherited from the preview range. Relocation/fixup state remains
visible as deferred-only state; decoded preview rows do not accept byte-entry or
relocation/fixup semantics.

## Mac Non-CODE Resource Metadata UI

018-023 adds browser-visible non-CODE resource metadata rows under
`binary_container_view.resource_fork.non_code_resource_details`.

```text
Source: C-backed resource_fork.types inventory.
Rows: resource type, count, candidate fact state, parser_use, payload decode
status, and inventory evidence.
Fact: macos.resource_fork.non_code_metadata.inventory.candidate.
Decode status: unsupported for payload semantics; no non-CODE payload decoding
or executable interpretation is implied.
```

The web UI renders these rows separately from CODE resources so CODE 0 metadata,
selected CODE 1 listing, and non-selected CODE previews keep their existing
behavior.

## Mac CODE 0 Jump-Table Drilldown

018-024 adds structured CODE 0 jump-table rows to
`binary_container_view.code_resource_details[CODE 0].jump_table_rows`.

```text
Accepted layout fields:
  entry_index, CODE 0 payload offset, entry size, and
  macos.jump_table.entries.accepted fact state.
Candidate target fields:
  target CODE resource, routine offset, jump-table offset, and
  macos.code_resource.jump_table.routine_offsets.candidate fact state.
```

CODE 0 remains metadata/jump-table-only. The drilldown separates accepted entry
layout from candidate target/routine interpretation, and the web/artifact views
do not decode CODE 0 as ordinary m68k code.

## Mac Relocation/Fixup Research Packet

018-021 reviewed local old/out-of-print Mac and MPW sources for Segment Loader
relocation/fixup evidence.

Checked sources:

```text
ext/docs_macos/Inside_Macintosh_Volume_II_1985.md
ext/docs_macos/Inside_Macintosh_Volume_III_1985.md
ext/docs_macos/MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md
ext/docs_macos/Programming_With_Macintosh_Programmers_Workshop_1987.md
knowledge/platform_executable_formats.json
```

Evidence classified:

```text
validated/current:
- Segment Loader loads CODE resources and updates jump-table state.
- CODE 0 and jump-table metadata remain accepted where already cited.

candidate:
- Segment Loader loading uses Resource Manager and Memory Manager, and a
  segment/package load can cause heap compaction and block relocation.

deferred:
- On-disk CODE relocation/fixup byte layout.
- Rules for applying fixups to preview/listing bytes.
- Any accepted relocation-aware roundtrip or control-flow claim.
```

The KB now records
`macos.packet.segment_loader.memory_relocation_context` as candidate evidence
and keeps `macos.segment_loader.relocation_fixups.deferred` deferred. Parser,
payload, artifact, and web output are unchanged.

## Mac Source-To-CODE Mapping Research

018-022 reviewed MPW source/build metadata and local documentation for
source-to-CODE mapping evidence.

Checked sources:

```text
ext/macos_tools/mpw_gm/source.json
ext/macos_tools/mpw_gm/asm_code_resources.json
ext/macos_includes/mpw_gm/source.json
ext/macos_includes/mpw_gm/inventory.json
docs/macos-initial-analysis-research.md
ext/docs_macos/MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md
ext/docs_macos/Programming_With_Macintosh_Programmers_Workshop_1987.md
```

Evidence classified:

```text
validated:
- MPW Asm creates object output and MPW Link creates a standalone program.
- MPW Link reports segment and jump-table-entry counts.
- MPW source segment names are used as CODE resource names generated by Link.

candidate/project-observed:
- Sample, Count, and Memory remain good future semantic fixtures.
- MPW/Tools/Asm remains the current real executable/container fixture.

deferred:
- Mapping the available Sample/Count/Memory sources to MPW/Tools/Asm CODE
  resources. They are different programs/fixtures.
- Source-to-CODE byte correspondence, symbol maps, and linker reconstruction.
```

The KB now records
`macos.packet.mpw.source_segment_to_code_resource_names` as validated source
mapping evidence. The current project payload boundary remains
`source_segments_map_to_observed_code_resources: false`.

## Current Limits

018-001 does not change parser or renderer behavior.

The Mac proof record is not enough to close Proposal 012. It is a schema gate
and guardrail: later work can add citation packets, accepted records, generated
checks, and parser/listing migration without changing the authority shape.
