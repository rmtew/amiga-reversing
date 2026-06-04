; Memory map
;   code[$00000000-$00001D00] -> runtime[$00000400-$00002100] policy materialized
;   Absolute memory refs:
;     absolute[$00000064] refs=1 access=a
;     absolute[$0000041A] refs=1 access=a
;     absolute[$00000AA6] refs=1 access=a
;     absolute[$00000AB0] refs=2 access=a
;     absolute[$00000AB4] refs=1 access=a
;     absolute[$00002100] refs=1 access=a
;     absolute[$00005000] refs=1 access=a
;     absolute[$00010000] refs=2 access=a
;     absolute[$00017D00] refs=1 access=a
;     absolute[$0001C000] refs=4 access=a
;     absolute[$0001C0BE] refs=2 access=a
;     absolute[$0001C0CE-$0001C0D0] refs=1 access=w
;     absolute[$0001C0D8] refs=2 access=a
;     absolute[$0002B01C] refs=1 access=a
;     absolute[$0002B1D2-$0002B1D4] refs=1 access=w
;     absolute[$00056000] refs=1 access=a
;     absolute[$00060000] refs=3 access=a

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

    INCLUDE "graphics/display.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/dmabits.i"

    RSSET 0
    RS.B 90
app_005A RS.W 1
    RS.B 28
app_0078 RS.W 1
app_007A RS.W 1
app_SIZEOF EQU __RS

INTF_CLRALL	EQU	$7FFF
_custom	EQU	$DFF000
m68k_vector_privilege_violation	EQU	$20
absolute_slot_00002100	EQU	$2100
stack_top_00005000	EQU	$5000
absolute_slot_00017D00	EQU	$17D00
absolute_slot_0001C000	EQU	$1C000
absolute_slot_0001C0BE	EQU	$1C0BE
absolute_slot_0001C0D8	EQU	$1C0D8
_ciaa	EQU	$BFE001
bitmap_00010000	EQU	$10000
bitmap_00010000_hi	EQU	bitmap_00010000/$10000
bitmap_00010000_lo	EQU	bitmap_00010000-(bitmap_00010000_hi*$10000)
bitmap_00011F40	EQU	$11F40
bitmap_00011F40_hi	EQU	bitmap_00011F40/$10000
bitmap_00011F40_lo	EQU	bitmap_00011F40-(bitmap_00011F40_hi*$10000)
bitmap_00013E80	EQU	$13E80
bitmap_00013E80_hi	EQU	bitmap_00013E80/$10000
bitmap_00013E80_lo	EQU	bitmap_00013E80-(bitmap_00013E80_hi*$10000)
bitmap_00015DC0	EQU	$15DC0
bitmap_00015DC0_hi	EQU	bitmap_00015DC0/$10000
bitmap_00015DC0_lo	EQU	bitmap_00015DC0-(bitmap_00015DC0_hi*$10000)
sprite_00000B1C	EQU	$B1C
sprite_00000B1C_hi	EQU	sprite_00000B1C/$10000
sprite_00000B1C_lo	EQU	sprite_00000B1C-(sprite_00000B1C_hi*$10000)
_ciab	EQU	$BFD000
disk_buffer_00060000	EQU	$60000

    SECTION code,code
loc_0_00000000:
    ORG $400
abs_0_00000400:
	bra.b abs_0_00000412
	dc.b $60,$00,$01,$D4,$60,$00,$02,$8A,$60,$00,$02,$5A,$60,$00,$02,$8E
abs_0_00000412:
	move.w #INTF_CLRALL,_custom+intena.l
abs_0_0000041A:
	move.l #abs_0_0000041A,m68k_vector_privilege_violation.l
	move #$2700,sr
	move.l #abs_0_00000AB0,_custom+cop1lc.l	; copper_list pointer
	clr.w _custom+copjmp1.l
	move.w #COLORON,_custom+bplcon0.l
	lea.l absolute_slot_00002100.l,a0
	move.l #$1FCE6,d0
	moveq.l #0,d1
abs_0_0000044E:
	move.l d1,(a0)+
	dbf.w d0,abs_0_0000044E
	lea.l stack_top_00005000.l,a7
	lea.l $00000064.l,a0
	move.l #abs_0_00000AA6,d0
	moveq.l #6,d1
abs_0_00000468:
	move.l d0,(a0)+
	dbf.w d1,abs_0_00000468
	move #$2000,sr
	move.w #$4445,abs_0_00000866.l
	move.w #$4445,abs_0_000008B8.l
	lea.l $00010000.l,a4	; bitmap memory plane 0 base $00010000
	moveq.l #3,d0
	jsr abs_0_00002040.l
	move.w #$2C81,_custom+diwstrt.l	; display window start v=$2C h=$81
	move.w #$F4C1,_custom+diwstop.l	; display window stop v=$F4 h=$C1
	move.w #$38,_custom+ddfstrt.l	; display fetch start $38
	move.w #$D0,_custom+ddfstop.l	; display fetch stop $D0
	clr.l _custom+bpl1mod.l
	lea.l absolute_slot_00017D00.l,a0
	lea.l _custom+color.l,a1
	moveq.l #7,d0
abs_0_000004C4:
	move.l (a0)+,(a1)+
	dbf.w d0,abs_0_000004C4
	move.w #DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER,_custom+dmacon.l
	move.l #abs_0_00000AB4,_custom+cop1lc.l	; copper_list pointer
	clr.w _custom+copjmp1.l
	move.w #$4489,abs_0_00000866.l
	move.w #$4489,abs_0_000008B8.l
	moveq.l #0,d0
	lea.l absolute_slot_0001C000.l,a4
	jsr abs_0_0000205A.l
	move.w #$4E75,$0001C0CE.l
	lea.l absolute_slot_0001C0BE.l,a0
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	lea.l absolute_slot_0001C0D8.l,a0
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	jsr $0001C000.l
	move.w #$4E75,$0002B1D2.l
	lea.l _custom+color.l,a0
	moveq.l #15,d0
