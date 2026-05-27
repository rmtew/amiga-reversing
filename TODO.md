# TODO

## General notes

- General auto-analysis of jump tables and symbolising tables with relative or absolute labels works well and is
  triggered for targets in different platforms. We should go through all known targets and prove out the viability
  of processing cases correctly where we do not already. We should already know the locations. This is a C auto-analysis
  thing. It should be done cleanly and generally for all platforms.
- Absolute address detection and processing. This is an incomplete area and all targets that use them (especially
  bootstrapped and/or decompressed payloads like Pandora or Bloodwych) need better handling in a clean general
  way helping users get a restored source that undoes the memory dump like nature of the presence of those absolute
  addresses.
- Label correctness. Generally Amiga and Atari ST are round-trip supported, so we know that the label accesses must
  be correct or the round-trip assembly should fail. However we do see labels being emitted that have no visible
  accesses.
- Type propagation. If we know from analysis what the type of some data is, that data location should be added to the
  pending auto-analysis set for processing. All accesses should respect that type, and the changing of the type at
  all surfaced references should make the expected auto-analysis changes. This should happen for Amiga library call
  arguments which we know by register and type from KB data, and it should happen for MacOS OS calls which we should
  have the metadata for from it's own KB and parsed include files and generated C .c/.h metadata similar to Amiga.

Current status map:

- Jump-table auto-analysis: the Pandora absolute-long, local indexed-long, and base-plus-word cases are now covered by
  reusable C facts/render tests. Remaining work should be driven by new target evidence, not another Pandora-specific
  rule.
- Absolute address processing: Magicland low absolute RAM classification, source-header summaries, and stable generated
  low-slot symbols are covered. Stronger semantic names/lifetimes remain future type-propagation work unless the
  analysis proves roles.
- Label correctness: the known Pandora orphan-label case is covered by the generated-label emission split. New label
  issues should be reduced to expression eligibility versus standalone definition proof.
- Type propagation: Amiga/Atari-style platform call/type propagation remains the general model. Mac `_GetFNum` now has
  generated metadata, stack-argument binding, and an output-pointer local typed-access bridge. Mac A5-world slot typing
  is intentionally not closed until accepted A5 lifetime evidence can connect ordinary instruction reads/writes to the
  signed A5 storage-layout regions now carried by C analysis.

## Investigation needed: MacOS/MPW asm

We don't support the way that official MacOS .a files work. This is to limit the investment of MacOS targets to
that required to support Amiga developers who might want to port a project to the Amiga. This means that if we need
to define something like structs and data types in ranges, we might do so with the Amiga structs and RSSET ranges
for now.

### System calls

We recognise what seem to be system calls.

```
CODE_1_loc_0000207e:
	move.w (a0)+,(a1)+
	dbf.w d0,CODE_1_loc_0000207e
	pea.l -$0100(a6)
	pea.l -$0102(a6)
CODE_1_data_0000208c:
	_GetFNum
	move.w -$0102(a6),$000C(a6)
	unlk a6
	move.l (a7)+,(a7)
	rts
```

In this case, presumably we know the input registers to _GetFNum or what is expected on the stack. Similar to Amiga
or Atari potentially in that we should be able to do type inference on the inputs and outputs. Amiga and Atari and
MacOS should have data on these calls and their inputs and outputs garnered from includes and other platform data
sources into the knowledge base as JSON which is used to generate platform-specific includes. This should be extended
to give us type analysis.

`_GetFNum` is present in the MPW GM interfaces, but not where a quick top-level glance tends to find it. It is in
`ext\macos_includes\mpw_gm\Interfaces\AIncludes\Fonts.a` as an `OPWORD $A900` macro, with the adjacent interface
comment:

```
; pascal void GetFNum(ConstStr255Param name, short *familyID)
```

The C interface in `ext\macos_includes\mpw_gm\Interfaces\CIncludes\Fonts.h` gives the same shape:

```
GetFNum(ConstStr255Param name, short *familyID) ONEWORDINLINE(0xA900)
```

So the example is not an unknown instruction or a guessed API. The call site prepares a copied Pascal string at
`-$0100(a6)`, pushes that address, pushes `-$0102(a6)` as an output pointer, executes `_GetFNum`, then copies the
returned font family ID from `-$0102(a6)` into the caller-visible word at `$000C(a6)`.

