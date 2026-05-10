# M68K analysis plan: RSSET, absolute memory, and lookup tables

This plan records the current RSSET survey and expands the design target to
absolute memory, ORG/runtime views, bootstrapping, and lookup-table rendering.
It should be reviewed before more renderer changes are made.

Amiga-specific nuances are recorded in `docs/design-amiga.md`. In this plan,
those notes are treated as platform requirements that plug into the generic C
analysis model, not as target metadata or renderer-side guesses.

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

Keep this section editable. The table should stay as a short topic index:
current state, current gap, and where to add detail. Do not keep appending long
history paragraphs into table cells. New evidence, corpus measurements, and test
names should go in per-topic notes below the table or in the relevant survey
section, so future updates are small diffs rather than rewritten wall-of-text
rows.

Latest update: internal structured-data role consumers are flags-only. Role text
is parsed only when setting policy/import metadata and emitted only as display
text; render-plan rows, runtime-address refs, inferred runtime refs, listing
JSON/navigation, table records, orphan nearby-data context, and platform runtime
sink checks now consume numeric role flags directly. Orphan nearby-data relation
state is now a compact C enum and corpus indexing consumes the exported relation
id, not the display string. Resident node-type decisions now use generated Amiga
symbol ids for `NT_LIBRARY`, `NT_DEVICE`, and `NT_RESOURCE`; node-type names are
display/export text only. Render lookup base-field slots now carry an explicit
owner-kind byte, so app-base slot decisions use compact state rather than
comparing the `__amiga_app_base__` display symbol. Static `LIB_SIZE` decisions
use the generated `AMIGA_OS_SYMBOL_ID_LIB_SIZE`; name-based constant lookup is
kept only for arbitrary source-symbol output. Type-flow nearby OS-call lookups
now use xref kind ids for OS calls and call outputs plus feature-class ids for
concrete OS API features, so stale kind display text does not affect API-output
provenance. Type-flow numeric-access reports now also carry compact cause ids
and propagation-chain kind ids; report branching for app-slot substructure and
API-output storage gaps uses those ids, while cause/chain strings remain display
and grouping names. Corpus indexing for code-start-derived direct control stubs
and Amiga LoadSeg entries now uses numeric code-start reason ids rather than
`reason_name` display strings. Orphan missing-inbound work-item gating uses the
numeric orphan status id rather than status display text.

Round-trip source reproduction is a quality gate for retained rendered-source
updates. When regenerated target `.s` files are committed as evidence, the same
target must be reassembled and compared to the source binary; source-quality
changes without exact reproduction are regressions unless explicitly recorded as
unsupported container/format oddities.

| Topic | Status | Next gap |
| --- | --- | --- |
| RSSET/app slots | Implemented and tested | Track only new real ownership conflicts. |
| Typed structs vs app slots | Implemented and tested | Broaden only from mapped runtime/source-space evidence. |
| ORG/runtime views | Implemented for current copied-range evidence | Expand with future runtime-copy/decompression heuristics. |
| Lookup/jump tables | Active, broad heuristic coverage | Use unresolved C candidate statuses for the next work item. |
| Absolute memory | Implemented for current owner classes | Broaden imported-target coverage and display/audio layout inference. |
| Orphaned code | Signals implemented, promotion remains conservative | Reduce callback/vector/API/runtime-copy queues with real flow recovery. |
| Targets | Bloodwych plus GenAm/MonAm/comparators indexed | Add tags/evidence only for new generalized heuristics. |

### Topic Notes

Add future evidence as short bullets under the relevant topic. Keep corpus
measurements and test names here, not in the index table.

#### RSSET/app slots

- App-slot rendering rejects known hardware bases and `_custom` offsets.
- Policy RSSET regions carry explicit app-layout/storage-kind ids; static names
  are display text only.
- C source analysis records rendered base-layout fields, layout-kind ids, alias
  overlays, typed owner metadata, and listing JSON layout fields.
- Same-base, different-layout overlaps are conflict-marked in
  `memory_layout_records`.
- Section-relative platform storage effects are marked `code_overlap` only when
  their mapped target range intersects accepted code; base-relative app offsets
  are not compared to source-code offsets.
- Coverage: `test_source_analysis_memory_layout_marks_same_base_layout_overlap_conflicted`
  and `test_source_analysis_platform_storage_effect_conflicts_only_mapped_section_storage`.

#### Typed structs vs app slots

- Typed app-slot struct regions own their generated struct extent; interior
  offsets are blocked from flat RSSET output and render through typed fields
  where known.
- Resolved/unresolved platform typed accesses, platform storage writes, owner
  ranges, aggregate extents, and conflict states are exported as numeric C ids
  plus display names.
- Type-flow/report gates use compact kind/feature ids and feature-class ids,
  including dynamic typed/app classes such as platform struct fields and API
  argument reasons.
- Coverage includes `test_source_analysis_platform_typed_access_conflicts_with_non_app_layout`
  and manifest fixture coverage for id-backed type-flow report/gate paths.
- Generated zero-offset embedded struct fields now participate in prefix
  refinement when generated base-table evidence has no candidate. This keeps
  C analysis authoritative for cases such as `FindTask` returning `TC_Struct`
  while later `Process` tail fields prove the wider container. Coverage:
  `facts_v2_analysis_refines_zero_offset_embedded_struct_prefix`.
- The type-flow gate accepts many prior refinements resolving to one later typed
  access, but still rejects a resolved-after-refinement claim when the later row
  lacks a concrete `platform_typed_access:any` xref. Coverage:
  `test_type_flow_gate_accepts_many_refinements_to_one_typed_access` and
  `test_type_flow_gate_rejects_refinement_resolution_without_typed_access_row`.
- Prefix-refinement evidence instructions render their generated container field
  immediately only when the access size exactly matches the field start and
  size. Non-exact wider/narrower probes remain numeric while still refining
  later flow.
