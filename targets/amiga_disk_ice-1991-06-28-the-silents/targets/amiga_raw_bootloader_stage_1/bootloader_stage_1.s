; Memory map
;   code[$00000000-$00005400] -> runtime[$00040000-$00045400] policy materialized
;   code[$00000046-$00005400] -> runtime[$00006000-$0000B3BA] discovered_copy suppressed
;   code[$0000004A-$00005400] -> runtime[$00006004-$0000B3BA] discovered_copy suppressed
;   Absolute memory refs:
;     absolute[$00002000] refs=4 access=a
;     absolute[$000066FC] refs=3 access=a
;     absolute[$00010000] refs=6 access=a
;     absolute[$00013000] refs=1 access=a
;     absolute[$0001E000] refs=2 access=a
;     absolute[$0001F000] refs=2 access=a
;     absolute[$00020000] refs=2 access=a
;     absolute[$00033100] refs=1 access=a

; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVOForbid

    INCLUDE "exec/exec_lib.i"
    INCLUDE "graphics/copper.i"
    INCLUDE "graphics/display.i"
    INCLUDE "hardware/adkbits.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/dmabits.i"
    INCLUDE "hardware/intbits.i"

    RSSET 0
    RS.B 34
app_0022 RS.L 1
    RS.B 8
app_002E RS.L 1
    RS.B 32
app_0052 RS.W 1
app_SIZEOF EQU __RS

_custom	EQU	$DFF000
INTF_CLRALL	EQU	$7FFF
DMAF_CLRALL	EQU	$7FFF
runtime_code_00006000	EQU	$6000
m68k_vector_level_1_interrupt_autovector	EQU	$64
m68k_vector_level_3_interrupt_autovector	EQU	$6C
absolute_slot_0001F000	EQU	$1F000
absolute_slot_00020000	EQU	$20000
runtime_address_00020000	EQU	$20000
absolute_slot_00010000	EQU	$10000
absolute_slot_00013000	EQU	$13000
runtime_address_00033100	EQU	$33100
absolute_slot_0001E000	EQU	$1E000
runtime_address_0001E000	EQU	$1E000
_ciab	EQU	$BFD000
_ciaa	EQU	$BFE001
absolute_slot_00002000	EQU	$2000

    SECTION code,code
loc_0_00000000:
    ORG $40000
abs_0_00040000:
	movea.l $0004.w,a6
	jsr _LVOForbid(a6)
	lea.l _custom.l,a5
	lea.l abs_0_000402B8(pc),a2
	move.w intenar(a5),(a2)+
	move.w dmaconr(a5),(a2)+
	move.w #INTF_CLRALL,intreq(a5)
	move.w #DMAF_CLRALL,dmacon(a5)
	move.w #INTF_CLRALL,intena(a5)
	lea.l abs_0_00040046(pc),a0
	lea.l runtime_code_00006000.l,a1
	move.w #$1500,d0
abs_0_0004003A:
	move.l (a0)+,(a1)+
	dbf.w d0,abs_0_0004003A
	jmp runtime_code_00006000.l
abs_0_00040046:
	lea.l abs_0_000449C2(pc),a0
	move.l a0,d0
	moveq.l #28,d1
	moveq.l #4,d2
	lea.l abs_0_0004075A(pc),a0
abs_0_00040054:
	move.w d0,$0006(a0)
	swap.w d0
	move.w d0,$0002(a0)
	swap.w d0
	add.l d1,d0
	addq.l #8,a0
	dbf.w d2,abs_0_00040054
	lea.l abs_0_00040822(pc),a0
	lea.l abs_0_000449C2(pc),a1
	bsr.w abs_0_000402BC
	lea.l abs_0_000404FE(pc),a0
	move.l $0064.w,(a0)
	lea.l abs_0_000404DE(pc),a0
	move.l a0,m68k_vector_level_1_interrupt_autovector.w
	lea.l abs_0_000404D4(pc),a0
	move.l $006C.w,(a0)
	lea.l abs_0_000404AA(pc),a0
	move.l a0,m68k_vector_level_3_interrupt_autovector.w
	lea.l abs_0_00040742(pc),a0
	move.l a0,$0080(a5)
	move.w #$87DF,$0096(a5)
	move.w #$C012,$009A(a5)
	clr.w $0088(a5)
	lea.l abs_0_000404D8(pc),a6
	lea.l abs_0_000406C6(pc),a0
	move.l a0,d0
	lea.l abs_0_000406C2(pc),a0
	move.l d0,(a0)
	bsr.w abs_0_000403A8
	move.b #$77,d2
	moveq.l #1,d7
	bsr.w abs_0_00040504
	move.b #$73,d2
	moveq.l #1,d7
	bsr.w abs_0_00040504
	moveq.l #24,d7
	move.b #$77,d2
	lea.l absolute_slot_0001F000.l,a5
	bsr.w abs_0_0004054E
	lea.l absolute_slot_0001F000.l,a0
	lea.l absolute_slot_00020000.l,a1
	bsr.w abs_0_000402BC
	lea.l abs_0_000404D8(pc),a6
	bsr.w abs_0_0004039A
abs_0_000400FC:
	tst.w $0002(a6)
	bne.b abs_0_000400FC
	jsr runtime_address_00020000.l
	lea.l _custom.l,a5
	move.w #DMAF_SETCLR|DMAF_BLITHOG|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER|DMAF_DISK|DMAF_AUDIO,dmacon(a5)
	move.w #INTF_CLRALL,intena(a5)
	move.w #INTF_SETCLR|INTF_INTEN|INTF_COPER|INTF_DSKBLK,intena(a5)
	move.w #INTF_CLRALL,intreq(a5)
	lea.l abs_0_00040742(pc),a0
	move.l a0,cop1lc(a5)	; copper_list pointer
	clr.w copjmp1(a5)
	lea.l abs_0_000404D8(pc),a6
	lea.l abs_0_000406C6(pc),a0
	move.l a0,d0
	lea.l abs_0_000406C2(pc),a0
	move.l d0,(a0)
	bsr.w abs_0_000403A8
	moveq.l #15,d7
	lea.l absolute_slot_00010000.l,a5
	move.b #$77,d2
	bsr.w abs_0_0004054E
	lea.l absolute_slot_00010000.l,a0
	lea.l absolute_slot_00013000.l,a1
	bsr.w abs_0_000402BC
	lea.l abs_0_000404D8(pc),a6
	bsr.w abs_0_0004039A
abs_0_0004016E:
	tst.w $0002(a6)
	bne.b abs_0_0004016E
	lea.l _custom.l,a5
	move.w #INTF_CLRALL,intena(a5)
	move.w #INTF_CLRALL,intreq(a5)
	move.w #DMAF_CLRALL,dmacon(a5)
	jsr runtime_address_00033100.l
	lea.l _custom.l,a5
	move.w #DMAF_SETCLR|DMAF_BLITHOG|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER|DMAF_DISK|DMAF_AUDIO,dmacon(a5)
	move.w #INTF_CLRALL,intena(a5)
	move.w #INTF_SETCLR|INTF_INTEN|INTF_COPER|INTF_DSKBLK,intena(a5)
	move.w #INTF_CLRALL,intreq(a5)
	lea.l abs_0_00040742(pc),a0
	move.l a0,cop1lc(a5)	; copper_list pointer
	clr.w copjmp1(a5)
	lea.l abs_0_00042B8E(pc),a0
	lea.l abs_0_000449C2(pc),a1
	bsr.w abs_0_000402BC
	lea.l abs_0_000404D8(pc),a6
	lea.l abs_0_00040704(pc),a0
	move.l a0,d0
	lea.l abs_0_000406C2(pc),a0
	move.l d0,(a0)
	bsr.w abs_0_000403A8
	move.b #$77,d2
	moveq.l #42,d7
	bsr.w abs_0_00040504
	moveq.l #35,d7
	lea.l absolute_slot_00010000.l,a5
	move.b #$77,d2
	bsr.w abs_0_0004054E
	lea.l absolute_slot_00010000.l,a0
	lea.l absolute_slot_0001E000.l,a1
	bsr.w abs_0_000402BC
	move.b #$73,d2
	moveq.l #69,d7
	bsr.w abs_0_00040504
	moveq.l #5,d7
	lea.l absolute_slot_00010000.l,a5
	move.b #$73,d2
	bsr.w abs_0_0004054E
	movea.l $0004.w,a6
	lea.l absolute_slot_00010000.l,a1
	move.l a1,app_002E(a6)
	moveq.l #0,d1
	lea.l app_0022(a6),a0
	moveq.l #22,d0
abs_0_00040236:
	add.w (a0)+,d1
	dbf.w d0,abs_0_00040236
	not.w d1
	move.w d1,app_0052(a6)
	lea.l abs_0_000404D8(pc),a6
	bsr.w abs_0_0004039A
abs_0_0004024A:
	tst.w $0002(a6)
	bne.b abs_0_0004024A
	jmp runtime_address_0001E000.l
	dc.b $4B,$F9,$00,$DF,$F0,$00,$08,$2D,$00,$0E,$00,$02,$66,$F8,$08,$39
	dc.b $00,$06,$00,$BF,$E0,$01,$66,$F6,$3B,$7C,$7F,$FF,$00,$96,$3B,$7C
	dc.b $7F,$FF,$00,$9A,$41,$FA,$02,$82,$21,$D0,$00,$64,$41,$FA,$02,$50
	dc.b $21,$D0,$00,$6C,$2C,$78,$00,$04,$22,$6E,$00,$9C,$2B,$69,$00,$26
	dc.b $00,$80,$32,$3C,$80,$00,$30,$3A,$00,$1A,$80,$41,$3B,$40,$00,$9A
	dc.b $30,$3A,$00,$12,$80,$41,$3B,$40,$00,$96,$4E,$AE,$FF,$76,$70,$00
	dc.b $4E,$75
abs_0_000402B8:
	dc.b $00,$00,$00,$00
abs_0_000402BC:
	move.l (a0)+,d0
	move.l (a0)+,d1
	move.l (a0)+,d5
	movea.l a1,a2
	adda.l d0,a0
	adda.l d1,a2
	move.l -(a0),d0
	eor.l d0,d5
abs_0_000402CC:
	lsr.l #1,d0
	bne.b abs_0_000402D4
	bsr.w abs_0_00040374
abs_0_000402D4:
	bcs.b abs_0_00040312
	moveq.l #8,d1
	moveq.l #1,d3
	lsr.l #1,d0
	bne.b abs_0_000402E2
	bsr.w abs_0_00040374
abs_0_000402E2:
	bcs.b abs_0_0004033E
	moveq.l #3,d1
	clr.w d4
abs_0_000402E8:
	bsr.w abs_0_00040380
	move.w d2,d3
	add.w d4,d3
abs_0_000402F0:
	moveq.l #7,d1
abs_0_000402F2:
	lsr.l #1,d0
	bne.b abs_0_000402FA
	bsr.w abs_0_00040374
abs_0_000402FA:
	roxl.l #1,d2
	dbf.w d1,abs_0_000402F2
	move.b d2,-(a2)
	dbf.w d3,abs_0_000402F0
	bra.w abs_0_0004034C
abs_0_0004030A:
	moveq.l #8,d1
	moveq.l #8,d4
	bra.w abs_0_000402E8
abs_0_00040312:
	moveq.l #2,d1
	bsr.w abs_0_00040380
	cmpi.b #2,d2
	blt.b abs_0_00040334
	cmpi.b #3,d2
	beq.b abs_0_0004030A
	moveq.l #8,d1
	bsr.w abs_0_00040380
	move.w d2,d3
	move.w #$C,d1
	bra.w abs_0_0004033E
abs_0_00040334:
	move.w #$9,d1
	add.w d2,d1
	addq.w #2,d2
	move.w d2,d3
abs_0_0004033E:
	bsr.w abs_0_00040380
abs_0_00040342:
	subq.w #1,a2
	move.b $0(a2,d2.w),(a2)
	dbf.w d3,abs_0_00040342
abs_0_0004034C:
	nop
	nop
	nop
	cmpa.l a2,a1
	blt.w abs_0_000402CC
	tst.l d5
	bne.b abs_0_00040362
	rts
	dc.b $4E,$71,$4E,$71
abs_0_00040362:
	move.w #$FFFF,d0
abs_0_00040366:
	nop
	nop
	nop
	dbf.w d0,abs_0_00040366
	moveq.l #-1,d0
	rts
abs_0_00040374:
	move.l -(a0),d0
	eor.l d0,d5
	move #$10,ccr
	roxr.l #1,d0
	rts
abs_0_00040380:
	subq.w #1,d1
	clr.w d2
abs_0_00040384:
	lsr.l #1,d0
	bne.b abs_0_00040392
	move.l -(a0),d0
	eor.l d0,d5
	move #$10,ccr
	roxr.l #1,d0
abs_0_00040392:
	roxl.l #1,d2
	dbf.w d1,abs_0_00040384
	rts
abs_0_0004039A:
	move.w #$1,$0002(a6)
	move.w #$5,$0004(a6)
	rts
abs_0_000403A8:
	move.w #$1,$0000(a6)
	move.w #$5,$0004(a6)
	rts
abs_0_000403B6:
	tst.w $0004(a6)
	beq.b abs_0_000403C4
	subq.w #1,$0004(a6)
	bra.w abs_0_000404C2
abs_0_000403C4:
	move.w #$5,$0004(a6)
	lea.l abs_0_000407A0(pc),a2
	movea.l abs_0_000406C2(pc),a3
	moveq.l #0,d6
	moveq.l #30,d1
abs_0_000403D6:
	move.w (a3)+,d0
	move.w (a2),d5
	move.w d5,d3
	move.w d0,d4
	andi.w #15,d4
	andi.w #15,d5
	cmp.w d4,d5
	beq.b abs_0_000403EE
	addq.w #1,d3
	subq.w #1,d6
abs_0_000403EE:
	move.w (a2),d5
	move.w d0,d4
	andi.w #240,d4
	andi.w #240,d5
	cmp.w d4,d5
	beq.b abs_0_00040404
	addi.w #16,d3
	subq.w #1,d6
abs_0_00040404:
	move.w (a2),d5
	move.w d0,d4
	andi.w #3840,d4
	andi.w #3840,d5
	cmp.w d4,d5
	beq.b abs_0_0004041A
	addi.w #256,d3
	subq.w #1,d6
abs_0_0004041A:
	move.w d3,(a2)
	addq.l #4,a2
	dbf.w d1,abs_0_000403D6
	tst.w d6
	beq.b abs_0_0004042A
	bra.w abs_0_000404C2
abs_0_0004042A:
	clr.w $0000(a6)
	bra.w abs_0_000404C2
abs_0_00040432:
	tst.w $0004(a6)
	beq.b abs_0_00040440
	subq.w #1,$0004(a6)
	bra.w abs_0_000404C2
abs_0_00040440:
	move.w #$5,$0004(a6)
	moveq.l #0,d6
	lea.l abs_0_000407A0(pc),a2
	moveq.l #0,d0
	moveq.l #30,d1
abs_0_00040450:
	move.w (a2),d5
	move.w d5,d3
	move.w d0,d4
	andi.w #15,d4
	andi.w #15,d5
	cmp.w d4,d5
	beq.b abs_0_00040466
	subq.w #1,d3
	subq.w #1,d6
abs_0_00040466:
	move.w (a2),d5
	move.w d0,d4
	andi.w #240,d4
	andi.w #240,d5
	cmp.w d4,d5
	beq.b abs_0_0004047C
	subi.w #16,d3
	subq.w #1,d6
abs_0_0004047C:
	move.w (a2),d5
	move.w d0,d4
	andi.w #3840,d4
	andi.w #3840,d5
	cmp.w d4,d5
	beq.b abs_0_00040492
	subi.w #256,d3
	subq.w #1,d6
abs_0_00040492:
	move.w d3,(a2)
	addq.l #4,a2
	dbf.w d1,abs_0_00040450
	tst.w d6
	beq.b abs_0_000404A2
	bra.w abs_0_000404C2
abs_0_000404A2:
	clr.w $0002(a6)
	bra.w abs_0_000404C2
abs_0_000404AA:
	movem.l d0-d7/a0-a6,-(a7)
	lea.l abs_0_000404D8(pc),a6
	tst.w $0002(a6)
	bne.w abs_0_00040432
	tst.w $0000(a6)
	bne.w abs_0_000403B6
abs_0_000404C2:
	lea.l _custom.l,a5
	move.w #INTF_COPER,intreq(a5)
	movem.l (a7)+,d0-d7/a0-a6
	rte
abs_0_000404D4:
	dc.b $00,$00,$00,$00
abs_0_000404D8:
	dc.b $00,$00,$00,$00,$00,$00
abs_0_000404DE:
	move.l a5,-(a7)
	lea.l _custom.l,a5
	move.w #$4000,dsklen(a5)
	move.w #INTF_DSKBLK,intreq(a5)
	lea.l abs_0_00040502(pc),a5
	move.w #$1,(a5)
	movea.l (a7)+,a5
	rte
abs_0_000404FE:
	dc.b $00,$00,$00,$00
abs_0_00040502:
	dc.w $0000
abs_0_00040504:
	lea.l _ciab.l,a4
	move.l #$55555555,d5
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	move.b #CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	move.b d2,ciaprb(a4)
abs_0_00040520:
	btst.b #5,$1001(a4)
	bne.b abs_0_00040520
abs_0_00040528:
	btst.b #4,$1001(a4)
	beq.b abs_0_00040534
	bsr.b abs_0_0004059A
	bra.b abs_0_00040528
abs_0_00040534:
	bsr.b abs_0_000405A2
	dbf.w d7,abs_0_00040534
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	move.b #CIAF_DSKMOTOR|CIAF_DSKSTEP,ciaprb(a4)
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	rts
abs_0_0004054E:
	lea.l _custom.l,a6
	lea.l _ciab.l,a4
	move.l #$55555555,d5
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	move.b #CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	move.b d2,ciaprb(a4)
abs_0_00040570:
	btst.b #5,$1001(a4)
	bne.b abs_0_00040570
abs_0_00040578:
	bsr.w abs_0_00040636
	bsr.b abs_0_000405A2
	dbf.w d7,abs_0_00040578
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	move.b #CIAF_DSKMOTOR|CIAF_DSKSTEP,ciaprb(a4)
	move.b #CIAF_DSKMOTOR|CIAF_DSKSEL3|CIAF_DSKSEL2|CIAF_DSKSEL1|CIAF_DSKSEL0|CIAF_DSKSIDE|CIAF_DSKDIREC|CIAF_DSKSTEP,ciaprb(a4)
	rts
abs_0_00040596:
	dc.l $00000000	; lookup_table
abs_0_0004059A:
	bset.b #CIAB_DSKDIREC,ciaprb(a4)
	bra.b abs_0_000405A8
abs_0_000405A2:
	bclr.b #CIAB_DSKDIREC,ciaprb(a4)
abs_0_000405A8:
	lea.l _ciaa+ciatodhi.l,a1
	move.l #$100,d1
	moveq.l #0,d0
	moveq.l #2,d2
abs_0_000405B8:
	move.b (a1),d0
	lsl.l #8,d0
	suba.l d1,a1
	dbf.w d2,abs_0_000405B8
	lsr.l #8,d0
	lea.l abs_0_00040596(pc),a1
	move.l d0,(a1)
	bclr.b #CIAB_DSKSTEP,ciaprb(a4)
	bset.b #CIAB_DSKSTEP,ciaprb(a4)
	nop
abs_0_000405D8:
	lea.l _ciaa+ciatodhi.l,a1
	move.l #$100,d1
	moveq.l #0,d0
	moveq.l #2,d2
abs_0_000405E8:
	move.b (a1),d0
	lsl.l #8,d0
	suba.l d1,a1
	dbf.w d2,abs_0_000405E8
	lsr.l #8,d0
	move.l abs_0_00040596(pc),d1
	cmp.l d1,d0
	beq.b abs_0_000405D8
	lea.l abs_0_00040596(pc),a1
	move.l d0,(a1)
abs_0_00040602:
	lea.l _ciaa+ciatodhi.l,a1
	move.l #$100,d1
	moveq.l #0,d0
	moveq.l #2,d2
abs_0_00040612:
	move.b (a1),d0
	lsl.l #8,d0
	suba.l d1,a1
	dbf.w d2,abs_0_00040612
	lsr.l #8,d0
	move.l abs_0_00040596(pc),d1
	cmp.l d1,d0
	beq.b abs_0_00040602
	lea.l abs_0_00040596(pc),a1
	move.l d0,(a1)
abs_0_0004062C:
	btst.b #5,$1001(a4)
	bne.b abs_0_0004062C
	rts
abs_0_00040636:
	lea.l abs_0_00040502(pc),a1
	clr.w (a1)
	move.w #$4000,dsklen(a6)
	lea.l absolute_slot_00002000.l,a0
	move.l a0,dskpt(a6)	; disk_buffer pointer $00002000
	move.w #ADKF_PRE560NS|ADKF_UARTBRK,adkcon(a6)
	move.w #ADKF_SETCLR|ADKF_MFMPREC|ADKF_WORDSYNC|ADKF_FAST,adkcon(a6)
	move.w #$4489,dsksync(a6)	; disk sync word $4489
	move.w #$9B06,dsklen(a6)	; disk DMA read 13836 bytes
	move.w #$9B06,dsklen(a6)	; disk DMA read 13836 bytes
abs_0_0004066A:
	tst.w (a1)
	beq.b abs_0_0004066A
	clr.w (a1)
	lea.l absolute_slot_00002000.l,a2
	moveq.l #10,d0
abs_0_00040678:
	cmpi.w #17545,(a2)+
	bne.b abs_0_00040678
	cmpi.w #17545,(a2)
	bne.b abs_0_00040686
	addq.l #2,a2
