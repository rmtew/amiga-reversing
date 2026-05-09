# M68K analysis plan: RSSET, absolute memory, and lookup tables

This plan records the current RSSET survey and expands the design target to
absolute memory, ORG/runtime views, bootstrapping, and lookup-table rendering.
It should be reviewed before more renderer changes are made.

## Objective

Build a C-owned model for persistent base-relative storage, absolute runtime
memory, ORG/runtime views, bootstraps, lookup tables, and orphaned code signals.
Rendering should consume that model to emit `RSSET`, labels, platform fields,
ORG ranges, relative table expressions, and web UI navigation without confusing
app storage, Amiga hardware, runtime-copied code, scalar data, orphan candidates,
and dispatch tables.

## Current Implementation Notes

Commit `ff0753d8069cbf5495debcaa9536f8d5b940cafe` added a guard against treating
unknown `a6` displacements as app slots when the displacement matches generated
`_custom` hardware metadata.

Relevant current behavior:

- `render_state_operand_uses_app_base()` rejects registers already known as
  hardware bases.
- Unknown `a6` fallback is still allowed, but not for `_custom` register,
  register-field, or register-range offsets.
- `render_asm_app_extension_rs()` builds RSSET output from app-base field slots
  and metadata RSSET layout regions.
- Overlapping slots are currently emitted as alias `RSSET $xxxx` fragments.
- The RSSET slot list uses renderer scratch arena storage.

The test covering the hardware false-positive class is
`test_facts_v2_render_asm_source_does_not_infer_app_slot_from_unknown_a6_custom_offset`.

Existing tests show partial lookup/absolute coverage:

- runtime copy and absolute entrypoint mapping
- interrupt/vector target discovery
- long jump-table target promotion
- word-relative dispatch target promotion
- runtime-mapped word dispatch rendering
- relocation-backed pointer-table classification
- absolute long lookup tables with labels and nulls
- pointer-table runtime data targets
- hardware/display/audio runtime sink classification
- runtime copy and ORG conflict suppression
- low trampoline suppression where a larger runtime range is stronger
- likely code islands can be detected, but are not accepted unless linked to
  real flow

These behaviors need one unified design model so new cases do not become
one-off heuristics.

## Current Code And Target Review

Reviewed implementation and tests before updating this plan. Current state:

Latest update: internal structured-data role consumers are flags-only. Role text
is parsed only when setting policy/import metadata and emitted only as display
text; render-plan rows, runtime-address refs, inferred runtime refs, listing
JSON/navigation, table records, orphan nearby-data context, and platform runtime
sink checks now consume numeric role flags directly. Orphan nearby-data relation
state is now a compact C enum and corpus indexing consumes the exported relation
id, not the display string.