- Untyped app-slot API argument records now distinguish generated NDK semantic
  pointer facts from true metadata gaps. `STRPTR` inputs with generated
  `string_ptr` semantics report `string_ptr`; generated non-struct pointer
  types such as `WORD *` report `typed_pointer`; only address inputs without
  type or semantic metadata report `missing_pointer_metadata`.
- Temporary full usage rebuilds found 231 resolved and 248 unresolved typed
  memory-layout records, 2,163 owner-range examples, 3,584 owner-range xrefs,
  no current corpus `conflicted` typed owner-range rows, 36,989 xrefs with kind
  ids, 3,842 typed-flow exact feature ids, and 3,859 dynamic typed/app
  feature-class xrefs with no missing class ids.

#### ORG/runtime views

- Tests cover runtime-copy jump targets, low trampoline suppression, policy
  runtime ranges, conflict failure, policy-vs-inferred precedence, corpus tags,
  and listing navigation for materialized/suppressed runtime views.
- Runtime-absolute raw targets now pass load address, payload extent, and
  transfer entrypoint into C policy. C materializes the raw load range and
  runtime entrypoint before analysis, so extracted Pandora-style payloads render
  at their loaded address without target-local ORG metadata.
- Runtime-view materialization reason, relationship, and role decisions are
  numeric ids; names remain display text.
- Relationship ids derive target-pattern tags for entry wrappers, contained
  helpers, overlaid helpers, and final-image-related runtime views.
- A temporary full usage rebuild found 2 entry-wrapper views, 4 contained-helper
  views, and 6 final-image-related views across Bloodwych, Conqueror, and
  imported disk rows.

#### Lookup/jump tables

- Existing coverage includes long dispatch, word-relative dispatch, far targets,
  runtime-mapped dispatch, mixed labels/raw entries, pointer tables, relative
  `target-base` rendering, accepted `table_records`, and unresolved
  `table_candidate_records`.
- Table role/conflict/status data is carried as compact ids/flags; corpus
  indexing does not infer table classes from rendered comments or display text.
- Implemented recovery patterns include PC-indexed word dispatch, biased
  PC-indexed word dispatch, address-register indexed word dispatch with signed
  table displacement, direct indexed stub tables, interleaved key/stub tables,
  post-instruction variable branch stubs from intra-instruction expression
  bases, backward and forward inline-tail dispatch, keyed long relative
  dispatch, branch-terminated inline stubs, and PC-indexed absolute long
  dispatch rendering.
- `table_candidate_records` are now a strict subset of recovered indirect sites.
  Generic unresolved `jsr (aN)` / `jmp (aN)` remains in
  `recovered_indirect_sites` and `analysis:indirect_site` tags, but no longer
  pollutes table-candidate navigation unless expression-base, table-base, or
  table-bound evidence exists. Indexed indirect syntax alone remains an
  indirect-site diagnostic, not a table work item.
- Isolated coverage includes:
  `test_facts_v2_pc_indexed_word_load_promotes_relative_jump_targets`,
  `test_facts_v2_biased_pc_indexed_word_load_promotes_relative_jump_targets`,
  `test_facts_v2_address_indexed_word_load_uses_signed_table_displacement`,
  `test_facts_v2_direct_indexed_stub_table_promotes_entries`,
  `test_facts_v2_intra_instruction_index_base_promotes_post_instruction_variable_stubs`,
  `test_facts_v2_indexed_backward_inline_tail_promotes_entries`,
  `test_facts_v2_indexed_forward_inline_tail_promotes_entries`,
  `test_facts_v2_swapped_keyed_long_table_promotes_relative_targets`,
  `test_facts_v2_branch_terminated_indexed_stubs_promote_entries`,
  `test_facts_v2_interleaved_key_stub_table_promotes_entries`,
  `test_facts_v2_indexed_indirect_without_table_evidence_is_not_table_candidate`,
  `test_orphan_signal_features_use_status_id_for_suppressed_signal`, and
  `test_project_source_facts_v2_pc_indexed_absolute_long_dispatch_table_roundtrips`.
- Recent full usage rebuilds reduced unsupported table shapes to zero, removed
  lookup-table missing-inbound work items, and kept suppressed structured-data
  overlaps out of work queues. Next table work must start from newly observed
  unresolved C statuses, not suppressed data overlaps.
- Address-register indexed word dispatch was proven from GenAm/MonAm-style
  evidence (`lea table_base(pc),a1`; `move.w -disp(a1,dN.w),dN`;
  `jmp/jsr 0(a1,dN.w)`). Temporary full usage rebuild
  `tmp_target_usage_after_address_indexed_word_dispatch.jsonl` changed
  `table:candidate_unresolved` 13 -> 6 and
  `analysis:lookup_table:word_relative_labels` 32 -> 39. The accepted tables
  initially exposed five orphan-code `jump_table` missing-inbound signals, but
  follow-up inspection showed those were scalar lookup tables adjacent to
  terminal decode islands, not dispatch tables. Orphan missing-inbound
  classification now consumes table-kind ids and only relative/absolute
  code-dispatch tables can become `jump_table` work items; scalar lookup tables
  remain nearby-data context. `tmp_target_usage_after_orphan_table_kind_gate.jsonl`
  changed `target-pattern:orphan_missing_jump_table` 5 -> 0 while preserving
  `table:candidate_unresolved` at 6 and
  `analysis:lookup_table:word_relative_labels` at 39. Regenerated `GenAm` and
  `MonAm302` source now renders large formerly raw byte spans as code while
  keeping exact source reproduction.
- Follow-up inspection of the remaining six unresolved table candidates found
  only shape-only indexed indirect calls/jumps with no expression base, table
  base, or bounded table span: GenAm dynamic DOS vector calls, Damocles menu
  library-vector wrappers, Midwinter II dynamic dispatch, Workbench Calculator,
  and Atari Lattice C linker cases. C analysis now keeps those as generic
  `recovered_indirect_sites` but removes them from `table_candidate_records`.
  `tmp_target_usage_after_strict_evidence_table_candidates.jsonl` changed
  `table:candidate_unresolved` 6 -> 0 while preserving
  `analysis:indirect_site` at 302.

#### Absolute memory