abs_0_00040686:
	move.l (a2)+,d1
	move.l (a2)+,d2
	and.l d5,d1
	and.l d5,d2
	asl.l #1,d1
	or.l d2,d1
	andi.l #65280,d1
	lsl.l #1,d1
	add.l a5,d1
	movea.l d1,a1
	lea.l $0030(a2),a2
	moveq.l #127,d1
abs_0_000406A4:
	move.l $0200(a2),d2
	move.l (a2)+,d3
	and.l d5,d2
	and.l d5,d3
	asl.l #1,d3
	or.l d3,d2
	move.l d2,(a1)+
	dbf.w d1,abs_0_000406A4
	dbf.w d0,abs_0_00040678
	lea.l $1600(a5),a5
	rts
abs_0_000406C2:
	dc.l $00000000	; lookup_table
abs_0_000406C6:
	dc.b $03,$00,$04,$00,$0F,$CA,$0F,$B9,$0F,$A8,$0F,$97,$0D,$86,$0C,$75
	dc.b $0B,$64,$0A,$53,$09,$42,$08,$31,$07,$20,$06,$10,$05,$10,$06,$20
	dc.b $0E,$52,$0A,$52,$0F,$CA,$03,$33,$04,$44,$05,$55,$06,$66,$07,$77
	dc.b $08,$88,$09,$99,$0A,$AA,$0C,$CC,$0D,$DD,$0E,$EE,$0F,$FF
abs_0_00040704:
	dc.b $06,$F0,$06,$F0,$06,$F0,$06,$F0,$06,$F0,$06,$F0,$06,$F0,$0E,$EF
	dc.b $0D,$DF,$0C,$CF,$0B,$BF,$0A,$AF,$08,$8C,$06,$6A,$04,$48,$04,$00
	dc.b $0F,$C9,$0F,$B8,$0F,$A7,$0F,$96,$0F,$85,$0E,$74,$0D,$63,$0C,$52
	dc.b $0B,$41,$0A,$30,$09,$20,$08,$20,$07,$10,$06,$00,$05,$00
abs_0_00040742:
	dc.w diwstrt,$2991	; display window start v=$29 h=$91
	dc.w diwstop,$29D1	; display window stop v=$29 h=$D1
	dc.w ddfstrt,$0050	; display fetch start $50
	dc.w ddfstop,$00B8	; display fetch stop $B8
	dc.w COPPER_WAIT|$6000,$FFFE	; copper wait v=$60 h=$00 mask $FFFE
	dc.w bplcon0,(5<<PLNCNTSHFT)|COLORON	; display 5 bitplanes lores color
abs_0_0004075A:
	dc.w bplpt,$0000	; bitmap pointer 0 disabled
	dc.w bplpt+$02,$0000
	dc.w bplpt+$04,$0000	; bitmap pointer 1 disabled
	dc.w bplpt+$06,$0000
	dc.w bplpt+$08,$0000	; bitmap pointer 2 disabled
	dc.w bplpt+$0A,$0000
	dc.w bplpt+$0C,$0000	; bitmap pointer 3 disabled
	dc.w bplpt+$0E,$0000
	dc.w bplpt+$10,$0000	; bitmap pointer 4 disabled
	dc.w bplpt+$12,$0000
	dc.w COPPER_WAIT|$EC00,$FFFE	; copper wait v=$EC h=$00 mask $FFFE
	dc.w bplcon0,COLORON
	dc.w bpl1mod,$0070	; bitplane modulo 112 bytes
	dc.w bpl2mod,$0070	; bitplane modulo 112 bytes
	dc.w bplcon1,$0000	; display scroll pf1=0 pf2=0
	dc.w bplcon2,$0000
	dc.w color,$0000
	dc.w $0182
abs_0_000407A0:
	dc.w $0000
	dc.w $0184
	dc.w $0000
	dc.w $0186
	dc.w $0000
	dc.w $0188
	dc.w $0000
	dc.w $018A
	dc.w $0000
	dc.w $018C
	dc.w $0000
	dc.w $018E
	dc.w $0000
	dc.w $0190
	dc.w $0000
	dc.w $0192
	dc.w $0000
	dc.w $0194
	dc.w $0000
	dc.w $0196
	dc.w $0000
	dc.w $0198
	dc.w $0000
	dc.w $019A
	dc.w $0000
	dc.w $019C
	dc.w $0000
	dc.w $019E
	dc.w $0000
	dc.w $01A0
	dc.w $0000
	dc.w $01A2
	dc.w $0000
	dc.w $01A4
	dc.w $0000
	dc.w $01A6
	dc.w $0000
	dc.w $01A8
	dc.w $0000
	dc.w $01AA
	dc.w $0000
	dc.w $01AC
	dc.w $0000
	dc.w $01AE
	dc.w $0000
	dc.w $01B0
	dc.w $0000
	dc.w $01B2
	dc.w $0000
	dc.w $01B4
	dc.w $0000
	dc.w $01B6
	dc.w $0000
	dc.w $01B8
	dc.w $0000
	dc.w $01BA
	dc.w $0000
	dc.w $01BC
	dc.w $0000
	dc.w $01BE
	dc.w $0000
	dc.w $009C
	dc.w $8010
	dc.w $FFFF
	dc.w $FFFE
