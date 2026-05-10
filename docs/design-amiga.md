# Amiga platform analysis design notes

This document is for implementers who are adding Amiga-specific analysis without
turning Amiga details into generic M68K rules.

Generic M68K analysis should answer instruction-flow and typed-flow questions.
Amiga platform analysis should answer questions about HUNK loading, Exec/DOS
runtime conventions, custom-chip memory, CIA registers, devices, libraries, and
other Amiga-specific ownership. The renderer should consume those C-owned facts;
Python and the web UI may display them, but must not invent them.

## Core Rule

Before rendering an Amiga-specific symbol, analysis must know:

```text
which Amiga owner is being addressed?
which address space owns it: hunk payload, LoadSeg metadata, runtime absolute,
hardware, vector table, app storage, or device/library structure?
what evidence proves that owner?
will the rendered expression stay editable and reproduce the original object?
```

If any answer is missing, keep the source conservative.

## LoadSeg Segment Headers

`LoadSeg()` does not return a bare pointer to only the hunk bytes. DOS links
loaded hunks through a segment list. For each loaded segment, the longword just
before the hunk body is the next segment link. In source terms:

```asm
segment_alloc_base:
    dc.l allocation_size
segment_link:
    dc.l next_segment_bptr      ; body_start-4
body_start:
    ; hunk payload starts here
```

Real programs can deliberately inspect this metadata. Voodoo Nightmare `run`
does this with a PC-relative reference to the longword before section start:

```asm
    lea.l loc_0_00000000-4(pc),a1
```

That is not an absolute low-memory `$4` access. It is not an ORG range. It is
also not a standalone `EQU -4` symbol, because `amiga_loadseg_segment_link(pc)`
hides the base of the expression. The useful source relationship is "the
LoadSeg link for this section", so the rendered operand must be anchored to the
section-start label plus the negative addend.

Rules:

- Render proven pre-segment references as section-start expressions such as
  `loc_0_00000000-4(pc)`.
- Do not emit `amiga_loadseg_segment_link EQU -4` for these operands.
- Do not model LoadSeg segment headers as ORG/runtime labels.
- Do not convert a section-start prelude reference into a hardware, vector, or
  absolute-RAM reference just because the addend is a small number.
- Keep reproduction exact after changing these expressions.

## HUNK Relocation Anchors

HUNK `HUNK_RELOC32` entries can legally point outside the loaded payload range.
For data relocations, the source model can preserve relocation semantics through
generated section-base pseudo-symbols:

```asm
    dc.l __section_0_base-$00000004
```

`__section_N_base` is not a rendered location label. It resolves in the C source
emitter to section `N`, offset `0`, so the rebuilt object receives a real
relocation against the section base with the encoded addend.

Use target labels for relocations into accepted source ranges. Use section-base
pseudo-symbols only for proven HUNK relocation anchors whose target is outside
the renderable hunk payload range. Ordinary code/data references should still
render to labels, not to `__section_N_base+offset`.

## ExecBase Absolute Address

The ExecBase pointer lives at absolute address `$4`. Users expect the familiar
literal form:

```asm
    movea.l $00000004.l,a6
```

Keep direct ExecBase loads literal. Do not render them as `ExecBase`,
`AbsExecBase`, a runtime label, an ORG label, or a LoadSeg segment-link
expression. Runtime copied code at address `$4` is a different fact and needs
separate runtime-copy evidence before it can use a runtime-code symbol.

## Runtime ORG Views And Decompressed Children

Some Amiga programs copy bytes from their loaded hunk into absolute memory and
execute them. That is an ORG/runtime view when the bytes already exist in the
source target. It is a decompressed child target only when analysis proves a new
produced byte image with its own load range, entrypoint, and provenance.

Rules:

- Use ORG/runtime views for copied or relocated bytes already present in the
  target.
- Use decompressed children for produced bytes with independent source/output
  ranges.
- Do not use decompression machinery to hide missing ORG/runtime-copy analysis.
- Do not use ORG rendering to hide a real packer.
- See `docs/design-m68k-analysis.md` and `docs/plan-m68k-analysis.md` for the
  generic runtime-view model and current work plan.

## Hardware And Platform Structures

Known Amiga platform structures must render through platform metadata, not app
slots:

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
audio channels, sprite definitions, copper/display structures, and any generated
Amiga platform struct.

Useful custom-chip block aliases include:

```asm
aud   EQU $0A0
aud0  EQU $0A0
aud1  EQU $0B0
aud2  EQU $0C0
aud3  EQU $0D0

sprpt EQU $120
spr   EQU $140

sd_pos    EQU $00
sd_ctl    EQU $02
sd_dataa  EQU $04
sd_dataB  EQU $06
sd_SIZEOF EQU $08
```

Render audio, sprite, copper, display, CIA, and custom-chip accesses through
generated platform metadata when the base is known. Prefer block aliases only
when they match the hardware layout and keep source editable without fragile
addends.