- Tests cover ExecBase literal behavior, stack top EQU, interrupt/vector target
  stores, runtime aliases, relocation anchors, hardware sinks, and
  display/copper/audio sinks.
- LoadSeg pre-segment references are platform facts: Voodoo Nightmare `run`
  proves a PC-relative section-start-minus-four operand that must render as a
  section-start expression rather than as a freestanding negative `EQU`.
- Direct rebuild now trusts rendered HUNK anchor expressions instead of refusing
  only because analysis recorded an out-of-payload data relocation diagnostic.
  Carrier Command `ramdrive.device` proves this with
  `__section_0_base-$00000004` and exact direct rebuild.
- HUNK anchor classification, Atari normalized-addend handling, and Atari
  image-offset relocation targets are now platform facts consumed by generic
  relocation analysis, not platform checks embedded in the generic relocation
  resolver.
- ExecBase and Amiga hardware absolute-address ownership is resolved through
  `platform_facts_v2`, so generic M68K analysis does not apply Amiga `$4` or
  custom-chip ownership to other platforms.
- Generated Amiga hardware ids, symbol ids, vector/function ids, and runtime
  target/access enums drive hardware/platform decisions; strings are source and
  JSON display text only.
- C JSON exposes base-layout fields, runtime views, runtime-address refs,
  normalized ranges, accepted absolute operands, owner ids, conflict-state ids,
  and record-kind ids.
- Decompression rows expose grouped source/load/entry facts and id-backed
  derived-target metadata. A temporary full usage rebuild found 19 grouped
  source/load/entry facts across 9 rows and 2 checked-in decompressed child
  targets.

#### Orphaned code

- C analysis records unresolved terminal-decode islands at accepted-code
  boundaries or data labels without promoting them to accepted code.
- Nearby structured data carries role flags, source offset, distance, and
  relation id; lookup-table-adjacent islands, pointer-table/callback evidence,
  CPU/vector operands, API evidence, policy seeds, and metadata labels are
  classified from ids/flags.
- Corpus missing-inbound work queues are emitted only from status-gated
  unresolved signal records.
- Current target-pattern queues remain API and metadata. Callback,
  runtime-copy, jump-table, and vector examples are either promoted from real
  flow evidence or kept as context without becoming missing-inbound work items.
- Relocation-backed function pointer tables now seed callback/function targets
  in C after the first reachable pass, gated by accepted-code overlap, code
  target validity, contiguous long relocations, and at least two entries. This
  turns proven table targets into rendered code instead of orphan/data islands.
  Coverage: `test_facts_v2_relocation_pointer_table_promotes_callback_targets`.
- Terminal indirect dispatches can now promote a pushed forward continuation
  address when the same site also resolves at least one real indirect target.
  The stack value must come from direct address-sized stack-push provenance, the
  jump must be terminal, and the target must be a forward same-section code
  candidate rather than an accepted-code interior byte. Bloodwych proves the
  pattern with `pea abs_0_00008226; ...; jmp (a0)`, matching the hand source's
  `adrL_008226` continuation and converting `abs_0_00008226` and the reached
  `abs_0_00006D3C` from data to code. Coverage:
  `facts_v2_terminal_indirect_jump_promotes_pushed_continuation`.
- Pointer-table adjacency alone is no longer classified as callback inbound
  evidence for orphaned code. Proven callback/function entries are promoted by
  relocation-backed pointer-table analysis; an orphan island merely adjacent to
  pointer data remains an unresolved signal with nearby-data context. This keeps
  the work queue focused on real missing flow rather than layout proximity.
  Coverage:
  `facts_v2_orphan_signal_keeps_overlapping_pointer_table_inbound_unknown` and
  `facts_v2_orphan_signal_keeps_following_pointer_table_inbound_unknown`.
- Runtime-view membership alone is no longer classified as runtime-copy inbound
  evidence for orphaned code. Runtime views describe address-space context; they
  prove missing runtime-copy flow only when a real control/reference edge proves
  the island is entered. Coverage:
  `facts_v2_orphan_signal_keeps_runtime_view_inbound_unknown_without_control_ref`.

#### Targets

- Bloodwych remains the proving target, with GenAm/MonAm and real corpus rows as
  comparators for generalized heuristics.
- Pandora demonstrates wrapper load versus final copied image; Conqueror
  demonstrates weak low ORG risk; Carrier stresses packed/runtime-copy
  ambiguity.
- `resources/clone_amiga/Bloodwych-68k/asm/BLOODWYCH439_relabel.asm` is
  comparison material for locating Bloodwych data/source-reference opportunities
  only. It is not an oracle and must not drive target-specific logic.
- Bloodwych runtime-view orphan comparison points from that hand source:
  `adrEA003E0B` and `adrEA003E7B` are message/data bytes despite plausible
  terminal decodes, while `adrCd006D3C` and the disk routine near `adrCd0086DE`
  are real code. The work item is therefore evidence separation: suppress or
  downgrade candidates backed by data/table/string provenance, and promote only
  candidates with a real inbound edge or reusable runtime-copy/control-flow
  proof.

### Recent Topic Notes

- Lookup/jump tables: added isolated exact-rebuild coverage for PC-indexed
  absolute long dispatch tables with `movea.l table(pc,dN.w),aN` feeding
  `jmp (aN)`. This protects the general C heuristic seen near the Starglider
  callback queue without making Starglider the hidden spec.
- OS/API analysis: indexed vector wrapper lookup, base-field library/device
  slots, and global base slots now store generated Amiga library/base ids for
  semantic decisions. Library/base names remain source/export text, not the
  semantic key.
- Orphan/code discovery: relocation-backed function pointer tables now promote
  valid callback/function targets in C. Full target-usage rebuild against the
  previous orphan-summary baseline reduced callback orphan signals from 5 to 1
  and target rows from 3 to 1; Starglider project/corpus callback rows dropped
  to 0, Midwinter II dropped from 3 to 1, vector rows dropped from 31 to 22,
  API rows from 10 to 8, and metadata rows from 219 to 204. Reproduction status
  counts did not change.
