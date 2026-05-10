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
	dc.b $21	; UBYTE RT_VERSION
	dc.b NT_LIBRARY	; UBYTE RT_TYPE = NT_LIBRARY
	dc.b $00	; BYTE RT_PRI
    ; DECL: font = OpenDiskFont(struct TextAttr *textAttr)
    ; KNOWN: base A6=diskfont.library:LIB; type A0=textAttr:struct TextAttr *
open_disk_font:	; STRUCT RT
    ; invalid overlap: decoded code at $0012 starts at structured data; emitted as data
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
resident_name:
    ; invalid overlap: decoded code at $001E starts at structured data; emitted as data
	dc.b "diskfont.library",$00	; string
	dc.b $00
resident_idstring:
    ; invalid overlap: decoded code at $0030 starts at structured data; emitted as data
	dc.b "diskfont 33.16 (10 Feb 1986)",$0D,$0A,$00	; string
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
	dc.l resident_name
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$21,$D0,$00,$00,$16
	dc.b $00,$10,$E0,$00,$00,$36,$0C,$00,$00,$00
resident_vectors:
	dc.l diskfont_lib_open
	dc.l diskfont_lib_close
	dc.l diskfont_lib_expunge
	dc.l diskfont_lib_extfunc
	dc.l loc_1_00000012
	dc.l loc_1_00000000
	dc.l $FFFFFFFF
    ; KNOWN: base A6=diskfont.library:LIB
diskfont_lib_expunge:
	move.l a2,-(a7)
	movea.l app_002A(a6),a2
loc_0_00000180:
	tst.l (a2)
	beq.b loc_0_000001D2
	tst.w $0054(a2)
	bgt.b loc_0_000001CE
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
	bne.b loc_0_000001CA
	movea.l $0004(a1),a0
	cmpa.l (a0),a1
	bne.b loc_0_000001CA
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
loc_0_000001CA:
	subq.w #1,$0028(a6)
loc_0_000001CE:
	movea.l (a2),a2
	bra.b loc_0_00000180
loc_0_000001D2:
	movea.l (a7)+,a2
	tst.w app_0026(a6)
	bne.b loc_0_0000023A
	tst.w $0028(a6)
	bgt.b loc_0_0000023A
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
loc_0_0000023A:
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
	beq.b loc_0_00000264
	btst.b #7,LIB_FLAGS(a6)
	beq.b loc_0_00000264
	jmp -$0012(a6)
loc_0_00000264:
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
	jsr loc_5_000000E0.l
	addq.w #4,a7
	rts
	dc.b $00,$00
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
	movem.l d2-d7/a2-a5,-(a7)
	move.l $0008(a6),d0
	move.l $000C(a6),d2
	move.l $0010(a6),d1
	movea.l d0,a4
	addq.l #2,d0
	subq.l #2,d2
	tst.l d2
	blt.b loc_3_00000020
	clr.w (a4)
loc_3_00000020:
	tst.l d2
	blt.b loc_3_00000026
	movea.l d0,a2
loc_3_00000026:
	move.l d0,-$0004(a6)
	move.l -$0004(a6),d7
	add.l d2,d7
	move.l d7,-$0004(a6)
	btst #0,d1
	beq.w loc_3_000000B8
	movea.l loc_2_0000000C.l,a0
	movea.l $008C(a0),a0
loc_3_00000046:
	tst.l (a0)
	beq.w loc_3_000000B8
	movea.l $000A(a0),a1
	moveq.l #1,d4
loc_3_00000052:
	tst.b (a1)+
	beq.b loc_3_0000005A
	addq.w #1,d4
	bra.b loc_3_00000052
loc_3_0000005A:
	moveq.l #0,d0
	move.w d4,d0
	move.l -$0004(a6),d7
	sub.l d0,d7
	move.l d7,-$0004(a6)
	moveq.l #0,d0
	move.w d4,d0
	moveq.l #10,d3
	add.l d3,d0
	sub.l d0,d2
	tst.l d2
	blt.b loc_3_000000B4
	movea.l $000A(a0),a1
	moveq.l #0,d3
	bra.b loc_3_0000008A
loc_3_0000007E:
	move.l d3,d0
	add.l -$0004(a6),d0
	movea.l d0,a5
	move.b (a1)+,(a5)
	addq.l #1,d3
