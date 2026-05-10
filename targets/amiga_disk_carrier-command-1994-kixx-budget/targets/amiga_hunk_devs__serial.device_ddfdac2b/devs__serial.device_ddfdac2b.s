    INCLUDE "exec/devices.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/intbits.i"

    RSSET LIB_SIZE
    RS.B 33
app_0043 RS.B 1
    RS.B 1
app_0045 RS.B 1
    RS.B 36
app_006A RS.L 1
app_006E RS.L 1
    RS.B 4
app_0076 RS.L 1
    RS.B 68
app_00BE RS.L 1
    RS.B 279
app_01D9 RS.B 1
    RS.B 1
app_01DB RS.B 1
app_SIZEOF EQU __RS

_custom	EQU	$DFF000
_ciab	EQU	$BFD000

    SECTION section_0,code
	dc.b $20,$3C,$FF,$FF,$FF,$FF,$4E,$75
resident_idstring:
	dc.b "serial 34.10 (27 May 1988)",$0D,$0A,$00	; string
	dc.b $00
resident:	; STRUCT RT
    ; invalid overlap: decoded code at $0026 starts at structured data; emitted as data
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l loc_0_00000FE4	; APTR RT_ENDSKIP
	dc.b RTF_COLDSTART	; UBYTE RT_FLAGS = RTF_COLDSTART
	dc.b $22	; UBYTE RT_VERSION
	dc.b NT_DEVICE	; UBYTE RT_TYPE = NT_DEVICE
	dc.b $3C	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
resident_name:
	dc.b "serial.device",$00	; string
loc_0_0000004E:
	dc.b "timer.device",$00	; string
	dc.b $00
loc_0_0000005C:
	dc.b "intuition.library",$00	; string
loc_0_0000006E:
	dc.b "misc.resource",$00	; string
resident_vectors:
	dc.b $FF,$FF
	dc.w $0012
	dc.w $034C
	dc.w $05A2
	dc.w $0010
	dc.w $042A
	dc.w $049C
	dc.w $FFFF
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_extfunc:
	rts
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_open:
	clr.b $001F(a1)
	tst.w $0020(a6)
	beq.b loc_0_000000B4
	btst.b #5,app_0045(a6)
	beq.b loc_0_000000AA
	btst.b #5,$004F(a1)
	bne.w loc_0_000002B8
loc_0_000000AA:
	move.b #$1,$001F(a1)
	bra.w loc_0_000004A4