abs_0_00040822:
	dc.b $00,$00,$23,$60,$00,$00,$4C,$90,$00,$E5,$38,$73,$F0,$03,$06,$81
	dc.b $5B,$03,$80,$98,$68,$16,$70,$1C,$05,$86,$7E,$03,$80,$98,$78,$18
	dc.b $10,$80,$02,$C6,$01,$D1,$DA,$0F,$83,$80,$18,$61,$01,$90,$BB,$89
	dc.b $87,$C1,$BD,$06,$BC,$A8,$7C,$05,$18,$3F,$82,$31,$46,$3E,$02,$DE
	dc.b $FF,$C2,$96,$3A,$1D,$05,$02,$FF,$0A,$58,$E8,$78,$B5,$A5,$8E,$87
	dc.b $41,$71,$82,$96,$0B,$18,$05,$07,$BF,$2D,$F9,$0E,$03,$A1,$90,$78
	dc.b $7F,$C1,$E0,$E0,$3A,$1C,$07,$DF,$F9,$DE,$0E,$03,$A1,$B0,$7E,$7D
	dc.b $E3,$E2,$00,$13,$18,$07,$C1,$F0,$27,$F8,$2D,$0E,$01,$A1,$8C,$7F
	dc.b $7C,$87,$E2,$BD,$3A,$1B,$87,$FF,$CE,$FE,$27,$E1,$A1,$80,$44,$40
	dc.b $C6,$3F,$07,$E3,$04,$33,$E0,$44,$77,$C0,$E3,$1F,$98,$CD,$A0,$86
	dc.b $60,$0C,$0E,$1B,$FF,$87,$FC,$60,$87,$00,$D0,$F7,$3F,$FD,$5F,$F1
	dc.b $96,$41,$0C,$C0,$18,$1F,$17,$FC,$17,$E1,$10,$40,$04,$63,$00,$EE
	dc.b $C1,$F9,$E3,$21,$88,$74,$3E,$13,$F0,$8F,$C6,$32,$1C,$03,$43,$F6
	dc.b $FF,$82,$C4,$72,$03,$80,$68,$7F,$3F,$FE,$3F,$E8,$E4,$31,$04,$C6
	dc.b $F7,$F0,$07,$1E,$FE,$43,$80,$68,$7F,$00,$E0,$1E,$18,$D0,$A0,$86
	dc.b $60,$0C,$0F,$F4,$07,$02,$CE,$03,$80,$A8,$61,$C5,$FF,$9F,$84,$00
	dc.b $06,$32,$C9,$1E,$00,$38,$FF,$C1,$C0,$54,$30,$0F,$C8,$10,$48,$07
	dc.b $D0,$75,$68,$86,$7E,$04,$0F,$F8,$1B,$13,$FC,$F4,$0A,$82,$A1,$A0
	dc.b $00,$C4,$AF,$E0,$5A,$68,$87,$BC,$1F,$0F,$82,$3A,$0D,$FD,$83,$EA
	dc.b $83,$81,$50,$C8,$01,$70,$20,$07,$90,$9C,$0A,$86,$C0,$07,$8A,$01
	dc.b $FD,$F5,$08,$8D,$50,$E0,$00,$62,$5F,$F0,$33,$B4,$43,$DE,$0F,$87
	dc.b $E1,$C7,$03,$89,$3F,$BA,$05,$91,$C0,$64,$38,$01,$FF,$04,$2C,$5F
	dc.b $41,$30,$38,$02,$87,$61,$FE,$1E,$00,$E1,$FC,$38,$C2,$A0,$28,$7A
	dc.b $00,$80,$BF,$DF,$FF,$04,$F1,$00,$1E,$8C,$72,$31,$3C,$5D,$3F,$96
	dc.b $1F,$A0,$2C,$70,$09,$0F,$00,$3F,$F3,$D0,$FF,$A8,$05,$87,$E0,$50
	dc.b $CE,$28,$30,$60,$0F,$E1,$B2,$14,$47,$00,$90,$F8,$3F,$FF,$FE,$8F
	dc.b $FF,$09,$C0,$28,$00,$39,$88,$3A,$34,$01,$8A,$70,$87,$A3,$A7,$F0
	dc.b $04,$00,$0E,$38,$19,$0C,$1D,$FF,$E0,$FF,$09,$3E,$93,$39,$50,$FF
	dc.b $D0,$02,$10,$3F,$B9,$E9,$0D,$04,$0E,$BE,$02,$1F,$FB,$FF,$83,$FF
	dc.b $E4,$FD,$26,$60,$81,$DD,$11,$A3,$EF,$3D,$A0,$D0,$EB,$FC,$A5,$58
	dc.b $10,$39,$80,$08,$66,$32,$A7,$F8,$88,$F8,$00,$45,$0E,$03,$21,$E4
	dc.b $C0,$90,$1D,$BB,$F8,$92,$02,$07,$30,$01,$0F,$F8,$7F,$F1,$FF,$F8
	dc.b $FC,$04,$A3,$86,$21,$A8,$C7,$0B,$B8,$38,$A9,$0B,$0D,$F6,$06,$C3
	dc.b $10,$08,$62,$00,$D0,$1E,$00,$3A,$9F,$A1,$73,$C0,$26,$54,$20,$43
	dc.b $30,$06,$80,$9A,$10,$00,$80,$74,$3F,$83,$B1,$7A,$BC,$19,$50,$10
	dc.b $3E,$C3,$F8,$40,$0F,$F8,$20,$92,$0C,$43,$51,$8E,$17,$FC,$F6,$E8
	dc.b $A8,$D3,$A4,$3D,$93,$10,$10,$C3,$A5,$0A,$90,$0D,$33,$54,$DF,$E0
	dc.b $20,$53,$87,$01,$E0,$DC,$01,$A0,$2D,$C8,$01,$00,$19,$1F,$21,$CC
	dc.b $50,$A0,$86,$A0,$0D,$01,$F2,$FF,$F7,$41,$8D,$E2,$03,$05,$92,$F0
	dc.b $77,$C0,$70,$C8,$00,$55,$20,$0F,$FC,$B9,$2A,$FE,$E6,$0F,$F0,$23
	dc.b $02,$1C,$00,$00,$44,$03,$80,$3D,$2D,$53,$B7,$84,$8A,$07,$BB,$80
	dc.b $87,$C0,$00,$29,$01,$EC,$00,$60,$01,$01,$E8,$76,$81,$CE,$A8,$21
	dc.b $D0,$00,$0E,$40,$7C,$FF,$EB,$FF,$FF,$FE,$53,$A0,$78,$A8,$F0,$6F
	dc.b $C0,$70,$D0,$00,$0B,$88,$33,$D6,$98,$6A,$99,$9D,$A3,$C1,$B0,$38
	dc.b $38,$44,$30,$64,$03,$EA,$6C,$65,$53,$FC,$48,$70,$0E,$07,$01,$0F
	dc.b $00,$04,$B1,$03,$FC,$05,$81,$85,$17,$F7,$B8,$30,$B6,$0E,$01,$C1
	dc.b $A0,$00,$99,$60,$7E,$7F,$D3,$FF,$BF,$FD,$07,$A0,$70,$E0,$08,$77
	dc.b $C1,$B0,$F0,$00,$09,$E4,$19,$EA,$D0,$14,$29,$A9,$D7,$01,$F0,$3F
	dc.b $32,$04,$30,$23,$32,$01,$E5,$7C,$FA,$F5,$B4,$5C,$F8,$0E,$18,$81
	dc.b $0E,$00,$04,$9A,$83,$F8,$01,$21,$85,$17,$CB,$78,$3A,$1E,$3A,$C1
	dc.b $F8,$50,$00,$47,$2C,$18,$C0,$A3,$C1,$23,$7F,$4F,$83,$A1,$E3,$A5
	dc.b $1F,$85,$01,$0E,$37,$D1,$66,$2B,$D8,$32,$A7,$BD,$F2,$02,$18,$41
	dc.b $C7,$03,$C1,$C7,$3C,$98,$47,$F5,$DF,$FD,$D7,$8F,$8F,$40,$73,$10
	dc.b $08,$70,$01,$EE,$6E,$18,$BF,$8C,$01,$09,$70,$6F,$81,$A3,$32,$3C
	dc.b $1C,$04,$4B,$E4,$86,$08,$2D,$F0,$0C,$4D,$F8,$1C,$18,$1A,$51,$B8
	dc.b $0E,$3A,$4F,$A6,$C8,$07,$F9,$45,$5B,$D7,$9C,$07,$2A,$08,$87,$8A
	dc.b $71,$11,$8F,$8E,$C9,$E1,$54,$F4,$F3,$06,$21,$10,$E7,$DF,$6E,$0F
	dc.b $F1,$C1,$44,$80,$60,$5F,$E0,$46,$22,$1A,$9B,$F6,$42,$0C,$47,$C4
	dc.b $02,$33,$F8,$07,$02,$21,$EF,$06,$C3,$8D,$66,$FA,$6C,$60,$00,$B8
	dc.b $44,$05,$E6,$80,$EB,$B2,$B0,$0E,$0C,$A8,$73,$D3,$8F,$0A,$B5,$D5
	dc.b $FC,$D3,$C6,$3D,$C9,$C1,$B8,$0E,$F7,$F6,$E0,$FE,$13,$A4,$B0,$06
	dc.b $07,$FC,$2C,$47,$83,$B0,$89,$BF,$F9,$10,$40,$22,$25,$58,$8D,$46
	dc.b $38,$26,$4F,$A6,$DC,$1F,$F3,$EA,$FD,$59,$80,$1F,$57,$B4,$1C,$40
	dc.b $50,$33,$20,$FF,$BF,$1C,$24,$D0,$1F,$FE,$BE,$18,$FE,$27,$06,$E0
	dc.b $2D,$DF,$FD,$C1,$F8,$0E,$9F,$C0,$41,$7F,$83,$50,$9C,$1B,$80,$CF
	dc.b $7F,$F9,$A0,$C4,$18,$18,$48,$20,$03,$51,$80,$5F,$4D,$9F,$BD,$91
	dc.b $8E,$5C,$FC,$66,$50,$81,$5C,$76,$83,$F0,$2C,$24,$3F,$DB,$C7,$F1
	dc.b $36,$2F,$0B,$FE,$14,$44,$B3,$83,$08,$1B,$C7,$FF,$68,$7C,$6C,$08
	dc.b $78,$07,$F0,$AC,$01,$27,$3B,$C1,$EE,$7F,$FC,$A0,$C4,$18,$18,$DC
	dc.b $04,$2A,$B8,$C1,$80,$83,$C3,$94,$CE,$9E,$E5,$C3,$94,$C6,$19,$99
	dc.b $8F,$C0,$0C,$D1,$60,$1C,$1E,$66,$1B,$CE,$20,$19,$18,$28,$3D,$7C
	dc.b $32,$3C,$2E,$00,$43,$DC,$3F,$FA,$FB,$C0,$2B,$42,$3F,$0A,$E0,$31
	dc.b $08,$DE,$0F,$B3,$FE,$08,$B1,$C0,$CD,$C0,$07,$D0,$62,$0A,$8D,$B1
	dc.b $83,$33,$BB,$01,$53,$E6,$84,$CC,$3D,$00,$6B,$45,$80,$70,$78,$9C
	dc.b $E7,$E6,$58,$E0,$13,$CF,$28,$72,$7C,$2E,$00,$43,$E8,$1F,$FE,$44
	dc.b $64,$10,$30,$DF,$81,$78,$0C,$48,$57,$83,$F4,$01,$88,$08,$32,$F0
	dc.b $03,$F4,$18,$82,$A3,$26,$37,$65,$14,$C4,$80,$EC,$32,$E6,$9E,$40
	dc.b $3C,$D1,$60,$1C,$1F,$17,$80,$D2,$1E,$1B,$C1,$C4,$1E,$81,$BE,$A0
	dc.b $73,$01,$A0,$FD,$03,$E1,$23,$5E,$88,$7F,$C1,$BD,$02,$A0,$10,$FE
	dc.b $80,$62,$02,$0D,$7C,$01,$C0,$10,$EF,$83,$61,$CD,$CE,$99,$25,$E0
	dc.b $E0,$59,$72,$E6,$9A,$40,$1D,$69,$B0,$0E,$0D,$E5,$E0,$15,$1F,$10
	dc.b $12,$AC,$2E,$3A,$14,$63,$10,$08,$7E,$40,$FF,$17,$F8,$07,$1F,$A3
	dc.b $FE,$09,$F0,$02,$28,$D5,$03,$E8,$09,$07,$FA,$0E,$88,$90,$66,$20
	dc.b $68,$F2,$70,$23,$FC,$B0,$70,$33,$F2,$A6,$AF,$78,$BD,$47,$06,$39
	dc.b $1E,$18,$40,$78,$E2,$B0,$47,$E3,$8F,$EF,$20,$09,$38,$1E,$0F,$E4
	dc.b $3F,$C1,$04,$2D,$E0,$7F,$C0,$5F,$80,$20,$A8,$38,$38,$00,$63,$81
	dc.b $03,$E1,$02,$07,$7F,$01,$0B,$D4,$14,$67,$02,$C9,$DC,$AF,$5B,$82
	dc.b $C9,$6A,$2B,$6B,$76,$06,$4E,$A5,$18,$38,$31,$C1,$ED,$8F,$CC,$16
	dc.b $0B,$F8,$E3,$FA,$08,$92,$81,$B6,$E6,$83,$FC,$01,$E0,$03,$C1,$51
	dc.b $7F,$E0,$0F,$C0,$9C,$C8,$70,$0E,$0E,$00,$24,$19,$FD,$50,$96,$0C
	dc.b $04,$1E,$1E,$5D,$DC,$0F,$5B,$00,$AD,$AD,$F8,$1C,$71,$43,$10,$B0
	dc.b $7A,$31,$FB,$A4,$0F,$5B,$FE,$71,$FD,$F0,$04,$0D,$47,$44,$70,$78
	dc.b $00,$91,$98,$20,$81,$FF,$80,$DF,$86,$95,$13,$D8,$1C,$1C,$00,$0C
	dc.b $42,$41,$85,$9B,$05,$20,$C4,$05,$1E,$04,$07,$CB,$FA,$89,$20,$25
	dc.b $51,$5A,$DA,$CE,$40,$D3,$00,$EE,$25,$E5,$83,$A0,$17,$28,$AF,$C4
	dc.b $05,$55,$D4,$E3,$F9,$80,$5A,$9B,$34,$1F,$00,$F0,$10,$43,$C1,$98
	dc.b $1F,$F0,$1F,$F8,$20,$E0,$D5,$0E,$00,$C1,$90,$60,$42,$C4,$04,$1B
	dc.b $F8,$49,$60,$E6,$0C,$40,$51,$F0,$60,$56,$49,$E0,$B2,$A5,$EB,$53
	dc.b $38,$A3,$A4,$18,$8B,$06,$01,$41,$A0,$B7,$68,$40,$AA,$E8,$71,$FC
	dc.b $3C,$82,$90,$56,$88,$1C,$C0,$48,$37,$01,$01,$07,$8C,$68,$01,$03
	dc.b $FC,$07,$7E,$41,$54,$59,$16,$0E,$43,$83,$BD,$06,$20,$20,$C5,$80
	dc.b $7E,$16,$0C,$04,$0E,$1F,$87,$03,$83,$48,$79,$14,$06,$42,$D2,$CB
	dc.b $7C,$6C,$01,$AD,$8A,$05,$60,$D8,$2E,$77,$90,$20,$56,$0C,$7F,$1E
	dc.b $1C,$6E,$07,$83,$B8,$80,$29,$38,$C0,$1C,$50,$30,$FF,$E0,$90,$07
	dc.b $D2,$1C,$01,$83,$C8,$F0,$D9,$44,$00,$70,$3F,$F1,$20,$07,$EC,$18
	dc.b $87,$23,$2E,$FC,$01,$E0,$1A,$20,$C5,$66,$DA,$4C,$E4,$30,$63,$19
	dc.b $81,$60,$34,$18,$B6,$20,$0B,$86,$49,$0E,$00,$81,$C7,$78,$F2,$21
	dc.b $EE,$1C,$1F,$66,$A4,$0C,$63,$C0,$4E,$4F,$F8,$9F,$80,$7F,$D8,$10
	dc.b $01,$EF,$0E,$03,$41,$F9,$76,$40,$C4,$5C,$CB,$D8,$0F,$6A,$20,$67
	dc.b $C0,$74,$4E,$46,$AF,$F4,$01,$51,$48,$44,$4A,$FE,$6A,$52,$59,$01
	dc.b $92,$C2,$58,$0D,$06,$17,$C4,$03,$E0,$DE,$43,$80,$20,$63,$14,$78
	dc.b $08,$D9,$27,$06,$ED,$DC,$02,$A0,$38,$46,$BE,$FD,$F0,$2F,$FE,$E1
	dc.b $1E,$1D,$01,$C0,$68,$37,$9F,$60,$1B,$0F,$F2,$3D,$14,$10,$05,$82
	dc.b $E3,$0F,$00,$C4,$39,$18,$61,$A0,$14,$52,$7F,$CD,$3F,$9A,$5F,$6F
	dc.b $6E,$0E,$38,$4B,$72,$D0,$70,$00,$9E,$80,$AB,$86,$B4,$CF,$6F,$99
	dc.b $BC,$56,$30,$08,$25,$2C,$08,$C1,$9C,$7B,$03,$8A,$07,$12,$00,$BF
	dc.b $F8,$EF,$FF,$00,$64,$15,$03,$07,$00,$7F,$F4,$0F,$D9,$FF,$40,$C4
	dc.b $60,$7F,$E0,$A2,$88,$4A,$B4,$42,$91,$C0,$07,$0B,$45,$B1,$5E,$C3
	dc.b $F0,$66,$24,$FF,$AE,$25,$73,$23,$8E,$03,$08,$72,$A0,$D0,$60,$5E
	dc.b $42,$12,$F1,$C4,$D0,$80,$A0,$00,$DB,$F9,$21,$E9,$27,$DC,$3E,$50
	dc.b $63,$9F,$E3,$E0,$B0,$C4,$80,$1F,$FF,$D8,$F1,$FF,$84,$51,$C0,$4E
	dc.b $5C,$E6,$83,$1F,$F9,$1F,$FB,$C6,$6F,$50,$3F,$00,$18,$C8,$63,$00
	dc.b $48,$51,$06,$47,$40,$0F,$17,$E3,$F0,$4D,$80,$F9,$11,$02,$03,$73
	dc.b $9C,$C9,$CE,$C1,$CE,$00,$C1,$A0,$00,$BE,$F8,$02,$8D,$8B,$A0,$0C
	dc.b $70,$00,$EF,$62,$43,$D0,$71,$C0,$B0,$74,$11,$DF,$61,$E0,$20,$DE
	dc.b $EC,$71,$9F,$FF,$87,$CF,$FE,$21,$E8,$38,$16,$0E,$3F,$F3,$FD,$0A
	dc.b $30,$40,$04,$0B,$C0,$0C,$1B,$8C,$06,$20,$28,$D8,$30,$FB,$47,$3F
	dc.b $4A,$D8,$1B,$EE,$94,$C0,$3C,$B2,$9B,$1C,$58,$38,$E0,$58,$34,$01
	dc.b $EF,$C0,$22,$37,$44,$01,$FE,$60,$D7,$98,$91,$E8,$38,$0B,$06,$A0
	dc.b $87,$FA,$06,$01,$CD,$7F,$7F,$CF,$7F,$FE,$7E,$7F,$E1,$02,$C1,$C7
	dc.b $02,$C1,$E1,$81,$C6,$49,$4A,$81,$E0,$01,$5A,$F1,$01,$88,$0A,$3B
	dc.b $08,$06,$68,$6F,$E1,$6F,$C4,$1C,$71,$BE,$0E,$79,$82,$9A,$0E,$38
	dc.b $16,$0D,$C0,$00,$7D,$F8,$04,$59,$83,$80,$1C,$72,$03,$91,$D0,$89
	dc.b $E5,$08,$38,$03,$07,$41,$83,$FC,$02,$01,$E7,$41,$8B,$E7,$BE,$08
	dc.b $B3,$FB,$84,$16,$23,$41,$88,$5A,$08,$30,$6E,$10,$0C,$A0,$7F,$00
	dc.b $76,$A2,$00,$62,$02,$8C,$72,$33,$53,$FF,$8D,$FF,$C0,$00,$0F,$1F
	dc.b $EA,$CD,$0A,$C0,$E3,$81,$60,$C4,$18,$03,$EB,$C0,$02,$B0,$1C,$39
	dc.b $06,$2F,$F8,$25,$FE,$98,$38,$03,$07,$E1,$C1,$FE,$83,$0B,$ED,$FE
	dc.b $FD,$02,$58,$40,$CC,$1A,$20,$70,$06,$0F,$00,$82,$02,$5D,$90,$02
	dc.b $07,$00,$09,$FA,$D0,$10,$01,$C8,$C7,$24,$0B,$9E,$9F,$F0,$FF,$E3
	dc.b $07,$E0,$E0,$0D,$D9,$C1,$96,$20,$0B,$8E,$0E,$70,$0A,$0C,$82,$02
	dc.b $1C,$5C,$00,$1E,$02,$7C,$40,$03,$03,$86,$04,$3D,$E0,$03,$20,$43
	dc.b $9C,$02,$83,$50,$60,$81,$88,$10,$3E,$F0,$55,$45,$13,$F0,$81,$90
	dc.b $07,$81,$0E,$01,$41,$B0,$50,$40,$C4,$08,$18,$00,$20,$8A,$DF,$7F
	dc.b $00,$74,$22,$31,$39,$1F,$84,$CF,$A7,$FE,$31,$05,$E0,$EF,$EF,$FD
	dc.b $AC,$F2,$0A,$2E,$57,$C0,$38,$05,$06,$41,$61,$0E,$16,$00,$45,$1B
	dc.b $81,$C4,$03,$E3,$83,$08,$7D,$CC,$07,$0A,$03,$9C,$02,$83,$50,$F0
	dc.b $7F,$47,$85,$FA,$0E,$59,$F8,$BF,$CF,$08,$3F,$40,$3B,$28,$70,$0A
	dc.b $0D,$82,$42,$06,$22,$45,$40,$01,$40,$BF,$E7,$EF,$60,$3E,$44,$37
	dc.b $2A,$46,$39,$50,$66,$FD,$3F,$83,$8C,$08,$1E,$47,$1C,$6F,$CF,$28
	dc.b $E7,$00,$CF,$F0,$72,$A0,$D0,$78,$18,$60,$A0,$00,$40,$19,$0C,$23
	dc.b $8F,$F8,$20,$8F,$FC,$40,$78,$58,$70,$0A,$0C,$C2,$C2,$06,$23,$31
	dc.b $0F,$DF,$FF,$E3,$FF,$BE,$51,$56,$01,$FA,$81,$C0,$28,$32,$0D,$08
	dc.b $18,$88,$08,$16,$E2,$5E,$CF,$CF,$A0,$1F,$A8,$37,$2A,$46,$39,$5C
	dc.b $26,$7E,$1C,$E3,$4E,$9E,$54,$04,$FF,$95,$CE,$A2,$59,$C0,$37,$80
	dc.b $E5,$41,$A0,$E6,$30,$C0,$C0,$86,$80,$BE,$0A,$00,$01,$FA,$B0,$BF
	dc.b $D8,$10,$58,$38,$6D,$68,$33,$0F,$83,$F4,$78,$4F,$FF,$D3,$ED,$FF
	dc.b $FF,$1F,$E7,$9C,$58,$A0,$7F,$60,$62,$1A,$0F,$20,$0F,$7D,$01,$60
	dc.b $90,$44,$80,$A0,$DF,$C8,$1F,$C8,$31,$06,$46,$60,$20,$CD,$FC,$F2
	dc.b $AB,$B8,$3A,$E9,$C0,$8D,$01,$38,$AB,$33,$E7,$30,$21,$CC,$43,$41
	dc.b $F0,$70,$80,$81,$6B,$90,$57,$10,$00,$80,$75,$88,$62,$44,$80,$78
	dc.b $DA,$0C,$C3,$62,$06,$23,$AD,$FF,$1E,$84,$09,$FF,$FE,$03,$12,$C2
	dc.b $03,$80,$D0,$64,$00,$31,$29,$48,$03,$82,$10,$28,$00,$08,$1B,$0C
	dc.b $90,$00,$63,$10,$64,$6A,$04,$DF,$A7,$80,$44,$FB,$B9,$16,$5F,$05
	dc.b $79,$91,$1A,$66,$76,$DC,$1C,$E0,$34,$1E,$47,$08,$10,$09,$CD,$41
	dc.b $2F,$02,$88,$07,$38,$B0,$3D,$F8,$C0,$B0,$08,$70,$1A,$0C,$26,$F0
	dc.b $BE,$2B,$E1,$50,$D0,$2F,$E7,$D0,$F7,$8C,$63,$80,$D0,$7D,$00,$50
	dc.b $10,$75,$07,$A4,$28,$0C,$00,$0C,$40,$81,$9C,$75,$23,$C8,$B1,$29
	dc.b $FF,$9F,$20,$F6,$55,$6A,$7F,$3F,$DA,$A7,$45,$6C,$4C,$C6,$38,$39
	dc.b $C0,$18,$36,$10,$10,$11,$01,$CA,$F8,$06,$42,$CD,$70,$1D,$7C,$20
	dc.b $3C,$14,$38,$0D,$07,$E8,$0F,$01,$F0,$1F,$85,$BF,$C5,$44,$D6,$FC
	dc.b $01,$FD,$A4,$43,$80,$D0,$60,$3D,$90,$50,$10,$FE,$07,$A4,$17,$4C
	dc.b $A0,$0C,$47,$84,$06,$20,$C8,$C0,$00,$DC,$0D,$1F,$6F,$80,$B5,$1E
	dc.b $55,$FF,$F5,$E1,$F3,$6A,$A3,$9C,$AD,$A4,$38,$E0,$28,$30,$2B,$CE
	dc.b $0A,$00,$13,$9A,$E7,$83,$CF,$3C,$1F,$03,$57,$DC,$43,$01,$83,$87
	dc.b $04,$83,$2A,$BF,$00,$63,$40,$7C,$03,$C3,$61,$1C,$41,$CF,$80,$3E
	dc.b $28,$C8,$70,$0A,$0E,$00,$0B,$91,$03,$12,$0E,$0C,$EA,$BA,$3F,$01
	dc.b $89,$74,$7F,$E0,$12,$D4,$8E,$00,$0C,$B2,$6D,$EA,$BB,$13,$FE,$67
	dc.b $23,$BF,$FE,$1E,$70,$16,$7F,$8C,$62,$43,$8E,$02,$83,$31,$9C,$21
	dc.b $54,$10,$00,$77,$8D,$C1,$20,$11,$E0,$7E,$F8,$C8,$38,$18,$39,$C0
	dc.b $48,$34,$00,$18,$C1,$E0,$F7,$ED,$B8,$1E,$27,$F0,$78,$04,$DF,$88
	dc.b $70,$38,$05,$06,$47,$18,$8F,$FC,$1C,$0C,$40,$81,$BC,$CF,$FD,$0F
	dc.b $FA,$21,$A5,$10,$C4,$63,$91,$E0,$18,$AC,$F6,$37,$FD,$DD,$3E,$87
	dc.b $F8,$1E,$07,$C4,$A6,$19,$BF,$07,$38,$09,$07,$00,$01,$C1,$81,$D5
	dc.b $78,$A0,$01,$A8,$BE,$52,$01,$B5,$9B,$FF,$C8,$82,$81,$21,$CE,$02
	dc.b $41,$E0,$01,$F6,$1F,$E3,$86,$9E,$01,$8C,$8B,$7F,$8C,$9F,$00,$7D
	dc.b $41,$BF,$30,$A8,$14,$18,$10,$0C,$6C,$0B,$84,$06,$30,$00,$30,$2E
	dc.b $70,$18,$8A,$0B,$FC,$27,$AA,$91,$E0,$01,$16,$29,$C3,$C9,$B3,$00
	dc.b $54,$52,$40,$7E,$59,$19,$B4,$5A,$46,$0F,$6E,$95,$41,$20,$D0,$00
	dc.b $7C,$3C,$3F,$60,$EA,$7F,$F7,$E7,$20,$38,$1D,$6A,$23,$AD,$C7,$02
	dc.b $C1,$43,$80,$90,$70,$00,$5D,$81,$E0,$30,$14,$44,$AF,$C1,$7B,$26
	dc.b $7F,$C1,$3F,$80,$77,$B4,$38,$09,$06,$39,$7A,$7F,$FF,$3F,$F8,$7F
	dc.b $BF,$A1,$F3,$02,$CF,$01,$88,$C0,$BF,$40,$B9,$94,$1A,$08,$2C,$34
	dc.b $00,$33,$C3,$1C,$1B,$F3,$4F,$6E,$DB,$D3,$E6,$E0,$CA,$CB,$19,$60
	dc.b $3C,$79,$0E,$38,$12,$0E,$80,$03,$C3,$C8,$2E,$01,$1F,$F8,$44,$10
	dc.b $01,$FB,$89,$81,$C1,$83,$E4,$40,$20,$37,$25,$06,$07,$D8,$16,$05
	dc.b $01,$CE,$02,$FC,$79,$FF,$02,$CE,$3E,$01,$F0,$07,$9C,$21,$CC,$40
	dc.b $C1,$FE,$FE,$BF,$FC,$63,$02,$31,$BF,$E7,$E1,$A2,$20,$31,$B0,$31
	dc.b $0A,$47,$40,$02,$59,$23,$F1,$30,$36,$56,$EE,$33,$BF,$A8,$31,$3A
	dc.b $93,$22,$07,$CD,$21,$C3,$6A,$41,$90,$01,$B2,$F5,$04,$82,$A1,$F3
	dc.b $87,$A4,$C0,$CF,$85,$81,$F7,$E3,$00,$20,$60,$E0,$C5,$20,$C5,$6F
	dc.b $C8,$70,$68,$36,$30,$37,$83,$C3,$FC,$00,$67,$E0,$0F,$C0,$3C,$6E
	dc.b $0E,$70,$12,$0C,$3A,$F4,$FB,$FA,$7D,$FC,$FC,$FF,$C3,$FF,$3F,$80
	dc.b $EC,$5D,$01,$A4,$81,$18,$48,$3C,$10,$D8,$7C,$00,$3F,$84,$06,$17
	dc.b $0F,$EA,$DD,$80,$E5,$ED,$4F,$CC,$D2,$72,$C0,$4C,$12,$1C,$70,$24
	dc.b $1B,$00,$03,$03,$40,$24,$23,$15,$C4,$79,$17,$00,$EE,$37,$07,$47
	dc.b $3F,$07,$29,$AE,$C0,$70,$3E,$00,$37,$C0,$C0,$48,$64,$30,$07,$00
	dc.b $0E,$63,$00,$21,$0F,$81,$FC,$01,$D0,$30,$E0,$24,$1C,$00,$1B,$A3
	dc.b $A1,$C3,$D5,$E3,$09,$60,$81,$DE,$FF,$FE,$A0,$C6,$C0,$01,$88,$52
	dc.b $3A,$00,$06,$C4,$4C,$53,$17,$B1,$4D,$08,$05,$CA,$27,$A9,$C4,$D2
	dc.b $08,$1C,$C6,$25,$8D,$06,$60,$A0,$11,$04,$4F,$F2,$1C,$44,$C3,$3F
	dc.b $C8,$81,$B1,$C4,$06,$21,$C1,$C9,$62,$41,$D0,$01,$9E,$2C,$06,$41
	dc.b $10,$FC,$78,$5F,$0F,$8F,$82,$5F,$83,$7E,$F0,$72,$C8,$D0,$66,$31
	dc.b $A3,$40,$A3,$E6,$F0,$3D,$06,$27,$83,$EF,$FD,$06,$31,$F8,$68,$3C
	dc.b $10,$D8,$66,$31,$E0,$02,$2B,$DA,$70,$A2,$54,$2C,$85,$06,$56,$6D
	dc.b $69,$84,$0E,$62,$16,$0C,$3A,$00,$83,$8F,$F9,$45,$20,$C7,$9F,$F1
	dc.b $60,$A8,$E1,$C0,$FB,$81,$A0,$CC,$61,$C0,$04,$50,$48,$3F,$1F,$37
	dc.b $D7,$E3,$E0,$43,$E0,$DF,$C0,$18,$1C,$C4,$0C,$18,$A0,$02,$27,$DF
	dc.b $E0,$7F,$EC,$17,$FE,$06,$18,$DF,$5F,$E0,$68,$31,$01,$46,$30,$03
	dc.b $8A,$71,$7F,$FC,$7F,$03,$C3,$FD,$E9,$30,$8F,$64,$0C,$C0,$83,$95
	dc.b $06,$83,$38,$A0,$20,$4B,$FF,$98,$C8,$03,$CF,$FD,$10,$36,$38,$40
	dc.b $88,$28,$3C,$E0,$48,$3E,$00,$38,$00,$8C,$0F,$0C,$30,$2B,$E0,$4C
	dc.b $40,$E7,$E0,$7F,$D8,$31,$03,$06,$06,$18,$01,$00,$FC,$41,$89,$C1
	dc.b $00,$C4,$BF,$82,$46,$02,$E0,$81,$88,$52,$3E,$00,$1C,$09,$02,$7D
	dc.b $FB,$88,$66,$0B,$04,$73,$EB,$2C,$8E,$60,$09,$C5,$07,$D8,$E9,$06
	dc.b $47,$0E,$4C,$18,$1D,$FF,$AF,$A4,$31,$AF,$DD,$F8,$7B,$3C,$00,$0A
	dc.b $18,$50,$92,$0F,$80,$06,$01,$F2,$06,$07,$8A,$30,$2B,$F0,$3C,$51
	dc.b $E3,$C0,$2F,$E0,$3A,$14,$38,$09,$07,$80,$03,$01,$2A,$80,$FF,$FB
	dc.b $BF,$06,$23,$FA,$0E,$18,$86,$FE,$BC,$5A,$91,$8E,$17,$21,$9F,$BA
	dc.b $B8,$7D,$03,$C1,$DE,$DF,$31,$23,$B4,$B4,$E2,$83,$E0,$34,$83,$38
	dc.b $80,$80,$06,$38,$3B,$DC,$1F,$08,$5F,$C3,$2D,$F0,$3D,$FC,$49,$48
	dc.b $03,$84,$38,$70,$48,$33,$81,$10,$E0,$F1,$FD,$F9,$BF,$3F,$BF,$4F
	dc.b $3F,$00,$FE,$39,$C8,$A0,$E0,$E1,$20,$D0,$00,$20,$39,$74,$00,$C4
	dc.b $B8,$00,$31,$0A,$06,$69,$E0,$1E,$83,$10,$24,$67,$10,$E5,$F3,$5F
	dc.b $D8,$43,$0A,$80,$07,$0A,$EE,$CB,$69,$CC,$2B,$71,$41,$CB,$22,$41
	dc.b $B0,$40,$84,$00,$01,$B0,$7F,$82,$7C,$30,$9E,$10,$3F,$F0,$F5,$BC
	dc.b $10,$90,$48,$7E,$EA,$90,$68,$10,$30,$38,$80,$B8,$30,$7E,$59,$09
	dc.b $09,$4F,$41,$8F,$00,$5F,$9A,$64,$09,$F0,$E0,$04,$1B,$04,$00,$58
	dc.b $07,$E9,$0C,$6C,$0A,$BA,$80,$1D,$68,$E4,$01,$C0,$A0,$F0,$40,$E1
	dc.b $C3,$82,$F8,$78,$D3,$F7,$47,$84,$20,$20,$F9,$79,$E6,$2D,$73,$37
	dc.b $6C,$08,$7C,$4A,$90,$64,$00,$40,$80,$80,$CC,$0B,$8E,$B2,$EC,$24
	dc.b $1D,$A7,$D8,$0E,$BF,$09,$41,$00,$4A,$1C,$E0,$24,$1C,$18,$38,$32
	dc.b $0C,$68,$10,$77,$DF,$F7,$FA,$10,$13,$FE,$74,$4E,$9E,$10,$FA,$29
	dc.b $06,$41,$04,$0F,$F5,$83,$1B,$FB,$EF,$89,$06,$36,$F0,$13,$7A,$F5
	dc.b $D0,$36,$83,$10,$A4,$6B,$E5,$7F,$78,$F5,$FD,$5C,$62,$E0,$23,$34
	dc.b $9A,$8C,$85,$3E,$75,$5A,$02,$1F,$C5,$94,$1E,$77,$40,$20,$C3,$00
	dc.b $F6,$4A,$FF,$01,$35,$8B,$DF,$01,$FD,$E6,$40,$40,$2C,$87,$38,$09
	dc.b $07,$9E,$3F,$03,$11,$03,$26,$18,$7F,$C1,$44,$40,$1F,$C0,$5F,$F2
	dc.b $F8,$C0,$E0,$E0,$A0,$DC,$E6,$91,$FC,$1F,$E0,$80,$FF,$FB,$BF,$64
	dc.b $0D,$7F,$F9,$D0,$3B,$83,$10,$A4,$73,$E3,$3F,$D3,$F4,$F8,$DD,$71
	dc.b $FB,$34,$1B,$FC,$79,$AA,$8E,$6A,$7B,$E2,$1C,$E0,$14,$1B,$E7,$C0
	dc.b $09,$03,$06,$C0,$D1,$23,$04,$0C,$F8,$D6,$0A,$FA,$E4,$E8,$F8,$4C
	dc.b $87,$31,$05,$06,$31,$5C,$3F,$8A,$77,$FC,$5F,$C8,$47,$D4,$0F,$FC
	dc.b $5C,$54,$C2,$25,$06,$62,$04,$0C,$F0,$1D,$61,$0F,$F7,$05,$EC,$20
	dc.b $61,$FF,$DF,$D1,$9C,$18,$85,$23,$3D,$33,$FB,$3F,$AF,$FC,$D3,$AF
	dc.b $D9,$61,$CE,$FF,$CC,$B0,$F9,$E9,$CE,$11,$90,$E7,$01,$20,$FF,$FC
	dc.b $01,$10,$18,$39,$0C,$1E,$B8,$00,$39,$C4,$4F,$80,$4F,$9D,$F8,$19
	dc.b $41,$C0,$50,$7F,$A1,$F0,$31,$1E,$7F,$0D,$B7,$F3,$00,$E6,$73,$FD
	dc.b $02,$F0,$14,$0F,$41,$5A,$0F,$C2,$D1,$87,$C6,$03,$C1,$20,$33,$FC
	dc.b $66,$3F,$F9,$F7,$D0,$3E,$A4,$20,$0D,$10,$A4,$73,$C3,$3F,$DF,$F4
	dc.b $FF,$9F,$A6,$42,$10,$37,$DF,$F3,$D6,$BB,$3A,$89,$A2,$1C,$E0,$14
	dc.b $1B,$E8,$08,$20,$06,$0F,$80,$12,$E2,$0E,$38,$01,$F8,$01,$71,$EF
	dc.b $A8,$EA,$0E,$31,$1A,$0C,$1C,$1E,$14,$74,$03,$BD,$7F,$C1,$00,$FE
	dc.b $FF,$C1,$BE,$01,$E2,$81,$CC,$43,$41,$97,$09,$8D,$FC,$03,$80,$3E
	dc.b $FE,$43,$11,$1F,$03,$34,$62,$0C,$8C,$FD,$CF,$EF,$7E,$BC,$4B,$F3
	dc.b $20,$44,$79,$FB,$E3,$2D,$D8,$BD,$1B,$98,$43,$91,$86,$83,$B0,$04
	dc.b $04,$60,$C6,$C4,$0E,$41,$01,$18,$1F,$05,$4F,$81,$66,$1E,$87,$00
	dc.b $A0,$FF,$D3,$C0,$06,$38,$08,$62,$5C,$10,$18,$C7,$D4,$83,$F4,$1F
	dc.b $04,$38,$05,$07,$FB,$7F,$FF,$DF,$82,$9A,$E0,$03,$86,$31,$B5,$C1
	dc.b $CC,$26,$20,$C8,$E7,$A2,$7F,$75,$D5,$C9,$4C,$29,$04,$0C,$46,$3F
	dc.b $27,$6C,$66,$42,$2C,$C4,$39,$C0,$28,$37,$C8,$88,$78,$58,$18,$50
	dc.b $20,$88,$21,$3F,$D0,$E0,$79,$FE,$63,$D0,$C0,$39,$F8,$68,$30,$F0
	dc.b $11,$44,$7A,$DD,$13,$06,$08,$49,$F8,$D0,$19,$C1,$F0,$86,$21,$A0
	dc.b $E3,$FF,$B9,$D0,$32,$5C,$00,$70,$50,$1F,$F8,$E8,$E6,$9F,$C0,$62
	dc.b $0C,$8C,$F8,$0F,$DD,$5E,$B7,$20,$01,$4A,$45,$A4,$01,$7B,$20,$FB
	dc.b $02,$4D,$64,$43,$9C,$06,$83,$02,$00,$10,$80,$07,$FF,$41,$A0,$08
	dc.b $FF,$A1,$C1,$C0,$F4,$76
	dc.b $99,$0C,$37,$8B,$41,$81,$83,$C0,$40,$E2,$02,$C0,$82,$C1,$09,$1F
	dc.b $03,$AA,$2C,$3E,$81,$C0,$28,$3F,$C0,$3F,$9F,$77,$E2,$18,$09,$8C
	dc.b $00,$03,$1B,$BC,$1C,$D1,$F8,$0C,$41,$91,$CC,$00,$77,$63,$AE,$C7
	dc.b $81,$C1,$88,$75,$48,$B7,$CA,$C9,$E3,$7B,$0A,$08,$71,$C0,$30,$60
	dc.b $D8,$00,$00,$FF,$84,$14,$01,$4F,$D6,$11,$3D,$70,$FF,$C3,$0C,$1C
	dc.b $E0,$14,$1F,$C0,$00,$52,$00,$0F,$FF,$FD,$F9,$F8,$4F,$F1,$FB,$F0
	dc.b $40,$40,$0F,$07,$38,$0D,$06,$41,$7B,$63,$FF,$20,$C2,$40,$C0,$F7
	dc.b $41,$74,$63,$67,$80,$E7,$88,$1C,$88,$62,$37,$E0,$2B,$87,$5B,$F1
	dc.b $8F,$E4,$11,$09,$3F,$13,$7C,$12,$84,$13,$F0,$D1,$0E,$70,$0A,$0D
	dc.b $E0,$12,$12,$32,$64,$A8,$50,$0A,$B6,$6C,$1E,$95,$20,$1F,$80,$73
	dc.b $1E,$90,$79,$13,$F0,$35,$C2,$88,$07,$C7,$FE,$F9,$F8,$97,$E0,$FF
	dc.b $F6,$58,$0E,$07,$07,$38,$0D,$06,$F4,$09,$91,$6D,$8D,$01,$20,$C0
	dc.b $EF,$03,$C3,$78,$E0,$82,$E8,$85,$18,$E0,$93,$86,$DB,$F8,$AB,$C1
	dc.b $C0,$80,$A7,$C4,$DD,$41,$DC,$08,$0F,$07,$86,$CD,$06,$60,$18,$60
	dc.b $81,$58,$40,$01,$A2,$81,$E6,$1B,$BD,$83,$82,$02,$01,$03,$9C,$06
	dc.b $83,$34,$1E,$50,$13,$00,$22,$25,$DE,$7E,$ED,$FC,$1E,$3F,$43,$1B
	dc.b $F4,$07,$01,$A0,$CE,$07,$2C,$3B,$7F,$C3,$C0,$04,$30,$23,$C0,$7C
	dc.b $30,$3A,$B5,$03,$FD,$02,$E6,$50,$70,$21,$B0,$C6,$85,$09,$80,$30
	dc.b $F9,$15,$00,$2E,$28,$05,$7E,$64,$E6,$05,$00,$53,$20,$71,$C0,$D0
	dc.b $63,$80,$31,$A4,$2A,$65,$41,$C6,$07,$E9,$81,$41,$C9,$08,$07,$00
	dc.b $A0,$C3,$85,$0E,$80,$02,$08,$62,$3E,$67,$FD,$9F,$E0,$27,$E1,$00
	dc.b $2E,$80,$1C,$E0,$14,$18,$60,$C1,$E2,$0E,$A3,$11,$0C,$01,$88,$50
	dc.b $30,$17,$A8,$28,$83,$23,$32,$08,$E6,$00,$FB,$CF,$67,$80,$0D,$50
	dc.b $04,$FF,$E5,$98,$AB,$60,$E3,$80,$E0,$C6,$80,$00,$4C,$08,$00,$06
	dc.b $68,$3D,$C0,$3D,$20,$1C,$C8,$39,$C0,$18,$31,$A0,$8F,$C0,$0C,$7B
	dc.b $46,$37,$C9,$FF,$47,$F8,$4B,$FD,$0C,$45,$60,$14,$18,$E0,$27,$D0
	dc.b $06,$03,$1A,$0C,$03,$11,$21,$8A,$85,$75,$19,$1F,$90,$7B,$30,$3F
	dc.b $EE,$65,$57,$58,$37,$E1,$57,$FB,$93,$30,$5B,$07,$38,$03,$07,$50
	dc.b $02,$30,$04,$00,$22,$C1,$00,$19,$41,$DC,$00,$D9,$C1,$E6,$C1,$CE
	dc.b $00,$C1,$DD,$06,$FF,$02,$E0,$62,$BF,$87,$FE,$3F,$F2,$03,$F1,$0C
	dc.b $38,$03,$07,$78,$0B,$F4,$0F,$81,$8A,$81,$E0,$40,$46,$21,$BE,$C0
	dc.b $4B,$02,$8D,$D0,$19,$B0,$2B,$F3,$84,$9E,$DB,$B8,$4D,$59,$F8,$E7
	dc.b $35,$59,$83,$9C,$43,$80,$A0,$D2,$00,$84,$90,$E1,$0D,$70,$60,$8A
	dc.b $2E,$66,$40,$AF,$60,$13,$80,$64,$60,$79,$C0,$50,$7F,$C1,$70,$51
	dc.b $9C,$23,$1B,$32,$7F,$4D,$06,$31,$FA,$A0,$01,$06,$09,$63,$41,$85
	dc.b $81,$46,$10,$8C,$63,$3E,$03,$F4,$18,$8B,$B8,$07,$C2,$0C,$41,$91
	dc.b $B7,$06,$67,$0B,$7E,$F3,$95,$4E,$4F,$36,$58,$7C,$2C,$B3,$D0,$72
	dc.b $08,$E0,$34,$18,$D0,$21,$B0,$70,$00,$67,$07,$1F,$6A,$7C,$34,$3C
	dc.b $F1,$07,$D1,$91,$00,$0E,$02,$83,$F6,$0F,$FE,$11,$C2,$BC,$1D,$5A
	dc.b $C7,$CF,$FF,$F0,$0F,$D3,$E2,$C0,$05,$C0,$28,$3F,$A0,$FF,$21,$FF
	dc.b $E2,$18,$8B,$97,$83,$FA,$0C,$40,$81,$F8,$00,$C4,$19,$1D,$20,$46
	dc.b $E2,$27,$DB,$99,$08,$21,$39,$9B,$C4,$0F,$59,$07,$D2,$ED,$60,$28
	dc.b $31,$80,$82,$43,$CC,$11,$47,$16,$B1,$19,$1F,$F8,$66,$0D,$32,$A2
	dc.b $C1,$FA,$07,$F4,$21,$81,$91,$5E,$FF,$6B,$C3,$1F,$FF,$F0,$3F,$67
	dc.b $C0,$58,$3F,$80,$FF,$47,$FF,$DF,$FA,$77,$5E,$1F,$9F,$E0,$18,$31
	dc.b $02,$06,$38,$0A,$0F,$F8,$36,$1F,$A0,$95,$E4,$4F,$B5,$C9,$64,$18
	dc.b $38,$65,$7F,$EE,$D3,$20,$0B,$07,$38,$03,$06,$24,$20,$98,$F0,$00
	dc.b $04,$D8,$FA,$C6,$1C,$C1,$F8,$19,$C5,$41,$C7,$04,$E0,$14,$1F,$30
	dc.b $FE,$E4,$38,$30,$03,$67,$E6,$E7,$88,$FF,$E7,$81,$07,$0B,$69,$88
	dc.b $28,$3F,$A1,$FE,$4F,$FF,$AF,$F9,$30,$3E,$00,$0F,$81,$01,$83,$06
	dc.b $FD,$4A,$46,$D0,$54,$C0,$13,$88,$39,$67,$CE,$5C,$14,$7F,$22,$ED
	dc.b $FD,$4F,$1C,$00,$0E,$01,$0E,$46,$0A,$0C,$C0,$03,$41,$C0,$E4,$05
	dc.b $36,$F8,$1C,$47,$83,$00,$63,$21,$1C,$02,$80,$43,$8C,$92,$83,$90
	dc.b $AE,$03,$E0,$E1,$06,$BF,$BC,$77,$0F,$E0,$70,$1F,$C0,$00,$60,$20
	dc.b $72,$A0,$50,$66,$36,$40,$1E,$27,$C8,$06,$25,$3F,$06,$0C,$8E,$02
	dc.b $40,$83,$10,$64,$7D,$82,$5E,$00,$D5,$33,$0A,$DC,$14,$7E,$2D,$B7
	dc.b $D6,$A2,$F6,$00,$17,$02,$1C,$C4,$14,$19,$30,$85,$07,$0E,$B4,$1D
	dc.b $5E,$FA,$19,$04,$E4,$09,$CC,$80,$B8,$0A,$40,$87,$1C,$05,$07,$98
	dc.b $3E,$E0,$3F,$8F,$8B,$8C,$FD,$F3,$3C,$0E,$03,$05,$BE,$80,$06,$C1
	dc.b $03,$98,$82,$83,$F2,$1F,$90,$43,$00,$8E,$03,$AE,$DD,$42,$07,$AE
	dc.b $03,$90,$83,$10,$64,$73,$03,$BC,$13,$EA,$CD,$40,$FA,$12,$6E,$72
	dc.b $6F,$E4,$4D,$ED,$82,$39,$82,$1C,$C4,$24,$18,$03,$20,$42,$03,$0D
	dc.b $4E,$7F,$D6,$79,$18,$40,$78,$01,$E1,$03,$38,$90,$24,$87,$1C,$05
	dc.b $07,$B6,$1F,$C0,$3D,$8E,$0B,$EC,$FC,$F3,$9F,$02,$16,$04,$FC,$40
	dc.b $1F,$41,$0B,$21,$41,$F6,$87,$90,$21,$82,$3F,$06,$14,$12,$D4,$0F
	dc.b $DD,$CF,$D1,$06,$21,$48,$C0,$0B,$83,$F0,$1B,$EB,$74,$80,$7A,$2A
	dc.b $E8,$B6,$7F,$EC,$59,$54,$03,$75,$24,$39,$88,$28,$3D,$20,$48,$0A
	dc.b $A5,$23,$5F,$CE,$7B,$3A,$94,$70,$03,$E6,$27,$EE,$61,$01,$0E,$31
	dc.b $0A,$0E,$FC,$1F,$01,$B7,$0E,$17,$E0,$FD,$E2,$76,$0C,$6C,$01,$F8
	dc.b $1E,$BE,$42,$0A,$84,$83,$80,$DC,$07,$40,$EE,$27,$05,$A1,$20,$7B
	dc.b $C0,$C4,$08,$1F,$BF,$C4,$03,$12,$91,$C0,$27,$83,$40,$43,$EB,$C7
	dc.b $82,$FA,$02,$C0,$78,$4B,$FE,$67,$3F,$88,$0B,$3A,$87,$C3,$5C,$DC
	dc.b $0E,$24,$07,$34,$29,$45,$07,$CE,$34,$67,$94,$30,$01,$EC,$0F,$E7
	dc.b $C0,$AE,$0A,$84,$83,$80,$6F,$81,$C5,$06,$03,$1B,$F8,$3F,$F9,$E5
	dc.b $00,$03,$80,$FC,$00,$03,$B7,$D1,$03,$58,$0E,$07,$5C,$0F,$01,$09
	dc.b $83,$12,$80,$43,$5F,$A0,$C4,$AF,$FF,$50,$3F,$09,$07,$82,$1B,$0E
	dc.b $02,$04,$11,$01,$17,$DC,$38,$5F,$D1,$B1,$DD,$DF,$F4,$6B,$3E,$60
	dc.b $F2,$59,$07,$31,$09,$07,$80,$05,$03,$41,$05,$A0,$F3,$F9,$D7,$DA
	dc.b $A6,$00,$0E,$E0,$B5,$00,$88,$20,$E3,$81,$20,$E0,$30,$E0,$4C,$26
	dc.b $37,$E0,$3F,$2F,$4C,$08,$07,$80,$FB,$C0,$FF,$9A,$07,$2C,$89,$06
	dc.b $80,$87,$00,$11,$31,$2F,$C7,$BB,$FA,$20,$05,$06,$FC,$01,$88,$52
	dc.b $33,$C8,$76,$80,$F5,$8F,$B7,$FD,$05,$0C,$CC,$F5,$4D,$CF,$14,$C0
	dc.b $68,$A0,$E7,$01,$20,$C0,$00,$60,$38,$21,$54,$08,$FF,$9F,$BF,$F5
	dc.b $61,$31,$D8,$03,$20,$11,$C4,$1C,$52,$D8,$0E,$07,$C1,$03,$03,$4A
	dc.b $00,$05,$83,$E2,$0F,$EB,$CE,$DC,$07,$C0,$FC,$7B,$03,$C0,$1D,$83
	dc.b $8C,$44,$83,$81,$06,$80,$4D,$20,$22,$17,$FB,$FF,$F2,$24,$6E,$99
	dc.b $3E,$B4,$43,$11,$A0,$10,$40,$22,$2A,$A3,$C3,$7F,$8A,$20,$01,$3E
	dc.b $F3,$29,$C0,$71,$DB,$30,$38,$A8,$48,$35,$38,$10,$01,$00,$02,$90
	dc.b $35,$FB,$9F,$B5,$E0,$6C,$3C,$80,$05,$46,$3F,$83,$8A,$84,$83,$70
	dc.b $20,$81,$A5,$80,$00,$D1,$E4,$03,$CE,$3C,$7E,$07,$E1,$BE,$03,$2D
	dc.b $E1,$41,$EE,$02,$41,$A8,$10,$02,$80,$60,$7F,$8B,$B0,$C6,$1F,$06
	dc.b $05,$F8,$03,$18,$05,$67,$FD,$06,$3C,$60,$C0,$40,$61,$D0,$10,$42
	dc.b $22,$D6,$FD,$88,$FD,$BF,$84,$51,$5F,$F6,$CC,$CD,$C1,$89,$24,$A0
	dc.b $E5,$5C,$A0,$C7,$04,$A9,$0A,$06,$23,$E3,$3D,$C2,$6C,$1F,$05,$06
	dc.b $21,$8C,$01,$C7,$02,$41,$98,$02,$20,$41,$A0,$20,$63,$20,$79,$88
	dc.b $1F,$03,$78,$7F,$A1,$4E,$FC,$40,$70,$70,$90,$74,$04,$30,$88,$BF
	dc.b $BF,$E0,$15,$40,$07,$F7,$FF,$FC,$92,$16,$47,$BF,$E0,$62,$14,$8D
	dc.b $61,$88,$6C,$01,$9D,$FF,$23,$FE,$7E,$E5,$4B,$D9,$3F,$30,$9F,$06
	dc.b $6C,$D6,$43,$9C,$04,$83,$08,$E1,$10,$00,$9D,$00,$A0,$FD,$FF,$D7
	dc.b $98,$F0,$AE,$0F,$60,$44,$93,$44,$90,$E7,$01,$20,$E6,$38,$E0,$71
	dc.b $01,$A0,$34,$01,$10,$62,$0C,$07,$87,$78,$2F,$82,$8E,$7C,$D0,$70
	dc.b $96,$90,$7A,$18,$63,$E0,$18,$90,$86,$00,$19,$1D,$F3,$FF,$A2,$46
	dc.b $7F,$C6,$9F,$FE,$C0,$4B,$52,$3C,$04,$22,$59,$CD,$33,$D1,$0F,$82
	dc.b $FE,$0B,$2D,$59,$E4,$C8,$F6,$50,$B3,$79,$0E,$2A,$0A,$0F,$04,$82
	dc.b $60,$B8,$89,$83,$EB,$7D,$3D,$33,$B1,$7E,$3E,$82,$80,$0F,$14,$43
	dc.b $8A,$82,$83,$31,$A5,$00,$A9,$78
	dc.l $03880740,$018F781F,$A386207A,$D9D80E07	; lookup_table
	dc.l $01E67F31,$8310207E,$2031AB2B,$FA60FFDC	; lookup_table
	dc.l $18852340,$724BEC66,$1750F4C7,$00E55153	; lookup_table
	dc.l $E3247920,$14BB0A81,$41F8802C,$4F1C3079	; lookup_table
	dc.l $0B8F0063,$5EC3907B,$082D9602,$A0A0F4CF	; lookup_table
	dc.l $FD00483C,$03C63863,$009E7C47,$93167D32	; lookup_table
	dc.l $E0241E07,$19FA0C63,$19E00188,$E1FF87E3	; lookup_table
	dc.l $97BED0C4,$291C0702,$B366986E,$87495C87	; lookup_table
	dc.l $FCAFEF36,$49B95494,$87380D06,$82305E34	; lookup_table
	dc.l $41CC667C,$0019F80C,$ADA79747,$C1C70141	; lookup_table
	dc.l $F0806244,$2E07CF37,$BFC0DF3E,$67C90B3F	; lookup_table
	dc.l $0839C048,$380F1818,$88FA442C,$AE105B50	; lookup_table
	dc.l $7FEBFAF9,$EFF40626,$47A0D4D8,$CC0E4C25	; lookup_table
	dc.l $88F801D1,$7EC4E62C,$453421C7,$38C18C4F	; lookup_table
	dc.l $42420DF8,$5F00D83C,$810CC287,$6340E2A0	; lookup_table
	dc.l $60FD0042,$2130894F,$FFE39E62,$2A15243C	; lookup_table
	dc.l $41C0283E,$0018887B,$D4342E00,$3B586031	; lookup_table
	dc.l $1C701426,$83810D87,$402AD9A7,$7B2A2C61	; lookup_table
	dc.l $3DFCFECF,$E78C68C4,$9621C0E3,$41818C17	; lookup_table
	dc.l $D1607CE7,$9FF26280,$0539E0A1,$73A1C028	; lookup_table
	dc.l $3B0018C1,$54082623,$CA98C2E8,$5F883805	; lookup_table
	dc.l $07A00312,$BF00BC66,$2081F3D1,$C0C4391A	; lookup_table
	dc.l $055B6336,$2EAEC640,$BAB8C0EF,$1B179404	; lookup_table
	dc.l $940E541A,$0C1C6279,$1FB71C1F,$C1A47F88	; lookup_table
	dc.l $4A770404,$8A073805,$06C0FFE8,$8B58C6F7	; lookup_table
	dc.l $022CE003,$111F41FE,$41C0283A,$07FF8470	; lookup_table
	dc.l $0880403E,$060C4BDF,$037E8310,$64701ACD	; lookup_table
	dc.l $857F7BEF,$1EDEEFE3,$50263CC6,$7C09A21C	; lookup_table
	dc.l $A8341C70,$81F80F07,$78087420,$E7FA07F6	; lookup_table
	dc.l $9C280C50,$3D5A0FFB,$D0C00803,$BDDD8417	; lookup_table
	dc.l $00041968,$F405E41C,$028340FF,$F83FFDFF	; lookup_table
	dc.l $10880100,$E9D0C568,$0FE0621C,$8EF5B00B	; lookup_table
	dc.l $BAFD150A,$6FCCD304,$625D9EE1,$93839506	; lookup_table
	dc.l $830C1802,$0220D7F1,$07083980,$E6334B04	; lookup_table
	dc.l $44460E03,$41FEFE02,$8660639B,$B0C6C101	; lookup_table
	dc.l $888F987F,$A0E0141C,$0777803F,$97F9C647	; lookup_table
	dc.l $0CA0C420,$79003101,$46CCB802,$8D7A860B	; lookup_table
	dc.l $177CA784,$709B3B31,$99039C06,$83043401	; lookup_table
	dc.l $0830D0E9,$030832FF,$E0D9C1E4,$58E0E701	; lookup_table
	dc.l $A0FDFA20,$1D604047,$FFFDE180,$30C63F08	; lookup_table
	dc.l $EF41C068,$3D5018DD,$1FEFEE00,$00943102	; lookup_table
	dc.l $07E93F09,$2C146B80,$5A1BF2BC,$98DA6727	; lookup_table
	dc.l $A9DAE7FD,$8E2C1C62,$2C181080,$830E9808	; lookup_table
	dc.l $2111FF81,$44078775,$07AC8307,$D80601C0	; lookup_table
	dc.l $019F4311,$85BFBFC1,$16F0701A,$0E83D00D	; lookup_table
	dc.l $1DD7F984,$0C4281FF,$FC57A096,$051AC00F	; lookup_table
	dc.l $06BADB96,$3CF9487E,$31F9FBA1,$930795EB	; lookup_table
	dc.l $06E10C73,$67000B19,$07FC6020,$5C2EE079	; lookup_table
	dc.l $C0307D00,$2408A5B9,$BFFCF0F0,$312FF897	; lookup_table
	dc.l $C8380307,$E0038086,$08640031,$025D319B	; lookup_table
	dc.l $C040C28F,$6202FF9E,$96983D42,$5619CC1C	; lookup_table
	dc.l $F4330D83,$D5018330,$015E08DC,$5100BD99	; lookup_table
	dc.l $07FCF842,$C0AC60E3,$8060FE20,$48112310	; lookup_table
	dc.l $5E2C3F08,$319FCF39,$D054060F,$80061122	; lookup_table
	dc.l $1E001C8A,$06207F0F,$E048D10E,$47B1057F	; lookup_table
	dc.l $C27A23F6,$48D39C77,$BCFC03D6,$C1CE00C1	; lookup_table
	dc.l $9441BE01,$6362873E,$EE0F7C21,$813E1400	; lookup_table
	dc.l $E70060FC,$00C07F00,$C33FC804,$3C203BC5	; lookup_table
	dc.l $FF83DE83,$10B07060,$2CE80027,$5281FF7B	; lookup_table
	dc.l $C363851D,$C00CFF5B,$5853E020,$F784E468	; lookup_table
	dc.l $E8C03B07,$E5EB0605,$F216F1ED,$0749313F	; lookup_table
	dc.l $73F21880,$2181183D,$80302F08,$722F1781	; lookup_table
	dc.l $FFFBFF9E,$5E854060,$FA00E18C,$420C3867	; lookup_table
	dc.l $C073860C,$04361B00,$3C7694DD,$48102101	; lookup_table
	dc.l $EE74F794,$080B0706,$23078009,$0439E133	; lookup_table
	dc.l $F8C7CB3A,$7FF11F11,$4D583B00,$774E00F8	; lookup_table
	dc.l $6A280F81,$FC3A044C,$064860F0,$01FE9181	; lookup_table
	dc.l $6EA0831F,$0B81EA72,$3C0032CB,$317869A3	; lookup_table
	dc.l $7561F73F,$DDFE3050,$4E0E701A,$0C4011D0	; lookup_table
	dc.l $F3211C78,$227B8D1C,$08800008,$43838DA1	; lookup_table
	dc.l $830708C0,$37381E00,$1EFC00FE,$8D0F1C83	; lookup_table
	dc.l $60183070,$717502C5,$EA061603,$B8D07020	; lookup_table
	dc.l $B0CAAE00,$6BC25AF3,$01436EAC,$7DC2BA4F	; lookup_table
	dc.l $FA0FD686,$0C068025,$B0EA00FF,$CFDFCFE0	; lookup_table
	dc.l $47516C01,$83CE0683,$C001E00F,$14C06FC0	; lookup_table
	dc.l $F0F70340,$FE8840C2,$C6604B1A,$0C403FB1	; lookup_table
	dc.l $0C021E11,$F8811020,$61E13031,$0E47C03A	; lookup_table
	dc.l $3147BDC5,$438BFCC7,$DE1457F8,$00D38701	; lookup_table
	dc.l $20D0008C,$04B82F18,$3FBF3BC7,$DF831EBA	; lookup_table
	dc.l $8041C824,$38A8683E,$01E1840B,$F010310E	; lookup_table
	dc.l $0FFF840E,$D0202064,$25070006,$A03FD1FF	; lookup_table
	dc.l $BEC31010,$60E2F031,$0A465560,$1DDE53DD	; lookup_table
	dc.l $C5D202AA,$C8F591F6,$690367EC,$28380002	; lookup_table
	dc.l $0246CF8C,$3F85C00F,$ED0F8CB7,$04CB120A	; lookup_table
	dc.l $AC1EC1EC,$21A7C078,$5009F83D,$2A0E1D03	; lookup_table
	dc.l $80907800,$7D07DD9F,$F4862E07,$E502808C	; lookup_table
	dc.l $0C18084C,$32A9C11D,$78EDBE46,$9012AB9C	; lookup_table
	dc.l $38054BF0,$10A70E01,$4180CA3C,$D37A47FB	; lookup_table
	dc.l $FCF0E247,$78FF5681,$071860E0,$683FC7A0	; lookup_table
	dc.l $A00F00EA,$728EC310,$3061E81C,$04838001	; lookup_table
	dc.l $E47DF624,$31703F61,$051F8188,$7237C0E9	; lookup_table
	dc.l $A46B0EEE,$B61C5B33,$F846EF42,$F4C29580	; lookup_table
	dc.l $9069964E,$1327FCFE,$6C3885D8,$0F720144	; lookup_table
	dc.l $8158701A,$0DF1D008,$030077F1,$98171806	; lookup_table
	dc.l $0ACA02A0,$306E1F50,$F1131820,$61C57E06	; lookup_table
	dc.l $81880A39,$C33C9611,$D26DCFFD,$9BE95CCF	; lookup_table
	dc.l $A940FCD8,$0D062CC9,$E05CFC1D,$4F810960	; lookup_table
	dc.l $B5190226,$EA5831CE,$8818D000,$152E9210	; lookup_table
	dc.l $37205C01,$831AF481,$00971462,$081BF80C	; lookup_table
	dc.l $4051865C,$59C5E3ED,$77B01E5B,$5031F37F	; lookup_table
	dc.l $45A6EA18,$30848F07,$7F83CA3D,$CD1D7E70	; lookup_table
	dc.l $60013752,$C187E807,$A0C21517,$FFD81C14	; lookup_table
	dc.l $E4170060,$C37A2040,$3F602010,$E2BF80C4	; lookup_table
	dc.l $25181380,$383C7FAF,$83056FF2,$31B44FF0	; lookup_table
	dc.l $2A0E0183,$009000FD,$F0F9A1C5,$7E03B9CB	; lookup_table
	dc.l $760044C2,$6CB062B5,$85DC020B,$7C18B040	; lookup_table
	dc.l $CF001C06,$0C0B421C,$020F3050,$B040CFC1	; lookup_table
	dc.l $F4428C07,$8331FC5B,$AE871218,$ECBE2649	; lookup_table
	dc.l $E80B0A82,$C19061FF,$F4F990E2,$4FE2683B	; lookup_table
	dc.l $36021161,$C0683800,$1404668E,$E0302B70	; lookup_table
	dc.l $0A81031E,$01C01830,$1A08700E,$70A5E103	; lookup_table
	dc.l $BF1F865E,$723C080C,$33B0F0DC,$E62D58BF	; lookup_table
	dc.l $60619BE6,$D43F0706,$84089FE5,$EFFEFE06	; lookup_table
	dc.l $09F9EE41,$81E072C1,$E06041FE,$9800DC33	; lookup_table
	dc.l $02EF01C1,$4DC07006,$0E02010D,$0DD7F00A	; lookup_table
	dc.l $AFFF0807,$14FC1259,$28CAA6F8,$015E4FF6	; lookup_table
	dc.l $7F96E4FB,$0FF3AC0E,$70160D00,$206443AB	; lookup_table
	dc.l $7FFC3C04,$46C13C00,$2283AA13,$838FF69F	; lookup_table
	dc.l $0178FF1F,$FEE4C14C,$809B4E0E,$3FE67FFB	; lookup_table
	dc.l $05C2A204,$0CF81620,$28D00003,$FFB3C2B6	; lookup_table
	dc.l $BFCE5FFC,$8B5D064F,$18395018,$34081002	; lookup_table
	dc.l $408F493F,$F23804DD,$09B26046,$0E64960D	; lookup_table
	dc.l $043F2B3C,$03B3FB1F,$FEFE038C,$47F7503F	; lookup_table
	dc.l $03068180,$1FEC9FFF,$42BC6067,$F7D01885	; lookup_table
	dc.l $461CF9AE,$09AEFDDC,$C0A1CD1E,$9840C438	; lookup_table
	dc.l $309C8C40,$719FD080,$02002320,$18020F70	; lookup_table
	dc.l $060F020C,$3AD0DFE3,$83FBC7FF,$7D0398C3	; lookup_table
	dc.l $EB10380B,$07061F99,$EF8310E0,$63FB9031	; lookup_table
	dc.l $0146C43E,$061F5637,$FF63BB97,$F7F01CD2	; lookup_table
	dc.l $2C8B06E1,$5010831F,$3D017109,$81300620	; lookup_table
	dc.l $60731030,$6A82A1A2,$0380FBF9,$431BF407	; lookup_table
	dc.l $11503837,$0AC38610,$00C0CC67,$E2A88323	; lookup_table
	dc.l $70168C29,$80F7FFEF,$5FFBE0B8,$040E3806	; lookup_table
	dc.l $0E000E02,$801C3F19,$020224BC,$7C0901DF	; lookup_table
	dc.l $8AB00A0D,$C06A1078,$0CFF8863,$50E087D0	; lookup_table
	dc.l $60E00C19,$897623E1,$00140FFC,$3F811F45	; lookup_table
	dc.l $28C70742,$16C78EFC,$9DDD9594,$7784178A	; lookup_table
	dc.l $C18101C2,$200C3E78,$40D81052,$84816040	; lookup_table
	dc.l $E70060D0,$00702A10,$7816F8F8,$1ADFB2FB	; lookup_table
	dc.l $0C1C0183,$C0038385,$601FFF9F,$8310207D	; lookup_table
	dc.l $FA10310D,$4641C197,$33E937C1,$E9FEBFDA	; lookup_table
	dc.l $81CA8021,$90200C0F,$0D320FC9,$AF523220	; lookup_table
	dc.l $75720866,$1408FC1D,$A4311A1F,$B89D9C1C	; lookup_table
	dc.l $07832060,$9EFFF327,$44503E90,$3D16A32A	; lookup_table
	dc.l $B59C1E02,$9B77FFF7,$D83F203A,$5E783904	; lookup_table
	dc.l $010BF84F,$59290522,$42090C0E,$2A010F01	; lookup_table
	dc.l $3903EF07,$137D6FDA,$0F610310,$21E04EFF	; lookup_table
	dc.l $A0386445,$C7D204B1,$A8C72AD1,$8EE04FED	; lookup_table
	dc.l $BFF5D04F,$880E701E,$0C820880,$7C4BEC07	; lookup_table
	dc.l $134E9411,$03AB9043,$C0839DA0,$FC26C47E	; lookup_table
	dc.l $59F404EC,$4380F07E,$10676831,$06060800	; lookup_table
	dc.l $06D46618,$101CB33F,$E3BB79BB,$E5C1B86B	; lookup_table
	dc.l $5E0C8002,$0632780B,$8890B003,$60012807	; lookup_table
	dc.l $310F07A0,$0F0121FD,$FFDFF3FF,$F70C7781	; lookup_table
	dc.l $CC43C1F8,$00727F04,$00103FF8,$482B96A3	; lookup_table
	dc.l $1C291C1B,$4E3AD7EC,$DC31E807,$38070650	; lookup_table
	dc.l $800801C4,$F92C4132,$04C10622,$41CE01C1	; lookup_table
	dc.l $984040E2,$C501058F,$CF018A94,$1B0DE0CE	; lookup_table
	dc.l $3801C00F,$89817B80,$C45987E0,$621A8E00	; lookup_table
	dc.l $0391587A,$E0777EDB,$F818D807,$2A008713	; lookup_table
	dc.l $447809E0,$90124022,$86007380,$F0740038	; lookup_table
	dc.l $8C7FD7E3,$A7C9B14B,$80E0021F,$001EA89B	; lookup_table
	dc.l $7FBE1017,$FFB07A0C,$41D19B33,$C52072A5	; lookup_table
	dc.l $5DF506C1,$EE043D08,$12603501,$32CD1032	; lookup_table
	dc.l $070321DD,$00E2FC3F,$80AC7011,$0F000625	; lookup_table
	dc.l $8FFFBFFE,$FF268806,$3FE4E0EE,$B73ED6B6	; lookup_table
	dc.l $150543B1,$09164916,$940261C0,$643BE01C	; lookup_table
	dc.l $5F6E7F68,$380A87F9,$FE1FFAFF,$FBFE07C3	; lookup_table
	dc.l $100C7163,$9945C3CF,$B4230A86,$E82768B1	; lookup_table
	dc.l $D10549C0,$28680038,$BF9B3D90,$70150F03	; lookup_table
	dc.l $FC7FE9D3,$EA862118,$D0278EC7,$F33D33D9	; lookup_table
	dc.l $54150D04,$9182C040,$C2838150,$E78FDFB6	; lookup_table
	dc.l $3B087015,$0E03FCFD,$EBA3D3FD,$838150DB	; lookup_table
	dc.l $81618E46,$3F3F978B,$C034D802,$87101D08	; lookup_table
	dc.l $00814543,$80A865C7,$FF7F1F1F,$94380287	; lookup_table
	dc.l $01DE7FFB,$D1D1FEC3,$100C700C,$87D8FC8D	; lookup_table
	dc.l $172C380A,$860C4270,$20209143,$80A86887	; lookup_table
	dc.l $DFFD8E0E,$34380A87,$8E7FFDE8,$C0FF4310	; lookup_table
	dc.l $8C78A79C,$8ECE0A94,$380A8604,$24371060	; lookup_table
	dc.l $614380A8,$70239FBE,$8A049438,$0A87063F	; lookup_table
	dc.l $FDF0C046,$884C7003,$3FFF5838,$01861904	; lookup_table
	dc.l $08838018,$613FEFC8,$3801861F,$FAF48310	; lookup_table
	dc.l $AC672C50,$38098648,$2D038098,$67045038	; lookup_table
	dc.l $09867C79,$0D10AC63,$81B0C400,$700B0C68	; lookup_table
	dc.l $0700B0C7,$81001FEE,$002F0460	; lookup_table
	dc.b $00,$10
