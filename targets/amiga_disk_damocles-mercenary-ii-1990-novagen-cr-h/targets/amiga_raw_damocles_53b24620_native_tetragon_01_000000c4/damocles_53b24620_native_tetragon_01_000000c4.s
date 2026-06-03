; Memory map
;   code[$00000000-$00010000] -> runtime[$00040000-$00050000] policy materialized
;   code[$000002D2-$00010000] -> runtime[$00042000-$00051D2E] conflicting_discovered_copy suppressed
;   code[$000002D3-$00010000] -> runtime[$00042001-$00051D2E] conflicting_discovered_copy suppressed
;   Absolute memory refs:
;     absolute[$00031000] refs=4 access=r
;     absolute[$00031004-$00031008] refs=1 access=w
;     absolute[$00031064] refs=1 access=r
;     absolute[$00032000-$00038000] refs=9 access=ra
;     absolute[$00038000-$0003B000] refs=1 access=a

; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: SysBase/_LVOOldOpenLibrary, _LVOFindResident, _LVOOldOpenLibrary

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/resident.i"
    INCLUDE "graphics/copper.i"
    INCLUDE "graphics/display.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/dmabits.i"
    INCLUDE "hardware/intbits.i"

_custom	EQU	$DFF000
runtime_address_00031000	EQU	$31000
runtime_address_00031064	EQU	$31064
copper_list_00042000	EQU	$42000
runtime_address_00044000	EQU	$44000
runtime_address_00043000	EQU	$43000
_ciaa	EQU	$BFE001
BPLCON2_PF2P2	EQU	$20
BPLCON2_PF1P2	EQU	$4
bitmap_00032000	EQU	$32000
bitmap_00032000_hi	EQU	bitmap_00032000/$10000
bitmap_00032000_lo	EQU	bitmap_00032000-(bitmap_00032000_hi*$10000)
bitmap_00035000	EQU	$35000
bitmap_00035000_hi	EQU	bitmap_00035000/$10000
bitmap_00035000_lo	EQU	bitmap_00035000-(bitmap_00035000_hi*$10000)
bitmap_00038000	EQU	$38000
bitmap_00038000_hi	EQU	bitmap_00038000/$10000
bitmap_00038000_lo	EQU	bitmap_00038000-(bitmap_00038000_hi*$10000)

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
	dc.b "dos.library",$00
abs_0_00040030:
	dcb.b $8,$20
	dc.b $50,$52,$45,$53,$45,$4E,$54,$53,$20,$4E,$45,$57,$20,$53,$54,$55
	dc.b $46,$46,$20,$20,$20,$20
abs_0_0004004E:
	dc.b $4D,$4C
abs_0_00040050:
	dc.b "        KRAYZI  "
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
	movea.l #runtime_address_00031000,a1
	jsr -$00C6(a6)
	movea.l #runtime_address_00031064,a0
	move.l #$38000,$0008(a0)
	move.b #$1,d0
	move.w #$140,d1
	move.w #$100,d2
	jsr -$0186(a6)
	move.l #$31064,$00031004.l
	move.w #$82,d1
	move.w #$19,d0
	movea.l #runtime_address_00031000,a1
	jsr -$00F0(a6)
	move.b #$1,d0
	jsr -$0156(a6)
	lea.l abs_0_00040030(pc),a0
	move.w #$1A,d0
	jsr -$003C(a6)
	move.w #$FA,d1
	move.w #$122,d0
	movea.l #runtime_address_00031000,a1
	jsr -$00F0(a6)
	lea.l abs_0_0004004E(pc),a0
	move.w #$2,d0
	jsr -$003C(a6)
	move.w #$A,d1
	move.w #$3C,d0
	movea.l #runtime_address_00031000,a1
	jsr -$00F0(a6)
	lea.l abs_0_00040050(pc),a0
	move.w #$10,d0
	jsr -$003C(a6)
	movea.l #$42000,a0
	lea.l abs_0_000402D2(pc),a1
	lea.l abs_0_000403D6(pc),a2
