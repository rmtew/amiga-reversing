; Memory map
;   Absolute memory refs:
;     absolute[$FFFFFF22] refs=1 access=a
;     absolute[$FFFFFF64] refs=1 access=a
;     absolute[$FFFFFF94] refs=2 access=a
;     absolute[$FFFFFFA6] refs=1 access=a

; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 2.0
;   evidence: highest recovered API requirement is 2.0
;   requirement drivers:
;     2.0: SysBase/_LVOexecPrivate5, SysBase/_LVOexecPrivate3, _LVOexecPrivate3, _LVOexecPrivate5
;   lower-version APIs also observed: 1.3

    INCLUDE "dos/dosextens.i"
    INCLUDE "exec/alerts.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/libraries.i"
    INCLUDE "exec/memory.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/intbits.i"

    RSSET 0
    RS.B 34
app_0022 RS.L 1
    RS.B 4
app_002A RS.L 1
    RS.B 12
app_003A RS.L 1
app_003E RS.L 1
    RS.B 16
app_0052 RS.W 1
app_SIZEOF EQU __RS

runtime_address_FFFFFF94	EQU	$FFFFFF94
runtime_address_FFFFFFA6	EQU	$FFFFFFA6
runtime_address_FFFFFF64	EQU	$FFFFFF64
runtime_address_FFFFFF22	EQU	$FFFFFF22
m68k_vector_division_by_zero	EQU	$14
_custom	EQU	$DFF000
runtime_address_FFFFFFEE	EQU	$FFFFFFEE
runtime_address_FFFFFFE8	EQU	$FFFFFFE8
_LVOexecPrivate3	EQU	-48
_LVOexecPrivate5	EQU	-60

    SECTION section_0,code
loc_0_00000000:
	movem.l d0/a0,-(a7)
	movea.l $00000004.l,a6
	move.l a6,h1dl_ExecBase.l
	move.l #$19C,d0
	move.l #MEMF_CLEAR|MEMF_PUBLIC,d1
	jsr _LVOAllocMem(a6)
	movea.l d0,a1
	movem.l (a7)+,d0/a0
	cmpa.l #$0,a1
	bne.b loc_0_00000032
	moveq.l #20,d0
	rts
loc_0_00000032:
	movea.l a1,a5
	move.l a5,-(a7)
	move.l d0,$0004(a5)
	move.l a0,$0008(a5)
	suba.l a1,a1
	jsr -$0126(a6)
	movea.l d0,a4
	lea.l loc_0_00000206(pc),a1
	moveq.l #0,d0
	jsr -$0228(a6)
	move.l d0,$0000(a5)
	bne.b loc_0_00000072
	movem.l d7/a5-a6,-(a7)
	move.l #AG_OpenLib|AO_DOSLib,d7
	movea.l $0004.w,a6
	jsr _LVOAlert(a6)
	movem.l (a7)+,d7/a5-a6
	moveq.l #100,d0
	bra.w loc_0_000001A4
loc_0_00000072:
	move.l d0,loc_1_00000004.l
	tst.l pr_CLI(a4)
	beq.w loc_0_0000013A
	suba.l a0,a0
	move.l pr_CLI(a4),d0
	lsl.l #2,d0
	move.l $10(a0,d0.l),d0
	lsl.l #2,d0
	movem.l a2-a3,-(a7)
	lea.l $009C(a5),a2
	lea.l $001C(a5),a3
	movea.l d0,a0
	moveq.l #0,d0
	move.b (a0)+,d0
	clr.b $0(a0,d0.l)
	move.l a0,(a3)+
	move.l $0004(a5),d0
	movea.l $0008(a5),a0
	lea.l $0(a0,d0.l),a1
loc_0_000000B2:
	cmpi.b #32,-(a1)
	dbhi.w d0,loc_0_000000B2
	clr.b $0001(a1)
loc_0_000000BE:
	move.b (a0)+,d1
	beq.b loc_0_0000011E
	cmpi.b #32,d1
	beq.b loc_0_000000BE
	cmpi.b #9,d1
	beq.b loc_0_000000BE
	move.l a2,(a3)+
	cmpi.b #34,d1
	beq.b loc_0_000000EA
	move.b d1,(a2)+
loc_0_000000D8:
	move.b (a0)+,d1
	beq.b loc_0_0000011E
	cmpi.b #32,d1
	beq.b loc_0_000000E6
	move.b d1,(a2)+
	bra.b loc_0_000000D8
loc_0_000000E6:
	clr.b (a2)+
	bra.b loc_0_000000BE
loc_0_000000EA:
	move.b (a0)+,d1
	beq.b loc_0_0000011E
	cmpi.b #34,d1
	beq.b loc_0_000000E6
	cmpi.b #42,d1
	bne.b loc_0_0000011A
	move.b (a0)+,d1
	cmpi.b #78,d1
	beq.b loc_0_00000108
	cmpi.b #110,d1
	bne.b loc_0_0000010C
loc_0_00000108:
	moveq.l #10,d1
	bra.b loc_0_0000011A
loc_0_0000010C:
	cmpi.b #69,d1
	beq.b loc_0_00000118
	cmpi.b #101,d1
	bne.b loc_0_0000011A
