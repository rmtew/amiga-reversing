# Proposal 033: Source Quality Semantic Closure

Status: proposed.

Proposal 032 moved source-quality analysis in the correct direction: C now owns
more of the address, range, platform-use, label, and source-quality fact model.
It did not finish the visible source-quality outcome. Damocles Tetragon payload
2 still shows the important gap:

```asm
runtime_address_00042C00 EQU $42C00

abs_0_00042C00:
    ori.b #$8000,d6
abs_0_00042C04:
    ori.b #0,d0

    move.w $00042C6C.l,d0
```

That output can round-trip exactly and still be poor restored source. The next
step is to close the semantic loop:

```text
C analysis proves meaning
  -> render consumes only proven meaning
  -> post-render C checks compare intended symbols with emitted symbols
  -> Python/web/report display facts, not infer them
```

There are no external API consumers for this codebase. Old internal call shapes,
compatibility wrappers, pseudo-facts, and renderer-owned semantic shortcuts
should be deleted when they preserve the wrong ownership boundary.

## Tutorial: The Remaining Failure

The Damocles notes in `TODO.md` are the representative fixture. They are not a
request for Damocles-specific logic. They expose general source-quality bugs.

### False Accepted Code

Legal M68K bytes are not proof of code:

```asm
abs_0_00042C00:
    ori.b #$8000,d6
abs_0_00042C04:
    ori.b #0,d0
abs_0_00042C08:
    ori.b #0,d0
```

The fix is not an `ori` blacklist. Real programs use `ori`. The fix is accepted
run proof:

```text
candidate decodes
  -> code-shaped observation
  -> optional orphan-code review signal
  -> not accepted code

candidate has entry/control/relocation/table/runtime/manual proof
  -> accepted code origin
  -> accepted code run
  -> terminal/proven-transfer/explicit-boundary audit
```

An accepted run that falls through weakly into data is a diagnostic or a
demotion. It is not silently rendered as restored source.

Partial block decode is a separate explicit failure when the framework has
accepted a block as code but cannot decode/prove the whole executable span:

```text
accepted code block/run
  -> CPU decode stops before a terminal or proven boundary
  -> no platform semantic instruction covers the stop
  -> no accepted non-code ownership explains a deliberate boundary
  -> partial_code_block_decode blocker
```

`partial_code_block_decode` must be distinct from
`unterminated_or_invalid_code_range`. The first means analysis claimed a code
span that CPU/platform decode cannot cover. The second means the run decodes
but has no credible ending or falls through into invalid ownership.

This check must run as early as the state is knowable. A locally bad candidate
is rejected during acceptance. A run-level partial decode is validated after
accepted bytes/runs are rebuilt and before render. Renderer discovery is only a
final invariant check, not the primary mechanism.

Platform semantics are part of the decode proof. Classic Mac OS object and
CODE-resource sources can contain A-line/F-line opwords that generic M68K
decode would otherwise treat as illegal or data:

```asm
    move.l  a0,-(sp)
    dc.w    $A9F0        ; Classic Mac OS trap/opword call
    addq.l  #4,sp
```

For a Mac OS backend this can be valid executable flow when the platform hook
identifies the opword and its flow behavior. For Amiga/Atari/raw targets, the
same word has no such meaning unless that platform proves one. The validation
question is therefore:

```text
CPU or platform semantic decode proves executable flow?
  yes -> accepted code may continue with platform evidence
  no  -> partial code-block diagnostic/refusal
```

The platform hook must return enough structure for accepted-run validation to
continue safely:

```text
offset
byte_length
flow_kind = fallthrough | call_like_fallthrough | terminal | unsupported
semantic_kind = macos_trap | macos_package_call | platform_private_opword | ...
symbol/display name if known
confidence/proof source
```

Knowing only that an opword is "known" is insufficient. Without `byte_length`,
analysis cannot know where executable flow resumes. Without `flow_kind`, it
cannot know whether fallthrough is valid.

### In-Image Address Identity

Damocles currently has labels and numeric accesses that disagree:

```asm
abs_0_00042C6C:
    ...

    move.w $00042C6C.l,d0
```

The address `$42C6C` is inside the materialized image. If C analysis knows that
storage address and accepts a label for it, the rendered operand should use the
approved symbol or the source-quality gate should explain why it cannot.

The model is:

```text
operand observes $00042C6C
  -> address_observation
  -> address_identity(target_section=0, target_offset=$42C6C)
  -> symbol obligation: storage operand should render abs_0_00042C6C
  -> post-render check: did the operand use that symbol?
```

This applies to absolute long, absolute word, immediate address, PC-relative,
relocated, indexed, and runtime-mapped observations where the instruction form
and platform context make the address meaning provable.

### Range Ownership

Individual absolute refs are low-signal:

```text
absolute[$00079910] refs=1 access=a
absolute[$00079938] refs=1 access=a
absolute[$00079AE4] refs=2 access=a
```

The useful fact is ownership and shape:

```text
$00079910..$0007FD00
  owner = display_buffer
  role = bitmap_plane_or_runtime_buffer
  evidence = pointer setup + copy loop + hardware sink
```

Render should not rediscover this. C source-quality analysis should group the
observations and publish the range. Render can then choose concise source text
or a header summary from that range fact.

### Platform Semantics

Low memory is not automatically a CPU vector:

```asm
lea.l $0074.w,a2
move.l abs_0_00007AB2.w,$63A8(a2)
```

`$74` can be used as a base value. It is only a vector semantic when the local
instruction shape proves vector installation, vector fill, or vector access.

```text
write.l #handler,$70
  -> platform_address_use(true_vector_install)
  -> render m68k_vector_level_4_interrupt_autovector

lea.l $74,a2
move.l value,$63A8(a2)
  -> low_memory_base/storage observation
  -> no vector symbol
```

Hardware names follow the same rule. `_custom+intena` is a platform-use fact,
not a renderer-side numeric lookup.

## Tutorial: The Correct Pipeline

The final ownership boundary is:

```text
decode/facts v2
  -> accepted bytes, CFG, relocations, raw observations

source-quality analysis
  -> code origins
  -> accepted runs
  -> address observations
  -> identities and ranges
  -> table/data-reference ownership
  -> platform address/semantic uses
  -> expected symbol accesses
  -> source-quality diagnostics

render preview
  -> consumes Source Analysis IR
  -> emits text
  -> records actual rendered symbol accesses
  -> reports true render/export failures

post-render source-quality gate
  -> expected accesses - actual accesses
  -> diagnostics/refusal

Python/web/report
  -> display exported C facts
```

`m68k_render_ir_preview_build()` should not create durable semantic facts. It
should receive `const M68kSourceAnalysisIR *` and record only output evidence:

```c
typedef struct M68kRenderedSymbolAccessIR {
  uint16_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  uint8_t access_kind;
  const char *symbol_name;
} M68kRenderedSymbolAccessIR;
```

If a renderer helper still classifies tables, labels, platform names, or memory
ranges, that helper is analysis code in the wrong place.

