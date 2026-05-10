    INCLUDE "exec/alerts.i"
    INCLUDE "exec/devices.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/intbits.i"

    RSSET LIB_SIZE
    RS.B 27
app_003D RS.B 1
    RS.B 46
app_006C RS.L 1
    RS.B 78
app_00BE RS.L 1
    RS.B 2292
app_09B6 RS.B 1
    RS.B 2
app_09B9 RS.B 1
app_SIZEOF EQU __RS

_ciab	EQU	$BFD000
_custom	EQU	$DFF000

    SECTION section_0,code
	dc.b $60,$00,$01,$4A
resident:	; STRUCT RT
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l loc_0_00000D58	; APTR RT_ENDSKIP
	dc.b RTF_COLDSTART	; UBYTE RT_FLAGS = RTF_COLDSTART
	dc.b $23	; UBYTE RT_VERSION
	dc.b NT_DEVICE	; UBYTE RT_TYPE = NT_DEVICE
	dc.b $F6	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
resident_name:
    ; invalid overlap: decoded code at $001E starts at structured data; emitted as data
	dc.b "printer.device",$00	; string
	dc.b $00
resident_idstring:
    ; invalid overlap: decoded code at $002E starts at structured data; emitted as data
	dc.b "printer 35.562 (20 Jul 1988)",$0D,$0A,$00	; string
	dc.b $00,$00,$00
    ; KNOWN: base A6=printer.device:LIB
printer_device_dev_beginio:
	movem.l d2/a3,-(a7)
	movea.l a1,a3
	andi.b #15,$001E(a3)
	clr.b $001F(a3)
	move.w $001C(a3),d2
	cmp.w $0032(a6),d2
	blt.b loc_0_0000006C
	moveq.l #0,d2
loc_0_0000006C:
	movea.l $002E(a6),a0
	tst.b $0(a0,d2.w)
	bmi.b loc_0_000000BA
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	tst.b $001F(a3)
	bne.b loc_0_000000AA
	lea.l $0034(a6),a0
	movea.l a3,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$016E(a6)
	movea.l (a7)+,a6
	bset.b #4,$001E(a3)
	bclr.b #0,$001E(a3)
loc_0_000000AA:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	bra.b loc_0_000000C8
loc_0_000000BA:
	lsl.w #2,d2
	movea.l $002A(a6),a0
	movea.l $0(a0,d2.w),a0
	movea.l a3,a1
	jsr (a0)
loc_0_000000C8:
	movem.l (a7)+,d2/a3
	rts
    ; KNOWN: base A6=printer.device:LIB
printer_device_dev_abortio:
	btst.b #7,$001E(a1)
	bne.w loc_0_000000E6
	move.b #$FE,$001F(a1)
	bsr.w loc_0_00000B12
	bsr.w loc_0_0000098C
loc_0_000000E6:
	moveq.l #0,d0
	rts
loc_0_000000EA:
	movem.l d2/a3,-(a7)
	move.l d0,d2
	movea.l a1,a3
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0078(a6)
	movea.l (a7)+,a6
	bset.b #7,$001E(a3)
	bne.b loc_0_00000138
	move.b d2,$001F(a1)
	btst.b #4,$001E(a3)
	beq.b loc_0_00000120
	movea.l (a3),a0
	movea.l $0004(a3),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
