    INCLUDE "exec/devices.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/libraries.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"

    RSSET LIB_SIZE
    RS.B 4
app_0026 RS.W 1
    RS.B 2
app_002A RS.L 1
app_SIZEOF EQU __RS


    SECTION section_0,code
    ; DECL: error = AvailFonts(STRPTR buffer, long bufBytes, long flags)
    ; KNOWN: base A6=diskfont.library:LIB; type A0=buffer:STRPTR; type D0=bufBytes:long; type D1=flags:long
avail_fonts:
	bra.w resident_init
resident:	; STRUCT RT
    ; invalid overlap: decoded code at $0004 starts at structured data; emitted as data
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l resident_init	; APTR RT_ENDSKIP
	dc.b $00	; UBYTE RT_FLAGS
	dc.b $22	; UBYTE RT_VERSION
	dc.b NT_LIBRARY	; UBYTE RT_TYPE = NT_LIBRARY
	dc.b $00	; BYTE RT_PRI
    ; DECL: font = OpenDiskFont(struct TextAttr *textAttr)
    ; KNOWN: base A6=diskfont.library:LIB; type A0=textAttr:struct TextAttr *
open_disk_font:	; STRUCT RT
    ; invalid overlap: decoded code at $0012 starts at structured data; emitted as data
	dc.l new_font_contents	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
    ; DECL: struct FontContentsHeader *NewFontContents(BPTR fontsLock, STRPTR fontName)
    ; KNOWN: base A6=diskfont.library:LIB; type A0=fontsLock:BPTR; type A1=fontName:STRPTR
new_font_contents:
    ; invalid overlap: decoded code at $001E starts at structured data; emitted as data
	dc.b "diskfont.library",$00	; string
	dc.b $00
resident_idstring:
    ; invalid overlap: decoded code at $0030 starts at structured data; emitted as data
	dc.b "diskfont 34.37 (27 May 1988)",$0D,$0A,$00	; string
	dc.b $00
resident_init:
	movem.l a0/a2,-(a7)
	lea.l resident_vectors(pc),a0
	lea.l loc_0_00000136(pc),a1
	lea.l loc_0_00000080(pc),a2
	move.l #$38,d0
	jsr -$0054(a6)
	movem.l (a7)+,a0/a2
	tst.l d0
	beq.b loc_0_0000007E
	movea.l d0,a1
	move.l a0,$0022(a1)
	jsr -$018C(a6)
	moveq.l #1,d0
loc_0_0000007E:
	rts
loc_0_00000080:
	dc.b $2F,$0E,$20,$40,$23,$CE
	dc.l loc_2_00000004
	dc.b $2C,$40,$23,$C0
	dc.l loc_2_00000000
	dc.b $43,$FA,$00,$84,$70,$00,$2F,$0E,$2C,$79
	dc.l loc_2_00000004
	dc.b $4E,$AE,$FD,$D8,$2C,$5F,$23,$C0
	dc.l loc_2_00000008
	dc.b $67,$00,$00,$4A,$43,$FA,$00,$72,$70,$00,$2F,$0E,$2C,$79
	dc.l loc_2_00000004
	dc.b $4E,$AE,$FD,$D8,$2C,$5F,$23,$C0
	dc.l loc_2_0000000C
	dc.b $67,$00,$00,$18,$41,$EE,$00,$2A,$20,$88,$58,$90,$42,$A8,$00,$04
	dc.b $21,$48,$00,$08,$20,$0E,$2C,$5F,$4E,$75,$22,$79
	dc.l loc_2_00000008
	dc.b $2F,$0E,$2C,$79
	dc.l loc_2_00000004
	dc.b $4E,$AE,$FE,$62,$2C,$5F,$22,$4E,$30,$2E,$00,$10,$92,$C0,$D0,$6E
	dc.b $00,$12,$48,$C0,$2F,$0E,$2C,$79
	dc.l loc_2_00000004
	dc.b $4E,$AE,$FF,$2E,$2C,$5F,$70,$00,$60,$C8,$64,$6F,$73,$2E,$6C,$69
	dc.b $62,$72,$61,$72,$79,$00,$67,$72,$61,$70,$68,$69,$63,$73,$2E,$6C
	dc.b $69,$62,$72,$61,$72,$79,$00,$00
loc_0_00000136:
	dc.b $E0,$00,$00,$08,$09,$00,$C0,$00,$00,$0A
	dc.l new_font_contents
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$22,$D0,$00,$00,$16
	dc.b $00,$25,$E0,$00,$00,$36,$0C,$00,$00,$00
resident_vectors:
	dc.l diskfont_lib_open
	dc.l diskfont_lib_close
	dc.l diskfont_lib_expunge
	dc.l diskfont_lib_extfunc
	dc.l loc_1_00000012
	dc.l loc_1_00000000
	dc.l loc_1_0000001E
	dc.l loc_1_0000002C
	dc.l $FFFFFFFF
    ; KNOWN: base A6=diskfont.library:LIB
