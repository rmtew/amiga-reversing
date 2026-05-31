# Proposal 032: Source Quality Analysis Hardening

Status: proposed.

Proposal 027 makes decompression reliable by executing target-owned native
decompressors and capturing the bytes they write. This proposal handles the
next failure layer: correct bytes can still become wrong source when analysis
assigns false meaning to them.

The rule is:

```text
native execution proves bytes
C analysis proves meaning
Source Rendering presents proven meaning
Python indexes and displays proven facts
```

Python must not decide whether bytes are code, whether a low address is a CPU
vector, whether an absolute address belongs to a range, whether a table owns
targets, or whether a generated label is justified. Those are source-quality
decisions and belong in C analysis.

## Tutorial: The Problem

Damocles Tetragon payload 2 originally looked like failed decompression. The
entrypoint decoded into legal-looking M68K, but the code was unrealistic and
quickly degraded into data:

```asm
abs_0_00059484:
    or.b d0,(a2)+
    andi.w #139,$6311(a0)
    dc.b $43,$0B,$01,$01,$0C,$00,$44,$00
```

Proposal 027 fixes that class by executing the native decompressor:

```text
Damocles parent bytes
  -> execute target-owned Tetragon unpacker
  -> capture writes into the materialized child image
  -> analyze final child load address and entrypoint
```

Conqueror shows the same lesson with two bootstrap stages:

```text
startup code
  -> copies helper to $000004
  -> helper copies decruncher to $000040
  -> decruncher unpacks payload to $000400
  -> final jump enters $000400
```

Native execution answers one question:

```text
What bytes did the target write?
```

Source-quality analysis answers the next questions:

```text
which bytes are executable?
which bytes are data, tables, strings, storage, or residual?
which operands observe addresses?
which address observations name the same storage?
which platform names are semantically proven?
which labels are justified and visibly used?
```

Round-trip verification is mandatory, but it is not enough. This can
round-trip exactly while still being wrong:

```asm
abs_0_00042C00:
    ori.b #$8000,d6
abs_0_00042C04:
    ori.b #0,d0
abs_0_00042C08:
    ori.b #0,d0
```

The bytes are preserved. The false claim is that these bytes are accepted code.

## Tutorial: Current Failure Shape

The current accepted-code path mainly lives in:

```text
src/m68k_analysis_facts_v2.c

append_code_start_fact()
enqueue_code_start_runtime()
enqueue_code_start_runtime_ex()
run_reachable_fixed_point()
validate_reachable_candidate_for_acceptance()
rebuild_accepted_bytes_from_starts()
```

Candidate validation currently proves local instruction shape:

```text
policy_structured_data_overlaps_range()
candidate_has_invalid_code_target()
candidate_has_reserved_full_extension()
candidate_reencodes_exactly()
candidate_overlaps_accepted_bytes()
```

That is useful, but it only proves that a candidate decodes and re-encodes. It
does not prove that control flow can enter it, that a table really dispatches
to it, or that the accepted run ends credibly.

The current fixed point is roughly:

```text
decode candidate
  -> validate local instruction shape
  -> mark accepted bytes
  -> append M68K_FACT_CODE_ACCEPTED
  -> enqueue direct targets
  -> enqueue indirect/table targets
  -> enqueue runtime aliases/copies
  -> enqueue vector/callback/API targets
  -> enqueue fallthrough
```

Several durable facts are still produced during or after render preview:

```text
m68k_analysis_facts_v2.c
  -> fixed point and accepted bytes
  -> data spans
  -> source blocker check
  -> m68k_render_ir_preview_build()

m68k_render_ir_preview_build()
  -> accepted code ranges
  -> orphan code signals
  -> range ownership
  -> table descriptors
  -> conflict ranges
  -> source-analysis section

m68k_analysis_facts_v2.c after preview
  -> recovered indirect sites
  -> address observations
  -> platform media/storage facts
  -> incomplete-analysis facts
  -> finalized conflicts
```

The current C artifact seam is already close to what we need:

```text
m68k_facts_v2_collect_source_analysis_profile()
  -> facts_v2_collect_profile_internal()
  -> m68k_render_ir_preview_build(..., out_source_analysis)
  -> append_recovered_indirect_sites_for_accepted()
  -> append_address_observations_for_accepted()
  -> append_platform_media_transfers_from_facts()
  -> append_platform_storage_layouts_from_object()
  -> facts_v2_append_incomplete_analysis_from_profile()
  -> m68k_ir_source_analysis_finalize_table_conflicts()
  -> m68k_ir_source_analysis_finalize_base_layout_conflicts()
```

That confirms the correct module seam is not Python and not the web layer. It
is the C Source Analysis IR handoff. The flaw is ordering and ownership:
semantic facts are still discovered by render lookup and then copied into
`M68kSourceAnalysisIR`, while some facts are appended after render preview has
already made decisions. Source-quality should move those decisions before
preview and leave preview as a formatter/exporter.

Rendering should not own accepted ranges, table descriptors, range ownership,
platform meaning, or label consistency. Rendering should format facts that C
analysis already proved.

The current source-refusal path is also too render-shaped:

```text
facts_v2_has_hard_failures()
  -> unresolved labels
  -> unresolved interior conflicts
  -> relocation failures
  -> relocation anchor failures
  -> table target set limit hits
  -> required instruction failures

facts_v2_has_source_blockers()
  -> currently just aliases facts_v2_has_hard_failures()

facts_v2_record_source_blocker_first_failure()
  -> writes M68K_SOURCE_EXPORT_FAILURE_* into M68kFactsV2Profile

m68k_render_ir_preview_build()
  -> can still refuse render, byte mismatch, or instruction relocation
```

That skeleton now uses source-export vocabulary rather than render-owned enum
names. Structural blockers, source-quality blockers, and render/export failures
share the profile summary fields, but the remaining ownership work is to make
all durable source-quality evidence live in Source Analysis IR before rendering.

## Tutorial: Add A Source-Quality Module

Add one deep C module at the Source Analysis IR seam:

```text
m68k_source_quality_analyze(input facts, platform adapter, result arena)
  -> appends source-quality fact families to M68kSourceAnalysisIR
  -> appends blocker counts to M68kFactsV2Profile
```

The interface is small. The implementation behind it can be large: origin
audit, accepted-run walks, address observation, range ownership, table
ownership, platform use-shape proof, and symbol consistency. That gives
locality: false code, vector naming, table promotion, and label disagreement
are fixed in one C module instead of in rendering, JSON, Python, and web code.

This module follows the existing project decisions:

```text
ADR 0001
  C owns compact semantic and reproduction facts.
  Python expands ids and bitflags into reports, CLI output, and UI labels.

ADR 0002
  Persistent analysis results use Result Arena ownership.
  Source-quality facts must not introduce caller-owned string lifetimes.

ADR 0004
  Manual Action Log is projected before analysis.
  Manual facts enter C as effective metadata, not Python-side overrides.
```

Run source-quality after each accepted-byte rebuild and before source blockers:

```text
seed roots
  -> reachable fixed point
  -> rebuild accepted bytes
  -> source-quality audit
  -> seed runtime/table/callback/API entries
  -> reachable fixed point
  -> rebuild accepted bytes
  -> source-quality audit
  -> classify data spans
  -> source blockers
  -> render preview
```

The current call order is the part to change:

```text
facts_v2_collect_profile_internal()
  -> source blockers
  -> m68k_render_ir_preview_build(..., out_source_analysis)
       -> creates M68kSourceAnalysisIR
       -> render lookup appends auto policy/source facts
       -> render walk appends per-section source-analysis facts
       -> render_asm_app_extension_rs() appends base layout facts
  -> append_recovered_indirect_sites_for_accepted()
  -> append_address_observations_for_accepted()
  -> append_platform_media_transfers_from_facts()
  -> append_platform_storage_layouts_from_object()
  -> finalize table/base-layout conflicts
```

That makes rendering both a consumer and a producer of analysis. It also means
some facts are too late to influence source refusal.

The corrected order is:

```text
facts_v2_collect_profile_internal()
  -> create M68kSourceAnalysisIR
  -> append raw structural facts that already exist
  -> m68k_source_quality_analyze()
       -> code origins / accepted runs
       -> address observations / identities / ranges
       -> platform uses / semantic uses
       -> table and data reference facts
       -> symbol origins / expected rendered accesses
       -> source-quality diagnostics
  -> source blockers read source-quality diagnostics
  -> m68k_render_ir_preview_build(..., const M68kSourceAnalysisIR *)
       -> format only
       -> record actual rendered accesses
  -> compare expected vs actual rendered accesses
  -> export profile/source JSON
```

`m68k_render_ir_preview_build()` should not create `M68kSourceAnalysisIR` or
append semantic facts. Its source-analysis parameter should become read-only
input. If rendering needs to record actual output, record only
`M68kRenderedSymbolAccessIR` or render/export diagnostics in a dedicated output
arena after source-quality has already produced the expected facts.

Place the new module beside facts v2, not under rendering:

```text
src/m68k_source_quality.h
src/m68k_source_quality.c
src/m68k_source_quality_platform.c   optional only if the adapter glue grows
src/m68k_ir.h / src/m68k_ir.c        fact storage and append helpers
src/platform_facts_v2.c              platform dictionary adapter remains here
```

Do not create a Python source-quality module. Python can call the C pipeline,
read JSON, group rows, and display diagnostics.

New or strengthened fact families:

```text
M68kSourceQualityDiagnosticIR
M68kCodeOriginIR
M68kAcceptedCodeRunIR
M68kAddressObservationIR
M68kAddressIdentityIR
M68kAbsoluteAddressRangeIR
M68kPlatformAddressUseIR
M68kPlatformSemanticUseIR
M68kSymbolOriginIR
M68kExpectedSymbolAccessIR
M68kRenderedSymbolAccessIR

existing families moved earlier or replaced:
M68kRangeOwnershipIR
M68kTableDescriptorIR
M68kTableConsumerIR
M68kTableEntryIR
M68kDataReferenceIR
M68kRuntimeViewIR
M68kRuntimeAddressRefIR
M68kAbsoluteMemoryRefIR -> M68kAddressObservationIR / M68kAddressIdentityIR /
  M68kAbsoluteAddressRangeIR
```

The current C seam already has the right shape:

```c
typedef struct M68kSourceAnalysisIR {
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
  M68kIncompleteAnalysisIR *incomplete_analyses;
  M68kPlatformStorageLayoutIR *platform_storage_layouts;
  M68kBaseLayoutFieldIR *base_layout_fields;
  M68kSectionAnalysisIR *sections;
  Arena *arena;
} M68kSourceAnalysisIR;

typedef struct M68kSectionAnalysisIR {
  M68kRangeOwnershipIR *range_ownerships;
  M68kTableDescriptorIR *table_descriptors;
  M68kTableConsumerIR *table_consumers;
  M68kTableEntryIR *table_entries;
  M68kDataReferenceIR *data_references;
  M68kRuntimeViewIR *runtime_views;
  M68kRuntimeAddressRefIR *runtime_address_refs;
  M68kAddressObservationIR *address_observations;
  M68kCodeStartRefIR *code_start_refs;
  Arena *arena;
} M68kSectionAnalysisIR;
```

The exact current structs have more fields than the simplified sketch above.
The important current-state finding is this:

```text
M68kSourceAnalysisIR currently owns:
  structured data policy/findings
  incomplete analysis facts
  platform storage layouts
  base layout fields
  sections

M68kSectionAnalysisIR currently owns:
  range ownerships
  table descriptors/consumers/entries
  data references
  runtime views/address refs
  code start refs
  orphan code signals
  CFG/violation/platform recovery facts

Missing as real C facts:
  source_quality_diagnostics
  code_origins
  accepted_code_runs
  address_observations
  address_identities
  absolute_address_ranges
  platform_address_uses
  platform_semantic_uses
  symbol_origins
  expected_symbol_accesses
  rendered_symbol_accesses
```

`source_analysis_to_json()` currently exports existing facts such as
`runtime_address_refs`, `data_references`, `code_start_refs`, and
`range_ownerships`. It does not yet export the new source-quality families.
That makes C IR and JSON export the first real implementation gap.

Placement rule:

```text
can be keyed by one source section and offset
  -> M68kSectionAnalysisIR

groups observations, spans sections, or summarizes target state
  -> M68kSourceAnalysisIR

is just a profile count or first failure
  -> M68kFactsV2Profile summary only, backed by source-analysis facts
```

Capacity policy:

```text
semantic truncation
  -> forbidden

temporary scratch limit hit
  -> source-quality blocker with first section/offset/capacity

persistent fact storage
  -> dynamic Result Arena arrays
```

Current refusal plumbing already proves the useful seam:

```text
facts_v2_has_hard_failures()
  unresolved_labels
  interior_conflicts_unresolved
  relocation_failures
  relocation_anchor_instruction_bytes
  relocation_anchor_unknown_contexts
  table_target_set_limit_hits
  required_instruction_failures

facts_v2_has_source_blockers()
  currently aliases hard failures

facts_v2_record_source_blocker_first_failure()
  writes asm_source_first_failure_* into M68kFactsV2Profile

facts_v2_append_incomplete_analysis_from_profile()
  currently turns table_target_set_limit_hits into M68kIncompleteAnalysisIR

m68k_render_ir_preview_build()
  can still fail later for true export/render failures
```

The first ownership cleanup is complete: `M68K_SOURCE_EXPORT_FAILURE_*` lives in
`m68k_source_export.h`, and both analysis/profile code and render/export code
use that shared vocabulary. The remaining problem is that refusal is still
profile-first: callers must know whether a failure was analysis,
source-quality, or render/export by reading the implementation.

The deeper interface is:

```text
M68kSourceQualityDiagnosticIR[]
  durable fact array, queryable through source analysis JSON

M68kSourceExportFailureKind
  small summary enum for refusal/profile/CLI/web display

M68kFactsV2Profile
  counts and first-failure summary only

M68kRenderIRPreview
  render/export failures only
```

Deletion test: deleting `m68k_render_ir.h` no longer deletes analysis refusal
vocabulary. The next deletion test is stricter: source-quality blockers should
be derivable from `M68kSourceQualityDiagnosticIR` before render preview starts.

## Tutorial: False Code And Accepted Runs

The first source-quality category is false accepted code.

Damocles has a false accepted run around `$42C00`:

```asm
abs_0_00042C00:
    ori.b #$8000,d6
abs_0_00042C04:
    ori.b #0,d0
abs_0_00042C08:
    ori.b #0,d0
...
abs_0_00042C74:
    dc.b $00,$88
```

Starglider shows the same class through a table-looking reference:

```asm
    dc.l loc_0_00006098

loc_0_00006098:
    ori.w #112,$0(a0,d0.w)
    ori.b #136,d0
    dc.b $00,$88,$00,$00,$00,$00,$01,$04
```

Pandora adds a third fixture:

```asm
abs_0_0004E3EC:
    negx.w d0
    ori.w #0,d0
    ori.b #0,d0
    ori.b #128,d0
    dc.b $00,$C0,$00,$C0,$00,$C0
```

These are not `ori` opcode bugs. Real code legitimately uses `ori`, including
hardware setup. The failure is accepting weak byte shape as executable proof.

The distinction is:

```text
legal instruction bytes
  -> code-shaped observation
  -> maybe orphan-code signal
  -> not accepted code without executable origin

accepted code
  -> has origin proof
  -> forms a credible accepted run
  -> does not end by weak fallthrough into data or a decode gap
```

Represent code origin explicitly:

```c
typedef enum M68kCodeOriginClass {
  M68K_CODE_ORIGIN_STRONG_ENTRY,
  M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET,
  M68K_CODE_ORIGIN_PROVEN_FALLTHROUGH,
  M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY,
  M68K_CODE_ORIGIN_MANUAL_SEED,
  M68K_CODE_ORIGIN_CONDITIONAL_TABLE_TARGET,
  M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS,
  M68K_CODE_ORIGIN_WEAK_SHAPE_ONLY,
  M68K_CODE_ORIGIN_DATA_REFERENCE_ONLY
} M68kCodeOriginClass;

typedef struct M68kCodeOriginIR {
  uint16_t section_index;
  uint32_t offset;
  uint32_t length;
  M68kCodeOriginClass origin_class;
  uint16_t source_section_index;
  uint32_t source_offset;
  uint8_t has_runtime_address;
  uint32_t runtime_address;
  uint32_t reason;
  uint32_t evidence_kind;
  uint8_t confidence;
} M68kCodeOriginIR;
```

