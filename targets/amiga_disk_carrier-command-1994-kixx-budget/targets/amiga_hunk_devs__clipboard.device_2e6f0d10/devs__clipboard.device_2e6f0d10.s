    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"


    SECTION section_0,code
	dc.b $70,$00,$4E,$75
resident:	; STRUCT RT
    ; invalid overlap: decoded code at $0004 starts at structured data; emitted as data
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l resident_name	; APTR RT_ENDSKIP
	dc.b $00	; UBYTE RT_FLAGS
	dc.b $23	; UBYTE RT_VERSION
	dc.b NT_DEVICE	; UBYTE RT_TYPE = NT_DEVICE
	dc.b $00	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
resident_name:
    ; invalid overlap: decoded code at $001E starts at structured data; emitted as data
	dc.b "clipboard.device",$00	; string
	dc.b $00
resident_idstring:
    ; invalid overlap: decoded code at $0030 starts at structured data; emitted as data
	dc.b "clipboard 35.2 (9 May 1988)",$0D,$0A,$00	; string
resident_init:
	movem.l a0/a6,-(a7)
	jsr loc_1_00000000.l
	addq.w #8,a7
	rts
    ; KNOWN: base A6=clipboard.device:LIB
clipboard_device_dev_abortio:
	movem.l d0/a1,-(a7)
	jsr loc_1_00000AA6.l
	addq.w #8,a7
	rts
    ; KNOWN: base A6=clipboard.device:LIB
clipboard_device_dev_beginio:
	move.l a1,-(a7)
	jsr loc_1_00000D80.l
	addq.w #4,a7
	rts
    ; KNOWN: base A6=clipboard.device:LIB
clipboard_device_lib_extfunc:
	jmp loc_1_00000EB0.l
    ; KNOWN: base A6=clipboard.device:LIB
clipboard_device_lib_close:
	move.l a1,-(a7)
	jsr loc_1_00000EEA.l
	addq.w #4,a7
	rts
    ; KNOWN: base A6=clipboard.device:LIB
clipboard_device_lib_open:
	move.l a1,-(a7)
	jsr loc_1_00000F32.l
	addq.w #4,a7
    ; KNOWN: base A6=clipboard.device:LIB
clipboard_device_lib_expunge:
	rts
    SECTION section_1,code
loc_1_00000000:
	movem.l d2/a2,-(a7)
	move.l $000C(a7),d2
	movea.l $0010(a7),a2
	move.l a2,loc_2_0000010E.l
	clr.l -(a7)
	pea.l loc_2_00000000.l
	jsr loc_8_00000194.l
	move.l d0,loc_2_00000112.l
	addq.l #8,a7
	bne.b loc_1_0000002E
	moveq.l #0,d0
	bra.b loc_1_0000008A
loc_1_0000002E:
	move.l d2,loc_2_00000116.l
	pea.l loc_2_0000011A.l
	jsr loc_5_00000000.l
	jsr loc_8_00000000.l
	move.l loc_2_00000096.l,-(a7)
	pea.l $015E(a2)
	jsr loc_8_000000AC.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.b loc_1_00000074
	move.l loc_2_00000112.l,-(a7)
	jsr loc_8_0000016C.l
	jsr loc_8_00000010.l
	moveq.l #0,d0
	bra.b loc_1_00000088
loc_1_00000074:
	pea.l loc_2_0000008C.l
	jsr loc_8_00000180.l
	jsr loc_8_00000010.l
	moveq.l #1,d0
loc_1_00000088:
	addq.l #4,a7
loc_1_0000008A:
	movem.l (a7)+,d2/a2
	rts
loc_1_00000090:
	movem.l d2/a2-a3,-(a7)
	movea.l $0010(a7),a2
	jsr loc_8_00000000.l
	move.l #$10000,-(a7)
	pea.l $0212.w
	jsr loc_8_00000020.l
	movea.l d0,a3
	move.l a3,d2
	addq.l #8,a7
	beq.b loc_1_000000E4
	movea.l $006C(a2),a0
	tst.l $0004(a0)
	beq.b loc_1_000000D0
	movea.l $006C(a2),a0
	move.l $000E(a0),d0
	addq.l #1,d0
	move.l d0,$000E(a3)
	bra.b loc_1_000000D4
loc_1_000000D0:
	clr.l $000E(a3)
loc_1_000000D4:
	move.l a3,-(a7)
	pea.l $0064(a2)
	jsr loc_8_00000080.l
	addq.l #8,a7
	bra.b loc_1_000000E8
loc_1_000000E4:
	clr.w $007A(a2)
loc_1_000000E8:
	jsr loc_8_00000010.l
	move.l a3,d0
	movem.l (a7)+,d2/a2-a3
	rts
loc_1_000000F6:
	movem.l d2-d6/a2-a3,-(a7)
	movea.l $0020(a7),a2
	move.l $0024(a7),d2
	moveq.l #0,d4
	clr.l -(a7)
	jsr loc_8_000000C4.l
	movea.l d0,a3
	move.l $00B8(a3),d3
	moveq.l #-1,d0
	move.l d0,$00B8(a3)
	pea.l loc_2_0000000C.l
	jsr loc_7_000000DC.l
	move.l d3,$00B8(a3)
	tst.l d0
	addq.l #8,a7
	bne.w loc_1_000001B4
	moveq.l #-2,d3
	move.l d3,-(a7)
	pea.l loc_2_00000014.l
	jsr loc_7_00000098.l
	move.l d0,d5
	addq.l #8,a7
	beq.w loc_1_000001DA
	moveq.l #-2,d6
	move.l d6,-(a7)
	pea.l loc_2_0000001A.l
	jsr loc_7_00000098.l
	move.l d0,d3
	addq.l #8,a7
	bne.b loc_1_00000176
	cmpi.l #1006,d2
	bne.b loc_1_00000176
	pea.l loc_2_0000002A.l
	jsr loc_7_000000C8.l
	move.l d0,d3
	addq.l #4,a7
loc_1_00000176:
	tst.l d3
	beq.b loc_1_000001A8
	move.l $000E(a2),-(a7)	; KNOWN: arg +12 PutChProc void (*)() code_ptr
	pea.l loc_2_0000003A.l	; KNOWN: arg +8 DataStream APTR
	pea.l $0048(a2)	; KNOWN: arg +4 FormatString STRPTR string_ptr
	jsr loc_3_00000000.l
	move.l d2,-(a7)
	pea.l $0048(a2)
	jsr loc_7_00000000.l
	move.l d0,d4
	move.l d3,-(a7)
	jsr loc_7_000000B4.l
	lea.l $0018(a7),a7
loc_1_000001A8:
	move.l d5,-(a7)
	jsr loc_7_000000B4.l
	addq.l #4,a7
	bra.b loc_1_000001DA
