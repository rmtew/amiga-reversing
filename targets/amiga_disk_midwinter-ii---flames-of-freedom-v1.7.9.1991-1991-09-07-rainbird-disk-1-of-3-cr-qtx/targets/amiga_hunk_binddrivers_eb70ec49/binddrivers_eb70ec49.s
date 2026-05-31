; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: 35 recovered call sites across 25 API groups
;          first observed: _LVOAllocMem x2, _LVOAlert x2, SysBase/_LVOOpenLibrary x3, _LVOFindTask
;          _LVOCloseLibrary x2, _LVOForbid, _LVOReplyMsg, _LVOFreeMem x2
;          remaining groups: 17; inspect JSON report

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
	link a6,#-260
	movem.l d2-d6/a2-a5,-(a7)
	movea.l #loc_3_00000044,a2
	movea.l #loc_3_0000003C,a4
	move.l #loc_3_00000040,d3
	lea.l -$0104(a6),a0
	move.l a0,$0004(a2)
	clr.l -(a7)
	pea.l loc_3_00000000.l	; KNOWN: arg +4 libName UBYTE * string_ptr amiga.library_name
	jsr loc_7_0000005C.l
	move.l d0,(a4)
	clr.l -(a7)
	pea.l loc_3_00000012.l	; KNOWN: arg +4 libName UBYTE * string_ptr amiga.library_name
	jsr loc_7_0000005C.l
	movea.l d3,a3
	move.l d0,(a3)
	tst.l (a4)
	lea.l $0010(a7),a7
	beq.w loc_2_000001BC
	movea.l d3,a0
	tst.l (a0)
	beq.w loc_2_000001BC
	move.l #$10000,-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	pea.l $0104.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_7_00000018.l
	movea.l d0,a3
	move.l a3,d2
	addq.l #8,a7
	beq.w loc_2_000001BC
	jsr loc_9_0000001C.l
	moveq.l #-2,d2
	move.l d2,-(a7)	; KNOWN: arg +8 structure structure
	pea.l loc_3_0000002E.l	; KNOWN: arg +4 vectors vectors
	jsr loc_6_00000000.l
	move.l d0,d6
	addq.l #8,a7
	beq.w loc_2_000001AE
	move.l d6,-(a7)
	jsr loc_6_00000068.l
	move.l d0,-$0004(a6)
	move.l a3,-(a7)	; KNOWN: arg +8 segList unsigned long
	move.l d6,-(a7)	; KNOWN: arg +4 resident RT
	jsr loc_6_00000030.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.w loc_2_0000019A
	tst.l $0004(a3)
	bgt.w loc_2_00000182
	bra.w loc_2_0000019A
loc_2_000000BA:
	pea.l loc_3_00000020.l
	pea.l $0008(a3)
	jsr loc_4_00000058.l
	move.l d0,d4
	addq.l #8,a7
	beq.w loc_2_00000182
	movea.l d4,a5
	move.b (a5),d2
	clr.b (a5)
	pea.l $0008(a3)
	move.l $0004(a2),-(a7)
	jsr loc_4_0000004C.l
	pea.l $0008(a3)
	jsr loc_8_00000000.l
	move.l d0,d5
	move.b d2,(a5)
	tst.l d5
	lea.l $000C(a7),a7
	beq.w loc_2_00000182
	pea.l loc_3_00000026.l
	movea.l d5,a5
	move.l $0036(a5),-(a7)
	jsr loc_8_00000028.l
	move.l d0,d0
	addq.l #8,a7
	beq.b loc_2_00000178
	move.l d0,$0008(a2)
	movea.l d5,a5
	move.l $0036(a5),$000C(a2)
	move.l d0,-(a7)
	jsr loc_2_0000021C.l
	move.l d0,d0
	addq.l #4,a7
	beq.b loc_2_00000178
	move.l d0,(a2)
	move.l $0004(a2),-(a7)
	jsr loc_6_0000007C.l
	move.l d0,d2
	addq.l #4,a7
	beq.b loc_2_00000178
	move.l d2,-(a7)
	jsr loc_2_000001E6.l
	move.l d0,d4
	addq.l #4,a7
	beq.b loc_2_0000016E
	pea.l $0010.w
	pea.l (a2)
	jsr loc_9_0000003C.l
	move.l d2,-(a7)	; KNOWN: arg +8 segList unsigned long
	move.l d4,-(a7)	; KNOWN: arg +4 resident RT
	jsr loc_7_00000000.l
	tst.l d0
	lea.l $0010(a7),a7
	bne.b loc_2_00000178