loc_3_0000008A:
	moveq.l #0,d0
	move.w d4,d0
	cmp.l d3,d0
	bhi.b loc_3_0000007E
	move.w #$1,(a2)
	move.l -$0004(a6),$0002(a2)
	move.w $0014(a0),$0006(a2)
	move.b $0016(a0),$0008(a2)
	move.b $0017(a0),$0009(a2)
	addq.w #1,(a4)
	moveq.l #10,d0
	adda.l d0,a2
loc_3_000000B4:
	movea.l (a0),a0
	bra.b loc_3_00000046
loc_3_000000B8:
	btst #1,d1
	beq.w loc_3_00000268
	clr.l -(a7)
	pea.l $0104.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_11_00000020.l
	movea.l d0,a3
	cmpa.w #$0,a3
	addq.l #8,a7
	beq.w loc_3_00000268
	move.l #$FFFFFFFE,-(a7)
	pea.l loc_4_00000000.l
	jsr loc_10_0000004C.l
	move.l d0,d5
	addq.l #8,a7
	beq.w loc_3_0000025A
	move.l d5,-(a7)
	jsr loc_10_000000B4.l
	move.l d0,-$0008(a6)
	move.l a3,-(a7)
	move.l d5,-(a7)
	jsr loc_10_0000007C.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.w loc_3_00000246
	tst.l $0004(a3)
	ble.w loc_3_00000246
loc_3_0000011A:
	move.l a3,-(a7)
	move.l d5,-(a7)
	jsr loc_10_00000098.l
	tst.l d0
	addq.l #8,a7
	beq.w loc_3_00000246
	pea.l $002E.w
	pea.l $0008(a3)
	jsr loc_7_00000084.l
	movea.l d0,a1
	cmpa.w #$0,a1
	addq.l #8,a7
	beq.b loc_3_0000011A
	pea.l loc_4_00000008.l
	move.l a1,-(a7)
	jsr loc_7_00000040.l
	tst.l d0
	addq.l #8,a7
	bne.b loc_3_0000011A
	tst.l $0004(a3)
	bge.b loc_3_0000011A
	pea.l $03ED.w
	pea.l $0008(a3)
	jsr loc_10_00000000.l
	move.l d0,d6
	addq.l #8,a7
	beq.b loc_3_0000011A
	pea.l $0008(a3)
	jsr loc_7_000000B6.l
	movea.l d0,a1
	moveq.l #1,d4
	addq.l #4,a7
loc_3_00000182:
	tst.b (a1)+
	beq.b loc_3_0000018A
	addq.w #1,d4
	bra.b loc_3_00000182
loc_3_0000018A:
	moveq.l #0,d0
	move.w d4,d0
	move.l -$0004(a6),d7
	sub.l d0,d7
	move.l d7,-$0004(a6)
	moveq.l #0,d0
	move.w d4,d0
	sub.l d0,d2
	tst.l d2
	blt.b loc_3_000001BE
	lea.l $0008(a3),a1
	moveq.l #0,d3
	bra.b loc_3_000001B6
loc_3_000001AA:
	move.l d3,d0
	add.l -$0004(a6),d0
	movea.l d0,a5
	move.b (a1)+,(a5)
	addq.l #1,d3
loc_3_000001B6:
	moveq.l #0,d0
	move.w d4,d0
	cmp.l d3,d0
	bhi.b loc_3_000001AA
loc_3_000001BE:
	pea.l $0004.w
	pea.l -$000C(a6)
	move.l d6,-(a7)
	jsr loc_10_00000030.l
	moveq.l #4,d3
	cmp.l d0,d3
	lea.l $000C(a7),a7
	bne.w loc_3_00000238
	cmpi.w #3840,-$000C(a6)
	bne.b loc_3_00000238
	moveq.l #0,d3
	bra.b loc_3_0000022E
loc_3_000001E6:
	pea.l $0104.w
	pea.l -$0110(a6)
	move.l d6,-(a7)
	jsr loc_10_00000030.l
	cmpi.l #260,d0
	lea.l $000C(a7),a7
	bne.b loc_3_0000022C
	moveq.l #10,d0
	sub.l d0,d2
	tst.l d2
	blt.b loc_3_0000022C
	move.w #$2,(a2)
	move.l -$0004(a6),$0002(a2)
	move.w -$0010(a6),$0006(a2)
	move.b -$000E(a6),$0008(a2)
	move.b -$000D(a6),$0009(a2)
	addq.w #1,(a4)
	moveq.l #10,d0
	adda.l d0,a2
loc_3_0000022C:
	addq.l #1,d3