abs_0_00000542:
	clr.w (a0)+
	dbf.w d0,abs_0_00000542
	jsr $0002B01C.l
	move.l #abs_0_00000AB0,_custom+cop1lc.l	; copper_list pointer
	clr.w _custom+copjmp1.l
	move.w #COLORON,_custom+bplcon0.l
	move.w #INTF_CLRALL,_custom+intena.l
	move.w #INTF_CLRALL,_custom+intreq.l
	move #$2000,sr
	lea.l $00010000.l,a0	; bitmap memory plane 0 base $00010000
	move.w #$1F47,d0
abs_0_00000584:
	clr.l (a0)+
	dbf.w d0,abs_0_00000584
	moveq.l #1,d0
	lea.l absolute_slot_0001C000.l,a4
	jsr abs_0_00002074.l
	lea.l absolute_slot_0001C0BE.l,a0
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	lea.l absolute_slot_0001C0D8.l,a0
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	move.w #$4E71,(a0)+
	move.b #CIAICRF_SETCLR|CIAICRF_SP,_ciaa+ciaicr.l
	jsr $0001C000.l
	jmp $00056000.l
	dcb.b $8,$00
	dc.b $20,$4C,$33,$FC,$82,$10,$00,$DF,$F0,$96,$23,$C0,$00,$00,$05,$D0
	dc.b $23,$C8,$00,$00,$05,$D4,$61,$00,$03,$C8,$61,$00,$03,$DE,$61,$00
	dc.b $04,$3E,$20,$39,$00,$00,$05,$D0,$20,$79,$00,$00,$05,$D4,$02,$80
	dc.b $00,$00,$00,$FF,$E7,$88,$43,$F9,$00,$00,$0B,$46,$2A,$31,$08,$00
	dc.b $23,$C5,$00,$02,$FF,$FC,$26,$48,$72,$00,$12,$31,$08,$04,$33,$C1
	dc.b $00,$00,$0B,$26,$4A,$31,$08,$05,$67,$00,$00,$16,$08,$B9,$00,$02
	dc.b $00,$BF,$D1,$00,$33,$FC,$00,$01,$00,$00,$0B,$24,$60,$00,$00,$10
	dc.b $08,$F9,$00,$02,$00,$BF,$D1,$00,$42,$79,$00,$00,$0B,$24,$33,$F1
	dc.b $08,$06,$00,$00,$0B,$38,$61,$00,$01,$82,$60,$00,$03,$7A,$33,$FC
	dc.b $7F,$FF,$00,$DF,$F0,$9A,$33,$FC,$7F,$FF,$00,$DF,$F0,$96,$33,$FC
	dc.b $82,$10,$00,$DF,$F0,$96,$41,$F9,$00,$03,$00,$00,$74,$00,$22,$3C
	dc.b $00,$00,$00,$01,$20,$3C,$00,$00,$9C,$80,$33,$C1,$00,$00,$0B,$2C
	dc.b $33,$C2,$00,$00,$0B,$24,$23,$C0,$00,$00,$0B,$2E,$24,$48,$61,$00
	dc.b $03,$10,$61,$00,$03,$26,$61,$00,$03,$86,$4A,$79,$00,$00,$0B,$24
	dc.b $67,$00,$00,$0E,$08,$B9,$00,$02,$00,$BF,$D1,$00,$60,$00,$00,$0A
	dc.b $08,$F9,$00,$02,$00,$BF,$D1,$00,$30,$39,$00,$00,$0B,$2C,$33,$FC
	dc.b $40,$00,$00,$DF,$F0,$24,$61,$00,$03,$8A,$61,$00,$00,$86,$33,$FC
	dc.b $77,$00,$00,$DF,$F0,$9E,$33,$FC,$82,$10,$00,$DF,$F0,$96,$33,$FC
	dc.b $91,$00,$00,$DF,$F0,$9E,$23,$FC,$00,$00,$0B,$66,$00,$DF,$F0,$20
	dc.b $33,$FC,$DF,$FF,$00,$DF,$F0,$24,$33,$FC,$DF,$FF,$00,$DF,$F0,$24
	dc.b $08,$39,$00,$01,$00,$DF,$F0,$1F,$67,$F6,$33,$FC,$40,$00,$00,$DF
	dc.b $F0,$24,$33,$FC,$7F,$FF,$00,$DF,$F0,$9C,$06,$79,$00,$01,$00,$00
	dc.b $0B,$24,$0C,$79,$00,$02,$00,$00,$0B,$24,$66,$00,$00,$10,$42,$79
	dc.b $00,$00,$0B,$24,$06,$79,$00,$01,$00,$00,$0B,$2C,$04,$B9,$00,$00
	dc.b $14,$00,$00,$00,$0B,$2E,$67,$00,$02,$7E,$6A,$00,$FF,$4E,$60,$00
	dc.b $02,$76,$30,$3C,$1F,$FF,$41,$F9,$00,$00,$0B,$66,$20,$FC,$AA,$AA
	dc.b $AA,$AA,$51,$C8,$FF,$F8,$78,$00,$36,$3C,$04,$FF,$41,$F9,$00,$00
	dc.b $21,$66,$30,$FC,$44,$89,$30,$FC,$2A,$AA,$20,$12,$D8,$80,$E2,$88
	dc.b $61,$00,$00,$1C,$20,$1A,$61,$00,$00,$16,$51,$CB,$FF,$EE,$20,$04
	dc.b $E2,$88,$61,$00,$00,$0A,$20,$04,$61,$00,$00,$04,$70,$00,$02,$80
	dc.b $55,$55,$55,$55,$24,$00,$0A,$82,$55,$55,$55,$55,$22,$02,$E3,$8A
	dc.b $E2,$89,$08,$C1,$00,$1F,$C2,$82,$80,$81,$08,$28,$00,$00,$FF,$FF
	dc.b $67,$04,$08,$80,$00,$1F,$20,$C0,$4E,$75,$4A,$85,$67,$00,$00,$42
	dc.b $6B,$00,$00,$3E,$61,$48,$06,$79,$00,$01,$00,$00,$0B,$24,$0C,$79
	dc.b $00,$02,$00,$00,$0B,$24,$65,$00,$00,$1C,$42,$79,$00,$00,$0B,$24
	dc.b $06,$79,$00,$01,$00,$00,$0B,$26,$08,$F9,$00,$02,$00,$BF,$D1,$00
	dc.b $60,$00,$FF,$C8,$08,$B9,$00,$02,$00,$BF,$D1,$00,$60,$00,$FF,$BC
	dc.b $4E,$75,$52,$79,$00,$00,$0B,$26,$4A,$85,$66,$AE,$4E,$75,$42,$79
	dc.b $00,$00,$0B,$32,$23,$C5,$00,$00,$0B,$34,$33,$F9,$00,$00,$0B,$38
	dc.b $00,$00,$0B,$3A,$30,$39,$00,$00,$0B,$26,$61,$00,$02,$16,$33,$FC
	dc.b $77,$FF,$00,$DF,$F0,$9E,$42,$79,$00,$DF,$F0,$24,$33,$FC