loc_0_00000118:
	moveq.l #27,d1
loc_0_0000011A:
	move.b d1,(a2)+
	bra.b loc_0_000000EA
loc_0_0000011E:
	clr.b (a2)
	clr.l (a3)
	move.l a3,d0
	lea.l $001C(a5),a3
	sub.l a3,d0
	lsr.l #2,d0
	movem.l (a7)+,a2-a3
	pea.l $001C(a5)
	move.l d0,-(a7)
	bra.w loc_0_00000196
loc_0_0000013A:
	lea.l pr_MsgPort(a4),a0
	jsr -$0180(a6)
	lea.l pr_MsgPort(a4),a0
	jsr -$0174(a6)
	move.l d0,$000C(a5)
	move.l d0,-(a7)
	clr.l -(a7)
	movea.l $0000(a5),a6
	movea.l d0,a2
	move.l $0024(a2),d0
	beq.b loc_0_00000168
	movea.l d0,a0
	move.l $0000(a0),d1
	jsr -$007E(a6)
loc_0_00000168:
	lea.l loc_0_00000212(pc),a0
	move.l a0,d1
	move.l #$3ED,d2
	jsr -$001E(a6)
	tst.l d0
	beq.b loc_0_000001A4
	move.l d0,$0010(a5)
	move.l d0,$009C(a4)
	move.l d0,$00A0(a4)
	lsl.l #2,d0
	movea.l d0,a0
	move.l $0008(a0),d0
	beq.b loc_0_00000196
	move.l d0,$00A4(a4)
loc_0_00000196:
	jsr loc_3_00000030.l
	moveq.l #0,d0
	bra.b loc_0_000001A4
loc_0_000001A0:
	move.l $0004(a7),d0
loc_0_000001A4:
	move.l d0,d2
	movea.l $00000004.l,a6
	suba.l a1,a1
	jsr _LVOFindTask(a6)
	movea.l d0,a4
	movea.l pr_ReturnAddr(a4),a5
	suba.l #$8,a5
	movea.l a5,a7
	movea.l (a7)+,a5
	move.l d2,-(a7)
	move.l $0010(a5),d1
	beq.b loc_0_000001D2
	movea.l $0000(a5),a6
	jsr -$0024(a6)
loc_0_000001D2:
	movea.l $00000004.l,a6
	move.l $0000(a5),d0
	beq.b loc_0_000001E4
	movea.l d0,a1
	jsr _LVOCloseLibrary(a6)
loc_0_000001E4:
	tst.l $000C(a5)
	beq.b loc_0_000001F6
	jsr _LVOForbid(a6)
	movea.l $000C(a5),a1
	jsr _LVOReplyMsg(a6)
loc_0_000001F6:
	movea.l a5,a1
	move.l #$19C,d0
	jsr _LVOFreeMem(a6)
	move.l (a7)+,d0
	rts
loc_0_00000206:
	dc.b "dos.library",$00
loc_0_00000212:
	dc.b $4E,$49,$4C,$3A,$00,$00
    SECTION section_1,data
h1dl_ExecBase:
	dc.b $00,$00,$00,$00
