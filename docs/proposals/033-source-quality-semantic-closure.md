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

### Implemented Slice: Shared Flow And False-Code Signals

The first implementation slice made the flow predicates shared instead of
mirrored locally:

```c
int platform_instruction_has_normal_fallthrough(const M68kInstructionIR *instruction);
int platform_instruction_has_terminal_state_flow(const M68kInstructionIR *instruction);
```

Analysis and source-quality run construction now ask the same question:

```text
rts/jmp/bra/trap-never-returns?
  -> no normal fallthrough
  -> accepted run stops here

ordinary instruction or conditional branch?
  -> normal fallthrough may continue
```

This matters because accepted-code ranges must not smear across a terminal
instruction merely because the next bytes also decode.

The runtime-copy rule was also tightened. A runtime address reference to the
start of a discovered copied range is not enough to seed code:

```text
runtime ref to copied range start
  + operand is data/storage use
  -> keep storage bytes as data

runtime ref to copied range start
  + operand is a control target
  -> may seed runtime-view code
```

This fixes the Damocles/Starglider class where a storage pointer into copied
bytes was upgraded into executable source.

Adjacent direct stub discovery was narrowed in the same spirit. For plain
same-section direct stubs, a sibling entry is not accepted from opcode shape
alone:

```text
reachable stub:
    bra.w real_target

neighboring bytes:
    bra.w possible_target

possible_target has existing code proof?
  yes -> sibling stub may be accepted
  no  -> neighboring bytes stay data/review material
```

Relocation-backed jump templates remain supported by their relocation-specific
path, but the remaining Starglider evidence shows why addends/relocations must
still be treated warily: a relocated value inside bytes that decode as `jmp`
does not by itself prove the containing bytes are code.

Source quality now has an additional blocker for the false-code shape that
Starglider exposes:

```text
accepted code run
  + executable/control origin
  + ends at accepted_gap
  + no terminal/proven continuation
  + non-control operand/data access also targets the run
  -> unterminated_or_invalid_code_range blocker
```

For Starglider this catches the high-score/name area:

```text
$9278..$92BE
  accepted as code by relocation-backed control inference
  also reached by real PC-relative data operands
  decodes until an accepted gap without terminal flow
  -> source-quality failure, not clean restored source
```

That blocker is not the final repair. The follow-through is to use the
diagnostic as a work item for the framework: trace the producer, then prevent
or demote the false relocation-backed template acceptance at cause. The correct
outcome is data/table/string ownership for the high-score area, not a permanent
"known blocker" annotation.

### Implemented Slice: Round-Trip Analysis Export And Guarded Dispatch

The round-trip report now has an optional analysis export path:

```powershell
uv run python -m amiga_reversing.tools.rendered_source_roundtrip_report `
  --json `
  --analysis-export-dir C:\tmp\m68k-roundtrip-analysis
```

For focused work, target ids can be selected directly:

```powershell
uv run python -m amiga_reversing.tools.rendered_source_roundtrip_report `
  --target amiga_disk_starglider-1987-rainbird__amiga_hunk_sg_9832b282 `
  --analysis-export-dir C:\tmp\m68k-roundtrip-analysis `
  --analysis-export-scope all `
  --json
```

By default this writes per-target analysis JSON only for failing rows. The
export contains the round-trip row, C source analysis from the facts-v2 listing
artifact, render evidence from the same source render, and source-quality
explanation:

```json
{
  "target": "amiga_hunk_genam",
  "roundtrip_row": { "...": "..." },
  "analysis": {
    "expected_symbol_accesses": [ "..." ],
    "rendered_symbol_accesses": [ "..." ]
  },
  "source_quality_explanation": { "...": "diagnostics and proof context" }
}
```

This replaces one-off diagnostic scripts. A failing round-trip now carries the
facts needed to find the producer:

```text
round-trip failure
  -> exported analysis JSON
  -> expected accesses / rendered accesses / code runs / data ranges / diagnostics
  -> fix the analysis producer at cause
  -> rerun round-trip
```

Source-quality refusal diagnostics should surface the same trail in normal tool
output, not only in exported JSON:

```text
kind=missing_expected_symbol_access
summary="expected symbol access was not rendered"
evidence="expected_symbol_access:producer=runtime_sink_pointer_operand access=equate symbol=bitmap_00060000 operand=0"
```

The rule is that a blocker is actionable framework work. The diagnostic must
name the producer, intended access kind, symbol, operand, and target when known
so the worker can fix the producer at cause instead of writing another temporary
inspection script.

The export must not use the pure `analyze_project_source_with_c_backend()` path.
That path is intentionally analysis-only and has no render evidence. Round-trip
export now uses the listing artifact analysis payload, which is backed by the
same `M68kRenderEvidenceIR` recorded during source rendering:

```text
CListingArtifact.create(...)
  -> source_plan
  -> source_analysis
  -> render_evidence
  -> analysis_payload()
       expected_symbol_accesses from source_analysis
       rendered_symbol_accesses from render_evidence
```

The export path must also survive partial diagnostic failure. If render-evidence
analysis is the component that refuses source, the worker still needs the
source-quality explanation:

```json
{
  "roundtrip_row": { "status": "exception" },
  "analysis_error": "RuntimeError: source refused",
  "source_quality_explanation": {
    "source_quality_explanations": [
      { "kind": "missing_expected_symbol_access" }
    ]
  }
}
```

Only failure to resolve the target, open metadata, or write the export file
should prevent an export path from being reported. Individual analysis
components should record `*_error` fields and let the remaining components run.

Diagnostic CLI entry offsets should accept the same numeric spellings as source
and notes, so workers can copy addresses directly from source:

```powershell
src\build\platform_file_cli.exe source-quality-explain amiga-raw payload.bin '$400'
src\build\platform_file_cli.exe source-quality-explain amiga-raw payload.bin 0x400
src\build\platform_file_cli.exe source-quality-explain amiga-raw payload.bin 1024
```

The current shared parser already accepts `$nnnn`, `0xnnnn`, decimal, binary
`%nnnn`, character literals, and signed values. CLI paths should keep using
that parser for positional raw entry offsets and `--entry-offset` policy
arguments.

The same rule now applies to Python tooling inputs that workers use while
diagnosing source-quality failures:

```text
reversing-loop --label-offset $42C00
web listing query source_offset=$42C00
manual seed range h0:$42C00..$42C70
platform KB numeric value %10010000
```

These are not independent numeric dialects. They use the shared
`parse_source_int()` helper so a value copied from rendered source, notes, or a
C CLI invocation means the same thing in Python tooling. Decimal text remains
decimal, so `010` is ten rather than an old octal spelling.

The GenAm failure exposed a separate false-code producer. Its real shape is a
zero-guarded PC-indexed word dispatch table:

```asm
    move.w table(pc,d1.w),d0
    beq.b  invalid_or_default_case
    move.b (a4)+,d1
    jsr    table(pc,d0.w)

table:
    dc.w   0
    dc.w   target_1-table
    dc.w   target_2-table
```

The zero entry is not a call to `table`. The `beq` proves that zero branches
around the indirect `jsr`; on the path to the `jsr`, the loaded word is
non-zero. Treating `0` as `table-table` promoted the table bytes as code and
produced an unterminated accepted run.

The fix is general and evidence-based:

```text
indexed word load feeds indexed indirect control transfer
  + nearby/origin-adjacent beq branches around the indirect site
  -> zero table entries are null/default entries
  -> skip zero entries when promoting control targets

indexed control operand base target
  -> table/data base evidence
  -> not a direct code target by itself
```

This preserves valid zero-displacement dispatch entries when there is no guard,
while preventing guarded null entries from becoming false code. The isolated
regression is `facts_v2_pc_indexed_word_dispatch_zero_guard_skips_null_entries`.
The corpus result after the fix:

```text
rendered-source round-trip targets: 55
failures: 0
amiga_hunk_genam: exact
Damocles Tetragon 02: exact
```

### Implemented Slice: Relocation-Backed Jump Template Hardening

The Starglider validation failure proved that a relocated value inside bytes
that decode as `jmp` is not enough proof of code:

```text
text/string/data bytes
  + relocated absolute value
  + bytes happen to decode as jmp abs.l
  + target has no existing code proof
  -> review/data evidence, not accepted code
```

The failing shape was a same-section relocation-backed jump-template scan that
promoted a nearby sibling entry too eagerly:

```text
real relocation-backed stub in section 0
nearby bytes decode as another absolute jmp
target $9278 is data/string/high-score storage
  -> old behavior: promote $9278 as code
  -> new behavior: require existing target code proof for same-section sibling
```

Cross-section relocation-backed templates remain supported because loader
stubs commonly jump from one section into another code section. The wary rule is
only for same-section sibling promotion, where the relocation/addend may simply
be restored data embedded in bytes that also decode legally.

The source-quality diagnostic exposed the bad producer. The fix was made at
that producer, not by accepting a permanent validation failure:

```text
validation failure
  -> analysis export identifies relocation-backed template producer
  -> same-section sibling needs candidate_target_has_existing_code_proof
  -> false code is never accepted
  -> regenerated source is clean
```

Corpus result after this slice:

```text
rendered-source update round-trip targets: 55
failures: 0
amiga_hunk_genam: exact
Damocles Tetragon 02: exact
Starglider: passes source-quality validation
Starglider 2 bootblock: passes source-quality validation
```

### Implemented Slice: Low-Memory Identity And Vector Naming

Damocles Tetragon payload 2 also exposed that low-memory addresses can be
observed inside the CPU-vector address range without being vector semantics.
The fix is not target-specific. Source-quality analysis now splits the raw
address space from the semantic identity used for symbols and ranges:

```text
write.l #handler,$70
  -> raw observation owner: CPU_VECTOR
  -> use_shape: true_vector_install
  -> identity/range owner: CPU_VECTOR
  -> exported owner symbol: m68k_vector_level_4_interrupt_autovector

lea.l $74,a2
move.l value,$63A8(a2)
  -> raw observation owner: CPU_VECTOR address space
  -> use_shape: low_memory_base / low_memory_storage
  -> identity/range owner: ABSOLUTE_MEMORY storage
  -> no vector owner symbol
```

The raw observation can still say that `$74` is numerically inside the vector
area. The address identity and absolute range only become vector-owned when the
instruction shape proves a true vector install. Analysis JSON follows the same
rule, so round-trip exports no longer make low-memory base/storage facts appear
as `m68k_vector_*` definitions.

The same split does not imply automatic `absolute_slot_*` uplift. A low-memory
base/storage observation is useful range evidence, but weak low-memory evidence
alone is not a durable symbol:

```text
lea.l $74,a2
  -> low_memory_base fact
  -> absolute range candidate
  -> no m68k_vector_* symbol
  -> no absolute_slot_00000074 symbol unless stronger storage evidence exists
```

This keeps address-domain naming conservative. Review tooling can surface the
candidate range, but rendered source should not invent a named slot merely
because the value is address-shaped or in low memory.

The isolated regression is in
`test_source_quality_analyze_exports_platform_address_uses`:

```c
low_base_ref.address = 0x74U;
low_base_ref.access_kind = M68K_SIM_ACCESS_COMPUTE_ADDRESS;
low_base_ref.owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR;
```

The expected result is a `low_memory_base` platform-use fact, storage identity,
and an unowned one-off absolute range, with no generated `absolute_slot_*`
symbol. A true write to `$70` remains a vector install and keeps the vector
symbol.

Focused Damocles verification exports analysis JSON for the exact target:

```powershell
uv run python -m amiga_reversing.tools.rendered_source_roundtrip_report `
  --target amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_raw_damocles_53b24620_native_tetragon_02_00000060 `
  --analysis-export-dir C:\tmp\m68k-roundtrip-analysis `
  --analysis-export-scope all `
  --no-write-report --json
```

The source round-trip remains exact. The exported JSON contains
`low_memory_base` and true-vector install facts, keeps
`m68k_vector_level_4_interrupt_autovector` for the write to `$70`, and does not
emit `m68k_vector_level_5_interrupt_autovector` for the `$74` low-memory base.
The same focused export now includes the post-render evidence needed to debug
symbol obligations:

```text
expected_symbol_access_count: 9522
rendered_symbol_access_count: 12667
rendered symbols include abs_0_00042C00, abs_0_00042C6C, abs_0_00042C70
missing_expected_symbol_access: absent
```

### In-Image Address Identity

Damocles originally had labels and numeric accesses that disagreed:

```asm
abs_0_00042C6C:
    ...

    move.w $00042C6C.l,d0
```

The address `$42C6C` is inside the materialized image. If C analysis knows that
storage address and accepts a label for it, the rendered operand should use the
approved symbol or the source-quality gate should explain why it cannot.

The current Damocles Tetragon 02 render now emits the in-image symbol form:

```asm
abs_0_00042C6C:
    dc.b $00,$00,$00,$00

    move.w abs_0_00042C6C.l,d0
```

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

### Implemented Slice: Platform Operand Expressions

Amiga OS call input value-domain rendering used to be decided while emitting a
prior instruction:

```text
render move.l #number,d7
  -> scan forward up to 12 accepted instructions
  -> resolve later _LVOAlert(a6)
  -> discover d7 is alertNumber
  -> translate number to AN_IconLib|AG_OpenLib|AO_DOSLib
  -> rewrite operand during render
```

That was analysis in rendering. The renderer was proving that an earlier
immediate belonged to a later platform call input.

The fact now belongs to source-quality analysis:

```text
recovered platform call _LVOAlert(a6)
  -> generated Amiga input metadata says d7 is alertNumber
  -> accepted previous instruction loads an immediate into d7
  -> value-domain expression is proven
  -> platform_semantic_use(offset=producer,
                           kind=platform_call_input,
                           operand_index=0,
                           operand_expr="AN_IconLib|AG_OpenLib|AO_DOSLib")
```

Render support is intentionally small:

```c
if (use->has_operand_expr && use->offset == instruction_offset) {
  render_asm_include_for_symbol_expr(preview, use->operand_expr);
  attach_amiga_platform_symbol(&instruction->operands[use->operand_index],
                               use->operand_expr);
}
```

There is no forward scan, register tracking, or platform-call resolution in the
renderer for this case now. The same C fact is exported to analysis JSON, so a
round-trip failure can show exactly which operand expression analysis expected.
The existing expected-symbol-access token obligations remain:

```text
operand_expr: AN_IconLib|AG_OpenLib|AO_DOSLib
expected accesses:
  AN_IconLib from platform_call_input_value_domain_operand
  AG_OpenLib from platform_call_input_value_domain_operand
  AO_DOSLib from platform_call_input_value_domain_operand
```

Recovered local helpers use the same rule. If analysis proves that a local
helper ultimately calls `_LVOAllocMem`, a preceding `d1` immediate may render as
`MEMF_FAST` only if the value still reaches the helper call:

```text
moveq.l #MEMF_FAST,d1
jsr     allocmem_helper
  -> operand_expr=MEMF_FAST

moveq.l #0,d1
move.b  (a1)+,d1
jsr     allocmem_helper
  -> d1 was overwritten
  -> no MEMF_ANY symbol
```

The corpus update found the second shape in Search for the King. The old
renderer printed `MEMF_ANY` for the zeroing instruction even though the next
instruction overwrote the argument register. Moving the scan into analysis
removes that false symbol while preserving the valid helper-mediated
`MEMF_FAST` cases in GenAm and MonAm.

### Implemented Slice: Palette Upload Tables

Amiga palette upload detection had the same ownership problem. The renderer
used to watch data pointers and hardware COLOR register pointers, then create a
structured data item while formatting source:

```text
lea.l   palette,a0
lea.l   $00DFF180,a1
move.w  (a0)+,(a1)+

renderer:
  -> infer a0 is source data
  -> infer a1 is COLOR00..COLOR31
  -> create palette structured-data item
```

That is analysis, not rendering. Source-quality analysis now owns the proof:

```text
accepted instruction stream
  -> source pointer tracker proves source section/offset
  -> hardware pointer tracker proves COLOR register range and byte offset
  -> word postincrement copy proves upload shape
  -> accepted source bytes prove the palette range is data, not code
  -> structured_data_item(role=palette, kind=words, consumer=upload_site)
```

The tracker deliberately supports the real address forms already seen in
fixtures:

```text
lea.l section-local-offset,a0
  -> source table in same section

lea.l runtime-address,a0
  -> source table through materialized runtime view

lea.l relocated-absolute,a0
  -> source table in relocation target section
```

The important rule is still conservative. A literal that merely looks like an
address does not become a palette or symbol. Promotion happens only when the
copy into the hardware COLOR range proves how the source bytes are used.

Render lookup no longer runs `render_lookup_infer_amiga_palette_uploads()`.
Render support is now only consumption:

```text
source_analysis.structured_data_items[role=palette]
  -> emit words
  -> attach "palette upload 32 colors" comment at the consumer site
  -> record render evidence
```

The isolated regressions cover same-section, runtime-translated, and
relocation-backed cross-section sources:

```text
facts_v2_palette_upload_auto_classifies_source_table
render_palette_upload_comment_requires_platform_semantic_use
facts_v2_genam_palette_upload_uses_runtime_translated_source_table
facts_v2_palette_upload_uses_source_section_accepted_bytes
```

The negative boundary matters as much as the positive one:

```text
source-quality emits platform_semantic_use(kind=palette, note_text=...)
  -> render prints "; palette upload 32 colors"

test removes platform_semantic_uses before render
  -> render still prints the move and table data
  -> render does not rediscover "; palette upload 32 colors"
```