| Topic | Current evidence | Gap to address |
| --- | --- | --- |
| RSSET/app slots | `render_state_operand_uses_app_base()` rejects known hardware bases and `_custom` offsets; `render_asm_app_extension_rs()` emits app/resident RSSET layouts from field slots and metadata; policy RSSET regions carry explicit app-layout and storage-kind ids so rendering/reporting does not classify static names; target metadata parses the app-layout flag directly and tests assert app-looking names alone do not infer it; resident/autoinit structured data carries compact platform/field ids so renderer decisions do not parse pseudo-struct text; listing app-slot aggregation stores access/width properties as compact typed values rather than copied strings; C source analysis now records rendered base-layout fields, layout-kind ids, and alias overlays as first-class facts; typed app-slot region fields carry generated owner-struct metadata; listing JSON exposes those layout fields directly. Same-base, different-layout overlaps are now marked conflicted in C `memory_layout_records`, with isolated coverage in `test_source_analysis_memory_layout_marks_same_base_layout_overlap_conflicted`. | Need accepted-code/runtime-space conflict checks only where the analysis has a real source/runtime mapping; do not compare base-relative app offsets directly to source code offsets. |
| Typed structs vs app slots | Typed app-slot struct regions own their full generated struct extent; interior offsets are blocked from flat RSSET output and render through typed fields where known. `_custom` offset false positives have an isolated test; C JSON now includes resolved/unresolved platform typed accesses, recovered platform storage writes, typed owner metadata on base-layout region records, and aggregate base-layout extent records in `memory_layout_records`; resolved typed accesses now carry generated `struct_size` and `field_size`; unresolved typed-access classification and platform storage effects now carry numeric C enum ids so corpus/report decisions do not branch on display strings; memory-layout records now expose normalized range space/start/size/end fields for compact ownership/range consumers; corpus target rows now include target-level memory-layout views summarized from numeric range-space, conflict-state, and absolute-owner ids. Same-base overlaps between app and named/metadata layouts are conflict-marked before export. | Need stronger C-side checks for typed/platform struct ownership against non-app ranges where those ranges share a comparable base or mapped runtime/source space. |
| ORG/runtime views | Tests cover runtime-copy jump targets, low trampoline suppression, policy runtime ranges, conflict failure, policy-vs-inferred precedence, corpus tags, listing navigation for materialized/suppressed runtime views, and compact C runtime-view relationships for larger-range exits, contained views, and runtime-copy overlays. Corpus indexing now uses numeric materialization reason and relationship ids for runtime-view decisions; names remain display text. | Need broader wrapper-load/helper/final-image target metrics and examples across imported disks. |
| Lookup/jump tables | Tests cover long dispatch, word-relative dispatch, far targets, runtime-mapped dispatch, mixed labels/raw entries, pointer tables, relative `target-base` rendering, C JSON `table_records` derived from accepted structured table data, consumer instruction provenance, source-pattern provenance, explicit `conflicted` flags for overlap handling, and C JSON `table_candidate_records` plus corpus tags/xrefs for unresolved indirect/table candidate sites by status, shape, source instruction range, operand index, source pattern, and rejected direct-stub bounds. Structured-data semantic roles now carry compact role flags, including string roles, so analysis/rendering does not branch on display strings for table/palette/copper/string properties; auto structured-data, inferred runtime-address dedupe, listing rows, listing navigation entries, runtime-address refs, table records, and orphan nearby-data context carry flags for known roles. Corpus indexing consumes C/listing role flags for table/copper/bitmap decisions and no longer infers table classes from rendered comments or display strings. Table conflict state now carries a numeric C enum id; string names remain exported display text only. | Need more rejected-bound classes beyond direct-stub tables where value-flow can prove candidate spans. |
| Absolute memory | Tests cover ExecBase literal behavior, stack top EQU, interrupt/vector target stores, runtime aliases, relocation anchors, hardware sinks, display/copper/audio sinks; generated Amiga hardware metadata now carries stable hardware-base ids, symbol ids for registers/ranges, and runtime-target kind enums so display/audio/runtime-sink analysis does not branch on static base/register/role strings; bootloader hardware read setup consumes generated hardware ids and enum access kinds, OpenLibrary/OpenDevice recognition uses generated vector/function ids, and C trace/platform base state carries generated base ids so `SysBase`, `exec.library`, and base-symbol aliases converge before LVO analysis; strings are kept only for exported JSON/source text. C JSON now exposes `memory_layout_records` for base-layout fields, runtime views, runtime-address references with external hardware sink addresses, normalized range facts, accepted absolute operands classified as ExecBase, CPU vector, hardware register/range, runtime range, section storage, or absolute memory with numeric conflict state ids, absolute-owner ids, and memory-layout record-kind ids. Absolute operands found inside orphan terminal-code signals are exported into the same memory-layout view as unresolved absolute-memory candidates rather than promoted to code. Corpus memory-layout views and memory-kind features derive from numeric ids/flags rather than display strings. Corpus decompression rows now expose grouped `decompression:source_load_entry` features tying source range, absolute load address, and entrypoint together for raw/decompressed payload relationships; a temporary full usage rebuild found 19 grouped facts across 9 rows, covering Carrier, Pandora, Damocles, and Voodoo Nightmare. | No current row-specific implementation gap; keep broader imported-target coverage under Targets. |
| Orphaned code | C analysis now records unresolved terminal-decode islands at accepted-code boundaries or data labels as orphan signals without promoting them to accepted code; nearby structured data carries role flags, source offset, distance, and compact relation id into the signal, so lookup-table-adjacent islands are classified with missing inbound `jump_table` and pointer-table-adjacent islands are classified as callback/function-table evidence without re-parsing semantic-role text. Policy-named orphan labels are distinguished as `policy_seed` evidence while object/metadata labels remain `metadata`. Source-analysis JSON now exposes target-level orphan status and missing-inbound summary counts consumed by corpus metrics. | Extend the signal with vector/API evidence classes and reconciliation after table/callback/vector improvements. |
| Targets | Bloodwych has many relative lookup tables; Pandora demonstrates wrapper load vs final copied image; Conqueror demonstrates weak low ORG risk; Carrier stresses packed/runtime-copy ambiguity; GenAm/MonAm remain comparator targets. Corpus rows now derive evidence-based `target-pattern:*` tags for relative lookup dispatch, copied runtime code, weak low trampolines, packed runtime copy, packed runtime-copy conflict, and orphan-code signals without target-name rules. | Need broader imported-disk coverage for wrapper/helper/final-image roles and future pattern tags as new heuristics land. |

Past decisions to preserve:

- C analysis is authoritative; Python/UI consume facts only.
- Do not hardcode M68K instruction knowledge; use generated decode/effect data.
- Do not emit `ORG` or labels merely to make output prettier.
- Keep `$4` ExecBase loads literal unless copied executable code at `$4` is
  actually proven.
- Weak low trampolines become numeric/EQU symbols, not disruptive ORGs.
- `code_start_refs` stay provenance-first but must be unioned with explicit
  policy/metadata/fallback seeds.
- Data/table/string classification must not overlap accepted code unless a
  source/runtime view explains the overlap.
- Comment-only output is not a retained improvement.

## Survey Method

Surveyed all rendered `.s` files currently under `targets/` and parsed top-level
`RSSET`, `app_* RS.*`, and unnamed `RS.*` rows. No duplicate RSSET symbol names
were found in the surveyed files.

## RSSET Survey

| Target source | Ranges | Origin and review |
| --- | ---: | --- |
| `carrier/.../c__loadwb_175153fc.s` | 1 | `RSSET 0`; small app-base layout. |
| `carrier/.../c__more_7c8dea18.s` | 1 | `RSSET 0`; small app-base layout. |
| `carrier/.../c__setpatch_50db5120.s` | 1 | `RSSET 0`; app-base storage. |
| `carrier/.../devs__parallel.device_0b78e156.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `carrier/.../devs__ramdrive.device_2c146d8c.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `carrier/.../devs__serial.device_ddfdac2b.s` | 9 | Main `LIB_SIZE` layout plus singleton overlays at `$0023,$0038,$0043,$0044,$0045,$0048,$01BD,$01C4`; not proven independent ranges. |
| `carrier/.../libs__icon.library_8bc90c0c.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `carrier/.../libs__info.library_3fb9d33a.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `carrier/.../libs__version.library_5059c1a5.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `carrier/.../amiga_raw_carrier_rnc_00004c60.s` | 1 | `RSSET 0`; decompressed raw target app layout. Needs absolute load range metadata. |
| `damocles/.../c__ed_fbb099a6.s` | 1 | `RSSET 0`; app-base storage. |
| `damocles/.../damocles_53b24620.s` | 1 | `RSSET 0`; app-base storage. |
| `damocles/.../devs__parallel.device_0b71ffaa.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `damocles/.../devs__printer.device_1aada1d4.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `ice_runner/.../bootloader_stage_1.s` | 1 | `RSSET 0`; bootloader/app storage. |
| `midwinter/.../bootblock.s` | 1 | `RSSET 0`; bootblock state. |
| `pandora/.../pandora_..._bk_00_000000e8.s` | 4 | Main `RSSET 0` plus overlays at `$01AD,$0287,$07EF`; raw absolute payload needs load/range tracking. |
| `search-for-the-king/.../king_481902ec.s` | 1 | `RSSET 0`; app-base storage. |
| `search-for-the-king/.../libs__icon.library_8bc90c0c.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `search-for-the-king/.../loadwb_f71d84f8.s` | 1 | `RSSET 0`; small app-base layout. |
| `starglider/.../c__binddrivers_0f9bcf15.s` | 1 | `RSSET 0`; small app-base layout. |
| `starglider/.../devs__parallel.device_0b78e156.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `starglider/.../devs__serial.device_ddfdac2b.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `starglider/.../libs__icon.library_8bc90c0c.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `starglider/.../libs__info.library_3fb9d33a.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `starglider/.../libs__mathieeedoubbas.library_3d4e4903.s` | 0 | Confirmed empty resident autoinit size: `resident_base_size == LIB_SIZE`; render `LIB_SIZE` directly, no empty app layout. |
| `starglider/.../libs__mathtrans.library_30d0f132.s` | 0 | Confirmed empty resident autoinit size: `resident_base_size == LIB_SIZE`; render `LIB_SIZE` directly, no empty app layout. |
| `starglider/.../libs__version.library_5059c1a5.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `starglider/.../sg_9832b282.s` | 1 | Large `RSSET 0`; app-base storage. |
| `starglider/.../system__diskcopy_c5715319.s` | 1 | `RSSET 0`; small app-base layout. |
| `voodoo-nightmare/.../run_df6ad190.s` | 1 | Large `RSSET 0`; app-base storage. |
| `targets/amiga_hunk_bloodwych/bloodwych.s` | 5 | Main `RSSET 0` plus byte overlays `$0001,$0003,$0005,$0007`; aliases inside one app layout. |
| `targets/amiga_hunk_genam/genam.s` | 5 | Main `RSSET 0` plus overlays `$021D,$023F,$057F,$10CC`; includes named `app_TimerBase`; not independent ranges. |
| `targets/amiga_hunk_magicland_dizzy_md/magicland_dizzy_md.s` | 1 | `RSSET 0`; minimal app/storage evidence. |
| `targets/amiga_hunk_monam302/monam302.s` | 5 | Main `RSSET 0` plus overlays `$0560,$0567,$082C,$0C6E`; includes named `app_ConsoleDevice`; not independent ranges. |
| `targets/amiga_hunk_voodoo_nightmare_run/voodoo_nightmare_run.s` | 1 | Large `RSSET 0`; app-base storage. |

## Multi-Range Review

The current multi-RSSET files do not prove multiple independent memory ranges.
They are mostly alias overlays inside one base:

| File | Finding |
| --- | --- |
| Carrier `serial.device` | One `LIB_SIZE` device extension. Extra ranges are singleton offsets inside that layout. |
| Pandora extracted BK target | One main app layout. Extra ranges are aliases; the larger issue is absolute load/runtime range tracking. |
| Bloodwych | Main app layout with byte overlays at odd offsets. Not independent bases. |
| GenAm | Main app layout with singleton overlays and API-derived base slots. Not independent bases. |
| MonAm | Main app layout with singleton overlays and API-derived base slots. Not independent bases. |

Required change: represent these as one layout with alias fields unless C analysis
proves a distinct base id.

## Implementation Requirements

1. Add or refine C analysis records for base-relative layouts:
   - base id and name
   - base kind: app, resident extension, IORequest, metadata, absolute
   - base address if known
   - field offset, size, access width, read/write/address evidence
   - alias/overlay relationship: implemented for app/metadata RSSET layout fields
   - source instruction provenance: implemented for app-slot access layout fields
   - confidence and conflict state: implemented for app/metadata RSSET layout fields
   - typed owner struct for app-slot region fields: implemented on
     base-layout field records and indexed as platform-struct memory layout
     evidence
   - platform-owned field evidence: implemented as resolved/unresolved typed
     access memory-layout records
   - unresolved typed-access classifications are exported with compact numeric
     C enum ids; corpus/report consumers use those ids and keep strings only
     for feature/display text
   - platform storage effects are indexed from numeric C effect ids; effect
     names remain display text
   - policy RSSET layout storage kinds are parsed once at the metadata boundary
     into compact C enum ids; strings remain display/export text
   - rendered base-layout fields carry compact layout-kind ids so range
     consumers can distinguish app layouts from named layouts without parsing
     layout/base names; corpus indexing exposes those ids as layout-kind
     features/xrefs
   - target metadata RSSET regions parse explicit flag bits for app layout;
     app-looking layout/base names do not synthesize that flag
   - resident/autoinit structured data parses generated struct/field ids and
     Amiga pseudo-field ids once; renderer decisions use ids, strings are
     exported text

2. Add absolute memory-layout records:
   - source section/file range
   - runtime destination base and extent
   - C JSON `memory_layout_records` implemented for base-layout fields,
     runtime views, runtime-address references, and recovered platform storage
     effects
   - memory-layout record kinds carry compact numeric ids; corpus consumers use
     ids for record-kind features and strings only for display
   - memory-layout kind features are derived from numeric record/effect/owner
     ids, runtime materialization state, alias flags, and structured-data role
     flags; strings remain display/export text
   - memory-layout records expose normalized range space/start/size/end fields
     so web/corpus consumers can merge ranges without reinterpreting
     record-specific offset fields
   - aggregate base-layout extent records are emitted from C analysis so UI and
     corpus consumers can navigate a full app/resident layout without
     reconstructing it from individual fields
   - runtime-address references expose external hardware sink addresses when
     generated platform sink metadata proves the consumer
   - accepted absolute operands are recorded as `absolute_memory_ref` records
     with generated access kind, owner classification, owner symbol where known,
     and accepted-code conflict state
   - orphan-code absolute operands are recorded as unresolved
     `absolute_memory_ref` memory-layout candidates with source provenance, but
     do not promote the orphan bytes to accepted code or invent ownership
   - absolute memory records export numeric owner-kind ids; corpus target rows
     summarize absolute-owner, range-space, and conflict views from numeric ids
   - non-clean memory-layout conflict states are indexed from numeric C
     conflict-state ids for corpus navigation, including `code_overlap` and
     unresolved candidates
   - copied-code entrypoints
   - stack, bitplane, copper, audio, and app-storage ranges when detected
   - ownership conflicts and accepted-code overlap gates

3. Add ORG/runtime-view records:
   - storage source range and runtime destination range
   - rendered logical PC base
   - separate runtime range base, extent, and entrypoint list
   - source-to-runtime address map
   - copy, decrunch, relocation, vector, trap, or trampoline provenance
   - entrypoint list with reason and confidence
   - classification: materialized ORG, weak trampoline, absolute symbol,
     suppressed candidate, unresolved problem
   - compact relationship to a stronger runtime view when suppression is caused
     by larger-range exit, contained view, or runtime-copy overlay: implemented
     with numeric relationship ids consumed by corpus/report code
   - corpus tags and rejected-candidate reason: implemented for runtime-view
     materialization/suppression reasons, runtime-view relationships, and
     listing navigation
   - exact reproduction/source reassembly status

4. Add lookup-table records:
   - table base label and source range: implemented as C JSON
     `table_records` for accepted structured lookup/pointer tables, with
     table role represented by C `role_flags`
   - consumer instruction/source provenance: implemented for auto-classified
     structured table data as `consumer_section`/`consumer_offset`
   - source-pattern provenance: implemented as C enum ids on structured table
     facts and recovered indirect/table-candidate facts; JSON derives
     `source_pattern` as display text, ignores stale source-pattern strings,
     and corpus tags consume the ids
   - semantic role provenance: implemented as C `semantic_role_flags`; JSON
     `semantic_role` is derived display text, C auto-analysis sets roles by
     flags, stale role strings are ignored, and C regression tests assert
     semantic roles/data classes through flags rather than display strings;
     legacy role-name parsing has been removed from the C analysis path
   - runtime-address data class provenance: implemented as C
     `data_class_flags`; JSON `data_class` is derived display text and stale
     class strings are ignored
   - entry size, signedness, stride, count, and bounds
   - table kind: scalar, pointer, relative pointer, code dispatch, data offset,
     hardware setup, mixed: implemented as C `table_kind_id` for scalar,
     pointer, relative-code-dispatch, and absolute-code-dispatch structured
     tables
   - base expression: table label, section base, runtime base, PC, or explicit
     data label: implemented as C `base_expression_id` target-label/table-label
     classification
   - entry target range and null/sentinel rules: target base recorded when
     known
   - confidence and conflict state: implemented for clean/code-overlap table
     records with numeric C enum ids
   - rejected table bounds on unresolved candidates: implemented for proven
     direct-stub spans rejected for insufficient entries; corpus consumers use
     C enum ids for recovered indirect flow, shape, status, source pattern, and
     table-bounds status rather than display strings

5. Add orphaned-code signal records:
   - candidate source range and decode start: implemented for terminal-decode
     islands at accepted-code boundaries or data labels
   - terminal instruction and candidate extent: implemented
   - plausibility score, CPU requirement, instruction count, and decode conflict
     count: implemented as compact signal fields using generated decode data
   - nearby data/table/string context: implemented for immediately adjacent
     structured data classes with nearby data offset, distance, and relation
   - possible missing inbound evidence class: jump table, callback, vector,
     runtime copy, API, metadata, or policy seed: implemented for current
     signal context as unknown, metadata-label, policy-named seed,
     runtime-copy evidence, lookup-table-adjacent jump tables, and
     pointer-table-adjacent callbacks
   - status: unresolved signal implemented; suppressed implemented for
     terminal-decode islands that overlap accepted structured data; linked,
     promoted, and broader rejected classes remain planned
   - UI/navigation surfacing: implemented as an `orphan-code` listing group
   - target-level signal count: implemented in source-analysis JSON, including
     compact status and missing-inbound summary counts
   - corpus tags/xrefs: implemented as `orphan-code:*` target usage features,
     including missing inbound, nearby data, required CPU, and instruction
     count; manifest decisions consume C enum IDs and structured-data role
     flags rather than display strings
   - listing row classification: generated C listing rows carry compact
     `kind_id` values; C listing/window/navigation logic consumes those ids
     and keeps `kind` strings as exported display text
   - corpus listing and type-flow consumers treat `kind_id` as authoritative
     for row-class decisions; tests build generated-row fixtures with explicit
     ids rather than falling back to display strings
   - listing label references carry compact access ids internally and in JSON;
     access strings are exported display text only
   - listing API-call duplicate suppression compares generated Amiga library
     and function ids, not resolved display names
   - source-IR comment rendering uses compact `comment_kind` metadata for
     structural decisions such as inline struct labels and metadata comments;
     comment text is display text only

6. Rendering rules:
   - emit one RSSET block per proven base layout
   - emit alias fragments only as overlays of that layout
   - never use RSSET for known hardware or platform struct fields
   - never use absolute label/addend tricks over code/data ranges
   - emit `ORG` only for proven source-level runtime views
   - keep weak low trampolines numeric or explicit absolute symbols
   - keep orphan candidates rendered as data until a real inbound edge or
     explicit seed proves code ownership
   - use storage labels before an ORG and runtime labels inside an ORG
   - render relative table entries as `target_label-base_label`
   - render absolute pointer entries as labels only when the target owner is
     proven
   - keep scalar entries numeric unless typed evidence gives them a better
     domain-specific symbolic form
   - keep include region, RSSET region, then EQU/symbol region ordering

7. Web UI rules:
   - show memory layout ranges and conflicts from C analysis
   - navigate to source evidence for each range
   - distinguish app layout fields, aliases, hardware fields, copied runtime
     code, display memory, audio memory, stack, pointer tables, jump tables,
     scalar tables, unresolved table candidates, and orphaned code signals

## ORG and Bootstrap Plan

ORG rendering is for proven runtime views. It is not a workaround for unknown
absolute addresses.

| Pattern | Evidence to collect | Render goal |
| --- | --- | --- |
| Direct copy then jump | source, destination, length, jump target | one `ORG` at destination when source bytes map cleanly |
| Vector/trap bootstrap | vector store, handler target, copy evidence, final jump | vector symbols plus materialized final runtime range |
| Low trampoline | small copied helper, jump into larger range | usually suppress ORG; keep numeric/symbolic absolute helper |
| Decrunch wrapper | compressed source, output range, output entry | extracted target or materialized runtime range, not wrapper labels |
| Raw extracted payload bootstrap | load address plus second-stage copy | prefer final copied image over wrapper load view |
| Multiple independent ORGs | distinct source/destination ranges and cross-ref semantics | multiple ORGs only when independently proven |
| Runtime table target | indirect jump through table into runtime range | table entries use runtime labels and source/runtime map |

Required data analysis:

- track source, destination, and length through registers, stack slots, app/global
  slots, and known helper calls
- keep range base, runtime extent, and entrypoint addresses as separate facts
- backtrack vector stores and interrupt/trap installs by value, not fixed adjacent
  instruction shapes
- union C-discovered entrypoints with explicit policy/metadata/fallback seeds
- keep entrypoint provenance and confidence so weak fallthrough noise is not
  materialized
- reject or suppress ranges that overlap accepted code unless they are a proven
  copied/runtime view
- detect when a wrapper load address is less useful than a later copied runtime
  image
- preserve separate storage/runtime label namespaces
- verify direct reproduction and source reassembly where supported

Required annotations for accepted ranges:

- `runtime-copied-code`
- `trap-vector-bootstrap` when applicable
- `multi-runtime-range` when applicable
- `materialized-org-range`
- source storage section, offset, and range
- runtime base, extent, entrypoints, and provenance
- copy-loop, vector, decrunch, relocation, or jump-table evidence
- conflict/overlap result and reproduction result

Required annotations for rejected or suppressed candidates:

- `suppressed-weak-org-range`
- `low-vector-trampoline`
- `overlaps-accepted-code`
- `conflicts-with-runtime-range`
- `source-bytes-not-accepted-code`
- `packed-or-transformed-payload`

Real proving examples:

- Bloodwych: trap/vector bootstrap into the useful `$400` runtime payload.
- Conqueror: weak `$4` trampoline must not become a disruptive `ORG $4`.
- Pandora BK extracted payload: wrapper load around `$20000`, helper at `$300`,
  final copied image at `$10000` with entry around `$1046A`.
- Carrier Command: low-address helpers and packed/transformed payloads make it a
  stress target rather than a simple policy template.

## Lookup Table Plan

All table types should be discovered from consumer evidence where possible, then
validated against the data span.

| Table class | Evidence to collect | Render goal |
| --- | --- | --- |
| Absolute pointer table | relocation, absolute target range, indexed load, pointer use | `dc.l target_label` or `dc.l 0` |
| Long jump table | indexed long load followed by `jmp/jsr` or equivalent traced control transfer | `dc.l case_label` |
| Word-relative jump table | indexed word load, sign/zero extension, base add, control transfer | `dc.w case_label-table_base` |
| PC-relative dispatch | PC-relative table base plus indexed word/long dispatch | `dc.w case_label-table_label` or `dc.l case_label` |
| Runtime-mapped dispatch | table stored in source bytes but consumed through runtime view | runtime labels with source/runtime mapping preserved |
| Data offset table | indexed word/long added to a data base and then read | `dc.w data_label-data_base` |
| Scalar lookup table | indexed read used as arithmetic, mask, coordinate, state, or value | keep numeric or type by domain when proven |
| Hardware setup table | values copied to custom/CIA/display/audio registers | symbolic hardware-domain values where platform metadata supports it |
| Mixed table | labels plus nulls/sentinels/raw scalar entries | symbolic entries only where each entry is proven |

Required data analysis:

- identify the indexed read and preserve the base register/value
- backtrack table base through `lea`, `movea`, PC-relative addressing, stack/app
  reloads, and runtime-copy maps
- track entry size and signedness through extension, scaling, add/sub, and branch
  target use
- infer table bounds from compares, masks, DBF loops, sentinel values, adjacent
  accepted code, and target validity
- reject table spans that overlap accepted code unless explicitly modelled as a
  copied/runtime view
   - record unresolved candidate sites so corpus indexing can find similar
     patterns: implemented as C JSON `table_candidate_records` from unresolved
     recovered indirect sites, with status, shape, source instruction range,
     operand index, and C source-pattern id

## Orphaned Code Signal Plan

Orphaned code detection is a diagnostic tool. It should reveal gaps in program
flow analysis, not paper over them.

| Signal | Evidence to collect | Use |
| --- | --- | --- |
| Terminal decode island | plausible instructions ending in `rts/rte/jmp/bra` | flag as unresolved code candidate |
| Post-table code island | code-like range near unresolved indexed dispatch data | drive jump/lookup table analysis |
| Vector-like target | absolute/vector store candidate not connected to accepted flow | drive vector backtracking |
| Runtime-copy-adjacent island | code-like bytes inside or near copied runtime source | drive ORG/runtime mapping |
| Callback-like island | code-like range near API inputs, app slots, or function tables | drive typed-flow/callback inference |

Required data analysis:

- scan unaccepted data ranges for plausible decode spans and terminal
  instructions using generated decode/effect metadata
- reject spans that overlap accepted code, known tables, strings, structured
  data, or platform-owned data unless a source/runtime map explains the overlap
- record why each candidate is not accepted yet
- correlate candidates with unresolved indirect jumps, lookup tables, vectors,
  callbacks, runtime copies, and absolute memory references; implemented for
  lookup-table-adjacent terminal islands as `jump_table` missing inbound and
  pointer-table-adjacent terminal islands as `callback`
- promote candidates only after a real inbound edge or explicit seed is found
- measure target signal counts before/after table/vector/ORG improvements

The intended improvement loop is:

```
find orphan signal
  -> identify likely missing inbound evidence
  -> improve generic/platform analysis
  -> accepted flow reaches the code
  -> orphan signal count decreases