`M68K_FACT_CODE_START_REASON_CONTROL_TARGET` is too broad. Split it by evidence
subkind:

```text
direct decoded branch/call/jump target
relocation-backed control transfer
traced indirect target set
long/word/keyed table target
relocation-backed function pointer table
runtime alias or copied-code entry
interrupt vector store
```

`CONTROL_TARGET` alone is not proof.

Current C has the right raw material, but it stores the wrong abstraction:

```text
append_code_start_fact()
enqueue_code_start_runtime_ex()
run_reachable_fixed_point()
validate_reachable_candidate_for_acceptance()
rebuild_accepted_bytes_from_starts()
```

`append_code_start_fact()` records reason, source offset, confidence, and
runtime address, then the work queue tries to decode the candidate.
`run_reachable_fixed_point()` accepts a candidate when local validation passes:

```text
policy structured-data overlap
invalid control target
reserved full extension
exact re-encode
accepted-byte overlap
```

After acceptance it appends `M68K_FACT_CODE_ACCEPTED`, records runtime-copy and
runtime-sink observations, enqueues direct targets, relocation targets, traced
indirect targets, copied-entry targets, interrupt-vector targets, table targets,
and finally normal fallthrough. Normal fallthrough is often speculative:

```text
candidate has normal fallthrough
  -> enqueue FALLTHROUGH with speculative confidence unless generated branch
```

That is useful reachability machinery, but it does not answer the
source-quality question "is this accepted run credible?" It also conflates
three different things:

```text
code start request
accepted decoded instruction
executable origin proof
```

`rebuild_accepted_bytes_from_starts()` then reconstructs byte coverage from
accepted starts. It proves non-overlap and byte coverage, not semantic validity.
The accepted-run audit must sit above this machinery and inspect the resulting
run as a whole.

Orphan-code signals already prove the project has some of the needed evidence:

```text
M68K_ORPHAN_CODE_SIGNAL_CONTEXT_ACCEPTED_CODE_BOUNDARY
M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RENDERABLE_LABEL
M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RUNTIME_VIEW

M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE
M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED
M68K_ORPHAN_CODE_SIGNAL_SUPPRESSED
```

Those facts are valuable precursor signals. They should not be reused as the
final source-quality interface because they describe code-shaped islands near
current analysis boundaries, not the origin and ending of every accepted run.
The accepted-run audit can reuse their scanners and nearby-data classification,
but it should emit `M68kAcceptedCodeRunIR` and diagnostics.

Audit accepted runs, not only individual instructions:

```c
typedef enum M68kAcceptedCodeRunEndKind {
  M68K_ACCEPTED_CODE_RUN_END_TERMINAL_FLOW,
  M68K_ACCEPTED_CODE_RUN_END_NONLOCAL_JUMP,
  M68K_ACCEPTED_CODE_RUN_END_PROVEN_BRANCH_TARGET,
  M68K_ACCEPTED_CODE_RUN_END_PROVEN_RANGE_BOUNDARY,
  M68K_ACCEPTED_CODE_RUN_END_SECTION_END,
  M68K_ACCEPTED_CODE_RUN_END_DATA_SPAN,
  M68K_ACCEPTED_CODE_RUN_END_DECODE_GAP,
  M68K_ACCEPTED_CODE_RUN_END_WEAK_FALLTHROUGH_CHAIN
} M68kAcceptedCodeRunEndKind;

typedef struct M68kAcceptedCodeRunIR {
  uint16_t section_index;
  uint32_t start_offset;
  uint32_t end_offset;
  uint32_t terminal_offset;
  M68kAcceptedCodeRunEndKind end_kind;
  uint16_t instruction_count;
  uint8_t weakest_origin_class;
} M68kAcceptedCodeRunIR;
```

Expected diagnostics:

```text
source-quality:accepted_code_without_executable_origin
source-quality:accepted_code_run_decode_gap
source-quality:accepted_code_run_falls_into_data
source-quality:accepted_code_run_weak_fallthrough_chain
source-quality:unterminated_or_invalid_code_range
source-quality:table_value_promoted_without_dispatch_proof
```

The worker response is to fix origin, range, table, or control-flow analysis.
It is not to stop at the diagnostic.

## Tutorial: Address Identity And Absolute Ranges

Damocles renders related addresses as unrelated facts:

```asm
runtime_address_00042C00 EQU $42C00

abs_0_00042C00:
    ...

movea.l runtime_address_00042C00.l,a3
move.w $00042C6C.l,d0
move.w $00042C70.l,d2
move.w d1,$00042C70.l
move.w d0,$00042C6C.l
move.l $0(a0,d0.w),$000459BA.l
move.l $0(a0,d0.w),$000459C6.l
```

`$42C00`, `$42C6C`, `$42C70`, `$459BA`, and `$459C6` are address observations
inside one materialized image. They need identity and range ownership, not
independent raw labels.

Start with observations:

```c
typedef enum M68kAddressObservationKind {
  M68K_ADDRESS_OBSERVATION_ABSOLUTE_OPERAND,
  M68K_ADDRESS_OBSERVATION_ADDRESS_IMMEDIATE,
  M68K_ADDRESS_OBSERVATION_PC_RELATIVE_VALUE,
  M68K_ADDRESS_OBSERVATION_INDEXED_BASE,
  M68K_ADDRESS_OBSERVATION_TABLE_ENTRY,
  M68K_ADDRESS_OBSERVATION_RUNTIME_COPY,
  M68K_ADDRESS_OBSERVATION_MANUAL_RUNTIME_REF
} M68kAddressObservationKind;

typedef struct M68kAddressObservationIR {
  uint16_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  M68kAddressObservationKind kind;
  uint32_t observed_address;
  uint8_t width;
  uint8_t is_write;
  uint8_t confidence;
} M68kAddressObservationIR;
```

Then group them:

```text
address observations
  -> address identity
  -> absolute address range
  -> range ownership
  -> labels and xrefs from accepted ownership
```

Illustration:

```text
observed:
  write $42C6C
  write $42C70
  read  $42C6C
  read  $42C70
  write $459BA
  write $459C6

identity:
  materialized Damocles runtime image

range owner:
  accepted app storage / runtime data range

not:
  five unrelated generated labels
  false code at $42C00
```

One-off non-system absolute references are also signals. If they are not
processor or platform addresses, they usually mean analysis missed a range,
table, runtime copy, loader output, or storage layout.

The observation pass must cover more than direct absolute operands:

```text
direct absolute operand:
  move.w $00042C6C.l,d0
  move.w d0,$00042C6C.l

address-domain immediate:
  movea.l #$00042C00,a3
  move.l  #handler,$0000006C.l

relocated operand:
  relocation target -> section storage observation

runtime mapped operand:
  runtime address -> materialized source offset observation

base plus displacement:
  lea.l $74.w,a2
  move.l d0,$67A8(a2)
  -> observed effective address $681C, base-source $74, shape low_memory_base

looped postincrement/predecrement:
  lea.l absolute_slot_00000144.w,a0
  lea.l runtime_code_00000318.w,a1
clear_loop:
  clr.b (a0)+
  cmpa.l a1,a0
  bne.b clear_loop
  -> range observation, not many one-off refs
```

Current C already records part of this:

```text
append_runtime_address_refs_for_accepted()
  -> direct address-domain operands that map through runtime ranges
  -> external runtime sink refs for platform sinks

trace_state_record_runtime_sink_ref()
  -> traced MOVE/MOVEA values into runtime-address sinks

trace_state_record_runtime_storage_sink_ref()
  -> traced values stored into platform-classed storage sinks

append_address_observations_for_accepted()
  -> direct absolute operands with memory read/write/compute/branch use
  -> address-domain immediates
  -> relocation target override to section storage
```

The problem is coverage, phase, and ownership.

`m68k_asm_operand_absolute_value()` sees only direct absolute effective
addresses. `append_address_observations_for_accepted()` adds those and some
address-domain immediates, but it does not make a durable general observation
for every address-bearing instruction form. The traced table/control machinery
can already reason about register-derived addresses in narrow paths, but that
knowledge is not lifted into source facts before rendering.

The current collector therefore misses or weakly represents forms such as:

```asm
movea.l #abs_0_00043080,a0
adda.w  $0(a0,d6.w),a3

lea.l   $74.w,a2
move.l  d0,$67A8(a2)

move.l  $0(a0,d0.w),$000459BA.l
```

Those are not exotic. They are ordinary source-address observations:

```text
immediate address loaded into address register
known address register plus displacement
known address register plus indexed table offset
absolute destination operand
```

`append_address_observations_for_accepted()` also runs after render preview and
assigns owner kind before C has grouped observations into identities and ranges.
That is too late for source-quality decisions. It also classifies CPU vectors by
numeric address after the platform owner check, which means an address such as
`$74` can become a vector name before source-quality has decided whether the
program is installing a vector, clearing vectors, using low-memory storage, or
using `$74` as a base to reach unrelated higher offsets.

Replace the shallow absolute-memory-ref collector with a source-quality address
observation pass:

```text
accepted instruction
  -> per-operand address observation builder
       direct absolute effective address
       address-domain immediate
       relocation target
       PC-relative target
       traced address-register base plus displacement
       indexed address-register base when base identity is known
       table entry value
       runtime copy or materialized runtime address
       platform runtime/storage sink
  -> address identity
  -> absolute/runtime/source range
  -> platform address use-shape
  -> expected symbol access
```

The replacement fact should carry the shape, not only the final number:

```c
typedef enum M68kAddressObservationForm {
  M68K_ADDRESS_OBSERVATION_FORM_ABSOLUTE_EA,
  M68K_ADDRESS_OBSERVATION_FORM_IMMEDIATE_ADDRESS,
  M68K_ADDRESS_OBSERVATION_FORM_RELOCATION_OPERAND,
  M68K_ADDRESS_OBSERVATION_FORM_PC_RELATIVE_TARGET,
  M68K_ADDRESS_OBSERVATION_FORM_REGISTER_BASE_DISPLACEMENT,
  M68K_ADDRESS_OBSERVATION_FORM_INDEXED_REGISTER_BASE,
  M68K_ADDRESS_OBSERVATION_FORM_TABLE_ENTRY,
  M68K_ADDRESS_OBSERVATION_FORM_RUNTIME_ADDRESS,
  M68K_ADDRESS_OBSERVATION_FORM_PLATFORM_SINK
} M68kAddressObservationForm;

typedef struct M68kAddressObservationIR {
  uint16_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  M68kAddressObservationKind kind;
  M68kAddressObservationForm form;
  uint32_t observed_address;
  uint32_t base_identity_id;
  int32_t displacement;
  uint8_t index_register;
  uint8_t access_width;
  uint8_t confidence;
} M68kAddressObservationIR;
```

The old `M68kAbsoluteMemoryRefIR` no longer remains in source analysis. The
remaining work is to make render-side absolute-memory discovery consume address
observations, address identities, and range ownership facts instead of
rebuilding an equivalent view.

### Runtime, Source, And Storage Ranges

Damocles also shows that addresses need range identity, not only better symbol
names:

```asm
lea.l abs_0_0006D480.l,a0      ; bitmap memory plane 2 +$1600
lea.l absolute_slot_0007D480.l,a1
copy_plane:
    move.l (a0)+,(a1)+
    cmpa.l #$6FD00,a0
    bne.b copy_plane

lea.l absolute_slot_000003FC.w,a0
cmp.b $73AB(a0),d3
cmp.b $6FA9(a0),d1
```

The `absolute_slot_*` names are a rendering symptom. They say only "raw absolute
address", while the program shape says more:

```text
source range:
  abs_0_0006D480..abs_0_0006FCFF

destination range:
  $0007D480..$0007FCFF

operation:
  copied bitmap plane/storage range

not:
  hundreds of unrelated absolute slots
```

The current C trace state has a small `absolute_slots[]` scratchpad. It can
remember that a long value was stored to an absolute address and reloaded later:

```text
trace_state_set_absolute_slot()
trace_state_find_absolute_slot_const()
trace_state_clear_absolute_slot()
```

That is useful local propagation, but it is not a source fact. It has a fixed
trace limit, no range identity, no range owner, and no durable relationship to
rendered symbols. Current tests prove the scratchpad can propagate an API type
or disk-buffer pointer through one absolute slot, but they also show the wrong
module seam: the assertion is on rendered source, not on a C storage/range fact.

Platform media/storage support has the same shape:

```text
append_platform_media_transfer_fact()
append_platform_media_transfers_from_facts()
append_platform_storage_layouts_from_object()
```

Those facts are appended into `M68kSourceAnalysisIR`, but they are not yet the
general range-identity layer used by ordinary absolute references, runtime
copies, bitmap planes, loader output, and low-memory application storage.

Promote this into source-quality range facts:

```c
typedef enum M68kRangeIdentityKind {
  M68K_RANGE_IDENTITY_SOURCE_SECTION,
  M68K_RANGE_IDENTITY_RUNTIME_MATERIALIZED,
  M68K_RANGE_IDENTITY_RUNTIME_COPY,
  M68K_RANGE_IDENTITY_ABSOLUTE_STORAGE,
  M68K_RANGE_IDENTITY_PLATFORM_MEDIA,
  M68K_RANGE_IDENTITY_PLATFORM_STORAGE
} M68kRangeIdentityKind;

typedef enum M68kRangeOperationKind {
  M68K_RANGE_OPERATION_COPY,
  M68K_RANGE_OPERATION_CLEAR,
  M68K_RANGE_OPERATION_FILL,
  M68K_RANGE_OPERATION_STRIDED_READ,
  M68K_RANGE_OPERATION_STRIDED_WRITE,
  M68K_RANGE_OPERATION_INDEXED_ACCESS
} M68kRangeOperationKind;
```

Then connect address observations to ranges:

```text
address observation
  -> range identity
  -> range operation
  -> storage/media/application owner
  -> expected symbol expression
```

The renderer should get expressions from those facts:

```asm
lea.l bitmap_plane_2+$1600,a0
lea.l display_backbuffer+$1600,a1
cmp.b object_slots+$73AB,d3
```

The exact names still come from normal symbol review. The important part is that
the renderer no longer invents `absolute_slot_0007D480` because C failed to
describe the range.

Expected diagnostics:

```text
source-quality:absolute_ref_without_range_owner
source-quality:absolute_ref_sparse_unowned_cluster
source-quality:address_identity_split
source-quality:address_observation_without_identity
source-quality:low_address_semantics_unproven
source-quality:absolute_slot_without_storage_identity
source-quality:range_copy_without_source_or_destination_owner
```

## Tutorial: Platform Semantics

Low addresses on Amiga can mean several different things:

```text
CPU exception vector table
ExecBase pointer
hardware register mirrors or aliases
temporary low-memory storage
runtime copied code
runtime staging buffers
ordinary application slots
base pointers used to reach higher offsets
```

Numeric address alone is not enough. Damocles shows the trap:

```asm
lea.l $74.w,a2
move.l d0,$67A8(a2)
move.l d1,$6BA8(a2)
```

`$74` is numerically the level 5 autovector slot, but this use shape is a base
for ordinary low-memory addressing. It should not become a vector semantic
name.

True vector installs look different:

```asm
move.l #handler,$0000006C.l
move.l #handler,$00000070.l
```

Vector clearing can also be real:

```text
loop writes zero over vector slots
  -> range-shaped vector-table operation
  -> platform semantic use is vector clearing
```

The platform adapter is a real seam because multiple platforms sit behind it:
Amiga HUNK, Atari ST, Mac resources/HFS, raw/native payloads.