## Tutorial: Current-State Audit

The current tree has already moved some work into the right layer. In
`m68k_analysis_facts_v2.c`, source-quality analysis is run before source render:

```text
build source analysis
  -> append address observations / platform media transfers
  -> m68k_source_quality_analyze(...)
  -> refuse pre-render source on source-quality blockers
  -> render preview
  -> m68k_source_quality_analyze_rendered_symbol_accesses(...)
```

`m68k_source_quality.c` now creates several C-owned facts:

- code origins from `code_start_refs`
- accepted code runs and range ownerships
- address observations from runtime address refs
- platform address uses for low-memory, CPU-vector, hardware-register, and
  ExecBase shapes
- address identities and absolute address ranges
- structured data table descriptors and entries
- post-render missing-symbol diagnostics

That is the correct direction, but it is not yet the clean final shape.

The important caveat is ordering. Current `m68k_analysis_facts_v2.c` still
does this:

```text
m68k_render_lookup_build(...)
  -> m68k_analysis_render_lookup_run_platform_passes(...)
  -> m68k_render_lookup_materialize_*_labels(...)
  -> m68k_analysis_render_lookup_build_source_analysis(...)
  -> append_symbol_facts_from_label_lookup(...)
  -> append_address_observations_for_accepted(...)
  -> m68k_source_quality_analyze(...)
  -> render preview records M68kRenderEvidenceIR
  -> compatibility mirror keeps rendered_symbol_accesses in source_analysis
  -> m68k_source_quality_analyze_rendered_symbol_accesses(source_analysis,
                                                         render_evidence)
```

So source-quality analysis is present, but it is not yet the owner of the
semantic pipeline. It validates and enriches facts that are still largely
assembled by render lookup. The migration must invert that dependency.

The final order should be:

```text
decode/facts/accepted bytes
  -> source-analysis builder
  -> generic data/range/table analysis
  -> platform extension analysis
  -> source-quality closure
  -> render lookup/view cache from immutable source analysis
  -> render evidence
  -> post-render source-quality closure
```

`M68kRenderLookup` can still exist, but only as a cache for questions the
renderer needs to answer quickly while formatting already-proven facts.

### Remaining Wrong Boundary: Render Lookup As Analyzer

`m68k_analysis_render_lookup.c` still runs major analysis passes whose names and
outputs are semantic, not presentational:

```text
render_lookup_infer_platform_runtime_structured_data()
render_lookup_infer_amiga_palette_uploads()
render_lookup_infer_amiga_bitmap_memory_uses()
render_lookup_infer_relocation_pointer_tables()
render_lookup_infer_indexed_word_dispatch_tables()
render_lookup_infer_pc_relative_lookup_scalars()
render_lookup_add_auto_structured_data_item()
source_analysis_append_auto_structured_data_policy()
```

Those passes build `M68kAnalysisStructuredDataItem` records, range ownership
views, table metadata, consumer registers, index domains, and source patterns.
They then append those analysis facts to `M68kSourceAnalysisIR`.

The clean path is not to keep this under a "render lookup" name. Split it:

```text
m68k_analysis_render_lookup.c
  -> label visibility and render-time lookup cache only

m68k_analysis_data.c
  -> generic table/string/data-range inference

m68k_analysis_platform_amiga.c
  -> Amiga hardware/runtime/display/audio/disk semantic inference

m68k_source_quality.c
  -> validation, closure, diagnostics, and source-export gating
```

The code can move in slices, but the end state should delete the render-owned
semantic storage once the analysis modules produce the same C facts directly.

The existing C tests already show the migration boundary:

```text
source_quality_analyze_exports_code_origins_and_runs
source_quality_analyze_exports_platform_address_uses
source_quality_analyze_exports_structured_data_range_ownership
source_quality_analyze_exports_structured_data_table_descriptor
source_quality_analyze_exports_table_entries_and_data_references
source_quality_analyze_blocks_code_without_executable_origin
source_quality_analyze_uses_cfg_terminal_run_end
source_quality_analyze_exports_orphan_conflict_ranges

render_lookup_range_ownership_uses_stable_auto_indices
```

The first group should stay and grow in source-quality/data/platform modules.
The last test is a marker for logic that must move out of render lookup. It can
be replaced by source-analysis range ownership tests once the lookup no longer
owns structured range state.

### Remaining Wrong Boundary: Generic Core Includes Amiga Semantics

`m68k_source_quality.c` currently includes generated Amiga and CPU runtime
knowledge directly:

```c
#include "generated/amiga_os_runtime.h"
#include "generated/m68k_cpu_runtime.h"
```

CPU exception vectors are generic enough for the M68K core. Amiga hardware
registers, `_custom`, ExecBase, and library/device semantics are platform
extension facts. The reliable shape is:

```c
typedef struct M68kPlatformSourceQualityHooks {
  uint8_t (*classify_address_use)(const M68kAddressObservationIR *observation);
  const char *(*symbol_for_address_use)(const M68kAddressObservationIR *observation,
                                        uint8_t use_shape,
                                        char *buffer,
                                        size_t buffer_size);
  int (*classify_semantic_opword)(const M68kDecodeSectionIR *section,
                                  uint32_t offset,
                                  M68kPlatformSemanticUseIR *out_use);
  int (*append_platform_ranges)(M68kSourceAnalysisIR *source_analysis);
} M68kPlatformSourceQualityHooks;
```

The core owns fact schemas, validation, address identity, range coalescing, and
diagnostics. The platform backend owns the semantic lookup that says "`$DFF09A`
is `_custom+intena`" or "`$74` is only a low-memory base in this instruction
shape." It also owns platform executable opword classification, such as Classic
Mac OS A-line/F-line traps and package calls, including whether the opword is a
call-like fallthrough, terminal transfer, or unsupported platform instruction.

This should fit the existing backend model. The code already carries
`M68kPlatformBackendKind` through objects, assembler policy, render preview, and
`platform_facts_v2_*` helpers. Source-quality platform hooks should be an
extension of that C backend/facts seam, not a new Python or renderer-side
registry:

```text
M68kPlatformBackendKind
  -> platform_facts_v2 generic dispatch
  -> platform_amiga source-quality hooks
  -> platform_atari/macos hooks as needed
  -> generic m68k_source_quality.c receives only hook results
```

`m68k_render_ir.c` also includes Amiga generated runtime metadata today. Some
of that is legitimate formatting of platform symbols, but any lookup that
decides whether an address is hardware, vector, ExecBase, bitmap, copper, audio,
disk, OS-call, or trap meaning must move to C analysis/platform facts first.
After the migration, render may ask "what string do I print for this proven
platform fact?", not "does this number have platform meaning?"

### Remaining Gap: Address Identity Is C-Owned But Not Closed

`m68k_source_quality.c` already builds `M68kAddressIdentityIR` and
`M68kAbsoluteAddressRangeIR` from `M68kAddressObservationIR`:

```text
address_observations
  -> append_address_identities_and_ranges
  -> address_identities
  -> absolute_address_ranges
  -> source_analysis_assign_absolute_memory_symbols
```

