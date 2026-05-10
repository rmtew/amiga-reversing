    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/memory.i"


    SECTION section,code
loc_0_00000000:
	bra.w loc_0_00000020
	dc.b $00,$00,$AB,$CD
loc_0_00000008:
	dc.l $00000000,$00000000,$00000000,$00000000	; lookup_table
	dc.l $000002FC	; lookup_table
loc_0_0000001C:
	dc.b $00,$00,$2D,$38
loc_0_00000020:
	movem.l d0/a0,-(a7)
	movea.l $0004.w,a6
	moveq.l #0,d4
	lea.l loc_0_0000022E(pc),a1
	bsr.b loc_0_000000AA
	beq.w loc_0_00000216
	move.l d0,-(a7)
	move.l d0,d5
	lea.l loc_0_00000240(pc),a1
	bsr.b loc_0_000000AA
	bne.b loc_0_00000046
	moveq.l #2,d7
	bra.w loc_0_000000F2
loc_0_00000046:
	movea.l d0,a5
	move.l d0,-(a7)
	suba.l a1,a1
	move.w #_LVOFindTask,d6
	bsr.b loc_0_000000B0
	movea.l d0,a4
	move.l d0,-(a7)
	tst.l $00AC(a4)
	bne.b loc_0_00000060
	bsr.b loc_0_0000009A
	move.l d0,d4
loc_0_00000060:
	move.l d4,-(a7)
	lea.l loc_0_0000001C(pc),a1
	move.l (a1),d0
	move.l d0,-(a7)
	moveq.l #MEMF_ANY,d1
	move.w #_LVOAllocMem,d6
	bsr.b loc_0_000000B0
	beq.b loc_0_000000DE
	move.l d0,-(a7)
	move.l -(a1),d2
	move.l loc_0_00000008(pc),d1
	moveq.l #-1,d3
	move.w #$FFBE,d6
	bsr.b loc_0_000000B4
	bmi.b loc_0_000000C8
	movem.l (a7),d2-d3
	move.w #$FFD6,d6
	bsr.b loc_0_000000B4
	ble.b loc_0_000000CC
	movea.l (a7)+,a1
	pea.l loc_0_000000D2(pc)
	jmp (a1)
loc_0_0000009A:
	lea.l $005C(a4),a0
	move.w #_LVOWaitPort,d6
	bsr.b loc_0_000000B0
	move.w #_LVOGetMsg,d6
	bra.b loc_0_000000B0
loc_0_000000AA:
	moveq.l #0,d0
	move.w #_LVOOpenLibrary,d6
loc_0_000000B0:
	movea.l a6,a3
	bra.b loc_0_000000B6
loc_0_000000B4:
	movea.l a5,a3
loc_0_000000B6:
	movem.l d1/a0-a1/a4-a6,-(a7)
	movea.l a3,a6
	jsr $0(a6,d6.w)
	movem.l (a7)+,d1/a0-a1/a4-a6
	tst.l d0
	rts
loc_0_000000C8:
	moveq.l #1,d7
	bra.b loc_0_000000CE
loc_0_000000CC:
	moveq.l #2,d7
loc_0_000000CE:
	swap.w d7
	addq.w #1,d7
loc_0_000000D2:
	movea.l (a7)+,a1
	move.l (a7)+,d0
	move.w #_LVOFreeMem,d6
	bsr.b loc_0_000000B0
	bra.b loc_0_000000E4
loc_0_000000DE:
	moveq.l #1,d7
	swap.w d7
	addq.w #4,a7
loc_0_000000E4:
	lea.l $0018(a7),a7
	movea.l a5,a1
	movea.l $0004.w,a6
	jsr _LVOCloseLibrary(a6)
loc_0_000000F2:
	move.l d7,d6
	mulu.w #$18,d7
	lea.l loc_0_00000162(pc),a1
	adda.l d7,a1
	lea.l loc_0_000001E6(pc),a2
	move.l a1,(a2)
	clr.w d6
	swap.w d6
	beq.b loc_0_00000112
	addi.b #48,d6
	move.b d6,$0016(a1)
loc_0_00000112:
	lea.l loc_0_0000024C(pc),a1
	lea.l loc_0_000001FA(pc),a2
	move.l a1,(a2)
	lea.l loc_0_00000254(pc),a1
	lea.l loc_0_0000020E(pc),a2
	move.l a1,(a2)
	suba.l a0,a0
	lea.l loc_0_000001DA(pc),a1
	lea.l loc_0_00000202(pc),a2
	lea.l loc_0_000001EE(pc),a3
	moveq.l #104,d0
	moveq.l #104,d1
	move.l #$140,d2
	moveq.l #66,d3
	movea.l d5,a6
	jsr -$015C(a6)
	movea.l a6,a1
	movea.l $0004.w,a6
	jsr _LVOCloseLibrary(a6)
loc_0_00000150:
	tst.l d4
	beq.b loc_0_0000015E
	jsr _LVOForbid(a6)
	movea.l d4,a1
	jsr _LVOReplyMsg(a6)
loc_0_0000015E:
	moveq.l #100,d0
	rts
loc_0_00000162:
	dc.b "Insufficient memory -  ",$00	; string
	dc.b "i/o error occurred  -  ",$00	; string
	dc.b "Error opening Dos Lib  ",$00	; string
	dc.b "Unable to find bas.dl  ",$00	; string
	dc.b "Unable to find bas.rl  ",$00	; string
loc_0_000001DA:
	dc.b $00,$01,$01,$00,$00,$0A,$00,$0A,$00,$00,$00,$00
loc_0_000001E6:
	dcb.b $8,$00
loc_0_000001EE:
	dc.b $00,$01,$01,$00,$00,$06,$00,$03,$00,$00,$00,$00
loc_0_000001FA:
	dcb.b $8,$00
loc_0_00000202:
	dc.b $00,$01,$01,$00,$00,$06,$00,$03,$00,$00,$00,$00
loc_0_0000020E:
	dcb.b $8,$00
loc_0_00000216:
	move.l #$80038004,d7
	addq.w #8,a7
	bsr.b loc_0_00000224
	ori.b #1,d0
loc_0_00000224:
	movea.l (a7)+,a5
	jsr -$006C(a6)
	bra.w loc_0_00000150
loc_0_0000022E:
	dc.b "intuition.library",$00	; string
loc_0_00000240:
	dc.b "dos.library",$00	; string
loc_0_0000024C:
	dc.b "Cancel",$00	; string
	dc.b $00
loc_0_00000254:
	dc.b $4F,$6B,$00,$00,$4E,$71,$4E,$71,$00,$00,$00,$01
