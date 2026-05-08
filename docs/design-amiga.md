# Amiga Platform Analysis

This document records Amiga-specific analysis and rendering rules that should
not be hidden in target metadata or generic M68K logic.

## HUNK Relocation Anchors

Amiga HUNK `HUNK_RELOC32` entries can legally point outside the loaded payload
range of the target hunk. A common example is a longword relocated as
`base(hunk 0)-4`, which refers to the LoadSeg segment link/header word before
the hunk payload. Some real executables also use segment-relative references to
reach other segment metadata or code.

These references must remain relocatable when source is reassembled. Rendering
them as plain numeric data preserves bytes but loses relocation semantics.
Rendering them as ordinary labels plus addends is also wrong: if the label is a
normal code/data label, user edits before that label can change the expression.

The source model therefore supports generated section-base pseudo-symbols:

```asm
    dc.l __section_0_base-$00000004
```

`__section_N_base` is not a rendered location label. It resolves in the C source
emitter to section `N`, offset `0`, so the rebuilt object receives a real
relocation against the section base with the encoded addend. Ordinary in-range
code/data references must still render to target labels, not to
`__section_N_base+offset`.

Rules:

- Use target labels for relocations into accepted source ranges.
- Use section-base pseudo-symbols only for proven HUNK relocation anchors whose
  target is outside the renderable hunk payload range.
- Do not use `EQU` constants for these anchors; constants lose relocation
  semantics.
- Do not use ORG/runtime labels to model hunk headers or segment links.
- Keep direct source/rebuild verification as the correctness gate.

## ExecBase Absolute Address

The Amiga ExecBase pointer lives at absolute address `$4`. Although the
platform metadata records this as `AbsExecBase`, rendered source should keep
direct ExecBase loads literal:

```asm
    movea.l $00000004.l,a6
```

This is the familiar Amiga idiom and is more useful to users than introducing a
symbol for the well-known low-memory vector. The renderer must still distinguish
this from runtime copied code at address `$4`: copy targets and control
transfers to discovered runtime code may use generated runtime-code symbols,
but the ordinary ExecBase load itself stays numeric.

Rules:

- Keep direct `($4)` ExecBase loads literal.
- Do not render ExecBase as a code/data label, an ORG label, or
  `runtime_code_00000004`.
- Use runtime-code symbols at `$4` only when analysis proves copied executable
  code is materialized there.

## Runtime-Copied ORG Code vs Decompression

Some Amiga programs copy bytes from their loaded hunk into absolute memory and
then execute them. This is not automatically decompression. If the copied bytes
are already present as source bytes and analysis proves the runtime destination,
the source model is an ORG/runtime view, not a decompressed child target.

Magicland Dizzy `MD` is the current proving example: C analysis records a
runtime view at `$5BFF0`, a runtime-address reference proves the copied range
start, and facts-v2 queues that address as a `runtime_view_entry`. The rendered
source should therefore decode the ORG payload in the same target. It should
not create a decompressed child unless later analysis proves a produced
replacement program that is not just an ORG view of shipped bytes.

Rules:

- Treat ORG/runtime views as source mappings of bytes already in the target.
- Treat decompressed children as produced bytes with their own provenance,
  output range, entrypoint, role, and reproduction status.
- Do not use decompression machinery to paper over missing ORG/runtime-copy
  analysis.
- Do not use ORG rendering to hide a real packer that produces bytes not present
  as a source range.
- Keep `docs/design-m68k-analysis.md` and `docs/plan-m68k-analysis.md` as the
  canonical ORG range evidence and rendering guide.

## Hardware Block Aliases

Some custom-chip register blocks are easier to read as block aliases plus field
offsets. These aliases belong in Amiga platform metadata or generated includes,
not in target metadata.

Useful aliases include:

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

Rules:

- Render audio, sprite, copper, display, CIA, and custom-chip accesses through
  platform metadata when the base is known.
- Do not infer app slots from offsets that belong to known hardware bases.
- Prefer block aliases only when they match the hardware layout and keep source
  editable without fragile addends.
