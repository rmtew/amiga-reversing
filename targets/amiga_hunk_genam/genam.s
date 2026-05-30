; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 2.0
;   evidence: highest recovered API requirement is 2.0
;   requirement drivers:
;     2.0: _LVOGetSysTime x2
;   lower-version APIs also observed: 1.3

    INCLUDE "devices/timer.i"
    INCLUDE "devices/timer_lib.i"
    INCLUDE "dos/dos.i"
    INCLUDE "dos/dos_lib.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/io.i"
    INCLUDE "exec/libraries.i"
    INCLUDE "exec/memory.i"

    RSSET 0
    RS.B 254
app_00FE RS.B 1
app_00FF RS.B 1
    RS.B 1
app_0101 RS.B 1
    RS.B 1
app_0103 RS.B 1
    RS.B 1
app_0105 RS.B 1
    RS.B 1
app_0107 RS.B 1
    RS.B 1
app_0109 RS.B 1
    RS.B 1
app_010B RS.B 1
    RS.B 1
app_010D RS.B 1
    RS.B 4
app_0112 RS.B 1
app_0113 RS.B 1
app_0114 RS.B 1
app_0115 RS.B 1
app_0116 RS.B 1
app_0117 RS.B 1
app_0118 RS.B 1
app_0119 RS.B 1
    RS.B 1
app_011B RS.B 1
app_011C RS.B 1
app_011D RS.B 1
app_011E RS.B 1
app_011F RS.B 1
    RS.B 224
app_0200 RS.L 1
app_0204 RS.L 1
app_0208 RS.L 1
app_020C RS.L 1
app_0210 RS.L 1
app_0214 RS.L 1
app_0218 RS.W 1
app_021A RS.B 1
app_021B RS.B 1
app_021C RS.W 1
app_021E RS.W 1
app_0220 RS.L 1
app_0224 RS.L 1
app_0228 RS.L 1
app_022C RS.L 1
app_0230 RS.L 1
app_0234 RS.L 1
app_0238 RS.B 1
app_0239 RS.B 1
app_023A RS.B 1
app_023B RS.B 1
app_023C RS.L 1
app_0240 RS.L 1
app_0244 RS.L 1
app_0248 RS.L 1
app_024C RS.L 1
app_0250 RS.L 1
app_0254 RS.W 1
    RS.B 268
app_0362 RS.L 1
    RS.B 130
app_03E8 RS.L 1
app_03EC RS.B 1
    RS.B 129
app_046E RS.L 1
    RS.B 130
app_04F4 RS.L 1
    RS.B 1
app_04F9 RS.B 1
app_04FA RS.L 1
    RS.B 124
app_057A RS.L 1
app_057E RS.L 1
    RS.B 38
app_05A8 RS.L 1
    RS.B 18
app_05BE RS.L 1
    RS.B 102
app_0628 RS.W 1
    RS.B 38
app_0650 RS.W 1
    RS.B 118
app_06C8 RS.B 1
    RS.B 81
app_071A RS.B 1
    RS.B 81
app_076C RS.L 1
    RS.B 30
app_078E RS.W 1
    RS.B 80
app_07E0 RS.B 1
    RS.B 81
app_0832 RS.L 1
    RS.B 4
app_083A RS.B 1
app_083B RS.B 1
app_083C RS.L 1
app_0840 RS.B 1
app_0841 RS.B 1
app_0842 RS.B 1
app_0843 RS.B 1
app_0844 RS.B 1
    RS.B 1
app_0846 RS.L 1
app_084A RS.L 1
    RS.B 14
app_085C RS.B 1
    RS.B 15
app_086C RS.B 1
    RS.B 5
app_0872 RS.L 1
    RS.B 8
app_087E RS.W 1
app_0880 RS.W 1
app_0882 RS.L 1
app_0886 RS.W 1
app_0888 RS.L 1
    RS.B 4
app_0890 RS.L 1
app_0894 RS.L 1
app_0898 RS.W 1
app_089A RS.W 1
app_089C RS.L 1
app_08A0 RS.L 1
    RS.B 156
app_0940 RS.L 1
app_0944 RS.L 1
app_0948 RS.L 1
app_094C RS.L 1
app_0950 RS.L 1
app_0954 RS.B 1
app_0955 RS.B 1
app_0956 RS.L 1
app_095A RS.L 1
    RS.B 508
app_0B5A RS.L 1
app_0B5E RS.L 1
app_0B62 RS.W 1
app_0B64 RS.W 1
app_0B66 RS.W 1
app_0B68 RS.W 1
app_0B6A RS.W 1
app_0B6C RS.W 1
app_0B6E RS.L 1
    RS.B 16
app_0B82 RS.B 1
    RS.B 80
app_0BD3 RS.B 1
    RS.B 80
app_0C24 RS.B 1
    RS.B 1
app_0C26 RS.B 1
    RS.B 5
app_0C2C RS.L 1
app_0C30 RS.L 1
    RS.B 162
app_DOSBase RS.L 1
app_0CDA RS.L 1
app_0CDE RS.L 1
app_0CE2 RS.L 1
    RS.B 260
app_0DEA RS.L 1
app_0DEE RS.W 1
app_0DF0 RS.L 1
app_0DF4 RS.B 1
    RS.B 1
app_0DF6 RS.L 1
    RS.B 126
app_0E78 RS.L 1
    RS.B 556
app_10A8 RS.B 8
app_10B0 RS.B 8
app_timer_device_iorequest RS.B 48
app_10E8 RS.L 1
    RSSET $021D
app_021D RS.B 1
    RSSET $023F
app_023F RS.B 1
    RSSET $057F
app_057F RS.B 1
    RSSET $10CC
app_TimerBase RS.L 1
    RSSET $10EC
app_SIZEOF EQU __RS


    SECTION section,code
    ; Hunk file entrypoint.
loc_0_00000000:
	bra.b loc_0_00000036
	dc.b $94,$4F,$7A,$30,$85,$C2
	dc.b "$VER: GenAm 3.18 (2.8.94)",$00
	dc.b $28,$43,$29,$20,$48,$69,$53,$6F,$66,$74,$20,$31,$39,$38,$35,$2D
	dc.b $31,$39,$39,$37
loc_0_00000036:
	jsr loc_0_0000A910.l
	jsr loc_0_00009106.l
	move.l a7,app_0234(a6)
	subq.l #4,app_0234(a6)
	movea.l #loc_0_0000A664,a0
	lea.l -$0002(a6),a1
	moveq.l #63,d0
loc_0_00000056:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_0_00000056
	lea.l app_00FE(a6),a0
	move.w #$94,d0
loc_0_00000064:
	clr.w (a0)+
	dbf.w d0,loc_0_00000064
	sf.b app_023A(a6)
	sf.b app_0238(a6)
	clr.b app_04F9(a6)
	jsr loc_0_000090A8.l
	lea.l app_0248(a6),a1
	clr.l (a1)
	move.l a1,$0172(a6)
	lea.l app_0244(a6),a1
	clr.l (a1)
	move.l a1,$016A(a6)
	bsr.w loc_0_00006E42
	clr.b app_06C8(a6)
	lea.l app_timer_device_iorequest+IO_DATA(a6),a3
	bsr.w loc_0_00004668
	lea.l app_0832(a6),a3
	bsr.w loc_0_00004668
	clr.b app_07E0(a6)
	lea.l app_08A0(a6),a0
	move.l a0,app_0940(a6)
	clr.w app_0254(a6)
	move.b #$64,app_023A(a6)
	jsr loc_0_0000A9BC.l
	bne.w loc_0_0000046E
	clr.b app_078E(a6)
	st.b app_0840(a6)
	sf.b app_0841(a6)
	sf.b app_0842(a6)
	st.b app_0843(a6)
	jsr parse_startup_options_buffer.l
	sf.b $0102(a6)
	jsr parse_option_source_buffer.l
	sf.b $0102(a6)
	lea.l app_07E0(a6),a0
	tst.b (a0)
	beq.b loc_0_00000110
	jsr loc_0_0000B0AC.l
	beq.w loc_0_00000174
	move.l a0,app_0230(a6)
	jsr parse_input_source_buffer.l
	bne.w loc_0_00000170
loc_0_00000110:
	jsr loc_0_0000AB2A.l
	tst.b app_04F9(a6)
	beq.w loc_0_00000178
	tst.b $0127(a6)
	bne.b loc_0_0000012C
	moveq.l #0,d0
	jsr loc_0_00008E7A.l
loc_0_0000012C:
	jsr loc_0_00004590.l
	bne.w loc_0_0000016C
	jsr loc_0_0000FCDA.l
	sf.b app_023A(a6)
	lea.l app_08A0(a6),a0
	move.l a0,app_0940(a6)
	clr.b $010A(a6)
	lea.l app_04F4(a6),a0
	jsr loc_0_00008856.l
	beq.b loc_0_000001C8
	moveq.l #10,d0
	jsr loc_0_00008E7A.l
	bsr.b loc_0_00000184
	move.b #$64,app_023A(a6)
	bra.w loc_0_0000046E
loc_0_0000016C:
	moveq.l #26,d0
	bra.b loc_0_0000017A
loc_0_00000170:
	moveq.l #24,d0
	bra.b loc_0_0000017A
loc_0_00000174:
	moveq.l #25,d0
	bra.b loc_0_0000017A
loc_0_00000178:
	moveq.l #23,d0
loc_0_0000017A:
	jsr loc_0_00008E7A.l
	bra.w loc_0_0000046E
loc_0_00000184:
	lea.l app_04F4(a6),a0
	moveq.l #0,d0
	move.b $0005(a0),d0
	subq.w #2,d0
	bmi.b loc_0_000001A0
	addq.w #6,a0
loc_0_00000194:
	move.b (a0)+,d1
	jsr loc_0_00008E98.l
	dbf.w d0,loc_0_00000194
loc_0_000001A0:
	jmp loc_0_00008E8C.l
loc_0_000001A6:
	move.w app_0218(a6),-(a7)
	clr.w app_0218(a6)
	jsr parse_option_source_buffer.l
	bne.b loc_0_00000178
	jsr parse_input_source_buffer.l
	bne.b loc_0_00000170
	move.w (a7)+,app_0218(a6)
	sf.b $0102(a6)
	rts
loc_0_000001C8:
	tst.l $017E(a6)
	bne.b loc_0_000001D2
	moveq.l #29,d0
	bra.b loc_0_0000017A
loc_0_000001D2:
	movea.l app_04F4(a6),a1
	move.b app_04F9(a6),d0
	subq.b #1,d0
loc_0_000001DC:
	move.l a1,d2
	move.b d0,d3
loc_0_000001E0:
	subq.b #1,d0
	bcs.b loc_0_000001FA
	move.b (a1)+,d1
	cmp.b #$5C,d1
	beq.b loc_0_000001DC
	cmp.b #$2F,d1
	beq.b loc_0_000001DC
	cmp.b #$3A,d1
	beq.b loc_0_000001DC
	bra.b loc_0_000001E0
loc_0_000001FA:
	lea.l app_057E(a6),a0
	movea.l d2,a1
	move.b d3,(a0)+
loc_0_00000202:
	beq.b loc_0_0000020A
	move.b (a1)+,(a0)+
	subq.b #1,d3
	bra.b loc_0_00000202
loc_0_0000020A:
	move.b #$A,(a0)
	bsr.w loc_0_00000496
	sf.b app_0840(a6)
	st.b app_0841(a6)
	st.b app_0842(a6)
	jsr parse_startup_options_buffer.l
	sf.b $0102(a6)
	lea.l app_05A8(a6),a0
	move.l a0,app_024C(a6)
	tst.b $0127(a6)
	bne.b loc_0_0000024A
	moveq.l #27,d0
	jsr loc_0_00008E7A.l
	bsr.w loc_0_00000184
	moveq.l #1,d0
	jsr loc_0_00008E7A.l
loc_0_0000024A:
	move.b app_0954(a6),app_0955(a6)
	sf.b app_0840(a6)
	st.b app_0841(a6)
	st.b app_0842(a6)
	sf.b app_0843(a6)
	bsr.w loc_0_000001A6
	bsr.w loc_0_000006AC
	bne.b loc_0_000002B0
	move.l a7,app_0234(a6)
	subq.l #4,app_0234(a6)
	sf.b app_0844(a6)
	bsr.w loc_0_000009C8
	bsr.w loc_0_000007F8
	tst.b app_0844(a6)
	beq.b loc_0_00000298
	sf.b app_0840(a6)
	st.b app_0841(a6)
	sf.b app_0842(a6)
	sf.b app_0843(a6)
	bsr.w loc_0_000001A6
loc_0_00000298:
	move.l a7,app_0234(a6)
	subq.l #4,app_0234(a6)
loc_0_000002A0:
	bsr.w loc_0_000006AC
	bne.b loc_0_000002B0
	bsr.w loc_0_000009C8
	bsr.w loc_0_000007F8
	bra.b loc_0_000002A0
loc_0_000002B0:
	tst.b $010C(a6)
	bne.w loc_0_000003B0
	bsr.w loc_0_00000590
	sf.b app_0955(a6)
	tst.b $0127(a6)
	bne.b loc_0_000002CE
	moveq.l #2,d0
	jsr loc_0_00008E7A.l
loc_0_000002CE:
	tst.b app_0115(a6)
	bgt.w loc_0_000006A4
	move.b app_0954(a6),app_0955(a6)
	jsr loc_0_0000AB50.l
	st.b app_0238(a6)
	bsr.w loc_0_00000496
	tst.b app_0954(a6)
	beq.b loc_0_000002F8
	sf.b app_083A(a6)
	st.b $0100(a6)
loc_0_000002F8:
	lea.l app_0832(a6),a3
	bsr.w loc_0_00004678
	sf.b app_0840(a6)
	st.b app_0841(a6)
	sf.b app_0842(a6)
	st.b app_0843(a6)
	jsr parse_startup_options_buffer.l
	sf.b app_0841(a6)
	jsr parse_option_source_buffer.l
	jsr parse_input_source_buffer.l
	sf.b $0102(a6)
	jsr loc_0_0000AB2A.l
	lea.l app_04F4(a6),a0
	clr.b $010A(a6)
	jsr loc_0_00008856.l
	beq.b loc_0_00000346
	jmp loc_0_0000846E.l
loc_0_00000346:
	st.b app_0841(a6)
	sf.b app_0843(a6)
	bsr.w loc_0_000001A6
	bsr.w loc_0_000006AC
	bne.b loc_0_00000386
	sf.b app_0844(a6)
	bsr.w loc_0_000009C8
	bsr.w loc_0_000008DC
	tst.b app_0844(a6)
	beq.b loc_0_00000376
	bsr.w loc_0_000001A6
	move.l a7,app_0234(a6)
	subq.l #4,app_0234(a6)
loc_0_00000376:
	bsr.w loc_0_000006AC
	bne.b loc_0_00000386
	bsr.w loc_0_000009C8
	bsr.w loc_0_000008DC
	bra.b loc_0_00000376
loc_0_00000386:
	bsr.w loc_0_0000057A
	bsr.w loc_0_000079CC
	bsr.w loc_0_000079DA
	jsr loc_0_00009898.l
	tst.b app_00FF(a6)
	beq.b loc_0_000003A4
	jsr loc_0_00008F60.l
loc_0_000003A4:
	tst.b app_0109(a6)
	beq.b loc_0_000003B0
	jsr loc_0_0000FB16.l
loc_0_000003B0:
	sf.b app_0955(a6)
	jsr loc_0_00009158.l
	jsr loc_0_000098AE.l
	jsr loc_0_00008A06.l
	tst.b $0127(a6)
	beq.b loc_0_000003D4
	move.b $010C(a6),d1
	beq.w loc_0_0000046E
loc_0_000003D4:
	jsr loc_0_00008E8C.l
	moveq.l #0,d1
	move.b $010C(a6),d1
	jsr loc_0_00008F04.l
	moveq.l #3,d0
	cmpi.b #1,$010C(a6)
	bne.b loc_0_000003F2
	addq.b #1,d0
loc_0_000003F2:
	jsr loc_0_00008E7A.l
	move.l app_0220(a6),d1
	subq.l #1,d1
	jsr loc_0_00008F04.l
	moveq.l #5,d0
	jsr loc_0_00008E7A.l
	move.l app_0224(a6),d1
	jsr loc_0_00008F04.l
	moveq.l #12,d0
	jsr loc_0_00008E7A.l
	jsr loc_0_0000962C.l
	moveq.l #22,d0
	tst.b app_0112(a6)
	bne.b loc_0_00000436
	moveq.l #18,d0
	tst.b app_0114(a6)
	beq.b loc_0_00000436
	moveq.l #17,d0
loc_0_00000436:
	jsr loc_0_00008E7A.l
	moveq.l #19,d0
	jsr loc_0_00008E7A.l
	moveq.l #0,d1
	move.w $0192(a6),d1
	beq.b loc_0_0000046E
	jsr loc_0_00008F04.l
	moveq.l #13,d0
	jsr loc_0_00008E7A.l
	moveq.l #0,d0
	move.w $0194(a6),d1
	jsr loc_0_00008F04.l
	moveq.l #14,d0
	jsr loc_0_00008E7A.l
loc_0_0000046E:
	jsr loc_0_0000916A.l
	jsr loc_0_0000ABC0.l
	move.l $018A(a6),d3
	beq.b loc_0_0000048A
	jsr loc_0_0000AFF2.l
	clr.l $018A(a6)
loc_0_0000048A:
	jsr loc_0_000090F2.l
	jsr loc_0_0000ACA4.l
loc_0_00000496:
	moveq.l #0,d0
	move.w d0,app_0218(a6)
	move.l d0,app_0224(a6)
	move.l d0,app_0220(a6)
	move.l d0,app_023C(a6)
	move.l d0,$015A(a6)
	move.l d0,$0162(a6)
	move.l d0,$018E(a6)
	move.w d0,app_087E(a6)
	move.w d0,app_0880(a6)
	move.l d0,app_0882(a6)
	move.b d0,$0106(a6)
	move.b d0,app_0112(a6)
	move.b d0,app_083B(a6)
	move.b d0,$0121(a6)
	sf.b $0123(a6)
	move.b d0,$0122(a6)
	sf.b $0124(a6)
	sf.b $012C(a6)
	st.b $012E(a6)
	sf.b $012D(a6)
	move.w #$200,$0130(a6)
	move.b d0,$0132(a6)
	move.b d0,$0133(a6)
	move.b #$1,app_085C(a6)
	move.b #$FF,app_086C(a6)
	sf.b $0125(a6)
	move.b d0,$012F(a6)
	move.w d0,$010E(a6)
	move.w #$FFFF,$0110(a6)
	move.b d0,app_0107(a6)
	move.l d0,app_0890(a6)
	move.w d0,app_0898(a6)
	move.w d0,app_089A(a6)
	move.l d0,app_084A(a6)
	moveq.l #1,d0
	move.l d0,app_0846(a6)
	st.b app_083A(a6)
	st.b app_0105(a6)
	move.w #$80,app_021E(a6)
	jsr loc_0_00008D82.l
	sf.b app_0114(a6)
	sf.b app_0115(a6)
	sf.b app_0118(a6)
	sf.b app_0117(a6)
	sf.b app_0101(a6)
	sf.b app_0119(a6)
	sf.b app_011D(a6)
	st.b app_011E(a6)
	st.b app_011F(a6)
	sf.b $0126(a6)
	move.b #$2E,app_0116(a6)
	move.b #$1,$0108(a6)
	bra.w loc_0_000078E0
loc_0_0000057A:
	tst.w app_087E(a6)
	bne.b loc_0_00000582
	rts
loc_0_00000582:
	move.w #$FFFF,app_0218(a6)
	moveq.l #50,d0
	jmp loc_0_00008486.l
loc_0_00000590:
	bsr.b loc_0_0000057A
	bsr.w loc_0_000079CC
	bsr.w loc_0_000079DA
	jsr loc_0_00008A06.l
	bsr.b loc_0_000005C2
	jsr loc_0_00008A5A.l
	cmpi.w #3,app_021C(a6)
	bne.b loc_0_000005B6
	jsr loc_0_0000A3F4.l
loc_0_000005B6:
	jsr loc_0_00009682.l
	clr.l $017A(a6)
	rts
loc_0_000005C2:
	movea.l $0172(a6),a3
	movea.l (a3),a3
	bsr.b loc_0_000005CC
	rts
loc_0_000005CC:
	tst.l (a3)
	beq.b loc_0_000005D8
	move.l a3,-(a7)
	movea.l (a3),a3
	bsr.b loc_0_000005CC
	movea.l (a7)+,a3
loc_0_000005D8:
	cmpi.b #9,$000D(a3)
	bne.b loc_0_000005E6
	movea.l $0008(a3),a2
	bsr.b loc_0_000005F8
loc_0_000005E6:
	tst.l $0004(a3)
	beq.b loc_0_000005F6
	move.l a3,-(a7)
	movea.l $0004(a3),a3
	bsr.b loc_0_000005CC
	movea.l (a7)+,a3
loc_0_000005F6:
	rts
loc_0_000005F8:
	tst.l (a2)
	beq.b loc_0_00000604
	move.l a2,-(a7)
	movea.l (a2),a2
	bsr.b loc_0_000005F8
	movea.l (a7)+,a2
loc_0_00000604:
	clr.l $0008(a2)
	tst.l $0004(a2)
	beq.b loc_0_00000618
	move.l a2,-(a7)
	movea.l $0004(a2),a2
	bsr.b loc_0_000005F8
	movea.l (a7)+,a2
loc_0_00000618:
	rts
loc_0_0000061A:
	tst.l app_0890(a6)
	bne.b loc_0_0000063E
	tst.b app_0101(a6)
	bne.b loc_0_00000662
	movea.l $017E(a6),a1
	movea.l $009E(a1),a0
	cmpa.l $00A2(a1),a0
	bcc.b loc_0_0000067E
loc_0_00000634:
	move.b (a0),d0
	cmp.b d0,d0
	rts
	dc.b $70,$FF,$4E,$75
loc_0_0000063E:
	tst.b app_0101(a6)
	beq.b loc_0_0000064E
	move.w app_0898(a6),d0
	cmp.w app_089A(a6),d0
	bhi.b loc_0_00000662
loc_0_0000064E:
	movea.l app_0890(a6),a1
	movea.l app_0894(a6),a0
	cmpa.l $0004(a1),a0
	bne.b loc_0_00000634
	movea.l $0008(a1),a0
	bra.b loc_0_00000634
loc_0_00000662:
	movea.l app_0882(a6),a2
	movea.l $0004(a2),a1
	movea.l $0010(a2),a0
	cmpa.l $0004(a1),a0
	bne.b loc_0_00000634
	movea.l $0008(a1),a1
	movea.l $0000(a1),a0
	bra.b loc_0_00000634
loc_0_0000067E:
	moveq.l #70,d0
	jmp loc_0_0000846E.l
	dc.b $4A,$FB,$69,$6E,$63,$6C,$75,$64,$65,$5F,$6C,$6F,$6E,$67,$6D,$61
	dc.b $63,$00
loc_0_00000698:
	tst.b app_0115(a6)
	beq.w loc_0_000006C6
loc_0_000006A0:
	bpl.b loc_0_000006A4
	rts
loc_0_000006A4:
	moveq.l #79,d0
	jmp loc_0_0000846E.l
loc_0_000006AC:
	tst.b app_0115(a6)
	bne.b loc_0_000006A0
	addq.l #1,app_0220(a6)
	tst.b app_0101(a6)
	bne.w loc_0_0000702A
	tst.l app_0890(a6)
	bne.w loc_0_0000743C
loc_0_000006C6:
	moveq.l #10,d1
	move.w #$FE,d2
	addq.w #1,app_0218(a6)
loc_0_000006D0:
	movea.l $017E(a6),a1
	movea.l $009E(a1),a4
	cmpa.l $00A2(a1),a4
	bcc.w loc_0_00000754
	move.w #$FC,d0
	moveq.l #10,d2
	move.l a4,app_0240(a6)
	movea.l a4,a2
loc_0_000006EC:
	cmp.b (a2)+,d2
	dbeq.w d0,loc_0_000006EC
	beq.b loc_0_0000070C
	cmpa.l $00A2(a1),a2
	bhi.b loc_0_0000071A
	move.b #$2A,-(a2)
	move.b #$A,-$0001(a2)
	move.l a2,$009E(a1)
	moveq.l #0,d0
	rts
loc_0_0000070C:
	cmpa.l $00A2(a1),a2
	bhi.b loc_0_0000071A
	move.l a2,$009E(a1)
	moveq.l #0,d0
	rts
loc_0_0000071A:
	move.l $00A6(a1),d1
	movea.l $0008(a1),a2
	adda.l d1,a2
	cmpa.l $00A2(a1),a2
	bne.b loc_0_00000776
	move.l $00A2(a1),d2
	sub.l a4,d2
	beq.b loc_0_00000754
	move.l d2,-(a7)
	subq.l #1,d2
	movea.l a4,a0
	movea.l $0008(a1),a2
	move.l a2,$009E(a1)
loc_0_00000740:
	move.b (a0)+,(a2)+
	dbf.w d2,loc_0_00000740
	move.l $00A6(a1),d1
	sub.l (a7)+,d1
	jsr loc_0_000089B0.l
	bra.b loc_0_0000076C
loc_0_00000754:
	movea.l $0008(a1),a2
	move.l a2,$009E(a1)
	adda.l $00A6(a1),a2
	cmpa.l $00A2(a1),a2
	bne.b loc_0_00000776
	jsr loc_0_000089BA.l
loc_0_0000076C:
	beq.w loc_0_000006D0
	jmp loc_0_0000846E.l
loc_0_00000776:
	move.w $009C(a1),app_0218(a6)
	clr.w $009C(a1)
	tst.b $0134(a6)
	beq.b loc_0_00000792
	tst.b app_0238(a6)
	beq.b loc_0_00000792
	move.b #$FE,$000E(a1)
loc_0_00000792:
	cmpi.b #12,$000D(a1)
	beq.b loc_0_000007AE
	move.l $0098(a1),d2
	beq.b loc_0_000007AE
	move.l a1,-(a7)
	jsr loc_0_0000AFB8.l
	movea.l (a7)+,a1
	clr.l $0098(a1)
loc_0_000007AE:
	move.l $0010(a1),$017E(a6)
	bne.w loc_0_00000698
	moveq.l #-1,d0
	rts
	dc.b $50,$EE,$01,$13,$4A,$2E,$02,$38,$67,$14,$B2,$3C,$00,$2B,$67,$18
	dc.b $B2,$3C,$00,$2D,$67,$0C,$72,$0A,$50,$EE,$01,$00,$4E,$75,$72,$0A
	dc.b $4E,$75,$53,$2E,$08,$3A,$60,$04,$52,$2E,$08,$3A,$5A,$EE,$01,$00
	dc.b $12,$1C
loc_0_000007EE:
	rts
loc_0_000007F0:
	tst.b app_0238(a6)
	bne.w loc_0_000008DC
loc_0_000007F8:
	tst.b $0129(a6)
	beq.w loc_0_000008C6
	tst.l $0182(a6)
	beq.w loc_0_000008C6
	cmpi.b #1,$0108(a6)
	bne.b loc_0_000007EE
	move.l $017E(a6),d0
	beq.b loc_0_000007EE
	move.b $0146(a6),d6
	movea.l d0,a0
	move.l $00AE(a0),d0
	beq.b loc_0_0000082A
	movea.l d0,a0
	cmp.b $0004(a0),d6
	beq.b loc_0_0000087A
loc_0_0000082A:
	movea.l $017E(a6),a0
	lea.l $00AA(a0),a0
loc_0_00000832:
	move.l (a0),d0
	beq.b loc_0_00000842
	movea.l d0,a0
	cmp.b $0004(a0),d6
	beq.b loc_0_00000872
	lea.l (a0),a0
	bra.b loc_0_00000832
loc_0_00000842:
	move.l a0,-(a7)
	moveq.l #32,d1
	jsr loc_0_000090BA.l
	movea.l (a7)+,a1
	move.l a0,(a1)
	clr.l (a0)
	move.b d6,$0004(a0)
	move.l #$FFFFFFFF,$0006(a0)
	clr.l $000A(a0)
	clr.w $0012(a0)
	clr.l $000E(a0)
	clr.l $0014(a0)
	clr.l $0018(a0)
loc_0_00000872:
	movea.l $017E(a6),a1
	move.l a0,$00AE(a1)
loc_0_0000087A:
	move.l app_023C(a6),d0
	sub.l $0182(a6),d0
	cmp.l $0006(a0),d0
	beq.b loc_0_000008C6
	moveq.l #0,d1
	move.w app_0218(a6),d1
	cmp.l $000A(a0),d1
	beq.b loc_0_000008C6
	tst.b $012A(a6)
	beq.b loc_0_000008BA
	addq.w #1,$0012(a0)
	lea.l $000A(a0),a1
	move.l d0,-(a7)
	move.l d1,d0
	jsr loc_0_00008ADA.l
	move.l (a7)+,d0
	lea.l $0006(a0),a1
	jsr loc_0_00008ADA.l
	bra.b loc_0_000008C6
loc_0_000008BA:
	addq.l #8,$0018(a0)
	move.l d0,$0006(a0)
	move.l d1,$000A(a0)
loc_0_000008C6:
	tst.b $0102(a6)
	bne.w loc_0_000009A4
	tst.b app_021A(a6)
	beq.w loc_0_00000996
	bra.w loc_0_000009A4
loc_0_000008DA:
	rts
loc_0_000008DC:
	tst.b $0129(a6)
	beq.w loc_0_00000972
	tst.l $0182(a6)
	beq.w loc_0_00000972
	cmpi.b #1,$0108(a6)
	bne.b loc_0_00000972
	move.l $017E(a6),d0
	beq.b loc_0_000008DA
	movea.l d0,a0
	move.b $0146(a6),d6
	movea.l $00AE(a0),a0
	cmp.b $0004(a0),d6
	beq.b loc_0_0000091E
	movea.l $017E(a6),a1
	lea.l $00AA(a1),a0
loc_0_00000912:
	movea.l (a0),a0
	cmp.b $0004(a0),d6
	bne.b loc_0_00000912
	move.l a0,$00AE(a1)
loc_0_0000091E:
	move.l app_023C(a6),d0
	sub.l $0182(a6),d0
	cmp.l $0006(a0),d0
	beq.b loc_0_00000972
	moveq.l #0,d1
	move.w app_0218(a6),d1
	cmp.l $000A(a0),d1
	beq.b loc_0_00000972
	tst.b $012A(a6)
	beq.b loc_0_0000095E
	lea.l $000A(a0),a1
	move.l d0,-(a7)
	move.l d1,d0
	jsr loc_0_00008B10.l
	move.l a1,$0014(a0)
	move.l (a7)+,d0
	lea.l $0006(a0),a1
	jsr loc_0_00008B10.l
	bra.b loc_0_0000096E
loc_0_0000095E:
	movea.l $0014(a0),a1
	move.l d0,$0006(a0)
	move.l d1,$000A(a0)
	move.l d1,(a1)+
	move.l d0,(a1)+
loc_0_0000096E:
	move.l a1,$0014(a0)
loc_0_00000972:
	tst.b $0102(a6)
	bne.b loc_0_000009A4
	tst.b $0100(a6)
	beq.b loc_0_00000996
	tst.b app_0113(a6)
	bne.b loc_0_00000996
	tst.b app_0101(a6)
	beq.b loc_0_000009A4
	tst.b app_0118(a6)
	bne.b loc_0_000009A4
	tst.b app_0117(a6)
	bne.b loc_0_000009A4
loc_0_00000996:
	sf.b app_0113(a6)
	clr.b app_083B(a6)
	sf.b app_0118(a6)
	rts
loc_0_000009A4:
	sf.b $0102(a6)
	jsr loc_0_000092A0.l
	bra.b loc_0_00000996
	dc.b $50,$EE,$01,$13,$72,$0A,$4A,$2E,$02,$38,$67,$08,$51,$EE,$01,$00
	dc.b $50,$EE,$08,$3A,$4E,$75
loc_0_000009C6:
	rts
loc_0_000009C8:
	movea.l app_024C(a6),a5
	move.l a5,app_0250(a6)
	clr.l $0182(a6)
	sf.b app_010D(a6)
	move.b (a4)+,d1
	cmp.b #$A,d1
	beq.b loc_0_000009C6
	cmp.b #$9,d1
	beq.b loc_0_000009EC
	cmp.b #$20,d1
	bne.b loc_0_00000A08
loc_0_000009EC:
	clr.l app_03E8(a6)
	bra.w loc_0_00000A2A
loc_0_000009F4:
	cmp.b #$3B,d1
	beq.w loc_0_00000C44
	cmp.b #$2A,d1
	beq.w loc_0_00000C44
	bra.w loc_0_00008432
loc_0_00000A08:
	st.b d2
	lea.l app_03E8(a6),a0
	clr.b $0004(a0)
	bsr.w loc_0_000076B8
	bne.b loc_0_000009F4
	cmp.b #$3A,d1
	bne.b loc_0_00000A2C
loc_0_00000A1E:
	move.b (a4)+,d1
	cmp.b #$3A,d1
	bne.b loc_0_00000A2C
	st.b app_03EC(a6)
loc_0_00000A2A:
	move.b (a4)+,d1
loc_0_00000A2C:
	cmp.b #$9,d1
	beq.b loc_0_00000A2A
	cmp.b #$20,d1
	beq.b loc_0_00000A2A
	cmp.b #$3D,d1
	beq.w loc_0_0000748A
	subq.l #1,a4
	move.l a4,-(a7)
	moveq.l #0,d2
	movea.l #loc_0_0000B21E,a0
	movea.l #loc_0_0000CD3C,a1
	movea.l #loc_0_0000BA08,a2
	moveq.l #0,d1
	move.b (a4)+,d1
	add.w d1,d1
	add.w $0(a0,d2.w),d1
	cmp.w $0(a1,d1.w),d2
	bne.b loc_0_00000AB2
	move.w $0(a2,d1.w),d2
	bmi.b loc_0_00000AE8
	moveq.l #0,d1
	move.b (a4)+,d1
	add.w d1,d1
	add.w $0(a0,d2.w),d1
	cmp.w $0(a1,d1.w),d2
	bne.b loc_0_00000AB2
	move.w $0(a2,d1.w),d2
	bmi.b loc_0_00000AE8
	moveq.l #0,d1
	move.b (a4)+,d1
	add.w d1,d1
	add.w $0(a0,d2.w),d1
	cmp.w $0(a1,d1.w),d2
	bne.b loc_0_00000AB2
	move.w $0(a2,d1.w),d2
	bmi.b loc_0_00000AE8
loc_0_00000A9A:
	moveq.l #0,d1
	move.b (a4)+,d1
	add.w d1,d1
	add.w $0(a0,d2.w),d1
	cmp.w $0(a1,d1.w),d2
	bne.b loc_0_00000AB2
	move.w $0(a2,d1.w),d2
	bpl.b loc_0_00000A9A
	bra.b loc_0_00000AE8
loc_0_00000AB2:
	move.w d2,d1
	add.w d1,d1
	add.w d1,d2
	movea.l #loc_0_0000E070,a0
	adda.w d2,a0
	tst.w $0002(a0)
	beq.b loc_0_00000AE8
	move.b -$0001(a4),d1
	cmp.b #$2E,d1
	beq.b loc_0_00000AE2
	cmp.b #$A,d1
	beq.b loc_0_00000AE2
	cmp.b #$9,d1
	beq.b loc_0_00000AE2
	cmp.b #$20,d1
	bne.b loc_0_00000AE8
loc_0_00000AE2:
	move.l (a7)+,d2
	bra.w loc_0_000074A2
loc_0_00000AE8:
	movea.l (a7)+,a4
	move.b (a4)+,d1
	cmp.b #$A,d1
	beq.w loc_0_00000C44
	cmp.b #$3B,d1
	beq.w loc_0_00000C44
	cmp.b #$2A,d1
	beq.w loc_0_00000C44
	lea.l app_0362(a6),a0
	bsr.w loc_0_00007680
	bne.w loc_0_00008432
	movea.l $0172(a6),a2
	move.l a1,d4
	movem.l d2/a3-a5,-(a7)
	bsr.w loc_0_00000B88
	movem.l (a7)+,d2/a3-a5
	beq.w loc_0_00006E5C
	movea.l d4,a4
	move.b -$0001(a4),d1
	cmp.b #$3A,d1
	bne.w loc_0_00008446
	lea.l app_03E8(a6),a1
	tst.l (a1)
	bne.w loc_0_00008446
	move.b d2,$0005(a0)
	bsr.b loc_0_00000B4E
	movea.l a1,a0
	clr.b $0004(a0)
	bra.w loc_0_00000A1E
loc_0_00000B4E:
	move.b $0005(a0),$0005(a1)
	tst.b app_00FE(a6)
	bne.b loc_0_00000B64
	move.l (a0),(a1)
	move.b $0006(a0),$0006(a1)
	rts
loc_0_00000B64:
	move.b $0005(a0),d0
	lea.l $0006(a1),a2
	move.l a2,(a1)
	addq.w #6,a0
loc_0_00000B70:
	move.b (a0)+,(a2)+
	subq.b #1,d0
	bne.b loc_0_00000B70
	rts
loc_0_00000B78:
	move.l (a2),d0
	beq.b loc_0_00000BC8
	movea.l d0,a1
	move.b $0016(a0),d2
	lea.l $0017(a0),a5
	bra.b loc_0_00000B9C
loc_0_00000B88:
	move.l (a2),d0
	beq.b loc_0_00000BC8
	movea.l d0,a1
	move.b $0005(a0),d2
	movea.l (a0),a5
	bra.b loc_0_00000B9C
loc_0_00000B96:
	move.l (a1),d0
	beq.b loc_0_00000BC4
	movea.l d0,a1
loc_0_00000B9C:
	cmp.b $0016(a1),d2
	bcs.b loc_0_00000B96
	bhi.b loc_0_00000BB8
	move.b d2,d3
	lea.l $0017(a1),a3
	movea.l a5,a4
loc_0_00000BAC:
	cmpm.b (a3)+,(a4)+
	bcs.b loc_0_00000B96
	bhi.b loc_0_00000BB8
	subq.b #1,d3
	bne.b loc_0_00000BAC
	rts
loc_0_00000BB8:
	move.l $0004(a1),d0
	beq.b loc_0_00000BC2
	movea.l d0,a1
	bra.b loc_0_00000B9C
loc_0_00000BC2:
	addq.w #4,a1
loc_0_00000BC4:
	moveq.l #3,d0
	rts
loc_0_00000BC8:
	movea.l a2,a1
	moveq.l #3,d0
	rts
loc_0_00000BCE:
	movem.l a3-a5,-(a7)
	move.l $015A(a6),d0
	beq.b loc_0_00000BE2
	movea.l d0,a2
	bsr.b loc_0_00000B88
	beq.b loc_0_00000BFC
	move.l a1,$015E(a6)
loc_0_00000BE2:
	movea.l $0162(a6),a2
	bsr.b loc_0_00000B88
	beq.b loc_0_00000BFC
	move.l a1,$0166(a6)
	movea.l $016A(a6),a2
	bsr.b loc_0_00000B88
	beq.b loc_0_00000BFC
	move.l a1,$016E(a6)
	moveq.l #-1,d0
loc_0_00000BFC:
	movem.l (a7)+,a3-a5
	rts
loc_0_00000C02:
	bsr.b loc_0_00000BCE
	bne.w loc_0_0000843A
	bset.b #6,$000C(a1)
	bne.w loc_0_00008436
	move.b $0108(a6),d3
	cmp.b $000D(a1),d3
	bne.w loc_0_00008436
	cmp.l $0008(a1),d4
	bne.w loc_0_0000843E
	move.b $0017(a1),d0
	cmp.b app_0116(a6),d0
	beq.b loc_0_00000C42
	tst.b $0004(a0)
	beq.b loc_0_00000C3A
	bsr.w loc_0_00004E4C
loc_0_00000C3A:
	lea.l $0010(a1),a0
	move.l a0,$015A(a6)
loc_0_00000C42:
	rts
loc_0_00000C44:
	move.l app_023C(a6),d4
	lea.l app_03E8(a6),a0
	tst.l (a0)
	bne.b loc_0_00000C84
	rts
loc_0_00000C52:
	btst.b #0,app_023F(a6)
	bne.w loc_0_00000C5E
	rts
loc_0_00000C5E:
	jmp loc_0_00009746.l
loc_0_00000C64:
	lea.l app_03E8(a6),a0
	tst.l (a0)
	beq.b loc_0_00000C52
	move.l app_023C(a6),d4
	btst #0,d4
	beq.b loc_0_00000C84
	jsr loc_0_00009746.l
	lea.l app_03E8(a6),a0
	move.l app_023C(a6),d4
loc_0_00000C84:
	tst.b app_0238(a6)
	bne.w loc_0_00000C02
	bsr.w loc_0_00000BCE
	beq.w loc_0_00008436
	move.b $0108(a6),d3
	move.b $0006(a0),d0
	cmp.b app_0116(a6),d0
	beq.b loc_0_00000CAC
	pea.l loc_0_00000C3A(pc)
	lea.l $0162(a6),a2
	bra.b loc_0_00000CB6
loc_0_00000CAC:
	lea.l $015A(a6),a2
	tst.l (a2)
	beq.w loc_0_00008442
loc_0_00000CB6:
	movea.l $0004(a2),a1
loc_0_00000CBA:
	cmpi.w #152,$0148(a6)
	bcc.b loc_0_00000CD0
	movem.l d3/a0-a1,-(a7)
	jsr loc_0_000090A8.l
	movem.l (a7)+,d3/a0-a1
loc_0_00000CD0:
	movea.l $013A(a6),a2
	move.l a2,(a1)
	movea.l a2,a1
	moveq.l #0,d0
	move.l d0,(a2)
	move.l d0,$0004(a2)
	move.l d4,$0008(a2)
	move.b d3,$000D(a2)
	move.w d0,$0014(a2)
	move.b d0,$000C(a2)
	move.b $0146(a6),$000E(a2)
	move.l d0,$0010(a2)
	lea.l $0016(a2),a2
	move.b $0005(a0),d0
	movea.l (a0),a0
	move.b d0,(a2)+
loc_0_00000D06:
	move.b (a0)+,(a2)+
	subq.b #1,d0
	bne.b loc_0_00000D06
	move.l a2,d0
	sub.l a1,d0
	addq.l #1,d0
	bclr #0,d0
	sub.w d0,$0148(a6)
	add.l d0,$013A(a6)
	rts
loc_0_00000D20:
	cmp.w $0148(a6),d0
	bcs.b loc_0_00000D34
	movem.l d0/d3/a0-a1,-(a7)
	jsr loc_0_000090A8.l
	movem.l (a7)+,d0/d3/a0-a1
loc_0_00000D34:
	move.l d0,-(a7)
	bsr.b loc_0_00000CBA
	sub.l d0,$013A(a6)
	add.w d0,$0148(a6)
	move.l (a7)+,d0
	sub.w d0,$0148(a6)
	add.l d0,$013A(a6)
	rts
	dc.b $22,$6A,$00,$04,$0C,$6E,$00,$98,$01,$48,$64,$0E,$48,$E7,$10,$C0
	dc.b $4E,$B9
	dc.l loc_0_000090A8
	dc.b $4C,$DF,$03,$08,$24,$6E,$01,$3A,$22,$8A,$22,$4A,$70,$00,$24,$80
	dc.b $25,$40,$00,$04,$25,$44,$00,$08,$15,$43,$00,$0D,$35,$40,$00,$14
	dc.b $15,$40,$00,$0C,$15,$6E,$01,$46,$00,$0E,$25,$40,$00,$10,$45,$EA
	dc.b $00,$16,$10,$28,$00,$05,$20,$50,$14,$C0,$14,$D8,$53,$00,$66,$FA
	dc.b $20,$0A,$90,$89,$52,$80,$08,$80,$00,$00,$91,$6E,$01,$48,$D1,$AE
	dc.b $01,$3A,$4E,$75
loc_0_00000DB6:
	bsr.b loc_0_00000DCC
	cmp.b #$F,d3
	bcs.b loc_0_00000DCA
	cmp.b #$13,d3
	bcc.b loc_0_00000DCA
	moveq.l #98,d0
	bra.w loc_0_00008486
loc_0_00000DCA:
	rts
loc_0_00000DCC:
	bsr.w loc_0_000079E6
	lea.l app_0628(a6),a0
	clr.w (a0)
	lea.l app_0650(a6),a0
	clr.w (a0)
	moveq.l #0,d4
	movem.l d5-d7,-(a7)
	moveq.l #1,d5
	bsr.w loc_0_00001208
	cmp.b #$1,d7
	bne.b loc_0_00000E2C
	movem.l d2-d3,-(a7)
	addq.b #1,d5
	bsr.w loc_0_00001208
	cmp.b #$4,d7
	bcs.w loc_0_00000E50
	cmp.b #$16,d7
	bcc.w loc_0_00000E50
	lea.l app_0628(a6),a0
	move.w (a0),d0
	addq.w #2,(a0)+
	move.w #$0,$0(a0,d0.w)
	lea.l app_0650(a6),a0
	move.w (a0),d0
	addq.w #8,(a0)+
	move.l (a7)+,$0(a0,d0.w)
	move.l (a7)+,$4(a0,d0.w)
	bsr.w loc_0_00000EDA
	bra.b loc_0_00000E3E
loc_0_00000E2C:
	lea.l app_0628(a6),a0
	move.w (a0),d0
	addq.w #2,(a0)+
	move.w #$0,$0(a0,d0.w)
	bsr.w loc_0_00000F0A
loc_0_00000E3E:
	movem.l (a7)+,d5-d7
	tst.w app_0628(a6)
	bne.b loc_0_00000E62
	tst.w app_0650(a6)
	bne.b loc_0_00000E62
	rts
loc_0_00000E50:
	movem.l (a7)+,d2-d3
	movem.l (a7)+,d5-d7
	movea.l a0,a4
	move.b -$0001(a4),d1
	moveq.l #0,d0
	rts
loc_0_00000E62:
	moveq.l #18,d0
	bra.w loc_0_00008482
	dc.b $11,$2B,$12,$2D,$04,$2A,$05,$2F,$02,$28,$03,$29,$13,$7E,$08,$3D
	dc.b $0E,$26,$EA,$21,$10,$5E,$0F,$7C,$FE,$24,$FA,$25,$F8,$40,$F4,$27
	dc.b $F4,$22,$00
loc_0_00000E8B:
	dc.b $00,$00,$00,$00,$04,$04,$16,$16,$14,$14,$14,$14,$14,$14,$12
	dc.w loc_0_000020B4-loc_0_00000EA2	; lookup_table
	dc.w loc_0_000010A4-loc_0_00000EA2
	dc.w loc_0_00002BC0-loc_0_00000EA2
	dc.w loc_0_00002CA2-loc_0_00000EA2
loc_0_00000EA2:
	dc.w loc_0_000010DA-loc_0_00000EA2	; lookup_table
	dc.w loc_0_000010F8-loc_0_00000EA2
	dc.w loc_0_00001120-loc_0_00000EA2
	dc.w loc_0_00001124-loc_0_00000EA2
	dc.w loc_0_00001128-loc_0_00000EA2
	dc.w loc_0_00001150-loc_0_00000EA2
	dc.w loc_0_00001156-loc_0_00000EA2
	dc.w loc_0_0000115C-loc_0_00000EA2
	dc.w loc_0_00001162-loc_0_00000EA2
	dc.w loc_0_00001168-loc_0_00000EA2
	dc.w loc_0_00001114-loc_0_00000EA2
	dc.w loc_0_00001118-loc_0_00000EA2
	dc.w loc_0_0000111C-loc_0_00000EA2
	dc.w loc_0_00001050-loc_0_00000EA2
	dc.w loc_0_00001096-loc_0_00000EA2
	dc.w loc_0_0000116E-loc_0_00000EA2
	dc.w loc_0_0000117A-loc_0_00000EA2
	dc.w loc_0_00001178-loc_0_00000EA2
loc_0_00000EC6:
	lea.l app_0628(a6),a0
	move.w (a0),d0
	addq.w #2,(a0)+
	move.w #$0,$0(a0,d0.w)
	moveq.l #1,d5
	bsr.w loc_0_00001208
loc_0_00000EDA:
	cmp.b #$2,d5
	bne.b loc_0_00000EF0
	cmp.b #$4,d7
	bcs.w loc_0_00000FC4
	cmp.b #$16,d7
	bcc.w loc_0_00000FC4
loc_0_00000EF0:
	cmp.b #$1,d7
	bne.b loc_0_00000F0A
loc_0_00000EF6:
	lea.l app_0650(a6),a0
	move.w (a0),d0
	addq.w #8,(a0)+
	move.l d2,$0(a0,d0.w)
	move.l d3,$4(a0,d0.w)
	bra.w loc_0_00000FBA
loc_0_00000F0A:
	cmp.b #$2,d7
	beq.w loc_0_00000F8A
	cmp.b #$4,d7
	bcs.w loc_0_00000FCA
	cmp.b #$16,d7
	bcc.w loc_0_00000FCA
	cmp.b #$1,d5
	bne.b loc_0_00000F60
	cmp.b #$11,d7
	beq.b loc_0_00000F5A
	cmp.b #$12,d7
	beq.b loc_0_00000F5E
	cmp.b #$4,d7
	beq.b loc_0_00000F44
	cmp.b #$13,d7
	bne.w loc_0_00000E62
	bra.b loc_0_00000F60
loc_0_00000F44:
	move.l app_023C(a6),d2
	moveq.l #0,d3
	move.b $0108(a6),d3
	cmp.b #$1,d3
	bne.b loc_0_00000F58
	addq.b #1,app_010B(a6)
loc_0_00000F58:
	bra.b loc_0_00000EF6
loc_0_00000F5A:
	moveq.l #21,d7
	bra.b loc_0_00000F60
loc_0_00000F5E:
	moveq.l #20,d7
loc_0_00000F60:
	lea.l loc_0_00000E8B(pc),a2
	lea.l app_0628(a6),a0
	move.w (a0),d0
	move.w $0(a0,d0.w),d6
	move.b $0(a2,d6.w),d6
	cmp.b $0(a2,d7.w),d6
	bge.b loc_0_00000F80
	addq.w #2,(a0)+
	move.w d7,$0(a0,d0.w)
	bra.b loc_0_00000F86
loc_0_00000F80:
	bsr.w loc_0_00000FFA
	bra.b loc_0_00000F60
loc_0_00000F86:
	moveq.l #0,d5
	bra.b loc_0_00000FBA
loc_0_00000F8A:
	bsr.w loc_0_00000EC6
	bsr.w loc_0_00001208
	lea.l app_0650(a6),a0
	move.w (a0),d0
	addq.w #8,(a0)+
	move.l d2,$0(a0,d0.w)
	move.l d3,$4(a0,d0.w)
	tst.w d3
	bpl.b loc_0_00000FAC
	moveq.l #42,d0
	bsr.w loc_0_00008486
loc_0_00000FAC:
	cmp.b #$3,d7
	beq.b loc_0_00000FB8
	moveq.l #19,d0
	bra.w loc_0_00008482
loc_0_00000FB8:
	moveq.l #1,d5
loc_0_00000FBA:
	addq.w #1,d5
	bsr.w loc_0_00001208
	bra.w loc_0_00000EDA
loc_0_00000FC4:
	movea.l a0,a4
	move.b -$0001(a4),d1
loc_0_00000FCA:
	lea.l loc_0_00000E8B(pc),a2
loc_0_00000FCE:
	lea.l app_0628(a6),a0
	move.w (a0),d0
	tst.w $0(a0,d0.w)
	beq.b loc_0_00000FE0
	bsr.w loc_0_00000FFA
	bra.b loc_0_00000FCE
loc_0_00000FE0:
	subq.w #2,app_0628(a6)
	lea.l app_0650(a6),a0
	subq.w #8,(a0)
	move.w (a0)+,d0
	move.l $0(a0,d0.w),d2
	move.l $4(a0,d0.w),d3
	rts
loc_0_00000FF6:
	bra.w loc_0_00000E62
loc_0_00000FFA:
	lea.l app_0650(a6),a0
	subq.w #8,(a0)
	bcs.b loc_0_00000FF6
	move.w (a0)+,d0
	move.l $0(a0,d0.w),d2
	move.l $4(a0,d0.w),d3
	move.w d1,-(a7)
	lea.l app_0628(a6),a1
	subq.w #2,(a1)
	move.w (a1)+,d1
	move.w $0(a1,d1.w),d1
	cmp.b #$13,d1
	bcc.b loc_0_00001032
	subq.w #8,-(a0)
	bcs.b loc_0_00000FF6
	move.w (a0)+,d0
	move.l $4(a0,d0.w),d6
	move.l $0(a0,d0.w),d0
	exg d0,d2
	exg d6,d3
loc_0_00001032:
	lea.l loc_0_00000EA2(pc),a1
	add.w d1,d1
	move.w -$8(a1,d1.w),d1
	jsr $0(a1,d1.w)
	move.w (a7)+,d1
	move.w -(a0),d0
	addq.w #8,(a0)+
	move.l d2,$0(a0,d0.w)
	move.l d3,$4(a0,d0.w)
	rts
loc_0_00001050:
	add.l d0,d2
	cmp.b #$1,d3
	beq.b loc_0_00001066
	cmp.b #$1,d6
	beq.b loc_0_0000106C
loc_0_0000105E:
	andi.w #65280,d6
	or.w d6,d3
	rts
loc_0_00001066:
	cmp.b #$1,d6
	beq.b loc_0_00001072
loc_0_0000106C:
	move.b #$1,d3
	bra.b loc_0_0000105E
loc_0_00001072:
	tst.b app_0107(a6)
	bne.b loc_0_00001086
	tst.b app_0238(a6)
	beq.b loc_0_0000108A
loc_0_0000107E:
	moveq.l #21,d0
loc_0_00001080:
	bsr.w loc_0_00008486
loc_0_00001084:
	st.b d4
loc_0_00001086:
	moveq.l #2,d3
	rts
loc_0_0000108A:
	tst.b $0158(a6)
	bne.b loc_0_0000107E
	bra.b loc_0_00001084
loc_0_00001092:
	moveq.l #20,d0
	bra.b loc_0_00001080
loc_0_00001096:
	sub.l d0,d2
	move.w d3,d0
	or.w d6,d0
	andi.w #32768,d0
	tst.w d6
	bmi.b loc_0_000010D4
loc_0_000010A4:
	cmp.b #$1,d6
	bne.b loc_0_000010C0
	btst.b #1,app_021C(a6)
	bne.b loc_0_000010BC
	btst #15,d3
	beq.b loc_0_000010BC
	add.l app_023C(a6),d2
loc_0_000010BC:
	subq.b #2,app_010B(a6)
loc_0_000010C0:
	cmp.b d3,d6
	beq.b loc_0_000010CC
	cmp.b #$1,d6
	bne.b loc_0_000010D0
	bsr.b loc_0_00001072
loc_0_000010CC:
	move.b #$2,d3
loc_0_000010D0:
	or.w d0,d3
	rts
loc_0_000010D4:
	bsr.w loc_0_00007A20
	bra.b loc_0_000010C0
loc_0_000010DA:
	bsr.b loc_0_000010E4
	bsr.w loc_0_0000117E
	moveq.l #2,d3
	rts
loc_0_000010E4:
	cmp.b #$1,d6
	beq.b loc_0_00001072
	or.w d3,d6
	bmi.b loc_0_00001092
	cmp.b #$1,d3
	beq.w loc_0_00001072
	rts
loc_0_000010F8:
	bsr.b loc_0_000010E4
	move.l d7,-(a7)
	bsr.w loc_0_000011B2
	movem.l (a7)+,d7
	bne.b loc_0_00001108
	rts
loc_0_00001108:
	tst.b app_0238(a6)
	bne.w loc_0_00001080
	bra.w loc_0_0000108A
loc_0_00001114:
	and.l d0,d2
	bra.b loc_0_000010E4
loc_0_00001118:
	or.l d0,d2
	bra.b loc_0_000010E4
loc_0_0000111C:
	eor.l d0,d2
	bra.b loc_0_000010E4
loc_0_00001120:
	lsl.l d0,d2
	bra.b loc_0_000010E4
loc_0_00001124:
	lsr.l d0,d2
	bra.b loc_0_000010E4
loc_0_00001128:
	cmp.l d0,d2
	seq.b d2
loc_0_0000112C:
	ext.w d2
	ext.l d2
	move.w d3,d0
	or.w d6,d0
	bmi.w loc_0_00001092
	cmp.b d3,d6
	beq.b loc_0_0000114C
	cmp.b #$1,d3
	beq.w loc_0_00001072
	cmp.b #$1,d6
	beq.w loc_0_00001072
loc_0_0000114C:
	moveq.l #2,d3
	rts
loc_0_00001150:
	cmp.l d0,d2
	sne.b d2
	bra.b loc_0_0000112C
loc_0_00001156:
	cmp.l d0,d2
	slt.b d2
	bra.b loc_0_0000112C
loc_0_0000115C:
	cmp.l d0,d2
	sgt.b d2
	bra.b loc_0_0000112C
loc_0_00001162:
	cmp.l d0,d2
	sle.b d2
	bra.b loc_0_0000112C
loc_0_00001168:
	cmp.l d0,d2
	sge.b d2
	bra.b loc_0_0000112C
loc_0_0000116E:
	not.l d2
loc_0_00001170:
	cmp.w #$1,d3
	beq.w loc_0_00001072
loc_0_00001178:
	rts
loc_0_0000117A:
	neg.l d2
	bra.b loc_0_00001170
loc_0_0000117E:
	move.l d2,d6
	eor.l d0,d6
	tst.l d2
	bgt.b loc_0_00001188
	neg.l d2
loc_0_00001188:
	tst.l d0
	bgt.b loc_0_0000118E
	neg.l d0
loc_0_0000118E:
	move.l d2,d3
	swap.w d3
	mulu.w d0,d2
	swap.w d0
	tst.w d3
	beq.b loc_0_0000119E
	swap.w d0
	bra.b loc_0_000011A4
loc_0_0000119E:
	tst.w d0
	beq.b loc_0_000011AA
	swap.w d3
loc_0_000011A4:
	mulu.w d3,d0
	swap.w d0
	add.l d0,d2
loc_0_000011AA:
	tst.l d6
	bpl.b loc_0_000011B0
	neg.l d2
loc_0_000011B0:
	rts
loc_0_000011B2:
	tst.l d0
	beq.b loc_0_00001200
	move.l d2,d6
	eor.l d0,d6
	move.l d6,-(a7)
	move.l d2,-(a7)
	tst.l d0
	bpl.b loc_0_000011C4
	neg.l d0
loc_0_000011C4:
	tst.l d2
	bpl.b loc_0_000011CA
	neg.l d2
loc_0_000011CA:
	moveq.l #31,d6
	move.l d0,d7
	moveq.l #0,d0
loc_0_000011D0:
	add.l d7,d7
	dbcs.w d6,loc_0_000011D0
	roxr.l #1,d7
	subi.w #31,d6
	neg.w d6
loc_0_000011DE:
	add.l d0,d0
	cmp.l d7,d2
	bcs.b loc_0_000011E8
	addq.l #1,d0
	sub.l d7,d2
loc_0_000011E8:
	lsr.l #1,d7
	dbf.w d6,loc_0_000011DE
	move.l (a7)+,d6
	bpl.b loc_0_000011F4
	neg.l d2
loc_0_000011F4:
	move.l (a7)+,d6
	bpl.b loc_0_000011FA
	neg.l d0
loc_0_000011FA:
	exg d0,d2
	cmp.b d0,d0
	rts
loc_0_00001200:
	moveq.l #61,d0
	rts
	dc.b $20,$4C,$4E,$75
loc_0_00001208:
	moveq.l #0,d7
	ext.w d1
	bmi.b loc_0_00001232
	move.b loc_0_00001252(pc,d1.w),d7
	beq.b loc_0_00001220
	bpl.b loc_0_00001226
	cmp.b #$FF,d7
	bne.b loc_0_0000123C
	bra.w loc_0_00001246
loc_0_00001220:
	movea.l a4,a0
	moveq.l #22,d7
	rts
loc_0_00001226:
	cmp.b #$1,d7
	beq.b loc_0_00001232
	movea.l a4,a0
	move.b (a4)+,d1
	rts
loc_0_00001232:
	movem.l d5-d6/a1-a2,-(a7)
	move.l a4,-(a7)
	bra.w loc_0_000012D2
loc_0_0000123C:
	movem.l d5-d6/a1-a2,-(a7)
	move.l a4,-(a7)
	bra.w loc_0_000013B8
loc_0_00001246:
	movem.l d5-d6/a1-a2,-(a7)
	move.l a4,-(a7)
	moveq.l #0,d2
	bra.w loc_0_00001324
loc_0_00001252:
	dcb.b $21,$00	; lookup_table
	dc.b $EA,$F4,$00,$FE,$FA,$0E,$F4,$02,$03,$04,$11,$00,$12,$01,$05	; lookup_table
	dcb.b $A,$FF	; lookup_table
	dc.b $00,$00,$F2,$08,$EE,$00,$F8	; lookup_table
	dcb.b $1A,$01	; lookup_table
	dc.b $00,$00,$00,$10,$01,$00	; lookup_table
	dcb.b $1A,$01	; lookup_table
	dc.b $00,$0F,$00,$13,$00	; lookup_table
loc_0_000012D2:
	lea.l app_046E(a6),a0
	bsr.w loc_0_000076B8
	beq.w loc_0_00001530
	moveq.l #22,d7
	bra.b loc_0_0000131C
loc_0_000012E2:
	move.b (a4)+,d1
	cmp.b #$3D,d1
	beq.b loc_0_00001300
	moveq.l #15,d7
	bra.b loc_0_0000131C
loc_0_000012EE:
	moveq.l #10,d7
	move.b (a4)+,d1
	cmp.b #$3C,d1
	beq.b loc_0_00001318
	cmp.b #$3E,d1
	beq.b loc_0_00001300
	bra.b loc_0_0000130E
loc_0_00001300:
	moveq.l #9,d7
	bra.b loc_0_0000131A
loc_0_00001304:
	moveq.l #11,d7
	move.b (a4)+,d1
	cmp.b #$3E,d1
	beq.b loc_0_00001318
loc_0_0000130E:
	cmp.b #$3D,d1
	bne.b loc_0_0000131C
	addq.w #2,d7
	bra.b loc_0_0000131A
loc_0_00001318:
	subq.w #4,d7
loc_0_0000131A:
	move.b (a4)+,d1
loc_0_0000131C:
	movea.l (a7)+,a0
	movem.l (a7)+,d5-d6/a1-a2
	rts
loc_0_00001324:
	move.b $012F(a6),d7
	beq.b loc_0_00001330
	subq.l #1,a4
	bra.w loc_0_000013B8
loc_0_00001330:
	lea.l -$0001(a4),a0
loc_0_00001334:
	add.l d2,d2
	move.l d2,d0
	add.l d0,d0
	add.l d0,d0
	add.l d0,d2
	subi.b #'0',d1
	andi.l #15,d1
	add.l d1,d2
	move.b (a4)+,d1
	cmp.b #$3A,d1
	bcc.b loc_0_00001358
	cmp.b #$30,d1
	bcc.b loc_0_00001334
loc_0_00001358:
	moveq.l #1,d7
	moveq.l #2,d3
	cmp.b #$24,d1
	bne.b loc_0_0000131C
	bra.w loc_0_0000166A
loc_0_00001366:
	moveq.l #4,d0
	move.b d1,d3
loc_0_0000136A:
	move.b (a4)+,d1
	cmp.b #$A,d1
	beq.w loc_0_00001434
	cmp.b d3,d1
	bne.b loc_0_00001382
	move.b (a4)+,d1
	cmp.b d3,d1
	beq.b loc_0_00001382
	moveq.l #2,d3
	bra.b loc_0_0000131C
loc_0_00001382:
	subq.b #1,d0
	bcs.w loc_0_0000143E
	lsl.l #8,d2
	move.b d1,d2
	bra.b loc_0_0000136A
loc_0_0000138E:
	move.b (a4)+,d1
	subi.b #'0',d1
	bcs.w loc_0_00001434
	cmp.b #$2,d1
	bcc.w loc_0_00001434
loc_0_000013A0:
	add.l d2,d2
	bcs.w loc_0_0000143E
	or.b d1,d2
	move.b (a4)+,d1
	subi.b #48,d1
	bcs.b loc_0_0000142C
	cmp.b #$2,d1
	bcs.b loc_0_000013A0
	bra.b loc_0_0000142C
loc_0_000013B8:
	neg.b d7
	ext.w d7
	moveq.l #0,d2
	moveq.l #2,d3
	moveq.l #1,d0
	exg d0,d7
	jmp $0(pc,d0.w)
loc_0_000013C8:
	bra.w loc_0_0000140E
loc_0_000013CC:
	bra.b loc_0_0000138E
loc_0_000013CE:
	bra.w loc_0_000013E6
loc_0_000013D2:
	bra.b loc_0_00001366
loc_0_000013D4:
	bra.w loc_0_000012EE
loc_0_000013D8:
	bra.w loc_0_00001304
loc_0_000013DC:
	bra.w loc_0_000012E2
loc_0_000013E0:
	moveq.l #64,d1
	bra.w loc_0_000012D2
loc_0_000013E6:
	move.b (a4),d0
	subi.b #48,d0
	bcs.b loc_0_000013E0
	cmp.b #$9,d0
	bcc.b loc_0_000013E0
	move.b d0,d1
	addq.l #1,a4
loc_0_000013F8:
	lsl.l #3,d2
	bcs.b loc_0_0000143E
	or.b d1,d2
	move.b (a4)+,d1
	subi.b #48,d1
	bcs.b loc_0_0000142C
	cmp.b #$9,d1
	bcs.b loc_0_000013F8
	bra.b loc_0_0000142C
loc_0_0000140E:
	lea.l loc_0_00001442(pc),a0
	moveq.l #0,d1
	move.b (a4)+,d1
	bmi.b loc_0_00001434
	move.b $0(a0,d1.w),d1
	bmi.b loc_0_00001434
loc_0_0000141E:
	lsl.l #4,d2
	or.b d1,d2
	move.b (a4)+,d1
	bmi.b loc_0_0000142C
	move.b $0(a0,d1.w),d1
	bpl.b loc_0_0000141E
loc_0_0000142C:
	move.b -$0001(a4),d1
	bra.w loc_0_0000131C
loc_0_00001434:
	moveq.l #22,d0
loc_0_00001436:
	bsr.w loc_0_00008486
	st.b d4
	bra.b loc_0_0000142C
loc_0_0000143E:
	moveq.l #23,d0
	bra.b loc_0_00001436
loc_0_00001442:
	dcb.b $30,$FF
	dc.b $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$FF,$FF,$FF,$FF,$FF,$FF
	dc.b $FF,$0A,$0B,$0C,$0D,$0E,$0F
	dcb.b $1A,$FF
	dc.b $0A,$0B,$0C,$0D,$0E,$0F
	dcb.b $19,$FF
loc_0_000014C2:
	movea.l (a0),a1
	subq.l #4,a7
	move.b (a1)+,$0002(a7)
	move.b (a1)+,$0003(a7)
	move.b (a1)+,(a7)
	move.b (a1)+,$0001(a7)
	move.l (a7)+,d0
	cmp.l #$52474E41,d0
	beq.b loc_0_0000151E
	cmp.w #$5F5F,d0
	bne.b loc_0_0000151C
	swap.w d0
	cmp.w #$5253,d0
	beq.b loc_0_00001516
	cmp.w #$4732,d0
	beq.b loc_0_00001504
	cmp.w #$4C4B,d0
	beq.b loc_0_000014FA
	bne.b loc_0_0000151C
loc_0_000014FA:
	moveq.l #0,d2
	move.w app_021C(a6),d2
	addq.w #1,d2
	bra.b loc_0_00001512
loc_0_00001504:
	move.l #$1002B,d2
	move.b $0121(a6),d0
	lsl.w #8,d0
	or.w d0,d2
loc_0_00001512:
	moveq.l #0,d0
	rts
loc_0_00001516:
	move.l app_084A(a6),d2
	bra.b loc_0_00001512
loc_0_0000151C:
	rts
loc_0_0000151E:
	moveq.l #0,d2
	tst.b app_0101(a6)
	beq.b loc_0_0000151C
	movea.l app_0882(a6),a1
	move.w $0008(a1),d2
	bra.b loc_0_00001512
loc_0_00001530:
	moveq.l #1,d7
	seq.b $0004(a0)
	cmp.b #$23,d1
	bne.b loc_0_00001542
	move.b (a4)+,d1
	st.b $0004(a0)
loc_0_00001542:
	cmpi.b #4,$0005(a0)
	bne.b loc_0_00001556
	bsr.w loc_0_000014C2
	bne.b loc_0_00001556
	moveq.l #2,d3
	bra.w loc_0_000015C8
loc_0_00001556:
	tst.b app_0238(a6)
	bne.w loc_0_00001606
	bsr.w loc_0_00000BCE
	beq.b loc_0_0000156C
	moveq.l #0,d2
	st.b d4
	moveq.l #2,d3
	bra.b loc_0_000015C8
loc_0_0000156C:
	move.l $0008(a1),d2
	moveq.l #0,d3
	move.b $000D(a1),d3
	btst.b #4,$000C(a1)
	bne.b loc_0_000015D0
loc_0_0000157E:
	cmp.b #$2,d3
	beq.b loc_0_000015C8
	cmp.b #$E,d3
	beq.b loc_0_000015C8
	cmp.b #$1,d3
	beq.b loc_0_000015F2
	cmp.b #$F,d3
	bcs.b loc_0_000015B8
	cmp.b #$13,d3
	bcc.b loc_0_000015B8
	lea.l app_0872(a6),a0
	move.l a0,d2
	move.l $0008(a1),(a0)+
	move.b $000E(a1),(a0)+
	move.b $000F(a1),(a0)+
	move.l $0010(a1),(a0)+
	move.w $0014(a1),(a0)
	bra.b loc_0_000015C8
loc_0_000015B8:
	cmp.b #$5,d3
	bne.w loc_0_00001696
	moveq.l #2,d3
	moveq.l #7,d0
	bsr.w loc_0_0000858C
loc_0_000015C8:
	move.b -$0001(a4),d1
	bra.w loc_0_0000131C
loc_0_000015D0:
	st.b d4
	swap.w d3
	move.w $0014(a1),d3
	bsr.w loc_0_000079F6
	swap.w d3
	move.b -$0001(a4),d1
	tst.b app_0238(a6)
	beq.w loc_0_0000131C
	ori.w #32768,d3
	bra.w loc_0_0000131C
loc_0_000015F2:
	tst.b $000E(a1)
	beq.b loc_0_000015C8
	move.b $0146(a6),d0
	cmp.b $000E(a1),d0
	beq.b loc_0_000015C8
	st.b d4
	bra.b loc_0_000015C8
loc_0_00001606:
	bsr.w loc_0_00000BCE
	sne.b d0
	move.b -$0001(a4),d1
	cmp.b #$23,d1
	bne.b loc_0_00001618
	move.b (a4)+,d1
loc_0_00001618:
	tst.b d0
	bne.w loc_0_000016A4
	btst.b #7,$000C(a1)
	beq.b loc_0_00001630
	btst.b #6,$000C(a1)
	beq.w loc_0_000016A4
loc_0_00001630:
	move.l $0008(a1),d2
	moveq.l #0,d3
	move.b $000D(a1),d3
	btst.b #4,$000C(a1)
	bne.b loc_0_000015D0
	cmp.b #$1,d3
	bne.w loc_0_0000157E
	move.b $0146(a6),d0
	cmp.b $000E(a1),d0
	bne.b loc_0_0000165C
	addq.b #1,app_010B(a6)
	bra.w loc_0_0000131C
loc_0_0000165C:
	ori.w #32768,d3
	st.b d4
	bsr.w loc_0_00007A0C
	bra.w loc_0_0000131C
loc_0_0000166A:
	movea.l a0,a1
	lea.l app_046E(a6),a0
	lea.l $0006(a0),a2
	move.l a2,(a0)
	sf.b $0004(a0)
	move.b app_0116(a6),(a2)+
	move.l a4,d0
	sub.l a1,d0
	move.b d0,$0005(a0)
	subq.b #1,d0
loc_0_00001688:
	move.b (a1)+,(a2)+
	subq.b #1,d0
	bne.b loc_0_00001688
	move.b (a4)+,d1
	moveq.l #1,d7
	bra.w loc_0_00001556
loc_0_00001696:
	moveq.l #24,d0
loc_0_00001698:
	moveq.l #2,d3
	st.b d4
	bsr.w loc_0_00008486
	bra.w loc_0_0000131C
loc_0_000016A4:
	moveq.l #3,d0
	bra.b loc_0_00001698
loc_0_000016A8:
	bsr.w loc_0_00000DB6
	tst.w d3
	bmi.b loc_0_000016C4
	cmp.b #$F,d3
	bcs.b loc_0_000016C2
	cmp.b #$13,d3
	bcc.b loc_0_000016C2
	moveq.l #98,d0
	bra.w loc_0_00008486
loc_0_000016C2:
	rts
loc_0_000016C4:
	st.b d4
	moveq.l #20,d0
	bra.w loc_0_00008486
loc_0_000016CC:
	bsr.b loc_0_000016A8
	cmp.b #$1,d3
	bne.b loc_0_000016DC
	tst.b app_0107(a6)
	beq.w loc_0_00008452
loc_0_000016DC:
	moveq.l #0,d0
	rts
	dc.b $20,$57,$54,$97,$60,$06,$20,$57,$54,$97,$3A,$C6,$30,$10,$3F,$00
	dc.b $08,$00,$00,$06,$67,$08,$61,$00,$01,$7A,$30,$1F,$60,$06,$61,$00
	dc.b $01,$7E,$30,$1F,$20,$6E,$02,$4C,$8B,$50,$BA,$3C,$00,$30,$65,$28
	dc.b $BA,$3C,$00,$3A,$65,$14,$BA,$3C,$00,$3C,$67,$16,$08,$05,$00,$06
	dc.b $66,$26,$08,$00,$00,$06,$67,$1A,$4E,$75,$08,$00,$00,$05,$67,$12
	dc.b $4E,$75,$4A,$00,$6A,$0C,$4E,$75,$14,$05,$E6,$0A,$05,$00,$67,$02
	dc.b $4E,$75,$70,$11,$60,$00,$6D,$40,$02,$45,$00,$BF,$34,$05,$E1,$5A
	dc.b $C0,$42,$67,$EE,$20,$5F,$4E,$E8,$00,$02
loc_0_0000175A:
	moveq.l #37,d0
	bra.w loc_0_00008482
loc_0_00001760:
	bsr.b loc_0_0000177E
	bne.b loc_0_0000175A
	tst.b d0
	bne.b loc_0_0000175A
	rts
	dc.b $61,$12,$66,$0C,$4A,$00,$66,$06,$70,$10,$61,$00,$6D,$10,$B0,$00
	dc.b $4E,$75,$60,$F4
loc_0_0000177E:
	move.b d1,d0
	movea.l a4,a0
	ext.w d0
	move.b $7E(a6,d0.w),d0
	cmp.b #$41,d0
	beq.b loc_0_000017B6
	cmp.b #$44,d0
	beq.b loc_0_000017B6
	cmp.b #$52,d0
	beq.b loc_0_000017E4
	cmp.b #$53,d0
	bne.w loc_0_0000181A
	move.b (a0)+,d0
	ext.w d0
	move.b $7E(a6,d0.w),d0
	cmp.b #$50,d0
	bne.b loc_0_0000181A
	moveq.l #1,d0
	moveq.l #7,d2
	bra.b loc_0_000017CA
loc_0_000017B6:
	move.b (a0)+,d2
	cmp.b #$37,d2
	bhi.b loc_0_0000181A
	subi.b #48,d2
	bcs.b loc_0_0000181A
	cmp.b #$41,d0
	seq.b d0
loc_0_000017CA:
	andi.b #1,d0
	moveq.l #0,d1
	move.b (a0)+,d1
	movea.l #loc_0_0000A764,a1
	tst.b $0(a1,d1.w)
	beq.b loc_0_0000181A
	movea.l a0,a4
	cmp.b d0,d0
	rts
loc_0_000017E4:
	move.b (a0)+,d2
	cmp.b #$39,d2
	bhi.b loc_0_0000181A
	cmp.b #$30,d2
	bcs.b loc_0_0000181A
	cmp.b #$31,d2
	bne.b loc_0_0000180E
	move.b (a0),d0
	cmp.b #$36,d0
	bcc.b loc_0_0000180E
	cmp.b #$30,d0
	bcs.b loc_0_0000180E
	addi.b #10,d0
	move.b d0,d2
	addq.l #1,a0
loc_0_0000180E:
	subi.b #48,d2
	cmp.b #$8,d2
	scc.b d0
	bra.b loc_0_000017CA
loc_0_0000181A:
	lea.l app_046E(a6),a0
	movem.l a2/a4,-(a7)
	move.b -$0001(a4),d1
	bsr.w loc_0_00007680
	bne.b loc_0_00001866
	movea.l $016A(a6),a2
	movem.l d1/d3/a3-a5,-(a7)
	bsr.w loc_0_00000B88
	movem.l (a7)+,d1/d3/a3-a5
	bne.b loc_0_00001866
	cmpi.b #4,$000D(a1)
	bne.b loc_0_00001866
	move.b $0009(a1),d0
	move.b $000B(a1),d2
	tst.b app_0238(a6)
	beq.b loc_0_0000185C
	btst.b #6,$000C(a1)
	beq.b loc_0_00001866
loc_0_0000185C:
	movem.l (a7)+,a0/a2
	movea.l a0,a2
	cmp.b d0,d0
	rts
loc_0_00001866:
	movem.l (a7)+,a2/a4
	move.b -$0001(a4),d1
	moveq.l #-1,d0
	rts
	dc.b $4A,$2E,$01,$19,$67,$06,$50,$EE,$01,$1A,$60,$04,$51,$EE,$01,$1A
	dc.b $61,$00,$FE,$FA,$66,$18,$7A,$00,$8A,$02,$4A,$00,$67,$0E,$00,$05
	dc.b $00,$08,$0C,$2E,$00,$01,$02,$39,$67,$00,$6B,$AE,$4E,$75,$24,$4C
	dc.b $B2,$3C,$00,$28,$67,$00,$01,$94,$B2,$3C,$00,$2D,$67,$00,$01,$C8
	dc.b $B2,$3C,$00,$23,$67,$00,$01,$E2,$48,$81,$12,$36,$10,$7E,$B2,$3C
	dc.b $00,$43,$67,$42,$B2,$3C,$00,$53,$67,$28,$B2,$3C,$00,$55,$66,$58
	dc.b $12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$53,$66,$4A,$12,$1C
	dc.b $48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$50,$66,$3C,$7A,$04,$60,$00
	dc.b $04,$0C,$12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$52,$66,$28
	dc.b $7A,$02,$60,$00,$03,$F8,$12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C
	dc.b $00,$43,$66,$14,$12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$52
	dc.b $66,$06,$7A,$01,$60,$00,$03,$D6,$28,$4A,$12,$2C,$FF,$FF,$61,$00
	dc.b $F4,$84,$B2,$3C,$00,$28,$67,$00,$01,$CE,$B2,$3C,$00,$2E,$67,$46
	dc.b $B2,$3C,$00,$5C,$67,$40,$4A,$2E,$01,$1C,$66,$52,$08,$2E,$00,$02
	dc.b $01,$0F,$67,$28,$30,$42,$B1,$C2,$66,$22,$4A,$04,$66,$1E,$B6,$3C
	dc.b $00,$01,$67,$18,$61,$00,$74,$66,$66,$12,$3A,$C2,$08,$C4,$00,$0F
	dc.b $61,$00,$00,$76,$7A,$38,$70,$0E,$60,$00,$6E,$8C,$4A,$2E,$01,$1A
	dc.b $67,$3E,$60,$00,$02,$90,$10,$14,$48,$80,$10,$36,$00,$7E,$B0,$3C
	dc.b $00,$4C,$67,$22,$B0,$3C,$00,$57,$66,$26,$52,$8C,$12,$1C,$7A,$38
	dc.b $4A,$2E,$02,$38,$67,$0C,$61,$00,$5F,$0C,$08,$84,$00,$0E,$61,$00
	dc.b $00,$38,$3A,$C2,$4E,$75,$52,$8C,$12,$1C,$08,$84,$00,$0F,$60,$04
	dc.b $08,$C4,$00,$0F,$7A,$39,$4A,$2E,$02,$38,$67,$18,$4A,$43,$6A,$06
	dc.b $4E,$F9
	dc.l loc_0_000098FC
	dc.b $61,$10,$B6,$3C,$00,$01,$66,$06,$4E,$B9
	dc.l loc_0_00009962
	dc.b $2A,$C2,$4E,$75,$4A,$2E,$02,$3B,$66,$44,$0C,$2E,$00,$01,$02,$39
	dc.b $67,$0C,$4A,$2E,$01,$1F,$67,$06,$08,$02,$00,$00,$66,$32,$08,$04
	dc.b $00,$0F,$67,$2A,$B6,$3C,$00,$02,$66,$24,$4A,$2E,$01,$1D,$67,$1E
	dc.b $30,$2E,$02,$1C,$B0,$7C,$00,$02,$65,$0E,$B0,$7C,$00,$04,$64,$08
	dc.b $B4,$BC,$00,$00,$00,$04,$67,$06,$70,$52,$61,$00,$6A,$54,$4E,$75
	dc.b $70,$23,$60,$00,$6A,$4C,$12,$1C,$4A,$2E,$01,$21,$66,$00,$34,$E6
	dc.b $61,$00,$FD,$22,$66,$00,$FE,$DE,$18,$02,$B2,$3C,$00,$29,$67,$10
	dc.b $B2,$3C,$00,$2C,$66,$00,$6A,$02,$42,$A7,$76,$02,$60,$00,$01,$0C
	dc.b $12,$1C,$7A,$10,$B2,$3C,$00,$2B,$66,$04,$7A,$18,$12,$1C,$8A,$04
	dc.b $4E,$75,$0C,$1C,$00,$28,$66,$00,$FE,$AC,$12,$1C,$61,$00,$FC,$E6
	dc.b $66,$00,$FE,$A2,$B2,$3C,$00,$29,$66,$00,$69,$CE,$12,$1C,$7A,$20
	dc.b $8A,$02,$4E,$75,$12,$1C,$61,$00,$F3,$18,$7A,$3C,$10,$2E,$02,$39
	dc.b $67,$28,$53,$00,$67,$3C,$53,$00,$67,$20,$4A,$2E,$02,$38,$67,$16
	dc.b $4A,$43,$6A,$06
	jmp loc_0_000098FC.l
	dc.b $B6,$3C,$00,$01,$66,$06,$4E,$B9
	dc.l loc_0_00009962
	dc.b $2A,$C2,$4E,$75,$4A,$2E,$02,$38,$67,$0E,$4A,$43,$6A,$06
	jmp loc_0_00009938.l
	dc.b $61,$00,$5D,$BA,$3A,$C2,$4E,$75,$4A,$2E,$02,$38,$67,$F6,$4A,$43
	dc.b $6B,$0C,$61,$00,$5D,$98,$02,$42,$00,$FF,$3A,$C2,$4E,$75,$1A,$FC
	dc.b $00,$00
	jmp loc_0_00009954.l
	dc.b $12,$1C,$2F,$02,$61,$00,$FC,$70,$66,$00,$00,$DA,$61,$00,$FC,$58
	dc.b $B2,$3C,$00,$29,$66,$4A,$08,$2E,$00,$01,$01,$0F,$67,$24,$4A,$04
	dc.b $66,$20,$4A,$97,$66,$1C,$7A,$10,$8A,$02,$24,$1F,$61,$00,$72,$98
	dc.b $66,$08,$12,$1C,$70,$0D,$60,$00,$6C,$C8,$2F,$02,$14,$05,$02,$02
	dc.b $00,$07,$7A,$28,$8A,$02,$24,$1F,$12,$1C,$4A,$43,$6A,$06
	jmp loc_0_0000991C.l
	dc.b $3A,$C2,$4A,$2E,$02,$38,$66,$00,$5D,$52,$4E,$75,$B2,$3C,$00,$2C
	dc.b $66,$00,$68,$F4,$7A,$30,$8A,$02,$12,$1C,$61,$00,$FC,$06,$66,$00
	dc.b $68,$E2,$E7,$08,$80,$02,$E9,$08,$48,$43,$16,$00,$24,$1F,$B2,$3C
	dc.b $00,$2E,$67,$06,$B2,$3C,$00,$5C,$66,$1C,$12,$1C,$48,$81,$12,$36
	dc.b $10,$7E,$B2,$3C,$00,$57,$67,$0C,$B2,$3C,$00,$4C,$66,$00,$68,$BC
	dc.b $00,$03,$00,$08,$12,$1C,$4A,$2E,$01,$21,$67,$10,$B2,$3C,$00,$2A
	dc.b $66,$0A,$12,$1C,$61,$00,$3B,$7E,$D0,$00,$86,$00,$B2,$3C,$00,$29
	dc.b $66,$00,$F3,$E4,$12,$1C,$1A,$C3,$48,$43,$4A,$43,$6A,$06
	jmp loc_0_00009946.l
	dc.b $1A,$C2,$4A,$2E,$02,$38,$66,$00,$5C,$C8,$4E,$75,$48,$81,$12,$36
	dc.b $10,$7E,$B2,$3C,$00,$50,$66,$00,$68,$66,$12,$1C,$48,$81,$12,$36
	dc.b $10,$7E,$B2,$3C,$00,$43,$66,$00,$68,$56,$24,$1F,$12,$1C,$B2,$3C
	dc.b $00,$29,$66,$44,$12,$1C,$7A,$3A,$4A,$2E,$02,$38,$67,$36,$4A,$43
	dc.b $6A,$06
	jmp loc_0_000098EE.l
	dc.b $B6,$3C,$00,$02,$67,$1A,$08,$84,$00,$0F,$61,$00,$FD,$B6,$94,$AE
	dc.b $02,$3C,$20,$0D,$90,$AE,$02,$4C,$94,$80,$3A,$C2,$60,$00,$5C,$76
	dc.b $4A,$2E,$01,$07,$66,$E0,$70,$21,$61,$00,$68,$34,$3A,$C2,$4E,$75
	dc.b $B2,$3C,$00,$2C,$66,$00,$68,$00,$7A,$3B,$2F,$02,$12,$1C,$61,$00
	dc.b $FB,$16,$66,$00,$67,$F2,$E7,$08,$80,$02,$E9,$08,$18,$00,$B2,$3C
	dc.b $00,$2E,$67,$06,$B2,$3C,$00,$5C,$66,$1C,$12,$1C,$48,$81,$12,$36
	dc.b $10,$7E,$B2,$3C,$00,$57,$67,$0C,$B2,$3C,$00,$4C,$66,$00,$67,$D0
	dc.b $00,$04,$00,$08,$12,$1C,$24,$1F,$4A,$2E,$01,$21,$67,$10,$B2,$3C
	dc.b $00,$2A,$66,$0A,$12,$1C,$61,$00,$3A,$90,$D0,$00,$88,$00,$1A,$C4
	dc.b $4A,$2E,$02,$38,$67,$32,$4A,$43,$6B,$20,$4A,$2E,$01,$07,$66,$06
	dc.b $B6,$3C,$00,$02,$67,$1C,$94,$AE,$02,$3C,$20,$0D,$90,$AE,$02,$4C
	dc.b $94,$80,$52,$82,$61,$00,$5B,$D2,$60,$0E,$4E,$B9
	dc.l loc_0_000098E0
	dc.b $60,$08,$70,$21,$61,$00,$67,$98,$1A,$C2,$B2,$3C,$00,$29,$66,$00
	dc.b $F2,$BA,$12,$1C,$4E,$75,$72,$00,$12,$1C,$22,$7C
	dc.l loc_0_0000A764
	dc.b $4A,$31,$10,$00,$67,$00,$FC,$1C,$08,$C5,$00,$06
loc_0_00001D14:
	dc.b $4E,$75,$61,$00,$32,$02,$60,$04,$61,$00,$06,$54,$61,$00,$FB,$5C
	dc.b $10,$05,$02,$40,$00,$78,$67,$0C,$B0,$3C,$00,$20,$66,$00,$FA,$10
	dc.b $00,$06,$00,$08,$02,$45,$00,$07,$8C,$45,$B2,$3C,$00,$2C,$66,$00
	dc.b $67,$1E,$12,$1C,$3F,$00,$61,$00,$FB,$32,$10,$05,$02,$40,$00,$78
	dc.b $B0,$5F,$66,$00,$F9,$EA,$02,$45,$00,$07,$EE,$5D,$8C,$45,$3A,$C6
	dc.b $4E,$75,$12,$1C,$61,$00,$F0,$4C,$B2,$3C,$00,$2C,$66,$64,$4A,$04
	dc.b $66,$60,$B6,$3C,$00,$02,$66,$5A,$B4,$BC,$00,$00,$00,$09,$64,$66
	dc.b $4A,$82,$6F,$62,$55,$8D,$61,$00,$70,$42,$66,$44,$02,$46,$40,$00
	dc.b $08,$46,$00,$0E,$EC,$4E,$00,$46,$50,$00,$61,$00,$31,$7A,$B4,$3C
	dc.b $00,$08,$66,$02,$74,$00,$EE,$5A,$8C,$42,$12,$1C,$61,$00,$F9,$34
	dc.b $00,$3F,$4A,$2E,$02,$38,$67,$0E,$70,$00,$10,$2E,$02,$39,$10,$3B
	dc.b $00,$0C,$D1,$6E,$01,$94,$70,$10,$60,$00,$6A,$3A,$02,$02,$02,$04
	dc.b $54,$8D,$12,$1C,$61,$00,$FC,$C6,$60,$00,$00,$BE,$08,$06,$00,$0E
	dc.b $66,$F0,$44,$82,$60,$EC,$08,$2E,$00,$01,$01,$0E,$67,$E4,$08,$06
	dc.b $00,$0E,$66,$02,$44,$82,$30,$42,$B1,$C2,$66,$E0,$48,$E7,$22,$00
	dc.b $B2,$3C,$00,$2C,$66,$00,$66,$58,$12,$1C,$61,$00,$31,$0A,$48,$E7
	dc.b $40,$08,$61,$00,$F9,$66,$66,$00,$00,$42,$4A,$00,$67,$00,$00,$3C
	dc.b $55,$8D,$61,$00,$6F,$A6,$66,$30,$50,$4F,$61,$00,$FA,$5C,$48,$82
	dc.b $3C,$3C,$41,$E8,$8C,$42,$EE,$5A,$8C,$42,$3A,$C6,$4C,$DF,$00,$44
	dc.b $3A,$C2,$70,$00,$0C,$2E,$00,$03,$02,$39,$66,$02,$70,$02,$D1,$6E
	dc.b $01,$94,$70,$15,$60,$00,$69,$AE,$54,$4D,$4C,$DF,$10,$02,$4C,$DF
	dc.b $00,$44,$08,$06,$00,$0E,$66,$02,$44,$82,$60,$00,$FF,$68,$54,$8D
	dc.b $B2,$3C,$00,$23,$66,$14,$08,$2E,$00,$04,$01,$0F,$66,$00,$FE,$E4
	dc.b $08,$2E,$00,$01,$01,$0E,$66,$00,$FE,$DA,$61,$00,$F9,$E2,$B2,$3C
	dc.b $00,$2C,$66,$00,$65,$CA,$12,$1C,$3F,$05,$61,$00,$F9,$DE,$38,$1F
	dc.b $20,$6E,$02,$4C,$14,$05,$02,$02,$00,$78,$B4,$3C,$00,$08,$67,$00
	dc.b $00,$4C,$B8,$3C,$00,$3C,$67,$30,$61,$00,$30,$5C,$30,$86,$4A,$02
	dc.b $66,$10,$DA,$05,$8B,$18,$B8,$3C,$00,$40,$64,$00,$F8,$72,$89,$10
	dc.b $4E,$75,$10,$04,$02,$00,$00,$78,$66,$00,$F8,$64,$D8,$04,$52,$04
	dc.b $89,$18,$8B,$10,$70,$3C,$60,$10,$EA,$5E,$02,$46,$07,$00,$61,$00
	dc.b $30,$26,$8C,$05,$30,$86,$70,$3D,$60,$00,$F8,$0C,$00,$06,$00,$C0
	dc.b $8C,$04,$02,$45,$00,$07,$EE,$5D,$8C,$45,$0C,$2E,$00,$03,$02,$39
	dc.b $66,$04,$08,$C6,$00,$08,$30,$86,$3A,$04,$BA,$3C,$00,$40,$64,$00
	dc.b $F8,$1E,$0C,$2E,$00,$01,$02,$39,$67,$00,$65,$1C,$4E,$75,$0C,$2E
	dc.b $00,$03,$02,$39,$66,$04,$00,$46,$01,$00,$61,$00,$F7,$A6,$00,$FF
	dc.b $48,$E7,$18,$00,$B2,$3C,$00,$2C,$66,$00,$65,$14,$12,$1C,$61,$00
	dc.b $F8,$16,$4C,$DF,$00,$18,$66,$00,$F8,$16,$D4,$02,$20,$6E,$02,$4C
	dc.b $85,$10,$61,$BE,$08,$2E,$00,$03,$01,$0E,$67,$42,$4A,$04,$66,$3E
	dc.b $B6,$3C,$00,$02,$66,$38,$36,$10,$02,$43,$01,$FF,$B6,$7C,$01,$FC
	dc.b $66,$2C,$20,$28,$00,$02,$32,$40,$B0,$89,$66,$22,$48,$E7,$80,$80
	dc.b $24,$00,$55,$4D,$61,$00,$6E,$34,$4C,$DF,$01,$01,$66,$0E,$08,$90
	dc.b $00,$00,$31,$40,$00,$02,$70,$17,$60,$00,$68,$5A,$54,$4D,$4E,$75
	dc.b $61,$00,$2F,$64,$3A,$C6,$B2,$3C,$00,$23,$66,$00,$64,$AA,$12,$1C
	dc.b $61,$00,$FA,$D6,$B2,$3C,$00,$2C,$66,$00,$64,$94,$12,$1C,$61,$00
	dc.b $F7,$0C,$00,$3D,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$D2,$61,$00
	dc.b $2F,$36,$3A,$C6,$B2,$3C,$00,$23,$66,$00,$64,$7C,$12,$1C,$61,$00
	dc.b $FA,$A8,$B2,$3C,$00,$2C,$66,$00,$64,$66,$12,$1C,$61,$00,$F6,$DE
	dc.b $00,$7D,$4E,$75,$10,$2E,$02,$39,$67,$00,$00,$BC,$B0,$3C,$00,$01
	dc.b $67,$4E,$B0,$3C,$00,$02,$67,$00,$00,$94,$4A,$2E,$01,$24,$66,$00
	dc.b $00,$8C,$0C,$2E,$00,$14,$01,$21,$6D,$2E,$50,$C6,$3A,$C6,$61,$00
	dc.b $F6,$74,$4A,$2E,$02,$38,$67,$1C,$4A,$04,$66,$18,$B6,$3C,$00,$02
	dc.b $66,$0C,$4A,$2E,$01,$07,$66,$06,$70,$1E,$61,$00,$64,$36,$94,$AE
	dc.b $02,$3C,$55,$82,$2A,$C2,$4E,$75,$70,$05,$61,$00,$65,$2C,$60,$4C
	dc.b $61,$00,$00,$CA,$67,$2E,$E0,$4E,$1A,$C6,$4A,$43,$6B,$00,$78,$6E
	dc.b $4A,$82,$66,$30,$BC,$3C,$00,$61,$67,$20,$08,$2E,$00,$06,$01,$0F
	dc.b $66,$08,$70,$53,$61,$00,$63,$FC,$60,$06,$70,$12,$61,$00,$67,$76
	dc.b $2A,$6E,$02,$4C,$3A,$FC,$4E,$71,$4E,$75,$1A,$FC,$00,$FF,$70,$3F
	dc.b $60,$00,$63,$E0,$61,$00,$58,$06,$1A,$C2,$4E,$75,$61,$00,$00,$7E
loc_0_000020B4:
	beq.b loc_0_000020C6
	move.w d6,(a5)+
	tst.w d3
	bmi.w loc_0_000098EE
	bsr.w loc_0_000078BC
	move.w d2,(a5)+
	rts
loc_0_000020C6:
	addq.l #4,a5
	rts
	dc.b $4A,$2E,$01,$2C,$6B,$94,$66,$00,$FF,$54,$08,$2E,$00,$00,$01,$0F
	dc.b $67,$D4,$61,$00,$EC,$D8,$4A,$04,$66,$46,$4A,$2E,$01,$07,$66,$06
	dc.b $B6,$3C,$00,$02,$67,$3A,$2F,$02,$94,$AE,$02,$3C,$59,$82,$67,$2E
	dc.b $6A,$02,$54,$82,$10,$02,$48,$80,$48,$C0,$B4,$80,$66,$20,$61,$00
	dc.b $6C,$C4,$66,$0C,$58,$8F,$8C,$02,$3A,$C6,$70,$0C,$60,$00,$66,$F0
	dc.b $08,$2E,$00,$05,$01,$0F,$67,$06,$70,$11,$61,$00,$66,$E2,$24,$1F
	dc.b $48,$7A,$FF,$88,$60,$04,$61,$00,$EC,$84,$4A,$2E,$02,$38,$66,$10
	dc.b $4A,$04,$66,$2E,$B6,$3C,$00,$02,$66,$28,$4A,$2E,$01,$07,$66,$22
	dc.b $4A,$43,$6B,$1E,$4A,$2E,$01,$07,$66,$06,$B6,$3C,$00,$02,$67,$18
	dc.b $08,$02,$00,$00,$67,$06,$70,$23,$61,$00,$63,$22,$94,$AE,$02,$3C
	dc.b $55,$82,$4A,$2E,$02,$38,$4E,$75,$70,$21,$61,$00,$63,$10,$4A,$2E
	dc.b $02,$38,$4E,$75,$B2,$3C,$00,$23,$66,$00,$62,$E6,$12,$1C,$61,$00
	dc.b $F5,$42,$4A,$82,$6B,$0E,$B4,$BC,$00,$00,$00,$08,$64,$06,$8C,$02
	dc.b $3A,$C6,$4E,$75,$3A,$C6,$70,$1D,$60,$00,$62,$E2,$0C,$2E,$00,$14
	dc.b $01,$21,$6D,$00,$0F,$84,$0C,$2E,$00,$20,$01,$21,$67,$00,$0F,$7A
	dc.b $4A,$2E,$02,$39,$66,$00,$62,$8A,$61,$00,$F5,$9C,$02,$42,$00,$FF
	dc.b $E8,$5A,$3A,$02,$B2,$3C,$00,$2C,$66,$00,$62,$8E,$12,$1C,$61,$7E
	dc.b $20,$6E,$02,$4C,$31,$45,$00,$02,$4E,$75,$0C,$2E,$00,$14,$01,$21
	dc.b $6D,$00,$0F,$46,$0C,$2E,$00,$20,$01,$21,$67,$00,$0F,$3C,$4A,$2E
	dc.b $02,$39,$66,$00,$62,$4C,$3A,$C6,$54,$8D,$61,$00,$F4,$DA,$00,$65
	dc.b $7A,$00,$61,$58,$B2,$3C,$00,$2C,$66,$00,$62,$4E,$12,$1C,$61,$00
	dc.b $F5,$46,$02,$42,$00,$FF,$E8,$5A,$8A,$42,$20,$6E,$02,$4C,$31,$45
	dc.b $00,$02,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00,$0E,$FC,$0C,$2E
	dc.b $00,$20,$01,$21,$67,$00,$0E,$F2,$4A,$2E,$02,$39,$66,$00,$62,$02
	dc.b $7A,$00,$61,$0A,$20,$6E,$02,$4C,$31,$45,$00,$02,$4E,$75,$3A,$C6
	dc.b $54,$8D,$3F,$05,$61,$00,$F4,$80,$00,$25,$3A,$1F,$B2,$3C,$00,$7B
	dc.b $66,$1A,$12,$1C,$61,$00,$F5,$0E,$66,$18,$4A,$00,$66,$0E,$08,$C5
	dc.b $00,$0B,$02,$42,$00,$FF,$ED,$4A,$8A,$42,$60,$28,$70,$55,$60,$00
	dc.b $61,$F8,$61,$00,$F4,$3E,$4A,$2E,$02,$38,$67,$18,$4A,$82,$6B,$08
	dc.b $B4,$BC,$00,$00,$00,$20,$65,$04,$61,$00,$56,$22,$ED,$4A,$02,$42
	dc.b $07,$C0,$8A,$42,$B2,$3C,$00,$3A,$66,$D2,$12,$1C,$61,$00,$F4,$C6
	dc.b $66,$0C,$4A,$00,$66,$C6,$08,$C5,$00,$05,$8A,$02,$60,$22,$61,$00
	dc.b $F4,$02,$4A,$2E,$02,$38,$67,$18,$4A,$82,$66,$06,$4A,$2E,$01,$20
	dc.b $66,$0E,$6F,$16,$B4,$BC,$00,$00,$00,$20,$67,$04,$6E,$0C,$8A,$42
	dc.b $B2,$3C,$00,$7D,$66,$96,$12,$1C,$4E,$75,$61,$00,$55,$D0,$60,$F0
	dc.b $50,$EE,$02,$3B,$B2,$3C,$00,$23,$67,$22,$61,$00,$F4,$5A,$2F,$0C
	dc.b $B2,$3C,$00,$2C,$66,$00,$61,$52,$12,$1C,$D4,$02,$52,$02,$42,$67
	dc.b $1A,$C2,$1A,$C6,$61,$00,$F3,$C0,$00,$FD,$60,$20,$3A,$C6,$12,$1C
	dc.b $61,$00,$EA,$8A,$2F,$0C,$3F,$02,$61,$00,$F7,$B4,$B2,$3C,$00,$2C
	dc.b $66,$00,$61,$26,$12,$1C,$61,$00,$F3,$9E,$00,$7D,$34,$1F,$24,$5F
	dc.b $02,$45,$00,$38,$66,$06,$70,$03,$60,$00,$0C,$9E,$B4,$7C,$00,$08
	dc.b $65,$16,$4A,$2E,$01,$1E,$67,$10,$28,$4A,$6A,$06,$70,$6A,$60,$00
	dc.b $61,$1C,$70,$09,$61,$00,$62,$1C,$70,$01,$60,$00,$0C,$7C,$50,$EE
	dc.b $02,$3B,$B2,$3C,$00,$23,$67,$22,$61,$00,$F3,$DC,$2F,$0C,$B2,$3C
	dc.b $00,$2C,$66,$00,$60,$D4,$12,$1C,$D4,$02,$52,$02,$42,$67,$1A,$C2
	dc.b $1A,$C6,$61,$00,$F3,$42,$00,$3D,$60,$A2,$3A,$C6,$12,$1C,$61,$00
	dc.b $EA,$0C,$2F,$0C,$3F,$02,$61,$00,$F7,$36,$B2,$3C,$00,$2C,$66,$00
	dc.b $60,$A8,$12,$1C,$61,$00,$F3,$20,$00,$3D,$60,$80,$0C,$2E,$00,$14
	dc.b $01,$21,$66,$00,$0D,$64,$4A,$2E,$02,$39,$67,$04,$61,$00,$60,$72
	dc.b $B2,$3C,$00,$23,$66,$00,$60,$8A,$12,$1C,$3A,$C6,$61,$00,$E9,$CE
	dc.b $61,$00,$F6,$FC,$B2,$3C,$00,$2C,$66,$00,$60,$6E,$12,$1C,$61,$00
	dc.b $F2,$E6,$00,$64,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00,$0D,$2A
	dc.b $0C,$2E,$00,$20,$01,$21,$67,$00,$0D,$20,$70,$00,$10,$2E,$02,$39
	dc.b $D0,$40,$8C,$7B,$00,$36,$61,$00,$F3,$3E,$7A,$00,$1A,$02,$B2,$3C
	dc.b $00,$2C,$66,$00,$60,$34,$12,$1C,$61,$00,$F3,$2C,$02,$42,$00,$FF
	dc.b $ED,$4A,$8A,$42,$B2,$3C,$00,$2C,$66,$00,$60,$1E,$12,$1C,$3F,$05
	dc.b $61,$00,$F2,$9A,$00,$3C,$3A,$DF,$4E,$75,$04,$00,$02,$00,$04,$00
	dc.b $06,$00,$70,$56,$60,$00,$60,$22,$0C,$2E,$00,$14,$01,$21,$6D,$00
	dc.b $0C,$C8,$0C,$2E,$00,$20,$01,$21,$67,$00,$0C,$BE,$70,$00,$10,$2E
	dc.b $02,$39,$B0,$3C,$00,$01,$67,$00,$5F,$C8,$B0,$3C,$00,$03,$66,$04
	dc.b $08,$C6,$00,$09,$3A,$C6,$7A,$00,$7C,$00,$61,$00,$F2,$CA,$8A,$02
	dc.b $B2,$3C,$00,$3A,$66,$BC,$12,$1C,$61,$00,$F2,$BC,$8C,$02,$B2,$3C
	dc.b $00,$2C,$66,$00,$5F,$B4,$12,$1C,$61,$30,$8A,$42,$B2,$3C,$00,$3A
	dc.b $66,$A0,$12,$1C,$61,$00,$00,$24,$8C,$42,$B2,$3C,$00,$2C,$66,$00
	dc.b $5F,$98,$12,$1C,$61,$20,$8A,$42,$B2,$3C,$00,$3A,$66,$84,$12,$1C
	dc.b $61,$14,$8C,$42,$3A,$C5,$3A,$C6,$4E,$75,$61,$00,$F2,$7A,$02,$42
	dc.b $00,$FF,$ED,$4A,$4E,$75,$B2,$3C,$00,$28,$66,$20,$12,$1C,$61,$00
	dc.b $F2,$84,$66,$18,$02,$42,$00,$FF,$4A,$00,$67,$04,$00,$02,$00,$08
	dc.b $E8,$5A,$B2,$3C,$00,$29,$66,$04,$12,$1C,$4E,$75,$60,$00,$5F,$1A
	dc.b $7E,$04,$B2,$3C,$00,$23,$66,$12,$12,$1C,$61,$00,$F1,$A6,$2E,$02
	dc.b $B2,$3C,$00,$2C,$66,$00,$5F,$32,$12,$1C,$B2,$3C,$00,$09,$67,$5C
	dc.b $B2,$3C,$00,$20,$67,$56,$B2,$3C,$00,$0A,$67,$50,$41,$EE,$04,$6E
	dc.b $61,$00,$51,$6C,$66,$00,$5E,$E2,$7C,$02,$B2,$3C,$00,$2E,$66,$20
	dc.b $12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$42,$67,$14,$B2,$3C
	dc.b $00,$57,$67,$0E,$7C,$04,$B2,$3C,$00,$4C,$66,$00,$5E,$D4,$60,$02
	dc.b $53,$8C,$12,$1C,$28,$07,$DE,$86,$48,$E7,$41,$00,$61,$10,$4C,$DF
	dc.b $00,$82,$B2,$3C,$00,$2C,$66,$04,$12,$1C,$60,$B0,$4E,$75,$4A,$2E
	dc.b $02,$38,$66,$2A,$61,$00,$E6,$2E,$67,$00,$5E,$92,$76,$02,$10,$28
	dc.b $00,$06,$B0,$2E,$01,$16,$67,$08,$45,$EE,$01,$6A,$60,$00,$E6,$FE
	dc.b $45,$EE,$01,$5A,$4A,$92,$66,$00,$E7,$8A,$60,$00,$5E,$7C,$61,$00
	dc.b $E6,$04,$66,$00,$5E,$6C,$08,$E9,$00,$06,$00,$0C,$66,$00,$5E,$5E
	dc.b $0C,$29,$00,$02,$00,$0D,$66,$00,$5E,$54,$B8,$A9,$00,$08,$66,$00
	dc.b $5E,$54,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00,$01,$58,$10,$2E
	dc.b $02,$39,$67,$12,$B0,$3C,$00,$02,$67,$0C,$B0,$3C,$00,$03,$66,$00
	dc.b $5E,$40,$08,$86,$00,$07,$61,$00,$F0,$D4,$00,$FD,$B2,$3C,$00,$2C
	dc.b $66,$00,$5E,$46,$12,$1C,$61,$00,$F1,$3E,$20,$6E,$02,$4C,$D4,$02
	dc.b $85,$10,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00,$0A,$FC,$3A,$06
	dc.b $08,$86,$00,$0B,$70,$00,$10,$2E,$02,$39,$D0,$40,$8C,$7B,$00,$2A
	dc.b $3A,$C6,$02,$45,$08,$00,$3A,$C5,$61,$00,$F0,$8C,$00,$64,$B2,$3C
	dc.b $00,$2C,$66,$00,$5E,$04,$12,$1C,$61,$00,$23,$D8,$E9,$02,$20,$6E
	dc.b $02,$4C,$85,$28,$00,$02,$4E,$75,$02,$00,$00,$00,$02,$00,$04,$00
	dc.b $7A,$00,$60,$04,$3A,$3C,$08,$00,$0C,$2E,$00,$14,$01,$21,$6D,$00
	dc.b $0A,$A8,$61,$00,$FC,$C2,$3A,$C6,$3A,$C5,$61,$00,$F0,$4A,$00,$FD
	dc.b $B2,$3C,$00,$2C,$66,$00,$5D,$C2,$12,$1C,$61,$00,$F0,$BA,$20,$6E
	dc.b $02,$4C,$B2,$3C,$00,$3A,$66,$16,$12,$1C,$85,$28,$00,$03,$61,$00
	dc.b $F0,$A6,$20,$6E,$02,$4C,$E9,$0A,$85,$28,$00,$02,$4E,$75,$70,$25
	dc.b $60,$00,$5D,$BA,$0C,$2E,$00,$14,$01,$21,$6D,$78,$10,$2E,$02,$39
	dc.b $67,$72,$B0,$3C,$00,$02,$67,$6C,$B0,$3C,$00,$03,$66,$00,$5D,$62
	dc.b $08,$06,$00,$08,$56,$C5,$48,$85,$02,$45,$08,$00,$08,$06,$00,$0E
	dc.b $57,$C6,$48,$86,$02,$46,$00,$40,$00,$46,$4C,$00,$3A,$C6,$3A,$C5
	dc.b $61,$00,$EF,$D4,$00,$FD,$B2,$3C,$00,$2C,$66,$00,$5D,$4C,$12,$1C
	dc.b $61,$00,$F0,$44,$20,$6E,$02,$4C,$B2,$3C,$00,$3A,$67,$0C,$85,$28
	dc.b $00,$03,$E9,$0A,$85,$28,$00,$02,$4E,$75,$12,$1C,$85,$28,$00,$03
	dc.b $61,$00,$F0,$24,$20,$6E,$02,$4C,$E9,$0A,$08,$C2,$00,$02,$85,$28
	dc.b $00,$02,$4E,$75,$61,$00,$EF,$96,$00,$FD,$B2,$3C,$00,$2C,$66,$00
	dc.b $5D,$08,$12,$1C,$61,$00,$F0,$00,$20,$6E,$02,$4C,$D4,$02,$85,$10
	dc.b $70,$02,$60,$00,$08,$84,$61,$00,$27,$A8,$3A,$C6,$61,$00,$F0,$FA
	dc.b $B2,$3C,$00,$2C,$66,$00,$5C,$E2,$12,$1C,$3F,$05,$61,$00,$F0,$F6
	dc.b $38,$1F,$20,$6E,$02,$4C,$30,$05,$02,$00,$00,$78,$67,$4A,$B0,$3C
	dc.b $00,$08,$67,$54,$B8,$3C,$00,$3C,$67,$74,$10,$04,$02,$00,$00,$78
	dc.b $B0,$3C,$00,$18,$66,$2E,$10,$05,$02,$00,$00,$78,$B0,$3C,$00,$18
	dc.b $66,$22,$3C,$3C,$B1,$08,$61,$00,$27,$58,$10,$04,$02,$00,$00,$07
	dc.b $8C,$00,$10,$05,$02,$40,$00,$07,$EE,$58,$8C,$40,$20,$6E,$02,$4C
	dc.b $30,$86,$4E,$75,$60,$00,$EF,$62,$DA,$05,$8B,$10,$3A,$04,$8B,$50
	dc.b $30,$3C,$00,$FF,$60,$00,$EF,$1A,$02,$05,$00,$07,$DA,$05,$0C,$2E
	dc.b $00,$03,$02,$39,$66,$02,$52,$05,$8B,$10,$3A,$04,$00,$44,$00,$C0
	dc.b $89,$50,$30,$3C,$00,$FF,$61,$00,$EE,$F8,$60,$00,$F7,$10,$3C,$3C
	dc.b $0C,$00,$61,$00,$26,$FC,$8C,$45,$30,$86,$70,$3D,$60,$00,$EE,$E2
	dc.b $61,$00,$26,$EE,$61,$16,$8C,$05,$B2,$3C,$00,$2C,$66,$00,$5C,$2A
	dc.b $12,$1C,$61,$08,$EE,$5D,$8C,$45,$3A,$C6,$4E,$75,$61,$00,$F0,$36
	dc.b $10,$05,$02,$00,$00,$78,$B0,$3C,$00,$18,$66,$00,$EE,$EC,$02,$45
	dc.b $00,$07,$4E,$75,$61,$00,$42,$72,$B2,$3C,$00,$2C,$66,$00,$5B,$FA
	dc.b $12,$1C,$2A,$02,$61,$00,$42,$62,$20,$02,$67,$18,$6B,$3C,$2F,$02
	dc.b $24,$2E,$02,$3C,$20,$17,$61,$00,$E9,$30,$24,$1F,$4A,$80,$67,$04
	dc.b $90,$82,$44,$80,$D0,$85,$28,$00,$67,$10,$B0,$BC,$00,$00,$00,$80
	dc.b $64,$18,$1A,$FC,$00,$00,$53,$00,$66,$F8,$D8,$AE,$02,$3C,$41,$EE
	dc.b $03,$E8,$4A,$90,$66,$00,$E3,$D4,$4E,$75,$70,$1D,$60,$00,$5B,$CE
	dc.b $43,$EC,$FF,$FF,$B2,$3C,$00,$0A,$67,$1A,$12,$1C,$B2,$3C,$00,$0A
	dc.b $66,$F8,$24,$0C,$94,$89,$53,$42,$4A,$2E,$02,$38,$67,$06,$61,$00
	dc.b $6E,$12,$72,$0A,$4E,$75,$61,$00,$EE,$7E,$8C,$02,$B2,$3C,$00,$2C
	dc.b $66,$00,$5B,$76,$12,$1C,$61,$00,$FE,$78,$60,$00,$F7,$BA,$3F,$01
	dc.b $10,$2E,$02,$39,$67,$06,$B0,$3C,$00,$01,$67,$10,$61,$00,$E3,$5C
	dc.b $10,$2E,$02,$39,$66,$02,$70,$02,$32,$1F,$4E,$75,$41,$EE,$03,$E8
	dc.b $4A,$90,$67,$08,$28,$2E,$02,$3C,$61,$00,$E3,$60,$10,$2E,$02,$39
	dc.b $60,$E6,$61,$CA,$61,$00,$41,$A2,$B2,$3C,$00,$2C,$67,$06,$2F,$02
	dc.b $74,$00,$60,$08,$12,$1C,$2F,$02,$61,$00,$41,$8E,$76,$00,$41,$FA
	dc.b $01,$8E,$22,$02,$16,$2E,$02,$39,$16,$30,$30,$00,$28,$1F,$42,$AE
	dc.b $01,$82,$4A,$2E,$01,$03,$67,$06,$4A,$2E,$02,$38,$66,$16,$E7,$AC
	dc.b $6A,$00,$00,$08,$70,$54,$60,$00,$5B,$10,$2D,$44,$01,$8E,$12,$2C
	dc.b $FF,$FF,$4E,$75,$1D,$7C,$00,$FF,$08,$3B,$2D,$6E,$02,$3C,$08,$3C
	dc.b $61,$00,$6D,$A2,$67,$D8,$42,$AE,$01,$8E,$53,$84,$65,$E0,$48,$7A
	dc.b $FF,$DE,$53,$03,$65,$2A,$67,$14,$2A,$C1,$7A,$04,$61,$36,$51,$CC
	dc.b $FF,$F8,$04,$84,$00,$01,$00,$00,$64,$EE,$4E,$75,$3A,$C1,$7A,$02
	dc.b $61,$22,$51,$CC,$FF,$F8,$04,$84,$00,$01,$00,$00,$64,$EE,$4E,$75
	dc.b $1A,$C1,$7A,$01,$61,$0E,$51,$CC,$FF,$F8,$04,$84,$00,$01,$00,$00
	dc.b $64,$EE,$4E,$75,$2F,$01,$22,$05,$24,$2E,$02,$3C,$D4,$AE,$01,$8E
	dc.b $61,$00,$6D,$22,$DB,$AE,$01,$8E,$22,$1F,$2A,$6E,$02,$4C,$4E,$75
	dc.b $61,$00,$FE,$FC,$B0,$3C,$00,$01,$67,$00,$00,$5E,$B0,$3C,$00,$03
	dc.b $67,$1A,$B0,$3C,$00,$02,$67,$08,$61,$00,$31,$02,$61,$1A,$60,$F8
	dc.b $61,$00,$E3,$9A,$61,$00,$F0,$B0,$61,$0E,$60,$F4,$61,$00,$E3,$8E
	dc.b $61,$00,$F0,$84,$61,$02,$60,$F4,$B2,$3C,$00,$2C,$66,$26,$12,$1C
	dc.b $B2,$3C,$00,$09,$67,$08,$B2,$3C,$00,$20,$67,$02,$4E,$75,$70,$0B
	dc.b $61,$00,$5B,$40,$12,$1C,$B2,$3C,$00,$09,$67,$F8,$B2,$3C,$00,$20
	dc.b $67,$F2,$4E,$75,$58,$8F,$4E,$75,$B2,$3C,$00,$27,$67,$24,$B2,$3C
	dc.b $00,$22,$67,$1E,$61,$00,$E3,$46,$4A,$2E,$02,$38,$67,$08,$4A,$43
	dc.b $6B,$0A,$61,$00,$4E,$0E,$1A,$C2,$61,$AE,$60,$DC,$61,$00,$6E,$CC
	dc.b $60,$F6,$16,$01,$48,$E7,$00,$0C,$12,$1C,$B2,$3C,$00,$0A,$67,$36
	dc.b $B2,$03,$66,$06,$12,$1C,$B6,$01,$66,$04,$1A,$C1,$60,$EA,$B2,$3C
	dc.b $00,$0A,$67,$1A,$B2,$3C,$00,$09,$67,$14,$B2,$3C,$00,$20,$67,$0E
	dc.b $B2,$3C,$00,$2C,$67,$08,$4C,$DF,$30,$00,$12,$03,$60,$A6,$50,$8F
	dc.b $61,$00,$FF,$66,$60,$92,$50,$8F,$70,$37,$60,$00,$59,$B0,$01,$00
	dc.b $01,$02,$61,$00,$FE,$1A,$48,$80,$1C,$3B,$00,$F4,$61,$00,$3F,$EA
	dc.b $4A,$82,$67,$0A,$28,$02,$16,$06,$72,$00,$60,$00,$FE,$62,$4E,$75
	dc.b $50,$EE,$01,$15,$72,$0A,$4E,$75,$41,$EE,$03,$E8,$4A,$90,$67,$02
	dc.b $4E,$75,$70,$29,$60,$00,$59,$72,$61,$EE,$4A,$2E,$02,$38,$66,$30
	dc.b $2F,$08,$61,$00,$3F,$94,$20,$5F,$48,$E7,$30,$00,$61,$00,$E0,$A6
	dc.b $4C,$DF,$00,$30,$67,$00,$59,$06,$16,$05,$48,$7A,$00,$44,$45,$EE
	dc.b $01,$6A,$55,$05,$67,$00,$E1,$76,$45,$EE,$01,$62,$60,$00,$E1,$6E
	dc.b $61,$00,$E0,$82,$66,$00,$58,$FE,$08,$29,$00,$06,$00,$0C,$66,$00
	dc.b $58,$DC,$2F,$09,$61,$00,$EB,$48,$22,$5F,$B4,$A9,$00,$08,$66,$00
	dc.b $58,$D4,$B6,$29,$00,$0D,$66,$00,$58,$C4,$08,$E9,$00,$06,$00,$0C
	dc.b $12,$2C,$FF,$FF,$1D,$7C,$00,$3D,$08,$3B,$2D,$42,$08,$3C,$4E,$75
	dc.b $70,$2D,$60,$00,$58,$F8,$70,$2E,$60,$00,$58,$F2,$61,$00,$FF,$6A
	dc.b $61,$00,$EB,$E2,$66,$F0,$48,$42,$34,$00,$48,$42,$02,$82,$00,$FF
	dc.b $00,$FF,$24,$6E,$01,$6A,$41,$EE,$03,$E8,$48,$E7,$20,$1C,$4A,$2E
	dc.b $02,$38,$66,$16,$61,$00
loc_0_00002BC0:
	adda.l a0,a7
	movem.l (a7)+,d4/a3-a5
	beq.w loc_0_00008436
	moveq.l #4,d3
	bsr.w loc_0_00000CBA
	moveq.l #10,d1
	rts
	dc.b $61,$00,$DF,$B2,$4C,$DF,$38,$10,$66,$00,$58,$5C,$0C,$29,$00,$04
	dc.b $00,$0D,$66,$00,$58,$4E,$B8,$A9,$00,$08,$66,$00,$58,$46,$08,$E9
	dc.b $00,$06,$00,$0C,$66,$00,$58,$3C,$72,$0A,$4E,$75,$4A,$2E,$02,$39
	dc.b $66,$00,$58,$44,$32,$3C,$00,$0A,$4E,$75,$61,$00,$F7,$40,$61,$00
	dc.b $EB,$6A,$66,$44,$B2,$3C,$00,$2C,$66,$00,$58,$44,$12,$1C,$48,$A7
	dc.b $A0,$00,$61,$00,$EB,$56,$4C,$9F,$00,$18,$66,$2C,$B6,$00,$67,$18
	dc.b $00,$06,$00,$88,$4A,$03,$67,$02,$C9,$42,$8C,$02,$02,$44,$00,$07
	dc.b $EE,$5C,$8C,$44,$3A,$C6,$4E,$75,$00,$06,$00,$40,$4A,$00,$67,$EA
	dc.b $00,$06,$00,$08,$C9,$42,$60,$E2,$54,$8D,$70,$2E,$60,$00,$58,$24
	dc.b $61,$00,$F2,$C0,$0C,$2E,$00,$03,$02,$39,$66,$04,$00,$06,$00,$40
	dc.b $61,$00,$EA,$EA,$8C,$02,$3A,$C6,$4E,$75,$0C,$2E,$00,$14,$01,$21
	dc.b $6D,$00,$04,$AC,$61,$00,$F6,$C6
loc_0_00002C8C:
	bsr.w loc_0_00001760
	or.b d2,d6
	move.w d6,(a5)+
	rts
	dc.b $10,$2E,$02,$39,$67,$F0,$B0,$3C,$00,$02,$67,$EA
loc_0_00002CA2:
	cmp.b #$3,d0
	bne.w loc_0_0000844A
	bset #6,d6
	bra.b loc_0_00002C8C
	dc.b $72,$0A,$70,$38,$60,$00,$57,$D0,$41,$EE,$0C,$24,$B2,$3C,$00,$0A
	dc.b $67,$3C,$B2,$3C,$00,$09,$67,$36,$B2,$3C,$00,$20,$67,$30,$04,$01
	dc.b $00,$30,$65,$2C,$B2,$3C,$00,$08,$64,$26,$70,$07,$90,$01,$12,$1C
	dc.b $B2,$3C,$00,$2B,$67,$0A,$B2,$3C,$00,$2D,$66,$14,$01,$90,$60,$02
	dc.b $01,$D0,$12,$1C,$B2,$3C,$00,$2C,$66,$04,$12,$1C,$60,$BE,$4E,$75
	dc.b $70,$4C,$60,$00,$57,$82,$61,$00,$3D,$CA,$4A,$82,$67,$00,$DF,$36
	dc.b $B2,$3C,$00,$09,$67,$06,$B2,$3C,$00,$20,$66,$04,$12,$1C,$60,$F0
	dc.b $61,$00,$DD,$16,$41,$FA,$00,$08,$2D,$48,$01,$7A,$72,$0A,$4E,$75
	dc.b $4A,$2E,$01,$1B,$66,$00,$57,$24,$41,$EE,$03,$E8,$76,$00,$61,$00
	dc.b $4A,$D8,$41,$EE,$03,$EE,$42,$2E,$01,$0A,$4E,$B9
	dc.l loc_0_0000AFDE
	dc.b $66,$00,$00,$86,$2D,$43,$01,$8A,$2D,$42,$01,$8E,$67,$68,$B4,$BC
	dc.b $FF,$FF,$FF,$FF,$66,$2A,$20,$6E,$01,$A2,$22,$28,$00,$0C,$20,$68
	dc.b $00,$08,$92,$88,$2D,$41,$01,$8E,$4A,$2E,$02,$38,$67,$48,$4A,$2E
	dc.b $01,$03,$67,$42,$24,$2E,$02,$3C,$61,$00,$69,$E8,$60,$00,$00,$38
	dc.b $4A,$2E,$02,$38,$67,$30,$4A,$2E,$01,$03,$67,$2A,$22,$02,$61,$00
	dc.b $63,$1A,$2F,$08,$22,$2E,$01,$8E,$26,$2E,$01,$8A,$4E,$B9
	dc.l loc_0_0000AFF6
	dc.b $22,$2E,$01,$8E,$20,$57,$24,$2E,$02,$3C,$61,$00,$69,$B4,$20,$5F
	dc.b $61,$00,$63,$0A,$26,$2E,$01,$8A,$42,$AE,$01,$8A,$4E,$B9
	dc.l loc_0_0000AFF2
	dc.b $72,$0A,$4E,$75,$70,$1A,$60,$00,$56,$AA,$47,$EE,$08,$32,$50,$EE
	dc.b $01,$2B,$60,$00,$18,$B0,$41,$EE,$03,$E8,$76,$0B,$61,$00,$4A,$26
	dc.b $50,$EE,$01,$0A,$61,$00,$5A,$5C,$66,$00,$56,$70,$72,$0A,$4E,$75
	dc.b $61,$00,$E8,$E0,$00,$64,$4A,$2E,$02,$39,$66,$00,$56,$3A,$4E,$75
	dc.b $50,$EE,$02,$3B,$61,$00,$E8,$CC,$00,$64,$51,$EE,$02,$3B,$B2,$3C
	dc.b $00,$2C,$66,$00,$56,$3A,$48,$E7,$18,$00,$12,$1C,$61,$00,$E9,$4C
	dc.b $4C,$DF,$00,$18,$66,$00,$E9,$38,$4A,$00,$67,$00,$E9,$32,$20,$6E
	dc.b $02,$4C,$D4,$02,$85,$10,$61,$00,$F5,$04,$08,$2E,$00,$02,$01,$0E
	dc.b $67,$6A,$4A,$04,$66,$66,$B6,$3C,$00,$02,$66,$60,$36,$10,$02,$43
	dc.b $00,$38,$B6,$3C,$00,$28,$66,$54,$30,$28,$00,$02,$67,$4E,$B0,$7C
	dc.b $00,$08,$6E,$48,$B0,$7C,$FF,$F8,$6D,$42,$36,$10,$02,$43,$00,$07
	dc.b $D6,$43,$B4,$03,$66,$36,$48,$E7,$80,$80,$24,$00,$55,$4D,$61,$00
	dc.b $5F,$3A,$4C,$DF,$01,$01,$66,$22,$E2,$4B,$4A,$40,$6A,$06,$08,$C3
	dc.b $00,$08,$44,$40,$02,$40,$00,$07,$EE,$58,$86,$40,$00,$43,$50,$48
	dc.b $30,$83,$70,$16,$60,$00,$59,$4E,$4E,$75,$54,$4D,$4E,$75,$0C,$2E
	dc.b $00,$14,$01,$21,$6D,$48,$10,$2E,$02,$39,$67,$4A,$B0,$3C,$00,$02
	dc.b $67,$44,$B0,$3C,$00,$03,$66,$00,$55,$6E,$3C,$3C,$48,$08,$61,$00
	dc.b $E8,$86,$8C,$02,$3A,$C6,$B2,$3C,$00,$2C,$66,$00,$55,$72,$12,$1C
	dc.b $B2,$3C,$00,$23,$66,$00,$55,$70,$12,$1C,$61,$00,$DE,$B6,$61,$00
	dc.b $EB,$AC,$08,$02,$00,$00,$66,$3E,$4A,$82,$6E,$3A,$4E,$75,$4A,$2E
	dc.b $02,$39,$66,$00,$55,$32,$61,$00,$E8,$4E,$8C,$02,$3A,$C6,$B2,$3C
	dc.b $00,$2C,$66,$00,$55,$3A,$12,$1C,$B2,$3C,$00,$23,$66,$00,$55,$38
	dc.b $12,$1C,$61,$00,$DE,$7E,$61,$00,$EB,$94,$08,$02,$00,$00,$66,$06
	dc.b $4A,$42,$6E,$02,$4E,$75,$70,$03,$60,$00,$56,$3E,$12,$1C,$61,$00
	dc.b $E7,$78,$61,$00,$49,$34,$4A,$2E,$02,$38,$67,$10,$4A,$2E,$09,$55
	dc.b $67,$0A,$3F,$01,$12,$02,$61,$00,$62,$10,$32,$1F,$B2,$3C,$00,$2C
	dc.b $67,$DA,$50,$EE,$01,$13,$4E,$75,$61,$00,$3B,$54,$B4,$BC,$00,$00
	dc.b $00,$26,$65,$00,$18,$8C,$B4,$BC,$00,$00,$00,$FF,$64,$00,$18,$82
	dc.b $3D,$42,$0B,$62,$50,$EE,$01,$13,$4E,$75,$B2,$3C,$00,$23,$66,$00
	dc.b $54,$C6,$12,$1C,$61,$00,$1F,$70,$3A,$C6,$61,$00,$EA,$EC,$B2,$3C
	dc.b $00,$2C,$66,$00,$54,$AA,$12,$1C,$61,$00,$E7,$22,$03,$3D,$4E,$75
	dc.b $20,$6E,$02,$4C,$52,$88,$53,$05,$67,$14,$4A,$2E,$01,$25,$67,$06
	dc.b $70,$65,$61,$00,$54,$AE,$10,$BC,$00,$7C,$70,$02,$60,$10,$10,$FC
	dc.b $00,$3C,$0C,$2E,$00,$03,$02,$39,$67,$00,$54,$5C,$4E,$75,$B0,$2E
	dc.b $02,$39,$67,$0C,$4A,$2E,$02,$39,$66,$00,$54,$4C,$1D,$40,$02,$39
	dc.b $4E,$75,$12,$1C,$30,$06,$3C,$3C,$02,$00,$B0,$7C,$C0,$00,$67,$94
	dc.b $7C,$00,$B0,$7C,$80,$00,$67,$8C,$3C,$3C,$0A,$00,$60,$86,$B2,$3C
	dc.b $00,$23,$67,$DE,$61,$00,$1E,$F0,$3A,$C6,$61,$00,$E8,$42,$B2,$3C
	dc.b $00,$2C,$66,$00,$54,$2A,$12,$1C,$10,$05,$02,$00,$00,$78,$66,$00
	dc.b $00,$42,$DA,$05,$52,$05,$8B,$2D,$FF,$FE,$61,$00,$E8,$2E,$20,$6E
	dc.b $02,$4C,$30,$3C,$00,$3C,$14,$05,$02,$02,$00,$78,$66,$1E,$30,$3C
	dc.b $00,$FD,$08,$06,$00,$0D,$66,$14,$10,$10,$E2,$08,$02,$40,$00,$07
	dc.b $81,$50,$DA,$05,$02,$50,$F0,$FF,$8B,$10,$4E,$75,$8B,$50,$60,$00
	dc.b $E6,$86,$08,$06,$00,$0D,$66,$00,$E6,$B6,$30,$3C,$00,$FD,$61,$00
	dc.b $E6,$70,$61,$00,$E6,$C8,$20,$6E,$02,$4C,$D4,$02,$85,$10,$4E,$75
	dc.b $22,$4C,$41,$FA,$00,$BA,$48,$81,$12,$36,$10,$7E,$B2,$18,$66,$00
	dc.b $00,$90,$12,$1C,$4A,$10,$66,$EE,$04,$01,$00,$30,$65,$70,$B2,$3C
	dc.b $00,$0A,$64,$6A,$74,$00,$14,$01,$C4,$FC,$00,$0A,$12,$1C,$04,$01
	dc.b $00,$30,$65,$5A,$B2,$3C,$00,$0A,$64,$54,$48,$81,$D4,$41,$12,$1C
	dc.b $C4,$FC,$00,$0A,$04,$01,$00,$30,$65,$44,$B2,$3C,$00,$0A,$64,$3E
	dc.b $48,$81,$D4,$41,$12,$1C,$4A,$42,$67,$3C,$B4,$7C,$00,$08,$67,$34
	dc.b $B4,$7C,$00,$0A,$67,$30,$B4,$7C,$00,$14,$67,$2A,$B4,$7C,$00,$1E
	dc.b $67,$24,$B4,$7C,$01,$4C,$67,$42,$B4,$7C,$00,$28,$67,$06,$B4,$7C
	dc.b $00,$3C,$66,$0A,$1D,$42,$01,$21,$50,$EE,$01,$22,$4E,$75,$70,$22
	dc.b $60,$00,$53,$50,$74,$00,$1D,$42,$01,$21,$51,$EE,$01,$22,$4E,$75
	dc.b $28,$49,$12,$2C,$FF,$FF,$41,$FA,$00,$1B,$48,$81,$12,$36,$10,$7E
	dc.b $B2,$18,$66,$DA,$12,$1C,$4A,$10,$66,$F0,$74,$20,$60,$D8,$4D,$43
	dc.b $36,$38,$00,$43,$50,$55,$33,$32,$00,$00
loc_0_0000316E:
	moveq.l #0,d2
loc_0_00003170:
	move.b (a4)+,d1
	cmp.b #$30,d1
	bcs.b loc_0_00003194
	cmp.b #$3A,d1
	bcc.b loc_0_00003194
	subi.b #48,d1
	ext.w d1
	ext.l d1
	add.l d2,d2
	move.l d2,d0
	add.l d2,d2
	add.l d2,d2
	add.l d0,d2
	add.l d1,d2
	bra.b loc_0_00003170
loc_0_00003194:
	subi.l #68000,d2
	bcs.b loc_0_000031E2
	beq.b loc_0_00003204
	cmp.l #$384,d2
	bgt.b loc_0_000031E2
	cmp.w #$8,d2
	beq.b loc_0_00003204
	cmp.w #$A,d2
	beq.b loc_0_00003204
	cmp.w #$14,d2
	beq.b loc_0_00003204
	cmp.w #$1E,d2
	beq.b loc_0_00003204
	cmp.w #$14C,d2
	beq.b loc_0_000031E4
	cmp.w #$28,d2
	beq.b loc_0_000031FE
	cmp.w #$3C,d2
	beq.b loc_0_000031FE
	cmp.w #$371,d2
	beq.b loc_0_000031F6
	cmp.w #$372,d2
	beq.b loc_0_000031EE
	cmp.w #$353,d2
	beq.b loc_0_000031E8
loc_0_000031E2:
	rts
loc_0_000031E4:
	moveq.l #32,d2
	bra.b loc_0_00003204
loc_0_000031E8:
	st.b $0123(a6)
	bra.b loc_0_0000320C
loc_0_000031EE:
	move.b #$52,$0122(a6)
	bra.b loc_0_0000320C
loc_0_000031F6:
	move.b #$51,$0122(a6)
	bra.b loc_0_0000320C
loc_0_000031FE:
	st.b $0122(a6)
	bra.b loc_0_00003208
loc_0_00003204:
	sf.b $0122(a6)
loc_0_00003208:
	move.b d2,$0121(a6)
loc_0_0000320C:
	cmp.b #$2F,d1
	beq.w loc_0_0000316E
	moveq.l #0,d0
	rts
	dc.b $61,$00,$1D,$00,$B2,$3C,$00,$23,$66,$00,$52,$48,$12,$1C,$61,$00
	dc.b $E4,$A4,$61,$16,$EE,$5A,$8C,$42,$B2,$3C,$00,$2C,$66,$00,$52,$2C
	dc.b $12,$1C,$61,$00,$E4,$AA,$00,$3F,$4E,$75,$4A,$2E,$02,$38,$67,$10
	dc.b $4A,$82,$67,$0E,$B4,$BC,$00,$00,$00,$08,$62,$0C,$66,$02,$74,$00
	dc.b $4E,$75,$4A,$2E,$01,$20,$66,$F8,$70,$1D,$60,$00,$52,$22,$61,$00
	dc.b $1B,$9E,$34,$2E,$02,$1C,$B4,$7C,$00,$03,$67,$20,$08,$02,$00,$01
	dc.b $66,$22,$B4,$7C,$00,$05,$67,$1C,$4A,$42,$66,$12,$61,$00,$47,$54
	dc.b $20,$4C,$12,$2C,$FF,$FF,$61,$00,$46,$58,$72,$0A,$4E,$75,$70,$06
	dc.b $60,$00,$52,$F2,$45,$EE,$01,$AE,$61,$00,$1B,$0C,$51,$EE,$01,$13
	dc.b $4E,$75,$12,$1C,$61,$00,$DB,$08,$4A,$04,$66,$00,$00,$82,$B6,$3C
	dc.b $00,$02,$66,$7A,$B2,$3C,$00,$2C,$66,$74,$28,$02,$2F,$0C,$12,$1C
	dc.b $61,$00,$E4,$B4,$66,$62,$4A,$00,$66,$30,$20,$04,$48,$80,$48,$C0
	dc.b $B8,$80,$66,$54,$08,$2E,$00,$03,$01,$0F,$67,$00,$00,$4C,$55,$8D
	dc.b $61,$00,$5A,$E4,$66,$40,$58,$8F,$00,$02,$00,$38,$D4,$02,$E1,$4A
	dc.b $84,$04,$3A,$C2,$70,$0F,$60,$00,$55,$08,$30,$44,$B8,$88,$66,$28
	dc.b $08,$2E,$00,$03,$01,$0E,$67,$00,$00,$20,$55,$8D,$61,$00,$5A,$B8
	dc.b $66,$14,$58,$8F,$D4,$02,$E1,$4A,$00,$42,$30,$7C,$3A,$C2,$3A,$C4
	dc.b $70,$17,$60,$00,$54,$DC,$54,$8D,$28,$5F,$72,$2C,$24,$04,$61,$00
	dc.b $E7,$68,$60,$3A,$30,$00,$10,$00,$30,$00,$20,$00,$70,$00,$10,$2E
	dc.b $02,$39,$D0,$00,$8C,$7B,$00,$EE,$3A,$C6,$B0,$3C,$00,$06,$66,$1A
	dc.b $B2,$3C,$00,$23,$66,$14,$08,$2E,$00,$03,$01,$0F,$66,$00,$FF,$44
	dc.b $08,$2E,$00,$03,$01,$0E,$66,$00,$FF,$3A,$61,$00,$E4,$FE,$B2,$3C
	dc.b $00,$2C,$66,$00,$50,$E6,$12,$1C,$08,$05,$00,$06,$66,$00,$00,$AC
	dc.b $20,$6E,$02,$4C,$8B,$50,$61,$00,$E4,$EE,$20,$6E,$02,$4C,$08,$05
	dc.b $00,$06,$66,$26,$34,$05,$30,$05,$02,$00,$00,$07,$D0,$00,$81,$10
	dc.b $02,$45,$00,$38,$DA,$45,$DA,$45,$DA,$45,$8B,$50,$02,$42,$00,$3F
	dc.b $B4,$7C,$00,$3A,$64,$00,$E3,$84,$4E,$75,$38,$10,$E2,$0D,$65,$2C
	dc.b $E2,$0D,$65,$50,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$50,$B0
	dc.b $10,$04,$02,$00,$00,$38,$B0,$3C,$00,$08,$66,$00,$E3,$5E,$02,$44
	dc.b $00,$07,$00,$44,$4E,$60,$30,$84,$60,$00,$EF,$5E,$3C,$3C,$44,$C0
	dc.b $0C,$2E,$00,$03,$02,$39,$66,$04,$61,$00,$50,$48,$02,$44,$00,$3F
	dc.b $10,$04,$02,$00,$00,$38,$B0,$3C,$00,$08,$67,$00,$E3,$2E,$8C,$44
	dc.b $30,$86,$4E,$75,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$50,$60
	dc.b $61,$00,$F3,$40,$3C,$3C,$46,$C0,$60,$D2,$24,$6E,$02,$4C,$E2,$0D
	dc.b $65,$3A,$E2,$0D,$65,$1C,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00
	dc.b $50,$3E,$61,$00,$E3,$1E,$3C,$3C,$4E,$68,$8C,$02,$34,$86,$60,$00
	dc.b $EE,$F8,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$50,$22,$34,$BC
	dc.b $40,$C0,$61,$00,$E2,$74,$00,$3D,$60,$00,$F2,$F8,$4A,$2E,$01,$21
	dc.b $66,$08,$61,$EA,$70,$04,$60,$00,$51,$0C,$34,$BC,$42,$C0,$61,$00
	dc.b $E2,$58,$00,$3D,$0C,$2E,$00,$03,$02,$39,$67,$00,$4F,$B6,$4E,$75
	dc.b $4A,$2E,$01,$21,$67,$00,$FC,$94,$4A,$2E,$01,$25,$67,$06,$70,$65
	dc.b $61,$00,$4F,$DC,$61,$00,$EE,$A2,$61,$00,$E2,$CC,$66,$26,$B2,$3C
	dc.b $00,$2C,$66,$00,$4F,$A6,$12,$1C,$3A,$FC,$4E,$7B,$E7,$08,$84,$00
	dc.b $02,$42,$00,$0F,$E8,$5A,$36,$02,$61,$36,$66,$00,$4F,$8A,$84,$43
	dc.b $3A,$C2,$4E,$75,$61,$2A,$66,$00,$4F,$7E,$B2,$3C,$00,$2C,$66,$00
	dc.b $4F,$7A,$12,$1C,$36,$02,$61,$00,$E2,$8E,$66,$00,$4F,$6A,$3A,$C6
	dc.b $E7,$08,$84,$00,$02,$42,$00,$0F,$E8,$5A,$86,$42,$3A,$C3,$4E,$75
	dc.b $10,$01,$48,$80,$10,$36,$00,$7E,$41,$FA,$00,$B4,$74,$00,$14,$18
	dc.b $67,$00,$00,$A8,$B0,$10,$66,$00,$00,$9A,$48,$E7,$A0,$88,$52,$88
	dc.b $10,$1C,$48,$80,$10,$36,$00,$7E,$B0,$18,$66,$00,$00,$82,$53,$02
	dc.b $66,$EE,$4F,$EF,$00,$10,$14,$18,$E1,$4A,$14,$18,$12,$1C,$10,$2E
	dc.b $01,$21,$67,$1E,$B0,$3C,$00,$28,$67,$3C,$B0,$3C,$00,$3C,$67,$1C
	dc.b $B0,$3C,$00,$20,$67,$06,$B0,$3C,$00,$0A,$66,$3E,$B4,$3C,$00,$02
	dc.b $65,$06,$70,$22,$61,$00,$4F,$18,$70,$00,$4E,$75,$B4,$7C,$08,$03
	dc.b $67,$F0,$B4,$7C,$08,$04,$67,$EA,$B4,$7C,$08,$05,$67,$E4,$B4,$7C
	dc.b $08,$02,$66,$E4,$60,$DC,$B4,$7C,$00,$08,$67,$D6,$B4,$7C,$08,$08
	dc.b $67,$D0,$B4,$7C,$08,$02,$66,$D0,$60,$C8,$B4,$7C,$08,$05,$64,$C2
	dc.b $B4,$7C,$08,$00,$64,$C2,$B4,$7C,$00,$03,$65,$BC,$60,$B4,$4C,$DF
	dc.b $11,$05,$41,$F0,$20,$03,$60,$00,$FF,$56,$70,$FF,$4E,$75,$02,$53
	dc.b $46,$43,$00,$00,$02,$44,$46,$43,$00,$01,$03,$43,$41,$43,$52,$00
	dc.b $02,$02,$55,$53,$50,$08,$00,$02,$56,$42,$52,$08,$01,$03,$43,$41
	dc.b $41,$52,$08,$02,$02,$4D,$53,$50,$08,$03,$02,$49,$53,$50,$08,$04
	dc.b $01,$54,$43,$00,$03,$03,$49,$54,$54,$30,$00,$04,$03,$49,$54,$54
	dc.b $31,$00,$05,$03,$44,$54,$54,$30,$00,$06,$03,$44,$54,$54,$31,$00
	dc.b $07,$04,$4D,$4D,$55,$53,$52,$08,$05,$02,$55,$52,$50,$08,$06,$02
	dc.b $53,$52,$50,$08,$07,$04,$42,$55,$53,$43,$52,$00,$08,$02,$50,$43
	dc.b $52,$08,$08,$00,$10,$2E,$02,$39,$67,$12,$B0,$3C,$00,$02,$67,$0C
	dc.b $B0,$3C,$00,$03,$66,$00,$4D,$FC,$00,$06,$00,$40,$61,$72,$66,$00
	dc.b $00,$4A,$B2,$3C,$00,$2C,$66,$00,$4E,$02,$12,$1C,$3A,$C6,$3A,$C4
	dc.b $61,$00,$E2,$14,$BA,$7C,$00,$40,$64,$00,$E0,$D0,$14,$05,$02,$02
	dc.b $00,$38,$B4,$3C,$00,$20,$66,$1C,$4A,$2E,$02,$38,$67,$16,$20,$6E
	dc.b $02,$4C,$20,$10,$74,$00,$76,$0F,$E3,$48,$E2,$52,$51,$CB,$FF,$FA
	dc.b $31,$42,$00,$02,$70,$34,$60,$00,$E0,$64,$00,$46,$04,$00,$3A,$C6
	dc.b $54,$8D,$61,$00,$E0,$34,$00,$6C,$B2,$3C,$00,$2C,$66,$00,$4D,$AC
	dc.b $12,$1C,$61,$0C,$66,$78,$20,$6E,$02,$4C,$31,$44,$00,$02,$4E,$75
	dc.b $78,$00,$61,$00,$E0,$B2,$67,$48,$41,$EE,$04,$6E,$48,$E7,$40,$08
	dc.b $61,$00,$3F,$DE,$66,$34,$24,$6E,$01,$6A,$48,$E7,$50,$1C,$61,$00
	dc.b $D4,$A0,$4C,$DF,$38,$0A,$66,$22,$0C,$29,$00,$05,$00,$0D,$66,$1A
	dc.b $28,$29,$00,$08,$4A,$2E,$02,$38,$67,$08,$08,$29,$00,$06,$00,$0C
	dc.b $67,$06,$50,$8F,$70,$00,$4E,$75,$70,$FF,$4C,$DF,$10,$02,$4E,$75
	dc.b $E7,$08,$D0,$02,$B2,$3C,$00,$2D,$67,$1A,$01,$C4,$B2,$3C,$00,$2F
	dc.b $67,$04,$70,$00,$4E,$75,$12,$1C,$61,$00,$E0,$4C,$67,$E2,$70,$39
	dc.b $60,$00,$4D,$48,$12,$1C,$B2,$3C,$00,$38,$64,$16,$B2,$3C,$00,$30
	dc.b $65,$10,$16,$00,$02,$00,$00,$08,$04,$01,$00,$30,$D0,$01,$12,$1C
	dc.b $60,$0E,$3F,$00,$61,$00,$E0,$20,$66,$D4,$E7,$08,$D0,$02,$36,$1F
	dc.b $B0,$03,$65,$CA,$52,$00,$07,$C4,$52,$03,$B6,$00,$66,$F8,$60,$AC
	dc.b $61,$00,$DF,$6C,$00,$FF,$48,$E7,$18,$00,$B2,$3C,$00,$2C,$66,$00
	dc.b $4C,$DA,$12,$1C,$61,$00,$DF,$DC,$4C,$DF,$00,$18,$D4,$02,$20,$6E
	dc.b $02,$4C,$85,$10,$10,$2E,$02,$39,$67,$0E,$B0,$3C,$00,$03,$67,$0E
	dc.b $B0,$3C,$00,$02,$66,$00,$4C,$9C,$00,$10,$00,$10,$4E,$75,$08,$2E
	dc.b $00,$03,$01,$0E,$67,$42,$4A,$04,$66,$3E,$B6,$3C,$00,$02,$66,$38
	dc.b $36,$10,$02,$43,$00,$3F,$B6,$3C,$00,$3C,$66,$2C,$20,$28,$00,$02
	dc.b $32,$40,$B0,$89,$66,$22,$48,$E7,$80,$80,$24,$00,$55,$4D,$61,$00
	dc.b $55,$E6,$4C,$DF,$01,$01,$66,$0E,$00,$10,$00,$10,$31,$40,$00,$02
	dc.b $70,$17,$60,$00,$50,$0C,$54,$4D,$4E,$75,$10,$2E,$02,$39,$B0,$3C
	dc.b $00,$01,$67,$00,$4C,$3E,$B0,$3C,$00,$03,$66,$04,$00,$06,$00,$40
	dc.b $61,$00,$DF,$64,$66,$24,$4A,$00,$66,$00,$00,$3A,$00,$06,$00,$80
	dc.b $02,$42,$00,$07,$EE,$5A,$8C,$42,$B2,$3C,$00,$2C,$66,$00,$4C,$2C
	dc.b $12,$1C,$61,$26,$3A,$C6,$3A,$C3,$4E,$75,$61,$1E,$B2,$3C,$00,$2C
	dc.b $66,$00,$4C,$18,$12,$1C,$61,$00,$DF,$10,$02,$42,$00,$07,$EE,$5A
	dc.b $8C,$42,$60,$E0,$70,$2F,$60,$00,$4C,$26,$74,$00,$0C,$2E,$00,$14
	dc.b $01,$21,$6D,$3A,$B2,$3C,$00,$28,$66,$3A,$12,$1C,$36,$02,$61,$00
	dc.b $DE,$F2,$66,$16,$8C,$02,$B2,$3C,$00,$2C,$66,$40,$12,$1C,$61,$00
	dc.b $DE,$20,$61,$00,$40,$2A,$36,$02,$60,$32,$61,$00,$DE,$14,$61,$00
	dc.b $40,$1E,$36,$02,$B2,$3C,$00,$2C,$66,$BA,$60,$00,$00,$16,$B2,$3C
	dc.b $00,$28,$67,$0E,$61,$00,$DD,$FA,$61,$00,$40,$04,$B2,$3C,$00,$28
	dc.b $66,$A2,$12,$1C,$36,$02,$61,$00,$DE,$AA,$8C,$02,$B2,$3C,$00,$29
	dc.b $66,$92,$12,$1C,$4E,$75,$B2,$3C,$00,$23,$66,$00,$4B,$96,$12,$1C
	dc.b $61,$00,$D4,$DC,$4A,$2E,$02,$38,$67,$2E,$61,$00,$3F,$F4,$4A,$43
	dc.b $6B,$42,$10,$02,$48,$80,$48,$C0,$B4,$80,$67,$1C,$B4,$BC,$00,$00
	dc.b $01,$00,$65,$06,$61,$00,$4B,$58,$60,$0E,$0C,$2E,$00,$03,$02,$39
	dc.b $67,$06,$70,$01,$61,$00,$4C,$7E,$1C,$02,$B2,$3C,$00,$2C,$66,$00
	dc.b $4B,$4A,$12,$1C,$61,$00,$DE,$42,$D4,$02,$70,$70,$80,$02,$1A,$C0
	dc.b $1A,$C6,$4E,$75,$2F,$02,$B2,$3C,$00,$2C,$66,$00,$4B,$2E,$12,$1C
	dc.b $61,$00,$DE,$26,$D4,$02,$70,$70,$80,$02,$1A,$C0,$24,$1F,$60,$00
	dc.b $60,$0C,$0C,$2E,$00,$0A,$01,$21,$6D,$00,$F7,$E0,$4A,$2E,$01,$25
	dc.b $67,$06,$70,$65,$61,$00,$4B,$28,$61,$00,$15,$B8,$3A,$C6,$61,$00
	dc.b $DE,$16,$66,$18,$76,$01,$61,$3C,$3A,$C3,$B2,$3C,$00,$2C,$66,$00
	dc.b $4A,$EA,$12,$1C,$61,$00,$DD,$62,$00,$3C,$4E,$75,$54,$8D,$61,$00
	dc.b $DD,$58,$00,$3C,$B2,$3C,$00,$2C,$66,$00,$4A,$D0,$12,$1C,$61,$00
	dc.b $DD,$E6,$66,$00,$F1,$F4,$76,$00,$61,$0A,$20,$6E,$02,$4C,$31,$43
	dc.b $00,$02,$4E,$75,$D4,$02,$4A,$00,$56,$C0,$02,$00,$00,$10,$86,$00
	dc.b $86,$02,$EA,$5B,$4E,$75,$61,$00,$E9,$B2,$61,$00,$DD,$22,$00,$3D
	dc.b $4E,$75,$B2,$3C,$00,$09,$67,$06,$B2,$3C,$00,$20,$66,$04,$12,$1C
	dc.b $60,$F0,$74,$00,$B2,$3C,$00,$0A,$67,$10,$B2,$3C,$00,$2A,$67,$0A
	dc.b $B2,$3C,$00,$3B,$67,$04,$61,$00,$30,$E2,$2F,$02,$61,$00,$3F,$D6
	dc.b $24,$1F,$43,$EE,$02,$56,$2D,$49,$01,$42,$23,$42,$00,$08,$42,$29
	dc.b $00,$0E,$2D,$42,$02,$3C,$41,$EE,$05,$A8,$2D,$48,$02,$4C,$1D,$7C
	dc.b $00,$02,$01,$08,$50,$EE,$01,$1B,$12,$2C,$FF,$FF
loc_0_00003A24:
	rts
	dc.b $61,$00,$30,$AA,$2F,$02,$61,$00,$5F,$70,$4C,$DF,$00,$04,$66,$30
	dc.b $2D,$42,$02,$3C,$41,$FA,$5E,$48,$2D,$48,$01,$7A,$12,$2C,$FF,$FF
	dc.b $50,$EE,$01,$12,$51,$EE,$01,$1C,$1D,$7C,$00,$0E,$01,$08,$10,$2E
	dc.b $02,$39,$67,$0A,$B0,$3C,$00,$03,$67,$04,$50,$EE,$01,$1C,$4E,$75
	dc.b $70,$45,$60,$00,$4A,$1C
loc_0_00003A6C:
	move.b (a4)+,d1
	beq.b loc_0_00003A90
	cmp.b #$20,d1
	beq.b loc_0_00003A6C
	cmp.b #$A,d1
	beq.b loc_0_00003A90
	cmp.b #$2B,d1
	beq.b loc_0_00003A92
	cmp.b #$2D,d1
	bne.w loc_0_00003A98
	bsr.w loc_0_00003B98
	beq.b loc_0_00003A6C
loc_0_00003A90:
	rts
loc_0_00003A92:
	bsr.w loc_0_00003E98
	bra.b loc_0_00003A6C
loc_0_00003A98:
	movem.l d1/a4,-(a7)
	ext.w d1
	move.b $7E(a6,d1.w),d1
	bsr.w loc_0_00003ED6
	beq.b loc_0_00003AB6
	bpl.b loc_0_00003AB0
	tst.b app_0841(a6)
	beq.b loc_0_00003AB2
loc_0_00003AB0:
	jsr (a0)
loc_0_00003AB2:
	addq.w #8,a7
	bra.b loc_0_00003ABE
loc_0_00003AB6:
	movem.l (a7)+,d1/a4
	bsr.w loc_0_00003AC2
loc_0_00003ABE:
	subq.w #1,a4
	bra.b loc_0_00003A6C
loc_0_00003AC2:
	tst.b app_0840(a6)
	beq.w loc_0_0000432C
	lea.l app_071A(a6),a1
	lea.l app_04FA(a6),a2
	move.l a2,app_04F4(a6)
	clr.b app_04F9(a6)
	lea.l app_0C30(a6),a3
	moveq.l #0,d2
	cmp.b #$22,d1
	bne.b loc_0_00003AEE
	move.b d1,d2
	move.b (a4)+,d1
	beq.w loc_0_00003D00
loc_0_00003AEE:
	moveq.l #0,d3
loc_0_00003AF0:
	move.b d1,(a2)+
	move.b d1,(a1)+
	move.b d1,(a3)+
	addq.b #1,app_04F9(a6)
	move.b (a4)+,d1
	beq.b loc_0_00003B26
	cmp.b #$A,d1
	beq.b loc_0_00003B26
	cmp.b #$20,d1
	beq.b loc_0_00003B22
	cmp.b #$2F,d1
	beq.b loc_0_00003AEE
	cmp.b d1,d2
	beq.b loc_0_00003B1E
	cmp.b #$2E,d1
	bne.b loc_0_00003AF0
	move.l a1,d3
	bra.b loc_0_00003AF0
loc_0_00003B1E:
	move.b (a4)+,d1
	bra.b loc_0_00003B26
loc_0_00003B22:
	tst.b d2
	bne.b loc_0_00003AF0
loc_0_00003B26:
	tst.l d3
	bne.b loc_0_00003B3A
	clr.b (a1)
	move.b #$2E,(a2)+
	move.b #$73,(a2)+
	addq.b #2,app_04F9(a6)
	bra.b loc_0_00003B44
loc_0_00003B3A:
	movea.l d3,a1
	clr.b (a1)
	lea.l $0516(a1),a1
	clr.b (a1)
loc_0_00003B44:
	move.b #$B,(a2)
	addq.b #1,app_04F9(a6)
	clr.b (a3)
	lea.l app_0C30(a6),a0
	bsr.w loc_0_00003B6A
	move.l a0,app_0C2C(a6)
	lea.l app_076C(a6),a3
loc_0_00003B5E:
	move.b (a0)+,(a3)+
	bne.b loc_0_00003B5E
	movea.l app_0C2C(a6),a0
	clr.b (a0)
	rts
loc_0_00003B6A:
	moveq.l #0,d0
	movea.l a0,a1
loc_0_00003B6E:
	move.b (a0)+,d1
	beq.b loc_0_00003B88
	cmp.b #$5C,d1
	beq.b loc_0_00003B84
	cmp.b #$2F,d1
	beq.b loc_0_00003B84
	cmp.b #$3A,d1
	bne.b loc_0_00003B6E
loc_0_00003B84:
	move.l a0,d0
	bra.b loc_0_00003B6E
loc_0_00003B88:
	tst.l d0
	bne.b loc_0_00003B92
	movea.l a1,a0
	moveq.l #-1,d0
	rts
loc_0_00003B92:
	movea.l d0,a0
	moveq.l #0,d0
	rts
loc_0_00003B98:
	move.b (a4)+,d1
	beq.b loc_0_00003BA8
	cmp.b #$20,d1
	beq.b loc_0_00003BA8
	cmp.b #$A,d1
	bne.b loc_0_00003BAC
loc_0_00003BA8:
	moveq.l #0,d0
	rts
loc_0_00003BAC:
	ext.w d1
	move.b $7E(a6,d1.w),d1
	cmp.b #$5B,d1
	bcc.b loc_0_00003BCA
	subi.b #65,d1
	bcs.b loc_0_00003C02
	add.b d1,d1
	ext.w d1
	lea.l loc_0_00003C12(pc,d1.w),a2
	adda.w (a2),a2
	jmp (a2)
loc_0_00003BCA:
	cmp.b #$7C,d1
	bne.b loc_0_00003C0E
	lea.l loc_0_00001442(pc),a0
	moveq.l #0,d1
	move.b (a4)+,d1
	bmi.b loc_0_00003C0E
	move.b $0(a0,d1.w),d1
	bmi.b loc_0_00003C0E
	moveq.l #0,d2
loc_0_00003BE2:
	lsl.l #4,d2
	or.b d1,d2
	move.b (a4)+,d1
	bmi.b loc_0_00003BF0
	move.b $0(a0,d1.w),d1
	bpl.b loc_0_00003BE2
loc_0_00003BF0:
	subq.w #1,a4
	tst.l $01A2(a6)
	bne.b loc_0_00003BFE
	jmp loc_0_0000A986.l
loc_0_00003BFE:
	moveq.l #0,d1
	rts
loc_0_00003C02:
	addi.b #65,d1
	cmp.b #$2E,d1
	beq.w loc_0_00003C96
loc_0_00003C0E:
	bra.w loc_0_00003D00
loc_0_00003C12:
	dc.b $00,$EE,$00,$72,$00,$46,$00,$50,$01,$EC,$00,$E4,$00,$7E,$01,$48
	dc.b $01,$28,$00,$DC,$00,$DA,$00,$88,$00,$56,$00,$D4,$01,$4A,$01,$8C
	dc.b $00,$30,$00,$CC,$00,$14,$00,$CC,$00,$C6,$02,$5C,$01,$34,$00,$3A
	dc.b $00,$BE,$00,$B4,$70,$00,$4E,$75,$43,$EE,$00,$FF
loc_0_00003C4E:
	tst.b app_0840(a6)
	beq.w loc_0_00003B98
	st.b (a1)
	bra.w loc_0_00003B98
	dc.b $43,$EE,$00,$FE,$60,$EC,$43,$EE,$0C,$26,$60,$E6,$4A,$2E,$08,$40
	dc.b $67,$00,$FF,$2A,$1D,$7C,$00,$01,$01,$04,$60,$00,$FF,$20,$43,$EE
	dc.b $01,$04,$60,$CE,$43,$EE,$02,$1B,$60,$C8,$4A,$2E,$08,$40,$67,$00
	dc.b $FF,$0C,$51,$EE,$01,$03,$60,$00,$FF,$04
loc_0_00003C96:
	lea.l $0127(a6),a1
	bra.b loc_0_00003C4E
	dc.b $4A,$2E,$08,$40,$67,$00,$FE,$F6,$51,$EE,$01,$03,$50,$EE,$01,$09
	dc.b $60,$00,$FE,$EA,$4A,$2E,$08,$40,$67,$00,$00,$08,$3D,$7C,$00,$02
	dc.b $02,$1C,$10,$14,$04,$00,$00,$30,$63,$00,$FE,$D2,$53,$00,$48,$80
	dc.b $B0,$7C,$00,$07,$64,$00,$FE,$C6,$01,$3C,$00,$6C,$67,$00,$00,$26
	dc.b $B0,$3C,$00,$06,$66,$00,$00,$04,$70,$02,$52,$4C,$4A,$2E,$08,$40
	dc.b $67,$00,$FE,$AA,$3D,$40,$02,$1C,$60,$00,$FE,$A2,$43,$EE,$02,$1A
	dc.b $60,$00,$FF,$50
loc_0_00003D00:
	moveq.l #-1,d0
	rts
	dc.b $74,$00,$14,$1C,$04,$02,$00,$30,$65,$F2,$B4,$3C,$00,$0A,$64,$EC
	dc.b $12,$14,$B2,$3C,$00,$30,$65,$1A,$B2,$3C,$00,$3A,$64,$14,$C4,$FC
	dc.b $00,$0A,$04,$01,$00,$30,$02,$41,$00,$FF,$D4,$41,$3D,$42,$0B,$6C
	dc.b $52,$4C,$4A,$42,$67,$C6,$4A,$2E,$08,$40,$67,$00,$FE,$58,$3D,$42
	dc.b $0B,$6C,$60,$00,$FE,$50,$47,$EE,$08,$32,$50,$EE,$01,$2B,$4A,$2E
	dc.b $08,$43,$67,$00,$00,$0A,$61,$00,$09,$3A,$70,$00,$4E,$75,$61,$00
	dc.b $09,$A6,$60,$F6,$47,$EE,$10,$E0,$51,$EE,$01,$2B,$60,$E4,$43,$EE
	dc.b $07,$E0,$60,$04,$43,$EE,$06,$C8
loc_0_00003D7C:
	moveq.l #81,d0
	moveq.l #0,d2
	cmpi.b #34,(a4)
	bne.b loc_0_00003D88
	move.b (a4)+,d2
loc_0_00003D88:
	move.b (a4)+,d1
	beq.b loc_0_00003DAE
	cmp.b #$A,d1
	beq.b loc_0_00003DAE
	cmp.b d2,d1
	beq.b loc_0_00003DB0
	cmp.b #$20,d1
	bne.b loc_0_00003DA0
	tst.b d2
	beq.b loc_0_00003DAE
loc_0_00003DA0:
	tst.b app_0840(a6)
	beq.w loc_0_00003DAA
	move.b d1,(a1)+
loc_0_00003DAA:
	subq.b #1,d0
	bne.b loc_0_00003D88
loc_0_00003DAE:
	subq.w #1,a4
loc_0_00003DB0:
	tst.b app_0840(a6)
	beq.w loc_0_00003DBA
	clr.b (a1)
loc_0_00003DBA:
	rts
	dc.b $4A,$2E,$08,$40,$67,$00,$00,$10,$50,$EE,$01,$00,$2D,$6E,$0C,$DA
	dc.b $09,$56,$50,$EE,$09,$54,$12,$14,$67,$00,$FD,$C2,$B2,$3C,$00,$20
	dc.b $67,$00,$FD,$BA,$B2,$3C,$00,$0A,$67,$00,$FD,$B2,$43,$EE,$07,$8E
	dc.b $60,$8E,$12,$1C,$67,$12,$B2,$3C,$00,$0A,$67,$0C,$B2,$3C,$00,$09
	dc.b $67,$F0,$B2,$3C,$00,$20,$67,$EA,$4E,$75,$4A,$2E,$08,$42,$66,$00
	dc.b $00,$2C,$61,$DE,$67,$22,$12,$1C,$67,$1E,$B2,$3C,$00,$0A,$67,$18
	dc.b $B2,$3C,$00,$09,$67,$00,$00,$12,$B2,$3C,$00,$20,$67,$00,$00,$0A
	dc.b $B2,$3C,$00,$2C,$66,$E0,$60,$DA,$53,$4C,$4E,$75,$61,$B4,$67,$5A
	dc.b $50,$C2,$41,$EE,$03,$E8,$42,$28,$00,$04,$61,$00,$38,$70,$66,$44
	dc.b $B2,$3C,$00,$3D,$67,$06,$74,$01,$76,$02,$60,$10,$12,$1C,$61,$00
	dc.b $CF,$5A,$4A,$04,$66,$2E,$B6,$3C,$00,$02,$66,$28,$41,$EE,$03,$E8
	dc.b $48,$E7,$60,$00,$61,$00,$CD,$5C,$4C,$DF,$00,$12,$67,$16,$45,$EE
	dc.b $01,$6A,$76,$02,$3F,$01,$61,$00,$CE,$32,$32,$1F,$B2,$3C,$00,$2C
	dc.b $66,$08,$60,$A8,$70,$51,$60,$00,$45,$F2,$60,$16
loc_0_00003E98:
	tst.b app_0841(a6)
	bne.b loc_0_00003EB4
loc_0_00003E9E:
	move.b (a4)+,d1
	beq.b loc_0_00003EAE
	cmp.b #$20,d1
	beq.b loc_0_00003EAE
	cmp.b #$A,d1
	bne.b loc_0_00003E9E
loc_0_00003EAE:
	subq.w #1,a4
	moveq.l #0,d0
	rts
loc_0_00003EB4:
	bsr.w loc_0_00004334
	bra.b loc_0_00003EAE
	dc.b $2F,$0C,$42,$6E,$02,$18,$61,$0C,$28,$5F,$52,$6E,$02,$18,$51,$EE
	dc.b $01,$02,$4E,$75,$2D,$4F,$02,$34,$60,$00,$04,$60
loc_0_00003ED6:
	lea.l loc_0_00003F3C(pc),a0
	moveq.l #0,d2
loc_0_00003EDC:
	move.b (a0)+,d2
	beq.b loc_0_00003F04
	cmp.b (a0),d1
	blt.b loc_0_00003F04
	bne.b loc_0_00003EFE
	lea.l $0001(a0),a1
	movea.l a4,a2
	move.b d2,d3
loc_0_00003EEE:
	subq.b #1,d3
	beq.b loc_0_00003F08
	move.b (a2)+,d0
	ext.w d0
	move.b $7E(a6,d0.w),d0
	cmp.b (a1)+,d0
	beq.b loc_0_00003EEE
loc_0_00003EFE:
	lea.l $2(a0,d2.w),a0
	bra.b loc_0_00003EDC
loc_0_00003F04:
	moveq.l #0,d0
	rts
loc_0_00003F08:
	move.b (a2),d0
	beq.b loc_0_00003F26
	cmp.b #$A,d0
	beq.b loc_0_00003F26
	cmp.b #$2C,d0
	beq.b loc_0_00003F26
	cmp.b #$9,d0
	beq.b loc_0_00003F26
	cmp.b #$20,d0
	beq.b loc_0_00003F26
	bra.b loc_0_00003EFE
loc_0_00003F26:
	move.b (a1)+,d0
	lsl.w #8,d0
	move.b (a1)+,d0
	lea.l -$2(a1,d0.w),a0
	movea.l a2,a4
	move.b (a4)+,d1
	lea.l loc_0_000042D3(pc),a2
	cmpa.l a2,a0
	rts
loc_0_00003F3C:
	dc.b $05,$41,$4C,$49,$4E,$4B,$02,$BE,$09,$41,$4C,$4C,$4F,$57,$5A,$45
	dc.b $52,$4F,$03,$54,$05,$41,$4D,$49,$47,$41,$02,$A2,$06,$41,$55,$54
	dc.b $4F,$50,$43,$02,$EF,$03,$42,$44,$4C,$02,$D7,$03,$42,$44,$57,$02
	dc.b $CB,$03,$42,$52,$42,$02,$A7,$03,$42,$52,$4C,$02,$AD,$03,$42,$52
	dc.b $53,$02,$9B,$03,$42,$52,$57,$02,$9B,$04,$43,$41,$53,$45,$01,$D8
	dc.b $06,$43,$48,$4B,$42,$49,$54,$02,$FB,$06,$43,$48,$4B,$49,$4D,$4D
	dc.b $02,$DA,$05,$43,$48,$4B,$50,$43,$02,$B6,$01,$44,$01,$D0,$05,$44
	dc.b $45,$42,$55,$47,$01,$C8,$04,$45,$56,$45,$4E,$02,$CB,$04,$46,$52
	dc.b $4F,$4D,$03,$5C,$06,$47,$45,$4E,$53,$59,$4D,$01,$A1,$04,$48,$43
	dc.b $4C,$4E,$02,$EC,$06,$48,$45,$41,$44,$45,$52,$03,$11,$06,$49,$4E
	dc.b $43,$44,$49,$52,$03,$16,$07,$49,$4E,$43,$4F,$4E,$43,$45,$02,$C4
	dc.b $07,$4C,$41,$54,$54,$49,$43,$45,$01,$E4,$04,$4C,$49,$4E,$45,$02
	dc.b $C9,$04,$4C,$49,$53,$54,$01,$B4,$05,$4C,$49,$53,$54,$31,$01,$B8
	dc.b $08,$4C,$4F,$43,$41,$4C,$44,$4F,$54,$02,$59,$06,$4C,$4F,$43,$41
	dc.b $4C,$55,$02,$48,$06,$4C,$4F,$57,$4D,$45,$4D,$02,$E7,$03,$4D,$45
	dc.b $58,$01,$AD,$0B,$4E,$4F,$41,$4C,$4C,$4F,$57,$5A,$45,$52,$4F,$02
	dc.b $6D,$08,$4E,$4F,$41,$55,$54,$4F,$50,$43,$02,$0E,$06,$4E,$4F,$43
	dc.b $41,$53,$45,$01,$23,$08,$4E,$4F,$43,$48,$4B,$42,$49,$54,$02,$3A
	dc.b $08,$4E,$4F,$43,$48,$4B,$49,$4D,$4D,$02,$17,$07,$4E,$4F,$43,$48
	dc.b $4B,$50,$43,$01,$F1,$07,$4E,$4F,$43,$4F,$44,$45,$53,$01,$0D,$07
	dc.b $4E,$4F,$44,$45,$42,$55,$47,$01,$09,$06,$4E,$4F,$45,$56,$45,$4E
	dc.b $01,$FC,$06,$4E,$4F,$48,$43,$4C,$4E,$02,$39,$09,$4E,$4F,$49,$4E
	dc.b $43,$4F,$4E,$43,$45,$02,$13,$06,$4E,$4F,$4C,$49,$4E,$45,$02,$24
	dc.b $06,$4E,$4F,$4C,$49,$53,$54,$01,$09,$07,$4E,$4F,$4C,$49,$53,$54
	dc.b $31,$01,$0B,$05,$4E,$4F,$4D,$45,$58,$01,$1B,$08,$4E,$4F,$53,$59
	dc.b $4D,$54,$41,$42,$00,$E0,$09,$4E,$4F,$54,$52,$41,$43,$45,$49,$46
	dc.b $00,$F8,$06,$4E,$4F,$54,$59,$50,$45,$00,$B3,$06,$4E,$4F,$57,$41
	dc.b $52,$4E,$00,$B6,$03,$4F,$44,$4C,$01,$54,$03,$4F,$44,$57,$01,$48
	dc.b $03,$4F,$4C,$44,$00,$E6,$05,$51,$55,$49,$45,$54,$02,$0C,$04,$53
	dc.b $52,$45,$43,$00,$ED,$05,$53,$55,$50,$45,$52,$00,$D5,$06,$53,$59
	dc.b $4D,$54,$41,$42,$00,$8A,$02,$54,$4F,$01,$AF,$07,$54,$52,$41,$43
	dc.b $45,$49,$46,$00,$9F,$04,$54,$59,$50,$45,$00,$5C,$04,$55,$53,$45
	dc.b $52,$00,$B5,$04,$57,$41,$52,$4E,$00,$5A,$07,$57,$41,$52,$4E,$42
	dc.b $49,$54,$01,$4C,$04,$57,$49,$54,$48,$01,$CD,$06,$58,$44,$45,$42
	dc.b $55,$47,$00,$22,$00,$00,$51,$EE,$00,$FE,$4E,$75,$50,$EE,$01,$09
	dc.b $51,$EE,$01,$03,$4E,$75,$50,$EE,$00,$FE,$4E,$75,$1D,$7C,$00,$01
	dc.b $01,$04,$4E,$75,$50,$EE,$01,$04,$4E,$75,$50,$EE,$01,$28,$4E,$75
	dc.b $51,$EE,$01,$04,$4E,$75,$51,$EE,$01,$07,$4E,$75,$50,$EE,$01,$07
	dc.b $4E,$75,$50,$EE,$01,$05,$4E,$75,$51,$EE,$01,$05,$4E,$75,$50,$EE
	dc.b $00,$FF,$4E,$75,$51,$EE,$00,$FF,$4E,$75,$50,$EE,$01,$00,$4E,$75
	dc.b $51,$EE,$01,$00,$4E,$75,$50,$EE,$02,$1A,$4E,$75,$51,$EE,$02,$1A
	dc.b $4E,$75,$50,$EE,$01,$26,$4E,$75,$51,$EE,$01,$26,$4E,$75,$50,$EE
	dc.b $01,$17,$4E,$75,$51,$EE,$01,$17,$4E,$75,$50,$EE,$01,$24,$4E,$75
	dc.b $51,$EE,$01,$25,$4E,$75,$50,$EE,$01,$25,$4E,$75,$70,$03,$60,$06
	dc.b $70,$05,$60,$02,$70,$02,$3D,$40,$02,$1C,$4A,$AE,$02,$24,$66,$00
	dc.b $01,$C6,$4A,$2E,$02,$38,$67,$00,$02,$D0,$4E,$75,$50,$EE,$01,$2C
	dc.b $4E,$75,$51,$EE,$01,$2C,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00
	dc.b $EF,$06,$1D,$7C,$00,$01,$01,$2C,$4E,$75,$50,$EE,$01,$2D,$4E,$75
	dc.b $51,$EE,$01,$2D,$4E,$75,$50,$EE,$01,$2E,$4E,$75,$51,$EE,$01,$2E
	dc.b $4E,$75,$50,$EE,$01,$19,$4E,$75,$51,$EE,$01,$19,$4E,$75,$50,$EE
	dc.b $01,$06,$4E,$75,$51,$EE,$01,$06,$4E,$75,$1D,$7C,$00,$5F,$01,$16
	dc.b $4E,$75,$1D,$7C,$00,$2E,$01,$16,$4E,$75,$50,$EE,$01,$1D,$4E,$75
	dc.b $51,$EE,$01,$1D,$4E,$75,$50,$EE,$01,$1F,$4E,$75,$51,$EE,$01,$1F
	dc.b $4E,$75,$50,$EE,$01,$1E,$4E,$75,$51,$EE,$01,$1E,$4E,$75,$1D,$7C
	dc.b $00,$01,$01,$1E,$4E,$75,$50,$EE,$01,$20,$4E,$75,$51,$EE,$01,$20
	dc.b $4E,$75,$50,$EE,$01,$34,$4E,$75,$51,$EE,$01,$34,$4E,$75,$50,$EE
	dc.b $01,$29,$50,$EE,$01,$2A,$4E,$75,$50,$EE,$01,$29,$51,$EE,$01,$2A
	dc.b $4E,$75,$51,$EE,$01,$29,$4E
loc_0_000042D3:
	dc.b $75,$61,$00,$FB,$18,$53,$4C,$4A,$2E,$08,$40,$67,$00,$00,$4C,$61
	dc.b $00,$FA,$94,$60,$48,$1F,$2E,$08,$40,$47,$EE,$10,$E0,$51,$EE,$01
	dc.b $2B,$60,$0C,$1F,$2E,$08,$43,$47,$EE,$08,$32,$50,$EE,$01,$2B,$61
	dc.b $00,$FA,$EA,$53,$4C,$4A,$1F,$60,$00,$FA,$4A,$50,$EE,$02,$1B,$4E
	dc.b $75,$50,$EE,$01,$27,$4E,$75,$61,$00,$FA,$D2,$60,$00,$F7,$A2,$61
	dc.b $00,$FA,$CA,$53,$4C,$43,$EE,$07,$E0
loc_0_0000432C:
	bsr.w loc_0_00003D7C
	move.b (a4)+,d1
	rts
loc_0_00004334:
	move.b (a4)+,d1
	st.b app_0844(a6)
	cmp.b #$A,d1
	beq.w loc_0_00003A24
	cmp.b #$9,d1
	beq.w loc_0_00003A24
	cmp.b #$20,d1
	beq.w loc_0_00003A24
	ext.w d1
	move.b $7E(a6,d1.w),d1
	beq.w loc_0_00003A24
	move.b (a4),d0
	cmp.b #$2B,d0
	beq.b loc_0_00004374
	cmp.b #$2D,d0
	beq.b loc_0_00004374
	bsr.w loc_0_00003ED6
	beq.b loc_0_00004374
	jsr (a0)
	bra.b loc_0_00004390
loc_0_00004374:
	subi.b #65,d1
	bcs.b loc_0_00004398
	cmp.b #$1A,d1
	bcc.b loc_0_00004398
	ext.w d1
	add.w d1,d1
	move.w loc_0_0000439E(pc,d1.w),d0
	beq.b loc_0_00004398
	move.b (a4)+,d1
	jsr loc_0_0000439E(pc,d0.w)
loc_0_00004390:
	cmp.b #$2C,d1
	beq.b loc_0_00004334
	rts
loc_0_00004398:
	moveq.l #58,d0
	bra.w loc_0_00008482
loc_0_0000439E:
	ori.l #192,(a2)+
	dc.b $00,$4E,$00,$AA,$00,$00,$00,$00,$00,$00,$00,$A2,$00,$00,$00,$00
	dc.b $00,$F2,$00,$64,$00,$00,$01,$66,$00,$6C,$00,$00,$00,$00,$00,$82
	dc.b $00,$5C,$00,$B2,$00,$00,$00,$8A,$00,$92,$00,$3A,$00,$00
loc_0_000043D2:
	moveq.l #64,d0
	bra.w loc_0_00008486
loc_0_000043D8:
	move.b (a4)+,d0
	exg d0,d1
	cmp.b #$2B,d0
	beq.b loc_0_000043EA
	cmp.b #$2D,d0
	bne.b loc_0_00004398
	tst.b d0
loc_0_000043EA:
	rts
loc_0_000043EC:
	bsr.b loc_0_000043D8
	seq.b d0
	andi.b #1,d0
	move.b d0,$0104(a6)
	rts
loc_0_000043FA:
	bsr.b loc_0_000043D8
	sne.b app_0107(a6)
	rts
loc_0_00004402:
	bsr.b loc_0_000043D8
	seq.b app_0117(a6)
	rts
loc_0_0000440A:
	cmp.b #$3D,d1
	bne.b loc_0_00004418
	bsr.w loc_0_0000316E
	bne.b loc_0_00004398
	rts
loc_0_00004418:
	bsr.b loc_0_000043D8
	seq.b $0106(a6)
	rts
loc_0_00004420:
	bsr.b loc_0_000043D8
	seq.b app_00FF(a6)
	rts
loc_0_00004428:
	bsr.b loc_0_000043D8
	seq.b app_0105(a6)
	rts
loc_0_00004430:
	bsr.b loc_0_000043D8
	seq.b $0104(a6)
	rts
loc_0_00004438:
	bsr.b loc_0_000043D8
	seq.b app_0119(a6)
	rts
loc_0_00004440:
	bsr.b loc_0_000043D8
	seq.b app_011D(a6)
	rts
loc_0_00004448:
	bsr.b loc_0_000043D8
	seq.b app_011F(a6)
	rts
loc_0_00004450:
	moveq.l #95,d2
	bsr.b loc_0_000043D8
	beq.b loc_0_00004458
	moveq.l #46,d2
loc_0_00004458:
	move.b d2,app_0116(a6)
	rts
loc_0_0000445E:
	bsr.w loc_0_0000455A
	bne.b loc_0_0000447A
	cmp.w #$8,d2
	bcs.w loc_0_00004398
	cmp.w #$80,d2
	bcc.w loc_0_00004398
	addq.w #1,d2
	move.w d2,app_021E(a6)
loc_0_0000447A:
	cmp.b #$2B,d1
	beq.b loc_0_00004488
	cmp.b #$2D,d1
	bne.b loc_0_0000448E
	tst.b d1
loc_0_00004488:
	sne.b app_00FE(a6)
	move.b (a4)+,d1
loc_0_0000448E:
	rts
loc_0_00004490:
	tst.l app_0224(a6)
	bne.w loc_0_000043D2
	move.b d1,d0
	move.b (a4)+,d1
	tst.b app_0238(a6)
	bne.b loc_0_00004502
	cmp.b #$2B,d0
	beq.b loc_0_000044E0
	cmp.b #$2D,d0
	beq.b loc_0_000044DC
	subi.b #48,d0
	bcs.w loc_0_00004398
	ext.w d0
	beq.b loc_0_000044DA
	subq.w #1,d0
	cmp.w #$7,d0
	bcc.w loc_0_00004398
	dc.b $01,$3C,$00,$6C,$67,$00,$FE,$CE,$B0,$3C,$00,$06,$66,$02,$70,$02
loc_0_000044D4:
	move.w d0,app_021C(a6)
	bra.b loc_0_000044E4
loc_0_000044DA:
	bra.b loc_0_000044E4
loc_0_000044DC:
	moveq.l #3,d0
	bra.b loc_0_000044D4
loc_0_000044E0:
	moveq.l #2,d0
	bra.b loc_0_000044D4
loc_0_000044E4:
	movea.l $0142(a6),a1
	movea.l $013E(a6),a0
	clr.l $0196(a6)
	tst.b app_0238(a6)
	bne.b loc_0_000044FA
	clr.l $01A6(a6)
loc_0_000044FA:
	bsr.w loc_0_000079A6
	move.b -$0001(a4),d1
loc_0_00004502:
	rts
loc_0_00004504:
	lea.l $010E(a6),a1
	ext.w d1
	move.b $7E(a6,d1.w),d1
	cmp.b #$57,d1
	bne.b loc_0_0000451A
	lea.l $0110(a6),a1
	move.b (a4)+,d1
loc_0_0000451A:
	cmp.b #$2D,d1
	beq.b loc_0_0000454E
	cmp.b #$2B,d1
	beq.b loc_0_00004552
	bsr.w loc_0_0000455A
	subq.w #1,d2
	bmi.w loc_0_00004398
	cmp.w #$B,d2
	bhi.w loc_0_00004398
	bsr.w loc_0_000043D8
	beq.b loc_0_00004546
	move.w (a1),d0
	bclr d2,d0
	move.w d0,(a1)
	rts
loc_0_00004546:
	move.w (a1),d0
	bset d2,d0
	move.w d0,(a1)
	rts
loc_0_0000454E:
	clr.w (a1)
	bra.b loc_0_00004556
loc_0_00004552:
	move.w #$FFFF,(a1)
loc_0_00004556:
	move.b (a4)+,d1
	rts
loc_0_0000455A:
	cmp.b #$30,d1
	bcs.b loc_0_0000458E
	cmp.b #$39,d1
	bhi.b loc_0_0000458E
	moveq.l #0,d2
	subi.b #48,d1
	move.b d1,d2
loc_0_0000456E:
	move.b (a4)+,d1
	cmp.b #$30,d1
	bcs.b loc_0_0000458C
	cmp.b #$3A,d1
	bcc.b loc_0_0000458C
	mulu.w #$A,d2
	subi.b #48,d1
	andi.w #15,d1
	add.w d1,d2
	bra.b loc_0_0000456E
loc_0_0000458C:
	moveq.l #0,d0
loc_0_0000458E:
	rts
loc_0_00004590:
	tst.b app_0954(a6)
	beq.b loc_0_000045C6
	lea.l app_078E(a6),a0
	tst.b (a0)
	bne.b loc_0_000045C2
	lea.l app_04F4(a6),a1
	moveq.l #0,d0
	move.b $0005(a1),d0
	subq.b #1,d0
	bmi.b loc_0_000045B4
	movea.l (a1),a1
loc_0_000045AE:
	move.b (a1)+,(a0)+
	dbf.w d0,loc_0_000045AE
loc_0_000045B4:
	clr.b (a0)
	lea.l app_078E(a6),a0
	lea.l loc_0_000045C8(pc),a2
	bsr.w loc_0_000045CE
loc_0_000045C2:
	bra.w open_output_file
loc_0_000045C6:
	rts
loc_0_000045C8:
	dc.b $2E,$6C,$73,$74,$00,$00
loc_0_000045CE:
	bsr.b loc_0_000045E2
	beq.b loc_0_000045D4
	movea.l d2,a1
loc_0_000045D4:
	subq.w #1,a1
loc_0_000045D6:
	move.b (a2)+,(a1)+
	bne.b loc_0_000045D6
	rts
loc_0_000045DC:
	bsr.b loc_0_000045E2
	beq.b loc_0_000045D4
	rts
loc_0_000045E2:
	movea.l a0,a1
loc_0_000045E4:
	moveq.l #0,d2
loc_0_000045E6:
	move.b (a1)+,d1
	beq.b loc_0_00004606
	cmp.b #$5C,d1
	beq.b loc_0_000045E4
	cmp.b #$2F,d1
	beq.b loc_0_000045E4
	cmp.b #$3A,d1
	beq.b loc_0_000045E4
	cmp.b #$2E,d1
	bne.b loc_0_000045E6
	move.l a1,d2
	bra.b loc_0_000045E6
loc_0_00004606:
	tst.l d2
	rts
	dc.b $4A,$2E,$01,$2B,$67,$F8,$20,$53,$10,$30,$30,$FF,$B0,$3C,$00,$3A
	dc.b $67,$EC,$B0,$3C,$00,$2F,$67,$E6,$B0,$3C,$00,$5C,$67,$E0,$72,$2F
	dc.b $20,$53,$B6,$6B,$00,$04,$65,$2E,$48,$E7,$E0,$60,$72,$64,$D2,$6B
	dc.b $00,$04,$61,$00,$4A,$7C,$22,$53,$26,$88,$32,$2B,$00,$04,$E4,$49
	dc.b $67,$08,$53,$41,$20,$D9,$51,$C9,$FF,$FC,$4C,$DF,$06,$07,$06,$6B
	dc.b $00,$64,$00,$04,$20,$53,$11,$81,$30,$00,$52,$43,$4E,$75
loc_0_00004668:
	moveq.l #MEMF_FAST,d1
	move.w d1,$0004(a3)
	bsr.w loc_0_000090BA
	move.l a0,(a3)
	clr.b (a0)
	rts
loc_0_00004678:
	movea.l (a3),a0
	clr.b (a0)
	moveq.l #0,d3
	tst.w $0004(a3)
	beq.b loc_0_00004694
	movea.l (a3),a0
loc_0_00004686:
	tst.b (a0)+
	beq.b loc_0_00004694
loc_0_0000468A:
	addq.w #1,d3
	tst.b (a0)+
	bne.b loc_0_0000468A
	addq.w #1,d3
	bra.b loc_0_00004686
loc_0_00004694:
	rts
	dc.b $12,$1C,$61,$E2,$74,$00,$B2,$3C,$00,$22,$67,$06,$B2,$3C,$00,$27
	dc.b $66,$04,$14,$01,$12,$1C,$67,$48,$B2,$3C,$00,$0A,$67,$42,$B2,$3C
	dc.b $00,$20,$66,$06,$4A,$02,$66,$1C,$60,$36,$B2,$3C,$00,$09,$67,$30
	dc.b $B2,$02,$67,$16,$B2,$3C,$00,$3B,$67,$06,$B2,$3C,$00,$2C,$66,$04
	dc.b $4A,$02,$67,$0E,$61,$00,$FF,$4E,$60,$CA,$12,$1C,$B2,$3C,$00,$2C
	dc.b $66,$0E,$61,$00,$FF,$20,$72,$00,$61,$00,$FF,$3A,$12,$1C,$60,$A4
	dc.b $61,$00,$FF,$12,$72,$00,$61,$00,$FF,$2C,$61,$00,$FF,$28,$12,$2C
	dc.b $FF,$FF,$4E,$75,$12,$1C,$74,$00,$B2,$3C,$00,$22,$67,$06,$B2,$3C
	dc.b $00,$27,$66,$04,$14,$01,$12,$1C,$67,$10,$B2,$3C,$00,$0A,$67,$0A
	dc.b $B2,$3C,$00,$20,$66,$06,$4A,$02,$66,$EC,$4E,$75,$B2,$3C,$00,$09
	dc.b $67,$F8,$B2,$02,$67,$10,$B2,$3C,$00,$3B,$67,$06,$B2,$3C,$00,$2C
	dc.b $66,$D4,$4A,$02,$66,$D0,$12,$1C,$B2,$3C,$00,$2C,$66,$DC,$12,$1C
	dc.b $60,$B4,$41,$EE,$06,$C8,$74,$00,$4A,$10,$67,$04,$72,$0A,$4E,$75
	dc.b $B2,$3C,$00,$0A,$67,$1A,$B2,$3C,$00,$09,$67,$14,$B2,$3C,$00,$20
	dc.b $67,$0E,$10,$C1,$12,$1C,$52,$02,$B4,$3C,$00,$52,$66,$E2,$72,$0A
	dc.b $42,$10,$4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00,$E9,$A0,$0C,$2E
	dc.b $00,$20,$01,$21,$67,$00,$E9,$96,$4A,$2E,$02,$39,$66,$00,$3C,$A6
	dc.b $61,$00,$D5,$78,$B2,$3C,$00,$2C,$66,$00,$3C,$B2,$12,$1C,$B2,$3C
	dc.b $00,$23,$66,$00,$3C,$B0,$12,$1C,$61,$00,$C5,$F6,$60,$00,$D3,$0C
	dc.b $61,$00,$DB,$88,$50,$EE,$02,$3B,$61,$00,$CF,$16,$00,$64,$4E,$75
	dc.b $4A,$2E,$02,$38,$67,$0A,$08,$EE,$00,$00,$0C,$24,$61,$00,$63,$6C
	dc.b $72,$0A,$50,$EE,$01,$13,$4E,$75,$08,$AE,$00,$00,$0C,$24,$4E,$75
	dc.b $61,$00,$22,$DA,$B4,$BC,$00,$00,$00,$0C,$65,$12,$B4,$BC,$00,$00
	dc.b $00,$FF,$64,$0A,$3D,$42,$0B,$64,$50,$EE,$01,$13,$4E,$75,$70,$4B
	dc.b $60,$00,$3C,$6E,$74,$00,$04,$01,$00,$30,$65,$4C,$B2,$3C,$00,$0A
	dc.b $64,$46,$14,$01,$12,$1C,$B2,$3C,$00,$0A,$67,$24,$B2,$3C,$00,$09
	dc.b $67,$1E,$B2,$3C,$00,$20,$67,$18,$04,$01,$00,$30,$65,$2A,$B2,$3C
	dc.b $00,$0A,$64,$24,$C4,$FC,$00,$0A,$02,$41,$00,$0F,$D4,$41,$12,$1C
	dc.b $70,$FC,$55,$82,$67,$18,$70,$FA,$5D,$82,$67,$12,$70,$00,$55,$82
	dc.b $67,$0C,$70,$FE,$5D,$82,$67,$06,$70,$5A,$60,$00,$3C,$14,$1D,$40
	dc.b $01,$2F,$4E,$75,$61,$00,$E2,$86,$61,$00,$EE,$48,$66,$00,$EE,$B2
	dc.b $74,$00,$34,$04,$24,$6E,$01,$6A,$41,$EE,$03,$E8,$48,$E7,$20,$1C
	dc.b $4A,$2E,$02,$38,$66,$18,$61,$00,$C2,$EA,$4C,$DF,$38,$10,$67,$00
	dc.b $3B,$90,$76,$05,$61,$00,$C4,$0E,$12,$2C,$FF,$FF,$4E,$75,$61,$00
	dc.b $C2,$D2,$4C,$DF,$38,$10,$66,$00,$3B,$7C,$0C,$29,$00,$05,$00,$0D
	dc.b $66,$00,$3B,$6E,$B8,$A9,$00,$08,$66,$00,$3B,$66,$08,$E9,$00,$06
	dc.b $00,$0C,$66,$00,$3B,$5C,$60,$D0,$01,$00,$01,$02,$41,$EE,$03,$E8
	dc.b $70,$00,$10,$2E,$02,$39,$B0,$3C,$00,$01,$67,$10,$08,$2E,$00,$00
	dc.b $08,$4D,$67,$08,$24,$2E,$08,$46,$D5,$AE,$08,$4A,$4A,$90,$66,$26
	dc.b $61,$00,$CD,$C4,$70,$00,$10,$2E,$02,$39,$10,$3B,$00,$CC,$E1,$AA
	dc.b $4A,$2E,$08,$46,$6A,$02,$44,$82,$20,$2E,$08,$4A,$D5,$AE,$08,$4A
	dc.b $24,$00,$60,$00,$E2,$54,$4A,$2E,$02,$38,$66,$48,$2F,$08,$61,$00
	dc.b $CD,$96,$20,$5F,$66,$6E,$4A,$04,$66,$6A,$2A,$02,$61,$00,$C2,$8A
	dc.b $67,$00,$3A,$EE,$45,$EE,$01,$6A,$76,$02,$28,$2E,$08,$4A,$10,$28
	dc.b $00,$06,$B0,$2E,$01,$16,$67,$0C,$61,$00,$C3,$56,$24,$05,$12,$2C
	dc.b $FF,$FF,$60,$A0,$45,$EE,$01,$5A,$4A,$92,$67,$00,$3A,$D0,$61,$00
	dc.b $C3,$D6,$60,$E8,$61,$00,$C2,$52,$66,$00,$3A,$CE,$0C,$29,$00,$02
	dc.b $00,$0D,$66,$00,$3A,$C4,$20,$29,$00,$08,$B0,$AE,$08,$4A,$66,$00
	dc.b $3A,$A8,$08,$E9,$00,$06,$00,$0C,$66,$00,$3A,$96,$61,$00,$CD,$28
	dc.b $60,$00,$FF,$62,$4E,$75,$61,$00,$21,$1A,$4A,$82,$6B,$00,$F0,$B2
	dc.b $2F,$02,$61,$00,$4F,$FE,$4C,$DF,$00,$04,$66,$00,$F0,$A4,$42,$AE
	dc.b $01,$82,$94,$AE,$02,$3C,$2D,$42,$01,$8E,$12,$2C,$FF,$FF,$4E,$75
	dc.b $94,$81,$65,$0E,$67,$0A,$28,$02,$76,$00,$72,$00,$61,$00,$DF,$74
	dc.b $70,$00,$4E,$75,$42,$AE,$08,$4A,$72,$0A,$4E,$75,$61,$00,$CC,$D8
	dc.b $66,$F2,$4A,$04,$66,$EE,$2D,$42,$08,$4A,$60,$00,$E1,$7C,$0C,$2E
	dc.b $00,$0A,$01,$21,$6D,$00,$E7,$26,$3A,$C6,$B2,$3C,$00,$23,$66,$00
	dc.b $3A,$54,$12,$1C,$61,$00,$C3,$9A,$60,$00,$D0,$B0,$0C,$2E,$00,$14
	dc.b $01,$21,$66,$00,$E7,$08,$61,$0E,$8C,$42,$3A,$C6,$4A,$2E,$02,$39
	dc.b $66,$00,$3A,$12,$4E,$75,$61,$00,$CD,$40,$66,$0E,$02,$42,$00,$07
	dc.b $02,$40,$00,$01,$E7,$48,$84,$40,$4E,$75,$70,$2E,$60,$00,$3A,$32
	dc.b $61,$00,$D9,$1A,$50,$EE,$02,$3B,$61,$00,$CC,$86,$00,$3D,$4E,$75
	dc.b $61,$1C,$44,$41,$54,$41,$00,$00,$61,$14,$42,$53,$53,$00,$61,$0E
	dc.b $54,$45,$58,$54,$00,$00,$61,$06,$43,$4F,$44,$45,$00,$00,$20,$5F
	dc.b $43,$EE,$04,$6E,$61,$00,$4B,$E8,$12,$FC,$00,$0A,$48,$E7,$40,$08
	dc.b $49,$EE,$04,$6E,$12,$1C,$61,$7A,$4C,$DF,$10,$02,$4E,$75,$41,$EE
	dc.b $04,$6E,$10,$C1,$12,$1C,$B2,$3C,$00,$09,$67,$4C,$B2,$3C,$00,$20
	dc.b $67,$46,$B2,$3C,$00,$2C,$67,$0A,$B2,$3C,$00,$0A,$67,$3A,$10,$C1
	dc.b $60,$E2,$10,$1C,$43,$FA,$00,$38,$04,$00,$00,$30,$65,$3E,$67,$10
	dc.b $43,$FA,$00,$31,$53,$00,$67,$08,$43,$FA,$00,$2E,$53,$00,$66,$2C
	dc.b $10,$FC,$00,$2C,$08,$2E,$00,$01,$02,$1D,$66,$04,$41,$EE,$04,$6E
	dc.b $12,$1C,$10,$D9,$66,$FC,$53,$88,$10,$BC,$00,$0A,$60,$8E,$43,$4F
	dc.b $44,$45,$00,$44,$41,$54,$41,$00,$42,$53,$53,$00,$70,$66,$60,$00
	dc.b $39,$6C,$61,$00,$2E,$B2,$12,$2C,$FF,$FF,$76,$01,$61,$00,$2E,$2E
	dc.b $72,$0A,$4E,$75,$61,$00,$DF,$D6,$4A,$2E,$02,$38,$66,$48,$2F,$08
	dc.b $61,$00,$1F,$7A,$20,$5F,$48,$E7,$30,$00,$61,$00,$C0,$8C,$4C,$DF
	dc.b $00,$30,$66,$10,$08,$29,$00,$07,$00,$0C,$67,$00,$38,$E4,$16,$05
	dc.b $24,$04,$60,$42,$48,$7A,$00,$16,$16,$05,$45,$EE,$01,$6A,$55,$05
	dc.b $67,$00,$C1,$4E,$45,$EE,$01,$62,$60,$00,$C1,$46,$08,$E9,$00,$07
	dc.b $00,$0C,$60,$00,$E0,$00,$61,$00,$C0,$50,$66,$00,$38,$CC,$08,$29
	dc.b $00,$07,$00,$0C,$67,$00,$38,$C2,$2F,$09,$61,$00,$CB,$16,$22,$5F
	dc.b $08,$E9,$00,$06,$00,$0C,$23,$42,$00,$08,$B6,$29,$00,$0D,$66,$00
	dc.b $38,$90,$60,$00,$DF,$D4,$B2,$3C,$00,$23,$67,$5C,$54,$8D,$61,$00
	dc.b $CC,$BC,$10,$05,$02,$00,$00,$78,$67,$2C,$34,$06,$02,$42,$00,$18
	dc.b $ED,$4A,$02,$46,$FF,$00,$00,$46,$00,$C0,$8C,$42,$20,$6E,$02,$4C
	dc.b $30,$86,$61,$00,$DB,$90,$70,$3C,$60,$00,$CB,$24,$00,$46,$02,$00
	dc.b $8C,$05,$3A,$C6,$4E,$75,$2A,$6E,$02,$4C,$61,$00,$03,$28,$B2,$3C
	dc.b $00,$2C,$66,$E8,$00,$06,$00,$20,$3A,$86,$DA,$05,$8B,$1D,$12,$1C
	dc.b $61,$00,$CB,$58,$85,$1D,$4E,$75,$12,$1C,$61,$00,$CA,$BA,$61,$00
	dc.b $E6,$2C,$EE,$5A,$8C,$42,$61,$00,$02,$FC,$B2,$3C,$00,$2C,$66,$00
	dc.b $38,$3C,$12,$1C,$61,$00,$CB,$34,$8C,$02,$3A,$C6,$4E,$75,$61,$00
	dc.b $CA,$96,$B4,$BC,$00,$00,$00,$FF,$64,$00,$FB,$D4,$4A,$2E,$02,$38
	dc.b $67,$10,$4A,$2E,$09,$55,$67,$0A,$38,$02,$61,$00,$42,$3A,$53,$44
	dc.b $66,$F8,$12,$2C,$FF,$FF,$50,$EE,$01,$13,$4E,$75,$4A,$2E,$01,$25
	dc.b $67,$06,$70,$65,$61,$00,$38,$1A,$3A,$C6,$B2,$3C,$00,$23,$66,$00
	dc.b $37,$F4,$12,$1C,$61,$00,$C1,$3A,$61,$00,$CE,$50,$4A,$2E,$02,$39
	dc.b $66,$00,$37,$C2,$4E,$75,$61,$00,$DA,$DC,$61,$00,$CA,$CE,$8C,$02
	dc.b $3A,$C6,$4E,$75,$61,$00,$D6,$D6,$61,$00,$CA,$46,$00,$3D,$4E,$75
	dc.b $4A,$2E,$02,$39,$66,$00,$37,$9E,$B2,$3C,$00,$23,$66,$00,$37,$B6
	dc.b $12,$1C,$61,$00,$C9,$EE,$61,$00,$2C,$1A,$8C,$02,$3A,$C6,$B4,$BC
	dc.b $00,$00,$00,$10,$64,$02,$4E,$75,$70,$1D,$60,$00,$37,$B4,$0C,$2E
	dc.b $00,$14,$01,$21,$6D,$00,$E4,$56,$61,$00,$D6,$70,$3A,$FC,$4C,$40
	dc.b $3A,$C6,$61,$00,$C9,$F6,$00,$FD,$B2,$3C,$00,$2C,$66,$00,$37,$6E
	dc.b $12,$1C,$61,$00,$CA,$66,$20,$6E,$02,$4C,$B2,$3C,$00,$3A,$67,$0C
	dc.b $85,$28,$00,$03,$E9,$0A,$85,$28,$00,$02,$4E,$75,$12,$1C,$85,$28
	dc.b $00,$03,$61,$00,$CA,$46,$20,$6E,$02,$4C,$E9,$0A,$85,$28,$00,$02
	dc.b $4E,$75,$0C,$2E,$00,$14,$01,$21,$6D,$00,$E4,$02,$3A,$C6,$20,$6E
	dc.b $02,$4C,$52,$88,$10,$2E,$02,$39,$67,$3A,$B0,$3C,$00,$03,$67,$1E
	dc.b $B0,$3C,$00,$02,$66,$00,$36,$FE,$B2,$3C,$00,$23,$66,$00,$37,$16
	dc.b $12,$1C,$00,$10,$00,$02,$61,$00,$C0,$58,$60,$00,$CD,$6E,$B2,$3C
	dc.b $00,$23,$66,$00,$37,$00,$12,$1C,$00,$10,$00,$03,$61,$00,$C0,$42
	dc.b $60,$00,$CD,$38,$B2,$3C,$00,$23,$67,$CE,$00,$10,$00,$04,$4E,$75
	dc.b $61,$00,$01,$92,$61,$00,$C9,$5A,$00,$3D,$4E,$75,$0C,$2E,$00,$14
	dc.b $01,$21,$6D,$EC,$61,$00,$01,$7E,$61,$00,$C9,$46,$00,$FF,$4E,$75
	dc.b $45,$EE,$0B,$82,$50,$EE,$01,$13,$74,$00,$76,$0A,$4A,$2E,$02,$38
	dc.b $66,$08,$4A,$12,$67,$04,$72,$0A,$4E,$75,$B2,$3C,$00,$27,$66,$04
	dc.b $76,$27,$12,$1C,$B6,$01,$67,$14,$B2,$3C,$00,$0A,$67,$16,$14,$C1
	dc.b $52,$02,$B4,$3C,$00,$50,$66,$EA,$72,$0A,$60,$08,$B6,$3C,$00,$0A
	dc.b $67,$02,$12,$1C,$42,$12,$4E,$75,$45,$EE,$0B,$D3,$60,$B6,$61,$00
	dc.b $C9,$74,$8C,$02,$3A,$C6,$4A,$2E,$02,$39,$66,$00,$36,$48,$4E,$75
	dc.b $0C,$6E,$00,$03,$02,$1C,$67,$02,$4E,$75,$58,$8F,$72,$0A,$4E,$75
	dc.b $12,$1C,$61,$EC,$41,$EE,$03,$E8,$61,$00,$28,$98,$66,$00,$36,$62
	dc.b $3F,$01,$61,$0A,$32,$1F,$B2,$3C,$00,$2C,$67,$E4,$4E,$75,$10,$28
	dc.b $00,$06,$B0,$2E,$01,$16,$67,$00,$36,$04,$4A,$2E,$02,$38,$67,$1A
	dc.b $61,$00,$BD,$86,$66,$16
loc_0_00004E4C:
	move.b $000C(a1),d0
	andi.b #144,d0
	bne.b loc_0_00004E62
	bset.b #5,$000C(a1)
	beq.w loc_0_000096D6
	rts
loc_0_00004E62:
	moveq.l #44,d0
	bra.w loc_0_00008486
	dc.b $70,$2B,$60,$00,$36,$16,$12,$1C,$60,$04,$7A,$2C,$61,$90,$41,$EE
	dc.b $03,$E8,$61,$00,$28,$3C,$66,$00,$36,$06,$10,$28,$00,$06,$B0,$2E
	dc.b $01,$16,$67,$DC,$76,$01,$0C,$2E,$00,$03,$02,$39,$66,$02,$76,$02
	dc.b $3F,$01,$3F,$03,$61,$00,$BD,$30,$4C,$9F,$00,$08,$67,$0A,$22,$6E
	dc.b $01,$66,$78,$00,$61,$00,$BE,$0C,$61,$12,$32,$1F,$1A,$01,$B2,$3C
	dc.b $00,$2C,$67,$B2,$B2,$3C,$00,$3D,$67,$AC,$4E,$75,$08,$2E,$00,$02
	dc.b $02,$1D,$66,$46,$B6,$29,$00,$0D,$66,$40,$08,$29,$00,$05,$00,$0C
	dc.b $66,$38,$08,$29,$00,$07,$00,$0C,$66,$30,$10,$29,$00,$17,$B0,$2E
	dc.b $01,$16,$67,$26,$08,$E9,$00,$04,$00,$0C,$66,$1C,$20,$6E,$01,$3E
	dc.b $BA,$3C,$00,$2C,$67,$08,$08,$E9,$00,$02,$00,$0C,$60,$04,$52,$68
	dc.b $00,$14,$33,$68,$00,$14,$00,$14,$4E,$75,$30,$3C,$00,$2B,$60,$00
	dc.b $35,$6E,$70,$00,$10,$2E,$02,$39,$8C,$3B,$00,$04,$4E,$75,$40,$00
	dc.b $40,$80,$2D,$4D,$08,$6E,$B2,$3C,$00,$5B,$67,$00,$00,$A8,$7E,$00
	dc.b $47,$EE,$08,$4E,$41,$EE,$08,$A0,$2D,$48,$09,$40,$48,$6C,$FF,$FF
	dc.b $61,$00,$04,$64,$24,$5F,$66,$00,$07,$68,$08,$07,$00,$00,$66,$34
	dc.b $B2,$3C,$00,$29,$66,$00,$00,$B0,$08,$07,$00,$01,$67,$00,$00,$C0
	dc.b $4A,$2B,$00,$09,$66,$00,$00,$B8,$10,$2B,$00,$08,$6B,$00,$00,$B0
	dc.b $7A,$10,$8A,$00,$12,$1C,$B2,$3C,$00,$2B,$66,$06,$08,$C5,$00,$03
	dc.b $12,$1C,$4E,$75,$B2,$3C,$00,$2C,$67,$00,$00,$82,$12,$1C,$B2,$3C
	dc.b $00,$2E,$66,$00,$00,$10,$24,$13,$36,$2B,$00,$04,$18,$2B,$00,$06
	dc.b $60,$00,$C9,$DE,$B2,$3C,$00,$09,$67,$00,$00,$18,$B2,$3C,$00,$20
	dc.b $67,$00,$00,$10,$B2,$3C,$00,$2C,$67,$08,$B2,$3C,$00,$0A,$66,$00
	dc.b $C9,$62,$28,$4A,$12,$2C,$FF,$FF,$61,$00,$C2,$36,$61,$00,$C9,$5A
	dc.b $60,$00,$C2,$2E,$7E,$00,$47,$EE,$08,$4E,$48,$47,$08,$C7,$00,$07
	dc.b $66,$00,$06,$CE,$47,$EE,$08,$5E,$41,$EE,$08,$F0,$2D,$48,$09,$40
	dc.b $12,$1C,$B2,$3C,$00,$5D,$67,$34,$B2,$3C,$00,$29,$67,$20,$61,$00
	dc.b $03,$A6,$66,$00,$06,$AC,$B2,$3C,$00,$2C,$66,$E6,$12,$1C,$B2,$3C
	dc.b $00,$5B,$66,$EA,$4A,$2B,$00,$0E,$6E,$C0,$60,$00,$06,$94,$4A,$2B
	dc.b $00,$0E,$6F,$00,$06,$8C,$12,$1C,$60,$00,$00,$1C,$4A,$2B,$00,$0E
	dc.b $6C,$00,$06,$7E,$48,$47,$47,$EE,$08,$4E,$41,$EE,$08,$A0,$2D,$48
	dc.b $09,$40,$12,$1C,$60,$C0,$4A,$2B,$00,$0E,$6C,$0E,$48,$47,$47,$EE
	dc.b $08,$4E,$41,$EE,$08,$A0,$2D,$48,$09,$40,$24,$07,$02,$82,$00,$07
	dc.b $00,$07,$20,$02,$48,$40,$E7,$48,$80,$42,$D0,$40,$D0,$40,$7A,$30
	dc.b $08,$07,$00,$03,$67,$02,$7A,$3B,$08,$07,$00,$17,$67,$00,$04,$CC
	dc.b $18,$2E,$01,$21,$B8,$3C,$00,$20,$67,$00,$E0,$A0,$38,$3C,$01,$D0
	dc.b $24,$3B,$00,$20,$88,$42,$48,$42,$2F,$0D,$3A,$C4,$4E,$BB,$20,$14
	dc.b $20,$5F,$08,$04,$00,$06,$67,$04,$08,$84,$00,$02,$30,$84,$70,$00
	dc.b $4E,$75,$01,$20,$00,$01,$01,$20,$00,$01,$01,$00,$00,$01,$01,$00
	dc.b $00,$01,$01,$20,$00,$01,$01,$20,$00,$01,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$20,$00,$05,$01,$20,$00,$05,$01,$00,$00,$05,$01,$00
	dc.b $00,$05,$01,$20,$00,$05,$01,$20,$00,$05,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$20,$00,$05,$01,$20,$00,$05,$01,$00,$00,$05,$01,$00
	dc.b $00,$05,$01,$20,$00,$05,$01,$20,$00,$05,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$20,$00,$05,$01,$20,$00,$05,$01,$00,$00,$05,$01,$00
	dc.b $00,$05,$01,$20,$00,$05,$01,$20,$00,$05,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$62,$00,$01,$01,$62,$00,$01,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$62,$00,$01,$01,$62,$00,$01,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$62,$00,$01,$01,$62,$00,$01,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$01,$62,$00,$01,$01,$62,$00,$01,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE,$00,$00,$05,$FE
	dc.b $00,$00,$08,$87,$00,$01,$08,$C7,$00,$02,$70,$08,$D0,$2E,$08,$56
	dc.b $1D,$40,$08,$58,$1D,$6E,$08,$57,$08,$69,$51,$EE,$08,$5A,$51,$EE
	dc.b $08,$5B,$47,$EE,$08,$5E,$41,$EE,$08,$F0,$2D,$48,$09,$40,$08,$07
	dc.b $00,$10,$67,$04,$61,$00,$00,$86,$08,$07,$00,$11,$67,$04,$61,$00
	dc.b $00,$66,$47,$EE,$08,$4E,$41,$EE,$08,$A0,$2D,$48,$09,$40,$08,$07
	dc.b $00,$02,$67,$04,$61,$00,$00,$FC,$08,$07,$00,$00,$67,$04,$61,$00
	dc.b $01,$1C,$4E,$75,$47,$EE,$08,$5E,$41,$EE,$08,$F0,$2D,$48,$09,$40
	dc.b $08,$07,$00,$10,$67,$04,$61,$00,$00,$44,$08,$07,$00,$11,$67,$04
	dc.b $61,$00,$00,$24,$08,$07,$00,$12,$67,$04,$61,$00,$00,$C6,$47,$EE
	dc.b $08,$4E,$41,$EE,$08,$A0,$2D,$48,$09,$40,$08,$07,$00,$00,$67,$04
	dc.b $61,$00,$00,$DA,$4E,$75,$4A,$2B,$00,$09,$66,$0E,$08,$84,$00,$07
	dc.b $08,$07,$00,$03,$66,$04,$8A,$2B,$00,$08,$4E,$75,$24,$13,$36,$2B
	dc.b $00,$04,$08,$2E,$00,$07,$01,$0F,$67,$40,$B6,$3C,$00,$01,$66,$1C
	dc.b $2F,$02,$94,$AE,$02,$3C,$20,$2E,$08,$6E,$90,$AE,$02,$4C,$94,$80
	dc.b $30,$42,$B1,$C2,$4C,$DF,$00,$04,$66,$20,$60,$06,$30,$42,$B1,$C2
	dc.b $66,$18,$4A,$2B,$00,$06,$66,$12,$61,$00,$3B,$1C,$66,$0C,$17,$7C
	dc.b $00,$01,$00,$07,$70,$13,$61,$00,$35,$48,$10,$2B,$00,$07,$B0,$3C
	dc.b $00,$03,$67,$00,$03,$C8,$53,$00,$67,$24,$6A,$06,$4A,$2E,$01,$2D
	dc.b $66,$1C,$00,$04,$00,$30,$08,$07,$00,$03,$67,$00,$C7,$CC,$4A,$2B
	dc.b $00,$09,$66,$00,$C7,$C4,$08,$C5,$00,$00,$60,$00,$04,$12,$08,$C4
	dc.b $00,$05,$08,$84,$00,$04,$08,$07,$00,$03,$67,$00,$C7,$CC,$60,$00
	dc.b $03,$BC,$4A,$2B,$00,$0B,$66,$22,$08,$84,$00,$06,$70,$0F,$C0,$2B
	dc.b $00,$0A,$E8,$58,$88,$40,$70,$01,$C0,$2B,$00,$0C,$EA,$58,$88,$40
	dc.b $70,$03,$C0,$2B,$00,$0D,$EE,$58,$88,$40,$4E,$75,$08,$C4,$00,$01
	dc.b $24,$13,$36,$2B,$00,$04,$10,$2B,$00,$07,$66,$42,$08,$2E,$00,$00
	dc.b $01,$0E,$67,$3A,$2F,$02,$94,$AE,$02,$3C,$20,$2E,$08,$6E,$90,$AE
	dc.b $02,$4C,$94,$80,$30,$42,$B1,$C2,$4C,$DF,$00,$04,$66,$20,$60,$06
	dc.b $30,$42,$B1,$C2,$66,$18,$4A,$2B,$00,$06,$66,$12,$61,$00,$3A,$58
	dc.b $66,$0C,$17,$7C,$00,$01,$00,$07,$70,$14,$61,$00,$34,$84,$10,$2B
	dc.b $00,$07,$B0,$3C,$00,$03,$67,$00,$03,$04,$53,$00,$67,$10,$6A,$06
	dc.b $4A,$2E,$01,$2E,$66,$08,$08,$C4,$00,$00,$60,$00,$C7,$0C,$08,$84
	dc.b $00,$00,$60,$00,$C7,$24,$76,$00,$42,$AE,$04,$6E,$61,$00,$C3,$C8
	dc.b $66,$00,$00,$A8,$D0,$00,$D0,$00,$D0,$00,$D0,$02,$B2,$3C,$00,$2E
	dc.b $67,$40,$B2,$3C,$00,$2A,$67,$34,$B0,$3C,$00,$08,$64,$1A,$17,$40
	dc.b $00,$0A,$17,$43,$00,$0B,$51,$EB,$00,$0C,$51,$EB,$00,$0D,$08,$C7
	dc.b $00,$02,$66,$00,$02,$CC,$4E,$75,$51,$00,$17,$40,$00,$08,$17,$43
	dc.b $00,$09,$08,$C7,$00,$01,$66,$00,$02,$B8,$4E,$75,$51,$EB,$00,$0C
	dc.b $60,$3C,$12,$1C,$48,$81,$12,$36,$10,$7E,$51,$EB,$00,$0C,$B2,$3C
	dc.b $00,$57,$67,$0C,$52,$2B,$00,$0C,$B2,$3C,$00,$4C,$66,$00,$02,$92
	dc.b $12,$1C,$B2,$3C,$00,$2A,$67,$16,$17,$40,$00,$0A,$51,$EB,$00,$0D
	dc.b $17,$43,$00,$0B,$08,$C7,$00,$02,$66,$00,$02,$76,$4E,$75,$17,$43
	dc.b $00,$0B,$17,$40,$00,$0A,$12,$1C,$61,$00,$02,$EE,$17,$40,$00,$0D
	dc.b $08,$C7,$00,$02,$66,$00,$02,$5A,$4E,$75,$20,$2E,$04,$6E,$67,$00
	dc.b $00,$9E,$41,$EC,$FF,$FF,$10,$2E,$04,$73,$55,$00,$67,$00,$00,$60
	dc.b $53,$00,$66,$00,$00,$8A,$10,$18,$48,$80,$10,$36,$00,$7E,$B0,$3C
	dc.b $00,$5A,$66,$00,$00,$7A,$10,$18,$48,$80,$10,$36,$00,$7E,$04,$00
	dc.b $00,$44,$56,$C2,$67,$4A,$56,$00,$67,$46,$B0,$3C,$00,$0F,$66,$00
	dc.b $00,$5E,$50,$C3,$10,$18,$48,$80,$10,$36,$00,$7E,$B0,$3C,$00,$43
	dc.b $66,$4C,$28,$48,$12,$1C,$50,$EB,$00,$08,$17,$43,$00,$09,$00,$87
	dc.b $00,$08,$00,$08,$08,$C7,$00,$01,$66,$00,$01,$E6,$4E,$75,$10,$18
	dc.b $48,$80,$10,$36,$00,$7E,$76,$00,$B0,$3C,$00,$50,$67,$C6,$60,$1E
	dc.b $10,$18,$04,$00,$00,$30,$65,$16,$B0,$3C,$00,$08,$64,$10,$50,$C3
	dc.b $28,$48,$12,$1C,$02,$02,$00,$01,$C1,$42,$60,$00,$FE,$B8,$2F,$0B
	dc.b $61,$00,$B8,$AC,$26,$5F,$26,$82,$37,$43,$00,$04,$17,$44,$00,$06
	dc.b $70,$00,$B2,$3C,$00,$2E,$66,$24,$12,$1C,$48,$81,$12,$36,$10,$7E
	dc.b $70,$01,$B2,$3C,$00,$57,$67,$12,$70,$02,$B2,$3C,$00,$4C,$67,$0A
	dc.b $70,$03,$B2,$3C,$00,$42,$66,$00,$01,$78,$12,$1C,$17,$40,$00,$07
	dc.b $08,$C7,$00,$00,$66,$00,$01,$6A,$4E,$75,$38,$3C,$01,$D0,$20,$3B
	dc.b $00,$16,$88,$40,$48,$40,$2F,$0D,$3A,$C4,$4E,$BB,$00,$12,$20,$5F
	dc.b $08,$04,$00,$06,$67,$04,$08,$84,$00,$02,$30,$84,$4E,$75,$00,$18
	dc.b $00,$00,$00,$34,$00,$00,$00,$BA,$00,$00,$00,$BA,$00,$00,$00,$78
	dc.b $00,$00,$00,$BA,$00,$00,$4A,$2B,$00,$09,$66,$00,$00,$9C,$4A,$2B
	dc.b $00,$08,$6A,$00,$00,$94,$7A,$3A,$55,$8D,$50,$8F,$3A,$FC,$FF,$FE
	dc.b $4E,$75,$4A,$2B,$00,$09,$66,$00,$00,$80,$0C,$2B,$00,$02,$00,$07
	dc.b $67,$00,$00,$76,$55,$8D,$50,$8F,$24,$13,$36,$2B,$00,$04,$18,$2B
	dc.b $00,$06,$08,$85,$00,$00,$08,$07,$00,$03,$66,$00,$00,$F0,$7A,$28
	dc.b $8A,$2B,$00,$08,$4A,$43,$6B,$00,$43,$3C,$3A,$C2,$4A,$2E,$02,$38
	dc.b $66,$00,$22,$CC,$4E,$75,$4A,$2B,$00,$09,$66,$3C,$4A,$2B,$00,$0B
	dc.b $66,$36,$08,$07,$00,$03,$66,$30,$42,$2B,$00,$03,$61,$08,$58,$4F
	dc.b $20,$5F,$30,$84,$4E,$75,$8A,$2B,$00,$08,$78,$0F,$C8,$2B,$00,$0A
	dc.b $E8,$5C,$4A,$2B,$00,$0C,$67,$04,$08,$C4,$00,$0B,$70,$03,$C0,$2B
	dc.b $00,$0D,$EE,$58,$88,$40,$4E,$75,$0C,$2B,$00,$03,$00,$07,$66,$60
	dc.b $24,$13,$36,$2B,$00,$04,$08,$07,$00,$02,$67,$00,$00,$50,$08,$07
	dc.b $00,$01,$67,$00,$00,$48,$08,$07,$00,$03,$66,$00,$00,$0C,$61,$B6
	dc.b $61,$00,$22,$50,$18,$02,$60,$A6,$61,$B0,$4A,$2E,$02,$38,$67,$2A
	dc.b $B6,$3C,$00,$02,$67,$18,$24,$13,$94,$AE,$02,$3C,$20,$2E,$08,$6E
	dc.b $90,$AE,$02,$4C,$94,$80,$61,$00,$22,$30,$18,$02,$60,$80,$4A,$2E
	dc.b $01,$07,$66,$E2,$70,$21,$61,$00,$2D,$F6,$4E,$75,$60,$00,$00,$22
	dc.b $08,$07,$00,$00,$67,$04,$61,$00,$FB,$D4,$08,$07,$00,$02,$67,$04
	dc.b $61,$00,$FC,$60,$08,$07,$00,$01,$67,$04,$61,$00,$FB,$AA,$4E,$75
	dc.b $70,$5B,$60,$00,$2D,$C6,$70,$44,$60,$00,$2D,$C0,$4A,$2E,$02,$38
	dc.b $67,$38,$4A,$43,$6B,$00,$42,$20,$B6,$3C,$00,$02,$67,$20,$3F,$04
	dc.b $08,$84,$00,$0F,$61,$00,$C3,$0C,$38,$1F,$94,$AE,$02,$3C,$20,$2E
	dc.b $08,$6E,$90,$AE,$02,$4C,$94,$80,$3A,$C2,$60,$00,$21,$C8,$4A,$2E
	dc.b $01,$07,$66,$DA,$70,$21,$61,$00,$2D,$86,$3A,$C2,$4E,$75,$3F,$04
	dc.b $4A,$2E,$02,$38,$67,$2C,$4A,$43,$6B,$00,$FF,$AC,$18,$2B,$00,$06
	dc.b $66,$20,$B6,$3C,$00,$02,$66,$0C,$4A,$2E,$01,$07,$66,$06,$70,$1E
	dc.b $61,$00,$2D,$5C,$94,$AE,$02,$3C,$20,$2E,$08,$6E,$90,$AE,$02,$4C
	dc.b $94,$80,$2A,$C2,$38,$1F,$4E,$75,$48,$E7,$38,$30,$61,$00,$B6,$8A
	dc.b $4A,$43,$6B,$28,$4A,$2E,$02,$38,$67,$28,$B6,$3C,$00,$02,$66,$1C
	dc.b $4A,$04,$66,$18,$4A,$82,$6B,$14,$B4,$BC,$00,$00,$00,$09,$64,$0C
	dc.b $10,$3B,$20,$17,$6B,$06,$4C,$DF,$0C,$1C,$4E,$75,$70,$5C,$61,$00
	dc.b $2D,$0E,$4C,$DF,$0C,$1C,$70,$00,$4E,$75,$00,$01,$FF,$02,$FF,$FF
	dc.b $FF,$03,$48,$81,$12,$36,$10,$7E,$60,$04,$41,$F1,$20,$00,$22,$48
	dc.b $34,$18,$67,$38,$B2,$18,$65,$34,$66,$F0,$48,$E7,$40,$08,$12,$1C
	dc.b $48,$81,$12,$36,$10,$7E,$B2,$18,$67,$F4,$4A,$20,$67,$06,$4C,$DF
	dc.b $10,$02,$60,$D6,$41,$FA,$4F,$A6,$4A,$30,$10,$00,$67,$F0,$50,$8F
	dc.b $34,$31,$20,$FE,$12,$2C,$FF,$FF,$70,$00,$4E,$75,$12,$2C,$FF,$FF
	dc.b $70,$FF,$4E,$75,$41,$FA,$00,$8A,$61,$46,$67,$24,$41,$FA,$00,$86
	dc.b $61,$3E,$67,$16,$41,$FA,$00,$89,$61,$36,$66,$2E,$1D,$40,$01,$33
	dc.b $B2,$3C,$00,$2C,$66,$22,$12,$1C,$60,$DA,$1D,$40,$01,$32,$60,$F0
	dc.b $61,$00,$BE,$C2,$4A,$82,$6B,$12,$B4,$BC,$00,$00,$00,$08,$64,$0A
	dc.b $EE,$5A,$3D,$42,$01,$30,$60,$D8,$4E,$75,$70,$3A,$60,$00,$2C,$5C
	dc.b $43,$EC,$FF,$FF,$12,$19,$48,$81,$12,$36,$10,$7E,$10,$18,$67,$06
	dc.b $B2,$00,$67,$F0,$4E,$75,$B2,$3C,$00,$3D,$66,$F8,$28,$49,$12,$1C
	dc.b $4A,$10,$6A,$04,$70,$00,$4E,$75,$70,$00,$48,$81,$12,$36,$10,$7E
	dc.b $14,$18,$67,$C6,$52,$00,$B4,$01,$66,$F6,$12,$1C,$B0,$00,$4E,$75
	dc.b $49,$44,$00,$FF
	dc.b "ROUND",$00
	dc.b "NPMZ",$00
	dc.b "PREC",$00
	dc.b $58,$44,$53,$00,$61,$00,$D2,$80,$16,$2E,$02,$39,$66,$06,$1D,$7C
	dc.b $00,$07,$02,$39,$B6,$3C,$00,$04,$65,$00,$D2,$7E,$4A,$2E,$02,$38
	dc.b $66,$52,$2F,$08,$61,$00,$06,$FA,$20,$5F,$66,$00,$2B,$DA,$48,$E7
	dc.b $30,$00,$61,$00,$B3,$1E,$4C,$DF,$00,$0C,$67,$00,$2B,$7E,$45,$EE
	dc.b $01,$6A,$2F,$02,$16,$2E,$02,$39,$06,$03,$00,$0B,$61,$00,$B3,$EC
	dc.b $24,$5F,$23,$52,$00,$08,$13,$6A,$00,$04,$00,$0E,$13,$6A,$00,$05
	dc.b $00,$0F,$23,$6A,$00,$06,$00,$10,$33,$6A,$00,$0A,$00,$14,$12,$2C
	dc.b $FF,$FF,$4E,$75,$61,$00,$B2,$DC,$66,$00,$2B,$58,$08,$29,$00,$06
	dc.b $00,$0C,$66,$00,$2B,$36,$16,$2E,$02,$39,$2F,$09,$61,$00,$06,$92
	dc.b $22,$5F,$66,$00,$2B,$72,$20,$42,$20,$29,$00,$08,$B0,$90,$66,$3C
	dc.b $10,$29,$00,$0E,$B0,$28,$00,$04,$66,$32,$10,$29,$00,$0F,$B0,$28
	dc.b $00,$05,$66,$28,$20,$29,$00,$10,$B0,$A8,$00,$06,$66,$1E,$30,$29
	dc.b $00,$14,$B0,$68,$00,$0A,$66,$14,$B6,$29,$00,$0D,$66,$00,$2A,$EC
	dc.b $08,$E9,$00,$06,$00,$0C,$12,$2C,$FF,$FF,$4E,$75,$60,$00,$2A,$E4
	dc.b $8C,$6E,$01,$30,$60,$00,$08,$64,$3A,$06,$3C,$3C,$F0,$48,$8C,$6E
	dc.b $01,$30,$48,$45,$3A,$06,$48,$45,$60,$00,$08,$98,$3C,$3C,$F0,$00
	dc.b $8C,$6E,$01,$30,$3A,$C6,$61,$00,$05,$9C,$66,$20,$B2,$3C,$00,$2C
	dc.b $66,$00,$2A,$D4,$12,$1C,$36,$02,$61,$00,$05,$8A,$66,$00,$00,$8E
	dc.b $E7,$4B,$84,$43,$EF,$4A,$3A,$C2,$60,$00,$03,$C2,$41,$FA,$01,$18
	dc.b $61,$00,$FD,$DC,$67,$30,$3A,$3C,$40,$00,$61,$00,$05,$C4,$3A,$C5
	dc.b $61,$00,$01,$46,$70,$FD,$61,$00,$BD,$40,$B2,$3C,$00,$2C,$66,$00
	dc.b $2A,$96,$12,$1C,$61,$00,$05,$4E,$66,$2C,$EF,$4A,$20,$6E,$02,$4C
	dc.b $85,$68,$00,$02,$4E,$75,$61,$00,$C9,$6C,$B2,$3C,$00,$2C,$66,$00
	dc.b $2A,$76,$12,$1C,$EC,$5A,$00,$42,$A0,$00,$3A,$C2,$61,$00,$00,$A6
	dc.b $70,$3D,$60,$00,$BD,$04,$41,$FA,$00,$BE,$61,$00,$FD,$82,$66,$16
	dc.b $61,$00,$00,$96,$20,$6E,$02,$4C,$EC,$5A,$08,$C2,$00,$0F,$31,$42
	dc.b $00,$02,$60,$00,$C9,$30,$70,$57,$60,$00,$2A,$60,$3A,$3C,$60,$00
	dc.b $61,$00,$05,$4E,$EF,$4B,$8A,$43,$3A,$C5,$61,$00,$00,$CC,$70,$3D
	dc.b $61,$00,$BC,$C6,$0C,$2E,$00,$05,$02,$39,$67,$02,$4E,$75,$B2,$3C
	dc.b $00,$7B,$66,$F8,$12,$1C,$B2,$3C,$00,$23,$67,$26,$61,$00,$BD,$24
	dc.b $66,$3C,$4A,$00,$66,$38,$02,$42,$00,$07,$E9,$0A,$08,$C2,$00,$0C
	dc.b $20,$6E,$02,$4C,$85,$68,$00,$02,$B2,$3C,$00,$7D,$66,$20,$12,$1C
	dc.b $4E,$75,$12,$1C,$61,$00,$BC,$4A,$B4,$BC,$FF,$FF,$FF,$C0,$6D,$0E
	dc.b $B4,$BC,$00,$00,$00,$3F,$6E,$06,$02,$42,$00,$7F,$60,$D2,$70,$61
	dc.b $60,$00,$29,$E8,$61,$00,$00,$62,$70,$38,$C0,$45,$51,$40,$67,$02
	dc.b $4E,$75,$20,$6E,$02,$4C,$08,$28,$00,$02,$00,$02,$67,$02,$4E,$75
	dc.b $70,$5F,$60,$00,$29,$C6,$00,$0C,$43,$4F,$4E,$54,$52,$4F,$4C,$00
	dc.b $00,$04,$00,$0A,$46,$50,$43,$52,$00,$00,$00,$04,$00,$0A,$46,$50
	dc.b $49,$41,$52,$00,$00,$01,$00,$0A,$46,$50,$53,$52,$00,$00,$00,$02
	dc.b $00,$0A,$49,$41,$44,$44,$52,$00,$00,$01,$00,$0C,$53,$54,$41,$54
	dc.b $55,$53,$00,$00,$00,$02,$00,$00,$B2,$3C,$00,$23,$66,$30,$16,$2E
	dc.b $02,$39,$B6,$3C,$00,$04,$65,$26,$12,$1C,$16,$2E,$02,$39,$61,$00
	dc.b $04,$80,$66,$00,$29,$62,$06,$03,$00,$F5,$10,$03,$16,$2E,$02,$39
	dc.b $20,$42,$61,$00,$56,$38,$66,$20,$7A,$3C,$60,$00,$06,$50,$61,$00
	dc.b $BD,$42,$BA,$7C,$00,$10,$64,$10,$70,$4E,$14,$2E,$02,$39,$05,$00
	dc.b $66,$06,$70,$5E,$61,$00,$29,$34,$4E,$75,$3C,$3C,$F0,$00,$8C,$6E
	dc.b $01,$30,$3A,$C6,$10,$2E,$02,$39,$B0,$3C,$00,$03,$67,$00,$01,$1A
	dc.b $61,$00,$01,$FA,$3A,$3C,$E0,$00,$61,$00,$00,$CE,$66,$2A,$3A,$C5
	dc.b $B2,$3C,$00,$2C,$66,$00,$28,$E0,$12,$1C,$61,$00,$FF,$7C,$70,$34
	dc.b $61,$00,$BB,$76,$61,$00,$00,$90,$67,$0C,$3A,$28,$00,$02,$61,$00
	dc.b $00,$94,$31,$45,$00,$02,$4E,$75,$61,$00,$03,$C2,$66,$2A,$08,$C5
	dc.b $00,$0B,$E9,$0A,$8A,$02,$3A,$C5,$B2,$3C,$00,$2C,$66,$00,$28,$A8
	dc.b $12,$1C,$61,$00,$FF,$44,$70,$34,$61,$00,$BB,$3E,$61,$58,$67,$06
	dc.b $08,$E8,$00,$04,$00,$02,$4E,$75,$3A,$FC,$D0,$00,$61,$00,$FF,$2A
	dc.b $70,$7D,$61,$00,$BB,$24,$B2,$3C,$00,$2C,$66,$00,$28,$7A,$12,$1C
	dc.b $61,$00,$03,$7A,$66,$14,$20,$6E,$02,$4C,$02,$42,$00,$0F,$E9,$4A
	dc.b $08,$C2,$00,$0B,$85,$68,$00,$02,$4E,$75,$3A,$3C,$D0,$00,$61,$00
	dc.b $00,$38,$66,$0C,$61,$1E,$20,$6E,$02,$4C,$31,$45,$00,$02,$4E,$75
	dc.b $70,$39,$60,$00,$28,$66,$70,$38,$C0,$45,$20,$6E,$02,$4C,$B0,$7C
	dc.b $00,$20,$4E,$75,$10,$05,$E0,$4D,$74,$07,$E2,$10,$E3,$55,$51,$CA
	dc.b $FF,$FA,$08,$C5,$00,$0C,$4E,$75,$61,$00,$02,$DA,$67,$02,$4E,$75
	dc.b $36,$02,$05,$C5,$B2,$3C,$00,$2F,$66,$08,$12,$1C,$61,$00,$02,$BA
	dc.b $60,$EE,$B2,$3C,$00,$2D,$66,$1C,$12,$1C,$61,$00,$02,$AC,$B4,$43
	dc.b $6D,$0C,$07,$C5,$52,$43,$B6,$42,$6F,$F8,$36,$02,$60,$D6,$70,$39
	dc.b $60,$00,$28,$04,$70,$00,$4E,$75,$3A,$3C,$A0,$00,$41,$FA,$FE,$38
	dc.b $61,$00,$FA,$FC,$66,$32,$EC,$5A,$8A,$42,$B2,$3C,$00,$2F,$66,$12
	dc.b $12,$1C,$41,$FA,$FE,$22,$61,$00,$FA,$E6,$67,$EA,$70,$39,$60,$00
	dc.b $27,$DA,$B2,$3C,$00,$2C,$66,$00,$27,$AE,$12,$1C,$3A,$C5,$61,$00
	dc.b $FE,$48,$70,$FF,$60,$00,$BA,$42,$3A,$C5,$61,$00,$FE,$3C,$70,$FF
	dc.b $61,$00,$BA,$36,$B2,$3C,$00,$2C,$66,$00,$27,$8C,$12,$1C,$3A,$3C
	dc.b $80,$00,$41,$FA,$FD,$E2,$61,$00,$FA,$A6,$66,$C0,$EC,$5A,$8A,$42
	dc.b $B2,$3C,$00,$2F,$66,$0E,$12,$1C,$41,$FA,$FD,$CC,$61,$00,$FA,$90
	dc.b $67,$EA,$60,$A8,$20,$6E,$02,$4C,$31,$45,$00,$02,$4E,$75,$8C,$6E
	dc.b $01,$30,$10,$2E,$02,$39,$67,$04,$61,$00,$00,$52,$3A,$C6,$B2,$3C
	dc.b $00,$23,$66,$00,$27,$4A,$12,$1C,$61,$00,$B9,$A6,$4A,$82,$6B,$08
	dc.b $B4,$BC,$00,$00,$00,$40,$65,$06,$70,$1D,$61,$00,$27,$4E,$02,$42
	dc.b $00,$3F,$00,$42,$5C,$00,$B2,$3C,$00,$2C,$66,$00,$27,$1A,$12,$1C
	dc.b $36,$02,$61,$00,$01,$C4,$EF,$4A,$86,$42,$3A,$C3,$4E,$75,$8C,$6E
	dc.b $01,$30,$48,$46,$42,$46,$2A,$C6,$72,$0A,$4E,$75,$0C,$2E,$00,$07
	dc.b $02,$39,$67,$0E,$4A,$2E,$02,$39,$66,$00,$26,$D4,$1D,$7C,$00,$07
	dc.b $02,$39,$4E,$75,$0C,$2E,$00,$3C,$01,$21,$67,$00,$00,$0C,$0C,$2E
	dc.b $00,$28,$01,$21,$66,$00,$D3,$A0,$3A,$06,$3C,$3C,$F0,$00,$8C,$6E
	dc.b $01,$30,$48,$45,$3A,$06,$48,$45,$61,$00,$01,$7A,$66,$1E,$EC,$5A
	dc.b $8A,$42,$ED,$5A,$61,$B6,$B2,$3C,$00,$2C,$66,$06,$12,$1C,$61,$00
	dc.b $01,$58,$3A,$C6,$EF,$5A,$8A,$42,$3A,$C5,$4E,$75,$08,$C5,$00,$0E
	dc.b $61,$00,$01,$AE,$2A,$C5,$61,$00,$FD,$30,$70,$FD,$61,$00,$B9,$2A
	dc.b $B2,$3C,$00,$2C,$66,$00,$26,$80,$12,$1C,$61,$00,$01,$2C,$EF,$4A
	dc.b $20,$6E,$02,$4C,$85,$68,$00,$02,$4E,$75,$8C,$6E,$01,$30,$4A,$2E
	dc.b $01,$25,$67,$06,$70,$65,$61,$00,$26,$82,$4A,$2E,$02,$39,$66,$00
	dc.b $26,$3E,$61,$00,$B8,$D6,$00,$6C,$4E,$75,$8C,$6E,$01,$30,$4A,$2E
	dc.b $01,$25,$67,$06,$70,$65,$61,$00,$26,$62,$4A,$2E,$02,$39,$66,$00
	dc.b $26,$1E,$61,$00,$B8,$B6,$00,$34,$4E,$75,$3A,$06,$3C,$3C,$F0,$40
	dc.b $8C,$6E,$01,$30,$48,$45,$3A,$06,$48,$45,$60,$00,$08,$54,$8C,$6E
	dc.b $01,$30,$3A,$C6,$7A,$30,$61,$00,$00,$CC,$66,$2E,$EC,$5A,$8A,$42
	dc.b $61,$00,$FF,$0A,$B2,$3C,$00,$2C,$66,$00,$25,$FC,$12,$1C,$61,$00
	dc.b $00,$A8,$8A,$42,$B2,$3C,$00,$3A,$66,$00,$C5,$E6,$12,$1C,$61,$00
	dc.b $00,$98,$EF,$4A,$8A,$42,$3A,$C5,$4E,$75,$08,$C5,$00,$0E,$61,$00
	dc.b $00,$F0,$3A,$C5,$61,$00,$FC,$72,$70,$FD,$61,$00,$B8,$6C,$B2,$3C
	dc.b $00,$2C,$66,$00,$25,$C2,$12,$1C,$61,$00,$00,$6E,$3A,$02,$B2,$3C
	dc.b $00,$3A,$66,$00,$C5,$AC,$12,$1C,$61,$00,$00,$5E,$EF,$4A,$8A,$42
	dc.b $20,$6E,$02,$4C,$8B,$68,$00,$02,$4E,$75,$3A,$06,$3C,$3C,$F0,$78
	dc.b $8C,$6E,$01,$30,$48,$45,$3A,$06,$48,$45,$2A,$C5,$60,$00,$EE,$5A
	dc.b $3A,$06,$3C,$3C,$F0,$00,$8C,$6E,$01,$30,$48,$45,$3A,$06,$48,$45
	dc.b $61,$00,$00,$32,$66,$0E,$EC,$5A,$8A,$42,$61,$00,$FE,$70,$3A,$C6
	dc.b $3A,$C5,$4E,$75,$08,$C5,$00,$0E,$61,$00,$00,$76,$2A,$C5,$61,$00
	dc.b $FB,$F8,$70,$FD,$60,$00,$B7,$F2,$61,$0A,$66,$02,$4E,$75,$70,$57
	dc.b $60,$00,$25,$64,$10,$01,$20,$4C,$48,$80,$10,$36,$00,$7E,$B0,$3C
	dc.b $00,$46,$66,$34,$10,$18,$48,$80,$10,$36,$00,$7E,$B0,$3C,$00,$50
	dc.b $66,$26,$14,$18,$04,$02,$00,$30,$65,$1E,$B4,$3C,$00,$08,$64,$18
	dc.b $48,$82,$70,$00,$10,$18,$43,$FA,$48,$10,$4A,$31,$00,$00,$67,$08
	dc.b $12,$00,$28,$48,$B0,$00,$4E,$75,$70,$FF,$4E,$75,$61,$00,$B8,$14
	dc.b $66,$0C,$4A,$00,$67,$08,$28,$48,$12,$2C,$FF,$FF,$70,$FF,$4E,$75
	dc.b $70,$00,$10,$2E,$02,$39,$67,$00,$24,$C6,$D0,$40,$8A,$7B,$00,$02
	dc.b $4E,$75,$18,$00,$10,$00,$00,$00,$14,$00,$0C,$00,$04,$00,$08,$00
	dc.b $41,$EE,$08,$7E,$78,$00,$42,$A0,$42,$A0,$42,$A0,$48,$83,$B2,$3C
	dc.b $00,$24,$67,$00,$01,$4C,$B2,$3C,$00,$3A,$67,$00,$01,$44,$B2,$3C
	dc.b $00,$2D,$67,$00,$00,$22,$B2,$3C,$00,$30,$65,$06,$B2,$3C,$00,$3A
	dc.b $65,$30,$61,$00,$B2,$38,$B6,$3C,$00,$0F,$65,$22,$B6,$3C,$00,$13
	dc.b $64,$1C,$70,$00,$4E,$75,$12,$1C,$61,$B6,$66,$10,$20,$42,$06,$03
	dc.b $00,$F5,$61,$00,$52,$0A,$04,$03,$00,$F5,$4A,$00,$4E,$75,$70,$64
	dc.b $4E,$75,$3F,$03,$56,$88,$50,$C2,$76,$01,$78,$FF,$7A,$00,$7C,$00
	dc.b $04,$01,$00,$30,$66,$0E,$4A,$05,$66,$0A,$B6,$3C,$00,$01,$67,$14
	dc.b $53,$44,$60,$10,$61,$00,$00,$C0,$50,$C5,$B6,$3C,$00,$FF,$66,$02
	dc.b $76,$00,$D8,$43,$12,$1C,$B2,$3C,$00,$2E,$66,$0A,$B6,$3C,$00,$01
	dc.b $66,$4E,$16,$05,$60,$EE,$B2,$3C,$00,$30,$65,$06,$B2,$3C,$00,$3A
	dc.b $65,$BE,$B2,$3C,$00,$45,$67,$06,$B2,$3C,$00,$65,$66,$32,$76,$00
	dc.b $12,$1C,$B2,$3C,$00,$2D,$57,$C2,$66,$02,$12,$1C,$B2,$3C,$00,$30
	dc.b $65,$16,$B2,$3C,$00,$3A,$64,$10,$04,$01,$00,$30,$02,$41,$00,$FF
	dc.b $C6,$FC,$00,$0A,$D6,$41,$60,$E2,$4A,$02,$67,$02,$44,$43,$D8,$43
	dc.b $41,$EE,$08,$72,$7C,$00,$4A,$05,$67,$36,$4A,$44,$6A,$06,$08,$D0
	dc.b $00,$06,$44,$44,$50,$C2,$02,$84,$00,$00,$FF,$FF,$88,$FC,$03,$E8
	dc.b $3A,$04,$42,$44,$48,$44,$88,$FC,$00,$64,$61,$28,$42,$44,$48,$44
	dc.b $88,$FC,$00,$0A,$61,$1E,$42,$44,$48,$44,$61,$18,$12,$2C,$FF,$FF
	dc.b $41,$EE,$08,$72,$36,$1F,$61,$00,$50,$58,$06,$43,$00,$0B,$24,$08
	dc.b $4A,$40,$4E,$75,$12,$04,$4A,$02,$67,$08,$83,$18,$52,$06,$46,$02
	dc.b $4E,$75,$BC,$3C,$00,$09,$67,$06,$E9,$49,$83,$10,$46,$02,$4E,$75
	dc.b $24,$4C,$43,$FA,$B3,$42,$12,$1C,$48,$81,$6B,$0C,$14,$31,$10,$00
	dc.b $6B,$06,$70,$04,$61,$28,$60,$EE,$70,$00,$10,$3B,$30,$19,$67,$14
	dc.b $74,$00,$3F,$00,$B0,$7C,$00,$20,$6D,$02,$70,$10,$91,$57,$61,$0E
	dc.b $30,$1F,$66,$EE,$60,$A4,$58,$50,$40,$20,$00,$40,$00,$00,$2F,$09
	dc.b $4A,$40,$67,$1A,$48,$40,$42,$40,$D1,$00,$48,$40,$41,$EE,$08,$7E
	dc.b $22,$48,$D3,$88,$D3,$88,$D3,$88,$65,$28,$53,$40,$66,$EE,$D1,$00
	dc.b $48,$82,$48,$C2,$41,$EE,$08,$7E,$20,$20,$D1,$82,$20,$80,$74,$00
	dc.b $20,$20,$D1,$82,$20,$80,$20,$20,$D1,$82,$65,$06,$20,$80,$22,$5F
	dc.b $4E,$75,$70,$5D,$61,$00,$23,$04,$22,$5F,$4E,$75,$20,$42,$48,$83
	dc.b $10,$3B,$30,$13,$6B,$08,$3A,$D8,$53,$00,$66,$FA,$4E,$75,$70,$00
	dc.b $10,$18,$3A,$C0,$4E,$75,$FF,$01,$02,$04,$06,$02,$06,$00,$4A,$2E
	dc.b $01,$23,$66,$0A,$0C,$2E,$00,$14,$01,$21,$66,$00,$CF,$7A,$4A,$2E
	dc.b $01,$25,$67,$06,$70,$65,$61,$00,$22,$C2,$10,$2E,$02,$39,$67,$16
	dc.b $B0,$3C,$00,$02,$67,$10,$B0,$3C,$00,$03,$66,$00,$22,$72,$08,$C6
	dc.b $00,$06,$60,$00,$BE,$50,$60,$00,$BE,$CC,$4A,$2E,$01,$23,$66,$0A
	dc.b $0C,$2E,$00,$14,$01,$21,$66,$00,$CF,$3E,$4A,$2E,$01,$25,$67,$06
	dc.b $70,$65,$61,$00,$22,$86,$3A,$06,$3C,$3C,$F0,$48,$48,$45,$3A,$06
	dc.b $48,$45,$4A,$2E,$02,$39,$66,$00,$22,$36,$61,$00,$B5,$48,$48,$45
	dc.b $8A,$02,$48,$45,$2A,$C5,$B2,$3C,$00,$2C,$66,$00,$22,$3A,$12,$1C
	dc.b $61,$00,$BF,$02,$66,$04,$54,$8D,$4E,$75,$55,$82,$4A,$43,$6B,$00
	dc.b $36,$B2,$61,$00,$16,$7C,$3A,$C2,$4E,$75,$0C,$2E,$00,$3C,$01,$21
	dc.b $67,$0A,$0C,$2E,$00,$28,$01,$21,$66,$00,$00,$14,$4A,$2E,$01,$25
	dc.b $67,$06,$70,$65,$61,$00,$22,$24,$3A,$FC,$F5,$18,$4E,$75,$4A,$2E
	dc.b $01,$23,$66,$0A,$0C,$2E,$00,$1E,$01,$21,$66,$00,$CE,$BA,$4A,$2E
	dc.b $01,$25,$67,$06,$70,$65,$61,$00,$22,$02,$3A,$C6,$3A,$FC,$24,$00
	dc.b $4E,$75,$0C,$2E,$00,$3C,$01,$21,$67,$0A,$0C,$2E,$00,$28,$01,$21
	dc.b $66,$00,$CE,$94,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$21,$DC
	dc.b $3A,$C6,$61,$00,$B5,$CE,$10,$05,$02,$00,$00,$38,$B0,$3C,$00,$10
	dc.b $66,$0E,$02,$05,$00,$07,$20,$6E,$02,$4C,$8A,$50,$30,$85,$4E,$75
	dc.b $70,$68,$60,$00,$21,$B6,$0C,$2E,$00,$3C,$01,$21,$67,$0A,$0C,$2E
	dc.b $00,$28,$01,$21,$66,$00,$CE,$50,$4A,$2E,$01,$25,$67,$06,$70,$65
	dc.b $61,$00,$21,$98,$3A,$C6,$4E,$75,$0C,$2E,$00,$3C,$01,$21,$67,$0A
	dc.b $0C,$2E,$00,$28,$01,$21,$66,$00,$00,$14,$4A,$2E,$01,$25,$67,$06
	dc.b $70,$65,$61,$00,$21,$76,$3C,$3C,$F5,$08,$60,$94,$4A,$2E,$01,$23
	dc.b $66,$0A,$0C,$2E,$00,$1E,$01,$21,$66,$00,$CE,$0C,$4A,$2E,$01,$25
	dc.b $67,$06,$70,$65,$61,$00,$21,$54,$34,$3C,$30,$00,$3A,$C6,$61,$00
	dc.b $00,$5C,$B2,$3C,$00,$2C,$66,$00,$21,$1E,$12,$1C,$B2,$3C,$00,$23
	dc.b $66,$00,$21,$1C,$12,$1C,$3F,$02,$61,$00,$B3,$76,$36,$1F,$4A,$2E
	dc.b $01,$23,$56,$C0,$02,$80,$00,$00,$00,$08,$00,$00,$00,$07,$4A,$82
	dc.b $6B,$04,$B4,$80,$6F,$08,$70,$59,$61,$00,$21,$10,$74,$00,$EB,$4A
	dc.b $84,$43,$B2,$3C,$00,$2C,$67,$04,$3A,$C2,$4E,$75,$12,$1C,$08,$C2
	dc.b $00,$0B,$3A,$C2,$61,$00,$B3,$4E,$00,$24,$4E,$75,$B2,$3C,$00,$23
	dc.b $67,$6E,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$53,$67,$40,$B2,$3C
	dc.b $00,$44,$66,$56,$12,$1C,$04,$01,$00,$30,$65,$4E,$B2,$3C,$00,$08
	dc.b $65,$22,$B2,$3C,$00,$16,$67,$06,$B2,$3C,$00,$36,$66,$3C,$12,$1C
	dc.b $B2,$3C,$00,$43,$67,$06,$B2,$3C,$00,$63,$66,$2E,$00,$42,$00,$01
	dc.b $12,$1C,$4E,$75,$08,$C1,$00,$03,$84,$01,$12,$1C,$4E,$75,$12,$1C
	dc.b $B2,$3C,$00,$46,$67,$06,$B2,$3C,$00,$66,$66,$0E,$12,$1C,$B2,$3C
	dc.b $00,$43,$67,$DC,$B2,$3C,$00,$63,$67,$D6,$70,$59,$60,$00,$20,$78
	dc.b $12,$1C,$3F,$02,$61,$00,$B2,$BA,$4A,$2E,$01,$23,$56,$C0,$02,$80
	dc.b $00,$00,$00,$08,$00,$00,$00,$07,$4A,$82,$6B,$04,$B4,$80,$6F,$08
	dc.b $70,$59,$61,$00,$20,$56,$74,$00,$84,$5F,$08,$C2,$00,$04,$4E,$75
	dc.b $4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$14,$01,$21,$66,$00,$CC,$E8
	dc.b $4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$20,$30,$34,$3C,$34,$00
	dc.b $60,$00,$FE,$DA,$4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$14,$01,$21
	dc.b $66,$00,$CC,$C4,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$20,$0C
	dc.b $3A,$C6,$3A,$FC,$A0,$00,$61,$00,$B2,$5C,$00,$FC,$4E,$75,$4A,$2E
	dc.b $01,$23,$66,$0A,$0C,$2E,$00,$1E,$01,$21,$66,$00,$CC,$9A,$4A,$2E
	dc.b $01,$25,$67,$06,$70,$65,$61,$00,$1F,$E2,$3A,$FC,$F0,$00,$34,$06
	dc.b $61,$00,$FE,$EA,$3A,$C2,$B2,$3C,$00,$2C,$66,$00,$1F,$AA,$12,$1C
	dc.b $61,$00,$B2,$22,$00,$24,$4E,$75,$0C,$2E,$00,$1E,$01,$21,$66,$00
	dc.b $CC,$66,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1F,$AE,$3A,$FC
	dc.b $F0,$00,$34,$3C,$01,$00,$60,$48,$4A,$2E,$01,$23,$66,$0A,$0C,$2E
	dc.b $00,$1E,$01,$21,$66,$00,$CC,$40,$4A,$2E,$01,$25,$67,$06,$70,$65
	dc.b $61,$00,$1F,$88,$3A,$FC,$F0,$00,$61,$58,$66,$22,$08,$C2,$00,$09
	dc.b $3A,$C2,$B2,$3C,$00,$2C,$66,$00,$1F,$4E,$12,$1C,$61,$00,$F5,$EA
	dc.b $70,$3F,$4A,$2E,$01,$23,$66,$02,$70,$24,$60,$00,$B1,$DC,$74,$00
	dc.b $4A,$2E,$02,$39,$67,$00,$1F,$18,$3A,$C2,$61,$00,$F5,$CC,$70,$24
	dc.b $61,$00,$B1,$C6,$B2,$3C,$00,$2C,$66,$00,$1F,$1C,$12,$1C,$61,$12
	dc.b $66,$0A,$20,$6E,$02,$4C,$85,$68,$00,$02,$4E,$75,$70,$58,$60,$00
	dc.b $1F,$2A,$41,$FA,$00,$4E,$61,$00,$F2,$26,$66,$44,$10,$02,$6A,$1E
	dc.b $4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$14,$01,$21,$66,$00,$CB,$B8
	dc.b $4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1F,$00,$60,$10,$08,$00
	dc.b $00,$06,$67,$0A,$0C,$2E,$00,$1E,$01,$21,$66,$00,$CB,$9A,$42,$02
	dc.b $D4,$42,$D4,$42,$02,$00,$00,$3F,$B0,$2E,$02,$39,$66,$00,$1E,$A0
	dc.b $4E,$75,$00,$08,$41,$43,$00,$00,$17,$82,$00,$08,$42,$41,$43,$00
	dc.b $1D,$82,$00,$08,$42,$41,$44,$00,$1C,$82,$00,$08,$43,$41,$4C,$00
	dc.b $14,$81,$00,$08,$43,$52,$50,$00,$13,$04,$00,$08,$44,$52,$50,$00
	dc.b $11,$84,$00,$0A,$4D,$4D,$55,$53,$52,$00,$18,$02,$00,$0A,$50,$43
	dc.b $53,$52,$00,$00,$19,$82,$00,$08,$50,$53,$52,$00,$18,$02,$00,$08
	dc.b $53,$43,$43,$00,$16,$81,$00,$08,$53,$52,$50,$00,$12,$04,$00,$08
	dc.b $54,$43,$00,$00,$10,$03,$00,$08,$54,$54,$30,$00,$02,$43,$00,$08
	dc.b $54,$54,$31,$00,$03,$43,$00,$08,$56,$41,$4C,$00,$2B,$81,$00,$00
	dc.b $4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$14,$01,$21,$66,$00,$CA,$F8
	dc.b $4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1E,$40,$61,$00,$B0,$9C
	dc.b $00,$6C,$4E,$75,$4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$14,$01,$21
	dc.b $66,$00,$CA,$D4,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1E,$1C
	dc.b $61,$00,$B0,$78,$00,$34,$4E,$75,$4A,$2E,$01,$23,$66,$0A,$0C,$2E
	dc.b $00,$14,$01,$21,$66,$00,$CA,$B0,$4A,$2E,$01,$25,$67,$06,$70,$65
	dc.b $61,$00,$1D,$F8,$3A,$06,$3C,$3C,$F0,$40,$48,$45,$3A,$06,$48,$45
	dc.b $2A,$C5,$61,$00,$BC,$D2,$50,$EE,$02,$3B,$61,$00,$B0,$38,$00,$3D
	dc.b $4E,$75,$08,$06,$00,$0F,$67,$00,$00,$2E,$0C,$2E,$00,$28,$01,$21
	dc.b $66,$00,$00,$42,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1D,$BC
	dc.b $08,$06,$00,$09,$66,$08,$3C,$3C,$F5,$48,$60,$00,$FB,$D4,$3C,$3C
	dc.b $F5,$68,$60,$00,$FB,$CC,$0C,$2E,$00,$3C,$01,$21,$66,$00,$CA,$48
	dc.b $4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1D,$90,$00,$46,$F5,$88
	dc.b $60,$00,$FB,$AE,$4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$1E,$01,$21
	dc.b $66,$00,$CA,$24,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00,$1D,$6C
	dc.b $4A,$2E,$02,$39,$66,$00,$1D,$28,$3A,$FC,$F0,$00,$34,$06,$61,$00
	dc.b $FC,$6C,$3A,$C2,$B2,$3C,$00,$2C,$66,$00,$1D,$2C,$12,$1C,$61,$00
	dc.b $AF,$A4,$00,$24,$B2,$3C,$00,$2C,$66,$00,$1D,$1C,$12,$1C,$B2,$3C
	dc.b $00,$23,$66,$00,$1D,$1A,$12,$1C,$61,$00,$AF,$76,$4A,$82,$6B,$08
	dc.b $B4,$BC,$00,$00,$00,$08,$65,$08,$70,$1D,$61,$00,$1D,$1E,$74,$00
	dc.b $EC,$5A,$B2,$3C,$00,$2C,$66,$14,$12,$1C,$36,$02,$61,$00,$AF,$F0
	dc.b $08,$C3,$00,$08,$02,$42,$00,$07,$EB,$4A,$84,$43,$20,$6E,$02,$4C
	dc.b $85,$68,$00,$02,$4E,$75,$4A,$2E,$01,$23,$66,$0A,$0C,$2E,$00,$14
	dc.b $01,$21,$66,$00,$C9,$92,$4A,$2E,$01,$25,$67,$06,$70,$65,$61,$00
	dc.b $1C,$DA,$3A,$FC,$F0,$78,$3A,$C6,$60,$00,$E5,$7E,$4A,$2E,$01,$23
	dc.b $66,$0A,$0C,$2E,$00,$14,$01,$21,$66,$00,$C9,$6C,$4A,$2E,$01,$25
	dc.b $67,$06,$70,$65,$61,$00,$1C,$B4,$3A,$FC,$F0,$00,$61,$00,$AF,$A4
	dc.b $66,$24,$4A,$00,$67,$1A,$36,$3C,$2C,$00,$86,$02,$3A,$C3,$B2,$3C
	dc.b $00,$2C,$66,$00,$1C,$72,$12,$1C,$61,$00,$AE,$EA,$00,$24,$4E,$75
	dc.b $70,$0E,$60,$00,$1C,$86,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$56
	dc.b $66,$EE,$12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$41,$66,$E0
	dc.b $12,$1C,$48,$81,$12,$36,$10,$7E,$B2,$3C,$00,$4C,$66,$D2,$12,$1C
	dc.b $3A,$FC,$28,$00,$60,$B8,$0C,$2E,$00,$20,$01,$21,$66,$00,$C8,$F8
	dc.b $3A,$C6,$4E,$75,$0C,$2E,$00,$3C,$01,$21,$67,$00,$00,$0C,$0C,$2E
	dc.b $00,$20,$01,$21,$66,$00,$C8,$E0,$4A,$2E,$01,$25,$67,$06,$70,$65
	dc.b $61,$00,$1C,$28,$B2,$3C,$00,$23,$66,$00,$1C,$04,$12,$1C,$3A,$FC
	dc.b $F8,$00,$3A,$C6,$61,$00,$B2,$2A,$60,$00,$BE,$F4,$0C,$2E,$00,$20
	dc.b $01,$21,$66,$00,$C8,$B2,$61,$00,$E6,$96,$3A,$FC,$F8,$00,$3A,$C6
	dc.b $61,$00,$AE,$52,$00,$65,$20,$6E,$02,$4C,$30,$10,$02,$00,$00,$38
	dc.b $66,$18,$B2,$3C,$00,$3A,$66,$00,$BB,$B8,$12,$1C,$61,$00,$AE,$B6
	dc.b $20,$6E,$02,$4C,$85,$28,$00,$03,$60,$06,$08,$E8,$00,$00,$00,$02
	dc.b $B2,$3C,$00,$2C,$66,$00,$1B,$A0,$12,$1C,$61,$00,$AE,$98,$20,$6E
	dc.b $02,$4C,$E9,$0A,$85,$28,$00,$02,$4E,$75,$0C,$2E,$00,$3C,$01,$21
	dc.b $67,$0A,$0C,$2E,$00,$28,$01,$21,$66,$00,$C8,$4C,$4A,$2E,$01,$25
	dc.b $67,$06,$70,$65,$61,$00,$1B,$94,$41,$FA,$00,$1C,$61,$00,$EE,$90
	dc.b $8C,$42,$3A,$C6,$4E,$75,$61,$D2,$B2,$3C,$00,$2C,$66,$00,$1B,$58
	dc.b $12,$1C,$60,$00,$F9,$9E,$00,$08,$42,$43,$00,$00,$00,$C0,$00,$08
	dc.b $44,$43,$00,$00,$00,$40,$00,$08,$49,$43,$00,$00,$00,$80,$00,$08
	dc.b $4E,$43,$00,$00,$00,$00,$00,$00,$0C,$2E,$00,$3C,$01,$21,$67,$00
	dc.b $00,$0C,$0C,$2E,$00,$28,$01,$21,$66,$00,$C7,$EC,$3A,$C6,$61,$00
	dc.b $AF,$32,$B2,$3C,$00,$2C,$66,$00,$1B,$0E,$12,$1C,$10,$05,$02,$00
	dc.b $00,$3F,$B0,$3C,$00,$39,$67,$6A,$02,$00,$00,$30,$B0,$3C,$00,$10
	dc.b $66,$00,$1A,$F0,$3F,$05,$61,$00,$AF,$0A,$30,$05,$02,$00,$00,$38
	dc.b $B0,$3C,$00,$18,$66,$30,$10,$05,$02,$40,$00,$07,$E8,$58,$00,$40
	dc.b $80,$00,$3A,$C0,$3A,$1F,$08,$C5,$00,$05,$08,$05,$00,$03,$67,$00
	dc.b $1A,$C2,$02,$45,$00,$27,$20,$6E,$02,$4C,$30,$10,$02,$40,$FF,$C0
	dc.b $8A,$40,$30,$85,$4E,$75,$30,$05,$02,$40,$00,$3F,$B0,$3C,$00,$39
	dc.b $66,$00,$1A,$A0,$3A,$1F,$08,$05,$00,$03,$67,$DA,$02,$45,$00,$07
	dc.b $60,$D4,$61,$00,$AE,$AE,$30,$05,$02,$40,$00,$38,$B0,$3C,$00,$10
	dc.b $66,$0A,$70,$18,$02,$45,$00,$07,$8A,$40,$60,$BA,$B0,$3C,$00,$18
	dc.b $66,$00,$1A,$70,$70,$08,$60,$EC,$70,$37,$60,$00,$1A,$8A,$14,$01
	dc.b $B2,$3C,$00,$22,$67,$06,$B2,$3C,$00,$27,$66,$EC,$24,$4C,$12,$1C
	dc.b $B2,$3C,$00,$0A,$67,$E2,$B2,$02,$66,$F4,$12,$1C,$B2,$02,$67,$EE
	dc.b $28,$0C,$98,$8A,$53,$44,$B2,$3C,$00,$2C,$66,$00,$1A,$3A,$12,$1C
	dc.b $16,$01,$B2,$3C,$00,$27,$67,$06,$B2,$3C,$00,$22,$66,$BA,$53,$44
	dc.b $65,$06,$B5,$0C,$67,$F8,$4E,$75,$70,$0A,$C1,$41,$B0,$03,$66,$06
	dc.b $52,$8C,$12,$1C,$70,$00,$4E,$75,$61,$A4,$57,$C0,$60,$00,$00,$D8
	dc.b $61,$9C,$56,$C0,$60,$00,$00,$D0,$61,$00,$AA,$5C,$67,$1E,$61,$00
	dc.b $A1,$62,$66,$18,$4A,$2E,$02,$38,$67,$12,$10,$29,$00,$0C,$08,$00
	dc.b $00,$07,$67,$08,$02,$00,$00,$40,$B0,$3C,$00,$40,$4E,$75,$41,$EE
	dc.b $03,$E8,$61,$00,$0C,$28,$66,$00,$19,$F2,$61,$CC,$57,$C0,$60,$00
	dc.b $00,$96,$41,$EE,$03,$E8,$61,$00,$0C,$14,$66,$00,$19,$DE,$61,$B8
	dc.b $56,$C0,$60,$00,$00,$82,$50,$EE,$01,$58,$61,$00,$A2,$FE,$51,$EE
	dc.b $01,$58,$4A,$43,$6B,$2C,$4A,$04,$66,$28,$4E,$75,$61,$E8,$B6,$3C
	dc.b $00,$02,$67,$1E,$4E,$75,$50,$EE,$01,$58,$61,$00,$A2,$DE,$51,$EE
	dc.b $01,$58,$4A,$43,$6B,$0C,$B6,$3C,$00,$01,$67,$06,$4A,$04,$66,$02
	dc.b $4E,$75,$70,$3E,$60,$00,$19,$90,$61,$DC,$1D,$7C,$00,$3D,$08,$3B
	dc.b $2D,$42,$08,$3C,$4E,$75,$70,$33,$60,$00,$19,$7C
loc_0_00006B08:
	move.w #$34,d0
	bra.w loc_0_0000846E
	dc.b $61,$E2,$5E,$C0,$60,$1C,$61,$DC,$5C,$C0,$60,$16,$61,$D6,$5D,$C0
	dc.b $60,$10,$61,$D0,$5F,$C0,$60,$0A,$61,$CA,$57,$C0,$60,$04,$61,$C4
	dc.b $56,$C0,$52,$6E,$08,$7E,$4A,$00,$67,$08,$61,$00,$01,$70,$72,$0A
	dc.b $4E,$75,$61,$00,$01,$68,$61,$00,$9C,$A8,$3E,$2E,$08,$7E,$61,$00
	dc.b $9B,$5C,$66,$B4,$61,$74,$67,$6C,$4A,$82,$67,$18,$B2,$BC,$45,$4C
	dc.b $53,$45,$66,$60,$B4,$BC,$49,$46,$00,$00,$66,$58,$BE,$6E,$08,$7E
	dc.b $67,$C8,$60,$50,$B2,$BC,$45,$4C,$53,$45,$67,$F0,$B2,$BC,$45,$4E
	dc.b $44,$43,$67,$12,$B2,$BC,$45,$4E,$44,$4D,$66,$1E,$4A,$2E,$01,$01
	dc.b $67,$32,$60,$00,$07,$00,$30,$2E,$08,$7E,$53,$6E,$08,$7E,$BE,$40
	dc.b $66,$22,$60,$96,$61,$00,$00,$E0,$60,$1A,$48,$41,$B2,$7C,$49,$46
	dc.b $66,$12,$48,$41,$41,$FA,$08,$B2,$30,$18,$67,$08,$B2,$40,$66,$F8
	dc.b $52,$6E,$08,$7E,$61,$00,$9C,$2A,$60,$84,$12,$1C,$B2,$3C,$00,$0A
	dc.b $67,$00,$00,$94,$B2,$3C,$00,$09,$67,$2E,$B2,$3C,$00,$20,$67,$28
	dc.b $B2,$3C,$00,$2A,$67,$00,$00,$80,$B2,$3C,$00,$3B,$67,$78,$12,$1C
	dc.b $B2,$3C,$00,$0A,$67,$70,$B2,$3C,$00,$09,$67,$0C,$B2,$3C,$00,$20
	dc.b $67,$06,$B2,$3C,$00,$3A,$66,$E6,$12,$1C,$B2,$3C,$00,$0A,$67,$56
	dc.b $B2,$3C,$00,$09,$67,$F2,$B2,$3C,$00,$20,$67,$EC,$B2,$3C,$00,$2A
	dc.b $67,$44,$B2,$3C,$00,$3B,$67,$3E,$41,$EE,$05,$A8,$42,$A0,$42,$A0
	dc.b $70,$07,$60,$1A,$12,$1C,$B2,$3C,$00,$0A,$67,$22,$B2,$3C,$00,$09
	dc.b $67,$1C,$B2,$3C,$00,$20,$67,$16,$B2,$3C,$00,$2E,$67,$10,$48,$81
	dc.b $12,$36,$10,$7E,$10,$C1,$51,$C8,$FF,$DC,$70,$00,$4E,$75,$4C,$EE
	dc.b $00,$06,$05,$A0,$70,$FF,$4E,$75,$30,$2E,$08,$7E,$67,$18,$4A,$2E
	dc.b $01,$01,$67,$0A,$24,$6E,$08,$82,$B0,$6A,$00,$0E,$67,$08,$53,$6E
	dc.b $08,$7E,$60,$00,$FE,$B6,$70,$30,$60,$00,$17,$FC,$30,$2E,$08,$7E
	dc.b $67,$14,$4A,$2E,$01,$01,$67,$0A,$24,$6E,$08,$82,$B0,$6A,$00,$0E
	dc.b $67,$04,$60,$00,$FE,$9E,$70,$31,$60,$00,$17,$DC,$4A,$2E,$01,$26
	dc.b $67,$22,$4A,$2E,$02,$38,$66,$1C,$4A,$2E,$01,$01,$67,$06,$4A,$2E
	dc.b $01,$17,$67,$10,$30,$2E,$08,$7E,$06,$00,$00,$30,$1D,$40,$08,$3B
	dc.b $60,$00,$25,$CE,$4E,$75,$22,$3C,$00,$00,$13,$88,$3D,$41,$01,$4E
	dc.b $61,$00,$23,$D8,$2D,$48,$01,$4A,$4E,$75,$70,$36,$60,$00,$17,$98
	dc.b $4A,$2E,$01,$01,$66,$F4,$4A,$AE,$08,$90,$66,$EE,$61,$00,$BE,$04
	dc.b $24,$6E,$01,$72,$48,$E7,$00,$0C,$61,$00,$9E,$7E,$56,$C0,$4C,$DF
	dc.b $30,$00,$4A,$2E,$02,$38,$66,$00,$00,$EE,$4A,$00,$67,$00,$17,$18
	dc.b $76,$08,$42,$84,$61,$00,$9F,$94,$48,$69,$00,$08,$10,$2E,$02,$39
	dc.b $67,$0C,$B0,$3C,$00,$01,$67,$06,$08,$E9,$00,$03,$00,$0C,$20,$6E
	dc.b $01,$4A,$0C,$6E,$01,$10,$01,$4E,$64,$02,$61,$8A,$22,$5F,$22,$88
	dc.b $42,$A8,$00,$08,$43,$E8,$00,$10,$20,$89,$21,$49,$00,$04,$21,$48
	dc.b $00,$0C,$2D,$49,$01,$4A,$04,$6E,$00,$10,$01,$4E,$26,$48,$61,$00
	dc.b $9A,$88,$61,$00,$99,$24,$66,$00,$FD,$90,$61,$30,$61,$00,$FE,$4C
	dc.b $67,$EC,$B2,$BC,$45,$4E,$44,$4D,$66,$E4,$4A,$82,$66,$E0,$20,$6B
	dc.b $00,$0C,$21,$6E,$01,$4A,$00,$04,$72,$0A,$08,$2E,$00,$00,$01,$4D
	dc.b $67,$08,$53,$6E,$01,$4E,$52,$AE,$01,$4A,$4E,$75,$0C,$6E,$01,$02
	dc.b $01,$4E,$64,$34,$20,$6B,$00,$0C,$21,$6E,$01,$4A,$00,$04,$61,$00
	dc.b $FF,$16,$22,$6B,$00,$0C,$23,$48,$00,$08,$27,$48,$00,$0C,$43,$E8
	dc.b $00,$0C,$20,$89,$42,$A8,$00,$04,$42,$A8,$00,$08,$70,$0C,$D0,$C0
	dc.b $D1,$AE,$01,$4A,$91,$6E,$01,$4E,$20,$6E,$01,$4A,$22,$4C,$72,$0A
	dc.b $10,$19,$10,$C0,$B2,$00,$66,$F8,$2D,$48,$01,$4A,$24,$09,$94,$8C
	dc.b $95,$6E,$01,$4E,$4E,$75,$4A,$00,$66,$00,$16,$30,$0C,$29,$00,$08
	dc.b $00,$0D,$66,$00,$16,$22,$08,$E9,$00,$06,$00,$0C,$66,$00,$16,$18
	dc.b $61,$00,$9A,$BA,$61,$00,$98,$72,$66,$00,$FC,$DE,$61,$00,$FD,$9C
	dc.b $67,$EE,$B2,$BC,$45,$4E,$44,$4D,$66,$E6,$4A,$82,$66,$E2,$72,$0A
	dc.b $4E,$75
loc_0_00006E42:
	move.l #$1F40,d1
	move.w d1,app_0886(a6)
	bsr.w loc_0_000090BA
	move.l a0,app_0888(a6)
	rts
loc_0_00006E56:
	moveq.l #78,d0
	bra.w loc_0_0000846E
loc_0_00006E5C:
	cmpi.w #580,app_0886(a6)
	bcs.b loc_0_00006E56
	movem.l d1/a1,-(a7)
	btst.b #3,$000C(a1)
	beq.b loc_0_00006E76
	bsr.w loc_0_00000C64
	bra.b loc_0_00006E7A
loc_0_00006E76:
	bsr.w loc_0_00000C44
loc_0_00006E7A:
	movem.l (a7)+,d1/a1
	tst.b app_0238(a6)
	beq.b loc_0_00006E8E
	btst.b #6,$000C(a1)
	beq.w loc_0_0000844E
loc_0_00006E8E:
	moveq.l #87,d0
	cmp.b #$A,d1
	beq.b loc_0_00006EAC
	cmp.b #$9,d1
	beq.b loc_0_00006EAC
	cmp.b #$20,d1
	beq.b loc_0_00006EAC
	cmp.b #$2E,d1
	bne.w loc_0_00008446
	moveq.l #0,d0
loc_0_00006EAC:
	movea.l app_0888(a6),a0
	sf.b $000C(a0)
	move.l app_0882(a6),(a0)
	move.l a0,app_0882(a6)
	move.w app_0880(a6),$000A(a0)
	movea.l $0008(a1),a1
	move.l a1,$0004(a0)
	move.l (a1),$0010(a0)
	move.w app_087E(a6),$000E(a0)
	lea.l $0008(a0),a1
	clr.w (a1)
	lea.l $0116(a0),a0
	move.b d0,(a0)+
	bne.b loc_0_00006EFE
	subq.l #1,a0
loc_0_00006EE4:
	move.b (a4)+,d1
	cmp.b #$A,d1
	beq.b loc_0_00006EFE
	cmp.b #$9,d1
	beq.b loc_0_00006EFC
	cmp.b #$20,d1
	beq.b loc_0_00006EFC
	move.b d1,(a0)+
	bra.b loc_0_00006EE4
loc_0_00006EFC:
	move.b (a4)+,d1
loc_0_00006EFE:
	clr.b (a0)+
loc_0_00006F00:
	cmp.b #$A,d1
	beq.w loc_0_00006F88
	cmp.b #$2A,d1
	beq.b loc_0_00006F88
	cmp.b #$3B,d1
	beq.b loc_0_00006F88
	cmp.b #$9,d1
	beq.b loc_0_00006F20
	cmp.b #$20,d1
	bne.b loc_0_00006F24
loc_0_00006F20:
	move.b (a4)+,d1
	bra.b loc_0_00006F00
loc_0_00006F24:
	addq.w #1,(a1)
	cmp.b #$2C,d1
	beq.b loc_0_00006F72
	cmp.b #$A,d1
	beq.b loc_0_00006F72
	cmp.b #$3C,d1
	bne.b loc_0_00006F54
loc_0_00006F38:
	move.b (a4)+,d1
	beq.b loc_0_00006F38
	cmp.b #$A,d1
	beq.b loc_0_00006F72
	cmp.b #$3E,d1
	bne.b loc_0_00006F50
	move.b (a4)+,d1
	cmp.b #$3E,d1
	bne.b loc_0_00006F72
loc_0_00006F50:
	move.b d1,(a0)+
	bra.b loc_0_00006F38
loc_0_00006F54:
	move.b d1,(a0)+
loc_0_00006F56:
	move.b (a4)+,d1
	beq.b loc_0_00006F56
	cmp.b #$A,d1
	beq.b loc_0_00006F72
	cmp.b #$9,d1
	beq.b loc_0_00006F72
	cmp.b #$20,d1
	beq.b loc_0_00006F72
	cmp.b #$2C,d1
	bne.b loc_0_00006F54
loc_0_00006F72:
	clr.b (a0)+
	cmp.b #$2C,d1
	bne.b loc_0_00006F88
	move.b (a4)+,d1
	cmp.b #$A,d1
	bne.b loc_0_00006F24
	bra.b loc_0_00006FB4
loc_0_00006F84:
	move.l (a7)+,app_0882(a6)
loc_0_00006F88:
	move.l a0,d0
	addq.l #1,d0
	bclr #0,d0
	move.l app_0888(a6),-(a7)
	move.l d0,app_0888(a6)
	sub.l (a7)+,d0
	sub.w d0,app_0886(a6)
	move.w app_0898(a6),d0
	bne.b loc_0_00006FA8
	st.b app_0118(a6)
loc_0_00006FA8:
	st.b app_0101(a6)
	addq.w #1,d0
	move.w d0,app_0898(a6)
	rts
loc_0_00006FB4:
	movea.l app_0882(a6),a2
	move.l a2,-(a7)
	move.l (a2),app_0882(a6)
	movem.l a0-a1,-(a7)
	bsr.w loc_0_0000061A
	movem.l (a7)+,a0-a1
	bne.b loc_0_00006F84
	cmp.b #$26,d0
	bne.b loc_0_00006F84
	movem.l a0-a1,-(a7)
	bsr.w loc_0_000007F0
	bsr.w loc_0_000006AC
	movem.l (a7)+,a0-a1
	movea.l (a7)+,a2
	bne.w loc_0_00006B08
	move.l a2,app_0882(a6)
	move.b (a4)+,d1
	cmp.b #$26,d1
	beq.b loc_0_00006FFA
	moveq.l #70,d0
	bsr.w loc_0_00008486
loc_0_00006FFA:
	move.b (a4)+,d1
	cmp.b #$9,d1
	beq.b loc_0_00006FFA
	cmp.b #$20,d1
	beq.b loc_0_00006FFA
	bra.w loc_0_00006F24
loc_0_0000700C:
	move.w app_0898(a6),d0
	cmp.w app_089A(a6),d0
	bhi.b loc_0_00007030
	bsr.w loc_0_0000743C
	movea.l a4,a0
	movea.l app_0882(a6),a2
	lea.l $0014(a2),a1
	moveq.l #0,d2
	bra.w loc_0_0000710C
loc_0_0000702A:
	tst.l app_0890(a6)
	bne.b loc_0_0000700C
loc_0_00007030:
	movea.l app_0882(a6),a2
	movea.l $0004(a2),a1
	movea.l $0010(a2),a0
	cmpa.l $0004(a1),a0
	bne.b loc_0_0000704C
	movea.l $0008(a1),a1
	move.l a1,$0004(a2)
	movea.l (a1),a0
loc_0_0000704C:
	moveq.l #10,d0
	movea.l a0,a4
	moveq.l #92,d2
loc_0_00007052:
	move.b (a0)+,d1
	cmp.b d0,d1
	beq.b loc_0_0000705E
	cmp.b d2,d1
	bne.b loc_0_00007052
	bra.b loc_0_0000707A
loc_0_0000705E:
	tst.l app_0890(a6)
	beq.b loc_0_0000706E
	move.w app_0898(a6),d0
	cmp.w app_089A(a6),d0
	bls.b loc_0_00007072
loc_0_0000706E:
	move.l a0,$0010(a2)
loc_0_00007072:
	move.l a4,app_0240(a6)
	moveq.l #0,d0
	rts
loc_0_0000707A:
	lea.l $0014(a2),a1
	move.l a0,d2
	sub.l a4,d2
	subq.w #1,d2
	beq.b loc_0_00007094
	move.l a0,d1
	move.w d2,d0
	movea.l a4,a0
loc_0_0000708C:
	move.b (a0)+,(a1)+
	subq.w #1,d0
	bne.b loc_0_0000708C
	movea.l d1,a0
loc_0_00007094:
	move.b (a0)+,d1
	cmp.b #$A,d1
	beq.w loc_0_00007126
	cmp.b #$40,d1
	beq.w loc_0_00007190
	cmp.b #$3C,d1
	beq.w loc_0_000071F6
	cmp.b #$3F,d1
	beq.w loc_0_0000713C
	moveq.l #48,d0
	cmp.b d0,d1
	bcs.b loc_0_00007132
	cmp.b #$3A,d1
	bcs.b loc_0_000070DE
	moveq.l #55,d0
	cmp.b #$41,d1
	bcs.b loc_0_00007106
	cmp.b #$5B,d1
	bcs.b loc_0_000070DE
	moveq.l #87,d0
	cmp.b #$61,d1
	bcs.b loc_0_00007106
	cmp.b #$7B,d1
	bcc.b loc_0_00007106
loc_0_000070DE:
	sub.b d0,d1
	move.l a0,-(a7)
	lea.l $0116(a2),a0
	ext.w d1
	beq.b loc_0_000070F8
	cmp.w $0008(a2),d1
	bgt.b loc_0_00007102
loc_0_000070F0:
	tst.b (a0)+
	bne.b loc_0_000070F0
	subq.w #1,d1
	bne.b loc_0_000070F0
loc_0_000070F8:
	addq.b #1,d2
	beq.b loc_0_0000711E
	move.b (a0)+,(a1)+
	bne.b loc_0_000070F8
	subq.l #1,a1
loc_0_00007102:
	movea.l (a7)+,a0
	bra.b loc_0_0000710C
loc_0_00007106:
	addq.b #1,d2
	beq.b loc_0_00007120
	move.b d1,(a1)+
loc_0_0000710C:
	move.b (a0)+,d1
	cmp.b #$A,d1
	beq.b loc_0_00007126
	cmp.b #$5C,d1
	bne.b loc_0_00007106
	bra.w loc_0_00007094
loc_0_0000711E:
	movea.l (a7)+,a0
loc_0_00007120:
	cmpi.b #10,(a0)+
	bne.b loc_0_00007120
loc_0_00007126:
	move.b #$A,(a1)+
	lea.l $0014(a2),a4
	bra.w loc_0_0000705E
loc_0_00007132:
	cmp.b #$23,d1
	beq.w loc_0_00007270
	bra.b loc_0_00007106
loc_0_0000713C:
	move.b (a0)+,d1
	moveq.l #48,d0
	cmp.b d0,d1
	bcs.b loc_0_00007132
	cmp.b #$3A,d1
	bcs.b loc_0_00007166
	moveq.l #55,d0
	cmp.b #$41,d1
	bcs.b loc_0_00007106
	cmp.b #$5B,d1
	bcs.b loc_0_00007166
	moveq.l #87,d0
	cmp.b #$61,d1
	bcs.b loc_0_00007106
	cmp.b #$7B,d1
	bcc.b loc_0_00007106
loc_0_00007166:
	sub.b d0,d1
	move.l a0,-(a7)
	lea.l $0116(a2),a0
	ext.w d1
	beq.b loc_0_00007180
	cmp.w $0008(a2),d1
	bgt.b loc_0_0000718A
loc_0_00007178:
	tst.b (a0)+
	bne.b loc_0_00007178
	subq.w #1,d1
	bne.b loc_0_00007178
loc_0_00007180:
	moveq.l #0,d1
loc_0_00007182:
	tst.b (a0)+
	beq.b loc_0_0000718C
	addq.l #1,d1
	bra.b loc_0_00007182
loc_0_0000718A:
	moveq.l #0,d1
loc_0_0000718C:
	bra.w loc_0_000071C4
loc_0_00007190:
	tst.b $000C(a2)
	bne.b loc_0_000071A2
	st.b $000C(a2)
	addq.w #1,app_0880(a6)
	addq.w #1,$000A(a2)
loc_0_000071A2:
	cmp.b #$F9,d2
	bcc.w loc_0_00007120
	addq.b #1,d2
	move.b #$5F,(a1)+
	move.l a0,-(a7)
	moveq.l #0,d1
	move.w $000A(a2),d1
	cmp.w #$A,d1
	bcs.b loc_0_000071E2
	cmp.w #$64,d1
	bcs.b loc_0_000071E8
loc_0_000071C4:
	movem.l d4/a2-a3,-(a7)
	movea.l a1,a3
	move.w d2,d4
	lea.l loc_0_000071F0(pc),a2
	bsr.w loc_0_00008F08
	movea.l a3,a1
	move.w d4,d2
	movem.l (a7)+,d4/a2-a3
	movea.l (a7)+,a0
	bra.w loc_0_0000710C
loc_0_000071E2:
	addq.b #1,d2
	move.b #$30,(a1)+
loc_0_000071E8:
	addq.b #1,d2
	move.b #$30,(a1)+
	bra.b loc_0_000071C4
loc_0_000071F0:
	addq.b #1,d4
	move.b d1,(a3)+
	rts
loc_0_000071F6:
	cmp.b #$F5,d2
	bcc.w loc_0_00007120
	move.b (a0)+,d1
	movem.l d2/d4/a0-a4,-(a7)
	cmp.b #$24,d1
	seq.b d4
	bne.b loc_0_00007214
	move.b (a0)+,d1
	bra.b loc_0_00007214
loc_0_00007210:
	move.l d2,d1
	bra.b loc_0_00007236
loc_0_00007214:
	movea.l a0,a4
	lea.l app_03E8(a6),a0
	bsr.w loc_0_000076B8
	bne.b loc_0_00007262
	cmp.b #$3E,d1
	bne.b loc_0_00007262
	bsr.w loc_0_000014C2
	beq.b loc_0_00007210
	bsr.w loc_0_00000BCE
	bne.b loc_0_00007262
	move.l $0008(a1),d1
loc_0_00007236:
	movea.l $000C(a7),a3
	lea.l loc_0_000071F0(pc),a2
	tst.b d4
	beq.b loc_0_0000724A
	move.l (a7),d4
	bsr.w loc_0_00008ED8
	bra.b loc_0_00007250
loc_0_0000724A:
	move.l (a7),d4
	bsr.w loc_0_00008F08
loc_0_00007250:
	move.l a3,d1
	move.w d4,d2
	move.l a4,d3
	movem.l (a7)+,d0/d4/a0-a4
	movea.l d1,a1
	movea.l d3,a0
	bra.w loc_0_0000710C
loc_0_00007262:
	movem.l (a7)+,d2/d4/a0-a4
	moveq.l #73,d0
	bsr.w loc_0_00008486
	bra.w loc_0_0000710C
loc_0_00007270:
	cmp.b #$FC,d2
	bcc.w loc_0_00007120
	moveq.l #0,d1
	move.w $0008(a2),d1
	move.l a0,-(a7)
	bra.w loc_0_000071C4
	dc.b $4A,$2E,$01,$01,$67,$54,$24,$6E,$08,$82,$3D,$6A,$00,$0E,$08,$7E
	dc.b $4A,$2E,$01,$01,$67,$44,$4A,$2E,$01,$17,$66,$04,$50,$EE,$01,$13
	dc.b $53,$6E,$08,$98,$24,$6E,$08,$82,$20,$0A,$90,$AE,$08,$88,$91,$6E
	dc.b $08,$86,$2D,$4A,$08,$88,$30,$2A,$00,$0E,$B0,$6E,$08,$7E,$67,$0A
	dc.b $3D,$40,$08,$7E,$70,$0A,$61,$00,$12,$C0,$20,$12,$2D,$40,$08,$82
	dc.b $66,$04,$51,$EE,$01,$01,$72,$0A,$4E,$75,$70,$35,$60,$00,$11,$A4
	dc.b $70,$3B,$60,$00,$11,$86,$28,$2E,$02,$3C,$41,$EE,$03,$E8,$4A,$90
	dc.b $67,$04,$61,$00,$99,$8C,$4A,$AE,$08,$90,$66,$00,$00,$36,$61,$00
	dc.b $F7,$CE,$2D,$42,$08,$8C,$6E,$30,$61,$00,$94,$E2,$61,$00,$93,$9A
	dc.b $66,$00,$F7,$F2,$61,$00,$F8,$B0,$67,$EE,$4A,$82,$66,$EA,$B2,$BC
	dc.b $52,$45,$50,$54,$67,$0C,$B2,$BC,$45,$4E,$44,$52,$66,$DA,$72,$0A
	dc.b $4E,$75,$70,$47,$60,$00,$11,$4C,$20,$6E,$01,$4A,$0C,$6E,$01,$10
	dc.b $01,$4E,$64,$04,$61,$00,$F9,$8C,$2D,$48,$08,$90,$3F,$2E,$01,$4E
	dc.b $42,$A8,$00,$08,$43,$E8,$00,$10,$20,$89,$21,$49,$00,$04,$21,$48
	dc.b $00,$0C,$2D,$49,$01,$4A,$04,$6E,$00,$10,$01,$4E,$26,$48,$61,$00
	dc.b $94,$7C,$42,$AE,$08,$90,$61,$00,$93,$30,$66,$00,$F7,$88,$2D,$4B
	dc.b $08,$90,$61,$00,$FA,$24,$61,$00,$F8,$3E,$67,$E2,$B2,$BC,$45,$4E
	dc.b $44,$52,$66,$DA,$4A,$82,$66,$D6,$61,$00,$94,$52,$50,$EE,$01,$13
	dc.b $20,$6B,$00,$0C,$21,$6E,$01,$4A,$00,$04,$08,$2E,$00,$00,$01,$4D
	dc.b $67,$14,$53,$6E,$01,$4E,$52,$AE,$01,$4A,$4A,$2E,$01,$01,$67,$06
	dc.b $3D,$6E,$08,$98,$08,$9A,$53,$AE,$08,$8C,$65,$3C,$2D,$4B,$08,$90
	dc.b $43,$EB,$00,$10,$2D,$49,$08,$94,$61,$00,$92,$CE,$66,$00,$F7,$26
	dc.b $48,$E7,$00,$18,$61,$00,$F7,$E0,$4C,$DF,$18,$00,$67,$0C,$B2,$BC
	dc.b $45,$4E,$44,$52,$66,$04,$4A,$82,$67,$CC,$50,$EE,$01,$13,$2F,$0B
	dc.b $61,$00,$95,$C2,$26,$5F,$60,$D0,$30,$1F,$34,$2E,$01,$4E,$4A,$AB
	dc.b $00,$08,$67,$02,$70,$00,$94,$40,$95,$6E,$01,$4E,$48,$C2,$D5,$AE
	dc.b $01,$4A,$42,$AE,$08,$90,$41,$FA,$24,$58,$2D,$48,$01,$7A,$72,$0A
	dc.b $4E,$75,$70,$48,$60,$00,$10,$4C
loc_0_0000743C:
	movea.l app_0890(a6),a1
	movea.l app_0894(a6),a0
	cmpa.l $0004(a1),a0
	bne.b loc_0_00007454
	movea.l $0008(a1),a1
	move.l a1,app_0890(a6)
	movea.l (a1),a0
loc_0_00007454:
	movea.l a0,a4
	moveq.l #10,d0
loc_0_00007458:
	cmp.b (a0)+,d0
	bne.b loc_0_00007458
	move.l a0,app_0894(a6)
	move.l a4,app_0240(a6)
	moveq.l #0,d0
	rts
	dc.b $4E,$45,$45,$51,$43,$00,$4E,$43,$44,$00,$4E,$44,$47,$54,$47,$45
	dc.b $4C,$54,$4C,$45,$00,$00
loc_0_0000747E:
	move.l d2,-(a7)
	bra.w loc_0_00000AE8
loc_0_00007484:
	dc.b $00,$00,$0D,$FE,$00,$00
loc_0_0000748A:
	lea.l loc_0_00007484(pc),a0
	tst.b app_0238(a6)
	beq.b loc_0_0000749C
	bsr.w loc_0_00009700
	move.b -$0001(a4),d1
loc_0_0000749C:
	moveq.l #0,d0
	bra.w loc_0_0000752E
loc_0_000074A2:
	tst.b app_0238(a6)
	beq.b loc_0_000074B0
	bsr.w loc_0_00009700
	move.b -$0001(a4),d1
loc_0_000074B0:
	cmp.b #$2E,d1
	bne.b loc_0_00007502
	move.b (a4)+,d1
	bmi.b loc_0_000074D2
	ext.w d1
	lea.l loc_0_00007578(pc),a1
	adda.w d1,a1
	move.b $0005(a0),d0
	bne.b loc_0_000074D6
loc_0_000074C8:
	move.b (a1),d0
	bmi.b loc_0_000074F6
	cmp.b #$4,d0
	bcs.b loc_0_00007518
loc_0_000074D2:
	bra.w loc_0_0000844A
loc_0_000074D6:
	bmi.b loc_0_000074E6
	tst.b $0122(a6)
	bne.w loc_0_000074E6
	subq.w #1,d0
loc_0_000074E2:
	beq.b loc_0_0000747E
	bra.b loc_0_000074C8
loc_0_000074E6:
	move.b (a1),d0
	bpl.b loc_0_00007518
	addq.w #2,d0
	beq.b loc_0_00007514
	addq.b #1,d0
	bne.b loc_0_000074D2
	moveq.l #6,d0
	bra.b loc_0_0000752E
loc_0_000074F6:
	addq.b #2,d0
	beq.b loc_0_00007514
	addq.b #1,d0
	bne.b loc_0_000074D2
	moveq.l #1,d0
	bra.b loc_0_00007518
loc_0_00007502:
	move.b $0005(a0),d0
	subq.w #1,d0
	bne.b loc_0_00007510
	tst.b $0122(a6)
	beq.b loc_0_000074E2
loc_0_00007510:
	moveq.l #0,d0
	bra.b loc_0_0000752E
loc_0_00007514:
	moveq.l #2,d0
	subq.l #1,a4
loc_0_00007518:
	move.b (a4)+,d1
	cmp.b #$9,d1
	beq.b loc_0_0000752E
	cmp.b #$20,d1
	beq.b loc_0_0000752E
	cmp.b #$A,d1
	bne.w loc_0_0000844A
loc_0_0000752E:
	cmp.b #$A,d1
	beq.b loc_0_00007542
	move.b (a4)+,d1
	cmp.b #$9,d1
	beq.b loc_0_0000752E
	cmp.b #$20,d1
	beq.b loc_0_0000752E
loc_0_00007542:
	move.b d0,app_0239(a6)
	sf.b app_023B(a6)
	move.w (a0)+,d6
	move.w (a0)+,d3
	move.w (a0)+,d2
	pea.l loc_0_00007614(pc)
	lea.l loc_0_00001D14(pc),a0
	adda.w d3,a0
	move.l a0,-(a7)
	move.w d1,-(a7)
	btst #15,d2
	beq.b loc_0_0000756A
	bsr.w loc_0_00000C64
	bra.b loc_0_00007574
loc_0_0000756A:
	btst #14,d2
	beq.b loc_0_00007574
	bsr.w loc_0_00000C44
loc_0_00007574:
	move.w (a7)+,d1
	rts
loc_0_00007578:
	dcb.b $9,$FF
	dc.b $FE
	dcb.b $16,$FF
	dc.b $FE
	dcb.b $21,$FF
	dc.b $01,$FF,$04,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$03,$FF,$FF,$FF,$05,$FF
	dc.b $FF,$FD,$FF,$FF,$FF,$02,$07
	dcb.b $9,$FF
	dc.b $01,$FF,$04,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$03,$FF,$FF,$FF,$05,$FF
	dc.b $FF,$FD,$FF,$FF,$FF,$02,$07,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$4A,$2E
	dc.b $01,$25,$67,$06,$70,$65,$61,$00,$0E,$84,$3A,$C6,$72,$0A,$4E,$75
	dc.b $20,$6E,$01,$7A,$42,$AE,$01,$7A,$4E,$D0
loc_0_00007614:
	dc.b $B2,$3C,$00,$0A,$67,$1E,$B2,$3C,$00,$09,$67,$18,$B2,$3C,$00,$20
	dc.b $67,$12,$B2,$3C,$00,$2A,$67,$0C,$B2,$3C,$00,$3B,$67,$06,$70,$0E
	dc.b $61,$00,$0E,$50,$4A,$AE,$01,$7A,$66,$CC,$4A,$AE,$01,$8E,$67,$1A
	dc.b $22,$2E,$01,$8E,$42,$AE,$01,$8E,$D3,$AE,$02,$3C,$4A,$81,$6B,$04
	dc.b $D3,$AE,$02,$24,$42,$AE,$01,$82,$4E,$75,$22,$0D,$92,$AE,$02,$4C
	dc.b $2D,$41,$01,$82,$67,$14,$24,$2E,$02,$3C,$D3,$AE,$02,$3C,$D3,$AE
	dc.b $02,$24,$4A,$2E,$02,$38,$66,$00,$20,$92,$4E,$75
loc_0_00007680:
	bsr.b loc_0_000076B8
	bne.b loc_0_000076A0
	movea.l (a0),a1
	move.b $0005(a0),d0
	moveq.l #46,d2
	addq.l #1,a1
	bra.b loc_0_00007694
loc_0_00007690:
	cmp.b (a1)+,d2
	beq.b loc_0_000076A2
loc_0_00007694:
	subq.b #1,d0
	bne.b loc_0_00007690
	move.b $0005(a0),d2
	movea.l a4,a1
	moveq.l #0,d0
loc_0_000076A0:
	rts
loc_0_000076A2:
	movea.l a4,a1
	move.b $0005(a0),d2
	sub.b d0,$0005(a0)
	ext.w d0
	suba.w d0,a4
	move.b -$0001(a4),d1
	moveq.l #0,d0
	rts
loc_0_000076B8:
	andi.w #255,d1
	lea.l loc_0_0000A764(pc),a2
	tst.b $0(a2,d1.w)
	beq.b loc_0_000076F4
	bpl.b loc_0_00007736
	move.b (a4),d1
	ext.w d1
	move.b $7E(a6,d1.w),d1
	cmp.b #$57,d1
	beq.b loc_0_000076E2
	cmp.b #$42,d1
	beq.b loc_0_000076E2
	cmp.b #$4C,d1
	bne.b loc_0_000076F0
loc_0_000076E2:
	move.b $0001(a4),d1
	tst.b $0(a2,d1.w)
	ble.b loc_0_000076F0
	moveq.l #46,d1
	bra.b loc_0_00007736
loc_0_000076F0:
	moveq.l #46,d1
	bra.b loc_0_0000773C
loc_0_000076F4:
	cmp.b #$3A,d1
	bcc.b loc_0_0000773C
	lea.l -$0001(a4),a1
	movea.l a4,a2
loc_0_00007700:
	move.b (a2)+,d1
	cmp.b #$24,d1
	beq.b loc_0_00007714
	cmp.b #$3A,d1
	bcc.b loc_0_00007736
	cmp.b #$30,d1
	bcc.b loc_0_00007700
loc_0_00007714:
	movea.l a2,a4
	move.l a2,d0
	sub.l a1,d0
	move.b d0,$0005(a0)
	lea.l $0006(a0),a2
	move.l a2,(a0)
	move.b app_0116(a6),(a2)+
	subq.b #1,d0
loc_0_0000772A:
	move.b (a1)+,(a2)+
	subq.b #1,d0
	bne.b loc_0_0000772A
	move.b (a4)+,d1
	moveq.l #0,d0
	rts
loc_0_00007736:
	clr.l (a0)
	moveq.l #41,d0
	rts
loc_0_0000773C:
	tst.b app_00FE(a6)
	bne.w loc_0_000077B0
	move.b d1,$0006(a0)
	lea.l -$0001(a4),a1
	move.l a1,(a0)
	moveq.l #0,d1
	moveq.l #0,d2
loc_0_00007752:
	move.b (a4)+,d1
	tst.b $0(a2,d1.w)
	beq.b loc_0_00007752
	bpl.b loc_0_00007794
	move.l a4,d2
	bra.b loc_0_00007752
loc_0_00007760:
	sub.l a4,d2
	addq.l #2,d2
	bne.b loc_0_00007798
	move.b -$0002(a4),d2
	cmp.b #$4C,d2
	beq.b loc_0_0000778E
	cmp.b #$6C,d2
	beq.b loc_0_0000778E
	cmp.b #$57,d2
	beq.b loc_0_0000778E
	cmp.b #$77,d2
	beq.b loc_0_0000778E
	cmp.b #$42,d2
	beq.b loc_0_0000778E
	cmp.b #$62,d2
	bne.b loc_0_00007798
loc_0_0000778E:
	subq.l #2,a4
	moveq.l #46,d1
	bra.b loc_0_00007798
loc_0_00007794:
	tst.l d2
	bne.b loc_0_00007760
loc_0_00007798:
	move.l a4,d0
	sub.l (a0),d0
	cmp.w app_021E(a6),d0
	bcs.b loc_0_000077A6
	move.w app_021E(a6),d0
loc_0_000077A6:
	subq.b #1,d0
	move.b d0,$0005(a0)
	moveq.l #0,d0
	rts
loc_0_000077B0:
	lea.l $0006(a0),a1
	move.l a1,(a0)
	moveq.l #1,d2
	moveq.l #0,d0
loc_0_000077BA:
	ext.w d1
	move.b $7E(a6,d1.w),d1
	move.b d1,(a1)+
	moveq.l #0,d1
	move.b (a4)+,d1
	tst.b $0(a2,d1.w)
	bgt.b loc_0_000077E4
	bmi.b loc_0_000077D6
	addq.b #1,d2
	bpl.b loc_0_000077BA
	moveq.l #127,d2
	bra.b loc_0_000077DC
loc_0_000077D6:
	move.l a4,d0
	addq.b #1,d2
	bpl.b loc_0_000077BA
loc_0_000077DC:
	move.b (a4)+,d1
	tst.b $0(a2,d1.w)
	ble.b loc_0_000077DC
loc_0_000077E4:
	tst.l d0
	beq.b loc_0_00007810
	sub.l a4,d0
	addq.l #2,d0
	bne.b loc_0_00007810
	move.b -$0002(a4),d0
	cmp.b #$4C,d0
	beq.b loc_0_0000780A
	cmp.b #$6C,d0
	beq.b loc_0_0000780A
	cmp.b #$57,d0
	beq.b loc_0_0000780A
	cmp.b #$77,d0
	bne.b loc_0_00007810
loc_0_0000780A:
	moveq.l #46,d1
	subq.l #2,a4
	subq.b #2,d2
loc_0_00007810:
	move.b d2,$0005(a0)
	moveq.l #0,d0
	rts
loc_0_00007818:
	moveq.l #0,d0
	move.b d1,d2
	cmp.b #$22,d1
	beq.b loc_0_0000782C
	cmp.b #$27,d1
	beq.b loc_0_0000782C
	moveq.l #0,d2
	subq.l #1,a4
loc_0_0000782C:
	move.b (a4)+,d1
	cmp.b #$A,d1
	beq.b loc_0_00007870
	cmp.b d1,d2
	beq.b loc_0_00007880
	cmp.b #$9,d1
	beq.b loc_0_00007844
	cmp.b #$20,d1
	bne.b loc_0_00007848
loc_0_00007844:
	tst.b d2
	beq.b loc_0_00007870
loc_0_00007848:
	cmp.b #$2C,d1
	bne.b loc_0_0000785A
	btst #16,d3
	beq.b loc_0_0000785A
loc_0_00007854:
	move.l a4,$0196(a6)
	bra.b loc_0_00007870
loc_0_0000785A:
	btst #17,d3
	bne.b loc_0_00007866
	ext.w d1
	move.b $7E(a6,d1.w),d1
loc_0_00007866:
	move.b d1,$6(a0,d0.w)
	addq.b #1,d0
	bpl.b loc_0_0000782C
	moveq.l #126,d0
loc_0_00007870:
	lea.l $0005(a0),a1
	addq.b #1,d0
	move.b d0,(a1)+
	move.b d3,$5(a0,d0.w)
	move.l a1,(a0)
	rts
loc_0_00007880:
	cmpi.b #44,(a4)+
	bne.b loc_0_00007870
	bra.b loc_0_00007854
	dc.b $FF,$FF,$FF,$00,$20,$02,$C0,$BA,$FF,$F8,$67,$44,$B0,$BA,$FF,$F2
	dc.b $67,$3E,$60,$2A,$20,$02,$48,$40,$4A,$40,$67,$34,$52,$40,$67,$30
	dc.b $60,$1C,$B6,$3C,$00,$01,$67,$1C,$10,$02,$48,$80,$60,$08,$B6,$3C
	dc.b $00,$01,$67,$10
loc_0_000078BC:
	move.w d2,d0
	ext.l d0
	cmp.l d0,d2
	bne.b loc_0_000078C6
	rts
loc_0_000078C6:
	moveq.l #29,d0
	bra.w loc_0_00008486
	dc.b $70,$1E,$4A,$2E,$01,$07,$67,$00,$0B,$B2,$4E,$75,$B6,$3C,$00,$01
	dc.b $67,$EE,$4E,$75
loc_0_000078E0:
	movea.l a4,a0
	lea.l app_057F(a6),a4
	move.b (a4)+,d1
	move.l a0,-(a7)
	bsr.b loc_0_00007902
	lea.l loc_0_000078FC(pc),a4
	move.b (a4)+,d1
	moveq.l #1,d3
	bsr.w loc_0_00007952
	movea.l (a7)+,a4
	rts
loc_0_000078FC:
	dc.b $54,$45,$58,$54,$0A,$00
loc_0_00007902:
	clr.l $015A(a6)
	lea.l app_03E8(a6),a0
	moveq.l #9,d3
	bsr.w loc_0_00007818
	movea.l $0172(a6),a2
	movem.l a3-a5,-(a7)
	bsr.w loc_0_00000B88
	sne.b d0
	movem.l (a7)+,a3-a5
	tst.b app_0238(a6)
	bne.b loc_0_00007942
	tst.b d0
	beq.b loc_0_00007942
	moveq.l #0,d4
	moveq.l #9,d3
	bsr.w loc_0_00000CBA
loc_0_00007934:
	move.l a1,$013E(a6)
	lea.l $0010(a1),a1
	move.l a1,$0162(a6)
	rts
loc_0_00007942:
	tst.b d0
	bne.b loc_0_0000794C
	bsr.b loc_0_00007934
	bra.w loc_0_000096A4
loc_0_0000794C:
	moveq.l #11,d0
	bra.w loc_0_0000846E
loc_0_00007952:
	sf.b app_011B(a6)
	sf.b app_011C(a6)
	move.b d3,$0108(a6)
	lea.l app_03E8(a6),a0
	clr.l $0196(a6)
	bset #16,d3
	btst.b #1,app_021D(a6)
	beq.b loc_0_00007976
	bset #17,d3
loc_0_00007976:
	bsr.w loc_0_00007818
	movea.l $013E(a6),a2
	addq.w #8,a2
	movem.l d3/a3-a5,-(a7)
	bsr.w loc_0_00000B88
	sne.b d0
	movem.l (a7)+,d3/a3-a5
	tst.b app_0238(a6)
	bne.b loc_0_000079C6
	tst.b d0
	beq.b loc_0_000079B2
	moveq.l #0,d4
	bsr.w loc_0_00000CBA
	movea.l $013E(a6),a0
	subq.b #1,$000C(a0)
loc_0_000079A6:
	move.b $000C(a0),d0
	bsr.w loc_0_000079E4
	move.b d0,$000E(a1)
loc_0_000079B2:
	move.l a1,$0142(a6)
	move.l $0008(a1),app_023C(a6)
	move.b $000E(a1),$0146(a6)
	bra.w loc_0_0000988A
loc_0_000079C6:
	tst.b d0
	beq.b loc_0_000079B2
	bra.b loc_0_0000794C
loc_0_000079CC:
	movea.l $0142(a6),a1
	move.l app_023C(a6),$0008(a1)
	bra.w loc_0_00009864
loc_0_000079DA:
	tst.b app_0238(a6)
	bne.w loc_0_000096BE
	rts
loc_0_000079E4:
	rts
loc_0_000079E6:
	movea.l app_0940(a6),a0
	clr.w (a0)
	move.l a0,app_089C(a6)
	sf.b app_010B(a6)
	rts
loc_0_000079F6:
	move.l a0,-(a7)
	movea.l app_089C(a6),a0
	move.w #$2B2B,(a0)+
	move.w d3,(a0)+
loc_0_00007A02:
	move.l a0,app_089C(a6)
	clr.w (a0)
	movea.l (a7)+,a0
	rts
loc_0_00007A0C:
	move.l a0,-(a7)
	move.b $000E(a1),d0
	movea.l app_089C(a6),a0
	move.w #$2B2B,(a0)+
	st.b (a0)+
	move.b d0,(a0)+
	bra.b loc_0_00007A02
loc_0_00007A20:
	move.l a0,-(a7)
	movea.l app_089C(a6),a0
	move.w #$2D2D,-$0004(a0)
	movea.l (a7)+,a0
	rts
loc_0_00007A30:
	dc.b "line malformed",$00
	dc.b "out of memory",$00
	dc.b "undefined symbol",$00
	dc.b "additional symbol on pass 2",$00
	dc.b "symbol defined twice",$00
	dc.b "phasing error",$00
	dc.b "local not allowed",$00
	dc.b "INTERNAL:invalid hashing",$00
	dc.b "instruction not recognised",$00
	dc.b "invalid size",$00
	dc.b "duplicate MODULE name",$00
	dc.b "forward reference",$00
	dc.b "invalid section name, TEXT assumed",$00
	dc.b "garbage following instruction",$00
	dc.b "addressing mode not recognised",$00
	dc.b "address register expected",$00
	dc.b "addressing mode not allowed",$00
	dc.b "expression mismatch",$00
	dc.b "missing close bracket",$00
	dc.b "imported label not allowed",$00
	dc.b "illegal type combination",$00
	dc.b "invalid number",$00
	dc.b "number too large",$00
	dc.b "misuse of label",$00
	dc.b "include file read error",$00
	dc.b "file not found",$00
	dc.b "header file not found",$00
	dc.b "repeated include file",$00
	dc.b "data too large",$00
	dc.b "relative not allowed",$00
	dc.b "comma expected",$00
	dc.b ".W or .L expected as index size",$00
	dc.b "absolute not allowed",$00
	dc.b "wrong processor",$00
	dc.b "odd address",$00
	dc.b "immediate data expected",$00
	dc.b "data register expected",$00
	dc.b "BSS or OFFSET section cannot contain data",$00
	dc.b "during writing binary file",$00
	dc.b "cannot create binary file",$00
	dc.b "symbol expected",$00
	dc.b "XREFs not allowed within brackets",$00
	dc.b "cannot import symbol",$00
	dc.b "cannot export symbol",$00
	dc.b "not yet implemented",$00
	dc.b "register expected",$00
	dc.b "invalid MOVEP addressing mode",$00
	dc.b "spurious ENDC",$00
	dc.b "spurious ELSE",$00
	dc.b "missing ENDC",$00
	dc.b "invalid IF expression, ignored",$00
	dc.b "source expired prematurely",$00
	dc.b "spurious ENDM or MEXIT",$00
	dc.b "cannot nest MACRO definitions or define in REPTs",$00
	dc.b "missing quote",$00
	dc.b "user error",$00
	dc.b "invalid register list",$00
	dc.b "invalid option",$00
	dc.b "fatally bad conditional",$00
	dc.b "relocation not allowed",$00
	dc.b "division by zero",$00
	dc.b "absolute expression MUST evaluate",$00
	dc.b "illegal BSR.S",$00
	dc.b "option must be at start",$00
	dc.b "INTERNAL:invalid optimisation",$00
	dc.b "can only assemble executable code to memory",$00
	dc.b "program buffer full",$00
	dc.b "linker format restriction",$00
	dc.b "ORG/RORG not allowed",$00
	dc.b "INTERNAL:invalid multi-line macro call",$00
	dc.b "cannot nest repeat loops",$00
	dc.b "spurious ENDR",$00
	dc.b "invalid numeric expansion",$00
	dc.b "during listing output",$00
	dc.b "invalid printer parameter",$00
	dc.b "invalid FORMAT parameter",$00
	dc.b "INTERNAL:bad section",$00
	dc.b "INTERNAL:macro memory",$00
	dc.b "assembly interrupted",$00
	dc.b "invalid section type",$00
	dc.b "in command-line symbol",$00
	dc.b "# probably missing",$00
	dc.b "short branch cannot be 0 bytes",$00
	dc.b "DCB or DS count must not be negative",$00
	dc.b "invalid bitfield specification",$00
	dc.b "colon (:) expected",$00
	dc.b "floating-point register expected",$00
	dc.b "MMU register expected",$00
	dc.b "invalid MMU function code",$00
	dc.b "invalid radix",$00
	dc.b "invalid 68020 addressing mode",$00
	dc.b "invalid index scale",$00
	dc.b "hex floating point number too large",$00
	dc.b "invalid opcode size for data/address register",$00
	dc.b "only FPIAR allowed",$00
	dc.b "maths co-processor required",$00
	dc.b "invalid k-factor",$00
	dc.b "floating point constant not allowed",$00
	dc.b "floating point constant too large",$00
	dc.b "bad floating point expression",$00
	dc.b "privileged instruction",$00
	dc.b "invalid section specified",$00
	dc.b "invalid pre-assembled file",$00
	dc.b "only (An) allowed for this instruction",$00
	dc.b "INTERNAL:memory list corrupt",$00
	dc.b "bit number should be 0-7 for byte",$00
	dc.b $70,$28,$60,$4C
loc_0_00008422:
	bsr.w loc_0_0000B024
	bne.b loc_0_0000842A
	rts
loc_0_0000842A:
	bsr.w loc_0_000098AE
	moveq.l #39,d0
	bra.b loc_0_0000846E
loc_0_00008432:
	moveq.l #1,d0
	bra.b loc_0_00008486
loc_0_00008436:
	moveq.l #5,d0
	bra.b loc_0_00008486
loc_0_0000843A:
	moveq.l #4,d0
	bra.b loc_0_00008486
loc_0_0000843E:
	moveq.l #6,d0
	bra.b loc_0_00008486
loc_0_00008442:
	moveq.l #7,d0
	bra.b loc_0_00008486
loc_0_00008446:
	moveq.l #9,d0
	bra.b loc_0_00008486
loc_0_0000844A:
	moveq.l #10,d0
	bra.b loc_0_00008486
loc_0_0000844E:
	moveq.l #12,d0
	bra.b loc_0_00008486
loc_0_00008452:
	moveq.l #33,d0
	bra.b loc_0_00008486
	dc.b $70,$1D,$60,$2C
loc_0_0000845A:
	moveq.l #38,d0
	bra.b loc_0_00008486
	dc.b $70,$0F,$60,$20,$70,$1F,$60,$1C,$70,$20,$60,$18,$70,$24,$60,$14
loc_0_0000846E:
	sf.b app_0955(a6)
	move.b #$14,app_023A(a6)
	bsr.b loc_0_00008486
	jmp loc_0_000003B0.l
loc_0_00008480:
	rts
loc_0_00008482:
	movea.l app_0234(a6),a7
loc_0_00008486:
	tst.b app_010D(a6)
	bne.b loc_0_00008480
	st.b app_010D(a6)
	cmpi.b #10,app_023A(a6)
	bcc.b loc_0_0000849E
	move.b #$A,app_023A(a6)
loc_0_0000849E:
	move.l a4,$0154(a6)
	movem.l d1-d3/a0-a3,-(a7)
	move.w d0,-(a7)
	moveq.l #6,d0
	bsr.w loc_0_00008E7A
	lea.l loc_0_00007A30(pc),a0
	addq.b #1,$010C(a6)
	moveq.l #0,d2
loc_0_000084B8:
	move.w (a7)+,d0
loc_0_000084BA:
	subq.w #1,d0
	beq.w loc_0_000084C6
loc_0_000084C0:
	tst.b (a0)+
	bne.b loc_0_000084C0
	bra.b loc_0_000084BA
loc_0_000084C6:
	tst.l $01A2(a6)
	beq.b loc_0_00008530
	movem.l d1-d3/a0-a2,-(a7)
	moveq.l #0,d3
	move.w app_0218(a6),d3
	moveq.l #0,d2
	movea.l $017E(a6),a1
	move.l a1,d1
	beq.b loc_0_00008520
	cmpi.b #12,$000D(a1)
	bne.b loc_0_0000852C
	move.l $0098(a1),d2
	tst.b app_0101(a6)
	bne.b loc_0_00008516
	tst.l app_0890(a6)
	bne.w loc_0_00008516
	move.l app_0240(a6),d1
	beq.b loc_0_0000852C
	movea.l d1,a2
	moveq.l #0,d0
	move.l $0154(a6),d1
loc_0_00008508:
	cmpa.l d1,a2
	beq.b loc_0_0000851A
	cmp.b #$A,d0
	beq.b loc_0_0000852C
	move.b (a2)+,d0
	bra.b loc_0_00008508
loc_0_00008516:
	move.l $009E(a1),d1
loc_0_0000851A:
	sub.l $0008(a1),d1
	subq.l #1,d1
loc_0_00008520:
	movea.l $01A2(a6),a1
	moveq.l #0,d0
	movea.l $0004(a1),a1
	jsr (a1)
loc_0_0000852C:
	movem.l (a7)+,d1-d3/a0-a2
loc_0_00008530:
	bsr.w loc_0_00009292
	move.w app_0218(a6),d0
	beq.b loc_0_00008584
	cmp.w #$FFFF,d0
	beq.b loc_0_00008576
	moveq.l #9,d0
	bsr.w loc_0_00008E7A
	moveq.l #0,d1
	move.w app_0218(a6),d1
	bsr.w loc_0_00008F04
	tst.l $017E(a6)
	beq.b loc_0_00008576
	moveq.l #11,d0
	bsr.w loc_0_00008E7A
	movea.l $017E(a6),a1
	moveq.l #0,d2
	move.b $0016(a1),d2
	subq.b #2,d2
	lea.l $0017(a1),a1
loc_0_0000856C:
	move.b (a1)+,d1
	bsr.w loc_0_00008E98
	dbf.w d2,loc_0_0000856C
loc_0_00008576:
	bsr.w loc_0_00008E8C
	st.b $0102(a6)
	movem.l (a7)+,d1-d3/a0-a3
loc_0_00008582:
	rts
loc_0_00008584:
	moveq.l #28,d0
	bsr.w loc_0_00008E7A
	bra.b loc_0_00008576
loc_0_0000858C:
	tst.b app_0238(a6)
	beq.b loc_0_00008582
	tst.b app_0105(a6)
	beq.b loc_0_00008582
	cmpi.b #5,app_023A(a6)
	bcc.b loc_0_000085A6
	move.b #$5,app_023A(a6)
loc_0_000085A6:
	move.l a4,$0154(a6)
	movem.l d1-d3/a0-a3,-(a7)
	move.w d0,-(a7)
	moveq.l #8,d0
	bsr.w loc_0_00008E7A
	lea.l loc_0_000085C2(pc),a0
	move.w #$8000,d2
	bra.w loc_0_000084B8
loc_0_000085C2:
	dc.b "sign extended operand",$00
	dc.b "relative cannot be relocated",$00
	dc.b "invalid LINK displacement",$00
	dc.b "68010 instruction, converted to MOVE SR",$00
	dc.b "size should be .W",$00
	dc.b "directive ignored",$00
	dc.b "misuse of register list",$00
	dc.b "no ORG specified",$00
	dc.b "bit number should be 0-7 for byte",$00
	dc.b "missing ENDC at end of macro",$00
	dc.b "trailing comma at end of DC directive",$00
	dc.b "branch made short",$00
	dc.b "offset removed",$00
	dc.b "short word addressing used",$00
	dc.b "MOVEQ substituted",$00
	dc.b "quick form used",$00
	dc.b "branch could be short",$00
	dc.b "short branch converted to NOP",$00
	dc.b "base displacement shortened",$00
	dc.b "outer displacement shortened",$00
	dc.b "ADD/SUB converted to LEA",$00
	dc.b "LEA converted to ADDQ/SUBQ",$00
	dc.b ".L converted to .W",$00
	dc.b $00,$02,$02,$02,$04,$00,$FF,$00,$02,$02,$00,$02,$02,$4A,$2E,$02
	dc.b $38,$67,$2C,$48,$A7,$C0,$00,$04,$40,$00,$0C,$10,$3B,$00,$E4,$6B
	dc.b $0A,$48,$80,$D1,$6E,$01,$94,$52,$6E,$01,$92,$30,$17,$04,$40,$00
	dc.b $0C,$32,$2E,$01,$10,$01,$01,$4C,$9F,$00,$03,$66,$00,$FD,$54,$4E
	dc.b $75,$70,$43,$60,$00,$FC,$2E
loc_0_00008842:
	movem.l a3-a5,-(a7)
	movea.l $0172(a6),a2
	jsr loc_0_00000B88.l
	movem.l (a7)+,a3-a5
	rts
loc_0_00008856:
	tst.b app_0238(a6)
	bne.w loc_0_00008950
	bsr.b loc_0_00008842
	bne.b loc_0_00008880
	tst.b $0134(a6)
	bne.b loc_0_0000887C
	cmpi.b #13,$000D(a1)
	beq.b loc_0_0000887C
	tst.w $009C(a1)
	bne.w loc_0_00008A02
	bra.w loc_0_00008958
loc_0_0000887C:
	moveq.l #0,d0
	rts
loc_0_00008880:
	moveq.l #0,d4
	moveq.l #11,d3
	moveq.l #89,d0
	add.l d0,d0
	jsr loc_0_00000D20.l
	clr.l $0098(a1)
	clr.l $00AA(a1)
	clr.l $00AE(a1)
	move.l a1,-(a7)
	bsr.w loc_0_0000AE7C
	movea.l (a7)+,a1
	bne.w loc_0_000089FE
	tst.l d1
	bpl.b loc_0_000088C4
	cmp.l #$FFFFFFFF,d1
	beq.b loc_0_000088C4
	move.b #$D,$000D(a1)
	neg.l d1
	jsr loc_0_0000FCD6.l
	moveq.l #0,d0
	rts
loc_0_000088C4:
	move.l d4,$0098(a1)
	move.l $017E(a6),$0010(a1)
	move.l a1,$017E(a6)
	tst.l d1
	bmi.b loc_0_00008914
	addq.l #3,d1
	bclr #0,d1
	move.l #$1200,d2
	bsr.w loc_0_0000B068
	move.l a1,-(a7)
	move.l d1,d3
	bsr.w loc_0_000090BA
	movea.l (a7)+,a1
	move.l a0,$0008(a1)
	move.l d3,$00A6(a1)
	adda.l d3,a0
	move.l a0,$00A2(a1)
	move.l a0,$009E(a1)
	move.w app_0218(a6),$009C(a1)
	clr.w app_0218(a6)
	st.b $000E(a1)
	bra.w loc_0_000089BA
loc_0_00008914:
	move.b #$C,$000D(a1)
	movea.l $01A2(a6),a0
	move.l $0008(a0),$0008(a1)
	move.l $0008(a0),$009E(a1)
	movea.l $000C(a0),a2
	cmpi.b #10,-$0001(a2)
	beq.b loc_0_0000893A
	move.b #$A,(a2)+
loc_0_0000893A:
	move.l a2,$00A2(a1)
	move.w app_0218(a6),$009C(a1)
	clr.w app_0218(a6)
	clr.b $000E(a1)
	moveq.l #0,d0
	rts
loc_0_00008950:
	bsr.w loc_0_00008842
	bne.w loc_0_00008A02
loc_0_00008958:
	move.b $000E(a1),d0
	cmp.b #$FE,d0
	beq.b loc_0_0000899A
	cmpi.b #13,$000D(a1)
	beq.b loc_0_0000899A
	move.l $017E(a6),$0010(a1)
	move.l a1,$017E(a6)
	tst.b d0
	beq.b loc_0_0000899C
	move.l a1,-(a7)
	bsr.w loc_0_0000AE7C
	movea.l (a7)+,a1
	bne.w loc_0_000089FE
	move.l d4,$0098(a1)
	move.l $0008(a1),$009E(a1)
	move.w app_0218(a6),$009C(a1)
	clr.w app_0218(a6)
	bra.b loc_0_000089BA
loc_0_0000899A:
	rts
loc_0_0000899C:
	move.l $0008(a1),$009E(a1)
	move.w app_0218(a6),$009C(a1)
	clr.w app_0218(a6)
	moveq.l #0,d0
	rts
loc_0_000089B0:
	move.l $0008(a1),$009E(a1)
	movea.l a2,a0
	bra.b loc_0_000089C6
loc_0_000089BA:
	movea.l $0008(a1),a0
	move.l a0,$009E(a1)
	move.l $00A6(a1),d1
loc_0_000089C6:
	move.l $0098(a1),d2
	movem.l d1/a0-a1,-(a7)
	bsr.w loc_0_0000AFC2
	movem.l (a7)+,d2/a0-a1
	bne.b loc_0_000089FA
	lea.l $0(a0,d1.l),a2
	cmp.l d1,d2
	beq.b loc_0_000089EE
	clr.b (a2)
	cmpi.b #10,-$0001(a2)
	beq.b loc_0_000089EE
	move.b #$A,(a2)+
loc_0_000089EE:
	move.l a2,$00A2(a1)
	addq.b #1,$000E(a1)
	moveq.l #0,d0
	rts
loc_0_000089FA:
	moveq.l #25,d0
	rts
loc_0_000089FE:
	moveq.l #26,d0
	rts
loc_0_00008A02:
	moveq.l #28,d0
	rts
loc_0_00008A06:
	moveq.l #11,d3
	lea.l loc_0_00008A0E(pc),a2
	bra.b loc_0_00008A26
loc_0_00008A0E:
	move.l $0098(a0),d2
	beq.b loc_0_00008A24
	clr.l $0098(a0)
	movem.l a0/a2,-(a7)
	bsr.w loc_0_0000AFB8
	movem.l (a7)+,a0/a2
loc_0_00008A24:
	rts
loc_0_00008A26:
	move.l $0172(a6),d0
	beq.b loc_0_00008A58
	movea.l d0,a0
	move.l (a0),d0
	beq.b loc_0_00008A58
	movea.l d0,a0
loc_0_00008A34:
	tst.l (a0)
	beq.b loc_0_00008A40
	move.l a0,-(a7)
	movea.l (a0),a0
	bsr.b loc_0_00008A34
	movea.l (a7)+,a0
loc_0_00008A40:
	tst.b d3
	beq.b loc_0_00008A4A
	cmp.b $000D(a0),d3
	bne.b loc_0_00008A4C
loc_0_00008A4A:
	jsr (a2)
loc_0_00008A4C:
	tst.l $0004(a0)
	beq.b loc_0_00008A58
	movea.l $0004(a0),a0
	bra.b loc_0_00008A34
loc_0_00008A58:
	rts
loc_0_00008A5A:
	lea.l app_04F4(a6),a0
	move.l d4,-(a7)
	bsr.w loc_0_00008842
	move.l (a7)+,d4
	move.l a1,app_057A(a6)
	moveq.l #0,d3
	lea.l loc_0_00008A72(pc),a2
	bra.b loc_0_00008A26
loc_0_00008A72:
	dc.b $10,$28,$00,$0D,$B0,$3C,$00,$0B,$67,$06,$B0,$3C,$00,$0C,$66,$56
	dc.b $2F,$08,$41,$E8,$00,$AA,$20,$10,$67,$4A,$20,$50,$22,$28,$00,$18
	dc.b $20,$01,$02,$00,$00,$03,$67,$06,$02,$01,$00,$FC,$58,$81,$21,$41
	dc.b $00,$18,$48,$E7,$00,$A0,$61,$00,$06,$10,$22,$48,$4C,$DF,$05,$00
	dc.b $21,$49,$00,$0E,$21,$49,$00,$14,$21,$7C,$FF,$FF,$FF,$FF,$00,$06
	dc.b $42,$A8,$00,$0A,$41,$D0,$0C,$6E,$00,$03,$02,$1C,$66,$B8,$52,$AE
	dc.b $02,$00,$60,$B2,$20,$5F,$4E,$75
loc_0_00008ADA:
	move.l (a1),d1
	bpl.b loc_0_00008AE2
	move.l d0,(a1)
	bra.b loc_0_00008AE6
loc_0_00008AE2:
	move.l d0,(a1)
	sub.l d1,d0
loc_0_00008AE6:
	beq.b loc_0_00008B08
	move.l $0018(a0),d1
	addq.l #1,d1
	cmp.l #$80,d0
	bcs.b loc_0_00008B02
	addq.l #2,d1
	cmp.l #$8000,d0
	bcs.b loc_0_00008B02
	addq.l #4,d1
loc_0_00008B02:
	move.l d1,$0018(a0)
	rts
loc_0_00008B08:
	move.l $0018(a0),d1
	addq.l #7,d1
	bra.b loc_0_00008B02
loc_0_00008B10:
	move.l (a1),d1
	bpl.b loc_0_00008B18
	move.l d0,(a1)
	bra.b loc_0_00008B1C
loc_0_00008B18:
	move.l d0,(a1)
	sub.l d1,d0
loc_0_00008B1C:
	movea.l $0014(a0),a1
	beq.b loc_0_00008B48
	cmp.w #$80,d0
	bcs.b loc_0_00008B44
	clr.b (a1)+
	cmp.l #$8000,d0
	bcs.b loc_0_00008B3E
loc_0_00008B32:
	clr.b (a1)+
	clr.b (a1)+
	swap.w d0
	bsr.w loc_0_00008B3E
	swap.w d0
loc_0_00008B3E:
	move.w d0,d1
	lsr.w #8,d1
	move.b d1,(a1)+
loc_0_00008B44:
	move.b d0,(a1)+
	rts
loc_0_00008B48:
	clr.b (a1)+
	bra.b loc_0_00008B32
loc_0_00008B4C:
	dc.b $24,$48,$0C,$6E,$00,$03,$02,$1C,$66,$14,$61,$00,$15,$9E,$48,$E7
	dc.b $20,$E0,$61,$00,$24,$F4,$4C,$DF,$07,$04,$25,$40,$00,$1C,$22,$3C
	dc.b $00,$00,$03,$F1,$61,$00,$15,$7C,$61,$5E,$61,$00,$15,$76,$72,$00
	dc.b $61,$00,$15,$70,$22,$3C,$4C,$49,$4E,$45,$4A,$2E,$01,$2A,$67,$06
	dc.b $22,$3C,$48,$43,$4C,$4E,$61,$00,$15,$5A,$70,$00,$61,$00,$14,$FE
	dc.b $52,$29,$00,$16,$4A,$2E,$01,$2A,$67,$0A,$72,$00,$32,$2A,$00,$12
	dc.b $61,$00,$15,$40,$61,$00,$15,$44,$20,$6A,$00,$0E,$22,$2A,$00,$18
	dc.b $48,$E7,$00,$60,$61,$00,$F8,$60,$4C,$DF,$06,$00,$61,$00,$15,$46
	dc.b $20,$4A,$45,$FA,$FF,$7C,$4E,$75
loc_0_00008BD4:
	moveq.l #0,d1
	move.b $0016(a1),d1
	subq.b #1,d1
	move.b d1,$0016(a1)
	move.l d1,d0
	andi.b #3,d0
	beq.b loc_0_00008BEE
	andi.b #252,d1
	addq.l #4,d1
loc_0_00008BEE:
	add.l $0018(a2),d1
	lsr.l #2,d1
	addq.l #3,d1
	tst.b $012A(a6)
	beq.b loc_0_00008BFE
	addq.l #1,d1
loc_0_00008BFE:
	rts
loc_0_00008C00:
	movea.l a0,a2
	bsr.b loc_0_00008BD4
	move.l d1,-(a7)
	addq.l #2,d1
	add.l d1,d1
	add.l d1,d1
	moveq.l #0,d0
	bsr.w loc_0_0000AE02
	move.l (a7),d1
	move.l a4,(a7)
	movea.l a0,a4
	move.l #$3F1,(a4)+
	move.l d1,(a4)+
	tst.b $012A(a6)
	beq.b loc_0_00008C64
	move.l $0008(a3),(a4)+
	move.l #$48434C4E,(a4)+
	bsr.w loc_0_00009D46
	addq.b #1,$0016(a1)
	moveq.l #0,d1
	move.w $0012(a2),d1
	move.l d1,(a4)+
	movea.l $000E(a2),a0
	move.l $0018(a2),d1
	lsr.l #2,d1
	subq.l #1,d1
loc_0_00008C4C:
	move.l (a0)+,(a4)+
	dbf.w d1,loc_0_00008C4C
	subi.l #65536,d1
	bcc.b loc_0_00008C4C
loc_0_00008C5A:
	movea.l (a7)+,a4
	movea.l a2,a0
	lea.l loc_0_00008C00(pc),a2
	rts
loc_0_00008C64:
	clr.l (a4)+
	move.l #$4C494E45,(a4)+
	bsr.w loc_0_00009D46
	addq.b #1,$0016(a1)
	movea.l $000E(a2),a0
	move.l $0018(a2),d1
	lsr.l #3,d1
	subq.l #1,d1
	move.l $0008(a3),d2
loc_0_00008C84:
	move.l (a0)+,(a4)+
	move.l (a0)+,d0
	add.l d2,d0
	move.l d0,(a4)+
	dbf.w d1,loc_0_00008C84
	subi.l #65536,d1
	bcc.b loc_0_00008C84
	bra.b loc_0_00008C5A
loc_0_00008C9A:
	movea.l app_057A(a6),a0
	bsr.w loc_0_00008CDC
	movea.l $0172(a6),a0
	movea.l (a0),a0
loc_0_00008CA8:
	tst.l (a0)
	beq.b loc_0_00008CB4
	move.l a0,-(a7)
	movea.l (a0),a0
	bsr.b loc_0_00008CA8
	movea.l (a7)+,a0
loc_0_00008CB4:
	move.b $000D(a0),d0
	cmp.b #$B,d0
	beq.b loc_0_00008CC4
	cmp.b #$C,d0
	bne.b loc_0_00008CCE
loc_0_00008CC4:
	cmpa.l app_057A(a6),a0
	beq.b loc_0_00008CCE
	bsr.w loc_0_00008CDC
loc_0_00008CCE:
	tst.l $0004(a0)
	beq.b loc_0_00008CDA
	movea.l $0004(a0),a0
	bra.b loc_0_00008CA8
loc_0_00008CDA:
	rts
loc_0_00008CDC:
	movea.l a0,a1
	move.l $00AA(a1),d0
loc_0_00008CE2:
	beq.b loc_0_00008CF2
	movea.l d0,a0
	cmp.b $0004(a0),d6
	beq.b loc_0_00008CF0
	move.l (a0),d0
	bra.b loc_0_00008CE2
loc_0_00008CF0:
	jsr (a2)
loc_0_00008CF2:
	movea.l a1,a0
	rts
loc_0_00008CF6:
	tst.l $0010(a1)
	beq.b loc_0_00008D1A
	movea.l $0010(a1),a1
loc_0_00008D00:
	tst.l (a1)
	beq.b loc_0_00008D0C
	move.l a1,-(a7)
	movea.l (a1),a1
	bsr.b loc_0_00008D00
	movea.l (a7)+,a1
loc_0_00008D0C:
	jsr (a2)
	tst.l $0004(a1)
	beq.b loc_0_00008D1A
	movea.l $0004(a1),a1
	bra.b loc_0_00008D00
loc_0_00008D1A:
	rts
loc_0_00008D1C:
	move.l a3,-(a7)
	movea.l a2,a3
	lea.l loc_0_00008D36(pc),a2
	bsr.b loc_0_00008CF6
	movea.l $016A(a6),a1
	tst.l (a1)
	beq.b loc_0_00008D32
	movea.l (a1),a1
	bsr.b loc_0_00008D00
loc_0_00008D32:
	movea.l (a7)+,a3
	rts
loc_0_00008D36:
	btst.b #5,$000C(a1)
	beq.b loc_0_00008D46
	cmp.b $000E(a1),d6
	bne.b loc_0_00008D46
	jsr (a3)
loc_0_00008D46:
	rts
loc_0_00008D48:
	tst.l $0010(a1)
	beq.b loc_0_00008D6C
	movea.l $0010(a1),a1
loc_0_00008D52:
	tst.l (a1)
	beq.b loc_0_00008D5E
	move.l a1,-(a7)
	movea.l (a1),a1
	bsr.b loc_0_00008D52
	movea.l (a7)+,a1
loc_0_00008D5E:
	bsr.b loc_0_00008D6E
	tst.l $0004(a1)
	beq.b loc_0_00008D6C
	movea.l $0004(a1),a1
	bra.b loc_0_00008D52
loc_0_00008D6C:
	rts
loc_0_00008D6E:
	btst.b #4,$000C(a1)
	beq.b loc_0_00008D80
	btst.b #2,$000C(a1)
	bne.b loc_0_00008D80
	jsr (a2)
loc_0_00008D80:
	rts
loc_0_00008D82:
	tst.b app_0238(a6)
	bne.b loc_0_00008DA0
	move.l #$196,d1
	bsr.w loc_0_000090BA
	move.l a0,app_0948(a6)
	move.l a0,app_094C(a6)
	clr.l (a0)+
	clr.w (a0)
	rts
loc_0_00008DA0:
	movea.l app_094C(a6),a0
	move.w $0004(a0),d0
	lea.l $6(a0,d0.w),a0
	move.l a0,app_0950(a6)
	movea.l app_0948(a6),a0
	move.l a0,app_094C(a6)
	moveq.l #-1,d0
	tst.w $0004(a0)
	beq.b loc_0_00008DC8
	clr.w $0004(a0)
	move.l $0006(a0),d0
loc_0_00008DC8:
	move.l d0,app_0944(a6)
	rts
	dc.b $20,$0D,$90,$AE,$02,$4C,$D0,$AE,$02,$24,$4A,$2E,$02,$38,$66,$44
	dc.b $2F,$00,$20,$6E,$09,$4C,$58,$88,$30,$18,$B0,$7C,$01,$90,$67,$10
	dc.b $21,$9F,$00,$00,$21,$82,$00,$04,$50,$40,$31,$00,$70,$00,$4E,$75
	dc.b $48,$E7,$60,$60,$22,$3C,$00,$00,$01,$96,$61,$00,$02,$B0,$22,$6E
	dc.b $09,$4C,$22,$88,$2D,$48,$09,$4C,$42,$98,$42,$58,$70,$00,$4C,$DF
	dc.b $06,$06,$60,$CC,$B0,$AE,$09,$44,$66,$32,$20,$6E,$09,$4C,$58,$88
	dc.b $30,$18,$B4,$B0,$00,$04,$67,$0A,$3F,$00,$70,$41,$61,$00,$F6,$4A
	dc.b $30,$1F,$50,$40,$B0,$7C,$01,$90,$67,$14,$31,$40,$FF,$FE,$D0,$C0
	dc.b $B1,$EE,$09,$50,$67,$1C,$2D,$50,$09,$44,$70,$00,$4E,$75,$20,$6E
	dc.b $09,$4C,$4A,$90,$67,$0C,$20,$50,$2D,$48,$09,$4C,$5C,$48,$70,$00
	dc.b $60,$D8,$70,$FF,$2D,$40,$09,$44,$70,$00,$4E,$75
loc_0_00008E7A:
	lea.l loc_0_000093FE(pc),a0
	tst.w d0
loc_0_00008E80:
	beq.w loc_0_00009292
loc_0_00008E84:
	tst.b (a0)+
	bne.b loc_0_00008E84
	subq.w #1,d0
	bra.b loc_0_00008E80
loc_0_00008E8C:
	moveq.l #10,d1
	bra.w loc_0_00009288
loc_0_00008E92:
	bsr.w loc_0_00008E96
loc_0_00008E96:
	moveq.l #32,d1
loc_0_00008E98:
	movem.l d0-d2/a0-a2,-(a7)
	bsr.w loc_0_00009288
	movem.l (a7)+,d0-d2/a0-a2
	rts
loc_0_00008EA6:
	move.w d1,-(a7)
	swap.w d1
	bsr.b loc_0_00008EAE
	move.w (a7)+,d1
loc_0_00008EAE:
	move.w d1,-(a7)
	lsr.w #8,d1
	bsr.b loc_0_00008EB6
	move.w (a7)+,d1
loc_0_00008EB6:
	move.w d1,-(a7)
	lsr.w #4,d1
	bsr.b loc_0_00008EBE
	move.w (a7)+,d1
loc_0_00008EBE:
	andi.w #15,d1
	move.b loc_0_00008EC8(pc,d1.w),d1
	bra.b loc_0_00008E98
loc_0_00008EC8:
	dc.b $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46	; lookup_table
loc_0_00008ED8:
	moveq.l #6,d3
	moveq.l #0,d2
loc_0_00008EDC:
	rol.l #4,d1
	move.l d1,-(a7)
	andi.w #15,d1
	bne.b loc_0_00008EEA
	tst.b d2
	beq.b loc_0_00008EF2
loc_0_00008EEA:
	st.b d2
	move.b loc_0_00008EC8(pc,d1.w),d1
	jsr (a2)
loc_0_00008EF2:
	move.l (a7)+,d1
	dbf.w d3,loc_0_00008EDC
	rol.l #4,d1
	andi.w #15,d1
	move.b loc_0_00008EC8(pc,d1.w),d1
	jmp (a2)
loc_0_00008F04:
	lea.l loc_0_00008E98(pc),a2
loc_0_00008F08:
	lea.l loc_0_00008F3C(pc),a0
	moveq.l #1,d2
	moveq.l #8,d0
loc_0_00008F10:
	moveq.l #0,d3
	cmp.l (a0)+,d1
	bcs.b loc_0_00008F22
	sub.l -(a0),d1
loc_0_00008F18:
	addq.b #1,d3
	sub.l (a0),d1
	bcc.b loc_0_00008F18
	add.l (a0)+,d1
	bra.b loc_0_00008F26
loc_0_00008F22:
	tst.b d2
	bpl.b loc_0_00008F32
loc_0_00008F26:
	st.b d2
	addi.b #48,d3
	exg d3,d1
	jsr (a2)
	exg d3,d1
loc_0_00008F32:
	dbf.w d0,loc_0_00008F10
	addi.b #48,d1
	jmp (a2)
loc_0_00008F3C:
	dc.b $3B,$9A,$CA,$00,$05,$F5,$E1,$00,$00,$98,$96,$80,$00,$0F,$42,$40
	dc.b $00,$01,$86,$A0,$00,$00,$27,$10,$00,$00,$03,$E8,$00,$00,$00,$64
	dc.b $00,$00,$00,$0A
loc_0_00008F60:
	moveq.l #20,d0
	bsr.w loc_0_00008E7A
	movea.l $016A(a6),a2
	lea.l loc_0_00008F90(pc),a4
	bsr.w loc_0_00008FD2
	moveq.l #9,d3
	lea.l loc_0_00008F98(pc),a2
	lea.l loc_0_00008F80(pc),a4
	bra.w loc_0_00008A26
loc_0_00008F80:
	dc.b $0C,$2B,$00,$02,$00,$0D,$67,$08,$10,$2B,$00,$0E,$60,$00,$07,$F8
loc_0_00008F90:
	bsr.w loc_0_00008E96
	bra.w loc_0_00008E92
loc_0_00008F98:
	dc.b $48,$E7,$10,$A0,$2F,$08,$70,$15,$61,$00,$FE,$D8,$20,$57,$41,$E8
	dc.b $00,$16,$14,$18,$12,$18,$61,$00,$FE,$E8,$53,$02,$6E,$F6,$61,$00
	dc.b $FE,$D4,$61,$00,$FE,$D0,$20,$5F,$45,$E8,$00,$10,$61,$0C,$4C,$DF
	dc.b $05,$08,$4E,$75
loc_0_00008FCC:
	jmp loc_0_000006A4.l
loc_0_00008FD2:
	move.l a2,d0
	beq.b loc_0_0000904C
	move.l (a2),d0
	beq.b loc_0_0000904C
	movea.l d0,a2
	suba.l a3,a3
	lea.l app_05BE(a6),a0
	moveq.l #127,d0
	move.b d0,(a0)+
loc_0_00008FE6:
	st.b (a0)+
	dbf.w d0,loc_0_00008FE6
loc_0_00008FEC:
	tst.b app_0115(a6)
	bgt.b loc_0_00008FCC
	lea.l app_05A8(a6),a3
	move.b $0017(a3),d3
	bsr.b loc_0_0000904E
	lea.l app_05A8(a6),a0
	cmpa.l a3,a0
	beq.b loc_0_0000904C
	bset.b #0,$000C(a3)
	btst.b #4,$000C(a3)
	bne.b loc_0_00008FEC
	move.l $0008(a3),d1
	bsr.w loc_0_00008EA6
	bsr.w loc_0_00008E92
	jsr (a4)
	moveq.l #0,d1
	move.b $000D(a3),d1
	lea.l loc_0_0000909A(pc),a0
	move.b $0(a0,d1.w),d1
	bsr.w loc_0_00008E98
	bsr.w loc_0_00008E92
	lea.l $0016(a3),a0
	move.b (a0)+,d4
loc_0_0000903C:
	move.b (a0)+,d1
	bsr.w loc_0_00008E98
	subq.b #1,d4
	bne.b loc_0_0000903C
	bsr.w loc_0_00008E8C
	bra.b loc_0_00008FEC
loc_0_0000904C:
	rts
loc_0_0000904E:
	tst.l (a2)
	beq.b loc_0_0000905A
	move.l a2,-(a7)
	movea.l (a2),a2
	bsr.b loc_0_0000904E
	movea.l (a7)+,a2
loc_0_0000905A:
	btst.b #0,$000C(a2)
	bne.b loc_0_00009088
	cmp.b $0017(a2),d3
	bcs.b loc_0_00009088
	lea.l $0016(a3),a0
	lea.l $0016(a2),a1
	move.b (a0)+,d0
	move.b (a1)+,d1
loc_0_00009074:
	cmpm.b (a1)+,(a0)+
	bcs.b loc_0_00009088
	bne.b loc_0_00009082
	subq.b #1,d0
	beq.b loc_0_00009088
	subq.b #1,d1
	bne.b loc_0_00009074
loc_0_00009082:
	movea.l a2,a3
	move.b $0017(a3),d3
loc_0_00009088:
	tst.l $0004(a2)
	beq.b loc_0_00009098
	move.l a2,-(a7)
	movea.l $0004(a2),a2
	bsr.b loc_0_0000904E
	movea.l (a7)+,a2
loc_0_00009098:
	rts
loc_0_0000909A:
	dc.b $3F,$52,$41,$3F,$72,$6C,$3F,$3F,$3F,$3F,$3F,$3F,$4F,$00
loc_0_000090A8:
	move.l #$2800,d1
	move.w d1,$0148(a6)
	bsr.b loc_0_000090BA
	move.l a0,$013A(a6)
	rts
loc_0_000090BA:
	addq.l #4,d1
	bsr.w loc_0_0000AE42
	beq.b loc_0_000090EC
	move.l $0136(a6),(a0)
	move.l a0,$0136(a6)
	addq.w #4,a0
	rts
	dc.b $59,$48,$43,$EE,$01,$36,$20,$11,$67,$0E,$B1,$C0,$67,$04,$22,$40
	dc.b $60,$F4,$22,$90,$60,$00,$1D,$82,$70,$69,$60,$00,$F3,$84
loc_0_000090EC:
	moveq.l #2,d0
	bra.w loc_0_0000846E
loc_0_000090F2:
	movea.l $0136(a6),a0
	bra.b loc_0_00009100
loc_0_000090F8:
	move.l (a0),-(a7)	; KNOWN: arg +4 memoryBlock APTR
	bsr.w loc_0_0000AE66
	movea.l (a7)+,a0
loc_0_00009100:
	move.l a0,d0
	bne.b loc_0_000090F8
	rts
loc_0_00009106:
	sf.b app_0954(a6)
	sf.b app_0955(a6)
	clr.l app_0956(a6)
	lea.l app_095A(a6),a0
	lea.l app_0B5A(a6),a1
	move.l a0,(a1)
	move.l a1,app_0B5E(a6)
	move.w #$84,app_0B62(a6)
	move.w #$3C,app_0B64(a6)
	clr.w app_0B66(a6)
	move.w #$FFFF,app_0B68(a6)
	clr.w app_0B6A(a6)
	clr.b app_0B82(a6)
	clr.b app_0BD3(a6)
	st.b app_0C24(a6)
	move.w #$8,app_0B6C(a6)
	lea.l app_0B6E(a6),a3
	bsr.w loc_0_0000AD0C
	clr.b (a3)
	rts
loc_0_00009158:
	tst.l app_0956(a6)
	beq.b loc_0_00009168
	bsr.w loc_0_0000AB56
	bsr.w loc_0_0000919E
	bsr.b loc_0_0000916A
loc_0_00009168:
	rts
loc_0_0000916A:
	tst.l app_0956(a6)
	beq.b loc_0_00009168
	move.l app_0956(a6),d3
	clr.l app_0956(a6)
	bra.w close_non_stdout_handle
loc_0_0000917C:
	movea.l app_0B5A(a6),a0
	cmpa.l app_0B5E(a6),a0
	beq.b loc_0_0000918E
	move.b d1,(a0)+
	move.l a0,app_0B5A(a6)
	rts
loc_0_0000918E:
	move.w d1,-(a7)
	bsr.b loc_0_0000919E
	bne.b loc_0_00009198
	move.w (a7)+,d1
	bra.b loc_0_0000917C
loc_0_00009198:
	moveq.l #74,d0
	bra.w loc_0_0000846E
loc_0_0000919E:
	move.l d3,-(a7)
	move.l app_0956(a6),d3
	lea.l app_095A(a6),a0
	move.l app_0B5A(a6),d1
	sub.l a0,d1
	beq.b loc_0_000091BC
	lea.l app_095A(a6),a1
	move.l a1,app_0B5A(a6)
	bsr.w write_output_block
loc_0_000091BC:
	movem.l (a7)+,d3
	rts
loc_0_000091C2:
	btst.b #0,app_0C24(a6)
	bne.b loc_0_000091CC
	rts
loc_0_000091CC:
	addq.w #1,app_0B6A(a6)
	moveq.l #16,d0
	bsr.w loc_0_00008E7A
	lea.l app_0B6E(a6),a0
	bsr.w loc_0_00009292
	moveq.l #15,d0
	bsr.w loc_0_00008E7A
	moveq.l #0,d1
	move.w app_0B6A(a6),d1
	move.l d3,-(a7)
	bsr.w loc_0_00008F04
	move.l (a7)+,d3
	bsr.w loc_0_00008E8C
	lea.l app_0B82(a6),a0
	tst.b (a0)
	beq.b loc_0_00009204
	bsr.w loc_0_00009292
	bra.b loc_0_00009224
loc_0_00009204:
	tst.l $017E(a6)
	beq.b loc_0_00009224
	movea.l $017E(a6),a1
	moveq.l #0,d2
	move.b $0016(a1),d2
	subq.b #2,d2
	lea.l $0017(a1),a1
loc_0_0000921A:
	move.b (a1)+,d1
	bsr.w loc_0_00008E98
	dbf.w d2,loc_0_0000921A
loc_0_00009224:
	bsr.w loc_0_00008E8C
	lea.l app_0BD3(a6),a0
	bsr.w loc_0_00009292
	bsr.w loc_0_00008E8C
	bra.w loc_0_00008E8C
loc_0_00009238:
	tst.w app_0B68(a6)
	bpl.b loc_0_0000924A
	clr.w app_0B68(a6)
	move.w d1,-(a7)
	bsr.w loc_0_000091C2
	move.w (a7)+,d1
loc_0_0000924A:
	cmp.b #$A,d1
	bne.b loc_0_0000926C
loc_0_00009250:
	clr.w app_0B66(a6)
	move.w app_0B68(a6),d0
	addq.w #1,app_0B68(a6)
	cmp.w app_0B64(a6),d0
	beq.w loc_0_0000AB56
	moveq.l #10,d1
	bsr.w loc_0_0000917C
	rts
loc_0_0000926C:
	move.w app_0B66(a6),d0
	cmp.w app_0B62(a6),d0
	blt.b loc_0_0000927E
	move.w d1,-(a7)
	bsr.b loc_0_00009250
	move.w (a7)+,d1
	bra.b loc_0_00009238
loc_0_0000927E:
	bsr.w loc_0_0000917C
	addq.w #1,app_0B66(a6)
	rts
loc_0_00009288:
	tst.b app_0955(a6)
	bne.b loc_0_00009238
	bra.w buffer_output_char
loc_0_00009292:
	move.b (a0)+,d1
	beq.b loc_0_0000929E
	move.l a0,-(a7)
	bsr.b loc_0_00009288
	movea.l (a7)+,a0
	bra.b loc_0_00009292
loc_0_0000929E:
	rts
loc_0_000092A0:
	movem.l d7/a3,-(a7)
	move.b app_0C24(a6),d7
	add.b d7,d7
	bcc.b loc_0_000092E4
	move.w app_0218(a6),d2
	cmp.w #$2710,d2
	bcc.b loc_0_000092D8
	bsr.w loc_0_00008E96
	cmp.w #$3E8,d2
	bcc.b loc_0_000092D8
	bsr.w loc_0_00008E96
	cmp.w #$64,d2
	bcc.b loc_0_000092D8
	bsr.w loc_0_00008E96
	cmp.w #$A,d2
	bcc.b loc_0_000092D8
	bsr.w loc_0_00008E96
loc_0_000092D8:
	moveq.l #0,d1
	move.w d2,d1
	bsr.w loc_0_00008F04
	bsr.w loc_0_00008E96
loc_0_000092E4:
	move.l $0182(a6),d4
	add.b d7,d7
	bcc.b loc_0_0000932E
	move.b $0146(a6),d0
	move.b app_083B(a6),d1
	beq.b loc_0_00009318
	cmp.b #$FF,d1
	beq.b loc_0_00009312
	bsr.w loc_0_00008E92
	move.b app_083B(a6),d1
	bsr.b loc_0_00009288
loc_0_00009306:
	move.l app_083C(a6),d1
	bsr.w loc_0_00008EA6
	moveq.l #0,d4
	bra.b loc_0_0000932E
loc_0_00009312:
	bsr.w loc_0_00009780
	bra.b loc_0_00009306
loc_0_00009318:
	bsr.w loc_0_00009780
	move.l $0182(a6),d4
	movea.l app_0250(a6),a3
	move.l app_023C(a6),d1
	sub.l d4,d1
	bsr.w loc_0_00008EA6
loc_0_0000932E:
	moveq.l #32,d1
	tst.b app_0101(a6)
	beq.b loc_0_0000933E
	tst.b app_0118(a6)
	bne.b loc_0_0000933E
	moveq.l #43,d1
loc_0_0000933E:
	bsr.w loc_0_00009288
	add.b d7,d7
	bcc.b loc_0_0000936C
	moveq.l #5,d3
	cmpi.w #81,app_0B62(a6)
	bcs.b loc_0_00009352
	moveq.l #9,d3
loc_0_00009352:
	tst.l d4
loc_0_00009354:
	beq.b loc_0_00009364
	move.b (a3)+,d1
	bsr.w loc_0_00008EB6
	subq.l #1,d4
	dbf.w d3,loc_0_00009354
	bra.b loc_0_0000936C
loc_0_00009364:
	bsr.w loc_0_00008E92
	dbf.w d3,loc_0_00009364
loc_0_0000936C:
	bsr.w loc_0_00008E96
	movea.l app_0240(a6),a3
	moveq.l #0,d2
	moveq.l #0,d3
	tst.b app_010D(a6)
	beq.b loc_0_00009388
	tst.b app_0955(a6)
	bne.b loc_0_00009388
	move.l $0154(a6),d3
loc_0_00009388:
	move.b (a3)+,d1
	cmp.l a3,d3
	bne.b loc_0_000093C4
	movem.l d0-d2/a0-a2,-(a7)
	cmp.b #$A,d1
	beq.b loc_0_0000939E
	cmp.b #$9,d1
	bne.b loc_0_000093A0
loc_0_0000939E:
	moveq.l #32,d1
loc_0_000093A0:
	tst.b $0128(a6)
	bne.b loc_0_000093AC
	bsr.w buffer_highlighted_char
	bra.b loc_0_000093B0
loc_0_000093AC:
	bsr.w buffer_output_char
loc_0_000093B0:
	movem.l (a7)+,d0-d2/a0-a2
	cmp.b #$A,d1
	beq.b loc_0_000093F4
	cmp.b #$9,d1
	beq.b loc_0_000093C4
	addq.w #1,d2
	bra.b loc_0_00009388
loc_0_000093C4:
	cmp.b #$A,d1
	beq.b loc_0_000093F4
	cmp.b #$9,d1
	bne.b loc_0_000093EC
	moveq.l #0,d0
	move.w d2,d0
	divu.w app_0B6C(a6),d0
	swap.w d0
	sub.w app_0B6C(a6),d0
	neg.w d0
loc_0_000093E0:
	bsr.w loc_0_00008E96
	addq.w #1,d2
	subq.w #1,d0
	bne.b loc_0_000093E0
	bra.b loc_0_00009388
loc_0_000093EC:
	addq.w #1,d2
	bsr.w loc_0_00008E98
	bra.b loc_0_00009388
loc_0_000093F4:
	bsr.w loc_0_00009288
	movem.l (a7)+,d7/a3
	rts
loc_0_000093FE:
	dc.b $47,$65,$6E,$41,$6D,$20,$4D,$61,$63,$72,$6F,$20,$41,$73,$73,$65
	dc.b $6D,$62,$6C,$65,$72,$20,$43,$6F,$70,$79,$72,$69,$67,$68,$74,$20
	dc.b $A9,$20,$48,$69,$53,$6F,$66,$74,$20,$31,$39,$38,$35,$2D,$31,$39
	dc.b $39,$37,$0A,$41,$6C,$6C,$20,$52,$69,$67,$68,$74,$73,$20,$52,$65
	dc.b $73,$65,$72,$76,$65,$64,$20,$2D,$20,$76,$65,$72,$73,$69,$6F,$6E
	dc.b $20,$33,$2E,$31,$38,$0A,$0A,$00,$50,$61,$73,$73,$20,$31,$0A,$00
	dc.b $50,$61,$73,$73,$20,$32,$0A,$00,$20,$65,$72,$72,$6F,$72,$73,$20
	dc.b $66,$6F,$75,$6E,$64,$0A,$00,$20,$65,$72,$72,$6F,$72,$20,$66,$6F
	dc.b $75,$6E,$64,$0A,$00,$20,$6C,$69,$6E,$65,$73,$20,$61,$73,$73,$65
	dc.b $6D,$62,$6C,$65,$64,$20,$69,$6E,$74,$6F,$20,$00,$45,$72,$72,$6F
	dc.b $72,$3A,$20,$00,$4C,$6F,$63,$61,$6C,$73,$3A,$0A,$00
	dc.b "Warning: ",$00
	dc.b $20,$61,$74,$20,$6C,$69,$6E,$65,$20,$00
	dc.b "Could not open file ",$00
	dc.b $20,$69,$6E,$20,$66,$69,$6C,$65,$20,$00,$20,$62,$79,$74,$65,$73
	dc.b $2C,$20,$00,$20,$6F,$70,$74,$69,$6D,$69,$73,$61,$74,$69,$6F,$6E
	dc.b $73,$20,$73,$61,$76,$69,$6E,$67,$20,$00,$20,$62,$79,$74,$65,$73
	dc.b $0A,$00,$20,$20,$50,$61,$67,$65,$20,$00
	dc.b "HiSoft GenAm 680x0 Macro Assembler v3.18   ",$00
	dc.b $20,$72,$65,$6C,$6F,$63,$61,$74,$61,$62,$6C,$65,$00,$20,$70,$6F
	dc.b $73,$69,$74,$69,$6F,$6E,$2D,$69,$6E,$64,$65,$70,$65,$6E,$64,$65
	dc.b $6E,$74,$00,$20,$63,$6F,$64,$65,$0A,$00,$0A,$09,$47,$4C,$4F,$42
	dc.b $41,$4C,$20,$53,$59,$4D,$42,$4F,$4C,$53,$0A,$0A,$00,$0A,$09,$4D
	dc.b $4F,$44,$55,$4C,$45,$20,$00,$20,$61,$62,$73,$6F,$6C,$75,$74,$65
	dc.b $00,$42,$61,$64,$20,$61,$72,$67,$75,$6D,$65,$6E,$74,$73,$0A,$00
	dc.b "Error in WITH file",$00
	dc.b "WITH file not found",$00
	dc.b "Could not open listing device",$0A
	dc.b $00
	dc.b "Assembling ",$00
	dc.b $20,$69,$6E,$20,$61,$73,$73,$65,$6D,$62,$6C,$79,$20,$6F,$70,$74
	dc.b $69,$6F,$6E,$73,$00,$4D,$61,$69,$6E,$20,$66,$69,$6C,$65,$20,$61
	dc.b $6C,$72,$65,$61,$64,$79,$20,$69,$6E,$63,$6C,$75,$64,$65,$64,$20
	dc.b $69,$6E,$20,$68,$65,$61,$64,$65,$72,$20,$66,$69,$6C,$65,$0A,$00
loc_0_0000962C:
	pea.l loc_0_00009292(pc)
	tst.b app_0109(a6)
	beq.b loc_0_0000963C
	lea.l loc_0_0000965A(pc),a0
	rts
loc_0_0000963C:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9AA
	bra.w loc_0_0000A396
loc_0_0000964A:
	tst.b app_0109(a6)
	beq.b loc_0_00009666
	lea.l loc_0_00009656(pc),a0
	rts
loc_0_00009656:
	dc.b $2E,$67,$73,$00
loc_0_0000965A:
	dc.b "Gen symbol",$00
	dc.b $00
loc_0_00009666:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9B0
	bra.w loc_0_0000A3A8
	dc.b $08,$2E,$00,$02,$02,$1D,$66,$00,$63,$56,$60,$00,$0D,$5E
loc_0_00009682:
	cmpi.w #3,app_021C(a6)
	beq.b loc_0_00009690
	tst.l $019A(a6)
	bne.b loc_0_0000969E
loc_0_00009690:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F954
	bra.w loc_0_00009BC6
loc_0_0000969E:
	moveq.l #66,d0
	bra.w loc_0_0000846E
loc_0_000096A4:
	tst.b app_0103(a6)
	beq.b loc_0_000096BC
	movea.l $013E(a6),a1
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F82E
	bra.w loc_0_00009A2C
loc_0_000096BC:
	rts
loc_0_000096BE:
	tst.b app_0103(a6)
	beq.b loc_0_000096BC
	movea.l $013E(a6),a1
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F82E
	bra.w loc_0_00009A2C
loc_0_000096D6:
	tst.b app_0103(a6)
	beq.b loc_0_000096EA
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F830
	bra.w loc_0_00009A2E
loc_0_000096EA:
	rts
	dc.b $4A,$2E,$01,$03,$67,$F8,$08,$2E,$00,$02,$02,$1D,$66,$00,$61,$34
	dc.b $60,$00,$03,$2E
loc_0_00009700:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F830
	bra.w loc_0_00009A2E
loc_0_0000970E:
	tst.b app_011B(a6)
	bne.b loc_0_00009728
	tst.b app_0103(a6)
	beq.b loc_0_000096EA
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F868
	bra.w loc_0_00009A90
loc_0_00009728:
	moveq.l #38,d0
	bra.w loc_0_00008486
loc_0_0000972E:
	cmpi.b #255,app_011B(a6)
	beq.b loc_0_00009744
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F982
	bra.w loc_0_00009C38
loc_0_00009744:
	rts
loc_0_00009746:
	move.l app_023C(a6),d2
	moveq.l #1,d1
	clr.b (a5)+
	add.l d1,app_023C(a6)
	add.l d1,app_0224(a6)
	tst.b app_0238(a6)
	beq.b loc_0_00009768
	tst.b app_0103(a6)
	beq.b loc_0_00009768
	bsr.b loc_0_0000972E
	beq.b loc_0_00009768
	bsr.b loc_0_0000970E
loc_0_00009768:
	movea.l app_024C(a6),a5
	move.l a5,app_0250(a6)
	rts
	dc.b $08,$2E,$00,$02,$02,$1D,$66,$00,$02,$E8,$60,$00,$02,$D6
loc_0_00009780:
	tst.b app_011B(a6)
	bne.b loc_0_00009794
	btst.b #2,app_021D(a6)
	bne.w loc_0_00009C2A
	bra.w loc_0_00009C2A
loc_0_00009794:
	moveq.l #79,d1
	bsr.w loc_0_00009288
	bra.w loc_0_00008E92
loc_0_0000979E:
	moveq.l #40,d0
	jmp loc_0_0000846E.l
loc_0_000097A6:
	tst.l $0186(a6)
	bne.b loc_0_000097C2
	movem.l d1-d2/a0-a2,-(a7)
	lea.l app_06C8(a6),a0
	bsr.w loc_0_000097C4
	bne.b loc_0_0000979E
	move.l d2,$0186(a6)
	movem.l (a7)+,d1-d2/a0-a2
loc_0_000097C2:
	rts
loc_0_000097C4:
	lea.l app_071A(a6),a1
	move.b (a0),d0
	beq.b loc_0_000097E4
	cmp.b #$2E,d0
	bne.b loc_0_00009826
	move.b $0001(a0),d0
	cmp.b #$2E,d0
	beq.b loc_0_00009826
	cmp.b #$5C,d0
	beq.b loc_0_00009826
	move.b (a0),d0
loc_0_000097E4:
	move.l a1,d2
loc_0_000097E6:
	tst.b (a1)+
	bne.b loc_0_000097E6
	sub.l a1,d2
	neg.l d2
	tst.b d0
	bne.b loc_0_000097F6
loc_0_000097F2:
	bsr.w loc_0_0000964A
loc_0_000097F6:
	subq.l #1,a1
	subq.b #1,d2
	bsr.w loc_0_00009812
	bsr.w loc_0_0000B002
	lea.l app_071A(a6),a0
	rts
loc_0_00009808:
	lea.l app_06C8(a6),a0
	lea.l app_071A(a6),a1
	moveq.l #0,d2
loc_0_00009812:
	cmp.b #$52,d2
	beq.b loc_0_00009820
	addq.b #1,d2
	move.b (a0)+,d1
	move.b d1,(a1)+
	bne.b loc_0_00009812
loc_0_00009820:
	lea.l app_071A(a6),a0
	rts
loc_0_00009826:
	tst.b (a0)+
	bne.b loc_0_00009826
	move.b -$0002(a0),d0
	cmp.b #$2F,d0
	beq.b loc_0_00009856
	cmp.b #$3A,d0
	beq.b loc_0_00009856
	lea.l app_06C8(a6),a0
	bsr.w loc_0_0000B002
	beq.w loc_0_0000985E
	bsr.b loc_0_00009808
	move.b #$2F,-$0001(a1)
loc_0_0000984E:
	lea.l app_076C(a6),a0
	bsr.b loc_0_00009812
	bra.b loc_0_000097F2
loc_0_00009856:
	bsr.b loc_0_00009808
	subq.w #1,a1
	subq.b #1,d2
	bra.b loc_0_0000984E
loc_0_0000985E:
	lea.l app_06C8(a6),a0
	rts
loc_0_00009864:
	lea.l loc_0_00009884(pc),a0
	move.l a0,$017A(a6)
	move.l app_024C(a6),d1
	tst.b app_011B(a6)
	bne.b loc_0_00009888
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F92C
	bra.w loc_0_00009B40
loc_0_00009884:
	dc.b $42,$AE,$01,$82
loc_0_00009888:
	rts
loc_0_0000988A:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F892
	bra.w loc_0_00009AA4
loc_0_00009898:
	tst.b app_0103(a6)
	beq.b loc_0_000098AC
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F992
	bra.w loc_0_00009DA6
loc_0_000098AC:
	rts
loc_0_000098AE:
	move.l $0186(a6),d2
	beq.b loc_0_000098BC
	bsr.w loc_0_0000AFB8
	clr.l $0186(a6)
loc_0_000098BC:
	rts
	dc.b $2F,$02,$20,$3C,$00,$00,$11,$3E,$92,$80,$64,$04,$D0,$81,$72,$00
	dc.b $20,$4E,$2F,$01,$22,$00,$61,$00,$EB,$4C,$22,$1F,$66,$E4,$24,$1F
	dc.b $4E,$75
loc_0_000098E0:
	dc.b $08,$2E,$00,$02,$02,$1D,$66,$00,$60,$BE,$60,$00,$0A,$6A
loc_0_000098EE:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9A2
	bra.w loc_0_0000A2CA
loc_0_000098FC:
	tst.b app_0112(a6)
	bne.b loc_0_0000991A
	cmp.b #$1,d3
	bne.b loc_0_0000990C
	st.b app_0114(a6)
loc_0_0000990C:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F99E
	bra.w loc_0_0000A2B6
loc_0_0000991A:
	rts
loc_0_0000991C:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9A2
	bra.w loc_0_0000A2D6
	dc.b $08,$2E,$00,$02,$02,$1D,$66,$00,$60,$70,$60,$00,$09,$94
loc_0_00009938:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9A2
	bra.w loc_0_0000A2CA
loc_0_00009946:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9A6
	bra.w loc_0_0000A32E
loc_0_00009954:
	btst.b #2,app_021D(a6)
	bne.w loc_0_0000F9A6
	bra.w loc_0_0000A35E
loc_0_00009962:
	dc.b $4A,$2E,$01,$06,$67,$06,$70,$3C,$60,$00,$EB,$1A,$4A,$2E,$01,$12
	dc.b $66,$28,$48,$E7,$60,$00,$50,$EE,$01,$14,$20,$0D,$90,$AE,$02,$4C
	dc.b $D0,$AE,$02,$3C,$48,$7A,$00,$10,$08,$2E,$00,$02,$02,$1D,$66,$00
	dc.b $60,$0A,$60,$00,$09,$14,$4C,$DF,$00,$06,$4E,$75,$70,$00,$10,$2E
	dc.b $01,$46,$22,$02,$92,$AE,$02,$3C,$08,$2E,$00,$02,$02,$1D,$66,$00
	dc.b $5E,$80,$60,$00,$00,$7A,$70,$00,$10,$2E,$01,$46,$22,$2E,$02,$3C
	dc.b $08,$2E,$00,$02,$02,$1D,$66,$00,$5E,$9A,$60,$00,$00,$A0
loc_0_000099D0:
	moveq.l #-1,d0
	move.l a1,-(a7)
loc_0_000099D4:
	move.b (a1)+,d1
	cmp.b #$A,d1
	beq.b loc_0_000099E8
	cmp.b #$9,d1
	beq.b loc_0_000099E8
	cmp.b #$20,d1
	bne.b loc_0_000099D4
loc_0_000099E8:
	move.l a1,d3
	movea.l (a7)+,a1
	sub.l a1,d3
	subq.l #1,d3
	beq.b loc_0_00009A22
	moveq.l #0,d2
loc_0_000099F4:
	addq.l #1,d0
	move.b (a2)+,d2
	beq.b loc_0_00009A22
	cmp.b d2,d3
	bcs.b loc_0_00009A22
	bne.b loc_0_00009A1E
	movem.l d2-d3/a1-a2,-(a7)
loc_0_00009A04:
	move.b (a1)+,d3
	ext.w d3
	move.b $7E(a6,d3.w),d3
	cmp.b (a2)+,d3
	bne.b loc_0_00009A1A
	subq.b #1,d2
	bne.b loc_0_00009A04
	movem.l (a7)+,d2-d3/a1-a2
	rts
loc_0_00009A1A:
	movem.l (a7)+,d2-d3/a1-a2
loc_0_00009A1E:
	adda.l d2,a2
	bra.b loc_0_000099F4
loc_0_00009A22:
	moveq.l #80,d0
	bsr.w loc_0_00008486
	moveq.l #-1,d0
	rts
loc_0_00009A2C:
	rts
loc_0_00009A2E:
	rts
	dc.b $4A,$2E,$01,$03,$67,$1A,$22,$6E,$01,$AA,$4A,$2E,$02,$38,$66,$10
	dc.b $22,$2E,$02,$3C,$92,$A9,$00,$1C,$D3,$A9,$00,$14,$23,$42,$00,$1C
	dc.b $70,$00,$4E,$75,$22,$6E,$01,$AA,$0C,$69,$03,$EB,$00,$12,$67,$00
	dc.b $E9,$FA,$D3,$AE,$02,$4C,$1A,$D8,$53,$81,$66,$FA,$4E,$75,$4A,$2E
	dc.b $02,$38,$67,$18,$4A,$2E,$01,$03,$67,$12,$22,$6E,$01,$AA,$0C,$69
	dc.b $03,$EB,$00,$12,$67,$06,$94,$81,$D5,$AE,$02,$4C,$70,$00,$4E,$75
loc_0_00009A90:
	movea.l $01AA(a6),a0
	cmpi.w #1003,$0012(a0)
	beq.w loc_0_0000845A
	add.l d1,app_024C(a6)
	rts
loc_0_00009AA4:
	tst.b app_0238(a6)
	bne.w loc_0_00009B0A
	bsr.w loc_0_00009B24
	beq.b loc_0_00009B04
	movem.l a0-a1,-(a7)
	moveq.l #36,d1
	bsr.w loc_0_000090BA
	movem.l (a7)+,a1-a2
	move.l a0,(a1)
	clr.l (a0)
	move.l a2,$0004(a0)
	clr.l $0014(a0)
	clr.l $001C(a0)
	clr.l $0018(a0)
	move.l #$3E9,$0010(a0)
	tst.l $0196(a6)
	beq.b loc_0_00009AFE
	movea.l $0196(a6),a1
	lea.l loc_0_00009B6A(pc),a2
	bsr.w loc_0_000099D0
	bne.b loc_0_00009AFE
	add.w d0,d0
	add.w d0,d0
	lea.l loc_0_00009BA2(pc),a2
	move.l $0(a2,d0.w),$0010(a0)
loc_0_00009AFE:
	clr.l $0008(a0)
	movea.l a0,a1
loc_0_00009B04:
	move.l a1,$01AA(a6)
	rts
loc_0_00009B0A:
	bsr.b loc_0_00009B24
	bne.b loc_0_00009B64
	move.l $000C(a1),app_024C(a6)
	bne.b loc_0_00009B1E
	lea.l app_05A8(a6),a0
	move.l a0,app_024C(a6)
loc_0_00009B1E:
	move.l a1,$01AA(a6)
	rts
loc_0_00009B24:
	lea.l $01A6(a6),a0
	move.b $000E(a1),d0
loc_0_00009B2C:
	tst.l (a0)
	beq.b loc_0_00009B3C
	addq.b #1,d0
	beq.b loc_0_00009B38
	movea.l (a0),a0
	bra.b loc_0_00009B2C
loc_0_00009B38:
	movea.l (a0),a1
	rts
loc_0_00009B3C:
	moveq.l #-1,d0
	rts
loc_0_00009B40:
	bsr.b loc_0_00009B24
	bne.b loc_0_00009B64
	tst.b app_0238(a6)
	bne.b loc_0_00009B5E
	move.l app_023C(a6),d2
	sub.l $001C(a1),d2
	add.l d2,$0014(a1)
	move.l app_023C(a6),$001C(a1)
	rts
loc_0_00009B5E:
	move.l a5,$000C(a1)
	rts
loc_0_00009B64:
	moveq.l #77,d0
	bra.w loc_0_0000846E
loc_0_00009B6A:
	dc.b $03,$42,$53,$53,$04,$43,$4F,$44,$45,$04,$44,$41,$54,$41,$05,$42
	dc.b $53,$53,$5F,$43,$05,$42,$53,$53,$5F,$46,$06,$43,$4F,$44,$45,$5F
	dc.b $43,$06,$43,$4F,$44,$45,$5F,$46,$06,$44,$41,$54,$41,$5F,$43,$06
	dc.b $44,$41,$54,$41,$5F,$46,$00,$00
loc_0_00009BA2:
	dc.b $00,$00,$03,$EB,$00,$00,$03,$E9,$00,$00,$03,$EA,$40,$00,$03,$EB
	dc.b $80,$00,$03,$EB,$40,$00,$03,$E9,$80,$00,$03,$E9,$40,$00,$03,$EA
	dc.b $80,$00,$03,$EA
loc_0_00009BC6:
	move.l a4,-(a7)
	movea.l $019A(a6),a4
	lea.l $01A6(a6),a3
loc_0_00009BD0:
	tst.l (a3)
	beq.b loc_0_00009C20
	movea.l (a3),a3
	move.l $0014(a3),d1
	beq.b loc_0_00009C24
	move.l d1,d0
	andi.b #3,d0
	beq.b loc_0_00009BEA
	andi.b #252,d1
	addq.l #4,d1
loc_0_00009BEA:
	move.l d1,$0014(a3)
	tst.l $019A(a6)
	beq.b loc_0_00009C02
	move.w $0010(a3),d0
	bsr.w loc_0_0000AE02
	bne.w loc_0_000090EC
	bra.b loc_0_00009C10
loc_0_00009C02:
	cmpi.w #1003,$0012(a3)
	beq.b loc_0_00009C24
	addq.l #8,d1
	bsr.w loc_0_000090BA
loc_0_00009C10:
	move.l a0,$0008(a3)
	move.l a0,$000C(a3)
	adda.l $0014(a3),a0
	clr.l -(a0)
	bra.b loc_0_00009BD0
loc_0_00009C20:
	movea.l (a7)+,a4
	rts
loc_0_00009C24:
	clr.l $000C(a3)
	bra.b loc_0_00009BD0
loc_0_00009C2A:
	move.b d0,d1
	not.b d1
	bsr.w loc_0_00008EB6
	moveq.l #46,d1
	bra.w loc_0_00009288
loc_0_00009C38:
	movea.l $01AA(a6),a1
	cmpi.w #1003,$0012(a1)
	rts
loc_0_00009C44:
	movea.l $019E(a6),a4
	tst.b $0104(a6)
	beq.b loc_0_00009C9E
	lea.l $01A6(a6),a3
loc_0_00009C52:
	movea.l (a3),a3
	movea.l $0004(a3),a0
	move.b $000E(a0),d6
	movea.l $013E(a6),a1
	lea.l loc_0_00009D02(pc),a2
	moveq.l #0,d7
	bsr.w loc_0_00008CF6
	tst.l d7
	beq.b loc_0_00009C9A
	move.l d7,d1
	addq.l #8,d1
	moveq.l #0,d0
	bsr.w loc_0_0000AE02
	bne.w loc_0_000090EC
	move.l a4,-(a7)
	movea.l a0,a4
	move.l #$3F0,(a4)+
	lea.l loc_0_00009D2A(pc),a2
	movea.l $013E(a6),a1
	movea.l $0004(a3),a0
	bsr.w loc_0_00008CF6
	clr.l (a4)
	movea.l (a7)+,a4
loc_0_00009C9A:
	tst.l (a3)
	bne.b loc_0_00009C52
loc_0_00009C9E:
	tst.b $0129(a6)
	beq.b loc_0_00009CBE
	lea.l $01A6(a6),a3
loc_0_00009CA8:
	movea.l (a3),a3
	movea.l $0004(a3),a0
	move.b $000E(a0),d6
	lea.l loc_0_00008C00(pc),a2
	bsr.w loc_0_00008C9A
	tst.l (a3)
	bne.b loc_0_00009CA8
loc_0_00009CBE:
	lea.l $01A6(a6),a3
loc_0_00009CC2:
	movea.l (a3),a3
	tst.l $0018(a3)
	beq.b loc_0_00009CFC
	moveq.l #0,d3
	lea.l $01A6(a6),a2
	moveq.l #1,d6
loc_0_00009CD2:
	movea.l (a2),a2
	movea.l $0004(a2),a0
	move.b $000E(a0),d3
	bsr.w loc_0_0000A164
	beq.b loc_0_00009CF8
loc_0_00009CE2:
	bsr.w loc_0_0000A192
	bne.b loc_0_00009CF8
	movea.l $0004(a0),a1
	adda.l $0008(a3),a1
	move.l $0008(a2),d1
	add.l d1,(a1)
	bra.b loc_0_00009CE2
loc_0_00009CF8:
	tst.l (a2)
	bne.b loc_0_00009CD2
loc_0_00009CFC:
	tst.l (a3)
	bne.b loc_0_00009CC2
	rts
loc_0_00009D02:
	dc.b $BC,$29,$00,$0E,$66,$F8,$0C,$29,$00,$01,$00,$0D,$66,$F0,$72,$00
	dc.b $12,$29,$00,$16,$24,$01,$02,$02,$00,$03,$67,$06,$02,$01,$00,$FC
	dc.b $58,$81,$DE,$81,$50,$87,$4E,$75
loc_0_00009D2A:
	dc.b $BC,$29,$00,$0E,$66,$D0,$0C,$29,$00,$01,$00,$0D,$66,$C8,$61,$0C
	dc.b $20,$29,$00,$08,$D0,$AB,$00,$08,$28,$C0,$4E,$75
loc_0_00009D46:
	moveq.l #0,d1
	move.b $0016(a1),d1
	move.l d1,d2
	andi.b #3,d2
	beq.b loc_0_00009D5A
	andi.b #252,d1
	addq.l #4,d1
loc_0_00009D5A:
	lsr.l #2,d1
	move.l d1,(a4)+
	lea.l $0016(a1),a0
	move.b (a0)+,d0
loc_0_00009D64:
	move.b (a0)+,(a4)+
	subq.b #1,d0
	bne.b loc_0_00009D64
	move.b $0016(a1),d0
	andi.b #3,d0
	beq.b loc_0_00009D7E
loc_0_00009D74:
	clr.b (a4)+
	addq.b #1,d0
	cmp.b #$4,d0
	bne.b loc_0_00009D74
loc_0_00009D7E:
	rts
loc_0_00009D80:
	movem.l d6/a0-a2,-(a7)
	movea.l $0004(a0),a0
	move.b $000E(a0),d6
	lea.l loc_0_00009DA2(pc),a2
	movea.l $013E(a6),a1
	moveq.l #0,d0
	bsr.w loc_0_00008D1C
	movem.l (a7)+,d6/a0-a2
	tst.l d0
	rts
loc_0_00009DA2:
	addq.l #1,d0
	rts
loc_0_00009DA6:
	tst.l $019A(a6)
	bne.w loc_0_00009C44
	bsr.w loc_0_000097A6
	cmpi.w #3,app_021C(a6)
	bne.b loc_0_00009E34
	bsr.w loc_0_0000A110
	move.l #$3F3,d1
	bsr.w loc_0_0000A0EE
	moveq.l #0,d1
	bsr.w loc_0_0000A0EE
	moveq.l #0,d1
	lea.l $01A6(a6),a0
loc_0_00009DD4:
	movea.l (a0),a0
	tst.l $0014(a0)
	bne.b loc_0_00009DE0
	bsr.b loc_0_00009D80
	beq.b loc_0_00009DE2
loc_0_00009DE0:
	addq.l #1,d1
loc_0_00009DE2:
	tst.l (a0)
	bne.b loc_0_00009DD4
	bsr.w loc_0_0000A0EE
	move.l d1,d2
	moveq.l #0,d1
	bsr.w loc_0_0000A0EE
	move.l d2,d1
	subq.l #1,d1
	bsr.w loc_0_0000A0EE
	lea.l $01A6(a6),a3
loc_0_00009DFE:
	movea.l (a3),a3
	move.l $0014(a3),d1
	bne.b loc_0_00009E0E
	movea.l a3,a0
	bsr.w loc_0_00009D80
	beq.b loc_0_00009E1C
loc_0_00009E0E:
	lsr.l #2,d1
	swap.w d1
	or.w $0010(a3),d1
	swap.w d1
	bsr.w loc_0_0000A0EE
loc_0_00009E1C:
	tst.l (a3)
	bne.b loc_0_00009DFE
	bsr.w loc_0_0000A0F6
	tst.b $0129(a6)
	beq.b loc_0_00009E2E
	bsr.w loc_0_0000A42E
loc_0_00009E2E:
	lea.l $01A6(a6),a3
	bra.b loc_0_00009E64
loc_0_00009E34:
	move.l #$3E7,d1
	lea.l $01AE(a6),a1
	tst.b (a1)
	beq.b loc_0_00009E50
	move.l a1,d0
loc_0_00009E44:
	tst.b (a1)+
	bne.b loc_0_00009E44
	subq.l #1,a1
	exg d0,a1
	sub.l a1,d0
	bra.b loc_0_00009E5C
loc_0_00009E50:
	movea.l $013E(a6),a1
	lea.l $0016(a1),a1
	move.b (a1)+,d0
	subq.b #1,d0
loc_0_00009E5C:
	bsr.w loc_0_0000A1D0
	lea.l $01A6(a6),a3
loc_0_00009E64:
	movea.l (a3),a3
	tst.l $0014(a3)
	bne.b loc_0_00009E76
	movea.l a3,a0
	bsr.w loc_0_00009D80
	beq.w loc_0_00009FF8
loc_0_00009E76:
	cmpi.w #3,app_021C(a6)
	beq.b loc_0_00009E94
	move.l #$3E8,d1
	movea.l $0004(a3),a1
	lea.l $0016(a1),a1
	move.b (a1)+,d0
	subq.b #1,d0
	bsr.w loc_0_0000A1D0
loc_0_00009E94:
	lea.l $0014(a3),a0
	move.l (a0),d0
	lsr.l #2,d0
	move.l d0,(a0)
	subq.l #4,a0
	moveq.l #8,d1
	bsr.w loc_0_00008422
	cmpi.w #1003,$0012(a3)
	beq.b loc_0_00009EBE
	movea.l $0008(a3),a0
	move.l $0014(a3),d1
	add.l d1,d1
	add.l d1,d1
	bsr.w loc_0_00008422
loc_0_00009EBE:
	bsr.w loc_0_0000A110
	tst.l $0018(a3)
	beq.w loc_0_00009F6C
	moveq.l #1,d6
	move.l #$3EC,d1
	bsr.b loc_0_00009EF4
	cmpi.w #3,app_021C(a6)
	beq.w loc_0_00009F6C
	move.l #$3F8,d1
	moveq.l #40,d6
	bsr.b loc_0_00009EF4
	move.l #$3F9,d1
	moveq.l #41,d6
	bsr.b loc_0_00009EF4
	bra.b loc_0_00009F6C
loc_0_00009EF4:
	moveq.l #0,d3
	move.l d1,-(a7)
	pea.l $01A6(a6)
	clr.l -(a7)
loc_0_00009EFE:
	movea.l $0004(a7),a0
loc_0_00009F02:
	tst.l (a0)
	beq.b loc_0_00009F5A
	movea.l (a0),a0
	subq.l #1,d3
	tst.l $0014(a0)
	bne.b loc_0_00009F16
	bsr.w loc_0_00009D80
	beq.b loc_0_00009F02
loc_0_00009F16:
	move.l a0,$0004(a7)
	bsr.w loc_0_0000A164
	beq.b loc_0_00009F4E
	move.l $0008(a7),d0
	beq.b loc_0_00009F34
	move.l d1,-(a7)
	move.l d0,d1
	bsr.w loc_0_0000A0EE
	move.l (a7)+,d1
	clr.l $0008(a7)
loc_0_00009F34:
	bsr.w loc_0_0000A0EE
	move.l (a7),d1
	bsr.w loc_0_0000A0EE
loc_0_00009F3E:
	bsr.w loc_0_0000A192
	bne.b loc_0_00009F4E
	move.l $0004(a0),d1
	bsr.w loc_0_0000A0EE
	bra.b loc_0_00009F3E
loc_0_00009F4E:
	addq.l #1,(a7)
	movea.l $013E(a6),a0
	cmp.b $000C(a0),d3
	bne.b loc_0_00009EFE
loc_0_00009F5A:
	tst.l $0008(a7)
	lea.l $000C(a7),a7
	bne.b loc_0_00009F6A
	moveq.l #0,d1
	bra.w loc_0_0000A0EE
loc_0_00009F6A:
	rts
loc_0_00009F6C:
	cmpi.w #3,app_021C(a6)
	beq.b loc_0_00009FA6
	move.l #$3EF,d1
	bsr.w loc_0_0000A0EE
	movea.l $0004(a3),a0
	move.b $000E(a0),d3
	movea.l $013E(a6),a1
	lea.l loc_0_0000A11A(pc),a2
	bsr.w loc_0_00008D48
	move.b d3,d6
	lea.l loc_0_0000A034(pc),a2
	movea.l $013E(a6),a1
	bsr.w loc_0_00008D1C
	moveq.l #0,d1
	bsr.w loc_0_0000A0EE
loc_0_00009FA6:
	tst.l app_020C(a6)
	beq.b loc_0_00009FBC
	movem.l d2/a0-a1,-(a7)
	bsr.w loc_0_0000B054
	movem.l (a7)+,d2/a0-a1
	move.l d0,$0020(a3)
loc_0_00009FBC:
	tst.b $0104(a6)
	beq.b loc_0_00009FE6
	movea.l $0004(a3),a0
	move.b $000E(a0),d6
	move.l #$3F0,d1
	bsr.w loc_0_0000A0EE
	movea.l $013E(a6),a1
	lea.l loc_0_0000A04C(pc),a2
	bsr.w loc_0_00008CF6
	moveq.l #0,d1
	bsr.w loc_0_0000A0EE
loc_0_00009FE6:
	tst.b $0129(a6)
	beq.w loc_0_00009FF6
	lea.l loc_0_00008B4C(pc),a2
	bsr.w loc_0_00008C9A
loc_0_00009FF6:
	bsr.b loc_0_0000A01A
loc_0_00009FF8:
	tst.l (a3)
	bne.w loc_0_00009E64
	lea.l $01A6(a6),a3
loc_0_0000A002:
	movea.l (a3),a3
	tst.l $0014(a3)
	bne.b loc_0_0000A028
	movea.l a3,a0
	bsr.w loc_0_00009D80
	bne.b loc_0_0000A028
	tst.l (a3)
	bne.b loc_0_0000A002
	bsr.w loc_0_0000A110
loc_0_0000A01A:
	move.l #$3F2,d1
	bsr.w loc_0_0000A0EE
	bra.w loc_0_0000A0F6
loc_0_0000A028:
	tst.l app_020C(a6)
	beq.b loc_0_0000A032
	bsr.w loc_0_0000A450
loc_0_0000A032:
	rts
loc_0_0000A034:
	dc.b $70,$01,$0C,$29,$00,$01,$00,$0D,$67,$02,$70,$02,$61,$56,$22,$29
	dc.b $00,$08,$60,$00,$00,$A6,$4E,$75
loc_0_0000A04C:
	dc.b $BC,$29,$00,$0E,$66,$F8,$0C,$29,$00,$01,$00,$0D,$66,$F0,$08,$29
	dc.b $00,$04,$00,$0C,$66,$E8,$0C,$6E,$00,$03,$02,$1C,$67,$12,$4A,$2E
	dc.b $01,$04,$6A,$08,$08,$29,$00,$05,$00,$0C,$67,$D2,$70,$00,$60,$C4
	dc.b $30,$2B,$00,$12,$B0,$7C,$03,$EA,$67,$0C,$B0,$7C,$03,$E9,$66,$EC
	dc.b $52,$AE,$02,$14,$60,$E6,$52,$AE,$02,$10,$60,$E0
loc_0_0000A098:
	moveq.l #0,d1
	move.b $0016(a1),d1
	move.l d1,d2
	andi.b #3,d2
	beq.b loc_0_0000A0AC
	andi.b #252,d1
	addq.l #4,d1
loc_0_0000A0AC:
	lsr.l #2,d1
	ror.l #8,d0
	or.l d0,d1
	bsr.b loc_0_0000A0EE
	moveq.l #4,d0
	add.b $0016(a1),d0
	cmp.w d0,d4
	bcc.b loc_0_0000A0C0
	bsr.b loc_0_0000A0F6
loc_0_0000A0C0:
	lea.l $0016(a1),a0
	move.b (a0)+,d0
loc_0_0000A0C6:
	move.b (a0)+,(a4)+
	subq.w #1,d4
	subq.b #1,d0
	bne.b loc_0_0000A0C6
	move.b $0016(a1),d0
	andi.b #3,d0
	beq.b loc_0_0000A0E4
loc_0_0000A0D8:
	clr.b (a4)+
	addq.b #1,d0
	subq.w #1,d4
	cmp.b #$4,d0
	bne.b loc_0_0000A0D8
loc_0_0000A0E4:
	rts
loc_0_0000A0E6:
	addq.w #4,d4
	move.l d1,-(a7)
	bsr.b loc_0_0000A0F6
	move.l (a7)+,d1
loc_0_0000A0EE:
	subq.w #4,d4
	bcs.b loc_0_0000A0E6
	move.l d1,(a4)+
	rts
loc_0_0000A0F6:
	move.l #$80,d1
	sub.w d4,d1
	beq.b loc_0_0000A110
	movem.l d0/d2/a0-a2,-(a7)
	lea.l app_05A8(a6),a0
	bsr.w loc_0_00008422
	movem.l (a7)+,d0/d2/a0-a2
loc_0_0000A110:
	lea.l app_05A8(a6),a4
	move.w #$80,d4
	rts
loc_0_0000A11A:
	movem.l a1-a2,-(a7)
	moveq.l #2,d6
	move.w $0014(a1),d2
	bsr.b loc_0_0000A13C
	moveq.l #4,d6
	bsr.b loc_0_0000A13C
	moveq.l #5,d6
	bsr.b loc_0_0000A13C
	moveq.l #7,d6
	bsr.b loc_0_0000A13C
	moveq.l #8,d6
	bsr.b loc_0_0000A13C
	movem.l (a7)+,a1-a2
	rts
loc_0_0000A13C:
	bsr.w loc_0_0000A164
	beq.b loc_0_0000A162
	movem.l d1-d2,-(a7)
	moveq.l #127,d0
	add.b d6,d0
	bsr.w loc_0_0000A098
	movem.l (a7)+,d1-d2
	bsr.b loc_0_0000A0EE
loc_0_0000A154:
	bsr.w loc_0_0000A192
	bne.b loc_0_0000A162
	move.l $0004(a0),d1
	bsr.b loc_0_0000A0EE
	bra.b loc_0_0000A154
loc_0_0000A162:
	rts
loc_0_0000A164:
	moveq.l #0,d1
	tst.l $0018(a3)
	beq.b loc_0_0000A17C
	bsr.b loc_0_0000A17E
	beq.b loc_0_0000A17C
loc_0_0000A170:
	bsr.b loc_0_0000A192
	bne.b loc_0_0000A178
	addq.l #1,d1
	bra.b loc_0_0000A170
loc_0_0000A178:
	bsr.b loc_0_0000A17E
	tst.l d1
loc_0_0000A17C:
	rts
loc_0_0000A17E:
	movea.l $0018(a3),a5
loc_0_0000A182:
	moveq.l #10,d5
	lea.l $000A(a5),a0
	move.l a0,$0006(a5)
	sub.w $0004(a5),d5
	rts
loc_0_0000A192:
	subq.w #1,d5
	bcs.b loc_0_0000A1C2
	movea.l $0006(a5),a0
	addq.l #8,$0006(a5)
	cmp.b (a0),d6
	bne.b loc_0_0000A192
	cmp.b $0001(a0),d3
	bne.b loc_0_0000A192
	cmp.b #$1,d6
	beq.b loc_0_0000A1C0
	cmp.b #$28,d6
	beq.b loc_0_0000A1C0
	cmp.b #$29,d6
	beq.b loc_0_0000A1C0
	cmp.w $0002(a0),d2
	bne.b loc_0_0000A192
loc_0_0000A1C0:
	rts
loc_0_0000A1C2:
	tst.l (a5)
	beq.b loc_0_0000A1CC
	movea.l (a5),a5
	bsr.b loc_0_0000A182
	bne.b loc_0_0000A192
loc_0_0000A1CC:
	moveq.l #-1,d0
	rts
loc_0_0000A1D0:
	lea.l app_05A8(a6),a0
	move.l d1,(a0)+
	moveq.l #0,d1
	move.b d0,d1
	move.l d1,d2
	andi.b #3,d2
	beq.b loc_0_0000A1E8
	andi.b #252,d1
	addq.l #4,d1
loc_0_0000A1E8:
	lsr.l #2,d1
	move.l d1,(a0)+
	beq.b loc_0_0000A1FA
loc_0_0000A1EE:
	move.b (a1)+,(a0)+
	subq.b #1,d0
	bne.b loc_0_0000A1EE
	clr.b (a0)+
	clr.b (a0)+
	clr.b (a0)+
loc_0_0000A1FA:
	add.l d1,d1
	add.l d1,d1
	addq.l #8,d1
	lea.l app_05A8(a6),a0
	bra.w loc_0_00008422
loc_0_0000A208:
	movea.l $01AA(a6),a0
	lea.l $0018(a0),a0
	tst.l (a0)
	beq.b loc_0_0000A220
loc_0_0000A214:
	movea.l (a0),a0
	tst.w $0004(a0)
	bne.b loc_0_0000A240
	tst.l (a0)
	bne.b loc_0_0000A214
loc_0_0000A220:
	movem.l d0-d2/a0/a2,-(a7)
	moveq.l #90,d1
	bsr.w loc_0_000090BA
	movem.l (a7)+,d0-d2/a1-a2
	move.l a0,(a1)
	clr.l (a0)
	move.w #$A,$0004(a0)
	lea.l $000A(a0),a1
	move.l a1,$0006(a0)
loc_0_0000A240:
	subq.w #1,$0004(a0)
	movea.l $0006(a0),a1
	addq.l #8,$0006(a0)
	movea.l a1,a0
	rts
loc_0_0000A250:
	movea.l app_0940(a6),a0
	move.w (a0)+,d0
	cmp.w #$2B2B,d0
	bne.b loc_0_0000A288
	move.w (a0)+,d0
	bpl.b loc_0_0000A280
	andi.w #255,d0
	cmpi.w #11565,(a0)
	bne.b loc_0_0000A280
	tst.b $0002(a0)
	bpl.b loc_0_0000A280
	cmp.b $0003(a0),d0
	bne.b loc_0_0000A280
	tst.w $0004(a0)
	bne.b loc_0_0000A288
	addq.l #4,a7
	rts
loc_0_0000A280:
	tst.w (a0)
	bne.b loc_0_0000A288
	tst.w -(a0)
	rts
loc_0_0000A288:
	moveq.l #68,d0
	bra.w loc_0_00008486
loc_0_0000A28E:
	add.l app_023C(a6),d2
	add.l a5,d2
	sub.l app_024C(a6),d2
	tst.b app_0103(a6)
	beq.b loc_0_0000A2A8
	bsr.w loc_0_0000A208
	move.w d0,(a0)
	move.l d2,$0004(a0)
loc_0_0000A2A8:
	rts
	dc.b $24,$00,$30,$3C,$01,$00,$80,$2E,$01,$46,$60,$E2
loc_0_0000A2B6:
	move.l d2,(a5)+
	bsr.b loc_0_0000A250
	bpl.b loc_0_0000A2C4
	ori.w #256,d0
	moveq.l #-4,d2
	bra.b loc_0_0000A28E
loc_0_0000A2C4:
	bsr.w loc_0_0000A36C
	dc.b $02,$FC
loc_0_0000A2CA:
	move.w d2,(a5)+
	bsr.b loc_0_0000A250
	bmi.b loc_0_0000A288
	bsr.w loc_0_0000A36C
	dc.b $04,$FE
loc_0_0000A2D6:
	cmpi.w #3,app_021C(a6)
	bne.w loc_0_0000A312
	move.w d2,(a5)+
	cmp.b #$1,d3
	beq.b loc_0_0000A288
	movea.l app_0940(a6),a0
	move.w (a0)+,d0
	cmp.w #$2B2B,d0
	bne.b loc_0_0000A288
	move.w (a0)+,d0
	bpl.b loc_0_0000A288
	cmpi.w #11565,(a0)
loc_0_0000A2FC:
	bne.b loc_0_0000A288
	tst.b $0002(a0)
	bpl.b loc_0_0000A288
	cmp.b $0003(a0),d0
	bne.b loc_0_0000A2FC
	tst.w $0004(a0)
	bne.b loc_0_0000A2FC
	rts
loc_0_0000A312:
	cmp.b #$1,d3
	bne.b loc_0_0000A2CA
	move.w d2,(a5)+
	bsr.w loc_0_0000A250
	bmi.b loc_0_0000A324
	bsr.b loc_0_0000A36C
	dc.b $07,$FE
loc_0_0000A324:
	ori.w #10240,d0
	moveq.l #-2,d2
	bra.w loc_0_0000A28E
loc_0_0000A32E:
	cmpi.w #3,app_021C(a6)
	beq.w loc_0_0000A288
	cmp.b #$1,d3
	bne.b loc_0_0000A35E
	move.b d2,(a5)+
	bsr.w loc_0_0000A250
	bmi.w loc_0_0000A34C
	bsr.b loc_0_0000A36C
	dc.b $08,$FF
loc_0_0000A34C:
	ori.w #10496,d0
	moveq.l #-1,d2
	bra.w loc_0_0000A28E
	dc.b $94,$AE,$02,$4C,$D4,$8D,$55,$82
loc_0_0000A35E:
	move.b d2,(a5)+
	bsr.w loc_0_0000A250
	bmi.w loc_0_0000A288
	bsr.b loc_0_0000A36C
	dc.b $05,$FF
loc_0_0000A36C:
	tst.b app_0103(a6)
	beq.b loc_0_0000A392
	bsr.w loc_0_0000A208
	movea.l (a7),a1
	move.b (a1)+,(a0)+
	move.b $0146(a6),(a0)+
	move.w d0,(a0)+
	move.b (a1)+,d2
	ext.w d2
	ext.l d2
	add.l app_023C(a6),d2
	add.l a5,d2
	sub.l app_024C(a6),d2
	move.l d2,(a0)+
loc_0_0000A392:
	addq.l #4,a7
	rts
loc_0_0000A396:
	lea.l loc_0_0000A3CC(pc),a0
	cmpi.w #3,app_021C(a6)
	beq.b loc_0_0000A3A6
	lea.l loc_0_0000A3BA(pc),a0
loc_0_0000A3A6:
	rts
loc_0_0000A3A8:
	lea.l loc_0_0000A3DD(pc),a0
	cmpi.w #3,app_021C(a6)
	beq.b loc_0_0000A3A6
	lea.l loc_0_0000A3C9(pc),a0
	rts
loc_0_0000A3BA:
	dc.b "Amiga linkable",$00
loc_0_0000A3C9:
	dc.b $2E,$6F,$00
loc_0_0000A3CC:
	dc.b "Amiga executable",$00
loc_0_0000A3DD:
	dc.b $00,$2F,$08,$12,$D8,$66,$FC,$13,$7C,$00,$2C,$FF,$FF,$20,$5F,$12
	dc.b $D8,$66,$FC,$53,$89,$4E,$75
loc_0_0000A3F4:
	tst.b $0104(a6)
	beq.b loc_0_0000A42C
	lea.l $01A6(a6),a3
loc_0_0000A3FE:
	movea.l (a3),a3
	tst.l $0014(a3)
	bne.b loc_0_0000A40E
	movea.l a3,a0
	bsr.w loc_0_00009D80
	beq.b loc_0_0000A428
loc_0_0000A40E:
	move.w $0012(a3),d0
	cmp.w #$3EA,d0
	beq.b loc_0_0000A424
	cmp.w #$3E9,d0
	bne.b loc_0_0000A428
	addq.l #1,app_0204(a6)
	bra.b loc_0_0000A428
loc_0_0000A424:
	addq.l #1,app_0208(a6)
loc_0_0000A428:
	tst.l (a3)
	bne.b loc_0_0000A3FE
loc_0_0000A42C:
	rts
loc_0_0000A42E:
	bsr.w loc_0_0000B054
	move.l d0,app_020C(a6)
	moveq.l #11,d1
	add.l app_0204(a6),d1
	add.l app_0208(a6),d1
	add.l app_0200(a6),d1
	lsl.l #2,d1
	movea.l a6,a0
	bsr.w loc_0_00008422
	bra.w loc_0_0000A110
loc_0_0000A450:
	move.l app_020C(a6),d2
	bsr.w loc_0_0000B042
	bsr.w loc_0_0000A110
	move.l #$3F1,d1
	bsr.w loc_0_0000A0EE
	moveq.l #9,d1
	add.l app_0204(a6),d1
	add.l app_0208(a6),d1
	add.l app_0200(a6),d1
	bsr.w loc_0_0000A0EE
	moveq.l #0,d1
	bsr.w loc_0_0000A0EE
	move.l #$48454144,d1
	bsr.w loc_0_0000A0EE
	move.l #$44424756,d1
	bsr.w loc_0_0000A0EE
	move.l #$30310000,d1
	bsr.w loc_0_0000A0EE
	move.l app_0210(a6),d1
	bsr.w loc_0_0000A0EE
	move.l app_0214(a6),d1
	bsr.w loc_0_0000A0EE
	move.l app_0200(a6),d1
	bsr.w loc_0_0000A0EE
	lea.l loc_0_0000A522(pc),a2
	bsr.w loc_0_00008A26
	move.l app_0208(a6),d1
	bsr.w loc_0_0000A0EE
	move.l #$3EA,d3
	bsr.w loc_0_0000A4E4
	move.l app_0204(a6),d1
	bsr.w loc_0_0000A0EE
	move.l #$3E9,d3
	bsr.w loc_0_0000A4E4
	bra.w loc_0_0000A0F6
loc_0_0000A4E4:
	tst.b $0104(a6)
	beq.b loc_0_0000A520
	moveq.l #0,d2
	lea.l $01A6(a6),a3
loc_0_0000A4F0:
	movea.l (a3),a3
	tst.l $0014(a3)
	bne.b loc_0_0000A500
	movea.l a3,a0
	bsr.w loc_0_00009D80
	beq.b loc_0_0000A51A
loc_0_0000A500:
	move.w $0012(a3),d0
	cmp.w d0,d3
	bne.b loc_0_0000A51A
	moveq.l #0,d1
	move.b d2,d1
	ror.b #8,d1
	add.l $0020(a3),d1
	move.b d2,-(a7)
	bsr.w loc_0_0000A0EE
	move.b (a7)+,d2
loc_0_0000A51A:
	addq.b #1,d2
	tst.l (a3)
	bne.b loc_0_0000A4F0
loc_0_0000A520:
	rts
loc_0_0000A522:
	dc.b $74,$00,$47,$EE,$01,$A6,$26,$53,$4A,$AB,$00,$14,$66,$08,$20,$4B
	dc.b $61,$00,$F8,$4C,$67,$12,$45,$FA,$00,$16,$20,$6B,$00,$04,$1C,$28
	dc.b $00,$0E,$61,$00,$E7,$54,$52,$02,$4A,$93,$66,$DA,$4E,$75,$72,$00
	dc.b $12,$02,$E0,$19,$D2,$A8,$00,$1C,$2F,$08,$61,$00,$FB,$90,$20,$5F
	dc.b $4E,$75
	dcb.b $40,$01
	dcb.b $17,$00
	dc.b $01
	dcb.b $1F,$00
	dc.b $01
	dcb.b $8,$00
	dcb.b $2E,$01
	dc.b $00
	dcb.b $12,$01
	dcb.b $1A,$00
	dc.b $01,$01,$01,$01,$00,$01
	dcb.b $1A,$00
	dc.b $01,$01,$01,$01,$01
loc_0_0000A664:
	dc.b $80,$81,$82,$83,$84,$85,$86,$87,$88,$89,$8A,$8B,$8C,$8D,$8E,$8F
	dc.b $90,$91,$92,$93,$94,$95,$96,$97,$98,$99,$9A,$9B,$9C,$9D,$9E,$9F
	dc.b $A0,$A1,$A2,$A3,$A4,$A5,$A6,$A7,$A8,$A9,$AA,$AB,$AC,$AD,$AE,$AF
	dc.b $B0,$B1,$B2,$B3,$B4,$B5,$B6,$B7,$B8,$B9,$BA,$BB,$BC,$BD,$BE,$BF
	dc.b $C0,$C1,$C2,$C3,$C4,$C5,$C6,$C7,$C8,$C9,$CA,$CB,$CC,$CD,$CE,$CF
	dc.b $D0,$D1,$D2,$D3,$D4,$D5,$D6,$D7,$D8,$D9,$DA,$DB,$DC,$DD,$DE,$DF
	dc.b $C0,$C1,$C2,$C3,$C4,$C5,$C6,$C7,$C8,$C9,$CA,$CB,$CC,$CD,$CE,$CF
	dc.b $D0,$D1,$D2,$D3,$D4,$D5,$D6,$F7,$D8,$D9,$DA,$DB,$DC,$DD,$DE,$FF
	dc.b $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$0A,$0B,$0C,$0D,$0E,$0F
	dc.b $10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$1A,$1B,$1C,$1D,$1E,$1F
	dc.b $20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$2A,$2B,$2C,$2D,$2E,$2F
	dc.b $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$3A,$3B,$3C,$3D,$3E,$3F
	dc.b $40,$41,$42,$43,$44,$45,$46,$47,$48,$49,$4A,$4B,$4C,$4D,$4E,$4F
	dc.b $50,$51,$52,$53,$54,$55,$56,$57,$58,$59,$5A,$5B,$5C,$5D,$5E,$5F
	dc.b $60,$41,$42,$43,$44,$45,$46,$47,$48,$49,$4A,$4B,$4C,$4D,$4E,$4F
	dc.b $50,$51,$52,$53,$54,$55,$56,$57,$58,$59,$5A,$7B,$7C,$7D,$7E,$7F
loc_0_0000A764:
	dcb.b $2E,$01
	dc.b $FF,$01
	dcb.b $A,$00
	dc.b $01,$01,$01,$01,$01
	dcb.b $1C,$00
	dc.b $01,$01,$01,$01,$00,$01
	dcb.b $1A,$00
	dcb.b $45,$01
	dcb.b $17,$00
	dc.b $01
	dcb.b $1F,$00
	dc.b $01
	dcb.b $8,$00
flush_output_buffer:
	move.l d3,-(a7)
	move.l app_0CDA(a6),d1
	bne.b loc_0_0000A878
	moveq.l #_LVOOutput,d0
	bsr.w call_dos_lvo
	move.l d0,app_0CDA(a6)
	move.l d0,d1
loc_0_0000A878:
	lea.l app_0DF6(a6),a0
	move.l a0,d2
	moveq.l #0,d3
	move.w app_0DEE(a6),d3
	moveq.l #_LVOWrite,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d3
	bsr.w poll_ctrl_c_signal
reset_output_buffer:
	clr.w app_0DEE(a6)
	lea.l app_0DF6(a6),a0
	move.l a0,app_0DF0(a6)
	rts
buffer_output_char:
	cmpi.w #130,app_0DEE(a6)
	beq.b flush_then_buffer_output_char
	movea.l app_0DF0(a6),a0
	move.b d1,(a0)+
	move.l a0,app_0DF0(a6)
	addq.w #1,app_0DEE(a6)
	cmp.b #$A,d1
	beq.b flush_output_buffer
	rts
flush_then_buffer_output_char:
	move.w d1,-(a7)
	bsr.b flush_output_buffer
	move.w (a7)+,d1
	bra.b buffer_output_char
buffer_highlighted_char:
	move.w d1,-(a7)
	lea.l loc_0_0000A8DE(pc),a0
loc_0_0000A8CA:
	move.b (a0)+,d1
	beq.b loc_0_0000A8DA
	bpl.b loc_0_0000A8D2
	move.w (a7),d1
loc_0_0000A8D2:
	move.l a0,-(a7)
	bsr.b buffer_output_char
	movea.l (a7)+,a0
	bra.b loc_0_0000A8CA
loc_0_0000A8DA:
	addq.l #2,a7
	rts
loc_0_0000A8DE:
	dc.b $1B,$5B,$33,$33,$3B,$37,$6D,$FF,$1B,$5B,$30,$6D,$00,$00
write_output_block:
	move.l d1,-(a7)
	exg d3,d1
	move.l a0,d2
	moveq.l #_LVOWrite,d0
	bsr.w call_dos_lvo
	bsr.w poll_ctrl_c_signal
	cmp.l (a7)+,d1
	rts
close_non_stdout_handle:
	cmp.l app_0CDA(a6),d3
	beq.b loc_0_0000A90E
	move.l d3,d1
	moveq.l #_LVOClose,d0
	bsr.w call_dos_lvo
loc_0_0000A90E:
	rts
loc_0_0000A910:
	movea.l (a7)+,a3
	clr.b -$1(a0,d0.l)
	movea.l a0,a4
	moveq.l #MEMF_PUBLIC,d1
	move.l #$1140,d0
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	tst.l d0
	bne.b loc_0_0000A930
	moveq.l #103,d0
	rts
loc_0_0000A930:
	movea.l d0,a6
	addq.l #2,a6
	clr.l $01A2(a6)
	clr.l app_0CDA(a6)
	lea.l loc_0_0000B0A0(pc),a1
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOOpenLibrary(a6)
	movea.l (a7)+,a6
	tst.l d0
	bne.b loc_0_0000A968
	lea.l -$0002(a6),a1
	move.l #$1140,d0
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	moveq.l #127,d0
	rts
loc_0_0000A968:
	move.l d0,app_DOSBase(a6)
	clr.b app_0DF4(a6)
	move.l a4,app_0228(a6)
	move.l a7,app_0CDE(a6)
	move.l #$1140,app_0DEA(a6)
	move.l a3,-(a7)
	bra.w reset_output_buffer
loc_0_0000A986:
	movea.l d2,a0
	cmpi.l #1145394720,(a0)
	bne.b loc_0_0000A9B8
	move.l a0,$01A2(a6)
	clr.l $0012(a0)
	clr.l $0016(a0)
	clr.l $001A(a0)
	clr.l $001E(a0)
	tst.b $0010(a0)
	bne.b loc_0_0000A9B8
	lea.l $0012(a0),a0
	move.l a0,$019A(a6)
	addq.w #4,a0
	move.l a0,$019E(a6)
loc_0_0000A9B8:
	moveq.l #0,d0
	rts
loc_0_0000A9BC:
	movea.l app_0228(a6),a0
	move.b (a0),d0
	cmp.b #$3F,d0
	bne.b loc_0_0000AA08
	lea.l loc_0_0000AAB6(pc),a0
	bsr.w loc_0_00009292
	bsr.w flush_output_buffer
	move.l #MEMF_LOCAL,d1
	bsr.w loc_0_000090BA
	move.l a0,-(a7)
	moveq.l #_LVOInput,d0
	bsr.w call_dos_lvo
	move.l d0,d1
	move.l (a7),d2
	move.l #$100,d3
	moveq.l #_LVORead,d0
	bsr.w call_dos_lvo
	cmp.b #$1,d0
	ble.w loc_0_0000AAAE
	movea.l (a7)+,a0
	move.l a0,app_0228(a6)
	clr.b -$1(a0,d0.w)
loc_0_0000AA08:
	sf.b app_0840(a6)
	sf.b app_0841(a6)
	sf.b app_0842(a6)
	jsr parse_option_source_buffer.l
	clr.b app_071A(a6)
	clr.b app_021B(a6)
	sf.b app_0C26(a6)
	st.b app_0103(a6)
	sf.b app_00FE(a6)
	sf.b app_00FF(a6)
	sf.b $0100(a6)
	lea.l loc_0_0000AAA0(pc),a0
	moveq.l #0,d0
	lea.l app_timer_device_iorequest(a6),a1
	moveq.l #0,d0
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOOpenDevice(a6)
	movea.l (a7)+,a6
	tst.b d0
	bne.b loc_0_0000AA70
	movea.l app_TimerBase(a6),a0
	cmpi.w #36,LIB_VERSION(a0)
	bcs.w loc_0_0000AA70
	lea.l app_10A8(a6),a0
	pea.l (a6)
	movea.l app_TimerBase(a6),a6
	jsr _LVOGetSysTime(a6)
	movea.l (a7)+,a6
loc_0_0000AA70:
	move.w #$3,app_021C(a6)
	clr.l app_022C(a6)
	clr.l app_0230(a6)
	tst.l $01A2(a6)
	bne.b loc_0_0000AA9C
	lea.l loc_0_0000AAF4(pc),a0
	bsr.w loc_0_0000B0AC
	bne.b loc_0_0000AA98
	lea.l loc_0_0000AAE9(pc),a0
	bsr.w loc_0_0000B0AC
	beq.b loc_0_0000AA9C
loc_0_0000AA98:
	move.l a0,app_022C(a6)
loc_0_0000AA9C:
	moveq.l #0,d0
	rts
loc_0_0000AAA0:
	dc.b "timer.device",$00
	dc.b $00
loc_0_0000AAAE:
	bsr.w loc_0_000090F2
	bra.w loc_0_0000ACA4
loc_0_0000AAB6:
	dc.b "FROM/A,TO/K,WITH/K,INCDIR/K/M,HEADER/K/M,QUIET/S: ",$00
loc_0_0000AAE9:
	dc.b $45,$4E,$56,$3A,$64,$65,$76,$70,$61,$63,$2F
loc_0_0000AAF4:
	dc.b "genam.opts",$00
	dc.b $00
parse_option_source_buffer:
	movea.l app_0228(a6),a4
	bra.w parse_option_source_loop
parse_input_source_buffer:
	move.l app_0230(a6),d0
	bra.b loc_0_0000AB12
parse_startup_options_buffer:
	move.l app_022C(a6),d0
loc_0_0000AB12:
	beq.b loc_0_0000AB28
	movea.l d0,a4
parse_option_source_loop:
	jsr loc_0_00003A6C.l
	bne.w loc_0_0000AB28
	tst.b d1
	beq.b loc_0_0000AB28
	move.b (a4),d1
	bne.b parse_option_source_loop
loc_0_0000AB28:
	rts
loc_0_0000AB2A:
	rts
open_output_file:
	move.l a0,d1
	move.l #MODE_NEWFILE,d2
	move.l d3,-(a7)
	moveq.l #0,d3
	moveq.l #_LVOOpen,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d3
	tst.l d0
	beq.w loc_0_0000AB4A
	move.l d0,app_0956(a6)
loc_0_0000AB4A:
	eori #4,ccr
	rts
loc_0_0000AB50:
	tst.b app_0955(a6)
	beq.b loc_0_0000AB84
loc_0_0000AB56:
	tst.w app_0B68(a6)
	bmi.b loc_0_0000AB84
	moveq.l #10,d1
	bsr.w loc_0_0000917C
	move.l app_0956(a6),d1
	cmp.l app_0CDA(a6),d1
	beq.b loc_0_0000AB7A
	cmpi.w #10752,app_078E(a6)
	beq.b loc_0_0000AB7A
	moveq.l #12,d1
	bsr.w loc_0_0000917C
loc_0_0000AB7A:
	clr.w app_0B66(a6)
	move.w #$FFFF,app_0B68(a6)
loc_0_0000AB84:
	rts
poll_ctrl_c_signal:
	movem.l d0-d2/a0-a2,-(a7)
	moveq.l #0,d0
	moveq.l #0,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSetSignal(a6)
	movea.l (a7)+,a6
	btst #12,d0
	beq.b loc_0_0000ABBA
	ori.b #127,app_0115(a6)
	moveq.l #0,d0
	move.l #SIGBREAKF_CTRL_C,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOSetSignal(a6)
	movea.l (a7)+,a6
loc_0_0000ABBA:
	movem.l (a7)+,d0-d2/a0-a2
loc_0_0000ABBE:
	rts
loc_0_0000ABC0:
	tst.b $0127(a6)
	bne.b loc_0_0000ABBE
	move.l app_0DEA(a6),d1
	bsr.w loc_0_00008F04
	lea.l loc_0_0000AC70(pc),a0
	bsr.w loc_0_00009292
	tst.b app_timer_device_iorequest+IO_ERROR(a6)
	bne.w loc_0_0000AC68
	movea.l app_TimerBase(a6),a0
	cmpi.w #36,LIB_VERSION(a0)
	bcs.w loc_0_0000AC58
	lea.l app_10B0(a6),a0
	pea.l (a6)
	movea.l app_TimerBase(a6),a6
	jsr _LVOGetSysTime(a6)
	movea.l (a7)+,a6
	lea.l app_10B0(a6),a0
	lea.l app_10A8(a6),a1
	pea.l (a6)
	movea.l app_TimerBase(a6),a6
	jsr _LVOSubTime(a6)
	movea.l (a7)+,a6
	lea.l loc_0_0000AC7C(pc),a0
	bsr.w loc_0_00009292
	move.l app_10B0(a6),d1
	bsr.w loc_0_00008F04
	moveq.l #46,d1
	bsr.w loc_0_00009288
	clr.l -(a7)
	clr.l -(a7)
	move.l #$30303030,d0
	move.l d0,-(a7)
	move.w d0,-(a7)
	lea.l $0006(a7),a3
	lea.l loc_0_0000AC6C(pc),a2
	move.l app_10B0+TV_MICRO(a6),d1
	bsr.w loc_0_00008F08
	lea.l -$0006(a3),a0
	bsr.w loc_0_00009292
	lea.l $000E(a7),a7
	lea.l loc_0_0000AC84(pc),a0
	bsr.w loc_0_00009292
loc_0_0000AC58:
	lea.l app_timer_device_iorequest(a6),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOCloseDevice(a6)
	movea.l (a7)+,a6
loc_0_0000AC68:
	bra.w loc_0_00008E8C
loc_0_0000AC6C:
	dc.b $16,$C1,$4E,$75
loc_0_0000AC70:
	dc.b " bytes used",$00
loc_0_0000AC7C:
	dc.b ", took ",$00
loc_0_0000AC84:
	dc.b " seconds",$00
loc_0_0000AC8D:
	dc.b "Press any key to exit",$00
	dc.b $00
loc_0_0000ACA4:
	bsr.w flush_output_buffer
	tst.b app_0C26(a6)
	beq.b loc_0_0000ACC2
	lea.l loc_0_0000AC8D(pc),a0
	move.l a0,d2
	moveq.l #21,d3
	move.l app_0CDA(a6),d1
	moveq.l #_LVOWrite,d0
	bsr.w call_dos_lvo
	bsr.b read_input_char
loc_0_0000ACC2:
	movea.l app_0CDE(a6),a7
	movea.l app_DOSBase(a6),a1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOCloseLibrary(a6)
	movea.l (a7)+,a6
	move.b app_023A(a6),d4
	lea.l -$0002(a6),a1
	move.l #$1140,d0
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	move.b d4,d0
	ext.w d0
	ext.l d0
	rts
read_input_char:
	moveq.l #_LVOInput,d0
	bsr.w call_dos_lvo
	move.l d0,d1
	clr.w -(a7)
	move.l a7,d2
	moveq.l #1,d3
	moveq.l #_LVORead,d0
	bsr.w call_dos_lvo
	move.b (a7)+,d1
	rts
loc_0_0000AD0C:
	lea.l -$000C(a7),a7
	move.l a7,d1
	move.l #_LVODateStamp,d0
	bsr.w call_dos_lvo
	move.l (a7),d0
	lea.l $000C(a7),a7
	divu.w #$5B5,d0
	add.w d0,d0
	add.w d0,d0
	addi.w #78,d0
	move.w d0,d1
	swap.w d0
loc_0_0000AD32:
	tst.w d0
	beq.b loc_0_0000AD52
	move.w #$16D,d2
	btst #1,d1
	bne.b loc_0_0000AD48
	btst #0,d1
	bne.b loc_0_0000AD48
	addq.w #1,d2
loc_0_0000AD48:
	cmp.w d2,d0
	blt.b loc_0_0000AD52
	sub.w d2,d0
	addq.w #1,d1
	bra.b loc_0_0000AD32
loc_0_0000AD52:
	addq.w #1,d0
	lea.l loc_0_0000ADD2(pc),a0
	moveq.l #1,d4
loc_0_0000AD5A:
	moveq.l #0,d2
	move.b (a0)+,d2
	cmp.b #$2,d4
	bne.b loc_0_0000AD72
	btst #0,d1
	bne.b loc_0_0000AD72
	btst #1,d1
	bne.b loc_0_0000AD72
	addq.w #1,d2
loc_0_0000AD72:
	cmp.w d2,d0
	ble.b loc_0_0000AD80
	sub.w d2,d0
	addq.w #1,d4
	cmp.w #$D,d4
	bne.b loc_0_0000AD5A
loc_0_0000AD80:
	move.w d1,-(a7)
	move.w d4,d1
	add.w d1,d1
	add.w d4,d1
	lea.l loc_0_0000ADDB(pc,d1.w),a0
	move.w (a7)+,d1
	move.b (a0)+,(a3)+
	move.b (a0)+,(a3)+
	move.b (a0)+,(a3)+
	move.b #$20,(a3)+
	cmp.w #$A,d0
	blt.b loc_0_0000ADA2
	bsr.b loc_0_0000ADBC
	bra.b loc_0_0000ADA4
loc_0_0000ADA2:
	bsr.b loc_0_0000ADCA
loc_0_0000ADA4:
	move.b #$20,(a3)+
	move.w d1,d0
	ext.l d0
	addi.w #1900,d0
	divu.w #$64,d0
	move.l d0,d1
	bsr.b loc_0_0000ADBC
	move.l d1,d0
	swap.w d0
loc_0_0000ADBC:
	swap.w d0
	clr.w d0
	swap.w d0
	divu.w #$A,d0
	bsr.b loc_0_0000ADCA
	swap.w d0
loc_0_0000ADCA:
	addi.b #48,d0
	move.b d0,(a3)+
	rts
loc_0_0000ADD2:
	dc.b $1F,$1C,$1F,$1E,$1F,$1E,$1F,$1F,$1E
loc_0_0000ADDB:
	dc.b $1F,$1E,$1F,$4A,$61,$6E,$46,$65,$62,$4D,$61,$72,$41,$70,$72,$4D
	dc.b $61,$79,$4A,$75,$6E,$4A,$75,$6C,$41,$75,$67,$53,$65,$70,$4F,$63
	dc.b $74,$4E,$6F,$76,$44,$65,$63
loc_0_0000AE02:
	addq.l #8,d1
	movem.l d1/a1,-(a7)
	rol.w #3,d0
	andi.l #6,d0
	ori.l #65537,d0
	exg d0,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,d1/a1
	tst.l d0
	beq.b loc_0_0000AE3E
	movea.l d0,a0
	move.l d1,(a0)+
	lsr.l #2,d0
	addq.l #1,d0
	move.l d0,(a4)
	movea.l a0,a4
	clr.l (a0)+
	moveq.l #0,d0
	rts
loc_0_0000AE3E:
	moveq.l #-1,d0
	rts
loc_0_0000AE42:
	addq.l #4,d1
	move.l d1,-(a7)
	move.l d1,d0
	moveq.l #MEMF_PUBLIC,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d1
	tst.l d0
	beq.b loc_0_0000AE64
	movea.l d0,a0
	move.l d1,(a0)+
	add.l d1,app_0DEA(a6)
loc_0_0000AE64:
	rts
loc_0_0000AE66:
	movea.l a0,a1
	move.l -(a1),d0
	sub.l d0,app_0DEA(a6)
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	rts
loc_0_0000AE7C:
	lea.l $0016(a1),a0
	moveq.l #0,d0
	move.b (a0)+,d0
	lea.l -$1(a0,d0.w),a1
	clr.b (a1)
	move.l a1,-(a7)
	bsr.b loc_0_0000AEB4
	movea.l (a7)+,a1
	move.b #$B,(a1)
	tst.l d4
	eori #4,ccr
	rts
loc_0_0000AE9C:
	movem.l d1/a0,-(a7)
loc_0_0000AEA0:
	move.b (a0)+,d1
	cmp.b #$3A,d1
	beq.b loc_0_0000AEAE
	tst.b d1
	bne.b loc_0_0000AEA0
	moveq.l #-1,d1
loc_0_0000AEAE:
	movem.l (a7)+,d1/a0
loc_0_0000AEB2:
	rts
loc_0_0000AEB4:
	bsr.b loc_0_0000AE9C
	beq.b loc_0_0000AEFE
	move.l a0,-(a7)
	bsr.w loc_0_0000AEFE
	movea.l (a7)+,a0
	tst.l d4
	bne.b loc_0_0000AEB2
	movea.l app_0C2C(a6),a2
	move.l a0,-(a7)
loc_0_0000AECA:
	move.b (a0)+,(a2)+
	bne.b loc_0_0000AECA
	move.l app_0832(a6),-(a7)
	lea.l app_0C30(a6),a0
loc_0_0000AED6:
	bsr.b loc_0_0000AEFE
	movea.l (a7)+,a1
	movea.l (a7)+,a0
	tst.l d4
	bne.b loc_0_0000AEFC
	tst.b (a1)
	beq.b loc_0_0000AEFC
	move.l a0,-(a7)
	lea.l app_0E78(a6),a2
loc_0_0000AEEA:
	move.b (a1)+,(a2)+
	bne.b loc_0_0000AEEA
	subq.l #1,a2
loc_0_0000AEF0:
	move.b (a0)+,(a2)+
	bne.b loc_0_0000AEF0
	move.l a1,-(a7)
	lea.l app_0E78(a6),a0
	bra.b loc_0_0000AED6
loc_0_0000AEFC:
	rts
loc_0_0000AEFE:
	tst.b $010A(a6)
	beq.b loc_0_0000AF28
	lea.l app_10E8(a6),a2
	move.l a0,-(a7)
loc_0_0000AF0A:
	move.b (a0)+,(a2)+
	bne.b loc_0_0000AF0A
	lea.l app_10E8(a6),a0
	lea.l loc_0_00009656(pc),a2
	bsr.w loc_0_000045CE
	bsr.w loc_0_0000AF28
	movea.l (a7)+,a0
	tst.l d4
	beq.b loc_0_0000AF28
	neg.l d1
	rts
loc_0_0000AF28:
	move.l a0,-(a7)
	move.l a0,d1
	move.l #MODE_OLDFILE,d2
	moveq.l #_LVOOpen,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d1
	move.l d0,d4
	beq.w loc_0_0000AFB6
	move.l $01A2(a6),d0
	beq.b loc_0_0000AF52
	movea.l d0,a0
	tst.l $0008(a0)
	beq.b loc_0_0000AF52
	moveq.l #-1,d1
	rts
loc_0_0000AF52:
	move.l d4,-(a7)
	moveq.l #ACCESS_READ,d2
	moveq.l #_LVOLock,d0
	bsr.w call_dos_lvo
	move.l d0,d4
	beq.w loc_0_0000AF8A
	move.l d0,d1
	lea.l app_0CE2(a6),a0
	move.l a0,d2
	move.l d2,d0
	andi.b #3,d0
	beq.b loc_0_0000AF78
	andi.b #252,d2
	addq.l #4,d2
loc_0_0000AF78:
	moveq.l #_LVOExamine,d0
	bsr.w call_dos_lvo
	move.l d0,-(a7)
	move.l d4,d1
	moveq.l #_LVOUnLock,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d0
loc_0_0000AF8A:
	movem.l (a7)+,d4
	beq.b loc_0_0000AFAC
	lea.l app_0CE2(a6),a0
	move.l a0,d0
	move.l d0,d2
	andi.b #3,d2
	beq.b loc_0_0000AFA4
	andi.b #252,d0
	addq.l #4,d0
loc_0_0000AFA4:
	movea.l d0,a0
	move.l $007C(a0),d1
	bne.b loc_0_0000AFB6
loc_0_0000AFAC:
	move.l d4,d1
	moveq.l #_LVOClose,d0
	bsr.w call_dos_lvo
	moveq.l #0,d4
loc_0_0000AFB6:
	rts
loc_0_0000AFB8:
	move.l d2,d1
	moveq.l #_LVOClose,d0
	bsr.w call_dos_lvo
	rts
loc_0_0000AFC2:
	move.l d3,-(a7)
	move.l d1,d3
	move.l d2,d1
	move.l a0,d2
	moveq.l #_LVORead,d0
	bsr.w call_dos_lvo
	tst.l d0
	bmi.b loc_0_0000AFD8
	move.l d0,d1
	moveq.l #0,d0
loc_0_0000AFD8:
	movem.l (a7)+,d3
	rts
loc_0_0000AFDE:
	move.l d4,-(a7)
	bsr.w loc_0_0000AEB4
	move.l d1,d2
	move.l d4,d3
	movem.l (a7)+,d4
	eori #4,ccr
	rts
loc_0_0000AFF2:
	move.l d3,d2
	bra.b loc_0_0000AFB8
loc_0_0000AFF6:
	exg d3,d1
	move.l a0,d2
	moveq.l #_LVORead,d0
	bsr.w call_dos_lvo
	rts
loc_0_0000B002:
	move.l a0,d1
	move.l #MODE_NEWFILE,d2
	move.l d3,-(a7)
	moveq.l #-1,d3
	moveq.l #_LVOOpen,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d3
	tst.l d0
	beq.b loc_0_0000B020
	move.l d0,d2
	moveq.l #0,d0
	rts
loc_0_0000B020:
	moveq.l #-1,d0
	rts
loc_0_0000B024:
	tst.l d1
	beq.b loc_0_0000B040
	movem.l d1-d3,-(a7)
	move.l d1,d3
	move.l $0186(a6),d1
	move.l a0,d2
	moveq.l #_LVOWrite,d0
	bsr.w call_dos_lvo
	movem.l (a7)+,d1-d3
	cmp.l d0,d1
loc_0_0000B040:
	rts
loc_0_0000B042:
	move.l d3,-(a7)
	moveq.l #OFFSET_BEGINNING,d3
	move.l $0186(a6),d1
	moveq.l #_LVOSeek,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d3
	rts
loc_0_0000B054:
	move.l d3,-(a7)
	move.l $0186(a6),d1
	moveq.l #0,d2
	moveq.l #OFFSET_CURRENT,d3
	moveq.l #_LVOSeek,d0
	bsr.w call_dos_lvo
	move.l (a7)+,d3
	rts
loc_0_0000B068:
	tst.b app_021B(a6)
	bne.b loc_0_0000B09A
	movem.l d1-d2/a0-a2,-(a7)
	move.l #MEMF_LARGEST|MEMF_PUBLIC,d1
	move.l a6,-(a7)
	movea.l $0004.w,a6
	jsr _LVOAvailMem(a6)
	movea.l (a7)+,a6
	movem.l (a7)+,d1-d2/a0-a2
	cmp.l #$7D00,d0
	bcs.b loc_0_0000B096
	asr.l #1,d0
	cmp.l d0,d1
	bcs.b loc_0_0000B098
loc_0_0000B096:
	move.l d2,d1
loc_0_0000B098:
	rts
loc_0_0000B09A:
	cmp.l d2,d1
	ble.b loc_0_0000B098
	bra.b loc_0_0000B096
loc_0_0000B0A0:
	dc.b "dos.library",$00
loc_0_0000B0AC:
	bsr.w loc_0_0000AF28
	tst.l d4
	beq.b loc_0_0000B0D4
	move.l d1,d5
	addq.l #1,d1
	bsr.w loc_0_000090BA
	move.l d5,d1
	move.l d4,d3
	move.l a0,-(a7)
	bsr.w loc_0_0000AFF6
	move.l d4,d3
	bsr.w loc_0_0000AFF2
	movea.l (a7)+,a0
	clr.b $0(a0,d5.l)
	tst.l d5
loc_0_0000B0D4:
	rts
call_dos_lvo:
	move.l a6,-(a7)
	tst.l $01A2(a6)
	beq.b loc_0_0000B0F0
	movea.l $01A2(a6),a0
	movea.l $0004(a0),a0
	movea.l app_DOSBase(a6),a6
	jsr (a0)
	movea.l (a7)+,a6
	rts
loc_0_0000B0F0:
	movea.l app_DOSBase(a6),a6
	jsr $0(a6,d0.w)
	movea.l (a7)+,a6
	rts
	dc.b $4A,$2E,$0D,$F4,$66,$22,$48,$E7,$80,$80,$20,$78,$00,$04,$10,$28
	dc.b $01,$29,$08,$00,$00,$04,$67,$12,$08,$00,$00,$01,$67,$0C,$1D,$7C
	dc.b $00,$01,$0D,$F4,$4C,$DF,$01,$01,$4E,$75,$70,$60,$60,$00,$D3,$44
	dc.b $4A,$45,$67,$36,$61,$CA,$F2,$3C,$88,$00,$00,$00,$00,$00,$BA,$7C
	dc.b $00,$0A,$64,$00,$00,$56,$CA,$FC,$03,$E8,$08,$10,$00,$06,$67,$02
	dc.b $44,$45,$F2,$3C,$50,$80,$00,$01,$F2,$05,$50,$92,$F2,$10,$4C,$00
	dc.b $F2,$00,$04,$23,$60,$00,$00,$1E,$4E,$75,$70,$05,$3F,$00,$61,$90
	dc.b $F2,$3C,$88,$00,$00,$00,$00,$00,$30,$1F,$48,$80,$C0,$FC,$00,$06
	dc.b $61,$00,$00,$20,$30,$03,$D0,$40,$D0,$43,$D0,$40,$61,$00,$00,$18
	dc.b $F2,$00,$A8,$00,$08,$00,$00,$06,$67,$04,$70,$63,$4E,$75,$70,$00
	dc.b $4E,$75,$4E,$FB,$00,$2A,$4E,$FB,$00,$FC,$F2,$10,$78,$00,$4E,$75
	dc.b $F2,$10,$70,$00,$4E,$75,$F2,$10,$60,$00,$4E,$75,$F2,$10,$74,$00
	dc.b $4E,$75,$F2,$10,$6C,$00,$4E,$75,$F2,$10,$64,$00,$4E,$75,$F2,$10
	dc.b $68,$00,$4E,$75,$F2,$10,$58,$00,$4E,$75,$F2,$10,$50,$00,$4E,$75
	dc.b $F2,$10,$40,$00,$4E,$75,$F2,$10,$54,$00,$4E,$75,$F2,$10,$4C,$00
	dc.b $4E,$75,$F2,$10,$44,$00,$4E,$75,$F2,$10,$48,$00,$4E,$75,$3F,$03
	dc.b $61,$00,$FE,$FE,$F2,$3C,$88,$00,$00,$00,$00,$00,$36,$1F,$48,$83
	dc.b $30,$03,$D0,$40,$D0,$43,$D0,$40,$61,$88,$F2,$00,$00,$1A,$60,$00
	dc.b $FF,$6C
loc_0_0000B21E:
	dc.b $00,$00,$00,$00,$00,$6E,$00,$76,$00,$D6,$00,$FC,$00,$EE,$01,$62
	dc.b $01,$84,$00,$86,$01,$D0,$01,$DC,$01,$CE,$01,$D8,$02,$46,$02,$52
	dc.b $02,$B8,$03,$26,$00,$1C,$00,$80,$00,$34,$00,$36,$00,$A2,$00,$E0
	dc.b $03,$8A,$00,$98,$03,$52,$01,$E4,$00,$F6,$00,$F2,$03,$8C,$01,$02
	dc.b $01,$0C,$01,$08,$01,$56,$02,$34,$01,$48,$01,$CE,$01,$5E,$01,$5C
	dc.b $01,$5C,$01,$6A,$01,$CA,$01,$D4,$01,$FC,$02,$38,$02,$5A,$02,$3E
	dc.b $03,$F0,$02,$64,$02,$48,$00,$00,$02,$50,$02,$78,$02,$68,$02,$6C
	dc.b $02,$C0,$02,$D0,$04,$1C,$04,$6E,$02,$FC,$04,$98,$03,$3E,$02,$C4
	dc.b $02,$C0,$02,$DC,$03,$1E,$03,$8A,$03,$A2,$03,$3A,$04,$FA,$04,$7E
	dc.b $03,$90,$05,$22,$03,$A2,$03,$AC,$03,$C8,$03,$B2,$03,$BA,$03,$E4
	dc.b $04,$0C,$03,$EE,$03,$F0,$04,$3A,$04,$14,$03,$FA,$04,$DE,$04,$14
	dc.b $04,$2A,$04,$26,$05,$46,$04,$42,$04,$3E,$05,$24,$04,$4E,$04,$A2
	dc.b $05,$7E,$04,$8C,$04,$AC,$04,$B6,$05,$6A,$04,$C0,$04,$EE,$05,$D8
	dc.b $05,$6E,$05,$0E,$05,$12,$05,$6E,$05,$CA,$05,$CE,$05,$EE,$05,$80
	dc.b $05,$DA,$05,$E2,$00,$00,$06,$04,$05,$EA,$06,$38,$05,$86,$06,$02
	dc.b $06,$52,$06,$06,$06,$56,$06,$56,$06,$60,$06,$40,$06,$50,$06,$68
	dc.b $06,$5E,$06,$50,$00,$00,$06,$6A,$06,$64,$06,$A2,$06,$66,$06,$70
	dc.b $06,$CE,$06,$7C,$06,$5C,$06,$6E,$06,$BC,$06,$D8,$06,$82,$06,$9A
	dc.b $06,$CE,$07,$22,$06,$CE,$00,$00,$00,$00,$00,$00,$06,$E4,$06,$D8
	dc.b $00,$00,$00,$00,$06,$EE,$06,$D0,$07,$00,$06,$F2,$07,$06,$07,$06
	dc.b $00,$00,$07,$3A,$00,$00,$00,$00,$07,$20
	dcb.b $E,$00
	dc.b $07,$22,$00,$00,$00,$00,$07,$2C,$00,$00,$00,$00,$07,$3E,$07,$4A
	dc.b $00,$02,$00,$04,$07,$2E,$00,$00,$07,$8A,$07,$3E,$07,$56,$07,$48
	dc.b $07,$40,$07,$62,$07,$68,$07,$6A,$07,$50,$00,$00,$07,$84,$07,$9C
	dc.b $07,$AC,$07,$66,$07,$70,$07,$64,$07,$7C,$00,$00,$07,$BA,$00,$00
	dc.b $07,$9E,$07,$7C,$07,$D0,$07,$C6,$07,$D4,$07,$BE,$00,$00,$07,$E2
	dc.b $07,$C2,$07,$D2,$07,$EA,$07,$E2,$07,$EA,$07,$FC,$07,$E4,$00,$00
	dc.b $08,$04,$08,$1A,$08,$3A,$08,$28,$08,$4A,$00,$00,$08,$60,$08,$2A
	dc.b $08,$32,$08,$56,$08,$B4,$08,$4E,$08,$36,$08,$4A,$08,$66,$08,$64
	dc.b $08,$50,$08,$86,$08,$84,$08,$8E,$08,$B6,$08,$C2,$08,$B0,$08,$C6
	dc.b $08,$B6,$08,$B8,$08,$C8,$08,$CC,$09,$20,$08,$E8,$08,$DE,$08,$D2
	dc.b $00,$00,$09,$22,$08,$DC,$09,$2C,$09,$1E,$09,$36,$09,$38,$09,$1A
	dc.b $09,$8C,$00,$00,$09,$A2,$09,$26,$09,$36,$09,$58,$09,$36,$09,$42
	dc.b $09,$3A,$00,$00,$00,$00,$09,$48,$09,$9A,$09,$A8,$09,$BE,$00,$00
	dc.b $09,$6E,$09,$C6,$00,$00,$00,$00,$00,$00,$09,$A6,$09,$98,$09,$B0
	dc.b $09,$AA,$00,$00,$00,$00,$0A,$04,$09,$C8,$09,$B2,$09,$D6,$09,$FC
	dc.b $09,$E2,$09,$C8,$0A,$04,$0A,$16,$00,$00,$09,$FE,$00,$00,$00,$00
	dc.b $00,$00,$0A,$0C,$0A,$18,$0A,$26,$0A,$2C,$0A,$34,$0A,$36,$0A,$38
	dc.b $0A,$3A,$0A,$44,$0A,$6E,$0A,$70,$0A,$A0,$00,$00,$0A,$18,$0A,$28
	dc.b $0A,$44,$0A,$46,$0A,$20,$0A,$28,$0A,$A6,$0A,$8A,$0A,$A2,$0A,$B4
	dc.b $0A,$B6,$0A,$B8,$0A,$BA,$0A,$C4,$0A,$72,$0A,$C0,$0A,$AC,$0A,$E2
	dc.b $00,$00,$0A,$CE,$0B,$06,$00,$00,$0B,$06,$0A,$FE,$0B,$0E,$0B,$1A
	dcb.b $A,$00
	dc.b $0B,$1E,$00,$00,$00,$00,$0B
	dcb.b $19,$00
	dc.b $0B,$0C,$0B,$48,$00,$00,$00,$00,$0B,$0E,$00,$00,$0B,$14,$00,$00
	dc.b $00,$00,$0B,$06,$00,$00,$0B,$14
	dcb.b $10,$00
	dc.b $0B,$1E,$0B,$38,$0B,$32,$0B,$2E,$00,$00,$0B,$28
	dcb.b $8,$00
	dc.b $0B,$36,$0B,$38,$0B,$46,$0B,$50
	dcb.b $10,$00
	dc.b $0B,$66,$0B,$52,$0B,$68,$0B,$76,$0B,$70,$0B,$70,$0B,$7A
	dcb.b $8,$00
	dc.b $0B,$8A,$0B,$80,$00,$00,$00,$00,$0B,$A6
	dcb.b $C,$00
	dc.b $0B,$A2,$0B,$9E,$0B,$8A
	dcb.b $20,$00
	dc.b $0B,$A2,$0B,$A4,$0B,$AE,$00,$00,$0B,$B6,$00,$00,$00,$00,$00,$00
	dc.b $0B,$A8
	dcb.b $A,$00
	dc.b $0B,$A2,$00,$00,$00,$00,$0B,$AE,$0B,$B0,$00,$00,$00,$00,$0B,$C4
	dcb.b $8,$00
	dc.b $0B,$C8,$0B,$D0,$0C,$06,$0B,$EC,$00,$00,$0B,$BA,$00,$00,$0B,$E0
	dc.b $00,$00,$0B,$D2,$0C,$18,$0C,$1A,$00,$00,$00,$00,$0C,$06,$0B,$F2
	dc.b $0C,$1E,$0C,$06,$00,$00,$0C,$22,$0C,$32,$0C,$3A,$0C,$52,$0C,$30
	dc.b $0C,$8A,$00,$00,$0C,$94,$0C,$12,$00,$00,$0C,$1A,$0C,$34,$0C,$40
	dc.b $0C,$38,$0C,$70,$00,$00,$0C,$48,$0C,$8E,$0C,$6C,$0C,$D8,$00,$00
	dc.b $0C,$9A
	dcb.b $8,$00
	dc.b $0C,$AC,$00,$00,$0C,$96,$0C,$9A,$0C,$BA,$0C,$BA,$0C,$AE,$0C,$9C
	dc.b $00,$00,$00,$00,$0C,$C2,$00,$00,$0C,$DA,$00,$00,$00,$00,$0C,$A2
	dc.b $0C,$BA,$0C,$CC,$0D,$06,$0C,$EC,$0D,$18,$0C,$EE,$00,$00,$0C,$D2
	dc.b $0C,$DA,$00,$00,$0D,$0E,$0D,$00,$00,$00,$0D,$22,$00,$00,$0D,$06
	dc.b $0D,$22,$0D,$34,$00,$00,$0D,$22,$0D,$1A,$0D,$24,$00,$00,$0D,$1E
	dcb.b $12,$00
	dc.b $0D,$3A,$0D,$3A,$0D,$3C,$0D,$28,$00,$00,$0D,$54,$00,$00,$0D,$42
	dc.b $0D,$58,$0D,$56,$0D,$4E,$0D,$60,$0D,$BC
	dcb.b $8,$00
	dc.b $0D,$54,$0D,$6E,$0D,$86,$0D,$6A
	dcb.b $24,$00
	dc.b $0D,$9E,$0D,$A0,$0D,$A2,$0D,$A6,$0D,$A8,$0D,$AC,$0D,$BA,$0D,$C4
	dc.b $0D,$72,$00,$00,$0D,$A8,$0D,$EC,$0D,$EA,$0D,$CE,$00,$00,$00,$00
	dc.b $0D,$EE
	dcb.b $1C,$00
	dc.b $0D,$D2,$0D,$DC,$0E,$02,$0D,$E8,$00,$00,$0D,$FC,$00,$00,$00,$00
	dc.b $00,$00,$0E,$00,$0E,$00,$00,$00,$0E,$1A
	dcb.b $8,$00
	dc.b $0E,$06,$00,$00,$00,$00,$0E,$14,$0E,$16,$0E,$18,$00,$00,$00,$00
	dc.b $0E,$7A
	dcb.b $C,$00
	dc.b $0E,$36
	dcb.b $12,$00
	dc.b $0E,$30,$0E,$5C,$00,$00,$00,$00,$00,$00,$0E,$42,$00,$00,$0E,$3E
	dc.b $00,$00,$00,$00,$0E,$66,$00,$00,$00,$00,$0E,$6E
	dcb.b $28,$00
	dc.b $0E,$70
	dcb.b $8,$00
	dc.b $0E,$9A,$0E,$86,$0E,$A6,$0E,$C2,$00,$00,$0E,$76,$00,$00,$0E,$9E
	dc.b $00,$00,$0E,$8A,$0E,$D2,$0E,$D4,$00,$00,$00,$00,$0E,$D6,$00,$00
	dc.b $00,$00,$0E,$CC,$00,$00,$0E,$DC,$0E,$C8,$0E,$FE,$0E,$D0,$00,$0A
	dc.b $00,$00,$0E,$E6,$0F,$0A,$0E,$E0,$0E,$EC,$00,$00,$00,$00,$00,$00
	dc.b $0F,$08,$00,$00,$0F,$02,$00,$00,$0E,$EC,$0E,$FA,$00,$00,$0F,$10
	dc.b $00,$00,$00,$00,$00,$00,$0F,$18
	dcb.b $16,$00
	dc.b $0E,$FE
	dcb.b $E,$00
	dc.b $0F,$0A,$0F,$52,$0F,$0E,$0F,$30,$0F,$22,$0F,$1E,$0F,$44,$0F,$3E
	dc.b $0F,$54,$0F,$5A,$00,$00,$00,$00,$0F,$76,$00,$02
	dcb.b $C,$00
	dc.b $0F,$5C,$0F,$7C,$0F,$60,$0F,$62
	dcb.b $20,$00
	dc.b $0F,$80,$0F,$74,$00,$00,$00,$00,$0F,$86,$0F,$76,$00,$00,$0F,$76
	dc.b $0F,$DA,$0F,$8E,$00,$00,$00,$00,$0F,$9C,$00,$00,$0F,$A0,$0F,$AA
	dcb.b $8,$00
	dc.b $0F,$C8,$00,$00,$00,$00,$0F,$A4
	dcb.b $12,$00
	dc.b $0F,$E0
	dcb.b $23,$00
	dc.b $0E,$0F,$D0,$0F,$D8,$00,$00,$00,$00,$00,$10,$0F,$D2,$00,$00,$00
	dc.b $00,$0F,$D4,$00,$00,$0F,$CE,$0F,$E4,$0F,$DE,$00,$00,$00,$00,$00
	dc.b $00,$0F,$D6,$0F,$E8,$00,$00,$10,$34,$10,$1A,$10,$0A,$10,$02,$10
	dc.b $54,$00,$00,$10,$5E,$0F,$E2,$0F,$FE,$00,$00,$00,$00,$10,$44,$10
	dc.b $68,$00,$00,$10,$64
	dcb.b $C,$00
	dc.b $10,$7E,$00,$00,$00,$00,$10,$6A,$10,$50,$00,$00,$00,$00,$10,$72
	dc.b $10,$80,$10,$B8,$10,$C2,$10,$C4,$10,$C6,$10,$C8,$10,$CA,$00,$00
	dc.b $10,$5C,$10,$76
	dcb.b $10,$00
	dc.b $10,$8A
	dcb.b $C,$00
	dc.b $10,$8C
	dcb.b $8,$00
	dc.b $10,$EA,$10,$D2,$10,$EC,$10,$EE,$00,$00,$10,$BE,$00,$00,$10,$E8
	dc.b $00,$00,$10,$DA,$10,$FC,$11,$18
	dcb.b $8,$00
	dc.b $10,$F4,$00,$00,$10,$FE
	dcb.b $8,$00
	dc.b $11,$1C
	dcb.b $2A,$00
	dc.b $11,$34
	dcb.b $26,$00
loc_0_0000BA08:
	dcb.b $66,$FF
	dc.b $03,$40,$03,$42,$06,$D2,$FF,$FF,$07,$12,$07,$46,$07,$4C,$FF,$FF
	dc.b $FF,$FF,$FF,$FF,$00,$02,$FF,$FF,$FF,$FF,$FF,$FF,$00,$04,$00,$06
	dc.b $00,$08,$00,$0A,$00,$0C,$00,$0E,$FF,$FF,$FF,$FF,$00,$10,$00,$12
	dc.b $FF,$FF,$00,$14,$00,$16,$00,$18,$00,$1A,$00,$1C,$FF,$FF,$00,$1E
	dc.b $00,$20,$00,$22,$00,$24,$FF,$FF,$FF,$FF,$00,$26,$FF,$FF,$FF,$FF
	dc.b $FF,$FF,$01,$1A,$01,$20,$FF,$FF,$01,$22,$FF,$FF,$00,$04,$00,$06
	dc.b $00,$08,$00,$0A,$00,$0C,$00,$0E,$FF,$FF,$FF,$FF,$00,$10,$00,$12
	dc.b $FF,$FF,$00,$14,$00,$16,$00,$18,$00,$1A,$00,$1C,$FF,$FF,$00,$1E
	dc.b $00,$20,$00,$22,$00,$24,$FF,$FF,$FF,$FF,$00,$26,$00,$28,$FF,$FF
	dc.b $00,$2A,$01,$1A,$01,$20,$00,$30,$01,$22,$00,$32,$00,$34,$00,$36
	dc.b $00,$38,$01,$1C,$00,$2C,$00,$3A,$00,$3C,$00,$3E,$00,$40,$00,$2E
	dc.b $00,$42,$FF,$FF,$00,$44,$00,$46,$00,$48,$00,$9A,$00,$4A,$01,$1E
	dc.b $FF,$FF,$FF,$FF,$01,$24,$00,$9C,$FF,$FF,$FF,$FF,$00,$28,$FF,$FF
	dc.b $00,$2A,$FF,$FF,$01,$32,$00,$30,$FF,$FF,$00,$32,$00,$34,$00,$36
	dc.b $00,$38,$01,$1C,$00,$2C,$00,$3A,$00,$3C,$00,$3E,$00,$40,$00,$2E
	dc.b $00,$42,$00,$4C,$00,$44,$00,$46,$00,$48,$00,$9A,$00,$4A,$01,$1E
	dc.b $00,$4E,$00,$50,$01,$24,$00,$9C,$00,$52,$00,$54,$00,$56,$00,$58
	dc.b $00,$5A,$01,$26,$01,$32,$00,$5C,$00,$5E,$00,$60,$00,$62,$01,$28
	dc.b $00,$68,$01,$46,$00,$6A,$00,$6C,$00,$64,$00,$6E,$01,$48,$01,$50
	dc.b $01,$52,$00,$4C,$00,$70,$01,$2A,$00,$72,$01,$54,$00,$66,$FF,$FF
	dc.b $00,$4E,$00,$50,$FF,$FF,$FF,$FF,$00,$52,$00,$54,$00,$56,$00,$58
	dc.b $00,$5A,$01,$26,$FF,$FF,$00,$5C,$00,$5E,$00,$60,$00,$62,$01,$28
	dc.b $00,$68,$01,$46,$00,$6A,$00,$6C,$00,$64,$00,$6E,$01,$48,$01,$50
	dc.b $01,$52,$01,$56,$00,$70,$01,$2A,$00,$72,$01,$54,$00,$66,$00,$74
	dc.b $00,$76,$00,$78,$00,$7A,$00,$7C,$01,$5E,$00,$7E,$01,$6A,$00,$80
	dc.b $01,$64,$01,$6C,$00,$82,$00,$84,$00,$86,$00,$88,$01,$66,$01,$68
	dc.b $00,$8A,$00,$8C,$00,$8E,$00,$90,$01,$6E,$00,$92,$FF,$FF,$FF,$FF
	dc.b $00,$94,$01,$56,$FF,$FF,$00,$96,$FF,$FF,$00,$98,$FF,$FF,$00,$74
	dc.b $00,$76,$00,$78,$00,$7A,$00,$7C,$01,$5E,$00,$7E,$01,$6A,$00,$80
	dc.b $01,$64,$01,$6C,$00,$82,$00,$84,$00,$86,$00,$88,$01,$66,$01,$68
	dc.b $00,$8A,$00,$8C,$00,$8E,$00,$90,$01,$6E,$00,$92,$00,$B0,$01,$60
	dc.b $00,$94,$00,$B2,$00,$9E,$00,$96,$00,$A8,$00,$98,$00,$A0,$00,$B6
	dc.b $00,$AA,$00,$A2,$01,$70,$00,$B4,$01,$40,$00,$A4,$01,$72,$01,$62
	dc.b $00,$A6,$00,$B8,$00,$AC,$00,$BA,$FF,$FF,$01,$42,$00,$BC,$01,$74
	dc.b $00,$AE,$FF,$FF,$FF,$FF,$01,$44,$FF,$FF,$FF,$FF,$00,$B0,$01,$60
	dc.b $01,$76,$00,$B2,$00,$9E,$FF,$FF,$00,$A8,$FF,$FF,$00,$A0,$00,$B6
	dc.b $00,$AA,$00,$A2,$01,$70,$00,$B4,$01,$40,$00,$A4,$01,$72,$01,$62
	dc.b $00,$A6,$00,$B8,$00,$AC,$00,$BA,$01,$58,$01,$42,$00,$BC,$01,$74
	dc.b $00,$AE,$00,$BE,$00,$C0,$01,$44,$00,$C2,$00,$C4,$00,$C6,$00,$D4
	dc.b $01,$76,$01,$5A,$01,$5C,$00,$D6,$00,$C8,$00,$CA,$01,$78,$01,$7A
	dc.b $01,$7C,$01,$96,$00,$CC,$00,$CE,$00,$D0,$00,$D8,$00,$D2,$01,$98
	dc.b $01,$9A,$00,$DA,$00,$DC,$FF,$FF,$01,$58,$01,$9C,$FF,$FF,$FF,$FF
	dc.b $FF,$FF,$00,$BE,$00,$C0,$01,$9E,$00,$C2,$00,$C4,$00,$C6,$00,$D4
	dc.b $01,$A0,$01,$5A,$01,$5C,$00,$D6,$00,$C8,$00,$CA,$01,$78,$01,$7A
	dc.b $01,$7C,$01,$96,$00,$CC,$00,$CE,$00,$D0,$00,$D8,$00,$D2,$01,$98
	dc.b $01,$9A,$00,$DA,$00,$DC,$00,$DE,$00,$E0,$01,$9C,$00,$E2,$00,$E4
	dc.b $00,$E6,$00,$E8,$01,$A2,$01,$9E,$01,$DC,$00,$EA,$00,$EC,$00,$EE
	dc.b $01,$A0,$00,$F0,$FF,$FF,$01,$DE,$01,$A4,$00,$F2,$00,$F4,$00,$F6
	dc.b $00,$F8
	dcb.b $10,$FF
	dc.b $01,$A6,$01,$E0,$00,$DE,$00,$E0,$FF,$FF,$00,$E2,$00,$E4,$00,$E6
	dc.b $00,$E8,$01,$A2,$FF,$FF,$01,$DC,$00,$EA,$00,$EC,$00,$EE,$01,$C6
	dc.b $00,$F0,$01,$C8,$01,$DE,$01,$A4,$00,$F2,$00,$F4,$00,$F6,$00,$F8
	dc.b $00,$FA,$00,$FC,$00,$FE,$01,$00,$01,$02,$01,$04,$01,$06,$01,$08
	dc.b $01,$A6,$01,$E0,$01,$E2,$01,$0A,$01,$0C,$01,$0E,$01,$EE,$01,$10
	dc.b $01,$E4,$01,$12,$01,$14,$01,$16,$FF,$FF,$01,$18,$FF,$FF,$01,$C6
	dc.b $01,$34,$01,$C8,$01,$36,$01,$38,$01,$D8,$FF,$FF,$01,$3A,$01,$DA
	dc.b $00,$FA,$00,$FC,$00,$FE,$01,$00,$01,$02,$01,$04,$01,$06,$01,$08
	dc.b $01,$3C,$01,$3E,$01,$E2,$01,$0A,$01,$0C,$01,$0E,$01,$EE,$01,$10
	dc.b $01,$E4,$01,$12,$01,$14,$01,$16,$01,$2A,$01,$18,$01,$E6,$01,$4A
	dc.b $01,$34,$01,$2C,$01,$36,$01,$38,$01,$D8,$01,$2E,$01,$3A,$01,$DA
	dc.b $01,$E8,$01,$30,$02,$18,$02,$26,$01,$30,$01,$4C,$01,$4E,$FF,$FF
	dc.b $01,$3C,$01,$3E,$FF,$FF,$FF,$FF,$FF,$FF,$01,$EA,$02,$28,$01,$EC
	dc.b $FF,$FF,$FF,$FF,$FF,$FF,$02,$2A,$01,$2A,$02,$2C,$01,$E6,$01,$4A
	dc.b $FF,$FF,$01,$2C,$FF,$FF,$02,$2E,$FF,$FF,$01,$2E,$FF,$FF,$02,$30
	dc.b $01,$E8,$01,$30,$02,$18,$02,$26,$01,$30,$01,$4C,$01,$4E,$01,$7E
	dc.b $02,$36,$01,$80,$01,$82,$01,$84,$01,$86,$01,$EA,$02,$28,$01,$EC
	dc.b $01,$88,$01,$8A,$01,$8C,$02,$2A,$01,$8E,$02,$2C,$01,$90,$02,$38
	dc.b $01,$92,$02,$3E,$01,$94,$02,$2E,$01,$A8,$01,$AA,$01,$AC,$02,$30
	dc.b $02,$32,$02,$40,$02,$46,$01,$AE,$02,$48,$02,$34,$02,$4A,$01,$7E
	dc.b $02,$36,$01,$80,$01,$82,$01,$84,$01,$86,$01,$B0,$01,$B2,$FF,$FF
	dc.b $01,$88,$01,$8A,$01,$8C,$02,$52,$01,$8E,$02,$3A,$01,$90,$02,$38
	dc.b $01,$92,$02,$3E,$01,$94,$02,$3C,$01,$A8,$01,$AA,$01,$AC,$02,$54
	dc.b $02,$32,$02,$40,$02,$46,$01,$AE,$02,$48,$02,$34,$02,$4A,$02,$5A
	dc.b $01,$B4,$01,$B6,$01,$B8,$FF,$FF,$02,$0E,$01,$B0,$01,$B2,$01,$BA
	dc.b $02,$10,$01,$BC,$01,$BE,$02,$52,$02,$70,$02,$3A,$01,$C0,$01,$C2
	dc.b $01,$C4,$01,$CA,$01,$CC,$02,$3C,$01,$CE,$02,$12,$02,$14,$02,$54
	dc.b $02,$5C,$01,$D0,$02,$16,$02,$72,$02,$5E,$01,$D2,$01,$D4,$02,$5A
	dc.b $01,$B4,$01,$B6,$01,$B8,$01,$D6,$02,$0E,$FF,$FF,$FF,$FF,$01,$BA
	dc.b $02,$10,$01,$BC,$01,$BE,$02,$74,$02,$70,$FF,$FF,$01,$C0,$01,$C2
	dc.b $01,$C4,$01,$CA,$01,$CC,$02,$7C,$01,$CE,$02,$12,$02,$14,$02,$42
	dc.b $02,$5C,$01,$D0,$02,$16,$02,$72,$02,$5E,$01,$D2,$01,$D4,$FF,$FF
	dc.b $02,$7E,$FF,$FF,$01,$F0,$01,$D6,$01,$F2,$01,$F4,$01,$F6,$01,$F8
	dc.b $01,$FA,$02,$44,$01,$FC,$02,$74,$02,$94,$01,$FE,$02,$00,$02,$02
	dc.b $02,$04,$02,$96,$02,$06,$02,$7C,$02,$08,$02,$0A,$02,$0C,$02,$42
	dc.b $02,$1A,$02,$1C,$02,$1E,$FF,$FF,$02,$20,$02,$56,$FF,$FF,$02,$58
	dc.b $02,$7E,$02,$22,$01,$F0,$02,$24,$01,$F2,$01,$F4,$01,$F6,$01,$F8
	dc.b $01,$FA,$02,$44,$01,$FC,$FF,$FF,$02,$94,$01,$FE,$02,$00,$02,$02
	dc.b $02,$04,$02,$96,$02,$06,$02,$4C,$02,$08,$02,$0A,$02,$0C,$02,$4E
	dc.b $02,$1A,$02,$1C,$02,$1E,$02,$50,$02,$20,$02,$56,$02,$76,$02,$58
	dc.b $02,$90,$02,$22,$02,$98,$02,$24,$02,$60,$02,$62,$02,$64,$02,$B2
	dc.b $02,$78,$02,$7A,$02,$66,$02,$9A,$02,$68,$02,$92,$02,$9C,$02,$6A
	dc.b $02,$CA,$FF,$FF,$FF,$FF,$02,$4C,$FF,$FF,$FF,$FF,$02,$6C,$02,$4E
	dc.b $FF,$FF,$FF,$FF,$02,$6E,$02,$50,$FF,$FF,$FF,$FF,$02,$76,$FF,$FF
	dc.b $02,$90,$FF,$FF,$02,$98,$FF,$FF,$02,$60,$02,$62,$02,$64,$02,$B2
	dc.b $02,$78,$02,$7A,$02,$66,$02,$9A,$02,$68,$02,$92,$02,$9C,$02,$6A
	dc.b $02,$CA,$02,$80,$02,$82,$02,$84,$02,$B4,$02,$9E,$02,$6C,$02,$86
	dc.b $02,$B8,$02,$88,$02,$6E,$02,$A0,$02,$8A,$02,$A4,$02,$A6,$02,$A8
	dc.b $02,$AA,$02,$A2,$02,$C2,$02,$8C,$02,$B6,$FF,$FF,$02,$BA,$02,$8E
	dc.b $02,$AC,$02,$BC,$02,$CC,$02,$BE,$02,$B4,$02,$AE,$02,$B0,$FF,$FF
	dc.b $FF,$FF,$02,$80,$02,$82,$02,$84,$02,$B4,$02,$9E,$02,$D2,$02,$86
	dc.b $02,$B8,$02,$88,$02,$C0,$02,$A0,$02,$8A,$02,$A4,$02,$A6,$02,$A8
	dc.b $02,$AA,$02,$A2,$02,$C2,$02,$8C,$02,$B6,$02,$C4,$02,$BA,$02,$8E
	dc.b $02,$AC,$02,$BC,$02,$CC,$02,$BE,$02,$B4,$02,$AE,$02,$B0,$02,$B6
	dc.b $02,$CE,$02,$D4,$02,$D6,$02,$C6,$02,$C8,$02,$DA,$02,$D2,$02,$DC
	dc.b $02,$DE,$02,$D0,$02,$C0,$02,$E0,$02,$E4,$02,$E6,$02,$EA,$02,$EE
	dc.b $02,$F6,$02,$F8,$02,$D8,$03,$04,$02,$E8,$02,$C4,$03,$06,$03,$08
	dc.b $FF,$FF,$FF,$FF,$03,$12,$02,$E2,$00,$AE,$02,$EC,$FF,$FF,$02,$B6
	dc.b $02,$CE,$02,$D4,$02,$D6,$02,$C6,$02,$C8,$02,$DA,$03,$14,$02,$DC
	dc.b $02,$DE,$02,$D0,$02,$F0,$02,$E0,$02,$E4,$02,$E6,$02,$EA,$02,$EE
	dc.b $02,$F6,$02,$F8,$02,$D8,$03,$04,$02,$E8,$03,$0A,$03,$06,$03,$08
	dc.b $02,$F2,$02,$F4,$03,$12,$02,$E2,$00,$AE,$02,$EC,$00,$FE,$03,$16
	dc.b $02,$FA,$01,$04,$01,$06,$01,$08,$03,$20,$03,$0C,$03,$14,$02,$FC
	dc.b $02,$FE,$01,$0E,$02,$F0,$03,$00,$03,$0E,$03,$22,$FF,$FF,$03,$02
	dc.b $03,$10,$01,$18,$03,$24,$03,$26,$03,$2A,$03,$0A,$FF,$FF,$03,$28
	dc.b $02,$F2,$02,$F4,$03,$2C,$03,$2E,$03,$30,$FF,$FF,$00,$FE,$03,$16
	dc.b $02,$FA,$01,$04,$01,$06,$01,$08,$03,$20,$03,$0C,$03,$18,$02,$FC
	dc.b $02,$FE,$01,$0E,$03,$32,$03,$00,$03,$0E,$03,$22,$03,$1A,$03,$02
	dc.b $03,$10,$01,$18,$03,$24,$03,$26,$03,$2A,$03,$34,$03,$1C,$03,$28
	dc.b $03,$36,$03,$38,$03,$2C,$03,$2E,$03,$30,$03,$1E,$03,$3A,$03,$3C
	dc.b $03,$3E,$03,$44,$FF,$FF,$03,$4E,$03,$50,$03,$52,$03,$18,$03,$54
	dc.b $03,$56,$03,$58,$03,$32,$03,$46,$03,$5A,$03,$5E,$03,$1A,$FF,$FF
	dc.b $03,$6C,$03,$6E,$03,$70,$03,$72,$FF,$FF,$03,$34,$03,$1C,$03,$7C
	dc.b $03,$36,$03,$38,$03,$48,$03,$60,$03,$5C,$03,$1E,$03,$3A,$03,$3C
	dc.b $03,$3E,$03,$44,$03,$4A,$03,$4E,$03,$50,$03,$52,$03,$4C,$03,$54
	dc.b $03,$56,$03,$58,$03,$62,$03,$64,$03,$5A,$03,$5E,$FF,$FF,$03,$66
	dc.b $03,$6C,$03,$6E,$03,$70,$03,$72,$03,$74,$03,$5A,$03,$78,$03,$7C
	dc.b $03,$7A,$03,$5C,$03,$48,$03,$60,$03,$5C,$03,$68,$03,$6A,$03,$7E
	dc.b $03,$86,$03,$8C,$03,$4A,$03,$88,$03,$76,$03,$80,$03,$4C,$03,$8E
	dc.b $03,$92,$03,$82,$03,$62,$03,$64,$03,$94,$03,$96,$03,$84,$03,$66
	dc.b $03,$8A,$03,$98,$03,$9A,$03,$9C,$03,$74,$03,$5A,$03,$78,$03,$9E
	dc.b $03,$7A,$03,$5C,$FF,$FF,$03,$A0,$03,$90,$03,$68,$03,$6A,$03,$7E
	dc.b $03,$86,$03,$8C,$03,$A2,$03,$88,$03,$76,$03,$80,$03,$A6,$03,$8E
	dc.b $03,$92,$03,$82,$03,$A4,$FF,$FF,$03,$94,$03,$96,$03,$84,$03,$B0
	dc.b $03,$8A,$03,$98,$03,$9A,$03,$9C,$03,$B2,$03,$A8,$03,$AA,$03,$9E
	dc.b $03,$AC,$03,$C6,$03,$B4,$03,$A0,$03,$90,$03,$AE,$03,$B6,$03,$B8
	dc.b $03,$C8,$03,$CA,$03,$A2,$03,$CC,$03,$E2,$03,$E4,$03,$A6,$03,$BA
	dc.b $03,$E6,$03,$BE,$03,$A4,$03,$C0,$03,$EA,$03,$BC,$03,$E8,$03,$B0
	dc.b $03,$C2,$03,$F0,$03,$C4,$FF,$FF,$03,$B2,$03,$A8,$03,$AA,$03,$EC
	dc.b $03,$AC,$03,$C6,$03,$B4,$03,$EE,$FF,$FF,$03,$AE,$03,$B6,$03,$B8
	dc.b $03,$C8,$03,$CA,$FF,$FF,$03,$CC,$03,$E2,$03,$E4,$03,$F2,$03,$BA
	dc.b $03,$E6,$03,$BE,$03,$F4,$03,$C0,$03,$EA,$03,$BC,$03,$E8,$03,$F6
	dc.b $03,$C2,$03,$F0,$03,$C4,$03,$CE,$03,$D0,$03,$D2,$03,$F8,$03,$EC
	dc.b $03,$FE,$03,$FA,$03,$D4,$03,$EE,$03,$D6,$03,$D8,$04,$00,$04,$02
	dc.b $03,$DA,$03,$DC,$03,$DE,$03,$E0,$04,$04,$04,$06,$03,$F2,$04,$08
	dc.b $FF,$FF,$04,$12,$03,$F4,$03,$FC,$04,$14,$04,$0A,$04,$16,$03,$F6
	dc.b $04,$1E,$FF,$FF,$FF,$FF,$03,$CE,$03,$D0,$03,$D2,$03,$F8,$FF,$FF
	dc.b $03,$FE,$03,$FA,$03,$D4,$FF,$FF,$03,$D6,$03,$D8,$04,$00,$04,$02
	dc.b $03,$DA,$03,$DC,$03,$DE,$03,$E0,$04,$04,$04,$06,$04,$0C,$04,$08
	dc.b $04,$0E,$04,$12,$04,$18,$03,$FC,$04,$14,$04,$0A,$04,$16,$04,$20
	dc.b $04,$1E,$04,$1A,$04,$24,$04,$34,$04,$28,$04,$4C,$04,$2A,$04,$2E
	dc.b $04,$26,$04,$1C,$04,$10,$04,$2C,$04,$30,$04,$4E,$04,$22,$FF,$FF
	dc.b $FF,$FF,$04,$50,$04,$32,$04,$52,$04,$54,$04,$56,$04,$0C,$FF,$FF
	dc.b $04,$0E,$04,$58,$04,$18
	dcb.b $8,$FF
	dc.b $04,$20,$04,$68,$04,$1A,$04,$24,$04,$34,$04,$28,$04,$4C,$04,$2A
	dc.b $04,$2E,$04,$26,$04,$1C,$04,$10,$04,$2C,$04,$30,$04,$4E,$04,$22
	dc.b $04,$36,$04,$38,$04,$50,$04,$32,$04,$52,$04,$54,$04,$56,$04,$5A
	dc.b $04,$42,$04,$3A,$04,$58,$04,$44,$04,$3C,$04,$46,$04,$5E,$04,$3E
	dc.b $04,$40,$04,$68,$04,$48,$04,$70,$04,$4A,$04,$72,$04,$5C,$04,$62
	dc.b $04,$64,$04,$66,$04,$6A,$04,$74,$04,$6C,$04,$60,$04,$76,$FF,$FF
	dc.b $04,$36,$04,$38,$04,$7C,$04,$7E,$04,$6E,$04,$80,$FF,$FF,$04,$5A
	dc.b $04,$42,$04,$3A,$04,$86,$04,$44,$04,$3C,$04,$46,$04,$5E,$04,$3E
	dc.b $04,$40,$04,$88,$04,$48,$04,$70,$04,$4A,$04,$72,$04,$5C,$04,$62
	dc.b $04,$64,$04,$66,$04,$6A,$04,$74,$04,$6C,$04,$60,$04,$76,$04,$78
	dc.b $04,$8A,$04,$8C,$04,$7C,$04,$7E,$04,$6E,$04,$80,$04,$82,$04,$8E
	dc.b $04,$84,$04,$7A,$04,$86,$04,$90,$04,$92,$04,$94,$04,$96,$FF,$FF
	dc.b $FF,$FF,$04,$88,$04,$9A,$04,$9E,$04,$A2,$04,$A6,$04,$C6,$04,$C8
	dc.b $04,$CA,$04,$CC,$04,$AA,$04,$CE,$04,$D0,$FF,$FF,$04,$98,$04,$78
	dc.b $04,$8A,$04,$8C,$04,$9C,$04,$A0,$04,$A4,$04,$A8,$04,$82,$04,$8E
	dc.b $04,$84,$04,$7A,$04,$AC,$04,$90,$04,$92,$04,$94,$04,$96,$04,$AE
	dc.b $04,$B2,$FF,$FF,$04,$9A,$04,$9E,$04,$A2,$04,$A6,$04,$C6,$04,$C8
	dc.b $04,$CA,$04,$CC,$04,$AA,$04,$CE,$04,$D0,$04,$D8,$04,$98,$04,$B0
	dc.b $04,$B4,$04,$F4,$04,$9C,$04,$A0,$04,$A4,$04,$A8,$04,$B6,$04,$B8
	dc.b $04,$BA,$04,$DC,$04,$AC,$04,$D2,$04,$BC,$04,$DA,$04,$BE,$04,$AE
	dc.b $04,$B2,$04,$C0,$04,$E0,$04,$E4,$04,$E8,$04,$EC,$04,$F6,$04,$F8
	dc.b $04,$C2,$04,$DE,$04,$F0,$04,$D4,$04,$C4,$04,$D8,$04,$D6,$04,$B0
	dc.b $04,$B4,$04,$F4,$04,$E2,$04,$E6,$04,$EA,$04,$EE,$04,$B6,$04,$B8
	dc.b $04,$BA,$04,$DC,$04,$F2,$04,$D2,$04,$BC,$04,$DA,$04,$BE,$04,$FA
	dc.b $04,$FC,$04,$C0,$04,$E0,$04,$E4,$04,$E8,$04,$EC,$04,$F6,$04,$F8
	dc.b $04,$C2,$04,$DE,$04,$F0,$04,$D4,$04,$C4,$04,$FE,$04,$D6,$05,$00
	dc.b $05,$02,$05,$06,$04,$E2,$04,$E6,$04,$EA,$04,$EE,$05,$04,$05,$08
	dc.b $05,$0A,$05,$0C,$04,$F2,$05,$0E,$05,$1A,$FF,$FF,$05,$20,$04,$FA
	dc.b $04,$FC,$FF,$FF,$05,$1C,$05,$22,$05,$1E,$02,$E6,$02,$F0,$02,$F6
	dc.b $05,$24,$05,$26,$05,$10,$05,$28,$05,$2A,$04,$FE,$05,$2C,$05,$00
	dc.b $05,$02,$05,$06,$05,$12,$05,$2E,$02,$F2,$02,$F4,$05,$04,$05,$08
	dc.b $05,$0A,$05,$0C,$05,$14,$05,$0E,$05,$1A,$05,$16,$05,$20,$05,$30
	dc.b $05,$32,$05,$18,$05,$1C,$05,$22,$05,$1E,$02,$E6,$02,$F0,$02,$F6
	dc.b $05,$24,$05,$26,$05,$10,$05,$28,$05,$2A,$05,$34,$05,$2C,$05,$36
	dc.b $05,$38,$05,$3A,$05,$12,$05,$2E,$02,$F2,$02,$F4,$05,$3C,$05,$3E
	dc.b $05,$40,$05,$42,$05,$14,$05,$48,$05,$4A,$05,$16,$05,$4C,$05,$30
	dc.b $05,$32,$05,$18,$05,$4E,$05,$50,$05,$44,$05,$52,$05,$54,$05,$56
	dc.b $05,$46,$05,$58,$05,$5A,$05,$5C,$05,$5E,$05,$34,$05,$60,$05,$36
	dc.b $05,$38,$05,$3A,$05,$66,$05,$74,$FF,$FF,$05,$62,$05,$3C,$05,$3E
	dc.b $05,$40,$05,$42,$05,$76,$05,$48,$05,$4A,$05,$64,$05,$4C,$05,$78
	dc.b $05,$70,$05,$68,$05,$4E,$05,$50,$05,$44,$05,$52,$05,$54,$05,$56
	dc.b $05,$46,$05,$58,$05,$5A,$05,$5C,$05,$5E,$05,$6A,$05,$60,$05,$72
	dc.b $05,$82,$05,$84,$05,$66,$05,$74,$05,$6C,$05,$62,$05,$7A,$05,$7E
	dc.b $05,$86,$05,$88,$05,$76,$05,$8A,$05,$6E,$05,$64,$03,$D0,$05,$78
	dc.b $05,$70,$05,$68,$05,$8C,$05,$90,$05,$B0,$05,$7C,$05,$80,$05,$94
	dc.b $05,$B2,$05,$96,$05,$8E,$05,$B4,$05,$B6,$05,$6A,$05,$98,$05,$72
	dc.b $05,$82,$05,$84,$05,$92,$05,$B8,$05,$6C,$05,$9A,$05,$7A,$05,$7E
	dc.b $05,$86,$05,$88,$05,$9C,$05,$8A,$05,$6E,$FF,$FF,$03,$D0,$05,$BA
	dc.b $05,$9E,$05,$BC,$05,$8C,$05,$90,$05,$B0,$05,$7C,$05,$80,$05,$94
	dc.b $05,$B2,$05,$96,$05,$8E,$05,$B4,$05,$B6,$05,$C2,$05,$98,$05,$A0
	dc.b $05,$A2,$05,$BE,$05,$92,$05,$B8,$05,$A8,$05,$9A,$05,$AA,$05,$CA
	dc.b $05,$A4,$05,$C0,$05,$9C,$05,$AC,$05,$CC,$05,$AE,$05,$A6,$05,$BA
	dc.b $05,$9E,$05,$BC,$05,$C4,$05,$C6,$05,$CE,$05,$D0,$05,$D2,$05,$D4
	dc.b $05,$D6,$05,$D8,$05,$DA,$05,$DC,$05,$E4,$05,$C2,$05,$E6,$05,$A0
	dc.b $05,$A2,$05,$BE,$05,$E8,$05,$DE,$05,$A8,$05,$E0,$05,$AA,$05,$CA
	dc.b $05,$A4,$05,$C0,$05,$E2,$05,$AC,$05,$CC,$05,$AE,$05,$A6,$05,$C8
	dc.b $05,$F0,$05,$FA,$05,$FE,$06,$00,$05,$CE,$05,$D0,$05,$D2,$05,$D4
	dc.b $05,$D6,$05,$D8,$05,$DA,$05,$DC,$05,$E4,$05,$EA,$05,$E6,$05,$F2
	dc.b $05,$FC,$06,$02,$05,$E8,$05,$DE,$05,$EC,$05,$E0,$05,$F4,$06,$04
	dc.b $06,$06,$06,$08,$05,$E2,$06,$0A,$05,$EE,$05,$F6,$06,$12,$05,$C8
	dc.b $05,$F0,$05,$FA,$05,$FE,$06,$00,$06,$0E,$05,$F8,$06,$14,$06,$16
	dc.b $06,$18,$06,$1A,$06,$0C,$06,$1C,$06,$1E,$05,$EA,$06,$20,$05,$F2
	dc.b $05,$FC,$06,$02,$06,$22,$06,$10,$05,$EC,$06,$24,$05,$F4,$06,$04
	dc.b $06,$06,$06,$08,$06,$26,$06,$0A,$05,$EE,$05,$F6,$06,$12,$06,$28
	dc.b $06,$2A,$06,$2C,$06,$3C,$06,$3E,$06,$0E,$05,$F8,$06,$14,$06,$16
	dc.b $06,$18,$06,$1A,$06,$0C,$06,$1C,$06,$1E,$06,$40,$06,$20,$06,$42
	dc.b $FF,$FF,$06,$64,$06,$22,$06,$10,$06,$2E,$06,$24,$FF,$FF,$06,$44
	dc.b $06,$48,$06,$4C,$06,$26,$06,$50,$06,$54,$06,$66,$06,$58,$06,$28
	dc.b $06,$2A,$06,$2C,$06,$3C,$06,$3E,$06,$30,$06,$5C,$06,$32,$06,$46
	dc.b $06,$4A,$06,$4E,$06,$60,$06,$52,$06,$56,$06,$40,$06,$5A,$06,$42
	dc.b $06,$34,$06,$64,$FF,$FF,$06,$36,$06,$38,$06,$5E,$06,$3A,$06,$44
	dc.b $06,$48,$06,$4C,$06,$62,$06,$50,$06,$54,$06,$66,$06,$58,$06,$6C
	dc.b $06,$6E,$06,$70,$06,$72,$06,$74,$06,$30,$06,$5C,$06,$32,$06,$46
	dc.b $06,$4A,$06,$4E,$06,$60,$06,$52,$06,$56,$06,$68,$06,$5A,$06,$76
	dc.b $06,$34,$06,$78,$06,$6A,$06,$36,$06,$38,$06,$5E,$06,$3A,$06,$7A
	dc.b $06,$7C,$06,$7E,$06,$62,$06,$80,$06,$82,$06,$84,$06,$86,$06,$6C
	dc.b $06,$6E,$06,$70,$06,$72,$06,$74,$06,$88,$FF,$FF,$06,$8A
	dcb.b $8,$FF
	dc.b $06,$92,$06,$9A,$06,$68,$FF,$FF,$06,$76,$FF,$FF,$06,$78,$06,$6A
	dc.b $06,$8E,$06,$94,$06,$90,$FF,$FF,$06,$7A,$06,$7C,$06,$7E,$06,$9C
	dc.b $06,$80,$06,$82,$06,$84,$06,$86,$06,$96,$06,$9E,$06,$A0,$06,$A2
	dc.b $06,$98,$06,$88,$00,$FE,$06,$8A,$02,$FA,$01,$04,$01,$06,$01,$08
	dc.b $06,$92,$06,$9A,$06,$AA,$01,$0A,$02,$FE,$01,$0E,$06,$B8,$03,$00
	dc.b $06,$8E,$06,$94,$06,$90,$03,$02,$06,$A4,$06,$8C,$06,$BA,$06,$9C
	dc.b $06,$BC,$06,$AC,$06,$AE,$06,$A6,$06,$96,$06,$9E,$06,$A0,$06,$A2
	dc.b $06,$98,$06,$B0,$00,$FE,$06,$A8,$02,$FA,$01,$04,$01,$06,$01,$08
	dc.b $06,$B4,$06,$B2,$06,$AA,$01,$0A,$02,$FE,$01,$0E,$06,$B8,$03,$00
	dc.b $06,$BE,$06,$C2,$06,$C6,$03,$02,$06,$A4,$06,$8C,$06,$BA,$06,$B6
	dc.b $06,$BC,$06,$AC,$06,$AE,$06,$A6,$06,$C8,$06,$CA,$06,$CC,$06,$C0
	dc.b $06,$C4,$06,$B0,$06,$CE,$06,$A8,$06,$D0,$06,$D4,$06,$DA,$06,$DC
	dc.b $06,$B4,$06,$B2,$06,$D6,$06,$DE,$06,$E0,$06,$E2,$06,$E4,$06,$E6
	dc.b $06,$BE,$06,$C2,$06,$C6,$06,$E8,$06,$D8,$06,$EA,$06,$EC,$06,$B6
	dc.b $07,$00,$FF,$FF,$FF,$FF,$07,$02,$06,$C8,$06,$CA,$06,$CC,$06,$C0
	dc.b $06,$C4,$07,$04,$06,$CE,$07,$06,$06,$D0,$06,$D4,$06,$DA,$06,$DC
	dc.b $07,$08,$07,$0A,$06,$D6,$06,$DE,$06,$E0,$06,$E2,$06,$E4,$06,$E6
	dc.b $06,$EE,$06,$F0,$06,$F2,$06,$E8,$06,$D8,$06,$EA,$06,$EC,$06,$F4
	dc.b $07,$00,$06,$F6,$06,$F8,$07,$02,$07,$0C,$07,$0E,$06,$FA,$06,$FC
	dc.b $06,$FE,$07,$04,$07,$10,$07,$06,$07,$14,$07,$16,$07,$18,$07,$1A
	dc.b $07,$08,$07,$0A,$07,$1C,$07,$22,$07,$24,$07,$3A,$07,$1E,$07,$26
	dc.b $06,$EE,$06,$F0,$06,$F2,$07,$20,$07,$28,$07,$3C,$FF,$FF,$06,$F4
	dc.b $FF,$FF,$06,$F6,$06,$F8,$FF,$FF,$07,$0C,$07,$0E,$06,$FA,$06,$FC
	dc.b $06,$FE,$07,$3E,$07,$10,$07,$40,$07,$14,$07,$16,$07,$18,$07,$1A
	dc.b $07,$42,$03,$0A,$07,$1C,$07,$22,$07,$24,$07,$3A,$07,$1E,$07,$26
	dc.b $07,$2A,$07,$2C,$07,$2E,$07,$20,$07,$28,$07,$3C,$07,$30,$07,$44
	dc.b $07,$32,$03,$0C,$07,$48,$07,$34,$07,$4A,$07,$4E,$07,$50,$07,$52
	dc.b $07,$54,$07,$3E,$07,$36,$07,$40,$07,$56,$07,$58,$07,$38,$07,$5A
	dc.b $07,$42,$03,$0A,$07,$6C,$07,$82,$07,$66,$07,$84,$07,$68,$07,$6E
	dc.b $07,$2A,$07,$2C,$07,$2E,$07,$6A,$07,$62,$07,$70,$07,$30,$07,$44
	dc.b $07,$32,$03,$0C,$07,$48,$07,$34,$07,$4A,$07,$4E,$07,$50,$07,$52
	dc.b $07,$54,$07,$5C,$07,$36,$07,$64,$07,$56,$07,$58,$07,$38,$07,$5A
	dc.b $07,$5E,$07,$86,$07,$6C,$07,$82,$07,$66,$07,$84,$07,$68,$07,$6E
	dc.b $07,$60,$07,$72,$07,$74,$07,$6A,$07,$62,$07,$70,$07,$7A,$07,$88
	dc.b $07,$7C,$07,$8A,$07,$76,$07,$94,$07,$96,$07,$7E,$07,$98,$07,$80
	dc.b $07,$78,$07,$5C,$07,$8C,$07,$64,$07,$B8,$07,$9C,$FF,$FF,$FF,$FF
	dc.b $07,$5E,$07,$86,$FF,$FF,$07,$BA,$07,$BC,$07,$BE,$07,$9A,$07,$8E
	dc.b $07,$60,$07,$72,$07,$74,$07,$90,$07,$92,$07,$9E,$07,$7A,$07,$88
	dc.b $07,$7C,$07,$8A,$07,$76,$07,$94,$07,$96,$07,$7E,$07,$98,$07,$80
	dc.b $07,$78,$07,$A0,$07,$8C,$FF,$FF,$07,$B8,$07,$9C,$07,$A4,$07,$A8
	dc.b $07,$AC,$07,$B0,$07,$B4,$07,$BA,$07,$BC,$07,$BE,$07,$9A,$07,$8E
	dc.b $07,$C6,$07,$A2,$07,$D4,$07,$90,$07,$92,$07,$9E,$07,$A6,$07,$AA
	dc.b $07,$AE,$07,$B2,$07,$B6,$07,$D6,$07,$C0,$07,$CA,$07,$D0,$07,$C8
	dc.b $07,$D8,$07,$A0,$FF,$FF,$07,$C2,$07,$CC,$07,$DA,$07,$A4,$07,$A8
	dc.b $07,$AC,$07,$B0,$07,$B4,$07,$C4,$07,$CE,$07,$D2,$07,$E2,$07,$E4
	dc.b $07,$C6,$07,$A2,$07,$D4,$07,$DE,$07,$DC,$07,$E6,$07,$A6,$07,$AA
	dc.b $07,$AE,$07,$B2,$07,$B6,$07,$D6,$07,$C0,$07,$CA,$07,$D0,$07,$C8
	dc.b $07,$D8,$07,$E8,$07,$E0,$07,$C2,$07,$CC,$07,$DA
	dcb.b $A,$FF
	dc.b $07,$C4,$07,$CE,$07,$D2,$07,$E2,$07,$E4,$FF,$FF,$FF,$FF,$FF,$FF
	dc.b $07,$DE,$07,$DC,$07,$E6
	dcb.b $16,$FF
	dc.b $07,$E8,$07,$E0
	dcb.b $132,$FF
loc_0_0000CD3C:
	dcb.b $60,$FF
	dc.b $00,$00,$00,$00,$00,$00,$01,$68,$01,$6A,$05,$C4,$00,$00,$06,$2E
	dc.b $06,$CA,$06,$D4,$FF,$FF,$FF,$FF,$FF,$FF,$00,$00,$FF,$FF,$FF,$FF
	dc.b $FF,$FF
	dcb.b $30,$00
	dc.b $FF,$FF,$00,$00,$FF,$FF,$00,$24,$00,$28,$FF,$FF,$00,$2A,$FF,$FF
	dcb.b $31,$00
	dc.b $04,$00,$00,$00,$04,$00,$24,$00,$28,$00,$06,$00,$2A,$00,$06,$00
	dc.b $06,$00,$06,$00,$06,$00,$26,$00,$04,$00,$06,$00,$06,$00,$06,$00
	dc.b $06,$00,$04,$00,$06,$FF,$FF,$00,$06,$00,$06,$00,$06,$00,$12,$00
	dc.b $06,$00,$26,$FF,$FF,$FF,$FF,$00,$2C,$00,$12,$FF,$FF,$FF,$FF,$00
	dc.b $04,$FF,$FF,$00,$04,$FF,$FF,$00,$32,$00,$06,$FF,$FF,$00,$06,$00
	dc.b $06,$00,$06,$00,$06,$00,$26,$00,$04,$00,$06,$00,$06,$00,$06,$00
	dc.b $06,$00,$04,$00,$06,$00,$08,$00,$06,$00,$06,$00,$06,$00,$12,$00
	dc.b $06,$00,$26,$00,$08,$00,$08,$00,$2C,$00,$12,$00,$08,$00,$08,$00
	dc.b $08,$00,$08,$00,$08,$00,$2E,$00,$32,$00,$08,$00,$0A,$00,$0A,$00
	dc.b $0A,$00,$2E,$00,$0C,$00,$38,$00,$0C,$00,$0C,$00,$0A,$00,$0C,$00
	dc.b $3A,$00,$3E,$00,$40,$00,$08,$00,$0C,$00,$38,$00,$0C,$00,$42,$00
	dc.b $0A,$FF,$FF,$00,$08,$00,$08,$FF,$FF,$FF,$FF,$00,$08,$00,$08,$00
	dc.b $08,$00,$08,$00,$08,$00,$2E,$FF,$FF,$00,$08,$00,$0A,$00,$0A,$00
	dc.b $0A,$00,$2E,$00,$0C,$00,$38,$00,$0C,$00,$0C,$00,$0A,$00,$0C,$00
	dc.b $3A,$00,$3E,$00,$40,$00,$44,$00,$0C,$00,$38,$00,$0C,$00,$42,$00
	dc.b $0A,$00,$0E,$00,$0E,$00,$0E,$00,$0E,$00,$0E,$00,$48,$00,$0E,$00
	dc.b $4E,$00,$0E,$00,$4C,$00,$50,$00,$0E,$00,$0E,$00,$0E,$00,$0E,$00
	dc.b $4C,$00,$4C,$00,$0E,$00,$0E,$00,$0E,$00,$10,$00,$52,$00,$10,$FF
	dc.b $FF,$FF,$FF,$00,$10,$00,$44,$FF,$FF,$00,$10,$FF,$FF,$00,$10,$FF
	dc.b $FF,$00,$0E,$00,$0E,$00,$0E,$00,$0E,$00,$0E,$00,$48,$00,$0E,$00
	dc.b $4E,$00,$0E,$00,$4C,$00,$50,$00,$0E,$00,$0E,$00,$0E,$00,$0E,$00
	dc.b $4C,$00,$4C,$00,$0E,$00,$0E,$00,$0E,$00,$10,$00,$52,$00,$10,$00
	dc.b $18,$00,$4A,$00,$10,$00,$18,$00,$14,$00,$10,$00,$16,$00,$10,$00
	dc.b $14,$00,$1A,$00,$16,$00,$14,$00,$54,$00,$18,$00,$36,$00,$14,$00
	dc.b $56,$00,$4A,$00,$14,$00,$1A,$00,$16,$00,$1A,$FF,$FF,$00,$36,$00
	dc.b $1A,$00,$58,$00,$16,$FF,$FF,$FF,$FF,$00,$36,$FF,$FF,$FF,$FF,$00
	dc.b $18,$00,$4A,$00,$58,$00,$18,$00,$14,$FF,$FF,$00,$16,$FF,$FF,$00
	dc.b $14,$00,$1A,$00,$16,$00,$14,$00,$54,$00,$18,$00,$36,$00,$14,$00
	dc.b $56,$00,$4A,$00,$14,$00,$1A,$00,$16,$00,$1A,$00,$46,$00,$36,$00
	dc.b $1A,$00,$58,$00,$16,$00,$1C,$00,$1C,$00,$36,$00,$1C,$00,$1C,$00
	dc.b $1C,$00,$1E,$00,$58,$00,$46,$00,$46,$00,$1E,$00,$1C,$00,$1C,$00
	dc.b $5A,$00,$5C,$00,$5E,$00,$62,$00,$1C,$00,$1C,$00,$1C,$00,$1E,$00
	dc.b $1C,$00,$64,$00,$68,$00,$1E,$00,$1E,$FF,$FF,$00,$46,$00,$6A,$FF
	dc.b $FF,$FF,$FF,$FF,$FF,$00,$1C,$00,$1C,$00,$6C,$00,$1C,$00,$1C,$00
	dc.b $1C,$00,$1E,$00,$6E,$00,$46,$00,$46,$00,$1E,$00,$1C,$00,$1C,$00
	dc.b $5A,$00,$5C,$00,$5E,$00,$62,$00,$1C,$00,$1C,$00,$1C,$00,$1E,$00
	dc.b $1C,$00,$64,$00,$68,$00,$1E,$00,$1E,$00,$20,$00,$20,$00,$6A,$00
	dc.b $20,$00,$20,$00,$20,$00,$20,$00,$70,$00,$6C,$00,$7E,$00,$20,$00
	dc.b $20,$00,$20,$00,$6E,$00,$20,$FF,$FF,$00,$80,$00,$72,$00,$20,$00
	dc.b $20,$00,$20,$00,$20
	dcb.b $10,$FF
	dc.b $00,$72,$00,$82,$00,$20,$00,$20,$FF,$FF,$00,$20,$00,$20,$00,$20
	dc.b $00,$20,$00,$70,$FF,$FF,$00,$7E,$00,$20,$00,$20,$00,$20,$00,$78
	dc.b $00,$20,$00,$78,$00,$80,$00,$72,$00,$20,$00,$20,$00,$20,$00,$20
	dc.b $00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22
	dc.b $00,$72,$00,$82,$00,$84,$00,$22,$00,$22,$00,$22,$00,$8A,$00,$22
	dc.b $00,$84,$00,$22,$00,$22,$00,$22,$FF,$FF,$00,$22,$FF,$FF,$00,$78
	dc.b $00,$34,$00,$78,$00,$34,$00,$34,$00,$7C,$FF,$FF,$00,$34,$00,$7C
	dc.b $00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22
	dc.b $00,$34,$00,$34,$00,$84,$00,$22,$00,$22,$00,$22,$00,$8A,$00,$22
	dc.b $00,$84,$00,$22,$00,$22,$00,$22,$00,$30,$00,$22,$00,$86,$00,$3C
	dc.b $00,$34,$00,$30,$00,$34,$00,$34,$00,$7C,$00,$30,$00,$34,$00,$7C
	dc.b $00,$86,$00,$3C,$00,$90,$00,$94,$00,$30,$00,$3C,$00,$3C,$FF,$FF
	dc.b $00,$34,$00,$34,$FF,$FF,$FF,$FF,$FF,$FF,$00,$88,$00,$96,$00,$88
	dc.b $FF,$FF,$FF,$FF,$FF,$FF,$00,$98,$00,$30,$00,$9A,$00,$86,$00,$3C
	dc.b $FF,$FF,$00,$30,$FF,$FF,$00,$9C,$FF,$FF,$00,$30,$FF,$FF,$00,$9E
	dc.b $00,$86,$00,$3C,$00,$90,$00,$94,$00,$30,$00,$3C,$00,$3C,$00,$60
	dc.b $00,$A2,$00,$60,$00,$60,$00,$60,$00,$60,$00,$88,$00,$96,$00,$88
	dc.b $00,$60,$00,$60,$00,$60,$00,$98,$00,$60,$00,$9A,$00,$60,$00,$A4
	dc.b $00,$60,$00,$A8,$00,$60,$00,$9C,$00,$74,$00,$74,$00,$74,$00,$9E
	dc.b $00,$A0,$00,$AA,$00,$AE,$00,$74,$00,$B0,$00,$A0,$00,$B2,$00,$60
	dc.b $00,$A2,$00,$60,$00,$60,$00,$60,$00,$60,$00,$74,$00,$74,$FF,$FF
	dc.b $00,$60,$00,$60,$00,$60,$00,$B6,$00,$60,$00,$A6,$00,$60,$00,$A4
	dc.b $00,$60,$00,$A8,$00,$60,$00,$A6,$00,$74,$00,$74,$00,$74,$00,$B8
	dc.b $00,$A0,$00,$AA,$00,$AE,$00,$74,$00,$B0,$00,$A0,$00,$B2,$00,$BC
	dc.b $00,$76,$00,$76,$00,$76,$FF,$FF,$00,$8E,$00,$74,$00,$74,$00,$76
	dc.b $00,$8E,$00,$76,$00,$76,$00,$B6,$00,$C2,$00,$A6,$00,$76,$00,$76
	dc.b $00,$76,$00,$7A,$00,$7A,$00,$A6,$00,$7A,$00,$8E,$00,$8E,$00,$B8
	dc.b $00,$BE,$00,$7A,$00,$8E,$00,$C4,$00,$BE,$00,$7A,$00,$7A,$00,$BC
	dc.b $00,$76,$00,$76,$00,$76,$00,$7A,$00,$8E,$FF,$FF,$FF,$FF,$00,$76
	dc.b $00,$8E,$00,$76,$00,$76,$00,$C6,$00,$C2,$FF,$FF,$00,$76,$00,$76
	dc.b $00,$76,$00,$7A,$00,$7A,$00,$CA,$00,$7A,$00,$8E,$00,$8E,$00,$AC
	dc.b $00,$BE,$00,$7A,$00,$8E,$00,$C4,$00,$BE,$00,$7A,$00,$7A,$FF,$FF
	dc.b $00,$CC,$FF,$FF,$00,$8C,$00,$7A,$00,$8C,$00,$8C,$00,$8C,$00,$8C
	dc.b $00,$8C,$00,$AC,$00,$8C,$00,$C6,$00,$D2,$00,$8C,$00,$8C,$00,$8C
	dc.b $00,$8C,$00,$D4,$00,$8C,$00,$CA,$00,$8C,$00,$8C,$00,$8C,$00,$AC
	dc.b $00,$92,$00,$92,$00,$92,$FF,$FF,$00,$92,$00,$BA,$FF,$FF,$00,$BA
	dc.b $00,$CC,$00,$92,$00,$8C,$00,$92,$00,$8C,$00,$8C,$00,$8C,$00,$8C
	dc.b $00,$8C,$00,$AC,$00,$8C,$FF,$FF,$00,$D2,$00,$8C,$00,$8C,$00,$8C
	dc.b $00,$8C,$00,$D4,$00,$8C,$00,$B4,$00,$8C,$00,$8C,$00,$8C,$00,$B4
	dc.b $00,$92,$00,$92,$00,$92,$00,$B4,$00,$92,$00,$BA,$00,$C8,$00,$BA
	dc.b $00,$D0,$00,$92,$00,$D6,$00,$92,$00,$C0,$00,$C0,$00,$C0,$00,$DE
	dc.b $00,$C8,$00,$C8,$00,$C0,$00,$D6,$00,$C0,$00,$D0,$00,$D6,$00,$C0
	dc.b $00,$EC,$FF,$FF,$FF,$FF,$00,$B4,$FF,$FF,$FF,$FF,$00,$C0,$00,$B4
	dc.b $FF,$FF,$FF,$FF,$00,$C0,$00,$B4,$FF,$FF,$FF,$FF,$00,$C8,$FF,$FF
	dc.b $00,$D0,$FF,$FF,$00,$D6,$FF,$FF,$00,$C0,$00,$C0,$00,$C0,$00,$DE
	dc.b $00,$C8,$00,$C8,$00,$C0,$00,$D6,$00,$C0,$00,$D0,$00,$D6,$00,$C0
	dc.b $00,$EC,$00,$CE,$00,$CE,$00,$CE,$00,$E0,$00,$D8,$00,$C0,$00,$CE
	dc.b $00,$E2,$00,$CE,$00,$C0,$00,$D8,$00,$CE,$00,$DA,$00,$DA,$00,$DC
	dc.b $00,$DC,$00,$D8,$00,$E8,$00,$CE,$00,$E0,$FF,$FF,$00,$E2,$00,$CE
	dc.b $00,$DC,$00,$E2,$00,$EE,$00,$E6,$00,$E8,$00,$DC,$00,$DC,$FF,$FF
	dc.b $FF,$FF,$00,$CE,$00,$CE,$00,$CE,$00,$E0,$00,$D8,$00,$F2,$00,$CE
	dc.b $00,$E2,$00,$CE,$00,$E6,$00,$D8,$00,$CE,$00,$DA,$00,$DA,$00,$DC
	dc.b $00,$DC,$00,$D8,$00,$E8,$00,$CE,$00,$E0,$00,$EA,$00,$E2,$00,$CE
	dc.b $00,$DC,$00,$E2,$00,$EE,$00,$E6,$00,$E8,$00,$DC,$00,$DC,$00,$EA
	dc.b $00,$F0,$00,$F4,$00,$F6,$00,$EA,$00,$EA,$00,$F8,$00,$F2,$00,$FA
	dc.b $00,$FC,$00,$F0,$00,$E6,$00,$FE,$01,$00,$01,$02,$01,$06,$01,$08
	dc.b $01,$0C,$01,$0E,$00,$F6,$01,$12,$01,$02,$00,$EA,$01,$14,$01,$16
	dc.b $FF,$FF,$FF,$FF,$01,$1C,$00,$FE,$01,$0C,$01,$06,$FF,$FF,$00,$EA
	dc.b $00,$F0,$00,$F4,$00,$F6,$00,$EA,$00,$EA,$00,$F8,$01,$1E,$00,$FA
	dc.b $00,$FC,$00,$F0,$01,$0A,$00,$FE,$01,$00,$01,$02,$01,$06,$01,$08
	dc.b $01,$0C,$01,$0E,$00,$F6,$01,$12,$01,$02,$01,$18,$01,$14,$01,$16
	dc.b $01,$0A,$01,$0A,$01,$1C,$00,$FE,$01,$0C,$01,$06,$01,$10,$01,$20
	dc.b $01,$10,$01,$10,$01,$10,$01,$10,$01,$24,$01,$18,$01,$1E,$01,$10
	dc.b $01,$10,$01,$10,$01,$0A,$01,$10,$01,$1A,$01,$2C,$FF,$FF,$01,$10
	dc.b $01,$1A,$01,$10,$01,$2E,$01,$34,$01,$36,$01,$18,$FF,$FF,$01,$34
	dc.b $01,$0A,$01,$0A,$01,$38,$01,$3A,$01,$3C,$FF,$FF,$01,$10,$01,$20
	dc.b $01,$10,$01,$10,$01,$10,$01,$10,$01,$24,$01,$18,$01,$22,$01,$10
	dc.b $01,$10,$01,$10,$01,$3E,$01,$10,$01,$1A,$01,$2C,$01,$22,$01,$10
	dc.b $01,$1A,$01,$10,$01,$2E,$01,$34,$01,$36,$01,$42,$01,$22,$01,$34
	dc.b $01,$48,$01,$58,$01,$38,$01,$3A,$01,$3C,$01,$22,$01,$5E,$01,$64
	dc.b $01,$66,$01,$6C,$FF,$FF,$01,$72,$01,$74,$01,$76,$01,$22,$01,$78
	dc.b $01,$7A,$01,$7C,$01,$3E,$01,$70,$01,$7E,$01,$80,$01,$22,$FF,$FF
	dc.b $01,$8A,$01,$8C,$01,$8E,$01,$90,$FF,$FF,$01,$42,$01,$22,$01,$9A
	dc.b $01,$48,$01,$58,$01,$70,$01,$84,$01,$7E,$01,$22,$01,$5E,$01,$64
	dc.b $01,$66,$01,$6C,$01,$70,$01,$72,$01,$74,$01,$76,$01,$70,$01,$78
	dc.b $01,$7A,$01,$7C,$01,$84,$01,$86,$01,$7E,$01,$80,$FF,$FF,$01,$88
	dc.b $01,$8A,$01,$8C,$01,$8E,$01,$90,$01,$94,$01,$86,$01,$98,$01,$9A
	dc.b $01,$98,$01,$88,$01,$70,$01,$84,$01,$7E,$01,$88,$01,$88,$01,$9C
	dc.b $01,$9E,$01,$A2,$01,$70,$01,$A0,$01,$94,$01,$9C,$01,$70,$01,$A6
	dc.b $01,$A8,$01,$9C,$01,$84,$01,$86,$01,$AA,$01,$AC,$01,$9C,$01,$88
	dc.b $01,$A0,$01,$AE,$01,$B0,$01,$B2,$01,$94,$01,$86,$01,$98,$01,$B4
	dc.b $01,$98,$01,$88,$FF,$FF,$01,$B8,$01,$A6,$01,$88,$01,$88,$01,$9C
	dc.b $01,$9E,$01,$A2,$01,$B8,$01,$A0,$01,$94,$01,$9C,$01,$BA,$01,$A6
	dc.b $01,$A8,$01,$9C,$01,$B8,$FF,$FF,$01,$AA,$01,$AC,$01,$9C,$01,$BE
	dc.b $01,$A0,$01,$AE,$01,$B0,$01,$B2,$01,$BE,$01,$BA,$01,$BC,$01,$B4
	dc.b $01,$BC,$01,$C6,$01,$BE,$01,$B8,$01,$A6,$01,$BC,$01,$C0,$01,$C0
	dc.b $01,$C8,$01,$CA,$01,$B8,$01,$CA,$01,$CE,$01,$D0,$01,$BA,$01,$C0
	dc.b $01,$D2,$01,$C4,$01,$B8,$01,$C4,$01,$D4,$01,$C0,$01,$D2,$01,$BE
	dc.b $01,$C4,$01,$D8,$01,$C4,$FF,$FF,$01,$BE,$01,$BA,$01,$BC,$01,$D6
	dc.b $01,$BC,$01,$C6,$01,$BE,$01,$D6,$FF,$FF,$01,$BC,$01,$C0,$01,$C0
	dc.b $01,$C8,$01,$CA,$FF,$FF,$01,$CA,$01,$CE,$01,$D0,$01,$DA,$01,$C0
	dc.b $01,$D2,$01,$C4,$01,$DC,$01,$C4,$01,$D4,$01,$C0,$01,$D2,$01,$DE
	dc.b $01,$C4,$01,$D8,$01,$C4,$01,$CC,$01,$CC,$01,$CC,$01,$E0,$01,$D6
	dc.b $01,$E4,$01,$E2,$01,$CC,$01,$D6,$01,$CC,$01,$CC,$01,$E6,$01,$E8
	dc.b $01,$CC,$01,$CC,$01,$CC,$01,$CC,$01,$EA,$01,$EC,$01,$DA,$01,$EE
	dc.b $FF,$FF,$01,$F2,$01,$DC,$01,$E2,$01,$F4,$01,$EE,$01,$F6,$01,$DE
	dc.b $01,$FC,$FF,$FF,$FF,$FF,$01,$CC,$01,$CC,$01,$CC,$01,$E0,$FF,$FF
	dc.b $01,$E4,$01,$E2,$01,$CC,$FF,$FF,$01,$CC,$01,$CC,$01,$E6,$01,$E8
	dc.b $01,$CC,$01,$CC,$01,$CC,$01,$CC,$01,$EA,$01,$EC,$01,$F0,$01,$EE
	dc.b $01,$F0,$01,$F2,$01,$FA,$01,$E2,$01,$F4,$01,$EE,$01,$F6,$01,$FE
	dc.b $01,$FC,$01,$FA,$02,$00,$02,$06,$02,$02,$02,$0E,$02,$02,$02,$04
	dc.b $02,$00,$01,$FA,$01,$F0,$02,$02,$02,$04,$02,$10,$01,$FE,$FF,$FF
	dc.b $FF,$FF,$02,$12,$02,$04,$02,$14,$02,$16,$02,$18,$01,$F0,$FF,$FF
	dc.b $01,$F0,$02,$1E,$01,$FA
	dcb.b $8,$FF
	dc.b $01,$FE,$02,$28,$01,$FA,$02,$00,$02,$06,$02,$02,$02,$0E,$02,$02
	dc.b $02,$04,$02,$00,$01,$FA,$01,$F0,$02,$02,$02,$04,$02,$10,$01,$FE
	dc.b $02,$08,$02,$08,$02,$12,$02,$04,$02,$14,$02,$16,$02,$18,$02,$20
	dc.b $02,$0C,$02,$08,$02,$1E,$02,$0C,$02,$08,$02,$0C,$02,$22,$02,$08
	dc.b $02,$08,$02,$28,$02,$0C,$02,$32,$02,$0C,$02,$34,$02,$20,$02,$24
	dc.b $02,$24,$02,$24,$02,$2A,$02,$36,$02,$2A,$02,$22,$02,$38,$FF,$FF
	dc.b $02,$08,$02,$08,$02,$40,$02,$42,$02,$2A,$02,$44,$FF,$FF,$02,$20
	dc.b $02,$0C,$02,$08,$02,$48,$02,$0C,$02,$08,$02,$0C,$02,$22,$02,$08
	dc.b $02,$08,$02,$4A,$02,$0C,$02,$32,$02,$0C,$02,$34,$02,$20,$02,$24
	dc.b $02,$24,$02,$24,$02,$2A,$02,$36,$02,$2A,$02,$22,$02,$38,$02,$3E
	dc.b $02,$4C,$02,$4E,$02,$40,$02,$42,$02,$2A,$02,$44,$02,$46,$02,$52
	dc.b $02,$46,$02,$3E,$02,$48,$02,$5A,$02,$5C,$02,$5E,$02,$60,$FF,$FF
	dc.b $FF,$FF,$02,$4A,$02,$62,$02,$64,$02,$66,$02,$68,$02,$74,$02,$76
	dc.b $02,$78,$02,$7A,$02,$6A,$02,$7C,$02,$7E,$FF,$FF,$02,$60,$02,$3E
	dc.b $02,$4C,$02,$4E,$02,$62,$02,$64,$02,$66,$02,$68,$02,$46,$02,$52
	dc.b $02,$46,$02,$3E,$02,$6A,$02,$5A,$02,$5C,$02,$5E,$02,$60,$02,$6C
	dc.b $02,$6E,$FF,$FF,$02,$62,$02,$64,$02,$66,$02,$68,$02,$74,$02,$76
	dc.b $02,$78,$02,$7A,$02,$6A,$02,$7C,$02,$7E,$02,$82,$02,$60,$02,$6C
	dc.b $02,$6E,$02,$90,$02,$62,$02,$64,$02,$66,$02,$68,$02,$70,$02,$70
	dc.b $02,$70,$02,$84,$02,$6A,$02,$80,$02,$70,$02,$82,$02,$70,$02,$6C
	dc.b $02,$6E,$02,$70,$02,$86,$02,$88,$02,$8A,$02,$8C,$02,$92,$02,$94
	dc.b $02,$70,$02,$84,$02,$8E,$02,$80,$02,$70,$02,$82,$02,$80,$02,$6C
	dc.b $02,$6E,$02,$90,$02,$86,$02,$88,$02,$8A,$02,$8C,$02,$70,$02,$70
	dc.b $02,$70,$02,$84,$02,$8E,$02,$80,$02,$70,$02,$82,$02,$70,$02,$96
	dc.b $02,$9A,$02,$70,$02,$86,$02,$88,$02,$8A,$02,$8C,$02,$92,$02,$94
	dc.b $02,$70,$02,$84,$02,$8E,$02,$80,$02,$70,$02,$9C,$02,$80,$02,$A0
	dc.b $02,$A2,$02,$A4,$02,$86,$02,$88,$02,$8A,$02,$8C,$02,$A2,$02,$A6
	dc.b $02,$B2,$02,$B8,$02,$8E,$02,$D2,$02,$DA,$FF,$FF,$02,$E4,$02,$96
	dc.b $02,$9A,$FF,$FF,$02,$DE,$02,$E8,$02,$DE,$02,$FA,$02,$FC,$02,$FE
	dc.b $03,$00,$03,$04,$02,$D4,$03,$0E,$03,$10,$02,$9C,$03,$12,$02,$A0
	dc.b $02,$A2,$02,$A4,$02,$D4,$03,$14,$02,$FC,$02,$FC,$02,$A2,$02,$A6
	dc.b $02,$B2,$02,$B8,$02,$D4,$02,$D2,$02,$DA,$02,$D4,$02,$E4,$03,$26
	dc.b $03,$28,$02,$D4,$02,$DE,$02,$E8,$02,$DE,$02,$FA,$02,$FC,$02,$FE
	dc.b $03,$00,$03,$04,$02,$D4,$03,$0E,$03,$10,$03,$2A,$03,$12,$03,$2C
	dc.b $03,$2E,$03,$30,$02,$D4,$03,$14,$02,$FC,$02,$FC,$03,$32,$03,$3C
	dc.b $03,$3E,$03,$44,$02,$D4,$03,$52,$03,$54,$02,$D4,$03,$56,$03,$26
	dc.b $03,$28,$02,$D4,$03,$78,$03,$7A,$03,$44,$03,$7C,$03,$80,$03,$88
	dc.b $03,$44,$03,$94,$03,$9A,$03,$9C,$03,$A2,$03,$2A,$03,$AC,$03,$2C
	dc.b $03,$2E,$03,$30,$03,$AE,$03,$B6,$FF,$FF,$03,$AC,$03,$32,$03,$3C
	dc.b $03,$3E,$03,$44,$03,$BA,$03,$52,$03,$54,$03,$AC,$03,$56,$03,$BE
	dc.b $03,$B2,$03,$AE,$03,$78,$03,$7A,$03,$44,$03,$7C,$03,$80,$03,$88
	dc.b $03,$44,$03,$94,$03,$9A,$03,$9C,$03,$A2,$03,$B0,$03,$AC,$03,$B2
	dc.b $03,$C8,$03,$CA,$03,$AE,$03,$B6,$03,$B0,$03,$AC,$03,$C0,$03,$C2
	dc.b $03,$CC,$03,$CE,$03,$BA,$03,$D2,$03,$B0,$03,$AC,$03,$DA,$03,$BE
	dc.b $03,$B2,$03,$AE,$03,$D2,$03,$D4,$03,$E2,$03,$C0,$03,$C2,$03,$D6
	dc.b $03,$E6,$03,$D6,$03,$D2,$03,$E8,$03,$EA,$03,$B0,$03,$D6,$03,$B2
	dc.b $03,$C8,$03,$CA,$03,$D4,$03,$EC,$03,$B0,$03,$D8,$03,$C0,$03,$C2
	dc.b $03,$CC,$03,$CE,$03,$D8,$03,$D2,$03,$B0,$FF,$FF,$03,$DA,$03,$EE
	dc.b $03,$D8,$03,$F2,$03,$D2,$03,$D4,$03,$E2,$03,$C0,$03,$C2,$03,$D6
	dc.b $03,$E6,$03,$D6,$03,$D2,$03,$E8,$03,$EA,$03,$F6,$03,$D6,$03,$DC
	dc.b $03,$DC,$03,$F4,$03,$D4,$03,$EC,$03,$E0,$03,$D8,$03,$E0,$03,$FC
	dc.b $03,$DC,$03,$F4,$03,$D8,$03,$E0,$04,$06,$03,$E0,$03,$DC,$03,$EE
	dc.b $03,$D8,$03,$F2,$03,$F8,$03,$F8,$04,$0A,$04,$0C,$04,$0E,$04,$10
	dc.b $04,$12,$04,$14,$04,$1A,$04,$1A,$04,$24,$03,$F6,$04,$26,$03,$DC
	dc.b $03,$DC,$03,$F4,$04,$28,$04,$1A,$03,$E0,$04,$1E,$03,$E0,$03,$FC
	dc.b $03,$DC,$03,$F4,$04,$1E,$03,$E0,$04,$06,$03,$E0,$03,$DC,$03,$F8
	dc.b $04,$2C,$04,$30,$04,$34,$04,$36,$04,$0A,$04,$0C,$04,$0E,$04,$10
	dc.b $04,$12,$04,$14,$04,$1A,$04,$1A,$04,$24,$04,$2A,$04,$26,$04,$2C
	dc.b $04,$30,$04,$3A,$04,$28,$04,$1A,$04,$2A,$04,$1E,$04,$2E,$04,$3C
	dc.b $04,$40,$04,$44,$04,$1E,$04,$46,$04,$2A,$04,$2E,$04,$4C,$03,$F8
	dc.b $04,$2C,$04,$30,$04,$34,$04,$36,$04,$48,$04,$2E,$04,$4E,$04,$50
	dc.b $04,$54,$04,$68,$04,$46,$04,$6A,$04,$6C,$04,$2A,$04,$6E,$04,$2C
	dc.b $04,$30,$04,$3A,$04,$72,$04,$48,$04,$2A,$04,$76,$04,$2E,$04,$3C
	dc.b $04,$40,$04,$44,$04,$78,$04,$46,$04,$2A,$04,$2E,$04,$4C,$04,$7A
	dc.b $04,$7C,$04,$7E,$04,$8A,$04,$8C,$04,$48,$04,$2E,$04,$4E,$04,$50
	dc.b $04,$54,$04,$68,$04,$46,$04,$6A,$04,$6C,$04,$8E,$04,$6E,$04,$90
	dc.b $FF,$FF,$04,$C6,$04,$72,$04,$48,$04,$80,$04,$76,$FF,$FF,$04,$B6
	dc.b $04,$B8,$04,$BA,$04,$78,$04,$BC,$04,$BE,$04,$CA,$04,$C0,$04,$7A
	dc.b $04,$7C,$04,$7E,$04,$8A,$04,$8C,$04,$80,$04,$C2,$04,$80,$04,$B6
	dc.b $04,$B8,$04,$BA,$04,$C4,$04,$BC,$04,$BE,$04,$8E,$04,$C0,$04,$90
	dc.b $04,$80,$04,$C6,$FF,$FF,$04,$80,$04,$80,$04,$C2,$04,$80,$04,$B6
	dc.b $04,$B8,$04,$BA,$04,$C4,$04,$BC,$04,$BE,$04,$CA,$04,$C0,$04,$CE
	dc.b $04,$D0,$04,$D6,$04,$F4,$04,$F6,$04,$80,$04,$C2,$04,$80,$04,$B6
	dc.b $04,$B8,$04,$BA,$04,$C4,$04,$BC,$04,$BE,$04,$CC,$04,$C0,$04,$F8
	dc.b $04,$80,$04,$FA,$04,$CC,$04,$80,$04,$80,$04,$C2,$04,$80,$04,$FE
	dc.b $05,$06,$05,$08,$04,$C4,$05,$0C,$05,$16,$05,$1C,$05,$1E,$04,$CE
	dc.b $04,$D0,$04,$D6,$04,$F4,$04,$F6,$05,$20,$FF,$FF,$05,$20
	dcb.b $8,$FF
	dc.b $05,$48,$05,$52,$04,$CC,$FF,$FF,$04,$F8,$FF,$FF,$04,$FA,$04,$CC
	dc.b $05,$34,$05,$4A,$05,$34,$FF,$FF,$04,$FE,$05,$06,$05,$08,$05,$56
	dc.b $05,$0C,$05,$16,$05,$1C,$05,$1E,$05,$4A,$05,$5C,$05,$62,$05,$8C
	dc.b $05,$4A,$05,$20,$05,$26,$05,$20,$05,$26,$05,$26,$05,$26,$05,$26
	dc.b $05,$48,$05,$52,$05,$98,$05,$26,$05,$26,$05,$26,$05,$A0,$05,$26
	dc.b $05,$34,$05,$4A,$05,$34,$05,$26,$05,$96,$05,$26,$05,$A4,$05,$56
	dc.b $05,$A8,$05,$98,$05,$9A,$05,$96,$05,$4A,$05,$5C,$05,$62,$05,$8C
	dc.b $05,$4A,$05,$9A,$05,$26,$05,$96,$05,$26,$05,$26,$05,$26,$05,$26
	dc.b $05,$9C,$05,$9A,$05,$98,$05,$26,$05,$26,$05,$26,$05,$A0,$05,$26
	dc.b $05,$AA,$05,$AC,$05,$B2,$05,$26,$05,$96,$05,$26,$05,$A4,$05,$9C
	dc.b $05,$A8,$05,$98,$05,$9A,$05,$96,$05,$B8,$05,$BC,$05,$BE,$05,$AA
	dc.b $05,$AC,$05,$9A,$05,$C0,$05,$96,$05,$C2,$05,$C8,$05,$CC,$05,$CE
	dc.b $05,$9C,$05,$9A,$05,$CA,$05,$D6,$05,$DA,$05,$DE,$05,$E0,$05,$E4
	dc.b $05,$AA,$05,$AC,$05,$B2,$05,$EC,$05,$CA,$06,$04,$06,$14,$05,$9C
	dc.b $06,$18,$FF,$FF,$FF,$FF,$06,$1A,$05,$B8,$05,$BC,$05,$BE,$05,$AA
	dc.b $05,$AC,$06,$1C,$05,$C0,$06,$1E,$05,$C2,$05,$C8,$05,$CC,$05,$CE
	dc.b $06,$20,$06,$22,$05,$CA,$05,$D6,$05,$DA,$05,$DE,$05,$E0,$05,$E4
	dc.b $06,$16,$06,$16,$06,$16,$05,$EC,$05,$CA,$06,$04,$06,$14,$06,$16
	dc.b $06,$18,$06,$16,$06,$16,$06,$1A,$06,$24,$06,$26,$06,$16,$06,$16
	dc.b $06,$16,$06,$1C,$06,$2C,$06,$1E,$06,$3C,$06,$3E,$06,$40,$06,$42
	dc.b $06,$20,$06,$22,$06,$64,$06,$6C,$06,$6E,$06,$76,$06,$66,$06,$72
	dc.b $06,$16,$06,$16,$06,$16,$06,$66,$06,$72,$06,$7C,$FF,$FF,$06,$16
	dc.b $FF,$FF,$06,$16,$06,$16,$FF,$FF,$06,$24,$06,$26,$06,$16,$06,$16
	dc.b $06,$16,$06,$80,$06,$2C,$06,$82,$06,$3C,$06,$3E,$06,$40,$06,$42
	dc.b $06,$92,$06,$8C,$06,$64,$06,$6C,$06,$6E,$06,$76,$06,$66,$06,$72
	dc.b $06,$74,$06,$74,$06,$74,$06,$66,$06,$72,$06,$7C,$06,$74,$06,$A6
	dc.b $06,$74,$06,$8C,$06,$CC,$06,$74,$06,$CE,$06,$D6,$06,$DC,$06,$E0
	dc.b $06,$E2,$06,$80,$06,$74,$06,$82,$06,$E4,$06,$EC,$06,$74,$06,$EE
	dc.b $06,$92,$06,$8C,$06,$F8,$07,$00,$06,$F6,$07,$02,$06,$F6,$06,$F8
	dc.b $06,$74,$06,$74,$06,$74,$06,$F6,$06,$F4,$06,$F8,$06,$74,$06,$A6
	dc.b $06,$74,$06,$8C,$06,$CC,$06,$74,$06,$CE,$06,$D6,$06,$DC,$06,$E0
	dc.b $06,$E2,$06,$F2,$06,$74,$06,$F4,$06,$E4,$06,$EC,$06,$74,$06,$EE
	dc.b $06,$F2,$07,$08,$06,$F8,$07,$00,$06,$F6,$07,$02,$06,$F6,$06,$F8
	dc.b $06,$F2,$06,$FA,$06,$FA,$06,$F6,$06,$F4,$06,$F8,$06,$FE,$07,$0A
	dc.b $06,$FE,$07,$0E,$06,$FA,$07,$22,$07,$24,$06,$FE,$07,$2A,$06,$FE
	dc.b $06,$FA,$06,$F2,$07,$1C,$06,$F4,$07,$3C,$07,$2C,$FF,$FF,$FF,$FF
	dc.b $06,$F2,$07,$08,$FF,$FF,$07,$3E,$07,$50,$07,$5E,$07,$2A,$07,$1C
	dc.b $06,$F2,$06,$FA,$06,$FA,$07,$1C,$07,$1C,$07,$2C,$06,$FE,$07,$0A
	dc.b $06,$FE,$07,$0E,$06,$FA,$07,$22,$07,$24,$06,$FE,$07,$2A,$06,$FE
	dc.b $06,$FA,$07,$2E,$07,$1C,$FF,$FF,$07,$3C,$07,$2C,$07,$30,$07,$32
	dc.b $07,$34,$07,$36,$07,$38,$07,$3E,$07,$50,$07,$5E,$07,$2A,$07,$1C
	dc.b $07,$6A,$07,$2E,$07,$72,$07,$1C,$07,$1C,$07,$2C,$07,$30,$07,$32
	dc.b $07,$34,$07,$36,$07,$38,$07,$76,$07,$68,$07,$6C,$07,$6E,$07,$6A
	dc.b $07,$7A,$07,$2E,$FF,$FF,$07,$68,$07,$6C,$07,$7C,$07,$30,$07,$32
	dc.b $07,$34,$07,$36,$07,$38,$07,$68,$07,$6C,$07,$6E,$07,$88,$07,$8C
	dc.b $07,$6A,$07,$2E,$07,$72,$07,$7E,$07,$7C,$07,$96,$07,$30,$07,$32
	dc.b $07,$34,$07,$36,$07,$38,$07,$76,$07,$68,$07,$6C,$07,$6E,$07,$6A
	dc.b $07,$7A,$07,$C2,$07,$7E,$07,$68,$07,$6C,$07,$7C
	dcb.b $A,$FF
	dc.b $07,$68,$07,$6C,$07,$6E,$07,$88,$07,$8C,$FF,$FF,$FF,$FF,$FF,$FF
	dc.b $07,$7E,$07,$7C,$07,$96
	dcb.b $16,$FF
	dc.b $07,$C2,$07,$7E
	dcb.b $132,$FF
loc_0_0000E070:
	dcb.b $8,$00
	dc.b $0D,$FE
	dcb.b $11E,$00
	dc.b $0C,$E6,$00,$02
	dcb.b $8,$00
	dc.b $0D,$C8
	dcb.b $82,$00
	dc.b $4E,$1A
	dcb.b $74,$00
	dc.b $80,$00,$13,$0E,$80
	dcb.b $5D,$00
	dc.b $2B,$CE
	dcb.b $1A,$00
	dc.b $51,$C0,$2D,$42,$80
	dcb.b $25,$00
	dc.b $50,$C0,$2D,$42,$80
	dcb.b $31,$00
	dc.b $51,$F8,$30,$14,$80
	dcb.b $31,$00
	dc.b $50,$F8,$30,$14,$80
	dcb.b $1F,$00
	dc.b $D0,$00,$01,$5E,$80,$00,$C0,$00,$13,$0E,$80,$00,$E1,$00,$2E,$98
	dc.b $80,$00,$E0,$00,$2E,$98,$80,$00,$64,$00,$02,$F4,$80
	dcb.b $D,$00
	dc.b $65,$00,$02,$F4,$80,$00,$67,$00,$02,$F4,$80
	dcb.b $25,$00
	dc.b $6C,$00,$02,$F4,$80,$00,$00,$00,$00,$00,$00,$00,$6E,$00,$02,$F4
	dc.b $80,$00,$62,$00,$02,$F4,$80,$00,$00,$00,$00,$00,$00,$00,$6F,$00
	dc.b $02,$F4,$80,$00,$63,$00,$02,$F4,$80,$00,$6D,$00,$02,$F4,$80,$00
	dc.b $6B,$00,$02,$F4,$80,$00,$66,$00,$02,$F4,$80,$00,$6A,$00,$02,$F4
	dc.b $80,$00,$60,$00,$02,$F4,$80,$00,$00,$00,$00,$00,$00,$00,$61,$00
	dc.b $02,$F4,$80,$00,$00,$00,$2D,$5A
	dcb.b $8,$00
	dc.b $68,$00,$02,$F4,$80,$00,$69,$00,$02,$F4,$80
	dcb.b $D,$00
	dc.b $08,$C0,$06,$EC,$80,$00,$41,$80,$08,$DA,$80,$00,$00,$00,$00,$00
	dc.b $00,$00,$42,$00,$30,$72,$80,$00,$B0,$00,$0A,$5C,$80
	dcb.b $31,$00
	dc.b $51,$C8,$0B,$CC,$80
	dcb.b $2B,$00
	dc.b $50,$C8,$0B,$CC,$80
	dcb.b $9,$00
	dc.b $0C,$18
	dcb.b $10,$00
	dc.b $0D,$E6,$40,$00,$B0,$00,$13,$0E,$80,$00,$00,$00,$0D,$FE
	dcb.b $8,$00
	dc.b $C1,$00,$0E,$FA,$80,$00,$48,$80,$0F,$50,$80
	dcb.b $2B,$00
	dc.b $F0,$80,$3C,$48,$80,$01
	dcb.b $1E,$00
	dc.b $F0,$8F,$3C,$48,$80,$01
	dcb.b $9E,$00
	dc.b $41,$22,$80,$01
	dcb.b $31,$00
	dc.b $0F,$41,$22,$80,$01
	dcb.b $2C,$00
	dc.b $4D,$40,$00,$00,$00,$00,$4D,$76
	dcb.b $1C,$00
	dc.b $0F,$F2
	dcb.b $E,$00
	dc.b $4E,$C0,$10,$F0,$80,$00,$4E,$80,$10,$F0,$80,$00,$41,$C0,$11,$00
	dc.b $80
	dcb.b $19,$00
	dc.b $E1,$08,$2E,$98,$80,$00,$E0,$08,$2E,$98,$80
	dcb.b $25,$00
	dc.b $44,$00,$30,$72,$80,$00,$00,$00,$00,$00,$00,$00,$4E,$71,$58,$F0
	dc.b $80,$00,$46,$00,$30,$72,$80
	dcb.b $9,$00
	dc.b $26,$22,$40,$00,$00,$00,$1D,$12,$00,$00,$00,$00,$12,$8A,$80
	dcb.b $49,$00
	dc.b $48,$40,$2A,$B2,$80
	dcb.b $6F,$00
	dc.b $2B,$66
	dcb.b $E,$00
	dc.b $E1,$18,$2E,$98,$80,$00,$E0,$18,$2E,$98,$80
	dcb.b $13,$00
	dc.b $4E,$74,$2C,$F0,$80,$00,$4E,$73,$58,$E4,$80,$00,$06,$C0,$2D,$0E
	dc.b $80,$00,$4E,$77,$58,$F0,$80,$00,$4E,$75,$58,$F0,$80,$00,$00,$00
	dc.b $00,$00,$00,$00,$54,$C0,$2D,$42,$80,$00,$55,$C0,$2D,$42,$80,$00
	dc.b $00,$00,$00,$00,$00,$00,$57,$C0,$2D,$42,$80,$00,$00,$00,$2E,$16
	dc.b $00,$00,$5C,$C0,$2D,$42,$80,$00,$5E,$C0,$2D,$42,$80,$00,$52,$C0
	dc.b $2D,$42,$80,$00,$5F,$C0,$2D,$42,$80,$00,$53,$C0,$2D,$42,$80,$00
	dc.b $5D,$C0,$2D,$42,$80,$00,$5B,$C0,$2D,$42,$80,$00,$56,$C0,$2D,$42
	dc.b $80,$00,$00,$00,$2F,$20,$40,$00,$5A,$C0,$2D,$42,$80,$00,$00,$00
	dc.b $00,$00,$00,$00,$90,$00,$01,$5E,$80,$00,$58,$C0,$2D,$42,$80,$00
	dc.b $59,$C0,$2D,$42,$80,$00,$00,$00,$00,$00,$00,$00,$4A,$C0,$2F,$86
	dc.b $80,$00,$00,$00,$00,$00,$00,$00,$54,$F8,$30,$14,$80,$00,$55,$F8
	dc.b $30,$14,$80,$00,$00,$00,$00,$00,$00,$00,$57,$F8,$30,$14,$80,$00
	dc.b $00,$00,$00,$00,$00,$00,$5C,$F8,$30,$14,$80,$00,$5E,$F8,$30,$14
	dc.b $80,$00,$52,$F8,$30,$14,$80,$00,$5F,$F8,$30,$14,$80,$00,$53,$F8
	dc.b $30,$14,$80,$00,$5D,$F8,$30,$14,$80,$00,$5B,$F8,$30,$14,$80,$00
	dc.b $56,$F8,$30,$14,$80,$00,$00,$00,$00,$00,$00,$00,$5A,$F8,$30,$14
	dc.b $80
	dcb.b $D,$00
	dc.b $50,$F8,$30,$14,$80,$00,$00,$00,$00,$00,$00,$00,$4A,$00,$30,$7E
	dc.b $80,$00,$00,$00,$30,$92,$40,$00,$58,$F8,$30,$14,$80,$00,$59,$F8
	dc.b $30,$14,$80
	dcb.b $19,$00
	dc.b $C1,$00,$00,$08,$80,$00,$D0,$C0,$02,$1E,$80,$00,$06,$00,$02,$A0
	dc.b $80,$00,$50,$00,$15,$04,$80,$00,$D1,$00,$00,$02,$80,$00,$02,$00
	dc.b $12,$8A,$80,$00,$08,$40,$06,$64,$80,$00,$08,$80,$06,$64,$80
	dcb.b $2B,$00
	dc.b $4A,$FA,$4B,$1E,$80,$00,$48,$48,$04,$6A,$80,$00,$08,$C0,$06,$64
	dc.b $80,$00,$08,$00,$05,$E6,$80
	dcb.b $D,$00
	dc.b $0C,$FC,$07,$4E,$80,$00,$08,$C0,$09,$1A,$80
	dcb.b $8,$00
	dc.b $C0,$09,$1A,$80,$00,$B0,$C0,$02,$1E,$80,$00,$0C,$00,$02,$C6,$80
	dc.b $00,$B1,$08,$0B,$16,$80,$00,$00,$00,$0B,$4A,$00,$00,$00,$00,$2D
	dc.b $68
	dcb.b $16,$00
	dc.b $2D,$52,$00,$00,$54,$C8,$0B,$CC,$80,$00,$55,$C8,$0B,$CC,$80,$00
	dc.b $57,$C8,$0B,$CC,$80,$00,$5C,$C8,$0B,$CC,$80,$00,$5E,$C8,$0B,$CC
	dc.b $80,$00,$52,$C8,$0B,$CC,$80,$00,$5F,$C8,$0B,$CC,$80,$00,$53,$C8
	dc.b $0B,$CC,$80,$00,$5D,$C8,$0B,$CC,$80,$00,$5B,$C8,$0B,$CC,$80,$00
	dc.b $56,$C8,$0B,$CC,$80,$00,$5A,$C8,$0B,$CC,$80,$00,$51,$C8,$0B,$CC
	dc.b $80,$00,$58,$C8,$0B,$CC,$80,$00,$59,$C8,$0B,$CC,$80,$00,$81,$C0
	dc.b $09,$BA,$80,$00,$80,$C0,$09,$BA,$80,$00,$00,$00,$4F,$78,$40,$00
	dc.b $00,$00,$4F,$54
	dcb.b $A,$00
	dc.b $55,$80,$00,$00,$00,$00,$57,$22,$00,$00,$0A,$00,$12,$8A,$80
	dcb.b $9,$00
	dc.b $0E,$82,$00,$00,$00,$00,$0E,$EC,$80,$00,$49,$C0,$0F,$6A,$80,$00
	dc.b $48,$80,$0F,$82,$80,$00,$00,$18,$40,$80,$80,$01,$00,$00,$00,$00
	dc.b $00,$00,$00,$22,$40,$80,$80,$01,$00,$00,$0F,$9C,$40
	dcb.b $D,$00
	dc.b $F0,$81,$3C,$48,$80,$01,$F0,$93,$3C,$48,$80,$01,$F0,$96,$3C,$48
	dc.b $80,$01,$F0,$92,$3C,$48,$80,$01,$F0,$95,$3C,$48,$80,$01,$F0,$94
	dc.b $3C,$48,$80,$01,$F0,$8E,$3C,$48,$80,$01
	dcb.b $18,$00
	dc.b $F0,$87,$3C,$48,$80,$01,$00,$00,$00,$00,$00,$00,$F0,$90,$3C,$48
	dc.b $80,$01,$00,$00,$00,$00,$00,$00,$F0,$9F,$3C,$48,$80,$01
	dcb.b $12,$00
	dc.b $F0,$88,$3C,$48,$80,$01,$00,$38,$40,$80,$80,$01,$00,$1D,$40,$80
	dc.b $80,$01
	dcb.b $14,$00
	dc.b $3C,$50,$80,$01
	dcb.b $25,$00
	dc.b $0F,$3C,$50,$80,$01
	dcb.b $D,$00
	dc.b $20,$40,$80,$80,$01
	dcb.b $20,$00
	dc.b $3B,$6C,$00,$01
	dcb.b $D,$00
	dc.b $01,$40,$80,$80,$01,$00,$00,$00,$00,$00,$00,$00,$21,$40,$80,$80
	dc.b $01,$00,$00,$00,$00,$00,$00,$00,$23,$40,$80,$80,$01,$00,$1A,$40
	dc.b $80,$80,$01,$F0,$80,$40,$46,$80,$01,$00,$00,$3A,$C8,$40
	dcb.b $8,$00
	dc.b $25,$40,$80,$80,$01
	dcb.b $25,$00
	dc.b $01,$41,$22,$80,$01,$00,$13,$41,$22,$80,$01,$00,$16,$41,$22,$80
	dc.b $01,$00,$12,$41,$22,$80,$01,$00,$0E,$40,$80,$80,$01,$00,$15,$41
	dc.b $22,$80,$01,$00,$14,$41,$22,$80,$01
	dcb.b $D,$00
	dc.b $0E,$41,$22,$80,$01
	dcb.b $19,$00
	dc.b $07,$41,$22,$80,$01
	dcb.b $D,$00
	dc.b $10,$41,$22,$80,$01
	dcb.b $D,$00
	dc.b $1F,$41,$22,$80,$01,$00,$00,$00,$00,$00,$00,$00,$28,$40,$80,$80
	dc.b $01
	dcb.b $13,$00
	dc.b $08,$41,$22,$80,$01,$00,$0F,$40,$80,$80,$01
	dcb.b $D,$00
	dc.b $3A,$41,$C8,$80,$01
	dcb.b $8,$00
	dc.b $15,$52,$00,$00,$00,$00,$4E,$14,$00,$00,$00,$00,$4E,$02,$00,$00
	dc.b $00,$00,$4D,$FC,$00,$00,$00,$00,$4E,$0E,$00,$00,$00,$00,$4E,$08
	dc.b $00,$00,$00,$00,$4D,$48,$00,$00,$00,$00,$4D,$8A,$00,$00,$00,$00
	dc.b $4E,$1A
	dcb.b $1A,$00
	dc.b $4E,$50,$11,$AE,$80,$00,$00,$00,$EA,$A8,$40,$00,$00,$00,$12,$68
	dc.b $40
	dcb.b $21,$00
	dc.b $16,$30,$80,$00,$C1,$C0,$09,$BA,$80,$00,$C0,$C0,$09,$BA,$80,$00
	dc.b $48,$00,$1C,$AA,$80,$00,$40,$00,$30,$72,$80
	dcb.b $19,$00
	dc.b $81,$40,$2A,$76,$80,$00,$00,$00,$2A,$C2,$40,$00,$F0,$87,$44,$96
	dc.b $80,$FF,$F0,$86,$44,$96,$80,$FF,$F0,$81,$44,$96,$80,$FF,$F0,$80
	dc.b $44,$96,$80,$FF,$F0,$8F,$44,$96,$80,$FF,$F0,$8E,$44,$96,$80,$FF
	dc.b $F0,$8D,$44,$96,$80,$FF,$F0,$8C,$44,$96,$80,$FF,$F0,$8B,$44,$96
	dc.b $80,$FF,$F0,$8A,$44,$96,$80,$FF,$F0,$83,$44,$96,$80,$FF,$F0,$82
	dc.b $44,$96,$80,$FF,$F0,$85,$44,$96,$80,$FF,$F0,$84,$44,$96,$80,$FF
	dc.b $F0,$89,$44,$96,$80,$FF,$F0,$88,$44,$96,$80,$FF
	dcb.b $38,$00
	dc.b $2A,$E2,$40
	dcb.b $1A,$00
	dc.b $07,$49,$60,$80,$FF,$00,$06,$49,$60,$80,$FF,$00,$00,$00,$00,$00
	dc.b $00,$00,$01,$49,$60,$80,$FF,$00,$00,$49,$60,$80,$FF,$00,$0F,$49
	dc.b $60,$80,$FF,$00,$0E,$49,$60,$80,$FF,$00,$0D,$49,$60,$80,$FF,$00
	dc.b $0C,$49,$60,$80,$FF,$00,$0B,$49,$60,$80,$FF,$00,$0A,$49,$60,$80
	dc.b $FF,$00,$03,$49,$60,$80,$FF,$00,$02,$49,$60,$80,$FF,$00,$05,$49
	dc.b $60,$80,$FF,$00,$04,$49,$60,$80,$FF,$00,$09,$49,$60,$80,$FF,$00
	dc.b $08,$49,$60,$80,$FF
	dcb.b $1A,$00
	dc.b $55,$D6
	dcb.b $A,$00
	dc.b $2C,$98,$00,$00,$E1,$10,$2E,$98,$80,$00,$E0,$10,$2E,$98,$80
	dcb.b $D,$00
	dc.b $81,$00,$00,$08,$80,$00,$00,$00,$00,$00,$00,$00,$4E,$72,$2F,$4E
	dc.b $80,$00,$90,$C0,$02,$1E,$80,$00,$04,$00,$02,$A0,$80,$00,$51,$00
	dc.b $15,$04,$80,$00,$00,$00,$00,$00,$00,$00,$91,$00,$00,$02,$80,$00
	dc.b $48,$40,$2F,$78,$80,$00,$08,$00,$4B,$64,$80,$00,$00,$00,$4B,$64
	dc.b $80
	dcb.b $9,$00
	dc.b $2D,$60,$00,$00,$5A,$F8,$30,$14,$80,$00,$4E,$40,$2F,$92,$80,$00
	dc.b $4E,$58,$30,$E0,$80,$00,$81,$80,$2A,$76,$80,$00,$00,$00,$31,$04
	dc.b $40,$00,$00,$00,$31,$5E,$40,$00,$EA,$C0,$05,$1A,$80,$00,$EC,$C0
	dc.b $05,$1A,$80,$00,$00,$00,$00,$00,$00,$00,$ED,$C0,$04,$D0,$80,$00
	dc.b $EF,$C0,$04,$92,$80,$00,$EE,$C0,$05,$1A,$80,$00,$E8,$C0,$05,$1A
	dc.b $80,$00,$06,$C0,$06,$B2,$80,$00,$00,$00,$08,$06,$80,$00,$F4,$18
	dc.b $4B,$C2,$80,$00,$F4,$08,$4B,$EE,$80,$00,$F4,$10,$4B,$EE,$80
	dcb.b $F,$00
	dc.b $2D,$90,$80,$00,$4C,$40,$09,$6A,$80,$00,$4C,$40,$09,$66,$80
	dcb.b $9,$00
	dc.b $4F,$54
	dcb.b $9,$00
	dc.b $1C,$40,$80,$80,$01,$00,$0C,$40,$80,$80,$01,$00,$0A,$40,$80,$80
	dc.b $01,$F0,$97,$3C,$48,$80,$01,$F0,$9C,$3C,$48,$80,$01,$F0,$99,$3C
	dc.b $48,$80,$01,$F0,$9D,$3C,$48,$80,$01,$F0,$9A,$3C,$48,$80,$01,$F0
	dc.b $9B,$3C,$48,$80,$01,$F0,$83,$3C,$48,$80,$01,$F0,$86,$3C,$48,$80
	dc.b $01,$F0,$82,$3C,$48,$80,$01,$F0,$85,$3C,$48,$80,$01,$F0,$84,$3C
	dc.b $48,$80,$01,$F0,$91,$3C,$48,$80,$01,$F0,$9E,$3C,$48,$80,$01,$F0
	dc.b $89,$3C,$48,$80,$01,$F0,$8B,$3C,$48,$80,$01,$F0,$8A,$3C,$48,$80
	dc.b $01,$F0,$8D,$3C,$48,$80,$01,$F0,$8C,$3C,$48,$80,$01,$00,$19,$40
	dc.b $80,$80,$01,$00,$5C,$40,$6C,$80,$01,$00,$66,$40,$6C,$80,$01,$00
	dc.b $01,$3C,$50,$80,$01,$00,$13,$3C,$50,$80,$01,$00,$16,$3C,$50,$80
	dc.b $01,$00,$12,$3C,$50,$80,$01,$00,$15,$3C,$50,$80,$01,$00,$14,$3C
	dc.b $50,$80,$01,$00,$0E,$3C,$50,$80,$01
	dcb.b $19,$00
	dc.b $07,$3C,$50,$80,$01,$00,$00,$00,$00,$00,$00,$00,$10,$3C,$50,$80
	dc.b $01,$00,$00,$00,$00,$00,$00,$00,$1F,$3C,$50,$80,$01
	dcb.b $13,$00
	dc.b $08,$3C,$50,$80,$01,$00,$64,$40,$6C,$80,$01,$00,$00,$00,$00,$00
	dc.b $00,$00,$67,$40,$6C,$80,$01,$00,$5E,$40,$6C,$80,$01,$00,$00,$00
	dc.b $00,$00,$00,$00,$6C,$40,$6C,$80,$01,$00,$10,$40,$80,$80,$01
	dcb.b $19,$00
	dc.b $16,$40,$80,$80,$01,$00,$14,$40,$80,$80,$01,$00,$00,$3C,$64,$80
	dc.b $01
	dcb.b $D,$00
	dc.b $58,$40,$6C,$80,$01,$00,$62,$40,$6C,$80,$01,$F1,$00,$41,$02,$80
	dc.b $01,$00,$00,$00,$00,$00,$00,$00,$60,$40,$6C,$80,$01,$00,$00,$00
	dc.b $00,$00,$00,$00,$17,$41,$22,$80,$01
	dcb.b $D,$00
	dc.b $02,$40,$80,$80,$01,$00,$00,$00,$00,$00,$00,$00,$63,$40,$6C,$80
	dc.b $01,$00,$5A,$40,$6C,$80,$01,$00,$1C,$41,$22,$80,$01,$00,$19,$41
	dc.b $22,$80,$01,$00,$1D,$41,$22,$80,$01,$00,$1A,$41,$22,$80,$01,$00
	dc.b $1B,$41,$22,$80,$01,$00,$03,$41,$22,$80,$01,$00,$06,$41,$22,$80
	dc.b $01,$00,$02,$41,$22,$80,$01,$00,$05,$41,$22,$80,$01,$00,$04,$41
	dc.b $22,$80,$01,$00,$04,$40,$80,$80,$01,$00,$11,$41,$22,$80,$01,$00
	dc.b $1E,$41,$22,$80,$01,$00,$00,$00,$00,$00,$00,$00,$68,$40,$6C,$80
	dc.b $01,$00,$09,$41,$22,$80,$01,$00,$0B,$41,$22,$80,$01,$00,$0A,$41
	dc.b $22,$80,$01,$00,$0D,$41,$22,$80,$01,$00,$0C,$41,$22,$80,$01,$00
	dc.b $09,$40,$80,$80,$01
	dcb.b $3E,$00
	dc.b $4F,$DC,$00,$00,$00,$00,$55,$70
	dcb.b $E,$00
	dc.b $20,$40,$1A,$64,$80,$00,$4E,$7A,$17,$84,$80,$00,$48,$80,$19,$28
	dc.b $80,$00,$01,$08,$1A,$EE,$80,$00,$70,$00,$1B,$BA,$80,$00,$0E,$00
	dc.b $1C,$36,$80
	dcb.b $1A,$00
	dc.b $07,$44,$D2,$80,$FF,$00,$06,$44,$D2,$80,$FF,$00,$01,$44,$D2,$80
	dc.b $FF,$00,$00,$44,$D2,$80,$FF,$00,$0F,$44,$D2,$80,$FF,$00,$0E,$44
	dc.b $D2,$80,$FF,$00,$0D,$44,$D2,$80,$FF,$00,$0C,$44,$D2,$80,$FF,$00
	dc.b $0B,$44,$D2,$80,$FF,$00,$0A,$44,$D2,$80,$FF,$00,$03,$44,$D2,$80
	dc.b $FF,$00,$02,$44,$D2,$80,$FF,$00,$05,$44,$D2,$80,$FF,$00,$04,$44
	dc.b $D2,$80,$FF,$00,$09,$44,$D2,$80,$FF,$00,$08,$44,$D2,$80,$FF
	dcb.b $D,$00
	dc.b $40,$49,$9A,$80,$FF,$00,$00,$49,$9A,$80,$FF,$F0,$00,$47,$D0,$80
	dc.b $FF,$00,$00,$00,$00,$00,$00,$F1,$00,$49,$3C,$80,$FF
	dcb.b $14,$00
	dc.b $2B,$06,$40,$00,$4E,$70,$58,$E4,$80
	dcb.b $9,$00
	dc.b $2C,$DE,$40
	dcb.b $D,$00
	dc.b $0C,$00,$4B,$64,$80,$00,$04,$00,$4B,$64,$80,$00,$08,$00,$2F,$C0
	dc.b $80,$00,$00,$00,$2F,$C0,$80,$00,$4E,$76,$58,$F0,$80,$00,$EB,$C0
	dc.b $04,$D0,$80,$00,$E9,$C0,$04,$D0,$80,$00,$00,$00,$00,$00,$00,$00
	dc.b $F4,$38,$4B,$C2,$80,$00,$F4,$28,$4B,$EE,$80,$00,$F4,$30,$4B,$EE
	dc.b $80,$00,$00,$00,$4F,$78,$40,$00,$00,$00,$0E,$76,$00,$00,$00,$0D
	dc.b $40,$80,$80,$01,$F0,$98,$3C,$48,$80,$01,$00,$17,$3C,$50,$80,$01
	dc.b $00,$1C,$3C,$50,$80,$01,$00,$19,$3C,$50,$80,$01,$00,$1D,$3C,$50
	dc.b $80,$01,$00,$1A,$3C,$50,$80,$01,$00,$1B,$3C,$50,$80,$01,$00,$03
	dc.b $3C,$50,$80,$01,$00,$06,$3C,$50,$80,$01,$00,$02,$3C,$50,$80,$01
	dc.b $00,$05,$3C,$50,$80,$01,$00,$04,$3C,$50,$80,$01,$00,$11,$3C,$50
	dc.b $80,$01,$00,$1E,$3C,$50,$80,$01,$00,$09,$3C,$50,$80,$01,$00,$0B
	dc.b $3C,$50,$80,$01,$00,$0A,$3C,$50,$80,$01,$00,$0D,$3C,$50,$80,$01
	dc.b $00,$0C,$3C,$50,$80,$01,$00,$44,$40,$80,$80,$01,$00,$45,$40,$6C
	dc.b $80,$01
	dcb.b $13,$00
	dc.b $03,$40,$80,$80,$01,$00,$15,$40,$80,$80,$01
	dcb.b $C,$00
	dc.b $C0,$00,$3E,$42,$80,$01,$00,$00,$0F,$A4,$40
	dcb.b $8,$00
	dc.b $26,$40,$80,$80,$01
	dcb.b $13,$00
	dc.b $40,$40,$80,$80,$01,$00,$18,$41,$22,$80,$01,$00,$41,$40,$6C,$80
	dc.b $01
	dcb.b $E,$00
	dc.b $41,$B2,$80,$01
	dcb.b $1F,$00
	dc.b $0F,$41,$B2,$80,$01
	dcb.b $14,$00
	dc.b $10,$1C,$80,$00,$00,$00,$10,$CA,$40
	dcb.b $D,$00
	dc.b $01,$C0,$4B,$2C,$80
	dcb.b $9,$00
	dc.b $15,$52,$80,$00,$F6,$00,$4C,$20,$80,$00,$00,$00,$EC,$9C,$40,$00
	dc.b $00,$00,$2A,$DA,$40,$00,$00,$00,$1C,$B6,$00,$00,$00,$00,$2A,$44
	dc.b $40,$00,$F0,$00,$45,$E0,$80,$FF,$22,$00,$47,$76,$80,$FF,$20,$00
	dc.b $47,$76,$80,$FF
	dcb.b $C,$00
	dc.b $82,$00,$49,$9A,$80,$FF,$80,$00,$49,$9A,$80,$FF
	dcb.b $30,$00
	dc.b $F0,$00,$4A,$A4,$80,$FF
	dcb.b $E,$00
	dc.b $30,$DA,$40,$00,$00,$00,$0B,$A6,$40,$00,$00,$18,$3C,$50,$80,$01
	dc.b $00,$08,$40,$80,$80,$01,$00,$1E,$40,$80,$80,$01,$00,$1F,$40,$80
	dc.b $80,$01,$00,$05,$40,$80,$80,$01,$F0,$00,$3F,$F6,$80,$01,$00,$00
	dc.b $00,$00,$00,$00,$00,$24,$40,$80,$80,$01,$00,$27,$40,$80,$80,$01
	dc.b $F0,$00,$41,$36,$80,$01,$00,$12,$40,$80,$80,$01,$00,$01,$41,$B2
	dc.b $80,$01,$00,$13,$41,$B2,$80,$01,$00,$16,$41,$B2,$80,$01,$00,$12
	dc.b $41,$B2,$80,$01,$00,$15,$41,$B2,$80,$01,$00,$14,$41,$B2,$80,$01
	dc.b $00,$0E,$41,$B2,$80,$01
	dcb.b $19,$00
	dc.b $07,$41,$B2,$80,$01,$00,$00,$00,$00,$00,$00,$00,$10,$41,$B2,$80
	dc.b $01,$00,$00,$00,$00,$00,$00,$00,$1F,$41,$B2,$80,$01
	dcb.b $13,$00
	dc.b $08,$41,$B2,$80,$01,$00,$11,$40,$80,$80,$01,$4A,$FC,$58,$F0,$80
	dc.b $00,$00,$00,$10,$D6,$40
	dcb.b $9,$00
	dc.b $13,$90,$40,$00,$F0,$00,$45,$32,$80,$FF,$F5,$00,$45,$7A,$80,$FF
	dc.b $F0,$00,$47,$4C,$80,$FF,$F0,$00,$47,$28,$80,$FF,$F0,$00,$47,$B0
	dc.b $80,$FF,$00,$00,$00,$00,$00,$00,$00,$07,$4A,$7E,$80,$FF,$00,$06
	dc.b $4A,$7E,$80,$FF,$00,$01,$4A,$7E,$80,$FF,$00,$00,$4A,$7E,$80,$FF
	dc.b $00,$0F,$4A,$7E,$80,$FF,$00,$0E,$4A,$7E,$80,$FF,$00,$0D,$4A,$7E
	dc.b $80,$FF,$00,$0C,$4A,$7E,$80,$FF,$00,$0B,$4A,$7E,$80,$FF,$00,$0A
	dc.b $4A,$7E,$80,$FF,$00,$03,$4A,$7E,$80,$FF,$00,$02,$4A,$7E,$80,$FF
	dc.b $00,$05,$4A,$7E,$80,$FF,$00,$04,$4A,$7E,$80,$FF,$00,$09,$4A,$7E
	dc.b $80,$FF,$00,$08,$4A,$7E,$80,$FF,$00,$00,$2C,$D6,$40,$00,$00,$00
	dc.b $2E,$04,$00,$00,$F1,$40,$40,$E2,$80,$01,$00,$17,$41,$B2,$80,$01
	dc.b $00,$1C,$41,$B2,$80,$01,$00,$19,$41,$B2,$80,$01,$00,$1D,$41,$B2
	dc.b $80,$01,$00,$1A,$41,$B2,$80,$01,$00,$1B,$41,$B2,$80,$01,$00,$03
	dc.b $41,$B2,$80,$01,$00,$06,$41,$B2,$80,$01,$00,$02,$41,$B2,$80,$01
	dc.b $00,$05,$41,$B2,$80,$01,$00,$04,$41,$B2,$80,$01,$00,$11,$41,$B2
	dc.b $80,$01,$00,$1E,$41,$B2,$80,$01,$00,$09,$41,$B2,$80,$01,$00,$0B
	dc.b $41,$B2,$80,$01,$00,$0A,$41,$B2,$80,$01,$00,$0D,$41,$B2,$80,$01
	dc.b $00,$0C,$41,$B2,$80,$01,$00,$00,$12,$3E,$40,$00,$F5,$10,$45,$BE
	dc.b $80,$FF,$F1,$40,$49,$18,$80,$FF,$00,$18,$41,$B2,$80,$01
loc_0_0000F82E:
	rts
loc_0_0000F830:
	rts
	dc.b $4A,$2E,$01,$03,$67,$28,$22,$6E,$01,$AA,$4A,$2E,$02,$38,$66,$12
	dc.b $22,$2E,$02,$3C,$92,$A9,$00,$1A,$D3,$A9,$00,$12,$23,$42,$00,$1A
	dc.b $60,$0C,$08,$E9,$00,$00,$00,$10,$66,$04,$23,$42,$00,$16,$70,$00
	dc.b $4E,$75,$70,$FF,$4E,$75
loc_0_0000F868:
	movea.l $01AA(a6),a0
	btst.b #1,$0010(a0)
	bne.w loc_0_0000F884
	add.l d1,app_024C(a6)
	bset.b #0,$0010(a0)
	beq.b loc_0_0000F88A
	rts
loc_0_0000F884:
	jmp loc_0_0000845A.l
loc_0_0000F88A:
	moveq.l #8,d0
	jmp loc_0_0000858C.l
loc_0_0000F892:
	move.b #$E,$0108(a6)
	tst.b app_0238(a6)
	bne.b loc_0_0000F8EA
	move.l a1,d2
	bsr.w loc_0_00009B24
	beq.b loc_0_0000F8E4
	movem.l a0-a1,-(a7)
	moveq.l #34,d1
	bsr.w loc_0_000090BA
	movem.l (a7)+,a1-a2
	move.l a0,(a1)
	clr.l (a0)
	clr.b $0010(a0)
	clr.l $0016(a0)
	move.l a2,$0004(a0)
	clr.l $0012(a0)
	clr.l $001A(a0)
	movea.l d2,a2
	cmpi.l #71455571,$0016(a2)
	bne.b loc_0_0000F8DE
	bset.b #1,$0010(a0)
loc_0_0000F8DE:
	clr.l $0008(a0)
	movea.l a0,a1
loc_0_0000F8E4:
	move.l a1,$01AA(a6)
	rts
loc_0_0000F8EA:
	bsr.w loc_0_00009B24
	bne.w loc_0_00009B64
	move.l $000C(a1),app_024C(a6)
	bne.b loc_0_0000F902
	lea.l app_05A8(a6),a0
	move.l a0,app_024C(a6)
loc_0_0000F902:
	move.l a1,$01AA(a6)
	tst.l $0196(a6)
	beq.b loc_0_0000F92A
	movem.l a1/a4,-(a7)
	movea.l $0196(a6),a4
	move.b (a4)+,d1
	jsr loc_0_000016CC.l
	movem.l (a7)+,a1/a4
	move.l d2,$001E(a1)
	bset.b #2,$0010(a1)
loc_0_0000F92A:
	rts
loc_0_0000F92C:
	bsr.w loc_0_00009B24
	bne.w loc_0_00009B64
	tst.b app_0238(a6)
	bne.b loc_0_0000F94E
	move.l app_023C(a6),d2
	sub.l $001A(a1),d2
	add.l d2,$0012(a1)
	move.l app_023C(a6),$001A(a1)
	rts
loc_0_0000F94E:
	move.l a5,$000C(a1)
	rts
loc_0_0000F954:
	lea.l $01A6(a6),a3
loc_0_0000F958:
	tst.l (a3)
	beq.b loc_0_0000F980
	movea.l (a3),a3
	move.l $0012(a3),d1
	beq.b loc_0_0000F97E
	btst.b #1,$0010(a3)
	bne.b loc_0_0000F97E
	addq.l #8,d1
	bsr.w loc_0_000090BA
	move.l a0,$0008(a3)
	move.l a0,$000C(a3)
	adda.l $0012(a3),a0
loc_0_0000F97E:
	bra.b loc_0_0000F958
loc_0_0000F980:
	rts
loc_0_0000F982:
	movea.l $01AA(a6),a1
	btst.b #1,$0010(a1)
	eori #4,ccr
	rts
loc_0_0000F992:
	bsr.w loc_0_000097A6
	bra.w loc_0_0000F9DA
	dc.b $4E,$75,$4E,$75
loc_0_0000F99E:
	move.l d2,(a5)+
	rts
loc_0_0000F9A2:
	move.w d2,(a5)+
	rts
loc_0_0000F9A6:
	move.b d2,(a5)+
	rts
loc_0_0000F9AA:
	lea.l loc_0_0000F9B6(pc),a0
	rts
loc_0_0000F9B0:
	lea.l loc_0_0000F9BF(pc),a0
	rts
loc_0_0000F9B6:
	dc.b $53,$2D,$72,$65,$63,$6F,$72,$64,$00
loc_0_0000F9BF:
	dc.b $2E,$6D,$78,$00
loc_0_0000F9C3:
	dc.b "HISOFT DEVPAC",$00
	dc.b $00,$12,$D8,$66,$FC,$53,$89,$4E,$75
loc_0_0000F9DA:
	bsr.w loc_0_0000A110
	lea.l $01AE(a6),a2
	tst.b (a2)
	bne.b loc_0_0000F9EA
	lea.l loc_0_0000F9C3(pc),a2
loc_0_0000F9EA:
	moveq.l #0,d6
	moveq.l #0,d5
	movea.l a2,a0
loc_0_0000F9F0:
	tst.b (a0)+
	bne.b loc_0_0000F9F0
	move.l a0,d2
	sub.l a2,d2
	subq.l #1,d2
	bsr.w loc_0_0000FA74
	lea.l $01A6(a6),a3
loc_0_0000FA02:
	movea.l (a3),a3
	move.l $0012(a3),d3
	beq.b loc_0_0000FA6C
	btst.b #1,$0010(a3)
	bne.b loc_0_0000FA6C
	move.l $0016(a3),d2
	btst.b #2,$0010(a3)
	beq.b loc_0_0000FA22
	move.l $001E(a3),d2
loc_0_0000FA22:
	add.l d3,d2
	moveq.l #3,d5
	cmp.l #$1000000,d2
	bcc.b loc_0_0000FA3A
	moveq.l #2,d5
	cmp.l #$10000,d2
	bcc.b loc_0_0000FA3A
	moveq.l #1,d5
loc_0_0000FA3A:
	movea.l $0008(a3),a2
	move.l $0016(a3),d6
	btst.b #2,$0010(a3)
	beq.b loc_0_0000FA4E
	move.l $001E(a3),d6
loc_0_0000FA4E:
	moveq.l #28,d2
	cmp.l d2,d3
	bge.b loc_0_0000FA56
	move.l d3,d2
loc_0_0000FA56:
	sub.l d2,d3
	bsr.b loc_0_0000FA74
	tst.l d3
	bne.b loc_0_0000FA4E
	moveq.l #10,d0
	sub.w d5,d0
	move.w d0,d5
	move.l $0016(a3),d6
	moveq.l #0,d2
	bsr.b loc_0_0000FA74
loc_0_0000FA6C:
	tst.l (a3)
	bne.b loc_0_0000FA02
	bra.w loc_0_0000A0F6
loc_0_0000FA74:
	cmp.w #$49,d4
	bcc.b loc_0_0000FA7E
	bsr.w loc_0_0000A0F6
loc_0_0000FA7E:
	moveq.l #48,d1
	add.b d5,d1
	movea.l a4,a0
	move.b #$53,(a4)+
	move.b d1,(a4)+
	addq.w #2,a4
	moveq.l #0,d7
	move.w d5,d1
	add.w d1,d1
	lea.l loc_0_0000FAF2(pc,d1.w),a1
	move.b (a1)+,d1
	move.l d6,d0
	lsl.l d1,d0
	move.l d0,-(a7)
	move.b (a1)+,d0
	movea.l a7,a1
loc_0_0000FAA2:
	move.b (a1)+,d1
	bsr.b loc_0_0000FADE
	subq.b #1,d0
	bne.b loc_0_0000FAA2
	addq.l #4,a7
	add.l d2,d6
	tst.l d2
	bra.b loc_0_0000FAB8
loc_0_0000FAB2:
	move.b (a2)+,d1
	bsr.b loc_0_0000FADE
	subq.l #1,d2
loc_0_0000FAB8:
	bne.b loc_0_0000FAB2
	move.l a4,-(a7)
	move.l a4,d1
	sub.l a0,d1
	addq.l #2,d1
	sub.l d1,d4
	lsr.w #1,d1
	subq.w #2,d1
	lea.l $0002(a0),a4
	bsr.b loc_0_0000FADE
	movea.l (a7)+,a4
	not.b d7
	move.b d7,d1
	bsr.b loc_0_0000FADE
	move.b #$A,(a4)+
	subq.l #1,d4
	rts
loc_0_0000FADE:
	add.b d1,d7
	move.w d1,-(a7)
	lsr.w #4,d1
	bsr.b loc_0_0000FAE8
	move.w (a7)+,d1
loc_0_0000FAE8:
	andi.w #15,d1
	move.b loc_0_0000FB06(pc,d1.w),(a4)+
	rts
loc_0_0000FAF2:
	dc.b $00,$02,$10,$02,$08,$03,$00,$04,$00,$01,$00,$01,$00,$01,$00,$04
	dc.b $08,$03,$10,$02
loc_0_0000FB06:
	dc.b $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46	; lookup_table
loc_0_0000FB16:
	bsr.w loc_0_000097A6
	movea.l $016A(a6),a1
	movea.l (a1),a1
	move.l #$84034,d2
	lea.l loc_0_0000FC7C(pc),a2
	bsr.w loc_0_0000FC5E
	move.l d1,-(a7)
	lea.l loc_0_0000FC7C(pc),a2
	movea.l $0172(a6),a1
	movea.l (a1),a1
	move.l #$3900,d2
	bsr.w loc_0_0000FC5E
	add.l (a7)+,d1
	addi.l #10,d1
	jsr loc_0_000090BA.l
	movea.l a0,a2
	move.w #$0,(a2)
	lea.l $000A(a0),a0
	move.l #$A,$0002(a2)
	lea.l $0002(a2),a3
	movea.l $016A(a6),a1
	movea.l (a1),a1
	move.l #$84034,d2
	bsr.w loc_0_0000FBA0
	clr.l (a3)
	lea.l $0006(a2),a3
	movea.l $0172(a6),a1
	movea.l (a1),a1
	move.l #$3900,d2
	bsr.w loc_0_0000FBA0
	move.l a0,d1
	sub.l a2,d1
	movea.l a2,a0
	jsr loc_0_00008422.l
	bra.w loc_0_000098AE
loc_0_0000FB9E:
	rts
loc_0_0000FBA0:
	move.l a1,d1
	beq.b loc_0_0000FB9E
	move.b $000D(a1),d0
	move.l a1,-(a7)
	btst d0,d2
	beq.b loc_0_0000FBF6
	move.l a0,d1
	sub.l a2,d1
	move.l d1,(a3)
	move.l a0,d1
	moveq.l #0,d0
	move.b $0016(a1),d0
	addq.l #8,a1
	movea.l a0,a3
	clr.l (a0)+
	clr.l (a0)+
	addi.l #14,d0
	bset #0,d0
loc_0_0000FBCE:
	move.b (a1)+,(a0)+
	dbf.w d0,loc_0_0000FBCE
	movea.l d1,a1
	move.b $000D(a1),d0
	cmp.b #$8,d0
	beq.b loc_0_0000FC04
	cmp.b #$B,d0
	bcs.b loc_0_0000FBF6
	cmp.b #$E,d0
	bcc.b loc_0_0000FBF6
	move.b #$D,$000D(a1)
	clr.l $0098(a1)
loc_0_0000FBF6:
	movea.l (a7),a1
	movea.l (a1),a1
	bsr.b loc_0_0000FBA0
	movea.l (a7)+,a1
	movea.l $0004(a1),a1
	bra.b loc_0_0000FBA0
loc_0_0000FC04:
	move.l a0,d0
	sub.l a2,d0
	movea.l $0008(a1),a0
	move.l d0,$0008(a1)
	add.l a2,d0
	movea.l a0,a1
	movea.l d0,a0
	pea.l $0004(a0)
	move.l a0,d0
	addi.l #16,d0
	sub.l a2,d0
	move.l d0,(a0)
	clr.l $0008(a0)
	lea.l $0010(a0),a0
loc_0_0000FC2E:
	move.l $0004(a1),d0
	sub.l (a1),d0
	move.l $0008(a1),-(a7)
	movea.l (a1),a1
	subq.w #1,d0
	bmi.b loc_0_0000FC44
loc_0_0000FC3E:
	move.b (a1)+,(a0)+
	dbf.w d0,loc_0_0000FC3E
loc_0_0000FC44:
	move.l (a7)+,d0
	beq.b loc_0_0000FC4C
	movea.l d0,a1
	bra.b loc_0_0000FC2E
loc_0_0000FC4C:
	move.l a0,d0
	sub.l a2,d0
	movea.l (a7)+,a1
	move.l d0,(a1)
	btst #0,d0
	beq.b loc_0_0000FC5C
	addq.w #1,a0
loc_0_0000FC5C:
	bra.b loc_0_0000FBF6
loc_0_0000FC5E:
	moveq.l #0,d1
	move.l a1,d0
	beq.b loc_0_0000FC7A
	move.l a1,-(a7)
	movea.l (a1),a1
	bsr.b loc_0_0000FC5E
	movea.l (a7),a1
	move.l d1,-(a7)
	movea.l $0004(a1),a1
	bsr.b loc_0_0000FC5E
	add.l (a7)+,d1
	movea.l (a7)+,a1
	jsr (a2)
loc_0_0000FC7A:
	rts
loc_0_0000FC7C:
	move.b $000D(a1),d0
	btst d0,d2
	beq.b loc_0_0000FCD4
	cmp.b #$8,d0
	beq.b loc_0_0000FC9E
	cmp.b #$B,d0
	bcs.b loc_0_0000FCC2
	cmp.b #$E,d0
	bcc.b loc_0_0000FCC2
	addi.l #178,d1
	rts
loc_0_0000FC9E:
	move.l a1,-(a7)
	addi.l #16,d1
	movea.l $0008(a1),a1
loc_0_0000FCAA:
	add.l $0004(a1),d1
	sub.l (a1),d1
	move.l $0008(a1),d0
	beq.b loc_0_0000FCBA
	movea.l d0,a1
	bra.b loc_0_0000FCAA
loc_0_0000FCBA:
	addq.l #1,d1
	bclr #0,d1
	movea.l (a7)+,a1
loc_0_0000FCC2:
	moveq.l #0,d0
	move.b $0016(a1),d0
	addi.l #24,d0
	bclr #0,d0
	add.l d0,d1
loc_0_0000FCD4:
	rts
loc_0_0000FCD6:
	move.l d4,d3
	bra.b loc_0_0000FD10
loc_0_0000FCDA:
	movea.l app_timer_device_iorequest+IO_DATA(a6),a0
loc_0_0000FCDE:
	tst.b (a0)
	beq.b loc_0_0000FD02
	lea.l app_10E8(a6),a1
loc_0_0000FCE6:
	move.b (a0)+,(a1)+
	bne.b loc_0_0000FCE6
	move.l a0,-(a7)
	lea.l app_10E8(a6),a0
	lea.l loc_0_00009656(pc),a2
	jsr loc_0_000045DC.l
	bsr.w loc_0_0000FD04
	movea.l (a7)+,a0
	bra.b loc_0_0000FCDE
loc_0_0000FD02:
	rts
loc_0_0000FD04:
	jsr loc_0_0000AFDE.l
	bne.w loc_0_0000FD8C
	move.l d2,d1
loc_0_0000FD10:
	move.l d1,-(a7)
	jsr loc_0_000090BA.l
	move.l (a7),d1
	move.l a0,(a7)
	move.l d3,-(a7)
	bsr.w loc_0_0000AFF6
	move.l (a7)+,d3
	bsr.w loc_0_0000AFF2
	movea.l (a7)+,a2
	move.l a2,d2
	move.w (a2),d0
	cmp.w #$0,d0
	bne.b loc_0_0000FD94
	movem.l a3-a5,-(a7)
	movea.l $0002(a2),a0
	movea.l $016A(a6),a2
	bsr.b loc_0_0000FD5C
	movea.l d2,a0
	movea.l $0006(a0),a0
	movea.l $0172(a6),a2
	bsr.b loc_0_0000FD5C
	movem.l (a7)+,a3-a5
loc_0_0000FD52:
	rts
loc_0_0000FD54:
	move.l (a0),d0
	beq.b loc_0_0000FD52
	clr.l (a0)
	movea.l d0,a0
loc_0_0000FD5C:
	adda.l d2,a0
	move.l d2,-(a7)
	jsr loc_0_00000B78.l
	movem.l (a7)+,d2
	beq.b loc_0_0000FD54
	move.l a0,(a1)
	move.b $000D(a0),d1
	cmp.b #$8,d1
	bne.b loc_0_0000FD54
	add.l d2,$0008(a0)
	movea.l $0008(a0),a1
	add.l d2,$0004(a1)
	add.l d2,(a1)
	bra.b loc_0_0000FD54
	dc.b $70,$05,$60,$02
loc_0_0000FD8C:
	moveq.l #27,d0
loc_0_0000FD8E:
	jmp loc_0_0000846E.l
loc_0_0000FD94:
	moveq.l #103,d0
	bra.b loc_0_0000FD8E