Those facts are exported to JSON and indexed by the corpus manifest as
`analysis:address_identity:*` and `analysis:absolute_address_range:*`. That is
the correct ownership. The gap is that an identity is not yet a render
obligation.

Today render still has address-symbol attachment paths that decide whether a
numeric operand becomes a symbol:

```c
attach_existing_materialized_runtime_immediate_symbols(...)
attach_unmapped_absolute_runtime_address_symbols(...)
attach_materialized_runtime_absolute_storage_symbols(...)
attach_absolute_memory_slot_symbols(...)
attach_absolute_memory_address_use_symbols(...)
```

Some of these consult C source-analysis observations, but the final choice is
still made while rendering. Others use render lookup, runtime-address mapping,
hardware lookups, or materialized-label checks directly. This is why Damocles
can still render a numeric `$00042C6C.l` even when the surrounding image has a
materialized storage label. C has partial identity facts, but it does not yet
say "this operand must render this symbol" and then verify that render did so.

The closure should be:

```text
instruction operand observes in-image address
  -> address_identity resolves section/offset/owner
  -> expected_symbol_access emitted with a precise address-observation producer
  -> render consumes that expected symbol
  -> rendered_symbol_access records actual output
  -> post-render gate blocks missing/wrong symbol
```

An address identity can also deliberately decline a symbol, but that decision
must be explicit:

```text
operand observes $00042C6C
  -> identity owner=in_image_storage
  -> no symbol because target range is hidden/overlaid/conflicted
  -> source-quality diagnostic explains why source kept a number
```

The important rule is that "in image and labelable" must not silently render as
a raw number. Either the operand is symbolized through the C-owned identity, or
the source-quality report contains the reason it is not.

Current implementation progress:

```text
SECTION_STORAGE address observation + accepted instruction + target symbol
  -> expected_symbol_access(access_kind=operand)
  -> producer=section_storage_address_observation
  -> post-render gate can refuse a raw numeric operand

ABSOLUTE address observation + accepted instruction + target symbol
  -> expected_symbol_access(access_kind=operand)
  -> producer=absolute_address_observation
  -> post-render gate can refuse a raw numeric operand
```

The producer is deliberately limited to ordinary memory read/write and
compute-address operands:

```text
move.w  abs_0_00042C6C.l,d0
lea     abs_0_00042C70.l,a0
  -> operand symbol obligation

jsr     loc_1_00000004.l
jmp     loc_1_00000004.l
  -> branch-target symbol obligation
```

This keeps address identity from swallowing control-flow semantics. Relocated
or intrinsic branch/call/jump targets are still owned by branch-target expected
access producers; storage observations only close the data/address operand
case.

For storage operands, the actual operand address remains the primary fact. A
relocation/addend target can be valid restored-source evidence for one operand
while being wrong for another operand in the same instruction:

```asm
    cmpi.l #loc_1_0000DE66,loc_1_0000DCCE.l
```

Here `loc_1_0000DE66` is the immediate value, while the memory-read operand is
`loc_1_0000DCCE.l`. If an address observation says the memory operand's raw
address is `$DCCE` but its addend-adjusted target is `$DE66`, the expected
operand symbol must use the raw storage symbol when one exists. The addend
target is not a safe substitute for the operand actually being read or written.

### Remaining Wrong Boundary: Render Evidence Mutates Source Analysis

`m68k_render_ir.c` records actual rendered symbol accesses during assembly
source emission. That is the right moment to observe what render emitted. The
post-render gate now has a first-class evidence object:

```c
typedef struct M68kRenderEvidenceSectionIR {
  uint32_t section_index;
  M68kRenderedSymbolAccessIR *rendered_symbol_accesses;
  size_t rendered_symbol_access_count;
  size_t rendered_symbol_access_capacity;
} M68kRenderEvidenceSectionIR;

typedef struct M68kRenderEvidenceIR {
  M68kRenderEvidenceSectionIR *sections;
  size_t section_count;
  size_t section_capacity;
  Arena *arena;
} M68kRenderEvidenceIR;
```

The render preview owns this object:

```text
m68k_render_ir_preview_init
  -> m68k_ir_render_evidence_create

record_rendered_*()
  -> m68k_ir_render_evidence_append_rendered_symbol_access

m68k_source_quality_analyze_rendered_symbol_accesses(source_analysis,
                                                     render_evidence)
  -> compares expected analysis obligations with render output evidence
```

The post-render gate is therefore explicit:

```text
source_analysis.expected_symbol_accesses
  minus render_evidence.rendered_symbol_accesses
  -> source_quality_diagnostics
```

This is not the final cleanup. For compatibility with current JSON/reporting,
render still mirrors rendered accesses into `M68kSectionAnalysisIR` while it
also records them in `M68kRenderEvidenceIR`. The important ownership step is
complete: source-quality validation no longer reads the section mirror. The
next cleanup is to give JSON/reporting an explicit render-evidence export path
and delete the section-level rendered-access mirror from source analysis.

### Remaining Wrong Boundary: Renderer-Side Platform Decisions

`M68kPlatformAddressUseIR` exists today, but it is only a narrow address-use
fact:

```text
true_vector_install
low_memory_base
low_memory_storage
hardware_register_access
execbase_literal
hardware_base_address
```

That is useful, but it is not enough to remove platform reasoning from render.
Current `m68k_render_ir.c` still contains platform decisions such as:

```text
render_asm_define_amiga_lvo_symbol_once()
render_asm_define_amiga_hardware_base_once()
render_asm_define_amiga_constant_once()
render_asm_define_m68k_vector_symbol_once()
format_copper_register_symbol()
format_copper_register_value_expr()
copper_runtime_pointer_register()
attach_amiga_hardware_register_symbols()
resolve_amiga_hardware_register_operand()
attach_amiga_next_call_input_immediate_symbol()
attach_amiga_hardware_display_comment_for_render()
attach_amiga_hardware_access_comment_for_render()
attach_amiga_runtime_sink_comment_for_render()
attach_platform_stack_cleanup_comment_for_render()
external_runtime_address_ref_role()
runtime_address_ref_sink_role()
```

Some of those functions are harmless formatting once the fact is already known.
Others decide meaning from an instruction, register state, address, or future
call. Those must move into C analysis/platform facts.

The split should be:

```text
analysis/platform:
  proves hardware register access
  proves copper register/value semantics
  proves runtime sink role
  proves OS call input value-domain symbol
  proves stack cleanup note
  emits semantic fact + expected symbol obligation

render:
  includes needed generated symbol files
  declares equates requested by semantic facts
  formats already-proven symbol/comment text
  records rendered symbol evidence
```

The durable fact family now exists for range-like platform semantic uses:

```c
typedef struct M68kPlatformSemanticUseIR {
  uint32_t offset;
  uint32_t size;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t role_flags;
  uint8_t kind;
  uint8_t source_pattern_id;
  uint8_t confidence;
  uint8_t has_target;
} M68kPlatformSemanticUseIR;
```