abs_0_00000866:
	dc.b $44,$89,$00,$DF,$F0,$7E,$33,$FC,$95,$00,$00,$DF,$F0,$9E,$23,$FC
	dc.b $00,$00,$0B,$66,$00,$DF,$F0,$20,$33,$FC,$94,$10,$00,$DF,$F0,$24
	dc.b $33,$FC,$94,$10,$00,$DF,$F0,$24,$52,$B9,$00,$00,$0B,$3C,$08,$39
	dc.b $00,$01,$00,$DF,$F0,$1F,$67,$F0,$33,$FC,$00,$02,$00,$DF,$F0,$9C
	dc.b $33,$FC,$40,$00,$00,$DF,$F0,$24,$43,$F9,$00,$00,$0B,$64,$54,$89
	dc.b $0C,$51
abs_0_000008B8:
	dc.b $44,$89,$67,$F8,$0C,$51,$2A,$AA,$66,$00,$FF,$7A,$54,$89,$3E,$3C
	dc.b $04,$FF,$76,$00,$20,$19,$02,$80,$55,$55,$55,$55,$E3,$80,$22,$19
	dc.b $02,$81,$55,$55,$55,$55,$80,$81,$D6,$80,$4A,$85,$67,$78,$23,$C0
	dc.b $00,$00,$0B,$40,$4A,$79,$00,$00,$0B,$38,$67,$00,$00,$44,$0C,$79
	dc.b $00,$04,$00,$00,$0B,$38,$65,$00,$00,$0C,$59,$79,$00,$00,$0B,$38
	dc.b $60,$00,$00,$54,$33,$F9,$00,$00,$0B,$38,$00,$00,$0B,$44,$42,$79
	dc.b $00,$00,$0B,$38,$0C,$79,$00,$01,$00,$00,$0B,$44,$67,$00,$00,$1C
	dc.b $0C,$79,$00,$02,$00,$00,$0B,$44,$67,$00,$00,$1A,$60,$00,$00,$20
	dc.b $16,$F9,$00,$00,$0B,$40,$53,$85,$67,$1C,$16,$F9,$00,$00,$0B,$41
	dc.b $53,$85,$67,$12,$16,$F9,$00,$00,$0B,$42,$53,$85,$67,$08,$16,$F9
	dc.b $00,$00,$0B,$43,$53,$85,$51,$CF,$FF,$6C,$20,$19,$02,$80,$55,$55
	dc.b $55,$55,$E3,$80,$22,$19,$02,$81,$55,$55,$55,$55,$80,$81,$B6,$00
	dc.b $66,$02,$4E,$75,$0C,$79,$00,$4E,$00,$00,$0B,$26,$64,$00,$FF,$F4
	dc.b $2A,$39,$00,$00,$0B,$34,$33,$F9,$00,$00,$0B,$3A,$00,$00,$0B,$38
	dc.b $97,$FC,$00,$00,$14,$00,$52,$79,$00,$00,$0B,$32,$0C,$79,$00,$03
	dc.b $00,$00,$0B,$32,$66,$00,$FE,$8E,$61,$00,$00,$84,$60,$00,$FE,$80
	dc.b $00,$39,$00,$78,$00,$BF,$D1,$00,$02,$39,$00,$7F,$00,$BF,$D1,$00
	dc.b $02,$39,$00,$F7,$00,$BF,$D1,$00,$4E,$75,$08,$39,$00,$05,$00,$BF
	dc.b $E0,$01,$66,$F6,$4E,$75,$00,$39,$00,$78,$00,$BF,$D1,$00,$00,$39
	dc.b $00,$80,$00,$BF,$D1,$00,$02,$39,$00,$F7,$00,$BF,$D1,$00,$00,$39
	dc.b $00,$08,$00,$BF,$D1,$00,$33,$FC,$00,$10,$00,$DF,$F0,$96,$4E,$75
	dc.b $02,$39,$00,$FD,$00,$BF,$D1,$00,$60,$08,$00,$39,$00,$02,$00,$BF
	dc.b $D1,$00,$02,$39,$00,$FE,$00,$BF,$D1,$00,$4E,$71,$00,$39,$00,$01
	dc.b $00,$BF,$D1,$00,$30,$3C,$07,$D0,$51,$C8,$FF,$FE,$4E,$75,$02,$39
	dc.b $00,$10,$00,$BF,$E0,$01,$66,$0A,$72,$05,$61,$00,$FF,$C4,$51,$C9
	dc.b $FF,$FA,$61,$00,$FF,$C6,$02,$39,$00,$10,$00,$BF,$E0,$01,$66,$F2
	dc.b $33,$FC,$00,$00,$00,$00,$0B,$2A,$30,$3C,$4E,$20,$51,$C8,$FF,$FE
	dc.b $4E,$75,$33,$C0,$00,$00,$0B,$28,$90,$79,$00,$00,$0B,$2A,$67,$2C
	dc.b $6A,$0C,$44,$40,$00,$39,$00,$02,$00,$BF,$D1,$00,$60,$08,$02,$39
	dc.b $00,$FD,$00,$BF,$D1,$00,$32,$00,$53,$41,$61,$00,$FF,$86,$51,$C9
	dc.b $FF,$FA,$33,$F9,$00,$00,$0B,$28,$00,$00,$0B,$2A,$4E,$75