The nuance for doing this right is that Mac trap knowledge is more than trap-name rendering. We need a generated Mac
OS/Toolbox call table with the trap word, include source, Pascal calling convention shape, parameter order, stack
widths, pointer/reference direction, and return/value effects. That data should drive the C analysis in the same
spirit as the Amiga and Atari platform call metadata. Once `_GetFNum` is represented structurally, the analysis should
be able to infer that `-$0100(a6)` is a `ConstStr255Param`, `-$0102(a6)` is a writable `short *familyID`, and
`$000C(a6)` receives a `FontFamilyID`-like value. The rendered source should then become clearer because the structured
call semantics, not comments or Python-side recognition, explain the stack slots.

Resolution note: generated Mac OS runtime metadata now carries structured C prototype fields for calls, including
`c_name`, `return_type`, and per-parameter rows with source order, type name, pointer depth, and direction. `_GetFNum`
is therefore represented as `void GetFNum(ConstStr255Param name, short * familyID)` from `Fonts.a`/`Fonts.h`, with the
font name as an input value and `familyID` as an output-or-inout pointer. This metadata is now consumed by the C
analysis bridge described below; this note is the source-data proof, not an open blocker by itself.

Progress note: reached Mac opword calls now expose those generated parameter rows through the recovered platform-call
JSON/API surface. The `_GetFNum` C regression renders the real `Fonts.a` include and `_GetFNum` macro, records the
reached platform call, and serializes `name: ConstStr255Param` plus `familyID: short *` with
`output_or_inout_pointer` direction instead of leaving Mac call `inputs` empty. Covered by
`facts_v2_macos_opword_call_falls_through` and `cmd /c src\precommit.bat m68k_ir`. The later C data-flow bridge work
now binds the observed `pea -$0100(a6)`/`pea -$0102(a6)` stack operands to those parameter rows and propagates the
output-pointer local read into a typed access fact.

Progress note: the first C data-flow bridge now records reached Mac stack arguments as recovered function-arg facts
directly from generated Mac runtime metadata. For the `_GetFNum` pattern, the opword call at payload offset 12 records
`name: ConstStr255Param` at call-stack offset 8 and `familyID: short *` at call-stack offset 4, including the
`output_or_inout_pointer` direction from the generated metadata. Covered by
`facts_v2_macos_call_stack_args_from_generated_metadata` and `cmd /c src\precommit.bat m68k_ir`. The same fact now binds
each parameter to the concrete pushed local-frame operand: `name` comes from `-$0100(a6)` and `familyID` comes from
`-$0102(a6)`. The output-pointer bridge now also records the later `move.w -$0102(a6),...` read as a typed local access:
`familyID` is read as a two-byte `short` with API-output provenance pointing back to the `_GetFNum` call. This keeps the
fact in C-owned source analysis rather than a rendered-source comment. Covered by the same regression and
`cmd /c src\precommit.bat m68k_ir`.

There is also an include/rendering distinction to preserve. The assembly source should include the real MPW interface
file that defines `_GetFNum` (for example `Fonts.a`, with whatever umbrella include policy we settle on), not emit local
EQU-style replacement definitions. The metadata generator can consume `Fonts.a`/`Fonts.h`, but the restored source
should remain source-compatible with the MPW assembler include style.

Resolution note: the committed MPW Asm artifact now renders MPW interface includes in header material before CODE 0,
including `Fonts.a`, `SegLoad.a`, `Traps.a`, and related interface files. `_GetFNum` and `_LoadSeg` are therefore
provided by real MPW include material in the restored source rather than local EQU hacks. This is intentionally a source
presentation concern; the call metadata remains generated from parsed Mac interface data for C analysis.

### A5 data storage

There seems to be data storage in negative A5 offsets. In this case we are using addresses in there as input on the
stack, and then using the output in one of those addresses. It appears to be moved into positive offsets under the
jump table (given we know the jump table offset is defined in the leading data as $20 in some standard location).
In this snippet the base register is `a6`, because the function has just done `link a6,#-258`. That makes the
`-$0100(a6)` and `-$0102(a6)` slots stack-frame locals, not A5-world globals. It is still useful evidence because it
shows the kind of type propagation Mac call metadata should enable: a stack local becomes a Pascal string buffer, a
neighboring word becomes an out-parameter destination, and the result is copied to another frame slot.