That keeps palette upload recognition in analysis. Render may format an
analysis-owned note, but it must not recreate the semantic decision from raw
register/data-pointer shape.

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

`m68k_analysis_render_lookup.c` used to run structured-data producers while
building a render cache:

```text
render_lookup_infer_relocation_pointer_tables()
render_lookup_add_auto_structured_data_item()
source_analysis_append_auto_structured_data_policy()
```

Those structured-data producer paths have now moved to C source-quality or have
been deleted as dead render-side helpers. The remaining wrong boundary is a
different family: platform and typed-flow analysis still lives in render lookup
because those passes were historically used to feed both formatting and later
source-analysis export.

Current audit:

```text
render_lookup_infer_global_base_slots()
  -> finds OpenLibrary/typed base slots and app base storage

render_lookup_infer_amiga_recovered_local_call_summaries()
render_lookup_infer_amiga_recovered_function_args()
  -> recovers helper/wrapper API call semantics and stack/register inputs

render_lookup_analyze_amiga_app_state_slots()
render_lookup_analyze_amiga_typed_refs()
  -> infers typed app slots, field accesses, and unresolved typed accesses

render_lookup_record_bootblock_disk_read_call()
render_lookup_infer_bootblock_runtime_copies()
  -> recovers bootblock disk reads and post-read runtime copies
```

This is one analyzer family, not four unrelated renderer conveniences. For
example, bootblock runtime-copy recovery depends on disk-read facts, and
disk-read facts are discovered inside the typed API-call flow that recognizes
`DoIO()` with a seeded `trackdisk.device` IO request. Moving only the runtime
copy pass would still leave the semantic proof in render lookup.

The clean migration is therefore:

```text
analysis/platform-amiga typed-flow pass
  -> recovered_platform_calls
  -> recovered_platform_disk_reads
  -> recovered_platform_runtime_copies
  -> typed app/global/base-slot facts
  -> unresolved typed-access facts

render lookup
  -> imports those facts
  -> materializes labels/comments needed to format already-proven facts
```

The next implementation slices should move this family by output fact group,
but each slice must keep producer evidence together. A slice that only copies a
downstream render lookup array into `M68kSourceAnalysisIR` is not enough; the
analysis that decides the fact exists must move with it.

`render_lookup_infer_platform_runtime_structured_data()` and
`render_lookup_infer_amiga_bitmap_memory_uses()` have been removed from this
list by moving their behavior to source-quality. PC-relative indexed scalar
lookup tables have also moved to source-quality:

```text
accepted PC-relative indexed read
  -> data target proves table start
  -> accepted code bytes, labels, existing structured data, and ownership stop the span
  -> source-quality emits structured_data_item(role=lookup_table,
                                               source_pattern=pc_relative_indexed_read)
  -> optional loop-domain evidence upgrades the entry-count proof
```

This producer deliberately yields when the same word read feeds an indexed
control transfer. That shape is dispatch-table evidence, not a scalar lookup
table:

```text
move.w table(pc,d0.w),d0
jmp    table(pc,d0.w)
  -> dispatch-table classifier owns extent and target proof
  -> generic PC-relative scalar classifier must not preclaim the range
```

Indexed word and keyed-long dispatch tables now also have a source-quality
producer. It records the same durable facts that render lookup previously kept
private:

```text
accepted indexed word table read or keyed-long table load/swap
  -> indexed indirect jump/call consumer
  -> table span from relative code-target scan
  -> consumer offset/registers
  -> target base expression
  -> mask/compare/loop index-domain proof when present
  -> source-quality emits structured_data_item(source_pattern=indexed_word_dispatch
                                               or keyed_long_relative_dispatch)
```

Indexed local pointer tables and indexed postincrement data-read tables have
also moved to source-quality. These shapes are generic analysis, not render
policy:

```text
local base pointer state
  + indexed long read from accepted data
  + entries resolve to accepted source offsets
  -> structured_data_item(role=pointer_table,
                          source_pattern=indexed_local_pointer_read)

local base pointer state
  + repeated postincrement word/long reads
  + accepted data span covers the read count
  -> structured_data_item(role=lookup_table,
                          source_pattern=postincrement_read_sequence)
```

The render lookup code now imports those C-owned structured-data items before
source render. It may still materialize labels or strings required to format
pointer-table targets, but that is render support over imported facts:

```text
source-quality classifies pointer/read-sequence tables
  -> render lookup imports structured_data_items
  -> render materializes target labels/strings when needed
  -> render formats the already-proven table
```

The deleted render-owned classifiers for this closure are:

```text
render_lookup_infer_indexed_word_dispatch_tables()
render_lookup_infer_indexed_local_pointer_tables()
render_lookup_infer_indexed_local_scalar_tables()
render_lookup_infer_indexed_postincrement_data_tables()
```

The old biased-dispatch risk was a pipeline-order problem. The fixed ordering is
now the source path:

```asm
    move.w table(pc,d0.w),d0
    jmp    table+2(pc,d0.w)

table:
    dc.w target0-(table+2) ; leading biased entry must render symbolically
```

```text
decode/facts
  -> source-quality table closure
  -> render lookup imports immutable structured_data_items
  -> source export
```

Source-quality still upserts same-range/same-role table items so weaker early
observations cannot downgrade later dispatch proof.

The generic string/data-span audit is closed for the known producer lanes:
string-table sequences, single terminated/bounded text, Mac OS symbol strings,
and multiline text now originate in source-quality. Render lookup still stores
imported items in its `auto_structured_data_items` cache because that cache is
how the renderer answers range-ownership questions quickly, but the append-back
path that turned render cache entries into source-analysis facts has been
removed.

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

`m68k_source_quality.c` currently still includes generated Amiga runtime
knowledge directly:

```c
#include "generated/amiga_os_runtime.h"
```

CPU exception vector address-use naming and platform-owned address exclusion
have moved behind `platform_facts_v2_*`. Amiga hardware registers, `_custom`,
ExecBase, and library/device semantics are platform extension facts. The
reliable shape is:

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

### Implemented Slice: Platform Address-Use Hooks

The address-use portion of this boundary is now behind `platform_facts_v2_*`
helpers. Source-quality still owns generic address observations, identities,
ranges, expected accesses, and diagnostics, but it no longer formats Amiga
hardware/vector/ExecBase address-use symbols itself:

```c
uint8_t platform_facts_v2_address_use_shape_from_observation(
  uint8_t platform_kind,
  const M68kAddressObservationIR *observation);

const char *platform_facts_v2_address_use_symbol_from_observation(
  uint8_t platform_kind,
  const M68kAddressObservationIR *observation,
  uint8_t shape,
  char *symbol_buf,
  size_t symbol_buf_size);
```

The source-quality flow is now:

```text
M68kAddressObservationIR
  -> platform_facts_v2_address_use_shape_from_observation(platform_kind, ...)
  -> platform_facts_v2_address_use_symbol_from_observation(platform_kind, ...)
  -> M68kPlatformAddressUseIR
  -> expected platform symbol access
  -> render evidence validation
```

Hardware-base relative accesses use the same platform boundary:

```c
int platform_facts_v2_hardware_base_address(
  uint8_t platform_kind,
  uint16_t base_id,
  uint32_t *out_address);

int platform_facts_v2_hardware_base_offset_for_address(
  uint8_t platform_kind,
  uint32_t address,
  uint16_t *out_base_id,
  uint32_t *out_offset);

int platform_facts_v2_address_has_symbolic_owner(
  uint8_t platform_kind,
  uint32_t address);
```

This is deliberately not a naming shortcut. A platform symbol is emitted only
after the access shape has evidence: vector write, low-memory base/storage,
hardware base address, hardware register access, or ExecBase literal. A number
that merely looks like an address remains numeric or review evidence until an
analysis pass proves how it is used.

The test harness now also copies `object->platform_backend_kind` into synthetic
source analyses before source-quality validation. That closes a hidden test
setup gap: platform facts must be selected explicitly, not by accidental
Amiga-default behavior in generic source-quality code.

The follow-up cleanup moved the stack-top absolute-symbol exclusion through
`platform_facts_v2_address_has_symbolic_owner()`. Source-quality still decides
whether an operand needs a rendered absolute symbol, but the answer "this value
is already a CPU-vector or platform-owned hardware address" now comes from
platform facts. That removed the direct CPU runtime include from
`m68k_source_quality.c` for this path.

Remaining work in this family is the larger Amiga semantic producers still
living in generic source-quality and render paths: bitmap/copper/audio/disk
semantic-use classification, OS call input domains, typed app/global slot flow,
and the remaining render lookup platform passes. Those should move in the same
direction: platform facts produce typed evidence, generic validation checks
schema and render evidence, rendering only formats proven facts.

### Partially Closed Gap: Address Identity And Renderer Cleanup

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
the correct ownership.

The basic in-image obligation path is now present:

```text
address_observation
  -> section_storage_address_observation expected access
  -> render emits the storage symbol
  -> M68kRenderEvidenceIR records the emitted symbol
  -> post-render gate compares expected vs rendered
```

Damocles Tetragon 02 verifies that direct storage operands for `$42C00`,
`$42C6C`, and `$42C70` are no longer the old raw-number failure. The focused
round-trip analysis export reports thousands of expected and rendered accesses
and includes `abs_0_00042C00`, `abs_0_00042C6C`, and `abs_0_00042C70` as
rendered symbols.

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
hardware lookups, or materialized-label checks directly. That is now the
remaining problem: the common direct-storage obligation exists, but render still
contains semantic helper decisions that should become C-owned obligations or
explicit "no symbol" decisions.

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

### Implemented Slice: Materialized Code-Patch Addends

Damocles also has the safe form of addend rendering: code writes into the
immediate field of another accepted instruction. The raw address is inside
code, but the source form humans need is the instruction anchor plus the byte
addend:

```asm
    move.l $0(a0,d0.w),$000459BA.l

abs_0_000459B8:
    jsr abs_0_000459B8.l
```

The restored source should make the patch site explicit without inventing a
separate label in the middle of the instruction:

```asm
    move.l $0(a0,d0.w),abs_0_000459B8+2.l

abs_0_000459B8:
    jsr abs_0_000459B8.l
```

This is not a general rule that every addend is trusted. Source-quality emits
the obligation only when all of these are true:

```text
absolute operand observation
  + memory write
  + target maps to materialized runtime/storage bytes
  + target byte is inside accepted code, not at instruction start
  + write width stays wholly inside one accepted instruction
  + the containing instruction has an accepted symbol origin
  -> expected_symbol_access(producer=materialized_code_patch_address_observation)
```

The render evidence must carry the same target section/offset as the expected
access. The visible label spelling may be a runtime/ORG alias such as
`abs_0_000459B8`, while the semantic comparison still uses the concrete anchor
target:

```text
offset=$458C8 operand=1
  expected target=0:$449B8 producer=materialized_code_patch_address_observation
  rendered target=0:$449B8 symbol=abs_0_000459B8
```

This closes the Damocles `$459BA/$459C6` case without weakening the wary addend
rule. If the write lands across instruction boundaries, into unaccepted code,
or into bytes with no accepted anchor, validation should fail or leave review
evidence instead of rendering a reassuring symbolic addend.

The Midwinter II `mwii` update-render pass exposed the matching false-positive
case. Some storage addresses also alias a runtime view where the same numeric
value lands inside section-0 code. That is not enough to create a code-patch
obligation when the observation already has an explicit section-storage target:

```asm
    move.w loc_1_0000312E.l,loc_1_0000319C.l
```

The producer therefore follows the renderer boundary:

```text
owner=runtime_range
  -> may translate runtime address to source code patch anchor

owner=section_storage with explicit target section
  -> storage/address observation owns the operand
  -> do not also require materialized code-patch addend
```

This prevents source-quality from demanding a section-0 addend symbol for an
operand that render correctly chose as section-1 storage.

### Implemented Boundary: Render Evidence Is Separate From Source Analysis

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

The renderer-side ownership boundary is now enforced in the IR shape. Rendered
accesses are not stored on `M68kSectionAnalysisIR` at all: the old
`rendered_symbol_accesses` section fields and
`m68k_ir_section_analysis_append_rendered_symbol_access()` API have been
deleted. Render only appends to `M68kRenderEvidenceIR`. Source analysis is still
passed to source export as read-only formatting input, but a render pass cannot
mutate it with emitted-output facts.

The first implementation slice added the explicit JSON export path:

```c
int source_analysis_to_json_with_render_evidence(
    const M68kSourceAnalysisIR *source_analysis,
    const M68kRenderEvidenceIR *render_evidence,
    char **out_json,
    M68kDiagSink diagnostics);
```

The default `source_analysis_to_json()` is pure analysis export. It has no
rendered-access source to consult, so it emits zero rendered accesses. The
render-evidence-aware form is the only JSON path that exports rendered accesses:

```text
source_analysis_to_json()
  -> expected_symbol_accesses from M68kSourceAnalysisIR
  -> rendered_symbol_access_count: 0
  -> rendered_symbol_accesses: []

source_analysis_to_json_with_render_evidence()
  -> rendered_symbol_accesses from M68kRenderEvidenceIR
  -> emits no rendered accesses for sections missing from the evidence object
  -> has no section mirror fallback
```

The regression fixtures now prove the split:

```text
rendered source export:
  M68kRenderEvidenceIR records label/operand/equate access evidence
  source_analysis_to_json() reports rendered_symbol_access_count: 0

source_quality_analyze_uses_render_evidence_without_section_mutation:
  explicit render evidence export count is 1
  missing_expected_symbol_access does not fire
```

The next slice fixed the listing-artifact lifetime path. Facts-v2 source export
now has an evidence-producing form:

```c
int m68k_facts_v2_render_asm_source_plan_analysis_profile_evidence_alloc(
    const M68kObject *object,
    const M68kAnalysisPolicy *policy,
    char **out_source,
    M68kRenderPlan *out_source_plan,
    M68kFactsV2Profile *out_profile,
    M68kSourceAnalysisIR *out_source_analysis,
    M68kRenderEvidenceIR *out_render_evidence,
    uint8_t fail_on_refused,
    M68kDiagSink diagnostics);
```

The listing artifact keeps that evidence beside the render plan:

```text
PlatformFileListingArtifact
  -> source_analysis
  -> source_plan
  -> render_evidence

platform_file_facts_v2_listing_artifact_analysis_json_alloc
  -> source_analysis_to_json_with_render_evidence(...)
```

That removes the need for ad hoc scripts when inspecting listing/round-trip
analysis JSON from the rendered output path.

The follow-up slice made source-quality explanation details evidence-aware too:

```text
unreferenced_label_statement diagnostic
  -> rendered_label detail
  -> M68kRenderEvidenceIR when supplied
  -> null rendered_label without render evidence
```

The final cleanup in this area was to migrate legacy pure-analysis fixtures to
explicit `M68kRenderEvidenceIR` helpers, then delete the section field/API
entirely. Future source-quality tests that need rendered-output evidence should
construct `M68kRenderEvidenceIR`; tests that only examine analysis facts should
not mention rendered accesses.

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
external_runtime_address_ref_role()
runtime_address_ref_sink_role()
```

Some of those functions are harmless formatting once the fact is already known.
Others decide meaning from an instruction, register state, address, or future
call. Those must move into C analysis/platform facts.

The base-relative hardware-register symbol path is now fact-backed:

```text
lea.l _custom.l,a0
move.w #INTF_CLRALL,intena(a0)

analysis:
  tracks a0 as _custom
  proves operand 1 is hardware_register_access at $00DFF09A
  exports platform_address_use(symbol_name="intena")

render:
  consumes platform_address_use
  keeps direct hardware lookup only when no source analysis is available
```

That matters because `intena(a0)` is not just pretty printing. It is a
semantic claim that `a0` is a hardware base and `$009A(a0)` is the interrupt
enable register. The renderer must not rediscover that claim after analysis.

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
  char *note_text;
  char *operand_expr;
  uint32_t offset;
  uint32_t size;
  uint32_t operand_index;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t role_flags;
  uint8_t kind;
  uint8_t source_pattern_id;
  uint8_t confidence;
  uint8_t has_target;
  uint8_t has_operand_expr;
} M68kPlatformSemanticUseIR;
```

It is exported as `platform_semantic_uses` and currently covers semantic
roles derived from structured data and runtime-address references, such as
bitmap, copper, audio, disk, blitter, palette, sprite, and audio-table uses.

That does not finish renderer-side platform closure. Render still performs
some instruction-local semantic decisions for display/audio/disk/blitter/copper
comments and some address/symbol attachment paths. Those decisions need either:

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

The second covered operand case is direct hardware-register value-domain
symbols:

```text
move.w #$7fff,$00dff09a.l
  -> address observation proves _custom+intena
  -> generated hardware metadata proves exec interrupt flag value domain
  -> value domain formats INTF_CLRALL
  -> expected_symbol_access:platform_hardware_register_value_domain_operand
```

Register-derived hardware-register value-domain symbols are also covered:

```text
lea.l _custom.l,a0
move.w #$7fff,intena(a0)
  -> source analysis tracks a0 as hardware base _custom
  -> intena(a0) resolves to the hardware register value domain
  -> value domain formats INTF_CLRALL
  -> expected_symbol_access:platform_hardware_base_register_value_domain_operand
```

The value-domain formatter for both producer families now sits behind platform
facts:

```c
platform_facts_v2_hardware_base_offset_immediate_expr(
  platform,
  base_id,
  register_offset,
  value,
  use_bit_domain,
  symbol_expr,
  symbol_expr_size);
```

