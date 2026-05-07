    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"


    SECTION section_0,code
	dc.b $70,$00,$4E,$75
resident:	; STRUCT RT
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
	dc.b "clipboard.device",$00
	dc.b $00
resident_idstring:
	dc.b "clipboard 35.2 (9 May 1988)",$0D,$0A,$00
resident_init:
	movem.l a0/a6,-(a7)
	jsr loc_1_00000000.l
	addq.w #8,a7
	rts
loc_0_0000005C:
	movem.l d0/a1,-(a7)
	jsr loc_1_00000AA6.l
	addq.w #8,a7
	rts
loc_0_0000006A:
	move.l a1,-(a7)
	jsr loc_1_00000D80.l
	addq.w #4,a7
	rts
loc_0_00000076:
	jmp loc_1_00000EB0.l
loc_0_0000007C:
	move.l a1,-(a7)
	jsr loc_1_00000EEA.l
	addq.w #4,a7
	rts
loc_0_00000088:
	move.l a1,-(a7)
	jsr loc_1_00000F32.l
	addq.w #4,a7
loc_0_00000092:
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
	dc.b $48,$E7,$3C,$38,$26,$6F,$00,$20,$28,$6F,$00,$24,$24,$6F,$00,$28
	dc.b $4E,$B9
	dc.l loc_8_00000000
	dc.b $7A,$00,$4A,$6B,$00,$7A,$67,$00,$01,$08,$4A,$AB,$00,$44,$67,$3E
	dc.b $00,$2C,$00,$40,$00,$1E,$74,$FF,$2F,$02,$2F,$2F,$00,$34,$2F,$2B
	dc.b $00,$44,$4E,$B9
	dc.l loc_7_00000068
	dc.b $72,$FF,$B2,$80,$4F,$EF,$00,$0C,$67,$00,$00,$DE,$2F,$2F,$00,$2C
	dc.b $2F,$0A,$2F,$2B,$00,$44,$4E,$B9
	dc.l loc_7_00000030
	dc.b $2A,$00,$4F,$EF,$00,$0C,$60,$00,$00,$C4,$20,$2B,$00,$76,$B0,$AF
	dc.b $00,$30,$63,$00,$00,$B8,$20,$2F,$00,$2C,$D0,$AF,$00,$30,$B0,$AB
	dc.b $00,$76,$63,$0A,$2A,$2B,$00,$76,$9A,$AF,$00,$30,$60,$04,$2A,$2F
	dc.b $00,$2C,$4A,$85,$67,$00,$00,$96,$22,$2F,$00,$30,$70,$09,$E0,$A9
	dc.b $26,$2F,$00,$30,$02,$83,$00,$00,$01,$FF,$22,$6B,$00,$72,$24,$09
	dc.b $66,$04,$22,$6B,$00,$64,$20,$01,$B0,$A9,$00,$0E,$67,$1A,$60,$04
	dc.b $22,$69,$00,$04,$20,$01,$B0,$A9,$00,$0E,$65,$F4,$60,$02,$22,$51
	dc.b $20,$01,$B0,$A9,$00,$0E,$62,$F6,$28,$05,$60,$48,$20,$3C,$00,$00
	dc.b $02,$00,$90,$83,$B8,$80,$63,$22,$34,$03,$60,$08,$30,$02,$14,$F1
	dc.b $00,$12,$52,$42,$0C,$42,$02,$00,$6D,$F2,$22,$51,$20,$3C,$00,$00
	dc.b $02,$00,$90,$83,$98,$80,$76,$00,$60,$1A,$34,$03,$60,$08,$30,$02
	dc.b $14,$F1,$00,$12,$52,$42,$30,$02,$48,$C0,$22,$04,$D2,$83,$B0,$81
	dc.b $65,$EC,$78,$00,$4A,$84,$66,$B4,$27,$49,$00,$72,$4E,$B9
	dc.l loc_8_00000010
	dc.b $20,$05,$4C,$DF,$1C,$3C,$4E,$75,$48,$E7,$3C,$3C,$24,$6F,$00,$24
	dc.b $28,$6F,$00,$28,$26,$6F,$00,$2C,$4E,$B9
	dc.l loc_8_00000000
	dc.b $7A,$00,$4A,$AA,$00,$44,$66,$00,$00,$F4,$20,$2F,$00,$30,$D0,$AF
	dc.b $00,$34,$0C,$80,$00,$00,$07,$D0,$63,$00,$00,$E2,$4A,$6A,$00,$7A
	dc.b $67,$00,$00,$DA,$2F,$3C,$00,$02,$00,$00,$4E,$B9
	dc.l loc_8_00000050
	dc.b $0C,$80,$00,$00,$40,$00,$58,$8F,$6C,$00,$00,$C2,$48,$78,$03,$EE
	dc.b $2F,$0A,$4E,$BA,$FD,$42,$25,$40,$00,$44,$50,$8F,$67,$00,$00,$AA
	dc.b $26,$2A,$00,$64,$60,$00,$00,$8C,$20,$2A,$00,$76,$20,$43,$22,$28
	dc.b $00,$0E,$E1,$81,$E3,$81,$B0,$81,$63,$68,$20,$2A,$00,$76,$20,$43
	dc.b $22,$28,$00,$0E,$52,$81,$E1,$81,$E3,$81,$B0,$81,$64,$30,$24,$2A
	dc.b $00,$76,$02,$82,$00,$00,$01,$FF,$20,$2A,$00,$76,$02,$80,$00,$00
	dc.b $01,$FF,$2F,$00,$2A,$43,$48,$6D,$00,$12,$2F,$2A,$00,$44,$4E,$B9
	dc.l loc_7_0000004C
	dc.b $B4,$80,$4F,$EF,$00,$0C,$67,$26,$60,$20,$48,$78,$02,$00,$2A,$43
	dc.b $48,$6D,$00,$12,$2F,$2A,$00,$44,$4E,$B9
	dc.l loc_7_0000004C
	dc.b $0C,$80,$00,$00,$02,$00,$4F,$EF,$00,$0C,$67,$04,$42,$6A,$00,$7A
	dc.b $48,$78,$02,$12,$2F,$03,$4E,$B9
	dc.l loc_8_00000038
	dc.b $26,$04,$50,$8F,$20,$43,$28,$10,$66,$00,$FF,$70,$48,$6A,$00,$64
	dc.b $4E,$B9
	dc.l loc_5_00000000
	dc.b $58,$8F,$60,$04,$42,$6A,$00,$7A,$4A,$6A,$00,$7A,$67,$00,$01,$32
	dc.b $4A,$AA,$00,$44,$67,$3E,$00,$2C,$00,$40,$00,$1E,$74,$FF,$2F,$02
	dc.b $2F,$2F,$00,$38,$2F,$2A,$00,$44,$4E,$B9
	dc.l loc_7_00000068
	dc.b $72,$FF,$B2,$80,$4F,$EF,$00,$0C,$67,$00,$01,$08,$2F,$2F,$00,$30
	dc.b $2F,$0B,$2F,$2A,$00,$44,$4E,$B9
	dc.l loc_7_0000004C
	dc.b $2A,$00,$4F,$EF,$00,$0C,$60,$00,$00,$EE,$24,$2F,$00,$34,$70,$09
	dc.b $E0,$AA,$28,$2F,$00,$34,$02,$84,$00,$00,$01,$FF,$26,$2A,$00,$72
	dc.b $66,$0A,$2F,$0A,$4E,$BA,$FB,$BC,$26,$00,$58,$8F,$4A,$83,$67,$40
	dc.b $20,$02,$20,$43,$B0,$A8,$00,$0E,$67,$36,$60,$06,$20,$43,$26,$28
	dc.b $00,$04,$20,$02,$20,$43,$B0,$A8,$00,$0E,$65,$F0,$60,$14,$20,$43
	dc.b $26,$10,$20,$43,$4A,$90,$66,$0A,$2F,$0A,$4E,$BA,$FB,$86,$26,$00
	dc.b $58,$8F,$4A,$83,$67,$0A,$20,$02,$20,$43,$B0,$A8,$00,$0E,$62,$DE
	dc.b $60,$00,$00,$76,$20,$3C,$00,$00,$02,$00,$90,$84,$B0,$AF,$00,$30
	dc.b $64,$42,$34,$04,$60,$0A,$30,$02,$22,$43,$13,$9B,$00,$12,$52,$42
	dc.b $0C,$42,$02,$00,$6D,$F0,$20,$43,$26,$10,$20,$43,$4A,$90,$66,$0A
	dc.b $2F,$0A,$4E,$BA,$FB,$3E,$26,$00,$58,$8F,$20,$3C,$00,$00,$02,$00
	dc.b $90,$84,$DA,$80,$20,$3C,$00,$00,$02,$00,$90,$84,$91,$AF,$00,$30
	dc.b $78,$00,$60,$24,$34,$04,$60,$0A,$30,$02,$22,$43,$13,$9B,$00,$12
	dc.b $52,$42,$30,$02,$48,$C0,$22,$2F,$00,$30,$D2,$84,$B0,$81,$65,$E8
	dc.b $DA,$AF,$00,$30,$42,$AF,$00,$30,$4A,$83,$67,$06,$4A,$AF,$00,$30
	dc.b $62,$82,$25,$43,$00,$72,$4E,$B9
	dc.l loc_8_00000010
	dc.b $20,$05,$4C,$DF,$3C,$3C,$4E,$75
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
	dc.b $48,$E7,$20,$20,$24,$6F,$00,$0C,$24,$2F,$00,$10,$08,$2A,$00,$07
	dc.b $00,$1E,$66,$0A,$2F,$0A,$4E,$B9
	dc.l loc_8_00000098
	dc.b $58,$8F,$B5,$C2,$67,$06,$02,$2A,$00,$FE,$00,$1E,$2F,$0A,$4E,$BA
	dc.b $FF,$96,$02,$2A,$00,$DF,$00,$1E,$58,$8F,$4C,$DF,$04,$04,$4E,$75
	dc.b $20,$6F,$00,$04,$22,$68,$00,$8C,$20,$68,$00,$7C,$4A,$91,$67,$16
	dc.b $4A,$90,$67,$10,$20,$28,$00,$30,$B0,$A9,$00,$30,$6C,$02,$60,$06
	dc.b $42,$40,$60,$04,$60,$FA,$70,$01,$48,$C0,$4E,$75,$20,$6F,$00,$04
	dc.b $22,$6F,$00,$08,$20,$2F,$00,$0C,$21,$69,$00,$28,$00,$B4,$31,$68
	dc.b $00,$10,$00,$AE,$21,$69,$00,$30,$00,$B0,$2F,$00,$2F,$09,$4E,$BA
	dc.b $FF,$74,$50,$8F,$4E,$75,$48,$E7,$20,$38,$24,$6F,$00,$14,$26,$6F
	dc.b $00,$18,$00,$2B,$00,$20,$00,$1E,$4A,$2A,$00,$42,$67,$0C,$02,$2B
	dc.b $00,$FE,$00,$1E,$70,$00,$60,$00,$02,$78,$15,$7C,$00,$01,$00,$42
	dc.b $74,$01,$4A,$6A,$00,$40,$66,$00,$00,$84,$2F,$0A,$4E,$BA,$FF,$72
	dc.b $30,$00,$58,$8F,$67,$18,$28,$6A,$00,$7C,$4A,$94,$67,$0E,$25,$6C
	dc.b $00,$30,$00,$3C,$35,$7C,$00,$02,$00,$40,$60,$60,$60,$5C,$28,$6A
	dc.b $00,$8C,$4A,$94,$67,$54,$25,$6C,$00,$30,$00,$3C,$30,$2C,$00,$1C
	dc.b $35,$40,$00,$40,$0C,$40,$00,$09,$66,$0E,$2F,$0B,$2F,$0C,$2F,$0A
	dc.b $4E,$BA,$FF,$5A,$4F,$EF,$00,$0C,$4A,$AA,$00,$44,$67,$1C,$2F,$2A
	dc.b $00,$44,$4E,$B9
	dc.l loc_7_0000001C
	dc.b $42,$AA,$00,$44,$48,$6A,$00,$48,$4E,$B9
	dc.l loc_7_00000084
	dc.b $50,$8F,$60,$08,$2F,$0A,$4E,$BA,$FA,$B8,$58,$8F,$35,$7C,$00,$01
	dc.b $00,$7A,$60,$02,$42,$42,$0C,$6A,$00,$09,$00,$40,$66,$5C,$2F,$0A
	dc.b $4E,$BA,$FE,$E8,$30,$00,$58,$8F,$67,$22,$28,$6A,$00,$7C,$4A,$94
	dc.b $67,$18,$48,$6A,$00,$9A,$2F,$2A,$00,$B4,$4E,$B9
	dc.l loc_8_0000012C
	dc.b $35,$7C,$00,$03,$00,$40,$50,$8F,$60,$30,$60,$2C,$28,$6A,$00,$8C
	dc.b $4A,$94,$67,$24,$25,$6C,$00,$30,$00,$3C,$30,$2C,$00,$1C,$35,$40
	dc.b $00,$40,$0C,$40,$00,$09,$66,$12,$2F,$0B,$2F,$0C,$2F,$0A,$4E,$BA
	dc.b $FE,$C6,$4F,$EF,$00,$0C,$60,$02,$42,$42,$0C,$6A,$00,$02,$00,$40
	dc.b $66,$00,$00,$A2,$28,$6A,$00,$7C,$4A,$94,$67,$00,$00,$96,$08,$2C
	dc.b $00,$04,$00,$1E,$67,$0A,$52,$6A,$00,$8A,$02,$2C,$00,$EF,$00,$1E
	dc.b $20,$2A,$00,$76,$B0,$AC,$00,$2C,$63,$54,$4A,$AC,$00,$28,$67,$22
	dc.b $2F,$2C,$00,$2C,$2F,$2C,$00,$24,$2F,$2C,$00,$28,$2F,$0C,$2F,$0A
	dc.b $4E,$BA,$FA,$42,$29,$40,$00,$20,$D1,$AC,$00,$2C,$4F,$EF,$00,$14
	dc.b $60,$3A,$20,$2C,$00,$24,$D0,$AC,$00,$2C,$B0,$AA,$00,$76,$64,$08
	dc.b $29,$6C,$00,$24,$00,$20,$60,$0C,$20,$2A,$00,$76,$90,$AC,$00,$2C
	dc.b $29,$40,$00,$20,$20,$2C,$00,$20,$D1,$AC,$00,$2C,$60,$0E,$42,$AC
	dc.b $00,$20,$70,$FF,$29,$40,$00,$30,$53,$6A,$00,$8A,$2F,$0B,$2F,$0C
	dc.b $4E,$BA,$FD,$BC,$4A,$6A,$00,$8A,$50,$8F,$66,$08,$42,$6A,$00,$40
	dc.b $60,$02,$42,$42,$0C,$6A,$00,$03,$00,$40,$66,$00,$00,$68,$28,$6A
	dc.b $00,$8C,$4A,$94,$67,$5C,$0C,$6C,$00,$03,$00,$1C,$66,$44,$2F,$2C
	dc.b $00,$2C,$2F,$2C,$00,$24,$2F,$2C,$00,$28,$2F,$0C,$2F,$0A,$4E,$BA
	dc.b $FA,$E8,$29,$40,$00,$20,$D1,$AC,$00,$2C,$20,$2C,$00,$2C,$B0,$AA
	dc.b $00,$76,$4F,$EF,$00,$14,$64,$06,$20,$2A,$00,$76,$60,$04,$20,$2C
	dc.b $00,$2C,$25,$40,$00,$76,$2F,$0B,$2F,$0C,$4E,$BA,$FD,$52,$50,$8F
	dc.b $60,$12,$0C,$6C,$00,$04,$00,$1C,$66,$08,$35,$7C,$00,$04,$00,$40
	dc.b $60,$02,$42,$42,$0C,$6A,$00,$04,$00,$40,$66,$46,$28,$6A,$00,$8C
	dc.b $70,$08,$B0,$AA,$00,$76,$62,$24,$48,$78,$00,$04,$48,$78,$00,$04
	dc.b $48,$6A,$00,$76,$2F,$0C,$2F,$0A,$4E,$BA,$F9,$4A,$72,$04,$B2,$80
	dc.b $4F,$EF,$00,$14,$66,$06,$50,$AA,$00,$76,$60,$04,$42,$AA,$00,$76
	dc.b $42,$6A,$00,$8A,$2F,$0B,$2F,$0C,$4E,$BA,$FC,$F4,$42,$6A,$00,$40
	dc.b $50,$8F,$4A,$42,$66,$00,$FD,$A6,$08,$2B,$00,$05,$00,$1E,$67,$06
	dc.b $02,$2B,$00,$FE,$00,$1E,$42,$2A,$00,$42,$4C,$DF,$1C,$04,$4E,$75
	dc.b $2F,$0A,$22,$6F,$00,$08,$20,$6F,$00,$0C,$24,$51,$22,$12,$60,$10
	dc.b $20,$2A,$00,$30,$B0,$A8,$00,$30,$6E,$04,$24,$41,$60,$EE,$72,$00
	dc.b $4A,$81,$66,$EC,$2F,$2A,$00,$04,$2F,$08,$2F,$09,$4E,$B9
	dc.l loc_8_00000064
	dc.b $4F,$EF,$00,$0C,$24,$5F,$4E,$75