loc_1_00000004:
	dc.b $00,$00,$00,$00,$00,$22,$00,$08,$52,$00,$00,$00
    SECTION section_2,code
	dc.b $00,$00,$00,$89,$78,$10,$D8,$89,$E4,$8C,$23,$44,$00,$0C,$4A,$81
	dc.b $66,$00,$00,$08,$72,$00,$60,$00,$00,$14,$24,$29,$00,$0C,$22,$11
	dc.b $20,$3C,$00,$00,$01,$28,$28,$6A,$FF,$84,$4E,$95,$26,$29,$00,$08
	dc.b $24,$29,$00,$04,$20,$3C,$00,$00,$01,$1C,$49,$EC,$00,$AC,$4E,$95
	dc.b $4E,$D6,$4E,$71,$42,$A9,$00,$08,$60,$00,$00,$18,$22,$11,$D2,$A9
	dc.b $00,$08,$74,$00,$14,$30,$18,$00,$4A,$82,$67,$00,$00,$10,$52,$A9
	dc.b $00,$08,$0C,$A9,$00,$00,$00,$FE,$00,$08,$6D,$E0,$22,$29,$00,$08
	dc.b $23,$41,$00,$0C,$74,$01,$B2,$82,$6D,$00,$00,$22,$D2,$91,$53,$81
	dc.b $76,$00,$16,$30,$18,$00,$22,$29,$00,$04,$E5,$89,$D2,$A9,$00,$0C
	dc.b $11,$83,$18,$00,$72,$FF,$D2,$A9,$00,$0C,$60,$D4,$22,$29,$00,$04
	dc.b $E5,$89,$11,$A9,$00,$0B,$18,$00,$22,$29,$00,$04,$4E,$D6,$4E,$71
	dc.b $70,$1C,$28,$6A,$01,$04,$4E,$95,$23,$41,$00,$10,$70,$20,$28,$6A
	dc.b $01,$08,$4E,$95,$23,$41,$00,$14,$42,$A9,$00,$18,$47,$EC,$01,$08
	dc.b $22,$0B,$E4,$89,$70,$28,$49,$EC,$01,$14,$4E,$95,$23,$41,$00,$1C
	dc.b $4A,$81,$67,$00,$00,$24,$24,$01,$E5,$8A,$4A,$B0,$28,$04,$6F,$00
	dc.b $00,$18,$76,$01,$D6,$B0,$28,$04,$21,$83,$28,$04,$22,$29,$00,$1C
	dc.b $E5,$89,$23,$70,$18,$08,$00,$18,$4A,$A9,$00,$18,$66,$00,$00,$16
	dc.b $47,$EC,$01,$0C,$22,$0B,$E4,$89,$70,$2C,$28,$6A,$01,$44,$4E,$95
	dc.b $23,$41,$00,$18,$4A,$A9,$00,$18,$66,$00,$00,$06,$72,$00,$4E,$D6
	dc.b $22,$29,$00,$04,$70,$2C,$28,$6A,$00,$F4,$4E,$95,$22,$29,$00,$08
	dc.b $70,$2C,$28,$6A,$00,$F8,$4E,$95,$24,$11,$72,$FF,$70,$2C,$28,$6A
	dc.b $00,$28,$4E,$95,$24,$3C,$00,$00,$02,$58,$22,$29,$00,$18,$70,$2C
	dc.b $28,$6A,$01,$E4,$4E,$95,$23,$41,$00,$0C,$22,$29,$00,$10,$70,$2C
	dc.b $28,$6A,$00,$F4,$4E,$95,$22,$29,$00,$14,$70,$2C,$28,$6A,$00,$F8
	dc.b $4E,$95,$4A,$A9,$00,$1C,$66,$00,$00,$12,$22,$29,$00,$18,$70,$2C
	dc.b $28,$6A,$01,$48,$4E,$95,$60,$00,$00,$12,$22,$29,$00,$1C,$E5,$89
	dc.b $24,$30,$18,$04,$53,$82,$21,$82,$18,$04,$72,$00,$B2,$A9,$00,$0C
	dc.b $66,$02,$46,$81,$4E,$D6,$4E,$71,$03,$52,$55,$4E,$05,$43,$3A,$52
	dc.b $55,$4E,$00,$00,$70,$10,$28,$6A,$00,$9C,$4E,$95,$E5,$89,$24,$30
	dc.b $18,$18,$E5,$8A,$23,$70,$28,$10,$00,$04,$60,$00,$00,$2C,$72,$03
	dc.b $D2,$A9,$00,$04,$24,$01,$22,$11,$70,$14,$28,$6A,$01,$34,$4E,$95
	dc.b $4A,$81,$66,$00,$00,$08,$22,$29,$00,$04,$4E,$D6,$22,$29,$00,$04
	dc.b $E5,$89,$23,$70,$18,$00,$00,$04,$4A,$A9,$00,$04,$66,$D0,$72,$00
	dc.b $4E,$D6,$4E,$71,$00,$00,$00,$00,$FF,$FF,$FF,$E1,$00,$00,$00,$44
	dc.b $00,$00,$00,$79
    SECTION section_3,code
loc_3_00000000:
	move.l d2,-(a7)
	move.l $0008(a7),d2
	jsr loc_21_00000010.l
	tst.l loc_4_000001F0.l
	beq.b loc_3_00000026
	move.l d2,-(a7)
	jsr loc_20_0000001C.l
	move.l d0,-(a7)
	jsr loc_17_00000000.l
	addq.l #8,a7
loc_3_00000026:
	jsr loc_21_00000000.l
	move.l (a7)+,d2
	rts
loc_3_00000030:
	movem.l d2-d5/a2-a4,-(a7)
	move.l $0020(a7),d2
	movea.l $0024(a7),a2
	movea.l #loc_3_00000000,a4
	movea.l #loc_15_00000000,a3
	move.l #loc_21_00000088,d3
	move.l h1dl_ExecBase.l,d4
	jsr loc_21_00000000.l
	tst.l d2
	sne.b d0
	neg.b d0
	ext.w d0
	ext.l d0
	move.l d0,loc_4_000001F0.l
	pea.l loc_4_00000000.l
	jsr (a4)
	tst.l loc_4_000001F0.l
	addq.l #4,a7
	beq.b loc_3_000000D8
	move.l d2,d0
	subq.l #1,d0
	asl.l #2,d0
	movea.l d0,a1
	movea.l $0(a1,a2.l),a0
	cmpi.b #63,(a0)
	bne.b loc_3_000000A0
	pea.l loc_4_0000001C.l
	jsr (a4)
	clr.l -(a7)
	jsr loc_0_000001A0.l
	addq.l #8,a7
loc_3_000000A0:
	moveq.l #1,d0
	cmp.l d2,d0
	bge.b loc_3_000000D8
	movea.l $0004(a2),a0
	cmpi.b #114,(a0)
	beq.b loc_3_000000BA
	movea.l $0004(a2),a0
	cmpi.b #82,(a0)
	bne.b loc_3_000000D8
