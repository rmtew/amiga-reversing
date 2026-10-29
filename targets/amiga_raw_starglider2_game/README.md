# Starglider 2: buildable original-layout rendered source

This directory contains the current native rendered export, published at the
user's explicit request. Canonical analysis facts and append-only histories live
alongside it. The game assembly is regenerated from those facts; unchanged assets
are retained byte-for-byte from their verified original slices;
the build script and README are packaging support, not hand-edited game code.

## Build

Requirements: Python **3.9+** (standard library only) and the external Motorola
frontend **vasmm68k_mot**. Tested with Python 3.12.14, vasm 2.0e / M68k backend
2.8. The 14 required Amiga include files are supplied in `includes/`.
No analysis DLL, emulator, original reference binary or network is needed.

From this directory:

```sh
python3 build.py --vasm /absolute/path/to/vasmm68k_mot
```

Or run the same script from the repository root:

```sh
python3 targets/amiga_raw_starglider2_game/build.py --vasm /absolute/path/to/vasmm68k_mot
```

If `vasmm68k_mot` is on PATH, omit `--vasm`. The build uses
`-Fbin -m68000 -no-opt`, validates every input checksum, assembles the main image
and the three separate analysis views, validates all 57 INCBIN source slices,
and checks the decoded protection inverse. Output and a build receipt go to
`bin/rebuilt/`, which is ignored by Git. The assembler executable is not bundled.

## Files and output

- `starglider2_game.s`: unmodified canonical native main assembly.
- `assets/`: 57 native INCBIN files, 93633 bytes in total.
- `includes/`: the 14 unmodified required header files; notices retained.
- `analysis_views/`: decoded protection and original boot-selector source views.
- `tools/starglider2_protection.py`: original deterministic inverse recipe.
- `rendered-manifest.json`: checksummed build inputs and exact output identities.
- `rendered-provenance.json`: native export/source version and publication scope.

The main output is `bin/rebuilt/Starglider2-original.raw`: **412736 bytes**,
original load/entry `$1000`, SHA256
`662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9`.
It is a raw game payload, **not an AmigaDOS HUNK executable or bootable disk**.
Original bootstrap/intro memory state is still required to execute it. No ROM,
ADF, full input `binary.bin`, captures or assembler executable is committed here.

## Scope and analysis views

This is the reviewed original absolute-address restoration with explicit
unknowns: 106034 code bytes are accepted; 12682 bytes in 272 intervals remain
unclassified. It is not full semantic/all-path restoration or a completed
walkthrough. The source and assets preserve every original output byte.

The native control-value analysis now recovers eight signed-WORD dispatch
contracts automatically, including separated load/LEA/JMP sequences and
address-register indices. Physical table extent is separate from any proven
runtime selector bounds. See the
[dispatch receipt](../../runtime/observations/starglider2-relative-dispatch.json).

Referenced NUL strings inside the character pool now have deterministic inferred
labels and quoted records. The pool owner, duplicate/shared addresses, suffix
pointers and control bytes remain intact. Structural records without recovered
references receive no new labels or reader claims. See the
[string-pool receipt](../../runtime/observations/starglider2-string-pool-subentities.json).

The decoded view is 3548 bytes: 3484 transformed bytes plus 64 unchanged context
bytes. It is an analysis image, not a replacement game payload. Its inverse is
checked against the rebuilt original. One known native original-image code/data
conflict at the encoded entry remains explicitly documented.

The boot installer source uses bootblock-relative logical coordinates (`ORG
$24`), not an assumed OS boot-buffer address. Its original source context
contains the 20 bytes copied to actual address `$380`; the resident view renders
those same bytes there. A matching stacked return PC `$13C06` returns selector
`$91`, otherwise forwarding to the main PRNG. The original-media flight prefix now has seven CPU write-site windows matching
the decoded protection view. Post-intro residency of the boot shim itself remains
unobserved; matching the selector result alone is not a residency proof. These views document original media provisioning;
they are not a newly supplied loader or bypass to install.

## Regeneration and history

`manual_actions.jsonl`, `decision_journal.jsonl`, `target_metadata.json` and
`source_binary.json` remain the canonical project state. Regenerate through the
normal framework native exporter with `source_package_payload(64)`; do not edit
the generated assembly to change facts. Materializing the canonical analyzer's
private input is separate from this standalone build. Rendered outputs must be
re-exported and their build manifest refreshed after source-fact changes.

See [the restoration plan](../../docs/targets/starglider2-restoration-plan.md)
and the historical [residual interval review](../../runtime/observations/starglider2-original-unknown-intervals.json).
The private final ZIP remains an earlier delivery; this committed tree now also
contains its actual rendered source and required dependencies.

## Refinement after source review

The native renderer now emits a span annotation once, preserving separate field
comments. Native indexed address-register loads can discover text-pointer
directories, with runtime-address mapping, text shape and ownership checks;
referenced control-prefixed NUL text is retained as text rather than losing its
control bytes. These inferences do not prove complete dynamic index domains.

Pilot-rating strings, writable numeric slots, counter producers and the
16-entry verdict directory are documented through canonical facts. Model-header
pointer entries carry original catalogue identities, including shared-header
and type30 selector exceptions. This is not visual identification or a runtime
proof of every model. See the current refinement receipt under
`runtime/observations/starglider2-refinement-text-models.json` in the repository.

After explicit user approval, the original-media probe entered the selected
answer through normal keyboard input and reached flight. A bounded CPU-only
watch explains the expected-character and remaining-answer latches; it does not
cover every protection failure, later writer, model phase or DMA access. No guest
memory/register writes were used. The old private ZIP is historical; this
committed source is the refined export.