diskfont_lib_expunge:
	move.l a2,-(a7)
	movea.l app_002A(a6),a2
loc_0_00000188:
	tst.l (a2)
	beq.b loc_0_000001DA
	tst.w $0054(a2)
	bgt.b loc_0_000001D6
	movea.l a2,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	move.l $0012(a2),d1
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	jsr -$009C(a6)
	movea.l (a7)+,a6
	lea.l $0036(a2),a1
	movea.l (a1),a0
	cmpa.l $0004(a0),a1
	bne.b loc_0_000001D2
	movea.l $0004(a1),a0
	cmpa.l (a0),a1
	bne.b loc_0_000001D2
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
loc_0_000001D2:
	subq.w #1,$0028(a6)
loc_0_000001D6:
	movea.l (a2),a2
	bra.b loc_0_00000188
loc_0_000001DA:
	movea.l (a7)+,a2
	tst.w app_0026(a6)
	bne.b loc_0_00000242
	tst.w $0028(a6)
	bgt.b loc_0_00000242
	movea.l loc_2_0000000C.l,a1
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOCloseLibrary(a6)
	movea.l (a7)+,a6
	movea.l loc_2_00000008.l,a1
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOCloseLibrary(a6)
	movea.l (a7)+,a6
	move.l $0022(a6),-(a7)
	movea.l a6,a1
	move.w $0010(a6),d0
	suba.w d0,a1
	add.w $0012(a6),d0
	ext.l d0
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	movea.l a6,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	move.l (a7)+,d0
	rts
loc_0_00000242:
	bset.b #7,$000E(a6)
	moveq.l #0,d0
    ; KNOWN: base A6=diskfont.library:LIB
diskfont_lib_extfunc:
	rts
    ; KNOWN: base A6=diskfont.library:LIB
diskfont_lib_open:
	bclr.b #7,LIB_FLAGS(a6)
	addq.w #1,app_0026(a6)
	move.l a6,d0
	rts
    ; KNOWN: base A6=diskfont.library:LIB
diskfont_lib_close:
	subq.w #1,app_0026(a6)
	bne.b loc_0_0000026C
	btst.b #7,LIB_FLAGS(a6)
	beq.b loc_0_0000026C
	jmp -$0012(a6)
loc_0_0000026C:
	moveq.l #0,d0
	rts
    SECTION section_1,code
loc_1_00000000:
	movem.l d0-d1,-(a7)
	move.l a0,-(a7)
	jsr loc_3_00000000.l
	adda.w #$C,a7
	rts
loc_1_00000012:
	move.l a0,-(a7)
	jsr loc_7_000000E0.l
	addq.w #4,a7
	rts
loc_1_0000001E:
	movem.l a0-a1,-(a7)
	jsr loc_5_00000000.l
	addq.l #8,a7
	rts
loc_1_0000002C:
	move.l a1,-(a7)
	jsr loc_5_00000240.l
	addq.l #4,a7
	rts
    SECTION section_2,data
loc_2_00000000:
	dc.b $00,$00,$00,$00
loc_2_00000004:
	dc.b $00,$00,$00,$00
loc_2_00000008:
	dc.b $00,$00,$00,$00
loc_2_0000000C:
	dc.b $00,$00,$00,$00
    SECTION section_3,code
loc_3_00000000:
	link a6,#-272
	movem.l d2-d6/a2-a4,-(a7)
	movea.l $0008(a6),a0
	move.l $000C(a6),d2
	move.l $0010(a6),d3
	move.l a0,d6
	addq.l #2,a0
	subq.l #2,d2
	blt.b loc_3_00000020
	movea.l d6,a1
	clr.w (a1)
loc_3_00000020:
	tst.l d2
	blt.b loc_3_00000026
	movea.l a0,a2
loc_3_00000026:
	move.l a0,d5
	add.l d2,d5
	btst #0,d3
	beq.w loc_3_0000009E
	movea.l loc_2_0000000C.l,a0
	movea.l $008C(a0),a4
	bra.b loc_3_0000009A
loc_3_0000003E:
	movea.l $000A(a4),a1
	moveq.l #1,d4
	bra.b loc_3_00000048
loc_3_00000046:
	addq.w #1,d4
loc_3_00000048:
	tst.b (a1)+
	bne.b loc_3_00000046
	moveq.l #0,d0
	move.w d4,d0
	sub.l d0,d5
	moveq.l #0,d0
	move.w d4,d0
	moveq.l #10,d1
	add.l d1,d0
	sub.l d0,d2
	blt.b loc_3_00000098
	movea.l $000A(a4),a1
	moveq.l #0,d0
	movea.l d0,a3
	bra.b loc_3_0000006E
loc_3_00000068:
	move.b (a1)+,$0(a3,d5.l)
	addq.l #1,a3
