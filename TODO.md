# TODO

## Payload target decompression failure

### `amiga_disk_conqueror-1990-rainbow-arts-de-en` / `amiga_hunk_conqueror_cf971606`

We extract compressed payloads as child targets for Damocles for example which has two tetragon decompression payloads we identify and show in the web UI. However there is no successfully extracted payload and child target shown in  `conqueror_cf971606.s`.

## Disassembly failures

### `amiga_disk_starglider-1987-rainbird` / `amiga_hunk_sg_9832b282` / `sg_9832b282.s` case study

This should never be emitted through auto-analysis outside of the context of MacOS jump tables for instance. Non-terminating instructions directly precede data. And "ori" is a classic false positive code recognition. Multiple blocks are emitted with this.
```
loc_0_00006098:
	ori.w #112,$0(a0,d0.w)
	ori.b #136,d0
	dc.b $00,$88,$00,$00,$00,$00,$01,$04,$01,$04,$00,$00,$00,$00,$02,$02
	dc.b $02,$02,$00,$00,$00,$00,$84,$01,$84,$01,$00,$00,$00,$00,$48,$00
	dc.b $48,$00,$00,$00,$00,$00,$30,$00,$30
	dcb.b $D,$00
```

Here we have a RTS (terminating instruction) polluting the emitted string, and it highlights an orphan code block that precedes it - possibly from the start of the block. The inline symbols suggest this is the case. We may not convert this and may flag it to the user for review, but it should possibly aid in excluding the bad string signal from the strings.
```
	dc.b $60,$00,$FE,$82,$48,$E7,$FF,$FE,$3F,$01,$43,$FA,$00,$F2,$22,$BC
	dc.b $20,$20,$20,$20,$23,$7C,$20,$20,$20,$20,$00,$04,$61,$00,$A9,$8A
	dc.b $61,$00,$14,$14,$20,$6E,$00,$04,$D0,$FC,$04,$D0,$43,$FA,$00,$CC
	dc.b $23,$FC,$00,$00,$00,$01
	dc.l loc_0_00009882
	dc.b $61,$00,$17,$D8,$30,$1F,$43,$FA,$00,$D4,$22,$BC,$20,$20,$20,$20
	dc.b $23,$7C,$20,$20,$20,$20,$00,$04,$61,$00,$A9,$54,$20,$6E,$00,$04
	dc.b $D0,$FC,$06,$60,$43,$FA,$00,$B2,$23,$FC,$00,$00,$00,$01
	dc.l loc_0_00009882
	dc.b $61,$00,$17,$A6,$61,$00,$16,$78,$4C,$DF,$7F,$FF,$4E,$75,$48,$E7
	dc.b $FF,$FE,$30,$01,$43,$FA,$00,$AC,$22,$BC,$20,$20,$20,$20,$23,$7C
	dc.b $20,$20,$20,$20,$00,$04,$61,$00,$A9,$14,$20,$6E,$00,$04,$D0,$FC
	dc.b $07,$F0,$43,$FA,$00,$8A,$23,$FC,$00,$00,$00,$01
	dc.l loc_0_00009882
	dc.b $61,$00,$17,$66,$61,$00,$16,$38,$4C,$DF,$7F,$FF,$4E,$75,$48,$E7
	dc.b $FF,$FE,$30,$01,$43,$FA,$00,$84,$22,$BC,$20,$20,$20,$20,$23,$7C
	dc.b $20,$20,$20,$20,$00,$04,$61,$00,$A8,$D4,$20,$6E,$00,$04,$D0,$FC
	dc.b $09,$80,$43,$FA,$00,$62,$23,$FC,$00,$00,$00,$01
	dc.l loc_0_00009882
	dc.b $61,$00,$17,$26,$61,$00,$15,$F8,$4C,$DF,$7F,$FF
	dc.b "NuD0        00000000",$00	; string
```

## String rendering and analysis

### `monam302.s` case study

There's a good argument that we can detect `loc_0_000081C6` is valid text with an upper case english-style word and punctuation. See also `loc_0_00004CA8`. We can gain confirmation by typing of usage of many of these, even API parameter types lining up.

