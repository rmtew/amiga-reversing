    INCLUDE "exec/devices.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/intbits.i"

    RSSET LIB_SIZE
app_0022 RS.W 1
    RS.B 4
app_0028 RS.L 1
app_002C RS.L 1
app_0030 RS.L 1
    RS.B 134
app_00BA RS.L 1
    RS.B 104
app_0126 RS.B 1
    RS.B 27
app_0142 RS.L 1
    RS.B 220
app_0222 RS.L 1
app_0226 RS.L 1
app_022A RS.L 1
app_SIZEOF EQU __RS

amiga_loadseg_segment_link	EQU	-4
_custom	EQU	$DFF000

    SECTION section_0,code
	dc.b $70,$FF,$4E,$75
resident:	; STRUCT RT
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l resident_init	; APTR RT_ENDSKIP
	dc.b RTF_COLDSTART	; UBYTE RT_FLAGS = RTF_COLDSTART
	dc.b $01	; UBYTE RT_VERSION
	dc.b NT_DEVICE	; UBYTE RT_TYPE = NT_DEVICE
	dc.b $14	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
	dcb.b $A,$00
	dc.l resident_name
	dc.b $00,$01
	dc.l $FFFFFFFC	; facts_v2 HUNK_RELOC32 numeric: source hunk 0 offset $0000002E, target hunk 0, loader result base(hunk 0)-$00000004; negative addend points before target hunk; left numeric
	dc.b $00,$00,$02,$70
	dc.l resident
	dc.b $00,$00,$00,$00,$4E,$F9
	dc.l loc_0_00000718
	rts
	dc.b $00,$00,$00,$00
	jmp loc_0_000005F0.l
	dc.b $4E,$75,$00,$00,$00,$00,$70,$00,$4E,$75,$00,$00,$70,$00,$4E,$75
	dc.b $00,$00,$4E,$F9
	dc.l loc_0_000005E8
	dcb.b $8,$00
	dc.b $03,$00
	dc.l resident_name
	dc.b $06,$00,$00,$2A,$00,$22,$00,$01,$00,$00
	dc.l resident_idstring
	dc.b $00,$00,$00,$00,$00,$01,$00,$00
loc_0_0000008C:
	dc.b $00,$00,$00,$00
loc_0_00000090:
	dc.b $00,$00,$00,$00
loc_0_00000094:
	dc.l $00000000	; lookup_table
loc_0_00000098:
	dc.b $00,$00,$00,$00,$10
	dcb.b $B,$00
	dc.l loc_0_000000AC
loc_0_000000AC:
	dc.b $10,$00,$00,$00,$00,$00,$01,$AA,$00,$96
	dcb.b $C,$00
	dc.b $10,$00
	dc.l loc_0_0000008C
	dc.b $00,$00,$00,$00,$00,$00
	dc.l loc_0_00000122	; pointer_table
	dc.l resident_name
	dcb.b $8,$00
loc_0_000000DE:
	dc.b $00,$00,$00,$0C,$00,$00,$00,$80,$00,$00,$00,$00,$00,$00
loc_0_000000EC:
	dc.w $0000,$0000,$0001,$0000	; lookup_table
loc_0_000000F4:
	dc.w $0000	; lookup_table
loc_0_000000F6:
	dc.l $00000000,$00000000,$00000000	; lookup_table
loc_0_00000102:
	dc.l $00000000	; lookup_table
loc_0_00000106:
	dc.l $00000000,$00000005,$00000000,$00000000	; lookup_table
	dc.l $00000000,$00000000,$444F5300	; lookup_table
loc_0_00000122:
	dcb.b $20,$00
resident_name:
	dc.b "ramdrive.device",$00
resident_idstring:
	dc.b "Commodore-Amiga Ram Drive 1.0 (6 Apr 88)",$0D,$0A,$00