loc_1_000001B4:
	move.l $000E(a2),-(a7)	; KNOWN: arg +12 PutChProc void (*)() code_ptr
	pea.l loc_2_0000004E.l	; KNOWN: arg +8 DataStream APTR
	pea.l $0048(a2)	; KNOWN: arg +4 FormatString STRPTR string_ptr
	jsr loc_3_00000000.l
	move.l d2,-(a7)
	pea.l $0048(a2)
	jsr loc_7_00000000.l
	move.l d0,d4
	lea.l $0014(a7),a7
loc_1_000001DA:
	move.l d4,d0
	movem.l (a7)+,d2-d6/a2-a3
	rts
loc_1_000001E2:
	movem.l d2/a2,-(a7)
	movea.l $000C(a7),a2
	jsr loc_8_00000000.l
	movea.l $0064(a2),a0
	bra.b loc_1_00000206
loc_1_000001F6:
	pea.l $0212.w
	move.l a0,-(a7)
	jsr loc_8_00000038.l
	movea.l d2,a0
	addq.l #8,a7
loc_1_00000206:
	move.l (a0),d2
	bne.b loc_1_000001F6
	pea.l $0064(a2)
	jsr loc_5_00000000.l
	clr.l $0072(a2)
	jsr loc_8_00000010.l
	addq.l #4,a7
	movem.l (a7)+,d2/a2
	rts
loc_1_00000226:
	movem.l d2-d5/a2-a4,-(a7)
	movea.l $0020(a7),a3
	movea.l $0024(a7),a4
	movea.l $0028(a7),a2
	jsr loc_8_00000000.l
	moveq.l #0,d5
	tst.w $007A(a3)
	beq.w loc_1_0000034C
	tst.l $0044(a3)
	beq.b loc_1_0000028A
	ori.b #64,$001E(a4)
	moveq.l #-1,d2
	move.l d2,-(a7)
	move.l $0034(a7),-(a7)
	move.l $0044(a3),-(a7)
	jsr loc_7_00000068.l
	moveq.l #-1,d1
	cmp.l d0,d1
	lea.l $000C(a7),a7
	beq.w loc_1_0000034C
	move.l $002C(a7),-(a7)
	move.l a2,-(a7)
	move.l $0044(a3),-(a7)
	jsr loc_7_00000030.l
	move.l d0,d5
	lea.l $000C(a7),a7
	bra.w loc_1_0000034C
loc_1_0000028A:
	move.l $0076(a3),d0
	cmp.l $0030(a7),d0
	bls.w loc_1_0000034C
	move.l $002C(a7),d0
	add.l $0030(a7),d0
	cmp.l $0076(a3),d0
	bls.b loc_1_000002AE
	move.l $0076(a3),d5
	sub.l $0030(a7),d5
	bra.b loc_1_000002B2
loc_1_000002AE:
	move.l $002C(a7),d5
loc_1_000002B2:
	tst.l d5
	beq.w loc_1_0000034C
	move.l $0030(a7),d1
	moveq.l #9,d0
	lsr.l d0,d1
	move.l $0030(a7),d3
	andi.l #511,d3
	movea.l $0072(a3),a1
	move.l a1,d2
	bne.b loc_1_000002D6
	movea.l $0064(a3),a1
loc_1_000002D6:
	move.l d1,d0
	cmp.l $000E(a1),d0
	beq.b loc_1_000002F8
	bra.b loc_1_000002E4
loc_1_000002E0:
	movea.l $0004(a1),a1
loc_1_000002E4:
	move.l d1,d0
	cmp.l $000E(a1),d0
	bcs.b loc_1_000002E0
	bra.b loc_1_000002F0
loc_1_000002EE:
	movea.l (a1),a1
loc_1_000002F0:
	move.l d1,d0
	cmp.l $000E(a1),d0
	bhi.b loc_1_000002EE
loc_1_000002F8:
	move.l d5,d4
	bra.b loc_1_00000344
loc_1_000002FC:
	move.l #$200,d0
	sub.l d3,d0
	cmp.l d0,d4
	bls.b loc_1_0000032A
	move.w d3,d2
	bra.b loc_1_00000314
loc_1_0000030C:
	move.w d2,d0
	move.b $12(a1,d0.w),(a2)+
	addq.w #1,d2
loc_1_00000314:
	cmpi.w #512,d2
	blt.b loc_1_0000030C
	movea.l (a1),a1
	move.l #$200,d0
	sub.l d3,d0
	sub.l d0,d4
	moveq.l #0,d3
	bra.b loc_1_00000344
loc_1_0000032A:
	move.w d3,d2
	bra.b loc_1_00000336
loc_1_0000032E:
	move.w d2,d0
	move.b $12(a1,d0.w),(a2)+
	addq.w #1,d2
loc_1_00000336:
	move.w d2,d0
	ext.l d0
	move.l d4,d1
	add.l d3,d1
	cmp.l d1,d0
	bcs.b loc_1_0000032E
	moveq.l #0,d4
loc_1_00000344:
	tst.l d4
	bne.b loc_1_000002FC
	move.l a1,$0072(a3)
loc_1_0000034C:
	jsr loc_8_00000010.l
	move.l d5,d0
	movem.l (a7)+,d2-d5/a2-a4
	rts
loc_1_0000035A:
	movem.l d2-d5/a2-a5,-(a7)
	movea.l $0024(a7),a2
	movea.l $0028(a7),a4
	movea.l $002C(a7),a3
	jsr loc_8_00000000.l
	moveq.l #0,d5
	tst.l $0044(a2)
	bne.w loc_1_0000046C
	move.l $0030(a7),d0
	add.l $0034(a7),d0
	cmpi.l #2000,d0
	bls.w loc_1_0000046C
	tst.w $007A(a2)
	beq.w loc_1_0000046C
	move.l #$20000,-(a7)
	jsr loc_8_00000050.l
	cmpi.l #16384,d0
	addq.l #4,a7
	bge.w loc_1_0000046C
	pea.l $03EE.w
	move.l a2,-(a7)
	jsr loc_1_000000F6(pc)
	move.l d0,$0044(a2)
	addq.l #8,a7
	beq.w loc_1_00000468
	move.l $0064(a2),d3
	bra.w loc_1_00000452
loc_1_000003C8:
	move.l $0076(a2),d0
	movea.l d3,a0
	move.l $000E(a0),d1
	asl.l #8,d1
	asl.l #1,d1
	cmp.l d1,d0
	bls.b loc_1_00000442
	move.l $0076(a2),d0
	movea.l d3,a0
	move.l $000E(a0),d1
	addq.l #1,d1
	asl.l #8,d1
	asl.l #1,d1
	cmp.l d1,d0
	bcc.b loc_1_0000041E
	move.l $0076(a2),d2
	andi.l #511,d2
	move.l $0076(a2),d0
	andi.l #511,d0
	move.l d0,-(a7)
	movea.l d3,a5
	pea.l $0012(a5)
	move.l $0044(a2),-(a7)
	jsr loc_7_0000004C.l
	cmp.l d0,d2
	lea.l $000C(a7),a7
	beq.b loc_1_00000442
	bra.b loc_1_0000043E