loc_1_0000095C:
	movea.l $0004(a7),a0
	move.b #$FD,$001F(a0)
	move.l a0,-(a7)
	jsr loc_1_000005B2(pc)
	addq.l #4,a7
	rts
loc_1_00000970:
	dc.b $20,$2F,$00,$04,$2F,$00,$4E,$BA,$FF,$E4,$58,$8F,$4E,$75
loc_1_0000097E:
	dc.b $20,$2F,$00,$04,$2F,$00,$4E,$BA,$FF,$D6,$58,$8F,$4E,$75
loc_1_0000098C:
	dc.b $20,$2F,$00,$04,$2F,$00,$4E,$BA,$FF,$C8,$58,$8F,$4E,$75
loc_1_0000099A:
	dc.b $20,$2F,$00,$04,$2F,$00,$4E,$BA,$FF,$BA,$58,$8F,$4E,$75
loc_1_000009A8:
	dc.b $2F,$02,$24,$2F,$00,$08,$2F,$02,$4E,$BA,$FF,$CC,$2F,$02,$4E,$BA
	dc.b $FF,$E2,$2F,$02,$4E,$BA,$FF,$CE,$4F,$EF,$00,$0C,$24,$1F,$4E,$75
loc_1_000009C8:
	dc.b $48,$E7,$00,$30,$24,$6F,$00,$0C,$26,$6A,$00,$18,$4A,$AA,$00,$30
	dc.b $66,$0C,$25,$6B,$00,$38,$00,$30,$00,$2A,$00,$10,$00,$1E,$20,$2B
	dc.b $00,$3C,$B0,$AA,$00,$30,$6F,$14,$42,$AA,$00,$20,$15,$7C,$00,$01
	dc.b $00,$1F,$2F,$0A,$4E,$BA,$FB,$B4,$58,$8F,$60,$16,$2F,$0A,$48,$6B
	dc.b $00,$7C,$4E,$BA,$FF,$16,$2F,$0A,$2F,$0B,$4E,$BA,$FC,$6E,$4F,$EF
	dc.b $00,$10,$4C,$DF,$0C,$00,$4E,$75