- Orphan/code discovery: relocated immediate code addresses loaded into address
  registers now retain relocation provenance through trace state, so later
  `jsr (aN)` / `jmp (aN)` can queue the cross-section target as accepted code.
  This is gated by generated MOVE metadata, a relocated immediate source,
  address-register destination, even code-section target, decodability, and no
  accepted-code interior overlap. The isolated regression is
  `facts_v2_relocated_indirect_call_promotes_cross_section_target`.
- Runtime-copy entry discovery: runtime-address references to a copied range
  start now seed code only when the source operand is a generated control
  target. Non-control address loads can still create labels and diagnostics, but
  they do not prove an entrypoint. Coverage:
  `facts_v2_orphan_signal_suppresses_non_control_runtime_address_ref`.
  Bloodwych runtime-copy orphan diagnostics now separate the hand-source mixed
  cases: `adrEA003E0B`, `adrEA003E7B`, `adrEA007C6F`, and `adrB_00EEDF`
  suppress as metadata/data-address labels, while the real code-boundary
  candidates at source offsets `0x6998`, `0x833A`, and `0x83F6` remain
  unresolved runtime-copy work items. Magicland Dizzy drops its two unresolved
  runtime-copy orphan signals to zero under the same control-target gate.
- Orphan/code discovery: required linkage labels that start short terminal
  Amiga API wrapper sequences now seed code with `linkage_api_entry`
  provenance. Generic analysis asks platform facts whether linkage API entry
  labels and LVO API matching are supported; Amiga owns the generated LVO
  metadata. This is gated by required label provenance, terminal decode, and no
  accepted-code overlap; unlabelled API-looking islands remain orphan signals.
  Coverage:
  `facts_v2_linkage_label_api_wrapper_promotes_code` and
  `test_real_dll_starglider_mathtrans_linkage_api_labels_promote_wrappers`.
- Memory ownership/orphan diagnostics: relocated absolute operands no longer
  become CPU-vector evidence solely because their relocation addend is a low
  number such as `$10` or `$14`. The C/render analysis keeps relocation
  provenance and classifies those operands as section storage; unrelocated
  vector-slot writes still classify as vectors. The isolated regression is
  `facts_v2_orphan_signal_does_not_treat_relocated_low_offset_as_vector`.
- Orphan/code discovery: pushed forward continuations for terminal indirect
  dispatch are now accepted as code only when stack provenance and resolved
  dispatch targets agree. Temporary corpus rebuild against
  `tmp_target_usage_after_control_runtime_entry.jsonl` found
  `analysis:stack_continuation_entry` in 6 Amiga rows / 6 entries, including
  Bloodwych and Damocles, and removed a weaker backward Devpac candidate that
  landed inside an existing instruction. Bloodwych unresolved orphan-code
  signals dropped from 3 to 2; exact Bloodwych render kept 0 instruction-byte
  mismatches and 0 numeric runtime refs.
- Targets: `resources/clone_amiga/Bloodwych-68k/asm/BLOODWYCH439_relabel.asm`
  is available as comparison material for Bloodwych data/source-reference
  investigation only. It must not drive target-specific logic.

Past decisions to preserve:

- C analysis is authoritative; Python/UI consume facts only.
- Do not hardcode M68K instruction knowledge; use generated decode/effect data.
- Do not emit `ORG` or labels merely to make output prettier.
- Any regenerated checked-in `.s` file must reassemble as a standalone source
  file with exact payload and relocation semantics. Full-file exactness is
  required when the container encoding has no known hunk-structure oddity; when
  the only mismatch is relocation encoding shape, record it explicitly.
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

Latest temporary target-usage rebuild after runtime-view role indexing:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage.jsonl --xrefs-output src\build\tmp_target_usage_xrefs.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets.jsonl --variants-output src\build\tmp_target_variant_index.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields.jsonl --workers 8`
- Scope: 493 entries, 488882 xrefs, 420647 snippet rows, 316 type-flow rows.
- Orphan inbound evidence found: `api` in 18 targets / 47 signals, `vector`
  in 33 targets / 187 signals, `jump_table` in 7 targets / 16 signals, and
  `callback` in 3 targets / 5 signals.
- Real API examples include Workbench `c/SetPatch`, MonAm302, and Starglider
  extracted libraries, so the classifier is not Bloodwych-specific.

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
     hardware setup, mixed: implemented as explicit C structured-data table
     metadata for scalar, pointer, relative-code-dispatch, and
     absolute-code-dispatch structured tables; JSON exports these ids and no
     longer reclassifies table kind from display fields
   - base expression: table label, section base, runtime base, PC, or explicit
     data label: implemented as explicit C structured-data table metadata for
     target-label/table-label classification; JSON exports these ids and no
     longer derives the base expression at export time
   - entry target range and null/sentinel rules: target base recorded when
     known
   - confidence and conflict state: implemented for clean/code-overlap table
     records with numeric C enum ids on the C structured-data item; JSON exports
     those fields and no longer checks accepted-code overlap for table records
   - rejected table bounds on unresolved candidates: implemented for proven
     direct-stub spans rejected for insufficient entries; corpus consumers use
     C enum ids for recovered indirect flow, shape, status, source pattern, and
     table-bounds status rather than display strings
   - unresolved table-candidate identity: implemented as C recovered-indirect
     site metadata (`is_table_candidate`, source-pattern id, conflict-state id);
     JSON exports those fields and no longer decides which indirect sites are
     table candidates

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
     terminal-decode islands that overlap accepted structured data; linked and
     promoted classes remain planned
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
  lookup-table-adjacent terminal islands as `jump_table` missing inbound,
  pointer-table-adjacent terminal islands as `callback`, and absolute
  vector-slot operands inside orphan islands as `vector`
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
| LoadSeg segment link | `section_start-4(pc)` | section-start expression, not standalone `EQU -4` |
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

Current corpus measurement after adding accepted absolute operand records and
section-relative storage conflict checks:

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

Platform storage conflict evidence from the temporary full manifest rebuild:

| Storage effect | Clean xrefs | Code-overlap xrefs |
| --- | ---: | ---: |
| `write_base_slot` | 19 | 0 |
| `write_typed_slot` | 34 | 0 |
| `write_global_base_slot` | 13 | 53 |
| `write_typed_global_slot` | 15 | 94 |

This validates that base-relative app slots are not compared to source-code
offsets, while section-relative global storage is conflict-marked when its
mapped target range overlaps accepted code.

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
| `runtime:view_role:contained_helper` | 4 |
| `runtime:view_role:entry_wrapper` | 2 |
| `runtime:view_role:final_image_related` | 6 |
| `target-pattern:runtime_contained_helper` | 4 |
| `target-pattern:runtime_entry_wrapper` | 2 |

Observed comparators include Bloodwych/Bloodwych disk variants for contained
runtime views and Conqueror for exits into a stronger copied range.

Rejected table-bound corpus evidence:

| Feature | Corpus xrefs |
| --- | ---: |
| `table:candidate_unresolved:table_bounds` | 13 |
| `table:candidate_unresolved:table_bounds_status:rejected_code_overlap` | 7 |
| `table:candidate_unresolved:table_bounds_status:rejected_insufficient_entries` | 6 |

Observed comparator: Damocles `c/ed` has three unresolved indexed direct-stub
candidate sites in both resource-manifest and promoted project-target views;
Conqueror/Bloodwych-style code-overlap spans are rejected rather than hidden.

Relocated immediate indirect-control corpus evidence after adding cross-section
trace provenance:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_relocated_indirect_cross_section.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_relocated_indirect_cross_section.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_relocated_indirect_cross_section.jsonl --variants-output src\build\tmp_target_variant_index_after_relocated_indirect_cross_section.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_relocated_indirect_cross_section.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_relocated_indirect_cross_section.jsonl --workers 8`
- Scope: 493 entries, 566166 xrefs, 476716 snippet rows, 322 type-flow rows.
- Carrier `info.library_3fb9d33a`: orphan signals 3 -> 1, vector-missing
  orphan signals 2 -> 0, OS call xrefs 38 -> 41.