loc_1_0000041E:
	pea.l $0200.w
	movea.l d3,a5
	pea.l $0012(a5)
	move.l $0044(a2),-(a7)
	jsr loc_7_0000004C.l
	cmpi.l #512,d0
	lea.l $000C(a7),a7
	beq.b loc_1_00000442
loc_1_0000043E:
	clr.w $007A(a2)
loc_1_00000442:
	pea.l $0212.w
	move.l d3,-(a7)
	jsr loc_8_00000038.l
	move.l d4,d3
	addq.l #8,a7
loc_1_00000452:
	movea.l d3,a0
	move.l (a0),d4
	bne.w loc_1_000003C8
	pea.l $0064(a2)
	jsr loc_5_00000000.l
	addq.l #4,a7
	bra.b loc_1_0000046C
loc_1_00000468:
	clr.w $007A(a2)
loc_1_0000046C:
	tst.w $007A(a2)
	beq.w loc_1_000005A4
	tst.l $0044(a2)
	beq.b loc_1_000004B8
	ori.b #64,$001E(a4)
	moveq.l #-1,d2
	move.l d2,-(a7)
	move.l $0038(a7),-(a7)
	move.l $0044(a2),-(a7)
	jsr loc_7_00000068.l
	moveq.l #-1,d1
	cmp.l d0,d1
	lea.l $000C(a7),a7
	beq.w loc_1_000005A4
	move.l $0030(a7),-(a7)
	move.l a3,-(a7)
	move.l $0044(a2),-(a7)
	jsr loc_7_0000004C.l
	move.l d0,d5
	lea.l $000C(a7),a7
	bra.w loc_1_000005A4
loc_1_000004B8:
	move.l $0034(a7),d2
	moveq.l #9,d0
	lsr.l d0,d2
	move.l $0034(a7),d4
	andi.l #511,d4
	move.l $0072(a2),d3
	bne.b loc_1_000004DA
	move.l a2,-(a7)
	jsr loc_1_00000090(pc)
	move.l d0,d3
	addq.l #4,a7
loc_1_000004DA:
	tst.l d3
	beq.b loc_1_0000051E
	move.l d2,d0
	movea.l d3,a0
	cmp.l $000E(a0),d0
	beq.b loc_1_0000051E
	bra.b loc_1_000004F0
loc_1_000004EA:
	movea.l d3,a0
	move.l $0004(a0),d3
loc_1_000004F0:
	move.l d2,d0
	movea.l d3,a0
	cmp.l $000E(a0),d0
	bcs.b loc_1_000004EA
	bra.b loc_1_00000510
loc_1_000004FC:
	movea.l d3,a0
	move.l (a0),d3
	movea.l d3,a0
	tst.l (a0)
	bne.b loc_1_00000510
	move.l a2,-(a7)
	jsr loc_1_00000090(pc)
	move.l d0,d3
	addq.l #4,a7
loc_1_00000510:
	tst.l d3
	beq.b loc_1_0000051E
	move.l d2,d0
	movea.l d3,a0
	cmp.l $000E(a0),d0
	bhi.b loc_1_000004FC
loc_1_0000051E:
	bra.w loc_1_00000596
loc_1_00000522:
	move.l #$200,d0
	sub.l d4,d0
	cmp.l $0030(a7),d0
	bcc.b loc_1_00000572
	move.w d4,d2
	bra.b loc_1_0000053E
loc_1_00000534:
	move.w d2,d0
	movea.l d3,a1
	move.b (a3)+,$12(a1,d0.w)
	addq.w #1,d2
loc_1_0000053E:
	cmpi.w #512,d2
	blt.b loc_1_00000534
	movea.l d3,a0
	move.l (a0),d3
	movea.l d3,a0
	tst.l (a0)
	bne.b loc_1_00000558
	move.l a2,-(a7)
	jsr loc_1_00000090(pc)
	move.l d0,d3
	addq.l #4,a7
loc_1_00000558:
	move.l #$200,d0
	sub.l d4,d0
	add.l d0,d5
	move.l #$200,d0
	sub.l d4,d0
	sub.l d0,$0030(a7)
	moveq.l #0,d4
	bra.b loc_1_00000596
loc_1_00000572:
	move.w d4,d2
	bra.b loc_1_00000580
loc_1_00000576:
	move.w d2,d0
	movea.l d3,a1
	move.b (a3)+,$12(a1,d0.w)
	addq.w #1,d2
loc_1_00000580:
	move.w d2,d0
	ext.l d0
	move.l $0030(a7),d1
	add.l d4,d1
	cmp.l d1,d0
	bcs.b loc_1_00000576
	add.l $0030(a7),d5
	clr.l $0030(a7)
loc_1_00000596:
	tst.l d3
	beq.b loc_1_000005A0
	tst.l $0030(a7)
	bhi.b loc_1_00000522
loc_1_000005A0:
	move.l d3,$0072(a2)
loc_1_000005A4:
	jsr loc_8_00000010.l
	move.l d5,d0
	movem.l (a7)+,d2-d5/a2-a5
	rts
loc_1_000005B2:
	move.l a2,-(a7)
	movea.l $0008(a7),a2
	jsr loc_8_00000000.l
	btst.b #7,$001E(a2)
	bne.b loc_1_000005DA
	btst.b #0,$001E(a2)
	bne.b loc_1_000005E0
	move.l a2,-(a7)
	jsr loc_8_00000158.l
	addq.l #4,a7
	bra.b loc_1_000005E0
loc_1_000005DA:
	andi.b #254,$001E(a2)
loc_1_000005E0:
	ori.b #128,$001E(a2)
	jsr loc_8_00000010.l
	movea.l (a7)+,a2
	rts
loc_1_000005F0:
	movem.l d2/a2,-(a7)
	movea.l $000C(a7),a2
	move.l $0010(a7),d2
	btst.b #7,$001E(a2)
	bne.b loc_1_0000060E
	move.l a2,-(a7)
	jsr loc_8_00000098.l
	addq.l #4,a7
loc_1_0000060E:
	cmpa.l d2,a2
	beq.b loc_1_00000618
	andi.b #254,$001E(a2)
loc_1_00000618:
	move.l a2,-(a7)
	jsr loc_1_000005B2(pc)
	andi.b #223,$001E(a2)
	addq.l #4,a7
	movem.l (a7)+,d2/a2
	rts