abs_0_00000AA6:
	move.w #INTF_CLRALL,_custom+intreq.l
	rte
abs_0_00000AB0:
	dc.w $FFFF,$FFFE
abs_0_00000AB4:
    ; display layout 4 bitmap planes $00010000..$00015DC0 step $1F40
	dc.w bplcon0,(4<<PLNCNTSHFT)|COLORON	; display 4 bitplanes lores color
	dc.w bplpt,bitmap_00010000_hi	; bitmap pointer $00010000
	dc.w bplpt+$02,bitmap_00010000_lo
	dc.w bplpt+$04,bitmap_00011F40_hi	; bitmap pointer $00011F40
	dc.w bplpt+$06,bitmap_00011F40_lo
	dc.w bplpt+$08,bitmap_00013E80_hi	; bitmap pointer $00013E80
	dc.w bplpt+$0A,bitmap_00013E80_lo
	dc.w bplpt+$0C,bitmap_00015DC0_hi	; bitmap pointer $00015DC0
	dc.w bplpt+$0E,bitmap_00015DC0_lo
	dc.w sprpt,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$02,sprite_00000B1C_lo
	dc.w sprpt+$04,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$06,sprite_00000B1C_lo
	dc.w sprpt+$08,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$0A,sprite_00000B1C_lo
	dc.w sprpt+$0C,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$0E,sprite_00000B1C_lo
	dc.w sprpt+$10,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$12,sprite_00000B1C_lo
	dc.w sprpt+$14,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$16,sprite_00000B1C_lo
	dc.w sprpt+$18,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$1A,sprite_00000B1C_lo
	dc.w sprpt+$1C,sprite_00000B1C_hi	; sprite pointer $00000B1C
	dc.w sprpt+$1E,sprite_00000B1C_lo
	dc.w $FFFF,$FFFE
	dcb.b $2B,$00
	dc.b $03,$82,$DC,$28,$00,$00,$00,$00,$01,$27,$6C,$3F,$00,$00,$00,$00
	dc.b $00,$4E,$20,$4E,$00,$00,$00,$00,$00,$7D,$20,$14
	dcb.b $1FD,$00
abs_0_00000D60:
	movem.l d2-d3/a0-a1,-(a7)
	move.w d0,abs_0_0000101C.l
	move.l d0,d3
	move.l a0,abs_0_00001014.l
	move.l a1,abs_0_00001018.l
	clr.l abs_0_0000101E.l
	lea.l abs_0_00001022(pc),a0
	move.l #$370,d0
	bsr.w abs_0_00000E7C
	movea.l abs_0_00001014(pc),a0
	moveq.l #0,d0
	move.w d3,d1
	subq.w #1,d1
abs_0_00000D96:
	mulu.w #$D,d3
	move.b (a0)+,d0
	bsr.w abs_0_00000E6A
	add.l d0,d3
	andi.l #2047,d3
	dbf.w d1,abs_0_00000D96
	divu.w #$48,d3
	clr.w d3
	swap.w d3
	addq.w #6,d3
	lsl.w #2,d3
abs_0_00000DB8:
	lea.l abs_0_00001022(pc),a0
	move.l $0(a0,d3.w),d0
	tst.l d0
	beq.w abs_0_00000E60
	bsr.w abs_0_00000E7C
	cmpi.l #2,(a0)
	bne.w abs_0_00000E60
	move.w abs_0_0000101C(pc),d1
	movea.l abs_0_00001014(pc),a1
	adda.w #$1B0,a0
	cmp.b (a0)+,d1
	bne.b abs_0_00000DFE
	subq.w #1,d1
abs_0_00000DE6:
	move.b (a0)+,d0
	bsr.w abs_0_00000E6A
	move.b d0,d2
	move.b (a1)+,d0
	bsr.w abs_0_00000E6A
	cmp.b d0,d2
	bne.b abs_0_00000DFE
	dbf.w d1,abs_0_00000DE6
	bra.b abs_0_00000E04
abs_0_00000DFE:
	move.w #$1F0,d3
	bra.b abs_0_00000DB8
abs_0_00000E04:
	lea.l abs_0_00001022(pc),a0
	cmpi.l #4294967293,$01FC(a0)
	bne.b abs_0_00000E60
	movea.l abs_0_00001018(pc),a1
abs_0_00000E16:
	move.l $0010(a0),d0
	beq.b abs_0_00000E44
	bsr.w abs_0_00000E7C
	cmpi.l #8,(a0)
	bne.b abs_0_00000E60
	move.l $000C(a0),d0
	add.l d0,abs_0_0000101E.l
	adda.w #$18,a0
	subq.l #1,d0
abs_0_00000E38:
	move.b (a0)+,(a1)+
	dbf.w d0,abs_0_00000E38
	lea.l abs_0_00001022(pc),a0
	bra.b abs_0_00000E16
abs_0_00000E44:
	moveq.l #0,d0
abs_0_00000E46:
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKSTEP,_ciab+ciaprb.l
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSIDE|CIAF_DSKSTEP,_ciab+ciaprb.l
	move.l abs_0_0000101E(pc),d1
	movem.l (a7)+,d2-d3/a0-a1
	rts