loc_1_00000A20:
	dc.b $48,$E7,$00,$30,$24,$6F,$00,$0C,$26,$6A,$00,$18,$4A,$AA,$00,$30
	dc.b $66,$0A,$52,$AB,$00,$38,$25,$6B,$00,$38,$00,$30,$20,$2B,$00,$3C
	dc.b $B0,$AA,$00,$30,$6F,$14,$42,$AA,$00,$20,$15,$7C,$00,$01,$00,$1F
	dc.b $2F,$0A,$4E,$BA,$FB,$5E,$58,$8F,$60,$16,$2F,$0A,$48,$6B,$00,$8C
	dc.b $4E,$BA,$FE,$C0,$2F,$0A,$2F,$0B,$4E,$BA,$FC,$18,$4F,$EF,$00,$10
	dc.b $4C,$DF,$0C,$00,$4E,$75
loc_1_00000A76:
	dc.b $20,$6F,$00,$04,$22,$68,$00,$18,$21,$69,$00,$38,$00,$30,$2F,$08
	dc.b $4E,$BA,$FB,$2A,$58,$8F,$4E,$75
loc_1_00000A8E:
	dc.b $20,$6F,$00,$04,$22,$68,$00,$18,$21,$69,$00,$3C,$00,$30,$2F,$08
	dc.b $4E,$BA,$FB,$12,$58,$8F,$4E,$75