```
CODE_1_loc_0000207e:
	move.w (a0)+,(a1)+
	dbf.w d0,CODE_1_loc_0000207e
	pea.l -$0100(a6)
	pea.l -$0102(a6)
CODE_1_data_0000208c:
	_GetFNum
	move.w -$0102(a6),$000C(a6)
	unlk a6
	move.l (a7)+,(a7)
	rts
```

The actual A5-world issue is separate. CODE 0 gives the application A5 layout:

```
CODE_0_above_a5_size:
	dc.l $00000AF0
CODE_0_below_a5_size:
	dc.l $00003920
CODE_0_jump_table_length:
	dc.l $00000AD0
CODE_0_jump_table_offset_from_a5:
	dc.l $00000020
```

The C parser already reads these fields from CODE 0 (`above_a5_size`, `below_a5_size`, `jump_table_length`,
`jump_table_offset_from_a5`). Before the current structured packet work, the restored-source packet emitted this only
as deferred platform context:

```
"a5_world":{"status":"deferred","source_visible":true,...}
```

That proved the A5 world was real and visible in the file format, but it did not promote it to a typed storage model.
Doing that correctly still needs a Mac platform storage domain in the C analysis, analogous to app/global slots
elsewhere, with positive A5 offsets distinguished from negative A5 offsets and stack-frame offsets.
Positive A5 offsets may address the jump table or app globals; negative offsets are not automatically the same thing,
and local `a6` frame offsets are a third case. The work should avoid collapsing all displacements into a single
"A5 data" bucket just because the rendered code is Mac.

The useful target state is that when a trap or normal instruction reads/writes a proven A5-world slot, the C facts carry
the base register, displacement, width, type, provenance, and lifetime confidence. That gives us cross-references and
names which can survive source edits. Free-form comments are not enough; the point is to make the storage model usable
for type propagation and rendering.

Resolution note: the restored-source packet now exposes CODE 0's parsed A5-world layout as structured C-owned platform
data instead of only a vague deferred placeholder. CODE 0 reports negative A5 globals, the positive A5 jump-table
window, and positive globals after the table, all with `a5` base-register coordinates. Nonzero CODE resources reference
CODE 0 as the owner of that layout. This intentionally keeps lifetime proof and slot type propagation deferred: the
current evidence proves the storage windows, not which function has A5 live or which individual slots hold typed values.
Mac trap metadata now creates typed stack/local facts for reached stack-parameter calls such as `_GetFNum`; A5-world
slot typing remains separate and requires accepted A5 lifetime evidence plus normal instruction reads/writes against
the CODE 0 storage windows. Do not infer A5 globals from `a6` frame locals.

Audit note: C source analysis now receives CODE 0 A5-world layout as `M68kObject` platform storage metadata and projects
it into source-analysis `platform_storage_layout` records. That closes the old carrier gap. A5-world slot typing still
cannot be completed by the same path used for `_GetFNum` stack locals, because the current evidence proves storage
windows, not that A5 is live at a specific ordinary instruction or that an accessed slot has a known type. The next
correct implementation step is lifetime/type proof over accepted instructions that read or write offsets inside those
regions. A renderer-only or Python-only A5 slot inference remains explicitly rejected.

Follow-up audit: the existing `M68kBaseLayoutFieldIR`/app-slot model is not the right carrier for this. It currently
models app-base storage with app-style symbols and conflict rules, while Mac CODE 0 proves three distinct A5 regions:
below-A5 globals, the positive jump-table window, and positive globals after the table. Reusing the Amiga app-layout
path would hide those distinctions and make later type/lifetime propagation less correct. The clean implementation
needs a Mac platform-data payload on `M68kObject` (populated from the enclosing CODE 0 resource, not guessed from the
selected CODE bytes) and a platform storage-layout IR that can describe signed A5-relative regions before individual
slot types are inferred.

Progress note: `M68kObject` now has a Mac platform-data carrier for CODE 0 A5-world layout. The carrier derives the
signed below-A5 global range, positive jump-table window, and positive global tail from parsed CODE 0 metadata and
rejects non-CODE0 metadata rather than guessing from selected CODE bytes. Covered by
`object_a5_world_layout_uses_code0_metadata`, `object_a5_world_layout_rejects_non_code0_metadata`, and
`cmd /c src\precommit.bat m68k_ir`.

