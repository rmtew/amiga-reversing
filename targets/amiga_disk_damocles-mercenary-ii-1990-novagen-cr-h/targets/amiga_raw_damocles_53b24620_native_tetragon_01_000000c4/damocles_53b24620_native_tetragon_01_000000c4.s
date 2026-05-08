    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/resident.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/dmabits.i"
    INCLUDE "hardware/intbits.i"

_custom	EQU	$DFF000
_ciaa	EQU	$BFE001

    SECTION code,code
loc_0_00000000:
    ORG $40000
abs_0_00040000:
	movem.l d0-d7/a0-a6,-(a7)
	bsr.w abs_0_00040060
	movem.l (a7)+,d0-d7/a0-a6
	movea.l $00000004.l,a6
	lea.l abs_0_00040024(pc),a1
	jsr _LVOFindResident(a6)
	movea.l d0,a0
	movea.l RT_INIT(a0),a0
	moveq.l #0,d0
	rts
abs_0_00040024:
	dc.b "dos.library",$00	; string
abs_0_00040030:
	dc.b "        PRESENTS NEW STUFF    "	; string
abs_0_0004004E:
	dc.b $4D,$4C
abs_0_00040050:
	dc.b "        KRAYZI  "	; string
abs_0_00040060:
	move.w #DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER,_custom+dmacon.l
	move.w #INTF_INTEN,_custom+intena.l
	movea.l #$32000,a0
	move.w #$2800,d0
abs_0_0004007A:
	clr.l (a0)+
	dbf.w d0,abs_0_0004007A
	lea.l abs_0_00040030(pc),a0
	movea.l $00000004.l,a6
	lea.l abs_0_00040264(pc),a1
	jsr _LVOOldOpenLibrary(a6)
	lea.l abs_0_00040274(pc),a0
	move.l d0,(a0)
	tst.l d0
	bne.w abs_0_000400A0
	rts
abs_0_000400A0:
	movea.l d0,a6
	movea.l #$31000,a1
	jsr -$00C6(a6)
	movea.l #$31064,a0
	move.l #$38000,$0008(a0)
	move.b #$1,d0
	move.w #$140,d1
	move.w #$100,d2
	jsr -$0186(a6)
	move.l #$31064,$00031004.l
	move.w #$82,d1
	move.w #$19,d0
	movea.l #$31000,a1
	jsr -$00F0(a6)
	move.b #$1,d0
	jsr -$0156(a6)
	lea.l abs_0_00040030(pc),a0
	move.w #$1A,d0
	jsr -$003C(a6)
	move.w #$FA,d1
	move.w #$122,d0
	movea.l #$31000,a1
	jsr -$00F0(a6)
	lea.l abs_0_0004004E(pc),a0
	move.w #$2,d0
	jsr -$003C(a6)
	move.w #$A,d1
	move.w #$3C,d0
	movea.l #$31000,a1
	jsr -$00F0(a6)
	lea.l abs_0_00040050(pc),a0
	move.w #$10,d0
	jsr -$003C(a6)
	movea.l #abs_0_00042000,a0
	lea.l abs_0_000402D2(pc),a1
	lea.l abs_0_000403D6(pc),a2
abs_0_00040144:
	move.b (a1)+,(a0)+
	cmpa.l a2,a1
	bne.w abs_0_00040144
	move.w #DMAF_SPRITE,_custom+dmacon.l
	movea.l #abs_0_00042000,a0
	move.l a0,_custom+cop1lc.l	; copper_list pointer
	move.w #$45,d3
	movea.l #abs_0_00044000,a0
abs_0_0004016A:
	bsr.w abs_0_00040278
	move.w d0,(a0)+
	bsr.w abs_0_00040278
	move.w d0,(a0)+
	bsr.w abs_0_00040278
	andi.w #511,d0
	move.w d0,(a0)+
	dbf.w d3,abs_0_0004016A
abs_0_00040184:
	movea.l #abs_0_00044000,a4
	move.w #$45,d3
	movea.l #abs_0_00043000,a5
abs_0_00040194:
	move.w (a4)+,d4
	move.w (a4)+,d5
	move.w (a4),d6
	subi.w #2,(a4)+
	tst.w d6
	ble.w abs_0_00040292
	ext.l d4
	divs.w d6,d4
	addi.w #160,d4
	ext.l d5
	divs.w d6,d5
	addi.w #128,d5
	tst.w d4
	blt.w abs_0_00040292
	tst.w d5
	blt.w abs_0_00040292
	cmpi.w #319,d4
	bgt.w abs_0_00040292
	cmpi.w #255,d5
	bgt.w abs_0_00040292
	move.w (a5),d0
	move.w d4,(a5)+
	move.w (a5),d1
	move.w d5,(a5)+
	bsr.w abs_0_000402AC
	move.w d4,d0
	move.w d5,d1
	mulu.w #$28,d1
	move.w d0,d2
	asr.w #3,d2
	add.w d2,d1
	asl.w #3,d2
	sub.w d0,d2
	subq.b #1,d2
	cmpi.w #400,d6
	bgt.b abs_0_000401FE
	cmpi.w #300,d6
	bgt.b abs_0_0004020A
	bra.b abs_0_00040216