```
loc_0_000081C6:
	dc.b $4C,$49,$42,$53,$3A
loc_0_000081CB:
	dc.b "monam.libfile",$00	; string
```

Also:

```
loc_0_00000000:
	bra.w loc_0_00000094
	dc.b $4D,$4F,$4E,$20
```

If that is a valid heuristic then it should be possible to apply it generally to character constant representations.

```
	cmp.l #$434F4445,d1
	beq.b loc_0_00007304
	cmp.l #$48554E4B,d1
	bne.b loc_0_000072C2
```

## Type analysis, variable naming and propagation

In this we know the output for calls like _LVOOpenScreen and _LVOOpenWindow. We know the type of calls like this and should be able to associate type and generate a name for the storage locations using general logic pulling in platform specific API data (generally applicable to all platforms), whether members in RSSET ranges or labels to data statements somewhere. Examples of names might be platform-profile driven, where for Amiga it might be `app_ScreenPtr` and `app_WindowPtr`.

There is nominal typing exhibited for the screen pointer with `sc_BarHeight`, however similar typing is not applied to either naming or access to the `NewScreen` or `NewWindow` structures whose pointers are passed into the calls. If `loc_0_00000492` is a `NewScreen` it should be named as such, and it should be typed as such, with either use of `.i` structs if possible or typed and annotated fields if more suitable. Any access into the ptr output structs is then open to auto-analysis similar to that which in theory is typing, naming and propagating in this code block.

```
loc_0_0000022C:
	lea.l loc_0_00000492(pc),a0
	move.w d1,$0004(a0)
	move.w d0,$0006(a0)
	move.w d2,$000C(a0)
	move.b loc_0_00000027(pc),d0
	move.b $0147(a6),d1
	eor.b d1,d0
	moveq.l #1,d1
	and.l d1,d0
	eor.b d1,d0
	move.l d0,loc_0_000004BA.l
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOOpenScreen(a6)
	movea.l (a7)+,a6
	move.l d0,app_00CE(a6)
	beq.w loc_0_000003EA
	movea.l d0,a1
	lea.l loc_0_000004CA(pc),a0
	move.l a1,$001E(a0)
	moveq.l #1,d1
	add.b sc_BarHeight(a1),d1
	move.l loc_0_00000496(pc),$0004(a0)
	move.w d1,$0002(a0)
	sub.w d1,$0006(a0)
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOOpenWindow(a6)
	movea.l (a7)+,a6
	move.l d0,app_05B4(a6)
```

## Amiga/Pandora resolved notes

This section tracks current general-analysis follow-ups that use Pandora as concrete evidence. Proposal 015 is closed as
the historical Pandora reversing-loop trial; these entries should be resolved as reusable C analysis/rendering work
unless the evidence proves a genuinely target-specific Pandora artifact.

### Address classification and labelisation

These are address looking values that likely fall within known ranges, and are also extracted out and used as addresses.
This is a good start to knowing to render them as labels.

```
	movea.l abs_0_0005CA6C(pc,d0.w),a0
abs_0_0005CA64:
	jsr abs_0_000199DE.l
	rts
abs_0_0005CA6C:
	dc.l $0005CCF5,$0005CD0B,$0005CD25,$0005CD3E	; lookup_table
	dc.l $0005CD57	; lookup_table
```

Resolution note: one general renderer/analysis gap is fixed here. C-owned absolute long lookup tables now run through
the same target-label materialization pass as pointer tables, so a table can create renderable labels for mapped data
targets before the `dc.l` row is emitted. This lets lookup-table values become symbolic label expressions instead of
remaining numeric only because the target had no pre-existing label. Covered by
`facts_v2_absolute_long_lookup_table_adds_data_target_labels`. This does not claim the separate byte-emitted dispatch
table at `lookup_table_00020CA0` or the base-plus-word `jmp $0(a3,a2.w)` form.

### Auto-analysis failures