loc_0_000000B4:
	clr.b $01D8(a6)
	clr.b $01D6(a6)
	move.w #$5DC,$01DC(a6)
	lea.l $00A2(a6),a0
	move.l a0,(a0)
	addq.l #4,(a0)
	clr.l $0004(a0)
	move.l a0,$0008(a0)
	lea.l $00B0(a6),a0
	move.l a0,(a0)
	addq.l #4,(a0)
	clr.l $0004(a0)
	move.l a0,$0008(a0)
	movem.l d2/a3,-(a7)
	move.l a1,-(a7)
	lea.l loc_0_0000005C(pc),a1
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$0228(a6)
	movea.l (a7)+,a6
	movea.l d0,a3
	move.l #$100,d0
	moveq.l #1,d1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00C6(a6)
	movea.l (a7)+,a6
	movea.l d0,a0
	beq.w loc_0_00000206
	move.l #$C0,d0
	move.l a0,d2
	move.l a6,-(a7)
	movea.l a3,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	movea.l a3,a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$019E(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	movea.l d2,a3
	move.w $0002(a3),d0
	lsl.w #1,d0
	lea.l loc_0_000003AC(pc),a0
	move.w $0(a0,d0.w),$01C4(a6)
	clr.w $01C2(a6)
	move.b #$8,app_0043(a6)
	move.b $00B6(a3),d0
	btst #0,d0
	beq.b loc_0_00000164
	move.b #$7,app_0043(a6)
loc_0_00000164:
	move.b #$8,d1
	lsr.b #4,d0
	sub.b d0,d1
	move.b d1,$0042(a6)
	move.b #$1,$0044(a6)
	move.b $00B7(a3),d0
	btst #4,d0
	beq.b loc_0_00000186
	move.b #$2,$0044(a6)
loc_0_00000186:
	move.b app_0043(a6),$004D(a1)
	move.b $0042(a6),$004C(a1)
	move.b $0044(a6),$004E(a1)
	bsr.w loc_0_00000CF0
	move.b $00B7(a3),d0
	andi.w #15,d0
	lsl.w #1,d0
	lea.l loc_0_000003BC(pc),a0
	clr.l $0036(a6)
	move.w $0(a0,d0.w),$0038(a6)
	move.b $00B8(a3),d0
	move.b d0,d1
	lsr.b #4,d0
	beq.b loc_0_000001D2
	bset.b #0,app_0045(a6)
	cmpi.b #2,d0
	bne.b loc_0_000001D8
	bset.b #1,app_0045(a6)
	bra.b loc_0_000001DE
loc_0_000001D2:
	bclr.b #0,app_0045(a6)
loc_0_000001D8:
	bclr.b #1,app_0045(a6)
loc_0_000001DE:
	andi.b #15,d1
	beq.b loc_0_000001F8
	bset.b #7,app_0045(a6)
	cmpi.b #1,d1
	bne.b loc_0_000001FE
	bset.b #2,app_0045(a6)
	bra.b loc_0_0000020E
loc_0_000001F8:
	bclr.b #7,app_0045(a6)
loc_0_000001FE:
	bclr.b #2,app_0045(a6)
	bra.b loc_0_0000020E
loc_0_00000206:
	movea.l (a7)+,a1
	movea.l #$0,a3
loc_0_0000020E:
	btst.b #1,$01BD(a6)
	beq.b loc_0_0000021C
	bset.b #0,app_0045(a6)
loc_0_0000021C:
	bsr.w loc_0_00000D64
	move.l $0036(a6),d2
	clr.l d0
	move.l a3,d1
	beq.b loc_0_00000230
	move.l #$100,d0
loc_0_00000230:
	bsr.w loc_0_00000348
	tst.l d0
	bne.b loc_0_00000246
	move.b #$4,$001F(a1)
	movem.l (a7)+,d2/a3
	move.l a6,d0
	rts
loc_0_00000246:
	move.l a1,-(a7)
	lea.l $0182(a6),a1
	lea.l loc_0_0000004E(pc),a0
	move.l #$1,d0
	clr.l d1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01BC(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_00000272
	movea.l (a7)+,a1
	move.b #$B,$001F(a1)
	bra.b loc_0_00000286
loc_0_00000272:
	move.l $0014(a1),$0066(a6)
	move.l $0196(a6),$0136(a6)
	move.l $019A(a6),$013A(a6)
	movea.l (a7)+,a1
loc_0_00000286:
	movem.l (a7)+,d2/a3
	tst.b $001F(a1)
	bne.w loc_0_000003DE
	move.w #INTF_RBF,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_TBE,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_RBF,_custom+intena.l
	btst.b #5,$004F(a1)
	beq.b loc_0_000002B8
	bset.b #5,app_0045(a6)
loc_0_000002B8:
	move.b app_0045(a6),$004F(a1)
	tst.b $001F(a1)
	bne.b loc_0_00000312
	addq.w #1,$0020(a6)
	move.w #INTF_INTEN,_custom+intena.l
	addq.b #1,$0126(a6)
	move.b _ciab+ciaddra.l,$01DA(a6)
	andi.b #7,_ciab+ciaddra.l
	move.b _ciab+ciapra.l,app_01DB(a6)
	ori.b #192,_ciab+ciaddra.l
	andi.b #CIAF_COMCTS|CIAF_COMDSR|CIAF_PRTRSEL|CIAF_PRTRPOUT|CIAF_PRTRBUSY,_ciab+ciapra.l
	andi.b #199,_ciab+ciaddra.l
	subq.b #1,$0126(a6)
	bge.b loc_0_00000312
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_00000312:
	move.l $0022(a6),$0030(a1)
	move.l $0036(a6),$0034(a1)
	clr.w $0050(a1)
	move.l $0042(a6),$004C(a1)
	move.l $01C2(a6),$003C(a1)
	move.l app_006A(a6),$0040(a1)
	move.l $01BA(a6),$0038(a1)
	move.l app_006E(a6),$0044(a1)
	move.l $0072(a6),$0048(a1)
	rts
loc_0_00000348:
	movem.l d2/a1/a3,-(a7)
	move.l a3,d1
	beq.b loc_0_00000362
	tst.l d0
	beq.b loc_0_00000362
	movea.l a3,a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00D2(a6)
	movea.l (a7)+,a6
loc_0_00000362:
	move.l d2,d0
	beq.b loc_0_0000037C
	moveq.l #1,d1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00C6(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_0000037C
	move.l d2,$0036(a6)
loc_0_0000037C:
	move.l d0,$0026(a6)
	move.l d0,$002E(a6)
	move.l d0,$002A(a6)
	move.l d0,$0032(a6)
	add.l d2,$0032(a6)
	clr.l $003A(a6)
	clr.l $003E(a6)
	lsr.l #1,d2
	move.l d2,$01C6(a6)
	lsr.l #1,d2
	move.l d2,$01CA(a6)
	movem.l (a7)+,d2/a1/a3
	tst.l d0
	rts
loc_0_000003AC:
	dc.b $00,$70,$01,$2C,$04,$B0,$09,$60,$12,$C0,$25,$80,$4B,$00,$7A,$12
loc_0_000003BC:
	dc.b $02,$00,$04,$00,$08,$00,$10,$00,$1F,$40,$3E,$80
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_close:
	moveq.l #0,d0
	clr.b $001F(a1)
	tst.w $0020(a6)
	beq.w loc_0_000004A4
	subq.w #1,$0020(a6)
	bne.w loc_0_000004A4
loc_0_000003DE:
	clr.l $004E(a6)
	clr.l $004A(a6)
	clr.l $0046(a6)
	move.w #INTF_INTEN,_custom+intena.l
	addq.b #1,$0126(a6)
	move.b _ciab+ciaddra.l,d0
	andi.b #7,d0
	ori.b #248,d0
	move.b d0,_ciab+ciaddra.l
	move.b _ciab+ciapra.l,d0
	move.b app_01DB(a6),d1
	andi.b #248,d1
	andi.b #7,d0
	or.b d1,d0
	move.b d0,_ciab+ciapra.l
	move.b _ciab+ciaddra.l,d0
	andi.b #7,d0
	move.b $01DA(a6),d1
	andi.b #248,d1
	or.b d1,d0
	move.b d0,_ciab+ciaddra.l
	subq.b #1,$0126(a6)
	bge.b loc_0_0000044C
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_0000044C:
	clr.w $0020(a6)
	lea.l $0122(a6),a0
	bsr.w loc_0_0000060A
	lea.l $0182(a6),a0
	bsr.w loc_0_0000060A
	move.l a1,-(a7)
	lea.l $0182(a6),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01C2(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	bclr.b #5,app_0045(a6)
	movem.l d2/a1/a3,-(a7)
	move.l $0036(a6),d0
	clr.l d2
	movea.l $0026(a6),a3
	bsr.w loc_0_00000348
	movem.l (a7)+,d2/a1/a3
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	btst.b #6,$01D8(a6)
	beq.b loc_0_000004A4
	jsr -$0012(a6)
loc_0_000004A4:
	rts
    ; KNOWN: base A6=serial.device:LIB
serial_device_dev_beginio:
	move.b #$5,$0008(a1)
	move.w $001C(a1),d0
	cmpi.w #11,d0
	bhi.b loc_0_00000510
	clr.b $001F(a1)
	lsl.w #2,d0
	lea.l loc_0_000004E0(pc),a0
	movea.l $0(a0,d0.w),a0
	jmp (a0)
loc_0_000004C6:
	move.l #$51,d1
	and.b $001E(a1),d1
	bne.b loc_0_000004DE
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_000004DE:
	rts
loc_0_000004E0:
	dc.l loc_0_00000510	; pointer_table
	dc.l loc_0_00000918
	dc.l loc_0_00000FE4
	dc.l loc_0_000006C4
	dc.l loc_0_00000510
	dc.l loc_0_00000996
	dc.l loc_0_000009B0
	dc.l loc_0_000009CA
	dc.l loc_0_000009EE
	dc.l loc_0_00000A60
	dc.l loc_0_00000AA4
	dc.l loc_0_00000B84
loc_0_00000510:
	move.b #$FD,$001F(a1)
	bra.b loc_0_000004C6
    ; KNOWN: base A6=serial.device:LIB
serial_device_dev_abortio:
	bset.b #7,$01D8(a6)
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_0000053A
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
	bclr.b #7,$01D8(a6)
	rts
loc_0_0000053A:
	clr.b $001F(a1)
	cmpi.w #2,$001C(a1)
	beq.b loc_0_0000055E
	cmpi.w #3,$001C(a1)
	beq.w loc_0_00000590
	cmpi.w #10,$001C(a1)
	beq.w loc_0_00000590
	bra.w loc_0_00000608
loc_0_0000055E:
	cmpa.l $004A(a6),a1
	bne.b loc_0_00000570
	bclr.b #1,$01D8(a6)
	clr.l $004A(a6)
	bra.b loc_0_000005E2
loc_0_00000570:
	btst.b #6,$001E(a1)
	beq.w loc_0_00000608
	move.l a1,-(a7)
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	movea.l (a7)+,a1
	subq.w #1,$0046(a6)
	bra.b loc_0_000005E2
loc_0_00000590:
	cmpa.l $004E(a6),a1
	bne.b loc_0_000005C4
	cmpi.w #10,$001C(a1)
	bne.b loc_0_000005B0
	bclr.b #5,$01D6(a6)
	beq.b loc_0_000005B0
	movea.l #$DFF09E,a0
	move.w #$800,(a0)
loc_0_000005B0:
	lea.l $0122(a6),a0
	bsr.b loc_0_0000060A
	clr.l $004E(a6)
	bclr.b #4,$01D8(a6)
	bra.w loc_0_000005E2
loc_0_000005C4:
	btst.b #6,$001E(a1)
	beq.w loc_0_00000608
	move.l a1,-(a7)
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	movea.l (a7)+,a1
	subq.w #1,$0048(a6)
loc_0_000005E2:
	bset.b #5,$001E(a1)
	andi.b #175,$001E(a1)
	move.b #$FE,$001F(a1)
	btst.b #0,$001E(a1)
	bne.b loc_0_00000608
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_00000608:
	rts
loc_0_0000060A:
	move.l a1,-(a7)
	movea.l a0,a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01E0(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	rts
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_expunge:
	move.l #$0,d0
	tst.w $0020(a6)
	beq.b loc_0_0000062C
	rts
loc_0_0000062C:
	move.l a6,-(a7)
	movea.l $01B6(a6),a6
	move.l #$1,d0
	jsr -$000C(a6)
	move.l #$0,d0
	jsr -$000C(a6)
	movea.l (a7)+,a6
	move.l #$B,d0
	movea.l $01AE(a6),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00A2(a6)
	movea.l (a7)+,a6
	move.l #$0,d0
	movea.l $01B2(a6),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00A2(a6)
	movea.l (a7)+,a6
	move.l $01AA(a6),-(a7)
	lea.l $014A(a6),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$0168(a6)
	movea.l (a7)+,a6
	lea.l $00EA(a6),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$0168(a6)
	movea.l (a7)+,a6
	movea.l a6,a1
	clr.l d0
	move.w $0010(a6),d0
	suba.l d0,a1
	add.w $0012(a6),d0
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00D2(a6)
	movea.l (a7)+,a6
	movea.l a6,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	move.l (a7)+,d0
	rts
loc_0_000006C4:
	clr.l $0020(a1)
	tst.l $0024(a1)
	beq.w loc_0_000004C6
	bclr.b #0,$001E(a1)
	bset.b #7,$01D8(a6)
	move.w #INTF_TBE,_custom+intena.l
	tst.w $0048(a6)
	bne.b loc_0_0000071C
	tst.l $004E(a6)
	bne.b loc_0_0000071C
	bset.b #4,$001E(a1)
	clr.l $005E(a6)
	move.l $0028(a1),$0056(a6)
	move.l a1,$004E(a6)
	move.w #INTF_SETCLR|INTF_TBE,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_TBE,_custom+intena.l
	bclr.b #7,$01D8(a6)
loc_0_0000071A:
	rts
loc_0_0000071C:
	bset.b #6,$001E(a1)
	lea.l $00B0(a6),a0
	lea.l $0004(a0),a0
	move.l $0004(a0),d0
	move.l a1,$0004(a0)
	move.l a0,(a1)
	move.l d0,$0004(a1)
	movea.l d0,a0
	move.l a1,(a0)
	addq.w #1,$0048(a6)
	move.w #INTF_SETCLR|INTF_TBE,_custom+intena.l
	bclr.b #7,$01D8(a6)
	rts
loc_0_00000750:
	dc.b $4A,$29,$01,$D9,$66,$00,$01,$8E,$48,$E7,$20,$02,$2C,$49,$08,$2E
	dc.b $00,$05,$01,$D6,$66,$00,$01,$70,$4A,$AE,$00,$4E,$67,$00,$01,$1E
	dc.b $22,$6E,$00,$4E,$08,$29,$00,$05,$00,$1E,$66,$00,$01,$10,$08,$2E
	dc.b $00,$02,$01,$D8,$66,$00,$01,$50,$08,$2E,$00,$02,$00,$45,$67,$3C
	dc.b $10,$39,$00,$BF,$D0,$00,$02,$00,$00,$18,$67,$30,$08,$00,$00,$03
	dc.b $67,$0A,$13,$7C,$00,$0D,$00,$1F,$60,$00,$00,$C4,$53,$6E,$01,$DC
	dc.b $66,$0A,$13,$7C,$00,$0B,$00,$1F,$60,$00,$00,$B4,$70,$00,$30,$2E
	dc.b $01,$CE,$ED,$88,$61,$00,$03,$6C,$60,$00,$01,$06,$3D,$7C,$05,$DC
	dc.b $01,$DC,$20,$6E,$00,$56,$42,$40,$10,$10,$22,$29,$00,$24,$6A,$10
	dc.b $08,$2E,$00,$04,$01,$D8,$67,$10,$53,$AE,$00,$5E,$60,$00,$00,$80
	dc.b $B2,$AE,$00,$5E,$63,$00,$00,$78,$33,$FC,$00,$01,$00,$DF,$F0,$9C
	dc.b $08,$AE,$00,$04,$01,$D8,$C0,$6E,$01,$D2,$66,$06,$08,$EE,$00,$04
	dc.b $01,$D8,$08,$2E,$00,$00,$00,$45,$67,$20,$08,$2E,$00,$01,$01,$BD
	dc.b $67,$0A,$08,$2E,$00,$00,$01,$BD,$66,$0A,$60,$0E,$4E,$B9
	dc.l loc_0_0000118C
	dc.b $67,$06,$12,$2E,$00,$43,$03,$C0,$80,$6E,$01,$D4,$33,$C0,$00,$DF
	dc.b $F0,$30,$52,$AE,$00,$56,$52,$AE,$00,$5E,$08,$29,$00,$06,$00,$4F
	dc.b $67,$0E,$41,$EE,$00,$6E,$72,$07,$B0,$18,$54,$C9,$FF,$FC,$67,$0C
	dc.b $20,$29,$00,$24,$6B,$68,$B0,$AE,$00,$5E,$6C,$62,$23,$6E,$00,$5E
	dc.b $00,$20,$08,$AE,$00,$04,$01,$D8,$42,$AE,$00,$4E,$2F,$0E,$2C,$6E
	dc.b $00,$62,$4E,$AE,$FE,$86,$2C,$5F,$60,$44,$4A,$6E,$00,$48,$67,$44
	dc.b $41,$EE,$00,$B0,$22,$50,$20,$11,$67,$08,$20,$80,$C1,$89,$23,$48
	dc.b $00,$04,$22,$40,$2D,$40,$00,$4E,$53,$6E,$00,$48,$08,$E9,$00,$04
	dc.b $00,$1E,$08,$A9,$00,$06,$00,$1E,$42,$AE,$00,$5E,$2D,$69,$00,$28
	dc.b $00,$56,$0C,$69,$00,$0A,$00,$1C,$66,$04,$61,$00,$01,$F4,$4C,$DF
	dc.b $40,$04,$4E,$75,$33,$FC,$00,$01,$00,$DF,$F0,$9A,$4C,$DF,$40,$04
	dc.b $4E,$75,$33,$FC,$00,$01,$00,$DF,$F0,$9C,$42,$41,$12,$29,$01,$D9
	dc.b $82,$69,$01,$D4,$42,$29,$01,$D9,$33,$C1,$00,$DF,$F0,$30,$4A,$A9
	dc.b $00,$4E,$66,$0E,$4A,$69,$00,$48,$66,$08,$33,$FC,$00,$01,$00,$DF
	dc.b $F0,$9A,$4E,$75,$00,$00
loc_0_00000918:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_00000A06
	move.l a1,-(a7)
	move.l $004A(a6),d0
	beq.b loc_0_00000932
	movea.l d0,a1
	bsr.w loc_0_0000053A
loc_0_00000932:
	move.l $004E(a6),d0
	beq.b loc_0_0000093E
	movea.l d0,a1
	bsr.w loc_0_0000053A
loc_0_0000093E:
	andi.b #32,app_0045(a6)
	clr.b $01D8(a6)
	movea.l (a7)+,a1
	move.l #$11130000,$0030(a1)
	move.l #$2580,$003C(a1)
	move.l #$8080100,$004C(a1)
	move.l #$3D090,$0040(a1)
	move.l #$200,$0034(a1)
	lea.l $0044(a1),a0
	move.l #$0,(a0)+
	move.l #$0,(a0)
	bsr.w loc_0_00000BF6
	bsr.w loc_0_0000099E
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
	bra.w loc_0_000004C6
loc_0_00000996:
	bsr.w loc_0_0000099E
	bra.w loc_0_000004C6
loc_0_0000099E:
	move.l $0026(a6),$002A(a6)
	move.l $0026(a6),$002E(a6)
	clr.l $003A(a6)
	rts
loc_0_000009B0:
	move.l $004E(a6),d0
	beq.b loc_0_000009BC
	bset.b #2,$01D8(a6)
loc_0_000009BC:
	move.l $004A(a6),d0
	beq.b loc_0_000009C6
	bsr.w loc_0_00001318
loc_0_000009C6:
	bra.w loc_0_000004C6
loc_0_000009CA:
	bclr.b #2,$01D8(a6)
	move.l $004A(a6),d0
	beq.b loc_0_000009DA
	bsr.w loc_0_000012FA
loc_0_000009DA:
	move.w #INTF_SETCLR|INTF_TBE,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_TBE,_custom+intena.l
	bra.w loc_0_000004C6
loc_0_000009EE:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_00000A06
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
	bra.w loc_0_000004C6
loc_0_00000A06:
	move.l a1,-(a7)
	lea.l $00A2(a6),a0
	bsr.w loc_0_00000A20
	lea.l $00B0(a6),a0
	bsr.w loc_0_00000A20
	clr.l $0046(a6)
	movea.l (a7)+,a1
	rts
loc_0_00000A20:
	movea.l (a0),a1
	move.l (a1),d0
	beq.b loc_0_00000A2E
	move.l d0,(a0)
	exg d0,a1
	move.l a0,$0004(a1)
loc_0_00000A2E:
	tst.l d0
	beq.w loc_0_00000A3C
	movea.l d0,a1
	bsr.w loc_0_00000A3E
	bra.b loc_0_00000A20
loc_0_00000A3C:
	rts
loc_0_00000A3E:
	bset.b #5,$001E(a1)
	move.b #$FE,$001F(a1)
	btst.b #0,$001E(a1)
	bne.b loc_0_00000A5E
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_00000A5E:
	rts
loc_0_00000A60:
	movea.l #$BFD0FE,a0
	move.b (a0),d0
	btst.b #2,app_0045(a6)
	beq.b loc_0_00000A80
	andi.b #239,d0
	btst.b #3,$01D8(a6)
	beq.b loc_0_00000A80
	bset #4,d0
loc_0_00000A80:
	andi.b #252,d0
	move.b d0,$0051(a1)
	move.b $01D6(a6),$0050(a1)
	andi.b #31,$0050(a1)
	andi.b #249,$01D6(a6)
	move.l $003A(a6),$0020(a1)
	bra.w loc_0_000004C6
loc_0_00000AA4:
	bclr.b #0,$001E(a1)
	btst.b #3,$004F(a1)
	beq.b loc_0_00000AC2
	tst.w $0048(a6)
	bne.w loc_0_0000071C
	tst.l $004E(a6)
	bne.w loc_0_0000071C
loc_0_00000AC2:
	bset.b #5,$01D6(a6)
	move.l app_006A(a6),d0
	bsr.w loc_0_00000B32
	move.l a1,$004E(a6)
	movea.l #$DFF09E,a0
	move.w #$8800,(a0)
	rts
loc_0_00000AE0:
	dc.b $08,$A9,$00,$05,$01,$D6,$67,$38,$48,$E7,$00,$42,$2C,$49,$22,$6E
	dc.b $00,$4E,$67,$28,$0C,$69,$00,$0A,$00,$1C,$66,$20,$08,$EE,$00,$01
	dc.b $01,$D6,$42,$AE,$00,$4E,$20,$7C,$00,$DF,$F0,$9E,$30,$BC,$08,$00
	dc.b $2F,$0E,$2C,$6E,$00,$62,$4E,$AE,$FE,$86,$2C,$5F,$4C,$DF,$42,$00
	dc.b $08,$29,$00,$07,$01,$D8,$66,$08,$33,$FC,$80,$01,$00,$DF,$F0,$9A
	dc.b $4E,$75
loc_0_00000B32:
	movem.l a1/a6,-(a7)
	move.w #INTF_TBE,_custom+intena.l
	lea.l $0122(a6),a1
	cmpi.b #5,$0008(a1)
	beq.b loc_0_00000B7C
	clr.l $0020(a1)
	cmpi.l #600,d0
	bhi.b loc_0_00000B5C
	move.l #$258,d0
loc_0_00000B5C:
	ori.b #255,d0
	move.l d0,$0024(a1)
	move.w #$9,$001C(a1)
	clr.b $001E(a1)
	movea.l $0014(a1),a6
	jsr -$001E(a6)
	movem.l (a7)+,a1/a6
	rts
loc_0_00000B7C:
	movem.l (a7)+,a1/a6
	rts
	dc.b $00,$00
loc_0_00000B84:
	btst.b #7,$004F(a1)
	beq.b loc_0_00000BB2
	bset.b #7,app_0045(a6)
	bclr.b #2,$01D8(a6)
	btst.b #3,$01D8(a6)
	beq.b loc_0_00000BB8
	bclr.b #7,$004F(a1)
	bsr.w loc_0_000012FA
	bset.b #7,$004F(a1)
	bra.b loc_0_00000BB8
loc_0_00000BB2:
	bclr.b #7,app_0045(a6)
loc_0_00000BB8:
	btst.b #1,$01D8(a6)
	bne.b loc_0_00000BD4
	tst.l $004E(a6)
	bne.b loc_0_00000BD4
	btst.b #4,$001E(a1)
	bne.b loc_0_00000BD4
	tst.l $0046(a6)
	beq.b loc_0_00000BDE
loc_0_00000BD4:
	move.b #$1,$001F(a1)
	bra.w loc_0_00000BF2
loc_0_00000BDE:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_00000BF6
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
loc_0_00000BF2:
	bra.w loc_0_000004C6
loc_0_00000BF6:
	movem.l d2/a3,-(a7)
	tst.b $004C(a1)
	beq.w loc_0_00000D48
	cmpi.b #8,$004C(a1)
	bgt.w loc_0_00000D48
	tst.b $004D(a1)
	beq.w loc_0_00000D48
	cmpi.b #8,$004D(a1)
	bgt.w loc_0_00000D48
	cmpi.b #2,$004E(a1)
	bgt.w loc_0_00000D48
	move.l $003C(a1),d0
	cmpi.l #112,d0
	blt.w loc_0_00000D48
	cmpi.l #292000,d0
	bgt.w loc_0_00000D48
	tst.l $0030(a1)
	beq.w loc_0_00000D48
	move.b $004C(a1),$0042(a6)
	move.b $004D(a1),app_0043(a6)
	move.b $004E(a1),$0044(a6)
	move.l $0030(a1),$0022(a6)
	move.l $0038(a1),$01BA(a6)
	btst.b #4,$004F(a1)
	beq.b loc_0_00000C74
	bset.b #7,$004F(a1)
loc_0_00000C74:
	btst.b #1,$003B(a1)
	beq.b loc_0_00000C82
	bset.b #0,$004F(a1)
loc_0_00000C82:
	move.b app_0045(a6),d0
	andi.b #32,d0
	move.b $004F(a1),app_0045(a6)
	or.b d0,app_0045(a6)
	move.b app_0045(a6),$004F(a1)
	move.l $003C(a1),$01C2(a6)
	bsr.w loc_0_00000D64
	move.l $0044(a1),app_006E(a6)
	move.l $0048(a1),$0072(a6)
	bsr.w loc_0_00000CF0
	tst.l $0040(a1)
	beq.w loc_0_00000D48
	move.l $0040(a1),app_006A(a6)
	move.l $0036(a6),d0
	cmp.l $0034(a1),d0
	beq.b loc_0_00000CEA
	move.l $0034(a1),d2
	cmpi.l #64,d2
	blt.b loc_0_00000CE4
	movea.l $0026(a6),a3
	bsr.w loc_0_00000348
	tst.l d0
	bne.b loc_0_00000CEA
loc_0_00000CE4:
	move.b #$4,$001F(a1)
loc_0_00000CEA:
	movem.l (a7)+,d2/a3
	rts
loc_0_00000CF0:
	clr.l d0
	clr.l d1
	move.b $004D(a1),d0
	tst.b $004E(a1)
	beq.b loc_0_00000D0C
	bset d0,d1
	cmpi.b #2,$004E(a1)
	bne.b loc_0_00000D0C
	lsl.w #1,d1
	bset d0,d1
loc_0_00000D0C:
	btst.b #0,app_0045(a6)
	beq.b loc_0_00000D16
	lsl.w #1,d1
loc_0_00000D16:
	move.w d1,$01D4(a6)
	bsr.w loc_0_00000D32
	move.w d0,$01D2(a6)
	clr.w d0
	move.b $004C(a1),d0
	bsr.w loc_0_00000D32
	move.w d0,$01D0(a6)
	rts
loc_0_00000D32:
	btst.b #0,app_0045(a6)
	bne.b loc_0_00000D3C
	subq.w #1,d0
loc_0_00000D3C:
	lsl.w #1,d0
	lea.l loc_0_00000D50(pc),a0
	move.w $0(a0,d0.w),d0
	rts
loc_0_00000D48:
	move.b #$5,$001F(a1)
	bra.b loc_0_00000CEA
loc_0_00000D50:
	dc.b $00,$01,$00,$03,$00,$07,$00,$0F,$00,$1F,$00,$3F,$00,$7F,$00,$FF
	dc.b $01,$FF,$03,$FF
loc_0_00000D64:
	move.l $01C2(a6),d0
	move.l d0,d1
	lsl.l #3,d0
	sub.l d1,d0
	move.l a1,-(a7)
	movea.l $0062(a6),a1
	moveq.l #0,d1
	move.b $0213(a1),d1
	movea.l #$17D7840,a1
	cmpi.b #50,d1
	bne.w loc_0_00000D8E
	movea.l #$179FF40,a1
loc_0_00000D8E:
	move.l a1,d1
	movea.l (a7)+,a1
	cmpi.l #65535,d0
	ble.b loc_0_00000DA8
	lsr.l #5,d0
	divu.w d0,d1
	andi.l #65535,d1
	lsr.l #5,d1
	bra.b loc_0_00000DAA
loc_0_00000DA8:
	divu.w d0,d1
loc_0_00000DAA:
	move.w d1,$01CE(a6)
	move.w $01CE(a6),d0
	bclr.b #5,$01D8(a6)
	cmpi.b #8,$0042(a6)
	bne.b loc_0_00000DD2
	btst.b #0,app_0045(a6)
	beq.b loc_0_00000DD2
	bset #15,d0
	bset.b #5,$01D8(a6)
loc_0_00000DD2:
	move.w d0,_custom+serper.l
	rts
	dc.b $00,$00
loc_0_00000DDC:
	dc.b $E0,$00,$00,$08,$03,$00,$C0,$00,$00,$0A
	dc.l resident_name
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$22,$D0,$00,$00,$16
	dc.b $00,$0A,$C0,$00,$00,$22,$11,$13,$00,$00,$C0,$00,$01,$C2,$00,$00
	dc.b $25,$80,$D0,$00,$01,$CE,$01,$74,$D0,$00,$01,$D0,$00,$FF,$D0,$00
	dc.b $01,$D2,$00,$FF,$D0,$00,$01,$D4,$01,$00,$C0,$00,$00,$42,$08,$08
	dc.b $01,$00,$C0,$00,$00,$6A,$00,$03,$D0,$90,$C0,$00,$00,$36,$00,$00
	dc.b $02,$00,$C0,$00,$01,$BE,$69,$96,$69,$96,$00,$00
resident_init:
	movem.l a0/a2,-(a7)
	lea.l resident_vectors(pc),a0
	lea.l loc_0_00000DDC(pc),a1
	suba.l a2,a2
	move.l #$1DE,d0
	move.l a6,-(a7)
	movea.l a6,a6
	jsr -$0054(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,a0/a2
	tst.l d0
	beq.w loc_0_00000FE0
	move.l a6,d1
	movem.l a3/a6,-(a7)
	movea.l d0,a6
	move.l a0,$01AA(a6)
	move.l d1,$0062(a6)
	move.w #$5DC,$01DC(a6)
	lea.l loc_0_0000006E(pc),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01F2(a6)
	movea.l (a7)+,a6
	move.l d0,$01B6(a6)
	beq.w loc_0_00000FE0
	lea.l resident_name(pc),a1
	move.l #$0,d0
	move.l a6,-(a7)
	movea.l $01B6(a6),a6
	jsr -$0006(a6)
	tst.l d0
	bne.w loc_0_00000EC4
	move.l #$1,d0
	lea.l resident_name(pc),a1
	jsr -$0006(a6)
loc_0_00000EC4:
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_00000ED2
	movem.l (a7)+,a3/a6
	bra.w loc_0_00000FE0
loc_0_00000ED2:
	lea.l app_00BE(a6),a0
	lea.l loc_0_0000071A.l,a3
	bsr.b loc_0_00000EF2
	lea.l $00D4(a6),a0
	lea.l loc_0_0000103E.l,a3
	bsr.b loc_0_00000EF2
	bra.w loc_0_00000F32
loc_0_00000EEE:
	move.l a0,$0010(a1)
loc_0_00000EF2:
	move.b #$10,$0009(a0)
	move.l #resident_name,$000A(a0)
	move.l a3,$0012(a0)
	move.l a6,$000E(a0)
	rts
loc_0_00000F0A:
	move.l #resident_name,$000A(a1)
	move.b #$0,$0009(a1)
	move.b #$1,$000E(a1)
	move.b #$4,$0008(a1)
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$0162(a6)
	movea.l (a7)+,a6
	rts
loc_0_00000F32:
	lea.l $00EA(a6),a1
	bsr.b loc_0_00000F0A
	lea.l $010C(a6),a0
	lea.l loc_0_00000AE0.l,a3
	bsr.b loc_0_00000EEE
	lea.l $0122(a6),a0
	move.b #$7,$0008(a0)
	lea.l $00EA(a6),a3
	move.l a3,$000E(a0)
	lea.l $014A(a6),a1
	bsr.b loc_0_00000F0A
	lea.l $016C(a6),a0
	lea.l loc_0_0000138A.l,a3
	bsr.b loc_0_00000EEE
	lea.l $0182(a6),a0
	move.b #$7,$0008(a0)
	lea.l $014A(a6),a3
	move.l a3,$000E(a0)
	movea.l a6,a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01B0(a6)
	movea.l (a7)+,a6
	lea.l app_0076(a6),a1
	moveq.l #11,d0
	move.l #loc_0_000011EC,$0012(a1)
	bsr.b loc_0_00000FC0
	move.l d0,$01AE(a6)
	lea.l $008C(a6),a1
	move.l #loc_0_00000750,$0012(a1)
	moveq.l #0,d0
	bsr.b loc_0_00000FC0
	move.l d0,$01B2(a6)
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	moveq.l #1,d0
	movem.l (a7)+,a3/a6
	bra.b loc_0_00000FDE
loc_0_00000FC0:
	move.l a6,$000E(a1)
	move.l #resident_name,$000A(a1)
	move.b #$2,$0008(a1)
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00A2(a6)
	movea.l (a7)+,a6
loc_0_00000FDE:
	rts
loc_0_00000FE0:
	clr.l d0
	bra.b loc_0_00000FDE
loc_0_00000FE4:
	clr.l $0020(a1)
	move.l $0024(a1),d1
	beq.w loc_0_000004C6
	tst.w $0046(a6)
	bne.b loc_0_00001002
	tst.l $004A(a6)
	bne.b loc_0_00001002
	cmp.l $003A(a6),d1
	bls.b loc_0_00001008
loc_0_00001002:
	bclr.b #0,$001E(a1)
loc_0_00001008:
	bset.b #6,$001E(a1)
	lea.l $00A2(a6),a0
	lea.l $0004(a0),a0
	move.l $0004(a0),d0
	move.l a1,$0004(a0)
	move.l a0,(a1)
	move.l d0,$0004(a1)
	movea.l d0,a0
	move.l a1,(a0)
	addq.w #1,$0046(a6)
	lea.l $00D4(a6),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00B4(a6)
	movea.l (a7)+,a6
	rts
loc_0_0000103E:
	dc.b $48,$E7,$20,$02,$2C,$49,$20,$2E,$00,$4A,$66,$46,$4A,$6E,$00,$46
	dc.b $6F,$00,$01,$36,$41,$EE,$00,$A2,$22,$50,$20,$11,$67,$08,$20,$80
	dc.b $C1,$89,$23,$48,$00,$04,$22,$40,$2D,$49,$00,$4A,$53,$6E,$00,$46
	dc.b $42,$AE,$00,$5A,$08,$E9,$00,$04,$00,$1E,$08,$A9,$00,$06,$00,$1E
	dc.b $2D,$69,$00,$28,$00,$52,$08,$EE,$00,$01,$01,$D8,$20,$29,$00,$24
	dc.b $60,$02,$22,$40,$4A,$AE,$00,$3A,$67,$00,$00,$EE,$22,$2E,$01,$C6
	dc.b $B2,$AE,$00,$3A,$6F,$0C,$08,$2E,$00,$03,$01,$D8,$67,$04,$61,$00
	dc.b $02,$4C,$20,$6E,$00,$2E,$10,$18,$B1,$EE,$00,$32,$6D,$04,$20,$6E
	dc.b $00,$26,$53,$AE,$00,$3A,$2D,$48,$00,$2E,$53,$88,$B1,$EE,$00,$26
	dc.b $66,$00,$00,$06,$20,$6E,$00,$32,$B1,$EE,$00,$3E,$67,$00,$00,$CC
	dc.b $08,$2E,$00,$00,$00,$45,$67,$3E,$08,$2E,$00,$05,$01,$D8,$66,$36
	dc.b $08,$2E,$00,$01,$01,$BD,$67,$1C,$12,$2E,$00,$42,$03,$80,$66,$0A
	dc.b $08,$2E,$00,$00,$01,$BD,$66,$10,$60,$16,$08,$2E,$00,$00,$01,$BD
	dc.b $67,$06,$60,$12,$61,$78,$67,$08,$13,$7C,$00,$09,$00,$1F,$60,$3E
	dc.b $12,$2E,$00,$42,$03,$80,$22,$29,$00,$24,$20,$6E,$00,$52,$10,$80
	dc.b $66,$04,$4A,$81,$6B,$28,$52,$A9,$00,$20,$52,$AE,$00,$52,$B2,$A9
	dc.b $00,$20,$63,$1A,$08,$29,$00,$06,$00,$4F,$67,$00,$FF,$48,$41,$EE
	dc.b $00,$6E,$72,$07,$B0,$18,$54,$C9,$FF,$FC,$66,$00,$FF,$38,$42,$AE
	dc.b $00,$4A,$08,$AE,$00,$01,$01,$D8,$08,$A9,$00,$04,$00,$1E,$08,$29
	dc.b $00,$00,$00,$1E,$66,$00,$FE,$D6,$2F,$0E,$2C,$6E,$00,$62,$4E,$AE
	dc.b $FE,$86,$2C,$5F,$60,$00,$FE,$C6,$4C,$DF,$40,$04,$4E,$75
loc_0_0000118C:
	dc.b $12,$00,$E8,$01,$B1,$01,$02,$01,$00,$0F,$24,$2E,$01,$BE,$08,$2E
	dc.b $00,$01,$00,$45,$67,$02,$46,$82,$03,$02,$4E,$75,$08,$AE,$00,$02
	dc.b $01,$D6,$67,$08,$13,$7C,$00,$0F,$00,$1F,$60,$24,$08,$AE,$00,$07
	dc.b $01,$D6,$67,$08,$13,$7C,$00,$09,$00,$1F,$60,$14,$13,$7C,$00,$0C
	dc.b $00,$1F,$08,$2E,$00,$00,$01,$D6,$67,$06,$13,$7C,$00,$06,$00,$1F
	dc.b $42,$AE,$00,$3E,$02,$2E,$00,$F8,$01,$D6,$60,$00,$FF,$74,$00,$00
loc_0_000011EC:
	dc.b $48,$E7,$20,$02,$2C,$49,$30,$28,$00,$18,$6B,$00,$01,$C6,$31,$7C
	dc.b $08,$00,$00,$9C,$08,$2E,$00,$04,$00,$45,$66,$5C,$02,$40,$0F,$FF
	dc.b $67,$00,$01,$3E,$08,$AE,$00,$06,$01,$D6,$66,$00,$01,$9A,$C0,$6E
	dc.b $01,$D0,$08,$2E,$00,$07,$00,$45,$66,$3E,$12,$00,$08,$2E,$00,$00
	dc.b $00,$45,$67,$06,$14,$2E,$00,$42,$05,$81,$B2,$2E,$00,$23,$66,$0A
	dc.b $08,$EE,$00,$02,$01,$D8,$60,$00,$00,$B0,$B2,$2E,$00,$22,$66,$18
	dc.b $08,$2E,$00,$02,$01,$D8,$67,$EE,$08,$AE,$00,$02,$01,$D8,$33,$FC
	dc.b $80,$01,$00,$DF,$F0,$9A,$60,$DE,$08,$2E,$00,$05,$01,$D8,$67,$3E
	dc.b $08,$2E,$00,$01,$01,$BD,$66,$16,$61,$00,$FF,$16,$67,$08,$08,$00
	dc.b $00,$08,$67,$12,$60,$28,$08,$00,$00,$08,$66,$0A,$60,$20,$08,$2E
	dc.b $00,$00,$01,$BD,$60,$E6,$08,$EE,$00,$07,$01,$D6,$4A,$AE,$00,$3E
	dc.b $66,$4A,$2D,$6E,$00,$2A,$00,$3E,$60,$42,$52,$AE,$00,$3A,$22,$2E
	dc.b $00,$36,$B2,$AE,$00,$3A,$6F,$26,$20,$6E,$00,$2A,$10,$C0,$2D,$48
	dc.b $00,$2A,$52,$AE,$00,$3A,$B1,$EE,$00,$32,$6D,$06,$2D,$6E,$00,$26
	dc.b $00,$2A,$92,$AE,$01,$CA,$B2,$AE,$00,$3A,$6C,$10,$60,$0C,$4A,$AE
	dc.b $00,$3E,$66,$06,$2D,$6E,$00,$2A,$00,$3E,$61,$30,$43,$EE,$00,$D4
	dc.b $2C,$6E,$00,$62,$4E,$AE,$FF,$4C,$4C,$DF,$40,$04,$4E,$75
loc_0_000012FA:
	move.b $0022(a6),app_01D9(a6)
	bclr.b #3,$01D8(a6)
	btst.b #2,app_0045(a6)
	beq.b loc_0_00001334
	bclr.b #CIAB_COMRTS,_ciab+ciapra.l
	bra.b loc_0_00001334
loc_0_00001318:
	move.b $0023(a6),app_01D9(a6)
	bset.b #3,$01D8(a6)
	btst.b #2,app_0045(a6)
	beq.b loc_0_00001334
	bset.b #CIAB_COMRTS,_ciab+ciapra.l
loc_0_00001334:
	btst.b #7,app_0045(a6)
	bne.b loc_0_00001346
	move.w #INTF_SETCLR|INTF_TBE,_custom+intena.l
	rts
loc_0_00001346:
	clr.b app_01D9(a6)
	rts
	dc.b $08,$2E,$00,$06,$01,$D6,$66,$A0,$08,$EE,$00,$06,$01,$D6,$2F,$09
	dc.b $43,$EE,$01,$82,$42,$A9,$00,$20,$20,$2E,$00,$6A,$E2,$88,$66,$02
	dc.b $70,$7F,$23,$40,$00,$24,$33,$7C,$00,$09,$00,$1C,$2F,$0E,$2C,$69
	dc.b $00,$14,$4E,$AE,$FF,$E2,$2C,$5F,$22,$5F,$60,$00,$FF,$6C
loc_0_0000138A:
	dc.b $48,$E7,$20,$02,$2C,$49,$08,$AE,$00,$06,$01,$D6,$67,$00,$FF,$5C
	dc.b $30,$39,$00,$DF,$F0,$18,$02,$40,$0F,$FF,$66,$00,$FF,$4E,$08,$EE
	dc.b $00,$02,$01,$D6,$60,$00,$FE,$E8,$41,$EE,$01,$82,$61,$00,$F2,$52
	dc.b $60,$00,$FE,$5E,$33,$FC,$08,$00,$00,$DF,$F0,$9C,$08,$EE,$00,$00
	dc.b $01,$D6,$60,$00,$FE,$CA
    SECTION section_1,code
    SECTION section_2,data
    SECTION section_3,data