loc_0_0000017D:
	dc.b "dos.library",$00
	dc.b $65,$78,$70,$61,$6E,$73,$69,$6F,$6E,$2E,$6C,$69,$62,$72,$61,$72
	dc.b $79,$00,$00,$48,$E7,$20,$22,$2C,$78,$00,$04,$22,$7A,$FE,$E6,$20
	dc.b $3C,$00,$00,$01,$D8,$4E,$AE,$FF,$34,$4A,$80,$67,$00,$00,$8A,$22
	dc.b $7A,$FE,$D6,$20,$3A,$FE,$D6,$4E,$AE,$FF,$34,$4A,$80,$67,$00,$00
	dc.b $7E,$43,$FA,$FE,$9C,$4E,$AE,$FE,$50,$08,$3A,$00,$01,$FF,$07,$66
	dc.b $66,$74,$00,$41,$FA,$FF,$00,$0C,$90,$00,$00,$00,$0F,$6D,$16,$24
	dc.b $28,$00,$3C,$0C,$82,$FF,$FF,$FF,$80,$6D,$4C,$0C,$82,$00,$00,$00
	dc.b $7F,$6F,$02,$74,$7F,$43,$FA,$FF,$89,$70,$22,$4E,$AE,$FD,$D8,$4A
	dc.b $80,$67,$34,$2C,$40,$41,$FA,$FE,$BE,$4E,$AE,$FF,$70,$41,$EE,$00
	dc.b $4A,$48,$E7,$00,$82,$2C,$78,$00,$04,$43,$FA,$FE,$A6,$22,$80,$67
	dc.b $0E,$20,$57,$43,$FA,$FE,$8C,$13,$42,$00,$09,$4E,$AE,$FE,$F2,$4C
	dc.b $DF,$03,$00,$4E,$AE,$FE,$62,$4C,$DF,$44,$04,$4E,$75,$22,$7A,$FE
	dc.b $44,$20,$3C,$00,$00,$01,$D8,$4E,$AE,$FF,$2E,$60,$EA,$43,$FA,$FF
	dc.b $25,$4E,$AE,$FF,$A0,$4A,$80,$67,$08,$20,$40,$20,$68,$00,$16,$4E
	dc.b $90,$4E,$75
resident_init:
	movem.l d2-d3/a2-a6,-(a7)
	movea.l $0004.w,a6
	lea.l loc_0_0000017D(pc),a1
	moveq.l #33,d0
	jsr _LVOOpenLibrary(a6)
	lea.l loc_0_00000570(pc),a0
	move.l d0,(a0)
	beq.w loc_0_0000052C
	movea.l d0,a1
	movea.l LIB_SIZE(a1),a2
	jsr _LVOCloseLibrary(a6)
	movea.l $0018(a2),a0
	adda.l a0,a0
	adda.l a0,a0
	move.l $0004(a0),d0
loc_0_0000029E:
	beq.w loc_0_0000052C
	lsl.l #2,d0
	movea.l d0,a2
	tst.l $0004(a2)
	bne.b loc_0_000002D6
	move.l $001C(a2),d0
	beq.b loc_0_000002D6
	lsl.l #2,d0
	movea.l d0,a3
	move.l $0004(a3),d0
	lsl.l #2,d0
	movea.l d0,a0
	lea.l resident_name(pc),a1
	clr.w d0
	move.b (a0)+,d0
	beq.b loc_0_000002D6
	subq.w #1,d0
loc_0_000002CA:
	cmpm.b (a0)+,(a1)+
	dbne.w d0,loc_0_000002CA
	bne.b loc_0_000002D6
	tst.b (a1)
	beq.b loc_0_000002DA
loc_0_000002D6:
	move.l (a2),d0
	bra.b loc_0_0000029E
loc_0_000002DA:
	move.l $0028(a2),d0
	lsl.l #2,d0
	movea.l d0,a0
	lea.l loc_0_00000122(pc),a1
	moveq.l #0,d0
	move.b (a0)+,d0
	subq.w #1,d0
loc_0_000002EC:
	move.b (a0)+,(a1)+
	dbf.w d0,loc_0_000002EC
	lea.l loc_0_000000DE(pc),a1
	move.l $0000(a3),-$0008(a1)
	move.l $000C(a3),-$0004(a1)
	move.l $0008(a3),d0
	lsl.l #2,d0
	movea.l d0,a0
	move.l (a0)+,d0
	move.w d0,d1
	cmpi.l #16,d0
	ble.b loc_0_0000031E
	moveq.l #16,d0
	move.w d0,d1
	bra.b loc_0_0000031E
loc_0_0000031C:
	move.l (a0)+,d0