loc_3_000000BA:
	movea.l d4,a0
	cmpi.w #35,$0014(a0)
	bhi.b loc_3_000000D8
	jsr loc_8_00000000.l
	tst.l d0
	bne.b loc_3_000000D8
	pea.l loc_4_00000032.l
	jsr (a4)
	addq.l #4,a7
loc_3_000000D8:
	clr.l -(a7)
	jsr loc_21_00000038.l
	move.l d0,d2
	pea.l loc_4_00000064.l	; KNOWN: arg +4 name UBYTE * string_ptr
	jsr loc_21_00000060.l
	move.l d0,d5
	addq.l #8,a7
	beq.b loc_3_0000010E
	pea.l loc_4_00000070.l
	jsr (a4)
	jsr loc_21_00000010.l
	pea.l $0005.w
	jsr loc_0_000001A0.l
	addq.l #8,a7
loc_3_0000010E:
	move.l #$10001,-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	pea.l $0022.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_21_00000020.l
	movea.l d0,a1
	move.l #loc_4_00000096,$000A(a1)
	move.b #$4,$0008(a1)
	move.l a1,-(a7)	; KNOWN: arg +4 port MP
	jsr loc_21_0000004C.l
	jsr loc_13_00000000.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.b loc_3_0000014E
	pea.l loc_4_000000A2.l
	jsr (a4)
	addq.l #4,a7
loc_3_0000014E:
	movea.l h1dl_ExecBase.l,a0
	cmpi.w #33,$0014(a0)
	beq.b loc_3_0000016A
	movea.l h1dl_ExecBase.l,a0
	cmpi.w #34,$0014(a0)
	bne.b loc_3_000001D4
loc_3_0000016A:
	pea.l loc_4_000000B6.l
	jsr (a4)
	move.l #loc_5_00000000,-(a7)	; KNOWN: arg +12 funcEntry unsigned long (*)() code_ptr
	pea.l runtime_address_FFFFFF94.l	; KNOWN: arg +8 funcOffset long
	move.l d4,-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_21_00000088.l
	move.l d0,loc_5_0000004E.l
	cmpi.l #16515072,loc_5_0000004E.l
	lea.l $0010(a7),a7
	blt.b loc_3_000001A8
	cmpi.l #16777215,loc_5_0000004E.l
	ble.b loc_3_000001CA
loc_3_000001A8:
	move.l loc_5_0000004E.l,-(a7)	; KNOWN: arg +12 funcEntry unsigned long (*)() code_ptr
	pea.l runtime_address_FFFFFF94.l	; KNOWN: arg +8 funcOffset long
	move.l d4,-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_21_00000088.l
	pea.l loc_4_000000C2.l
	jsr (a4)
	lea.l $0010(a7),a7
	bra.b loc_3_000001D4
loc_3_000001CA:
	pea.l loc_4_000000DC.l
	jsr (a4)
	addq.l #4,a7
loc_3_000001D4:
	clr.l -(a7)
	pea.l loc_4_000000E0.l	; KNOWN: arg +4 libName UBYTE * string_ptr amiga.library_name
	jsr loc_21_000000A4.l
	movea.l d0,a2
	move.l a2,d5
	addq.l #8,a7
	bne.b loc_3_000001F4
	pea.l loc_4_000000F0.l
	jsr (a4)
	bra.b loc_3_0000022C
loc_3_000001F4:
	cmpi.w #35,LIB_VERSION(a2)
	bhi.b loc_3_00000224
	move.l #loc_12_00000000,-(a7)	; KNOWN: arg +12 funcEntry unsigned long (*)() code_ptr
	pea.l runtime_address_FFFFFFA6.l	; KNOWN: arg +8 funcOffset long
	move.l a2,-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_21_00000088.l
	move.l d0,-(a7)
	jsr loc_10_00000076.l
	pea.l loc_4_00000116.l
	jsr (a4)
	lea.l $0014(a7),a7
loc_3_00000224:
	move.l a2,-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_21_00000074.l
loc_3_0000022C:
	addq.l #4,a7
	movea.l d4,a0
	cmpi.w #35,$0014(a0)
	bhi.b loc_3_00000274
	jsr loc_9_00000000.l
	pea.l loc_4_00000126.l
	jsr (a4)
	jsr loc_7_00000000.l
	pea.l loc_4_0000014C.l
	jsr (a4)
	move.l #loc_6_00000000,-(a7)	; KNOWN: arg +12 funcEntry unsigned long (*)() code_ptr
	pea.l runtime_address_FFFFFF64.l	; KNOWN: arg +8 funcOffset long
	move.l d4,-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_21_00000088.l
	pea.l loc_4_00000160.l
	jsr (a4)
	lea.l $0018(a7),a7
loc_3_00000274:
	movea.l d2,a1
	move.l $00AC(a1),d0
	asl.l #2,d0
	movea.l d0,a2
	movea.l loc_1_00000004.l,a0
	cmpi.w #35,LIB_VERSION(a0)
	bhi.w loc_3_0000030E
	move.l $003C(a2),d0
	bra.b loc_3_000002B0
loc_3_00000294:
	movea.l (a3),a0
	cmpi.l #556,-$0004(a0)
	bne.b loc_3_000002AC
	movea.l (a3),a0
	cmpi.l #137,$0004(a0)
	beq.b loc_3_000002B8