loc_1_0000062C:
	movea.l $0004(a7),a0
	movea.l $008C(a0),a1
	movea.l $007C(a0),a0
	tst.l (a1)
	beq.b loc_1_00000652
	tst.l (a0)
	beq.b loc_1_00000650
	move.l $0030(a0),d0
	cmp.l $0030(a1),d0
	bge.b loc_1_0000064C
	bra.b loc_1_00000652
loc_1_0000064C:
	clr.w d0
loc_1_0000064E:
	bra.b loc_1_00000654
loc_1_00000650:
	bra.b loc_1_0000064C
loc_1_00000652:
	moveq.l #1,d0
loc_1_00000654:
	ext.l d0
	rts
loc_1_00000658:
	movea.l $0004(a7),a0
	movea.l $0008(a7),a1
	move.l $000C(a7),d0
	move.l $0028(a1),$00B4(a0)
	move.w $0010(a0),$00AE(a0)
	move.l $0030(a1),$00B0(a0)
	move.l d0,-(a7)
	move.l a1,-(a7)
	jsr loc_1_000005F0(pc)
	addq.l #8,a7
	rts
loc_1_00000682:
	movem.l d2/a2-a4,-(a7)
	movea.l $0014(a7),a2
	movea.l $0018(a7),a3
	ori.b #32,$001E(a3)
	tst.b $0042(a2)
	beq.b loc_1_000006A6
	andi.b #254,$001E(a3)
	moveq.l #0,d0
	bra.w loc_1_0000091C
loc_1_000006A6:
	move.b #$1,$0042(a2)
	moveq.l #1,d2
loc_1_000006AE:
	tst.w $0040(a2)
	bne.w loc_1_00000738
	move.l a2,-(a7)
	jsr loc_1_0000062C(pc)
	move.w d0,d0
	addq.l #4,a7
	beq.b loc_1_000006DA
	movea.l $007C(a2),a4
	tst.l (a4)
	beq.b loc_1_000006D8
	move.l $0030(a4),$003C(a2)
	move.w #$2,$0040(a2)
loc_1_000006D6:
	bra.b loc_1_00000738
loc_1_000006D8:
	bra.b loc_1_00000736
loc_1_000006DA:
	movea.l $008C(a2),a4
	tst.l (a4)
	beq.b loc_1_00000736
	move.l $0030(a4),$003C(a2)
	move.w $001C(a4),d0
	move.w d0,$0040(a2)
	cmpi.w #9,d0
	bne.b loc_1_00000704
	move.l a3,-(a7)
	move.l a4,-(a7)
	move.l a2,-(a7)
	jsr loc_1_00000658(pc)
	lea.l $000C(a7),a7
loc_1_00000704:
	tst.l $0044(a2)
	beq.b loc_1_00000726
	move.l $0044(a2),-(a7)
	jsr loc_7_0000001C.l
	clr.l $0044(a2)
	pea.l $0048(a2)
	jsr loc_7_00000084.l
	addq.l #8,a7
	bra.b loc_1_0000072E
loc_1_00000726:
	move.l a2,-(a7)
	jsr loc_1_000001E2(pc)
	addq.l #4,a7
loc_1_0000072E:
	move.w #$1,$007A(a2)
	bra.b loc_1_00000738
loc_1_00000736:
	clr.w d2
loc_1_00000738:
	cmpi.w #9,$0040(a2)
	bne.b loc_1_0000079C
	move.l a2,-(a7)
	jsr loc_1_0000062C(pc)
	move.w d0,d0
	addq.l #4,a7
	beq.b loc_1_0000076E
	movea.l $007C(a2),a4
	tst.l (a4)
	beq.b loc_1_0000076C
	pea.l $009A(a2)
	move.l $00B4(a2),-(a7)
	jsr loc_8_0000012C.l
	move.w #$3,$0040(a2)
	addq.l #8,a7
loc_1_0000076A:
	bra.b loc_1_0000079C
loc_1_0000076C:
	bra.b loc_1_0000079A
loc_1_0000076E:
	movea.l $008C(a2),a4
	tst.l (a4)
	beq.b loc_1_0000079A
	move.l $0030(a4),$003C(a2)
	move.w $001C(a4),d0
	move.w d0,$0040(a2)
	cmpi.w #9,d0
	bne.b loc_1_0000079C
	move.l a3,-(a7)
	move.l a4,-(a7)
	move.l a2,-(a7)
	jsr loc_1_00000658(pc)
	lea.l $000C(a7),a7
	bra.b loc_1_0000079C
loc_1_0000079A:
	clr.w d2
loc_1_0000079C:
	cmpi.w #2,$0040(a2)
	bne.w loc_1_00000846
	movea.l $007C(a2),a4
	tst.l (a4)
	beq.w loc_1_00000844
	btst.b #4,$001E(a4)
	beq.b loc_1_000007C2
	addq.w #1,$008A(a2)
	andi.b #239,$001E(a4)
loc_1_000007C2:
	move.l $0076(a2),d0
	cmp.l $002C(a4),d0
	bls.b loc_1_00000820
	tst.l $0028(a4)
	beq.b loc_1_000007F4
	move.l $002C(a4),-(a7)
	move.l $0024(a4),-(a7)
	move.l $0028(a4),-(a7)
	move.l a4,-(a7)
	move.l a2,-(a7)
	jsr loc_1_00000226(pc)
	move.l d0,$0020(a4)
	add.l d0,$002C(a4)
	lea.l $0014(a7),a7
	bra.b loc_1_0000082E
loc_1_000007F4:
	move.l $0024(a4),d0
	add.l $002C(a4),d0
	cmp.l $0076(a2),d0
	bcc.b loc_1_0000080A
	move.l $0024(a4),$0020(a4)
	bra.b loc_1_00000816
loc_1_0000080A:
	move.l $0076(a2),d0
	sub.l $002C(a4),d0
	move.l d0,$0020(a4)
loc_1_00000816:
	move.l $0020(a4),d0
	add.l d0,$002C(a4)
	bra.b loc_1_0000082E
loc_1_00000820:
	clr.l $0020(a4)
	moveq.l #-1,d0
	move.l d0,$0030(a4)
	subq.w #1,$008A(a2)
loc_1_0000082E:
	move.l a3,-(a7)
	move.l a4,-(a7)
	jsr loc_1_000005F0(pc)
	tst.w $008A(a2)
	addq.l #8,a7
	bne.b loc_1_00000846
	clr.w $0040(a2)
	bra.b loc_1_00000846
loc_1_00000844:
	clr.w d2