- Starglider `info.library_3fb9d33a`: orphan signals 3 -> 1,
  vector-missing orphan signals 2 -> 0, OS call xrefs 38 -> 41.
- Damocles `printer.device_1aada1d4`: orphan signals 2 -> 1,
  vector-missing orphan signals 1 -> 0, label definitions 928 -> 944.
- Direct rebuild exactness passed for all three affected promoted targets.

Relocated operand memory-owner corpus evidence after preventing low relocation
addends from becoming vector ownership:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_relocated_memory_owner.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_relocated_memory_owner.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_relocated_memory_owner.jsonl --variants-output src\build\tmp_target_variant_index_after_relocated_memory_owner.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_relocated_memory_owner.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_relocated_memory_owner.jsonl --workers 8`
- Scope: 493 entries, 546467 xrefs, 476716 snippet rows, 322 type-flow rows.
- False vector-missing orphan signals dropped 17 -> 0 across Workbench
  `Pipe-Handler`, `NoFastMem`, `CMD`, `Preferences`, `mathieeedoubtrans.library`,
  and Starglider `mathtrans.library`.
- CPU-vector memory-owner xrefs dropped 6028 -> 825 while absolute-memory-ref
  records stayed at 52136; section-storage xrefs rose 34846 -> 43616. This is
  ownership reclassification, not hidden data removal.

Strict table-candidate corpus evidence after separating generic indirect sites
from table-shaped work items:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_strict_table_candidates.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_strict_table_candidates.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_strict_table_candidates.jsonl --variants-output src\build\tmp_target_variant_index_after_strict_table_candidates.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_strict_table_candidates.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_strict_table_candidates.jsonl --workers 8`
- Scope: 493 entries, 515996 xrefs, 476716 snippet rows, 322 type-flow rows.
- `analysis:indirect_site` stayed 4936 -> 4936, preserving the generic indirect
  control queue.
- `table:candidate_unresolved` dropped 4385 -> 32; remaining table candidates
  are indexed/table-shaped (`table:candidate_unresolved:shape:index.brief`
  stayed 32 -> 32), while plain indirect-shaped table tags dropped 4353 -> 0.
- The largest visible queue reductions are in Workbench/Carrier/Starglider
  `info.library`, `printer.device`, `Preferences`, and other library/vector
  style call sites that were not proven lookup tables.

Table-base gate evidence after rejecting bases inside the consuming instruction:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_table_base_gate.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_table_base_gate.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_table_base_gate.jsonl --variants-output src\build\tmp_target_variant_index_after_table_base_gate.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_table_base_gate.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_table_base_gate.jsonl --workers 8`
- Scope: 493 entries, 515988 xrefs, 476716 snippet rows, 322 type-flow rows.
- `analysis:indirect_site` stayed 4936 -> 4936 and
  `table:candidate_unresolved` stayed 32 -> 32, so indexed-control candidates
  remain visible.
- `table:candidate_unresolved:table_base` dropped 8 -> 0. The removed bases
  were the control instruction's own extension word, not real external table
  starts, in Atari Devpac `GEN/MON/AMON` variants and project GenAm/MonAm
  targets.
- Follow-up implementation keeps that provenance as
  `expression_base_offset` on recovered indirect sites and table-candidate JSON,
  while `table_offset` remains reserved for real external table data.
- Corpus after the split: `table:candidate_unresolved:expression_base`
  0 -> 8, `table:candidate_unresolved:table_base` stayed 0 -> 0,
  `table:candidate_unresolved` stayed 32 -> 32, and accepted lookup-table
  label rendering stayed unchanged.
- Post-instruction variable branch-stub recovery now consumes those eight
  expression-base candidates when the bytes after the indexed control
  instruction decode as at least two nonfallthrough branch stubs. Corpus after
  this change: `analysis:indirect_site:status:jump_table` 551 -> 559,
  `table:candidate_unresolved` 32 -> 24,
  `table:candidate_unresolved:expression_base` 8 -> 0, orphan-code signals
  924 -> 911, reproduction-exact targets stayed 38 -> 38, and status-ok targets
  stayed 486 -> 486.
- Affected real targets include project GenAm and MonAm plus six Atari Devpac
  `GEN/MON/AMON` variants. Regenerated checked-in source demonstrates the
  visible gain: GenAm and MonAm render the post-instruction branch stubs as
  labels and `bra.*` instructions instead of opaque `dc.b` data after
  `jmp $0(pc,d0.w)`.
- Source-refresh reproduction gate: `targets/amiga_hunk_genam/genam.s`
  reassembles full-file exact; `targets/amiga_hunk_monam302/monam302.s`
  reassembles payload-exact and relocation-semantics exact, with only hunk
  relocation encoding shape differing.

Linkage API entry corpus evidence:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_linkage_api_entry.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_linkage_api_entry.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_linkage_api_entry.jsonl --variants-output src\build\tmp_target_variant_index_after_linkage_api_entry.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_linkage_api_entry.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_linkage_api_entry.jsonl --workers 8`
- Compared with `tmp_target_usage_after_post_instruction_stub_table.jsonl`,
  `target-pattern:orphan_missing_api` dropped 11 rows / 11 signals -> 4 rows /
  4 signals; `orphan-code:missing_inbound:api` dropped 11 rows / 18 signals ->
  4 rows / 5 signals. Callback, runtime-copy, and table-candidate queues were
  unchanged.
