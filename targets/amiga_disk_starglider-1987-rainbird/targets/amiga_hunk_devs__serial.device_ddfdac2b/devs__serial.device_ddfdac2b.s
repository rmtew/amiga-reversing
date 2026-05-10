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
loc_0_00000000:
	dc.b "serial 33.2 (19 Feb 1986)"	; string
	dc.b $0D,$0A,$00
resident:	; STRUCT RT
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l loc_0_000013AC	; APTR RT_ENDSKIP
	dc.b RTF_COLDSTART	; UBYTE RT_FLAGS = RTF_COLDSTART
	dc.b $21	; UBYTE RT_VERSION
	dc.b NT_DEVICE	; UBYTE RT_TYPE = NT_DEVICE
	dc.b $3C	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l loc_0_00000000	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
	dc.b $00,$00
resident_name:
	dc.b "serial.device",$00	; string
loc_0_00000046:
	dc.b "timer.device",$00	; string
	dc.b $00
loc_0_00000054:
	dc.b "intuition.library",$00	; string
loc_0_00000066:
	dc.b "misc.resource",$00	; string
resident_vectors:
	dc.b $FF,$FF
	dc.w $0012
	dc.w $033C
	dc.w $0588
	dc.w $0010
	dc.w $041A
	dc.w $0494
	dc.w $FFFF
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_extfunc:
	rts
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_open:
	clr.b $001F(a1)
	tst.w $0020(a6)
	beq.b loc_0_000000AC
	btst.b #5,app_0045(a6)
	beq.b loc_0_000000A2
	btst.b #5,$004F(a1)
	bne.w loc_0_000002AC
loc_0_000000A2:
	move.b #$1,$001F(a1)
	bra.w loc_0_0000048C
loc_0_000000AC:
	clr.b $01D8(a6)
	clr.b $01D6(a6)
	move.w #$C8,$01DC(a6)
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
	lea.l loc_0_00000054(pc),a1
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$0228(a6)
	movea.l (a7)+,a6
	movea.l d0,a3
	beq.w loc_0_00000202
	move.l #$100,d0
	moveq.l #1,d1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00C6(a6)
	movea.l (a7)+,a6
	movea.l d0,a0
	beq.w loc_0_00000202
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
	lea.l loc_0_00000394(pc),a0
	move.w $0(a0,d0.w),$01C4(a6)
	clr.w $01C2(a6)
	move.b #$8,app_0043(a6)
	move.b $00B6(a3),d0
	btst #0,d0
	beq.b loc_0_00000160
	move.b #$7,app_0043(a6)
loc_0_00000160:
	move.b #$8,d1
	lsr.b #4,d0
	sub.b d0,d1
	move.b d1,$0042(a6)
	move.b #$1,$0044(a6)
	move.b $00B7(a3),d0
	btst #4,d0
	beq.b loc_0_00000182
	move.b #$2,$0044(a6)
loc_0_00000182:
	move.b app_0043(a6),$004D(a1)
	move.b $0042(a6),$004C(a1)
	move.b $0044(a6),$004E(a1)
	bsr.w loc_0_000010E4
	move.b $00B7(a3),d0
	andi.w #15,d0
	lsl.w #1,d0
	lea.l loc_0_000003A4(pc),a0
	clr.w $0036(a6)
	move.w $0(a0,d0.w),$0038(a6)
	move.b $00B8(a3),d0
	move.b d0,d1
	lsr.b #4,d0
	beq.b loc_0_000001CE
	bset.b #0,app_0045(a6)
	cmpi.b #2,d0
	bne.b loc_0_000001D4
	bset.b #1,app_0045(a6)
	bra.b loc_0_000001DA
loc_0_000001CE:
	bclr.b #0,app_0045(a6)
loc_0_000001D4:
	bclr.b #1,app_0045(a6)
loc_0_000001DA:
	andi.b #15,d1
	beq.b loc_0_000001F4
	bset.b #7,app_0045(a6)
	cmpi.b #1,d1
	bne.b loc_0_000001FA
	bset.b #2,app_0045(a6)
	bra.b loc_0_0000020A
loc_0_000001F4:
	bclr.b #7,app_0045(a6)
loc_0_000001FA:
	bclr.b #2,app_0045(a6)
	bra.b loc_0_0000020A
loc_0_00000202:
	movea.l (a7)+,a1
	movea.l #$0,a3
loc_0_0000020A:
	btst.b #1,$01BD(a6)
	beq.b loc_0_00000218
	bset.b #0,app_0045(a6)
loc_0_00000218:
	bsr.w loc_0_00001150
	move.l $0036(a6),d2
	clr.l d0
	cmpa.l #$0,a3
	beq.b loc_0_00000230
	move.l #$100,d0