loc_3_000002AC:
	movea.l (a3),a0
	move.l (a0),d0
loc_3_000002B0:
	asl.l #2,d0
	move.l d0,(a3)
	tst.l (a3)
	bne.b loc_3_00000294
loc_3_000002B8:
	tst.l (a3)
	beq.b loc_3_0000030E
	pea.l loc_4_00000174.l
	jsr (a4)
	addq.l #8,(a3)
	move.l loc_1_00000004.l,d0
	movea.l #runtime_address_FFFFFF22,a0
	cmpi.l #1894080512,$0(a0,d0.l)
	addq.l #4,a7
	bne.b loc_3_00000304
	move.l #loc_15_00000004,-(a7)	; KNOWN: arg +12 funcEntry unsigned long (*)() code_ptr
	pea.l runtime_address_FFFFFF22.l	; KNOWN: arg +8 funcOffset long
	move.l loc_1_00000004.l,-(a7)	; KNOWN: arg +4 library LIB
	jsr loc_21_00000088.l
	pea.l loc_4_00000186.l
	jsr (a4)
	lea.l $0010(a7),a7
	bra.b loc_3_0000030E
loc_3_00000304:
	pea.l loc_4_000001A4.l
	jsr (a4)
	addq.l #4,a7
loc_3_0000030E:
	clr.l $003C(a2)
	jsr loc_21_00000010.l
	clr.l -(a7)
	jsr loc_0_000001A0.l
	addq.l #4,a7
	movem.l (a7)+,d2-d5/a2-a4
	rts
    SECTION section_4,data
loc_4_00000000:
	dc.b "SetPatch 1.34 (12-May-89)",$0A
	dc.b $00
	dc.b $00
loc_4_0000001C:
	dc.b "Usage: SetPatch [r]",$0A
	dc.b $00
	dc.b $00
loc_4_00000032:
	dc.b "Patch for RAD use with 1MB chip memory installed",$0A
	dc.b $00
loc_4_00000064:
	dc.b "SetPatch-01",$00
loc_4_00000070:
	dc.b "SetPatch has already been installed.",$0A
	dc.b $00
loc_4_00000096:
	dc.b "SetPatch-01",$00
loc_4_000000A2:
	dc.b "Trackdisk patched",$0A
	dc.b $00
	dc.b $00
loc_4_000000B6:
	dc.b "Alert patch",$00
loc_4_000000C2:
	dc.b " skipped (vector in use)"
	dc.b $0A,$00
loc_4_000000DC:
	dc.b $65,$64,$0A,$00
loc_4_000000E0:
	dc.b "layers.library",$00
	dc.b $00
loc_4_000000F0:
	dc.b "Error: could not open layers.library",$0A
	dc.b $00
loc_4_00000116:
	dc.b "Layers patched",$0A
	dc.b $00
loc_4_00000126:
	dc.b "Exec 68881/68882 exceptions patched",$0A
	dc.b $00
	dc.b $00
loc_4_0000014C:
	dc.b "AllocEntry patched",$0A
	dc.b $00
loc_4_00000160:
	dc.b "UserState patched",$0A
	dc.b $00
	dc.b $00
loc_4_00000174:
	dc.b "DOS Execute call ",$00
loc_4_00000186:
	dc.b "patched to use resident RUN",$0A
	dc.b $00
	dc.b $00
loc_4_000001A4:
	dc.b "already patched",$0A
	dc.b $00
	dc.b $00
	dc.b "Copyright 1989 Commodore-Amiga, Inc. All Rights Reserved",$00
	dc.b $00
loc_4_000001F0:
	dc.b $00,$00,$00,$00
    SECTION section_5,code
loc_5_00000000:
	dc.b $33,$FC,$40,$00,$00,$DF,$F0,$9A,$20,$3C,$48,$45,$4C,$50,$B0,$B8
	dc.b $00,$00,$67,$00,$00,$2E,$21,$C0,$00,$00,$41,$F8,$01,$00,$20,$87
	dc.b $08,$D0,$00,$07,$58,$88,$20,$D5,$20,$38,$00,$04,$22,$00,$02,$81
	dc.b $FF,$00,$00,$01,$66,$0C,$20,$7A,$00,$16,$D1,$FC,$00,$00,$00,$30
	dc.b $4E,$D0,$20,$7A,$00,$0A,$D1,$FC,$00,$00,$00,$88,$4E,$D0
loc_5_0000004E:
	dc.b $00,$00,$00,$00,$00,$00
    SECTION section_6,code
loc_6_00000000:
	move.l (a7)+,d1
	move a7,usp
	movea.l d0,a7
	movea.l a5,a0
	lea.l loc_6_00000010(pc),a5
	jmp -$001E(a6)
loc_6_00000010:
	dc.b $2A,$48,$2F,$41,$00,$02,$02,$57,$DF,$FF,$4E,$73
    SECTION section_7,code
loc_7_00000000:
	movea.l $0004.w,a6
	cmpi.w #35,LIB_VERSION(a6)
	bls.b loc_7_0000000E
	rts
