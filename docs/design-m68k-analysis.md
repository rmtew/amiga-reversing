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
- source instruction and data provenance
- whether the value is relocatable, absolute hardware, runtime absolute, or raw
  scalar data
- whether symbolic rendering would remain editable and reproduce exactly

The renderer should prefer stable symbols for owned memory and keep raw numeric
values when no owner is proven.

## Lookup Tables

Lookup tables must be modelled by the consumer expression, not only by the bytes.
A table is useful when analysis knows how entries are indexed and interpreted.

Common table classes:

```
absolute pointer table      dc.l target_a,target_b,0
relative word jump table    dc.w target_a-table_base,target_b-table_base
pc-relative dispatch table  move.w table(pc,d0.w),d1 ; jmp table(pc,d1.w)
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
accepted target ranges
sentinel/null rules
mixed-entry policy
confidence and conflict state
```

Table detection should start from consumers:

```
indexed read -> value transform -> jump/call/address use
                       |
                       +-> table base, entry size, signedness, bounds
```

Then analysis can safely back-fill the data range and render entries using
labels. Bytes alone may classify a span as a scalar table, but jump-table or
pointer-table rendering needs consumer evidence or relocation evidence.

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
table $505C..$507A          jump offsets     indexed dispatch consumer
$00010000..$00010FFF        ORG runtime      second-stage copy + jump
```

This should be data from C analysis. The UI can filter, navigate, and show
conflicts, but should not classify memory itself.

## Correctness Gates

- Do not emit app RSSET fields for known hardware or platform structs.
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
- Do not render raw absolute or addend-based table values when analysis can prove
  a stable symbolic target-base expression.
- Do not render symbolic table entries unless the table base, target range, and
  entry interpretation are proven.
- Do not use target metadata except for fixture-backed local facts.
- Preserve direct source correctness and exact reproduction.
- Treat comment-only output as a side effect, not a real analysis gain.
- Keep M68K instruction behavior in generated decode/effect data, not hand-coded
  renderer heuristics.