loc_0_0000031E:
	move.l d0,(a1)+
	dbf.w d1,loc_0_0000031C
	move.l loc_0_00000106(pc),d0
	sub.l loc_0_00000102(pc),d0
	addq.w #1,d0
	mulu.w loc_0_000000EC(pc),d0
	mulu.w loc_0_000000F4(pc),d0
	beq.w loc_0_0000052C
	move.l d0,d2
	subq.l #1,d2
	add.l loc_0_000000F6(pc),d2
	lsr.l #1,d2
	lea.l loc_0_00000568(pc),a0
	move.l d2,(a0)
	mulu.w #$200,d0
	addq.l #8,d0
	lea.l loc_0_00000094(pc),a0
	move.l d0,(a0)
	moveq.l #0,d1
	bsr.w loc_0_0000057A
	lea.l loc_0_00000090(pc),a0
	move.l d0,(a0)
	beq.w loc_0_0000052C
	addq.l #8,d0
	lea.l loc_0_00000098(pc),a0
	move.l d0,(a0)
	movea.l d0,a3
	move.l #$270,d0
	moveq.l #2,d1
	bsr.w loc_0_0000057A
	tst.l d0
	beq.w loc_0_00000540
	movea.l d0,a4
	move.l #$1D8,d0
	moveq.l #0,d1
	bsr.w loc_0_0000057A
	lea.l loc_0_0000008C(pc),a0
	move.l d0,(a0)
	beq.w loc_0_00000534
	movea.l d0,a5
	lea.l loc_0_000005E0(pc),a0
	movea.l a5,a1
	move.w #$75,d0
loc_0_000003A6:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_0_000003A6
	lea.l resident(pc),a0
	lea.l $0008(a4),a1
	move.w #$99,d0
loc_0_000003B8:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_0_000003B8
	move.l a4,d1
	lea.l amiga_loadseg_segment_link(pc),a0
	sub.l a0,d1
	lea.l loc_0_0000054C(pc),a0
loc_0_000003CA:
	move.w (a0)+,d0
	bmi.b loc_0_000003D4
	add.l d1,$0(a4,d0.w)
	bra.b loc_0_000003CA
loc_0_000003D4:
	lea.l $0138(a5),a0
	move.l a0,$0044(a4)
	lea.l $0010(a5),a0
	move.l a0,$0050(a4)
	lea.l $0008(a5),a0
	move.l a0,$0068(a4)
	lea.l $01A0(a4),a0
	move.l a0,$001E(a4)
	move.w #INTF_INTEN,_custom+intena.l
	addq.b #1,app_0126(a6)
	lea.l $0022(a4),a0
	move.l app_0222(a6),(a0)
	move.l a0,app_0222(a6)
	lea.l $003A(a4),a0
	move.l app_0226(a6),$0004(a0)
	beq.b loc_0_0000041E
	bset.b #7,$0004(a0)
loc_0_0000041E:
	move.l a0,app_0226(a6)
	jsr _LVOSumKickData(a6)
	move.l d0,app_022A(a6)
	subq.b #1,app_0126(a6)
	bge.b loc_0_00000438
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_00000438:
	lea.l $006C(a4),a1
	jsr _LVOAddDevice(a6)
	move.l $0122(a4),d1
	bne.b loc_0_0000044C
	move.l #$444F5300,d1
loc_0_0000044C:
	movea.l a3,a1
	moveq.l #127,d0
loc_0_00000450:
	move.l d1,(a1)+
	addq.l #1,d1
	dbf.w d0,loc_0_00000450
	move.l loc_0_00000568(pc),d0
	mulu.w #$200,d0
	lea.l $0(a3,d0.l),a2
	movea.l a2,a1
	moveq.l #127,d0
	moveq.l #0,d1
loc_0_0000046A:
	move.l d1,(a1)+
	dbf.w d0,loc_0_0000046A
	move.l #$2,(a2)
	move.l #$1,$01FC(a2)
	move.l #$48,$000C(a2)
	movea.l loc_0_00000570(pc),a6
	lea.l $01E4(a2),a0
	move.l a0,d1
	jsr -$00C0(a6)
	lea.l $01A4(a2),a0
	move.l a0,d1
	jsr -$00C0(a6)
	lea.l loc_0_00000574(pc),a0
	lea.l $01B0(a2),a1
	moveq.l #0,d0
	move.b (a0),d0