Source-quality still decides that the operand is a hardware write/read and that
an immediate operand must be checked. It no longer opens the Amiga register
metadata to choose the immediate/value-domain expression. That keeps the
analysis producer in C while moving the Amiga-specific value-domain lookup to
the platform facts seam.

Stack-cleanup comments are now a recovered platform-call fact consumption case,
not a render-time rediscovery case:

```text
pea 7.w
trap #1
addq.l #2,a7
  -> source analysis records recovered_platform_call(note_kind=stack_cleanup)
  -> render consumes that fact
  -> addq.l #2,a7 ; KNOWN: stack cleanup for c_rawcin pop 2
```

Runtime-address sink comments are partially moved across the same boundary:

```text
move.l #$00067D00,_custom+dskpt.l
  -> runtime_address_ref(has_sink_address, sink=$DFF020)
  -> source analysis assigns data_class_flags = disk_buffer
  -> render comment consumes the source-analysis runtime ref role first
  -> fallback platform metadata only if the analysis ref has no role
```

The same applies to register-fed sink comments:

```text
move.l d0,_custom+cop1lc.l
  -> source analysis records runtime_address_ref(data_class=copper_list)
  -> render emits ; copper_list pointer from that C-owned role
```

This is not full platform-semantic closure. The fallback still exists because
some render paths can run without a source-analysis payload, and several
copper/display/audio/disk comments still do instruction-local platform lookups.
It does, however, remove one more durable semantic choice from the comment
formatter when source analysis is available.

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
direct hardware register value-domain operands
register-derived hardware register value-domain operands
stack-cleanup comments from recovered platform-call facts
```

The remaining coverage gap is now per-family, not a broad absence of
semantic-use or runtime-sink producers. The already-covered families have
positive fact/export/source checks and, where render ownership was historically
ambiguous, negative boundary tests that remove semantic uses before render:

```text
runtime-address sink pointer operands/comments
disk DMA comments
copper display-layout comments
display-setup comments
bitmap-memory comments
palette upload comments
audio-register comments
hardware-access comments
hardware-value comments
platform address-use operand symbols
platform stack-cleanup comments
platform call-input operand expressions
platform call-input comments
audio length-source comments
audio pointer/period source comments
```

Remaining work should name the exact unpinned family, add its source-quality
producer if missing, and add the same boundary test shape. Do not reintroduce a
generic renderer-side platform scan to close a fixture quickly.

The next coverage is now implemented as a separate producer, not one broad
"label exists" rule:

```text
append_expected_platform_symbol_operand_accesses()
```

It consumes concrete hardware-register platform-address-use facts:

```text
M68kPlatformAddressUseIR(symbol_name="intena",
                         offset=6,
                         operand_index=1,
                         use_shape=hardware_register_access)
  -> expected_symbol_access(symbol="intena",
                            access=operand,
                            producer=platform_address_use)
```

That closes the validation gap for platform-owned operand symbols such as
`intena(a0)` and `aud0+ac_len(a0)`. If source-quality proves the platform
symbol and render later emits `$009A(a0)` instead, the post-render gate must
fail with `missing_expected_symbol_access`.

This is intentionally not applied to every `platform_address_use` shape yet.
Facts such as `execbase_literal`, `low_memory_base`, and vector/storage address
uses remain address-domain facts until their renderer-visible symbol contract is
owned by a dedicated producer.

It also skips platform address uses backed only by conflicted/orphan address
observations. Those facts are still exported for review, but they are not a
rendered operand-symbol obligation while the bytes remain outside accepted
code.

The producer also checks that the `platform_address_use` belongs to the
accepted instruction operand, not merely to the same offset. Alternate decodes
can produce useful address-observation facts at an accepted PC, but they must
not create a rendered-symbol obligation for an operand that the selected
instruction does not actually contain.

The contract mirrors what the renderer can actually emit:

```text
move.w d0,_custom+color.l       -> expected _custom+color operand access
move.w d0,color(a5)             -> expected color operand access
movea.l #$00DFF180,a1           -> no expected _custom+color operand access
```

Immediate values that merely look like hardware addresses remain numeric unless
another semantic producer owns a renderer-visible symbol for that operand. This
prevents validation from demanding a platform name for a literal address load
that the renderer deliberately keeps as a number.

The renderer side also consumes source-analysis platform address uses directly.
If analysis proves that an operand is a hardware register access, rendering must
not depend solely on local render-state rediscovery:

```text
analysis: offset=$4D9C4 operand=1 symbol=aud0+ac_ptr
bytes:    move.l a2,$00A0(a6)
render:   move.l a2,aud0+ac_ptr(a6)
```

Likewise, generated runtime aliases are lower priority than proven platform
hardware symbols:

```text
before: lea.l runtime_code_00DFF180.l,a0
after:  lea.l _custom+color.l,a0
```

Only generated runtime alias names such as `runtime_code_*` and
`runtime_address_*` are replaceable this way. Existing non-generated/manual
symbols keep their names.

Implemented closure:

```text
source-quality creates platform_semantic_use(... operand_expr=...)
  -> the same helper appends expected_symbol_access rows for every symbolic token
  -> producer is the semantic family that owns the operand expression
  -> render consumes operand_expr and records rendered symbol evidence
```

This removes the old split where a semantic-use pass could create the operand
expression while a later, duplicated expected-access pass tried to rediscover
the same producer. The helper now makes the ownership contract local:

```c
append_platform_operand_expr_semantic_use(...,
  operand_expr="INTF_CLRALL",
  expected_producer="platform_hardware_register_value_domain_operand")
```

Existing focused fixtures cover the three migrated families:

```text
platform_call_input_value_domain_operand
platform_hardware_register_value_domain_operand
platform_hardware_base_register_value_domain_operand
```

The render boundary for call-input operand expressions is pinned:

```text
render_platform_call_input_operand_requires_semantic_use
  -> removes platform_semantic_uses and expected operand obligations
     before render
  -> the Alert() setup and call still render
  -> AN_IconLib|AG_OpenLib|AO_DOSLib does not appear
  -> the input value falls back to a numeric immediate
```

This is the rule for reverser-facing symbols: API-domain constants appear only
when analysis has proved the operand is an API input and exported the semantic
operand expression. A raw value that merely equals a useful constant stays raw.

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

Implemented closure:

```text
expected_symbol_access producer is missing or "unknown"
  -> source_quality_diagnostic(
       kind=expected_symbol_access_without_producer,
       origin=auto_analysis,
       blocker=true)
  -> missing-rendered-symbol checking is skipped for that access
     because the primary failure is the untraceable producer
```

This keeps `m68k_ir_section_analysis_append_expected_symbol_access()` defensive:
callers can still construct or import old fixture data and JSON can still show
`"producer":"unknown"`. The validated source-quality path is stricter. If an
expected symbol access participates in rendered-source validation, it must name
the producer that created the obligation, even when the renderer happened to
emit the matching symbol. The focused regression is
`source_quality_analyze_blocks_expected_symbol_access_without_producer`.

Platform operand expressions now have the same closure rule. Once source
analysis chooses to export a symbolic operand expression, every symbol token in
that expression must have a matching `expected_symbol_access` at the same
instruction offset and operand index:

```text
platform_semantic_use(offset=4,
                      operand=0,
                      operand_expr=bitmap_00060000)
  -> expected_symbol_access(offset=4,
                            operand=0,
                            symbol=bitmap_00060000,
                            producer=runtime_sink_pointer_operand)
```

If the semantic expression exists without the obligation, source-quality emits:

```text
kind=platform_operand_expr_without_expected_access
origin=auto_analysis
blocker=true
summary="platform operand expression has no expected symbol access"
evidence="platform_semantic_use:kind=runtime_sink_pointer operand_expr=bitmap_00060000 missing_symbol=bitmap_00060000 operand=0"
```

This is intentionally a source-analysis failure, not a renderer warning. The
renderer may format the expression, but it must not be the only place that knows
the symbol should be visible. Focused regressions:
`source_quality_analyze_blocks_platform_operand_expr_without_expected_access`
and `source_quality_analyze_accepts_platform_operand_expr_expected_access`.

The Damocles `TRIO` target exposed the companion rule for runtime sinks:
do not create a runtime-role operand expression when the operand already has a
stronger loaded-source identity.

```text
move.l #loc_1_00002290,_custom+bltdpt.l
  -> platform_semantic_use(kind=runtime_sink_pointer,
                           target_section=1,
                           target_offset=$2290,
                           note="blitter_destination pointer $00002290")
  -> no operand_expr=blitter_destination_00002290
  -> no expected_symbol_access(runtime_sink_pointer_operand,
                              blitter_destination_00002290)
```

The source-quality fix is cause-level: the runtime sink producer now prefers a
decoded operand target or a unique existing storage symbol origin before it
falls back to a runtime-role equate. This keeps `loc_*`/object storage labels
as address-located data symbols, and reserves runtime sink equates for external
or otherwise unmaterialized addresses.

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

Current implementation progress:

```text
table target-set capacity hit
  -> incomplete_analysis(kind=capacity_exhausted, source=table_target_set)
  -> source_quality_diagnostic(kind=table_target_set_limit)
  -> severity=error blocker=true
  -> source export failure kind=table_target_set_limit
```

The older fixed target-set lane is also no longer the normal path for large
keyed-long dispatch tables. The focused fixture
`facts_v2_swapped_keyed_long_table_has_no_fixed_target_set_cap` proves 65 table
targets are recovered without tripping the fixed-capacity failure. Capacity
diagnostics therefore remain as a loud invariant failure for genuinely
unhandled bounded-analysis cases, not as an accepted truncation mode.

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

That matters because accepted-run handling must not treat an executable origin
as enough to downgrade a bad run:

```text
accepted code without executable origin
  -> error, blocker

accepted code with policy/manual origin but accepted-gap ending
  -> error/blocker unless a credible boundary is proven
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

Current implementation progress:

```text
M68kSourceQualityDiagnosticIR append
  -> severity normalized to error
  -> blocker normalized to true
```

This is enforced at the C IR append boundary for both source-level and
section-level diagnostics. A caller cannot serialize a source-quality warning
and leave the tooling to decide whether to ignore it. If the framework has
enough evidence to emit a source-quality diagnostic, the analysis is failed; if
it does not, the condition belongs in a separate review/candidate fact, not in
the diagnostic stream.

Manual entry-point provenance now survives the C boundary:

```text
target metadata seeded_code_entrypoints
  -> seed_origin/manual source_path parsed by C metadata loader
  -> M68kAnalysisEntryPoint.provenance
  -> M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT
     + manual_action_log_entry_point / decision_journal_entry_point evidence
  -> M68kCodeOriginIR(origin_class=manual_seed)
```

The fact reason stays `policy_entry_point` so existing entry-point behavior and
render compatibility are preserved. The evidence kind carries the stronger
source identity. Source-quality uses that evidence to classify manual origins
and to emit `manual_evidence_conflict` when the manual seed is part of a bad
accepted-code run.

The source-analysis render lookup also now treats code-start evidence as part
of the retained proof value without multiplying code-start refs. When multiple
facts describe the same start, it keeps one ref and prefers manual evidence over
generic evidence, and known evidence over unknown accepted-code evidence:

```text
same section/offset/reason/source
  unknown accepted-code evidence
  decision-journal entry evidence
    -> one code_start_ref
    -> evidence_kind=decision_journal_entry_point
```

That matters because the first isolated propagation test exposed this bug: the
manual fact was produced correctly, but the lookup could later replace it with
a size-bearing accepted-code fact that had no provenance. The fix is at cause,
not a test workaround.

Current focused coverage:

```text
facts_v2_policy_entry_point_preserves_manual_provenance
  -> policy entry provenance reaches source_analysis code_start_refs
  -> source_analysis JSON exports manual_seed origin

source_quality_analyze_exports_manual_code_origin
  -> manual evidence maps policy entry reason to manual_seed origin

source_quality_analyze_blocks_manual_partial_code_as_manual_conflict
  -> same invalid partial decode shape as the generic fixture
  -> diagnostic kind changes to manual_evidence_conflict
  -> diagnostic origin is manual_evidence

source_quality_analyze_blocks_manual_seed_inside_instruction
  -> manual code-start evidence at an interior accepted-code byte
  -> source-quality fails with manual_evidence_conflict

source_quality_analyze_blocks_manual_seed_structured_data_overlap
  -> manual-origin accepted run overlaps structured data
  -> structured data is recorded as code_overlap
  -> source-quality fails with manual_evidence_conflict

source_quality_analyze_blocks_manual_unterminated_gap_as_manual_conflict
  -> manual-origin accepted run decodes but lacks terminal/proven continuation
  -> generic unterminated diagnostic is upgraded to manual_evidence_conflict
```

The source-quality implementation now has two manual-only checks in addition to
the generic run checks:

```text
manual code-start ref
  + certain_code_byte[offset]
  + !certain_code_start[offset]
  -> manual_evidence_conflict

manual-origin accepted run
  + overlaps accepted/conflicted non-code range ownership
  -> manual_evidence_conflict
```

This keeps the policy strict without making every ordinary code/data range
conflict into a manual failure. Manual evidence is only special when it tries to
force code through facts the analysis already knows contradict it.

Platform opword partial-decode coverage is also now explicit:

```text
accepted code start at $0000
  bytes: A9 00 4E 75
  no recovered platform call at $0000
  -> partial_code_block_decode at $0000

accepted code start at $0000
  bytes: A9 00 4E 75
  recovered Mac OS platform call at $0000
  -> platform opword covers $0000..$0002
  -> decoded rts at $0002 supplies terminal run end
  -> no partial_code_block_decode
```

The rule is deliberately fact-based. Source-quality does not bless all A-line
or F-line words as executable. It only treats a two-byte platform opword as
covered when analysis has already recorded a recovered platform call at that
offset.

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
materialized_code_patch_address_observation for safe writes into accepted
instruction interiors
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
1. Done: add entry-point provenance/source fields to M68kAnalysisEntryPoint.
2. Done: preserve manual_action_log and decision_journal provenance through
   metadata parsing into code-start evidence.
3. Done: export provenance through code-start refs and M68kCodeOriginIR.
4. Done: add source-quality tests for manual seed at valid code, data overlap,
   mid-instruction, partial decode, and unterminated accepted-gap runs.
5. Done: add partial-code-block fixtures:
   generic accepted run whose decode stops before a credible terminal;
   same byte shape under Mac OS where an A-line/F-line platform opword proves
   executable flow; same opword under Amiga/raw where no platform proof exists
   and source export is refused.
6. Done: accepted-gap accepted-code runs become blockers when overlapping
   range ownership carries negative evidence or unresolved non-code conflict.
7. Done for current orphan terminal-decode path: weak shape-only runs remain
   review/candidate facts, not accepted code. During migration, any future
   legacy weak-shape accepted runs must be demoted before render.
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
  -> done for current orphan terminal-decode path: report only, no accepted code
  -> covered by tightened isolated C fixtures:
     facts_v2_orphan_absolute_operand_records_unresolved_memory_layout
     facts_v2_orphan_absolute_operand_classifies_amiga_hardware_owner
  -> remaining migration rule: any legacy weak_shape_only accepted run must be
     demoted before render rather than rendered as code

platform opword accepted as executable code
  -> done: source-quality accepts two-byte opword coverage only when recovered
     platform-call evidence exists at that offset
  -> covered by isolated C fixtures:
     source_quality_analyze_blocks_raw_platform_opword_partial_decode
     source_quality_analyze_accepts_macos_opword_platform_call_coverage

accepted gap overlaps negative range evidence
  -> done: fail as unterminated_or_invalid_code_range
  -> covered by isolated C fixture:
     source_quality_analyze_blocks_accepted_gap_with_negative_range_evidence

Starglider 2 runtime copy label validation
  -> validation found an unreferenced rendered label at runtime $380
  -> root cause was producer-side runtime translation choosing a broad copy
     range before the narrower conflicting discovered copy
  -> done: runtime address refs now keep conflicting discovered copies for
     reference resolution and choose the most specific matching runtime range
  -> materialization remains suppressed for conflicting discovered copies
  -> covered by isolated C fixture:
     facts_v2_runtime_ref_prefers_specific_conflicting_copy

rendered source evidence for runtime aliases
  -> done: rendered label/access matching accepts an exact symbol-name match
     when target offsets differ because producer analysis has competing storage
     and runtime views for the same address
  -> covered by isolated C fixture:
     source_quality_analyze_accepts_runtime_label_name_reference

DOS longword-fill bootblock promoted as code
  -> validation/corpus review found a DOS-looking bootblock whose second sector
     is the structural fill pattern DOS80, DOS81, ..., DOSFF
  -> root cause was producer-side disk inspection: boot_block_is_dos_longword_fill
     checked the checksum/root longwords and therefore never recognized the
     fill pattern
  -> done: disk inspection treats zero bootcode plus DOSxx longwords as
     structural bootblock data, not executable code
  -> affected target reimported as asset_data:
     3D Construction Kit II disk 2 amiga_raw_bootblock
  -> stale rendered bootblock.s removed because the target no longer has a
     rendered-source artifact
  -> covered by focused fixtures:
     test_inspect_disk_amiga_dos_longword_fill_bootblock_is_asset_data
     test_c_backend_non_code_bootblock_metadata_does_not_seed_boot_entry
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

Round-trip follow-through on this slice:

```text
platform-rendered-source-roundtrip --update-rendered-source --json
  -> 55 targets checked
  -> 0 failures
  -> 39 full-file exact
  -> 15 content-exact only
  -> 1 unsupported Mac OS assembly target
```