Progress note: selected Mac HFS CODE listing artifacts now build in C from the enclosing HFS/resource-fork context,
not from detached CODE bytes. The artifact extracts the selected nonzero CODE executable span, attaches the CODE 0
A5-world layout to the `M68kObject`, and serializes `macos_a5_world_layout` in the analysis JSON. Context-free Mac CODE
byte artifacts still report `macos_a5_world_layout: null`, which prevents accidental guessing from incomplete bytes.
Covered by `test_021_007_macos_hfs_code_artifact_carries_code0_a5_world_layout`,
`tests/test_macos_c_backend.py`, and `cmd /c src\precommit.bat m68k_ir`.

Resolution note: the carried CODE 0 A5-world layout is now projected into source-analysis memory-layout records as a
generic `platform_storage_layout` IR, not as an Amiga app/base layout and not through a Mac renderer shortcut. Mac
populates generic `M68kObject` platform-storage rows for below-A5 globals, the A5 jump-table window, and above-A5
globals; the C facts pipeline copies those rows into `memory_layout_records` with signed A5 coordinates. Covered by
`facts_v2_macos_a5_world_layout_reaches_source_analysis`,
`test_021_007_macos_hfs_code_artifact_carries_code0_a5_world_layout`,
`tests/test_macos_c_backend.py`, and `cmd /c src\precommit.bat m68k_ir`. Remaining work is A5 lifetime/type
propagation: only accesses proven to have A5 live should become typed A5 storage facts.


### Pascal strings

Resolution note: current Mac artifact rendering emits byte-preserving quoted source, for example
`dc.b $87,"GETRSRC",$00,$00`, instead of leaving those rows as opaque hex bytes. The first fix used the Mac target
artifact bridge; the durable fix now lives in the C auto-data pass as `macos_symbol_string` structured rows with
`macos_symbol_record` provenance. Remaining broader work is to move other proven string classifications into C-owned
structured rows where possible, especially for non-Mac targets and record shapes beyond this high-bit Mac symbol case.

Audit note: the general C path already owns ordinary length-prefixed ASCII records when the byte stream proves a safe
sequence, and it renders them from structured row roles rather than label text. Covered by
`facts_v2_length_prefixed_ascii_sequence_renders_strings`,
`facts_v2_length_prefixed_ascii_sequence_respects_code_overlap`, and the existing ASCII/string-sequence regressions.
The Mac `$87,"GETRSRC"` / `$8A,"GETFONTNBR"` rows are deliberately not promoted by the generic scanner: the high bit is
format-specific symbol-record state, not a plain Pascal length byte. Resolution note: the C auto-data pass now has a
Mac-gated `macos_symbol_string` structured-data role for high-bit length/control symbol records. It emits first-class
structured rows with `string` and `length_prefixed_string` roles plus `macos_symbol_record` source-pattern provenance,
renders them as byte-preserving quoted `dc.b` rows, and does not promote the same bytes on Amiga/Atari backends. Covered by
`facts_v2_macos_highbit_symbol_string_renders_structured_data`,
`facts_v2_highbit_symbol_string_is_not_generic_pascal`, and `cmd /c src\precommit.bat m68k_ir`. Broader string cleanup
remains about other proven string/data forms, not this Mac high-bit symbol-record case.

If we know a string is a string of some sort, we should display it as the restored source should see it: textual where
the bytes prove a textual representation, raw/residual where they do not. This is a general structured-data concern,
not just MacOS. The Mac high-bit symbol-string examples below are now covered by C-owned structured rows; other targets
or record shapes still need evidence-driven generalization rather than label-text heuristics.

```
CODE_1_data_pascal_string_00002066:
	dc.b $87,$47,$45,$54,$52,$53,$52,$43,$00,$00
```

The old failure was that the label said `pascal_string` while the bytes remained opaque. The fixed path no longer uses
the label as proof. `$87` is not a normal seven-bit length byte; it is the high bit set on a length-like value. Nearby
examples such as `$8A,$47,$45,$54,$46,$4F,$4E,$54,$4E,$42,$52...` show the same pattern around trap names like
`GETFONTNBR`. That is why the generic scanner still refuses broad high-bit Pascal promotion: these are Mac symbol/name
records with flag bits or tool-specific metadata around a Pascal-style string.