loc_3_0000006E:
	moveq.l #0,d0
	move.w d4,d0
	cmp.l a3,d0
	bhi.b loc_3_00000068
	move.w #$1,(a2)
	move.l d5,$0002(a2)
	move.w $0014(a4),$0006(a2)
	move.b $0016(a4),$0008(a2)
	move.b $0017(a4),$0009(a2)
	movea.l d6,a0
	addq.w #1,(a0)
	moveq.l #10,d0
	adda.l d0,a2
loc_3_00000098:
	movea.l (a4),a4
loc_3_0000009A:
	tst.l (a4)
	bne.b loc_3_0000003E
loc_3_0000009E:
	btst #1,d3
	beq.w loc_3_00000252
	clr.l -(a7)
	pea.l $0104.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_13_00000020.l
	movea.l d0,a4
	move.l a4,d3
	addq.l #8,a7
	beq.w loc_3_00000252
	moveq.l #-2,d3
	move.l d3,-(a7)
	pea.l loc_4_00000000.l
	jsr loc_12_0000004C.l
	move.l d0,-$0004(a6)
	addq.l #8,a7
	beq.w loc_3_00000244
	move.l -$0004(a6),-(a7)
	jsr loc_12_000000B4.l
	move.l d0,-$0008(a6)
	move.l a4,-(a7)
	move.l -$0004(a6),-(a7)
	jsr loc_12_0000007C.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.w loc_3_0000022E
	tst.l $0004(a4)
	ble.w loc_3_0000022E
	bra.w loc_3_0000021A
loc_3_00000106:
	pea.l $002E.w
	pea.l $0008(a4)
	jsr loc_9_0000007E.l
	movea.l d0,a1
	move.l a1,d3
	addq.l #8,a7
	beq.w loc_3_0000021A
	pea.l loc_4_00000008.l
	move.l a1,-(a7)
	jsr loc_9_0000003C.l
	tst.l d0
	addq.l #8,a7
	bne.w loc_3_0000021A
	tst.l $0004(a4)
	bge.w loc_3_0000021A
	pea.l $03ED.w
	pea.l $0008(a4)
	jsr loc_12_00000000.l
	move.l d0,d3
	addq.l #8,a7
	beq.w loc_3_0000021A
	pea.l $0008(a4)
	jsr loc_9_000000B2.l
	movea.l d0,a1
	moveq.l #1,d4
	addq.l #4,a7
	bra.b loc_3_00000166
loc_3_00000164:
	addq.w #1,d4
loc_3_00000166:
	tst.b (a1)+
	bne.b loc_3_00000164
	moveq.l #0,d0
	move.w d4,d0
	sub.l d0,d5
	moveq.l #0,d0
	move.w d4,d0
	sub.l d0,d2
	blt.b loc_3_00000190
	lea.l $0008(a4),a1
	moveq.l #0,d0
	movea.l d0,a3
	bra.b loc_3_00000188
loc_3_00000182:
	move.b (a1)+,$0(a3,d5.l)
	addq.l #1,a3
loc_3_00000188:
	moveq.l #0,d0
	move.w d4,d0
	cmp.l a3,d0
	bhi.b loc_3_00000182
loc_3_00000190:
	pea.l $0004.w
	pea.l -$000C(a6)
	move.l d3,-(a7)
	jsr loc_12_00000030.l
	moveq.l #4,d1
	cmp.l d0,d1
	lea.l $000C(a7),a7
	bne.b loc_3_00000210
	cmpi.w #3840,-$000C(a6)
	bne.b loc_3_00000210
	moveq.l #0,d0
	movea.l d0,a3
	bra.b loc_3_00000206
loc_3_000001B8:
	pea.l $0104.w
	pea.l -$0110(a6)
	move.l d3,-(a7)
	jsr loc_12_00000030.l
	cmpi.l #260,d0
	lea.l $000C(a7),a7
	bne.b loc_3_00000204
	moveq.l #10,d0
	sub.l d0,d2
	blt.b loc_3_00000204
	move.w #$2,(a2)
	move.l d5,$0002(a2)
	move.w -$0010(a6),$0006(a2)
	move.b -$000E(a6),$0008(a2)
	moveq.l #0,d0
	move.b -$000D(a6),d0
	moveq.l #2,d1
	or.l d1,d0
	move.b d0,$0009(a2)
	movea.l d6,a0
	addq.w #1,(a0)
	moveq.l #10,d0
	adda.l d0,a2
loc_3_00000204:
	addq.l #1,a3
loc_3_00000206:
	moveq.l #0,d0
	move.w -$000A(a6),d0
	cmp.l a3,d0
	bhi.b loc_3_000001B8
loc_3_00000210:
	move.l d3,-(a7)
	jsr loc_12_0000001C.l
	addq.l #4,a7