loc_0_000004AA:
	move.b (a0)+,(a1)+
	dbf.w d0,loc_0_000004AA
	move.l loc_0_00000094(pc),d0
	cmpi.l #2080776,d0
	bgt.b loc_0_0000051A
	move.l loc_0_00000568(pc),d0
	addq.l #1,d0
	move.l d0,$013C(a2)
	moveq.l #-1,d0
	move.l d0,$0138(a2)
	lea.l $0204(a2),a1
	movea.l a1,a0
	moveq.l #-1,d0
	moveq.l #126,d1
loc_0_000004D6:
	move.l d0,(a0)+
	dbf.w d1,loc_0_000004D6
	move.l loc_0_00000568(pc),d1
	sub.l loc_0_000000F6(pc),d1
	move.l d1,d2
	move.l d1,d3
	andi.w #31,d1
	bclr d1,d0
	lsr.l #5,d2
	lsl.l #2,d2
	and.l d0,$0(a1,d2.l)
	not.l d0
	addi.l #127,d0
	addq.l #1,d3
	move.l d3,d2
	andi.w #31,d3
	moveq.l #-1,d1
	bclr d3,d1
	lsr.l #5,d2
	lsl.l #2,d2
	and.l d1,$0(a1,d2.l)
	not.l d1
	add.l d1,d0
	move.l d0,$0200(a2)
loc_0_0000051A:
	movea.l a2,a0
	moveq.l #127,d0
	moveq.l #0,d1
loc_0_00000520:
	add.l (a0)+,d1
	dbf.w d0,loc_0_00000520
	neg.l d1
	move.l d1,$0014(a2)
loc_0_0000052C:
	moveq.l #0,d0
	movem.l (a7)+,d2-d3/a2-a6
	rts
loc_0_00000534:
	movea.l a4,a1
	move.l #$270,d0
	jsr -$00D2(a6)
loc_0_00000540:
	movea.l a3,a1
	move.l loc_0_00000094(pc),d0
	jsr -$00D2(a6)
	bra.b loc_0_0000052C
loc_0_0000054C:
	dc.b $00,$0A,$00,$0E,$00,$16,$00,$1A,$00,$2C,$00,$32,$00,$3A,$00,$76
	dc.b $00,$84,$00,$AC,$00,$C8,$00,$D2,$00,$D6,$FF,$FF
loc_0_00000568:
	dc.l $00000000,$00000000	; lookup_table
loc_0_00000570:
	dc.l $00000000	; lookup_table
loc_0_00000574:
	dc.b $05,$52,$41,$4D,$42,$30
loc_0_0000057A:
	movem.l d2-d3/a2-a3,-(a7)
	move.w #INTF_INTEN,_custom+intena.l
	addq.b #1,app_0126(a6)
	movea.l app_0142(a6),a0
	moveq.l #0,d3
loc_0_00000590:
	movea.l a0,a1
	move.l (a1),d2
	beq.b loc_0_000005E2
	movea.l d2,a0
	move.w d1,d2
	and.w $000E(a1),d2
	cmp.w d1,d2
	bne.b loc_0_00000590
	movea.l $0010(a1),a2
loc_0_000005A6:
	cmp.l $0004(a2),d0
	bhi.b loc_0_000005B2
	movea.l a2,a3
	move.l $0004(a2),d3
loc_0_000005B2:
	move.l $0000(a2),d2
	beq.b loc_0_000005BC
	movea.l d2,a2
	bra.b loc_0_000005A6
loc_0_000005BC:
	tst.l d3
	beq.b loc_0_00000590
	sub.l d0,d3
	andi.w #65528,d3
	adda.l d3,a3
	movea.l a3,a1
	jsr -$00CC(a6)
loc_0_000005CE:
	subq.b #1,app_0126(a6)
	bge.b loc_0_000005DC
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_000005DC:
	movem.l (a7)+,d2-d3/a2-a3
loc_0_000005E0:
	rts
loc_0_000005E2:
	moveq.l #0,d0
	bra.b loc_0_000005CE
	dc.b $00,$00
loc_0_000005E8:
	move.l d1,$0018(a1)
	moveq.l #0,d0
	rts