loc_0_00000120:
	btst.b #0,$001E(a3)
	bne.b loc_0_00000138
	movea.l a3,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_00000138:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$007E(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,d2/a3
	rts
resident_init:
	movem.l a0/a2,-(a7)
	lea.l resident_vectors(pc),a0
	lea.l loc_0_0000037E(pc),a1
	lea.l loc_0_0000019E(pc),a2
	move.l #$AA1,d0
	jsr -$0054(a6)
	movem.l (a7)+,a0/a2
	tst.l d0
	bne.b loc_0_0000018A
	movem.l d7/a5-a6,-(a7)
	move.l #AG_MakeLib,d7
	movea.l $0004.w,a6
	jsr _LVOAlert(a6)
	movem.l (a7)+,d7/a5-a6
	bra.b loc_0_0000019C
	dc.b $4A,$80,$67,$12
loc_0_0000018A:
	movea.l d0,a1
	move.l a1,loc_1_00000000.l
	move.l a0,$0022(a1)
	jsr -$01B0(a6)
	moveq.l #1,d0
loc_0_0000019C:
	rts
loc_0_0000019E:
	dc.b $2F,$0E,$20,$40,$23,$CE
	dc.l loc_1_0000000C
	dc.b $2C,$40,$43,$FA,$01,$B5,$70,$00,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FD,$D8,$2C,$5F,$23,$C0
	dc.l loc_1_00000010
	dc.b $67,$00,$01,$46,$43,$FA,$01,$A3,$70,$00,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FD,$D8,$2C,$5F,$23,$C0
	dc.l loc_1_00000014
	dc.b $67,$00,$00,$FE,$43,$FA,$01,$67,$70,$00,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FD,$D8,$2C,$5F,$23,$C0
	dc.l loc_1_00000018
	dc.b $67,$00,$00,$B6,$41,$FA,$01,$3C,$70,$01,$72,$00,$43,$EE,$01,$10
	dc.b $2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$44,$2C,$5F,$4A,$80,$66,$6C,$41,$EE,$01,$B6,$2D,$48
	dc.b $01,$94,$30,$3C,$03,$FF,$32,$3C,$AF,$DB,$30,$C1,$51,$C8,$FF,$FC
	dc.b $93,$C9,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$DA,$2C,$5F,$41,$EE,$09,$B6,$43,$EE,$01,$5A,$23,$48
	dc.b $00,$3E,$48,$E0,$80,$02,$23,$48,$00,$36,$45,$FA,$04,$FE,$70,$00
	dc.b $26,$40,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$E6,$2C,$5F,$70,$02,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$C2,$2C,$5F,$42,$39
	dc.l loc_1_00000020
	dc.b $20,$0E,$2C,$5F,$4E,$75,$48,$E7,$01,$06,$2E,$3C,$00,$03,$80,$15
	dc.b $2C,$78,$00,$04,$4E,$AE,$FF,$94,$4C,$DF,$60,$80,$22,$79
	dc.l loc_1_00000018
	dc.b $2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$62,$2C,$5F,$48,$E7,$01,$06,$2E,$3C,$00,$03,$80,$04
	dc.b $2C,$78,$00,$04,$4E,$AE,$FF,$94,$4C,$DF,$60,$80,$22,$79
	dc.l loc_1_00000014
	dc.b $2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$62,$2C,$5F,$48,$E7,$01,$06,$2E,$3C,$00,$03,$80,$02
	dc.b $2C,$78,$00,$04,$4E,$AE,$FF,$94,$4C,$DF,$60,$80,$22,$79
	dc.l loc_1_00000010
	dc.b $2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$62,$2C,$5F,$48,$E7,$01,$06,$2E,$3C,$00,$03,$80,$07
	dc.b $2C,$78,$00,$04,$4E,$AE,$FF,$94,$4C,$DF,$60,$80,$22,$4E,$30,$2E
	dc.b $00,$10,$92,$C0,$D0,$6E,$00,$12,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FF,$2E,$2C,$5F,$70,$00,$60,$00,$FF
	dc.b "Jtimer.device",$00	; string
loc_0_0000034F:
	dc.b "intuition.library",$00	; string
loc_0_00000361:
	dc.b "dos.library",$00	; string
loc_0_0000036D:
	dc.b "graphics.library",$00	; string
loc_0_0000037E:
	dc.b $E0,$00,$00,$08,$03,$00,$C0,$00,$00,$0A
	dc.l resident_name
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$23,$D0,$00,$00,$16
	dc.b $02,$32,$C0,$00,$00,$2A
	dc.l loc_0_0000040C
	dc.b $C0,$00,$00,$2E
	dc.l loc_0_00000440
	dc.b $D0,$00,$00,$32,$00,$0D,$E0,$00,$00,$3C,$04,$00,$C0,$00,$00,$3E
	dc.l resident_name
	dc.b $E0,$00,$01,$40,$04,$00,$C0,$00,$01,$42
	dc.l resident_name
	dc.b $E0,$00,$01,$62,$01,$00,$E0,$00,$01,$63,$00,$00,$C0,$00,$01,$64
	dc.l resident_name
	dc.b $C0,$00,$00,$64
	dc.l loc_0_00000858
	dc.b $C0,$00,$00,$68
	dc.l loc_0_000009BA
	dc.b $D0,$00,$00,$5A,$FF,$FF,$00,$00
resident_vectors:
	dc.b $FF,$FF
	dc.w $0118
	dc.w $0224
	dc.w $006C
	dc.w $0116
	dc.w $FC54
	dc.w $FCD2
	dc.w $FFFF
loc_0_0000040C:
	dc.l loc_0_00000730	; pointer_table
	dc.l loc_0_0000045A
	dc.l loc_0_00000758
	dc.l loc_0_00000C80
	dc.l loc_0_00000758
	dc.l loc_0_00000758
	dc.l loc_0_00000738
	dc.l loc_0_00000740
	dc.l loc_0_00000748
	dc.l loc_0_00000C94
	dc.l loc_0_00000CC0
	dc.l loc_0_00000CD4
	dc.l loc_0_0000044E
loc_0_00000440:
	dc.b $FF,$FF,$FF,$00,$FF,$FF,$FF,$FF,$FF,$00,$00,$00,$FF,$00
loc_0_0000044E:
	move.l a1,-(a7)
	jsr loc_32_00000000.l
	movea.l (a7)+,a1
	rts
loc_0_0000045A:
	bsr.w loc_0_00000738
	bsr.w loc_0_00000748
	bsr.w loc_0_00000740
	rts
    ; KNOWN: base A6=printer.device:LIB
printer_device_lib_expunge:
	tst.w $0020(a6)
	bne.w loc_0_0000050A
	move.l a6,-(a7)
	jsr loc_8_000001A2.l
	addq.l #4,a7
	lea.l $015A(a6),a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0120(a6)
	movea.l (a7)+,a6
	lea.l $0110(a6),a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$01C2(a6)
	movea.l (a7)+,a6
	movea.l loc_1_00000018.l,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$019E(a6)
	movea.l (a7)+,a6
	movea.l loc_1_00000014.l,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$019E(a6)
	movea.l (a7)+,a6
	movea.l loc_1_00000010.l,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$019E(a6)
	movea.l (a7)+,a6
	move.l $0022(a6),-(a7)
	movea.l a6,a1
	move.w $0010(a6),d0
	suba.w d0,a1
	add.w $0012(a6),d0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$00D2(a6)
	movea.l (a7)+,a6
	movea.l a6,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	move.l (a7)+,d0
	rts
loc_0_0000050A:
	bset.b #7,app_09B6(a6)
	moveq.l #0,d0
    ; KNOWN: base A6=printer.device:LIB
printer_device_lib_extfunc:
	rts
    ; KNOWN: base A6=printer.device:LIB
printer_device_lib_open:
	move.l a3,-(a7)
	movea.l a1,a3
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	addq.w #1,$0020(a6)
	cmpi.w #1,$0020(a6)
	bne.w loc_0_000005E8
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	suba.l a1,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0126(a6)
	movea.l (a7)+,a6
	move.l d0,loc_1_0000001C.l
	lea.l $0034(a6),a0
	move.l a0,$0018(a3)
	move.l a6,-(a7)
	jsr loc_8_00000000.l
	addq.l #4,a7
	tst.l d0
	bne.w loc_0_000005F8
	cmpi.b #0,app_09B9(a6)
	beq.b loc_0_00000588
	cmpi.b #1,app_09B9(a6)
	bne.w loc_0_000005F6
	lea.l loc_0_00000612(pc),a0
	bra.b loc_0_0000058C
loc_0_00000588:
	lea.l loc_0_00000602(pc),a0
loc_0_0000058C:
	moveq.l #0,d0
	moveq.l #0,d1
	lea.l app_006C(a6),a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$01BC(a6)
	movea.l (a7)+,a6
	tst.l d0
	bne.b loc_0_000005F6
	moveq.l #40,d0
	lea.l app_006C(a6),a0
	lea.l app_00BE(a6),a1
loc_0_000005B0:
	move.w (a0)+,(a1)+
	dbf.w d0,loc_0_000005B0
	move.l a3,-(a7)
	movea.l loc_1_00000004.l,a0
	movea.l $000C(a0),a0
	jsr (a0)
	addq.l #4,a7
	tst.l d0
	bne.b loc_0_000005D4
	bclr.b #7,app_09B6(a6)
loc_0_000005D0:
	movea.l (a7)+,a3
	rts
loc_0_000005D4:
	lea.l app_006C(a6),a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$01C2(a6)
	movea.l (a7)+,a6
	bra.b loc_0_000005F6
loc_0_000005E8:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
loc_0_000005F6:
	moveq.l #-1,d0
loc_0_000005F8:
	move.b d0,$001F(a3)
	subq.w #1,$0020(a6)
	bra.b loc_0_000005D0
loc_0_00000602:
	dc.b "parallel.device",$00	; string
loc_0_00000612:
	dc.b "serial.device",$00	; string
    ; KNOWN: base A6=printer.device:LIB
printer_device_lib_close:
	move.l a3,-(a7)
	movea.l a1,a3
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
loc_0_00000632:
	lea.l $0138(a6),a0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0174(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_00000668
	lea.l app_006C(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000658
	bclr.b #0,app_09B6(a6)
	bra.b loc_0_00000632
loc_0_00000658:
	lea.l app_00BE(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000632
	bclr.b #1,app_09B6(a6)
	bra.b loc_0_00000632
loc_0_00000668:
	move.b $0147(a6),-(a7)
	move.l $0148(a6),-(a7)
	moveq.l #-1,d0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$014A(a6)
	movea.l (a7)+,a6
	move.b d0,$0147(a6)
	bmi.b loc_0_000006A0
	suba.l a1,a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0126(a6)
	movea.l (a7)+,a6
	move.l d0,$0148(a6)
	bsr.w loc_0_000009BA
	bra.b loc_0_000006A4
loc_0_000006A0:
	clr.l $0148(a6)
loc_0_000006A4:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	move.l a3,-(a7)
	movea.l loc_1_00000004.l,a0
	movea.l $0010(a0),a0
	jsr (a0)
	addq.l #4,a7
	lea.l app_006C(a6),a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$01C2(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	move.b $0147(a6),d0
	bmi.b loc_0_000006EA
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0150(a6)
	movea.l (a7)+,a6
loc_0_000006EA:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	move.l (a7)+,$0148(a6)
	move.b (a7)+,$0147(a6)
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	subq.w #1,$0020(a6)
	moveq.l #0,d0
	move.l d0,$0018(a3)
	move.l d0,$0014(a3)
	bne.b loc_0_0000072C
	btst.b #7,app_09B6(a6)
	beq.b loc_0_0000072C
	movea.l a3,a1
	jsr -$0012(a6)
loc_0_0000072C:
	movea.l (a7)+,a3
	rts
loc_0_00000730:
	moveq.l #-3,d0
	bsr.w loc_0_000000EA
	rts
loc_0_00000738:
	bset.b #0,app_003D(a6)
	rts
loc_0_00000740:
	bclr.b #0,app_003D(a6)
	rts
loc_0_00000748:
	movea.l $0048(a6),a1
	tst.l (a1)
	beq.b loc_0_00000756
	bsr.w printer_device_dev_abortio
	bra.b loc_0_00000748
loc_0_00000756:
	rts
loc_0_00000758:
	bra.w loc_0_00000730
	dc.b $4C,$EF,$50,$00,$00,$04,$70,$FF,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$B6,$2C,$5F,$2A,$00,$1D,$45,$00,$43,$41,$EE,$00,$48
	dc.b $20,$88,$58,$90,$42,$A8,$00,$04,$21,$48,$00,$08,$43,$EE,$01,$5A
	dc.b $2D,$49,$00,$44,$2D,$49,$01,$48,$70,$FF,$2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$B6,$2C,$5F,$2C,$00,$1D,$46,$01,$47,$41,$EE,$01,$4C
	dc.b $20,$88,$58,$90,$42,$A8,$00,$04,$21,$48,$00,$08,$41,$EE,$01,$38
	dc.b $2D,$48,$01,$1E,$2D,$48,$00,$7A,$2D,$48,$00,$CC,$70,$02,$22,$4C
	dc.b $2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$BC,$2C,$5F,$7E,$00,$0B,$C7,$0D,$C7,$20,$07,$2F,$0E
	dc.b $2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$C2,$2C,$5F,$24,$00,$0D,$02,$67,$36,$41,$EE,$01,$38
	dc.b $2F,$0E,$2C,$79
	dc.l loc_1_0000000C
	dc.b $4E,$AE,$FE,$8C,$2C,$5F,$4A,$80,$67,$20,$43,$EE,$00,$6C,$B0,$89
	dc.b $66,$08,$08,$AE,$00,$00,$09,$B6,$60,$DA,$43,$EE,$00,$BE,$B0,$89
	dc.b $66,$D2,$08,$AE,$00,$01,$09,$B6,$60,$CA,$0B,$02,$67,$B0,$22,$6E
	dc.b $00,$48,$4A,$91,$67,$A8,$08,$E9,$00,$05,$00,$1E,$23,$C9
	dc.l loc_1_00000008
	dc.b $30,$29,$00,$1C,$E5,$48,$20,$6E,$00,$2A,$20,$70,$00,$00,$4E,$90
	dc.b $60,$DA
loc_0_00000858:
	movea.l $0004(a7),a0
	move.l $0008(a7),d0
	bsr.b loc_0_00000864
	rts
loc_0_00000864:
	tst.l d0
	beq.b loc_0_000008A0
	move.l a6,-(a7)
	movea.l loc_1_00000000.l,a6
	movem.l d0/a0,-(a7)
	bsr.b loc_0_000008B2
	tst.b d0
	bne.b loc_0_000008A2
	movem.l (a7)+,d0/a0
	bset.b #0,app_09B6(a6)
	bne.b loc_0_000008A6
	lea.l app_006C(a6),a1
loc_0_0000088A:
	move.l d0,$0024(a1)
	move.l a0,$0028(a1)
	move.w #$3,$001C(a1)
	bsr.w loc_0_0000097A
	bsr.b loc_0_000008B2
loc_0_0000089E:
	movea.l (a7)+,a6
loc_0_000008A0:
	rts
loc_0_000008A2:
	addq.l #8,a7
	bra.b loc_0_0000089E
loc_0_000008A6:
	bset.b #1,app_09B6(a6)
	lea.l app_00BE(a6),a1
	bra.b loc_0_0000088A
loc_0_000008B2:
	movea.l loc_1_00000008.l,a0
	moveq.l #0,d0
	move.b $001F(a0),d0
	bne.b loc_0_000008CE
	move.b app_09B6(a6),d0
	not.b d0
	andi.b #3,d0
	beq.b loc_0_000008D0
	moveq.l #0,d0
loc_0_000008CE:
	rts
loc_0_000008D0:
	bsr.w loc_0_00000960
loc_0_000008D4:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	move.b $0147(a6),d1
	bset d1,d0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$013E(a6)
	movea.l (a7)+,a6
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	movea.l $014C(a6),a0
	tst.l (a0)
	beq.b loc_0_000008D4
loc_0_0000090E:
	lea.l $0138(a6),a0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0174(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_000008B2
	lea.l app_006C(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000936
	bclr.b #0,app_09B6(a6)
	bsr.b loc_0_0000098C
	bra.b loc_0_0000090E
loc_0_00000936:
	lea.l app_00BE(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000948
	bclr.b #1,app_09B6(a6)
	bsr.b loc_0_0000098C
	bra.b loc_0_0000090E
loc_0_00000948:
	lea.l $0110(a6),a1
	cmp.l a1,d0
	bne.b loc_0_0000095A
	bsr.w loc_0_00000A78
	tst.l d0
	beq.b loc_0_0000090E
	rts
loc_0_0000095A:
	bsr.b loc_0_0000098C
	bra.w loc_0_000008B2
loc_0_00000960:
	lea.l $0110(a6),a1
	move.w #$9,$001C(a1)
	movea.l loc_1_00000004.l,a0
	move.l $0032(a0),$0020(a1)
	clr.l $0024(a1)
loc_0_0000097A:
	clr.b $001E(a1)
	move.l a6,-(a7)
	movea.l $0014(a1),a6
	jsr -$001E(a6)
	movea.l (a7)+,a6
	rts
loc_0_0000098C:
	lea.l $0110(a6),a1
	cmpi.b #7,$0008(a1)
	bne.b loc_0_0000099A
	rts
loc_0_0000099A:
	movem.l a1/a6,-(a7)
	movea.l $0014(a1),a6
	jsr -$0024(a6)
	movem.l (a7)+,a1/a6
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$01DA(a6)
	movea.l (a7)+,a6
	rts
loc_0_000009BA:
	move.l a6,-(a7)
	movea.l loc_1_00000008.l,a0
	moveq.l #0,d0
	move.b $001F(a0),d0
	bne.b loc_0_000009DC
	movea.l loc_1_00000000.l,a6
loc_0_000009D0:
	move.b app_09B6(a6),d0
	andi.b #3,d0
	bne.b loc_0_000009E0
	moveq.l #0,d0
loc_0_000009DC:
	movea.l (a7)+,a6
	rts
loc_0_000009E0:
	bsr.w loc_0_00000960
loc_0_000009E4:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	move.b $0147(a6),d1
	bset d1,d0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$013E(a6)
	movea.l (a7)+,a6
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	movea.l $014C(a6),a0
	tst.l (a0)
	beq.b loc_0_000009E4
loc_0_00000A1E:
	lea.l $0138(a6),a0
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0174(a6)
	movea.l (a7)+,a6
	tst.l d0
	beq.b loc_0_000009D0
	lea.l app_006C(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000A48
	bclr.b #0,app_09B6(a6)
	bsr.w loc_0_0000098C
	bra.b loc_0_00000A1E
loc_0_00000A48:
	lea.l app_00BE(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000A5C
	bclr.b #1,app_09B6(a6)
	bsr.w loc_0_0000098C
	bra.b loc_0_00000A1E
loc_0_00000A5C:
	lea.l $0110(a6),a1
	cmp.l a1,d0
	bne.b loc_0_00000A70
	bsr.w loc_0_00000A78
	tst.l d0
	beq.b loc_0_00000A1E
	bra.w loc_0_000009DC
loc_0_00000A70:
	bsr.w loc_0_0000098C
	bra.w loc_0_000009D0
loc_0_00000A78:
	movem.l d2-d3/a2-a3,-(a7)
	cmpi.b #1,app_09B9(a6)
	bne.b loc_0_00000A8A
	pea.l loc_0_00000BEA(pc)
	bra.b loc_0_00000AD4
loc_0_00000A8A:
	movea.l #_ciab,a0
	movea.l $0004.w,a2
	move.w #INTF_INTEN,_custom+intena.l
	addq.b #1,$0126(a2)
	move.b ciaddra(a0),d0
	move.b d0,d1
	andi.b #249,d1
	move.b d1,ciaddra(a0)
	moveq.l #0,d1
	move.b ciapra(a0),d1
	andi.w #6,d1
	move.b d0,ciaddra(a0)
	add.w d1,d1
	move.l loc_0_00000B3A(pc,d1.w),-(a7)
	movea.l $0004.w,a2
	subq.b #1,$0126(a2)
	bge.b loc_0_00000AD4
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_0_00000AD4:
	movem.l loc_0_00000B4A(pc),d0-d3/a1-a3
	move.l (a7)+,$0010(a1)
	movea.l loc_1_0000001C.l,a0
	cmpi.b #13,$0008(a0)
	bne.b loc_0_00000AFA
	movea.l $00B8(a0),a0
	cmpa.w #$FFFF,a0
	bne.b loc_0_00000AFC
	clr.l d0
	bra.b loc_0_00000B0A
loc_0_00000AFA:
	suba.l a0,a0
loc_0_00000AFC:
	move.l a6,-(a7)
	movea.l loc_1_00000018.l,a6
	jsr -$015C(a6)
	movea.l (a7)+,a6
loc_0_00000B0A:
	movem.l (a7)+,d2-d3/a2-a3
	tst.l d0
	bne.b loc_0_00000B36
loc_0_00000B12:
	bclr.b #0,app_09B6(a6)
	beq.b loc_0_00000B22
	lea.l app_006C(a6),a1
	bsr.w loc_0_0000099A
loc_0_00000B22:
	bclr.b #1,app_09B6(a6)
	beq.b loc_0_00000B32
	lea.l app_00BE(a6),a1
	bsr.w loc_0_0000099A
loc_0_00000B32:
	moveq.l #1,d0
	rts
loc_0_00000B36:
	moveq.l #0,d0
	rts
loc_0_00000B3A:
	dc.l loc_0_00000B9E	; pointer_table
	dc.l loc_0_00000BC8
	dc.l loc_0_00000BEA
	dc.l loc_0_00000C1A
loc_0_00000B4A:
	dc.l $00000000,$00000000,$00000127,$0000003D	; lookup_table
	dc.l loc_0_00000B66	; pointer_table
	dc.l loc_0_00000C48
	dc.l loc_0_00000C64
loc_0_00000B66:
	ori.b #$100,d1
	ori.b #3,d6
loc_0_00000B6E:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000B8D
	ori.b #0,d0
loc_0_00000B7A:
	dc.l loc_0_00000B82
	dc.b $00,$09,$00,$00
loc_0_00000B82:
	dc.b "topaz.font",$00	; string
loc_0_00000B8D:
	dc.b "printer trouble:",$00	; string
loc_0_00000B9E:
	ori.b #$100,d1
	ori.b #15,d6
loc_0_00000BA6:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000BB2
	ori.b #0,d0
loc_0_00000BB2:
	dc.b "make printer on-line.",$00	; string
loc_0_00000BC8:
	ori.b #$100,d1
	ori.b #15,d6
loc_0_00000BD0:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000BDC
	ori.b #0,d0
loc_0_00000BDC:
	dc.b "out of paper.",$00	; string
loc_0_00000BEA:
	ori.b #$100,d1
	ori.b #15,d6
loc_0_00000BF2:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000BFE
	ori.b #0,d0
loc_0_00000BFE:
	bls.b loc_0_00000C68
	dc.b $65,$63,$6B,$20,$70,$72,$69,$6E,$74,$65,$72,$20,$61,$6E,$64,$20
	dc.b $63,$61,$62,$6C,$69,$6E,$67,$2E,$00,$00
loc_0_00000C1A:
	ori.b #$100,d1
	ori.b #15,d6
loc_0_00000C22:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000C2E
	ori.b #0,d0
loc_0_00000C2E:
	bls.b *+106
	dc.b $65,$63,$6B,$20,$70,$72,$69,$6E,$74,$65,$72,$20,$61,$6E,$64,$20
	dc.b $70,$61,$70,$65,$72,$2E,$00,$00
loc_0_00000C48:
	ori.b #$100,d1
	ori.b #3,d6
loc_0_00000C50:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000C5C
	ori.b #0,d0
loc_0_00000C5C:
	moveq.l #101,d1
	dc.b $73,$75,$6D,$65,$00,$00
loc_0_00000C64:
	ori.b #$100,d1
loc_0_00000C68:
	ori.b #3,d6
loc_0_00000C6C:
	dc.l loc_0_00000B7A	; pointer_table
	dc.l loc_0_00000C78
	ori.b #0,d0
loc_0_00000C78:
	dc.b "cancel",$00	; string
	dc.b $00
loc_0_00000C80:
	move.l a1,-(a7)
	move.l a1,-(a7)
	jsr loc_10_00000000.l
	addq.l #4,a7
	movea.l (a7)+,a1
	bsr.w loc_0_000000EA
	rts
loc_0_00000C94:
	move.l a1,-(a7)
	movea.l $0028(a1),a0
	move.l $0024(a1),d0
	clr.l $0020(a1)
	bsr.w loc_0_00000864
	tst.l d0
	bne.b loc_0_00000CB2
	movea.l (a7),a1
	move.l $0024(a1),$0020(a1)
loc_0_00000CB2:
	bsr.w loc_0_000009BA
	movea.l (a7)+,a1
	bsr.w loc_0_000000EA
	rts
	dc.b $00,$00
loc_0_00000CC0:
	move.l a1,-(a7)
	move.l a1,-(a7)
	jsr loc_2_00000114.l
	addq.l #4,a7
	movea.l (a7)+,a1
	bsr.w loc_0_000000EA
	rts
loc_0_00000CD4:
	move.l a1,-(a7)
	move.l a1,-(a7)
	jsr loc_6_00000000.l
	addq.l #4,a7
	movea.l (a7)+,a1
	bsr.w loc_0_000000EA
	rts
loc_0_00000CE8:
	movem.l a4/a6,-(a7)
	movea.l loc_1_00000000.l,a4
	movea.l $0068(a4),a0
	jsr (a0)
	tst.l d0
	bne.b loc_0_00000D50
	lea.l $0110(a4),a1
	move.w #$9,$001C(a1)
	move.l $000C(a7),$0020(a1)
	move.l $0010(a7),$0024(a1)
	clr.b $001E(a1)
	movea.l $0014(a1),a6
	jsr -$001E(a6)
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$0084(a6)
	movea.l (a7)+,a6
	lea.l $0110(a4),a1
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$01DA(a6)
	movea.l (a7)+,a6
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	jsr -$008A(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	tst.l d0
loc_0_00000D50:
	movem.l (a7)+,a4/a6
	rts
	dc.b $00,$00
loc_0_00000D58:
    SECTION section_1,data
loc_1_00000000:
	dc.b $00,$00,$00,$00
loc_1_00000004:
	dc.b $00,$00,$00,$00
loc_1_00000008:
	dc.b $00,$00,$00,$00
loc_1_0000000C:
	dc.b $00,$00,$00,$00
loc_1_00000010:
	dc.b $00,$00,$00,$00
loc_1_00000014:
	dc.b $00,$00,$00,$00
loc_1_00000018:
	dc.b $00,$00,$00,$00
loc_1_0000001C:
	dc.b $00,$00,$00,$00
loc_1_00000020:
	dcb.b $20,$00
    SECTION section_2,code
loc_2_00000000:
	move.l a2,-(a7)
	move.l $0008(a7),d0
	movea.l #loc_11_0000007A,a2
	clr.b loc_11_0000017C.l
	clr.b loc_11_0000017E.l
	movea.l loc_1_00000000.l,a0
	clr.b $0AA0(a0)
	clr.l loc_11_00000194.l
	clr.l loc_11_000001B8.l
	tst.l d0
	beq.b loc_2_00000044
	tst.l loc_3_00000000.l
	bne.b loc_2_00000044
	jsr loc_2_000000B2.l
	tst.l d0
	beq.b loc_2_0000006A
loc_2_00000044:
	jsr loc_2_0000006E.l
	moveq.l #1,d0
	move.l d0,loc_3_00000000.l
	moveq.l #3,d0
	move.l d0,loc_11_00000194.l
	move.b #$1B,(a2)
	move.b #$23,$0001(a2)
	move.b #$31,$0002(a2)
loc_2_0000006A:
	movea.l (a7)+,a2
	rts
loc_2_0000006E:
	movea.l #loc_1_00000000,a1
	movea.l (a1),a0
	move.w $0A56(a0),loc_3_00000004.l
	movea.l (a1),a0
	move.w $0A58(a0),loc_3_00000006.l
	movea.l (a1),a0
	move.w $0A5A(a0),loc_3_00000008.l
	movea.l (a1),a0
	move.w $0A5C(a0),loc_3_0000000A.l
	movea.l (a1),a0
	move.w $0A5E(a0),loc_3_0000000C.l
	movea.l (a1),a0
	move.w $0A6A(a0),loc_3_0000000E.l
	rts
loc_2_000000B2:
	movea.l #loc_1_00000000,a1
	movea.l (a1),a0
	move.w $0A56(a0),d0
	cmp.w loc_3_00000004.l,d0
	bne.b loc_2_0000010C
	movea.l (a1),a0
	move.w $0A58(a0),d0
	cmp.w loc_3_00000006.l,d0
	bne.b loc_2_0000010C
	movea.l (a1),a0
	move.w $0A5A(a0),d0
	cmp.w loc_3_00000008.l,d0
	bne.b loc_2_0000010C
	movea.l (a1),a0
	move.w $0A5C(a0),d0
	cmp.w loc_3_0000000A.l,d0
	bne.b loc_2_0000010C
	movea.l (a1),a0
	move.w $0A5E(a0),d0
	cmp.w loc_3_0000000C.l,d0
	bne.b loc_2_0000010C
	movea.l (a1),a0
	move.w $0A6A(a0),d0
	cmp.w loc_3_0000000E.l,d0
	beq.b loc_2_00000110
loc_2_0000010C:
	moveq.l #-1,d0
	bra.b loc_2_00000112
loc_2_00000110:
	moveq.l #0,d0
loc_2_00000112:
	rts
loc_2_00000114:
	link a6,#-264
	movem.l d2-d5/a2,-(a7)
	movea.l $0008(a6),a0
	move.b $0022(a0),-$0004(a6)
	move.b $0023(a0),-$0003(a6)
	move.b $0024(a0),-$0002(a6)
	move.b $0025(a0),-$0001(a6)
	moveq.l #0,d0
	move.w $0020(a0),d0
	move.l d0,d5
	moveq.l #76,d0
	cmp.l d5,d0
	bne.b loc_2_00000158
	moveq.l #0,d0
	move.b -$0004(a6),d0
	move.l d0,loc_11_000001B8.l
	clr.b d3
	bra.w loc_2_0000022A
loc_2_00000158:
	pea.l -$0004(a6)
	pea.l -$0108(a6)
	moveq.l #0,d0
	move.w $0020(a0),d0
	move.l d0,-(a7)
	jsr loc_2_00000238.l
	move.l d0,d3
	moveq.l #1,d0
	cmp.l d3,d0
	lea.l $000C(a7),a7
	ble.b loc_2_0000017E
	bra.w loc_2_0000022A
loc_2_0000017E:
	moveq.l #0,d4
	tst.l d5
	bne.b loc_2_00000194
	clr.l -(a7)
	pea.l $0001.w
	jsr loc_0_00000CE8.l
	move.l d0,d4
	addq.l #8,a7
loc_2_00000194:
	tst.l d4
	bne.w loc_2_00000210
	movea.l loc_1_00000000.l,a0
	move.b $0AA0(a0),d2
	bne.b loc_2_000001C2
	move.l d3,-(a7)
	pea.l -$0108(a6)
	jsr loc_0_00000858.l
	move.l d0,d4
	addq.l #8,a7
	bne.b loc_2_00000210
	jsr loc_0_000009BA.l
	move.l d0,d4
	bra.b loc_2_00000210
loc_2_000001C2:
	lea.l -$0108(a6),a2
loc_2_000001C6:
	move.l a2,d1
	bra.b loc_2_000001CE
loc_2_000001CA:
	addq.l #1,a2
	subq.l #1,d3
loc_2_000001CE:
	cmp.b (a2),d2
	beq.b loc_2_000001D6
	tst.l d3
	bne.b loc_2_000001CA
loc_2_000001D6:
	move.l a2,d0
	sub.l d1,d0
	move.l d0,-(a7)
	move.l d1,-(a7)
	jsr loc_0_00000858.l
	move.l d0,d4
	addq.l #8,a7
	bne.b loc_2_000001F2
	jsr loc_0_000009BA.l
	move.l d0,d4
loc_2_000001F2:
	cmp.b (a2),d2
	bne.b loc_2_00000208
	clr.l -(a7)
	pea.l $0001.w
	jsr loc_0_00000CE8.l
	addq.l #1,a2
	subq.l #1,d3
	addq.l #8,a7
loc_2_00000208:
	tst.l d3
	beq.b loc_2_00000210
	tst.l d4
	beq.b loc_2_000001C6
loc_2_00000210:
	tst.l d5
	bne.b loc_2_00000228
	tst.l d4
	bne.b loc_2_00000228
	clr.l -(a7)
	pea.l $0001.w
	jsr loc_0_00000CE8.l
	move.l d0,d4
	addq.l #8,a7
loc_2_00000228:
	move.b d4,d3
loc_2_0000022A:
	moveq.l #0,d0
	move.b d3,d0
	movem.l -$011C(a6),d2-d5/a2
	unlk a6
	rts
loc_2_00000238:
	movem.l d2-d3/a2-a3,-(a7)
	move.l $0018(a7),d2
	movea.l $001C(a7),a2
	moveq.l #0,d3
	movea.l d3,a3
	move.l a2,-(a7)
	pea.l loc_11_0000017E.l
	pea.l loc_11_00000180.l
	pea.l loc_11_0000017C.l
	move.l d2,-(a7)
	pea.l $002A(a7)
	movea.l loc_1_00000004.l,a0
	movea.l $002A(a0),a0
	jsr (a0)
	move.l d0,d0
	lea.l $0018(a7),a7
	beq.b loc_2_0000027A
loc_2_00000276:
	movea.l d0,a1
	bra.b loc_2_000002D8
loc_2_0000027A:
	movea.l loc_1_00000004.l,a0
	moveq.l #0,d0
	move.w $0016(a7),d0
	move.l d0,d3
	asl.l #2,d3
	movea.l d3,a1
	move.l $0026(a0),d0
	move.l $0(a1,d0.l),d1
	bra.b loc_2_000002B0
loc_2_00000296:
	cmpi.b #255,d0
	bne.b loc_2_000002A0
	moveq.l #-1,d0
	bra.b loc_2_00000276
loc_2_000002A0:
	cmpi.b #254,d0
	bne.b loc_2_000002A8
	clr.b d0
loc_2_000002A8:
	movea.l a3,a1
	addq.l #1,a3
	move.b d0,$0(a1,d2.l)
loc_2_000002B0:
	move.b $0(a3,d1.l),d0
	bne.b loc_2_00000296
	cmpi.w #48,$0016(a7)
	beq.b loc_2_000002CE
	cmpi.w #57,$0016(a7)
	beq.b loc_2_000002CE
	cmpi.w #58,$0016(a7)
	bne.b loc_2_000002D6
loc_2_000002CE:
	movea.l a3,a1
	addq.l #1,a3
	move.b (a2),$0(a1,d2.l)
loc_2_000002D6:
	movea.l a3,a1
loc_2_000002D8:
	move.l a1,d0
	movem.l (a7)+,d2-d3/a2-a3
	rts
    SECTION section_3,data
loc_3_00000000:
	dc.b $00,$00,$00,$00
loc_3_00000004:
	dc.b $00,$00
loc_3_00000006:
	dc.b $00,$00
loc_3_00000008:
	dc.b $00,$00
loc_3_0000000A:
	dc.b $00,$00
loc_3_0000000C:
	dc.b $00,$00
loc_3_0000000E:
	dc.b $00,$00
    SECTION section_4,code
loc_4_00000000:
	moveq.l #0,d0
	rts
loc_4_00000004:
	moveq.l #-1,d0
	rts
    SECTION section_5,data
loc_5_00000000:
	dc.l loc_5_00000180	; pointer_table
	dc.l loc_5_00000182
	dc.l loc_5_00000184
	dc.l loc_5_00000186
	dc.l loc_5_00000188
	dc.l loc_5_0000018A
	dc.l loc_5_0000018C
	dc.l loc_5_0000018E
	dc.l loc_5_00000190
	dc.l loc_5_00000192
	dc.l loc_5_00000194
	dc.l loc_5_00000196
	dc.l loc_5_00000198
	dc.l loc_5_0000019A
	dc.l loc_5_0000019C
	dc.l loc_5_0000019E
	dc.l loc_5_000001A0
	dc.l loc_5_000001A2
	dc.l loc_5_000001A4
	dc.l loc_5_000001A6
	dc.l loc_5_000001A8
	dc.l loc_5_000001AA
	dc.l loc_5_000001AC
	dc.l loc_5_000001AE
	dc.l loc_5_000001B0
	dc.l loc_5_000001B2
	dc.l loc_5_000001B4
	dc.l loc_5_000001B6
	dc.l loc_5_000001B8
	dc.l loc_5_000001BA
	dc.l loc_5_000001BC
	dc.l loc_5_000001BE
	dc.l loc_5_000001C0
	dc.l loc_5_000001C2
	dc.l loc_5_000001C4
	dc.l loc_5_000001C6
	dc.l loc_5_000001C8
	dc.l loc_5_000001CA
	dc.l loc_5_000001CC
	dc.l loc_5_000001CE
	dc.l loc_5_000001D0
	dc.l loc_5_000001D2
	dc.l loc_5_000001D4
	dc.l loc_5_000001D6
	dc.l loc_5_000001D8
	dc.l loc_5_000001DA
	dc.l loc_5_000001DC
	dc.l loc_5_000001DE
	dc.l loc_5_000001E0
	dc.l loc_5_000001E2
	dc.l loc_5_000001E4
	dc.l loc_5_000001E6
	dc.l loc_5_000001E8
	dc.l loc_5_000001EA
	dc.l loc_5_000001EC
	dc.l loc_5_000001EE
	dc.l loc_5_000001F0
	dc.l loc_5_000001F2
	dc.l loc_5_000001F4
	dc.l loc_5_000001F6
	dc.l loc_5_000001F8
	dc.l loc_5_000001FA
	dc.l loc_5_000001FC
	dc.l loc_5_000001FE
	dc.l loc_5_00000200
	dc.l loc_5_00000202
	dc.l loc_5_00000204
	dc.l loc_5_00000206
	dc.l loc_5_00000208
	dc.l loc_5_0000020A
	dc.l loc_5_0000020C
	dc.l loc_5_0000020E
	dc.l loc_5_00000210
	dc.l loc_5_00000212
	dc.l loc_5_00000214
	dc.l loc_5_00000216
	dc.l loc_5_00000218
	dc.l loc_5_0000021A
	dc.l loc_5_0000021C
	dc.l loc_5_0000021E
	dc.l loc_5_00000220
	dc.l loc_5_00000222
	dc.l loc_5_00000224
	dc.l loc_5_00000226
	dc.l loc_5_00000228
	dc.l loc_5_0000022A
	dc.l loc_5_0000022C
	dc.l loc_5_0000022E
	dc.l loc_5_00000230
	dc.l loc_5_00000232
	dc.l loc_5_00000234
	dc.l loc_5_00000236
	dc.l loc_5_00000238
	dc.l loc_5_0000023A
	dc.l loc_5_0000023C
	dc.l loc_5_0000023E
loc_5_00000180:
	dc.b $20,$00
loc_5_00000182:
	dc.b $21,$00
loc_5_00000184:
	dc.b $63,$00
loc_5_00000186:
	dc.b $4C,$00
loc_5_00000188:
	dc.b $6F,$00
loc_5_0000018A:
	dc.b $59,$00
loc_5_0000018C:
	dc.b $7C,$00
loc_5_0000018E:
	dc.b $53,$00
loc_5_00000190:
	dc.b $22,$00
loc_5_00000192:
	dc.b $63,$00
loc_5_00000194:
	dc.b $61,$00
loc_5_00000196:
	dc.b $60,$00
loc_5_00000198:
	dc.b $7E,$00
loc_5_0000019A:
	dc.b $2D,$00
loc_5_0000019C:
	dc.b $72,$00
loc_5_0000019E:
	dc.b $2D,$00
loc_5_000001A0:
	dc.b $2A,$00
loc_5_000001A2:
	dc.b $2B,$00
loc_5_000001A4:
	dc.b $32,$00
loc_5_000001A6:
	dc.b $33,$00
loc_5_000001A8:
	dc.b $27,$00
loc_5_000001AA:
	dc.b $75,$00
loc_5_000001AC:
	dc.b $50,$00
loc_5_000001AE:
	dc.b $2E,$00
loc_5_000001B0:
	dc.b $2C,$00
loc_5_000001B2:
	dc.b $31,$00
loc_5_000001B4:
	dc.b $6F,$00
loc_5_000001B6:
	dc.b $27,$00
loc_5_000001B8:
	dc.b $2F,$00
loc_5_000001BA:
	dc.b $2F,$00
loc_5_000001BC:
	dc.b $2F,$00
loc_5_000001BE:
	dc.b $3F,$00
loc_5_000001C0:
	dc.b $41,$00
loc_5_000001C2:
	dc.b $41,$00
loc_5_000001C4:
	dc.b $41,$00
loc_5_000001C6:
	dc.b $41,$00
loc_5_000001C8:
	dc.b $41,$00
loc_5_000001CA:
	dc.b $41,$00
loc_5_000001CC:
	dc.b $41,$00
loc_5_000001CE:
	dc.b $43,$00
loc_5_000001D0:
	dc.b $45,$00
loc_5_000001D2:
	dc.b $45,$00
loc_5_000001D4:
	dc.b $45,$00
loc_5_000001D6:
	dc.b $45,$00
loc_5_000001D8:
	dc.b $49,$00
loc_5_000001DA:
	dc.b $49,$00
loc_5_000001DC:
	dc.b $49,$00
loc_5_000001DE:
	dc.b $49,$00
loc_5_000001E0:
	dc.b $44,$00
loc_5_000001E2:
	dc.b $4E,$00
loc_5_000001E4:
	dc.b $4F,$00
loc_5_000001E6:
	dc.b $4F,$00
loc_5_000001E8:
	dc.b $4F,$00
loc_5_000001EA:
	dc.b $4F,$00
loc_5_000001EC:
	dc.b $4F,$00
loc_5_000001EE:
	dc.b $78,$00
loc_5_000001F0:
	dc.b $4F,$00
loc_5_000001F2:
	dc.b $55,$00
loc_5_000001F4:
	dc.b $55,$00
loc_5_000001F6:
	dc.b $55,$00
loc_5_000001F8:
	dc.b $55,$00
loc_5_000001FA:
	dc.b $59,$00
loc_5_000001FC:
	dc.b $54,$00
loc_5_000001FE:
	dc.b $33,$00
loc_5_00000200:
	dc.b $61,$00
loc_5_00000202:
	dc.b $61,$00
loc_5_00000204:
	dc.b $61,$00
loc_5_00000206:
	dc.b $61,$00
loc_5_00000208:
	dc.b $61,$00
loc_5_0000020A:
	dc.b $61,$00
loc_5_0000020C:
	dc.b $61,$00
loc_5_0000020E:
	dc.b $63,$00
loc_5_00000210:
	dc.b $65,$00
loc_5_00000212:
	dc.b $65,$00
loc_5_00000214:
	dc.b $65,$00
loc_5_00000216:
	dc.b $65,$00
loc_5_00000218:
	dc.b $69,$00
loc_5_0000021A:
	dc.b $69,$00
loc_5_0000021C:
	dc.b $69,$00
loc_5_0000021E:
	dc.b $69,$00
loc_5_00000220:
	dc.b $64,$00
loc_5_00000222:
	dc.b $6E,$00
loc_5_00000224:
	dc.b $6F,$00
loc_5_00000226:
	dc.b $6F,$00
loc_5_00000228:
	dc.b $6F,$00
loc_5_0000022A:
	dc.b $6F,$00
loc_5_0000022C:
	dc.b $6F,$00
loc_5_0000022E:
	dc.b $2F,$00
loc_5_00000230:
	dc.b $6F,$00
loc_5_00000232:
	dc.b $75,$00
loc_5_00000234:
	dc.b $75,$00
loc_5_00000236:
	dc.b $75,$00
loc_5_00000238:
	dc.b $75,$00
loc_5_0000023A:
	dc.b $79,$00
loc_5_0000023C:
	dc.b $74,$00
loc_5_0000023E:
	dc.b $79,$00
	dc.l loc_5_00000282	; pointer_table
	dc.l loc_4_00000000
	dc.l loc_4_00000000
	dc.l loc_4_00000000
	dc.l loc_4_00000000
	dc.b $00,$01,$50,$01
	dcb.b $12,$00
	dc.l loc_4_00000004	; pointer_table
	dc.l loc_4_00000000
	dc.b $00,$00,$00,$00
	dc.l loc_5_00000000
	dcb.b $8,$00
loc_5_00000282:
	dc.b "Generic",$00	; string
	dc.b $00,$00
    SECTION section_6,code
loc_6_00000000:
	link a6,#-248
	movem.l d2-d7/a2-a5,-(a7)
	movea.l $0008(a6),a2
	movea.l #loc_22_00000000,a4
	move.l #loc_1_00000000,d6
	move.l #loc_1_00000004,-$000C(a6)
	moveq.l #114,d5
	lea.l -$00F8(a6),a0
loc_6_00000026:
	clr.b (a0)+
	subq.w #1,d5
	bne.b loc_6_00000026
	move.l $0020(a2),d0
	move.l d0,-$001C(a6)
	move.l d0,-$00F4(a6)
	move.w $002C(a2),-$0046(a6)
	move.w $002E(a2),-$0076(a6)
	move.w $0030(a2),-$0002(a6)
	move.w $0032(a2),-$001E(a6)
	move.l $0034(a2),-$004C(a6)
	move.l $0038(a2),-$0058(a6)
	movea.l loc_1_00000004.l,a0
	move.l $002E(a0),d0
	move.l d0,-$0074(a6)
	move.l d0,-$00F8(a6)
	movea.l d6,a3
	movea.l (a3),a0
	move.w $0A92(a0),-$00AA(a6)
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	move.l d0,-$0040(a6)
	andi.l #240,-$0040(a6)
	moveq.l #0,d2
	move.w $003C(a2),d2
	move.l d2,-$0084(a6)
	pea.l -$0084(a6)
	jsr loc_6_00001316.l
	movea.l loc_1_00000004.l,a0
	btst.b #0,$0014(a0)
	addq.l #4,a7
	bne.b loc_6_000000BC
	pea.l -$00F8(a6)
	move.l a2,-(a7)
	pea.l $0002.w
	bra.w loc_6_000012DA
loc_6_000000BC:
	move.l -$0084(a6),-$0044(a6)
	moveq.l #64,d0
	move.l -$0044(a6),d3
	and.l d0,d3
	move.l d3,-$0044(a6)
	moveq.l #0,d2
	move.w -$00AA(a6),d2
	move.l d2,d0
	moveq.l #8,d1
	and.l d1,d0
	or.l d0,d3
	move.l d3,-$0044(a6)
	beq.b loc_6_000000E8
	moveq.l #-65,d0
	and.l d0,-$0084(a6)
loc_6_000000E8:
	move.l -$0084(a6),-(a7)
	pea.l $0005.w
	clr.l -(a7)
	move.l -$0084(a6),-(a7)
	move.l a2,-(a7)
	movea.l -$0074(a6),a3
	jsr (a3)
	move.l d0,d5
	lea.l $0014(a7),a7
	beq.b loc_6_0000010A
	bra.w loc_6_000012D2
loc_6_0000010A:
	move.l -$0084(a6),-$00A8(a6)
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #512,d0
	beq.b loc_6_00000126
	movea.l #loc_7_00000010,a0
	bra.b loc_6_0000012C
loc_6_00000126:
	movea.l #loc_7_00000000,a0
loc_6_0000012C:
	move.l a0,-$00C8(a6)
	movea.l loc_1_00000004.l,a0
	moveq.l #0,d1
	move.b $0015(a0),d1
	move.w d1,d4
	andi.w #7,d4
	cmpi.w #2,d4
	beq.b loc_6_00000166
	cmpi.w #3,d4
	bne.b loc_6_00000160
	cmpi.w #3,d4
	bne.b loc_6_00000166
	movea.l d6,a1
	movea.l (a1),a0
	cmpi.w #2,$0A64(a0)
	beq.b loc_6_00000166
loc_6_00000160:
	ori.w #2,-$0088(a6)
loc_6_00000166:
	movea.l d6,a1
	movea.l (a1),a0
	cmpi.w #1,$0A62(a0)
	bne.b loc_6_00000178
	ori.w #8,-$0088(a6)
loc_6_00000178:
	movea.l d6,a1
	movea.l (a1),a0
	cmpi.w #2,$0A64(a0)
	beq.b loc_6_0000018A
	ori.w #1,-$0088(a6)
loc_6_0000018A:
	movea.l d6,a1
	movea.l (a1),a0
	tst.w $0A64(a0)
	bne.b loc_6_000001A0
	movea.l d6,a1
	movea.l (a1),a0
	move.w $0A66(a0),-$008C(a6)
	bra.b loc_6_000001A4
loc_6_000001A0:
	clr.w -$008C(a6)
loc_6_000001A4:
	move.l $0028(a2),d2
	andi.l #2048,d2
	beq.b loc_6_000001B6
	ori.w #4,-$0088(a6)
loc_6_000001B6:
	move.l $0028(a2),d2
	andi.l #32768,d2
	sne.b d5
	neg.b d5
	ext.w d5
	ext.l d5
	btst.b #2,$002B(a2)
	sne.b -$0025(a6)
	neg.b -$0025(a6)
	move.l -$0028(a6),d0
	ext.w d0
	ext.l d0
	move.l d0,-$0028(a6)
	movea.l -$001C(a6),a0
	move.l (a0),-$0024(a6)
	beq.b loc_6_00000248
	movea.l -$0024(a6),a0
	tst.l $0020(a0)
	beq.b loc_6_00000212
	movea.l -$0024(a6),a1
	movea.l $0020(a1),a0
	moveq.l #0,d0
	move.w (a0),d0
	asl.l #3,d0
	move.w d0,-$004E(a6)
	movea.l -$0024(a6),a1
	movea.l $0020(a1),a0
	bra.b loc_6_00000262
loc_6_00000212:
	movea.l -$0024(a6),a0
	move.w $0014(a0),-$004E(a6)
	movea.l -$0024(a6),a0
	move.w $0010(a0),d0
	sub.w d0,-$004E(a6)
	addq.w #1,-$004E(a6)
	movea.l -$0024(a6),a0
	move.w $0016(a0),-$0048(a6)
	movea.l -$0024(a6),a0
	move.w $0012(a0),d0
	sub.w d0,-$0048(a6)
	addq.w #1,-$0048(a6)
	bra.b loc_6_00000268
loc_6_00000248:
	movea.l -$001C(a6),a1
	movea.l $0004(a1),a0
	moveq.l #0,d0
	move.w (a0),d0
	asl.l #3,d0
	move.w d0,-$004E(a6)
	movea.l -$001C(a6),a1
	movea.l $0004(a1),a0
loc_6_00000262:
	move.w $0002(a0),-$0048(a6)
loc_6_00000268:
	tst.w -$0046(a6)
	bcs.b loc_6_000002B4
	tst.w -$0076(a6)
	bcs.b loc_6_000002B4
	tst.w -$0002(a6)
	bls.b loc_6_000002B4
	tst.w -$001E(a6)
	bls.b loc_6_000002B4
	moveq.l #0,d3
	move.w -$004E(a6),d3
	move.l d3,d2
	moveq.l #0,d3
	move.w -$0002(a6),d3
	moveq.l #0,d0
	move.w -$0046(a6),d0
	add.l d0,d3
	cmp.l d3,d2
	bcs.b loc_6_000002B4
	moveq.l #0,d3
	move.w -$0048(a6),d3
	move.l d3,d2
	moveq.l #0,d3
	move.w -$001E(a6),d3
	moveq.l #0,d0
	move.w -$0076(a6),d0
	add.l d0,d3
	cmp.l d3,d2
	bcc.b loc_6_000002C2
loc_6_000002B4:
	pea.l -$00F8(a6)
	move.l a2,-(a7)
	pea.l $0004.w
	bra.w loc_6_000012DA
loc_6_000002C2:
	movea.l loc_1_00000004.l,a0
	moveq.l #0,d2
	move.w $0022(a0),d2
	move.l d2,-$006C(a6)
	movea.l loc_1_00000004.l,a0
	moveq.l #0,d2
	move.w $0024(a0),d2
	move.l d2,-$0070(a6)
	movea.l loc_1_00000004.l,a0
	move.l $001A(a0),-$007C(a6)
	tst.l -$0040(a6)
	beq.b loc_6_00000338
	movea.l d6,a1
	movea.l (a1),a0
	moveq.l #0,d2
	move.w $0A94(a0),d2
	move.l d2,d4
	btst.b #7,-$003D(a6)
	beq.b loc_6_0000031E
	move.l d4,d0
	mulu.w -$0002(a6),d4
	swap.w d0
	mulu.w -$0002(a6),d0
	swap.w d0
	clr.w d0
	add.l d0,d4
	bra.w loc_6_00000394
loc_6_0000031E:
	btst.b #6,-$003D(a6)
	bne.w loc_6_00000394
	move.l -$006C(a6),d1
	move.l d4,d0
	jsr loc_38_00000040.l
	move.l d0,d3
	bra.b loc_6_00000386
loc_6_00000338:
	movea.l d6,a3
	movea.l (a3),a0
	moveq.l #0,d2
	move.w $0A5E(a0),d2
	move.l d2,d4
	addq.l #1,d4
	movea.l (a3),a1
	moveq.l #0,d3
	move.w $0A5C(a1),d3
	sub.l d3,d4
	move.l d4,d1
	move.l -$006C(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d4
	movea.l (a3),a0
	move.w $0A56(a0),d0
	cmpi.w #1024,d0
	blt.b loc_6_00000384
	ble.b loc_6_00000374
	cmpi.w #2048,d0
	bne.b loc_6_00000384
	bra.b loc_6_0000037C
loc_6_00000374:
	move.l d4,d3
	addq.l #6,d3
	moveq.l #12,d1
	bra.b loc_6_0000038A
loc_6_0000037C:
	move.l d4,d3
	addq.l #7,d3
	moveq.l #15,d1
	bra.b loc_6_0000038A
loc_6_00000384:
	move.l d4,d3
loc_6_00000386:
	addq.l #5,d3
	moveq.l #10,d1
loc_6_0000038A:
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,d4
loc_6_00000394:
	tst.l d4
	beq.b loc_6_000003A4
	move.l -$007C(a6),d0
	cmp.l d4,d0
	bls.b loc_6_000003A4
	move.l d4,d0
	bra.b loc_6_000003A8
loc_6_000003A4:
	move.l -$007C(a6),d0
loc_6_000003A8:
	move.l d0,-$0080(a6)
	movea.l loc_1_00000004.l,a0
	move.l $001E(a0),-$0060(a6)
	tst.l -$0040(a6)
	beq.b loc_6_00000400
	movea.l d6,a1
	movea.l (a1),a0
	moveq.l #0,d2
	move.w $0A96(a0),d2
	btst.b #7,-$003D(a6)
	beq.b loc_6_000003E4
	move.l d2,d0
	mulu.w -$001E(a6),d2
	swap.w d0
	mulu.w -$001E(a6),d0
	swap.w d0
	clr.w d0
	add.l d0,d2
	bra.b loc_6_00000442
loc_6_000003E4:
	btst.b #6,-$003D(a6)
	bne.b loc_6_00000442
	move.l -$0070(a6),d1
	move.l d2,d0
	jsr loc_38_00000040.l
	move.l d0,d3
	addq.l #5,d3
	moveq.l #10,d1
	bra.b loc_6_00000438
loc_6_00000400:
	move.l -$0070(a6),d2
	movea.l d6,a1
	movea.l (a1),a0
	move.l d2,d0
	mulu.w $0A6A(a0),d2
	swap.w d0
	mulu.w $0A6A(a0),d0
	swap.w d0
	clr.w d0
	add.l d0,d2
	move.w $0A5A(a0),d0
	cmpi.w #512,d0
	bne.b loc_6_00000432
	bra.w loc_6_00000428
loc_6_00000428:
	move.l d2,d3
	addq.l #4,d3
	move.l d3,d2
	lsr.l #3,d2
	bra.b loc_6_00000442
loc_6_00000432:
	move.l d2,d3
	addq.l #3,d3
	moveq.l #6,d1
loc_6_00000438:
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,d2
loc_6_00000442:
	tst.l d2
	beq.b loc_6_0000044E
	move.l -$0060(a6),d0
	cmp.l d2,d0
	bhi.b loc_6_00000454
loc_6_0000044E:
	tst.l -$0060(a6)
	bne.b loc_6_00000458
loc_6_00000454:
	move.l d2,d0
	bra.b loc_6_0000045C
loc_6_00000458:
	move.l -$0060(a6),d0
loc_6_0000045C:
	move.l d0,-$0054(a6)
	bne.b loc_6_0000046A
	move.l #$AFC80,-$0054(a6)
loc_6_0000046A:
	move.l -$0040(a6),d0
	andi.l #224,d0
	beq.b loc_6_00000486
	andi.l #4294967104,-$0084(a6)
	move.l d4,-$004C(a6)
	move.l d2,-$0058(a6)
loc_6_00000486:
	tst.l -$004C(a6)
	beq.b loc_6_0000049C
	tst.l -$0058(a6)
	beq.b loc_6_0000049C
	btst.b #7,-$0081(a6)
	beq.w loc_6_00000548
loc_6_0000049C:
	moveq.l #1,d0
	move.l d0,-$0068(a6)
	movea.l d6,a1
	movea.l (a1),a0
	btst.b #7,$0A71(a0)
	beq.b loc_6_000004BE
	moveq.l #15,d0
	move.l d0,-$0038(a6)
	moveq.l #16,d0
	move.l d0,-$003C(a6)
	bra.w loc_6_0000054C
loc_6_000004BE:
	movea.l loc_1_00000014.l,a0
	cmpi.w #33,$0014(a0)
	bcs.b loc_6_00000520
	movea.l loc_1_00000014.l,a3
	moveq.l #0,d0
	move.w $00DE(a3),d0
	muls.w #$A,d0
	move.l #$B6,d1
	jsr loc_38_0000009E.l
	move.l d0,-(a7)
	jsr loc_6_000012EA.l
	move.l d0,-$0038(a6)
	movea.l loc_1_00000014.l,a3
	moveq.l #0,d0
	move.w $00DC(a3),d0
	muls.w #$A,d0
	move.l #$B6,d1
	jsr loc_38_0000009E.l
	move.l d0,-(a7)
	jsr loc_6_000012EA.l
	move.l d0,-$003C(a6)
	addq.l #8,a7
	bra.b loc_6_0000052C
loc_6_00000520:
	moveq.l #6,d0
	move.l d0,-$0038(a6)
	moveq.l #7,d0
	move.l d0,-$003C(a6)
loc_6_0000052C:
	tst.l d5
	bne.b loc_6_00000538
	move.l -$0038(a6),d0
	add.l d0,-$0038(a6)
loc_6_00000538:
	tst.l -$0028(a6)
	bne.b loc_6_0000054C
	move.l -$003C(a6),d0
	add.l d0,-$003C(a6)
	bra.b loc_6_0000054C
loc_6_00000548:
	clr.l -$0068(a6)
loc_6_0000054C:
	btst.b #3,-$0087(a6)
	beq.b loc_6_000005BE
	move.w -$0076(a6),d4
	move.w -$0046(a6),-$0076(a6)
	move.w -$001E(a6),-$0046(a6)
	add.w d4,-$0046(a6)
	subq.w #1,-$0046(a6)
	move.l -$004C(a6),d0
	move.l -$0058(a6),-$004C(a6)
	move.l d0,-$0058(a6)
	move.l -$0038(a6),d0
	move.l -$003C(a6),-$0038(a6)
	move.l d0,-$003C(a6)
	move.w -$0002(a6),d4
	move.w -$001E(a6),-$0002(a6)
	move.w d4,-$001E(a6)
	move.l -$0084(a6),d3
	moveq.l #63,d0
	and.l d0,d3
	movea.l -$0084(a6),a3
	moveq.l #-64,d0
	move.l a3,d1
	and.l d0,d1
	move.l d3,d2
	lsl.l #1,d2
	moveq.l #42,d0
	and.l d0,d2
	lsr.l #1,d3
	moveq.l #21,d0
	and.l d0,d3
	or.l d1,d3
	or.l d3,d2
	move.l d2,-$0084(a6)
loc_6_000005BE:
	tst.l -$0084(a6)
	bne.b loc_6_00000600
	tst.l -$004C(a6)
	blt.b loc_6_000005D0
	tst.l -$0058(a6)
	bge.b loc_6_00000600
loc_6_000005D0:
	move.l -$004C(a6),d1
	moveq.l #0,d3
	move.w -$0002(a6),d3
	move.l d3,d0
	jsr loc_38_00000040.l
	move.l -$0058(a6),d1
	jsr loc_38_0000009E.l
	move.l d0,-$004C(a6)
	bge.b loc_6_000005FC
	move.l -$004C(a6),d0
	neg.l d0
	move.l d0,-$004C(a6)
loc_6_000005FC:
	clr.l -$0058(a6)
loc_6_00000600:
	move.l -$004C(a6),-$0010(a6)
	move.l -$0058(a6),-$0008(a6)
	btst.b #0,-$0081(a6)
	beq.b loc_6_0000063C
	move.l -$006C(a6),d1
	move.l -$0010(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d3
	addi.l #500,d3
	move.l #$3E8,d1
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,-$0010(a6)
loc_6_0000063C:
	btst.b #1,-$0081(a6)
	beq.b loc_6_0000066C
	move.l -$0070(a6),d1
	move.l -$0008(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d3
	addi.l #500,d3
	move.l #$3E8,d1
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,-$0008(a6)
loc_6_0000066C:
	tst.l -$0010(a6)
	beq.b loc_6_0000067A
	btst.b #2,-$0081(a6)
	beq.b loc_6_00000682
loc_6_0000067A:
	move.l -$0080(a6),-$0010(a6)
	bra.b loc_6_000006B6
loc_6_00000682:
	btst.b #4,-$0081(a6)
	beq.b loc_6_000006B6
	move.l -$0010(a6),d2
	moveq.l #15,d1
	lsr.l d1,d2
	move.l d2,-$0010(a6)
	addq.l #1,-$0010(a6)
	move.l -$0010(a6),d2
	lsr.l #1,d2
	move.l d2,d1
	move.l -$0080(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d2
	moveq.l #16,d1
	lsr.l d1,d2
	move.l d2,-$0010(a6)
loc_6_000006B6:
	tst.l -$0008(a6)
	beq.b loc_6_000006C4
	btst.b #3,-$0081(a6)
	beq.b loc_6_000006CE
loc_6_000006C4:
	move.l -$0054(a6),-$0008(a6)
	bra.w loc_6_0000074E
loc_6_000006CE:
	btst.b #5,-$0081(a6)
	beq.w loc_6_0000074E
	move.l -$0008(a6),d2
	moveq.l #15,d1
	lsr.l d1,d2
	move.l d2,-$0008(a6)
	addq.l #1,-$0008(a6)
	move.l -$0008(a6),d2
	lsr.l #1,d2
	move.l d2,-$0008(a6)
	clr.w d5
	moveq.l #1,d4
	clr.w -$0086(a6)
loc_6_000006FA:
	moveq.l #0,d0
	move.w -$0086(a6),d0
	add.l -$0054(a6),d0
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,d1
	jsr loc_38_0000006C.l
	move.l d0,d3
	move.l d3,d1
	move.l -$0008(a6),d0
	jsr loc_38_00000040.l
	movea.l d0,a3
	addq.w #1,d5
	add.w d4,d4
	moveq.l #0,d0
	move.w d4,d0
	lsr.l #1,d0
	move.w d0,-$0086(a6)
	move.l -$0008(a6),d1
	move.l a3,d0
	jsr loc_38_0000006C.l
	cmp.l d0,d3
	bne.b loc_6_000006FA
	move.l a3,-$0008(a6)
	moveq.l #16,d0
	move.l -$0008(a6),d1
	lsr.l d0,d1
	move.l d1,-$0008(a6)
loc_6_0000074E:
	tst.l -$0068(a6)
	beq.w loc_6_00000862
	clr.w d5
	moveq.l #1,d4
	clr.w -$0086(a6)
loc_6_0000075E:
	move.l -$0038(a6),d2
	move.l d2,d0
	mulu.w -$0002(a6),d2
	swap.w d0
	mulu.w -$0002(a6),d0
	swap.w d0
	clr.w d0
	add.l d0,d2
	move.l d2,d1
	move.l -$006C(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d2
	moveq.l #0,d3
	move.w -$0086(a6),d3
	add.l d3,d2
	moveq.l #0,d0
	move.w d4,d0
	move.l d0,d1
	move.l d2,d0
	jsr loc_38_0000006C.l
	move.l d0,-$002C(a6)
	move.l -$003C(a6),d2
	move.l d2,d0
	mulu.w -$001E(a6),d2
	swap.w d0
	mulu.w -$001E(a6),d0
	swap.w d0
	clr.w d0
	add.l d0,d2
	move.l d2,d1
	move.l -$0070(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d2
	moveq.l #0,d3
	move.w -$0086(a6),d3
	add.l d3,d2
	moveq.l #0,d0
	move.w d4,d0
	move.l d0,d1
	move.l d2,d0
	jsr loc_38_0000006C.l
	move.l d0,-$0030(a6)
	move.l -$002C(a6),d1
	move.l -$0008(a6),d0
	jsr loc_38_00000040.l
	move.l d0,d3
	move.l -$0030(a6),d1
	move.l -$0010(a6),d0
	jsr loc_38_00000040.l
	movea.l d0,a3
	addq.w #1,d5
	add.w d4,d4
	moveq.l #0,d0
	move.w d4,d0
	lsr.l #1,d0
	move.w d0,-$0086(a6)
	move.l -$0008(a6),d1
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,d2
	move.l -$002C(a6),d7
	cmp.l d2,d7
	bne.w loc_6_0000075E
	move.l -$0010(a6),d1
	move.l a3,d0
	jsr loc_38_0000006C.l
	move.l d0,d2
	move.l -$0030(a6),d7
	cmp.l d2,d7
	bne.w loc_6_0000075E
	cmp.l a3,d3
	bls.b loc_6_0000084E
	move.l -$002C(a6),d1
	move.l a3,d0
	jsr loc_38_0000006C.l
	move.l d0,-$0008(a6)
	bra.b loc_6_00000862
loc_6_0000084E:
	cmp.l a3,d3
	bcc.b loc_6_00000862
	move.l -$0030(a6),d1
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,-$0010(a6)
loc_6_00000862:
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #256,d0
	beq.w loc_6_0000092E
	moveq.l #0,d3
	move.w -$0002(a6),d3
	move.l d3,d2
	cmp.l -$0010(a6),d2
	bls.b loc_6_0000088C
	moveq.l #0,d2
	move.w -$0002(a6),d2
	move.l d2,-$0010(a6)
	bra.b loc_6_000008D0
loc_6_0000088C:
	moveq.l #0,d2
	move.w -$0002(a6),d2
	move.l d2,d1
	move.l -$0010(a6),d0
	jsr loc_38_00000060.l
	move.w d0,d4
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,d2
	moveq.l #0,d3
	move.w -$0002(a6),d3
	lsr.l #1,d3
	cmp.l d3,d2
	bcc.b loc_6_000008BE
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,d2
	sub.l d2,-$0010(a6)
	bra.b loc_6_000008D0
loc_6_000008BE:
	moveq.l #0,d3
	move.w -$0002(a6),d3
	move.l d3,d2
	moveq.l #0,d3
	move.w d4,d3
	sub.l d3,d2
	add.l d2,-$0010(a6)
loc_6_000008D0:
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d2
	cmp.l -$0008(a6),d2
	bls.b loc_6_000008EA
	moveq.l #0,d2
	move.w -$001E(a6),d2
	move.l d2,-$0008(a6)
	bra.b loc_6_0000092E
loc_6_000008EA:
	moveq.l #0,d2
	move.w -$001E(a6),d2
	move.l d2,d1
	move.l -$0008(a6),d0
	jsr loc_38_00000060.l
	move.w d0,d4
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,d2
	moveq.l #0,d3
	move.w -$001E(a6),d3
	lsr.l #1,d3
	cmp.l d3,d2
	bcc.b loc_6_0000091C
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,d2
	sub.l d2,-$0008(a6)
	bra.b loc_6_0000092E
loc_6_0000091C:
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d2
	moveq.l #0,d3
	move.w d4,d3
	sub.l d3,d2
	add.l d2,-$0008(a6)
loc_6_0000092E:
	tst.l -$007C(a6)
	beq.b loc_6_00000944
	move.l -$007C(a6),d0
	cmp.l -$0010(a6),d0
	bcc.b loc_6_00000944
	move.l -$007C(a6),-$0010(a6)
loc_6_00000944:
	tst.l -$0060(a6)
	beq.b loc_6_0000095A
	move.l -$0060(a6),d0
	cmp.l -$0008(a6),d0
	bcc.b loc_6_0000095A
	move.l -$0060(a6),-$0008(a6)
loc_6_0000095A:
	tst.l -$0044(a6)
	beq.b loc_6_0000097A
	movea.l loc_1_00000004.l,a0
	move.l $001A(a0),d3
	sub.l -$0010(a6),d3
	addq.l #1,d3
	move.l d3,d2
	lsr.l #1,d2
	move.w d2,-$008E(a6)
	bra.b loc_6_000009D4
loc_6_0000097A:
	movea.l d6,a1
	movea.l (a1),a0
	moveq.l #0,d2
	move.b $0A99(a0),d2
	move.l d2,d0
	beq.b loc_6_000009D4
	move.l d0,d3
	movea.l loc_1_00000004.l,a0
	move.l d3,d2
	mulu.w $0022(a0),d3
	swap.w d2
	mulu.w $0022(a0),d2
	swap.w d2
	clr.w d2
	add.l d2,d3
	addq.l #5,d3
	moveq.l #10,d1
	move.l d3,d0
	jsr loc_38_0000006C.l
	movea.l loc_1_00000004.l,a0
	move.l $001A(a0),d2
	move.l -$0010(a6),d3
	add.l d0,d3
	cmp.l d3,d2
	bcc.b loc_6_000009D0
	movea.l loc_1_00000004.l,a0
	move.l $001A(a0),d0
	sub.l -$0010(a6),d0
loc_6_000009D0:
	move.w d0,-$008E(a6)
loc_6_000009D4:
	move.l -$0084(a6),d2
	andi.l #8192,d2
	beq.b loc_6_00000A02
	moveq.l #0,d3
	move.w -$008E(a6),d3
	move.l d3,d2
	add.l -$0010(a6),d2
	move.l d2,$0034(a2)
	move.l -$0008(a6),$0038(a2)
	pea.l -$00F8(a6)
	move.l a2,-(a7)
	clr.l -(a7)
	bra.w loc_6_000012DA
loc_6_00000A02:
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d2
	cmp.l -$0008(a6),d2
	shi.b -$0015(a6)
	neg.b -$0015(a6)
	move.l -$0018(a6),d0
	ext.w d0
	ext.l d0
	movem.l d0,-$0018(a6)
	beq.b loc_6_00000A5E
	move.l -$0008(a6),d1
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d0
	jsr loc_38_0000006C.l
	move.l d0,d2
	move.w d2,-$0094(a6)
	move.l -$0008(a6),d1
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d0
	jsr loc_38_00000060.l
	move.l d0,d2
	move.w d2,-$0092(a6)
	move.w -$0006(a6),-$0090(a6)
	bra.b loc_6_00000A94
loc_6_00000A5E:
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d1
	move.l -$0008(a6),d0
	jsr loc_38_0000006C.l
	move.l d0,d2
	move.w d2,-$0094(a6)
	moveq.l #0,d3
	move.w -$001E(a6),d3
	move.l d3,d1
	move.l -$0008(a6),d0
	jsr loc_38_00000060.l
	move.l d0,d2
	move.w d2,-$0092(a6)
	move.w -$001E(a6),-$0090(a6)
loc_6_00000A94:
	moveq.l #0,d3
	move.w -$0002(a6),d3
	move.l d3,d2
	cmp.l -$0010(a6),d2
	shi.b -$0011(a6)
	neg.b -$0011(a6)
	move.l -$0014(a6),d0
	ext.w d0
	ext.l d0
	movem.l d0,-$0014(a6)
	beq.b loc_6_00000AEC
	move.l -$0010(a6),d1
	moveq.l #0,d2
	move.w -$0002(a6),d2
	move.l d2,d0
	jsr loc_38_0000006C.l
	move.w d0,-$0062(a6)
	move.l -$0010(a6),d1
	moveq.l #0,d2
	move.w -$0002(a6),d2
	move.l d2,d0
	jsr loc_38_00000060.l
	move.w d0,-$005A(a6)
	move.w -$000E(a6),-$0078(a6)
	bra.b loc_6_00000B14
loc_6_00000AEC:
	move.l -$0010(a6),d0
	divu.w -$0002(a6),d0
	move.w d0,-$0062(a6)
	moveq.l #0,d2
	move.w -$0002(a6),d2
	move.l d2,d1
	move.l -$0010(a6),d0
	jsr loc_38_00000060.l
	move.w d0,-$005A(a6)
	move.w -$0002(a6),-$0078(a6)
loc_6_00000B14:
	movea.l -$001C(a6),a1
	movea.l $0004(a1),a0
	moveq.l #0,d1
	move.b $0005(a0),d1
	move.w d1,-$0032(a6)
	cmpi.w #8,-$0032(a6)
	bls.b loc_6_00000B34
	ori.w #16,-$0088(a6)
loc_6_00000B34:
	clr.w d5
	bra.b loc_6_00000B64
loc_6_00000B38:
	movea.l -$001C(a6),a5
	movea.l $0004(a5),a3
	move.w d5,d0
	asl.w #2,d0
	move.l $8(a3,d0.w),-(a7)
	jsr loc_41_00000044.l
	move.l d0,d3
	moveq.l #2,d0
	and.l d0,d3
	cmp.l d3,d0
	addq.l #4,a7
	beq.b loc_6_00000B62
	ori.w #16,-$0088(a6)
	bra.b loc_6_00000B6A
loc_6_00000B62:
	addq.w #1,d5
loc_6_00000B64:
	cmp.w -$0032(a6),d5
	bcs.b loc_6_00000B38
loc_6_00000B6A:
	btst.b #4,-$0087(a6)
	beq.b loc_6_00000B96
	tst.l -$0024(a6)
	beq.b loc_6_00000B96
	movea.l -$0024(a6),a1
	movea.l $0008(a1),a0
	bra.b loc_6_00000B92
loc_6_00000B82:
	tst.l $0008(a0)
	beq.b loc_6_00000B90
	ori.w #64,-$0088(a6)
	bra.b loc_6_00000B96
loc_6_00000B90:
	movea.l (a0),a0
loc_6_00000B92:
	move.l a0,d0
	bne.b loc_6_00000B82
loc_6_00000B96:
	btst.b #6,-$0087(a6)
	bne.w loc_6_00000CE8
	pea.l $0001.w
	pea.l $0064.w
	jsr loc_41_00000000.l
	move.l d0,-$00F0(a6)
	addq.l #8,a7
	bne.b loc_6_00000BBA
	bra.w loc_6_000010F2
loc_6_00000BBA:
	movea.l -$00F0(a6),a0
	movea.l -$001C(a6),a1
	movea.l a0,a3
	moveq.l #24,d0
loc_6_00000BC6:
	move.l (a1)+,(a3)+
	dbf.w d0,loc_6_00000BC6
	movea.l -$00F0(a6),a0
	move.b #$FF,$0018(a0)
	movea.l -$00F0(a6),a0
	clr.l $0004(a0)
	movea.l -$00F0(a6),a0
	clr.l (a0)
	moveq.l #0,d0
	move.w -$0032(a6),d0
	asl.l #2,d0
	move.w d0,d4
	addi.w #40,d4
	movea.l -$00F0(a6),a3
	pea.l $0001.w
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,$0004(a3)
	addq.l #8,a7
	bne.b loc_6_00000C12
	bra.w loc_6_000010F2
loc_6_00000C12:
	movea.l -$00F0(a6),a0
	movea.l $0004(a0),a1
	movea.l -$001C(a6),a5
	movea.l $0004(a5),a0
	moveq.l #9,d0
loc_6_00000C24:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_6_00000C24
	movea.l -$00F0(a6),a0
	movea.l $0004(a0),a1
	clr.l $0008(a1)
	movea.l -$00F0(a6),a0
	movea.l $0004(a0),a1
	move.w #$1,$0002(a1)
	move.w -$004E(a6),d1
	cmp.w -$0048(a6),d1
	bls.b loc_6_00000C56
	moveq.l #0,d2
	move.w -$004E(a6),d2
	bra.b loc_6_00000C5C
loc_6_00000C56:
	moveq.l #0,d2
	move.w -$0048(a6),d2
loc_6_00000C5C:
	move.w d2,d4
	moveq.l #0,d2
	move.w d4,d2
	move.l d2,d0
	moveq.l #15,d1
	add.l d1,d0
	moveq.l #16,d1
	jsr loc_38_0000009E.l
	add.l d0,d0
	move.w d0,d4
	movea.l -$00F0(a6),a0
	movea.l $0004(a0),a1
	move.w d4,(a1)
	moveq.l #0,d3
	move.w -$0032(a6),d3
	mulu.w d4,d3
	move.l d3,d2
	move.w d2,-$0086(a6)
	movea.l -$00F0(a6),a3
	movea.l $0004(a3),a3
	pea.l $0002.w
	moveq.l #0,d3
	move.w -$0086(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,$0008(a3)
	addq.l #8,a7
	bne.b loc_6_00000CB2
	bra.w loc_6_000010F2
loc_6_00000CB2:
	moveq.l #1,d5
	bra.b loc_6_00000CE2
loc_6_00000CB6:
	movea.l -$00F0(a6),a0
	movea.l $0004(a0),a1
	move.w d5,d1
	asl.w #2,d1
	lea.l $0008(a1),a3
	movea.l $0004(a0),a0
	moveq.l #0,d2
	move.w d5,d2
	subq.l #1,d2
	asl.l #2,d2
	move.l $8(a0,d2.l),d0
	moveq.l #0,d2
	move.w d4,d2
	add.l d2,d0
	move.l d0,$0(a3,d1.w)
	addq.w #1,d5
loc_6_00000CE2:
	cmp.w -$0032(a6),d5
	bcs.b loc_6_00000CB6
loc_6_00000CE8:
	moveq.l #1,d0
	movea.l -$001C(a6),a1
	movea.l $0004(a1),a0
	move.b $0005(a0),d1
	asl.l d1,d0
	move.w d0,d4
	btst.b #7,$002B(a2)
	beq.b loc_6_00000D08
	move.w d4,d1
	lsr.w #1,d1
	move.w d1,d4
loc_6_00000D08:
	moveq.l #0,d0
	move.w d4,d0
	asl.l #2,d0
	move.w d0,-$0086(a6)
	btst.b #7,$002B(a2)
	beq.b loc_6_00000D2A
	moveq.l #64,d0
	moveq.l #0,d2
	move.w d4,d2
	sub.l d2,d0
	asl.l #2,d0
	move.w d0,d1
	add.w d1,-$0086(a6)
loc_6_00000D2A:
	move.w -$0086(a6),-$00B8(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$0086(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	movea.l d0,a3
	move.l a3,d2
	addq.l #8,a7
	bne.b loc_6_00000D4E
	bra.w loc_6_000010F2
loc_6_00000D4E:
	move.l a3,-$00E4(a6)
	clr.w d5
	bra.b loc_6_00000DBC
loc_6_00000D56:
	moveq.l #0,d3
	move.w d5,d3
	move.l d3,-(a7)
	move.l $0024(a2),-(a7)
	jsr loc_42_0000001C.l
	move.w d0,-$0086(a6)
	moveq.l #0,d0
	move.w -$0086(a6),d0
	moveq.l #15,d2
	and.l d2,d0
	move.b d0,(a3)
	moveq.l #0,d0
	move.w -$0086(a6),d0
	lsr.l #4,d0
	moveq.l #0,d2
	move.w d0,d2
	move.l d2,d0
	moveq.l #15,d1
	and.l d1,d0
	move.b d0,$0001(a3)
	moveq.l #0,d0
	move.w -$0086(a6),d0
	lsr.l #8,d0
	moveq.l #0,d2
	move.w d0,d2
	move.l d2,d0
	and.l d1,d0
	move.b d0,$0002(a3)
	btst.b #7,$002B(a2)
	addq.l #8,a7
	beq.b loc_6_00000DB8
	move.l (a3),d2
	lsr.l #1,d2
	andi.l #2139062143,d2
	move.l d2,$0080(a3)
loc_6_00000DB8:
	addq.l #4,a3
	addq.w #1,d5
loc_6_00000DBC:
	cmp.w d4,d5
	bcs.b loc_6_00000D56
	movea.l loc_1_00000004.l,a0
	btst.b #3,$0015(a0)
	beq.b loc_6_00000DD2
	moveq.l #0,d0
	bra.b loc_6_00000DD8
loc_6_00000DD2:
	move.l #$F0F0F0F,d0
loc_6_00000DD8:
	movea.l d6,a1
	movea.l (a1),a0
	cmpi.w #1,$0A60(a0)
	bne.b loc_6_00000DEC
	move.l #$F0F0F0F,d2
	bra.b loc_6_00000DEE
loc_6_00000DEC:
	moveq.l #0,d2
loc_6_00000DEE:
	eor.l d2,d0
	movea.l -$00E4(a6),a3
	clr.w d5
	bra.b loc_6_00000E0E
loc_6_00000DF8:
	move.l d0,d2
	eor.l d2,(a3)
	btst.b #7,$002B(a2)
	beq.b loc_6_00000E0A
	move.l d0,d2
	eor.l d2,$0080(a3)
loc_6_00000E0A:
	addq.l #4,a3
	addq.w #1,d5
loc_6_00000E0E:
	cmp.w d4,d5
	bcs.b loc_6_00000DF8
	movea.l -$00E4(a6),a3
	clr.w d5
	bra.b loc_6_00000E52
loc_6_00000E1A:
	moveq.l #0,d3
	move.w -$0088(a6),d3
	move.l d3,-(a7)
	move.l a3,-(a7)
	jsr loc_20_000007F2.l
	btst.b #7,$002B(a2)
	addq.l #8,a7
	beq.b loc_6_00000E4E
	moveq.l #0,d3
	move.w -$0088(a6),d3
	move.l d3,-(a7)
	move.l a3,d0
	addi.l #128,d0
	move.l d0,-(a7)
	jsr loc_20_000007F2.l
	addq.l #8,a7
loc_6_00000E4E:
	addq.l #4,a3
	addq.w #1,d5
loc_6_00000E52:
	cmp.w d4,d5
	bcs.b loc_6_00000E1A
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	moveq.l #7,d2
	and.l d2,d0
	beq.b loc_6_00000E82
	btst.b #2,-$0087(a6)
	bne.b loc_6_00000E82
	movea.l d6,a1
	movea.l (a1),a0
	cmpi.w #2,$0A64(a0)
	bne.b loc_6_00000E82
	pea.l -$00F8(a6)
	jsr loc_24_00000000.l
	addq.l #4,a7
loc_6_00000E82:
	move.w -$0046(a6),-$00A4(a6)
	move.w -$0076(a6),-$00A2(a6)
	move.w -$0002(a6),d1
	move.w d1,-$008A(a6)
	move.w d1,-$00A0(a6)
	move.w -$001E(a6),-$009E(a6)
	move.w -$0002(a6),d4
	addi.w #15,d4
	andi.w #65520,d4
	moveq.l #0,d0
	move.w d4,d0
	add.l d0,d0
	move.w d0,-$00BC(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00BC(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00EC(a6)
	addq.l #8,a7
	bne.b loc_6_00000ED4
	bra.w loc_6_000010F2
loc_6_00000ED4:
	moveq.l #0,d3
	move.w -$008E(a6),d3
	move.l d3,d2
	add.l -$0010(a6),d2
	move.l d2,-$009C(a6)
	move.l -$0008(a6),-$0098(a6)
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #2048,d0
	beq.b loc_6_00000F34
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00BC(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00C4(a6)
	addq.l #8,a7
	bne.b loc_6_00000F16
	bra.w loc_6_000010F2
loc_6_00000F16:
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00BC(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00C0(a6)
	addq.l #8,a7
	bne.b loc_6_00000F34
	bra.w loc_6_000010F2
loc_6_00000F34:
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #3072,d0
	beq.b loc_6_00000F6E
	move.l -$009C(a6),d2
	addq.l #1,d2
	asl.l #2,d2
	move.w d2,-$00B2(a6)
	move.l #$10001,-(a7)
	moveq.l #0,d3
	move.w -$00B2(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00D8(a6)
	addq.l #8,a7
	bne.b loc_6_00000F6E
	bra.w loc_6_000010F2
loc_6_00000F6E:
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #1024,d0
	beq.b loc_6_00000FA8
	move.l -$009C(a6),d2
	addq.l #1,d2
	asl.l #2,d2
	move.w d2,-$00B0(a6)
	move.l #$10001,-(a7)
	moveq.l #0,d3
	move.w -$00B0(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00D4(a6)
	addq.l #8,a7
	bne.b loc_6_00000FA8
	bra.w loc_6_000010F2
loc_6_00000FA8:
	moveq.l #0,d0
	move.w -$0002(a6),d0
	asl.l #2,d0
	move.w d0,-$00B6(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00B6(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00E0(a6)
	addq.l #8,a7
	bne.b loc_6_00000FD2
	bra.w loc_6_000010F2
loc_6_00000FD2:
	btst.b #2,-$0087(a6)
	beq.w loc_6_00001050
	btst.b #3,-$0087(a6)
	bne.b loc_6_00001014
	moveq.l #0,d0
	move.w -$001E(a6),d0
	asl.l #2,d0
	move.w d0,-$00B4(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00B4(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00DC(a6)
	addq.l #8,a7
	bne.b loc_6_0000100E
	bra.w loc_6_000010F2
loc_6_0000100E:
	move.w -$0046(a6),d4
	bra.b loc_6_00001018
loc_6_00001014:
	move.w -$0076(a6),d4
loc_6_00001018:
	tst.w d4
	beq.b loc_6_00001044
	moveq.l #0,d0
	move.w d4,d0
	add.l d0,d0
	move.w d0,-$00BA(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00BA(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00E8(a6)
	addq.l #8,a7
	bne.b loc_6_00001044
	bra.w loc_6_000010F2
loc_6_00001044:
	pea.l -$00F8(a6)
	jsr loc_20_00000000.l
	addq.l #4,a7
loc_6_00001050:
	moveq.l #0,d0
	move.w -$0002(a6),d0
	add.l d0,d0
	move.w d0,-$00AE(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00AE(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00D0(a6)
	addq.l #8,a7
	bne.b loc_6_0000107A
	bra.w loc_6_000010F2
loc_6_0000107A:
	movea.l -$00D0(a6),a3
	move.w -$0002(a6),d4
	move.w -$0078(a6),-$0086(a6)
loc_6_00001088:
	move.l a3,d2
	addq.l #2,a3
	pea.l -$0086(a6)
	move.w -$0078(a6),d0
	ext.l d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$005A(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0062(a6),d0
	move.l d0,-(a7)
	jsr loc_29_00000000.l
	movea.l d2,a5
	move.w d0,(a5)
	subq.w #1,d4
	lea.l $0010(a7),a7
	bne.b loc_6_00001088
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #3072,d0
	bne.b loc_6_000010CE
	tst.l -$0014(a6)
	beq.b loc_6_00001110
loc_6_000010CE:
	move.l -$009C(a6),d2
	add.l d2,d2
	move.w d2,-$00AC(a6)
	pea.l $0001.w
	moveq.l #0,d3
	move.w -$00AC(a6),d3
	move.l d3,-(a7)
	jsr loc_41_00000000.l
	move.l d0,-$00CC(a6)
	addq.l #8,a7
	bne.b loc_6_00001100
loc_6_000010F2:
	pea.l -$00F8(a6)
	move.l a2,-(a7)
	pea.l $0006.w
	bra.w loc_6_000012DA
loc_6_00001100:
	movea.l -$00CC(a6),a3
	move.w -$009A(a6),d4
loc_6_00001108:
	move.w #$1,(a3)+
	subq.w #1,d4
	bne.b loc_6_00001108
loc_6_00001110:
	moveq.l #0,d2
	move.w -$008E(a6),d2
	add.l -$0010(a6),d2
	move.l d2,-(a7)
	clr.l -(a7)
	move.l -$0008(a6),-(a7)
	moveq.l #0,d0
	move.w -$008E(a6),d0
	add.l -$0010(a6),d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	movea.l -$0074(a6),a3
	jsr (a3)
	move.l d0,d5
	ori.w #32,-$0088(a6)
	tst.l d5
	lea.l $0014(a7),a7
	beq.b loc_6_0000114A
	bra.w loc_6_000012D2
loc_6_0000114A:
	pea.l $0003.w
	clr.l -(a7)
	clr.l -(a7)
	clr.l -(a7)
	movea.l -$0074(a6),a3
	jsr (a3)
	clr.w d4
	moveq.l #0,d0
	move.w d4,d0
	addq.l #1,d0
	move.w d0,-$0086(a6)
	movea.l loc_1_00000004.l,a0
	btst.b #4,$0015(a0)
	lea.l $0010(a7),a7
	beq.b loc_6_000011BC
	movea.l d6,a1
	movea.l (a1),a0
	cmpi.w #2,$0A64(a0)
	bne.b loc_6_000011B0
	movea.l loc_1_00000004.l,a0
	cmpi.b #4,$0015(a0)
	beq.b loc_6_000011A0
	movea.l loc_1_00000004.l,a0
	cmpi.b #12,$0015(a0)
	bne.b loc_6_000011A8
loc_6_000011A0:
	moveq.l #0,d0
	move.w d4,d0
	addq.l #4,d0
	bra.b loc_6_000011B8
loc_6_000011A8:
	moveq.l #0,d0
	move.w d4,d0
	addq.l #3,d0
	bra.b loc_6_000011B8
loc_6_000011B0:
	moveq.l #3,d4
	moveq.l #0,d0
	move.w d4,d0
	addq.l #1,d0
loc_6_000011B8:
	move.w d0,-$0086(a6)
loc_6_000011BC:
	moveq.l #0,d3
	move.w -$0048(a6),d3
	move.l d3,d2
	moveq.l #0,d3
	move.w -$009E(a6),d3
	moveq.l #0,d0
	move.w -$00A2(a6),d0
	add.l d0,d3
	cmp.l d3,d2
	bls.b loc_6_000011DC
	ori.w #128,-$0088(a6)
loc_6_000011DC:
	bra.w loc_6_000012CA
loc_6_000011E0:
	moveq.l #0,d0
	move.w -$00AA(a6),d0
	andi.l #2048,d0
	beq.b loc_6_0000123A
	tst.w -$00A2(a6)
	beq.b loc_6_00001212
	move.l -$00EC(a6),-(a7)
	pea.l -$00F8(a6)
	moveq.l #0,d2
	move.w -$00A2(a6),d2
	subq.l #1,d2
	move.l d2,-(a7)
	jsr loc_30_00000000.l
	lea.l $000C(a7),a7
	bra.b loc_6_00001220
loc_6_00001212:
	movea.l -$00EC(a6),a3
loc_6_00001216:
	move.w #$FFFF,(a3)+
	subq.w #1,-$0002(a6)
	bne.b loc_6_00001216
loc_6_00001220:
	move.l -$00C0(a6),-(a7)
	pea.l -$00F8(a6)
	moveq.l #0,d3
	move.w -$00A2(a6),d3
	move.l d3,-(a7)
	jsr loc_30_00000000.l
	lea.l $000C(a7),a7
loc_6_0000123A:
	tst.l -$0018(a6)
	beq.b loc_6_00001258
	tst.l -$0014(a6)
	beq.b loc_6_00001258
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,-(a7)
	pea.l -$00F8(a6)
	jsr loc_18_00000000.l
	bra.b loc_6_00001298
loc_6_00001258:
	tst.l -$0018(a6)
	beq.b loc_6_00001270
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,-(a7)
	pea.l -$00F8(a6)
	jsr loc_16_00000000.l
	bra.b loc_6_00001298
loc_6_00001270:
	tst.l -$0014(a6)
	beq.b loc_6_00001288
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,-(a7)
	pea.l -$00F8(a6)
	jsr loc_14_00000000.l
	bra.b loc_6_00001298
loc_6_00001288:
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,-(a7)
	pea.l -$00F8(a6)
	jsr loc_12_00000000.l
loc_6_00001298:
	move.l d0,d5
	addq.l #8,a7
	tst.l d5
	bne.b loc_6_000012D2
	moveq.l #0,d3
	move.w d4,d3
	move.l d3,d2
	moveq.l #0,d3
	move.w -$0086(a6),d3
	subq.l #1,d3
	cmp.l d3,d2
	beq.b loc_6_000012C8
	pea.l $0006.w
	clr.l -(a7)
	clr.l -(a7)
	clr.l -(a7)
	movea.l -$0074(a6),a3
	jsr (a3)
	move.l d0,d5
	lea.l $0010(a7),a7
loc_6_000012C8:
	addq.w #1,d4
loc_6_000012CA:
	cmp.w -$0086(a6),d4
	bcs.w loc_6_000011E0
loc_6_000012D2:
	pea.l -$00F8(a6)
	move.l a2,-(a7)
	move.l d5,-(a7)
loc_6_000012DA:
	jsr (a4)
	lea.l $000C(a7),a7
	movem.l -$0120(a6),d2-d7/a2-a5
	unlk a6
	rts
loc_6_000012EA:
	move.l d2,-(a7)
	move.l $0008(a7),d2
	moveq.l #10,d1
	move.l d2,d0
	jsr loc_38_0000007A.l
	moveq.l #4,d1
	cmp.l d0,d1
	bge.b loc_6_00001308
	moveq.l #10,d0
	add.l d0,d2
	bra.w loc_6_00001308
loc_6_00001308:
	moveq.l #10,d1
	move.l d2,d0
	jsr loc_38_0000009E.l
	move.l (a7)+,d2
	rts
loc_6_00001316:
	movea.l $0004(a7),a1
	movea.l loc_1_00000000.l,a0
	moveq.l #0,d0
	move.b $0A98(a0),d0
	add.w d0,d0
	movea.l #loc_7_00000020,a0
	move.w $0(a0,d0.w),d1
	beq.b loc_6_00001340
	andi.l #4294965503,(a1)
	moveq.l #0,d0
	move.w d1,d0
	or.l d0,(a1)
loc_6_00001340:
	rts
	dc.b $00,$00
    SECTION section_7,data
loc_7_00000000:
	dc.b $00,$08,$02,$0A,$0C,$04,$0E,$06,$03,$0B,$01,$09,$0E,$07,$0D,$05
loc_7_00000010:
	dc.b $05,$0C,$0E,$03,$08,$00,$06,$0A,$0D,$02,$04,$0E,$07,$0B,$09,$01
loc_7_00000020:
	dc.b $00,$00,$01,$00,$02,$00,$03,$00,$04,$00,$05,$00,$06,$00,$07,$00
    SECTION section_8,code
loc_8_00000000:
	link a6,#-4
	movem.l d2-d5/a2-a4,-(a7)
	movea.l #loc_1_00000000,a3
	movea.l #loc_1_00000004,a4
	pea.l $00E8.w
	movea.l (a3),a2
	pea.l $09B8(a2)
	jsr loc_43_00000000.l
	movea.l (a3),a0
	move.w $0A36(a0),d2
	cmpi.w #13,d2
	addq.l #8,a7
	bcc.b loc_8_00000050
	tst.w d2
	bne.b loc_8_0000003E
	movea.l (a3),a0
	lea.l $0A38(a0),a2
	bra.b loc_8_0000004C
loc_8_0000003E:
	move.w d2,d0
	asl.w #2,d0
	movea.l #loc_9_0000000E,a0
	movea.l $0(a0,d0.w),a2
loc_8_0000004C:
	move.l a2,d4
	bra.b loc_8_00000054
loc_8_00000050:
	bra.w loc_8_00000196
loc_8_00000054:
	tst.b (a2)
	bne.b loc_8_0000005C
	bra.w loc_8_00000196
loc_8_0000005C:
	clr.l -$0004(a6)
	pea.l -$0004(a6)
	jsr loc_6_00001316.l
	move.l #loc_1_00000020,-(a7)
	move.l a2,-(a7)
	jsr loc_8_000001CE.l
	tst.l d0
	lea.l $000C(a7),a7
	bne.b loc_8_000000C2
	pea.l $0001.w
	jsr loc_2_00000000.l
	movea.l (a3),a0
	movea.l $005C(a0),a1
	cmpi.w #35,$0008(a1)
	addq.l #4,a7
	bcs.b loc_8_000000A0
	movea.l (a4),a0
	clr.l $003A(a0)
loc_8_000000A0:
	move.l -$0004(a6),-(a7)
	pea.l $0005.w
	clr.l -(a7)
	move.l -$0004(a6),-(a7)
	clr.l -(a7)
	movea.l (a4),a2
	movea.l $002E(a2),a0
	jsr (a0)
	moveq.l #0,d0
	lea.l $0014(a7),a7
	bra.w loc_8_00000198
loc_8_000000C2:
	movea.l (a3),a0
	tst.l $0056(a0)
	beq.b loc_8_000000E6
	movea.l (a3),a2
	move.l $0056(a2),-(a7)
	jsr loc_40_00000058.l
	movea.l (a3),a0
	clr.l $0056(a0)
	movea.l (a3),a0
	move.w #$FFFF,$005A(a0)
	addq.l #4,a7
loc_8_000000E6:
	moveq.l #-2,d5
	move.l d5,-(a7)
	pea.l loc_9_00000000.l
	jsr loc_40_00000000.l
	move.l d0,d3
	addq.l #8,a7
	beq.w loc_8_00000196
	move.l d3,-(a7)
	jsr loc_40_00000030.l
	move.l d0,d5
	movea.l (a3),a2
	move.l d4,-(a7)
	jsr loc_40_00000044.l
	move.l d0,$0056(a2)
	movea.l (a3),a0
	movea.l (a3),a1
	move.l $0056(a1),d0
	lsl.l #2,d0
	move.l d0,$005C(a0)
	addq.l #8,a7
	beq.b loc_8_00000184
	movea.l (a3),a0
	movea.l $005C(a0),a1
	lea.l $000C(a1),a2
	move.l a2,(a4)
	move.l (a3),-(a7)
	movea.l (a4),a2
	movea.l $0004(a2),a0
	jsr (a0)
	clr.l -(a7)
	jsr loc_2_00000000.l
	movea.l (a3),a0
	move.w d2,$005A(a0)
	movea.l #loc_1_00000020,a0
	movea.l d4,a1
	addq.l #8,a7
loc_8_00000156:
	move.b (a1)+,(a0)+
	bne.b loc_8_00000156
	move.l d5,-(a7)
	jsr loc_40_00000030.l
	move.l d3,-(a7)
	jsr loc_40_0000001C.l
	movea.l (a3),a0
	movea.l $005C(a0),a1
	cmpi.w #35,$0008(a1)
	addq.l #8,a7
	bcs.b loc_8_00000180
	movea.l (a4),a0
	clr.l $003A(a0)
loc_8_00000180:
	bra.w loc_8_000000A0
loc_8_00000184:
	move.l d5,-(a7)
	jsr loc_40_00000030.l
	move.l d3,-(a7)
	jsr loc_40_0000001C.l
	addq.l #8,a7
loc_8_00000196:
	moveq.l #-1,d0
loc_8_00000198:
	movem.l -$0020(a6),d2-d5/a2-a4
	unlk a6
	rts
loc_8_000001A2:
	movea.l loc_1_00000000.l,a0
	tst.l $0056(a0)
	beq.b loc_8_000001CC
	movea.l loc_1_00000004.l,a0
	movea.l $0008(a0),a0
	jsr (a0)
	movea.l loc_1_00000000.l,a0
	move.l $0056(a0),-(a7)
	jsr loc_40_00000058.l
	addq.l #4,a7
loc_8_000001CC:
	rts
loc_8_000001CE:
	movea.l $0004(a7),a0
	movea.l $0008(a7),a1
loc_8_000001D6:
	move.b (a0)+,d0
	move.b (a1)+,d1
	cmpi.b #97,d0
	blt.b loc_8_000001EA
	cmpi.b #122,d0
	bgt.b loc_8_000001EA
	subi.b #32,d0
loc_8_000001EA:
	cmpi.b #97,d1
	blt.b loc_8_000001FA
	cmpi.b #122,d1
	bgt.b loc_8_000001FA
	subi.b #32,d1
loc_8_000001FA:
	cmp.b d1,d0
	bne.b loc_8_00000206
	tst.b d0
	beq.b loc_8_00000206
	tst.b d1
	bne.b loc_8_000001D6
loc_8_00000206:
	cmp.b d1,d0
	bne.b loc_8_0000020E
	moveq.l #0,d0
	bra.b loc_8_00000218
loc_8_0000020E:
	tst.b d0
	bne.b loc_8_00000216
	moveq.l #-1,d0
	bra.b loc_8_00000218
loc_8_00000216:
	moveq.l #1,d0
loc_8_00000218:
	rts
	dc.b $00,$00
    SECTION section_9,data
loc_9_00000000:
	dc.b $44,$45,$56,$53,$3A,$70,$72,$69,$6E,$74,$65,$72,$73,$00
loc_9_0000000E:
	dc.b $00,$00,$00,$00
	dc.l loc_9_00000042	; pointer_table
	dc.l loc_9_00000058
	dc.l loc_9_00000068
	dc.l loc_9_00000074
	dc.l loc_9_00000080
	dc.l loc_9_00000096
	dc.l loc_9_000000A4
	dc.l loc_9_000000AA
	dc.l loc_9_000000B6
	dc.l loc_9_000000C2
	dc.l loc_9_000000D4
	dc.l loc_9_000000E0
loc_9_00000042:
	dc.b "ALPHACOM_ALPHAPRO_101",$00	; string
loc_9_00000058:
	dc.b "BROTHER_HR-15XL",$00	; string
loc_9_00000068:
	dc.b "CBM_MPS1000",$00	; string
loc_9_00000074:
	dc.b "DIABLO_630",$00	; string
	dc.b $00
loc_9_00000080:
	dc.b $44,$49,$41,$42,$4C,$4F,$5F,$41,$44,$56,$41,$4E,$54,$41,$47,$45
	dc.b $5F,$44,$32,$35,$00,$00
loc_9_00000096:
	dc.b $44,$49,$41,$42,$4C,$4F,$5F,$43,$2D,$31,$35,$30,$00,$00
loc_9_000000A4:
	dc.b "EPSON",$00	; string
loc_9_000000AA:
	dc.b "EPSON_JX-80",$00	; string
loc_9_000000B6:
	dc.b "OKIMATE_20",$00	; string
	dc.b $00
loc_9_000000C2:
	dc.b "QUME_LETTERPRO_20",$00	; string
loc_9_000000D4:
	dc.b "HP_LASERJET",$00	; string
loc_9_000000E0:
	dc.b "HP_LASERJET_PLUS",$00	; string
	dc.b $00,$00,$00
    SECTION section_10,code
loc_10_00000000:
	link a6,#-400
	movem.l d2-d6/a2-a5,-(a7)
	movea.l $0008(a6),a3
	move.l #loc_11_00000194,d3
	move.l #loc_11_00000182,d5
	move.l #loc_11_0000007A,-$0004(a6)
	moveq.l #0,d1
	movea.l $0024(a3),a0
	move.l a0,-$0008(a6)
	moveq.l #-1,d0
	movea.l d0,a4
	cmpa.l a0,a4
	bne.b loc_10_00000048
	clr.l -$0008(a6)
loc_10_00000036:
	movea.l -$0008(a6),a0
	addq.l #1,-$0008(a6)
	move.l $0028(a3),d0
	tst.b $0(a0,d0.l)
	bne.b loc_10_00000036
loc_10_00000048:
	clr.l loc_3_00000000.l
	movea.l d5,a0
	clr.l (a0)
	movea.l loc_1_00000000.l,a1
	movea.l $005C(a1),a2
	cmpi.w #35,$0008(a2)
	bcs.b loc_10_00000070
	movea.l loc_1_00000004.l,a1
	moveq.l #1,d0
	move.l d0,$003A(a1)
loc_10_00000070:
	bra.w loc_10_0000016C
loc_10_00000074:
	movea.l d3,a0
	move.l (a0),loc_11_00000190.l
	clr.w loc_11_0000018E.l
	bra.b loc_10_000000A0
loc_10_00000084:
	movea.l d3,a5
	movea.l (a5),a0
	addq.l #1,(a5)
	movea.l #loc_11_0000007A,a1
	movea.l d5,a5
	movea.l (a5),a4
	addq.l #1,(a5)
	move.l $0028(a3),d0
	move.b $0(a4,d0.l),$0(a1,a0.l)
loc_10_000000A0:
	movea.l d5,a0
	move.l -$0008(a6),d0
	cmp.l (a0),d0
	ble.b loc_10_000000B4
	movea.l d3,a0
	cmpi.l #256,(a0)
	blt.b loc_10_00000084
loc_10_000000B4:
	movea.l d3,a2
	move.l (a2),-$000C(a6)
	pea.l -$0190(a6)
	move.l -$000C(a6),-(a7)
	jsr loc_10_0000040E.l
	movea.l d0,a4
	movea.l loc_1_00000000.l,a1
	move.b $0AA0(a1),d2
	addq.l #8,a7
	bne.b loc_10_000000F8
	move.l a4,-(a7)
	pea.l -$0190(a6)
	jsr loc_0_00000858.l
	move.l d0,d1
	addq.l #8,a7
	bne.w loc_10_0000016C
	jsr loc_0_000009BA.l
	move.l d0,d1
	bra.w loc_10_0000016C
loc_10_000000F8:
	moveq.l #0,d6
	moveq.l #0,d4
	moveq.l #0,d1
	bra.b loc_10_00000164
loc_10_00000100:
	bra.b loc_10_00000104
loc_10_00000102:
	addq.l #1,d6
loc_10_00000104:
	movea.l d6,a0
	adda.l d4,a0
	cmpa.l a0,a4
	ble.b loc_10_0000011A
	movea.l d6,a0
	adda.l d4,a0
	lea.l -$0190(a6),a1
	cmp.b $0(a1,a0.l),d2
	bne.b loc_10_00000102
loc_10_0000011A:
	move.l d6,-(a7)
	lea.l -$0190(a6),a2
	pea.l $0(a2,d4.l)
	jsr loc_0_00000858.l
	move.l d0,d1
	addq.l #8,a7
	bne.b loc_10_00000138
	jsr loc_0_000009BA.l
	move.l d0,d1
loc_10_00000138:
	tst.l d1
	bne.b loc_10_0000015A
	movea.l d6,a0
	adda.l d4,a0
	lea.l -$0190(a6),a1
	cmp.b $0(a1,a0.l),d2
	bne.b loc_10_0000015A
	clr.l -(a7)
	pea.l $0001.w
	jsr loc_0_00000CE8.l
	move.l d0,d1
	addq.l #8,a7
loc_10_0000015A:
	movea.l d6,a0
	adda.l d4,a0
	addq.l #1,a0
	move.l a0,d4
	moveq.l #0,d6
loc_10_00000164:
	cmp.l a4,d4
	bge.b loc_10_0000016C
	tst.l d1
	beq.b loc_10_00000100
loc_10_0000016C:
	tst.l d1
	bne.b loc_10_0000017C
	movea.l d5,a0
	move.l -$0008(a6),d0
	cmp.l (a0),d0
	bgt.w loc_10_00000074
loc_10_0000017C:
	movea.l d3,a0
	clr.l (a0)
	tst.l d1
	bne.b loc_10_000001BC
	tst.w loc_11_0000018E.l
	beq.b loc_10_000001BC
	bra.b loc_10_000001B0
loc_10_0000018E:
	movea.l d3,a5
	movea.l (a5),a0
	addq.l #1,(a5)
	movea.l #loc_11_0000007A,a1
	movea.l #loc_11_0000018A,a2
	movea.l (a2),a4
	addq.l #1,(a2)
	movea.l #loc_11_0000007A,a2
	move.b $0(a2,a4.l),$0(a1,a0.l)
loc_10_000001B0:
	move.l -$000C(a6),d0
	cmp.l loc_11_0000018A.l,d0
	bgt.b loc_10_0000018E
loc_10_000001BC:
	tst.l d1
	bne.b loc_10_000001C8
	move.l -$0008(a6),$0020(a3)
	bra.b loc_10_000001CC
loc_10_000001C8:
	clr.l $0020(a3)
loc_10_000001CC:
	moveq.l #0,d0
	move.b d1,d0
	movem.l -$01B4(a6),d2-d6/a2-a5
	unlk a6
	rts
loc_10_000001DA:
	link a6,#-4
	movem.l d2-d6/a2-a4,-(a7)
	move.l $0008(a6),d4
	move.l $000C(a6),d5
	movea.l #loc_11_000001BC,a3
	movea.l #loc_11_000001A6,a2
	pea.l loc_11_000001B0.l
	pea.l (a2)
	move.l d4,-(a7)
	pea.l loc_11_00000186.l
	jsr loc_10_00000900.l
	move.b d0,loc_11_000001A4.l
	move.b #$FF,(a3)
	cmpi.b #104,loc_11_000001A4.l
	lea.l $0010(a7),a7
	beq.b loc_10_0000022E
	cmpi.b #108,loc_11_000001A4.l
	bne.b loc_10_00000252
loc_10_0000022E:
	cmpi.b #20,(a2)
	bne.b loc_10_00000252
	moveq.l #0,d1
	move.b loc_11_000001A4.l,d1
	move.l d1,d0
	moveq.l #4,d1
	and.l d1,d0
	jsr loc_38_0000009E.l
	move.b d0,loc_11_0000017E.l
	bra.w loc_10_00000404
loc_10_00000252:
	clr.l -$0004(a6)
	bra.w loc_10_000003F6
loc_10_0000025A:
	moveq.l #0,d6
loc_10_0000025C:
	move.b loc_11_000001A4.l,d0
	movea.l #loc_11_0000002C,a0
	cmp.b $0(a0,d6.l),d0
	bne.w loc_10_0000039A
	tst.l loc_11_000001B0.l
	bne.b loc_10_00000290
	moveq.l #2,d0
	cmp.l d6,d0
	bne.b loc_10_00000290
	moveq.l #0,d0
	move.b (a2),d0
	moveq.l #1,d1
	and.l d1,d0
	moveq.l #55,d1
	add.l d1,d0
	move.b d0,(a3)
	bra.w loc_10_000003A4
loc_10_00000290:
	moveq.l #1,d0
	cmp.l loc_11_000001B0.l,d0
	beq.b loc_10_000002A8
	moveq.l #5,d0
	cmp.l d6,d0
	bne.b loc_10_000002A8
	move.b #$FF,(a3)
	bra.w loc_10_000003A4
loc_10_000002A8:
	moveq.l #9,d0
	cmp.l d6,d0
	bne.b loc_10_000002BA
	tst.b (a2)
	bne.b loc_10_000002BA
	move.b #$3B,(a3)
	bra.w loc_10_000003A4
loc_10_000002BA:
	tst.l loc_11_000001B0.l
	bne.b loc_10_000002D0
	moveq.l #10,d0
	cmp.l d6,d0
	bne.b loc_10_000002D0
	move.b #$40,(a3)
	bra.w loc_10_000003A4
loc_10_000002D0:
	moveq.l #2,d0
	cmp.l loc_11_000001B0.l,d0
	bne.b loc_10_000002E8
	moveq.l #12,d0
	cmp.l d6,d0
	bne.b loc_10_000002E8
	move.b #$4B,(a3)
	bra.w loc_10_000003A4
loc_10_000002E8:
	moveq.l #2,d0
	cmp.l loc_11_000001B0.l,d0
	bne.b loc_10_0000030A
	moveq.l #13,d0
	cmp.l d6,d0
	bne.b loc_10_0000030A
	moveq.l #0,d0
	move.b (a2),d0
	move.l d0,loc_11_000001B8.l
	move.b #$4C,(a3)
	bra.w loc_10_000003A4
loc_10_0000030A:
	moveq.l #6,d0
	cmp.l d6,d0
	bge.b loc_10_00000324
	moveq.l #10,d0
	cmp.l d6,d0
	beq.b loc_10_00000324
	movea.l #loc_11_0000003A,a0
	move.b $0(a0,d6.l),(a3)
	bra.w loc_10_000003A4
loc_10_00000324:
	tst.l d6
	bne.b loc_10_00000336
	cmpi.b #29,(a2)
	bls.b loc_10_00000336
	move.b #$C,(a3)
	bra.w loc_10_000003A4
loc_10_00000336:
	moveq.l #7,d0
	cmp.l d6,d0
	ble.b loc_10_0000039A
	moveq.l #0,d0
	movea.l d0,a4
loc_10_00000340:
	move.b (a2),d0
	move.l d6,d1
	move.l d1,d2
	add.l d1,d1
	move.l d1,d3
	add.l d1,d1
	add.l d3,d1
	add.l d2,d1
	movea.l #loc_11_00000048,a1
	adda.l d1,a1
	cmp.b $0(a1,a4.l),d0
	bne.b loc_10_00000374
	movea.l #loc_11_0000003A,a0
	move.b $0(a0,d6.l),d0
	ext.w d0
	ext.l d0
	move.l a4,d1
	add.l d1,d0
	move.b d0,(a3)
	bra.b loc_10_0000037C
loc_10_00000374:
	addq.l #1,a4
	moveq.l #7,d0
	cmp.l a4,d0
	bgt.b loc_10_00000340
loc_10_0000037C:
	move.b (a2),d0
	move.l d6,d1
	move.l d1,d2
	add.l d1,d1
	move.l d1,d3
	add.l d1,d1
	add.l d3,d1
	add.l d2,d1
	movea.l #loc_11_00000048,a1
	adda.l d1,a1
	cmp.b $0(a1,a4.l),d0
	beq.b loc_10_000003A4
loc_10_0000039A:
	addq.l #1,d6
	moveq.l #14,d0
	cmp.l d6,d0
	bgt.w loc_10_0000025C
loc_10_000003A4:
	cmpi.b #65,(a3)
	beq.b loc_10_000003B0
	cmpi.b #64,(a3)
	bne.b loc_10_000003B6
loc_10_000003B0:
	clr.l loc_11_00000198.l
loc_10_000003B6:
	tst.b (a3)
	blt.b loc_10_000003DA
	clr.l -(a7)
	pea.l (a2)
	move.l d5,-(a7)
	move.l d4,-(a7)
	move.b (a3),d1
	ext.w d1
	ext.l d1
	move.l d1,-(a7)
	jsr loc_10_00000864.l
	move.l d0,loc_11_000001B4.l
	lea.l $0014(a7),a7
loc_10_000003DA:
	moveq.l #0,d6
loc_10_000003DC:
	move.l d6,d0
	addq.l #1,d0
	move.b $0(a2,d0.l),$0(a2,d6.l)
	addq.l #1,d6
	moveq.l #9,d0
	cmp.l d6,d0
	bgt.b loc_10_000003DC
	clr.b $0009(a2)
	addq.l #1,-$0004(a6)
loc_10_000003F6:
	move.l -$0004(a6),d0
	cmp.l loc_11_00000198.l,d0
	ble.w loc_10_0000025A
loc_10_00000404:
	movem.l -$0024(a6),d2-d6/a2-a4
	unlk a6
	rts
loc_10_0000040E:
	link a6,#-4
	movem.l d2-d6/a2-a5,-(a7)
	move.l $0008(a6),d4
	move.l $000C(a6),d3
	movea.l #loc_11_000001A4,a3
	movea.l #loc_11_000001BC,a4
	movea.l #loc_11_0000019C,a2
	clr.l loc_11_00000186.l
	clr.l loc_11_000001B0.l
	clr.l loc_11_0000018A.l
	clr.l loc_11_00000198.l
	clr.l (a2)
	clr.l loc_11_000001B4.l
	clr.l loc_11_000001A0.l
	movea.l loc_1_00000000.l,a0
	movea.l $005C(a0),a0
	moveq.l #0,d0
	move.w $0008(a0),d0
	move.l d0,d6
	bra.w loc_10_00000802
loc_10_0000046C:
	movea.l #loc_11_00000186,a0
	move.l (a0),d0
	addq.l #1,(a0)
	movea.l #loc_11_0000007A,a0
	move.b $0(a0,d0.l),(a3)
	tst.l loc_11_000001B8.l
	ble.b loc_10_0000049C
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a1
	move.b (a3),$0(a1,d3.l)
	subq.l #1,loc_11_000001B8.l
	bra.w loc_10_00000802
loc_10_0000049C:
	moveq.l #-1,d2
	moveq.l #35,d0
	cmp.l d6,d0
	bgt.b loc_10_000004DA
	movea.l loc_1_00000004.l,a0
	tst.l $003E(a0)
	beq.b loc_10_000004DA
	move.b loc_11_0000017E.l,d1
	ext.w d1
	ext.l d1
	move.l d1,-(a7)
	moveq.l #0,d0
	move.b (a3),d0
	move.l d0,-(a7)
	movea.l (a2),a0
	pea.l $0(a0,d3.l)
	movea.l loc_1_00000004.l,a0
	movea.l $003E(a0),a0
	jsr (a0)
	move.l d0,d2
	lea.l $000C(a7),a7
loc_10_000004DA:
	tst.l d2
	blt.b loc_10_000004E6
	move.l d2,d0
	add.l d0,(a2)
	bra.w loc_10_00000802
loc_10_000004E6:
	cmpi.b #27,(a3)
	bne.w loc_10_00000624
	move.l d4,-(a7)
	pea.l loc_11_00000186.l
	jsr loc_10_0000099E.l
	move.b d0,(a3)
	cmpi.b #35,(a3)
	addq.l #8,a7
	bne.w loc_10_00000580
	move.b #$FF,(a4)
	move.l d4,-(a7)
	pea.l loc_11_00000186.l
	jsr loc_10_0000099E.l
	move.b d0,(a3)
	moveq.l #0,d5
	addq.l #8,a7
loc_10_00000520:
	move.b (a3),d0
	movea.l #loc_11_0000001C,a0
	cmp.b $0(a0,d5.l),d0
	bne.b loc_10_00000538
	movea.l #loc_11_00000024,a0
	move.b $0(a0,d5.l),(a4)
loc_10_00000538:
	addq.l #1,d5
	moveq.l #8,d0
	cmp.l d5,d0
	bgt.b loc_10_00000520
	tst.b (a4)
	ble.w loc_10_00000802
	cmpi.b #1,(a4)
	bne.b loc_10_00000558
	clr.b loc_11_0000017C.l
	clr.b loc_11_0000017E.l
loc_10_00000558:
	clr.l -(a7)
	pea.l loc_11_000001A6.l
	move.l d3,-(a7)
	move.l d4,-(a7)
	move.b (a4),d1
	ext.w d1
	ext.l d1
	move.l d1,-(a7)
	jsr loc_10_00000864.l
	move.l d0,loc_11_000001B4.l
	lea.l $0014(a7),a7
	bra.w loc_10_00000802
loc_10_00000580:
	cmpi.b #40,(a3)
	bne.b loc_10_000005C2
	move.b #$FF,(a4)
	move.l d4,-(a7)
	pea.l loc_11_00000186.l
	jsr loc_10_0000099E.l
	move.b d0,(a3)
	moveq.l #0,d5
	addq.l #8,a7
loc_10_0000059E:
	move.b (a3),d0
	movea.l #loc_11_00000010,a0
	cmp.b $0(a0,d5.l),d0
	bne.b loc_10_000005AE
	move.b d5,(a4)
loc_10_000005AE:
	addq.l #1,d5
	moveq.l #11,d0
	cmp.l d5,d0
	bgt.b loc_10_0000059E
	tst.b (a4)
	blt.w loc_10_00000802
	addi.b #34,(a4)
	bra.b loc_10_00000558
loc_10_000005C2:
	cmpi.b #91,(a3)
	bne.b loc_10_000005CC
	bra.w loc_10_000006C8
loc_10_000005CC:
	moveq.l #0,d5
loc_10_000005CE:
	movea.l #loc_11_00000000,a0
	move.b $0(a0,d5.l),d0
	cmp.b (a3),d0
	bne.b loc_10_00000618
	movea.l #loc_11_00000008,a0
	move.b $0(a0,d5.l),(a4)
	bne.b loc_10_000005F4
	clr.b loc_11_0000017C.l
	clr.b loc_11_0000017E.l
loc_10_000005F4:
	clr.l -(a7)
	pea.l loc_11_000001A6.l
	move.l d3,-(a7)
	move.l d4,-(a7)
	move.b (a4),d1
	ext.w d1
	ext.l d1
	move.l d1,-(a7)
	jsr loc_10_00000864.l
	move.l d0,loc_11_000001B4.l
	lea.l $0014(a7),a7
loc_10_00000618:
	addq.l #1,d5
	moveq.l #8,d0
	cmp.l d5,d0
	ble.w loc_10_00000802
	bra.b loc_10_000005CE
loc_10_00000624:
	cmpi.b #10,(a3)
	bne.w loc_10_000006C2
	tst.b loc_11_0000017E.l
	bne.b loc_10_0000063A
	move.b #$3,(a4)
	bra.b loc_10_0000063E
loc_10_0000063A:
	move.b #$2,(a4)
loc_10_0000063E:
	pea.l $0001.w
	pea.l loc_11_000001A6.l
	move.l d3,-(a7)
	move.l d4,-(a7)
	move.b (a4),d1
	ext.w d1
	ext.l d1
	move.l d1,-(a7)
	jsr loc_10_00000864.l
	move.l d0,loc_11_000001B4.l
	lea.l $0014(a7),a7
	bge.w loc_10_00000802
	tst.b loc_11_0000017E.l
	bne.b loc_10_000006B2
	move.l (a2),d0
	addq.l #2,d0
	cmpi.l #256,d0
	ble.b loc_10_00000696
	move.l loc_11_00000186.l,d0
	subq.l #1,d0
	move.l d0,loc_11_0000018A.l
	moveq.l #2,d0
	move.l d0,loc_11_000001A0.l
	bra.w loc_10_00000802
loc_10_00000696:
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a1
	move.b #$A,$0(a1,d3.l)
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a1
	move.b #$D,$0(a1,d3.l)
	bra.w loc_10_00000802
loc_10_000006B2:
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a1
	move.b #$A,$0(a1,d3.l)
	bra.w loc_10_00000802
loc_10_000006C2:
	cmpi.b #155,(a3)
	bne.b loc_10_000006D6
loc_10_000006C8:
	move.l d3,-(a7)
	move.l d4,-(a7)
	jsr loc_10_000001DA(pc)
	addq.l #8,a7
	bra.w loc_10_00000802
loc_10_000006D6:
	cmpi.b #160,(a3)
	bcs.w loc_10_000007F8
	move.l #loc_5_00000000,-$0004(a6)
	moveq.l #33,d0
	cmp.l d6,d0
	bgt.b loc_10_00000704
	movea.l loc_1_00000004.l,a0
	tst.l $0036(a0)
	beq.b loc_10_00000704
	movea.l loc_1_00000004.l,a0
	move.l $0036(a0),-$0004(a6)
loc_10_00000704:
	moveq.l #0,d1
	move.b (a3),d1
	move.l d1,d0
	addi.l #4294967136,d0
	asl.l #2,d0
	movea.l d0,a0
	movea.l -$0004(a6),a5
	movea.l $0(a0,a5.l),a1
	clr.l loc_11_000001A0.l
	bra.b loc_10_00000758
loc_10_00000724:
	cmpi.b #92,(a1)+
	bne.b loc_10_00000752
	cmpi.b #48,(a1)
	blt.b loc_10_00000750
	cmpi.b #57,(a1)
	bgt.b loc_10_00000750
	moveq.l #0,d5
loc_10_00000738:
	cmpi.b #48,(a1)
	blt.b loc_10_00000752
	cmpi.b #57,(a1)
	bgt.b loc_10_00000752
	addq.l #1,a1
	addq.l #1,d5
	moveq.l #3,d0
	cmp.l d5,d0
	ble.b loc_10_00000752
	bra.b loc_10_00000738
loc_10_00000750:
	addq.l #1,a1
loc_10_00000752:
	addq.l #1,loc_11_000001A0.l
loc_10_00000758:
	tst.b (a1)
	bne.b loc_10_00000724
	move.l (a2),d0
	add.l loc_11_000001A0.l,d0
	cmpi.l #256,d0
	ble.b loc_10_0000077E
	move.l loc_11_00000186.l,d0
	subq.l #1,d0
	move.l d0,loc_11_0000018A.l
	bra.w loc_10_00000802
loc_10_0000077E:
	moveq.l #0,d1
	move.b (a3),d1
	move.l d1,d0
	addi.l #4294967136,d0
	asl.l #2,d0
	movea.l d0,a0
	movea.l -$0004(a6),a5
	movea.l $0(a0,a5.l),a1
	bra.b loc_10_000007F2
loc_10_00000798:
	cmpi.b #92,(a1)
	bne.b loc_10_000007E8
	addq.l #1,a1
	cmpi.b #48,(a1)
	blt.b loc_10_000007AC
	cmpi.b #57,(a1)
	ble.b loc_10_000007AE
loc_10_000007AC:
	bra.b loc_10_000007E8
loc_10_000007AE:
	moveq.l #0,d2
	moveq.l #0,d5
loc_10_000007B2:
	cmpi.b #48,(a1)
	blt.b loc_10_000007DC
	cmpi.b #57,(a1)
	bgt.b loc_10_000007DC
	move.b (a1)+,d0
	ext.w d0
	ext.l d0
	add.l d2,d2
	move.l d2,d1
	asl.l #2,d2
	add.l d1,d2
	add.l d2,d0
	moveq.l #48,d1
	sub.l d1,d0
	move.l d0,d2
	addq.l #1,d5
	moveq.l #3,d0
	cmp.l d5,d0
	bgt.b loc_10_000007B2
loc_10_000007DC:
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a5
	move.b d2,$0(a5,d3.l)
	bra.b loc_10_000007F2
loc_10_000007E8:
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a5
	move.b (a1)+,$0(a5,d3.l)
loc_10_000007F2:
	tst.b (a1)
	beq.b loc_10_00000802
	bra.b loc_10_00000798
loc_10_000007F8:
	move.l (a2),d0
	addq.l #1,(a2)
	movea.l d0,a1
	move.b (a3),$0(a1,d3.l)
loc_10_00000802:
	cmp.l loc_11_00000186.l,d4
	ble.b loc_10_00000824
	move.l (a2),d0
	add.l loc_11_000001A0.l,d0
	cmpi.l #256,d0
	bge.b loc_10_00000824
	tst.l loc_11_000001B4.l
	ble.w loc_10_0000046C
loc_10_00000824:
	tst.l loc_11_0000018A.l
	beq.b loc_10_0000083A
	move.l loc_11_0000018A.l,d0
	cmp.l loc_11_00000186.l,d0
	blt.b loc_10_00000844
loc_10_0000083A:
	move.l d4,d0
	sub.l loc_11_00000186.l,d0
	bra.b loc_10_0000084C
loc_10_00000844:
	move.l d4,d0
	sub.l loc_11_0000018A.l,d0
loc_10_0000084C:
	sub.l d0,loc_11_00000182.l
	clr.l loc_11_00000194.l
	move.l (a2),d0
	movem.l -$0028(a6),d2-d6/a2-a5
	unlk a6
	rts
loc_10_00000864:
	link a6,#-260
	move.l d2,-(a7)
	move.b $000B(a6),d0
	move.l $0010(a6),d2
	clr.l loc_11_000001A0.l
	move.b d0,d1
	ext.w d1
	move.l $0014(a6),-(a7)
	pea.l -$0104(a6)
	moveq.l #0,d0
	move.w d1,d0
	move.l d0,-(a7)
	jsr loc_2_00000238.l
	move.l d0,d1
	lea.l $000C(a7),a7
	bgt.b loc_10_0000089A
	bra.b loc_10_000008F6
loc_10_0000089A:
	movea.l loc_11_0000019C.l,a1
	adda.l d1,a1
	move.l a1,d0
	cmpi.l #256,d0
	ble.b loc_10_000008D4
	move.l d1,loc_11_000001A0.l
	tst.b $001B(a6)
	bne.b loc_10_000008C0
	jsr loc_10_000009D6.l
	bra.b loc_10_000008CE
loc_10_000008C0:
	movea.l loc_11_00000186.l,a1
	subq.l #1,a1
	move.l a1,loc_11_0000018A.l
loc_10_000008CE:
	moveq.l #1,d0
	move.l d0,d1
	bra.b loc_10_000008F6
loc_10_000008D4:
	moveq.l #0,d0
	bra.b loc_10_000008F0
loc_10_000008D8:
	movea.l #loc_11_0000019C,a0
	movea.l (a0),a1
	addq.l #1,(a0)
	movea.l a1,a0
	lea.l -$0104(a6),a1
	move.b $0(a1,d0.l),$0(a0,d2.l)
	addq.l #1,d0
loc_10_000008F0:
	cmp.l d1,d0
	blt.b loc_10_000008D8
	moveq.l #0,d1
loc_10_000008F6:
	move.l d1,d0
	move.l -$0108(a6),d2
	unlk a6
	rts
loc_10_00000900:
	movem.l d2-d4/a2-a4,-(a7)
	move.l $001C(a7),d2
	move.l $0020(a7),d3
	movea.l $0024(a7),a3
	moveq.l #0,d0
	movea.l d0,a4
	clr.b (a3)
	bra.b loc_10_00000962
loc_10_00000918:
	cmpi.b #59,d1
	bne.b loc_10_00000926
	addq.l #1,a4
	clr.b $0(a4,a3.l)
	bra.b loc_10_00000962
loc_10_00000926:
	cmpi.b #32,d1
	bne.b loc_10_00000936
	movea.l $0028(a7),a1
	moveq.l #1,d0
loc_10_00000932:
	move.l d0,(a1)
	bra.b loc_10_00000962
loc_10_00000936:
	cmpi.b #34,d1
	bne.b loc_10_00000944
	movea.l $0028(a7),a1
	moveq.l #2,d0
	bra.b loc_10_00000932
loc_10_00000944:
	movea.l a4,a1
	moveq.l #0,d0
	move.b d1,d0
	movea.l d0,a0
	moveq.l #48,d0
	suba.l d0,a0
	moveq.l #0,d0
	move.b $0(a4,a3.l),d0
	muls.w #$A,d0
	adda.l d0,a0
	move.l a0,d4
	move.b d4,$0(a1,a3.l)
loc_10_00000962:
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_10_0000099E.l
	move.b d0,d1
	cmpi.b #48,d0
	addq.l #8,a7
	bcs.b loc_10_0000097C
	cmpi.b #57,d1
	bls.b loc_10_00000918
loc_10_0000097C:
	cmpi.b #32,d1
	beq.b loc_10_00000918
	cmpi.b #59,d1
	beq.b loc_10_00000918
	cmpi.b #34,d1
	beq.b loc_10_00000918
	move.l a4,loc_11_00000198.l
	moveq.l #0,d0
	move.b d1,d0
	movem.l (a7)+,d2-d4/a2-a4
	rts
loc_10_0000099E:
	movea.l $0004(a7),a1
	move.l $0008(a7),d0
	move.l (a1),d1
	addq.l #1,(a1)
	movea.l #loc_11_0000007A,a0
	move.b $0(a0,d1.l),d1
	cmp.l (a1),d0
	blt.b loc_10_000009C4
	cmpi.l #256,loc_11_0000019C.l
	blt.b loc_10_000009D0
loc_10_000009C4:
	jsr loc_10_000009D6.l
	clr.b d1
	bra.w loc_10_000009D0
loc_10_000009D0:
	moveq.l #0,d0
	move.b d1,d0
	rts
loc_10_000009D6:
	movea.l #loc_11_0000018A,a1
	move.l loc_11_00000186.l,d0
	subq.l #1,d0
	move.l d0,(a1)
	bra.b loc_10_000009EA
loc_10_000009E8:
	subq.l #1,(a1)
loc_10_000009EA:
	tst.l (a1)
	ble.b loc_10_00000A06
	move.l (a1),d1
	movea.l #loc_11_0000007A,a0
	moveq.l #0,d0
	move.b $0(a0,d1.l),d0
	moveq.l #127,d1
	and.l d1,d0
	moveq.l #27,d1
	cmp.l d0,d1
	bne.b loc_10_000009E8
loc_10_00000A06:
	move.w #$1,loc_11_0000018E.l
	move.l (a1),d0
	rts
	dc.b $00,$00
    SECTION section_11,data
loc_11_00000000:
	dc.b "cDEMLKHJ"	; string
loc_11_00000008:
	dc.b $00,$02,$03,$04,$20,$21,$43,$44
loc_11_00000010:
	dc.b $42,$52,$4B,$41,$45,$48,$59,$5A,$4A,$36,$43,$00
loc_11_0000001C:
	dc.b $31,$39,$30,$38,$32,$33,$34,$35
loc_11_00000024:
	dc.b $01,$3C,$3D,$3E,$3F,$42,$49,$4A
loc_11_0000002C:
	dc.b "mwzvpFgEtqrsxr"	; string
loc_11_0000003A:
	dc.b $05,$0E,$15,$1B,$2D,$31,$45,$30,$39,$3A,$40,$41,$4B,$4C
loc_11_00000048:
	dc.b $00,$03,$17,$04,$18,$01,$16,$00,$02,$01,$04,$03,$06,$05,$06,$05
	dc.b $04,$03,$02,$01,$FF,$02,$01,$04,$03,$00,$FF,$FF,$02,$01,$00,$FF
	dc.b $FF,$FF,$FF,$05,$07,$06,$00,$03,$01,$FF,$00,$03,$01,$04,$FF,$FF
	dc.b $FF,$00
loc_11_0000007A:
	dcb.b $102,$00
loc_11_0000017C:
	dc.b $00,$00
loc_11_0000017E:
	dc.b $00,$00
loc_11_00000180:
	dc.b $00,$00
loc_11_00000182:
	dc.b $00,$00,$00,$00
loc_11_00000186:
	dc.b $00,$00,$00,$00
loc_11_0000018A:
	dc.b $00,$00,$00,$00
loc_11_0000018E:
	dc.b $00,$00
loc_11_00000190:
	dc.b $00,$00,$00,$00
loc_11_00000194:
	dc.b $00,$00,$00,$00
loc_11_00000198:
	dc.b $00,$00,$00,$00
loc_11_0000019C:
	dc.b $00,$00,$00,$00
loc_11_000001A0:
	dc.b $00,$00,$00,$00
loc_11_000001A4:
	dc.b $00,$00
loc_11_000001A6:
	dcb.b $A,$00
loc_11_000001B0:
	dc.b $00,$00,$00,$00
loc_11_000001B4:
	dc.b $00,$00,$00,$00
loc_11_000001B8:
	dc.b $00,$00,$00,$00
loc_11_000001BC:
	dc.b $00,$00,$00,$00
    SECTION section_12,code
loc_12_00000000:
	link a6,#-16
	movem.l d2-d6/a2,-(a7)
	movea.l $0008(a6),a2
	move.l $000C(a6),d2
	clr.w d5
	move.w $0056(a2),-$0002(a6)
	move.w $005A(a2),-$0004(a6)
	move.w $0064(a2),-$0008(a6)
	move.w $0066(a2),-$000A(a6)
	move.w $0068(a2),d0
	move.w d0,-$000C(a6)
	move.w d0,-$000E(a6)
	move.w $004E(a2),d4
	andi.w #2048,d4
	moveq.l #0,d6
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #1024,d1
	beq.b loc_12_0000005C
	movea.l loc_1_00000000.l,a0
	tst.w $0A64(a0)
	beq.b loc_12_0000005C
	moveq.l #1,d6
loc_12_0000005C:
	move.l a2,-(a7)
	jsr loc_20_000008A8.l
	tst.w d4
	addq.l #4,a7
	beq.b loc_12_000000A6
	move.l a2,-(a7)
	jsr loc_36_00000000.l
	cmpi.w #1,-$0004(a6)
	addq.l #4,a7
	bne.b loc_12_00000096
	btst.b #7,$0071(a2)
	bne.b loc_12_00000096
	move.w $0058(a2),d0
	movea.l $0038(a2),a0
loc_12_0000008C:
	move.w #$FFFF,(a0)+
	subq.w #1,d0
	beq.b loc_12_000000BE
	bra.b loc_12_0000008C
loc_12_00000096:
	move.l $0038(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0002(a6),d0
	addq.l #1,d0
	bra.b loc_12_000000B2
loc_12_000000A6:
	move.l $000C(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0002(a6),d0
loc_12_000000B2:
	move.l d0,-(a7)
	jsr loc_30_00000000.l
	lea.l $000C(a7),a7
loc_12_000000BE:
	clr.l -(a7)
	moveq.l #0,d0
	move.w -$0002(a6),d0
	moveq.l #0,d1
	move.w $0056(a2),d1
	sub.l d1,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_000001E4.l
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #4096,d1
	lea.l $000C(a7),a7
	beq.b loc_12_000000FC
	moveq.l #0,d0
	move.w -$0002(a6),d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_00000168.l
	addq.l #8,a7
loc_12_000000FC:
	moveq.l #0,d1
	move.w $004E(a2),d1
	moveq.l #7,d0
	and.l d0,d1
	beq.b loc_12_00000128
	btst.b #2,$0071(a2)
	beq.b loc_12_00000128
	movea.l loc_1_00000000.l,a0
	cmpi.w #2,$0A64(a0)
	bne.b loc_12_00000128
	move.l a2,-(a7)
	jsr loc_24_00000056.l
	addq.l #4,a7
loc_12_00000128:
	pea.l -$000E(a6)
	move.w -$000C(a6),d0
	ext.l d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$000A(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0008(a6),d0
	move.l d0,-(a7)
	jsr loc_29_00000000.l
	move.l d0,d3
	move.w d3,-$0006(a6)
	lea.l $0010(a7),a7
loc_12_00000154:
	tst.w d4
	beq.b loc_12_00000180
	pea.l $0001.w
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	moveq.l #0,d1
	move.w d3,d1
	sub.l d1,d0
	move.l d0,-(a7)
	jsr loc_36_0000001A.l
	lea.l $0010(a7),a7
	bra.b loc_12_00000192
loc_12_00000180:
	tst.w d6
	beq.b loc_12_00000192
	pea.l $0001.w
	move.l a2,-(a7)
	jsr loc_34_00000000.l
	addq.l #8,a7
loc_12_00000192:
	move.l d2,-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,-(a7)
	jsr loc_20_000004D8.l
	tst.w d4
	lea.l $000C(a7),a7
	beq.b loc_12_000001B6
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	addq.l #4,a7
	bra.b loc_12_000001CC
loc_12_000001B6:
	tst.w d6
	beq.b loc_12_000001CC
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	move.l a2,-(a7)
	jsr loc_34_0000023C.l
	addq.l #8,a7
loc_12_000001CC:
	clr.l -(a7)
	move.l (a2),-(a7)
	addq.w #1,d5
	moveq.l #0,d0
	move.w d5,d0
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,-(a7)
	jsr loc_20_0000077C.l
	move.l d0,d0
	lea.l $000C(a7),a7
	bne.b loc_12_000001F0
	subq.w #1,d3
	bne.w loc_12_00000154
loc_12_000001F0:
	tst.l d0
	bne.b loc_12_00000200
	addq.w #1,-$0002(a6)
	subq.w #1,-$0004(a6)
	bne.w loc_12_0000005C
loc_12_00000200:
	tst.l d0
	bne.b loc_12_0000021A
	pea.l $0001.w
	move.l (a2),-(a7)
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,-(a7)
	jsr loc_20_0000077C.l
	lea.l $000C(a7),a7
loc_12_0000021A:
	movem.l -$0028(a6),d2-d6/a2
	unlk a6
	rts
    SECTION section_13,data
    SECTION section_14,code
loc_14_00000000:
	link a6,#-16
	movem.l d2-d6/a2,-(a7)
	movea.l $0008(a6),a2
	move.l $000C(a6),d2
	clr.w d5
	move.w $0056(a2),-$0002(a6)
	move.w $0064(a2),-$0008(a6)
	move.w $0066(a2),-$000A(a6)
	move.w $0068(a2),d0
	move.w d0,-$000C(a6)
	move.w d0,-$000E(a6)
	move.w $005A(a2),-$0004(a6)
	move.w $004E(a2),d4
	andi.w #2048,d4
	moveq.l #0,d6
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #1024,d1
	beq.b loc_14_0000005C
	movea.l loc_1_00000000.l,a0
	tst.w $0A64(a0)
	beq.b loc_14_0000005C
	moveq.l #1,d6
loc_14_0000005C:
	move.l a2,-(a7)
	jsr loc_20_000008A8.l
	tst.w d4
	addq.l #4,a7
	beq.b loc_14_000000A6
	move.l a2,-(a7)
	jsr loc_36_00000000.l
	cmpi.w #1,-$0004(a6)
	addq.l #4,a7
	bne.b loc_14_00000096
	btst.b #7,$0071(a2)
	bne.b loc_14_00000096
	move.w $0058(a2),d0
	movea.l $0038(a2),a0
loc_14_0000008C:
	move.w #$FFFF,(a0)+
	subq.w #1,d0
	beq.b loc_14_000000BE
	bra.b loc_14_0000008C
loc_14_00000096:
	move.l $0038(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0002(a6),d0
	addq.l #1,d0
	bra.b loc_14_000000B2
loc_14_000000A6:
	move.l $000C(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0002(a6),d0
loc_14_000000B2:
	move.l d0,-(a7)
	jsr loc_30_00000000.l
	lea.l $000C(a7),a7
loc_14_000000BE:
	clr.l -(a7)
	moveq.l #0,d0
	move.w -$0002(a6),d0
	moveq.l #0,d1
	move.w $0056(a2),d1
	sub.l d1,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_000001E4.l
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #4096,d1
	lea.l $000C(a7),a7
	beq.b loc_14_000000FC
	moveq.l #0,d0
	move.w -$0002(a6),d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_00000168.l
	addq.l #8,a7
loc_14_000000FC:
	clr.l -(a7)
	move.l a2,-(a7)
	jsr loc_20_0000037C.l
	moveq.l #0,d1
	move.w $004E(a2),d1
	moveq.l #7,d0
	and.l d0,d1
	addq.l #8,a7
	beq.b loc_14_00000134
	btst.b #2,$0071(a2)
	beq.b loc_14_00000134
	movea.l loc_1_00000000.l,a0
	cmpi.w #2,$0A64(a0)
	bne.b loc_14_00000134
	move.l a2,-(a7)
	jsr loc_24_00000056.l
	addq.l #4,a7
loc_14_00000134:
	pea.l -$000E(a6)
	move.w -$000C(a6),d0
	ext.l d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$000A(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0008(a6),d0
	move.l d0,-(a7)
	jsr loc_29_00000000.l
	move.l d0,d3
	move.w d3,-$0006(a6)
	lea.l $0010(a7),a7
loc_14_00000160:
	tst.w d4
	beq.b loc_14_0000018A
	clr.l -(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	moveq.l #0,d1
	move.w d3,d1
	sub.l d1,d0
	move.l d0,-(a7)
	jsr loc_36_0000001A.l
	lea.l $0010(a7),a7
	bra.b loc_14_0000019A
loc_14_0000018A:
	tst.w d6
	beq.b loc_14_0000019A
	clr.l -(a7)
	move.l a2,-(a7)
	jsr loc_34_00000000.l
	addq.l #8,a7
loc_14_0000019A:
	move.l d2,-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,-(a7)
	jsr loc_20_000004D8.l
	tst.w d4
	lea.l $000C(a7),a7
	beq.b loc_14_000001BE
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	addq.l #4,a7
	bra.b loc_14_000001D4
loc_14_000001BE:
	tst.w d6
	beq.b loc_14_000001D4
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	move.l a2,-(a7)
	jsr loc_34_0000023C.l
	addq.l #8,a7
loc_14_000001D4:
	clr.l -(a7)
	move.l (a2),-(a7)
	addq.w #1,d5
	moveq.l #0,d0
	move.w d5,d0
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,-(a7)
	jsr loc_20_0000077C.l
	move.l d0,d0
	lea.l $000C(a7),a7
	bne.b loc_14_000001F8
	subq.w #1,d3
	bne.w loc_14_00000160
loc_14_000001F8:
	tst.l d0
	bne.b loc_14_00000208
	addq.w #1,-$0002(a6)
	subq.w #1,-$0004(a6)
	bne.w loc_14_0000005C
loc_14_00000208:
	tst.l d0
	bne.b loc_14_00000222
	pea.l $0001.w
	move.l (a2),-(a7)
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,-(a7)
	jsr loc_20_0000077C.l
	lea.l $000C(a7),a7
loc_14_00000222:
	movem.l -$0028(a6),d2-d6/a2
	unlk a6
	rts
    SECTION section_15,data
    SECTION section_16,code
loc_16_00000000:
	link a6,#-16
	movem.l d2-d6/a2,-(a7)
	movea.l $0008(a6),a2
	move.l $000C(a6),d2
	clr.w -$0004(a6)
	move.w $0056(a2),d3
	move.w $0064(a2),-$0008(a6)
	move.w $0066(a2),-$000A(a6)
	move.w $0068(a2),d0
	move.w d0,-$000C(a6)
	move.w d0,-$000E(a6)
	move.w $005A(a2),d5
	move.w $004E(a2),d6
	andi.w #2048,d6
	moveq.l #0,d0
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #1024,d1
	beq.b loc_16_0000005A
	movea.l loc_1_00000000.l,a0
	tst.w $0A64(a0)
	beq.b loc_16_0000005A
	moveq.l #1,d0
loc_16_0000005A:
	move.w d0,-$0006(a6)
loc_16_0000005E:
	move.l a2,-(a7)
	jsr loc_20_000008A8.l
	tst.w d6
	addq.l #4,a7
	beq.b loc_16_000000A4
	move.l a2,-(a7)
	jsr loc_36_00000000.l
	cmpi.w #1,d5
	addq.l #4,a7
	bne.b loc_16_00000096
	btst.b #7,$0071(a2)
	bne.b loc_16_00000096
	move.w $0058(a2),d0
	movea.l $0038(a2),a0
loc_16_0000008C:
	move.w #$FFFF,(a0)+
	subq.w #1,d0
	beq.b loc_16_000000BA
	bra.b loc_16_0000008C
loc_16_00000096:
	move.l $0038(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d3,d0
	addq.l #1,d0
	bra.b loc_16_000000AE
loc_16_000000A4:
	move.l $000C(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d3,d0
loc_16_000000AE:
	move.l d0,-(a7)
	jsr loc_30_00000000.l
	lea.l $000C(a7),a7
loc_16_000000BA:
	clr.l -(a7)
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w $0056(a2),d1
	sub.l d1,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_000001E4.l
	addq.w #1,d3
	pea.l -$000E(a6)
	move.w -$000C(a6),d0
	ext.l d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$000A(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0008(a6),d0
	move.l d0,-(a7)
	jsr loc_29_00000000.l
	move.w d0,-$0002(a6)
	move.w -$0002(a6),d4
	lea.l $001C(a7),a7
	bra.b loc_16_00000136
loc_16_00000104:
	move.l $000C(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d3,d0
	move.l d0,-(a7)
	jsr loc_30_00000000.l
	pea.l $0001.w
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w $0056(a2),d1
	sub.l d1,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_000001E4.l
	addq.w #1,d3
	lea.l $0018(a7),a7
loc_16_00000136:
	subq.w #1,d4
	bne.b loc_16_00000104
	move.w -$0002(a6),d4
	moveq.l #0,d0
	move.w -$0002(a6),d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_16_00000266.l
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #4096,d1
	addq.l #8,a7
	beq.b loc_16_0000016E
	moveq.l #0,d0
	move.w d3,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_00000168.l
	addq.l #8,a7
loc_16_0000016E:
	moveq.l #0,d1
	move.w $004E(a2),d1
	moveq.l #7,d0
	and.l d0,d1
	beq.b loc_16_0000019A
	btst.b #2,$0071(a2)
	beq.b loc_16_0000019A
	movea.l loc_1_00000000.l,a0
	cmpi.w #2,$0A64(a0)
	bne.b loc_16_0000019A
	move.l a2,-(a7)
	jsr loc_24_00000056.l
	addq.l #4,a7
loc_16_0000019A:
	tst.w d6
	beq.b loc_16_000001C4
	pea.l $0001.w
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d4,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w d4,d0
	moveq.l #0,d1
	move.w -$0002(a6),d1
	sub.l d1,d0
	move.l d0,-(a7)
	jsr loc_36_0000001A.l
	lea.l $0010(a7),a7
	bra.b loc_16_000001D8
loc_16_000001C4:
	tst.w -$0006(a6)
	beq.b loc_16_000001D8
	pea.l $0001.w
	move.l a2,-(a7)
	jsr loc_34_00000000.l
	addq.l #8,a7
loc_16_000001D8:
	move.l d2,-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	jsr loc_20_000004D8.l
	tst.w d6
	lea.l $000C(a7),a7
	beq.b loc_16_000001FE
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	addq.l #4,a7
	bra.b loc_16_00000216
loc_16_000001FE:
	tst.w -$0006(a6)
	beq.b loc_16_00000216
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	move.l a2,-(a7)
	jsr loc_34_0000023C.l
	addq.l #8,a7
loc_16_00000216:
	clr.l -(a7)
	move.l (a2),-(a7)
	addq.w #1,-$0004(a6)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,-(a7)
	jsr loc_20_0000077C.l
	move.l d0,d0
	lea.l $000C(a7),a7
	bne.b loc_16_00000240
	sub.w -$0002(a6),d5
	bne.w loc_16_0000005E
loc_16_00000240:
	tst.l d0
	bne.b loc_16_0000025C
	pea.l $0001.w
	move.l (a2),-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	jsr loc_20_0000077C.l
	lea.l $000C(a7),a7
loc_16_0000025C:
	movem.l -$0028(a6),d2-d6/a2
	unlk a6
	rts
loc_16_00000266:
	movem.l d2-d4/a2,-(a7)
	movea.l $0014(a7),a0
	move.w $001A(a7),d2
	movea.l $0018(a0),a2
	move.w $0058(a0),d3
	move.w d2,d4
	lsr.w #1,d4
	moveq.l #0,d1
	move.w $0070(a0),d1
	moveq.l #3,d0
	and.l d0,d1
	cmp.l d1,d0
	beq.b loc_16_000002F8
loc_16_0000028C:
	moveq.l #0,d0
	move.b $0003(a2),d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d2,d1
	jsr loc_38_0000006C.l
	move.b d0,$0003(a2)
	moveq.l #0,d0
	move.b (a2),d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d2,d1
	jsr loc_38_0000006C.l
	move.b d0,(a2)
	moveq.l #0,d0
	move.b $0001(a2),d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d2,d1
	jsr loc_38_0000006C.l
	move.b d0,$0001(a2)
	moveq.l #0,d0
	move.b $0002(a2),d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d2,d1
	jsr loc_38_0000006C.l
	move.b d0,$0002(a2)
	addq.l #4,a2
	subq.w #1,d3
	beq.b loc_16_00000318
	bra.b loc_16_0000028C
loc_16_000002F8:
	moveq.l #0,d0
	move.b $0003(a2),d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d2,d1
	jsr loc_38_0000006C.l
	move.b d0,$0003(a2)
	addq.l #4,a2
	subq.w #1,d3
	bne.b loc_16_000002F8
loc_16_00000318:
	movem.l (a7)+,d2-d4/a2
	rts
	dc.b $00,$00
    SECTION section_17,data
    SECTION section_18,code
loc_18_00000000:
	link a6,#-12
	movem.l d2-d6/a2,-(a7)
	movea.l $0008(a6),a2
	move.l $000C(a6),d2
	clr.w d6
	move.w $0056(a2),d3
	move.w $0064(a2),-$0006(a6)
	move.w $0066(a2),-$0008(a6)
	move.w $0068(a2),d0
	move.w d0,-$000A(a6)
	move.w d0,-$000C(a6)
	move.w $005A(a2),d5
	moveq.l #0,d0
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #1024,d1
	beq.b loc_18_00000050
	movea.l loc_1_00000000.l,a0
	tst.w $0A64(a0)
	beq.b loc_18_00000050
	moveq.l #1,d0
loc_18_00000050:
	move.w d0,-$0004(a6)
	andi.w #63487,$004E(a2)
loc_18_0000005A:
	move.l a2,-(a7)
	jsr loc_20_000008A8.l
	move.l $000C(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d3,d0
	move.l d0,-(a7)
	jsr loc_30_00000000.l
	clr.l -(a7)
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w $0056(a2),d1
	sub.l d1,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_000001E4.l
	addq.w #1,d3
	pea.l -$000C(a6)
	move.w -$000A(a6),d0
	ext.l d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0008(a6),d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	move.l d0,-(a7)
	jsr loc_29_00000000.l
	move.w d0,-$0002(a6)
	move.w -$0002(a6),d4
	lea.l $002C(a7),a7
	bra.b loc_18_000000F0
loc_18_000000BE:
	move.l $000C(a2),-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d3,d0
	move.l d0,-(a7)
	jsr loc_30_00000000.l
	pea.l $0001.w
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w $0056(a2),d1
	sub.l d1,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_000001E4.l
	addq.w #1,d3
	lea.l $0018(a7),a7
loc_18_000000F0:
	subq.w #1,d4
	bne.b loc_18_000000BE
	moveq.l #0,d1
	move.w $004E(a2),d1
	andi.l #4096,d1
	beq.b loc_18_00000112
	moveq.l #0,d0
	move.w d3,d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_00000168.l
	addq.l #8,a7
loc_18_00000112:
	moveq.l #0,d0
	move.w -$0002(a6),d0
	move.l d0,-(a7)
	move.l a2,-(a7)
	jsr loc_20_0000037C.l
	moveq.l #0,d1
	move.w $004E(a2),d1
	moveq.l #7,d0
	and.l d0,d1
	addq.l #8,a7
	beq.b loc_18_00000150
	btst.b #2,$0071(a2)
	beq.b loc_18_00000150
	movea.l loc_1_00000000.l,a0
	cmpi.w #2,$0A64(a0)
	bne.b loc_18_00000150
	move.l a2,-(a7)
	jsr loc_24_00000056.l
	addq.l #4,a7
loc_18_00000150:
	tst.w -$0004(a6)
	beq.b loc_18_00000162
	clr.l -(a7)
	move.l a2,-(a7)
	jsr loc_34_00000000.l
	addq.l #8,a7
loc_18_00000162:
	move.l d2,-(a7)
	move.l a2,-(a7)
	moveq.l #0,d0
	move.w d6,d0
	move.l d0,-(a7)
	jsr loc_20_000004D8.l
	tst.w -$0004(a6)
	lea.l $000C(a7),a7
	beq.b loc_18_0000018E
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	move.l a2,-(a7)
	jsr loc_34_0000023C.l
	addq.l #8,a7
loc_18_0000018E:
	clr.l -(a7)
	move.l (a2),-(a7)
	addq.w #1,d6
	moveq.l #0,d0
	move.w d6,d0
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,-(a7)
	jsr loc_20_0000077C.l
	move.l d0,d0
	lea.l $000C(a7),a7
	bne.b loc_18_000001B4
	sub.w -$0002(a6),d5
	bne.w loc_18_0000005A
loc_18_000001B4:
	tst.l d0
	bne.b loc_18_000001CE
	pea.l $0001.w
	move.l (a2),-(a7)
	moveq.l #0,d0
	move.w d6,d0
	move.l d0,-(a7)
	jsr loc_20_0000077C.l
	lea.l $000C(a7),a7
loc_18_000001CE:
	movem.l -$0024(a6),d2-d6/a2
	unlk a6
	rts
    SECTION section_19,data
    SECTION section_20,code
loc_20_00000000:
	link a6,#-12
	movem.l d2-d7/a2-a4,-(a7)
	movea.l $0008(a6),a2
	movea.l $0014(a2),a4
	movea.l loc_1_00000004.l,a0
	btst.b #3,$0015(a0)
	beq.b loc_20_00000022
	moveq.l #0,d0
	bra.b loc_20_00000024
loc_20_00000022:
	moveq.l #15,d0
loc_20_00000024:
	move.l d0,-$0008(a6)
	movea.l loc_1_00000000.l,a0
	cmpi.w #1,$0A60(a0)
	bne.b loc_20_0000003A
	moveq.l #15,d0
	bra.b loc_20_0000003C
loc_20_0000003A:
	moveq.l #0,d0
loc_20_0000003C:
	move.l d0,d1
	eor.l d1,-$0008(a6)
	btst.b #3,$0071(a2)
	beq.b loc_20_00000066
	movea.l $0018(a2),a3
	move.w $0054(a2),d2
	move.w d2,d6
	sub.w $0058(a2),d6
	moveq.l #-1,d0
	move.w d0,-$0004(a6)
	move.w $0056(a2),-$0002(a6)
	bra.b loc_20_00000080
loc_20_00000066:
	movea.l $001C(a2),a3
	move.w $0056(a2),d2
	move.w $005A(a2),d6
	add.w d2,d6
	moveq.l #1,d0
	move.w d0,-$0004(a6)
	move.w $0054(a2),-$0002(a6)
loc_20_00000080:
	tst.w -$0002(a6)
	beq.w loc_20_0000013E
	bra.w loc_20_00000136
loc_20_0000008C:
	move.l (a4),-$000C(a6)
	move.l $0010(a2),d5
	moveq.l #0,d0
	move.w $0070(a2),d0
	moveq.l #16,d1
	and.l d1,d0
	move.l d0,-(a7)
	move.l $0008(a2),-(a7)
	move.l d5,-(a7)
	move.w -$0002(a6),d0
	ext.l d0
	move.l d0,-(a7)
	move.w d2,d0
	ext.l d0
	move.l d0,-(a7)
	clr.l -(a7)
	move.l $0004(a2),-(a7)
	jsr loc_27_00000076.l
	clr.w d4
	lea.l $001C(a7),a7
	bra.b loc_20_00000114
loc_20_000000C8:
	movea.l d5,a0
	addq.l #2,d5
	moveq.l #0,d0
	move.w (a0),d0
	move.l d0,d3
	moveq.l #16,d1
	cmp.l d0,d1
	ble.b loc_20_000000E6
	move.l d3,d0
	asl.l #2,d0
	movea.l d0,a0
	move.l $0(a0,a4.l),-$000C(a6)
	bra.b loc_20_00000112
loc_20_000000E6:
	move.l d3,d1
	moveq.l #15,d7
	and.l d7,d1
	move.l -$0008(a6),d0
	eor.l d0,d1
	moveq.l #32,d7
	movea.l d7,a0
	cmpa.l d3,a0
	ble.b loc_20_00000100
	move.b d1,-$000C(a6)
	bra.b loc_20_00000112
loc_20_00000100:
	moveq.l #48,d0
	movea.l d0,a0
	cmpa.l d3,a0
	ble.b loc_20_0000010E
	move.b d1,-$000A(a6)
	bra.b loc_20_00000112
loc_20_0000010E:
	move.b d1,-$000B(a6)
loc_20_00000112:
	addq.w #1,d4
loc_20_00000114:
	cmp.w -$0002(a6),d4
	blt.b loc_20_000000C8
	moveq.l #0,d0
	move.w $0070(a2),d0
	move.l d0,-(a7)
	pea.l -$000C(a6)
	jsr loc_20_000007F2.l
	move.l -$000C(a6),(a3)+
	add.w -$0004(a6),d2
	addq.l #8,a7
loc_20_00000136:
	cmp.w d6,d2
	beq.b loc_20_0000015E
	bra.w loc_20_0000008C
loc_20_0000013E:
	bra.b loc_20_0000015A
loc_20_00000140:
	move.l (a4),(a3)
	moveq.l #0,d0
	move.w $0070(a2),d0
	move.l d0,-(a7)
	pea.l (a3)
	jsr loc_20_000007F2.l
	addq.l #4,a3
	add.w -$0004(a6),d2
	addq.l #8,a7
loc_20_0000015A:
	cmp.w d6,d2
	bne.b loc_20_00000140
loc_20_0000015E:
	movem.l -$0030(a6),d2-d7/a2-a4
	unlk a6
	rts
loc_20_00000168:
	movem.l d2-d4,-(a7)
	movea.l $0010(a7),a0
	move.w $0016(a7),d2
	movea.l $0018(a0),a1
	move.w $0058(a0),d4
loc_20_0000017C:
	btst #0,d2
	beq.b loc_20_0000019E
	btst.b #3,$0001(a1)
	beq.b loc_20_0000018E
	moveq.l #2,d3
	bra.b loc_20_00000190
loc_20_0000018E:
	moveq.l #0,d3
loc_20_00000190:
	btst.b #0,(a1)
	beq.b loc_20_0000019A
	moveq.l #1,d0
	bra.b loc_20_0000019C
loc_20_0000019A:
	moveq.l #0,d0
loc_20_0000019C:
	bra.b loc_20_000001B8
loc_20_0000019E:
	btst.b #3,$0002(a1)
	beq.b loc_20_000001AA
	moveq.l #2,d3
	bra.b loc_20_000001AC
loc_20_000001AA:
	moveq.l #0,d3
loc_20_000001AC:
	btst.b #3,(a1)
	beq.b loc_20_000001B6
	moveq.l #1,d0
	bra.b loc_20_000001B8
loc_20_000001B6:
	moveq.l #0,d0
loc_20_000001B8:
	or.w d0,d3
	cmpi.w #1,d3
	bne.b loc_20_000001C8
	move.b #$6,$0003(a1)
	bra.b loc_20_000001D8
loc_20_000001C8:
	moveq.l #0,d0
	move.w d3,d0
	asl.l #2,d0
	moveq.l #0,d1
	move.w d3,d1
	add.l d1,d0
	move.b d0,$0003(a1)
loc_20_000001D8:
	addq.l #4,a1
	subq.w #1,d4
	bne.b loc_20_0000017C
	movem.l (a7)+,d2-d4
	rts
loc_20_000001E4:
	link a6,#-4
	movem.l d2-d6/a2-a4,-(a7)
	movea.l $0008(a6),a2
	move.w $000E(a6),d2
	move.l $0010(a6),d1
	move.l $0014(a2),d4
	move.w $0058(a2),d3
	movea.l $000C(a2),a3
	movea.l $0018(a2),a4
	movea.l loc_1_00000004.l,a0
	btst.b #3,$0015(a0)
	beq.b loc_20_0000021A
	moveq.l #0,d5
	bra.b loc_20_0000021C
loc_20_0000021A:
	moveq.l #15,d5
loc_20_0000021C:
	movea.l loc_1_00000000.l,a0
	cmpi.w #1,$0A60(a0)
	bne.b loc_20_0000022E
	moveq.l #15,d0
	bra.b loc_20_00000230
loc_20_0000022E:
	moveq.l #0,d0
loc_20_00000230:
	move.l d0,d6
	eor.l d6,d5
	btst.b #2,$0071(a2)
	beq.w loc_20_00000348
	btst.b #3,$0071(a2)
	bne.b loc_20_0000025A
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,d6
	asl.l #2,d6
	movea.l d6,a0
	move.l $001C(a2),d0
	move.l $0(a0,d0.l),-$0004(a6)
loc_20_0000025A:
	tst.l d1
	beq.w loc_20_000002D6
loc_20_00000260:
	btst.b #3,$0071(a2)
	beq.b loc_20_0000026C
	move.l (a4),-$0004(a6)
loc_20_0000026C:
	move.w (a3)+,d2
	cmpi.w #16,d2
	bcc.b loc_20_00000286
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,d1
	asl.l #2,d1
	movea.l d1,a0
	move.l $0(a0,d4.l),-$0004(a6)
	bra.b loc_20_000002C8
loc_20_00000286:
	move.w d2,d1
	andi.w #15,d1
	move.w d5,d0
	eor.w d0,d1
	move.w d2,d0
	lsr.w #4,d0
	cmpi.w #1,d0
	blt.b loc_20_000002B0
	ble.b loc_20_000002A4
	cmpi.w #2,d0
	bne.b loc_20_000002B0
	bra.b loc_20_000002AA
loc_20_000002A4:
	move.b d1,-$0004(a6)
	bra.b loc_20_000002B4
loc_20_000002AA:
	move.b d1,-$0002(a6)
	bra.b loc_20_000002B4
loc_20_000002B0:
	move.b d1,-$0003(a6)
loc_20_000002B4:
	moveq.l #0,d0
	move.w $0070(a2),d0
	move.l d0,-(a7)
	pea.l -$0004(a6)
	jsr loc_20_000007F2.l
	addq.l #8,a7
loc_20_000002C8:
	move.l -$0004(a6),d0
	add.l d0,(a4)+
	subq.w #1,d3
	beq.w loc_20_00000372
	bra.b loc_20_00000260
loc_20_000002D6:
	btst.b #3,$0071(a2)
	beq.b loc_20_000002E2
	move.l (a4),-$0004(a6)
loc_20_000002E2:
	move.w (a3)+,d2
	cmpi.w #16,d2
	bcc.b loc_20_000002FC
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,d1
	asl.l #2,d1
	movea.l d1,a0
	move.l $0(a0,d4.l),-$0004(a6)
	bra.b loc_20_0000033E
loc_20_000002FC:
	move.w d2,d1
	andi.w #15,d1
	move.w d5,d0
	eor.w d0,d1
	move.w d2,d0
	lsr.w #4,d0
	cmpi.w #1,d0
	blt.b loc_20_00000326
	ble.b loc_20_0000031A
	cmpi.w #2,d0
	bne.b loc_20_00000326
	bra.b loc_20_00000320
loc_20_0000031A:
	move.b d1,-$0004(a6)
	bra.b loc_20_0000032A
loc_20_00000320:
	move.b d1,-$0002(a6)
	bra.b loc_20_0000032A
loc_20_00000326:
	move.b d1,-$0003(a6)
loc_20_0000032A:
	moveq.l #0,d0
	move.w $0070(a2),d0
	move.l d0,-(a7)
	pea.l -$0004(a6)
	jsr loc_20_000007F2.l
	addq.l #8,a7
loc_20_0000033E:
	move.l -$0004(a6),(a4)+
	subq.w #1,d3
	beq.b loc_20_00000372
	bra.b loc_20_000002D6
loc_20_00000348:
	tst.l d1
	beq.b loc_20_00000360
loc_20_0000034C:
	moveq.l #0,d0
	move.w (a3)+,d0
	asl.l #2,d0
	movea.l d0,a1
	move.l $0(a1,d4.l),d0
	add.l d0,(a4)+
	subq.w #1,d3
	beq.b loc_20_00000372
	bra.b loc_20_0000034C
loc_20_00000360:
	moveq.l #0,d0
	move.w (a3)+,d0
	move.l d0,d1
	asl.l #2,d1
	movea.l d1,a0
	move.l $0(a0,d4.l),(a4)+
	subq.w #1,d3
	bne.b loc_20_00000360
loc_20_00000372:
	movem.l -$0024(a6),d2-d6/a2-a4
	unlk a6
	rts
loc_20_0000037C:
	link a6,#-12
	movem.l d2-d6/a2-a4,-(a7)
	movea.l $0008(a6),a2
	move.w $000E(a6),d2
	move.w $0058(a2),d6
	movea.l $0018(a2),a3
	movea.l a3,a4
	move.l $0028(a2),-$000C(a6)
	moveq.l #0,d0
	move.w $0070(a2),d0
	movea.l d0,a0
	moveq.l #3,d0
	move.l a0,d1
	and.l d0,d1
	movea.l d1,a0
	cmp.l a0,d0
	beq.w loc_20_00000476
loc_20_000003B2:
	clr.w d0
	move.w d0,-$0008(a6)
	move.w d0,-$0006(a6)
	move.w d0,d4
	move.w d4,-$0004(a6)
	movea.l -$000C(a6),a0
	addq.l #2,-$000C(a6)
	move.w (a0),-$0002(a6)
	move.w -$0002(a6),d3
loc_20_000003D2:
	moveq.l #0,d0
	move.b $0003(a3),d0
	add.w d0,d4
	moveq.l #0,d0
	move.b (a3),d0
	add.w d0,-$0004(a6)
	moveq.l #0,d0
	move.b $0001(a3),d0
	add.w d0,-$0006(a6)
	moveq.l #0,d0
	move.b $0002(a3),d0
	add.w d0,-$0008(a6)
	addq.l #4,a3
	subq.w #1,d3
	bne.b loc_20_000003D2
	move.w d2,d5
	add.w -$0002(a6),d5
	move.w d5,d3
	lsr.w #1,d3
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d5,d1
	jsr loc_38_0000006C.l
	move.b d0,$0003(a4)
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w -$0004(a6),d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d5,d1
	jsr loc_38_0000006C.l
	move.b d0,(a4)
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w -$0006(a6),d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d5,d1
	jsr loc_38_0000006C.l
	move.b d0,$0001(a4)
	moveq.l #0,d0
	move.w d3,d0
	moveq.l #0,d1
	move.w -$0008(a6),d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d5,d1
	jsr loc_38_0000006C.l
	move.b d0,$0002(a4)
	addq.l #4,a4
	sub.w -$0002(a6),d6
	beq.b loc_20_000004C4
	bra.w loc_20_000003B2
loc_20_00000476:
	clr.w d4
	movea.l -$000C(a6),a0
	addq.l #2,-$000C(a6)
	move.w (a0),-$0002(a6)
	move.w -$0002(a6),d3
loc_20_00000488:
	moveq.l #0,d0
	move.b $0003(a3),d0
	add.w d0,d4
	addq.l #4,a3
	subq.w #1,d3
	bne.b loc_20_00000488
	move.w d2,d5
	add.w -$0002(a6),d5
	moveq.l #0,d0
	move.w d5,d0
	lsr.l #1,d0
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,d0
	moveq.l #0,d1
	move.w d4,d1
	add.l d1,d0
	moveq.l #0,d1
	move.w d5,d1
	jsr loc_38_0000006C.l
	move.b d0,$0003(a4)
	addq.l #4,a4
	sub.w -$0002(a6),d6
	bne.b loc_20_00000476
loc_20_000004C4:
	move.l a2,-(a7)
	jsr loc_20_000008C6.l
	addq.l #4,a7
	movem.l -$002C(a6),d2-d6/a2-a4
	unlk a6
	rts
loc_20_000004D8:
	link a6,#-16
	movem.l d2-d6/a2-a4,-(a7)
	move.w $000A(a6),d2
	movea.l $000C(a6),a1
	move.l $0010(a6),d1
	movea.l (a1),a4
	movea.l loc_1_00000000.l,a0
	movea.l $005C(a0),a0
	cmpi.w #35,$0008(a0)
	bcs.b loc_20_00000518
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	move.l d1,-(a7)
	move.l a1,-(a7)
	jsr (a4)
	lea.l $0010(a7),a7
	bra.w loc_20_00000772
loc_20_00000518:
	moveq.l #0,d0
	move.w d2,d0
	movea.l d0,a0
	moveq.l #3,d0
	move.l a0,d4
	and.l d0,d4
	asl.l #2,d4
	movea.l d4,a0
	adda.l $0030(a1),a0
	move.l a0,-$0010(a6)
	movea.l $0028(a1),a2
	move.b $006D(a1),d1
	move.b d1,d3
	eori.b #15,d3
	move.w $006A(a1),-$0004(a6)
	move.w $0058(a1),-$000A(a6)
	movea.l $0018(a1),a3
	move.b $0071(a1),-$0007(a6)
	andi.b #2,-$0007(a6)
	moveq.l #0,d0
	move.w $0070(a1),d0
	movea.l d0,a0
	moveq.l #3,d0
	move.l a0,d4
	and.l d0,d4
	movea.l d4,a0
	cmp.l a0,d0
	bne.w loc_20_0000061A
	tst.b d1
	beq.b loc_20_000005BC
loc_20_00000574:
	move.w (a2)+,-$0006(a6)
	move.b $0003(a3),d4
	beq.b loc_20_000005A8
loc_20_0000057E:
	cmp.b d3,d4
	bls.b loc_20_0000059C
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	clr.l -(a7)
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_0000059C:
	addq.w #1,-$0004(a6)
	subq.w #1,-$0006(a6)
	beq.b loc_20_000005B0
	bra.b loc_20_0000057E
loc_20_000005A8:
	move.w -$0006(a6),d0
	add.w d0,-$0004(a6)
loc_20_000005B0:
	addq.l #4,a3
	subq.w #1,-$000A(a6)
	beq.w loc_20_00000772
	bra.b loc_20_00000574
loc_20_000005BC:
	move.w (a2)+,-$0006(a6)
	move.b $0003(a3),d4
	beq.b loc_20_00000606
loc_20_000005C6:
	moveq.l #0,d0
	move.w -$0004(a6),d0
	movea.l d0,a0
	moveq.l #3,d0
	move.l a0,d1
	and.l d0,d1
	movea.l d1,a0
	movea.l -$0010(a6),a1
	cmp.b $0(a0,a1.l),d4
	bls.b loc_20_000005FA
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	clr.l -(a7)
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_000005FA:
	addq.w #1,-$0004(a6)
	subq.w #1,-$0006(a6)
	beq.b loc_20_0000060E
	bra.b loc_20_000005C6
loc_20_00000606:
	move.w -$0006(a6),d0
	add.w d0,-$0004(a6)
loc_20_0000060E:
	addq.l #4,a3
	subq.w #1,-$000A(a6)
	beq.w loc_20_00000772
	bra.b loc_20_000005BC
loc_20_0000061A:
	tst.b d1
	beq.w loc_20_000006AC
loc_20_00000620:
	move.b (a3),d5
	move.b $0001(a3),d6
	move.b $0002(a3),-$0001(a6)
	move.w (a2)+,-$0006(a6)
loc_20_00000630:
	cmp.b d3,d5
	bls.b loc_20_00000650
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	pea.l $0001.w
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_00000650:
	cmp.b d3,d6
	bls.b loc_20_00000670
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	pea.l $0002.w
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_00000670:
	move.b -$0001(a6),d0
	cmp.b d3,d0
	bls.b loc_20_00000694
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	pea.l $0003.w
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_00000694:
	addq.w #1,-$0004(a6)
	subq.w #1,-$0006(a6)
	bne.b loc_20_00000630
	addq.l #4,a3
	subq.w #1,-$000A(a6)
	beq.w loc_20_00000772
	bra.w loc_20_00000620
loc_20_000006AC:
	move.b $0003(a3),d4
	move.b (a3),d5
	move.b $0001(a3),d6
	move.b $0002(a3),-$0001(a6)
	move.w (a2)+,-$0006(a6)
loc_20_000006C0:
	moveq.l #0,d0
	move.w -$0004(a6),d0
	movea.l d0,a0
	moveq.l #3,d0
	move.l a0,d1
	and.l d0,d1
	movea.l d1,a0
	movea.l -$0010(a6),a1
	move.b $0(a0,a1.l),d3
	tst.b -$0007(a6)
	beq.b loc_20_000006F8
	cmp.b d3,d4
	bls.b loc_20_000006F8
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	clr.l -(a7)
	bra.b loc_20_00000756
loc_20_000006F8:
	cmp.b d3,d5
	bls.b loc_20_00000718
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	pea.l $0001.w
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_00000718:
	cmp.b d3,d6
	bls.b loc_20_00000738
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	pea.l $0002.w
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_00000738:
	move.b -$0001(a6),d0
	cmp.b d3,d0
	bls.b loc_20_0000075C
	pea.l $0001.w
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w -$0004(a6),d0
	move.l d0,-(a7)
	pea.l $0003.w
loc_20_00000756:
	jsr (a4)
	lea.l $0010(a7),a7
loc_20_0000075C:
	addq.w #1,-$0004(a6)
	subq.w #1,-$0006(a6)
	bne.w loc_20_000006C0
	addq.l #4,a3
	subq.w #1,-$000A(a6)
	bne.w loc_20_000006AC
loc_20_00000772:
	movem.l -$0030(a6),d2-d6/a2-a4
	unlk a6
	rts
loc_20_0000077C:
	movem.l d2-d3/a2,-(a7)
	move.w $0012(a7),d2
	movea.l $0014(a7),a2
	move.l $0018(a7),d1
	moveq.l #0,d3
	moveq.l #0,d0
	move.w d2,d0
	movea.l loc_1_00000004.l,a0
	divu.w $0018(a0),d0
	swap.w d0
	andi.l #65535,d0
	move.w d0,d0
	bne.b loc_20_000007AC
	tst.l d1
	beq.b loc_20_000007B4
loc_20_000007AC:
	tst.w d0
	beq.b loc_20_000007EA
	tst.l d1
	beq.b loc_20_000007EA
loc_20_000007B4:
	tst.w d0
	bne.b loc_20_000007C2
	movea.l loc_1_00000004.l,a0
	move.w $0018(a0),d0
loc_20_000007C2:
	pea.l $0002.w
	moveq.l #0,d1
	move.w d0,d1
	move.l d1,-(a7)
	clr.l -(a7)
	clr.l -(a7)
	jsr (a2)
	move.l d0,d3
	lea.l $0010(a7),a7
	bne.b loc_20_000007EA
	pea.l $0003.w
	clr.l -(a7)
	clr.l -(a7)
	clr.l -(a7)
	jsr (a2)
	lea.l $0010(a7),a7
loc_20_000007EA:
	move.l d3,d0
	movem.l (a7)+,d2-d3/a2
	rts
loc_20_000007F2:
	move.l d2,-(a7)
	movea.l $0008(a7),a0
	movea.l loc_1_00000000.l,a1
	cmpi.w #2,$0A64(a1)
	beq.b loc_20_00000832
	moveq.l #0,d0
	move.b $0001(a0),d0
	muls.w #$96,d0
	moveq.l #0,d1
	move.b $0002(a0),d1
	muls.w #$4D,d1
	add.l d1,d0
	moveq.l #0,d1
	move.b (a0),d1
	muls.w #$1D,d1
	add.l d1,d0
	addi.l #128,d0
	asr.l #8,d0
	move.w d0,d2
	bra.b loc_20_0000085C
loc_20_00000832:
	moveq.l #0,d0
	move.b (a0),d0
	move.w d0,d2
	moveq.l #0,d0
	move.b $0001(a0),d0
	cmp.w d2,d0
	bcc.b loc_20_0000084A
	moveq.l #0,d0
	move.b $0001(a0),d0
	move.w d0,d2
loc_20_0000084A:
	moveq.l #0,d0
	move.b $0002(a0),d0
	cmp.w d2,d0
	bcc.b loc_20_0000085C
	moveq.l #0,d0
	move.b $0002(a0),d0
	move.w d0,d2
loc_20_0000085C:
	movea.l loc_1_00000000.l,a1
	btst.b #7,$0A71(a1)
	beq.b loc_20_0000087E
	move.w d2,d0
	lsr.w #2,d0
	move.w d0,d2
	moveq.l #0,d0
	move.w d2,d0
	asl.l #2,d0
	moveq.l #0,d1
	move.w d2,d1
	add.l d1,d0
	move.w d0,d2
loc_20_0000087E:
	move.b d2,$0003(a0)
	move.l (a7)+,d2
	rts
loc_20_00000886:
	movea.l $0004(a7),a0
	move.l $0028(a0),d0
	move.l $002C(a0),$0028(a0)
	move.l d0,$002C(a0)
	move.w $004A(a0),d0
	move.w $004C(a0),$004A(a0)
	move.w d0,$004C(a0)
	rts
loc_20_000008A8:
	movea.l $0004(a7),a0
	move.w $006E(a0),d0
	cmp.w $0058(a0),d0
	beq.b loc_20_000008C4
	move.w $006E(a0),$0058(a0)
	move.l a0,-(a7)
	jsr loc_20_00000886(pc)
	addq.l #4,a7
loc_20_000008C4:
	rts
loc_20_000008C6:
	movea.l $0004(a7),a0
	move.w $006E(a0),d0
	cmp.w $0058(a0),d0
	bne.b loc_20_000008EC
	move.l $005C(a0),d0
	moveq.l #0,d1
	move.w $006A(a0),d1
	sub.l d1,d0
	move.w d0,$0058(a0)
	move.l a0,-(a7)
	jsr loc_20_00000886(pc)
	addq.l #4,a7
loc_20_000008EC:
	rts
loc_20_000008EE:
	movea.l $0004(a7),a0
	move.l $0018(a0),d0
	move.l $0020(a0),$0018(a0)
	move.l d0,$0020(a0)
	rts
	dc.b $00,$00
    SECTION section_21,data
    SECTION section_22,code
loc_22_00000000:
	movem.l d2-d4/a2-a5,-(a7)
	move.l $0020(a7),d0
	movea.l $0024(a7),a3
	movea.l $0028(a7),a2
	movea.l #loc_41_00000018,a4
	move.b d0,d2
	cmpi.b #8,d0
	bne.b loc_22_00000020
	clr.b d2
loc_22_00000020:
	move.l $0008(a2),d4
	beq.b loc_22_0000006C
	movea.l d4,a0
	move.l $0004(a0),d3
	beq.b loc_22_00000062
	movea.l d3,a0
	move.l $0008(a0),d1
	beq.b loc_22_0000004C
	moveq.l #0,d0
	movea.l d3,a5
	move.b $0005(a5),d0
	andi.w #255,d0
	mulu.w (a5),d0
	move.l d0,-(a7)
	move.l d1,-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_0000004C:
	moveq.l #0,d0
	movea.l d3,a5
	move.b $0005(a5),d0
	asl.l #2,d0
	moveq.l #40,d1
	add.l d1,d0
	move.l d0,-(a7)
	move.l d3,-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_00000062:
	pea.l $0064.w
	move.l d4,-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_0000006C:
	tst.l $0014(a2)
	beq.b loc_22_00000082
	moveq.l #0,d0
	move.w $0040(a2),d0
	move.l d0,-(a7)
	move.l $0014(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_00000082:
	tst.l $000C(a2)
	beq.b loc_22_00000098
	moveq.l #0,d0
	move.w $003C(a2),d0
	move.l d0,-(a7)
	move.l $000C(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_00000098:
	tst.l $0034(a2)
	beq.b loc_22_000000AE
	moveq.l #0,d0
	move.w $003C(a2),d0
	move.l d0,-(a7)
	move.l $0034(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_000000AE:
	tst.l $0038(a2)
	beq.b loc_22_000000C4
	moveq.l #0,d0
	move.w $003C(a2),d0
	move.l d0,-(a7)
	move.l $0038(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_000000C4:
	tst.l $0020(a2)
	beq.b loc_22_000000DA
	moveq.l #0,d0
	move.w $0046(a2),d0
	move.l d0,-(a7)
	move.l $0020(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_000000DA:
	tst.l $0024(a2)
	beq.b loc_22_000000F0
	moveq.l #0,d0
	move.w $0048(a2),d0
	move.l d0,-(a7)
	move.l $0024(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_000000F0:
	tst.l $0018(a2)
	beq.b loc_22_00000106
	moveq.l #0,d0
	move.w $0042(a2),d0
	move.l d0,-(a7)
	move.l $0018(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_00000106:
	tst.l $001C(a2)
	beq.b loc_22_0000011C
	moveq.l #0,d0
	move.w $0044(a2),d0
	move.l d0,-(a7)
	move.l $001C(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_0000011C:
	tst.l $0010(a2)
	beq.b loc_22_00000132
	moveq.l #0,d0
	move.w $003E(a2),d0
	move.l d0,-(a7)
	move.l $0010(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_00000132:
	tst.l $0028(a2)
	beq.b loc_22_00000148
	moveq.l #0,d0
	move.w $004A(a2),d0
	move.l d0,-(a7)
	move.l $0028(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_00000148:
	tst.l $002C(a2)
	beq.b loc_22_0000015E
	moveq.l #0,d0
	move.w $004C(a2),d0
	move.l d0,-(a7)
	move.l $002C(a2),-(a7)
	jsr (a4)
	addq.l #8,a7
loc_22_0000015E:
	btst.b #5,$0071(a2)
	beq.b loc_22_00000180
	pea.l $0004.w
	clr.l -(a7)
	move.l $0050(a2),-(a7)
	move.b d2,d0
	ext.w d0
	ext.l d0
	move.l d0,-(a7)
	movea.l (a2),a0
	jsr (a0)
	lea.l $0010(a7),a7
loc_22_00000180:
	move.b d2,$001F(a3)
	move.b d2,d0
	ext.w d0
	ext.l d0
	movem.l (a7)+,d2-d4/a2-a5
	rts
    SECTION section_23,data
    SECTION section_24,code
loc_24_00000000:
	movea.l $0004(a7),a1
	movea.l loc_1_00000004.l,a0
	btst.b #3,$0015(a0)
	beq.b loc_24_00000032
	moveq.l #1,d1
	movea.l $0004(a1),a0
	movea.l $0004(a0),a0
	move.b $0005(a0),d0
	asl.l d0,d1
	move.l d1,-(a7)
	move.l $0014(a1),-(a7)
	move.l a1,-(a7)
	jsr loc_24_00000168.l
	bra.b loc_24_00000050
loc_24_00000032:
	moveq.l #1,d1
	movea.l $0004(a1),a0
	movea.l $0004(a0),a0
	move.b $0005(a0),d0
	asl.l d0,d1
	move.l d1,-(a7)
	move.l $0014(a1),-(a7)
	move.l a1,-(a7)
	jsr loc_24_00000098.l
loc_24_00000050:
	lea.l $000C(a7),a7
	rts
loc_24_00000056:
	movea.l $0004(a7),a0
	movea.l loc_1_00000004.l,a1
	btst.b #3,$0015(a1)
	beq.b loc_24_0000007E
	moveq.l #0,d0
	move.w $0058(a0),d0
	move.l d0,-(a7)
	move.l $0018(a0),-(a7)
	move.l a0,-(a7)
	jsr loc_24_00000168.l
	bra.b loc_24_00000092
loc_24_0000007E:
	moveq.l #0,d0
	move.w $0058(a0),d0
	move.l d0,-(a7)
	move.l $0018(a0),-(a7)
	move.l a0,-(a7)
	jsr loc_24_00000098.l
loc_24_00000092:
	lea.l $000C(a7),a7
	rts
loc_24_00000098:
	link a6,#-4
	movem.l d2-d6,-(a7)
	movea.l $0008(a6),a1
	movea.l $000C(a6),a0
	move.l $0010(a6),d2
	btst.b #0,$004F(a1)
	beq.b loc_24_000000B8
	moveq.l #1,d6
	bra.b loc_24_000000BA
loc_24_000000B8:
	moveq.l #0,d6
loc_24_000000BA:
	btst.b #1,$004F(a1)
	beq.b loc_24_000000C6
	moveq.l #1,d0
	bra.b loc_24_000000C8
loc_24_000000C6:
	moveq.l #0,d0
loc_24_000000C8:
	move.w d0,-$0002(a6)
	btst.b #2,$004F(a1)
	beq.b loc_24_000000D8
	moveq.l #1,d0
	bra.b loc_24_000000DA
loc_24_000000D8:
	moveq.l #0,d0
loc_24_000000DA:
	move.w d0,-$0004(a6)
loc_24_000000DE:
	moveq.l #0,d0
	move.b $0003(a0),d0
	move.w d0,d5
	moveq.l #0,d0
	move.b (a0),d0
	moveq.l #0,d1
	move.w d5,d1
	sub.l d1,d0
	lsr.l #1,d0
	move.w d0,d3
	moveq.l #0,d0
	move.b $0001(a0),d0
	moveq.l #0,d1
	move.w d5,d1
	sub.l d1,d0
	lsr.l #1,d0
	move.w d0,d4
	moveq.l #0,d0
	move.b $0002(a0),d0
	moveq.l #0,d1
	move.w d5,d1
	sub.l d1,d0
	lsr.l #1,d0
	move.w d0,d1
	tst.w d6
	beq.b loc_24_00000128
	cmp.w d4,d3
	bcc.b loc_24_00000122
	moveq.l #0,d0
	move.w d3,d0
	bra.b loc_24_00000126
loc_24_00000122:
	moveq.l #0,d0
	move.w d4,d0
loc_24_00000126:
	sub.b d0,(a0)
loc_24_00000128:
	tst.w -$0002(a6)
	beq.b loc_24_00000140
	cmp.w d3,d1
	bcc.b loc_24_00000138
	moveq.l #0,d0
	move.w d1,d0
	bra.b loc_24_0000013C
loc_24_00000138:
	moveq.l #0,d0
	move.w d3,d0
loc_24_0000013C:
	sub.b d0,$0002(a0)
loc_24_00000140:
	tst.w -$0004(a6)
	beq.b loc_24_00000158
	cmp.w d1,d4
	bcc.b loc_24_00000150
	moveq.l #0,d0
	move.w d4,d0
	bra.b loc_24_00000154
loc_24_00000150:
	moveq.l #0,d0
	move.w d1,d0
loc_24_00000154:
	sub.b d0,$0001(a0)
loc_24_00000158:
	addq.l #4,a0
	subq.l #1,d2
	bne.b loc_24_000000DE
	movem.l -$0018(a6),d2-d6
	unlk a6
	rts
loc_24_00000168:
	link a6,#-4
	movem.l d2-d6,-(a7)
	movea.l $0008(a6),a1
	movea.l $000C(a6),a0
	move.l $0010(a6),d1
	btst.b #0,$004F(a1)
	beq.b loc_24_00000188
	moveq.l #1,d5
	bra.b loc_24_0000018A
loc_24_00000188:
	moveq.l #0,d5
loc_24_0000018A:
	btst.b #1,$004F(a1)
	beq.b loc_24_00000196
	moveq.l #1,d6
	bra.b loc_24_00000198
loc_24_00000196:
	moveq.l #0,d6
loc_24_00000198:
	btst.b #2,$004F(a1)
	beq.b loc_24_000001A4
	moveq.l #1,d0
	bra.b loc_24_000001A6
loc_24_000001A4:
	moveq.l #0,d0
loc_24_000001A6:
	move.w d0,-$0002(a6)
loc_24_000001AA:
	moveq.l #0,d0
	move.b $0002(a0),d0
	move.w d0,d2
	moveq.l #0,d0
	move.b $0001(a0),d0
	move.w d0,d3
	moveq.l #0,d0
	move.b (a0),d0
	move.w d0,d4
	tst.w d5
	beq.b loc_24_000001E2
	cmp.w d3,d2
	bls.b loc_24_000001E2
	cmp.w d4,d2
	bls.b loc_24_000001E2
	cmp.w d4,d3
	bls.b loc_24_000001D6
	moveq.l #0,d0
	move.w d3,d0
	bra.b loc_24_000001DA
loc_24_000001D6:
	moveq.l #0,d0
	move.w d4,d0
loc_24_000001DA:
	sub.w d0,d2
	move.w d2,d0
	lsr.w #1,d0
	add.b d0,(a0)
loc_24_000001E2:
	tst.w d6
	beq.b loc_24_00000206
	cmp.w d2,d3
	bls.b loc_24_00000206
	cmp.w d4,d3
	bls.b loc_24_00000206
	cmp.w d4,d2
	bls.b loc_24_000001F8
	moveq.l #0,d0
	move.w d2,d0
	bra.b loc_24_000001FC
loc_24_000001F8:
	moveq.l #0,d0
	move.w d4,d0
loc_24_000001FC:
	sub.w d0,d3
	move.w d3,d0
	lsr.w #1,d0
	add.b d0,$0002(a0)
loc_24_00000206:
	tst.w -$0002(a6)
	beq.b loc_24_0000022C
	cmp.w d2,d4
	bls.b loc_24_0000022C
	cmp.w d3,d4
	bls.b loc_24_0000022C
	cmp.w d3,d2
	bls.b loc_24_0000021E
	moveq.l #0,d0
	move.w d2,d0
	bra.b loc_24_00000222
loc_24_0000021E:
	moveq.l #0,d0
	move.w d3,d0
loc_24_00000222:
	sub.w d0,d4
	move.w d4,d0
	lsr.w #1,d0
	add.b d0,$0001(a0)
loc_24_0000022C:
	addq.l #4,a0
	subq.l #1,d1
	bne.w loc_24_000001AA
	movem.l -$0018(a6),d2-d6
	unlk a6
	rts
	dc.b $00,$00
    SECTION section_25,data
    SECTION section_26,code
    SECTION section_27,code
	dc.b $48,$E7,$38,$22,$2C,$79
	dc.l loc_1_00000014
	dc.b $20,$6F,$00,$18,$4C,$EF,$00,$0F,$00,$1C,$24,$6F,$00,$2C,$22,$6F
	dc.b $00,$30,$28,$2F,$00,$34,$4E,$B9
	dc.l loc_27_0000002C
	dc.b $4C,$DF,$44,$1C,$4E,$75
loc_27_0000002C:
	dc.b $48,$E7,$3F,$38,$94,$40,$48,$C2,$52,$82,$6F,$36,$2E,$00,$2A,$01
	dc.b $96,$41,$48,$C3,$52,$83,$6F,$2A,$26,$48,$28,$49,$7C,$00,$60,$16
	dc.b $20,$4B,$20,$07,$22,$05,$22,$4C,$4E,$B9
	dc.l loc_27_000000A2
	dc.b $52,$85,$D5,$C2,$D5,$C2,$DC,$82,$51,$CB,$FF,$E8,$20,$06,$4C,$DF
	dc.b $1C,$FC,$4E,$75,$70,$FF,$4C,$DF,$1C,$FC,$4E,$75
loc_27_00000076:
	movem.l d2-d4/a2/a6,-(a7)
	movea.l loc_1_00000014.l,a6
	movea.l $0018(a7),a0
	movem.l $001C(a7),d0-d2
	movea.l $0028(a7),a2
	movea.l $002C(a7),a1
	move.l $0030(a7),d4
	jsr loc_27_000000A2.l
	movem.l (a7)+,d2-d4/a2/a6
	rts
loc_27_000000A2:
	movem.l d2-d6/a2-a3,-(a7)
	tst.w d4
	beq.w loc_27_000000BC
	movem.l a0-a1,-(a7)
	bsr.w loc_27_00000248
	movem.l (a7)+,a0-a1
	move.l d2,d4
	bra.b loc_27_000000F8
loc_27_000000BC:
	movem.l d0-d1/a0-a1,-(a7)
	movea.l $0004(a1),a1
	clr.l d0
	move.w $0000(a1),d0
	clr.l d1
	move.b $0005(a1),d1
	mulu.w d1,d0
	lea.l $0008(a1),a1
	movea.l (a1),a1
	clr.l d1
	jsr -$012C(a6)
	movem.l (a7)+,d0-d1/a0-a1
	move.l d2,d4
	moveq.l #1,d5
	move.l #$C0,d6
	moveq.l #0,d2
	moveq.l #0,d3
	move.l a1,-(a7)
	jsr -$0228(a6)
	movea.l (a7)+,a1
loc_27_000000F8:
	movea.l $0004(a1),a1
	clr.l d1
	move.b $0005(a1),d1
	subq.b #1,d1
	lsl.b #2,d1
	lea.l $0008(a1),a0
	addi.w #15,d4
	lsr.w #4,d4
	subq.w #1,d4
	move.l d4,d2
	movea.l $0(a0,d1.w),a1
	movea.l a2,a3
	clr.l d5
loc_27_0000011C:
	move.w (a1)+,d5
	beq.w loc_27_000001AA
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
	moveq.l #0,d3
	roxl.w #1,d5
	addx.w d3,d3
	move.w d3,(a3)+
loc_27_000001A2:
	dbf.w d2,loc_27_0000011C
	bra.w loc_27_00000230
loc_27_000001AA:
	move.l d5,(a3)+
	move.l d5,(a3)+
	move.l d5,(a3)+
	move.l d5,(a3)+
	move.l d5,(a3)+
	move.l d5,(a3)+
	move.l d5,(a3)+
	move.l d5,(a3)+
	bra.b loc_27_000001A2
loc_27_000001BC:
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	lsl (a3)+
	bra.w loc_27_0000022C
loc_27_000001E0:
	move.l d4,d2
	movea.l $0(a0,d1.w),a1
	movea.l a2,a3
loc_27_000001E8:
	move.w (a1)+,d5
	beq.b loc_27_000001BC
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
	roxl.w #1,d5
	roxl (a3)+
loc_27_0000022C:
	dbf.w d2,loc_27_000001E8
loc_27_00000230:
	subq.b #4,d1
	bge.b loc_27_000001E0
	movem.l (a7)+,d2-d6/a2-a3
	rts
	dc.b $2F,$02,$4C,$EF,$03,$07,$00,$08,$61,$04,$24,$1F,$4E,$75
loc_27_00000248:
	movem.l d2-d5/a2-a3,-(a7)
	movea.l $0000(a0),a2
	cmpa.l #$0,a2
	beq.w loc_27_00000262
	add.w $0010(a2),d0
	add.w $0012(a2),d1
loc_27_00000262:
	movea.l $0004(a0),a0
	mulu.w $0000(a0),d1
	moveq.l #7,d3
	and.w d0,d3
	lsr.w #3,d0
	add.l d1,d0
	clr.w d1
	move.b $0005(a0),d1
	lea.l $0008(a0),a0
	movea.l $0004(a1),a1
	lea.l $0008(a1),a1
	addq.w #7,d2
	lsr.w #3,d2
	bra.b loc_27_000002AE
loc_27_0000028A:
	movea.l (a0)+,a2
	adda.l d0,a2
	movea.l (a1)+,a3
	move.w d2,d4
	bra.b loc_27_00000296
loc_27_00000294:
	move.b (a2)+,(a3)+
loc_27_00000296:
	dbf.w d4,loc_27_00000294
	move.w d3,d5
	bra.b loc_27_000002AA
loc_27_0000029E:
	movea.l a3,a2
	move.w d2,d4
	bra.b loc_27_000002A6
loc_27_000002A4:
	roxl -(a2)
loc_27_000002A6:
	dbf.w d4,loc_27_000002A4
loc_27_000002AA:
	dbf.w d5,loc_27_0000029E
loc_27_000002AE:
	dbf.w d1,loc_27_0000028A
	movem.l (a7)+,d2-d5/a2-a3
	rts
    SECTION section_28,code
    SECTION section_29,code
loc_29_00000000:
	move.l $0004(a7),d0
	movea.l $0010(a7),a0
	move.l $0008(a7),d1
	sub.w d1,(a0)
	bgt.b loc_29_00000018
	addq.w #1,d0
	move.l $000C(a7),d1
	add.w d1,(a0)
loc_29_00000018:
	rts
	dc.b $00,$00
    SECTION section_30,code
loc_30_00000000:
	movem.l d2-d6/a2-a3,-(a7)
	move.w $0022(a7),d2
	movea.l $0024(a7),a3
	movea.l $0028(a7),a2
	btst.b #3,$0071(a3)
	beq.b loc_30_00000050
	move.l $0004(a3),d6
	move.w $0054(a3),d3
	move.w $0058(a3),d4
loc_30_00000024:
	move.w d3,d0
	ext.l d0
	subq.w #1,d3
	ext.l d0
	move.l d0,-(a7)
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	move.l d6,-(a7)
	jsr loc_42_00000000.l
	move.w d0,(a2)
	lea.l $000C(a7),a7
	bge.b loc_30_00000046
	clr.w (a2)
loc_30_00000046:
	addq.l #2,a2
	subq.w #1,d4
	beq.w loc_30_000000EA
	bra.b loc_30_00000024
loc_30_00000050:
	btst.b #6,$0071(a3)
	beq.b loc_30_0000008E
	move.l $0004(a3),d6
	move.w $0054(a3),d3
	move.w $0058(a3),d4
loc_30_00000064:
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	move.w d3,d0
	ext.l d0
	addq.w #1,d3
	ext.l d0
	move.l d0,-(a7)
	move.l d6,-(a7)
	jsr loc_42_00000000.l
	move.w d0,(a2)
	lea.l $000C(a7),a7
	bge.b loc_30_00000086
	clr.w (a2)
loc_30_00000086:
	addq.l #2,a2
	subq.w #1,d4
	beq.b loc_30_000000EA
	bra.b loc_30_00000064
loc_30_0000008E:
	move.l $0004(a3),d6
	move.w $0054(a3),d3
	move.w $0058(a3),d5
loc_30_0000009A:
	cmpi.w #1008,d5
	bge.b loc_30_000000A6
	move.w d5,d4
	ext.l d4
	bra.b loc_30_000000AC
loc_30_000000A6:
	move.l #$3F0,d4
loc_30_000000AC:
	moveq.l #0,d0
	move.w $0070(a3),d0
	moveq.l #16,d1
	and.l d1,d0
	move.l d0,-(a7)
	move.l $0008(a3),-(a7)
	move.l a2,-(a7)
	ext.l d4
	move.l d4,-(a7)
	moveq.l #0,d0
	move.w d2,d0
	move.l d0,-(a7)
	move.w d3,d0
	ext.l d0
	move.l d0,-(a7)
	move.l d6,-(a7)
	jsr loc_27_00000076.l
	subi.w #1008,d5
	addi.w #1008,d3
	lea.l $07E0(a2),a2
	tst.w d5
	lea.l $001C(a7),a7
	bgt.b loc_30_0000009A
loc_30_000000EA:
	movem.l (a7)+,d2-d6/a2-a3
	rts
    SECTION section_31,data
    SECTION section_32,code
loc_32_00000000:
	link a6,#-84
	movem.l a2-a3,-(a7)
	movea.l $0008(a6),a2
	movea.l #loc_1_00000000,a1
	movea.l $0028(a2),a3
	movea.l (a1),a0
	tst.b $09B9(a0)
	bne.b loc_32_0000004C
	movea.l (a1),a0
	lea.l $006C(a0),a0
	lea.l -$0054(a6),a1
	moveq.l #14,d0
loc_32_0000002A:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_32_0000002A
	move.w (a0)+,(a1)+
	move.w #$9,-$0038(a6)
	pea.l -$0054(a6)
	jsr loc_41_00000030.l
	move.b -$0020(a6),(a3)+
	clr.b (a3)
	moveq.l #1,d0
	bra.b loc_32_0000008C
loc_32_0000004C:
	movea.l (a1),a0
	lea.l $006C(a0),a0
	lea.l -$0054(a6),a1
	moveq.l #19,d0
loc_32_00000058:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_32_00000058
	move.w (a0)+,(a1)+
	move.w #$9,-$0038(a6)
	pea.l -$0054(a6)
	jsr loc_41_00000030.l
	move.b -$0003(a6),d0
	andi.b #255,d0
	move.b d0,(a3)+
	moveq.l #0,d0
	move.w -$0004(a6),d0
	andi.l #65280,d0
	asr.l #8,d0
	move.b d0,(a3)
	moveq.l #2,d0
loc_32_0000008C:
	move.l d0,$0020(a2)
	addq.l #4,a7
	movem.l -$005C(a6),a2-a3
	unlk a6
	rts
    SECTION section_33,data
    SECTION section_34,code
loc_34_00000000:
	link a6,#-16
	movem.l d2-d6/a2-a4,-(a7)
	movea.l $0008(a6),a2
	move.l $000C(a6),d2
	tst.l d2
	beq.b loc_34_0000001E
	move.l a2,-(a7)
	jsr loc_20_000008A8.l
	addq.l #4,a7
loc_34_0000001E:
	move.l $0028(a2),-$000C(a6)
	move.w $0058(a2),-$0010(a6)
	move.l $0018(a2),-$0008(a6)
	movea.l $0020(a2),a3
	movea.l $0024(a2),a4
	moveq.l #7,d0
	move.b d0,-$0003(a6)
	movea.l loc_1_00000000.l,a0
	cmpi.w #2,$0A64(a0)
	bne.w loc_34_000001A0
loc_34_0000004E:
	movea.l -$000C(a6),a0
	move.w (a0)+,-$000E(a6)
	move.l a0,-$000C(a6)
loc_34_0000005A:
	movea.l -$0008(a6),a0
	move.b (a0),d3
	move.b (a3),d1
	ext.w d1
	ext.l d1
	addq.l #4,d1
	move.l d1,d0
	divs.w #$8,d0
	add.b d0,d3
	move.b $0001(a0),d5
	move.b $0001(a3),d1
	ext.w d1
	ext.l d1
	addq.l #4,d1
	move.l d1,d0
	divs.w #$8,d0
	add.b d0,d5
	move.b $0002(a0),d6
	move.b $0002(a3),d1
	ext.w d1
	ext.l d1
	addq.l #4,d1
	move.l d1,d0
	divs.w #$8,d0
	add.b d0,d6
	cmp.b -$0003(a6),d3
	ble.b loc_34_000000BC
	move.b #$F,(a3)
	move.b d3,d0
	ext.w d0
	ext.l d0
	moveq.l #15,d1
	sub.l d1,d0
	add.l d0,d0
	move.b d0,d4
	add.b d4,d3
	subi.b #15,d3
	bra.b loc_34_000000CA
loc_34_000000BC:
	clr.b (a3)
	move.b d3,d0
	ext.w d0
	ext.l d0
	add.l d0,d0
	move.b d0,d4
	add.b d4,d3
loc_34_000000CA:
	cmp.b -$0003(a6),d5
	ble.b loc_34_000000F0
	move.b #$F,$0001(a3)
	move.b d5,d0
	ext.w d0
	ext.l d0
	moveq.l #15,d1
	sub.l d1,d0
	add.l d0,d0
	move.b d0,-$0001(a6)
	add.b -$0001(a6),d5
	subi.b #15,d5
	bra.b loc_34_00000104
loc_34_000000F0:
	clr.b $0001(a3)
	move.b d5,d0
	ext.w d0
	ext.l d0
	add.l d0,d0
	move.b d0,-$0001(a6)
	add.b -$0001(a6),d5
loc_34_00000104:
	cmp.b -$0003(a6),d6
	ble.b loc_34_0000012A
	move.b #$F,$0002(a3)
	move.b d6,d0
	ext.w d0
	ext.l d0
	moveq.l #15,d1
	sub.l d1,d0
	add.l d0,d0
	move.b d0,-$0002(a6)
	add.b -$0002(a6),d6
	subi.b #15,d6
	bra.b loc_34_0000013E
loc_34_0000012A:
	clr.b $0002(a3)
	move.b d6,d0
	ext.w d0
	ext.l d0
	add.l d0,d0
	move.b d0,-$0002(a6)
	add.b -$0002(a6),d6
loc_34_0000013E:
	moveq.l #0,d0
	move.w $0070(a2),d0
	move.l d0,-(a7)
	move.l a3,-(a7)
	jsr loc_20_000007F2.l
	move.b d3,d0
	add.b d0,(a4)
	move.b d5,d0
	add.b d0,$0001(a4)
	move.b d6,d0
	add.b d0,$0002(a4)
	addq.l #4,a4
	move.b d4,d0
	add.b d0,(a4)
	move.b -$0001(a6),d0
	add.b d0,$0001(a4)
	move.b -$0002(a6),d0
	add.b d0,$0002(a4)
	addq.l #4,a3
	move.b d3,d0
	add.b d0,(a3)
	move.b d5,d0
	add.b d0,$0001(a3)
	move.b d6,d0
	add.b d0,$0002(a3)
	subq.w #1,-$000E(a6)
	addq.l #8,a7
	bne.w loc_34_0000005A
	addq.l #4,-$0008(a6)
	subq.w #1,-$0010(a6)
	beq.w loc_34_0000021A
	bra.w loc_34_0000004E
loc_34_000001A0:
	movea.l -$000C(a6),a0
	move.w (a0)+,-$000E(a6)
	move.l a0,-$000C(a6)
loc_34_000001AC:
	move.b $0003(a3),d1
	ext.w d1
	ext.l d1
	addq.l #4,d1
	move.l d1,d0
	divs.w #$8,d0
	move.b d0,d3
	movea.l -$0008(a6),a0
	add.b $0003(a0),d3
	cmp.b -$0003(a6),d3
	ble.b loc_34_000001E8
	move.b #$F,$0003(a3)
	move.b d3,d0
	ext.w d0
	ext.l d0
	moveq.l #15,d1
	sub.l d1,d0
	add.l d0,d0
	move.b d0,d4
	add.b d4,d3
	subi.b #15,d3
	bra.b loc_34_000001F8
loc_34_000001E8:
	clr.b $0003(a3)
	move.b d3,d0
	ext.w d0
	ext.l d0
	add.l d0,d0
	move.b d0,d4
	add.b d4,d3
loc_34_000001F8:
	move.b d3,d0
	add.b d0,$0003(a4)
	addq.l #4,a4
	move.b d4,$0003(a4)
	addq.l #4,a3
	add.b d0,$0003(a3)
	subq.w #1,-$000E(a6)
	bne.b loc_34_000001AC
	addq.l #4,-$0008(a6)
	subq.w #1,-$0010(a6)
	bne.b loc_34_000001A0
loc_34_0000021A:
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	tst.l d2
	addq.l #4,a7
	beq.b loc_34_00000232
	move.l a2,-(a7)
	jsr loc_20_000008C6.l
	addq.l #4,a7
loc_34_00000232:
	movem.l -$0030(a6),d2-d6/a2-a4
	unlk a6
	rts
loc_34_0000023C:
	movea.l $0004(a7),a0
	move.l $0024(a0),d0
	move.l $0020(a0),$0024(a0)
	move.l d0,$0020(a0)
	movea.l $0024(a0),a0
	clr.l (a0)
	rts
	dc.b $00,$00
    SECTION section_35,data
    SECTION section_36,code
loc_36_00000000:
	movea.l $0004(a7),a0
	move.l $0034(a0),d0
	move.l $000C(a0),$0034(a0)
	move.l $0038(a0),$000C(a0)
	move.l d0,$0038(a0)
	rts
loc_36_0000001A:
	link a6,#-40
	movem.l d2-d7/a2-a4,-(a7)
	move.w $000A(a6),d2
	move.w $000E(a6),d3
	movea.l $0010(a6),a2
	tst.l $0014(a6)
	beq.b loc_36_0000003E
	move.l a2,-(a7)
	jsr loc_20_000008A8.l
	addq.l #4,a7
loc_36_0000003E:
	move.l $000C(a2),-$0010(a6)
	move.l $0034(a2),d6
	move.l $0038(a2),-$0004(a6)
	movea.l $0018(a2),a4
	movea.l $0020(a2),a3
	move.w $0058(a2),-$0022(a6)
	move.l $0028(a2),-$0014(a6)
	movea.l -$0014(a6),a0
	move.w (a0)+,d5
	move.l a0,-$0014(a6)
loc_36_0000006C:
	move.l (a4),(a3)+
	subq.w #1,d5
	bne.b loc_36_0000006C
	addq.l #2,-$0010(a6)
	addq.l #2,d6
	addq.l #2,-$0004(a6)
	addq.l #4,a4
	subq.w #2,-$0022(a6)
loc_36_00000082:
	movea.l d6,a1
	move.w (a1),-$0008(a6)
	movea.l -$0004(a6),a1
	move.w (a1),-$000A(a6)
	movea.l -$0010(a6),a1
	move.w -$0002(a1),-$0016(a6)
	movea.l -$0010(a6),a1
	move.w $0002(a1),-$0018(a6)
	movea.l d6,a1
	move.w -$0002(a1),-$001A(a6)
	move.w $0002(a1),-$001C(a6)
	movea.l -$0004(a6),a1
	move.w -$0002(a1),-$001E(a6)
	movea.l -$0004(a6),a1
	move.w $0002(a1),-$0020(a6)
	movea.l -$0014(a6),a0
	addq.l #2,-$0014(a6)
	move.w (a0),d4
	move.w d4,d5
loc_36_000000D2:
	move.l (a4),(a3)+
	subq.w #1,d4
	bne.b loc_36_000000D2
	move.w d5,-$000C(a6)
	subq.w #1,-$000C(a6)
	move.w d3,-$0006(a6)
	subq.w #1,-$0006(a6)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	mulu.w -$000C(a6),d0
	lsr.l #1,d0
	move.w d0,-$0024(a6)
	moveq.l #0,d0
	move.w -$0006(a6),d0
	mulu.w -$000C(a6),d0
	move.l d0,d1
	add.l d0,d0
	add.l d1,d0
	lsr.l #1,d0
	move.w d0,-$0026(a6)
	move.w -$0006(a6),d0
	lsr.w #1,d0
	tst.w -$0006(a6)
	beq.w loc_36_000002E0
	cmp.w d0,d2
	bhi.w loc_36_00000206
	cmpi.w #1,-$0006(a6)
	bls.w loc_36_00000206
	move.w -$0016(a6),d0
	cmp.w -$0008(a6),d0
	bne.b loc_36_00000194
	move.w -$001C(a6),d0
	cmp.w -$0008(a6),d0
	bne.b loc_36_0000014A
	move.w -$001E(a6),d0
	cmp.w -$0008(a6),d0
	beq.b loc_36_00000194
loc_36_0000014A:
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	suba.l a0,a3
	moveq.l #0,d0
	move.w -$0024(a6),d0
	moveq.l #0,d1
	move.w -$000C(a6),d1
	mulu.w d2,d1
	sub.l d1,d0
	moveq.l #0,d1
	move.w -$0006(a6),d1
	jsr loc_38_0000006C.l
	move.w d0,d1
	move.w d1,d4
	bra.b loc_36_0000017C
loc_36_00000178:
	move.l -$0004(a4),(a3)+
loc_36_0000017C:
	move.w d1,d0
	subq.w #1,d1
	tst.w d0
	bne.b loc_36_00000178
	move.w d5,d1
	sub.w d4,d1
	moveq.l #0,d0
	move.w d1,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	adda.l a0,a3
loc_36_00000194:
	move.w -$0018(a6),d0
	cmp.w -$0008(a6),d0
	bne.w loc_36_000002E0
	move.w -$001A(a6),d0
	cmp.w -$0008(a6),d0
	bne.b loc_36_000001B6
	move.w -$0020(a6),d0
	cmp.w -$0008(a6),d0
	beq.w loc_36_000002E0
loc_36_000001B6:
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	suba.l a0,a3
	moveq.l #0,d0
	move.w -$000C(a6),d0
	mulu.w d2,d0
	moveq.l #0,d1
	move.w -$0024(a6),d1
	add.l d1,d0
	moveq.l #0,d1
	move.w -$0006(a6),d1
	jsr loc_38_0000006C.l
	addq.l #1,d0
	move.w d0,d1
	move.w d1,d4
	moveq.l #0,d0
	move.w d1,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	adda.l a0,a3
	move.w d5,d1
	sub.w d4,d1
	bra.b loc_36_000001FA
loc_36_000001F6:
	move.l $0004(a4),(a3)+
loc_36_000001FA:
	move.w d1,d0
	subq.w #1,d1
	tst.w d0
	beq.w loc_36_000002E0
	bra.b loc_36_000001F6
loc_36_00000206:
	cmp.w d0,d2
	bls.w loc_36_000002E0
	move.w -$0016(a6),d0
	cmp.w -$000A(a6),d0
	bne.b loc_36_00000276
	move.w -$0020(a6),d0
	cmp.w -$000A(a6),d0
	bne.b loc_36_0000022A
	move.w -$001A(a6),d0
	cmp.w -$000A(a6),d0
	beq.b loc_36_00000276
loc_36_0000022A:
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	suba.l a0,a3
	moveq.l #0,d0
	move.w -$000C(a6),d0
	mulu.w d2,d0
	moveq.l #0,d1
	move.w -$0024(a6),d1
	neg.l d1
	add.l d1,d0
	moveq.l #0,d1
	move.w -$0006(a6),d1
	jsr loc_38_0000006C.l
	move.w d0,d1
	move.w d1,d4
	bra.b loc_36_0000025E
loc_36_0000025A:
	move.l -$0004(a4),(a3)+
loc_36_0000025E:
	move.w d1,d0
	subq.w #1,d1
	tst.w d0
	bne.b loc_36_0000025A
	move.w d5,d1
	sub.w d4,d1
	moveq.l #0,d0
	move.w d1,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	adda.l a0,a3
loc_36_00000276:
	move.w -$0018(a6),d0
	cmp.w -$000A(a6),d0
	bne.b loc_36_000002E0
	move.w -$001E(a6),d0
	cmp.w -$000A(a6),d0
	bne.b loc_36_00000294
	move.w -$001C(a6),d0
	cmp.w -$000A(a6),d0
	beq.b loc_36_000002E0
loc_36_00000294:
	moveq.l #0,d0
	move.w d5,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	suba.l a0,a3
	moveq.l #0,d0
	move.w -$0026(a6),d0
	moveq.l #0,d1
	move.w -$000C(a6),d1
	mulu.w d2,d1
	sub.l d1,d0
	moveq.l #0,d1
	move.w -$0006(a6),d1
	jsr loc_38_0000006C.l
	addq.l #1,d0
	move.w d0,d1
	move.w d1,d4
	moveq.l #0,d0
	move.w d1,d0
	move.l d0,d7
	asl.l #2,d7
	movea.l d7,a0
	adda.l a0,a3
	move.w d5,d1
	sub.w d4,d1
	bra.b loc_36_000002D8
loc_36_000002D4:
	move.l $0004(a4),(a3)+
loc_36_000002D8:
	move.w d1,d0
	subq.w #1,d1
	tst.w d0
	bne.b loc_36_000002D4
loc_36_000002E0:
	addq.l #2,-$0010(a6)
	addq.l #2,d6
	addq.l #2,-$0004(a6)
	addq.l #4,a4
	subq.w #1,-$0022(a6)
	bne.w loc_36_00000082
	movea.l -$0014(a6),a0
	move.w (a0)+,d5
	move.l a0,-$0014(a6)
loc_36_000002FE:
	move.l (a4),(a3)+
	subq.w #1,d5
	bne.b loc_36_000002FE
	move.l a2,-(a7)
	jsr loc_20_000008EE.l
	tst.l $0014(a6)
	addq.l #4,a7
	beq.b loc_36_0000031E
	move.l a2,-(a7)
	jsr loc_20_000008C6.l
	addq.l #4,a7
loc_36_0000031E:
	movem.l -$004C(a6),d2-d7/a2-a4
	unlk a6
	rts
    SECTION section_37,data
    SECTION section_38,code
loc_38_00000000:
	cmpi.l #65535,d2
	bgt.b loc_38_00000020
	movea.w d1,a1
	clr.w d1
	swap.w d1
	divu.w d2,d1
	move.l d1,d0
	swap.w d1
	move.w a1,d0
	divu.w d2,d0
	move.w d0,d1
	clr.w d0
	swap.w d0
	rts
loc_38_00000020:
	move.l d1,d0
	clr.w d0
	swap.w d0
	swap.w d1
	clr.w d1
	movea.l d2,a1
	moveq.l #15,d2
loc_38_0000002E:
	add.l d1,d1
	addx.l d0,d0
	cmpa.l d0,a1
	bgt.b loc_38_0000003A
	sub.l a1,d0
	addq.w #1,d1
loc_38_0000003A:
	dbf.w d2,loc_38_0000002E
	rts
loc_38_00000040:
	move.l d2,-(a7)
	move.l d0,d2
	mulu.w d1,d2
	movea.l d2,a0
	move.l d0,d2
	swap.w d2
	mulu.w d1,d2
	swap.w d1
	mulu.w d1,d0
	add.l d2,d0
	swap.w d0
	clr.w d0
	adda.l d0,a0
	move.l a0,d0
	move.l (a7)+,d2
	rts
loc_38_00000060:
	move.l d2,-(a7)
	move.l d1,d2
	move.l d0,d1
	bsr.b loc_38_00000000
	move.l (a7)+,d2
	rts
loc_38_0000006C:
	move.l d2,-(a7)
	move.l d1,d2
	move.l d0,d1
	bsr.b loc_38_00000000
	move.l d1,d0
	move.l (a7)+,d2
	rts
loc_38_0000007A:
	move.l d2,-(a7)
	move.l d1,d2
	bge.b loc_38_00000082
	neg.l d2
loc_38_00000082:
	move.l d0,d1
	moveq.l #0,d0
	tst.l d1
	bge.b loc_38_0000008E
	neg.l d1
	not.l d0
loc_38_0000008E:
	movea.l d0,a0
	bsr.w loc_38_00000000
	move.w a0,d2
	beq.b loc_38_0000009A
	neg.l d0
loc_38_0000009A:
	move.l (a7)+,d2
	rts
loc_38_0000009E:
	move.l d2,-(a7)
	movea.l d0,a0
	moveq.l #0,d0
	move.l d1,d2
	bge.b loc_38_000000AC
	neg.l d2
	not.l d0
loc_38_000000AC:
	move.l a0,d1
	bge.b loc_38_000000B4
	neg.l d1
	not.l d0
loc_38_000000B4:
	movea.l d0,a0
	bsr.w loc_38_00000000
	move.l a0,d2
	beq.b loc_38_000000C0
	neg.l d1
loc_38_000000C0:
	move.l d1,d0
	move.l (a7)+,d2
	rts
	dc.b $00,$00
    SECTION section_39,code
    SECTION section_40,code
loc_40_00000000:
	movem.l d2/a6,-(a7)
	movea.l loc_1_00000010.l,a6
	movem.l $000C(a7),d1-d2
	jsr -$0054(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_40_0000001C:
	move.l a6,-(a7)
	movea.l loc_1_00000010.l,a6
	move.l $0008(a7),d1
	jsr -$005A(a6)
	movea.l (a7)+,a6
	rts
loc_40_00000030:
	move.l a6,-(a7)
	movea.l loc_1_00000010.l,a6
	move.l $0008(a7),d1
	jsr -$007E(a6)
	movea.l (a7)+,a6
	rts
loc_40_00000044:
	move.l a6,-(a7)
	movea.l loc_1_00000010.l,a6
	move.l $0008(a7),d1
	jsr -$0096(a6)
	movea.l (a7)+,a6
	rts
loc_40_00000058:
	move.l a6,-(a7)
	movea.l loc_1_00000010.l,a6
	move.l $0008(a7),d1
	jsr -$009C(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_41,code
loc_41_00000000:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	movem.l $0008(a7),d0-d1
	jsr -$00C6(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_41_00000018:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	movea.l $0008(a7),a1
	move.l $000C(a7),d0
	jsr -$00D2(a6)
	movea.l (a7)+,a6
	rts
loc_41_00000030:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	movea.l $0008(a7),a1
	jsr -$01C8(a6)
	movea.l (a7)+,a6
	rts
loc_41_00000044:
	move.l a6,-(a7)
	movea.l loc_1_0000000C.l,a6
	movea.l $0008(a7),a1
	jsr -$0216(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_42,code
loc_42_00000000:
	move.l a6,-(a7)
	movea.l loc_1_00000014.l,a6
	movea.l $0008(a7),a1
	movem.l $000C(a7),d0-d1
	jsr -$013E(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_42_0000001C:
	move.l a6,-(a7)
	movea.l loc_1_00000014.l,a6
	movea.l $0008(a7),a0
	move.l $000C(a7),d0
	jsr -$0246(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_43,code
loc_43_00000000:
	move.l a6,-(a7)
	movea.l loc_1_00000018.l,a6
	movea.l $0008(a7),a0
	move.l $000C(a7),d0
	jsr -$0084(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_44,data
    SECTION section_45,data