- Real affected comparator: Starglider `libs/mathtrans.library` section 15 now
  renders the required labelled wrapper at `$14` as instructions instead of
  `dc.b`; direct source rebuild remains exact.

Runtime-copy DBCC counter evidence:

- C analysis now looks forward from postincrement copy instructions for a DBCC
  loop whose generated metadata identifies the counter register and whose branch
  target covers the copy instruction. The traced value of that register defines
  the copied range length; this removes the old D0-only assumption for DBCC
  loops.
- Isolated regression:
  `facts_v2_runtime_copy_size_uses_following_dbcc_register` uses a D3 DBCC copy
  loop and verifies the runtime view size is 4 bytes, not the remaining section
  size.
- Corpus command:
  `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_dbcc_copy_counter.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_dbcc_copy_counter.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_dbcc_copy_counter.jsonl --variants-output src\build\tmp_target_variant_index_after_dbcc_copy_counter.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_dbcc_copy_counter.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_dbcc_copy_counter.jsonl --workers 8`
- Scope: 493 entries, 515815 xrefs, 476678 snippet rows, 322 type-flow rows.
- Compared with `tmp_target_usage_after_linkage_api_entry.jsonl`,
  `runtime:copied_code` increased 68 -> 70 and `runtime:view` increased
  68 -> 70. The unresolved runtime-copy orphan queue stayed 6 rows / 6 target
  patterns, so this is a range-quality improvement rather than an orphan queue
  reduction.
- Real affected targets: Carrier Command gains one copied-code runtime view and
  renders the `$c0` copied helper bytes as instructions; Starglider collapses a
  huge fallback copied range from 313744 bytes to 32 bytes; Voodoo Nightmare
  tightens a copied range from 5290 bytes to 5195 bytes.
- Regenerated checked-in source/benchmarks for Carrier Command and Starglider,
  plus the Pandora extracted raw target benchmark after the accepted change.

Runtime-copy decrement/branch and runtime-address label evidence:

- C analysis now recognizes postincrement copy loops followed by explicit
  decrement-and-branch control, using generated instruction metadata for the
  decrement and branch target instead of fixed instruction adjacency. Long
  counters use the full traced register value, not the low word.
- Runtime-address reference labels from `movea #abs,An` are provenance-first:
  accepted code/control/hardware sink refs still labelize, but plain address
  loads only force labels when the target maps through a discovered copied
  runtime range and later accepted instructions prove the loaded register is a
  pointer. Raw load-address translations alone do not create source labels.
- Amiga hardware runtime-address sinks now mark materialized source labels for
  long immediates written directly to generated hardware sink registers, and
  rendering reuses already-proven materialized labels for weaker immediate
  loads without creating new labels.
- Isolated C coverage:
  `facts_v2_runtime_copy_size_uses_decrement_branch_counter` and
  `facts_v2_runtime_movea_pointer_use_labels_materialized_target`.
- Real target coverage: Pandora extracted BK payload now keeps only the final
  `ORG $10000` image plus the bounded post-copy `ORG $55370`, removes the
  spurious `ORG $5548F`, removes false raw-load labels
  `loc_0_00057800`/`loc_0_00057D00`, renders
  `movea.l #abs_0_0001C3A8,a0` for a copied-image table base, and renders
  `move.l #abs_0_0005D5DE,bltapt(a5)` for a blitter source pointer.
- Targeted pytest coverage extends
  `test_real_dll_pandora_bootstrap_does_not_promote_zero_padding_as_code` to
  guard the real Pandora rendering behavior. Regenerated benchmark:
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
  in 0.82s with exact direct/source reproduction retained.

Actionable unresolved orphan missing-inbound corpus evidence after gating
suppressed signals out of work-item tags:

| Feature | Target rows | Signals |
| --- | ---: | ---: |
| `target-pattern:orphan_missing_api` | 4 | 4 |
| `target-pattern:orphan_missing_callback` | 0 | 0 |
| `target-pattern:orphan_missing_jump_table` | 0 | 0 |
| `target-pattern:orphan_missing_metadata` | 208 | 208 |
| `target-pattern:orphan_missing_runtime_copy` | 0 | 0 |
| `target-pattern:orphan_missing_vector` | 0 | 0 |

Examples include unlabelled MonAm/Starglider API candidates. Bloodwych
runtime-view orphan islands remain navigable as runtime-view context, but no
longer become runtime-copy work items without control-flow proof. The former
Midwinter II callback row is kept as nearby pointer-table context, not a
callback work item, because no table entry or control edge proves inbound flow.
The previous jump-table-adjacent examples were suppressed hex-character lookup
table overlaps and are no longer work items.