loc_3_0000022E:
	moveq.l #0,d0
	move.w -$000A(a6),d0
	cmp.l d3,d0
	bhi.b loc_3_000001E6
loc_3_00000238:
	move.l d6,-(a7)
	jsr loc_10_0000001C.l
	addq.l #4,a7
	bra.w loc_3_0000011A
loc_3_00000246:
	move.l -$0008(a6),-(a7)
	jsr loc_10_000000B4.l
	move.l d5,-(a7)
	jsr loc_10_00000068.l
	addq.l #8,a7
loc_3_0000025A:
	pea.l $0104.w	; KNOWN: arg +8 byteSize unsigned long
	move.l a3,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_11_00000038.l
	addq.l #8,a7
loc_3_00000268:
	tst.l d2
	bge.b loc_3_00000272
	move.l d2,d0
	neg.l d0
	bra.b loc_3_00000274
loc_3_00000272:
	moveq.l #0,d0
loc_3_00000274:
	movem.l (a7)+,d2-d7/a2-a5
	unlk a6
	rts
    SECTION section_4,data
loc_4_00000000:
	dc.b $46,$4F,$4E,$54,$53,$3A,$00,$00
loc_4_00000008:
	dc.b $2E,$66,$6F,$6E,$74,$00,$00,$00
    SECTION section_5,code
loc_5_00000000:
	movem.l d2-d6,-(a7)
	movea.l $0018(a7),a0
	movea.l $001C(a7),a1
	tst.w $0100(a1)
	beq.w loc_5_000000D4
	move.l #$7FFF,d5
	move.w $0100(a1),d2
	sub.w $0004(a0),d2
	bcc.b loc_5_0000002E
	move.w d2,d0
	ext.l d0
	asl.l #6,d0
	add.l d0,d5
	bra.b loc_5_00000036
loc_5_0000002E:
	move.w d2,d0
	ext.l d0
	asl.l #8,d0
	sub.l d0,d5
loc_5_00000036:
	moveq.l #0,d2
	move.b $0006(a0),d2
	moveq.l #0,d0
	move.b $0102(a1),d0
	eor.w d0,d2
	moveq.l #0,d4
	move.b $0007(a0),d4
	moveq.l #0,d0
	move.b $0103(a1),d0
	eor.w d0,d4
	moveq.l #1,d3
	clr.w d6
loc_5_00000056:
	move.w d3,d0
	ext.l d0
	move.w d2,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_5_0000008E
	moveq.l #0,d0
	move.b $0102(a1),d0
	move.w d3,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_5_00000080
	move.w d6,d0
	asl.w #2,d0
	movea.l #loc_6_00000028,a0
	sub.l $0(a0,d0.w),d5
	bra.b loc_5_0000008E
loc_5_00000080:
	move.w d6,d0
	asl.w #2,d0
	movea.l #loc_6_00000008,a0
	sub.l $0(a0,d0.w),d5
loc_5_0000008E:
	move.w d3,d0
	ext.l d0
	move.w d4,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_5_000000C6
	moveq.l #0,d0
	move.b $0103(a1),d0
	move.w d3,d1
	ext.l d1
	and.l d1,d0
	beq.b loc_5_000000B8
	move.w d6,d0
	asl.w #2,d0
	movea.l #loc_6_00000068,a0
	sub.l $0(a0,d0.w),d5
	bra.b loc_5_000000C6
loc_5_000000B8:
	move.w d6,d0
	asl.w #2,d0
	movea.l #loc_6_00000048,a0
	sub.l $0(a0,d0.w),d5
loc_5_000000C6:
	add.w d3,d3
	addq.w #1,d6
	moveq.l #7,d0
	cmp.w d6,d0
	bgt.b loc_5_00000056
	move.l d5,d0
	bra.b loc_5_000000DA
loc_5_000000D4:
	move.l #$FFFF8001,d0
loc_5_000000DA:
	movem.l (a7)+,d2-d6
	rts
loc_5_000000E0:
	link a6,#-286
	movem.l d2-d7/a2-a5,-(a7)
	movea.l $0008(a6),a2
	movea.l a2,a0
	lea.l -$001A(a6),a1
	moveq.l #7,d2