abs_0_00000E60:
	moveq.l #-1,d0
	move.b d0,abs_0_00001012.l
	bra.b abs_0_00000E46
abs_0_00000E6A:
	cmpi.b #97,d0
	bcs.b abs_0_00000E7A
	cmpi.b #122,d0
	bhi.b abs_0_00000E7A
	subi.w #32,d0
abs_0_00000E7A:
	rts
abs_0_00000E7C:
	movem.l d0-d7/a0-a6,-(a7)
	lea.l abs_0_00000FE6(pc),a2
	lea.l abs_0_00001012(pc),a1
	divu.w #$B,d0
	cmp.b (a1),d0
	beq.w abs_0_00000FA6
	lea.l _custom+dsklen.l,a6
	move.w #$4489,app_005A(a6)
	move.w #$7F00,app_007A(a6)
	move.w #$9500,app_007A(a6)
	move.l #$55555555,d2
	lea.l _ciab+ciaprb.l,a5
	lea.l $0F01(a5),a4
abs_0_00000EBA:
	move.b #$7D,(a5)
	move.b #$75,(a5)
	cmpi.b #255,(a1)
	bne.b abs_0_00000ED6
abs_0_00000EC8:
	btst.b #4,(a4)
	beq.b abs_0_00000ED4
	bsr.w abs_0_00000FCA
	bra.b abs_0_00000EC8
abs_0_00000ED4:
	clr.b (a1)
abs_0_00000ED6:
	move.l d0,d1
	bclr #0,d1
	bclr.b #0,(a1)
	cmp.b (a1),d1
	beq.b abs_0_00000EF6
	bcs.b abs_0_00000EEE
	bsr.w abs_0_00000FD0
	addq.b #2,(a1)
	bra.b abs_0_00000ED6
abs_0_00000EEE:
	bsr.w abs_0_00000FCA
	subq.b #2,(a1)
	bra.b abs_0_00000ED6
abs_0_00000EF6:
	btst #0,d0
	beq.b abs_0_00000F02
	addq.b #1,(a1)
	bclr.b #2,(a5)
abs_0_00000F02:
	moveq.l #11,d3
abs_0_00000F04:
	btst.b #5,(a4)
	bne.b abs_0_00000F04
	move.w #$4000,(a6)
	move.w #$8210,$0072(a6)
	lea.l disk_buffer_00060000.l,a3
	move.l a3,-$0004(a6)
	clr.l $0440(a3)
	move.w #$1002,app_0078(a6)
	move.w #$9960,(a6)
	move.w #$9960,(a6)
abs_0_00000F30:
	tst.l $0440(a3)
	beq.b abs_0_00000F30
abs_0_00000F36:
	cmpi.w #17545,(a3)
	bne.b abs_0_00000F40
	addq.l #2,a3
	bra.b abs_0_00000F36
abs_0_00000F40:
	bsr.w abs_0_00000FBC
	move.l d5,d4
	swap.w d4
	cmp.b (a1),d4
	beq.b abs_0_00000F52
	st.b (a1)
abs_0_00000F4E:
	bra.w abs_0_00000EBA
abs_0_00000F52:
	lsr.w #8,d5
	lsl.w #2,d5
	move.w d5,d6
	cmpi.w #44,d6
	bcc.b abs_0_00000F4E
	adda.w #$28,a3
	bsr.b abs_0_00000FBC
	move.l d5,d1
	move.l a3,$0(a2,d6.w)
	moveq.l #0,d7
	moveq.l #127,d4
abs_0_00000F6E:
	move.l (a3),d5
	move.l $0200(a3),d6
	eor.l d5,d7
	eor.l d6,d7
	and.l d2,d5
	and.l d2,d6
	lsl.l #1,d5
	or.l d5,d6
	move.l d6,(a3)+
	dbf.w d4,abs_0_00000F6E
	and.l d2,d7
	cmp.l d7,d1
	bne.b abs_0_00000F4E
	adda.w #$200,a3
abs_0_00000F90:
	btst.b #1,-$0005(a6)
	beq.b abs_0_00000F90
	subq.b #1,d3
	beq.b abs_0_00000FA6
abs_0_00000F9C:
	cmpi.w #17545,(a3)+
	bne.b abs_0_00000F9C
	bra.w abs_0_00000F36
abs_0_00000FA6:
	swap.w d0
	lsl.w #2,d0
	movea.l $0(a2,d0.w),a2
	moveq.l #127,d0
abs_0_00000FB0:
	move.l (a2)+,(a0)+
	dbf.w d0,abs_0_00000FB0
	movem.l (a7)+,d0-d7/a0-a6
	rts
abs_0_00000FBC:
	move.l (a3)+,d4
	move.l (a3)+,d5
	and.l d2,d4
	and.l d2,d5
	lsl.l #1,d4
	or.l d4,d5
	rts
abs_0_00000FCA:
	bset.b #1,(a5)
	bra.b abs_0_00000FD4
abs_0_00000FD0:
	bclr.b #1,(a5)
abs_0_00000FD4:
	bclr.b #0,(a5)
	bset.b #0,(a5)
	move.w #$A00,d3
abs_0_00000FE0:
	dbf.w d3,abs_0_00000FE0
	rts
abs_0_00000FE6:
	dcb.b $2C,$00
abs_0_00001012:
	dc.b $FF,$00
abs_0_00001014:
	dc.l $00000000	; lookup_table
abs_0_00001018:
	dc.l $00000000	; lookup_table
abs_0_0000101C:
	dc.w $0000	; lookup_table
abs_0_0000101E:
	dc.l $00000000	; lookup_table