```text
src/platform_common.h
src/platform_facts_v2.c

platform_facts_v2_resolve_trap_call()
platform_facts_v2_resolve_opcode_call()
platform_facts_v2_resolve_stack_cleanup_call()
platform_facts_v2_is_callback_vector_slot()
platform_facts_v2_is_runtime_address_sink()
platform_facts_v2_runtime_address_sink_kind()
platform_facts_v2_runtime_address_storage_sink_kind()
platform_facts_v2_absolute_memory_owner()
platform_facts_v2_absolute_memory_owner_stays_literal()
platform_facts_v2_relocation_anchor_kind()
platform_facts_v2_fixup_addend_is_normalized_target()
platform_facts_v2_image_offset_target()
platform_facts_v2_supports_linkage_api_entry_labels()
platform_facts_v2_lvo_is_api()
platform_facts_v2_pc_relative_section_anchor_for_target()
platform_facts_v2_supports_loadseg_segment_chain()
platform_facts_v2_loadseg_segment_body_for_hops()
```

`platform_facts_v2.c` is already the right adapter seam. It includes generated
Amiga, Atari ST, and Mac OS runtime dictionaries behind one interface. That
makes the seam real: deleting it would spread platform dictionaries, calling
conventions, relocation quirks, and file-format anchors through generic M68K
analysis.

The adapter should answer platform-domain questions:

```text
is this address in a known platform domain?
is this address a runtime-address sink?
what structured data class does that sink imply?
is this file-format immediate an image offset?
is this target expressible through a platform section anchor?
does this platform support this linkage or loader convention?
```

It should not decide that a particular instruction is semantically installing a
vector, clearing a vector range, using low memory as scratch, or using a
vector-numbered address as an application base. Those decisions require
instruction shape and local data-flow, so they belong in source-quality
analysis.

In other words:

```text
platform adapter:
  address $DFF096 is a known Amiga hardware register
  address $64 is in the CPU vector address domain
  this register can be a runtime-address sink
  this relocation addend has platform-specific meaning

source-quality module:
  this accepted instruction wrote a handler pointer to vector $64
  this loop clears vector-sized entries
  this instruction used $74 as an arithmetic/base value
  this hardware write really carries a runtime-address observation
  this copper pointer proves a copper-list structured-data item
  this copper list carries bitmap plane pointers
  this audio pointer plus length write proves a sound-sample range

renderer:
  print the already-approved platform symbol/comment/form
```

Keep that seam. Move use-shape proof into source-quality facts:

```c
typedef enum M68kPlatformAddressUseShape {
  M68K_PLATFORM_ADDRESS_USE_TRUE_VECTOR_INSTALL,
  M68K_PLATFORM_ADDRESS_USE_VECTOR_FILL_LOOP,
  M68K_PLATFORM_ADDRESS_USE_VECTOR_CLEAR_LOOP,
  M68K_PLATFORM_ADDRESS_USE_CALLBACK_SLOT_INSTALL,
  M68K_PLATFORM_ADDRESS_USE_LOW_MEMORY_BASE,
  M68K_PLATFORM_ADDRESS_USE_LOW_MEMORY_STORAGE,
  M68K_PLATFORM_ADDRESS_USE_HARDWARE_REGISTER,
  M68K_PLATFORM_ADDRESS_USE_RUNTIME_ADDRESS_SINK
} M68kPlatformAddressUseShape;
```

Renderer and JSON code must not expand numeric CPU-vector ownership into
symbols. A vector symbol requires `M68kPlatformAddressUseIR` with a
vector-semantic use shape.

The same rule applies to useful Amiga comments. Render lookup currently infers
real platform semantics:

```text
render_lookup_infer_platform_runtime_structured_data()
  -> copper-list role
  -> sound-sample role
  -> auto structured-data item

render_lookup_add_copper_bitmap_runtime_refs()
  -> bitmap runtime address refs from copper list words

render_lookup_comment_bitmap_memory_uses_for_instruction()
  -> bitmap memory plane comments from inferred runtime refs

render_lookup_infer_amiga_audio_length_sources()
  -> audio sample length/period/source comments

collect_display_setup_before_offset()
format_display_setup_comment()
format_copper_display_layout_comment()
  -> display setup and copper layout comments
```

Those are good analyses in the wrong Module. They should become C
source-quality/platform facts. Comments are just one rendering of those facts.

Use two layers:

```c
typedef enum M68kPlatformSemanticUseKind {
  M68K_PLATFORM_SEMANTIC_USE_COPPER_LIST,
  M68K_PLATFORM_SEMANTIC_USE_BITMAP_PLANE,
  M68K_PLATFORM_SEMANTIC_USE_DISPLAY_SETUP,
  M68K_PLATFORM_SEMANTIC_USE_SOUND_SAMPLE,
  M68K_PLATFORM_SEMANTIC_USE_DISK_BUFFER,
  M68K_PLATFORM_SEMANTIC_USE_BLITTER_BUFFER
} M68kPlatformSemanticUseKind;

typedef struct M68kPlatformSemanticUseIR {
  uint16_t section_index;
  uint32_t offset;
  M68kPlatformSemanticUseKind kind;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t runtime_address;
  uint32_t size;
  uint32_t role_flags;
  uint8_t confidence;
} M68kPlatformSemanticUseIR;
```

Then rendering becomes simple:

```text
platform semantic use fact:
  kind=sound_sample target=loc_0_00000060 size=...

renderer:
  emits "; sound_sample pointer" or a structured-data block
```

This preserves the useful current output without keeping render lookup as a
second analysis engine. The interface also makes tests stronger: assert the C
fact first, then assert source formatting.

Current renderer/JSON code to delete as `M68kPlatformAddressUseIR` and
`M68kAbsoluteAddressRangeIR` land:

```text
attach_m68k_cpu_vector_symbols()
attach_absolute_memory_slot_symbols()
attach_absolute_memory_address_use_symbols()
absolute_memory_ref_owner_symbols()
absolute_memory_ref_owner_symbol_expr()
render_absolute_memory_header_collect()
render_absolute_memory_header_coalesce()
render_asm_absolute_memory_header()
render_lookup_infer_amiga_runtime_sink_immediate_refs()
render_lookup_infer_amiga_call_hardware_base_seeds()
render_lookup_analyze_amiga_app_state_slots()
render_lookup_infer_platform_runtime_structured_data()
render_lookup_add_copper_bitmap_runtime_refs()
render_lookup_comment_bitmap_memory_uses_for_instruction()
render_lookup_infer_amiga_audio_length_sources()
render_app_rs_append_layout_facts()
render_asm_app_extension_rs()
M68kRenderInferredHardwareBaseSeed
```

`render_absolute_memory_header_collect()` currently scans accepted instructions
from the renderer and uses fixed collection limits:

```text
M68K_RENDER_ABSOLUTE_MEMORY_HEADER_COLLECT_LIMIT = 256
M68K_RENDER_ABSOLUTE_MEMORY_HEADER_RANGE_LIMIT = 32
```

That is source analysis hidden in rendering, with silent truncation pressure.
The replacement is C-owned range facts plus a source-quality diagnostic if a
capacity limit is reached. Rendering can print a memory-map header from those
facts, but it must not discover or coalesce the ranges itself.

Current analysis hooks to reuse:

```text
candidate_stores_immediate_to_interrupt_vector()
candidate_stores_trace_to_callback_vector()
enqueue_interrupt_vector_store_target()
append_runtime_address_refs_for_accepted()
append_address_observations_for_accepted()
trace_state_record_runtime_sink_ref()
trace_state_record_runtime_storage_sink_ref()
```

These are not wrong. They are currently too narrow or late in the pipeline.
The clean path is to feed their observations into `M68kPlatformAddressUseIR`,
`M68kAddressObservationIR`, and `M68kAbsoluteAddressRangeIR` before source
blockers and rendering.

Fixture evidence:

```asm
; Conqueror: true vector install after native decrunching
move.l #abs_0_0000041A,m68k_vector_privilege_violation.l

; Bloodwych: vector fill loop plus explicit installs
move.l #abs_0_00008CC8,d0
lea.l m68k_vector_spurious_interrupt.w,a0
moveq.l #7,d1
vector_fill:
    move.l d0,(a0)+
    dbf.w d1,vector_fill
move.l #abs_0_00008C20,m68k_vector_level_3_interrupt_autovector.w

; Bloodwych: vector save/restore/manipulation
move.l m68k_vector_illegal_instruction.l,d1
move.l (a7)+,m68k_vector_illegal_instruction.l
move.l d1,m68k_vector_illegal_instruction.l
```

Those should produce vector-semantic platform uses. Damocles shows the opposite
case:

```asm
m68k_vector_level_5_interrupt_autovector EQU $74

lea.l m68k_vector_level_5_interrupt_autovector.w,a2
move.l d0,$67A8(a2)
move.l abs_0_00007ABA.w,$6BA8(a2)
```

Here `$74` is a numeric vector address, but the use shape is low-memory base
addressing. It should produce a low-memory base/storage platform use and a
diagnostic for the current vector name, not a vector-semantic symbol.

Magicland Dizzy gives another middle case:

```asm
clr.b m68k_vector_trap_4_instruction_vector.w
move.b d1,m68k_vector_trap_4_instruction_vector.w
cmpi.b #39,m68k_vector_trap_4_instruction_vector.w
```

These byte-sized operations on vector-numbered slots may be intentional
low-memory storage or handler-state scratch, not necessarily handler installs.
The source-quality use shape must say which evidence exists.

Deletion test:

```text
delete platform_facts_v2.c
  -> platform dictionaries and calling conventions reappear across analysis
     modules, so the seam is earning its keep

delete renderer helpers that attach CPU-vector symbols numerically
  -> complexity should not reappear; source-quality facts should replace them
```

## Tutorial: Tables And Data References

Table entries are address observations first. They become code targets only
when accepted code proves the dispatch use.

Bad path:

```text
dc.l loc_0_00006098
  -> value decodes as instructions
  -> promote target to accepted code
```

Good path:

```text
accepted code reads table entry
  -> table consumer fact
  -> table descriptor fact
  -> table entry fact
  -> target origin: conditional table target
  -> accepted-run audit
  -> accepted code only if target survives audit
```

Required facts:

```text
M68kTableDescriptorIR
M68kTableConsumerIR
M68kTableEntryIR
M68kDataReferenceIR
M68kCodeOriginIR(evidence_kind = table target)
```

The current IR already has most of the table surface:

```text
M68kAnalysisStructuredDataSourcePattern
  relocation_pointer_table
  indexed_word_dispatch
  indexed_local_pointer_read
  indexed_local_scalar_read
  pc_relative_indexed_read
  keyed_long_relative_dispatch
  pointer_string_table
  word_offset_string_table
  pc_relative_indexed_indirect_dispatch

M68kAnalysisTableKind
  scalar
  pointer
  relative_code_dispatch
  absolute_code_dispatch
  relative_data_lookup

M68kAnalysisTableEntryCountProof
  structured_range
  consumer_structural_scan
  relocation_record
  platform_record
  index_mask_domain
  index_compare_domain
  loop_limit

M68kTableEntryTargetStatus
  numeric_exact
  accepted_target
  unresolved_target
  interior_code_target
  conflicted_target
```

That is the right vocabulary. The problem is phase and ownership. Today the
renderer still materializes table target labels and appends table/data facts:

```text
render_lookup_materialize_long_table_targets()
render_lookup_materialize_structured_long_table_target_labels()
render_analysis_code_table_target_status()
render_analysis_append_data_reference_for_table_entry()
render_analysis_append_table_entry_target()
render_analysis_append_table_entry_numeric()
render_analysis_append_lookup_table_entries_for_item()
render_analysis_append_lookup_table_descriptors_for_section()
```

Those functions should either move into C source-quality analysis or disappear
behind it. The renderer may format a table, but it must not discover ownership,
targets, or executable meaning.

The analysis side already has useful table hooks:

```text
seed_relocation_backed_function_pointer_tables()
append_backward_sliced_indirect_table_targets_for_accepted()
trace_state_candidate_loads_keyed_long_relative_table_entry()
trace_state_candidate_swaps_keyed_long_relative_table_entry()
scan_long_control_target_table()
candidate_matches_direct_control_stub_table_entry()
```

Keep those as producers of observations, descriptors, consumers, entries, and
conditional origins. Then let the accepted-run audit decide whether a table
target becomes code.

Illustration:

```text
table-looking value
  -> M68kAddressObservationIR(kind = table_entry)
  -> M68kTableEntryIR(target_status = numeric_exact or unresolved)
  -> no code

accepted dispatch consumer reads the table
  -> M68kTableConsumerIR
  -> M68kCodeOriginIR(class = conditional_table_target)
  -> accepted-run audit
  -> accepted code or source-quality diagnostic
```

Starglider is the negative fixture:

```asm
loc_0_00005D58:
    dc.l loc_0_00005E58
    dc.l loc_0_00006098

loc_0_00006098:
    ori.w #112,$0(a0,d0.w)
    ori.b #136,d0
    dc.b $00,$88,$00,$00,$00,$00,$01,$04
```

The table-looking values must not be enough to accept `loc_0_00006098` as
code. If dispatch proof is weak or the target run degrades into data, the
result is table/address evidence plus a source-quality diagnostic, not a code
label.

Pandora and Bloodwych are positive fixtures to preserve:

```text
Pandora:
  word_offset_string_table, 114 entries, relative_data_lookup
  pc_relative_indexed_indirect_dispatch, 33 accepted code entries

Bloodwych:
  indexed_local_scalar_read, 73 numeric_exact scalar entries
  pointer table, 5 accepted data/code references as currently proven
```

Capacity failures stay in C:

```text
table target set capacity reached
  -> incomplete-analysis fact
  -> source-quality blocker diagnostic
  -> asm source refused before render
```

Do not express this as a renderer failure. The implementation is allowed to
raise scratch limits, but semantic truncation is still forbidden.

## Tutorial: Symbols And Rendered Accesses

Damocles exposed labels that had no visible accesses, or whose numeric operands
were not connected to the emitted symbol. That is a source-quality failure, not
a renderer cosmetic issue.

Model both sides:

```text
symbol origin:
  why this label exists

rendered symbol access:
  where the final source visibly uses it
```

Current C/render state is split:

```text
m68k_analysis_facts_v2.c
  M68K_FACT_LABEL_CREATED
  M68K_FACT_LABEL_REQUIRED
  label_lookup_create_label()
  materialize_safe_required_labels()
  resolve_required_label_invariants()

m68k_render_ir.c / m68k_analysis_render_lookup.c
  labels
  label_target_refs
  label_statement_refs
  storage_label_target_refs
  lookup_has_renderable_label()
  lookup_should_emit_label_statement()
  render_lookup_mark_label_target_ref()
  render_lookup_mark_label_statement_ref()
  render_lookup_mark_storage_label_target_ref()
```

That is useful implementation material, but it is not a durable source-quality
interface. Analysis can say a label exists or is required, and render lookup
can decide locally whether to print it, but no persistent fact says:

```text
why the symbol exists
which operand or statement used it
which expected access was stripped or left numeric
whether the symbol was code, data, platform, storage, or manual evidence
```

`resolve_required_label_invariants()` currently detects unresolved required
labels and interior conflicts. It does not diagnose labels that render without
real accesses, or operands that should have rendered through an approved
in-image symbol but remained numeric.

Render lookup already has a local approximation of actual access tracking:

```text
label_target_refs
label_statement_refs
storage_label_target_refs

lookup_label_has_inbound_target_ref()
lookup_label_has_statement_ref()
lookup_storage_label_has_inbound_target_ref()
lookup_has_renderable_label()
```

That tracking is render-local and decision-oriented. For example,
`lookup_has_renderable_label()` can suppress a label inside a structured range
unless render lookup has a target ref, statement ref, explicit name, relocation,
anchor, string span, copper-list boundary, or palette boundary. Those are valid
formatting concerns, but the source-quality question is different:

```text
did C expect this symbol to exist?
did C expect a label statement, operand, equate, or storage access?
did the renderer actually emit that access?
did render suppress a symbol whose C origin was still valid?
did render invent an access whose C origin was absent?
```

Keep the render-local arrays only as implementation evidence for actual output.
They should be drained into `M68kRenderedSymbolAccessIR` and then deleted once
the renderer writes actual accesses directly.

Damocles shows both sides:

```asm
runtime_address_00042C00 EQU $42C00

abs_0_00042C00:
    ori.b #$8000,d6

movea.l runtime_address_00042C00.l,a3
move.w $00042C6C.l,d0
move.w $00042C70.l,d2
move.l $0(a0,d0.w),$000459BA.l
move.l $0(a0,d0.w),$000459C6.l
```