Pointer-table orphan-context corpus evidence:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_pointer_table_orphan_context.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_pointer_table_orphan_context.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_pointer_table_orphan_context.jsonl --variants-output src\build\tmp_target_variant_index_after_pointer_table_orphan_context.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_pointer_table_orphan_context.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_pointer_table_orphan_context.jsonl --workers 8`
- Scope: 493 entries, 490676 xrefs, 464170 snippet rows, 320 type-flow rows.
- Compared with `tmp_target_usage_after_strict_evidence_table_candidates.jsonl`,
  `orphan-code:missing_inbound:callback` dropped 1 -> 0, while
  `orphan-code:nearby_data:pointer_table` stayed 1 -> 1 and
  `orphan-code:signal` stayed 902 -> 902.

Runtime-view orphan-context corpus evidence:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_runtime_view_orphan_context.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_runtime_view_orphan_context.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_runtime_view_orphan_context.jsonl --variants-output src\build\tmp_target_variant_index_after_runtime_view_orphan_context.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_runtime_view_orphan_context.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_runtime_view_orphan_context.jsonl --workers 8`
- Scope: 493 entries, 490676 xrefs, 464170 snippet rows, 320 type-flow rows,
  43 unresolved typed-field rows.
- Compared with `tmp_target_usage_after_pointer_table_orphan_context.jsonl`,
  `orphan-code:missing_inbound:runtime_copy` dropped 10 -> 0 and
  `target-pattern:orphan_missing_runtime_copy` dropped 4 rows / 4 signals -> 0,
  while `orphan-code:context:runtime_view` stayed 10 -> 10,
  `orphan-code:signal` stayed 902 -> 902, and
  `analysis:pointer_table:long_label_entries` stayed 6908 -> 6908.
- Type-flow check:
  `python -m src.scripts.target_usage_manifest type-flow-check --type-flow-report src\build\tmp_target_type_flow_report_after_runtime_view_orphan_context.jsonl --unresolved-typed-fields src\build\tmp_target_unresolved_typed_fields_after_runtime_view_orphan_context.jsonl --xrefs src\build\tmp_target_usage_xrefs_after_runtime_view_orphan_context.jsonl --output src\build\tmp_type_flow_check_after_runtime_view_orphan_context.json`
  reported `ok: true` and `violation_count: 0`.

Zero-offset embedded struct prefix-refinement corpus evidence:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_zero_offset_prefix_struct.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_zero_offset_prefix_struct.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_zero_offset_prefix_struct.jsonl --variants-output src\build\tmp_target_variant_index_after_zero_offset_prefix_struct.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_zero_offset_prefix_struct.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_zero_offset_prefix_struct.jsonl --workers 8`
- Scope: 493 entries, 491480 xrefs, 464176 snippet rows, 320 type-flow rows,
  39 unresolved typed-field rows.
- Compared with `tmp_target_usage_after_runtime_view_orphan_context`, Process
  prefix refinements rose 0 -> 126, Process prefix candidates rose 0 -> 126,
  typed accesses rose 1742 -> 2045, unresolved typed-field report rows dropped
  43 -> 39, and orphan/table counts stayed unchanged
  (`orphan-code:signal` 902 -> 902,
  `analysis:pointer_table:long_label_entries` 6908 -> 6908).
- Real comparator evidence includes Carrier Command `c/More`, Search for the
  King, and matching platform-file manifest rows. These show `TC_Struct`
  pointers refined to `Process` and later rendered as fields such as `pr_CLI`
  and `pr_WindowPtr`.
- Type-flow check:
  `python -m src.scripts.target_usage_manifest type-flow-check --type-flow-report src\build\tmp_target_type_flow_report_after_zero_offset_prefix_struct.jsonl --unresolved-typed-fields src\build\tmp_target_unresolved_typed_fields_after_zero_offset_prefix_struct.jsonl --xrefs src\build\tmp_target_usage_xrefs_after_zero_offset_prefix_struct.jsonl --output src\build\tmp_type_flow_check_after_zero_offset_prefix_struct.json`
  reported `ok: true`, `violation_count: 0`, and 145 applied refinements.

Exact prefix-evidence rendering corpus evidence:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_exact_prefix_evidence_render.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_exact_prefix_evidence_render.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_exact_prefix_evidence_render.jsonl --variants-output src\build\tmp_target_variant_index_after_exact_prefix_evidence_render.jsonl --type-flow-report-output src\build\tmp_target_type_flow_report_after_exact_prefix_evidence_render.jsonl --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_exact_prefix_evidence_render.jsonl --workers 8`
- Scope: 493 entries, 493736 xrefs, 464193 snippet rows, 320 type-flow rows,
  39 unresolved typed-field rows.
- Compared with `tmp_target_usage_after_zero_offset_prefix_struct`, typed
  accesses rose 2045 -> 3032 and prefix-refinement typed-access provenance rose
  138 -> 279. Refinement counts, unresolved typed-access counts, orphan-code
  signals, and pointer-table label counts stayed stable.
- Type-flow check:
  `python -m src.scripts.target_usage_manifest type-flow-check --type-flow-report src\build\tmp_target_type_flow_report_after_exact_prefix_evidence_render.jsonl --unresolved-typed-fields src\build\tmp_target_unresolved_typed_fields_after_exact_prefix_evidence_render.jsonl --xrefs src\build\tmp_target_usage_xrefs_after_exact_prefix_evidence_render.jsonl --output src\build\tmp_type_flow_check_after_exact_prefix_evidence_render.json`
  reported `ok: true`, `violation_count: 0`, and 145 applied refinements.
- Regenerated Search for the King `king_481902ec.s` now reflects current code
  discovery plus exact prefix-field rendering such as `pr_WindowPtr(a0)`.
  Direct rebuild compare reported `direct_compare_status: full_file_exact`,
  `direct_compare_payload_exact: true`, and relocation semantics exact.

App-slot API argument classification evidence:

- Command: `python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_manifest_after_app_arg_reason.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_app_arg_reason.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_app_arg_reason.jsonl --type-flow-report-output src\build\tmp_type_flow_report_after_app_arg_reason.json --workers 8`
- Scope: 493 entries, 493736 xrefs, 464193 snippet rows, 320 type-flow rows.
- Compared with `tmp_target_usage_xrefs_after_exact_prefix_evidence_render`,
  app-slot API arg count stayed 3; `missing_struct_metadata` dropped 3 -> 0;
  generated NDK semantic reasons are now `string_ptr` 2 and `typed_pointer` 1.
- Real comparator evidence is MonAm302: `RawKeyConvert A1` and `Text A0`
  classify as `string_ptr`; `PolyDraw A0` classifies as `typed_pointer`.
- Type-flow check on `tmp_type_flow_report_after_app_arg_reason.json` reported
  `ok: true`, `violation_count: 0`, and no metric regressions.

API input preserved-alias typing evidence:

- Gap: generated API input metadata typed the scratch argument register, but
  source values kept in preserved address registers stayed numeric after calls
  such as `movea.l a2,a1; jsr _LVOInitRastPort(a6); move.w $003A(a2),d0`.
- C typed-flow now tracks plain address-register aliases and applies generated
  Amiga API input struct types back to preserved alias sources only when the
  platform calling convention says the source register survives the call.
- Isolated tests:
  `test_facts_v2_analysis_propagates_api_input_type_through_preserved_alias`
  and
  `test_facts_v2_analysis_does_not_propagate_api_input_type_through_scratch_alias`.
- Command: `uv run python -m src.scripts.target_usage_manifest build --output src\build\tmp_target_usage_after_api_input_alias.jsonl --xrefs-output src\build\tmp_target_usage_xrefs_after_api_input_alias.jsonl --snippet-rows-output src\build\tmp_target_usage_snippets_after_api_input_alias.jsonl --variants-output src\build\tmp_target_variant_index_after_api_input_alias.jsonl --type-flow-report-output src\build\tmp_type_flow_report_after_api_input_alias.json --unresolved-typed-field-report-output src\build\tmp_target_unresolved_typed_fields_after_api_input_alias.jsonl --workers 8`
- Scope: 493 entries, 494140 xrefs, 464201 snippet rows, 320 type-flow rows,
  42 unresolved typed-field rows.
- Compared with `tmp_type_flow_report_after_app_arg_reason`, resolved typed
  accesses rose 430 -> 453, numeric address-register accesses without type
  dropped 57686 -> 57660, and `typed_access_provenance:api_input` rose 0 -> 23.
- Comparator evidence:
  Damocles `c/ed` now renders `rp_TxWidth(a2)`, `rp_TxHeight(a2)`,
  `rp_TxBaseline(a1)`, and `rp_Mask(a2)` from `InitRastPort`/`InitBitMap`
  input aliases. Workbench/FF and two platform-file hunk comparators show the
  same generated API-input alias behavior for `RastPort` and `IO` fields.
- Type-flow check:
  `uv run python -m src.scripts.target_usage_manifest type-flow-check --type-flow-report src\build\tmp_type_flow_report_after_api_input_alias.json --unresolved-typed-fields src\build\tmp_target_unresolved_typed_fields_after_api_input_alias.jsonl --xrefs src\build\tmp_target_usage_xrefs_after_api_input_alias.jsonl --output src\build\tmp_type_flow_check_after_api_input_alias.json`
  reported `ok: true`, `violation_count: 0`, and no metric regressions.

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
  by a larger range, contained range, or runtime-copy overlay. Corpus target
  rows tag entry-wrapper, contained-helper, and final-image-related runtime
  views from numeric relationship ids. Broader imported-target coverage should
  be extended as new runtime-copy/decompression heuristics land.
- Existing alias emission is backed by explicit pre-render layout alias facts:
  sorted slot overlap is classified before emission, exported through
  `base_layout_field` records, and covered by the RSSET alias C tests.
- Accepted lookup/pointer table records now use explicit C table metadata on the
  structured-data item. Unresolved/rejected table candidates now carry explicit
  C candidate metadata on recovered indirect sites; direct-stub rejected-bound
  classes feed the same model.
- Orphaned code signals have a first-class fact model for unresolved
  terminal-decode islands at accepted-code boundaries or data labels, plus
  suppressed structured-data overlap signals; target-level missing-inbound
  target-pattern tags now identify jump-table, callback, vector, API,
  runtime-copy, and metadata queues for later implementation cycles.
- The signal should be reconciled after jump/lookup table work: a good table
  improvement should turn some orphan candidates into reached code, not just hide
  them.
- Table candidate records now include rejected direct-stub bounds when the
  control operand proves the table base and the bounded scan is too weak to
  promote. First-entry unsupported/undecoded direct-stub candidates now also
  carry explicit rejected bounds, so rejected-bound classes feed one candidate
  model instead of relying on status-only partial records.
- Bloodwych contains many already-rendered relative lookup tables; those are a
  useful proving target, but GenAm/MonAm and imported disk targets should remain
  comparators so Bloodwych does not become the hidden spec.
- Voodoo Nightmare `run` uses the Amiga segment base/linkage address to compute
  and jump to code in another loaded segment. The current model recognizes the
  standard local LoadSeg-link helper through Amiga platform logic and promotes
  the resolved segment body as a C-owned code entrypoint. The generic trace
  engine now only asks whether the active platform supports LoadSeg segment
  chains; the Amiga platform layer owns that answer and the symbol provenance
  for section-start-minus-four anchor rendering. Target usage indexing tags
  these entries as `analysis:platform_loadseg_entry` and
  `target-pattern:platform_loadseg_entry`. A corpus manifest run found this in
  Voodoo Nightmare `run` platform/project targets; broader helper variants still
  need comparator coverage.

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
- Relocated immediate code addresses loaded into address registers can promote
  indirect call/jump targets only through relocation provenance and generated
  MOVE metadata.
- Relocated low-offset operands are section-storage references, not vector
  evidence; unrelocated vector-slot operands remain vector evidence.
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