loc_7_0000000E:
	lea.l loc_7_0000001E(pc),a0
	move.l a0,d0
	movea.w #$FF22,a0
	movea.l a6,a1
	jmp -$01A4(a6)
loc_7_0000001E:
	dc.b $48,$E7,$30,$38,$24,$48,$76,$00,$36,$2A,$00,$0E,$20,$03,$E7,$88
	dc.b $06,$80,$00,$00,$00,$10,$22,$3C,$00,$01,$00,$00,$4E,$AE,$FF,$3A
	dc.b $26,$40,$28,$40,$4A,$80,$67,$66,$37,$43,$00,$0E,$45,$EA,$00,$10
	dc.b $47,$EB,$00,$10,$74,$00,$22,$2A,$00,$00,$20,$2A,$00,$04,$27,$40
	dc.b $00,$04,$67,$08,$4E,$AE,$FF,$3A,$4A,$80,$67,$16,$27,$40,$00,$00
	dc.b $50,$8A,$50,$8B,$52,$42,$53,$83,$66,$DC,$20,$0C,$4C,$DF,$1C,$0C
	dc.b $4E,$75,$53,$42,$6B,$10,$51,$8B,$22,$6B,$00,$00,$20,$2B,$00,$04
	dc.b $4E,$AE,$FF,$2E,$60,$EC,$70,$00,$30,$2C,$00,$0E,$E7,$88,$06,$80
	dc.b $00,$00,$00,$10,$22,$4C,$4E,$AE,$FF,$2E,$20,$2A,$00,$00,$08,$C0
	dc.b $00,$1F,$60,$C8,$00,$00
    SECTION section_8,code
loc_8_00000000:
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOForbid(a6)
	cmpi.w #35,LIB_VERSION(a6)
	bge.w loc_8_000000AA
	cmpi.l #524288,app_003E(a6)
	ble.w loc_8_000000AA
	tst.l app_002A(a6)
	bne.w loc_8_000000AA
	moveq.l #44,d0
	move.l app_003A(a6),d1
	sub.l d0,d1
	subi.l #32,d1
	andi.l #4294967292,d1
	movea.l d1,a1
	move.l a1,-(a7)	; KNOWN: arg +4 address APTR
	jsr _LVOTypeOfMem(a6)
	movea.l (a7)+,a1
	btst #1,d0
	beq.b loc_8_0000006A
	moveq.l #44,d0
	move.l a1,-(a7)	; KNOWN: arg +4 byteSize unsigned long
	jsr _LVOAllocAbs(a6)
	movea.l (a7)+,a1
	tst.l d0
	bne.b loc_8_00000076
	moveq.l #44,d0
	suba.l #$320,a1
	jsr _LVOAllocAbs(a6)
	tst.l d0
	bne.b loc_8_00000076
loc_8_0000006A:
	moveq.l #44,d0
	moveq.l #MEMF_CHIP|MEMF_PUBLIC,d1
	jsr _LVOAllocMem(a6)
	tst.l d0
	beq.b loc_8_000000AA
loc_8_00000076:
	moveq.l #44,d1
	movea.l d0,a0
	lea.l loc_8_000000B4(pc),a1
	bra.b loc_8_00000082
loc_8_00000080:
	move.b (a1)+,(a0)+
loc_8_00000082:
	dbf.w d1,loc_8_00000080
	move.l d0,app_002A(a6)
	moveq.l #0,d1
	lea.l app_0022(a6),a0
	move.w #$16,d0
loc_8_00000094:
	add.w (a0)+,d1
	dbf.w d0,loc_8_00000094
	not.w d1
	move.w d1,app_0052(a6)
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	moveq.l #0,d0
	rts
loc_8_000000AA:
	jsr -$008A(a6)
	movea.l (a7)+,a6
	moveq.l #20,d0
	rts
loc_8_000000B4:
	dc.b $72,$00,$41,$EE,$00,$22,$30,$3C,$00,$16,$D2,$58,$51,$C8,$FF,$FC
	dc.b $46,$41,$3D,$41,$00,$52,$0C,$AD,$B7,$FC,$00,$04,$00,$1E,$66,$0A
	dc.b $26,$6E,$00,$3E,$DB,$FC,$00,$00,$00,$1E,$4E,$D5
    SECTION section_9,code
loc_9_00000000:
	movea.l m68k_vector_division_by_zero.w,a0
	move.w (a0),d0
	ext.w d0
	ext.l d0
	adda.l d0,a0
	addq.l #2,a0
	addq.l #6,a0
	cmpi.w #58095,(a0)
	beq.b loc_9_0000001A
	tst.w $0001.w
loc_9_0000001A:
	move.l a0,loc_9_00000038.l
	lea.l loc_9_0000003C.l,a1
	movea.l #$C0,a0
	moveq.l #15,d0
loc_9_0000002E:
	move.l a1,(a0)+
	addq.w #2,a1
	dbf.w d0,loc_9_0000002E
	rts
loc_9_00000038:
	dc.b $00,$00,$00,$00