loc_3_0000021A:
	move.l a4,-(a7)
	move.l -$0004(a6),-(a7)
	jsr loc_12_00000098.l
	tst.l d0
	addq.l #8,a7
	bne.w loc_3_00000106
loc_3_0000022E:
	move.l -$0008(a6),-(a7)
	jsr loc_12_000000B4.l
	move.l -$0004(a6),-(a7)
	jsr loc_12_00000068.l
	addq.l #8,a7
loc_3_00000244:
	pea.l $0104.w	; KNOWN: arg +8 byteSize unsigned long
	move.l a4,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_13_00000038.l
	addq.l #8,a7
loc_3_00000252:
	tst.l d2
	bge.b loc_3_0000025C
	move.l d2,d0
	neg.l d0
	bra.b loc_3_0000025E
loc_3_0000025C:
	moveq.l #0,d0
loc_3_0000025E:
	movem.l -$0130(a6),d2-d6/a2-a4
	unlk a6
	rts
    SECTION section_4,data
loc_4_00000000:
	dc.b $46,$4F,$4E,$54,$53,$3A,$00,$00
loc_4_00000008:
	dc.b $2E,$66,$6F,$6E,$74,$00,$00,$00
    SECTION section_5,code
loc_5_00000000:
	link a6,#-40
	movem.l d2-d7/a2-a5,-(a7)
	move.l $0008(a6),d0
	move.l $000C(a6),d2
	moveq.l #0,d5
	movea.l d5,a3
	clr.l -$0004(a6)
	moveq.l #0,d4
	move.l d0,-(a7)
	jsr loc_12_000000B4.l
	move.l d0,-$0008(a6)
	pea.l $0001.w	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	pea.l $0104.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_13_00000020.l
	move.l d0,d3
	lea.l $000C(a7),a7
	beq.w loc_5_000001F0
	move.l d2,-(a7)
	jsr loc_9_0000002C.l
	moveq.l #31,d1
	cmp.l d0,d1
	addq.l #4,a7
	blt.w loc_5_000001F0
	move.l d2,-(a7)
	pea.l -$0028(a6)
	jsr loc_9_00000000.l
	pea.l $002E.w
	pea.l -$0028(a6)
	jsr loc_9_0000007E.l
	movea.l d0,a2
	move.l a2,d5
	lea.l $0010(a7),a7
	beq.w loc_5_000001F0
	pea.l loc_6_00000000.l
	move.l a2,-(a7)
	jsr loc_9_0000003C.l
	tst.l d0
	addq.l #8,a7
	bne.w loc_5_000001F0
	clr.b (a2)
	moveq.l #-2,d2
	move.l d2,-(a7)
	pea.l -$0028(a6)
	jsr loc_12_0000004C.l
	move.l d0,d4
	addq.l #8,a7
	beq.w loc_5_000001F0
	moveq.l #0,d6
	move.l d3,-(a7)
	move.l d4,-(a7)
	jsr loc_12_0000007C.l
	tst.l d0
	addq.l #8,a7
	beq.w loc_5_000001F0
	bra.b loc_5_000000BC
loc_5_000000BA:
	addq.l #1,d6
loc_5_000000BC:
	move.l d3,-(a7)
	move.l d4,-(a7)
	jsr loc_12_00000098.l
	tst.l d0
	addq.l #8,a7
	bne.b loc_5_000000BA
	jsr loc_12_000000C8.l
	cmpi.l #232,d0
	bne.w loc_5_000001F0
	move.l d6,d2
	asl.l #2,d2
	movea.l d2,a0
	move.l a0,d0
	asl.l #6,d2
	movea.l d2,a0
	adda.l d0,a0
	addq.l #8,a0
	move.l a0,d6
	move.l #$10001,-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	move.l d6,-(a7)	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_13_00000020.l
	movea.l d0,a3
	move.l a3,d2
	addq.l #8,a7
	beq.w loc_5_000001F0
	move.l d6,(a3)
	move.w #$F00,$0004(a3)
	clr.w $0006(a3)
	move.l d4,-(a7)
	jsr loc_12_000000B4.l
	move.l d3,-(a7)
	move.l d4,-(a7)
	jsr loc_12_0000007C.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.w loc_5_000001F0