loc_5_000000F4:
	move.b (a0)+,(a1)+
	dbf.w d2,loc_5_000000F4
	move.l (a2),-(a7)
	jsr loc_7_000000B6.l
	move.l d0,-$001A(a6)
	pea.l -$001A(a6)
	jsr loc_12_00000000.l
	move.l d0,-$0004(a6)
	movea.l -$0004(a6),a3
	cmpa.w #$0,a3
	addq.l #8,a7
	beq.b loc_5_00000132
	move.w $0014(a3),-$001E(a6)
	move.b $0016(a3),-$001C(a6)
	move.b $0017(a3),-$001B(a6)
loc_5_00000132:
	move.l #$FFFFFFFE,-(a7)
	pea.l loc_6_00000000.l
	jsr loc_10_0000004C.l
	movea.l d0,a4
	exg d7,a4
	tst.l d7
	exg d7,a4
	addq.l #8,a7
	bne.b loc_5_00000158
	move.l -$0004(a6),d0
	bra.w loc_5_0000035E
loc_5_00000158:
	move.l a4,-(a7)
	jsr loc_10_000000B4.l
	move.l d0,-$000C(a6)
	move.l #$FFFFFFFE,-(a7)
	move.l (a2),-(a7)
	jsr loc_10_0000004C.l
	move.l d0,-$0008(a6)
	lea.l $000C(a7),a7
	beq.w loc_5_0000032C
	pea.l $03ED.w
	move.l (a2),-(a7)
	jsr loc_10_00000000.l
	move.l d0,d6
	addq.l #8,a7
	beq.w loc_5_00000320
	pea.l $0004.w
	pea.l -$0012(a6)
	move.l d6,-(a7)
	jsr loc_10_00000030.l
	moveq.l #4,d2
	cmp.l d0,d2
	lea.l $000C(a7),a7
	bne.w loc_5_00000316
	move.w #$F00,-$0012(a6)
	beq.w loc_5_00000316
	moveq.l #0,d4
	move.w -$0010(a6),d4
	muls.w #$104,d4
	clr.l -(a7)
	move.l d4,-(a7)	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_11_00000020.l
	move.l d0,d5
	addq.l #8,a7
	beq.w loc_5_00000316
	move.l d4,-(a7)
	move.l d5,-(a7)
	move.l d6,-(a7)
	jsr loc_10_00000030.l
	cmp.l d0,d4
	lea.l $000C(a7),a7
	bne.w loc_5_0000030A
loc_5_000001EA:
	exg d7,a3
	tst.l d7
	exg d7,a3
	beq.b loc_5_00000206
	pea.l -$011E(a6)
	pea.l -$001A(a6)
	jsr loc_5_00000000(pc)
	move.w d0,-$000E(a6)
	addq.l #8,a7
	bra.b loc_5_0000020A
loc_5_00000206:
	clr.w -$000E(a6)
loc_5_0000020A:
	moveq.l #-1,d3
	clr.w d7
	movea.w d7,a2
	bra.b loc_5_0000023A
loc_5_00000212:
	moveq.l #0,d2
	move.w a2,d2
	mulu.w #$104,d2
	add.l d5,d2
	movea.l d2,a5
	pea.l (a5)
	pea.l -$001A(a6)
	jsr loc_5_00000000(pc)
	move.w d0,d2
	cmp.w -$000E(a6),d2
	addq.l #8,a7
	ble.b loc_5_00000238
	move.w d2,-$000E(a6)
	move.w a2,d3
loc_5_00000238:
	addq.w #1,a2
loc_5_0000023A:
	move.w -$0010(a6),d0
	cmp.w a2,d0
	bhi.b loc_5_00000212
	tst.w d3
	blt.w loc_5_00000304
	move.w d3,d2
	ext.l d2
	mulu.w #$104,d2
	add.l d5,d2
	movea.l d2,a5
	pea.l (a5)
	jsr loc_10_000000C8.l
	move.l d0,d2
	movea.l d2,a0
	lsl.l #2,d2
	addq.l #8,d2
	movea.l d2,a1
	movea.l a1,a2
	moveq.l #8,d2
	cmp.l a1,d2
	addq.l #4,a7
	beq.w loc_5_000002F4
	cmpi.w #3968,$000E(a2)
	bne.b loc_5_000002D8
	move.l a0,$0012(a2)
	move.l -$001A(a6),-(a7)
	pea.l $0016(a2)
	jsr loc_7_00000000.l
	ori.b #2,$004D(a2)
	jsr loc_11_00000000.l
	pea.l $0036(a2)
	jsr loc_12_00000028.l
	addq.w #1,$0054(a2)
	move.l a2,-(a7)
	movea.l loc_2_00000000.l,a1
	pea.l $002A(a1)	; KNOWN: arg +4 list LH
	jsr loc_11_00000050.l
	movea.l loc_2_00000000.l,a0
	addq.w #1,$0028(a0)
	jsr loc_11_00000010.l
	moveq.l #-1,d3
	lea.l $0036(a2),a0
	move.l a0,-$0004(a6)
	lea.l $0014(a7),a7
	bra.b loc_5_00000304