The rerendered target diffs were reviewed. The useful source changes are in the
same direction as the proposal: runtime-copy aliases no longer force storage
`ORG`s where the copied range should remain a runtime view, and Damocles
Tetragon 01 now exposes the copper list structurally instead of as anonymous
bytes. These are source-quality improvements, not round-trip regressions.

Render/source-analysis ownership follow-through:

```text
m68k_render_ir_preview_emit_prepared
  -> now receives const M68kSourceAnalysisIR *

render_asm_instruction
  -> now receives const M68kSourceAnalysisIR *
```

This does not move more analysis into rendering. It tightens the opposite
contract: rendering may consume source-analysis facts and emit render evidence,
but it may not mutate source-analysis state while formatting output.

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
5. Done for hardware value-domain immediate operands: source-quality emits
   `hardware_value` semantic uses with `operand_expr`; render only consumes the
   expression.
6. Done for runtime-address sink pointer comments: source-quality emits
   `runtime_sink_pointer` semantic uses and render appends their `note_text`.
7. Done for base-relative hardware register operand symbols: source-quality
   emits `platform_address_use` facts from its hardware-base tracker, and
   render consumes those facts for operands such as `intena(a0)` and
   `aud0+ac_len(a0)`.
8. Done for palette upload comments: source-quality emits
   `palette` semantic uses with `note_text`, and render does not rediscover the
   upload comment when those facts are removed.
9. Done for inferred hardware-base seed production: source-quality owns direct
   and callback-indirect propagation, and render lookup no longer stores or
   exports inferred hardware-base seeds.
10. Delete renderer scans once equivalent C facts drive the same source.
```

Keep `M68kPlatformAddressUseIR` for address-shape facts. Use
`M68kPlatformSemanticUseIR` for higher-level meanings and comments.

The hardware-base seed ownership gap is now closed for the direct and
callback-indirect shapes that feed Amiga `_custom` register naming.
Source-quality owns the seed producer and consumer side: it infers the seed,
then uses the same seed list to produce `platform_address_use`, hardware note,
hardware value-domain, and runtime-sink facts.

```text
old:
  render_lookup_infer_amiga_call_hardware_base_seeds()
    -> inferred_hardware_base_seeds
    -> copied into M68kSourceQualityHardwareBaseSeed[]
    -> source-quality emits C-owned facts

current direct-call shape:
  source-quality tracks proven hardware-base registers
    + same-section direct call target
    -> source-quality seeds the callee entry directly
    -> source-quality emits C-owned facts

current callback-indirect shape:
  lea.l callback_1(pc),a0
  move.l a0,$003E(a3)
  lea.l callback_2(pc),a0
  move.l a0,$003E(a3)
  lea.l _custom,a5
  movea.l $003E(a3),a0
  jsr (a0)

  source-quality sees two callback targets stored into the same base/field
    + the indirect call loads that same field into the control register
    + the call-site state proves a5 is _custom
    -> source-quality seeds each callback entry with a5=_custom
    -> source-quality emits C-owned facts
```

The direct and callback-indirect slices both preserve the existing conflict
behavior: two different hardware bases for the same section/offset/register
seed make the seed conflicted and prevent propagation. The old render lookup
seed cache, its callback scanner, and the facts-v2 copy bridge have been
deleted; render no longer produces semantic seed input for source-quality.

Current runtime-sink closure:

```text
runtime address ref
  -> source-quality exports M68kPlatformSemanticUseIR(kind=copper_list, ...)
  -> renderer formats the sink pointer comment from that semantic-use role
  -> source still renders the same useful comment, but the role decision is no
     longer recovered from runtime-ref flags inside render
```

The fixture `facts_v2_register_runtime_sink_auto_classifies_copper_list` now
checks both sides:

```c
M68K_C_ASSERT(strstr(analysis_json, "\"kind_name\":\"copper_list\"") != NULL);
M68K_C_ASSERT(strstr(source, "\tmove.l d0,_custom+cop1lc.l\t; copper_list pointer\n") != NULL);
```

Current disk-DMA comment closure:

```text
accepted hardware write observation
  + destination is DSKLEN/DSKSYNC
  + source operand is an immediate value
  -> source-quality exports M68kPlatformSemanticUseIR(kind=disk_dma,
                                                      note_text=...)
  -> renderer appends note_text
  -> renderer does not recompute whether the write is disk DMA
```

The semantic-use fact now has an optional note field for comments that are
already fully decided by C analysis:

```c
typedef struct M68kPlatformSemanticUseIR {
  char *note_text;
  uint32_t offset;
  uint32_t size;
  ...
} M68kPlatformSemanticUseIR;
```

For example:

```asm
    move.w  #$9F40,_custom+dsklen.l  ; disk DMA read 16000 bytes
```

comes from:

```json
{
  "kind_name": "disk_dma",
  "note_text": "disk DMA read 16000 bytes"
}
```

The boundary is now covered negatively as well. If a test mutator removes
`platform_semantic_uses` after source-quality analysis, render must not
recreate the higher-level disk-DMA comment:

```c
M68K_C_ASSERT(strstr(source, "\tmove.w #$9F40,") != NULL);
M68K_C_ASSERT(strstr(source, "disk DMA read 16000 bytes") == NULL);
```

This is intentionally not a renderer-side analysis shortcut. In the source
export path, renderer formatting consumes C-owned note text and operand symbols.
If source analysis is present and the fact is absent, render must leave the
operand/comment unsemantic rather than recreate the claim.

Current audio-register comment closure:

```text
accepted hardware field access
  + destination/source is audN+ac_len/ac_per/ac_vol/ac_dat
  + absolute field address or proven _custom base-relative field address
  -> source-quality exports M68kPlatformSemanticUseIR(kind=audio_register,
                                                      note_text=...)
  -> renderer appends note_text
  -> render no longer contains audio-register comment decisions
```

The important follow-through was the base-relative case:

```asm
    lea.l   _custom.l,a0
    move.w  #$40,aud0+ac_len(a0)       ; sound sample length 128 bytes
    move.w  d0,_custom+aud0+ac_per.l   ; audio period
```

Absolute hardware observations already carried enough information for analysis
to attach notes. The `_custom` base-relative form did not, so the fix was not
to keep audio logic in render. Source-quality now scans accepted instructions
with its hardware-base tracker and emits the same `audio_register` semantic-use
notes for base-relative hardware fields.

Regression coverage now checks both the visible source and exported facts:

```c
M68K_C_ASSERT(strstr(analysis_json, "\"kind_name\":\"audio_register\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"sound sample length 128 bytes\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json, "\"note_text\":\"audio data word\"") != NULL);
```

The same rule covers hardware operand symbols. Source-quality emits
`platform_address_use` records and matching expected symbol accesses for proven
hardware-base and hardware-register operands:

```text
lea.l _custom.l,a0
move.w #INTF_CLRALL,intena(a0)
  -> platform_address_use(offset=move, operand=1,
                          shape=hardware_register_access,
                          symbol_name="intena")
  -> expected_symbol_access(producer=platform_address_use,
                            symbol_name="intena")
```

The focused negative fixture clears the `symbol_name` after source-quality
analysis. Rendering must not rediscover `intena(a0)` from the tracked `_custom`
base:

```text
facts_v2_render_asm_source_does_not_recreate_missing_platform_address_symbol
  -> clears platform_address_use.symbol_name for intena
  -> renders #INTF_CLRALL,$009A(a0)
  -> does not render intena(a0)
```

Renderer fallback for hardware register names is now only a no-source-analysis
preview compatibility path. It is not allowed to participate in source export
or post-render validation.

The render boundary is also explicit:

```text
render_audio_register_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> aud0+ac_len/aud0+ac_per operands still render
  -> "sound sample length ..." and "audio period ..." do not appear
```

Current hardware-access comment closure:

```text
accepted hardware register/range access
  + read from JOY0DAT/JOY1DAT/INTREQR
    or non-immediate write into COLOR range
  + absolute operand or proven _custom base-relative operand
  -> source-quality exports M68kPlatformSemanticUseIR(kind=hardware_access,
                                                      note_text=...)
  -> renderer appends note_text
  -> render no longer contains those access-comment recognizers
```

Examples:

```asm
    move.w  d0,_custom+color+$1E.l   ; palette color 15
    move.l  a0,_custom+color.l       ; palette colors 0-1
    move.w  _custom+joy0dat.l,d0     ; joystick/mouse port 0 data
    move.w  _custom+intreqr.l,d0     ; interrupt request state
```

The fix uses the same two evidence paths as audio:

```text
absolute hardware observation
  -> source-quality note

accepted instruction + source-quality hardware-base tracker
  -> base-relative hardware note
```

The rendered output is unchanged, but the source of truth moved. Tests assert
both `kind_name:"hardware_access"` and the expected `note_text` values for
palette, joystick/mouse, and interrupt-state comments.

The render boundary is explicit for this family too:

```text
render_hardware_access_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> color/joy0dat operand symbols still render from platform-address facts
  -> "palette color ..." and "joystick/mouse ..." do not appear
```

Current immediate hardware-value comment closure:

```text
accepted hardware register write
  + source operand is an immediate value
  + destination is display/blitter setup register
    or DSKLEN/DSKSYNC through absolute/base-relative addressing
  -> source-quality exports M68kPlatformSemanticUseIR(kind=hardware_value
                                                      or disk_dma,
                                                      note_text=...)
  -> renderer appends note_text
  -> instruction render no longer has a hardware display/disk fallback
```

Examples:

```asm
    move.w  #(4<<PLNCNTSHFT)|COLORON,_custom+bplcon0.l
            ; display 4 bitplanes lores color

    move.w  #(120<<6)|18,bltsize(a0)
            ; blitter size 120 rows x 18 words (36 bytes/row)

    move.w  #$4489,dsksync(a0)
            ; disk sync word $4489
```

This closes the instruction-comment migration for the families covered by the
old `attach_amiga_hardware_display_comment_for_render()` and
`attach_amiga_hardware_access_comment_for_render()` paths. Instruction comments
now come from C source-quality semantic-use facts.

The render boundary for hardware-value notes is pinned:

```text
render_hardware_value_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses and their expected operand obligations
     before render
  -> display/blitter/disk-sync writes still render
  -> "display 4 bitplanes ...", "blitter size ...", and
     "disk sync word ..." do not appear
```

This test clears expected accesses as well as semantic uses because the same
`hardware_value` fact family can own operand expressions and comments. The
boundary being tested here is only the comment: render must not rediscover the
human note after analysis facts are removed.

Current hardware value-domain operand closure:

```text
accepted hardware register access
  + source operand is an immediate value
  + hardware register has a value/bit domain or a safe custom formatter
  -> source-quality exports M68kPlatformSemanticUseIR(kind=hardware_value,
                                                      operand_index=N,
                                                      operand_expr=...)
  -> source-quality exports expected symbol accesses for the expression
  -> renderer attaches operand_expr to that operand
  -> renderer does not resolve hardware register state to rewrite immediates
```

This is separate from comments. A register write can need both an operand
expression and a note, but the proof belongs in source-quality in both cases:

```asm
    move.w  #INTF_CLRALL,intreq(a5)
    move.w  #DMAF_SETCLR|DMAF_MASTER,dmacon(a5)
```

The moved path covers direct absolute hardware accesses and base-relative
hardware accesses. Base-relative facts are seed-aware, so callback targets and
local helpers that inherit a hardware base register do not fall back to
renderer-only state. The old
`attach_amiga_hardware_register_immediate_symbols()` scan was deleted from
`m68k_render_ir.c`; render now consumes `platform_semantic_use` operand
expressions.

Current hardware register operand-symbol closure:

```text
accepted instruction + source-quality hardware-base tracker
  + operand is memory read/write/compute through a known hardware base
  + generated Amiga metadata names the register/field/range
  -> source-quality exports M68kPlatformAddressUseIR(
       use_shape=hardware_register_access,
       symbol_name="intena" or "aud0+ac_len",
       address=$00DFF09A or field address)
  -> renderer attaches that symbol to the operand
  -> renderer does not call hardware-register lookup for source-analysis-backed
     base-relative operands
```

Regression coverage now checks that the rendered source and the analysis facts
agree:

```c
M68K_C_ASSERT(strstr(source,
  "\tmove.w #INTF_CLRALL,intena(a0)\n") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"use_shape_name\":\"hardware_register_access\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json, "\"symbol_name\":\"intena\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json, "\"symbol_name\":\"aud0+ac_len\"") != NULL);
M68K_C_ASSERT(expected->producer != NULL &&
  strcmp(expected->producer, "platform_address_use") == 0);
```

The retained renderer fallback is only for callers that render without source
analysis. The normal rendered-source path must have C-owned facts; if those
facts are missing, the fix is to improve analysis, not to reintroduce
renderer-side platform reasoning.

The next tightening removed the unsafe fallback for incomplete C facts. If
`source_analysis` contains a `platform_address_use` for a hardware register or
hardware base but that use has no `symbol_name`, render now leaves the operand
numeric instead of calling Amiga hardware lookup to recreate a name:

```text
platform_address_use(kind=hardware_register_access, symbol_name=NULL)
  -> render $009A(a0)
  -> do not render intena(a0)
  -> source-quality/analysis must be fixed to publish symbol_name
```

The regression mutates a valid `_custom` base-relative `intena(a0)` use by
clearing the C-owned symbol before prepared rendering. The rendered source must
show `$009A(a0)`, proving render did not hide the incomplete analysis fact.

The same cleanup pass deleted stale render-lookup indexed-dispatch helpers that
were no longer referenced after source-quality/table analysis took ownership of
those cases. That was fix-at-cause work exposed by the dead-code gate, not a
cache or test workaround.

Custom symbolic expressions such as BPLCON0 plane-count composition and BLTSIZE
height/width composition remain supported, but as shared platform formatting:

```c
int platform_amiga_hardware_register_custom_immediate_expr(
  const AmigaOsHardwareRegisterInfo *hardware_register,
  uint32_t value,
  int use_bit_domain,
  char *expr,
  size_t expr_size);
```

That helper formats a semantic case already proven by source-quality. It must
not be used as a renderer-side license to discover whether an operand should be
symbolic.

Current copper-row comment closure:

```text
structured data item has role=copper_list
  -> source-quality walks intact 4-byte copper rows
  -> source-quality exports M68kPlatformSemanticUseIR(kind=copper_row,
                                                     note_text=...)
  -> source-quality exports M68kPlatformSemanticUseIR(kind=copper_display_layout,
                                                     note_text=...)
  -> renderer appends note_text for that row
  -> renderer emits the whole-list layout note as a comment line
  -> renderer does not recompute wait/display/pointer row comments
```

The producer mirrors the renderer's raw-word split rule: if a label lands on
the second word of a would-be copper row, source-quality does not publish a
`copper_row` fact for bytes that render must split. The focused fixture checks
both source text and analysis JSON:

```c
M68K_C_ASSERT(strstr(analysis_json, "\"kind_name\":\"copper_row\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"display window start v=$2C h=$81\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"copper wait v=$2C h=$06 mask $FFFE\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"bitmap pointer $12345678\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"kind_name\":\"copper_display_layout\"") != NULL);
```

The negative boundary is equally important. If a test removes
`platform_semantic_uses` before rendering, the structured copper list may still
render ordinary register/value expressions, but no source-quality-owned row
semantics may survive:

```text
render_copper_display_layout_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> "display layout 2 bitmap planes ..." does not appear
  -> "bitmap pointer $00010000" does not appear
  -> bitmap_00010000_hi / bitmap_00010000_lo do not appear
  -> copper bytes still render
```

That keeps the split clear: copper-list formatting is renderer support;
bitmap-pointer interpretation is source-quality evidence.

Bitmap-memory comments now follow the same rule:

```text
runtime ref to copper list sink
  -> source-quality creates copper-list structured data item
  -> source-quality reads copper bitmap pointer rows
  -> source-quality creates bitmap runtime refs
  + later absolute/base-relative bitmap memory use
  -> source-quality exports M68kPlatformSemanticUseIR(kind=bitmap_memory,
                                                     note_text=...)
  -> renderer appends note_text on the instruction
```

Those bitmap runtime refs are semantic evidence, not automatic symbol
promotion:

```text
lea.l $00010010.l,a0
  + $00010010 lies inside a proven bitmap plane
  -> render numeric operand
  -> add "; bitmap memory plane 0 +$10 ($00010010)"
  -> do not coin runtime_address_00010010

movea.l #$00068000,a2
  + destination is an address register
  + $00068000 is a proven bitmap plane base
  -> address setup for bitmap memory
  -> render numeric operand/comment, not runtime_address_00068000
```

The render fallback that attaches generic `runtime_address_*` symbols must
yield when source-quality already emitted a stronger bitmap-memory semantic
use. A bitmap comment proves "this value is part of a bitmap range"; it does
not prove that the literal itself is a durable named address.

The boundary fixture is:

```text
facts_v2_copper_bitmap_memory_uses_are_commented
  -> proves source-quality emits bitmap_memory notes

render_bitmap_memory_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> code still renders
  -> "bitmap memory plane ..." does not appear
```

That rule is now applied to the generic fallback itself: rendering no longer
promotes a plain address-looking literal to `runtime_address_*` just because the
operand feeds an address-like instruction form. The renderer may use a runtime
symbol when analysis has emitted a runtime-address ref/range fact, a sink role,
or a materialized runtime source mapping. Without that C-owned fact, the operand
stays numeric:

```asm
    movea.l #$4418C,a0
```

not:

```asm
runtime_address_0004418C EQU $4418C
    movea.l #runtime_address_0004418C,a0