loc_5_0000012E:
	move.l d3,-(a7)
	move.l d4,-(a7)
	jsr loc_12_00000098.l
	move.l d0,d5
	addq.l #8,a7
	beq.w loc_5_000001D4
	movea.l d3,a0
	tst.l $0004(a0)
	bge.w loc_5_000001D4
	movea.l d3,a2
	pea.l $0008(a2)
	jsr loc_12_000000D8.l
	move.l d0,d2
	addq.l #4,a7
	beq.w loc_5_000001D4
	move.l d2,d0
	asl.l #2,d0
	movea.l d0,a0
	addq.l #8,a0
	movea.l a0,a4
	cmpi.w #3968,$000E(a4)
	bne.b loc_5_000001CA
	lea.l $0008(a3),a1
	move.w $0006(a3),d0
	addq.w #1,$0006(a3)
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,d7
	muls.w #$104,d7
	movea.l d7,a0
	adda.l a1,a0
	movea.l a0,a2
	pea.l -$0028(a6)
	pea.l (a2)
	jsr loc_9_00000000.l
	pea.l loc_6_00000006.l
	pea.l (a2)
	jsr loc_9_00000010.l
	movea.l d3,a5
	pea.l $0008(a5)
	pea.l (a2)
	jsr loc_9_00000010.l
	move.w $004A(a4),$0100(a2)
	move.b $004C(a4),$0102(a2)
	move.b $004D(a4),$0103(a2)
	lea.l $0018(a7),a7
loc_5_000001CA:
	move.l d2,-(a7)
	jsr loc_12_000000EC.l
	addq.l #4,a7
loc_5_000001D4:
	tst.l d5
	bne.w loc_5_0000012E
	jsr loc_12_000000C8.l
	cmpi.l #232,d0
	bne.b loc_5_000001F0
	lea.l $0004(a3),a0
	move.l a0,-$0004(a6)
loc_5_000001F0:
	tst.l -$0004(a6)
	bne.b loc_5_00000206
	move.l a3,d0
	beq.b loc_5_00000206
	move.l d6,-(a7)	; KNOWN: arg +8 byteSize unsigned long
	move.l a3,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_13_00000038.l
	addq.l #8,a7
loc_5_00000206:
	tst.l d4
	beq.b loc_5_00000214
	move.l d4,-(a7)
	jsr loc_12_00000068.l
	addq.l #4,a7
loc_5_00000214:
	tst.l d3
	beq.b loc_5_00000226
	pea.l $0104.w	; KNOWN: arg +8 byteSize unsigned long
	move.l d3,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_13_00000038.l
	addq.l #8,a7
loc_5_00000226:
	move.l -$0008(a6),-(a7)
	jsr loc_12_000000B4.l
	move.l -$0004(a6),d0
	addq.l #4,a7
	movem.l -$0050(a6),d2-d7/a2-a5
	unlk a6
	rts
loc_5_00000240:
	movea.l $0004(a7),a0
	move.l -(a0),-(a7)	; KNOWN: arg +8 byteSize unsigned long
	move.l a0,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_13_00000038.l
	addq.l #8,a7
	rts
	dc.b $00,$00
    SECTION section_6,data
loc_6_00000000:
	dc.b $2E,$66,$6F,$6E,$74,$00
loc_6_00000006:
	dc.b $2F,$00
    SECTION section_7,code
loc_7_00000000:
	movem.l d2-d6,-(a7)
	movea.l $0018(a7),a0
	movea.l $001C(a7),a1
	tst.w $0100(a1)
	beq.w loc_7_000000D2
	move.l #$7FFF,d2
	move.w $0100(a1),d5
	sub.w $0004(a0),d5
	bge.b loc_7_0000002E
	move.w d5,d0
	ext.l d0
	asl.l #6,d0
	add.l d0,d2
	bra.b loc_7_00000036
loc_7_0000002E:
	move.w d5,d0
	ext.l d0
	asl.l #8,d0
	sub.l d0,d2
loc_7_00000036:
	moveq.l #0,d0
	move.b $0006(a0),d0
	move.w d0,d5
	moveq.l #0,d0
	move.b $0102(a1),d0
	eor.w d0,d5
	moveq.l #0,d0
	move.b $0007(a0),d0
	move.w d0,d6
	moveq.l #0,d0
	move.b $0103(a1),d0
	eor.w d0,d6
	moveq.l #1,d3
	clr.w d4
loc_7_0000005A:
	move.w d3,d0
	ext.l d0
	move.w d5,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_7_00000090
	moveq.l #0,d1
	move.b $0102(a1),d1
	move.l d1,d0
	move.w d3,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_7_00000082
	move.w d4,d0
	asl.w #2,d0
	movea.l #loc_8_00000028,a0
	bra.b loc_7_0000008C
loc_7_00000082:
	move.w d4,d0
	asl.w #2,d0
	movea.l #loc_8_00000008,a0
loc_7_0000008C:
	sub.l $0(a0,d0.w),d2
loc_7_00000090:
	move.w d3,d0
	ext.l d0
	move.w d6,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_7_000000C6
	moveq.l #0,d1
	move.b $0103(a1),d1
	move.l d1,d0
	move.w d3,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_7_000000B8
	move.w d4,d0
	asl.w #2,d0
	movea.l #loc_8_00000068,a0
	bra.b loc_7_000000C2
loc_7_000000B8:
	move.w d4,d0
	asl.w #2,d0
	movea.l #loc_8_00000048,a0
loc_7_000000C2:
	sub.l $0(a0,d0.w),d2
