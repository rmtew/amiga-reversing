# Proposal 018: Platform Executable Format Knowledge

Status: open. This proposal defines the single top-down cited executable and
object-format authority that Mac OS, Amiga, and Atari ST parsers should use
before target-specific analysis guesses at code/data boundaries.

## Purpose

Amiga, Atari ST, and Classic Mac OS all have fixed retro executable/container
formats. They are no longer moving targets. The project should capture their
standard file structures as cited knowledge, then generate or validate parser
behavior from that knowledge.

The immediate blocker is Proposal 012: Mac CODE rendering was advanced with a
pattern heuristic for `movea.l (a7)+,a0`. That is not enough. The Mac parser
needs cited Segment Loader, CODE resource, A5 world, jump-table, relocation,
and entrypoint facts before its rendered source can be treated as correct.

018 is knowledge/schema first and parser implementation second. Parser work
must consume or validate against the KB; it must not invent accepted executable
rules directly in target or renderer code.

## Authority Shape

018 has two authority forms:

- `docs/platform-executable-formats.md` is the human-readable narrative
  authority: concepts, citations, parser assertions, conflicts, examples, and
  known limits.
- `knowledge/platform_executable_formats.schema.json` and
  `knowledge/platform_executable_formats.json` are the executable authority for
  validation, generated parser checks, and code generation.

The JSON KB cites source documents and fact ids explained by the markdown. The
markdown does not replace structured facts; it explains the interpretation and
why any parser assertion is acceptable.

## Target Knowledge

Each platform executable-format record should describe:

- format identifiers and file/container signatures;
- container nesting and fork/resource/object relationships;
- code, data, bss, relocation, symbol, and metadata regions;
- standard entrypoint rules by file type;
- loader/runtime metadata and fixup semantics;
- standard compiler/linker outputs for the platform;
- citations for every accepted fact;
- parser assertions only when a document is indirect, with the evidence and
  standard interpretation recorded.

The shared schema should be one top-level model with platform extension blocks,
not unrelated per-platform schemas. Core records contain:

```text
platform
format_id
archetype_id
producer / variant / applies_to
identification
containers
regions
relocations
symbols
entrypoints
loader_model
runtime_model
analysis_model
renderer_expectations
unknowns / conflicts / deferred / unsupported
facts[]
```

Important claims have stable fact ids, status, source policy, and citations.
Tooling should be able to report that parser behavior is backed by a specific
fact id such as `macos.code_resource.nonzero.segment_header`.

## Fact States

Accepted parser behavior may consume only:

- `validated`: directly supported by allowed cited sources.
- `parser_asserted`: indirect source or observed behavior plus explicit
  standard interpretation and review status.

Parser behavior may not consume these as accepted facts:

- `candidate`: research/report only; may produce candidate ranges.
- `deferred`: known but not implemented.
- `unsupported`: intentionally out of current parser scope.

Unknowns and conflicts are first-class records. Each records scope, evidence,
blocked behavior, and required parser action: fail closed, emit candidate, emit
placeholder, ignore safely, or block closeout.

## Source Policy

Allowed source types:

- `old_out_of_print`: old no-longer-sold platform manuals/books used as cited
  reference material.
- `modern_compatible`: modern sources with compatible license.
- `project_observed`: committed fixtures, extracted metadata, and parser drift
  tests.
- `parser_asserted`: project-maintained standard interpretation when direct
  documentation is unavailable or indirect.

Excluded source types:

- modern incompatible sources as KB inputs;
- copied large source text in KB records;
- undocumented facts presented as validated.

Each citation records `source_type`, `license_status`, `citation`, and
`fact_status`. Observed fixture bytes can support candidates and parser
assertions, but observed bytes alone cannot validate a general platform rule.

## Model Split

The KB separates these layers:

- `file_structure`: bytes, headers, regions, tables, symbols, relocations.
- `loader_model`: OS loader behavior for those structures.
- `runtime_entry_model`: stack/register/base-pointer state at entry.
- `analysis_model`: how facts become code/data/bss/symbol ranges.

Entrypoints are also typed:

- `file_entrypoint`
- `segment_entrypoint`
- `runtime_entrypoint`
- `exported_entrypoint`
- `callback_entrypoint`
- `analysis_seed_entrypoint`