loc_2_0000016E:
	move.l d2,-(a7)	; KNOWN: arg +4 sysStack APTR
	jsr loc_6_00000090.l
	addq.l #4,a7
loc_2_00000178:
	move.l d5,-(a7)
	jsr loc_8_00000014.l
	addq.l #4,a7
loc_2_00000182:
	move.l a3,-(a7)
	move.l d6,-(a7)	; KNOWN: arg +4 alertNum unsigned long exec.alert.number
	jsr loc_6_0000004C.l
	tst.l d0
	addq.l #8,a7
	bne.w loc_2_000000BA
	jsr loc_9_0000002C.l
loc_2_0000019A:
	move.l -$0004(a6),-(a7)
	jsr loc_6_00000068.l
	move.l d6,-(a7)	; KNOWN: arg +4 target APTR
	jsr loc_6_0000001C.l
	addq.l #8,a7
loc_2_000001AE:
	pea.l $0104.w	; KNOWN: arg +8 byteSize unsigned long
	move.l a3,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_7_00000030.l
	addq.l #8,a7
loc_2_000001BC:
	tst.l (a4)
	beq.b loc_2_000001CA
	move.l (a4),-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_7_00000048.l
	addq.l #4,a7
loc_2_000001CA:
	movea.l d3,a0
	tst.l (a0)
	beq.b loc_2_000001DC
	movea.l d3,a2
	move.l (a2),-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_7_00000048.l
	addq.l #4,a7
loc_2_000001DC:
	movem.l -$0128(a6),d2-d6/a2-a5
	unlk a6
	rts
loc_2_000001E6:
	move.l $0004(a7),d0
	lsl.l #2,d0
	movea.l d0,a0
	move.l -$0004(a0),d1
	subq.l #8,d1
	lea.l $0004(a0),a0
	bra.b loc_2_00000212
loc_2_000001FA:
	cmpi.w #19196,(a0)
	bne.b loc_2_0000020A
	cmpa.l $0002(a0),a0
	bne.b loc_2_0000020A
	move.l a0,d0
	bra.b loc_2_0000021A
loc_2_0000020A:
	subq.l #2,d1
	move.l a0,d0
	addq.l #2,d0
	movea.l d0,a0
loc_2_00000212:
	moveq.l #26,d0
	cmp.l d1,d0
	blt.b loc_2_000001FA
	moveq.l #0,d0
loc_2_0000021A:
	rts
loc_2_0000021C:
	movem.l d2-d4,-(a7)
	move.l $0010(a7),d2
	moveq.l #0,d4
loc_2_00000226:
	pea.l $007C.w
	move.l d2,-(a7)
	jsr loc_4_00000030.l
	move.l d0,d3
	addq.l #8,a7
	beq.b loc_2_00000240
	move.l d3,d0
	addq.l #1,d3
	sub.l d2,d0
	bra.b loc_2_0000024A
loc_2_00000240:
	move.l d2,-(a7)
	jsr loc_4_00000020.l
	addq.l #4,a7
loc_2_0000024A:
	move.l d0,-(a7)
	move.l d2,-(a7)
	move.l d4,-(a7)
	jsr loc_2_00000268.l
	move.l d0,d4
	move.l d3,d2
	lea.l $000C(a7),a7
	bne.b loc_2_00000226
	move.l d4,d0
	movem.l (a7)+,d2-d4
	rts
