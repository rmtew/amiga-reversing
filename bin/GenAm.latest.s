INCLUDE "devices/timer.i"
INCLUDE "devices/timer_lib.i"
INCLUDE "dos/dos.i"
INCLUDE "dos/dos_lib.i"
INCLUDE "dos/dosextens.i"
INCLUDE "exec/exec_lib.i"
INCLUDE "exec/io.i"
INCLUDE "exec/libraries.i"
INCLUDE "exec/memory.i"

RSSET 0
RS.B 328
app_ULONG RS.L 1
RS.B 58
app_file_0186 RS.L 1
RS.B 24
app_slot_01A2 RS.L 1
RS.B 1968
app_file_0956 RS.L 1
RS.B 892
app_DOSBase RS.L 1
app_file_0CDA RS.L 1
RS.B 4
app_fileinfoblock RS.L 1
RS.B 962
app_dest_10A8 RS.L 1
RS.B 4
app_dest_10B0 RS.L 1
RS.B 4
app_timer_device_iorequest RS.L 1
RS.B 44
app_SIZEOF EQU __RS


    SECTION section,code
h0_0000:
    bra.s h0_ExecAllocMem_0036
    DC.B    $94,$4f
    DC.L    $7a3085c2
    DC.B    "$VER: GenAm 3.18 (2.8.94)",0
    DC.B    "(C) HiSoft 1985-1997"
h0_ExecAllocMem_0036:
    jsr h0_ExecAllocMem_A910.l
h0_003C:
    jsr h0_9106.l
h0_0042:
    move.l a7,$0234(a6)
    subq.l #4,$0234(a6)
    movea.l #dat_A664,a0
    lea.l -$0002(a6),a1
    moveq.l #63,d0
h0_0056:
    move.l (a0)+,(a1)+
    dbf.w d0,h0_0056
h0_005C:
    lea.l $00FE(a6),a0
    move.w #$94,d0
h0_0064:
    clr.w (a0)+
    dbf.w d0,h0_0064
h0_006A:
    sf.b $023A(a6)
    sf.b $0238(a6)
    clr.b $04F9(a6)
    jsr h0_90A8.l
h0_007C:
    lea.l $0248(a6),a1
    clr.l (a1)
    move.l a1,$0172(a6)
    lea.l $0244(a6),a1
    clr.l (a1)
    move.l a1,$016A(a6)
    bsr.w h0_6E42
h0_0094:
    clr.b $06C8(a6)
    lea.l app_timer_device_iorequest+IO_DATA(a6),a3
    bsr.w h0_4668
h0_00A0:
    lea.l $0832(a6),a3
    bsr.w h0_4668
h0_00A8:
    clr.b $07E0(a6)
    lea.l $08A0(a6),a0
    move.l a0,$0940(a6)
    clr.w $0254(a6)
    move.b #$64,$023A(a6)
    jsr h0_A9BC.l
h0_00C4:
    bne.w h0_046E
h0_00C8:
    clr.b $078E(a6)
    st.b $0840(a6)
    sf.b $0841(a6)
    sf.b $0842(a6)
    st.b $0843(a6)
    jsr h0_AB0E.l
h0_00E2:
    sf.b $0102(a6)
    jsr h0_AB00.l
h0_00EC:
    sf.b $0102(a6)
    lea.l $07E0(a6),a0
    tst.b (a0)
    beq.s h0_0110
h0_00F8:
    jsr h0_B0AC.l
h0_00FE:
    beq.w h0_0174
h0_0102:
    move.l a0,$0230(a6)
    jsr h0_AB08.l
h0_010C:
    bne.w h0_0170
h0_0110:
    jsr h0_AB2A.l
h0_0116:
    tst.b $04F9(a6)
    beq.w h0_0178
h0_011E:
    tst.b $0127(a6)
    bne.s h0_012C
h0_0124:
    moveq.l #0,d0
    jsr h0_8E7A.l
h0_012C:
    jsr h0_4590.l
h0_0132:
    bne.w h0_016C
h0_0136:
    jsr h0_FCDA.l
h0_013C:
    sf.b $023A(a6)
    lea.l $08A0(a6),a0
    move.l a0,$0940(a6)
    clr.b $010A(a6)
    lea.l $04F4(a6),a0
    jsr h0_8856.l
h0_0156:
    beq.s h0_01C8
h0_0158:
    moveq.l #10,d0
    jsr h0_8E7A.l
h0_0160:
    bsr.s h0_0184
h0_0162:
    move.b #$64,$023A(a6)
    bra.w h0_046E
h0_016C:
    moveq.l #26,d0
    bra.s h0_017A
h0_0170:
    moveq.l #24,d0
    bra.s h0_017A
h0_0174:
    moveq.l #25,d0
    bra.s h0_017A
h0_0178:
    moveq.l #23,d0
h0_017A:
    jsr h0_8E7A.l
h0_0180:
    bra.w h0_046E
h0_0184:
    lea.l $04F4(a6),a0
    moveq.l #0,d0
    move.b $0005(a0),d0
    subq.w #2,d0
    bmi.s h0_01A0
h0_0192:
    addq.w #6,a0
h0_0194:
    move.b (a0)+,d1
    jsr h0_8E98.l
h0_019C:
    dbf.w d0,h0_0194
h0_01A0:
    jmp h0_8E8C.l
h0_01A6:
    move.w $0218(a6),-(a7)
    clr.w $0218(a6)
    jsr h0_AB00.l
h0_01B4:
    bne.s h0_0178
h0_01B6:
    jsr h0_AB08.l
h0_01BC:
    bne.s h0_0170
h0_01BE:
    move.w (a7)+,$0218(a6)
    sf.b $0102(a6)
    rts
h0_01C8:
    tst.l $017E(a6)
    bne.s h0_01D2
h0_01CE:
    moveq.l #29,d0
    bra.s h0_017A
h0_01D2:
    movea.l $04F4(a6),a1
    move.b $04F9(a6),d0
    subq.b #1,d0
h0_01DC:
    move.l a1,d2
    move.b d0,d3
h0_01E0:
    subq.b #1,d0
    bcs.s h0_01FA
h0_01E4:
    move.b (a1)+,d1
    cmp.b #$5C,d1
    beq.s h0_01DC
h0_01EC:
    cmp.b #$2F,d1
    beq.s h0_01DC
h0_01F2:
    cmp.b #$3A,d1
    beq.s h0_01DC
h0_01F8:
    bra.s h0_01E0
h0_01FA:
    lea.l $057E(a6),a0
    movea.l d2,a1
    move.b d3,(a0)+
h0_0202:
    beq.s h0_020A
h0_0204:
    move.b (a1)+,(a0)+
    subq.b #1,d3
    bra.s h0_0202
h0_020A:
    move.b #$A,(a0)
    bsr.w h0_0496
h0_0212:
    sf.b $0840(a6)
    st.b $0841(a6)
    st.b $0842(a6)
    jsr h0_AB0E.l
h0_0224:
    sf.b $0102(a6)
    lea.l $05A8(a6),a0
    move.l a0,$024C(a6)
    tst.b $0127(a6)
    bne.s h0_024A
h0_0236:
    moveq.l #27,d0
    jsr h0_8E7A.l
h0_023E:
    bsr.w h0_0184
h0_0242:
    moveq.l #1,d0
    jsr h0_8E7A.l
h0_024A:
    move.b $0954(a6),$0955(a6)
    sf.b $0840(a6)
    st.b $0841(a6)
    st.b $0842(a6)
    sf.b $0843(a6)
    bsr.w h0_01A6
h0_0264:
    bsr.w h0_06AC
h0_0268:
    bne.s h0_02B0
h0_026A:
    move.l a7,$0234(a6)
    subq.l #4,$0234(a6)
    sf.b $0844(a6)
    bsr.w h0_09C8
h0_027A:
    bsr.w h0_07F8
h0_027E:
    tst.b $0844(a6)
    beq.s h0_0298
h0_0284:
    sf.b $0840(a6)
    st.b $0841(a6)
    sf.b $0842(a6)
    sf.b $0843(a6)
    bsr.w h0_01A6
h0_0298:
    move.l a7,$0234(a6)
    subq.l #4,$0234(a6)
h0_02A0:
    bsr.w h0_06AC
h0_02A4:
    bne.s h0_02B0
h0_02A6:
    bsr.w h0_09C8
h0_02AA:
    bsr.w h0_07F8
h0_02AE:
    bra.s h0_02A0
h0_02B0:
    tst.b $010C(a6)
    bne.w h0_03B0
h0_02B8:
    bsr.w h0_0590
h0_02BC:
    sf.b $0955(a6)
    tst.b $0127(a6)
    bne.s h0_02CE
h0_02C6:
    moveq.l #2,d0
    jsr h0_8E7A.l
h0_02CE:
    tst.b $0115(a6)
    bgt.w h0_06A4
h0_02D6:
    move.b $0954(a6),$0955(a6)
    jsr h0_AB50.l
h0_02E2:
    st.b $0238(a6)
    bsr.w h0_0496
h0_02EA:
    tst.b $0954(a6)
    beq.s h0_02F8
h0_02F0:
    sf.b $083A(a6)
    st.b $0100(a6)
h0_02F8:
    lea.l $0832(a6),a3
    bsr.w h0_4678
h0_0300:
    sf.b $0840(a6)
    st.b $0841(a6)
    sf.b $0842(a6)
    st.b $0843(a6)
    jsr h0_AB0E.l
h0_0316:
    sf.b $0841(a6)
    jsr h0_AB00.l
h0_0320:
    jsr h0_AB08.l
h0_0326:
    sf.b $0102(a6)
    jsr h0_AB2A.l
h0_0330:
    lea.l $04F4(a6),a0
    clr.b $010A(a6)
    jsr h0_8856.l
h0_033E:
    beq.s h0_0346
h0_0340:
    jmp h0_846E.l
h0_0346:
    st.b $0841(a6)
    sf.b $0843(a6)
    bsr.w h0_01A6
h0_0352:
    bsr.w h0_06AC
h0_0356:
    bne.s h0_0386
h0_0358:
    sf.b $0844(a6)
    bsr.w h0_09C8
h0_0360:
    bsr.w h0_08DC
h0_0364:
    tst.b $0844(a6)
    beq.s h0_0376
h0_036A:
    bsr.w h0_01A6
h0_036E:
    move.l a7,$0234(a6)
    subq.l #4,$0234(a6)
h0_0376:
    bsr.w h0_06AC
h0_037A:
    bne.s h0_0386
h0_037C:
    bsr.w h0_09C8
h0_0380:
    bsr.w h0_08DC
h0_0384:
    bra.s h0_0376
h0_0386:
    bsr.w h0_057A
h0_038A:
    bsr.w h0_79CC
h0_038E:
    bsr.w h0_79DA
h0_0392:
    jsr h0_9898.l
h0_0398:
    tst.b $00FF(a6)
    beq.s h0_03A4
h0_039E:
    jsr h0_8F60.l
h0_03A4:
    tst.b $0109(a6)
    beq.s h0_03B0
h0_03AA:
    jsr h0_FB16.l
h0_03B0:
    sf.b $0955(a6)
    jsr h0_9158.l
h0_03BA:
    jsr h0_98AE.l
h0_03C0:
    jsr h0_8A06.l
h0_03C6:
    tst.b $0127(a6)
    beq.s h0_03D4
h0_03CC:
    move.b $010C(a6),d1
    beq.w h0_046E
h0_03D4:
    jsr h0_8E8C.l
h0_03DA:
    moveq.l #0,d1
    move.b $010C(a6),d1
    jsr h0_8F04.l
h0_03E6:
    moveq.l #3,d0
    cmpi.b #1,$010C(a6)
    bne.s h0_03F2
h0_03F0:
    addq.b #1,d0
h0_03F2:
    jsr h0_8E7A.l
h0_03F8:
    move.l $0220(a6),d1
    subq.l #1,d1
    jsr h0_8F04.l
h0_0404:
    moveq.l #5,d0
    jsr h0_8E7A.l
h0_040C:
    move.l $0224(a6),d1
    jsr h0_8F04.l
h0_0416:
    moveq.l #12,d0
    jsr h0_8E7A.l
h0_041E:
    jsr h0_962C.l
h0_0424:
    moveq.l #22,d0
    tst.b $0112(a6)
    bne.s h0_0436
h0_042C:
    moveq.l #18,d0
    tst.b $0114(a6)
    beq.s h0_0436
h0_0434:
    moveq.l #17,d0
h0_0436:
    jsr h0_8E7A.l
h0_043C:
    moveq.l #19,d0
    jsr h0_8E7A.l
h0_0444:
    moveq.l #0,d1
    move.w app_file_0186+fh_Buf(a6),d1
    beq.s h0_046E
h0_044C:
    jsr h0_8F04.l
h0_0452:
    moveq.l #13,d0
    jsr h0_8E7A.l
h0_045A:
    moveq.l #0,d0
    move.w $0194(a6),d1
    jsr h0_8F04.l
h0_0466:
    moveq.l #14,d0
    jsr h0_8E7A.l
h0_046E:
    jsr h0_916A.l
h0_0474:
    jsr h0_ABC0.l
h0_047A:
    move.l app_file_0186+fh_Interactive(a6),d3
    beq.s h0_048A
h0_0480:
    jsr h0_AFF2.l
h0_0486:
    clr.l app_file_0186+fh_Interactive(a6)
h0_048A:
    jsr h0_90F2.l
h0_0490:
    jsr h0_DOSOutput_ACA4.l             ; KNOWN: DOSBase _LVOOutput fallback via local wrapper
h0_0496:
    moveq.l #0,d0
    move.w d0,$0218(a6)
    move.l d0,$0224(a6)
    move.l d0,$0220(a6)
    move.l d0,$023C(a6)
    move.l d0,$015A(a6)
    move.l d0,$0162(a6)
    move.l d0,app_file_0186+fh_Type(a6)
    move.w d0,$087E(a6)
    move.w d0,$0880(a6)
    move.l d0,$0882(a6)
    move.b d0,$0106(a6)
    move.b d0,$0112(a6)
    move.b d0,$083B(a6)
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
    move.b #$1,$085C(a6)
    move.b #$FF,$086C(a6)
    sf.b $0125(a6)
    move.b d0,$012F(a6)
    move.w d0,$010E(a6)
    move.w #$FFFF,$0110(a6)
    move.b d0,$0107(a6)
    move.l d0,$0890(a6)
    move.w d0,$0898(a6)
    move.w d0,$089A(a6)
    move.l d0,$084A(a6)
    moveq.l #1,d0
    move.l d0,$0846(a6)
    st.b $083A(a6)
    st.b $0105(a6)
    move.w #$80,$021E(a6)
    jsr h0_8D82.l
h0_0542:
    sf.b $0114(a6)
    sf.b $0115(a6)
    sf.b $0118(a6)
    sf.b $0117(a6)
    sf.b $0101(a6)
    sf.b $0119(a6)
    sf.b $011D(a6)
    st.b $011E(a6)
    st.b $011F(a6)
    sf.b $0126(a6)
    move.b #$2E,$0116(a6)
    move.b #$1,$0108(a6)
    bra.w h0_78E0
h0_057A:
    tst.w $087E(a6)
    bne.s h0_0582
h0_0580:
    rts
h0_0582:
    move.w #$FFFF,$0218(a6)
    moveq.l #50,d0
    jmp h0_8486.l
h0_0590:
    bsr.s h0_057A
h0_0592:
    bsr.w h0_79CC
h0_0596:
    bsr.w h0_79DA
h0_059A:
    jsr h0_8A06.l
h0_05A0:
    bsr.s h0_05C2
h0_05A2:
    jsr h0_8A5A.l
h0_05A8:
    cmpi.w #3,$021C(a6)
    bne.s h0_05B6
h0_05B0:
    jsr h0_A3F4.l
h0_05B6:
    jsr h0_9682.l
h0_05BC:
    clr.l $017A(a6)
    rts
h0_05C2:
    movea.l $0172(a6),a3
    movea.l (a3),a3
    bsr.s h0_05CC
h0_05CA:
    rts
h0_05CC:
    tst.l (a3)
    beq.s h0_05D8
h0_05D0:
    move.l a3,-(a7)
    movea.l (a3),a3
    bsr.s h0_05CC
h0_05D6:
    movea.l (a7)+,a3
h0_05D8:
    cmpi.b #9,$000D(a3)
    bne.s h0_05E6
h0_05E0:
    movea.l $0008(a3),a2
    bsr.s h0_05F8
h0_05E6:
    tst.l $0004(a3)
    beq.s h0_05F6
h0_05EC:
    move.l a3,-(a7)
    movea.l $0004(a3),a3
    bsr.s h0_05CC
h0_05F4:
    movea.l (a7)+,a3
h0_05F6:
    rts
h0_05F8:
    tst.l (a2)
    beq.s h0_0604
h0_05FC:
    move.l a2,-(a7)
    movea.l (a2),a2
    bsr.s h0_05F8
h0_0602:
    movea.l (a7)+,a2
h0_0604:
    clr.l $0008(a2)
    tst.l $0004(a2)
    beq.s h0_0618
h0_060E:
    move.l a2,-(a7)
    movea.l $0004(a2),a2
    bsr.s h0_05F8
h0_0616:
    movea.l (a7)+,a2
h0_0618:
    rts
h0_061A:
    tst.l $0890(a6)
    bne.s h0_063E
h0_0620:
    tst.b $0101(a6)
    bne.s h0_0662
h0_0626:
    movea.l $017E(a6),a1
    movea.l $009E(a1),a0
    cmpa.l $00A2(a1),a0
    bcc.s h0_067E
h0_0634:
    move.b (a0),d0
    cmp.b d0,d0
    rts
    DC.B    $70,$ff,$4e,$75 ; VIOLATION: orphaned code island at $063A is not reached from known entrypoints
h0_063E:
    tst.b $0101(a6)
    beq.s h0_064E
h0_0644:
    move.w $0898(a6),d0
    cmp.w $089A(a6),d0
    bhi.s h0_0662
h0_064E:
    movea.l $0890(a6),a1
    movea.l $0894(a6),a0
    cmpa.l $0004(a1),a0
    bne.s h0_0634
h0_065C:
    movea.l $0008(a1),a0
    bra.s h0_0634
h0_0662:
    movea.l $0882(a6),a2
    movea.l $0004(a2),a1
    movea.l $0010(a2),a0
    cmpa.l $0004(a1),a0
    bne.s h0_0634
h0_0674:
    movea.l $0008(a1),a1
    movea.l $0000(a1),a0
    bra.s h0_0634
h0_067E:
    moveq.l #70,d0
    jmp h0_846E.l
    DC.B    $4a,$fb
    DC.B    "include_longmac",0
h0_0698:
    tst.b $0115(a6)
    beq.w h0_06C6
h0_06A0:
    bpl.s h0_06A4
h0_06A2:
    rts
h0_06A4:
    moveq.l #79,d0
    jmp h0_846E.l
h0_06AC:
    tst.b $0115(a6)
    bne.s h0_06A0
h0_06B2:
    addq.l #1,$0220(a6)
    tst.b $0101(a6)
    bne.w h0_702A
h0_06BE:
    tst.l $0890(a6)
    bne.w h0_743C
h0_06C6:
    moveq.l #10,d1
    move.w #$FE,d2
    addq.w #1,$0218(a6)
h0_06D0:
    movea.l $017E(a6),a1
    movea.l $009E(a1),a4
    cmpa.l $00A2(a1),a4
    bcc.w h0_0754
h0_06E0:
    move.w #$FC,d0
    moveq.l #10,d2
    move.l a4,$0240(a6)
    movea.l a4,a2
h0_06EC:
    cmp.b (a2)+,d2
    dbeq.w d0,h0_06EC
h0_06F2:
    beq.s h0_070C
h0_06F4:
    cmpa.l $00A2(a1),a2
    bhi.s h0_071A
h0_06FA:
    move.b #$2A,-(a2)
    move.b #$A,-$0001(a2)
    move.l a2,$009E(a1)
    moveq.l #0,d0
    rts
h0_070C:
    cmpa.l $00A2(a1),a2
    bhi.s h0_071A
h0_0712:
    move.l a2,$009E(a1)
    moveq.l #0,d0
    rts
h0_071A:
    move.l $00A6(a1),d1
    movea.l $0008(a1),a2
    adda.l d1,a2
    cmpa.l $00A2(a1),a2
    bne.s h0_0776
h0_072A:
    move.l $00A2(a1),d2
    sub.l a4,d2
    beq.s h0_0754
h0_0732:
    move.l d2,-(a7)
    subq.l #1,d2
    movea.l a4,a0
    movea.l $0008(a1),a2
    move.l a2,$009E(a1)
h0_0740:
    move.b (a0)+,(a2)+
    dbf.w d2,h0_0740
h0_0746:
    move.l $00A6(a1),d1
    sub.l (a7)+,d1
    jsr h0_89B0.l
h0_0752:
    bra.s h0_076C
h0_0754:
    movea.l $0008(a1),a2
    move.l a2,$009E(a1)
    adda.l $00A6(a1),a2
    cmpa.l $00A2(a1),a2
    bne.s h0_0776
h0_0766:
    jsr h0_89BA.l
h0_076C:
    beq.w h0_06D0
h0_0770:
    jmp h0_846E.l
h0_0776:
    move.w $009C(a1),$0218(a6)
    clr.w $009C(a1)
    tst.b $0134(a6)
    beq.s h0_0792
h0_0786:
    tst.b $0238(a6)
    beq.s h0_0792
h0_078C:
    move.b #$FE,$000E(a1)
h0_0792:
    cmpi.b #12,$000D(a1)
    beq.s h0_07AE
h0_079A:
    move.l $0098(a1),d2
    beq.s h0_07AE
h0_07A0:
    move.l a1,-(a7)
    jsr h0_DOSClose_AFB8.l              ; KNOWN: DOSBase _LVOClose fallback via local wrapper
h0_07A8:
    movea.l (a7)+,a1
    clr.l $0098(a1)
h0_07AE:
    move.l $0010(a1),$017E(a6)
    bne.w h0_0698
h0_07B8:
    moveq.l #-1,d0
    rts
    DC.L    $50ee0113,$4a2e0238,$6714b23c,$002b6718,$b23c002d,$670c720a,$50ee0100 ; VIOLATION: orphaned code island at $07BC is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $72,$0a,$4e,$75 ; VIOLATION: orphaned code island at $07DA is not reached from known entrypoints
    DC.B    $53,$2e,$08,$3a,$60,$04 ; VIOLATION: orphaned code island at $07DE is not reached from known entrypoints
    DC.B    $52,$2e,$08,$3a,$5a,$ee,$01,$00,$12,$1c ; VIOLATION: orphaned code island at $07E4 is not reached from known entrypoints
h0_07EE:
    rts
h0_07F0:
    tst.b $0238(a6)
    bne.w h0_08DC
h0_07F8:
    tst.b $0129(a6)
    beq.w h0_08C6
h0_0800:
    tst.l $0182(a6)
    beq.w h0_08C6
h0_0808:
    cmpi.b #1,$0108(a6)
    bne.s h0_07EE
h0_0810:
    move.l $017E(a6),d0
    beq.s h0_07EE
h0_0816:
    move.b $0146(a6),d6
    movea.l d0,a0
    move.l $00AE(a0),d0
    beq.s h0_082A
h0_0822:
    movea.l d0,a0
    cmp.b $0004(a0),d6
    beq.s h0_087A
h0_082A:
    movea.l $017E(a6),a0
    lea.l $00AA(a0),a0
h0_0832:
    move.l (a0),d0
    beq.s h0_0842
h0_0836:
    movea.l d0,a0
    cmp.b $0004(a0),d6
    beq.s h0_0872
h0_083E:
    lea.l (a0),a0
    bra.s h0_0832
h0_0842:
    move.l a0,-(a7)
    moveq.l #32,d1
    jsr h0_ExecAllocMem_90BA.l          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_084C:
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
h0_0872:
    movea.l $017E(a6),a1
    move.l a0,$00AE(a1)
h0_087A:
    move.l $023C(a6),d0
    sub.l $0182(a6),d0
    cmp.l $0006(a0),d0
    beq.s h0_08C6
h0_0888:
    moveq.l #0,d1
    move.w $0218(a6),d1
    cmp.l $000A(a0),d1
    beq.s h0_08C6
h0_0894:
    tst.b $012A(a6)
    beq.s h0_08BA
h0_089A:
    addq.w #1,$0012(a0)
    lea.l $000A(a0),a1
    move.l d0,-(a7)
    move.l d1,d0
    jsr h0_8ADA.l
h0_08AC:
    move.l (a7)+,d0
    lea.l $0006(a0),a1
    jsr h0_8ADA.l
h0_08B8:
    bra.s h0_08C6
h0_08BA:
    addq.l #8,$0018(a0)
    move.l d0,$0006(a0)
    move.l d1,$000A(a0)
h0_08C6:
    tst.b $0102(a6)
    bne.w h0_09A4
h0_08CE:
    tst.b $021A(a6)
    beq.w h0_0996
h0_08D6:
    bra.w h0_09A4
h0_08DA:
    rts
h0_08DC:
    tst.b $0129(a6)
    beq.w h0_0972
h0_08E4:
    tst.l $0182(a6)
    beq.w h0_0972
h0_08EC:
    cmpi.b #1,$0108(a6)
    bne.s h0_0972
h0_08F4:
    move.l $017E(a6),d0
    beq.s h0_08DA
h0_08FA:
    movea.l d0,a0
    move.b $0146(a6),d6
    movea.l $00AE(a0),a0
    cmp.b $0004(a0),d6
    beq.s h0_091E
h0_090A:
    movea.l $017E(a6),a1
    lea.l $00AA(a1),a0
h0_0912:
    movea.l (a0),a0
    cmp.b $0004(a0),d6
    bne.s h0_0912
h0_091A:
    move.l a0,$00AE(a1)
h0_091E:
    move.l $023C(a6),d0
    sub.l $0182(a6),d0
    cmp.l $0006(a0),d0
    beq.s h0_0972
h0_092C:
    moveq.l #0,d1
    move.w $0218(a6),d1
    cmp.l $000A(a0),d1
    beq.s h0_0972
h0_0938:
    tst.b $012A(a6)
    beq.s h0_095E
h0_093E:
    lea.l $000A(a0),a1
    move.l d0,-(a7)
    move.l d1,d0
    jsr h0_8B10.l
h0_094C:
    move.l a1,$0014(a0)
    move.l (a7)+,d0
    lea.l $0006(a0),a1
    jsr h0_8B10.l
h0_095C:
    bra.s h0_096E
h0_095E:
    movea.l $0014(a0),a1
    move.l d0,$0006(a0)
    move.l d1,$000A(a0)
    move.l d1,(a1)+
    move.l d0,(a1)+
h0_096E:
    move.l a1,$0014(a0)
h0_0972:
    tst.b $0102(a6)
    bne.s h0_09A4
h0_0978:
    tst.b $0100(a6)
    beq.s h0_0996
h0_097E:
    tst.b $0113(a6)
    bne.s h0_0996
h0_0984:
    tst.b $0101(a6)
    beq.s h0_09A4
h0_098A:
    tst.b $0118(a6)
    bne.s h0_09A4
h0_0990:
    tst.b $0117(a6)
    bne.s h0_09A4
h0_0996:
    sf.b $0113(a6)
    clr.b $083B(a6)
    sf.b $0118(a6)
    rts
h0_09A4:
    sf.b $0102(a6)
    jsr h0_92A0.l
h0_09AE:
    bra.s h0_0996
    DC.L    $50ee0113,$720a4a2e,$02386708,$51ee0100,$50ee083a ; VIOLATION: orphaned code island at $09B0 is not reached from known entrypoints
    DC.B    $4e,$75
h0_09C6:
    rts
h0_09C8:
    movea.l $024C(a6),a5
    move.l a5,$0250(a6)
    clr.l $0182(a6)
    sf.b $010D(a6)
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.s h0_09C6
h0_09E0:
    cmp.b #$9,d1
    beq.s h0_09EC
h0_09E6:
    cmp.b #$20,d1
    bne.s h0_0A08
h0_09EC:
    clr.l $03E8(a6)
    bra.w h0_0A2A
h0_09F4:
    cmp.b #$3B,d1
    beq.w h0_0C44
h0_09FC:
    cmp.b #$2A,d1
    beq.w h0_0C44
h0_0A04:
    bra.w h0_8432
h0_0A08:
    st.b d2
    lea.l $03E8(a6),a0
    clr.b $0004(a0)
    bsr.w h0_76B8
h0_0A16:
    bne.s h0_09F4
h0_0A18:
    cmp.b #$3A,d1
    bne.s h0_0A2C
h0_0A1E:
    move.b (a4)+,d1
    cmp.b #$3A,d1
    bne.s h0_0A2C
h0_0A26:
    st.b $03EC(a6)
h0_0A2A:
    move.b (a4)+,d1
h0_0A2C:
    cmp.b #$9,d1
    beq.s h0_0A2A
h0_0A32:
    cmp.b #$20,d1
    beq.s h0_0A2A
h0_0A38:
    cmp.b #$3D,d1
    beq.w h0_748A
h0_0A40:
    subq.l #1,a4
    move.l a4,-(a7)
    moveq.l #0,d2
    movea.l #dat_B21E,a0
    movea.l #dat_CD3C,a1
    movea.l #dat_BA08,a2
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AB2
h0_0A68:
    move.w $0(a2,d1.w),d2
    bmi.s h0_0AE8
h0_0A6E:
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AB2
h0_0A7E:
    move.w $0(a2,d1.w),d2
    bmi.s h0_0AE8
h0_0A84:
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AB2
h0_0A94:
    move.w $0(a2,d1.w),d2
    bmi.s h0_0AE8
h0_0A9A:
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AB2
h0_0AAA:
    move.w $0(a2,d1.w),d2
    bpl.s h0_0A9A
h0_0AB0:
    bra.s h0_0AE8
h0_0AB2:
    move.w d2,d1
    add.w d1,d1
    add.w d1,d2
    movea.l #dat_E070,a0
    adda.w d2,a0
    tst.w $0002(a0)
    beq.s h0_0AE8
h0_0AC6:
    move.b -$0001(a4),d1
    cmp.b #$2E,d1
    beq.s h0_0AE2
h0_0AD0:
    cmp.b #$A,d1
    beq.s h0_0AE2
h0_0AD6:
    cmp.b #$9,d1
    beq.s h0_0AE2
h0_0ADC:
    cmp.b #$20,d1
    bne.s h0_0AE8
h0_0AE2:
    move.l (a7)+,d2
    bra.w h0_74A2
h0_0AE8:
    movea.l (a7)+,a4
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.w h0_0C44
h0_0AF4:
    cmp.b #$3B,d1
    beq.w h0_0C44
h0_0AFC:
    cmp.b #$2A,d1
    beq.w h0_0C44
h0_0B04:
    lea.l $0362(a6),a0
    bsr.w h0_7680
h0_0B0C:
    bne.w h0_8432
h0_0B10:
    movea.l $0172(a6),a2
    move.l a1,d4
    movem.l d2/a3-a5,-(a7)
    bsr.w h0_0B88
h0_0B1E:
    movem.l (a7)+,d2/a3-a5
    beq.w h0_6E5C
h0_0B26:
    movea.l d4,a4
    move.b -$0001(a4),d1
    cmp.b #$3A,d1
    bne.w h0_8446
h0_0B34:
    lea.l $03E8(a6),a1
    tst.l (a1)
    bne.w h0_8446
h0_0B3E:
    move.b d2,$0005(a0)
    bsr.s h0_0B4E
h0_0B44:
    movea.l a1,a0
    clr.b $0004(a0)
    bra.w h0_0A1E
h0_0B4E:
    move.b $0005(a0),$0005(a1)
    tst.b $00FE(a6)
    bne.s h0_0B64
h0_0B5A:
    move.l (a0),(a1)
    move.b $0006(a0),$0006(a1)
    rts
h0_0B64:
    move.b $0005(a0),d0
    lea.l $0006(a1),a2
    move.l a2,(a1)
    addq.w #6,a0
h0_0B70:
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s h0_0B70
h0_0B76:
    rts
h0_0B78:
    move.l (a2),d0
    beq.s h0_0BC8
h0_0B7C:
    movea.l d0,a1
    move.b $0016(a0),d2
    lea.l $0017(a0),a5
    bra.s h0_0B9C
h0_0B88:
    move.l (a2),d0
    beq.s h0_0BC8
h0_0B8C:
    movea.l d0,a1
    move.b $0005(a0),d2
    movea.l (a0),a5
    bra.s h0_0B9C
h0_0B96:
    move.l (a1),d0
    beq.s h0_0BC4
h0_0B9A:
    movea.l d0,a1
h0_0B9C:
    cmp.b $0016(a1),d2
    bcs.s h0_0B96
h0_0BA2:
    bhi.s h0_0BB8
h0_0BA4:
    move.b d2,d3
    lea.l $0017(a1),a3
    movea.l a5,a4
h0_0BAC:
    cmpm.b (a3)+,(a4)+
    bcs.s h0_0B96
h0_0BB0:
    bhi.s h0_0BB8
h0_0BB2:
    subq.b #1,d3
    bne.s h0_0BAC
h0_0BB6:
    rts
h0_0BB8:
    move.l $0004(a1),d0
    beq.s h0_0BC2
h0_0BBE:
    movea.l d0,a1
    bra.s h0_0B9C
h0_0BC2:
    addq.w #4,a1
h0_0BC4:
    moveq.l #3,d0
    rts
h0_0BC8:
    movea.l a2,a1
    moveq.l #3,d0
    rts
h0_0BCE:
    movem.l a3-a5,-(a7)
    move.l $015A(a6),d0
    beq.s h0_0BE2
h0_0BD8:
    movea.l d0,a2
    bsr.s h0_0B88
h0_0BDC:
    beq.s h0_0BFC
h0_0BDE:
    move.l a1,$015E(a6)
h0_0BE2:
    movea.l $0162(a6),a2
    bsr.s h0_0B88
h0_0BE8:
    beq.s h0_0BFC
h0_0BEA:
    move.l a1,$0166(a6)
    movea.l $016A(a6),a2
    bsr.s h0_0B88
h0_0BF4:
    beq.s h0_0BFC
h0_0BF6:
    move.l a1,$016E(a6)
    moveq.l #-1,d0
h0_0BFC:
    movem.l (a7)+,a3-a5
    rts
h0_0C02:
    bsr.s h0_0BCE
h0_0C04:
    bne.w h0_843A
h0_0C08:
    bset.b #6,$000C(a1)
    bne.w h0_8436
h0_0C12:
    move.b $0108(a6),d3
    cmp.b $000D(a1),d3
    bne.w h0_8436
h0_0C1E:
    cmp.l $0008(a1),d4
    bne.w h0_843E
h0_0C26:
    move.b $0017(a1),d0
    cmp.b $0116(a6),d0
    beq.s h0_0C42
h0_0C30:
    tst.b $0004(a0)
    beq.s h0_0C3A
h0_0C36:
    bsr.w h0_4E4C
h0_0C3A:
    lea.l $0010(a1),a0
    move.l a0,$015A(a6)
h0_0C42:
    rts
h0_0C44:
    move.l $023C(a6),d4
    lea.l $03E8(a6),a0
    tst.l (a0)
    bne.s h0_0C84
h0_0C50:
    rts
h0_0C52:
    btst.b #0,$023F(a6)
    bne.w h0_0C5E
h0_0C5C:
    rts
h0_0C5E:
    jmp h0_9746.l
h0_0C64:
    lea.l $03E8(a6),a0
    tst.l (a0)
    beq.s h0_0C52
h0_0C6C:
    move.l $023C(a6),d4
    btst #0,d4
    beq.s h0_0C84
h0_0C76:
    jsr h0_9746.l
h0_0C7C:
    lea.l $03E8(a6),a0
    move.l $023C(a6),d4
h0_0C84:
    tst.b $0238(a6)
    bne.w h0_0C02
h0_0C8C:
    bsr.w h0_0BCE
h0_0C90:
    beq.w h0_8436
h0_0C94:
    move.b $0108(a6),d3
    move.b $0006(a0),d0
    cmp.b $0116(a6),d0
    beq.s h0_0CAC
h0_0CA2:
    pea.l h0_0C3A(pc)
    lea.l $0162(a6),a2
    bra.s h0_0CB6
h0_0CAC:
    lea.l $015A(a6),a2
    tst.l (a2)
    beq.w h0_8442
h0_0CB6:
    movea.l $0004(a2),a1
h0_0CBA:
    cmpi.w #152,app_ULONG(a6)
    bcc.s h0_0CD0
h0_0CC2:
    movem.l d3/a0-a1,-(a7)
    jsr h0_90A8.l
h0_0CCC:
    movem.l (a7)+,d3/a0-a1
h0_0CD0:
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
h0_0D06:
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s h0_0D06
h0_0D0C:
    move.l a2,d0
    sub.l a1,d0
    addq.l #1,d0
    bclr #0,d0
    sub.w d0,app_ULONG(a6)
    add.l d0,$013A(a6)
    rts
h0_0D20:
    cmp.w app_ULONG(a6),d0
    bcs.s h0_0D34
h0_0D26:
    movem.l d0/d3/a0-a1,-(a7)
    jsr h0_90A8.l
h0_0D30:
    movem.l (a7)+,d0/d3/a0-a1
h0_0D34:
    move.l d0,-(a7)
    bsr.s h0_0CBA
h0_0D38:
    sub.l d0,$013A(a6)
    add.w d0,app_ULONG(a6)
    move.l (a7)+,d0
    sub.w d0,app_ULONG(a6)
    add.l d0,$013A(a6)
    rts
    DC.L    $226a0004,$0c6e0098,$0148640e,$48e710c0 ; VIOLATION: orphaned code island at $0D4C is not reached from known entrypoints
    DC.B    $4e,$b9
    DC.L    h0_90A8
    DC.B    $4c,$df
    DC.L    $0308246e,$013a228a,$224a7000,$24802540,$00042544,$00081543,$000d3540,$00141540
    DC.L    $000c156e,$0146000e,$25400010,$45ea0016,$10280005,$205014c0,$14d85300,$66fa200a
    DC.L    $90895280,$08800000,$916e0148,$d1ae013a
    DC.B    $4e,$75
h0_0DB6:
    bsr.s h0_0DCC
h0_0DB8:
    cmp.b #$F,d3
    bcs.s h0_0DCA
h0_0DBE:
    cmp.b #$13,d3
    bcc.s h0_0DCA
h0_0DC4:
    moveq.l #98,d0
    bra.w h0_8486
h0_0DCA:
    rts
h0_0DCC:
    bsr.w h0_79E6
h0_0DD0:
    lea.l $0628(a6),a0
    clr.w (a0)
    lea.l $0650(a6),a0
    clr.w (a0)
    moveq.l #0,d4
    movem.l d5-d7,-(a7)
    moveq.l #1,d5
    bsr.w h0_1208
h0_0DE8:
    cmp.b #$1,d7
    bne.s h0_0E2C
h0_0DEE:
    movem.l d2-d3,-(a7)
    addq.b #1,d5
    bsr.w h0_1208
h0_0DF8:
    cmp.b #$4,d7
    bcs.w h0_0E50
h0_0E00:
    cmp.b #$16,d7
    bcc.w h0_0E50
h0_0E08:
    lea.l $0628(a6),a0
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,$0(a0,d0.w)
    lea.l $0650(a6),a0
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l (a7)+,$0(a0,d0.w)
    move.l (a7)+,$4(a0,d0.w)
    bsr.w h0_0EDA
h0_0E2A:
    bra.s h0_0E3E
h0_0E2C:
    lea.l $0628(a6),a0
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,$0(a0,d0.w)
    bsr.w h0_0F0A
h0_0E3E:
    movem.l (a7)+,d5-d7
    tst.w $0628(a6)
    bne.s h0_0E62
h0_0E48:
    tst.w $0650(a6)
    bne.s h0_0E62
h0_0E4E:
    rts
h0_0E50:
    movem.l (a7)+,d2-d3
    movem.l (a7)+,d5-d7
    movea.l a0,a4
    move.b -$0001(a4),d1
    moveq.l #0,d0
    rts
h0_0E62:
    moveq.l #18,d0
    bra.w h0_8482
    DC.L    $112b122d,$042a052f,$02280329,$137e083d,$0e26ea21,$105e0f7c,$fe24fa25,$f840f427
    DC.B    $f4,$22,$00
dat_0E8B:
    DC.B    $00
    DC.L    $00000004,$04161614,$14141414
    DC.B    $14,$12
    DC.W    h0_20B4-dat_0EA2
    DC.W    h0_10A4-dat_0EA2
    DC.W    h0_2BC0-dat_0EA2
    DC.W    h0_2CA2-dat_0EA2
dat_0EA2:
    DC.W    h0_10DA-dat_0EA2
    DC.W    h0_10F8-dat_0EA2
    DC.W    h0_1120-dat_0EA2
    DC.W    h0_1124-dat_0EA2
    DC.W    h0_1128-dat_0EA2
    DC.W    h0_1150-dat_0EA2
    DC.W    h0_1156-dat_0EA2
    DC.W    h0_115C-dat_0EA2
    DC.W    h0_1162-dat_0EA2
    DC.W    h0_1168-dat_0EA2
    DC.W    h0_1114-dat_0EA2
    DC.W    h0_1118-dat_0EA2
    DC.W    h0_111C-dat_0EA2
    DC.W    h0_1050-dat_0EA2
    DC.W    h0_1096-dat_0EA2
    DC.W    h0_116E-dat_0EA2
    DC.W    h0_117A-dat_0EA2
    DC.W    h0_1178-dat_0EA2
h0_0EC6:
    lea.l $0628(a6),a0
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,$0(a0,d0.w)
    moveq.l #1,d5
    bsr.w h0_1208
h0_0EDA:
    cmp.b #$2,d5
    bne.s h0_0EF0
h0_0EE0:
    cmp.b #$4,d7
    bcs.w h0_0FC4
h0_0EE8:
    cmp.b #$16,d7
    bcc.w h0_0FC4
h0_0EF0:
    cmp.b #$1,d7
    bne.s h0_0F0A
h0_0EF6:
    lea.l $0650(a6),a0
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l d2,$0(a0,d0.w)
    move.l d3,$4(a0,d0.w)
    bra.w h0_0FBA
h0_0F0A:
    cmp.b #$2,d7
    beq.w h0_0F8A
h0_0F12:
    cmp.b #$4,d7
    bcs.w h0_0FCA
h0_0F1A:
    cmp.b #$16,d7
    bcc.w h0_0FCA
h0_0F22:
    cmp.b #$1,d5
    bne.s h0_0F60
h0_0F28:
    cmp.b #$11,d7
    beq.s h0_0F5A
h0_0F2E:
    cmp.b #$12,d7
    beq.s h0_0F5E
h0_0F34:
    cmp.b #$4,d7
    beq.s h0_0F44
h0_0F3A:
    cmp.b #$13,d7
    bne.w h0_0E62
h0_0F42:
    bra.s h0_0F60
h0_0F44:
    move.l $023C(a6),d2
    moveq.l #0,d3
    move.b $0108(a6),d3
    cmp.b #$1,d3
    bne.s h0_0F58
h0_0F54:
    addq.b #1,$010B(a6)
h0_0F58:
    bra.s h0_0EF6
h0_0F5A:
    moveq.l #21,d7
    bra.s h0_0F60
h0_0F5E:
    moveq.l #20,d7
h0_0F60:
    lea.l dat_0E8B(pc),a2
    lea.l $0628(a6),a0
    move.w (a0),d0
    move.w $0(a0,d0.w),d6
    move.b $0(a2,d6.w),d6
    cmp.b $0(a2,d7.w),d6
    bge.s h0_0F80
h0_0F78:
    addq.w #2,(a0)+
    move.w d7,$0(a0,d0.w)
    bra.s h0_0F86
h0_0F80:
    bsr.w h0_0FFA
h0_0F84:
    bra.s h0_0F60
h0_0F86:
    moveq.l #0,d5
    bra.s h0_0FBA
h0_0F8A:
    bsr.w h0_0EC6
h0_0F8E:
    bsr.w h0_1208
h0_0F92:
    lea.l $0650(a6),a0
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l d2,$0(a0,d0.w)
    move.l d3,$4(a0,d0.w)
    tst.w d3
    bpl.s h0_0FAC
h0_0FA6:
    moveq.l #42,d0
    bsr.w h0_8486
h0_0FAC:
    cmp.b #$3,d7
    beq.s h0_0FB8
h0_0FB2:
    moveq.l #19,d0
    bra.w h0_8482
h0_0FB8:
    moveq.l #1,d5
h0_0FBA:
    addq.w #1,d5
    bsr.w h0_1208
h0_0FC0:
    bra.w h0_0EDA
h0_0FC4:
    movea.l a0,a4
    move.b -$0001(a4),d1
h0_0FCA:
    lea.l dat_0E8B(pc),a2
h0_0FCE:
    lea.l $0628(a6),a0
    move.w (a0),d0
    tst.w $0(a0,d0.w)
    beq.s h0_0FE0
h0_0FDA:
    bsr.w h0_0FFA
h0_0FDE:
    bra.s h0_0FCE
h0_0FE0:
    subq.w #2,$0628(a6)
    lea.l $0650(a6),a0
    subq.w #8,(a0)
    move.w (a0)+,d0
    move.l $0(a0,d0.w),d2
    move.l $4(a0,d0.w),d3
    rts
h0_0FF6:
    bra.w h0_0E62
h0_0FFA:
    lea.l $0650(a6),a0
    subq.w #8,(a0)
    bcs.s h0_0FF6
h0_1002:
    move.w (a0)+,d0
    move.l $0(a0,d0.w),d2
    move.l $4(a0,d0.w),d3
    move.w d1,-(a7)
    lea.l $0628(a6),a1
    subq.w #2,(a1)
    move.w (a1)+,d1
    move.w $0(a1,d1.w),d1
    cmp.b #$13,d1
    bcc.s h0_1032
h0_1020:
    subq.w #8,-(a0)
    bcs.s h0_0FF6
h0_1024:
    move.w (a0)+,d0
    move.l $4(a0,d0.w),d6
    move.l $0(a0,d0.w),d0
    exg d0,d2
    exg d6,d3
h0_1032:
    lea.l dat_0EA2(pc),a1
    add.w d1,d1
    move.w -$8(a1,d1.w),d1
    jsr $0(a1,d1.w)
h0_1040:
    move.w (a7)+,d1
    move.w -(a0),d0
    addq.w #8,(a0)+
    move.l d2,$0(a0,d0.w)
    move.l d3,$4(a0,d0.w)
    rts
h0_1050:
    add.l d0,d2
    cmp.b #$1,d3
    beq.s h0_1066
h0_1058:
    cmp.b #$1,d6
    beq.s h0_106C
h0_105E:
    andi.w #65280,d6
    or.w d6,d3
    rts
h0_1066:
    cmp.b #$1,d6
    beq.s h0_1072
h0_106C:
    move.b #$1,d3
    bra.s h0_105E
h0_1072:
    tst.b $0107(a6)
    bne.s h0_1086
h0_1078:
    tst.b $0238(a6)
    beq.s h0_108A
h0_107E:
    moveq.l #21,d0
h0_1080:
    bsr.w h0_8486
h0_1084:
    st.b d4
h0_1086:
    moveq.l #2,d3
    rts
h0_108A:
    tst.b $0158(a6)
    bne.s h0_107E
h0_1090:
    bra.s h0_1084
h0_1092:
    moveq.l #20,d0
    bra.s h0_1080
h0_1096:
    sub.l d0,d2
    move.w d3,d0
    or.w d6,d0
    andi.w #32768,d0
    tst.w d6
    bmi.s h0_10D4
h0_10A4:
    cmp.b #$1,d6
    bne.s h0_10C0
h0_10AA:
    btst.b #1,$021C(a6)
    bne.s h0_10BC
h0_10B2:
    btst #15,d3
    beq.s h0_10BC
h0_10B8:
    add.l $023C(a6),d2
h0_10BC:
    subq.b #2,$010B(a6)
h0_10C0:
    cmp.b d3,d6
    beq.s h0_10CC
h0_10C4:
    cmp.b #$1,d6
    bne.s h0_10D0
h0_10CA:
    bsr.s h0_1072
h0_10CC:
    move.b #$2,d3
h0_10D0:
    or.w d0,d3
    rts
h0_10D4:
    bsr.w h0_7A20
h0_10D8:
    bra.s h0_10C0
h0_10DA:
    bsr.s h0_10E4
h0_10DC:
    bsr.w h0_117E
h0_10E0:
    moveq.l #2,d3
    rts
h0_10E4:
    cmp.b #$1,d6
    beq.s h0_1072
h0_10EA:
    or.w d3,d6
    bmi.s h0_1092
h0_10EE:
    cmp.b #$1,d3
    beq.w h0_1072
h0_10F6:
    rts
h0_10F8:
    bsr.s h0_10E4
h0_10FA:
    move.l d7,-(a7)
    bsr.w h0_11B2
h0_1100:
    movem.l (a7)+,d7
    bne.s h0_1108
h0_1106:
    rts
h0_1108:
    tst.b $0238(a6)
    bne.w h0_1080
h0_1110:
    bra.w h0_108A
h0_1114:
    and.l d0,d2
    bra.s h0_10E4
h0_1118:
    or.l d0,d2
    bra.s h0_10E4
h0_111C:
    eor.l d0,d2
    bra.s h0_10E4
h0_1120:
    lsl.l d0,d2
    bra.s h0_10E4
h0_1124:
    lsr.l d0,d2
    bra.s h0_10E4
h0_1128:
    cmp.l d0,d2
    seq.b d2
h0_112C:
    ext.w d2
    ext.l d2
    move.w d3,d0
    or.w d6,d0
    bmi.w h0_1092
h0_1138:
    cmp.b d3,d6
    beq.s h0_114C
h0_113C:
    cmp.b #$1,d3
    beq.w h0_1072
h0_1144:
    cmp.b #$1,d6
    beq.w h0_1072
h0_114C:
    moveq.l #2,d3
    rts
h0_1150:
    cmp.l d0,d2
    sne.b d2
    bra.s h0_112C
h0_1156:
    cmp.l d0,d2
    slt.b d2
    bra.s h0_112C
h0_115C:
    cmp.l d0,d2
    sgt.b d2
    bra.s h0_112C
h0_1162:
    cmp.l d0,d2
    sle.b d2
    bra.s h0_112C
h0_1168:
    cmp.l d0,d2
    sge.b d2
    bra.s h0_112C
h0_116E:
    not.l d2
h0_1170:
    cmp.w #$1,d3
    beq.w h0_1072
h0_1178:
    rts
h0_117A:
    neg.l d2
    bra.s h0_1170
h0_117E:
    move.l d2,d6
    eor.l d0,d6
    tst.l d2
    bgt.s h0_1188
h0_1186:
    neg.l d2
h0_1188:
    tst.l d0
    bgt.s h0_118E
h0_118C:
    neg.l d0
h0_118E:
    move.l d2,d3
    swap.w d3
    mulu.w d0,d2
    swap.w d0
    tst.w d3
    beq.s h0_119E
h0_119A:
    swap.w d0
    bra.s h0_11A4
h0_119E:
    tst.w d0
    beq.s h0_11AA
h0_11A2:
    swap.w d3
h0_11A4:
    mulu.w d3,d0
    swap.w d0
    add.l d0,d2
h0_11AA:
    tst.l d6
    bpl.s h0_11B0
h0_11AE:
    neg.l d2
h0_11B0:
    rts
h0_11B2:
    tst.l d0
    beq.s h0_1200
h0_11B6:
    move.l d2,d6
    eor.l d0,d6
    move.l d6,-(a7)
    move.l d2,-(a7)
    tst.l d0
    bpl.s h0_11C4
h0_11C2:
    neg.l d0
h0_11C4:
    tst.l d2
    bpl.s h0_11CA
h0_11C8:
    neg.l d2
h0_11CA:
    moveq.l #31,d6
    move.l d0,d7
    moveq.l #0,d0
h0_11D0:
    add.l d7,d7
h0_11D2:
    dbcs.w d6,h0_11D0
h0_11D6:
    roxr.l #1,d7
    subi.w #31,d6
    neg.w d6
h0_11DE:
    add.l d0,d0
    cmp.l d7,d2
    bcs.s h0_11E8
h0_11E4:
    addq.l #1,d0
    sub.l d7,d2
h0_11E8:
    lsr.l #1,d7
    dbf.w d6,h0_11DE
h0_11EE:
    move.l (a7)+,d6
    bpl.s h0_11F4
h0_11F2:
    neg.l d2
h0_11F4:
    move.l (a7)+,d6
    bpl.s h0_11FA
h0_11F8:
    neg.l d0
h0_11FA:
    exg d0,d2
    cmp.b d0,d0
    rts
h0_1200:
    moveq.l #61,d0
    rts
    DC.B    $20,$4c,$4e,$75 ; VIOLATION: orphaned code island at $1204 is not reached from known entrypoints
h0_1208:
    moveq.l #0,d7
    ext.w d1
    bmi.s h0_1232
h0_120E:
    move.b dat_1252(pc,d1.w),d7
    beq.s h0_1220
h0_1214:
    bpl.s h0_1226
h0_1216:
    cmp.b #$FF,d7
    bne.s h0_123C
h0_121C:
    bra.w h0_1246
h0_1220:
    movea.l a4,a0
    moveq.l #22,d7
    rts
h0_1226:
    cmp.b #$1,d7
    beq.s h0_1232
h0_122C:
    movea.l a4,a0
    move.b (a4)+,d1
    rts
h0_1232:
    movem.l d5-d6/a1-a2,-(a7)
    move.l a4,-(a7)
    bra.w h0_12D2
h0_123C:
    movem.l d5-d6/a1-a2,-(a7)
    move.l a4,-(a7)
    bra.w h0_13B8
h0_1246:
    movem.l d5-d6/a1-a2,-(a7)
    move.l a4,-(a7)
    moveq.l #0,d2
    bra.w h0_1324
dat_1252:
    DC.B    $00,$00
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$000000ea
    DC.L    $f400fefa,$0ef40203,$04110012,$0105ffff,$ffffffff,$ffffffff,$0000f208,$ee00f801
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01000000,$10010001
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01000f00
    DC.B    $13,$00
h0_12D2:
    lea.l $046E(a6),a0
    bsr.w h0_76B8
h0_12DA:
    beq.w h0_1530
h0_12DE:
    moveq.l #22,d7
    bra.s h0_131C
h0_12E2:
    move.b (a4)+,d1
    cmp.b #$3D,d1
    beq.s h0_1300
h0_12EA:
    moveq.l #15,d7
    bra.s h0_131C
h0_12EE:
    moveq.l #10,d7
    move.b (a4)+,d1
    cmp.b #$3C,d1
    beq.s h0_1318
h0_12F8:
    cmp.b #$3E,d1
    beq.s h0_1300
h0_12FE:
    bra.s h0_130E
h0_1300:
    moveq.l #9,d7
    bra.s h0_131A
h0_1304:
    moveq.l #11,d7
    move.b (a4)+,d1
    cmp.b #$3E,d1
    beq.s h0_1318
h0_130E:
    cmp.b #$3D,d1
    bne.s h0_131C
h0_1314:
    addq.w #2,d7
    bra.s h0_131A
h0_1318:
    subq.w #4,d7
h0_131A:
    move.b (a4)+,d1
h0_131C:
    movea.l (a7)+,a0
    movem.l (a7)+,d5-d6/a1-a2
    rts
h0_1324:
    move.b $012F(a6),d7
    beq.s h0_1330
h0_132A:
    subq.l #1,a4
    bra.w h0_13B8
h0_1330:
    lea.l -$0001(a4),a0
h0_1334:
    add.l d2,d2
    move.l d2,d0
    add.l d0,d0
    add.l d0,d0
    add.l d0,d2
    subi.b #48,d1
    andi.l #15,d1
    add.l d1,d2
    move.b (a4)+,d1
    cmp.b #$3A,d1
    bcc.s h0_1358
h0_1352:
    cmp.b #$30,d1
    bcc.s h0_1334
h0_1358:
    moveq.l #1,d7
    moveq.l #2,d3
    cmp.b #$24,d1
    bne.s h0_131C
h0_1362:
    bra.w h0_166A
h0_1366:
    moveq.l #4,d0
    move.b d1,d3
h0_136A:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.w h0_1434
h0_1374:
    cmp.b d3,d1
    bne.s h0_1382
h0_1378:
    move.b (a4)+,d1
    cmp.b d3,d1
    beq.s h0_1382
h0_137E:
    moveq.l #2,d3
    bra.s h0_131C
h0_1382:
    subq.b #1,d0
    bcs.w h0_143E
h0_1388:
    lsl.l #8,d2
    move.b d1,d2
    bra.s h0_136A
h0_138E:
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.w h0_1434
h0_1398:
    cmp.b #$2,d1
    bcc.w h0_1434
h0_13A0:
    add.l d2,d2
    bcs.w h0_143E
h0_13A6:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.s h0_142C
h0_13B0:
    cmp.b #$2,d1
    bcs.s h0_13A0
h0_13B6:
    bra.s h0_142C
h0_13B8:
    neg.b d7
    ext.w d7
    moveq.l #0,d2
    moveq.l #2,d3
    moveq.l #1,d0
    exg d0,d7
h0_13C4:
    jmp h0_13C8-2(pc,d0.w) ; VIOLATION: invalid overlap: instruction bytes at +2 are referenced by reachable pc-relative operand | invalid overlap: pc-relative reference targets +2 into instruction at $13C4
h0_13C8:
    bra.w h0_140E
h0_13CC:
    bra.s h0_138E
h0_13CE:
    bra.w h0_13E6
h0_13D2:
    bra.s h0_1366
h0_13D4:
    bra.w h0_12EE
h0_13D8:
    bra.w h0_1304
h0_13DC:
    bra.w h0_12E2
h0_13E0:
    moveq.l #64,d1
h0_13E2:
    bra.w h0_12D2
h0_13E6:
    move.b (a4),d0
    subi.b #48,d0
    bcs.s h0_13E0
h0_13EE:
    cmp.b #$9,d0
    bcc.s h0_13E0
h0_13F4:
    move.b d0,d1
    addq.l #1,a4
h0_13F8:
    lsl.l #3,d2
    bcs.s h0_143E
h0_13FC:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.s h0_142C
h0_1406:
    cmp.b #$9,d1
    bcs.s h0_13F8
h0_140C:
    bra.s h0_142C
h0_140E:
    lea.l dat_1442(pc),a0
    moveq.l #0,d1
    move.b (a4)+,d1
    bmi.s h0_1434
h0_1418:
    move.b $0(a0,d1.w),d1
    bmi.s h0_1434
h0_141E:
    lsl.l #4,d2
    or.b d1,d2
    move.b (a4)+,d1
    bmi.s h0_142C
h0_1426:
    move.b $0(a0,d1.w),d1
    bpl.s h0_141E
h0_142C:
    move.b -$0001(a4),d1
    bra.w h0_131C
h0_1434:
    moveq.l #22,d0
h0_1436:
    bsr.w h0_8486
h0_143A:
    st.b d4
    bra.s h0_142C
h0_143E:
    moveq.l #23,d0
    bra.s h0_1436
dat_1442:
    DC.B    $ff,$ff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffff0001,$02030405,$06070809,$ffffffff,$ffffff0a
    DC.L    $0b0c0d0e,$0fffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffff0a
    DC.L    $0b0c0d0e,$0fffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.B    $ff,$ff
h0_14C2:
    movea.l (a0),a1
    subq.l #4,a7
    move.b (a1)+,$0002(a7)
h0_14CA:
    move.b (a1)+,$0003(a7)
    move.b (a1)+,(a7)
    move.b (a1)+,$0001(a7)
    move.l (a7)+,d0
    cmp.l #$52474E41,d0
    beq.s h0_151E
h0_14DE:
    cmp.w #$5F5F,d0
    bne.s h0_151C
h0_14E4:
    swap.w d0
    cmp.w #$5253,d0
    beq.s h0_1516
h0_14EC:
    cmp.w #$4732,d0
    beq.s h0_1504
h0_14F2:
    cmp.w #$4C4B,d0
    beq.s h0_14FA
h0_14F8:
    bne.s h0_151C
h0_14FA:
    moveq.l #0,d2
    move.w $021C(a6),d2
    addq.w #1,d2
    bra.s h0_1512
h0_1504:
    move.l #$1002B,d2
    move.b $0121(a6),d0
    lsl.w #8,d0
    or.w d0,d2
h0_1512:
    moveq.l #0,d0
    rts
h0_1516:
    move.l $084A(a6),d2
    bra.s h0_1512
h0_151C:
    rts
h0_151E:
    moveq.l #0,d2
    tst.b $0101(a6)
    beq.s h0_151C
h0_1526:
    movea.l $0882(a6),a1
    move.w $0008(a1),d2
    bra.s h0_1512
h0_1530:
    moveq.l #1,d7
    seq.b $0004(a0)
    cmp.b #$23,d1
    bne.s h0_1542
h0_153C:
    move.b (a4)+,d1
    st.b $0004(a0)
h0_1542:
    cmpi.b #4,$0005(a0)
    bne.s h0_1556
h0_154A:
    bsr.w h0_14C2
h0_154E:
    bne.s h0_1556
h0_1550:
    moveq.l #2,d3
    bra.w h0_15C8
h0_1556:
    tst.b $0238(a6)
    bne.w h0_1606
h0_155E:
    bsr.w h0_0BCE
h0_1562:
    beq.s h0_156C
h0_1564:
    moveq.l #0,d2
    st.b d4
    moveq.l #2,d3
    bra.s h0_15C8
h0_156C:
    move.l $0008(a1),d2
    moveq.l #0,d3
    move.b $000D(a1),d3
    btst.b #4,$000C(a1)
    bne.s h0_15D0
h0_157E:
    cmp.b #$2,d3
    beq.s h0_15C8
h0_1584:
    cmp.b #$E,d3
    beq.s h0_15C8
h0_158A:
    cmp.b #$1,d3
    beq.s h0_15F2
h0_1590:
    cmp.b #$F,d3
    bcs.s h0_15B8
h0_1596:
    cmp.b #$13,d3
    bcc.s h0_15B8
h0_159C:
    lea.l $0872(a6),a0
    move.l a0,d2
    move.l $0008(a1),(a0)+
    move.b $000E(a1),(a0)+
    move.b $000F(a1),(a0)+
    move.l $0010(a1),(a0)+
    move.w $0014(a1),(a0)
    bra.s h0_15C8
h0_15B8:
    cmp.b #$5,d3
    bne.w h0_1696
h0_15C0:
    moveq.l #2,d3
    moveq.l #7,d0
    bsr.w h0_858C
h0_15C8:
    move.b -$0001(a4),d1
    bra.w h0_131C
h0_15D0:
    st.b d4
    swap.w d3
    move.w $0014(a1),d3
    bsr.w h0_79F6
h0_15DC:
    swap.w d3
    move.b -$0001(a4),d1
    tst.b $0238(a6)
    beq.w h0_131C
h0_15EA:
    ori.w #32768,d3
    bra.w h0_131C
h0_15F2:
    tst.b $000E(a1)
    beq.s h0_15C8
h0_15F8:
    move.b $0146(a6),d0
    cmp.b $000E(a1),d0
    beq.s h0_15C8
h0_1602:
    st.b d4
    bra.s h0_15C8
h0_1606:
    bsr.w h0_0BCE
h0_160A:
    sne.b d0
    move.b -$0001(a4),d1
    cmp.b #$23,d1
    bne.s h0_1618
h0_1616:
    move.b (a4)+,d1
h0_1618:
    tst.b d0
    bne.w h0_16A4
h0_161E:
    btst.b #7,$000C(a1)
    beq.s h0_1630
h0_1626:
    btst.b #6,$000C(a1)
    beq.w h0_16A4
h0_1630:
    move.l $0008(a1),d2
    moveq.l #0,d3
    move.b $000D(a1),d3
    btst.b #4,$000C(a1)
    bne.s h0_15D0
h0_1642:
    cmp.b #$1,d3
    bne.w h0_157E
h0_164A:
    move.b $0146(a6),d0
    cmp.b $000E(a1),d0
    bne.s h0_165C
h0_1654:
    addq.b #1,$010B(a6)
    bra.w h0_131C
h0_165C:
    ori.w #32768,d3
    st.b d4
    bsr.w h0_7A0C
h0_1666:
    bra.w h0_131C
h0_166A:
    movea.l a0,a1
    lea.l $046E(a6),a0
    lea.l $0006(a0),a2
    move.l a2,(a0)
    sf.b $0004(a0)
    move.b $0116(a6),(a2)+
    move.l a4,d0
    sub.l a1,d0
    move.b d0,$0005(a0)
    subq.b #1,d0
h0_1688:
    move.b (a1)+,(a2)+
    subq.b #1,d0
    bne.s h0_1688
h0_168E:
    move.b (a4)+,d1
    moveq.l #1,d7
    bra.w h0_1556
h0_1696:
    moveq.l #24,d0
h0_1698:
    moveq.l #2,d3
    st.b d4
    bsr.w h0_8486
h0_16A0:
    bra.w h0_131C
h0_16A4:
    moveq.l #3,d0
    bra.s h0_1698
h0_16A8:
    bsr.w h0_0DB6
h0_16AC:
    tst.w d3
    bmi.s h0_16C4
h0_16B0:
    cmp.b #$F,d3
    bcs.s h0_16C2
h0_16B6:
    cmp.b #$13,d3
    bcc.s h0_16C2
h0_16BC:
    moveq.l #98,d0
    bra.w h0_8486
h0_16C2:
    rts
h0_16C4:
    st.b d4
    moveq.l #20,d0
    bra.w h0_8486
h0_16CC:
    bsr.s h0_16A8
h0_16CE:
    cmp.b #$1,d3
    bne.s h0_16DC
h0_16D4:
    tst.b $0107(a6)
    beq.w h0_8452
h0_16DC:
    moveq.l #0,d0
    rts
h0_16E0:
    movea.l (a7),a0
    addq.l #2,(a7)
    bra.s h0_16EC
    DC.B    $20,$57,$54,$97,$3a,$c6 ; VIOLATION: orphaned code island at $16E6 is not reached from known entrypoints
h0_16EC:
    move.w (a0),d0
    move.w d0,-(a7)
    btst #6,d0
    beq.s h0_16FE
h0_16F6:
    bsr.w h0_1872
h0_16FA:
    move.w (a7)+,d0
    bra.s h0_1704
h0_16FE:
    bsr.w h0_187E
h0_1702:
    move.w (a7)+,d0
h0_1704:
    movea.l $024C(a6),a0
    or.w d5,(a0)
    cmp.b #$30,d5
    bcs.s h0_1738
h0_1710:
    cmp.b #$3A,d5
    bcs.s h0_172A
h0_1716:
    cmp.b #$3C,d5
    beq.s h0_1732
h0_171C:
    btst #6,d5
    bne.s h0_1748
h0_1722:
    btst #6,d0
    beq.s h0_1742
h0_1728:
    rts
h0_172A:
    btst #5,d0
    beq.s h0_1742
h0_1730:
    rts
h0_1732:
    tst.b d0
    bpl.s h0_1742
h0_1736:
    rts
h0_1738:
    move.b d5,d2
    lsr.b #3,d2
    btst d2,d0
    beq.s h0_1742
h0_1740:
    rts
h0_1742:
    moveq.l #17,d0
    bra.w h0_8486
h0_1748:
    andi.w #191,d5
    move.w d5,d2
    rol.w #8,d2
    and.w d2,d0
    beq.s h0_1742
h0_1754:
    movea.l (a7)+,a0
    jmp $0002(a0)                       ; CANDIDATE: indirect_jump index unresolved
h0_175A:
    moveq.l #37,d0
    bra.w h0_8482
h0_1760:
    bsr.s h0_177E
h0_1762:
    bne.s h0_175A
h0_1764:
    tst.b d0
    bne.s h0_175A
h0_1768:
    rts
h0_176A:
    bsr.s h0_177E
h0_176C:
    bne.s h0_177A
h0_176E:
    tst.b d0
    bne.s h0_1778
h0_1772:
    moveq.l #16,d0
    bsr.w h0_8486
h0_1778:
    cmp.b d0,d0
h0_177A:
    rts
    DC.B    $60,$f4
h0_177E:
    move.b d1,d0
    movea.l a4,a0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b #$41,d0
    beq.s h0_17B6
h0_178E:
    cmp.b #$44,d0
    beq.s h0_17B6
h0_1794:
    cmp.b #$52,d0
    beq.s h0_17E4
h0_179A:
    cmp.b #$53,d0
    bne.w h0_181A
h0_17A2:
    move.b (a0)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b #$50,d0
    bne.s h0_181A
h0_17B0:
    moveq.l #1,d0
    moveq.l #7,d2
    bra.s h0_17CA
h0_17B6:
    move.b (a0)+,d2
    cmp.b #$37,d2
    bhi.s h0_181A
h0_17BE:
    subi.b #48,d2
    bcs.s h0_181A
h0_17C4:
    cmp.b #$41,d0
    seq.b d0
h0_17CA:
    andi.b #1,d0
    moveq.l #0,d1
    move.b (a0)+,d1
    movea.l #dat_A764,a1
    tst.b $0(a1,d1.w)
    beq.s h0_181A
h0_17DE:
    movea.l a0,a4
    cmp.b d0,d0
    rts
h0_17E4:
    move.b (a0)+,d2
    cmp.b #$39,d2
    bhi.s h0_181A
h0_17EC:
    cmp.b #$30,d2
    bcs.s h0_181A
h0_17F2:
    cmp.b #$31,d2
    bne.s h0_180E
h0_17F8:
    move.b (a0),d0
    cmp.b #$36,d0
    bcc.s h0_180E
h0_1800:
    cmp.b #$30,d0
    bcs.s h0_180E
h0_1806:
    addi.b #10,d0
    move.b d0,d2
    addq.l #1,a0
h0_180E:
    subi.b #48,d2
    cmp.b #$8,d2
    scc.b d0
    bra.s h0_17CA
h0_181A:
    lea.l $046E(a6),a0
    movem.l a2/a4,-(a7)
    move.b -$0001(a4),d1
    bsr.w h0_7680
h0_182A:
    bne.s h0_1866
h0_182C:
    movea.l $016A(a6),a2
    movem.l d1/d3/a3-a5,-(a7)
    bsr.w h0_0B88
h0_1838:
    movem.l (a7)+,d1/d3/a3-a5
    bne.s h0_1866
h0_183E:
    cmpi.b #4,$000D(a1)
    bne.s h0_1866
h0_1846:
    move.b $0009(a1),d0
    move.b $000B(a1),d2
    tst.b $0238(a6)
    beq.s h0_185C
h0_1854:
    btst.b #6,$000C(a1)
    beq.s h0_1866
h0_185C:
    movem.l (a7)+,a0/a2
    movea.l a0,a2
    cmp.b d0,d0
    rts
h0_1866:
    movem.l (a7)+,a2/a4
    move.b -$0001(a4),d1
    moveq.l #-1,d0
    rts
h0_1872:
    tst.b $0119(a6)
    beq.s h0_187E
h0_1878:
    st.b $011A(a6)
    bra.s h0_1882
h0_187E:
    sf.b $011A(a6)
h0_1882:
    bsr.w h0_177E
h0_1886:
    bne.s h0_18A0
h0_1888:
    moveq.l #0,d5
    or.b d2,d5
    tst.b d0
    beq.s h0_189E
h0_1890:
    ori.b #8,d5
    cmpi.b #1,$0239(a6)
    beq.w h0_844A
h0_189E:
    rts
h0_18A0:
    movea.l a4,a2
    cmp.b #$28,d1
    beq.w h0_1A3C
h0_18AA:
    cmp.b #$2D,d1
    beq.w h0_1A78
h0_18B2:
    cmp.b #$23,d1
    beq.w h0_1A9A
h0_18BA:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$43,d1
    beq.s h0_1908
h0_18C6:
    cmp.b #$53,d1
    beq.s h0_18F4
h0_18CC:
    cmp.b #$55,d1
    bne.s h0_192A
h0_18D2:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$53,d1
    bne.s h0_192A
h0_18E0:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$50,d1
    bne.s h0_192A
h0_18EE:
    moveq.l #4,d5
    bra.w h0_1CFE
h0_18F4:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$52,d1
    bne.s h0_192A
h0_1902:
    moveq.l #2,d5
    bra.w h0_1CFE
h0_1908:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$43,d1
    bne.s h0_192A
h0_1916:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$52,d1
    bne.s h0_192A
h0_1924:
    moveq.l #1,d5
    bra.w h0_1CFE
h0_192A:
    movea.l a2,a4
    move.b -$0001(a4),d1
h0_1930:
    bsr.w h0_0DB6
h0_1934:
    cmp.b #$28,d1
    beq.w h0_1B08
h0_193C:
    cmp.b #$2E,d1
    beq.s h0_1988
h0_1942:
    cmp.b #$5C,d1
    beq.s h0_1988
h0_1948:
    tst.b $011C(a6)
    bne.s h0_19A0
h0_194E:
    btst.b #2,$010F(a6)
    beq.s h0_197E
h0_1956:
    movea.w d2,a0
    cmpa.l d2,a0
    bne.s h0_197E
h0_195C:
    tst.b d4
    bne.s h0_197E
h0_1960:
    cmp.b #$1,d3
    beq.s h0_197E
h0_1966:
    bsr.w h0_8DCE
h0_196A:
    bne.s h0_197E
h0_196C:
    move.w d2,(a5)+
    bset #15,d4
    bsr.w h0_19EA
h0_1976:
    moveq.l #56,d5
    moveq.l #14,d0
    bra.w h0_8808
h0_197E:
    tst.b $011A(a6)
    beq.s h0_19C2
h0_1984:
    bra.w h0_1C16
h0_1988:
    move.b (a4),d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b #$4C,d0
    beq.s h0_19B8
h0_1996:
    cmp.b #$57,d0
    bne.s h0_19C2
h0_199C:
    addq.l #1,a4
    move.b (a4)+,d1
h0_19A0:
    moveq.l #56,d5
    tst.b $0238(a6)
    beq.s h0_19B4
h0_19A8:
    bsr.w h0_78B6
h0_19AC:
    bclr #14,d4
    bsr.w h0_19EA
h0_19B4:
    move.w d2,(a5)+
    rts
h0_19B8:
    addq.l #1,a4
    move.b (a4)+,d1
    bclr #15,d4
    bra.s h0_19C6
h0_19C2:
    bset #15,d4
h0_19C6:
    moveq.l #57,d5
    tst.b $0238(a6)
    beq.s h0_19E6
h0_19CE:
    tst.w d3
    bpl.s h0_19D8
h0_19D2:
    jmp h0_98FC.l
h0_19D8:
    bsr.s h0_19EA
h0_19DA:
    cmp.b #$1,d3
    bne.s h0_19E6
h0_19E0:
    jsr h0_9962.l
h0_19E6:
    move.l d2,(a5)+
    rts
h0_19EA:
    tst.b $023B(a6)
    bne.s h0_1A34
h0_19F0:
    cmpi.b #1,$0239(a6)
    beq.s h0_1A04
h0_19F8:
    tst.b $011F(a6)
    beq.s h0_1A04
h0_19FE:
    btst #0,d2
    bne.s h0_1A36
h0_1A04:
    btst #15,d4
    beq.s h0_1A34
h0_1A0A:
    cmp.b #$2,d3
    bne.s h0_1A34
h0_1A10:
    tst.b $011D(a6)
    beq.s h0_1A34
h0_1A16:
    move.w $021C(a6),d0
    cmp.w #$2,d0
    bcs.s h0_1A2E
h0_1A20:
    cmp.w #$4,d0
    bcc.s h0_1A2E
h0_1A26:
    cmp.l #$4,d2
    beq.s h0_1A34
h0_1A2E:
    moveq.l #82,d0
    bsr.w h0_8486
h0_1A34:
    rts
h0_1A36:
    moveq.l #35,d0
    bra.w h0_8486
h0_1A3C:
    move.b (a4)+,d1
    tst.b $0121(a6)
    bne.w h0_4F2A
h0_1A46:
    bsr.w h0_176A
h0_1A4A:
    bne.w h0_192A
h0_1A4E:
    move.b d2,d4
    cmp.b #$29,d1
    beq.s h0_1A66
h0_1A56:
    cmp.b #$2C,d1
    bne.w h0_845E
h0_1A5E:
    clr.l -(a7)
    moveq.l #2,d3
    bra.w h0_1B70
h0_1A66:
    move.b (a4)+,d1
    moveq.l #16,d5
    cmp.b #$2B,d1
    bne.s h0_1A74
h0_1A70:
    moveq.l #24,d5
    move.b (a4)+,d1
h0_1A74:
    or.b d4,d5
    rts
h0_1A78:
    cmpi.b #40,(a4)+
    bne.w h0_192A
h0_1A80:
    move.b (a4)+,d1
    bsr.w h0_176A
h0_1A86:
    bne.w h0_192A
h0_1A8A:
    cmp.b #$29,d1
    bne.w h0_845E
h0_1A92:
    move.b (a4)+,d1
    moveq.l #32,d5
    or.b d2,d5
    rts
h0_1A9A:
    move.b (a4)+,d1
    bsr.w h0_0DB6
h0_1AA0:
    moveq.l #60,d5
    move.b $0239(a6),d0
    beq.s h0_1AD0
h0_1AA8:
    subq.b #1,d0
    beq.s h0_1AE8
h0_1AAC:
    subq.b #1,d0
    beq.s h0_1AD0
h0_1AB0:
    tst.b $0238(a6)
    beq.s h0_1ACC
h0_1AB6:
    tst.w d3
    bpl.s h0_1AC0
h0_1ABA:
    jmp h0_98FC.l
h0_1AC0:
    cmp.b #$1,d3
    bne.s h0_1ACC
h0_1AC6:
    jsr h0_9962.l
h0_1ACC:
    move.l d2,(a5)+
    rts
h0_1AD0:
    tst.b $0238(a6)
    beq.s h0_1AE4
h0_1AD6:
    tst.w d3
    bpl.s h0_1AE0
h0_1ADA:
    jmp h0_9938.l
h0_1AE0:
    bsr.w h0_789C
h0_1AE4:
    move.w d2,(a5)+
    rts
h0_1AE8:
    tst.b $0238(a6)
    beq.s h0_1AE4
h0_1AEE:
    tst.w d3
    bmi.s h0_1AFE
h0_1AF2:
    bsr.w h0_788C
h0_1AF6:
    andi.w #255,d2
    move.w d2,(a5)+
    rts
h0_1AFE:
    move.b #$0,(a5)+
    jmp h0_9954.l
h0_1B08:
    move.b (a4)+,d1
    move.l d2,-(a7)
    bsr.w h0_177E
h0_1B10:
    bne.w h0_1BEC
h0_1B14:
    bsr.w h0_176E
h0_1B18:
    cmp.b #$29,d1
    bne.s h0_1B68
h0_1B1E:
    btst.b #1,$010F(a6)
    beq.s h0_1B4A
h0_1B26:
    tst.b d4
    bne.s h0_1B4A
h0_1B2A:
    tst.l (a7)
    bne.s h0_1B4A
h0_1B2E:
    moveq.l #16,d5
    or.b d2,d5
    move.l (a7)+,d2
    bsr.w h0_8DCE
h0_1B38:
    bne.s h0_1B42
h0_1B3A:
    move.b (a4)+,d1
    moveq.l #13,d0
    bra.w h0_8808
h0_1B42:
    move.l d2,-(a7)
    move.b d5,d2
    andi.b #7,d2
h0_1B4A:
    moveq.l #40,d5
    or.b d2,d5
    move.l (a7)+,d2
    move.b (a4)+,d1
    tst.w d3
    bpl.s h0_1B5C
h0_1B56:
    jmp h0_991C.l
h0_1B5C:
    move.w d2,(a5)+
    tst.b $0238(a6)
    bne.w h0_78B6
h0_1B66:
    rts
h0_1B68:
    cmp.b #$2C,d1
    bne.w h0_8462
h0_1B70:
    moveq.l #48,d5
    or.b d2,d5
    move.b (a4)+,d1
    bsr.w h0_177E
h0_1B7A:
    bne.w h0_845E
h0_1B7E:
    lsl.b #3,d0
    or.b d2,d0
    lsl.b #4,d0
    swap.w d3
    move.b d0,d3
    move.l (a7)+,d2
    cmp.b #$2E,d1
    beq.s h0_1B96
h0_1B90:
    cmp.b #$5C,d1
    bne.s h0_1BB2
h0_1B96:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s h0_1BB0
h0_1BA4:
    cmp.b #$4C,d1
    bne.w h0_8466
h0_1BAC:
    ori.b #8,d3
h0_1BB0:
    move.b (a4)+,d1
h0_1BB2:
    tst.b $0121(a6)
    beq.s h0_1BC8
h0_1BB8:
    cmp.b #$2A,d1
    bne.s h0_1BC8
h0_1BBE:
    move.b (a4)+,d1
    bsr.w h0_5740
h0_1BC4:
    add.b d0,d0
    or.b d0,d3
h0_1BC8:
    cmp.b #$29,d1
    bne.w h0_0FB2
h0_1BD0:
    move.b (a4)+,d1
    move.b d3,(a5)+
    swap.w d3
    tst.w d3
    bpl.s h0_1BE0
h0_1BDA:
    jmp h0_9946.l
h0_1BE0:
    move.b d2,(a5)+
    tst.b $0238(a6)
    bne.w h0_78B0
h0_1BEA:
    rts
h0_1BEC:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$50,d1
    bne.w h0_845E
h0_1BFA:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$43,d1
    bne.w h0_845E
h0_1C0A:
    move.l (a7)+,d2
    move.b (a4)+,d1
    cmp.b #$29,d1
    bne.s h0_1C58
h0_1C14:
    move.b (a4)+,d1
h0_1C16:
    moveq.l #58,d5
    tst.b $0238(a6)
    beq.s h0_1C54
h0_1C1E:
    tst.w d3
    bpl.s h0_1C28
h0_1C22:
    jmp h0_98EE.l
h0_1C28:
    cmp.b #$2,d3
    beq.s h0_1C48
h0_1C2E:
    bclr #15,d4
    bsr.w h0_19EA
h0_1C36:
    sub.l $023C(a6),d2
    move.l a5,d0
    sub.l $024C(a6),d0
    sub.l d0,d2
    move.w d2,(a5)+
    bra.w h0_78BC
h0_1C48:
    tst.b $0107(a6)
    bne.s h0_1C2E
h0_1C4E:
    moveq.l #33,d0
    bsr.w h0_8486
h0_1C54:
    move.w d2,(a5)+
    rts
h0_1C58:
    cmp.b #$2C,d1
    bne.w h0_845E
h0_1C60:
    moveq.l #59,d5
    move.l d2,-(a7)
    move.b (a4)+,d1
    bsr.w h0_177E
h0_1C6A:
    bne.w h0_845E
h0_1C6E:
    lsl.b #3,d0
    or.b d2,d0
    lsl.b #4,d0
    move.b d0,d4
    cmp.b #$2E,d1
    beq.s h0_1C82
h0_1C7C:
    cmp.b #$5C,d1
    bne.s h0_1C9E
h0_1C82:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s h0_1C9C
h0_1C90:
    cmp.b #$4C,d1
    bne.w h0_8466
h0_1C98:
    ori.b #8,d4
h0_1C9C:
    move.b (a4)+,d1
h0_1C9E:
    move.l (a7)+,d2
    tst.b $0121(a6)
    beq.s h0_1CB6
h0_1CA6:
    cmp.b #$2A,d1
    bne.s h0_1CB6
h0_1CAC:
    move.b (a4)+,d1
    bsr.w h0_5740
h0_1CB2:
    add.b d0,d0
    or.b d0,d4
h0_1CB6:
    move.b d4,(a5)+
    tst.b $0238(a6)
    beq.s h0_1CF0
h0_1CBE:
    tst.w d3
    bmi.s h0_1CE2
h0_1CC2:
    tst.b $0107(a6)
    bne.s h0_1CCE
h0_1CC8:
    cmp.b #$2,d3
    beq.s h0_1CEA
h0_1CCE:
    sub.l $023C(a6),d2
    move.l a5,d0
    sub.l $024C(a6),d0
    sub.l d0,d2
    addq.l #1,d2
    bsr.w h0_78B0
h0_1CE0:
    bra.s h0_1CF0
h0_1CE2:
    jsr h0_98E0.l
h0_1CE8:
    bra.s h0_1CF2
h0_1CEA:
    moveq.l #33,d0
    bsr.w h0_8486
h0_1CF0:
    move.b d2,(a5)+
h0_1CF2:
    cmp.b #$29,d1
    bne.w h0_0FB2
h0_1CFA:
    move.b (a4)+,d1
    rts
h0_1CFE:
    moveq.l #0,d1
    move.b (a4)+,d1
    movea.l #dat_A764,a1
    tst.b $0(a1,d1.w)
    beq.w h0_192A
h0_1D10:
    bset #6,d5
h0_1D14:
    rts
    DC.B    $61,$00,$32,$02,$60,$04 ; VIOLATION: orphaned code island at $1D16 is not reached from known entrypoints
    DC.L    $61000654,$6100fb5c,$10050240,$0078670c,$b03c0020,$6600fa10,$00060008,$02450007
    DC.L    $8c45b23c,$002c6600,$671e121c,$3f006100,$fb321005,$02400078,$b05f6600,$f9ea0245
    DC.L    $0007ee5d,$8c453ac6,$4e75121c,$6100f04c,$b23c002c,$66644a04,$6660b63c,$0002665a
    DC.L    $b4bc0000,$00096466,$4a826f62,$558d6100 ; VIOLATION: orphaned code island at $1D1C is not reached from known entrypoints
    DC.B    "pBfD"
    DC.L    $02464000,$0846000e,$ec4e0046,$50006100,$317ab43c,$00086602,$7400ee5a,$8c42121c
    DC.L    $6100f934,$003f4a2e,$0238670e,$7000102e,$0239103b,$000cd16e,$01947010,$60006a3a
    DC.L    $02020204,$548d121c,$6100fcc6,$600000be,$0806000e,$66f04482,$60ec082e,$0001010e
    DC.L    $67e40806,$000e6602,$44823042,$b1c266e0,$48e72200,$b23c002c,$66006658,$121c6100
    DC.L    $310a48e7,$40086100,$f9666600,$00424a00,$6700003c,$558d6100,$6fa66630,$504f6100
    DC.L    $fa5c4882,$3c3c41e8,$8c42ee5a,$8c423ac6,$4cdf0044,$3ac27000,$0c2e0003,$02396602
    DC.L    $7002d16e,$01947015,$600069ae,$544d4cdf,$10024cdf,$00440806,$000e6602,$44826000
    DC.L    $ff68548d,$b23c0023,$6614082e,$0004010f,$6600fee4,$082e0001,$010e6600,$feda6100
    DC.L    $f9e2b23c,$002c6600,$65ca121c,$3f056100,$f9de381f,$206e024c,$14050202,$0078b43c
    DC.L    $00086700,$004cb83c,$003c6730,$6100305c,$30864a02,$6610da05,$8b18b83c,$00406400
    DC.L    $f8728910,$4e751004,$02000078,$6600f864,$d8045204,$89188b10,$703c6010,$ea5e0246
    DC.L    $07006100,$30268c05,$3086703d,$6000f80c,$000600c0,$8c040245,$0007ee5d,$8c450c2e
    DC.L    $00030239,$660408c6,$00083086,$3a04ba3c,$00406400,$f81e0c2e,$00010239,$6700651c
    DC.L    $4e750c2e,$00030239,$66040046,$01006100,$f7a600ff,$48e71800,$b23c002c,$66006514
    DC.L    $121c6100,$f8164cdf,$00186600,$f816d402,$206e024c,$851061be,$082e0003,$010e6742
    DC.L    $4a04663e,$b63c0002,$66383610,$024301ff,$b67c01fc
    DC.B    "f, (",0
    DC.B    $02,$32,$40
    DC.L    $b0896622,$48e78080,$2400554d,$61006e34,$4cdf0101,$660e0890,$00003140,$00027017
    DC.L    $6000685a
    DC.B    "TMNua",0
    DC.B    $2f,$64
    DC.L    $3ac6b23c,$00236600,$64aa121c,$6100fad6,$b23c002c,$66006494,$121c6100,$f70c003d
    DC.L    $4e750c2e,$00140121,$6dd26100,$2f363ac6,$b23c0023,$6600647c,$121c6100,$faa8b23c
    DC.L    $002c6600,$6466121c,$6100f6de,$007d4e75,$102e0239,$670000bc,$b03c0001,$674eb03c
    DC.L    $00026700,$00944a2e,$01246600,$008c0c2e,$00140121,$6d2e50c6,$3ac66100,$f6744a2e
    DC.L    $0238671c,$4a046618,$b63c0002,$660c4a2e,$01076606,$701e6100,$643694ae,$023c5582
    DC.L    $2ac24e75,$70056100
    DC.B    "e,`La",0
    DC.B    $00,$ca
    DC.L    $672ee04e,$1ac64a43,$6b00786e,$4a826630,$bc3c0061,$6720082e,$0006010f,$66087053
    DC.L    $610063fc,$60067012,$61006776,$2a6e024c,$3afc4e71,$4e751afc,$00ff703f,$600063e0
    DC.L    $61005806,$1ac24e75,$6100007e
h0_20B4:
    beq.s h0_20C6
h0_20B6:
    move.w d6,(a5)+
    tst.w d3
    bmi.w h0_98EE
h0_20BE:
    bsr.w h0_78BC
h0_20C2:
    move.w d2,(a5)+
    rts
h0_20C6:
    addq.l #4,a5
    rts
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $20CA is not reached from known entrypoints
    DC.L    $012c6b94,$6600ff54,$082e0000,$010f67d4,$6100ecd8,$4a046646,$4a2e0107,$6606b63c
    DC.L    $0002673a,$2f0294ae,$023c5982,$672e6a02,$54821002,$488048c0,$b4806620,$61006cc4
    DC.L    $660c588f,$8c023ac6,$700c6000
    DC.B    $66,$f0
    DC.B    $08,$2e ; VIOLATION: orphaned code island at $211A is not reached from known entrypoints
    DC.L    $0005010f,$67067011,$610066e2,$241f487a,$ff886004
    DC.L    $6100ec84,$4a2e0238,$66104a04,$662eb63c,$00026628,$4a2e0107 ; VIOLATION: orphaned code island at $2130 is not reached from known entrypoints
    DC.B    "f",$22,"JCk"
    DC.B    $1e,$4a,$2e
    DC.L    $01076606,$b63c0002,$67180802,$00006706,$70236100,$632294ae,$023c5582,$4a2e0238
    DC.B    $4e,$75
    DC.B    $70,$21,$61,$00,$63,$10,$4a,$2e,$02,$38,$4e,$75 ; VIOLATION: orphaned code island at $2172 is not reached from known entrypoints
    DC.B    $b2,$3c ; VIOLATION: orphaned code island at $217E is not reached from known entrypoints
    DC.L    $00236600,$62e6121c,$6100f542,$4a826b0e,$b4bc0000,$00086406,$8c023ac6
    DC.B    $4e,$75
    DC.B    $3a,$c6,$70,$1d,$60,$00,$62,$e2 ; VIOLATION: orphaned code island at $219E is not reached from known entrypoints
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $21A6 is not reached from known entrypoints
    DC.L    $00140121,$6d000f84,$0c2e0020,$01216700,$0f7a4a2e,$02396600,$628a6100,$f59c0242
    DC.L    $00ffe85a,$3a02b23c,$002c6600,$628e121c
    DC.B    "a~ n"
    DC.L    $024c3145,$00024e75
    DC.L    $0c2e0014,$01216d00,$0f460c2e,$00200121,$67000f3c,$4a2e0239,$6600624c,$3ac6548d
    DC.L    $6100f4da,$00657a00,$6158b23c,$002c6600,$624e121c,$6100f546,$024200ff,$e85a8a42
    DC.L    $206e024c,$31450002 ; VIOLATION: orphaned code island at $21E4 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $222E is not reached from known entrypoints
    DC.L    $00140121,$6d000efc,$0c2e0020,$01216700,$0ef24a2e,$02396600,$62027a00,$610a206e
    DC.L    $024c3145,$00024e75
    DC.L    $3ac6548d,$3f056100,$f4800025,$3a1fb23c,$007b661a,$121c6100,$f50e6618,$4a00660e
    DC.L    $08c5000b,$024200ff,$ed4a8a42 ; VIOLATION: orphaned code island at $2258 is not reached from known entrypoints
    DC.B    $60,$28
    DC.B    $70,$55,$60,$00,$61,$f8 ; VIOLATION: orphaned code island at $2286 is not reached from known entrypoints
    DC.L    $6100f43e,$4a2e0238,$67184a82,$6b08b4bc,$00000020,$65046100,$5622ed4a,$024207c0
    DC.L    $8a42b23c,$003a66d2,$121c6100,$f4c6660c,$4a0066c6,$08c50005,$8a026022 ; VIOLATION: orphaned code island at $228C is not reached from known entrypoints
    DC.L    $6100f402,$4a2e0238,$67184a82,$66064a2e,$0120660e,$6f16b4bc,$00000020,$67046e0c
    DC.L    $8a42b23c,$007d6696,$121c4e75 ; VIOLATION: orphaned code island at $22C8 is not reached from known entrypoints
    DC.L    $610055d0,$60f050ee,$023bb23c,$00236722,$6100f45a,$2f0cb23c,$002c6600,$6152121c
    DC.L    $d4025202,$42671ac2,$1ac66100,$f3c000fd,$60203ac6,$121c6100,$ea8a2f0c,$3f026100
    DC.L    $f7b4b23c,$002c6600,$6126121c,$6100f39e,$007d341f,$245f0245,$00386606,$70036000
    DC.L    $0c9eb47c,$00086516,$4a2e011e,$6710284a,$6a06706a,$6000611c,$70096100,$621c7001
    DC.L    $60000c7c,$50ee023b,$b23c0023,$67226100,$f3dc2f0c,$b23c002c,$660060d4,$121cd402
    DC.L    $52024267,$1ac21ac6,$6100f342,$003d60a2,$3ac6121c,$6100ea0c,$2f0c3f02,$6100f736
    DC.L    $b23c002c,$660060a8,$121c6100,$f320003d,$60800c2e,$00140121,$66000d64,$4a2e0239
    DC.L    $67046100,$6072b23c,$00236600,$608a121c,$3ac66100,$e9ce6100,$f6fcb23c,$002c6600
    DC.L    $606e121c,$6100f2e6,$00644e75,$0c2e0014,$01216d00,$0d2a0c2e,$00200121,$67000d20
    DC.L    $7000102e,$0239d040,$8c7b0036,$6100f33e,$7a001a02,$b23c002c,$66006034,$121c6100
    DC.L    $f32c0242,$00ffed4a,$8a42b23c,$002c6600,$601e121c,$3f056100,$f29a003c,$3adf4e75
    DC.L    $04000200,$04000600,$70566000,$60220c2e,$00140121,$6d000cc8,$0c2e0020,$01216700
    DC.L    $0cbe7000,$102e0239,$b03c0001,$67005fc8,$b03c0003,$660408c6,$00093ac6,$7a007c00
    DC.L    $6100f2ca,$8a02b23c,$003a66bc,$121c6100,$f2bc8c02,$b23c002c,$66005fb4,$121c6130
    DC.L    $8a42b23c,$003a66a0,$121c6100,$00248c42,$b23c002c,$66005f98,$121c6120,$8a42b23c
    DC.L    $003a6684,$121c6114,$8c423ac5,$3ac64e75,$6100f27a,$024200ff,$ed4a4e75,$b23c0028
    DC.L    $6620121c,$6100f284,$66180242,$00ff4a00,$67040002,$0008e85a,$b23c0029,$6604121c
    DC.L    $4e756000,$5f1a7e04,$b23c0023,$6612121c,$6100f1a6,$2e02b23c,$002c6600,$5f32121c
    DC.L    $b23c0009,$675cb23c,$00206756,$b23c000a,$675041ee,$046e6100,$516c6600,$5ee27c02
    DC.L    $b23c002e,$6620121c,$48811236,$107eb23c,$00426714,$b23c0057,$670e7c04,$b23c004c
    DC.L    $66005ed4,$6002538c,$121c2807,$de8648e7,$41006110,$4cdf0082,$b23c002c,$6604121c
    DC.L    $60b04e75,$4a2e0238,$662a6100,$e62e6700,$5e927602,$10280006,$b02e0116,$670845ee
    DC.L    $016a6000,$e6fe45ee,$015a4a92,$6600e78a,$60005e7c,$6100e604,$66005e6c,$08e90006
    DC.L    $000c6600,$5e5e0c29,$0002000d,$66005e54,$b8a90008,$66005e54,$4e750c2e,$00140121
    DC.L    $6d000158,$102e0239,$6712b03c,$0002670c,$b03c0003,$66005e40,$08860007,$6100f0d4
    DC.L    $00fdb23c,$002c6600,$5e46121c,$6100f13e,$206e024c,$d4028510,$4e750c2e,$00140121
    DC.L    $6d000afc,$3a060886,$000b7000,$102e0239,$d0408c7b,$002a3ac6,$02450800,$3ac56100
    DC.L    $f08c0064,$b23c002c,$66005e04,$121c6100,$23d8e902,$206e024c,$85280002,$4e750200
    DC.L    $00000200,$04007a00,$60043a3c,$08000c2e,$00140121,$6d000aa8,$6100fcc2,$3ac63ac5
    DC.L    $6100f04a,$00fdb23c,$002c6600,$5dc2121c,$6100f0ba,$206e024c,$b23c003a,$6616121c
    DC.L    $85280003,$6100f0a6,$206e024c,$e90a8528,$00024e75,$70256000,$5dba0c2e,$00140121
    DC.L    $6d78102e,$02396772,$b03c0002,$676cb03c,$00036600,$5d620806,$000856c5,$48850245
    DC.L    $08000806,$000e57c6,$48860246,$00400046,$4c003ac6,$3ac56100,$efd400fd,$b23c002c
    DC.L    $66005d4c,$121c6100,$f044206e,$024cb23c,$003a670c,$85280003,$e90a8528,$00024e75
    DC.L    $121c8528,$00036100,$f024206e,$024ce90a,$08c20002,$85280002,$4e756100,$ef9600fd
    DC.L    $b23c002c,$66005d08,$121c6100,$f000206e,$024cd402,$85107002,$60000884,$610027a8
    DC.L    $3ac66100,$f0fab23c,$002c6600,$5ce2121c,$3f056100,$f0f6381f,$206e024c,$30050200
    DC.L    $0078674a,$b03c0008,$6754b83c,$003c6774,$10040200,$0078b03c,$0018662e,$10050200
    DC.L    $0078b03c,$00186622,$3c3cb108,$61002758,$10040200,$00078c00,$10050240,$0007ee58
    DC.L    $8c40206e,$024c3086,$4e756000,$ef62da05,$8b103a04,$8b50303c,$00ff6000,$ef1a0205
    DC.L    $0007da05,$0c2e0003,$02396602,$52058b10,$3a040044,$00c08950,$303c00ff,$6100eef8
    DC.L    $6000f710,$3c3c0c00,$610026fc,$8c453086,$703d6000,$eee26100,$26ee6116,$8c05b23c
    DC.L    $002c6600,$5c2a121c,$6108ee5d,$8c453ac6,$4e756100,$f0361005,$02000078,$b03c0018
    DC.L    $6600eeec,$02450007,$4e756100,$4272b23c,$002c6600,$5bfa121c,$2a026100,$42622002
    DC.L    $67186b3c,$2f02242e,$023c2017,$6100e930,$241f4a80,$67049082,$4480d085,$28006710
    DC.L    $b0bc0000,$00806418,$1afc0000,$530066f8,$d8ae023c,$41ee03e8,$4a906600,$e3d44e75
    DC.L    $701d6000,$5bce43ec,$ffffb23c,$000a671a,$121cb23c,$000a66f8,$240c9489 ; VIOLATION: orphaned code island at $22F4 is not reached from known entrypoints
    DC.B    "SBJ."
    DC.L    $02386706,$61006e12,$720a4e75,$6100ee7e,$8c02b23c,$002c6600,$5b76121c,$6100fe78
    DC.L    $6000f7ba,$3f01102e,$02396706,$b03c0001,$67106100,$e35c102e,$02396602,$7002321f
    DC.L    $4e7541ee,$03e84a90,$6708282e,$023c6100,$e360102e,$023960e6,$61ca6100,$41a2b23c
    DC.L    $002c6706,$2f027400,$6008121c,$2f026100,$418e7600,$41fa018e,$2202162e,$02391630
    DC.L    $3000281f,$42ae0182,$4a2e0103,$67064a2e,$02386616,$e7ac6a00,$00087054,$60005b10
    DC.L    $2d44018e,$122cffff,$4e751d7c,$00ff083b,$2d6e023c,$083c6100,$6da267d8,$42ae018e
    DC.L    $538465e0,$487affde,$5303652a,$67142ac1,$7a046136,$51ccfff8,$04840001,$000064ee
    DC.L    $4e753ac1,$7a026122,$51ccfff8,$04840001,$000064ee,$4e751ac1,$7a01610e,$51ccfff8
    DC.L    $04840001,$000064ee,$4e752f01,$2205242e,$023cd4ae,$018e6100,$6d22dbae,$018e221f
    DC.L    $2a6e024c,$4e756100,$fefcb03c,$00016700,$005eb03c,$0003671a,$b03c0002,$67086100
    DC.L    $3102611a,$60f86100,$e39a6100,$f0b0610e,$60f46100,$e38e6100,$f0846102,$60f4b23c
    DC.L    $002c6626,$121cb23c,$00096708,$b23c0020,$67024e75,$700b6100,$5b40121c,$b23c0009
    DC.L    $67f8b23c,$002067f2,$4e75588f,$4e75b23c,$00276724,$b23c0022,$671e6100,$e3464a2e
    DC.L    $02386708,$4a436b0a,$61004e0e,$1ac261ae,$60dc6100,$6ecc60f6,$160148e7,$000c121c
    DC.L    $b23c000a,$6736b203,$6606121c,$b6016604,$1ac160ea,$b23c000a,$671ab23c,$00096714
    DC.L    $b23c0020,$670eb23c,$002c6708,$4cdf3000,$120360a6,$508f6100,$ff666092,$508f7037
    DC.L    $600059b0,$01000102,$6100fe1a,$48801c3b,$00f46100,$3fea4a82,$670a2802,$16067200
    DC.L    $6000fe62,$4e7550ee,$0115720a,$4e7541ee,$03e84a90,$67024e75,$70296000,$597261ee
    DC.L    $4a2e0238,$66302f08,$61003f94,$205f48e7,$30006100,$e0a64cdf,$00306700,$59061605
    DC.L    $487a0044,$45ee016a,$55056700,$e17645ee,$01626000,$e16e6100,$e0826600,$58fe0829
    DC.L    $0006000c,$660058dc,$2f096100,$eb48225f,$b4a90008,$660058d4,$b629000d,$660058c4
    DC.L    $08e90006,$000c122c,$ffff1d7c,$003d083b,$2d42083c
    DC.B    "Nup-`",0
    DC.B    $58,$f8
    DC.L    $702e6000,$58f26100,$ff6a6100,$ebe266f0,$48423400,$48420282,$00ff00ff,$246e016a
    DC.L    $41ee03e8,$48e7201c,$4a2e0238,$66166100
h0_2BC0:
    adda.l a0,a7
    movem.l (a7)+,d4/a3-a5
    beq.w h0_8436
h0_2BCA:
    moveq.l #4,d3
    bsr.w h0_0CBA
h0_2BD0:
    moveq.l #10,d1
    rts
    DC.L    $6100dfb2,$4cdf3810,$6600585c,$0c290004,$000d6600,$584eb8a9,$00086600,$584608e9
    DC.L    $0006000c,$6600583c,$720a4e75 ; VIOLATION: orphaned code island at $2BD4 is not reached from known entrypoints
    DC.B    $4a,$2e,$02,$39,$66,$00,$58,$44,$32,$3c,$00,$0a,$4e,$75 ; VIOLATION: orphaned code island at $2C00 is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $2C0E is not reached from known entrypoints
    DC.L    $f7406100,$eb6a6644,$b23c002c,$66005844,$121c48a7,$a0006100,$eb564c9f,$0018662c
    DC.L    $b6006718,$00060088,$4a036702,$c9428c02,$02440007,$ee5c8c44,$3ac64e75
    DC.B    $00,$06,$00,$40,$4a,$00,$67,$ea,$00,$06,$00,$08,$c9,$42,$60,$e2 ; VIOLATION: orphaned code island at $2C4C is not reached from known entrypoints
    DC.B    $54,$8d,$70,$2e,$60,$00,$58,$24 ; VIOLATION: orphaned code island at $2C5C is not reached from known entrypoints
    DC.L    $6100f2c0,$0c2e0003,$02396604,$00060040,$6100eaea,$8c023ac6 ; VIOLATION: orphaned code island at $2C64 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $0c,$2e,$00,$14,$01,$21,$6d,$00,$04,$ac,$61,$00,$f6,$c6 ; VIOLATION: orphaned code island at $2C7E is not reached from known entrypoints
h0_2C8C:
    bsr.w h0_1760
h0_2C90:
    or.b d2,d6
    move.w d6,(a5)+
    rts
    DC.B    $10,$2e,$02,$39,$67,$f0,$b0,$3c,$00,$02,$67,$ea ; VIOLATION: orphaned code island at $2C96 is not reached from known entrypoints
h0_2CA2:
    cmp.b #$3,d0
    bne.w h0_844A
h0_2CAA:
    bset #6,d6
    bra.s h0_2C8C
    DC.B    $72,$0a,$70,$38,$60,$00,$57,$d0 ; VIOLATION: orphaned code island at $2CB0 is not reached from known entrypoints
    DC.L    $41ee0c24,$b23c000a,$673cb23c,$00096736,$b23c0020,$67300401,$0030652c,$b23c0008
    DC.L    $64267007,$9001121c,$b23c002b,$670ab23c,$002d6614,$01906002 ; VIOLATION: orphaned code island at $2CB8 is not reached from known entrypoints
    DC.L    $01d0121c,$b23c002c,$6604121c,$60be4e75,$704c6000,$57826100,$3dca4a82,$6700df36
    DC.L    $b23c0009,$6706b23c,$00206604,$121c60f0,$6100dd16,$41fa0008,$2d48017a,$720a4e75
    DC.L    $4a2e011b,$66005724,$41ee03e8,$76006100,$4ad841ee,$03ee422e,$010a4eb9 ; VIOLATION: orphaned code island at $2CF0 is not reached from known entrypoints
    DC.L    h0_AFDE
    DC.L    $66000086,$2d43018a,$2d42018e,$6768b4bc,$ffffffff
    DC.B    "f* n"
    DC.L    $01a22228,$000c2068,$00089288,$2d41018e,$4a2e0238
    DC.B    "gHJ."
    DC.L    $01036742,$242e023c,$610069e8,$60000038,$4a2e0238
    DC.B    "g0J."
    DC.L    $0103672a,$22026100,$631a2f08,$222e018e,$262e018a
    DC.B    $4e,$b9
    DC.L    h0_DOSRead_AFF6
    DC.B    $22,$2e
    DC.L    $018e2057,$242e023c,$610069b4,$205f6100,$630a262e,$018a42ae,$018a4eb9
    DC.L    h0_AFF2
    DC.L    $720a4e75,$701a6000,$56aa47ee,$083250ee,$012b6000,$18b041ee,$03e8760b,$61004a26
    DC.L    $50ee010a,$61005a5c,$66005670,$720a4e75,$6100e8e0,$00644a2e,$02396600
    DC.B    "V:NuP"
    DC.B    $ee,$02,$3b
    DC.L    $6100e8cc,$006451ee,$023bb23c,$002c6600,$563a48e7,$1800121c,$6100e94c,$4cdf0018
    DC.L    $6600e938,$4a006700,$e932206e,$024cd402,$85106100,$f504082e,$0002010e,$676a4a04
    DC.L    $6666b63c,$00026660,$36100243,$0038b63c,$00286654,$30280002,$674eb07c,$00086e48
    DC.L    $b07cfff8,$6d423610,$02430007,$d643b403,$663648e7,$80802400,$554d6100,$5f3a4cdf
    DC.L    $01016622,$e24b4a40,$6a0608c3,$00084440,$02400007,$ee588640,$00435048,$30837016
    DC.L    $6000594e
    DC.B    "NuTMNu"
    DC.B    $0c,$2e
    DC.L    $00140121,$6d48102e,$0239674a,$b03c0002,$6744b03c,$00036600
    DC.B    "Un<<H"
    DC.B    $08,$61,$00
    DC.L    $e8868c02,$3ac6b23c,$002c6600,$5572121c,$b23c0023,$66005570,$121c6100,$deb66100
    DC.L    $ebac0802,$0000663e,$4a826e3a
    DC.B    "NuJ."
    DC.L    $02396600,$55326100,$e84e8c02,$3ac6b23c,$002c6600,$553a121c,$b23c0023,$66005538
    DC.L    $121c6100,$de7e6100,$eb940802,$00006606,$4a426e02,$4e757003,$6000563e,$121c6100
    DC.L    $e7786100
    DC.B    "I4J."
    DC.L    $02386710,$4a2e0955,$670a3f01,$12026100,$6210321f,$b23c002c,$67da50ee,$01134e75
    DC.L    $61003b54,$b4bc0000,$00266500,$188cb4bc,$000000ff,$64001882,$3d420b62,$50ee0113
    DC.L    $4e75b23c,$00236600,$54c6121c,$61001f70,$3ac66100,$eaecb23c,$002c6600,$54aa121c
    DC.L    $6100e722,$033d4e75,$206e024c,$52885305,$67144a2e,$01256706,$70656100,$54ae10bc
    DC.L    $007c7002,$601010fc,$003c0c2e,$00030239,$6700545c,$4e75b02e,$0239670c,$4a2e0239
    DC.L    $6600544c,$1d400239,$4e75121c,$30063c3c,$0200b07c,$c0006794,$7c00b07c,$8000678c
    DC.L    $3c3c0a00,$6086b23c,$002367de,$61001ef0,$3ac66100,$e842b23c,$002c6600,$542a121c
    DC.L    $10050200,$00786600,$0042da05,$52058b2d,$fffe6100,$e82e206e,$024c303c,$003c1405
    DC.L    $02020078,$661e303c,$00fd0806,$000d6614,$1010e208,$02400007,$8150da05,$0250f0ff
    DC.L    $8b104e75,$8b506000,$e6860806,$000d6600,$e6b6303c,$00fd6100,$e6706100,$e6c8206e
    DC.L    $024cd402,$85104e75,$224c41fa,$00ba4881,$1236107e,$b2186600,$0090121c,$4a1066ee
    DC.L    $04010030,$6570b23c,$000a646a,$74001401,$c4fc000a,$121c0401,$0030655a,$b23c000a
    DC.L    $64544881,$d441121c,$c4fc000a,$04010030,$6544b23c,$000a643e,$4881d441,$121c4a42
    DC.L    $673cb47c,$00086734,$b47c000a,$6730b47c,$0014672a,$b47c001e,$6724b47c,$014c6742
    DC.L    $b47c0028,$6706b47c,$003c660a,$1d420121,$50ee0122
    DC.B    $4e,$75
h0_3132:
    moveq.l #34,d0
    bra.w h0_8486
    DC.B    $74,$00,$1d,$42,$01,$21,$51,$ee,$01,$22,$4e,$75 ; VIOLATION: orphaned code island at $3138 is not reached from known entrypoints
    DC.L    $2849122c,$ffff41fa,$001b4881,$1236107e,$b21866da,$121c4a10,$66f07420,$60d84d43
    DC.L    $36380043 ; VIOLATION: orphaned code island at $3144 is not reached from known entrypoints
    DC.B    "PU32",0
    DC.B    $00
h0_316E:
    moveq.l #0,d2
h0_3170:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.s h0_3194
h0_3178:
    cmp.b #$3A,d1
    bcc.s h0_3194
h0_317E:
    subi.b #48,d1
    ext.w d1
    ext.l d1
    add.l d2,d2
    move.l d2,d0
    add.l d2,d2
    add.l d2,d2
    add.l d0,d2
    add.l d1,d2
    bra.s h0_3170
h0_3194:
    subi.l #68000,d2
    bcs.s h0_31E2
    beq.s h0_3204
    cmp.l #$384,d2
    bgt.s h0_31E2
    cmp.w #$8,d2
    beq.s h0_3204
    cmp.w #$A,d2
    beq.s h0_3204
    cmp.w #$14,d2
    beq.s h0_3204
    cmp.w #$1E,d2
    beq.s h0_3204
    cmp.w #$14C,d2
    beq.s h0_31E4
    cmp.w #$28,d2
    beq.s h0_31FE
    cmp.w #$3C,d2
    beq.s h0_31FE
    cmp.w #$371,d2
    beq.s h0_31F6
    cmp.w #$372,d2
    beq.s h0_31EE
    cmp.w #$353,d2
    beq.s h0_31E8
h0_31E2:
    rts
h0_31E4:
    DC.L    $7420601c ; VIOLATION: orphaned code island at $31E4 is not reached from known entrypoints
h0_31E8:
    DC.B    $50,$ee,$01,$23,$60,$1e ; VIOLATION: orphaned code island at $31E8 is not reached from known entrypoints
h0_31EE:
    DC.B    $1d,$7c,$00,$52,$01,$22,$60,$16 ; VIOLATION: orphaned code island at $31EE is not reached from known entrypoints
h0_31F6:
    DC.B    $1d,$7c,$00,$51,$01,$22,$60,$0e ; VIOLATION: orphaned code island at $31F6 is not reached from known entrypoints
h0_31FE:
    DC.B    $50,$ee,$01,$22,$60,$04 ; VIOLATION: orphaned code island at $31FE is not reached from known entrypoints
h0_3204:
    DC.L    $51ee0122,$1d420121,$b23c002f,$6700ff5c,$70004e75,$61001d00,$b23c0023,$66005248
    DC.L    $121c6100,$e4a46116,$ee5a8c42,$b23c002c,$6600522c,$121c6100,$e4aa003f ; VIOLATION: orphaned code island at $3204 is not reached from known entrypoints
    DC.B    "NuJ."
    DC.L    $02386710,$4a82670e,$b4bc0000,$0008620c,$66027400
    DC.B    "NuJ."
    DC.L    $012066f8,$701d6000,$52226100,$1b9e342e,$021cb47c,$00036720,$08020001,$6622b47c
    DC.L    $0005671c,$4a426612,$61004754,$204c122c,$ffff6100,$4658720a,$4e757006,$600052f2
    DC.L    $45ee01ae,$61001b0c,$51ee0113,$4e75121c,$6100db08,$4a046600,$0082b63c,$0002667a
    DC.L    $b23c002c,$66742802,$2f0c121c,$6100e4b4,$66624a00,$66302004,$488048c0,$b8806654
    DC.L    $082e0003,$010f6700,$004c558d,$61005ae4,$6640588f,$00020038,$d402e14a,$84043ac2
    DC.L    $700f6000,$55083044,$b8886628,$082e0003,$010e6700,$0020558d,$61005ab8,$6614588f
    DC.L    $d402e14a,$0042307c,$3ac23ac4,$70176000,$54dc548d
    DC.B    "(_r,$"
    DC.B    $04,$61,$00
    DC.L    $e768603a,$30001000,$30002000,$7000102e,$0239d000,$8c7b00ee,$3ac6b03c,$0006661a
    DC.L    $b23c0023,$6614082e,$0003010f,$6600ff44,$082e0003,$010e6600,$ff3a6100,$e4feb23c
    DC.L    $002c6600,$50e6121c,$08050006,$660000ac,$206e024c,$8b506100,$e4ee206e,$024c0805
    DC.L    $00066626,$34053005,$02000007,$d0008110,$02450038,$da45da45,$da458b50,$0242003f
    DC.L    $b47c003a,$6400e384,$4e753810,$e20d652c,$e20d6550,$4a2e0125,$67067065,$610050b0
    DC.L    $10040200,$0038b03c,$00086600,$e35e0244,$00070044,$4e603084,$6000ef5e,$3c3c44c0
    DC.L    $0c2e0003,$02396604,$61005048,$0244003f,$10040200,$0038b03c,$00086700,$e32e8c44
    DC.L    $30864e75,$4a2e0125,$67067065,$61005060,$6100f340,$3c3c46c0,$60d2246e,$024ce20d
    DC.L    $653ae20d,$651c4a2e,$01256706,$70656100,$503e6100,$e31e3c3c,$4e688c02,$34866000
    DC.L    $eef84a2e,$01256706,$70656100,$502234bc,$40c06100,$e274003d,$6000f2f8,$4a2e0121
    DC.L    $660861ea,$70046000,$510c34bc,$42c06100,$e258003d,$0c2e0003,$02396700,$4fb64e75
    DC.L    $4a2e0121,$6700fc94,$4a2e0125,$67067065,$61004fdc,$6100eea2,$6100e2cc,$6626b23c
    DC.L    $002c6600,$4fa6121c,$3afc4e7b,$e7088400,$0242000f,$e85a3602,$61366600,$4f8a8443
    DC.L    $3ac24e75,$612a6600,$4f7eb23c,$002c6600,$4f7a121c,$36026100,$e28e6600,$4f6a3ac6
    DC.L    $e7088400,$0242000f,$e85a8642,$3ac34e75,$10014880,$1036007e,$41fa00b4,$74001418
    DC.L    $670000a8,$b0106600,$009a48e7,$a0885288,$101c4880,$1036007e,$b0186600,$00825302
    DC.L    $66ee4fef,$00101418,$e14a1418,$121c102e,$0121671e,$b03c0028,$673cb03c,$003c671c
    DC.L    $b03c0020,$6706b03c,$000a663e,$b43c0002,$65067022,$61004f18,$70004e75,$b47c0803
    DC.L    $67f0b47c,$080467ea,$b47c0805,$67e4b47c,$080266e4,$60dcb47c,$000867d6,$b47c0808
    DC.L    $67d0b47c,$080266d0,$60c8b47c,$080564c2,$b47c0800,$64c2b47c,$000365bc,$60b44cdf
    DC.L    $110541f0,$20036000,$ff5670ff,$4e750253,$46430000,$02444643,$00010343,$41435200
    DC.L    $02025553,$50080002,$56425208,$01034341,$41520802,$024d5350,$08030249,$53500804
    DC.L    $01544300,$03034954,$54300004,$03495454,$31000503
    DC.B    "DTT0",0
    DC.B    $06,$03
    DC.B    "DTT1",0
    DC.L    $07044d4d,$55535208,$05025552,$50080602,$53525008,$07044255,$53435200,$08025043
    DC.L    $52080800,$102e0239,$6712b03c,$0002670c,$b03c0003,$66004dfc,$00060040,$61726600
    DC.L    $004ab23c,$002c6600,$4e02121c,$3ac63ac4,$6100e214,$ba7c0040,$6400e0d0,$14050202
    DC.L    $0038b43c,$0020661c,$4a2e0238,$6716206e,$024c2010,$7400760f,$e348e252,$51cbfffa
    DC.L    $31420002,$70346000,$e0640046,$04003ac6,$548d6100,$e034006c,$b23c002c,$66004dac
    DC.L    $121c610c
    DC.B    "fx n"
    DC.L    $024c3144,$00024e75,$78006100,$e0b26748,$41ee046e,$48e74008,$61003fde
    DC.B    "f4$n"
    DC.L    $016a48e7,$501c6100,$d4a04cdf,$380a6622,$0c290005,$000d661a,$28290008,$4a2e0238
    DC.L    $67080829,$0006000c,$6706508f,$70004e75,$70ff4cdf,$10024e75,$e708d002,$b23c002d
    DC.L    $671a01c4,$b23c002f,$67047000,$4e75121c,$6100e04c,$67e27039,$60004d48,$121cb23c
    DC.L    $00386416,$b23c0030,$65101600,$02000008,$04010030,$d001121c,$600e3f00,$6100e020
    DC.L    $66d4e708,$d002361f,$b00365ca,$520007c4,$5203b600,$66f860ac,$6100df6c,$00ff48e7
    DC.L    $1800b23c,$002c6600,$4cda121c,$6100dfdc,$4cdf0018,$d402206e,$024c8510,$102e0239
    DC.L    $670eb03c,$0003670e,$b03c0002,$66004c9c,$00100010,$4e75082e,$0003010e,$67424a04
    DC.L    $663eb63c,$00026638,$36100243,$003fb63c,$003c662c,$20280002,$3240b089,$662248e7
    DC.L    $80802400,$554d6100,$55e64cdf,$0101660e,$00100010,$31400002,$70176000,$500c544d
    DC.L    $4e75102e,$0239b03c,$00016700,$4c3eb03c,$00036604,$00060040,$6100df64,$66244a00
    DC.L    $6600003a,$00060080,$02420007,$ee5a8c42,$b23c002c,$66004c2c,$121c6126,$3ac63ac3
    DC.L    $4e75611e,$b23c002c,$66004c18,$121c6100,$df100242,$0007ee5a,$8c4260e0,$702f6000
    DC.L    $4c267400,$0c2e0014,$01216d3a,$b23c0028,$663a121c,$36026100,$def26616,$8c02b23c
    DC.L    $002c6640,$121c6100,$de206100,$402a3602,$60326100,$de146100,$401e3602,$b23c002c
    DC.L    $66ba6000,$0016b23c,$0028670e,$6100ddfa,$61004004,$b23c0028,$66a2121c,$36026100
    DC.L    $deaa8c02,$b23c0029,$6692121c,$4e75b23c,$00236600,$4b96121c,$6100d4dc,$4a2e0238
    DC.L    $672e6100,$3ff44a43,$6b421002,$488048c0,$b480671c,$b4bc0000,$01006506,$61004b58
    DC.L    $600e0c2e,$00030239,$67067001,$61004c7e,$1c02b23c,$002c6600,$4b4a121c,$6100de42
    DC.L    $d4027070,$80021ac0,$1ac64e75,$2f02b23c,$002c6600,$4b2e121c,$6100de26,$d4027070
    DC.L    $80021ac0,$241f6000,$600c0c2e,$000a0121,$6d00f7e0,$4a2e0125,$67067065,$61004b28
    DC.L    $610015b8,$3ac66100,$de166618,$7601613c,$3ac3b23c,$002c6600,$4aea121c,$6100dd62
    DC.L    $003c4e75,$548d6100,$dd58003c,$b23c002c,$66004ad0,$121c6100,$dde66600,$f1f47600
    DC.L    $610a206e,$024c3143,$00024e75,$d4024a00,$56c00200,$00108600,$8602ea5b,$4e756100
    DC.L    $e9b26100,$dd22003d,$4e75b23c,$00096706,$b23c0020,$6604121c,$60f07400,$b23c000a
    DC.L    $6710b23c,$002a670a,$b23c003b,$67046100,$30e22f02,$61003fd6,$241f43ee,$02562d49
    DC.L    $01422342,$00084229,$000e2d42,$023c41ee,$05a82d48,$024c1d7c,$00020108,$50ee011b
    DC.L    $122cffff
h0_3A24:
    rts
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $3A26 is not reached from known entrypoints
    DC.L    $30aa2f02,$61005f70,$4cdf0004
    DC.B    "f0-B"
    DC.L    $023c41fa
    DC.B    "^H-H"
    DC.L    $017a122c,$ffff50ee,$011251ee,$011c1d7c,$000e0108,$102e0239,$670ab03c,$00036704
    DC.L    $50ee011c
    DC.B    $4e,$75
    DC.B    $70,$45,$60,$00,$4a,$1c ; VIOLATION: orphaned code island at $3A66 is not reached from known entrypoints
h0_3A6C:
    move.b (a4)+,d1
    beq.s h0_3A90
h0_3A70:
    cmp.b #$20,d1
    beq.s h0_3A6C
h0_3A76:
    cmp.b #$A,d1
    beq.s h0_3A90
h0_3A7C:
    cmp.b #$2B,d1
    beq.s h0_3A92
h0_3A82:
    cmp.b #$2D,d1
    bne.w h0_3A98
h0_3A8A:
    bsr.w h0_3B98
h0_3A8E:
    beq.s h0_3A6C
h0_3A90:
    rts
h0_3A92:
    bsr.w h0_3E98
h0_3A96:
    bra.s h0_3A6C
h0_3A98:
    movem.l d1/a4,-(a7)
    ext.w d1
    move.b $7E(a6,d1.w),d1
    bsr.w h0_3ED6
h0_3AA6:
    beq.s h0_3AB6
h0_3AA8:
    bpl.s h0_3AB0
h0_3AAA:
    tst.b $0841(a6)
    beq.s h0_3AB2
h0_3AB0:
    jsr (a0)
h0_3AB2:
    addq.w #8,a7
    bra.s h0_3ABE
h0_3AB6:
    movem.l (a7)+,d1/a4
    bsr.w h0_3AC2
h0_3ABE:
    subq.w #1,a4
    bra.s h0_3A6C
h0_3AC2:
    tst.b $0840(a6)
    beq.w h0_432C
h0_3ACA:
    lea.l $071A(a6),a1
    lea.l $04FA(a6),a2
    move.l a2,$04F4(a6)
    clr.b $04F9(a6)
    lea.l $0C30(a6),a3
    moveq.l #0,d2
    cmp.b #$22,d1
    bne.s h0_3AEE
h0_3AE6:
    move.b d1,d2
    move.b (a4)+,d1
    beq.w h0_3D00
h0_3AEE:
    moveq.l #0,d3
h0_3AF0:
    move.b d1,(a2)+
    move.b d1,(a1)+
    move.b d1,(a3)+
    addq.b #1,$04F9(a6)
    move.b (a4)+,d1
    beq.s h0_3B26
h0_3AFE:
    cmp.b #$A,d1
    beq.s h0_3B26
h0_3B04:
    cmp.b #$20,d1
    beq.s h0_3B22
h0_3B0A:
    cmp.b #$2F,d1
    beq.s h0_3AEE
h0_3B10:
    cmp.b d1,d2
    beq.s h0_3B1E
h0_3B14:
    cmp.b #$2E,d1
    bne.s h0_3AF0
h0_3B1A:
    move.l a1,d3
    bra.s h0_3AF0
h0_3B1E:
    move.b (a4)+,d1
    bra.s h0_3B26
h0_3B22:
    tst.b d2
    bne.s h0_3AF0
h0_3B26:
    tst.l d3
    bne.s h0_3B3A
h0_3B2A:
    clr.b (a1)
    move.b #$2E,(a2)+
    move.b #$73,(a2)+
    addq.b #2,$04F9(a6)
    bra.s h0_3B44
h0_3B3A:
    movea.l d3,a1
    clr.b (a1)
    lea.l $0516(a1),a1
    clr.b (a1)
h0_3B44:
    move.b #$B,(a2)
    addq.b #1,$04F9(a6)
    clr.b (a3)
    lea.l $0C30(a6),a0
    bsr.w h0_3B6A
h0_3B56:
    move.l a0,$0C2C(a6)
    lea.l $076C(a6),a3
h0_3B5E:
    move.b (a0)+,(a3)+
    bne.s h0_3B5E
h0_3B62:
    movea.l $0C2C(a6),a0
    clr.b (a0)
    rts
h0_3B6A:
    moveq.l #0,d0
    movea.l a0,a1
h0_3B6E:
    move.b (a0)+,d1
    beq.s h0_3B88
h0_3B72:
    cmp.b #$5C,d1
    beq.s h0_3B84
h0_3B78:
    cmp.b #$2F,d1
    beq.s h0_3B84
h0_3B7E:
    cmp.b #$3A,d1
    bne.s h0_3B6E
h0_3B84:
    move.l a0,d0
    bra.s h0_3B6E
h0_3B88:
    tst.l d0
    bne.s h0_3B92
h0_3B8C:
    movea.l a1,a0
    moveq.l #-1,d0
    rts
h0_3B92:
    movea.l d0,a0
    moveq.l #0,d0
    rts
h0_3B98:
    move.b (a4)+,d1
    beq.s h0_3BA8
h0_3B9C:
    cmp.b #$20,d1
    beq.s h0_3BA8
h0_3BA2:
    cmp.b #$A,d1
    bne.s h0_3BAC
h0_3BA8:
    moveq.l #0,d0
    rts
h0_3BAC:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$5B,d1
    bcc.s h0_3BCA
h0_3BB8:
    subi.b #65,d1
    bcs.s h0_3C02
h0_3BBE:
    add.b d1,d1
    ext.w d1
    lea.l dat_3C12(pc,d1.w),a2
    adda.w (a2),a2
    jmp (a2)
h0_3BCA:
    cmp.b #$7C,d1
    bne.s h0_3C0E
h0_3BD0:
    lea.l dat_1442(pc),a0
    moveq.l #0,d1
    move.b (a4)+,d1
    bmi.s h0_3C0E
h0_3BDA:
    move.b $0(a0,d1.w),d1
    bmi.s h0_3C0E
h0_3BE0:
    moveq.l #0,d2
h0_3BE2:
    lsl.l #4,d2
    or.b d1,d2
    move.b (a4)+,d1
    bmi.s h0_3BF0
h0_3BEA:
    move.b $0(a0,d1.w),d1
    bpl.s h0_3BE2
h0_3BF0:
    subq.w #1,a4
    tst.l app_slot_01A2(a6)
    bne.s h0_3BFE
h0_3BF8:
    jmp h0_A986.l
h0_3BFE:
    moveq.l #0,d1
    rts
h0_3C02:
    addi.b #65,d1
    cmp.b #$2E,d1
    beq.w h0_3C96
h0_3C0E:
    bra.w h0_3D00
dat_3C12:
    DC.W    h0_3D00-*
dat_3C14:
    DC.W    h0_3C86-*
dat_3C16:
    DC.W    h0_3C5C-*
dat_3C18:
    DC.W    h0_3C68-*
dat_3C1A:
    DC.W    h0_3E06-*
dat_3C1C:
    DC.W    h0_3D00-*
dat_3C1E:
    DC.W    h0_3C9C-*
dat_3C20:
    DC.W    h0_3D68-*
dat_3C22:
    DC.W    h0_3D4A-*
dat_3C24:
    DC.W    h0_3D00-*
dat_3C26:
    DC.W    h0_3D00-*
dat_3C28:
    DC.W    h0_3CB0-*
dat_3C2A:
    DC.W    h0_3C80-*
dat_3C2C:
    DC.W    h0_3D00-*
dat_3C2E:
    DC.W    h0_3D78-*
dat_3C30:
    DC.W    h0_3DBC-*
dat_3C32:
    DC.W    h0_3C62-*
dat_3C34:
    DC.W    h0_3D00-*
dat_3C36:
    DC.W    h0_3C4A-*
dat_3C38:
    DC.W    h0_3D04-*
dat_3C3A:
    DC.W    h0_3D00-*
dat_3C3C:
    DC.W    h0_3E98-*
dat_3C3E:
    DC.W    h0_3D72-*
dat_3C40:
    DC.W    h0_3C7A-*
dat_3C42:
    DC.W    h0_3D00-*
dat_3C44:
    DC.W    h0_3CF8-*
    DC.B    $70,$00,$4e,$75
h0_3C4A:
    lea.l $00FF(a6),a1
h0_3C4E:
    tst.b $0840(a6)
    beq.w h0_3B98
h0_3C56:
    st.b (a1)
    bra.w h0_3B98
h0_3C5C:
    lea.l $00FE(a6),a1
    bra.s h0_3C4E
h0_3C62:
    lea.l $0C26(a6),a1
    bra.s h0_3C4E
h0_3C68:
    tst.b $0840(a6)
    beq.w h0_3B98
h0_3C70:
    move.b #$1,$0104(a6)
    bra.w h0_3B98
h0_3C7A:
    lea.l $0104(a6),a1
    bra.s h0_3C4E
h0_3C80:
    lea.l $021B(a6),a1
    bra.s h0_3C4E
h0_3C86:
    tst.b $0840(a6)
    beq.w h0_3B98
h0_3C8E:
    sf.b $0103(a6)
    bra.w h0_3B98
h0_3C96:
    lea.l $0127(a6),a1
    bra.s h0_3C4E
h0_3C9C:
    tst.b $0840(a6)
    beq.w h0_3B98
h0_3CA4:
    sf.b $0103(a6)
    st.b $0109(a6)
    bra.w h0_3B98
h0_3CB0:
    tst.b $0840(a6)
    beq.w h0_3CBE
h0_3CB8:
    move.w #$2,$021C(a6)
h0_3CBE:
    move.b (a4),d0
    subi.b #48,d0
    bls.w h0_3B98
h0_3CC8:
    subq.b #1,d0
    ext.w d0
    cmp.w #$7,d0
    bcc.w h0_3B98
    DC.L    $013c006c,$67000026,$b03c0006,$66000004,$7002524c,$4a2e0840,$6700feaa,$3d40021c
    DC.L    $6000fea2 ; VIOLATION: decode failed in reachable code; region emitted as data
h0_3CF8:
    lea.l $021A(a6),a1
    bra.w h0_3C4E
h0_3D00:
    moveq.l #-1,d0
    rts
h0_3D04:
    moveq.l #0,d2
    move.b (a4)+,d2
    subi.b #48,d2
    bcs.s h0_3D00
h0_3D0E:
    cmp.b #$A,d2
    bcc.s h0_3D00
h0_3D14:
    move.b (a4),d1
    cmp.b #$30,d1
    bcs.s h0_3D36
h0_3D1C:
    cmp.b #$3A,d1
    bcc.s h0_3D36
h0_3D22:
    mulu.w #$A,d2
    subi.b #48,d1
    andi.w #255,d1
    add.w d1,d2
    move.w d2,$0B6C(a6)
    addq.w #1,a4
h0_3D36:
    tst.w d2
    beq.s h0_3D00
h0_3D3A:
    tst.b $0840(a6)
    beq.w h0_3B98
h0_3D42:
    move.w d2,$0B6C(a6)
    bra.w h0_3B98
h0_3D4A:
    DC.B    $47 ; VIOLATION: invalid overlap: decoded instruction at $3D4A crosses required label at $3D4B; region emitted as data
h0_3D4B:
    lsr.b #7,d0
    movea.w (a0),a1
    asr.b #7,d1
    move.l a2,$2E08(a5)
    DC.B    $43 ; VIOLATION: decode failed in reachable code; region emitted as data
h0_3D56:
    beq.w h0_3D62
h0_3D5A:
    DC.B    $61,$00 ; VIOLATION: invalid overlap: decoded instruction at $3D5A crosses required label at $3D5C; region emitted as data
h0_3D5C:
    DC.B    $09,$3a ; VIOLATION: invalid overlap: decoded instruction at $3D5C crosses required label at $3D5E; region emitted as data
h0_3D5E:
    moveq.l #0,d0
    rts
h0_3D62:
    bsr.w h0_470A
h0_3D66:
    bra.s h0_3D5E
h0_3D68:
    lea.l app_timer_device_iorequest+IO_DATA(a6),a3
    sf.b $012B(a6)
    bra.s h0_3D56
h0_3D72:
    lea.l $07E0(a6),a1
    bra.s h0_3D7C
h0_3D78:
    lea.l $06C8(a6),a1
h0_3D7C:
    moveq.l #81,d0
    moveq.l #0,d2
h0_3D80:
    cmpi.b #34,(a4)
    bne.s h0_3D88
h0_3D86:
    move.b (a4)+,d2
h0_3D88:
    move.b (a4)+,d1
    beq.s h0_3DAE
h0_3D8C:
    cmp.b #$A,d1
    beq.s h0_3DAE
h0_3D92:
    DC.B    $b2 ; VIOLATION: invalid overlap: decoded instruction at $3D92 crosses required label at $3D93; region emitted as data
h0_3D93:
    DC.B    $02,$67,$1a ; VIOLATION: invalid overlap: decoded instruction at $3D93 crosses required label at $3D96; region emitted as data
h0_3D96:
    cmp.b #$20,d1
    bne.s h0_3DA0
h0_3D9C:
    tst.b d2
    beq.s h0_3DAE
h0_3DA0:
    tst.b $0840(a6)
    beq.w h0_3DAA
h0_3DA8:
    DC.B    $12 ; VIOLATION: invalid overlap: decoded instruction at $3DA8 crosses required label at $3DA9; region emitted as data
h0_3DA9:
    DC.B    $c1 ; VIOLATION: invalid overlap: decoded instruction at $3DA9 crosses required label at $3DAA; region emitted as data
h0_3DAA:
    subq.b #1,d0
    bne.s h0_3D88
h0_3DAE:
    subq.w #1,a4
h0_3DB0:
    tst.b $0840(a6)
    beq.w h0_3DBA
h0_3DB8:
    clr.b (a1)
h0_3DBA:
    rts
h0_3DBC:
    DC.B    $4a,$2e,$08 ; VIOLATION: invalid overlap: decoded instruction at $3DBC crosses required label at $3DBF; region emitted as data
h0_3DBF:
    negx.w -(a7)
    DC.B    $00,$00,$10 ; VIOLATION: invalid overlap: decoded instruction at $3DC1 crosses required label at $3DC4; region emitted as data
h0_3DC4:
    st.b $0100(a6)
    move.l app_file_0CDA+fh_Link(a6),app_file_0956+fh_Link(a6)
    st.b $0954(a6)
h0_3DD2:
    move.b (a4),d1
    beq.w h0_3B98
h0_3DD8:
    cmp.b #$20,d1
    beq.w h0_3B98
h0_3DE0:
    cmp.b #$A,d1
    beq.w h0_3B98
h0_3DE8:
    lea.l $078E(a6),a1
    bra.s h0_3D7C
h0_3DEE:
    move.b (a4)+,d1
    beq.s h0_3E04
h0_3DF2:
    cmp.b #$A,d1
    beq.s h0_3E04
h0_3DF8:
    cmp.b #$9,d1
    beq.s h0_3DEE
h0_3DFE:
    cmp.b #$20,d1
    beq.s h0_3DEE
h0_3E04:
    rts
h0_3E06:
    tst.b $0842(a6)
    bne.w h0_3E38
h0_3E0E:
    bsr.s h0_3DEE
h0_3E10:
    beq.s h0_3E34
h0_3E12:
    move.b (a4)+,d1
    beq.s h0_3E34
h0_3E16:
    cmp.b #$A,d1
    beq.s h0_3E34
h0_3E1C:
    cmp.b #$9,d1
    beq.w h0_3E34
h0_3E24:
    cmp.b #$20,d1
    beq.w h0_3E34
h0_3E2C:
    cmp.b #$2C,d1
    bne.s h0_3E12
h0_3E32:
    bra.s h0_3E0E
h0_3E34:
    subq.w #1,a4
    rts
h0_3E38:
    bsr.s h0_3DEE
h0_3E3A:
    beq.s h0_3E96
h0_3E3C:
    st.b d2
    lea.l $03E8(a6),a0
    clr.b $0004(a0)
    bsr.w h0_76B8
h0_3E4A:
    bne.s h0_3E90
h0_3E4C:
    cmp.b #$3D,d1
    beq.s h0_3E58
h0_3E52:
    moveq.l #1,d2
    moveq.l #2,d3
    bra.s h0_3E68
h0_3E58:
    move.b (a4)+,d1
    bsr.w h0_0DB6
h0_3E5E:
    tst.b d4
    bne.s h0_3E90
h0_3E62:
    cmp.b #$2,d3
    bne.s h0_3E90
h0_3E68:
    lea.l $03E8(a6),a0
    movem.l d1-d2,-(a7)
    bsr.w h0_0BCE
h0_3E74:
    movem.l (a7)+,d1/d4
    beq.s h0_3E90
h0_3E7A:
    lea.l $016A(a6),a2
    moveq.l #2,d3
    move.w d1,-(a7)
    bsr.w h0_0CB6
h0_3E86:
    move.w (a7)+,d1
    cmp.b #$2C,d1
    bne.s h0_3E96
h0_3E8E:
    bra.s h0_3E38
h0_3E90:
    moveq.l #81,d0
    bra.w h0_8486
h0_3E96:
    bra.s h0_3EAE
h0_3E98:
    tst.b $0841(a6)
    DC.B    $66 ; VIOLATION: invalid overlap: decoded instruction at $3E9C crosses required label at $3E9D; region emitted as data
h0_3E9D:
    DC.B    $16 ; VIOLATION: invalid overlap: decoded instruction at $3E9D crosses required label at $3E9E; region emitted as data
h0_3E9E:
    move.b (a4)+,d1
    beq.s h0_3EAE
h0_3EA2:
    cmp.b #$20,d1
    beq.s h0_3EAE
h0_3EA8:
    cmp.b #$A,d1
    bne.s h0_3E9E
h0_3EAE:
    subq.w #1,a4
    moveq.l #0,d0
h0_3EB2:
    rts
h0_3EB4:
    bsr.w h0_4334
h0_3EB8:
    bra.s h0_3EAE
    DC.B    $2f,$0c ; VIOLATION: orphaned code island at $3EBA is not reached from known entrypoints
    DC.L    $426e0218,$610c285f,$526e0218,$51ee0102
    DC.B    $4e,$75
    DC.B    $2d,$4f,$02,$34,$60,$00,$04,$60 ; VIOLATION: orphaned code island at $3ECE is not reached from known entrypoints
h0_3ED6:
    lea.l dat_3F3C(pc),a0
    moveq.l #0,d2
h0_3EDC:
    move.b (a0)+,d2
    beq.s h0_3F04
h0_3EE0:
    cmp.b (a0),d1
    blt.s h0_3F04
h0_3EE4:
    bne.s h0_3EFE
h0_3EE6:
    lea.l $0001(a0),a1
    movea.l a4,a2
    move.b d2,d3
h0_3EEE:
    subq.b #1,d3
    beq.s h0_3F08
h0_3EF2:
    move.b (a2)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b (a1)+,d0
    beq.s h0_3EEE
h0_3EFE:
    lea.l $2(a0,d2.w),a0
    bra.s h0_3EDC
h0_3F04:
    moveq.l #0,d0
    rts
h0_3F08:
    move.b (a2),d0
    beq.s h0_3F26
h0_3F0C:
    cmp.b #$A,d0
    beq.s h0_3F26
h0_3F12:
    cmp.b #$2C,d0
    beq.s h0_3F26
h0_3F18:
    cmp.b #$9,d0
    beq.s h0_3F26
h0_3F1E:
    cmp.b #$20,d0
    beq.s h0_3F26
h0_3F24:
    bra.s h0_3EFE
h0_3F26:
    move.b (a1)+,d0
    lsl.w #8,d0
    move.b (a1)+,d0
    lea.l -$2(a1,d0.w),a0
    movea.l a2,a4
    move.b (a4)+,d1
    lea.l dat_42D3(pc),a2
    cmpa.l a2,a0
    rts
dat_3F3C:
    DC.B    $05,$41,$4c,$49,$4e,$4b
dat_3F42:
    DC.W    h0_4200-*
    DC.L    $09414c4c
    DC.B    "OWZERO"
dat_3F4E:
    DC.W    h0_42A2-*
    DC.L    $05414d49
    DC.B    $47,$41
dat_3F56:
    DC.W    h0_41F8-*
    DC.L    $06415554
    DC.B    $4f,$50,$43
dat_3F5F:
    DC.W    h0_424E-*
    DC.B    $03,$42,$44,$4c
dat_3F65:
    DC.W    h0_423C-*
    DC.B    $03,$42,$44,$57
dat_3F6B:
    DC.W    h0_4236-*
    DC.B    $03,$42,$52,$42
dat_3F71:
    DC.W    h0_4218-*
    DC.B    $03,$42,$52,$4c
dat_3F77:
    DC.W    h0_4224-*
    DC.B    $03,$42,$52,$53
dat_3F7D:
    DC.W    h0_4218-*
    DC.B    $03,$42,$52,$57
dat_3F83:
    DC.W    h0_421E-*
    DC.B    $04
    DC.B    "CASE"
dat_3F8A:
    DC.W    h0_4162-*
    DC.L    $0643484b
    DC.B    $42,$49,$54
dat_3F93:
    DC.W    h0_428E-*
    DC.B    $06
    DC.B    "CHKIMM"
dat_3F9C:
    DC.W    h0_4276-*
    DC.B    $05
    DC.B    "CHKPC"
dat_3FA4:
    DC.W    h0_425A-*
    DC.B    $01,$44
dat_3FA8:
    DC.W    h0_4178-*
    DC.B    $05
    DC.B    "DEBUG"
dat_3FB0:
    DC.W    h0_4178-*
    DC.B    $04
    DC.B    "EVEN"
dat_3FB7:
    DC.W    h0_4282-*
    DC.B    $04
    DC.B    "FROM"
dat_3FBE:
    DC.W    h0_431A-*
    DC.L    $0647454e
    DC.B    $53,$59,$4d
dat_3FC7:
    DC.W    h0_4168-*
    DC.B    $04
    DC.B    "HCLN"
dat_3FCE:
    DC.W    h0_42BA-*
    DC.L    $06484541
    DC.B    $44,$45,$52
dat_3FD7:
    DC.W    h0_42E8-*
    DC.B    $06
    DC.B    "INCDIR"
dat_3FE0:
    DC.W    h0_42F6-*
    DC.B    $07
    DC.B    "INCONCE"
dat_3FEA:
    DC.W    h0_42AE-*
    DC.L    $074c4154
    DC.B    "TICE"
dat_3FF4:
    DC.W    h0_41D8-*
    DC.B    $04
    DC.B    "LINE"
dat_3FFB:
    DC.W    h0_42C4-*
    DC.B    $04
    DC.B    "LIST"
dat_4002:
    DC.W    h0_41B6-*
    DC.L    $054c4953
    DC.B    $54,$31
dat_400A:
    DC.W    h0_41C2-*
    DC.L    $084c4f43
    DC.B    "ALDOT"
dat_4015:
    DC.W    h0_426E-*
    DC.B    $06
    DC.B    "LOCALU"
dat_401E:
    DC.W    h0_4266-*
    DC.L    $064c4f57
    DC.B    $4d,$45,$4d
dat_4027:
    DC.W    h0_430E-*
    DC.B    $03,$4d,$45,$58
dat_402D:
    DC.W    h0_41DA-*
    DC.B    $0b
    DC.B    "NOALLOWZERO"
dat_403B:
    DC.W    h0_42A8-*
    DC.B    $08
    DC.B    "NOAUTOPC"
dat_4046:
    DC.W    h0_4254-*
    DC.L    $064e4f43
    DC.B    $41,$53,$45
dat_404F:
    DC.W    h0_4172-*
    DC.B    $08
    DC.B    "NOCHKBIT"
dat_405A:
    DC.W    h0_4294-*
    DC.L    $084e4f43
    DC.B    "HKIMM"
dat_4065:
    DC.W    h0_427C-*
    DC.B    $07
    DC.B    "NOCHKPC"
dat_406F:
    DC.W    h0_4260-*
    DC.B    $07
    DC.B    "NOCODES"
dat_4079:
    DC.W    h0_4186-*
    DC.B    $07
    DC.B    "NODEBUG"
dat_4083:
    DC.W    h0_418C-*
    DC.B    $06
    DC.B    "NOEVEN"
dat_408C:
    DC.W    h0_4288-*
    DC.B    $06
    DC.B    "NOHCLN"
dat_4095:
    DC.W    h0_42CE-*
    DC.B    $09
    DC.B    "NOINCONCE"
dat_40A1:
    DC.W    h0_42B4-*
    DC.B    $06
    DC.B    "NOLINE"
dat_40AA:
    DC.W    h0_42CE-*
    DC.L    $064e4f4c
    DC.B    $49,$53,$54
dat_40B3:
    DC.W    h0_41BC-*
    DC.B    $07
    DC.B    "NOLIST1"
dat_40BD:
    DC.W    h0_41C8-*
    DC.B    $05
    DC.B    "NOMEX"
dat_40C5:
    DC.W    h0_41E0-*
    DC.B    $08
    DC.B    "NOSYMTAB"
dat_40D0:
    DC.W    h0_41B0-*
    DC.B    $09
    DC.B    "NOTRACEIF"
dat_40DC:
    DC.W    h0_41D4-*
    DC.B    $06
    DC.B    "NOTYPE"
dat_40E5:
    DC.W    h0_4198-*
    DC.B    $06
    DC.B    "NOWARN"
dat_40EE:
    DC.W    h0_41A4-*
    DC.L    $034f444c
dat_40F4:
    DC.W    h0_4248-*
    DC.B    $03,$4f,$44,$57
dat_40FA:
    DC.W    h0_4242-*
    DC.L    $034f4c44
dat_4100:
    DC.W    h0_41E6-*
    DC.B    $05
    DC.B    "QUIET"
dat_4108:
    DC.W    h0_4314-*
    DC.B    $04
    DC.B    "SREC"
dat_410F:
    DC.W    h0_41FC-*
    DC.B    $05
    DC.B    "SUPER"
dat_4117:
    DC.W    h0_41EC-*
    DC.B    $06
    DC.B    "SYMTAB"
dat_4120:
    DC.W    h0_41AA-*
    DC.B    $02,$54,$4f
dat_4125:
    DC.W    h0_42D4-*
    DC.B    $07
    DC.B    "TRACEIF"
dat_412F:
    DC.W    h0_41CE-*
    DC.B    $04
    DC.B    "TYPE"
dat_4136:
    DC.W    h0_4192-*
    DC.L    $04555345
    DC.B    $52
dat_413D:
    DC.W    h0_41F2-*
    DC.B    $04
    DC.B    "WARN"
dat_4144:
    DC.W    h0_419E-*
    DC.B    $07
    DC.B    "WARNBIT"
dat_414E:
    DC.W    h0_429A-*
    DC.L    $04574954
    DC.B    $48
dat_4155:
    DC.W    h0_4322-*
    DC.B    $06
    DC.B    "XDEBUG"
dat_415E:
    DC.W    h0_4180-*
    DC.B    $00,$00
h0_4162:
    sf.b $00FE(a6)
    rts
h0_4168:
    st.b $0109(a6)
    sf.b $0103(a6)
    rts
h0_4172:
    st.b $00FE(a6)
    rts
h0_4178:
    move.b #$1,$0104(a6)
    rts
h0_4180:
    st.b $0104(a6)
    rts
h0_4186:
    st.b $0128(a6)
    rts
h0_418C:
    sf.b $0104(a6)
    rts
h0_4192:
    sf.b $0107(a6)
    rts
h0_4198:
    st.b $0107(a6)
    rts
h0_419E:
    st.b $0105(a6)
    rts
h0_41A4:
    sf.b $0105(a6)
    rts
h0_41AA:
    st.b $00FF(a6)
    rts
h0_41B0:
    sf.b $00FF(a6)
    rts
h0_41B6:
    st.b $0100(a6)
    rts
h0_41BC:
    sf.b $0100(a6)
    rts
h0_41C2:
    st.b $021A(a6)
    rts
h0_41C8:
    sf.b $021A(a6)
    rts
h0_41CE:
    st.b $0126(a6)
    rts
h0_41D4:
    sf.b $0126(a6)
h0_41D8:
    rts
h0_41DA:
    st.b $0117(a6)
    rts
h0_41E0:
    sf.b $0117(a6)
    rts
h0_41E6:
    st.b $0124(a6)
    rts
h0_41EC:
    sf.b $0125(a6)
    rts
h0_41F2:
    st.b $0125(a6)
    rts
h0_41F8:
    moveq.l #3,d0
    bra.s h0_4202
h0_41FC:
    moveq.l #5,d0
    bra.s h0_4202
h0_4200:
    moveq.l #2,d0
h0_4202:
    move.w d0,$021C(a6)
    tst.l $0224(a6)
    bne.w h0_43D2
    tst.b $0238(a6)
    beq.w h0_44E4
    rts
h0_4218:
    st.b $012C(a6)
    rts
h0_421E:
    sf.b $012C(a6)
    rts
h0_4224:
    cmpi.b #20,$0121(a6)
    blt.w h0_3132
    move.b #$1,$012C(a6)
    rts
h0_4236:
    st.b $012D(a6)
    rts
h0_423C:
    sf.b $012D(a6)
    rts
h0_4242:
    st.b $012E(a6)
    rts
h0_4248:
    sf.b $012E(a6)
    rts
h0_424E:
    st.b $0119(a6)
    rts
h0_4254:
    sf.b $0119(a6)
    rts
h0_425A:
    st.b $0106(a6)
    rts
h0_4260:
    sf.b $0106(a6)
    rts
h0_4266:
    move.b #$5F,$0116(a6)
    rts
h0_426E:
    move.b #$2E,$0116(a6)
    rts
h0_4276:
    st.b $011D(a6)
    rts
h0_427C:
    sf.b $011D(a6)
    rts
h0_4282:
    st.b $011F(a6)
    rts
h0_4288:
    sf.b $011F(a6)
    rts
h0_428E:
    st.b $011E(a6)
    rts
h0_4294:
    sf.b $011E(a6)
    rts
h0_429A:
    move.b #$1,$011E(a6)
    rts
h0_42A2:
    st.b $0120(a6)
    rts
h0_42A8:
    sf.b $0120(a6)
    rts
h0_42AE:
    st.b $0134(a6)
    rts
h0_42B4:
    sf.b $0134(a6)
    rts
h0_42BA:
    st.b $0129(a6)
    st.b $012A(a6)
    rts
h0_42C4:
    st.b $0129(a6)
    sf.b $012A(a6)
    rts
h0_42CE:
    sf.b $0129(a6)
    DC.B    $4e ; VIOLATION: invalid overlap: decoded instruction at $42D2 crosses required label at $42D3; region emitted as data
dat_42D3:
    DC.B    $75
h0_42D4:
    bsr.w h0_3DEE
    subq.w #1,a4
    tst.b $0840(a6)
    beq.w h0_432C
    bsr.w h0_3D78
    bra.s h0_4330
h0_42E8:
    move.b $0840(a6),-(a7)
    lea.l app_timer_device_iorequest+IO_DATA(a6),a3
    sf.b $012B(a6)
    bra.s h0_4302
h0_42F6:
    move.b $0843(a6),-(a7)
    lea.l $0832(a6),a3
    st.b $012B(a6)
h0_4302:
    bsr.w h0_3DEE
    subq.w #1,a4
    tst.b (a7)+
    bra.w h0_3D56
h0_430E:
    st.b $021B(a6)
    rts
h0_4314:
    st.b $0127(a6)
    rts
h0_431A:
    bsr.w h0_3DEE
    bra.w h0_3AC2
h0_4322:
    bsr.w h0_3DEE
    subq.w #1,a4
    lea.l $07E0(a6),a1
h0_432C:
    bsr.w h0_3D7C
h0_4330:
    move.b (a4)+,d1
    rts
h0_4334:
    move.b (a4)+,d1
    st.b $0844(a6)
    cmp.b #$A,d1
    beq.w h0_3A24
h0_4342:
    cmp.b #$9,d1
    beq.w h0_3A24
h0_434A:
    cmp.b #$20,d1
    beq.w h0_3A24
h0_4352:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    beq.w h0_3A24
h0_435C:
    move.b (a4),d0
    cmp.b #$2B,d0
    beq.s h0_4374
h0_4364:
    cmp.b #$2D,d0
    beq.s h0_4374
h0_436A:
    bsr.w h0_3ED6
h0_436E:
    beq.s h0_4374
h0_4370:
    jsr (a0)
h0_4372:
    bra.s h0_4390
h0_4374:
    subi.b #65,d1
    bcs.s h0_4398
h0_437A:
    cmp.b #$1A,d1
    bcc.s h0_4398
h0_4380:
    ext.w d1
    add.w d1,d1
    move.w dat_439E(pc,d1.w),d0
    beq.s h0_4398
h0_438A:
    move.b (a4)+,d1
    jsr dat_439E(pc,d0.w)
h0_4390:
    cmp.b #$2C,d1
    beq.s h0_4334
h0_4396:
    rts
h0_4398:
    moveq.l #58,d0
    bra.w h0_8482
dat_439E:
    DC.W    h0_4438-dat_439E
    DC.W    $0000
    DC.W    h0_445E-dat_439E
    DC.W    h0_43EC-dat_439E
    DC.W    h0_4448-dat_439E
    DC.W    $0000
    DC.W    $0000
    DC.W    $0000
    DC.W    h0_4440-dat_439E
    DC.W    $0000
    DC.W    $0000
    DC.W    h0_4490-dat_439E
    DC.W    h0_4402-dat_439E
    DC.W    $0000
    DC.W    h0_4504-dat_439E
    DC.W    h0_440A-dat_439E
    DC.W    $0000
    DC.W    $0000
    DC.W    h0_4420-dat_439E
    DC.W    h0_43FA-dat_439E
    DC.W    h0_4450-dat_439E
    DC.W    $0000
    DC.W    h0_4428-dat_439E
    DC.W    h0_4430-dat_439E
    DC.W    h0_43D8-dat_439E
    DC.W    $0000
h0_43D2:
    moveq.l #64,d0
h0_43D4:
    bra.w h0_8486
h0_43D8:
    move.b (a4)+,d0
    exg d0,d1
    cmp.b #$2B,d0
    beq.s h0_43EA
h0_43E2:
    cmp.b #$2D,d0
    bne.s h0_4398
h0_43E8:
    tst.b d0
h0_43EA:
    rts
h0_43EC:
    bsr.s h0_43D8
h0_43EE:
    seq.b d0
    andi.b #1,d0
    move.b d0,$0104(a6)
    rts
h0_43FA:
    bsr.s h0_43D8
h0_43FC:
    sne.b $0107(a6)
    rts
h0_4402:
    bsr.s h0_43D8
h0_4404:
    seq.b $0117(a6)
    rts
h0_440A:
    cmp.b #$3D,d1
    bne.s h0_4418
h0_4410:
    bsr.w h0_316E
h0_4414:
    bne.s h0_4398
h0_4416:
    rts
h0_4418:
    bsr.s h0_43D8
h0_441A:
    seq.b $0106(a6)
    rts
h0_4420:
    bsr.s h0_43D8
h0_4422:
    seq.b $00FF(a6)
    rts
h0_4428:
    bsr.s h0_43D8
h0_442A:
    seq.b $0105(a6)
    rts
h0_4430:
    bsr.s h0_43D8
h0_4432:
    seq.b $0104(a6)
    rts
h0_4438:
    bsr.s h0_43D8
h0_443A:
    seq.b $0119(a6)
    rts
h0_4440:
    bsr.s h0_43D8
h0_4442:
    seq.b $011D(a6)
    rts
h0_4448:
    bsr.s h0_43D8
h0_444A:
    seq.b $011F(a6)
    rts
h0_4450:
    moveq.l #95,d2
    bsr.s h0_43D8
h0_4454:
    beq.s h0_4458
h0_4456:
    moveq.l #46,d2
h0_4458:
    move.b d2,$0116(a6)
    rts
h0_445E:
    bsr.w h0_455A
h0_4462:
    bne.s h0_447A
h0_4464:
    cmp.w #$8,d2
    bcs.w h0_4398
h0_446C:
    cmp.w #$80,d2
    bcc.w h0_4398
h0_4474:
    addq.w #1,d2
    move.w d2,$021E(a6)
h0_447A:
    cmp.b #$2B,d1
    beq.s h0_4488
h0_4480:
    cmp.b #$2D,d1
    bne.s h0_448E
h0_4486:
    tst.b d1
h0_4488:
    sne.b $00FE(a6)
    move.b (a4)+,d1
h0_448E:
    rts
h0_4490:
    tst.l $0224(a6)
    bne.w h0_43D2
h0_4498:
    move.b d1,d0
    move.b (a4)+,d1
    tst.b $0238(a6)
    bne.s h0_4502
h0_44A2:
    cmp.b #$2B,d0
    beq.s h0_44E0
h0_44A8:
    DC.B    $b0,$3c ; VIOLATION: invalid overlap: decoded instruction at $44A8 crosses required label at $44AA; region emitted as data
h0_44AA:
    DC.B    $00,$2d,$67,$2e ; VIOLATION: invalid overlap: decoded instruction at $44AA crosses required label at $44AE; region emitted as data
h0_44AE:
    subi.b #48,d0
    bcs.w h0_4398
h0_44B6:
    ext.w d0
    beq.s h0_44DA
h0_44BA:
    subq.w #1,d0
    cmp.w #$7,d0
    bcc.w h0_4398
    DC.L    $013c006c ; VIOLATION: decode failed in reachable code; region emitted as data
h0_44C8:
    beq.w h0_4398
h0_44CC:
    cmp.b #$6,d0
    bne.s h0_44D4
h0_44D2:
    moveq.l #2,d0
h0_44D4:
    move.w d0,$021C(a6)
    bra.s h0_44E4
h0_44DA:
    bra.s h0_44E4
h0_44DC:
    moveq.l #3,d0
h0_44DE:
    bra.s h0_44D4
h0_44E0:
    moveq.l #2,d0
    bra.s h0_44D4
h0_44E4:
    movea.l $0142(a6),a1
    movea.l $013E(a6),a0
    clr.l app_file_0186+fh_Pos(a6)
    tst.b $0238(a6)
    bne.s h0_44FA
h0_44F6:
    clr.l $01A6(a6)
h0_44FA:
    bsr.w h0_79A6
h0_44FE:
    move.b -$0001(a4),d1
h0_4502:
    rts
h0_4504:
    lea.l $010E(a6),a1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$57,d1
    bne.s h0_451A
h0_4514:
    lea.l $0110(a6),a1
    move.b (a4)+,d1
h0_451A:
    cmp.b #$2D,d1
    beq.s h0_454E
h0_4520:
    cmp.b #$2B,d1
    beq.s h0_4552
h0_4526:
    bsr.w h0_455A
h0_452A:
    subq.w #1,d2
    bmi.w h0_4398
h0_4530:
    cmp.w #$B,d2
    bhi.w h0_4398
h0_4538:
    bsr.w h0_43D8
h0_453C:
    beq.s h0_4546
h0_453E:
    move.w (a1),d0
    bclr d2,d0
    move.w d0,(a1)
    rts
h0_4546:
    move.w (a1),d0
    bset d2,d0
    move.w d0,(a1)
    rts
h0_454E:
    clr.w (a1)
    bra.s h0_4556
h0_4552:
    move.w #$FFFF,(a1)
h0_4556:
    move.b (a4)+,d1
    rts
h0_455A:
    cmp.b #$30,d1
    bcs.s h0_458E
h0_4560:
    cmp.b #$39,d1
    bhi.s h0_458E
h0_4566:
    moveq.l #0,d2
    subi.b #48,d1
    move.b d1,d2
h0_456E:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.s h0_458C
h0_4576:
    cmp.b #$3A,d1
    bcc.s h0_458C
h0_457C:
    mulu.w #$A,d2
    subi.b #48,d1
    andi.w #15,d1
    add.w d1,d2
    bra.s h0_456E
h0_458C:
    moveq.l #0,d0
h0_458E:
    rts
h0_4590:
    tst.b $0954(a6)
    beq.s h0_45C6
h0_4596:
    lea.l $078E(a6),a0
    tst.b (a0)
    bne.s h0_45C2
h0_459E:
    lea.l $04F4(a6),a1
    moveq.l #0,d0
    move.b $0005(a1),d0
    subq.b #1,d0
    bmi.s h0_45B4
h0_45AC:
    movea.l (a1),a1
h0_45AE:
    move.b (a1)+,(a0)+
    dbf.w d0,h0_45AE
h0_45B4:
    clr.b (a0)
    lea.l $078E(a6),a0
    lea.l dat_45C8(pc),a2
    bsr.w h0_45CE
h0_45C2:
    bra.w h0_AB2C
h0_45C6:
    rts
dat_45C8:
    DC.B    $2e,$6c,$73,$74,$00,$00 ; VIOLATION: orphaned code island at $45C8 is not reached from known entrypoints
h0_45CE:
    bsr.s h0_45E2
h0_45D0:
    beq.s h0_45D4
h0_45D2:
    movea.l d2,a1
h0_45D4:
    subq.w #1,a1
h0_45D6:
    move.b (a2)+,(a1)+
    bne.s h0_45D6
h0_45DA:
    rts
h0_45DC:
    bsr.s h0_45E2
h0_45DE:
    beq.s h0_45D4
h0_45E0:
    rts
h0_45E2:
    movea.l a0,a1
h0_45E4:
    moveq.l #0,d2
h0_45E6:
    move.b (a1)+,d1
    beq.s h0_4606
h0_45EA:
    cmp.b #$5C,d1
    beq.s h0_45E4
h0_45F0:
    cmp.b #$2F,d1
    beq.s h0_45E4
h0_45F6:
    cmp.b #$3A,d1
    beq.s h0_45E4
h0_45FC:
    cmp.b #$2E,d1
    bne.s h0_45E6
h0_4602:
    move.l a1,d2
    bra.s h0_45E6
h0_4606:
    tst.l d2
h0_4608:
    rts
h0_460A:
    tst.b $012B(a6)
    beq.s h0_4608
h0_4610:
    movea.l (a3),a0
    move.b -$1(a0,d3.w),d0
    cmp.b #$3A,d0
    beq.s h0_4608
h0_461C:
    cmp.b #$2F,d0
    beq.s h0_4608
h0_4622:
    cmp.b #$5C,d0
    beq.s h0_4608
h0_4628:
    moveq.l #47,d1
h0_462A:
    movea.l (a3),a0
    cmp.w $0004(a3),d3
    bcs.s h0_4660
h0_4632:
    movem.l d0-d2/a1-a2,-(a7)
    moveq.l #100,d1
    add.w $0004(a3),d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_4640:
    movea.l (a3),a1
    move.l a0,(a3)
    move.w $0004(a3),d1
    lsr.w #2,d1
    beq.s h0_4654
h0_464C:
    subq.w #1,d1
h0_464E:
    move.l (a1)+,(a0)+
    dbf.w d1,h0_464E
h0_4654:
    movem.l (a7)+,d0-d2/a1-a2
    addi.w #100,$0004(a3)
    movea.l (a3),a0
h0_4660:
    move.b d1,$0(a0,d3.w)
    addq.w #1,d3
    rts
h0_4668:
    moveq.l #MEMF_FAST,d1
    move.w d1,$0004(a3)
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_4672:
    move.l a0,(a3)
    clr.b (a0)
    rts
h0_4678:
    movea.l (a3),a0
    clr.b (a0)
h0_467C:
    moveq.l #0,d3
    tst.w $0004(a3)
    beq.s h0_4694
h0_4684:
    movea.l (a3),a0
h0_4686:
    tst.b (a0)+
    beq.s h0_4694
h0_468A:
    addq.w #1,d3
    tst.b (a0)+
    bne.s h0_468A
h0_4690:
    addq.w #1,d3
    bra.s h0_4686
h0_4694:
    rts
h0_4696:
    move.b (a4)+,d1
    bsr.s h0_467C
h0_469A:
    moveq.l #0,d2
    cmp.b #$22,d1
    beq.s h0_46A8
h0_46A2:
    cmp.b #$27,d1
    bne.s h0_46AC
h0_46A8:
    move.b d1,d2
h0_46AA:
    move.b (a4)+,d1
h0_46AC:
    beq.s h0_46F6
h0_46AE:
    cmp.b #$A,d1
    beq.s h0_46F6
h0_46B4:
    cmp.b #$20,d1
    bne.s h0_46C0
h0_46BA:
    tst.b d2
    bne.s h0_46DA
h0_46BE:
    bra.s h0_46F6
h0_46C0:
    cmp.b #$9,d1
    beq.s h0_46F6
h0_46C6:
    cmp.b d2,d1
    beq.s h0_46E0
h0_46CA:
    cmp.b #$3B,d1
    beq.s h0_46D6
h0_46D0:
    cmp.b #$2C,d1
    bne.s h0_46DA
h0_46D6:
    tst.b d2
    beq.s h0_46E8
h0_46DA:
    bsr.w h0_462A
h0_46DE:
    bra.s h0_46AA
h0_46E0:
    move.b (a4)+,d1
    cmp.b #$2C,d1
    bne.s h0_46F6
h0_46E8:
    bsr.w h0_460A
h0_46EC:
    moveq.l #0,d1
    bsr.w h0_462A
h0_46F2:
    move.b (a4)+,d1
    bra.s h0_469A
h0_46F6:
    bsr.w h0_460A
h0_46FA:
    moveq.l #0,d1
    bsr.w h0_462A
h0_4700:
    bsr.w h0_462A
h0_4704:
    move.b -$0001(a4),d1
    rts
h0_470A:
    move.b (a4)+,d1
h0_470C:
    moveq.l #0,d2
    cmp.b #$22,d1
    beq.s h0_471A
h0_4714:
    cmp.b #$27,d1
    bne.s h0_471E
h0_471A:
    move.b d1,d2
h0_471C:
    move.b (a4)+,d1
h0_471E:
    beq.s h0_4730
h0_4720:
    cmp.b #$A,d1
    beq.s h0_4730
h0_4726:
    cmp.b #$20,d1
    bne.s h0_4732
h0_472C:
    tst.b d2
    bne.s h0_471C
h0_4730:
    rts
h0_4732:
    cmp.b #$9,d1
    beq.s h0_4730
h0_4738:
    cmp.b d2,d1
    beq.s h0_474C
h0_473C:
    cmp.b #$3B,d1
    beq.s h0_4748
h0_4742:
    cmp.b #$2C,d1
    bne.s h0_471C
h0_4748:
    tst.b d2
    bne.s h0_471C
h0_474C:
    move.b (a4)+,d1
    cmp.b #$2C,d1
    bne.s h0_4730
h0_4754:
    move.b (a4)+,d1
    bra.s h0_470C
    DC.B    $41,$ee,$06,$c8,$74,$00,$4a,$10,$67,$04,$72,$0a,$4e,$75 ; VIOLATION: orphaned code island at $4758 is not reached from known entrypoints
    DC.B    $b2,$3c ; VIOLATION: orphaned code island at $4766 is not reached from known entrypoints
    DC.L    $000a671a,$b23c0009,$6714b23c,$0020670e,$10c1121c,$5202b43c,$005266e2,$720a4210
    DC.B    $4e,$75
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $478A is not reached from known entrypoints
    DC.L    $00140121,$6d00e9a0,$0c2e0020,$01216700,$e9964a2e,$02396600,$3ca66100,$d578b23c
    DC.L    $002c6600,$3cb2121c,$b23c0023,$66003cb0,$121c6100,$c5f66000
    DC.B    $d3,$0c
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $47C6 is not reached from known entrypoints
    DC.L    $db8850ee,$023b6100,$cf160064
    DC.B    "NuJ."
    DC.L    $0238670a,$08ee0000,$0c246100,$636c720a,$50ee0113
    DC.B    $4e,$75
    DC.B    $08,$ae,$00,$00,$0c,$24,$4e,$75 ; VIOLATION: orphaned code island at $47EE is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $47F6 is not reached from known entrypoints
    DC.L    $22dab4bc,$0000000c,$6512b4bc,$000000ff,$640a3d42,$0b6450ee,$01134e75
    DC.B    $70,$4b,$60,$00,$3c,$6e ; VIOLATION: orphaned code island at $4814 is not reached from known entrypoints
    DC.B    $74,$00 ; VIOLATION: orphaned code island at $481A is not reached from known entrypoints
    DC.L    $04010030,$654cb23c,$000a6446,$1401121c,$b23c000a,$6724b23c,$0009671e,$b23c0020
    DC.L    $67180401,$0030652a,$b23c000a,$6424c4fc,$000a0241,$000fd441,$121c70fc,$55826718
    DC.L    $70fa5d82,$67127000,$5582670c,$70fe5d82,$6706705a,$60003c14
    DC.B    $1d,$40,$01,$2f,$4e,$75 ; VIOLATION: orphaned code island at $4874 is not reached from known entrypoints
    DC.B    $61,$00,$e2,$86,$61,$00,$ee,$48,$66,$00,$ee,$b2,$74,$00,$34,$04 ; VIOLATION: orphaned code island at $487A is not reached from known entrypoints
h0_488A:
    movea.l $016A(a6),a2
    lea.l $03E8(a6),a0
    movem.l d2/a3-a5,-(a7)
    tst.b $0238(a6)
    bne.s h0_48B4
h0_489C:
    bsr.w h0_0B88
h0_48A0:
    movem.l (a7)+,d4/a3-a5
    beq.w h0_8436
h0_48A8:
    moveq.l #5,d3
    bsr.w h0_0CBA
h0_48AE:
    move.b -$0001(a4),d1
    rts
h0_48B4:
    bsr.w h0_0B88
h0_48B8:
    movem.l (a7)+,d4/a3-a5
    bne.w h0_843A
h0_48C0:
    cmpi.b #5,$000D(a1)
    bne.w h0_8436
h0_48CA:
    cmp.l $0008(a1),d4
    bne.w h0_8436
h0_48D2:
    bset.b #6,$000C(a1)
    bne.w h0_8436
h0_48DC:
    bra.s h0_48AE
    DC.B    $01,$00 ; VIOLATION: orphaned code island at $48DE is not reached from known entrypoints
    DC.L    $010241ee,$03e87000,$102e0239,$b03c0001,$6710082e,$0000084d,$6708242e,$0846d5ae
    DC.L    $084a4a90,$66266100,$cdc47000,$102e0239,$103b00cc,$e1aa4a2e,$08466a02,$4482202e
    DC.L    $084ad5ae,$084a2400,$6000e254
    DC.L    $4a2e0238,$66482f08,$6100cd96 ; VIOLATION: orphaned code island at $492C is not reached from known entrypoints
    DC.B    " _fnJ"
    DC.B    $04,$66,$6a
    DC.L    $2a026100,$c28a6700,$3aee45ee,$016a7602,$282e084a,$10280006,$b02e0116,$670c6100
    DC.L    $c3562405,$122cffff
    DC.B    $60,$a0
    DC.B    $45,$ee,$01,$5a,$4a,$92,$67,$00,$3a,$d0,$61,$00,$c3,$d6,$60,$e8 ; VIOLATION: orphaned code island at $496A is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $497A is not reached from known entrypoints
    DC.L    $c2526600,$3ace0c29,$0002000d,$66003ac4,$20290008,$b0ae084a,$66003aa8,$08e90006
    DC.L    $000c6600,$3a966100,$cd286000,$ff624e75,$6100211a,$4a826b00,$f0b22f02,$61004ffe
    DC.L    $4cdf0004,$6600f0a4,$42ae0182,$94ae023c,$2d42018e,$122cffff,$4e759481,$650e670a
    DC.L    $28027600,$72006100,$df747000,$4e7542ae,$084a720a,$4e756100,$ccd866f2,$4a0466ee
    DC.L    $2d42084a,$6000e17c,$0c2e000a,$01216d00,$e7263ac6,$b23c0023,$66003a54,$121c6100
    DC.L    $c39a6000,$d0b00c2e,$00140121,$6600e708,$610e8c42,$3ac64a2e,$02396600,$3a124e75
    DC.L    $6100cd40,$660e0242,$00070240,$0001e748,$84404e75,$702e6000,$3a326100,$d91a50ee
    DC.L    $023b6100,$cc86003d,$4e75611c
    DC.B    "DATA",0
    DC.B    $00,$61,$14
    DC.L    $42535300,$610e5445,$58540000,$6106434f,$44450000,$205f43ee,$046e6100,$4be812fc
    DC.L    $000a48e7,$400849ee,$046e121c,$617a4cdf,$10024e75,$41ee046e,$10c1121c,$b23c0009
    DC.L    $674cb23c,$00206746,$b23c002c,$670ab23c,$000a673a,$10c160e2,$101c43fa,$00380400
    DC.L    $0030653e,$671043fa,$00315300,$670843fa,$002e5300,$662c10fc,$002c082e,$0001021d
    DC.L    $660441ee,$046e121c,$10d966fc,$538810bc,$000a608e
    DC.B    "CODE",0
    DC.B    "DATA",0
    DC.B    $42,$53
    DC.L    $53007066,$6000396c,$61002eb2,$122cffff,$76016100,$2e2e720a,$4e756100,$dfd64a2e
    DC.L    $02386648,$2f086100,$1f7a205f,$48e73000,$6100c08c,$4cdf0030,$66100829,$0007000c
    DC.L    $670038e4,$16052404
    DC.B    "`BHz",0
    DC.B    $16,$16,$05
    DC.L    $45ee016a,$55056700,$c14e45ee,$01626000,$c14608e9,$0007000c,$6000e000,$6100c050
    DC.L    $660038cc,$08290007,$000c6700,$38c22f09,$6100cb16,$225f08e9,$0006000c,$23420008
    DC.L    $b629000d,$66003890,$6000dfd4,$b23c0023,$675c548d,$6100ccbc,$10050200,$0078672c
    DC.L    $34060242,$0018ed4a,$0246ff00,$004600c0,$8c42206e,$024c3086,$6100db90,$703c6000
    DC.L    $cb240046,$02008c05,$3ac64e75,$2a6e024c,$61000328,$b23c002c,$66e80006,$00203a86
    DC.L    $da058b1d,$121c6100,$cb58851d,$4e75121c,$6100caba,$6100e62c,$ee5a8c42,$610002fc
    DC.L    $b23c002c,$6600383c,$121c6100,$cb348c02,$3ac64e75,$6100ca96,$b4bc0000,$00ff6400
    DC.L    $fbd44a2e,$02386710,$4a2e0955,$670a3802,$6100423a,$534466f8,$122cffff,$50ee0113
    DC.B    "NuJ."
    DC.L    $01256706,$70656100,$381a3ac6,$b23c0023,$660037f4,$121c6100,$c13a6100,$ce504a2e
    DC.L    $02396600,$37c24e75,$6100dadc,$6100cace,$8c023ac6,$4e756100,$d6d66100,$ca46003d
    DC.B    "NuJ."
    DC.L    $02396600,$379eb23c,$00236600,$37b6121c,$6100c9ee,$61002c1a,$8c023ac6,$b4bc0000
    DC.L    $00106402,$4e75701d,$600037b4,$0c2e0014,$01216d00,$e4566100,$d6703afc,$4c403ac6
    DC.L    $6100c9f6,$00fdb23c,$002c6600,$376e121c,$6100ca66,$206e024c,$b23c003a,$670c8528
    DC.L    $0003e90a,$85280002,$4e75121c,$85280003,$6100ca46,$206e024c,$e90a8528,$00024e75
    DC.L    $0c2e0014,$01216d00,$e4023ac6,$206e024c,$5288102e,$0239673a,$b03c0003,$671eb03c
    DC.L    $00026600,$36feb23c,$00236600,$3716121c,$00100002,$6100c058,$6000cd6e,$b23c0023
    DC.L    $66003700,$121c0010,$00036100,$c0426000,$cd38b23c,$002367ce,$00100004,$4e756100
    DC.L    $01926100,$c95a003d,$4e750c2e,$00140121,$6dec6100,$017e6100,$c94600ff,$4e7545ee
    DC.L    $0b8250ee,$01137400,$760a4a2e,$02386608,$4a126704,$720a4e75,$b23c0027,$66047627
    DC.L    $121cb601,$6714b23c,$000a6716,$14c15202,$b43c0050,$66ea720a,$6008b63c,$000a6702
    DC.L    $121c4212,$4e7545ee,$0bd360b6,$6100c974,$8c023ac6,$4a2e0239,$66003648,$4e750c6e
    DC.L    $0003021c,$67024e75,$588f720a,$4e75121c,$61ec41ee,$03e86100,$28986600,$36623f01
    DC.L    $610a321f,$b23c002c,$67e44e75,$10280006,$b02e0116,$67003604,$4a2e0238,$671a6100
    DC.L    $bd866616
h0_4E4C:
    move.b $000C(a1),d0
    andi.b #144,d0
    bne.s h0_4E62
h0_4E56:
    bset.b #5,$000C(a1)
    beq.w h0_96D6
h0_4E60:
    rts
h0_4E62:
    moveq.l #44,d0
    bra.w h0_8486
    DC.B    $70,$2b,$60,$00,$36,$16 ; VIOLATION: orphaned code island at $4E68 is not reached from known entrypoints
    DC.B    $12,$1c,$60,$04 ; VIOLATION: orphaned code island at $4E6E is not reached from known entrypoints
    DC.B    $7a,$2c ; VIOLATION: orphaned code island at $4E72 is not reached from known entrypoints
    DC.L    $619041ee,$03e86100,$283c6600,$36061028,$0006b02e,$011667dc,$76010c2e,$00030239
    DC.L    $66027602,$3f013f03,$6100bd30,$4c9f0008,$670a226e,$01667800,$6100be0c,$6112321f
    DC.L    $1a01b23c,$002c67b2,$b23c003d,$67ac4e75
    DC.L    $082e0002,$021d6646,$b629000d,$66400829,$0005000c,$66380829,$0007000c,$66301029
    DC.L    $0017b02e,$01166726,$08e90004,$000c661c,$206e013e,$ba3c002c,$670808e9,$0002000c ; VIOLATION: orphaned code island at $4EC4 is not reached from known entrypoints
    DC.B    $60,$04
    DC.B    $52,$68,$00,$14,$33,$68,$00,$14,$00,$14,$4e,$75 ; VIOLATION: orphaned code island at $4F06 is not reached from known entrypoints
    DC.B    $30,$3c,$00,$2b,$60,$00,$35,$6e ; VIOLATION: orphaned code island at $4F12 is not reached from known entrypoints
    DC.B    $70,$00,$10,$2e,$02,$39,$8c,$3b,$00,$04,$4e,$75 ; VIOLATION: orphaned code island at $4F1A is not reached from known entrypoints
    DC.B    $40,$00,$40,$80 ; VIOLATION: orphaned code island at $4F26 is not reached from known entrypoints
h0_4F2A:
    move.l a5,$086E(a6)
    cmp.b #$5B,d1
    beq.w h0_4FDC
h0_4F36:
    moveq.l #0,d7
    lea.l $084E(a6),a3
    lea.l $08A0(a6),a0
    move.l a0,$0940(a6)
    pea.l -$0001(a4)
    bsr.w h0_53AE
h0_4F4C:
    movea.l (a7)+,a2
    bne.w h0_56B8
h0_4F52:
    btst #0,d7
    bne.s h0_4F8C
h0_4F58:
    cmp.b #$29,d1
    bne.w h0_500E
h0_4F60:
    btst #1,d7
    beq.w h0_5026
h0_4F68:
    tst.b $0009(a3)
    bne.w h0_5026
h0_4F70:
    move.b $0008(a3),d0
    bmi.w h0_5026
h0_4F78:
    moveq.l #16,d5
    or.b d0,d5
    move.b (a4)+,d1
    cmp.b #$2B,d1
    bne.s h0_4F8A
h0_4F84:
    bset #3,d5
    move.b (a4)+,d1
h0_4F8A:
    rts
h0_4F8C:
    cmp.b #$2C,d1
    beq.w h0_5014
h0_4F94:
    move.b (a4)+,d1
    cmp.b #$2E,d1
    bne.w h0_4FAC
h0_4F9E:
    move.l (a3),d2
    move.w $0004(a3),d3
    move.b $0006(a3),d4
    bra.w h0_1988
h0_4FAC:
    cmp.b #$9,d1
    beq.w h0_4FCA
h0_4FB4:
    cmp.b #$20,d1
    beq.w h0_4FCA
h0_4FBC:
    cmp.b #$2C,d1
    beq.s h0_4FCA
h0_4FC2:
    cmp.b #$A,d1
    bne.w h0_192A
h0_4FCA:
    movea.l a2,a4
    move.b -$0001(a4),d1
    bsr.w h0_1208
h0_4FD4:
    bsr.w h0_1930
h0_4FD8:
    bra.w h0_1208
h0_4FDC:
    moveq.l #0,d7
    lea.l $084E(a6),a3
h0_4FE2:
    swap.w d7
    bset #7,d7
    bne.w h0_56B8
h0_4FEC:
    lea.l $085E(a6),a3
    lea.l $08F0(a6),a0
    move.l a0,$0940(a6)
    move.b (a4)+,d1
h0_4FFA:
    cmp.b #$5D,d1
    beq.s h0_5034
h0_5000:
    cmp.b #$29,d1
    beq.s h0_5026
h0_5006:
    bsr.w h0_53AE
h0_500A:
    bne.w h0_56B8
h0_500E:
    cmp.b #$2C,d1
    bne.s h0_4FFA
h0_5014:
    move.b (a4)+,d1
    cmp.b #$5B,d1
    bne.s h0_5006
h0_501C:
    tst.b $000E(a3)
    bgt.s h0_4FE2
h0_5022:
    bra.w h0_56B8
h0_5026:
    tst.b $000E(a3)
    ble.w h0_56B8
h0_502E:
    move.b (a4)+,d1
    bra.w h0_504E
h0_5034:
    tst.b $000E(a3)
    bge.w h0_56B8
h0_503C:
    swap.w d7
    lea.l $084E(a6),a3
    lea.l $08A0(a6),a0
    move.l a0,$0940(a6)
    move.b (a4)+,d1
    bra.s h0_500E
h0_504E:
    tst.b $000E(a3)
    bge.s h0_5062
h0_5054:
    swap.w d7
    lea.l $084E(a6),a3
    lea.l $08A0(a6),a0
    move.l a0,$0940(a6)
h0_5062:
    move.l d7,d2
    andi.l #458759,d2
    move.l d2,d0
    swap.w d0
    lsl.w #3,d0
    or.w d2,d0
    add.w d0,d0
    add.w d0,d0
    moveq.l #48,d5
    btst #3,d7
    beq.s h0_5080
h0_507E:
    moveq.l #59,d5
h0_5080:
    btst #23,d7
    beq.w h0_5552
h0_5088:
    move.b $0121(a6),d4
    cmp.b #$20,d4
h0_5090:
    beq.w h0_3132
h0_5094:
    move.w #$1D0,d4
    move.l dat_50BA(pc,d0.w),d2
    or.w d2,d4
    swap.w d2
    move.l a5,-(a7)
    move.w d4,(a5)+
    jsr dat_50BA(pc,d2.w)
h0_50A8:
    movea.l (a7)+,a0
    btst #6,d4
    beq.s h0_50B4
h0_50B0:
    bclr #2,d4
h0_50B4:
    move.w d4,(a0)
    moveq.l #0,d0
    rts
dat_50BA:
    DC.B    $01,$20
    DC.L    $00010120,$00010100,$00010100,$00010120,$00010120,$000105fe,$000005fe,$00000120
    DC.L    $00050120,$00050100,$00050100,$00050120,$00050120,$000505fe,$000005fe,$00000120
    DC.L    $00050120,$00050100,$00050100,$00050120,$00050120,$000505fe,$000005fe,$00000120
    DC.L    $00050120,$00050100,$00050100,$00050120,$00050120,$000505fe,$000005fe,$00000162
    DC.L    $00010162,$000105fe,$000005fe,$000005fe,$000005fe,$000005fe,$000005fe,$00000162
    DC.L    $00010162,$000105fe,$000005fe,$000005fe,$000005fe,$000005fe,$000005fe,$00000162
    DC.L    $00010162,$000105fe,$000005fe,$000005fe,$000005fe,$000005fe,$000005fe,$00000162
    DC.L    $00010162,$000105fe,$000005fe,$000005fe,$000005fe,$000005fe,$000005fe,$00000887
    DC.L    $000108c7,$00027008,$d02e0856,$1d400858,$1d6e0857,$086951ee,$085a51ee,$085b47ee
    DC.L    $085e41ee,$08f02d48,$09400807,$00106704,$61000086,$08070011,$67046100,$006647ee
    DC.L    $084e41ee,$08a02d48,$09400807,$00026704,$610000fc,$08070000,$67046100,$011c4e75
    DC.L    $47ee085e,$41ee08f0,$2d480940,$08070010,$67046100,$00440807,$00116704,$61000024
    DC.L    $08070012,$67046100,$00c647ee,$084e41ee,$08a02d48,$09400807,$00006704,$610000da
    DC.B    "NuJ+",0
    DC.B    $09,$66,$0e
    DC.L    $08840007,$08070003,$66048a2b,$00084e75,$2413362b,$0004082e,$0007010f,$6740b63c
    DC.L    $0001661c,$2f0294ae,$023c202e,$086e90ae,$024c9480,$3042b1c2,$4cdf0004
    DC.B    $66,$20
h0_52A2:
    bra.s h0_52AA
    DC.B    $30,$42,$b1,$c2,$66,$18 ; VIOLATION: orphaned code island at $52A4 is not reached from known entrypoints
h0_52AA:
    tst.b $0006(a3)
    bne.s h0_52C2
h0_52B0:
    bsr.w h0_8DCE
h0_52B4:
    bne.s h0_52C2
h0_52B6:
    move.b #$1,$0007(a3)
    moveq.l #19,d0
    bsr.w h0_8808
h0_52C2:
    move.b $0007(a3),d0
    cmp.b #$3,d0
    beq.w h0_5694
h0_52CE:
    subq.b #1,d0
    beq.s h0_52F6
h0_52D2:
    bpl.s h0_52DA
h0_52D4:
    tst.b $012D(a6)
    bne.s h0_52F6
h0_52DA:
    ori.b #48,d4
    btst #3,d7
    beq.w h0_1AB0
h0_52E6:
    tst.b $0009(a3)
    bne.w h0_1AB0
h0_52EE:
    bset #0,d5
    bra.w h0_5706
h0_52F6:
    bset #5,d4
    bclr #4,d4
    btst #3,d7
    beq.w h0_1AD0
h0_5306:
    bra.w h0_56C4
    DC.B    $4a,$2b ; VIOLATION: orphaned code island at $530A is not reached from known entrypoints
    DC.L    $000b6622,$08840006,$700fc02b,$000ae858,$88407001,$c02b000c,$ea588840,$7003c02b
    DC.L    $000dee58,$88404e75
    DC.L    $08c40001,$2413362b,$0004102b,$00076642,$082e0000,$010e673a,$2f0294ae,$023c202e
    DC.L    $086e90ae,$024c9480,$3042b1c2,$4cdf0004,$66206006 ; VIOLATION: orphaned code island at $5334 is not reached from known entrypoints
    DC.L    $3042b1c2,$66184a2b,$00066612,$61003a58,$660c177c,$00010007,$70146100,$3484102b
    DC.L    $0007b03c,$00036700,$03045300,$67106a06,$4a2e012e,$660808c4,$00006000 ; VIOLATION: orphaned code island at $5368 is not reached from known entrypoints
    DC.B    $c7,$0c
    DC.B    $08,$84,$00,$00,$60,$00,$c7,$24 ; VIOLATION: orphaned code island at $53A6 is not reached from known entrypoints
h0_53AE:
    moveq.l #0,d3
    clr.l $046E(a6)
    bsr.w h0_177E
h0_53B8:
    bne.w h0_5462
h0_53BC:
    add.b d0,d0
    add.b d0,d0
    add.b d0,d0
    add.b d2,d0
    cmp.b #$2E,d1
    beq.s h0_540A
h0_53CA:
    cmp.b #$2A,d1
    beq.s h0_5404
h0_53D0:
    cmp.b #$8,d0
    bcc.s h0_53F0
h0_53D6:
    move.b d0,$000A(a3)
    move.b d3,$000B(a3)
    sf.b $000C(a3)
    sf.b $000D(a3)
    bset #2,d7
    bne.w h0_56B8
h0_53EE:
    rts
h0_53F0:
    subq.b #8,d0
    move.b d0,$0008(a3)
    move.b d3,$0009(a3)
    bset #1,d7
    bne.w h0_56B8
h0_5402:
    rts
h0_5404:
    sf.b $000C(a3)
    bra.s h0_5446
h0_540A:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    sf.b $000C(a3)
    cmp.b #$57,d1
    beq.s h0_5428
h0_541C:
    addq.b #1,$000C(a3)
    cmp.b #$4C,d1
    bne.w h0_56B8
h0_5428:
    move.b (a4)+,d1
    cmp.b #$2A,d1
    beq.s h0_5446
h0_5430:
    move.b d0,$000A(a3)
    sf.b $000D(a3)
    move.b d3,$000B(a3)
    bset #2,d7
    bne.w h0_56B8
h0_5444:
    rts
h0_5446:
    move.b d3,$000B(a3)
    move.b d0,$000A(a3)
    move.b (a4)+,d1
    bsr.w h0_5740
h0_5454:
    move.b d0,$000D(a3)
    bset #2,d7
    bne.w h0_56B8
h0_5460:
    rts
h0_5462:
    move.l $046E(a6),d0
    beq.w h0_5506
h0_546A:
    lea.l -$0001(a4),a0
    move.b $0473(a6),d0
    subq.b #2,d0
    beq.w h0_54D6
h0_5478:
    subq.b #1,d0
    bne.w h0_5506
h0_547E:
    move.b (a0)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b #$5A,d0
    bne.w h0_5506
h0_548E:
    move.b (a0)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    subi.b #68,d0
    sne.b d2
    beq.s h0_54E8
h0_549E:
    addq.b #3,d0
    beq.s h0_54E8
h0_54A2:
    cmp.b #$F,d0
    bne.w h0_5506
h0_54AA:
    st.b d3
h0_54AC:
    move.b (a0)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b #$43,d0
    bne.s h0_5506
h0_54BA:
    movea.l a0,a4
    move.b (a4)+,d1
    st.b $0008(a3)
    move.b d3,$0009(a3)
    ori.l #524296,d7
    bset #1,d7
    bne.w h0_56B8
h0_54D4:
    rts
h0_54D6:
    move.b (a0)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    moveq.l #0,d3
    cmp.b #$50,d0
    beq.s h0_54AC
h0_54E6:
    bra.s h0_5506
h0_54E8:
    move.b (a0)+,d0
    subi.b #48,d0
    bcs.s h0_5506
h0_54F0:
    cmp.b #$8,d0
    bcc.s h0_5506
h0_54F6:
    st.b d3
    movea.l a0,a4
    move.b (a4)+,d1
    andi.b #1,d2
    exg d0,d2
    bra.w h0_53BC
h0_5506:
    move.l a3,-(a7)
    bsr.w h0_0DB6
h0_550C:
    movea.l (a7)+,a3
    move.l d2,(a3)
    move.w d3,$0004(a3)
    move.b d4,$0006(a3)
    moveq.l #0,d0
    cmp.b #$2E,d1
    bne.s h0_5544
h0_5520:
    move.b (a4)+,d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    moveq.l #1,d0
    cmp.b #$57,d1
    beq.s h0_5542
h0_5530:
    moveq.l #2,d0
    cmp.b #$4C,d1
    beq.s h0_5542
h0_5538:
    moveq.l #3,d0
    cmp.b #$42,d1
    bne.w h0_56B8
h0_5542:
    move.b (a4)+,d1
h0_5544:
    move.b d0,$0007(a3)
    bset #0,d7
    bne.w h0_56B8
h0_5550:
    rts
h0_5552:
    move.w #$1D0,d4
    move.l h0_556E(pc,d0.w),d0
    or.w d0,d4
    swap.w d0
    move.l a5,-(a7)
    move.w d4,(a5)+
    jsr dat_5576(pc,d0.w)
h0_5566:
    movea.l (a7)+,a0
    btst #6,d4
    beq.s h0_5572
h0_556E:
    bclr #2,d4
h0_5572:
    move.w d4,(a0)
    rts
dat_5576:
    DC.B    $00,$18
    DC.L    $00000034,$000000ba,$000000ba,$00000078,$000000ba,$00004a2b,$00096600,$009c4a2b
    DC.L    $00086a00,$00947a3a,$558d508f,$3afcfffe
    DC.B    "NuJ+",0
    DC.B    $09,$66,$00
    DC.L    $00800c2b,$00020007,$67000076,$558d508f,$2413362b,$0004182b,$00060885,$00000807
    DC.L    $00036600,$00f07a28,$8a2b0008,$4a436b00,$433c3ac2,$4a2e0238,$660022cc
    DC.B    "NuJ+",0
    DC.B    $09
    DC.B    "f<J+",0
    DC.B    $0b
    DC.L    $66360807,$00036630,$422b0003
    DC.B    $61,$08
h0_5606:
    addq.w #4,a7
    movea.l (a7)+,a0
    move.w d4,(a0)
    rts
    DC.B    $8a,$2b ; VIOLATION: orphaned code island at $560E is not reached from known entrypoints
    DC.L    $0008780f,$c82b000a,$e85c4a2b,$000c6704,$08c4000b,$7003c02b,$000dee58,$88404e75
    DC.L    $0c2b0003,$00076660,$2413362b,$00040807,$00026700,$00500807,$00016700,$00480807
    DC.L    $00036600,$000c61b6,$61002250 ; VIOLATION: orphaned code island at $5630 is not reached from known entrypoints
    DC.B    $18,$02
h0_565E:
    bra.s h0_5606
    DC.L    $61b04a2e,$0238672a,$b63c0002,$67182413,$94ae023c,$202e086e,$90ae024c,$94806100
    DC.L    $22301802 ; VIOLATION: orphaned code island at $5660 is not reached from known entrypoints
    DC.B    $60,$80
    DC.B    $4a,$2e,$01,$07,$66,$e2,$70,$21,$61,$00,$2d,$f6,$4e,$75 ; VIOLATION: orphaned code island at $5686 is not reached from known entrypoints
h0_5694:
    bra.w h0_56B8
    DC.L    $08070000,$67046100,$fbd40807,$00026704,$6100fc60,$08070001,$67046100,$fbaa4e75 ; VIOLATION: orphaned code island at $5698 is not reached from known entrypoints
h0_56B8:
    moveq.l #91,d0
    bra.w h0_8482
h0_56BE:
    moveq.l #68,d0
    bra.w h0_8482
h0_56C4:
    tst.b $0238(a6)
    beq.s h0_5702
h0_56CA:
    tst.w d3
    bmi.w h0_98EE
h0_56D0:
    cmp.b #$2,d3
    beq.s h0_56F6
h0_56D6:
    move.w d4,-(a7)
    bclr #15,d4
    bsr.w h0_19EA
h0_56E0:
    move.w (a7)+,d4
    sub.l $023C(a6),d2
    move.l $086E(a6),d0
    sub.l $024C(a6),d0
    sub.l d0,d2
    move.w d2,(a5)+
    bra.w h0_78BC
h0_56F6:
    tst.b $0107(a6)
    bne.s h0_56D6
h0_56FC:
    moveq.l #33,d0
    bsr.w h0_8486
h0_5702:
    move.w d2,(a5)+
    rts
h0_5706:
    move.w d4,-(a7)
    tst.b $0238(a6)
    beq.s h0_573A
h0_570E:
    tst.w d3
    bmi.w h0_56BE
h0_5714:
    move.b $0006(a3),d4
    bne.s h0_573A
h0_571A:
    cmp.b #$2,d3
    bne.s h0_572C
h0_5720:
    tst.b $0107(a6)
    bne.s h0_572C
h0_5726:
    moveq.l #30,d0
    bsr.w h0_8486
h0_572C:
    sub.l $023C(a6),d2
    move.l $086E(a6),d0
    sub.l $024C(a6),d0
    sub.l d0,d2
h0_573A:
    move.l d2,(a5)+
    move.w (a7)+,d4
    rts
h0_5740:
    movem.l d2-d4/a2-a3,-(a7)
    bsr.w h0_0DD0
h0_5748:
    tst.w d3
    bmi.s h0_5774
h0_574C:
    tst.b $0238(a6)
    beq.s h0_577A
h0_5752:
    cmp.b #$2,d3
    bne.s h0_5774
h0_5758:
    tst.b d4
    bne.s h0_5774
h0_575C:
    tst.l d2
    bmi.s h0_5774
h0_5760:
    cmp.l #$9,d2
    bcc.s h0_5774
h0_5768:
    move.b dat_5782-1(pc,d2.w),d0 ; VIOLATION: invalid overlap: pc-relative reference targets +1 into instruction at $5780
    bmi.s h0_5774
h0_576E:
    movem.l (a7)+,d2-d4/a2-a3
    rts
h0_5774:
    moveq.l #92,d0
    bsr.w h0_8486
h0_577A:
    movem.l (a7)+,d2-d4/a2-a3
    moveq.l #0,d0
h0_5780:
    rts ; VIOLATION: invalid overlap: instruction bytes at +1 are referenced by reachable pc-relative operand
dat_5782:
    DC.B    $00,$01
    DC.L    $ff02ffff,$ff034881,$1236107e,$600441f1,$20002248,$34186738,$b2186534,$66f048e7
    DC.L    $4008121c,$48811236,$107eb218,$67f44a20,$67064cdf,$100260d6,$41fa4fa6,$4a301000
    DC.L    $67f0508f,$343120fe,$122cffff,$70004e75,$122cffff,$70ff4e75,$41fa008a
    DC.B    "aFg$A"
    DC.B    $fa,$00,$86
    DC.L    $613e6716,$41fa0089
    DC.B    "a6f."
    DC.L    $1d400133,$b23c002c,$6622121c,$60da1d40,$013260f0,$6100bec2,$4a826b12,$b4bc0000
    DC.L    $0008640a,$ee5a3d42,$013060d8
    DC.B    "Nup:`",0
    DC.B    $2c,$5c
    DC.L    $43ecffff,$12194881,$1236107e,$10186706,$b20067f0,$4e75b23c,$003d66f8,$2849121c
    DC.L    $4a106a04,$70004e75,$70004881,$1236107e,$141867c6,$5200b401,$66f6121c,$b0004e75
    DC.L    $494400ff
    DC.B    "ROUND",0
    DC.B    "NPMZ",0
    DC.B    "PREC",0
    DC.L    $58445300,$6100d280,$162e0239,$66061d7c,$00070239,$b63c0004,$6500d27e,$4a2e0238
    DC.L    $66522f08,$610006fa,$205f6600,$2bda48e7,$30006100,$b31e4cdf,$000c6700,$2b7e45ee
    DC.L    $016a2f02,$162e0239,$0603000b,$6100b3ec
    DC.B    "$_#R",0
    DC.B    $08,$13,$6a
    DC.L    $0004000e,$136a0005,$000f236a,$00060010,$336a000a,$0014122c,$ffff4e75,$6100b2dc
    DC.L    $66002b58,$08290006,$000c6600,$2b36162e,$02392f09,$61000692,$225f6600
    DC.B    "+r B )",0
    DC.B    $08
    DC.L    $b090663c,$1029000e,$b0280004,$66321029,$000fb028,$00056628,$20290010,$b0a80006
    DC.L    $661e3029,$0014b068,$000a6614,$b629000d,$66002aec,$08e90006,$000c122c,$ffff4e75
    DC.L    $60002ae4,$8c6e0130,$60000864,$3a063c3c,$f0488c6e,$01304845,$3a064845,$60000898
    DC.L    $3c3cf000,$8c6e0130,$3ac66100,$059c6620,$b23c002c,$66002ad4,$121c3602,$6100058a
    DC.L    $6600008e,$e74b8443,$ef4a3ac2,$600003c2,$41fa0118,$6100fddc
    DC.B    "g0:<@",0
    DC.B    $61,$00
    DC.L    $05c43ac5,$61000146,$70fd6100,$bd40b23c,$002c6600,$2a96121c,$6100054e,$662cef4a
    DC.L    $206e024c,$85680002,$4e756100,$c96cb23c,$002c6600,$2a76121c,$ec5a0042,$a0003ac2
    DC.L    $610000a6,$703d6000,$bd0441fa,$00be6100,$fd826616,$61000096,$206e024c,$ec5a08c2
    DC.L    $000f3142,$00026000,$c9307057,$60002a60,$3a3c6000,$6100054e,$ef4b8a43,$3ac56100
    DC.L    $00cc703d,$6100bcc6,$0c2e0005,$02396702,$4e75b23c,$007b66f8,$121cb23c,$00236726
    DC.L    $6100bd24,$663c4a00,$66380242,$0007e90a,$08c2000c,$206e024c,$85680002,$b23c007d
    DC.L    $6620121c,$4e75121c,$6100bc4a,$b4bcffff,$ffc06d0e,$b4bc0000,$003f6e06,$0242007f
    DC.L    $60d27061,$600029e8,$61000062,$7038c045,$51406702
    DC.B    "Nu n"
    DC.L    $024c0828,$00020002,$67024e75,$705f6000,$29c6000c
    DC.B    "CONTROL",0
    DC.L    $0004000a
    DC.B    "FPCR",0
    DC.B    $00,$00,$04
    DC.L    $000a4650,$49415200,$0001000a
    DC.B    "FPSR",0
    DC.B    $00,$00,$02
    DC.L    $000a4941,$44445200,$0001000c
    DC.B    "STATUS",0
    DC.B    $00
    DC.L    $00020000,$b23c0023,$6630162e,$0239b63c,$00046526,$121c162e,$02396100,$04806600
    DC.L    $29620603,$00f51003,$162e0239,$20426100
    DC.B    "V8f z<`",0
    DC.L    $06506100,$bd42ba7c,$00106410,$704e142e,$02390500,$6606705e,$61002934
    DC.B    "Nu<<"
    DC.L    $f0008c6e,$01303ac6,$102e0239,$b03c0003,$6700011a,$610001fa,$3a3ce000,$610000ce
    DC.L    $662a3ac5,$b23c002c,$660028e0,$121c6100,$ff7c7034,$6100bb76,$61000090,$670c3a28
    DC.L    $00026100,$00943145,$00024e75,$610003c2,$662a08c5,$000be90a,$8a023ac5,$b23c002c
    DC.L    $660028a8,$121c6100,$ff447034,$6100bb3e,$61586706,$08e80004,$00024e75,$3afcd000
    DC.L    $6100ff2a,$707d6100,$bb24b23c,$002c6600,$287a121c,$6100037a,$6614206e,$024c0242
    DC.L    $000fe94a,$08c2000b,$85680002
    DC.B    "Nu:<"
    DC.L    $d0006100,$0038660c,$611e206e,$024c3145,$00024e75,$70396000
    DC.B    "(fp8"
    DC.L    $c045206e,$024cb07c,$00204e75,$1005e04d,$7407e210,$e35551ca,$fffa08c5,$000c4e75
    DC.L    $610002da,$67024e75,$360205c5,$b23c002f,$6608121c,$610002ba,$60eeb23c,$002d661c
    DC.L    $121c6100,$02acb443,$6d0c07c5,$5243b642,$6ff83602,$60d67039,$60002804,$70004e75
    DC.L    $3a3ca000,$41fafe38,$6100fafc,$6632ec5a,$8a42b23c,$002f6612,$121c41fa,$fe226100
    DC.L    $fae667ea,$70396000,$27dab23c,$002c6600,$27ae121c,$3ac56100,$fe4870ff,$6000ba42
    DC.L    $3ac56100,$fe3c70ff,$6100ba36,$b23c002c,$6600278c,$121c3a3c,$800041fa,$fde26100
    DC.L    $faa666c0,$ec5a8a42,$b23c002f,$660e121c,$41fafdcc,$6100fa90,$67ea60a8,$206e024c
    DC.L    $31450002,$4e758c6e,$0130102e,$02396704,$61000052,$3ac6b23c,$00236600,$274a121c
    DC.L    $6100b9a6,$4a826b08,$b4bc0000,$00406506,$701d6100,$274e0242,$003f0042,$5c00b23c
    DC.L    $002c6600,$271a121c,$36026100,$01c4ef4a,$86423ac3,$4e758c6e,$01304846,$42462ac6
    DC.L    $720a4e75,$0c2e0007,$0239670e,$4a2e0239,$660026d4,$1d7c0007,$02394e75,$0c2e003c
    DC.L    $01216700,$000c0c2e,$00280121,$6600d3a0,$3a063c3c,$f0008c6e,$01304845,$3a064845
    DC.L    $6100017a,$661eec5a,$8a42ed5a,$61b6b23c,$002c6606,$121c6100,$01583ac6,$ef5a8a42
    DC.L    $3ac54e75,$08c5000e,$610001ae,$2ac56100,$fd3070fd,$6100b92a,$b23c002c,$66002680
    DC.L    $121c6100,$012cef4a,$206e024c,$85680002,$4e758c6e,$01304a2e,$01256706,$70656100
    DC.L    $26824a2e,$02396600,$263e6100,$b8d6006c,$4e758c6e,$01304a2e,$01256706,$70656100
    DC.B    "&bJ."
    DC.L    $02396600,$261e6100,$b8b60034,$4e753a06,$3c3cf040,$8c6e0130,$48453a06,$48456000
    DC.L    $08548c6e,$01303ac6,$7a306100,$00cc662e,$ec5a8a42,$6100ff0a,$b23c002c,$660025fc
    DC.L    $121c6100,$00a88a42,$b23c003a,$6600c5e6,$121c6100,$0098ef4a,$8a423ac5,$4e7508c5
    DC.L    $000e6100,$00f03ac5,$6100fc72,$70fd6100,$b86cb23c,$002c6600,$25c2121c,$6100006e
    DC.L    $3a02b23c,$003a6600,$c5ac121c,$6100005e,$ef4a8a42,$206e024c,$8b680002,$4e753a06
    DC.L    $3c3cf078,$8c6e0130,$48453a06,$48452ac5,$6000ee5a,$3a063c3c,$f0008c6e,$01304845
    DC.L    $3a064845,$61000032,$660eec5a,$8a426100,$fe703ac6,$3ac54e75,$08c5000e,$61000076
    DC.L    $2ac56100,$fbf870fd,$6000b7f2,$610a6602
    DC.B    "NupW`",0
    DC.B    $25,$64
    DC.L    $1001204c,$48801036,$007eb03c,$00466634,$10184880,$1036007e,$b03c0050,$66261418
    DC.L    $04020030,$651eb43c,$00086418,$48827000,$101843fa,$48104a31,$00006708,$12002848
    DC.L    $b0004e75,$70ff4e75,$6100b814,$660c4a00,$67082848,$122cffff,$70ff4e75,$7000102e
    DC.L    $02396700,$24c6d040,$8a7b0002,$4e751800,$10000000,$14000c00,$04000800,$41ee087e
    DC.L    $780042a0,$42a042a0,$4883b23c,$00246700,$014cb23c,$003a6700,$0144b23c,$002d6700
    DC.L    $0022b23c,$00306506,$b23c003a,$65306100,$b238b63c,$000f6522,$b63c0013,$641c7000
    DC.L    $4e75121c,$61b66610,$20420603,$00f56100,$520a0403,$00f54a00
    DC.B    "NupdNu?"
    DC.B    $03
    DC.L    $568850c2,$760178ff,$7a007c00,$04010030,$660e4a05,$660ab63c,$00016714,$53446010
    DC.L    $610000c0,$50c5b63c,$00ff6602,$7600d843,$121cb23c,$002e660a,$b63c0001,$664e1605
    DC.L    $60eeb23c,$00306506,$b23c003a,$65beb23c,$00456706,$b23c0065,$66327600,$121cb23c
    DC.L    $002d57c2,$6602121c,$b23c0030,$6516b23c,$003a6410,$04010030,$024100ff,$c6fc000a
    DC.L    $d64160e2,$4a026702,$4443d843,$41ee0872,$7c004a05
    DC.B    "g6JDj"
    DC.B    $06,$08,$d0
    DC.L    $00064444,$50c20284,$0000ffff,$88fc03e8,$3a044244,$484488fc,$00646128
    DC.B    "BDHD"
    DC.L    $88fc000a,$611e4244,$48446118,$122cffff,$41ee0872,$361f6100,$50580643,$000b2408
    DC.B    "J@Nu"
    DC.L    $12044a02,$67088318,$52064602,$4e75bc3c,$00096706,$e9498310,$46024e75,$244c43fa
    DC.L    $b342121c,$48816b0c,$14311000,$6b067004,$612860ee,$7000103b,$30196714,$74003f00
    DC.L    $b07c0020,$6d027010,$9157610e,$301f66ee,$60a45850,$40200040,$00002f09,$4a40671a
    DC.B    "H@B@"
    DC.L    $d1004840,$41ee087e,$2248d388,$d388d388
    DC.B    "e(S@f"
    DC.B    $ee,$d1,$00
    DC.L    $488248c2,$41ee087e,$2020d182,$20807400,$2020d182,$20802020,$d1826506,$2080225f
    DC.B    "Nup]a",0
    DC.B    $23,$04
    DC.B    $22,"_Nu BH"
    DC.B    $83
    DC.L    $103b3013,$6b083ad8,$530066fa,$4e757000,$10183ac0,$4e75ff01,$02040602,$06004a2e
    DC.L    $0123660a,$0c2e0014,$01216600,$cf7a4a2e,$01256706,$70656100,$22c2102e,$02396716
    DC.L    $b03c0002,$6710b03c,$00036600,$227208c6,$00066000,$be506000,$becc4a2e,$0123660a
    DC.L    $0c2e0014,$01216600,$cf3e4a2e,$01256706,$70656100,$22863a06,$3c3cf048,$48453a06
    DC.B    "HEJ."
    DC.L    $02396600,$22366100,$b5484845,$8a024845,$2ac5b23c,$002c6600,$223a121c,$6100bf02
    DC.L    $6604548d,$4e755582,$4a436b00,$36b26100,$167c3ac2,$4e750c2e,$003c0121,$670a0c2e
    DC.L    $00280121,$66000014,$4a2e0125,$67067065,$61002224,$3afcf518
    DC.B    "NuJ."
    DC.L    $0123660a,$0c2e001e,$01216600,$ceba4a2e,$01256706,$70656100,$22023ac6,$3afc2400
    DC.L    $4e750c2e,$003c0121,$670a0c2e,$00280121,$6600ce94,$4a2e0125,$67067065,$610021dc
h0_62AC:
    move.w d6,(a5)+
    bsr.w h0_187E
h0_62B2:
    move.b d5,d0
    andi.b #56,d0
    cmp.b #$10,d0
    bne.s h0_62CC
h0_62BE:
    andi.b #7,d5
    movea.l $024C(a6),a0
    or.w (a0),d5
    move.w d5,(a0)
    rts
h0_62CC:
    moveq.l #104,d0
    bra.w h0_8486
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $62D2 is not reached from known entrypoints
    DC.L    $003c0121,$670a0c2e,$00280121,$6600ce50,$4a2e0125,$67067065,$61002198,$3ac64e75
    DC.L    $0c2e003c
    DC.B    $01,$21
h0_62FA:
    beq.s h0_6306
h0_62FC:
    cmpi.b #40,$0121(a6)
    bne.w h0_6318
h0_6306:
    tst.b $0125(a6)
    beq.s h0_6312
h0_630C:
    moveq.l #101,d0
    bsr.w h0_8486
h0_6312:
    move.w #$F508,d6
    bra.s h0_62AC
h0_6318:
    tst.b $0123(a6)
    bne.s h0_6328
h0_631E:
    cmpi.b #30,$0121(a6)
    bne.w h0_3132
h0_6328:
    tst.b $0125(a6)
    beq.s h0_6334
h0_632E:
    moveq.l #101,d0
    bsr.w h0_8486
h0_6334:
    move.w #$3000,d2
    move.w d6,(a5)+
    bsr.w h0_6398
h0_633E:
    cmp.b #$2C,d1
    bne.w h0_8462
h0_6346:
    move.b (a4)+,d1
    cmp.b #$23,d1
    bne.w h0_846A
h0_6350:
    move.b (a4)+,d1
    move.w d2,-(a7)
    bsr.w h0_16CC
h0_6358:
    move.w (a7)+,d3
    tst.b $0123(a6)
    sne.b d0
    andi.l #8,d0
    ori.b #7,d0
    tst.l d2
    bmi.s h0_6372
h0_636E:
    cmp.l d0,d2
    ble.s h0_637A
h0_6372:
    moveq.l #89,d0
    bsr.w h0_8486
h0_6378:
    moveq.l #0,d2
h0_637A:
    lsl.w #5,d2
    or.w d3,d2
    cmp.b #$2C,d1
    beq.s h0_6388
h0_6384:
    move.w d2,(a5)+
    rts
h0_6388:
    move.b (a4)+,d1
    bset #11,d2
    move.w d2,(a5)+
    bsr.w h0_16E0
h0_6394:
    ori.b #$4E75,-(a4)
h0_6398:
    cmp.b #$23,d1
    beq.s h0_640C
h0_639E:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$53,d1
    beq.s h0_63EA
h0_63AA:
    cmp.b #$44,d1
    bne.s h0_6406
h0_63B0:
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.s h0_6406
h0_63B8:
    cmp.b #$8,d1
    bcs.s h0_63E0
h0_63BE:
    cmp.b #$16,d1
    beq.s h0_63CA
h0_63C4:
    cmp.b #$36,d1
    bne.s h0_6406
h0_63CA:
    move.b (a4)+,d1
    cmp.b #$43,d1
    beq.s h0_63D8
h0_63D2:
    cmp.b #$63,d1
    bne.s h0_6406
h0_63D8:
    ori.w #1,d2
h0_63DC:
    move.b (a4)+,d1
    rts
h0_63E0:
    bset #3,d1
    or.b d1,d2
    move.b (a4)+,d1
    rts
h0_63EA:
    move.b (a4)+,d1
    cmp.b #$46,d1
    beq.s h0_63F8
h0_63F2:
    cmp.b #$66,d1
    bne.s h0_6406
h0_63F8:
    move.b (a4)+,d1
    cmp.b #$43,d1
    beq.s h0_63DC
h0_6400:
    cmp.b #$63,d1
    beq.s h0_63DC
h0_6406:
    moveq.l #89,d0
    bra.w h0_8482
h0_640C:
    move.b (a4)+,d1
    move.w d2,-(a7)
    bsr.w h0_16CC
h0_6414:
    tst.b $0123(a6)
    sne.b d0
    andi.l #8,d0
    ori.b #7,d0
    tst.l d2
    bmi.s h0_642C
h0_6428:
    cmp.l d0,d2
    ble.s h0_6434
h0_642C:
    moveq.l #89,d0
    bsr.w h0_8486
h0_6432:
    moveq.l #0,d2
h0_6434:
    or.w (a7)+,d2
    bset #4,d2
    rts
    DC.L    $4a2e0123,$660a0c2e,$00140121,$6600cce8,$4a2e0125,$67067065,$61002030,$343c3400
    DC.L    $6000feda,$4a2e0123,$660a0c2e,$00140121,$6600ccc4,$4a2e0125,$67067065,$6100200c
    DC.L    $3ac63afc,$a0006100,$b25c00fc ; VIOLATION: orphaned code island at $643C is not reached from known entrypoints
    DC.B    "NuJ."
    DC.L    $0123660a,$0c2e001e,$01216600,$cc9a4a2e,$01256706,$70656100,$1fe23afc,$f0003406
    DC.L    $6100feea,$3ac2b23c,$002c6600,$1faa121c,$6100b222,$00244e75,$0c2e001e,$01216600
    DC.L    $cc664a2e,$01256706,$70656100,$1fae3afc,$f000343c,$01006048,$4a2e0123,$660a0c2e
    DC.L    $001e0121,$6600cc40,$4a2e0125,$67067065,$61001f88,$3afcf000
    DC.B    "aXf",$22
    DC.L    $08c20009,$3ac2b23c,$002c6600,$1f4e121c,$6100f5ea
    DC.B    "p?J."
    DC.L    $01236602,$70246000,$b1dc7400,$4a2e0239,$67001f18,$3ac26100,$f5cc7024,$6100b1c6
    DC.L    $b23c002c,$66001f1c,$121c6112,$660a206e,$024c8568,$00024e75,$70586000,$1f2a41fa
    DC.L    $004e6100,$f2266644,$10026a1e,$4a2e0123,$660a0c2e,$00140121,$6600cbb8,$4a2e0125
    DC.L    $67067065,$61001f00,$60100800,$0006670a,$0c2e001e,$01216600,$cb9a4202,$d442d442
    DC.L    $0200003f,$b02e0239,$66001ea0,$4e750008,$41430000,$17820008,$42414300,$1d820008
    DC.L    $42414400,$1c820008,$43414c00,$14810008,$43525000,$13040008,$44525000,$1184000a
    DC.B    "MMUSR",0
    DC.B    $18,$02
    DC.L    $000a5043,$53520000,$19820008,$50535200,$18020008,$53434300,$16810008,$53525000
    DC.L    $12040008,$54430000,$10030008,$54543000,$02430008,$54543100,$03430008,$56414c00
    DC.L    $2b810000,$4a2e0123,$660a0c2e,$00140121,$6600caf8,$4a2e0125,$67067065,$61001e40
    DC.L    $6100b09c,$006c4e75,$4a2e0123,$660a0c2e,$00140121,$6600cad4,$4a2e0125,$67067065
    DC.L    $61001e1c,$6100b078,$00344e75,$4a2e0123,$660a0c2e,$00140121,$6600cab0,$4a2e0125
    DC.L    $67067065,$61001df8,$3a063c3c,$f0404845,$3a064845,$2ac56100,$bcd250ee,$023b6100
    DC.L    $b038003d,$4e750806,$000f6700,$002e0c2e,$00280121,$66000042,$4a2e0125,$67067065
    DC.L    $61001dbc,$08060009,$66083c3c,$f5486000,$fbd43c3c,$f5686000,$fbcc0c2e,$003c0121
    DC.L    $6600ca48,$4a2e0125,$67067065,$61001d90,$0046f588,$6000fbae,$4a2e0123,$660a0c2e
    DC.L    $001e0121,$6600ca24,$4a2e0125,$67067065,$61001d6c,$4a2e0239,$66001d28,$3afcf000
    DC.L    $34066100,$fc6c3ac2,$b23c002c,$66001d2c,$121c6100,$afa40024,$b23c002c,$66001d1c
    DC.L    $121cb23c,$00236600,$1d1a121c,$6100af76,$4a826b08,$b4bc0000,$00086508,$701d6100
    DC.L    $1d1e7400,$ec5ab23c,$002c6614,$121c3602,$6100aff0,$08c30008,$02420007,$eb4a8443
    DC.L    $206e024c,$85680002
    DC.B    "NuJ."
    DC.L    $0123660a,$0c2e0014,$01216600,$c9924a2e,$01256706,$70656100,$1cda3afc,$f0783ac6
    DC.L    $6000e57e,$4a2e0123,$660a0c2e,$00140121,$6600c96c,$4a2e0125,$67067065,$61001cb4
    DC.L    $3afcf000,$6100afa4,$66244a00,$671a363c,$2c008602,$3ac3b23c,$002c6600,$1c72121c
    DC.L    $6100aeea,$00244e75,$700e6000,$1c864881,$1236107e,$b23c0056,$66ee121c,$48811236
    DC.L    $107eb23c,$004166e0,$121c4881,$1236107e,$b23c004c,$66d2121c,$3afc2800,$60b80c2e
    DC.L    $00200121,$6600c8f8,$3ac64e75,$0c2e003c,$01216700,$000c0c2e,$00200121,$6600c8e0
    DC.L    $4a2e0125,$67067065,$61001c28,$b23c0023,$66001c04,$121c3afc,$f8003ac6,$6100b22a
    DC.L    $6000bef4,$0c2e0020,$01216600,$c8b26100,$e6963afc,$f8003ac6,$6100ae52,$0065206e
    DC.L    $024c3010,$02000038,$6618b23c,$003a6600,$bbb8121c,$6100aeb6,$206e024c,$85280003
    DC.L    $600608e8,$00000002,$b23c002c,$66001ba0,$121c6100,$ae98206e,$024ce90a,$85280002
    DC.L    $4e750c2e,$003c0121,$670a0c2e,$00280121,$6600c84c,$4a2e0125,$67067065,$61001b94
    DC.L    $41fa001c,$6100ee90,$8c423ac6,$4e7561d2,$b23c002c,$66001b58,$121c6000,$f99e0008
    DC.L    $42430000,$00c00008,$44430000,$00400008,$49430000,$00800008,$4e430000,$00000000
    DC.L    $0c2e003c,$01216700,$000c0c2e,$00280121,$6600c7ec,$3ac66100,$af32b23c,$002c6600
    DC.L    $1b0e121c,$10050200,$003fb03c,$0039676a,$02000030,$b03c0010,$66001af0,$3f056100
    DC.L    $af0a3005,$02000038,$b03c0018,$66301005,$02400007,$e8580040,$80003ac0,$3a1f08c5
    DC.L    $00050805,$00036700,$1ac20245,$0027206e,$024c3010,$0240ffc0,$8a403085,$4e753005
    DC.L    $0240003f,$b03c0039,$66001aa0,$3a1f0805,$000367da,$02450007,$60d46100,$aeae3005
    DC.L    $02400038,$b03c0010,$660a7018,$02450007,$8a4060ba,$b03c0018,$66001a70,$700860ec
    DC.L    $70376000,$1a8a1401,$b23c0022,$6706b23c,$002766ec,$244c121c,$b23c000a,$67e2b202
    DC.L    $66f4121c,$b20267ee,$280c988a,$5344b23c,$002c6600,$1a3a121c,$1601b23c,$00276706
    DC.L    $b23c0022,$66ba5344,$6506b50c,$67f84e75,$700ac141,$b0036606,$528c121c,$70004e75
    DC.L    $61a457c0,$600000d8,$619c56c0,$600000d0,$6100aa5c,$671e6100,$a1626618,$4a2e0238
    DC.L    $67121029,$000c0800,$00076708,$02000040,$b03c0040,$4e7541ee,$03e86100,$0c286600
    DC.L    $19f261cc,$57c06000,$009641ee,$03e86100,$0c146600,$19de61b8,$56c06000,$008250ee
    DC.L    $01586100,$a2fe51ee,$01584a43,$6b2c4a04
    DC.B    "f(Nua"
    DC.B    $e8,$b6,$3c
    DC.L    $0002671e,$4e7550ee,$01586100,$a2de51ee,$01584a43,$6b0cb63c,$00016706,$4a046602
    DC.B    "Nup>`",0
    DC.B    $19,$90
    DC.L    $61dc1d7c,$003d083b,$2d42083c
    DC.B    "Nup3`",0
    DC.B    $19,$7c
h0_6B08:
    move.w #$34,d0
    bra.w h0_846E
    DC.B    $61,$e2,$5e,$c0,$60,$1c ; VIOLATION: orphaned code island at $6B10 is not reached from known entrypoints
    DC.B    $61,$dc,$5c,$c0,$60,$16 ; VIOLATION: orphaned code island at $6B16 is not reached from known entrypoints
    DC.B    $61,$d6,$5d,$c0,$60,$10 ; VIOLATION: orphaned code island at $6B1C is not reached from known entrypoints
    DC.B    $61,$d0,$5f,$c0,$60,$0a ; VIOLATION: orphaned code island at $6B22 is not reached from known entrypoints
    DC.B    $61,$ca,$57,$c0,$60,$04 ; VIOLATION: orphaned code island at $6B28 is not reached from known entrypoints
    DC.B    $61,$c4 ; VIOLATION: orphaned code island at $6B2E is not reached from known entrypoints
    DC.L    $56c0526e,$087e4a00,$67086100,$0170720a
    DC.B    $4e,$75
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $6B42 is not reached from known entrypoints
    DC.L    $01686100,$9ca83e2e,$087e6100,$9b5c66b4
    DC.B    "atglJ"
    DC.B    $82,$67,$18
    DC.L    $b2bc454c
    DC.B    "SEf`"
    DC.L    $b4bc4946,$00006658,$be6e087e,$67c86050
    DC.L    $b2bc454c,$534567f0,$b2bc454e,$44436712,$b2bc454e,$444d661e,$4a2e0101,$67326000 ; VIOLATION: orphaned code island at $6B74 is not reached from known entrypoints
    DC.B    $07,$00
    DC.B    $30,$2e,$08,$7e,$53,$6e,$08,$7e,$be,$40,$66,$22,$60,$96 ; VIOLATION: orphaned code island at $6B96 is not reached from known entrypoints
    DC.B    $61,$00,$00,$e0,$60,$1a ; VIOLATION: orphaned code island at $6BA4 is not reached from known entrypoints
    DC.B    $48,$41 ; VIOLATION: orphaned code island at $6BAA is not reached from known entrypoints
    DC.L    $b27c4946,$66124841,$41fa08b2,$30186708,$b24066f8,$526e087e,$61009c2a
    DC.B    $60,$84
h0_6BCA:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.w h0_6C66
h0_6BD4:
    cmp.b #$9,d1
    beq.s h0_6C08
h0_6BDA:
    cmp.b #$20,d1
    beq.s h0_6C08
h0_6BE0:
    cmp.b #$2A,d1
    beq.w h0_6C66
h0_6BE8:
    cmp.b #$3B,d1
    beq.s h0_6C66
h0_6BEE:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.s h0_6C66
h0_6BF6:
    cmp.b #$9,d1
    beq.s h0_6C08
h0_6BFC:
    cmp.b #$20,d1
    beq.s h0_6C08
h0_6C02:
    cmp.b #$3A,d1
    bne.s h0_6BEE
h0_6C08:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.s h0_6C66
h0_6C10:
    cmp.b #$9,d1
    beq.s h0_6C08
h0_6C16:
    cmp.b #$20,d1
    beq.s h0_6C08
h0_6C1C:
    cmp.b #$2A,d1
    beq.s h0_6C66
h0_6C22:
    cmp.b #$3B,d1
    beq.s h0_6C66
h0_6C28:
    lea.l $05A8(a6),a0
    clr.l -(a0)
    clr.l -(a0)
    moveq.l #7,d0
    bra.s h0_6C4E
h0_6C34:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.s h0_6C5E
h0_6C3C:
    cmp.b #$9,d1
    beq.s h0_6C5E
h0_6C42:
    cmp.b #$20,d1
    beq.s h0_6C5E
h0_6C48:
    cmp.b #$2E,d1
    beq.s h0_6C5E
h0_6C4E:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    move.b d1,(a0)+
    dbf.w d0,h0_6C34
h0_6C5A:
    moveq.l #0,d0
    rts
h0_6C5E:
    movem.l $05A0(a6),d1-d2
    moveq.l #-1,d0
h0_6C66:
    rts
    DC.L    $302e087e,$67184a2e,$0101670a,$246e0882,$b06a000e,$6708536e,$087e6000 ; VIOLATION: orphaned code island at $6C68 is not reached from known entrypoints
    DC.B    $fe,$b6
    DC.B    $70,$30,$60,$00,$17,$fc ; VIOLATION: orphaned code island at $6C86 is not reached from known entrypoints
    DC.L    $302e087e,$67144a2e,$0101670a,$246e0882,$b06a000e,$67046000 ; VIOLATION: orphaned code island at $6C8C is not reached from known entrypoints
    DC.B    $fe,$9e
    DC.B    $70,$31,$60,$00,$17,$dc ; VIOLATION: orphaned code island at $6CA6 is not reached from known entrypoints
    DC.L    $4a2e0126 ; VIOLATION: orphaned code island at $6CAC is not reached from known entrypoints
    DC.B    "g",$22,"J."
    DC.L    $0238661c,$4a2e0101,$67064a2e,$01176710,$302e087e,$06000030,$1d40083b,$600025ce
    DC.B    "Nu",$22,"<",0
    DC.B    $00,$13,$88
    DC.L    $3d41014e,$610023d8,$2d48014a
    DC.B    "Nup6`",0
    DC.B    $17,$98
    DC.L    $4a2e0101,$66f44aae,$089066ee,$6100be04,$246e0172,$48e7000c,$61009e7e,$56c04cdf
    DC.L    $30004a2e,$02386600,$00ee4a00,$67001718,$76084284,$61009f94,$48690008,$102e0239
    DC.L    $670cb03c,$00016706,$08e90003,$000c206e,$014a0c6e,$0110014e,$6402618a,$225f2288
    DC.L    $42a80008,$43e80010,$20892149,$00042148,$000c2d49,$014a046e,$0010014e,$26486100
    DC.L    $9a886100,$99246600,$fd906130,$6100fe4c,$67ecb2bc
    DC.B    "ENDMf"
    DC.B    $e4,$4a,$82
    DC.L    $66e0206b,$000c216e,$014a0004,$720a082e,$0000014d,$6708536e,$014e52ae,$014a4e75
    DC.L    $0c6e0102,$014e6434,$206b000c,$216e014a,$00046100,$ff16226b,$000c2348,$00082748
    DC.L    $000c43e8,$000c2089,$42a80004,$42a80008,$700cd0c0,$d1ae014a,$916e014e,$206e014a
    DC.L    $224c720a,$101910c0,$b20066f8,$2d48014a,$2409948c,$956e014e,$4e754a00,$66001630
    DC.L    $0c290008,$000d6600,$162208e9,$0006000c,$66001618,$61009aba,$61009872,$6600fcde
    DC.L    $6100fd9c,$67eeb2bc
    DC.B    "ENDMf"
    DC.B    $e6,$4a,$82
    DC.L    $66e2720a
    DC.B    $4e,$75
h0_6E42:
    move.l #$1F40,d1
    move.w d1,$0886(a6)
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_6E50:
    move.l a0,$0888(a6)
    rts
h0_6E56:
    moveq.l #78,d0
    bra.w h0_846E
h0_6E5C:
    cmpi.w #580,$0886(a6)
    bcs.s h0_6E56
h0_6E64:
    movem.l d1/a1,-(a7)
    btst.b #3,$000C(a1)
    beq.s h0_6E76
h0_6E70:
    bsr.w h0_0C64
h0_6E74:
    bra.s h0_6E7A
h0_6E76:
    bsr.w h0_0C44
h0_6E7A:
    movem.l (a7)+,d1/a1
    tst.b $0238(a6)
    beq.s h0_6E8E
h0_6E84:
    btst.b #6,$000C(a1)
    beq.w h0_844E
h0_6E8E:
    moveq.l #87,d0
    cmp.b #$A,d1
    beq.s h0_6EAC
h0_6E96:
    cmp.b #$9,d1
    beq.s h0_6EAC
h0_6E9C:
    cmp.b #$20,d1
    beq.s h0_6EAC
h0_6EA2:
    cmp.b #$2E,d1
    bne.w h0_8446
h0_6EAA:
    moveq.l #0,d0
h0_6EAC:
    movea.l $0888(a6),a0
    sf.b $000C(a0)
    move.l $0882(a6),(a0)
    move.l a0,$0882(a6)
    move.w $0880(a6),$000A(a0)
    movea.l $0008(a1),a1
    move.l a1,$0004(a0)
    move.l (a1),$0010(a0)
    move.w $087E(a6),$000E(a0)
    lea.l $0008(a0),a1
    clr.w (a1)
    lea.l $0116(a0),a0
    move.b d0,(a0)+
    bne.s h0_6EFE
h0_6EE2:
    subq.l #1,a0
h0_6EE4:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.s h0_6EFE
h0_6EEC:
    cmp.b #$9,d1
    beq.s h0_6EFC
h0_6EF2:
    cmp.b #$20,d1
    beq.s h0_6EFC
h0_6EF8:
    move.b d1,(a0)+
    bra.s h0_6EE4
h0_6EFC:
    move.b (a4)+,d1
h0_6EFE:
    clr.b (a0)+
h0_6F00:
    cmp.b #$A,d1
    beq.w h0_6F88
h0_6F08:
    cmp.b #$2A,d1
    beq.s h0_6F88
h0_6F0E:
    cmp.b #$3B,d1
    beq.s h0_6F88
h0_6F14:
    cmp.b #$9,d1
    beq.s h0_6F20
h0_6F1A:
    cmp.b #$20,d1
    bne.s h0_6F24
h0_6F20:
    move.b (a4)+,d1
    bra.s h0_6F00
h0_6F24:
    addq.w #1,(a1)
    cmp.b #$2C,d1
    beq.s h0_6F72
h0_6F2C:
    cmp.b #$A,d1
    beq.s h0_6F72
h0_6F32:
    cmp.b #$3C,d1
    bne.s h0_6F54
h0_6F38:
    move.b (a4)+,d1
    beq.s h0_6F38
h0_6F3C:
    cmp.b #$A,d1
    beq.s h0_6F72
h0_6F42:
    cmp.b #$3E,d1
    bne.s h0_6F50
h0_6F48:
    move.b (a4)+,d1
    cmp.b #$3E,d1
    bne.s h0_6F72
h0_6F50:
    move.b d1,(a0)+
    bra.s h0_6F38
h0_6F54:
    move.b d1,(a0)+
h0_6F56:
    move.b (a4)+,d1
    beq.s h0_6F56
h0_6F5A:
    cmp.b #$A,d1
    beq.s h0_6F72
h0_6F60:
    cmp.b #$9,d1
    beq.s h0_6F72
h0_6F66:
    cmp.b #$20,d1
    beq.s h0_6F72
h0_6F6C:
    cmp.b #$2C,d1
    bne.s h0_6F54
h0_6F72:
    clr.b (a0)+
    cmp.b #$2C,d1
    bne.s h0_6F88
h0_6F7A:
    move.b (a4)+,d1
    cmp.b #$A,d1
    bne.s h0_6F24
h0_6F82:
    bra.s h0_6FB4
h0_6F84:
    move.l (a7)+,$0882(a6)
h0_6F88:
    move.l a0,d0
    addq.l #1,d0
    bclr #0,d0
    move.l $0888(a6),-(a7)
    move.l d0,$0888(a6)
    sub.l (a7)+,d0
    sub.w d0,$0886(a6)
    move.w $0898(a6),d0
h0_6FA2:
    bne.s h0_6FA8
h0_6FA4:
    st.b $0118(a6)
h0_6FA8:
    st.b $0101(a6)
    addq.w #1,d0
    move.w d0,$0898(a6)
    rts
h0_6FB4:
    movea.l $0882(a6),a2
    move.l a2,-(a7)
    move.l (a2),$0882(a6)
    movem.l a0-a1,-(a7)
    bsr.w h0_061A
h0_6FC6:
    movem.l (a7)+,a0-a1
    bne.s h0_6F84
h0_6FCC:
    cmp.b #$26,d0
    bne.s h0_6F84
h0_6FD2:
    movem.l a0-a1,-(a7)
    bsr.w h0_07F0
h0_6FDA:
    bsr.w h0_06AC
h0_6FDE:
    movem.l (a7)+,a0-a1
    movea.l (a7)+,a2
    bne.w h0_6B08
h0_6FE8:
    move.l a2,$0882(a6)
    move.b (a4)+,d1
    cmp.b #$26,d1
    beq.s h0_6FFA
h0_6FF4:
    moveq.l #70,d0
    bsr.w h0_8486
h0_6FFA:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s h0_6FFA
h0_7002:
    cmp.b #$20,d1
    beq.s h0_6FFA
h0_7008:
    bra.w h0_6F24
h0_700C:
    move.w $0898(a6),d0
    cmp.w $089A(a6),d0
    bhi.s h0_7030
h0_7016:
    bsr.w h0_743C
h0_701A:
    movea.l a4,a0
    movea.l $0882(a6),a2
    lea.l $0014(a2),a1
    moveq.l #0,d2
    bra.w h0_710C
h0_702A:
    tst.l $0890(a6)
    bne.s h0_700C
h0_7030:
    movea.l $0882(a6),a2
    movea.l $0004(a2),a1
    movea.l $0010(a2),a0
    cmpa.l $0004(a1),a0
    bne.s h0_704C
h0_7042:
    movea.l $0008(a1),a1
    move.l a1,$0004(a2)
    movea.l (a1),a0
h0_704C:
    moveq.l #10,d0
    movea.l a0,a4
    moveq.l #92,d2
h0_7052:
    move.b (a0)+,d1
    cmp.b d0,d1
    beq.s h0_705E
h0_7058:
    cmp.b d2,d1
    bne.s h0_7052
h0_705C:
    bra.s h0_707A
h0_705E:
    tst.l $0890(a6)
    beq.s h0_706E
h0_7064:
    move.w $0898(a6),d0
    cmp.w $089A(a6),d0
    bls.s h0_7072
h0_706E:
    move.l a0,$0010(a2)
h0_7072:
    move.l a4,$0240(a6)
    moveq.l #0,d0
    rts
h0_707A:
    lea.l $0014(a2),a1
    move.l a0,d2
    sub.l a4,d2
    subq.w #1,d2
    beq.s h0_7094
h0_7086:
    move.l a0,d1
    move.w d2,d0
    movea.l a4,a0
h0_708C:
    move.b (a0)+,(a1)+
    subq.w #1,d0
    bne.s h0_708C
h0_7092:
    movea.l d1,a0
h0_7094:
    move.b (a0)+,d1
    cmp.b #$A,d1
    beq.w h0_7126
h0_709E:
    cmp.b #$40,d1
    beq.w h0_7190
h0_70A6:
    cmp.b #$3C,d1
    beq.w h0_71F6
h0_70AE:
    cmp.b #$3F,d1
    beq.w h0_713C
h0_70B6:
    moveq.l #48,d0
    cmp.b d0,d1
    bcs.s h0_7132
h0_70BC:
    cmp.b #$3A,d1
    bcs.s h0_70DE
h0_70C2:
    moveq.l #55,d0
    cmp.b #$41,d1
    bcs.s h0_7106
h0_70CA:
    cmp.b #$5B,d1
    bcs.s h0_70DE
h0_70D0:
    moveq.l #87,d0
    cmp.b #$61,d1
    bcs.s h0_7106
h0_70D8:
    cmp.b #$7B,d1
    bcc.s h0_7106
h0_70DE:
    sub.b d0,d1
    move.l a0,-(a7)
    lea.l $0116(a2),a0
    ext.w d1
    beq.s h0_70F8
h0_70EA:
    cmp.w $0008(a2),d1
    bgt.s h0_7102
h0_70F0:
    tst.b (a0)+
    bne.s h0_70F0
h0_70F4:
    subq.w #1,d1
    bne.s h0_70F0
h0_70F8:
    addq.b #1,d2
    beq.s h0_711E
h0_70FC:
    move.b (a0)+,(a1)+
    bne.s h0_70F8
h0_7100:
    subq.l #1,a1
h0_7102:
    movea.l (a7)+,a0
    bra.s h0_710C
h0_7106:
    addq.b #1,d2
    beq.s h0_7120
h0_710A:
    move.b d1,(a1)+
h0_710C:
    move.b (a0)+,d1
    cmp.b #$A,d1
    beq.s h0_7126
h0_7114:
    cmp.b #$5C,d1
    bne.s h0_7106
h0_711A:
    bra.w h0_7094
h0_711E:
    movea.l (a7)+,a0
h0_7120:
    cmpi.b #10,(a0)+
    bne.s h0_7120
h0_7126:
    move.b #$A,(a1)+
    lea.l $0014(a2),a4
    bra.w h0_705E
h0_7132:
    cmp.b #$23,d1
    beq.w h0_7270
h0_713A:
    bra.s h0_7106
h0_713C:
    move.b (a0)+,d1
    moveq.l #48,d0
    cmp.b d0,d1
    bcs.s h0_7132
h0_7144:
    cmp.b #$3A,d1
    bcs.s h0_7166
h0_714A:
    moveq.l #55,d0
    cmp.b #$41,d1
    bcs.s h0_7106
h0_7152:
    cmp.b #$5B,d1
    bcs.s h0_7166
h0_7158:
    moveq.l #87,d0
    cmp.b #$61,d1
    bcs.s h0_7106
h0_7160:
    cmp.b #$7B,d1
    bcc.s h0_7106
h0_7166:
    sub.b d0,d1
    move.l a0,-(a7)
    lea.l $0116(a2),a0
    ext.w d1
    beq.s h0_7180
h0_7172:
    cmp.w $0008(a2),d1
    bgt.s h0_718A
h0_7178:
    tst.b (a0)+
    bne.s h0_7178
h0_717C:
    subq.w #1,d1
    bne.s h0_7178
h0_7180:
    moveq.l #0,d1
h0_7182:
    tst.b (a0)+
    beq.s h0_718C
h0_7186:
    addq.l #1,d1
    bra.s h0_7182
h0_718A:
    moveq.l #0,d1
h0_718C:
    bra.w h0_71C4
h0_7190:
    tst.b $000C(a2)
    bne.s h0_71A2
h0_7196:
    st.b $000C(a2)
    addq.w #1,$0880(a6)
    addq.w #1,$000A(a2)
h0_71A2:
    cmp.b #$F9,d2
    bcc.w h0_7120
h0_71AA:
    addq.b #1,d2
    move.b #$5F,(a1)+
    move.l a0,-(a7)
    moveq.l #0,d1
    move.w $000A(a2),d1
    cmp.w #$A,d1
    bcs.s h0_71E2
h0_71BE:
    cmp.w #$64,d1
    bcs.s h0_71E8
h0_71C4:
    movem.l d4/a2-a3,-(a7)
    movea.l a1,a3
    move.w d2,d4
    lea.l h0_71F0(pc),a2
    bsr.w h0_8F08
h0_71D4:
    movea.l a3,a1
    move.w d4,d2
    movem.l (a7)+,d4/a2-a3
    movea.l (a7)+,a0
    bra.w h0_710C
h0_71E2:
    addq.b #1,d2
    move.b #$30,(a1)+
h0_71E8:
    addq.b #1,d2
    move.b #$30,(a1)+
    bra.s h0_71C4
h0_71F0:
    addq.b #1,d4
    move.b d1,(a3)+
    rts
h0_71F6:
    cmp.b #$F5,d2
    bcc.w h0_7120
h0_71FE:
    move.b (a0)+,d1
    movem.l d2/d4/a0-a4,-(a7)
    cmp.b #$24,d1
    seq.b d4
    bne.s h0_7214
h0_720C:
    move.b (a0)+,d1
    bra.s h0_7214
h0_7210:
    move.l d2,d1
    bra.s h0_7236
h0_7214:
    movea.l a0,a4
    lea.l $03E8(a6),a0
    bsr.w h0_76B8
h0_721E:
    bne.s h0_7262
h0_7220:
    cmp.b #$3E,d1
    bne.s h0_7262
h0_7226:
    bsr.w h0_14C2
h0_722A:
    beq.s h0_7210
h0_722C:
    bsr.w h0_0BCE
h0_7230:
    bne.s h0_7262
h0_7232:
    move.l $0008(a1),d1
h0_7236:
    movea.l $000C(a7),a3
    lea.l h0_71F0(pc),a2
    tst.b d4
    beq.s h0_724A
h0_7242:
    move.l (a7),d4
    bsr.w h0_8ED8
h0_7248:
    bra.s h0_7250
h0_724A:
    move.l (a7),d4
    bsr.w h0_8F08
h0_7250:
    move.l a3,d1
    move.w d4,d2
    move.l a4,d3
    movem.l (a7)+,d0/d4/a0-a4
    movea.l d1,a1
    movea.l d3,a0
    bra.w h0_710C
h0_7262:
    movem.l (a7)+,d2/d4/a0-a4
    moveq.l #73,d0
    bsr.w h0_8486
h0_726C:
    bra.w h0_710C
h0_7270:
    cmp.b #$FC,d2
    bcc.w h0_7120
h0_7278:
    moveq.l #0,d1
    move.w $0008(a2),d1
    move.l a0,-(a7)
    bra.w h0_71C4
    DC.L    $4a2e0101 ; VIOLATION: orphaned code island at $7284 is not reached from known entrypoints
    DC.B    "gT$n"
    DC.L    $08823d6a,$000e087e,$4a2e0101
    DC.B    "gDJ."
    DC.L    $01176604,$50ee0113,$536e0898,$246e0882,$200a90ae,$0888916e,$08862d4a,$0888302a
    DC.L    $000eb06e,$087e670a,$3d40087e,$700a6100,$12c02012,$2d400882,$660451ee,$0101720a
    DC.B    $4e,$75
    DC.B    $70,$35,$60,$00,$11,$a4 ; VIOLATION: orphaned code island at $72DE is not reached from known entrypoints
    DC.B    $70,$3b,$60,$00,$11,$86 ; VIOLATION: orphaned code island at $72E4 is not reached from known entrypoints
    DC.B    $28,$2e ; VIOLATION: orphaned code island at $72EA is not reached from known entrypoints
    DC.L    $023c41ee,$03e84a90,$67046100,$998c4aae,$08906600,$00366100,$f7ce2d42,$088c6e30
    DC.L    $610094e2,$6100939a,$6600f7f2,$6100f8b0,$67ee4a82,$66eab2bc
    DC.B    "REPTg"
    DC.B    $0c,$b2,$bc
    DC.B    "ENDRf"
    DC.B    $da,$72,$0a,$4e,$75
    DC.B    $70,$47,$60,$00,$11,$4c ; VIOLATION: orphaned code island at $7336 is not reached from known entrypoints
    DC.L    $206e014a,$0c6e0110,$014e6404,$6100f98c,$2d480890,$3f2e014e,$42a80008,$43e80010
    DC.L    $20892149,$00042148,$000c2d49,$014a046e,$0010014e,$26486100,$947c42ae,$08906100
    DC.L    $93306600,$f7882d4b,$08906100,$fa246100,$f83e67e2,$b2bc454e,$445266da,$4a8266d6
    DC.L    $61009452 ; VIOLATION: orphaned code island at $733C is not reached from known entrypoints
    DC.B    $50,$ee
h0_73A2:
    btst.b d0,(a3)
    movea.l $000C(a3),a0
    move.l $014A(a6),$0004(a0)
    btst.b #0,$014D(a6)
    beq.s h0_73CA
h0_73B6:
    subq.w #1,$014E(a6)
    addq.l #1,$014A(a6)
    tst.b $0101(a6)
    beq.s h0_73CA
h0_73C4:
    move.w $0898(a6),$089A(a6)
h0_73CA:
    subq.l #1,$088C(a6)
    bcs.s h0_740C
h0_73D0:
    move.l a3,$0890(a6)
    lea.l $0010(a3),a1
    move.l a1,$0894(a6)
h0_73DC:
    bsr.w h0_06AC
h0_73E0:
    bne.w h0_6B08
h0_73E4:
    movem.l a3-a4,-(a7)
    bsr.w h0_6BCA
h0_73EC:
    movem.l (a7)+,a3-a4
    beq.s h0_73FE
h0_73F2:
    cmp.l #$454E4452,d1
    bne.s h0_73FE
h0_73FA:
    tst.l d2
    beq.s h0_73CA
h0_73FE:
    st.b $0113(a6)
    move.l a3,-(a7)
    bsr.w h0_09C8
h0_7408:
    movea.l (a7)+,a3
    bra.s h0_73DC
h0_740C:
    move.w (a7)+,d0
    move.w $014E(a6),d2
    tst.l $0008(a3)
    beq.s h0_741A
h0_7418:
    moveq.l #0,d0
h0_741A:
    sub.w d0,d2
    sub.w d2,$014E(a6)
    ext.l d2
    add.l d2,$014A(a6)
    clr.l $0890(a6)
    lea.l dat_9884(pc),a0
    move.l a0,$017A(a6)
    moveq.l #10,d1
    rts
    DC.B    $70,$48,$60,$00,$10,$4c ; VIOLATION: orphaned code island at $7436 is not reached from known entrypoints
h0_743C:
    movea.l $0890(a6),a1
    movea.l $0894(a6),a0
    cmpa.l $0004(a1),a0
    bne.s h0_7454
h0_744A:
    movea.l $0008(a1),a1
    move.l a1,$0890(a6)
    movea.l (a1),a0
h0_7454:
    movea.l a0,a4
    moveq.l #10,d0
h0_7458:
    cmp.b (a0)+,d0
    bne.s h0_7458
h0_745C:
    move.l a0,$0894(a6)
    move.l a4,$0240(a6)
    moveq.l #0,d0
    rts
    DC.B    "NEEQC",0
    DC.B    $4e,$43
    DC.L    $44004e44
    DC.B    "GTGELTLE",0
    DC.B    $00
h0_747E:
    move.l d2,-(a7)
    bra.w h0_0AE8
dat_7484:
    DC.B    $00,$00,$0d,$fe,$00,$00
h0_748A:
    lea.l dat_7484(pc),a0
    tst.b $0238(a6)
    beq.s h0_749C
h0_7494:
    bsr.w h0_9700
h0_7498:
    move.b -$0001(a4),d1
h0_749C:
    moveq.l #0,d0
    bra.w h0_752E
h0_74A2:
    tst.b $0238(a6)
    beq.s h0_74B0
h0_74A8:
    bsr.w h0_9700
h0_74AC:
    move.b -$0001(a4),d1
h0_74B0:
    DC.B    $b2,$3c ; VIOLATION: invalid overlap: decoded instruction at $74B0 crosses required label at $74B2; region emitted as data
h0_74B2:
    DC.B    $00,$2e,$66,$4c ; VIOLATION: invalid overlap: decoded instruction at $74B2 crosses required label at $74B6; region emitted as data
h0_74B6:
    move.b (a4)+,d1
    bmi.s h0_74D2
h0_74BA:
    ext.w d1
    lea.l dat_7578(pc),a1
    adda.w d1,a1
    move.b $0005(a0),d0
    bne.s h0_74D6
h0_74C8:
    move.b (a1),d0
    bmi.s h0_74F6
h0_74CC:
    cmp.b #$4,d0
    bcs.s h0_7518
h0_74D2:
    bra.w h0_844A
h0_74D6:
    bmi.s h0_74E6
h0_74D8:
    tst.b $0122(a6)
    bne.w h0_74E6
h0_74E0:
    subq.w #1,d0
h0_74E2:
    beq.s h0_747E
h0_74E4:
    bra.s h0_74C8
h0_74E6:
    move.b (a1),d0
    bpl.s h0_7518
h0_74EA:
    addq.w #2,d0
    beq.s h0_7514
h0_74EE:
    addq.b #1,d0
    bne.s h0_74D2
h0_74F2:
    moveq.l #6,d0
    bra.s h0_752E
h0_74F6:
    addq.b #2,d0
    beq.s h0_7514
h0_74FA:
    addq.b #1,d0
    bne.s h0_74D2
h0_74FE:
    moveq.l #1,d0
    bra.s h0_7518
h0_7502:
    move.b $0005(a0),d0
    subq.w #1,d0
    bne.s h0_7510
h0_750A:
    tst.b $0122(a6)
    beq.s h0_74E2
h0_7510:
    moveq.l #0,d0
    bra.s h0_752E
h0_7514:
    moveq.l #2,d0
    subq.l #1,a4
h0_7518:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s h0_752E
h0_7520:
    cmp.b #$20,d1
    beq.s h0_752E
h0_7526:
    cmp.b #$A,d1
    bne.w h0_844A
h0_752E:
    cmp.b #$A,d1
    beq.s h0_7542
h0_7534:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s h0_752E
h0_753C:
    cmp.b #$20,d1
    beq.s h0_752E
h0_7542:
    move.b d0,$0239(a6)
    sf.b $023B(a6)
    move.w (a0)+,d6
    move.w (a0)+,d3
    move.w (a0)+,d2
    pea.l dat_7614(pc)
    lea.l h0_1D14(pc),a0
    adda.w d3,a0
    move.l a0,-(a7)
    move.w d1,-(a7)
    btst #15,d2
    beq.s h0_756A
h0_7564:
    bsr.w h0_0C64
h0_7568:
    bra.s h0_7574
h0_756A:
    btst #14,d2
    beq.s h0_7574
h0_7570:
    bsr.w h0_0C44
h0_7574:
    move.w (a7)+,d1
    rts
dat_7578:
    DC.L    $ffffffff,$ffffffff,$fffeffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $feffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffff01ff,$04ffffff,$ffffffff,$03ffffff,$05fffffd,$ffffff02,$07ffffff,$ffffffff
    DC.L    $ffff01ff,$04ffffff,$ffffffff,$03ffffff,$05fffffd,$ffffff02,$07ffffff,$ffffffff
    DC.L    $4a2e0125,$67067065,$61000e84,$3ac6720a
    DC.B    "Nu n"
    DC.L    $017a42ae,$017a4ed0
dat_7614:
    DC.L    $b23c000a,$671eb23c,$00096718,$b23c0020,$6712b23c,$002a670c,$b23c003b,$6706700e
    DC.L    $61000e50,$4aae017a,$66cc4aae,$018e671a,$222e018e,$42ae018e,$d3ae023c,$4a816b04
    DC.L    $d3ae0224,$42ae0182,$4e75220d,$92ae024c,$2d410182,$6714242e,$023cd3ae,$023cd3ae
    DC.L    $02244a2e,$02386600,$20924e75
h0_7680:
    bsr.s h0_76B8
h0_7682:
    bne.s h0_76A0
h0_7684:
    movea.l (a0),a1
    move.b $0005(a0),d0
    moveq.l #46,d2
    addq.l #1,a1
    bra.s h0_7694
h0_7690:
    cmp.b (a1)+,d2
    beq.s h0_76A2
h0_7694:
    subq.b #1,d0
    bne.s h0_7690
h0_7698:
    move.b $0005(a0),d2
    movea.l a4,a1
    moveq.l #0,d0
h0_76A0:
    rts
h0_76A2:
    movea.l a4,a1
    move.b $0005(a0),d2
    sub.b d0,$0005(a0)
    ext.w d0
    suba.w d0,a4
    move.b -$0001(a4),d1
    moveq.l #0,d0
    rts
h0_76B8:
    andi.w #255,d1
    lea.l dat_A764(pc),a2
    tst.b $0(a2,d1.w)
    beq.s h0_76F4
h0_76C6:
    bpl.s h0_7736
h0_76C8:
    move.b (a4),d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s h0_76E2
h0_76D6:
    cmp.b #$42,d1
    beq.s h0_76E2
h0_76DC:
    cmp.b #$4C,d1
    bne.s h0_76F0
h0_76E2:
    move.b $0001(a4),d1
    tst.b $0(a2,d1.w)
    ble.s h0_76F0
h0_76EC:
    moveq.l #46,d1
    bra.s h0_7736
h0_76F0:
    moveq.l #46,d1
    bra.s h0_773C
h0_76F4:
    cmp.b #$3A,d1
    bcc.s h0_773C
h0_76FA:
    lea.l -$0001(a4),a1
    movea.l a4,a2
h0_7700:
    move.b (a2)+,d1
    cmp.b #$24,d1
    beq.s h0_7714
h0_7708:
    cmp.b #$3A,d1
    bcc.s h0_7736
h0_770E:
    cmp.b #$30,d1
    bcc.s h0_7700
h0_7714:
    movea.l a2,a4
    move.l a2,d0
    sub.l a1,d0
    move.b d0,$0005(a0)
    lea.l $0006(a0),a2
    move.l a2,(a0)
    move.b $0116(a6),(a2)+
    subq.b #1,d0
h0_772A:
    move.b (a1)+,(a2)+
    subq.b #1,d0
    bne.s h0_772A
h0_7730:
    move.b (a4)+,d1
    moveq.l #0,d0
    rts
h0_7736:
    clr.l (a0)
    moveq.l #41,d0
    rts
h0_773C:
    tst.b $00FE(a6)
    bne.w h0_77B0
h0_7744:
    move.b d1,$0006(a0)
    lea.l -$0001(a4),a1
    move.l a1,(a0)
    moveq.l #0,d1
    moveq.l #0,d2
h0_7752:
    move.b (a4)+,d1
    tst.b $0(a2,d1.w)
    beq.s h0_7752
h0_775A:
    bpl.s h0_7794
h0_775C:
    move.l a4,d2
    bra.s h0_7752
h0_7760:
    sub.l a4,d2
    addq.l #2,d2
    bne.s h0_7798
    move.b -$0002(a4),d2
    cmp.b #$4C,d2
    beq.s h0_778E
    cmp.b #$6C,d2
    beq.s h0_778E
    cmp.b #$57,d2
    beq.s h0_778E
    cmp.b #$77,d2
    beq.s h0_778E
    cmp.b #$42,d2
    beq.s h0_778E
    cmp.b #$62,d2
    bne.s h0_7798
h0_778E:
    subq.l #2,a4
    moveq.l #46,d1
    bra.s h0_7798
h0_7794:
    tst.l d2
    bne.s h0_7760
h0_7798:
    move.l a4,d0
    sub.l (a0),d0
    cmp.w $021E(a6),d0
    bcs.s h0_77A6
h0_77A2:
    move.w $021E(a6),d0
h0_77A6:
    subq.b #1,d0
    move.b d0,$0005(a0)
    moveq.l #0,d0
    rts
h0_77B0:
    lea.l $0006(a0),a1
    move.l a1,(a0)
    moveq.l #1,d2
    moveq.l #0,d0
h0_77BA:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    move.b d1,(a1)+
    moveq.l #0,d1
    move.b (a4)+,d1
    tst.b $0(a2,d1.w)
    bgt.s h0_77E4
h0_77CC:
    bmi.s h0_77D6
h0_77CE:
    addq.b #1,d2
    bpl.s h0_77BA
h0_77D2:
    moveq.l #127,d2
    bra.s h0_77DC
h0_77D6:
    move.l a4,d0
    addq.b #1,d2
    bpl.s h0_77BA
h0_77DC:
    move.b (a4)+,d1
    tst.b $0(a2,d1.w)
    ble.s h0_77DC
h0_77E4:
    tst.l d0
    beq.s h0_7810
h0_77E8:
    sub.l a4,d0
    addq.l #2,d0
    bne.s h0_7810
h0_77EE:
    move.b -$0002(a4),d0
    cmp.b #$4C,d0
    beq.s h0_780A
h0_77F8:
    cmp.b #$6C,d0
    beq.s h0_780A
h0_77FE:
    cmp.b #$57,d0
    beq.s h0_780A
h0_7804:
    cmp.b #$77,d0
    bne.s h0_7810
h0_780A:
    moveq.l #46,d1
    subq.l #2,a4
    subq.b #2,d2
h0_7810:
    move.b d2,$0005(a0)
    moveq.l #0,d0
    rts
h0_7818:
    moveq.l #0,d0
    move.b d1,d2
    cmp.b #$22,d1
    beq.s h0_782C
h0_7822:
    cmp.b #$27,d1
    beq.s h0_782C
h0_7828:
    moveq.l #0,d2
    subq.l #1,a4
h0_782C:
    move.b (a4)+,d1
    cmp.b #$A,d1
    beq.s h0_7870
h0_7834:
    cmp.b d1,d2
    beq.s h0_7880
h0_7838:
    cmp.b #$9,d1
    beq.s h0_7844
h0_783E:
    cmp.b #$20,d1
    bne.s h0_7848
h0_7844:
    tst.b d2
    beq.s h0_7870
h0_7848:
    cmp.b #$2C,d1
    bne.s h0_785A
h0_784E:
    btst #16,d3
    beq.s h0_785A
h0_7854:
    move.l a4,app_file_0186+fh_Pos(a6)
    bra.s h0_7870
h0_785A:
    btst #17,d3
    bne.s h0_7866
h0_7860:
    ext.w d1
    move.b $7E(a6,d1.w),d1
h0_7866:
    move.b d1,$6(a0,d0.w)
    addq.b #1,d0
    bpl.s h0_782C
    moveq.l #126,d0
h0_7870:
    lea.l $0005(a0),a1
    addq.b #1,d0
    move.b d0,(a1)+
    move.b d3,$5(a0,d0.w)
    move.l a1,(a0)
    rts
h0_7880:
    cmpi.b #44,(a4)+
    bne.s h0_7870
h0_7886:
    bra.s h0_7854
dat_7888:
    DC.L    $ffffff00
h0_788C:
    move.l d2,d0
    and.l dat_7888(pc),d0
    beq.s h0_78D8
h0_7894:
    cmp.l dat_7888(pc),d0
    beq.s h0_78D8
h0_789A:
    bra.s h0_78C6
h0_789C:
    move.l d2,d0
    swap.w d0
    tst.w d0
    beq.s h0_78D8
h0_78A4:
    addq.w #1,d0
    beq.s h0_78D8
h0_78A8:
    bra.s h0_78C6
    DC.B    $b6,$3c,$00,$01,$67,$1c ; VIOLATION: orphaned code island at $78AA is not reached from known entrypoints
h0_78B0:
    move.b d2,d0
    ext.w d0
    bra.s h0_78BE
h0_78B6:
    cmp.b #$1,d3
    beq.s h0_78CC
h0_78BC:
    move.w d2,d0
h0_78BE:
    ext.l d0
    cmp.l d0,d2
    bne.s h0_78C6
h0_78C4:
    rts
h0_78C6:
    moveq.l #29,d0
    bra.w h0_8486
h0_78CC:
    moveq.l #30,d0
    tst.b $0107(a6)
    beq.w h0_8486
h0_78D6:
    rts
h0_78D8:
    cmp.b #$1,d3
    beq.s h0_78CC
h0_78DE:
    rts
h0_78E0:
    movea.l a4,a0
    lea.l $057F(a6),a4
    move.b (a4)+,d1
    move.l a0,-(a7)
    bsr.s h0_7902
h0_78EC:
    lea.l dat_78FC(pc),a4
    move.b (a4)+,d1
    moveq.l #1,d3
    bsr.w h0_7952
h0_78F8:
    movea.l (a7)+,a4
    rts
dat_78FC:
    DC.B    $54,$45,$58,$54,$0a,$00
h0_7902:
    clr.l $015A(a6)
    lea.l $03E8(a6),a0
    moveq.l #9,d3
    bsr.w h0_7818
h0_7910:
    movea.l $0172(a6),a2
    movem.l a3-a5,-(a7)
    bsr.w h0_0B88
h0_791C:
    sne.b d0
    movem.l (a7)+,a3-a5
    tst.b $0238(a6)
    bne.s h0_7942
h0_7928:
    tst.b d0
    beq.s h0_7942
h0_792C:
    moveq.l #0,d4
    moveq.l #9,d3
    bsr.w h0_0CBA
h0_7934:
    move.l a1,$013E(a6)
    lea.l $0010(a1),a1
    move.l a1,$0162(a6)
    rts
h0_7942:
    tst.b d0
    bne.s h0_794C
h0_7946:
    bsr.s h0_7934
h0_7948:
    bra.w h0_96A4
h0_794C:
    moveq.l #11,d0
    bra.w h0_846E
h0_7952:
    sf.b $011B(a6)
    sf.b $011C(a6)
    move.b d3,$0108(a6)
    lea.l $03E8(a6),a0
    clr.l app_file_0186+fh_Pos(a6)
    bset #16,d3
    btst.b #1,$021D(a6)
    beq.s h0_7976
h0_7972:
    bset #17,d3
h0_7976:
    bsr.w h0_7818
h0_797A:
    movea.l $013E(a6),a2
    addq.w #8,a2
    movem.l d3/a3-a5,-(a7)
    bsr.w h0_0B88
h0_7988:
    sne.b d0
    movem.l (a7)+,d3/a3-a5
    tst.b $0238(a6)
    bne.s h0_79C6
h0_7994:
    tst.b d0
    beq.s h0_79B2
h0_7998:
    moveq.l #0,d4
    bsr.w h0_0CBA
h0_799E:
    movea.l $013E(a6),a0
    subq.b #1,$000C(a0)
h0_79A6:
    move.b $000C(a0),d0
    bsr.w h0_79E4
h0_79AE:
    move.b d0,$000E(a1)
h0_79B2:
    move.l a1,$0142(a6)
    move.l $0008(a1),$023C(a6)
    move.b $000E(a1),$0146(a6)
    bra.w h0_988A
h0_79C6:
    tst.b d0
    beq.s h0_79B2
h0_79CA:
    bra.s h0_794C
h0_79CC:
    movea.l $0142(a6),a1
    move.l $023C(a6),$0008(a1)
    bra.w h0_9864
h0_79DA:
    tst.b $0238(a6)
    bne.w h0_96BE
h0_79E2:
    rts
h0_79E4:
    rts
h0_79E6:
    movea.l $0940(a6),a0
    clr.w (a0)
    move.l a0,$089C(a6)
    sf.b $010B(a6)
    rts
h0_79F6:
    move.l a0,-(a7)
    movea.l $089C(a6),a0
    move.w #$2B2B,(a0)+
    move.w d3,(a0)+
h0_7A02:
    move.l a0,$089C(a6)
    clr.w (a0)
    movea.l (a7)+,a0
    rts
h0_7A0C:
    move.l a0,-(a7)
    move.b $000E(a1),d0
    movea.l $089C(a6),a0
    move.w #$2B2B,(a0)+
    st.b (a0)+
    move.b d0,(a0)+
    bra.s h0_7A02
h0_7A20:
    move.l a0,-(a7)
    movea.l $089C(a6),a0
    move.w #$2D2D,-$0004(a0)
    movea.l (a7)+,a0
    rts
dat_7A30:
    DC.B    "line malformed",0
    DC.B    "out of memory",0
    DC.B    "undefined symbol",0
    DC.B    "additional symbol on pass 2",0
    DC.B    "symbol defined twice",0
    DC.B    "phasing error",0
    DC.B    "local not allowed",0
    DC.B    "INTERNAL:invalid hashing",0
    DC.B    "instruction not recognised",0
    DC.B    "invalid size",0
    DC.B    "duplicate MODULE name",0
    DC.B    "forward reference",0
    DC.B    "invalid section name, TEXT assumed",0
    DC.B    "garbage following instruction",0
    DC.B    "addressing mode not recognised",0
    DC.B    "address register expected",0
    DC.B    "addressing mode not allowed",0
    DC.B    "expression mismatch",0
    DC.B    "missing close bracket",0
    DC.B    "imported label not allowed",0
    DC.B    "illegal type combination",0
    DC.B    "invalid number",0
    DC.B    "number too large",0
    DC.B    "misuse of label",0
    DC.B    "include file read error",0
    DC.B    "file not found",0
    DC.B    "header file not found",0
    DC.B    "repeated include file",0
    DC.B    "data too large",0
    DC.B    "relative not allowed",0
    DC.B    "comma expected",0
    DC.B    ".W or .L expected as index size",0
    DC.B    "absolute not allowed",0
    DC.B    "wrong processor",0
    DC.B    "odd address",0
    DC.B    "immediate data expected",0
    DC.B    "data register expected",0
    DC.B    "BSS or OFFSET section cannot contain data",0
    DC.B    "during writing binary file",0
    DC.B    "cannot create binary file",0
    DC.B    "symbol expected",0
    DC.B    "XREFs not allowed within brackets",0
    DC.B    "cannot import symbol",0
    DC.B    "cannot export symbol",0
    DC.B    "not yet implemented",0
    DC.B    "register expected",0
    DC.B    "invalid MOVEP addressing mode",0
    DC.B    "spurious ENDC",0
    DC.B    "spurious ELSE",0
    DC.B    "missing ENDC",0
    DC.B    "invalid IF expression, ignored",0
    DC.B    "source expired prematurely",0
    DC.B    "spurious ENDM or MEXIT",0
    DC.B    "cannot nest MACRO definitions or define in REPTs",0
    DC.B    "missing quote",0
    DC.B    "user error",0
    DC.B    "invalid register list",0
    DC.B    "invalid option",0
    DC.B    "fatally bad conditional",0
    DC.B    "relocation not allowed",0
    DC.B    "division by zero",0
    DC.B    "absolute expression MUST evaluate",0
    DC.B    "illegal BSR.S",0
    DC.B    "option must be at start",0
    DC.B    "INTERNAL:invalid optimisation",0
    DC.B    "can only assemble executable code to memory",0
    DC.B    "program buffer full",0
    DC.B    "linker format restriction",0
    DC.B    "ORG/RORG not allowed",0
    DC.B    "INTERNAL:invalid multi-line macro call",0
    DC.B    "cannot nest repeat loops",0
    DC.B    "spurious ENDR",0
    DC.B    "invalid numeric expansion",0
    DC.B    "during listing output",0
    DC.B    "invalid printer parameter",0
    DC.B    "invalid FORMAT parameter",0
    DC.B    "INTERNAL:bad section",0
    DC.B    "INTERNAL:macro memory",0
    DC.B    "assembly interrupted",0
    DC.B    "invalid section type",0
    DC.B    "in command-line symbol",0
    DC.B    "# probably missing",0
    DC.B    "short branch cannot be 0 bytes",0
    DC.B    "DCB or DS count must not be negative",0
    DC.B    "invalid bitfield specification",0
    DC.B    "colon (:) expected",0
    DC.B    "floating-point register expected",0
    DC.B    "MMU register expected",0
    DC.B    "invalid MMU function code",0
    DC.B    "invalid radix",0
    DC.B    "invalid 68020 addressing mode",0
    DC.B    "invalid index scale",0
    DC.B    "hex floating point number too large",0
    DC.B    "invalid opcode size for data/address register",0
    DC.B    "only FPIAR allowed",0
    DC.B    "maths co-processor required",0
    DC.B    "invalid k-factor",0
    DC.B    "floating point constant not allowed",0
    DC.B    "floating point constant too large",0
    DC.B    "bad floating point expression",0
    DC.B    "privileged instruction",0
    DC.B    "invalid section specified",0
    DC.B    "invalid pre-assembled file",0
    DC.B    "only (An) allowed for this instruction",0
    DC.B    "INTERNAL:memory list corrupt",0
    DC.B    "bit number should be 0-7 for byte",0
    DC.B    "p(`L"
h0_8422:
    bsr.w h0_DOSWrite_B024              ; KNOWN: DOSBase _LVOWrite fallback via local wrapper
h0_8426:
    bne.s h0_842A
h0_8428:
    rts
h0_842A:
    bsr.w h0_98AE
h0_842E:
    moveq.l #39,d0
    bra.s h0_846E
h0_8432:
    moveq.l #1,d0
    bra.s h0_8486
h0_8436:
    moveq.l #5,d0
    bra.s h0_8486
h0_843A:
    moveq.l #4,d0
    bra.s h0_8486
h0_843E:
    moveq.l #6,d0
    bra.s h0_8486
h0_8442:
    moveq.l #7,d0
    bra.s h0_8486
h0_8446:
    moveq.l #9,d0
    bra.s h0_8486
h0_844A:
    moveq.l #10,d0
    bra.s h0_8486
h0_844E:
    moveq.l #12,d0
    bra.s h0_8486
h0_8452:
    moveq.l #33,d0
    bra.s h0_8486
    DC.B    $70,$1d,$60,$2c ; VIOLATION: orphaned code island at $8456 is not reached from known entrypoints
h0_845A:
    moveq.l #38,d0
    bra.s h0_8486
h0_845E:
    moveq.l #15,d0
    bra.s h0_8482
h0_8462:
    moveq.l #31,d0
    bra.s h0_8482
h0_8466:
    moveq.l #32,d0
    bra.s h0_8482
h0_846A:
    moveq.l #36,d0
    bra.s h0_8482
h0_846E:
    sf.b $0955(a6)
    move.b #$14,$023A(a6)
    bsr.s h0_8486
h0_847A:
    jmp h0_03B0.l
h0_8480:
    rts
h0_8482:
    movea.l $0234(a6),a7
h0_8486:
    tst.b $010D(a6)
    bne.s h0_8480
h0_848C:
    st.b $010D(a6)
    cmpi.b #10,$023A(a6)
    bcc.s h0_849E
h0_8498:
    move.b #$A,$023A(a6)
h0_849E:
    move.l a4,$0154(a6)
    movem.l d1-d3/a0-a3,-(a7)
    move.w d0,-(a7)
    moveq.l #6,d0
    bsr.w h0_8E7A
h0_84AE:
    lea.l dat_7A30(pc),a0
    addq.b #1,$010C(a6)
    moveq.l #0,d2
h0_84B8:
    move.w (a7)+,d0
h0_84BA:
    subq.w #1,d0
    beq.w h0_84C6
h0_84C0:
    tst.b (a0)+
    bne.s h0_84C0
h0_84C4:
    bra.s h0_84BA
h0_84C6:
    tst.l app_slot_01A2(a6)
    beq.s h0_8530
h0_84CC:
    movem.l d1-d3/a0-a2,-(a7)
    moveq.l #0,d3
    move.w $0218(a6),d3
    moveq.l #0,d2
    movea.l $017E(a6),a1
    move.l a1,d1
    beq.s h0_8520
h0_84E0:
    cmpi.b #12,$000D(a1)
    bne.s h0_852C
h0_84E8:
    move.l $0098(a1),d2
    tst.b $0101(a6)
    bne.s h0_8516
h0_84F2:
    tst.l $0890(a6)
    bne.w h0_8516
h0_84FA:
    move.l $0240(a6),d1
    beq.s h0_852C
h0_8500:
    movea.l d1,a2
    moveq.l #0,d0
    move.l $0154(a6),d1
h0_8508:
    cmpa.l d1,a2
    beq.s h0_851A
h0_850C:
    cmp.b #$A,d0
    beq.s h0_852C
h0_8512:
    move.b (a2)+,d0
    bra.s h0_8508
h0_8516:
    move.l $009E(a1),d1
h0_851A:
    sub.l $0008(a1),d1
    subq.l #1,d1
h0_8520:
    movea.l app_slot_01A2(a6),a1
    moveq.l #0,d0
    movea.l $0004(a1),a1
    jsr (a1)                            ; KNOWN: callback field +4 from app_slot_01A2
h0_852C:
    movem.l (a7)+,d1-d3/a0-a2
h0_8530:
    bsr.w h0_9292
h0_8534:
    move.w $0218(a6),d0
    beq.s h0_8584
h0_853A:
    cmp.w #$FFFF,d0
    beq.s h0_8576
h0_8540:
    moveq.l #9,d0
    bsr.w h0_8E7A
h0_8546:
    moveq.l #0,d1
    move.w $0218(a6),d1
    bsr.w h0_8F04
h0_8550:
    tst.l $017E(a6)
    beq.s h0_8576
h0_8556:
    moveq.l #11,d0
    bsr.w h0_8E7A
h0_855C:
    movea.l $017E(a6),a1
    moveq.l #0,d2
    move.b $0016(a1),d2
    subq.b #2,d2
    lea.l $0017(a1),a1
h0_856C:
    move.b (a1)+,d1
    bsr.w h0_8E98
h0_8572:
    dbf.w d2,h0_856C
h0_8576:
    bsr.w h0_8E8C
h0_857A:
    st.b $0102(a6)
    movem.l (a7)+,d1-d3/a0-a3
h0_8582:
    rts
h0_8584:
    moveq.l #28,d0
    bsr.w h0_8E7A
h0_858A:
    bra.s h0_8576
h0_858C:
    tst.b $0238(a6)
    beq.s h0_8582
h0_8592:
    tst.b $0105(a6)
    beq.s h0_8582
h0_8598:
    cmpi.b #5,$023A(a6)
    bcc.s h0_85A6
h0_85A0:
    move.b #$5,$023A(a6)
h0_85A6:
    move.l a4,$0154(a6)
    movem.l d1-d3/a0-a3,-(a7)
    move.w d0,-(a7)
    moveq.l #8,d0
    bsr.w h0_8E7A
h0_85B6:
    lea.l dat_85C2(pc),a0
    move.w #$8000,d2
    bra.w h0_84B8
dat_85C2:
    DC.B    "sign extended operand",0
    DC.B    "relative cannot be relocated",0
    DC.B    "invalid LINK displacement",0
    DC.B    "68010 instruction, converted to MOVE SR",0
    DC.B    "size should be .W",0
    DC.B    "directive ignored",0
    DC.B    "misuse of register list",0
    DC.B    "no ORG specified",0
    DC.B    "bit number should be 0-7 for byte",0
    DC.B    "missing ENDC at end of macro",0
    DC.B    "trailing comma at end of DC directive",0
    DC.B    "branch made short",0
    DC.B    "offset removed",0
    DC.B    "short word addressing used",0
    DC.B    "MOVEQ substituted",0
    DC.B    "quick form used",0
    DC.B    "branch could be short",0
    DC.B    "short branch converted to NOP",0
    DC.B    "base displacement shortened",0
    DC.B    "outer displacement shortened",0
    DC.B    "ADD/SUB converted to LEA",0
    DC.B    "LEA converted to ADDQ/SUBQ",0
    DC.B    ".L converted to .W",0
    DC.B    $00
dat_87FC:
    DC.B    $02,$02,$02,$04,$00,$ff,$00,$02,$02,$00,$02,$02
h0_8808:
    tst.b $0238(a6)
    beq.s h0_883A
h0_880E:
    movem.w d0-d1,-(a7)
    subi.w #12,d0
    move.b dat_87FC(pc,d0.w),d0
    bmi.s h0_8826
h0_881C:
    ext.w d0
    add.w d0,$0194(a6)
    addq.w #1,app_file_0186+fh_Buf(a6)
h0_8826:
    move.w (a7),d0
    subi.w #12,d0
    move.w $0110(a6),d1
    btst d0,d1
    movem.w (a7)+,d0-d1
    bne.w h0_858C
h0_883A:
    rts
    DC.B    $70,$43,$60,$00,$fc,$2e ; VIOLATION: orphaned code island at $883C is not reached from known entrypoints
h0_8842:
    movem.l a3-a5,-(a7)
    movea.l $0172(a6),a2
    jsr h0_0B88.l
h0_8850:
    movem.l (a7)+,a3-a5
    rts
h0_8856:
    tst.b $0238(a6)
    bne.w h0_8950
h0_885E:
    bsr.s h0_8842
h0_8860:
    bne.s h0_8880
h0_8862:
    tst.b $0134(a6)
    bne.s h0_887C
h0_8868:
    cmpi.b #13,$000D(a1)
    beq.s h0_887C
h0_8870:
    tst.w $009C(a1)
    bne.w h0_8A02
h0_8878:
    bra.w h0_8958
h0_887C:
    moveq.l #0,d0
    rts
h0_8880:
    moveq.l #0,d4
    moveq.l #11,d3
    moveq.l #89,d0
    add.l d0,d0
    jsr h0_0D20.l
h0_888E:
    clr.l $0098(a1)
    clr.l $00AA(a1)
    clr.l $00AE(a1)
    move.l a1,-(a7)
    bsr.w h0_AE7C
h0_88A0:
    movea.l (a7)+,a1
    DC.B    $66 ; VIOLATION: invalid overlap: decoded instruction at $88A2 crosses required label at $88A3; region emitted as data
h0_88A3:
    DC.B    $00,$01,$5a ; VIOLATION: invalid overlap: decoded instruction at $88A3 crosses required label at $88A6; region emitted as data
h0_88A6:
    tst.l d1
    bpl.s h0_ExecAvailMem_88C4
h0_88AA:
    cmp.l #$FFFFFFFF,d1
    beq.s h0_ExecAvailMem_88C4
h0_88B2:
    move.b #$D,$000D(a1)
    neg.l d1
    jsr h0_FCD6.l
h0_88C0:
    moveq.l #0,d0
    rts
h0_ExecAvailMem_88C4:
    move.l d4,$0098(a1)
    move.l $017E(a6),$0010(a1)
    move.l a1,$017E(a6)
    tst.l d1
    bmi.s h0_8914
h0_ExecAvailMem_88D6:
    addq.l #3,d1
    bclr #0,d1
    move.l #$1200,d2
    bsr.w h0_ExecAvailMem_B068
h0_88E6:
    move.l a1,-(a7)
    move.l d1,d3
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_88EE:
    movea.l (a7)+,a1
    move.l a0,$0008(a1)
    move.l d3,$00A6(a1)
    adda.l d3,a0
    move.l a0,$00A2(a1)
    move.l a0,$009E(a1)
    move.w $0218(a6),$009C(a1)
    clr.w $0218(a6)
    st.b $000E(a1)
    bra.w h0_89BA
h0_8914:
    move.b #$C,$000D(a1)
    movea.l app_slot_01A2(a6),a0
    move.l $0008(a0),$0008(a1)
    move.l $0008(a0),$009E(a1)
    movea.l $000C(a0),a2
    cmpi.b #10,-$0001(a2)
    beq.s h0_893A
h0_8936:
    move.b #$A,(a2)+
h0_893A:
    move.l a2,$00A2(a1)
    move.w $0218(a6),$009C(a1)
    clr.w $0218(a6)
    clr.b $000E(a1)
    moveq.l #0,d0
    rts
h0_8950:
    bsr.w h0_8842
h0_8954:
    bne.w h0_8A02
h0_8958:
    move.b $000E(a1),d0
    cmp.b #$FE,d0
    beq.s h0_899A
h0_8962:
    cmpi.b #13,$000D(a1)
    beq.s h0_899A
h0_896A:
    move.l $017E(a6),$0010(a1)
    move.l a1,$017E(a6)
    tst.b d0
    beq.s h0_899C
h0_8978:
    move.l a1,-(a7)
    bsr.w h0_AE7C
h0_897E:
    movea.l (a7)+,a1
    bne.w h0_89FE
h0_8984:
    move.l d4,$0098(a1)
    move.l $0008(a1),$009E(a1)
    move.w $0218(a6),$009C(a1)
    clr.w $0218(a6)
    bra.s h0_89BA
h0_899A:
    rts
h0_899C:
    move.l $0008(a1),$009E(a1)
    move.w $0218(a6),$009C(a1)
    clr.w $0218(a6)
    moveq.l #0,d0
    rts
h0_89B0:
    move.l $0008(a1),$009E(a1)
    movea.l a2,a0
    bra.s h0_89C6
h0_89BA:
    movea.l $0008(a1),a0
    move.l a0,$009E(a1)
    move.l $00A6(a1),d1
h0_89C6:
    move.l $0098(a1),d2
    movem.l d1/a0-a1,-(a7)
    bsr.w h0_AFC2                       ; KNOWN: DOSBase _LVORead fallback via local wrapper
h0_89D2:
    movem.l (a7)+,d2/a0-a1
    bne.s h0_89FA
h0_89D8:
    lea.l $0(a0,d1.l),a2
    cmp.l d1,d2
    beq.s h0_89EE
h0_89E0:
    clr.b (a2)
    cmpi.b #10,-$0001(a2)
    beq.s h0_89EE
h0_89EA:
    move.b #$A,(a2)+
h0_89EE:
    move.l a2,$00A2(a1)
    addq.b #1,$000E(a1)
    moveq.l #0,d0
    rts
h0_89FA:
    moveq.l #25,d0
    rts
h0_89FE:
    moveq.l #26,d0
    rts
h0_8A02:
    moveq.l #28,d0
    rts
h0_8A06:
    moveq.l #11,d3
    lea.l h0_8A0E(pc),a2
    bra.s h0_8A26
h0_8A0E:
    move.l $0098(a0),d2
    beq.s h0_8A24
h0_8A14:
    clr.l $0098(a0)
    movem.l a0/a2,-(a7)
    bsr.w h0_DOSClose_AFB8              ; KNOWN: DOSBase _LVOClose fallback via local wrapper
h0_8A20:
    movem.l (a7)+,a0/a2
h0_8A24:
    rts
h0_8A26:
    move.l $0172(a6),d0
    beq.s h0_8A58
h0_8A2C:
    movea.l d0,a0
    move.l (a0),d0
    beq.s h0_8A58
h0_8A32:
    movea.l d0,a0
h0_8A34:
    tst.l (a0)
    beq.s h0_8A40
h0_8A38:
    move.l a0,-(a7)
    movea.l (a0),a0
    bsr.s h0_8A34
h0_8A3E:
    movea.l (a7)+,a0
h0_8A40:
    tst.b d3
    beq.s h0_8A4A
h0_8A44:
    cmp.b $000D(a0),d3
    bne.s h0_8A4C
h0_8A4A:
    jsr (a2)
h0_8A4C:
    tst.l $0004(a0)
    beq.s h0_8A58
h0_8A52:
    movea.l $0004(a0),a0
    bra.s h0_8A34
h0_8A58:
    rts
h0_8A5A:
    lea.l $04F4(a6),a0
    move.l d4,-(a7)
    bsr.w h0_8842
h0_8A64:
    move.l (a7)+,d4
    move.l a1,$057A(a6)
    moveq.l #0,d3
    lea.l h0_8A72(pc),a2
    bra.s h0_8A26
h0_8A72:
    move.b $000D(a0),d0
    cmp.b #$B,d0
    beq.s h0_8A82
h0_8A7C:
    cmp.b #$C,d0
    bne.s h0_8AD8
h0_8A82:
    move.l a0,-(a7)
    lea.l $00AA(a0),a0
h0_8A88:
    move.l (a0),d0
    beq.s h0_8AD6
h0_8A8C:
    movea.l (a0),a0
    move.l $0018(a0),d1
    move.l d1,d0
    andi.b #3,d0
    beq.s h0_8AA0
h0_8A9A:
    andi.b #252,d1
    addq.l #4,d1
h0_8AA0:
    move.l d1,$0018(a0)
    movem.l a0/a2,-(a7)
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_8AAC:
    movea.l a0,a1
    movem.l (a7)+,a0/a2
    move.l a1,$000E(a0)
    move.l a1,$0014(a0)
    move.l #$FFFFFFFF,$0006(a0)
    clr.l $000A(a0)
    lea.l (a0),a0
    cmpi.w #3,$021C(a6)
    bne.s h0_8A88
h0_8AD0:
    addq.l #1,$0200(a6)
    bra.s h0_8A88
h0_8AD6:
    movea.l (a7)+,a0
h0_8AD8:
    rts
h0_8ADA:
    move.l (a1),d1
    bpl.s h0_8AE2
h0_8ADE:
    move.l d0,(a1)
    bra.s h0_8AE6
h0_8AE2:
    move.l d0,(a1)
    sub.l d1,d0
h0_8AE6:
    beq.s h0_8B08
h0_8AE8:
    move.l $0018(a0),d1
    addq.l #1,d1
    cmp.l #$80,d0
    bcs.s h0_8B02
h0_8AF6:
    addq.l #2,d1
    cmp.l #$8000,d0
    bcs.s h0_8B02
h0_8B00:
    addq.l #4,d1
h0_8B02:
    move.l d1,$0018(a0)
    rts
h0_8B08:
    move.l $0018(a0),d1
    addq.l #7,d1
    bra.s h0_8B02
h0_8B10:
    move.l (a1),d1
    bpl.s h0_8B18
h0_8B14:
    move.l d0,(a1)
    bra.s h0_8B1C
h0_8B18:
    move.l d0,(a1)
    sub.l d1,d0
h0_8B1C:
    movea.l $0014(a0),a1
    beq.s h0_8B48
h0_8B22:
    cmp.w #$80,d0
    bcs.s h0_8B44
h0_8B28:
    clr.b (a1)+
    cmp.l #$8000,d0
    bcs.s h0_8B3E
h0_8B32:
    clr.b (a1)+
    clr.b (a1)+
    swap.w d0
    bsr.w h0_8B3E
h0_8B3C:
    swap.w d0
h0_8B3E:
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a1)+
h0_8B44:
    move.b d0,(a1)+
    rts
h0_8B48:
    clr.b (a1)+
    bra.s h0_8B32
dat_8B4C:
    DC.L    $24480c6e,$0003021c,$66146100,$159e48e7,$20e06100,$24f44cdf,$07042540,$001c223c
    DC.L    $000003f1,$6100157c,$615e6100,$15767200,$61001570 ; VIOLATION: orphaned code island at $8B4C is not reached from known entrypoints
    DC.B    $22,"<LINEJ."
    DC.L    $012a6706
    DC.B    $22,"<HCLNa",0
    DC.L    $155a7000,$610014fe,$52290016,$4a2e012a,$670a7200,$322a0012,$61001540,$61001544
    DC.L    $206a000e,$222a0018,$48e70060,$6100f860,$4cdf0600,$61001546,$204a45fa,$ff7c4e75
h0_8BD4:
    moveq.l #0,d1
    move.b $0016(a1),d1
    subq.b #1,d1
    move.b d1,$0016(a1)
    move.l d1,d0
    andi.b #3,d0
    beq.s h0_8BEE
h0_8BE8:
    andi.b #252,d1
    addq.l #4,d1
h0_8BEE:
    add.l $0018(a2),d1
    lsr.l #2,d1
    addq.l #3,d1
    tst.b $012A(a6)
    beq.s h0_8BFE
h0_8BFC:
    addq.l #1,d1
h0_8BFE:
    rts
h0_8C00:
    movea.l a0,a2
    bsr.s h0_8BD4
h0_8C04:
    move.l d1,-(a7)
    addq.l #2,d1
    add.l d1,d1
    add.l d1,d1
    moveq.l #0,d0
    bsr.w h0_ExecAllocMem_AE02
h0_8C12:
    move.l (a7),d1
    move.l a4,(a7)
    movea.l a0,a4
    move.l #$3F1,(a4)+
    move.l d1,(a4)+
    tst.b $012A(a6)
    beq.s h0_8C64
h0_8C26:
    move.l $0008(a3),(a4)+
    move.l #$48434C4E,(a4)+
    bsr.w h0_9D46
h0_8C34:
    addq.b #1,$0016(a1)
    moveq.l #0,d1
    move.w $0012(a2),d1
    move.l d1,(a4)+
    movea.l $000E(a2),a0
    move.l $0018(a2),d1
    lsr.l #2,d1
    subq.l #1,d1
h0_8C4C:
    move.l (a0)+,(a4)+
    dbf.w d1,h0_8C4C
h0_8C52:
    subi.l #65536,d1
    bcc.s h0_8C4C
h0_8C5A:
    movea.l (a7)+,a4
    movea.l a2,a0
    lea.l h0_8C00(pc),a2
    rts
h0_8C64:
    clr.l (a4)+
    move.l #$4C494E45,(a4)+
    bsr.w h0_9D46
h0_8C70:
    addq.b #1,$0016(a1)
    movea.l $000E(a2),a0
    move.l $0018(a2),d1
    lsr.l #3,d1
    subq.l #1,d1
    move.l $0008(a3),d2
h0_8C84:
    move.l (a0)+,(a4)+
    move.l (a0)+,d0
    add.l d2,d0
    move.l d0,(a4)+
    dbf.w d1,h0_8C84
h0_8C90:
    subi.l #65536,d1
    bcc.s h0_8C84
h0_8C98:
    bra.s h0_8C5A
h0_8C9A:
    movea.l $057A(a6),a0
    bsr.w h0_8CDC
h0_8CA2:
    movea.l $0172(a6),a0
    movea.l (a0),a0
h0_8CA8:
    tst.l (a0)
    beq.s h0_8CB4
h0_8CAC:
    move.l a0,-(a7)
    movea.l (a0),a0
    bsr.s h0_8CA8
h0_8CB2:
    movea.l (a7)+,a0
h0_8CB4:
    move.b $000D(a0),d0
    cmp.b #$B,d0
    beq.s h0_8CC4
h0_8CBE:
    cmp.b #$C,d0
    bne.s h0_8CCE
h0_8CC4:
    cmpa.l $057A(a6),a0
    beq.s h0_8CCE
h0_8CCA:
    bsr.w h0_8CDC
h0_8CCE:
    tst.l $0004(a0)
    beq.s h0_8CDA
h0_8CD4:
    movea.l $0004(a0),a0
    bra.s h0_8CA8
h0_8CDA:
    rts
h0_8CDC:
    movea.l a0,a1
    move.l $00AA(a1),d0
h0_8CE2:
    beq.s h0_8CF2
h0_8CE4:
    movea.l d0,a0
    cmp.b $0004(a0),d6
    beq.s h0_8CF0
h0_8CEC:
    move.l (a0),d0
    bra.s h0_8CE2
h0_8CF0:
    jsr (a2)
h0_8CF2:
    movea.l a1,a0
    rts
h0_8CF6:
    tst.l $0010(a1)
    beq.s h0_8D1A
h0_8CFC:
    movea.l $0010(a1),a1
h0_8D00:
    tst.l (a1)
    beq.s h0_8D0C
h0_8D04:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_8D00
h0_8D0A:
    movea.l (a7)+,a1
h0_8D0C:
    jsr (a2)
h0_8D0E:
    tst.l $0004(a1)
    beq.s h0_8D1A
h0_8D14:
    movea.l $0004(a1),a1
    bra.s h0_8D00
h0_8D1A:
    rts
h0_8D1C:
    move.l a3,-(a7)
    movea.l a2,a3
    lea.l h0_8D36(pc),a2
    bsr.s h0_8CF6
h0_8D26:
    movea.l $016A(a6),a1
    tst.l (a1)
    beq.s h0_8D32
h0_8D2E:
    movea.l (a1),a1
    bsr.s h0_8D00
h0_8D32:
    movea.l (a7)+,a3
    rts
h0_8D36:
    btst.b #5,$000C(a1)
    beq.s h0_8D46
h0_8D3E:
    cmp.b $000E(a1),d6
    bne.s h0_8D46
h0_8D44:
    jsr (a3)                            ; CANDIDATE: indirect_call index unresolved
h0_8D46:
    rts
h0_8D48:
    tst.l $0010(a1)
    beq.s h0_8D6C
h0_8D4E:
    movea.l $0010(a1),a1
h0_8D52:
    tst.l (a1)
    beq.s h0_8D5E
h0_8D56:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_8D52
h0_8D5C:
    movea.l (a7)+,a1
h0_8D5E:
    bsr.s h0_8D6E
h0_8D60:
    tst.l $0004(a1)
    beq.s h0_8D6C
h0_8D66:
    movea.l $0004(a1),a1
    bra.s h0_8D52
h0_8D6C:
    rts
h0_8D6E:
    btst.b #4,$000C(a1)
    beq.s h0_8D80
h0_8D76:
    btst.b #2,$000C(a1)
    bne.s h0_8D80
h0_8D7E:
    jsr (a2)
h0_8D80:
    rts
h0_8D82:
    tst.b $0238(a6)
    bne.s h0_8DA0
h0_8D88:
    move.l #$196,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_8D92:
    move.l a0,$0948(a6)
    move.l a0,$094C(a6)
    clr.l (a0)+
    clr.w (a0)
    rts
h0_8DA0:
    movea.l $094C(a6),a0
    move.w $0004(a0),d0
    lea.l $6(a0,d0.w),a0
    move.l a0,$0950(a6)
    movea.l $0948(a6),a0
    move.l a0,$094C(a6)
    moveq.l #-1,d0
    tst.w $0004(a0)
    beq.s h0_8DC8
h0_8DC0:
    clr.w $0004(a0)
    move.l $0006(a0),d0
h0_8DC8:
    move.l d0,$0944(a6)
    rts
h0_8DCE:
    move.l a5,d0
    sub.l $024C(a6),d0
    add.l $0224(a6),d0
    tst.b $0238(a6)
    bne.s h0_8E22
h0_8DDE:
    move.l d0,-(a7)
    movea.l $094C(a6),a0
    addq.l #4,a0
    move.w (a0)+,d0
    cmp.w #$190,d0
    beq.s h0_8DFE
h0_8DEE:
    move.l (a7)+,$0(a0,d0.w)
    move.l d2,$4(a0,d0.w)
    addq.w #8,d0
    move.w d0,-(a0)
    moveq.l #0,d0
    rts
h0_8DFE:
    movem.l d1-d2/a1-a2,-(a7)
    move.l #$196,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_8E0C:
    movea.l $094C(a6),a1
    move.l a0,(a1)
    move.l a0,$094C(a6)
    clr.l (a0)+
    clr.w (a0)+
    moveq.l #0,d0
    movem.l (a7)+,d1-d2/a1-a2
    bra.s h0_8DEE
h0_8E22:
    cmp.l $0944(a6),d0
    bne.s h0_8E5A
h0_8E28:
    movea.l $094C(a6),a0
    addq.l #4,a0
    move.w (a0)+,d0
    cmp.l $4(a0,d0.w),d2
    beq.s h0_8E40
h0_8E36:
    move.w d0,-(a7)
    moveq.l #65,d0
    bsr.w h0_8486
h0_8E3E:
    move.w (a7)+,d0
h0_8E40:
    addq.w #8,d0
    cmp.w #$190,d0
    beq.s h0_8E5C
h0_8E48:
    move.w d0,-$0002(a0)
    adda.w d0,a0
    cmpa.l $0950(a6),a0
    beq.s h0_8E70
h0_8E54:
    move.l (a0),$0944(a6)
    moveq.l #0,d0
h0_8E5A:
    rts
h0_8E5C:
    movea.l $094C(a6),a0
    tst.l (a0)
    beq.s h0_8E70
h0_8E64:
    movea.l (a0),a0
    move.l a0,$094C(a6)
    addq.w #6,a0
    moveq.l #0,d0
    bra.s h0_8E48
h0_8E70:
    moveq.l #-1,d0
    move.l d0,$0944(a6)
    moveq.l #0,d0
    rts
h0_8E7A:
    lea.l dat_93FE(pc),a0
    tst.w d0
h0_8E80:
    beq.w h0_9292
h0_8E84:
    tst.b (a0)+
    bne.s h0_8E84
h0_8E88:
    subq.w #1,d0
    bra.s h0_8E80
h0_8E8C:
    moveq.l #10,d1
    bra.w h0_9288
h0_8E92:
    bsr.w h0_8E96
h0_8E96:
    moveq.l #32,d1
h0_8E98:
    movem.l d0-d2/a0-a2,-(a7)
    bsr.w h0_9288
h0_8EA0:
    movem.l (a7)+,d0-d2/a0-a2
    rts
h0_8EA6:
    move.w d1,-(a7)
    swap.w d1
    bsr.s h0_8EAE
h0_8EAC:
    move.w (a7)+,d1
h0_8EAE:
    move.w d1,-(a7)
    lsr.w #8,d1
    bsr.s h0_8EB6
h0_8EB4:
    move.w (a7)+,d1
h0_8EB6:
    move.w d1,-(a7)
    lsr.w #4,d1
    bsr.s h0_8EBE
h0_8EBC:
    move.w (a7)+,d1
h0_8EBE:
    andi.w #15,d1
    move.b dat_8EC8(pc,d1.w),d1
    bra.s h0_8E98
dat_8EC8:
    DC.B    $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46
h0_8ED8:
    moveq.l #6,d3
    moveq.l #0,d2
h0_8EDC:
    rol.l #4,d1
    move.l d1,-(a7)
    andi.w #15,d1
    bne.s h0_8EEA
h0_8EE6:
    tst.b d2
    beq.s h0_8EF2
h0_8EEA:
    st.b d2
    move.b dat_8EC8(pc,d1.w),d1
    jsr (a2)
h0_8EF2:
    move.l (a7)+,d1
    dbf.w d3,h0_8EDC
h0_8EF8:
    rol.l #4,d1
    andi.w #15,d1
    move.b dat_8EC8(pc,d1.w),d1
    jmp (a2)
h0_8F04:
    lea.l h0_8E98(pc),a2
h0_8F08:
    lea.l dat_8F3C(pc),a0
    moveq.l #1,d2
    moveq.l #8,d0
h0_8F10:
    moveq.l #0,d3
    cmp.l (a0)+,d1
    bcs.s h0_8F22
h0_8F16:
    sub.l -(a0),d1
h0_8F18:
    addq.b #1,d3
    sub.l (a0),d1
    bcc.s h0_8F18
h0_8F1E:
    add.l (a0)+,d1
    bra.s h0_8F26
h0_8F22:
    tst.b d2
    bpl.s h0_8F32
h0_8F26:
    st.b d2
    addi.b #48,d3
    exg d3,d1
    jsr (a2)
h0_8F30:
    exg d3,d1
h0_8F32:
    dbf.w d0,h0_8F10
h0_8F36:
    addi.b #48,d1
    jmp (a2)
dat_8F3C:
    DC.L    $3b9aca00,$05f5e100,$00989680,$000f4240,$000186a0,$00002710,$000003e8,$00000064
    DC.L    $0000000a ; VIOLATION: orphaned code island at $8F3C is not reached from known entrypoints
h0_8F60:
    moveq.l #20,d0
    bsr.w h0_8E7A
h0_8F66:
    movea.l $016A(a6),a2
    lea.l dat_8F90(pc),a4
    bsr.w h0_8FD2
h0_8F72:
    moveq.l #9,d3
    lea.l h0_8F98(pc),a2
    lea.l dat_8F80(pc),a4
    bra.w h0_8A26
dat_8F80:
    DC.B    $0c,$2b,$00,$02,$00,$0d,$67,$08,$10,$2b,$00,$0e,$60,$00,$07,$f8 ; VIOLATION: orphaned code island at $8F80 is not reached from known entrypoints
dat_8F90:
    DC.B    $61,$00,$ff,$04,$60,$00,$fe,$fc ; VIOLATION: orphaned code island at $8F90 is not reached from known entrypoints
h0_8F98:
    movem.l d3/a0/a2,-(a7)
    move.l a0,-(a7)
    moveq.l #21,d0
    bsr.w h0_8E7A
h0_8FA4:
    movea.l (a7),a0
    lea.l $0016(a0),a0
    move.b (a0)+,d2
h0_8FAC:
    move.b (a0)+,d1
    bsr.w h0_8E98
h0_8FB2:
    subq.b #1,d2
    bgt.s h0_8FAC
h0_8FB6:
    bsr.w h0_8E8C
h0_8FBA:
    bsr.w h0_8E8C
h0_8FBE:
    movea.l (a7)+,a0
    lea.l $0010(a0),a2
    bsr.s h0_8FD2
h0_8FC6:
    movem.l (a7)+,d3/a0/a2
    rts
h0_8FCC:
    jmp h0_06A4.l
h0_8FD2:
    move.l a2,d0
    beq.s h0_904C
h0_8FD6:
    move.l (a2),d0
    beq.s h0_904C
h0_8FDA:
    movea.l d0,a2
    suba.l a3,a3
    lea.l $05BE(a6),a0
    moveq.l #127,d0
    move.b d0,(a0)+
h0_8FE6:
    st.b (a0)+
    dbf.w d0,h0_8FE6
h0_8FEC:
    tst.b $0115(a6)
    bgt.s h0_8FCC
h0_8FF2:
    lea.l $05A8(a6),a3
    move.b $0017(a3),d3
    bsr.s h0_904E
h0_8FFC:
    lea.l $05A8(a6),a0
    cmpa.l a3,a0
    beq.s h0_904C
h0_9004:
    bset.b #0,$000C(a3)
    btst.b #4,$000C(a3)
    bne.s h0_8FEC
h0_9012:
    move.l $0008(a3),d1
    bsr.w h0_8EA6
h0_901A:
    bsr.w h0_8E92
h0_901E:
    jsr (a4)                            ; CANDIDATE: indirect_call index unresolved
h0_9020:
    moveq.l #0,d1
    move.b $000D(a3),d1
    lea.l dat_909A(pc),a0
    move.b $0(a0,d1.w),d1
    bsr.w h0_8E98
h0_9032:
    bsr.w h0_8E92
h0_9036:
    lea.l $0016(a3),a0
    move.b (a0)+,d4
h0_903C:
    move.b (a0)+,d1
    bsr.w h0_8E98
h0_9042:
    subq.b #1,d4
    bne.s h0_903C
h0_9046:
    bsr.w h0_8E8C
h0_904A:
    bra.s h0_8FEC
h0_904C:
    rts
h0_904E:
    tst.l (a2)
    beq.s h0_905A
h0_9052:
    move.l a2,-(a7)
    movea.l (a2),a2
    bsr.s h0_904E
h0_9058:
    movea.l (a7)+,a2
h0_905A:
    btst.b #0,$000C(a2)
    bne.s h0_9088
h0_9062:
    cmp.b $0017(a2),d3
    bcs.s h0_9088
h0_9068:
    lea.l $0016(a3),a0
    lea.l $0016(a2),a1
    move.b (a0)+,d0
    move.b (a1)+,d1
h0_9074:
    cmpm.b (a1)+,(a0)+
    bcs.s h0_9088
h0_9078:
    bne.s h0_9082
h0_907A:
    subq.b #1,d0
    beq.s h0_9088
h0_907E:
    subq.b #1,d1
    bne.s h0_9074
h0_9082:
    movea.l a2,a3
    move.b $0017(a3),d3
h0_9088:
    tst.l $0004(a2)
    beq.s h0_9098
h0_908E:
    move.l a2,-(a7)
    movea.l $0004(a2),a2
    bsr.s h0_904E
h0_9096:
    movea.l (a7)+,a2
h0_9098:
    rts
dat_909A:
    DC.B    $3f,$52,$41,$3f,$72,$6c,$3f,$3f,$3f,$3f,$3f,$3f,$4f,$00
h0_90A8:
    move.l #$2800,d1
    move.w d1,app_ULONG(a6)
    bsr.s h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_90B4:
    move.l a0,$013A(a6)
    rts
h0_ExecAllocMem_90BA:
    addq.l #MEMF_FAST,d1
    bsr.w h0_AE42                       ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_90C0:
    beq.s h0_90EC
h0_90C2:
    move.l $0136(a6),(a0)
    move.l a0,$0136(a6)
    addq.w #4,a0
    rts
    DC.B    $59,$48 ; VIOLATION: orphaned code island at $90CE is not reached from known entrypoints
    DC.L    $43ee0136,$2011670e,$b1c06704,$224060f4
    DC.B    $22,$90,$60,$00,$1d,$82 ; VIOLATION: orphaned code island at $90E0 is not reached from known entrypoints
    DC.B    $70,$69,$60,$00,$f3,$84 ; VIOLATION: orphaned code island at $90E6 is not reached from known entrypoints
h0_90EC:
    moveq.l #2,d0
    bra.w h0_846E
h0_90F2:
    movea.l $0136(a6),a0
    bra.s h0_9100
h0_90F8:
    move.l (a0),-(a7)
    bsr.w h0_ExecFreeMem_AE66
h0_90FE:
    movea.l (a7)+,a0
h0_9100:
    move.l a0,d0
    bne.s h0_90F8
h0_9104:
    rts
h0_9106:
    sf.b $0954(a6)
    sf.b $0955(a6)
    clr.l app_file_0956+fh_Link(a6)
    lea.l app_file_0956+fh_Interactive(a6),a0
    lea.l $0B5A(a6),a1
    move.l a0,(a1)
    move.l a1,$0B5E(a6)
    move.w #$84,$0B62(a6)
    move.w #$3C,$0B64(a6)
    clr.w $0B66(a6)
    move.w #$FFFF,$0B68(a6)
    clr.w $0B6A(a6)
    clr.b $0B82(a6)
    clr.b $0BD3(a6)
    st.b $0C24(a6)
    move.w #$8,$0B6C(a6)
    lea.l $0B6E(a6),a3
    bsr.w h0_AD0C
h0_9154:
    clr.b (a3)
    rts
h0_9158:
    tst.l app_file_0956+fh_Link(a6)
    beq.s h0_9168
h0_915E:
    bsr.w h0_AB56
h0_9162:
    bsr.w h0_919E
h0_9166:
    bsr.s h0_916A
h0_9168:
    rts
h0_916A:
    tst.l app_file_0956+fh_Link(a6)
    beq.s h0_9168
h0_9170:
    move.l app_file_0956+fh_Link(a6),d3
    clr.l app_file_0956+fh_Link(a6)
    bra.w h0_DOSClose_A900
h0_917C:
    movea.l $0B5A(a6),a0
    cmpa.l $0B5E(a6),a0
    beq.s h0_918E
h0_9186:
    move.b d1,(a0)+
    move.l a0,$0B5A(a6)
    rts
h0_918E:
    move.w d1,-(a7)
    bsr.s h0_919E
h0_9192:
    bne.s h0_9198
h0_9194:
    move.w (a7)+,d1
    bra.s h0_917C
h0_9198:
    moveq.l #74,d0
    bra.w h0_846E
h0_919E:
    move.l d3,-(a7)
    move.l app_file_0956+fh_Link(a6),d3
    lea.l app_file_0956+fh_Interactive(a6),a0
    move.l $0B5A(a6),d1
    sub.l a0,d1
    beq.s h0_91BC
h0_91B0:
    lea.l app_file_0956+fh_Interactive(a6),a1
    move.l a1,$0B5A(a6)
    bsr.w h0_A8EC                       ; KNOWN: DOSBase _LVOWrite fallback via local wrapper
h0_91BC:
    movem.l (a7)+,d3
    rts
h0_91C2:
    btst.b #0,$0C24(a6)
    bne.s h0_91CC
h0_91CA:
    rts
h0_91CC:
    addq.w #1,$0B6A(a6)
    moveq.l #16,d0
    bsr.w h0_8E7A
h0_91D6:
    lea.l $0B6E(a6),a0
    bsr.w h0_9292
h0_91DE:
    moveq.l #15,d0
    bsr.w h0_8E7A
h0_91E4:
    moveq.l #0,d1
    move.w $0B6A(a6),d1
    move.l d3,-(a7)
    bsr.w h0_8F04
h0_91F0:
    move.l (a7)+,d3
    bsr.w h0_8E8C
h0_91F6:
    lea.l $0B82(a6),a0
    tst.b (a0)
    beq.s h0_9204
h0_91FE:
    bsr.w h0_9292
h0_9202:
    bra.s h0_9224
h0_9204:
    tst.l $017E(a6)
    beq.s h0_9224
h0_920A:
    movea.l $017E(a6),a1
    moveq.l #0,d2
    move.b $0016(a1),d2
    subq.b #2,d2
    lea.l $0017(a1),a1
h0_921A:
    move.b (a1)+,d1
    bsr.w h0_8E98
h0_9220:
    dbf.w d2,h0_921A
h0_9224:
    bsr.w h0_8E8C
h0_9228:
    lea.l $0BD3(a6),a0
    bsr.w h0_9292
h0_9230:
    bsr.w h0_8E8C
h0_9234:
    bra.w h0_8E8C
h0_9238:
    tst.w $0B68(a6)
    bpl.s h0_924A
h0_923E:
    clr.w $0B68(a6)
    move.w d1,-(a7)
    bsr.w h0_91C2
h0_9248:
    move.w (a7)+,d1
h0_924A:
    cmp.b #$A,d1
    bne.s h0_926C
h0_9250:
    clr.w $0B66(a6)
    move.w $0B68(a6),d0
    addq.w #1,$0B68(a6)
    cmp.w $0B64(a6),d0
    beq.w h0_AB56
h0_9264:
    moveq.l #10,d1
    bsr.w h0_917C
h0_926A:
    rts
h0_926C:
    move.w $0B66(a6),d0
    cmp.w $0B62(a6),d0
    blt.s h0_927E
h0_9276:
    move.w d1,-(a7)
    bsr.s h0_9250
h0_927A:
    move.w (a7)+,d1
    bra.s h0_9238
h0_927E:
    bsr.w h0_917C
h0_9282:
    addq.w #1,$0B66(a6)
    rts
h0_9288:
    tst.b $0955(a6)
    bne.s h0_9238
h0_928E:
    bra.w h0_A89E
h0_9292:
    move.b (a0)+,d1
    beq.s h0_929E
h0_9296:
    move.l a0,-(a7)
    bsr.s h0_9288
h0_929A:
    movea.l (a7)+,a0
    bra.s h0_9292
h0_929E:
    rts
h0_92A0:
    movem.l d7/a3,-(a7)
    move.b $0C24(a6),d7
    add.b d7,d7
    bcc.s h0_92E4
h0_92AC:
    move.w $0218(a6),d2
    cmp.w #$2710,d2
    bcc.s h0_92D8
h0_92B6:
    bsr.w h0_8E96
h0_92BA:
    cmp.w #$3E8,d2
    bcc.s h0_92D8
h0_92C0:
    bsr.w h0_8E96
h0_92C4:
    cmp.w #$64,d2
    bcc.s h0_92D8
h0_92CA:
    bsr.w h0_8E96
h0_92CE:
    cmp.w #$A,d2
    bcc.s h0_92D8
h0_92D4:
    bsr.w h0_8E96
h0_92D8:
    moveq.l #0,d1
    move.w d2,d1
    bsr.w h0_8F04
h0_92E0:
    bsr.w h0_8E96
h0_92E4:
    move.l $0182(a6),d4
    add.b d7,d7
    bcc.s h0_932E
h0_92EC:
    move.b $0146(a6),d0
    move.b $083B(a6),d1
    beq.s h0_9318
h0_92F6:
    cmp.b #$FF,d1
    beq.s h0_9312
h0_92FC:
    bsr.w h0_8E92
h0_9300:
    move.b $083B(a6),d1
    bsr.s h0_9288
h0_9306:
    move.l $083C(a6),d1
    bsr.w h0_8EA6
h0_930E:
    moveq.l #0,d4
    bra.s h0_932E
h0_9312:
    bsr.w h0_9780
h0_9316:
    bra.s h0_9306
h0_9318:
    bsr.w h0_9780
h0_931C:
    move.l $0182(a6),d4
    movea.l $0250(a6),a3
    move.l $023C(a6),d1
    sub.l d4,d1
    bsr.w h0_8EA6
h0_932E:
    moveq.l #32,d1
    tst.b $0101(a6)
    beq.s h0_933E
h0_9336:
    tst.b $0118(a6)
    bne.s h0_933E
h0_933C:
    moveq.l #43,d1
h0_933E:
    bsr.w h0_9288
h0_9342:
    add.b d7,d7
    bcc.s h0_936C
h0_9346:
    moveq.l #5,d3
    cmpi.w #81,$0B62(a6)
    bcs.s h0_9352
h0_9350:
    moveq.l #9,d3
h0_9352:
    tst.l d4
h0_9354:
    beq.s h0_9364
h0_9356:
    move.b (a3)+,d1
    bsr.w h0_8EB6
h0_935C:
    subq.l #1,d4
    dbf.w d3,h0_9354
h0_9362:
    bra.s h0_936C
h0_9364:
    bsr.w h0_8E92
h0_9368:
    dbf.w d3,h0_9364
h0_936C:
    bsr.w h0_8E96
h0_9370:
    movea.l $0240(a6),a3
    moveq.l #0,d2
    moveq.l #0,d3
    tst.b $010D(a6)
    beq.s h0_9388
h0_937E:
    tst.b $0955(a6)
    bne.s h0_9388
h0_9384:
    move.l $0154(a6),d3
h0_9388:
    move.b (a3)+,d1
    cmp.l a3,d3
    bne.s h0_93C4
h0_938E:
    movem.l d0-d2/a0-a2,-(a7)
    cmp.b #$A,d1
    beq.s h0_939E
h0_9398:
    cmp.b #$9,d1
    bne.s h0_93A0
h0_939E:
    moveq.l #32,d1
h0_93A0:
    tst.b $0128(a6)
    bne.s h0_93AC
h0_93A6:
    bsr.w h0_A8C4
h0_93AA:
    bra.s h0_93B0
h0_93AC:
    bsr.w h0_A89E
h0_93B0:
    movem.l (a7)+,d0-d2/a0-a2
    cmp.b #$A,d1
    beq.s h0_93F4
h0_93BA:
    cmp.b #$9,d1
    beq.s h0_93C4
h0_93C0:
    addq.w #1,d2
    bra.s h0_9388
h0_93C4:
    cmp.b #$A,d1
    beq.s h0_93F4
h0_93CA:
    cmp.b #$9,d1
    bne.s h0_93EC
h0_93D0:
    moveq.l #0,d0
    move.w d2,d0
    divu.w $0B6C(a6),d0
    swap.w d0
    sub.w $0B6C(a6),d0
    neg.w d0
h0_93E0:
    bsr.w h0_8E96
h0_93E4:
    addq.w #1,d2
    subq.w #1,d0
    bne.s h0_93E0
h0_93EA:
    bra.s h0_9388
h0_93EC:
    addq.w #1,d2
    bsr.w h0_8E98
h0_93F2:
    bra.s h0_9388
h0_93F4:
    bsr.w h0_9288
h0_93F8:
    movem.l (a7)+,d7/a3
    rts
dat_93FE:
    DC.B    "GenAm Macro Assembler Copyright "
    DC.B    $a9
    DC.B    " HiSoft 1985-1997"
    DC.L    $0a416c6c
    DC.B    " Rights Reserved - version 3.18"
    DC.B    $0a
    DC.L    $0a005061
    DC.B    "ss 1"
    DC.L    $0a005061
    DC.B    "ss 2"
    DC.L    $0a002065
    DC.B    "rrors found"
    DC.B    $0a
    DC.L    $00206572
    DC.B    "ror found"
    DC.B    $0a,$00
    DC.B    " lines assembled into ",0
    DC.B    "Error: ",0
    DC.B    "Locals:"
    DC.B    $0a,$00
    DC.B    "Warning: ",0
    DC.B    " at line ",0
    DC.B    "Could not open file ",0
    DC.B    " in file ",0
    DC.B    " bytes, ",0
    DC.B    " optimisations saving ",0
    DC.B    " bytes"
    DC.L    $0a002020
    DC.B    "Page ",0
    DC.B    "HiSoft GenAm 680x0 Macro Assembler v3.18   ",0
    DC.B    " relocatable",0
    DC.B    " position-independent",0
    DC.B    " code"
    DC.B    $0a,$00
    DC.L    $0a09474c
    DC.B    "OBAL SYMBOLS"
    DC.L    $0a0a000a,$094d4f44
    DC.B    "ULE ",0
    DC.B    " absolute",0
    DC.B    "Bad arguments"
    DC.L    $0a004572
    DC.B    "ror in WITH file",0
    DC.B    "WITH file not found",0
    DC.B    "Could not open listing device"
    DC.B    $0a,$00
    DC.B    "Assembling ",0
    DC.B    " in assembly options",0
    DC.B    "Main file already included in header file"
    DC.B    $0a,$00
h0_962C:
    pea.l h0_9292(pc)
    tst.b $0109(a6)
    beq.s h0_963C
h0_9636:
    lea.l dat_965A(pc),a0
    rts
h0_963C:
    btst.b #2,$021D(a6)
    bne.w h0_F9AA
h0_9646:
    bra.w h0_A396
h0_964A:
    tst.b $0109(a6)
    beq.s h0_9666
h0_9650:
    lea.l dat_9656(pc),a0
    rts
dat_9656:
    DC.L    $2e677300
dat_965A:
    DC.B    $47,$65,$6e,$20,$73,$79,$6d,$62,$6f,$6c,$00,$00
h0_9666:
    btst.b #2,$021D(a6)
    bne.w h0_F9B0
h0_9670:
    bra.w h0_A3A8
    DC.B    $08,$2e,$00,$02,$02,$1d,$66,$00,$63,$56,$60,$00,$0d,$5e ; VIOLATION: orphaned code island at $9674 is not reached from known entrypoints
h0_9682:
    cmpi.w #3,$021C(a6)
    beq.s h0_9690
h0_968A:
    tst.l app_file_0186+fh_End(a6)
    bne.s h0_969E
h0_9690:
    btst.b #2,$021D(a6)
    bne.w h0_F954
h0_969A:
    bra.w h0_ExecAllocMem_9BC6
h0_969E:
    moveq.l #66,d0
    bra.w h0_846E
h0_96A4:
    tst.b $0103(a6)
    beq.s h0_96BC
h0_96AA:
    movea.l $013E(a6),a1
    btst.b #2,$021D(a6)
    bne.w h0_F82E
h0_96B8:
    bra.w h0_9A2C
h0_96BC:
    rts
h0_96BE:
    tst.b $0103(a6)
    beq.s h0_96BC
h0_96C4:
    movea.l $013E(a6),a1
    btst.b #2,$021D(a6)
    bne.w h0_F82E
h0_96D2:
    bra.w h0_9A2C
h0_96D6:
    tst.b $0103(a6)
    beq.s h0_96EA
h0_96DC:
    btst.b #2,$021D(a6)
    bne.w h0_F830
h0_96E6:
    bra.w h0_9A2E
h0_96EA:
    rts
    DC.L    $4a2e0103,$67f8082e,$0002021d,$66006134,$6000032e ; VIOLATION: orphaned code island at $96EC is not reached from known entrypoints
h0_9700:
    btst.b #2,$021D(a6)
    bne.w h0_F830
h0_970A:
    bra.w h0_9A2E
h0_970E:
    tst.b $011B(a6)
    bne.s h0_9728
h0_9714:
    tst.b $0103(a6)
    beq.s h0_96EA
h0_971A:
    btst.b #2,$021D(a6)
    bne.w h0_F868
h0_9724:
    bra.w h0_9A90
h0_9728:
    moveq.l #38,d0
    bra.w h0_8486
h0_972E:
    cmpi.b #255,$011B(a6)
    beq.s h0_9744
h0_9736:
    btst.b #2,$021D(a6)
    bne.w h0_F982
h0_9740:
    bra.w h0_9C38
h0_9744:
    rts
h0_9746:
    move.l $023C(a6),d2
    moveq.l #1,d1
    clr.b (a5)+
    add.l d1,$023C(a6)
    add.l d1,$0224(a6)
    tst.b $0238(a6)
    beq.s h0_9768
h0_975C:
    tst.b $0103(a6)
    beq.s h0_9768
h0_9762:
    bsr.s h0_972E
h0_9764:
    beq.s h0_9768
h0_9766:
    bsr.s h0_970E
h0_9768:
    movea.l $024C(a6),a5
    move.l a5,$0250(a6)
    rts
    DC.B    $08,$2e,$00,$02,$02,$1d,$66,$00,$02,$e8,$60,$00,$02,$d6 ; VIOLATION: orphaned code island at $9772 is not reached from known entrypoints
h0_9780:
    tst.b $011B(a6)
    bne.s h0_9794
h0_9786:
    btst.b #2,$021D(a6)
    bne.w h0_9C2A
h0_9790:
    bra.w h0_9C2A
h0_9794:
    moveq.l #79,d1
    bsr.w h0_9288
h0_979A:
    bra.w h0_8E92
h0_979E:
    moveq.l #40,d0
    jmp h0_846E.l
h0_97A6:
    tst.l app_file_0186+fh_Link(a6)
    bne.s h0_97C2
h0_97AC:
    movem.l d1-d2/a0-a2,-(a7)
    lea.l $06C8(a6),a0
    bsr.w h0_97C4
h0_97B8:
    bne.s h0_979E
h0_97BA:
    move.l d2,app_file_0186+fh_Link(a6)
    movem.l (a7)+,d1-d2/a0-a2
h0_97C2:
    rts
h0_97C4:
    lea.l $071A(a6),a1
    move.b (a0),d0
    beq.s h0_97E4
h0_97CC:
    cmp.b #$2E,d0
    bne.s h0_9826
h0_97D2:
    move.b $0001(a0),d0
    cmp.b #$2E,d0
    beq.s h0_9826
h0_97DC:
    cmp.b #$5C,d0
    beq.s h0_9826
h0_97E2:
    move.b (a0),d0
h0_97E4:
    move.l a1,d2
h0_97E6:
    tst.b (a1)+
    bne.s h0_97E6
h0_97EA:
    sub.l a1,d2
    neg.l d2
    tst.b d0
    bne.s h0_97F6
h0_97F2:
    bsr.w h0_964A
h0_97F6:
    subq.l #1,a1
    subq.b #1,d2
    bsr.w h0_9812
h0_97FE:
    bsr.w h0_B002                       ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_9802:
    lea.l $071A(a6),a0
    rts
h0_9808:
    lea.l $06C8(a6),a0
    lea.l $071A(a6),a1
    moveq.l #0,d2
h0_9812:
    cmp.b #$52,d2
    beq.s h0_9820
h0_9818:
    addq.b #1,d2
    move.b (a0)+,d1
    move.b d1,(a1)+
    bne.s h0_9812
h0_9820:
    lea.l $071A(a6),a0
    rts
h0_9826:
    tst.b (a0)+
    bne.s h0_9826
h0_982A:
    move.b -$0002(a0),d0
    cmp.b #$2F,d0
    beq.s h0_9856
h0_9834:
    cmp.b #$3A,d0
    beq.s h0_9856
h0_983A:
    lea.l $06C8(a6),a0
    bsr.w h0_B002                       ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_9842:
    beq.w h0_985E
h0_9846:
    bsr.s h0_9808
h0_9848:
    move.b #$2F,-$0001(a1)
h0_984E:
    lea.l $076C(a6),a0
    bsr.s h0_9812
h0_9854:
    bra.s h0_97F2
h0_9856:
    bsr.s h0_9808
h0_9858:
    subq.w #1,a1
    subq.b #1,d2
    bra.s h0_984E
h0_985E:
    lea.l $06C8(a6),a0
    rts
h0_9864:
    lea.l dat_9884(pc),a0
    move.l a0,$017A(a6)
    move.l $024C(a6),d1
    tst.b $011B(a6)
    bne.s h0_9888
h0_9876:
    btst.b #2,$021D(a6)
    bne.w h0_F92C
h0_9880:
    bra.w h0_9B40
dat_9884:
    DC.L    $42ae0182
h0_9888:
    rts
h0_988A:
    btst.b #2,$021D(a6)
    bne.w h0_F892
h0_9894:
    bra.w h0_9AA4
h0_9898:
    tst.b $0103(a6)
    beq.s h0_98AC
h0_989E:
    btst.b #2,$021D(a6)
    bne.w h0_F992
h0_98A8:
    bra.w h0_9DA6
h0_98AC:
    rts
h0_98AE:
    move.l app_file_0186+fh_Link(a6),d2
    beq.s h0_98BC
h0_98B4:
    bsr.w h0_DOSClose_AFB8              ; KNOWN: DOSBase _LVOClose fallback via local wrapper
h0_98B8:
    clr.l app_file_0186+fh_Link(a6)
h0_98BC:
    rts
    DC.B    $2f,$02 ; VIOLATION: orphaned code island at $98BE is not reached from known entrypoints
    DC.L    $203c0000,$113e9280,$6404d081,$7200204e,$2f012200,$6100eb4c,$221f66e4,$241f4e75
h0_98E0:
    btst.b #2,$021D(a6)
    bne.w h0_F9A6
h0_98EA:
    bra.w h0_A356
h0_98EE:
    btst.b #2,$021D(a6)
    bne.w h0_F9A2
h0_98F8:
    bra.w h0_A2CA
h0_98FC:
    tst.b $0112(a6)
    bne.s h0_991A
h0_9902:
    cmp.b #$1,d3
    bne.s h0_990C
h0_9908:
    st.b $0114(a6)
h0_990C:
    btst.b #2,$021D(a6)
    bne.w h0_F99E
h0_9916:
    bra.w h0_A2B6
h0_991A:
    rts
h0_991C:
    btst.b #2,$021D(a6)
    bne.w h0_F9A2
h0_9926:
    bra.w h0_A2D6
    DC.B    $08,$2e,$00,$02,$02,$1d,$66,$00,$60,$70,$60,$00,$09,$94 ; VIOLATION: orphaned code island at $992A is not reached from known entrypoints
h0_9938:
    btst.b #2,$021D(a6)
    bne.w h0_F9A2
h0_9942:
    bra.w h0_A2CA
h0_9946:
    btst.b #2,$021D(a6)
    bne.w h0_F9A6
h0_9950:
    bra.w h0_A32E
h0_9954:
    btst.b #2,$021D(a6)
    bne.w h0_F9A6
h0_995E:
    bra.w h0_A35E
h0_9962:
    tst.b $0106(a6)
    beq.s h0_996E
h0_9968:
    moveq.l #60,d0
    bra.w h0_8486
h0_996E:
    tst.b $0112(a6)
    bne.s h0_999C
h0_9974:
    movem.l d1-d2,-(a7)
    st.b $0114(a6)
    move.l a5,d0
    sub.l $024C(a6),d0
    add.l $023C(a6),d0
    pea.l dat_9998(pc)
    btst.b #2,$021D(a6)
    bne.w h0_F99C
h0_9994:
    bra.w h0_A2AA
dat_9998:
    DC.L    $4cdf0006
h0_999C:
    rts
    DC.B    $70,$00 ; VIOLATION: orphaned code island at $999E is not reached from known entrypoints
    DC.L    $102e0146,$220292ae,$023c082e,$0002021d,$66005e80,$6000007a
    DC.L    $7000102e,$0146222e,$023c082e,$0002021d,$66005e9a,$600000a0 ; VIOLATION: orphaned code island at $99B8 is not reached from known entrypoints
h0_99D0:
    moveq.l #-1,d0
    move.l a1,-(a7)
h0_99D4:
    move.b (a1)+,d1
    cmp.b #$A,d1
    beq.s h0_99E8
h0_99DC:
    cmp.b #$9,d1
    beq.s h0_99E8
h0_99E2:
    cmp.b #$20,d1
    bne.s h0_99D4
h0_99E8:
    move.l a1,d3
    movea.l (a7)+,a1
    sub.l a1,d3
    subq.l #1,d3
    beq.s h0_9A22
h0_99F2:
    moveq.l #0,d2
h0_99F4:
    addq.l #1,d0
    move.b (a2)+,d2
    beq.s h0_9A22
h0_99FA:
    cmp.b d2,d3
    bcs.s h0_9A22
h0_99FE:
    bne.s h0_9A1E
h0_9A00:
    movem.l d2-d3/a1-a2,-(a7)
h0_9A04:
    move.b (a1)+,d3
    ext.w d3
    move.b $7E(a6,d3.w),d3
    cmp.b (a2)+,d3
    bne.s h0_9A1A
h0_9A10:
    subq.b #1,d2
    bne.s h0_9A04
h0_9A14:
    movem.l (a7)+,d2-d3/a1-a2
    rts
h0_9A1A:
    movem.l (a7)+,d2-d3/a1-a2
h0_9A1E:
    adda.l d2,a2
    bra.s h0_99F4
h0_9A22:
    moveq.l #80,d0
    bsr.w h0_8486
h0_9A28:
    moveq.l #-1,d0
    rts
h0_9A2C:
    rts
h0_9A2E:
    rts
    DC.L    $4a2e0103,$671a226e,$01aa4a2e,$02386610,$222e023c,$92a9001c,$d3a90014,$2342001c
    DC.L    $70004e75 ; VIOLATION: orphaned code island at $9A30 is not reached from known entrypoints
    DC.L    $226e01aa,$0c6903eb,$00126700,$e9fad3ae,$024c1ad8,$538166fa ; VIOLATION: orphaned code island at $9A54 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $9A6E is not reached from known entrypoints
    DC.L    $02386718,$4a2e0103,$6712226e,$01aa0c69,$03eb0012,$67069481,$d5ae024c,$70004e75
h0_9A90:
    movea.l $01AA(a6),a0
    cmpi.w #1003,$0012(a0)
    beq.w h0_845A
h0_9A9E:
    add.l d1,$024C(a6)
    rts
h0_9AA4:
    tst.b $0238(a6)
    bne.w h0_9B0A
h0_9AAC:
    bsr.w h0_9B24
h0_9AB0:
    beq.s h0_9B04
h0_9AB2:
    movem.l a0-a1,-(a7)
    moveq.l #36,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_9ABC:
    movem.l (a7)+,a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.l a2,$0004(a0)
    clr.l $0014(a0)
    clr.l $001C(a0)
    clr.l $0018(a0)
    move.l #$3E9,$0010(a0)
    tst.l app_file_0186+fh_Pos(a6)
    beq.s h0_9AFE
h0_9AE2:
    movea.l app_file_0186+fh_Pos(a6),a1
    lea.l dat_9B6A(pc),a2
    bsr.w h0_99D0
h0_9AEE:
    bne.s h0_9AFE
h0_9AF0:
    add.w d0,d0
    add.w d0,d0
    lea.l dat_9BA2(pc),a2
    move.l $0(a2,d0.w),$0010(a0)
h0_9AFE:
    clr.l $0008(a0)
    movea.l a0,a1
h0_9B04:
    move.l a1,$01AA(a6)
    rts
h0_9B0A:
    bsr.s h0_9B24
h0_9B0C:
    bne.s h0_9B64
h0_9B0E:
    move.l $000C(a1),$024C(a6)
    bne.s h0_9B1E
h0_9B16:
    lea.l $05A8(a6),a0
    move.l a0,$024C(a6)
h0_9B1E:
    move.l a1,$01AA(a6)
    rts
h0_9B24:
    lea.l $01A6(a6),a0
    move.b $000E(a1),d0
h0_9B2C:
    tst.l (a0)
    beq.s h0_9B3C
h0_9B30:
    addq.b #1,d0
    beq.s h0_9B38
h0_9B34:
    movea.l (a0),a0
    bra.s h0_9B2C
h0_9B38:
    movea.l (a0),a1
    rts
h0_9B3C:
    moveq.l #-1,d0
    rts
h0_9B40:
    bsr.s h0_9B24
h0_9B42:
    bne.s h0_9B64
h0_9B44:
    tst.b $0238(a6)
    bne.s h0_9B5E
h0_9B4A:
    move.l $023C(a6),d2
    sub.l $001C(a1),d2
    add.l d2,$0014(a1)
    move.l $023C(a6),$001C(a1)
    rts
h0_9B5E:
    move.l a5,$000C(a1)
    rts
h0_9B64:
    moveq.l #77,d0
    bra.w h0_846E
dat_9B6A:
    DC.B    $03,$42
    DC.L    $53530443,$4f444504
    DC.B    "DATA"
    DC.L    $05425353,$5f430542
    DC.B    "SS_F"
    DC.L    $06434f44,$455f4306
    DC.B    "CODE_F"
    DC.B    $06
    DC.B    "DATA_C"
    DC.B    $06
    DC.B    "DATA_F",0
    DC.B    $00
dat_9BA2:
    DC.B    $00,$00
    DC.L    $03eb0000,$03e90000,$03ea4000,$03eb8000,$03eb4000,$03e98000,$03e94000,$03ea8000
    DC.B    $03,$ea
h0_ExecAllocMem_9BC6:
    move.l a4,-(a7)
    movea.l app_file_0186+fh_End(a6),a4
    lea.l $01A6(a6),a3
h0_ExecAllocMem_9BD0:
    tst.l (a3)
    beq.s h0_9C20
h0_ExecAllocMem_9BD4:
    movea.l (a3),a3
    move.l $0014(a3),d1
    beq.s h0_9C24
h0_ExecAllocMem_9BDC:
    move.l d1,d0
    andi.b #3,d0
    beq.s h0_ExecAllocMem_9BEA
h0_ExecAllocMem_9BE4:
    andi.b #252,d1
    addq.l #4,d1
h0_ExecAllocMem_9BEA:
    move.l d1,$0014(a3)
    tst.l app_file_0186+fh_End(a6)
    beq.s h0_9C02
h0_ExecAllocMem_9BF4:
    move.w $0010(a3),d0
    bsr.w h0_ExecAllocMem_AE02
h0_9BFC:
    bne.w h0_90EC
h0_9C00:
    bra.s h0_9C10
h0_9C02:
    cmpi.w #1003,$0012(a3)
    beq.s h0_9C24
h0_9C0A:
    addq.l #8,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_9C10:
    move.l a0,$0008(a3)
    move.l a0,$000C(a3)
    adda.l $0014(a3),a0
    clr.l -(a0)
    bra.s h0_ExecAllocMem_9BD0
h0_9C20:
    movea.l (a7)+,a4
    rts
h0_9C24:
    clr.l $000C(a3)
    bra.s h0_ExecAllocMem_9BD0
h0_9C2A:
    move.b d0,d1
    not.b d1
    bsr.w h0_8EB6
h0_9C32:
    moveq.l #46,d1
    bra.w h0_9288
h0_9C38:
    movea.l $01AA(a6),a1
    cmpi.w #1003,$0012(a1)
    rts
h0_9C44:
    movea.l app_file_0186+fh_Funcs(a6),a4
    tst.b $0104(a6)
    beq.s h0_9C9E
h0_9C4E:
    lea.l $01A6(a6),a3
h0_9C52:
    movea.l (a3),a3
    movea.l $0004(a3),a0
    move.b $000E(a0),d6
    movea.l $013E(a6),a1
    lea.l h0_9D02(pc),a2
    moveq.l #0,d7
    bsr.w h0_8CF6
h0_ExecAllocMem_9C6A:
    tst.l d7
    beq.s h0_9C9A
h0_ExecAllocMem_9C6E:
    move.l d7,d1
    addq.l #8,d1
    moveq.l #0,d0
    bsr.w h0_ExecAllocMem_AE02
h0_9C78:
    bne.w h0_90EC
h0_9C7C:
    move.l a4,-(a7)
    movea.l a0,a4
    move.l #$3F0,(a4)+
    lea.l h0_9D2A(pc),a2
    movea.l $013E(a6),a1
    movea.l $0004(a3),a0
    bsr.w h0_8CF6
h0_9C96:
    clr.l (a4)
    movea.l (a7)+,a4
h0_9C9A:
    tst.l (a3)
    bne.s h0_9C52
h0_9C9E:
    tst.b $0129(a6)
    beq.s h0_9CBE
h0_9CA4:
    lea.l $01A6(a6),a3
h0_9CA8:
    movea.l (a3),a3
    movea.l $0004(a3),a0
    move.b $000E(a0),d6
    lea.l h0_8C00(pc),a2
    bsr.w h0_8C9A
h0_9CBA:
    tst.l (a3)
    bne.s h0_9CA8
h0_9CBE:
    lea.l $01A6(a6),a3
h0_9CC2:
    movea.l (a3),a3
    tst.l $0018(a3)
    beq.s h0_9CFC
h0_9CCA:
    moveq.l #0,d3
    lea.l $01A6(a6),a2
    moveq.l #1,d6
h0_9CD2:
    movea.l (a2),a2
    movea.l $0004(a2),a0
    move.b $000E(a0),d3
    bsr.w h0_A164
h0_9CE0:
    beq.s h0_9CF8
h0_9CE2:
    bsr.w h0_A192
h0_9CE6:
    bne.s h0_9CF8
h0_9CE8:
    movea.l $0004(a0),a1
    adda.l $0008(a3),a1
    move.l $0008(a2),d1
    add.l d1,(a1)
    bra.s h0_9CE2
h0_9CF8:
    tst.l (a2)
    bne.s h0_9CD2
h0_9CFC:
    tst.l (a3)
    bne.s h0_9CC2
h0_9D00:
    rts
h0_9D02:
    cmp.b $000E(a1),d6
    bne.s h0_9D00
h0_9D08:
    cmpi.b #1,$000D(a1)
    bne.s h0_9D00
h0_9D10:
    moveq.l #0,d1
    move.b $0016(a1),d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_9D24
h0_9D1E:
    andi.b #252,d1
    addq.l #4,d1
h0_9D24:
    add.l d1,d7
    addq.l #8,d7
    rts
h0_9D2A:
    cmp.b $000E(a1),d6
    bne.s h0_9D00
h0_9D30:
    cmpi.b #1,$000D(a1)
    bne.s h0_9D00
h0_9D38:
    bsr.s h0_9D46
h0_9D3A:
    move.l $0008(a1),d0
    add.l $0008(a3),d0
    move.l d0,(a4)+
    rts
h0_9D46:
    moveq.l #0,d1
    move.b $0016(a1),d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_9D5A
h0_9D54:
    andi.b #252,d1
    addq.l #4,d1
h0_9D5A:
    lsr.l #2,d1
    move.l d1,(a4)+
    lea.l $0016(a1),a0
    move.b (a0)+,d0
h0_9D64:
    move.b (a0)+,(a4)+
    subq.b #1,d0
    bne.s h0_9D64
h0_9D6A:
    move.b $0016(a1),d0
    andi.b #3,d0
    beq.s h0_9D7E
h0_9D74:
    clr.b (a4)+
    addq.b #1,d0
    cmp.b #$4,d0
    bne.s h0_9D74
h0_9D7E:
    rts
h0_9D80:
    movem.l d6/a0-a2,-(a7)
    movea.l $0004(a0),a0
    move.b $000E(a0),d6
    lea.l dat_9DA2(pc),a2
    movea.l $013E(a6),a1
    moveq.l #0,d0
    bsr.w h0_8D1C
h0_9D9A:
    movem.l (a7)+,d6/a0-a2
    tst.l d0
    rts
dat_9DA2:
    DC.L    $52804e75 ; VIOLATION: orphaned code island at $9DA2 is not reached from known entrypoints
h0_9DA6:
    tst.l app_file_0186+fh_End(a6)
    bne.w h0_9C44
h0_9DAE:
    bsr.w h0_97A6
h0_9DB2:
    cmpi.w #3,$021C(a6)
    bne.s h0_9E34
h0_9DBA:
    bsr.w h0_A110
h0_9DBE:
    move.l #$3F3,d1
    bsr.w h0_A0EE
h0_9DC8:
    moveq.l #0,d1
    bsr.w h0_A0EE
h0_9DCE:
    moveq.l #0,d1
    lea.l $01A6(a6),a0
h0_9DD4:
    movea.l (a0),a0
    tst.l $0014(a0)
    bne.s h0_9DE0
h0_9DDC:
    bsr.s h0_9D80
h0_9DDE:
    beq.s h0_9DE2
h0_9DE0:
    addq.l #1,d1
h0_9DE2:
    tst.l (a0)
    bne.s h0_9DD4
h0_9DE6:
    bsr.w h0_A0EE
h0_9DEA:
    move.l d1,d2
    moveq.l #0,d1
    bsr.w h0_A0EE
h0_9DF2:
    move.l d2,d1
    subq.l #1,d1
    bsr.w h0_A0EE
h0_9DFA:
    lea.l $01A6(a6),a3
h0_9DFE:
    movea.l (a3),a3
    move.l $0014(a3),d1
    bne.s h0_9E0E
h0_9E06:
    movea.l a3,a0
    bsr.w h0_9D80
h0_9E0C:
    beq.s h0_9E1C
h0_9E0E:
    lsr.l #2,d1
    swap.w d1
    or.w $0010(a3),d1
    swap.w d1
    bsr.w h0_A0EE
h0_9E1C:
    tst.l (a3)
    bne.s h0_9DFE
h0_9E20:
    bsr.w h0_A0F6
h0_9E24:
    tst.b $0129(a6)
    beq.s h0_9E2E
h0_9E2A:
    bsr.w h0_A42E
h0_9E2E:
    lea.l $01A6(a6),a3
    bra.s h0_9E64
h0_9E34:
    move.l #$3E7,d1
    lea.l $01AE(a6),a1
    tst.b (a1)
    beq.s h0_9E50
h0_9E42:
    move.l a1,d0
h0_9E44:
    tst.b (a1)+
    bne.s h0_9E44
h0_9E48:
    subq.l #1,a1
    exg d0,a1
    sub.l a1,d0
    bra.s h0_9E5C
h0_9E50:
    movea.l $013E(a6),a1
    lea.l $0016(a1),a1
    move.b (a1)+,d0
    subq.b #1,d0
h0_9E5C:
    bsr.w h0_A1D0
h0_9E60:
    lea.l $01A6(a6),a3
h0_9E64:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_9E76
h0_9E6C:
    movea.l a3,a0
    bsr.w h0_9D80
h0_9E72:
    beq.w h0_9FF8
h0_9E76:
    cmpi.w #3,$021C(a6)
    beq.s h0_9E94
h0_9E7E:
    move.l #$3E8,d1
    movea.l $0004(a3),a1
    lea.l $0016(a1),a1
    move.b (a1)+,d0
    subq.b #1,d0
    bsr.w h0_A1D0
h0_9E94:
    lea.l $0014(a3),a0
    move.l (a0),d0
    lsr.l #2,d0
    move.l d0,(a0)
    subq.l #4,a0
    moveq.l #8,d1
    bsr.w h0_8422
h0_9EA6:
    cmpi.w #1003,$0012(a3)
    beq.s h0_9EBE
h0_9EAE:
    movea.l $0008(a3),a0
    move.l $0014(a3),d1
    add.l d1,d1
    add.l d1,d1
    bsr.w h0_8422
h0_9EBE:
    bsr.w h0_A110
h0_9EC2:
    tst.l $0018(a3)
    beq.w h0_9F6C
h0_9ECA:
    moveq.l #1,d6
    move.l #$3EC,d1
    bsr.s h0_9EF4
h0_9ED4:
    cmpi.w #3,$021C(a6)
    beq.w h0_9F6C
h0_9EDE:
    move.l #$3F8,d1
    moveq.l #40,d6
    bsr.s h0_9EF4
h0_9EE8:
    move.l #$3F9,d1
    moveq.l #41,d6
    bsr.s h0_9EF4
h0_9EF2:
    bra.s h0_9F6C
h0_9EF4:
    moveq.l #0,d3
    move.l d1,-(a7)
    pea.l $01A6(a6)
    clr.l -(a7)
h0_9EFE:
    movea.l $0004(a7),a0
h0_9F02:
    tst.l (a0)
    beq.s h0_9F5A
h0_9F06:
    movea.l (a0),a0
    subq.l #1,d3
    tst.l $0014(a0)
    bne.s h0_9F16
h0_9F10:
    bsr.w h0_9D80
h0_9F14:
    beq.s h0_9F02
h0_9F16:
    move.l a0,$0004(a7)
    bsr.w h0_A164
h0_9F1E:
    beq.s h0_9F4E
h0_9F20:
    move.l $0008(a7),d0
    beq.s h0_9F34
h0_9F26:
    move.l d1,-(a7)
    move.l d0,d1
    bsr.w h0_A0EE
h0_9F2E:
    move.l (a7)+,d1
    clr.l $0008(a7)
h0_9F34:
    bsr.w h0_A0EE
h0_9F38:
    move.l (a7),d1
    bsr.w h0_A0EE
h0_9F3E:
    bsr.w h0_A192
h0_9F42:
    bne.s h0_9F4E
h0_9F44:
    move.l $0004(a0),d1
    bsr.w h0_A0EE
h0_9F4C:
    bra.s h0_9F3E
h0_9F4E:
    addq.l #1,(a7)
    movea.l $013E(a6),a0
    cmp.b $000C(a0),d3
    bne.s h0_9EFE
h0_9F5A:
    tst.l $0008(a7)
    lea.l $000C(a7),a7
    bne.s h0_9F6A
h0_9F64:
    moveq.l #0,d1
    bra.w h0_A0EE
h0_9F6A:
    rts
h0_9F6C:
    cmpi.w #3,$021C(a6)
    beq.s h0_9FA6
h0_9F74:
    move.l #$3EF,d1
    bsr.w h0_A0EE
h0_9F7E:
    movea.l $0004(a3),a0
    move.b $000E(a0),d3
    movea.l $013E(a6),a1
    lea.l h0_A11A(pc),a2
    bsr.w h0_8D48
h0_9F92:
    move.b d3,d6
    lea.l dat_A034(pc),a2
    movea.l $013E(a6),a1
    bsr.w h0_8D1C
h0_9FA0:
    moveq.l #0,d1
    bsr.w h0_A0EE
h0_9FA6:
    tst.l $020C(a6)
    beq.s h0_9FBC
h0_9FAC:
    movem.l d2/a0-a1,-(a7)
    bsr.w h0_B054                       ; KNOWN: DOSBase _LVOSeek fallback via local wrapper
h0_9FB4:
    movem.l (a7)+,d2/a0-a1
    move.l d0,$0020(a3)
h0_9FBC:
    tst.b $0104(a6)
    beq.s h0_9FE6
h0_9FC2:
    movea.l $0004(a3),a0
    move.b $000E(a0),d6
    move.l #$3F0,d1
    bsr.w h0_A0EE
h0_9FD4:
    movea.l $013E(a6),a1
    lea.l h0_A04C(pc),a2
    bsr.w h0_8CF6
h0_9FE0:
    moveq.l #0,d1
    bsr.w h0_A0EE
h0_9FE6:
    tst.b $0129(a6)
    beq.w h0_9FF6
h0_9FEE:
    lea.l dat_8B4C(pc),a2
    bsr.w h0_8C9A
h0_9FF6:
    bsr.s h0_A01A
h0_9FF8:
    tst.l (a3)
    bne.w h0_9E64
h0_9FFE:
    lea.l $01A6(a6),a3
h0_A002:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_A028
h0_A00A:
    movea.l a3,a0
    bsr.w h0_9D80
h0_A010:
    bne.s h0_A028
h0_A012:
    tst.l (a3)
    bne.s h0_A002
h0_A016:
    bsr.w h0_A110
h0_A01A:
    move.l #$3F2,d1
    bsr.w h0_A0EE
h0_A024:
    bra.w h0_A0F6
h0_A028:
    tst.l $020C(a6)
    beq.s h0_A032
h0_A02E:
    bsr.w h0_A450
h0_A032:
    rts
dat_A034:
    DC.B    $70,$01,$0c,$29,$00,$01,$00,$0d,$67,$02,$70,$02 ; VIOLATION: orphaned code island at $A034 is not reached from known entrypoints
h0_A040:
    bsr.s h0_A098
h0_A042:
    move.l $0008(a1),d1
    bra.w h0_A0EE
h0_A04A:
    rts
h0_A04C:
    cmp.b $000E(a1),d6
    bne.s h0_A04A
h0_A052:
    cmpi.b #1,$000D(a1)
    bne.s h0_A04A
h0_A05A:
    btst.b #4,$000C(a1)
    bne.s h0_A04A
h0_A062:
    cmpi.w #3,$021C(a6)
    beq.s h0_A07C
h0_A06A:
    tst.b $0104(a6)
    bpl.s h0_A078
h0_A070:
    btst.b #5,$000C(a1)
    beq.s h0_A04A
h0_A078:
    moveq.l #0,d0
    bra.s h0_A040
h0_A07C:
    move.w $0012(a3),d0
    cmp.w #$3EA,d0
    beq.s h0_A092
h0_A086:
    cmp.w #$3E9,d0
    bne.s h0_A078
h0_A08C:
    addq.l #1,$0214(a6)
    bra.s h0_A078
h0_A092:
    addq.l #1,$0210(a6)
    bra.s h0_A078
h0_A098:
    moveq.l #0,d1
    move.b $0016(a1),d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_A0AC
h0_A0A6:
    andi.b #252,d1
    addq.l #4,d1
h0_A0AC:
    lsr.l #2,d1
    ror.l #8,d0
    or.l d0,d1
    bsr.s h0_A0EE
h0_A0B4:
    moveq.l #4,d0
    add.b $0016(a1),d0
    cmp.w d0,d4
    bcc.s h0_A0C0
h0_A0BE:
    bsr.s h0_A0F6
h0_A0C0:
    lea.l $0016(a1),a0
    move.b (a0)+,d0
h0_A0C6:
    move.b (a0)+,(a4)+
    subq.w #1,d4
    subq.b #1,d0
    bne.s h0_A0C6
h0_A0CE:
    move.b $0016(a1),d0
    andi.b #3,d0
    beq.s h0_A0E4
h0_A0D8:
    clr.b (a4)+
    addq.b #1,d0
    subq.w #1,d4
    cmp.b #$4,d0
    bne.s h0_A0D8
h0_A0E4:
    rts
h0_A0E6:
    addq.w #4,d4
    move.l d1,-(a7)
    bsr.s h0_A0F6
h0_A0EC:
    move.l (a7)+,d1
h0_A0EE:
    subq.w #4,d4
    bcs.s h0_A0E6
h0_A0F2:
    move.l d1,(a4)+
    rts
h0_A0F6:
    move.l #$80,d1
    sub.w d4,d1
    beq.s h0_A110
h0_A100:
    movem.l d0/d2/a0-a2,-(a7)
    lea.l $05A8(a6),a0
    bsr.w h0_8422
h0_A10C:
    movem.l (a7)+,d0/d2/a0-a2
h0_A110:
    lea.l $05A8(a6),a4
    move.w #$80,d4
    rts
h0_A11A:
    movem.l a1-a2,-(a7)
    moveq.l #2,d6
    move.w $0014(a1),d2
    bsr.s h0_A13C
h0_A126:
    moveq.l #4,d6
    bsr.s h0_A13C
h0_A12A:
    moveq.l #5,d6
    bsr.s h0_A13C
h0_A12E:
    moveq.l #7,d6
    bsr.s h0_A13C
h0_A132:
    moveq.l #8,d6
    bsr.s h0_A13C
h0_A136:
    movem.l (a7)+,a1-a2
    rts
h0_A13C:
    bsr.w h0_A164
h0_A140:
    beq.s h0_A162
h0_A142:
    movem.l d1-d2,-(a7)
    moveq.l #127,d0
    add.b d6,d0
    bsr.w h0_A098
h0_A14E:
    movem.l (a7)+,d1-d2
    bsr.s h0_A0EE
h0_A154:
    bsr.w h0_A192
h0_A158:
    bne.s h0_A162
h0_A15A:
    move.l $0004(a0),d1
    bsr.s h0_A0EE
h0_A160:
    bra.s h0_A154
h0_A162:
    rts
h0_A164:
    moveq.l #0,d1
    tst.l $0018(a3)
    beq.s h0_A17C
h0_A16C:
    bsr.s h0_A17E
h0_A16E:
    beq.s h0_A17C
h0_A170:
    bsr.s h0_A192
h0_A172:
    bne.s h0_A178
h0_A174:
    addq.l #1,d1
    bra.s h0_A170
h0_A178:
    bsr.s h0_A17E
h0_A17A:
    tst.l d1
h0_A17C:
    rts
h0_A17E:
    movea.l $0018(a3),a5
h0_A182:
    moveq.l #10,d5
    lea.l $000A(a5),a0
    move.l a0,$0006(a5)
    sub.w $0004(a5),d5
    rts
h0_A192:
    subq.w #1,d5
    bcs.s h0_A1C2
h0_A196:
    movea.l $0006(a5),a0
    addq.l #8,$0006(a5)
    cmp.b (a0),d6
    bne.s h0_A192
h0_A1A2:
    cmp.b $0001(a0),d3
    bne.s h0_A192
h0_A1A8:
    cmp.b #$1,d6
    beq.s h0_A1C0
h0_A1AE:
    cmp.b #$28,d6
    beq.s h0_A1C0
h0_A1B4:
    cmp.b #$29,d6
    beq.s h0_A1C0
h0_A1BA:
    cmp.w $0002(a0),d2
    bne.s h0_A192
h0_A1C0:
    rts
h0_A1C2:
    tst.l (a5)
    beq.s h0_A1CC
h0_A1C6:
    movea.l (a5),a5
    bsr.s h0_A182
h0_A1CA:
    bne.s h0_A192
h0_A1CC:
    moveq.l #-1,d0
    rts
h0_A1D0:
    lea.l $05A8(a6),a0
    move.l d1,(a0)+
    moveq.l #0,d1
    move.b d0,d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_A1E8
h0_A1E2:
    andi.b #252,d1
    addq.l #4,d1
h0_A1E8:
    lsr.l #2,d1
    move.l d1,(a0)+
    beq.s h0_A1FA
h0_A1EE:
    move.b (a1)+,(a0)+
    subq.b #1,d0
    bne.s h0_A1EE
h0_A1F4:
    clr.b (a0)+
    clr.b (a0)+
    clr.b (a0)+
h0_A1FA:
    add.l d1,d1
    add.l d1,d1
    addq.l #8,d1
    lea.l $05A8(a6),a0
    bra.w h0_8422
h0_A208:
    movea.l $01AA(a6),a0
    lea.l $0018(a0),a0
    tst.l (a0)
    beq.s h0_A220
h0_A214:
    movea.l (a0),a0
    tst.w $0004(a0)
    bne.s h0_A240
h0_A21C:
    tst.l (a0)
    bne.s h0_A214
h0_A220:
    movem.l d0-d2/a0/a2,-(a7)
    moveq.l #90,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_A22A:
    movem.l (a7)+,d0-d2/a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.w #$A,$0004(a0)
    lea.l $000A(a0),a1
    move.l a1,$0006(a0)
h0_A240:
    subq.w #1,$0004(a0)
    movea.l $0006(a0),a1
    addq.l #8,$0006(a0)
    movea.l a1,a0
    rts
h0_A250:
    movea.l $0940(a6),a0
    move.w (a0)+,d0
    cmp.w #$2B2B,d0
    bne.s h0_A288
h0_A25C:
    move.w (a0)+,d0
    bpl.s h0_A280
h0_A260:
    andi.w #255,d0
    cmpi.w #11565,(a0)
    bne.s h0_A280
h0_A26A:
    tst.b $0002(a0)
    bpl.s h0_A280
h0_A270:
    cmp.b $0003(a0),d0
    bne.s h0_A280
h0_A276:
    tst.w $0004(a0)
    bne.s h0_A288
h0_A27C:
    addq.l #4,a7
    rts
h0_A280:
    tst.w (a0)
    bne.s h0_A288
h0_A284:
    tst.w -(a0)
    rts
h0_A288:
    moveq.l #68,d0
    bra.w h0_8486
h0_A28E:
    add.l $023C(a6),d2
    add.l a5,d2
    sub.l $024C(a6),d2
h0_A298:
    tst.b $0103(a6)
    beq.s h0_A2A8
h0_A29E:
    bsr.w h0_A208
h0_A2A2:
    move.w d0,(a0)
    move.l d2,$0004(a0)
h0_A2A8:
    rts
h0_A2AA:
    move.l d0,d2
    move.w #$100,d0
    or.b $0146(a6),d0
    bra.s h0_A298
h0_A2B6:
    move.l d2,(a5)+
    bsr.s h0_A250
h0_A2BA:
    bpl.s h0_A2C4
h0_A2BC:
    ori.w #256,d0
    moveq.l #-4,d2
    bra.s h0_A28E
h0_A2C4:
    bsr.w h0_A36C
    DC.B    $02,$fc ; VIOLATION: decode failed in reachable code; region emitted as data
h0_A2CA:
    move.w d2,(a5)+
    bsr.s h0_A250
h0_A2CE:
    bmi.s h0_A288
h0_A2D0:
    bsr.w h0_A36C
    DC.B    $04,$fe ; VIOLATION: decode failed in reachable code; region emitted as data
h0_A2D6:
    cmpi.w #3,$021C(a6)
    bne.w h0_A312
h0_A2E0:
    move.w d2,(a5)+
    cmp.b #$1,d3
    beq.s h0_A288
h0_A2E8:
    movea.l $0940(a6),a0
    move.w (a0)+,d0
    cmp.w #$2B2B,d0
    bne.s h0_A288
h0_A2F4:
    move.w (a0)+,d0
    bpl.s h0_A288
h0_A2F8:
    cmpi.w #11565,(a0)
h0_A2FC:
    bne.s h0_A288
h0_A2FE:
    tst.b $0002(a0)
    bpl.s h0_A288
h0_A304:
    cmp.b $0003(a0),d0
    bne.s h0_A2FC
h0_A30A:
    tst.w $0004(a0)
    bne.s h0_A2FC
h0_A310:
    rts
h0_A312:
    cmp.b #$1,d3
    bne.s h0_A2CA
h0_A318:
    move.w d2,(a5)+
    bsr.w h0_A250
h0_A31E:
    bmi.s h0_A324
h0_A320:
    bsr.s h0_A36C
    DC.B    $07,$fe ; VIOLATION: decode failed in reachable code; region emitted as data
h0_A324:
    ori.w #10240,d0
    moveq.l #-2,d2
    bra.w h0_A28E
h0_A32E:
    cmpi.w #3,$021C(a6)
    beq.w h0_A288
h0_A338:
    cmp.b #$1,d3
    bne.s h0_A35E
h0_A33E:
    move.b d2,(a5)+
    bsr.w h0_A250
h0_A344:
    bmi.w h0_A34C
h0_A348:
    bsr.s h0_A36C
    DC.B    $08,$ff ; VIOLATION: decode failed in reachable code; region emitted as data
h0_A34C:
    ori.w #10496,d0
    moveq.l #-1,d2
    bra.w h0_A28E
h0_A356:
    sub.l $024C(a6),d2
    add.l a5,d2
    subq.l #2,d2
h0_A35E:
    move.b d2,(a5)+
    bsr.w h0_A250
h0_A364:
    bmi.w h0_A288
h0_A368:
    bsr.s h0_A36C
    DC.B    $05,$ff ; VIOLATION: decode failed in reachable code; region emitted as data
h0_A36C:
    tst.b $0103(a6)
    beq.s h0_A392
h0_A372:
    bsr.w h0_A208
h0_A376:
    movea.l (a7),a1
    move.b (a1)+,(a0)+
    move.b $0146(a6),(a0)+
    move.w d0,(a0)+
    move.b (a1)+,d2
    ext.w d2
    ext.l d2
    add.l $023C(a6),d2
    add.l a5,d2
    sub.l $024C(a6),d2
    move.l d2,(a0)+
h0_A392:
    addq.l #4,a7
    rts
h0_A396:
    lea.l dat_A3CC(pc),a0
    cmpi.w #3,$021C(a6)
    beq.s h0_A3A6
h0_A3A2:
    lea.l dat_A3BA(pc),a0
h0_A3A6:
    rts
h0_A3A8:
    lea.l dat_A3DD(pc),a0
    cmpi.w #3,$021C(a6)
    beq.s h0_A3A6
h0_A3B4:
    lea.l dat_A3C9(pc),a0
    rts
dat_A3BA:
    DC.B    $41,$6d,$69,$67,$61,$20,$6c,$69,$6e,$6b,$61,$62,$6c,$65,$00
dat_A3C9:
    DC.B    $2e,$6f,$00
dat_A3CC:
    DC.B    "Amiga executable",0
dat_A3DD:
    DC.B    $00,$2f,$08
    DC.L    $12d866fc,$137c002c,$ffff205f,$12d866fc,$53894e75
h0_A3F4:
    tst.b $0104(a6)
    beq.s h0_A42C
h0_A3FA:
    lea.l $01A6(a6),a3
h0_A3FE:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_A40E
h0_A406:
    movea.l a3,a0
    bsr.w h0_9D80
h0_A40C:
    beq.s h0_A428
h0_A40E:
    move.w $0012(a3),d0
    cmp.w #$3EA,d0
    beq.s h0_A424
h0_A418:
    cmp.w #$3E9,d0
    bne.s h0_A428
h0_A41E:
    addq.l #1,$0204(a6)
    bra.s h0_A428
h0_A424:
    addq.l #1,$0208(a6)
h0_A428:
    tst.l (a3)
    bne.s h0_A3FE
h0_A42C:
    rts
h0_A42E:
    bsr.w h0_B054                       ; KNOWN: DOSBase _LVOSeek fallback via local wrapper
h0_A432:
    move.l d0,$020C(a6)
    moveq.l #11,d1
    add.l $0204(a6),d1
    add.l $0208(a6),d1
    add.l $0200(a6),d1
    lsl.l #2,d1
    movea.l a6,a0
    bsr.w h0_8422
h0_A44C:
    bra.w h0_A110
h0_A450:
    move.l $020C(a6),d2
    bsr.w h0_B042                       ; KNOWN: DOSBase _LVOSeek fallback via local wrapper
h0_A458:
    bsr.w h0_A110
h0_A45C:
    move.l #$3F1,d1
    bsr.w h0_A0EE
h0_A466:
    moveq.l #9,d1
    add.l $0204(a6),d1
    add.l $0208(a6),d1
    add.l $0200(a6),d1
    bsr.w h0_A0EE
h0_A478:
    moveq.l #0,d1
    bsr.w h0_A0EE
h0_A47E:
    move.l #$48454144,d1
    bsr.w h0_A0EE
h0_A488:
    move.l #$44424756,d1
    bsr.w h0_A0EE
h0_A492:
    move.l #$30310000,d1
    bsr.w h0_A0EE
h0_A49C:
    move.l $0210(a6),d1
    bsr.w h0_A0EE
h0_A4A4:
    move.l $0214(a6),d1
    bsr.w h0_A0EE
h0_A4AC:
    move.l $0200(a6),d1
    bsr.w h0_A0EE
h0_A4B4:
    lea.l h0_A522(pc),a2
    bsr.w h0_8A26
h0_A4BC:
    move.l $0208(a6),d1
    bsr.w h0_A0EE
h0_A4C4:
    move.l #$3EA,d3
    bsr.w h0_A4E4
h0_A4CE:
    move.l $0204(a6),d1
    bsr.w h0_A0EE
h0_A4D6:
    move.l #$3E9,d3
    bsr.w h0_A4E4
h0_A4E0:
    bra.w h0_A0F6
h0_A4E4:
    tst.b $0104(a6)
    beq.s h0_A520
h0_A4EA:
    moveq.l #0,d2
    lea.l $01A6(a6),a3
h0_A4F0:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_A500
h0_A4F8:
    movea.l a3,a0
    bsr.w h0_9D80
h0_A4FE:
    beq.s h0_A51A
h0_A500:
    move.w $0012(a3),d0
    cmp.w d0,d3
    bne.s h0_A51A
h0_A508:
    moveq.l #0,d1
    move.b d2,d1
    ror.b #8,d1
    add.l $0020(a3),d1
    move.b d2,-(a7)
    bsr.w h0_A0EE
h0_A518:
    move.b (a7)+,d2
h0_A51A:
    addq.b #1,d2
    tst.l (a3)
    bne.s h0_A4F0
h0_A520:
    rts
h0_A522:
    moveq.l #0,d2
    lea.l $01A6(a6),a3
h0_A528:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_A538
h0_A530:
    movea.l a3,a0
    bsr.w h0_9D80
h0_A536:
    beq.s h0_A54A
h0_A538:
    lea.l dat_A550(pc),a2
    movea.l $0004(a3),a0
    move.b $000E(a0),d6
    bsr.w h0_8C9A
h0_A548:
    addq.b #1,d2
h0_A54A:
    tst.l (a3)
    bne.s h0_A528
h0_A54E:
    rts
dat_A550:
    DC.L    $72001202,$e019d2a8,$001c2f08,$6100fb90 ; VIOLATION: orphaned code island at $A550 is not reached from known entrypoints
    DC.B    " _Nu"
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$00000000,$00000000
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$01010001,$01010101,$01010101,$01010101,$01010101
    DC.L    $01000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010100
    DC.L    $01000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010101
dat_A664:
    DC.L    $80818283,$84858687,$88898a8b,$8c8d8e8f,$90919293,$94959697,$98999a9b,$9c9d9e9f
    DC.L    $a0a1a2a3,$a4a5a6a7,$a8a9aaab,$acadaeaf,$b0b1b2b3,$b4b5b6b7,$b8b9babb,$bcbdbebf
    DC.L    $c0c1c2c3,$c4c5c6c7,$c8c9cacb,$cccdcecf,$d0d1d2d3,$d4d5d6d7,$d8d9dadb,$dcdddedf
    DC.L    $c0c1c2c3,$c4c5c6c7,$c8c9cacb,$cccdcecf,$d0d1d2d3,$d4d5d6f7,$d8d9dadb,$dcdddeff
    DC.L    $00010203,$04050607,$08090a0b,$0c0d0e0f,$10111213,$14151617,$18191a1b,$1c1d1e1f
    DC.B    " !",$22,"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[",$5c,"]^_`ABCDEFGHIJKLMNOPQRSTUVWXYZ{|}~"
    DC.B    $7f
dat_A764:
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$0101ff01,$00000000,$00000000,$00000101,$01010100
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010100
    DC.L    $01000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010101
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$00000000,$00000000
h0_A864:
    move.l d3,-(a7)
    move.l app_file_0CDA+fh_Link(a6),d1
    bne.s h0_DOSWrite_A878
h0_DOSOutput_A86C:
    moveq.l #_LVOOutput,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOOutput fallback via local wrapper
h0_DOSWrite_A872:
    move.l d0,app_file_0CDA+fh_Link(a6)
    move.l d0,d1
h0_DOSWrite_A878:
    lea.l $0DF6(a6),a0
    move.l a0,d2
    moveq.l #0,d3
    move.w $0DEE(a6),d3
    moveq.l #_LVOWrite,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOWrite fallback via local wrapper
h0_ExecSetSignal_A88A:
    move.l (a7)+,d3
    bsr.w h0_ExecSetSignal_AB86
h0_A890:
    clr.w $0DEE(a6)
    lea.l $0DF6(a6),a0
    move.l a0,$0DF0(a6)
    rts
h0_A89E:
    cmpi.w #130,$0DEE(a6)
    beq.s h0_DOSOutput_A8BC
h0_A8A6:
    movea.l $0DF0(a6),a0
    move.b d1,(a0)+
    move.l a0,$0DF0(a6)
    addq.w #1,$0DEE(a6)
    cmp.b #$A,d1
    beq.s h0_A864
h0_A8BA:
    rts
h0_DOSOutput_A8BC:
    move.w d1,-(a7)
    bsr.s h0_A864                       ; KNOWN: DOSBase _LVOOutput fallback via local wrapper
h0_A8C0:
    move.w (a7)+,d1
    bra.s h0_A89E
h0_A8C4:
    move.w d1,-(a7)
    lea.l dat_A8DE(pc),a0
h0_A8CA:
    move.b (a0)+,d1
    beq.s h0_A8DA
h0_A8CE:
    bpl.s h0_A8D2
h0_A8D0:
    move.w (a7),d1
h0_A8D2:
    move.l a0,-(a7)
    bsr.s h0_A89E
h0_A8D6:
    movea.l (a7)+,a0
    bra.s h0_A8CA
h0_A8DA:
    addq.l #2,a7
    rts
dat_A8DE:
    DC.B    $1b,$5b,$33,$33,$3b,$37,$6d,$ff,$1b,$5b,$30,$6d,$00,$00 ; VIOLATION: orphaned code island at $A8DE is not reached from known entrypoints
h0_A8EC:
    move.l d1,-(a7)
    exg d3,d1
    move.l a0,d2
    moveq.l #_LVOWrite,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOWrite fallback via local wrapper
h0_ExecSetSignal_A8F8:
    bsr.w h0_ExecSetSignal_AB86
h0_A8FC:
    cmp.l (a7)+,d1
    rts
h0_DOSClose_A900:
    cmp.l app_file_0CDA+fh_Link(a6),d3
    beq.s h0_A90E
h0_DOSClose_A906:
    move.l d3,d1
    moveq.l #_LVOClose,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOClose fallback via local wrapper
h0_A90E:
    rts
h0_ExecAllocMem_A910:
    movea.l (a7)+,a3
    clr.b -$1(a0,d0.l)
    movea.l a0,a4
    moveq.l #MEMF_PUBLIC,d1
    move.l #$1140,d0
    movea.l $0004.w,a6
    jsr _LVOAllocMem(a6)
h0_A928:
    tst.l d0
    bne.s h0_ExecOpenLibrary
    moveq.l #103,d0
    rts
h0_ExecOpenLibrary:
    movea.l d0,a6
    addq.l #2,a6
    clr.l app_slot_01A2(a6)
    clr.l app_file_0CDA+fh_Link(a6)
    lea.l dat_B0A0(pc),a1
    moveq.l #0,d0
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOOpenLibrary(a6)
h0_ExecFreeMem_A94C:
    movea.l (a7)+,a6
    tst.l d0
    bne.s h0_A968
h0_ExecFreeMem_A952:
    lea.l -$0002(a6),a1
    move.l #$1140,d0
    movea.l $0004.w,a6
    jsr _LVOFreeMem(a6)
h0_A964:
    moveq.l #127,d0
    rts
h0_A968:
    move.l d0,app_DOSBase(a6)
    clr.b $0DF4(a6)
    move.l a4,$0228(a6)
    move.l a7,app_file_0CDA+fh_Interactive(a6)
    move.l #$1140,$0DEA(a6)
    move.l a3,-(a7)
    bra.w h0_A890
h0_A986:
    movea.l d2,a0
    cmpi.l #1145394720,(a0)
    bne.s h0_A9B8
h0_A990:
    move.l a0,app_slot_01A2(a6)
    clr.l $0012(a0)
    clr.l $0016(a0)
    clr.l $001A(a0)
    clr.l $001E(a0)
    tst.b $0010(a0)
    bne.s h0_A9B8
h0_A9AA:
    lea.l $0012(a0),a0
    move.l a0,app_file_0186+fh_End(a6)
    addq.w #4,a0
    move.l a0,app_file_0186+fh_Funcs(a6)
h0_A9B8:
    moveq.l #0,d0
    rts
h0_A9BC:
    movea.l $0228(a6),a0
    move.b (a0),d0
    cmp.b #$3F,d0
    bne.s h0_AA08
h0_A9C8:
    lea.l dat_AAB6(pc),a0
    bsr.w h0_9292
h0_DOSOutput_A9D0:
    bsr.w h0_A864                       ; KNOWN: DOSBase _LVOOutput fallback via local wrapper
h0_A9D4:
    move.l #MEMF_LOCAL,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_DOSInput_A9DE:
    move.l a0,-(a7)
    moveq.l #_LVOInput,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOInput fallback via local wrapper
h0_DOSRead_A9E6:
    move.l d0,d1
    move.l (a7),d2
    move.l #$100,d3
    moveq.l #_LVORead,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVORead fallback via local wrapper
h0_A9F6:
    cmp.b #$1,d0
    ble.w h0_AAAE
h0_A9FE:
    movea.l (a7)+,a0
    move.l a0,$0228(a6)
    clr.b -$1(a0,d0.w)
h0_AA08:
    sf.b $0840(a6)
    sf.b $0841(a6)
    sf.b $0842(a6)
    jsr h0_AB00.l
h0_ExecOpenDevice:
    clr.b $071A(a6)
    clr.b $021B(a6)
    sf.b $0C26(a6)
    st.b $0103(a6)
    sf.b $00FE(a6)
    sf.b $00FF(a6)
    sf.b $0100(a6)
    lea.l dat_AAA0(pc),a0
    moveq.l #0,d0
    lea.l app_dest_10B0+TV_SIZE(a6),a1
    moveq.l #0,d0
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOOpenDevice(a6)
h0_AA4C:
    movea.l (a7)+,a6
    tst.b d0
    bne.s h0_AA70
h0_AA52:
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a0
    cmpi.w #36,LIB_VERSION(a0)
    bcs.w h0_AA70
h0_AA60:
    lea.l app_dest_10A8+TV_SECS(a6),a0
    pea.l (a6)
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVOGetSysTime(a6)
h0_AA6E:
    movea.l (a7)+,a6
h0_AA70:
    move.w #$3,$021C(a6)
    clr.l $022C(a6)
    clr.l $0230(a6)
    tst.l app_slot_01A2(a6)
    bne.s h0_AA9C
h0_AA84:
    lea.l dat_AAF4(pc),a0
    bsr.w h0_B0AC
h0_AA8C:
    bne.s h0_AA98
h0_AA8E:
    lea.l dat_AAE9(pc),a0
    bsr.w h0_B0AC
h0_AA96:
    beq.s h0_AA9C
h0_AA98:
    move.l a0,$022C(a6)
h0_AA9C:
    moveq.l #0,d0
    rts
dat_AAA0:
    DC.B    $74,$69,$6d,$65,$72,$2e,$64,$65,$76,$69,$63,$65,$00,$00
h0_AAAE:
    bsr.w h0_90F2
h0_AAB2:
    bra.w h0_DOSOutput_ACA4
dat_AAB6:
    DC.B    "FROM/A,TO/K,WITH/K,INCDIR/K/M,HEADER/K/M,QUIET/S: ",0
dat_AAE9:
    DC.B    $45,$4e,$56,$3a,$64,$65,$76,$70,$61,$63,$2f
dat_AAF4:
    DC.B    $67,$65,$6e,$61,$6d,$2e,$6f,$70,$74,$73,$00,$00
h0_AB00:
    movea.l $0228(a6),a4
    bra.w h0_AB16
h0_AB08:
    move.l $0230(a6),d0
    bra.s h0_AB12
h0_AB0E:
    move.l $022C(a6),d0
h0_AB12:
    beq.s h0_AB28
h0_AB14:
    movea.l d0,a4
h0_AB16:
    jsr h0_3A6C.l
h0_AB1C:
    bne.w h0_AB28
h0_AB20:
    tst.b d1
    beq.s h0_AB28
h0_AB24:
    move.b (a4),d1
    bne.s h0_AB16
h0_AB28:
    rts
h0_AB2A:
    rts
h0_AB2C:
    move.l a0,d1
    move.l #MODE_NEWFILE,d2
    move.l d3,-(a7)
    moveq.l #0,d3
    moveq.l #_LVOOpen,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_AB3E:
    move.l (a7)+,d3
    tst.l d0
    beq.w h0_AB4A
h0_AB46:
    move.l d0,app_file_0956+fh_Link(a6)
h0_AB4A:
    eori #4,ccr
    rts
h0_AB50:
    tst.b $0955(a6)
    beq.s h0_AB84
h0_AB56:
    tst.w $0B68(a6)
    bmi.s h0_AB84
h0_AB5C:
    moveq.l #10,d1
    bsr.w h0_917C
h0_AB62:
    move.l app_file_0956+fh_Link(a6),d1
    cmp.l app_file_0CDA+fh_Link(a6),d1
    beq.s h0_AB7A
h0_AB6C:
    cmpi.w #10752,$078E(a6)
    beq.s h0_AB7A
h0_AB74:
    moveq.l #12,d1
    bsr.w h0_917C
h0_AB7A:
    clr.w $0B66(a6)
    move.w #$FFFF,$0B68(a6)
h0_AB84:
    rts
h0_ExecSetSignal_AB86:
    movem.l d0-d2/a0-a2,-(a7)
    moveq.l #0,d0
    moveq.l #0,d1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOSetSignal(a6)
h0_ExecSetSignal_AB98:
    movea.l (a7)+,a6
    btst #12,d0
    beq.s h0_ABBA
    ori.b #127,$0115(a6)
    moveq.l #0,d0
    move.l #SIGBREAKF_CTRL_C,d1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOSetSignal(a6)
    movea.l (a7)+,a6
h0_ABBA:
    movem.l (a7)+,d0-d2/a0-a2
h0_ABBE:
    rts
h0_ABC0:
    tst.b $0127(a6)
    bne.s h0_ABBE
h0_ABC6:
    move.l $0DEA(a6),d1
    bsr.w h0_8F04
h0_ABCE:
    lea.l dat_AC70(pc),a0
    bsr.w h0_9292
h0_ABD6:
    tst.b app_timer_device_iorequest+IO_ERROR(a6)
    bne.w h0_AC68
h0_ABDE:
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a0
    cmpi.w #36,LIB_VERSION(a0)
    bcs.w h0_ExecCloseDevice
h0_ABEC:
    lea.l app_dest_10B0+TV_SECS(a6),a0
    pea.l (a6)
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVOGetSysTime(a6)
h0_ABFA:
    movea.l (a7)+,a6
    lea.l app_dest_10B0+TV_SECS(a6),a0
    lea.l app_dest_10A8+TV_SECS(a6),a1
    pea.l (a6)
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVOSubTime(a6)
h0_AC0E:
    movea.l (a7)+,a6
    lea.l dat_AC7C(pc),a0
    bsr.w h0_9292
h0_AC18:
    move.l app_dest_10B0+TV_SECS(a6),d1
    bsr.w h0_8F04
h0_AC20:
    moveq.l #46,d1
    bsr.w h0_9288
h0_AC26:
    clr.l -(a7)
    clr.l -(a7)
    move.l #$30303030,d0
    move.l d0,-(a7)
    move.w d0,-(a7)
    lea.l $0006(a7),a3
    lea.l dat_AC6C(pc),a2
    move.l app_dest_10B0+TV_MICRO(a6),d1
    bsr.w h0_8F08
h0_AC44:
    lea.l -$0006(a3),a0
    bsr.w h0_9292
h0_AC4C:
    lea.l $000E(a7),a7
    lea.l dat_AC84(pc),a0
    bsr.w h0_9292
h0_ExecCloseDevice:
    lea.l app_dest_10B0+TV_SIZE(a6),a1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOCloseDevice(a6)
h0_AC66:
    movea.l (a7)+,a6
h0_AC68:
    bra.w h0_8E8C
dat_AC6C:
    DC.L    $16c14e75 ; VIOLATION: orphaned code island at $AC6C is not reached from known entrypoints
dat_AC70:
    DC.B    $20,$62,$79,$74,$65,$73,$20,$75,$73,$65,$64,$00
dat_AC7C:
    DC.B    $2c,$20,$74,$6f,$6f,$6b,$20,$00
dat_AC84:
    DC.B    $20,$73,$65,$63,$6f,$6e,$64,$73,$00
dat_AC8D:
    DC.B    "Press any key to exit",0
    DC.B    $00
h0_DOSOutput_ACA4:
    bsr.w h0_A864                       ; KNOWN: DOSBase _LVOOutput fallback via local wrapper
h0_DOSWrite_ACA8:
    tst.b $0C26(a6)
    beq.s h0_ACC2
h0_DOSWrite_ACAE:
    lea.l dat_AC8D(pc),a0
    move.l a0,d2
    moveq.l #21,d3
    move.l app_file_0CDA+fh_Link(a6),d1
    moveq.l #_LVOWrite,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOWrite fallback via local wrapper
h0_ACC0:
    bsr.s h0_DOSInput_ACF4              ; KNOWN: DOSBase _LVOInput fallback via local wrapper
h0_ACC2:
    movea.l app_file_0CDA+fh_Interactive(a6),a7
    movea.l app_DOSBase(a6),a1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOCloseLibrary(a6)
h0_ExecFreeMem_ACD4:
    movea.l (a7)+,a6
    move.b $023A(a6),d4
    lea.l -$0002(a6),a1
    move.l #$1140,d0
    movea.l $0004.w,a6
    jsr _LVOFreeMem(a6)
h0_ACEC:
    move.b d4,d0
    ext.w d0
    ext.l d0
    rts
h0_DOSInput_ACF4:
    moveq.l #_LVOInput,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOInput fallback via local wrapper
h0_DOSRead_ACFA:
    move.l d0,d1
    clr.w -(a7)
    move.l a7,d2
    moveq.l #1,d3
    moveq.l #_LVORead,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVORead fallback via local wrapper
h0_AD08:
    move.b (a7)+,d1
    rts
h0_AD0C:
    lea.l -$000C(a7),a7
    move.l a7,d1
    move.l #$FFFFFF40,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVODateStamp fallback via local wrapper
h0_AD1C:
    move.l (a7),d0
    lea.l $000C(a7),a7
    divu.w #$5B5,d0
    add.w d0,d0
    add.w d0,d0
    addi.w #78,d0
    move.w d0,d1
    swap.w d0
h0_AD32:
    tst.w d0
    beq.s h0_AD52
h0_AD36:
    move.w #$16D,d2
    btst #1,d1
    bne.s h0_AD48
h0_AD40:
    btst #0,d1
    bne.s h0_AD48
h0_AD46:
    addq.w #1,d2
h0_AD48:
    cmp.w d2,d0
    blt.s h0_AD52
h0_AD4C:
    sub.w d2,d0
    addq.w #1,d1
    bra.s h0_AD32
h0_AD52:
    addq.w #1,d0
    lea.l dat_ADD2(pc),a0
    moveq.l #1,d4
h0_AD5A:
    moveq.l #0,d2
    move.b (a0)+,d2
    cmp.b #$2,d4
    bne.s h0_AD72
h0_AD64:
    btst #0,d1
    bne.s h0_AD72
h0_AD6A:
    btst #1,d1
    bne.s h0_AD72
h0_AD70:
    addq.w #1,d2
h0_AD72:
    cmp.w d2,d0
    ble.s h0_AD80
h0_AD76:
    sub.w d2,d0
    addq.w #1,d4
    cmp.w #$D,d4
    bne.s h0_AD5A
h0_AD80:
    move.w d1,-(a7)
    move.w d4,d1
    add.w d1,d1
    add.w d4,d1
    lea.l dat_ADDB(pc,d1.w),a0
    move.w (a7)+,d1
    move.b (a0)+,(a3)+
    move.b (a0)+,(a3)+
    move.b (a0)+,(a3)+
    move.b #$20,(a3)+
    cmp.w #$A,d0
    blt.s h0_ADA2
h0_AD9E:
    bsr.s h0_ADBC
h0_ADA0:
    bra.s h0_ADA4
h0_ADA2:
    bsr.s h0_ADCA
h0_ADA4:
    move.b #$20,(a3)+
    move.w d1,d0
    ext.l d0
    addi.w #1900,d0
    divu.w #$64,d0
    move.l d0,d1
    bsr.s h0_ADBC
h0_ADB8:
    move.l d1,d0
    swap.w d0
h0_ADBC:
    swap.w d0
    clr.w d0
    swap.w d0
    divu.w #$A,d0
    bsr.s h0_ADCA
h0_ADC8:
    swap.w d0
h0_ADCA:
    addi.b #48,d0
    move.b d0,(a3)+
    rts
dat_ADD2:
    DC.B    $1f,$1c,$1f,$1e,$1f,$1e,$1f,$1f,$1e
dat_ADDB:
    DC.B    $1f
    DC.L    $1e1f4a61
    DC.B    "nFebMarAprMayJunJulAugSepOctNovDec"
h0_ExecAllocMem_AE02:
    addq.l #8,d1
    movem.l d1/a1,-(a7)
    rol.w #3,d0
    andi.l #6,d0
    ori.l #65537,d0
    exg d0,d1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOAllocMem(a6)
h0_AE22:
    movea.l (a7)+,a6
    movem.l (a7)+,d1/a1
    tst.l d0
    beq.s h0_AE3E
h0_AE2C:
    movea.l d0,a0
    move.l d1,(a0)+
    lsr.l #2,d0
    addq.l #1,d0
    move.l d0,(a4)
    movea.l a0,a4
    clr.l (a0)+
    moveq.l #0,d0
    rts
h0_AE3E:
    moveq.l #-1,d0
    rts
h0_AE42:
    addq.l #4,d1
    move.l d1,-(a7)
    move.l d1,d0
    moveq.l #MEMF_PUBLIC,d1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOAllocMem(a6)
h0_AE54:
    movea.l (a7)+,a6
    move.l (a7)+,d1
    tst.l d0
    beq.s h0_AE64
h0_AE5C:
    movea.l d0,a0
    move.l d1,(a0)+
    add.l d1,$0DEA(a6)
h0_AE64:
    rts
h0_ExecFreeMem_AE66:
    movea.l a0,a1
    move.l -(a1),d0
    sub.l d0,$0DEA(a6)
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFreeMem(a6)
h0_AE78:
    movea.l (a7)+,a6
    rts
h0_AE7C:
    lea.l $0016(a1),a0
    moveq.l #0,d0
    move.b (a0)+,d0
    lea.l -$1(a0,d0.w),a1
    clr.b (a1)
    move.l a1,-(a7)
    bsr.s h0_AEB4
h0_AE8E:
    movea.l (a7)+,a1
    move.b #$B,(a1)
    tst.l d4
    eori #4,ccr
    rts
h0_AE9C:
    movem.l d1/a0,-(a7)
h0_AEA0:
    move.b (a0)+,d1
    cmp.b #$3A,d1
    beq.s h0_AEAE
h0_AEA8:
    tst.b d1
    bne.s h0_AEA0
h0_AEAC:
    moveq.l #-1,d1
h0_AEAE:
    movem.l (a7)+,d1/a0
h0_AEB2:
    rts
h0_AEB4:
    bsr.s h0_AE9C
h0_AEB6:
    beq.s h0_AEFE
h0_AEB8:
    move.l a0,-(a7)
    bsr.w h0_AEFE
h0_AEBE:
    movea.l (a7)+,a0
    tst.l d4
    bne.s h0_AEB2
h0_AEC4:
    movea.l $0C2C(a6),a2
    move.l a0,-(a7)
h0_AECA:
    move.b (a0)+,(a2)+
    bne.s h0_AECA
h0_AECE:
    move.l $0832(a6),-(a7)
    lea.l $0C30(a6),a0
h0_AED6:
    bsr.s h0_AEFE
h0_AED8:
    movea.l (a7)+,a1
    movea.l (a7)+,a0
    tst.l d4
    bne.s h0_AEFC
h0_AEE0:
    tst.b (a1)
    beq.s h0_AEFC
h0_AEE4:
    move.l a0,-(a7)
    lea.l $0E78(a6),a2
h0_AEEA:
    move.b (a1)+,(a2)+
    bne.s h0_AEEA
h0_AEEE:
    subq.l #1,a2
h0_AEF0:
    move.b (a0)+,(a2)+
    bne.s h0_AEF0
h0_AEF4:
    move.l a1,-(a7)
    lea.l $0E78(a6),a0
    bra.s h0_AED6
h0_AEFC:
    rts
h0_AEFE:
    tst.b $010A(a6)
    beq.s h0_DOSOpen
h0_AF04:
    lea.l app_timer_device_iorequest+IOSTD_SIZE(a6),a2
    move.l a0,-(a7)
h0_AF0A:
    move.b (a0)+,(a2)+
    bne.s h0_AF0A
h0_AF0E:
    lea.l app_timer_device_iorequest+IOSTD_SIZE(a6),a0
    lea.l dat_9656(pc),a2
    bsr.w h0_45CE
h0_AF1A:
    bsr.w h0_DOSOpen                    ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_AF1E:
    movea.l (a7)+,a0
    tst.l d4
    beq.s h0_DOSOpen
h0_AF24:
    neg.l d1
    rts
h0_DOSOpen:
    move.l a0,-(a7)
    move.l a0,d1
    move.l #MODE_OLDFILE,d2
    moveq.l #_LVOOpen,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_AF38:
    move.l (a7)+,d1
    move.l d0,d4
    beq.w h0_AFB6
h0_AF40:
    move.l app_slot_01A2(a6),d0
    beq.s h0_AF52
h0_AF46:
    movea.l d0,a0
    tst.l $0008(a0)
    beq.s h0_AF52
h0_AF4E:
    moveq.l #-1,d1
    rts
h0_AF52:
    move.l d4,-(a7)
    moveq.l #ACCESS_READ,d2
    moveq.l #_LVOLock,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOLock fallback via local wrapper
h0_DOSExamine_AF5C:
    move.l d0,d4
    beq.w h0_DOSClose_AF8A
h0_DOSExamine_AF62:
    move.l d0,d1
    lea.l app_fileinfoblock+fib_DiskKey(a6),a0
    move.l a0,d2
    move.l d2,d0
    andi.b #3,d0
    beq.s h0_DOSExamine_AF78
h0_DOSExamine_AF72:
    andi.b #252,d2
    addq.l #4,d2
h0_DOSExamine_AF78:
    moveq.l #_LVOExamine,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOExamine fallback via local wrapper
h0_AF7E:
    move.l d0,-(a7)
    move.l d4,d1
    moveq.l #_LVOUnLock,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOUnLock fallback via local wrapper
h0_DOSClose_AF88:
    move.l (a7)+,d0
h0_DOSClose_AF8A:
    movem.l (a7)+,d4
    beq.s h0_DOSClose_AFAC
h0_DOSClose_AF90:
    lea.l app_fileinfoblock+fib_DiskKey(a6),a0
    move.l a0,d0
    move.l d0,d2
    andi.b #3,d2
    beq.s h0_DOSClose_AFA4
h0_DOSClose_AF9E:
    andi.b #252,d0
    addq.l #4,d0
h0_DOSClose_AFA4:
    movea.l d0,a0
    move.l fib_Size(a0),d1
    bne.s h0_AFB6
h0_DOSClose_AFAC:
    move.l d4,d1
    moveq.l #_LVOClose,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOClose fallback via local wrapper
h0_AFB4:
    moveq.l #0,d4
h0_AFB6:
    rts
h0_DOSClose_AFB8:
    move.l d2,d1
    moveq.l #_LVOClose,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOClose fallback via local wrapper
h0_AFC0:
    rts
h0_AFC2:
    move.l d3,-(a7)
    move.l d1,d3
    move.l d2,d1
    move.l a0,d2
    moveq.l #_LVORead,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVORead fallback via local wrapper
h0_AFD0:
    tst.l d0
    bmi.s h0_AFD8
h0_AFD4:
    move.l d0,d1
    moveq.l #0,d0
h0_AFD8:
    movem.l (a7)+,d3
    rts
h0_AFDE:
    move.l d4,-(a7)
    bsr.w h0_AEB4
h0_AFE4:
    move.l d1,d2
    move.l d4,d3
    movem.l (a7)+,d4
    eori #4,ccr
    rts
h0_AFF2:
    move.l d3,d2
    bra.s h0_DOSClose_AFB8
h0_DOSRead_AFF6:
    exg d3,d1
    move.l a0,d2
    moveq.l #_LVORead,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVORead fallback via local wrapper
h0_B000:
    rts
h0_B002:
    move.l a0,d1
    move.l #MODE_NEWFILE,d2
    move.l d3,-(a7)
    moveq.l #-1,d3
    moveq.l #_LVOOpen,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_B014:
    move.l (a7)+,d3
    tst.l d0
    beq.s h0_B020
h0_B01A:
    move.l d0,d2
    moveq.l #0,d0
    rts
h0_B020:
    moveq.l #-1,d0
    rts
h0_DOSWrite_B024:
    tst.l d1
    beq.s h0_B040
h0_DOSWrite_B028:
    movem.l d1-d3,-(a7)
    move.l d1,d3
    move.l app_file_0186+fh_Link(a6),d1
    move.l a0,d2
    moveq.l #_LVOWrite,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOWrite fallback via local wrapper
h0_B03A:
    movem.l (a7)+,d1-d3
    cmp.l d0,d1
h0_B040:
    rts
h0_B042:
    move.l d3,-(a7)
    moveq.l #OFFSET_BEGINNING,d3
    move.l app_file_0186+fh_Link(a6),d1
    moveq.l #_LVOSeek,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOSeek fallback via local wrapper
h0_B050:
    move.l (a7)+,d3
    rts
h0_B054:
    move.l d3,-(a7)
    move.l app_file_0186+fh_Link(a6),d1
    moveq.l #0,d2
    moveq.l #OFFSET_CURRENT,d3
    moveq.l #_LVOSeek,d0
    bsr.w h0_B0D6                       ; KNOWN: DOSBase _LVOSeek fallback via local wrapper
h0_B064:
    move.l (a7)+,d3
    rts
h0_ExecAvailMem_B068:
    tst.b $021B(a6)
    bne.s h0_B09A
h0_ExecAvailMem_B06E:
    movem.l d1-d2/a0-a2,-(a7)
    move.l #MEMF_LARGEST|MEMF_PUBLIC,d1
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOAvailMem(a6)
h0_B082:
    movea.l (a7)+,a6
    movem.l (a7)+,d1-d2/a0-a2
    cmp.l #$7D00,d0
    bcs.s h0_B096
h0_B090:
    asr.l #1,d0
    cmp.l d0,d1
    bcs.s h0_B098
h0_B096:
    move.l d2,d1
h0_B098:
    rts
h0_B09A:
    cmp.l d2,d1
    ble.s h0_B098
h0_B09E:
    bra.s h0_B096
dat_B0A0:
    DC.B    $64,$6f,$73,$2e,$6c,$69,$62,$72,$61,$72,$79,$00
h0_B0AC:
    bsr.w h0_DOSOpen                    ; KNOWN: DOSBase _LVOOpen fallback via local wrapper
h0_B0B0:
    tst.l d4
    beq.s h0_B0D4
h0_B0B4:
    move.l d1,d5
    addq.l #1,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_DOSRead_B0BC:
    move.l d5,d1
    move.l d4,d3
    move.l a0,-(a7)
    bsr.w h0_DOSRead_AFF6
h0_B0C6:
    move.l d4,d3
    bsr.w h0_AFF2
h0_B0CC:
    movea.l (a7)+,a0
    clr.b $0(a0,d5.l)
    tst.l d5
h0_B0D4:
    rts
h0_B0D6:
    move.l a6,-(a7)
    tst.l app_slot_01A2(a6)
    beq.s h0_B0F0
h0_B0DE:
    movea.l app_slot_01A2(a6),a0
    movea.l $0004(a0),a0
    movea.l app_DOSBase(a6),a6
    jsr (a0)                            ; KNOWN: callback field +4 from app_slot_01A2
h0_B0EC:
    movea.l (a7)+,a6
    rts
h0_B0F0:
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)                     ; KNOWN: DOSBase indexed vector via d0
h0_B0F8:
    movea.l (a7)+,a6
    rts
    DC.L    $4a2e0df4,$662248e7,$80802078,$00041028,$01290800,$00046712,$08000001,$670c1d7c
    DC.L    $00010df4,$4cdf0101 ; VIOLATION: orphaned code island at $B0FC is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $70,$60 ; VIOLATION: orphaned code island at $B126 is not reached from known entrypoints
    DC.L    $6000d344
    DC.B    "JEg6a"
    DC.B    $ca,$f2,$3c
    DC.L    $88000000,$0000ba7c,$000a6400,$0056cafc,$03e80810,$00066702,$4445f23c,$50800001
    DC.L    $f2055092,$f2104c00,$f2000423,$6000001e,$4e757005,$3f006190,$f23c8800,$00000000
    DC.L    $301f4880,$c0fc0006,$61000020,$3003d040,$d043d040,$61000018,$f200a800,$08000006
    DC.L    $67047063,$4e757000,$4e754efb,$002a4efb,$00fcf210,$78004e75,$f2107000,$4e75f210
    DC.L    $60004e75,$f2107400,$4e75f210,$6c004e75,$f2106400,$4e75f210,$68004e75,$f2105800
    DC.L    $4e75f210,$50004e75,$f2104000,$4e75f210,$54004e75,$f2104c00,$4e75f210,$44004e75
    DC.L    $f2104800,$4e753f03,$6100fefe,$f23c8800,$00000000,$361f4883,$3003d040,$d043d040
    DC.L    $6188f200,$001a6000
    DC.B    $ff,$6c
dat_B21E:
    DC.B    $00,$00
    DC.L    $0000006e,$007600d6,$00fc00ee,$01620184,$008601d0,$01dc01ce,$01d80246,$025202b8
    DC.L    $0326001c,$00800034,$003600a2,$00e0038a,$00980352,$01e400f6,$00f2038c,$0102010c
    DC.L    $01080156,$02340148,$01ce015e,$015c015c,$016a01ca,$01d401fc,$0238025a,$023e03f0
    DC.L    $02640248,$00000250,$02780268,$026c02c0,$02d0041c,$046e02fc,$0498033e,$02c402c0
    DC.L    $02dc031e,$038a03a2,$033a04fa,$047e0390,$052203a2,$03ac03c8,$03b203ba,$03e4040c
    DC.L    $03ee03f0,$043a0414,$03fa04de,$0414042a,$04260546,$0442043e,$0524044e,$04a2057e
    DC.L    $048c04ac,$04b6056a,$04c004ee,$05d8056e,$050e0512,$056e05ca,$05ce05ee,$058005da
    DC.L    $05e20000,$060405ea,$06380586,$06020652,$06060656,$06560660,$06400650,$0668065e
    DC.L    $06500000,$066a0664,$06a20666,$067006ce,$067c065c,$066e06bc,$06d80682,$069a06ce
    DC.L    $072206ce,$00000000,$000006e4,$06d80000,$000006ee,$06d00700,$06f20706,$07060000
    DC.L    $073a0000,$00000720,$00000000,$00000000,$00000000,$00000722,$00000000,$072c0000
    DC.L    $0000073e,$074a0002,$0004072e,$0000078a,$073e0756,$07480740,$07620768,$076a0750
    DC.L    $00000784,$079c07ac,$07660770,$0764077c,$000007ba,$0000079e,$077c07d0,$07c607d4
    DC.L    $07be0000,$07e207c2,$07d207ea,$07e207ea,$07fc07e4,$00000804,$081a083a,$0828084a
    DC.L    $00000860,$082a0832,$085608b4,$084e0836,$084a0866,$08640850,$08860884,$088e08b6
    DC.L    $08c208b0,$08c608b6,$08b808c8,$08cc0920,$08e808de,$08d20000,$092208dc,$092c091e
    DC.L    $09360938,$091a098c,$000009a2,$09260936,$09580936,$0942093a,$00000000,$0948099a
    DC.L    $09a809be,$0000096e,$09c60000,$00000000,$09a60998,$09b009aa,$00000000,$0a0409c8
    DC.L    $09b209d6,$09fc09e2,$09c80a04,$0a160000,$09fe0000,$00000000,$0a0c0a18,$0a260a2c
    DC.L    $0a340a36,$0a380a3a,$0a440a6e,$0a700aa0,$00000a18,$0a280a44,$0a460a20,$0a280aa6
    DC.L    $0a8a0aa2,$0ab40ab6,$0ab80aba,$0ac40a72,$0ac00aac,$0ae20000,$0ace0b06,$00000b06
    DC.L    $0afe0b0e,$0b1a0000,$00000000,$00000000,$0b1e0000,$00000b00,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$0b0c0b48,$00000000,$0b0e0000,$0b140000
    DC.L    $00000b06,$00000b14,$00000000,$00000000,$00000000,$00000000,$0b1e0b38,$0b320b2e
    DC.L    $00000b28,$00000000,$00000000,$0b360b38,$0b460b50,$00000000,$00000000,$00000000
    DC.L    $00000000,$0b660b52,$0b680b76,$0b700b70,$0b7a0000,$00000000,$00000b8a,$0b800000
    DC.L    $00000ba6,$00000000,$00000000,$00000000,$0ba20b9e,$0b8a0000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000ba2,$0ba40bae,$00000bb6
    DC.L    $00000000,$00000ba8,$00000000,$00000000,$00000ba2,$00000000,$0bae0bb0,$00000000
    DC.L    $0bc40000,$00000000,$00000bc8,$0bd00c06,$0bec0000,$0bba0000,$0be00000,$0bd20c18
    DC.L    $0c1a0000,$00000c06,$0bf20c1e,$0c060000,$0c220c32,$0c3a0c52,$0c300c8a,$00000c94
    DC.L    $0c120000,$0c1a0c34,$0c400c38,$0c700000,$0c480c8e,$0c6c0cd8,$00000c9a,$00000000
    DC.L    $00000000,$0cac0000,$0c960c9a,$0cba0cba,$0cae0c9c,$00000000,$0cc20000,$0cda0000
    DC.L    $00000ca2,$0cba0ccc,$0d060cec,$0d180cee,$00000cd2,$0cda0000,$0d0e0d00,$00000d22
    DC.L    $00000d06,$0d220d34,$00000d22,$0d1a0d24,$00000d1e,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000d3a,$0d3a0d3c,$0d280000,$0d540000,$0d420d58,$0d560d4e,$0d600dbc
    DC.L    $00000000,$00000000,$0d540d6e,$0d860d6a,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$0d9e0da0,$0da20da6,$0da80dac
    DC.L    $0dba0dc4,$0d720000,$0da80dec,$0dea0dce,$00000000,$0dee0000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000dd2,$0ddc0e02,$0de80000,$0dfc0000
    DC.L    $00000000,$0e000e00,$00000e1a,$00000000,$00000000,$0e060000,$00000e14,$0e160e18
    DC.L    $00000000,$0e7a0000,$00000000,$00000000,$00000e36,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000e30,$0e5c0000,$00000000,$0e420000,$0e3e0000,$00000e66,$00000000
    DC.L    $0e6e0000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000e70,$00000000,$00000000,$0e9a0e86,$0ea60ec2,$00000e76
    DC.L    $00000e9e,$00000e8a,$0ed20ed4,$00000000,$0ed60000,$00000ecc,$00000edc,$0ec80efe
    DC.L    $0ed0000a,$00000ee6,$0f0a0ee0,$0eec0000,$00000000,$0f080000,$0f020000,$0eec0efa
    DC.L    $00000f10,$00000000,$00000f18,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000efe,$00000000,$00000000,$00000000,$00000f0a,$0f520f0e,$0f300f22,$0f1e0f44
    DC.L    $0f3e0f54,$0f5a0000,$00000f76,$00020000,$00000000,$00000000,$00000f5c,$0f7c0f60
    DC.L    $0f620000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000f80,$0f740000,$00000f86,$0f760000,$0f760fda,$0f8e0000,$00000f9c,$00000fa0
    DC.L    $0faa0000,$00000000,$00000fc8,$00000000,$0fa40000,$00000000,$00000000,$00000000
    DC.L    $00000000,$0fe00000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$000e0fd0,$0fd80000,$00000010,$0fd20000,$00000fd4,$00000fce
    DC.L    $0fe40fde,$00000000,$00000fd6,$0fe80000,$1034101a,$100a1002,$10540000,$105e0fe2
    DC.L    $0ffe0000,$00001044,$10680000,$10640000,$00000000,$00000000,$0000107e,$00000000
    DC.L    $106a1050,$00000000,$10721080,$10b810c2,$10c410c6,$10c810ca,$0000105c,$10760000
    DC.L    $00000000,$00000000,$00000000,$0000108a,$00000000,$00000000,$00000000,$108c0000
    DC.L    $00000000,$000010ea,$10d210ec,$10ee0000,$10be0000,$10e80000,$10da10fc,$11180000
    DC.L    $00000000,$000010f4,$000010fe,$00000000,$00000000,$111c0000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $11340000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000
dat_BA08:
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffff0340,$034206d2,$ffff0712,$0746074c,$ffffffff,$ffff0002,$ffffffff
    DC.L    $ffff0004,$00060008,$000a000c,$000effff,$ffff0010,$0012ffff,$00140016,$0018001a
    DC.L    $001cffff,$001e0020,$00220024,$ffffffff,$0026ffff,$ffffffff,$011a0120,$ffff0122
    DC.L    $ffff0004,$00060008,$000a000c,$000effff,$ffff0010,$0012ffff,$00140016,$0018001a
    DC.L    $001cffff,$001e0020,$00220024,$ffffffff,$00260028,$ffff002a,$011a0120,$00300122
    DC.L    $00320034,$00360038,$011c002c,$003a003c,$003e0040,$002e0042,$ffff0044,$00460048
    DC.L    $009a004a,$011effff,$ffff0124,$009cffff,$ffff0028,$ffff002a,$ffff0132,$0030ffff
    DC.L    $00320034,$00360038,$011c002c,$003a003c,$003e0040,$002e0042,$004c0044,$00460048
    DC.L    $009a004a,$011e004e,$00500124,$009c0052,$00540056,$0058005a,$01260132,$005c005e
    DC.L    $00600062,$01280068,$0146006a,$006c0064,$006e0148,$01500152,$004c0070,$012a0072
    DC.L    $01540066,$ffff004e,$0050ffff,$ffff0052,$00540056,$0058005a,$0126ffff,$005c005e
    DC.L    $00600062,$01280068,$0146006a,$006c0064,$006e0148,$01500152,$01560070,$012a0072
    DC.L    $01540066,$00740076,$0078007a,$007c015e,$007e016a,$00800164,$016c0082,$00840086
    DC.L    $00880166,$0168008a,$008c008e,$0090016e,$0092ffff,$ffff0094,$0156ffff,$0096ffff
    DC.L    $0098ffff,$00740076,$0078007a,$007c015e,$007e016a,$00800164,$016c0082,$00840086
    DC.L    $00880166,$0168008a,$008c008e,$0090016e,$009200b0,$01600094,$00b2009e,$009600a8
    DC.L    $009800a0,$00b600aa,$00a20170,$00b40140,$00a40172,$016200a6,$00b800ac,$00baffff
    DC.L    $014200bc,$017400ae,$ffffffff,$0144ffff,$ffff00b0,$01600176,$00b2009e,$ffff00a8
    DC.L    $ffff00a0,$00b600aa,$00a20170,$00b40140,$00a40172,$016200a6,$00b800ac,$00ba0158
    DC.L    $014200bc,$017400ae,$00be00c0,$014400c2,$00c400c6,$00d40176,$015a015c,$00d600c8
    DC.L    $00ca0178,$017a017c,$019600cc,$00ce00d0,$00d800d2,$0198019a,$00da00dc,$ffff0158
    DC.L    $019cffff,$ffffffff,$00be00c0,$019e00c2,$00c400c6,$00d401a0,$015a015c,$00d600c8
    DC.L    $00ca0178,$017a017c,$019600cc,$00ce00d0,$00d800d2,$0198019a,$00da00dc,$00de00e0
    DC.L    $019c00e2,$00e400e6,$00e801a2,$019e01dc,$00ea00ec,$00ee01a0,$00f0ffff,$01de01a4
    DC.L    $00f200f4,$00f600f8,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$01a601e0,$00de00e0
    DC.L    $ffff00e2,$00e400e6,$00e801a2,$ffff01dc,$00ea00ec,$00ee01c6,$00f001c8,$01de01a4
    DC.L    $00f200f4,$00f600f8,$00fa00fc,$00fe0100,$01020104,$01060108,$01a601e0,$01e2010a
    DC.L    $010c010e,$01ee0110,$01e40112,$01140116,$ffff0118,$ffff01c6,$013401c8,$01360138
    DC.L    $01d8ffff,$013a01da,$00fa00fc,$00fe0100,$01020104,$01060108,$013c013e,$01e2010a
    DC.L    $010c010e,$01ee0110,$01e40112,$01140116,$012a0118,$01e6014a,$0134012c,$01360138
    DC.L    $01d8012e,$013a01da,$01e80130,$02180226,$0130014c,$014effff,$013c013e,$ffffffff
    DC.L    $ffff01ea,$022801ec,$ffffffff,$ffff022a,$012a022c,$01e6014a,$ffff012c,$ffff022e
    DC.L    $ffff012e,$ffff0230,$01e80130,$02180226,$0130014c,$014e017e,$02360180,$01820184
    DC.L    $018601ea,$022801ec,$0188018a,$018c022a,$018e022c,$01900238,$0192023e,$0194022e
    DC.L    $01a801aa,$01ac0230,$02320240,$024601ae,$02480234,$024a017e,$02360180,$01820184
    DC.L    $018601b0,$01b2ffff,$0188018a,$018c0252,$018e023a,$01900238,$0192023e,$0194023c
    DC.L    $01a801aa,$01ac0254,$02320240,$024601ae,$02480234,$024a025a,$01b401b6,$01b8ffff
    DC.L    $020e01b0,$01b201ba,$021001bc,$01be0252,$0270023a,$01c001c2,$01c401ca,$01cc023c
    DC.L    $01ce0212,$02140254,$025c01d0,$02160272,$025e01d2,$01d4025a,$01b401b6,$01b801d6
    DC.L    $020effff,$ffff01ba,$021001bc,$01be0274,$0270ffff,$01c001c2,$01c401ca,$01cc027c
    DC.L    $01ce0212,$02140242,$025c01d0,$02160272,$025e01d2,$01d4ffff,$027effff,$01f001d6
    DC.L    $01f201f4,$01f601f8,$01fa0244,$01fc0274,$029401fe,$02000202,$02040296,$0206027c
    DC.L    $0208020a,$020c0242,$021a021c,$021effff,$02200256,$ffff0258,$027e0222,$01f00224
    DC.L    $01f201f4,$01f601f8,$01fa0244,$01fcffff,$029401fe,$02000202,$02040296,$0206024c
    DC.L    $0208020a,$020c024e,$021a021c,$021e0250,$02200256,$02760258,$02900222,$02980224
    DC.L    $02600262,$026402b2,$0278027a,$0266029a,$02680292,$029c026a,$02caffff,$ffff024c
    DC.L    $ffffffff,$026c024e,$ffffffff,$026e0250,$ffffffff,$0276ffff,$0290ffff,$0298ffff
    DC.L    $02600262,$026402b2,$0278027a,$0266029a,$02680292,$029c026a,$02ca0280,$02820284
    DC.L    $02b4029e,$026c0286,$02b80288,$026e02a0,$028a02a4,$02a602a8,$02aa02a2,$02c2028c
    DC.L    $02b6ffff,$02ba028e,$02ac02bc,$02cc02be,$02b402ae,$02b0ffff,$ffff0280,$02820284
    DC.L    $02b4029e,$02d20286,$02b80288,$02c002a0,$028a02a4,$02a602a8,$02aa02a2,$02c2028c
    DC.L    $02b602c4,$02ba028e,$02ac02bc,$02cc02be,$02b402ae,$02b002b6,$02ce02d4,$02d602c6
    DC.L    $02c802da,$02d202dc,$02de02d0,$02c002e0,$02e402e6,$02ea02ee,$02f602f8,$02d80304
    DC.L    $02e802c4,$03060308,$ffffffff,$031202e2,$00ae02ec,$ffff02b6,$02ce02d4,$02d602c6
    DC.L    $02c802da,$031402dc,$02de02d0,$02f002e0,$02e402e6,$02ea02ee,$02f602f8,$02d80304
    DC.L    $02e8030a,$03060308,$02f202f4,$031202e2,$00ae02ec,$00fe0316,$02fa0104,$01060108
    DC.L    $0320030c,$031402fc,$02fe010e,$02f00300,$030e0322,$ffff0302,$03100118,$03240326
    DC.L    $032a030a,$ffff0328,$02f202f4,$032c032e,$0330ffff,$00fe0316,$02fa0104,$01060108
    DC.L    $0320030c,$031802fc,$02fe010e,$03320300,$030e0322,$031a0302,$03100118,$03240326
    DC.L    $032a0334,$031c0328,$03360338,$032c032e,$0330031e,$033a033c,$033e0344,$ffff034e
    DC.L    $03500352,$03180354,$03560358,$03320346,$035a035e,$031affff,$036c036e,$03700372
    DC.L    $ffff0334,$031c037c,$03360338,$03480360,$035c031e,$033a033c,$033e0344,$034a034e
    DC.L    $03500352,$034c0354,$03560358,$03620364,$035a035e,$ffff0366,$036c036e,$03700372
    DC.L    $0374035a,$0378037c,$037a035c,$03480360,$035c0368,$036a037e,$0386038c,$034a0388
    DC.L    $03760380,$034c038e,$03920382,$03620364,$03940396,$03840366,$038a0398,$039a039c
    DC.L    $0374035a,$0378039e,$037a035c,$ffff03a0,$03900368,$036a037e,$0386038c,$03a20388
    DC.L    $03760380,$03a6038e,$03920382,$03a4ffff,$03940396,$038403b0,$038a0398,$039a039c
    DC.L    $03b203a8,$03aa039e,$03ac03c6,$03b403a0,$039003ae,$03b603b8,$03c803ca,$03a203cc
    DC.L    $03e203e4,$03a603ba,$03e603be,$03a403c0,$03ea03bc,$03e803b0,$03c203f0,$03c4ffff
    DC.L    $03b203a8,$03aa03ec,$03ac03c6,$03b403ee,$ffff03ae,$03b603b8,$03c803ca,$ffff03cc
    DC.L    $03e203e4,$03f203ba,$03e603be,$03f403c0,$03ea03bc,$03e803f6,$03c203f0,$03c403ce
    DC.L    $03d003d2,$03f803ec,$03fe03fa,$03d403ee,$03d603d8,$04000402,$03da03dc,$03de03e0
    DC.L    $04040406,$03f20408,$ffff0412,$03f403fc,$0414040a,$041603f6,$041effff,$ffff03ce
    DC.L    $03d003d2,$03f8ffff,$03fe03fa,$03d4ffff,$03d603d8,$04000402,$03da03dc,$03de03e0
    DC.L    $04040406,$040c0408,$040e0412,$041803fc,$0414040a,$04160420,$041e041a,$04240434
    DC.L    $0428044c,$042a042e,$0426041c,$0410042c,$0430044e,$0422ffff,$ffff0450,$04320452
    DC.L    $04540456,$040cffff,$040e0458,$0418ffff,$ffffffff,$ffff0420,$0468041a,$04240434
    DC.L    $0428044c,$042a042e,$0426041c,$0410042c,$0430044e,$04220436,$04380450,$04320452
    DC.L    $04540456,$045a0442,$043a0458,$0444043c,$0446045e,$043e0440,$04680448,$0470044a
    DC.L    $0472045c,$04620464,$0466046a,$0474046c,$04600476,$ffff0436,$0438047c,$047e046e
    DC.L    $0480ffff,$045a0442,$043a0486,$0444043c,$0446045e,$043e0440,$04880448,$0470044a
    DC.L    $0472045c,$04620464,$0466046a,$0474046c,$04600476,$0478048a,$048c047c,$047e046e
    DC.L    $04800482,$048e0484,$047a0486,$04900492,$04940496,$ffffffff,$0488049a,$049e04a2
    DC.L    $04a604c6,$04c804ca,$04cc04aa,$04ce04d0,$ffff0498,$0478048a,$048c049c,$04a004a4
    DC.L    $04a80482,$048e0484,$047a04ac,$04900492,$04940496,$04ae04b2,$ffff049a,$049e04a2
    DC.L    $04a604c6,$04c804ca,$04cc04aa,$04ce04d0,$04d80498,$04b004b4,$04f4049c,$04a004a4
    DC.L    $04a804b6,$04b804ba,$04dc04ac,$04d204bc,$04da04be,$04ae04b2,$04c004e0,$04e404e8
    DC.L    $04ec04f6,$04f804c2,$04de04f0,$04d404c4,$04d804d6,$04b004b4,$04f404e2,$04e604ea
    DC.L    $04ee04b6,$04b804ba,$04dc04f2,$04d204bc,$04da04be,$04fa04fc,$04c004e0,$04e404e8
    DC.L    $04ec04f6,$04f804c2,$04de04f0,$04d404c4,$04fe04d6,$05000502,$050604e2,$04e604ea
    DC.L    $04ee0504,$0508050a,$050c04f2,$050e051a,$ffff0520,$04fa04fc,$ffff051c,$0522051e
    DC.L    $02e602f0,$02f60524,$05260510,$0528052a,$04fe052c,$05000502,$05060512,$052e02f2
    DC.L    $02f40504,$0508050a,$050c0514,$050e051a,$05160520,$05300532,$0518051c,$0522051e
    DC.L    $02e602f0,$02f60524,$05260510,$0528052a,$0534052c,$05360538,$053a0512,$052e02f2
    DC.L    $02f4053c,$053e0540,$05420514,$0548054a,$0516054c,$05300532,$0518054e,$05500544
    DC.L    $05520554,$05560546,$0558055a,$055c055e,$05340560,$05360538,$053a0566,$0574ffff
    DC.L    $0562053c,$053e0540,$05420576,$0548054a,$0564054c,$05780570,$0568054e,$05500544
    DC.L    $05520554,$05560546,$0558055a,$055c055e,$056a0560,$05720582,$05840566,$0574056c
    DC.L    $0562057a,$057e0586,$05880576,$058a056e,$056403d0,$05780570,$0568058c,$059005b0
    DC.L    $057c0580,$059405b2,$0596058e,$05b405b6,$056a0598,$05720582,$05840592,$05b8056c
    DC.L    $059a057a,$057e0586,$0588059c,$058a056e,$ffff03d0,$05ba059e,$05bc058c,$059005b0
    DC.L    $057c0580,$059405b2,$0596058e,$05b405b6,$05c20598,$05a005a2,$05be0592,$05b805a8
    DC.L    $059a05aa,$05ca05a4,$05c0059c,$05ac05cc,$05ae05a6,$05ba059e,$05bc05c4,$05c605ce
    DC.L    $05d005d2,$05d405d6,$05d805da,$05dc05e4,$05c205e6,$05a005a2,$05be05e8,$05de05a8
    DC.L    $05e005aa,$05ca05a4,$05c005e2,$05ac05cc,$05ae05a6,$05c805f0,$05fa05fe,$060005ce
    DC.L    $05d005d2,$05d405d6,$05d805da,$05dc05e4,$05ea05e6,$05f205fc,$060205e8,$05de05ec
    DC.L    $05e005f4,$06040606,$060805e2,$060a05ee,$05f60612,$05c805f0,$05fa05fe,$0600060e
    DC.L    $05f80614,$06160618,$061a060c,$061c061e,$05ea0620,$05f205fc,$06020622,$061005ec
    DC.L    $062405f4,$06040606,$06080626,$060a05ee,$05f60612,$0628062a,$062c063c,$063e060e
    DC.L    $05f80614,$06160618,$061a060c,$061c061e,$06400620,$0642ffff,$06640622,$0610062e
    DC.L    $0624ffff,$06440648,$064c0626,$06500654,$06660658,$0628062a,$062c063c,$063e0630
    DC.L    $065c0632,$0646064a,$064e0660,$06520656,$0640065a,$06420634,$0664ffff,$06360638
    DC.L    $065e063a,$06440648,$064c0662,$06500654,$06660658,$066c066e,$06700672,$06740630
    DC.L    $065c0632,$0646064a,$064e0660,$06520656,$0668065a,$06760634,$0678066a,$06360638
    DC.L    $065e063a,$067a067c,$067e0662,$06800682,$06840686,$066c066e,$06700672,$06740688
    DC.L    $ffff068a,$ffffffff,$ffffffff,$0692069a,$0668ffff,$0676ffff,$0678066a,$068e0694
    DC.L    $0690ffff,$067a067c,$067e069c,$06800682,$06840686,$0696069e,$06a006a2,$06980688
    DC.L    $00fe068a,$02fa0104,$01060108,$0692069a,$06aa010a,$02fe010e,$06b80300,$068e0694
    DC.L    $06900302,$06a4068c,$06ba069c,$06bc06ac,$06ae06a6,$0696069e,$06a006a2,$069806b0
    DC.L    $00fe06a8,$02fa0104,$01060108,$06b406b2,$06aa010a,$02fe010e,$06b80300,$06be06c2
    DC.L    $06c60302,$06a4068c,$06ba06b6,$06bc06ac,$06ae06a6,$06c806ca,$06cc06c0,$06c406b0
    DC.L    $06ce06a8,$06d006d4,$06da06dc,$06b406b2,$06d606de,$06e006e2,$06e406e6,$06be06c2
    DC.L    $06c606e8,$06d806ea,$06ec06b6,$0700ffff,$ffff0702,$06c806ca,$06cc06c0,$06c40704
    DC.L    $06ce0706,$06d006d4,$06da06dc,$0708070a,$06d606de,$06e006e2,$06e406e6,$06ee06f0
    DC.L    $06f206e8,$06d806ea,$06ec06f4,$070006f6,$06f80702,$070c070e,$06fa06fc,$06fe0704
    DC.L    $07100706,$07140716,$0718071a,$0708070a,$071c0722,$0724073a,$071e0726,$06ee06f0
    DC.L    $06f20720,$0728073c,$ffff06f4,$ffff06f6,$06f8ffff,$070c070e,$06fa06fc,$06fe073e
    DC.L    $07100740,$07140716,$0718071a,$0742030a,$071c0722,$0724073a,$071e0726,$072a072c
    DC.L    $072e0720,$0728073c,$07300744,$0732030c,$07480734,$074a074e,$07500752,$0754073e
    DC.L    $07360740,$07560758,$0738075a,$0742030a,$076c0782,$07660784,$0768076e,$072a072c
    DC.L    $072e076a,$07620770,$07300744,$0732030c,$07480734,$074a074e,$07500752,$0754075c
    DC.L    $07360764,$07560758,$0738075a,$075e0786,$076c0782,$07660784,$0768076e,$07600772
    DC.L    $0774076a,$07620770,$077a0788,$077c078a,$07760794,$0796077e,$07980780,$0778075c
    DC.L    $078c0764,$07b8079c,$ffffffff,$075e0786,$ffff07ba,$07bc07be,$079a078e,$07600772
    DC.L    $07740790,$0792079e,$077a0788,$077c078a,$07760794,$0796077e,$07980780,$077807a0
    DC.L    $078cffff,$07b8079c,$07a407a8,$07ac07b0,$07b407ba,$07bc07be,$079a078e,$07c607a2
    DC.L    $07d40790,$0792079e,$07a607aa,$07ae07b2,$07b607d6,$07c007ca,$07d007c8,$07d807a0
    DC.L    $ffff07c2,$07cc07da,$07a407a8,$07ac07b0,$07b407c4,$07ce07d2,$07e207e4,$07c607a2
    DC.L    $07d407de,$07dc07e6,$07a607aa,$07ae07b2,$07b607d6,$07c007ca,$07d007c8,$07d807e8
    DC.L    $07e007c2,$07cc07da,$ffffffff,$ffffffff,$ffff07c4,$07ce07d2,$07e207e4,$ffffffff
    DC.L    $ffff07de,$07dc07e6,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffff07e8
    DC.L    $07e0ffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
dat_CD3C:
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $00000000,$00000168,$016a05c4,$0000062e,$06ca06d4,$ffffffff,$ffff0000,$ffffffff
    DC.L    $ffff0000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$0000ffff,$0000ffff,$00240028,$ffff002a
    DC.L    $ffff0000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000004,$00000004,$00240028,$0006002a
    DC.L    $00060006,$00060006,$00260004,$00060006,$00060006,$00040006,$ffff0006,$00060006
    DC.L    $00120006,$0026ffff,$ffff002c,$0012ffff,$ffff0004,$ffff0004,$ffff0032,$0006ffff
    DC.L    $00060006,$00060006,$00260004,$00060006,$00060006,$00040006,$00080006,$00060006
    DC.L    $00120006,$00260008,$0008002c,$00120008,$00080008,$00080008,$002e0032,$0008000a
    DC.L    $000a000a,$002e000c,$0038000c,$000c000a,$000c003a,$003e0040,$0008000c,$0038000c
    DC.L    $0042000a,$ffff0008,$0008ffff,$ffff0008,$00080008,$00080008,$002effff,$0008000a
    DC.L    $000a000a,$002e000c,$0038000c,$000c000a,$000c003a,$003e0040,$0044000c,$0038000c
    DC.L    $0042000a,$000e000e,$000e000e,$000e0048,$000e004e,$000e004c,$0050000e,$000e000e
    DC.L    $000e004c,$004c000e,$000e000e,$00100052,$0010ffff,$ffff0010,$0044ffff,$0010ffff
    DC.L    $0010ffff,$000e000e,$000e000e,$000e0048,$000e004e,$000e004c,$0050000e,$000e000e
    DC.L    $000e004c,$004c000e,$000e000e,$00100052,$00100018,$004a0010,$00180014,$00100016
    DC.L    $00100014,$001a0016,$00140054,$00180036,$00140056,$004a0014,$001a0016,$001affff
    DC.L    $0036001a,$00580016,$ffffffff,$0036ffff,$ffff0018,$004a0058,$00180014,$ffff0016
    DC.L    $ffff0014,$001a0016,$00140054,$00180036,$00140056,$004a0014,$001a0016,$001a0046
    DC.L    $0036001a,$00580016,$001c001c,$0036001c,$001c001c,$001e0058,$00460046,$001e001c
    DC.L    $001c005a,$005c005e,$0062001c,$001c001c,$001e001c,$00640068,$001e001e,$ffff0046
    DC.L    $006affff,$ffffffff,$001c001c,$006c001c,$001c001c,$001e006e,$00460046,$001e001c
    DC.L    $001c005a,$005c005e,$0062001c,$001c001c,$001e001c,$00640068,$001e001e,$00200020
    DC.L    $006a0020,$00200020,$00200070,$006c007e,$00200020,$0020006e,$0020ffff,$00800072
    DC.L    $00200020,$00200020,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$00720082,$00200020
    DC.L    $ffff0020,$00200020,$00200070,$ffff007e,$00200020,$00200078,$00200078,$00800072
    DC.L    $00200020,$00200020,$00220022,$00220022,$00220022,$00220022,$00720082,$00840022
    DC.L    $00220022,$008a0022,$00840022,$00220022,$ffff0022,$ffff0078,$00340078,$00340034
    DC.L    $007cffff,$0034007c,$00220022,$00220022,$00220022,$00220022,$00340034,$00840022
    DC.L    $00220022,$008a0022,$00840022,$00220022,$00300022,$0086003c,$00340030,$00340034
    DC.L    $007c0030,$0034007c,$0086003c,$00900094,$0030003c,$003cffff,$00340034,$ffffffff
    DC.L    $ffff0088,$00960088,$ffffffff,$ffff0098,$0030009a,$0086003c,$ffff0030,$ffff009c
    DC.L    $ffff0030,$ffff009e,$0086003c,$00900094,$0030003c,$003c0060,$00a20060,$00600060
    DC.L    $00600088,$00960088,$00600060,$00600098,$0060009a,$006000a4,$006000a8,$0060009c
    DC.L    $00740074,$0074009e,$00a000aa,$00ae0074,$00b000a0,$00b20060,$00a20060,$00600060
    DC.L    $00600074,$0074ffff,$00600060,$006000b6,$006000a6,$006000a4,$006000a8,$006000a6
    DC.L    $00740074,$007400b8,$00a000aa,$00ae0074,$00b000a0,$00b200bc,$00760076,$0076ffff
    DC.L    $008e0074,$00740076,$008e0076,$007600b6,$00c200a6,$00760076,$0076007a,$007a00a6
    DC.L    $007a008e,$008e00b8,$00be007a,$008e00c4,$00be007a,$007a00bc,$00760076,$0076007a
    DC.L    $008effff,$ffff0076,$008e0076,$007600c6,$00c2ffff,$00760076,$0076007a,$007a00ca
    DC.L    $007a008e,$008e00ac,$00be007a,$008e00c4,$00be007a,$007affff,$00ccffff,$008c007a
    DC.L    $008c008c,$008c008c,$008c00ac,$008c00c6,$00d2008c,$008c008c,$008c00d4,$008c00ca
    DC.L    $008c008c,$008c00ac,$00920092,$0092ffff,$009200ba,$ffff00ba,$00cc0092,$008c0092
    DC.L    $008c008c,$008c008c,$008c00ac,$008cffff,$00d2008c,$008c008c,$008c00d4,$008c00b4
    DC.L    $008c008c,$008c00b4,$00920092,$009200b4,$009200ba,$00c800ba,$00d00092,$00d60092
    DC.L    $00c000c0,$00c000de,$00c800c8,$00c000d6,$00c000d0,$00d600c0,$00ecffff,$ffff00b4
    DC.L    $ffffffff,$00c000b4,$ffffffff,$00c000b4,$ffffffff,$00c8ffff,$00d0ffff,$00d6ffff
    DC.L    $00c000c0,$00c000de,$00c800c8,$00c000d6,$00c000d0,$00d600c0,$00ec00ce,$00ce00ce
    DC.L    $00e000d8,$00c000ce,$00e200ce,$00c000d8,$00ce00da,$00da00dc,$00dc00d8,$00e800ce
    DC.L    $00e0ffff,$00e200ce,$00dc00e2,$00ee00e6,$00e800dc,$00dcffff,$ffff00ce,$00ce00ce
    DC.L    $00e000d8,$00f200ce,$00e200ce,$00e600d8,$00ce00da,$00da00dc,$00dc00d8,$00e800ce
    DC.L    $00e000ea,$00e200ce,$00dc00e2,$00ee00e6,$00e800dc,$00dc00ea,$00f000f4,$00f600ea
    DC.L    $00ea00f8,$00f200fa,$00fc00f0,$00e600fe,$01000102,$01060108,$010c010e,$00f60112
    DC.L    $010200ea,$01140116,$ffffffff,$011c00fe,$010c0106,$ffff00ea,$00f000f4,$00f600ea
    DC.L    $00ea00f8,$011e00fa,$00fc00f0,$010a00fe,$01000102,$01060108,$010c010e,$00f60112
    DC.L    $01020118,$01140116,$010a010a,$011c00fe,$010c0106,$01100120,$01100110,$01100110
    DC.L    $01240118,$011e0110,$01100110,$010a0110,$011a012c,$ffff0110,$011a0110,$012e0134
    DC.L    $01360118,$ffff0134,$010a010a,$0138013a,$013cffff,$01100120,$01100110,$01100110
    DC.L    $01240118,$01220110,$01100110,$013e0110,$011a012c,$01220110,$011a0110,$012e0134
    DC.L    $01360142,$01220134,$01480158,$0138013a,$013c0122,$015e0164,$0166016c,$ffff0172
    DC.L    $01740176,$01220178,$017a017c,$013e0170,$017e0180,$0122ffff,$018a018c,$018e0190
    DC.L    $ffff0142,$0122019a,$01480158,$01700184,$017e0122,$015e0164,$0166016c,$01700172
    DC.L    $01740176,$01700178,$017a017c,$01840186,$017e0180,$ffff0188,$018a018c,$018e0190
    DC.L    $01940186,$0198019a,$01980188,$01700184,$017e0188,$0188019c,$019e01a2,$017001a0
    DC.L    $0194019c,$017001a6,$01a8019c,$01840186,$01aa01ac,$019c0188,$01a001ae,$01b001b2
    DC.L    $01940186,$019801b4,$01980188,$ffff01b8,$01a60188,$0188019c,$019e01a2,$01b801a0
    DC.L    $0194019c,$01ba01a6,$01a8019c,$01b8ffff,$01aa01ac,$019c01be,$01a001ae,$01b001b2
    DC.L    $01be01ba,$01bc01b4,$01bc01c6,$01be01b8,$01a601bc,$01c001c0,$01c801ca,$01b801ca
    DC.L    $01ce01d0,$01ba01c0,$01d201c4,$01b801c4,$01d401c0,$01d201be,$01c401d8,$01c4ffff
    DC.L    $01be01ba,$01bc01d6,$01bc01c6,$01be01d6,$ffff01bc,$01c001c0,$01c801ca,$ffff01ca
    DC.L    $01ce01d0,$01da01c0,$01d201c4,$01dc01c4,$01d401c0,$01d201de,$01c401d8,$01c401cc
    DC.L    $01cc01cc,$01e001d6,$01e401e2,$01cc01d6,$01cc01cc,$01e601e8,$01cc01cc,$01cc01cc
    DC.L    $01ea01ec,$01da01ee,$ffff01f2,$01dc01e2,$01f401ee,$01f601de,$01fcffff,$ffff01cc
    DC.L    $01cc01cc,$01e0ffff,$01e401e2,$01ccffff,$01cc01cc,$01e601e8,$01cc01cc,$01cc01cc
    DC.L    $01ea01ec,$01f001ee,$01f001f2,$01fa01e2,$01f401ee,$01f601fe,$01fc01fa,$02000206
    DC.L    $0202020e,$02020204,$020001fa,$01f00202,$02040210,$01feffff,$ffff0212,$02040214
    DC.L    $02160218,$01f0ffff,$01f0021e,$01faffff,$ffffffff,$ffff01fe,$022801fa,$02000206
    DC.L    $0202020e,$02020204,$020001fa,$01f00202,$02040210,$01fe0208,$02080212,$02040214
    DC.L    $02160218,$0220020c,$0208021e,$020c0208,$020c0222,$02080208,$0228020c,$0232020c
    DC.L    $02340220,$02240224,$0224022a,$0236022a,$02220238,$ffff0208,$02080240,$0242022a
    DC.L    $0244ffff,$0220020c,$02080248,$020c0208,$020c0222,$02080208,$024a020c,$0232020c
    DC.L    $02340220,$02240224,$0224022a,$0236022a,$02220238,$023e024c,$024e0240,$0242022a
    DC.L    $02440246,$02520246,$023e0248,$025a025c,$025e0260,$ffffffff,$024a0262,$02640266
    DC.L    $02680274,$02760278,$027a026a,$027c027e,$ffff0260,$023e024c,$024e0262,$02640266
    DC.L    $02680246,$02520246,$023e026a,$025a025c,$025e0260,$026c026e,$ffff0262,$02640266
    DC.L    $02680274,$02760278,$027a026a,$027c027e,$02820260,$026c026e,$02900262,$02640266
    DC.L    $02680270,$02700270,$0284026a,$02800270,$02820270,$026c026e,$02700286,$0288028a
    DC.L    $028c0292,$02940270,$0284028e,$02800270,$02820280,$026c026e,$02900286,$0288028a
    DC.L    $028c0270,$02700270,$0284028e,$02800270,$02820270,$0296029a,$02700286,$0288028a
    DC.L    $028c0292,$02940270,$0284028e,$02800270,$029c0280,$02a002a2,$02a40286,$0288028a
    DC.L    $028c02a2,$02a602b2,$02b8028e,$02d202da,$ffff02e4,$0296029a,$ffff02de,$02e802de
    DC.L    $02fa02fc,$02fe0300,$030402d4,$030e0310,$029c0312,$02a002a2,$02a402d4,$031402fc
    DC.L    $02fc02a2,$02a602b2,$02b802d4,$02d202da,$02d402e4,$03260328,$02d402de,$02e802de
    DC.L    $02fa02fc,$02fe0300,$030402d4,$030e0310,$032a0312,$032c032e,$033002d4,$031402fc
    DC.L    $02fc0332,$033c033e,$034402d4,$03520354,$02d40356,$03260328,$02d40378,$037a0344
    DC.L    $037c0380,$03880344,$0394039a,$039c03a2,$032a03ac,$032c032e,$033003ae,$03b6ffff
    DC.L    $03ac0332,$033c033e,$034403ba,$03520354,$03ac0356,$03be03b2,$03ae0378,$037a0344
    DC.L    $037c0380,$03880344,$0394039a,$039c03a2,$03b003ac,$03b203c8,$03ca03ae,$03b603b0
    DC.L    $03ac03c0,$03c203cc,$03ce03ba,$03d203b0,$03ac03da,$03be03b2,$03ae03d2,$03d403e2
    DC.L    $03c003c2,$03d603e6,$03d603d2,$03e803ea,$03b003d6,$03b203c8,$03ca03d4,$03ec03b0
    DC.L    $03d803c0,$03c203cc,$03ce03d8,$03d203b0,$ffff03da,$03ee03d8,$03f203d2,$03d403e2
    DC.L    $03c003c2,$03d603e6,$03d603d2,$03e803ea,$03f603d6,$03dc03dc,$03f403d4,$03ec03e0
    DC.L    $03d803e0,$03fc03dc,$03f403d8,$03e00406,$03e003dc,$03ee03d8,$03f203f8,$03f8040a
    DC.L    $040c040e,$04100412,$0414041a,$041a0424,$03f60426,$03dc03dc,$03f40428,$041a03e0
    DC.L    $041e03e0,$03fc03dc,$03f4041e,$03e00406,$03e003dc,$03f8042c,$04300434,$0436040a
    DC.L    $040c040e,$04100412,$0414041a,$041a0424,$042a0426,$042c0430,$043a0428,$041a042a
    DC.L    $041e042e,$043c0440,$0444041e,$0446042a,$042e044c,$03f8042c,$04300434,$04360448
    DC.L    $042e044e,$04500454,$04680446,$046a046c,$042a046e,$042c0430,$043a0472,$0448042a
    DC.L    $0476042e,$043c0440,$04440478,$0446042a,$042e044c,$047a047c,$047e048a,$048c0448
    DC.L    $042e044e,$04500454,$04680446,$046a046c,$048e046e,$0490ffff,$04c60472,$04480480
    DC.L    $0476ffff,$04b604b8,$04ba0478,$04bc04be,$04ca04c0,$047a047c,$047e048a,$048c0480
    DC.L    $04c20480,$04b604b8,$04ba04c4,$04bc04be,$048e04c0,$04900480,$04c6ffff,$04800480
    DC.L    $04c20480,$04b604b8,$04ba04c4,$04bc04be,$04ca04c0,$04ce04d0,$04d604f4,$04f60480
    DC.L    $04c20480,$04b604b8,$04ba04c4,$04bc04be,$04cc04c0,$04f80480,$04fa04cc,$04800480
    DC.L    $04c20480,$04fe0506,$050804c4,$050c0516,$051c051e,$04ce04d0,$04d604f4,$04f60520
    DC.L    $ffff0520,$ffffffff,$ffffffff,$05480552,$04ccffff,$04f8ffff,$04fa04cc,$0534054a
    DC.L    $0534ffff,$04fe0506,$05080556,$050c0516,$051c051e,$054a055c,$0562058c,$054a0520
    DC.L    $05260520,$05260526,$05260526,$05480552,$05980526,$05260526,$05a00526,$0534054a
    DC.L    $05340526,$05960526,$05a40556,$05a80598,$059a0596,$054a055c,$0562058c,$054a059a
    DC.L    $05260596,$05260526,$05260526,$059c059a,$05980526,$05260526,$05a00526,$05aa05ac
    DC.L    $05b20526,$05960526,$05a4059c,$05a80598,$059a0596,$05b805bc,$05be05aa,$05ac059a
    DC.L    $05c00596,$05c205c8,$05cc05ce,$059c059a,$05ca05d6,$05da05de,$05e005e4,$05aa05ac
    DC.L    $05b205ec,$05ca0604,$0614059c,$0618ffff,$ffff061a,$05b805bc,$05be05aa,$05ac061c
    DC.L    $05c0061e,$05c205c8,$05cc05ce,$06200622,$05ca05d6,$05da05de,$05e005e4,$06160616
    DC.L    $061605ec,$05ca0604,$06140616,$06180616,$0616061a,$06240626,$06160616,$0616061c
    DC.L    $062c061e,$063c063e,$06400642,$06200622,$0664066c,$066e0676,$06660672,$06160616
    DC.L    $06160666,$0672067c,$ffff0616,$ffff0616,$0616ffff,$06240626,$06160616,$06160680
    DC.L    $062c0682,$063c063e,$06400642,$0692068c,$0664066c,$066e0676,$06660672,$06740674
    DC.L    $06740666,$0672067c,$067406a6,$0674068c,$06cc0674,$06ce06d6,$06dc06e0,$06e20680
    DC.L    $06740682,$06e406ec,$067406ee,$0692068c,$06f80700,$06f60702,$06f606f8,$06740674
    DC.L    $067406f6,$06f406f8,$067406a6,$0674068c,$06cc0674,$06ce06d6,$06dc06e0,$06e206f2
    DC.L    $067406f4,$06e406ec,$067406ee,$06f20708,$06f80700,$06f60702,$06f606f8,$06f206fa
    DC.L    $06fa06f6,$06f406f8,$06fe070a,$06fe070e,$06fa0722,$072406fe,$072a06fe,$06fa06f2
    DC.L    $071c06f4,$073c072c,$ffffffff,$06f20708,$ffff073e,$0750075e,$072a071c,$06f206fa
    DC.L    $06fa071c,$071c072c,$06fe070a,$06fe070e,$06fa0722,$072406fe,$072a06fe,$06fa072e
    DC.L    $071cffff,$073c072c,$07300732,$07340736,$0738073e,$0750075e,$072a071c,$076a072e
    DC.L    $0772071c,$071c072c,$07300732,$07340736,$07380776,$0768076c,$076e076a,$077a072e
    DC.L    $ffff0768,$076c077c,$07300732,$07340736,$07380768,$076c076e,$0788078c,$076a072e
    DC.L    $0772077e,$077c0796,$07300732,$07340736,$07380776,$0768076c,$076e076a,$077a07c2
    DC.L    $077e0768,$076c077c,$ffffffff,$ffffffff,$ffff0768,$076c076e,$0788078c,$ffffffff
    DC.L    $ffff077e,$077c0796,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffff07c2
    DC.L    $077effff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
dat_E070:
    DC.L    $00000000,$00000000,$0dfe0000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$0ce60002,$00000000,$00000000,$0dc80000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$4e1a0000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00008000,$130e8000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$2bce0000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$51c02d42,$80000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$000050c0,$2d428000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$51f83014,$80000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $000050f8,$30148000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$0000d000,$015e8000,$c000130e,$8000e100,$2e988000,$e0002e98,$80006400
    DC.L    $02f48000,$00000000,$00000000,$00000000,$650002f4,$80006700,$02f48000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $6c0002f4,$80000000,$00000000,$6e0002f4,$80006200,$02f48000,$00000000,$00006f00
    DC.L    $02f48000,$630002f4,$80006d00,$02f48000,$6b0002f4,$80006600,$02f48000,$6a0002f4
    DC.L    $80006000,$02f48000,$00000000,$00006100,$02f48000,$00002d5a,$00000000,$00000000
    DC.L    $680002f4,$80006900,$02f48000,$00000000,$00000000,$00000000,$08c006ec,$80004180
    DC.L    $08da8000,$00000000,$00004200,$30728000,$b0000a5c,$80000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$000051c8,$0bcc8000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$000050c8,$0bcc8000,$00000000
    DC.L    $00000000,$0c180000,$00000000,$00000000,$00000000,$00000de6,$4000b000,$130e8000
    DC.L    $00000dfe,$00000000,$00000000,$c1000efa,$80004880,$0f508000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $0000f080,$3c488001,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$0000f08f,$3c488001,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00004122,$80010000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$0000000f
    DC.L    $41228001,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$4d400000,$00004d76,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$0ff20000,$00000000,$00000000
    DC.L    $00000000,$4ec010f0,$80004e80,$10f08000,$41c01100,$80000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$0000e108,$2e988000,$e0082e98,$80000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00004400
    DC.L    $30728000,$00000000,$00004e71,$58f08000,$46003072,$80000000,$00000000,$00002622
    DC.L    $40000000,$1d120000,$0000128a,$80000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00004840,$2ab28000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00002b66,$00000000,$00000000,$00000000,$0000e118,$2e988000
    DC.L    $e0182e98,$80000000,$00000000,$00000000,$00000000,$00000000,$4e742cf0,$80004e73
    DC.L    $58e48000,$06c02d0e,$80004e77,$58f08000,$4e7558f0,$80000000,$00000000,$54c02d42
    DC.L    $800055c0,$2d428000,$00000000,$000057c0,$2d428000,$00002e16,$00005cc0,$2d428000
    DC.L    $5ec02d42,$800052c0,$2d428000,$5fc02d42,$800053c0,$2d428000,$5dc02d42,$80005bc0
    DC.L    $2d428000,$56c02d42,$80000000,$2f204000,$5ac02d42,$80000000,$00000000,$9000015e
    DC.L    $800058c0,$2d428000,$59c02d42,$80000000,$00000000,$4ac02f86,$80000000,$00000000
    DC.L    $54f83014,$800055f8,$30148000,$00000000,$000057f8,$30148000,$00000000,$00005cf8
    DC.L    $30148000,$5ef83014,$800052f8,$30148000,$5ff83014,$800053f8,$30148000,$5df83014
    DC.L    $80005bf8,$30148000,$56f83014,$80000000,$00000000,$5af83014,$80000000,$00000000
    DC.L    $00000000,$000050f8,$30148000,$00000000,$00004a00,$307e8000,$00003092,$400058f8
    DC.L    $30148000,$59f83014,$80000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $0000c100,$00088000,$d0c0021e,$80000600,$02a08000,$50001504,$8000d100,$00028000
    DC.L    $0200128a,$80000840,$06648000,$08800664,$80000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$4afa4b1e
    DC.L    $80004848,$046a8000,$08c00664,$80000800,$05e68000,$00000000,$00000000,$00000000
    DC.L    $0cfc074e,$800008c0,$091a8000,$00000000,$000000c0,$091a8000,$b0c0021e,$80000c00
    DC.L    $02c68000,$b1080b16,$80000000,$0b4a0000,$00002d68,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00002d52,$000054c8,$0bcc8000,$55c80bcc,$800057c8,$0bcc8000
    DC.L    $5cc80bcc,$80005ec8,$0bcc8000,$52c80bcc,$80005fc8,$0bcc8000,$53c80bcc,$80005dc8
    DC.L    $0bcc8000,$5bc80bcc,$800056c8,$0bcc8000,$5ac80bcc,$800051c8,$0bcc8000,$58c80bcc
    DC.L    $800059c8,$0bcc8000,$81c009ba,$800080c0,$09ba8000,$00004f78,$40000000,$4f540000
    DC.L    $00000000,$00000000,$55800000,$00005722,$00000a00,$128a8000,$00000000,$00000000
    DC.L    $0e820000,$00000eec,$800049c0,$0f6a8000,$48800f82,$80000018,$40808001,$00000000
    DC.L    $00000022,$40808001,$00000f9c,$40000000,$00000000,$00000000,$0000f081,$3c488001
    DC.L    $f0933c48,$8001f096,$3c488001,$f0923c48,$8001f095,$3c488001,$f0943c48,$8001f08e
    DC.L    $3c488001,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$f0873c48
    DC.L    $80010000,$00000000,$f0903c48,$80010000,$00000000,$f09f3c48,$80010000,$00000000
    DC.L    $00000000,$00000000,$00000000,$f0883c48,$80010038,$40808001,$001d4080,$80010000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00003c50,$80010000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$0000000f,$3c508001
    DC.L    $00000000,$00000000,$00000000,$00204080,$80010000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00003b6c,$00010000,$00000000,$00000000
    DC.L    $00000001,$40808001,$00000000,$00000021,$40808001,$00000000,$00000023,$40808001
    DC.L    $001a4080,$8001f080,$40468001,$00003ac8,$40000000,$00000000,$00254080,$80010000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000001,$41228001,$00134122,$80010016,$41228001,$00124122,$8001000e,$40808001
    DC.L    $00154122,$80010014,$41228001,$00000000,$00000000,$00000000,$000e4122,$80010000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000007,$41228001,$00000000
    DC.L    $00000000,$00000000,$00104122,$80010000,$00000000,$00000000,$0000001f,$41228001
    DC.L    $00000000,$00000028,$40808001,$00000000,$00000000,$00000000,$00000000,$00000008
    DC.L    $41228001,$000f4080,$80010000,$00000000,$00000000,$0000003a,$41c88001,$00000000
    DC.L    $00000000,$15520000,$00004e14,$00000000,$4e020000,$00004dfc,$00000000,$4e0e0000
    DC.L    $00004e08,$00000000,$4d480000,$00004d8a,$00000000,$4e1a0000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$4e5011ae,$80000000,$eaa84000,$00001268
    DC.L    $40000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00001630,$8000c1c0,$09ba8000,$c0c009ba,$80004800,$1caa8000,$40003072,$80000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00008140,$2a768000,$00002ac2
    DC.L    $4000f087,$449680ff,$f0864496,$80fff081,$449680ff,$f0804496,$80fff08f,$449680ff
    DC.L    $f08e4496,$80fff08d,$449680ff,$f08c4496,$80fff08b,$449680ff,$f08a4496,$80fff083
    DC.L    $449680ff,$f0824496,$80fff085,$449680ff,$f0844496,$80fff089,$449680ff,$f0884496
    DC.L    $80ff0000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00002ae2,$40000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000007,$496080ff,$00064960
    DC.L    $80ff0000,$00000000,$00014960,$80ff0000,$496080ff,$000f4960,$80ff000e,$496080ff
    DC.L    $000d4960,$80ff000c,$496080ff,$000b4960,$80ff000a,$496080ff,$00034960,$80ff0002
    DC.L    $496080ff,$00054960,$80ff0004,$496080ff,$00094960,$80ff0008,$496080ff,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$000055d6,$00000000,$00000000
    DC.L    $00002c98,$0000e110,$2e988000,$e0102e98,$80000000,$00000000,$00000000,$00008100
    DC.L    $00088000,$00000000,$00004e72,$2f4e8000,$90c0021e,$80000400,$02a08000,$51001504
    DC.L    $80000000,$00000000,$91000002,$80004840,$2f788000,$08004b64,$80000000,$4b648000
    DC.L    $00000000,$00000000,$2d600000,$5af83014,$80004e40,$2f928000,$4e5830e0,$80008180
    DC.L    $2a768000,$00003104,$40000000,$315e4000,$eac0051a,$8000ecc0,$051a8000,$00000000
    DC.L    $0000edc0,$04d08000,$efc00492,$8000eec0,$051a8000,$e8c0051a,$800006c0,$06b28000
    DC.L    $00000806,$8000f418,$4bc28000,$f4084bee,$8000f410,$4bee8000,$00000000,$00000000
    DC.L    $00000000,$00002d90,$80004c40,$096a8000,$4c400966,$80000000,$00000000,$00004f54
    DC.L    $00000000,$00000000,$001c4080,$8001000c,$40808001,$000a4080,$8001f097,$3c488001
    DC.L    $f09c3c48,$8001f099,$3c488001,$f09d3c48,$8001f09a,$3c488001,$f09b3c48,$8001f083
    DC.L    $3c488001,$f0863c48,$8001f082,$3c488001,$f0853c48,$8001f084,$3c488001,$f0913c48
    DC.L    $8001f09e,$3c488001,$f0893c48,$8001f08b,$3c488001,$f08a3c48,$8001f08d,$3c488001
    DC.L    $f08c3c48,$80010019,$40808001,$005c406c,$80010066,$406c8001,$00013c50,$80010013
    DC.L    $3c508001,$00163c50,$80010012,$3c508001,$00153c50,$80010014,$3c508001,$000e3c50
    DC.L    $80010000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000007,$3c508001
    DC.L    $00000000,$00000010,$3c508001,$00000000,$0000001f,$3c508001,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000008,$3c508001,$0064406c,$80010000,$00000000,$0067406c
    DC.L    $8001005e,$406c8001,$00000000,$0000006c,$406c8001,$00104080,$80010000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000016,$40808001,$00144080,$80010000
    DC.L    $3c648001,$00000000,$00000000,$00000000,$0058406c,$80010062,$406c8001,$f1004102
    DC.L    $80010000,$00000000,$0060406c,$80010000,$00000000,$00174122,$80010000,$00000000
    DC.L    $00000000,$00000002,$40808001,$00000000,$00000063,$406c8001,$005a406c,$8001001c
    DC.L    $41228001,$00194122,$8001001d,$41228001,$001a4122,$8001001b,$41228001,$00034122
    DC.L    $80010006,$41228001,$00024122,$80010005,$41228001,$00044122,$80010004,$40808001
    DC.L    $00114122,$8001001e,$41228001,$00000000,$00000068,$406c8001,$00094122,$8001000b
    DC.L    $41228001,$000a4122,$8001000d,$41228001,$000c4122,$80010009,$40808001,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00004fdc,$00000000
    DC.L    $55700000,$00000000,$00000000,$00000000,$20401a64,$80004e7a,$17848000,$48801928
    DC.L    $80000108,$1aee8000,$70001bba,$80000e00,$1c368000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$000744d2,$80ff0006,$44d280ff,$000144d2,$80ff0000
    DC.L    $44d280ff,$000f44d2,$80ff000e,$44d280ff,$000d44d2,$80ff000c,$44d280ff,$000b44d2
    DC.L    $80ff000a,$44d280ff,$000344d2,$80ff0002,$44d280ff,$000544d2,$80ff0004,$44d280ff
    DC.L    $000944d2,$80ff0008,$44d280ff,$00000000,$00000000,$00000000,$0040499a,$80ff0000
    DC.L    $499a80ff,$f00047d0,$80ff0000,$00000000,$f100493c,$80ff0000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00002b06,$40004e70,$58e48000,$00000000,$00000000,$2cde4000
    DC.L    $00000000,$00000000,$00000000,$0c004b64,$80000400,$4b648000,$08002fc0,$80000000
    DC.L    $2fc08000,$4e7658f0,$8000ebc0,$04d08000,$e9c004d0,$80000000,$00000000,$f4384bc2
    DC.L    $8000f428,$4bee8000,$f4304bee,$80000000,$4f784000,$00000e76,$0000000d,$40808001
    DC.L    $f0983c48,$80010017,$3c508001,$001c3c50,$80010019,$3c508001,$001d3c50,$8001001a
    DC.L    $3c508001,$001b3c50,$80010003,$3c508001,$00063c50,$80010002,$3c508001,$00053c50
    DC.L    $80010004,$3c508001,$00113c50,$8001001e,$3c508001,$00093c50,$8001000b,$3c508001
    DC.L    $000a3c50,$8001000d,$3c508001,$000c3c50,$80010044,$40808001,$0045406c,$80010000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00034080,$80010015,$40808001,$00000000
    DC.L    $00000000,$00000000,$c0003e42,$80010000,$0fa44000,$00000000,$00000026,$40808001
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000040,$40808001,$00184122,$80010041
    DC.L    $406c8001,$00000000,$00000000,$00000000,$000041b2,$80010000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$000f41b2,$80010000,$00000000
    DC.L    $00000000,$00000000,$00000000,$0000101c,$80000000,$10ca4000,$00000000,$00000000
    DC.L    $00000000,$01c04b2c,$80000000,$00000000,$00001552,$8000f600,$4c208000,$0000ec9c
    DC.L    $40000000,$2ada4000,$00001cb6,$00000000,$2a444000,$f00045e0,$80ff2200,$477680ff
    DC.L    $20004776,$80ff0000,$00000000,$00000000,$00008200,$499a80ff,$8000499a,$80ff0000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$0000f000,$4aa480ff,$00000000,$00000000,$00000000
    DC.L    $000030da,$40000000,$0ba64000,$00183c50,$80010008,$40808001,$001e4080,$8001001f
    DC.L    $40808001,$00054080,$8001f000,$3ff68001,$00000000,$00000024,$40808001,$00274080
    DC.L    $8001f000,$41368001,$00124080,$80010001,$41b28001,$001341b2,$80010016,$41b28001
    DC.L    $001241b2,$80010015,$41b28001,$001441b2,$8001000e,$41b28001,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$000741b2,$80010000,$00000000,$001041b2
    DC.L    $80010000,$00000000,$001f41b2,$80010000,$00000000,$00000000,$00000000,$00000000
    DC.L    $000841b2,$80010011,$40808001,$4afc58f0,$80000000,$10d64000,$00000000,$00000000
    DC.L    $13904000,$f0004532,$80fff500,$457a80ff,$f000474c,$80fff000,$472880ff,$f00047b0
    DC.L    $80ff0000,$00000000,$00074a7e,$80ff0006,$4a7e80ff,$00014a7e,$80ff0000,$4a7e80ff
    DC.L    $000f4a7e,$80ff000e,$4a7e80ff,$000d4a7e,$80ff000c,$4a7e80ff,$000b4a7e,$80ff000a
    DC.L    $4a7e80ff,$00034a7e,$80ff0002,$4a7e80ff,$00054a7e,$80ff0004,$4a7e80ff,$00094a7e
    DC.L    $80ff0008,$4a7e80ff,$00002cd6,$40000000,$2e040000,$f14040e2,$80010017,$41b28001
    DC.L    $001c41b2,$80010019,$41b28001,$001d41b2,$8001001a,$41b28001,$001b41b2,$80010003
    DC.L    $41b28001,$000641b2,$80010002,$41b28001,$000541b2,$80010004,$41b28001,$001141b2
    DC.L    $8001001e,$41b28001,$000941b2,$8001000b,$41b28001,$000a41b2,$8001000d,$41b28001
    DC.L    $000c41b2,$80010000,$123e4000,$f51045be,$80fff140,$491880ff,$001841b2
    DC.B    $80,$01
h0_F82E:
    rts
h0_F830:
    rts
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $F832 is not reached from known entrypoints
    DC.L    $01036728,$226e01aa,$4a2e0238,$6612222e,$023c92a9,$001ad3a9,$00122342,$001a600c
    DC.B    $08,$e9,$00,$00,$00,$10,$66,$04,$23,$42,$00,$16,$70,$00,$4e,$75 ; VIOLATION: orphaned code island at $F854 is not reached from known entrypoints
    DC.L    $70ff4e75 ; VIOLATION: orphaned code island at $F864 is not reached from known entrypoints
h0_F868:
    movea.l $01AA(a6),a0
    btst.b #1,$0010(a0)
    bne.w h0_F884
h0_F876:
    add.l d1,$024C(a6)
    bset.b #0,$0010(a0)
    beq.s h0_F88A
h0_F882:
    rts
h0_F884:
    jmp h0_845A.l
h0_F88A:
    moveq.l #8,d0
    jmp h0_858C.l
h0_F892:
    move.b #$E,$0108(a6)
    tst.b $0238(a6)
    bne.s h0_F8EA
h0_F89E:
    move.l a1,d2
    bsr.w h0_9B24
h0_F8A4:
    beq.s h0_F8E4
h0_F8A6:
    movem.l a0-a1,-(a7)
    moveq.l #34,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_F8B0:
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
    bne.s h0_F8DE
h0_F8D8:
    bset.b #1,$0010(a0)
h0_F8DE:
    clr.l $0008(a0)
    movea.l a0,a1
h0_F8E4:
    move.l a1,$01AA(a6)
    rts
h0_F8EA:
    bsr.w h0_9B24
h0_F8EE:
    bne.w h0_9B64
h0_F8F2:
    move.l $000C(a1),$024C(a6)
    bne.s h0_F902
h0_F8FA:
    lea.l $05A8(a6),a0
    move.l a0,$024C(a6)
h0_F902:
    move.l a1,$01AA(a6)
    tst.l app_file_0186+fh_Pos(a6)
    beq.s h0_F92A
h0_F90C:
    movem.l a1/a4,-(a7)
    movea.l app_file_0186+fh_Pos(a6),a4
    move.b (a4)+,d1
    jsr h0_16CC.l
h0_F91C:
    movem.l (a7)+,a1/a4
    move.l d2,$001E(a1)
    bset.b #2,$0010(a1)
h0_F92A:
    rts
h0_F92C:
    bsr.w h0_9B24
h0_F930:
    bne.w h0_9B64
h0_F934:
    tst.b $0238(a6)
    bne.s h0_F94E
h0_F93A:
    move.l $023C(a6),d2
    sub.l $001A(a1),d2
    add.l d2,$0012(a1)
    move.l $023C(a6),$001A(a1)
    rts
h0_F94E:
    move.l a5,$000C(a1)
    rts
h0_F954:
    lea.l $01A6(a6),a3
h0_F958:
    tst.l (a3)
    beq.s h0_F980
h0_F95C:
    movea.l (a3),a3
    move.l $0012(a3),d1
    beq.s h0_F97E
h0_F964:
    btst.b #1,$0010(a3)
    bne.s h0_F97E
h0_F96C:
    addq.l #8,d1
    bsr.w h0_ExecAllocMem_90BA          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_F972:
    move.l a0,$0008(a3)
    move.l a0,$000C(a3)
    adda.l $0012(a3),a0
h0_F97E:
    bra.s h0_F958
h0_F980:
    rts
h0_F982:
    movea.l $01AA(a6),a1
    btst.b #1,$0010(a1)
    eori #4,ccr
    rts
h0_F992:
    bsr.w h0_97A6
h0_F996:
    bra.w h0_F9DA
    DC.B    $4e,$75
h0_F99C:
    rts
h0_F99E:
    move.l d2,(a5)+
    rts
h0_F9A2:
    move.w d2,(a5)+
    rts
h0_F9A6:
    move.b d2,(a5)+
    rts
h0_F9AA:
    lea.l dat_F9B6(pc),a0
    rts
h0_F9B0:
    lea.l dat_F9BF(pc),a0
    rts
dat_F9B6:
    DC.B    $53,$2d,$72,$65,$63,$6f,$72,$64,$00
dat_F9BF:
    DC.L    $2e6d7800
dat_F9C3:
    DC.B    "HISOFT DEVPAC",0
    DC.B    $00,$12,$d8
    DC.L    $66fc5389
    DC.B    $4e,$75
h0_F9DA:
    bsr.w h0_A110
h0_F9DE:
    lea.l $01AE(a6),a2
    tst.b (a2)
    bne.s h0_F9EA
h0_F9E6:
    lea.l dat_F9C3(pc),a2
h0_F9EA:
    moveq.l #0,d6
    moveq.l #0,d5
    movea.l a2,a0
h0_F9F0:
    tst.b (a0)+
    bne.s h0_F9F0
h0_F9F4:
    move.l a0,d2
    sub.l a2,d2
    subq.l #1,d2
    bsr.w h0_FA74
h0_F9FE:
    lea.l $01A6(a6),a3
h0_FA02:
    movea.l (a3),a3
    move.l $0012(a3),d3
    beq.s h0_FA6C
h0_FA0A:
    btst.b #1,$0010(a3)
    bne.s h0_FA6C
h0_FA12:
    move.l $0016(a3),d2
    btst.b #2,$0010(a3)
    beq.s h0_FA22
h0_FA1E:
    move.l $001E(a3),d2
h0_FA22:
    add.l d3,d2
    moveq.l #3,d5
    cmp.l #$1000000,d2
    bcc.s h0_FA3A
h0_FA2E:
    moveq.l #2,d5
    cmp.l #$10000,d2
    bcc.s h0_FA3A
h0_FA38:
    moveq.l #1,d5
h0_FA3A:
    movea.l $0008(a3),a2
    move.l $0016(a3),d6
    btst.b #2,$0010(a3)
    beq.s h0_FA4E
h0_FA4A:
    move.l $001E(a3),d6
h0_FA4E:
    moveq.l #28,d2
    cmp.l d2,d3
    bge.s h0_FA56
h0_FA54:
    move.l d3,d2
h0_FA56:
    sub.l d2,d3
    bsr.s h0_FA74
h0_FA5A:
    tst.l d3
    bne.s h0_FA4E
h0_FA5E:
    moveq.l #10,d0
    sub.w d5,d0
    move.w d0,d5
    move.l $0016(a3),d6
    moveq.l #0,d2
    bsr.s h0_FA74
h0_FA6C:
    tst.l (a3)
    bne.s h0_FA02
h0_FA70:
    bra.w h0_A0F6
h0_FA74:
    cmp.w #$49,d4
    bcc.s h0_FA7E
h0_FA7A:
    bsr.w h0_A0F6
h0_FA7E:
    moveq.l #48,d1
    add.b d5,d1
    movea.l a4,a0
    move.b #$53,(a4)+
    move.b d1,(a4)+
    addq.w #2,a4
    moveq.l #0,d7
    move.w d5,d1
    add.w d1,d1
    lea.l dat_FAF2(pc,d1.w),a1
    move.b (a1)+,d1
    move.l d6,d0
    lsl.l d1,d0
    move.l d0,-(a7)
    move.b (a1)+,d0
    movea.l a7,a1
h0_FAA2:
    move.b (a1)+,d1
    bsr.s h0_FADE
h0_FAA6:
    subq.b #1,d0
    bne.s h0_FAA2
h0_FAAA:
    addq.l #4,a7
    add.l d2,d6
    tst.l d2
    bra.s h0_FAB8
h0_FAB2:
    move.b (a2)+,d1
    bsr.s h0_FADE
h0_FAB6:
    subq.l #1,d2
h0_FAB8:
    bne.s h0_FAB2
h0_FABA:
    move.l a4,-(a7)
    move.l a4,d1
    sub.l a0,d1
    addq.l #2,d1
    sub.l d1,d4
    lsr.w #1,d1
    subq.w #2,d1
    lea.l $0002(a0),a4
    bsr.s h0_FADE
h0_FACE:
    movea.l (a7)+,a4
    not.b d7
    move.b d7,d1
    bsr.s h0_FADE
h0_FAD6:
    move.b #$A,(a4)+
    subq.l #1,d4
    rts
h0_FADE:
    add.b d1,d7
    move.w d1,-(a7)
    lsr.w #4,d1
    bsr.s h0_FAE8
h0_FAE6:
    move.w (a7)+,d1
h0_FAE8:
    andi.w #15,d1
    move.b dat_FB06(pc,d1.w),(a4)+
    rts
dat_FAF2:
    DC.B    $00,$02
    DC.L    $10020803,$00040001,$00010001,$00040803
    DC.B    $10,$02
dat_FB06:
    DC.B    $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46
h0_FB16:
    bsr.w h0_97A6
h0_FB1A:
    movea.l $016A(a6),a1
    movea.l (a1),a1
    move.l #$84034,d2
    lea.l dat_FC7C(pc),a2
    bsr.w h0_FC5E
h0_FB2E:
    move.l d1,-(a7)
    lea.l dat_FC7C(pc),a2
    movea.l $0172(a6),a1
    movea.l (a1),a1
    move.l #$3900,d2
    bsr.w h0_FC5E
h0_FB44:
    add.l (a7)+,d1
    addi.l #10,d1
    jsr h0_ExecAllocMem_90BA.l          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_FB52:
    movea.l a0,a2
    move.w #$0,(a2)
    lea.l $000A(a0),a0
    move.l #$A,$0002(a2)
    lea.l $0002(a2),a3
    movea.l $016A(a6),a1
    movea.l (a1),a1
    move.l #$84034,d2
    bsr.w h0_FBA0
h0_FB78:
    clr.l (a3)
    lea.l $0006(a2),a3
    movea.l $0172(a6),a1
    movea.l (a1),a1
    move.l #$3900,d2
    bsr.w h0_FBA0
h0_FB8E:
    move.l a0,d1
    sub.l a2,d1
    movea.l a2,a0
    jsr h0_8422.l
h0_FB9A:
    bra.w h0_98AE
h0_FB9E:
    rts
h0_FBA0:
    move.l a1,d1
    beq.s h0_FB9E
h0_FBA4:
    move.b $000D(a1),d0
    move.l a1,-(a7)
    btst d0,d2
    beq.s h0_FBF6
h0_FBAE:
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
h0_FBCE:
    move.b (a1)+,(a0)+
    dbf.w d0,h0_FBCE
h0_FBD4:
    movea.l d1,a1
    move.b $000D(a1),d0
    cmp.b #$8,d0
    beq.s h0_FC04
h0_FBE0:
    cmp.b #$B,d0
    bcs.s h0_FBF6
h0_FBE6:
    cmp.b #$E,d0
    bcc.s h0_FBF6
h0_FBEC:
    move.b #$D,$000D(a1)
    clr.l $0098(a1)
h0_FBF6:
    movea.l (a7),a1
    movea.l (a1),a1
    bsr.s h0_FBA0
h0_FBFC:
    movea.l (a7)+,a1
    movea.l $0004(a1),a1
    bra.s h0_FBA0
h0_FC04:
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
h0_FC2E:
    move.l $0004(a1),d0
    sub.l (a1),d0
    move.l $0008(a1),-(a7)
    movea.l (a1),a1
    subq.w #1,d0
    bmi.s h0_FC44
h0_FC3E:
    move.b (a1)+,(a0)+
    dbf.w d0,h0_FC3E
h0_FC44:
    move.l (a7)+,d0
    beq.s h0_FC4C
h0_FC48:
    movea.l d0,a1
    bra.s h0_FC2E
h0_FC4C:
    move.l a0,d0
    sub.l a2,d0
    movea.l (a7)+,a1
    move.l d0,(a1)
    btst #0,d0
    beq.s h0_FC5C
h0_FC5A:
    addq.w #1,a0
h0_FC5C:
    bra.s h0_FBF6
h0_FC5E:
    moveq.l #0,d1
    move.l a1,d0
    beq.s h0_FC7A
h0_FC64:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_FC5E
h0_FC6A:
    movea.l (a7),a1
    move.l d1,-(a7)
    movea.l $0004(a1),a1
    bsr.s h0_FC5E
h0_FC74:
    add.l (a7)+,d1
    movea.l (a7)+,a1
    jsr (a2)                            ; CANDIDATE: indirect_call index unresolved
h0_FC7A:
    rts
dat_FC7C:
    DC.L    $1029000d,$01026750,$b03c0008,$6714b03c,$000b6532,$b03c000e,$642c0681,$000000b2 ; VIOLATION: orphaned code island at $FC7C is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $2f,$09 ; VIOLATION: orphaned code island at $FC9E is not reached from known entrypoints
    DC.L    $06810000,$00102269,$0008d2a9,$00049291,$20290008,$67042240
    DC.B    $60,$f0
    DC.B    $52,$81 ; VIOLATION: orphaned code island at $FCBA is not reached from known entrypoints
    DC.L    $08810000,$225f7000,$10290016,$06800000,$00180880,$0000d280
    DC.B    $4e,$75
h0_FCD6:
    move.l d4,d3
    bra.s h0_FD10
h0_FCDA:
    movea.l app_timer_device_iorequest+IO_DATA(a6),a0
h0_FCDE:
    tst.b (a0)
    beq.s h0_FD02
h0_FCE2:
    lea.l app_timer_device_iorequest+IOSTD_SIZE(a6),a1
h0_FCE6:
    move.b (a0)+,(a1)+
    bne.s h0_FCE6
h0_FCEA:
    move.l a0,-(a7)
    lea.l app_timer_device_iorequest+IOSTD_SIZE(a6),a0
    lea.l dat_9656(pc),a2
    jsr h0_45DC.l
h0_FCFA:
    bsr.w h0_FD04
h0_FCFE:
    movea.l (a7)+,a0
    bra.s h0_FCDE
h0_FD02:
    rts
h0_FD04:
    jsr h0_AFDE.l
h0_FD0A:
    bne.w h0_FD8C
h0_FD0E:
    move.l d2,d1
h0_FD10:
    move.l d1,-(a7)
    jsr h0_ExecAllocMem_90BA.l          ; KNOWN: SysBase _LVOAllocMem fallback via local wrapper
h0_FD18:
    move.l (a7),d1
    move.l a0,(a7)
    move.l d3,-(a7)
    bsr.w h0_DOSRead_AFF6
h0_FD22:
    move.l (a7)+,d3
    bsr.w h0_AFF2
h0_FD28:
    movea.l (a7)+,a2
    move.l a2,d2
    move.w (a2),d0
    cmp.w #$0,d0
    bne.s h0_FD94
h0_FD34:
    movem.l a3-a5,-(a7)
    movea.l $0002(a2),a0
    movea.l $016A(a6),a2
    bsr.s h0_FD5C
h0_FD42:
    movea.l d2,a0
    movea.l $0006(a0),a0
    movea.l $0172(a6),a2
    bsr.s h0_FD5C
h0_FD4E:
    movem.l (a7)+,a3-a5
h0_FD52:
    rts
h0_FD54:
    move.l (a0),d0
    beq.s h0_FD52
h0_FD58:
    clr.l (a0)
    movea.l d0,a0
h0_FD5C:
    adda.l d2,a0
    move.l d2,-(a7)
    jsr h0_0B78.l
h0_FD66:
    movem.l (a7)+,d2
    beq.s h0_FD54
h0_FD6C:
    move.l a0,(a1)
    move.b $000D(a0),d1
    cmp.b #$8,d1
    bne.s h0_FD54
h0_FD78:
    add.l d2,$0008(a0)
    movea.l $0008(a0),a1
    add.l d2,$0004(a1)
    add.l d2,(a1)
    bra.s h0_FD54
    DC.L    $70056002 ; VIOLATION: orphaned code island at $FD88 is not reached from known entrypoints
h0_FD8C:
    moveq.l #27,d0
h0_FD8E:
    jmp h0_846E.l
h0_FD94:
    moveq.l #103,d0
    bra.s h0_FD8E