loc_5_000002D8:
	move.l a0,-(a7)
	jsr loc_10_000000DC.l
	move.w d3,d2
	ext.l d2
	mulu.w #$104,d2
	movea.l d2,a0
	adda.l d5,a0
	clr.w $0100(a0)
	addq.l #4,a7
	bra.b loc_5_00000304
loc_5_000002F4:
	move.w d3,d2
	ext.l d2
	mulu.w #$104,d2
	movea.l d2,a0
	adda.l d5,a0
	clr.w $0100(a0)
loc_5_00000304:
	tst.w d3
	bge.w loc_5_000001EA
loc_5_0000030A:
	move.l d4,-(a7)	; KNOWN: arg +8 byteSize unsigned long
	move.l d5,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_11_00000038.l
	addq.l #8,a7
loc_5_00000316:
	move.l d6,-(a7)
	jsr loc_10_0000001C.l
	addq.l #4,a7
loc_5_00000320:
	move.l -$0008(a6),-(a7)
	jsr loc_10_00000068.l
	addq.l #4,a7
loc_5_0000032C:
	move.l -$000C(a6),-(a7)
	jsr loc_10_000000B4.l
	move.l a4,-(a7)
	jsr loc_10_00000068.l
	exg d7,a3
	tst.l d7
	exg d7,a3
	addq.l #8,a7
	beq.b loc_5_0000035A
	move.l -$0004(a6),d7
	cmp.l a3,d7
	beq.b loc_5_0000035A
	move.l a3,-(a7)
	jsr loc_12_00000014.l
	addq.l #4,a7
loc_5_0000035A:
	move.l -$0004(a6),d0
loc_5_0000035E:
	movem.l (a7)+,d2-d7/a2-a5
	unlk a6
	rts
	dc.b $00,$00
    SECTION section_6,data
loc_6_00000000:
	dc.b $46,$4F,$4E,$54,$53,$3A,$00,$00
loc_6_00000008:
	dc.b $00,$00,$00,$04,$00,$00,$00,$08,$00,$00,$00,$10
	dcb.b $14,$00
loc_6_00000028:
	dc.b $00,$00,$00,$80,$00,$00,$00,$80,$00,$00,$00,$80
	dcb.b $14,$00
loc_6_00000048:
	dc.b $00,$00,$00,$01,$00,$00,$00,$01,$00,$00,$80,$00,$00,$00,$00,$20
	dc.b $00,$00,$00,$20,$00,$00,$00,$20,$00,$00,$00,$02,$00,$00,$00,$00
loc_6_00000068:
	dc.b $00,$00,$00,$01,$00,$00,$00,$01,$00,$00,$80,$00,$00,$00,$00,$20
	dc.b $00,$00,$00,$20,$00,$00,$00,$80,$00,$00,$00,$02,$00,$00,$00,$00
    SECTION section_7,code
loc_7_00000000:
	movea.l $0004(a7),a1
	movea.l $0008(a7),a0
loc_7_00000008:
	move.b (a0),(a1)+
	tst.b (a0)+
	bne.b loc_7_00000008
	rts
	dc.b $2F,$02,$20,$6F,$00,$08,$24,$2F,$00,$0C,$4A,$10,$67,$04,$52,$88
	dc.b $60,$F8,$2F,$02,$2F,$08,$4E,$BA,$FF,$D8,$50,$8F,$24,$1F,$4E,$75
loc_7_00000030:
	movea.l $0004(a7),a0
	moveq.l #0,d0
loc_7_00000036:
	tst.b (a0)+
	beq.b loc_7_0000003E
	addq.l #1,d0
	bra.b loc_7_00000036
loc_7_0000003E:
	rts
loc_7_00000040:
	movea.l $0004(a7),a1
	movea.l $0008(a7),a0
loc_7_00000048:
	move.b (a0),d0
	cmp.b (a1)+,d0
	bne.b loc_7_00000056
	tst.b (a0)+
	bne.b loc_7_00000048
	moveq.l #0,d0
	bra.b loc_7_00000066