loc_1_00000AA6:
	link a6,#-24
	movem.l d2-d5/a2-a5,-(a7)
	move.l $0008(a6),d2
	movea.l $000C(a6),a2
	move.l #loc_5_00000000,d3
	move.l #loc_2_00000068,d4
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
	movea.l #loc_2_00000068,a2
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
	dc.b $64,$6F,$73,$2E,$6C,$69,$62,$72,$61,$72,$79,$00
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
loc_2_00000068:
	jmp loc_0_00000088.l
loc_2_0000006E:
	jmp loc_0_0000007C.l
loc_2_00000074:
	jmp loc_0_00000092.l
loc_2_0000007A:
	jmp loc_0_00000076.l
loc_2_00000080:
	jmp loc_0_0000006A.l
loc_2_00000086:
	jmp loc_0_0000005C.l
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
	dc.b $63,$6C,$69,$70,$62,$6F,$61,$72,$64,$2E,$64,$65,$76,$69,$63,$65
	dc.b $00,$00
loc_2_000000C0:
	dc.b $63,$6C,$69,$70,$62,$6F,$61,$72,$64,$20,$33,$35,$2E,$32,$20,$28
	dc.b $39,$20,$4D,$61,$79,$20,$31,$39,$38,$38,$29,$0A,$0D,$00
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
	dc.b $2F,$0E,$2C,$79
	dc.l loc_2_0000010E
	dc.b $22,$2F,$00,$08,$4E,$AE,$FF,$28,$2C,$5F,$4E,$75
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
