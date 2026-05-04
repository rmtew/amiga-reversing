    INCLUDE "devices/console_lib.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/memory.i"
    INCLUDE "exec/ports.i"
    INCLUDE "graphics/gfxbase.i"
    INCLUDE "graphics/graphics_lib.i"
    INCLUDE "intuition/intuition.i"
    INCLUDE "intuition/intuition_lib.i"
    INCLUDE "intuition/screens.i"
    INCLUDE "resources/disk.i"

    RSSET 0
    RS.B 8
app_0008 RS.L 1
app_000C RS.L 1
app_0010 RS.L 1
    RS.B 28
app_0030 RS.L 1
    RS.B 20
app_0048 RS.L 1
app_004C RS.L 1
app_0050 RS.L 1
    RS.B 3
app_0057 RS.B 1
app_0058 RS.L 1
    RS.B 78
app_00AA RS.L 1
app_00AE RS.L 1
app_00B2 RS.L 1
app_00B6 RS.L 1
    RS.B 4
app_IntuitionBase RS.L 1
    RS.B 4
app_GfxBase RS.L 1
app_00CA RS.L 1
app_00CE RS.L 1
app_00D2 RS.L 1
app_00D6 RS.L 1
app_00DA RS.L 1
app_00DE RS.L 1
app_00E2 RS.L 1
app_00E6 RS.L 1
app_00EA RS.L 1
app_00EE RS.L 1
app_00F2 RS.L 1
app_00F6 RS.L 1
app_00FA RS.L 1
app_00FE RS.L 1
app_0102 RS.L 1
    RS.B 4
app_010A RS.L 1
    RS.B 4
app_0112 RS.B 34
app_0134 RS.L 1
    RS.B 2
app_013A RS.L 1
app_013E RS.L 1
    RS.B 4
app_0146 RS.L 1
app_014A RS.L 1
    RS.B 8
app_0156 RS.L 1
app_015A RS.L 1
app_015E RS.L 1
app_0162 RS.L 1
    RS.B 14
app_0174 RS.L 1
app_0178 RS.L 1
    RS.B 20
app_0190 RS.L 1
app_0194 RS.L 1
app_0198 RS.L 1
    RS.B 2
app_019E RS.L 1
    RS.B 566
app_03D8 RS.L 1
app_03DC RS.L 1
    RS.B 368
app_0550 RS.L 1
    RS.B 10
app_055E RS.L 1
    RS.B 2
app_0564 RS.L 1
app_0568 RS.L 1
app_056C RS.L 1
app_0570 RS.L 1
app_0574 RS.L 1
app_0578 RS.L 1
app_057C RS.L 1
app_0580 RS.L 1
app_0584 RS.L 1
app_0588 RS.L 1
app_058C RS.L 1
    RS.B 1
app_0591 RS.B 1
    RS.B 34
app_05B4 RS.L 1
app_05B8 RS.L 1
    RS.B 18
app_05CE RS.L 1
    RS.B 48
app_0602 RS.L 1
    RS.B 18
app_0618 RS.L 1
    RS.B 48
app_064C RS.L 1
    RS.B 70
app_0696 RS.L 1
app_069A RS.L 1
    RS.B 14
app_06AC RS.L 1
    RS.B 48
app_06E0 RS.L 1
    RS.B 18
app_06F6 RS.L 1
    RS.B 48
app_072A RS.L 1
    RS.B 18
app_0740 RS.L 1
app_0744 RS.L 1
    RS.B 66
app_078A RS.L 1
    RS.B 90
app_07E8 RS.L 1
app_07EC RS.L 1
    RS.B 16
app_0800 RS.L 1
    RS.B 16
app_0814 RS.L 1
app_console_device_iorequest RS.B 48
app_0848 RS.L 1
    RS.B 26
app_0866 RS.L 1
app_086A RS.L 1
app_086E RS.L 1
    RS.B 2
app_0874 RS.L 1
    RS.B 12
app_0884 RS.L 1
    RS.B 188
app_0944 RS.L 1
    RS.B 96
app_09A8 RS.L 1
app_09AC RS.L 1
    RS.B 292
app_0AD4 RS.L 1
    RS.B 56
app_0B10 RS.L 1
    RS.B 244
app_0C08 RS.L 1
    RS.B 96
app_0C6C RS.L 1
    RS.B 408
app_0E08 RS.L 1
app_SIZEOF EQU __RS
app_005A EQU $005A
app_00D8 EQU $00D8
app_00DC EQU $00DC
app_00E4 EQU $00E4
app_00E5 EQU $00E5
app_00E8 EQU $00E8
app_00EC EQU $00EC
app_00F0 EQU $00F0
app_00F4 EQU $00F4
app_00F8 EQU $00F8
app_00FC EQU $00FC
app_0100 EQU $0100
app_0104 EQU $0104
app_0135 EQU $0135
app_0136 EQU $0136
app_0147 EQU $0147
app_0148 EQU $0148
app_0149 EQU $0149
app_014B EQU $014B
app_014C EQU $014C
app_03DE EQU $03DE
app_0560 EQU $0560
app_0567 EQU $0567
app_0585 EQU $0585
app_0586 EQU $0586
app_0587 EQU $0587
app_0815 EQU $0815
app_0816 EQU $0816
app_ConsoleDevice EQU $082C
app_0C6E EQU $0C6E


    SECTION section_0,code
loc_0_00000000:
	bra.w loc_0_00000094
	dc.b $4D,$4F,$4E,$20
	dc.l loc_0_00000024
	dc.b $00,$00,$00,$54
loc_0_00000010:
	dc.b $00,$00,$00,$00
loc_0_00000014:
	dc.l $00000000	; lookup_table
loc_0_00000018:
	dc.l $00000000,$00000000	; lookup_table
loc_0_00000020:
	dc.b $00,$00,$00,$00
loc_0_00000024:
	dc.b $00	; lookup_table
loc_0_00000025:
	dc.b $FF,$FF
loc_0_00000027:
	dc.b $00,$00,$20	; lookup_table
loc_0_0000002A:
	dc.b $08,$00,$00,$00,$00,$00,$00,$00
loc_0_00000032:
	dcb.b $40,$00
loc_0_00000072:
	dc.b $FF,$FF,$FF,$00,$00,$01
	dc.b "$VER: MonAm 3.02 (31.1.92)",$00	; string
	dc.b $00
loc_0_00000094:
	movem.l d0/a0,loc_0_000088EC.l
	move.l #$E1A,d0
	move.l #MEMF_CLEAR|MEMF_PUBLIC,d1
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l d0,a6
	tst.l d0
	bne.b loc_0_000000BA
	moveq.l #103,d0
	rts
loc_0_000000BA:
	cmpi.l #1145394720,loc_0_00000010.l
	seq.b app_0162(a6)
	bne.b loc_0_000000D0
	move.l loc_0_00000014(pc),app_015E(a6)
loc_0_000000D0:
	move.l a7,app_00B6(a6)
	move.l $0004(a7),app_00B2(a6)
	moveq.l #33,d0
	lea.l loc_0_000081D9.l,a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOOpenLibrary(a6)
	movea.l (a7)+,a6
	move.l d0,app_IntuitionBase(a6)
	beq.b loc_0_00000128
	moveq.l #29,d0
	lea.l loc_0_000081F7.l,a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOOpenLibrary(a6)
	movea.l (a7)+,a6
	move.l d0,app_GfxBase(a6)
	beq.b loc_0_00000128
	moveq.l #29,d0
	lea.l loc_0_000081EB.l,a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOOpenLibrary(a6)
	movea.l (a7)+,a6
	move.l d0,$00C2(a6)
	bne.b loc_0_0000012E
loc_0_00000128:
	moveq.l #122,d4
	bra.w loc_0_00000448
loc_0_0000012E:
	lea.l loc_0_00008208.l,a0
	moveq.l #-1,d0
	lea.l app_console_device_iorequest(a6),a1
	moveq.l #0,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOOpenDevice(a6)
	movea.l (a7)+,a6
	tst.l d0
	bne.w loc_0_00000446
	suba.l a1,a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFindTask(a6)
	movea.l (a7)+,a6
	move.l d0,h0dl_DOSBase.l
	move.l d0,$0122(a6)
	moveq.l #-1,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocSignal(a6)
	movea.l (a7)+,a6
	move.b d0,app_0112+MP_SIGBIT(a6)
	moveq.l #-1,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocSignal(a6)
	movea.l (a7)+,a6
	move.b d0,loc_0_0000895E.l
	lea.l app_0112(a6),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAddPort(a6)
	movea.l (a7)+,a6
	movea.l $0004.w,a0
	move.w $0128(a0),d0
	btst #4,d0
	sne.b loc_0_00008906.l
	andi.b #3,d0
	beq.b loc_0_000001E8
	lea.l loc_0_0000159C(pc),a1
	move.l a1,loc_0_00001536.l
	cmp.b #$1,d0
	bne.b loc_0_000001CE
	move.w #$4E71,loc_0_000015B2.l
	bra.b loc_0_000001E8
loc_0_000001CE:
	lea.l loc_0_000019BC(pc),a5
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSupervisor(a6)
	movea.l (a7)+,a6
	andi.b #1,d0
	move.b d0,app_0135(a6)
loc_0_000001E8:
	bsr.w loc_0_00000526
	link a5,#-186
	movea.l a7,a0
	move.l #$BA,d0
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOGetPrefs(a6)
	movea.l (a7)+,a6
	tst.b $00B9(a7)
	sne.b app_0147(a6)
	unlk a5
	bsr.w loc_0_00004C0A
	movea.l app_GfxBase(a6),a0
	movem.w gb_NormalDisplayRows(a0),d0-d1
	move.w #$8000,d2
	move.b loc_0_00000027(pc),d3
	beq.b loc_0_0000022C
	ori.w #4,d2
	add.w d0,d0
loc_0_0000022C:
	lea.l loc_0_00000492(pc),a0
	move.w d1,$0004(a0)
	move.w d0,$0006(a0)
	move.w d2,$000C(a0)
	move.b loc_0_00000027(pc),d0
	move.b app_0147(a6),d1
	eor.b d1,d0
	moveq.l #1,d1
	and.l d1,d0
	eor.b d1,d0
	move.l d0,loc_0_000004BA.l
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOOpenScreen(a6)
	movea.l (a7)+,a6
	move.l d0,app_00CE(a6)
	beq.w loc_0_000003EA
	movea.l d0,a1
	lea.l loc_0_000004CA(pc),a0
	move.l a1,$001E(a0)
	moveq.l #1,d1
	add.b sc_BarHeight(a1),d1
	move.l loc_0_00000496(pc),$0004(a0)
	move.w d1,$0002(a0)
	sub.w d1,$0006(a0)
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOOpenWindow(a6)
	movea.l (a7)+,a6
	move.l d0,app_05B4(a6)
	beq.w loc_0_000003DA
	movea.l #loc_1_00000000,a0
	jsr loc_0_00008146.l
	bsr.w loc_0_00003E98
	bsr.w loc_0_00005CEE
	move.b #$78,app_0149(a6)
	st.b app_014B(a6)
	sf.b app_00E4(a6)
	sf.b app_0146(a6)
	move.l #$FFFFFFFF,app_013E(a6)
	clr.l loc_0_000088F6.l
	clr.b loc_0_000088F5.l
	lea.l app_0010(a6),a0
	moveq.l #15,d0
loc_0_000002D8:
	clr.l (a0)+
	dbf.w d0,loc_0_000002D8
	clr.l app_0050(a6)
	clr.w app_005A(a6)
	clr.w app_0058(a6)
	movea.l $0004.w,a0
	move.l a0,$00BA(a6)
	move.l a0,$005C(a6)
	move.l a0,$0054(a6)
	bsr.w loc_0_00003D66
	bsr.w loc_0_00003F58
	lea.l app_05B8(a6),a3
	bsr.w loc_0_00007FB8
	bsr.w loc_0_00005696
	bsr.w loc_0_000009B8
	lea.l loc_0_00000032(pc),a0
	tst.b (a0)
	beq.b loc_0_0000031E
	bsr.w loc_0_000074EC
loc_0_0000031E:
	pea.l loc_0_00000554(pc)
	move.l app_015E(a6),d0
	beq.b loc_0_0000033E
	lea.l loc_0_00000336(pc),a3
	movea.l loc_0_000088F0.l,a4
	bra.w loc_0_0000556A
loc_0_00000336:
	dc.b $4D,$45,$4D,$54,$41,$53,$4B,$00
loc_0_0000033E:
	movem.l loc_0_000088EC.l,d0/a0
	lea.l $0(a0,d0.l),a1
loc_0_0000034A:
	cmpi.b #32,-(a1)
	dbhi.w d0,loc_0_0000034A
	clr.b $0001(a1)
	cmpa.l a0,a1
	bcs.w loc_0_0000550E
	st.b d0
loc_0_0000035E:
	cmpi.b #32,(a0)+
	beq.b loc_0_0000035E
	cmpi.b #34,-$0001(a0)
	beq.b loc_0_00000370
	subq.l #1,a0
	sf.b d0
loc_0_00000370:
	movea.l a0,a3
loc_0_00000372:
	move.b (a0)+,d1
	beq.b loc_0_00000396
	tst.b d0
	beq.b loc_0_00000382
	cmp.b #$22,d1
	bne.b loc_0_00000372
	bra.b loc_0_00000388
loc_0_00000382:
	cmp.b #$20,d1
	bne.b loc_0_00000372
loc_0_00000388:
	clr.b -$0001(a0)
loc_0_0000038C:
	move.b (a0)+,d1
	beq.b loc_0_00000396
	cmp.b #$20,d1
	beq.b loc_0_0000038C
loc_0_00000396:
	lea.l -$0001(a0),a4
	bra.w loc_0_0000554E
loc_0_0000039E:
	bsr.w loc_0_0000752C
	movea.l app_00B6(a6),a7
	move.l app_013A(a6),d0
	beq.b loc_0_000003BC
	movea.l app_0136(a6),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
loc_0_000003BC:
	bsr.w loc_0_00007740
	jsr loc_0_000081B6.l
	bsr.w loc_0_00000528
	movea.l app_05B4(a6),a0
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOCloseWindow(a6)
	movea.l (a7)+,a6
loc_0_000003DA:
	movea.l app_00CE(a6),a0
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOCloseScreen(a6)
	movea.l (a7)+,a6
loc_0_000003EA:
	move.b app_0135(a6),d0
	beq.b loc_0_00000400
	lea.l loc_0_000019BC(pc),a5
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSupervisor(a6)
	movea.l (a7)+,a6
loc_0_00000400:
	lea.l app_0112(a6),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVORemPort(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	move.b app_0112+MP_SIGBIT(a6),d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeSignal(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	move.b loc_0_0000895E.l,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeSignal(a6)
	movea.l (a7)+,a6
	lea.l app_console_device_iorequest(a6),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOCloseDevice(a6)
	movea.l (a7)+,a6
loc_0_00000446:
	moveq.l #0,d4
loc_0_00000448:
	move.l $00C2(a6),d0
	bsr.b loc_0_00000472
	move.l app_GfxBase(a6),d0
	bsr.b loc_0_00000472
	move.l app_IntuitionBase(a6),d0
	bsr.b loc_0_00000472
	move.l #$E1A,d0
	movea.l a6,a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	move.l d4,d0
	rts
loc_0_00000472:
	beq.b loc_0_00000482
	movea.l d0,a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOCloseLibrary(a6)
	movea.l (a7)+,a6
loc_0_00000482:
	rts
	dc.l loc_0_0000048C
	dc.b $00,$08,$00,$00
loc_0_0000048C:
	dc.b $74,$6F,$70,$61,$7A,$00
loc_0_00000492:
	dc.b $00,$00,$00,$00
loc_0_00000496:
	dc.b $02,$80,$00,$C8,$00,$01,$00,$01,$80,$00,$10,$0F,$00,$00,$00,$00
	dc.l loc_0_000004FA
	dcb.b $8,$00
	dc.l loc_0_000004B6
loc_0_000004B6:
	dc.b $80,$00,$00,$2C
loc_0_000004BA:
	dc.b $00,$00,$00,$01,$80,$00,$00,$39,$00,$00,$00,$01,$00,$00,$00,$00
loc_0_000004CA:
	dc.b $00,$00,$00,$00,$02,$80,$00,$C8,$00,$01,$00,$00,$04,$00,$00,$02
	dc.b $19,$40
	dcb.b $1D,$00
	dc.b $0F
loc_0_000004FA:
	dc.b $4D,$6F,$6E,$41,$6D,$20,$76,$65,$72,$73,$69,$6F,$6E,$20,$33,$2E
	dc.b $30,$32,$20,$20,$43,$6F,$70,$79,$72,$69,$67,$68,$74,$20,$A9,$20
	dc.b $31,$39,$39,$32,$20,$48,$69,$53,$6F,$66,$74,$00
loc_0_00000526:
	rts
loc_0_00000528:
	rts
loc_0_0000052A:
	lea.l app_05B8(a6),a3
	move.w #$1,$000A(a3)
	move.w app_00EE(a6),$000C(a3)
	bra.w loc_0_00005836
	dc.b $4A,$2E,$00,$E5,$67,$0E,$48,$E7,$40,$10,$61,$E0,$51,$EE,$00,$E5
	dc.b $4C,$DF,$08,$02,$4E,$75
loc_0_00000554:
	dc.b $61,$00,$3B,$CE,$6B,$36,$61,$E2,$B2,$3C,$00,$09,$67,$22,$B2,$3C
	dc.b $00,$88,$67,$22,$B2,$3C,$00,$87,$67,$00,$49,$BC,$60,$00,$00,$4E
	dc.b $20,$2E,$00,$DE,$67,$DA,$26,$40,$61,$00,$01,$2E,$67,$D2,$60,$D8
	dc.b $61,$00,$05,$BA,$60,$CA,$61,$00,$05,$E4,$60,$C4,$61,$AC,$20,$2E
	dc.b $00,$DE,$67,$BC,$26,$40,$B2,$3C,$00,$5A,$67,$00,$00,$96,$B2,$3C
	dc.b $00,$3A,$65,$0E,$B2,$3C,$00,$48,$67,$00,$49,$7C,$61,$00,$01,$6E
	dc.b $60,$9E,$04,$01,$00,$30,$61,$00,$05,$2C,$60,$94,$10,$01,$B0,$3C
	dc.b $00,$41,$65,$04,$02,$00,$00,$DF,$41,$FA,$3D,$A4,$16,$18,$14,$18
	dc.b $67,$9E,$B4,$00,$67,$04,$54,$48,$60,$F2,$4A,$03,$67,$48,$53,$03
	dc.b $67,$28,$53,$03,$67,$1A,$53,$03,$67,$0C,$0C,$2E,$00,$01,$01,$34
	dc.b $67,$34,$72,$21,$60,$1C,$4A,$2E,$01,$34,$67,$2A,$72,$22,$60,$12
	dc.b $4A,$2E,$01,$34,$66,$20,$72,$23,$60,$08,$72,$24,$4A,$2E,$01,$34
	dc.b $6B,$14,$3F,$01,$61,$00,$FF,$10,$32,$1F,$61,$00,$64,$3A,$50,$EE
	dc.b $00,$E5,$60,$00,$FF,$2C,$D0,$D0,$26,$6E,$00,$DE,$4E,$90,$60,$00
	dc.b $FF,$20,$2F,$0B,$47,$EE,$05,$B8,$61,$00,$50,$58,$47,$EE,$07,$40
	dc.b $4C,$AE,$00,$1F,$08,$6A,$61,$00,$50,$44,$50,$EB,$00,$14,$24,$5F
	dc.b $41,$EB,$00,$16,$43,$EA,$00,$16,$70,$19,$30,$D9,$51,$C8,$FF,$FC
	dc.b $50,$C7,$50,$C4,$61,$00,$54,$EC,$1F,$2B,$00,$35,$61,$00,$57,$60
	dc.b $10,$1F,$0C,$2B,$00,$04,$00,$34,$66,$04,$17,$40,$00,$35,$61,$00
	dc.b $58,$9E,$61,$00,$3A,$98,$6B,$14,$B2,$3C,$00,$1B,$67,$06,$61,$18
	dc.b $67,$F0,$60,$F4,$61,$00,$57,$02,$60,$00,$FE,$B6,$B2,$3C,$00,$5A
	dc.b $67,$F2,$61,$00,$00,$78,$60,$DA,$48,$7A,$00,$60,$20,$6B,$00,$3E
	dc.b $B2,$3C,$00,$80,$67,$40,$B2,$3C,$00,$82,$67,$3E,$B2,$3C,$00,$83
	dc.b $67,$3C,$B2,$3C,$00,$81,$67,$2A,$B2,$3C,$00,$84,$67,$34,$B2,$3C
	dc.b $00,$85,$67,$32,$B2,$3C,$00,$89,$67,$28,$B2,$3C,$00,$8A,$67,$26
	dc.b $4A,$6E,$07,$44,$67,$06,$B2,$3C,$00,$20,$67,$06,$58,$8F,$72,$00
	dc.b $4E,$75,$4E,$E8,$00,$06,$4E,$E8,$00,$04,$4E,$E8,$00,$08,$4E,$E8
	dc.b $00,$0A,$4E,$E8,$00,$0C,$4E,$E8,$00,$0E,$6B,$02,$4E,$75,$42,$AB
	dc.b $00,$0A,$20,$6B,$00,$3E,$4E,$90,$72,$00,$4E,$75,$B2,$3C,$00,$41
	dc.b $67,$00,$04,$4C,$B2,$3C,$00,$42,$67,$00,$00,$FA,$B2,$3C,$00,$45
	dc.b $67,$00,$00,$C0,$B2,$3C,$00,$47,$67,$00,$04,$7C,$B2,$3C,$00,$4C
	dc.b $67,$00,$05,$C8,$B2,$3C,$00,$4F,$67,$00,$0B,$5E,$B2,$3C,$00,$50
	dc.b $67,$00,$01,$98,$B2,$3C,$00,$52,$67,$1A,$B2,$3C,$00,$53,$67,$00
	dc.b $04,$94,$B2,$3C,$00,$54,$67,$00,$09,$46,$B2,$3C,$00,$57,$67,$00
	dc.b $04,$88,$4E,$75,$2F,$0B,$76,$04,$41,$FA,$7E,$36,$61,$00,$12,$FC
	dc.b $61,$00,$52,$3C,$66,$48,$4A,$14,$67,$44,$24,$4C,$12,$1A,$67,$F0
	dc.b $B2,$3C,$00,$3D,$66,$F6,$43,$EE,$0A,$D4,$24,$0A,$94,$89,$53,$42
	dc.b $61,$00,$6A,$4C,$66,$DA,$48,$E7,$00,$88,$28,$4A,$61,$00,$63,$AA
	dc.b $4C,$DF,$11,$00,$66,$CA,$20,$82,$2F,$08,$61,$00,$55,$DC,$24,$1F
	dc.b $4A,$6E,$07,$44,$66,$04,$61,$00,$57,$12,$26,$5F,$4E,$75,$61,$00
	dc.b $55,$C8,$26,$5F,$4E,$75,$2F,$0B,$47,$EE,$07,$40,$4A,$6B,$00,$04
	dc.b $66,$08,$61,$00,$56,$F6,$26,$5F,$4E,$75,$61,$00,$57,$32,$26,$5F
	dc.b $4E,$75,$10,$2B,$00,$34,$B0,$3C,$00,$02,$67,$00,$FF,$78,$B0,$3C
	dc.b $00,$01,$67,$00,$58,$4C,$B0,$3C,$00,$04,$67,$02,$4E,$75,$0A,$2B
	dc.b $00,$0C,$00,$35,$13,$EB,$00,$35
	dc.l loc_0_0000002A
	dc.b $61,$00,$4E,$74,$60,$00,$56,$FC,$41,$FA,$7E,$15,$61,$00,$00,$06
	dc.b $66,$A8,$4E,$75,$2F,$0B,$76,$04,$61,$00,$12,$44,$61,$00,$51,$84
	dc.b $66,$62,$4A,$14,$67,$5E,$61,$00,$63,$28,$67,$0A,$61,$00,$56,$06
	dc.b $49,$EE,$0A,$D4,$60,$E6,$2A,$02,$74,$01,$4A,$01,$67,$2E,$B2,$3C
	dc.b $00,$2C,$66,$E8,$12,$1C,$B2,$3C,$00,$3F,$67,$42,$B2,$3C,$00,$2A
	dc.b $67,$4E,$B2,$3C,$00,$3D,$67,$54,$B2,$3C,$00,$2D,$66,$04,$4A,$14
	dc.b $67,$5A,$61,$00,$62,$EE,$66,$C4,$4A,$01,$66,$C0,$2C,$02,$61,$00
	dc.b $55,$0C,$24,$06,$76,$01,$22,$45,$61,$00,$35,$06,$66,$0A,$26,$5F
	dc.b $70,$01,$4E,$75,$61,$00,$54,$F6,$26,$5F,$70,$00,$4E,$75,$61,$00
	dc.b $62,$88,$66,$98,$2F,$0C,$61,$00,$54,$E4,$28,$5F,$76,$04,$60,$D6
	dc.b $4A,$1C,$66,$88,$61,$00,$54,$D6,$76,$03,$60,$CA,$4A,$1C,$66,$00
	dc.b $FF,$7C,$61,$00,$54,$C8,$76,$02,$74,$00,$60,$BA,$61,$00,$54,$BE
	dc.b $22,$45,$61,$00,$35,$58,$66,$C0,$61,$00,$35,$84,$60,$B0,$61,$00
	dc.b $6C,$BC,$66,$08,$41,$FA,$7D,$89,$60,$00,$11,$DC,$50,$EE,$00,$E4
	dc.b $61,$00,$56,$20,$51,$EE,$00,$E4,$4E,$75
loc_0_0000090A:
	dc.l loc_0_0000095E
	dc.b $E9,$05
	dc.l loc_0_00000964
	dc.b $ED,$00
	dc.l loc_0_0000096A
	dc.b $E0,$0D
	dc.l loc_0_00000970
	dc.b $09,$E5
	dc.l loc_0_00000976
	dc.b $0D,$E0
	dc.l loc_0_0000097C
	dc.b $00,$ED
	dc.l loc_0_00000982
	dc.b $A9,$65
	dc.l loc_0_00000989
	dc.b $AD,$60
	dc.l loc_0_00000990
	dc.b $A0,$6D
	dc.l loc_0_00000997
	dc.b $B0,$65
	dc.l loc_0_0000099E
	dc.b $A9,$70
	dc.l loc_0_000009A5
	dc.b $B0,$70
	dc.l loc_0_000009AC
	dc.b $F0,$00
	dc.l loc_0_000009B2
	dc.b $00,$F0
loc_0_0000095E:
	dc.b $8C,$46,$51,$E6,$72,$00
loc_0_00000964:
	dc.b $8C,$47,$50,$E7,$F0,$00
loc_0_0000096A:
	dc.b $8C,$48,$D0,$E8,$70,$00
loc_0_00000970:
	dc.b $C6,$54,$AD,$66,$75,$00
loc_0_00000976:
	dc.b $C7,$53,$AD,$67,$F3,$00
loc_0_0000097C:
	dc.b $C8,$D3,$AD,$68,$73,$00
loc_0_00000982:
	dc.b $89,$40,$57,$AA,$63,$78,$00
loc_0_00000989:
	dc.b $89,$41,$56,$AA,$64,$F6,$00
loc_0_00000990:
	dc.b $89,$42,$D6,$AA,$65,$76,$00
loc_0_00000997:
	dc.b $86,$4C,$D6,$AB,$63,$78,$00
loc_0_0000099E:
	dc.b $8B,$40,$57,$A6,$6D,$F6,$00
loc_0_000009A5:
	dc.b $8A,$4C,$DA,$A9,$6D,$F9,$00
loc_0_000009AC:
	dc.b $81,$4B,$D1,$EB,$F2,$00
loc_0_000009B2:
	dc.b $CB,$D4,$A5,$6B,$F5,$00
loc_0_000009B8:
	lea.l app_0618(a6),a3
	move.l a3,app_00DE(a6)
	lea.l app_05CE(a6),a3
	moveq.l #1,d0
	move.w d0,app_00F2(a6)
	move.w app_00DC(a6),d1
	move.w app_00EC(a6),d2
	subq.w #2,d2
	move.w d2,app_00FE(a6)
	move.w #$A,d3
	bsr.w loc_0_0000565E
	move.w #$19,app_00FA(a6)
	move.w app_00EC(a6),d0
	subi.w #26,d0
	move.w d0,app_00F4(a6)
	move.w $0008(a3),d0
	add.w $000C(a3),d0
	add.w app_00DC(a6),d0
	add.w app_00DC(a6),d0
	addq.w #1,d0
	move.w d0,app_00F6(a6)
	neg.w d0
	add.w app_00EA(a6),d0
	sub.w app_00DC(a6),d0
	ext.l d0
	divu.w app_00D8(a6),d0
	move.w d0,app_0104(a6)
	subq.w #1,d0
	lsr.w #1,d0
	move.w d0,app_0102(a6)
	move.w app_00F4(a6),d0
	subq.w #3,d0
	move.w d0,app_00FC(a6)
	move.w app_0102(a6),d0
	mulu.w app_00D8(a6),d0
	add.w app_00F6(a6),d0
	add.w app_00DC(a6),d0
	addq.w #1,d0
	move.w d0,app_00F8(a6)
	neg.w d0
	add.w app_00EA(a6),d0
	sub.w app_00DC(a6),d0
	subq.w #1,d0
	ext.l d0
	divu.w app_00D8(a6),d0
	move.w d0,app_0100(a6)
	addq.b #2,app_0602(a6)
	addq.b #3,app_064C(a6)
	addq.b #3,app_06E0(a6)
	addq.b #1,app_0696(a6)
	addq.b #1,app_072A(a6)
	move.w app_00F0(a6),d0
	bsr.w loc_0_00000CFC
	moveq.l #MEMF_FAST,d1
loc_0_00000A78:
	movem.w d0-d1,-(a7)
	moveq.l #5,d0
	sub.b d1,d0
	move.b d0,$003C(a3)
	suba.l a0,a0
	bsr.w loc_0_00001176
	move.l a0,$0044(a3)
	cmpi.b #1,$003C(a3)
	beq.b loc_0_00000ACA
	cmpi.b #2,$003C(a3)
	bne.b loc_0_00000AB0
	st.b $0042(a3)
	move.l #$70630000,$0044(a0)
	move.l $0054(a6),$0038(a3)
loc_0_00000AB0:
	move.w (a7),d0
	rol.w #4,d0
	move.w d0,(a7)
	andi.w #15,d0
	bne.b loc_0_00000AC2
	bsr.w loc_0_00005DD2
	bra.b loc_0_00000AD2
loc_0_00000AC2:
	bsr.w loc_0_00000C90
	bsr.w loc_0_0000565E
loc_0_00000ACA:
	bsr.w loc_0_00005DD2
	bsr.w loc_0_00000C84
loc_0_00000AD2:
	lea.l $004A(a3),a3
	movem.w (a7)+,d0-d1
	dbf.w d1,loc_0_00000A78
	rts
	dc.b $61,$00,$03,$04,$60,$00,$53,$F8,$47,$EE,$05,$CE,$74,$06,$B2,$2B
	dc.b $00,$3C,$67,$0A,$47,$EB,$00,$4A,$51,$CA,$FF,$F4,$4E,$75,$20,$2E
	dc.b $00,$DE,$67,$1A,$B0,$8B,$66,$02,$4E,$75,$2F,$0B,$26,$40,$4A,$6B
	dc.b $00,$04,$67,$08,$51,$C7,$50,$C4,$61,$00,$50,$3C,$26,$5F,$20,$6B
	dc.b $00,$44,$61,$00,$07,$46,$2D,$4B,$00,$DE,$4A,$6B,$00,$04,$66,$08
	dc.b $12,$3C,$00,$C0,$60,$00,$00,$CA,$50,$C7,$50,$C4,$60,$00,$50,$18
	dc.b $36,$3C,$07,$8A,$20,$2E,$00,$DE,$67,$04,$26,$00,$96,$8E,$74,$06
	dc.b $B6,$7C,$07,$8A,$66,$04,$36,$3C,$05,$84,$06,$43,$00,$4A,$4A,$76
	dc.b $30,$04,$66,$06,$51,$CA,$FF,$EA,$4E,$75,$47,$F6,$30,$00,$60,$8E
	dc.b $4E,$75,$0C,$2B,$00,$02,$00,$34,$67,$12,$0C,$2B,$00,$04,$00,$34
	dc.b $66,$0C,$20,$6B,$00,$44,$61,$00,$06,$E2,$66,$02,$4E,$75,$41,$FA
	dc.b $79,$A6,$61,$00,$0E,$50,$66,$F4,$0C,$2B,$00,$04,$00,$34,$66,$12
	dc.b $20,$6B,$00,$44,$61,$00,$05,$98,$61,$00,$02,$EC,$61,$00,$05,$50
	dc.b $60,$04,$27,$42,$00,$38,$60,$00,$53,$6A,$0C,$2B,$00,$04,$00,$34
	dc.b $66,$0A,$41,$FA,$79,$88,$61,$00,$0E,$1C,$67,$02,$4E,$75,$2F,$02
	dc.b $20,$6B,$00,$44,$61,$00,$05,$68,$61,$00,$02,$C0,$24,$1F,$52,$82
	dc.b $66,$0E,$34,$28,$00,$22,$94,$6B,$00,$06,$54,$42,$61,$00,$02,$AC
	dc.b $61,$00,$05,$0C,$60,$00,$53,$2C,$72,$40,$60,$04,$12,$3C,$00,$80
loc_0_00000C00:
	tst.w app_0744(a6)
	bne.b loc_0_00000C1A
	move.b $003C(a3),d2
	cmp.b #$1,d2
	beq.b loc_0_00000C1A
	move.w app_00F0(a6),d0
	bsr.w loc_0_00000CD4
	bpl.b loc_0_00000C1C
loc_0_00000C1A:
	rts
loc_0_00000C1C:
	move.w d0,app_00F0(a6)
	bsr.w loc_0_00000CFC
	lea.l loc_0_00000C62(pc),a0
	bsr.w loc_0_00000C30
	lea.l loc_0_00000C78(pc),a0
loc_0_00000C30:
	lea.l app_0618(a6),a3
	moveq.l #3,d2
loc_0_00000C36:
	rol.w #4,d0
	rol.w #4,d1
	movem.w d0-d1,-(a7)
	andi.w #15,d0
	andi.w #15,d1
	cmp.w d0,d1
	beq.b loc_0_00000C54
	movem.l d2/a0,-(a7)
	jsr (a0)
	movem.l (a7)+,d2/a0
loc_0_00000C54:
	lea.l $004A(a3),a3
	movem.w (a7)+,d0-d1
	dbf.w d2,loc_0_00000C36
loc_0_00000C60:
	rts
loc_0_00000C62:
	tst.b d1
	beq.b loc_0_00000C60
	bsr.w loc_0_00005696
	sf.b d4
	sf.b d7
	bsr.w loc_0_00005B56
	clr.w $0004(a3)
	rts
loc_0_00000C78:
	dc.b $4A,$00,$67,$E4,$61,$00,$00,$12,$61,$00,$49,$DC
loc_0_00000C84:
	movea.l $0044(a3),a0
	bsr.w loc_0_00000F9A
	bra.w loc_0_00005F22
loc_0_00000C90:
	move.w app_00F6(a6),d1
	btst #3,d0
	bne.b loc_0_00000C9E
	move.w app_00F8(a6),d1
loc_0_00000C9E:
	move.w d1,-(a7)
	move.w app_00F2(a6),d1
	btst #1,d0
	bne.b loc_0_00000CAE
	move.w app_00F4(a6),d1
loc_0_00000CAE:
	movem.w d0-d1,-(a7)
	andi.w #3,d0
	asl.w #1,d0
	addi.w #250,d0
	move.w -$2(a6,d0.w),d2
	moveq.l #12,d0
	and.w (a7)+,d0
	asr.w #1,d0
	addi.w #256,d0
	move.w -$2(a6,d0.w),d3
	movem.w (a7)+,d0-d1
	rts
loc_0_00000CD4:
	move.l d2,-(a7)
	bsr.w loc_0_00000CFC
	subq.b #2,d2
	asl.b #4,d2
	or.b d1,d2
	move.w d0,d1
loc_0_00000CE2:
	move.w #$F0,d0
	and.b (a0)+,d0
	beq.b loc_0_00000CF4
	cmp.b d2,d0
	bne.b loc_0_00000CE2
	moveq.l #15,d0
	and.b -(a0),d0
	bra.b loc_0_00000CF6
loc_0_00000CF4:
	moveq.l #-1,d0
loc_0_00000CF6:
	movem.l (a7)+,d2
	rts
loc_0_00000CFC:
	mulu.w #$6,d0
	addi.l #loc_0_0000090A,d0
	movea.l d0,a1
	movea.l (a1)+,a0
	move.w (a1),d0
	rts
	dc.b $4A,$6E,$07,$44,$66,$00,$00,$84,$10,$2B,$00,$34,$B0,$3C,$00,$02
	dc.b $67,$78,$B0,$3C,$00,$04,$66,$0A,$20,$6B,$00,$44,$4A,$A8,$00,$1E
	dc.b $67,$68,$2F,$0B,$76,$04,$41,$FA,$79,$64,$61,$00,$0D,$44,$20,$57
	dc.b $42,$14,$4A,$28,$00,$42,$67,$0E,$20,$68,$00,$44,$41,$E8,$00,$44
	dc.b $22,$4C,$12,$D8,$66,$FC,$61,$00,$4C,$6C,$67,$06,$61,$00,$50,$40
	dc.b $60,$36,$70,$00,$4A,$14,$67,$16,$20,$4C,$48,$E7,$00,$14,$61,$00
	dc.b $5D,$CA,$4C,$DF,$28,$00,$67,$06,$61,$00,$50,$DC,$60,$D8,$61,$00
	dc.b $50,$1E,$26,$57,$50,$C7,$61,$00,$00,$14,$4A,$2B,$00,$42,$67,$08
	dc.b $61,$00,$00,$56,$61,$00,$51,$4A,$26,$5F,$4E,$75,$3F,$07,$51,$C4
	dc.b $51,$C7,$61,$00,$4D,$B4,$3E,$1F,$51,$EB,$00,$42,$4A,$14,$67,$32
	dc.b $17,$7C,$00,$01,$00,$42,$22,$6B,$00,$44,$41,$E9,$00,$44,$70,$3F
	dc.b $10,$DC,$57,$C8,$FF,$FC,$42,$20,$20,$29,$00,$44,$02,$80,$DF,$DF
	dc.b $FF,$00,$B0,$BC,$70,$63,$00,$00,$66,$08,$23,$40,$00,$44,$50,$EB
	dc.b $00,$42,$50,$C4,$60,$00,$4D,$72
loc_0_00000DE6:
	move.l a3,-(a7)
	lea.l app_06F6(a6),a3
	moveq.l #4,d0
loc_0_00000DEE:
	move.l d0,-(a7)
	bsr.w loc_0_0000113E
	move.l $0044(a3),d0
loc_0_00000DF8:
	movea.l d0,a0
	move.l (a0),d0
	bne.b loc_0_00000DF8
loc_0_00000DFE:
	tst.b $0009(a0)
	beq.b loc_0_00000E38
	bpl.b loc_0_00000E0E
	cmpi.b #3,$0008(a0)
	beq.b loc_0_00000E56
loc_0_00000E0E:
	bsr.w loc_0_0000126A
	movem.l d3/a0-a5,-(a7)
	lea.l $0044(a0),a4
	bsr.w loc_0_00006B70
	movem.l (a7)+,d3/a0-a5
	bne.b loc_0_00000E38
	move.l d2,d1
	cmpi.b #4,$0008(a0)
	bne.b loc_0_00000E34
	bsr.w loc_0_00000E96
	bra.b loc_0_00000E38
loc_0_00000E34:
	move.l d1,$000A(a0)
loc_0_00000E38:
	movea.l $0004(a0),a0
	move.l a0,d0
	bne.b loc_0_00000DFE
	movea.l $0044(a3),a0
	bsr.w loc_0_000010FE
	lea.l -$004A(a3),a3
	move.l (a7)+,d0
	dbf.w d0,loc_0_00000DEE
	movea.l (a7)+,a3
	rts
loc_0_00000E56:
	movem.l d0/d3/d6/a0-a2,-(a7)
	movea.l $0054(a6),a1
	move.l $000A(a0),d0
	addq.l #1,d0
	andi.b #254,d0
	movea.l d0,a2
	cmpa.l a2,a1
	blt.b loc_0_00000E86
	move.w $0006(a3),d6
	subq.w #3,d6
	bcs.b loc_0_00000E86
	move.l a1,-(a7)
loc_0_00000E78:
	bsr.w loc_0_00006964
	cmpa.l (a7),a2
	beq.b loc_0_00000E8E
	dbf.w d6,loc_0_00000E78
	movea.l (a7)+,a1
loc_0_00000E86:
	move.l a1,d1
	movem.l (a7)+,d0/d3/d6/a0-a2
	bra.b loc_0_00000E34
loc_0_00000E8E:
	movea.l (a7)+,a1
	movem.l (a7)+,d0/d3/d6/a0-a2
	bra.b loc_0_00000E38
loc_0_00000E96:
	bsr.w loc_0_00006EA6
	move.l d2,d1
	beq.b loc_0_00000ECC
	movem.l a0-a2,-(a7)
	cmp.l #$FFFF,d1
	bls.b loc_0_00000EAC
	moveq.l #-1,d1
loc_0_00000EAC:
	movem.l $0012(a0),a1-a2
	move.w $0022(a0),d0
	movea.l $000E(a0),a0
	bsr.w loc_0_00000ECE
	move.l a0,d2
	movem.l (a7)+,a0-a2
	move.w d1,$0022(a0)
	move.l d2,$000E(a0)
loc_0_00000ECC:
	rts
loc_0_00000ECE:
	cmp.w #$1,d1
	bhi.b loc_0_00000EDA
	moveq.l #1,d1
	movea.l a1,a0
	rts
loc_0_00000EDA:
	sub.w d1,d0
	bcs.b loc_0_00000EF6
	beq.b loc_0_00000EF4
	subq.w #1,d0
loc_0_00000EE2:
	cmpi.b #10,-(a0)
	bne.b loc_0_00000EE2
	dbf.w d0,loc_0_00000EE2
loc_0_00000EEC:
	cmpi.b #10,-(a0)
	bne.b loc_0_00000EEC
	addq.l #1,a0
loc_0_00000EF4:
	rts
loc_0_00000EF6:
	neg.w d0
	subq.w #1,d0
loc_0_00000EFA:
	cmpi.b #10,(a0)+
	bne.b loc_0_00000EFA
	cmpa.l a2,a0
	dbcc.w d0,loc_0_00000EFA
	bcs.b loc_0_00000EF4
	sub.w d0,d1
	subq.w #1,d1
	subq.l #1,a0
	bra.b loc_0_00000EEC
	dc.b $61,$00,$02,$2C,$20,$6B,$00,$44,$61,$00,$02,$5C,$66,$00,$00,$80
	dc.b $60,$00,$4F,$32,$0C,$2B,$00,$04,$00,$34,$66,$08,$51,$C4,$51,$C7
	dc.b $61,$00,$4C,$24,$20,$6B,$00,$44,$61,$00,$02,$A4,$66,$00,$00,$60
	dc.b $0C,$2B,$00,$04,$00,$34,$67,$02,$4E,$75,$20,$6B,$00,$44,$61,$00
	dc.b $02,$F4,$72,$03,$0C,$2B,$00,$01,$00,$3C,$66,$02,$72,$02,$60,$00
	dc.b $01,$96,$20,$6B,$00,$44,$20,$28,$00,$04,$67,$04,$20,$40,$60,$2A
	dc.b $20,$10,$66,$02,$4E,$75,$20,$40,$20,$10,$66,$FA,$60,$1C,$20,$6B
	dc.b $00,$44,$20,$10,$67,$04,$20,$40,$60,$10,$20,$28,$00,$04,$66,$02
	dc.b $4E,$75,$20,$40,$20,$28,$00,$04,$66,$F8
loc_0_00000F9A:
	bsr.w loc_0_0000113E
loc_0_00000F9E:
	move.l a0,-(a7)
	sf.b d4
	sf.b d7
	bsr.w loc_0_00005B56
	movea.l (a7),a0
	cmpi.b #3,$0008(a0)
	bcc.b loc_0_00000FB6
	bsr.w loc_0_00005696
loc_0_00000FB6:
	movea.l (a7)+,a0
	moveq.l #-1,d0
	movea.l a0,a1
loc_0_00000FBC:
	addq.l #1,d0
	move.l (a1),d1
	movea.l d1,a1
	bne.b loc_0_00000FBC
	move.w d0,$0048(a3)
	bsr.w loc_0_000010FE
	st.b d4
	cmpa.l app_00DE(a6),a3
	seq.b d7
	bsr.w loc_0_00005B56
	bra.w loc_0_00005F22
	dc.b $10,$2B,$00,$3C,$61,$00,$02,$BE,$67,$0A,$41,$FA,$75,$93,$61,$00
	dc.b $39,$24,$67,$02,$4E,$75,$41,$EE,$0A,$D4,$61,$00,$00,$94,$26,$6E
	dc.b $00,$DE,$41,$EE,$0A,$D4,$61,$00,$00,$04,$60,$96
loc_0_00001008:
	move.l a0,-(a7)
	bsr.w loc_0_0000113E
	movea.l $0044(a3),a0
	tst.l $0012(a0)
	beq.b loc_0_00001022
	bsr.w loc_0_00001176
	bne.b loc_0_00001022
	bsr.w loc_0_00001244
loc_0_00001022:
	movea.l (a7)+,a1
	bsr.w loc_0_00001204
	tst.l $001E(a0)
	beq.b loc_0_00001042
	st.b $0009(a0)
	move.l #$70630000,$0044(a0)
	move.l $0054(a6),d2
	bsr.w loc_0_00000E96
loc_0_00001042:
	rts
loc_0_00001044:
	tst.b app_0585(a6)
	beq.b loc_0_00001050
	move.l app_0578(a6),d0
	bne.b loc_0_00001052
loc_0_00001050:
	rts
loc_0_00001052:
	movea.l d0,a0
	lea.l $0004(a0),a0
	move.l a0,-(a7)
	bsr.w loc_0_0000107C
	movea.l (a7)+,a0
	bne.b loc_0_00001050
	lea.l app_06AC(a6),a3
	bsr.b loc_0_00001008
	tst.w $0004(a3)
	bne.w loc_0_00000F9E
	bsr.w loc_0_000010FE
	move.b #$C0,d1
	bra.w loc_0_00000C00
loc_0_0000107C:
	move.l a0,-(a7)
	movea.l a0,a5
	moveq.l #0,d2
	bsr.w loc_0_0000492E
	movea.l (a7)+,a0
	beq.b loc_0_0000108C
	rts
loc_0_0000108C:
	move.l a3,app_0156(a6)
	adda.l d4,a3
	move.l a3,app_015A(a6)
	bsr.w loc_0_00007C2C
	beq.b loc_0_000010A8
	move.l d0,app_057C(a6)
	move.l a0,app_0580(a6)
	moveq.l #0,d0
	rts
loc_0_000010A8:
	clr.l app_057C(a6)
	clr.l app_0580(a6)
	rts
	dc.b $4A,$6E,$07,$44,$66,$10,$12,$2B,$00,$34,$10,$2B,$00,$3C,$61,$00
	dc.b $01,$DE,$66,$00,$00,$04,$4E,$75,$20,$6B,$00,$44,$52,$01,$B2,$3C
	dc.b $00,$04,$63,$02,$72,$01,$B2,$3C,$00,$02,$66,$08,$B0,$3C,$00,$01
	dc.b $66,$EA,$67,$0C,$B2,$3C,$00,$04,$66,$06,$4A,$A8,$00,$12,$67,$DC
	dc.b $61,$00,$00,$4A,$11,$41,$00,$08,$60,$00,$FE,$A2
loc_0_000010FE:
	move.l a0,$0044(a3)
	move.b $0008(a0),$0034(a3)
	bsr.w loc_0_00005DD2
	movea.l $0044(a3),a0
	bsr.w loc_0_0000126A
	move.l $000A(a0),$0038(a3)
	move.b $0009(a0),$0042(a3)
	move.b $0008(a0),d0
	cmp.b #$4,d0
	bne.b loc_0_0000113C
	move.l $000E(a0),$0038(a3)
	move.w $0022(a0),$0036(a3)
	move.b $0024(a0),$0035(a3)
loc_0_0000113C:
	rts
loc_0_0000113E:
	move.l a0,-(a7)
	movea.l $0044(a3),a0
	move.b $0042(a3),$0009(a0)
	move.b $0034(a3),d0
	move.b d0,$0008(a0)
	cmp.b #$4,d0
	beq.b loc_0_00001160
	move.l $0038(a3),$000A(a0)
	bra.b loc_0_00001172
loc_0_00001160:
	move.l $0038(a3),$000E(a0)
	move.w $0036(a3),$0022(a0)
	move.b $0035(a3),$0024(a0)
loc_0_00001172:
	movea.l (a7)+,a0
	rts
loc_0_00001176:
	move.l a0,-(a7)
	move.l #$84,d0
	bsr.w loc_0_00008160
	movea.l (a7)+,a1
	beq.b loc_0_000011DC
	movea.l a0,a2
	move.l #$83,d0
loc_0_0000118E:
	clr.b (a2)+
	dbf.w d0,loc_0_0000118E
	move.b loc_0_0000002A.l,d0
	move.l a1,(a0)
	beq.b loc_0_000011D2
	movea.l $0004(a1),a2
	move.l a0,$0004(a1)
	move.l a2,$0004(a0)
	beq.b loc_0_000011AE
	move.l a0,(a2)
loc_0_000011AE:
	move.b $0008(a1),d1
	moveq.l #3,d0
	cmp.b #$4,d1
	beq.b loc_0_000011C4
	moveq.l #1,d0
	cmp.b #$2,d1
	beq.b loc_0_000011C4
	move.b d1,d0
loc_0_000011C4:
	move.b d0,$0008(a0)
	move.l $000A(a1),$000A(a0)
	move.b $0024(a1),d0
loc_0_000011D2:
	move.b d0,$0024(a0)
	move.w #$1,$0022(a0)
loc_0_000011DC:
	rts
	dc.b $4C,$D0,$06,$00,$20,$09,$67,$08,$23,$4A,$00,$04,$66,$06,$60,$06
	dc.b $20,$0A,$67,$10,$24,$89,$2F,$00,$61,$00,$00,$4C,$61,$00,$6F,$8E
	dc.b $20,$5F,$72,$01,$4E,$75
loc_0_00001204:
	move.l a0,-(a7)
	movea.l a1,a0
	bsr.w loc_0_00001288
	movea.l (a7),a1
	lea.l $0025(a1),a1
	moveq.l #30,d0
loc_0_00001214:
	move.b (a0)+,(a1)+
	dbeq.w d0,loc_0_00001214
	clr.b -(a1)
	movea.l (a7)+,a0
	movea.l app_0156(a6),a1
	move.l a1,$0012(a0)
	move.l a1,$000E(a0)
	move.l app_015A(a6),$0016(a0)
	move.l app_0580(a6),$001A(a0)
	move.l app_057C(a6),$001E(a0)
	move.b #$4,$0008(a0)
	rts
loc_0_00001244:
	move.l a0,-(a7)
	move.l $0012(a0),-(a7)
	movea.l $001A(a0),a0
	bsr.w loc_0_0000818A
	movea.l (a7)+,a0
	bsr.w loc_0_0000818A
	movea.l (a7)+,a0
	clr.l $0012(a0)
	clr.l $001E(a0)
	move.w #$1,$0022(a0)
	rts
loc_0_0000126A:
	move.l $0012(a0),d0
	beq.b loc_0_00001286
	move.l d0,app_0156(a6)
	move.l $0016(a0),app_015A(a6)
	move.l $001A(a0),app_0580(a6)
	move.l $001E(a0),app_057C(a6)
loc_0_00001286:
	rts
loc_0_00001288:
	movea.l a0,a1
loc_0_0000128A:
	move.b (a1)+,d0
	beq.b loc_0_0000129E
	cmp.b #$3A,d0
	beq.b loc_0_0000129A
	cmp.b #$2F,d0
	bne.b loc_0_0000128A
loc_0_0000129A:
	movea.l a1,a0
	bra.b loc_0_0000128A
loc_0_0000129E:
	rts
	dc.b $B0,$3C,$00,$03,$67,$04,$B0,$3C,$00,$05,$4E,$75,$2F,$0B,$76,$06
	dc.b $41,$FA,$73,$FB,$61,$00,$07,$C8,$61,$00,$47,$08,$66,$66,$12,$1C
	dc.b $67,$62,$61,$00,$58,$A8,$67,$06,$49,$EE,$0A,$D4,$60,$EA,$2E,$02
	dc.b $61,$00,$07,$02,$61,$00,$06,$FE,$72,$3D,$61,$00,$45,$DE,$72,$24
	dc.b $61,$00,$45,$D8,$24,$07,$61,$00,$57,$B2,$72,$12,$61,$00,$57,$6C
	dc.b $22,$07,$61,$00,$57,$E8,$20,$07,$61,$00,$6B,$FE,$67,$10,$2F,$00
	dc.b $72,$12,$61,$00,$57,$56,$20,$1F,$74,$20,$61,$00,$68,$CC,$34,$2B
	dc.b $00,$0A,$76,$04,$61,$00,$44,$58,$61,$00,$2E,$06,$6B,$06,$B2,$3C
	dc.b $00,$20,$67,$8A,$61,$00,$4A,$76,$26,$5F,$4E,$75,$51,$C4,$51,$C7
	dc.b $61,$00,$48,$24,$41,$EB,$00,$16,$10,$FC,$00,$20,$43,$FA,$71,$CC
	dc.b $10,$2B,$00,$34,$B0,$3C,$00,$01,$67,$0E,$43,$FA,$71,$B2,$B0,$3C
	dc.b $00,$03,$67,$04,$43,$FA,$71,$C5,$10,$D9,$66,$FC,$11,$7C,$00,$20
	dc.b $FF,$FF,$42,$10,$50,$C4,$50,$C7,$60,$00,$47,$EC
loc_0_0000136C:
	dc.b $00
loc_0_0000136D:
	dcb.b $43,$00
loc_0_000013B0:
	dc.b $2F,$00,$23,$EF,$00,$04
	dc.l loc_0_00008960
	dc.b $2F,$7C
	dc.l loc_0_000014C8
	dc.b $00,$04,$48,$E7,$FF,$FE,$93,$C9,$2C,$78,$00,$04,$4E,$AE,$FE,$DA
	dc.b $28,$40,$23,$C0
	dc.l loc_0_0000895A
	dc.b $22,$3C
	dc.l loc_0_00001448
	dc.b $E4,$89,$29,$41,$00,$AC,$20,$7A,$75,$70,$29,$68,$00,$98,$00,$98
	dc.b $29,$68,$00,$9C,$00,$9C,$29,$68,$00,$A0,$00,$A0,$43,$EF,$00,$44
	dc.b $29,$49,$00,$B0,$29,$7C
	dc.l loc_0_000014D0
	dc.b $00,$32,$70,$FF,$2F,$0E,$2C,$78,$00,$04,$4E,$AE,$FE,$B6,$2C,$5F
	dc.b $13,$C0
	dc.l loc_0_000088F4
	dc.b $20,$3A,$74,$D6,$E5,$88,$58,$80,$2F,$40,$00,$3C,$20,$40,$20,$F9
	dc.l loc_0_000088FA
	dc.b $30,$B9
	dc.l loc_0_000088FE
	dc.b $4C,$DF,$7F,$FF,$70,$00,$41,$FA,$00,$48,$10,$18,$4E,$75,$00,$00
loc_0_00001448:
	dcb.b $10,$00
loc_0_00001458:
	dcb.b $2C,$00
loc_0_00001484:
	dc.b $00,$00,$00,$00
loc_0_00001488:
	dc.b $00
loc_0_00001489:
	dcb.b $3F,$00
loc_0_000014C8:
	dc.b $50,$F9
	dc.l loc_0_000088F5
loc_0_000014CE:
	dc.b $4A,$FC
loc_0_000014D0:
	dc.b $23,$C0
	dc.l loc_0_00008916
	dc.b $20,$1F,$B0,$3C,$00,$09,$66,$14,$0C,$AF
	dc.l loc_0_000014C8
	dc.b $00,$02,$66,$0A,$20,$3A,$74,$2C,$08,$97,$00,$07,$4E,$73,$B0,$BC
	dc.b $00,$00,$00,$04,$66,$34,$0C,$AF
	dc.l loc_0_0000173C
	dc.b $00,$02,$67,$0E,$0C,$AF
	dc.l loc_0_000014CE
	dc.b $00,$02,$66,$20,$70,$1D,$60,$1C,$4A,$39
	dc.l loc_0_00008906
	dc.b $67,$04,$F3,$7A,$74,$7A,$20,$3A,$73,$F6,$3E,$BA,$73,$EC,$2F,$7A
	dc.b $73,$E4,$00,$02,$4E,$73,$23,$C0
	dc.l loc_0_00008908
	dc.b $4E,$F9
loc_0_00001536:
	dc.l loc_0_0000153A
loc_0_0000153A:
	dc.b $B0,$BC,$00,$00,$00,$03,$6E,$38,$66,$34,$08,$2F,$00,$00,$00,$0D
	dc.b $66,$2C,$30,$2F,$00,$06,$2F,$08,$20,$6F,$00,$0E,$54,$88,$B0,$60
	dc.b $67,$14,$B0,$60,$67,$10,$B0,$60,$67,$0C,$B0,$60,$67,$08,$B0,$60
	dc.b $67,$04,$20,$6F,$00,$0E,$2F,$48,$00,$0E,$20,$5F,$70,$03,$50,$8F
	dc.b $33,$D7
	dc.l loc_0_00008910
	dc.b $08,$97,$00,$07,$23,$EF,$00,$02
	dc.l loc_0_0000890C
	dc.b $23,$CF
	dc.l loc_0_00008912
	dc.b $2F,$7C
	dc.l loc_0_000016CC
	dc.b $00,$02,$4E,$73
loc_0_0000159C:
	dc.b $33,$DF
	dc.l loc_0_00008910
	dc.b $23,$DF
	dc.l loc_0_0000890C
	dc.b $B0,$BC,$00,$00,$00,$09,$4C,$9F,$00,$01
loc_0_000015B2:
	dc.b $67,$00,$01,$12,$02,$40,$F0,$00,$67,$3C,$B0,$7C,$10,$00,$67,$36
	dc.b $B0,$7C,$20,$00,$67,$2A,$B0,$7C,$80,$00,$67,$18,$B0,$7C,$90,$00
	dc.b $67,$1E,$B0,$7C,$A0,$00,$67,$12,$B0,$7C,$B0,$00,$66,$18,$4F,$EF
	dc.b $00,$54,$60,$12,$4F,$EF,$00,$32,$60,$0C,$4F,$EF,$00,$18,$60,$06
	dc.b $23,$DF
	dc.l loc_0_0000890C
	dc.b $2F,$08,$4A,$39
	dc.l loc_0_00008906
	dc.b $67,$32,$41,$FA,$73,$92,$F3,$28,$00,$00,$4A,$28,$00,$00,$67,$24
	dc.b $70,$00,$10,$28,$00,$01,$B0,$3C,$00,$18,$67,$06,$B0,$3C,$00,$38
	dc.b $66,$06,$08,$F0,$00,$03,$00,$00,$F2,$28,$F0,$FF,$00,$E4,$F2,$28
	dc.b $BC,$00,$00,$D8,$2F,$01,$20,$78,$00,$04,$32,$28,$01,$28,$41,$FA
	dc.b $73,$24,$4E,$7A,$00,$00,$10,$C0,$4E,$7A,$00,$01,$10,$C0,$4E,$7A
	dc.b $08,$01,$20,$C0,$08,$01,$00,$01,$67,$48,$4E,$7A,$08,$03,$20,$C0
	dc.b $4E,$7A,$08,$04,$20,$C0,$4E,$7A,$08,$02,$20,$C0,$08,$01,$00,$03
	dc.b $66,$30,$4E,$7A,$00,$02,$30,$C0,$08,$01,$00,$02,$67,$24,$F0,$10
	dc.b $62,$00,$F0,$28,$42,$00,$00,$02,$F0,$28,$0A,$00,$00,$06,$F0,$28
	dc.b $0E,$00,$00,$0A,$F0,$28,$4E,$00,$00,$0E,$F0,$28,$4A,$00,$00,$16
	dc.b $4E,$71,$4C,$DF,$01,$02,$3F,$3C,$00,$10,$2F,$3C
	dc.l loc_0_000016CC
	dc.b $30,$3A,$72,$5E,$08,$80,$00,$0F,$3F,$00,$20,$0F,$50,$80,$23,$C0
	dc.l loc_0_00008912
	dc.b $4E,$73,$58,$8F,$60,$00,$FF,$2E
loc_0_000016CC:
	dc.b $48,$F9,$FF,$FE
	dc.l loc_0_0000891A
	dc.b $0C,$B9,$00,$00,$00,$1D
	dc.l loc_0_00008908
	dc.b $66,$08,$23,$FA,$72,$7E
	dc.l loc_0_0000890C
	dc.b $22,$7A,$72,$6C,$70,$00,$12,$3A,$72,$6E,$03,$C0,$2F,$0E,$2C,$78
	dc.b $00,$04,$4E,$AE,$FE,$BC,$2C,$5F,$0C,$B9,$00,$00,$00,$1D
	dc.l loc_0_00008908
	dc.b $67,$2A,$70,$00,$12,$3A,$71,$E4,$03,$C0,$2F,$0E,$2C,$78,$00,$04
	dc.b $4E,$AE,$FE,$C2,$2C,$5F,$70,$00,$72,$00,$14,$3A,$71,$CE,$05,$C1
	dc.b $2F,$0E,$2C,$78,$00,$04,$4E,$AE,$FE,$CE,$2C,$5F,$4C,$FA,$FF,$FF
	dc.b $71,$DC
loc_0_0000173C:
	dc.b $4A,$FC
loc_0_0000173E:
	dc.b $10,$02,$0F,$03,$0A,$04,$03,$05,$04,$06,$05,$07,$06,$08,$07,$09
	dc.b $1F,$0A,$20,$0B,$33,$0D,$34,$0E,$08,$18,$1D,$1D,$2C,$30,$2D,$31
	dc.b $2E,$32,$2F,$33,$30,$34,$31,$35,$32,$36,$35,$38,$00,$00
loc_0_0000176C:
	movem.l loc_0_00008916(pc),d0-d7/a0-a5
	movem.l d0-d7/a0-a5,app_0010(a6)
	movem.l loc_0_0000894E(pc),d0-d1
	movem.l d0-d1,app_0048(a6)
	movea.l loc_0_0000890C(pc),a1
	move.l a1,$0054(a6)
	move.l loc_0_00008912(pc),app_0050(a6)
	move.w loc_0_00008910.l,app_005A(a6)
	move.l loc_0_00008908(pc),d1
	st.b app_0134(a6)
	cmp.b #$4,d1
	beq.w loc_0_00001864
	cmp.b #$9,d1
	beq.w loc_0_00001812
	cmp.b #$1D,d1
	bne.b loc_0_000017C2
	sf.b app_0134(a6)
	clr.b loc_0_000088F5.l
loc_0_000017C2:
	lea.l loc_0_0000173E(pc),a0
	moveq.l #0,d0
loc_0_000017C8:
	move.b (a0)+,d0
	beq.b loc_0_000017D4
	cmp.b (a0)+,d1
	bne.b loc_0_000017C8
	move.l d0,d1
	bra.b loc_0_000017D6
loc_0_000017D4:
	moveq.l #30,d1
loc_0_000017D6:
	clr.l app_03D8(a6)
	clr.b app_014A(a6)
	move.l app_00DE(a6),-(a7)
	move.w d1,-(a7)
	bsr.w loc_0_00000DE6
	bsr.w loc_0_00005E6E
	bsr.w loc_0_00005EDE
	bsr.w loc_0_0000052A
	move.w (a7)+,d1
	cmp.w #$1D,d1
	bne.b loc_0_00001804
	tst.b app_0162(a6)
	bne.w loc_0_00004462
loc_0_00001804:
	bsr.w loc_0_00006A5A
	st.b app_00E5(a6)
	move.l (a7)+,app_00DE(a6)
	rts
loc_0_00001812:
	bsr.w loc_0_00003F70
	moveq.l #7,d1
	tst.l app_03D8(a6)
	bne.w loc_0_00001836
loc_0_00001820:
	move.b app_014A(a6),d0
	beq.b loc_0_000017D6
	bra.b loc_0_0000182C
loc_0_00001828:
	moveq.l #11,d1
	bra.b loc_0_000017D6
loc_0_0000182C:
	subq.l #1,app_0194(a6)
	beq.b loc_0_00001828
	bra.w loc_0_0000193C
loc_0_00001836:
	moveq.l #0,d3
	movea.l app_03D8(a6),a0
	clr.l app_03D8(a6)
	movea.l (a0),a1
	move.w #$4AFC,(a1)
	move.w app_005A(a6),d0
	andi.w #32767,d0
	or.w app_03DC(a6),d0
	move.w d0,app_005A(a6)
	bpl.w loc_0_00001926
	tst.b app_014A(a6)
	beq.w loc_0_000017D6
	bra.b loc_0_00001820
loc_0_00001864:
	pea.l app_055E(a6)
	cmpa.l (a7)+,a1
	beq.b loc_0_000018DA
	cmpa.l app_0564(a6),a1
	beq.b loc_0_000018EE
	st.b app_0567(a6)
	bsr.w loc_0_00003E3C
	bne.b loc_0_000018D4
	movem.l a0-a1,-(a7)
	bsr.w loc_0_00003F70
	movem.l (a7)+,a0-a1
	move.w $0006(a0),d0
	cmp.w #$3,d0
	beq.b loc_0_000018CE
	cmp.w #$1,d0
	beq.b loc_0_000018C0
	cmp.w #$2,d0
	beq.b loc_0_000018BA
	lea.l $000C(a0),a4
	movem.l a0-a1,-(a7)
	bsr.w loc_0_00006B70
	movem.l (a7)+,a0-a1
	bne.b loc_0_000018EA
	tst.b d1
	bne.b loc_0_000018EA
	tst.l d2
	beq.b loc_0_000018EA
	bra.b loc_0_000018C6
loc_0_000018BA:
	addq.l #1,$0008(a0)
	bra.b loc_0_000018EA
loc_0_000018C0:
	subq.l #1,$0008(a0)
	bne.b loc_0_000018EA
loc_0_000018C6:
	move.w $0004(a0),(a1)
	clr.w $0006(a0)
loc_0_000018CE:
	moveq.l #11,d1
	bra.w loc_0_000017D6
loc_0_000018D4:
	moveq.l #10,d1
	bra.w loc_0_000017D6
loc_0_000018DA:
	move.l app_0560(a6),$0054(a6)
	bsr.w loc_0_00003F70
	moveq.l #7,d1
	bra.w loc_0_000017D6
loc_0_000018EA:
	moveq.l #0,d3
	bra.b loc_0_0000190A
loc_0_000018EE:
	move.w app_0568(a6),(a1)
	moveq.l #-42,d0
	move.l d0,app_0564(a6)
	movea.l app_056C(a6),a0
	movea.l $0000(a0),a1
	move.w #$4AFC,(a1)
	bsr.w loc_0_00003F70
	st.b d3
loc_0_0000190A:
	btst.b #0,app_0057(a6)
	bne.b loc_0_00001926
	movea.l $0054(a6),a2
	bsr.w loc_0_0000736A
	bne.b loc_0_00001926
	movea.l a2,a1
	bsr.w loc_0_00003E3C
	beq.w loc_0_0000199E
loc_0_00001926:
	tst.b d3
	beq.b loc_0_0000193C
	move.l a3,-(a7)
	bsr.w loc_0_0000052A
	moveq.l #37,d1
	bsr.w loc_0_00006A5A
	st.b app_00E5(a6)
	movea.l (a7)+,a3
loc_0_0000193C:
	movem.l app_0010(a6),d0-d7/a0-a5
	movem.l d0-d7/a0-a5,loc_0_00008916.l
	movem.l app_0048(a6),d0-d1
	movem.l d0-d1,loc_0_0000894E.l
	move.l $0054(a6),loc_0_0000890C.l
	move.w app_005A(a6),loc_0_00008910.l
	moveq.l #0,d0
	moveq.l #0,d1
	move.b loc_0_0000895E(pc),d2
	bset d2,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSetSignal(a6)
	movea.l (a7)+,a6
	movea.l loc_0_0000895A(pc),a1
	moveq.l #0,d0
	move.b loc_0_000088F4(pc),d1
	bset d1,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSignal(a6)
	movea.l (a7)+,a6
	move.b #$1,app_0134(a6)
	rts
loc_0_0000199E:
	move.w app_005A(a6),d0
	andi.w #32768,d0
	move.w d0,app_03DC(a6)
	move.l a0,app_03D8(a6)
	move.w $0004(a0),(a1)
	bset.b #7,app_005A(a6)
	bra.w loc_0_00001926
loc_0_000019BC:
	dc.b $4E,$7A,$10,$02,$2F,$01,$08,$81,$00,$00,$82,$00,$4E,$7B,$10,$02
	dc.b $20,$1F,$4E,$73
loc_0_000019D0:
	pea.l loc_0_000019D4(pc)
loc_0_000019D4:
	move.w #$4,$000A(a3)
	move.w app_00D8(a6),d0
	add.w d0,$000C(a3)
	rts
	dc.b $2F,$0B,$2F,$08,$76,$04,$61,$52,$20,$5F,$61,$00,$50,$7A,$37,$7C
	dc.b $00,$04,$00,$0A,$30,$2E,$00,$D8,$D1,$6B,$00,$0C,$49,$EE,$0A,$D4
	dc.b $42,$14,$78,$00,$61,$00,$3F,$B8,$66,$26,$4A,$14,$67,$22,$61,$00
	dc.b $51,$5C,$66,$04,$4A,$01,$67,$0A,$61,$00,$44,$36,$49,$EE,$0A,$D4
	dc.b $60,$E2,$2F,$02,$61,$00,$43,$72,$24,$1F,$26,$5F,$70,$00,$4E,$75
	dc.b $61,$00,$43,$66,$26,$5F,$74,$FF,$4E,$75
loc_0_00001A3E:
	moveq.l #8,d2
	add.w app_00E2(a6),d2
	lea.l loc_0_00008524(pc),a2
loc_0_00001A48:
	movem.w app_086E(a6),d0-d1/d4
	add.w app_086A(a6),d0
	add.w app_086A(a6),d0
	sub.w d2,d0
	lsr.w #1,d0
	sub.w d3,d1
	mulu.w app_00D8(a6),d1
	lea.l app_078A(a6),a3
	clr.b $003C(a3)
	bsr.w loc_0_00005B1E
	sf.b $0014(a3)
	move.w #$4,$000A(a3)
	move.w app_00D8(a6),$000C(a3)
	rts
loc_0_00001A7E:
	move.l a0,-(a7)
	bsr.b loc_0_00001A3E
	movea.l (a7)+,a0
	bsr.w loc_0_00006A6A
	bsr.w loc_0_000019D4
	lea.l app_0AD4(a6),a4
	clr.b (a4)
	moveq.l #0,d4
	rts
loc_0_00001A96:
	move.l a1,-(a7)
	move.l a0,-(a7)
	movem.w app_086E(a6),d0-d1/d4
	moveq.l #30,d2
	moveq.l #5,d3
	lea.l loc_0_00008568(pc),a2
	bsr.b loc_0_00001A48
	movea.l (a7)+,a0
	bsr.b loc_0_00001ABA
	move.w app_00D8(a6),d0
	add.w d0,d0
	add.w d0,$000C(a3)
	movea.l (a7)+,a0
loc_0_00001ABA:
	move.l a0,-(a7)
	movea.l a0,a1
loc_0_00001ABE:
	tst.b (a0)+
	bne.b loc_0_00001ABE
	lea.l $001E(a1),a1
	suba.l a0,a1
	move.w a1,d0
	lsr.w #1,d0
	move.w d0,$000A(a3)
	movea.l (a7)+,a0
	bra.w loc_0_00006A6A
loc_0_00001AD6:
	move.l a3,-(a7)
	lea.l loc_0_0000855F(pc),a1
	bsr.b loc_0_00001A96
loc_0_00001ADE:
	bsr.w loc_0_00004120
	bmi.b loc_0_00001ADE
	cmp.b #$1B,d1
	beq.b loc_0_00001AF0
	cmp.b #$A,d1
	bne.b loc_0_00001ADE
loc_0_00001AF0:
	bsr.w loc_0_00005D9C
	movea.l (a7)+,a3
	rts
loc_0_00001AF8:
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
loc_0_00001B04:
	move.l a4,-(a7)
	lea.l loc_0_000087FA(pc),a4
	moveq.l #0,d1
	move.w d0,d1
	lea.l loc_0_00001B24(pc),a2
	bsr.w loc_0_00006AE0
	clr.b (a4)+
	movea.l (a7)+,a4
	bsr.w loc_0_00005E6E
	lea.l loc_0_000087EB(pc),a0
	bra.b loc_0_00001AD6
loc_0_00001B24:
	move.b d1,(a4)+
	rts
	dc.b $43,$FA,$6B,$0F,$61,$00,$FF,$68,$61,$00,$25,$EE,$6B,$FA,$02,$01
	dc.b $00,$DF,$B2,$3C,$00,$59,$67,$0A,$B2,$3C,$00,$4E,$67,$04,$B2,$3C
	dc.b $00,$1B,$3F,$01,$61,$00,$42,$4E,$32,$1F,$B2,$3C,$00,$59,$4E,$75
	dc.b $4A,$81,$6A,$44,$44,$81,$18,$FC,$00,$2D,$60,$3C,$4A,$01,$6A,$06
	dc.b $18,$FC,$00,$2D,$44,$01,$02,$81,$00,$00,$00,$FF,$60,$2A,$4A,$41
	dc.b $6A,$06,$18,$FC,$00,$2D,$44,$41,$02,$81,$00,$00,$FF,$FF,$60,$18
	dc.b $20,$01,$61,$00,$63,$EE,$67,$10,$4A,$2E,$05,$92,$67,$00,$60,$5A
	dc.b $18,$FC,$00,$7B,$60,$00,$60,$52,$B2,$BC,$00,$00,$00,$0A,$64,$12
	dc.b $06,$01,$00,$30,$18,$C1,$4E,$75,$2F,$02,$50,$C2,$48,$41,$70,$03
	dc.b $60,$0A,$18,$FC,$00,$24,$2F,$02,$74,$00,$70,$07,$E9,$99,$3F,$01
	dc.b $02,$01,$00,$0F,$66,$04,$4A,$02,$67,$10,$50,$C2,$B2,$3C,$00,$09
	dc.b $6F,$02,$5E,$01,$06,$01,$00,$30,$18,$C1,$32,$1F,$51,$C8,$FF,$DE
	dc.b $24,$1F,$4E,$75,$41,$FA,$00,$18,$E3,$99,$18,$F0,$10,$00,$10,$30
	dc.b $10,$01,$67,$02,$18,$C0,$E2,$99,$18,$FC,$00,$20,$4E,$75,$74,$00
	dc.b $66,$00,$68,$69,$6C,$73,$63,$63,$63,$73,$6E,$65,$65,$71,$76,$63
	dc.b $76,$73,$70,$6C,$6D,$69,$67,$65,$6C,$74,$67,$74,$6C,$65,$41,$FA
	dc.b $00,$12,$48,$85,$18,$FC,$00,$2E,$18,$F0,$50,$00,$18,$FC,$00,$20
	dc.b $4E,$75,$62,$77,$6C,$3F,$64,$00,$41,$FA,$00,$1A,$48,$81,$E5,$99
	dc.b $18,$F0,$10,$00,$18,$F0,$10,$01,$18,$F0,$10,$02,$18,$FC,$00,$20
	dc.b $E4,$99,$4E,$75,$74,$73,$74,$20,$63,$68,$67,$20,$63,$6C,$72,$20
	dc.b $73,$65,$74,$20,$02,$01,$00,$07,$06,$01,$00,$30,$18,$C1,$4E,$75
loc_0_00001C78:
	move.w (a5)+,d7
	clr.b app_014C(a6)
	lea.l loc_0_0000379C(pc),a0
	clr.l d0
loc_0_00001C84:
	addq.l #1,d0
	move.w d7,d2
	and.w (a0)+,d2
	cmp.w (a0)+,d2
	bne.b loc_0_00001C84
	moveq.l #0,d1
	lea.l loc_0_00003934(pc),a0
loc_0_00001C94:
	move.b (a0)+,d1
	subq.b #1,d0
	beq.b loc_0_00001C9E
	adda.l d1,a0
	bra.b loc_0_00001C94
loc_0_00001C9E:
	move.b (a0)+,d2
	lea.l app_09A8(a6),a4
	subq.b #2,d1
	bcs.b loc_0_00001CAE
loc_0_00001CA8:
	move.b (a0)+,(a4)+
	dbf.w d1,loc_0_00001CA8
loc_0_00001CAE:
	move.b d2,d6
	bsr.b loc_0_00001CD4
	move.b #$A,(a4)+
	clr.l d0
	rts
loc_0_00001CBA:
	ext.w d0
	add.w d0,d0
	move.w $0(a0,d0.w),d0
	jmp $0(a0,d0.w)
	dc.b $42,$80,$10,$18,$53,$00,$18,$D8,$51,$C8,$FF,$FC,$4E,$75
loc_0_00001CD4:
	lea.l loc_0_00001CE6(pc),a0
	move.b d6,d0
	move.w d7,d5
	andi.w #192,d5
	lsr.w #6,d5
	bsr.b loc_0_00001CBA
	rts
loc_0_00001CE6:
	dc.b $FF,$FE,$14,$E8,$00,$72,$00,$CC,$01,$20,$01,$4A,$01,$6E,$01,$DE
	dc.b $01,$E4,$01,$F0,$02,$00,$02,$10,$02,$2A,$02,$58,$02,$68,$02,$78
	dc.b $03,$40,$03,$7A,$03,$A8,$03,$C4,$03,$F2,$04,$06,$04,$2A,$04,$8E
	dc.b $05,$06,$05,$1E,$14,$E8,$14,$E8,$05,$7A,$05,$BA,$06,$5A,$06,$4A
	dc.b $06,$EC,$07,$6C,$07,$72,$08,$D4,$09,$2E,$01,$E4,$09,$36,$09,$46
	dc.b $09,$58,$13,$44,$13,$B0,$14,$04,$14,$14,$14,$42,$14,$58,$14,$68
	dc.b $14,$7A,$14,$8C,$0B,$5A,$09,$F2,$0A,$56,$09,$E2,$10,$B0,$07,$E4
	dc.b $08,$54,$61,$00,$FE,$CC,$18,$FC,$00,$23,$4A,$05,$66,$08,$32,$1D
	dc.b $61,$00,$FE,$06,$60,$14,$BA,$3C,$00,$01,$67,$08,$22,$1D,$61,$00
	dc.b $FE,$12,$60,$06,$32,$1D,$61,$00,$FE,$02,$18,$FC,$00,$2C,$10,$07
	dc.b $02,$00,$00,$3F,$B0,$3C,$00,$3C,$66,$1C,$4A,$05,$66,$0C,$41,$FA
	dc.b $00,$06,$60,$00,$FF,$2C,$03,$63,$63,$72,$41,$FA,$00,$06,$60,$00
	dc.b $FF,$20,$02,$73,$72,$00,$78,$3D,$60,$00,$14,$20,$70,$6C,$08,$07
	dc.b $00,$06,$66,$02,$70,$77,$18,$C0,$18,$FC,$00,$20,$14,$07,$36,$07
	dc.b $E0,$4B,$E2,$4B,$41,$FA,$00,$16,$43,$FA,$00,$2C,$08,$07,$00,$07
	dc.b $67,$02,$C3,$48,$4E,$90,$18,$FC,$00,$2C,$4E,$D1,$32,$1D,$61,$00
	dc.b $FD,$90,$18,$FC,$00,$28,$18,$FC,$00,$61,$12,$02,$61,$00,$FE,$78
	dc.b $18,$FC,$00,$29,$4E,$75,$18,$FC,$00,$64,$12,$03,$60,$00,$FE,$68
	dc.b $12,$05,$61,$00,$FE,$36,$42,$05,$18,$FC,$00,$64,$32,$07,$E0,$49
	dc.b $E2,$49,$61,$00,$FE,$52,$18,$FC,$00,$2C,$78,$3D,$30,$07,$02,$00
	dc.b $00,$C0,$66,$02,$78,$FD,$60,$00,$13,$A2,$12,$05,$61,$00,$FE,$0C
	dc.b $42,$05,$18,$FC,$00,$23,$32,$1D,$61,$00,$FD,$2E,$18,$FC,$00,$2C
	dc.b $78,$3D,$30,$07,$02,$00,$00,$C0,$66,$DC,$78,$7D,$60,$D8,$3A,$07
	dc.b $70,$0C,$E0,$6D,$02,$45,$00,$03,$1A,$3B,$50,$60,$3F,$07,$78,$FF
	dc.b $61,$00,$13,$68,$3E,$1F,$10,$2E,$01,$4B,$2D,$6E,$01,$4E,$01,$52
	dc.b $51,$EE,$01,$4B,$3F,$00,$18,$FC,$00,$2C,$32,$07,$10,$3C,$00,$09
	dc.b $E0,$69,$02,$41,$00,$07,$34,$07,$EC,$4A,$02,$42,$00,$07,$78,$3F
	dc.b $61,$00,$13,$4A,$30,$1F,$4A,$2E,$01,$4B,$67,$18,$4A,$00,$67,$18
	dc.b $50,$EE,$01,$4C,$4C,$EE,$00,$03,$01,$4E,$C1,$41,$48,$EE,$00,$03
	dc.b $01,$4E,$4E,$75,$1D,$40,$01,$4B,$4E,$75,$03,$00,$02,$01,$32,$1D
	dc.b $60,$00,$FC,$B8,$02,$07,$00,$07,$06,$07,$00,$30,$18,$C7,$4E,$75
	dc.b $61,$F2,$18,$FC,$00,$2C,$18,$FC,$00,$23,$32,$1D,$60,$00,$FC,$92
	dc.b $61,$E2,$41,$FA,$00,$06,$60,$00,$FD,$D8,$04,$2C,$75,$73,$70,$20
	dc.b $02,$47,$00,$0F,$BE,$3C,$00,$0A,$65,$08,$18,$FC,$00,$31,$04,$07
	dc.b $00,$0A,$06,$07,$00,$30,$18,$C7,$4E,$75,$10,$24,$B0,$3C,$00,$2E
	dc.b $67,$08,$52,$8C,$61,$00,$FD,$0A,$60,$02,$7A,$02,$10,$2E,$09,$A8
	dc.b $78,$64,$B0,$3C,$00,$6A,$67,$00,$12,$A2,$B0,$3C,$00,$70,$67,$00
	dc.b $12,$9A,$78,$3D,$60,$00,$12,$94,$7A,$01,$78,$FD,$61,$00,$12,$8C
	dc.b $18,$FC,$00,$2C,$60,$00,$FE,$48,$7A,$01,$78,$FD,$61,$00,$12,$7C
	dc.b $18,$FC,$00,$2C,$60,$00,$FE,$44,$1A,$07,$EC,$0D,$02,$05,$00,$01
	dc.b $52,$05,$61,$00,$FC,$BC,$3F,$1D,$78,$6C,$61,$00,$12,$5E,$1D,$7C
	dc.b $00,$03,$01,$4D,$3C,$1F,$18,$FC,$00,$2C,$70,$0F,$E3,$56,$E2,$51
	dc.b $51,$C8,$FF,$FA,$36,$01,$E0,$5B,$18,$3C,$00,$64,$61,$12,$4A,$03
	dc.b $67,$08,$4A,$01,$67,$04,$18,$FC,$00,$2F,$36,$01,$18,$3C,$00,$61
	dc.b $4A,$03,$67,$40,$70,$07,$01,$03,$67,$6E,$18,$C4,$B8,$3C,$00,$66
	dc.b $66,$04,$18,$FC,$00,$70,$7C,$37,$9C,$00,$18,$C6,$4A,$00,$67,$24
	dc.b $53,$00,$01,$03,$67,$4E,$4A,$00,$66,$1C,$18,$FC,$00,$2D,$4A,$2E
	dc.b $05,$91,$67,$0C,$18,$C4,$B8,$3C,$00,$66,$66,$04,$18,$FC,$00,$70
	dc.b $18,$FC,$00,$37,$4E,$75,$53,$00,$01,$03,$66,$22,$18,$FC,$00,$2D
	dc.b $4A,$2E,$05,$91,$67,$0C,$18,$C4,$B8,$3C,$00,$66,$66,$04,$18,$FC
	dc.b $00,$70,$7C,$36,$9C,$00,$18,$C6,$18,$FC,$00,$2F,$60,$0A,$4A,$00
	dc.b $67,$B8,$60,$D2,$18,$FC,$00,$2F,$53,$00,$64,$8A,$53,$8C,$4E,$75
	dc.b $1A,$07,$EC,$0D,$02,$05,$00,$01,$52,$05,$61,$00,$FB,$F4,$3C,$1D
	dc.b $34,$07,$02,$02,$00,$38,$B4,$3C,$00,$20,$66,$18,$32,$06,$61,$00
	dc.b $FF,$44,$18,$FC,$00,$2C,$78,$34,$61,$00,$11,$80,$1D,$7C,$00,$03
	dc.b $01,$4D,$4E,$75,$61,$00,$FF,$24,$60,$E8,$7A,$01,$08,$07,$00,$07
	dc.b $66,$02,$7A,$02,$61,$00,$FB,$BA,$7A,$01,$78,$FD,$61,$00,$11,$5C
	dc.b $E2,$4F,$E0,$4F,$02,$07,$00,$07,$06,$07,$00,$30,$18,$FC,$00,$2C
	dc.b $18,$FC,$00,$64,$18,$C7,$4E,$75,$7A,$02,$78,$64,$61,$00,$11,$3C
	dc.b $10,$3C,$00,$09,$32,$07,$E0,$69,$18,$FC,$00,$2C,$18,$FC,$00,$61
	dc.b $60,$00,$FB,$C4,$32,$07,$E0,$49,$02,$01,$00,$0F,$61,$00,$FB,$38
	dc.b $18,$FC,$00,$64,$02,$07,$00,$07,$06,$07,$00,$30,$18,$C7,$18,$FC
	dc.b $00,$2C,$22,$0D,$34,$1D,$48,$C2,$D2,$82,$D2,$AE,$00,$04,$60,$00
	dc.b $FA,$B2,$32,$07,$E0,$49,$02,$41,$00,$0F,$61,$00,$FB,$0A,$42,$05
	dc.b $78,$3D,$60,$00,$10,$E6,$61,$00,$FB,$38,$18,$FC,$00,$23,$32,$07
	dc.b $E0,$49,$E2,$49,$02,$41,$00,$07,$66,$02,$72,$08,$61,$00,$FB,$6C
	dc.b $18,$FC,$00,$2C,$78,$3F,$60,$00,$10,$C2,$30,$07,$02,$40,$00,$F8
	dc.b $14,$07,$32,$07,$E0,$49,$E2,$49,$B0,$3C,$00,$40,$67,$16,$B0,$3C
	dc.b $00,$48,$67,$26,$B0,$3C,$00,$88,$67,$32,$18,$FC,$00,$3F,$18,$FC
	dc.b $00,$3F,$4E,$75,$18,$FC,$00,$64,$61,$00,$FB,$2C,$18,$FC,$00,$2C
	dc.b $18,$FC,$00,$64,$12,$02,$60,$00,$FB,$1E,$18,$FC,$00,$61,$61,$00
	dc.b $FB,$16,$18,$FC,$00,$2C,$18,$FC,$00,$61,$60,$E8,$18,$FC,$00,$64
	dc.b $61,$00,$FB,$04,$18,$FC,$00,$2C,$18,$FC,$00,$61,$60,$D6,$32,$07
	dc.b $E0,$49,$02,$01,$00,$0F,$67,$0C,$B2,$3C,$00,$01,$67,$10,$61,$00
	dc.b $FA,$66,$60,$12,$53,$8C,$28,$FC,$62,$72,$61,$20,$60,$08,$53,$8C
	dc.b $28,$FC,$62,$73,$72,$20,$12,$07,$67,$44,$B2,$3C,$00,$FF,$66,$16
	dc.b $19,$7C,$00,$2E,$FF,$FF,$18,$FC,$00,$6C,$18,$FC,$00,$20,$22,$15
	dc.b $D2,$8D,$58,$4D,$60,$14,$19,$7C,$00,$2E,$FF,$FF,$18,$FC,$00,$73
	dc.b $18,$FC,$00,$20,$48,$81,$48,$C1,$D2,$8D,$D2,$AE,$00,$04,$61,$00
	dc.b $F9,$B2,$4A,$2E,$05,$92,$67,$04,$18,$FC,$00,$7D,$4E,$75,$32,$1D
	dc.b $48,$C1,$55,$81,$60,$E2,$12,$07,$61,$00,$F9,$74,$18,$FC,$00,$2C
	dc.b $18,$FC,$00,$64,$32,$07,$E0,$49,$E2,$49,$60,$00,$FA,$6A,$70,$FF
	dc.b $0C,$34,$00,$78,$00,$00,$66,$04,$61,$00,$FA,$16,$12,$07,$34,$07
	dc.b $E0,$4A,$E2,$4A,$08,$07,$00,$03,$67,$24,$18,$FC,$00,$2D,$18,$FC
	dc.b $00,$28,$18,$FC,$00,$61,$61,$00,$FA,$3E,$41,$FA,$00,$28,$61,$00
	dc.b $FA,$90,$12,$02,$61,$00,$FA,$30,$18,$FC,$00,$29,$4E,$75,$18,$FC
	dc.b $00,$64,$61,$00,$FA,$22,$18,$FC,$00,$2C,$18,$FC,$00,$64,$12,$02
	dc.b $60,$00,$FA,$14,$05,$29,$2C,$2D,$28,$61,$61,$00,$F9,$C4,$BA,$3C
	dc.b $00,$03,$66,$06,$49,$EE,$09,$A8,$60,$30,$32,$07,$18,$FC,$00,$28
	dc.b $18,$FC,$00,$61,$61,$00,$F9,$F0,$41,$FA,$00,$1A,$61,$00,$FA,$42
	dc.b $32,$07,$E0,$49,$E2,$49,$61,$00,$F9,$DE,$18,$FC,$00,$29,$18,$FC
	dc.b $00,$2B,$4E,$75,$05,$29,$2B,$2C,$28,$61,$41,$FA,$00,$10,$3A,$07
	dc.b $EC,$4D,$02,$05,$00,$07,$10,$05,$60,$00,$FA,$0A,$00,$3A,$00,$3A
	dc.b $00,$3A,$00,$10,$00,$5A,$00,$5A,$00,$5A,$00,$10,$E4,$0D,$02,$05
	dc.b $00,$01,$52,$05,$28,$FC,$63,$6D,$70,$61,$61,$00,$F9,$54,$78,$FF
	dc.b $61,$00,$0E,$F8,$18,$FC,$00,$2C,$18,$FC,$00,$61,$32,$07,$E2,$49
	dc.b $E0,$49,$60,$00,$F9,$82,$41,$FA,$00,$1A,$61,$00,$F9,$D4,$61,$00
	dc.b $F9,$30,$78,$FF,$61,$00,$0E,$D4,$18,$FC,$00,$2C,$18,$FC,$00,$64
	dc.b $60,$DA,$03,$63,$6D,$70,$02,$05,$00,$03,$41,$FA,$00,$1A,$61,$00
	dc.b $F9,$B0,$61,$00,$F9,$0C,$18,$FC,$00,$64,$61,$C0,$18,$FC,$00,$2C
	dc.b $78,$3D,$60,$00,$0E,$A6,$03,$65,$6F,$72,$61,$00,$F8,$F4,$30,$07
	dc.b $02,$40,$01,$00,$66,$54,$78,$FD,$60,$3A,$30,$07,$02,$40,$F1,$F8
	dc.b $B0,$7C,$C1,$40,$67,$0C,$B0,$7C,$C1,$48,$67,$06,$B0,$7C,$C1,$88
	dc.b $66,$0E,$49,$EE,$09,$A8,$28,$FC,$65,$78,$67,$20,$60,$00,$FD,$AC
	dc.b $BA,$3C,$00,$03,$67,$40,$61,$00,$F8,$B8,$30,$07,$02,$40,$01,$00
	dc.b $66,$18,$78,$FF,$61,$00,$0E,$54,$18,$FC,$00,$2C,$18,$FC,$00,$64
	dc.b $32,$07,$E2,$49,$E0,$49,$60,$00,$F8,$DE,$18,$FC,$00,$64,$32,$07
	dc.b $E2,$49,$E0,$49,$61,$00,$F8,$D0,$18,$FC,$00,$2C,$30,$07,$38,$3C
	dc.b $00,$3C,$60,$00,$0E,$26,$3A,$07,$E0,$4D,$02,$05,$00,$01,$52,$05
	dc.b $61,$00,$F8,$6E,$78,$FF,$61,$00,$0E,$12,$18,$FC,$00,$2C,$18,$FC
	dc.b $00,$61,$32,$07,$E2,$49,$E0,$49,$60,$00,$F8,$9C,$32,$07,$BA,$3C
	dc.b $00,$03,$67,$3C,$E4,$09,$61,$48,$61,$00,$F8,$46,$32,$07,$E0,$49
	dc.b $E2,$49,$08,$07,$00,$05,$66,$1E,$18,$FC,$00,$23,$02,$41,$00,$07
	dc.b $66,$02,$72,$08,$61,$00,$F8,$74,$18,$FC,$00,$2C,$18,$FC,$00,$64
	dc.b $12,$07,$60,$00,$F8,$62,$18,$FC,$00,$64,$02,$01,$00,$07,$60,$E4
	dc.b $E0,$49,$61,$0C,$18,$FC,$00,$20,$7A,$02,$78,$3C,$60,$00,$0D,$AC
	dc.b $02,$41,$00,$06,$41,$FB,$10,$1E,$18,$D8,$18,$D0,$B2,$3C,$00,$04
	dc.b $66,$04,$18,$FC,$00,$78,$72,$6C,$70,$08,$01,$07,$66,$02,$72,$72
	dc.b $18,$C1,$4E,$75,$61,$73,$6C,$73,$72,$6F,$72,$6F,$32,$07,$60,$00
	dc.b $F7,$2A,$43,$ED,$FF,$FE,$61,$00,$19,$DE,$67,$02,$4E,$75,$49,$EE
	dc.b $09,$A8,$3E,$28,$00,$04,$2F,$08,$61,$00,$F8,$0E,$19,$7C,$00,$20
	dc.b $FF,$FF,$18,$FC,$00,$5B,$20,$5F,$22,$28,$00,$08,$30,$28,$00,$06
	dc.b $B0,$7C,$00,$01,$67,$34,$B0,$7C,$00,$02,$67,$2A,$B0,$7C,$00,$03
	dc.b $67,$1E,$18,$FC,$00,$3F,$43,$E8,$00,$0C,$70,$07,$12,$19,$67,$1E
	dc.b $18,$C1,$51,$C8,$FF,$F8,$18,$FC,$00,$2E,$18,$FC,$00,$2E,$60,$0E
	dc.b $18,$FC,$00,$2A,$60,$08,$18,$FC,$00,$3D,$61,$00,$F6,$DE,$18,$FC
	dc.b $00,$5D,$4E,$75,$30,$07,$02,$40,$00,$3F,$B0,$7C,$00,$2E,$66,$5E
	dc.b $20,$2E,$00,$54,$54,$80,$B0,$8D,$66,$08,$20,$6E,$00,$48,$D0,$D5
	dc.b $60,$1E,$4A,$2E,$01,$46,$67,$46,$20,$2E,$01,$42,$67,$40,$08,$00
	dc.b $00,$00,$66,$3A,$24,$40,$61,$00,$4E,$6C,$66,$32,$20,$52,$D0,$D5
	dc.b $61,$00,$5B,$A4,$67,$28,$18,$FC,$00,$5F,$18,$FC,$00,$4C,$18,$FC
	dc.b $00,$56,$18,$FC,$00,$4F,$61,$00,$56,$D2,$18,$FC,$00,$28,$18,$FC
	dc.b $00,$61,$18,$FC,$00,$36,$18,$FC,$00,$29,$54,$4D,$4E,$75,$78,$64
	dc.b $60,$00,$0C,$98,$4A,$AE,$01,$36,$67,$2E,$30,$07,$02,$40,$0E,$00
	dc.b $B0,$7C,$0C,$00,$66,$22,$30,$07,$02,$40,$00,$3F,$B0,$7C,$00,$38
	dc.b $67,$1A,$B0,$7C,$00,$39,$67,$1E,$B0,$7C,$00,$3A,$67,$1E,$02,$40
	dc.b $00,$38,$B0,$7C,$00,$28,$67,$2C,$60,$00,$F8,$E4,$74,$04,$B4,$55
	dc.b $66,$F6,$70,$02,$60,$0E,$24,$15,$70,$04,$60,$08,$34,$15,$48,$C2
	dc.b $D4,$8D,$70,$02,$2D,$42,$01,$42,$D0,$8D,$54,$80,$2D,$40,$01,$3E
	dc.b $60,$00,$F8,$BC,$30,$07,$02,$40,$00,$07,$01,$2E,$01,$49,$67,$C8
	dc.b $D0,$40,$D0,$40,$41,$EE,$00,$30,$20,$70,$00,$00,$D0,$D5,$24,$08
	dc.b $70,$02,$60,$D0,$34,$1D,$32,$02,$02,$42,$0F,$FF,$E9,$59,$41,$FA
	dc.b $07,$8C,$08,$07,$00,$00,$66,$0A,$61,$0E,$18,$FC,$00,$2C,$60,$00
	dc.b $00,$26,$61,$22,$18,$FC,$00,$2C,$B4,$58,$67,$0A,$10,$10,$67,$10
	dc.b $48,$80,$D0,$C0,$60,$F2,$52,$88,$18,$D8,$66,$FC,$53,$8C,$4E,$75
	dc.b $18,$FC,$00,$3F,$4E,$75,$02,$01,$00,$0F,$70,$61,$51,$01,$64,$04
	dc.b $50,$01,$70,$64,$18,$C0,$06,$01,$00,$30,$18,$C1,$4E,$75,$7A,$02
	dc.b $78,$3D,$60,$00,$0B,$B6,$78,$25,$61,$28,$BE,$7C,$10,$00,$65,$04
	dc.b $18,$FC,$00,$3F,$4E,$75,$78,$65,$61,$18,$18,$FC,$00,$2C,$32,$07
	dc.b $E0,$49,$E8,$49,$60,$00,$00,$7A,$32,$15,$61,$F4,$18,$FC,$00,$2C
	dc.b $78,$25,$7A,$02,$3F,$15,$54,$4D,$61,$00,$0B,$80,$18,$FC,$00,$7B
	dc.b $3E,$1F,$32,$07,$EC,$49,$08,$07,$00,$0B,$66,$0C,$02,$81,$00,$00
	dc.b $00,$1F,$61,$00,$00,$34,$60,$08,$02,$01,$00,$1F,$61,$00,$00,$42
	dc.b $18,$FC,$00,$3A,$32,$07,$02,$81,$00,$00,$00,$1F,$08,$07,$00,$05
	dc.b $66,$0C,$4A,$01,$66,$02,$72,$20,$61,$00,$00,$0E,$60,$04,$61,$00
	dc.b $00,$20,$18,$FC,$00,$7D,$4E,$75,$82,$FC,$00,$0A,$4A,$41,$67,$06
	dc.b $06,$01,$00,$30,$18,$C1,$48,$41,$06,$01,$00,$30,$18,$C1,$4E,$75
	dc.b $18,$FC,$00,$64,$B2,$3C,$00,$08,$65,$04,$18,$FC,$00,$3F,$60,$00
	dc.b $F5,$A6,$78,$34,$08,$07,$00,$06,$67,$02,$78,$6C,$7A,$02,$60,$00
	dc.b $0A,$FA,$32,$07,$02,$41,$00,$07,$34,$07,$E6,$4A,$02,$02,$00,$07
	dc.b $B4,$3C,$00,$01,$67,$1A,$B4,$3C,$00,$07,$67,$2C,$18,$FC,$00,$53
	dc.b $61,$00,$00,$92,$18,$FC,$00,$20,$78,$3D,$7A,$00,$60,$00,$0A,$DE
	dc.b $18,$FC,$00,$44,$18,$FC,$00,$42,$61,$00,$00,$7A,$18,$FC,$00,$20
	dc.b $61,$00,$0A,$EE,$60,$00,$F9,$A8,$B2,$3C,$00,$02,$65,$CE,$18,$FC
	dc.b $00,$74,$18,$FC,$00,$72,$18,$FC,$00,$61,$18,$FC,$00,$70,$61,$00
	dc.b $00,$54,$60,$00,$0A,$4C,$02,$47,$00,$7F,$67,$32,$18,$FC,$00,$62
	dc.b $61,$4C,$08,$07,$00,$06,$67,$16,$18,$FC,$00,$2E,$18,$FC,$00,$6C
	dc.b $18,$FC,$00,$20,$22,$15,$D2,$8D,$58,$4D,$60,$00,$FA,$6E,$18,$FC
	dc.b $00,$20,$32,$15,$48,$C1,$D2,$8D,$54,$4D,$60,$00,$FA,$5E,$32,$15
	dc.b $4A,$41,$66,$C8,$54,$4D,$18,$FC,$00,$6E,$18,$FC,$00,$6F,$18,$FC
	dc.b $00,$70,$4E,$75,$3E,$1D,$BE,$7C,$00,$20,$64,$00,$0E,$E8,$41,$FA
	dc.b $00,$26,$30,$07,$08,$00,$00,$05,$66,$0C,$02,$40,$00,$1F,$D0,$40
	dc.b $D0,$40,$41,$FB,$00,$16,$18,$D8,$18,$D8,$67,$06,$18,$D8,$67,$02
	dc.b $18,$D8,$53,$4C,$4E,$75,$3F,$3F,$00,$00,$66,$00,$00,$00,$65,$71
	dc.b $00,$00,$6F,$67,$74,$00,$6F,$67,$65,$00,$6F,$6C,$74,$00,$6F,$6C
	dc.b $65,$00,$6F,$67,$6C,$00,$6F,$72,$00,$00,$75,$6E,$00,$00,$75,$65
	dc.b $71,$00,$75,$67,$74,$00,$75,$67,$65,$00,$75,$6C,$74,$00,$75,$6C
	dc.b $65,$00,$6E,$65,$00,$00,$74,$00,$00,$00,$73,$66,$00,$00,$73,$65
	dc.b $71,$00,$67,$74,$00,$00,$67,$65,$00,$00,$6C,$74,$00,$00,$6C,$65
	dc.b $00,$00,$67,$6C,$00,$00,$67,$6C,$65,$00,$6E,$67,$6C,$65,$6E,$67
	dc.b $6C,$00,$6E,$6C,$65,$00,$6E,$6C,$74,$00,$6E,$67,$65,$00,$6E,$67
	dc.b $74,$00,$73,$6E,$65,$00,$73,$74,$00,$00,$41,$FA,$00,$06,$60,$00
	dc.b $09,$78,$01,$78,$05,$06,$01,$AA,$02,$E4,$03,$E0,$03,$B0,$04,$A4
	dc.b $04,$70,$30,$06,$02,$40,$00,$3F,$D0,$40,$30,$3B,$00,$14,$41,$FA
	dc.b $00,$90,$D0,$C0,$18,$D8,$66,$FC,$19,$7C,$00,$2E,$FF,$FF,$4E,$75
	dc.b $00,$0A,$00,$0F,$00,$13,$00,$18,$00,$1E,$00,$00,$00,$23,$00,$00
	dc.b $00,$2A,$00,$31,$00,$36,$00,$00,$00,$3B,$00,$40,$00,$46,$00,$4A
	dc.b $00,$4E,$00,$53,$00,$5A,$00,$00,$00,$61,$00,$66,$00,$6C,$00,$00
	dc.b $00,$71,$00,$75,$00,$7A,$00,$00,$00,$7E,$00,$83,$00,$87,$00,$8E
	dc.b $00,$95,$00,$99,$00,$9D,$00,$A1,$00,$A5,$00,$AC,$00,$B0,$00,$B6
	dc.b $00,$BD
	dcb.b $F,$00
	dc.b $03,$00,$03,$00,$03,$00,$03,$00,$03,$00,$03,$00,$03,$00,$03,$00
	dc.b $C1,$00,$00,$00,$C5
	dcb.b $A,$00
	dc.b $3F,$3F,$00,$73,$69,$6E,$63,$6F,$73,$00,$6D,$6F,$76,$65,$00,$69
	dc.b $6E,$74,$00
	dc.b "sinh",$00	; string
	dc.b "intrz",$00	; string
	dc.b "sqrt",$00	; string
	dc.b "lognp1",$00	; string
	dc.b "etoxm1",$00	; string
	dc.b "tanh",$00	; string
	dc.b "atan",$00	; string
	dc.b "asin",$00	; string
	dc.b "atanh",$00	; string
	dc.b $73,$69,$6E,$00,$74,$61,$6E,$00
	dc.b "etox",$00	; string
	dc.b "twotox",$00	; string
	dc.b "tentox",$00	; string
	dc.b "logn",$00	; string
	dc.b "log10",$00	; string
	dc.b "log2",$00	; string
	dc.b $61,$62,$73,$00,$63,$6F,$73,$68,$00,$6E,$65,$67,$00,$61,$63,$6F
	dc.b $73,$00,$63,$6F,$73,$00,$67,$65,$74,$65,$78,$70,$00,$67,$65,$74
	dc.b $6D,$61,$6E,$00,$64,$69,$76,$00,$6D,$6F,$64,$00,$61,$64,$64,$00
	dc.b $6D,$75,$6C,$00,$73,$67,$6C,$64,$69,$76,$00,$72,$65,$6D,$00,$73
	dc.b $63,$61,$6C,$65,$00,$73,$67,$6C,$6D,$75,$6C,$00,$73,$75,$62,$00
	dc.b $63,$6D,$70,$00,$74,$73,$74,$00,$00,$61,$00,$FE,$96,$02,$47,$00
	dc.b $3F,$67,$04,$18,$FC,$00,$3F,$18,$FC,$00,$78,$18,$FC,$00,$20,$32
	dc.b $06,$ED,$59,$61,$00,$00,$66,$08,$06,$00,$05,$66,$36,$30,$06,$EE
	dc.b $58,$90,$01,$02,$00,$00,$07,$66,$2A,$4E,$75,$32,$06,$ED,$59,$02
	dc.b $41,$00,$07,$B2,$3C,$00,$07,$67,$00,$00,$8A,$61,$00,$FE,$54,$18
	dc.b $FB,$10,$46,$18,$FC,$00,$20,$BE,$3C,$00,$3C,$67,$42,$78,$FD,$61
	dc.b $00,$01,$BA,$32,$06,$02,$41,$00,$7F,$B2,$3C,$00,$3A,$67,$CA,$18
	dc.b $FC,$00,$2C,$02,$41,$00,$38,$B2,$3C,$00,$30,$66,$0A,$32,$06,$61
	dc.b $00,$00,$0A,$18,$FC,$00,$3A,$32,$06,$EE,$59,$18,$FC,$00,$66,$18
	dc.b $FC,$00,$70,$60,$00,$F2,$20,$6C,$73,$78,$70,$77,$64,$62,$3F,$18
	dc.b $FC,$00,$23,$74,$00,$14,$3B,$10,$1C,$67,$10,$18,$FC,$00,$24,$32
	dc.b $1D,$61,$00,$F1,$46,$51,$CA,$FF,$F8,$60,$A8,$32,$1D,$61,$00,$F1
	dc.b $00,$60,$A0,$01,$01,$05,$05,$00,$03,$00,$00,$18,$D8,$66,$FC,$53
	dc.b $4C,$4E,$75,$41,$FA,$00,$56,$61,$F2,$32,$06,$02,$41,$00,$3F,$61
	dc.b $00,$F0,$E8,$18,$FC,$00,$2C,$61,$9E,$18,$FC,$00,$20,$18,$FC,$00
	dc.b $3B,$32,$06,$02,$01,$00,$3F,$B2,$3C,$00,$34,$64,$18,$41,$FA,$00
	dc.b $38,$10,$18,$6B,$0C,$B0,$01,$67,$06,$4A,$18,$66,$FC,$60,$F2,$60
	dc.b $BA,$60,$00,$0B,$B0,$18,$FC,$00,$31,$18,$FC,$00,$65,$10,$01,$04
	dc.b $00,$00,$33,$72,$01,$E1,$61,$60,$00,$F0,$A0
	dc.b "movecr.x #",$00	; string
	dc.b $00,$00,$70,$69,$00,$0B,$6C,$6F,$67,$31,$30,$28,$32,$29,$00,$0C
	dc.b $65,$00,$0D,$6C,$6F,$67,$32,$28,$65,$29,$00,$0E,$6C,$6F,$67,$31
	dc.b $30,$28,$65,$29,$00,$0F,$30,$00,$30,$6C,$6E,$28,$32,$29,$00,$31
	dc.b $6C,$6E,$28,$31,$30,$29,$00,$32,$31,$00,$33,$31,$30,$00,$FF,$18
	dc.b $FC,$00,$6D,$18,$FC,$00,$6F,$18,$FC,$00,$76,$18,$FC,$00,$65,$18
	dc.b $FC,$00,$2E,$32,$06,$ED,$59,$02,$41,$00,$07,$18,$FB,$10,$06,$60
	dc.b $00,$00,$0A,$6C,$73,$78,$70,$77,$64,$62,$70,$18,$FC,$00,$20,$61
	dc.b $00,$FE,$E0,$18,$FC,$00,$2C,$32,$06,$ED,$59,$02,$41,$00,$07,$78
	dc.b $3D,$61,$00,$00,$62,$32,$06,$ED,$59,$02,$41,$00,$07,$B2,$3C,$00
	dc.b $03,$67,$30,$B2,$3C,$00,$07,$66,$1C,$18,$FC,$00,$7B,$18,$FC,$00
	dc.b $64,$12,$06,$E8,$19,$B2,$3C,$00,$10,$65,$04,$18,$FC,$00,$3F,$61
	dc.b $00,$F0,$CE,$60,$2A,$12,$06,$02,$01,$00,$7F,$67,$04,$18,$FC,$00
	dc.b $3F,$4E,$75,$18,$FC,$00,$7B,$12,$06,$08,$01,$00,$06,$67,$06,$00
	dc.b $01,$00,$80,$60,$04,$02,$01,$00,$7F,$48,$81,$61,$00,$EF,$9A,$18
	dc.b $FC,$00,$7D,$4E,$75,$70,$53,$03,$00,$66,$0C,$12,$07,$02,$01,$00
	dc.b $38,$66,$04,$18,$FC,$00,$3F,$7A,$01,$3F,$06,$61,$00,$05,$E6,$3C
	dc.b $1F,$4E,$75,$78,$7D,$60,$F2,$78,$FD,$60,$EE,$61,$00,$00,$90,$61
	dc.b $00,$00,$36,$18,$FC,$00,$2C,$61,$00,$00,$10,$02,$04,$00,$3F,$3F
	dc.b $03,$61,$00,$05,$C0,$36,$1F,$4E,$75,$41,$FA,$00,$08,$18,$30,$30
	dc.b $00,$4E,$75,$FC,$FF,$FD,$FC,$FD,$FC,$FC,$FC,$61,$00,$00,$60,$61
	dc.b $E8,$61,$DC,$18,$FC,$00,$2C,$70,$02,$02,$03,$00,$07,$41,$FA,$00
	dc.b $3E,$67,$00,$0A,$3A,$B6,$3C,$00,$03,$65,$20,$B6,$3C,$00,$04,$67
	dc.b $1A,$01,$03,$67,$0A,$61,$00,$FE,$2E,$18,$FC,$00,$2F,$60,$04,$4A
	dc.b $18,$66,$FC,$53,$00,$64,$EA,$53,$4C,$4E,$75,$01,$03,$66,$08,$4A
	dc.b $18,$66,$FC,$53,$00,$60,$F4,$61,$00,$FE,$0C
	dc.b "Nufpcr",$00	; string
	dc.b "fpsr",$00	; string
	dc.b "fpiar",$00	; string
	dc.b $18,$FC,$00,$6D,$18,$FC,$00,$6F,$18,$FC,$00,$76,$18,$FC,$00,$65
	dc.b $26,$06,$ED,$5B,$02,$03,$00,$07,$B6,$3C,$00,$03,$65,$0A,$B6,$3C
	dc.b $00,$04,$67,$04,$18,$FC,$00,$6D,$7A,$02,$60,$00,$EF,$70,$61,$00
	dc.b $00,$76,$16,$06,$08,$06,$00,$0C,$66,$12,$08,$06,$00,$0B,$66,$0C
	dc.b $12,$06,$70,$07,$E3,$11,$E2,$13,$51,$C8,$FF,$FA,$61,$30,$18,$FC
	dc.b $00,$2C,$7A,$01,$78,$34,$08,$06,$00,$0C,$66,$02,$78,$10,$60,$00
	dc.b $04,$E6,$61,$00,$00,$42,$7A,$01,$78,$6C,$61,$00,$FE,$F0,$18,$FC
	dc.b $00,$2C,$16,$06,$08,$06,$00,$0C,$66,$04,$18,$FC,$00,$3F,$08,$06
	dc.b $00,$0B,$66,$0C,$78,$66,$3F,$06,$61,$00,$F2,$92,$3C,$1F,$4E,$75
	dc.b $18,$FC,$00,$64,$12,$06,$E8,$19,$B2,$3C,$00,$08,$65,$04,$18,$FC
	dc.b $00,$3F,$60,$00,$EF,$3E,$70,$78,$41,$FA,$00,$12,$61,$00,$FD,$4A
	dc.b $18,$C0,$18,$FC,$00,$20,$4E,$75,$70,$6C,$60,$EC,$6D,$6F,$76,$65
	dc.b $6D,$2E,$00,$00,$60,$00,$09,$2A,$00,$00,$06,$53,$46,$43,$00,$00
	dc.b $00,$01,$06,$44,$46,$43,$00,$00,$00,$02,$06,$43,$41,$43,$52,$00
	dc.b $08,$00,$06,$55,$53,$50,$00,$00,$08,$01,$06,$56,$42,$52,$00,$00
	dc.b $08,$02,$06,$43,$41,$41,$52,$00,$08,$03,$06,$4D,$53,$50,$00,$00
	dc.b $08,$04,$06,$49,$53,$50,$00,$00,$08,$04,$00,$00,$41,$FA,$00,$06
	dc.b $60,$00,$04,$22,$00,$B8,$01,$32,$00,$42,$00,$10,$02,$16,$08,$DC
	dc.b $08,$DC,$08,$DC,$61,$00,$01,$00,$7A,$01,$61,$00,$EE,$70,$BC,$7C
	dc.b $60,$00,$66,$14,$61,$00,$00,$EA,$18,$FC,$00,$2C,$41,$FA,$00,$06
	dc.b $60,$00,$FC,$B6,$70,$73,$72,$00,$BC,$7C,$62,$00,$66,$00,$08,$A2
	dc.b $61,$EA,$60,$00,$00,$C8,$61,$00,$00,$CE,$7A,$02,$08,$06,$00,$0B
	dc.b $67,$02,$7A,$04,$61,$00,$EE,$36,$32,$06,$02,$41,$F0,$FF,$B2,$7C
	dc.b $40,$00,$67,$04,$18,$FC,$00,$3F,$32,$06,$02,$41,$03,$00,$B2,$7C
	dc.b $03,$00,$66,$04,$18,$FC,$00,$3F,$08,$06,$00,$09,$66,$3A,$61,$00
	dc.b $00,$90,$18,$FC,$00,$2C,$08,$06,$00,$0B,$67,$1A,$08,$06,$00,$0A
	dc.b $66,$06,$18,$FC,$00,$73,$60,$04,$18,$FC,$00,$63,$18,$FC,$00,$72
	dc.b $18,$FC,$00,$70,$4E,$75,$08,$06,$00,$0A,$66,$00,$08,$34,$18,$FC
	dc.b $00,$74,$18,$FC,$00,$63,$4E,$75,$61,$CC,$60,$50,$61,$58,$7A,$02
	dc.b $61,$00,$ED,$CA,$32,$06,$02,$41,$F8,$FF,$B2,$7C,$08,$00,$67,$04
	dc.b $18,$FC,$00,$3F,$32,$06,$02,$41,$03,$00,$B2,$7C,$03,$00,$66,$04
	dc.b $18,$FC,$00,$3F,$08,$06,$00,$09,$66,$20,$61,$24,$18,$FC,$00,$2C
	dc.b $18,$FC,$00,$74,$18,$FC,$00,$74,$08,$06,$00,$0A,$67,$06,$18,$FC
	dc.b $00,$31,$4E,$75,$18,$FC,$00,$30,$4E,$75,$61,$E4,$18,$FC,$00,$2C
	dc.b $78,$24,$60,$00,$FD,$38,$18,$FC,$00,$6D,$18,$FC,$00,$6F,$18,$FC
	dc.b $00,$76,$18,$FC,$00,$65,$08,$06,$00,$08,$67,$08,$18,$FC,$00,$66
	dc.b $18,$FC,$00,$64,$4E,$75,$32,$06,$ED,$59,$02,$01,$00,$07,$67,$56
	dc.b $41,$FA,$00,$40,$61,$00,$FB,$A2,$B2,$3C,$00,$01,$67,$3A,$B2,$3C
	dc.b $00,$04,$67,$08,$B2,$3C,$00,$06,$66,$00,$07,$86,$18,$FC,$00,$20
	dc.b $61,$6A,$18,$FC,$00,$2C,$18,$FC,$00,$23,$32,$06,$02,$41,$00,$07
	dc.b $61,$00,$EC,$74,$08,$06,$00,$0B,$67,$00,$00,$1A,$18,$FC,$00,$2C
	dc.b $60,$8E,$66,$6C,$75,$73,$68,$00,$18,$FC,$00,$61,$BC,$7C,$24,$00
	dc.b $66,$00,$07,$4E,$4E,$75,$41,$FA,$00,$2E,$61,$00,$FB,$4C,$08,$06
	dc.b $00,$09,$66,$06,$18,$FC,$00,$77,$60,$04,$18,$FC,$00,$72,$18,$FC
	dc.b $00,$20,$61,$18,$32,$06,$02,$41,$FD,$E0,$B2,$7C,$20,$00,$66,$00
	dc.b $07,$20,$60,$00,$FF,$48,$6C,$6F,$61,$64,$00,$00,$12,$06,$02,$01
	dc.b $00,$18,$67,$24,$B2,$3C,$00,$08,$67,$18,$B2,$3C,$00,$10,$67,$04
	dc.b $60,$00,$06,$FE,$18,$FC,$00,$23,$32,$06,$02,$41,$00,$07,$60,$00
	dc.b $EB,$F6,$12,$06,$60,$00,$02,$76,$12,$06,$02,$41,$00,$07,$53,$01
	dc.b $6B,$0A,$66,$00,$06,$DC,$18,$FC,$00,$64,$60,$04,$18,$FC,$00,$73
	dc.b $18,$FC,$00,$66,$18,$FC,$00,$63,$4E,$75,$41,$FA,$00,$40,$61,$00
	dc.b $FA,$C8,$08,$06,$00,$09,$66,$06,$18,$FC,$00,$77,$60,$04,$18,$FC
	dc.b $00,$72,$18,$FC,$00,$20,$61,$94,$61,$00,$FE,$D2,$18,$FC,$00,$2C
	dc.b $18,$FC,$00,$23,$32,$06,$ED,$59,$61,$00,$EC,$88,$08,$06,$00,$08
	dc.b $66,$10,$BC,$3C,$00,$20,$64,$00,$06,$88,$4E,$75,$74,$65,$73,$74
	dc.b $00,$00,$32,$06,$02,$41,$1C,$00,$67,$00,$06,$76,$12,$06,$E7,$19
	dc.b $18,$FC,$00,$2C,$18,$FC,$00,$61,$60,$00,$EC,$58,$3A,$07,$EF,$5D
	dc.b $02,$05,$00,$03,$53,$05,$60,$00,$EC,$04,$EC,$49,$60,$00,$01,$DE
	dc.b $32,$07,$3C,$1D,$02,$41,$00,$3F,$B2,$7C,$00,$3C,$67,$18,$61,$DC
	dc.b $61,$00,$01,$C8,$18,$FC,$00,$2C,$32,$06,$61,$DE,$18,$FC,$00,$2C
	dc.b $78,$3C,$60,$00,$01,$82,$18,$FC,$00,$32,$BE,$7C,$0A,$FC,$67,$00
	dc.b $06,$20,$61,$B8,$61,$00,$01,$A4,$18,$FC,$00,$3A,$32,$15,$61,$00
	dc.b $01,$9C,$18,$FC,$00,$2C,$32,$06,$61,$B0,$18,$FC,$00,$3A,$32,$15
	dc.b $61,$A8,$18,$FC,$00,$2C,$32,$06,$61,$06,$18,$FC,$00,$3A,$32,$1D
	dc.b $18,$FC,$00,$28,$61,$46,$18,$FC,$00,$29,$4E,$75,$3C,$1D,$08,$06
	dc.b $00,$0B,$66,$0A,$18,$FC,$00,$6D,$18,$FC,$00,$70,$60,$08,$18,$FC
	dc.b $00,$68,$18,$FC,$00,$6B,$18,$FC,$00,$32,$3A,$07,$EF,$5D,$02,$05
	dc.b $00,$03,$61,$00,$EB,$68,$32,$06,$02,$41,$03,$FF,$66,$00,$05,$B2
	dc.b $78,$64,$61,$00,$FB,$18,$18,$FC,$00,$2C,$32,$06,$4A,$41,$6B,$06
	dc.b $18,$FC,$00,$64,$60,$04,$18,$FC,$00,$61,$E9,$59,$60,$00,$EB,$84
	dc.b $61,$00,$EB,$3A,$61,$00,$06,$86,$18,$FC,$00,$2C,$60,$00,$FA,$F8
	dc.b $61,$00,$EB,$2A,$78,$FF,$60,$00,$00,$CE,$3C,$1D,$08,$06,$00,$0B
	dc.b $67,$06,$18,$FC,$00,$73,$4E,$75,$18,$FC,$00,$75,$4E,$75,$7A,$02
	dc.b $61,$00,$EB,$0A,$61,$00,$FA,$D4,$18,$FC,$00,$2C,$4E,$75,$61,$DA
	dc.b $61,$EC,$08,$06,$00,$0A,$67,$08,$61,$00,$00,$D0,$18,$FC,$00,$3A
	dc.b $32,$06,$60,$98,$61,$C4,$08,$06,$00,$0A,$66,$04,$18,$FC,$00,$6C
	dc.b $61,$CC,$60,$E4,$61,$00,$ED,$7A,$18,$FC,$00,$2C,$18,$FC,$00,$23
	dc.b $22,$1D,$60,$00,$E9,$FA,$61,$00,$F0,$B0,$18,$FC,$00,$2C,$18,$FC
	dc.b $00,$23,$32,$1D,$60,$00,$EA,$10,$32,$07,$E0,$49,$02,$01,$00,$0F
	dc.b $61,$00,$EA,$70,$53,$4C,$32,$07,$02,$01,$00,$07,$B2,$3C,$00,$04
	dc.b $67,$30,$18,$FC,$00,$2E,$B2,$3C,$00,$02,$67,$12,$B2,$3C,$00,$03
	dc.b $66,$00,$04,$DE,$18,$FC,$00,$6C,$22,$1D,$60,$00,$00,$0A,$18,$FC
	dc.b $00,$77,$32,$1D,$48,$C1,$18,$FC,$00,$20,$18,$FC,$00,$23,$60,$00
	dc.b $E9,$CE,$4E,$75,$3C,$1D,$32,$06,$E7,$59,$02,$41,$00,$07,$10,$01
	dc.b $60,$00,$EA,$EE,$4E,$75,$2D,$4D,$05,$94,$32,$07,$02,$41,$00,$07
	dc.b $34,$07,$E6,$4A,$02,$02,$00,$07,$10,$02,$3C,$01,$41,$FA,$00,$06
	dc.b $60,$00,$EA,$CE,$00,$10,$00,$20,$00,$34,$00,$76,$00,$84,$00,$AC
	dc.b $01,$92,$04,$72,$05,$04,$67,$00,$04,$78,$12,$06,$18,$FC,$00,$64
	dc.b $60,$00,$EA,$60,$05,$04,$67,$00,$04,$68,$4A,$05,$67,$00,$04,$62
	dc.b $18,$FC,$00,$61,$60,$00,$EA,$4C,$05,$04,$67,$00,$04,$54,$08,$EE
	dc.b $00,$00,$01,$4B,$66,$28,$61,$0A,$2D,$40,$01,$4E,$1D,$45,$01,$4D
	dc.b $60,$1C,$30,$06,$D0,$40,$D0,$40,$B0,$7C,$00,$1C,$66,$0A,$08,$2E
	dc.b $00,$05,$00,$5A,$67,$02,$70,$20,$20,$36,$00,$30,$4E,$75,$18,$FC
	dc.b $00,$28,$61,$BC,$18,$FC,$00,$29,$4E,$75,$05,$04,$67,$00,$04,$12
	dc.b $61,$BC,$18,$FC,$00,$2B,$4E,$75,$05,$04,$67,$00,$04,$04,$18,$FC
	dc.b $00,$2D,$08,$2E,$00,$00,$01,$4B,$66,$D4,$61,$A2,$02,$45,$00,$03
	dc.b $70,$00,$10,$3B,$50,$08,$91,$AE,$01,$4E,$4E,$75,$01,$02,$04,$00
	dc.b $05,$04,$67,$00,$03,$DC,$32,$1D,$48,$C1,$08,$EE,$00,$00,$01,$4B
	dc.b $66,$0C,$61,$8E,$D0,$81,$2D,$40,$01,$4E,$1D,$45,$01,$4D,$4A,$AE
	dc.b $00,$AE,$67,$4A,$0D,$2E,$05,$90,$67,$1A,$30,$01,$48,$C0,$2F,$02
	dc.b $14,$06,$52,$02,$61,$00,$49,$58,$4C,$DF,$00,$04,$67,$06,$61,$00
	dc.b $49,$16,$60,$2E,$4A,$2E,$01,$48,$67,$24,$BC,$3C,$00,$07,$67,$1E
	dc.b $30,$01,$48,$C0,$2F,$02,$74,$00,$14,$06,$E5,$4A,$D0,$B6,$20,$30
	dc.b $24,$1F,$61,$00,$4B,$FA,$67,$06,$61,$00,$48,$EC,$60,$04,$61,$00
	dc.b $E8,$6C,$12,$06,$60,$00,$FF,$48,$10,$04,$48,$80,$D0,$C0,$30,$04
	dc.b $ED,$58,$02,$40,$00,$3C,$B0,$7C,$00,$3C,$66,$0A,$08,$2E,$00,$05
	dc.b $00,$5A,$67,$02,$70,$40,$20,$36,$00,$10,$08,$04,$00,$0B,$66,$02
	dc.b $48,$C0,$D1,$C0,$2D,$48,$01,$4E,$1D,$45,$01,$4D,$4E,$75,$50,$C3
	dc.b $38,$1D,$08,$04,$00,$08,$66,$00,$00,$C4,$12,$04,$48,$81,$48,$C1
	dc.b $D2,$AE,$05,$94,$D2,$AE,$00,$04,$61,$00,$E8,$24,$18,$FC,$00,$28
	dc.b $18,$FC,$00,$70,$18,$FC,$00,$63,$18,$FC,$00,$2C,$61,$00,$00,$46
	dc.b $18,$FC,$00,$29,$4E,$75,$08,$04,$00,$05,$67,$00,$02,$F4,$38,$1D
	dc.b $51,$C3,$08,$04,$00,$08,$66,$00,$00,$84,$30,$3C,$06,$00,$C0,$44
	dc.b $67,$00,$02,$6C,$12,$04,$61,$00,$E7,$C2,$18,$FC,$00,$28,$18,$FC
	dc.b $00,$61,$72,$30,$D2,$06,$18,$C1,$18,$FC,$00,$2C,$61,$06,$18,$FC
	dc.b $00,$29,$4E,$75,$30,$04,$EB,$58,$02,$40,$00,$1E,$18,$FB,$00,$2A
	dc.b $18,$FB,$00,$27,$18,$FC,$00,$2E,$70,$77,$08,$04,$00,$0B,$67,$02
	dc.b $70,$6C,$18,$C0,$30,$3C,$06,$00,$C0,$44,$67,$0A,$18,$FC,$00,$2A
	dc.b $EF,$58,$18,$FB,$00,$23,$4E,$75,$64,$30,$64,$31,$64,$32,$64,$33
	dc.b $64,$34,$64,$35,$64,$36,$64,$37,$61,$30,$61,$31,$61,$32,$61,$33
	dc.b $61,$34,$61,$35,$61,$36,$61,$37,$32,$34,$38,$00,$18,$FC,$00,$28
	dc.b $70,$07,$C0,$44,$08,$04,$00,$06,$67,$04,$08,$C0,$00,$03,$41,$FA
	dc.b $00,$0C,$61,$00,$E8,$8C,$18,$FC,$00,$29,$4E,$75,$00,$20,$00,$30
	dc.b $00,$4A,$00,$4A,$00,$E8,$00,$6A,$00,$8A,$00,$8A,$00,$AA,$00,$B6
	dc.b $00,$CC,$00,$CC,$00,$E8,$00,$E8,$00,$E8,$00,$E8,$61,$00,$00,$CC
	dc.b $61,$00,$01,$2C,$61,$00,$01,$60,$60,$00,$01,$9A,$18,$FC,$00,$5B
	dc.b $61,$00,$00,$B8,$61,$00,$01,$18,$61,$00,$01,$4C,$61,$00,$01,$86
	dc.b $18,$FC,$00,$5D,$4E,$75,$18,$FC,$00,$5B,$61,$00,$00,$9E,$61,$00
	dc.b $00,$FE,$61,$00,$01,$32,$61,$00,$01,$6C,$18,$FC,$00,$5D,$18,$FC
	dc.b $00,$2C,$60,$00,$01,$44,$18,$FC,$00,$5B,$61,$00,$00,$7E,$61,$00
	dc.b $00,$DE,$61,$00,$01,$50,$18,$FC,$00,$5D,$18,$FC,$00,$2C,$61,$00
	dc.b $01,$06,$60,$00,$01,$40,$18,$FC,$00,$5B,$61,$00,$00,$5E,$61,$00
	dc.b $00,$BE,$61,$00,$01,$30,$18,$FC,$00,$5D,$18,$FC,$00,$2C,$61,$00
	dc.b $00,$E6,$60,$00,$01,$04,$61,$00,$00,$42,$61,$00,$00,$A2,$60,$00
	dc.b $01,$14,$18,$FC,$00,$5B,$61,$00,$00,$32,$61,$00,$00,$92,$61,$00
	dc.b $01,$04,$18,$FC,$00,$5D,$4E,$75,$18,$FC,$00,$5B,$61,$00,$00,$1C
	dc.b $61,$00,$00,$7C,$61,$00,$00,$EE,$18,$FC,$00,$5D,$18,$FC,$00,$2C
	dc.b $60,$00,$00,$C6,$18,$FC,$00,$3F,$4E,$75,$70,$30,$C0,$44,$67,$2A
	dc.b $E8,$48,$53,$00,$67,$56,$53,$40,$66,$26,$32,$1D,$4A,$03,$66,$06
	dc.b $61,$00,$E6,$3A,$60,$38,$48,$C1,$D2,$AE,$00,$04,$4A,$04,$6B,$04
	dc.b $D2,$AE,$05,$94,$61,$00,$E6,$38,$60,$24,$18,$FC,$00,$3F,$60,$1E
	dc.b $22,$1D,$4A,$03,$67,$0C,$D2,$AE,$00,$04,$4A,$04,$6B,$04,$D2,$AE
	dc.b $05,$94,$61,$00,$E6,$1A,$18,$FC,$00,$2E,$18,$FC,$00,$6C,$4A,$2E
	dc.b $05,$92,$67,$04,$18,$FC,$00,$7D,$18,$FC,$00,$2C,$4E,$75,$4A,$04
	dc.b $6A,$22,$18,$FC,$00,$7A,$4A,$03,$66,$1E,$4A,$2E,$05,$87,$67,$10
	dc.b $18,$FC,$00,$61,$70,$30,$D0,$06,$18,$C0,$18,$FC,$00,$2C,$4E,$75
	dc.b $53,$4C,$4E,$75,$4A,$03,$67,$E8,$18,$FC,$00,$70,$18,$FC,$00,$63
	dc.b $18,$FC,$00,$2C,$4E,$75,$08,$04,$00,$06,$67,$12,$18,$FC,$00,$7A
	dc.b $18,$FC,$00,$64,$18,$FC,$00,$3F,$18,$FC,$00,$2C,$4E,$75,$61,$00
	dc.b $FD,$E4,$18,$FC,$00,$2C,$4E,$75,$08,$04,$00,$00,$67,$10,$22,$1D
	dc.b $61,$00,$E5,$9C,$18,$FC,$00,$2E,$18,$FC,$00,$6C,$4E,$75,$32,$1D
	dc.b $60,$00,$E5,$7A,$0C,$24,$00,$2C,$67,$02,$52,$8C,$4E,$75,$08,$EE
	dc.b $00,$00,$01,$4B,$66,$0A,$61,$00,$FC,$2A,$20,$40,$61,$00,$FC,$FA
	dc.b $12,$04,$61,$00,$E5,$46,$18,$FC,$00,$28,$18,$FC,$00,$61,$12,$06
	dc.b $61,$00,$E6,$40,$18,$FC,$00,$2C,$4A,$44,$6B,$06,$18,$FC,$00,$64
	dc.b $60,$04,$18,$FC,$00,$61,$32,$04,$70,$0C,$E0,$69,$61,$00,$E6,$24
	dc.b $70,$77,$02,$44,$08,$00,$67,$02,$70,$6C,$18,$FC,$00,$2E,$18,$C0
	dc.b $18,$FC,$00,$29,$4E,$75,$41,$FA,$00,$08,$10,$01,$60,$00,$E6,$52
	dc.b $00,$1A,$00,$46,$00,$5C,$00,$8C,$01,$04,$01,$2C,$01,$2C,$01,$2C
	dc.b $18,$FC,$00,$3F,$18,$FC,$00,$3F,$4E,$75,$08,$04,$00,$05,$67,$F0
	dc.b $32,$1D,$48,$C1,$61,$0E,$61,$00,$E4,$F6,$18,$FC,$00,$2E,$18,$FC
	dc.b $00,$77,$4E,$75,$08,$EE,$00,$00,$01,$4B,$66,$08,$2D,$41,$01,$4E
	dc.b $1D,$45,$01,$4D,$4E,$75,$08,$04,$00,$05,$67,$C4,$22,$1D,$61,$E4
	dc.b $60,$00,$E4,$CC,$05,$28,$70,$63,$29,$7D,$20,$00,$08,$04,$00,$06
	dc.b $67,$AE,$32,$15,$48,$C1,$D2,$8D,$54,$8D,$D2,$AE,$00,$04,$61,$C4
	dc.b $61,$00,$E4,$AC,$41,$FA,$00,$10,$4A,$2E,$05,$92,$67,$04,$41,$FA
	dc.b $FF,$D4,$60,$00,$E5,$D8,$04,$28,$70,$63,$29,$20,$08,$04,$00,$06
	dc.b $67,$00,$FF,$7E,$3C,$15,$38,$06,$30,$3C,$07,$00,$C0,$44,$66,$00
	dc.b $FC,$3E,$12,$06,$48,$81,$48,$C1,$D2,$8D,$54,$8D,$D2,$AE,$00,$04
	dc.b $61,$00,$E4,$6C,$41,$FA,$00,$10,$61,$00,$E5,$A2,$4A,$46,$6B,$0C
	dc.b $18,$FC,$00,$64,$60,$0A,$04,$28,$70,$63,$2C,$20,$18,$FC,$00,$61
	dc.b $32,$06,$70,$0C,$E0,$69,$61,$00,$E5,$2A,$18,$FC,$00,$2E,$02,$46
	dc.b $08,$00,$67,$06,$18,$FC,$00,$6C,$60,$04,$18,$FC,$00,$77,$18,$FC
	dc.b $00,$29,$08,$EE,$00,$00,$01,$4B,$67,$02,$4E,$75,$41,$ED,$FF,$FE
	dc.b $60,$00,$FB,$A6,$08,$04,$00,$07,$67,$00,$FF,$06,$18,$FC,$00,$23
	dc.b $4A,$05,$66,$06,$32,$1D,$60,$00,$E3,$EC,$BA,$3C,$00,$02,$66,$06
	dc.b $22,$1D,$60,$00,$E3,$FA,$32,$1D,$60,$00,$E3,$EC,$18,$FC,$00,$3F
	dc.b $4E,$75
loc_0_0000379C:
	dc.b $F1,$38,$01,$08,$F9,$C0,$00,$C0,$FF,$00,$00,$00,$FF,$00,$02,$00
	dc.b $FF,$00,$04,$00,$FF,$00,$06,$00,$FF,$C0,$0A,$C0,$FD,$C0,$0C,$C0
	dc.b $FF,$00,$08,$00,$FF,$00,$0A,$00,$FF,$00,$0C,$00,$F1,$00,$01,$00
	dc.b $F0,$00,$10,$00,$F1,$C0,$20,$40,$F0,$00,$20,$00,$F1,$C0,$30,$40
	dc.b $F0,$00,$30,$00,$FF,$FF,$4A,$FB,$FF,$FF,$4A,$FC,$FF,$FF,$4E,$70
	dc.b $FF,$FF,$4E,$71,$FF,$FF,$4E,$72,$FF,$FF,$4E,$73,$FF,$FF,$4E,$74
	dc.b $FF,$FF,$4E,$75,$FF,$FF,$4E,$76,$FF,$FF,$4E,$77,$FF,$FE,$4E,$7A
	dc.b $FF,$F8,$48,$40,$FF,$F8,$48,$80,$FF,$F8,$48,$C0,$FF,$F8,$4E,$50
	dc.b $FF,$F8,$4E,$58,$FF,$F8,$4E,$60,$FF,$F8,$4E,$68,$FF,$F8,$49,$C0
	dc.b $FF,$F0,$4E,$40,$FF,$C0,$40,$C0,$FF,$C0,$42,$C0,$FF,$F8,$48,$48
	dc.b $FF,$C0,$44,$C0,$FF,$C0,$46,$C0,$FF,$F8,$48,$08,$FF,$C0,$48,$00
	dc.b $FF,$C0,$4A,$C0,$FF,$C0,$4E,$80,$FF,$C0,$4E,$C0,$FF,$C0,$4C,$00
	dc.b $FF,$C0,$4C,$40,$FF,$80,$48,$80,$FF,$80,$4C,$80,$FF,$40,$48,$40
	dc.b $FF,$00,$40,$00,$FF,$00,$42,$00,$FF,$00,$44,$00,$FF,$00,$46,$00
	dc.b $FF,$00,$4A,$00,$F1,$40,$41,$00,$F1,$C0,$41,$C0,$F0,$FE,$50,$F8
	dc.b $F0,$F8,$50,$F8,$F0,$F8,$50,$C8,$F0,$C0,$50,$C0,$F1,$00,$50,$00
	dc.b $F1,$00,$51,$00,$F0,$00,$60,$00,$F1,$00,$70,$00,$F1,$F0,$81,$00
	dc.b $F1,$F0,$81,$40,$F1,$F0,$81,$80,$F1,$C0,$80,$C0,$F1,$C0,$81,$C0
	dc.b $F0,$00,$80,$00,$F0,$C0,$90,$C0,$F1,$30,$91,$00,$F0,$00,$90,$00
	dc.b $F1,$38,$B1,$08,$F0,$00,$B0,$00,$F1,$F0,$C1,$00,$F1,$C0,$C0,$C0
	dc.b $F1,$C0,$C1,$C0,$F1,$30,$C1,$00,$F0,$00,$C0,$00,$F0,$C0,$D0,$C0
	dc.b $F1,$30,$D1,$00,$F0,$00,$D0,$00,$FF,$C0,$E8,$C0,$FF,$C0,$E9,$C0
	dc.b $FF,$C0,$EA,$C0,$FF,$C0,$EB,$C0,$FF,$C0,$EC,$C0,$FF,$C0,$ED,$C0
	dc.b $FF,$C0,$EE,$C0,$FF,$C0,$EF,$C0,$F0,$00,$E0,$00,$FF,$C0,$F0,$00
	dc.b $FF,$C0,$F2,$00,$FF,$C0,$F2,$40,$FF,$80,$F2,$80,$FF,$C0,$F3,$00
	dc.b $FF,$C0,$F3,$40,$00,$00,$00,$00
loc_0_00003934:
	dc.b $07,$03,$6D,$6F,$76,$65,$70,$2E,$02,$2A,$63,$04,$02,$6F,$72,$69
	dc.b $05,$02,$61,$6E,$64,$69,$05,$02,$73,$75,$62,$69,$05,$02,$61,$64
	dc.b $64,$69,$04,$29,$63,$61,$73,$04,$29,$63,$61,$73,$02,$05,$62,$05
	dc.b $02,$65,$6F,$72,$69,$05,$2B,$63,$6D,$70,$69,$02,$04,$62,$08,$06
	dc.b $6D,$6F,$76,$65,$2E,$62,$20,$09,$38,$6D,$6F,$76,$65,$61,$2E,$6C
	dc.b $20,$08,$06,$6D,$6F,$76,$65,$2E,$6C,$20,$09,$06,$6D,$6F,$76,$65
	dc.b $61,$2E,$77,$20,$08,$06,$6D,$6F,$76,$65,$2E,$77,$20,$06,$21,$64
	dc.b $63,$2E,$77,$20,$08,$22,$69,$6C,$6C,$65,$67,$61,$6C,$06,$00,$72
	dc.b $65,$73,$65,$74,$04,$00,$6E,$6F,$70,$07,$07,$73,$74,$6F,$70,$20
	dc.b $23,$04,$00,$72,$74,$65,$06,$07,$72,$74,$64,$20,$23,$04,$00,$72
	dc.b $74,$73,$06,$00,$74,$72,$61,$70,$76,$04,$00,$72,$74,$72,$07,$23
	dc.b $6D,$6F,$76,$65,$63,$20,$07,$08,$73,$77,$61,$70,$20,$64,$08,$08
	dc.b $65,$78,$74,$2E,$77,$20,$64,$08,$08,$65,$78,$74,$2E,$6C,$20,$64
	dc.b $07,$09,$6C,$69,$6E,$6B,$20,$61,$07,$08,$75,$6E,$6C,$6B,$20,$61
	dc.b $09,$0A,$6D,$6F,$76,$65,$2E,$6C,$20,$61,$0D,$08,$6D,$6F,$76,$65
	dc.b $2E,$6C,$20,$75,$73,$70,$2C,$61,$09,$25,$65,$78,$74,$62,$2E,$6C
	dc.b $20,$64,$07,$0B,$74,$72,$61,$70,$20,$23,$0A,$0C,$6D,$6F,$76,$65
	dc.b $20,$73,$72,$2C,$2E,$0A,$24,$6D,$6F,$76,$65,$20,$63,$63,$72,$2C
	dc.b $07,$08,$62,$6B,$70,$74,$20,$23,$08,$0D,$6D,$6F,$76,$65,$2E,$62
	dc.b $20,$08,$0E,$6D,$6F,$76,$65,$2E,$77,$20,$09,$2F,$6C,$69,$6E,$6B
	dc.b $2E,$6C,$20,$61,$07,$0C,$6E,$62,$63,$64,$20,$2E,$06,$0C,$74,$61
	dc.b $73,$20,$2E,$05,$37,$6A,$73,$72,$20,$05,$37,$6A,$6D,$70,$20,$04
	dc.b $2D,$6D,$75,$6C,$04,$2E,$64,$69,$76,$06,$10,$6D,$6F,$76,$65,$6D
	dc.b $06,$0F,$6D,$6F,$76,$65,$6D,$06,$0C,$70,$65,$61,$20,$2E,$05,$0C
	dc.b $6E,$65,$67,$78,$04,$0C,$63,$6C,$72,$04,$0C,$6E,$65,$67,$04,$0C
	dc.b $6E,$6F,$74,$04,$2C,$74,$73,$74,$04,$11,$63,$68,$6B,$05,$12,$6C
	dc.b $65,$61,$20,$02,$14,$73,$05,$31,$74,$72,$61,$70,$03,$13,$64,$62
	dc.b $02,$14,$73,$05,$15,$61,$64,$64,$71,$05,$15,$73,$75,$62,$71,$02
	dc.b $17,$62,$08,$18,$6D,$6F,$76,$65,$71,$20,$23,$06,$19,$73,$62,$63
	dc.b $64,$20,$06,$30,$70,$61,$63,$6B,$20,$06,$30,$75,$6E,$70,$6B,$20
	dc.b $05,$11,$64,$69,$76,$75,$05,$11,$64,$69,$76,$73,$03,$1F,$6F,$72
	dc.b $05,$1E,$73,$75,$62,$61,$05,$19,$73,$75,$62,$78,$04,$1E,$73,$75
	dc.b $62,$05,$1C,$63,$6D,$70,$6D,$01,$1D,$06,$19,$61,$62,$63,$64,$20
	dc.b $05,$11,$6D,$75,$6C,$75,$05,$11,$6D,$75,$6C,$73,$05,$16,$65,$78
	dc.b $67,$20,$04,$1F,$61,$6E,$64,$05,$1E,$61,$64,$64,$61,$05,$19,$61
	dc.b $64,$64,$78,$04,$1E,$61,$64,$64,$07,$26,$62,$66,$74,$73,$74,$20
	dc.b $08,$27,$62,$66,$65,$78,$74,$75,$20,$07,$26,$62,$66,$63,$68,$67
	dc.b $20,$08,$27,$62,$66,$65,$78,$74,$73,$20,$07,$26,$62,$66,$63,$6C
	dc.b $72,$20,$07,$27,$62,$66,$66,$66,$6F,$20,$07,$26,$62,$66,$73,$65
	dc.b $74,$20,$07,$28,$62,$66,$69,$6E,$73,$20,$01,$20,$02,$36,$70,$02
	dc.b $32,$66,$02,$33,$66,$02,$34,$66,$07,$35,$66,$73,$61,$76,$65,$20
	dc.b $0A,$35,$66,$72,$65,$73,$74,$6F,$72,$65,$20,$06,$21,$64,$63,$2E
	dc.b $77,$20,$48,$E7,$1F,$1C,$2F,$2E,$00,$AE,$2F,$2E,$01,$36,$42,$AE
	dc.b $00,$AE,$42,$AE,$01,$36,$2F,$0A,$78,$03,$4B,$EA,$FF,$F4,$24,$4D
	dc.b $61,$00,$37,$74,$66,$46,$54,$4D,$48,$E7,$08,$04,$61,$00,$E0,$76
	dc.b $BB,$EF,$00,$08,$4C,$DF,$20,$10,$66,$2E,$43,$EE,$09,$A8,$12,$19
	dc.b $B2,$3C,$00,$5B,$67,$0C,$B2,$3C,$00,$3F,$67,$1C,$B2,$3C,$00,$0A
	dc.b $66,$EC,$58,$8F,$70,$00,$2D,$5F,$01,$36,$2D,$5F,$00,$AE,$24,$4D
	dc.b $4C,$DF,$38,$F8,$4A,$00,$4E,$75,$51,$CC,$FF,$BC,$2A,$5F,$55,$4D
	dc.b $70,$FF,$60,$E2,$2D,$4A,$00,$54,$60,$00,$08,$AC,$2D,$4A,$00,$54
	dc.b $08,$EE,$00,$07,$00,$5A,$50,$C3,$60,$00,$DC,$C8,$41,$EE,$05,$54
	dc.b $20,$3C,$4E,$71,$4E,$71,$20,$80,$21,$40,$00,$04,$31,$40,$00,$08
	dc.b $31,$7C,$4A,$FC,$00,$0A,$30,$12,$B0,$7C,$4A,$FC,$67,$C6,$02,$40
	dc.b $FF,$F0,$B0,$7C,$4E,$40,$67,$20,$02,$40,$FF,$C0,$B0,$7C,$4E,$80
	dc.b $67,$1C,$02,$40,$FF,$00,$B0,$7C,$61,$00,$67,$00,$00,$8E,$02,$40
	dc.b $F0,$00,$B0,$7C,$A0,$00,$66,$A4,$30,$9A,$60,$00,$00,$A0,$30,$1A
	dc.b $30,$80,$12,$00,$02,$01,$00,$38,$B2,$3C,$00,$10,$67,$00,$00,$8E
	dc.b $B2,$3C,$00,$28,$67,$2A,$B2,$3C,$00,$30,$67,$24,$B2,$3C,$00,$38
	dc.b $66,$1A,$12,$00,$02,$01,$00,$07,$67,$16,$B2,$3C,$00,$04,$64,$0C
	dc.b $B2,$3C,$00,$01,$66,$10,$21,$5A,$00,$02,$60,$60,$60,$00,$FF,$5E
	dc.b $31,$5A,$00,$02,$60,$56,$B2,$3C,$00,$02,$66,$0A,$20,$0A,$32,$1A
	dc.b $48,$C1,$D0,$81,$60,$30,$32,$1A,$10,$01,$48,$80,$48,$C0,$D0,$8A
	dc.b $55,$80,$34,$01,$ED,$5A,$02,$42,$00,$3C,$24,$36,$20,$10,$08,$01
	dc.b $00,$0B,$66,$02,$48,$C2,$D0,$82,$60,$0C,$30,$1A,$4A,$00,$67,$10
	dc.b $48,$80,$48,$C0,$D0,$8A,$30,$BC,$4E,$B9,$21,$40,$00,$02,$60,$0C
	dc.b $30,$1A,$48,$C0,$43,$F2,$00,$FE,$20,$09,$60,$EA,$2D,$4A,$05,$60
	dc.b $2F,$08,$2D,$5F,$00,$54,$08,$AE,$00,$07,$00,$5A,$50,$C3,$60,$00
	dc.b $DB,$C2
loc_0_00003D66:
	moveq.l #7,d0
	lea.l app_019E(a6),a0
loc_0_00003D6C:
	clr.w (a0)
	lea.l $0048(a0),a0
	dbf.w d0,loc_0_00003D6C
	rts
loc_0_00003D78:
	moveq.l #7,d0
	lea.l app_0198(a6),a0
loc_0_00003D7E:
	tst.w $0006(a0)
	beq.b loc_0_00003D9E
	movea.l (a0),a1
	cmpi.w #19196,(a1)
	beq.b loc_0_00003D94
	clr.w $0006(a0)
	clr.l (a0)
	bra.b loc_0_00003D9E
loc_0_00003D94:
	lea.l $0048(a0),a0
	dbf.w d0,loc_0_00003D7E
	moveq.l #-1,d0
loc_0_00003D9E:
	rts
loc_0_00003DA0:
	move.l a1,-(a7)
	bsr.w loc_0_00003E3C
	bne.b loc_0_00003DAC
	bsr.w loc_0_00003E6E
loc_0_00003DAC:
	bsr.b loc_0_00003D78
	movea.l (a7)+,a1
	lea.l loc_0_000085EE(pc),a2
	bne.b loc_0_00003E06
	move.l a1,d0
	btst #0,d0
	lea.l loc_0_000085D6(pc),a2
	bne.b loc_0_00003E06
	cmp.b #$4,d3
	bne.b loc_0_00003DD6
	move.l a0,-(a7)
	lea.l $000C(a0),a0
loc_0_00003DCE:
	move.b (a4)+,(a0)+
	bne.b loc_0_00003DCE
	movea.l (a7)+,a0
	bra.b loc_0_00003DE0
loc_0_00003DD6:
	bsr.w loc_0_000073A4
	lea.l loc_0_000085CE(pc),a2
	bne.b loc_0_00003E06
loc_0_00003DE0:
	bsr.b loc_0_00003E10
	move.w (a1),$0004(a0)
	move.w #$4AFC,(a1)
	cmpi.w #19196,(a1)
	lea.l loc_0_000085E0(pc),a2
	bne.b loc_0_00003E04
	bsr.b loc_0_00003E26
	move.l a1,(a0)
	move.l d2,$0008(a0)
	move.w d3,$0006(a0)
	moveq.l #0,d0
	rts
loc_0_00003E04:
	bsr.b loc_0_00003E26
loc_0_00003E06:
	movea.l a2,a0
	bsr.w loc_0_00001AD6
	moveq.l #-1,d0
	rts
loc_0_00003E10:
	movem.l d0-d1/a0-a1,-(a7)
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOForbid(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,d0-d1/a0-a1
	rts
loc_0_00003E26:
	movem.l d0-d1/a0-a1,-(a7)
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,d0-d1/a0-a1
	rts
loc_0_00003E3C:
	moveq.l #7,d0
	lea.l app_0198(a6),a0
loc_0_00003E42:
	cmpa.l (a0),a1
	bne.b loc_0_00003E50
	tst.w $0006(a0)
	beq.b loc_0_00003E50
	moveq.l #0,d0
	rts
loc_0_00003E50:
	lea.l $0048(a0),a0
	dbf.w d0,loc_0_00003E42
	moveq.l #-1,d0
	rts
loc_0_00003E5C:
	moveq.l #7,d0
	lea.l app_0198(a6),a0
loc_0_00003E62:
	bsr.b loc_0_00003E6E
	lea.l $0048(a0),a0
	dbf.w d0,loc_0_00003E62
	rts
loc_0_00003E6E:
	bsr.b loc_0_00003E10
	tst.w $0006(a0)
	beq.b loc_0_00003E86
	clr.w $0006(a0)
	movea.l (a0),a1
	cmpi.w #19196,(a1)
	bne.b loc_0_00003E86
	move.w $0004(a0),(a1)
loc_0_00003E86:
	bra.b loc_0_00003E26
	dc.b $61,$86,$2D,$49,$05,$64,$3D,$51,$05,$68,$32,$BC,$4A,$FC,$60,$8E
loc_0_00003E98:
	movea.l $0004.w,a0
	move.l $003E(a0),app_0008(a6)
	lea.l $0142(a0),a1
	move.l a1,app_000C(a6)
	rts
	dc.b $B5,$EE,$00,$08,$65,$16,$B5,$FC,$00,$F8,$00,$00,$65,$14,$B5,$FC
	dc.b $01,$00,$00,$00,$64,$0C,$4B,$FA,$00,$44,$4E,$75,$4B,$FA,$00,$26
	dc.b $4E,$75,$28,$6E,$00,$0C,$20,$14,$67,$16,$28,$40,$4A,$94,$67,$10
	dc.b $B5,$CC,$65,$F2,$B5,$EC,$00,$18,$64,$EC,$4B,$FA,$00,$4A,$4E,$75
	dc.b $95,$CA,$60,$D8,$52,$8A,$B5,$EE,$00,$08,$64,$02,$4E,$75,$4B,$FA
	dc.b $00,$0C,$24,$7C,$00,$F8,$00,$00,$B2,$01,$4E,$75,$52,$8A,$B5,$FC
	dc.b $01,$00,$00,$00,$64,$02,$4E,$75,$28,$6E,$00,$0C,$4A,$94,$67,$32
	dc.b $28,$54,$4A,$94,$67,$2C,$B9,$EE,$00,$08,$65,$F4,$24,$4C,$4B,$FA
	dc.b $00,$06,$B2,$01,$4E,$75,$52,$8A,$B5,$EC,$00,$18,$64,$02,$4E,$75
	dc.b $28,$54,$4A,$94,$67,$0C,$B9,$EE,$00,$08,$65,$F4,$B2,$01,$24,$4C
	dc.b $4E,$75,$95,$CA,$4B,$FA,$FF,$9E,$B2,$01,$4E,$75
loc_0_00003F58:
	lea.l app_03DE(a6),a0
	move.l a0,app_0550(a6)
	moveq.l #4,d0
loc_0_00003F62:
	clr.l $0046(a0)
	lea.l $004A(a0),a0
	dbf.w d0,loc_0_00003F62
	rts
loc_0_00003F70:
	movea.l app_0550(a6),a0
	lea.l app_0010(a6),a1
	moveq.l #15,d0
loc_0_00003F7A:
	move.l (a1)+,(a0)+
	dbf.w d0,loc_0_00003F7A
	move.l app_0050(a6),(a0)+
	move.w app_005A(a6),(a0)+
	move.l $0054(a6),(a0)+
	lea.l app_0550(a6),a1
	cmpa.l a0,a1
	bne.b loc_0_00003F98
	lea.l app_03DE(a6),a0
loc_0_00003F98:
	move.l a0,app_0550(a6)
	rts
	dc.b $45,$FA,$46,$C0,$61,$00,$1F,$08,$17,$7C,$00,$10,$00,$35,$4A,$AE
	dc.b $04,$24,$67,$00,$00,$F2,$78,$30,$7A,$07,$74,$06,$60,$02,$74,$08
	dc.b $61,$00,$2A,$B6,$12,$04,$61,$00,$18,$F4,$52,$04,$51,$CD,$FF,$F0
	dc.b $61,$00,$2A,$C4,$41,$EE,$03,$DE,$28,$48,$45,$EE,$05,$50,$4A,$A8
	dc.b $00,$90,$67,$16,$4A,$A8,$00,$DA,$67,$10,$4A,$A8,$01,$24,$67,$0A
	dc.b $4A,$A8,$01,$6E,$67,$04,$28,$6E,$05,$50,$72,$0C,$61,$00,$2A,$5E
	dc.b $76,$07,$61,$00,$2A,$80,$24,$1C,$61,$00,$2A,$92,$51,$CB,$FF,$F4
	dc.b $61,$00,$10,$84,$72,$0D,$61,$00,$2A,$44,$76,$07,$61,$00,$2A,$66
	dc.b $24,$1C,$61,$00,$2A,$78,$51,$CB,$FF,$F4,$61,$00,$10,$6A,$72,$02
	dc.b $61,$00,$2A,$2A,$24,$1C,$61,$00,$2A,$64,$61,$00,$2A,$48,$72,$01
	dc.b $61,$00,$2A,$1A,$34,$14,$61,$00,$2A,$5C,$61,$00,$2A,$38,$38,$1C
	dc.b $61,$00,$26,$52,$61,$00,$10,$40,$72,$00,$61,$00,$2A,$00,$24,$14
	dc.b $61,$00,$2A,$3A,$61,$00,$2A,$1E,$14,$2B,$00,$35,$20,$14,$61,$00
	dc.b $3E,$8A,$67,$04,$61,$00,$3B,$64,$52,$02,$61,$00,$29,$FC,$2F,$0A
	dc.b $24,$5C,$61,$00,$29,$24,$61,$00,$17,$B0,$24,$5F,$61,$00,$10,$08
	dc.b $B5,$CC,$66,$04,$49,$EE,$03,$DE,$B9,$EE,$05,$50,$67,$08,$4A,$AC
	dc.b $00,$46,$66,$00,$FF,$56,$61,$00,$0F,$FE,$60,$00,$1C,$F2
loc_0_000040AC:
	movem.l d0-d2/a0-a2,-(a7)
	movea.l app_05B4(a6),a0
	movea.l wd_UserPort(a0),a0
	bsr.w loc_0_000042D6
	beq.b loc_0_000040F2
	move.l $0014(a1),d1
	cmp.l #$400,d1
	bne.b loc_0_000040E6
	bsr.w loc_0_000041F4
	bmi.b loc_0_000040E6
	cmp.w #$1B,d1
	bne.b loc_0_000040E6
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOReplyMsg(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	bra.b loc_0_000040F4
loc_0_000040E6:
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOReplyMsg(a6)
	movea.l (a7)+,a6
loc_0_000040F2:
	moveq.l #-1,d0
loc_0_000040F4:
	movem.l (a7)+,d0-d2/a0-a2
	rts
loc_0_000040FA:
	movem.l d0/d2/a0-a2,-(a7)
loc_0_000040FE:
	movea.l app_05B4(a6),a0
	movea.l wd_UserPort(a0),a0
	bsr.w loc_0_000042D6
	beq.b loc_0_0000411A
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOReplyMsg(a6)
	movea.l (a7)+,a6
	bra.b loc_0_000040FE
loc_0_0000411A:
	movem.l (a7)+,d0/d2/a0-a2
	rts
loc_0_00004120:
	bsr.b loc_0_000040FA
	bra.b loc_0_0000412C
	dc.b $48,$E7,$B1,$F0,$50,$C7,$60,$06
loc_0_0000412C:
	movem.l d0/d2-d3/d7/a0-a3,-(a7)
	sf.b d7
	tst.l app_0570(a6)
	beq.b loc_0_0000413C
	bsr.w loc_0_00005940
loc_0_0000413C:
	tst.b d7
	beq.b loc_0_0000415E
	moveq.l #0,d1
	move.b loc_0_0000895E(pc),d0
	bset d0,d1
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSetSignal(a6)
	movea.l (a7)+,a6
	move.b loc_0_0000895E(pc),d1
	btst d1,d0
	bne.b loc_0_0000419A
loc_0_0000415E:
	movea.l app_05B4(a6),a0
	movea.l wd_UserPort(a0),a0
	bsr.w loc_0_000042D6
	bne.b loc_0_000041B4
	moveq.l #0,d0
	movea.l app_05B4(a6),a0
	movea.l wd_UserPort(a0),a0
	move.b $000F(a0),d1
	bset d1,d0
	tst.b d7
	beq.b loc_0_00004186
	move.b loc_0_0000895E(pc),d1
	bset d1,d0
loc_0_00004186:
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOWait(a6)
	movea.l (a7)+,a6
	move.b loc_0_0000895E(pc),d1
	btst d1,d0
	beq.b loc_0_000041A6
loc_0_0000419A:
	movem.l d4-d7/a0-a5,-(a7)
	bsr.w loc_0_0000176C
	movem.l (a7)+,d4-d7/a0-a5
loc_0_000041A6:
	movea.l app_05B4(a6),a0
	movea.l wd_UserPort(a0),a0
	bsr.w loc_0_000042D6
	beq.b loc_0_0000413C
loc_0_000041B4:
	move.l $0014(a1),d1
	cmp.l #$400,d1
	bne.b loc_0_000041E4
	bsr.b loc_0_000041F4
	smi.b -(a7)
	move.w d1,-(a7)
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOReplyMsg(a6)
	movea.l (a7)+,a6
	move.w (a7)+,d1
	move.b (a7)+,d0
	tst.w d1
	beq.w loc_0_0000413C
	tst.b d0
	movem.l (a7)+,d0/d2-d3/d7/a0-a3
	rts
loc_0_000041E4:
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOReplyMsg(a6)
	movea.l (a7)+,a6
	bra.w loc_0_0000413C
loc_0_000041F4:
	move.l a1,-(a7)
	lea.l app_0848(a6),a0
	move.l a0,-(a7)
	clr.l (a0)+
	move.b #$1,(a0)+
	clr.b (a0)+
	move.w $0018(a1),(a0)+
	move.w $001A(a1),(a0)+
	movea.l $001C(a1),a1
	move.l (a1),(a0)
	movea.l (a7)+,a0
	lea.l app_0866(a6),a1
	clr.l (a1)
	moveq.l #4,d1
	suba.l a2,a2
	move.l a6,-(a7)
	movea.l app_ConsoleDevice(a6),a6
	jsr _LVORawKeyConvert(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	tst.l d0
	ble.b loc_0_0000428E
	move.w $001A(a1),d3
	lea.l app_0866(a6),a0
	move.b (a0)+,d1
	subq.l #1,d0
	beq.b loc_0_00004296
	cmp.b #$9B,d1
	bne.b loc_0_00004292
	move.b (a0)+,d2
	lea.l loc_0_000042C0(pc),a2
	subq.l #1,d0
	beq.b loc_0_00004276
	lea.l loc_0_000042CF(pc),a2
	subq.l #1,d0
	beq.b loc_0_00004264
	lea.l loc_0_000042D4(pc),a2
	move.b (a0)+,d2
	cmpi.b #126,(a0)
	beq.b loc_0_00004276
	bra.b loc_0_00004292
loc_0_00004264:
	move.w #$87,d1
	cmp.b #$3F,d2
	beq.b loc_0_00004280
	cmp.b #$20,d2
	bne.b loc_0_00004292
	move.b (a0)+,d2
loc_0_00004276:
	move.b (a2)+,d0
	beq.b loc_0_00004292
	move.b (a2)+,d1
	cmp.b d2,d0
	bne.b loc_0_00004276
loc_0_00004280:
	cmp.b #$D,d1
	bne.b loc_0_00004288
	moveq.l #10,d1
loc_0_00004288:
	andi.w #255,d1
	rts
loc_0_0000428E:
	moveq.l #0,d1
	rts
loc_0_00004292:
	moveq.l #63,d1
	rts
loc_0_00004296:
	btst #7,d3
	beq.b loc_0_00004280
	cmp.b #$61,d1
	bcs.b loc_0_000042B8
	cmp.b #$7B,d1
	bcc.b loc_0_000042B8
	andi.b #223,d1
	cmp.b #$58,d1
	bne.b loc_0_000042B8
	move.w #$86,d1
	rts
loc_0_000042B8:
	andi.w #255,d1
	moveq.l #-1,d0
	rts
loc_0_000042C0:
	dc.b $41,$82,$42,$83,$43,$85,$44,$84,$54,$80,$53,$81,$5A,$88,$00
loc_0_000042CF:
	dc.b $40,$8A,$41,$89,$00
loc_0_000042D4:
	dc.b $00,$00
loc_0_000042D6:
	movem.l d2/a2,-(a7)
	movea.l a0,a2
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOGetMsg(a6)
	movea.l (a7)+,a6
	move.l d0,d2
	beq.b loc_0_0000436A
	movea.l d0,a1
	cmpi.l #1024,MN_SIZE(a1)
	bne.b loc_0_0000436A
	btst.b #1,$001A(a1)
	beq.b loc_0_0000436A
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOForbid(a6)
	movea.l (a7)+,a6
	movea.l $0014(a2),a1
	movea.l d2,a2
	bra.b loc_0_00004356
loc_0_00004314:
	cmpi.l #1024,$0014(a1)
	bne.b loc_0_00004354
	btst.b #1,$001A(a1)
	beq.b loc_0_00004354
	move.w $0018(a1),d0
	cmp.w $0018(a2),d0
	bne.b loc_0_00004354
	movem.l a0-a1,-(a7)
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVORemove(a6)
	movea.l (a7)+,a6
	movea.l $0004(a7),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOReplyMsg(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,a0-a1
loc_0_00004354:
	movea.l a0,a1
loc_0_00004356:
	movea.l (a1),a0
	move.l a0,d0
	bne.b loc_0_00004314
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	movea.l d2,a1
loc_0_0000436A:
	move.l d2,d0
	movem.l (a7)+,d2/a2
	rts
	dc.b $00,$3E,$CB,$9C,$00,$3C,$CB,$AC,$00,$2E,$CB,$E6,$00,$2C,$CB,$FE
	dc.b $00,$1B,$C7,$5C,$00,$41,$CC,$54,$00,$42,$05,$26,$00,$44,$09,$CC
	dc.b $00,$47,$01,$A6,$00,$48,$FC,$06,$00,$49,$09,$60,$00,$4C,$3D,$32
	dc.b $00,$4D,$C7,$CE,$00,$4E,$02,$DC,$00,$4F,$CF,$00,$00,$50,$0D,$24
	dc.b $01,$52,$0A,$D0,$00,$53,$0A,$44,$01,$55,$01,$72,$00,$56,$00,$74
	dc.b $00,$57,$09,$76,$01,$01,$01,$32,$02,$02,$00,$34,$00,$03,$00,$80
	dc.b $00,$0B,$00,$4E,$03,$0C,$11,$36,$00,$10,$05,$A2,$02,$11,$10,$7E
	dc.b $01,$12,$00,$E2,$01,$13,$01,$32,$01,$14,$00,$AA,$00,$15,$11,$04
	dc.b $04,$18,$10,$C8,$01,$19,$00,$DE,$01,$1A,$00,$DA,$00,$00,$0C,$2B
	dc.b $00,$03,$00,$34,$66,$18,$22,$6B,$00,$38,$48,$7A,$1A,$D0,$61,$00
	dc.b $FA,$2A,$67,$00,$FA,$58,$74,$01,$76,$01,$60,$00,$F9,$82,$4E,$75
	dc.b $41,$FA,$42,$00,$61,$00,$D7,$00,$66,$F4,$61,$00,$FA,$2E,$60,$00
	dc.b $1A,$AC,$61,$00,$1A,$64,$41,$FA,$43,$F1,$43,$FA,$43,$FA,$61,$00
	dc.b $D6,$54,$61,$00,$FC,$DA,$61,$00,$1A,$24,$60,$00,$19,$4E,$4A,$2E
	dc.b $01,$34,$67,$0C,$41,$FA,$43,$A8,$61,$00,$D6,$CC,$67,$02,$4E,$75
loc_0_00004462:
	bsr.w loc_0_00003E5C
	bsr.b loc_0_0000446C
	bra.w loc_0_0000039E
loc_0_0000446C:
	move.l loc_0_000088F6(pc),d1
	beq.b loc_0_00004494
	clr.l loc_0_000088F6.l
	clr.l app_00AA(a6)
	tst.b app_0134(a6)
	bne.b loc_0_00004494
	tst.l app_015E(a6)
	bne.b loc_0_00004494
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$009C(a6)
	movea.l (a7)+,a6
loc_0_00004494:
	rts
	dc.b $61,$0A,$61,$00,$2E,$D0,$67,$00,$F7,$C2,$4E,$75,$4A,$AE,$00,$50
	dc.b $67,$14,$08,$2E,$00,$00,$00,$57,$66,$0C,$24,$6E,$00,$54,$61,$00
	dc.b $2E,$B4,$66,$02,$4E,$75,$58,$8F,$41,$FA,$41,$03,$60,$00,$D6,$12
	dc.b $61,$DA,$32,$12,$08,$AE,$00,$07,$00,$5A,$50,$C3,$60,$00,$D4,$36
	dc.b $61,$CA,$50,$C3,$08,$EE,$00,$07,$00,$5A,$22,$6E,$00,$54,$61,$00
	dc.b $F9,$56,$66,$00,$D4,$3C,$0C,$68,$00,$03,$00,$06,$66,$00,$D4,$32
	dc.b $60,$00,$D4,$12,$61,$A6,$08,$AE,$00,$07,$00,$5A,$61,$00,$24,$60
	dc.b $22,$4A,$76,$01,$74,$01,$61,$00,$F8,$92,$66,$06,$50,$C3,$60,$00
	dc.b $D3,$F4,$4E,$75,$61,$86,$61,$00,$24,$46,$2D,$4A,$00,$54,$74,$54
	dc.b $61,$00,$C8,$BE,$60,$00,$19,$B2,$41,$FA,$40,$D4,$61,$00,$C3,$00
	dc.b $66,$8E,$4E,$75,$0C,$2B,$00,$02,$00,$34,$66,$02,$4E,$75,$76,$05
	dc.b $61,$00,$D4,$F6,$41,$FA,$41,$1C,$61,$00,$25,$1A,$20,$6E,$00,$DE
	dc.b $72,$54,$0C,$28,$00,$04,$00,$34,$67,$40,$76,$00,$4C,$AB,$00,$0C
	dc.b $00,$0A,$86,$EE,$00,$D8,$61,$00,$12,$00,$61,$00,$FB,$AE,$6B,$FA
	dc.b $B2,$3C,$00,$1B,$67,$00,$01,$00,$02,$01,$00,$DF,$B2,$3C,$00,$42
	dc.b $67,$18,$B2,$3C,$00,$57,$67,$12,$B2,$3C,$00,$4C,$67,$0C,$B2,$3C
	dc.b $00,$54,$67,$06,$B2,$3C,$00,$49,$66,$D0,$1D,$41,$0B,$8F,$61,$00
	dc.b $13,$14,$61,$00,$D4,$2A,$49,$EE,$0A,$D4,$42,$14,$78,$00,$7C,$01
	dc.b $61,$00,$14,$0A,$66,$00,$00,$C0,$4A,$14,$67,$00,$00,$BA,$61,$00
	dc.b $D4,$0E,$4B,$EE,$0B,$8F,$1A,$1D,$BA,$3C,$00,$49,$67,$64,$BA,$3C
	dc.b $00,$54,$67,$5E,$42,$2D,$FF,$FC,$12,$1C,$4A,$14,$66,$18,$02,$01
	dc.b $00,$DF,$B2,$3C,$00,$4C,$67,$0A,$B2,$3C,$00,$57,$66,$08,$7C,$02
	dc.b $60,$36,$7C,$04,$60,$32,$53,$4C,$61,$00,$25,$70,$66,$20,$BA,$3C
	dc.b $00,$42,$67,$0E,$BA,$3C,$00,$57,$67,$04,$2A,$C2,$60,$06,$3A,$C2
	dc.b $60,$02,$1A,$C2,$4A,$01,$67,$10,$B2,$3C,$00,$2C,$67,$BA,$61,$00
	dc.b $18,$2E,$49,$EE,$0A,$D4,$60,$88,$41,$EE,$0B,$90,$20,$0D,$90,$88
	dc.b $60,$34,$4A,$2E,$0B,$8D,$41,$FA,$40,$D6,$61,$00,$05,$5A,$67,$04
	dc.b $5A,$EE,$0B,$8D,$20,$4C,$4A,$2E,$0B,$8D,$67,$0C,$12,$1C,$61,$00
	dc.b $30,$D8,$1A,$C1,$66,$F6,$60,$04,$1A,$DC,$66,$FC,$20,$0C,$90,$88
	dc.b $53,$80,$42,$2E,$0A,$D4,$1D,$40,$0B,$8C,$53,$06,$1D,$46,$0B,$8E
	dc.b $61,$00,$17,$24,$60,$08,$42,$6E,$0B,$8C,$60,$00,$17,$1A,$61,$00
	dc.b $BE,$A4,$50,$EE,$00,$E5,$72,$0E,$61,$00,$23,$CA,$20,$6E,$00,$DE
	dc.b $24,$68,$00,$38,$10,$28,$00,$34,$38,$28,$00,$36,$B0,$3C,$00,$02
	dc.b $67,$30,$1F,$00,$61,$00,$F8,$00,$10,$1F,$47,$EE,$0B,$8C,$76,$00
	dc.b $16,$1B,$67,$1E,$52,$4B,$7C,$00,$1C,$1B,$B0,$3C,$00,$04,$67,$00
	dc.b $00,$BA,$61,$00,$00,$12,$10,$1B,$B0,$3C,$00,$49,$66,$0C,$60,$00
	dc.b $01,$20,$60,$00,$BE,$50,$D5,$C6
loc_0_000046DE:
	dc.b $4E,$D5,$28,$06,$46,$84,$22,$0A,$C8,$81,$24,$44,$18,$1B,$53,$03
	dc.b $7A,$00,$4A,$2E,$0B,$8D,$67,$0C,$60,$36,$61,$00,$F9,$B2,$66,$04
	dc.b $2E,$0A,$60,$6A,$52,$45,$67,$F2,$61,$D4,$B8,$12,$66,$F6,$2E,$0A
	dc.b $4A,$03,$67,$5A,$20,$4B,$10,$03,$4E,$B9
	dc.l loc_0_000046DE
	dc.b $67,$0C,$12,$12,$B2,$18,$66,$06,$53,$00,$66,$EE,$60,$42,$24,$47
	dc.b $60,$D4,$60,$0A,$61,$00,$F9,$7A,$66,$04,$2E,$0A,$60,$32,$52,$45
	dc.b $67,$F2,$61,$9C,$12,$12,$61,$00,$2F,$EA,$B8,$01,$66,$F0,$2E,$0A
	dc.b $4A,$03,$67,$1C,$20,$4B,$10,$03,$61,$88,$67,$10,$12,$12,$61,$00
	dc.b $2F,$D2,$B2,$18,$66,$06,$53,$00,$66,$EE,$60,$04,$24,$47,$60,$CE
	dc.b $20,$6E,$00,$DE,$21,$47,$00,$38,$61,$00,$BD,$CE,$60,$00,$17,$64
	dc.b $60,$00,$BD,$C6,$0C,$1B,$00,$54,$66,$F6,$61,$00,$21,$50,$67,$F0
	dc.b $20,$4A,$4A,$2E,$0B,$8D,$66,$32,$12,$18,$B2,$3C,$00,$0A,$67,$EA
	dc.b $B2,$13,$66,$F4,$48,$E7,$10,$90,$52,$8B,$53,$43,$67,$0A,$B7,$08
	dc.b $67,$F8,$4C,$DF,$09,$08,$60,$E0,$4C,$DF,$09,$08,$26,$6E,$00,$DE
	dc.b $27,$4A,$00,$38,$37,$44,$00,$36,$60,$AE,$12,$18,$B2,$3C,$00,$0A
	dc.b $67,$B8,$61,$00,$2F,$5E,$B2,$13,$66,$F0,$48,$E7,$10,$90,$52,$8B
	dc.b $53,$43,$67,$D4,$12,$18,$61,$00,$2F,$4A,$B2,$1B,$67,$F2,$4C,$DF
	dc.b $09,$08,$60,$D6,$2E,$0A,$60,$00,$FF,$78,$20,$0A,$08,$00,$00,$00
	dc.b $67,$04,$61,$00,$FE,$DC,$22,$4A,$45,$EA,$00,$09,$61,$00,$FE,$D2
	dc.b $C5,$49,$93,$CA,$B3,$FC,$00,$00,$00,$0A,$67,$08,$45,$EA,$00,$09
	dc.b $61,$00,$FE,$BE,$61,$00,$F8,$8A,$67,$CA,$48,$E7,$00,$0C,$2A,$4A
	dc.b $48,$E7,$02,$20,$61,$00,$D4,$46,$2C,$1F,$70,$00,$10,$2E,$0B,$8C
	dc.b $53,$00,$43,$EE,$09,$A8,$41,$EE,$0B,$90,$14,$18,$4A,$2E,$0B,$8D
	dc.b $66,$3A,$12,$19,$B4,$01,$67,$08,$B2,$3C,$00,$0A,$66,$F4,$60,$16
	dc.b $4A,$00,$67,$20,$48,$E7,$80,$C0,$53,$40,$B3,$08,$56,$C8,$FF,$FC
	dc.b $4C,$DF,$03,$01,$67,$0E,$4C,$DF,$34,$00,$61,$00,$FE,$64,$61,$00
	dc.b $FE,$60,$60,$82,$2E,$1F,$50,$8F,$60,$00,$FE,$E6,$12,$19,$61,$00
	dc.b $2E,$A2,$B4,$01,$67,$08,$B2,$3C,$00,$0A,$66,$F0,$60,$D8,$4A,$00
	dc.b $67,$E2,$48,$E7,$80,$C0,$53,$40,$12,$19,$61,$00,$2E,$86,$B2,$18
	dc.b $56,$C8,$FF,$F6,$60,$BA,$41,$FA,$3C,$B6,$76,$04,$61,$00,$D1,$C4
	dc.b $61,$00,$11,$02,$66,$00,$14,$DA,$4A,$14,$67,$00,$14,$D4,$41,$EE
	dc.b $0A,$D4,$74,$00,$12,$18,$67,$1E,$B2,$3C,$00,$2C,$66,$F6,$28,$48
	dc.b $2F,$08,$61,$00,$22,$7C,$20,$5F,$67,$0A,$49,$EE,$0A,$D4,$61,$00
	dc.b $10,$D6,$60,$D0,$42,$20,$61,$2E,$66,$18,$2D,$4B,$07,$E0,$2D,$4B
	dc.b $06,$50,$2D,$4B,$06,$9A,$D7,$C4,$53,$8B,$2D,$4B,$07,$E4,$60,$00
	dc.b $15,$D2,$4E,$75,$76,$04,$61,$00,$D1,$6A,$61,$00,$10,$A8,$66,$5A
	dc.b $4A,$14,$67,$56,$74,$00,$2F,$02,$61,$00,$14,$76,$4B,$EE,$0A,$D4
	dc.b $24,$1F
loc_0_0000492E:
	move.l d2,-(a7)
	bsr.w loc_0_000073E2
	movea.l (a7)+,a0
	bne.b loc_0_00004966
	move.l a0,-(a7)
	bsr.w loc_0_000073EC
	move.l (a7)+,d0
	bne.b loc_0_00004954
	move.l d4,d0
	addq.l #1,d0
	bsr.w loc_0_00008160
	beq.b loc_0_00004964
	move.b #$A,$0(a0,d4.l)
	move.l a0,d0
loc_0_00004954:
	movea.l d0,a3
	movea.l d0,a0
	bsr.w loc_0_0000742A
	bsr.w loc_0_00007474
	moveq.l #0,d0
	rts
loc_0_00004964:
	moveq.l #103,d0
loc_0_00004966:
	move.w d0,-(a7)
	bsr.w loc_0_00007474
	move.w (a7)+,d0
	bsr.w loc_0_00001B04
	moveq.l #-1,d0
	rts
	dc.b $61,$00,$14,$24,$70,$FF,$4E,$75,$76,$10,$41,$FA,$3D,$44,$61,$00
	dc.b $D0,$F8,$41,$FA,$3F,$05,$4A,$2E,$05,$85,$61,$00,$02,$0A,$67,$00
	dc.b $00,$06,$5A,$EE,$05,$85,$41,$FA,$3E,$CE,$61,$00,$20,$C8,$72,$4E
	dc.b $4A,$2E,$05,$84,$67,$0A,$72,$44,$4A,$2E,$05,$84,$6A,$02,$72,$48
	dc.b $61,$00,$0F,$02,$53,$6B,$00,$0A,$61,$00,$02,$28,$61,$00,$F7,$68
	dc.b $6B,$FA,$B2,$3C,$00,$1B,$67,$00,$01,$CA,$B2,$3C,$00,$0A,$67,$2A
	dc.b $02,$01,$00,$DF,$70,$01,$B2,$3C,$00,$44,$67,$10,$70,$00,$B2,$3C
	dc.b $00,$4E,$67,$08,$70,$FF,$B2,$3C,$00,$48,$66,$D0,$1D,$40,$05,$84
	dc.b $61,$00,$0E,$C2,$61,$00,$CF,$D8,$60,$08,$61,$00,$01,$E6,$61,$00
	dc.b $CF,$CE,$41,$FA,$3E,$A1,$4A,$2E,$05,$86,$61,$00,$01,$8A,$67,$00
	dc.b $00,$06,$5A,$EE,$05,$86,$41,$FA,$3C,$D7,$4A,$2E,$00,$E6,$61,$00
	dc.b $01,$76,$67,$00,$00,$06,$5A,$EE,$00,$E6,$41,$FA,$3C,$F4,$61,$00
	dc.b $20,$34,$61,$00,$CF,$9A,$49,$EE,$0A,$D4,$18,$FC,$00,$5C,$72,$00
	dc.b $32,$2E,$08,$16,$45,$FA,$D0,$D8,$61,$00,$20,$90,$42,$14,$49,$EE
	dc.b $0A,$D4,$61,$00,$04,$C2,$49,$EE,$0A,$D4,$61,$00,$0F,$60,$66,$00
	dc.b $01,$32,$61,$00,$20,$F2,$66,$EE,$B4,$BC,$00,$00,$00,$08,$65,$E6
	dc.b $B4,$BC,$00,$00,$00,$78,$64,$DE,$3D,$42,$08,$16,$61,$00,$CF,$50
	dc.b $41,$FA,$3C,$4A,$4A,$2E,$01,$48,$61,$00,$01,$0C,$67,$04,$5A,$EE
	dc.b $01,$48,$41,$FA,$3E,$33,$4A,$2E,$05,$87,$61,$00,$00,$FA,$67,$04
	dc.b $5A,$EE,$05,$87,$41,$FA,$3D,$B0,$10,$3A,$B5,$77,$61,$00,$00,$E8
	dc.b $67,$06,$5A,$F9
	dc.l loc_0_00000027
	dc.b $41,$FA,$3D,$57,$61,$00,$1F,$A6,$61,$00,$CF,$0C,$49,$EE,$0A,$D4
	dc.b $41,$EE,$08,$84,$22,$4C,$12,$D8,$66,$FC,$61,$00,$04,$42,$61,$00
	dc.b $0E,$E4,$66,$00,$00,$B6,$49,$EE,$0A,$D4,$4A,$14,$67,$22,$43,$EE
	dc.b $08,$84,$20,$4C,$B3,$08,$66,$08,$4A,$28,$FF,$FF,$66,$F6,$60,$18
	dc.b $41,$EE,$0A,$D4,$61,$00,$29,$E8,$67,$0E,$61,$00,$13,$4A,$60,$CE
	dc.b $61,$00,$2A,$1C,$42,$2E,$08,$84,$61,$00,$CE,$BC,$61,$00,$CE,$B8
	dc.b $41,$FA,$3C,$B4,$61,$00,$1F,$46,$61,$00,$00,$C0,$61,$00,$F5,$F4
	dc.b $6B,$FA,$02,$01,$00,$DF,$B2,$3C,$00,$59,$66,$5E,$41,$FA,$01,$77
	dc.b $61,$00,$28,$76,$66,$4A,$41,$FA,$B4,$DE,$50,$D8,$10,$EE,$01,$48
	dc.b $10,$EE,$00,$E6,$52,$88,$30,$EE,$08,$16,$41,$FA,$B5,$18,$10,$EE
	dc.b $05,$84,$10,$EE,$05,$85,$10,$EE,$05,$86,$10,$EE,$05,$87,$30,$EE
	dc.b $00,$F0,$41,$FA,$B4,$C0,$43,$EE,$08,$84,$10,$D9,$66,$FC,$41,$FA
	dc.b $B4,$A6,$78,$54,$61,$00,$28,$BE,$66,$06,$61,$00,$28,$EA,$60,$0A
	dc.b $2F,$00,$61,$06,$20,$1F,$60,$00,$CF,$6E,$60,$00,$12,$02,$56,$E7
	dc.b $61,$00,$1E,$CA,$72,$4E,$4A,$1F,$67,$02,$72,$59,$61,$00,$0D,$0E
	dc.b $53,$6B,$00,$0A,$61,$34,$61,$00,$F5,$6A,$6B,$FA,$B2,$3C,$00,$1B
	dc.b $67,$44,$B2,$3C,$00,$0A,$67,$36,$02,$01,$00,$DF,$B2,$3C,$00,$59
	dc.b $67,$06,$B2,$3C,$00,$4E,$66,$DE,$3F,$01,$61,$00,$0C,$E0,$61,$00
	dc.b $CD,$F6,$32,$1F,$B2,$3C,$00,$4F,$4E,$75,$76,$00,$4C,$AB,$00,$0C
	dc.b $00,$0A,$86,$EE,$00,$D8,$61,$00,$0B,$78,$72,$00,$4E,$75,$61,$EA
	dc.b $61,$00,$CD,$D4,$60,$F4,$58,$8F,$60,$00,$11,$94
loc_0_00004C0A:
	st.b app_0591(a6)
	tst.b app_0162(a6)
	beq.b loc_0_00004C26
	tst.b loc_0_00000024.l
	bne.b loc_0_00004C62
	move.b app_0147(a6),loc_0_00000027.l
	bra.b loc_0_00004C62
loc_0_00004C26:
	move.b app_0147(a6),loc_0_00000027.l
	lea.l loc_0_00004CB3(pc),a5
	bsr.w loc_0_000073E2
	beq.b loc_0_00004C4E
	movea.l h0dl_DOSBase.l,a0
	moveq.l #-1,d0
	move.l d0,$00B8(a0)
	lea.l loc_0_00004CA8(pc),a5
	bsr.w loc_0_000073E2
	bne.b loc_0_00004C62
loc_0_00004C4E:
	lea.l loc_0_00000024(pc),a0
	moveq.l #84,d4
	bsr.w loc_0_0000742A
	bsr.w loc_0_00007474
	move.b loc_0_00000024(pc),d0
	beq.b loc_0_00004CA6
loc_0_00004C62:
	movea.l h0dl_DOSBase.l,a0
	clr.l $00B8(a0)
	lea.l loc_0_00000025(pc),a0
	move.b (a0)+,app_0148(a6)
	move.b (a0)+,app_00E6(a6)
	tst.b (a0)+
	move.w (a0)+,app_0816(a6)
	lea.l loc_0_00000072(pc),a0
	move.b (a0)+,app_0584(a6)
	move.b (a0)+,app_0585(a6)
	move.b (a0)+,app_0586(a6)
	move.b (a0)+,app_0587(a6)
	move.w (a0)+,app_00F0(a6)
	tst.b loc_0_0000002A.l
	bne.b loc_0_00004CA6
	move.b #$8,loc_0_0000002A.l
loc_0_00004CA6:
	rts
loc_0_00004CA8:
	dc.b $45,$4E,$56,$3A,$44,$65,$76,$70,$61,$63,$2F
loc_0_00004CB3:
	dc.b $4D,$6F,$6E,$41,$6D,$2E,$70,$72,$65,$66,$73,$00,$00,$61,$00,$0D
	dc.b $00,$66,$2A,$4A,$14,$67,$26,$61,$00,$1E,$A4,$66,$22,$B2,$3C,$00
	dc.b $2C,$66,$1C,$2A,$02,$61,$00,$1E,$96,$66,$14,$B2,$3C,$00,$2C,$66
	dc.b $0E,$2C,$02,$61,$00,$1E,$88,$66,$06,$4A,$01,$66,$02,$4E,$75,$61
	dc.b $00,$11,$60,$49,$EE,$0A,$D4,$60,$C4,$76,$04,$41,$FA,$3A,$3A,$61
	dc.b $00,$CD,$7A,$49,$EE,$0A,$D4,$61,$B4,$66,$28,$BC,$85,$6D,$F4,$24
	dc.b $42,$22,$46,$20,$45,$9C,$88,$67,$1A,$52,$86,$B5,$C8,$64,$08,$14
	dc.b $D8,$53,$86,$66,$FA,$60,$0C,$52,$89,$45,$F2,$68,$00,$15,$21,$53
	dc.b $86,$66,$FA,$60,$00,$10,$64,$76,$04,$41,$FA,$3A,$0E,$61,$00,$CD
	dc.b $3C,$49,$EE,$0A,$D4,$61,$00,$FF,$76,$66,$E8,$9C,$85,$6D,$F2,$20
	dc.b $45,$10,$C2,$53,$86,$64,$FA,$60,$DA,$76,$04,$41,$FA,$3A,$00,$61
	dc.b $00,$CD,$1A,$61,$00,$0C,$58,$66,$00,$00,$8C,$4A,$14,$67,$00,$00
	dc.b $86,$61,$00,$10,$26,$41,$EE,$0A,$D4,$4A,$10,$67,$76,$22,$08,$74
	dc.b $FE,$2F,$0E,$2C,$6E,$00,$C2,$4E,$AE,$FF,$AC,$2C,$5F,$28,$00,$67
	dc.b $00,$CD,$64,$41,$EE,$09,$B0,$24,$08,$22,$04,$2F,$0E,$2C,$6E,$00
	dc.b $C2,$4E,$AE,$FF,$9A,$2C,$5F,$4A,$80,$66,$20,$2F,$0E,$2C,$6E,$00
	dc.b $C2,$4E,$AE,$FF,$7C,$2C,$5F,$61,$00,$CD,$48,$22,$04,$2F,$0E,$2C
	dc.b $6E,$00,$C2,$4E,$AE,$FF,$A6,$2C,$5F,$4E,$75,$20,$3C,$00,$00,$00
	dc.b $D4,$4A,$AE,$09,$B4,$6F,$E0,$22,$04,$2F,$0E,$2C,$6E,$00,$C2,$4E
	dc.b $AE,$FF,$82,$2C,$5F,$22,$00,$2F,$0E,$2C,$6E,$00,$C2,$4E,$AE,$FF
	dc.b $A6,$2C,$5F,$4E,$75,$60,$00,$0F,$A2,$76,$07,$41,$FA,$39,$7C,$61
	dc.b $00,$CC,$7A,$61,$00,$0B,$BA,$66,$74,$4A,$14,$67,$70,$61,$00,$CB
	dc.b $BE,$41,$FA,$39,$7C,$61,$00,$1C,$50,$61,$00,$CB,$B6,$42,$2E,$0B
	dc.b $10,$78,$00,$60,$04,$61,$00,$10,$2A,$49,$EE,$0B,$10,$61,$00,$0B
	dc.b $90,$66,$4A,$61,$00,$1D,$38,$66,$EC,$B2,$3C,$00,$2C,$66,$E6,$2A
	dc.b $02,$61,$00,$1D,$2A,$66,$DE,$4A,$01,$66,$DA,$28,$02,$98,$85,$6D
	dc.b $D4,$52,$84,$41,$EE,$0A,$D4,$61,$00,$25,$5A,$66,$12,$20,$45,$61
	dc.b $00,$25,$DE,$66,$0A,$61,$00,$26,$0A,$61,$00,$10,$00,$60,$0E,$61
	dc.b $00,$0F,$FA,$3F,$00,$61,$06,$30,$1F,$60,$00,$CC,$86,$60,$00,$0F
	dc.b $1A,$76,$07,$61,$00,$CB,$B6,$41,$FA,$39,$18,$61,$00,$1B,$DA,$61
	dc.b $00,$FD,$54,$61,$00,$F2,$94,$B2,$3C,$00,$1B,$67,$00,$00,$78,$02
	dc.b $01,$00,$DF,$B2,$3C,$00,$47,$67,$06,$B2,$3C,$00,$49,$66,$E4,$3F
	dc.b $01,$61,$00,$0A,$04,$61,$00,$CB,$16,$32,$1F,$B2,$3C,$00,$47,$67
	dc.b $4E,$49,$EE,$0A,$D4,$22,$2E,$01,$94,$67,$04,$61,$00,$CC,$EE,$42
	dc.b $14,$49,$EE,$0A,$D4,$61,$42,$49,$EE,$0A,$D4,$61,$00,$0A,$E2,$66
	dc.b $34,$4A,$14,$67,$30,$61,$00,$1C,$72,$66,$EC,$2D,$42,$01,$94,$7E
	dc.b $03,$61,$00,$CA,$DA,$3F,$07,$61,$1C,$36,$1F,$61,$00,$F5,$A2,$1D
	dc.b $43,$01,$4A,$08,$EE,$00,$07,$00,$5A,$50,$C3,$60,$00,$CA,$16,$61
	dc.b $04,$60,$00,$F5,$B0,$60,$00,$0E,$82,$28,$0C,$4A,$1C,$66,$FC,$C9
	dc.b $8C,$98,$8C,$53,$44,$4E,$75,$48,$7A,$B6,$28,$45,$FA,$38,$89,$61
	dc.b $00,$0F,$78,$72,$16,$61,$00,$1B,$20,$7E,$07,$49,$EE,$01,$98,$32
	dc.b $2C,$00,$06,$67,$54,$24,$14,$61,$00,$1B,$4E,$61,$00,$1B,$32,$74
	dc.b $FF,$74,$16,$20,$14,$61,$00,$2F,$9E,$67,$04,$61,$00,$2C,$78,$52
	dc.b $02,$61,$00,$1B,$10,$24,$54,$61,$00,$1A,$3A,$0C,$6C,$00,$04,$00
	dc.b $06,$66,$1E,$61,$00,$01,$1C,$74,$09,$61,$00,$1A,$F8,$72,$3F,$61
	dc.b $00,$09,$36,$45,$EC,$00,$0C,$12,$1A,$67,$06,$61,$00,$09,$2A,$60
	dc.b $F6,$61,$00,$00,$FE,$61,$00,$00,$FA,$49,$EC,$00,$48,$51,$CF,$FF
	dc.b $A0,$72,$29,$61,$00,$1A,$B2,$72,$26,$10,$2E,$01,$34,$67,$08,$72
	dc.b $25,$4A,$00,$6A,$02,$72,$27,$61,$00,$1A,$9E,$61,$00,$00,$D4,$72
	dc.b $2A,$61,$00,$1A,$94,$61,$00,$00,$CA,$4A,$2E,$01,$34,$67,$40,$24
	dc.b $7A,$39,$22,$D5,$CA,$D5,$CA,$74,$04,$D4,$8A,$2F,$02,$61,$00,$1A
	dc.b $B8,$72,$2D,$61,$00,$08,$D2,$24,$17,$D4,$AA,$FF,$FC,$51,$82,$61
	dc.b $00,$1A,$A6,$61,$00,$1A,$8A,$20,$1F,$61,$00,$2E,$FA,$67,$06,$74
	dc.b $20,$61,$00,$2B,$D2,$61,$00,$00,$8A,$24,$52,$20,$0A,$66,$C4,$72
	dc.b $28,$61,$00,$1A,$44,$72,$02,$61,$18,$72,$2C,$61,$00,$08,$9A,$72
	dc.b $04,$61,$0E,$72,$2C,$61,$00,$08,$90,$72,$00,$61,$04,$61,$62,$60
	dc.b $16,$08,$C1,$00,$00,$2F,$0E,$2C,$78,$00,$04,$4E,$AE,$FF,$28,$2C
	dc.b $5F,$22,$00,$60,$00,$1A,$94,$72,$2B,$61,$00,$1A,$0C,$61,$42,$20
	dc.b $78,$00,$04,$24,$68,$01,$42,$4A,$92,$67,$30,$24,$0A,$B4,$BC,$00
	dc.b $04,$00,$00,$64,$02,$74,$00,$61,$00,$1A,$2E,$72,$2D,$61,$00,$08
	dc.b $48,$24,$2A,$00,$18,$61,$00,$1A,$20,$61,$00,$1A,$04,$20,$6A,$00
	dc.b $0A,$61,$00,$19,$E4,$61,$0A,$24,$52,$60,$CC,$61,$14,$60,$00,$0D
	dc.b $0A,$61,$00,$19,$FE,$30,$2B,$00,$0C,$B0,$6B,$00,$08,$6C,$02,$4E
	dc.b $75,$48,$E7,$3F,$3C,$61,$00,$F0,$82,$6B,$1C,$B2,$3C,$00,$1B,$67
	dc.b $0E,$61,$00,$05,$E0,$4C,$DF,$3C,$FC,$42,$AB,$00,$0A,$4E,$75,$4C
	dc.b $DF,$3C,$FC,$58,$8F,$60,$C6,$2F,$0B,$61,$00,$B6,$52,$26,$5F,$60
	dc.b $D4,$41,$FA,$36,$E8,$76,$0A,$61,$00,$C9,$A2,$42,$AE,$01,$74,$60
	dc.b $04,$61,$00,$0D,$6E,$49,$EE,$0A,$D4,$61,$00,$08,$D4,$66,$00,$01
	dc.b $F6,$4A,$14,$67,$00,$01,$F0,$61,$00,$1A,$74,$66,$E4,$B2,$3C,$00
	dc.b $2C,$66,$DE,$52,$82,$02,$02,$00,$FE,$2D,$42,$01,$6C,$61,$00,$1A
	dc.b $5E,$66,$CE,$B4,$AE,$01,$6C,$6F,$C8,$2D,$42,$01,$70,$24,$42,$61
	dc.b $00,$22,$46,$66,$BC,$24,$6E,$01,$6C,$61,$00,$22,$3C,$66,$B2,$61
	dc.b $00,$C8,$A0,$72,$18,$61,$00,$19,$20,$61,$00,$C8,$96,$42,$2E,$0A
	dc.b $D4,$78,$00,$60,$04,$61,$00,$0D,$0A,$49,$EE,$0A,$D4,$61,$00,$08
	dc.b $70,$66,$00,$01,$92,$51,$EE,$01,$63,$4A,$14,$67,$46,$61,$00,$1A
	dc.b $0E,$66,$E2,$2D,$42,$01,$64,$42,$AE,$01,$68,$4A,$01,$67,$1A,$B2
	dc.b $3C,$00,$2C,$66,$D0,$61,$00,$19,$F6,$66,$CA,$4A,$01,$66,$C6,$B4
	dc.b $AE,$01,$64,$65,$C0,$2D,$42,$01,$68,$24,$2E,$01,$64,$08,$02,$00
	dc.b $00,$66,$B2,$20,$02,$61,$00,$22,$0A,$66,$AA,$52,$2E,$01,$63,$20
	dc.b $42,$42,$90,$61,$00,$C8,$2C,$72,$17,$61,$00,$18,$AC,$61,$00,$C8
	dc.b $22,$4B,$EE,$0B,$10,$78,$00,$42,$2E,$0A,$D4,$60,$04,$61,$00,$0C
	dc.b $92,$49,$EE,$0A,$D4,$61,$00,$07,$F8,$66,$00,$01,$1A,$4A,$14,$67
	dc.b $60,$61,$00,$19,$9A,$66,$E6,$B2,$3C,$00,$2C,$66,$E0,$2A,$82,$61
	dc.b $00,$19,$8C,$66,$D8,$B4,$95,$6F,$D4,$70,$00,$4A,$01,$67,$22,$B2
	dc.b $3C,$00,$2C,$66,$C8,$12,$1C,$02,$01,$00,$DF,$B2,$3C,$00,$42,$67
	dc.b $10,$70,$01,$B2,$3C,$00,$57,$67,$08,$70,$02,$B2,$3C,$00,$4C,$66
	dc.b $AC,$22,$15,$52,$81,$02,$01,$00,$FE,$2A,$C1,$52,$82,$02,$02,$00
	dc.b $FE,$2A,$C2,$3A,$C0,$37,$7C,$00,$04,$00,$0A,$61,$00,$06,$06,$60
	dc.b $84,$42,$95,$61,$00,$C7,$9C,$72,$19,$61,$00,$18,$1C,$61,$00,$C7
	dc.b $92,$42,$2E,$0A,$D4,$78,$00,$49,$EE,$0A,$D4,$61,$00,$07,$72,$66
	dc.b $00,$00,$94,$4A,$14,$67,$16,$20,$4C,$61,$00,$21,$58,$67,$06,$61
	dc.b $00,$0C,$0A,$60,$E2,$61,$00,$0C,$04,$61,$00,$22,$16,$2A,$6E,$01
	dc.b $6C,$4A,$2E,$01,$63,$67,$42,$BB,$EE,$01,$70,$6E,$34,$61,$00,$00
	dc.b $7C,$66,$28,$10,$2A,$00,$09,$67,$18,$53,$00,$67,$0A,$58,$8D,$BB
	dc.b $EA,$00,$04,$6D,$F8,$60,$E0,$54,$8D,$BB,$EA,$00,$04,$6D,$F8,$60
	dc.b $D6,$52,$8D,$BB,$EA,$00,$04,$6D,$F8,$60,$CC,$61,$00,$C9,$C8,$60
	dc.b $C6,$50,$EE,$01,$63,$2A,$6E,$01,$6C,$4A,$AE,$01,$74,$66,$1C,$61
	dc.b $00,$22,$E8,$66,$16,$51,$EE,$00,$E4,$51,$EE,$01,$63,$61,$00,$0A
	dc.b $CA,$41,$FA,$33,$A9,$61,$00,$C7,$FC,$60,$16,$50,$EE,$00,$E4,$61
	dc.b $00,$17,$B0,$61,$36,$51,$EE,$00,$E4,$51,$EE,$01,$63,$61,$00,$0A
	dc.b $AA,$4A,$AE,$01,$74,$66,$00,$21,$98,$4E,$75,$45,$EE,$0B,$10,$20
	dc.b $12,$67,$14,$BB,$C0,$6D,$0A,$BB,$EA,$00,$04,$6C,$04,$70,$00,$4E
	dc.b $75,$45,$EA,$00,$0A,$60,$E8,$70,$FF,$4E,$75,$BB,$EE,$01,$70,$6F
	dc.b $02,$4E,$75,$4A,$2E,$00,$E4,$6A,$F8,$61,$D0,$66,$7A,$2F,$0D,$49
	dc.b $EE,$09,$A8,$28,$FC,$64,$63,$2E,$62,$53,$8C,$10,$2A,$00,$09,$67
	dc.b $40,$53,$40,$67,$1E,$18,$FC,$00,$6C,$18,$FC,$00,$20,$78,$01,$22
	dc.b $1D,$61,$00,$C8,$32,$18,$FC,$00,$2C,$BB,$EA,$00,$04,$5C,$CC,$FF
	dc.b $F0,$60,$3A,$18,$FC,$00,$77,$18,$FC,$00,$20,$78,$03,$32,$1D,$61
	dc.b $00,$C8,$0C,$18,$FC,$00,$2C,$BB,$EA,$00,$04,$5C,$CC,$FF,$F0,$60
	dc.b $1C,$18,$FC,$00,$62,$18,$FC,$00,$20,$78,$07,$12,$1D,$61,$00,$C7
	dc.b $DC,$18,$FC,$00,$2C,$BB,$EA,$00,$04,$5C,$CC,$FF,$F0,$19,$7C,$00
	dc.b $0A,$FF,$FF,$28,$5F,$60,$0C,$48,$E7,$1F,$04,$61,$00,$C8,$C8,$4C
	dc.b $DF,$10,$F8,$28,$0D,$98,$8C,$61,$3C,$49,$EE,$09,$A8,$74,$FF,$52
	dc.b $02,$12,$1C,$B2,$3C,$00,$0A,$67,$24,$B2,$3C,$00,$20,$66,$18,$70
	dc.b $07,$90,$02,$65,$12,$72,$09,$4A,$AE,$01,$74,$66,$08,$14,$00,$61
	dc.b $00,$16,$92,$72,$20,$74,$08,$61,$00,$04,$CE,$60,$D2,$61,$00,$16
	dc.b $A2,$60,$00,$FF,$28,$4A,$AE,$01,$74,$66,$44,$24,$0C,$61,$00,$16
	dc.b $98,$61,$00,$16,$7C,$76,$00,$B6,$44,$6C,$12,$14,$34,$30,$00,$61
	dc.b $00,$16,$96,$52,$43,$B6,$7C,$00,$0A,$66,$EC,$60,$0A,$61,$00,$16
	dc.b $60,$61,$00,$16,$5C,$60,$EC,$61,$00,$16,$56,$74,$0C,$20,$0C,$61
	dc.b $00,$2A,$C4,$67,$04,$61,$00,$27,$9E,$52,$02,$60,$00,$16,$36,$20
	dc.b $0C,$61,$00,$2A,$B2,$67,$0E,$28,$40,$2F,$04,$28,$1C,$E5,$84,$61
	dc.b $00,$27,$C0,$28,$1F,$72,$09,$60,$00,$04,$5E,$41,$FA,$33,$E3,$61
	dc.b $00,$C6,$C4,$66,$3E,$49,$FA,$C0,$5E,$78,$14,$10,$3A,$34,$85,$66
	dc.b $32,$4A,$2E,$01,$34,$6B,$2E,$2F,$0E,$2C,$78,$00,$04,$4E,$AE,$FF
	dc.b $7C,$2C,$5F,$20,$7A,$34,$D2,$20,$68,$00,$36,$20,$8C,$08,$A8,$00
	dc.b $07,$00,$04,$21,$44,$00,$08,$2F,$0E,$2C,$78,$00,$04,$4E,$AE,$FF
	dc.b $76,$2C,$5F,$4E,$75,$2D,$4C,$00,$54,$08,$AE,$00,$07,$00,$5A,$2D
	dc.b $44,$00,$10,$50,$C3,$60,$00,$C4,$6C,$41,$FA,$33,$7B,$61,$00,$C6
	dc.b $66,$66,$E0,$10,$3A,$34,$2D,$66,$DA,$2F,$0E,$2C,$78,$00,$04,$4E
	dc.b $AE,$FF,$7C,$2C,$5F,$20,$7A,$34,$80,$20,$68,$00,$36,$08,$E8,$00
	dc.b $07,$00,$04,$2F,$0E,$2C,$78,$00,$04,$4E,$AE,$FF,$76,$2C,$5F,$4E
	dc.b $75,$4A,$AE,$01,$5E,$66,$12,$4A,$AE,$00,$AE,$67,$0C,$41,$FA,$33
	dc.b $4B,$61,$00,$C6,$22,$67,$00,$22,$3A,$4E,$75
loc_0_0000550E:
	moveq.l #7,d3
	lea.l loc_0_0000858F(pc),a0
	bsr.w loc_0_00001A7E
	bsr.w loc_0_000059C0
	bne.b loc_0_0000554A
	tst.b (a4)
	beq.b loc_0_0000554A
	bsr.w loc_0_000019D0
	lea.l loc_0_000085A7(pc),a0
	bsr.w loc_0_00006A6A
	bsr.w loc_0_000019D4
	lea.l app_0B10(a6),a4
	clr.b (a4)
	bsr.w loc_0_000059C0
	bne.b loc_0_0000554A
	move.l a4,-(a7)
	bsr.b loc_0_0000554A
	movea.l (a7)+,a4
	lea.l app_0AD4(a6),a3
	bra.b loc_0_0000554E
loc_0_0000554A:
	bra.w loc_0_00005D9C
loc_0_0000554E:
	bsr.w loc_0_0000446C
	bsr.w loc_0_00007740
	move.l a3,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0096(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.w loc_0_00001AF8
loc_0_0000556A:
	move.l d0,loc_0_000088F6.l
	add.l d0,d0
	add.l d0,d0
	addq.l #4,d0
	move.l d0,app_00AA(a6)
	lea.l loc_0_0000136D(pc),a0
	movea.l a3,a1
	lea.l loc_0_0000136C(pc),a2
	st.b (a2)
loc_0_00005586:
	addq.b #1,(a2)
	move.b (a1)+,(a0)+
	bne.b loc_0_00005586
	clr.b -(a0)
	movem.l d4-d7/a3-a5,-(a7)
	move.l a3,-(a7)
	bsr.w loc_0_0000052A
	movea.l (a7)+,a0
	bsr.w loc_0_00007780
	bsr.w loc_0_00007E10
	bsr.w loc_0_0000052A
	movem.l (a7)+,d4-d7/a3-a5
	movea.l a4,a0
	lea.l loc_0_00001488(pc),a1
	clr.b (a1)+
loc_0_000055B2:
	move.b (a0)+,(a1)+
	bne.b loc_0_000055B2
	cmpi.b #10,-$0002(a1)
	beq.b loc_0_000055C6
	move.b #$A,-$0001(a1)
	clr.b (a1)
loc_0_000055C6:
	move.l a1,d0
	lea.l loc_0_00001489(pc),a0
	sub.l a0,d0
	move.b d0,-(a0)
	movea.l app_00AA(a6),a1
	move.l a1,app_069A(a6)
	moveq.l #1,d3
	moveq.l #1,d2
	bsr.w loc_0_00003DA0
	movea.l app_00AA(a6),a1
	move.w (a1),loc_0_000088FA.l
	move.w #$4EF9,(a1)+
	move.l (a1),loc_0_000088FC.l
	move.l #loc_0_000013B0,(a1)
	movea.l h0dl_DOSBase(pc),a0
	move.l $00AC(a0),d0
	add.l d0,d0
	add.l d0,d0
	movea.l d0,a0
	moveq.l #15,d0
	lea.l loc_0_00001448(pc),a1
loc_0_0000560E:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_0_0000560E
	move.l #loc_0_0000136C,d1
	lsr.l #2,d1
	move.l d1,loc_0_00001458.l
	move.l loc_0_000088F6(pc),loc_0_00001484.l
	move.l a3,d1
	moveq.l #0,d2
	movea.l h0dl_DOSBase(pc),a0
	move.b $0009(a0),d2
	move.l loc_0_000088F6(pc),d3
	moveq.l #80,d4
	add.l app_00B2(a6),d4
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	move.l d0,app_010A(a6)
	beq.b loc_0_0000565C
	move.b #$1,app_0134(a6)
	bsr.w loc_0_00001044
loc_0_0000565C:
	rts
loc_0_0000565E:
	movem.w d2-d3,$0004(a3)
	movem.w d0-d1,$000E(a3)
	clr.l $000A(a3)
	move.w $000E(a3),d0
	move.w d0,$0012(a3)
	mulu.w app_00D6(a6),d0
	move.w d0,$000E(a3)
	st.b $0014(a3)
	move.w $0006(a3),d0
	mulu.w app_00D8(a6),d0
	move.w d0,$0008(a3)
	rts
loc_0_00005690:
	bsr.b loc_0_0000565E
	sf.b $0014(a3)
loc_0_00005696:
	move.w $0008(a3),d3
	move.l a2,-(a7)
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetAPen(a6)
	movea.l (a7)+,a6
	movem.w $000E(a3),d0-d1
	move.w $0004(a3),d2
	mulu.w app_00D6(a6),d2
	add.w d0,d2
	subq.w #1,d2
	add.w d1,d3
	subq.w #1,d3
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVORectFill(a6)
	movea.l (a7)+,a6
	moveq.l #1,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetAPen(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a2
	rts
loc_0_000056EA:
	move.b d1,-(a7)
	mulu.w app_00D6(a6),d2
	add.w $000E(a3),d2
	add.w $0010(a3),d3
	add.w app_00DA(a6),d3
	move.w d2,d0
	move.w d3,d1
	movea.l a5,a1
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOMove(a6)
	movea.l (a7)+,a6
	movea.l a5,a1
	tst.b d7
	bne.b loc_0_00005730
	movea.l a7,a0
	moveq.l #1,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOText(a6)
	movea.l (a7)+,a6
loc_0_0000572C:
	addq.l #2,a7
	rts
loc_0_00005730:
	moveq.l #5,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetDrMd(a6)
	movea.l (a7)+,a6
	movea.l a7,a0
	moveq.l #1,d0
	movea.l a5,a1
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOText(a6)
	movea.l (a7)+,a6
	moveq.l #1,d0
	movea.l a5,a1
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetDrMd(a6)
	movea.l (a7)+,a6
	bra.b loc_0_0000572C
	dc.b $C6,$EE,$00,$D8
loc_0_00005772:
	movem.w d2-d3,-(a7)
	moveq.l #3,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetDrMd(a6)
	movea.l (a7)+,a6
	movem.w (a7)+,d0-d1
	mulu.w app_00D6(a6),d0
	add.w $000E(a3),d0
	add.w $0010(a3),d1
	move.w d0,d2
	add.w app_00D6(a6),d2
	subq.w #1,d2
	move.w d1,d3
	add.w app_00D8(a6),d3
	subq.w #1,d3
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVORectFill(a6)
	movea.l (a7)+,a6
	moveq.l #1,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetDrMd(a6)
	movea.l (a7)+,a6
	rts
	dc.b $48,$E7,$1C,$00,$4A,$00,$5A,$C1,$00,$01,$00,$01,$48,$81,$C3,$EE
	dc.b $00,$D8,$70,$00,$4C,$AB,$00,$0C,$00,$0E,$38,$2E,$00,$D6,$C8,$EB
	dc.b $00,$04,$D8,$42,$53,$44,$3A,$2B,$00,$06,$CA,$EE,$00,$D8,$DA,$43
	dc.b $53,$45,$2F,$0E,$22,$6E,$00,$D2,$2C,$6E,$00,$C6,$4E,$AE,$FE,$74
	dc.b $2C,$5F,$4C,$DF,$00,$38,$4E,$75,$70,$FF,$61,$B4,$30,$2B,$00,$06
	dc.b $53,$40,$C0,$EE,$00,$D8,$37,$40,$00,$0C,$42,$6B,$00,$0A,$4E,$75
	dc.b $70,$00,$61,$9C,$42,$AB,$00,$0A
loc_0_00005834:
	rts
loc_0_00005836:
	tst.b app_00E4(a6)
	bne.b loc_0_00005834
	tst.l app_0570(a6)
	beq.b loc_0_00005846
	bsr.w loc_0_00005940
loc_0_00005846:
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetAPen(a6)
	movea.l (a7)+,a6
	move.w $000A(a3),d0
	mulu.w app_00D6(a6),d0
	add.w $000E(a3),d0
	move.w $000C(a3),d1
	add.w $0010(a3),d1
	move.w $0004(a3),d2
	mulu.w app_00D6(a6),d2
	add.w $000E(a3),d2
	cmp.w d0,d2
	ble.b loc_0_00005896
	subq.w #1,d2
	move.w d1,d3
	add.w app_00D8(a6),d3
	subq.w #1,d3
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVORectFill(a6)
	movea.l (a7)+,a6
loc_0_00005896:
	moveq.l #1,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetAPen(a6)
	movea.l (a7)+,a6
	rts
	dc.b $06,$01,$00,$30,$60,$00,$00,$0A,$48,$E7,$F1,$E0,$50,$C3,$60,$06
loc_0_000058BA:
	movem.l d0-d3/d7/a0-a2,-(a7)
	sf.b d3
	tst.b app_00E4(a6)
	bne.w loc_0_00007544
	cmpa.l app_0570(a6),a3
	beq.b loc_0_000058E6
	move.w d1,-(a7)
	bsr.b loc_0_00005940
	move.w (a7)+,d1
	tst.b $0014(a3)
	beq.b loc_0_00005908
	move.l a3,app_0570(a6)
	lea.l app_0944(a6),a0
	move.l a0,app_0574(a6)
loc_0_000058E6:
	tst.b d3
	bne.b loc_0_000058F0
	cmp.b #$A,d1
	beq.b loc_0_00005900
loc_0_000058F0:
	movea.l app_0574(a6),a0
	move.b d1,(a0)+
	move.l a0,app_0574(a6)
	movem.l (a7)+,d0-d3/d7/a0-a2
	rts
loc_0_00005900:
	bsr.b loc_0_00005940
	move.l a3,app_0570(a6)
	bra.b loc_0_00005932
loc_0_00005908:
	tst.b d3
	bne.b loc_0_00005912
	cmp.b #$A,d1
	beq.b loc_0_00005932
loc_0_00005912:
	move.w $000A(a3),d0
	cmp.w $0004(a3),d0
	beq.b loc_0_0000592C
	movem.w $000A(a3),d2-d3
	addq.w #1,$000A(a3)
	moveq.l #0,d7
	bsr.w loc_0_000056EA
loc_0_0000592C:
	movem.l (a7)+,d0-d3/d7/a0-a2
	rts
loc_0_00005932:
	clr.w $000A(a3)
	move.w app_00D8(a6),d0
	add.w d0,$000C(a3)
	bra.b loc_0_0000592C
loc_0_00005940:
	tst.l app_0570(a6)
	beq.b loc_0_000059BA
	movem.l d3/a3,-(a7)
	movea.l app_0570(a6),a3
	movem.w $000A(a3),d2-d3
	cmp.w $0008(a3),d3
	bge.b loc_0_000059AE
	mulu.w app_00D6(a6),d2
	add.w $000E(a3),d2
	add.w $0010(a3),d3
	add.w app_00DA(a6),d3
	move.w d2,d0
	move.w d3,d1
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOMove(a6)
	movea.l (a7)+,a6
	move.l app_0574(a6),d0
	lea.l app_0944(a6),a0
	sub.l a0,d0
	beq.b loc_0_000059AE
	move.w $0004(a3),d1
	sub.w $000A(a3),d1
	cmp.w d1,d0
	blt.b loc_0_00005998
	move.w d1,d0
loc_0_00005998:
	add.w d0,$000A(a3)
	ext.l d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOText(a6)
	movea.l (a7)+,a6
loc_0_000059AE:
	lea.l app_0944(a6),a0
	move.l a0,app_0574(a6)
	movem.l (a7)+,d3/a3
loc_0_000059BA:
	clr.l app_0570(a6)
	rts
loc_0_000059C0:
	moveq.l #0,d4
	movea.l a4,a0
loc_0_000059C4:
	tst.b (a0)+
	bne.b loc_0_000059C4
	move.l a0,d5
	sub.l a4,d5
	subq.w #1,d5
	bsr.w loc_0_00005B0C
	bsr.w loc_0_00005AF6
loc_0_000059D6:
	move.w $000C(a3),d3
	moveq.l #4,d2
	add.w d4,d2
	bsr.w loc_0_00005772
loc_0_000059E2:
	bsr.w loc_0_0000412C
	bmi.b loc_0_000059E2
	cmp.b #$A,d1
	beq.w loc_0_00005AD0
	cmp.b #$1B,d1
	beq.w loc_0_00005AD0
	cmp.b #$8,d1
	beq.w loc_0_00005A98
	cmp.b #$7F,d1
	beq.w loc_0_00005AB8
	cmp.w #$86,d1
	beq.w loc_0_00005AD8
	cmp.w #$84,d1
	beq.b loc_0_00005A68
	cmp.w #$85,d1
	beq.b loc_0_00005A74
	cmp.w #$89,d1
	beq.b loc_0_00005A80
	cmp.w #$8A,d1
	beq.b loc_0_00005A8C
	tst.b d1
	beq.b loc_0_000059E2
	cmp.b #$80,d1
	bcs.b loc_0_00005A38
	cmp.b #$A0,d1
	bcs.b loc_0_000059E2
loc_0_00005A38:
	cmp.w app_00E2(a6),d5
	beq.b loc_0_000059E2
	move.w d5,d0
	addq.w #1,d5
	sub.w d4,d0
	beq.b loc_0_00005A52
	lea.l -$1(a4,d5.w),a0
loc_0_00005A4A:
	move.b -(a0),$0001(a0)
	subq.w #1,d0
	bne.b loc_0_00005A4A
loc_0_00005A52:
	bsr.w loc_0_00005AE4
	move.b d1,$0(a4,d4.w)
	addq.w #1,d4
loc_0_00005A5C:
	clr.b $0(a4,d5.w)
loc_0_00005A60:
	bsr.w loc_0_00005AF6
	bra.w loc_0_000059D6
loc_0_00005A68:
	tst.w d4
	beq.w loc_0_000059E2
	bsr.b loc_0_00005AE4
	subq.w #1,d4
	bra.b loc_0_00005A60
loc_0_00005A74:
	cmp.w d4,d5
	beq.w loc_0_000059E2
	bsr.b loc_0_00005AE4
	addq.w #1,d4
	bra.b loc_0_00005A60
loc_0_00005A80:
	tst.w d4
	beq.w loc_0_000059E2
	bsr.b loc_0_00005AE4
	moveq.l #0,d4
	bra.b loc_0_00005A60
loc_0_00005A8C:
	cmp.w d4,d5
	beq.w loc_0_000059E2
	bsr.b loc_0_00005AE4
	move.w d5,d4
	bra.b loc_0_00005A60
loc_0_00005A98:
	tst.w d4
	beq.w loc_0_000059E2
	bsr.b loc_0_00005AE4
	move.w d5,d0
	sub.w d4,d0
	beq.b loc_0_00005AB2
	lea.l $0(a4,d4.w),a0
loc_0_00005AAA:
	move.b (a0)+,-$0002(a0)
	subq.w #1,d0
	bne.b loc_0_00005AAA
loc_0_00005AB2:
	subq.w #1,d4
	subq.w #1,d5
	bra.b loc_0_00005A5C
loc_0_00005AB8:
	move.w d5,d0
	sub.w d4,d0
	beq.w loc_0_000059E2
	lea.l $1(a4,d4.w),a0
loc_0_00005AC4:
	move.b (a0)+,-$0002(a0)
	subq.w #1,d0
	bne.b loc_0_00005AC4
	subq.w #1,d5
	bra.b loc_0_00005A5C
loc_0_00005AD0:
	bsr.b loc_0_00005AE4
	cmp.b #$A,d1
	rts
loc_0_00005AD8:
	bsr.b loc_0_00005B0C
	clr.b (a4)
	moveq.l #0,d4
	moveq.l #0,d5
	bra.w loc_0_000059D6
loc_0_00005AE4:
	move.w d1,-(a7)
	moveq.l #4,d2
	add.w d4,d2
	move.w $000C(a3),d3
	bsr.w loc_0_00005772
	move.w (a7)+,d1
	rts
loc_0_00005AF6:
	move.w $000A(a3),-(a7)
	movea.l a4,a0
	bsr.w loc_0_00006A6A
	moveq.l #32,d1
	bsr.w loc_0_000058BA
	move.w (a7)+,$000A(a3)
	rts
loc_0_00005B0C:
	move.w $000A(a3),-(a7)
	move.w app_00E2(a6),d2
	bsr.w loc_0_00006A76
	move.w (a7)+,$000A(a3)
	rts
loc_0_00005B1E:
	move.l a2,-(a7)
	add.w app_00DC(a6),d1
	bsr.w loc_0_00005690
	movea.l (a7)+,a2
	lea.l $0016(a3),a0
	moveq.l #26,d0
	move.b #$20,(a0)+
loc_0_00005B34:
	move.b (a2)+,(a0)+
	dbeq.w d0,loc_0_00005B34
	move.b #$20,-$0001(a0)
	clr.b (a0)
	lea.l loc_0_00005F32(pc),a0
	move.l a0,$003E(a3)
	clr.w $0042(a3)
	moveq.l #0,d7
	st.b d4
	st.b $0014(a3)
loc_0_00005B56:
	move.l a4,-(a7)
	movea.l a3,a4
	lea.l app_05B8(a6),a3
	move.w $0012(a4),d2
	move.w $0010(a4),d3
	sub.w app_00DC(a6),d3
	tst.b $003C(a4)
	beq.b loc_0_00005BA0
	moveq.l #48,d1
	add.b $003C(a4),d1
	bsr.w loc_0_00005C2C
	move.l $0044(a4),d0
	beq.b loc_0_00005BA0
	movea.l d0,a0
	tst.l $0004(a0)
	bne.b loc_0_00005B8C
	tst.l (a0)
	beq.b loc_0_00005BA0
loc_0_00005B8C:
	moveq.l #0,d1
	move.w $0048(a4),d1
	divu.w #$1A,d1
	swap.w d1
	addi.b #97,d1
	bsr.w loc_0_00005C2C
loc_0_00005BA0:
	moveq.l #32,d1
	bsr.w loc_0_00005C2C
	lea.l loc_0_00005C4E(pc),a0
	lea.l $0016(a4),a1
	move.l a1,(a0)
	moveq.l #0,d0
	move.b $0034(a4),d0
	asl.w #2,d0
	movea.l $0(a0,d0.w),a0
	bsr.w loc_0_00005C1C
	cmpi.b #4,$0034(a4)
	bne.b loc_0_00005BE4
	movea.l $0044(a4),a0
	lea.l $0025(a0),a0
	bsr.w loc_0_00005C1C
	moveq.l #41,d1
	bsr.w loc_0_00005C2C
	movea.l $0044(a4),a0
	tst.l $001E(a0)
	beq.b loc_0_00005C06
loc_0_00005BE4:
	tst.b $0042(a4)
	beq.b loc_0_00005C06
	cmpi.b #2,$0034(a4)
	beq.b loc_0_00005C06
	move.w #$20,d1
	bsr.w loc_0_00005C2C
	movea.l $0044(a4),a0
	lea.l $0044(a0),a0
	bsr.w loc_0_00005C1C
loc_0_00005C06:
	move.w #$20,d1
	bsr.w loc_0_00005C2C
	tst.b d4
	beq.w loc_0_00005CC4
	bsr.b loc_0_00005C62
loc_0_00005C16:
	movea.l a4,a3
	movea.l (a7)+,a4
	rts
loc_0_00005C1C:
	move.b (a0)+,d1
	beq.b loc_0_00005C2A
	move.l a0,-(a7)
	bsr.w loc_0_00005C2C
	movea.l (a7)+,a0
	bra.b loc_0_00005C1C
loc_0_00005C2A:
	rts
loc_0_00005C2C:
	move.w $0012(a4),d0
	add.w $0004(a4),d0
	cmp.w d0,d2
	bcc.b loc_0_00005C4A
	tst.b d4
	bne.b loc_0_00005C3E
	moveq.l #32,d1
loc_0_00005C3E:
	movem.w d2-d3,-(a7)
	bsr.w loc_0_000056EA
	movem.w (a7)+,d2-d3
loc_0_00005C4A:
	addq.w #1,d2
	rts
loc_0_00005C4E:
	dc.b $00,$00,$00,$00
	dc.l loc_0_0000850A	; pointer_table
	dc.l loc_0_00008511
	dc.l loc_0_000084FE
	dc.l loc_0_0000851B
loc_0_00005C62:
	move.w $000E(a4),d0
	subq.w #1,d0
	move.w $0010(a4),d1
	subq.w #1,d1
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOMove(a6)
	movea.l (a7)+,a6
	movea.l app_00D2(a6),a1
	lea.l app_0874(a6),a0
	move.w $0004(a4),d0
	mulu.w app_00D6(a6),d0
	add.w $000E(a4),d0
	addq.w #1,d0
	move.w d0,(a0)+
	move.w $0026(a1),d1
	move.w d1,(a0)+
	add.w $0008(a4),d1
	addq.w #1,d1
	move.w d0,(a0)+
	move.w d1,(a0)+
	move.w $0024(a1),(a0)+
	move.w d1,(a0)+
	move.l $0024(a1),(a0)+
	moveq.l #4,d0
	lea.l app_0874(a6),a0
	move.l a6,-(a7)
	movea.l app_GfxBase(a6),a6
	jsr _LVOPolyDraw(a6)
	movea.l (a7)+,a6
	rts
loc_0_00005CC4:
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetAPen(a6)
	movea.l (a7)+,a6
	bsr.b loc_0_00005C62
	moveq.l #1,d0
	move.l a6,-(a7)
	movea.l app_00D2(a6),a1
	movea.l app_GfxBase(a6),a6
	jsr _LVOSetAPen(a6)
	movea.l (a7)+,a6
	bra.w loc_0_00005C16
loc_0_00005CEE:
	movea.l app_05B4(a6),a0
	movea.l wd_RPort(a0),a2
	move.l a2,app_00D2(a6)
	move.w $003C(a2),app_00D6(a6)
	move.w $003A(a2),app_00D8(a6)
	move.w $003E(a2),app_00DA(a6)
	move.w wd_Height(a0),app_00EA(a6)
	move.w wd_Width(a0),d0
	move.w d0,app_00E8(a6)
	ext.l d0
	divu.w app_00D6(a6),d0
	move.w d0,app_00EC(a6)
	move.w d0,d2
	move.w app_00EA(a6),d3
	ext.l d3
	divu.w app_00D8(a6),d3
	moveq.l #0,d4
	moveq.l #0,d0
	moveq.l #0,d1
	lea.l app_05B8(a6),a3
	bset #15,d4
	bsr.w loc_0_00005690
	move.w app_00D8(a6),d0
	addq.w #1,d0
	move.w d0,app_00DC(a6)
	moveq.l #6,d0
	lea.l app_05CE(a6),a0
loc_0_00005D52:
	clr.w $0004(a0)
	lea.l $004A(a0),a0
	dbf.w d0,loc_0_00005D52
	clr.l app_00DE(a6)
	lea.l app_086A(a6),a0
	move.w #$1,(a0)+
	move.w app_00DC(a6),(a0)+
	move.w app_00EC(a6),d0
	subq.w #2,d0
	move.w d0,(a0)+
	move.w app_00EA(a6),d0
	ext.l d0
	divu.w app_00D8(a6),d0
	subq.w #2,d0
	move.w d0,(a0)+
	move.w #$32,app_00E2(a6)
	move.w app_00EA(a6),d0
	sub.w app_00D8(a6),d0
	move.w d0,app_00EE(a6)
	clr.l app_0570(a6)
	rts
loc_0_00005D9C:
	movem.l d4-d7,-(a7)
	pea.l loc_0_00005DCC(pc)
	bsr.w loc_0_00005696
	sf.b d7
	sf.b d4
	bsr.w loc_0_00005B56
	clr.w $0004(a3)
	lea.l app_0740(a6),a3
	tst.w $0004(a3)
	beq.w loc_0_00005EFA
	st.b d7
	st.b d4
	bsr.w loc_0_00005B56
	bra.w loc_0_00005F22
loc_0_00005DCC:
	dc.b $4C,$DF,$00,$F0,$4E,$75
loc_0_00005DD2:
	moveq.l #0,d1
	move.w $0004(a3),d1
	moveq.l #0,d0
	move.b $0034(a3),d0
	add.w d0,d0
	jmp loc_0_00005DE4(pc,d0.w)
loc_0_00005DE4:
	dc.b $4E,$75,$60,$06,$60,$12,$60,$30,$60,$54,$41,$FA,$01,$F2,$27,$48
	dc.b $00,$3E,$04,$41,$00,$0A,$60,$0C,$41,$FA,$08,$F8,$27,$48,$00,$3E
	dc.b $04,$41,$00,$26,$82,$FC,$00,$07,$D2,$41,$B2,$7C,$00,$10,$63,$02
	dc.b $72,$10,$17,$41,$00,$35,$4E,$75,$04,$41,$00,$26,$64,$02,$72,$00
	dc.b $B2,$3C,$00,$06,$64,$02,$72,$00,$B2,$3C,$00,$10,$65,$02,$72,$10
	dc.b $17,$41,$00,$35,$41,$FA,$09,$48,$27,$48,$00,$3E,$4E,$75,$17,$79
	dc.l loc_0_0000002A
	dc.b $00,$35,$41,$FA,$09,$E2,$27,$48,$00,$3E,$4E,$75,$48,$E7,$C0,$C0
	dc.b $20,$6E,$00,$CE,$2F,$0E,$2C,$6E,$00,$BE,$4E,$AE,$FF,$A0,$2C,$5F
	dc.b $4C,$DF,$03,$03,$4E,$75
loc_0_00005E6E:
	movea.l app_IntuitionBase(a6),a1
	movea.l app_00CE(a6),a0
	cmpa.l $003C(a1),a0
	beq.b loc_0_00005E88
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOScreenToFront(a6)
	movea.l (a7)+,a6
loc_0_00005E88:
	movea.l app_05B4(a6),a0
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOActivateWindow(a6)
	movea.l (a7)+,a6
	rts
	dc.b $20,$6E,$00,$CE,$2F,$0E,$2C,$6E,$00,$BE,$4E,$AE,$FF,$0A,$2C,$5F
	dc.b $4E,$75,$2F,$0A,$47,$EE,$05,$B8,$61,$00,$F7,$E2,$47,$EE,$07,$40
	dc.b $41,$EB,$00,$16,$70,$19,$42,$58,$51,$C8,$FF,$FC,$4C,$AE,$00,$1F
	dc.b $08,$6A,$92,$6E,$00,$DC,$24,$5F,$61,$00,$FC,$4A,$50,$C7,$50,$C4
	dc.b $60,$00,$FC,$7A
loc_0_00005EDE:
	lea.l app_05CE(a6),a3
	moveq.l #6,d2
loc_0_00005EE4:
	tst.w $0004(a3)
	beq.b loc_0_00005EF0
	move.w d2,-(a7)
	bsr.b loc_0_00005F22
	move.w (a7)+,d2
loc_0_00005EF0:
	lea.l $004A(a3),a3
	dbf.w d2,loc_0_00005EE4
	rts
loc_0_00005EFA:
	lea.l app_05CE(a6),a3
	moveq.l #6,d2
loc_0_00005F00:
	tst.w $0004(a3)
	beq.b loc_0_00005F18
	move.w d2,-(a7)
	cmpa.l app_00DE(a6),a3
	seq.b d7
	st.b d4
	bsr.w loc_0_00005B56
	bsr.b loc_0_00005F22
	move.w (a7)+,d2
loc_0_00005F18:
	lea.l $004A(a3),a3
	dbf.w d2,loc_0_00005F00
	rts
loc_0_00005F22:
	clr.l $000A(a3)
	movea.l $003E(a3),a0
	jsr $0000(a0)
	bra.w loc_0_00005940
loc_0_00005F32:
	dc.b $60,$00,$00,$10,$60,$0C,$60,$0A,$60,$08,$60,$06,$60,$04,$60,$02
	dc.b $4E,$71,$72,$00,$4E,$75,$3E,$2B,$00,$06,$24,$6B,$00,$38,$61,$0A
	dc.b $61,$00,$0B,$40,$53,$07,$66,$F6,$4E,$75,$24,$0A,$61,$00,$0B,$3A
	dc.b $61,$00,$0B,$1E,$1C,$2B,$00,$35,$61,$38,$7C,$00,$1C,$2B,$00,$35
	dc.b $61,$00,$13,$F6,$94,$C6,$66,$1C,$61,$00,$13,$EE,$66,$16,$61,$00
	dc.b $0B,$00,$12,$1A,$66,$04,$12,$3C,$00,$B7,$61,$00,$F9,$24,$53,$06
	dc.b $66,$F0,$4E,$75,$14,$2B,$00,$35,$52,$02,$61,$00,$0A,$D8,$D4,$C6
	dc.b $4E,$75,$4A,$06,$67,$28,$61,$00,$0A,$D8,$61,$00,$13,$BC,$67,$08
	dc.b $52,$8A,$61,$00,$0A,$D2,$60,$06,$14,$1A,$61,$00,$0A,$EC,$30,$0A
	dc.b $08,$00,$00,$00,$66,$04,$61,$00,$0A,$B8,$53,$06,$66,$DC,$4E,$75
	dc.b $53,$AB,$00,$38,$70,$FF,$4E,$75,$52,$AB,$00,$38,$70,$FF,$4E,$75
	dc.b $60,$00,$FF,$64,$60,$0A,$60,$12,$60,$22,$60,$3E,$60,$E2,$60,$E8
	dc.b $70,$00,$10,$2B,$00,$35,$44,$40,$60,$06,$70,$00,$10,$2B,$00,$35
	dc.b $C1,$EB,$00,$06,$D1,$AB,$00,$38,$72,$FF,$4E,$75,$61,$00,$F8,$1C
	dc.b $70,$00,$10,$2B,$00,$35,$91,$AB,$00,$38,$24,$6B,$00,$38,$61,$00
	dc.b $FF,$3A,$61,$00,$F9,$1A,$72,$00,$4E,$75,$61,$00,$F7,$E6,$70,$00
	dc.b $10,$2B,$00,$35,$D1,$AB,$00,$38,$32,$2B,$00,$06,$53,$41,$C2,$C0
	dc.b $24,$6B,$00,$38,$D5,$C1,$61,$00,$FF,$12,$61,$00,$F8,$F2,$72,$00
	dc.b $4E,$75,$28,$6B,$00,$38,$7C,$00,$7E,$00,$7A,$00,$78,$00,$18,$2B
	dc.b $00,$35,$C8,$FC,$00,$05,$E2,$4C,$36,$04,$60,$60,$3F,$03,$74,$0A
	dc.b $4A,$05,$67,$04,$D4,$44,$52,$42,$D4,$46,$36,$07,$61,$00,$F6,$EE
	dc.b $36,$1F,$4E,$75,$00,$00,$01,$01,$01,$02,$02,$03,$03,$03,$04,$04
	dc.b $05,$05,$05,$06,$06,$07,$07,$07,$08,$08,$09,$09,$09,$0A,$0A,$0B
	dc.b $0B,$0B,$0C,$0C,$0D,$0D,$0D,$0E,$0E,$0F,$0F,$0F,$10,$3B,$60,$D6
	dc.b $48,$80,$4E,$75,$46,$05,$66,$0A,$CC,$FC,$00,$05,$E2,$4E,$36,$04
	dc.b $60,$0A,$61,$E8,$3C,$00,$76,$00,$16,$2B,$00,$35,$61,$9E,$61,$00
	dc.b $E0,$5A,$6B,$00,$00,$CE,$3F,$01,$61,$92,$32,$1F,$B2,$3C,$00,$1B
	dc.b $67,$00,$A6,$F6,$B2,$3C,$00,$09,$67,$CA,$B2,$3C,$00,$88,$67,$C4
	dc.b $B2,$7C,$00,$82,$67,$00,$00,$C8,$B2,$7C,$00,$83,$67,$00,$00,$E2
	dc.b $B2,$7C,$00,$85,$67,$00,$00,$FE,$B2,$7C,$00,$84,$67,$00,$01,$26
	dc.b $B2,$3C,$00,$08,$67,$00,$01,$1E,$4A,$05,$66,$50,$70,$30,$B2,$00
	dc.b $65,$AA,$B2,$3C,$00,$3A,$65,$12,$02,$01,$00,$DF,$B2,$3C,$00,$41
	dc.b $65,$9A,$B2,$3C,$00,$47,$64,$94,$70,$37,$92,$00,$14,$01,$61,$00
	dc.b $FF,$6C,$41,$F4,$00,$00,$20,$08,$61,$00,$12,$58,$66,$00,$00,$B6
	dc.b $61,$00,$00,$C2,$02,$00,$00,$01,$66,$08,$02,$10,$00,$F0,$85,$10
	dc.b $60,$20,$02,$10,$00,$0F,$E9,$0A,$85,$10,$60,$16,$4A,$01,$67,$00
	dc.b $FF,$5C,$41,$F4,$60,$00,$20,$08,$61,$00,$12,$28,$66,$04,$19,$81
	dc.b $60,$00,$42,$6B,$00,$0A,$48,$E7,$1F,$08,$CE,$EE,$00,$D8,$37,$47
	dc.b $00,$0C,$24,$4C,$61,$00,$FD,$C4,$61,$00,$F7,$A4,$4C,$DF,$10,$F8
	dc.b $60,$62,$3F,$01,$61,$00,$FE,$C6,$32,$1F,$B2,$3C,$00,$45,$67,$00
	dc.b $A6,$28,$3F,$01,$61,$00,$A6,$22,$32,$1F,$60,$00,$A5,$62,$70,$00
	dc.b $10,$2B,$00,$35,$99,$C0,$53,$47,$64,$00,$00,$86,$48,$E7,$1F,$08
	dc.b $61,$00,$FE,$3A,$4C,$DF,$10,$F8,$7E,$00,$61,$00,$DF,$1C,$60,$70
	dc.b $70,$00,$10,$2B,$00,$35,$D9,$C0,$52,$47,$BE,$6B,$00,$06,$66,$60
	dc.b $53,$47,$48,$E7,$1F,$08,$61,$00,$FE,$32,$4C,$DF,$10,$F8,$61,$00
	dc.b $DE,$F8,$60,$4C,$52,$46,$61,$0C,$66,$02,$52,$46,$BC,$43,$66,$40
	dc.b $7C,$00,$60,$CC,$4A,$05,$66,$1A,$70,$00,$30,$06,$72,$01,$08,$2B
	dc.b $00,$00,$00,$3B,$67,$02,$72,$03,$D0,$41,$80,$FC,$00,$05,$48,$40
	dc.b $4A,$40,$4E,$75,$53,$46,$65,$08,$61,$DA,$66,$14,$53,$46,$64,$10
	dc.b $3C,$03,$53,$46,$61,$CE,$66,$00,$FF,$76,$53,$46,$60,$00,$FF,$70
	dc.b $60,$00,$FE,$7A,$61,$00,$08,$2A,$72,$3D,$61,$00,$F6,$5C,$60,$00
	dc.b $08,$20,$43,$EE,$00,$10,$7E,$30,$72,$64,$61,$00,$F6,$4C,$12,$07
	dc.b $61,$00,$F6,$46,$61,$DE,$24,$51,$24,$0A,$61,$00,$08,$1C,$61,$00
	dc.b $08,$00,$61,$00,$07,$FC,$7C,$03,$12,$19,$66,$04,$12,$3C,$00,$B7
	dc.b $61,$00,$F6,$1E,$51,$CE,$FF,$F2,$61,$00,$07,$E6,$61,$00,$07,$E2
	dc.b $61,$00,$07,$DE,$61,$00,$07,$DA,$72,$61,$61,$00,$F6,$0C,$12,$07
	dc.b $61,$00,$F6,$06,$61,$9E,$24,$69,$00,$1C,$61,$00,$FC,$9E,$61,$00
	dc.b $07,$D2,$52,$07,$BE,$3C,$00,$38,$66,$9E,$72,$01,$61,$00,$07,$8A
	dc.b $34,$2E,$00,$5A,$61,$00,$07,$CA,$7E,$05,$61,$00,$07,$A4,$51,$CF
	dc.b $FF,$FA,$38,$2E,$00,$5A,$61,$00,$03,$B8,$61,$00,$07,$A6,$72,$00
	dc.b $61,$00,$07,$66,$24,$2E,$00,$54,$61,$00,$07,$9E,$61,$00,$07,$82
	dc.b $61,$00,$07,$7E,$24,$6E,$00,$54,$51,$EE,$01,$4B,$61,$00,$06,$96
	dc.b $08,$EE,$00,$00,$01,$4B,$67,$4E,$72,$11,$61,$00,$07,$3C,$24,$2E
	dc.b $01,$4E,$2D,$42,$07,$D4,$61,$00,$07,$70,$24,$6E,$01,$4E,$70,$00
	dc.b $10,$2E,$01,$4D,$1C,$3B,$00,$3E,$61,$00,$FC,$68,$4A,$2E,$01,$4C
	dc.b $67,$24,$72,$3E,$61,$00,$F5,$72,$24,$2E,$01,$52,$2D,$42,$07,$D4
	dc.b $61,$00,$07,$46,$24,$6E,$01,$52,$70,$00,$10,$2E,$01,$4D,$1C,$3B
	dc.b $00,$14,$61,$00,$FC,$3E,$50,$EE,$01,$4B,$61,$00,$F4,$C8,$61,$00
	dc.b $07,$22,$60,$04,$01,$02,$04,$08,$0C,$6B,$00,$0A,$00,$06,$63,$00
	dc.b $01,$80,$20,$78,$00,$04,$30,$28,$01,$28,$43,$FA,$02,$14,$08,$00
	dc.b $00,$00,$67,$1E,$43,$FA,$02,$12,$08,$00,$00,$01,$67,$14,$08,$00
	dc.b $00,$03,$66,$0E,$43,$FA,$02,$1C,$08,$00,$00,$02,$67,$04,$43,$FA
	dc.b $02,$44,$61,$00,$01,$60,$4A,$39
	dc.l loc_0_00008906
	dc.b $67,$00,$01,$02,$43,$FA,$02,$88,$61,$00,$01,$4E,$43,$FA,$26,$AE
	dc.b $7E,$00,$72,$66,$61,$00,$F4,$E6,$72,$70,$61,$00,$F4,$E0,$12,$07
	dc.b $61,$00,$F4,$CA,$61,$00,$FE,$72,$F2,$11,$48,$00,$34,$19,$61,$00
	dc.b $06,$B4,$72,$20,$61,$00,$F4,$C6,$54,$49,$24,$19,$61,$00,$06,$9E
	dc.b $72,$20,$61,$00,$F4,$B8,$24,$19,$61,$00,$06,$92,$72,$20,$61,$00
	dc.b $F4,$AC,$2F,$09,$43,$EE,$05,$9C,$F2,$11,$6C,$11,$72,$20,$08,$11
	dc.b $00,$07,$67,$02,$72,$2D,$61,$00,$F4,$94,$32,$19,$00,$41,$80,$00
	dc.b $52,$41,$66,$20,$54,$49,$41,$FA,$02,$2B,$08,$11,$00,$06,$66,$0E
	dc.b $22,$19,$41,$FA,$02,$23,$82,$91,$67,$04,$41,$FA,$02,$16,$61,$00
	dc.b $06,$1C,$60,$60,$52,$49,$12,$19,$02,$01,$00,$0F,$61,$00,$F4,$4E
	dc.b $72,$2E,$61,$00,$F4,$58,$3F,$07,$7E,$07,$10,$19,$61,$00,$00,$98
	dc.b $51,$CF,$FF,$F8,$3E,$1F,$72,$65,$61,$00,$F4,$42,$43,$EE,$05,$9C
	dc.b $72,$2B,$08,$11,$00,$06,$67,$02,$72,$2D,$61,$00,$F4,$30,$F2,$00
	dc.b $A8,$00,$72,$00,$08,$00,$00,$0D,$67,$06,$E9,$E9,$10,$04,$00,$02
	dc.b $61,$00,$F4,$0A,$12,$19,$02,$01,$00,$0F,$61,$00,$F4,$00,$10,$11
	dc.b $61,$00,$00,$54,$22,$5F,$61,$00,$05,$DE,$52,$07,$BE,$3C,$00,$08
	dc.b $66,$00,$FF,$10,$61,$00,$05,$D0,$1F,$2B,$00,$35,$17,$7C,$00,$10
	dc.b $00,$35,$7E,$00,$43,$FA,$0E,$82,$72,$6D,$61,$00,$F3,$E0,$72,$30
	dc.b $D2,$07,$61,$00,$F3,$D8,$61,$00,$FD,$70,$34,$19,$24,$76,$20,$00
	dc.b $61,$00,$FA,$6C,$61,$00,$05,$A0,$52,$47,$BE,$7C,$00,$0A,$66,$D8
	dc.b $17,$5F,$00,$35,$4E,$75,$85,$80,$30,$30,$E9,$C2,$14,$08,$61,$00
	dc.b $F3,$AC,$12,$02,$60,$00,$F3,$A6,$4A,$11,$6B,$00,$05,$7A,$61,$02
	dc.b $60,$F6,$74,$00,$14,$19,$66,$06,$61,$00,$05,$6C,$60,$04,$61,$00
	dc.b $05,$48,$41,$FA,$00,$24,$12,$19,$61,$00,$05,$26,$61,$00,$FD,$1A
	dc.b $3F,$07,$3E,$19,$45,$FA,$23,$C4,$D4,$D9,$14,$1A,$61,$00,$05,$5E
	dc.b $51,$CF,$FF,$F8,$3E,$1F,$4E,$75,$73,$73,$70,$00,$73,$66,$63,$00
	dc.b $64,$66,$63,$00,$76,$62,$72,$00,$6D,$73,$70,$00,$69,$73,$70,$00
	dc.b "cacr",$00	; string
	dc.b "caar",$00	; string
	dc.b "mmusr",$00	; string
	dc.b $74,$63,$00,$74,$74,$30,$00,$74,$74,$31,$00,$63,$72,$70,$00,$73
	dc.b $72,$70,$00
	dc.b "fpcr",$00	; string
	dc.b "fpsr",$00	; string
	dc.b "fpiar",$00	; string
	dc.b $00,$00,$00,$00,$03,$00,$0A,$FF,$00,$00,$00,$00,$03,$00,$0A,$03
	dc.b $01,$00,$00,$00,$5C,$00,$03,$00,$03,$00,$5E,$03,$02,$00,$00,$00
	dc.b $5D,$FF,$00,$00,$00,$00,$03,$00,$0A,$03,$04,$00,$03,$00,$62,$03
	dc.b $01,$00,$00,$00,$5C,$03,$06,$00,$01,$00,$6E,$00,$03,$00,$03,$00
	dc.b $5E,$03,$05,$00,$03,$00,$66,$03,$02,$00,$00,$00,$5D,$03,$07,$00
	dc.b $03,$00,$6A,$FF,$00,$00,$00,$00,$03,$00,$0A,$04,$01,$00,$00,$00
	dc.b $5C,$06,$08,$00,$01,$00,$70,$07,$0C,$00,$07,$00,$7E,$00,$03,$00
	dc.b $03,$00,$5E,$04,$02,$00,$00,$00,$5D,$09,$09,$00,$03,$00,$72,$03
	dc.b $0D,$00,$07,$00,$86,$00,$05,$00,$03,$00,$66,$03,$06,$00,$01,$00
	dc.b $6E,$06,$0A,$00,$03,$00,$76,$00,$04,$00,$03,$00,$62,$03,$07,$00
	dc.b $03,$00,$6A,$02,$0B,$00,$03,$00,$7A,$FF,$00,$00,$0E,$00,$01,$01
	dc.b $68,$02,$0F,$00,$03,$01,$6A,$02,$10,$00,$03,$01,$6E,$FF,$00,$73
	dc.b $6E,$61,$6E,$00,$69,$6E,$66,$69,$6E,$69,$74,$79,$00,$61,$00,$03
	dc.b $FA,$24,$11,$60,$00,$04,$24,$61,$00,$03,$F0,$24,$11,$61,$00,$04
	dc.b $1A,$24,$29,$00,$04,$60,$00,$04,$12,$67,$0C,$12,$18,$61,$00,$F2
	dc.b $2A,$12,$18,$60,$00,$F2,$24,$54,$88,$61,$00,$03,$E6,$60,$00,$03
	dc.b $E2,$41,$FA,$00,$48,$08,$04,$00,$0F,$61,$DE,$08,$04,$00,$0E,$61
	dc.b $D8,$72,$53,$08,$04,$00,$0D,$66,$02,$72,$55,$61,$00,$F1,$FC,$72
	dc.b $4D,$08,$04,$00,$0C,$66,$02,$72,$49,$61,$00,$F1,$EE,$74,$04,$08
	dc.b $04,$00,$04,$61,$08,$D8,$04,$51,$CA,$FF,$F6,$4E,$75,$67,$06,$12
	dc.b $18,$60,$00,$F1,$D6,$52,$88,$60,$00,$03,$98,$54,$30,$54,$31,$58
	dc.b $4E,$5A,$56,$43,$00,$60,$00,$FB,$6C,$60,$0C,$60,$0A,$60,$08,$60
	dc.b $06,$60,$04,$60,$02,$4E,$71,$72,$1B,$4E,$75,$24,$6B,$00,$38,$3C
	dc.b $2B,$00,$06,$4A,$2B,$00,$35,$66,$14,$74,$08,$20,$0A,$61,$00,$17
	dc.b $D8,$66,$20,$24,$0A,$61,$00,$03,$72,$74,$00,$60,$1A,$24,$0A,$61
	dc.b $00,$03,$68,$61,$00,$03,$4C,$20,$0A,$14,$2B,$00,$35,$61,$00,$17
	dc.b $B8,$67,$04,$61,$00,$14,$92,$61,$00,$03,$2C,$72,$20,$B5,$EE,$00
	dc.b $54,$66,$02,$72,$3E,$61,$00,$F1,$62,$61,$00,$02,$94,$2F,$0A,$61
	dc.b $00,$F0,$D4,$61,$00,$03,$2E,$24,$5F,$53,$06,$66,$A6,$4E,$75,$61
	dc.b $50,$55,$8A,$27,$4A,$00,$38,$70,$FF,$4E,$75,$61,$44,$54,$8A,$60
	dc.b $F2,$60,$00,$FF,$88,$60,$0A,$60,$18,$60,$4C,$60,$42,$60,$E0,$60
	dc.b $EA,$30,$2B,$00,$06,$D0,$40,$48,$C0,$91,$AB,$00,$38,$70,$FF,$4E
	dc.b $75,$20,$2B,$00,$38,$52,$80,$08,$80,$00,$00,$24,$40,$3C,$2B,$00
	dc.b $06,$61,$00,$01,$B0,$53,$06,$66,$F8,$27,$4A,$00,$38,$72,$FF,$4E
	dc.b $75,$20,$2B,$00,$38,$52,$80,$08,$80,$00,$00,$24,$40,$4E,$75,$61
	dc.b $F0,$61,$00,$01,$90,$60,$E2,$61,$E8,$61,$00,$D3,$FA,$60,$DA,$24
	dc.b $6B,$00,$38,$3C,$2B,$00,$06,$38,$2B,$00,$36,$53,$46,$61,$00,$00
	dc.b $FC,$57,$CE,$FF,$FA,$66,$10,$4A,$46,$6B,$0C,$61,$00,$F0,$38,$61
	dc.b $00,$02,$92,$51,$CE,$FF,$F6,$4E,$75,$B5,$EE,$01,$56,$67,$18,$0C
	dc.b $22,$00,$0A,$66,$F4,$B5,$EE,$01,$56,$67,$08,$0C,$22,$00,$0A,$66
	dc.b $F4,$52,$8A,$53,$44,$70,$FF,$4E,$75,$70,$00,$4E,$75,$60,$00,$FF
	dc.b $B0,$60,$32,$60,$46,$60,$06,$60,$64,$60,$EE,$60,$EC,$24,$6B,$00
	dc.b $38,$38,$2B,$00,$36,$61,$C2,$67,$18,$2F,$0A,$61,$00,$EF,$DE,$61
	dc.b $00,$EF,$E4,$24,$5F,$37,$44,$00,$36,$27,$4A,$00,$38,$61,$00,$00
	dc.b $8C,$70,$00,$4E,$75,$24,$6B,$00,$38,$34,$2B,$00,$06,$38,$2B,$00
	dc.b $36,$53,$42,$61,$94,$57,$CA,$FF,$FC,$60,$16,$24,$6B,$00,$38,$38
	dc.b $2B,$00,$36,$34,$2B,$00,$06,$53,$42,$61,$4C,$67,$46,$51,$CA,$FF
	dc.b $FA,$27,$4A,$00,$38,$37,$44,$00,$36,$70,$FF,$4E,$75,$24,$6B,$00
	dc.b $38,$38,$2B,$00,$36,$34,$2B,$00,$06,$53,$42,$61,$2A,$67,$24,$51
	dc.b $CA,$FF,$FA,$2F,$0A,$61,$00,$EF,$5C,$61,$00,$EF,$7A,$24,$5F,$61
	dc.b $2A,$24,$6B,$00,$38,$38,$2B,$00,$36,$61,$0C,$27,$4A,$00,$38,$37
	dc.b $44,$00,$36,$70,$00,$4E,$75,$B5,$EE,$01,$5A,$67,$00,$00,$84,$0C
	dc.b $1A,$00,$0A,$66,$F2,$52,$44,$70,$FF,$4E,$75,$B5,$EE,$01,$5A,$67
	dc.b $70,$4A,$2E,$05,$84,$67,$1C,$6B,$0E,$72,$00,$32,$04,$2F,$0A,$61
	dc.b $00,$01,$CC,$24,$5F,$60,$06,$34,$04,$61,$00,$01,$96,$61,$00,$01
	dc.b $72,$76,$00,$B5,$EE,$01,$5A,$67,$48,$12,$1A,$B2,$3C,$00,$0D,$67
	dc.b $F2,$B2,$3C,$00,$0A,$67,$2A,$B2,$3C,$00,$09,$67,$08,$61,$00,$EF
	dc.b $8A,$52,$43,$60,$DE,$34,$03,$72,$00,$12,$2B,$00,$35,$53,$41,$46
	dc.b $41,$C4,$41,$D4,$2B,$00,$35,$94,$43,$D6,$42,$61,$00,$01,$28,$60
	dc.b $C2,$2F,$0A,$61,$00,$EE,$E0,$24,$5F,$61,$00,$01,$38,$52,$44,$70
	dc.b $FF,$4E,$75
loc_0_00006964:
	bsr.w loc_0_0000736A
	bne.b loc_0_000069A2
	lea.l $000A(a2),a2
	bsr.w loc_0_0000736A
	lea.l -$000A(a2),a2
	bne.b loc_0_000069A2
	movem.l d4-d7/a3-a5,-(a7)
	movea.l a2,a5
	move.l app_00AE(a6),-(a7)
	move.l app_0136(a6),-(a7)
	clr.l app_00AE(a6)
	clr.l app_0136(a6)
	bsr.w loc_0_00001C78
	move.l (a7)+,app_0136(a6)
	move.l (a7)+,app_00AE(a6)
	movea.l a5,a2
	movem.l (a7)+,d4-d7/a3-a5
	rts
loc_0_000069A2:
	addq.w #2,a2
	rts
	dc.b $20,$0A,$52,$80,$08,$80,$00,$00,$24,$40,$61,$00,$09,$B8,$66,$00
	dc.b $00,$9C,$45,$EA,$00,$0A,$61,$00,$09,$AC,$45,$EA,$FF,$F6,$66,$00
	dc.b $00,$8C,$48,$E7,$0F,$1C,$2A,$4A,$61,$00,$B2,$A8,$24,$4D,$24,$0C
	dc.b $94,$8E,$04,$42,$09,$AA,$4C,$DF,$38,$F0,$41,$EE,$09,$A8,$12,$18
	dc.b $61,$00,$EE,$D2,$51,$CA,$FF,$F8,$4E,$75,$20,$0A,$52,$80,$08,$80
	dc.b $00,$00,$24,$40,$61,$00,$09,$6E,$66,$52,$45,$EA,$00,$0A,$61,$00
	dc.b $09,$64,$45,$EA,$FF,$F6,$66,$44,$48,$E7,$0F,$1C,$2A,$4A,$61,$00
	dc.b $B2,$62,$24,$4D,$24,$0C,$94,$8E,$04,$42,$09,$AA,$4C,$DF,$38,$F0
	dc.b $41,$EE,$09,$A8,$12,$18,$B2,$3C,$00,$20,$66,$16,$3F,$02,$74,$08
	dc.b $94,$88,$48,$6E,$09,$A8,$D4,$9F,$6B,$04,$61,$00,$00,$34,$34,$1F
	dc.b $72,$20,$61,$00,$EE,$70,$51,$CA,$FF,$DC,$4E,$75,$54,$8A,$72,$2A
	dc.b $60,$00,$EE,$62
loc_0_00006A5A:
	lea.l loc_0_00008217(pc),a0
	tst.b d1
	beq.b loc_0_00006A6A
loc_0_00006A62:
	tst.b (a0)+
	bne.b loc_0_00006A62
	subq.b #1,d1
	bne.b loc_0_00006A62
loc_0_00006A6A:
	move.b (a0)+,d1
	beq.b loc_0_00006A74
	bsr.w loc_0_000058BA
	bra.b loc_0_00006A6A
loc_0_00006A74:
	rts
loc_0_00006A76:
	tst.b d2
loc_0_00006A78:
	beq.b loc_0_00006A80
	bsr.b loc_0_00006A82
	subq.b #1,d2
	bra.b loc_0_00006A78
loc_0_00006A80:
	rts
loc_0_00006A82:
	moveq.l #32,d1
	bra.w loc_0_000058BA
	dc.b $72,$2A,$61,$00,$EE,$2E,$72,$2A,$60,$00,$EE,$28,$72,$0A,$60,$00
	dc.b $EE,$22,$3F,$02,$48,$42,$61,$02,$34,$1F,$3F,$02,$E0,$4A,$61,$02
	dc.b $34,$1F,$3F,$02,$E8,$0A,$61,$02,$34,$1F,$02,$42,$00,$0F,$12,$3B
	dc.b $20,$06,$60,$00,$ED,$FE,$30,$31,$32,$33,$34,$35,$36,$37,$38,$39
	dc.b $41,$42,$43,$44,$45,$46,$45,$FA,$ED,$EA,$41,$FA,$00,$54,$74,$FF
	dc.b $70,$03,$60,$0C,$45,$FA,$ED,$DC
loc_0_00006AE0:
	lea.l loc_0_00006B14(pc),a0
	moveq.l #1,d2
	moveq.l #8,d0
loc_0_00006AE8:
	moveq.l #0,d3
	cmp.l (a0)+,d1
	bcs.b loc_0_00006AFA
	sub.l -(a0),d1
loc_0_00006AF0:
	addq.b #1,d3
	sub.l (a0),d1
	bcc.b loc_0_00006AF0
	add.l (a0)+,d1
	bra.b loc_0_00006AFE
loc_0_00006AFA:
	tst.b d2
	bpl.b loc_0_00006B0A
loc_0_00006AFE:
	st.b d2
	addi.b #48,d3
	exg d3,d1
	jsr (a2)
	exg d3,d1
loc_0_00006B0A:
	dbf.w d0,loc_0_00006AE8
	addi.b #48,d1
	jmp (a2)
loc_0_00006B14:
	dc.b $3B,$9A,$CA,$00,$05,$F5,$E1,$00,$00,$98,$96,$80,$00,$0F,$42,$40
	dc.b $00,$01,$86,$A0,$00,$00,$27,$10,$00,$00,$03,$E8,$00,$00,$00,$64
	dc.b $00,$00,$00,$0A,$2F,$0C,$50,$EE,$08,$15,$61,$00,$00,$30,$66,$0E
	dc.b $4A,$01,$66,$0A,$51,$EE,$08,$15,$70,$00,$28,$5F,$4E,$75,$51,$EE
	dc.b $08,$15,$70,$FF,$28,$5F,$4E,$75,$61,$12,$66,$04,$4A,$01,$67,$06
	dc.b $61,$00,$F2,$EE,$70,$FF,$4E,$75,$61,$04,$60,$EE
loc_0_00006B70:
	move.b (a4)+,d1
	lea.l app_07EC(a6),a0
	clr.w (a0)
	lea.l app_0800(a6),a0
	clr.w (a0)
	clr.b app_0814(a6)
	movem.l d4-d7,-(a7)
	bsr.w loc_0_00006C10
	movem.l (a7)+,d4-d7
	tst.w app_07EC(a6)
	bne.b loc_0_00006BA0
	tst.w app_0800(a6)
	bne.b loc_0_00006BA0
	move.b app_0814(a6),d0
	rts
loc_0_00006BA0:
	moveq.l #1,d0
	rts
loc_0_00006BA4:
	dc.b $13,$2B,$14,$2D,$06,$2A,$07,$2F,$02,$28,$03,$29,$15,$7E,$17,$23
	dc.b $18,$3F,$0A,$3D,$10,$26,$11,$7C,$11,$21,$12,$5E,$04,$7B,$05,$7D
	dc.b $FE,$24,$FC,$25,$FA,$40,$F8,$27,$F8,$22,$F6,$5C,$00
loc_0_00006BD1:
	dc.b $00,$00,$00,$00,$00,$00,$04,$04,$16,$16,$01,$01,$01,$01,$01,$01
	dc.b $12,$12,$12,$02,$02,$1D,$1E,$1F,$1F
loc_0_00006BEA:
	dc.b $02,$F0,$02,$36,$02,$54,$02,$58,$02,$5C,$02,$72,$02,$66,$02,$6C
	dc.b $02,$78,$02,$7E,$02,$48,$02,$4C,$02,$50,$02,$2E,$02,$32,$02,$84
	dc.b $02,$88,$02,$8C,$02,$BC
loc_0_00006C10:
	lea.l app_07EC(a6),a0
	move.w (a0),d0
	addq.w #2,(a0)+
	move.w #$0,$0(a0,d0.w)
	moveq.l #1,d5
	bsr.w loc_0_00006F9C
loc_0_00006C24:
	cmp.b #$2,d5
	bne.b loc_0_00006C3A
	cmp.b #$6,d7
	bcs.w loc_0_00006D88
	cmp.b #$19,d7
	bcc.w loc_0_00006D88
loc_0_00006C3A:
	cmp.b #$1,d7
	bne.b loc_0_00006C50
loc_0_00006C40:
	lea.l app_0800(a6),a0
	move.w (a0),d0
	addq.w #4,(a0)+
	move.l d2,$0(a0,d0.w)
	bra.w loc_0_00006D7E
loc_0_00006C50:
	cmp.b #$2,d7
	beq.b loc_0_00006CD0
	cmp.b #$4,d7
	beq.w loc_0_00006CF2
	cmp.b #$6,d7
	bcs.w loc_0_00006D9A
	cmp.b #$19,d7
	bcc.w loc_0_00006D9A
	cmp.b #$1,d5
	bne.b loc_0_00006CA4
	cmp.b #$13,d7
	beq.b loc_0_00006CA4
	cmp.b #$14,d7
	beq.b loc_0_00006CA2
	cmp.b #$6,d7
	beq.b loc_0_00006C9C
	cmp.b #$17,d7
	beq.b loc_0_00006CA4
	cmp.b #$18,d7
	beq.b loc_0_00006CA4
	cmp.b #$15,d7
	bne.w loc_0_00006BA0
	bra.b loc_0_00006CA4
loc_0_00006C9C:
	move.l $0054(a6),d2
	bra.b loc_0_00006C40
loc_0_00006CA2:
	moveq.l #22,d7
loc_0_00006CA4:
	lea.l loc_0_00006BD1(pc),a2
	lea.l app_07EC(a6),a0
	move.w (a0),d0
	move.w $0(a0,d0.w),d6
	move.b $0(a2,d6.w),d6
	cmp.b $0(a2,d7.w),d6
	bge.b loc_0_00006CC4
	addq.w #2,(a0)+
	move.w d7,$0(a0,d0.w)
	bra.b loc_0_00006CCA
loc_0_00006CC4:
	bsr.w loc_0_00006DD0
	bra.b loc_0_00006CA4
loc_0_00006CCA:
	moveq.l #0,d5
	bra.w loc_0_00006D7E
loc_0_00006CD0:
	bsr.w loc_0_00006C10
	lea.l app_0800(a6),a0
	move.w (a0),d0
	addq.w #4,(a0)+
	move.l d2,$0(a0,d0.w)
	cmp.b #$3,d7
	beq.b loc_0_00006CEC
loc_0_00006CE6:
	move.b #$2,app_0814(a6)
loc_0_00006CEC:
	moveq.l #1,d5
	bra.w loc_0_00006D7E
loc_0_00006CF2:
	bsr.w loc_0_00006C10
	cmp.b #$5,d7
	bne.b loc_0_00006CE6
	cmp.b #$2E,d1
	bne.b loc_0_00006D48
	move.b (a4)+,d0
	move.b (a4)+,d1
	andi.b #223,d0
	cmp.b #$42,d0
	beq.b loc_0_00006D24
	cmp.b #$57,d0
	beq.b loc_0_00006D34
	cmp.b #$4C,d0
	beq.b loc_0_00006D48
	move.b #$7,app_0814(a6)
	bra.b loc_0_00006D7E
loc_0_00006D24:
	movea.l d2,a2
	bsr.w loc_0_0000736A
	bne.b loc_0_00006D72
	movea.l d2,a0
	moveq.l #0,d2
	move.b (a0),d2
	bra.b loc_0_00006D62
loc_0_00006D34:
	btst #0,d2
	bne.b loc_0_00006D72
	movea.l d2,a2
	bsr.w loc_0_0000736A
	bne.b loc_0_00006D72
	moveq.l #0,d2
	move.w (a2),d2
	bra.b loc_0_00006D62
loc_0_00006D48:
	btst #0,d2
	bne.b loc_0_00006D72
	movea.l d2,a2
	bsr.w loc_0_0000736A
	bne.b loc_0_00006D72
	addq.l #3,a2
	bsr.w loc_0_0000736A
	bne.b loc_0_00006D72
	movea.l d2,a0
	move.l (a0),d2
loc_0_00006D62:
	lea.l app_0800(a6),a0
	move.w (a0),d0
	addq.w #4,(a0)+
	move.l d2,$0(a0,d0.w)
	moveq.l #1,d5
	bra.b loc_0_00006D7E
loc_0_00006D72:
	tst.b app_0815(a6)
	bne.b loc_0_00006D62
	move.b #$6,app_0814(a6)
loc_0_00006D7E:
	addq.w #1,d5
	bsr.w loc_0_00006F9C
	bra.w loc_0_00006C24
loc_0_00006D88:
	cmp.b #$3,d7
	beq.b loc_0_00006D9A
	cmp.b #$5,d7
	beq.b loc_0_00006D9A
	movea.l a0,a4
	move.b -$0001(a4),d1
loc_0_00006D9A:
	lea.l loc_0_00006BD1(pc),a2
loc_0_00006D9E:
	lea.l app_07EC(a6),a0
	move.w (a0),d0
	tst.w $0(a0,d0.w)
	beq.b loc_0_00006DB0
	bsr.w loc_0_00006DD0
	bra.b loc_0_00006D9E
loc_0_00006DB0:
	subq.w #2,app_07EC(a6)
	lea.l app_0800(a6),a0
	subq.w #4,(a0)
	move.w (a0)+,d0
	move.l $0(a0,d0.w),d2
	rts
loc_0_00006DC2:
	move.w (a7)+,d1
loc_0_00006DC4:
	move.w #$4,(a0)
	move.b #$8,app_0814(a6)
	rts
loc_0_00006DD0:
	lea.l app_0800(a6),a0
	subq.w #4,(a0)
	bcs.b loc_0_00006DC4
	move.w (a0)+,d0
	move.l $0(a0,d0.w),d2
	move.w d1,-(a7)
	lea.l app_07EC(a6),a1
	subq.w #2,(a1)
	move.w (a1)+,d1
	move.w $0(a1,d1.w),d1
	cmp.b #$15,d1
	bcc.b loc_0_00006DFE
	subq.w #4,-(a0)
	bcs.b loc_0_00006DC2
	move.w (a0)+,d0
	move.l $0(a0,d0.w),d0
	exg d0,d2
loc_0_00006DFE:
	lea.l loc_0_00006BEA(pc),a1
	add.w d1,d1
	move.w -$C(a1,d1.w),d1
	jsr $0(a1,d1.w)
	move.w (a7)+,d1
	move.w -(a0),d0
	addq.w #4,(a0)+
	move.l d2,$0(a0,d0.w)
	rts
	dc.b $D4,$80,$4E,$75,$94,$80,$4E,$75,$2F,$07,$61,$00,$00,$EA,$4C,$DF
	dc.b $00,$80,$67,$04,$1D,$40,$08,$14,$4E,$75,$C4,$80,$4E,$75,$84,$80
	dc.b $4E,$75,$B1,$82,$4E,$75,$E1,$AA,$4E,$75,$E0,$AA,$4E,$75,$B4,$80
	dc.b $57,$C2,$48,$82,$48,$C2,$4E,$75,$B4,$80,$5D,$C2,$60,$F4,$B4,$80
	dc.b $5E,$C2,$60,$EE,$B4,$80,$56,$C2,$60,$E8,$B4,$80,$5F,$C2,$60,$E2
	dc.b $B4,$80,$5C,$C2,$60,$DC,$46,$82,$4E,$75,$44,$82,$4E,$75,$48,$E7
	dc.b $C0,$80,$22,$2E,$05,$7C,$67,$22,$20,$6E,$05,$80,$B4,$90,$65,$10
	dc.b $53,$81,$60,$04,$B4,$90,$65,$06,$50,$88,$57,$C9,$FF,$F8,$51,$88
	dc.b $24,$28,$00,$04,$4C,$DF,$01,$03,$4E,$75,$74,$00,$60,$F6
loc_0_00006EA6:
	movem.l d0-d1/a0,-(a7)
	move.l app_057C(a6),d1
	beq.b loc_0_00006ED2
	movea.l app_0580(a6),a0
	cmp.l $0004(a0),d2
	bcs.b loc_0_00006ED2
	subq.l #1,d1
	bra.b loc_0_00006EC4
loc_0_00006EBE:
	cmp.l $0004(a0),d2
	bcs.b loc_0_00006ECC
loc_0_00006EC4:
	addq.l #8,a0
	dbeq.w d1,loc_0_00006EBE
	bne.b loc_0_00006ED2
loc_0_00006ECC:
	move.l -$0008(a0),d2
	bra.b loc_0_00006ED4
loc_0_00006ED2:
	moveq.l #0,d2
loc_0_00006ED4:
	movem.l (a7)+,d0-d1/a0
	rts
	dc.b $2C,$02,$B1,$86,$4A,$82,$6E,$02,$44,$82,$4A,$80,$6E,$02,$44,$80
	dc.b $26,$02,$48,$43,$C4,$C0,$48,$40,$4A,$43,$67,$04,$48,$40,$60,$06
	dc.b $4A,$40,$67,$08,$48,$43,$C0,$C3,$48,$40,$D4,$80,$4A,$86,$6A,$02
	dc.b $44,$82,$4E,$75
loc_0_00006F0E:
	tst.l d0
	beq.b loc_0_00006F5C
	move.l d2,d6
	eor.l d0,d6
	move.l d6,-(a7)
	move.l d2,-(a7)
	tst.l d0
	bpl.b loc_0_00006F20
	neg.l d0
loc_0_00006F20:
	tst.l d2
	bpl.b loc_0_00006F26
	neg.l d2
loc_0_00006F26:
	moveq.l #31,d6
	move.l d0,d7
	moveq.l #0,d0
loc_0_00006F2C:
	add.l d7,d7
	dbcs.w d6,loc_0_00006F2C
	roxr.l #1,d7
	subi.w #31,d6
	neg.w d6
loc_0_00006F3A:
	add.l d0,d0
	cmp.l d7,d2
	bcs.b loc_0_00006F44
	addq.l #1,d0
	sub.l d7,d2
loc_0_00006F44:
	lsr.l #1,d7
	dbf.w d6,loc_0_00006F3A
	move.l (a7)+,d6
	bpl.b loc_0_00006F50
	neg.l d2
loc_0_00006F50:
	move.l (a7)+,d6
	bpl.b loc_0_00006F56
	neg.l d0
loc_0_00006F56:
	exg d0,d2
	cmp.b d0,d0
	rts
loc_0_00006F5C:
	moveq.l #3,d0
	rts
loc_0_00006F60:
	tst.b d1
	bmi.b loc_0_00006F98
	cmp.b #$2E,d1
	beq.b loc_0_00006F98
	cmp.b #$30,d1
	bcs.b loc_0_00006F94
	cmp.b #$3A,d1
	bcs.b loc_0_00006F98
	cmp.b #$40,d1
	bcs.b loc_0_00006F94
	cmp.b #$5B,d1
	bcs.b loc_0_00006F98
	cmp.b #$5F,d1
	beq.b loc_0_00006F98
	cmp.b #$61,d1
	bcs.b loc_0_00006F94
	cmp.b #$7B,d1
	bcs.b loc_0_00006F98
loc_0_00006F94:
	moveq.l #-1,d0
	rts
loc_0_00006F98:
	moveq.l #0,d0
	rts
loc_0_00006F9C:
	movem.l d5-d6/a1-a2,-(a7)
	move.l a4,-(a7)
	moveq.l #0,d7
	lea.l loc_0_00006BA4(pc),a0
loc_0_00006FA8:
	move.b (a0)+,d7
	beq.b loc_0_00006FBA
	cmp.b (a0)+,d1
	bne.b loc_0_00006FA8
	tst.b d7
	bmi.w loc_0_00007088
	bra.w loc_0_0000703A
loc_0_00006FBA:
	cmp.b #$3C,d1
	beq.b loc_0_0000700E
	cmp.b #$3E,d1
	beq.b loc_0_00007024
	moveq.l #0,d2
	cmp.b #$3A,d1
	bcc.b loc_0_00006FD4
	cmp.b #$30,d1
	bcc.b loc_0_00007044
loc_0_00006FD4:
	moveq.l #1,d7
	bsr.b loc_0_00006F60
	bne.b loc_0_0000700A
	lea.l -$0001(a4),a1
	moveq.l #0,d2
loc_0_00006FE0:
	addq.w #1,d2
	move.b (a4)+,d1
	bsr.w loc_0_00006F60
	beq.b loc_0_00006FE0
	bsr.w loc_0_000071F2
	bne.b loc_0_00006FF6
	move.l (a0),d2
	bra.w loc_0_00007084
loc_0_00006FF6:
	move.l a1,-(a7)
	bsr.w loc_0_000075B2
	movea.l (a7)+,a1
	beq.w loc_0_00007084
	movea.l a1,a4
	moveq.l #0,d2
	bra.w loc_0_00007112
loc_0_0000700A:
	moveq.l #25,d7
	bra.b loc_0_0000703C
loc_0_0000700E:
	moveq.l #12,d7
	move.b (a4)+,d1
	cmp.b #$3C,d1
	beq.b loc_0_00007038
	cmp.b #$3E,d1
	beq.b loc_0_00007020
	bra.b loc_0_0000702E
loc_0_00007020:
	moveq.l #11,d7
	bra.b loc_0_0000703A
loc_0_00007024:
	moveq.l #13,d7
	move.b (a4)+,d1
	cmp.b #$3E,d1
	beq.b loc_0_00007038
loc_0_0000702E:
	cmp.b #$3D,d1
	bne.b loc_0_0000703C
	addq.w #2,d7
	bra.b loc_0_0000703A
loc_0_00007038:
	subq.w #4,d7
loc_0_0000703A:
	move.b (a4)+,d1
loc_0_0000703C:
	movea.l (a7)+,a0
	movem.l (a7)+,d5-d6/a1-a2
	rts
loc_0_00007044:
	moveq.l #0,d2
	subq.l #1,a4
	moveq.l #1,d7
	bra.w loc_0_00007112
	dc.b $12,$1C,$B2,$3C,$00,$30,$65,$00,$00,$E8,$B2,$3C,$00,$3A,$64,$00
	dc.b $00,$E0,$D4,$82,$20,$02,$D0,$80,$D0,$80,$D4,$80,$04,$01,$00,$30
	dc.b $02,$81,$00,$00,$00,$0F,$D4,$81,$12,$1C,$B2,$3C,$00,$3A,$64,$06
	dc.b $B2,$3C,$00,$30,$64,$DC
loc_0_00007084:
	moveq.l #1,d7
	bra.b loc_0_0000703C
loc_0_00007088:
	neg.b d7
	ext.w d7
	moveq.l #0,d2
	moveq.l #1,d0
	exg d0,d7
	jmp $0(pc,d0.w)
	dc.b $60,$7A,$60,$2C,$60,$4E,$60,$02,$60,$AE,$70,$04,$16,$01,$12,$1C
	dc.b $B2,$3C,$00,$0A,$67,$00,$00,$92,$B2,$03,$66,$08,$12,$1C,$B2,$03
	dc.b $67,$02,$60,$82,$53,$00,$65,$00,$00,$8E,$E1,$8A,$14,$01,$60,$DE
	dc.b $12,$1C,$04,$01,$00,$30,$65,$70,$B2,$3C,$00,$02,$64,$6A,$D4,$82
	dc.b $65,$74,$84,$01,$12,$1C,$04,$01,$00,$30,$65,$4E,$B2,$3C,$00,$02
	dc.b $65,$EC,$60,$46,$10,$14,$04,$00,$00,$30,$65,$46,$B0,$3C,$00,$09
	dc.b $64,$40,$12,$00,$52,$8C,$E7,$8A,$65,$4C,$84,$01,$12,$1C,$04,$01
	dc.b $00,$30,$65,$26,$B2,$3C,$00,$09,$65,$EC,$60,$1E
loc_0_00007112:
	lea.l loc_0_00007150(pc),a0
	moveq.l #0,d1
	move.b (a4)+,d1
	bmi.b loc_0_0000713E
	move.b $0(a0,d1.w),d1
	bmi.b loc_0_0000713E
loc_0_00007122:
	lsl.l #4,d2
	or.b d1,d2
	move.b (a4)+,d1
	bmi.b loc_0_00007130
	move.b $0(a0,d1.w),d1
	bpl.b loc_0_00007122
loc_0_00007130:
	move.b -$0001(a4),d1
	bra.w loc_0_0000703C
	dc.b $72,$40,$60,$00,$FE,$98
loc_0_0000713E:
	moveq.l #4,d0
	tst.b app_0814(a6)
	bne.b loc_0_00007130
	move.b d0,app_0814(a6)
	bra.b loc_0_00007130
	dc.b $70,$05,$60,$F0
loc_0_00007150:
	dcb.b $30,$FF
	dc.b $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$FF,$FF,$FF,$FF,$FF,$FF
	dc.b $FF,$0A,$0B,$0C,$0D,$0E,$0F
	dcb.b $1A,$FF
	dc.b $0A,$0B,$0C,$0D,$0E,$0F
	dcb.b $19,$FF
loc_0_000071D0:
	move.b $0001(a1),d0
	subi.b #48,d0
	bcs.b loc_0_00007202
	cmp.b #$A,d0
	bcc.b loc_0_00007202
	ext.w d0
	add.w d0,d0
	lea.l loc_0_00007356(pc),a0
	move.w $0(a0,d0.w),d0
	lea.l $0(a6,d0.w),a0
	bra.b loc_0_0000726A
loc_0_000071F2:
	move.b (a1),d0
	andi.b #223,d0
	cmp.w #$2,d2
	beq.b loc_0_00007206
	bcc.w loc_0_0000728A
loc_0_00007202:
	moveq.l #-1,d0
	rts
loc_0_00007206:
	lea.l app_0030(a6),a0
	cmp.b #$41,d0
	beq.b loc_0_0000726E
	lea.l app_0010(a6),a0
	cmp.b #$44,d0
	beq.b loc_0_0000726E
	cmp.b #$53,d0
	beq.b loc_0_00007242
	cmp.b #$4D,d0
	beq.b loc_0_000071D0
	cmp.b #$50,d0
	bne.b loc_0_00007202
	lea.l $0054(a6),a0
	cmpi.b #67,$0001(a1)
	beq.b loc_0_0000726A
	cmpi.b #99,$0001(a1)
	beq.b loc_0_0000726A
	bra.b loc_0_00007202
loc_0_00007242:
	move.b $0001(a1),d0
	andi.b #223,d0
	lea.l app_0058(a6),a0
	cmp.b #$52,d0
	beq.b loc_0_0000726A
	cmp.b #$50,d0
	bne.b loc_0_00007202
	lea.l app_004C(a6),a0
	btst.b #5,app_005A(a6)
	beq.b loc_0_0000726A
	lea.l app_0050(a6),a0
loc_0_0000726A:
	moveq.l #0,d0
	rts
loc_0_0000726E:
	move.b $0001(a1),d0
	subi.b #48,d0
	bcs.b loc_0_00007202
	cmp.b #$8,d0
	bcc.b loc_0_00007202
	andi.w #15,d0
	add.w d0,d0
	add.w d0,d0
	adda.w d0,a0
	bra.b loc_0_0000726A
loc_0_0000728A:
	movem.l d1/d3/a1,-(a7)
	move.b #$DF,d3
	cmp.w #$3,d2
	bne.b loc_0_000072C6
	move.b (a1)+,d1
	and.b d3,d1
	cmp.b #$53,d1
	bne.b loc_0_000072C2
	move.b (a1)+,d1
	and.b d3,d1
	cmp.b #$53,d1
	bne.b loc_0_000072C2
	move.b (a1)+,d1
	and.b d3,d1
	cmp.b #$50,d1
	bne.b loc_0_000072C2
	lea.l app_0050(a6),a0
	moveq.l #0,d1
loc_0_000072BC:
	movem.l (a7)+,d1/d3/a1
	rts
loc_0_000072C2:
	moveq.l #-1,d1
	bra.b loc_0_000072BC
loc_0_000072C6:
	cmp.w #$4,d2
	beq.b loc_0_000072CE
	bcs.b loc_0_000072C2
loc_0_000072CE:
	clr.l -(a7)
	movea.l a7,a0
	move.b (a1)+,d1
	and.b d3,d1
	move.b d1,(a0)+
	move.b (a1)+,d1
	and.b d3,d1
	move.b d1,(a0)+
	move.b (a1)+,d1
	and.b d3,d1
	move.b d1,(a0)+
	move.b (a1)+,d1
	and.b d3,d1
	move.b d1,(a0)+
	move.l (a7)+,d1
	cmp.l #$434F4445,d1
	beq.b loc_0_00007304
	cmp.l #$48554E4B,d1
	bne.b loc_0_000072C2
	cmp.w #$4,d2
	bne.b loc_0_00007310
	bra.b loc_0_000072C2
loc_0_00007304:
	cmp.w #$4,d2
	bne.b loc_0_000072C2
	lea.l app_00AA(a6),a0
	bra.b loc_0_000072BC
loc_0_00007310:
	move.w d2,d0
	subq.w #4,d0
	moveq.l #0,d3
loc_0_00007316:
	move.b (a1)+,d1
	subi.b #48,d1
	bcs.b loc_0_000072C2
	cmp.b #$A,d1
	bcc.b loc_0_000072C2
	mulu.w #$A,d3
	ext.w d1
	add.w d1,d3
	subq.w #1,d0
	bne.b loc_0_00007316
	lea.l loc_0_000088F6(pc),a0
loc_0_00007334:
	subq.w #1,d3
	bmi.b loc_0_000072C2
	tst.l (a0)
	beq.b loc_0_000072C2
	movea.l (a0),a0
	adda.l a0,a0
	adda.l a0,a0
	tst.w d3
	bne.b loc_0_00007334
	addq.l #4,a0
	move.l a0,app_07E8(a6)
	lea.l app_07E8(a6),a0
	moveq.l #0,d1
	bra.w loc_0_000072BC
loc_0_00007356:
	dc.b $07,$D4,$06,$06,$06,$50,$06,$9A,$06,$E4,$07,$2E,$07,$D8,$07,$DC
	dc.b $07,$E0,$07,$E4
loc_0_0000736A:
	move.l a2,d0
	andi.l #4278190080,d0
	bne.b loc_0_0000737C
	cmpa.l #$F80000,a2
	bcc.b loc_0_00007398
loc_0_0000737C:
	movem.l d1/a0-a1/a6,-(a7)
	movea.l $0004.w,a6
	move.l a2,d0
	move.w #$8000,d0
	movea.l d0,a1
	jsr _LVOTypeOfMem(a6)
	movem.l (a7)+,d1/a0-a1/a6
	tst.w d0
	beq.b loc_0_0000739C
loc_0_00007398:
	moveq.l #0,d0
	rts
loc_0_0000739C:
	moveq.l #-1,d0
	rts
	dc.b $02,$00,$00,$FE
loc_0_000073A4:
	cmp.l #$8,d0
	bcs.b loc_0_000073B0
	cmp.b d0,d0
	rts
loc_0_000073B0:
	andi #4,ccr
	rts
	dc.b $22,$08,$24,$3C,$00,$00,$03,$EE
loc_0_000073BE:
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	move.l d0,d3
	bne.b loc_0_000073DC
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
loc_0_000073DC:
	eori #4,ccr
	rts
loc_0_000073E2:
	move.l a5,d1
	move.l #$3ED,d2
	bra.b loc_0_000073BE
loc_0_000073EC:
	move.l d3,-(a7)
	move.l d3,d1
	moveq.l #0,d2
	moveq.l #1,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0042(a6)
	movea.l (a7)+,a6
	move.l (a7),d1
	moveq.l #0,d2
	moveq.l #0,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0042(a6)
	movea.l (a7)+,a6
	move.l d0,d4
	move.l (a7),d1
	moveq.l #0,d2
	moveq.l #-1,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0042(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d3
	rts
loc_0_0000742A:
	move.l d3,-(a7)
	move.l d3,d1
	move.l a0,d2
	move.l d4,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d3
	rts
loc_0_00007442:
	move.l d3,-(a7)
	move.l d3,d1
	move.l a0,d2
	move.l d4,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0030(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d3
	tst.l d0
	bge.b loc_0_00007470
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	move.w d0,-(a7)
	bsr.b loc_0_00007474
	move.w (a7)+,d0
	rts
loc_0_00007470:
	moveq.l #0,d0
	rts
loc_0_00007474:
	move.l d3,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
	rts
	dc.b $2D,$43,$01,$74
loc_0_00007488:
	lea.l app_0C08(a6),a0
	move.l a0,app_0178(a6)
	rts
	dc.b $61,$2C,$26,$2E,$01,$74,$60,$DA
loc_0_0000749A:
	bsr.w loc_0_000040AC
	beq.w loc_0_000075A0
	lea.l app_0E08(a6),a0
	movea.l app_0178(a6),a1
	cmpa.l a0,a1
	bne.b loc_0_000074B6
	move.w d1,-(a7)
	bsr.b loc_0_000074C0
	move.w (a7)+,d1
	bra.b loc_0_0000749A
loc_0_000074B6:
	move.b d1,(a1)+
	move.l a1,app_0178(a6)
	bra.w loc_0_000075A6
loc_0_000074C0:
	move.l app_0178(a6),d0
	lea.l app_0C08(a6),a0
	sub.l a0,d0
	beq.b loc_0_000074E6
	movem.l d3-d4,-(a7)
	move.l app_0174(a6),d3
	lea.l app_0C08(a6),a0
	move.l d0,d4
	bsr.w loc_0_00007442
	beq.b loc_0_000074E6
	bclr.b #7,app_00E4(a6)
loc_0_000074E6:
	movem.l (a7)+,d3-d4
	bra.b loc_0_00007488
loc_0_000074EC:
	move.l a0,-(a7)
	bsr.b loc_0_0000752C
	move.l (a7),d1
	move.l #$3EE,d2
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	tst.l d0
	bne.b loc_0_0000751A
	addq.l #4,a7
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	tst.l d0
	rts
loc_0_0000751A:
	move.l d0,app_0190(a6)
	lea.l app_0884(a6),a1
	movea.l (a7)+,a0
loc_0_00007524:
	move.b (a0)+,(a1)+
	bne.b loc_0_00007524
	moveq.l #0,d0
	rts
loc_0_0000752C:
	move.l app_0190(a6),d1
	beq.b loc_0_00007542
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
	clr.l app_0190(a6)
loc_0_00007542:
	rts
loc_0_00007544:
	tst.b app_00E4(a6)
	bpl.b loc_0_000075A6
	cmp.b #$A,d1
	bne.b loc_0_00007558
	tst.b d3
	beq.b loc_0_00007570
	moveq.l #32,d1
	bra.b loc_0_00007570
loc_0_00007558:
	cmp.b #$9,d1
	bne.b loc_0_00007562
	tst.b d3
	beq.b loc_0_00007570
loc_0_00007562:
	move.b d1,d0
	andi.b #127,d0
	cmp.b #$20,d0
	bcc.b loc_0_00007570
	moveq.l #32,d1
loc_0_00007570:
	tst.l app_0174(a6)
	bne.w loc_0_0000749A
	move.b d1,-(a7)
	move.l app_0190(a6),d1
	move.l a7,d2
	moveq.l #1,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0030(a6)
	movea.l (a7)+,a6
	move.b (a7)+,d1
	subq.l #1,d0
	bne.b loc_0_000075A0
	cmp.b #$A,d1
	bne.b loc_0_000075A6
	bsr.w loc_0_000040AC
	bne.b loc_0_000075A6
loc_0_000075A0:
	bclr.b #7,app_00E4(a6)
loc_0_000075A6:
	movem.l (a7)+,d0-d3/d7/a0-a2
	rts
	dc.b $4A,$AE,$01,$90,$4E,$75
loc_0_000075B2:
	tst.b app_0586(a6)
	beq.b loc_0_000075FA
	lea.l app_0C6C(a6),a0
	move.b d2,(a0)
	moveq.l #0,d0
	move.b (a0)+,d0
	move.b #$5F,(a0)+
	subq.w #1,d0
	bmi.w loc_0_00007C2A
loc_0_000075CC:
	move.b (a1)+,(a0)+
	dbf.w d0,loc_0_000075CC
	lea.l app_0C6E(a6),a1
	bsr.w loc_0_000075FA
	beq.w loc_0_00007C2A
	lea.l app_0C6C(a6),a1
	move.b (a1)+,d2
	addq.b #1,d2
	bsr.w loc_0_000075FA
	beq.w loc_0_00007C2A
	lea.l app_0C6C(a6),a1
	move.b (a1)+,d2
	addq.b #1,d2
	move.b #$40,(a1)
loc_0_000075FA:
	movem.l d1/d4/a2,-(a7)
	lea.l app_00AE(a6),a2
	tst.l (a2)
	beq.w loc_0_000076C2
	moveq.l #0,d0
	move.b d2,d0
	cmp.w app_0816(a6),d0
	ble.b loc_0_00007616
	move.w app_0816(a6),d0
loc_0_00007616:
	tst.b app_00E6(a6)
	bne.w loc_0_000076CA
	clr.l -(a7)
	movea.l a7,a0
	moveq.l #1,d1
	move.b (a1)+,(a0)+
	cmp.b d1,d0
	beq.b loc_0_00007644
	addq.b #1,d1
	move.b (a1)+,(a0)+
	cmp.b d1,d0
	beq.b loc_0_00007644
	addq.b #1,d1
	move.b (a1)+,(a0)+
	cmp.b d1,d0
	beq.b loc_0_00007644
	addq.b #1,d1
	move.b (a1)+,(a0)+
	cmp.b d1,d0
	beq.b loc_0_00007644
	addq.b #1,d1
loc_0_00007644:
	move.l (a7)+,d1
loc_0_00007646:
	move.l (a2),d3
	beq.b loc_0_0000765C
	asl.l #2,d3
	movea.l d3,a2
	lea.l $0004(a2),a0
	cmpi.l #1008,(a0)+
	bne.b loc_0_00007646
	moveq.l #1,d3
loc_0_0000765C:
	beq.b loc_0_000076C2
loc_0_0000765E:
	move.l (a0)+,d3
	beq.b loc_0_00007646
	asl.l #2,d3
	cmp.l (a0),d1
	bne.b loc_0_000076BC
	move.w d3,d4
	cmp.w app_0816(a6),d3
	ble.b loc_0_00007674
	move.w app_0816(a6),d4
loc_0_00007674:
	cmp.w d4,d0
	bgt.b loc_0_000076BC
	cmp.w #$4,d4
	bne.b loc_0_00007684
	cmp.w d4,d0
	ble.b loc_0_000076AC
	bra.b loc_0_000076BC
loc_0_00007684:
	movem.l d0-d1/a0-a1,-(a7)
	addq.l #4,a0
	subq.l #4,d0
	subq.l #4,d4
loc_0_0000768E:
	move.b (a0)+,d1
	beq.b loc_0_000076B8
	cmp.b (a1)+,d1
	bne.b loc_0_000076B8
	subq.w #1,d0
	beq.b loc_0_000076A0
	subq.w #1,d4
	bne.b loc_0_0000768E
	bra.b loc_0_000076B8
loc_0_000076A0:
	subq.l #1,d4
	beq.b loc_0_000076A8
	tst.b (a0)
	bne.b loc_0_000076B8
loc_0_000076A8:
	movem.l (a7)+,d0-d1/a0-a1
loc_0_000076AC:
	move.l $0(a0,d3.l),d2
	movem.l (a7)+,d1/d4/a2
	moveq.l #0,d0
	rts
loc_0_000076B8:
	movem.l (a7)+,d0-d1/a0-a1
loc_0_000076BC:
	lea.l $4(a0,d3.l),a0
	bra.b loc_0_0000765E
loc_0_000076C2:
	movem.l (a7)+,d1/d4/a2
	moveq.l #-1,d0
	rts
loc_0_000076CA:
	move.l (a2),d3
	beq.b loc_0_000076E0
	asl.l #2,d3
	movea.l d3,a2
	lea.l $0004(a2),a0
	cmpi.l #1008,(a0)+
	bne.b loc_0_000076CA
	moveq.l #1,d3
loc_0_000076E0:
	beq.b loc_0_000076C2
	move.b (a1),d1
	bsr.w loc_0_0000772E
loc_0_000076E8:
	move.l (a0)+,d3
	beq.b loc_0_000076CA
	asl.l #2,d3
	move.w d3,d4
	cmp.w app_0816(a6),d3
	ble.b loc_0_000076FA
	move.w app_0816(a6),d4
loc_0_000076FA:
	cmp.w d4,d0
	bgt.b loc_0_00007728
	movem.l d0-d1/a0-a1,-(a7)
loc_0_00007702:
	move.b (a0)+,d1
	beq.b loc_0_00007724
	bsr.b loc_0_0000772E
	move.b d1,-(a7)
	move.b (a1)+,d1
	bsr.b loc_0_0000772E
	cmp.b (a7)+,d1
	bne.b loc_0_00007724
	subq.w #1,d0
	beq.b loc_0_0000771C
	subq.w #1,d4
	bne.b loc_0_00007702
	bra.b loc_0_00007724
loc_0_0000771C:
	subq.l #1,d4
	beq.b loc_0_000076A8
	tst.b (a0)
	beq.b loc_0_000076A8
loc_0_00007724:
	movem.l (a7)+,d0-d1/a0-a1
loc_0_00007728:
	lea.l $4(a0,d3.l),a0
	bra.b loc_0_000076E8
loc_0_0000772E:
	cmp.b #$61,d1
	bcs.b loc_0_0000773E
	cmp.b #$7B,d1
	bcc.b loc_0_0000773E
	andi.b #223,d1
loc_0_0000773E:
	rts
loc_0_00007740:
	bsr.w loc_0_00007DE0
	move.l app_00AE(a6),d1
	cmp.l loc_0_00000018(pc),d1
	beq.b loc_0_0000775A
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$009C(a6)
	movea.l (a7)+,a6
loc_0_0000775A:
	clr.l app_00AE(a6)
	move.l app_0588(a6),d0
	beq.b loc_0_0000777E
	movea.l d0,a1
	move.l app_058C(a6),d0
	lsl.l #2,d0
	addq.l #4,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	clr.l app_0588(a6)
loc_0_0000777E:
	rts
loc_0_00007780:
	tst.l app_015E(a6)
	bne.w loc_0_00007ACE
	move.l a0,-(a7)
	bsr.b loc_0_00007740
	suba.l a4,a4
	lea.l loc_0_000088F6(pc),a5
	move.l (a7)+,d1
	move.l #$3ED,d2
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	move.l d0,d4
	beq.w loc_0_0000784E
	moveq.l #26,d1
	bsr.w loc_0_00006A5A
	bsr.w loc_0_00007B98
	cmp.l #$3F3,d0
	bne.w loc_0_00007840
loc_0_000077C0:
	bsr.w loc_0_00007B98
	beq.b loc_0_000077CC
	bsr.w loc_0_00007BD0
	bra.b loc_0_000077C0
loc_0_000077CC:
	bsr.w loc_0_00007B98
	bsr.w loc_0_00007B98
	move.l d0,d5
	bsr.w loc_0_00007B98
	sub.l d5,d0
	addq.l #1,d0
	bsr.w loc_0_00007BD0
loc_0_000077E2:
	bsr.w loc_0_00007B98
loc_0_000077E6:
	cmp.l #$3F0,d0
	beq.w loc_0_0000788A
	cmp.l #$3F1,d0
	beq.w loc_0_00007916
	cmp.l #$3EC,d0
	beq.b loc_0_00007860
	cmp.l #$3F2,d0
	bne.b loc_0_00007822
	bsr.w loc_0_00007B98
	tst.l d1
	bne.b loc_0_000077E6
	move.l d4,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
	rts
loc_0_00007822:
	movea.l (a5),a5
	adda.l a5,a5
	adda.l a5,a5
	cmp.l #$3E9,d0
	beq.b loc_0_00007870
	cmp.l #$3EA,d0
	beq.b loc_0_00007870
	cmp.l #$3EB,d0
	beq.b loc_0_00007882
loc_0_00007840:
	move.l d4,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
loc_0_0000784E:
	rts
loc_0_00007850:
	move.l d4,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
	rts
loc_0_00007860:
	bsr.w loc_0_00007B98
	beq.w loc_0_000077E2
	addq.l #1,d0
	bsr.w loc_0_00007BD0
	bra.b loc_0_00007860
loc_0_00007870:
	bsr.w loc_0_00007B98
	andi.l #1073741823,d0
	bsr.w loc_0_00007BD0
	bra.w loc_0_000077E2
loc_0_00007882:
	bsr.w loc_0_00007B98
	bra.w loc_0_000077E2
loc_0_0000788A:
	bsr.w loc_0_00007B3E
	bsr.w loc_0_00007B70
	move.l d0,d5
	subq.l #4,d5
	moveq.l #2,d6
loc_0_00007898:
	bsr.w loc_0_00007B7C
	beq.b loc_0_000078AA
	add.l d0,d6
	addq.l #2,d6
	addq.l #1,d0
	bsr.w loc_0_00007B88
	bra.b loc_0_00007898
loc_0_000078AA:
	asl.l #2,d6
	move.l d5,d0
	bsr.w loc_0_00007BCA
	bsr.w loc_0_000078CE
	beq.b loc_0_00007850
	lea.l $0008(a4),a0
	move.l a5,d1
	addq.l #4,d1
loc_0_000078C0:
	move.l (a0)+,d0
	beq.w loc_0_000077E2
	asl.l #2,d0
	adda.l d0,a0
	add.l d1,(a0)+
	bra.b loc_0_000078C0
loc_0_000078CE:
	moveq.l #8,d0
	add.l d6,d0
	moveq.l #MEMF_ANY,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_00007914
	movea.l a4,a0
	movea.l d0,a4
	move.l a0,d1
	bne.b loc_0_000078F0
	lea.l app_00AE(a6),a0
loc_0_000078F0:
	addq.l #4,d0
	asr.l #2,d0
	move.l d0,(a0)
	moveq.l #8,d1
	add.l d6,d1
	move.l d1,(a4)+
	clr.l (a4)
	move.l d4,d1
	move.l a4,d2
	addq.l #4,d2
	move.l d6,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	move.l a4,d0
loc_0_00007914:
	rts
loc_0_00007916:
	bsr.w loc_0_00007B98
	lea.l -$0010(a7),a7
	asl.l #2,d0
	move.l d0,(a7)
	bsr.w loc_0_00007BB6
	move.l d0,$0004(a7)
	add.l d0,(a7)
	bsr.w loc_0_00007B98
	move.l d0,$0008(a7)
	bsr.w loc_0_00007B98
	bsr.w loc_0_00007AB6
	bne.w loc_0_000079FE
	move.l $0008(a7),d1
	lea.l $4(a5,d1.l),a0
	move.l a0,d1
	bsr.w loc_0_00007A80
	beq.w loc_0_000079FE
	movea.l a0,a3
	move.l a3,$000C(a7)
	move.l $0004(a7),d0
	addq.l #4,d0
	move.l d0,$0028(a3)
	cmpi.l #1397900064,$0024(a3)
	beq.b loc_0_00007998
	bsr.w loc_0_00007B98
	bsr.w loc_0_00007A0C
	bsr.w loc_0_00007BB6
	move.l d0,$002C(a3)
	sub.l (a7),d0
	neg.l d0
	move.l d0,$0038(a3)
	cmpi.l #1279872581,$0024(a3)
	beq.b loc_0_000079F8
	bsr.w loc_0_00007B98
	addq.l #4,$002C(a3)
	bra.b loc_0_000079FA
loc_0_00007998:
	moveq.l #9,d0
	bsr.w loc_0_00007BD0
	bsr.w loc_0_00007B3E
	bsr.w loc_0_00007B7C
	move.l d0,$0038(a3)
	bsr.w loc_0_00007B7C
	bsr.w loc_0_00007B7C
	move.l d0,$0004(a7)
	bsr.w loc_0_00007B70
	add.l $0004(a7),d0
	move.l d0,$002C(a3)
	move.l $0004(a7),d3
	addq.w #4,a3
	bra.b loc_0_000079DA
loc_0_000079CA:
	move.b (a0)+,d0
	beq.b loc_0_000079E4
	cmp.b #$3A,d0
	beq.b loc_0_000079DA
	cmp.b #$2F,d0
	bne.b loc_0_000079DE
loc_0_000079DA:
	move.l a0,$0004(a7)
loc_0_000079DE:
	dbf.w d3,loc_0_000079CA
	clr.b (a0)
loc_0_000079E4:
	movea.l $0004(a7),a0
	moveq.l #30,d0
loc_0_000079EA:
	move.b (a0)+,(a3)+
	dbeq.w d0,loc_0_000079EA
	movea.l $000C(a7),a3
	move.l $0038(a3),d0
loc_0_000079F8:
	asr.l #3,d0
loc_0_000079FA:
	move.l d0,$0034(a3)
loc_0_000079FE:
	move.l (a7),d0
	lea.l $0010(a7),a7
	bsr.w loc_0_00007BCA
	bra.w loc_0_000077E2
loc_0_00007A0C:
	pea.l $0022(a3)
	move.l a3,-(a7)
	addq.w #4,a3
	bra.b loc_0_00007A44
loc_0_00007A16:
	move.l d0,-(a7)
	bsr.w loc_0_00007B98
	moveq.l #3,d1
loc_0_00007A1E:
	rol.l #8,d0
	cmp.b #$3A,d0
	beq.b loc_0_00007A38
	cmp.b #$2F,d0
	beq.b loc_0_00007A38
	move.b d0,(a3)+
	cmpa.l $0008(a7),a3
	bls.b loc_0_00007A3E
	subq.l #1,a3
	bra.b loc_0_00007A3E
loc_0_00007A38:
	movea.l $0004(a7),a3
	addq.w #4,a3
loc_0_00007A3E:
	dbf.w d1,loc_0_00007A1E
	move.l (a7)+,d0
loc_0_00007A44:
	dbf.w d0,loc_0_00007A16
	clr.b (a3)
	movea.l (a7)+,a3
	addq.l #4,a7
	rts
loc_0_00007A50:
	movem.l d1/a1,-(a7)
	asl.l #2,d0
	bra.b loc_0_00007A66
loc_0_00007A58:
	cmpi.b #58,(a0)+
	beq.b loc_0_00007A66
	cmpi.b #47,-$0001(a0)
	bne.b loc_0_00007A6A
loc_0_00007A66:
	movea.l a0,a1
	move.l d0,d1
loc_0_00007A6A:
	dbf.w d0,loc_0_00007A58
	movem.l (a7)+,d0/a0
loc_0_00007A72:
	move.b (a1)+,(a0)+
	beq.b loc_0_00007A7E
	subq.l #1,d0
	dbls.w d1,loc_0_00007A72
	clr.b (a1)
loc_0_00007A7E:
	rts
loc_0_00007A80:
	movem.l d0-d1,-(a7)
	moveq.l #60,d0
	bsr.w loc_0_00008160
	movem.l (a7)+,d0-d1
	beq.w loc_0_00007AB4
	clr.l $0028(a0)
	move.l d0,$0024(a0)
	move.l d1,$0030(a0)
	lea.l app_0578(a6),a1
loc_0_00007AA2:
	move.l (a1),d0
	beq.b loc_0_00007AB0
	exg d0,a1
	cmp.l $0030(a1),d1
	bcc.b loc_0_00007AA2
	exg d0,a1
loc_0_00007AB0:
	move.l d0,(a0)
	move.l a0,(a1)
loc_0_00007AB4:
	rts
loc_0_00007AB6:
	cmp.l #$48434C4E,d0
	beq.b loc_0_00007ACC
	cmp.l #$4C494E45,d0
	beq.b loc_0_00007ACC
	cmp.l #$53524320,d0
loc_0_00007ACC:
	rts
loc_0_00007ACE:
	lea.l loc_0_00000018(pc),a4
	move.l (a4),app_00AE(a6)
loc_0_00007AD6:
	move.l (a4),d0
	beq.b loc_0_00007B3C
	asl.l #2,d0
	movea.l d0,a4
	lea.l $0004(a4),a2
	cmpi.l #1009,(a2)+
	bne.b loc_0_00007AD6
	addq.l #8,a2
	move.l (a2),d0
	bsr.b loc_0_00007AB6
	bne.b loc_0_00007AD6
	move.l -$0004(a2),d1
	bsr.b loc_0_00007A80
	beq.b loc_0_00007B3C
	movea.l a0,a3
	move.l $0004(a2),d1
	asl.l #2,d1
	lea.l $8(a2,d1.l),a0
	cmpi.l #1279872581,$0024(a3)
	beq.b loc_0_00007B14
	move.l (a0)+,d0
	bra.b loc_0_00007B20
loc_0_00007B14:
	move.l -$0008(a2),d0
	sub.l $0004(a2),d0
	subq.l #3,d0
	asr.l #1,d0
loc_0_00007B20:
	move.l d0,$0034(a3)
	move.l a0,$002C(a3)
	move.l $0004(a2),d0
	moveq.l #30,d1
	lea.l $0008(a2),a0
	lea.l $0004(a3),a1
	bsr.w loc_0_00007A50
	bra.b loc_0_00007AD6
loc_0_00007B3C:
	rts
loc_0_00007B3E:
	bsr.w loc_0_00007BB6
	move.l d0,-(a7)
	move.l d4,d1
	lea.l app_0C08(a6),a0
	move.l a0,d2
	move.l #$200,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	tst.l d0
	bge.b loc_0_00007B64
	moveq.l #0,d0
loc_0_00007B64:
	lea.l app_0C08(a6),a0
	movea.l (a7)+,a1
	move.l d0,d2
	add.l a0,d2
	rts
loc_0_00007B70:
	move.l a0,d0
	pea.l app_0C08(a6)
	sub.l (a7)+,d0
	add.l a1,d0
	rts
loc_0_00007B7C:
	cmp.l a0,d2
	beq.b loc_0_00007B84
	move.l (a0)+,d0
	rts
loc_0_00007B84:
	bsr.b loc_0_00007B3E
	bra.b loc_0_00007B7C
loc_0_00007B88:
	tst.l d0
	beq.b loc_0_00007B96
loc_0_00007B8C:
	move.l d0,-(a7)
	bsr.b loc_0_00007B7C
	moveq.l #-1,d0
	add.l (a7)+,d0
	bne.b loc_0_00007B8C
loc_0_00007B96:
	rts
loc_0_00007B98:
	move.l d4,d1
	lea.l app_09A8(a6),a0
	move.l a0,d2
	moveq.l #4,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	move.l d0,d1
	move.l app_09A8(a6),d0
	rts
loc_0_00007BB6:
	moveq.l #0,d2
	moveq.l #0,d3
loc_0_00007BBA:
	move.l d4,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0042(a6)
	movea.l (a7)+,a6
	rts
loc_0_00007BCA:
	moveq.l #-1,d3
	move.l d0,d2
	bra.b loc_0_00007BBA
loc_0_00007BD0:
	moveq.l #0,d3
	move.l d0,d2
	asl.l #2,d2
	bra.b loc_0_00007BBA
	dc.b $20,$40,$20,$18,$E5,$80,$53,$80,$12,$18,$67,$0A,$61,$00,$DC,$D4
	dc.b $53,$02,$57,$C8,$FF,$F4,$4E,$75,$48,$E7,$40,$80,$20,$40,$20,$18
	dc.b $E5,$80,$53,$80,$B0,$7C,$00,$0F,$65,$02,$70,$0F,$12,$18,$67,$06
	dc.b $18,$C1,$51,$C8,$FF,$F8,$4C,$DF,$01,$02,$4E,$75,$20,$4C,$26,$04
	dc.b $53,$83,$12,$18,$67,$08,$61,$00,$DC,$9A,$51,$CB,$FF,$F6,$4E,$75
	dc.b $B0,$00
loc_0_00007C2A:
	rts
loc_0_00007C2C:
	bsr.w loc_0_00001288
	movem.l d2-d5/a0/a2-a4,-(a7)
	moveq.l #0,d5
	moveq.l #0,d2
	lea.l app_0578(a6),a2
loc_0_00007C3C:
	bsr.w loc_0_00007D6C
	beq.w loc_0_00007C4C
	add.l $0034(a2),d5
	addq.l #1,d2
	bra.b loc_0_00007C3C
loc_0_00007C4C:
	move.l d5,d0
	beq.w loc_0_00007D68
	asl.l #3,d0
	bsr.w loc_0_00008160
	beq.w loc_0_00007D68
	movea.l a0,a3
	movea.l a0,a4
	tst.l app_015E(a6)
	bne.b loc_0_00007C84
	move.l #loc_0_0000136D,d1
	move.l #$3ED,d2
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	move.l d0,d4
	beq.w loc_0_00007D62
loc_0_00007C84:
	lea.l app_0578(a6),a2
loc_0_00007C88:
	movea.l $0010(a7),a0
	bsr.w loc_0_00007D6C
	beq.w loc_0_00007D36
	tst.l app_015E(a6)
	beq.b loc_0_00007CBC
	movea.l $002C(a2),a0
	move.l $0034(a2),d0
	cmpi.l #1212369998,$0024(a2)
	bne.b loc_0_00007CB6
	bsr.w loc_0_00007D9E
	bra.b loc_0_00007C88
loc_0_00007CB2:
	move.l (a0)+,(a4)+
	move.l (a0)+,(a4)+
loc_0_00007CB6:
	subq.l #1,d0
	bcc.b loc_0_00007CB2
	bra.b loc_0_00007C88
loc_0_00007CBC:
	move.l $0028(a2),d0
	bsr.w loc_0_00007BCA
	bsr.w loc_0_00007B98
	cmp.l $0024(a2),d0
	bne.w loc_0_00007D54
	move.l $002C(a2),d0
	bsr.w loc_0_00007BCA
	move.l $0038(a2),d3
	cmpi.l #1212369998,$0024(a2)
	bne.b loc_0_00007D10
	move.l d3,d0
	bsr.w loc_0_00008160
	beq.w loc_0_00007D54
	move.l d4,d1
	move.l a0,d2
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	movea.l d2,a0
	bsr.w loc_0_00007D9E
	movea.l d2,a0
	bsr.w loc_0_0000818A
	bra.w loc_0_00007C88
loc_0_00007D10:
	move.l d4,d1
	move.l a4,d2
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	move.l $0034(a2),d0
	move.l $0030(a2),d1
	bra.b loc_0_00007D2E
loc_0_00007D2A:
	addq.l #4,a4
	add.l d1,(a4)+
loc_0_00007D2E:
	subq.l #1,d0
	bcc.b loc_0_00007D2A
	bra.w loc_0_00007C88
loc_0_00007D36:
	tst.l app_015E(a6)
	bne.b loc_0_00007D4A
	move.l d4,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
loc_0_00007D4A:
	movea.l a3,a0
	move.l d5,d0
loc_0_00007D4E:
	movem.l (a7)+,d2-d5/a1-a4
	rts
loc_0_00007D54:
	move.l d4,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
loc_0_00007D62:
	movea.l a3,a0
	bsr.w loc_0_0000818A
loc_0_00007D68:
	moveq.l #0,d0
	bra.b loc_0_00007D4E
loc_0_00007D6C:
	move.l (a2),d0
	beq.w loc_0_00007D96
	movea.l d0,a2
	movem.l a0/a2,-(a7)
	addq.w #4,a2
loc_0_00007D7A:
	move.b (a0)+,d1
	bsr.w loc_0_0000772E
	move.b d1,d0
	move.b (a2)+,d1
	bsr.w loc_0_0000772E
	cmp.b d0,d1
	bne.b loc_0_00007D98
	tst.b d0
	bne.b loc_0_00007D7A
	movem.l (a7)+,a0/a2
	moveq.l #1,d0
loc_0_00007D96:
	rts
loc_0_00007D98:
	movem.l (a7)+,a0/a2
	bra.b loc_0_00007D6C
loc_0_00007D9E:
	move.l a3,-(a7)
	suba.l a1,a1
	movea.l $0030(a2),a3
	move.l $0034(a2),d1
	add.l d1,d1
	bra.b loc_0_00007DBA
loc_0_00007DAE:
	move.b (a0)+,d0
	beq.b loc_0_00007DC2
	ext.w d0
loc_0_00007DB4:
	adda.w d0,a1
loc_0_00007DB6:
	move.l a1,(a4)+
	exg a3,a1
loc_0_00007DBA:
	subq.l #1,d1
	bcc.b loc_0_00007DAE
	movea.l (a7)+,a3
	rts
loc_0_00007DC2:
	move.b (a0)+,d0
	lsl.w #8,d0
	move.b (a0)+,d0
	bne.b loc_0_00007DB4
	tst.w d0
	bne.b loc_0_00007DB4
	move.b (a0)+,d0
	lsl.w #8,d0
	move.b (a0)+,d0
	swap.w d0
	move.b (a0)+,d0
	lsl.w #8,d0
	move.b (a0)+,d0
	adda.l d0,a1
	bra.b loc_0_00007DB6
loc_0_00007DE0:
	clr.l app_0578(a6)
	move.l app_0578(a6),d0
	beq.b loc_0_00007DF6
loc_0_00007DEA:
	movea.l d0,a0
	move.l (a0),-(a7)
	bsr.w loc_0_0000818A
	move.l (a7)+,d0
	bne.b loc_0_00007DEA
loc_0_00007DF6:
	rts
loc_0_00007DF8:
	move.l (a1),d1
	beq.b loc_0_00007E0E
	asl.l #2,d1
	movea.l d1,a1
	lea.l $0004(a1),a0
	cmpi.l #1008,(a0)+
	bne.b loc_0_00007DF8
	moveq.l #1,d1
loc_0_00007E0E:
	rts
loc_0_00007E10:
	lea.l app_00AE(a6),a1
	moveq.l #0,d0
loc_0_00007E16:
	bsr.b loc_0_00007DF8
	beq.b loc_0_00007E2A
loc_0_00007E1A:
	addq.l #3,d0
	move.l (a0),d1
	asl.l #2,d1
	lea.l $8(a0,d1.l),a0
	bne.b loc_0_00007E1A
	subq.l #3,d0
	bra.b loc_0_00007E16
loc_0_00007E2A:
	tst.l d0
	beq.b loc_0_00007E86
	lsr.l #1,d0
	bset #0,d0
	addq.l #2,d0
	move.l d0,app_058C(a6)
	asl.l #2,d0
	addq.l #4,d0
	move.l #MEMF_CLEAR,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	move.l d0,app_0588(a6)
	beq.b loc_0_00007E86
	movem.l d6-d7,-(a7)
	lea.l app_00AE(a6),a1
loc_0_00007E5E:
	bsr.b loc_0_00007DF8
	beq.b loc_0_00007E82
	move.l a1,-(a7)
loc_0_00007E64:
	move.l (a0),d1
	bne.b loc_0_00007E6C
	movea.l (a7)+,a1
	bra.b loc_0_00007E5E
loc_0_00007E6C:
	asl.l #2,d1
	move.l $4(a0,d1.l),d0
	move.l a0,-(a7)
	bsr.b loc_0_00007E88
	movea.l (a7)+,a0
	beq.b loc_0_00007E7C
	move.l a0,(a1)
loc_0_00007E7C:
	lea.l $8(a0,d1.l),a0
	bra.b loc_0_00007E64
loc_0_00007E82:
	movem.l (a7)+,d6-d7
loc_0_00007E86:
	rts
loc_0_00007E88:
	movea.l app_0588(a6),a1
	move.l app_058C(a6),d2
	move.l d0,d6
	divu.w d2,d6
	bvc.b loc_0_00007EA8
	movem.l d0/d2,-(a7)
	exg d2,d0
	bsr.w loc_0_00006F0E
	move.l d0,d6
	swap.w d6
	movem.l (a7)+,d0/d2
loc_0_00007EA8:
	swap.w d6
	ext.l d6
	bpl.b loc_0_00007EB0
	neg.l d6
loc_0_00007EB0:
	add.l d6,d6
	add.l d6,d6
	add.l d2,d2
	add.l d2,d2
loc_0_00007EB8:
	move.l $0(a1,d6.l),d7
	beq.b loc_0_00007ED8
	movea.l d7,a0
	move.l (a0),d7
	asl.l #2,d7
	cmp.l $4(a0,d7.l),d0
	beq.b loc_0_00007ED4
	addq.l #4,d6
	cmp.l d6,d2
	bne.b loc_0_00007EB8
	moveq.l #0,d6
	bra.b loc_0_00007EB8
loc_0_00007ED4:
	movea.l a0,a1
	rts
loc_0_00007ED8:
	lea.l $0(a1,d6.l),a1
	moveq.l #-1,d7
	rts
	dc.b $48,$E7,$63,$C0,$4A,$80,$6B,$04,$61,$9E,$67,$04,$70,$00,$60,$02
	dc.b $20,$09,$4C,$DF,$03,$C6,$4E,$75,$4A,$AE,$05,$88,$66,$E2,$4A,$2E
	dc.b $01,$63,$66,$02,$4E,$75,$B0,$AE,$01,$6C,$65,$20,$B0,$AE,$01,$70
	dc.b $62,$1A,$48,$E7,$40,$80,$4A,$2E,$01,$63,$6B,$28,$20,$6E,$01,$64
	dc.b $22,$18,$67,$0C,$B2,$80,$66,$F8,$4C,$DF,$01,$02,$70,$00,$4E,$75
	dc.b $4A,$AE,$01,$68,$67,$06,$B1,$EE,$01,$68,$6C,$EC,$21,$40,$FF,$FC
	dc.b $42,$90,$60,$E4,$20,$6E,$01,$64,$22,$18,$67,$DC,$B0,$81,$66,$F8
	dc.b $41,$EE,$01,$80,$10,$FC,$00,$6C,$22,$00,$C9,$48,$61,$00,$9C,$60
	dc.b $C9,$48,$42,$10,$22,$08,$41,$EE,$01,$7C,$92,$88,$53,$81,$E4,$81
	dc.b $20,$81,$20,$08,$4C,$DF,$01,$02,$4E,$75,$51,$EE,$05,$92,$2F,$00
	dc.b $61,$00,$FF,$76,$66,$28,$20,$17,$2E,$88,$08,$00,$00,$00,$66,$22
	dc.b $61,$00,$F3,$D8,$66,$1C,$20,$40,$0C,$50,$4E,$F9,$66,$14,$20,$28
	dc.b $00,$02,$20,$57,$61,$00,$FF,$52,$67,$04,$50,$EE,$05,$92,$58,$4F
	dc.b $4E,$75,$20,$5F,$70,$00,$4E,$75
loc_0_00007FB8:
	tst.b app_0162(a6)
	beq.b loc_0_00007FE0
	move.l loc_0_00000020.l,d0
	beq.w loc_0_000080AA
	moveq.l #0,d4
	movea.l d0,a0
	lea.l $0008(a0),a4
	move.l a4,app_0136(a6)
	tst.b (a0)
	beq.w loc_0_000080AA
	clr.b (a0)
	bra.w loc_0_0000807C
loc_0_00007FE0:
	moveq.l #27,d1
	bsr.w loc_0_00006A5A
	move.l #loc_0_000081CB,d1
	move.l #$3ED,d2
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	move.l d0,d4
	bne.b loc_0_0000801A
	move.l #loc_0_000081C6,d1
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	move.l d0,d4
	beq.w loc_0_000080AA
loc_0_0000801A:
	moveq.l #28,d1
	bsr.w loc_0_00006A5A
	lea.l app_09A8(a6),a0
	move.l d4,d1
	move.l a0,d2
	moveq.l #8,d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
	subq.l #8,d0
	bne.w loc_0_0000809A
	cmpi.l #1107297264,app_09A8(a6)
	bne.b loc_0_0000809A
	move.l app_09AC(a6),d0
	beq.b loc_0_0000809A
	move.l d0,app_013A(a6)
	moveq.l #MEMF_ANY,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_0000809A
	move.l d0,app_0136(a6)
	movea.l d0,a4
	move.l d4,d1
	move.l a4,d2
	move.l app_013A(a6),d3
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$002A(a6)
	movea.l (a7)+,a6
loc_0_0000807C:
	move.l (a4)+,d1
	beq.b loc_0_0000809A
	asl.l #2,d1
	adda.l d1,a4
	move.w (a4),d1
	ext.l d1
	move.l (a4),d2
	ext.l d2
	asl.l #2,d1
	lea.l app_00B6(a6),a0
	add.l $0(a0,d1.l),d2
	move.l d2,(a4)+
	bra.b loc_0_0000807C
loc_0_0000809A:
	move.l d4,d1
	beq.b loc_0_000080AA
	move.l a6,-(a7)
	movea.l $00C2(a6),a6
	jsr -$0024(a6)
	movea.l (a7)+,a6
loc_0_000080AA:
	rts
	dc.b $20,$2E,$01,$36,$67,$1E,$48,$E7,$40,$80,$C1,$88,$22,$10,$67,$10
	dc.b $E5,$81,$B0,$B0,$18,$04,$67,$06,$41,$F0,$18,$08,$60,$EE,$20,$08
	dc.b $4C,$DF,$01,$02,$4E,$75,$4A,$AE,$00,$AE,$67,$00,$00,$6C,$45,$FA
	dc.b $05,$E2,$61,$00,$DD,$CC,$4B,$EE,$00,$AE,$7C,$00,$20,$15,$67,$12
	dc.b $E5,$80,$2A,$40,$49,$ED,$00,$04,$0C,$9C,$00,$00,$03,$F0,$66,$EC
	dc.b $70,$01,$67,$3C,$28,$1C,$67,$E4,$E5,$84,$24,$34,$48,$00,$61,$00
	dc.b $E9,$8E,$61,$00,$E9,$72,$61,$00,$FB,$00,$49,$F4,$48,$04,$61,$00
	dc.b $E9,$78,$52,$46,$BC,$6B,$00,$06,$66,$DA,$61,$00,$BF,$F8,$B2,$3C
	dc.b $00,$1B,$67,$10,$7C,$00,$61,$00,$D5,$62,$42,$AB,$00,$0A,$60,$C4
	dc.b $61,$00,$BF,$E2,$61,$00,$DC,$5A,$4E,$75
loc_0_00008146:
	movem.w (a0)+,d0-d3
	exg d0,d1
	movea.l a0,a1
	movea.l app_05B4(a6),a0
	move.l a6,-(a7)
	movea.l app_IntuitionBase(a6),a6
	jsr _LVOSetPointer(a6)
	movea.l (a7)+,a6
	rts
loc_0_00008160:
	addq.l #8,d0
	move.l d0,-(a7)
	moveq.l #MEMF_PUBLIC,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d1
	tst.l d0
	beq.b loc_0_00008188
	movea.l d0,a0
	move.l app_00CA(a6),(a0)
	move.l a0,app_00CA(a6)
	addq.l #4,a0
	move.l d1,(a0)+
	rts
loc_0_00008188:
	rts
loc_0_0000818A:
	move.l a0,d0
	beq.b loc_0_000081B4
	subq.l #8,a0
	lea.l app_00CA(a6),a1
loc_0_00008194:
	cmpa.l (a1),a0
	beq.b loc_0_000081A0
	tst.l (a1)
	beq.b loc_0_000081B4
	movea.l (a1),a1
	bra.b loc_0_00008194
loc_0_000081A0:
	move.l (a0),(a1)
	movea.l a0,a1
	move.l $0004(a0),d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
loc_0_000081B4:
	rts
loc_0_000081B6:
	move.l app_00CA(a6),d0
	beq.b loc_0_000081C4
	addq.l #8,d0
	movea.l d0,a0
	bsr.b loc_0_0000818A
	bra.b loc_0_000081B6
loc_0_000081C4:
	rts
loc_0_000081C6:
	dc.b $4C,$49,$42,$53,$3A
loc_0_000081CB:
	dc.b "monam.libfile",$00	; string
loc_0_000081D9:
	dc.b "intuition.library",$00	; string
loc_0_000081EB:
	dc.b "dos.library",$00	; string
loc_0_000081F7:
	dc.b "graphics.library",$00	; string
loc_0_00008208:
	dc.b "console.device",$00	; string
loc_0_00008217:
	dc.b "pc = ",$00	; string
	dc.b "sr = ",$00	; string
	dc.b "a7'= ",$00	; string
	dc.b "Divide by zero",$00	; string
	dc.b "CHK exception",$00	; string
	dc.b "TRAPV exception",$00	; string
	dc.b "Privilege violation",$00	; string
	dc.b "Trace",$00	; string
	dc.b "Bad interrupt",$00	; string
	dc.b "Invalid TRAP",$00	; string
	dc.b "Illegal exception",$00	; string
	dc.b "Breakpoint",$00	; string
	dc.b $64,$20,$3D,$00,$61,$20,$3D,$00
	dc.b "Searching...",$00	; string
	dc.b "Address error",$00	; string
	dc.b "Bus error",$00	; string
	dc.b $20,$20,$3B,$00,$2C,$20,$00
	dc.b "Text: ",$00	; string
	dc.b "Data: ",$00	; string
	dc.b "BSS : ",$00	; string
	dc.b $43,$75,$72,$72,$65,$6E,$74,$20,$42,$72,$65,$61,$6B,$70,$6F,$69
	dc.b $6E,$74,$73,$3A,$0A,$00
	dc.b "Data start,end<,size>",$00	; string
	dc.b "Cross-reference list",$00	; string
	dc.b $46,$69,$6C,$65,$6E,$61,$6D,$65,$00
	dc.b "Checking for symbols..",$00	; string
	dc.b $43,$68,$65,$63,$6B,$69,$6E,$67,$20,$66,$6F,$72,$20,$6C,$69,$62
	dc.b $66,$69,$6C,$65,$2E,$2E,$0A,$00,$4C,$6F,$61,$64,$69,$6E,$67,$20
	dc.b $6C,$69,$62,$66,$69,$6C,$65,$2E,$2E,$0A,$00
	dc.b "Task terminated",$00	; string
	dc.b "Unknown exception",$00	; string
	dc.b "Line A exception",$00	; string
	dc.b "Line F exception",$00	; string
	dc.b "Task must be running!",$00	; string
	dc.b "Task loaded!",$00	; string
	dc.b "No task loaded!",$00	; string
	dc.b "Task must be suspended!",$00	; string
	dc.b "Executing",$00	; string
	dc.b "None",$00	; string
	dc.b "Suspended",$00	; string
	dc.b "Free memory Chip,Fast,All: ",$00	; string
	dc.b "Task: ",$00	; string
	dc.b "Hunk list:",$00	; string
	dc.b "Memory list:",$00	; string
	dc.b "Unordered condition",$00	; string
	dc.b "Inexact result",$00	; string
	dc.b "FP divide by zero",$00	; string
	dc.b "Underflow",$00	; string
	dc.b "Operand error",$00	; string
	dc.b "Overflow",$00	; string
	dc.b "Signaling NAN",$00	; string
	dc.b "Co-processor violation",$00	; string
	dc.b "Format error",$00	; string
	dc.b "Bad MMU configuration",$00	; string
loc_0_000084FE:
	dc.b "Disassembly",$00	; string
loc_0_0000850A:
	dc.b "Memory",$00	; string
loc_0_00008511:
	dc.b "Registers",$00	; string
loc_0_0000851B:
	dc.b "Source (",$00	; string
loc_0_00008524:
	dc.b $20,$20,$45,$53,$43,$20,$74,$6F,$20,$61,$62,$6F,$72,$74,$20,$20
	dc.b $20,$00
	dc.b "Window start address?",$00	; string
	dc.b "Go to source line?",$00	; string
loc_0_0000855F:
	dc.b $5B,$52,$65,$74,$75,$72,$6E,$5D,$00
loc_0_00008568:
	dc.b $20,$00
	dc.b "Filename to load",$00	; string
	dc.b "Source file to load",$00	; string
loc_0_0000858F:
	dc.b "Executable file to load",$00	; string
loc_0_000085A7:
	dc.b "Command line",$00	; string
	dc.b "Register=value",$00	; string
	dc.b "Cannot run",$00	; string
loc_0_000085CE:
	dc.b "In ROM!",$00	; string
loc_0_000085D6:
	dc.b "It's odd!",$00	; string
loc_0_000085E0:
	dc.b "Cannot write!",$00	; string
loc_0_000085EE:
	dc.b "Too many breakpoints!",$00	; string
	dc.b "Run until address[,param n=*?-]",$00	; string
	dc.b "Kill all breakpoints",$00	; string
	dc.b $20,$59,$2F,$4E,$3F,$00
	dc.b "Breakpoint address[,param n=*?-]",$00	; string
	dc.b "History",$00	; string
	dc.b "Search for B/W/L/T/I? ",$00	; string
	dc.b "No printer device selected",$00	; string
	dc.b "Expression to lock",$00	; string
	dc.b "Enter expression",$00	; string
	dc.b "Symbols",$00	; string
	dc.b "PREFERENCES",$00	; string
	dc.b "Show relative offset symbols Y/N? ",$00	; string
	dc.b "Case insensitive symbols Y/N? ",$00	; string
	dc.b "Ignore case Y/N? ",$00	; string
	dc.b "Symbol significance",$00	; string
	dc.b "Copy start,end,to",$00	; string
	dc.b "Fill start,end,with",$00	; string
	dc.b "Set current drive/directory",$00	; string
	dc.b "Save binary, filename",$00	; string
	dc.b "start address,end",$00	; string
	dc.b "Run: Go,Instruction ",$00	; string
	dc.b "Help",$00	; string
	dc.b "Disassemble start,end",$00	; string
	dc.b "Save preferences Y/N? ",$00	; string
loc_0_000087EB:
	dc.b $41,$6D,$69,$67,$61,$44,$4F,$53,$20,$65,$72,$72,$6F,$72,$20
loc_0_000087FA:
	dc.b "12345",$00	; string
	dc.b "Quit with task running",$00	; string
	dc.b "Printer device name",$00	; string
	dc.b "Press any key",$00	; string
	dc.b "Stop task",$00	; string
	dc.b "Kill task",$00	; string
	dc.b "Unload symbols",$00	; string
	dc.b "Interlace Y/N? ",$00	; string
	dc.b "Source window line numbers D/H/N? ",$00	; string
	dc.b "Auto-load source file Y/N? ",$00	; string
	dc.b "Automatic '_' or '@' prefix Y/N? ",$00	; string
	dc.b "Show ZAn in disassembly Y/N? ",$00	; string
	dc.b $00
loc_0_000088EC:
	dc.b $00,$00,$00,$00
loc_0_000088F0:
	dc.b $00,$00,$00,$00
loc_0_000088F4:
	dc.b $00	; lookup_table
loc_0_000088F5:
	dc.b $00
loc_0_000088F6:
	dc.l $00000000	; lookup_table
loc_0_000088FA:
	dc.b $00,$00
loc_0_000088FC:
	dc.b $00,$00
loc_0_000088FE:
	dcb.b $8,$00
loc_0_00008906:
	dc.b $00,$00
loc_0_00008908:
	dc.l $00000000	; lookup_table
loc_0_0000890C:
	dc.l $00000000	; lookup_table
loc_0_00008910:
	dc.b $00,$00
loc_0_00008912:
	dc.l $00000000	; lookup_table
loc_0_00008916:
	dc.l $00000000	; lookup_table
loc_0_0000891A:
	dcb.b $34,$00
loc_0_0000894E:
	dc.l $00000000,$00000000	; lookup_table
h0dl_DOSBase:
	dc.l $00000000	; lookup_table
loc_0_0000895A:
	dc.l $00000000	; lookup_table
loc_0_0000895E:
	dc.b $00,$00	; lookup_table
loc_0_00008960:
	dcb.b $D,$00
	dc.b $01,$00,$00,$00,$01
	dcb.b $16A,$00
    SECTION section_1,data_c
loc_1_00000000:
	dc.b $00,$0B,$00,$0C,$FF,$FA,$FF,$FE,$00,$00,$00,$00,$00,$00,$1F,$00
	dc.b $0A,$00,$35,$80,$00,$00,$7F,$C0,$00,$00,$7F,$C0,$00,$00,$3F,$80
	dc.b $00,$00,$5F,$40,$00,$00,$51,$40,$00,$00,$91,$20,$00,$00,$A0,$A0
	dc.b $00,$00,$A0,$A0,$80,$20,$A0,$A0,$20,$80,$20,$80
	dcb.b $8,$00