General jump table processing. This table was the evidence case for processing absolute-address tables like other
pointer tables, mapping entries into known address ranges and inferring code blocks at each address.

```
	add.w d2,d2
	add.w d2,d2
	movea.l lookup_table_00020CA0(pc,d2.w),a1
	adda.w d0,a0
	jmp (a1)
lookup_table_00020CA0:
	dc.b $00,$01,$0C,$C0,$00,$01,$0C,$CC,$00,$01,$0C,$D8,$00,$01,$0C,$E4
	dc.b $00,$01,$0C,$F0,$00,$01,$0C,$FC,$00,$01,$0D,$08,$00,$01,$0D,$14
```

It is even possible that it is generating labels for those addresses already, but not rendering the data block
as the labels. This label is not found anywhere.

```
abs_0_00010CC0:
	bclr.b d1,(a0)
	bclr.b d1,$0028(a0)
	bclr.b d1,$0050(a0)
	jmp (a3)
```

Resolution note: the `lookup_table_00020CA0` shape is covered by a general C classifier fix. Indexed local long
pointer-table detection now accepts a bounded gap between the table load and the indirect `jmp`/`jsr` when each
intervening instruction preserves the loaded address register. This matches `movea.l table(pc,d2.w),a1`;
`adda.w d0,a0`; `jmp (a1)` without hardcoding Pandora. The table then renders as `dc.l` label entries and the targets
are materialized through the existing pointer-table target-label path. Covered by
`facts_v2_indexed_local_base_pointer_table_survives_preserving_gap`. The base-plus-word dispatch below is a separate
word-relative table form and is covered by the later resolution note.

Another jump table. In this case it is more complex and tracking registers may be harder and better to defer?

```
abs_0_0005DC20:
	add.b d0,d0
	lea.l abs_0_0005DCE8(pc),a2
	movea.w $0(a2,d0.w),a2
	jmp $0(a3,a2.w)
```

Resolution note: the base-plus-word form is now handled in the general C facts/render path when the table base and
target base are both proven. Indexed word-table loads may carry a word-relative table value in either a data register
or an address register, and indexed `jmp`/`jsr` operands consume that value using the actual index register kind. This
matches the `movea.w $0(a2,d0.w),a2`; `jmp $0(a3,a2.w)` shape without a Pandora-specific rule. The renderer uses the
same proof to emit `dc.w target-base` table rows instead of raw bytes. Covered by
`facts_v2_address_register_index_word_load_promotes_relative_jump_targets`.


## Amiga/Magicland Dizzy resolved and deferred notes

### Memory map and absolute addresses

The source header now renders an absolute-memory overview for the user working with the restored source. The C analysis
detects accepted absolute address access, maps ownership, summarizes address spans, and promotes safe operands to stable
generated symbols. Stronger lifetime/size/semantic names still require additional proof.

```
	lea.l abs_0_00062205(pc),a0
	lea.l $00006F50.l,a1
	trap #3
	lea.l abs_0_00064CD8.l,a0
	lea.l $00032DD0.l,a2
	lea.l $0004B470.l,a3
	lea.l $0002F490.l,a4
```

Illustrative of gaps in our analysis of absolute addresses is also this snippet:

```
abs_0_0005C3E6:
	move.l #$70152,$012A.w
	move.l #$78152,$0126.w
	move.l #$D40,$0132.w
	move.l #$1140,$012E.w
```

