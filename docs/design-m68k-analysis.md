# M68K analysis design notes

This document is for implementers. It explains how M68K analysis should model
storage that is not simply "bytes in the current code section", with RSSET
layouts and absolute runtime memory as the first worked example.

The source renderer should be deterministic output from C analysis facts. Python
or web code may display those facts, but must not invent them.

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

## Web UI Requirement

The UI should be able to show an analysed memory layout view:

```
range                       kind             evidence
$000400..$0012FF            runtime code     copy loop + jump
$070000..$076000            bitmap           bitplane pointer writes
_custom+$00E0.._custom+$00EE display regs    hardware metadata
a6+$0000..a6+$0FCF          app layout       app-slot refs
a6+$0001                    app alias        overlay field
```

This should be data from C analysis. The UI can filter, navigate, and show
conflicts, but should not classify memory itself.

## Correctness Gates

- Do not emit app RSSET fields for known hardware or platform structs.
- Do not treat alias RSSET fragments as independent ranges without distinct base
  provenance.
- Do not overlap accepted code unless the range is explicitly a copied/runtime
  view with source/runtime mapping.
- Do not use target metadata except for fixture-backed local facts.
- Preserve direct source correctness and exact reproduction.
- Keep M68K instruction behavior in generated decode/effect data, not hand-coded
  renderer heuristics.