loc_9_0000003C:
	dc.b $61,$20,$61,$1E,$61,$1C,$61,$1A,$61,$18,$61,$16,$61,$14,$61,$12
	dc.b $61,$10,$61,$0E,$61,$0C,$61,$0A,$61,$08,$61,$06,$61,$04,$61,$02
	dc.b $4E,$71,$2F,$00,$48,$7A,$FF,$DC,$20,$1F,$91,$AF,$00,$04,$20,$1F
	dc.b $06,$97,$00,$00,$00,$60,$2F,$3A,$FF,$C4,$4E,$75
    SECTION section_10,code
loc_10_00000000:
	movea.l $0004(a7),a0
	bra.b loc_10_00000008
loc_10_00000006:
	addq.l #2,a0
loc_10_00000008:
	moveq.l #0,d0
	move.w (a0),d0
	andi.l #65280,d0
	cmpi.l #24832,d0
	bne.b loc_10_00000006
	move.l a0,d0
	rts
loc_10_0000001E:
	move.l d2,-(a7)
	movea.l $0008(a7),a0
	move.w (a0),d1
	moveq.l #0,d0
	move.w d1,d0
	andi.l #255,d0
	beq.b loc_10_00000050
	moveq.l #0,d0
	move.w d1,d0
	move.l d0,d1
	andi.l #255,d1
	move.l d1,d0
	asr.l #1,d0
	move.l d0,d1
	btst #6,d1
	beq.b loc_10_00000068
	moveq.l #-128,d0
	or.l d0,d1
	bra.b loc_10_00000068
loc_10_00000050:
	moveq.l #0,d0
	move.w $0002(a0),d0
	asr.l #1,d0
	move.l d0,d1
	andi.l #16384,d0
	beq.b loc_10_00000068
	ori.l #4294934528,d1
loc_10_00000068:
	move.l d1,d0
	add.l d0,d0
	move.l a0,d2
	add.l d2,d0
	addq.l #2,d0
	move.l (a7)+,d2
	rts
loc_10_00000076:
	movem.l d2/a2,-(a7)
	move.l $000C(a7),d2
	movea.l #loc_10_0000001E,a2
	addq.l #2,d2
	move.l d2,-(a7)
	jsr (a2)
	move.l d0,-(a7)
	jsr loc_10_00000000(pc)
	move.l d0,d2
	move.l d2,-(a7)
	jsr (a2)
	move.l d0,loc_11_00000000.l
	addq.l #2,d2
	move.l d2,-(a7)
	jsr loc_10_00000000(pc)
	move.l d0,d2
	move.l d2,-(a7)
	jsr (a2)
	move.l d0,loc_11_00000004.l
	addq.l #2,d2
	move.l d2,-(a7)
	jsr loc_10_00000000(pc)
	move.l d0,-(a7)
	jsr (a2)
	move.l d0,loc_11_00000008.l
	lea.l $001C(a7),a7
	movem.l (a7)+,d2/a2
	rts
    SECTION section_11,data
loc_11_00000000:
	dc.b $00,$00,$00,$00
loc_11_00000004:
	dc.b $00,$00,$00,$00
loc_11_00000008:
	dc.b $00,$00,$00,$00
    SECTION section_12,code
loc_12_00000000:
	dc.b $2F,$0A,$24,$49,$2F,$2A,$00,$44,$20,$79
	dc.l loc_11_00000000
	dc.b $4E,$90,$58,$8F,$4A,$80,$67,$20,$22,$4A,$24,$69,$00,$44,$2F,$09
	dc.b $20,$79
	dc.l loc_11_00000004
	dc.b $4E,$90,$2E,$8A,$20,$79
	dc.l loc_11_00000008
	dc.b $4E,$90,$58,$8F,$70,$01,$60,$02,$42,$80,$24,$5F,$4E,$75
    SECTION section_13,code
loc_13_00000000:
	movem.l a5-a6,-(a7)
	movea.l $0004.w,a6
	lea.l loc_13_000000BC(pc),a1
	jsr _LVOOpenResource(a6)
	movea.l d0,a5
	move.l a5,d0
	beq.b loc_13_00000076
	move.w $0014(a5),d1
	moveq.l #0,d0
	cmpi.w #35,d1
	bhi.b loc_13_00000076
	movea.l $0004.w,a0
	move.w #INTF_INTEN,_custom+intena.l
	addq.b #1,$0126(a0)
	movea.l a5,a1
	lea.l loc_13_0000007C(pc),a0
	move.l a0,d0
	movea.l #runtime_address_FFFFFFEE,a0
	jsr _LVOSetFunction(a6)
	move.l d0,loc_13_000000B4.l
	movea.l a5,a1
	lea.l loc_13_00000094(pc),a0
	move.l a0,d0
	movea.l #runtime_address_FFFFFFE8,a0
	jsr _LVOSetFunction(a6)
	move.l d0,loc_13_000000B8.l
	movea.l $0004.w,a0
	subq.b #1,$0126(a0)
	bge.b loc_13_00000074
	move.w #INTF_SETCLR|INTF_INTEN,_custom+intena.l
loc_13_00000074:
	moveq.l #-1,d0
loc_13_00000076:
	movem.l (a7)+,a5-a6
	rts