It is exported as `platform_semantic_uses` and currently covers semantic
roles derived from structured data and runtime-address references, such as
bitmap, copper, audio, disk, blitter, palette, sprite, and audio-table uses.

That does not finish renderer-side platform closure. Render still performs
some instruction-local semantic decisions for display/audio/disk/blitter/copper
comments, stack-cleanup notes, runtime-address sink role comments, and
next-call input value-domain operands. Those decisions need either:

```text
first-class semantic/use facts
  -> when the source meaning should be queryable after analysis

expected-symbol access producers
  -> when the immediate requirement is to validate a rendered platform symbol
```

The first source-quality slice for this boundary is now implemented:

```text
recovered platform call _LVOAlert
  -> generated metadata proves D7 is an alert-number input
  -> nearby accepted instruction loads an immediate into D7
  -> value domain formats AN_IconLib|AG_OpenLib|AO_DOSLib
  -> expected_symbol_access:platform_call_input_value_domain_operand
```

Render should ultimately consume these C-owned facts instead of rescanning
forward to find the next platform call or reclassifying hardware/register
numbers while formatting.

### Remaining Gap: Expected Symbol Producer Coverage Is Too Narrow

Expected-symbol accesses now carry a producer id. That is important because a
missing rendered symbol is not just "some label did not print"; it is a failed
obligation from a specific analysis rule.

Current implemented producer ids include:

```text
relocated_branch
intrinsic_branch
data_operand
manual_equate
generated absolute-symbol equate operand obligations
label_statement
section_storage_address_observation
absolute_address_observation
table_entry_target
```

The producer field is exported with each expected symbol access. Missing-symbol
diagnostics surface it through producer-qualified evidence source text:

```text
missing_expected_symbol_access
  evidence_source = expected_symbol_access:section_storage_address_observation
```

That gives the worker the rule that created the failed obligation instead of
only the missing symbol name.

Current multi-producer progress:

```text
same source/operand/symbol/kind obligation from producer_one
same source/operand/symbol/kind obligation from producer_two
  -> one expected_symbol_access
  -> producer = producer_one,producer_two
  -> producers = [producer_one, producer_two] in JSON
  -> one missing-symbol diagnostic with both causes visible
```

The gate should not emit duplicate diagnostics for one missing rendered symbol
just because two analysis rules required it. It should also not drop either
rule's evidence.

The remaining gap is no longer a generic lack of producer ids. Several of the
old gap names are now implemented:

```text
relocation-backed branch/call targets
intrinsic branch/call/jump targets
ordinary data operands
manual equates
generated non-manual equates
independent label statements
section-storage address observations
absolute address observations
accepted table-entry targets
rendered storage-label evidence
materialized runtime range-start storage-label obligations
PC-relative data operands crossing materialized runtime ORG boundaries
PC-relative control operands crossing materialized runtime ORG boundaries
platform call input value-domain operands
```

The remaining coverage gap is narrower:

```text
platform semantic comments
hardware/register value-domain operands
runtime-address sink role symbols/comments
stack-cleanup comments
```

Until those producers are complete, the post-render gate can catch the covered
part of the label/source mismatch class and must not pretend the uncovered
classes are validated.

The next coverage should stay as separate functions, not one broad "label
exists" rule:

```text
append_expected_platform_symbol_operand_accesses()
```

Current generated-equate progress:

```text
source-quality analysis sees an absolute address observation that requires a
generated absolute symbol
  -> expected_symbol_access(access_kind=equate,
                            producer=absolute_address_observation)

renderer declares the generated symbol with EQU
  -> declaration metadata marks the symbol as an EQU

renderer emits that symbol in an operand
  -> rendered_symbol_access(access_kind=equate)
  -> post-render gate proves the operand used the emitted EQU
```

This is intentionally not a generic "any symbol-looking value is an address"
rule. Section-storage observations that resolve to real in-image labels remain
`access_kind=operand`; only declarations emitted as `EQU` are recorded as
rendered equate accesses.

Current storage-label progress:

```text
source-quality analysis sees materialized runtime view start
  -> expected_symbol_access(access_kind=storage_label,
                            producer=storage_label_statement)

renderer emits a storage-domain label before switching ORG to runtime domain
  -> rendered_symbol_access(access_kind=storage_label)
  -> post-render gate can match an expected storage-label obligation

source-quality analysis sees a PC-relative data operand cross a materialized
runtime ORG boundary
  -> expected_symbol_access(access_kind=operand,
                            producer=pc_relative_storage_operand)
  -> expected_symbol_access(access_kind=storage_label,
                            producer=pc_relative_storage_label_statement)

If the ordinary data-target producer already created the same operand
obligation, producer evidence is merged; this records both reasons without
duplicating the expected access.

source-quality analysis sees a PC-relative branch/call/jump target cross the
same boundary
  -> expected_symbol_access(access_kind=branch_target,
                            producer=pc_relative_storage_operand)
  -> expected_symbol_access(access_kind=storage_label,
                            producer=pc_relative_storage_label_statement)

If the intrinsic or relocated branch producer already created the branch-target
obligation, producer evidence is merged; the storage-label statement remains a
separate obligation because it proves the storage-domain label was emitted.
```

These producers are C-owned. They do not reuse the renderer-only
`storage_label_target_refs` side effect; source analysis owns the
operand/cross-ORG condition, and render only formats and records the label.

Each new producer must set a precise producer id/string in
`M68kExpectedSymbolAccessIR`. A missing or empty producer should be treated as a
test failure for new source-quality code, with the existing `"unknown"` fallback
reserved for old/manual fixture construction and defensive JSON export.

Current table-entry progress:

```text
accepted table entry has a target symbol origin
  -> expected symbol access emitted at the table entry offset
  -> producer = table_entry_target
  -> rendered table entry must record matching operand evidence
  -> missing evidence is a render/analysis closure bug, not user review work

relocation-backed pointer-table entry
  -> entry target comes from the relocation fact for that entry
  -> not from a table-wide target section

relocation target lies inside the relocation/table payload itself
  -> keep numeric
  -> do not create a target-label obligation
```

The table-entry rule is intentionally narrow. It does not promote every
numeric table-looking value into a symbol. It only closes the loop after earlier
analysis has accepted the entry target and there is a C-owned symbol origin at
that target. Midwinter II exposed why this matters: a relocation pointer table
can contain entries whose relocation targets live in a different section from
the table. The entry fact must therefore use the relocation at the entry offset,
not the structured item's default target section. The existing hunk safety rule
also remains required: a relocation that points back into the relocation payload
is preservation metadata, not proof that the payload should be symbolized.

## Tutorial: Symbol Obligations

Rendered labels are useful only when justified and visible. Source-quality
analysis should produce explicit obligations:

```c
typedef enum M68kExpectedSymbolAccessKind {
  M68K_EXPECTED_SYMBOL_ACCESS_OPERAND,
  M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET,
  M68K_EXPECTED_SYMBOL_ACCESS_LABEL_STATEMENT,
  M68K_EXPECTED_SYMBOL_ACCESS_EQUATE,
  M68K_EXPECTED_SYMBOL_ACCESS_STORAGE_LABEL
} M68kExpectedSymbolAccessKind;

typedef struct M68kExpectedSymbolAccessIR {
  uint16_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  M68kExpectedSymbolAccessKind kind;
  const char *symbol_name;
  const char *producer;
} M68kExpectedSymbolAccessIR;
```

The producer must be precise:

```text
relocation-backed jsr operand
  -> expected branch/call target symbol

absolute operand targets accepted in-image storage
  -> expected operand symbol

accepted data boundary label
  -> expected label statement

generated absolute storage slot
  -> expected equate-backed operand use
```

Broad facts such as "a label exists here" are not enough. The obligation must
say why this rendered text should exist.

## Tutorial: Tables And Data References

Damocles exposes a relative lookup table:

```asm
andi.w #1023,d5
add.w d5,d5
lea.l abs_0_0005D8C0.l,a1
adda.w $0(a1,d5.w),a1

abs_0_0005D8C0:
    dc.w $0800
    dc.w $0804
    dc.w $0808
```

The general C analysis should recover:

```text
index mask 1023
  -> index domain 0..1023
add.w index,index
  -> word table stride
lea table_base,a1
adda.w (a1,index.w),a1
  -> relative word offset table
  -> table entries target table_base + signed_word(entry)
```

There must be no fixed local cap that silently turns the tail into raw bytes.
If the analysis cannot prove the full bounds, it emits a structured incomplete
analysis fact:

```text
table_candidate
  status = incomplete
  reason = unresolved_bound | conflicting_target | capacity_limit
  visible source = conservative data plus diagnostic
```

A capacity limit is an analysis failure to fix, not a fallback behavior to hide.

## Tutorial: Manual And Editor Input

Manual input is evidence, not a bypass:

```text
manual code seed
  -> code origin(manual_seed)
  -> still must decode
  -> still must pass overlap, range, and accepted-run audits

manual label
  -> symbol evidence
  -> not code evidence

manual runtime ref
  -> address evidence
  -> not code proof
```

If a user forces bad code, C analysis should report the same diagnostics that
auto-analysis would report for bad code. The editor should not be able to make
the source appear clean by skipping source-quality gates.

Current-state gap:

```text
manual_action_log
  -> Python projection
  -> TargetMetadata.seeded_code_entrypoints
  -> target metadata JSON
  -> M68kAnalysisPolicy.entry_points
  -> M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT
  -> M68kCodeOriginIR(origin_class=strong_entry)
```

That path does reach C source-quality analysis, so manual code seeds are not
completely outside the gate. However, the evidence type is flattened. By the
time source-quality sees the run, a manual seed looks like any other policy
entry point. `M68kAnalysisEntryPoint` carries only section and offset, so C
source-quality cannot say whether the origin was automatic policy, target
metadata, manual review, or another projection.

That matters because current accepted-run handling treats an executable origin
as enough to avoid the hard blocker:

```text
accepted code without executable origin
  -> error, blocker

accepted code with policy/manual origin but accepted-gap ending
  -> warning, non-blocker
```

For the desired behavior, manual provenance must survive into C:

```c
typedef enum M68kAnalysisEntryPointProvenance {
  M68K_ANALYSIS_ENTRY_POINT_SOURCE_DEFAULT,
  M68K_ANALYSIS_ENTRY_POINT_TARGET_METADATA,
  M68K_ANALYSIS_ENTRY_POINT_MANUAL_ACTION_LOG,
  M68K_ANALYSIS_ENTRY_POINT_DECISION_JOURNAL
} M68kAnalysisEntryPointProvenance;
```

Then source-quality can emit `MANUAL_EVIDENCE_CONFLICT` when a manual code seed
decodes poorly, overlaps structured data, lands inside an instruction, or
creates an unterminated/invalid accepted run. Manual evidence should strengthen
where analysis is consistent, not downgrade failures.

## Implementation Slices

Each slice must fix the obvious cause of any validation failure it exposes.
Adding a validator and then stopping because a tracked target now fails is not
completion; it is the start of the repair.

This is an acceptance rule, not a preference. A slice that discovers a
framework-owned source-quality failure is not complete until the cause is fixed,
the failure is reduced to an isolated test, and the affected target
renders/round-trips again. "Cause" means the wrong producer, missing producer,
bad classifier, missing conflict rule, bad accepted-run proof, or wrong
render-evidence path that actually made the framework emit bad source. The only
acceptable deferral is a failure whose cause is outside the slice and whose
diagnostic chain is explicit enough to reproduce without another investigation
pass.

This applies to all proposal work, not only dedicated validation slices. If an
implementation step changes analysis, rendering, address identity, platform
semantics, table detection, fixture import, or test coverage and that work
surfaces a framework-owned failure, the same work item owns the cause analysis
and the obvious fix.

```text
proposal work touches source-quality behavior
  -> validation/test/target exposes a failure
  -> classify the failure as framework-owned or genuinely outside scope
  -> if framework-owned and causally visible, fix the cause now
  -> add or tighten the isolated fixture that proves the repaired behavior
  -> only defer with a precise diagnostic chain when the fix is outside scope
```

The proposal must not normalize this pattern:

```text
validator added
  -> target fails
  -> failure is listed as a blocker
  -> implementation moves on without fixing the bad producer
```

That is not a successful validation outcome. It is an incomplete slice.

The slice workflow is:

```text
new validation exposes failure
  -> treat the failure as a reproduction
  -> reduce it to a focused fixture
  -> identify the bad producer, missing platform semantic, or missing conflict
     classifier
  -> fix that cause in the same slice when it is within scope
  -> rerender affected targets
  -> update fixture/invariant inventory
```

Do not complete a slice by only surfacing a validation error when the fix is
obvious from the same evidence. Leaving work behind is acceptable only when the
failure is genuinely outside the proposal slice and the remaining work is
documented with target, section/offset, diagnostic, fact chain, and proposed
next fix.

In concrete terms, these are different outcomes:

```text
validation exposes false code acceptance
  -> find the analysis rule that promoted weak bytes to accepted code
  -> fix that rule or add the missing conflict classifier
  -> keep an isolated false-code fixture
  -> rerender the target that originally exposed it

validation exposes missing rendered symbol access
  -> find the missing or wrong expected-symbol producer
  -> fix address identity / platform semantic / render evidence at cause
  -> keep an isolated symbol-obligation fixture
  -> rerender the target that originally exposed it
```

These are not valid completions:

```text
validation exposes false code acceptance
  -> record "bad code blocker"
  -> leave the weak code producer unchanged

validation exposes missing symbol access
  -> record "render blocker"
  -> leave analysis without the missing symbol obligation
```

The documentation for any deferred failure must be concrete enough that another
worker can reproduce it without re-discovering the problem:

```text
target/project
source section and offset
diagnostic kind/error code
expected source-quality fact
actual bad producer or missing producer
why the fix is outside this slice
next implementation step
```