```

The focused fixture is:

```c
M68K_C_ASSERT(strstr(source, "\tmovea.l #$4418C,a0\n") != NULL);
M68K_C_ASSERT(strstr(source, "runtime_address_0004418C") == NULL);
```

The same boundary applies to Amiga API call inputs. `SetFunction` takes a
negative function offset, but that value is an argument-domain scalar, not a
memory address. Source-quality now records the direct stack argument as a
platform call input and suppresses the otherwise tempting absolute-slot
obligation:

```asm
    pea.l $FFFFFF94.l    ; KNOWN: arg +8 funcOffset long
```

not:

```asm
runtime_address_FFFFFF94 EQU $FFFFFF94
    pea.l runtime_address_FFFFFF94.l
```

and not:

```asm
absolute_slot_FFFFFF94 EQU $FFFFFF94
    pea.l absolute_slot_FFFFFF94.l
```

The focused fixture asserts both the visible source and the source-analysis
contract:

```c
M68K_C_ASSERT(strstr(source,
  "\tpea.l $FFFFFF94.l\t; KNOWN: arg +8 funcOffset long\n") != NULL);
M68K_C_ASSERT(strstr(source, "runtime_address_FFFFFF94") == NULL);
M68K_C_ASSERT(strstr(source, "absolute_slot_FFFFFF94") == NULL);
M68K_C_ASSERT(saw_call_input_use);
M68K_C_ASSERT(!saw_bad_expected_access);
```

String-pointer API inputs follow the same ownership rule. When analysis has
already recovered a platform call and knows that one of its documented inputs is
a string pointer, source-quality should mark the pointed bytes as string data
without asking source export to discover that semantic fact:

```asm
    movea.l $4.w,a6
    lea.l   dos_library_name(pc),a1
    jsr     _LVOOldOpenLibrary(a6)
    rts

dos_library_name:
    dc.b "dos.library",0
```

The analysis path is:

```text
recovered platform call OldOpenLibrary
  -> documented input A1 is STRING_PTR
  -> pointer tracker proves A1 targets image bytes
  -> source-quality validates a bounded C string span
  -> M68kAnalysisStructuredDataItem(kind=STRING,
                                    source_pattern=api_string_pointer)
```

That fact must exist before source rendering. A focused no-render fixture
asserts it through `m68k_facts_v2_collect_source_analysis_profile()`, so the
test does not pass merely because the source exporter happened to print a
string.

Render lookup now consumes this C-owned fact instead of rediscovering it from
platform-call inputs. The renderer may still register a formatting span so the
visible source stays readable, but it does not decide that the bytes are an API
string:

```text
source-quality:
  recovered platform call + generated STRING_PTR input metadata
  + pointer tracker proves target bytes
  + C string validation
  -> structured_data_item(kind=STRING, source_pattern=api_string_pointer)

render lookup:
  imports the structured-data item
  -> formats the already-proven string span
  -> does not scan call inputs to create API-string facts
```

The pointer tracker covers both address-register and data-register API string
inputs. That matters for `Open`, where the filename travels through `D1` and
may be relocation-backed:

```asm
    move.l  #libfile_name,d1
    move.l  #MODE_OLDFILE,d2
    jsr     _LVOOpen(a6)
    move.l  #path_prefix,d1
    jsr     _LVOOpen(a6)

path_prefix:
    dc.b "LIBS:"
libfile_name:
    dc.b "monam.libfile",$00
```

The C producer must treat the nested pointer start as a boundary, not as a
reason to split the outer string byte by byte. Existing compatible text ranges
can be upgraded to `api_string_pointer`; incompatible structured data, code, or
conflicted ownership still stops the promotion.

The focused fixtures assert both the no-render analysis fact and the visible
source shape:

```c
M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_STRING_POINTER,
  string_item->source_pattern_id);
M68K_C_ASSERT(strstr(source, "loc_0_0000001C:\n\tdc.b \"LIBS:\"\n") != NULL);
M68K_C_ASSERT(strstr(source, "loc_0_00000021:\n\tdc.b \"monam.libfile\",$00\n") != NULL);
```

Exact-length API text buffers, such as `Write(file, buffer, length)`, now use
the same source-quality ownership model, but with their own source pattern. They
are not C strings and must not use `api_string_pointer`:

```text
source-quality:
  recovered _LVOWrite call
  + D2 buffer pointer proves target bytes
  + D3 scalar proves exact length
  + bounded multiline text-shape validation
  -> structured_data_item(kind=STRING, source_pattern=api_text_buffer)

render lookup:
  imports the structured-data item
  -> formats the already-proven bounded text span
  -> does not scan Write inputs to create text-buffer facts
```

The no-render fixture asserts the analysis fact directly:

```c
M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_TEXT_BUFFER,
  text_item->source_pattern_id);
M68K_C_ASSERT_U32(24U, text_item->size);
```

The shape gate remains deliberately narrower than generic text inference: the
buffer must be exact-length, printable/multiline, non-code, relocation-free,
not already owned by incompatible structured data, and not immediately followed
by a zero terminator that would make it a C-string candidate instead.

Copper pointer display-setup comments now follow the same rule too:

```text
accepted immediate writes to display hardware registers
  + runtime ref to a structured copper list
  -> render lookup records/classifies the copper-list runtime ref only
  -> source-quality exports M68kPlatformSemanticUseIR(kind=display_setup,
                                                     note_text=...)
  -> renderer emits the note as a copper-list header comment
```

The focused fixture asserts the source-analysis fact:

```c
M68K_C_ASSERT(strstr(analysis_json, "\"kind_name\":\"display_setup\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"display setup 4 bitplanes lores color ...\"") != NULL);
```

This note is intentionally list-level, like `copper_display_layout`, because it
shares the copper-list start offset with the first row. Rendering it as an
inline row comment would compete with the row's own `bitmap pointer` note.

The render boundary is pinned too:

```text
render_display_setup_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> code and copper data still render
  -> "display setup 4 bitplanes ..." does not appear
```

The same placement rule applies when the copper list cannot be emitted through
the structured copper-list renderer and must remain raw bytes:

```asm
abs_0_000517FC:
    ; display layout 4 bitmap planes $00068000..$0006DDC0 step $1F40
    dc.b $2B,$01,$FF,$FE,$01,$00,$42,$00,...
```

That is rendering support, not render-time analysis. The renderer is only
placing an existing `M68kPlatformSemanticUseIR(kind=copper_display_layout)` at
the raw span start. If the fact is absent, the renderer must not rediscover it
from bytes.

Hardware-base semantic notes follow the same source-quality rule. Render lookup
may still infer that a local helper inherits a hardware base register, because
that is part of existing platform flow analysis:

```asm
    lea.l _custom.l,a6
    bsr.w helper
    rts
helper:
    move.w #$9F40,dsklen(a6)    ; disk DMA read 16000 bytes
    rts
```

But the comment must be exported from source-quality:

```c
M68K_C_ASSERT(strstr(analysis_json, "\"kind_name\":\"disk_dma\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"disk DMA read 16000 bytes\"") != NULL);
```

This now relies on source-quality's own inferred hardware-base seed list. It
avoids a second renderer-only semantic path while keeping existing targets that
rely on helper and callback base propagation.

Audio length-source comments now follow the same rule for the migrated case:

```asm
    move.w  -2(a0),d1
    asl.w   #1,d1
    move.w  d1,_custom+aud0+ac_len.l
            ; audio sample length derived from -$0002(a0) header word
```

```text
accepted register load from displacement(aN)
  + register-preserving immediate transform
  + later write of that register to ac_len
  -> source-quality exports M68kPlatformSemanticUseIR(kind=audio_register,
                                                     note_text=...)
  -> renderer appends note_text
  -> render lookup no longer owns the ac_len source comment
```

The focused fixture asserts both sides:

```c
M68K_C_ASSERT(strstr(source,
  "\tmove.w d1,_custom+aud0+ac_len.l\t"
  "; audio sample length derived from -$0002(a0) header word\n") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"audio sample length derived from -$0002(a0) header word\"") != NULL);
```

The render boundary is pinned:

```text
render_audio_length_source_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> the ac_len write still renders
  -> "audio sample length derived from -$0002(a0) header word" does not appear
```

Audio period-source provenance is now C-owned too, but it uses a target-bearing
semantic fact rather than baking a rendered label into source-quality text:

```asm
    move.w  period_table(pc,d0.w),d0
    asl.l   #2,d0
    move.w  d0,_custom+aud0+ac_per.l
            ; period from period_table+$02 transformed | audio period
```

```text
accepted word load from C-known data target
  + register-preserving immediate transform
  + later write of that register to ac_per
  -> source-quality exports M68kPlatformSemanticUseIR(
       kind=audio_period_source,
       has_target=true,
       target_section_index=...,
       target_offset=...,
       note_text="transformed")
  -> renderer formats the target label from the target fields
  -> generic audio-register note still contributes "audio period"
```

This keeps the ownership line intact:

```text
C analysis proves "period source target is section/offset, transformed"
renderer spells that target as loc/runtime/policy label text
```

The fixture asserts exported analysis, not just rendered text:

```c
M68K_C_ASSERT(strstr(analysis_json,
  "\"kind_name\":\"audio_period_source\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"target_section_index\":0,\"target_offset\":42") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"transformed\"") != NULL);
```

Dynamic audio pointer-source provenance now follows the same pattern, with one
important extension: the fact needs two targets when a dynamic offset table is
known.

```asm
    lea.l   sound_sample,a0
    adda.w  sample_offsets(pc,d0.w),a0
    lea.l   $0030(a0),a0
    move.l  a0,_custom+aud0+ac_ptr.l
            ; source sound_sample+$30 + dynamic offset from sample_offsets | sound_sample pointer
```

```text
accepted source pointer load
  + accepted indexed offset add
  + later write of that address register to ac_ptr
  -> source-quality exports M68kPlatformSemanticUseIR(
       kind=audio_pointer_source,
       has_target=true,
       target_section_index=sample source section,
       target_offset=sample source offset,
       has_secondary_target=true,
       secondary_target_section_index=offset table section,
       secondary_target_offset=offset table offset,
       note_text="dynamic_offset")
  -> renderer formats the primary and secondary targets as labels
  -> generic audio-register note still contributes "sound_sample pointer"
```

The key rule is the same as for period source comments:

```text
C analysis proves "sample pointer source target, optional dynamic table target"
renderer chooses only spelling: local label, runtime label, or generated label
```

The fixture now asserts that the dynamic pointer comment is backed by exported
semantic uses, and the render boundary is pinned:

```text
render_audio_pointer_period_source_comments_require_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> the ac_ptr/ac_per writes still render
  -> "source loc_0_00000060 ..." does not appear
  -> "dynamic offset from loc_0_00000028" does not appear
  -> "period from loc_0_0000002A transformed" does not appear
  -> generic audio notes such as "sound_sample pointer" and "audio period"
     do not appear
```

This confirms the renderer is only spelling source-quality facts. It is not
rerunning the audio provenance analysis or regenerating generic audio notes
from register names.

The fixture now asserts that the dynamic pointer comment is backed by exported
analysis:

```c
M68K_C_ASSERT(strstr(analysis_json,
  "\"kind_name\":\"audio_pointer_source\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"target_section_index\":0,\"target_offset\":96") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"secondary_target_section_index\":0,\"secondary_target_offset\":40") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"dynamic_offset\"") != NULL);
```

The render-owned audio pointer fallback in `m68k_analysis_render_lookup.c` was
deleted. If this comment disappears in future work, source-quality JSON will
show whether the producer stopped finding the primary/secondary target or render
stopped consuming the fact.

The same negative-boundary test now exists for copper display-layout comments.
After source-quality has found the copper bitmap layout, a test mutator removes
`platform_semantic_uses` before rendering. Render may still format the copper
words, but it must not rediscover the high-level display layout from bytes:

```c
M68K_C_ASSERT(strstr(source, "display layout 2 bitmap planes") == NULL);
M68K_C_ASSERT(strlen(source) != 0U);
```

### Implemented Slice: OS Call Input Notes

The same ownership rule now covers Amiga OS call input comments. Previously the
render lookup pass walked backward from a recovered OS call and attached
comments directly:

```asm
    move.l  #$10000,-(a7)     ; KNOWN: arg +8 attributes
    pea.l   buffer            ; KNOWN: arg +4 byteSize
    jsr     local_allocmem_wrapper
```

That was analysis inside rendering. The renderer was deciding that the previous
stack push represented a documented call input. Source-quality now owns that
decision:

```text
recovered_platform_call at call site
  -> resolve documented vector inputs from the call symbol or wrapper note
  -> scan accepted setup instructions immediately before the call
  -> direct/vector call:
       allow stack pushes and caller-stack register loads
     local wrapper dispatch:
       allow stack pushes only
     local helper dispatch:
       do not infer caller arguments from the helper's internal OS call
  -> export M68kPlatformSemanticUseIR(
       kind=platform_call_input,
       offset=setup instruction offset,
       note_text="KNOWN: arg +N ...")
  -> renderer appends note_text only
```

The wrapper distinction is important. This caller-side register load is not an
argument setup for the wrapper call:

```asm
    move.l  $0008(a7),d1      ; no KNOWN comment
    move.l  #$10000,-(a7)     ; KNOWN: arg +8 attributes
    pea.l   $0060.w           ; KNOWN: arg +4 byteSize
    jsr     local_allocmem_wrapper
```

Inside the wrapper, the same register load shape can be real call input setup
because the immediate call is the direct `_LVOAllocMem(a6)` call:

```asm
local_allocmem_wrapper:
    movem.l $0008(a7),d0-d1   ; KNOWN: arg +4 byteSize | KNOWN: arg +8 attributes
    jsr     _LVOAllocMem(a6)
    rts
```

Local helpers are stricter than wrappers. A helper that performs extra work
before or after an OS vector proves that the helper itself uses the OS API, not
that every caller stack push maps to that API's documented inputs. Analysis now
records such calls with a distinct `LOCAL_HELPER_SYMBOL` note kind and
source-quality skips caller argument comments for that note kind:

```text
caller:
  jsr helper_that_may_call_allocmem

helper:
  tst.l d0
  beq.s done
  jsr _LVOAllocMem(a6)
done:
  rts

result:
  recovered helper/API fact exists
  no platform_call_input semantic-use is attached to the caller
```

The focused fixture asserts both rendered source and analysis JSON:

```c
M68K_C_ASSERT(strstr(source,
  "\tpea.l $0060.w\t; KNOWN: arg +4 byteSize") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"kind_name\":\"platform_call_input\"") != NULL);
M68K_C_ASSERT(strstr(analysis_json,
  "\"note_text\":\"KNOWN: arg +8 attributes") != NULL);
```

The old render-owned `render_lookup_add_call_setup_comments_for_vector` path was
deleted. The lingering `render_lookup_infer_amiga_call_input_comments` name was
also retired after inspection showed the path no longer emitted comments. The
render boundary for call-input comments is pinned:

```text
render_platform_call_input_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> the setup instruction still renders
  -> "KNOWN: arg +8 funcOffset long" does not appear
```

This keeps documented API argument comments analysis-owned. The renderer may
append a note already exported by source-quality; it may not walk recovered API
calls and reconstruct the comment by itself.

The later renderer-owned API string/text-buffer span pass was removed as well:
source-quality now owns both `api_string_pointer` and `api_text_buffer`
structured-data facts, while render lookup only imports and formats them.

### Implemented Slice: Stack Cleanup Notes

Atari GEMDOS stack-cleanup comments now use the same analysis-owned route.
Earlier, source analysis recovered the cleanup call, but render still walked
`recovered_platform_calls` and constructed the comment itself:

```asm
    addq.l #2,a7    ; KNOWN: stack cleanup for c_rawcin pop 2
```

That was not deciding whether the instruction was a cleanup, but it still kept
the durable explanation out of source-quality JSON. The analysis pass now emits
an explicit semantic use:

```text
trap #1 c_rawcin
  -> recovered_platform_call(note_kind=stack_cleanup)
  -> platform_semantic_use(kind=platform_stack_cleanup,
       offset=cleanup instruction offset,
       note_text="KNOWN: stack cleanup for c_rawcin pop 2")
  -> renderer appends note_text only
```

The render-owned stack-cleanup formatter was deleted. The focused fixture
asserts both the pre-render semantic-use record and the unchanged rendered
comment, so a future failure shows whether analysis stopped publishing the fact
or render stopped consuming it.

The render boundary is now pinned:

```text
render_platform_stack_cleanup_comment_requires_platform_semantic_use
  -> removes platform_semantic_uses before render
  -> the cleanup instruction still renders
  -> "KNOWN: stack cleanup for c_rawcin pop 2" does not appear
```

This keeps recovered platform-call metadata as input to source-quality, not a
second renderer-side source of inline comments.

### Implemented Slice: Runtime Sink Pointer Notes

Runtime sink comments now follow the same rule. Previously render inspected the
instruction destination, resolved the Amiga hardware register, looked for an
external runtime-address ref, chose a role, and constructed the inline comment:

```asm
    move.l #disk_buffer_00067D00,_custom+dskpt.l ; disk_buffer pointer $00067D00
```

That was source-quality analysis in the renderer. The C source-quality pass now
publishes the explanation as a semantic use:

```text
hardware write observation to _custom+dskpt
  + runtime-address ref $00067D00 at the same instruction
  -> platform_semantic_use(kind=runtime_sink_pointer,
       role_flags=disk_buffer,
       note_text="disk_buffer pointer $00067D00")
  -> renderer appends note_text only