abs_0_00001022:
	dc.b "ve),sAdr,(i=index),sync,length,strk,(anztrk) -> raw trackread            *> (drive),sAdr,(i=index),length,strk,(anztrk) -> raw trackwrite                x -> exit                                                                       --------------------------------------------------------------------------------.                                                                               ap               *p mod b/f/m/k -> bootbl",$00
	dc.b $00,$00,$00,$00,$00,$02,$1C,$00,$00,$02,$57,$00,$08,$29,$55,$00
	dc.b $00,$00,$02,$00,$00,$00,$00,$00,$00,$03,$FB,$00,$00,$04,$7D,$00
	dc.b $00,$00,$02,$00,$00,$03,$FB,$00,$00,$00,$01,$00,$00,$00,$00,$00
	dc.b $00,$06,$2F,$8A,$38,$07,$F6
	dcb.b $11E,$00
	dc.b $06,$2F
	dcb.b $F,$00
	dc.b $37
	dcb.b $5E,$00
	dc.b $0F,$4B,$00,$00,$00,$15,$00,$00,$07,$D4,$07,$61,$63,$6F,$6E,$66
	dc.b $69,$67
	dcb.b $3E,$00
	dc.b $03,$70,$00,$00,$00,$00,$FF,$FF,$FF,$FD,$00,$00,$00,$00,$00,$00
	dc.b $02,$1C
	dcb.b $16,$00
	dc.b $05,$05,$00,$00,$00,$00,$30,$00,$00,$00,$FF,$F0
	dcb.b $4F,$00
	dc.b $88
	dcb.b $F,$00
	dc.b $01,$C0,$00,$00,$00,$00,$07
	dcb.b $18,$00
	dc.b $07,$FF,$F8
	dcb.b $19,$00
	dc.b $F0,$00,$00,$00,$00,$00,$00,$01,$00,$7F,$E0,$00,$00,$00,$00,$06
	dcb.b $10,$00
	dc.b $C0,$00,$00,$00,$20,$64,$63,$2E,$62,$20,$20,$20,$20,$22,$20,$20
	dc.b $20,$20,$20,$20,$49,$6E,$73,$65,$72,$74,$20,$64,$69,$73,$6B,$20
	dc.b $23,$31,$20,$61,$6E,$64,$20,$63,$6C,$69,$63,$6B,$20,$6D,$6F,$75
	dc.b $73,$65,$20,$21,$20,$22,$0A,$63,$6F,$6E,$74,$3A,$20,$20,$20,$6D
	dc.b $6F,$76,$65,$2E,$6C,$20,$24,$34,$2C,$61,$36,$0A
	dcb.b $8,$20
	dc.b $6A,$73,$72,$20,$2D,$31,$35,$30,$28,$61,$36,$29,$0A
	dcb.b $8,$20
	dc.b $6C,$65,$61,$20,$24,$64,$66,$66,$30,$30,$30,$2C,$61,$36,$0A
	dcb.b $8,$20
	dc.b $6D,$6F,$76,$65,$20,$23,$24,$37,$66,$66,$66,$2C,$64,$30,$0A
	dcb.b $8,$20
	dc.b $6D,$6F,$76,$65,$20,$64,$30,$2C,$31,$35,$34,$28,$61,$36,$29,$0A
	dcb.b $8,$20
	dc.b $6D,$6F,$76,$65,$20,$64,$30,$2C,$31,$35,$30,$28,$61,$36,$29,$0A
	dcb.b $8,$20
	dc.b $63,$6C,$72,$2E,$6C,$20,$33,$32,$34,$28,$61,$36,$29,$0A
	dcb.b $8,$20
	dc.b $63,$6C,$72,$2E,$6C,$20,$33,$33,$32,$28,$61,$36,$29,$0A
	dcb.b $8,$20
	dc.b $6C,$65,$61,$20,$20,$24,$34,$30,$2C,$61,$37,$0A
	dcb.b $8,$20
	dc.b $62,$73,$65,$74,$20,$23,$37,$2C,$24,$62,$66,$64,$31,$30,$30,$0A
	dcb.b $8,$20
	dc.b $62,$63,$6C,$72,$20,$00,$00,$00,$00,$00,$00,$2E,$20,$00,$00,$03
	dc.b $D8
	dcb.b $12,$00
	dc.b $02,$1C,$00,$00,$04,$FF
	dcb.b $12,$00
	dc.b $05,$8D
	dcb.b $1AB,$00
	dc.b $FC,$08,$F4,$00,$00,$00,$12,$00,$20,$00,$00,$00,$20,$32,$80,$00
	dc.b $FC,$18,$26,$00,$00,$00,$04,$00,$00,$00,$05,$00,$00,$18,$46,$00
	dc.b $FC,$19,$A0
	dcb.b $A,$00
	dc.b $18,$66,$00,$00,$18,$E2,$00,$FC,$52,$32,$ED,$54,$00,$20,$29,$E8
	dc.b $00,$00,$00,$02,$00,$20,$29,$E8,$00,$05,$00,$01,$00,$01,$00,$00
	dc.b $00,$2C,$00,$00,$00,$14,$00,$20,$00,$00,$00,$00,$00,$00,$32,$60
	dc.b $00,$00,$01,$A0,$00,$05,$00,$00,$00,$00,$00,$20,$32,$88,$00,$FC
	dc.b $53,$42,$00,$00,$1D,$16,$00,$00,$00,$00,$00,$FC,$14,$AE,$00,$FC
	dc.b $14,$B4,$00,$FE,$8D,$3A,$00,$00,$00,$01,$00,$FE,$8D,$51,$00,$FE
	dc.b $8D,$40
	dcb.b $B,$00
	dc.b $0C,$00,$00,$00,$80,$00,$00,$00,$00,$00,$00,$00,$02,$00,$00,$00
	dc.b $01,$00,$00,$00,$0B,$00,$00,$00,$02
	dcb.b $F,$00
	dc.b $4F,$FF,$FF,$FF,$FF,$00,$00,$00,$00,$FF,$FF,$FF,$FF,$00,$FC,$18
	dc.b $54,$00,$FE,$86,$DE,$00,$00,$27,$01,$FF,$FE,$01,$80,$00,$00,$01
	dc.b $82,$0F,$FF,$01,$84,$07,$78,$01,$86,$0F,$E0,$01,$A0,$00,$00,$01
	dc.b $A2,$00,$0F,$01,$A4,$00,$00,$01,$A6,$00,$0C,$01,$A8,$04,$44,$01
	dc.b $AA,$05,$55,$01,$AC,$06,$66,$01,$AE,$07,$77,$01,$B0,$08,$88,$01
	dc.b $B2,$09,$99,$01,$B4,$0A,$AA,$01,$B6,$0B,$BB,$01,$B8,$0C,$CC,$01
	dc.b $BA,$0D,$DD,$01,$BC,$0E,$EE,$01,$BE,$0F,$FF,$00,$8E,$05,$81,$01
	dc.b $00,$02,$00,$01,$04,$00,$24,$00,$90,$40,$C1,$00,$92,$00,$3C,$00
	dc.b $94,$00,$D0,$01,$02,$00,$00,$01,$08,$00,$00,$01,$0A,$00,$00,$00
	dc.b $E0,$00,$00,$00,$E2,$FF,$80,$00,$E4,$00,$01,$00,$E6,$4F,$80,$28
	dc.b $01,$FF,$FE,$01,$00,$A2,$00,$FF,$DF,$FF,$FE,$28,$01,$FF,$FE,$01
	dc.b $00,$02,$00,$FF,$FF,$FF,$FE,$FF,$FF,$FF,$F6,$00,$00,$00,$00,$00
	dc.b $00,$32,$60,$00,$00,$00,$78,$00,$00,$00,$00,$00,$00,$07,$76,$66
	dc.b $66,$60,$06,$B0,$00,$06,$C3,$C1,$87,$E7,$E1,$C0,$03,$C3,$E6,$67
	dc.b $E3,$C1,$CC,$C3,$03,$80,$00,$01,$80,$63
	dcb.b $9,$00
	dc.b $06,$B6,$66,$67,$E0,$06,$B0,$00,$0F,$E0,$61,$87,$67,$63,$00,$00
	dc.b $60,$66,$00,$00,$63,$0F,$E3,$00,$09,$68,$00,$00,$00,$00,$32,$60
	dc.b $00,$00,$00,$28
	dcb.b $C,$00
	dc.b $09,$58
	dcb.b $14,$00
	dc.b $1D,$56,$00,$00,$1D,$52,$00,$00,$00,$00,$00,$00,$02,$00,$E6,$00
	dc.b $00,$00,$00,$DD
	dcb.b $B,$00
	dc.b $20,$00,$00,$00,$20,$00,$00,$00,$20,$00,$20
	dcb.b $1C,$00
	dc.b $01,$80,$00,$00,$00,$E2,$00,$00,$01,$20,$00,$00,$01,$22,$1A,$80
	dc.b $01,$24,$00,$00,$01,$26,$1A,$78,$01,$28,$00,$00,$01,$2A,$1A,$78
	dc.b $01,$2C,$00,$00,$01,$2E,$1A,$78,$01,$30,$00,$00,$01,$32,$1A,$78
	dc.b $01,$34,$00,$00,$01,$36,$1A,$78,$01,$38,$00,$00,$01,$3A,$1A,$78
	dc.b $01,$3C,$00,$00,$01,$3E,$1A,$78,$0C,$01,$FF,$FE,$00,$8A,$00,$00
	dc.b $FF,$FE,$FF,$FF,$FF,$FF,$FF,$FE,$FE,$00,$FF,$00,$00,$00,$00,$00
	dc.b $27,$40,$37,$00,$00,$00,$FC,$00,$7C,$00,$FE,$00,$7C,$00,$86,$00
	dc.b $78,$00,$8C,$00,$7C,$00,$86,$00,$6E,$00,$93,$00,$07,$00,$69,$80
	dc.b $03,$80,$04,$C0,$01,$C0,$02,$60,$00,$80,$01,$40,$00,$00,$00,$80
	dcb.b $1F,$00
	dc.b $C0,$00,$02,$00,$00,$00,$0F,$00,$08,$00,$01,$00,$00,$1A,$E8,$01
	dcb.b $8,$00
	dc.b $18,$FF,$F1,$FF,$E7,$FF,$CF,$FF,$9F,$0F,$3F,$C6,$7F,$E0,$FF,$F1
	dc.b $FF,$00,$00,$1A,$68,$00,$00,$1A,$C8,$00,$46,$00,$FE,$45,$BC,$00
	dc.b $FE,$00,$00,$00,$00,$00,$17,$00,$08,$00,$01,$00,$00,$1B,$20,$01
	dc.b $00,$00,$00,$00,$00,$4B,$5E,$00,$FE,$C0,$00,$06,$00,$00,$03,$C0
	dc.b $00,$00,$0F,$C0,$00,$00,$39,$C0,$00,$00,$E1,$C0,$00,$03,$FF,$C0
	dc.b $00,$1F,$83,$F0,$00,$C0,$00,$06,$00,$00,$00,$1B,$A0,$00,$00,$1B
	dc.b $28,$00,$3C,$00,$FE,$4B,$F4,$00,$FE,$4B,$DA
	dcb.b $8,$00
	dc.b $1A,$98,$00,$00,$1A,$08,$00,$00,$00,$00,$00,$1D,$00,$0A,$00,$02
	dc.b $00,$00,$1B,$78,$03,$00,$00,$00,$00,$00,$00,$00,$1A,$98,$3F,$FF
	dc.b $FF,$3C,$30,$00,$3F,$3C,$30,$00,$03,$3C,$30,$3F,$F3,$3C,$30,$3F
	dc.b $F3,$3C,$30,$3F,$F3,$3C,$30,$3F,$F3,$3C,$3F,$3F,$F3,$3C,$3F,$00
	dc.b $03,$3C,$3F,$FF,$FF,$3C,$00,$00,$00,$00,$0F,$FF,$C0,$00,$0F,$00
	dc.b $00,$00,$0F,$00,$00,$00,$0F,$00,$00,$00,$0F,$00,$00,$00,$0F
	dcb.b $F,$00
	dc.b $95,$64
	dcb.b $8,$00
	dc.b $1B,$88,$00,$00,$1C,$00,$00,$D8,$00,$FE,$B0,$7A,$00,$FE,$B0,$60
	dcb.b $8,$00
	dc.b $1C,$80,$00,$00,$00,$30,$00,$00,$00,$FE,$B4,$CA,$00,$FE,$B4,$7C
	dcb.b $8,$00
	dc.b $1B,$D0,$00,$00,$1B,$E8,$00,$00,$00,$FF,$40,$30,$00,$FF,$3E,$62
	dc.b $00,$00,$00,$00,$00,$00,$00,$FC,$00,$B6,$00,$FC,$4B,$64,$00,$FE
	dc.b $43,$DC,$00,$FE,$4B,$44,$00,$FC,$45,$74,$00,$FC,$47,$FC,$00,$FE
	dc.b $42,$D0,$00,$FE,$45,$28,$00,$FC,$53,$E4,$00,$FE,$4B,$8E,$00,$FE
	dc.b $4B,$DA,$00,$FE,$8D,$6C,$00,$FC,$35,$08,$00,$FE,$4C,$26,$00,$FE
	dc.b $09,$A4,$00,$FE,$4C,$6C,$00,$FE,$95,$64,$00,$FD,$3D,$8C,$00,$FC
	dc.b $32,$76,$00,$FE,$3D,$A4,$00,$FE,$B4,$7C,$00,$FF,$3E,$62,$00,$FE
	dc.b $B0,$60,$00,$FE,$83,$E0
	dcb.b $8,$00
	dc.b $4E,$F9,$00,$FC,$52,$F0,$4E,$F9,$00,$FC,$51,$DC,$4E,$F9,$00,$FC
	dc.b $51,$AA,$4E,$F9,$00,$FC,$51,$9E,$4E,$F9,$00,$FC,$51,$8C,$4E,$F9
	dc.b $00,$FC,$51,$7A,$4E,$F9,$00,$FC,$50,$B6,$4E,$F9,$00,$FC,$50,$44
	dc.b $4E,$F9,$00,$FC,$50,$CA,$4E,$F9,$00,$FC,$50,$9A,$4E,$F9,$00,$FC
	dc.b $4F,$F0,$4E,$F9,$00,$FC,$4F,$0E,$4E,$F9,$00,$FC,$4F,$D4,$4E,$F9
	dc.b $00,$FC,$50,$64,$4E,$F9,$00,$FC,$4E,$8A,$4E,$F9,$00,$FC,$4C,$DA
	dc.b $4E,$F9,$00,$FC,$4F,$20,$4E,$F9,$00,$FC,$4E,$F8,$4E,$F9,$00,$FC
	dc.b $4F,$BC,$4E,$F9,$00,$FC,$4E,$E0,$4E,$F9,$00,$FC,$50,$28,$4E,$F9
	dc.b $00,$FC,$4C,$70,$4E,$F9,$00,$FC,$4C,$70,$4E,$F9,$00,$FC,$4C,$6C
	dc.b $4E,$F9,$00,$FC,$4C,$64,$00,$20,$05,$5E,$00,$00,$06,$76,$08,$00
	dc.b $00,$FC,$4B,$B0,$04,$00,$00,$96,$01,$C8,$00,$22,$00,$01,$00,$FC
	dc.b $4B,$7E,$95,$8B,$00,$00,$00,$01,$00,$00,$00,$00,$06,$76,$00,$00
	dc.b $00,$00,$00,$00,$19,$D8
	dcb.b $E,$00
	dc.b $19,$D8,$00,$00,$00,$00,$00,$00,$19,$D8,$00,$00,$00,$00,$1D,$64
	dc.b $00,$00,$00,$00,$00,$00,$1D,$60
	dcb.b $42,$00
	dcb.b $60,$01
	dcb.b $49,$00
	dc.b $01,$01,$01,$01,$01,$01,$01
	dcb.b $22,$00
	dc.b $1E,$82,$00,$00,$00,$00,$00,$00,$1E,$7E
	dcb.b $10,$00
	dc.b $FF,$FF
	dcb.b $49,$00
	dc.b $07,$C9,$20
	dcb.b $118,$00