The intended outcome is:

```text
added validation
  -> target exposed framework bug
  -> producer/conflict/platform semantic fixed
  -> target renders correctly or refuses with a precise remaining diagnostic
```

The rejected outcome is:

```text
added validation
  -> target now fails
  -> called it a blocker
  -> left the producer unchanged
```

Implementation must treat this as a repair loop, not a stopping condition:

```text
new validation detects bad source
  -> preserve the failing fixture
  -> identify the producer that created the bad fact
  -> add or tighten the isolated source-quality test
  -> fix the producer/classifier/render-evidence path at cause
  -> rerender and round-trip the affected targets
```

A blocker diagnostic is a product-facing refusal to emit misleading restored
source. It is not an engineering excuse to stop the proposal work. If the
failure comes from an obvious cause in the slice being implemented, the slice is
not complete until that cause is fixed. If the failure exposes a genuinely
separate subsystem, keep the diagnostic, document the separate owner/slice, and
do not claim the current slice as complete unless the emitted source is no
longer wrong for the covered case.

### Slice 1: Render Preview Read-Only Source Analysis

Change render preview to consume source analysis:

```text
before:
  render preview creates/appends M68kSourceAnalysisIR facts

after:
  m68k_source_quality_analyze(...) -> M68kSourceAnalysisIR
  render preview consumes const M68kSourceAnalysisIR *
  render preview records M68kRenderedSymbolAccessIR only
```

Delete compatibility wrappers and old parameter shapes during the migration.

### Slice 2: Expected Symbol Access Producers

Keep the completed precise C producers:

```text
relocated_branch
intrinsic_branch
data_operand
manual_equate
label_statement
section_storage_address_observation
absolute_address_observation
table_entry_target
merged producer evidence for duplicate obligations
rendered storage-label evidence
storage_label_statement for materialized runtime range starts
pc_relative_storage_operand for cross-ORG PC-relative data operands
pc_relative_storage_operand for cross-ORG PC-relative control operands
pc_relative_storage_label_statement for those operand-required storage labels
```

The PC-relative storage producers are deliberately narrow. Crossing a
materialized runtime range is not enough by itself. The target offset must map
to a distinct runtime address; otherwise an ordinary `loc_*` operand and label
after an `ORG` is already valid source:

```text
lea.l loc_2_0000014C(pc),a0
...
section_2[$6A-$14C) -> runtime[$100-$1E2)

target $14C is outside the copied runtime range
  -> no storage-label obligation
  -> ordinary label access is valid

target inside copied runtime range and runtime != storage
  -> operand may need storage-space spelling
  -> expected pc_relative_storage_operand
  -> expected pc_relative_storage_label_statement
```

Add the remaining precise C producers:

- platform semantic operands and comments

Do not reuse generic label-created or label-required facts. Those pseudo-facts
were deleted because they hid why a symbol was needed.

### Slice 3: Post-Render Symbol Gate

Run a post-render C check:

```text
for expected in expected_symbol_accesses:
  if no matching rendered_symbol_access:
    diagnostic missing_expected_symbol_access
```

The gate should distinguish:

- renderer chose numeric where C required a symbol
- renderer emitted a label that no operand uses
- branch/call target symbol was omitted
- equate exists but operand did not use it
- storage label exists but no label statement was emitted

### Slice 4: Accepted-Run Demotion

Upgrade accepted-run auditing from reporting to action:

```text
weak shape-only run
  -> never promote in the final model
  -> demote during migration only to repair old bad facts

accepted/proven code later fails validation
  -> source-quality blocker

manual seeded invalid run
  -> diagnostic/refusal, not silent acceptance
```

Weak code evidence is a review indicator, not a reason to convert bytes into
code:

```text
weak decode island
address-shaped value
nearby label
plausible instruction sequence
orphan terminal-looking block
  -> orphan_code_signal / possible_code_candidate / address_observation
  -> no accepted_code
  -> no code label
  -> no source code rendering
  -> no fallthrough propagation
```

Damocles `$42C00`, Starglider false `ori` blocks, and Pandora false-code blocks
must go through the same generic path.

Current implementation detail:

```text
accepted_run_has_executable_origin == false
  -> accepted_code_without_executable_origin
  -> severity=error blocker=true

run.end_kind == accepted_gap + accepted non-code range starts at run end +
hard fallthrough proof reaches the run
  -> unterminated_or_invalid_code_range
  -> severity=error blocker=true
```

The remaining gap is earlier promotion. A run that falls into data should
either never be promoted in the first place or become a source-quality blocker
when a required/proven origin made it accepted:

```text
accepted_gap + nearby_data/string/table/absolute-storage evidence
  -> severity=error blocker=true

weak accepted_gap + no hard origin
  -> not accepted code; review/candidate fact only

manual origin + accepted_gap
  -> manual_evidence_conflict blocker unless explicit boundary proof exists
```

The implementation should avoid opcode-specific checks. The inputs are origin
class, CFG end kind, CPU/platform decode coverage, nearby range ownership,
orphan-code signals, structured data overlap, and address/table/string evidence.

Credible code boundaries are explicit:

```text
terminal CPU instruction
  -> rts, rte, bra, jmp, trap/no-return call when proven

platform semantic terminal/fallthrough
  -> MacOS A-line/F-line trap with byte length and flow kind

proven control split
  -> branch/jump/call target starts or exits a block

section/resource boundary
  -> executable section/resource ends exactly here

explicit owned non-code boundary
  -> following bytes are proven data/table/string
  -> current code has a credible transfer/boundary before them
```

Non-boundaries:

```text
decode stopped on invalid next word
next bytes look awkward
one-off address value points here
run simply reaches data with no terminal/transfer
```

Implementation order:

```text
1. Add entry-point provenance/source fields to M68kAnalysisEntryPoint.
2. Preserve manual_action_log and decision_journal provenance through metadata
   parsing into M68K_FACT_CODE_START_REF.
3. Export provenance in M68kCodeOriginIR.
4. Add source-quality tests for manual seed at valid code, data overlap,
   mid-instruction, and unterminated accepted-gap runs.
5. Add partial-code-block fixtures:
   generic accepted run whose decode stops before a credible terminal;
   same byte shape under Mac OS where an A-line/F-line platform opword proves
   executable flow; same opword under Amiga/raw where no platform proof exists
   and source export is refused.
6. Change accepted-gap severity to blocker when negative evidence is present.
7. Stop promoting weak shape-only runs; keep them as review/candidate facts.
   During migration, demote any existing shape-only accepted runs before render.
```

Current implementation progress:

```text
partial_code_block_decode diagnostic kind
  -> added to C source-quality diagnostics
  -> emitted as severity=error/blocker when accepted code bytes are not fully
     covered by decoded instruction candidates
  -> covered by isolated C fixture:
     source_quality_analyze_blocks_partial_code_block_decode
  -> positive terminal decode path asserts no partial-code diagnostic:
     source_quality_analyze_uses_decode_terminal_run_end
```