```

The producer has two lanes because the source evidence has two shapes:

```text
absolute hardware observation
  move.l #$00067D00,_custom+dskpt.l
  -> sink address is present in the address observation

hardware-base register state
  lea.l  _custom.l,a5
  move.l a0,bltapt(a5)
  -> source-quality tracks a5 as _custom
  -> sink address is base(_custom)+$50
```

Both lanes use the same note formatter. Full long writes to runtime-address
sink registers get pointer notes. Word writes to pointer halves such as
`bplpt+$02(a0)` do not get generic pointer notes; those need high/low pair proof
from the copper/list or platform-specific path.

The renderer-side fallback used to print an external address suffix for some
in-image zero labels:

```asm
    move.l #loc_3_00000000,_custom+aud0+ac_ptr.l ; sound_sample pointer $00000000
```

The source-quality fact now keeps the role but avoids pretending that a normal
source label is an external runtime address:

```asm
    move.l #loc_3_00000000,_custom+aud0+ac_ptr.l ; sound_sample pointer
```

The renderer-side runtime-sink comment scanner and its role fallback were
deleted. Focused coverage asserts both the rendered comment and the exported
`runtime_sink_pointer` JSON record, so the pipeline can distinguish producer
failure from render consumption failure.

The in-image runtime-sink operand label now follows the same boundary. Earlier
render resolved the hardware destination, checked whether the immediate runtime
address mapped back into the source image, and rewrote the source operand:

```asm
    move.l  #loc_0_00000014,_custom+aud0+ac_ptr.l ; sound_sample pointer
```

That was a semantic decision in the renderer. Source-quality now attaches the
source target to the same `runtime_sink_pointer` semantic use:

```text
runtime-address ref at sink write
  + ref has source target section/offset
  + source operand is the immediate runtime address
  -> platform_semantic_use(kind=runtime_sink_pointer,
       operand_index=source_operand,
       target_section_index=...,
       target_offset=...)
  -> renderer formats that target as the current source/runtime label
```

The renderer may still choose the textual label spelling, because `loc_*` versus
storage/runtime spelling is render support. It no longer discovers that the
operand is a sink pointer or maps the immediate back into source bytes. The old
`attach_amiga_runtime_sink_immediate_symbols()` scan was deleted.

External runtime sink operands use the same semantic-use record instead of a
renderer-only role scan. Earlier render inspected runtime refs, resolved the
hardware sink role, coined a symbol, declared an `EQU`, and rewrote the
immediate:

```asm
disk_buffer_00067D00 EQU $67D00

    move.l  #disk_buffer_00067D00,_custom+dskpt.l ; disk_buffer pointer $00067D00
```

Source-quality now publishes the full fact needed by render:

```text
runtime-address ref at sink write
  + ref has no source target
  + hardware sink role is disk_buffer
  + source operand is the immediate runtime address
  -> platform_semantic_use(kind=runtime_sink_pointer,
       operand_index=source_operand,
       operand_expr="disk_buffer_00067D00",
       runtime_address=$00067D00)
  -> renderer declares operand_expr EQU runtime_address
  -> renderer attaches operand_expr to the operand
```

This keeps the role decision in source-quality. Render still owns only textual
declaration and operand formatting.

The same pass also covers the producer form that originally depended on a local
renderer scan:

```asm
bitmap_00060000 EQU $60000

    move.l  #bitmap_00060000,d0
    move.w  d0,$0006(a0)
    move.l  #bitmap_00060000,abs_0_00000130.l
```

The rule is deliberately narrow:

```text
accepted instruction
  + one operand stores/addresses materialized local runtime storage
  + another immediate equals a runtime address already proven as a sink role
  + that immediate operand does not already have a materialized source target
  -> platform_semantic_use(kind=runtime_sink_pointer,
       operand_index=immediate_operand,
       operand_expr="bitmap_00060000",
       runtime_address=$00060000)
  -> expected_symbol_access(producer=runtime_sink_pointer_operand)
```

This is not address-shaped-number promotion. The immediate only becomes a
symbol when an existing runtime-address ref has already proved a structured
sink role such as `bitmap` or `disk_buffer`. If the immediate points back into
current materialized source, the source-target label wins and no runtime sink
operand expression is installed. Focused C tests now assert both render output
and exported source-analysis JSON for `disk_buffer_00067D00` and
`bitmap_00060000`.

The corpus follow-through exposed two precedence rules that are part of the
feature, not target exceptions:

```text
same operand/address has a stronger semantic operand expression
  -> generic absolute-address observation does not also require an equate

same operand/address maps to materialized source storage
  -> materialized label/data ownership wins
  -> no external runtime sink equate is coined
```

This is why Midwinter II should render `loc_0_000351C2.l` for an in-image
target and only keep a structured sink comment, while Conqueror should not
require both `disk_buffer_00060000` and a generic `absolute_slot_00060000` for
the same operand. After applying these rules, the full rendered-source
round-trip corpus has zero source-quality failures, including Damocles Tetragon
02.

With that fact in place, the old renderer helper that searched candidates for
local runtime storage and coined external runtime-address symbols was deleted.
Render consumes `platform_semantic_use.operand_expr`; it no longer decides that
an immediate is a bitmap/disk-buffer pointer by scanning runtime refs itself.

The remaining generic runtime-address operand formatter is now guarded by the
same boundary. When source-analysis is present, runtime sink operands may only
get role-named symbols such as `disk_buffer_00067D00` from
`platform_semantic_use(kind=runtime_sink_pointer)`:

```text
source_analysis section exists
  + runtime-address ref has sink role
  + no runtime_sink_pointer operand_expr/target fact survived
  -> renderer leaves the raw numeric operand
  -> post-render validation/debugging exposes the missing C fact

no source_analysis section exists
  -> legacy preview fallback may still format runtime sink role symbols
     for non-source diagnostic views
```

The focused regression mutates a valid source-analysis result by clearing the
semantic uses before render. The output deliberately falls back to raw numeric
source:

```asm
    move.l #$67D00,$00DFF020.l
```

and does not recreate `disk_buffer_00067D00`. That proves source-backed render
is no longer silently covering a missing runtime-sink semantic fact.

The analysis-side replacement is deliberately local. It may propagate a
role-named operand from an immediate register load only when the loaded register
feeds a nearby `runtime_sink_pointer` semantic use:

```text
movea.l #$77D00,a0
move.l  a0,bltapt(a5)       ; runtime_sink_pointer blitter_source

producer load -> register value -> sink use
```

It may not scan the whole section for "some other sink used the same value" and
then rename every matching immediate. Same-value coincidence is weak evidence:

```asm
    move.l #disk_buffer_00067D00,_custom+dskpt.l
    move.l #$67D00,d0
```

The first operand is sink-proven. The second is only numerically equal, so it
stays numeric unless analysis can prove a real consumer.

The later label-only variant of the same mistake was also deleted:

```c
render_lookup_infer_amiga_runtime_sink_immediate_refs(...)
```

That pass decoded accepted instructions during render lookup, resolved Amiga
hardware sink destinations, mapped the immediate runtime value back into source
storage, and called `render_lookup_mark_label()`. It no longer had visible
ownership after source-quality started publishing `runtime_sink_pointer`
semantic uses, target offsets, operand expressions, and expected symbol
accesses. Corpus round-trip stayed content-exact after removal, proving the
durable C facts now carry the behavior rather than the render cache.

Runtime structured data now follows the same rule. The old render lookup path
used runtime sink refs to create copper-list and sound-sample structured data,
then scanned copper rows to invent bitmap runtime refs:

```text
render_lookup_infer_platform_runtime_structured_data()
  runtime ref -> COP1LC/COP2LC -> copper list item
  copper bitmap pointer rows -> bitmap runtime refs
  runtime ref -> AUDxLC + nearby AUDxLEN -> sound sample item
```

That analysis now belongs to source-quality:

```text
source-analysis runtime refs
  -> copper-list / sound-sample structured data items
  -> copper bitmap pointer rows -> bitmap base runtime refs
  -> accepted code scan -> bitmap-memory semantic-use notes
  -> renderer consumes structured data and notes
```

The renderability condition still matters. Policy/raw/nested copper spans that
render as bytes may still prove bitmap base ranges and list-level semantic
notes, but they must not create word-row symbol obligations that the source
renderer cannot satisfy.

Remaining platform-comment work is now limited to any other renderer helpers
that still describe platform meaning while formatting data. Display-layout,
display-setup, bitmap-memory, palette upload, runtime sink pointer, copper
runtime-pointer expressions, and runtime structured data are C-owned. Once a
comment family is migrated, the corresponding renderer fallback must be
deleted, not left as a second source of truth.

The copper runtime-pointer expression-symbol case now follows the same
ownership rule. Source-quality recognizes bitmap pointer word pairs inside
structured copper lists and publishes both the operand expression fact and the
matching expected symbol access for each emitted word:

```asm
    dc.w bplpt,bitmap_12345678_hi     ; bitmap pointer $12345678
    dc.w bplpt+$02,bitmap_12345678_lo
```

```text
copper-list structured data item
  + copper move targets a runtime-address sink such as bplpt
  + adjacent high/low rows prove the same pointer
  + the containing copper list can render as structured word rows
  -> platform_semantic_use(kind=copper_row,
       offset=high row,
       operand_index=none/data-row,
       operand_expr="bitmap_12345678_hi",
       runtime_address=$12345678,
       role_flags=bitmap)
  -> platform_semantic_use(kind=copper_row,
       offset=low row,
       operand_index=none/data-row,
       operand_expr="bitmap_12345678_lo",
       runtime_address=$12345678,
       role_flags=bitmap)
  -> expected symbol access bitmap_12345678_hi at high row
  -> expected symbol access bitmap_12345678_lo at low row
  -> render consumes operand_expr; it does not parse the pair again
  -> renderer records rendered data-equate accesses for those rows
  -> post-render source-quality gate fails if either symbol disappears
```

The renderability condition is part of the obligation. If an enclosing copper
span is emitted as raw bytes because it is a byte-classified item, overlaps
accepted code, or contains a blocking nested structured boundary, source-quality
may still publish list-level semantic notes such as display layout, but it must
not require `bitmap_*_hi/lo` symbol accesses that the source renderer cannot
emit:

```asm
abs_0_000517FC:
    ; display layout 4 bitmap planes $00068000..$0006DDC0 step $1F40
    dc.b $2B,$01,$FF,$FE,$01,$00,$42,$00,...
```

Rendering still formats and declares the `EQU` expressions because that is text
emission support:

```asm
bitmap_12345678        EQU     $12345678
bitmap_12345678_hi     EQU     bitmap_12345678/$10000
bitmap_12345678_lo     EQU     bitmap_12345678-(bitmap_12345678_hi*$10000)
```

It no longer owns the semantic obligation or the pair recognizer. The focused
fixture `facts_v2_copper_bitmap_pointers_render_display_layout_comment` now
checks the four C-owned semantic uses, their `operand_expr` values in exported
analysis JSON, and the expected accesses with producer
`copper_runtime_pointer_word_symbol`; render evidence proves the source
actually used those expressions. The fixture also covers the Pandora shape
where a same-offset untyped bytes placeholder exists beside the row-emitting
copper-list item. Source-quality must choose the copper-list item for the
renderability proof, not let the placeholder suppress valid bitmap/sprite word
symbols.

Palette upload comments and palette table classification have been moved onto
the same C-owned semantic path. Source-quality detects the source palette table
and records the upload instruction as the table consumer:

```text
palette table item
  offset=$10
  size=64
  role=palette
  consumer=$0C
```

Source-quality then publishes the visible comment as a semantic use at the
consumer instruction:

```text
platform_semantic_use(kind=palette,
  offset=$0C,
  note_text="palette upload 32 colors",
  target_offset=$10)
```

Render consumes that note like other `platform_semantic_use` comments. The
renderer no longer decides that an instruction is a palette upload while
formatting source.

Relocation-backed pointer table classification has also moved to
source-quality. The old render-lookup pass scanned relocation records and
accepted-code bytes while building the formatting cache:

```text
render_lookup_infer_relocation_pointer_tables
  -> scan decoded sections
  -> find consecutive reloc32 entries outside accepted code
  -> create auto structured LONGS pointer table item
```

That was the wrong ownership boundary. Whether a relocated long run is a
pointer table is source-analysis meaning, not source formatting. The new flow
is:

```text
source-quality
  -> scan relocation facts plus accepted bytes
  -> require two or more consecutive reloc32 data entries
  -> require targets inside known target sections
  -> append structured_data_item(
       kind=LONGS,
       role=POINTER_TABLE,
       source_pattern=RELOCATION_POINTER_TABLE)

render setup
  -> import C-owned structured_data_items into the render lookup cache
  -> materialize long-table target labels
  -> format the table from the imported facts
```

The render import is deliberately a cache handoff, not new analysis:

```c
if (render_asm_source) {
    m68k_analysis_render_lookup_import_source_analysis_structured_data(
        &render_lookup, source_analysis);
    m68k_render_lookup_materialize_structured_long_table_target_labels(
        &render_lookup, &decode);
}
```

This keeps existing relocation pointer tables rendering exactly while deleting
the renderer-owned classifier. The focused fixtures
`facts_v2_relocation_backed_data_longs_auto_classify_pointer_table` and
`facts_v2_relocation_pointer_table_does_not_promote_callback_targets_without_control_use`
prove both halves: data relocations still become pointer tables, but callback
targets are not promoted as executable code without control-flow proof.

The implementation must also keep the evidence domain narrow. A first C-owned
version reproduced the old behavior by walking every possible section offset and
then searching all relocation facts for each four-byte span:

```text
for offset in section bytes:
  if exact relocation fact exists at offset:
    maybe extend pointer table
```

That is the right meaning but the wrong algorithm. The Search for the King web
listing caught it as a CDP timeout: analysis spent tens of seconds in source
quality before rendering could start. The fix is to iterate relocation facts as
the primary domain, sort them by source offset, and only then check accepted-code
bytes:

```text
reloc32 facts for section
  -> sort by source offset
  -> skip duplicate-offset relocations
  -> skip entries overlapping accepted code
  -> group offsets start, start+4, start+8...
  -> emit pointer table only for runs of at least two longs
```

This is a source-quality rule for the rest of the proposal: analysis that is
driven by sparse evidence must iterate the sparse evidence directly. Whole-image
walks are valid only when the bytes themselves are the evidence, such as string
or raw data classification.

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

The first completed table-reference sub-slice moves PC-relative indexed scalar
lookup tables out of render lookup. The source-quality producer now owns:

```text
consumer offset
table start and span
entry kind: byte/word/long
source pattern
index register when proven
loop-limit entry-count proof when proven
```

The next table-reference sub-slice adds source-quality ownership for indexed
word dispatch and keyed-long relative dispatch tables. The C producer now
recognizes these consumer shapes:

```asm
    move.w table(pc,d0.w),d0
    jmp    table(pc,d0.w)

    adda.w (table,a0,d1.w),a1
    jmp    (a1)

    move.l (a0)+,d0
    swap   d0
    jmp    table(pc,d0.w)
```

It exports:

```text
source_pattern: indexed_word_dispatch | keyed_long_relative_dispatch
consumer section/offset
index register kind/index
target register kind/index when applicable
target base section/offset
relative code-dispatch table descriptor
entry targets and data references
mask/compare/loop index-domain proof when proven
```

The dispatch closure now runs before source export in the facts-v2 source path:

```text
decode/accepted ranges/platform passes
  -> build source_analysis
  -> source-quality table closure
  -> render lookup imports the immutable dispatch structured_data_items
  -> source render consumes imported facts
```

That removes the temporary renderer-owned mirror for indexed/keyed dispatch
classification. `render_lookup_infer_indexed_word_dispatch_tables()` and its
keyed-long helper state were deleted. The renderer still owns formatting and
label materialization, but it no longer decides that these bytes are dispatch
tables.

The next completed table-reference sub-slice moves indexed local pointer tables
and indexed postincrement data-read tables into source-quality. These were
previously hidden in render lookup even though they describe source facts:

```asm
    lea.l pointer_table(pc),a0
    move.l $0(a0,d0.w),d1

pointer_table:
    dc.l target_0
    dc.l target_1
```

```asm
    lea.l word_table(pc),a0
    move.w (a0)+,d0
    move.w (a0)+,d1

word_table:
    dc.w $1122,$3344,$5566,$7788
```

The C producer now exports:

```text
source_pattern: indexed_local_pointer_read | postincrement_read_sequence
consumer section/offset
index register kind/index when indexed
target register kind/index when the load target is proven
table start and span
entry kind: word/long/pointer
```

Pointer-table target labels and short target strings are still materialized by
render lookup, but only after importing source-quality facts:

```text
source-quality owns table classification
  -> render lookup imports structured_data_items
  -> m68k_analysis_render_lookup_materialize_pointer_table_targets()
       adds renderable target labels/strings
  -> no render-side pointer/postincrement classifier remains
```

The focused regressions assert that these facts now live in
`source_analysis.structured_data_items` with their source pattern ids, not in
render auto-policy state:

```c
M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ
M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POSTINCREMENT_READ_SEQUENCE
```

The next completed table-reference sub-slice moves indexed local scalar tables
and word-offset target promotion into source-quality. These are the local-base
forms that read table data through an address register already proven to point
at accepted target bytes:

```asm
    lea.l table(pc),a0
    adda.w $0(a0,d1.w),a1

table:
    dc.w target_0-base
    dc.w target_1-base
```

```asm
    lea.l table(pc),a0
    move.w $0(a0,d1.w),d0
    adda.w d0,a1