abs_0_00042B8E:
	dc.b $00,$00,$1E,$28,$00,$00,$4C,$90,$66,$18,$C8,$D6,$80,$0F,$F7,$00
	dc.b $1F,$EE,$00,$17,$58,$A8,$15,$33,$10,$EC,$62,$31,$94,$C7,$03,$29
	dc.b $83,$87,$B3,$80,$06,$C6,$54,$01,$CC,$70,$32,$99,$50,$76,$31,$C0
	dc.b $CA,$65,$41,$D8,$C5,$79,$A9,$C5,$00,$C3,$31,$0F,$F6,$14,$1D,$0C
	dc.b $C4,$3F,$D8,$50,$74,$33,$10,$FF,$61,$41,$D0,$CC,$43,$FD,$85,$07
	dc.b $43,$31,$0F,$F6,$14,$1D,$0C,$C4,$3F,$D8,$50,$74,$33,$80,$D8,$66
	dc.b $20,$FC,$D6,$8B,$81,$98,$84,$C3,$39,$46,$06,$38,$0A,$8D,$50,$34
	dc.b $19,$50,$34,$37,$C0,$A0,$67,$00,$E0,$D0,$B2,$81,$87,$E0,$40,$E0
	dc.b $08,$18,$E0,$14,$30,$F4,$08,$22,$14,$59,$1A,$1E,$00,$2A,$F9,$81
	dc.b $E8,$86,$43,$BC,$02,$06,$54,$0D,$0F,$FC,$16,$D5,$2A,$00,$86,$60
	dc.b $14,$0E,$FC,$03,$3D,$31,$0F,$06,$E0,$94,$0C,$3E,$03,$D5,$03,$80
	dc.b $30,$FC,$1F,$E1,$18,$D3,$10,$E8,$7C,$60,$2A,$05,$87,$18,$D2,$A0
	dc.b $F0,$6F,$E0,$E8,$86,$07,$CA,$03,$10,$C8,$62,$80,$40,$CC,$6A,$C0
	dc.b $0E,$02,$C3,$63,$00,$E0,$64,$3B,$46,$50,$63,$F0,$30,$CF,$0A,$70
	dc.b $1E,$0C,$12,$54,$0A,$5E,$0A,$01,$25,$8E,$86,$40,$00,$E2,$92,$C3
	dc.b $43,$AB,$E9,$88,$0C,$3F,$C0,$12,$C2,$C3,$03,$01,$50,$24,$39,$88
	dc.b $60,$64,$05,$31,$00,$87,$F6,$02,$AE,$20,$6B,$11,$F9,$47,$00,$A1
	dc.b $C0,$01,$8A,$06,$01,$88,$2C,$3F,$10,$15,$02,$C3,$0F,$01,$50,$68
	dc.b $3D,$76,$20,$64,$17,$D8,$36,$02,$81,$BF,$FE,$C0,$C4,$12,$1C,$70
	dc.b $50,$36,$08,$FC,$A3,$81,$50,$F8,$20,$C0,$18,$82,$C3,$E3,$01,$50
	dc.b $74,$36,$01,$AC,$12,$A0,$90,$7D,$DD,$40,$FF,$FB,$E0,$73,$0C,$0F
	dc.b $E8,$07,$A9,$90,$C5,$0A,$62,$3D,$40,$1C,$0E,$86,$62,$23,$20,$31
	dc.b $02,$87,$C8,$14,$0D,$22,$4A,$83,$21,$9A,$21,$03,$DC,$29,$C0,$08
	dc.b $31,$62,$A0,$61,$15,$03,$02,$B5,$7D,$40,$62,$09,$0F,$7C,$02,$10
	dc.b $10,$0C,$4B,$A8,$01,$C0,$28,$60,$00,$70,$DF,$B8,$23,$30,$18,$81
	dc.b $43,$7F,$02,$5C,$10,$37,$D9,$2A,$04,$87,$00,$00,$71,$01,$68,$C4
	dc.b $28,$3D,$02,$84,$16,$54,$FF,$F7,$BF,$02,$03,$D6,$03,$10,$48,$77
	dc.b $FC,$75,$E0,$38,$31,$10,$0A,$88,$0E,$01,$43,$30,$FE,$81,$8D,$C1
	dc.b $33,$80,$C4,$0A,$1F,$A2,$50,$31,$F0,$15,$01,$43,$0E,$81,$F8,$21
	dc.b $C0,$25,$41,$A0,$F8,$2B,$81,$9A,$D3,$C1,$CF,$B7,$E0,$76,$13,$10
	dc.b $88,$7E,$C6,$A0,$1C,$03,$E4,$91,$89,$C0,$31,$19,$0C,$03,$1A,$01
	dc.b $37,$00,$0E,$29,$F0,$1E,$A6,$43,$FF,$00,$74,$B1,$21,$89,$50,$64
	dc.b $3B,$F9,$0F,$E0,$CF,$41,$88,$58,$3F,$A2,$60,$77,$FE,$9E,$9F,$F8
	dc.b $5C,$BB,$CF,$C8,$50,$31,$09,$0D,$FD,$D8,$11,$11,$50,$FD,$07,$F9
	dc.b $06,$07,$03,$21,$C0,$7C,$42,$62,$E0,$DF,$81,$64,$62,$19,$0F,$8A
	dc.b $18,$19,$7B,$4A,$80,$21,$E0,$00,$C4,$4A,$A6,$08,$A8,$34,$1E,$03
	dc.b $30,$39,$F7,$08,$6D,$5A,$33,$FA,$02,$FA,$0A,$F1,$41,$C6,$00,$83
	dc.b $45,$06,$25,$00,$7E,$E0,$81,$83,$8E,$C8,$60,$0C,$10,$50,$9F,$F0
	dc.b $23,$EF,$CF,$C0,$68,$62,$09,$0F,$2E,$38,$19,$50,$64,$3F,$00,$50
	dc.b $43,$F0,$10,$E8,$31,$03,$06,$FE,$0C,$56,$E0,$77,$5F,$D7,$E8,$90
	dc.b $BD,$81,$80,$52,$58,$88,$76,$20,$50,$A0,$3F,$DC,$00,$20,$08,$7A
	dc.b $89,$0C,$00,$82,$1A,$13,$F8,$04,$7F,$FB,$F9,$0C,$43,$21,$E5,$C7
	dc.b $03,$31,$0C,$87,$F0,$02,$AB,$F2,$04,$01,$88,$18,$31,$8C,$A0,$7F
	dc.b $F7,$E7,$2A,$98,$C0,$9F,$40,$21,$5B,$BF,$C0,$C4,$12,$18,$3A,$40
	dc.b $07,$00,$09,$1E,$28,$A8,$E3,$92,$18,$04,$84,$24,$AF,$E0,$0E,$14
	dc.b $08,$03,$10,$90,$F2,$E3,$81,$95,$06,$43,$24,$83,$DE,$20,$91,$50
	dc.b $30,$18,$84,$83,$1F,$01,$40,$70,$3B,$E0,$4C,$47,$12,$8B,$FF,$03
	dc.b $72,$90,$69,$80,$20,$F7,$C5,$60,$63,$03,$83,$12,$C6,$00,$81,$5E
	dc.b $64,$3D,$80,$12,$5F,$00,$31,$8E,$2F,$81,$2A,$00,$87,$C2,$0E,$40
	dc.b $20,$75,$B1,$88,$64,$36,$08,$3D,$C2,$06,$20,$E0,$E3,$C0,$34,$C2
	dc.b $0F,$05,$28,$1A,$D9,$47,$00,$21,$86,$80,$60,$07,$E3,$12,$83,$00
	dc.b $F9,$40,$E0,$24,$3E,$E0,$12,$5E,$00,$20,$10,$5F,$E4,$3D,$44,$87
	dc.b $FF,$E1,$0E,$40,$20,$70,$60,$31,$0C,$87,$89,$7F,$8F,$F0,$22,$80
	dc.b $A6,$20,$A0,$F8,$2B,$81,$CF,$FA,$FE,$A0,$A8,$A0,$1F,$F0,$C0,$8C
	dc.b $40,$21,$FF,$F4,$01,$C0,$0F,$9F,$7C,$40,$00,$00,$70,$58,$F5,$22
	dc.b $1F,$8F,$FB,$EF,$00,$08,$25,$0E,$23,$10,$C8,$68,$93,$FC,$FE,$40
	dc.b $C0,$C4,$1A,$19,$F8,$1A,$A0,$30,$18,$81,$83,$E0,$AE,$06,$7E,$09
	dc.b $F8,$FF,$7E,$FE,$80,$83,$E6,$01,$CA,$84,$70,$02,$1C,$20,$38,$E3
	dc.b $F3,$E8,$4D,$D2,$D2,$38,$11,$0F,$E0,$1A,$16,$02,$0C,$0E,$04,$C4
	dc.b $12,$1E,$F2,$10,$37,$FC,$0C,$14,$18,$86,$43,$80,$01,$84,$E6,$01
	dc.b $02,$88,$41,$31,$05,$07,$F2,$03,$80,$E0,$73,$40,$5E,$48,$38,$87
	dc.b $23,$01,$31,$01,$07,$93,$2E,$81,$40,$D8,$80,$80,$11,$AD,$42,$C1
	dc.b $40,$31,$04,$87,$01,$F9,$04,$F8,$02,$02,$07,$17,$88,$0C,$41,$21
	dc.b $9F,$80,$DF,$A8,$1D,$44,$62,$15,$0F,$84,$0C,$00,$40,$CC,$42,$41
	dc.b $FF,$FA,$40,$54,$38,$1F,$67,$FE,$FA,$05,$46,$83,$BE,$03,$10,$A0
	dc.b $E4,$AC,$F0,$60,$62,$20,$03,$88,$98,$80,$58,$01,$50,$4B,$09,$0D
	dc.b $00,$1A,$17,$18,$0C,$60,$2E,$0F,$44,$12,$C2,$43,$31,$0A,$06,$07
	dc.b $C1,$F6,$83,$10,$A8,$70,$20,$60,$99,$24,$C4,$24,$1B,$F8,$3B,$AB
	dc.b $81,$9F,$FB,$76,$DD,$E0,$82,$0B,$50,$84,$09,$47,$03,$81,$87,$07
	dc.b $03,$7F,$08,$1E,$38,$C1,$24,$06,$60,$2C,$83,$10,$48,$68,$00,$30
	dc.b $B1,$C0,$39,$06,$78,$73,$20,$C4,$12,$1E,$34,$50,$30,$FF,$08,$12
	dc.b $C6,$43,$78,$90,$30,$18,$06,$25,$83,$3F,$07,$75,$70,$33,$FE,$BA
	dc.b $2F,$7C,$50,$4B,$FD,$1E,$C8,$31,$09,$07,$FE,$00,$C0,$E0,$77,$E2
	dc.b $8C,$68,$DF,$91,$F1,$82,$F4,$15,$E2,$43,$00,$01,$C4,$15,$2C,$0F
	dc.b $18,$08,$1E,$AC,$87,$3C,$84,$0D,$FF,$E2,$06,$20,$D0,$C0,$C0,$C1
	dc.b $40,$00,$C4,$34,$1C,$F8,$32,$F3,$81,$DF,$EE,$A0,$77,$62,$80,$5D
	dc.b $00,$2C,$26,$21,$C0,$DF,$C1,$18,$1C,$0E,$7C,$8B,$07,$87,$01,$C3
	dc.b $18,$AD,$02,$58,$48,$64,$00,$38,$82,$A4,$80,$F2,$3D,$06,$20,$50
	dc.b $F0,$40,$C8,$27,$E0,$5C,$8C,$42,$A1,$B0,$09,$EA,$68,$3F,$F4,$F8
	dc.b $19,$07,$03,$7F,$FD,$80,$D9,$C3,$40,$BC,$34,$C0,$62,$24,$1D,$F8
	dc.b $0E,$A8,$41,$81,$40,$E7,$A2,$28,$61,$16,$60,$62,$05,$0E,$04,$04
	dc.b $82,$21,$F9,$72,$83,$10,$28,$70,$20,$64,$11,$FF,$CF,$94,$15,$E0
	dc.b $C3,$25,$8D,$07,$FE,$4F,$03,$80,$E0,$7B,$F9,$E0,$57,$18,$2A,$02
	dc.b $06,$18,$82,$0E,$08,$43,$01,$81,$E8,$40,$73,$10,$1C,$12,$24,$08
	dc.b $09,$66,$43,$38,$9E,$00,$48,$27,$10,$31,$24,$33,$11,$37,$90,$F3
	dc.b $EC,$04,$06,$25,$43,$2B,$C7,$07,$FF,$73,$0B,$20,$10,$7D,$E0,$2A
	dc.b $02,$07,$18,$03,$82,$8E,$03,$03,$C0,$61,$06,$7E,$A0,$04,$F9,$81
	dc.b $C1,$92,$02,$60,$98,$84,$43,$8F,$01,$C4,$48,$27,$11,$88,$64,$3F
	dc.b $F0,$38,$05,$C8,$7C,$F0,$1A,$0C,$42,$A1,$BF,$80,$4B,$2C,$1F,$FE
	dc.b $64,$2C,$80,$41,$FB,$82,$C0,$A8,$08,$18,$58,$0F,$50,$41,$FF,$F1
	dc.b $C0,$96,$04,$1D,$00,$34,$09,$64,$3F,$82,$0F,$A2,$4B,$11,$0C,$BC
	dc.b $07,$11,$1C,$20,$03,$88,$C4,$32,$1E,$F8,$3F,$B2,$08,$C7,$B8,$3E
	dc.b $06,$21,$50,$FE,$40,$25,$84,$0C,$C4,$04,$1B,$FF,$34,$2C,$82,$41
	dc.b $85,$76,$42,$D4,$7D,$86,$FF,$10,$62,$1C,$0F,$FC,$01,$C0,$20,$EF
	dc.b $DA,$03,$33,$31,$13,$18,$C3,$81,$90,$C8,$19,$C3,$FC,$B0,$62,$51
	dc.b $F0,$68,$12,$C6,$43,$37,$AD,$E4,$3E,$00,$C4,$A8,$78,$20,$2B,$C2
	dc.b $06,$62,$02,$0E,$FF,$C6,$16,$40,$20,$DB,$C5,$EE,$90,$70,$3E,$C7
	dc.b $B0,$18,$81,$06,$FE,$03,$10,$10,$77,$FE,$83,$07,$18,$AF,$9F,$83
	dc.b $F8,$18,$82,$43,$20,$03,$1E,$C6,$C5,$04,$40,$03,$88,$C4,$0A,$18
	dc.b $F8,$29,$06,$F2,$3F,$01,$88,$54,$30,$10,$15,$E1,$03,$31,$01,$07
	dc.b $BE,$01,$50,$90,$60,$E5,$DE,$88,$10,$9C,$FB,$A0,$70,$53,$10,$60
	dc.b $7E,$2C,$20,$CF,$DA,$8C,$7C,$30,$49,$11,$F8,$41,$A0,$46,$4C,$40
	dc.b $21,$F8,$9E,$06,$22,$82,$50,$01,$C4,$06,$03,$10,$48,$62,$40,$40
	dc.b $DC,$FF,$A0,$D0,$62,$15,$0C,$0C,$08,$02,$33,$06,$20,$A0,$C1,$C0
	dc.b $65,$54,$0C,$20,$4F,$E5,$87,$90,$54,$5D,$C5,$A8,$12,$C0,$83,$3F
	dc.b $05,$8E,$10,$3B,$40,$20,$73,$44,$30,$8A,$10,$3E,$26,$64,$12,$C2
	dc.b $43,$A0,$9D,$3F,$10,$C3,$04,$88,$03,$88,$04,$06,$20,$90,$E7,$CF
	dc.b $E1,$AA,$28,$FF,$CF,$DF,$78,$31,$02,$86,$F1,$37,$00,$31,$05,$06
	dc.b $26,$07,$9B,$60,$38,$18,$E5,$40,$03,$01,$3C,$02,$F8,$41,$88,$70
	dc.b $30,$F0,$46,$04,$83,$02,$44,$80,$70,$83,$A1,$3E,$A0,$70,$12,$1D
	dc.b $00,$0E,$26,$00,$30,$41,$00,$38,$86,$21,$21,$EF,$81,$BE,$23,$54
	dc.b $AF,$CF,$F0,$2A,$04,$86,$25,$D6,$09,$68,$A8,$19,$C0,$50,$30,$C0
	dc.b $0C,$44,$83,$C0,$31,$81,$51,$56,$97,$BF,$50,$62,$1C,$0C,$0C,$11
	dc.b $80,$20,$CF,$F0,$12,$50,$1C,$21,$FC,$C4,$FF,$58,$31,$04,$86,$70
	dc.b $2C,$10,$80,$0E,$20,$50,$18,$82,$43,$C0,$79,$86,$58,$8F,$FF,$3F
	dc.b $A0,$C4,$2A,$1E,$B4,$98,$82,$83,$7F,$86,$85,$90,$08,$31,$FD,$08
	dc.b $15,$16,$3E,$D3,$05,$0E,$1D,$60,$02,$06,$02,$03,$D4,$90,$7E,$00
	dc.b $F0,$24,$1C,$F4,$C4,$34,$2B,$41,$03,$6C,$0B,$06,$C0,$03,$81,$23
	dc.b $B4,$3F,$30,$91,$41,$27,$A9,$10,$DD,$C0,$21,$31,$6F,$FE,$61,$F9
	dc.b $E0,$C4,$2A,$1C,$57,$10,$38,$99,$07,$0A,$06,$82,$00,$C4,$90,$7B
	dc.b $00,$31,$84,$23,$FC,$91,$0E,$CC,$18,$83,$03,$7F,$00,$83,$7D,$02
	dc.b $81,$8E,$46,$20,$40,$EE,$46,$FC,$50,$38,$11,$0D,$80,$07,$02,$04
	dc.b $04,$C9,$E4,$70,$2D,$01,$88,$90,$FE,$00,$1D,$12,$0F,$C8,$FF,$3A
	dc.b $02,$58,$21,$98,$81,$03,$01,$01,$89,$63,$21,$2C,$60,$6C,$20,$18
	dc.b $89,$07,$78,$DF,$03,$81,$1F,$03,$A3,$E4,$C1,$88,$30,$33,$F0,$5A
	dc.b $A1,$03,$48,$EA,$07,$F8,$3F,$01,$C1,$DF,$C3,$46,$F4,$C0,$C4,$70
	dc.b $30,$C4,$90,$78,$00,$38,$1D,$E1,$C2,$F9,$13,$40,$E0,$30,$31,$2C
	dc.b $50,$7B,$FF,$90,$31,$02,$07,$86,$02,$48,$A8,$18,$18,$96,$28,$33
	dc.b $10,$10,$6B,$82,$70,$04,$0F,$3E,$96,$07,$00,$A0,$DD,$C0,$70,$50
	dc.b $1C,$5B,$74,$18,$83,$03,$DF,$01,$F8,$48,$3B,$FC,$18,$09,$46,$23
	dc.b $FF,$1B,$BE,$81,$C0,$60,$64,$00,$18,$89,$07,$80,$03,$81,$31,$10
	dc.b $07,$23,$04,$0E,$03,$03,$0C,$45,$07,$BF,$83,$0C,$48,$C4,$08,$1C
	dc.b $78,$0C,$40,$A1,$AA,$C9,$54,$DA,$D3,$80,$20,$61,$FA,$70,$38,$09
	dc.b $06,$B4,$77,$40,$83,$8A,$FF,$FD,$5D,$4B,$1E,$BC,$C0,$E7,$F9,$E0
	dc.b $98,$12,$0D,$91,$1E,$1B,$F3,$41,$18,$56,$40,$70,$18,$1D,$03,$08
	dc.b $36,$0A,$00,$07,$02,$C1,$60,$03,$F6,$60,$01,$88,$44,$3D,$F7,$E7
	dc.b $FE,$0C,$1D,$11,$03,$1F,$01,$50,$30,$33,$10,$B0,$63,$E0,$70,$9A
	dc.b $22,$06,$54,$0C,$0F,$BF,$1E,$07,$00,$20,$CF,$D4,$0F,$14,$30,$20
	dc.b $54,$F9,$98,$0C,$43,$03,$FF,$00,$8C,$48,$37,$FB,$04,$24,$0C,$12
	dc.b $4F,$E0,$18,$08,$18,$19,$2E,$06,$10,$09,$44,$90,$67,$15,$80,$1F
	dc.b $28,$00,$5C,$58,$00,$78,$87,$E3,$C1,$AF,$F8,$3F,$22,$32,$A6,$22
	dc.b $54,$0C,$0C,$C4,$14,$1F,$00,$0F,$52,$81,$C1,$81,$03,$38,$02,$07
	dc.b $5F,$DF,$03,$80,$10,$77,$FC,$2B,$48,$5D,$42,$07,$3E,$AD,$00,$C4
	dc.b $E0,$61,$C1,$20,$D7,$D8,$59,$F8,$B1,$76,$58,$0C,$18,$07,$46,$21
	dc.b $40,$EE,$3B,$81,$B0,$54,$00,$38,$86,$80,$48,$32,$B6,$00,$0E,$39
	dc.b $81,$EF,$82,$70,$24,$1E,$7F,$0B,$FF,$D6,$27,$6A,$81,$87,$73,$03
	dc.b $31,$0B,$07,$A1,$51,$5E,$90,$69,$FE,$70,$38,$09,$07,$06,$5B,$02
	dc.b $8A,$90,$20,$71,$A0,$15,$E6,$07,$BE,$02,$30,$90,$7F,$F8,$46,$4F
	dc.b $F8,$B8,$62,$07,$06,$00,$DA,$60,$64,$01,$90,$1C,$01,$06,$40,$87
	dc.b $03,$88,$90,$68,$28,$00,$06,$D3,$03,$DF,$04,$CB,$70,$3A,$0B,$3F
	dc.b $0E,$05,$94,$C0,$DF,$C0,$6E,$4C,$0F,$80,$11,$B5,$8A,$0A,$07,$F7
	dc.b $53,$10,$A0,$66,$E4,$C0,$C7,$FD,$A0,$70,$02,$0C,$DC,$22,$4D,$06
	dc.b $25,$D6,$89,$BC,$E0,$62,$14,$0C,$38,$14,$1C,$7E,$C4,$E8,$FE,$0C
	dc.b $40,$81,$81,$00,$C0,$98,$1A,$00,$2C,$07,$00,$41,$E8,$1C,$4F,$7F
	dc.b $E0,$C4,$28,$18,$E0,$30,$3B,$F0,$50,$37,$03,$A0,$B9,$FE,$27,$D0
	dc.b $68,$0C,$0C,$7E,$18,$1E,$00,$28,$1B,$81,$FD,$11,$03,$2A,$0A,$06
	dc.b $57,$9C,$0C,$FC,$0D,$D1,$20,$C9,$F1,$50,$28,$31,$0A,$5F,$FB,$6E
	dc.b $64,$18,$80,$43,$2F,$62,$C3,$8F,$C7,$69,$10,$34,$2E,$E8,$0E,$00
	dc.b $43,$C8,$9F,$C3,$7F,$C0,$E0,$10,$30,$11,$E8,$0E,$00,$43,$F3,$05
	dc.b $D1,$08,$3E,$10,$15,$00,$43,$E0,$02,$06,$34,$44,$0C,$F5,$02,$1F
	dc.b $FF,$6D,$1C,$06,$81,$24,$07,$1F,$04,$79,$03,$D5,$C0,$F3,$02,$41
	dc.b $FD,$D8,$FF,$A0,$BE,$BF,$78,$3C,$E8,$25,$80,$86,$00,$18,$9C,$01
	dc.b $82,$42,$82,$1F,$00,$1E,$60,$70,$02,$1F,$88,$05,$00,$41,$E1,$80
	dc.b $A8,$02,$19,$80,$95,$05,$03,$31,$08,$87,$FE,$95,$D4,$8D,$00,$A0
	dc.b $73,$11,$90,$38,$87,$03,$C1,$9A,$86,$40,$C4,$08,$18,$3B,$FB,$87
	dc.b $46,$07,$00,$21,$83,$01,$F2,$31,$2D,$44,$1E,$71,$01,$C0,$F0,$7F
	dc.b $E0,$EB,$6D,$20,$50,$3C,$70,$15,$00,$43,$31,$06,$06,$7F,$44,$0C
	dc.b $A8,$3C,$1C,$CF,$94,$09,$08,$81,$9F,$CF,$2F,$A0,$AF,$38,$1E,$60
	dc.b $48,$30,$20,$38,$18,$81,$03,$CF,$7F,$3D,$40,$62,$70,$34,$C0,$90
	dc.b $60,$60,$D8,$8C,$41,$81,$88,$00,$8C,$02,$19,$88,$48,$31,$88,$08
	dc.b $7B,$7D,$31,$0E,$87,$7E,$D5,$07,$CC,$A0,$71,$FB,$E0,$FF,$58,$31
	dc.b $0F,$06,$FF,$06,$02,$81,$68,$20,$66,$30,$6E,$64,$07,$03,$C1,$C0
	dc.b $01,$C3,$42,$23,$29,$8C,$04,$61,$01,$C0,$F0,$67,$E0,$DB,$6E,$06
	dc.b $0C,$52,$0D,$C8,$04,$1E,$1B,$4F,$3A,$1D,$44,$0C,$E0,$1C,$1B,$FD
	dc.b $8C,$11,$5A,$81,$EF,$A7,$A9,$E0,$60,$18,$B8,$1A,$60,$70,$3B,$FC
	dc.b $18,$6F,$C5,$03,$DC,$A2,$72,$E0,$38,$1E,$0F,$00,$1B,$F2,$46,$14
	dc.b $0C,$18,$B2,$03,$81,$E0,$C7,$C0,$28,$12,$0F,$BC,$07,$79,$C0,$CA
	dc.b $83,$81,$EA,$D7,$26,$C5,$82,$07,$43,$15,$03,$83,$CF,$64,$86,$85
	dc.b $EA,$09,$01,$EF,$4F,$CB,$E5,$C1,$88,$78,$3E,$F0,$24,$0E,$50,$01
	dc.b $9A,$7F,$8F,$CC,$81,$C0,$08,$66,$22,$48,$53,$D8,$F8,$5E,$03,$81
	dc.b $E0,$C3,$C1,$28,$12,$0F,$DC,$05,$41,$E0,$ED,$AA,$1A,$DC,$A1,$0F
	dc.b $01,$50,$78,$36,$76,$D8,$1D,$85,$03,$FC,$6F,$67,$41,$C4,$38,$14
	dc.b $0E,$64,$B8,$1F,$FB,$BA,$12,$34,$2B,$C0,$4C,$0F,$C0,$FC,$EF,$86
	dc.b $07,$03,$C1,$BC,$01,$6B,$A8,$19,$88,$FF,$04,$40,$70,$3C,$1C,$38
	dc.b $25,$02,$41,$FC,$00,$A8,$18,$1A,$00,$0A,$83,$81,$88,$08,$AB,$5C
	dc.b $3E,$21,$41,$03,$80,$A8,$3C,$1D,$FB,$C4,$18,$1C,$11,$24,$0A,$CE
	dc.b $FF,$03,$10,$10,$69,$81,$C0,$CC,$F9,$E0,$D1,$B5,$7C,$5D,$E0,$DF
	dc.b $9E,$C0,$62,$01,$0C,$F0,$01,$F1,$05,$91,$24,$C2,$2F,$80,$31,$00
	dc.b $87,$86,$0B,$E0,$10,$6F,$E0,$31,$0E,$06,$54,$02,$0C,$C4,$AF,$E0
	dc.b $1E,$A2,$06,$62,$02,$0F,$7C,$07,$00,$20,$CC,$46,$5F,$C0,$70,$54
	dc.b $5A,$4F,$88,$1C,$5C,$01,$40,$E5,$13,$81,$FF,$8B,$87,$7F,$40,$7F
	dc.b $50,$92,$95,$A7,$3D,$FE,$50,$38,$0C,$0F,$00,$09,$79,$C0,$C7,$3C
	dc.b $20,$62,$04,$0F,$81,$FD,$F3,$E0,$14,$81,$89,$C0,$E6,$23,$81,$F1
	dc.b $80,$E2,$B8,$1E,$44,$54,$1C,$0F,$3C,$7D,$E1,$81,$F7,$31,$03,$8E
	dc.b $A6,$06,$70,$14,$0C,$DF,$E6,$05,$79,$C0,$FE,$9E,$7F,$00,$B0,$20
	dc.b $23,$F1,$90,$96,$8C,$41,$81,$97,$80,$18,$B8,$18,$7D,$E7,$F0,$1E
	dc.b $02,$86,$FF,$7C,$7F,$83,$03,$81,$C0,$F2,$01,$20,$38,$0C,$0C,$20
	dc.b $06,$33,$B3,$70,$37,$E0,$91,$23,$80,$C0,$FD,$FE,$E0,$31,$16,$0F
	dc.b $FC,$02,$12,$62,$1C,$0F,$E0,$1E,$06,$21,$20,$CA,$82,$81,$98,$84
	dc.b $83,$89,$00,$1C,$70,$35,$FE,$0F,$BF,$90,$B2,$08,$4F,$FF,$F4,$7F
	dc.b $18,$0C,$4A,$06,$4B,$26,$99,$C0,$CC,$EC,$3F,$21,$FC,$C9,$49,$3F
	dc.b $FF,$47,$A1,$E0,$F5,$28,$19,$05,$04,$23,$01,$C0,$60,$61,$88,$10
	dc.b $60,$B4,$26,$00,$11,$57,$00,$04,$B3,$81,$FE,$80,$12,$18,$1C,$00
	dc.b $28,$3F,$FF,$D8,$12,$C7,$03,$18,$8E,$06,$6B,$27,$E0,$2A,$AC,$B0
	dc.b $81,$95,$07,$03,$64,$00,$C4,$70,$30,$3C,$AF,$2B,$3C,$13,$CF,$FF
	dc.b $44,$B9,$6C,$04,$1E,$AA,$06,$41,$3C,$F1,$40,$70,$18,$1E,$9C,$8F
	dc.b $E4,$7F,$7F,$F3,$FF,$C1,$08,$38,$22,$07,$1A,$8E,$07,$02,$4F,$01
	dc.b $C0,$60,$66,$8C,$10,$CE,$BC,$00,$60,$01,$89,$88,$C3,$12,$C0,$83
	dc.b $18,$8E,$06,$05,$8C,$0F,$F8,$9E,$06,$21,$20,$CC,$83,$81,$F6,$34
	dc.b $FF,$82,$00,$50,$08,$0C,$41,$41,$E1,$80,$E0,$38,$1D,$3E,$9F,$97
	dc.b $3E,$0E,$2F,$FD,$00,$5A,$9C,$F2,$18,$87,$03,$1C,$01,$06,$CF,$C7
	dc.b $F9,$BE,$7E,$4A,$5B,$00,$65,$9D,$06,$20,$20,$FF,$01,$D7,$7A,$05
	dc.b $03,$E8,$7C,$85,$25,$80,$01,$00,$60,$3C,$3F,$00,$C1,$C0,$E0,$7F
	dc.b $FC,$30,$1C,$06,$07,$DE,$00,$C0,$A0,$7E,$00,$21,$29,$50,$30,$3F
	dc.b $C1,$F8,$15,$03,$03,$F0,$01,$88,$50,$30,$F0,$62,$C9,$50,$70,$3C
	dc.b $9C,$98,$1C,$07,$03,$E6,$F6,$8F,$42,$80,$C0,$CD,$24,$A6,$E0,$E3
	dc.b $98,$1F,$FB,$9F,$22,$07,$01,$81,$87,$DC,$C0,$C4,$08,$18,$04,$C6
	dc.b $3A,$0C,$E1,$C0,$60,$70,$44,$70,$1C,$06,$06,$20,$0A,$48,$C4,$A7
	dc.b $11,$FA,$04,$0C,$43,$81,$FE,$83,$08,$B4,$05,$1F,$00,$60,$50,$38
	dc.b $19,$B8,$4B,$45,$41,$40,$D7,$64,$62,$38,$1F,$00,$0C,$42,$81,$BF
	dc.b $02,$45,$88,$18,$1C,$50,$3A,$49,$28,$1C,$07,$03,$FE,$E6,$82,$5C
	dc.b $54,$58,$8B,$A8,$18,$85,$03,$E7,$FF,$F9,$C4,$C0,$70,$70,$3D,$EF
	dc.b $88,$5A,$14,$06,$42,$1E,$07,$03,$81,$40,$C2,$00,$00,$53,$F0,$38
	dc.b $0C,$0E,$80,$FA,$16,$80,$40,$C0,$A4,$1F,$E8,$30,$62,$14,$0C,$82
	dc.b $FE,$01,$AC,$30,$35,$08,$42,$28,$18,$1C,$84,$10,$4A,$4B,$14,$0F
	dc.b $58,$A8,$18,$96,$30,$38,$21,$AD,$29,$88,$50,$3F,$30,$1C,$02,$83
	dc.b $1F,$25,$81,$50,$50,$30,$85,$5F,$D4,$29,$01,$03,$F5,$00,$E0,$48
	dc.b $39,$FE,$F3,$97,$EC,$57,$D6,$00,$1D,$2F,$F3,$03,$80,$40,$CA,$01
	dc.b $00,$02,$0C,$02,$80,$7C,$FB,$1F,$12,$00,$09,$03,$89,$40,$14,$32
	dc.b $41,$61,$60,$10,$06,$96,$B0,$A6,$32,$10,$10,$32,$A8,$3A,$31,$0E
	dc.b $06,$64,$14,$0C,$31,$18,$1C,$AA,$10,$3A,$08,$A8,$28,$1E,$CD,$6F
	dc.b $E5,$01,$50,$E0,$7F,$C6,$38,$08,$39,$12,$A8,$42,$4A,$06,$21,$40
	dc.b $FB,$40,$63,$18,$0F,$A0,$10,$3B,$F0,$7F,$8C,$3F,$C2,$52,$40,$E0
	dc.b $28,$B6,$00,$18,$84,$0D,$E6,$1C,$82,$80,$62,$1C,$0C,$3F,$FB,$0D
	dc.b $01,$52,$10,$03,$89,$7C,$07,$A9,$40,$C8,$07,$D8,$06,$21,$20,$F0
	dc.b $C1,$30,$25,$57,$FE,$FC,$0A,$82,$81,$9F,$00,$C4,$2C,$1C,$4C,$10
	dc.b $33,$D4,$60,$65,$43,$6E,$00,$C4,$10,$63,$F8,$B0,$E8,$15,$02,$07
	dc.b $41,$3F,$03,$72,$A0,$7D,$60,$31,$09,$06,$7F,$85,$E2,$84,$79,$FF
	dc.b $0F,$80,$9F,$4D,$20,$E0,$50,$30,$C0,$0E,$42,$58,$20,$C1,$C1,$A1
	dc.b $18,$88,$80,$0C,$6F,$E0,$1B,$95,$03,$B2,$8C,$40,$41,$EE,$76,$80
	dc.b $4A,$A3,$10,$60,$60,$03,$80,$08,$31,$03,$06,$02,$03,$8E,$90,$65
	dc.b $51,$AF,$F1,$BA,$0C,$43,$81,$FF,$DA,$60,$2A,$0A,$07,$80,$05,$38
	dc.b $C4,$AF,$E2,$3F,$F8,$F8,$3D,$41,$06,$41,$C1,$79,$F7,$8A,$48,$7E
	dc.b $02,$FE,$CB,$03,$80,$40,$D0,$03,$A0,$39,$18,$80,$83,$03,$FC,$BC
	dc.b $41,$88,$90,$00,$3A,$23,$0A,$07,$7E,$0C,$49,$12,$C5,$07,$78,$0A
	dc.b $02,$98,$87,$03,$30,$BE,$A3,$10,$50,$7F,$E0,$70,$15,$42,$06,$40
	dc.b $D4,$0D,$3D,$B3,$CB,$DF,$06,$20,$20,$FC,$E5,$60,$54,$14,$0E,$04
	dc.b $82,$05,$78,$40,$E7,$C3,$FE,$50,$62,$0A,$0F,$98,$82,$14,$82,$7F
	dc.b $00,$FE,$21,$81,$C0,$20,$62,$1E,$01,$08,$31,$09,$06,$03,$F1,$40
	dc.b $83,$11,$40,$01,$C5,$9E,$01,$C0,$20,$6E,$25,$3D,$45,$07,$40,$08
	dc.b $FA,$EC,$08,$C4,$04,$33,$11,$7F,$06,$81,$C7,$10,$30,$C4,$20,$7F
	dc.b $E4,$F6,$7C,$92,$E4,$25,$81,$07,$65,$24,$82,$8A,$92,$E1,$CD,$20
	dc.b $31,$02,$07,$9E,$7F,$E2,$0F,$83,$10,$10,$60,$00,$0D,$83,$A5,$FC
	dc.b $07,$16,$C8,$0C,$40,$81,$84,$60,$09,$FC,$60,$C4,$04,$18,$17,$E6
	dc.b $08,$3E,$09,$28,$00,$1C,$47,$20,$31,$02,$06,$41,$77,$80,$C4,$24
	dc.b $18,$A4,$38,$04,$0F,$62,$F9,$01,$88,$10,$3F,$8F,$F1,$F4,$18,$80
	dc.b $83,$E9,$93,$F0,$1C,$F4,$81,$98,$1A,$74,$79,$E1,$03,$72,$10,$77
	dc.b $EB,$A2,$28,$2A,$0A,$06,$06,$47,$03,$10,$20,$63,$82,$4E,$02,$58
	dc.b $10,$70,$3C,$30,$23,$02,$06,$01,$FE,$C6,$83,$10,$20,$7E,$00,$CC
	dc.b $B6,$00,$62,$02,$0C,$17,$F9,$05,$16,$85,$38,$13,$10,$20,$7D,$12
	dc.b $C4,$62,$02,$0F,$4A,$C1,$01,$50,$10,$37,$CB,$20,$08,$1F,$80,$16
	dc.b $64,$C4,$14,$1D,$41,$10,$33,$8E,$A0,$7C,$10,$C9,$05,$45,$FE,$0C
	dc.b $43,$81,$DF,$D5,$08,$20,$54,$28,$1C,$32,$2C,$0E,$21,$C1,$E3,$BF
	dc.b $E5,$41,$88,$08,$33,$FD,$2E,$04,$18,$81,$03,$01,$01,$C5,$FC,$01
	dc.b $C2,$81,$60,$31,$A0,$31,$04,$1E,$00,$54,$0C,$42,$81,$81,$00,$E2
	dc.b $01,$01,$15,$46,$A9,$F0,$03,$14,$83,$0E,$12,$A0,$20,$7F,$C0,$21
	dc.b $42,$07,$30,$35,$91,$88,$70,$37,$38,$C4,$28,$19,$94,$95,$14,$FD
	dc.b $1A,$29,$03,$06,$21,$20,$D2,$42,$20,$54,$14,$0E,$30,$06,$20,$40
	dc.b $DF,$C0,$2D,$17,$1F,$C0,$C4,$38,$1B,$F8,$DF,$82,$03,$80,$81,$81
	dc.b $FE,$20,$20,$F5,$08,$1D,$04,$3F,$87,$03,$10,$E0,$70,$1F,$50,$38
	dc.b $AD,$0A,$08,$03,$88,$70,$B7,$E0,$A0,$1F,$C0,$18,$80,$83,$FB,$FF
	dc.b $81,$45,$A1,$41,$FF,$20,$62,$04,$0F,$32,$30,$BE,$C0,$18,$8A,$0F
	dc.b $80,$6F,$E8,$81,$95,$16,$3C,$8C,$A4,$12,$D4,$86,$20,$20,$FE,$41
	dc.b $60,$54,$14,$0E,$60,$06,$20,$40,$C7,$C0,$73,$5C,$9E,$40,$C4,$04
	dc.b $1D,$97,$CC,$03,$8B,$FE,$0E,$F1,$01,$81,$C2,$88,$02,$82,$7E,$CC
	dc.b $81,$88,$08,$37,$F0,$18,$C4,$63,$DD,$7C,$20,$40,$D0,$BD,$E0,$A0
	dc.b $1F,$30,$18,$86,$83,$30,$02,$07,$F0,$01,$C1,$18,$84,$87,$C4,$C4
	dc.b $0C,$F5,$28,$1E,$38,$49,$28,$45,$21,$0C,$40,$41,$FB,$81,$C0,$A8
	dc.b $B5,$E0,$E6,$08,$6E,$8C,$44,$3C,$15,$97,$99,$94,$0C,$40,$41,$A6
	dc.b $FE,$C0,$8C,$B0,$E0,$FE,$08,$7B,$87,$06,$B6,$7F,$34,$60,$62,$02
	dc.b $0F,$F8,$01,$D0,$10,$18,$26,$80,$8F,$04,$18,$81,$03,$A0,$2F,$78
	dc.b $0C,$43,$41,$C1,$0F,$78,$7F,$87,$0E,$04,$B3,$21,$E5,$4C,$10,$80
	dc.b $3F,$23,$10,$20,$61,$F8,$10,$38,$8C,$42,$41,$82,$40,$C0,$E0,$A8
	dc.b $E3,$EC,$18,$78,$31,$06,$06,$FE,$61,$03,$10,$10,$61,$1F,$C0,$28
	dc.b $31,$28,$7F,$06,$12,$07,$01,$81,$BF,$80,$C4,$24,$1E,$94,$02,$03
	dc.b $11,$C0,$10,$E0,$21,$C1,$88,$30,$37,$FF,$08,$18,$80,$83,$20,$80
	dc.b $40,$38,$38,$E3,$FC,$1C,$78,$2A,$2D,$7E,$10,$30,$C4,$D0,$66,$22
	dc.b $70,$03,$10,$60,$63,$E0,$AF,$8B,$C0,$31,$12,$0E,$5A,$02,$05,$40
	dc.b $40,$C3,$70,$3A,$10,$4B,$0C,$0C,$BC,$03,$11,$20,$E6,$C0,$46,$04
	dc.b $0C,$1C,$33,$03,$17,$03,$80,$C0,$CB,$C0,$31,$12,$0E,$70,$07,$10
	dc.b $20,$0D,$04,$4F,$00,$AD,$01,$50,$C0,$CB,$C0,$31,$12,$0E,$7C,$05
	dc.b $57,$E0,$0A,$84,$7F,$02,$03,$11,$50,$C0,$C0,$35,$3D,$D1,$88,$10
	dc.b $32,$A2,$D9,$80,$C4,$04,$1E,$26,$04,$0E,$0A,$1E,$19,$01,$2F,$83
	dc.b $12,$CF,$88,$21,$04,$1C,$90,$C4,$04,$1E,$30,$0E,$20,$A9,$07,$08
	dc.b $80,$A5,$C0,$E1,$50,$0A,$69,$65,$30,$88,$62,$02,$0C,$E0,$42,$00
	dc.b $62,$22,$90,$0E,$68,$1C,$2E,$F9,$CF,$3C,$E7,$D9,$0F,$52,$41,$FF
	dc.b $80,$C4,$08,$18,$E4,$04,$34,$A0,$81,$98,$81,$43,$E3,$05,$01,$4E
	dc.b $02,$81,$D8,$00,$C4,$04,$1D,$13,$08,$07,$46,$0E,$04,$B2,$F9,$01
	dc.b $89,$47,$0A,$70,$03,$10,$10,$67,$03,$84,$31,$43,$26,$00,$62,$E0
	dc.b $78,$00,$31,$01,$06,$70,$24,$10,$00,$44,$0E,$27,$70,$0E,$16,$5B
	dc.b $BF,$00,$31,$01,$07,$46,$00,$DB,$E8,$43,$C6,$00,$3B,$F0,$B0,$5B
	dc.b $41,$3D,$45,$07,$A6,$D6,$0B,$C3,$9E,$05,$78,$40,$F8,$00,$81,$D3
	dc.b $80,$C4,$24,$19,$88,$0E,$0A,$54,$2A,$C0,$31,$2B,$01,$4B,$C0,$62
	dc.b $02,$0C,$08,$0A,$17,$50,$D1,$0B,$50,$07,$03,$81,$EF,$80,$C4,$04
	dc.b $19,$C0,$E0,$08,$80,$30,$2A,$60,$1A,$01,$03,$A0,$29,$88,$48,$36
	dc.b $34,$20,$65,$43,$BC,$03,$10,$88,$79,$72,$02,$3C,$00,$3D,$4A,$06
	dc.b $31,$0E,$0C,$0C,$67,$03,$43,$05,$40,$40,$F3,$80,$31,$11,$0C,$04
	dc.b $08,$F7,$50,$8F,$82,$82,$1A,$00,$C4,$44,$30,$20,$1C,$46,$00,$C0
	dc.b $88,$01,$81,$23,$00,$62,$22,$18,$18,$FE,$02,$08,$A6,$80,$6F,$80
	dc.b $62,$11,$0F,$F0,$14,$90,$08,$DC,$74,$A8,$38,$1D,$30,$0C,$40,$41
	dc.b $81,$86,$30,$20,$A8,$28,$18,$80,$0C,$4A,$38,$52,$E0,$18,$80,$83
	dc.b $07,$0F,$40,$47,$0A,$50,$37,$40,$0E,$15,$40,$07,$03,$BC,$03,$10
	dc.b $90,$61,$F4,$04,$28,$C0,$90,$01,$81,$26,$00,$70,$AA,$E0,$1B,$A0
	dc.b $00,$9D,$4C,$0D,$20,$61,$C3,$F8,$38,$70,$54,$04,$0E,$F0,$06,$20
	dc.b $50,$C7,$80,$54,$26,$21,$40,$CE,$00,$81,$D2,$80,$E7,$04,$1E,$18
	dc.b $35,$02,$0A,$82,$81,$D6,$00,$C4,$A3,$85,$2D,$07,$79,$6B,$00,$81
	dc.b $A1,$83,$C0,$40,$E0,$C4,$08,$1D,$20,$07,$0B,$50,$03,$81,$DD,$0B
	dc.b $80,$E0,$70,$38,$40,$76,$04,$2C,$18,$8B,$34,$FB,$D6,$BC,$0A,$06
	dc.b $57,$E8,$0C,$40,$41,$E3,$83,$F0,$61,$E3,$E0,$08,$1B,$E0,$32,$22
	dc.b $81,$E4,$09,$88,$28,$31,$F0,$3F,$CD,$6B,$4A,$8B,$EC,$0A,$01,$43
	dc.b $00,$F9,$70,$3F,$F1,$78,$15,$01,$03,$7F,$00,$E4,$A0,$03,$11,$36
	dc.b $1C,$88,$B0,$0A,$DC,$C0,$D8,$2A,$30,$30,$08,$3C,$63,$81,$03,$C8
	dc.b $00,$E1,$76,$EA,$3E,$01,$F2,$10,$7A,$80,$38,$98,$26,$00,$07,$15
	dc.b $C0,$07,$04,$EB,$A8,$19,$5E,$08,$3F,$70,$38,$08,$7C,$04,$74,$FE
	dc.b $CC,$18,$00,$22,$01,$03,$A1,$4E,$07,$3C,$2F,$E0,$67,$10,$CA,$95
	dc.b $0C,$7F,$EC,$28,$04,$1F,$AA,$07,$01,$C0,$FA,$40,$71,$4B,$80,$E0
	dc.b $08,$19,$40,$0C,$44,$7C,$16,$13,$FE,$EF,$0B,$10,$E0,$7F,$F4,$B0
	dc.b $38,$A1,$80,$38,$04,$0C,$60,$19,$83,$AB,$04,$0F,$E0,$02,$4C,$20
	dc.b $F3,$80,$71,$0C,$80,$D0,$08,$1F,$C0,$07,$04,$F5,$18,$1C,$6D,$08
	dc.b $30,$10,$08,$00,$89,$88,$30,$32,$58,$A0,$74,$B1,$C0,$E4,$2A,$C0
	dc.b $03,$10,$20,$6F,$E0,$2A,$1E,$32,$89,$52,$03,$22,$1A,$86,$18,$87
	dc.b $03,$9F,$01,$C0,$70,$32,$A1,$0E,$B8,$0B,$9F,$CB,$03,$10,$E0,$79
	dc.b $20,$60,$A7,$00,$38,$04,$0E,$60,$19,$82,$3B,$C4,$0F,$C1,$8E,$06
	dc.b $21,$C0,$FB,$81,$81,$11,$02,$D0,$08,$1B,$C0,$0D,$C8,$41,$CF,$80
	dc.b $C4,$38,$1F,$B8,$18,$2B,$E0,$7C,$01,$03,$09,$81,$8B,$81,$BF,$80
	dc.b $C4,$38,$1E,$E0,$A0,$82,$18,$08,$18,$39,$4E,$01,$81,$D2,$B5,$03
	dc.b $60,$9A,$80,$54,$1C,$0F,$30,$06,$22,$38,$0C,$0E,$56,$A8,$1B,$04
	dc.b $AC,$00,$E0,$20,$67,$F0,$10,$56,$13,$10,$E0,$7A,$05,$C8,$02,$06
	dc.b $CA,$0C,$08,$08,$0C,$12,$02,$00,$09,$E6,$32,$07,$10,$28,$1E,$00
	dc.b $06,$23,$81,$BD,$82,$90,$47,$07,$00,$06,$09,$90,$62,$70,$33,$F0
	dc.b $10,$A7,$03,$FE,$01,$44,$02,$02,$A1,$04,$B7,$84,$E0,$18,$19,$00
	dc.b $3F,$4B,$81,$B9,$80,$E0,$28,$1C,$08,$BE,$9A,$0C,$44,$70,$28,$1F
	dc.b $00,$36,$E3,$81,$AC,$00,$70,$08,$1B,$F8,$00,$3E,$7E,$23,$90,$41
	dc.b $A0,$08,$40,$70,$18,$1B,$10,$2C,$00,$81,$C0,$40,$8C,$23,$34,$7F
	dc.b $81,$DC,$14,$0E,$80,$11,$11,$40,$D8,$27,$D0,$15,$05,$03,$81,$1F
	dc.b $85,$04,$62,$1C,$0F,$7C,$7E,$06,$21,$C0,$CA,$21,$A2,$BF,$70,$43
	dc.b $08,$7F,$8B,$E0,$31,$52,$99,$7C,$E4,$1C,$03,$03,$08,$01,$50,$50
	dc.b $30,$20,$18,$81,$03,$5F,$99,$A9,$B4,$66,$BB,$DD,$D0,$E7,$60,$30
	dc.b $32,$E0,$14,$43,$85,$32,$B9,$21,$C9,$C0,$07,$00,$40,$C3,$03,$E0
	dc.b $38,$0C,$0C,$C8,$07,$15,$01,$51,$A8,$81,$FF,$37,$DD,$A0,$7E,$AD
	dc.b $A9,$40,$F8,$04,$F4,$82,$06,$20,$40,$C0,$C0,$54,$0A,$0F,$BC,$04
	dc.b $B1,$C0,$FF,$F7,$E0,$62,$04,$0F,$F0,$05,$40,$40,$F3,$C0,$31,$04
	dc.b $0C,$82,$2A,$07,$00,$C0,$CD,$54,$20,$70,$04,$0E,$04,$06,$20,$40
	dc.b $E7,$C0,$59,$04,$0F,$6B,$8E,$03,$80,$C0,$C9,$40,$51,$18,$94,$04
	dc.b $03,$80,$A0,$C6,$57,$20,$38,$0C,$0C,$E4,$07,$11,$89,$60,$80,$38
	dc.b $04,$0F,$BC,$03,$11,$40,$C9,$63,$81,$9F,$38,$40,$70,$08,$19,$50
	dc.b $50,$36,$28,$60,$66,$20,$20,$E3,$C0,$62,$04,$0D,$F0,$05,$40,$40
	dc.b $C9,$E8,$84,$94,$53,$2A,$61,$E5,$F8,$70,$0C,$0C,$28,$05,$41,$40
	dc.b $EC,$0A,$63,$5B,$B3,$2B,$25,$CC,$E2,$75,$53,$F3,$B0,$18,$18,$9B
	dc.b $04,$10,$80,$81,$C1,$80,$70,$08,$1E,$C6,$EF,$6D,$F6,$1E,$20,$93
	dc.b $88,$0E,$03,$03,$1D,$90,$82,$B9,$10,$36,$40,$0E,$01,$03,$73,$4A
	dc.b $06,$C2,$14,$0F,$80,$47,$BC,$20,$EB,$04,$0C,$75,$A3,$10,$10,$FF
	dc.b $C3,$FF,$C0,$F0,$40,$23,$A8,$40,$FF,$B1,$D7,$7B,$6B,$AC,$F5,$82
	dc.b $38,$70,$1C,$0C,$50,$05,$40,$A0,$CC,$63,$BB,$BE,$52,$A9,$2F,$DA
	dc.b $0E,$07,$03,$18,$E0,$82,$10,$70,$33,$12,$E2,$22,$0D,$6A,$F6,$FD
	dc.b $D3,$08,$38,$18,$F8,$84,$06,$89,$81,$9A,$14,$C4,$28,$1F,$3E,$3C
	dc.b $0C,$40,$41,$80,$80,$C4,$02,$1A,$D3,$30,$33,$08,$3F,$FA,$06,$21
	dc.b $20,$C5,$E3,$40,$04,$11,$0A,$69,$D8,$62,$1C,$0C,$7F,$82,$02,$A1
	dc.b $20,$FF,$9B,$EF,$6E,$FD,$5B,$AE,$F5,$78,$62,$1C,$0C,$67,$80,$05
	dc.b $06,$21,$20,$E2,$10,$91,$02,$A4,$71,$04,$D8,$62,$1C,$0C,$78,$40
	dc.b $09,$06,$21,$20,$CE,$08,$81,$98,$84,$83,$1F,$01,$54,$62,$12,$0D
	dc.b $D0,$18,$19,$88,$70,$3F,$C0,$FF,$C4,$18,$84,$83,$83,$46,$45,$1A
	dc.b $9B,$C4,$09,$61,$88,$70,$33,$30,$15,$02,$83,$23,$0A,$06,$FF,$A7
	dc.b $03,$10,$E0,$67,$E0,$FB,$BC,$00,$38,$02,$0C,$9F,$08,$1C,$00,$BC
	dc.b $0C,$43,$81,$9E,$04,$42,$04,$60,$70,$04,$19,$AE,$10,$3F,$FE,$F8
	dc.b $18,$87,$03,$F3,$A1,$C1,$E6,$04,$0C,$C4,$32,$1F,$C0,$3B,$C2,$3E
	dc.b $09,$81,$95,$0D,$18,$40,$19,$C1,$B0,$02,$BB,$06,$23,$81,$E5,$FE
	dc.b $37,$A0,$A8,$04,$1F,$F5,$BC,$36,$C8,$81,$FD,$80,$C4,$38,$1F,$9F
	dc.b $C2,$3A,$29,$30,$81,$8E,$01,$03,$31,$02,$07,$00,$6F,$03,$10,$E0
	dc.b $7F,$80,$95,$02,$38,$31,$07,$07,$9E,$03,$10,$10,$7F,$9D,$FE,$28
	dc.b $31,$0E,$87,$E0,$06,$20,$1D,$89,$20,$E0,$7F,$51,$6C,$AD,$A2,$9F
	dc.b $BC,$99,$53,$80,$1C,$E0,$24,$1F,$28,$0E,$03,$81,$FC,$5B,$C2,$AF
	dc.b $88,$1D,$78,$0C,$41,$41,$A5,$F4,$46,$08,$18,$32,$24,$38,$00,$81
	dc.b $93,$80,$C4,$14,$1A,$F4,$68,$0C,$0F,$F8,$14,$D0,$40,$CC,$40,$C1
	dc.b $F3,$82,$D0,$18,$19,$8D,$1C,$8C,$0C,$C4,$14,$18,$C0,$24,$83,$81
	dc.b $F7,$60,$B0,$79,$9F,$54,$10,$0B,$F0,$62,$2C,$19,$88,$50,$3E,$00
	dc.b $11,$DE,$60,$4A,$9A,$6E,$98,$0E,$02,$43,$1E,$06,$00,$0C,$00,$40
	dc.b $40,$2F,$5E,$00,$E4,$61,$90,$FE,$41,$C0,$04,$0F,$7C,$06,$21,$E8
	dc.b $DF,$80,$4B,$94,$1D,$18,$05,$8B,$27,$00,$39,$C0,$24,$30,$0F,$BE
	dc.b $FD,$3E,$32,$10,$5E,$C0,$31,$0B,$06,$49,$4C,$0C,$08,$40,$B0,$03
	dc.b $04,$13,$78,$0C,$42,$C1,$EA,$05,$03,$31,$06,$07,$3E,$03,$10,$0C
	dc.b $60,$B6,$8F,$53,$BD,$11,$D2,$F3,$BC,$2A,$03,$07,$C2,$04,$0C,$AA
	dc.b $FA,$00,$80,$10,$35,$DE,$98,$3E,$E5,$03,$4C,$06,$06,$C6,$03,$10
	dc.b $D0,$69,$CB,$D0,$08,$EC,$0D,$07,$38,$03,$10,$A0,$76,$0D,$40,$CC
	dc.b $42,$A1,$D2,$03,$03,$31,$02,$86,$83,$18,$40,$AF,$94,$76,$51,$3B
	dc.b $7E,$01,$CE,$03,$41,$87,$21,$03,$2A,$A4,$00,$81,$F8,$A6,$F4,$A1
	dc.b $79,$38,$1F,$D8,$05,$0A,$C2,$0F,$62,$9F,$FF,$42,$A4,$28,$1A,$F2
	dc.b $F6,$02,$34,$09,$81,$82,$01,$80,$B3,$C0,$7F,$C2,$07,$FC,$0B,$A0
	dc.b $A0,$77,$E0,$31,$00,$C6,$90,$B3,$AB,$EA,$96,$56,$BD,$3B,$BF,$FB
	dc.b $FF,$C1,$81,$E8,$0B,$EE,$0A,$02,$FE,$01,$03,$2F,$00,$FD,$3F,$DE
	dc.b $27,$00,$F5,$F4,$8F,$A2,$F1,$98,$19,$89,$7F,$C0,$62,$30,$90,$7F
	dc.b $F4,$1A,$22,$00,$70,$0E,$E2,$F7,$02,$09,$29,$81,$D5,$51,$03,$31
	dc.b $11,$48,$C0,$06,$20,$C0,$CF,$C0,$62,$1E,$8F,$F8,$8A,$4D,$D9,$26
	dc.b $59,$BC,$86,$73,$BF,$EE,$FE,$80,$83,$85,$07,$03,$28,$A9,$C4,$76
	dc.b $01,$7B,$E6,$FE,$FF,$44,$8A,$EF,$A4,$3F,$E1,$FC,$8E,$64,$40,$FC
	dc.b $C1,$C4,$53,$11,$EF,$FF,$03,$FE,$41,$0C,$80,$80,$E2,$45,$38,$BD
	dc.b $E0,$8B,$22,$A0,$60,$01,$90,$90,$A9,$88,$88,$00,$1E,$7F,$63,$BA
	dc.b $98,$19,$88,$64,$32,$20,$20,$66,$20,$D0,$FC,$94,$23,$62,$77,$F5
	dc.b $70,$86,$67,$7E,$FB,$CF,$E0,$08,$39,$C1,$7B,$40,$40,$3C,$45,$D7
	dc.b $FF,$3D,$00,$5F,$FD,$C9,$64,$85,$BD,$27,$D0,$07,$C0,$40,$E0,$A0
	dc.b $7C,$20,$14,$13,$F6,$08,$22,$58,$E0,$25,$B0,$28,$40,$8D,$B1,$C1
	dc.b $10,$D8,$2F,$7E,$62,$F1,$98,$19,$BD,$3D,$33,$E0,$31,$8E,$00,$0F
	dc.b $9C,$B1,$CA,$14,$0C,$EC,$03,$11,$90,$C7,$83,$81,$98,$86,$43,$84
	dc.b $FC,$10,$3D,$DB,$A7,$6B,$91,$9C,$00,$FA,$13,$24,$A4,$56,$8A,$EF
	dc.b $81,$42,$7E,$F7,$CF,$80,$04,$89,$BB,$1F,$FE,$3F,$80,$B4,$90,$46
	dc.b $31,$0A,$06,$C2,$09,$41,$1F,$02,$08,$E1,$EF,$80,$0A,$1C,$06,$D2
	dc.b $12,$A1,$1B,$F0,$BC,$6E,$07,$3C,$0F,$41,$E0,$07,$08,$9E,$10,$1F
	dc.b $CA,$63,$1A,$68,$06,$66,$FA,$06,$20,$E8,$E3,$07,$F1,$5A,$4D,$3F
	dc.b $AD,$00,$27,$40,$3B,$94,$9B,$30,$F6,$78,$1D,$03,$DE,$02,$81,$BD
	dc.b $8F,$81,$8C,$3C,$04,$C8,$18,$06,$22,$D4,$07,$89,$40,$AD,$02,$84
	dc.b $21,$E0,$66,$18,$18,$F0,$04,$C9,$E3,$88,$00,$90,$12,$A8,$0E,$62
	dc.b $56,$C0,$A0,$66,$25,$F0,$07,$08,$BF,$38,$1F,$E6,$4F,$93,$AE,$CB
	dc.b $BF,$80,$62,$01,$8C,$2A,$D4,$D3,$B8,$08,$43,$80,$02,$7C,$03,$F0
	dc.b $41,$60,$84,$1B,$31,$D2,$1F,$7F,$F3,$DF,$C7,$F0,$73,$F0,$0F,$00
	dc.b $8C,$44,$0E,$1B,$20,$0D,$10,$2A,$2F,$E0,$2C,$AF,$F0,$7C,$8A,$40
	dc.b $9E,$7E,$00,$A2,$82,$38,$93,$00,$21,$04,$02,$BA,$DC,$01,$C4,$70
	dc.b $D9,$EB,$74,$BF,$1F,$F8,$60,$7F,$DF,$07,$E1,$5E,$AF,$9D,$E0,$43
	dc.b $1E,$00,$17,$FC,$1E,$00,$02,$19,$88,$48,$32,$96,$C8,$7B,$CD,$D7
	dc.b $08,$2A,$18,$00,$15,$14,$66,$7F,$01,$C0,$E0,$47,$17,$EF,$F8,$5C
	dc.b $07,$B6,$09,$F8,$B5,$61,$30,$0A,$07,$38,$82,$28,$81,$10,$00,$02
	dc.b $BF,$C1,$6D,$D1,$1F,$80,$48,$42,$00,$03,$11,$47,$02,$7E,$03,$89
	dc.b $00,$22,$06,$02,$1E,$0B,$B9,$03,$02,$07,$FC,$0F,$02,$9E,$33,$EE
	dc.b $00,$8E,$EF,$77,$5F,$7F,$81,$10,$60,$04,$13,$00,$79,$88,$08,$66
	dc.b $20,$A0,$E6,$22,$21,$80,$3D,$19,$CE,$60,$70,$46,$00,$55,$2E,$8A
	dc.b $07,$F7,$E9,$FD,$87,$FF,$BB,$0E,$2D,$A8,$1C,$03,$7D,$03,$91,$E6
	dc.b $70,$D8,$06,$0E,$00,$81,$E6,$00,$10,$40,$00,$5E,$1F,$98,$00,$78
	dc.b $0F,$FE,$60,$79,$22,$82,$00,$8A,$38,$0E,$06,$01,$31,$0E,$1A,$46
	dc.b $43,$C0,$CF,$44,$D5,$C0,$07,$08,$82,$FD,$80,$E2,$7E,$FF,$9F,$17
	dc.b $3E,$AC,$1D,$0C,$40,$54,$80,$F0,$01,$E0,$CC,$41,$41,$F7,$83,$7A
	dc.b $A2,$1C,$13,$EF,$30,$91,$E9,$70,$BA,$7F,$07,$2F,$C0,$71,$8A,$D8
	dc.b $FE,$02,$12,$E3,$88,$82,$0F,$00,$89,$7F,$15,$8A,$28,$30,$71,$0C
	dc.b $00,$70,$40,$50,$10,$00,$06,$08,$62,$38,$01,$EE,$08,$52,$29,$10
	dc.b $0C,$45,$FF,$3A,$07,$01,$40,$C0,$01,$C1,$1D,$5C,$E0,$31,$13,$FF
	dc.b $08,$F4,$24,$17,$74,$07,$02,$FF,$DD,$7F,$7F,$88,$29,$7D,$86,$01
	dc.b $08,$39,$60,$C9,$62,$C1,$80,$80,$C4,$02,$19,$67,$EF,$9D,$9C,$D1
	dc.b $9C,$FC,$A2,$B3,$7C,$07,$82,$B9,$00,$21,$0F,$83,$B2,$BF,$07,$80
	dc.b $40,$AC,$F0,$7E,$FD,$9F,$E9,$3B,$E3,$61,$AF,$DF,$4E,$20,$73,$81
	dc.b $2A,$82,$81,$81,$0F,$80,$82,$80,$07,$86,$90,$10,$32,$10,$2E,$F4
	dc.b $DF,$F2,$07,$01,$40,$D2,$2F,$11,$16,$97,$F0,$1C,$C5,$03,$DE,$01
	dc.b $C1,$76,$ED,$FB,$F9,$F9,$C5,$76,$FA,$2B,$43,$11,$30,$E6,$20,$21
	dc.b $80,$3D,$20,$7F,$67,$E0,$53,$80,$81,$54,$6A,$20,$75,$02,$FF,$87
	dc.b $40,$26,$7F,$03,$80,$E3,$5F,$FF,$FB,$CE,$E1,$2F,$FD,$C3,$CF,$5F
	dc.b $93,$90,$39,$C0,$CC,$41,$03,$0E,$01,$00,$90,$85,$03,$E1,$E5,$81
	dc.b $78,$87,$F8,$40,$E0,$28,$1C,$C4,$10,$30,$5A,$82,$85,$03,$1E,$1A
	dc.b $3C,$41,$C1,$7F,$7F,$D3,$C2,$AB,$B5,$29,$31,$1E,$0C,$C4,$34,$1C
	dc.b $C4,$04,$30,$0D,$E2,$07,$0E,$EF,$85,$E2,$10,$10,$0E,$38,$24,$65
	dc.b $01,$07,$90,$80,$78,$40,$C4,$BE,$E0,$2A,$88,$37,$DB,$F9,$81,$AF
	dc.b $1F,$98,$38,$52,$A0,$B0,$64,$20,$31,$2C,$F8,$CC,$0E,$02,$81,$80
	dc.b $82,$E0,$2C,$1E,$F0,$0C,$40,$41,$A4,$A5,$6C,$40,$E2,$BC,$5D,$80
	dc.b $C1,$98,$86,$83,$03,$01,$88,$78,$3E,$E9,$7C,$0F,$FA,$FB,$94,$B0
	dc.b $AE,$1C,$0F,$00,$08,$04,$1C,$14,$02,$06,$00,$22,$BF,$82,$25,$AD
	dc.b $18,$7F,$E2,$28,$4E,$94,$38,$28,$60,$0A,$80,$C1,$F4,$80,$C4,$B6
	dc.b $D0,$C4,$70,$04,$0F,$E0,$07,$00,$60,$C5,$80,$62,$1C,$0D,$FD,$AB
	dc.b $15,$60,$8B,$D2,$86,$20,$B0,$C3,$C0,$62,$01,$0F,$1E,$03,$7D,$3C
	dc.b $37,$1A,$2D,$87,$03,$82,$03,$10,$B0,$66,$E2,$71,$FD,$BE,$06,$A1
	dc.b $F1,$43,$82,$8C,$80,$A8,$0C,$19,$4A,$2C,$09,$6A,$41,$F9,$0D,$49
	dc.b $38,$1F,$10,$1C,$01,$83,$D6,$BA,$81,$C0,$70,$3B,$F0,$82,$39,$1C
	dc.b $07,$05,$83,$25,$8B,$06,$3E,$03,$10,$F0,$7B,$DF,$E0,$1F,$0F,$60
	dc.b $91,$C4,$53,$C0,$1C,$E2,$89,$00,$E0,$18,$3F,$DD,$F3,$F4,$7F,$DF
	dc.b $13,$98,$07,$82,$0E,$0A,$72,$02,$A0,$30,$67,$8B,$B0,$2A,$B0,$86
	dc.b $30,$1C,$11,$C1,$7A,$40,$70,$06,$0F,$0E,$8A,$07,$01,$C0,$CA,$EF
	dc.b $AE,$93,$76,$48,$62,$0B,$0E,$62,$3C,$18,$01,$F7,$F8,$1F,$C1,$F9
	dc.b $E8,$81,$6D,$6C,$07,$38,$82,$40,$4C,$1A,$0E,$82,$7F,$1F,$22,$80
	dc.b $F0,$40,$E0,$BD,$20,$2A,$0B,$06,$80,$04,$EB,$08,$70,$01,$D1,$1C
	dc.b $17,$24,$07,$01,$60,$CA,$A3,$80,$60,$65,$F7,$B6,$87,$E5,$24,$80
	dc.b $0B,$06,$62,$16,$0E,$62,$3C,$1B,$F0,$04,$76,$07,$FF,$C2,$3F,$42
	dc.b $B0,$07,$38,$18,$40,$0E,$01,$83,$BF,$04,$30,$B6,$08,$00,$14,$E3
	dc.b $82,$9E,$00,$C4,$02,$18,$08,$10,$A3,$80,$60,$7D,$80,$38,$06,$86
	dc.b $BC,$2A,$7A,$17,$B8,$43,$10,$58,$7A,$85,$AC,$0D,$07,$FC,$05,$8B
	dc.b $9A,$F9,$FC,$48,$10,$9A,$87,$02,$10,$01,$C0,$70,$73,$05,$BE,$01
	dc.b $BC,$41,$C0,$10,$37,$80,$15,$03,$83,$38,$10,$14,$18,$74,$47,$00
	dc.b $40,$F6,$00,$70,$15,$0D,$FD,$FA,$74,$04,$22,$E2,$90,$00,$60,$FF
	dc.b $CF,$FF,$91,$00,$12,$0F,$FD,$FE,$10,$01,$FE,$E0,$00,$91,$80,$00
	dc.b $00,$00,$00,$50
abs_0_000449C2:
	dcb.b $A3E,$00