loc_1_00000846:
	cmpi.w #3,$0040(a2)
	bne.w loc_1_000008B6
	movea.l $008C(a2),a4
	tst.l (a4)
	beq.b loc_1_000008B4
	cmpi.w #3,$001C(a4)
	bne.b loc_1_000008A4
	move.l $002C(a4),-(a7)
	move.l $0024(a4),-(a7)
	move.l $0028(a4),-(a7)
	move.l a4,-(a7)
	move.l a2,-(a7)
	jsr loc_1_0000035A(pc)
	move.l d0,$0020(a4)
	add.l d0,$002C(a4)
	move.l $002C(a4),d0
	cmp.l $0076(a2),d0
	lea.l $0014(a7),a7
	bcc.b loc_1_00000890
	move.l $0076(a2),d0
	bra.b loc_1_00000894
loc_1_00000890:
	move.l $002C(a4),d0
loc_1_00000894:
	move.l d0,$0076(a2)
	move.l a3,-(a7)
	move.l a4,-(a7)
	jsr loc_1_000005F0(pc)
	addq.l #8,a7
	bra.b loc_1_000008B6
loc_1_000008A4:
	cmpi.w #4,$001C(a4)
	bne.b loc_1_000008B4
	move.w #$4,$0040(a2)
	bra.b loc_1_000008B6
loc_1_000008B4:
	clr.w d2
loc_1_000008B6:
	cmpi.w #4,$0040(a2)
	bne.b loc_1_00000904
	movea.l $008C(a2),a4
	moveq.l #8,d0
	cmp.l $0076(a2),d0
	bhi.b loc_1_000008EE
	pea.l $0004.w
	pea.l $0004.w
	pea.l $0076(a2)
	move.l a4,-(a7)
	move.l a2,-(a7)
	jsr loc_1_00000226(pc)
	moveq.l #4,d1
	cmp.l d0,d1
	lea.l $0014(a7),a7
	bne.b loc_1_000008EE
	addq.l #8,$0076(a2)
	bra.b loc_1_000008F2
loc_1_000008EE:
	clr.l $0076(a2)
loc_1_000008F2:
	clr.w $008A(a2)
	move.l a3,-(a7)
	move.l a4,-(a7)
	jsr loc_1_000005F0(pc)
	clr.w $0040(a2)
	addq.l #8,a7
loc_1_00000904:
	tst.w d2
	bne.w loc_1_000006AE
	btst.b #5,$001E(a3)
	beq.b loc_1_00000918
	andi.b #254,$001E(a3)
loc_1_00000918:
	clr.b $0042(a2)
loc_1_0000091C:
	movem.l (a7)+,d2/a2-a4
	rts
loc_1_00000922:
	move.l a2,-(a7)
	movea.l $0008(a7),a1
	movea.l $000C(a7),a0
	movea.l (a1),a2
loc_1_0000092E:
	move.l (a2),d1
	bra.b loc_1_00000942
loc_1_00000932:
	move.l $0030(a2),d0
	cmp.l $0030(a0),d0
	bgt.b loc_1_00000940
	movea.l d1,a2
	bra.b loc_1_0000092E
loc_1_00000940:
	moveq.l #0,d1
loc_1_00000942:
	tst.l d1
	bne.b loc_1_00000932
	move.l $0004(a2),-(a7)
	move.l a0,-(a7)
	move.l a1,-(a7)
	jsr loc_8_00000064.l
	lea.l $000C(a7),a7
	movea.l (a7)+,a2
	rts
loc_1_0000095C:
	movea.l $0004(a7),a0
	move.b #$FD,$001F(a0)
	move.l a0,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
	rts
loc_1_00000970:
	move.l $0004(a7),d0
	move.l d0,-(a7)
	jsr loc_1_0000095C(pc)
	addq.l #4,a7
	rts
loc_1_0000097E:
	move.l $0004(a7),d0
	move.l d0,-(a7)
	jsr loc_1_0000095C(pc)
	addq.l #4,a7
	rts
loc_1_0000098C:
	move.l $0004(a7),d0
	move.l d0,-(a7)
	jsr loc_1_0000095C(pc)
	addq.l #4,a7
	rts
loc_1_0000099A:
	move.l $0004(a7),d0
	move.l d0,-(a7)
	jsr loc_1_0000095C(pc)
	addq.l #4,a7
	rts
loc_1_000009A8:
	move.l d2,-(a7)
	move.l $0008(a7),d2
	move.l d2,-(a7)
	jsr loc_1_0000097E(pc)
	move.l d2,-(a7)
	jsr loc_1_0000099A(pc)
	move.l d2,-(a7)
	jsr loc_1_0000098C(pc)
	lea.l $000C(a7),a7
	move.l (a7)+,d2
	rts
loc_1_000009C8:
	movem.l a2-a3,-(a7)
	movea.l $000C(a7),a2
	movea.l $0018(a2),a3
	tst.l $0030(a2)
	bne.b loc_1_000009E6
	move.l $0038(a3),$0030(a2)
	ori.b #16,$001E(a2)
loc_1_000009E6:
	move.l $003C(a3),d0
	cmp.l $0030(a2),d0
	ble.b loc_1_00000A04
	clr.l $0020(a2)
	move.b #$1,$001F(a2)
	move.l a2,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
	bra.b loc_1_00000A1A
loc_1_00000A04:
	move.l a2,-(a7)
	pea.l $007C(a3)
	jsr loc_1_00000922(pc)
	move.l a2,-(a7)
	move.l a3,-(a7)
	jsr loc_1_00000682(pc)
	lea.l $0010(a7),a7
loc_1_00000A1A:
	movem.l (a7)+,a2-a3
	rts
loc_1_00000A20:
	movem.l a2-a3,-(a7)
	movea.l $000C(a7),a2
	movea.l $0018(a2),a3
	tst.l $0030(a2)
	bne.b loc_1_00000A3C
	addq.l #1,$0038(a3)
	move.l $0038(a3),$0030(a2)
loc_1_00000A3C:
	move.l $003C(a3),d0
	cmp.l $0030(a2),d0
	ble.b loc_1_00000A5A
	clr.l $0020(a2)
	move.b #$1,$001F(a2)
	move.l a2,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
	bra.b loc_1_00000A70
loc_1_00000A5A:
	move.l a2,-(a7)
	pea.l $008C(a3)
	jsr loc_1_00000922(pc)
	move.l a2,-(a7)
	move.l a3,-(a7)
	jsr loc_1_00000682(pc)
	lea.l $0010(a7),a7
loc_1_00000A70:
	movem.l (a7)+,a2-a3
	rts
loc_1_00000A76:
	movea.l $0004(a7),a0
	movea.l $0018(a0),a1
	move.l $0038(a1),$0030(a0)
	move.l a0,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
	rts
loc_1_00000A8E:
	movea.l $0004(a7),a0
	movea.l $0018(a0),a1
	move.l $003C(a1),$0030(a0)
	move.l a0,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
	rts
