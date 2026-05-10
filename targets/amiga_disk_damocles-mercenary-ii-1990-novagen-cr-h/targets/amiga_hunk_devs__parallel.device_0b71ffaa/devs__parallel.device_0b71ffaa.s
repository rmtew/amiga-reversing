    INCLUDE "exec/devices.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"
    INCLUDE "hardware/cia.i"

    RSSET LIB_SIZE
    RS.B 56
app_005A RS.L 1
    RS.B 12
app_006A RS.L 1
    RS.B 7
app_0075 RS.B 1
app_0076 RS.B 1
app_SIZEOF EQU __RS

_ciab	EQU	$BFD000
_ciaa	EQU	$BFE001

    SECTION section_0,code
	dc.b $70,$FF,$4E,$75
resident:	; STRUCT RT
    ; invalid overlap: decoded code at $0004 starts at structured data; emitted as data
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l loc_0_000004CE	; APTR RT_ENDSKIP
	dc.b RTF_COLDSTART	; UBYTE RT_FLAGS = RTF_COLDSTART
	dc.b $22	; UBYTE RT_VERSION
	dc.b NT_DEVICE	; UBYTE RT_TYPE = NT_DEVICE
	dc.b $3C	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_init	; APTR RT_INIT
resident_idstring:
    ; invalid overlap: decoded code at $001E starts at structured data; emitted as data
	dc.b "parallel 34.9 (18 Apr 1988)",$0D,$0A,$00	; string
resident_name:
    ; invalid overlap: decoded code at $003C starts at structured data; emitted as data
	dc.b "parallel.device",$00	; string
loc_0_0000004C:
	dc.b "misc.resource",$00	; string
loc_0_0000005A:
	dc.b "ciaa.resource",$00	; string
resident_vectors:
	dc.b $FF,$FF
	dc.w $0012
	dc.w $007A
	dc.w $020E
	dc.w $0010
	dc.w $00A8
	dc.w $01A6
	dc.w $FFFF
    ; KNOWN: base A6=parallel.device:LIB
parallel_device_lib_extfunc:
	rts
    ; KNOWN: base A6=parallel.device:LIB
parallel_device_lib_open:
	clr.b $001F(a1)
	tst.w $0020(a6)
	beq.b loc_0_0000009E
	btst.b #5,app_0075(a6)
	beq.b loc_0_00000094
	btst.b #5,$0035(a1)
	bne.b loc_0_000000B0
loc_0_00000094:
	move.b #$1,$001F(a1)
	bra.w loc_0_0000010C
loc_0_0000009E:
	clr.b app_0076(a6)
	btst.b #5,$0035(a1)
	beq.b loc_0_000000B0
	bset.b #5,app_0075(a6)
loc_0_000000B0:
	tst.b $001F(a1)
	bne.b loc_0_000000C0
	tst.b $0020(a6)
	bne.b loc_0_000000C0
	addq.w #1,$0020(a6)
loc_0_000000C0:
	move.b app_0075(a6),$0035(a1)
	bset.b #4,app_0076(a6)
	btst.b #1,$0035(a1)
	beq.b loc_0_000000E0
	move.l app_005A(a6),$0036(a1)
	move.l $005E(a6),$003A(a1)
loc_0_000000E0:
	rts
    ; KNOWN: base A6=parallel.device:LIB
parallel_device_lib_close:
	clr.b $001F(a1)
	tst.w $0020(a6)
	beq.b loc_0_0000010C
	subq.w #1,$0020(a6)
	bne.b loc_0_0000010C
	clr.w $0072(a6)
	clr.l $0026(a6)
	bclr.b #5,app_0075(a6)
	btst.b #0,app_0076(a6)
	beq.b loc_0_0000010C
	jsr -$0012(a6)
loc_0_0000010C:
	moveq.l #0,d0
	rts
    ; KNOWN: base A6=parallel.device:LIB