Expected interpretation:

```text
abs_0_00042C00
  -> has a label statement
  -> should not be accepted code unless the accepted-run audit proves it
  -> symbol origin must explain whether it is data/storage/runtime image base

$42C6C and $42C70
  -> have repeated read/write operands
  -> should be address observations in the same identity/range
  -> numeric operands are expected-access failures if symbols are approved

$459BA and $459C6
  -> are write destinations in the materialized image
  -> need storage/range identity and visible symbol access or diagnostics
```

Expected facts:

```c
typedef enum M68kSymbolOriginKind {
  M68K_SYMBOL_ORIGIN_ACCEPTED_CODE_TARGET,
  M68K_SYMBOL_ORIGIN_DATA_REFERENCE,
  M68K_SYMBOL_ORIGIN_TABLE_ENTRY,
  M68K_SYMBOL_ORIGIN_ADDRESS_IDENTITY,
  M68K_SYMBOL_ORIGIN_PLATFORM_SEMANTIC_USE,
  M68K_SYMBOL_ORIGIN_MANUAL_LABEL
} M68kSymbolOriginKind;

typedef enum M68kSymbolAccessExpectationKind {
  M68K_SYMBOL_ACCESS_EXPECT_LABEL_STATEMENT,
  M68K_SYMBOL_ACCESS_EXPECT_BRANCH_TARGET,
  M68K_SYMBOL_ACCESS_EXPECT_OPERAND,
  M68K_SYMBOL_ACCESS_EXPECT_EQUATE,
  M68K_SYMBOL_ACCESS_EXPECT_STORAGE_LABEL
} M68kSymbolAccessExpectationKind;

typedef enum M68kRenderedSymbolAccessKind {
  M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT,
  M68K_RENDERED_SYMBOL_ACCESS_BRANCH_TARGET,
  M68K_RENDERED_SYMBOL_ACCESS_OPERAND,
  M68K_RENDERED_SYMBOL_ACCESS_EQUATE,
  M68K_RENDERED_SYMBOL_ACCESS_COMMENT_ONLY
} M68kRenderedSymbolAccessKind;
```

Clean source mode should fail when:

```text
generated symbol was expected but stripped
label statement exists without origin
label has origin but no visible rendered access
numeric operand should have used an approved in-image symbol
renderer creates a semantic name not present in C facts
symbol access points at a different address identity than the symbol origin
```

Expected diagnostics:

```text
source-quality:label_statement_without_symbol_origin
source-quality:symbol_origin_without_rendered_access
source-quality:expected_symbol_access_missing
source-quality:rendered_symbol_access_without_origin
source-quality:numeric_operand_for_approved_symbol
source-quality:symbol_access_identity_mismatch
source-quality:comment_only_symbol_access
```

`COMMENT_ONLY` is intentionally not a satisfying access for source-quality.
Comments can preserve hints, but clean source needs the operand, label,
directive, or equate to carry the semantic relationship.

Renderer helpers to migrate or delete as source-quality facts land:

```text
render_absolute_memory_header_collect()
render_absolute_memory_header_coalesce()
render_asm_define_absolute_memory_slot_symbol_once()
attach_absolute_memory_slot_symbols()
attach_absolute_memory_address_use_symbols()
attach_m68k_cpu_vector_symbols()
attach_runtime_address_ref_symbols()
attach_existing_materialized_runtime_immediate_symbols()
attach_unmapped_absolute_runtime_address_symbols()
attach_materialized_runtime_absolute_storage_symbols()
absolute_memory_ref_owner_symbols()
absolute_memory_ref_owner_symbol_expr()
```

The replacement rule is:

```text
renderer formats C-approved symbol refs only
JSON exports C facts only
Python indexes C facts only
```

Model the source-quality facts as expected and actual access:

```text
M68kSymbolOriginIR
  symbol id/name
  section/offset or absolute address
  origin kind
  owning address identity/range when present
  code origin when executable
  confidence and source evidence

M68kExpectedSymbolAccessIR
  symbol id/name
  source section/offset
  operand index or statement kind
  expected access kind
  target section/offset or absolute address
  owning address identity/range
  source evidence

M68kRenderedSymbolAccessIR
  symbol id/name
  source section/offset
  operand index or statement kind
  access kind
  rendered target section/offset or absolute address
  expected/actual/missing status
```

Then rendering becomes a projection:

```text
C fact says symbol is approved and expected
  -> renderer emits the operand/label/equate
  -> renderer records actual rendered access
  -> source-quality compares expected and actual before export is accepted
```

Implementation order:

```text
1. Convert M68K_FACT_LABEL_CREATED into M68kSymbolOriginIR.
2. Convert M68K_FACT_LABEL_REQUIRED into M68kExpectedSymbolAccessIR where the
   source operand/statement is known.
3. Create expected accesses from address identities, range ownership, table
   entries, platform semantic uses, accepted code targets, and manual labels.
4. Make renderer consume expected access facts when choosing labels/equates.
5. Record actual rendered accesses during the render walk.
6. Compare expected and actual accesses before clean source export is accepted.
7. Delete render-only label consistency decisions after equivalent C facts
   exist.
```

`M68K_FACT_LABEL_CREATED` and `M68K_FACT_LABEL_REQUIRED` should disappear from
the final source-quality path. During a mechanical migration they may exist only
as local precursors that feed symbol-origin and expected-access facts. Do not
ship them as a parallel semantic system.

Corpus/search state:

```text
current checked-in corpus:
  no final rows for analysis:symbol_origin
  no final rows for analysis:rendered_symbol_access
  no rows for label:definition_without_reference
  orphan-code:context:renderable_label finds 235 current targets / 986 rows

current tests:
  already describe the expected JSON/index shape for:
    analysis:symbol_origin:without_rendered_access
    analysis:rendered_symbol_access:targeted
    target-pattern:source_quality_label_consistency

fixture search until C emits final facts:
  Damocles target output and TODO notes are primary evidence
  orphan-code:context:renderable_label is related but not equivalent
  a fresh corpus index is required after C emits symbol facts
```

Implementation progress:

```text
C now exports first-class symbol-origin and expected-symbol-access rows from the
existing label precursor facts:

  M68K_FACT_LABEL_CREATED
    -> M68kSymbolOriginIR(origin_kind=label_created)

  M68K_FACT_LABEL_REQUIRED
    -> M68kExpectedSymbolAccessIR(access_kind=label_statement)

These are intentionally narrow. They preserve the current C evidence as durable
source-analysis JSON without claiming operand use-sites that the renderer has
not recorded.

Rendered symbol accesses remain absent until the render walk records real
label/operand/equate uses. Python manifest indexing consumes only exported C
facts and must not synthesize rendered use-sites from target-ref bitsets.

Follow-up progress:

  emitted label statements now produce M68kRenderedSymbolAccessIR rows with
  access_kind=label_statement. This is the first actual side of the comparison
  model because it is recorded from the same C decision path that emits source
  label rows. Operand/equate rendered accesses still remain unimplemented until
  the render walk records the exact operand/directive use-sites.
```

Representative search result:

```text
Starglider / SG
  source_id: amiga-hunk/025feefefd10 and related variants
  renderable-label orphan-code pressure

Workbench hunks
  many renderable-label rows
  useful negative coverage only; do not import just to make game-source rules
  fit OS/library noise
```

## Tutorial: Manual And Editor Input

Existing misclassifications come from auto-analysis, not user editing. That is
still a failure case. Manual input must not bypass the same checks.

The current pipeline is:

```text
Manual Action Log
  -> manual_actions.py
       validate_manual_action_payload()
       _project_actions()
       _projected_manual_seed()
       _projected_manual_label()
  -> effective_metadata.py
       _apply_manual_seed_projection()
       _manual_seed_to_code_entrypoint()
       _manual_seed_to_data_entity()
       _manual_label_to_code_label()
       _manual_representation_to_metadata()
  -> TargetMetadata
  -> platform_file_lib.c
       append_metadata_manual_representation_local()
       append_metadata_manual_runtime_address_ref_local()
       validate_effective_policy_against_object_local()
  -> M68kAnalysisPolicy
  -> m68k_analysis_facts_v2.c
       seed_facts_from_object()
       POLICY_ENTRY_POINT code starts
       named labels
       policy structured data overlap checks
  -> m68k_analysis_render_lookup.c
       manual runtime-address refs
  -> m68k_render_ir.c / m68k_ir_codec.c
       manual representations
```

This is the right broad shape, but the seam is too shallow today. Python
validates the log structure and projects the user's intent. C then consumes the
projection and validates basic ranges, but some manual facts become strong code
starts or render formatting inputs before source-quality has a chance to prove
the result.

The clean interface is:

```text
Python manual projection
  owns:
    durable user intent
    log identity checks
    conflict review items between manual actions

C source-quality module
  owns:
    whether the projected intent is valid for this binary
    whether manual code decodes into an accepted run
    whether manual data conflicts with accepted code
    whether manual labels have symbol origins
    whether manual representations have valid symbols/equates/accesses
    whether runtime refs are address observations, ranges, or code origins
```

Manual facts should enter as evidence:

```text
manual code seed
  -> M68kCodeOriginIR(origin=manual_seed)
  -> still must pass accepted-run audit

manual data seed
  -> M68kRangeOwnershipIR or structured-data fact
  -> conflicts with accepted code produce diagnostics

manual label
  -> M68kSymbolOriginIR(origin=manual_label)
  -> not executable proof

manual runtime ref
  -> M68kAddressObservationIR / runtime identity / range fact
  -> not executable proof by itself

manual representation
  -> expected rendered-access fact
  -> still requires range, symbol, equate, and operand consistency

manual target equate
  -> symbol/equate origin
  -> not a numeric operand rewrite unless source-quality accepts the access

manual execution view
  -> runtime address identity/range evidence
  -> code only when paired with a code origin and accepted-run audit
```

Focused failures:

```text
manual code seed overlapping known data
manual code seed ending in decode gap
manual label on unreconciled range
manual representation pointing at unavailable symbol
manual runtime ref that proves address observation but not code
manual target equate with no actual rendered access
manual execution view whose runtime range does not map to image bytes
```

The editor should not be able to create broken code blocks silently. If a user
forces bad evidence, C analysis should produce the same diagnostics as it does
for bad auto-analysis.

Fixed policy-array capacity is also a source-quality concern. Today policy
storage has limits such as:

```text
M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT
M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT
M68K_ANALYSIS_TARGET_EQUATE_LIMIT
M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT
```

Those limits are acceptable only as input transport limits while the C policy
object exists. They must not silently truncate semantic evidence. The target
shape is Result Arena backed source-quality arrays. Until that migration is
done, hitting a semantic policy limit must emit incomplete-analysis plus a
blocking diagnostic, not partial clean source.

## Implementation Slices

### Slice 1: Diagnostic IR And Refusal Plumbing

Add `M68kSourceQualityDiagnosticIR` with severity, blocker flag, kind, section,
offset, evidence source, and optional related address/range.

Existing C support to absorb:

```text
facts_v2_has_hard_failures()
facts_v2_has_source_blockers()
facts_v2_record_source_blocker_first_failure()
facts_v2_append_incomplete_analysis_from_profile()
facts_v2_has_asm_source_failures()
m68k_render_ir_preview_build()
record_source_export_failure()
```

Current failure kinds to split:

```text
source-quality / analysis blockers:
  UNRESOLVED_LABEL
  INTERIOR_CONFLICT
  RELOCATION
  RELOCATION_ANCHOR
  UNASSEMBLABLE_HUNK_DATA_RELOCATION
  UNASSEMBLABLE_HUNK_BASE_REGISTER_RELOCATION
  REQUIRED_INSTRUCTION
  TABLE_TARGET_SET_LIMIT
  false accepted code run
  unterminated accepted code run
  missing address identity/range owner
  missing expected rendered symbol access
  manual evidence conflict

render/export failures:
  RENDER
  BYTE_MISMATCH
  INSTRUCTION_RELOCATION
```

The renderer-named asm-source failure enum has been renamed to
`M68kSourceExportFailureKind`. Next, make source-quality diagnostics feed the
existing profile fields:

```text
asm_source_refused
asm_source_first_failure_kind
asm_source_first_failure_section
asm_source_first_failure_offset
asm_source_first_failure_aux_offset
```

Current migration target:

```text
M68K_SOURCE_EXPORT_FAILURE_*
  -> M68kSourceExportFailureKind in m68k_source_export.h

facts_v2_has_source_blockers()
  -> checks source-quality blocker count plus existing structural blockers

facts_v2_record_source_blocker_first_failure()
  -> reads first blocking M68kSourceQualityDiagnosticIR when present
  -> falls back only for render/export failures that happen after render starts

table_target_set_limit_hits
  -> incomplete-analysis fact
  -> source-quality blocker diagnostic
```

Implementation rule:

```text
blocking source-quality diagnostic exists
  -> asm_source_refused = 1
  -> asm_source_first_failure_* summarizes first blocking diagnostic
  -> render_asm_source = 0 before m68k_render_ir_preview_build()

render/export failure exists
  -> asm_source_refused = 1
  -> asm_source_first_failure_* summarizes export failure
  -> no durable source-quality diagnostic unless analysis fact caused it
```

Do not leave the renderer enum as the cross-module source-refusal vocabulary.
Rendering can still report export failures, but source-quality failures should
not be named after render internals.

### Slice 2: Source-Quality Pass

Add `m68k_source_quality_analyze()` before source blockers and render preview.
Initially it can project existing facts into the new pass. As each family moves
over, delete the old render/JSON producer.

### Slice 3: Code Origins

Promote `M68K_FACT_CODE_START` and `M68K_FACT_CODE_ACCEPTED` provenance into
`M68kCodeOriginIR`. Preserve reason, source offset, runtime address, length,
origin class, confidence, and evidence subkind.

Address/data references may create observations, ranges, tables, symbols, or
diagnostics. They must not create accepted code by themselves.

Implementation order:

```text
1. Add explicit evidence subkind for every enqueue path:
   direct control, relocation control, traced indirect, runtime alias,
   copied-entry target, interrupt-vector target, table target, callback field,
   platform API entry, inline resume, and fallthrough.
2. Convert code-start requests into M68kCodeOriginIR candidates before they are
   accepted.
3. Mark speculative fallthrough as weak until the accepted-run audit proves the
   run ending.
4. Mark table/data/address references as observations first, not executable
   origins.
5. Delete bare CONTROL_TARGET as a final origin class.
```

### Slice 4: Accepted Code Run Audit

Walk accepted starts through flow metadata. Record credible endings and
suspicious endings. Diagnose or demote invalid weak runs.

Run after each phase that can introduce new starts.

Implementation order:

```text
1. Build runs from accepted_start/accepted_bytes after each fixed-point phase
   and after each accepted-byte rebuild.
2. For each run, record start, end, terminal instruction, instruction count,
   weakest origin class, and end kind.
3. Treat terminal flow, nonlocal jump, proven branch target, explicit range
   boundary, and section end with strong origin as credible endings.
4. Treat decode gap, fallthrough into data, weak fallthrough chain, and table
   value without dispatch proof as diagnostics.
5. Demote weak accepted starts when the run cannot be justified.
6. Refuse clean source export when a required/manual/strong origin cannot be
   demoted but the run is invalid.
7. Keep orphan-code signals as precursor/review facts, not the final audit.
```

Focused tests:

```text
Damocles:
  accepted ori-like run at $42C00
  -> weak/invalid accepted run diagnostic or demotion

Starglider:
  pointer-table value loc_0_00006098
  -> table/data reference remains data unless dispatch proof exists

Pandora:
  false weak-origin code at abs_0_0004E3EC
  -> accepted-run audit catches weak fallthrough into data

positive:
  direct branch/call target ending in rts
  -> accepted run with proven control origin and terminal-flow end

manual:
  manual code seed ending in decode gap
  -> blocker diagnostic, not silent accepted code
```

### Slice 5: Address Identity And Absolute Ranges

Replace absolute-memory header discovery with C source-quality address facts:

```text
address observations
  -> address identities
  -> absolute address ranges
  -> range ownership
  -> diagnostics for one-off/sparse unowned refs
```

Implementation order:

```text
1. Add M68kAddressObservationIR with address form and source evidence fields.
2. Move direct absolute operands, address immediates, relocation targets, and
   runtime mapped operands into the address-observation producers.
3. Lift traced address-register base plus displacement and indexed-base forms
   out of narrow table/control paths into the general observation pass.
4. Convert runtime sink, storage sink, runtime copy, PC-relative, table-entry,
   and loop-range evidence into the same observation vocabulary.
5. Build M68kAddressIdentityIR groups before platform naming or rendering.
6. Build M68kAbsoluteAddressRangeIR / runtime range ownership from identities.
7. Build range operation facts for copied, cleared, filled, indexed, and
   strided ranges.
8. Map platform media/storage facts into the same range identity vocabulary.
9. Emit diagnostics for sparse unowned refs, one-off non-system refs, identity
   splits, and low-address uses with unproven semantics.
10. Make symbols and renderer consume expected accesses from identities/ranges.
11. Delete M68kAbsoluteMemoryRefIR after consumers move to observations,
    identities, and ranges. [done for source analysis]
12. Delete render-side absolute-memory header and symbol discovery.
13. Keep absolute-slot trace propagation only as local trace implementation, not
    as a rendered semantic or exported range fact.
```

Focused tests:

```text
Damocles:
  move.w $00042C6C.l,d0
  move.w d0,$00042C6C.l
  -> one owned materialized runtime range with expected symbol accesses

Damocles:
  move.l $0(a0,d0.w),$000459BA.l
  move.l $0(a0,d0.w),$000459C6.l
  -> destination absolute observations inside the same owned range

Damocles:
  movea.l #abs_0_00043080,a0
  adda.w $0(a0,d6.w),a3
  -> indexed data/table observation, not a code origin

Damocles/Starglider:
  low address used as a base for high offsets
  -> low-memory base/storage use, not CPU vector naming

Voodoo/Carrier:
  copied runtime ranges
  -> runtime/source identity split is explicit and source rendering uses the
     correct identity

Damocles:
  copy abs_0_0006D480..$6FD00 to $7D480
  -> source and destination range identities plus copy operation

Damocles:
  base $3FC with $6FA9/$73AB/$73A8 offsets
  -> application storage region with field-offset observations, not unrelated
     absolute_slot labels
```

### Slice 6: Tables And Data References

Move table descriptors, consumers, entries, and data references into C before
render. Code-start promotion may consume table entries only when accepted code
proves the dispatch use and source-quality audit accepts the target origin.

Implementation order:

```text
1. Preserve the existing IR vocabulary for descriptors, consumers, entries,
   data references, source patterns, table kinds, entry-count proof, and target
   status.
2. Move render-owned table fact construction into the source-quality pass.
3. Convert table values into address observations and table entries first.
4. Convert only proven dispatch consumers into conditional code origins.
5. Run accepted-code audit before any table target becomes durable code.
6. Emit incomplete-analysis plus source-quality blocker diagnostics for table
   target set capacity limits.
7. Delete render-owned table analysis in the same slice.
```

The deletion test is strict here. If `render_analysis_*table*()` disappears and
the complexity reappears in JSON or Python, the seam is wrong. It should
reappear only inside the C source-quality implementation.

### Slice 7: Platform Address Uses

Keep `platform_facts_v2.c` as the platform adapter. Move semantic use-shape
decisions into source-quality facts. Move platform semantic annotations out of
render lookup at the same time.

Implementation order:

```text
1. Add M68kPlatformAddressUseIR and JSON export.
2. Emit positive vector uses from immediate vector stores, traced vector stores,
   vector fill/clear loops, and callback-slot installs.
3. Emit low-memory base/storage uses when vector-numbered addresses are used as
   address bases or ordinary storage.
4. Emit hardware/runtime-sink uses from accepted memory accesses that feed
   platform runtime-address sinks.
5. Add M68kPlatformSemanticUseIR for copper lists, bitmap planes, display
   setup, sound samples, disk buffers, blitter buffers, and related sizes.
6. Convert runtime sink/storage sink facts into platform semantic uses before
   render preview.
7. Convert copper-list bitmap pointer extraction, display setup collection, and
   audio length/period/source analysis into C source-quality facts.
8. Make renderer consume these facts for vector/hardware/runtime-sink symbols,
   structured-data roles, and comments.
9. Delete numeric CPU-vector and hardware-symbol attachment fallbacks from
   renderer/JSON.
10. Delete render-owned Amiga semantic analysis helpers after equivalent C facts
    exist.
```

### Slice 8: Symbol And Rendered-Access Consistency

Add symbol-origin, expected-symbol-access, and rendered-symbol-access facts.
Diagnose labels without origins, generated symbols stripped by rendering,
numeric operands that should be symbolic, and expected accesses that do not
render.

Implementation order:

```text
1. Convert LABEL_CREATED/LABEL_REQUIRED into M68kSymbolOriginIR with source
   evidence and origin kind.
2. Add M68kExpectedSymbolAccessIR from address identity, table/data
   references, platform address use, accepted code targets, and manual labels.
3. Make render consume expected symbol accesses when choosing label/equate/
   operand forms.
4. Drain label_target_refs, label_statement_refs, and
   storage_label_target_refs into M68kRenderedSymbolAccessIR while they still
   exist.
5. Record actual rendered accesses directly from the render walk.
6. Compare expected and actual accesses before accepting clean source export.
7. Treat comment-only references as hints, not satisfying rendered accesses.
8. Delete render-only label consistency decisions that now duplicate C facts.
9. Delete LABEL_CREATED/LABEL_REQUIRED if they have no remaining distinct role.
```

Focused tests:

```text
label created by accepted branch target has origin and rendered access
label created by table data target has data/table origin, not code origin
manual label on data has origin but no executable origin
numeric operand to in-image storage produces expected rendered access
expected generated access missing from final source refuses export
visible table reference to false code does not validate that code target
label statement with no origin refuses clean source export
symbol origin whose only use is a comment refuses clean source export
rendered operand symbol whose address identity differs from origin refuses
```

### Slice 9: Manual/Edit Validation

Ensure Manual Seeds, Manual Labels, Manual Representations, runtime refs, and
execution views all feed the same C validation.

Implementation order:

```text
1. Preserve Python as the manual-log projection adapter only.
2. Tag policy-derived C facts with manual origin information instead of
   collapsing them into generic policy entry points.
3. Convert manual code seeds into M68kCodeOriginIR and run accepted-code audit.
4. Convert manual data seeds into range ownership or structured-data evidence.
5. Convert manual labels into M68kSymbolOriginIR.
6. Convert manual runtime refs and execution views into address observations,
   runtime identities, and absolute ranges before any code promotion.
7. Convert manual representations and target equates into expected
   rendered-symbol-access facts.
8. Diagnose manual evidence that conflicts with decoded bytes, accepted runs,
   range ownership, address identity, or rendered access output.
9. Delete render-lookup-only manual semantic construction after C emits the
   equivalent facts.
```

Positive fixture: Pandora already has manual code seeds, manual
representations, rsset layout regions, and manual semantic pressure. It should
remain valid, but only because C source-quality proves the projected facts.

Negative fixture: create a small target or test fixture where a manual code seed
lands on known structured data. The editor may record the action, but source
export must refuse it with a source-quality diagnostic.

### Slice 10: Python And Corpus Refresh

Keep Python generic. It indexes C-emitted facts only.

Current Python/search work is mostly ahead of C. The indexer already accepts
both global and section-local arrays for most proposed C facts:

```text
diagnostic:source_quality
source-quality:kind:*
source-quality:severity:*
source-quality:origin:*
analysis:code_origin
analysis:code_origin_class:*
analysis:code_origin_evidence:*
analysis:code_origin:weak
analysis:accepted_code_run
analysis:accepted_code_run_end:*
analysis:accepted_code_run_origin:*
analysis:accepted_code_run:suspicious_end
analysis:address_identity:*
analysis:absolute_address_range:*
analysis:platform_address_use:*
analysis:platform_semantic_use:*      add with M68kPlatformSemanticUseIR
analysis:symbol_origin:*
analysis:expected_symbol_access:*     add with M68kExpectedSymbolAccessIR
analysis:rendered_symbol_access:*
target-pattern:source_quality_*
```

The tests already describe the JSON shape Python expects:

```text
tests/test_target_usage_manifest.py
  test_source_quality_diagnostics_feature_and_xref()
  test_analysis_accepted_code_runs_are_indexed_for_false_code_search()
  test_analysis_code_origins_are_indexed_for_false_code_search()
  test_analysis_address_identities_are_indexed_for_identity_search()
  test_analysis_symbol_facts_are_indexed_for_label_consistency_search()
  test_analysis_range_facts_are_indexed_for_range_search()
  test_analysis_table_facts_are_indexed_for_table_search()
  test_analysis_reference_facts_are_indexed_for_observation_search()
  test_analysis_platform_address_uses_are_indexed_for_semantic_search()
  add test_analysis_platform_semantic_uses_are_indexed_for_semantic_search()
  add test_analysis_expected_symbol_accesses_are_indexed_for_label_consistency_search()
```

Current implementation check:

```text
amiga_reversing/disasm/corpus_usage.py
  exposes read/query/import helpers for the corpus manifest:
    read_manifest()
    read_xrefs()
    read_snippet_rows()
    feature_list()
    query_targets()
    query_xrefs()
    corpus_import_media_body()

src/scripts/target_usage_manifest.py
  already defines xref kinds and feature groups for:
    analysis:accepted_code_run*
    analysis:code_origin*
    analysis:address_identity*
    analysis:absolute_address_range*
    analysis:symbol_origin*
    analysis:rendered_symbol_access*
    analysis:table_descriptor*
    analysis:table_consumer*
    analysis:table_entry*
    analysis:data_reference*
    analysis:address_observation*
    analysis:platform_address_use*

  add alongside C export:
    analysis:platform_semantic_use*
    analysis:expected_symbol_access*

tests/test_target_usage_manifest.py
  already proves synthetic xrefs for the existing proposed final facts
  should add synthetic xrefs for platform_semantic_use and
  expected_symbol_access when those C arrays are exported
  already derives precursor target-pattern rows from existing output pressure

amiga_reversing/tools/precommit.py
  already has a facts-v2 source gate wrapper:
    AMIGA_REVERSING_FULL_REPRO_FACTS_V2_SOURCE_GATE=1

amiga_reversing/web/app.js
  already treats diagnostics as a corpus group:
    diagnostic:*
    source-quality:*

amiga_reversing/tools/platform_kb.py
  reads source_analysis.json, platform_summary.json, and gap inputs for reports
  must remain a report helper, not a semantic source-quality classifier
```

So the clean path is:

```text
C emits facts
  -> source_analysis_to_json() exports the same fields
  -> Python indexes them without inference
  -> corpus search finds fixtures and coverage gaps
```

Use precursor lanes only to find fixtures. They are not authoritative because
they are derived from current rendered output.

The wrapper boundary is:

```text
Python and web may:
  call generation and analysis
  read source_analysis.json, profiles, manifests, xrefs, and snippets
  filter, sort, group, and display C-emitted facts
  import corpus media for reproduction
  orchestrate source gates

Python and web must not:
  decide whether bytes are code or data
  decide whether an address is platform, range-owned, or one-off noise
  create source-quality facts from rendered symptoms
  suppress C source-quality blockers
  promote precursor rows into final truth
```

Do not add more Python inference for this proposal unless a new C fact family
needs a generic index lane. The current gap is C emission, two generic index
lanes for `platform_semantic_use` and `expected_symbol_access`, and refreshed
corpus rows. It is not a reason to move source-quality decisions into Python.

Current checked-in corpus state:

```text
final source-quality lanes:
  no checked-in rows yet for:
    target-pattern:source_quality_false_code
    analysis:accepted_code_run:suspicious_end
    analysis:code_origin:weak
    target-pattern:source_quality_label_consistency
    target-pattern:source_quality_platform_semantics
    target-pattern:source_quality_unowned_range

proposal-specific precursor target-pattern lanes:
  currently zero checked-in rows for:
    target-pattern:source_quality_precursor_false_code
    target-pattern:source_quality_precursor_label_consistency
    target-pattern:source_quality_precursor_platform_semantics
    target-pattern:source_quality_precursor_unowned_range
    target-pattern:source_quality_precursor_runtime_identity
    target-pattern:source_quality_precursor_table_range

  this is a checked-in corpus refresh gap, not missing Python capability:
    src/scripts/target_usage_manifest.py already maps
    orphan-code:context:accepted_code_boundary to
    target-pattern:source_quality_precursor_false_code

precursor lanes:
  orphan-code:context:accepted_code_boundary finds 62 current targets
  orphan-code:reason:terminal_decode finds 254 current targets
  orphan-code:status:unresolved finds 254 current targets
  orphan-code:context:renderable_label finds 235 current targets
  memory-layout-view:absolute_owner:cpu_vector finds 116 current targets
  memory-layout-view:absolute_owner:absolute_memory finds 114 current targets
  memory-layout-view:absolute_owner:section_storage finds 130 current targets
  memory-layout-view:absolute_owner:runtime_range finds 21 current targets
  runtime:suppressed_org_range finds 23 current targets
  runtime:copied_code finds 24 current targets
  table:source_pattern:indexed_local_pointer_read finds 17 current targets
  table:source_pattern:indexed_local_scalar_read finds 1 current target
  memory-layout-view:absolute_unowned_one_off currently finds zero rows
```

The source-quality `target-pattern:*` rules exist in
`src/scripts/target_usage_manifest.py`, but the checked-in manifest has not
been refreshed since those rows were added. Do not add Python classifiers to
paper over that. The next corpus step is to emit the C fact families, rebuild
the corpus outputs, and then use the existing final lanes for search.

Representative accepted-code-boundary precursor rows:

```text
Starglider / SG
  corpus source_id: amiga-hunk/c1ed77bc6e32
  repeated accepted-code-boundary pressure in the game executable

Pandora / c/show
  corpus source_id: amiga-hunk/62541881e8b7
  accepted-code-boundary rows at offsets $0B86 and $0ECE

Damocles / Damocles and c/ed
  corpus source_ids: amiga-hunk/71e96e192663, amiga-hunk/3f3009bac481
  useful for Amiga hunk pressure separate from the native Tetragon child

Midwinter II / mwii
  corpus source_id: amiga-hunk/87deaf4aa606
  19 accepted-code-boundary rows, 133 terminal-decode rows, 133 unresolved
  orphan-code rows, plus indexed-local-pointer-table pressure

Voodoo Nightmare / run
  corpus source_ids: amiga-hunk/64a1e661103a, amiga-hunk/abcec3459986
  copied-code and suppressed-org pressure in two variants

Magicland Dizzy / MD
  corpus source_id: amiga-hunk/f26cb8133afe
  eight copied-code rows, seven suppressed-org rows, and pointer-table pressure

3D Construction Kit II / 3d2.exe
  corpus source_id: amiga-hunk/b3df48ed8085
  56 terminal-decode rows, copied-code, suppressed-org, and low-address
  platform-name pressure

Carrier Command / Carrier
  corpus source_id: amiga-hunk/5855d79d8920
  copied-code rows include copied data/code bodies at small and high runtime
  addresses; useful for runtime identity splits already covered by a project
  target

Bloodwych Extended Levels / C/BEXT
  corpus source_id: amiga-hunk/2bd7cb30c832
  runtime copied-code rows plus hardware interrupt masking; useful corpus-only
  pressure unless current Bloodwych target lacks the same mechanism

Workbench and bundled library/device hunks
  useful negative fixtures for OS/library noise
  not primary game coverage

Devpac / GenAm / MonAm tool hunks
  many accepted-code-boundary rows
  useful negative coverage for assembler/tool binaries
  not primary game-source fixtures
```

The current project already has targets for Damocles, Starglider, Pandora,
Conqueror, Bloodwych, Magicland Dizzy, Search For The King, Carrier Command,
Midwinter, and Voodoo Nightmare. Use those before importing new corpus targets.
Import Midwinter II only if existing projects do not provide enough
label/orphan-code scale. Import 3D Construction Kit II only if runtime identity
needs a larger non-Novagen, non-Rainbird fixture after Voodoo, Carrier, and
Magicland have been exercised.