loc_7_000000C6:
	add.w d3,d3
	addq.w #1,d4
	cmpi.w #7,d4
	blt.b loc_7_0000005A
	bra.b loc_7_000000D8
loc_7_000000D2:
	move.l #$FFFF8001,d2
loc_7_000000D8:
	move.l d2,d0
	movem.l (a7)+,d2-d6
	rts
loc_7_000000E0:
	link a6,#-288
	movem.l d2-d7/a2-a4,-(a7)
	movea.l $0008(a6),a2
	movea.l a2,a0
	lea.l -$001C(a6),a1
	move.l (a0)+,(a1)+
	move.l (a0)+,(a1)+
	move.l (a2),-(a7)
	jsr loc_9_000000B2.l
	move.l d0,-$001C(a6)
	pea.l -$001C(a6)
	jsr loc_14_00000000.l
	movea.l d0,a4
	movea.l a4,a3
	move.l a3,d2
	addq.l #8,a7
	beq.b loc_7_00000142
	move.w $0014(a3),-$0020(a6)
	move.b $0016(a3),-$001E(a6)
	move.b $0017(a3),-$001D(a6)
	pea.l -$0120(a6)
	pea.l -$001C(a6)
	jsr loc_7_00000000(pc)
	cmpi.l #32767,d0
	addq.l #8,a7
	bne.b loc_7_00000142
	bra.w loc_7_00000394
loc_7_00000142:
	moveq.l #-2,d2
	move.l d2,-(a7)
	pea.l loc_8_00000000.l
	jsr loc_12_0000004C.l
	move.l d0,-$000C(a6)
	addq.l #8,a7
	bne.b loc_7_0000015E
	bra.w loc_7_00000394
loc_7_0000015E:
	move.l -$000C(a6),-(a7)
	jsr loc_12_000000B4.l
	move.l d0,-$0010(a6)
	moveq.l #-2,d2
	move.l d2,-(a7)
	move.l (a2),-(a7)
	jsr loc_12_0000004C.l
	move.l d0,-$0004(a6)
	lea.l $000C(a7),a7
	beq.w loc_7_0000036C
	pea.l $03ED.w
	move.l (a2),-(a7)
	jsr loc_12_00000000.l
	move.l d0,-$0008(a6)
	addq.l #8,a7
	beq.w loc_7_00000360
	pea.l $0004.w
	pea.l -$0014(a6)
	move.l -$0008(a6),-(a7)
	jsr loc_12_00000030.l
	moveq.l #4,d2
	movea.l d2,a0
	cmpa.l d0,a0
	lea.l $000C(a7),a7
	bne.w loc_7_00000354
	moveq.l #0,d0
	move.w -$0014(a6),d0
	andi.l #65528,d0
	cmpi.l #3840,d0
	bne.w loc_7_00000354
	moveq.l #0,d0
	move.w -$0012(a6),d0
	move.l d0,d6
	muls.w #$104,d6
	clr.l -(a7)
	move.l d6,-(a7)	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_13_00000020.l
	move.l d0,d5
	addq.l #8,a7
	beq.w loc_7_00000354
	move.l d6,-(a7)
	move.l d5,-(a7)
	move.l -$0008(a6),-(a7)
	jsr loc_12_00000030.l
	cmp.l d0,d6
	lea.l $000C(a7),a7
	bne.w loc_7_00000348
loc_7_00000206:
	move.l a3,d0
	beq.b loc_7_0000021C
	pea.l -$0120(a6)
	pea.l -$001C(a6)
	jsr loc_7_00000000(pc)
	move.w d0,d4
	addq.l #8,a7
	bra.b loc_7_0000021E
loc_7_0000021C:
	clr.w d4
loc_7_0000021E:
	moveq.l #-1,d2
	clr.w d3
	bra.b loc_7_00000248
loc_7_00000224:
	movea.w d3,a0
	move.l a0,d7
	ext.l d7
	muls.w #$104,d7
	movea.l d7,a0
	pea.l $0(a0,d5.l)
	pea.l -$001C(a6)
	jsr loc_7_00000000(pc)
	cmp.w d4,d0
	addq.l #8,a7
	ble.b loc_7_00000246
	move.w d0,d4
	move.w d3,d2
loc_7_00000246:
	addq.w #1,d3
