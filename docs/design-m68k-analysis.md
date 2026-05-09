# M68K analysis design notes

This document is for implementers. It explains how M68K analysis should model
storage that is not simply "bytes in the current code section", with RSSET
layouts and absolute runtime memory as the first worked example.

The source renderer should be deterministic output from C analysis facts. Python
or web code may display those facts, but must not invent them.

The same rule covers these related topics:

- RSSET layouts: base-relative storage such as app slots and resident extension
  fields.
- Absolute memory: runtime addresses, hardware addresses, vectors, display
  memory, audio memory, stack, and absolute globals.
- Lookup tables: indexed data that should render as editable symbolic values,
  not fragile raw addends.
- ORG/runtime views: source bytes copied or relocated to absolute addresses and
  then executed.
- Bootstraps: small in-memory trampolines, vector handlers, decrunch wrappers,
  and loaders that prepare the useful runtime program.
- Orphaned code signals: code-like islands that are not yet linked into accepted
  program flow from the real entrypoints.

## Core rule

Analysis must answer this before rendering invents a symbol:

```
what base is being addressed?
what offset is being addressed?
what memory range owns that base?
what evidence proves the ownership?
does that ownership conflict with accepted code, hardware, or a typed struct?
```

If those answers are unknown, keep the source conservative.

## Reading Existing Evidence

When reviewing a target, separate accepted facts from signals:

```
accepted fact      renderer may use it directly
analysis signal    renderer keeps source conservative; UI/corpus can surface it
policy seed        explicit root or range; must carry reason/confidence
metadata seed      fixture-backed target/platform fact
fallback seed      last-resort root; must not suppress stronger evidence
```

Examples from current implementation:

- App-slot references are gathered only from accepted instruction starts.
- Unknown `a6` app-base fallback is blocked for generated `_custom` hardware
  offsets.
- RSSET rendering uses app-base field slots and metadata layout regions, with
  alias fragments when fields overlap.
- Runtime views and lookup tables already have tests for conflict suppression,
  runtime mapped dispatch, vector targets, and relative table rendering.
- Orphaned code signals are first-class analysis facts; they remain conservative
  diagnostics until a real inbound edge links them into accepted flow.

This distinction matters because "the bytes decode" is not the same as "the
program reaches this code".

## RSSET

`RSSET` is an assembler cursor for defining offsets inside a layout. It is not a
memory allocation by itself.

Typical app-base layout:

```asm
    RSSET 0
app_DOSBase RS.L 1
app_GfxBase RS.L 1
app_SIZEOF EQU __RS

    move.l d0,app_DOSBase(a6)
```

This is legitimate only when analysis has evidence that `a6` is the app base, or
that the target metadata/policy explicitly seeds that base.

Resident library/device layouts use the library base extension:

```asm
    INCLUDE "exec/libraries.i"

    RSSET LIB_SIZE
app_ExecBase RS.L 1
app_SegList RS.L 1
app_SIZEOF EQU __RS
```

That means "fields after the Amiga Library/Device header", not a generic app
scratch block.

If a resident autoinit size is exactly `LIB_SIZE` and no extension slots are
proven, render the size as `LIB_SIZE` and do not emit an empty `RSSET LIB_SIZE`
region:

```asm
resident_autoinit:
    dc.l LIB_SIZE    ; ULONG resident_base_size
```

Only render `app_SIZEOF` when the autoinit size is greater than `LIB_SIZE` or
when actual extension fields have been proved. An empty `app_SIZEOF EQU __RS`
does not improve source reconstruction and incorrectly suggests an app-specific
layout exists.

## Not RSSET

Known platform structures must render as platform fields, not app slots:

```asm
    lea.l _custom.l,a6
    move.w d0,intena(a6)
```

This must not become:

```asm
app_009A RS.W 1
    move.w d0,app_009A(a6)
```

The same applies to `_ciaa`, `_ciab`, library bases, device bases, IO requests,
audio channels, sprite definitions, copper/display structures, and any other
known generated Amiga platform struct.