abs_0_00002000:
	dc.b $6C,$6F,$67,$6F
abs_0_00002004:
	dc.b $69,$6E,$74,$72,$6F
abs_0_00002009:
	dc.b $67,$61,$6D,$65,$20
	dcb.b $32,$00
abs_0_00002040:
	movem.l d0/a0-a1,-(a7)
abs_0_00002044:
	lea.l abs_0_00002000.w,a0
	moveq.l #4,d0
	movea.l a4,a1
	jsr abs_0_00000D60.w
	tst.l d0
	bne.b abs_0_00002044
	movem.l (a7)+,d0/a0-a1
	rts
abs_0_0000205A:
	movem.l d0/a0-a1,-(a7)
abs_0_0000205E:
	lea.l abs_0_00002004.w,a0
	moveq.l #5,d0
	movea.l a4,a1
	jsr abs_0_00000D60.w
	tst.l d0
	bne.b abs_0_0000205E
	movem.l (a7)+,d0/a0-a1
	rts
abs_0_00002074:
	movem.l d0/a0-a1,-(a7)
abs_0_00002078:
	lea.l abs_0_00002009.w,a0
	moveq.l #4,d0
	movea.l a4,a1
	jsr abs_0_00000D60.w
	tst.l d0
	bne.b abs_0_00002078
	movem.l (a7)+,d0/a0-a1
	rts
	dcb.b $72,$00