loc_7_00000248:
	move.w -$0012(a6),d0
	cmp.w d3,d0
	bhi.b loc_7_00000224
	tst.w d2
	blt.w loc_7_00000342
	move.l -$0004(a6),-(a7)
	jsr loc_12_00000100.l
	move.l d0,d3
	move.l d3,-(a7)
	jsr loc_12_000000B4.l
	movea.w d2,a0
	move.l a0,d7
	ext.l d7
	muls.w #$104,d7
	movea.l d7,a0
	pea.l $0(a0,d5.l)
	jsr loc_12_000000D8.l
	move.l d0,d4
	move.l d0,d7
	lsl.l #2,d7
	movea.l d7,a0
	addq.l #8,a0
	move.l a0,d1
	movea.l d1,a2
	moveq.l #8,d0
	cmp.l d1,d0
	lea.l $000C(a7),a7
	beq.w loc_7_00000322
	cmpi.w #3968,$000E(a2)
	bne.b loc_7_00000304
	move.l d4,$0012(a2)
	move.l -$001C(a6),-(a7)
	pea.l $0016(a2)
	jsr loc_9_00000000.l
	lea.l $0016(a2),a0
	move.l a0,$0040(a2)
	ori.b #2,$004D(a2)
	jsr loc_13_00000000.l
	pea.l $0036(a2)
	jsr loc_14_00000028.l
	addq.w #1,$0054(a2)
	move.l a2,-(a7)
	movea.l loc_2_00000000.l,a0
	pea.l $002A(a0)	; KNOWN: arg +4 list LH
	jsr loc_13_00000050.l
	movea.l loc_2_00000000.l,a0
	addq.w #1,$0028(a0)
	jsr loc_13_00000010.l
	moveq.l #-1,d2
	lea.l $0036(a2),a4
	lea.l $0014(a7),a7
	bra.b loc_7_00000334
loc_7_00000304:
	move.l d4,-(a7)
	jsr loc_12_000000EC.l
	move.w d2,d0
	ext.l d0
	muls.w #$104,d0
	movea.l d0,a0
	movea.l a0,a2
	adda.l d5,a2
	clr.w $0100(a2)
	addq.l #4,a7
	bra.b loc_7_00000334
loc_7_00000322:
	move.w d2,d0
	ext.l d0
	muls.w #$104,d0
	movea.l d0,a0
	movea.l a0,a1
	adda.l d5,a1
	clr.w $0100(a1)
loc_7_00000334:
	tst.l d3
	beq.b loc_7_00000342
	move.l d3,-(a7)
	jsr loc_12_00000068.l
	addq.l #4,a7
loc_7_00000342:
	tst.w d2
	bge.w loc_7_00000206
loc_7_00000348:
	move.l d6,-(a7)	; KNOWN: arg +8 byteSize unsigned long
	move.l d5,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_13_00000038.l
	addq.l #8,a7
loc_7_00000354:
	move.l -$0008(a6),-(a7)
	jsr loc_12_0000001C.l
	addq.l #4,a7
loc_7_00000360:
	move.l -$0004(a6),-(a7)
	jsr loc_12_00000068.l
	addq.l #4,a7
loc_7_0000036C:
	move.l -$0010(a6),-(a7)
	jsr loc_12_000000B4.l
	move.l -$000C(a6),-(a7)
	jsr loc_12_00000068.l
	move.l a3,d2
	addq.l #8,a7
	beq.b loc_7_00000394
	cmpa.l a3,a4
	beq.b loc_7_00000394
	move.l a3,-(a7)
	jsr loc_14_00000014.l
	addq.l #4,a7
loc_7_00000394:
	move.l a4,d0
	movem.l -$0144(a6),d2-d7/a2-a4
	unlk a6
	rts
    SECTION section_8,data
loc_8_00000000:
	dc.b $46,$4F,$4E,$54,$53,$3A,$00,$00
loc_8_00000008:
	dc.b $00,$00,$00,$04,$00,$00,$00,$08,$00,$00,$00,$10
	dcb.b $14,$00
loc_8_00000028:
	dc.b $00,$00,$00,$80,$00,$00,$00,$80,$00,$00,$00,$80
	dcb.b $14,$00
loc_8_00000048:
	dc.b $00,$00,$00,$01,$00,$00,$00,$01,$00,$00,$80,$00,$00,$00,$00,$20
	dc.b $00,$00,$00,$20,$00,$00,$00,$20,$00,$00,$00,$02,$00,$00,$00,$00
loc_8_00000068:
	dc.b $00,$00,$00,$01,$00,$00,$00,$01,$00,$00,$80,$00,$00,$00,$00,$20
	dc.b $00,$00,$00,$20,$00,$00,$00,$80,$00,$00,$00,$02,$00,$00,$00,$00
    SECTION section_9,code
loc_9_00000000:
	movea.l $0004(a7),a1
	movea.l $0008(a7),a0
loc_9_00000008:
	move.b (a0),(a1)+
	tst.b (a0)+
	bne.b loc_9_00000008
	rts
loc_9_00000010:
	movea.l $0004(a7),a0
	move.l $0008(a7),d0
	bra.b loc_9_0000001C
loc_9_0000001A:
	addq.l #1,a0
loc_9_0000001C:
	tst.b (a0)
	bne.b loc_9_0000001A
	move.l d0,-(a7)
	move.l a0,-(a7)
	jsr loc_9_00000000(pc)
	addq.l #8,a7
	rts