The current Mac `movea.l (a7)+,a0` boundary is only an
`analysis_seed_entrypoint` / candidate until 018-002 validates or replaces it.

## Archetypes

The KB defines standard target archetypes, not just byte formats:

- `amiga.executable`, `amiga.object`, `amiga.library`, `amiga.device`,
  `amiga.resident`, `amiga.disk_bootblock`
- `atari_st.prg`, `atari_st.tos`, `atari_st.ttp`
- `macos.application_code_resources`, `macos.mpw_tool_code_resources`

Each archetype defines identification, expected containers/regions, entrypoint
model, standard metadata, parser checks, renderer expectations, and unsupported
or deferred areas.

## Output Locations

Canonical source/spec locations:

```text
docs/platform-executable-formats.md
knowledge/platform_executable_formats.schema.json
knowledge/platform_executable_formats.json
```

Generated runtime/check locations:

```text
src/generated/platform_executable_formats.c
src/generated/platform_executable_formats.h
tests/test_platform_executable_formats.py
```

C tests should follow the existing `src/test_*` pattern where parser checks need
native coverage.

## Platform Scope

Mac OS:

- HFS file metadata and Finder type/creator.
- Resource fork map.
- `CODE 0` and nonzero `CODE` resources.
- Segment Loader behavior, A5 world, jump table, inter-segment calls, entry
  conventions, relocation/fixup model, and MPW Link output.
- MPW object/library formats where local docs or examples support them.

Amiga:

- HUNK executable, object, library, resident, device, and LoadSeg behavior.
- Code/data/bss hunks, relocations, symbols, overlays, resident structures, and
  library/device entry conventions.
- Old out-of-print manuals/books, compatible modern sources, project-observed
  facts, and parser assertions where direct documentation is unavailable.

Atari ST:

- PRG/TOS/TTP/GEMDOS executable header, text/data/bss, relocation table,
  symbol table, basepage/entrypoint conventions, and trap ABI links.
- Devpac/EmuTOS/Hatari or manual sources as citations where they define file
  structure and loader behavior.

## Acceptance Criteria

- A shared schema exists for platform executable-format KB records.
- A thin Mac OS proof record exists with the initial schema so schema decisions
  are tested against the 012 blocker, not only abstract examples.
- Mac OS executable parsing rules are backed by local docs/MD/KB citations
  before Proposal 012 can close.
- Mac OS CODE byte-entry, relocation/fixup, and CODE 0 jump-table/segment-map
  behavior is either accepted with citations/parser assertions or explicitly
  emitted as candidate/deferred/unsupported evidence.
- Mac OS targets expose multi-CODE resource structure as navigable/renderable
  source evidence, not only one selected CODE resource.
- Amiga and Atari ST records cover their standard executable-bearing formats
  with citations and parser assertions where needed.
- Parser/check scaffolding consumes the KB or validates C parser output against
  the KB.
- KB-backed parser output emits only fact ids that resolve to KB record items
  with matching fact status and parser-use semantics; citation packet ids and
  `fact_candidate_id` values are not accepted parser fact ids.
- Tests reject heuristic-only executable parsing when no cited or asserted
  platform rule exists.
- Target-specific analysis remains separate from standard platform semantics.
- Renderer expectations are derived obligations: output must expose platform
  code/data/bss/entry/relocation facts and must not present one platform as
  another, but exact formatting remains renderer-owned.

## Issue Seeds

018-001. Executable-Format KB Schema Gate

```text
Prestep/gate. Define the shared schema, canonical KB locations, fact states,
source policy, citation/assertion rules, unknown/conflict/deferred handling,
typed entrypoint vocabulary, and a thin Mac proof record. No later issue may
commit accepted executable-format KB records or parser migrations before this
gate is complete.
```

018-002. Mac OS Executable Citation Packet

```text
Research-only after 018-001. Extract cited Segment Loader, resource fork, CODE
resource, A5 world, jump-table, relocation/fixup, entrypoint, and MPW Link/Rez
facts from local MD/docs/KB and MPW examples. The current `movea.l (a7)+,a0`
boundary remains candidate evidence until this packet validates or replaces it.
```

018-003. Mac OS KB Record And Heuristic Migration