loc_1_00000AA6:
	link a6,#-24
	movem.l d2-d5/a2-a5,-(a7)
	move.l $0008(a6),d2
	movea.l $000C(a6),a2
	move.l #loc_5_00000000,d3
	move.l #resident_vectors,d4
	jsr loc_8_00000000.l
	movea.l d4,a5
	andi.b #247,$0032(a5)
	movea.l loc_2_0000011A.l,a3
loc_1_00000AD6:
	move.l (a3),d0
	movea.l a3,a4
	bra.b loc_1_00000AF2
loc_1_00000ADC:
	cmp.l $000E(a3),d2
	bls.b loc_1_00000AE6
	movea.l d0,a3
	bra.b loc_1_00000AD6
loc_1_00000AE6:
	cmp.l $000E(a3),d2
	bne.b loc_1_00000AF0
	moveq.l #0,d0
	movea.l d0,a4
loc_1_00000AF0:
	moveq.l #0,d0
loc_1_00000AF2:
	tst.l d0
	bne.b loc_1_00000ADC
	move.l a4,d0
	beq.w loc_1_00000D06
	move.l #$10001,-(a7)
	pea.l $00B8.w
	jsr loc_8_00000020.l
	movea.l d0,a3
	move.l a3,d5
	addq.l #8,a7
	bne.b loc_1_00000B26
	move.b #$FF,$001F(a2)
	jsr loc_8_00000010.l
	moveq.l #-1,d0
	bra.w loc_1_00000D76
loc_1_00000B26:
	move.l #loc_2_00000058,$000A(a3)
	move.l d2,$000E(a3)
	moveq.l #1,d0
	move.l d0,$0012(a3)
	pea.l $002A(a3)
	jsr loc_5_00000000.l
	moveq.l #1,d0
	move.l d0,$0038(a3)
	moveq.l #1,d0
	move.l d0,$003C(a3)
	move.b #$1,$0043(a3)
	pea.l $0064(a3)
	jsr loc_5_00000000.l
	clr.w $007A(a3)
	pea.l $007C(a3)
	jsr loc_5_00000000.l
	pea.l $008C(a3)
	jsr loc_5_00000000.l
	movea.l d4,a5
	addq.w #1,$0044(a5)
	move.l a3,$0018(a2)
	move.l $0004(a4),-(a7)
	move.l a3,-(a7)
	pea.l loc_2_0000011A.l
	jsr loc_8_00000064.l
	pea.l $03ED.w
	move.l a3,-(a7)
	jsr loc_1_000000F6(pc)
	move.l d0,d2
	lea.l $0024(a7),a7
	beq.w loc_1_00000CCC
	moveq.l #-1,d3
	move.l d3,-(a7)
	pea.l $0004.w
	move.l d2,-(a7)
	jsr loc_7_00000068.l
	moveq.l #-1,d1
	cmp.l d0,d1
	lea.l $000C(a7),a7
	beq.w loc_1_00000CBE
	pea.l $0004.w
	pea.l -$0004(a6)
	move.l d2,-(a7)
	jsr loc_7_00000030.l
	moveq.l #4,d1
	cmp.l d0,d1
	lea.l $000C(a7),a7
	bne.w loc_1_00000CBE
	move.w #$1,$007A(a3)
	addq.l #8,-$0004(a6)
	move.l -$0004(a6),$0076(a3)
	moveq.l #-1,d3
	move.l d3,-(a7)
	clr.l -(a7)
	move.l d2,-(a7)
	jsr loc_7_00000068.l
	moveq.l #-1,d1
	cmp.l d0,d1
	lea.l $000C(a7),a7
	bne.b loc_1_00000C0A
	clr.w $007A(a3)
loc_1_00000C0A:
	bra.b loc_1_00000C44
loc_1_00000C0C:
	move.l a3,-(a7)
	jsr loc_1_00000090(pc)
	movea.l d0,a0
	move.l a0,d3
	addq.l #4,a7
	bne.b loc_1_00000C1C
	bra.b loc_1_00000C38
loc_1_00000C1C:
	pea.l $0200.w
	pea.l $0012(a0)
	move.l d2,-(a7)
	jsr loc_7_00000030.l
	cmpi.l #512,d0
	lea.l $000C(a7),a7
	beq.b loc_1_00000C3C
loc_1_00000C38:
	clr.w $007A(a3)
loc_1_00000C3C:
	subi.l #512,-$0004(a6)
loc_1_00000C44:
	tst.w $007A(a3)
	beq.b loc_1_00000C54
	cmpi.l #512,-$0004(a6)
	bgt.b loc_1_00000C0C
loc_1_00000C54:
	tst.w $007A(a3)
	beq.b loc_1_00000C90
	tst.l -$0004(a6)
	ble.b loc_1_00000C90
	move.l a3,-(a7)
	jsr loc_1_00000090(pc)
	movea.l d0,a0
	move.l a0,d3
	addq.l #4,a7
	bne.b loc_1_00000C70
	bra.b loc_1_00000C8C
loc_1_00000C70:
	move.l -$0004(a6),-(a7)
	pea.l $0012(a0)
	move.l d2,-(a7)
	jsr loc_7_00000030.l
	move.l d0,d1
	cmp.l -$0004(a6),d1
	lea.l $000C(a7),a7
	beq.b loc_1_00000C90
loc_1_00000C8C:
	clr.w $007A(a3)
loc_1_00000C90:
	tst.w $007A(a3)
	bne.b loc_1_00000CBE
	move.l a3,-(a7)
	jsr loc_1_000001E2(pc)
	moveq.l #-1,d3
	move.l d3,-(a7)
	move.l $0076(a3),-(a7)
	move.l d2,-(a7)
	jsr loc_7_00000068.l
	tst.l d0
	lea.l $0010(a7),a7
	bne.b loc_1_00000CBE
	move.l d2,$0044(a3)
	moveq.l #0,d2
	clr.w $007A(a3)
loc_1_00000CBE:
	tst.l d2
	beq.b loc_1_00000CCC
	move.l d2,-(a7)
	jsr loc_7_0000001C.l
	addq.l #4,a7
loc_1_00000CCC:
	tst.w $007A(a3)
	bne.b loc_1_00000CD6
	clr.l $0076(a3)
loc_1_00000CD6:
	clr.b $0043(a3)
	bra.b loc_1_00000CF2
loc_1_00000CDC:
	moveq.l #1,d1
	move.b $0009(a0),d0
	asl.l d0,d1
	move.l d1,-(a7)
	move.l $000E(a0),-(a7)
	jsr loc_8_000000EC.l
	addq.l #8,a7
loc_1_00000CF2:
	pea.l $0016(a3)
	jsr loc_8_00000144.l
	movea.l d0,a0
	move.l a0,d2
	addq.l #4,a7
	beq.b loc_1_00000D68
	bra.b loc_1_00000CDC
