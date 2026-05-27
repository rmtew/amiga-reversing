# TODO

## Rendered source round-trip priority

Direct rebuild exactness is a tooling-quality signal: it proves the loader, internal model, and rebuilder can preserve
the original bytes without passing through the human-facing `.s` file. It is not the completion criterion for restored
source.

The core target is rendered source round-trip exactness:

1. Rendered source exact at container level where the original file shape can be reproduced by the standard assembler
   and standard container writer.
2. Rendered source exact at content level where code/data bytes are exact but the original container uses odd ordering,
   padding, relocation encoding, or auxiliary layout that should be classified rather than copied with per-target
   workarounds.
3. Direct rebuild exact only is insufficient except as a diagnostic that remaining defects are in source rendering,
   assembly, or supported container output.
4. Assembler errors and source byte mismatches are active defects unless the verifier can prove and report an explicit
   unsupported container-only reason.

Current `.s` target status:

- `amiga_hunk_genam`: direct rebuild exact and rendered source exact. This is the reference success state.
- `amiga_hunk_monam302`: direct rebuild exact, rendered source assembles but has 111 diff ranges. Fix source
  rendering/assembler exactness before treating it as complete.
- `amiga_hunk_bloodwych`: direct rebuild exact, rendered source currently fails assembly on
  `abs_0_00008ECC`. Fix label/materialized-address emission generally; do not add a Bloodwych-only symbol workaround.
- `amiga_disk_magicland-dizzy-1991-codemasters-trsi-lsd__amiga_hunk_md_e066dc14`: direct rebuild exact, rendered
  source assembles but has one diff range. Determine whether that is a real source defect or a classified
  container/content distinction, then make the verifier say which.
- `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`: rendered source fails assembly on
  `abs_0_0005CCF5`. This remains a general absolute/runtime label materialization or data-block splitting defect, not a
  Pandora-specific patch point.
- `macos_hfs_mpw_gm__macos_file_mpw_tools_asm`: round-trip unsupported until the Mac target has a resolvable
  `source_binary.json` and assembler/container support. Keep Mac `asm.s` out of the Amiga round-trip success claim.

Acceptance rule: prefer standard, reusable assembler/container behavior. If exact container reproduction is impossible
or not worth supporting for a non-standard input shape, record a content-exact result with an explicit structural reason
instead of adding target-specific rebuild behavior.

## Amiga/Pandora resolved notes

This section tracks current general-analysis follow-ups that use Pandora as concrete evidence. Proposal 015 is closed as
the historical Pandora reversing-loop trial; these entries should be resolved as reusable C analysis/rendering work
unless the evidence proves a genuinely target-specific Pandora artifact.

### Orphaned label definitions

`abs_0_00056218` has no accesses only a definition. This reflects a lack of awareness of why we are emitting these
orphaned labels and what it means with respect to our analysis being correct. Are we identifying absolute address
references perhaps and not substituting the in-segment/bootstrapped range label for that address at point of access?

Resolution note: generated labels now separate expression eligibility from standalone label-statement emission in the
C renderer. A local address may still be usable in symbolic operands or table rows, but it is only emitted as a
definition when accepted code, explicit naming, relocation/storage data, sink-backed runtime data, or a proven
structured table needs that source label to exist. PC-relative xrefs are now harvested only from accepted candidates,
so raw-data decode candidates cannot manufacture label definitions. Runtime refs that render as alternate external
runtime symbols no longer force unrelated source-offset labels. Covered by `render_ir_suppresses_orphan_structured_field_label`,
existing runtime/table/copper render tests, `cmd /c src\precommit.bat m68k_ir`, and a Pandora raw render check showing
`abs_0_00056218:` count `0`.

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