```text
After 018-001 and 018-002. Convert the Mac citation packet into accepted or
parser-asserted KB records, explicitly migrate current CODE parsing heuristics,
and record unresolved behavior as candidate/deferred rather than accepted.
```

018-004. Generated Checks And Heuristic Guardrails

```text
After 018-001 and at least one accepted platform record. Add schema/data
validation, candidate-vs-accepted guardrails, and reportable KB-backed parser
coverage so heuristic-only executable parsing cannot be marked complete.
```

018-005. Mac OS Parser And Listing KB Migration

```text
After 018-003 and 018-004. Update the Mac OS C parser, Python wrapper, and
listing/rendering paths to consume or validate against accepted KB facts.
Accepted code/data/entry classifications must cite validated or
parser-asserted fact ids; candidate facts may only produce candidate ranges.
```

018-006. Amiga/Atari Backfill Plan And First Records

```text
Research may start early, but accepted records require 018-001. Define the
Amiga and Atari ST backfill register and first cited records for their standard
executable-bearing formats without changing existing parser behavior.
```

018-007. Executable KB Issue Sign-Off Enforcement

```text
After at least one 018 issue has completed using this protocol. Add a local
validator for 018 issue structure and sign-off checklists, following the 017
issue enforcement pattern, so future 018 closure cannot bypass evidence,
review, and required sign-off sections.
```

018-008. Parser Output Fact Validation And Mac OS Rendering Cleanup

```text
Post-review follow-up after b5e38e84. Add parser-output-to-KB validation so
every emitted kb_record_id/fact_id/fact_status/parser_use resolves to
knowledge/platform_executable_formats.json with matching semantics. Fix the
invalid Mac parser fact id currently emitted for Segment Loader CODE resources,
drift-test or generate C fact constants from the KB, and remove Amiga
SECTION code,code output from every Mac rendering path.
```

018-009. Mac OS CODE Entry, Relocation, And Segment Map

```text
After 018-008. Ground Mac CODE byte-entry rules, Segment Loader
relocation/fixup semantics, and CODE 0 jump-table-to-segment/routine mapping in
cited or parser-asserted executable-format KB facts. Update parser/listing
output so CODE resources, candidate routine entries, deferred relocation state,
and orphan code/data islands are surfaced structurally instead of being silently
guessed or dropped.
```

018-010. Mac OS Multi-CODE Resource Rendering And Navigation

```text
After 018-009. Make every Mac CODE resource inspectable as structured
source/navigation output. Render CODE 0 as jump-table/application metadata,
render nonzero CODE resources with accepted segment metadata, candidate routine
anchors, orphan ranges, deferred relocation state, and listing previews or
placeholders, while preserving candidate/deferred status and keeping the
selected CODE 1 listing as one subview rather than the whole Mac project view.
```

018-011. Amiga HUNK Accepted Format Records

```text
Parallel-safe with 018-010. Promote a narrow, cited slice of Amiga HUNK
executable/object/library facts from report-only candidate inventory to
validated or parser-asserted executable-format KB records. Keep parser behavior
unchanged and do not modify Mac files.
```

018-012. Atari ST PRG Accepted Format Records

```text
Parallel-safe with 018-010. Promote a narrow, cited slice of Atari ST
PRG/TOS/TTP executable facts from report-only candidate inventory to validated
or parser-asserted executable-format KB records. Keep parser behavior unchanged
and do not modify Mac files.
```

018-013. Platform Executable KB Generated C Fact Table

```text
Parallel-safe with 018-010 if it avoids Mac rendering/navigation files.
Generate C fact constants/tables from knowledge/platform_executable_formats.json
so parser code can reference KB-derived ids/status/parser-use values instead of
hardcoded strings. Keep parser output semantics unchanged.
```

018-014. Mac OS Non-CODE Resource Metadata Inventory

```text
Parallel-safe with 018-010 if it remains inventory/research focused. Classify
Mac non-CODE resource types such as acur, CURS, cmdo, and vers as accepted
metadata, candidate metadata, deferred, unsupported, or conflict evidence
without changing CODE rendering/navigation.
```

018-015. MPW Object And Library Format Research Packet

```text
Parallel-safe with 018-010. Search local MPW docs and extracted files for object
and library format evidence, then record citation packets or candidate/deferred
KB records. Do not implement parser/import/rendering behavior.
```

018-016. Executable Format Source Citation Audit