```

The C producer now exports:

```text
source_pattern: indexed_local_scalar_read
consumer section/offset
table start and span
entry kind: word
index register kind/index when proven
target base section/offset only when durable evidence proves target meaning
```

Target-base promotion is deliberately wary. A direct indexed relative address
materialization may render symbolically when the destination address register
does not feed a later indirect jump/call:

```text
adda.w table(base,index),a1
  + a1 later used as data/storage pointer
  -> table entries may be relative data/string targets

adda.w table(base,index),a1
  + jmp (a1) or jsr (a1)
  -> dispatch classifier owns target proof
  -> scalar classifier must not preclaim code targets
```

Word-offset string/data targets are also source-quality facts now. The table
target base is attached only when there is enough target evidence, such as two
bounded text-shaped entries or existing durable labels/ranges:

```text
relative word table
  + at least two bounded text targets
  -> table source_pattern=word_offset_string_table
  -> target strings/raw bounded data become structured_data_items

relative word table
  + one address-looking value only
  -> keep numeric/review evidence
  -> no invented symbol obligation
```

The evidence count is distinct-target based. A thousand copies of the same
zero displacement do not prove a thousand targets:

```text
base + 0, base + 0, base + 0, ...
  -> one distinct target
  -> not enough proof to force symbolic relative entries

base + 0, base + 8, base + 24, ...
  -> multiple distinct targets
  -> target-bearing table evidence can be durable
```

Direct PC-indexed long dispatch tables are also C-owned facts. The analysis
keeps their dispatch kind separate from the display role:

```asm
    movea.l table(pc,d0.w),a0
    jmp     (a0)

table:
    dc.l target_0
    dc.l target_1
```

```text
source_pattern: pc_relative_indexed_indirect_dispatch
semantic role: pointer_table
table kind: absolute_code_dispatch
```

That means the renderer may show the data as a pointer table while validation
and table-entry records still know it is control-flow evidence.

This enforces the broader address rule: weak address-shaped numerics are review
signals, not conversion proof. Symbolic entries require consumer evidence,
bounded target evidence, or existing analysis facts that make the target useful
to a reverser.

The completion invariant for this sub-slice is now:

```text
source-quality owns table classification
  -> render lookup imports structured_data_items before source render
  -> biased leading entries, zero-guarded entries, keyed-long entries, and
     address-indexed entries render from imported facts
  -> pointer tables and postincrement read sequences render from imported facts
  -> indexed local scalar and word-offset string/data tables render from imported facts
  -> direct PC-indexed long dispatch tables keep pointer-table display semantics
     without losing code-dispatch table metadata
  -> weaker scalar observations cannot overwrite stronger dispatch facts
  -> no render-side dispatch, pointer-table, scalar-table, or postincrement
     classifier is needed
```

This matters for biased dispatch tables. A leading entry can first be observed
as a plain PC-relative indexed read and later proven to be part of the
dispatch table:

```asm
loc_0_0000000A:
    dc.w loc_0_00000016-loc_0_0000000C ; lookup_table
loc_0_0000000C:
    dc.w loc_0_0000002E-loc_0_0000000C ; lookup_table
```

Same-range/same-role updates therefore rank source patterns. Plain scalar
observations may fill an unknown item, but they must not downgrade a proven
`indexed_word_dispatch`, `pc_relative_indexed_indirect_dispatch`, or
`keyed_long_relative_dispatch` item back to numeric scalar data.

The migration also removes the old render-side habit of creating zero-size
auto structured-data anchors. A label should survive only when analysis can
explain a visible access, a structural boundary, or an object/platform origin:

```asm
    dc.l $0004CACA        ; numeric table value only
; no abs_0_0004CACA label unless table-entry analysis proves that value is a
; target worth naming and rendering symbolically.
```

The Bloodwych table at source offset `$120A` exposed the same rule from the
other direction. Source-quality correctly proved a five-entry relative word
dispatch table, but render still owned an earlier two-byte auto guess at the
same start:

```asm
    lea.l abs_0_0000166A.l,a1
    lea.l abs_0_000015AE.l,a0
    adda.w $0(a0,d1.w),a1
    jmp (a1)

abs_0_000015AE:
    dc.w $0000          ; stale two-byte guess
    dc.b $FF,$6C,$00,$F0,$FF,$4E,$FF,$FA
```

The correct rendered result consumes the imported C table fact:

```asm
abs_0_000015AE:
    dc.w abs_0_0000166A-abs_0_0000166A ; lookup_table
    dc.w abs_0_000015D6-abs_0_0000166A
    dc.w abs_0_0000175A-abs_0_0000166A
    dc.w abs_0_000015B8-abs_0_0000166A
    dc.w abs_0_00001664-abs_0_0000166A
```

That required two general fixes:

```text
address observation raw runtime value
  -> resolved source/storage target
  -> table base and entries use source offsets, not raw runtime literals

same-start render auto item
  -> source-analysis import may widen/replace the auto item
  -> policy/manual ownership still wins
  -> source render sees the C-owned table extent
```

The isolated regression is
`render_lookup_import_source_analysis_widens_same_start_auto_item`. The target
confirmation is Bloodwych rendered-source round-trip: source render is now
content-exact; the remaining status is the existing container-shape mismatch,
not a source-quality refusal.

Pandora exposed the companion render invariant. A relative table expression may
only name labels that can be emitted as definitions:

```asm
abs_0_0001A6DC:
    dc.w abs_0_0001A25D-abs_0_0001A25C ; valid: both labels are renderable
    dc.w abs_0_0001A25E-abs_0_0001A25C ; invalid: target is an interior byte
```

The second line assembles only if `abs_0_0001A25E` is defined. If render
discovers that backward label after it has already passed the target offset,
the source is invalid. The rule is therefore:

```text
relative table entry target/base is forward
  -> render may materialize the label before reaching it

relative table entry target/base is backward
  -> label must already be renderable
  -> otherwise keep the raw numeric table value
```

This is formatting support, not semantic discovery. C analysis still owns the
table fact; render merely refuses a symbolic spelling that would create an
undefined label. The isolated regression is
`facts_v2_word_lookup_table_keeps_unrenderable_backward_target_raw`. Pandora's
focused update-render round-trip is exact after the fix.

### Implemented Slice: Pointer-String Table Targets

Pointer-table target string promotion had the same wrong ownership boundary.
Render lookup previously walked pointer-table targets and converted any small
printable NUL-terminated target into a string:

```text
render sees pointer table entry -> target bytes look like "XOa\0"
  -> render creates pointer_string_table item
  -> source displays a false string
```

That was unsafe because a pointer target can be data, code, a callback stub, or
plain storage. Printable bytes are review evidence, not conversion proof.

The implemented rule is now analysis-owned:

```text
explicit pointer_string_table policy/table fact
  -> promote valid target strings

ordinary pointer table + dense string-pool evidence
  -> promote only dense target strings

relocation-backed one-entry pointer + dense string-pool evidence
  -> promote that target string

isolated pointer target with printable bytes
  -> keep bytes/labels numeric, do not invent a string
```

The dense-pool check is deliberately about neighboring string structure, not
the spelling of a single target:

```text
pointer -> "JAN\0FEB\0MAR\0"
  -> dense C-string pool
  -> pointer_string_table structured-data items + table data references

pointer -> "XOa\0\x01h..."
  -> isolated printable prefix inside instruction-shaped bytes
  -> no string item
```

Source-quality now creates the `pointer_string_table` target items and the
table-entry data references. Render lookup still materializes pointer target
labels, but it no longer classifies pointer targets as strings.

The focused fixtures are:

```text
facts_v2_pointer_table_targets_promote_short_strings
  -> explicit pointer_string_table policy still works

facts_v2_pointer_table_targets_infer_dense_short_string_pool
  -> dense short C-string pool promotes without explicit policy tagging

facts_v2_pointer_table_targets_reject_isolated_printable_code_prefix
  -> relocation-backed isolated "XOa\0" does not become a string

facts_v2_relocation_pointer_target_promotes_single_dense_short_string
  -> one-entry relocation pointer can promote when the target is in a dense pool
```

The corpus update confirms the intended split:

```text
Damocles Tetragon 02
  "2<\0" false pointer-target string removed

Midwinter II
  false strings such as "XOa\0", "0-\0", "1|\0", and "Bh\0" removed
  dense real short strings such as df0: and Ship preserved

Search for the King
  isolated "WW\0" false string removed
```

Rendered-source round-trip after the update remains clean:

```json
{"targets":54,"failures":0,"rendered_source_full_file_exact":38,
 "rendered_source_content_exact_only":15,"unsupported":1}
```

This slice also reinforces the larger proposal rule: address-looking or
printable-looking data is not enough to upgrade source. The framework needs
proven table/string structure, and when validation or render diffs expose a
false conversion the follow-through is to fix the producer, not to whitelist the
target.

### Implemented Slice: Generic String-Table Sequence Ownership

Generic adjacent string-table promotion had the same wrong boundary. Render
lookup previously scanned unowned bytes and promoted any run of three short
printable terminated spans:

```text
render sees "MISS",$ff,"HITS",$ff,"RUNS",$ff
  -> render creates string_table_sequence items
  -> source_analysis later inherits renderer-owned facts
```

That made source quality depend on renderer discovery. The implemented rule is
now C-owned:

```text
source-quality sees a dense adjacent string sequence
  + at least three compatible entries
  + no accepted-code byte overlap
  + no label/structured-data interior conflict
  + existing weak string items are compatible
  -> emit string_table_sequence structured-data items

only one or two adjacent printable spans
  -> review/data evidence
  -> do not promote
```

Line-terminated rows are part of the same dense sequence proof. A table can mix
plain NUL/FF terminated rows and LF/CR terminated rows:

```asm
    dc.b "Text: ",$00
    dc.b "Data: ",$00
    dc.b "BSS : ",$00
    dc.b "Current Breakpoints:",$0A
    dc.b $00
```

The source-quality scanner owns the full row extent, including line-break bytes,
before render formats the item. Render can still decide the textual spelling of
the already-owned item, but it no longer creates the durable
`string_table_sequence` fact.

The focused fixtures are:

```text
facts_v2_adjacent_short_ascii_spans_auto_classify_string_sequence
  -> three short FF-terminated strings become C-owned string_table_sequence

facts_v2_two_adjacent_short_ascii_spans_do_not_classify_string_sequence
  -> two printable spans stay raw data/review evidence

facts_v2_rank_string_sequence_renders_starglider_examples
  -> Starglider-style adjacent rank strings stay readable

facts_v2_table_context_promotes_plain_entry_without_space
  -> existing weak text items can be upgraded together by table context

facts_v2_adjacent_line_terminated_ascii_sequence_promotes_lf_rows
  -> LF-terminated rows in a dense table are owned by source quality

facts_v2_line_terminated_sequence_does_not_split_format_placeholder
  -> format-placeholder text is not split just because it is printable
```

The render lookup fallback that performed dense string-sequence discovery has
been deleted. Generic single-string detection is covered by the next slice;
remaining render-side generic data-span detection is now a visible cleanup lane,
not the desired long-term ownership model.

### Implemented Slice: Generic Single-String Ownership

Single terminated and bounded text spans had the same renderer-owned shape:

```text
render lookup sees printable bytes
  -> render creates terminated_text or bounded_text structured data
  -> source_analysis inherits a renderer decision
```

That path has been moved into source-quality analysis. The C scanner now owns
the generic single-string proof:

```text
candidate start
  + quoted-string-safe payload
  + NUL/$FF terminator or label-bounded readable span
  + no relocation/interior label/range/accepted-code overlap
  + no length-prefixed record shape
  -> structured_data_item(kind=STRING, source_pattern=terminated_text|bounded_text)
```

For code sections, weak printable bytes are still not code. The scanner uses
the accepted-code map as the hard boundary: bytes already accepted as
instructions block generic text, while unaccepted code-section bytes may be
classified as data text if the normal string proof is present. The old
nearby-terminal-code guard is also analysis-owned now, so an unlabeled printable
run immediately after a function epilogue is not promoted just because its bytes
happen to decode as text.

Bounded text still needs a visible boundary because it has no terminator:

```asm
    bra.b after_title
title:
    dc.b " TETRAGON "
after_title:
    rts
```

The source-quality result is:

```text
source_analysis.structured_data_items:
  section=0 offset=2 size=10 kind=string source_pattern=bounded_text
```

Render lookup no longer runs `render_lookup_infer_data_strings()`. It imports
the C-owned item and formats it. The focused analysis-only regressions are:

```text
facts_v2_analysis_collects_terminated_text_without_source_render
  -> C source_analysis owns terminated_text before render

facts_v2_analysis_collects_bounded_text_without_source_render
  -> C source_analysis owns bounded_text before render
```

The Damocles Tetragon 02 planet-name span is the target-scale smoke test for
this rule. It sits in a code-bearing raw payload but has no accepted-code
overlap:

```text
offset=$71DC size=249 source_pattern=terminated_text
```

That means the source-quality pass owns the string before render lookup imports
it; render lookup no longer needs a private fallback to keep the assembler
readable.

### Implemented Slice: Render Auto Producer Cleanup

After the generic string producers moved to C, render lookup still carried dead
helpers named like producers:

```text
render_lookup_add_auto_structured_data_item()
render_lookup_set_auto_structured_data_item_target()
render_lookup_set_auto_structured_data_item_source_pattern()
```

Those helpers had no remaining callers. Keeping them would make the ownership
boundary look ambiguous and invite future render-side semantic producers. They
have been removed. Render lookup still stores imported source-analysis items in
its auto-item arrays because that is rendering support, not analysis:

```text
C source_quality emits structured_data_item
  -> render_lookup_import_source_analysis_structured_data_item()
  -> render owns formatting/range lookup only
```

The cleanup is intentionally source-neutral: C unit tests pass and the
read-only rendered-source round-trip reports the same exact/content-exact target
set with no new rendered-source churn.

### Implemented Slice: Render Auto Append-Back Removal

The next cleanup removes the final append-back path:

```text
render lookup AUTO structured-data ownership
  -> m68k_analysis_render_lookup_append_auto_policy()
  -> source_analysis.structured_data_items
```

That path made render lookup a latent analysis producer even after the concrete
text and table producers had moved into source-quality. It also made the
pipeline order harder to reason about: a fact could appear only because a render
preview ran first.

The source-quality boundary is now one-way:

```text
source-quality creates structured_data_item facts
  -> render lookup imports those facts for ownership and formatting
  -> render evidence records what was emitted
  -> source-quality validates emitted evidence
```

Render evidence validation remains post-render because it compares expected
analysis obligations with the actual source text emitted by the renderer. It is
not an analysis producer and does not mutate source analysis with new semantic
facts.

### Implemented Slice: Mac OS Symbol String Ownership

Mac OS high-bit symbol records had the same ownership bug as the generic text
cases:

```text
render lookup sees $87,"GETRSRC",0,0
  -> render creates macos_symbol_string structured data
  -> source_analysis inherits a renderer decision
```

That is backwards. The platform backend is now copied into the C
`M68kSourceAnalysisIR`, and source-quality analysis owns the platform-specific
structured-data decision:

```c
typedef struct M68kSourceAnalysisIR {
  M68kPlatformFileKind file_kind;
  uint8_t platform_backend_kind;
  uint8_t reserved0[3];
  M68kAnalysisPolicy policy;
  ...
} M68kSourceAnalysisIR;
```

The C scanner runs only for the Mac OS backend:

```text
platform_backend_kind == MACOS
  + high bit length byte
  + quoted-string-safe payload
  + no relocation/label/range/accepted-code overlap
  + optional NUL padding
  -> structured_data_item(
       kind=STRING,
       roles=string|length_prefixed_string|macos_symbol_string,
       source_pattern=macos_symbol_record)
```

Render lookup no longer has a Mac symbol recognizer. It imports the C-owned
structured-data item and formats it:

```text
C source quality proves macos_symbol_record
  -> render lookup imports the item
  -> renderer prints bytes/text for that item
  -> post-render source_analysis still shows the C-owned fact
```

The focused regression is analysis-only, so it cannot pass because render
lookup reintroduced the decision:

```text
facts_v2_analysis_collects_macos_symbol_string_without_source_render
  -> source_analysis has one MACOS_SYMBOL_STRING item at offset 0
  -> source_pattern is MACOS_SYMBOL_RECORD
```

### Implemented Slice: Multiline Text Ownership

Multiline text promotion had the same renderer-owned shape:

```text
render sees printable bytes plus CR/LF layout
  -> render creates multiline_text structured data
  -> source_analysis later inherits the renderer decision
```

That is now C-owned source-quality work. The analysis pass scans for multiline
text after platform/API string facts and before generic string-table sequence
promotion:

```c
SOURCE_QUALITY_CHECK_OK(append_multiline_string_items(
  source_analysis, decode, facts, accepted_bytes));
SOURCE_QUALITY_CHECK_OK(append_string_table_sequence_items(
  source_analysis, decode, accepted_bytes));
```

The scanner accepts only text-shaped spans with enough structure:

```text
start looks like text or CR/LF lead-in
  + at least two text lines
  + at least two line breaks
  + enough alphabetic content
  + no accepted-code byte overlap
  + no relocation/interior hard boundary
  -> multiline_text structured-data item
```

Weak renderer-origin text can be upgraded by stronger C evidence:

```text
bounded_text at same start
terminated_text inside the candidate
control_string_stream inside the candidate
untyped bytes placeholder at same start
  -> refinable evidence
  -> replaced/contained by C multiline_text