loc_9_0000002C:
	movea.l $0004(a7),a0
	moveq.l #0,d0
	bra.b loc_9_00000036
loc_9_00000034:
	addq.l #1,d0
loc_9_00000036:
	tst.b (a0)+
	bne.b loc_9_00000034
	rts
loc_9_0000003C:
	movea.l $0004(a7),a1
	movea.l $0008(a7),a0
	bra.b loc_9_0000004E
loc_9_00000046:
	tst.b (a0)+
	bne.b loc_9_0000004E
	moveq.l #0,d0
	bra.b loc_9_00000060
loc_9_0000004E:
	move.b (a0),d0
	cmp.b (a1)+,d0
	beq.b loc_9_00000046
	move.b -(a1),d0
	cmp.b (a0),d0
	bge.b loc_9_0000005E
	moveq.l #-1,d0
	bra.b loc_9_00000060
loc_9_0000005E:
	moveq.l #1,d0
loc_9_00000060:
	rts
	dc.b $20,$6F,$00,$04,$10,$2F,$00,$0B,$60,$0A,$B2,$00,$66,$04,$20,$08
	dc.b $60,$08,$52,$88,$12,$10,$66,$F2,$70,$00,$4E,$75
loc_9_0000007E:
	movem.l d2-d3,-(a7)
	move.l $000C(a7),d3
	move.b $0013(a7),d2
	move.l d3,-(a7)
	jsr loc_9_0000002C(pc)
	movea.l d0,a0
	subq.l #1,a0
	movea.l a0,a0
	adda.l d3,a0
	addq.l #4,a7
	bra.b loc_9_000000A6
loc_9_0000009C:
	cmp.b (a0),d2
	bne.b loc_9_000000A4
	move.l a0,d0
	bra.b loc_9_000000AC
loc_9_000000A4:
	subq.l #1,a0
loc_9_000000A6:
	cmpa.l d3,a0
	bge.b loc_9_0000009C
	moveq.l #0,d0
loc_9_000000AC:
	movem.l (a7)+,d2-d3
	rts
loc_9_000000B2:
	move.l d2,-(a7)
	move.l $0008(a7),d2
	pea.l $002F.w
	move.l d2,-(a7)
	jsr loc_9_0000007E(pc)
	move.l d0,d0
	addq.l #8,a7
	bne.b loc_9_000000DA
	pea.l $003A.w
	move.l d2,-(a7)
	jsr loc_9_0000007E(pc)
	move.l d0,d0
	addq.l #8,a7
	bne.b loc_9_000000DA
	bra.b loc_9_000000DE
loc_9_000000DA:
	addq.l #1,d0
	move.l d0,d2
loc_9_000000DE:
	move.l d2,d0
	move.l (a7)+,d2
	rts
    SECTION section_10,data
    SECTION section_11,code
    SECTION section_12,code
loc_12_00000000:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$001E(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_12_0000001C:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$0024(a6)
	movea.l (a7)+,a6
	rts
loc_12_00000030:
	movem.l d2-d3/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $0010(a7),d1-d3
	jsr -$002A(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
loc_12_0000004C:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$0054(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_12_00000068:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$005A(a6)
	movea.l (a7)+,a6
	rts
loc_12_0000007C:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$0066(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_12_00000098:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$006C(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_12_000000B4:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$007E(a6)
	movea.l (a7)+,a6
	rts
loc_12_000000C8:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	rts
loc_12_000000D8:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$0096(a6)
	movea.l (a7)+,a6
	rts
loc_12_000000EC:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$009C(a6)
	movea.l (a7)+,a6
	rts
loc_12_00000100:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$00D2(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_13,code
loc_13_00000000:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOForbid(a6)
	movea.l (a7)+,a6
	rts
loc_13_00000010:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	rts
loc_13_00000020:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	movem.l $0008(a7),d0-d1	; KNOWN: arg +4 byteSize unsigned long | KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_13_00000038:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 memoryBlock APTR
	move.l $000C(a7),d0	; KNOWN: arg +8 byteSize unsigned long
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	rts
loc_13_00000050:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	movem.l $0008(a7),a0-a1	; KNOWN: arg +4 list LH | KNOWN: arg +8 node LN
	jsr _LVOAddTail(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
    SECTION section_14,code
loc_14_00000000:
	move.l a6,-(a7)
	movea.l loc_2_0000000C.l,a6
	movea.l $0008(a7),a0
	jsr -$0048(a6)
	movea.l (a7)+,a6
	rts
loc_14_00000014:
	move.l a6,-(a7)
	movea.l loc_2_0000000C.l,a6
	movea.l $0008(a7),a1
	jsr -$004E(a6)
	movea.l (a7)+,a6
	rts
loc_14_00000028:
	move.l a6,-(a7)
	movea.l loc_2_0000000C.l,a6
	movea.l $0008(a7),a1
	jsr -$01E0(a6)
	movea.l (a7)+,a6
	rts