loc_0_000005F0:
	movem.l a2/a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOForbid(a6)
	move.w $001C(a1),d0
	cmpi.w #16,d0
	blt.b loc_0_00000608
	clr.w d0
loc_0_00000608:
	add.w d0,d0
	jsr loc_0_0000062C(pc,d0.w)
	move.b d0,$001F(a1)
	movea.l $0004.w,a6
	btst.b #0,$001E(a1)
	bne.b loc_0_00000622
	jsr _LVOReplyMsg(a6)
loc_0_00000622:
	jsr _LVOPermit(a6)
	movem.l (a7)+,a2/a6
	rts
loc_0_0000062C:
	dc.b $60,$1E,$60,$1C,$60,$36,$60,$56,$60,$20,$60,$1E,$60,$12,$60,$10
	dc.b $60,$0E,$60,$10,$60,$0A,$60,$46,$60,$10,$60,$08,$60,$16,$60,$0E
	dc.b $70,$FD,$4E,$75,$70,$01,$23,$40,$00,$20,$70,$00,$4E,$75,$20,$29
	dc.b $00,$18,$66,$F0,$70,$00,$23,$40,$00,$20,$4E,$75,$2C,$69,$00,$14
	dc.b $52,$6E,$00,$22,$20,$2E,$00,$30,$67,$0C,$D0,$A9,$00,$2C,$20,$40
	dc.b $24,$69,$00,$28,$60,$2A,$53,$6E,$00,$22,$70,$1D,$4E,$75,$08,$29
	dc.b $00,$00,$00,$1B,$66,$00,$00,$78,$20,$69,$00,$28,$2C,$69,$00,$14
	dc.b $52,$6E,$00,$22,$20,$2E,$00,$30,$67,$DC,$D0,$A9,$00,$2C,$24,$40
	dc.b $20,$29,$00,$24,$67,$48,$EE,$88,$53,$80,$24,$D8,$24,$D8,$24,$D8
	dc.b $24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8
	dc.b $24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8
	dc.b $24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8
	dc.b $24,$D8,$24,$D8,$24,$D8,$24,$D8,$24,$D8,$51,$C8,$FF,$BE,$23,$69
	dc.b $00,$24,$00,$20,$53,$6E,$00,$22,$6B,$08,$70,$00,$4E,$75,$70,$1C
	dc.b $4E,$75,$20,$78,$00,$04,$52,$28,$01,$27,$60,$12
loc_0_00000718:
	movea.l $0004.w,a0
	addq.b #1,$0127(a0)
	moveq.l #0,d0
	subq.w #1,app_0022(a6)
	bpl.w loc_0_000007AA
	moveq.l #0,d0
	tst.l app_0030(a6)
	beq.b loc_0_000007AA
	movem.l a2-a4,-(a7)
	lea.l -$0032(a6),a2
	lea.l -$004A(a6),a3
	lea.l app_00BA(a6),a4
	movea.l a6,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	clr.l app_0030(a6)
	movea.l app_0028(a6),a1
	move.l app_002C(a6),d0
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	lea.l app_0226(a6),a1
loc_0_00000768:
	cmpa.l (a1),a2
	beq.b loc_0_0000077C
	movea.l (a1),a1
loc_0_0000076E:
	move.l (a1)+,d0
	bgt.b loc_0_0000076E
	beq.b loc_0_00000780
	bclr #31,d0
	movea.l d0,a1
	bra.b loc_0_00000768
loc_0_0000077C:
	move.l $0004(a2),(a1)
loc_0_00000780:
	lea.l app_0222(a6),a1
loc_0_00000784:
	cmpa.l (a1),a3
	beq.b loc_0_00000790
	move.l (a1),d0
	beq.b loc_0_00000792
	movea.l d0,a1
	bra.b loc_0_00000784
loc_0_00000790:
	move.l (a3),(a1)
loc_0_00000792:
	jsr _LVOSumKickData(a6)
	move.l d0,app_022A(a6)
	movea.l a4,a0
loc_0_0000079C:
	tst.b (a0)+
	bne.b loc_0_0000079C
	move.b #$3A,-(a0)
	move.l a4,d0
	movem.l (a7)+,a2-a4
loc_0_000007AA:
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_1,code
    SECTION section_2,data