This is only the first validation slice. It deliberately does not solve weak
shape-only promotion or platform semantic opword coverage. Those remain in this
slice because partial decode validation is useful only when the producer fixes
follow:

```text
accepted bytes without decode coverage
  -> fail now

weak decode island promoted without hard evidence
  -> next: stop promoting or demote before render

platform opword accepted as executable code
  -> next: require platform hook byte length and flow kind
```

When this validation fires on a real target during the proposal work, the slice
is not complete until the cause is fixed. The expected path is:

```text
validation failure found
  -> preserve the smallest fixture that reproduces it
  -> identify the producer/classifier/render-evidence path that created it
  -> repair that path
  -> rerender affected targets
  -> keep the fixture as regression coverage
```

Treating the diagnostic itself as the deliverable would only make the framework
better at reporting broken source. The proposal outcome is corrected source.

### Slice 5: Address Identity And Range Closure

Close the existing C-owned identity/range model instead of adding more
renderer-side special cases. First make identities produce symbol obligations:

```text
M68kAddressObservationIR
  -> M68kAddressIdentityIR
  -> M68kExpectedSymbolAccessIR(producer=section_storage_address_observation
                                or absolute_address_observation)
  -> M68kRenderedSymbolAccessIR
  -> missing/wrong symbol diagnostic
```

Then extend the identity/range model to cover:

- in-image storage
- runtime copied images
- bitmap/display/audio/disk buffers
- loader output
- dense low-memory app storage
- sparse unowned absolute refs

The C facts should carry enough information for concise rendered summaries:

```c
typedef struct M68kAbsoluteAddressRangeIR {
  uint32_t start;
  uint32_t size;
  uint8_t owner_kind;
  uint8_t role_kind;
  uint8_t status;
  uint32_t observation_count;
  const char *symbol_name;
} M68kAbsoluteAddressRangeIR;
```

Renderer headers should format these records, not rediscover them. The current
renderer helpers that attach materialized runtime, absolute storage, absolute
slot, absolute address-use, and unmapped runtime symbols should be reduced to
formatting C-owned `symbol_name` and obligation facts. If a helper still needs
to ask whether a number is a runtime image, hardware address, low-memory slot,
or materialized source address, that analysis belongs before render.

### Slice 6: Platform Semantic Use Closure

Move remaining platform semantic decisions into C facts:

- CPU vector install/fill/access
- low-memory base/storage
- Amiga hardware register access
- copper/display/bitmap/audio/disk/blitter semantic uses
- OS call and trap semantic uses
- OS call input value-domain symbols
- stack-cleanup notes
- runtime-address sink roles

Renderer-side numeric lookup is allowed only for formatting a C-owned
`symbol_name`.

Implementation order:

```text
1. M68kPlatformSemanticUseIR and JSON export exist.
2. Add/verify corpus/xref lanes for analysis:platform_semantic_use:*.
3. Move hardware/display/access comments from render to semantic-use producers.
4. Move next-call input immediate symbol rendering to consume source-quality/platform facts.
5. Move runtime-address sink role naming to semantic-use/address-range facts.
6. Delete the renderer scans once equivalent C facts drive the same source.
```

Keep `M68kPlatformAddressUseIR` for address-shape facts. Use
`M68kPlatformSemanticUseIR` for higher-level meanings and comments.

### Slice 7: Table And Data Reference Closure

Generalize C table descriptors:

- indexed word/long/pointer tables
- relative offset tables
- dispatch tables
- string pointer tables
- data target tables
- mixed table/data/code conflict cases

Each table has consumer evidence, bounds evidence, entry shape, and either
accepted entries or a structured non-classification reason.

### Slice 8: Python/Web/Report Cleanup

Python should index and display C facts:

```text
source_analysis_json
  -> diagnostics
  -> code origins/runs
  -> address identities/ranges
  -> platform uses
  -> table descriptors
  -> expected/rendered symbol accesses
```

Remove Python compatibility lanes for nonexistent or obsolete C facts. Do not
recreate source-quality decisions in JSON export or web report code.

Current wrapper audit:

```text
amiga_reversing/disasm/corpus_usage.py
  -> presentation labels for already-exported features

amiga_reversing/web/app.js
  -> presentation labels for already-exported features

src/scripts/target_usage_manifest.py
  -> indexes source-analysis JSON into corpus/search features

amiga_reversing/disasm/macos_project_payload.py
  -> still computes macos_source_quality_gate_v1 in Python

amiga_reversing/disasm/macos_target_artifact.py
  -> renders that Python-computed gate into source comments
```

The first three are acceptable wrapping behavior when they only display or
index C-exported facts. The Mac OS gate is different: it computes checklist
values, semantic closeout status, residual status, label/xref status, and
claims/does-not-claim text in Python. That model may be useful, but the clean
target is still C-owned source-quality facts.

Migration path:

```text
1. Move Mac OS source-quality gate state into C source-analysis facts.
2. Export the same checklist/status rows through source_analysis_json.
3. Change Python artifact generation to render exported rows only.
4. Delete Python semantic closeout calculations and fixture-only status text.
```

No platform gets an exception: Amiga, Atari, Mac OS, and raw targets all use the
same rule that source-quality meaning is produced by C.

## Fixture Matrix

Primary fixtures:

- Damocles Tetragon payload 2: in-image addresses, false `$42C00` run, absolute
  ranges, low-memory base/vector distinction, lookup tables.
- Starglider: false `ori` code blocks near data and strings.
- Pandora: false-code islands and string/table interactions.
- Magicland Dizzy: dense low-memory app storage and disk/decompression-adjacent
  evidence.
- Midwinter II `mwii`: later scale fixture for labels, orphan-code signals, and
  relocation-backed source-quality checks.

Representative unit tests should use small in-memory C fixtures first. Target
fixtures should then confirm that the isolated patterns are present in real
targets.

Current imported target evidence:

```text
Damocles Tetragon payload 2
  abs_0_00042C00 emits a long `ori` run that should be demoted or refused
  $00042C6C operands are numeric even though abs_0_00042C6C exists in-image
  runtime_address_00042C00 is used where current-image identity may be needed
  current source also shows numeric writes to $000459BA and $000459C6

Starglider
  loc_0_00005B04 is a repeated `ori.b #0,d0` island after an `rts`
  this is a second false-code fixture independent of Damocles decompression

Magicland Dizzy
  dense low-memory `absolute_slot_*` refs exercise range grouping
  `_custom+intena` and `intena(a6)` exercise platform-use naming
  lookup tables exercise data/table descriptor ownership
  current source shows `absolute_slot_00000092`, `absolute_slot_00000790`,
  `_custom+intena`, `intena(a6)`, and many `dc.w ... ; lookup_table` runs

Midwinter II `mwii`
  large quantities of labels and table-shaped data exercise scale and
  false-positive table/range classification pressure

Pandora
  source notes still identify false-code islands adjacent to strings and
  table-shaped data; keep it as the string/table interaction fixture
