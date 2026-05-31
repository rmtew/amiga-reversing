; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: 16 recovered call sites across 14 API groups
;          first observed: _LVOAllocMem, _LVOAlert, SysBase/_LVOForbid x2, _LVOFindTask, _LVOCloseLibrary
;          _LVOForbid x2, _LVOReplyMsg, _LVOFreeMem
;          remaining groups: 6; inspect JSON report

    INCLUDE "dos/dosextens.i"
    INCLUDE "exec/alerts.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/memory.i"


    SECTION section_0,code
loc_0_00000000:
	movem.l d0/a0,-(a7)
	movea.l $00000004.l,a6
	move.l a6,h1dl_ExecBase.l
	move.l #$19C,d0
	move.l #MEMF_CLEAR|MEMF_PUBLIC,d1
	jsr _LVOAllocMem(a6)
	movea.l d0,a1
	movem.l (a7)+,d0/a0
	cmpa.l #$0,a1
	bne.b loc_0_00000032
	moveq.l #20,d0
	rts
loc_0_00000032:
	movea.l a1,a5
	move.l a5,-(a7)
	move.l d0,$0004(a5)
	move.l a0,$0008(a5)
	suba.l a1,a1
	jsr -$0126(a6)
	movea.l d0,a4
	lea.l loc_0_000001C4(pc),a1
	moveq.l #0,d0
	jsr -$0228(a6)
	move.l d0,$0000(a5)
	bne.b loc_0_00000072
	movem.l d7/a5-a6,-(a7)
	move.l #AG_OpenLib|AO_DOSLib,d7
	movea.l $0004.w,a6
	jsr _LVOAlert(a6)
	movem.l (a7)+,d7/a5-a6
	moveq.l #100,d0
	bra.w loc_0_00000176
loc_0_00000072:
	move.l d0,loc_1_00000004.l
	tst.l pr_CLI(a4)
	beq.w loc_0_0000013A
	suba.l a0,a0
	move.l pr_CLI(a4),d0
	lsl.l #2,d0
	move.l $10(a0,d0.l),d0
	lsl.l #2,d0
	movem.l a2-a3,-(a7)
	lea.l $009C(a5),a2
	lea.l $001C(a5),a3
	movea.l d0,a0
	moveq.l #0,d0
	move.b (a0)+,d0
	clr.b $0(a0,d0.l)
	move.l a0,(a3)+
	move.l $0004(a5),d0
	movea.l $0008(a5),a0
	lea.l $0(a0,d0.l),a1
loc_0_000000B2:
	cmpi.b #32,-(a1)
	dbhi.w d0,loc_0_000000B2
	clr.b $0001(a1)
loc_0_000000BE:
	move.b (a0)+,d1
	beq.b loc_0_0000011E
	cmpi.b #32,d1
	beq.b loc_0_000000BE
	cmpi.b #9,d1
	beq.b loc_0_000000BE
	move.l a2,(a3)+
	cmpi.b #34,d1
	beq.b loc_0_000000EA
	move.b d1,(a2)+
loc_0_000000D8:
	move.b (a0)+,d1
	beq.b loc_0_0000011E
	cmpi.b #32,d1
	beq.b loc_0_000000E6
	move.b d1,(a2)+
	bra.b loc_0_000000D8
loc_0_000000E6:
	clr.b (a2)+
	bra.b loc_0_000000BE
loc_0_000000EA:
	move.b (a0)+,d1
	beq.b loc_0_0000011E
	cmpi.b #34,d1
	beq.b loc_0_000000E6
	cmpi.b #42,d1
	bne.b loc_0_0000011A
	move.b (a0)+,d1
	cmpi.b #78,d1
	beq.b loc_0_00000108
	cmpi.b #110,d1
	bne.b loc_0_0000010C
loc_0_00000108:
	moveq.l #10,d1
	bra.b loc_0_0000011A
loc_0_0000010C:
	cmpi.b #69,d1
	beq.b loc_0_00000118
	cmpi.b #101,d1
	bne.b loc_0_0000011A
loc_0_00000118:
	moveq.l #27,d1
loc_0_0000011A:
	move.b d1,(a2)+
	bra.b loc_0_000000EA
loc_0_0000011E:
	clr.b (a2)
	clr.l (a3)
	move.l a3,d0
	lea.l $001C(a5),a3
	sub.l a3,d0
	lsr.l #2,d0
	movem.l (a7)+,a2-a3
	pea.l $001C(a5)
	move.l d0,-(a7)
	bra.w loc_0_00000168