Progress note: low absolute RAM slots in runtime-mapped sections are no longer misclassified as section storage just
because the numeric address is less than the section size. The C facts path now only falls back to `section_storage`
for unrelocated absolute operands when the section has no runtime address range; relocated operands still keep their
explicit section-storage owner. Magicland's example addresses now classify as `absolute_memory`: `$0126` (10 refs),
`$012A` (21 refs), `$012E` (4 refs), `$0132` (6 refs), `$00006F50` (14 refs), `$0002F490` (2 refs), `$00032DD0`
(1 ref), and `$0004B470` (1 ref). Covered by
`facts_v2_runtime_mapped_section_keeps_low_absolute_refs_absolute` and `cmd /c src\precommit.bat m68k_ir`.
Progress note: the rendered source header now includes a bounded, coalesced `Absolute memory refs` subsection built
from accepted C decode candidates. It summarizes absolute RAM ranges by address span, reference count, and read/write/
address-use kind, while filtering platform hardware and low address-only constants out of the overview. The Magicland
header now exposes the low RAM slot cluster (`$00000112-$00000318`) and high buffer/pointer addresses such as
`$0002F490`, `$00032DD0`, and `$0004B470` directly in the human-facing memory map. The later resolution notes promote
ordinary absolute memory operands to stable generated slot symbols where the C owner model proves they are safe.
Stronger semantic names and size/lifetime evidence still require analysis proof, not address-span summaries alone.

Resolution note: repeated low absolute RAM operands now render through stable generated symbols when the C owner model
proves they are absolute memory, not hardware registers, CPU vectors, section storage, or materialized runtime ranges.
The Magicland setup above now renders as `absolute_slot_0000012A.w`, `absolute_slot_00000126.w`,
`absolute_slot_00000132.w`, and `absolute_slot_0000012E.w`, with matching `EQU` declarations in the source header.
This is a general renderer/facts improvement, not a Magicland-specific rule. Covered by
`facts_v2_render_asm_source_symbols_low_absolute_memory_slots`, `cmd /c src\precommit.bat m68k_ir`, and regenerated
`targets/amiga_hunk_magicland_dizzy_md/magicland_dizzy_md.s`. Stronger semantic names and lifetime/size evidence for
those slots remain future type-propagation work unless a later analysis pass proves their roles.

Resolution note: absolute long address-use operands now share the same stable generated-symbol path when the C owner
model proves an ordinary absolute-memory range. This covers Magicland-style setup operands such as `$00006F50.l` and
`$0002F490.l` without inventing target-specific names. The address-use pass runs after stronger semantic renderers and
skips existing instruction/platform annotations, so stack-top setup, bitmap/display memory comments, hardware, vectors,
and materialized runtime labels keep their more specific rendering. Covered by
`facts_v2_render_asm_source_symbols_absolute_address_uses`, the existing stack-top and bitmap memory render tests, and
`cmd /c src\precommit.bat m68k_ir`.

### Disk access

The standalone `amiga_hunk_magicland_dizzy_md` target remains a hunk file project. A source disk is now available in the
local corpus as `resources/platform_amiga/Magicland Dizzy (1991)(Codemasters)[cr TRSI][t +2 LSD].zip`, and a disk-project
baseline has been imported as `targets/amiga_disk_magicland-dizzy-1991-codemasters-trsi-lsd/` with the `MD` executable
child rendered at `targets/amiga_disk_magicland-dizzy-1991-codemasters-trsi-lsd/targets/amiga_hunk_md_e066dc14/md.s`.
The broader disk-access/child-payload mapping remains deferred until analysis can bind track reads to exact disk bytes
and payload roles without guessing.

```
abs_0_000646BA:
	btst.b #CIAB_DSKTRACK0,_ciaa+ciapra.l
```

This is a target/sub-target parent/child project relationship candidate. We currently in the web UI for project
browsing show hierarchical target relationships, where we might have an executable which is a decompressor/payload
wrapper, then we show as child the decompressed payload and both are sub-targets of perhaps the disk project. If
we are able to relate disk access routines to where they access and how much they read, and get back the disk
data we can then treat it as child payloads of the target that read it. This might be depending on how it is referenced
even auto-analysable as code leads with implied entrypoints and register sets, or data, maybe textual or graphical.

Resolution note: the actionable source-quality part is now covered by the current C analysis/render path rather than a
Magicland-specific post-process. Regenerating the target with the current engine renders the disk helper through
platform hardware names: `_ciaa`/`_ciab` register bits, `dmacon`, `adkcon`, `dsksync`, `dskpt`, `dsklen`, and `intreq`,
including `dskpt(a6)` as a `disk_buffer` pointer sink. That makes the disk DMA setup, sync word, ready/block polling,
and read length visible from accepted instructions in the source. The newly imported disk project supplies the durable
parent/child target scaffold for future work, but the correct child-payload work still needs a general external-resource
relationship model that proves which disk bytes each routine reads and how those bytes should be interpreted.