The clean direction is to make string rendering driven by structured data class, not label text. A row should know
whether it is a C string, Pascal string, fixed string field, symbol record, or unknown byte sequence. Then the renderer
can choose source forms like a length byte plus quoted text, raw bytes for non-text flag fields, and explicit residual
bytes for padding. That should be general across Amiga, Atari, and Mac where the data model can prove the string kind.

For Mac specifically, the classifier should not erase the work-in-progress signal. If a region is only a candidate
Pascal/string record, the rendered source can still be more readable, but the row metadata must preserve that it is not
yet a fully understood Toolbox string object. The important invariant is byte preservation and reassemblability first,
then readable quoted text where the structured row proves the representation.

### A5 calls and the jump table

There are several lines of leading data implying use of A5 and placement of the jump table in the positive offsets
of what is kept in A5:

```
CODE_0_above_a5_size:
	dc.l $00000AF0
...
CODE_0_jump_table_length:
	dc.l $00000AD0
CODE_0_jump_table_offset_from_a5:
	dc.l $00000020
```

Then there are calls into positive A5 offsets littered throughout the code:

```
CODE_1_loc_0000043c:
	move.w d0,-(a7)
	jsr $078A(a5)
```

This implies that we can in theory refer to jump table entry calls based on the label we place for an entry in the
jump table. It seems to be derived using a formula like value in `CODE_0_jump_table_offset_from_a5` +
(table_offset - start_of_table).

The current renderer already exposes CODE 0 as a table of entries:

```
CODE_0_jump_table:
CODE_0_jump_table_entry_0:
	dc.w $0000
	move.w #27,-(a7)
	_LoadSeg
CODE_0_jump_table_entry_1:
	dc.w $0000
	dc.w $FFFF
	dc.l $00000000
CODE_0_jump_table_entry_2:
	dc.w $0001
	_LoadSeg
	dc.l CODE_1_loc_0000601e-CODE_1
```

The C packet also emits `code0_routing_table` and `code0_dispatch_reference` records, and tests currently treat the
routine offsets as candidate records rather than accepted byte-entry proof. That is the right caution: the segment
table shape and CODE resource routing are accepted parser output, but individual routine entry semantics still need to
come from actual entry spans and flow analysis.

The required bridge from positive A5 calls to these table rows is the table-window lookup described below. Calls like:

```
	jsr $078A(a5)
```

should be resolvable when `$078A` lands inside the proven CODE 0 jump table window. Given
`CODE_0_jump_table_offset_from_a5 == $20`, the table-relative offset would be `$078A - $20`, and with 8-byte entries
that should identify a specific `CODE_0_jump_table_entry_N` if the offset is aligned and in range. The rendered call
should then use the symbolic entry label, and the analysis should record the xref from the call site to the jump-table
entry and from that entry to the target CODE resource/routine when proven.

Resolution note: the table-entry relation is now carried as C-owned platform data on generated routine candidates:
`a5_entry_offset`, `a5_callable_offset`, `callable_entry_byte_offset`, and `callable_entry_kind`. This deliberately
does not claim byte-entry proof for target routines, because `$078A` is not an entry-start displacement in the current
fixture; it lands two bytes into a proven 8-byte CODE 0 entry, on the Segment Loader trap word. The Mac artifact bridge
now consumes those C-emitted callable-slot facts when semantic source rows contain `jsr`/`jmp disp(a5)`. Proven callable
slot displacements render as source-stable table expressions such as
`CODE_0_jump_table_entry_237+2-CODE_0_jump_table+CODE_0_jump_table_a5_offset(a5)`; unresolved, duplicate, malformed, or
out-of-table A5 control transfers remain numeric. Covered by
`test_macos_semantic_row_text_rewrites_proven_a5_callable_slots`,
`test_committed_macos_subtarget_metadata_and_asm_shape`, and the committed MPW Asm artifact, which no longer contains
the raw `jsr $078A(a5)` example.