### Slice 11: Delete Render/JSON Semantic Producers

As each C fact family lands, delete the render or JSON producer that used to
create the same meaning. Do this in the same slice as the replacement fact when
possible.

Do not leave compatibility paths. A renderer helper either formats C-approved
facts or it is removed.

## Fixture Matrix

Primary fixtures:

```text
Damocles Tetragon payload 2
  preserve:
    valid decompressed entrypoint at $59484
    true vector installs at $6C/$70/$14
    bitmap/source/storage range copies such as $6D480->$7D480
    low absolute application storage base $3FC with high field offsets
  reject/diagnose:
    false accepted ori run at $42C00
    split identity across $42C00/$42C6C/$42C70/$459BA/$459C6
    false vector base $74 + large offsets
    raw absolute_slot labels emitted where a range identity should exist

Starglider
  preserve:
    true vector installs for levels 1-7 and spurious vector
  reject/diagnose:
    dc.l table target loc_0_00006098 becoming code from shape only
    ori-like false code island

Pandora
  preserve:
    valid ori/hardware setup and blitter/DMA writes
    true vector write to level 3 autovector
    word-offset string table with 114 relative data references
    pc-relative indexed indirect dispatch with 33 accepted code entries
    manual code seeds, representations, and rsset layouts after C validation
  reject/diagnose:
    false weak-origin code at abs_0_0004E3EC
    manual evidence that bypasses accepted-run/range/symbol-access checks

Conqueror
  preserve:
    runtime staging at $4 and $40
    final decrunched code load/entry at $400
  reject/diagnose:
    treating low addresses as CPU vectors by address alone

Bloodwych
  preserve:
    vector fill loop from $60 and explicit handler installs
    indexed scalar table with numeric entries only
    small pointer table whose accepted references remain proven
  reject/diagnose:
    vector-numbered arithmetic base cases without vector-use shape

Magicland Dizzy
  preserve:
    dense low absolute app storage
    runtime code staging around $100/$318 when executor evidence proves it
  reject/diagnose:
    one-off or sparse non-system absolute refs with no range owner

Voodoo Nightmare
  preserve:
    existing project target coverage for the run hunk
    section copy to runtime $400 that is suppressed as source
    section copy to runtime $78000 that remains materialized
    byte lookup tables that must stay data, not weak code origins
  reject/diagnose:
    low absolute slots such as $2 unless a real platform use-shape exists
    copied runtime ranges that do not prove their source bytes are ordinary code

Carrier Command
  preserve:
    existing project target coverage
    larger copied-code and suppressed-org pressure than the small bootstrap cases
  reject/diagnose:
    runtime identity splits where source, materialized copy, and address refs
    disagree

Search For The King
  preserve:
    existing project target coverage
    dense absolute-memory pressure
    real Amiga platform semantics
  reject/diagnose:
    orphan-code precursor ranges with accepted-code boundaries
    renderable-label orphan-code pressure
    false CPU-vector naming by numeric address alone
```

Corpus import rule:

```text
Prefer existing project targets.
Import a corpus target only when it proves a distinct mechanism.
Use top precursor rows first.
Treat Workbench and bundled library/device hunks as negative platform fixtures.
```

Current import recommendation:

```text
do not import yet:
  Damocles, Starglider, Pandora, Conqueror, Bloodwych, Magicland Dizzy,
  Search For The King, Carrier Command, Midwinter, and Voodoo Nightmare already
  exist as project targets

consider importing later:
  Midwinter II / mwii
    when label/orphan-code scale is needed beyond current project targets

  3D Construction Kit II / 3d2.exe
    when runtime identity needs a larger non-existing project fixture

keep corpus-only unless needed for a platform regression:
  Workbench l/Pipe-Handler
  Workbench System/DiskCopy
  Workbench l/FastFileSystem
  bundled libs/info.library, libs/icon.library, libs/mathtrans.library
  Atari ST Voodoo Nightmare AUTO/F13.PRG
    useful for cross-platform indexed-local-scalar-table pressure only after
    the generic C table facts are proven on Amiga targets
```

## Verification Gates

IR gate:

```text
src/m68k_ir.h
src/m68k_ir.c
src/test_m68k_ir.c

Proves enum names, append helpers, deep-copy, destroy, and JSON-safe string
ownership for each new fact family.
```

Analysis gate:

```text
src/m68k_analysis_facts_v2.c
source-quality C module tests

Proves:
  address reference does not become code
  weak origin cannot silently seed accepted code
  accepted run ending in data/decode gap is diagnosed or demoted
  unterminated code conversion is diagnosed before render
  manual code seed still passes the same audit
  manual label without visible access produces diagnostics
  source-quality errors feed the existing source-refusal path
```

Render gate:

```text
src/m68k_render_ir.c
src/m68k_source_ir_render.c

Proves:
  renderer consumes C facts
  numeric vector fallback is gone
  generated symbol stripping is unreachable or diagnosed
  round-trip still passes
```

Corpus/search gate:

```text
tests/test_target_usage_manifest.py
fresh corpus/target_usage_manifest.jsonl

Proves:
  synthetic exported C facts remain searchable
  precursor source-quality lanes still find known pressure
  final source-quality lanes appear after C emits facts
  xrefs point back to section/offset or listing evidence
```

Target gate:

```text
Damocles Tetragon payload 2
Starglider
Pandora
Conqueror
Bloodwych
Magicland Dizzy
Search For The King
```

Output-affecting changes still require normal project verification:

```text
cmd /c src\precommit.bat
round-trip verification for changed rendered targets
git diff --check
```

## Acceptance Criteria

- Damocles `$42C00`, `$42C6C`, `$42C70`, `$459BA`, and `$459C6` share an
  in-image address identity and ownership model.
- The false Damocles `$42C00` `ori` run is not silently accepted as code.
- Starglider and Pandora false-code blocks hit the same diagnostic/fix path.
- Unterminated or weak code conversions become source-quality diagnostics
  before render.
- Every accepted code range exposes executable-origin proof.
- Every accepted code origin exposes an evidence subkind; `CONTROL_TARGET`
  alone is not accepted as proof.
- Every accepted code run has terminal flow, proven transfer, or explicit range
  boundary; weak fallthrough into data is diagnosed or demoted.
- Address/data references no longer promote code by themselves.
- Address-like operands in supported instruction forms produce C observations.
- `M68kAbsoluteMemoryRefIR` is deleted; final consumers use address
  observations, identities, and ranges.
- `$74 + displacement` style base addressing becomes a low-memory base/storage
  observation, not a CPU-vector use.
- One-off and sparse non-system absolute refs are grouped into candidate ranges
  or diagnosed as missing ownership.
- True vector installs and vector fill loops still render with vector
  semantics.
- Dense low absolute app storage, such as Magicland, is preserved as app
  storage, not vector semantics.
- Platform adapter functions report possible platform domains and sinks; they
  do not decide renderable use semantics by numeric address alone.
- CPU-vector owner facts are not rendered as vector symbols without a
  `platform_address_use` vector-semantic shape.
- Hardware register symbols and comments come from C-owned platform address use
  facts, not renderer-side address lookups.
- Copper, bitmap, display, audio, disk-buffer, and blitter semantics come from
  `M68kPlatformSemanticUseIR`, not renderer-side Amiga inference helpers.
- Table/range candidates have C-owned consumer evidence or a structured
  non-classification reason.
- Manual code seeds count as explicit origin evidence but still fail or emit
  diagnostics when invalid, overlapping, unterminated, or unrenderable.
- Manual labels create symbol evidence, not code evidence.
- Manual runtime refs create address evidence, not code proof by themselves.
- Rendered labels have visible references, explicit structured origins, or are
  not emitted.
- Expected symbol accesses are represented in C by
  `M68kExpectedSymbolAccessIR` before rendering chooses operand text.
- `M68K_FACT_LABEL_CREATED` and `M68K_FACT_LABEL_REQUIRED` are deleted from the
  final source-quality path unless a remaining distinct non-symbol role is
  proven.
- Labels present in source but unused by rendered operands produce C
  diagnostics, not renderer-only silence.
- Numeric operands that target C-owned in-image storage either render through
  the approved symbol or produce an expected-access diagnostic.
- Generated-symbol stripping is unreachable in clean output or emits a
  source-quality diagnostic.
- Render preview no longer creates durable accepted-code, range-ownership,
  table, data-reference, platform, or label-consistency facts.
- Render preview receives `M68kSourceAnalysisIR` as semantic input and may only
  record actual rendered accesses or true render/export failures.
- Renderer and JSON no longer expand numeric CPU-vector ownership into symbols.
- Renderer-owned table, absolute-memory-header, platform-semantic, and
  label-consistency helpers are deleted once equivalent C facts exist; the same
  complexity must not reappear in Python or JSON export code.
- Source-quality diagnostics are queryable through corpus feature lanes.
- Blocking source-quality diagnostics feed `asm_source_refused` before render
  preview.
- Source-quality fact production has no silent fixed-capacity truncation.
- Output-affecting changes have focused fixture coverage and round-trip checks.

## Non-Goals

- Do not hand-edit target outputs as the fix.
- Do not add Damocles-only, Starglider-only, or Pandora-only recognizers for
  general source-quality failures.
- Do not add an `ori` opcode blacklist.
- Do not move source-quality decisions into Python.
- Do not assign platform names in renderers from numeric address values alone.
- Do not keep numeric-vector renderer fallbacks once semantic facts exist.
- Do not suppress diagnostics to make generation appear clean.
- Do not let manual/editor-created code blocks bypass C source-quality
  validation.
- Do not silently truncate semantic tables, target sets, range observations, or
  symbol-access facts because a fixed local capacity was reached.
- Do not preserve flawed legacy behavior for compatibility.

## Resolution Notes

Add dated or commit-scoped notes here as implementation lands. Each note should
name the fixture, the C fact or diagnostic added, and the target evidence it
resolves.

### Source-Quality Diagnostic IR Bootstrap

Implemented the first durable C Source Analysis IR lane:

```text
M68kSourceQualityDiagnosticIR
  -> source-level diagnostics
  -> section-level diagnostics
  -> source_analysis_to_json()
  -> Python target usage manifest feature/xref indexing
```

The first producer is the existing table-target-set capacity source blocker.
It now emits both:

```text
M68kIncompleteAnalysisIR(kind = capacity_exhausted, source_kind = table_target_set)
M68kSourceQualityDiagnosticIR(kind = table_target_set_limit, blocker = true)
```

This does not complete source-quality hardening. It removes the previous
profile-only blind spot for one existing blocker and creates the C-owned JSON
surface needed for later false-code, address-identity, platform-semantics, and
symbol-access diagnostics.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py::test_source_quality_diagnostics_feature_and_xref tests\test_target_usage_manifest.py::test_source_quality_precursor_target_patterns_are_derived_from_existing_features -q
```

### Code Origins And Accepted Runs Bootstrap

Implemented the first accepted-code source-quality fact families:

```text
M68kCodeOriginIR
  -> per-section executable origin observations derived from C code-start refs
  -> origin classes distinguish strong entries, platform semantic entries,
     proven control targets, fallthrough, and runtime aliases

M68kAcceptedCodeRunIR
  -> contiguous accepted-code byte runs
  -> instruction count
  -> run-end classification
  -> JSON export through source_analysis_to_json()
```

This is intentionally not the final false-code proof. It gives the C pipeline
a durable surface for "what accepted this code?" and "where does this accepted
run end?" so later source-quality checks can refuse weak runs without scraping
rendered source text.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
```

### Accepted-Code Origin Blocker

Added the first source-quality audit rule over accepted runs:

```text
accepted code run
  -> must contain an executable origin stronger than fallthrough
  -> otherwise emits accepted_code_without_executable_origin
  -> diagnostic severity error
  -> blocker true
```

The analyzer also reads C CFG edges to refine accepted-run endings:

```text
return edge at run end -> terminal
jump edge at run end   -> proven_transfer
otherwise a non-section-end run remains accepted_gap
```

`accepted_gap` now emits a non-blocking
`unterminated_or_invalid_code_range` warning when the run has a real origin but
no terminal/proven-transfer ending yet. This keeps the current output from
being silently reclassified while making the residual source-quality weakness
queryable and visible through C facts.

Facts-v2 profiles now count source-quality diagnostics and blockers, expose the
first source-quality diagnostic, and map blocking source-quality failures to
the source refusal summary. This is still running after render preview because
render preview currently creates some required section-analysis inputs; moving
those producers before render remains required before Proposal 032 can close.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
git diff --check
```

### Address Observation Migration Surface

Added the first C-owned address observation fact family:

```text
M68kAddressObservationIR
  -> source section offset
  -> operand index
  -> raw/address value
  -> target section/offset when known
  -> access width/kind
  -> source kind
```

The initial producer was a migration bridge from existing C facts:

```text
M68kAbsoluteMemoryRefIR
  -> address_observation(source = absolute_operand)

M68kRuntimeAddressRefIR
  -> address_observation(source = runtime_address_ref)
```

The migration is now complete for direct absolute operands:
`M68kAbsoluteMemoryRefIR` has been removed from `M68kSectionAnalysisIR`.
Accepted-code and orphan-code operand scans append
`M68kAddressObservationIR(source = absolute_operand)` directly. Runtime address
refs still become observations in source-quality analysis because they remain a
distinct runtime-source fact family.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
git diff --check
```

### Address Identity And Range Bootstrap

Added the first C-owned grouping layer over address observations:

```text
M68kAddressIdentityIR
  -> groups address observations by observed address
  -> records owner kind, role kind, source provenance, runtime-address presence,
     observation count, and conflict state
  -> writes identity_id back onto M68kAddressObservationIR

M68kAbsoluteAddressRangeIR
  -> summarizes each address identity as an absolute-address range record
  -> records owner, status, access kind, read/write/access counts, and source
     provenance
```

This is still a bootstrap, not the final range model. It creates the durable C
fact families and JSON surface that the manifest already indexes for:

```text
analysis:address_identity
analysis:address_identity:conflict
analysis:absolute_address_range
analysis:absolute_address_range:unowned_one_off
analysis:absolute_address_range:unowned_sparse
```

The current producer is intentionally conservative:

```text
absolute operand observations + runtime refs
  -> address observations
  -> address identities
  -> absolute address ranges
```

`M68kAbsoluteMemoryRefIR` is no longer present in source analysis. The remaining
renderer/platform semantic cleanup must consume the observation, identity, and
range facts directly instead of rebuilding equivalent views.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
```

### Platform Address Use Bootstrap

Added the first C-owned platform-address-use fact family:

```text
M68kPlatformAddressUseIR
  -> section offset / operand index
  -> observed address and effective address
  -> access kind and width
  -> use shape
  -> confidence
```

The initial producer derives use-shape records from C address observations:

```text
CPU vector + memory write     -> true_vector_install
CPU vector + compute address  -> low_memory_base
CPU vector + read             -> low_memory_storage
hardware register/range       -> hardware_register_access
ExecBase literal              -> execbase_literal
low absolute non-owner access -> low_memory_base / low_memory_storage
```

This does not yet remove renderer-side symbol lookup. It establishes the
source-analysis fact lane that later renderer cleanup must consume before
rendering CPU vectors or hardware names.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
```

### Accepted Code Range Ownership Migration

Moved accepted-code range ownership out of render preview and into the C
source-quality analyzer:

```text
M68kSectionAnalysisIR.certain_code_byte
  -> m68k_source_quality_analyze()
  -> M68kRangeOwnershipIR(kind = code, status = accepted)
```

`m68k_render_ir_preview_build()` no longer appends accepted-code
`range_ownerships`. Rendering still builds the source-analysis shell for now,
but this specific durable semantic fact is now owned by source-quality analysis
beside `M68kAcceptedCodeRunIR`, so later render cleanup can consume rather than
produce it.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Prepared Render Lookup And Pre-Render Source Quality

Moved the remaining source-analysis build point ahead of source rendering:

```text
facts_v2_collect_profile_internal()
  -> build render lookup
  -> run platform lookup passes
  -> materialize lookup-derived labels
  -> build Source Analysis IR from the prepared lookup
  -> append storage/incomplete/recovered/address/media facts
  -> run m68k_source_quality_analyze()
  -> source blocker check
  -> emit source from prepared lookup + const Source Analysis IR
```