loc_1_00000D06:
	addq.l #1,$0012(a3)
	movea.l d4,a0
	addq.w #1,$0044(a0)
	move.l a3,$0018(a2)
	cmpi.b #1,$0043(a3)
	bne.b loc_1_00000D68
	clr.l -(a7)
	jsr loc_8_000000C4.l
	move.l d0,-$000A(a6)
	moveq.l #-1,d2
	move.l d2,-(a7)
	jsr loc_8_00000104.l
	move.b d0,-$000F(a6)
	pea.l -$0018(a6)
	pea.l $0016(a3)
	jsr loc_8_0000012C.l
	moveq.l #1,d1
	move.b -$000F(a6),d0
	asl.l d0,d1
	move.l d1,-(a7)
	jsr loc_8_000000D8.l
	move.b -$000F(a6),d1
	ext.w d1
	ext.l d1
	move.l d1,-(a7)
	jsr loc_8_00000118.l
	lea.l $0018(a7),a7
loc_1_00000D68:
	jsr loc_8_00000010.l
	move.b $001F(a2),d0
	ext.w d0
	ext.l d0
loc_1_00000D76:
	movem.l -$0038(a6),d2-d5/a2-a5
	unlk a6
	rts
loc_1_00000D80:
	movem.l d2/a2-a4,-(a7)
	movea.l $0014(a7),a2
	movea.l $0018(a2),a3
	jsr loc_8_00000000.l
	subq.l #1,$0012(a3)
	bne.w loc_1_00000E82
	tst.w $007A(a3)
	beq.w loc_1_00000E38
	tst.l $0044(a3)
	bne.w loc_1_00000E38
	moveq.l #1,d0
	cmp.l $003C(a3),d0
	bge.w loc_1_00000E38
	pea.l $03EE.w
	move.l a3,-(a7)
	jsr loc_1_000000F6(pc)
	move.l d0,$0044(a3)
	addq.l #8,a7
	beq.w loc_1_00000E38
	move.l $0076(a3),d2
	movea.l $0064(a3),a4
	bra.b loc_1_00000E2E
loc_1_00000DD2:
	tst.l (a4)
	beq.b loc_1_00000E2A
	cmpi.l #512,d2
	ble.b loc_1_00000E08
	pea.l $0200.w
	pea.l $0012(a4)
	move.l $0044(a3),-(a7)
	jsr loc_7_0000004C.l
	cmpi.l #512,d0
	lea.l $000C(a7),a7
	beq.b loc_1_00000E00
	clr.w $007A(a3)
loc_1_00000E00:
	subi.l #512,d2
	bra.b loc_1_00000E26
loc_1_00000E08:
	move.l d2,-(a7)
	pea.l $0012(a4)
	move.l $0044(a3),-(a7)
	jsr loc_7_0000004C.l
	cmp.l d0,d2
	lea.l $000C(a7),a7
	beq.b loc_1_00000E24
	clr.w $007A(a3)
loc_1_00000E24:
	moveq.l #0,d2
loc_1_00000E26:
	movea.l (a4),a4
	bra.b loc_1_00000E2E
loc_1_00000E2A:
	clr.w $007A(a3)
loc_1_00000E2E:
	tst.w $007A(a3)
	beq.b loc_1_00000E38
	tst.l d2
	bgt.b loc_1_00000DD2
loc_1_00000E38:
	tst.l $0044(a3)
	beq.b loc_1_00000E62
	move.l $0044(a3),-(a7)
	jsr loc_7_0000001C.l
	tst.w $007A(a3)
	addq.l #4,a7
	beq.b loc_1_00000E56
	tst.l $0076(a3)
	bne.b loc_1_00000E6A
loc_1_00000E56:
	pea.l $0048(a3)
	jsr loc_7_00000084.l
	bra.b loc_1_00000E68
loc_1_00000E62:
	move.l a3,-(a7)
	jsr loc_1_000001E2(pc)
loc_1_00000E68:
	addq.l #4,a7
loc_1_00000E6A:
	move.l a3,-(a7)
	jsr loc_8_00000098.l
	pea.l $00B8.w
	move.l a3,-(a7)
	jsr loc_8_00000038.l
	lea.l $000C(a7),a7
loc_1_00000E82:
	moveq.l #0,d0
	move.l d0,$0014(a2)
	move.l d0,$0018(a2)
	subq.w #1,loc_2_000000AC.l
	bne.b loc_1_00000EA4
	btst.b #3,loc_2_0000009A.l
	beq.b loc_1_00000EA4
	jsr loc_1_00000EB0.l
loc_1_00000EA4:
	jsr loc_8_00000010.l
	movem.l (a7)+,d2/a2-a4
	rts
loc_1_00000EB0:
	move.l a2,-(a7)
	movea.l #resident_vectors,a2
	tst.w $0044(a2)
	bne.b loc_1_00000EDE
	move.l loc_2_00000112.l,-(a7)
	jsr loc_8_0000016C.l
	pea.l $0024(a2)
	jsr loc_8_00000098.l
	move.l loc_2_00000116.l,d0
	addq.l #8,a7
	bra.b loc_1_00000EE6
loc_1_00000EDE:
	ori.b #8,$0032(a2)
	moveq.l #0,d0
loc_1_00000EE6:
	movea.l (a7)+,a2
	rts
loc_1_00000EEA:
	move.l a2,-(a7)
	movea.l $0008(a7),a2
	jsr loc_8_00000000.l
	move.b #$5,$0008(a2)
	andi.b #79,$001E(a2)
	cmpi.w #12,$001C(a2)
	bcs.b loc_1_00000F12
	move.l a2,-(a7)
	jsr loc_1_0000095C(pc)
	bra.b loc_1_00000F26
loc_1_00000F12:
	move.l a2,-(a7)
	move.w $001C(a2),d0
	asl.w #2,d0
	movea.l #loc_2_000000DE,a0
	movea.l $0(a0,d0.w),a0
	jsr (a0)
loc_1_00000F26:
	addq.l #4,a7
	jsr loc_8_00000010.l
	movea.l (a7)+,a2
	rts
loc_1_00000F32:
	move.l a2,-(a7)
	movea.l $0008(a7),a2
	jsr loc_8_00000000.l
	btst.b #7,$001E(a2)
	bne.b loc_1_00000F6E
	btst.b #6,$001E(a2)
	bne.b loc_1_00000F6E
	move.b #$FE,$001F(a2)
	btst.b #5,$001E(a2)
	beq.b loc_1_00000F66
	move.l a2,-(a7)
	jsr loc_8_00000098.l
	addq.l #4,a7
loc_1_00000F66:
	move.l a2,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
loc_1_00000F6E:
	jsr loc_8_00000010.l
	movea.l (a7)+,a2
	rts
    SECTION section_2,data
loc_2_00000000:
	dc.b "dos.library",$00	; string
loc_2_0000000C:
	dc.b $43,$4C,$49,$50,$53,$3A,$00,$00
