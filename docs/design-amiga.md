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

Some loaders wrap this in a small local helper that walks the LoadSeg chain and
returns another segment body in an address register:

```asm
    move.w d6,d7
    lea.l loc_1_00000000-4(pc),a1
next_segment:
    movea.l (a1),a1
    adda.l a1,a1
    adda.l a1,a1
    dbf.w d7,next_segment
    addq.l #4,a1
    rts
```

Voodoo Nightmare `run` then calls through the returned register. The Amiga
platform layer owns the fact that this is a LoadSeg segment-list traversal. The
generic M68K flow engine may use the resolved section body as a normal
entrypoint, but it must not infer this behavior for Atari ST, raw binaries, or
ordinary M68K code without Amiga HUNK platform ownership. Shared analysis code
must query platform facts for LoadSeg segment-chain support and section-body
resolution; it may carry the resulting entrypoint provenance, but it must not
encode Amiga ownership as a generic M68K rule.

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

The fact that out-of-payload executable HUNK relocations may be preserved as
section-base anchors is Amiga platform knowledge. Generic relocation analysis
should ask the platform layer whether a fixup/raw value is a platform anchor;
other platforms may normalize or reject equivalent-looking addends differently.

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

This is an Amiga platform ownership fact. Generic M68K analysis should ask the
platform layer whether an absolute address is ExecBase, hardware, or another
platform-owned range before falling back to CPU vectors, runtime ranges, section
storage, or unresolved absolute memory. Other platforms must not inherit the
Amiga `$4` rule.

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

## Linkage API Wrapper Labels

Some imported Amiga objects contain required labels on short terminal wrapper
code that calls a library vector through `a6` and returns or tail-jumps. When
the label is fixture-backed and the LVO is present in generated Amiga OS
metadata, C analysis may promote that label as a code entrypoint. Unlabelled
API-looking byte islands stay orphan signals.

Generic M68K analysis must not know which LVOs are Amiga APIs. It should ask the
platform facts layer whether linkage API entry labels are supported and whether
an observed LVO belongs to the platform API set.