loc_0_00000230:
	bsr.w loc_0_0000033C
	tst.l d0
	beq.w loc_0_0000033A
	move.l a1,-(a7)
	lea.l $0182(a6),a1
	lea.l loc_0_00000046(pc),a0
	move.l #$1,d0
	clr.l d1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01BC(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_00000266
	movea.l (a7)+,a1
	move.b #$B,$001F(a1)
	bra.b loc_0_0000027A
loc_0_00000266:
	move.l $0014(a1),$0066(a6)
	move.l $0196(a6),$0136(a6)
	move.l $019A(a6),$013A(a6)
	movea.l (a7)+,a1
loc_0_0000027A:
	movem.l (a7)+,d2/a3
	tst.b $001F(a1)
	bne.w loc_0_000003C6
	move.w #INTF_RBF,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_TBE,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_RBF,_custom+intena.l
	btst.b #5,$004F(a1)
	beq.b loc_0_000002AC
	bset.b #5,app_0045(a6)
loc_0_000002AC:
	move.b app_0045(a6),$004F(a1)
	tst.b $001F(a1)
	bne.b loc_0_00000306
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
	bge.b loc_0_00000306
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_00000306:
	move.l $0022(a6),$0030(a1)
	move.l $0036(a6),$0034(a1)
	clr.w $0050(a1)
	move.l $0042(a6),$004C(a1)
	move.l $01C2(a6),$003C(a1)
	move.l app_006A(a6),$0040(a1)
	move.l $01BA(a6),$0038(a1)
	move.l app_006E(a6),$0044(a1)
	move.l $0072(a6),$0048(a1)
loc_0_0000033A:
	rts
loc_0_0000033C:
	move.l a1,-(a7)
	movea.l a3,a1
	beq.b loc_0_0000034E
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00D2(a6)
	movea.l (a7)+,a6
loc_0_0000034E:
	move.l d2,d0
	beq.b loc_0_00000368
	moveq.l #1,d1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00C6(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_00000368
	move.l d2,$0036(a6)
loc_0_00000368:
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
	movea.l (a7)+,a1
	rts
loc_0_00000394:
	dc.b $00,$70,$01,$2C,$04,$B0,$09,$60,$12,$C0,$25,$80,$4B,$00,$7A,$12
loc_0_000003A4:
	dc.b $02,$00,$04,$00,$08,$00,$10,$00,$1F,$40,$3E,$80
    ; KNOWN: base A6=serial.device:LIB
serial_device_lib_close:
	moveq.l #0,d0
	clr.b $001F(a1)
	tst.w $0020(a6)
	beq.w loc_0_0000048C
	subq.w #1,$0020(a6)
	bne.w loc_0_0000048C
loc_0_000003C6:
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
	bge.b loc_0_00000434
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_00000434:
	clr.w $0020(a6)
	lea.l $0122(a6),a0
	bsr.w loc_0_000005E8
	lea.l $0182(a6),a0
	bsr.w loc_0_000005E8
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
	bsr.w loc_0_0000033C
	movem.l (a7)+,d2/a1/a3
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	btst.b #6,$01D8(a6)
	beq.b loc_0_0000048C
	jsr -$0012(a6)
loc_0_0000048C:
	rts
    ; KNOWN: base A6=serial.device:LIB
serial_device_dev_beginio:
	move.b #$5,$0008(a1)
	move.w $001C(a1),d0
	cmpi.w #11,d0
	ble.w loc_0_000004A6
	move.w #$0,$001C(a1)
loc_0_000004A6:
	clr.b $001F(a1)
	lsl.w #2,d0
	lea.l loc_0_000004D0(pc),a0
	movea.l $0(a0,d0.w),a0
	jmp (a0)
loc_0_000004B6:
	move.l #$51,d1
	and.b $001E(a1),d1
	bne.b loc_0_000004CE
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_000004CE:
	rts
loc_0_000004D0:
	dc.l loc_0_00000500	; pointer_table
	dc.l loc_0_00000D00
	dc.l loc_0_000006A8
	dc.l loc_0_00000AB4
	dc.l loc_0_00000500
	dc.l loc_0_00000D7E
	dc.l loc_0_00000D98
	dc.l loc_0_00000DB2
	dc.l loc_0_00000DCE
	dc.l loc_0_00000E40
	dc.l loc_0_00000E80
	dc.l loc_0_00000F5C
loc_0_00000500:
	move.b #$FD,$001F(a1)
	bra.b loc_0_000004B6
    ; KNOWN: base A6=serial.device:LIB
serial_device_dev_abortio:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_0000051E
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
	rts
loc_0_0000051E:
	clr.b $001F(a1)
	cmpi.w #2,$001C(a1)
	beq.b loc_0_00000542
	cmpi.w #3,$001C(a1)
	beq.w loc_0_00000574
	cmpi.w #10,$001C(a1)
	beq.w loc_0_00000574
	bra.w loc_0_000005E6
loc_0_00000542:
	cmpa.l $004A(a6),a1
	bne.b loc_0_00000554
	bclr.b #1,$01D8(a6)
	clr.l $004A(a6)
	bra.b loc_0_000005C0
loc_0_00000554:
	btst.b #6,$001E(a1)
	beq.w loc_0_000005E6
	move.l a1,-(a7)
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	movea.l (a7)+,a1
	subq.w #1,$0046(a6)
	bra.b loc_0_000005C0
loc_0_00000574:
	cmpa.l $004E(a6),a1
	bne.b loc_0_000005A6
	cmpi.w #10,$001C(a1)
	bne.b loc_0_00000598
	bclr.b #5,$01D6(a6)
	beq.b loc_0_00000598
	movea.l #$DFF09E,a0
	move.w #$800,(a0)
	bsr.w loc_0_000005E8
loc_0_00000598:
	clr.l $004E(a6)
	bclr.b #4,$01D8(a6)
	bra.w loc_0_000005C0
loc_0_000005A6:
	btst.b #6,$001E(a1)
	beq.w loc_0_000005E6
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	subq.w #1,$0048(a6)
loc_0_000005C0:
	bset.b #5,$001E(a1)
	andi.b #175,$001E(a1)
	move.b #$FE,$001F(a1)
	btst.b #0,$001E(a1)
	bne.b loc_0_000005E6
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_000005E6:
	rts
loc_0_000005E8:
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
	beq.b loc_0_00000610
	bset.b #6,$01D8(a6)
	rts
loc_0_00000610:
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
loc_0_000006A8:
	clr.l $0020(a1)
	move.l $0024(a1),d1
	beq.w loc_0_000004B6
	tst.w $0046(a6)
	bne.b loc_0_000006C6
	tst.l $004A(a6)
	bne.b loc_0_000006C6
	cmp.l $003A(a6),d1
	bls.b loc_0_000006CC
loc_0_000006C6:
	bclr.b #0,$001E(a1)
loc_0_000006CC:
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
loc_0_00000702:
	dc.b $48,$E7,$20,$02,$2C,$49,$20,$2E,$00,$4A,$66,$46,$4A,$6E,$00,$46
	dc.b $6F,$00,$01,$38,$41,$EE,$00,$A2,$22,$50,$20,$11,$67,$08,$20,$80
	dc.b $C1,$89,$23,$48,$00,$04,$22,$40,$2D,$49,$00,$4A,$53,$6E,$00,$46
	dc.b $42,$AE,$00,$5A,$08,$E9,$00,$04,$00,$1E,$08,$A9,$00,$06,$00,$1E
	dc.b $2D,$69,$00,$28,$00,$52,$08,$EE,$00,$01,$01,$D8,$20,$29,$00,$24
	dc.b $60,$02,$22,$40,$4A,$AE,$00,$3A,$67,$00,$00,$F0,$22,$2E,$01,$C6
	dc.b $B2,$AE,$00,$3A,$6F,$0C,$08,$2E,$00,$03,$01,$D8,$67,$04,$61,$00
	dc.b $02,$5E,$20,$6E,$00,$2E,$10,$10,$52,$88,$B1,$EE,$00,$32,$6D,$04
	dc.b $20,$6E,$00,$26,$53,$AE,$00,$3A,$2D,$48,$00,$2E,$53,$88,$B1,$EE
	dc.b $00,$26,$66,$00,$00,$06,$20,$6E,$00,$32,$B1,$EE,$00,$3E,$67,$00
	dc.b $00,$CC,$08,$2E,$00,$00,$00,$45,$67,$3E,$08,$2E,$00,$05,$01,$D8
	dc.b $66,$36,$08,$2E,$00,$01,$01,$BD,$67,$1C,$12,$2E,$00,$42,$03,$80
	dc.b $66,$0A,$08,$2E,$00,$00,$01,$BD,$66,$10,$60,$16,$08,$2E,$00,$00
	dc.b $01,$BD,$67,$06,$60,$12,$61,$78,$67,$08,$13,$7C,$00,$09,$00,$1F
	dc.b $60,$3E,$12,$2E,$00,$42,$03,$80,$22,$29,$00,$24,$20,$6E,$00,$52
	dc.b $10,$80,$66,$04,$4A,$81,$6B,$28,$52,$A9,$00,$20,$52,$AE,$00,$52
	dc.b $B2,$A9,$00,$20,$63,$1A,$08,$29,$00,$06,$00,$4F,$67,$00,$FF,$46
	dc.b $41,$EE,$00,$6E,$72,$07,$B0,$18,$54,$C9,$FF,$FC,$66,$00,$FF,$36
	dc.b $42,$AE,$00,$4A,$08,$AE,$00,$01,$01,$D8,$08,$A9,$00,$04,$00,$1E
	dc.b $08,$29,$00,$00,$00,$1E,$66,$00,$FE,$D4,$2F,$0E,$2C,$6E,$00,$62
	dc.b $4E,$AE,$FE,$86,$2C,$5F,$60,$00,$FE,$C4,$4C,$DF,$40,$04,$4E,$75
loc_0_00000852:
	dc.b $12,$00,$E8,$01,$B1,$01,$02,$01,$00,$0F,$24,$2E,$01,$BE,$08,$2E
	dc.b $00,$01,$00,$45,$67,$02,$46,$82,$03,$02,$4E,$75,$08,$AE,$00,$02
	dc.b $01,$D6,$67,$08,$13,$7C,$00,$0F,$00,$1F,$60,$24,$08,$AE,$00,$07
	dc.b $01,$D6,$67,$08,$13,$7C,$00,$09,$00,$1F,$60,$14,$13,$7C,$00,$0C
	dc.b $00,$1F,$08,$2E,$00,$00,$01,$D6,$67,$06,$13,$7C,$00,$06,$00,$1F
	dc.b $42,$AE,$00,$3E,$02,$2E,$00,$F8,$01,$D6,$60,$00,$FF,$74
loc_0_000008B0:
	dc.b $48,$E7,$20,$12,$2C,$49,$30,$39,$00,$DF,$F0,$18,$33,$FC,$08,$00
	dc.b $00,$DF,$F0,$9C,$6B,$00,$01,$E4,$08,$2E,$00,$04,$00,$45,$66,$00
	dc.b $00,$5E,$02,$40,$03,$FF,$67,$00,$01,$4A,$08,$AE,$00,$06,$01,$D6
	dc.b $66,$00,$01,$BC,$C0,$6E,$01,$D0,$08,$2E,$00,$07,$00,$45,$66,$3E
	dc.b $12,$00,$08,$2E,$00,$00,$00,$45,$67,$06,$14,$2E,$00,$42,$05,$81
	dc.b $B2,$2E,$00,$23,$66,$0A,$08,$EE,$00,$02,$01,$D8,$60,$00,$00,$BC
	dc.b $B2,$2E,$00,$22,$66,$18,$08,$2E,$00,$02,$01,$D8,$67,$EE,$08,$AE
	dc.b $00,$02,$01,$D8,$33,$FC,$80,$01,$00,$DF,$F0,$9A,$60,$DE,$08,$2E
	dc.b $00,$05,$01,$D8,$67,$3E,$08,$2E,$00,$01,$01,$BD,$66,$16,$61,$00
	dc.b $FF,$12,$67,$08,$08,$00,$00,$08,$67,$12,$60,$28,$08,$00,$00,$08
	dc.b $66,$0A,$60,$20,$08,$2E,$00,$00,$01,$BD,$60,$E6,$08,$EE,$00,$07
	dc.b $01,$D6,$4A,$AE,$00,$3E,$66,$52,$2D,$6E,$00,$2A,$00,$3E,$60,$4A
	dc.b $52,$AE,$00,$3A,$22,$2E,$00,$36,$B2,$AE,$00,$3A,$6F,$00,$00,$2E
	dc.b $20,$6E,$00,$2A,$10,$80,$52,$AE,$00,$3A,$52,$AE,$00,$2A,$D1,$FC
	dc.b $00,$00,$00,$01,$B1,$EE,$00,$32,$6D,$06,$2D,$6E,$00,$26,$00,$2A
	dc.b $92,$AE,$01,$CA,$B2,$AE,$00,$3A,$6C,$10,$60,$0C,$4A,$AE,$00,$3E
	dc.b $66,$06,$2D,$6E,$00,$2A,$00,$3E,$61,$34,$43,$EE,$00,$D4,$2F,$0E
	dc.b $2C,$6E,$00,$62,$4E,$AE,$FF,$4C,$2C,$5F,$4C,$DF,$48,$04,$4E,$75
loc_0_000009D0:
	move.b $0022(a6),app_01D9(a6)
	bclr.b #3,$01D8(a6)
	btst.b #2,app_0045(a6)
	beq.b loc_0_00000A0A
	bclr.b #CIAB_COMRTS,_ciab+ciapra.l
	bra.b loc_0_00000A0A
loc_0_000009EE:
	move.b $0023(a6),app_01D9(a6)
	bset.b #3,$01D8(a6)
	btst.b #2,app_0045(a6)
	beq.b loc_0_00000A0A
	bset.b #CIAB_COMRTS,_ciab+ciapra.l
loc_0_00000A0A:
	btst.b #7,app_0045(a6)
	bne.b loc_0_00000A1C
	move.w #INTF_SETCLR|INTF_TBE,_custom+intena.l
	rts
loc_0_00000A1C:
	clr.b app_01D9(a6)
	rts
	dc.b $08,$2E,$00,$06,$01,$D6,$66,$A0,$08,$EE,$00,$06,$01,$D6,$2F,$09
	dc.b $43,$EE,$01,$82,$23,$7C,$00,$00,$00,$00,$00,$20,$23,$6E,$00,$6A
	dc.b $00,$24,$04,$A9,$00,$00,$00,$0A,$00,$24,$33,$7C,$00,$09,$00,$1C
	dc.b $2F,$0E,$2C,$69,$00,$14,$4E,$AE,$FF,$E2,$2C,$5F,$10,$29,$00,$1F
	dc.b $22,$5F,$4A,$00,$67,$00,$FF,$62,$13,$7C,$00,$0B,$00,$1F,$60,$00
	dc.b $FF,$58
loc_0_00000A74:
	dc.b $48,$E7,$20,$12,$2C,$49,$08,$AE,$00,$06,$01,$D6,$67,$00,$FF,$48
	dc.b $30,$39,$00,$DF,$F0,$18,$02,$40,$03,$FF,$4A,$40,$66,$00,$FF,$38
	dc.b $08,$EE,$00,$02,$01,$D6,$60,$00,$FE,$C6,$41,$EE,$01,$82,$61,$00
	dc.b $FB,$44,$60,$00,$FE,$3C,$08,$EE,$00,$00,$01,$D6,$60,$00,$FE,$B0
loc_0_00000AB4:
	clr.l $0020(a1)
	tst.l $0024(a1)
	beq.w loc_0_00000AF6
	bclr.b #0,$001E(a1)
	tst.w $0048(a6)
	bne.b loc_0_00000AD2
	tst.l $004E(a6)
	beq.b loc_0_00000AFA
loc_0_00000AD2:
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
loc_0_00000AF6:
	bra.w loc_0_000004B6
loc_0_00000AFA:
	btst.b #2,app_0045(a6)
	beq.b loc_0_00000B0E
	bsr.w loc_0_00000B34
	tst.b $001F(a1)
	bne.w loc_0_000004B6
loc_0_00000B0E:
	bset.b #4,$001E(a1)
	clr.l $005E(a6)
	move.l $0028(a1),$0056(a6)
	move.l a1,$004E(a6)
	move.w #INTF_SETCLR|INTF_TBE,_custom+intreq.l
	move.w #INTF_SETCLR|INTF_TBE,_custom+intena.l
loc_0_00000B32:
	rts
loc_0_00000B34:
	move.b _ciab+ciapra.l,d0
	andi.b #24,d0
	beq.b loc_0_00000B4C
	btst #3,d0
	beq.b loc_0_00000B4C
	move.b #$D,$001F(a1)
loc_0_00000B4C:
	rts
loc_0_00000B4E:
	dc.b $4A,$29,$01,$D9,$66,$00,$01,$82,$48,$E7,$20,$02,$2C,$49,$08,$2E
	dc.b $00,$05,$01,$D6,$66,$00,$01,$64,$4A,$AE,$00,$4E,$67,$00,$01,$10
	dc.b $22,$6E,$00,$4E,$08,$29,$00,$05,$00,$1E,$66,$00,$01,$02,$08,$2E
	dc.b $00,$02,$01,$D8,$66,$00,$01,$44,$08,$2E,$00,$02,$00,$45,$67,$2C
	dc.b $61,$A4,$08,$29,$00,$0D,$00,$1F,$66,$00,$00,$C4,$08,$00,$00,$04
	dc.b $67,$1A,$04,$6E,$00,$01,$01,$DC,$67,$00,$00,$B4,$70,$00,$30,$2E
	dc.b $01,$CE,$ED,$88,$61,$00,$03,$66,$60,$00,$01,$0A,$3D,$7C,$00,$C8
	dc.b $01,$DC,$20,$6E,$00,$56,$42,$40,$10,$10,$22,$29,$00,$24,$6A,$10
	dc.b $08,$2E,$00,$04,$01,$D8,$67,$10,$53,$AE,$00,$5E,$60,$00,$00,$80
	dc.b $B2,$AE,$00,$5E,$63,$00,$00,$78,$33,$FC,$00,$01,$00,$DF,$F0,$9C
	dc.b $08,$AE,$00,$04,$01,$D8,$C0,$6E,$01,$D2,$66,$06,$08,$EE,$00,$04
	dc.b $01,$D8,$08,$2E,$00,$00,$00,$45,$67,$20,$08,$2E,$00,$01,$01,$BD
	dc.b $67,$0A,$08,$2E,$00,$00,$01,$BD,$66,$0A,$60,$0E,$4E,$B9
	dc.l loc_0_00000852
	dc.b $67,$06,$12,$2E,$00,$43,$03,$C0,$80,$6E,$01,$D4,$33,$C0,$00,$DF
	dc.b $F0,$30,$52,$AE,$00,$56,$52,$AE,$00,$5E,$08,$29,$00,$06,$00,$4F
	dc.b $67,$0E,$41,$EE,$00,$6E,$72,$07,$B0,$18,$54,$C9,$FF,$FC,$67,$0C
	dc.b $20,$29,$00,$24,$6B,$6C,$B0,$AE,$00,$5E,$6C,$66,$23,$6E,$00,$5E
	dc.b $00,$20,$08,$AE,$00,$04,$01,$D8,$42,$AE,$00,$4E,$2F,$0E,$2C,$6E
	dc.b $00,$62,$4E,$AE,$FE,$86,$2C,$5F,$60,$00,$00,$48,$4A,$6E,$00,$48
	dc.b $67,$00,$00,$46,$41,$EE,$00,$B0,$22,$50,$20,$11,$67,$08,$20,$80
	dc.b $C1,$89,$23,$48,$00,$04,$22,$40,$2D,$40,$00,$4E,$53,$6E,$00,$48
	dc.b $08,$E9,$00,$04,$00,$1E,$08,$A9,$00,$06,$00,$1E,$42,$AE,$00,$5E
	dc.b $2D,$69,$00,$28,$00,$56,$0C,$69,$00,$0A,$00,$1C,$66,$04,$61,$00
	dc.b $01,$DE,$4C,$DF,$40,$04,$4E,$75,$4C,$DF,$40,$04,$33,$FC,$00,$01
	dc.b $00,$DF,$F0,$9A,$4E,$75,$33,$FC,$00,$01,$00,$DF,$F0,$9C,$42,$41
	dc.b $12,$29,$01,$D9,$82,$69,$01,$D4,$42,$29,$01,$D9,$33,$C1,$00,$DF
	dc.b $F0,$30,$4A,$A9,$00,$4E,$66,$06,$4A,$69,$00,$48,$67,$CE,$4E,$75
loc_0_00000D00:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_00000DE6
	move.l a1,-(a7)
	move.l $004A(a6),d0
	beq.b loc_0_00000D1A
	movea.l d0,a1
	bsr.w loc_0_0000051E
loc_0_00000D1A:
	move.l $004E(a6),d0
	beq.b loc_0_00000D26
	movea.l d0,a1
	bsr.w loc_0_0000051E
loc_0_00000D26:
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
	bsr.w loc_0_00000FCE
	bsr.w loc_0_00000D86
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
	bra.w loc_0_000004B6
loc_0_00000D7E:
	bsr.w loc_0_00000D86
	bra.w loc_0_000004B6
loc_0_00000D86:
	move.l $0026(a6),$002A(a6)
	move.l $0026(a6),$002E(a6)
	clr.l $003A(a6)
	rts
loc_0_00000D98:
	move.l $004E(a6),d0
	beq.b loc_0_00000DA4
	bset.b #2,$01D8(a6)
loc_0_00000DA4:
	move.l $004A(a6),d0
	beq.b loc_0_00000DAE
	bsr.w loc_0_000009EE
loc_0_00000DAE:
	bra.w loc_0_000004B6
loc_0_00000DB2:
	bclr.b #2,$01D8(a6)
	move.l $004A(a6),d0
	beq.b loc_0_00000DC2
	bsr.w loc_0_000009D0
loc_0_00000DC2:
	move.w #INTF_SETCLR|INTF_TBE,_custom+intreq.l
	bra.w loc_0_000004B6
loc_0_00000DCE:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_00000DE6
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
	bra.w loc_0_000004B6
loc_0_00000DE6:
	move.l a1,-(a7)
	lea.l $00A2(a6),a0
	bsr.w loc_0_00000E00
	lea.l $00B0(a6),a0
	bsr.w loc_0_00000E00
	clr.l $0046(a6)
	movea.l (a7)+,a1
	rts
loc_0_00000E00:
	movea.l (a0),a1
	move.l (a1),d0
	beq.b loc_0_00000E0E
	move.l d0,(a0)
	exg d0,a1
	move.l a0,$0004(a1)
loc_0_00000E0E:
	tst.l d0
	beq.w loc_0_00000E1C
	movea.l d0,a1
	bsr.w loc_0_00000E1E
	bra.b loc_0_00000E00
loc_0_00000E1C:
	rts
loc_0_00000E1E:
	bset.b #5,$001E(a1)
	move.b #$FE,$001F(a1)
	btst.b #0,$001E(a1)
	bne.b loc_0_00000E3E
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_00000E3E:
	rts
loc_0_00000E40:
	movea.l #$BFD0FE,a0
	move.b (a0),d0
	andi.b #111,d0
	btst.b #2,app_0045(a6)
	beq.b loc_0_00000E60
	btst.b #3,$01D8(a6)
	beq.b loc_0_00000E60
	bset #4,d0
loc_0_00000E60:
	move.b d0,$0051(a1)
	move.b $01D6(a6),$0050(a1)
	andi.b #31,$0050(a1)
	move.l $003A(a6),$0020(a1)
	andi.b #249,$01D6(a6)
	bra.w loc_0_000004B6
loc_0_00000E80:
	bclr.b #0,$001E(a1)
	btst.b #3,$004F(a1)
	beq.b loc_0_00000E9E
	tst.w $0048(a6)
	bne.w loc_0_00000AD2
	tst.l $004E(a6)
	bne.w loc_0_00000AD2
loc_0_00000E9E:
	move.l app_006A(a6),d0
	bsr.w loc_0_00000F1A
	tst.b $001F(a1)
	bne.b loc_0_00000EC2
	move.l a1,$004E(a6)
	bset.b #5,$01D6(a6)
	movea.l #$DFF09E,a0
	move.w #$8800,(a0)
	bra.b loc_0_00000ED2
loc_0_00000EC2:
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
	clr.l $004E(a6)
loc_0_00000ED2:
	rts
loc_0_00000ED4:
	dc.b $08,$A9,$00,$05,$01,$D6,$67,$34,$2F,$0E,$2C,$49,$22,$6E,$00,$4E
	dc.b $67,$28,$0C,$69,$00,$0A,$00,$1C,$66,$20,$08,$EE,$00,$01,$01,$D6
	dc.b $42,$AE,$00,$4E,$20,$7C,$00,$DF,$F0,$9E,$30,$BC,$08,$00,$2F,$0E
	dc.b $2C,$6E,$00,$62,$4E,$AE,$FE,$86,$2C,$5F,$2C,$5F,$33,$FC,$80,$01
	dc.b $00,$DF,$F0,$9A,$4E,$75
loc_0_00000F1A:
	move.w #INTF_TBE,_custom+intena.l
	move.l a1,-(a7)
	lea.l $0122(a6),a1
	move.l #$0,$0020(a1)
	move.l d0,$0024(a1)
	move.w #$9,$001C(a1)
	move.l a6,-(a7)
	movea.l $0014(a1),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	move.b $001F(a1),d0
	movea.l (a7)+,a1
	tst.b d0
	beq.b loc_0_00000F58
	move.b #$B,$001F(a1)
	clr.b d0
loc_0_00000F58:
	rts
	dc.b $00,$00
loc_0_00000F5C:
	btst.b #7,$004F(a1)
	beq.b loc_0_00000F8A
	bset.b #7,app_0045(a6)
	bclr.b #2,$01D8(a6)
	btst.b #3,$01D8(a6)
	beq.b loc_0_00000F90
	bclr.b #7,$004F(a1)
	bsr.w loc_0_000009D0
	bset.b #7,$004F(a1)
	bra.b loc_0_00000F90
loc_0_00000F8A:
	bclr.b #7,app_0045(a6)
loc_0_00000F90:
	btst.b #1,$01D8(a6)
	bne.b loc_0_00000FAC
	tst.l $004E(a6)
	bne.b loc_0_00000FAC
	btst.b #4,$001E(a1)
	bne.b loc_0_00000FAC
	tst.l $0046(a6)
	beq.b loc_0_00000FB6
loc_0_00000FAC:
	move.b #$1,$001F(a1)
	bra.w loc_0_00000FCA
loc_0_00000FB6:
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	bsr.w loc_0_00000FCE
	move.w #INTF_SETCLR|INTF_RBF|INTF_TBE,_custom+intena.l
loc_0_00000FCA:
	bra.w loc_0_000004B6
loc_0_00000FCE:
	movem.l d2/a3,-(a7)
	tst.b $004C(a1)
	beq.w loc_0_00001136
	cmpi.b #8,$004C(a1)
	bgt.w loc_0_00001136
	tst.b $004D(a1)
	beq.w loc_0_00001136
	cmpi.b #8,$004D(a1)
	bgt.w loc_0_00001136
	tst.b $004E(a1)
	beq.w loc_0_00001136
	cmpi.b #2,$004E(a1)
	bgt.w loc_0_00001136
	move.l $003C(a1),d0
	cmpi.l #112,d0
	blt.w loc_0_00001136
	cmpi.l #292000,d0
	bgt.w loc_0_00001136
	tst.l $0030(a1)
	beq.w loc_0_00001136
	move.b $004C(a1),$0042(a6)
	move.b $004D(a1),app_0043(a6)
	move.b $004E(a1),$0044(a6)
	move.l $0030(a1),$0022(a6)
	move.l $0038(a1),$01BA(a6)
	btst.b #4,$004F(a1)
	beq.b loc_0_00001054
	bset.b #7,$004F(a1)
loc_0_00001054:
	btst.b #1,$003B(a1)
	beq.b loc_0_00001062
	bset.b #0,$004F(a1)
loc_0_00001062:
	move.b app_0045(a6),d0
	andi.b #32,d0
	move.b $004F(a1),app_0045(a6)
	or.b d0,app_0045(a6)
	move.b app_0045(a6),$004F(a1)
	move.l $003C(a1),$01C2(a6)
	bsr.w loc_0_00001150
	move.l $0044(a1),app_006E(a6)
	move.l $0048(a1),$0072(a6)
	bsr.w loc_0_000010E4
	tst.l $0040(a1)
	beq.w loc_0_00001136
	move.l $0040(a1),app_006A(a6)
	move.l $0036(a6),d0
	cmp.l $0034(a1),d0
	beq.b loc_0_000010DE
	move.l $0034(a1),d2
	cmpi.l #512,d2
	blt.b loc_0_000010D8
	movea.l $0026(a6),a3
	bsr.w loc_0_0000033C
	tst.l d0
	bne.b loc_0_000010DE
	move.l $0036(a6),d2
	move.l d2,$0034(a1)
	clr.l d0
	movea.l #$0,a3
	bsr.w loc_0_0000033C
loc_0_000010D8:
	move.b #$4,$001F(a1)
loc_0_000010DE:
	movem.l (a7)+,d2/a3
	rts
loc_0_000010E4:
	clr.l d0
	clr.l d1
	move.b $004D(a1),d0
	bset d0,d1
	cmpi.b #2,$004E(a1)
	bne.b loc_0_000010FA
	lsl.w #1,d1
	bset d0,d1
loc_0_000010FA:
	btst.b #0,app_0045(a6)
	beq.b loc_0_00001104
	lsl.w #1,d1
loc_0_00001104:
	move.w d1,$01D4(a6)
	bsr.w loc_0_00001120
	move.w d0,$01D2(a6)
	clr.w d0
	move.b $004C(a1),d0
	bsr.w loc_0_00001120
	move.w d0,$01D0(a6)
	rts
loc_0_00001120:
	btst.b #0,app_0045(a6)
	bne.b loc_0_0000112A
	subq.w #1,d0
loc_0_0000112A:
	lsl.w #1,d0
	lea.l loc_0_0000113E(pc),a0
	move.w $0(a0,d0.w),d0
	rts
loc_0_00001136:
	move.b #$5,$001F(a1)
	bra.b loc_0_000010DE
loc_0_0000113E:
	dc.b $00,$01,$00,$03,$00,$07,$00,$0F,$00,$1F,$00,$3F,$00,$7F,$00,$FF
	dc.b $01,$FF
loc_0_00001150:
	move.l $01C2(a6),d0
	move.l d0,d1
	lsl.l #3,d0
	sub.l d1,d0
	move.l #$17D7840,d1
	cmpi.l #65535,d0
	ble.b loc_0_00001176
	lsr.l #5,d0
	divu.w d0,d1
	andi.l #65535,d1
	lsr.l #5,d1
	bra.b loc_0_00001178
loc_0_00001176:
	divu.w d0,d1
loc_0_00001178:
	move.w d1,$01CE(a6)
	move.w $01CE(a6),d0
	bclr.b #5,$01D8(a6)
	cmpi.b #8,$0042(a6)
	bne.b loc_0_000011A0
	btst.b #0,app_0045(a6)
	beq.b loc_0_000011A0
	ori.w #15,d0
	bset.b #5,$01D8(a6)
loc_0_000011A0:
	move.w d0,_custom+serper.l
	rts
loc_0_000011A8:
	dc.b $E0,$00,$00,$08,$03,$00,$C0,$00,$00,$0A
	dc.l resident_name
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$21,$D0,$00,$00,$16
	dc.b $00,$02,$C0,$00,$00,$22,$11,$13,$00,$00,$C0,$00,$01,$C2,$00,$00
	dc.b $25,$80,$D0,$00,$01,$CE,$01,$74,$D0,$00,$01,$D0,$00,$FF,$D0,$00
	dc.b $01,$D2,$00,$FF,$D0,$00,$01,$D4,$01,$00,$C0,$00,$00,$42,$08,$08
	dc.b $01,$00,$C0,$00,$00,$6A,$00,$03,$D0,$90,$C0,$00,$00,$36,$00,$00
	dc.b $02,$00,$C0,$00,$01,$BE,$69,$96,$69,$96,$00,$00
resident_init:
	movem.l a0/a2,-(a7)
	lea.l resident_vectors(pc),a0
	lea.l loc_0_000011A8(pc),a1
	suba.l a2,a2
	move.l #$1DE,d0
	move.l a6,-(a7)
	movea.l a6,a6
	jsr -$0054(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,a0/a2
	tst.l d0
	beq.w loc_0_000013A8
	move.l a6,d1
	movem.l a3/a6,-(a7)
	movea.l d0,a6
	move.l a0,$01AA(a6)
	move.l d1,$0062(a6)
	move.w #$C8,$01DC(a6)
	lea.l loc_0_00000066(pc),a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01F2(a6)
	movea.l (a7)+,a6
	move.l d0,$01B6(a6)
	beq.w loc_0_000013A8
	lea.l resident_name(pc),a1
	move.l #$0,d0
	move.l a6,-(a7)
	movea.l $01B6(a6),a6
	jsr -$0006(a6)
	tst.l d0
	bne.w loc_0_0000128C
	move.l #$1,d0
	jsr -$0006(a6)
loc_0_0000128C:
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_0000129A
	movem.l (a7)+,a3/a6
	bra.w loc_0_000013A8
loc_0_0000129A:
	lea.l app_00BE(a6),a0
	lea.l loc_0_00000B32.l,a3
	bsr.b loc_0_000012BA
	lea.l $00D4(a6),a0
	lea.l loc_0_00000702.l,a3
	bsr.b loc_0_000012BA
	bra.w loc_0_000012FA
loc_0_000012B6:
	move.l a0,$0010(a1)
loc_0_000012BA:
	move.b #$10,$0009(a0)
	move.l #resident_name,$000A(a0)
	move.l a3,$0012(a0)
	move.l a6,$000E(a0)
	rts
loc_0_000012D2:
	move.l #resident_name,$000A(a1)
	move.b #$0,$0009(a1)
	move.b #$1,$000E(a1)
	move.b #$4,$0008(a1)
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$0162(a6)
	movea.l (a7)+,a6
	rts
loc_0_000012FA:
	lea.l $00EA(a6),a1
	bsr.b loc_0_000012D2
	lea.l $010C(a6),a0
	lea.l loc_0_00000ED4.l,a3
	bsr.b loc_0_000012B6
	lea.l $0122(a6),a0
	move.b #$5,$0008(a0)
	lea.l $00EA(a6),a3
	move.l a3,$000E(a0)
	lea.l $014A(a6),a1
	bsr.b loc_0_000012D2
	lea.l $016C(a6),a0
	lea.l loc_0_00000A74.l,a3
	bsr.b loc_0_000012B6
	lea.l $0182(a6),a0
	move.b #$5,$0008(a0)
	lea.l $014A(a6),a3
	move.l a3,$000E(a0)
	movea.l a6,a1
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$01B0(a6)
	movea.l (a7)+,a6
	lea.l app_0076(a6),a1
	moveq.l #11,d0
	move.l #loc_0_000008B0,$0012(a1)
	bsr.b loc_0_00001388
	move.l d0,$01AE(a6)
	lea.l $008C(a6),a1
	move.l #loc_0_00000B4E,$0012(a1)
	moveq.l #0,d0
	bsr.b loc_0_00001388
	move.l d0,$01B2(a6)
	move.w #INTF_RBF|INTF_TBE,_custom+intena.l
	moveq.l #1,d0
	movem.l (a7)+,a3/a6
	bra.b loc_0_000013A6
loc_0_00001388:
	move.l a6,$000E(a1)
	move.l #resident_name,$000A(a1)
	move.b #$2,$0008(a1)
	move.l a6,-(a7)
	movea.l $0062(a6),a6
	jsr -$00A2(a6)
	movea.l (a7)+,a6
loc_0_000013A6:
	rts
loc_0_000013A8:
	clr.l d0
	bra.b loc_0_000013A6
loc_0_000013AC:
    SECTION section_1,code
    SECTION section_2,data
    SECTION section_3,data
