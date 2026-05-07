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