abs_0_000401FE:
	movea.l #$32000,a1
	adda.l d1,a1
	bset.b d2,(a1)
	bra.b abs_0_0004022A
abs_0_0004020A:
	movea.l #$35000,a1
	adda.l d1,a1
	bset.b d2,(a1)
	bra.b abs_0_0004022A
abs_0_00040216:
	movea.l #$32000,a1
	adda.l d1,a1
	bset.b d2,(a1)
	movea.l #$35000,a1
	adda.l d1,a1
	bset.b d2,(a1)
abs_0_0004022A:
	dbf.w d3,abs_0_00040194
	lea.l abs_0_000403D6(pc),a6
	subi.w #1,(a6)
	tst.w (a6)
	beq.b abs_0_00040246
	btst.b #CIAB_GAMEPORT0,_ciaa+ciapra.l
	bne.w abs_0_00040184
abs_0_00040246:
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
	movea.l abs_0_00040274(pc),a6
	move.l $0026(a6),_custom+cop1lc.l	; copper_list pointer
	move.w #$FFEC,_custom+dmacon.l
	rts
abs_0_00040264:
	dc.b "graphics.library"	; string
abs_0_00040274:
	dc.l $00000000	; lookup_table
abs_0_00040278:
	move.w _custom+vhposr.l,d0
	lea.l abs_0_000403D8(pc),a3
	muls.w (a3),d0
	addi.w #4681,d0
	ext.l d0
	lea.l abs_0_000403D8(pc),a3
	move.w d0,(a3)
	rts
abs_0_00040292:
	suba.l #$6,a4
	bsr.w abs_0_00040278
	move.w d0,(a4)+
	bsr.w abs_0_00040278
	move.w d0,(a4)+
	move.w #$258,(a4)+
	bra.w abs_0_0004022A
abs_0_000402AC:
	mulu.w #$28,d1
	move.w d0,d2
	asr.w #3,d2
	add.w d2,d1
	asl.w #3,d2
	sub.w d0,d2
	subq.b #1,d2
	movea.l #$32000,a1
	adda.l d1,a1
	bclr.b d2,(a1)
	movea.l #$35000,a1
	adda.l d1,a1
	bclr.b d2,(a1)
	rts
abs_0_000402D2:
	dc.b $01,$80,$00,$00,$01,$82,$03,$35,$01,$84,$06,$68,$01,$86,$0A,$AC
	dc.b $01,$8A,$0F,$00,$01,$8C,$0F,$00,$01,$00,$02,$00,$01,$04,$00,$24
	dc.b $00,$8E,$05,$81,$00,$90,$40,$C1,$00,$92,$00,$38,$00,$94,$00,$D0
	dc.b $01,$02,$00,$00,$01,$08,$00,$00,$01,$0A,$00,$00,$00,$E0,$00,$03
	dc.b $00,$E2,$20,$00,$00,$E4,$00,$03,$00,$E6,$50,$00,$00,$E8,$00,$03
	dc.b $00,$EA,$80,$00,$2C,$01,$FF,$FE,$01,$00,$32,$00,$9E,$01,$FF,$FE
	dc.b $01,$8E,$0F,$00,$01,$88,$0F,$00,$01,$80,$00,$02,$A0,$01,$FF,$FE
	dc.b $01,$80,$00,$03,$A2,$01,$FF,$FE,$01,$80,$00,$05,$A4,$01,$FF,$FE
	dc.b $01,$80,$00,$07,$A6,$01,$FF,$FE,$01,$80,$00,$09,$A8,$01,$FF,$FE
	dc.b $01,$80,$00,$0B,$AA,$01,$FF,$FE,$01,$80,$00,$0D,$AC,$01,$FF,$FE
	dc.b $01,$80,$00,$0F,$AE,$01,$FF,$FE,$01,$80,$00,$0D,$B0,$01,$FF,$FE
	dc.b $01,$80,$00,$0B,$B2,$01,$FF,$FE,$01,$80,$00,$09,$B4,$01,$FF,$FE
	dc.b $01,$80,$00,$07,$B6,$01,$FF,$FE,$01,$80,$00,$05,$B8,$01,$FF,$FE
	dc.b $01,$80,$00,$03,$BA,$01,$FF,$FE,$01,$80,$00,$01,$BC,$01,$FF,$FE
	dc.b $01,$80,$00,$01,$BE,$01,$FF,$FE,$01,$80,$00,$00,$FF,$DF,$FF,$FE
	dc.b $01,$88,$04,$44,$01,$8E,$04,$45,$2B,$01,$FF,$FE,$01,$00,$02,$00
	dc.b $FF,$FF,$FF,$FE
abs_0_000403D6:
	dc.b $13,$88
abs_0_000403D8:
	dc.b $00,$00
	dc.b "RV (20-07-1988)",$00	; string
	dc.b $41,$FA,$65,$72,$20,$6F
	dcb.b $1C10,$00
abs_0_00042000:
	dcb.b $1000,$00
abs_0_00043000:
	dcb.b $1000,$00
abs_0_00044000:
	dcb.b $C000,$00