parallel_device_dev_beginio:
	clr.b $001F(a1)
	moveq.l #16,d0
	move.l a1,-(a7)
	move.l a6,-(a7)
	movea.l $0022(a6),a6
	jsr -$0012(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	move.b #$5,$0008(a1)
	move.w $001C(a1),d0
	cmpi.w #10,d0
	bgt.w loc_0_00000206
	lsl.w #2,d0
	lea.l loc_0_000001DA(pc),a0
	movea.l $0(a0,d0.w),a0
	jsr (a0)
	move.b #$51,d1
	and.b $001E(a1),d1
	bne.w loc_0_0000015C
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_0000015C:
	cmpi.w #2,$001C(a1)
	bne.b loc_0_00000184
	btst.b #4,app_0076(a6)
	beq.b loc_0_000001BC
	ori.b #1,_ciab+ciaddra.l
	bclr.b #CIAB_PRTRBUSY,_ciab+ciapra.l
	bclr.b #4,app_0076(a6)
	bra.b loc_0_000001BC
loc_0_00000184:
	cmpi.w #3,$001C(a1)
	bne.b loc_0_000001C2
	bclr.b #0,_ciab+ciaddra.l
	btst.b #CIAB_PRTRBUSY,_ciab+ciapra.l
	bne.b loc_0_000001BC
	btst.b #2,app_0076(a6)
	bne.b loc_0_000001C2
	move.l #$90,d0
	move.l a1,-(a7)
	move.l a6,-(a7)
	movea.l $0022(a6),a6
	jsr -$0018(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
loc_0_000001BC:
	bset.b #2,app_0076(a6)
loc_0_000001C2:
	move.l #$90,d0
loc_0_000001C8:
	move.l a1,-(a7)
	move.l a6,-(a7)
	movea.l $0022(a6),a6
	jsr -$0012(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	rts
loc_0_000001DA:
	dc.l loc_0_00000206	; pointer_table
	dc.l loc_0_000002D8
	dc.l loc_0_000004D0
	dc.l loc_0_000004D0
	dc.l loc_0_00000206
	dc.l loc_0_000002E8
	dc.l loc_0_000002EA
	dc.l loc_0_00000306
	dc.l loc_0_00000308
	dc.l loc_0_0000034C
	dc.l loc_0_0000038C
loc_0_00000206:
	move.b #$FD,$001F(a1)
	rts
    ; KNOWN: base A6=parallel.device:LIB
parallel_device_dev_abortio:
	moveq.l #16,d0
	bsr.b loc_0_000001C8
	cmpa.l $0026(a6),a1
	bne.b loc_0_0000021E
	clr.l $0026(a6)
	bra.b loc_0_0000024A
loc_0_0000021E:
	btst.b #6,$001E(a1)
	beq.w loc_0_00000270
	move.l a1,-(a7)
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	movea.l (a7)+,a1
	subq.w #1,$0072(a6)
	bne.b loc_0_0000024A
	tst.l $0026(a6)
	bne.b loc_0_0000024A
	bclr.b #2,app_0076(a6)
loc_0_0000024A:
	move.b #$FE,$001F(a1)
	bset.b #5,$001E(a1)
	andi.b #175,$001E(a1)
	btst.b #0,$001E(a1)
	bne.b loc_0_00000270
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
loc_0_00000270:
	bsr.w loc_0_000001C2
	rts
    ; KNOWN: base A6=parallel.device:LIB
parallel_device_lib_expunge:
	moveq.l #0,d0
	tst.w $0020(a6)
	beq.b loc_0_00000280
	rts
loc_0_00000280:
	moveq.l #4,d0
	lea.l $0036(a6),a1
	move.l a6,-(a7)
	movea.l $0022(a6),a6
	jsr -$000C(a6)
	movea.l (a7)+,a6
	move.l a6,-(a7)
	movea.l app_006A(a6),a6
	moveq.l #3,d0
	jsr -$000C(a6)
	moveq.l #2,d0
	jsr -$000C(a6)
	movea.l (a7)+,a6
	movea.l a6,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	move.l $0062(a6),-(a7)
	movea.l a6,a1
	moveq.l #0,d0
	move.w $0010(a6),d0
	suba.l d0,a1
	add.w $0012(a6),d0
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$00D2(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d0
	rts
	dc.b $00,$00
loc_0_000002D8:
	bsr.b loc_0_00000308
	move.l $0026(a6),d0
	beq.b loc_0_000002E6
	movea.l d0,a1
	bsr.w parallel_device_dev_abortio
loc_0_000002E6:
	rts
loc_0_000002E8:
	rts
loc_0_000002EA:
	moveq.l #16,d0
	bsr.w loc_0_000001C8
	bclr.b #0,$001E(a1)
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d1
	rts
loc_0_00000306:
	rts
loc_0_00000308:
	move.l a1,-(a7)
	lea.l $004C(a6),a0
loc_0_0000030E:
	movea.l (a0),a1
	move.l (a1),d0
	beq.b loc_0_0000031C
	move.l d0,(a0)
	exg d0,a1
	move.l a0,$0004(a1)
loc_0_0000031C:
	tst.l d0
	beq.w loc_0_0000032A
	movea.l d0,a1
	bsr.w loc_0_00000330
	bra.b loc_0_0000030E
loc_0_0000032A:
	clr.w $0072(a6)
	rts
loc_0_00000330:
	bset.b #5,$001E(a1)
	move.b #$FE,$001F(a1)
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$017A(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a1
	rts
loc_0_0000034C:
	moveq.l #16,d0
	bsr.w loc_0_000001C8
	move.b _ciab+ciaddra.l,d1
	andi.b #7,d1
	andi.b #248,_ciab+ciaddra.l
	move.b _ciab+ciapra.l,d0
	andi.b #7,d0
	andi.b #248,$0074(a6)
	or.b d0,$0074(a6)
	move.b $0074(a6),$0034(a1)
	or.b d1,_ciab+ciaddra.l
	bsr.w loc_0_000001C2
	rts
	dc.b $00,$00
loc_0_0000038C:
	btst.b #2,app_0076(a6)
	beq.b loc_0_0000039C
	move.b #$1,$001F(a1)
	bra.b loc_0_000003B6
loc_0_0000039C:
	move.b $0035(a1),app_0075(a6)
	btst.b #1,app_0075(a6)
	beq.b loc_0_000003B6
	move.l $0036(a1),app_005A(a6)
	move.l $003A(a1),$005E(a6)
loc_0_000003B6:
	rts
loc_0_000003B8:
	dc.b $E0,$00,$00,$08,$03,$00,$C0,$00,$00,$0A
	dc.l resident_name
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$22,$D0,$00,$00,$16
	dc.b $00,$09,$00,$00,$00,$00
resident_init:
	movem.l a0/a2,-(a7)
	lea.l resident_vectors(pc),a0
	lea.l loc_0_000003B8(pc),a1
	suba.l a2,a2
	move.l #$77,d0
	move.l a6,-(a7)
	movea.l a6,a6
	jsr -$0054(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,a0/a2
	tst.l d0
	beq.w loc_0_000004C8
	move.l a6,d1
	move.l a6,-(a7)
	movea.l d0,a6
	move.l a0,$0062(a6)
	move.l d1,$0032(a6)
	lea.l loc_0_0000004C(pc),a1
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$01F2(a6)
	movea.l (a7)+,a6
	move.l d0,app_006A(a6)
	beq.w loc_0_000004CA
	lea.l resident_name(pc),a1
	move.l a6,-(a7)
	movea.l app_006A(a6),a6
	moveq.l #2,d0
	jsr -$0006(a6)
	tst.l d0
	bne.w loc_0_0000044A
	moveq.l #3,d0
	lea.l resident_name(pc),a1
	jsr -$0006(a6)
loc_0_0000044A:
	movea.l (a7)+,a6
	tst.l d0
	bne.w loc_0_000004CA
	lea.l $004C(a6),a0
	move.b #$5,$000C(a0)
	move.l a0,(a0)
	addq.l #4,(a0)
	clr.l $0004(a0)
	move.l a0,$0008(a0)
	movea.l a6,a1
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$01B0(a6)
	movea.l (a7)+,a6
	lea.l loc_0_0000005A(pc),a1
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0032(a6),a6
	jsr -$01F2(a6)
	movea.l (a7)+,a6
	move.l d0,$0022(a6)
	lea.l $0036(a6),a1
	move.l #resident_name,$000A(a1)
	move.b #$2,$0008(a1)
	move.l a6,$000E(a1)
	move.l #loc_0_00000590,$0012(a1)
	moveq.l #4,d0
	move.l a6,-(a7)
	movea.l $0022(a6),a6
	jsr -$0006(a6)
	movea.l (a7)+,a6
	moveq.l #16,d0
	move.l a6,-(a7)
	movea.l $0022(a6),a6
	jsr -$0012(a6)
	movea.l (a7)+,a6
	movea.l (a7)+,a6
loc_0_000004C8:
	rts
loc_0_000004CA:
	clr.l d0
	bra.b loc_0_000004C8
loc_0_000004CE:
	dc.b $00,$00
loc_0_000004D0:
	tst.l $0024(a1)
	bne.b loc_0_000004DC
	clr.l $0020(a1)
	rts
loc_0_000004DC:
	exg a5,a6
	bclr.b #0,$001E(a1)
	btst.b #2,$0076(a5)
	beq.b loc_0_00000514
	bset.b #6,$001E(a1)
	lea.l $004C(a5),a0
	lea.l $0004(a0),a0
	move.l $0004(a0),d0
	move.l a1,$0004(a0)
	move.l a0,(a1)
	move.l d0,$0004(a1)
	movea.l d0,a0
	move.l a1,(a0)
	addq.w #1,$0072(a5)
	exg a5,a6
	rts
loc_0_00000514:
	bsr.b loc_0_0000051A
	exg a5,a6
	rts
loc_0_0000051A:
	bclr.b #6,$001E(a1)
	bset.b #4,$001E(a1)
	move.l $0028(a1),$002A(a5)
	clr.l $002E(a5)
	move.l a1,$0026(a5)
	tst.l $0024(a1)
	bpl.b loc_0_00000540
	bset.b #3,$0076(a5)
loc_0_00000540:
	move.b #$0,d0
	bclr.b #3,$0074(a5)
	beq.b loc_0_00000552
	bset.b #4,$0076(a5)
loc_0_00000552:
	cmpi.w #2,$001C(a1)
	beq.b loc_0_00000564
	bset.b #3,$0074(a5)
	move.b #$FF,d0
loc_0_00000564:
	move.b d0,_ciaa+ciaddrb.l
	rts
	dc.b $4A,$6D,$00,$72,$67,$00,$00,$BA,$41,$ED,$00,$4C,$22,$50,$20,$11
	dc.b $67,$08,$20,$80,$C1,$89,$23,$48,$00,$04,$53,$6D,$00,$72,$22,$40
	dc.b $61,$8C,$60,$0A
loc_0_00000590:
	dc.b $2A,$49,$20,$2D,$00,$26,$67,$D4,$22,$40,$20,$6D,$00,$2A,$08,$29
	dc.b $00,$05,$00,$1E,$66,$5E,$0C,$69,$00,$03,$00,$1C,$66,$14,$10,$18
	dc.b $13,$C0,$00,$BF,$E1,$01,$66,$20,$08,$2D,$00,$03,$00,$76,$67,$18
	dc.b $60,$42,$10,$39,$00,$BF,$E1,$01,$66,$08,$08,$2D,$00,$03,$00,$76
	dc.b $66,$32,$20,$6D,$00,$2A,$10,$C0,$2B,$48,$00,$2A,$52,$AD,$00,$2E
	dc.b $08,$29,$00,$01,$00,$35,$67,$0E,$41,$E9,$00,$36,$72,$07,$B0,$18
	dc.b $54,$C9,$FF,$FC,$67,$0E,$20,$29,$00,$24,$6B,$06,$B0,$AD,$00,$2E
	dc.b $6F,$02,$4E,$75,$23,$6D,$00,$2E,$00,$20,$08,$AD,$00,$03,$00,$76
	dc.b $08,$A9,$00,$04,$00,$1E,$2F,$0E,$2C,$6D,$00,$32,$4E,$AE,$FE,$86
	dc.b $2C,$5F,$42,$AD,$00,$26,$4A,$6D,$00,$72,$66,$D6,$08,$AD,$00,$02
	dc.b $00,$76,$2F,$0E,$2C,$6D,$00,$22,$70,$10,$4E,$AE,$FF,$EE,$2C,$5F
	dc.b $4E,$75,$00,$00
    SECTION section_1,code
    SECTION section_2,data