loc_7_00000056:
	move.b (a0),d0
	subq.l #1,a1
	movea.l a1,a0
	cmp.b (a0),d0
	ble.b loc_7_00000064
	moveq.l #-1,d0
	bra.b loc_7_00000066
loc_7_00000064:
	moveq.l #1,d0
loc_7_00000066:
	rts
	dc.b $20,$6F,$00,$04,$10,$2F,$00,$0B,$12,$10,$67,$0C,$B2,$00,$66,$04
	dc.b $20,$08,$60,$06,$52,$88,$60,$F0,$70,$00,$4E,$75
loc_7_00000084:
	movem.l d2-d3,-(a7)
	move.l $000C(a7),d3
	move.b $0013(a7),d2
	move.l d3,-(a7)
	jsr loc_7_00000030(pc)
	subq.l #1,d0
	movea.l d0,a0
	adda.l d3,a0
	addq.l #4,a7
loc_7_0000009E:
	cmpa.l d3,a0
	bcs.b loc_7_000000AE
	cmp.b (a0),d2
	bne.b loc_7_000000AA
	move.l a0,d0
	bra.b loc_7_000000B0
loc_7_000000AA:
	subq.l #1,a0
	bra.b loc_7_0000009E
loc_7_000000AE:
	moveq.l #0,d0
loc_7_000000B0:
	movem.l (a7)+,d2-d3
	rts
loc_7_000000B6:
	movem.l d2-d3,-(a7)
	move.l $000C(a7),d2
	pea.l $002F.w
	move.l d2,-(a7)
	jsr loc_7_00000084(pc)
	move.l d0,d3
	addq.l #8,a7
	bne.b loc_7_000000E2
	pea.l $003A.w
	move.l d2,-(a7)
	jsr loc_7_00000084(pc)
	move.l d0,d3
	addq.l #8,a7
	bne.b loc_7_000000E2
	move.l d2,d0
	bra.b loc_7_000000E4
loc_7_000000E2:
	move.l d3,d0
loc_7_000000E4:
	movem.l (a7)+,d2-d3
	rts
	dc.b $00,$00
    SECTION section_8,data
    SECTION section_9,code
    SECTION section_10,code
loc_10_00000000:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$001E(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_10_0000001C:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$0024(a6)
	movea.l (a7)+,a6
	rts
loc_10_00000030:
	movem.l d2-d3/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $0010(a7),d1-d3
	jsr -$002A(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
loc_10_0000004C:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$0054(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_10_00000068:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$005A(a6)
	movea.l (a7)+,a6
	rts
loc_10_0000007C:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$0066(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_10_00000098:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000008.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$006C(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_10_000000B4:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$007E(a6)
	movea.l (a7)+,a6
	rts
loc_10_000000C8:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$0096(a6)
	movea.l (a7)+,a6
	rts
loc_10_000000DC:
	move.l a6,-(a7)
	movea.l loc_2_00000008.l,a6
	move.l $0008(a7),d1
	jsr -$009C(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_11,code
loc_11_00000000:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOForbid(a6)
	movea.l (a7)+,a6
	rts
loc_11_00000010:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	rts
loc_11_00000020:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	movem.l $0008(a7),d0-d1	; KNOWN: arg +4 byteSize unsigned long | KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_11_00000038:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 memoryBlock APTR
	move.l $000C(a7),d0	; KNOWN: arg +8 byteSize unsigned long
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	rts
loc_11_00000050:
	move.l a6,-(a7)
	movea.l loc_2_00000004.l,a6
	movem.l $0008(a7),a0-a1	; KNOWN: arg +4 list LH | KNOWN: arg +8 node LN
	jsr _LVOAddTail(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
    SECTION section_12,code
loc_12_00000000:
	move.l a6,-(a7)
	movea.l loc_2_0000000C.l,a6
	movea.l $0008(a7),a0
	jsr -$0048(a6)
	movea.l (a7)+,a6
	rts
loc_12_00000014:
	move.l a6,-(a7)
	movea.l loc_2_0000000C.l,a6
	movea.l $0008(a7),a1
	jsr -$004E(a6)
	movea.l (a7)+,a6
	rts
loc_12_00000028:
	move.l a6,-(a7)
	movea.l loc_2_0000000C.l,a6
	movea.l $0008(a7),a1
	jsr -$01E0(a6)
	movea.l (a7)+,a6
	rts