```text
Parallel-safe with 018-010. Audit accepted and parser-asserted executable-format
facts for source quality, source policy, and claim strength. Downgrade,
defer, or convert weak accepted claims rather than relying on structural
validation alone. Do not change parser/rendering behavior.
```

018-017. Mac OS Nonselected CODE Preview And Windowing

```text
After 018-010. Add bounded candidate preview/listing windows for non-selected
nonzero Mac CODE resources where current classified ranges support them. CODE 0
must remain metadata-only, selected CODE 1 must keep the existing full listing
route, previews must be bounded to candidate code ranges, and relocation/fixup
or byte-entry semantics must remain candidate/deferred until separately
validated.
```

018-018. Mac OS CODE Preview Web UI And CDP Verification

```text
After 018-017. Make the Mac project web UI consume code_resource_details and
preview_windows so the browser-visible project view shows CODE 0 metadata,
selected CODE 1 listing state, non-selected candidate preview rows, no-preview
reasons, and deferred relocation/fixup state. Add CDP browser verification for
the rendered Mac project page.
```

018-019. Mac OS Candidate CODE Preview Disassembly Rows

```text
After 018-018. Replace unconditional dc.w/dc.b candidate preview rows with
decoded Mac-style m68k rows where the existing listing/decode path can safely
produce them. Keep rows candidate-only, keep relocation/fixups deferred, and
preserve data-row fallback with an explicit reason.
```

018-020. Mac OS CODE Preview Extraction Cache

```text
After 018-017, and preferably after 018-019 if preview row semantics are being
changed. Avoid repeated CODE resource extraction during one Mac project payload
build. Keep output semantics unchanged and prove cache hit/isolation behavior
with instrumented tests.
```

018-021. Mac OS Relocation/Fixup Citation Packet

```text
Batch-safe research/doc issue. Search allowed local Mac/MPW sources for Segment
Loader relocation/fixup evidence, record citation packets or KB facts with
accepted/candidate/deferred/conflict status, and do not change parser, payload,
artifact, or web behavior.
```

018-022. Mac OS Source-To-CODE Mapping Research

```text
Batch-safe research/doc issue. Compare MPW source/build metadata, documentation,
and observed CODE resources to classify source-to-CODE mapping evidence. Keep
the current source/binary boundary safe and do not change parser or UI behavior.
```

018-023. Mac OS Non-CODE Resource Web UI

```text
After 018-014 and 018-018. Surface non-CODE resource metadata inventory in the
Mac web UI with candidate/deferred/unsupported labels and CDP verification.
Avoid concurrent edits with 018-024 because both touch the Mac container UI.
```

018-024. Mac OS CODE 0 Jump Table Drilldown

```text
After 018-010. Render CODE 0 jump-table entries as structured artifact/web
rows. Keep accepted jump-table layout facts separate from candidate
segment/routine interpretation and keep CODE 0 metadata-only.
```

018-025. Proposal 012 Closeout Matrix

```text
Batch-safe docs issue. Add a Proposal 012 closeout matrix that separates
completed starter support from remaining blockers and deeper roundtrip work.
Do not change code and do not mark Proposal 012 closed.
```

## Implementation Notes

- 018-001 added the canonical human/schema/data authority files:
  `docs/platform-executable-formats.md`,
  `knowledge/platform_executable_formats.schema.json`, and
  `knowledge/platform_executable_formats.json`. The initial KB contains a thin
  Mac proof record only. It represents `macos`, HFS resource-fork CODE
  resources, CODE 0 as candidate metadata, nonzero CODE resources as candidate
  segment resources, and the current `movea.l (a7)+,a0` boundary as an
  `analysis_seed_entrypoint` with `candidate_only` parser use.
- 018-001 also added
  `amiga_reversing.tools.platform_executable_formats` and
  `tests/test_platform_executable_formats.py`. The validator enforces the
  source/fact-state vocabulary and rejects candidate/deferred/unsupported facts
  that try to authorize accepted parser output. No parser or renderer behavior
  changed.