loc_2_00000268:
	movem.l d2-d6,-(a7)
	move.l $0018(a7),d4
	move.l $001C(a7),d2
	move.l $0020(a7),d3
	move.l d3,-(a7)
	pea.l $002F.w
	move.l d2,-(a7)
	jsr loc_2_000003C6.l
	move.l d0,d6
	lea.l $000C(a7),a7
	beq.b loc_2_00000296
	move.l d6,d5
	addq.l #1,d6
	sub.l d2,d5
	bra.b loc_2_00000298
loc_2_00000296:
	move.l d3,d5
loc_2_00000298:
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr loc_2_00000368.l
	tst.l d0
	addq.l #8,a7
	beq.b loc_2_000002AC
loc_2_000002A8:
	moveq.l #0,d0
	bra.b loc_2_000002F2
loc_2_000002AC:
	move.l d2,-(a7)
	jsr loc_2_00000396.l
	move.l d0,d2
	tst.l d6
	addq.l #4,a7
	beq.b loc_2_000002E0
	move.l d3,d0
	sub.l d5,d0
	subq.l #1,d0
	move.l d0,-(a7)
	move.l d6,-(a7)
	jsr loc_2_00000368.l
	tst.l d0
	addq.l #8,a7
	beq.b loc_2_000002D4
	bra.b loc_2_000002A8
loc_2_000002D4:
	move.l d6,-(a7)
	jsr loc_2_00000396.l
	addq.l #4,a7
	bra.b loc_2_000002E2
loc_2_000002E0:
	moveq.l #-1,d0
loc_2_000002E2:
	move.l d0,-(a7)
	move.l d2,-(a7)
	move.l d4,-(a7)
	jsr loc_2_000002F8.l
	lea.l $000C(a7),a7
loc_2_000002F2:
	movem.l (a7)+,d2-d6
	rts
loc_2_000002F8:
	movem.l d2-d4/a2-a3,-(a7)
	movea.l $0018(a7),a2
	move.l $001C(a7),d2
	move.l $0020(a7),d3
	moveq.l #0,d0
	movea.l d0,a3
	bra.b loc_2_0000032C
loc_2_0000030E:
	btst.b #1,$000E(a3)
	beq.b loc_2_0000032C
	move.l a3,-(a7)
	move.l a2,-(a7)
	jsr loc_2_0000034A.l
	tst.l d0
	addq.l #8,a7
	bne.b loc_2_0000032C
	move.l a2,$0030(a3)
	movea.l a3,a2
loc_2_0000032C:
	move.l d3,-(a7)
	move.l d2,-(a7)
	move.l a3,-(a7)
	jsr loc_9_00000000.l
	movea.l d0,a3
	move.l a3,d4
	lea.l $000C(a7),a7
	bne.b loc_2_0000030E
	move.l a2,d0
	movem.l (a7)+,d2-d4/a2-a3
	rts
loc_2_0000034A:
	movea.l $0004(a7),a0
	move.l $0008(a7),d0
	bra.b loc_2_00000360
loc_2_00000354:
	cmpa.l d0,a0
	bne.b loc_2_0000035C
	moveq.l #1,d0
	bra.b loc_2_00000366
loc_2_0000035C:
	movea.l $0030(a0),a0
loc_2_00000360:
	move.l a0,d1
	bne.b loc_2_00000354
	moveq.l #0,d0
loc_2_00000366:
	rts
loc_2_00000368:
	movea.l $0004(a7),a0
	move.l $0008(a7),d1
	tst.l d1
	bne.b loc_2_00000378
loc_2_00000374:
	moveq.l #1,d0
loc_2_00000376:
	bra.b loc_2_00000394
loc_2_00000378:
	bra.b loc_2_0000038A
loc_2_0000037A:
	move.b (a0)+,d0
	cmpi.b #48,d0
	blt.b loc_2_00000388
	cmpi.b #57,d0
	ble.b loc_2_0000038A
loc_2_00000388:
	bra.b loc_2_00000374
loc_2_0000038A:
	move.l d1,d0
	subq.l #1,d1
	tst.l d0
	bgt.b loc_2_0000037A
	moveq.l #0,d0
loc_2_00000394:
	rts
loc_2_00000396:
	move.l d2,-(a7)
	movea.l $0008(a7),a0
	moveq.l #0,d0
	bra.b loc_2_000003BE