loc_2_00000014:
	dc.b "DEVS:",$00	; string
loc_2_0000001A:
	dc.b "DEVS:clipboards",$00	; string
loc_2_0000002A:
	dc.b "DEVS:clipboards",$00	; string
loc_2_0000003A:
	dc.b "DEVS:clipboards/%ld",$00	; string
loc_2_0000004E:
	dc.b "CLIPS:%ld",$00	; string
loc_2_00000058:
	dc.b "clipboard.unit",$00	; string
	dc.b $00
resident_vectors:
	jmp clipboard_device_lib_open.l
loc_2_0000006E:
	jmp clipboard_device_lib_close.l
loc_2_00000074:
	jmp clipboard_device_lib_expunge.l
loc_2_0000007A:
	jmp clipboard_device_lib_extfunc.l
loc_2_00000080:
	jmp clipboard_device_dev_beginio.l
loc_2_00000086:
	jmp clipboard_device_dev_abortio.l
loc_2_0000008C:
	dcb.b $8,$00
	dc.b $03,$00
loc_2_00000096:
	dc.l loc_2_000000AE
loc_2_0000009A:
	dc.b $06,$00,$00,$24,$00,$22,$00,$23,$00,$02
	dc.l loc_2_000000C0
	dc.b $00,$00,$00,$00
loc_2_000000AC:
	dc.b $00,$00
loc_2_000000AE:
	dc.b "clipboard.device",$00	; string
	dc.b $00
loc_2_000000C0:
	dc.b "clipboard 35.2 (9 May 1988)"	; string
	dc.b $0A,$0D,$00
loc_2_000000DE:
	dc.l loc_1_0000095C	; pointer_table
	dc.l loc_1_000009A8
	dc.l loc_1_000009C8
	dc.l loc_1_00000A20
	dc.l loc_1_00000A20
	dc.l loc_1_00000970
	dc.l loc_1_0000097E
	dc.l loc_1_0000098C
	dc.l loc_1_0000099A
	dc.l loc_1_00000A20
	dc.l loc_1_00000A76
	dc.l loc_1_00000A8E
loc_2_0000010E:
	dc.b $00,$00,$00,$00
loc_2_00000112:
	dc.b $00,$00,$00,$00
loc_2_00000116:
	dc.b $00,$00,$00,$00
loc_2_0000011A:
	dcb.b $E,$00
    SECTION section_3,code
loc_3_00000000:
	movem.l a2-a4/a6,-(a7)
	movea.l $0014(a7),a3
	movea.l $0018(a7),a0
	lea.l $001C(a7),a1
	lea.l loc_3_00000024(pc),a2
	movea.l $00000004.l,a6
	jsr _LVORawDoFmt(a6)
	movem.l (a7)+,a2-a4/a6
	rts
loc_3_00000024:
	dc.b $16,$C0,$4E,$75
    SECTION section_4,code
    SECTION section_5,code
loc_5_00000000:
	movea.l $0004(a7),a0
	move.l a0,(a0)
	addq.l #4,(a0)
	clr.l $0004(a0)
	move.l a0,$0008(a0)
	rts
	dc.b $00,$00
    SECTION section_6,code
    SECTION section_7,code
loc_7_00000000:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000112.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$001E(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_7_0000001C:
	move.l a6,-(a7)
	movea.l loc_2_00000112.l,a6
	move.l $0008(a7),d1
	jsr -$0024(a6)
	movea.l (a7)+,a6
	rts
loc_7_00000030:
	movem.l d2-d3/a6,-(a7)
	movea.l loc_2_00000112.l,a6
	movem.l $0010(a7),d1-d3
	jsr -$002A(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
loc_7_0000004C:
	movem.l d2-d3/a6,-(a7)
	movea.l loc_2_00000112.l,a6
	movem.l $0010(a7),d1-d3
	jsr -$0030(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
loc_7_00000068:
	movem.l d2-d3/a6,-(a7)
	movea.l loc_2_00000112.l,a6
	movem.l $0010(a7),d1-d3
	jsr -$0042(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
loc_7_00000084:
	move.l a6,-(a7)
	movea.l loc_2_00000112.l,a6
	move.l $0008(a7),d1
	jsr -$0048(a6)
	movea.l (a7)+,a6
	rts
loc_7_00000098:
	movem.l d2/a6,-(a7)
	movea.l loc_2_00000112.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$0054(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_7_000000B4:
	move.l a6,-(a7)
	movea.l loc_2_00000112.l,a6
	move.l $0008(a7),d1
	jsr -$005A(a6)
	movea.l (a7)+,a6
	rts
loc_7_000000C8:
	move.l a6,-(a7)
	movea.l loc_2_00000112.l,a6
	move.l $0008(a7),d1
	jsr -$0078(a6)
	movea.l (a7)+,a6
	rts
loc_7_000000DC:
	move.l a6,-(a7)
	movea.l loc_2_00000112.l,a6
	move.l $0008(a7),d1
	jsr -$00AE(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_8,code
loc_8_00000000:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000010:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000020:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movem.l $0008(a7),d0-d1
	jsr -$00C6(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_8_00000038:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	move.l $000C(a7),d0
	jsr -$00D2(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000050:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	move.l $0008(a7),d1
	jsr -$00D8(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000064:
	movem.l a2/a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movem.l $000C(a7),a0-a2
	jsr -$00EA(a6)
	movem.l (a7)+,a2/a6
	rts
	dc.b $00,$00
loc_8_00000080:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movem.l $0008(a7),a0-a1
	jsr -$00F6(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_8_00000098:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	jsr -$00FC(a6)
	movea.l (a7)+,a6
	rts
loc_8_000000AC:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movem.l $0008(a7),a0-a1
	jsr -$0114(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_8_000000C4:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	jsr -$0126(a6)
	movea.l (a7)+,a6
	rts
loc_8_000000D8:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	move.l $0008(a7),d0
	jsr -$013E(a6)
	movea.l (a7)+,a6
	rts
loc_8_000000EC:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	move.l $000C(a7),d0
	jsr -$0144(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000104:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	move.l $0008(a7),d0
	jsr -$014A(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000118:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	move.l $0008(a7),d0
	jsr -$0150(a6)
	movea.l (a7)+,a6
	rts
loc_8_0000012C:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movem.l $0008(a7),a0-a1
	jsr -$016E(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_8_00000144:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a0
	jsr -$0174(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000158:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	jsr -$017A(a6)
	movea.l (a7)+,a6
	rts
loc_8_0000016C:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	jsr -$019E(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000180:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	jsr -$01B0(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000194:
	move.l a6,-(a7)
	movea.l loc_2_0000010E.l,a6
	movea.l $0008(a7),a1
	move.l $000C(a7),d0
	jsr -$0228(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_9,data