The ownership boundary remains the C analysis/platform layer, not a Mac source post-processor. A5-relative control
transfers are ordinary M68K operands plus Mac platform context, so the renderer may only consume C-owned callable-slot
facts and must not infer table membership from label text. Non-call A5 accesses remain separate: some positive offsets
may be globals, some are jump-table entries, and malformed or out-of-range offsets stay numeric with a residual/
unresolved fact rather than guessed labels.

There is also a source-restoration nuance for the table itself. The `dc.l CODE_1_loc_...-CODE_1` form is better than
absolute numeric offsets because it remains edit-friendly if source moves. The same principle should apply to any
derived A5-call rendering: prefer symbolic table-entry labels and segment-relative expressions where they are proven,
while keeping raw numeric data where the parser cannot prove the relationship.

## Investigation needed: Amiga/Pandora

This section tracks current general-analysis follow-ups that use Pandora as concrete evidence. Proposal 015 is closed as
the historical Pandora reversing-loop trial; these entries should be resolved as reusable C analysis/rendering work
unless the evidence proves a genuinely target-specific Pandora artifact.

### Register content propagation

Note that here we store code pointers in locations like `app_0360`. These get called with predictable register
contents like `_custom` in `a5`. The original failure was that `_custom` did not propagate consistently to relevant
locations in Pandora; this remains useful as evidence for the general register-tracking fix recorded below.

```
abs_0_00010A72:
	lea.l abs_0_000134C2.l,a0
	move.l (a0)+,$0180(a5)
	move.l (a0)+,$0184(a5)
	move.l (a0)+,$0188(a5)
	move.l (a0)+,$018C(a5)
	move.l (a0)+,$0190(a5)
	move.l (a0)+,$0194(a5)
	move.l (a0)+,$0198(a5)
	move.l (a0)+,$019C(a5)
	lea.l abs_0_00010AA2(pc),a0
	move.l a0,app_0360(a6)
	rts
abs_0_00010AA2:
	move.w app_0230(a6),$0182(a5)
	move.w #$E8,$0194(a5)
	lea.l abs_0_00010AB8(pc),a0
	move.l a0,app_0360(a6)
	rts
abs_0_00010AB8:
	bset.b #7,app_027B(a6)
	lea.l abs_0_00010A72(pc),a0
	move.l a0,app_0360(a6)
	rts
```

Here we use `app_0364` and `a5` is lost. In some c

```
abs_0_00010910:
	btst #5,d0
	beq.b abs_0_00010928
	movea.l app_0364(a6),a0
	jsr (a0)
	move.w #$20,$009C(a5)
	movem.l (a7)+,d0/a0-a1/a5-a6
	rte
```

Resolution note: accepted callback-slot indirect targets now inherit the call-site trace state in the C facts pass,
and the render lookup projects proven Amiga hardware-base register state through the same callback-slot shape. This
keeps callback bodies reached through app slots such as `app_0360`/`app_0364` rendering hardware accesses through the
same symbolic register base proven at the indirect call site, without a Pandora-specific rule. Covered by
`facts_v2_callback_field_target_inherits_call_site_trace_state`.

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


## Investigation needed: Amiga/Magicland Dizzy

### Memory map and absolute addresses

In theory we render a memory map at the top of the file as a comment for the overview of the user who is working
with the final rendered code. We should be detecting all absolute address access and mapping what is put there and
how big the space is, almost like a RSSET range. The lifetime and size and placement of all used absolute addresses
would allow better analysis and cross-referencing for mapped usage/purpose and rendering.

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
`$0002F490`, `$00032DD0`, and `$0004B470` directly in the human-facing memory map. Remaining work: promote stable
slot/range names and stronger size/lifetime evidence where analysis can prove them, instead of only using
address-span summaries.

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

This is a hunk file project. The implication here is that we should update this to a disk project and treat the
executable as the entrypoint and map in external data from disk, analysing the access. This might be an Amiga-specific
platform hook of a general approach to external files?

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
and read length visible from accepted instructions in the source. The broader parent disk-project/child payload mapping
is formally deferred for this target because the repo contains `bin/MagiclandDizzy_MD_f26cb8133afe` as an extracted
hunk file plus rebuilt/cache artifacts, but no source Magicland disk image to bind track reads back to real disk bytes.
The correct future work needs actual source media and a general external-resource relationship model, not guessed child
payloads from a standalone executable.

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