loc_2_000003A0:
	cmpi.b #48,d1
	blt.b loc_2_000003C2
	cmpi.b #57,d1
	bgt.b loc_2_000003C2
	add.l d0,d0
	move.l d0,d2
	asl.l #2,d0
	add.l d2,d0
	ext.w d1
	ext.l d1
	add.l d1,d0
	moveq.l #48,d1
	sub.l d1,d0
loc_2_000003BE:
	move.b (a0)+,d1
	bne.b loc_2_000003A0
loc_2_000003C2:
	move.l (a7)+,d2
	rts
loc_2_000003C6:
	movem.l d2-d3,-(a7)
	move.l $000C(a7),d2
	move.b $0013(a7),d0
	move.l $0014(a7),d3
	ext.w d0
	ext.l d0
	move.l d0,-(a7)
	move.l d2,-(a7)
	jsr loc_4_00000030.l
	move.l d0,d1
	move.l d3,d0
	add.l d2,d0
	cmp.l d0,d1
	addq.l #8,a7
	ble.b loc_2_000003F2
	moveq.l #0,d1
loc_2_000003F2:
	move.l d1,d0
	movem.l (a7)+,d2-d3
	rts
	dc.w $0000
    SECTION section_3,data
loc_3_00000000:
	dc.b "expansion.library",$00
loc_3_00000012:
	dc.b "icon.library",$00
	dc.b $00
loc_3_00000020:
	dc.b ".info",$00
loc_3_00000026:
	dc.b "PRODUCT",$00
loc_3_0000002E:
	dc.b "SYS:Expansion",$00
loc_3_0000003C:
	dc.b $00,$00,$00,$00
loc_3_00000040:
	dc.b $00,$00,$00,$00
loc_3_00000044:
	dcb.b $10,$00
    SECTION section_4,code
	dc.b $4C,$EF,$03,$00,$00,$04
loc_4_00000006:
	moveq.l #0,d0
loc_4_00000008:
	move.b (a0)+,d1
	cmp.b (a1)+,d1
	bne.b loc_4_00000014
	tst.b d1
	bne.b loc_4_00000008
	bra.b loc_4_0000001C
loc_4_00000014:
	bhi.b loc_4_0000001A
	moveq.l #-1,d0
	bra.b loc_4_0000001C
loc_4_0000001A:
	moveq.l #1,d0
loc_4_0000001C:
	rts
	dc.w $0000
loc_4_00000020:
	movea.l $0004(a7),a0
loc_4_00000024:
	moveq.l #-1,d0
loc_4_00000026:
	tst.b (a0)+
	dbeq.w d0,loc_4_00000026
	not.l d0
	rts
loc_4_00000030:
	movea.l $0004(a7),a0
	move.l $0008(a7),d0
loc_4_00000038:
	move.b (a0)+,d1
	beq.b loc_4_00000046
	cmp.b d0,d1
	bne.b loc_4_00000038
	subq.l #1,a0
	move.l a0,d0
loc_4_00000044:
	rts
loc_4_00000046:
	moveq.l #0,d0
	bra.b loc_4_00000044
	dc.w $0000
loc_4_0000004C:
	movem.l $0004(a7),a0-a1
loc_4_00000052:
	move.b (a1)+,(a0)+
	bne.b loc_4_00000052
	rts
loc_4_00000058:
	movem.l $0004(a7),a0-a1
	move.l a2,-(a7)
	movea.l a0,a2
	bsr.w loc_4_00000024
	adda.l d0,a2
	move.l d0,d1
	movea.l a1,a0
	bsr.w loc_4_00000024
	cmp.l d0,d1
	bcs.b loc_4_00000086
	suba.l d0,a2
	movea.l a2,a0
	bsr.w loc_4_00000006
	tst.l d0
	bne.b loc_4_00000086
	move.l a2,d0
loc_4_00000082:
	movea.l (a7)+,a2
	rts
loc_4_00000086:
	moveq.l #0,d0
	bra.b loc_4_00000082
	dc.w $0000
    SECTION section_5,code
    SECTION section_6,code