policy-owned structured item or explicit interior boundary
  -> stop or reject the multiline span
```

An interior label is a hard boundary because it may be a table target or other
visible access point. The scanner may stop a multiline span before such a label
once the preceding span already has enough text shape, but it must not absorb the
label into a larger text item.

Render lookup no longer performs multiline text discovery. When C imports a
stronger multiline item, render lookup suppresses contained weak auto text
ownership so stale `terminated_text`/`bounded_text`/`control_string_stream`
guesses cannot reappear after render:

```text
source_analysis multiline_text $0000..$0037
render auto terminated_text $001F..$0037
render policy control_string_stream $0000..$0020
  -> disable contained weak auto range
  -> disable contained weak policy range
  -> render sees only multiline_text
```

The render layer still owns formatting. For C-owned multiline text it formats
the accepted item as line-based `dc.b` rows and ignores speculative unnamed
labels or generic string-span boundaries inside the same item:

```asm
credits_text:
    dc.b "   CREATED BY: SHAHID AHMAD",$0D
    dc.b "   DAVID EASTMAN",$0D
    dc.b "PUBLISHED BY: FIREBIRD",$00
```

This keeps the ownership boundary clean:

```text
C source quality decides multiline_text exists
render lookup imports that fact and removes weaker guesses
render formats the fact without inventing a new semantic item
post-render source_analysis keeps the C-owned item
```

Focused fixtures:

```text
facts_v2_multiline_string_auto_classifies_crlf_text
facts_v2_labeled_printable_multiline_text_auto_classifies
facts_v2_printable_multiline_text_stops_at_existing_string
facts_v2_unlabeled_code_printable_multiline_text_is_not_multiline
render_lookup_import_source_analysis_suppresses_contained_weak_text
```

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
  -> indexes C-owned source-analysis summaries for decoded Mac CODE resources

amiga_reversing/disasm/macos_target_artifact.py
  -> no longer renders Python-computed source-quality comments
```

The wrappers are acceptable only while they display or index C-exported facts.
The removed Mac OS gate was different: it computed checklist values, semantic
closeout status, residual status, label/xref status, and claims/does-not-claim
text in Python. That model may have been useful for discussion, but it violated
the ownership rule. Source-quality meaning now belongs to C facts.

Completed migration:

```text
1. C source-quality explain exports source_analysis JSON.
2. Mac project payload removes macos_source_quality_gate_v1.
3. Mac project payload exposes c_source_analysis_summary_v1 rows only.
4. Mac target artifact source comments no longer render Python gate text.
5. Any missing Mac source-quality fact must be added in C, not re-derived in
   Python.
```

The first enabling step is now in place: the C source-quality explain API
exports full `source_analysis` JSON alongside the existing blocker explanation
packet:

```json
{
  "source_quality": {
    "source_quality_explanation_count": 0,
    "sections": []
  },
  "source_analysis": {
    "section_count": 1,
    "sections": [
      {
        "accepted_code_run_count": 1,
        "symbol_origin_count": 1
      }
    ]
  },
  "profile": {
    "generation": "facts_v2_source_quality_explain",
    "backend": "macos-code"
  }
}
```

Python can now read the C-owned code runs, symbol origins, diagnostics,
expected accesses, and platform facts from the same explain packet used by
source-export failure reporting. The Mac project payload consumes the same
listing-artifact analysis payload while the artifact is open:

```py
window, _window_profile = artifact.window_payload(start=0, count=total_rows)
source_analysis, _analysis_profile = artifact.analysis_payload()
```

It then publishes a compact index:

```json
{
  "source_analysis_summaries": [
    {
      "kind": "c_source_analysis_summary_v1",
      "authority": "c_source_analysis",
      "resource_id": 1,
      "section_count": 1,
      "source_quality_diagnostic_count": 0,
      "accepted_code_run_count": 1
    }
  ]
}
```

That index is not a verdict. It is a pointer to C-owned facts suitable for web
navigation and debugging. If we need semantic closeout status, label/xref
resolution status, residual status, or source-quality failures for Mac CODE,
those facts must be produced by the shared C analysis and validation layer.

The old Mac OS target-artifact source-comment renderer for that Python gate has
also been deleted. Generated Mac OS source already omits `; Source quality gate`
comments; keeping a dead renderer for Python-computed semantic closeout would
invite the wrong ownership boundary back into source export.

No platform gets an exception: Amiga, Atari, Mac OS, and raw targets all use the
same rule that source-quality meaning is produced by C.

## Fixture Matrix

Primary fixtures:

- Damocles Tetragon payload 2: in-image addresses, false `$42C00` run, absolute
  ranges, low-memory base/vector distinction, code-patch addends, lookup
  tables.
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
  address-looking literals are no longer promoted to `runtime_address_*`
  without a runtime-address fact proving runtime-domain identity
  writes to $000459BA and $000459C6 render as abs_0_000459B8+2 and
  abs_0_000459C4+2 only when source-quality proves accepted instruction anchors

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

Two discoverability gaps were found in the wrapping layer and closed without
moving ownership out of C:

```text
expected_symbol_accesses
  -> indexed from C source-analysis JSON
  -> first-class Python/web labels for kind, producer, targeted, and base lanes

platform_semantic_uses
  -> indexed and xref-backed as analysis:platform_semantic_use:*
  -> participates in target-pattern:source_quality_platform_semantics
  -> first-class Python/web labels for base, kind, and source lanes
```

Those labels are presentation only. The feature rows still come from C
source-analysis JSON via `src/scripts/target_usage_manifest.py`.

The web feature label helper now mirrors the Python corpus label helper for the
same C-owned platform-semantic lanes:

```js
analysis:platform_semantic_use_kind:bitmap_plane
  -> "Platform semantic use: bitmap plane"

analysis:platform_semantic_use_source:postincrement_read_sequence
  -> "Platform semantic use source: postincrement read sequence"
```

No web code derives platform semantics. It only names features that were already
emitted from `source_analysis.platform_semantic_uses`.

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
  in-image address identity, materialized code-patch addend obligations, and
  expected symbol access checks.
- Numeric operands that target C-owned in-image storage either render through
  the approved symbol or emit a source-quality diagnostic.
- `runtime_address_*` is used only when C analysis emits a runtime-address
  ref/range/sink fact proving runtime-domain identity. Plain address-looking
  literals stay numeric.
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

The table and text closure updates exposed expected target churn while
source-quality facts replaced renderer guesses. That churn is now mostly a
formatting question: render lookup imports C-owned tables and strings, and the
remaining stale boundary is the platform typed-flow analyzer family still
living in `m68k_analysis_render_lookup.c`. That is not a reason to keep platform
semantics in render lookup; it is evidence for the next cleanup: move the
producer-side Amiga typed-flow, recovered API-call, disk-read/runtime-copy, and
base-slot facts into an analysis/platform module, then leave render lookup as
formatting support only.

### Implemented Slice: Render Hardware Offset Lookup Uses Platform Facts

The renderer still had one duplicate Amiga hardware lookup path for base-relative
operands:

```text
known custom base in address register
  + displacement
  -> renderer directly searches hardware register/field/range tables
  -> renderer formats the symbol itself
```

That path is now fact-backed. Render import still prefers a
`platform_address_use` produced by source-quality analysis. The legacy fallback
used only when no source analysis is available now calls the platform facts
helper instead of reimplementing base-id/offset lookup in `m68k_render_ir.c`:

```c
base_symbol = platform_facts_v2_hardware_base_offset_symbol(
  M68K_PLATFORM_BACKEND_AMIGA_HUNK,
  state->address_hardware_base_id[base_reg],
  displacement,
  symbol_name,
  sizeof(symbol_name));
```

This does not make fallback rendering the desired ownership model. It narrows
the remaining fallback to formatting support through the same platform facts
API used by analysis, while keeping the source-analysis path authoritative when
facts are present.

### Implemented Slice: App-Base Hardware Exclusion Uses Platform Facts

The typed app-slot pass also had a smaller ownership leak. When deciding whether
an `a6` displacement should be treated as application storage, render lookup
directly searched Amiga hardware register tables to avoid misclassifying custom
chip registers:

```text
operand uses (disp,a6)
  -> if disp is a known CUSTOM offset, do not call it app storage
  -> otherwise, weak a6 fallback may classify it as app-base storage
```

That rule is still correct, but the hardware-address knowledge now lives behind
the platform facts API:

```c
platform_facts_v2_hardware_base_offset_known(
  M68K_PLATFORM_BACKEND_AMIGA_HUNK,
  AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
  displacement);
```

This is intentionally conservative. The app-slot pass may use the result as a
negative guard, but it does not get to learn hardware register table details or
invent a symbol from a numeric displacement. Positive hardware naming remains a
platform-address-use or platform-facts rendering concern.

### Implemented Slice: Typed Absolute Storage Rejects Hardware Owners Only

Typed-flow also had an absolute-storage path:

```text
store typed value to absolute address
load typed value from same absolute address
  -> propagate the type through that storage slot
```

That is valid for real program storage, including low-memory storage used by
some targets. The first attempted cleanup used the broad symbolic-owner helper
and failed existing low-memory fixtures because CPU-vector-range addresses such
as `$80` may still be application storage when the instruction shape does not
prove vector semantics. The correct rule is narrower:

```text
absolute address is hardware-owned
  -> do not track it as typed storage

absolute address merely looks like low-memory/vector space
  -> do not reject it here
  -> let address-use/range analysis decide whether vector semantics are proven
```

The platform facts API now exposes that distinction explicitly:

```c
platform_facts_v2_address_has_hardware_owner(platform, address)
platform_facts_v2_address_has_symbolic_owner(platform, address)
```

Typed absolute-storage tracking uses the hardware-owner predicate. The focused
regression stores an API-typed value through a hardware field address
`$00DFF0A4`, reloads it, and verifies the later `(a0)` access stays numeric
instead of becoming `MP_SIGBIT(a0)`. Existing `$80` absolute-slot tests continue
to pass, proving that low-memory storage was not accidentally folded into the
hardware guard.

### Implemented Slice: Copper Register Names Use Platform Facts

Copper-list rendering still had a direct hardware-table lookup for the register
word in each `dc.w register,value` pair:

```text
copper register word
  -> renderer searches CUSTOM register table
  -> renderer searches CUSTOM field table
  -> renderer searches CUSTOM range table
  -> renderer formats the symbol
```

That is formatting, but it was still a duplicated platform decision. The
symbol-name path now delegates to the same platform facts helper used by
analysis and other render fallback code:

```c
platform_facts_v2_hardware_base_offset_symbol(
  M68K_PLATFORM_BACKEND_AMIGA_HUNK,
  AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
  offset,
  buf,
  buf_size);
```

The renderer still copies the returned symbol into its caller buffer because the
facts helper may return either a static name such as `bplcon0` or a formatted
field/range expression such as `aud0+ac_len`.

### Implemented Slice: Copper Register Value Expressions Use Platform Facts

Copper-list value formatting had the same ownership leak in a different form:

```text
copper register word and value
  -> renderer finds CUSTOM register metadata
  -> renderer applies Amiga custom immediate/value-domain formatting
  -> renderer emits INTF_CLRALL, BEAMCON0_PAL, and similar symbols
```

That path now asks the platform facts layer for the value expression:

```c
platform_facts_v2_hardware_base_offset_value_expr(
  M68K_PLATFORM_BACKEND_AMIGA_HUNK,
  AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
  offset,
  value,
  buf,
  buf_size);
```

The renderer still decides whether a copper row is a move/wait/skip and still
prints the row. It no longer knows how to look up Amiga register value-domain
metadata. That keeps `INTF_CLRALL`, `DMAF_CLRALL`, `BEAMCON0_PAL`, and related
expressions behind the same platform facts API boundary as register names.

### Implemented Slice: Hardware Base Symbols Use Platform Facts

Renderer hardware-base formatting also had small direct Amiga lookups:

```text
state says register holds CUSTOM base id
  -> renderer asks Amiga metadata for `_custom`

literal/address operand is $00DFF000
  -> renderer asks Amiga metadata whether that is a hardware base
```

Those are formatting-support questions, not new semantic proof, but they still
duplicated platform metadata access in `m68k_render_ir.c`. The renderer now asks
platform facts for both forms:

```c
platform_facts_v2_hardware_base_symbol(platform, base_id);
platform_facts_v2_hardware_base_symbol_for_address(platform, address);
```

The rule remains conservative. Source analysis must still prove that an operand
is a hardware-base address use before the renderer attaches the symbol when
source analysis is present. The no-source-analysis fallback can still format
legacy preview output, but it no longer opens the Amiga hardware-base tables
itself.

### Implemented Slice: Dead Absolute Hardware Fallback Removed

Absolute hardware operand rendering had a stale fallback path after the
source-analysis lookup:

```text
absolute operand
  -> ask source analysis for a hardware-base or hardware-register use
  -> if no hardware-register use exists, continue
  -> otherwise, after the fact, try renderer-local hardware table lookup
```

The final renderer-local lookup could not run. If `source_analysis` was absent,
`source_analysis_platform_address_use_for_operand` returned `NULL` and the
function had already continued. If `source_analysis` was present, the fallback
was explicitly skipped before it could attach a symbol.

The dead fallback has been removed instead of being rewritten. That keeps the
ownership rule clear:

```text
absolute hardware symbol
  = source-analysis/platform-address-use fact
  -> rendered symbol

no fact
  -> no renderer-invented hardware symbol
```

This is a small cleanup, but it matters for proposal 033 because dormant
renderer-side semantic paths are the same class of problem as active renderer
guesses. They make future behaviour harder to reason about and can reintroduce
symbol promotion without the analysis evidence this proposal requires.

### Implemented Slice: Stack-Top Guard Uses Shared Symbolic-Owner Facts

The renderer has one intentionally narrow runtime-address symbol invention:
loading an absolute address into `a7` may render as a stack-top equate:

```asm
  lea.l stack_top_00080000.l,a7
  movea.l #stack_top_0007FFFC,a7
```

That is useful only when the literal has no stronger meaning. CPU vectors,
ExecBase, hardware registers, and other platform-owned addresses must not be
renamed as stack tops merely because they flow into `a7`.

Source-quality validation already used the shared ownership predicate:

```c
!platform_facts_v2_address_has_symbolic_owner(platform_kind, value)
```

Render now uses the same predicate instead of duplicating CPU-vector and Amiga
hardware table checks. The rule is therefore backend-aware:

```text
address has a platform/CPU symbolic owner
  -> keep the stronger owner, do not invent stack_top_*

address has no symbolic owner and is loaded into a7
  -> stack_top_* render is allowed
```

The focused fixture keeps the useful stack-top cases, rejects low vector address
`$00000004`, and also rejects Amiga hardware register `$00DFF09A` as a stack-top
candidate.

### Implemented Slice: Runtime Sink Role Lookup Uses Platform Facts

Runtime-address references can point at platform sink registers. On Amiga, those
include copper pointers, disk DMA pointers, blitter pointers, bitmap plane
pointers, sprite pointers, and audio sample pointers.

The renderer previously found external sink roles by walking Amiga hardware
register tables itself:

```text
runtime ref targets external address/offset
  -> renderer searches hardware register by CPU address
  -> renderer searches hardware range by CPU address
  -> renderer searches CUSTOM register by offset
  -> renderer searches CUSTOM range by offset
  -> renderer reads runtime_target_role from metadata
```

That is now a platform-facts responsibility. The important correction is that
the two forms stay separate. A CPU address is not treated as a CUSTOM-relative
offset merely because its numeric value happens to match one.

```c
platform_facts_v2_runtime_address_sink_data_class(
  M68K_PLATFORM_BACKEND_AMIGA_HUNK,
  0x00DFF020); /* "disk_buffer" */

platform_facts_v2_hardware_base_offset_runtime_address_sink_data_class(
  M68K_PLATFORM_BACKEND_AMIGA_HUNK,
  AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
  0x0020);    /* "disk_buffer" */
```

Render no longer knows how to search those Amiga register/range tables for this
case. It asks platform facts for the sink role, then formats the already-proven
runtime-address symbol or comment. The fixture covers both absolute and offset
forms through distinct APIs. It also proves that plain `$0020` is not accepted
by the address API, preventing in-image storage addresses such as `$0130` from
being accidentally reinterpreted as CUSTOM register offsets.

### Implemented Slice: Materialized Runtime Guards Use Symbolic Owners

Materialized runtime storage/code patch rendering had another duplicate guard:

```text
if platform absolute-memory owner exists
  -> do not materialize as source storage

if CPU exception vector exists
  -> do not materialize as source storage
```

The second check was renderer-local knowledge. It has been replaced with the
shared symbolic-owner predicate:

```c
platform_facts_v2_address_has_symbolic_owner(platform_kind, runtime_address)
```

This deliberately does not move CPU vectors into
`platform_facts_v2_absolute_memory_owner()`. That owner function feeds address
observations, and low-memory values may still be application storage unless the
instruction shape proves vector semantics. The render guard only needs the
narrower question: "does this address already have a stronger symbolic owner
than materialized runtime storage?" For that question, CPU vectors and hardware
owners are both exclusions.

## Non-Goals

- Do not add Damocles-only, Starglider-only, Pandora-only, or Magicland-only
  recognizers.
- Do not blacklist individual opcodes such as `ori`.
- Do not move source-quality decisions into Python, JSON export, or web code.
- Do not preserve internal API compatibility when it keeps the wrong ownership.
- Do not hand-edit generated target source as the fix.
- Do not hide incomplete analysis behind fallback rendering.
- Do not treat exact round-trip as proof of semantic source quality.