- 018-002 added Mac citation packets to the executable-format KB. Validated
  packets now cite local Inside Macintosh and MPW manual markdown for the HFS
  resource-fork application-code relationship, Segment Loader CODE resources,
  nonzero CODE segment headers, CODE 0 jump-table/A5 metadata, CODE 1 main
  startup, A5 jump-table offset, and MPW Link application output. Project
  observed MPW Asm inventory remains candidate-only, the current
  `movea.l (a7)+,a0` boundary remains candidate-only, and relocation/fixup
  semantics remain deferred. No parser or renderer behavior changed.
- 018-003 added the first accepted Mac executable-format record,
  `macos.hfs_resource_fork.code_resources.mpw_application`. It accepts only
  facts backed by validated 018-002 packets: HFS resource-fork application code,
  Segment Loader CODE resources, CODE 0 jump-table/A5 metadata, nonzero CODE
  segment headers, CODE 1 main startup, A5 jump-table offset, and MPW Link
  output. The `movea.l (a7)+,a0` boundary is explicitly migrated to
  candidate-only state; relocation/fixups and byte-level entry rules remain
  deferred. No parser or renderer behavior changed.
- 018-004 added the first local guardrail report:
  `python -m amiga_reversing.tools.platform_executable_formats guardrails`.
  It separates KB-backed records from report-only records and lists accepted,
  candidate-only, deferred, and unsupported fact ids. Tests fail if the Mac
  `movea.l (a7)+,a0` candidate is promoted to accepted parser output, while the
  018-001 thin proof remains report-only and untouched legacy parser behavior is
  not blocked.
- 018-005 updated the Mac C parser summary, Python listing adapter, project
  payload, and committed MPW Asm target artifact to expose KB fact ids/status.
  CODE 0 and nonzero CODE segment-header classifications are validated parser
  output. The current `movea.l (a7)+,a0` executable byte boundary is still used
  to extract/render the starter listing, but it is now explicitly
  `candidate_code` with `candidate_only` parser use; missing entry evidence is
  deferred. Regression tests keep `SECTION code,code` out of Mac listings.
- 018-006 added first report-only Amiga and Atari records:
  `amiga.hunk.load_file.basic_backfill` and
  `atari_st.prg.gemdos_basic_backfill`. They cite the existing normalized
  HUNK/PRG KBs, list backfill-required parser assumptions, set `kb_backed:
  false`, and do not change parser behavior or authorize accepted parser output.
- 018-007 added `amiga_reversing.tools.validate_018_issues`. The validator
  checks 018 issue status vocabulary, Proposal 018 references, required protocol
  sections, completed-issue completion evidence, completed checkbox sign-off,
  and superseded/deleted reasons without rewriting files.
- Post-review of commit `b5e38e84` found that 018-004/018-005 are not enough
  for full proposal closeout. Guardrails validate KB-internal candidate/accepted
  state, but parser-emitted fact ids are not yet checked against KB records. At
  least one emitted id, `macos.segment_loader.code_resources`, resolves only to
  a citation packet `fact_candidate_id`, not a KB item/fact with matching
  parser-use semantics. One lower-level Mac raw CODE rendering test path also
  still expects Amiga-style `SECTION code,code`. 018-008 is required before
  018 can be treated as complete.
- 018-008 added `validate_parser_fact_references()` to validate real parser
  output against KB record items, including inherited `kb_record_id` context for
  nested layout ranges. Tests now reject citation-packet `fact_candidate_id`
  values as parser facts, reject status/parser-use drift, and drift-test the C
  Mac fact constants against the KB. The invalid emitted
  `macos.segment_loader.code_resources` id was replaced with
  `macos.resource_fork.code_resources.accepted`, and the raw Mac CODE listing
  test now uses the Mac listing adapter so `SECTION code,code` is filtered on
  that path too. The `movea.l (a7)+,a0` boundary remains candidate-only.
- 018-009 is the next Mac-specific blocker after 018-008. It must not close by
  relabelling the current `movea.l (a7)+,a0` scan as accepted without citations
  or parser assertions. It should either validate byte-entry and relocation
  rules or keep them candidate/deferred while exposing CODE 0 jump-table,
  segment/routine, and orphan-island evidence structurally.
- 018-009 added that structured Mac output. The C summary, project payload, and
  committed MPW `Asm` artifact now expose CODE 0 jump-table spans, nonzero CODE
  segment jump-table spans, candidate routine offsets, candidate/deferred
  orphan ranges, and deferred relocation/fixup placeholders with KB fact ids.
  The `movea.l (a7)+,a0` boundary is still candidate-only; relocation/fixup
  interpretation and complete byte-level CODE entry rules remain deferred.