loc_6_00000000:
	movem.l d2/a6,-(a7)
	movea.l loc_1_00000004.l,a6
	movem.l $000C(a7),d1-d2	; KNOWN: arg +4 segList unsigned long
	jsr _LVOMakeLibrary(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.w $0000
loc_6_0000001C:
	move.l a6,-(a7)
	movea.l loc_1_00000004.l,a6
	move.l $0008(a7),d1
	jsr _LVOMakeFunctions(a6)
	movea.l (a7)+,a6
	rts
loc_6_00000030:
	movem.l d2/a6,-(a7)
	movea.l loc_1_00000004.l,a6
	movem.l $000C(a7),d1-d2	; KNOWN: arg +4 segList unsigned long
	jsr _LVOInitResident(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.w $0000
loc_6_0000004C:
	movem.l d2/a6,-(a7)
	movea.l loc_1_00000004.l,a6
	movem.l $000C(a7),d1-d2
	jsr _LVOAlert(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.w $0000
loc_6_00000068:
	move.l a6,-(a7)
	movea.l loc_1_00000004.l,a6
	move.l $0008(a7),d1
	jsr _LVOEnable(a6)
	movea.l (a7)+,a6
	rts
loc_6_0000007C:
	move.l a6,-(a7)
	movea.l loc_1_00000004.l,a6
	move.l $0008(a7),d1
	jsr _LVOSuperState(a6)
	movea.l (a7)+,a6
	rts
loc_6_00000090:
	move.l a6,-(a7)
	movea.l loc_1_00000004.l,a6
	move.l $0008(a7),d1
	jsr _LVOUserState(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_7,code
loc_7_00000000:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 resident RT
	move.l $000C(a7),d1	; KNOWN: arg +8 segList unsigned long
	jsr _LVOInitResident(a6)
	movea.l (a7)+,a6
	rts
loc_7_00000018:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movem.l $0008(a7),d0-d1	; KNOWN: arg +4 byteSize unsigned long | KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	rts
	dc.w $0000
loc_7_00000030:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 memoryBlock APTR
	move.l $000C(a7),d0	; KNOWN: arg +8 byteSize unsigned long
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	rts
loc_7_00000048:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 library LIB
	jsr _LVOCloseLibrary(a6)
	movea.l (a7)+,a6
	rts
loc_7_0000005C:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 libName UBYTE * string_ptr amiga.library_name
	move.l $000C(a7),d0	; KNOWN: arg +8 version unsigned long
	jsr _LVOOpenLibrary(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_8,code
loc_8_00000000:
	move.l a6,-(a7)
	movea.l loc_3_00000040.l,a6
	movea.l $0008(a7),a0
	jsr -$004E(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000014:
	move.l a6,-(a7)
	movea.l loc_3_00000040.l,a6
	movea.l $0008(a7),a0
	jsr -$005A(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000028:
	move.l a6,-(a7)
	movea.l loc_3_00000040.l,a6
	movem.l $0008(a7),a0-a1
	jsr -$0060(a6)
	movea.l (a7)+,a6
	rts
	dc.w $0000
    SECTION section_9,code
loc_9_00000000:
	move.l a6,-(a7)
	movea.l loc_3_0000003C.l,a6
	movea.l $0008(a7),a0
	movem.l $000C(a7),d0-d1
	jsr -$0048(a6)
	movea.l (a7)+,a6
	rts
	dc.w $0000
loc_9_0000001C:
	move.l a6,-(a7)
	movea.l loc_3_0000003C.l,a6
	jsr -$0078(a6)
	movea.l (a7)+,a6
	rts
loc_9_0000002C:
	move.l a6,-(a7)
	movea.l loc_3_0000003C.l,a6
	jsr -$007E(a6)
	movea.l (a7)+,a6
	rts
loc_9_0000003C:
	move.l a6,-(a7)
	movea.l loc_3_0000003C.l,a6
	movea.l $0008(a7),a0
	move.l $000C(a7),d0
	jsr -$0084(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_10,data