### Unrecognised decompression routine

Decompression routine at `abs_0_000647F2`? It makes sense that this is placed near the disk access, and it likely
follows data loading from tracks and MFM decoding.

There is a general project here which likely relates to platforms, but is not necessarily platform specific except
for classification of where has been found or is likely to be found. A lot of these decompression routines will be
iterations on standard compression approaches, if not direct adaptations of pre-existing routines. If we can
heuristically identify these, their inputs, outputs and perhaps even type of compression, we can then perhaps
reliably hook into them and simulate them to pass in compressed payload and get out the decompressed original
data. 

Resolution note: this is now understood well enough not to force it through the existing executable self-decrunch child
path. The routine is reached from the trap #3 loader after the loaded block is checked for long magic `$4D4C4443`
(`MLDC`), copies from the packed block at `a0`, writes output through caller-provided `a3`, and returns to the parent
flow. That is an asset/data decompressor shape, not the current C self-decrunch event shape that writes an executable
runtime image and transfers into it. Current `analyze-file amiga-hunk bin\MagiclandDizzy_MD_f26cb8133afe` therefore
emits no `decompression_events`, which is correct for the existing model. The clean future work is a general C
asset-decompression evidence model with packed-source provenance from the disk/resource loader and an accepted codec
provider or simulator entry contract. For this hunk-only target, the source media/packed block bytes are not present,
so materializing decompressed children here would be guessed and is intentionally deferred.

### String decode heuristic fail

This maps to a lookup table of strings and correctly reconciles strings, but seems to stop before the end.

```
abs_0_00064398:
	dc.w $000C,$02A0	; lookup_table
	dc.b "MAGICLAND DIZZY!",$00	; string
	dc.b $00,$00,$05,$15,$00
	dc.b "AMIGA AND ST VERSIONS CODED BY",$00	; string
	dc.b $00,$00,$09,$1C,$E0
	dc.b "DEREK LEIGH-GILCHRIST.",$00	; string
	dc.b $00,$00,$0D,$31,$E0
	dc.b "ALL ARTWORK BY",$00	; string
	dc.b $00,$00,$0C,$39,$C0
	dc.b "LEIGH CHRISTIAN.",$00	; string
	dc.b $00,$00,$00,$76,$20,$43,$4F,$50,$59,$52,$49,$47,$48,$54,$20,$31
	dc.b $39,$39,$31,$20,$43,$4F,$44,$45,$4D,$41,$53,$54,$45,$52,$53,$20
	dc.b $53,$4F,$46,$54,$57,$41,$52,$45,$20,$4C,$54,$44,$2E,$FF,$00
```

Resolution note: the general C structured-data string classifier now handles this record shape without a
Magicland-specific address rule. A plain ASCII string may start after a printable separator byte only when the same
section already has a nearby sequence of prior structured strings and the nearest short separator contains control
bytes. This keeps the normal mid-string split guard intact while allowing the final `COPYRIGHT 1991 CODEMASTERS
SOFTWARE LTD.` record to render as byte-preserving quoted source. Covered by
`facts_v2_control_separated_ascii_sequence_keeps_printable_separator_tail`.

## Hand notes

### Guided user reviews

I've become convinced that a reverse engineering tool has the ability to do a set of minimal things that can streamline the experience for users.

- Use heuristics to judge whether data is likely to be code as a building block.
- Use heuristics to identify orphan code blocks and use that to aid in correct analysis.

### Implementation mistakes

Fixed capacities were used for tables of various kinds and data that fell outside were truncated from one or both of analysis or enhanced non-data rendering. There never should have been fixed capacities and the presence of fallback for failure is a failure in and of itself. We should never have used fixed capacities and if we did, encountering the limit should be a failure case that requires the code to be refactored to remove them.