- 018-010 turned the 018-009 segment-map evidence into per-CODE resource
  source/navigation views. The Mac project payload now exposes
  `code_resource_details` and navigation groups for every CODE resource; the
  committed MPW `Asm` artifact has a per-CODE detail subview for CODE 0,
  nonzero CODE segment metadata, candidate routine/code anchors, orphan ranges,
  deferred relocation/fixups, and listing availability. CODE 0 remains
  metadata/jump-table output, routine/code anchors remain candidate where
  appropriate, and relocation/fixups remain deferred until separately
  validated.
- 018-011 through 018-016 are intended as parallel-safe work items while
  018-010 proceeds. They should not require updates from 018-010 and should
  avoid Mac multi-CODE rendering/navigation files unless their issue explicitly
  permits metadata-only inventory. Their purpose is to advance Amiga/Atari KB
  acceptance, generated fact-table infrastructure, MPW format research, and
  citation quality without blocking the Mac rendering slice.
- 018-017 added bounded candidate preview windows for non-selected nonzero Mac
  CODE resources where the existing classifier exposes `candidate_code` ranges.
  CODE 0 remains metadata/jump-table only, selected CODE 1 keeps the full
  listing route, preview rows stay `candidate_only`, and relocation/fixup
  interpretation remains deferred. Resources without candidate code ranges keep
  structured placeholders that name the classifier evidence blocking preview.
- 018-018 made those Mac CODE detail records visible in the browser project
  page. The current `macos` renderer consumes `code_resource_details` and
  `preview_windows`, shows CODE 0 as metadata/jump-table-only, preserves the
  selected CODE 1 listing panel, labels non-selected preview rows as
  candidate/bounded, shows no-preview reasons, and keeps relocation/fixup state
  deferred. A CDP test opens the rendered Mac project page and checks those DOM
  states.
- 018-021 reviewed local Mac/MPW sources for relocation/fixup evidence. It
  added candidate evidence that Segment Loader loading can cause Memory
  Manager heap/block relocation, but it did not find accepted on-disk CODE
  fixup byte-layout rules. `macos.segment_loader.relocation_fixups.deferred`
  remains deferred-only and parser behavior is unchanged.
- 018-022 reviewed MPW source/build-to-CODE mapping evidence. Local old-source
  documentation validates that MPW segment names become CODE resource names,
  but the available Sample/Count/Memory source fixtures are not the source for
  the observed MPW/Tools/Asm executable. The project boundary therefore remains
  `source_segments_map_to_observed_code_resources: false`.
- 018-025 added a Proposal 012 closeout matrix that separates completed starter
  support from full-closeout blockers and deeper roundtrip work. It does not
  close Proposal 012 and does not promote candidate/deferred Mac facts.

## Relationship To 012

Proposal 012 remains open for full executable/CODE correctness. 018-005 removes
the stale claim that the Mac parser/listing path accepts the current byte-entry
heuristic, and 018-008 validates emitted parser fact ids against the KB, but
relocation/fixup semantics and byte-level entry rules remain deferred/candidate.
018-009 exposes CODE 0 jump-table to segment/routine mapping, orphan-island
evidence, and deferred relocation placeholders structurally. 018-010 now exposes
that structure in per-CODE payload/navigation/artifact views, while keeping
unresolved byte-entry and relocation semantics candidate/deferred rather than
accepted.
018-017 makes those non-selected CODE views inspectable with bounded
candidate-only preview windows where safe ranges exist; it still does not close
Proposal 012 because the byte-entry rule and relocation/fixup semantics remain
candidate/deferred.
018-018 carries the same fact-state boundaries into the browser UI and verifies
them with CDP; it adds UI coverage, not accepted byte-entry or relocation
semantics.
018-021 and 018-022 clarify why relocation/fixups and source-to-CODE mapping
remain blockers despite additional cited context, and 018-025 makes that split
auditable in Proposal 012.

018 sits above 011 and 012 as the shared executable/container format authority.
It does not absorb all platform knowledge; it owns file structure, loader model,
entrypoints, relocations, symbols, code/data/bss boundaries, and renderer
obligations for executable-bearing formats.