loc_13_0000007C:
	movea.l loc_13_000000B4(pc),a0
	jsr (a0)
	tst.l d0
	beq.b loc_13_00000092
	movea.l $0004.w,a0
	move.l $0114(a0),loc_13_000000B0.l
loc_13_00000092:
	rts
loc_13_00000094:
	move.l loc_13_000000B0(pc),d1
	movea.l $0004.w,a0
	cmp.l $0114(a0),d1
	bne.b loc_13_000000A8
loc_13_000000A2:
	movea.l loc_13_000000B8(pc),a0
	jmp (a0)
loc_13_000000A8:
	moveq.l #-1,d0
	cmp.l d0,d1
	beq.b loc_13_000000A2
	rts
loc_13_000000B0:
	dc.l $FFFFFFFF	; lookup_table
loc_13_000000B4:
	dc.l $00000000	; lookup_table
loc_13_000000B8:
	dc.l $00000000	; lookup_table
loc_13_000000BC:
	dc.b "disk.resource",$00
	dc.w $0000
    SECTION section_14,code
    SECTION section_15,code
loc_15_00000000:
	dc.b $00,$00,$00,$00
loc_15_00000004:
	dc.b $48,$E7,$3F,$3E,$2A,$0F,$04,$85,$00,$00,$05,$DC,$08,$85,$00,$01
	dc.b $22,$45,$20,$39
	dc.l loc_1_00000004
	dc.b $06,$80,$00,$00,$00,$2A,$20,$40,$4C,$E8,$64,$00,$00,$00,$28,$7A
	dc.b $FF,$D4,$91,$C8,$70,$0C,$4E,$95,$20,$01,$4C,$DF,$7C,$FC,$4E,$75
    SECTION section_16,code
loc_16_00000000:
	movem.l a2-a4/a6,-(a7)
	movea.l $0014(a7),a4
	movea.l $0018(a7),a0
	movea.l $001C(a7),a1
	lea.l loc_16_0000004C(pc),a2
	lea.l -$008C(a7),a7
	movea.l a7,a3
	movea.l $00000004.l,a6
	jsr _LVORawDoFmt(a6)
	moveq.l #-1,d0
loc_16_00000026:
	tst.b (a3)+
	dbeq.w d0,loc_16_00000026
	not.l d0
	beq.b loc_16_00000042
	move.l d0,-(a7)
	pea.l $0004(a7)
	pea.l (a4)
	jsr loc_20_00000000.l
	lea.l $000C(a7),a7
loc_16_00000042:
	lea.l $008C(a7),a7
	movem.l (a7)+,a2-a4/a6
	rts
loc_16_0000004C:
	dc.b $16,$C0,$4E,$75
    SECTION section_17,code
loc_17_00000000:
	movem.l d2-d3,-(a7)
	move.l $000C(a7),d3
	move.l $0010(a7),d2
	pea.l $0014(a7)
	move.l d2,-(a7)
	move.l d3,-(a7)
	jsr loc_16_00000000.l
	lea.l $000C(a7),a7
	movem.l (a7)+,d2-d3
	rts
    SECTION section_18,data
    SECTION section_19,code
    SECTION section_20,code
loc_20_00000000:
	movem.l d2-d3/a6,-(a7)
	movea.l loc_1_00000004.l,a6
	movem.l $0010(a7),d1-d3
	jsr _LVOexecPrivate3(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.w $0000
loc_20_0000001C:
	move.l a6,-(a7)
	movea.l loc_1_00000004.l,a6
	jsr _LVOexecPrivate5(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_21,code
loc_21_00000000:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	jsr _LVOForbid(a6)
	movea.l (a7)+,a6
	rts
loc_21_00000010:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	jsr _LVOPermit(a6)
	movea.l (a7)+,a6
	rts
loc_21_00000020:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movem.l $0008(a7),d0-d1	; KNOWN: arg +4 byteSize unsigned long | KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	rts
	dc.w $0000
loc_21_00000038:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 name UBYTE * string_ptr
	jsr _LVOFindTask(a6)
	movea.l (a7)+,a6
	rts
loc_21_0000004C:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 port MP
	jsr _LVOAddPort(a6)
	movea.l (a7)+,a6
	rts
loc_21_00000060:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 name UBYTE * string_ptr
	jsr _LVOFindPort(a6)
	movea.l (a7)+,a6
	rts
loc_21_00000074:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 library LIB
	jsr _LVOCloseLibrary(a6)
	movea.l (a7)+,a6
	rts
loc_21_00000088:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 library LIB
	movea.l $000C(a7),a0	; KNOWN: arg +8 funcOffset long
	move.l $0010(a7),d0	; KNOWN: arg +12 funcEntry unsigned long (*)() code_ptr
	jsr _LVOSetFunction(a6)
	movea.l (a7)+,a6
	rts
loc_21_000000A4:
	move.l a6,-(a7)
	movea.l h1dl_ExecBase.l,a6
	movea.l $0008(a7),a1
	move.l $000C(a7),d0
	jsr _LVOOpenLibrary(a6)
	movea.l (a7)+,a6
	rts
    SECTION section_22,data
    SECTION section_23,data