Render preview no longer owns the source-analysis lifecycle or the blocker
ordering. It receives a prepared lookup plus completed source-analysis input
and formats output. Source-quality blockers are now counted before render
emission, so byte-real source with source-quality failures can be refused
without waiting for `.s` text generation.

The old `m68k_render_ir_preview_build(..., out_source_analysis)` compatibility
surface was removed instead of preserved. This codebase has no external API
customers, so the internal C tests now use a local helper over the prepared
lookup API rather than carrying a production wrapper for a stale ownership
model.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Absolute Memory Header From Source-Quality Ranges

Removed the render-side absolute-memory header scan:

```text
deleted:
  render_absolute_memory_header_collect()
  render_absolute_memory_header_add_range()
  render_absolute_memory_header_coalesce()

kept:
  SourceQuality address observations
  M68kAddressIdentityIR
  M68kAbsoluteAddressRangeIR
```

Source rendering now formats the memory-map absolute reference header from
`M68kSourceAnalysisIR.absolute_address_ranges`. Render no longer walks accepted
instructions to decide which absolute operands are meaningful for that header.
The source-quality pass sorts and coalesces absolute ranges so the durable C
facts remain stable and readable before presentation sees them.

The target re-render changed only generated source comments in the memory-map
header. Round-trip stayed exact/content-exact with the existing container
policy. The visible effect is that the header no longer reports render-local
operand scan output; it reports source-quality-owned unowned absolute ranges.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --update-rendered-source --json
```

### Render Walk Source-Analysis Decoupling

Moved source-analysis section assembly out of the source row walk:

```text
before:
  m68k_render_ir_preview_build()
    walks rendered rows
    mutates M68kSectionAnalysisIR while emitting labels
    appends CFG/orphan/platform facts at the end of each rendered section

after:
  m68k_render_ir_preview_build()
    builds lookup/platform passes
    builds source-analysis sections before presentation rows
    walks rows only for source/text/plan presentation
```

This removes the row-emission dependency from durable section analysis. Null
analysis policy remains a supported internal call shape because the render path
already accepts it; this is not a compatibility shim for external consumers.

The remaining ownership gap is narrower: some producers still live in
`m68k_render_ir.c`, but they no longer depend on row emission as their control
flow. Next cleanup should move those producers behind a C analysis/source-quality
entry point and make render preview consume the completed analysis model.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Code Origin Evidence Naming

Made `M68kCodeOriginIR.evidence_kind` a named C source-quality evidence value
instead of exporting the old numeric code-start reason as the public evidence
field:

```text
before:
  evidence_kind = 3
  reason_name = policy_entry_point

after:
  evidence_kind_id = 3
  evidence_kind = policy_entry_point
  reason_name = policy_entry_point
```

The mapper now distinguishes entry, fallthrough, runtime-view, platform,
stack-continuation, direct-control, runtime-control, relocation-backed control,
traced indirect control, dispatch-table control, callback-field control,
vector-store control, and runtime-copy control origins. There is no compatibility
alias for broad control-target evidence: a producer that cannot name its
evidence source reports `unknown`, which is a real analysis gap.

### Code Origin Evidence Producer Storage

Moved code-origin evidence from a source-quality-side reconstruction into the
producer-owned fact path:

```text
enqueue/prove code start
  -> M68kFact.code_start_evidence_kind
  -> M68kCodeStartRefIR.evidence_kind
  -> M68kCodeOriginIR.evidence_kind
  -> JSON/report names
```

Direct decoded branch/call/jump targets now carry
`direct_control_target`; runtime-translated targets carry
`runtime_control_target`. Source quality no longer reconstructs evidence from
the generic code-start reason. Missing evidence remains `unknown`, which makes
the producer gap visible instead of hiding it behind compatibility inference.

### Control Origin Producer Evidence Split

Removed the broad control-target evidence value instead of keeping it as an API
compatibility alias. `CONTROL_TARGET` with no producer-owned evidence now
exports `unknown`, and each resolved producer threads the specific evidence it
owns:

```text
decoded direct branch/call/jump    -> direct_control_target
runtime-translated branch/call/jump -> runtime_control_target
relocation-backed control target   -> relocation_control_target
trace-derived indirect target      -> traced_indirect_control_target
dispatch/jump table target         -> dispatch_table_control_target
callback field target              -> callback_field_control_target
interrupt/vector store target      -> vector_store_control_target
copied/runtime entry target        -> runtime_copy_control_target
```

This deliberately breaks the old numeric evidence IDs. They are internal C IR
values, not a public compatibility contract.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### CFG Source-Analysis Producer Split And Weak Code Prune

Moved CFG block/edge construction for Source Analysis IR out of
`m68k_render_ir.c` and into `m68k_analysis_render_lookup.c`:

```text
accepted section bytes
  -> m68k_analysis_render_lookup_append_cfg_for_section()
  -> M68kCfgBlockIR / M68kCfgEdgeIR
  -> render preview consumes the generated section-analysis facts
```

The render preview still calls the producer during the migration window, but
the durable CFG source-analysis construction is no longer implemented in the
source row renderer. Remaining render-side CFG helpers are limited to current
orphan-code presentation/analysis seams and should be removed when orphan-code
signal production moves fully before render.

Removed relocation-backed function-pointer table promotion as executable proof:

```text
relocated pointer-like data table
  -> labels/data references may remain
  -> target bytes do not become accepted code

accepted dispatch/control use
  -> still promotes code through the normal traced control-flow/table paths
```

Added an accepted-code reachability prune after platform/runtime seeding:

```text
executable seed origins
  -> walk accepted direct targets and normal fallthrough
  -> keep reachable accepted starts
  -> demote accepted starts that are only disconnected shape/data artifacts
```

This directly addresses the Starglider and Midwinter II source-quality failures
where disconnected accepted islands followed rejected candidates. The rendered
source now preserves those bytes as data instead of treating them as credible
code, while all rendered-source round-trip checks remain exact or content-exact
according to their existing container policy.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Pre-Render Source Blocker Diagnostics

Moved pre-render-safe source-analysis facts ahead of render preview:

```text
object platform storage layouts
  -> M68kSourceAnalysisIR before render preview

table target set capacity hit
  -> M68kIncompleteAnalysisIR before render preview
  -> M68kSourceQualityDiagnosticIR(blocker) before render preview
  -> asm_source_refused before render preview
```

`facts_v2_has_source_blockers()` now includes source-quality blockers, and the
profile source-quality counters are recomputed from `M68kSourceAnalysisIR` so
the pre-render and post-render passes do not double count diagnostics. This is
still partial: diagnostics that depend on render-owned section/base-layout
producers cannot move earlier until those producers are removed from render.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Amiga LVO Call Fact Collection

Moved Amiga LVO call fact collection onto the collect-only source-analysis path.
The resolver is shared by source rendering, immediate-argument lookahead, and
analysis-only collection:

```text
accepted Amiga instruction candidate
  -> shared Amiga vector resolver
  -> platform call fact
  -> recovered platform effects
```

The shared resolver preserves the existing resolution order:

```text
state-known A6 base
  -> direct wrapper
  -> indexed wrapper dispatch
  -> immediate LVO
  -> local helper summary
```

Render output still uses that same resolver for operand text, but the recovered
platform call fact no longer requires rendering `asm.s`. The new regression
proves `_LVOForbid` is collected from an accepted Amiga instruction stream with
`m68k_facts_v2_collect_source_analysis_profile()`, and that the resolved call
does not also surface as an unresolved indirect site.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Platform Seed Analysis Split

Moved platform register-seed application out of the source-render-only block.
Policy and lookup seeds now update the platform analysis state whenever source
analysis is being built:

```text
analysis loop offset
  -> policy register seeds
  -> lookup register seeds
  -> collect-only platform facts or source rendering
```

The render branch still owns only the visible seed comments. The new regression
proves a policy-seeded `exec.library` A6 base produces a recovered `_LVOAlert`
platform call through `m68k_facts_v2_collect_source_analysis_profile()` without
rendering `asm.s`.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Amiga LVO Fact Append Pre-Render Split

Removed the durable Amiga LVO call/effect fact append from
`render_asm_instruction()`. The accepted-candidate loop now records those facts
before optional instruction rendering:

```text
accepted Amiga instruction candidate
  -> shared Amiga vector resolver
  -> recovered_platform_call / recovered_platform_effect
  -> optional source instruction rendering
```

The renderer still uses the shared resolver to format operands and advance
platform state, but it no longer owns the semantic fact append. Collect-only
runs advance platform state through the same resolver without invoking source
formatting.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Base Layout Fact Append Split

Moved RSSET/base-layout fact append out of the header source renderer:

```text
m68k_render_ir_preview_build(..., out_source_analysis)
  -> render lookup platform/app-slot pass
  -> append base-layout fields before source text rendering

render_asm_app_extension_rs()
  -> formats RSSET/header rows only
```

This is a migration split, not the final ownership shape. Durable
`base_layout_field` records are no longer appended by the function that writes
RSSET text, and collect-only source analysis now proves app-slot layout fields
without rendering source. Full closeout still needs the app/base-slot producer
to move into pre-render source-quality/platform analysis so the renderer reads
finished layout facts instead of rebuilding the same slot list for presentation.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Mac Opcode Call Fact Render Decoupling

Mac OS opcode call facts no longer depend on rendering source text. The preview
loop now records the resolved opcode call and generated stack/type facts before
the source formatter branch:

```text
accepted opcode word
  -> platform_facts_v2_resolve_opcode_call()
  -> recovered_platform_call / recovered_function_arg / typed_access facts
  -> optional source text row
```

The regression covers collect-only analysis for `_GetFNum`:

```text
m68k_facts_v2_collect_source_analysis_profile()
  -> recovered_platform_call(_GetFNum)
```

This did not finish platform-call ownership by itself. Later slices moved
trap-call and Amiga LVO/wrapper facts onto collect-only analysis as well, then
the platform-call analysis pass extraction made those producers a named
pre-render section pass instead of inline render-loop hooks.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Trap Call Fact Render Decoupling

Atari/Mac trap-style instruction call facts now append from the accepted
candidate loop instead of `render_asm_instruction()`:

```text
accepted instruction candidate
  -> platform_facts_v2_resolve_trap_call()
  -> recovered_platform_call
  -> optional instruction source rendering
```

The regression covers collect-only analysis for Atari `m_shrink`; rendering
source is no longer required for that platform-call fact to exist.

This was still a migration step when landed. Later slices moved the Amiga
LVO/wrapper path onto collect-only analysis with a shared resolver, then
extracted the pre-render platform-call analysis pass so durable platform-call
facts are no longer appended from the render row walk.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Structured Data Range Ownership Migration

Moved structured-data range ownership export out of render preview and into
source-quality analysis:

```text
M68kAnalysisStructuredDataItem
  -> shared IR range kind/evidence helpers
  -> m68k_source_quality_analyze()
  -> M68kRangeOwnershipIR(text/table/structured/platform_metadata)
```

`m68k_render_ir_preview_build()` no longer appends lookup-owned
`range_ownerships` into Source Analysis IR. Render lookup still keeps an
internal range view for formatting and boundary decisions, but the durable
source-analysis fact is now emitted from the C analysis item model.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Table Descriptor And Consumer Migration

Moved structured-data table descriptor and consumer fact export out of render
preview and into source-quality analysis:

```text
M68kAnalysisStructuredDataItem(table metadata)
  -> shared IR table entry-size helper
  -> m68k_source_quality_analyze()
  -> M68kTableDescriptorIR
  -> M68kTableConsumerIR
```

Render preview still emits byte-dependent table entries and data references,
because those currently read section bytes and accepted-code maps. The durable
descriptor/consumer facts are now C source-quality facts, not render-export
facts.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Table Entry And Data Reference Migration

Removed the remaining durable table-entry/data-reference export from render
preview. Source-quality analysis now receives the decode IR plus accepted-code
maps directly:

```text
M68kAnalysisStructuredDataItem + M68kDecodeSectionIR bytes
  -> m68k_source_quality_analyze()
  -> M68kTableEntryIR
  -> M68kDataReferenceIR
```

This keeps byte-dependent facts in C analysis while preserving the previous
render behavior:

```text
word relative table entry       -> signed target from table base
keyed long relative table entry -> signed high-word target
pointer/absolute long table     -> source/runtime label-backed target, else numeric exact
code dispatch target            -> accepted/interior/unresolved status from accepted-code maps
data table target               -> accepted data reference with structured/text/string evidence
```

No compatibility wrapper was kept. `m68k_source_quality_analyze()` is the single
internal API because this codebase has no external consumers to preserve.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Immediate Text Token Migration

Moved immediate printable-token facts out of render preview and into
source-quality analysis:

```text
accepted M68kDecodeCandidate immediate operands
  -> shared decode effective-size helper
  -> shared operand immediate-value helper
  -> m68k_source_quality_analyze()
  -> M68kImmediateTextTokenIR
```

The source-quality module now emits these operand facts from accepted decode
rows. Render and render-lookup call the shared C IR helpers directly; the old
local compatibility wrappers were removed because this codebase has no external
API consumers to preserve.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Orphan Conflict Range Migration

Moved orphan-code conflict range ownership out of render preview and into
source-quality analysis:

```text
M68kOrphanCodeSignalIR with nearby data relation
  -> m68k_source_quality_analyze()
  -> M68kRangeOwnershipIR(kind = conflict, status = conflict)
```

Render still discovers orphan-code signals for now because that pass depends on
render lookup boundaries and structured-data overlap checks. The conflict range
derived from those signals is no longer renderer-owned.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Stack Cleanup Fact Append Pre-Render Split

Moved Atari stack-cleanup platform call fact append out of source rendering.
The accepted-candidate pass now records both the direct trap call and the
following cleanup fact before optional `.s` emission:

```text
accepted trap call + accepted stack cleanup instruction
  -> platform_facts_v2_resolve_stack_cleanup_call()
  -> M68kRecoveredPlatformCallIR(note = stack_cleanup)
```

`attach_platform_stack_cleanup_comment_for_render()` now only formats the
human-facing comment. It no longer receives `M68kSectionAnalysisIR`, so it
cannot mutate durable analysis facts while rendering. The regression uses a
generated Atari `Crawcin` metadata row because that call has known caller stack
cleanup; calls with unknown cleanup, such as `Mshrink`, correctly do not produce
a cleanup fact.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Platform Call Analysis Pass Extraction

Extracted the remaining inline platform-call fact hooks from the mixed render
loop into a named pre-render section pass:

```text
accepted section bytes
  -> m68k_analysis_render_lookup_append_platform_call_facts_for_section()
  -> direct trap call facts
  -> stack-cleanup facts
  -> Mac opcode call and stack-argument facts
  -> Amiga LVO/direct-wrapper/local-helper facts
```

The render loop still resolves platform calls to format source text, but it no
longer appends durable recovered platform-call facts while emitting rows. The
analysis pass owns its own platform state, Mac stack-argument recovery, and
Amiga vector-call fact emission. The shared Amiga vector resolver now lives in
`m68k_analysis_render_lookup.c`; render calls it only to format proven symbolic
presentation. This keeps rendered-source presentation and collect-only source
analysis aligned without preserving a render-time compatibility path.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Absolute Operand Observation Direct Ownership

Removed the temporary absolute-memory-ref source-analysis IR:

```text
deleted:
  M68kAbsoluteMemoryRefIR
  M68kSectionAnalysisIR.absolute_memory_refs
  m68k_ir_section_analysis_append_absolute_memory_ref()

kept as durable C facts:
  M68kAddressObservationIR(source = absolute_operand)
  M68kAddressIdentityIR
  M68kAbsoluteAddressRangeIR
  M68kPlatformAddressUseIR
```

Accepted instructions now append absolute/address-domain operands directly as
address observations:

```text
accepted M68kDecodeCandidate operand
  -> absolute operand or address-domain immediate
  -> platform/runtime/relocation owner classification
  -> M68kAddressObservationIR(source = absolute_operand)