abs_0_00040144:
	move.b (a1)+,(a0)+
	cmpa.l a2,a1
	bne.w abs_0_00040144
	move.w #DMAF_SPRITE,_custom+dmacon.l
	movea.l #copper_list_00042000,a0
	move.l a0,_custom+cop1lc.l	; copper_list pointer
	move.w #$45,d3
	movea.l #runtime_address_00044000,a0
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
	movea.l #runtime_address_00044000,a4
	move.w #$45,d3
	movea.l #runtime_address_00043000,a5
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
	dc.b "graphics.library"
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
    ; display layout 3 bitmap planes $00032000..$00038000 step $3000
	dc.w color,$0000
	dc.w color+$02,$0335
	dc.w color+$04,$0668
	dc.w color+$06,$0AAC
	dc.w color+$0A,$0F00
	dc.w color+$0C,$0F00
	dc.w bplcon0,COLORON
	dc.w bplcon2,BPLCON2_PF2P2|BPLCON2_PF1P2
	dc.w diwstrt,$0581	; display window start v=$05 h=$81
	dc.w diwstop,$40C1	; display window stop v=$40 h=$C1
	dc.w ddfstrt,$0038	; display fetch start $38
	dc.w ddfstop,$00D0	; display fetch stop $D0
	dc.w bplcon1,$0000	; display scroll pf1=0 pf2=0
	dc.w bpl1mod,$0000	; bitplane modulo 0 bytes
	dc.w bpl2mod,$0000	; bitplane modulo 0 bytes
	dc.w bplpt,bitmap_00032000_hi	; bitmap pointer $00032000
	dc.w bplpt+$02,bitmap_00032000_lo
	dc.w bplpt+$04,bitmap_00035000_hi	; bitmap pointer $00035000
	dc.w bplpt+$06,bitmap_00035000_lo
	dc.w bplpt+$08,bitmap_00038000_hi	; bitmap pointer $00038000
	dc.w bplpt+$0A,bitmap_00038000_lo
	dc.w COPPER_WAIT|$2C00,$FFFE	; copper wait v=$2C h=$00 mask $FFFE
	dc.w bplcon0,(3<<PLNCNTSHFT)|COLORON	; display 3 bitplanes lores color
	dc.w COPPER_WAIT|$9E00,$FFFE	; copper wait v=$9E h=$00 mask $FFFE
	dc.w color+$0E,$0F00
	dc.w color+$08,$0F00
	dc.w color,$0002
	dc.w COPPER_WAIT|$A000,$FFFE	; copper wait v=$A0 h=$00 mask $FFFE
	dc.w color,$0003
	dc.w COPPER_WAIT|$A200,$FFFE	; copper wait v=$A2 h=$00 mask $FFFE
	dc.w color,$0005
	dc.w COPPER_WAIT|$A400,$FFFE	; copper wait v=$A4 h=$00 mask $FFFE
	dc.w color,$0007
	dc.w COPPER_WAIT|$A600,$FFFE	; copper wait v=$A6 h=$00 mask $FFFE
	dc.w color,$0009
	dc.w COPPER_WAIT|$A800,$FFFE	; copper wait v=$A8 h=$00 mask $FFFE
	dc.w color,$000B
	dc.w COPPER_WAIT|$AA00,$FFFE	; copper wait v=$AA h=$00 mask $FFFE
	dc.w color,$000D
	dc.w COPPER_WAIT|$AC00,$FFFE	; copper wait v=$AC h=$00 mask $FFFE
	dc.w color,$000F
	dc.w COPPER_WAIT|$AE00,$FFFE	; copper wait v=$AE h=$00 mask $FFFE
	dc.w color,$000D
	dc.w COPPER_WAIT|$B000,$FFFE	; copper wait v=$B0 h=$00 mask $FFFE
	dc.w color,$000B
	dc.w COPPER_WAIT|$B200,$FFFE	; copper wait v=$B2 h=$00 mask $FFFE
	dc.w color,$0009
	dc.w COPPER_WAIT|$B400,$FFFE	; copper wait v=$B4 h=$00 mask $FFFE
	dc.w color,$0007
	dc.w COPPER_WAIT|$B600,$FFFE	; copper wait v=$B6 h=$00 mask $FFFE
	dc.w color,$0005
	dc.w COPPER_WAIT|$B800,$FFFE	; copper wait v=$B8 h=$00 mask $FFFE
	dc.w color,$0003
	dc.w COPPER_WAIT|$BA00,$FFFE	; copper wait v=$BA h=$00 mask $FFFE
	dc.w color,$0001
	dc.w COPPER_WAIT|$BC00,$FFFE	; copper wait v=$BC h=$00 mask $FFFE
	dc.w color,$0001
	dc.w COPPER_WAIT|$BE00,$FFFE	; copper wait v=$BE h=$00 mask $FFFE
	dc.w color,$0000
	dc.w COPPER_WAIT|$FFDE,$FFFE	; copper wait v=$FF h=$DE mask $FFFE
	dc.w color+$08,$0444
	dc.w color+$0E,$0445
	dc.w COPPER_WAIT|$2B00,$FFFE	; copper wait v=$2B h=$00 mask $FFFE
	dc.w bplcon0,COLORON
	dc.w $FFFF,$FFFE
abs_0_000403D6:
	dc.b $13,$88
abs_0_000403D8:
	dc.w $0000
	dc.b "RV (20-07-1988)",$00
	dc.b $41,$FA,$65,$72,$20,$6F
	dcb.b $FC10,$00