```

Additional coverage already present or worth keeping imported:

- Conqueror decompressed stage: executor-backed decompression plus load/entry
  recovery at `$400`.
- Starglider 2 bootloader stage: boot/runtime staging without a normal DOS
  file path.
- Adventures of Robin Hood bootloader stages: multi-stage loader and raw stage
  imports.
- Rome AD92 disk 1: non-code DOS-looking bootblock that must remain visible as
  structural asset data, not invalid code.
- 3D Construction Kit II: larger label/orphan-code scale if Damocles,
  Starglider, Pandora, Magicland, and Midwinter II are not enough.

Additional import candidates after corpus regeneration:

```text
Benefactor disks 1-3
  multi-disk Psygnosis target; import if platform semantic-use coverage needs
  more display/audio/disk/blitter examples than Magicland and Damocles provide

Rome AD92 disks 2-3
  same title family as the imported disk 1 asset bootblock; import if the
  structural asset-data path needs multi-disk confirmation

Treasure Island Dizzy
  older Codemasters title; import if Magicland-specific low-memory/table
  patterns need a second same-publisher contrast fixture

Zynaps
  older cracked game disk; import if false-code/orphan-code discovery still
  needs more non-Novagen/non-Rainbird examples after corpus regeneration
```

IPF-only resources such as Elite v2 and Frontier are not immediate fixture
imports unless IPF import support is added. They are useful future coverage for
disk-image diversity, but they should not block the ADF-backed source-quality
work.

## Corpus Search Status

`src/scripts/target_usage_manifest.py` already knows how to index the core
source-quality lanes:

```text
source-quality diagnostics
accepted_code_runs
address_identities
range_ownerships
table_descriptors
expected_symbol_accesses
rendered_symbol_accesses
platform_address_uses
target-pattern:source_quality_*
```

The tests cover those feature emitters. The current checked-in corpus artifacts
do not yet contain any source-backed rows for these new lanes, so corpus search
currently returns no source-quality examples. That means the proposal work
needs one of these actions before corpus-driven discovery becomes reliable:

```text
regenerate corpus/target_usage_manifest.jsonl
regenerate corpus/target_usage_xrefs.jsonl
regenerate corpus/target_usage_snippet_rows
then query target-pattern:source_quality_* and analysis:* lanes
```

One discoverability gap was found in the wrapping layer: expected symbol access
features were indexed but not given first-class labels in the Python/web corpus
feature-label helpers. Those labels should remain Python/web presentation only;
the feature itself must continue to come from C source-analysis JSON.

A second discoverability gap remains around coverage, not existence:
`platform_semantic_uses` is exported, but corpus/xref indexing must be checked
against the current fact shape before promising
`analysis:platform_semantic_use:*` rows. Until those lanes are verified,
`target-pattern:source_quality_platform_semantics` may still need precursor
features such as platform calls, hardware names, platform address uses, and
expected symbol producers.

## Verification Gates

Required:

```text
cmd /c src\build.bat
src\build\m68k_c_unit_tests.exe
uv run python -m pytest tests -q
uv run mypy
uv run ruff check
uv run platform-rendered-source-roundtrip --update-rendered-source --json
uv run platform-rendered-source-roundtrip --json
git diff --check
```

Rendered-source round-trip must stay exact or content-exact according to the
existing report categories. Source-quality improvements should be visible in
checked-in `.s` diffs.

## Acceptance Criteria

- Damocles `$42C00` is no longer silently rendered as accepted code unless a
  real executable origin and credible run ending are proven.
- Damocles `$42C6C`, `$42C70`, `$459BA`, and `$459C6` are handled through
  in-image address identity and expected symbol access checks.
- Numeric operands that target C-owned in-image storage either render through
  the approved symbol or emit a source-quality diagnostic.
- `runtime_address_*` is used only when the address is truly runtime-domain or
  otherwise not representable as current image storage.
- Low-memory base usage does not render as CPU-vector symbols unless the C
  platform-use fact proves vector semantics.
- Hardware, vector, bitmap, copper, audio, disk, blitter, OS-call, and trap
  symbols come from C platform semantic/use facts.
- Absolute memory headers are range-oriented and sourced from
  `M68kAbsoluteAddressRangeIR`.
- Table render output is backed by C table descriptors with consumer and bounds
  evidence.
- Fixed-capacity truncation produces an analysis failure/diagnostic, not a
  silent fallback.
- Render preview does not create durable semantic facts.
- Python/web/report do not infer source-quality meaning.
- Manual/editor changes pass the same C source-quality checks as auto-analysis.
- All output-affecting changes are reflected in regenerated target `.s` files
  and round-trip report output.
- Validation failures discovered during implementation are preserved as
  fixtures and fixed at cause in the same slice when the cause is inside the
  slice scope. "Cause" means the producer, classifier, accepted-run proof,
  platform semantic hook, or render-evidence path that created the bad source.
- A slice is not accepted when it merely adds a diagnostic for an obvious
  producer bug and leaves the restored source wrong.
- A validation failure is not a blocker by itself; it is a work item to trace
  back to the bad producer, classifier, accepted-run proof, platform semantic,
  or render-evidence path and repair there.
- If the validation exposes a legitimate framework problem, the fix belongs in
  this work unless it is demonstrably outside the slice boundary. In that case
  the boundary and follow-up fixture must be explicit, not an excuse to leave a
  known bad conversion/rendering silent.

## Trailing Observations For Later Work

These observations are not part of the partial-code diagnostic patch, but they
matter before proposal 033 can be called complete.

The rendered-source gate previously reported missing recorded source paths for
the Magicland Dizzy hunk targets:

```text
bin/imported/magicland_dizzy_zip/
  Magicland Dizzy (1991)(Codemasters)[cr TRSI][t +2 LSD].adf
```

That was stale extracted-path metadata. The current fix is archive-aware disk
access in the Python C-backend wrapper plus Magicland metadata pointing at the
tracked resource zip:

```text
resources/platform_amiga/
  Magicland Dizzy (1991)(Codemasters)[cr TRSI][t +2 LSD].zip
```

The read-only all-target gate then reports zero failures, with Damocles
Tetragon 02 exact. This is gate hygiene for proposal 033: tracked target
metadata must not depend on ignored extracted disk images.

The current gate also shows many content-exact but not full-file-exact hunk
targets because of known container-shape, relocation ordering/grouping, size,
or policy-divergence categories. Those should not block source-quality slices
when the rendered source is content-exact, but final acceptance should keep the
distinction visible in the report instead of treating them as source render
regressions.

## Non-Goals

- Do not add Damocles-only, Starglider-only, Pandora-only, or Magicland-only
  recognizers.
- Do not blacklist individual opcodes such as `ori`.
- Do not move source-quality decisions into Python, JSON export, or web code.
- Do not preserve internal API compatibility when it keeps the wrong ownership.
- Do not hand-edit generated target source as the fix.
- Do not hide incomplete analysis behind fallback rendering.
- Do not treat exact round-trip as proof of semantic source quality.