loc_0_0000013A:
	lea.l pr_MsgPort(a4),a0
	jsr -$0180(a6)
	lea.l pr_MsgPort(a4),a0
	jsr -$0174(a6)
	move.l d0,$000C(a5)
	move.l d0,-(a7)
	clr.l -(a7)
	movea.l $0000(a5),a6
	movea.l d0,a2
	move.l $0024(a2),d0
	beq.b loc_0_00000168
	movea.l d0,a0
	move.l $0000(a0),d1
	jsr -$007E(a6)
loc_0_00000168:
	jsr loc_2_00000000.l
	moveq.l #0,d0
	bra.b loc_0_00000176
	dc.b $20,$2F,$00,$04
loc_0_00000176:
	move.l d0,d2
	movea.l $00000004.l,a6
	suba.l a1,a1
	jsr _LVOFindTask(a6)
	movea.l d0,a4
	movea.l pr_ReturnAddr(a4),a5
	suba.l #$8,a5
	movea.l a5,a7
	movea.l (a7)+,a5
	move.l d2,-(a7)
	move.l $0000(a5),d0
	beq.b loc_0_000001A2
	movea.l d0,a1
	jsr _LVOCloseLibrary(a6)
loc_0_000001A2:
	tst.l $000C(a5)
	beq.b loc_0_000001B4
	jsr _LVOForbid(a6)
	movea.l $000C(a5),a1
	jsr _LVOReplyMsg(a6)
loc_0_000001B4:
	movea.l a5,a1
	move.l #$19C,d0
	jsr _LVOFreeMem(a6)
	move.l (a7)+,d0
	rts
loc_0_000001C4:
	dc.b "dos.library",$00
	dc.b $4E,$49,$4C,$3A,$00,$00,$00,$00
    SECTION section_1,data
h1dl_ExecBase:
	dc.b $00,$00,$00,$00
loc_1_00000004:
	dc.b $00,$00,$00,$00,$00,$22,$00,$08,$52,$58,$00,$00
    SECTION section_2,code
loc_2_00000000:
	movem.l d2-d3/a2,-(a7)
	moveq.l #0,d3
	moveq.l #0,d2
	movea.l h1dl_ExecBase.l,a2
	jsr loc_5_00000000.l
	movea.l $0142(a2),a0
	bra.b loc_2_00000058
loc_2_0000001A:
	tst.l d2
	bne.b loc_2_0000003C
	move.l a0,d0
	cmpi.l #12582912,d0
	bcs.b loc_2_0000003C
	move.l a0,d0
	cmpi.l #13631488,d0
	bcc.b loc_2_0000003C
	cmpi.w #5,$000E(a0)
	bne.b loc_2_0000003C
	move.l a0,d2
loc_2_0000003C:
	tst.l d3
	bne.b loc_2_00000056
	cmpi.w #3,$000E(a0)
	bne.b loc_2_00000056
	move.l a0,d0
	cmpi.l #2097152,d0
	bcc.b loc_2_00000056
	move.l $0004(a0),d3
loc_2_00000056:
	movea.l (a0),a0
loc_2_00000058:
	tst.l (a0)
	bne.b loc_2_0000001A
	tst.l d2
	beq.b loc_2_0000007E
	cmp.l d2,d3
	beq.b loc_2_0000007E
	move.l d2,-(a7)	; KNOWN: arg +4 node LN
	jsr loc_5_0000003C.l
	move.l d3,-(a7)	; KNOWN: arg +12 pred LN
	move.l d2,-(a7)	; KNOWN: arg +8 node LN
	pea.l $0142(a2)	; KNOWN: arg +4 list LH
	jsr loc_5_00000010.l
	lea.l $0010(a7),a7
loc_2_0000007E:
	jsr loc_5_0000002C.l
	movem.l (a7)+,d2-d3/a2
	rts
	dc.w $0000
    SECTION section_3,data
    SECTION section_4,code
    SECTION section_5,code
loc_5_00000000:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	jsr _LVOForbid(a6)
	movea.l (a7)+,a6
	rts
loc_5_00000010:
	movem.l a2/a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movem.l $000C(a7),a0-a2	; KNOWN: arg +4 list LH | KNOWN: arg +8 node LN | KNOWN: arg +12 pred LN
	jsr _LVOInsert(a6)
	movem.l (a7)+,a2/a6
	rts
	dc.w $0000
loc_5_0000002C:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	rts
loc_5_0000003C:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 node LN
	jsr _LVORemove(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_6,data
