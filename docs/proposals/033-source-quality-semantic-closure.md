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
  -> render preview mutates rendered_symbol_accesses into source_analysis
  -> m68k_source_quality_analyze_rendered_symbol_accesses(...)
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
  int (*append_platform_ranges)(M68kSourceAnalysisIR *source_analysis);
} M68kPlatformSourceQualityHooks;
```

The core owns fact schemas, validation, address identity, range coalescing, and
diagnostics. The platform backend owns the semantic lookup that says "`$DFF09A`
is `_custom+intena`" or "`$74` is only a low-memory base in this instruction
shape."

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
  -> expected_symbol_access emitted with producer=address_identity
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

### Remaining Wrong Boundary: Render Evidence Mutates Source Analysis

`m68k_render_ir.c` now records actual rendered symbol accesses during assembly
source emission. That is the right moment to observe what render emitted, but
the target object is still `M68kSourceAnalysisIR`:

```c
record_rendered_label_statement_access(source_analysis, ...)
record_rendered_instruction_symbol_accesses(source_analysis, ...)
```

That makes render mutate the same object that analysis proved. The cleaner
interface is a separate render evidence object:

```c
typedef struct M68kRenderEvidenceIR {
  M68kRenderedSymbolAccessIR *rendered_symbol_accesses;
  size_t rendered_symbol_access_count;
} M68kRenderEvidenceIR;
```

Then the post-render gate is explicit:

```text
source_analysis.expected_symbol_accesses
  minus render_evidence.rendered_symbol_accesses
  -> source_quality_diagnostics
```

This keeps source analysis immutable during render while still allowing the C
post-render gate to compare intended symbols with actual emitted text.

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

The missing durable fact family is a real platform semantic-use record. The
diagnostic name `platform_semantic_use` exists, but there is not yet a
first-class exported `M68kPlatformSemanticUseIR` analogous to
`M68kPlatformAddressUseIR`. Add it before moving renderer-side comments and
symbols:

```c
typedef struct M68kPlatformSemanticUseIR {
  uint16_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  uint8_t semantic_kind;
  uint8_t access_kind;
  uint8_t confidence;
  M68kPlatformNameRef symbol_ref;
  M68kPlatformNameRef type_ref;
  M68kPlatformNameRef value_domain_ref;
  char *render_text;
} M68kPlatformSemanticUseIR;
```

This is the fact that should drive display/audio/disk/blitter/copper comments,
OS-call input value-domain symbols, stack-cleanup notes, and runtime-address
sink role labels. Render should not rescan forward to find the next platform
call or reclassify a hardware register from raw numbers.

### Remaining Gap: Expected Symbol Producers Are Too Narrow

The current expected-symbol producer covers intrinsic branch/control labels. It
does not yet cover the full set needed for Damocles-style failures:

```text
absolute operand targets in-image storage
PC-relative operand targets storage
generated equates
accepted storage labels
independent label statements
table entry target labels
platform semantic operands
```

Until those producers exist, the post-render gate can catch only a small part
of the label/source mismatch class.

The current producer is specifically
`append_expected_intrinsic_branch_symbol_accesses()`. It walks accepted
instructions, selects branch/call/jump targets with an intrinsic label operand,
skips relocation-covered operands, then requires an existing symbol origin at
the target. That is a good first producer, but it explains why Damocles numeric
absolute storage operands are not caught yet: they are not intrinsic control
targets.

The next producers should be separate functions, not one broad "label exists"
rule:

```text
append_expected_absolute_storage_operand_accesses()
append_expected_pc_relative_storage_operand_accesses()
append_expected_equate_operand_accesses()
append_expected_storage_label_statements()
append_expected_table_entry_target_accesses()
append_expected_platform_symbol_operand_accesses()
```

Each producer should carry a producer id/string into
`M68kExpectedSymbolAccessIR`, so diagnostics can say which analysis obligation
the renderer failed to satisfy.

The current `M68kExpectedSymbolAccessIR` has symbol, source offset, target,
operand, access kind, confidence, and `has_target`, but no producer field. Add a
small enum or interned string field before expanding producers; otherwise the
post-render diagnostic will identify only the missing symbol, not the analysis
rule that required it.

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
  -> expected equate and operand symbol
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

Add precise C producers for:

- relocation-backed branch/call targets
- ordinary absolute/PC-relative operand symbols
- generated equates
- accepted storage labels
- independent label statements

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
  -> demote to orphan-code signal or data

run has origin but no credible ending
  -> source-quality diagnostic

manual seeded invalid run
  -> diagnostic/refusal, not silent acceptance
```

Damocles `$42C00`, Starglider false `ori` blocks, and Pandora false-code blocks
must go through the same generic path.

Current implementation detail:

```text
accepted_run_has_executable_origin == false
  -> accepted_code_without_executable_origin
  -> severity=error blocker=true

run.end_kind == accepted_gap
  -> unterminated_or_invalid_code_range
  -> severity=warning blocker=false
```

That second case is too weak for the failure class. A seeded or auto-accepted
run that falls into data should either be demoted before render or become a
source-quality blocker when negative evidence is present:

```text
accepted_gap + nearby_data/string/table/absolute-storage evidence
  -> severity=error blocker=true

accepted_gap + no negative evidence yet
  -> warning plus review item

manual origin + accepted_gap
  -> manual_evidence_conflict blocker unless explicit boundary proof exists
```

The implementation should avoid opcode-specific checks. The inputs are origin
class, CFG end kind, nearby range ownership, orphan-code signals, structured
data overlap, and address/table/string evidence.

Implementation order:

```text
1. Add entry-point provenance/source fields to M68kAnalysisEntryPoint.
2. Preserve manual_action_log and decision_journal provenance through metadata
   parsing into M68K_FACT_CODE_START_REF.
3. Export provenance in M68kCodeOriginIR.
4. Add source-quality tests for manual seed at valid code, data overlap,
   mid-instruction, and unterminated accepted-gap runs.
5. Change accepted-gap severity to blocker when negative evidence is present.
6. Demote shape-only runs before render when no executable origin remains.
```

### Slice 5: Address Identity And Range Closure

Close the existing C-owned identity/range model instead of adding more
renderer-side special cases. First make identities produce symbol obligations:

```text
M68kAddressObservationIR
  -> M68kAddressIdentityIR
  -> M68kExpectedSymbolAccessIR(producer=address_identity)
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
1. Add M68kPlatformSemanticUseIR and JSON export.
2. Add corpus/xref lanes for analysis:platform_semantic_use:*.
3. Move hardware/display/access comments from render to semantic-use producers.
4. Move next-call input immediate symbol recovery to semantic-use producers.
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

A second, deeper discoverability gap remains by design: there is no exported
`platform_semantic_uses` array yet, so corpus indexing cannot honestly expose
`analysis:platform_semantic_use:*` rows. Add those lanes only when the C fact
exists. Until then, `target-pattern:source_quality_platform_semantics` can be
found only from precursor features such as platform calls, hardware names, and
platform address uses.

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

## Non-Goals

- Do not add Damocles-only, Starglider-only, Pandora-only, or Magicland-only
  recognizers.
- Do not blacklist individual opcodes such as `ori`.
- Do not move source-quality decisions into Python, JSON export, or web code.
- Do not preserve internal API compatibility when it keeps the wrong ownership.
- Do not hand-edit generated target source as the fix.
- Do not hide incomplete analysis behind fallback rendering.
- Do not treat exact round-trip as proof of semantic source quality.