```

The orphan-code signal path does the same for unresolved terminal islands. The
memory-layout JSON surface now emits these as
`record_kind = "address_observation"` instead of exposing the removed
intermediate record. The per-section `address_observations` JSON rows expose
owner kind, owner offset, conflict state, and identity id directly. This
intentionally breaks the old internal schema rather than preserving a
compatibility wrapper.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Absolute Memory Header Collection Cap Removal

Removed the fixed 256-row collection cap from the render-side absolute-memory
header collector:

```text
before:
  stack buffer[256]
  overflow -> truncated collection

after:
  preview scratch arena array
  grow as needed
  presentation may still show the first 32 ranges with an explicit omission note
```

The larger ownership issue was closed by the later source-quality range
migration: header rows now consume `M68kSourceAnalysisIR.absolute_address_ranges`
instead of rediscovering ranges while rendering. The cap cleanup remains useful
because presentation still limits visible rows deliberately, with an explicit
omission note, instead of silently truncating collection.

Verified:

```text
cmd /c src\build.bat
```

### Source Analysis Lifetime Ownership

Moved `M68kSourceAnalysisIR` creation and destruction out of
`m68k_render_ir_preview_build()` and into `facts_v2_collect_profile_internal()`:

```text
before:
  render preview creates Source Analysis IR
  render preview destroys it on render failure

after:
  facts_v2 creates Source Analysis IR before decode/render handoff
  render preview only appends into an already-created analysis object
  facts_v2 owns failure cleanup
```

This is intentionally not a compatibility-preserving API wrapper. The renderer
must not own the lifetime of the analysis object because source-quality and
platform fact producers need a stable pre-render destination. Remaining work:
move the render-owned section/base-layout producers into that earlier
facts/source-quality phase, then refuse blocked source before preview starts.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Absolute Memory Operand Symbol Ownership

Removed the render-time absolute-memory owner predicate used while formatting
instruction operands:

```text
before:
  render operand
    -> ask platform facts/runtime/source layout whether address is "absolute"
    -> create absolute_slot_* EQU

after:
  facts/source-quality
    -> M68kAddressObservationIR(source = absolute_operand,
                                owner_kind = absolute_memory)
  render operand
    -> find the matching observation for section/offset/operand/address
    -> create absolute_slot_* EQU only from that analysis fact
```

Source rendering now always builds a source-analysis object, even when the
caller only requested emitted text. That deliberately drops the old internal
path where `m68k_facts_v2_render_asm_source_alloc()` could render without the
analysis facts needed by source-quality. The renderer still formats operands,
but the durable answer to "is this an absolute memory use?" now comes from C
analysis records.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --update-rendered-source --json
```

### Render Source Analysis Contract

Deleted the compatibility path where `m68k_render_ir_preview_emit_prepared()`
could render asm source without a `M68kSourceAnalysisIR`:

```text
before:
  render preview receives source_analysis = NULL
    -> reruns platform-call analysis only for preview side effects
    -> renders source anyway

after:
  facts_v2 source export
    -> always creates source_analysis
    -> runs platform/source-quality analysis first
    -> passes source_analysis to render preview

  render preview
    -> refuses asm source without source_analysis
```

This removes a stale internal API shape. Text preview can still run without
source-analysis facts, but asm source export cannot, because operand symbols,
source-quality blockers, and platform facts now depend on the analysis object.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### Source-Analysis Label Producer Split

Moved the section label-offset append out of `m68k_render_ir.c` and into
`m68k_analysis_render_lookup.c`:

```text
before:
  m68k_render_ir_build_source_analysis_from_lookup()
    -> local render helper appends source-analysis labels

after:
  m68k_analysis_render_lookup_append_labels_for_section()
    -> appends label offsets for Source Analysis IR

  m68k_analysis_render_lookup.c
    -> owns the shared label visibility predicate

  render row walk
    -> asks lookup_should_emit_label_statement() for visible labels
```

This is intentionally not a compatibility wrapper. The shared predicate remains
available because presentation still needs the same label visibility decision,
but the durable act of writing labels into `M68kSectionAnalysisIR` now lives in
the analysis module beside CFG construction.

Verified:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests\test_target_usage_manifest.py -q
uv run platform-rendered-source-roundtrip --no-write-report --json
```

### DLL Policy ABI Cleanup

The intermittent `test_ir_policy_dll` access violation was caused by duplicating
the full `M68kAnalysisPolicy` layout in Python. The C struct had moved on; the
ctypes mirror was stale, so C policy-copy code could read invalid trailing
fields.

Removed the Python-owned policy struct mirror. The DLL tests now allocate and
destroy opaque C-owned policies:

```text
platform_file_analysis_policy_create(max_cpu)
  -> C allocates and initializes M68kAnalysisPolicy

platform_file_facts_v2_analysis_*_json(..., policy)
  -> consumes the opaque handle

platform_file_analysis_policy_destroy(policy)
  -> C destroys internal policy storage and frees the object
```

This deliberately drops the old test-side ABI duplication. Python no longer
needs to track every internal analysis-policy field.

Verified:

```text
uv run python -m pytest src\tests\test_ir_policy_dll.py -q
20 consecutive runs of src\tests\test_ir_policy_dll.py
```

### Generic Decode Helper Ownership

Moved `render_section_extent()` and `accepted_start_at()` out of
`m68k_render_ir.c`. They are decode/lookup predicates used by both analysis and
presentation, not renderer-owned formatting behavior. Keeping them with the
analysis/lookup code reduces the remaining render dependency before the larger
RSSET/base-layout extraction.

### Base-Layout Source-Analysis Append Split

Moved the durable base-layout field append out of `m68k_render_ir.c`:

```text
before:
  render_asm_app_extension_rs_append_layout_facts()
    -> collected app/RSSET slots
    -> appended M68kBaseLayoutFieldIR into Source Analysis IR

after:
  m68k_analysis_render_lookup_append_base_layout_fields()
    -> appends M68kBaseLayoutFieldIR into Source Analysis IR

  render_asm_app_extension_rs()
    -> still formats RSSET declarations from the shared slot collection model
```

The shared slot/layout model was also renamed away from `render_app_rs_*` and
`M68kRenderAppRs*`. The remaining gap is module ownership rather than public
API compatibility: the neutral app-layout collector still lives in
`m68k_render_ir.c` because it depends on nearby app/base-slot lookup helpers.
It should move once those dependencies are similarly neutralized, but the
durable Source Analysis IR append no longer has renderer-owned names or a
renderer-owned append path.

### Premature Symbol-Access Manifest Lane Removal

Removed Python manifest support and synthetic tests for `symbol_origins` and
`rendered_symbol_accesses` while C does not export those arrays. Keeping those
lanes made the API look more complete than it is and forced tests to preserve a
future JSON shape with no real C producer.

This does not remove the requirement. The correct implementation remains:

```text
C Source Analysis IR
  -> M68kSymbolOriginIR / M68kExpectedSymbolAccessIR / M68kRenderedSymbolAccessIR
  -> platform_file_json.c exports those arrays
  -> target_usage_manifest.py indexes the exported C facts
```

Until that C path exists, Python should not carry compatibility code for
nonexistent source-quality facts.

### C Symbol-Access Fact Export

Added the C Source Analysis IR rows described above:

```text
M68kSymbolOriginIR
M68kExpectedSymbolAccessIR
M68kRenderedSymbolAccessIR
```

`platform_file_json.c` now exports those rows from C-owned source analysis, and
`target_usage_manifest.py` indexes only the exported C facts. The old Python
manifest shortcut remains deleted; there is no compatibility lane for
nonexistent or guessed facts.

The broad `M68K_FACT_LABEL_CREATED` path has now been deleted. Analysis labels
live in the facts-v2 label lookup and are exported as
`M68kSymbolOriginIR(origin_kind=analysis_label)`. A rendered-access requirement
still must come from a specific render obligation such as a label statement,
operand symbol, branch target, equate, or storage label, not from generic label
existence.

### Post-Render Symbol-Access Gate

Added `m68k_source_quality_analyze_rendered_symbol_accesses()` as a post-render
source-quality pass:

```text
pre-render source-quality:
  code origins, accepted runs, ownership ranges, tables, address identities

render preview/source:
  emits actual rendered symbol-access facts

post-render source-quality:
  expected_symbol_accesses - rendered_symbol_accesses
    -> missing_expected_symbol_access blocker
```

This placement matters. The check is about rendered output, so it runs after
`m68k_render_ir_preview_emit_prepared()` has populated the actual rendered
facts. Running it before render confused valid numeric/data cases with missing
source output.

Current enforced case:

```text
expected: access_kind=label_statement, symbol=loc_0_00000004, offset=4
rendered: no matching non-comment label_statement
result: source_quality diagnostic missing_expected_symbol_access, blocker=true
```

Follow-up work remains to add precise C producers for relocation-backed branch
targets, ordinary operand symbols, equates, storage labels, and independent
label-statement obligations. Those producers must be reason-driven; they must
not reuse broad label-created or label-required facts as a shortcut.

### Actual Rendered Label Access Recording

Moved `M68kRenderedSymbolAccessIR(access_kind=label_statement)` recording out of
the source-analysis label setup path and into the actual assembly render pass.
This is the correct ownership split:

```text
m68k_analysis_render_lookup_append_labels_for_section()
  -> records label offsets that analysis says are available

m68k_render_ir_preview_emit_prepared()
  -> when it emits "loc_...:" into asm source
  -> appends rendered_symbol_access(label_statement)

m68k_source_quality_analyze_rendered_symbol_accesses()
  -> compares expected accesses with actual rendered accesses
```

The symbolic branch fixture now asserts both the rendered source line and the
matching C source-analysis rendered access for `loc_0_00000004`. That prevents
the previous mistake where a pre-render visibility decision was reported as if
it were actual emitted source.

### Intrinsic Branch Symbol Access Gate

Added the first reason-driven branch target symbol-access producer:

```text
accepted decode candidate
  -> intrinsic branch/call/jump operand
  -> same-section accepted target with a C symbol origin
  -> M68kExpectedSymbolAccessIR(branch_target)
```

The producer deliberately does not use CFG edges as the symbol obligation
source. CFG edges currently do not carry target section identity, and
relocation-backed absolute calls can decode as same-section absolute zero before
the relocation-aware renderer correctly emits a cross-section label. Treating
those CFG rows as symbol obligations was false evidence.

Rendering now records actual emitted operand symbols from the instruction render
path:

```text
rendered instruction text contains operand symbol
  -> M68kRenderedSymbolAccessIR(operand)

rendered instruction text contains operand symbol for a decoded control target
  -> M68kRenderedSymbolAccessIR(branch_target)
```

For decoded targets that do not carry an operand index, the render recorder only
classifies the symbol as a branch target when the candidate has exactly one
decoded control target. That is a metadata-backed association, not a mnemonic
shape shortcut.

The symbolic branch fixture now asserts the full C loop:

```text
expected branch target access
rendered branch target access
rendered target label statement
post-render source-quality gate stays clear
```

Relocation-backed branch/call symbol obligations remain future work. They need a
relocation-aware C producer rather than reusing CFG rows or broad label-created
facts.

### Internal API Compatibility Cleanup

The old `m68k_render_ir_build_source_analysis_from_lookup()` name was removed.
The internal entry point is now:

```text
m68k_analysis_render_lookup_build_source_analysis()
```

No compatibility wrapper was kept. Source-analysis construction is analysis
work, even while some implementation still lives near render helpers during the
remaining migration. This codebase has no external API consumers, so stale
internal names should be deleted when they preserve old ownership boundaries.

The unnamed app-base slot helper was also renamed from fallback terminology to
generated-symbol terminology. `app_XXXX` is not a compatibility fallback; it is
the deterministic generated label for an observed app-base displacement when no
stronger platform/library symbol is proven.

### Orphan-Code Signal Producer Migration

Moved orphan-code signal and orphan absolute-operand observation production out
of `m68k_render_ir.c` and into the analysis lookup producer:

```text
m68k_analysis_render_lookup_append_orphan_code_signals_for_section()
```

The renderer no longer owns these durable facts:

```text
M68kOrphanCodeSignalIR
M68kAddressObservationIR(source = absolute_operand, from orphan island)
```

Those rows are semantic review evidence: they describe code-shaped islands,
nearby structured data, missing inbound evidence, vector/API hints, and memory
observations. Rendering may display them, but it should not decide or append
them. The moved producer still uses the same C lookup evidence and keeps the
rendered source behavior unchanged.

### Source-Analysis Builder Ownership

Moved `m68k_analysis_render_lookup_build_source_analysis()` into
`m68k_analysis_render_lookup.c`. The renderer no longer assembles durable
`M68kSourceAnalysisIR` sections; it receives a completed analysis object and
records only rendered-symbol-access evidence while emitting source text.

```text
m68k_analysis_render_lookup_build_source_analysis()
  -> auto policy
  -> base layout fields
  -> section analysis producers
  -> platform call facts
  -> labels / CFG / orphan-code signals
  -> M68kSourceAnalysisIR

m68k_render_ir_preview_emit_prepared()
  -> consumes M68kSourceAnalysisIR
  -> records rendered symbol accesses
  -> emits text rows
```

This is an internal ownership cleanup, not a compatibility layer. There are no
external consumers that need the old render-owned location.

### Base-Layout Internal API Cleanup

Removed the stale app/RS render names from the shared base-layout collector:

```text
M68kAppRsLayoutSlot      -> M68kBaseLayoutSlot
M68kAppRsLayoutGroup     -> M68kBaseLayoutGroup
app_rs_layout_collect_*  -> base_layout_collect_*
M68K_RENDER_APP_*        -> M68K_APP_*
```

The collector is used by both source-quality fact production and assembly
presentation, so it should not carry renderer ownership in its type names.
Only the final `render_asm_base_layout_rs()` path remains render-specific
because that function emits `RSSET`/`RS.*` source text.

### Source-Blocker Analysis Runs Without Source Export

`facts_v2_collect_profile_internal()` now builds a local `M68kSourceAnalysisIR`
when source blockers are requested, even if the caller is not exporting
assembly source. This makes pre-render source-quality diagnostics visible to
direct/source-blocker profiles instead of only to source-export callers.

The post-render symbol-access comparison is gated to actual assembly-source
rendering:

```text
collect source analysis only
  -> expected_symbol_access rows may exist
  -> no rendered_symbol_access rows are required
  -> no missing-rendered-symbol blocker is emitted

render assembly source
  -> rendered_symbol_access rows are recorded from emitted source
  -> expected vs rendered access gate runs
```

That keeps source-quality checks active for profile/refusal paths without
turning collect-only analysis into a false render failure.

### Removed Unused Label-Creation API

Deleted the production-facing `m68k_fact_ir_create_label()` helper and the
`m68k_fact_ir_has_label()` fact-list scan. Production had already moved label
creation behind the facts-v2 label lookup so duplicate creation is tracked
against the active decode extents. Only tests still called the old create
helper, and the fact-list scan existed only as a null-lookup fallback.

Tests now construct explicit `M68kAnalysisLabelPoint` fixtures when they need
synthetic labels. No compatibility wrapper remains, because this repository has
no external API consumers to preserve.

### Symbol Origins Consume Label Lookup

Source Analysis IR no longer builds symbol origins by scanning
`M68K_FACT_LABEL_CREATED` rows. The facts-v2 label lookup now carries the
confidence for each active label offset, and symbol-origin production walks
that lookup directly:

```text
facts-v2 label lookup
  -> active label offsets + confidence
  -> M68kSymbolOriginIR(origin_kind = analysis_label)
```

The public JSON/source-analysis origin name changed from `label_created` to
`analysis_label`. That deliberately breaks the stale internal vocabulary:
source-quality consumers should see an analysis label origin, not a legacy fact
implementation detail.

### Label Created Fact Deletion

`M68K_FACT_LABEL_CREATED` has been removed from `M68kFactIR`. It was not an
independent fact; it duplicated the active label lookup and forced render lookup
construction to scan append-only facts for label materialization.

The replacement model is direct:

```text
facts-v2 label lookup
  -> M68kAnalysisLabelPoint(section, offset, confidence)
  -> render lookup label materialization
  -> source-analysis symbol origins
```

`LABEL_REQUIRED` remains for now because it still represents an unsatisfied
symbol obligation before analysis proves that the requested label can be
materialized. That is a narrower remaining debt item than the old
created-label fact.