Typed app-slot structs own their whole proven extent. If analysis proves an app
slot contains a `TimerVal`, IO request, library/device base, or other generated
platform struct, interior offsets inside that struct must not create new flat
`app_NNNN` RSSET fields. They should render through the typed field expression
when the field is known, or remain unresolved/numeric when it is not. This keeps
the app layout from inventing duplicate storage for bytes that belong to a typed
substructure.

Resolved platform typed-access records carry both `struct_size` and
`field_size`. The observed field access remains the rendering fact, while the
struct size gives memory-layout consumers a compact ownership range for the
typed base.

## Base Provenance

Every RSSET field needs a base provenance record:

```
base id:          __amiga_app_base__
base kind:        app storage, resident extension, typed IORequest, metadata
base address:     unknown, hunk-relative, or absolute
offset range:     start..end
evidence:         instruction refs, API result, register seed, metadata
confidence:       strong, medium, weak
conflict state:   clean, overlaps accepted code, overlaps struct, overlaps hw
```

The app-layout property is an analysis flag on the RSSET layout region, not a
renderer-side comparison of names such as `app` or `__amiga_app_base__`.
Names remain display/provenance data; control flow decisions consume the flag.

Multiple `RSSET` stanzas in the rendered source are not automatically multiple
memory ranges. They can be overlay aliases at offsets inside the same base.

Example alias:

```asm
    RSSET 0
app_word RS.W 1
app_SIZEOF EQU __RS

    RSSET $0001
app_low_byte RS.B 1
```

That is one layout with an alias overlay. A second independent layout requires a
different proven base id.

## Comparable Ranges

Conflict checks must compare addresses in the same address space. A base-relative
app slot offset is not a source-code offset:

```asm
    move.l d0,app_0100(a6)
```

The range is `a6+$0100..a6+$0103`. Without a proven mapping for `a6`, this must
not be compared to source bytes `$0100..$0103`.

Section-relative storage is different:

```asm
    move.l d0,loc_0_00000100.l
```

If analysis records this as a platform storage effect with
`range_space_kind = section_relative`, `target_section_index = 0`, and
`target_offset = $0100`, then it is comparable to accepted-code bytes in section
0. If any byte in the target range is accepted code, the memory-layout record is
`conflicted = true` and `conflict_state_id = code_overlap`.

Correctness gates:

- base-relative app, resident, or typed-slot ranges are only compared against
  other ranges proven to use the same base
- section-relative ranges may be compared to accepted source-code bytes in the
  target section
- runtime-absolute ranges may be compared only through a proven runtime/source
  view
- display strings such as `app_0100` or `loc_0_00000100` are not proof that two
  ranges share an address space

## Absolute Runtime Memory

Absolute relocated targets need memory-range tracking, not ad hoc labels.

The analysis model should keep storage and runtime address spaces separate:

```
source hunk/file bytes
  section 0: $000000..$0003FF
      copy loop writes
          runtime code: $000400..$0012FF
          stack:        $07F000..$080000
          bitplanes:    $070000..$076000
          app base:     a6 + $0000..$0FCF
          hardware:     _custom + display/audio/copper fields
```

For an absolute addressed file, the base address and extent are part of the
target model. Labels inside absolute runtime code must be tied to the runtime
range that owns them, while source-copy labels stay tied to source storage.

Absolute memory rows carry a compact conflict state. `clean` means the resolved
address does not overlap accepted code in the current source view.
`code_overlap` means the address does overlap accepted code; renderers must not
treat that as a free data region unless another source/runtime mapping proves
the overlap is intentional.

An absolute operand decoded only inside an orphan-code signal is not an accepted
memory fact. It should still be exported in the same memory-layout view with
`conflict_state_id = unresolved`, unknown ownership unless platform evidence
proves more, and the orphan instruction as source provenance. This lets the UI
surface "code-like bytes refer to absolute memory" without promoting the bytes
to code or inventing labels.

## ORG and Runtime Views

`ORG` changes the assembler's logical PC. It is useful only when it represents a
real source-level runtime view, not when it hides missing analysis.

Keep three addresses separate:

```
storage address       where bytes live in the hunk/file
runtime address       where the program copies or relocates those bytes
rendered logical PC   where the assembler thinks it is after ORG
```

Example:

```asm
storage_payload:
    dc.b ...

    ORG $400
runtime_payload:
    move.w #INTF_CLRALL,_custom+intena
```

The label `storage_payload` names file bytes. The label `runtime_payload` names
the copied runtime view. They are related, but they are not interchangeable.

The runtime range base and the first runtime entrypoint are also separate facts.
A copied range can start at `$400` while the first proven instruction entered is
`$45C`. Use the range base for mapping bytes and the entrypoint list for code
discovery.

Strong ORG evidence usually has:

- a source range
- a destination runtime range
- a size or terminating copy condition
- an entrypoint into the destination
- accepted code at the mapped source bytes
- no incompatible overlap with stronger accepted code

Weak evidence should not produce an `ORG`. A low-memory trampoline, vector stub,
or temporary copy helper can stay numeric or become an absolute symbol until it
is proven to be an independent source-level runtime range.

Multiple ORGs are valid only when analysis proves independent runtime ranges and
the assembler's `ORG` semantics keep cross-references correct.

Runtime-view analysis state should stay compact. Each runtime view row records
the storage range, runtime range, materialization decision, reason, and only
when proven a related runtime view. Relationship kinds are enum facts such as
`exits_to_larger_runtime_range`, `contained_by_runtime_range`, and
`overlaid_by_runtime_copy`. The C row does not store narrative annotations; UI
and corpus tooling extrapolate those row-level facts into wrapper/helper/final
image navigation.

## Bootstraps and In-Memory Relocation

Many Amiga programs do not execute the main program where it appears in the file.
They bootstrap it.

Common patterns:

```
loader hunk -> copy loop -> runtime code -> jump runtime entry
loader hunk -> vector install -> trap/interrupt -> copy main payload
packed data -> decrunch -> copied payload -> jump entry
raw extracted payload -> second-stage copy -> final absolute image
low trampoline -> larger runtime range
```

Bloodwych-style shape:

```asm
    lea.l payload_source(pc),a6
    lea.l $400.l,a0
copy_loop:
    move.b (a6)+,(a0)+
    dbf d0,copy_loop
    jmp $400.l

payload_source:
    ; bytes that execute at $400
```

Rendered shape when proven:

```asm
payload_source:
    ORG $400
runtime_entry:
    move.w #INTF_CLRALL,_custom+intena
```

Pandora-style shape:

```
wrapper load address:   $20000
small copied helper:    $00300
final runtime image:    $10000..$10xxx
entrypoint:             $1046A
```

The useful ORG is the final `$10000` image, not the wrapper load address and not
the weak `$300` helper unless later evidence proves that helper is independently
important source.

Conqueror-style warning:

```
absolute $4 reference        weak low address
larger copied range $40/$64  useful runtime range
```

Do not emit an `ORG $4` simply because control briefly reaches `$4`. That can
create duplicate labels and broken cross-range references.

Required bootstrap facts:

```
source storage range
runtime destination range
runtime base and runtime extent
copy/decrunch/relocation mechanism
entrypoint list
trampoline/vector relationship
source-to-runtime address map
confidence and conflict state
reproduction status
corpus tags and rejected-candidate reason
```

Runtime copied code should be discovered from value-flow and control-flow facts:
copy source, destination, and length; vector stores; trap/interrupt dispatch;
indirect jumps; and explicit metadata/policy seeds. Rendering should not guess.

## Orphaned Code Signals

Sometimes bytes left as data decode cleanly as code and contain terminal
instructions such as `rts`, `rte`, `jmp`, or unconditional branches. That is a
signal, not proof that the source renderer should silently promote the bytes to
accepted code.

Why this matters:

```
entrypoint -> normal flow -> unresolved indirect jump
                              |
                              v
                      orphan-like code island
                      ... rts
```

Auto-converting the island can make the listing prettier, but it hides the real
bug: analysis failed to connect the island to the program through a jump table,
callback, vector, copied runtime entry, or API-discovered entrypoint.

The right model is:

```
accepted code       reached from known roots
orphan candidate    decodes as plausible terminal code, not reached yet
resolved orphan     later linked by stronger analysis evidence
rejected orphan     overlaps data/table/strings or fails plausibility
```

Required orphan facts:

```
candidate source range
decode start and terminal instruction
plausibility score, CPU requirement, instruction count, and decode conflict count
nearby data/table/string context
possible inbound evidence: jump table, vector, callback, runtime copy, API
why it is not accepted yet
what analysis would need to connect it
```

Only promote an orphan candidate to accepted code when a real inbound edge or
explicit policy/metadata seed proves it. Until then, expose it as an analysis
problem and corpus tag.

The success metric is not "more auto-converted code". The success metric is that
orphan signals decrease because better jump/lookup table, callback, vector, ORG,
or absolute-memory analysis found real links.

Cause classification should be evidence-based even when the signal stays
unresolved. For example, an orphan terminal island immediately adjacent to a
`lookup_table` remains data in the rendered source, but its missing inbound class
should be `jump_table` so the next implementation pass can focus on dispatch
recovery rather than treating it as an unknown island. A similar island adjacent
to a `pointer_table` should be classified as callback/function-table evidence,
not promoted until an actual inbound edge is found.

Internal orphan facts are ids and flags, not display strings. Nearby data context
stores semantic role flags plus a compact relation id (`overlap`, `after`,
`before`). Missing inbound evidence stores a compact id (`unknown`, `jump_table`,
`callback`, `vector`, `runtime_copy`, `api`, `metadata`, `policy_seed`). JSON
may include text names for UI output, but corpus and analysis consumers must use
the ids/flags. A policy-named label is explicit seed evidence
(`policy_seed`); an object or metadata label is only `metadata` evidence.

## Absolute Memory Access

Absolute memory is not one thing. Analysis should classify the ownership before
rendering a symbol.

```
$00000004              ExecBase address, normally keep literal $4
$00000080              CPU vector table slot
$00000400..$0012FF     copied runtime code
$00010000..$00010FFF   final bootstrap runtime image
$00070000..$00075FFF   bitmap/display memory
$00076000..$00076FFF   audio/sample/data buffer
$00DFF000..$00DFFFFF   Amiga custom chip registers
a6+$0000..a6+$0FCF     app base-relative storage
```

Examples:

```asm
    movea.l $4.w,a6                  ; ExecBase literal, not ExecBase symbol
    move.l  #trap_handler,$80.w      ; vector slot with code target
    move.w  #$0200,_custom+dmacon    ; hardware register
    move.l  #bitmap_00070000,bpl1pt  ; display memory pointer
```

Required analysis facts:

- address expression and width
- read, write, address-taken, call, or jump use
- owner range if known
- target range if the value is a pointer
- sink address when a pointer is written to an external owner such as `_custom`
  display, copper, disk, sprite, or audio registers
- source instruction and data provenance
- whether the value is relocatable, absolute hardware, runtime absolute, or raw
  scalar data
- whether symbolic rendering would remain editable and reproduce exactly

The renderer should prefer stable symbols for owned memory and keep raw numeric
values when no owner is proven.

Packed or transformed payloads need a grouped relationship fact in corpus/UI
views: source section range, absolute load address, and entrypoint must be
queryable together. Separate `source_range`, `output_load_address`, and
`entrypoint` features remain useful, but the grouped relationship is the proof
that a raw/decompressed child has a coherent runtime image.

Current C source analysis records accepted absolute operands as
`absolute_memory_ref` memory-layout records. The operand is accepted only from a
decoded instruction already reached by flow analysis, and the use kind comes from
generated simulator metadata:

```
source instruction       move.w #$1234,$00DFF09A.l
address                  $00DFF09A
access                   memory_write
owner                    hardware_register
owner symbol             _custom+intena
conflict gate            mark if a memory read/write overlaps accepted code
```

Owner classification is provenance-first:

```
$4 on Amiga        execbase_literal
CPU vector slot    cpu_vector
Amiga hardware     hardware_register or hardware_register_range
runtime map hit    runtime_range
in-section hit     section_storage
otherwise          absolute_memory
```

This fact is diagnostic and navigational. It does not by itself authorize new
labels or source rewriting.

## Lookup Tables

Lookup tables must be modelled by the consumer expression, not only by the bytes.
A table is useful when analysis knows how entries are indexed and interpreted.

Common table classes:

```
absolute pointer table      dc.l target_a,target_b,0
relative word jump table    dc.w target_a-table_base,target_b-table_base
pc-relative dispatch table  move.w table(pc,d0.w),d1 ; jmp table(pc,d1.w)
keyed relative dispatch     dc.w target_a-table_base,key_a
scalar lookup table         dc.b 0,1,4,9,16
offset lookup table         dc.w row0-map_base,row1-map_base
hardware setup table        dc.w bplcon0_value,diwstrt_value,...
mixed table                 labels, nulls, raw sentinels, scalar entries
```

Jump table example:

```asm
dispatch:
    move.w  jump_offsets(pc,d0.w),d0
    jmp     jump_offsets(pc,d0.w)

jump_offsets:
    dc.w case_0-jump_offsets
    dc.w case_1-jump_offsets
    dc.w case_2-jump_offsets
```

The important part is the relative expression. Raw values such as `$0012` are
fragile: if a user edits code between the table base and target, the rebuilt
source can silently point at the wrong target. `case_1-jump_offsets` remains
editable.

Keyed relative dispatch is the same source-restoration problem with a wider
entry. One observed shape loads a longword from `(aN)+`, swaps the words, then
uses the new low word as a PC-relative control offset. The high word should
render as `case-table_base`; the low word stays numeric unless later domain
analysis proves it is symbolic:

```asm
dispatch:
    move.l  (a1)+,d2
    swap.w  d2
    jsr     keyed_table(pc,d2.w)

keyed_table:
    dc.w    case_a-keyed_table,$001e
    dc.w    case_b-keyed_table,$0020
```

Absolute pointer table example:

```asm
ptr_table:
    dc.l handler_0
    dc.l handler_1
    dc.l 0
```

Offset table example:

```asm
room_offsets:
    dc.w room_0-room_base
    dc.w room_1-room_base
```

Required table facts:

```
table base label
table source range
entry size and signedness
entry count and stride
entry kind: scalar, pointer, relative pointer, code target, data target
base expression: table base, section base, runtime base, PC, or explicit label
consumer instruction and value-flow provenance
source pattern that identified the table
accepted target ranges
sentinel/null rules
mixed-entry policy
confidence and conflict state
```

Table detection should start from consumers:

```
indexed read -> value transform -> jump/call/address use
                       |
                       +-> source pattern, table base, entry size, signedness, bounds
```

Then analysis can safely back-fill the data range and render entries using
labels. Bytes alone may classify a span as a scalar table, but jump-table or
pointer-table rendering needs consumer evidence or relocation evidence.
Current source-pattern examples include relocation pointer tables, indexed word
dispatch, indexed local pointer reads, indexed local scalar reads,
postincrement read sequences, PC-relative indexed reads, and keyed long relative
dispatch.

Rejected candidate bounds are still useful when analysis can prove the table
base and a bounded candidate span, but cannot accept the table yet:

```asm
    jmp     table(pc,d1.w)
    nop
table:
    bra.b   possible_handler
    nop
possible_handler:
    rts
```

If this scan finds only one uniform direct-stub entry, the site remains an
unresolved indirect jump. C analysis should still record:

```
table_offset, table_size
table_entry_size, table_entry_count
table_bounds_status = rejected_insufficient_entries
```

This gives corpus/UI navigation a precise work item without hiding the missing
inbound analysis. It must not promote bytes to code or classify data unless a
real inbound edge, relocation, runtime mapping, or policy seed proves ownership.

## Relative Target-Base Substitution

When a table entry is calculated as `target - base`, render that relationship
directly:

```
raw word:       $012C
base:           abs_0_0000505C
target:         abs_0_00005188
rendered:       dc.w abs_0_00005188-abs_0_0000505C
```

Acceptable bases include:

- the table label
- a nearby explicit base label used by code
- the current runtime range base
- a section base when relocation evidence proves it
- a data structure base when typed-flow proves it

Do not choose a convenient base just to make numbers look symbolic. The base must
come from analysis evidence.

## Web UI Requirement

The UI should be able to show an analysed memory layout view:

```
range                       kind             evidence
$000400..$0012FF            runtime code     copy loop + jump
$070000..$076000            bitmap           bitplane pointer writes
_custom+$00E0.._custom+$00EE display regs    hardware metadata
a6+$0000..a6+$0FCF          app layout       app-slot refs
a6+$0001                    app alias        overlay field
typed field                 platform struct  root/owner/field provenance
table $505C..$507A          jump offsets     indexed dispatch consumer
$00010000..$00010FFF        ORG runtime      second-stage copy + jump
orphan h0:$D3EE..$D42A      code signal      terminal decode, no inbound edge
```

This should be data from C analysis. The UI can filter, navigate, and show
conflicts, but should not classify memory itself.

Resolved platform typed accesses are memory-layout evidence too. They prove that
a base and displacement are owned by a platform struct field, so they should be
visible beside app slots and runtime ranges rather than only in type-flow reports.
Unresolved typed accesses should remain unresolved records with classification
such as field gap, prefix extension, or mistyped base.

Runtime address references should preserve both sides of a hardware sink:

```
source instruction       move.l #bitmap_00070000,_custom+bpl1pt
runtime/data target      $00070000 bitmap/display memory
sink address             $00DFF0E0 BPL1PTH/BPL1PTL owner range
```

This lets rendering and the web UI explain why an absolute buffer is display or
audio memory without reparsing rendered source text.

Target-level memory-layout views are summaries over these C records, not a
second classifier. They use numeric `range_space_kind`, `conflict_state_id`, and
absolute `owner_kind_id` fields to answer broad questions such as "does this
target have absolute hardware refs?", "which address spaces are present?", and
"are any layout ranges conflicted?". String names in the view are display labels
resolved from those ids.

## Platform Base Identity

Amiga library/device base identity in C analysis state is a generated base id.
Names are retained only for emitted source, JSON text, and user-facing labels.
The analysis must canonicalize equivalent evidence such as `exec.library`,
`SysBase`, and safe base-symbol aliases to the same generated base id before LVO
lookup, OpenLibrary/OpenDevice recognition, or local/base-slot propagation.

Do not compare static strings to decide whether a register is ExecBase, DOSBase,
or another platform base. Use generated ids for decisions and resolve text from
metadata only at output boundaries.
Policy RSSET layout storage kinds follow the same rule: decode metadata text
once into compact C enum ids, consume the ids internally, and keep strings only
for source/debug/export text.
Memory-layout conflict features follow the same split: `memory-layout:conflict`
is the boolean bucket and `memory-layout:conflict_state:<state>` is the stateful
bucket derived from `conflict_state_id`. Do not emit duplicate state spellings
such as `memory-layout:conflict:<state>`.
Base-layout fields also carry a compact layout-kind id. Range and conflict
consumers must use that id before comparing base-relative ranges; layout/base
names remain labels, not classifiers.
Base-relative conflicts are only valid inside the same proven base. App offsets
must not be compared directly to source-code offsets; accepted-code conflicts
need an explicit source/runtime mapping before the ranges are comparable.

## Correctness Gates

- Do not emit app RSSET fields for known hardware or platform structs.
- Do not emit flat app RSSET fields for offsets inside a proven typed app-slot
  struct range.
- Do not treat alias RSSET fragments as independent ranges without distinct base
  provenance.
- Do not overlap accepted code unless the range is explicitly a copied/runtime
  view with source/runtime mapping.
- Do not emit duplicate visible labels for storage and runtime namespaces unless
  they truly name the same logical source location.
- Do not add an `ORG` for a weak trampoline when a stronger larger runtime view
  explains the same control flow.
- Do not let a wrapper load address suppress later copied-image entrypoint
  evidence.
- Do not promote orphaned code-like data to accepted code merely because it
  decodes and terminates.
- Do not render raw absolute or addend-based table values when analysis can prove
  a stable symbolic target-base expression.
- Do not render symbolic table entries unless the table base, target range, and
  entry interpretation are proven.
- Do not use target metadata except for fixture-backed local facts.
- Preserve direct source correctness and exact reproduction.
- Treat comment-only output as a side effect, not a real analysis gain.
- Keep M68K instruction behavior in generated decode/effect data, not hand-coded
  renderer heuristics.