```

This means a lower orphan count is only a gain when the candidate became reached
code through real analysis. Blind auto-conversion is not progress.

## Absolute Memory Plan

All absolute memory access should be classified by ownership before rendering:

| Class | Examples | Render goal |
| --- | --- | --- |
| ExecBase literal | `$4.w`, `$00000004` | usually keep `$4`; document as Amiga rule |
| CPU/vector table | `$10,$20,$68,$70,$80` | vector symbols plus discovered code target where proven |
| Hardware registers | `_custom`, `_ciaa`, `_ciab` ranges | generated platform field names |
| Display memory | bitplanes, sprite pointers, copper pointers | bitmap/copper labels tied to runtime memory ranges |
| Audio memory | AUDx pointer/length/sample source | sound sample labels and length evidence |
| Runtime copied code | ORG/runtime payload ranges | runtime labels with source/runtime mapping |
| Decompressed payload | RNC/BK/Tetragon outputs loaded at absolute addresses | extracted target load range and entrypoint |
| Bootstrap helper | low copied trampoline/helper code | symbol or suppressed weak range unless independently proven |
| Absolute globals | fixed RAM buffers, stacks, app state | named memory ranges when ownership is proven |
| Absolute lookup tables | tables whose entries target absolute ranges | symbolic labels or relative expressions by table kind |

Required data analysis:

- track absolute writes, reads, address loads, calls, and jumps; accepted
  absolute operands are now exposed as C `absolute_memory_ref` records
- attach each absolute address to a memory owner or leave it numeric
- merge copy/decompression outputs with runtime entrypoint discovery
- propagate hardware/display/audio sink types back to source data; implemented
  runtime-sink, palette-range, bootloader setup, and display/audio decisions use
  generated hardware symbol ids plus runtime-target kind/access enums, with
  strings kept for display/export text
- preserve exact reproduction while avoiding fragile addends
- expose all accepted and rejected absolute-memory candidates in the web UI

Current corpus measurement after adding accepted absolute operand records:

| Feature | Xrefs |
| --- | ---: |
| `memory-layout:record:absolute_memory_ref` | 40,698 |
| `memory-layout:kind:section_storage` | 25,925 |
| `memory-layout:kind:runtime_range` | 4,690 |
| `memory-layout:kind:cpu_vector` | 4,578 |
| `memory-layout:kind:absolute_memory` | 2,989 |
| `memory-layout:kind:hardware_register` | 1,343 |
| `memory-layout:kind:execbase_literal` | 1,159 |
| `memory-layout:kind:hardware_register_range` | 14 |

Conflict corpus evidence:

| Feature | Corpus xrefs |
| --- | ---: |
| `memory-layout:conflict` | 12,153 |
| `memory-layout:conflict_state:code_overlap` | 12,153 |

Comparator target evidence:

| Target | Absolute operand records |
| --- | ---: |
| Bloodwych | 1,232 |
| GenAm | 115 |
| MonAm | 84 |
| Magicland Dizzy | 1,595 |
| Conqueror main executable | 26 |

Runtime-view relationship corpus evidence after adding compact C relationship
fields:

| Feature | Corpus xrefs |
| --- | ---: |
| `runtime:view_related_range` | 6 |
| `runtime:view_relationship:contained_by_runtime_range` | 4 |
| `runtime:view_relationship:exits_to_larger_runtime_range` | 2 |

Observed comparators include Bloodwych/Bloodwych disk variants for contained
runtime views and Conqueror for exits into a stronger copied range.

Rejected table-bound corpus evidence:

| Feature | Corpus xrefs |
| --- | ---: |
| `table:candidate_unresolved:table_bounds` | 6 |
| `table:candidate_unresolved:table_bounds_status:rejected_insufficient_entries` | 6 |

Observed comparator: Damocles `c/ed` has three unresolved indexed direct-stub
candidate sites in both resource-manifest and promoted project-target views.

## Design Update Rule

`docs/design-m68k-analysis.md` is the tutorial companion to this plan. Each time
implementation starts on a planned item, update the design with:

- the user-facing problem
- the analysis fact shape
- a short assembly example
- a text diagram if address spaces or ownership are involved
- correctness gates and rejection cases

Do this before or during implementation, not after the behavior has drifted into
undocumented renderer heuristics.

## Open Checks Before Implementation

- Empty `LIB_SIZE` contexts in Starglider math libraries are resolved:
  resident autoinit sizes equal to `LIB_SIZE` render directly as `LIB_SIZE`,
  and no empty app layout is emitted.
- Large app layouts such as Carrier RNC, Starglider, and Voodoo still need
  stricter overlap checks against accepted code and non-app typed/platform
  struct ranges. Typed app-slot struct interiors no longer produce flat
  duplicate app fields.
- Absolute raw/decompressed targets have accepted operand and orphan-candidate
  memory-layout records; they still need load address, source extent, and entry
  range merged into the same higher-level target/load relationship model.
- Runtime-copy facts now record compact relationships when suppression is caused
  by a larger range, contained range, or runtime-copy overlay. Remaining work is
  target-level wrapper/helper/final-image grouping across imported disk targets.
- Existing alias emission is backed by explicit pre-render layout alias facts:
  sorted slot overlap is classified before emission, exported through
  `base_layout_field` records, and covered by the RSSET alias C tests.
- Lookup-table rendering still needs a single table fact model instead of
  scattered case-specific render behavior for unresolved/rejected candidates.
- Orphaned code signals have a first-class fact model for unresolved
  terminal-decode islands at accepted-code boundaries or data labels, plus
  suppressed structured-data overlap signals; target-level metrics and broader
  cause classification remain.
- The signal should be reconciled after jump/lookup table work: a good table
  improvement should turn some orphan candidates into reached code, not just hide
  them.
- Table candidate records now include rejected direct-stub bounds when the
  control operand proves the table base and the bounded scan is too weak to
  promote. Broader rejected-bound classes remain open.
- Bloodwych contains many already-rendered relative lookup tables; those are a
  useful proving target, but GenAm/MonAm and imported disk targets should remain
  comparators so Bloodwych does not become the hidden spec.

## Regression and Acceptance Checklist

- Includes stay in the include region, before RSSET and EQU/symbol regions.
- Conqueror-style weak `ORG $4` remains suppressed.
- Storage `loc_` labels and runtime `abs_` labels do not collide.
- Address `$4` is not rendered as an ordinary code location when it is ExecBase
  or a low vector/address.
- `_custom` offsets are not rendered as app slots.
- Installed interrupt/vector handlers are queued as code when their targets are
  proven.
- Copy/vector store recognition uses value backtracking, not fixed adjacent
  instruction pairs.
- Jump tables render symbolic target-base expressions when the calculation is
  proven.
- Orphaned code-like data is reported as a signal, not accepted as code, until an
  inbound edge or explicit seed proves it.
- Orphan signal counts are tracked before/after jump/table/vector/ORG analysis
  changes.
- Data/table classification does not overlap accepted code unless a
  source/runtime mapping proves it.
- Each generalized heuristic has an isolated test and at least one non-Bloodwych
  comparator where possible.
- Direct reproduction and source reassembly pass where supported.
