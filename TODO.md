# TODO

## Investigation needed: MacOS/MPW asm

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

Also I have looked in `ext\macos_includes\mpw_gm\Interfaces` and not found `_GetFNum`. Where it comes from I do not
know.

### A5 data storage

There seems to be data storage in negative A5 offsets. In this case we are using addresses in there as input on the
stack, and then using the output in one of those addresses. It appears to be moved into positive offsets under the
jump table (given we know the jump table offset is defined in the leading data as $20 in some standard location).
In Amiga we have 

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


### Pascal strings

If we know a string is a string of some sort, we should display it as the restored  source should see it. As a
textual string where applicable. This is an opportunity for clean up. It should be a general thing, not just MacOS.
We already do it in seemingly inconsistent cases, so looking at data in other targets for failures where we're doing
it haphazardly and generalising an approach might be worth doing.

```
CODE_1_data_pascal_string_00002066:
	dc.b $87,$47,$45,$54,$52,$53,$52,$43,$00,$00
```

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

## Investigation needed: Amiga/Pandora

Moved into `docs/proposals/015-agent-reversing-pandora-target.md` as structured
deferred work entries.

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

### Unrecognised decompression routine

Decompression routine at `abs_0_000647F2`? It makes sense that this is placed near the disk access, and it likely
follows data loading from tracks and MFM decoding.

There is a general project here which likely relates to platforms, but is not necessarily platform specific except
for classification of where has been found or is likely to be found. A lot of these decompression routines will be
iterations on standard compression approaches, if not direct adaptations of pre-existing routines. If we can
heuristically identify these, their inputs, outputs and perhaps even type of compression, we can then perhaps
reliably hook into them and simulate them to pass in compressed payload and get out the decompressed original
data. 

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