INCLUDE "GEMDOS.I"
INCLUDE "XBIOS.I"

    COMMENT HEAD=$7
    SECTION TEXT,code
h0_0000:
    bra.s h0_001E
    DC.B    $95,$29
    DC.L    $7b008696
    DC.B    "Gen(C) HiSoft 1985-93",0
h0_001E:
    jsr h0_B8BE.l
h0_0024:
    jsr h0_9192.l
h0_002A:
    move.l a7,$0266(a6)
    subq.l #4,$0266(a6)
    movea.l #dat_B65C,a0
    lea.l -$0002(a6),a1
    moveq.l #63,d0
h0_003E:
    move.l (a0)+,(a1)+
    dbf.w d0,h0_003E
h0_0044:
    lea.l $00FE(a6),a0
    move.w #$AD,d0
h0_004C:
    clr.w (a0)+
    dbf.w d0,h0_004C
h0_0052:
    sf.b $026C(a6)
    sf.b $026A(a6)
    clr.b $052F(a6)
    jsr h0_9134.l
h0_0064:
    lea.l $027A(a6),a1
    clr.l (a1)
    move.l a1,$0178(a6)
    lea.l $0276(a6),a1
    clr.l (a1)
    move.l a1,$0170(a6)
    bsr.w h0_6EA4
h0_007C:
    clr.b $06FE(a6)
    lea.l $507C(a6),a3
    bsr.w h0_474A
h0_0088:
    lea.l $0868(a6),a3
    bsr.w h0_474A
h0_0090:
    clr.b $0816(a6)
    lea.l $475A(a6),a0
    move.l a0,$47FA(a6)
    clr.w $0286(a6)
    move.b #$64,$026C(a6)
    jsr h0_B956.l
h0_00AC:
    bne.w h0_045E
h0_00B0:
    clr.b $07C4(a6)
    st.b $46FA(a6)
    sf.b $46FB(a6)
    sf.b $46FC(a6)
    st.b $46FD(a6)
    jsr h0_BB64.l
h0_00CA:
    sf.b $0103(a6)
    jsr h0_BB50.l
h0_00D4:
    sf.b $0103(a6)
    lea.l $0816(a6),a0
    tst.b (a0)
    beq.s h0_00F8
h0_00E0:
    jsr h0_BAF8.l
h0_00E6:
    beq.w h0_015C
h0_00EA:
    move.l a0,$0262(a6)
    jsr h0_BB22.l
h0_00F4:
    bne.w h0_0158
h0_00F8:
    jsr h0_BBAA.l
h0_00FE:
    tst.b $052F(a6)
    beq.w h0_0160
h0_0106:
    tst.b $0129(a6)
    bne.s h0_0114
h0_010C:
    moveq.l #0,d0
    jsr h0_8F00.l
h0_0114:
    jsr h0_4672.l
h0_011A:
    bne.w h0_0154
h0_011E:
    jsr h0_10E3C.l
h0_0124:
    sf.b $026C(a6)
    lea.l $475A(a6),a0
    move.l a0,$47FA(a6)
    clr.b $010B(a6)
    lea.l $052A(a6),a0
    jsr h0_8904.l
h0_013E:
    beq.s h0_01B0
h0_0140:
    moveq.l #10,d0
    jsr h0_8F00.l
h0_0148:
    bsr.s h0_016C
h0_014A:
    move.b #$64,$026C(a6)
    bra.w h0_045E
h0_0154:
    moveq.l #26,d0
    bra.s h0_0162
h0_0158:
    moveq.l #24,d0
    bra.s h0_0162
h0_015C:
    moveq.l #25,d0
    bra.s h0_0162
h0_0160:
    moveq.l #23,d0
h0_0162:
    jsr h0_8F00.l
h0_0168:
    bra.w h0_045E
h0_016C:
    lea.l $052A(a6),a0
    moveq.l #0,d0
    move.b $0005(a0),d0
    subq.w #2,d0
    bmi.s h0_0188
h0_017A:
    addq.w #6,a0
h0_017C:
    move.b (a0)+,d1
    jsr h0_8F1E.l
h0_0184:
    dbf.w d0,h0_017C
h0_0188:
    jmp h0_8F12.l
h0_018E:
    move.w $024C(a6),-(a7)
    clr.w $024C(a6)
    jsr h0_BB50.l
h0_019C:
    bne.s h0_0160
h0_019E:
    jsr h0_BB22.l
h0_01A4:
    bne.s h0_0158
h0_01A6:
    move.w (a7)+,$024C(a6)
    sf.b $0103(a6)
    rts
h0_01B0:
    tst.l $01AC(a6)
    bne.s h0_01BA
h0_01B6:
    moveq.l #29,d0
    bra.s h0_0162
h0_01BA:
    movea.l $052A(a6),a1
    move.b $052F(a6),d0
    subq.b #1,d0
h0_01C4:
    move.l a1,d2
    move.b d0,d3
h0_01C8:
    subq.b #1,d0
    bcs.s h0_01E2
h0_01CC:
    move.b (a1)+,d1
    cmp.b #$5C,d1
    beq.s h0_01C4
h0_01D4:
    cmp.b #$2F,d1
    beq.s h0_01C4
h0_01DA:
    cmp.b #$3A,d1
    beq.s h0_01C4
h0_01E0:
    bra.s h0_01C8
h0_01E2:
    lea.l $05B4(a6),a0
    movea.l d2,a1
    move.b d3,(a0)+
h0_01EA:
    beq.s h0_01F2
h0_01EC:
    move.b (a1)+,(a0)+
    subq.b #1,d3
    bra.s h0_01EA
h0_01F2:
    move.b #$D,(a0)
    bsr.w h0_0486
h0_01FA:
    sf.b $46FA(a6)
    st.b $46FB(a6)
    st.b $46FC(a6)
    jsr h0_BB64.l
h0_020C:
    sf.b $0103(a6)
    lea.l $05DE(a6),a0
    move.l a0,$027E(a6)
    tst.b $0129(a6)
    bne.s h0_0232
h0_021E:
    moveq.l #27,d0
    jsr h0_8F00.l
h0_0226:
    bsr.w h0_016C
h0_022A:
    moveq.l #1,d0
    jsr h0_8F00.l
h0_0232:
    move.b $480E(a6),$480F(a6)
    sf.b $46FA(a6)
    st.b $46FB(a6)
    st.b $46FC(a6)
    sf.b $46FD(a6)
    bsr.w h0_018E
h0_024C:
    bsr.w h0_06C4
h0_0250:
    bne.s h0_029E
h0_0252:
    move.l a7,$0266(a6)
    subq.l #4,$0266(a6)
    sf.b $46FE(a6)
    bsr.w h0_0A00
h0_0262:
    bsr.w h0_0830
h0_0266:
    tst.b $46FE(a6)
    beq.s h0_0286
h0_026C:
    tst.l $01D0(a6)
    bne.s h0_0286
h0_0272:
    sf.b $46FA(a6)
    st.b $46FB(a6)
    sf.b $46FC(a6)
    sf.b $46FD(a6)
    bsr.w h0_018E
h0_0286:
    move.l a7,$0266(a6)
    subq.l #4,$0266(a6)
h0_028E:
    bsr.w h0_06C4
h0_0292:
    bne.s h0_029E
h0_0294:
    bsr.w h0_0A00
h0_0298:
    bsr.w h0_0830
h0_029C:
    bra.s h0_028E
h0_029E:
    tst.b $010D(a6)
    bne.w h0_039E
h0_02A6:
    bsr.w h0_0584
h0_02AA:
    sf.b $480F(a6)
    tst.b $0129(a6)
    bne.s h0_02BC
h0_02B4:
    moveq.l #2,d0
    jsr h0_8F00.l
h0_02BC:
    tst.b $0117(a6)
    bgt.w h0_06BC
h0_02C4:
    move.b $480E(a6),$480F(a6)
    jsr h0_BBFE.l
h0_02D0:
    st.b $026A(a6)
    bsr.w h0_0486
h0_02D8:
    tst.b $480E(a6)
    beq.s h0_02E6
h0_02DE:
    sf.b $46F4(a6)
    st.b $0101(a6)
h0_02E6:
    lea.l $0868(a6),a3
    bsr.w h0_475A
h0_02EE:
    sf.b $46FA(a6)
    st.b $46FB(a6)
    sf.b $46FC(a6)
    st.b $46FD(a6)
    jsr h0_BB64.l
h0_0304:
    sf.b $46FB(a6)
    jsr h0_BB50.l
h0_030E:
    jsr h0_BB22.l
h0_0314:
    sf.b $0103(a6)
    jsr h0_BBAA.l
h0_031E:
    lea.l $052A(a6),a0
    clr.b $010B(a6)
    jsr h0_8904.l
h0_032C:
    beq.s h0_0334
h0_032E:
    jmp h0_853E.l
h0_0334:
    st.b $46FB(a6)
    sf.b $46FD(a6)
    bsr.w h0_018E
h0_0340:
    bsr.w h0_06C4
h0_0344:
    bne.s h0_0374
h0_0346:
    sf.b $46FE(a6)
    bsr.w h0_0A00
h0_034E:
    bsr.w h0_0914
h0_0352:
    tst.b $46FE(a6)
    beq.s h0_0364
h0_0358:
    bsr.w h0_018E
h0_035C:
    move.l a7,$0266(a6)
    subq.l #4,$0266(a6)
h0_0364:
    bsr.w h0_06C4
h0_0368:
    bne.s h0_0374
h0_036A:
    bsr.w h0_0A00
h0_036E:
    bsr.w h0_0914
h0_0372:
    bra.s h0_0364
h0_0374:
    bsr.w h0_056E
h0_0378:
    bsr.w h0_7A42
h0_037C:
    bsr.w h0_7A50
h0_0380:
    jsr h0_9B12.l
h0_0386:
    tst.b $0100(a6)
    beq.s h0_0392
h0_038C:
    jsr h0_8FE6.l
h0_0392:
    tst.b $010A(a6)
    beq.s h0_039E
h0_0398:
    jsr h0_10C78.l
h0_039E:
    sf.b $480F(a6)
    jsr h0_91E4.l
h0_03A8:
    jsr h0_9B42.l
h0_03AE:
    jsr h0_8AC4.l
h0_03B4:
    tst.b $0129(a6)
    beq.s h0_03C2
h0_03BA:
    move.b $010D(a6),d1
    beq.w h0_045E
h0_03C2:
    jsr h0_8F12.l
h0_03C8:
    moveq.l #0,d1
    move.b $010D(a6),d1
    jsr h0_8F8A.l
h0_03D4:
    moveq.l #3,d0
    cmpi.b #1,$010D(a6)
    bne.s h0_03E0
h0_03DE:
    addq.b #1,d0
h0_03E0:
    jsr h0_8F00.l
h0_03E6:
    moveq.l #0,d1
    move.w $0254(a6),d1
    subq.w #1,d1
    jsr h0_8F8A.l
h0_03F4:
    moveq.l #5,d0
    jsr h0_8F00.l
h0_03FC:
    move.l $0256(a6),d1
    jsr h0_8F8A.l
h0_0406:
    moveq.l #12,d0
    jsr h0_8F00.l
h0_040E:
    jsr h0_9718.l
h0_0414:
    moveq.l #22,d0
    tst.b $0114(a6)
    bne.s h0_0426
h0_041C:
    moveq.l #18,d0
    tst.b $0116(a6)
    beq.s h0_0426
h0_0424:
    moveq.l #17,d0
h0_0426:
    jsr h0_8F00.l
h0_042C:
    moveq.l #19,d0
    jsr h0_8F00.l
h0_0434:
    moveq.l #0,d1
    move.w $01C0(a6),d1
    beq.s h0_045E
h0_043C:
    jsr h0_8F8A.l
h0_0442:
    moveq.l #13,d0
    jsr h0_8F00.l
h0_044A:
    moveq.l #0,d0
    move.w $01C2(a6),d1
    jsr h0_8F8A.l
h0_0456:
    moveq.l #14,d0
    jsr h0_8F00.l
h0_045E:
    jsr h0_91F6.l
h0_0464:
    jsr h0_BC30.l
h0_046A:
    move.l $01B8(a6),d3
    beq.s h0_047A
h0_0470:
    jsr h0_BFAE.l
h0_0476:
    clr.l $01B8(a6)
h0_047A:
    jsr h0_917E.l
h0_0480:
    jsr h0_BD0A.l
h0_0486:
    moveq.l #0,d0
    move.w d0,$024C(a6)
    move.l d0,$0256(a6)
    move.w d0,$0254(a6)
    move.l d0,$026E(a6)
    move.l d0,$0160(a6)
    move.l d0,$0168(a6)
    move.l d0,$01BC(a6)
    move.w d0,$4738(a6)
    move.w d0,$473A(a6)
    move.l d0,$473C(a6)
    move.b d0,$0107(a6)
    move.b d0,$0114(a6)
    move.b d0,$46F5(a6)
    move.b d0,$0123(a6)
    sf.b $0125(a6)
    move.b d0,$0124(a6)
    sf.b $0126(a6)
    sf.b $012E(a6)
    st.b $0130(a6)
    sf.b $012F(a6)
    move.w #$200,$0132(a6)
    move.b d0,$0134(a6)
    move.b d0,$0135(a6)
    move.b #$1,$4716(a6)
    move.b #$FF,$4726(a6)
    sf.b $0127(a6)
    move.b d0,$0131(a6)
    move.w d0,$0110(a6)
    move.w #$FFFF,$0112(a6)
    move.b d0,$0108(a6)
    move.l d0,$474A(a6)
    move.w d0,$4752(a6)
    move.w d0,$4754(a6)
    move.l d0,$0138(a6)
    move.l d0,$4704(a6)
    moveq.l #1,d0
    move.l d0,$4700(a6)
    st.b $46F4(a6)
    st.b $0106(a6)
    move.w #$80,$0252(a6)
    jsr h0_8E08.l
h0_0536:
    sf.b $0116(a6)
    sf.b $0117(a6)
    sf.b $011A(a6)
    sf.b $0119(a6)
    sf.b $0102(a6)
    sf.b $011B(a6)
    sf.b $011F(a6)
    st.b $0120(a6)
    st.b $0121(a6)
    sf.b $0128(a6)
    move.b #$2E,$0118(a6)
    move.b #$1,$0109(a6)
    bra.w h0_794E
h0_056E:
    tst.w $4738(a6)
    bne.s h0_0576
h0_0574:
    rts
h0_0576:
    move.w #$FFFF,$024C(a6)
    moveq.l #50,d0
    jmp h0_8556.l
h0_0584:
    bsr.s h0_056E
h0_0586:
    bsr.w h0_7A42
h0_058A:
    bsr.w h0_7A50
h0_058E:
    jsr h0_8AC4.l
h0_0594:
    bsr.s h0_05A8
h0_0596:
    jsr h0_8B18.l
h0_059C:
    jsr h0_97BC.l
h0_05A2:
    clr.l $01A8(a6)
    rts
h0_05A8:
    movea.l $0178(a6),a3
    movea.l (a3),a3
    bsr.s h0_05DC
h0_05B0:
    lea.l $0184(a6),a0
    bsr.s h0_05CC
h0_05B6:
    lea.l $0190(a6),a0
    bsr.s h0_05CC
h0_05BC:
    lea.l $019C(a6),a0
    bsr.s h0_05CC
h0_05C2:
    move.l $018C(a6),d0
    add.l d0,$0198(a6)
    rts
h0_05CC:
    btst.b #0,$0003(a0)
    beq.s h0_05DA
h0_05D4:
    addq.l #1,(a0)
    addq.l #1,$0008(a0)
h0_05DA:
    rts
h0_05DC:
    tst.l (a3)
    beq.s h0_05E8
h0_05E0:
    move.l a3,-(a7)
    movea.l (a3),a3
    bsr.s h0_05DC
h0_05E6:
    movea.l (a7)+,a3
h0_05E8:
    cmpi.b #9,$000D(a3)
    bne.s h0_05F6
h0_05F0:
    movea.l $0008(a3),a2
    bsr.s h0_0608
h0_05F6:
    tst.l $0004(a3)
    beq.s h0_0606
h0_05FC:
    move.l a3,-(a7)
    movea.l $0004(a3),a3
    bsr.s h0_05DC
h0_0604:
    movea.l (a7)+,a3
h0_0606:
    rts
h0_0608:
    tst.l (a2)
    beq.s h0_0614
h0_060C:
    move.l a2,-(a7)
    movea.l (a2),a2
    bsr.s h0_0608
h0_0612:
    movea.l (a7)+,a2
h0_0614:
    clr.l $0008(a2)
    tst.l $0004(a2)
    beq.s h0_0628
h0_061E:
    move.l a2,-(a7)
    movea.l $0004(a2),a2
    bsr.s h0_0608
h0_0626:
    movea.l (a7)+,a2
h0_0628:
    rts
h0_062A:
    tst.l $474A(a6)
    bne.s h0_0656
h0_0630:
    tst.b $0102(a6)
    bne.s h0_067A
h0_0636:
    movea.l $01AC(a6),a1
    movea.l $009E(a1),a0
    cmpa.l $00A2(a1),a0
    bcc.s h0_0696
h0_0644:
    cmpi.b #10,(a0)+
    beq.s h0_064C
h0_064A:
    subq.l #1,a0
h0_064C:
    move.b (a0),d0
    cmp.b d0,d0
    rts
    DC.B    $70,$ff,$4e,$75 ; VIOLATION: orphaned code island at $0652 is not reached from known entrypoints
h0_0656:
    tst.b $0102(a6)
    beq.s h0_0666
h0_065C:
    move.w $4752(a6),d0
    cmp.w $4754(a6),d0
    bhi.s h0_067A
h0_0666:
    movea.l $474A(a6),a1
    movea.l $474E(a6),a0
    cmpa.l $0004(a1),a0
    bne.s h0_064C
h0_0674:
    movea.l $0008(a1),a0
    bra.s h0_064C
h0_067A:
    movea.l $473C(a6),a2
    movea.l $0004(a2),a1
    movea.l $0010(a2),a0
    cmpa.l $0004(a1),a0
    bne.s h0_064C
h0_068C:
    movea.l $0008(a1),a1
    movea.l $0000(a1),a0
    bra.s h0_064C
h0_0696:
    moveq.l #70,d0
    jmp h0_853E.l
    DC.B    $4a,$fb
    DC.B    "include_longmac",0
h0_06B0:
    tst.b $0117(a6)
    beq.w h0_06EC
h0_06B8:
    bpl.s h0_06BC
h0_06BA:
    rts
h0_06BC:
    moveq.l #79,d0
    jmp h0_853E.l
h0_06C4:
    movea.l $01D4(a6),a0
    move.b (a0),d0
    andi.b #3,d0
    subq.b #3,d0
    beq.s h0_06BC
h0_06D2:
    tst.b $0117(a6)
    bne.s h0_06B8
h0_06D8:
    addq.w #1,$0254(a6)
    tst.b $0102(a6)
    bne.w h0_708C
h0_06E4:
    tst.l $474A(a6)
    bne.w h0_749E
h0_06EC:
    moveq.l #13,d1
    move.w #$FE,d2
    addq.w #1,$024C(a6)
h0_06F6:
    movea.l $01AC(a6),a1
    movea.l $009E(a1),a4
h0_06FE:
    cmpa.l $00A2(a1),a4
    bcc.w h0_078C
h0_0706:
    cmpi.b #10,(a4)
    bne.s h0_0710
h0_070C:
    addq.l #1,a4
    bra.s h0_06FE
h0_0710:
    move.w #$FC,d0
    moveq.l #13,d2
    move.l a4,$0272(a6)
    movea.l a4,a2
h0_071C:
    cmp.b (a2)+,d2
    dbeq.w d0,h0_071C
h0_0722:
    beq.s h0_073C
h0_0724:
    cmpa.l $00A2(a1),a2
    bhi.s h0_0752
h0_072A:
    move.b #$2A,-(a2)
    move.b #$D,-$0001(a2)
    move.l a2,$009E(a1)
    moveq.l #0,d0
    rts
h0_073C:
    moveq.l #10,d0
h0_073E:
    cmpa.l $00A2(a1),a2
    bhi.s h0_0752
h0_0744:
    cmp.b (a2)+,d0
    beq.s h0_073E
h0_0748:
    subq.l #1,a2
    move.l a2,$009E(a1)
    moveq.l #0,d0
    rts
h0_0752:
    move.l $00A6(a1),d1
    movea.l $0008(a1),a2
    adda.l d1,a2
    cmpa.l $00A2(a1),a2
    bne.s h0_07AE
h0_0762:
    move.l $00A2(a1),d2
    sub.l a4,d2
    beq.s h0_078C
h0_076A:
    move.l d2,-(a7)
    subq.l #1,d2
    movea.l a4,a0
    movea.l $0008(a1),a2
    move.l a2,$009E(a1)
h0_0778:
    move.b (a0)+,(a2)+
    dbf.w d2,h0_0778
h0_077E:
    move.l $00A6(a1),d1
    sub.l (a7)+,d1
    jsr h0_8A66.l
h0_078A:
    bra.s h0_07A4
h0_078C:
    movea.l $0008(a1),a2
    move.l a2,$009E(a1)
    adda.l $00A6(a1),a2
    cmpa.l $00A2(a1),a2
    bne.s h0_07AE
h0_079E:
    jsr h0_8A70.l
h0_07A4:
    beq.w h0_06F6
h0_07A8:
    jmp h0_853E.l
h0_07AE:
    move.w $009C(a1),$024C(a6)
    clr.w $009C(a1)
    tst.b $0136(a6)
    beq.s h0_07CA
h0_07BE:
    tst.b $026A(a6)
    beq.s h0_07CA
h0_07C4:
    move.b #$FE,$000E(a1)
h0_07CA:
    cmpi.b #12,$000D(a1)
    beq.s h0_07E6
h0_07D2:
    move.l $0098(a1),d2
    beq.s h0_07E6
h0_07D8:
    move.l a1,-(a7)
    jsr h0_BF68.l
h0_07E0:
    movea.l (a7)+,a1
    clr.l $0098(a1)
h0_07E6:
    move.l $0010(a1),$01AC(a6)
    bne.w h0_06B0
h0_07F0:
    moveq.l #-1,d0
    rts
    DC.L    $50ee0115,$4a2e026a,$6714b23c,$002b6718,$b23c002d,$670c720d,$50ee0101 ; VIOLATION: orphaned code island at $07F4 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $72,$0d,$4e,$75 ; VIOLATION: orphaned code island at $0812 is not reached from known entrypoints
    DC.B    $53,$2e,$46,$f4,$60,$04 ; VIOLATION: orphaned code island at $0816 is not reached from known entrypoints
    DC.B    $52,$2e,$46,$f4,$5a,$ee,$01,$01,$12,$1c ; VIOLATION: orphaned code island at $081C is not reached from known entrypoints
h0_0826:
    rts
h0_0828:
    tst.b $026A(a6)
    bne.w h0_0914
h0_0830:
    tst.b $012B(a6)
    beq.w h0_08FE
h0_0838:
    tst.l $01B0(a6)
    beq.w h0_08FE
h0_0840:
    cmpi.b #1,$0109(a6)
    bne.s h0_0826
h0_0848:
    move.l $01AC(a6),d0
    beq.s h0_0826
h0_084E:
    move.b $014C(a6),d6
    movea.l d0,a0
    move.l $00AE(a0),d0
    beq.s h0_0862
h0_085A:
    movea.l d0,a0
    cmp.b $0004(a0),d6
    beq.s h0_08B2
h0_0862:
    movea.l $01AC(a6),a0
    lea.l $00AA(a0),a0
h0_086A:
    move.l (a0),d0
    beq.s h0_087A
h0_086E:
    movea.l d0,a0
    cmp.b $0004(a0),d6
    beq.s h0_08AA
h0_0876:
    lea.l (a0),a0
    bra.s h0_086A
h0_087A:
    move.l a0,-(a7)
    moveq.l #32,d1
    jsr h0_9146.l
h0_0884:
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
h0_08AA:
    movea.l $01AC(a6),a1
    move.l a0,$00AE(a1)
h0_08B2:
    move.l $026E(a6),d0
    sub.l $01B0(a6),d0
    cmp.l $0006(a0),d0
    beq.s h0_08FE
h0_08C0:
    moveq.l #0,d1
    move.w $024C(a6),d1
    cmp.l $000A(a0),d1
    beq.s h0_08FE
h0_08CC:
    tst.b $012C(a6)
    beq.s h0_08F2
h0_08D2:
    addq.w #1,$0012(a0)
    lea.l $000A(a0),a1
    move.l d0,-(a7)
    move.l d1,d0
    jsr h0_8B8C.l
h0_08E4:
    move.l (a7)+,d0
    lea.l $0006(a0),a1
    jsr h0_8B8C.l
h0_08F0:
    bra.s h0_08FE
h0_08F2:
    addq.l #8,$0018(a0)
    move.l d0,$0006(a0)
    move.l d1,$000A(a0)
h0_08FE:
    tst.b $0103(a6)
    bne.w h0_09DC
h0_0906:
    tst.b $024E(a6)
    beq.w h0_09CE
h0_090E:
    bra.w h0_09DC
h0_0912:
    rts
h0_0914:
    tst.b $012B(a6)
    beq.w h0_09AA
h0_091C:
    tst.l $01B0(a6)
    beq.w h0_09AA
h0_0924:
    cmpi.b #1,$0109(a6)
    bne.s h0_09AA
h0_092C:
    move.l $01AC(a6),d0
    beq.s h0_0912
h0_0932:
    movea.l d0,a0
    move.b $014C(a6),d6
    movea.l $00AE(a0),a0
    cmp.b $0004(a0),d6
    beq.s h0_0956
h0_0942:
    movea.l $01AC(a6),a1
    lea.l $00AA(a1),a0
h0_094A:
    movea.l (a0),a0
    cmp.b $0004(a0),d6
    bne.s h0_094A
h0_0952:
    move.l a0,$00AE(a1)
h0_0956:
    move.l $026E(a6),d0
    sub.l $01B0(a6),d0
    cmp.l $0006(a0),d0
    beq.s h0_09AA
h0_0964:
    moveq.l #0,d1
    move.w $024C(a6),d1
    cmp.l $000A(a0),d1
    beq.s h0_09AA
h0_0970:
    tst.b $012C(a6)
    beq.s h0_0996
h0_0976:
    lea.l $000A(a0),a1
    move.l d0,-(a7)
    move.l d1,d0
    jsr h0_8BC2.l
h0_0984:
    move.l a1,$0014(a0)
    move.l (a7)+,d0
    lea.l $0006(a0),a1
    jsr h0_8BC2.l
h0_0994:
    bra.s h0_09A6
h0_0996:
    movea.l $0014(a0),a1
    move.l d0,$0006(a0)
    move.l d1,$000A(a0)
    move.l d1,(a1)+
    move.l d0,(a1)+
h0_09A6:
    move.l a1,$0014(a0)
h0_09AA:
    tst.b $0103(a6)
    bne.s h0_09DC
h0_09B0:
    tst.b $0101(a6)
    beq.s h0_09CE
h0_09B6:
    tst.b $0115(a6)
    bne.s h0_09CE
h0_09BC:
    tst.b $0102(a6)
    beq.s h0_09DC
h0_09C2:
    tst.b $011A(a6)
    bne.s h0_09DC
h0_09C8:
    tst.b $0119(a6)
    bne.s h0_09DC
h0_09CE:
    sf.b $0115(a6)
    clr.b $46F5(a6)
    sf.b $011A(a6)
    rts
h0_09DC:
    sf.b $0103(a6)
    jsr h0_937C.l
h0_09E6:
    bra.s h0_09CE
    DC.L    $50ee0115,$720d4a2e,$026a6708,$51ee0101,$50ee46f4 ; VIOLATION: orphaned code island at $09E8 is not reached from known entrypoints
    DC.B    $4e,$75
h0_09FE:
    rts
h0_0A00:
    movea.l $027E(a6),a5
    move.l a5,$0282(a6)
    clr.l $01B0(a6)
    sf.b $010E(a6)
    move.b (a4)+,d1
    cmp.b #$D,d1
    beq.s h0_09FE
h0_0A18:
    cmp.b #$9,d1
    beq.s h0_0A24
h0_0A1E:
    cmp.b #$20,d1
    bne.s h0_0A48
h0_0A24:
    clr.l $041E(a6)
    bra.w h0_0A6A
h0_0A2C:
    cmp.b #$A,d1
    beq.w h0_0C84
h0_0A34:
    cmp.b #$3B,d1
    beq.w h0_0C84
h0_0A3C:
    cmp.b #$2A,d1
    beq.w h0_0C84
h0_0A44:
    bra.w h0_8502
h0_0A48:
    st.b d2
    lea.l $041E(a6),a0
    clr.b $0004(a0)
    bsr.w h0_7726
h0_0A56:
    bne.s h0_0A2C
h0_0A58:
    cmp.b #$3A,d1
    bne.s h0_0A6C
h0_0A5E:
    move.b (a4)+,d1
    cmp.b #$3A,d1
    bne.s h0_0A6C
h0_0A66:
    st.b $0422(a6)
h0_0A6A:
    move.b (a4)+,d1
h0_0A6C:
    cmp.b #$9,d1
    beq.s h0_0A6A
h0_0A72:
    cmp.b #$20,d1
    beq.s h0_0A6A
h0_0A78:
    cmp.b #$3D,d1
    beq.w h0_74EC
h0_0A80:
    subq.l #1,a4
    move.l a4,-(a7)
    moveq.l #0,d2
    movea.l #dat_C328,a0
    movea.l #dat_DE12,a1
    movea.l #dat_CB06,a2
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AF2
h0_0AA8:
    move.w $0(a2,d1.w),d2
    bmi.s h0_0B28
h0_0AAE:
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AF2
h0_0ABE:
    move.w $0(a2,d1.w),d2
    bmi.s h0_0B28
h0_0AC4:
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AF2
h0_0AD4:
    move.w $0(a2,d1.w),d2
    bmi.s h0_0B28
h0_0ADA:
    moveq.l #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w $0(a0,d2.w),d1
    cmp.w $0(a1,d1.w),d2
    bne.s h0_0AF2
h0_0AEA:
    move.w $0(a2,d1.w),d2
    bpl.s h0_0ADA
h0_0AF0:
    bra.s h0_0B28
h0_0AF2:
    move.w d2,d1
    add.w d1,d1
    add.w d1,d2
    movea.l #dat_F11E,a0
    adda.w d2,a0
    tst.w $0002(a0)
    beq.s h0_0B28
h0_0B06:
    move.b -$0001(a4),d1
    cmp.b #$2E,d1
    beq.s h0_0B22
h0_0B10:
    cmp.b #$D,d1
    beq.s h0_0B22
h0_0B16:
    cmp.b #$9,d1
    beq.s h0_0B22
h0_0B1C:
    cmp.b #$20,d1
    bne.s h0_0B28
h0_0B22:
    move.l (a7)+,d2
    bra.w h0_750A
h0_0B28:
    movea.l (a7)+,a4
    move.b (a4)+,d1
    cmp.b #$D,d1
    beq.w h0_0C84
h0_0B34:
    cmp.b #$3B,d1
    beq.w h0_0C84
h0_0B3C:
    cmp.b #$2A,d1
    beq.w h0_0C84
h0_0B44:
    lea.l $0398(a6),a0
    bsr.w h0_76EE
h0_0B4C:
    bne.w h0_8502
h0_0B50:
    movea.l $0178(a6),a2
    move.l a1,d4
    movem.l d2/a3-a5,-(a7)
    bsr.w h0_0BC8
h0_0B5E:
    movem.l (a7)+,d2/a3-a5
    beq.w h0_6EBE
h0_0B66:
    movea.l d4,a4
    move.b -$0001(a4),d1
    cmp.b #$3A,d1
    bne.w h0_8516
h0_0B74:
    lea.l $041E(a6),a1
    tst.l (a1)
    bne.w h0_8516
h0_0B7E:
    move.b d2,$0005(a0)
    bsr.s h0_0B8E
h0_0B84:
    movea.l a1,a0
    clr.b $0004(a0)
    bra.w h0_0A5E
h0_0B8E:
    move.b $0005(a0),$0005(a1)
    tst.b $00FE(a6)
    bne.s h0_0BA4
h0_0B9A:
    move.l (a0),(a1)
    move.b $0006(a0),$0006(a1)
    rts
h0_0BA4:
    move.b $0005(a0),d0
    lea.l $0006(a1),a2
    move.l a2,(a1)
    addq.w #6,a0
h0_0BB0:
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s h0_0BB0
h0_0BB6:
    rts
h0_0BB8:
    move.l (a2),d0
    beq.s h0_0C08
h0_0BBC:
    movea.l d0,a1
    move.b $0016(a0),d2
    lea.l $0017(a0),a5
    bra.s h0_0BDC
h0_0BC8:
    move.l (a2),d0
    beq.s h0_0C08
h0_0BCC:
    movea.l d0,a1
    move.b $0005(a0),d2
    movea.l (a0),a5
    bra.s h0_0BDC
h0_0BD6:
    move.l (a1),d0
    beq.s h0_0C04
h0_0BDA:
    movea.l d0,a1
h0_0BDC:
    cmp.b $0016(a1),d2
    bcs.s h0_0BD6
h0_0BE2:
    bhi.s h0_0BF8
h0_0BE4:
    move.b d2,d3
    lea.l $0017(a1),a3
    movea.l a5,a4
h0_0BEC:
    cmpm.b (a3)+,(a4)+
    bcs.s h0_0BD6
h0_0BF0:
    bhi.s h0_0BF8
h0_0BF2:
    subq.b #1,d3
    bne.s h0_0BEC
h0_0BF6:
    rts
h0_0BF8:
    move.l $0004(a1),d0
    beq.s h0_0C02
h0_0BFE:
    movea.l d0,a1
    bra.s h0_0BDC
h0_0C02:
    addq.w #4,a1
h0_0C04:
    moveq.l #3,d0
    rts
h0_0C08:
    movea.l a2,a1
    moveq.l #3,d0
    rts
h0_0C0E:
    movem.l a3-a5,-(a7)
    move.l $0160(a6),d0
    beq.s h0_0C22
h0_0C18:
    movea.l d0,a2
    bsr.s h0_0BC8
h0_0C1C:
    beq.s h0_0C3C
h0_0C1E:
    move.l a1,$0164(a6)
h0_0C22:
    movea.l $0168(a6),a2
    bsr.s h0_0BC8
h0_0C28:
    beq.s h0_0C3C
h0_0C2A:
    move.l a1,$016C(a6)
    movea.l $0170(a6),a2
    bsr.s h0_0BC8
h0_0C34:
    beq.s h0_0C3C
h0_0C36:
    move.l a1,$0174(a6)
    moveq.l #-1,d0
h0_0C3C:
    movem.l (a7)+,a3-a5
    rts
h0_0C42:
    bsr.s h0_0C0E
h0_0C44:
    bne.w h0_850A
h0_0C48:
    bset.b #6,$000C(a1)
    bne.w h0_8506
h0_0C52:
    move.b $0109(a6),d3
    cmp.b $000D(a1),d3
    bne.w h0_8506
h0_0C5E:
    cmp.l $0008(a1),d4
    bne.w h0_850E
h0_0C66:
    move.b $0017(a1),d0
    cmp.b $0118(a6),d0
    beq.s h0_0C82
h0_0C70:
    tst.b $0004(a0)
    beq.s h0_0C7A
h0_0C76:
    bsr.w h0_4F2A
h0_0C7A:
    lea.l $0010(a1),a0
    move.l a0,$0160(a6)
h0_0C82:
    rts
h0_0C84:
    move.l $026E(a6),d4
    lea.l $041E(a6),a0
    tst.l (a0)
    bne.s h0_0CC4
h0_0C90:
    rts
h0_0C92:
    btst.b #0,$0271(a6)
    bne.w h0_0C9E
h0_0C9C:
    rts
h0_0C9E:
    jmp h0_993A.l
h0_0CA4:
    lea.l $041E(a6),a0
    tst.l (a0)
    beq.s h0_0C92
h0_0CAC:
    move.l $026E(a6),d4
    btst #0,d4
    beq.s h0_0CC4
h0_0CB6:
    jsr h0_993A.l
h0_0CBC:
    lea.l $041E(a6),a0
    move.l $026E(a6),d4
h0_0CC4:
    tst.b $026A(a6)
    bne.w h0_0C42
h0_0CCC:
    bsr.w h0_0C0E
h0_0CD0:
    beq.w h0_8506
h0_0CD4:
    move.b $0109(a6),d3
    move.b $0006(a0),d0
    cmp.b $0118(a6),d0
    beq.s h0_0CEC
h0_0CE2:
    pea.l h0_0C7A(pc)
    lea.l $0168(a6),a2
    bra.s h0_0CF6
h0_0CEC:
    lea.l $0160(a6),a2
    tst.l (a2)
    beq.w h0_8512
h0_0CF6:
    movea.l $0004(a2),a1
h0_0CFA:
    cmpi.w #152,$014E(a6)
    bcc.s h0_0D10
h0_0D02:
    movem.l d3/a0-a1,-(a7)
    jsr h0_9134.l
h0_0D0C:
    movem.l (a7)+,d3/a0-a1
h0_0D10:
    movea.l $0140(a6),a2
    move.l a2,(a1)
    movea.l a2,a1
    moveq.l #0,d0
    move.l d0,(a2)
    move.l d0,$0004(a2)
    move.l d4,$0008(a2)
    move.b d3,$000D(a2)
    move.w d0,$0014(a2)
    move.b d0,$000C(a2)
    move.b $014C(a6),$000E(a2)
    move.l d0,$0010(a2)
    lea.l $0016(a2),a2
    move.b $0005(a0),d0
    movea.l (a0),a0
    move.b d0,(a2)+
h0_0D46:
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s h0_0D46
h0_0D4C:
    move.l a2,d0
    sub.l a1,d0
    addq.l #1,d0
    bclr #0,d0
    sub.w d0,$014E(a6)
    add.l d0,$0140(a6)
    rts
h0_0D60:
    cmp.w $014E(a6),d0
    bcs.s h0_0D74
h0_0D66:
    movem.l d0/d3/a0-a1,-(a7)
    jsr h0_9134.l
h0_0D70:
    movem.l (a7)+,d0/d3/a0-a1
h0_0D74:
    move.l d0,-(a7)
    bsr.s h0_0CFA
h0_0D78:
    sub.l d0,$0140(a6)
    add.w d0,$014E(a6)
    move.l (a7)+,d0
    sub.w d0,$014E(a6)
    add.l d0,$0140(a6)
    rts
    DC.L    $226a0004,$0c6e0098,$014e640e,$48e710c0 ; VIOLATION: orphaned code island at $0D8C is not reached from known entrypoints
    DC.B    $4e,$b9
    DC.L    h0_9134
    DC.B    $4c,$df
    DC.L    $0308246e,$0140228a,$224a7000,$24802540,$00042544,$00081543,$000d3540,$00141540
    DC.L    $000c156e,$014c000e,$25400010,$45ea0016,$10280005,$205014c0,$14d85300,$66fa200a
    DC.L    $90895280,$08800000,$916e014e,$d1ae0140
    DC.B    $4e,$75
h0_0DF6:
    bsr.s h0_0E0C
h0_0DF8:
    cmp.b #$F,d3
    bcs.s h0_0E0A
h0_0DFE:
    cmp.b #$13,d3
    bcc.s h0_0E0A
h0_0E04:
    moveq.l #98,d0
    bra.w h0_8556
h0_0E0A:
    rts
h0_0E0C:
    bsr.w h0_7AB6
h0_0E10:
    lea.l $065E(a6),a0
    clr.w (a0)
    lea.l $0686(a6),a0
    clr.w (a0)
    moveq.l #0,d4
    movem.l d5-d7,-(a7)
    moveq.l #1,d5
    bsr.w h0_1262
h0_0E28:
    cmp.b #$1,d7
    bne.s h0_0E6C
h0_0E2E:
    movem.l d2-d3,-(a7)
    addq.b #1,d5
    bsr.w h0_1262
h0_0E38:
    cmp.b #$4,d7
    bcs.w h0_0E90
h0_0E40:
    cmp.b #$16,d7
    bcc.w h0_0E90
h0_0E48:
    lea.l $065E(a6),a0
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,$0(a0,d0.w)
    lea.l $0686(a6),a0
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l (a7)+,$0(a0,d0.w)
    move.l (a7)+,$4(a0,d0.w)
    bsr.w h0_0F1A
h0_0E6A:
    bra.s h0_0E7E
h0_0E6C:
    lea.l $065E(a6),a0
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,$0(a0,d0.w)
    bsr.w h0_0F4A
h0_0E7E:
    movem.l (a7)+,d5-d7
    tst.w $065E(a6)
    bne.s h0_0EA2
h0_0E88:
    tst.w $0686(a6)
    bne.s h0_0EA2
h0_0E8E:
    rts
h0_0E90:
    movem.l (a7)+,d2-d3
    movem.l (a7)+,d5-d7
    movea.l a0,a4
    move.b -$0001(a4),d1
    moveq.l #0,d0
    rts
h0_0EA2:
    moveq.l #18,d0
    bra.w h0_8552
    DC.L    $112b122d,$042a052f,$02280329,$137e083d,$0e26ea21,$105e0f7c,$fe24fa25,$f840f427
    DC.B    $f4,$22,$00
dat_0ECB:
    DC.B    $00
    DC.L    $00000004,$04161614,$14141414
    DC.B    $14,$12
    DC.W    h0_20F4-dat_0EE2
    DC.W    h0_10E4-dat_0EE2
    DC.W    h0_2C00-dat_0EE2
    DC.W    h0_2CE2-dat_0EE2
dat_0EE2:
    DC.W    h0_1134-dat_0EE2
    DC.W    h0_1152-dat_0EE2
    DC.W    h0_117A-dat_0EE2
    DC.W    h0_117E-dat_0EE2
    DC.W    h0_1182-dat_0EE2
    DC.W    h0_11AA-dat_0EE2
    DC.W    h0_11B0-dat_0EE2
    DC.W    h0_11B6-dat_0EE2
    DC.W    h0_11BC-dat_0EE2
    DC.W    h0_11C2-dat_0EE2
    DC.W    h0_116E-dat_0EE2
    DC.W    h0_1172-dat_0EE2
    DC.W    h0_1176-dat_0EE2
    DC.B    $01,$c8
    DC.W    h0_10F0-dat_0EE2
    DC.W    h0_11C8-dat_0EE2
    DC.W    h0_11D4-dat_0EE2
    DC.W    h0_11D2-dat_0EE2
h0_0F06:
    lea.l $065E(a6),a0
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,$0(a0,d0.w)
    moveq.l #1,d5
    bsr.w h0_1262
h0_0F1A:
    cmp.b #$2,d5
    bne.s h0_0F30
h0_0F20:
    cmp.b #$4,d7
    bcs.w h0_101E
h0_0F28:
    cmp.b #$16,d7
    bcc.w h0_101E
h0_0F30:
    cmp.b #$1,d7
    bne.s h0_0F4A
h0_0F36:
    lea.l $0686(a6),a0
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l d2,$0(a0,d0.w)
    move.l d3,$4(a0,d0.w)
    bra.w h0_1014
h0_0F4A:
    cmp.b #$2,d7
    beq.w h0_0FE4
h0_0F52:
    cmp.b #$4,d7
    bcs.w h0_1024
h0_0F5A:
    cmp.b #$16,d7
    bcc.w h0_1024
h0_0F62:
    cmp.b #$1,d5
    bne.s h0_0FBA
h0_0F68:
    cmp.b #$11,d7
    beq.s h0_0FB4
h0_0F6E:
    cmp.b #$12,d7
    beq.s h0_0FB8
h0_0F74:
    cmp.b #$4,d7
    beq.s h0_0F84
h0_0F7A:
    cmp.b #$13,d7
    bne.w h0_0EA2
h0_0F82:
    bra.s h0_0FBA
h0_0F84:
    move.l $026E(a6),d2
    moveq.l #0,d3
    move.b $0109(a6),d3
    cmp.b #$1,d3
    bne.s h0_0F98
h0_0F94:
    addq.b #1,$010C(a6)
h0_0F98:
    tst.b $00FF(a6)
    bne.s h0_0F36
h0_0F9E:
    tst.b $026A(a6)
    beq.s h0_0F36
h0_0FA4:
    moveq.l #0,d0
    move.b $014C(a6),d0
    lea.l $0180(a6),a0
    add.l $0(a0,d0.w),d2
    bra.s h0_0F36
h0_0FB4:
    moveq.l #21,d7
    bra.s h0_0FBA
h0_0FB8:
    moveq.l #20,d7
h0_0FBA:
    lea.l dat_0ECB(pc),a2
    lea.l $065E(a6),a0
    move.w (a0),d0
    move.w $0(a0,d0.w),d6
    move.b $0(a2,d6.w),d6
    cmp.b $0(a2,d7.w),d6
    bge.s h0_0FDA
h0_0FD2:
    addq.w #2,(a0)+
    move.w d7,$0(a0,d0.w)
    bra.s h0_0FE0
h0_0FDA:
    bsr.w h0_1054
h0_0FDE:
    bra.s h0_0FBA
h0_0FE0:
    moveq.l #0,d5
    bra.s h0_1014
h0_0FE4:
    bsr.w h0_0F06
h0_0FE8:
    bsr.w h0_1262
h0_0FEC:
    lea.l $0686(a6),a0
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l d2,$0(a0,d0.w)
    move.l d3,$4(a0,d0.w)
    tst.w d3
    bpl.s h0_1006
h0_1000:
    moveq.l #42,d0
    bsr.w h0_8556
h0_1006:
    cmp.b #$3,d7
    beq.s h0_1012
h0_100C:
    moveq.l #19,d0
    bra.w h0_8552
h0_1012:
    moveq.l #1,d5
h0_1014:
    addq.w #1,d5
    bsr.w h0_1262
h0_101A:
    bra.w h0_0F1A
h0_101E:
    movea.l a0,a4
    move.b -$0001(a4),d1
h0_1024:
    lea.l dat_0ECB(pc),a2
h0_1028:
    lea.l $065E(a6),a0
    move.w (a0),d0
    tst.w $0(a0,d0.w)
    beq.s h0_103A
h0_1034:
    bsr.w h0_1054
h0_1038:
    bra.s h0_1028
h0_103A:
    subq.w #2,$065E(a6)
    lea.l $0686(a6),a0
    subq.w #8,(a0)
    move.w (a0)+,d0
    move.l $0(a0,d0.w),d2
    move.l $4(a0,d0.w),d3
    rts
h0_1050:
    bra.w h0_0EA2
h0_1054:
    lea.l $0686(a6),a0
    subq.w #8,(a0)
    bcs.s h0_1050
h0_105C:
    move.w (a0)+,d0
    move.l $0(a0,d0.w),d2
    move.l $4(a0,d0.w),d3
    move.w d1,-(a7)
    lea.l $065E(a6),a1
    subq.w #2,(a1)
    move.w (a1)+,d1
    move.w $0(a1,d1.w),d1
    cmp.b #$13,d1
    bcc.s h0_108C
h0_107A:
    subq.w #8,-(a0)
    bcs.s h0_1050
h0_107E:
    move.w (a0)+,d0
    move.l $4(a0,d0.w),d6
    move.l $0(a0,d0.w),d0
    exg d0,d2
    exg d6,d3
h0_108C:
    lea.l dat_0EE2(pc),a1
    add.w d1,d1
    move.w -$8(a1,d1.w),d1
    jsr $0(a1,d1.w)
h0_109A:
    move.w (a7)+,d1
    move.w -(a0),d0
    addq.w #8,(a0)+
    move.l d2,$0(a0,d0.w)
    move.l d3,$4(a0,d0.w)
    rts
    DC.B    $d4,$80 ; VIOLATION: orphaned code island at $10AA is not reached from known entrypoints
    DC.L    $b63c0001,$670ebc3c,$0001670e,$0246ff00,$86464e75
    DC.B    $bc,$3c,$00,$01,$67,$06,$16,$3c,$00,$01,$60,$ec ; VIOLATION: orphaned code island at $10C0 is not reached from known entrypoints
h0_10CC:
    tst.b $0108(a6)
    bne.s h0_10E0
h0_10D2:
    tst.b $026A(a6)
    beq.s h0_10E4
h0_10D8:
    moveq.l #21,d0
h0_10DA:
    bsr.w h0_8556
h0_10DE:
    st.b d4
h0_10E0:
    moveq.l #2,d3
    rts
h0_10E4:
    tst.b $015E(a6)
    bne.s h0_10D8
h0_10EA:
    bra.s h0_10DE
h0_10EC:
    moveq.l #20,d0
    bra.s h0_10DA
h0_10F0:
    sub.l d0,d2
    move.w d3,d0
    or.w d6,d0
    andi.w #32768,d0
    tst.w d6
    bmi.s h0_112E
h0_10FE:
    cmp.b #$1,d6
    bne.s h0_111A
h0_1104:
    btst.b #1,$0250(a6)
    bne.s h0_1116
h0_110C:
    btst #15,d3
    beq.s h0_1116
h0_1112:
    add.l $026E(a6),d2
h0_1116:
    subq.b #2,$010C(a6)
h0_111A:
    cmp.b d3,d6
    beq.s h0_1126
h0_111E:
    cmp.b #$1,d6
    bne.s h0_112A
h0_1124:
    bsr.s h0_10CC
h0_1126:
    move.b #$2,d3
h0_112A:
    or.w d0,d3
    rts
h0_112E:
    bsr.w h0_7AF0
h0_1132:
    bra.s h0_111A
h0_1134:
    bsr.s h0_113E
h0_1136:
    bsr.w h0_11D8
h0_113A:
    moveq.l #2,d3
    rts
h0_113E:
    cmp.b #$1,d6
    beq.s h0_10CC
h0_1144:
    or.w d3,d6
    bmi.s h0_10EC
h0_1148:
    cmp.b #$1,d3
    beq.w h0_10CC
h0_1150:
    rts
h0_1152:
    bsr.s h0_113E
h0_1154:
    move.l d7,-(a7)
    bsr.w h0_120C
h0_115A:
    movem.l (a7)+,d7
    bne.s h0_1162
h0_1160:
    rts
h0_1162:
    tst.b $026A(a6)
    bne.w h0_10DA
h0_116A:
    bra.w h0_10E4
h0_116E:
    and.l d0,d2
    bra.s h0_113E
h0_1172:
    or.l d0,d2
    bra.s h0_113E
h0_1176:
    eor.l d0,d2
    bra.s h0_113E
h0_117A:
    lsl.l d0,d2
    bra.s h0_113E
h0_117E:
    lsr.l d0,d2
    bra.s h0_113E
h0_1182:
    cmp.l d0,d2
    seq.b d2
h0_1186:
    ext.w d2
    ext.l d2
    move.w d3,d0
    or.w d6,d0
    bmi.w h0_10EC
h0_1192:
    cmp.b d3,d6
    beq.s h0_11A6
h0_1196:
    cmp.b #$1,d3
    beq.w h0_10CC
h0_119E:
    cmp.b #$1,d6
    beq.w h0_10CC
h0_11A6:
    moveq.l #2,d3
    rts
h0_11AA:
    cmp.l d0,d2
    sne.b d2
    bra.s h0_1186
h0_11B0:
    cmp.l d0,d2
    slt.b d2
    bra.s h0_1186
h0_11B6:
    cmp.l d0,d2
    sgt.b d2
    bra.s h0_1186
h0_11BC:
    cmp.l d0,d2
    sle.b d2
    bra.s h0_1186
h0_11C2:
    cmp.l d0,d2
    sge.b d2
    bra.s h0_1186
h0_11C8:
    not.l d2
h0_11CA:
    cmp.w #$1,d3
    beq.w h0_10CC
h0_11D2:
    rts
h0_11D4:
    neg.l d2
    bra.s h0_11CA
h0_11D8:
    move.l d2,d6
    eor.l d0,d6
    tst.l d2
    bgt.s h0_11E2
h0_11E0:
    neg.l d2
h0_11E2:
    tst.l d0
    bgt.s h0_11E8
h0_11E6:
    neg.l d0
h0_11E8:
    move.l d2,d3
    swap.w d3
    mulu.w d0,d2
    swap.w d0
    tst.w d3
    beq.s h0_11F8
h0_11F4:
    swap.w d0
    bra.s h0_11FE
h0_11F8:
    tst.w d0
    beq.s h0_1204
h0_11FC:
    swap.w d3
h0_11FE:
    mulu.w d3,d0
    swap.w d0
    add.l d0,d2
h0_1204:
    tst.l d6
    bpl.s h0_120A
h0_1208:
    neg.l d2
h0_120A:
    rts
h0_120C:
    tst.l d0
    beq.s h0_125A
h0_1210:
    move.l d2,d6
    eor.l d0,d6
    move.l d6,-(a7)
    move.l d2,-(a7)
    tst.l d0
    bpl.s h0_121E
h0_121C:
    neg.l d0
h0_121E:
    tst.l d2
    bpl.s h0_1224
h0_1222:
    neg.l d2
h0_1224:
    moveq.l #31,d6
    move.l d0,d7
    moveq.l #0,d0
h0_122A:
    add.l d7,d7
    dbcs.w d6,h0_122A
h0_1230:
    roxr.l #1,d7
    subi.w #31,d6
    neg.w d6
h0_1238:
    add.l d0,d0
    cmp.l d7,d2
    bcs.s h0_1242
h0_123E:
    addq.l #1,d0
    sub.l d7,d2
h0_1242:
    lsr.l #1,d7
    dbf.w d6,h0_1238
h0_1248:
    move.l (a7)+,d6
    bpl.s h0_124E
h0_124C:
    neg.l d2
h0_124E:
    move.l (a7)+,d6
    bpl.s h0_1254
h0_1252:
    neg.l d0
h0_1254:
    exg d0,d2
    cmp.b d0,d0
    rts
h0_125A:
    moveq.l #61,d0
    rts
    DC.B    $20,$4c,$4e,$75 ; VIOLATION: orphaned code island at $125E is not reached from known entrypoints
h0_1262:
    moveq.l #0,d7
    ext.w d1
    bmi.s h0_128C
h0_1268:
    move.b dat_12AC(pc,d1.w),d7
    beq.s h0_127A
h0_126E:
    bpl.s h0_1280
h0_1270:
    cmp.b #$FF,d7
    bne.s h0_1296
h0_1276:
    bra.w h0_12A0
h0_127A:
    movea.l a4,a0
    moveq.l #22,d7
    rts
h0_1280:
    cmp.b #$1,d7
    beq.s h0_128C
h0_1286:
    movea.l a4,a0
    move.b (a4)+,d1
    rts
h0_128C:
    movem.l d5-d6/a1-a2,-(a7)
    move.l a4,-(a7)
    bra.w h0_132C
h0_1296:
    movem.l d5-d6/a1-a2,-(a7)
    move.l a4,-(a7)
    bra.w h0_1412
h0_12A0:
    movem.l d5-d6/a1-a2,-(a7)
    move.l a4,-(a7)
    moveq.l #0,d2
    bra.w h0_137E
dat_12AC:
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00eaf400,$fefa0ef4,$02030411,$00120105,$ffffffff,$ffffffff,$ffff0000,$f208ee00
    DC.L    $f8010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010100,$00001001
    DC.L    $00010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010100,$0f001300
h0_132C:
    lea.l $04A4(a6),a0
    bsr.w h0_7726
h0_1334:
    beq.w h0_158C
h0_1338:
    moveq.l #22,d7
    bra.s h0_1376
h0_133C:
    move.b (a4)+,d1
    cmp.b #$3D,d1
    beq.s h0_135A
h0_1344:
    moveq.l #15,d7
    bra.s h0_1376
h0_1348:
    moveq.l #10,d7
    move.b (a4)+,d1
    cmp.b #$3C,d1
    beq.s h0_1372
h0_1352:
    cmp.b #$3E,d1
    beq.s h0_135A
h0_1358:
    bra.s h0_1368
h0_135A:
    moveq.l #9,d7
    bra.s h0_1374
h0_135E:
    moveq.l #11,d7
    move.b (a4)+,d1
    cmp.b #$3E,d1
    beq.s h0_1372
h0_1368:
    cmp.b #$3D,d1
    bne.s h0_1376
h0_136E:
    addq.w #2,d7
    bra.s h0_1374
h0_1372:
    subq.w #4,d7
h0_1374:
    move.b (a4)+,d1
h0_1376:
    movea.l (a7)+,a0
    movem.l (a7)+,d5-d6/a1-a2
    rts
h0_137E:
    move.b $0131(a6),d7
    beq.s h0_138A
h0_1384:
    subq.l #1,a4
    bra.w h0_1412
h0_138A:
    lea.l -$0001(a4),a0
h0_138E:
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
    bcc.s h0_13B2
h0_13AC:
    cmp.b #$30,d1
    bcc.s h0_138E
h0_13B2:
    moveq.l #1,d7
    moveq.l #2,d3
    cmp.b #$24,d1
    bne.s h0_1376
h0_13BC:
    bra.w h0_16F2
h0_13C0:
    moveq.l #4,d0
    move.b d1,d3
h0_13C4:
    move.b (a4)+,d1
    cmp.b #$D,d1
    beq.w h0_148E
h0_13CE:
    cmp.b d3,d1
    bne.s h0_13DC
h0_13D2:
    move.b (a4)+,d1
    cmp.b d3,d1
    beq.s h0_13DC
h0_13D8:
    moveq.l #2,d3
    bra.s h0_1376
h0_13DC:
    subq.b #1,d0
    bcs.w h0_1498
h0_13E2:
    lsl.l #8,d2
    move.b d1,d2
    bra.s h0_13C4
h0_13E8:
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.w h0_148E
h0_13F2:
    cmp.b #$2,d1
    bcc.w h0_148E
h0_13FA:
    add.l d2,d2
    bcs.w h0_1498
h0_1400:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.s h0_1486
h0_140A:
    cmp.b #$2,d1
    bcs.s h0_13FA
h0_1410:
    bra.s h0_1486
h0_1412:
    neg.b d7
    ext.w d7
    moveq.l #0,d2
    moveq.l #2,d3
    moveq.l #1,d0
    exg d0,d7
h0_141E:
    jmp h0_1422-2(pc,d0.w) ; VIOLATION: invalid overlap: instruction bytes at +2 are referenced by reachable pc-relative operand | invalid overlap: pc-relative reference targets +2 into instruction at $141E
h0_1422:
    bra.w h0_1468
h0_1426:
    bra.s h0_13E8
h0_1428:
    bra.w h0_1440
h0_142C:
    bra.s h0_13C0
h0_142E:
    bra.w h0_1348
h0_1432:
    bra.w h0_135E
h0_1436:
    bra.w h0_133C
h0_143A:
    moveq.l #64,d1
h0_143C:
    bra.w h0_132C
h0_1440:
    move.b (a4),d0
    subi.b #48,d0
    bcs.s h0_143A
h0_1448:
    cmp.b #$9,d0
    bcc.s h0_143A
h0_144E:
    move.b d0,d1
    addq.l #1,a4
h0_1452:
    lsl.l #3,d2
    bcs.s h0_1498
h0_1456:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #48,d1
    bcs.s h0_1486
h0_1460:
    cmp.b #$9,d1
    bcs.s h0_1452
h0_1466:
    bra.s h0_1486
h0_1468:
    lea.l dat_149C(pc),a0
    moveq.l #0,d1
    move.b (a4)+,d1
    bmi.s h0_148E
h0_1472:
    move.b $0(a0,d1.w),d1
    bmi.s h0_148E
h0_1478:
    lsl.l #4,d2
    or.b d1,d2
    move.b (a4)+,d1
    bmi.s h0_1486
h0_1480:
    move.b $0(a0,d1.w),d1
    bpl.s h0_1478
h0_1486:
    move.b -$0001(a4),d1
    bra.w h0_1376
h0_148E:
    moveq.l #22,d0
h0_1490:
    bsr.w h0_8556
h0_1494:
    st.b d4
    bra.s h0_1486
h0_1498:
    moveq.l #23,d0
    bra.s h0_1490
dat_149C:
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$00010203,$04050607,$0809ffff,$ffffffff
    DC.L    $ff0a0b0c,$0d0e0fff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ff0a0b0c,$0d0e0fff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
h0_151C:
    movea.l (a0),a1
    subq.l #4,a7
    move.b (a1)+,$0002(a7)
    move.b (a1)+,$0003(a7)
    move.b (a1)+,(a7)
    move.b (a1)+,$0001(a7)
    move.l (a7)+,d0
    cmp.l #$52474E41,d0
    beq.s h0_157A
h0_1538:
    cmp.w #$5F5F,d0
    bne.s h0_1578
h0_153E:
    swap.w d0
h0_1540:
    cmp.w #$5253,d0
    beq.s h0_1572
h0_1546:
    cmp.w #$4732,d0
    beq.s h0_1564
h0_154C:
    cmp.w #$4C4B,d0
    beq.s h0_1554
h0_1552:
    bne.s h0_1578
h0_1554:
    moveq.l #0,d2
    tst.b $00FF(a6)
    beq.s h0_156E
h0_155C:
    move.w $0250(a6),d2
    addq.w #1,d2
    bra.s h0_156E
h0_1564:
    moveq.l #43,d2
    move.b $0123(a6),d0
    lsl.w #8,d0
    or.w d0,d2
h0_156E:
    moveq.l #0,d0
    rts
h0_1572:
    move.l $4704(a6),d2
    bra.s h0_156E
h0_1578:
    rts
h0_157A:
    moveq.l #0,d2
    tst.b $0102(a6)
    beq.s h0_1578
h0_1582:
    movea.l $473C(a6),a1
    move.w $0008(a1),d2
    bra.s h0_156E
h0_158C:
    moveq.l #1,d7
    seq.b $0004(a0)
    cmp.b #$23,d1
    bne.s h0_15A2
h0_1598:
    move.b (a4)+,d1
    tst.b $00FF(a6)
    sne.b $0004(a0)
h0_15A2:
    cmpi.b #4,$0005(a0)
    bne.s h0_15B6
h0_15AA:
    bsr.w h0_151C
h0_15AE:
    bne.s h0_15B6
h0_15B0:
    moveq.l #2,d3
    bra.w h0_1628
h0_15B6:
    tst.b $026A(a6)
    bne.w h0_166C
h0_15BE:
    bsr.w h0_0C0E
h0_15C2:
    beq.s h0_15CC
h0_15C4:
    moveq.l #0,d2
    st.b d4
    moveq.l #2,d3
    bra.s h0_1628
h0_15CC:
    move.l $0008(a1),d2
    moveq.l #0,d3
    move.b $000D(a1),d3
    btst.b #4,$000C(a1)
    bne.s h0_1630
h0_15DE:
    cmp.b #$2,d3
    beq.s h0_1628
h0_15E4:
    cmp.b #$E,d3
    beq.s h0_1628
h0_15EA:
    cmp.b #$1,d3
    beq.s h0_1652
h0_15F0:
    cmp.b #$F,d3
    bcs.s h0_1618
h0_15F6:
    cmp.b #$13,d3
    bcc.s h0_1618
h0_15FC:
    lea.l $472C(a6),a0
    move.l a0,d2
    move.l $0008(a1),(a0)+
    move.b $000E(a1),(a0)+
    move.b $000F(a1),(a0)+
    move.l $0010(a1),(a0)+
    move.w $0014(a1),(a0)
    bra.s h0_1628
h0_1618:
    cmp.b #$5,d3
    bne.w h0_171E
h0_1620:
    moveq.l #2,d3
    moveq.l #7,d0
    bsr.w h0_8660
h0_1628:
    move.b -$0001(a4),d1
    bra.w h0_1376
h0_1630:
    st.b d4
    swap.w d3
    move.w $0014(a1),d3
    bsr.w h0_7AC6
h0_163C:
    swap.w d3
    move.b -$0001(a4),d1
    tst.b $026A(a6)
    beq.w h0_1376
h0_164A:
    ori.w #32768,d3
    bra.w h0_1376
h0_1652:
    tst.b $00FF(a6)
    bne.s h0_165E
h0_1658:
    tst.b $000E(a1)
    beq.s h0_1628
h0_165E:
    move.b $014C(a6),d0
    cmp.b $000E(a1),d0
    beq.s h0_1628
h0_1668:
    st.b d4
    bra.s h0_1628
h0_166C:
    bsr.w h0_0C0E
h0_1670:
    sne.b d0
    move.b -$0001(a4),d1
    cmp.b #$23,d1
    bne.s h0_167E
h0_167C:
    move.b (a4)+,d1
h0_167E:
    tst.b d0
    bne.w h0_172C
h0_1684:
    btst.b #7,$000C(a1)
    beq.s h0_1696
h0_168C:
    btst.b #6,$000C(a1)
    beq.w h0_172C
h0_1696:
    move.l $0008(a1),d2
    moveq.l #0,d3
    move.b $000D(a1),d3
    tst.b $00FF(a6)
    bne.s h0_16C0
h0_16A6:
    cmp.b #$1,d3
    bne.w h0_15DE
h0_16AE:
    moveq.l #0,d0
    move.b $000E(a1),d0
    lea.l $0180(a6),a0
    add.l $0(a0,d0.w),d2
    bra.w h0_1376
h0_16C0:
    btst.b #4,$000C(a1)
    bne.w h0_1630
h0_16CA:
    cmp.b #$1,d3
    bne.w h0_15DE
h0_16D2:
    move.b $014C(a6),d0
    cmp.b $000E(a1),d0
    bne.s h0_16E4
h0_16DC:
    addq.b #1,$010C(a6)
    bra.w h0_1376
h0_16E4:
    ori.w #32768,d3
    st.b d4
    bsr.w h0_7ADC
h0_16EE:
    bra.w h0_1376
h0_16F2:
    movea.l a0,a1
    lea.l $04A4(a6),a0
    lea.l $0006(a0),a2
    move.l a2,(a0)
    sf.b $0004(a0)
    move.b $0118(a6),(a2)+
    move.l a4,d0
    sub.l a1,d0
    move.b d0,$0005(a0)
    subq.b #1,d0
h0_1710:
    move.b (a1)+,(a2)+
    subq.b #1,d0
    bne.s h0_1710
h0_1716:
    move.b (a4)+,d1
    moveq.l #1,d7
    bra.w h0_15B6
h0_171E:
    moveq.l #24,d0
h0_1720:
    moveq.l #2,d3
    st.b d4
    bsr.w h0_8556
h0_1728:
    bra.w h0_1376
h0_172C:
    moveq.l #3,d0
    bra.s h0_1720
h0_1730:
    bsr.w h0_0DF6
h0_1734:
    tst.b $00FF(a6)
    beq.s h0_173E
h0_173A:
    tst.w d3
    bmi.s h0_1752
h0_173E:
    cmp.b #$F,d3
    bcs.s h0_1750
h0_1744:
    cmp.b #$13,d3
    bcc.s h0_1750
h0_174A:
    moveq.l #98,d0
    bra.w h0_8556
h0_1750:
    rts
h0_1752:
    st.b d4
    moveq.l #20,d0
    bra.w h0_8556
h0_175A:
    bsr.s h0_1730
h0_175C:
    cmp.b #$1,d3
    bne.s h0_176A
h0_1762:
    tst.b $0108(a6)
    beq.w h0_8522
h0_176A:
    moveq.l #0,d0
    rts
    DC.B    $20,$57,$54,$97,$60,$06 ; VIOLATION: orphaned code island at $176E is not reached from known entrypoints
    DC.L    $20575497,$3ac63010,$3f000800,$00066708,$6100017a,$301f6006 ; VIOLATION: orphaned code island at $1774 is not reached from known entrypoints
    DC.L    $6100017e,$301f206e,$027e8b50,$ba3c0030,$6528ba3c,$003a6514,$ba3c003c,$67160805
    DC.L    $00066626,$08000006,$671a4e75 ; VIOLATION: orphaned code island at $178C is not reached from known entrypoints
    DC.B    $08,$00,$00,$05,$67,$12,$4e,$75 ; VIOLATION: orphaned code island at $17B8 is not reached from known entrypoints
    DC.B    $4a,$00,$6a,$0c,$4e,$75 ; VIOLATION: orphaned code island at $17C0 is not reached from known entrypoints
    DC.B    $14,$05,$e6,$0a,$05,$00,$67,$02,$4e,$75 ; VIOLATION: orphaned code island at $17C6 is not reached from known entrypoints
    DC.B    $70,$11,$60,$00,$6d,$82 ; VIOLATION: orphaned code island at $17D0 is not reached from known entrypoints
    DC.B    $02,$45 ; VIOLATION: orphaned code island at $17D6 is not reached from known entrypoints
    DC.L    $00bf3405,$e15ac042,$67ee205f,$4ee80002
    DC.B    $70,$25,$60,$00,$6d,$66 ; VIOLATION: orphaned code island at $17E8 is not reached from known entrypoints
    DC.B    $61,$1c,$66,$f6,$4a,$00,$66,$f2,$4e,$75 ; VIOLATION: orphaned code island at $17EE is not reached from known entrypoints
    DC.L    $6112660c,$4a006606,$70106100,$6d52b000,$4e7560f4,$1001204c,$48801036,$007eb03c
    DC.L    $00416728,$b03c0044,$6722b03c,$0052674a,$b03c0053,$6600007a,$10184880,$1036007e
    DC.L    $b03c0050,$666a7001,$74076014,$1418b43c,$0037625c,$04020030,$6556b03c,$004157c0
    DC.L    $02000001,$72001218 ; VIOLATION: orphaned code island at $17F8 is not reached from known entrypoints
    DC.B    $22,$7c
    DC.L    dat_B75C
    DC.B    $4a,$31
    DC.L    $1000673c,$2848b000,$4e751418,$b43c0039,$622eb43c,$00306528,$b43c0031,$66161010
    DC.L    $b03c0036,$640eb03c,$00306508,$0600000a,$14005288,$04020030,$b43c0008,$54c060b0
    DC.L    $41ee04a4,$48e70028,$122cffff,$61005e38
    DC.B    "f:$n"
    DC.L    $017048e7,$501c6100,$f3044cdf,$380a6628,$0c290004,$000d6620,$10290009,$1429000b
    DC.L    $4a2e026a,$67080829,$0006000c,$670a4cdf,$05002448,$b0004e75,$4cdf1400,$122cffff
    DC.L    $70ff4e75,$4a2e011b,$670650ee,$011c6004,$51ee011c,$6100fefa,$66187a00,$8a024a00
    DC.L    $670e0005,$00080c2e,$0001026b,$67006bf0
    DC.B    "Nu$L"
    DC.L    $b23c0028,$67000182,$b23c002d,$670001b6,$b23c0023,$670001d0,$48811236,$107eb23c
    DC.L    $00436742,$b23c0053,$6728b23c,$00556658,$121c4881,$1236107e,$b23c0053,$664a121c
    DC.L    $48811236,$107eb23c,$0050663c,$7a046000,$0438121c,$48811236,$107eb23c,$00526628
    DC.L    $7a026000,$0424121c,$48811236,$107eb23c,$00436614,$121c4881,$1236107e,$b23c0052
    DC.L    $66067a01,$60000402,$284a122c,$ffff6100,$f436b23c,$00286700,$01ceb23c,$002e6746
    DC.L    $b23c005c
    DC.B    "g@J."
    DC.L    $011e6652,$082e0002,$01116728,$3042b1c2,$66224a04,$661eb63c,$00016718,$6100745e
    DC.L    $66123ac2,$08c4000f,$6100007c,$7a38700d,$60006eac,$4a2e011c,$673e6000,$029c1014
    DC.L    $48801036,$007eb03c,$004c6722,$b03c0057,$6626528c,$121c7a38,$4a2e026a,$670c6100
    DC.L    $5eec0884,$000e6100,$003e3ac2,$4e75528c,$121c0884,$000f6004,$08c4000f
    DC.B    "z9J."
    DC.L    $026a671e,$4a2e00ff,$670a4a43,$6a064ef9
    DC.L    h0_9BB4
    DC.L    $6110b63c,$00016606
    DC.B    $4e,$b9
    DC.L    h0_9C8C
    DC.B    $2a,$c2
    DC.B    "NuJ."
    DC.L    $026d662c,$0c2e0001,$026b670c,$4a2e0121,$67060802,$0000661a,$0804000f,$6712b63c
    DC.L    $0002660c,$4a2e011f,$67067052,$61006aa8
    DC.B    "Nup#`",0
    DC.B    $6a,$a0
    DC.L    $121c4a2e,$01236600,$35486100,$fd346600,$fef01802,$b23c0029,$6710b23c,$002c6600
    DC.L    $6a5642a7,$76026000,$0124121c,$7a10b23c,$002b6604,$7a18121c,$8a044e75,$0c1c0028
    DC.L    $6600febe,$121c6100,$fcf86600,$feb4b23c,$00296600,$6a22121c,$7a208a02,$4e75121c
    DC.L    $6100f2dc,$7a3c102e,$026b672e,$53006748,$53006726,$4a2e026a,$671c4a2e,$00ff670a
    DC.L    $4a436a06
    DC.B    $4e,$f9
    DC.L    h0_9BB4
    DC.B    $b6,$3c
    DC.L    $00016606
    DC.B    $4e,$b9
    DC.L    h0_9C8C
    DC.B    $2a,$c2
    DC.B    "NuJ."
    DC.L    $026a6714,$4a2e00ff,$670a4a43,$6a064ef9
    DC.L    h0_9C2C
    DC.L    $61005da0,$3ac24e75,$4a2e026a,$67f64a2e,$00ff6704,$4a436b0c,$61005d78,$024200ff
    DC.L    $3ac24e75,$1afc0000
    DC.B    $4e,$f9
    DC.L    h0_9C6C
    DC.B    $12,$1c
    DC.L    $2f026100,$fc706600,$00e66100,$fc58b23c,$00296650,$082e0001,$01116724,$4a046620
    DC.L    $4a97661c,$7a108a02,$241f6100,$72906608,$121c700c,$60006ce8,$2f021405,$02020007
    DC.L    $7a288a02,$241f121c,$4a2e00ff,$670a4a43,$6a064ef9
    DC.L    h0_9BEC
    DC.L    $3ac24a2e,$026a6600
    DC.B    "],Nu"
    DC.L    $b23c002c,$66006930,$7a308a02,$121c6100,$fc006600,$691ee708,$8002e908,$48431600
    DC.L    $241fb23c,$002e6706,$b23c005c,$661c121c,$48811236,$107eb23c,$0057670c,$b23c004c
    DC.L    $660068f8,$00030008,$121c4a2e,$01236710,$b23c002a,$660a121c,$61003bd0,$d0008600
    DC.L    $b23c0029,$6600f3aa,$121c1ac3
    DC.B    "HCJ.",0
    DC.B    $ff,$67,$0a
    DC.L    $4a436a06
    DC.B    $4e,$f9
    DC.L    h0_9C4C
    DC.B    $1a,$c2
    DC.L    $4a2e026a,$66005c9c,$4e754881,$1236107e,$b23c0050,$6600689c,$121c4881,$1236107e
    DC.L    $b23c0043,$6600688c,$241f121c,$b23c0029,$665e121c
    DC.B    "z:J."
    DC.L    $026a6750,$4a2e00ff,$670a4a43,$6a064ef9
    DC.L    h0_9B94
    DC.L    $b63c0002,$672e0884,$000f6100,$fdaa94ae,$026e200d,$90ae027e,$94804a2e,$00ff660e
    DC.L    $7000102e,$014c41ee,$018094b0,$00003ac2,$60005c30,$4a2e0108,$66cc7021,$61006850
    DC.L    $3ac24e75,$b23c002c,$6600681c,$7a3b2f02,$121c6100,$faf06600,$680ee708,$8002e908
    DC.L    $1800b23c,$002e6706,$b23c005c,$661c121c,$48811236,$107eb23c,$0057670c,$b23c004c
    DC.L    $660067ec,$00040008,$121c241f,$4a2e0123,$6710b23c,$002a660a,$121c6100,$3ac2d000
    DC.L    $88001ac4,$4a2e026a
    DC.B    "g8J.",0
    DC.B    $ff,$67,$04
    DC.B    "JCk J."
    DC.B    $01,$08
    DC.L    $6606b63c,$0002671c,$94ae026e,$200d90ae,$027e9480,$52826100,$5b86600e
    DC.B    $4e,$b9
    DC.L    h0_9B74
    DC.B    $60,$08
    DC.L    $70216100,$67ae1ac2,$b23c0029,$6600f25a,$121c4e75,$7200121c
    DC.B    $22,$7c
    DC.L    dat_B75C
    DC.B    $4a,$31
    DC.L    $10006700,$fbf008c5
    DC.B    $00,$06
dat_1DCE:
    DC.B    $4e,$75
    DC.L    $61003226,$60046100,$06a06100,$fb301005,$02400078,$670cb03c,$00206600,$f9e40006
    DC.L    $00080245,$00078c45,$b23c002c,$66006734,$121c3f00,$6100fb06,$10050240,$0078b05f
    DC.L    $6600f9be,$02450007,$ee5d8c45,$3ac64e75,$121c6100,$efd2b23c,$002c6664,$4a046660
    DC.L    $b63c0002,$665ab4bc,$00000009,$64664a82,$6f62558d,$6100700e,$66440246,$40000846
    DC.L    $000eec4e,$00465000,$6100319e,$b43c0008,$66027400,$ee5a8c42,$121c6100,$f908003f
    DC.L    $4a2e026a,$670e7000,$102e026b,$103b000c,$d16e01c2,$700f6000,$6a2e0202,$0204548d
    DC.L    $121c6100,$fc886000,$00be0806,$000e66f0,$448260ec,$082e0001,$011067e4,$0806000e
    DC.L    $66024482,$3042b1c2,$66e048e7,$2200b23c,$002c6600,$666e121c,$6100312e,$48e74008
    DC.L    $6100f93a,$66000042,$4a006700,$003c558d,$61006f72
    DC.B    "f0POa",0
    DC.B    $fa,$30
    DC.L    $48823c3c,$41e88c42,$ee5a8c42,$3ac64cdf,$00443ac2,$70000c2e,$0003026b,$66027002
    DC.L    $d16e01c2,$70146000,$69a2544d,$4cdf1002,$4cdf0044,$0806000e,$66024482,$6000ff68
    DC.L    $548db23c,$00236614,$082e0004,$01116600,$fee4082e,$00010110,$6600feda,$6100f9b6
    DC.L    $b23c002c,$660065e0,$121c3f05,$6100f9b2,$381f206e,$027e1405,$02020078,$b43c0008
    DC.L    $6700004c,$b83c003c,$67306100,$30803086,$4a026610,$da058b18,$b83c0040,$6400f846
    DC.L    $89104e75,$10040200,$00786600,$f838d804,$52048918,$8b10703c,$6010ea5e,$02460700
    DC.L    $6100304a,$8c053086,$703d6000,$f7e00006,$00c08c04,$02450007,$ee5d8c45,$0c2e0003
    DC.L    $026b6604,$08c60008,$30863a04,$ba3c0040,$6400f7f2,$0c2e0001,$026b6700
    DC.B    "e2Nu"
    DC.L    $0c2e0003,$026b6604,$00460100,$6100f77a,$00ff48e7,$1800b23c,$002c6600,$652a121c
    DC.L    $6100f7ea,$4cdf0018,$6600f7ea,$d402206e,$027e8510,$61be082e,$00030110,$67424a04
    DC.L    $663eb63c,$00026638,$36100243,$01ffb67c,$01fc662c,$20280002,$3240b089,$662248e7
    DC.L    $80802400,$554d6100,$6e004cdf,$0101660e,$08900000,$31400002,$70166000
    DC.B    "hNTMNua",0
    DC.L    $2f883ac6,$b23c0023,$660064c0,$121c6100,$fa98b23c,$002c6600,$64aa121c,$6100f6e0
    DC.L    $003d4e75,$0c2e0014,$01236dd2,$61002f5a,$3ac6b23c,$00236600,$6492121c,$6100fa6a
    DC.L    $b23c002c,$6600647c,$121c6100,$f6b2007d,$4e75102e,$026b6700,$00e2b03c,$00016768
    DC.L    $b03c0002,$670000b4,$4a2e0126,$660000ac,$0c2e0014,$01236d42,$50c63ac6,$6100f642
    DC.L    $4a2e026a
h0_20F4:
    beq.s h0_2126
h0_20F6:
    tst.b d4
    bne.s h0_2126
h0_20FA:
    cmp.b #$2,d3
    bne.s h0_210C
h0_2100:
    tst.b $0108(a6)
    bne.s h0_210C
h0_2106:
    moveq.l #30,d0
    bsr.w h0_8556
h0_210C:
    sub.l $026E(a6),d2
    tst.b $00FF(a6)
    bne.s h0_2124
h0_2116:
    moveq.l #0,d0
    move.b $014C(a6),d0
    lea.l $0180(a6),a0
    sub.l $0(a0,d0.w),d2
h0_2124:
    subq.l #2,d2
h0_2126:
    move.l d2,(a5)+
    rts
    DC.B    $70,$05,$61,$00,$65,$32,$60,$58 ; VIOLATION: orphaned code island at $212A is not reached from known entrypoints
    DC.B    $70,$22,$60,$00,$64,$20 ; VIOLATION: orphaned code island at $2132 is not reached from known entrypoints
    DC.L    $610000e2,$6734e04e,$1ac64a2e,$00ff6706,$4a436b00,$7a284a82,$6630bc3c,$00616720
    DC.L    $082e0006,$01116608,$70536100,$63f26006 ; VIOLATION: orphaned code island at $2138 is not reached from known entrypoints
    DC.B    $70,$11,$61,$00,$67,$4a,$2a,$6e,$02,$7e,$3a,$fc,$4e,$71,$4e,$75 ; VIOLATION: orphaned code island at $2168 is not reached from known entrypoints
    DC.B    $1a,$fc,$00,$ff,$70,$3f,$60,$00,$63,$d6 ; VIOLATION: orphaned code island at $2178 is not reached from known entrypoints
    DC.B    $61,$00,$57,$9a,$1a,$c2,$4e,$75 ; VIOLATION: orphaned code island at $2182 is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $218A is not reached from known entrypoints
    DC.L    $00906716,$3ac64a2e,$00ff6706,$4a436b00,$79f86100,$578a3ac2
    DC.B    $4e,$75
    DC.B    $58,$8d,$4e,$75 ; VIOLATION: orphaned code island at $21A6 is not reached from known entrypoints
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $21AA is not reached from known entrypoints
    DC.L    $012e6b88,$6600ff2e,$082e0000,$011167ce,$6100ec38,$4a046652,$4a2e0108,$6606b63c
    DC.L    $00026746,$2f024a2e,$00ff6606,$4a2e014c,$663694ae,$026e5982,$672e6a02,$54821002
    DC.L    $488048c0,$b4806620,$61006c5e,$660c588f,$8c023ac6,$700b6000
    DC.B    $66,$b2
    DC.B    $08,$2e ; VIOLATION: orphaned code island at $2206 is not reached from known entrypoints
    DC.L    $00050111,$67067010,$610066a4,$241f487a,$ff766004
    DC.L    $6100ebd8,$4a2e026a,$66104a04,$6648b63c,$00026642,$4a2e0108 ; VIOLATION: orphaned code island at $221C is not reached from known entrypoints
    DC.B    "f<J.",0
    DC.B    $ff,$67,$04
    DC.B    "JCk2J."
    DC.B    $01,$08
    DC.L    $6606b63c,$0002672c,$08020000,$67067023,$61006300,$94ae026e,$4a2e00ff,$660e7000
    DC.L    $102e014c,$41ee0180,$94b00000,$55824a2e,$026a4e75
    DC.B    $70,$21,$61,$00,$62,$da,$4a,$2e,$02,$6a,$4e,$75 ; VIOLATION: orphaned code island at $2278 is not reached from known entrypoints
    DC.L    $b23c0023,$660062b0,$121c6100,$f4ca4a82,$6b0eb4bc,$00000008,$64068c02,$3ac64e75 ; VIOLATION: orphaned code island at $2284 is not reached from known entrypoints
    DC.B    $3a,$c6,$70,$1d,$60,$00,$62,$ac ; VIOLATION: orphaned code island at $22A4 is not reached from known entrypoints
    DC.L    $0c2e0014,$01236d00,$0fa40c2e,$00200123,$67000f9a,$4a2e026b,$66006254,$6100f524
    DC.L    $024200ff,$e85a3a02,$b23c002c,$66006258,$121c617e,$206e027e,$31450002 ; VIOLATION: orphaned code island at $22AC is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $22EA is not reached from known entrypoints
    DC.L    $00140123,$6d000f66,$0c2e0020,$01236700,$0f5c4a2e,$026b6600,$62163ac6,$548d6100
    DC.L    $f4620065,$7a006158,$b23c002c,$66006218,$121c6100,$f4ce0242,$00ffe85a,$8a42206e
    DC.L    $027e3145,$00024e75
    DC.L    $0c2e0014,$01236d00,$0f1c0c2e,$00200123,$67000f12,$4a2e026b,$660061cc,$7a00610a
    DC.L    $206e027e,$31450002 ; VIOLATION: orphaned code island at $2334 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $3a,$c6 ; VIOLATION: orphaned code island at $235E is not reached from known entrypoints
    DC.L    $548d3f05,$6100f408,$00253a1f,$b23c007b,$661a121c,$6100f496,$66184a00,$660e08c5
    DC.L    $000b0242,$00ffed4a,$8a426028
    DC.B    $70,$55,$60,$00,$61,$c2 ; VIOLATION: orphaned code island at $238C is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $2392 is not reached from known entrypoints
    DC.L    $f3c64a2e,$026a6718,$4a826b08,$b4bc0000,$00206504,$6100558a,$ed4a0242,$07c08a42
    DC.L    $b23c003a,$66d2121c,$6100f44e,$660c4a00,$66c608c5,$00058a02
    DC.B    $60,$22
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $23CE is not reached from known entrypoints
    DC.L    $f38a4a2e,$026a6718,$4a826606,$4a2e0122,$660e6f16,$b4bc0000,$00206704,$6e0c8a42
    DC.L    $b23c007d,$6696121c
    DC.B    $4e,$75
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $23FA is not reached from known entrypoints
    DC.L    $553860f0,$50ee026d,$b23c0023,$67226100,$f3e22f0c,$b23c002c,$6600611c,$121cd402
    DC.L    $52024267,$1ac21ac6,$6100f348,$00fd6020,$3ac6121c,$6100e9c4,$2f0c3f02,$6100f736
    DC.L    $b23c002c,$660060f0,$121c6100,$f326007d,$341f245f,$02450038,$66067003,$60000cc4
    DC.L    $b47c0008,$65164a2e,$01206710,$284a6a06,$706a6000,$60e67009,$610061ea,$70016000
    DC.L    $0ca250ee,$026db23c,$00236722,$6100f364,$2f0cb23c,$002c6600,$609e121c,$d4025202
    DC.L    $42671ac2,$1ac66100,$f2ca003d,$60a23ac6,$121c6100,$e9462f0c,$3f026100,$f6b8b23c
    DC.L    $002c6600,$6072121c,$6100f2a8,$003d6080,$0c2e0014,$01236600,$0d844a2e,$026b6704
    DC.L    $6100603c,$b23c0023,$66006054,$121c3ac6,$6100e908,$6100f67e,$b23c002c,$66006038
    DC.L    $121c6100,$f26e0064,$4e750c2e,$00140123,$6d000d4a,$0c2e0020,$01236700,$0d407000
    DC.L    $102e026b,$d0408c7b,$00366100,$f2c67a00,$1a02b23c,$002c6600,$5ffe121c,$6100f2b4
    DC.L    $024200ff,$ed4a8a42,$b23c002c,$66005fe8,$121c3f05,$6100f222,$003c3adf,$4e750400
    DC.L    $02000400,$06007056,$60005fec,$0c2e0014,$01236d00,$0ce80c2e,$00200123,$67000cde
    DC.L    $7000102e,$026bb03c,$00016700,$5f92b03c,$00036604,$08c60009,$3ac67a00,$7c006100
    DC.L    $f2528a02,$b23c003a,$66bc121c,$6100f244,$8c02b23c,$002c6600,$5f7e121c,$61308a42
    DC.L    $b23c003a,$66a0121c,$61000024,$8c42b23c,$002c6600,$5f62121c,$61208a42,$b23c003a
    DC.L    $6684121c,$61148c42,$3ac53ac6,$4e756100,$f2020242,$00ffed4a,$4e75b23c,$00286620
    DC.L    $121c6100,$f20c6618,$024200ff,$4a006704,$00020008,$e85ab23c,$00296604,$121c4e75
    DC.L    $60005ee4,$7e04b23c,$00236612,$121c6100,$f12e2e02,$b23c002c,$66005efc,$121cb23c
    DC.L    $00096758,$b23c0020,$6752b23c,$000d674c,$41ee04a4,$610050d4,$66005eac,$7c02b23c
    DC.L    $002e6620,$121c4881,$1236107e,$b23c0042,$6714b23c,$0057670e,$7c04b23c,$004c6600
    DC.L    $5e9e6002,$538c121c,$2807de86,$2f07610e,$2e1fb23c,$002c6604,$121c60b4
    DC.B    "NuJ."
    DC.L    $026a662a,$6100e56c,$67005e60,$76021028,$0006b02e,$01186708,$45ee0170,$6000e63c
    DC.L    $45ee0160,$4a926600,$e6c86000,$5e4a6100,$e5426600,$5e3a08e9,$0006000c,$66005e2c
    DC.L    $0c290002,$000d6600,$5e22b8a9,$00086600
    DC.B    "^",$22,"Nu"
    DC.L    $0c2e0014,$01236d00,$0158102e,$026b6712,$b03c0002,$670cb03c,$00036600,$5e0e0886
    DC.L    $00076100,$f06000fd,$b23c002c,$66005e14,$121c6100,$f0ca206e,$027ed402,$85104e75
    DC.L    $0c2e0014,$01236d00,$0b203a06,$0886000b,$7000102e,$026bd040,$8c7b002a,$3ac60245
    DC.L    $08003ac5,$6100f018,$0064b23c,$002c6600,$5dd2121c,$610023b8,$e902206e,$027e8528
    DC.L    $00024e75,$02000000,$02000400,$7a006004,$3a3c0800,$0c2e0014,$01236d00,$0acc6100
    DC.L    $fcc63ac6,$3ac56100,$efd600fd,$b23c002c,$66005d90,$121c6100,$f046206e,$027eb23c
    DC.L    $003a6616,$121c8528,$00036100,$f032206e,$027ee90a,$85280002
    DC.B    "Nup%`",0
    DC.B    $5d,$88
    DC.L    $0c2e0014,$01236d78,$102e026b,$6772b03c,$0002676c,$b03c0003,$66005d30,$08060008
    DC.L    $56c54885,$02450800,$0806000e,$57c64886,$02460040,$00464c00,$3ac63ac5,$6100ef60
    DC.L    $00fdb23c,$002c6600,$5d1a121c,$6100efd0,$206e027e,$b23c003a,$670c8528,$0003e90a
    DC.L    $85280002,$4e75121c,$85280003,$6100efb0,$206e027e,$e90a08c2,$00028528,$00024e75
    DC.L    $6100ef22,$00fdb23c,$002c6600,$5cd6121c,$6100ef8c,$206e027e,$d4028510,$70026000
    DC.L    $08ae6100,$27843ac6,$6100f086,$b23c002c,$66005cb0,$121c3f05,$6100f082,$381f206e
    DC.L    $027e3005,$02000078,$674ab03c,$00086754,$b83c003c,$67741004,$02000078,$b03c0018
    DC.L    $662e1005,$02000078,$b03c0018
    DC.B    "f",$22,"<<"
    DC.L    $b1086100,$27341004,$02000007,$8c001005,$02400007,$ee588c40,$206e027e,$30864e75
    DC.L    $6000eeee,$da058b10,$3a048b50,$303c00ff,$6000eea6,$02050007,$da050c2e,$0003026b
    DC.L    $66025205,$8b103a04,$004400c0,$8950303c,$00ff6100,$ee846000,$f6c83c3c,$0c006100
    DC.L    $26d88c45,$3086703d,$6000ee6e,$610026ca,$61168c05,$b23c002c,$66005bf8,$121c6108
    DC.L    $ee5d8c45,$3ac64e75,$6100efc2,$10050200,$0078b03c,$00186600,$ee780245,$00074e75
    DC.L    $610041cc,$b23c002c,$66005bc8,$121c2a02,$610041bc,$20026718,$6b3c2f02,$242e026e
    DC.L    $20176100,$e888241f,$4a806704,$90824480,$d0852800,$6710b0bc,$00000080,$64181afc
    DC.L    $00005300,$66f8d8ae,$026e41ee,$041e4a90,$6600e312,$4e75701d,$60005b9c,$43ecffff
    DC.L    $b23c000d,$671a121c,$b23c000d,$66f8240c,$94895342,$4a2e026a,$67066100,$6e9c720d
    DC.L    $4e756100,$ee0a8c02,$b23c002c,$66005b44,$121c6100,$fe786000,$f7923f01,$102e026b
    DC.L    $6706b03c,$00016710,$6100e29a,$102e026b,$66027002,$321f4e75,$41ee041e,$4a906708
    DC.L    $282e026e,$6100e29e,$102e026b,$60e661ca,$610040fc,$b23c002c,$67062f02,$74006008
    DC.L    $121c2f02,$610040e8,$760041fa,$017e2202,$162e026b,$16303000,$281f42ae,$01b04a2e
    DC.L    $01046706,$4a2e026a,$6616e7ac,$6a000008,$70546000,$5ade2d44,$01bc122c,$ffff4e75
    DC.L    $1d7c00ff,$46f52d6e,$026e46f6,$61006e7a,$67d842ae,$01bc5384,$65e0487a,$ffde5303
    DC.L    $652a6714,$2ac17a04,$613651cc,$fff80484,$00010000,$64ee4e75,$3ac17a02,$612251cc
    DC.L    $fff80484,$00010000,$64ee4e75,$1ac17a01,$610e51cc,$fff80484,$00010000,$64ee4e75
    DC.L    $2f012205,$242e026e,$d4ae01bc,$61006de0,$dbae01bc,$221f2a6e,$027e4e75,$6100fefc
    DC.L    $b03c0001,$67000048,$b03c0003,$671ab03c,$00026708,$610030ec,$611a60f8,$6100e2d8
    DC.L    $6100f030,$610e60f4,$6100e2cc,$6100effe,$610260f4,$b23c002c,$6610121c,$b23c0009
    DC.L    $67f8b23c,$002067f2,$4e75588f,$4e75b23c,$0027672a,$b23c0022,$67246100,$e29a4a2e
    DC.L    $026a670e,$4a2e00ff,$67044a43,$6b0a6100,$4d8a1ac2,$61be60d6,$610070f2,$60f61601
    DC.L    $48e7000c,$121cb23c,$000d6736,$b2036606,$121cb601,$66041ac1,$60eab23c,$000d671a
    DC.L    $b23c0009,$6714b23c,$0020670e,$b23c002c,$67084cdf,$30001203,$60a0508f,$6100ff76
    DC.L    $608c508f,$70376000,$598e0100,$01026100,$fe2a4880,$1c3b00f4,$61003f54,$4a82670a
    DC.L    $28021606,$72006000,$fe724e75,$50ee0117,$720d4e75,$41ee041e,$4a906702
    DC.B    "Nup)"
h0_2C00:
    bra.w h0_8552
    DC.L    $61ee4a2e,$026a6630,$2f086100,$3ef8205f,$48e73000,$6100dff4,$4cdf0030,$670058e4
    DC.L    $1605487a,$005e45ee,$01705505,$6700e0c4,$45ee0168,$6000e0bc ; VIOLATION: orphaned code island at $2C04 is not reached from known entrypoints
    DC.L    $6100dfd0,$660058dc,$08290006,$000c6600,$58ba2f09,$6100eade,$225fb63c,$00016614
    DC.L    $4a2e00ff,$660e7000,$102e014c,$41ee0180,$94b00000,$b4a90008,$66005898,$b629000d
    DC.L    $66005888,$08e90006,$000c122c,$ffff1d7c,$003d46f5,$2d4246f6 ; VIOLATION: orphaned code island at $2C3C is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $2C96 is not reached from known entrypoints
    DC.L    $ff5c2f0c,$2f0843ec,$ffff4eb9
    DC.L    h0_C03E
    DC.B    " _(I"
    DC.L    $121c6100,$ff56285f,$4a016602,$720d4e75
    DC.B    $70,$2e,$60,$00,$58,$96 ; VIOLATION: orphaned code island at $2CBC is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $2CC2 is not reached from known entrypoints
    DC.L    $ff306100,$eb4466f0,$48423400,$48420282,$00ff00ff,$246e0170,$41ee041e
    DC.B    $48,$e7
h0_2CE2:
    move.l (a4)+,d0
    tst.b $026A(a6)
    bne.s h0_2D00
h0_2CEA:
    bsr.w h0_0BC8
h0_2CEE:
    movem.l (a7)+,d4/a3-a5
    beq.w h0_8506
h0_2CF6:
    moveq.l #4,d3
    bsr.w h0_0CFA
h0_2CFC:
    moveq.l #13,d1
    rts
h0_2D00:
    bsr.w h0_0BC8
h0_2D04:
    movem.l (a7)+,d4/a3-a5
    bne.w h0_850A
h0_2D0C:
    cmpi.b #4,$000D(a1)
    bne.w h0_8506
h0_2D16:
    cmp.l $0008(a1),d4
    bne.w h0_8506
h0_2D1E:
    bset.b #6,$000C(a1)
    bne.w h0_8506
h0_2D28:
    moveq.l #13,d1
    rts
    DC.B    $4a,$2e,$02,$6b,$66,$00,$57,$e8,$32,$3c,$00,$0d,$4e,$75 ; VIOLATION: orphaned code island at $2D2C is not reached from known entrypoints
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $2D3A is not reached from known entrypoints
    DC.L    $f71a6100,$eacc6644,$b23c002c,$660057e8,$121c48a7,$a0006100,$eab84c9f,$0018662c
    DC.L    $b6006718,$00060088,$4a036702,$c9428c02,$02440007,$ee5c8c44,$3ac64e75
    DC.B    $00,$06,$00,$40,$4a,$00,$67,$ea,$00,$06,$00,$08,$c9,$42,$60,$e2 ; VIOLATION: orphaned code island at $2D78 is not reached from known entrypoints
    DC.B    $54,$8d,$70,$2e,$60,$00,$57,$c8 ; VIOLATION: orphaned code island at $2D88 is not reached from known entrypoints
    DC.L    $6100f24e,$0c2e0003,$026b6604,$00060040,$6100ea4c,$8c023ac6 ; VIOLATION: orphaned code island at $2D90 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $2DAA is not reached from known entrypoints
    DC.L    $00140123,$6d0004a6,$6100f6a0,$6100ea34,$8c023ac6
    DC.B    $4e,$75
    DC.B    $10,$2e ; VIOLATION: orphaned code island at $2DC2 is not reached from known entrypoints
    DC.L    $026b67f0,$b03c0002,$67eab03c,$00036600,$574608c6,$000660dc
    DC.B    $72,$0d,$70,$38,$60,$00,$57,$74 ; VIOLATION: orphaned code island at $2DDC is not reached from known entrypoints
    DC.L    $41ee4ade,$b23c000d,$673cb23c,$00096736,$b23c0020,$67300401,$0030652c,$b23c0008
    DC.L    $64267007,$9001121c,$b23c002b,$670ab23c,$002d6614,$01906002 ; VIOLATION: orphaned code island at $2DE4 is not reached from known entrypoints
    DC.L    $01d0121c,$b23c002c,$6604121c,$60be4e75,$704c6000,$57266100,$3cfa4a82,$6700de4a
    DC.L    $b23c0009,$6706b23c,$00206604,$121c60f0,$6100dc2a,$41fa0008,$2d4801a8,$720d4e75
    DC.L    $4a2e011d,$660056c8,$41ee041e,$76006100,$4a1a41ee,$0424422e,$010b4eb9 ; VIOLATION: orphaned code island at $2E1C is not reached from known entrypoints
    DC.L    h0_BF9A
    DC.L    $66000086,$2d4301b8,$2d4201bc,$6768b4bc,$ffffffff
    DC.B    "f* n"
    DC.L    $01d02228,$00242068,$00209288,$2d4101bc,$4a2e026a
    DC.B    "gHJ."
    DC.L    $01046742,$242e026e,$61006ab2,$60000038,$4a2e026a
    DC.B    "g0J."
    DC.L    $0104672a,$22026100,$627a2f08,$222e01bc,$262e01b8
    DC.B    $4e,$b9
    DC.L    h0_BFB2
    DC.B    $22,$2e
    DC.L    $01bc2057,$242e026e,$61006a7e,$205f6100
    DC.B    "bj&."
    DC.L    $01b842ae,$01b84eb9
    DC.L    h0_BFAE
    DC.L    $720d4e75,$701a6000,$564e47ee,$086850ee,$012d6000,$186641ee,$041e760b,$61004968
    DC.L    $50ee010b,$610059de,$66005614,$720d4e75,$6100e842,$00644a2e,$026b6600,$55de4e75
    DC.L    $50ee026d,$6100e82e,$006451ee,$026db23c,$002c6600,$55de48e7,$1800121c,$6100e8ae
    DC.L    $4cdf0018,$6600e89a,$4a006700,$e894206e,$027ed402,$85106100,$f4de082e,$00020110
    DC.L    $676a4a04,$6666b63c,$00026660,$36100243,$0038b63c,$00286654,$30280002,$674eb07c
    DC.L    $00086e48,$b07cfff8,$6d423610,$02430007,$d643b403,$663648e7,$80802400,$554d6100
    DC.L    $5e944cdf,$01016622,$e24b4a40,$6a0608c3,$00084440,$02400007,$ee588640,$00435048
    DC.L    $30837015,$600058d0
    DC.B    "NuTMNu"
    DC.B    $0c,$2e
    DC.L    $00140123,$6d48102e,$026b674a,$b03c0002,$6744b03c,$00036600,$55123c3c,$48086100
    DC.L    $e7e88c02,$3ac6b23c,$002c6600,$5516121c,$b23c0023,$66005514,$121c6100,$ddca6100
    DC.L    $eafc0802,$0000663e,$4a826e3a
    DC.B    "NuJ."
    DC.L    $026b6600,$54d66100,$e7b08c02,$3ac6b23c,$002c6600,$54de121c,$b23c0023,$660054dc
    DC.L    $121c6100,$dd926100,$eaea0802,$00006606,$4a426e02,$4e757003,$600055e6,$121c6100
    DC.L    $e6da6100
    DC.B    "HvJ."
    DC.L    $026a6710,$4a2e480f,$670a3f01,$12026100,$6170321f,$b23c002c,$67da50ee,$01154e75
    DC.L    $61003a84,$b4bc0000,$00266500,$1842b4bc,$000000ff,$64001838,$3d424a1c,$50ee0115
    DC.L    $4e75b23c,$00236600,$546a121c,$61001f22,$3ac66100,$ea3cb23c,$002c6600,$544e121c
    DC.L    $6100e684,$033d4e75,$206e027e,$52885305,$67144a2e,$01276706,$70656100,$545210bc
    DC.L    $007c7002,$601010fc,$003c0c2e,$0003026b,$67005400,$4e75b02e,$026b670c,$4a2e026b
    DC.L    $660053f0,$1d40026b,$4e75121c,$30063c3c,$0200b07c,$c0006794,$7c00b07c,$8000678c
    DC.L    $3c3c0a00,$6086b23c,$002367de,$61001ea2,$3ac66100,$e7a4b23c,$002c6600,$53ce121c
    DC.L    $10050200,$00786600,$0042da05,$52058b2d,$fffe6100,$e790206e,$027e303c,$003c1405
    DC.L    $02020078,$661e303c,$00fd0806,$000d6614,$1010e208,$02400007,$8150da05,$0250f0ff
    DC.L    $8b104e75,$8b506000,$e5e80806,$000d6600,$e618303c,$00fd6100,$e5d26100,$e62a206e
    DC.L    $027ed402,$85104e75,$224c41fa,$00b44881,$1236107e,$b2186600,$008a121c,$4a1066ee
    DC.L    $04010030,$656ab23c,$000a6464,$74001401,$c4fc000a,$121c0401,$00306554,$b23c000a
    DC.L    $644e4881,$d441121c,$c4fc000a,$04010030,$653eb23c,$000a6438,$4881d441,$121c4a42
    DC.L    $6736b47c,$0008672e,$b47c000a,$672ab47c,$00146724,$b47c001e,$671eb47c,$014c673c
    DC.L    $b47c0028,$660a1d42,$012350ee,$01244e75
h0_3258:
    DC.L    $70226000,$52fa7400,$1d420123,$51ee0124
    DC.B    "Nu(I"
    DC.L    $122cffff,$41fa001b,$48811236,$107eb218,$66da121c,$4a1066f0,$742060d8
    DC.B    "MC68",0
    DC.B    "CPU32",0
    DC.B    $00
h0_3294:
    moveq.l #0,d2
h0_3296:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.s h0_32BA
h0_329E:
    cmp.b #$3A,d1
    bcc.s h0_32BA
h0_32A4:
    subi.b #48,d1
    ext.w d1
    ext.l d1
    add.l d2,d2
    move.l d2,d0
    add.l d2,d2
    add.l d2,d2
    add.l d0,d2
    add.l d1,d2
    bra.s h0_3296
h0_32BA:
    subi.l #68000,d2
    bcs.s h0_3302
    beq.s h0_3324
    cmp.l #$384,d2
    bgt.s h0_3302
    cmp.w #$8,d2
    beq.s h0_3324
    cmp.w #$A,d2
    beq.s h0_3324
    cmp.w #$14,d2
    beq.s h0_3324
    cmp.w #$1E,d2
    beq.s h0_3324
    cmp.w #$14C,d2
    beq.s h0_3304
    cmp.w #$28,d2
    beq.s h0_331E
    cmp.w #$371,d2
    beq.s h0_3316
    cmp.w #$372,d2
    beq.s h0_330E
    cmp.w #$353,d2
    beq.s h0_3308
h0_3302:
    rts
h0_3304:
    DC.L    $7420601c ; VIOLATION: orphaned code island at $3304 is not reached from known entrypoints
h0_3308:
    DC.B    $50,$ee,$01,$25,$60,$1e ; VIOLATION: orphaned code island at $3308 is not reached from known entrypoints
h0_330E:
    DC.B    $1d,$7c,$00,$52,$01,$24,$60,$16 ; VIOLATION: orphaned code island at $330E is not reached from known entrypoints
h0_3316:
    DC.B    $1d,$7c,$00,$51,$01,$24,$60,$0e ; VIOLATION: orphaned code island at $3316 is not reached from known entrypoints
h0_331E:
    DC.B    $50,$ee,$01,$24,$60,$04 ; VIOLATION: orphaned code island at $331E is not reached from known entrypoints
h0_3324:
    DC.L    $51ee0124,$1d420123,$b23c002f,$6700ff62,$70004e75,$61001cbe,$b23c0023,$660051f8
    DC.L    $121c6100,$e4126116,$ee5a8c42,$b23c002c,$660051dc,$121c6100,$e418003f ; VIOLATION: orphaned code island at $3324 is not reached from known entrypoints
    DC.B    "NuJ."
    DC.L    $026a6710,$4a82670e,$b4bc0000,$0008620c,$66027400
    DC.B    "NuJ."
    DC.L    $012266f8,$701d6000,$51d26100,$1b60342e,$02500802,$00016622,$b47c0005,$671c4a42
    DC.L    $66126100,$46b0204c,$122cffff,$610045ac,$720d4e75,$70066000,$52ac45ee,$01e26100
    DC.L    $1ad451ee,$01154e75,$121c6100,$da2e4a04,$66000082,$b63c0002,$667ab23c,$002c6674
    DC.L    $28022f0c,$121c6100,$e4286662,$4a006630,$20044880,$48c0b880,$6654082e,$00030111
    DC.L    $6700004c,$558d6100
    DC.B    "ZPf@X"
    DC.B    $8f,$00,$02
    DC.L    $0038d402,$e14a8404,$3ac2700e,$6000549c,$3044b888,$6628082e,$00030110,$67000020
    DC.L    $558d6100,$5a246614,$588fd402,$e14a0042,$307c3ac2,$3ac47016,$60005470,$548d285f
    DC.L    $722c2404,$6100e6ca,$603a3000,$10003000,$20007000,$102e026b,$d0008c7b,$00ee3ac6
    DC.L    $b03c0006,$661ab23c,$00236614,$082e0003,$01116600,$ff44082e,$00030110,$6600ff3a
    DC.L    $6100e472,$b23c002c,$6600509c,$121c0805,$00066600,$00ac206e,$027e8b50,$6100e462
    DC.L    $206e027e,$08050006,$66263405,$30050200,$0007d000,$81100245,$0038da45,$da45da45
    DC.L    $8b500242,$003fb47c,$003a6400,$e2f84e75,$3810e20d,$652ce20d
    DC.B    "ePJ."
    DC.L    $01276706,$70656100,$50661004,$02000038,$b03c0008,$6600e2d2,$02440007,$00444e60
    DC.L    $30846000,$ef4a3c3c,$44c00c2e,$0003026b,$66046100,$4ffe0244,$003f1004,$02000038
    DC.L    $b03c0008,$6700e2a2,$8c443086
    DC.B    "NuJ."
    DC.L    $01276706,$70656100,$50166100,$f3283c3c,$46c060d2,$246e027e,$e20d653a,$e20d651c
    DC.L    $4a2e0127,$67067065,$61004ff4,$6100e292
    DC.B    "<<Nh"
    DC.L    $8c023486,$6000eee4,$4a2e0127,$67067065,$61004fd8,$34bc40c0,$6100e1e8,$003d6000
    DC.L    $f2e04a2e,$01236608,$61ea7004,$600050c6,$34bc42c0,$6100e1cc,$003d0c2e,$0003026b
    DC.L    $67004f6c
    DC.B    "NuJ."
    DC.L    $01236700,$fca04a2e,$01276706,$70656100,$4f926100,$ee8e6100,$e2406626,$b23c002c
    DC.L    $66004f5c,$121c3afc,$4e7be708,$84000242,$000fe85a,$36026136,$66004f40,$84433ac2
    DC.B    "Nua*f",0
    DC.B    $4f,$34
    DC.L    $b23c002c,$66004f30,$121c3602,$6100e202,$66004f20,$3ac6e708,$84000242,$000fe85a
    DC.L    $86423ac3,$4e751001,$48801036,$007e41fa,$00807400,$14186774,$b010666a,$48e7a088
    DC.L    $5288101c,$48801036,$007eb018,$66545302,$66f04fef,$00101418,$e14a1418,$121c102e
    DC.L    $01236718,$b03c0028,$671cb03c,$00206706,$b03c000a,$6618b43c,$00026506,$70226100
    DC.L    $4eda7000,$4e75b47c,$080266f6,$60eeb47c,$080564e8,$b47c0800,$64e8b47c,$000365e2
    DC.L    $60da4cdf,$110541f0,$20036088,$70ff4e75,$02534643,$00000244,$46430001,$03434143
    DC.L    $52000202,$55535008,$00025642,$52080103
    DC.B    "CAAR"
    DC.L    $0802024d,$53500803,$02495350,$08040154,$43000303
    DC.B    "ITT0",0
    DC.B    $04,$03
    DC.B    "ITT1",0
    DC.L    $05034454,$54300006,$03445454,$31000704
    DC.B    "MMUSR"
    DC.B    $08,$05,$02
    DC.L    $55525008,$06025352,$50080700,$102e026b,$6712b03c,$0002670c,$b03c0003,$66004df4
    DC.L    $00060040,$61726600,$004ab23c,$002c6600,$4dfa121c,$3ac63ac4,$6100e1ca,$ba7c0040
    DC.L    $6400e086,$14050202,$0038b43c,$0020661c,$4a2e026a,$6716206e,$027e2010,$7400760f
    DC.L    $e348e252,$51cbfffa,$31420002,$70346000,$e01a0046,$04003ac6,$548d6100,$dfea006c
    DC.L    $b23c002c,$66004da4,$121c610c
    DC.B    "fx n"
    DC.L    $027e3144,$00024e75,$78006100,$e0686748,$41ee04a4,$48e74008,$61003f74
    DC.B    "f4$n"
    DC.L    $017048e7,$501c6100,$d4084cdf,$380a6622,$0c290005,$000d661a,$28290008,$4a2e026a
    DC.L    $67080829,$0006000c,$6706508f,$70004e75,$70ff4cdf,$10024e75,$e708d002,$b23c002d
    DC.L    $671a01c4,$b23c002f,$67047000,$4e75121c,$6100e002,$67e27039,$60004d40,$121cb23c
    DC.L    $00386416,$b23c0030,$65101600,$02000008,$04010030,$d001121c,$600e3f00,$6100dfd6
    DC.L    $66d4e708,$d002361f,$b00365ca,$520007c4,$5203b600,$66f860ac,$6100df22,$00ff48e7
    DC.L    $1800b23c,$002c6600,$4cd2121c,$6100df92,$4cdf0018,$d402206e,$027e8510,$102e026b
    DC.L    $670eb03c,$0003670e,$b03c0002,$66004c94,$00100010,$4e75082e,$00030110,$67424a04
    DC.L    $663eb63c,$00026638,$36100243,$003fb63c,$003c662c,$20280002,$3240b089,$662248e7
    DC.L    $80802400,$554d6100,$55944cdf,$0101660e,$00100010,$31400002,$70166000,$4fe2544d
    DC.L    $4e75102e,$026bb03c,$00016700,$4c36b03c,$00036604,$00060040,$6100df1a,$66244a00
    DC.L    $6600003a,$00060080,$02420007,$ee5a8c42,$b23c002c,$66004c24,$121c6126,$3ac63ac3
    DC.L    $4e75611e,$b23c002c,$66004c10,$121c6100,$dec60242,$0007ee5a,$8c4260e0,$702f6000
    DC.L    $4c1e7400,$0c2e0014,$01236d3a,$b23c0028,$663a121c,$36026100,$dea86616,$8c02b23c
    DC.L    $002c6640,$121c6100,$ddd06100,$3fc03602,$60326100,$ddc46100,$3fb43602,$b23c002c
    DC.L    $66ba6000,$0016b23c,$0028670e,$6100ddaa,$61003f9a,$b23c0028,$66a2121c,$36026100
    DC.L    $de608c02,$b23c0029,$6692121c,$4e75b23c,$00236600,$4b8e121c,$6100d444,$4a2e026a
    DC.L    $67346100,$3f8a4a2e,$00ff6704
    DC.B    "JCkB"
    DC.L    $10024880,$48c0b480,$671cb4bc,$00000100,$65066100,$4b4a600e,$0c2e0003,$026b6706
    DC.L    $70016100,$4c741c02,$b23c002c,$66004b3c,$121c6100,$ddf2d402,$70708002,$1ac01ac6
    DC.L    $4e752f02,$b23c002c,$66004b20,$121c6100,$ddd6d402,$70708002,$1ac0241f,$60006246
    DC.L    $0c2e000a,$01236d00,$f8284a2e,$01276706,$70656100,$4b1a6100,$15b83ac6,$6100ddc6
    DC.L    $66187601,$613c3ac3,$b23c002c,$66004adc,$121c6100,$dd12003c,$4e75548d,$6100dd08
    DC.L    $003cb23c,$002c6600,$4ac2121c,$6100dd96,$6600f242,$7600610a,$206e027e,$31430002
    DC.L    $4e75d402,$4a0056c0,$02000010,$86008602,$ea5b4e75,$6100e9da,$6100dcd2,$003d4e75
    DC.L    $b23c0009,$6706b23c,$00206604,$121c60f0,$7400b23c,$000d6710,$b23c002a,$670ab23c
    DC.L    $003b6704,$61003060,$2f026100,$3f6e241f,$43ee0288,$2d490148,$23420008,$4229000e
    DC.L    $2d42026e,$41ee05de,$2d48027e,$1d7c0002,$010950ee,$011d122c
    DC.B    $ff,$ff
h0_3B02:
    rts
    DC.L    $61003028,$2f026100,$61d64cdf,$00046630,$2d42026e,$41fa5fca,$2d4801a8,$122cffff
    DC.L    $50ee0114,$51ee011e,$1d7c000e,$0109102e,$026b670a,$b03c0003,$670450ee,$011e4e75 ; VIOLATION: orphaned code island at $3B04 is not reached from known entrypoints
    DC.B    $70,$45,$60,$00,$4a,$0e ; VIOLATION: orphaned code island at $3B44 is not reached from known entrypoints
h0_3B4A:
    move.b (a4)+,d1
    beq.s h0_3B6E
h0_3B4E:
    cmp.b #$20,d1
    beq.s h0_3B4A
h0_3B54:
    cmp.b #$D,d1
    beq.s h0_3B6E
h0_3B5A:
    cmp.b #$2B,d1
    beq.s h0_3B70
h0_3B60:
    cmp.b #$2D,d1
    bne.w h0_3B76
h0_3B68:
    bsr.w h0_3C7C
h0_3B6C:
    beq.s h0_3B4A
h0_3B6E:
    rts
h0_3B70:
    bsr.w h0_3F62
h0_3B74:
    bra.s h0_3B4A
h0_3B76:
    tst.b $4EF0(a6)
    beq.s h0_3B9E
h0_3B7C:
    movem.l d1/a4,-(a7)
    ext.w d1
    move.b $7E(a6,d1.w),d1
    bsr.w h0_3FA0
h0_3B8A:
    beq.s h0_3B9A
h0_3B8C:
    bpl.s h0_3B94
h0_3B8E:
    tst.b $46FB(a6)
    beq.s h0_3B96
h0_3B94:
    jsr (a0)
h0_3B96:
    addq.w #8,a7
    bra.s h0_3BA2
h0_3B9A:
    movem.l (a7)+,d1/a4
h0_3B9E:
    bsr.w h0_3BA6
h0_3BA2:
    subq.w #1,a4
    bra.s h0_3B4A
h0_3BA6:
    tst.b $46FA(a6)
    beq.w h0_4406
h0_3BAE:
    lea.l $0750(a6),a1
    lea.l $0530(a6),a2
    move.l a2,$052A(a6)
    clr.b $052F(a6)
    lea.l $4EFE(a6),a3
    moveq.l #0,d2
    cmp.b #$22,d1
    bne.s h0_3BD2
h0_3BCA:
    move.b d1,d2
    move.b (a4)+,d1
    beq.w h0_3DC8
h0_3BD2:
    moveq.l #0,d3
h0_3BD4:
    move.b d1,(a2)+
    move.b d1,(a1)+
    move.b d1,(a3)+
    addq.b #1,$052F(a6)
    move.b (a4)+,d1
    beq.s h0_3C0A
h0_3BE2:
    cmp.b #$D,d1
    beq.s h0_3C0A
h0_3BE8:
    cmp.b #$20,d1
    beq.s h0_3C06
h0_3BEE:
    cmp.b #$2F,d1
    beq.s h0_3BD2
h0_3BF4:
    cmp.b d1,d2
    beq.s h0_3C02
h0_3BF8:
    cmp.b #$2E,d1
    bne.s h0_3BD4
h0_3BFE:
    move.l a1,d3
    bra.s h0_3BD4
h0_3C02:
    move.b (a4)+,d1
    bra.s h0_3C0A
h0_3C06:
    tst.b d2
    bne.s h0_3BD4
h0_3C0A:
    tst.l d3
    bne.s h0_3C1E
h0_3C0E:
    clr.b (a1)
    move.b #$2E,(a2)+
    move.b #$73,(a2)+
    addq.b #2,$052F(a6)
    bra.s h0_3C28
h0_3C1E:
    movea.l d3,a1
    clr.b (a1)
    lea.l $47AE(a1),a1
    clr.b (a1)
h0_3C28:
    move.b #$B,(a2)
    addq.b #1,$052F(a6)
    clr.b (a3)
    lea.l $4EFE(a6),a0
    bsr.w h0_3C4E
h0_3C3A:
    move.l a0,$4EFA(a6)
    lea.l $07A2(a6),a3
h0_3C42:
    move.b (a0)+,(a3)+
    bne.s h0_3C42
h0_3C46:
    movea.l $4EFA(a6),a0
    clr.b (a0)
    rts
h0_3C4E:
    moveq.l #0,d0
    movea.l a0,a1
h0_3C52:
    move.b (a0)+,d1
    beq.s h0_3C6C
h0_3C56:
    cmp.b #$5C,d1
    beq.s h0_3C68
h0_3C5C:
    cmp.b #$2F,d1
    beq.s h0_3C68
h0_3C62:
    cmp.b #$3A,d1
    bne.s h0_3C52
h0_3C68:
    move.l a0,d0
    bra.s h0_3C52
h0_3C6C:
    tst.l d0
    bne.s h0_3C76
h0_3C70:
    movea.l a1,a0
    moveq.l #-1,d0
    rts
h0_3C76:
    movea.l d0,a0
    moveq.l #0,d0
    rts
h0_3C7C:
    move.b (a4)+,d1
    beq.s h0_3C8C
h0_3C80:
    cmp.b #$20,d1
    beq.s h0_3C8C
h0_3C86:
    cmp.b #$D,d1
    bne.s h0_3C90
h0_3C8C:
    moveq.l #0,d0
    rts
h0_3C90:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$5B,d1
    bcc.s h0_3CBA
h0_3C9C:
    subi.b #65,d1
    bcs.s h0_3CAE
h0_3CA2:
    add.b d1,d1
    ext.w d1
    lea.l dat_3CBE(pc,d1.w),a2
    adda.w (a2),a2
    jmp (a2)
h0_3CAE:
    addi.b #65,d1
    cmp.b #$2E,d1
    beq.w h0_3D42
h0_3CBA:
    bra.w h0_3DC8
dat_3CBE:
    DC.W    h0_3DC8-*
dat_3CC0:
    DC.W    h0_3D32-*
dat_3CC2:
    DC.W    h0_3D08-*
    DC.B    $00,$50
dat_3CC6:
    DC.W    h0_3ED0-*
dat_3CC8:
    DC.W    h0_3DC8-*
dat_3CCA:
    DC.W    h0_3D48-*
dat_3CCC:
    DC.W    h0_3E30-*
dat_3CCE:
    DC.W    h0_3E12-*
dat_3CD0:
    DC.W    h0_3DC8-*
dat_3CD2:
    DC.W    h0_3DC8-*
    DC.B    $00,$88
dat_3CD6:
    DC.W    h0_3D2C-*
dat_3CD8:
    DC.W    h0_3DC8-*
dat_3CDA:
    DC.W    h0_3E40-*
    DC.B    $01,$a8
dat_3CDE:
    DC.W    h0_3D0E-*
dat_3CE0:
    DC.W    h0_3DC8-*
    DC.B    $00,$14
dat_3CE4:
    DC.W    h0_3DCC-*
dat_3CE6:
    DC.W    h0_3DC8-*
dat_3CE8:
    DC.W    h0_3F62-*
dat_3CEA:
    DC.W    h0_3E3A-*
dat_3CEC:
    DC.W    h0_3D26-*
dat_3CEE:
    DC.W    h0_3DC8-*
dat_3CF0:
    DC.W    h0_3DC0-*
    DC.B    $70,$00
    DC.L    $4e7543ee
dat_3CF8:
    DC.W    h0_3DFE-6-*
h0_3CFA:
    tst.b $46FA(a6)
    beq.w h0_3C7C
h0_3D02:
    st.b (a1)
    bra.w h0_3C7C
h0_3D08:
    lea.l $00FE(a6),a1
    bra.s h0_3CFA
h0_3D0E:
    lea.l $4EF1(a6),a1
    bra.s h0_3CFA
    DC.L    $4a2e46fa,$6700ff62,$1d7c0001,$01056000 ; VIOLATION: orphaned code island at $3D14 is not reached from known entrypoints
    DC.B    $ff,$58
h0_3D26:
    lea.l $0105(a6),a1
    bra.s h0_3CFA
h0_3D2C:
    lea.l $024F(a6),a1
    bra.s h0_3CFA
h0_3D32:
    tst.b $46FA(a6)
    beq.w h0_3C7C
h0_3D3A:
    sf.b $0104(a6)
    bra.w h0_3C7C
h0_3D42:
    lea.l $0129(a6),a1
    bra.s h0_3CFA
h0_3D48:
    tst.b $46FA(a6)
    beq.w h0_3C7C
h0_3D50:
    sf.b $0104(a6)
    st.b $010A(a6)
    bra.w h0_3C7C
    DC.L    $4a2e46fa,$6700000c,$3d7c0000,$025050ee,$00ff1014,$04000030,$6500ff06,$6616524c
    DC.L    $4a2e46fa,$6700fefa,$51ee00ff,$426e0250,$6000feee,$53004880,$b07c0007,$6400fee2
    DC.L    $013c0063,$67000026,$b03c0006,$66000004,$7002524c,$4a2e46fa,$6700fec6,$3d400250
    DC.L    $6000febe ; VIOLATION: orphaned code island at $3D5C is not reached from known entrypoints
h0_3DC0:
    lea.l $024E(a6),a1
    bra.w h0_3CFA
h0_3DC8:
    moveq.l #-1,d0
    rts
h0_3DCC:
    moveq.l #0,d2
    move.b (a4)+,d2
    subi.b #48,d2
    bcs.s h0_3DC8
h0_3DD6:
    cmp.b #$A,d2
    bcc.s h0_3DC8
h0_3DDC:
    move.b (a4),d1
    cmp.b #$30,d1
    bcs.s h0_3DFE
h0_3DE4:
    cmp.b #$3A,d1
    bcc.s h0_3DFE
h0_3DEA:
    mulu.w #$A,d2
    subi.b #48,d1
    andi.w #255,d1
    add.w d1,d2
    move.w d2,$4A26(a6)
    addq.w #1,a4
h0_3DFE:
    tst.w d2
    beq.s h0_3DC8
h0_3E02:
    tst.b $46FA(a6)
    beq.w h0_3C7C
h0_3E0A:
    move.w d2,$4A26(a6)
    bra.w h0_3C7C
h0_3E12:
    lea.l $0868(a6),a3
    st.b $012D(a6)
    tst.b $46FD(a6)
h0_3E1E:
    beq.w h0_3E2A
h0_3E22:
    bsr.w h0_4778
h0_3E26:
    moveq.l #0,d0
    rts
h0_3E2A:
    bsr.w h0_47EC
h0_3E2E:
    bra.s h0_3E26
h0_3E30:
    lea.l $507C(a6),a3
    sf.b $012D(a6)
    bra.s h0_3E1E
h0_3E3A:
    lea.l $0816(a6),a1
    bra.s h0_3E44
h0_3E40:
    lea.l $06FE(a6),a1
h0_3E44:
    moveq.l #81,d0
    moveq.l #0,d2
    cmpi.b #34,(a4)
    bne.s h0_3E50
h0_3E4E:
    move.b (a4)+,d2
h0_3E50:
    move.b (a4)+,d1
    beq.s h0_3E76
h0_3E54:
    cmp.b #$D,d1
    beq.s h0_3E76
h0_3E5A:
    cmp.b d2,d1
    beq.s h0_3E78
h0_3E5E:
    cmp.b #$20,d1
    bne.s h0_3E68
h0_3E64:
    tst.b d2
    beq.s h0_3E76
h0_3E68:
    tst.b $46FA(a6)
    beq.w h0_3E72
h0_3E70:
    move.b d1,(a1)+
h0_3E72:
    subq.b #1,d0
    bne.s h0_3E50
h0_3E76:
    subq.w #1,a4
h0_3E78:
    tst.b $46FA(a6)
    beq.w h0_3E82
h0_3E80:
    clr.b (a1)
h0_3E82:
    rts
    DC.L    $4a2e46fa,$67000012,$50ee0101,$2d7c0000,$00034810,$50ee480e,$12146700,$fddcb23c
    DC.L    $00206700,$fdd4b23c,$000d6700,$fdcc43ee,$07c4608c ; VIOLATION: orphaned code island at $3E84 is not reached from known entrypoints
h0_3EB8:
    move.b (a4)+,d1
    beq.s h0_3ECE
h0_3EBC:
    cmp.b #$D,d1
    beq.s h0_3ECE
h0_3EC2:
    cmp.b #$9,d1
    beq.s h0_3EB8
h0_3EC8:
    cmp.b #$20,d1
    beq.s h0_3EB8
h0_3ECE:
    rts
h0_3ED0:
    tst.b $46FC(a6)
    bne.w h0_3F02
h0_3ED8:
    bsr.s h0_3EB8
h0_3EDA:
    beq.s h0_3EFE
h0_3EDC:
    move.b (a4)+,d1
    beq.s h0_3EFE
h0_3EE0:
    cmp.b #$D,d1
    beq.s h0_3EFE
h0_3EE6:
    cmp.b #$9,d1
    beq.w h0_3EFE
h0_3EEE:
    cmp.b #$20,d1
h0_3EF2:
    beq.w h0_3EFE
h0_3EF6:
    cmp.b #$2C,d1
    bne.s h0_3EDC
h0_3EFC:
    bra.s h0_3ED8
h0_3EFE:
    subq.w #1,a4
    rts
h0_3F02:
    bsr.s h0_3EB8
h0_3F04:
    beq.s h0_3F60
h0_3F06:
    st.b d2
    lea.l $041E(a6),a0
    clr.b $0004(a0)
    bsr.w h0_7726
h0_3F14:
    bne.s h0_3F5A
h0_3F16:
    cmp.b #$3D,d1
    beq.s h0_3F22
h0_3F1C:
    moveq.l #1,d2
    moveq.l #2,d3
    bra.s h0_3F32
h0_3F22:
    move.b (a4)+,d1
    bsr.w h0_0DF6
h0_3F28:
    tst.b d4
    bne.s h0_3F5A
h0_3F2C:
    cmp.b #$2,d3
    bne.s h0_3F5A
h0_3F32:
    lea.l $041E(a6),a0
    movem.l d1-d2,-(a7)
    bsr.w h0_0C0E
h0_3F3E:
    movem.l (a7)+,d1/d4
    beq.s h0_3F5A
h0_3F44:
    lea.l $0170(a6),a2
    moveq.l #2,d3
    move.w d1,-(a7)
    bsr.w h0_0CF6
h0_3F50:
    move.w (a7)+,d1
    cmp.b #$2C,d1
    bne.s h0_3F60
h0_3F58:
    bra.s h0_3F02
h0_3F5A:
    moveq.l #81,d0
    bra.w h0_8556
h0_3F60:
    bra.s h0_3F78
h0_3F62:
    tst.b $46FB(a6)
    bne.s h0_3F7E
h0_3F68:
    move.b (a4)+,d1
    beq.s h0_3F78
h0_3F6C:
    cmp.b #$20,d1
    beq.s h0_3F78
h0_3F72:
    cmp.b #$D,d1
    bne.s h0_3F68
h0_3F78:
    subq.w #1,a4
    moveq.l #0,d0
    rts
h0_3F7E:
    bsr.w h0_440E
h0_3F82:
    bra.s h0_3F78
    DC.L    $2f0c426e,$024c610c ; VIOLATION: orphaned code island at $3F84 is not reached from known entrypoints
    DC.B    "(_Rn"
    DC.L    $024c51ee,$01034e75
    DC.B    $2d,$4f,$02,$66,$60,$00,$04,$70 ; VIOLATION: orphaned code island at $3F98 is not reached from known entrypoints
h0_3FA0:
    lea.l dat_4006(pc),a0
    moveq.l #0,d2
h0_3FA6:
    move.b (a0)+,d2
    beq.s h0_3FCE
h0_3FAA:
    cmp.b (a0),d1
    blt.s h0_3FCE
h0_3FAE:
    bne.s h0_3FC8
h0_3FB0:
    lea.l $0001(a0),a1
    movea.l a4,a2
    move.b d2,d3
h0_3FB8:
    subq.b #1,d3
    beq.s h0_3FD2
h0_3FBC:
    move.b (a2)+,d0
    ext.w d0
    move.b $7E(a6,d0.w),d0
    cmp.b (a1)+,d0
    beq.s h0_3FB8
h0_3FC8:
    lea.l $2(a0,d2.w),a0
    bra.s h0_3FA6
h0_3FCE:
    moveq.l #0,d0
    rts
h0_3FD2:
    move.b (a2),d0
    beq.s h0_3FF0
h0_3FD6:
    cmp.b #$D,d0
    beq.s h0_3FF0
h0_3FDC:
    cmp.b #$2C,d0
    beq.s h0_3FF0
h0_3FE2:
    cmp.b #$9,d0
    beq.s h0_3FF0
h0_3FE8:
    cmp.b #$20,d0
    beq.s h0_3FF0
h0_3FEE:
    bra.s h0_3FC8
h0_3FF0:
    move.b (a1)+,d0
    lsl.w #8,d0
    move.b (a1)+,d0
    lea.l -$2(a1,d0.w),a0
    movea.l a2,a4
    move.b (a4)+,d1
    lea.l dat_43AD(pc),a2
    cmpa.l a2,a0
    rts
dat_4006:
    DC.B    $09,$41,$4c,$4c,$4f,$57,$5a,$45,$52,$4f
dat_4010:
    DC.W    h0_437C-*
    DC.B    $05
    DC.B    "ATARI"
dat_4018:
    DC.W    h0_42C8-*
    DC.B    $06
    DC.B    "AUTOPC"
dat_4021:
    DC.W    h0_4328-*
    DC.B    $03,$42,$44,$4c
dat_4027:
    DC.W    h0_4316-*
    DC.B    $03,$42,$44,$57
dat_402D:
    DC.W    h0_4310-*
    DC.B    $03,$42,$52,$42
dat_4033:
    DC.W    h0_42F2-*
    DC.B    $03,$42,$52,$4c
dat_4039:
    DC.W    h0_42FE-*
    DC.B    $03,$42,$52,$53
dat_403F:
    DC.W    h0_42F2-*
    DC.B    $03,$42,$52,$57
dat_4045:
    DC.W    h0_42F8-*
    DC.B    $04
    DC.B    "CASE"
dat_404C:
    DC.W    h0_4230-*
    DC.B    $06
    DC.B    "CHKBIT"
dat_4055:
    DC.W    h0_4368-*
    DC.B    $06
    DC.B    "CHKIMM"
dat_405E:
    DC.W    h0_4350-*
    DC.L    $0543484b
    DC.B    $50,$43
dat_4066:
    DC.W    h0_4334-*
    DC.B    $01,$44
dat_406A:
    DC.W    h0_4246-*
    DC.L    $05444542
    DC.B    $55,$47
dat_4072:
    DC.W    h0_4246-*
    DC.L    $03445249
dat_4078:
    DC.W    h0_42D6-*
    DC.B    $04
    DC.B    "EVEN"
dat_407F:
    DC.W    h0_435C-*
    DC.B    $04
    DC.B    "FROM"
dat_4086:
    DC.W    h0_43F4-*
    DC.L    $0647454e
    DC.B    $53,$59,$4d
dat_408F:
    DC.W    h0_4236-*
    DC.B    $03,$47,$53,$54
dat_4095:
    DC.W    h0_42CE-*
    DC.B    $04
    DC.B    "HCLN"
dat_409C:
    DC.W    h0_4394-*
    DC.B    $06
    DC.B    "HEADER"
dat_40A5:
    DC.W    h0_43C2-*
    DC.B    $06
    DC.B    "INCDIR"
dat_40AE:
    DC.W    h0_43D0-*
    DC.L    $07494e43
    DC.B    "ONCE"
dat_40B8:
    DC.W    h0_4388-*
    DC.B    $07
    DC.B    "LATTICE"
dat_40C2:
    DC.W    h0_42A6-*
    DC.L    $044c494e
    DC.B    $45
dat_40C9:
    DC.W    h0_439E-*
    DC.B    $04
    DC.B    "LIST"
dat_40D0:
    DC.W    h0_4284-*
    DC.B    $05
    DC.B    "LIST1"
dat_40D8:
    DC.W    h0_4290-*
    DC.B    $08
    DC.B    "LOCALDOT"
dat_40E3:
    DC.W    h0_4348-*
    DC.B    $06
    DC.B    "LOCALU"
dat_40EC:
    DC.W    h0_4340-*
    DC.B    $06
    DC.B    "LOWMEM"
dat_40F5:
    DC.W    h0_43E8-*
    DC.B    $03,$4d,$45,$58
dat_40FB:
    DC.W    h0_42AA-*
    DC.B    $0b
    DC.B    "NOALLOWZERO"
dat_4109:
    DC.W    h0_4382-*
    DC.B    $08
    DC.B    "NOAUTOPC"
dat_4114:
    DC.W    h0_432E-*
    DC.B    $06
    DC.B    "NOCASE"
dat_411D:
    DC.W    h0_4240-*
    DC.B    $08
    DC.B    "NOCHKBIT"
dat_4128:
    DC.W    h0_436E-*
    DC.B    $08
    DC.B    "NOCHKIMM"
dat_4133:
    DC.W    h0_4356-*
    DC.B    $07
    DC.B    "NOCHKPC"
dat_413D:
    DC.W    h0_433A-*
    DC.B    $07
    DC.B    "NOCODES"
dat_4147:
    DC.W    h0_4254-*
    DC.B    $07
    DC.B    "NODEBUG"
dat_4151:
    DC.W    h0_425A-*
    DC.B    $06
    DC.B    "NOEVEN"
dat_415A:
    DC.W    h0_4362-*
    DC.L    $064e4f48
    DC.B    $43,$4c,$4e
dat_4163:
    DC.W    h0_43A8-*
    DC.B    $09
    DC.B    "NOINCONCE"
dat_416F:
    DC.W    h0_438E-*
    DC.B    $06
    DC.B    "NOLINE"
dat_4178:
    DC.W    h0_43A8-*
    DC.B    $06
    DC.B    "NOLIST"
dat_4181:
    DC.W    h0_428A-*
    DC.B    $07
    DC.B    "NOLIST1"
dat_418B:
    DC.W    h0_4296-*
    DC.B    $05
    DC.B    "NOMEX"
dat_4193:
    DC.W    h0_42B0-*
    DC.B    $08
    DC.B    "NOSYMTAB"
dat_419E:
    DC.W    h0_427E-*
    DC.L    $094e4f54
    DC.B    "RACEIF"
dat_41AA:
    DC.W    h0_42A2-*
    DC.L    $064e4f54
    DC.B    $59,$50,$45
dat_41B3:
    DC.W    h0_4266-*
    DC.B    $06
    DC.B    "NOWARN"
dat_41BC:
    DC.W    h0_4272-*
    DC.B    $03,$4f,$44,$4c
dat_41C2:
    DC.W    h0_4322-*
    DC.L    $034f4457
dat_41C8:
    DC.W    h0_431C-*
    DC.B    $03,$4f,$4c,$44
dat_41CE:
    DC.W    h0_42B6-*
    DC.L    $05515549
    DC.B    $45,$54
dat_41D6:
    DC.W    h0_43EE-*
    DC.L    $04535245
    DC.B    $43
dat_41DD:
    DC.W    h0_42D2-*
    DC.B    $05
    DC.B    "SUPER"
dat_41E5:
    DC.W    h0_42BC-*
    DC.B    $06
    DC.B    "SYMTAB"
dat_41EE:
    DC.W    h0_4278-*
    DC.B    $02,$54,$4f
dat_41F3:
    DC.W    h0_43AE-*
    DC.B    $07
    DC.B    "TRACEIF"
dat_41FD:
    DC.W    h0_429C-*
    DC.B    $04
    DC.B    "TYPE"
dat_4204:
    DC.W    h0_4260-*
    DC.B    $04
    DC.B    "USER"
dat_420B:
    DC.W    h0_42C2-*
    DC.B    $04
    DC.B    "WARN"
dat_4212:
    DC.W    h0_426C-*
    DC.L    $07574152
    DC.B    "NBIT"
dat_421C:
    DC.W    h0_4374-*
    DC.B    $04
    DC.B    "WITH"
dat_4223:
    DC.W    h0_43FC-*
    DC.B    $06
    DC.B    "XDEBUG"
dat_422C:
    DC.W    h0_424E-*
    DC.B    $00,$00
h0_4230:
    sf.b $00FE(a6)
    rts
h0_4236:
    st.b $010A(a6)
    sf.b $0104(a6)
    rts
h0_4240:
    st.b $00FE(a6)
    rts
h0_4246:
    move.b #$1,$0105(a6)
    rts
h0_424E:
    st.b $0105(a6)
    rts
h0_4254:
    st.b $012A(a6)
    rts
h0_425A:
    sf.b $0105(a6)
    rts
h0_4260:
    sf.b $0108(a6)
    rts
h0_4266:
    st.b $0108(a6)
    rts
h0_426C:
    st.b $0106(a6)
    rts
h0_4272:
    sf.b $0106(a6)
    rts
h0_4278:
    st.b $0100(a6)
    rts
h0_427E:
    sf.b $0100(a6)
    rts
h0_4284:
    st.b $0101(a6)
    rts
h0_428A:
    sf.b $0101(a6)
    rts
h0_4290:
    st.b $024E(a6)
    rts
h0_4296:
    sf.b $024E(a6)
    rts
h0_429C:
    st.b $0128(a6)
    rts
h0_42A2:
    sf.b $0128(a6)
h0_42A6:
    moveq.l #2,d0
    bra.s h0_42D8
h0_42AA:
    st.b $0119(a6)
    rts
h0_42B0:
    sf.b $0119(a6)
    rts
h0_42B6:
    st.b $0126(a6)
    rts
h0_42BC:
    sf.b $0127(a6)
    rts
h0_42C2:
    st.b $0127(a6)
    rts
h0_42C8:
    sf.b $00FF(a6)
    bra.s h0_42E0
h0_42CE:
    moveq.l #0,d0
    bra.s h0_42D8
h0_42D2:
    moveq.l #5,d0
    bra.s h0_42D8
h0_42D6:
    moveq.l #1,d0
h0_42D8:
    st.b $00FF(a6)
    move.w d0,$0250(a6)
h0_42E0:
    tst.l $0256(a6)
    bne.w h0_44AC
    tst.b $026A(a6)
    beq.w h0_45C6
    rts
h0_42F2:
    st.b $012E(a6)
    rts
h0_42F8:
    sf.b $012E(a6)
    rts
h0_42FE:
    cmpi.b #20,$0123(a6)
    blt.w h0_3258
    move.b #$1,$012E(a6)
    rts
h0_4310:
    st.b $012F(a6)
    rts
h0_4316:
    sf.b $012F(a6)
    rts
h0_431C:
    st.b $0130(a6)
    rts
h0_4322:
    sf.b $0130(a6)
    rts
h0_4328:
    st.b $011B(a6)
    rts
h0_432E:
    sf.b $011B(a6)
    rts
h0_4334:
    st.b $0107(a6)
    rts
h0_433A:
    sf.b $0107(a6)
    rts
h0_4340:
    move.b #$5F,$0118(a6)
    rts
h0_4348:
    move.b #$2E,$0118(a6)
    rts
h0_4350:
    st.b $011F(a6)
    rts
h0_4356:
    sf.b $011F(a6)
    rts
h0_435C:
    st.b $0121(a6)
    rts
h0_4362:
    sf.b $0121(a6)
    rts
h0_4368:
    st.b $0120(a6)
    rts
h0_436E:
    sf.b $0120(a6)
    rts
h0_4374:
    move.b #$1,$0120(a6)
    rts
h0_437C:
    st.b $0122(a6)
    rts
h0_4382:
    sf.b $0122(a6)
    rts
h0_4388:
    st.b $0136(a6)
    rts
h0_438E:
    sf.b $0136(a6)
    rts
h0_4394:
    st.b $012B(a6)
    st.b $012C(a6)
    rts
h0_439E:
    st.b $012B(a6)
    sf.b $012C(a6)
    rts
h0_43A8:
    sf.b $012B(a6)
    DC.B    $4e ; VIOLATION: invalid overlap: decoded instruction at $43AC crosses required label at $43AD; region emitted as data
dat_43AD:
    DC.B    $75
h0_43AE:
    bsr.w h0_3EB8
    subq.w #1,a4
    tst.b $46FA(a6)
    beq.w h0_4406
    bsr.w h0_3E40
    bra.s h0_440A
h0_43C2:
    move.b $46FA(a6),-(a7)
    lea.l $507C(a6),a3
    sf.b $012D(a6)
    bra.s h0_43DC
h0_43D0:
    move.b $46FD(a6),-(a7)
    lea.l $0868(a6),a3
    st.b $012D(a6)
h0_43DC:
    bsr.w h0_3EB8
    subq.w #1,a4
    tst.b (a7)+
    bra.w h0_3E1E
h0_43E8:
    st.b $024F(a6)
    rts
h0_43EE:
    st.b $0129(a6)
    rts
h0_43F4:
    bsr.w h0_3EB8
    bra.w h0_3BA6
h0_43FC:
    bsr.w h0_3EB8
    subq.w #1,a4
    lea.l $0816(a6),a1
h0_4406:
    bsr.w h0_3E44
h0_440A:
    move.b (a4)+,d1
    rts
h0_440E:
    move.b (a4)+,d1
    st.b $46FE(a6)
    cmp.b #$D,d1
    beq.w h0_3B02
h0_441C:
    cmp.b #$9,d1
    beq.w h0_3B02
h0_4424:
    cmp.b #$20,d1
    beq.w h0_3B02
h0_442C:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    beq.w h0_3B02
h0_4436:
    move.b (a4),d0
    cmp.b #$2B,d0
    beq.s h0_444E
h0_443E:
    cmp.b #$2D,d0
    beq.s h0_444E
h0_4444:
    bsr.w h0_3FA0
h0_4448:
    beq.s h0_444E
h0_444A:
    jsr (a0)
h0_444C:
    bra.s h0_446A
h0_444E:
    subi.b #65,d1
    bcs.s h0_4472
h0_4454:
    cmp.b #$1A,d1
    bcc.s h0_4472
h0_445A:
    ext.w d1
    add.w d1,d1
    move.w dat_4478(pc,d1.w),d0
    beq.s h0_4472
h0_4464:
    move.b (a4)+,d1
    jsr dat_4478(pc,d0.w)
h0_446A:
    cmp.b #$2C,d1
    beq.s h0_440E
h0_4470:
    rts
h0_4472:
    moveq.l #58,d0
    bra.w h0_8552
dat_4478:
    DC.W    h0_4512-dat_4478
    DC.W    $0000
    DC.B    $00,$c0
    DC.W    h0_44C6-dat_4478
    DC.W    h0_4522-dat_4478
    DC.W    $0000
    DC.W    $0000
    DC.W    $0000
    DC.W    h0_451A-dat_4478
    DC.W    $0000
    DC.W    $0000
    DC.W    h0_456A-dat_4478
    DC.W    h0_44DC-dat_4478
    DC.W    $0000
    DC.W    h0_45E6-dat_4478
    DC.W    h0_44E4-dat_4478
    DC.W    $0000
    DC.W    $0000
    DC.W    h0_44FA-dat_4478
    DC.W    h0_44D4-dat_4478
    DC.W    h0_452A-dat_4478
    DC.W    $0000
    DC.W    h0_4502-dat_4478
    DC.W    h0_450A-dat_4478
    DC.W    $0000
    DC.W    $0000
h0_44AC:
    moveq.l #64,d0
h0_44AE:
    bra.w h0_8556
h0_44B2:
    move.b (a4)+,d0
    exg d0,d1
    cmp.b #$2B,d0
    beq.s h0_44C4
h0_44BC:
    cmp.b #$2D,d0
    bne.s h0_4472
h0_44C2:
    tst.b d0
h0_44C4:
    rts
h0_44C6:
    bsr.s h0_44B2
h0_44C8:
    seq.b d0
    andi.b #1,d0
    move.b d0,$0105(a6)
    rts
h0_44D4:
    bsr.s h0_44B2
h0_44D6:
    sne.b $0108(a6)
    rts
h0_44DC:
    bsr.s h0_44B2
h0_44DE:
    seq.b $0119(a6)
    rts
h0_44E4:
    cmp.b #$3D,d1
    bne.s h0_44F2
h0_44EA:
    bsr.w h0_3294
h0_44EE:
    bne.s h0_4472
h0_44F0:
    rts
h0_44F2:
    bsr.s h0_44B2
h0_44F4:
    seq.b $0107(a6)
    rts
h0_44FA:
    bsr.s h0_44B2
h0_44FC:
    seq.b $0100(a6)
    rts
h0_4502:
    bsr.s h0_44B2
h0_4504:
    seq.b $0106(a6)
    rts
h0_450A:
    bsr.s h0_44B2
h0_450C:
    seq.b $0105(a6)
    rts
h0_4512:
    bsr.s h0_44B2
h0_4514:
    seq.b $011B(a6)
    rts
h0_451A:
    bsr.s h0_44B2
h0_451C:
    seq.b $011F(a6)
    rts
h0_4522:
    bsr.s h0_44B2
h0_4524:
    seq.b $0121(a6)
    rts
h0_452A:
    moveq.l #95,d2
    bsr.s h0_44B2
h0_452E:
    beq.s h0_4532
h0_4530:
    moveq.l #46,d2
h0_4532:
    move.b d2,$0118(a6)
    rts
    DC.L    $61000102,$6616b47c,$00086500,$ff2eb47c,$00806400,$ff265242,$3d420252,$b23c002b
    DC.L    $6708b23c,$002d6608,$4a0156ee,$00fe121c ; VIOLATION: orphaned code island at $4538 is not reached from known entrypoints
    DC.B    $4e,$75
h0_456A:
    tst.l $0256(a6)
    bne.w h0_44AC
h0_4572:
    move.b d1,d0
    move.b (a4)+,d1
    tst.b $026A(a6)
    bne.s h0_45E4
h0_457C:
    cmp.b #$2B,d0
    beq.s h0_45BE
h0_4582:
    cmp.b #$2D,d0
    beq.s h0_45B8
h0_4588:
    subi.b #48,d0
    bcs.w h0_4472
h0_4590:
    ext.w d0
    beq.s h0_45B8
h0_4594:
    subq.w #1,d0
    cmp.w #$7,d0
    bcc.w h0_4472
    DC.B    $01,$3c ; VIOLATION: decode failed in reachable code; region emitted as data
    DC.L    $00636700,$feceb03c,$00066602,$700250ee,$00ff3d40,$0250600e
h0_45B8:
    sf.b $00FF(a6)
    bra.s h0_45C6
h0_45BE:
    st.b $00FF(a6)
    clr.w $0250(a6)
h0_45C6:
    movea.l $0148(a6),a1
    movea.l $0144(a6),a0
    clr.l $01C4(a6)
    tst.b $026A(a6)
    bne.s h0_45DC
h0_45D8:
    clr.l $01DA(a6)
h0_45DC:
    bsr.w h0_7A1A
h0_45E0:
    move.b -$0001(a4),d1
h0_45E4:
    rts
h0_45E6:
    lea.l $0110(a6),a1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$57,d1
    bne.s h0_45FC
h0_45F6:
    lea.l $0112(a6),a1
    move.b (a4)+,d1
h0_45FC:
    cmp.b #$2D,d1
    beq.s h0_4630
h0_4602:
    cmp.b #$2B,d1
    beq.s h0_4634
h0_4608:
    bsr.w h0_463C
h0_460C:
    subq.w #1,d2
    bmi.w h0_4472
h0_4612:
    cmp.w #$B,d2
    bhi.w h0_4472
h0_461A:
    bsr.w h0_44B2
h0_461E:
    beq.s h0_4628
h0_4620:
    move.w (a1),d0
    bclr d2,d0
    move.w d0,(a1)
    rts
h0_4628:
    move.w (a1),d0
    bset d2,d0
    move.w d0,(a1)
    rts
h0_4630:
    clr.w (a1)
    bra.s h0_4638
h0_4634:
    move.w #$FFFF,(a1)
h0_4638:
    move.b (a4)+,d1
    rts
h0_463C:
    cmp.b #$30,d1
    bcs.s h0_4670
h0_4642:
    cmp.b #$39,d1
    bhi.s h0_4670
h0_4648:
    moveq.l #0,d2
    subi.b #48,d1
    move.b d1,d2
h0_4650:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.s h0_466E
h0_4658:
    cmp.b #$3A,d1
    bcc.s h0_466E
h0_465E:
    mulu.w #$A,d2
    subi.b #48,d1
    andi.w #15,d1
    add.w d1,d2
    bra.s h0_4650
h0_466E:
    moveq.l #0,d0
h0_4670:
    rts
h0_4672:
    tst.b $480E(a6)
    beq.s h0_46A8
h0_4678:
    lea.l $07C4(a6),a0
    tst.b (a0)
    bne.s h0_46A4
h0_4680:
    lea.l $052A(a6),a1
    moveq.l #0,d0
    move.b $0005(a1),d0
    subq.b #1,d0
    bmi.s h0_4696
h0_468E:
    movea.l (a1),a1
h0_4690:
    move.b (a1)+,(a0)+
    dbf.w d0,h0_4690
h0_4696:
    clr.b (a0)
    lea.l $07C4(a6),a0
    lea.l dat_46AA(pc),a2
    bsr.w h0_46B0
h0_46A4:
    bra.w h0_BBE4
h0_46A8:
    rts
dat_46AA:
    DC.B    $2e,$6c,$73,$74,$00,$00 ; VIOLATION: orphaned code island at $46AA is not reached from known entrypoints
h0_46B0:
    bsr.s h0_46C4
h0_46B2:
    beq.s h0_46B6
h0_46B4:
    movea.l d2,a1
h0_46B6:
    subq.w #1,a1
h0_46B8:
    move.b (a2)+,(a1)+
    bne.s h0_46B8
h0_46BC:
    rts
h0_46BE:
    bsr.s h0_46C4
h0_46C0:
    beq.s h0_46B6
h0_46C2:
    rts
h0_46C4:
    movea.l a0,a1
h0_46C6:
    moveq.l #0,d2
h0_46C8:
    move.b (a1)+,d1
    beq.s h0_46E8
h0_46CC:
    cmp.b #$5C,d1
    beq.s h0_46C6
h0_46D2:
    cmp.b #$2F,d1
    beq.s h0_46C6
h0_46D8:
    cmp.b #$3A,d1
    beq.s h0_46C6
h0_46DE:
    cmp.b #$2E,d1
    bne.s h0_46C8
h0_46E4:
    move.l a1,d2
    bra.s h0_46C8
h0_46E8:
    tst.l d2
h0_46EA:
    rts
h0_46EC:
    tst.b $012D(a6)
    beq.s h0_46EA
h0_46F2:
    movea.l (a3),a0
    move.b -$1(a0,d3.w),d0
    cmp.b #$3A,d0
    beq.s h0_46EA
h0_46FE:
    cmp.b #$2F,d0
    beq.s h0_46EA
h0_4704:
    cmp.b #$5C,d0
    beq.s h0_46EA
h0_470A:
    moveq.l #92,d1
h0_470C:
    movea.l (a3),a0
    cmp.w $0004(a3),d3
    bcs.s h0_4742
h0_4714:
    movem.l d0-d2/a1-a2,-(a7)
    moveq.l #100,d1
    add.w $0004(a3),d1
    bsr.w h0_9146
h0_4722:
    movea.l (a3),a1
    move.l a0,(a3)
    move.w $0004(a3),d1
    lsr.w #2,d1
    beq.s h0_4736
h0_472E:
    subq.w #1,d1
h0_4730:
    move.l (a1)+,(a0)+
    dbf.w d1,h0_4730
h0_4736:
    movem.l (a7)+,d0-d2/a1-a2
    addi.w #100,$0004(a3)
    movea.l (a3),a0
h0_4742:
    move.b d1,$0(a0,d3.w)
    addq.w #1,d3
    rts
h0_474A:
    moveq.l #4,d1
    move.w d1,$0004(a3)
    bsr.w h0_9146
h0_4754:
    move.l a0,(a3)
    clr.b (a0)
    rts
h0_475A:
    movea.l (a3),a0
    clr.b (a0)
h0_475E:
    moveq.l #0,d3
    tst.w $0004(a3)
    beq.s h0_4776
h0_4766:
    movea.l (a3),a0
h0_4768:
    tst.b (a0)+
    beq.s h0_4776
h0_476C:
    addq.w #1,d3
    tst.b (a0)+
    bne.s h0_476C
h0_4772:
    addq.w #1,d3
    bra.s h0_4768
h0_4776:
    rts
h0_4778:
    move.b (a4)+,d1
    bsr.s h0_475E
h0_477C:
    moveq.l #0,d2
    cmp.b #$22,d1
    beq.s h0_478A
h0_4784:
    cmp.b #$27,d1
    bne.s h0_478E
h0_478A:
    move.b d1,d2
h0_478C:
    move.b (a4)+,d1
h0_478E:
    beq.s h0_47D8
h0_4790:
    cmp.b #$D,d1
    beq.s h0_47D8
h0_4796:
    cmp.b #$20,d1
    bne.s h0_47A2
h0_479C:
    tst.b d2
    bne.s h0_47BC
h0_47A0:
    bra.s h0_47D8
h0_47A2:
    cmp.b #$9,d1
    beq.s h0_47D8
h0_47A8:
    cmp.b d2,d1
    beq.s h0_47C2
h0_47AC:
    cmp.b #$3B,d1
    beq.s h0_47B8
h0_47B2:
    cmp.b #$2C,d1
    bne.s h0_47BC
h0_47B8:
    tst.b d2
    beq.s h0_47CA
h0_47BC:
    bsr.w h0_470C
h0_47C0:
    bra.s h0_478C
h0_47C2:
    move.b (a4)+,d1
    cmp.b #$2C,d1
    bne.s h0_47D8
h0_47CA:
    bsr.w h0_46EC
h0_47CE:
    moveq.l #0,d1
    bsr.w h0_470C
h0_47D4:
    move.b (a4)+,d1
    bra.s h0_477C
h0_47D8:
    bsr.w h0_46EC
h0_47DC:
    moveq.l #0,d1
    bsr.w h0_470C
h0_47E2:
    bsr.w h0_470C
h0_47E6:
    move.b -$0001(a4),d1
    rts
h0_47EC:
    move.b (a4)+,d1
h0_47EE:
    moveq.l #0,d2
    cmp.b #$22,d1
    beq.s h0_47FC
h0_47F6:
    cmp.b #$27,d1
    bne.s h0_4800
h0_47FC:
    move.b d1,d2
h0_47FE:
    move.b (a4)+,d1
h0_4800:
    beq.s h0_4812
h0_4802:
    cmp.b #$D,d1
    beq.s h0_4812
h0_4808:
    cmp.b #$20,d1
    bne.s h0_4814
h0_480E:
    tst.b d2
    bne.s h0_47FE
h0_4812:
    rts
h0_4814:
    cmp.b #$9,d1
    beq.s h0_4812
h0_481A:
    cmp.b d2,d1
    beq.s h0_482E
h0_481E:
    cmp.b #$3B,d1
    beq.s h0_482A
h0_4824:
    cmp.b #$2C,d1
    bne.s h0_47FE
h0_482A:
    tst.b d2
    bne.s h0_47FE
h0_482E:
    move.b (a4)+,d1
    cmp.b #$2C,d1
    bne.s h0_4812
h0_4836:
    move.b (a4)+,d1
    bra.s h0_47EE
    DC.B    $41,$ee,$06,$fe,$74,$00,$4a,$10,$67,$04,$72,$0d,$4e,$75 ; VIOLATION: orphaned code island at $483A is not reached from known entrypoints
    DC.L    $b23c000d,$671ab23c,$00096714,$b23c0020,$670e10c1,$121c5202,$b43c0052,$66e2720d
    DC.L    $42104e75 ; VIOLATION: orphaned code island at $4848 is not reached from known entrypoints
    DC.L    $0c2e0014,$01236d00,$e9e40c2e,$00200123,$6700e9da,$4a2e026b,$66003c94,$6100d550
    DC.L    $b23c002c,$66003ca0,$121cb23c,$00236600,$3c9e121c,$6100c554,$6000d2ac ; VIOLATION: orphaned code island at $486C is not reached from known entrypoints
    DC.L    $6100dbac,$50ee026d,$6100cec2,$00644e75,$4a2e026a,$670a08ee,$00004ade,$61007338
    DC.L    $720d50ee,$01154e75 ; VIOLATION: orphaned code island at $48A8 is not reached from known entrypoints
    DC.B    $08,$ae,$00,$00,$4a,$de,$4e,$75 ; VIOLATION: orphaned code island at $48D0 is not reached from known entrypoints
    DC.L    $61002254,$b4bc0000,$000c6512,$b4bc0000,$00ff640a,$3d424a1e,$50ee0115 ; VIOLATION: orphaned code island at $48D8 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $70,$4b,$60,$00,$3c,$5c ; VIOLATION: orphaned code island at $48F6 is not reached from known entrypoints
    DC.L    $74000401,$0030654c,$b23c000a,$64461401,$121cb23c,$000d6724,$b23c0009,$671eb23c
    DC.L    $00206718,$04010030,$652ab23c,$000a6424,$c4fc000a,$0241000f,$d441121c,$70fc5582
    DC.L    $671870fa,$5d826712,$70005582,$670c70fe,$5d826706,$705a6000 ; VIOLATION: orphaned code island at $48FC is not reached from known entrypoints
    DC.B    $3c,$02
    DC.B    $1d,$40,$01,$31,$4e,$75 ; VIOLATION: orphaned code island at $4956 is not reached from known entrypoints
    DC.L    $6100e296,$6100ee3e,$6600eea8,$74003404,$246e0170,$41ee041e,$48e7201c,$4a2e026a
    DC.L    $66186100,$c2484cdf,$38106700,$3b7e7605,$6100c36c,$122cffff ; VIOLATION: orphaned code island at $495C is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $61,$00 ; VIOLATION: orphaned code island at $4996 is not reached from known entrypoints
    DC.L    $c2304cdf,$38106600,$3b6a0c29,$0005000d,$66003b5c,$b8a90008,$66003b54,$08e90006
    DC.L    $000c6600,$3b4a60d0
    DC.L    $01000102,$41ee041e,$7000102e,$026bb03c,$00016710,$082e0000,$47076708,$242e4700
    DC.L    $d5ae4704,$4a906626,$6100cd70,$7000102e,$026b103b,$00cce1aa,$4a2e4700,$6a024482
    DC.L    $202e4704,$d5ae4704,$24006000 ; VIOLATION: orphaned code island at $49C0 is not reached from known entrypoints
    DC.B    $e2,$7e
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $4A0E is not reached from known entrypoints
    DC.L    $026a6648,$2f086100,$cd42205f,$666e4a04,$666a2a02,$6100c1e8,$67003adc,$45ee0170
    DC.L    $7602282e,$47041028,$0006b02e,$0118670c,$6100c2b4,$2405122c,$ffff60a0
    DC.B    $45,$ee,$01,$60,$4a,$92,$67,$00,$3a,$be,$61,$00,$c3,$34,$60,$e8 ; VIOLATION: orphaned code island at $4A4C is not reached from known entrypoints
    DC.L    $6100c1b0,$66003abc,$0c290002,$000d6600,$3ab22029,$0008b0ae,$47046600,$3a9608e9
    DC.L    $0006000c,$66003a84,$6100ccd4,$6000ff62,$4e756100,$20944a82,$6b00f0ae,$2f026100
    DC.L    $527a4cdf,$00046600,$f0a042ae,$01b094ae,$026e2d42,$01bc122c,$ffff4e75,$9481650e
    DC.L    $670a2802,$76007200,$6100df94,$70004e75,$42ae4704,$720d4e75,$6100cc84,$66f24a04
    DC.L    $66ee2d42,$47046000,$e1a60c2e,$000a0123,$6d00e76a,$3ac6b23c,$00236600,$3a42121c
    DC.L    $6100c2f8,$6000d050,$0c2e0014,$01236600,$e74c610e,$8c423ac6,$4a2e026b,$66003a00
    DC.L    $4e756100,$ccec660e,$02420007,$02400001,$e7488440 ; VIOLATION: orphaned code island at $4A5C is not reached from known entrypoints
    DC.B    "Nup.`",0
    DC.B    $3a,$20
    DC.L    $6100d93e,$50ee026d,$6100cc32,$003d4e75,$611c4441,$54410000,$61144253,$5300610e
    DC.B    "TEXT",0
    DC.B    $00,$61,$06
    DC.B    "CODE",0
    DC.B    $00,$20,$5f
    DC.L    $43ee04a4,$61004c26,$12fc000d,$48e74008,$49ee04a4,$121c617a,$4cdf1002,$4e7541ee
    DC.L    $04a410c1,$121cb23c,$0009674c,$b23c0020,$6746b23c,$002c670a,$b23c000d,$673a10c1
    DC.L    $60e2101c,$43fa0038,$04000030,$653e6710,$43fa0031,$53006708,$43fa002e,$5300662c
    DC.L    $10fc002c,$082e0001,$02516604,$41ee04a4,$121c10d9,$66fc5388,$10bc000d,$608e434f
    DC.L    $44450044,$41544100,$42535300,$70666000,$395a6100,$2e46122c,$ffff7601,$61002dba
    DC.L    $720d4e75,$6100dfe6,$4a2e026a,$66482f08,$61001eee,$205f48e7,$30006100,$bfea4cdf
    DC.L    $00306610,$08290007,$000c6700,$38d21605,$24046042,$487a0016,$160545ee,$01705505
    DC.L    $6700c0ac,$45ee0168,$6000c0a4,$08e90007,$000c6000,$e02a6100,$bfae6600,$38ba0829
    DC.L    $0007000c,$670038b0,$2f096100,$cabc225f,$08e90006,$000c2342,$0008b629,$000d6600
    DC.L    $387e6000,$dffeb23c,$0023675c,$548d6100,$cc681005,$02000078,$672c3406,$02420018
    DC.L    $ed4a0246,$ff000046,$00c08c42,$206e027e,$30866100,$dbb0703c,$6000cad0,$00460200
    DC.L    $8c053ac6
    DC.B    "Nu*n"
    DC.L    $027e6100,$0324b23c,$002c66e8,$00060020,$3a86da05,$8b1d121c,$6100cb04,$851d4e75
    DC.L    $121c6100,$ca666100,$e66aee5a,$8c426100,$02f8b23c,$002c6600,$382a121c,$6100cae0
    DC.L    $8c023ac6,$4e756100,$ca42b4bc,$000000ff,$6400fbd4,$4a2e026a,$67104a2e,$480f670a
    DC.L    $38026100,$41de5344,$66f8122c,$ffff50ee,$01154e75,$4a2e0127,$67067065,$61003808
    DC.L    $3ac6b23c,$00236600,$37e2121c,$6100c098,$6100cdf0,$4a2e026b,$660037b0,$4e756100
    DC.L    $dafc6100,$ca7a8c02,$3ac64e75,$6100d6fa,$6100c9f2,$003d4e75,$4a2e026b,$6600378c
    DC.L    $b23c0023,$660037a4,$121c6100,$c9946100,$2ba68c02,$3ac6b4bc,$00000010,$64024e75
    DC.L    $701d6000,$37a20c2e,$00140123,$6d00e49a,$6100d694,$3afc4c40,$3ac66100,$c9a200fd
    DC.L    $b23c002c,$6600375c,$121c6100,$ca12206e,$027eb23c,$003a670c,$85280003,$e90a8528
    DC.L    $00024e75,$121c8528,$00036100,$c9f2206e,$027ee90a,$85280002,$4e750c2e,$00140123
    DC.L    $6d00e446,$3ac6206e,$027e5288,$102e026b,$673ab03c,$0003671e,$b03c0002,$660036ec
    DC.L    $b23c0023,$66003704,$121c0010,$00026100,$bfb66000,$cd0eb23c,$00236600,$36ee121c
    DC.L    $00100003,$6100bfa0,$6000ccd2,$b23c0023,$67ce0010,$00044e75,$6100018e,$6100c906
    DC.L    $003d4e75,$0c2e0014,$01236dec,$6100017a,$6100c8f2,$00ff4e75,$45ee4a3c,$50ee0115
    DC.L    $7400760d,$4a2e026a,$66084a12,$6704720d,$4e75b23c,$00276604,$7627121c,$b6016714
    DC.L    $b23c000d,$671614c1,$5202b43c,$005066ea,$720d6008,$b63c000d,$6702121c,$42124e75
    DC.L    $45ee4a8d,$60b66100,$c9208c02,$3ac64a2e,$026b6600
    DC.B    "66NuJ.",0
    DC.B    $ff
    DC.L    $6604588f,$720d4e75,$121c61f0,$41ee041e,$61002828,$66003654,$3f01610a,$321fb23c
    DC.L    $002c67e4,$4e751028,$0006b02e,$01186700,$35f64a2e,$026a671a,$6100bce8
    DC.B    $66,$16
h0_4F2A:
    move.b $000C(a1),d0
    andi.b #144,d0
    bne.s h0_4F40
h0_4F34:
    bset.b #5,$000C(a1)
    beq.w h0_9850
h0_4F3E:
    rts
h0_4F40:
    moveq.l #44,d0
    bra.w h0_8556
    DC.B    $70,$2b,$60,$00,$36,$08 ; VIOLATION: orphaned code island at $4F46 is not reached from known entrypoints
    DC.L    $121c6004 ; VIOLATION: orphaned code island at $4F4C is not reached from known entrypoints
    DC.L    $7a2c6194,$41ee041e,$610027cc,$660035f8,$10280006,$b02e0118,$67dc7601,$0c2e0003
    DC.L    $026b6602,$76023f01,$3f036100,$bc924c9f,$0008670a,$226e016c,$78006100,$bd6e6112
    DC.L    $321f1a01,$b23c002c,$67b2b23c,$003d67ac ; VIOLATION: orphaned code island at $4F50 is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $08,$2e ; VIOLATION: orphaned code island at $4FA2 is not reached from known entrypoints
    DC.L    $00020251,$6646b629,$000d6640,$08290005,$000c6638,$08290007,$000c6630,$10290017
    DC.L    $b02e0118,$672608e9,$0004000c,$661c206e,$0144ba3c,$002c6708,$08e90002,$000c6004
    DC.B    $52,$68,$00,$14,$33,$68,$00,$14,$00,$14,$4e,$75 ; VIOLATION: orphaned code island at $4FE4 is not reached from known entrypoints
    DC.B    $30,$3c,$00,$2b,$60,$00,$35,$60 ; VIOLATION: orphaned code island at $4FF0 is not reached from known entrypoints
    DC.B    $70,$00,$10,$2e,$02,$6b,$8c,$3b,$00,$04,$4e,$75 ; VIOLATION: orphaned code island at $4FF8 is not reached from known entrypoints
    DC.L    $40004080 ; VIOLATION: orphaned code island at $5004 is not reached from known entrypoints
    DC.B    "-MG("
    DC.L    $b23c005b,$670000a8,$7e0047ee,$470841ee
    DC.B    "GZ-HG"
    DC.B    $fa,$48,$6c
    DC.L    $ffff6100,$0464245f,$66000764,$08070000,$6634b23c,$00296600,$00b00807,$00016700
    DC.L    $00c04a2b,$00096600,$00b8102b,$00086b00,$00b07a10,$8a00121c,$b23c002b,$660608c5
    DC.L    $0003121c
    DC.B    $4e,$75
    DC.B    $b2,$3c ; VIOLATION: orphaned code island at $506A is not reached from known entrypoints
    DC.L    $002c6700,$0082121c,$b23c002e,$66000010,$2413362b,$0004182b,$00066000
    DC.B    $c9,$8e
    DC.B    $b2,$3c ; VIOLATION: orphaned code island at $508A is not reached from known entrypoints
    DC.L    $00096700,$0018b23c,$00206700,$0010b23c,$002c6708,$b23c000d,$6600c912,$284a122c
    DC.L    $ffff6100,$c1b26100,$c90a6000
    DC.B    $c1,$aa
    DC.B    $7e,$00 ; VIOLATION: orphaned code island at $50BA is not reached from known entrypoints
    DC.L    $47ee4708,$484708c7,$00076600,$06ca47ee,$471841ee,$47aa2d48,$47fa121c,$b23c005d
    DC.L    $6734b23c,$00296720,$610003a6,$660006a8,$b23c002c,$66e6121c,$b23c005b,$66ea4a2b
    DC.L    $000e6ec0,$60000690
    DC.B    $4a,$2b,$00,$0e,$6f,$00,$06,$88,$12,$1c,$60,$00,$00,$1c ; VIOLATION: orphaned code island at $5104 is not reached from known entrypoints
    DC.B    $4a,$2b ; VIOLATION: orphaned code island at $5112 is not reached from known entrypoints
    DC.L    $000e6c00,$067a4847,$47ee4708,$41ee475a,$2d4847fa,$121c60c0
    DC.L    $4a2b000e,$6c0e4847,$47ee4708,$41ee475a,$2d4847fa,$24070282,$00070007,$20024840
    DC.L    $e7488042,$d040d040,$7a300807,$00036702,$7a3b0807,$00176700,$04cc182e,$0123b83c
    DC.L    $00206700,$cfc2383c,$01d0243b,$00208842,$48422f0d,$3ac44ebb,$2014205f,$08040006
    DC.L    $67040884,$00023084,$70004e75,$01200001,$01200001,$01000001,$01000001,$01200001
    DC.L    $01200001,$05fa0000,$05fa0000,$01200005,$01200005,$01000005,$01000005,$01200005
    DC.L    $01200005,$05fa0000,$05fa0000,$01200005,$01200005,$01000005,$01000005,$01200005
    DC.L    $01200005,$05fa0000,$05fa0000,$01200005,$01200005,$01000005,$01000005,$01200005
    DC.L    $01200005,$05fa0000,$05fa0000,$01620001,$01620001,$05fa0000,$05fa0000,$05fa0000
    DC.L    $05fa0000,$05fa0000,$05fa0000,$01620001,$01620001,$05fa0000,$05fa0000,$05fa0000
    DC.L    $05fa0000,$05fa0000,$05fa0000,$01620001,$01620001,$05fa0000,$05fa0000,$05fa0000
    DC.L    $05fa0000,$05fa0000,$05fa0000,$01620001,$01620001,$05fa0000,$05fa0000,$05fa0000
    DC.L    $05fa0000,$05fa0000,$05fa0000,$08870001,$08c70002,$7008d02e,$47101d40,$47121d6e
    DC.L    $47114723,$51ee4714,$51ee4715,$47ee4718,$41ee47aa,$2d4847fa,$08070010,$67046100
    DC.L    $00860807,$00116704,$61000066,$47ee4708,$41ee475a,$2d4847fa,$08070002,$67046100
    DC.L    $00fc0807,$00006704,$6100011c,$4e7547ee,$471841ee,$47aa2d48,$47fa0807,$00106704
    DC.L    $61000044,$08070011,$67046100,$00240807,$00126704,$610000c6,$47ee4708,$41ee475a
    DC.L    $2d4847fa,$08070000,$67046100,$00da4e75,$4a2b0009,$660e0884,$00070807,$00036604
    DC.L    $8a2b0008,$4e752413,$362b0004,$082e0007,$01116740,$b63c0001,$661c2f02,$94ae026e ; VIOLATION: orphaned code island at $512C is not reached from known entrypoints
    DC.B    " .G("
    DC.L    $90ae027e,$94803042,$b1c24cdf,$00046620,$60063042,$b1c26618,$4a2b0006,$66126100
    DC.L    $3ac4660c,$177c0001,$00077012,$61003518,$102b0007,$b03c0003,$670003c4,$53006724
    DC.L    $6a064a2e,$012f661c,$00040030,$08070003,$6700c76a,$4a2b0009,$6600c762,$08c50000
    DC.L    $60000414,$08c40005,$08840004,$08070003,$6700c770,$600003b8,$4a2b000b,$66220884
    DC.L    $0006700f,$c02b000a,$e8588840,$7001c02b,$000cea58,$88407003,$c02b000d,$ee588840
    DC.L    $4e7508c4,$00012413,$362b0004,$102b0007,$6642082e,$00000110,$673a2f02,$94ae026e
    DC.B    " .G("
    DC.L    $90ae027e,$94803042,$b1c24cdf,$00046620,$60063042,$b1c26618,$4a2b0006,$66126100
    DC.L    $3a00660c,$177c0001,$00077013,$61003454,$102b0007,$b03c0003,$67000300,$53006710
    DC.L    $6a064a2e,$01306608,$08c40000,$6000c6aa,$08840000,$6000c6c8,$760042ae,$04a46100
    DC.L    $c3786600,$00a8d000,$d000d000,$d002b23c,$002e6740,$b23c002a,$6734b03c,$0008641a
    DC.L    $1740000a,$1743000b,$51eb000c,$51eb000d,$08c70002,$660002c8,$4e755100,$17400008
    DC.L    $17430009,$08c70001,$660002b4,$4e7551eb,$000c603c,$121c4881,$1236107e,$51eb000c
    DC.L    $b23c0057,$670c522b,$000cb23c,$004c6600,$028e121c,$b23c002a,$67161740,$000a51eb
    DC.L    $000d1743,$000b08c7,$00026600,$02724e75,$1743000b,$1740000a,$121c6100,$02f61740
    DC.L    $000d08c7,$00026600,$02564e75,$202e04a4,$6700009e,$41ecffff,$102e04a9,$55006700
    DC.L    $00605300,$6600008a,$10184880,$1036007e,$b03c005a,$6600007a,$10184880,$1036007e
    DC.L    $04000044,$56c2674a,$56006746,$b03c000f,$6600005e,$50c31018,$48801036,$007eb03c
    DC.L    $0043664c,$2848121c,$50eb0008,$17430009,$00870008,$000808c7,$00016600,$01e24e75
    DC.L    $10184880,$1036007e,$7600b03c,$005067c6,$601e1018,$04000030,$6516b03c,$00086410
    DC.L    $50c32848,$121c0202,$0001c142,$6000feb8,$2f0b6100,$b80e265f,$26823743,$00041744
    DC.L    $00067000,$b23c002e,$6624121c,$48811236,$107e7001,$b23c0057,$67127002,$b23c004c
    DC.L    $670a7003,$b23c0042,$66000174,$121c1740,$000708c7,$00006600,$01664e75,$383c01d0
    DC.L    $203b0016,$88404840,$2f0d3ac4,$4ebb0012,$205f0804,$00066704,$08840002,$30844e75
    DC.L    $00180000,$00340000,$00b60000,$00b60000,$007e0000,$00b60000,$4a2b0009,$66000098
    DC.L    $4a2b0008,$6a000090,$7a3a558d,$508f3afc,$fffe4e75,$4a2b0009,$6600007c,$0c2b0002
    DC.L    $00076700,$0072558d,$508f2413,$362b0004,$182b0006,$08850000,$08070003,$660000ec
    DC.L    $7a288a2b,$00084a2e,$00ff6706,$4a436b00,$45283ac2,$4a2e026a,$66002256
    DC.B    "NuJ+",0
    DC.B    $09
    DC.B    "f2J+",0
    DC.B    $0b
    DC.L    $662c0807,$00036626,$422b0003,$8a2b0008,$780fc82b,$000ae85c,$4a2b000c,$670408c4
    DC.L    $000b7003,$c02b000d,$ee588840,$4e750c2b,$00030007,$66602413,$362b0004,$08070002
    DC.L    $67000050,$08070001,$67000048,$08070003,$6600000c,$61b66100,$21e41802,$4e7561b0
    DC.L    $4a2e026a,$672ab63c,$00026718,$241394ae,$026e202e,$472890ae,$027e9480,$610021c4
    DC.L    $18024e75,$4a2e0108,$66e27021,$61002dec,$4e756000,$00220807,$00006704,$6100fbd8
    DC.L    $08070002,$67046100,$fc640807,$00016704,$6100fbae
    DC.B    "Nup[`",0
    DC.B    $2d,$bc
    DC.L    $70446000,$2db64a2e,$026a673e,$4a2e00ff,$67064a43,$6b0043e6,$b63c0002,$67203f04
    DC.L    $0884000f,$6100c2c0,$381f94ae,$026e202e,$472890ae,$027e9480,$3ac26000
    DC.B    "!VJ."
    DC.L    $010866da,$70216100,$2d763ac2,$4e753f04,$4a2e026a
    DC.B    "g2J.",0
    DC.B    $ff,$67,$06
    DC.L    $4a436b00,$ffa0182b,$00066620,$b63c0002,$660c4a2e,$01086606,$701e6100,$2d4694ae
    DC.L    $026e202e,$472890ae,$027e9480,$2ac2381f,$4e7548e7,$38306100,$b5e44a2e,$00ff6704
    DC.B    "JCk(J."
    DC.B    $02,$6a
    DC.L    $6728b63c,$0002661c,$4a046618,$4a826b14,$b4bc0000,$0009640c,$103b2017,$6b064cdf
    DC.L    $0c1c4e75,$705c6100,$2cf24cdf,$0c1c7000,$4e750001,$ff02ffff,$ff034881,$1236107e
    DC.L    $600441f1,$20002248,$34186738,$b2186534,$66f048e7,$4008121c,$48811236,$107eb218
    DC.L    $67f44a20,$67064cdf,$100260d6,$41fa5eb2,$4a301000,$67f0508f,$343120fe,$122cffff
    DC.L    $70004e75,$122cffff,$70ff4e75,$41fa008a
    DC.B    "aFg$A"
    DC.B    $fa,$00,$86
    DC.L    $613e6716,$41fa0089
    DC.B    "a6f."
    DC.L    $1d400135,$b23c002c,$6622121c,$60da1d40,$013460f0,$6100be64,$4a826b12,$b4bc0000
    DC.L    $0008640a,$ee5a3d42,$013260d8
    DC.B    "Nup:`",0
    DC.B    $2c,$40
    DC.L    $43ecffff,$12194881,$1236107e,$10186706,$b20067f0,$4e75b23c,$003d66f8,$2849121c
    DC.L    $4a106a04,$70004e75,$70004881,$1236107e,$141867c6,$5200b401,$66f6121c,$b0004e75
    DC.L    $494400ff
    DC.B    "ROUND",0
    DC.B    "NPMZ",0
    DC.B    "PREC",0
    DC.L    $58445300,$6100d286,$162e026b,$66061d7c,$0007026b,$b63c0004,$6500d284,$4a2e026a
    DC.L    $66522f08,$610006f0,$205f6600,$2bbe48e7,$30006100,$b2724cdf,$000c6700,$2b6245ee
    DC.L    $01702f02,$162e026b,$0603000b,$6100b340
    DC.B    "$_#R",0
    DC.B    $08,$13,$6a
    DC.L    $0004000e,$136a0005,$000f236a,$00060010,$336a000a,$0014122c,$ffff4e75,$6100b230
    DC.L    $66002b3c,$08290006,$000c6600,$2b1a162e,$026b2f09,$61000688,$225f6600
    DC.B    "+V B )",0
    DC.B    $08
    DC.L    $b090663c,$1029000e,$b0280004,$66321029,$000fb028,$00056628,$20290010,$b0a80006
    DC.L    $661e3029,$0014b068,$000a6614,$b629000d,$66002ad0,$08e90006,$000c122c,$ffff4e75
    DC.L    $60002ac8,$8c6e0132,$6000085a,$3a063c3c,$f0488c6e,$01324845,$3a064845,$6000088e
    DC.L    $3c3cf000,$8c6e0132,$3ac66100,$05926620,$b23c002c,$66002ab8,$121c3602,$61000580
    DC.L    $6600008e,$e74b8443,$ef4a3ac2,$600003c2,$41fa0118,$6100fddc
    DC.B    "g0:<@",0
    DC.B    $61,$00
    DC.L    $05ba3ac5,$61000146,$70fd6100,$bce2b23c,$002c6600,$2a7a121c,$61000544,$662cef4a
    DC.L    $206e027e,$85680002,$4e756100,$c986b23c,$002c6600,$2a5a121c,$ec5a0042,$a0003ac2
    DC.L    $610000a6,$703d6000,$bca641fa,$00be6100,$fd826616,$61000096,$206e027e,$ec5a08c2
    DC.L    $000f3142,$00026000,$c94a7057,$60002a44,$3a3c6000,$61000544,$ef4b8a43,$3ac56100
    DC.L    $00cc703d,$6100bc68,$0c2e0005,$026b6702,$4e75b23c,$007b66f8,$121cb23c,$00236726
    DC.L    $6100bcc6,$663c4a00,$66380242,$0007e90a,$08c2000c,$206e027e,$85680002,$b23c007d
    DC.L    $6620121c,$4e75121c,$6100bbec,$b4bcffff,$ffc06d0e,$b4bc0000,$003f6e06,$0242007f
    DC.L    $60d27061,$600029cc,$61000062,$7038c045,$51406702
    DC.B    "Nu n"
    DC.L    $027e0828,$00020002,$67024e75,$705f6000,$29aa000c
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
    DC.L    $00020000,$b23c0023,$6630162e,$026bb63c,$00046526,$121c162e,$026b6100,$04766600
    DC.L    $29460603,$00f51003,$162e026b,$20426100,$65086620,$7a3c6000,$06466100,$bce4ba7c
    DC.L    $00106410,$704e142e,$026b0500,$6606705e,$61002918
    DC.B    "Nu<<"
    DC.L    $f0008c6e,$01323ac6,$102e026b,$b03c0003,$6700011a,$610001fa,$3a3ce000,$610000ce
    DC.L    $662a3ac5,$b23c002c,$660028c4,$121c6100,$ff7c7034,$6100bb18,$61000090,$670c3a28
    DC.L    $00026100,$00943145,$00024e75,$610003b8,$662a08c5,$000be90a,$8a023ac5,$b23c002c
    DC.L    $6600288c,$121c6100,$ff447034,$6100bae0,$61586706,$08e80004,$00024e75,$3afcd000
    DC.L    $6100ff2a,$707d6100,$bac6b23c,$002c6600,$285e121c,$61000370,$6614206e,$027e0242
    DC.L    $000fe94a,$08c2000b,$85680002
    DC.B    "Nu:<"
    DC.L    $d0006100,$0038660c,$611e206e,$027e3145,$00024e75,$70396000
    DC.B    "(Jp8"
    DC.L    $c045206e,$027eb07c,$00204e75,$1005e04d,$7407e210,$e35551ca,$fffa08c5,$000c4e75
    DC.L    $610002d0,$67024e75,$360205c5,$b23c002f,$6608121c,$610002b0,$60eeb23c,$002d661c
    DC.L    $121c6100,$02a2b443,$6d0c07c5,$5243b642,$6ff83602,$60d67039,$600027e8,$70004e75
    DC.L    $3a3ca000,$41fafe38,$6100fafc,$6632ec5a,$8a42b23c,$002f6612,$121c41fa,$fe226100
    DC.L    $fae667ea,$70396000,$27beb23c,$002c6600,$2792121c,$3ac56100,$fe4870ff,$6000b9e4
    DC.L    $3ac56100,$fe3c70ff,$6100b9d8,$b23c002c,$66002770,$121c3a3c,$800041fa,$fde26100
    DC.L    $faa666c0,$ec5a8a42,$b23c002f,$660e121c,$41fafdcc,$6100fa90,$67ea60a8,$206e027e
    DC.L    $31450002,$4e758c6e,$0132102e,$026b6704,$61000052,$3ac6b23c,$00236600,$272e121c
    DC.L    $6100b948,$4a826b08,$b4bc0000,$00406506,$701d6100,$27320242,$003f0042,$5c00b23c
    DC.L    $002c6600,$26fe121c,$36026100,$01baef4a,$86423ac3,$4e758c6e,$01324846,$42462ac6
    DC.L    $720d4e75,$0c2e0007,$026b670e,$4a2e026b,$660026b8,$1d7c0007,$026b4e75,$0c2e0028
    DC.L    $01236600,$d3e43a06,$3c3cf000,$8c6e0132,$48453a06,$48456100,$017a661e,$ec5a8a42
    DC.L    $ed5a61c0,$b23c002c,$6606121c,$61000158,$3ac6ef5a,$8a423ac5,$4e7508c5,$000e6100
    DC.L    $01ae2ac5,$6100fd3a,$70fd6100,$b8d6b23c,$002c6600,$266e121c,$6100012c,$ef4a206e
    DC.L    $027e8568,$00024e75,$8c6e0132,$4a2e0127,$67067065,$61002670,$4a2e026b,$6600262c
    DC.L    $6100b882,$006c4e75,$8c6e0132,$4a2e0127,$67067065,$61002650,$4a2e026b,$6600260c
    DC.L    $6100b862,$00344e75,$3a063c3c,$f0408c6e,$01324845,$3a064845,$60000816,$8c6e0132
    DC.L    $3ac67a30,$610000cc,$662eec5a,$8a426100,$ff14b23c,$002c6600,$25ea121c,$610000a8
    DC.L    $8a42b23c,$003a6600,$c60a121c,$61000098,$ef4a8a42,$3ac54e75,$08c5000e,$610000f0
    DC.L    $3ac56100,$fc7c70fd,$6100b818,$b23c002c,$660025b0,$121c6100,$006e3a02,$b23c003a
    DC.L    $6600c5d0,$121c6100,$005eef4a,$8a42206e,$027e8b68,$00024e75,$3a063c3c,$f0788c6e
    DC.L    $01324845,$3a064845,$2ac56000,$ee5a3a06,$3c3cf000,$8c6e0132,$48453a06,$48456100
    DC.L    $0032660e,$ec5a8a42,$6100fe7a,$3ac63ac5,$4e7508c5,$000e6100,$00762ac5,$6100fc02
    DC.L    $70fd6000,$b79e610a,$66024e75,$70576000,$25521001,$204c4880,$1036007e,$b03c0046
    DC.L    $66341018,$48801036,$007eb03c,$00506626,$14180402,$0030651e,$b43c0008,$64184882
    DC.L    $70001018,$43fa5726,$4a310000,$67081200,$2848b000,$4e7570ff,$4e756100,$b7c0660c
    DC.L    $4a006708,$2848122c,$ffff70ff,$4e757000,$102e026b,$670024b4,$d0408a7b,$00024e75
    DC.L    $18001000,$00001400,$0c000400,$080041ee,$47387800,$42a042a0,$42a04883,$b23c0024
    DC.L    $6700014c,$b23c003a,$67000144,$b23c002d,$67000022,$b23c0030,$6506b23c,$003a6530
    DC.L    $6100b1b0,$b63c000f,$6522b63c,$0013641c,$70004e75,$121c61b6,$66102042,$060300f5
    DC.L    $6100622e,$040300f5,$4a004e75
    DC.B    "pdNu?"
    DC.B    $03,$56,$88
    DC.L    $50c27601,$78ff7a00,$7c000401,$0030660e,$4a05660a,$b63c0001,$67145344,$60106100
    DC.L    $00c050c5,$b63c00ff,$66027600,$d843121c,$b23c002e,$660ab63c,$0001664e,$160560ee
    DC.L    $b23c0030,$6506b23c,$003a65be,$b23c0045,$6706b23c,$00656632,$7600121c,$b23c002d
    DC.L    $57c26602,$121cb23c,$00306516,$b23c003a,$64100401,$00300241,$00ffc6fc,$000ad641
    DC.L    $60e24a02,$67024443,$d84341ee,$472c7c00,$4a056736,$4a446a06,$08d00006,$444450c2
    DC.L    $02840000,$ffff88fc,$03e83a04
    DC.B    "BDHD"
    DC.L    $88fc0064
    DC.B    "a(BDHD"
    DC.B    $88,$fc
    DC.L    $000a611e
    DC.B    "BDHDa"
    DC.B    $18,$12,$2c
    DC.L    $ffff41ee,$472c361f,$61005f6c,$0643000b,$24084a40,$4e751204,$4a026708,$83185206
    DC.L    $46024e75,$bc3c0009,$6706e949,$83104602
    DC.B    "Nu$LC"
    DC.B    $fa,$b2,$ba
    DC.L    $121c4881,$6b0c1431,$10006b06,$70046128,$60ee7000,$103b3019,$67147400,$3f00b07c
    DC.L    $00206d02,$70109157,$610e301f,$66ee60a4
    DC.B    "XP@ ",0
    DC.B    $40,$00,$00
    DC.L    $2f094a40,$671a4840,$4240d100,$484041ee
    DC.B    "G8",$22,"H"
    DC.L    $d388d388,$d3886528,$534066ee,$d1004882,$48c241ee
    DC.B    "G8  "
    DC.L    $d1822080,$74002020,$d1822080,$2020d182,$65062080
    DC.B    $22,"_Nup]a",0
    DC.L    $22f2225f
    DC.B    "Nu BH"
    DC.B    $83,$10,$3b
    DC.L    $30136b08,$3ad85300,$66fa4e75,$70001018,$3ac04e75,$ff010204,$06020600,$4a2e0125
    DC.L    $660a0c2e,$00140123,$6600cfbe,$4a2e0127,$67067065,$610022b0,$102e026b,$6716b03c
    DC.L    $00026710,$b03c0003,$66002260,$08c60006,$6000be28,$6000bec4,$4a2e0125,$660a0c2e
    DC.L    $00140123,$6600cf82,$4a2e0127,$67067065,$61002274,$3a063c3c,$f0484845,$3a064845
    DC.L    $4a2e026b,$66002224,$6100b4f4,$48458a02,$48452ac5,$b23c002c,$66002228,$121c6100
    DC.L    $bf0c6604,$548d4e75,$55824a2e,$00ff6706,$4a436b00,$38706100,$16023ac2,$4e750c2e
    DC.L    $00280123,$66000014
    DC.B    $4a,$2e
h0_633A:
    btst.b d0,-(a7)
    beq.s h0_6344
h0_633E:
    moveq.l #101,d0
    bsr.w h0_8556
h0_6344:
    move.w #$F518,(a5)+
    rts
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $634A is not reached from known entrypoints
    DC.L    $0125660a,$0c2e001e,$01236600,$cf004a2e,$01276706,$70656100,$21f23ac6,$3afc2400
    DC.B    $4e,$75
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $636E is not reached from known entrypoints
    DC.L    $00280123,$6600cee2,$4a2e0127,$67067065,$610021d4,$3ac66100,$b5841005,$02000038
    DC.L    $b03c0010,$660e0205,$0007206e,$027e8a50,$30854e75
    DC.B    $70,$68,$60,$00,$21,$ae ; VIOLATION: orphaned code island at $63A4 is not reached from known entrypoints
    DC.B    $0c,$2e ; VIOLATION: orphaned code island at $63AA is not reached from known entrypoints
    DC.L    $00280123,$6600cea6,$4a2e0127,$67067065,$61002198,$3ac64e75
    DC.L    $0c2e0028,$01236600,$00144a2e,$01276706,$70656100 ; VIOLATION: orphaned code island at $63C4 is not reached from known entrypoints
    DC.B    "!~<<"
    DC.L    $f50860a4
    DC.L    $4a2e0125,$660a0c2e,$001e0123,$6600ce6a,$4a2e0127,$67067065,$6100215c,$343c3000
    DC.L    $3ac66100,$005cb23c,$002c6600,$2126121c,$b23c0023,$66002124,$121c3f02,$6100b33c
    DC.L    $361f4a2e,$012556c0,$02800000,$00080000,$00074a82,$6b04b480,$6f087059,$61002118
    DC.L    $7400eb4a,$8443b23c,$002c6704,$3ac24e75 ; VIOLATION: orphaned code island at $63E0 is not reached from known entrypoints
    DC.L    $121c08c2,$000b3ac2,$6100b314,$00244e75,$b23c0023,$676e4881,$1236107e,$b23c0053
    DC.L    $6740b23c,$00446656,$121c0401,$0030654e,$b23c0008,$6522b23c,$00166706,$b23c0036
    DC.L    $663c121c,$b23c0043,$6706b23c,$0063662e,$00420001,$121c4e75 ; VIOLATION: orphaned code island at $6450 is not reached from known entrypoints
    DC.B    $08,$c1,$00,$03,$84,$01,$12,$1c,$4e,$75 ; VIOLATION: orphaned code island at $64A8 is not reached from known entrypoints
    DC.B    $12,$1c ; VIOLATION: orphaned code island at $64B2 is not reached from known entrypoints
    DC.L    $b23c0046,$6706b23c,$0066660e,$121cb23c,$004367dc,$b23c0063,$67d67059,$60002080
    DC.L    $121c3f02,$6100b280,$4a2e0125,$56c00280,$00000008,$00000007,$4a826b04,$b4806f08
    DC.L    $70596100,$205e7400,$845f08c2,$00044e75 ; VIOLATION: orphaned code island at $64D4 is not reached from known entrypoints
    DC.L    $4a2e0125,$660a0c2e,$00140123,$6600cd46,$4a2e0127,$67067065,$61002038,$343c3400
    DC.L    $6000feda,$4a2e0125,$660a0c2e,$00140123,$6600cd22,$4a2e0127,$67067065,$61002014
    DC.L    $3ac63afc,$a0006100,$b22200fc ; VIOLATION: orphaned code island at $6504 is not reached from known entrypoints
    DC.B    "NuJ."
    DC.L    $0125660a,$0c2e001e,$01236600,$ccf84a2e,$01276706,$70656100,$1fea3afc,$f0003406
    DC.L    $6100feea,$3ac2b23c,$002c6600,$1fb2121c,$6100b1e8,$00244e75,$0c2e001e,$01236600
    DC.L    $ccc44a2e,$01276706,$70656100,$1fb63afc,$f000343c,$01006048,$4a2e0125,$660a0c2e
    DC.L    $001e0123,$6600cc9e,$4a2e0127,$67067065,$61001f90,$3afcf000
    DC.B    "aXf",$22
    DC.L    $08c20009,$3ac2b23c,$002c6600,$1f56121c,$6100f60e
    DC.B    "p?J."
    DC.L    $01256602,$70246000,$b1a27400,$4a2e026b,$67001f20,$3ac26100,$f5f07024,$6100b18c
    DC.L    $b23c002c,$66001f24,$121c6112,$660a206e,$027e8568,$00024e75,$70586000,$1f3241fa
    DC.L    $004e6100,$f24a6644,$10026a1e,$4a2e0125,$660a0c2e,$00140123,$6600cc16,$4a2e0127
    DC.L    $67067065,$61001f08,$60100800,$0006670a,$0c2e001e,$01236600,$cbf84202,$d442d442
    DC.L    $0200003f,$b02e026b,$66001ea8,$4e750008,$41430000,$17820008,$42414300,$1d820008
    DC.L    $42414400,$1c820008,$43414c00,$14810008,$43525000,$13040008,$44525000,$1184000a
    DC.B    "MMUSR",0
    DC.B    $18,$02
    DC.L    $000a5043,$53520000,$19820008,$50535200,$18020008,$53434300,$16810008,$53525000
    DC.L    $12040008,$54430000,$10030008,$54543000,$02430008,$54543100,$03430008,$56414c00
    DC.L    $2b810000,$4a2e0125,$660a0c2e,$00140123,$6600cb56,$4a2e0127,$67067065,$61001e48
    DC.L    $6100b062,$006c4e75,$4a2e0125,$660a0c2e,$00140123,$6600cb32,$4a2e0127,$67067065
    DC.L    $61001e24,$3a063c3c,$f0404845,$3a064845,$2ac56100,$bd3450ee,$026d6100,$b022003d
    DC.L    $4e750c2e,$00280123,$66000024,$4a2e0127,$67067065,$61001df0,$08060009,$66083c3c
    DC.L    $f5486000,$fc103c3c,$f5686000,$fc084a2e,$0125660a,$0c2e001e,$01236600,$cacc4a2e
    DC.L    $01276706,$70656100,$1dbe4a2e,$026b6600,$1d7a3afc,$f0003406,$6100fcb6,$3ac2b23c
    DC.L    $002c6600,$1d7e121c,$6100afb4,$0024b23c,$002c6600,$1d6e121c,$b23c0023,$66001d6c
    DC.L    $121c6100,$af864a82,$6b08b4bc,$00000008,$6508701d,$61001d70,$7400ec5a,$b23c002c
    DC.L    $6614121c,$36026100,$b00008c3,$00080242,$0007eb4a,$8443206e,$027e8568,$00024e75
    DC.L    $4a2e0125,$660a0c2e,$00140123,$6600ca3a,$4a2e0127,$67067065,$61001d2c,$3afcf078
    DC.L    $3ac66000,$e5e24a2e,$0125660a,$0c2e0014,$01236600,$ca144a2e,$01276706,$70656100
    DC.L    $1d063afc,$f0006100,$afb46624,$4a00671a,$363c2c00,$86023ac3,$b23c002c,$66001cc4
    DC.L    $121c6100,$aefa0024,$4e75700e,$60001cd8,$48811236,$107eb23c,$005666ee,$121c4881
    DC.L    $1236107e,$b23c0041,$66e0121c,$48811236,$107eb23c,$004c66d2,$121c3afc,$280060b8
    DC.L    $0c2e0020,$01236600,$c9a03ac6,$4e750c2e,$00200123,$6600c992,$b23c0023,$66001c6c
    DC.L    $121c3afc,$f8003ac6,$6100b23e,$6000bf8e,$0c2e0020,$01236600,$c9706100,$e70c3afc
    DC.L    $f8003ac6,$6100ae78,$0065206e,$027e3010,$02000038,$6618b23c,$003a6600,$bc56121c
    DC.L    $6100aedc,$206e027e,$85280003,$600608e8,$00000002,$b23c002c,$66001c08,$121c6100
    DC.L    $aebe206e,$027ee90a,$85280002,$4e750c2e,$00280123,$6600c912,$4a2e0127,$67067065
    DC.L    $61001c04,$41fa001c,$6100ef1c,$8c423ac6,$4e7561da,$b23c002c,$66001bc8,$121c6000
    DC.L    $fa160008,$42430000,$00c00008,$44430000,$00400008,$49430000,$00800008,$4e430000
    DC.L    $00000000,$0c2e0028,$01236600,$b7963ac6,$6100af6a,$b23c002c,$66001b88,$121c1005
    DC.L    $0200003f,$b03c0039,$676a0200,$0030b03c,$00106600,$1b6a3f05,$6100af42,$30050200
    DC.L    $0038b03c,$00186630,$10050240,$0007e858,$00408000,$3ac03a1f,$08c50005,$08050003
    DC.L    $67001b3c,$02450027,$206e027e,$30100240,$ffc08a40,$30854e75,$30050240,$003fb03c
    DC.L    $00396600,$1b1a3a1f,$08050003,$67da0245,$000760d4,$6100aee6,$30050240,$0038b03c
    DC.L    $0010660a,$70180245,$00078a40,$60bab03c,$00186600,$1aea7008,$60ec7037,$60001b04
    DC.L    $1401b23c,$00226706,$b23c0027,$66ec244c,$121cb23c,$000d67e2,$b20266f4,$121cb202
    DC.L    $67ee280c,$988a5344,$b23c002c,$66001ab4,$121c1601,$b23c0027,$6706b23c,$002266ba
    DC.L    $53446506,$b50c67f8,$4e75700d,$c141b003,$6606528c,$121c7000,$4e7561a4,$57c06000
    DC.L    $00e4619c,$56c06000,$00dc6100,$aa60671e,$6100a14c,$66184a2e,$026a6712,$1029000c
    DC.L    $08000007,$67080200,$0040b03c,$00404e75,$41ee041e,$61000c40,$66001a6c,$61cc57c0
    DC.L    $600000a2,$41ee041e,$61000c2c,$66001a58,$61b856c0,$6000008e,$50ee015e,$6100a2e8
    DC.L    $51ee015e,$4a2e00ff,$67044a43,$6b324a04
    DC.B    "f.Nua"
    DC.B    $e2,$b6,$3c
    DC.L    $00026724,$4e7550ee,$015e6100,$a2c251ee,$015e4a2e,$00ff6704,$4a436b0c,$b63c0001
    DC.L    $67064a04,$66024e75,$703e6000,$19fe61d6,$1d7c003d,$46f52d42,$46f64e75,$70336000
    DC.B    $19,$ea
h0_6B6A:
    move.w #$34,d0
    bra.w h0_853E
    DC.B    $61,$e2,$5e,$c0,$60,$1c ; VIOLATION: orphaned code island at $6B72 is not reached from known entrypoints
    DC.B    $61,$dc,$5c,$c0,$60,$16 ; VIOLATION: orphaned code island at $6B78 is not reached from known entrypoints
    DC.B    $61,$d6,$5d,$c0,$60,$10 ; VIOLATION: orphaned code island at $6B7E is not reached from known entrypoints
    DC.B    $61,$d0,$5f,$c0,$60,$0a ; VIOLATION: orphaned code island at $6B84 is not reached from known entrypoints
    DC.B    $61,$ca,$57,$c0,$60,$04 ; VIOLATION: orphaned code island at $6B8A is not reached from known entrypoints
    DC.L    $61c456c0 ; VIOLATION: orphaned code island at $6B90 is not reached from known entrypoints
    DC.B    "RnG8J",0
    DC.B    $67,$08
    DC.L    $61000170,$720d4e75
    DC.L    $61000168,$61009c7e ; VIOLATION: orphaned code island at $6BA4 is not reached from known entrypoints
    DC.B    ">.G8a",0
    DC.B    $9b,$12
    DC.L    $66b46174,$676c4a82,$6718b2bc
    DC.B    "ELSEf`"
    DC.B    $b4,$bc
    DC.L    $49460000,$6658be6e,$473867c8
    DC.B    $60,$50
    DC.B    $b2,$bc ; VIOLATION: orphaned code island at $6BD6 is not reached from known entrypoints
    DC.B    "ELSEg"
    DC.B    $f0,$b2,$bc
    DC.B    "ENDCg"
    DC.B    $12,$b2,$bc
    DC.B    "ENDMf"
    DC.B    $1e,$4a,$2e
    DC.L    $01026732,$60000700
    DC.B    $30,$2e,$47,$38,$53,$6e,$47,$38,$be,$40,$66,$22,$60,$96 ; VIOLATION: orphaned code island at $6BF8 is not reached from known entrypoints
    DC.B    $61,$00,$00,$e0,$60,$1a ; VIOLATION: orphaned code island at $6C06 is not reached from known entrypoints
    DC.L    $4841b27c,$49466612,$484141fa,$08b23018,$6708b240,$66f8526e,$47386100,$9c006084 ; VIOLATION: orphaned code island at $6C0C is not reached from known entrypoints
    DC.L    $121cb23c,$000d6700,$0094b23c,$0009672e,$b23c0020,$6728b23c,$002a6700,$0080b23c
    DC.L    $003b6778,$121cb23c,$000d6770,$b23c0009,$670cb23c,$00206706,$b23c003a,$66e6121c
    DC.L    $b23c000d,$6756b23c,$000967f2,$b23c0020,$67ecb23c,$002a6744,$b23c003b,$673e41ee
    DC.L    $05de42a0,$42a07007 ; VIOLATION: orphaned code island at $6C2C is not reached from known entrypoints
    DC.B    $60,$1a
    DC.B    $12,$1c ; VIOLATION: orphaned code island at $6C96 is not reached from known entrypoints
    DC.L    $b23c000d,$6722b23c,$0009671c,$b23c0020,$6716b23c,$002e6710,$48811236,$107e10c1
    DC.L    $51c8ffdc,$70004e75
    DC.B    $4c,$ee,$00,$06,$05,$d6,$70,$ff,$4e,$75 ; VIOLATION: orphaned code island at $6CC0 is not reached from known entrypoints
    DC.B    "0.G8g" ; VIOLATION: orphaned code island at $6CCA is not reached from known entrypoints
    DC.B    $18
    DC.L    $4a2e0102,$670a246e,$473cb06a,$000e6708
    DC.B    "SnG8`",0
    DC.B    $fe,$b6
    DC.B    $70,$30,$60,$00,$18,$6a ; VIOLATION: orphaned code island at $6CE8 is not reached from known entrypoints
    DC.B    "0.G8g" ; VIOLATION: orphaned code island at $6CEE is not reached from known entrypoints
    DC.B    $14
    DC.L    $4a2e0102,$670a246e,$473cb06a,$000e6704,$6000fe9e
    DC.B    $70,$31,$60,$00,$18,$4a ; VIOLATION: orphaned code island at $6D08 is not reached from known entrypoints
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $6D0E is not reached from known entrypoints
    DC.L    $01286722,$4a2e026a,$661c4a2e,$01026706,$4a2e0119,$6710302e,$47380600,$00301d40
    DC.L    $46f56000
    DC.B    "&HNu",$22,"<",0
    DC.B    $00
    DC.L    $13883d41,$01546100,$24022d48,$01504e75,$70366000,$18064a2e,$010266f4,$4aae474a
    DC.L    $66ee6100,$be94246e,$017848e7,$000c6100,$9e5c56c0,$4cdf3000,$4a2e026a,$660000ee
    DC.L    $4a006700,$17867608,$42846100,$9f724869,$0008102e,$026b670c,$b03c0001,$670608e9
    DC.L    $0003000c,$206e0150,$0c6e0110,$01546402,$618a225f,$228842a8,$000843e8,$00102089
    DC.L    $21490004,$2148000c,$2d490150,$046e0010,$01542648,$61009a5e,$610098da,$6600fd90
    DC.L    $61306100,$fe4c67ec,$b2bc454e,$444d66e4,$4a8266e0,$206b000c,$216e0150,$0004720d
    DC.L    $082e0000,$01536708,$536e0154,$52ae0150,$4e750c6e,$01020154
    DC.B    "d4 k",0
    DC.B    $0c,$21,$6e
    DC.L    $01500004,$6100ff16,$226b000c,$23480008,$2748000c,$43e8000c,$208942a8,$000442a8
    DC.L    $0008700c,$d0c0d1ae,$0150916e,$0154206e,$0150224c,$720d1019,$10c0b200,$66f82d48
    DC.L    $01502409,$948c956e,$01544e75,$4a006600,$169e0c29,$0008000d,$66001690,$08e90006
    DC.L    $000c6600,$16866100,$9a906100,$98286600,$fcde6100,$fd9c67ee,$b2bc454e,$444d66e6
    DC.L    $4a8266e2,$720d4e75
h0_6EA4:
    move.l #$1F40,d1
    move.w d1,$4740(a6)
    bsr.w h0_9146
h0_6EB2:
    move.l a0,$4742(a6)
    rts
h0_6EB8:
    moveq.l #78,d0
    bra.w h0_853E
h0_6EBE:
    cmpi.w #580,$4740(a6)
    bcs.s h0_6EB8
h0_6EC6:
    movem.l d1/a1,-(a7)
    btst.b #3,$000C(a1)
    beq.s h0_6ED8
h0_6ED2:
    bsr.w h0_0CA4
h0_6ED6:
    bra.s h0_6EDC
h0_6ED8:
    bsr.w h0_0C84
h0_6EDC:
    movem.l (a7)+,d1/a1
    tst.b $026A(a6)
    beq.s h0_6EF0
h0_6EE6:
    btst.b #6,$000C(a1)
    beq.w h0_851E
h0_6EF0:
    moveq.l #87,d0
    cmp.b #$D,d1
    beq.s h0_6F0E
h0_6EF8:
    cmp.b #$9,d1
    beq.s h0_6F0E
h0_6EFE:
    cmp.b #$20,d1
    beq.s h0_6F0E
h0_6F04:
    cmp.b #$2E,d1
    bne.w h0_8516
h0_6F0C:
    moveq.l #0,d0
h0_6F0E:
    movea.l $4742(a6),a0
    sf.b $000C(a0)
    move.l $473C(a6),(a0)
    move.l a0,$473C(a6)
    move.w $473A(a6),$000A(a0)
    movea.l $0008(a1),a1
    move.l a1,$0004(a0)
    move.l (a1),$0010(a0)
    move.w $4738(a6),$000E(a0)
    lea.l $0008(a0),a1
    clr.w (a1)
    lea.l $0116(a0),a0
    move.b d0,(a0)+
    bne.s h0_6F60
h0_6F44:
    subq.l #1,a0
h0_6F46:
    move.b (a4)+,d1
    cmp.b #$D,d1
    beq.s h0_6F60
h0_6F4E:
    cmp.b #$9,d1
    beq.s h0_6F5E
h0_6F54:
    cmp.b #$20,d1
    beq.s h0_6F5E
h0_6F5A:
    move.b d1,(a0)+
    bra.s h0_6F46
h0_6F5E:
    move.b (a4)+,d1
h0_6F60:
    clr.b (a0)+
h0_6F62:
    cmp.b #$D,d1
    beq.w h0_6FEA
h0_6F6A:
    cmp.b #$2A,d1
    beq.s h0_6FEA
h0_6F70:
    cmp.b #$3B,d1
    beq.s h0_6FEA
h0_6F76:
    cmp.b #$9,d1
    beq.s h0_6F82
h0_6F7C:
    cmp.b #$20,d1
    bne.s h0_6F86
h0_6F82:
    move.b (a4)+,d1
    bra.s h0_6F62
h0_6F86:
    addq.w #1,(a1)
    cmp.b #$2C,d1
    beq.s h0_6FD4
h0_6F8E:
    cmp.b #$D,d1
    beq.s h0_6FD4
h0_6F94:
    cmp.b #$3C,d1
    bne.s h0_6FB6
h0_6F9A:
    move.b (a4)+,d1
    beq.s h0_6F9A
h0_6F9E:
    cmp.b #$D,d1
    beq.s h0_6FD4
h0_6FA4:
    cmp.b #$3E,d1
    bne.s h0_6FB2
h0_6FAA:
    move.b (a4)+,d1
    cmp.b #$3E,d1
    bne.s h0_6FD4
h0_6FB2:
    move.b d1,(a0)+
    bra.s h0_6F9A
h0_6FB6:
    move.b d1,(a0)+
h0_6FB8:
    move.b (a4)+,d1
    beq.s h0_6FB8
h0_6FBC:
    cmp.b #$D,d1
    beq.s h0_6FD4
h0_6FC2:
    cmp.b #$9,d1
    beq.s h0_6FD4
h0_6FC8:
    cmp.b #$20,d1
    beq.s h0_6FD4
h0_6FCE:
    cmp.b #$2C,d1
    bne.s h0_6FB6
h0_6FD4:
    clr.b (a0)+
    cmp.b #$2C,d1
    bne.s h0_6FEA
h0_6FDC:
    move.b (a4)+,d1
    cmp.b #$D,d1
    bne.s h0_6F86
h0_6FE4:
    bra.s h0_7016
h0_6FE6:
    move.l (a7)+,$473C(a6)
h0_6FEA:
    move.l a0,d0
    addq.l #1,d0
    bclr #0,d0
    move.l $4742(a6),-(a7)
    move.l d0,$4742(a6)
    sub.l (a7)+,d0
    sub.w d0,$4740(a6)
    move.w $4752(a6),d0
    bne.s h0_700A
h0_7006:
    st.b $011A(a6)
h0_700A:
    st.b $0102(a6)
    addq.w #1,d0
    move.w d0,$4752(a6)
    rts
h0_7016:
    movea.l $473C(a6),a2
    move.l a2,-(a7)
    move.l (a2),$473C(a6)
    movem.l a0-a1,-(a7)
    bsr.w h0_062A
h0_7028:
    movem.l (a7)+,a0-a1
    bne.s h0_6FE6
h0_702E:
    cmp.b #$26,d0
    bne.s h0_6FE6
h0_7034:
    movem.l a0-a1,-(a7)
    bsr.w h0_0828
h0_703C:
    bsr.w h0_06C4
h0_7040:
    movem.l (a7)+,a0-a1
    movea.l (a7)+,a2
    bne.w h0_6B6A
h0_704A:
    move.l a2,$473C(a6)
    move.b (a4)+,d1
    cmp.b #$26,d1
    beq.s h0_705C
h0_7056:
    moveq.l #70,d0
    bsr.w h0_8556
h0_705C:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s h0_705C
h0_7064:
    cmp.b #$20,d1
    beq.s h0_705C
h0_706A:
    bra.w h0_6F86
h0_706E:
    move.w $4752(a6),d0
    cmp.w $4754(a6),d0
    bhi.s h0_7092
h0_7078:
    bsr.w h0_749E
h0_707C:
    movea.l a4,a0
    movea.l $473C(a6),a2
    lea.l $0014(a2),a1
    moveq.l #0,d2
    bra.w h0_716E
h0_708C:
    tst.l $474A(a6)
    bne.s h0_706E
h0_7092:
    movea.l $473C(a6),a2
    movea.l $0004(a2),a1
    movea.l $0010(a2),a0
    cmpa.l $0004(a1),a0
    bne.s h0_70AE
h0_70A4:
    movea.l $0008(a1),a1
    move.l a1,$0004(a2)
    movea.l (a1),a0
h0_70AE:
    moveq.l #13,d0
    movea.l a0,a4
    moveq.l #92,d2
h0_70B4:
    move.b (a0)+,d1
    cmp.b d0,d1
    beq.s h0_70C0
h0_70BA:
    cmp.b d2,d1
    bne.s h0_70B4
h0_70BE:
    bra.s h0_70DC
h0_70C0:
    tst.l $474A(a6)
    beq.s h0_70D0
h0_70C6:
    move.w $4752(a6),d0
    cmp.w $4754(a6),d0
    bls.s h0_70D4
h0_70D0:
    move.l a0,$0010(a2)
h0_70D4:
    move.l a4,$0272(a6)
    moveq.l #0,d0
    rts
h0_70DC:
    lea.l $0014(a2),a1
    move.l a0,d2
    sub.l a4,d2
    subq.w #1,d2
    beq.s h0_70F6
h0_70E8:
    move.l a0,d1
    move.w d2,d0
    movea.l a4,a0
h0_70EE:
    move.b (a0)+,(a1)+
    subq.w #1,d0
    bne.s h0_70EE
h0_70F4:
    movea.l d1,a0
h0_70F6:
    move.b (a0)+,d1
    cmp.b #$D,d1
    beq.w h0_7188
h0_7100:
    cmp.b #$40,d1
    beq.w h0_71F2
h0_7108:
    cmp.b #$3C,d1
    beq.w h0_7258
h0_7110:
    cmp.b #$3F,d1
    beq.w h0_719E
h0_7118:
    moveq.l #48,d0
    cmp.b d0,d1
    bcs.s h0_7194
h0_711E:
    cmp.b #$3A,d1
    bcs.s h0_7140
h0_7124:
    moveq.l #55,d0
    cmp.b #$41,d1
    bcs.s h0_7168
h0_712C:
    cmp.b #$5B,d1
    bcs.s h0_7140
h0_7132:
    moveq.l #87,d0
    cmp.b #$61,d1
    bcs.s h0_7168
h0_713A:
    cmp.b #$7B,d1
    bcc.s h0_7168
h0_7140:
    sub.b d0,d1
    move.l a0,-(a7)
    lea.l $0116(a2),a0
    ext.w d1
    beq.s h0_715A
h0_714C:
    cmp.w $0008(a2),d1
    bgt.s h0_7164
h0_7152:
    tst.b (a0)+
    bne.s h0_7152
h0_7156:
    subq.w #1,d1
    bne.s h0_7152
h0_715A:
    addq.b #1,d2
    beq.s h0_7180
h0_715E:
    move.b (a0)+,(a1)+
    bne.s h0_715A
h0_7162:
    subq.l #1,a1
h0_7164:
    movea.l (a7)+,a0
    bra.s h0_716E
h0_7168:
    addq.b #1,d2
    beq.s h0_7182
h0_716C:
    move.b d1,(a1)+
h0_716E:
    move.b (a0)+,d1
    cmp.b #$D,d1
    beq.s h0_7188
h0_7176:
    cmp.b #$5C,d1
    bne.s h0_7168
h0_717C:
    bra.w h0_70F6
h0_7180:
    movea.l (a7)+,a0
h0_7182:
    cmpi.b #13,(a0)+
    bne.s h0_7182
h0_7188:
    move.b #$D,(a1)+
    lea.l $0014(a2),a4
    bra.w h0_70C0
h0_7194:
    cmp.b #$23,d1
    beq.w h0_72D2
h0_719C:
    bra.s h0_7168
h0_719E:
    move.b (a0)+,d1
    moveq.l #48,d0
    cmp.b d0,d1
    bcs.s h0_7194
h0_71A6:
    cmp.b #$3A,d1
    bcs.s h0_71C8
h0_71AC:
    moveq.l #55,d0
    cmp.b #$41,d1
    bcs.s h0_7168
h0_71B4:
    cmp.b #$5B,d1
    bcs.s h0_71C8
h0_71BA:
    moveq.l #87,d0
    cmp.b #$61,d1
    bcs.s h0_7168
h0_71C2:
    cmp.b #$7B,d1
    bcc.s h0_7168
h0_71C8:
    sub.b d0,d1
    move.l a0,-(a7)
    lea.l $0116(a2),a0
    ext.w d1
    beq.s h0_71E2
h0_71D4:
    cmp.w $0008(a2),d1
    bgt.s h0_71EC
h0_71DA:
    tst.b (a0)+
    bne.s h0_71DA
h0_71DE:
    subq.w #1,d1
    bne.s h0_71DA
h0_71E2:
    moveq.l #0,d1
h0_71E4:
    tst.b (a0)+
    beq.s h0_71EE
h0_71E8:
    addq.l #1,d1
    bra.s h0_71E4
h0_71EC:
    moveq.l #0,d1
h0_71EE:
    bra.w h0_7226
h0_71F2:
    tst.b $000C(a2)
    bne.s h0_7204
h0_71F8:
    st.b $000C(a2)
    addq.w #1,$473A(a6)
    addq.w #1,$000A(a2)
h0_7204:
    cmp.b #$F9,d2
    bcc.w h0_7182
h0_720C:
    addq.b #1,d2
    move.b #$5F,(a1)+
    move.l a0,-(a7)
    moveq.l #0,d1
    move.w $000A(a2),d1
    cmp.w #$A,d1
    bcs.s h0_7244
h0_7220:
    cmp.w #$64,d1
    bcs.s h0_724A
h0_7226:
    movem.l d4/a2-a3,-(a7)
    movea.l a1,a3
    move.w d2,d4
    lea.l h0_7252(pc),a2
    bsr.w h0_8F8E
h0_7236:
    movea.l a3,a1
    move.w d4,d2
    movem.l (a7)+,d4/a2-a3
    movea.l (a7)+,a0
    bra.w h0_716E
h0_7244:
    addq.b #1,d2
    move.b #$30,(a1)+
h0_724A:
    addq.b #1,d2
    move.b #$30,(a1)+
    bra.s h0_7226
h0_7252:
    addq.b #1,d4
    move.b d1,(a3)+
    rts
h0_7258:
    cmp.b #$F5,d2
    bcc.w h0_7182
h0_7260:
    move.b (a0)+,d1
    movem.l d2/d4/a0-a4,-(a7)
    cmp.b #$24,d1
    seq.b d4
    bne.s h0_7276
h0_726E:
    move.b (a0)+,d1
    bra.s h0_7276
h0_7272:
    move.l d2,d1
    bra.s h0_7298
h0_7276:
    movea.l a0,a4
    lea.l $041E(a6),a0
    bsr.w h0_7726
h0_7280:
    bne.s h0_72C4
h0_7282:
    cmp.b #$3E,d1
    bne.s h0_72C4
h0_7288:
    bsr.w h0_151C
h0_728C:
    beq.s h0_7272
h0_728E:
    bsr.w h0_0C0E
h0_7292:
    bne.s h0_72C4
h0_7294:
    move.l $0008(a1),d1
h0_7298:
    movea.l $000C(a7),a3
    lea.l h0_7252(pc),a2
    tst.b d4
    beq.s h0_72AC
h0_72A4:
    move.l (a7),d4
    bsr.w h0_8F5E
h0_72AA:
    bra.s h0_72B2
h0_72AC:
    move.l (a7),d4
    bsr.w h0_8F8E
h0_72B2:
    move.l a3,d1
    move.w d4,d2
    move.l a4,d3
    movem.l (a7)+,d0/d4/a0-a4
    movea.l d1,a1
    movea.l d3,a0
    bra.w h0_716E
h0_72C4:
    movem.l (a7)+,d2/d4/a0-a4
    moveq.l #73,d0
    bsr.w h0_8556
h0_72CE:
    bra.w h0_716E
h0_72D2:
    cmp.b #$FC,d2
    bcc.w h0_7182
h0_72DA:
    moveq.l #0,d1
    move.w $0008(a2),d1
    move.l a0,-(a7)
    bra.w h0_7226
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $72E6 is not reached from known entrypoints
    DC.L    $01026754
    DC.B    "$nG<=j",0
    DC.B    $0e
    DC.B    "G8J."
    DC.L    $01026744,$4a2e0119,$660450ee,$0115536e
    DC.B    "GR$nG< "
    DC.B    $0a
    DC.L    $90ae4742,$916e4740
    DC.B    "-JGB0*",0
    DC.B    $0e
    DC.L    $b06e4738,$670a3d40,$4738700a,$61001332,$20122d40,$473c6604,$51ee0102,$720d4e75
    DC.B    $70,$35,$60,$00,$12,$12 ; VIOLATION: orphaned code island at $7340 is not reached from known entrypoints
    DC.B    $70,$3b,$60,$00,$11,$f4 ; VIOLATION: orphaned code island at $7346 is not reached from known entrypoints
    DC.L    $282e026e,$41ee041e,$4a906704,$6100996a,$4aae474a,$66000036,$6100f7c8 ; VIOLATION: orphaned code island at $734C is not reached from known entrypoints
    DC.B    "-BGFn0a",0
    DC.L    $94b86100,$93506600,$f7f26100,$f8b067ee,$4a8266ea,$b2bc5245,$5054670c,$b2bc454e
    DC.L    $445266da,$720d4e75
    DC.B    $70,$47,$60,$00,$11,$ba ; VIOLATION: orphaned code island at $7398 is not reached from known entrypoints
    DC.B    $20,$6e ; VIOLATION: orphaned code island at $739E is not reached from known entrypoints
    DC.L    $01500c6e,$01100154,$64046100,$f98c2d48
    DC.B    "GJ?."
    DC.L    $015442a8,$000843e8,$00102089,$21490004,$2148000c,$2d490150,$046e0010,$01542648
    DC.L    $61009452,$42ae474a,$610092e6,$6600f788
    DC.B    "-KGJa",0
    DC.B    $fa,$24
    DC.L    $6100f83e,$67e2b2bc
    DC.B    "ENDRf"
    DC.B    $da,$4a,$82
    DC.L    $66d66100,$942850ee,$0115206b,$000c216e,$01500004,$082e0000,$01536714,$536e0154
    DC.L    $52ae0150,$4a2e0102,$67063d6e
    DC.B    "GRGTS"
    DC.B    $ae
    DC.B    "GFe<-KGJC"
    DC.B    $eb
    DC.L    $00102d49,$474e6100,$92846600,$f72648e7,$00186100,$f7e04cdf,$1800670c,$b2bc454e
    DC.L    $44526604,$4a8267cc,$50ee0115,$2f0b6100,$9598265f
    DC.B    $60,$d0
    DC.B    $30,$1f ; VIOLATION: orphaned code island at $746E is not reached from known entrypoints
    DC.L    $342e0154,$4aab0008,$67027000,$9440956e,$015448c2,$d5ae0150,$42ae474a,$41fa2656
    DC.L    $2d4801a8,$720d4e75
    DC.B    $70,$48,$60,$00,$10,$ba ; VIOLATION: orphaned code island at $7498 is not reached from known entrypoints
h0_749E:
    movea.l $474A(a6),a1
    movea.l $474E(a6),a0
    cmpa.l $0004(a1),a0
    bne.s h0_74B6
h0_74AC:
    movea.l $0008(a1),a1
    move.l a1,$474A(a6)
    movea.l (a1),a0
h0_74B6:
    movea.l a0,a4
    moveq.l #13,d0
h0_74BA:
    cmp.b (a0)+,d0
    bne.s h0_74BA
h0_74BE:
    move.l a0,$474E(a6)
    move.l a4,$0272(a6)
    moveq.l #0,d0
    rts
    DC.B    "NEEQC",0
    DC.L    $4e434400
    DC.B    "NDGTGELTLE",0
    DC.B    $00
h0_74E0:
    move.l d2,-(a7)
    bra.w h0_0B28
dat_74E6:
    DC.B    $00,$00,$0e,$36,$00,$00
h0_74EC:
    lea.l dat_74E6(pc),a0
    tst.b $00FF(a6)
    beq.s h0_7504
h0_74F6:
    tst.b $026A(a6)
    beq.s h0_7504
h0_74FC:
    bsr.w h0_98A6
h0_7500:
    move.b -$0001(a4),d1
h0_7504:
    moveq.l #0,d0
    bra.w h0_759C
h0_750A:
    tst.b $00FF(a6)
    beq.s h0_751E
h0_7510:
    tst.b $026A(a6)
    beq.s h0_751E
h0_7516:
    bsr.w h0_98A6
h0_751A:
    move.b -$0001(a4),d1
h0_751E:
    cmp.b #$2E,d1
    bne.s h0_7570
h0_7524:
    move.b (a4)+,d1
    bmi.s h0_7540
h0_7528:
    ext.w d1
    lea.l dat_75E6(pc),a1
    adda.w d1,a1
    move.b $0005(a0),d0
    bne.s h0_7544
h0_7536:
    move.b (a1),d0
    bmi.s h0_7564
h0_753A:
    cmp.b #$4,d0
    bcs.s h0_7586
h0_7540:
    bra.w h0_851A
h0_7544:
    bmi.s h0_7554
h0_7546:
    tst.b $0124(a6)
    bne.w h0_7554
h0_754E:
    subq.w #1,d0
h0_7550:
    beq.s h0_74E0
h0_7552:
    bra.s h0_7536
h0_7554:
    move.b (a1),d0
    bpl.s h0_7586
h0_7558:
    addq.w #2,d0
    beq.s h0_7582
h0_755C:
    addq.b #1,d0
    bne.s h0_7540
h0_7560:
    moveq.l #6,d0
    bra.s h0_759C
h0_7564:
    addq.b #2,d0
    beq.s h0_7582
h0_7568:
    addq.b #1,d0
    bne.s h0_7540
h0_756C:
    moveq.l #1,d0
    bra.s h0_7586
h0_7570:
    move.b $0005(a0),d0
    subq.w #1,d0
    bne.s h0_757E
h0_7578:
    tst.b $0124(a6)
    beq.s h0_7550
h0_757E:
    moveq.l #0,d0
    bra.s h0_759C
h0_7582:
    moveq.l #2,d0
    subq.l #1,a4
h0_7586:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s h0_759C
h0_758E:
    cmp.b #$20,d1
    beq.s h0_759C
h0_7594:
    cmp.b #$D,d1
    bne.w h0_851A
h0_759C:
    cmp.b #$D,d1
    beq.s h0_75B0
h0_75A2:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s h0_759C
h0_75AA:
    cmp.b #$20,d1
    beq.s h0_759C
h0_75B0:
    move.b d0,$026B(a6)
    sf.b $026D(a6)
    move.w (a0)+,d6
    move.w (a0)+,d3
    move.w (a0)+,d2
    pea.l dat_7682(pc)
    lea.l dat_1DCE(pc),a0
    adda.w d3,a0
    move.l a0,-(a7)
    move.w d1,-(a7)
    btst #15,d2
    beq.s h0_75D8
h0_75D2:
    bsr.w h0_0CA4
h0_75D6:
    bra.s h0_75E2
h0_75D8:
    btst #14,d2
    beq.s h0_75E2
h0_75DE:
    bsr.w h0_0C84
h0_75E2:
    move.w (a7)+,d1
    rts
dat_75E6:
    DC.B    $ff,$ff
    DC.L    $ffffffff,$fffffffe,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$fffffeff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $01ff04ff,$ffffffff,$ffff03ff,$ffff05ff,$fffdffff,$ff0207ff,$ffffffff,$ffffffff
    DC.L    $01ff04ff,$ffffffff,$ffff03ff,$ffff05ff,$fffdffff,$ff0207ff,$ffffffff,$ffff4a2e
    DC.L    $01276706,$70656100,$0ee63ac6,$720d4e75,$206e01a8,$42ae01a8
    DC.B    $4e,$d0
dat_7682:
    DC.B    $b2,$3c
    DC.L    $000d671e,$b23c0009,$6718b23c,$00206712,$b23c002a,$670cb23c,$003b6706,$700e6100
    DC.L    $0eb24aae,$01a866cc,$4aae01bc,$671a222e,$01bc42ae,$01bcd3ae,$026e4a81,$6b04d3ae
    DC.L    $025642ae,$01b04e75,$220d92ae,$027e2d41,$01b06714,$242e026e,$d3ae026e,$d3ae0256
    DC.L    $4a2e026a,$660021e4
    DC.B    $4e,$75
h0_76EE:
    bsr.s h0_7726
h0_76F0:
    bne.s h0_770E
h0_76F2:
    movea.l (a0),a1
    move.b $0005(a0),d0
    moveq.l #46,d2
    addq.l #1,a1
    bra.s h0_7702
h0_76FE:
    cmp.b (a1)+,d2
    beq.s h0_7710
h0_7702:
    subq.b #1,d0
    bne.s h0_76FE
h0_7706:
    move.b $0005(a0),d2
    movea.l a4,a1
    moveq.l #0,d0
h0_770E:
    rts
h0_7710:
    movea.l a4,a1
    move.b $0005(a0),d2
    sub.b d0,$0005(a0)
    ext.w d0
    suba.w d0,a4
    move.b -$0001(a4),d1
    moveq.l #0,d0
    rts
h0_7726:
    andi.w #255,d1
    lea.l dat_B75C(pc),a2
    tst.b $0(a2,d1.w)
    beq.s h0_7762
h0_7734:
    bpl.s h0_77A4
h0_7736:
    move.b (a4),d1
    ext.w d1
    move.b $7E(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s h0_7750
h0_7744:
    cmp.b #$42,d1
    beq.s h0_7750
h0_774A:
    cmp.b #$4C,d1
    bne.s h0_775E
h0_7750:
    move.b $0001(a4),d1
    tst.b $0(a2,d1.w)
    ble.s h0_775E
h0_775A:
    moveq.l #46,d1
    bra.s h0_77A4
h0_775E:
    moveq.l #46,d1
    bra.s h0_77AA
h0_7762:
    cmp.b #$3A,d1
    bcc.s h0_77AA
h0_7768:
    lea.l -$0001(a4),a1
    movea.l a4,a2
h0_776E:
    move.b (a2)+,d1
    cmp.b #$24,d1
    beq.s h0_7782
h0_7776:
    cmp.b #$3A,d1
    bcc.s h0_77A4
h0_777C:
    cmp.b #$30,d1
    bcc.s h0_776E
h0_7782:
    movea.l a2,a4
    move.l a2,d0
    sub.l a1,d0
    move.b d0,$0005(a0)
    lea.l $0006(a0),a2
    move.l a2,(a0)
    move.b $0118(a6),(a2)+
    subq.b #1,d0
h0_7798:
    move.b (a1)+,(a2)+
    subq.b #1,d0
    bne.s h0_7798
h0_779E:
    move.b (a4)+,d1
    moveq.l #0,d0
    rts
h0_77A4:
    clr.l (a0)
    moveq.l #41,d0
    rts
h0_77AA:
    tst.b $00FE(a6)
    bne.w h0_781E
h0_77B2:
    move.b d1,$0006(a0)
    lea.l -$0001(a4),a1
    move.l a1,(a0)
    moveq.l #0,d1
    moveq.l #0,d2
h0_77C0:
    move.b (a4)+,d1
    tst.b $0(a2,d1.w)
    beq.s h0_77C0
h0_77C8:
    bpl.s h0_7802
h0_77CA:
    move.l a4,d2
    bra.s h0_77C0
h0_77CE:
    sub.l a4,d2
    addq.l #2,d2
    bne.s h0_7806
    move.b -$0002(a4),d2
    cmp.b #$4C,d2
    beq.s h0_77FC
    cmp.b #$6C,d2
    beq.s h0_77FC
    cmp.b #$57,d2
    beq.s h0_77FC
    cmp.b #$77,d2
    beq.s h0_77FC
    cmp.b #$42,d2
    beq.s h0_77FC
    cmp.b #$62,d2
    bne.s h0_7806
h0_77FC:
    subq.l #2,a4
    moveq.l #46,d1
    bra.s h0_7806
h0_7802:
    tst.l d2
    bne.s h0_77CE
h0_7806:
    move.l a4,d0
    sub.l (a0),d0
    cmp.w $0252(a6),d0
    bcs.s h0_7814
h0_7810:
    move.w $0252(a6),d0
h0_7814:
    subq.b #1,d0
    move.b d0,$0005(a0)
    moveq.l #0,d0
    rts
h0_781E:
    lea.l $0006(a0),a1
    move.l a1,(a0)
    moveq.l #1,d2
    moveq.l #0,d0
h0_7828:
    ext.w d1
    move.b $7E(a6,d1.w),d1
    move.b d1,(a1)+
    moveq.l #0,d1
    move.b (a4)+,d1
    tst.b $0(a2,d1.w)
    bgt.s h0_7852
h0_783A:
    bmi.s h0_7844
h0_783C:
    addq.b #1,d2
    bpl.s h0_7828
h0_7840:
    moveq.l #127,d2
    bra.s h0_784A
h0_7844:
    move.l a4,d0
    addq.b #1,d2
    bpl.s h0_7828
h0_784A:
    move.b (a4)+,d1
    tst.b $0(a2,d1.w)
    ble.s h0_784A
h0_7852:
    tst.l d0
    beq.s h0_787E
h0_7856:
    sub.l a4,d0
    addq.l #2,d0
    bne.s h0_787E
h0_785C:
    move.b -$0002(a4),d0
    cmp.b #$4C,d0
    beq.s h0_7878
h0_7866:
    cmp.b #$6C,d0
    beq.s h0_7878
h0_786C:
    cmp.b #$57,d0
    beq.s h0_7878
h0_7872:
    cmp.b #$77,d0
    bne.s h0_787E
h0_7878:
    moveq.l #46,d1
    subq.l #2,a4
    subq.b #2,d2
h0_787E:
    move.b d2,$0005(a0)
    moveq.l #0,d0
    rts
h0_7886:
    moveq.l #0,d0
    move.b d1,d2
    cmp.b #$22,d1
    beq.s h0_789A
h0_7890:
    cmp.b #$27,d1
    beq.s h0_789A
h0_7896:
    moveq.l #0,d2
    subq.l #1,a4
h0_789A:
    move.b (a4)+,d1
    cmp.b #$D,d1
    beq.s h0_78DE
h0_78A2:
    cmp.b d1,d2
    beq.s h0_78EE
h0_78A6:
    cmp.b #$9,d1
    beq.s h0_78B2
h0_78AC:
    cmp.b #$20,d1
    bne.s h0_78B6
h0_78B2:
    tst.b d2
    beq.s h0_78DE
h0_78B6:
    cmp.b #$2C,d1
    bne.s h0_78C8
h0_78BC:
    btst #16,d3
    beq.s h0_78C8
h0_78C2:
    move.l a4,$01C4(a6)
    bra.s h0_78DE
h0_78C8:
    btst #17,d3
    bne.s h0_78D4
h0_78CE:
    ext.w d1
    move.b $7E(a6,d1.w),d1
h0_78D4:
    move.b d1,$6(a0,d0.w)
    addq.b #1,d0
    bpl.s h0_789A
    moveq.l #126,d0
h0_78DE:
    lea.l $0005(a0),a1
    addq.b #1,d0
    move.b d0,(a1)+
    move.b d3,$5(a0,d0.w)
    move.l a1,(a0)
    rts
h0_78EE:
    cmpi.b #44,(a4)+
    bne.s h0_78DE
h0_78F4:
    bra.s h0_78C2
    DC.B    $ff,$ff
    DC.L    $ff002002,$c0bafff8,$6744b0ba,$fff2673e,$602a2002
    DC.B    "H@J@g4R@g0`"
    DC.B    $1c
    DC.L    $b63c0001,$671c1002,$48806008,$b63c0001,$67103002,$48c0b480,$66024e75,$701d6000
    DC.L    $0c1e701e,$4a2e0108,$67000c14,$4e75b63c,$000167ee
    DC.B    $4e,$75
h0_794E:
    movea.l a4,a0
    lea.l $05B5(a6),a4
    move.b (a4)+,d1
    move.l a0,-(a7)
    bsr.s h0_7970
h0_795A:
    lea.l dat_796A(pc),a4
    move.b (a4)+,d1
    moveq.l #1,d3
    bsr.w h0_79C0
h0_7966:
    movea.l (a7)+,a4
    rts
dat_796A:
    DC.B    $54,$45,$58,$54,$0d,$00 ; VIOLATION: orphaned code island at $796A is not reached from known entrypoints
h0_7970:
    clr.l $0160(a6)
    lea.l $041E(a6),a0
    moveq.l #9,d3
    bsr.w h0_7886
h0_797E:
    movea.l $0178(a6),a2
    movem.l a3-a5,-(a7)
    bsr.w h0_0BC8
h0_798A:
    sne.b d0
    movem.l (a7)+,a3-a5
    tst.b $026A(a6)
    bne.s h0_79B0
h0_7996:
    tst.b d0
    beq.s h0_79B0
h0_799A:
    moveq.l #0,d4
    moveq.l #9,d3
    bsr.w h0_0CFA
h0_79A2:
    move.l a1,$0144(a6)
    lea.l $0010(a1),a1
    move.l a1,$0168(a6)
    rts
h0_79B0:
    tst.b d0
    bne.s h0_79BA
h0_79B4:
    bsr.s h0_79A2
h0_79B6:
    bra.w h0_97EA
h0_79BA:
    moveq.l #11,d0
    bra.w h0_853E
h0_79C0:
    sf.b $011D(a6)
    sf.b $011E(a6)
    move.b d3,$0109(a6)
    lea.l $041E(a6),a0
    clr.l $01C4(a6)
    bset #16,d3
    tst.b $00FF(a6)
    beq.s h0_79EA
h0_79DE:
    btst.b #1,$0251(a6)
    beq.s h0_79EA
h0_79E6:
    bset #17,d3
h0_79EA:
    bsr.w h0_7886
h0_79EE:
    movea.l $0144(a6),a2
    addq.w #8,a2
    movem.l d3/a3-a5,-(a7)
    bsr.w h0_0BC8
h0_79FC:
    sne.b d0
    movem.l (a7)+,d3/a3-a5
    tst.b $026A(a6)
    bne.s h0_7A3A
h0_7A08:
    tst.b d0
    beq.s h0_7A26
h0_7A0C:
    moveq.l #0,d4
    bsr.w h0_0CFA
h0_7A12:
    movea.l $0144(a6),a0
    subq.b #1,$000C(a0)
h0_7A1A:
    move.b $000C(a0),d0
    bsr.w h0_7A5A
h0_7A22:
    move.b d0,$000E(a1)
h0_7A26:
    move.l a1,$0148(a6)
    move.l $0008(a1),$026E(a6)
    move.b $000E(a1),$014C(a6)
    bra.w h0_9AEA
h0_7A3A:
    tst.b d0
    beq.s h0_7A26
h0_7A3E:
    bra.w h0_79BA
h0_7A42:
    movea.l $0148(a6),a1
    move.l $026E(a6),$0008(a1)
    bra.w h0_9AAA
h0_7A50:
    tst.b $026A(a6)
    bne.w h0_981E
h0_7A58:
    rts
h0_7A5A:
    tst.b $00FF(a6)
    beq.s h0_7A68
h0_7A60:
    cmpi.w #1,$0250(a6)
    bne.s h0_7AB4
h0_7A68:
    move.b $0016(a1),d0
    move.l $0016(a1),d1
    cmp.b #$4,d0
    beq.s h0_7A86
h0_7A76:
    cmp.b #$5,d0
    beq.s h0_7A92
h0_7A7C:
    moveq.l #13,d0
    bsr.w h0_8556
h0_7A82:
    moveq.l #0,d0
    rts
h0_7A86:
    cmp.l #$4425353,d1
    bne.s h0_7A7C
h0_7A8E:
    moveq.l #24,d0
    rts
h0_7A92:
    lsl.l #8,d1
    move.b $001A(a1),d1
    moveq.l #0,d0
    cmp.l #$434F4445,d1
    beq.s h0_7AB4
h0_7AA2:
    cmp.l #$54455854,d1
    beq.s h0_7AB4
h0_7AAA:
    cmp.l #$44415441,d1
    bne.s h0_7A7C
h0_7AB2:
    moveq.l #12,d0
h0_7AB4:
    rts
h0_7AB6:
    movea.l $47FA(a6),a0
    clr.w (a0)
    move.l a0,$4756(a6)
    sf.b $010C(a6)
    rts
h0_7AC6:
    move.l a0,-(a7)
    movea.l $4756(a6),a0
    move.w #$2B2B,(a0)+
    move.w d3,(a0)+
h0_7AD2:
    move.l a0,$4756(a6)
    clr.w (a0)
    movea.l (a7)+,a0
    rts
h0_7ADC:
    move.l a0,-(a7)
    move.b $000E(a1),d0
    movea.l $4756(a6),a0
    move.w #$2B2B,(a0)+
    st.b (a0)+
    move.b d0,(a0)+
    bra.s h0_7AD2
h0_7AF0:
    move.l a0,-(a7)
    movea.l $4756(a6),a0
    move.w #$2D2D,-$0004(a0)
    movea.l (a7)+,a0
    rts
dat_7B00:
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
h0_84F2:
    bsr.w h0_BFDA
h0_84F6:
    bne.s h0_84FA
h0_84F8:
    rts
h0_84FA:
    bsr.w h0_9B42
h0_84FE:
    moveq.l #39,d0
    bra.s h0_853E
h0_8502:
    moveq.l #1,d0
    bra.s h0_8556
h0_8506:
    moveq.l #5,d0
    bra.s h0_8556
h0_850A:
    moveq.l #4,d0
    bra.s h0_8556
h0_850E:
    moveq.l #6,d0
    bra.s h0_8556
h0_8512:
    moveq.l #7,d0
    bra.s h0_8556
h0_8516:
    moveq.l #9,d0
    bra.s h0_8556
h0_851A:
    moveq.l #10,d0
    bra.s h0_8556
h0_851E:
    moveq.l #12,d0
    bra.s h0_8556
h0_8522:
    moveq.l #33,d0
    bra.s h0_8556
    DC.B    $70,$1d,$60,$2c ; VIOLATION: orphaned code island at $8526 is not reached from known entrypoints
h0_852A:
    moveq.l #38,d0
    bra.s h0_8556
    DC.B    $70,$0f,$60,$20 ; VIOLATION: orphaned code island at $852E is not reached from known entrypoints
    DC.B    $70,$1f,$60,$1c ; VIOLATION: orphaned code island at $8532 is not reached from known entrypoints
    DC.B    $70,$20,$60,$18 ; VIOLATION: orphaned code island at $8536 is not reached from known entrypoints
    DC.B    $70,$24,$60,$14 ; VIOLATION: orphaned code island at $853A is not reached from known entrypoints
h0_853E:
    sf.b $480F(a6)
    move.b #$14,$026C(a6)
    bsr.s h0_8556
h0_854A:
    jmp h0_039E.l
h0_8550:
    rts
h0_8552:
    movea.l $0266(a6),a7
h0_8556:
    tst.b $010E(a6)
    bne.s h0_8550
h0_855C:
    st.b $010E(a6)
    cmpi.b #10,$026C(a6)
    bcc.s h0_856E
h0_8568:
    move.b #$A,$026C(a6)
h0_856E:
    move.l a4,$015A(a6)
    movem.l d1-d3/a0-a3,-(a7)
    move.w d0,-(a7)
    moveq.l #6,d0
    bsr.w h0_8F00
h0_857E:
    lea.l dat_7B00(pc),a0
    addq.b #1,$010D(a6)
    moveq.l #0,d2
h0_8588:
    move.w (a7)+,d0
h0_858A:
    subq.w #1,d0
    beq.w h0_8596
h0_8590:
    tst.b (a0)+
    bne.s h0_8590
h0_8594:
    bra.s h0_858A
h0_8596:
    tst.l $01D0(a6)
    beq.s h0_8604
h0_859C:
    movem.l d1-d3/a0-a2,-(a7)
    moveq.l #0,d0
    move.w $024C(a6),d0
    moveq.l #0,d2
    movea.l $01AC(a6),a1
    move.l a1,d1
    beq.s h0_85F0
h0_85B0:
    cmpi.b #12,$000D(a1)
    bne.s h0_8600
h0_85B8:
    move.l $0098(a1),d2
    tst.b $0102(a6)
    bne.s h0_85E6
h0_85C2:
    tst.l $474A(a6)
    bne.w h0_85E6
h0_85CA:
    move.l $0272(a6),d1
    beq.s h0_8600
h0_85D0:
    moveq.l #0,d3
    movea.l d1,a2
    move.l $015A(a6),d1
h0_85D8:
    cmpa.l d1,a2
    beq.s h0_85EA
h0_85DC:
    cmp.b #$D,d3
    beq.s h0_8600
h0_85E2:
    move.b (a2)+,d3
    bra.s h0_85D8
h0_85E6:
    moveq.l #0,d1
    bra.s h0_85F0
h0_85EA:
    sub.l $0272(a6),d1
    subq.l #1,d1
h0_85F0:
    movea.l $01D0(a6),a1
    moveq.l #0,d3
    movea.l $01D0(a6),a1
    movea.l $0014(a1),a1
    jsr (a1)                            ; CANDIDATE: indirect_call index unresolved
h0_8600:
    movem.l (a7)+,d1-d3/a0-a2
h0_8604:
    bsr.w h0_9334
h0_8608:
    move.w $024C(a6),d0
    beq.s h0_8658
h0_860E:
    cmp.w #$FFFF,d0
    beq.s h0_864A
h0_8614:
    moveq.l #9,d0
    bsr.w h0_8F00
h0_861A:
    moveq.l #0,d1
    move.w $024C(a6),d1
    bsr.w h0_8F8A
h0_8624:
    tst.l $01AC(a6)
    beq.s h0_864A
h0_862A:
    moveq.l #11,d0
    bsr.w h0_8F00
h0_8630:
    movea.l $01AC(a6),a1
    moveq.l #0,d2
    move.b $0016(a1),d2
    subq.b #2,d2
    lea.l $0017(a1),a1
h0_8640:
    move.b (a1)+,d1
    bsr.w h0_8F1E
h0_8646:
    dbf.w d2,h0_8640
h0_864A:
    bsr.w h0_8F12
h0_864E:
    st.b $0103(a6)
    movem.l (a7)+,d1-d3/a0-a3
h0_8656:
    rts
h0_8658:
    moveq.l #28,d0
    bsr.w h0_8F00
h0_865E:
    bra.s h0_864A
h0_8660:
    tst.b $026A(a6)
    beq.s h0_8656
h0_8666:
    tst.b $0106(a6)
    beq.s h0_8656
h0_866C:
    cmpi.b #5,$026C(a6)
    bcc.s h0_867A
h0_8674:
    move.b #$5,$026C(a6)
h0_867A:
    move.l a4,$015A(a6)
    movem.l d1-d3/a0-a3,-(a7)
    move.w d0,-(a7)
    moveq.l #8,d0
    bsr.w h0_8F00
h0_868A:
    lea.l dat_8696(pc),a0
    move.w #$8000,d2
    bra.w h0_8588
dat_8696:
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
    DC.B    $00,$02,$02
    DC.L    $020400ff,$00020200,$02024a2e,$026a672c,$48a7c000,$0440000b,$103b00e4,$6b0a4880
    DC.L    $d16e01c2,$526e01c0,$30170440,$000b322e,$01120101,$4c9f0003,$6600fd7a
    DC.B    $4e,$75
h0_88EA:
    moveq.l #67,d0
    bra.w h0_853E
h0_88F0:
    movem.l a3-a5,-(a7)
    movea.l $0178(a6),a2
    jsr h0_0BC8.l
h0_88FE:
    movem.l (a7)+,a3-a5
    rts
h0_8904:
    tst.b $026A(a6)
    bne.w h0_8A06
h0_890C:
    bsr.s h0_88F0
h0_890E:
    bne.s h0_892E
h0_8910:
    tst.b $0136(a6)
    bne.s h0_892A
h0_8916:
    cmpi.b #13,$000D(a1)
    beq.s h0_892A
h0_891E:
    tst.w $009C(a1)
    bne.w h0_8AC0
h0_8926:
    bra.w h0_8A0E
h0_892A:
    moveq.l #0,d0
    rts
h0_892E:
    moveq.l #0,d4
    moveq.l #11,d3
    moveq.l #89,d0
    add.l d0,d0
    jsr h0_0D60.l
h0_893C:
    clr.l $0098(a1)
    clr.l $00AA(a1)
    clr.l $00AE(a1)
    move.l a1,-(a7)
    bsr.w h0_BE60
h0_894E:
    movea.l (a7)+,a1
    bne.w h0_8ABC
h0_8954:
    tst.l d1
    bpl.s h0_8972
h0_8958:
    cmp.l #$FFFFFFFF,d1
    beq.s h0_8972
h0_8960:
    move.b #$D,$000D(a1)
    neg.l d1
    jsr h0_10E38.l
h0_896E:
    moveq.l #0,d0
    rts
h0_8972:
    move.l d4,$0098(a1)
    move.l $01AC(a6),$0010(a1)
    move.l a1,$01AC(a6)
    tst.l d1
    bmi.s h0_89C2
h0_8984:
    addq.l #3,d1
    bclr #0,d1
    move.l #$1200,d2
    bsr.w h0_C01E
h0_8994:
    move.l a1,-(a7)
    move.l d1,d3
    bsr.w h0_9146
h0_899C:
    movea.l (a7)+,a1
    move.l a0,$0008(a1)
    move.l d3,$00A6(a1)
    adda.l d3,a0
    move.l a0,$00A2(a1)
    move.l a0,$009E(a1)
    move.w $024C(a6),$009C(a1)
    clr.w $024C(a6)
    st.b $000E(a1)
    bra.w h0_8A70
h0_89C2:
    move.b #$C,$000D(a1)
    movea.l $01D0(a6),a0
    move.l $0020(a0),$0008(a1)
    move.l $0020(a0),$009E(a1)
    movea.l $0024(a0),a2
    cmpi.b #10,-$0001(a2)
    bne.s h0_89EC
h0_89E4:
    cmpi.b #13,-$0002(a2)
    beq.s h0_89F0
h0_89EC:
    move.b #$D,(a2)+
h0_89F0:
    move.l a2,$00A2(a1)
    move.w $024C(a6),$009C(a1)
    clr.w $024C(a6)
    clr.b $000E(a1)
    moveq.l #0,d0
    rts
h0_8A06:
    bsr.w h0_88F0
h0_8A0A:
    bne.w h0_8AC0
h0_8A0E:
    move.b $000E(a1),d0
    cmp.b #$FE,d0
    beq.s h0_8A50
h0_8A18:
    cmpi.b #13,$000D(a1)
    beq.s h0_8A50
h0_8A20:
    move.l $01AC(a6),$0010(a1)
    move.l a1,$01AC(a6)
    tst.b d0
    beq.s h0_8A52
h0_8A2E:
    move.l a1,-(a7)
    bsr.w h0_BE60
h0_8A34:
    movea.l (a7)+,a1
    bne.w h0_8ABC
h0_8A3A:
    move.l d4,$0098(a1)
    move.l $0008(a1),$009E(a1)
    move.w $024C(a6),$009C(a1)
    clr.w $024C(a6)
    bra.s h0_8A70
h0_8A50:
    rts
h0_8A52:
    move.l $0008(a1),$009E(a1)
    move.w $024C(a6),$009C(a1)
    clr.w $024C(a6)
    moveq.l #0,d0
    rts
h0_8A66:
    move.l $0008(a1),$009E(a1)
    movea.l a2,a0
    bra.s h0_8A7C
h0_8A70:
    movea.l $0008(a1),a0
    move.l a0,$009E(a1)
    move.l $00A6(a1),d1
h0_8A7C:
    move.l $0098(a1),d2
    movem.l d1/a0-a1,-(a7)
    bsr.w h0_BF84
h0_8A88:
    movem.l (a7)+,d2/a0-a1
    bne.s h0_8AB8
h0_8A8E:
    lea.l $0(a0,d1.l),a2
    cmp.l d1,d2
    beq.s h0_8AAC
h0_8A96:
    clr.b (a2)
    cmpi.b #10,-$0001(a2)
    bne.s h0_8AA8
h0_8AA0:
    cmpi.b #13,-$0002(a2)
    beq.s h0_8AAC
h0_8AA8:
    move.b #$D,(a2)+
h0_8AAC:
    move.l a2,$00A2(a1)
    addq.b #1,$000E(a1)
    moveq.l #0,d0
    rts
h0_8AB8:
    moveq.l #25,d0
    rts
h0_8ABC:
    moveq.l #26,d0
    rts
h0_8AC0:
    moveq.l #28,d0
    rts
h0_8AC4:
    moveq.l #11,d3
    lea.l h0_8ACC(pc),a2
    bra.s h0_8AE4
h0_8ACC:
    move.l $0098(a0),d2
    beq.s h0_8AE2
h0_8AD2:
    clr.l $0098(a0)
    movem.l a0/a2,-(a7)
    bsr.w h0_BF68
h0_8ADE:
    movem.l (a7)+,a0/a2
h0_8AE2:
    rts
h0_8AE4:
    move.l $0178(a6),d0
    beq.s h0_8B16
h0_8AEA:
    movea.l d0,a0
    move.l (a0),d0
    beq.s h0_8B16
h0_8AF0:
    movea.l d0,a0
h0_8AF2:
    tst.l (a0)
    beq.s h0_8AFE
h0_8AF6:
    move.l a0,-(a7)
    movea.l (a0),a0
    bsr.s h0_8AF2
h0_8AFC:
    movea.l (a7)+,a0
h0_8AFE:
    tst.b d3
    beq.s h0_8B08
h0_8B02:
    cmp.b $000D(a0),d3
    bne.s h0_8B0A
h0_8B08:
    jsr (a2)
h0_8B0A:
    tst.l $0004(a0)
    beq.s h0_8B16
h0_8B10:
    movea.l $0004(a0),a0
    bra.s h0_8AF2
h0_8B16:
    rts
h0_8B18:
    lea.l $052A(a6),a0
    move.l d4,-(a7)
    bsr.w h0_88F0
h0_8B22:
    move.l (a7)+,d4
    move.l a1,$05B0(a6)
    moveq.l #0,d3
    lea.l h0_8B30(pc),a2
    bra.s h0_8AE4
h0_8B30:
    move.b $000D(a0),d0
    cmp.b #$B,d0
    beq.s h0_8B40
h0_8B3A:
    cmp.b #$C,d0
    bne.s h0_8B8A
h0_8B40:
    move.l a0,-(a7)
    lea.l $00AA(a0),a0
h0_8B46:
    move.l (a0),d0
    beq.s h0_8B88
h0_8B4A:
    movea.l (a0),a0
    move.l $0018(a0),d1
    move.l d1,d0
    andi.b #3,d0
    beq.s h0_8B5E
h0_8B58:
    andi.b #252,d1
    addq.l #4,d1
h0_8B5E:
    move.l d1,$0018(a0)
    movem.l a0/a2,-(a7)
    bsr.w h0_9146
h0_8B6A:
    movea.l a0,a1
    movem.l (a7)+,a0/a2
    move.l a1,$000E(a0)
    move.l a1,$0014(a0)
    move.l #$FFFFFFFF,$0006(a0)
    clr.l $000A(a0)
    lea.l (a0),a0
    bra.s h0_8B46
h0_8B88:
    movea.l (a7)+,a0
h0_8B8A:
    rts
h0_8B8C:
    move.l (a1),d1
    bpl.s h0_8B94
h0_8B90:
    move.l d0,(a1)
    bra.s h0_8B98
h0_8B94:
    move.l d0,(a1)
    sub.l d1,d0
h0_8B98:
    beq.s h0_8BBA
h0_8B9A:
    move.l $0018(a0),d1
    addq.l #1,d1
    cmp.l #$80,d0
    bcs.s h0_8BB4
h0_8BA8:
    addq.l #2,d1
    cmp.l #$8000,d0
    bcs.s h0_8BB4
h0_8BB2:
    addq.l #4,d1
h0_8BB4:
    move.l d1,$0018(a0)
    rts
h0_8BBA:
    move.l $0018(a0),d1
    addq.l #7,d1
    bra.s h0_8BB4
h0_8BC2:
    move.l (a1),d1
    bpl.s h0_8BCA
h0_8BC6:
    move.l d0,(a1)
    bra.s h0_8BCE
h0_8BCA:
    move.l d0,(a1)
    sub.l d1,d0
h0_8BCE:
    movea.l $0014(a0),a1
    beq.s h0_8BFA
h0_8BD4:
    cmp.w #$80,d0
    bcs.s h0_8BF6
h0_8BDA:
    clr.b (a1)+
    cmp.l #$8000,d0
    bcs.s h0_8BF0
h0_8BE4:
    clr.b (a1)+
    clr.b (a1)+
    swap.w d0
    bsr.w h0_8BF0
h0_8BEE:
    swap.w d0
h0_8BF0:
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a1)+
h0_8BF6:
    move.b d0,(a1)+
    rts
h0_8BFA:
    clr.b (a1)+
    bra.s h0_8BE4
dat_8BFE:
    DC.B    "$H",$22,"<",0 ; VIOLATION: orphaned code island at $8BFE is not reached from known entrypoints
    DC.B    $00
    DC.L    $03f16100
    DC.B    "&6a^a",0
    DC.B    $26,$30
    DC.L    $72006100
    DC.B    "&*",$22,"<LINEJ."
    DC.B    $01,$2c
    DC.L    $6706223c
    DC.B    "HCLNa",0
    DC.B    $26,$14
    DC.L    $70006100,$25b85229,$00164a2e,$012c670a,$7200322a,$00126100,$25fa6100,$25fe206a
    DC.L    $000e222a,$001848e7,$00606100,$f89a4cdf,$06006100,$2600204a,$45faff98
    DC.B    $4e,$75
h0_8C6A:
    moveq.l #0,d1
    move.b $0016(a1),d1
    subq.b #1,d1
    move.b d1,$0016(a1)
    move.l d1,d0
    andi.b #3,d0
    beq.s h0_8C84
h0_8C7E:
    andi.b #252,d1
    addq.l #4,d1
h0_8C84:
    add.l $0018(a2),d1
    lsr.l #2,d1
    addq.l #3,d1
    tst.b $012C(a6)
    beq.s h0_8C94
h0_8C92:
    addq.l #1,d1
h0_8C94:
    rts
h0_8C96:
    movea.l a0,a2
    bsr.s h0_8C6A
h0_8C9A:
    move.l d1,-(a7)
    addq.l #2,d1
    add.l d1,d1
    add.l d1,d1
    sub.l d1,d4
    bcs.w h0_88EA
h0_8CA8:
    move.l (a7)+,d1
    move.l #$3F1,(a4)+
    move.l d1,(a4)+
    tst.b $012C(a6)
    beq.s h0_8CF2
h0_8CB8:
    clr.l (a4)+
    move.l #$48434C4E,(a4)+
    bsr.w h0_A35E
h0_8CC4:
    addq.b #1,$0016(a1)
    moveq.l #0,d1
    move.w $0012(a2),d1
    move.l d1,(a4)+
    movea.l $000E(a2),a0
    move.l $0018(a2),d1
    lsr.l #2,d1
    subq.l #1,d1
h0_8CDC:
    move.l (a0)+,(a4)+
    dbf.w d1,h0_8CDC
h0_8CE2:
    subi.l #65536,d1
    bcc.s h0_8CDC
h0_8CEA:
    movea.l a2,a0
    lea.l h0_8C96(pc),a2
    rts
h0_8CF2:
    clr.l (a4)+
    move.l #$4C494E45,(a4)+
    bsr.w h0_A35E
h0_8CFE:
    addq.b #1,$0016(a1)
    movea.l $000E(a2),a0
    move.l $0018(a2),d1
    lsr.l #3,d1
    subq.l #1,d1
h0_8D0E:
    move.l (a0)+,(a4)+
    move.l (a0)+,(a4)+
    dbf.w d1,h0_8D0E
h0_8D16:
    subi.l #65536,d1
    bcc.s h0_8D0E
h0_8D1E:
    bra.s h0_8CEA
h0_8D20:
    movea.l $05B0(a6),a0
    bsr.w h0_8D62
h0_8D28:
    movea.l $0178(a6),a0
    movea.l (a0),a0
h0_8D2E:
    tst.l (a0)
    beq.s h0_8D3A
h0_8D32:
    move.l a0,-(a7)
    movea.l (a0),a0
    bsr.s h0_8D2E
h0_8D38:
    movea.l (a7)+,a0
h0_8D3A:
    move.b $000D(a0),d0
    cmp.b #$B,d0
    beq.s h0_8D4A
h0_8D44:
    cmp.b #$C,d0
    bne.s h0_8D54
h0_8D4A:
    cmpa.l $05B0(a6),a0
    beq.s h0_8D54
h0_8D50:
    bsr.w h0_8D62
h0_8D54:
    tst.l $0004(a0)
    beq.s h0_8D60
h0_8D5A:
    movea.l $0004(a0),a0
    bra.s h0_8D2E
h0_8D60:
    rts
h0_8D62:
    movea.l a0,a1
    move.l $00AA(a1),d0
h0_8D68:
    beq.s h0_8D78
h0_8D6A:
    movea.l d0,a0
    cmp.b $0004(a0),d6
    beq.s h0_8D76
h0_8D72:
    move.l (a0),d0
    bra.s h0_8D68
h0_8D76:
    jsr (a2)
h0_8D78:
    movea.l a1,a0
    rts
h0_8D7C:
    tst.l $0010(a1)
    beq.s h0_8DA0
h0_8D82:
    movea.l $0010(a1),a1
h0_8D86:
    tst.l (a1)
    beq.s h0_8D92
h0_8D8A:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_8D86
h0_8D90:
    movea.l (a7)+,a1
h0_8D92:
    jsr (a2)
h0_8D94:
    tst.l $0004(a1)
    beq.s h0_8DA0
h0_8D9A:
    movea.l $0004(a1),a1
    bra.s h0_8D86
h0_8DA0:
    rts
h0_8DA2:
    move.l a3,-(a7)
    movea.l a2,a3
    lea.l h0_8DBC(pc),a2
    bsr.s h0_8D7C
h0_8DAC:
    movea.l $0170(a6),a1
    tst.l (a1)
    beq.s h0_8DB8
h0_8DB4:
    movea.l (a1),a1
    bsr.s h0_8D86
h0_8DB8:
    movea.l (a7)+,a3
    rts
h0_8DBC:
    btst.b #5,$000C(a1)
    beq.s h0_8DCC
h0_8DC4:
    cmp.b $000E(a1),d6
    bne.s h0_8DCC
h0_8DCA:
    jsr (a3)                            ; CANDIDATE: indirect_call index unresolved
h0_8DCC:
    rts
h0_8DCE:
    tst.l $0010(a1)
    beq.s h0_8DF2
h0_8DD4:
    movea.l $0010(a1),a1
h0_8DD8:
    tst.l (a1)
    beq.s h0_8DE4
h0_8DDC:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_8DD8
h0_8DE2:
    movea.l (a7)+,a1
h0_8DE4:
    bsr.s h0_8DF4
h0_8DE6:
    tst.l $0004(a1)
    beq.s h0_8DF2
h0_8DEC:
    movea.l $0004(a1),a1
    bra.s h0_8DD8
h0_8DF2:
    rts
h0_8DF4:
    btst.b #4,$000C(a1)
    beq.s h0_8E06
h0_8DFC:
    btst.b #2,$000C(a1)
    bne.s h0_8E06
h0_8E04:
    jsr (a2)
h0_8E06:
    rts
h0_8E08:
    tst.b $026A(a6)
    bne.s h0_8E26
h0_8E0E:
    move.l #$196,d1
    bsr.w h0_9146
h0_8E18:
    move.l a0,$4802(a6)
    move.l a0,$4806(a6)
    clr.l (a0)+
    clr.w (a0)
    rts
h0_8E26:
    movea.l $4806(a6),a0
    move.w $0004(a0),d0
    lea.l $6(a0,d0.w),a0
    move.l a0,$480A(a6)
    movea.l $4802(a6),a0
    move.l a0,$4806(a6)
    moveq.l #-1,d0
    tst.w $0004(a0)
    beq.s h0_8E4E
h0_8E46:
    clr.w $0004(a0)
    move.l $0006(a0),d0
h0_8E4E:
    move.l d0,$47FE(a6)
    rts
    DC.L    $200d90ae,$027ed0ae,$02564a2e,$026a6644,$2f00206e,$48065888,$3018b07c,$01906710
    DC.L    $219f0000,$21820004,$50403100,$70004e75 ; VIOLATION: orphaned code island at $8E54 is not reached from known entrypoints
    DC.L    $48e76060,$223c0000,$01966100,$02b6226e,$48062288,$2d484806,$42984258,$70004cdf
    DC.L    $060660cc ; VIOLATION: orphaned code island at $8E84 is not reached from known entrypoints
    DC.L    $b0ae47fe ; VIOLATION: orphaned code island at $8EA8 is not reached from known entrypoints
    DC.B    "f2 nH"
    DC.B    $06,$58,$88
    DC.L    $3018b4b0,$0004670a,$3f007041,$6100f694,$301f5040,$b07c0190,$67143140,$fffed0c0
    DC.L    $b1ee480a,$671c2d50,$47fe7000
    DC.B    $4e,$75
    DC.B    $20,$6e ; VIOLATION: orphaned code island at $8EE2 is not reached from known entrypoints
    DC.L    $48064a90,$670c2050,$2d484806,$5c487000
    DC.B    $60,$d8
    DC.B    $70,$ff,$2d,$40,$47,$fe,$70,$00,$4e,$75 ; VIOLATION: orphaned code island at $8EF6 is not reached from known entrypoints
h0_8F00:
    lea.l dat_94DC(pc),a0
    tst.w d0
h0_8F06:
    beq.w h0_9334
h0_8F0A:
    tst.b (a0)+
    bne.s h0_8F0A
h0_8F0E:
    subq.w #1,d0
    bra.s h0_8F06
h0_8F12:
    moveq.l #13,d1
    bra.w h0_931A
h0_8F18:
    bsr.w h0_8F1C
h0_8F1C:
    moveq.l #32,d1
h0_8F1E:
    movem.l d0-d2/a0-a2,-(a7)
    bsr.w h0_931A
h0_8F26:
    movem.l (a7)+,d0-d2/a0-a2
    rts
h0_8F2C:
    move.w d1,-(a7)
    swap.w d1
    bsr.s h0_8F34
h0_8F32:
    move.w (a7)+,d1
h0_8F34:
    move.w d1,-(a7)
    lsr.w #8,d1
    bsr.s h0_8F3C
h0_8F3A:
    move.w (a7)+,d1
h0_8F3C:
    move.w d1,-(a7)
    lsr.w #4,d1
    bsr.s h0_8F44
h0_8F42:
    move.w (a7)+,d1
h0_8F44:
    andi.w #15,d1
    move.b dat_8F4E(pc,d1.w),d1
    bra.s h0_8F1E
dat_8F4E:
    DC.B    $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46
h0_8F5E:
    moveq.l #6,d3
    moveq.l #0,d2
h0_8F62:
    rol.l #4,d1
    move.l d1,-(a7)
    andi.w #15,d1
    bne.s h0_8F70
h0_8F6C:
    tst.b d2
    beq.s h0_8F78
h0_8F70:
    st.b d2
    move.b dat_8F4E(pc,d1.w),d1
    jsr (a2)
h0_8F78:
    move.l (a7)+,d1
    dbf.w d3,h0_8F62
h0_8F7E:
    rol.l #4,d1
    andi.w #15,d1
    move.b dat_8F4E(pc,d1.w),d1
    jmp (a2)
h0_8F8A:
    lea.l h0_8F1E(pc),a2
h0_8F8E:
    lea.l dat_8FC2(pc),a0
    moveq.l #1,d2
    moveq.l #8,d0
h0_8F96:
    moveq.l #0,d3
    cmp.l (a0)+,d1
    bcs.s h0_8FA8
h0_8F9C:
    sub.l -(a0),d1
h0_8F9E:
    addq.b #1,d3
    sub.l (a0),d1
    bcc.s h0_8F9E
h0_8FA4:
    add.l (a0)+,d1
    bra.s h0_8FAC
h0_8FA8:
    tst.b d2
    bpl.s h0_8FB8
h0_8FAC:
    st.b d2
    addi.b #48,d3
    exg d3,d1
    jsr (a2)
h0_8FB6:
    exg d3,d1
h0_8FB8:
    dbf.w d0,h0_8F96
h0_8FBC:
    addi.b #48,d1
    jmp (a2)
dat_8FC2:
    DC.B    $3b,$9a ; VIOLATION: orphaned code island at $8FC2 is not reached from known entrypoints
    DC.L    $ca0005f5,$e1000098,$9680000f,$42400001,$86a00000,$27100000,$03e80000,$00640000
    DC.B    $00,$0a
h0_8FE6:
    moveq.l #20,d0
    bsr.w h0_8F00
h0_8FEC:
    movea.l $0170(a6),a2
    lea.l dat_9016(pc),a4
    bsr.w h0_905E
h0_8FF8:
    moveq.l #9,d3
    lea.l h0_901E(pc),a2
    lea.l dat_9006(pc),a4
    bra.w h0_8AE4
dat_9006:
    DC.B    $0c,$2b,$00,$02,$00,$0d,$67,$08,$10,$2b,$00,$0e,$60,$00,$09,$82 ; VIOLATION: orphaned code island at $9006 is not reached from known entrypoints
dat_9016:
    DC.B    $61,$00,$ff,$04,$60,$00,$fe,$fc ; VIOLATION: orphaned code island at $9016 is not reached from known entrypoints
h0_901E:
    movem.l d3/a0/a2,-(a7)
    move.l a0,-(a7)
    moveq.l #21,d0
    bsr.w h0_8F00
h0_902A:
    tst.b $00FF(a6)
    beq.s h0_9042
h0_9030:
    movea.l (a7),a0
    lea.l $0016(a0),a0
    move.b (a0)+,d2
h0_9038:
    move.b (a0)+,d1
    bsr.w h0_8F1E
h0_903E:
    subq.b #1,d2
    bgt.s h0_9038
h0_9042:
    bsr.w h0_8F12
h0_9046:
    bsr.w h0_8F12
h0_904A:
    movea.l (a7)+,a0
    lea.l $0010(a0),a2
    bsr.s h0_905E
h0_9052:
    movem.l (a7)+,d3/a0/a2
    rts
h0_9058:
    jmp h0_06BC.l
h0_905E:
    move.l a2,d0
    beq.s h0_90D8
h0_9062:
    move.l (a2),d0
    beq.s h0_90D8
h0_9066:
    movea.l d0,a2
    suba.l a3,a3
    lea.l $05F4(a6),a0
    moveq.l #127,d0
    move.b d0,(a0)+
h0_9072:
    st.b (a0)+
    dbf.w d0,h0_9072
h0_9078:
    tst.b $0117(a6)
    bgt.s h0_9058
h0_907E:
    lea.l $05DE(a6),a3
    move.b $0017(a3),d3
    bsr.s h0_90DA
h0_9088:
    lea.l $05DE(a6),a0
    cmpa.l a3,a0
    beq.s h0_90D8
h0_9090:
    bset.b #0,$000C(a3)
    btst.b #4,$000C(a3)
    bne.s h0_9078
h0_909E:
    move.l $0008(a3),d1
    bsr.w h0_8F2C
h0_90A6:
    bsr.w h0_8F18
h0_90AA:
    jsr (a4)                            ; CANDIDATE: indirect_call index unresolved
h0_90AC:
    moveq.l #0,d1
    move.b $000D(a3),d1
    lea.l dat_9126(pc),a0
    move.b $0(a0,d1.w),d1
    bsr.w h0_8F1E
h0_90BE:
    bsr.w h0_8F18
h0_90C2:
    lea.l $0016(a3),a0
    move.b (a0)+,d4
h0_90C8:
    move.b (a0)+,d1
    bsr.w h0_8F1E
h0_90CE:
    subq.b #1,d4
    bne.s h0_90C8
h0_90D2:
    bsr.w h0_8F12
h0_90D6:
    bra.s h0_9078
h0_90D8:
    rts
h0_90DA:
    tst.l (a2)
    beq.s h0_90E6
h0_90DE:
    move.l a2,-(a7)
    movea.l (a2),a2
    bsr.s h0_90DA
h0_90E4:
    movea.l (a7)+,a2
h0_90E6:
    btst.b #0,$000C(a2)
    bne.s h0_9114
h0_90EE:
    cmp.b $0017(a2),d3
    bcs.s h0_9114
h0_90F4:
    lea.l $0016(a3),a0
    lea.l $0016(a2),a1
    move.b (a0)+,d0
    move.b (a1)+,d1
h0_9100:
    cmpm.b (a1)+,(a0)+
    bcs.s h0_9114
h0_9104:
    bne.s h0_910E
h0_9106:
    subq.b #1,d0
    beq.s h0_9114
h0_910A:
    subq.b #1,d1
    bne.s h0_9100
h0_910E:
    movea.l a2,a3
    move.b $0017(a3),d3
h0_9114:
    tst.l $0004(a2)
    beq.s h0_9124
h0_911A:
    move.l a2,-(a7)
    movea.l $0004(a2),a2
    bsr.s h0_90DA
h0_9122:
    movea.l (a7)+,a2
h0_9124:
    rts
dat_9126:
    DC.B    $3f,$52,$41,$3f,$72,$6c,$3f,$3f,$3f,$3f,$3f,$3f,$4f,$00
h0_9134:
    move.l #$2800,d1
    move.w d1,$014E(a6)
    bsr.s h0_9146
h0_9140:
    move.l a0,$0140(a6)
    rts
h0_9146:
    addq.l #4,d1
    bsr.w h0_BDF4
h0_914C:
    beq.s h0_9178
h0_914E:
    move.l $013C(a6),(a0)
    move.l a0,$013C(a6)
    addq.w #4,a0
    rts
    DC.B    $59,$48 ; VIOLATION: orphaned code island at $915A is not reached from known entrypoints
    DC.L    $43ee013c,$2011670e,$b1c06704,$224060f4
    DC.B    $22,$90,$60,$00,$2c,$e0 ; VIOLATION: orphaned code island at $916C is not reached from known entrypoints
    DC.B    $70,$69,$60,$00,$f3,$c8 ; VIOLATION: orphaned code island at $9172 is not reached from known entrypoints
h0_9178:
    moveq.l #2,d0
    bra.w h0_853E
h0_917E:
    movea.l $013C(a6),a0
    bra.s h0_918C
h0_9184:
    move.l (a0),-(a7)
    bsr.w h0_BE50
h0_918A:
    movea.l (a7)+,a0
h0_918C:
    move.l a0,d0
    bne.s h0_9184
h0_9190:
    rts
h0_9192:
    sf.b $480E(a6)
    sf.b $480F(a6)
    clr.l $4810(a6)
    lea.l $4814(a6),a0
    lea.l $4A14(a6),a1
    move.l a0,(a1)
    move.l a1,$4A18(a6)
    move.w #$84,$4A1C(a6)
    move.w #$3C,$4A1E(a6)
    clr.w $4A20(a6)
    move.w #$FFFF,$4A22(a6)
    clr.w $4A24(a6)
    clr.b $4A3C(a6)
    clr.b $4A8D(a6)
    st.b $4ADE(a6)
    move.w #$8,$4A26(a6)
    lea.l $4A28(a6),a3
    bsr.w h0_BD4A
h0_91E0:
    clr.b (a3)
    rts
h0_91E4:
    tst.l $4810(a6)
    beq.s h0_91F4
h0_91EA:
    bsr.w h0_BC04
h0_91EE:
    bsr.w h0_922A
h0_91F2:
    bsr.s h0_91F6
h0_91F4:
    rts
h0_91F6:
    tst.l $4810(a6)
    beq.s h0_91F4
h0_91FC:
    move.l $4810(a6),d3
    clr.l $4810(a6)
    bra.w h0_B8A8
h0_9208:
    movea.l $4A14(a6),a0
    cmpa.l $4A18(a6),a0
    beq.s h0_921A
h0_9212:
    move.b d1,(a0)+
    move.l a0,$4A14(a6)
    rts
h0_921A:
    move.w d1,-(a7)
    bsr.s h0_922A
h0_921E:
    bne.s h0_9224
h0_9220:
    move.w (a7)+,d1
    bra.s h0_9208
h0_9224:
    moveq.l #74,d0
    bra.w h0_853E
h0_922A:
    move.l d3,-(a7)
    move.l $4810(a6),d3
    lea.l $4814(a6),a0
    move.l $4A14(a6),d1
    sub.l a0,d1
    beq.s h0_9248
h0_923C:
    lea.l $4814(a6),a1
    move.l a1,$4A14(a6)
    bsr.w h0_B890
h0_9248:
    movem.l (a7)+,d3
    rts
h0_924E:
    btst.b #0,$4ADE(a6)
    bne.s h0_9258
h0_9256:
    rts
h0_9258:
    addq.w #1,$4A24(a6)
    moveq.l #16,d0
    bsr.w h0_8F00
h0_9262:
    lea.l $4A28(a6),a0
    bsr.w h0_9334
h0_926A:
    moveq.l #15,d0
    bsr.w h0_8F00
h0_9270:
    moveq.l #0,d1
    move.w $4A24(a6),d1
    move.l d3,-(a7)
    bsr.w h0_8F8A
h0_927C:
    move.l (a7)+,d3
    bsr.w h0_8F12
h0_9282:
    lea.l $4A3C(a6),a0
    tst.b (a0)
    beq.s h0_9290
h0_928A:
    bsr.w h0_9334
h0_928E:
    bra.s h0_92B0
h0_9290:
    tst.l $01AC(a6)
    beq.s h0_92B0
h0_9296:
    movea.l $01AC(a6),a1
    moveq.l #0,d2
    move.b $0016(a1),d2
    subq.b #2,d2
    lea.l $0017(a1),a1
h0_92A6:
    move.b (a1)+,d1
    bsr.w h0_8F1E
h0_92AC:
    dbf.w d2,h0_92A6
h0_92B0:
    bsr.w h0_8F12
h0_92B4:
    lea.l $4A8D(a6),a0
    bsr.w h0_9334
h0_92BC:
    bsr.w h0_8F12
h0_92C0:
    bra.w h0_8F12
h0_92C4:
    tst.w $4A22(a6)
    bpl.s h0_92D6
h0_92CA:
    clr.w $4A22(a6)
    move.w d1,-(a7)
    bsr.w h0_924E
h0_92D4:
    move.w (a7)+,d1
h0_92D6:
    cmp.b #$D,d1
    bne.s h0_92FE
h0_92DC:
    clr.w $4A20(a6)
    move.w $4A22(a6),d0
    addq.w #1,$4A22(a6)
    cmp.w $4A1E(a6),d0
    beq.w h0_BC04
h0_92F0:
    moveq.l #13,d1
    bsr.w h0_9208
h0_92F6:
    moveq.l #10,d1
    bsr.w h0_9208
h0_92FC:
    rts
h0_92FE:
    move.w $4A20(a6),d0
    cmp.w $4A1C(a6),d0
    blt.s h0_9310
h0_9308:
    move.w d1,-(a7)
    bsr.s h0_92DC
h0_930C:
    move.w (a7)+,d1
    bra.s h0_92C4
h0_9310:
    bsr.w h0_9208
h0_9314:
    addq.w #1,$4A20(a6)
    rts
h0_931A:
    tst.b $480F(a6)
    bne.s h0_92C4
h0_9320:
    cmp.b #$D,d1
    bne.s h0_9330
h0_9326:
    tst.l $01D0(a6)
    bne.s h0_9330
h0_932C:
    bsr.s h0_9330
h0_932E:
    moveq.l #10,d1
h0_9330:
    bra.w h0_B870
h0_9334:
    tst.b $480F(a6)
    bne.s h0_936E
h0_933A:
    tst.l $01D0(a6)
    beq.s h0_936E
h0_9340:
    movem.l d0-d2/a0-a2,-(a7)
    movea.l a0,a1
h0_9346:
    move.b (a0)+,d1
    bne.s h0_9346
h0_934A:
    suba.l a1,a0
    subq.w #1,a0
    move.l a1,-(a7)
    move.l a0,-(a7)
    move.w #$1,-(a7)
    move.w #$40,-(a7)
    movea.l $01D0(a6),a0
    movea.l $0010(a0),a0
    jsr (a0)                            ; CANDIDATE: indirect_call index unresolved
h0_9364:
    lea.l $000C(a7),a7
    movem.l (a7)+,d0-d2/a0-a2
    rts
h0_936E:
    move.b (a0)+,d1
    beq.s h0_937A
h0_9372:
    move.l a0,-(a7)
    bsr.s h0_931A
h0_9376:
    movea.l (a7)+,a0
    bra.s h0_936E
h0_937A:
    rts
h0_937C:
    movem.l d7/a3,-(a7)
    move.b $4ADE(a6),d7
    add.b d7,d7
    bcc.s h0_93C0
h0_9388:
    move.w $024C(a6),d2
    cmp.w #$2710,d2
    bcc.s h0_93B4
h0_9392:
    bsr.w h0_8F1C
h0_9396:
    cmp.w #$3E8,d2
    bcc.s h0_93B4
h0_939C:
    bsr.w h0_8F1C
h0_93A0:
    cmp.w #$64,d2
    bcc.s h0_93B4
h0_93A6:
    bsr.w h0_8F1C
h0_93AA:
    cmp.w #$A,d2
    bcc.s h0_93B4
h0_93B0:
    bsr.w h0_8F1C
h0_93B4:
    moveq.l #0,d1
    move.w d2,d1
    bsr.w h0_8F8A
h0_93BC:
    bsr.w h0_8F1C
h0_93C0:
    move.l $01B0(a6),d4
    add.b d7,d7
    bcc.s h0_940C
h0_93C8:
    move.b $014C(a6),d0
    move.b $46F5(a6),d1
    beq.s h0_93F6
h0_93D2:
    cmp.b #$FF,d1
    beq.s h0_93F0
h0_93D8:
    bsr.w h0_8F18
h0_93DC:
    move.b $46F5(a6),d1
    bsr.w h0_931A
h0_93E4:
    move.l $46F6(a6),d1
    bsr.w h0_8F2C
h0_93EC:
    moveq.l #0,d4
    bra.s h0_940C
h0_93F0:
    bsr.w h0_9990
h0_93F4:
    bra.s h0_93E4
h0_93F6:
    bsr.w h0_9990
h0_93FA:
    move.l $01B0(a6),d4
    movea.l $0282(a6),a3
    move.l $026E(a6),d1
    sub.l d4,d1
    bsr.w h0_8F2C
h0_940C:
    moveq.l #32,d1
    tst.b $0102(a6)
    beq.s h0_941C
h0_9414:
    tst.b $011A(a6)
    bne.s h0_941C
h0_941A:
    moveq.l #43,d1
h0_941C:
    bsr.w h0_931A
h0_9420:
    add.b d7,d7
    bcc.s h0_944A
h0_9424:
    moveq.l #5,d3
    cmpi.w #81,$4A1C(a6)
    bcs.s h0_9430
h0_942E:
    moveq.l #9,d3
h0_9430:
    tst.l d4
h0_9432:
    beq.s h0_9442
h0_9434:
    move.b (a3)+,d1
    bsr.w h0_8F3C
h0_943A:
    subq.l #1,d4
    dbf.w d3,h0_9432
h0_9440:
    bra.s h0_944A
h0_9442:
    bsr.w h0_8F18
h0_9446:
    dbf.w d3,h0_9442
h0_944A:
    bsr.w h0_8F1C
h0_944E:
    movea.l $0272(a6),a3
    moveq.l #0,d2
    moveq.l #0,d3
    tst.b $010E(a6)
    beq.s h0_9466
h0_945C:
    tst.b $480F(a6)
    bne.s h0_9466
h0_9462:
    move.l $015A(a6),d3
h0_9466:
    move.b (a3)+,d1
    cmp.l a3,d3
    bne.s h0_94A2
h0_946C:
    movem.l d0-d2/a0-a2,-(a7)
    cmp.b #$D,d1
    beq.s h0_947C
h0_9476:
    cmp.b #$9,d1
    bne.s h0_947E
h0_947C:
    moveq.l #32,d1
h0_947E:
    tst.b $012A(a6)
    bne.s h0_948A
h0_9484:
    bsr.w h0_B85C
h0_9488:
    bra.s h0_948E
h0_948A:
    bsr.w h0_B870
h0_948E:
    movem.l (a7)+,d0-d2/a0-a2
    cmp.b #$D,d1
    beq.s h0_94D2
h0_9498:
    cmp.b #$9,d1
    beq.s h0_94A2
h0_949E:
    addq.w #1,d2
    bra.s h0_9466
h0_94A2:
    cmp.b #$D,d1
    beq.s h0_94D2
h0_94A8:
    cmp.b #$9,d1
    bne.s h0_94CA
h0_94AE:
    moveq.l #0,d0
    move.w d2,d0
    divu.w $4A26(a6),d0
    swap.w d0
    sub.w $4A26(a6),d0
    neg.w d0
h0_94BE:
    bsr.w h0_8F1C
h0_94C2:
    addq.w #1,d2
    subq.w #1,d0
    bne.s h0_94BE
h0_94C8:
    bra.s h0_9466
h0_94CA:
    addq.w #1,d2
    bsr.w h0_8F1E
h0_94D0:
    bra.s h0_9466
h0_94D2:
    bsr.w h0_931A
h0_94D6:
    movem.l (a7)+,d7/a3
    rts
dat_94DC:
    DC.B    "Gen Macro Assembler Copyright "
    DC.B    $bd
    DC.B    " HiSoft 1985-93"
    DC.B    $0d
    DC.B    "All Rights Reserved - version 3.10"
    DC.B    $0d,$0d,$00
    DC.B    "Pass 1"
    DC.B    $0d,$00
    DC.B    "Pass 2"
    DC.B    $0d,$00
    DC.B    " errors found"
    DC.B    $0d,$00
    DC.B    " error found"
    DC.B    $0d
    DC.L    $00206c69
    DC.B    "nes assembled into ",0
    DC.B    "Error: ",0
    DC.B    "Locals:"
    DC.B    $0d
    DC.L    $00576172
    DC.B    "ning: ",0
    DC.B    " at line ",0
    DC.B    "Could not open file ",0
    DC.B    " in file ",0
    DC.B    " bytes, ",0
    DC.B    " optimisations saving ",0
    DC.B    " bytes"
    DC.B    $0d,$00
    DC.B    "  Page ",0
    DC.B    "HiSoft Gen 680x0 Macro Assembler v3.10   ",0
    DC.B    " relocatable",0
    DC.B    " position-independent",0
    DC.B    " code"
    DC.B    $0d,$00
    DC.L    $0d09474c
    DC.B    "OBAL SYMBOLS"
    DC.L    $0d0d000d,$094d4f44
    DC.B    "ULE ",0
    DC.B    " absolute",0
    DC.B    "Invalid command line - see manual"
    DC.L    $0d004572
    DC.B    "ror in WITH file",0
    DC.B    "WITH file not found",0
    DC.B    "Could not open listing device"
    DC.B    $0d,$00
    DC.B    "Assembling ",0
    DC.B    " in assembly options",0
    DC.B    "Main file already included in header file"
    DC.B    $0d,$00
h0_9718:
    pea.l h0_9334(pc)
    tst.b $010A(a6)
    beq.s h0_9728
h0_9722:
    lea.l dat_9760(pc),a0
    rts
h0_9728:
    tst.b $00FF(a6)
    beq.w h0_A45A
h0_9730:
    tst.w $0250(a6)
    beq.w h0_A92C
h0_9738:
    btst.b #1,$0251(a6)
    bne.w h0_B49C
h0_9742:
    btst.b #2,$0251(a6)
    bne.w h0_10B06
h0_974C:
    bra.w h0_AC7A
h0_9750:
    tst.b $010A(a6)
    beq.s h0_976C
h0_9756:
    lea.l dat_975C(pc),a0
    rts
dat_975C:
    DC.L    $2e677300
dat_9760:
    DC.B    $47,$65,$6e,$20,$73,$79,$6d,$62,$6f,$6c,$00,$00
h0_976C:
    tst.b $00FF(a6)
    beq.w h0_A460
h0_9774:
    tst.w $0250(a6)
    beq.w h0_A932
h0_977C:
    btst.b #1,$0251(a6)
    bne.w h0_B4AE
h0_9786:
    btst.b #2,$0251(a6)
    bne.w h0_10B0C
h0_9790:
    bra.w h0_AC8A
    DC.L    $4a2e00ff,$67000ce2,$4a6e0250,$67000cda,$082e0001,$02516600,$1d2a082e,$00020251
    DC.L    $66007378,$60000cc2 ; VIOLATION: orphaned code island at $9794 is not reached from known entrypoints
h0_97BC:
    tst.b $00FF(a6)
    beq.w h0_9D7C
h0_97C4:
    tst.w $0250(a6)
    beq.w h0_A484
h0_97CC:
    btst.b #1,$0251(a6)
    bne.w h0_AE8A
h0_97D6:
    btst.b #2,$0251(a6)
    bne.w h0_10AA0
h0_97E0:
    bra.w h0_A94A
h0_97E4:
    moveq.l #66,d0
    bra.w h0_853E
h0_97EA:
    tst.b $0104(a6)
    beq.s h0_981C
h0_97F0:
    movea.l $0144(a6),a1
    tst.b $00FF(a6)
    beq.w h0_9D48
h0_97FC:
    tst.w $0250(a6)
    beq.w h0_A4B2
h0_9804:
    btst.b #1,$0251(a6)
    bne.w h0_AD0A
h0_980E:
    btst.b #2,$0251(a6)
    bne.w h0_108B8
h0_9818:
    bra.w h0_A9E0
h0_981C:
    rts
h0_981E:
    tst.b $0104(a6)
    beq.s h0_981C
h0_9824:
    movea.l $0144(a6),a1
    tst.b $00FF(a6)
    beq.w h0_9D48
h0_9830:
    tst.w $0250(a6)
    beq.w h0_A5BA
h0_9838:
    btst.b #1,$0251(a6)
    bne.w h0_AD0A
h0_9842:
    btst.b #2,$0251(a6)
    bne.w h0_108B8
h0_984C:
    bra.w h0_A9E0
h0_9850:
    tst.b $0104(a6)
    beq.s h0_9876
h0_9856:
    tst.w $0250(a6)
    beq.w h0_A540
h0_985E:
    btst.b #1,$0251(a6)
    bne.w h0_AD0C
h0_9868:
    btst.b #2,$0251(a6)
    bne.w h0_108BA
h0_9872:
    bra.w h0_A9E0
h0_9876:
    rts
    DC.L    $4a2e0104,$67f84a2e,$00ff6700,$04c64a6e,$02506700,$0e12082e,$00010251,$66001474
    DC.L    $082e0002,$02516600,$70186000 ; VIOLATION: orphaned code island at $9878 is not reached from known entrypoints
    DC.B    $11,$42
h0_98A6:
    tst.b $00FF(a6)
    beq.w h0_9D48
h0_98AE:
    tst.w $0250(a6)
    beq.w h0_A63A
h0_98B6:
    btst.b #1,$0251(a6)
    bne.w h0_AD0C
h0_98C0:
    btst.b #2,$0251(a6)
    bne.w h0_108BA
h0_98CA:
    bra.w h0_A9E0
h0_98CE:
    tst.b $011D(a6)
    bne.s h0_9902
h0_98D4:
    tst.b $0104(a6)
    beq.s h0_9876
h0_98DA:
    tst.b $00FF(a6)
    beq.w h0_9EE6
h0_98E2:
    tst.w $0250(a6)
    beq.w h0_A736
h0_98EA:
    btst.b #1,$0251(a6)
    bne.w h0_AD54
h0_98F4:
    btst.b #2,$0251(a6)
    bne.w h0_108F2
h0_98FE:
    bra.w h0_A9DA
h0_9902:
    moveq.l #38,d0
    bra.w h0_8556
h0_9908:
    cmpi.b #255,$011D(a6)
    beq.s h0_9938
h0_9910:
    tst.b $00FF(a6)
    beq.w h0_9E50
h0_9918:
    tst.w $0250(a6)
    beq.w h0_A69A
h0_9920:
    btst.b #1,$0251(a6)
    bne.w h0_AEEC
h0_992A:
    btst.b #2,$0251(a6)
    bne.w h0_10AD6
h0_9934:
    bra.w h0_9E50
h0_9938:
    rts
h0_993A:
    move.l $026E(a6),d2
    moveq.l #1,d1
    clr.b (a5)+
    add.l d1,$026E(a6)
    add.l d1,$0256(a6)
    tst.b $026A(a6)
    beq.s h0_995E
h0_9950:
    tst.b $0104(a6)
    beq.s h0_995E
h0_9956:
    bsr.s h0_9908
h0_9958:
    beq.s h0_995E
h0_995A:
    bsr.w h0_98CE
h0_995E:
    movea.l $027E(a6),a5
    move.l a5,$0282(a6)
    rts
    DC.L    $4a2e00ff,$670004ea,$4a6e0250,$67000d84,$082e0001,$02516600,$104e082e,$00020251
    DC.L    $66001044,$60001040 ; VIOLATION: orphaned code island at $9968 is not reached from known entrypoints
h0_9990:
    tst.b $011D(a6)
    bne.s h0_99BE
h0_9996:
    tst.b $00FF(a6)
    beq.w h0_A442
h0_999E:
    tst.w $0250(a6)
    beq.w h0_A920
h0_99A6:
    btst.b #1,$0251(a6)
    bne.w h0_AEDE
h0_99B0:
    btst.b #2,$0251(a6)
    bne.w h0_AEDE
h0_99BA:
    bra.w h0_A442
h0_99BE:
    moveq.l #79,d1
    bsr.w h0_931A
h0_99C4:
    bra.w h0_8F18
h0_99C8:
    moveq.l #40,d0
    jmp h0_853E.l
h0_99D0:
    tst.l $01C8(a6)
    bne.w h0_88EA
h0_99D8:
    tst.l $01B4(a6)
    bne.s h0_9A08
h0_99DE:
    movem.l d1-d2/a0-a2,-(a7)
    lea.l $06FE(a6),a0
    bsr.w h0_9A0A
h0_99EA:
    bne.s h0_99C8
h0_99EC:
    move.l d2,$01B4(a6)
    move.l $01D0(a6),d0
    beq.s h0_9A04
h0_99F6:
    movea.l d0,a1
    movea.l $0040(a1),a1
    move.l a1,d0
    beq.s h0_9A04
h0_9A00:
    move.b (a0)+,(a1)+
    bne.s h0_9A00
h0_9A04:
    movem.l (a7)+,d1-d2/a0-a2
h0_9A08:
    rts
h0_9A0A:
    lea.l $0750(a6),a1
    move.b (a0),d0
    beq.s h0_9A2A
h0_9A12:
    cmp.b #$2E,d0
    bne.s h0_9A6C
h0_9A18:
    move.b $0001(a0),d0
    cmp.b #$2E,d0
    beq.s h0_9A6C
h0_9A22:
    cmp.b #$5C,d0
    beq.s h0_9A6C
h0_9A28:
    move.b (a0),d0
h0_9A2A:
    move.l a1,d2
h0_9A2C:
    tst.b (a1)+
    bne.s h0_9A2C
h0_9A30:
    sub.l a1,d2
    neg.l d2
    tst.b d0
    bne.s h0_9A3C
h0_9A38:
    bsr.w h0_9750
h0_9A3C:
    subq.l #1,a1
    subq.b #1,d2
    bsr.w h0_9A58
h0_9A44:
    bsr.w h0_BFC4
h0_9A48:
    lea.l $0750(a6),a0
    rts
h0_9A4E:
    lea.l $06FE(a6),a0
    lea.l $0750(a6),a1
    moveq.l #0,d2
h0_9A58:
    cmp.b #$52,d2
    beq.s h0_9A66
h0_9A5E:
    addq.b #1,d2
    move.b (a0)+,d1
    move.b d1,(a1)+
    bne.s h0_9A58
h0_9A66:
    lea.l $0750(a6),a0
    rts
h0_9A6C:
    tst.b (a0)+
    bne.s h0_9A6C
h0_9A70:
    move.b -$0002(a0),d0
    cmp.b #$5C,d0
    beq.s h0_9A9C
h0_9A7A:
    cmp.b #$3A,d0
    beq.s h0_9A9C
h0_9A80:
    lea.l $06FE(a6),a0
    bsr.w h0_BFC4
h0_9A88:
    beq.w h0_9AA4
h0_9A8C:
    bsr.s h0_9A4E
h0_9A8E:
    move.b #$5C,-$0001(a1)
h0_9A94:
    lea.l $07A2(a6),a0
    bsr.s h0_9A58
h0_9A9A:
    bra.s h0_9A38
h0_9A9C:
    bsr.s h0_9A4E
h0_9A9E:
    subq.w #1,a1
    subq.b #1,d2
    bra.s h0_9A94
h0_9AA4:
    lea.l $06FE(a6),a0
    rts
h0_9AAA:
    lea.l dat_9AE4(pc),a0
    move.l a0,$01A8(a6)
    move.l $027E(a6),d1
    tst.b $011D(a6)
    bne.s h0_9AE8
h0_9ABC:
    tst.b $00FF(a6)
    beq.w h0_9FE0
h0_9AC4:
    tst.w $0250(a6)
    beq.w h0_A638
h0_9ACC:
    btst.b #1,$0251(a6)
    bne.w h0_AE04
h0_9AD6:
    btst.b #2,$0251(a6)
    bne.w h0_109B6
h0_9AE0:
    bra.w h0_9FE0
dat_9AE4:
    DC.L    $42ae01b0
h0_9AE8:
    rts
h0_9AEA:
    tst.b $00FF(a6)
    beq.w h0_A008
h0_9AF2:
    tst.w $0250(a6)
    beq.w h0_A618
h0_9AFA:
    btst.b #1,$0251(a6)
    bne.w h0_AD68
h0_9B04:
    btst.b #2,$0251(a6)
    bne.w h0_1091C
h0_9B0E:
    bra.w h0_A008
h0_9B12:
    tst.b $0104(a6)
    beq.s h0_9B40
h0_9B18:
    tst.b $00FF(a6)
    beq.w h0_A02C
h0_9B20:
    tst.w $0250(a6)
    beq.w h0_A812
h0_9B28:
    btst.b #1,$0251(a6)
    bne.w h0_AF1E
h0_9B32:
    btst.b #2,$0251(a6)
    bne.w h0_10AE6
h0_9B3C:
    bra.w h0_AAD0
h0_9B40:
    rts
h0_9B42:
    move.l $01B4(a6),d2
    beq.s h0_9B50
h0_9B48:
    bsr.w h0_BF68
h0_9B4C:
    clr.l $01B4(a6)
h0_9B50:
    rts
h0_9B52:
    move.l d2,-(a7)
h0_9B54:
    move.l #$50DA,d0
    sub.l d0,d1
    bcc.s h0_9B62
h0_9B5E:
    add.l d1,d0
    moveq.l #0,d1
h0_9B62:
    movea.l a6,a0
    move.l d1,-(a7)
    move.l d0,d1
    bsr.w h0_84F2
h0_9B6C:
    move.l (a7)+,d1
    bne.s h0_9B54
h0_9B70:
    move.l (a7)+,d2
    rts
h0_9B74:
    tst.w $0250(a6)
    beq.w h0_A830
h0_9B7C:
    btst.b #1,$0251(a6)
    bne.w h0_B45C
h0_9B86:
    btst.b #2,$0251(a6)
    bne.w h0_10B02
h0_9B90:
    bra.w h0_AA0E
h0_9B94:
    tst.w $0250(a6)
    beq.w h0_A836
h0_9B9C:
    btst.b #1,$0251(a6)
    bne.w h0_B41A
h0_9BA6:
    btst.b #2,$0251(a6)
    bne.w h0_10AFE
h0_9BB0:
    bra.w h0_AA7C
h0_9BB4:
    tst.b $0114(a6)
    beq.s h0_9BC0
h0_9BBA:
    tst.w $0250(a6)
    bne.s h0_9BEA
h0_9BC0:
    cmp.b #$1,d3
    bne.s h0_9BCA
h0_9BC6:
    st.b $0116(a6)
h0_9BCA:
    tst.w $0250(a6)
    beq.w h0_A814
h0_9BD2:
    btst.b #1,$0251(a6)
    bne.w h0_B406
h0_9BDC:
    btst.b #2,$0251(a6)
    bne.w h0_10AFA
h0_9BE6:
    bra.w h0_AA48
h0_9BEA:
    rts
h0_9BEC:
    tst.w $0250(a6)
    beq.w h0_A82C
h0_9BF4:
    btst.b #1,$0251(a6)
    bne.w h0_B426
h0_9BFE:
    btst.b #2,$0251(a6)
    bne.w h0_10AFE
h0_9C08:
    bra.w h0_AA6C
    DC.L    $4a6e0250,$67000c1a,$082e0001,$02516600,$17fe082e,$00020251,$66006ed8,$60000e42 ; VIOLATION: orphaned code island at $9C0C is not reached from known entrypoints
h0_9C2C:
    tst.w $0250(a6)
    beq.w h0_A828
h0_9C34:
    btst.b #1,$0251(a6)
    bne.w h0_B41A
h0_9C3E:
    btst.b #2,$0251(a6)
    bne.w h0_10AFE
h0_9C48:
    bra.w h0_AA6C
h0_9C4C:
    tst.w $0250(a6)
    beq.w h0_A824
h0_9C54:
    btst.b #1,$0251(a6)
    bne.w h0_B440
h0_9C5E:
    btst.b #2,$0251(a6)
    bne.w h0_10B02
h0_9C68:
    bra.w h0_AA0E
h0_9C6C:
    tst.w $0250(a6)
    beq.w h0_A820
h0_9C74:
    btst.b #1,$0251(a6)
    bne.w h0_B464
h0_9C7E:
    btst.b #2,$0251(a6)
    bne.w h0_10B02
h0_9C88:
    bra.w h0_AA0E
h0_9C8C:
    tst.b $0107(a6)
    beq.s h0_9C98
h0_9C92:
    moveq.l #60,d0
    bra.w h0_8556
h0_9C98:
    tst.b $0114(a6)
    bne.s h0_9CE0
h0_9C9E:
    movem.l d1-d2,-(a7)
    st.b $0116(a6)
    move.l a5,d0
    sub.l $027E(a6),d0
    add.l $026E(a6),d0
    pea.l dat_9CDC(pc)
    tst.b $00FF(a6)
    beq.w h0_A398
h0_9CBC:
    tst.w $0250(a6)
    beq.w h0_A64E
h0_9CC4:
    btst.b #1,$0251(a6)
    bne.w h0_B3FA
h0_9CCE:
    btst.b #2,$0251(a6)
    bne.w h0_10AF8
h0_9CD8:
    bra.w h0_A9AA
dat_9CDC:
    DC.L    $4cdf0006
h0_9CE0:
    rts
    DC.B    $70,$00 ; VIOLATION: orphaned code island at $9CE2 is not reached from known entrypoints
    DC.L    $102e014c,$220292ae,$026e4a2e,$00ff6700,$071e4a6e,$02506700,$09d2082e,$00010251
    DC.L    $66001008,$082e0002,$02516600,$6bac6000
    DC.B    $0c,$ce
    DC.B    $70,$00 ; VIOLATION: orphaned code island at $9D16 is not reached from known entrypoints
    DC.L    $102e014c,$222e026e,$4a2e00ff,$6700ad92,$4a6e0250,$6700098c,$082e0001,$02516600
    DC.L    $0ffa082e,$00020251,$66006bac,$6000ad72
h0_9D48:
    rts
    DC.B    $41,$fa ; VIOLATION: orphaned code island at $9D4A is not reached from known entrypoints
    DC.L    $002ab308,$6622b308,$661eb308,$661ab308,$6616b308,$66122f0c,$2849121c
    DC.B    $4e,$b9
    DC.L    h0_175A
    DC.B    $2d,$42
    DC.L    $4b10285f
    DC.B    "NuHEAD=",0
h0_9D7C:
    tst.l $01C8(a6)
    bne.w h0_9DF2
h0_9D84:
    move.l #$104,d1
    add.l $0184(a6),d1
    move.l #$1200,d2
    bsr.w h0_C01E
h0_9D98:
    move.l d1,$4AE4(a6)
    move.l d1,$4AE8(a6)
    bsr.w h0_9146
h0_9DA4:
    move.l a0,$4AE0(a6)
    move.l a0,$4AEC(a6)
    move.l a0,$027E(a6)
    move.l #$82,d1
    add.l $0190(a6),d1
    move.l #$1200,d2
    bsr.w h0_C01E
h0_9DC4:
    move.l d1,$4AF8(a6)
    move.l d1,$4AFC(a6)
    bsr.w h0_9146
h0_9DD0:
    move.l a0,$4AF4(a6)
    move.l a0,$4B00(a6)
    moveq.l #0,d0
    move.l d0,$4B08(a6)
    moveq.l #28,d0
    move.l d0,$4AF0(a6)
    add.l $0184(a6),d0
    move.l d0,$4B04(a6)
h0_9DEC:
    clr.l $4B10(a6)
    rts
h0_9DF2:
    moveq.l #28,d1
    add.l $01C8(a6),d1
    move.l d1,$4AE0(a6)
    move.l d1,$4AEC(a6)
    move.l d1,$027E(a6)
    move.l $0184(a6),d2
    move.l d1,$4AE4(a6)
    move.l d1,$4AE8(a6)
    add.l d2,d1
    move.l $0190(a6),$4AF8(a6)
    move.l $0190(a6),$4AFC(a6)
    move.l d1,$4AF4(a6)
    move.l d1,$4B00(a6)
    moveq.l #28,d1
    add.l $0184(a6),d1
    add.l $0190(a6),d1
    cmp.l $01CC(a6),d1
    bcc.w h0_88EA
h0_9E38:
    movea.l $01C8(a6),a1
    clr.w (a1)+
    move.l $0184(a6),(a1)+
    move.l $0190(a6),(a1)+
    move.l $019C(a6),(a1)+
    clr.l (a1)+
    clr.b (a1)+
    bra.s h0_9DEC
h0_9E50:
    cmpi.b #24,$014C(a6)
    rts
    DC.L    $102e014c,$673cb03c,$000c6600,$e6c62002,$d081b0ae,$4afc6f34,$48e76080,$6100fb5a
    DC.L    $43ee4af4,$222e4b04,$610000ea,$4cdf0106,$d081b0ae,$4b086f04,$2d404b08,$d3ae4b04 ; VIOLATION: orphaned code island at $9E58 is not reached from known entrypoints
    DC.B    $60,$3e
    DC.B    $20,$02 ; VIOLATION: orphaned code island at $9E9A is not reached from known entrypoints
    DC.L    $d081b0ae,$4ae86e0c,$d3ae027e,$1ad85381,$66fa4e75
    DC.L    $48e76080,$6100fb1a,$43ee4ae0,$222e4af0,$610000aa,$4cdf0106,$d081b0ae,$4b086f04
    DC.L    $2d404b08,$d3ae4af0,$08000000,$670452ae,$027e6000 ; VIOLATION: orphaned code island at $9EB0 is not reached from known entrypoints
    DC.B    $e6,$0e
h0_9EE6:
    moveq.l #0,d0
    move.b $014C(a6),d0
    beq.s h0_9EF8
h0_9EEE:
    cmp.b #$C,d0
    beq.s h0_9F26
h0_9EF4:
    bra.w h0_852A
h0_9EF8:
    move.l d2,d0
    addi.l #256,d0
    cmp.l $4AE8(a6),d0
    bcc.s h0_9F0C
h0_9F06:
    add.l d1,$027E(a6)
    rts
h0_9F0C:
    tst.l $01C8(a6)
    bne.s h0_9F06
h0_9F12:
    bsr.w h0_99D0
h0_9F16:
    lea.l $4AE0(a6),a1
    move.l $4AF0(a6),d1
    bsr.s h0_9F54
h0_9F20:
    add.l d1,$4AE8(a6)
    rts
h0_9F26:
    move.l d2,d0
    addi.l #256,d0
    cmp.l $4AFC(a6),d0
    bcc.s h0_9F3A
h0_9F34:
    add.l d1,$027E(a6)
    rts
h0_9F3A:
    tst.l $01C8(a6)
    bne.s h0_9F34
h0_9F40:
    bsr.w h0_99D0
h0_9F44:
    lea.l $4AF4(a6),a1
    move.l $4B04(a6),d1
    bsr.s h0_9F54
h0_9F4E:
    add.l d1,$4AFC(a6)
    rts
h0_9F54:
    move.l a5,d0
    andi.b #1,d0
    beq.s h0_9F6C
h0_9F5C:
    move.b -(a5),-(a7)
    bsr.s h0_9F6C
h0_9F60:
    movea.l $027E(a6),a0
    move.b (a7)+,(a0)+
    move.l a0,$027E(a6)
    rts
h0_9F6C:
    tst.l $01C8(a6)
    bne.w h0_88EA
h0_9F74:
    move.l a1,-(a7)
    cmp.l $4B08(a6),d1
    ble.s h0_9F8C
h0_9F7C:
    move.l d1,-(a7)
    sub.l $4B08(a6),d1
    add.l d1,$4B08(a6)
    bsr.w h0_9B52
h0_9F8A:
    move.l (a7)+,d1
h0_9F8C:
    movea.l (a7),a1
    move.l d1,$0010(a1)
    move.l d1,d2
    bsr.w h0_BFFE
h0_9F98:
    movea.l (a7)+,a1
    movea.l (a1),a0
    move.l a5,d1
    move.l a0,$027E(a6)
    sub.l a0,d1
    add.l d1,$0010(a1)
    move.l $0010(a1),-(a7)
    move.l d1,-(a7)
    bsr.w h0_84F2
h0_9FB2:
    move.l (a7)+,d1
    move.l (a7)+,d0
    cmp.l $4B08(a6),d0
    ble.s h0_9FC0
h0_9FBC:
    move.l d0,$4B08(a6)
h0_9FC0:
    rts
h0_9FC2:
    lea.l $0180(a6),a0
    moveq.l #0,d0
    move.b $014C(a6),d0
    move.l $0256(a6),d2
    sub.l $4B14(a6),d2
    add.l d2,$4(a0,d0.w)
    move.l $026E(a6),$C(a0,d0.w)
    rts
h0_9FE0:
    tst.b $026A(a6)
    beq.s h0_9FC2
h0_9FE6:
    move.b $014C(a6),d0
    beq.s h0_9FF4
h0_9FEC:
    cmp.b #$C,d0
    beq.s h0_9FFA
h0_9FF2:
    rts
h0_9FF4:
    move.l d1,$4AEC(a6)
    rts
h0_9FFA:
    move.l d1,$4B00(a6)
    rts
h0_A000:
    move.l $0256(a6),$4B14(a6)
    rts
h0_A008:
    tst.b $026A(a6)
    beq.s h0_A000
h0_A00E:
    move.b $014C(a6),d0
    beq.s h0_A01C
h0_A014:
    cmp.b #$C,d0
    beq.s h0_A024
h0_A01A:
    rts
h0_A01C:
    move.l $4AEC(a6),$027E(a6)
    rts
h0_A024:
    move.l $4B00(a6),$027E(a6)
    rts
h0_A02C:
    tst.l $01C8(a6)
    bne.w h0_A2BE
h0_A034:
    bsr.w h0_99D0
h0_A038:
    lea.l $4AE0(a6),a1
    move.l $4AF0(a6),d1
    movea.l $4AEC(a6),a5
    bsr.w h0_9F6C
h0_A048:
    lea.l $4AF4(a6),a1
    move.l $4B04(a6),d1
    movea.l $4B00(a6),a5
    bsr.w h0_9F6C
h0_A058:
    btst.b #0,$4B0B(a6)
    beq.s h0_A06C
h0_A060:
    moveq.l #1,d1
    lea.l $05DE(a6),a0
    clr.b (a0)
    bsr.w h0_84F2
h0_A06C:
    clr.l $4B0C(a6)
    tst.b $0105(a6)
    beq.w h0_A172
h0_A078:
    movea.l $4AE0(a6),a4
    move.l $4AE4(a6),d4
    lea.l h0_A094(pc),a2
    movea.l $0144(a6),a1
    bsr.w h0_8D7C
h0_A08C:
    bsr.w h0_A138
h0_A090:
    bra.w h0_A172
h0_A094:
    move.b $000D(a1),d0
    cmp.b #$1,d0
    bne.w h0_A136
h0_A0A0:
    moveq.l #0,d2
    move.w #$A200,d1
    move.b $000E(a1),d0
    beq.s h0_A0C2
h0_A0AC:
    move.l $0198(a6),d2
    move.w #$A100,d1
    cmp.b #$18,d0
    beq.s h0_A0C2
h0_A0BA:
    move.l $018C(a6),d2
    move.w #$A400,d1
h0_A0C2:
    add.l $0008(a1),d2
    move.l d2,-(a7)
    move.b $0016(a1),d0
    lea.l $0017(a1),a0
    tst.b $0105(a6)
    bpl.s h0_A114
h0_A0D6:
    cmp.b #$9,d0
    bcs.s h0_A114
h0_A0DC:
    moveq.l #28,d2
    cmp.l d2,d4
    bge.s h0_A0E4
h0_A0E2:
    bsr.s h0_A138
h0_A0E4:
    sub.l d2,d4
    moveq.l #7,d2
h0_A0E8:
    move.b (a0)+,(a4)+
    dbf.w d2,h0_A0E8
h0_A0EE:
    move.b #$48,d1
    move.w d1,(a4)+
    move.l (a7)+,(a4)+
    subi.b #9,d0
    ext.w d0
    lea.l $000E(a4),a4
    move.l a4,-(a7)
    clr.l -(a4)
    clr.l -(a4)
    clr.l -(a4)
    clr.w -(a4)
h0_A10A:
    move.b (a0)+,(a4)+
    dbf.w d0,h0_A10A
h0_A110:
    movea.l (a7)+,a4
    rts
h0_A114:
    moveq.l #14,d2
    cmp.l d2,d4
    bge.s h0_A11C
h0_A11A:
    bsr.s h0_A138
h0_A11C:
    sub.l d2,d4
    moveq.l #7,d2
h0_A120:
    move.b (a0)+,(a4)+
    subq.b #1,d0
    dbeq.w d2,h0_A120
h0_A128:
    subq.w #1,d2
    bmi.s h0_A132
h0_A12C:
    clr.b (a4)+
    dbf.w d2,h0_A12C
h0_A132:
    move.w d1,(a4)+
    move.l (a7)+,(a4)+
h0_A136:
    rts
h0_A138:
    tst.l $01C8(a6)
    bne.w h0_88EA
h0_A140:
    movem.l d0-d3/a0-a3,-(a7)
    move.l $4AE4(a6),d1
    sub.l d4,d1
    beq.s h0_A15A
h0_A14C:
    add.l d1,$4B0C(a6)
    movea.l $4AE0(a6),a0
    movea.l a0,a4
    bsr.w h0_84F2
h0_A15A:
    movem.l (a7)+,d0-d3/a0-a3
    move.l $4AE4(a6),d4
    rts
    DC.B    $26,$6e,$4a,$e0,$28,$2e,$4a,$e4,$42,$9b,$60,$00,$00,$c2 ; VIOLATION: orphaned code island at $A164 is not reached from known entrypoints
h0_A172:
    movea.l $4AE0(a6),a3
    move.l $4AE4(a6),d4
    bsr.s h0_A180
h0_A17C:
    bra.w h0_A232
h0_A180:
    move.l $0188(a6),d0
    or.l $0194(a6),d0
    bne.s h0_A18E
h0_A18A:
    clr.l (a3)+
    rts
h0_A18E:
    moveq.l #0,d3
    sf.b d6
    lea.l $0188(a6),a1
    tst.l (a1)
    bne.s h0_A1A4
h0_A19A:
    lea.l $0194(a6),a1
    st.b d6
    move.l $0184(a6),d3
h0_A1A4:
    movea.l (a1),a1
    lea.l $000A(a1),a0
    moveq.l #50,d2
    sub.w $0008(a1),d2
    move.l (a0)+,d0
    add.l d3,d0
    move.l d0,(a3)+
    subq.l #4,d4
h0_A1B8:
    subq.w #1,d2
    beq.s h0_A1E0
h0_A1BC:
    move.l (a0)+,d1
    add.l d3,d1
    move.l d1,d5
    sub.l d0,d1
h0_A1C4:
    cmp.l #$FE,d1
    ble.s h0_A1DA
h0_A1CC:
    move.l d1,-(a7)
    moveq.l #1,d1
    bsr.s h0_A206
h0_A1D2:
    moveq.l #-127,d1
    add.l d1,d1
    add.l (a7)+,d1
    bra.s h0_A1C4
h0_A1DA:
    bsr.s h0_A206
h0_A1DC:
    move.l d5,d0
    bra.s h0_A1B8
h0_A1E0:
    tst.l (a1)
    beq.s h0_A1F2
h0_A1E4:
    movea.l (a1),a1
    lea.l $000A(a1),a0
    moveq.l #50,d2
    sub.w $0008(a1),d2
    bra.s h0_A1BC
h0_A1F2:
    tst.b d6
    bne.s h0_A204
h0_A1F6:
    st.b d6
    lea.l $0194(a6),a1
    move.l $0184(a6),d3
    tst.l (a1)
    bne.s h0_A1E0
h0_A204:
    moveq.l #0,d1
h0_A206:
    move.b d1,(a3)+
    subq.l #1,d4
    beq.s h0_A20E
h0_A20C:
    rts
h0_A20E:
    tst.l $01C8(a6)
    bne.w h0_88EA
h0_A216:
    movem.l d0-d2/a0-a2,-(a7)
    movea.l $4AE0(a6),a0
    move.l a3,d1
    sub.l a0,d1
    movea.l a0,a3
    bsr.w h0_84F2
h0_A228:
    move.l $4AE4(a6),d4
    movem.l (a7)+,d0-d2/a0-a2
    rts
h0_A232:
    tst.b $012B(a6)
    beq.s h0_A240
h0_A238:
    btst #0,d4
    beq.s h0_A240
h0_A23E:
    bsr.s h0_A204
h0_A240:
    bsr.s h0_A20E
h0_A242:
    bsr.s h0_A274
h0_A244:
    moveq.l #0,d2
    bsr.w h0_BFFE
h0_A24A:
    lea.l $05DE(a6),a0
    move.w #$601A,(a0)+
    move.l $0184(a6),(a0)+
    move.l $0190(a6),(a0)+
    move.l $019C(a6),(a0)+
    move.l $4B0C(a6),(a0)+
    clr.l (a0)+
    move.l $4B10(a6),(a0)+
    clr.w (a0)+
    lea.l $05DE(a6),a0
    moveq.l #28,d1
    bra.w h0_84F2
h0_A274:
    tst.b $012B(a6)
    beq.w h0_A298
h0_A27C:
    lea.l dat_A29A(pc),a0
    moveq.l #36,d1
    bsr.w h0_84F2
h0_A286:
    bsr.w h0_B260
h0_A28A:
    moveq.l #0,d6
    lea.l dat_8BFE(pc),a2
    bsr.w h0_8D20
h0_A294:
    bra.w h0_B246
h0_A298:
    rts
dat_A29A:
    DC.B    $00,$00
    DC.L    $03f10000,$00070000,$00004845
    DC.B    "ADDBGV01",0
    DC.B    $00,$00,$00
    DC.L    $00000000,$00000000
    DC.B    $00,$00
h0_A2BE:
    moveq.l #0,d2
    move.l $01CC(a6),d4
    sub.l $0184(a6),d4
    sub.l $0190(a6),d4
    subi.l #30,d4
    tst.b $0105(a6)
    beq.s h0_A30C
h0_A2D8:
    movea.l $01C8(a6),a4
    lea.l $001C(a4),a4
    adda.l $0184(a6),a4
    adda.l $0190(a6),a4
    move.l d4,-(a7)
    lea.l h0_A094(pc),a2
    movea.l $0144(a6),a1
    bsr.w h0_8D7C
h0_A2F6:
    move.l (a7)+,d2
    sub.l d4,d2
    beq.s h0_A30C
h0_A2FC:
    movea.l $01C8(a6),a0
    addq.l #2,d2
    subq.l #2,d4
    bcs.w h0_88EA
h0_A308:
    move.l d2,$000E(a0)
h0_A30C:
    movea.l $01C8(a6),a3
    move.l $4B10(a6),$0016(a3)
    lea.l $001C(a3),a3
    adda.l $0184(a6),a3
    adda.l $0190(a6),a3
    adda.l d2,a3
    bsr.w h0_A180
h0_A328:
    movea.l a3,a4
    btst #0,d4
    beq.s h0_A334
h0_A330:
    clr.b (a4)+
    subq.l #1,d4
h0_A334:
    tst.b $012B(a6)
    beq.s h0_A344
h0_A33A:
    moveq.l #0,d6
    lea.l h0_8C96(pc),a2
    bsr.w h0_8D20
h0_A344:
    cmp.l #$4,d4
    bcs.w h0_88EA
h0_A34E:
    move.l #$3F2,(a4)+
    movea.l $01C8(a6),a0
    move.w #$601A,(a0)
    rts
h0_A35E:
    moveq.l #0,d1
    move.b $0016(a1),d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_A372
h0_A36C:
    andi.b #252,d1
    addq.l #4,d1
h0_A372:
    lsr.l #2,d1
    move.l d1,(a4)+
    lea.l $0016(a1),a0
    move.b (a0)+,d0
h0_A37C:
    move.b (a0)+,(a4)+
    subq.b #1,d0
    bne.s h0_A37C
h0_A382:
    move.b $0016(a1),d0
    andi.b #3,d0
    beq.s h0_A396
h0_A38C:
    clr.b (a4)+
    addq.b #1,d0
    cmp.b #$4,d0
    bne.s h0_A38C
h0_A396:
    rts
h0_A398:
    move.l d0,d2
    movea.l $0148(a6),a1
    moveq.l #0,d0
    move.b $000E(a1),d0
    cmp.b #$18,d0
    beq.w h0_9C92
h0_A3AC:
    tst.b $0104(a6)
    bne.s h0_A3B4
h0_A3B2:
    rts
h0_A3B4:
    move.l a2,-(a7)
    lea.l $0188(a6),a1
    adda.w d0,a1
    movea.l (a1),a2
    tst.l (a1)
    bne.s h0_A3EA
h0_A3C2:
    bsr.s h0_A3CC
h0_A3C4:
    movea.l a0,a2
    move.l a0,$0004(a2)
    bra.s h0_A3FC
h0_A3CC:
    movem.l a1-a2,-(a7)
    move.l #$D2,d1
    bsr.w h0_9146
h0_A3DA:
    movem.l (a7)+,a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.w #$32,$0008(a0)
    rts
h0_A3EA:
    movea.l $0004(a2),a0
    tst.w $0008(a0)
    bne.s h0_A3FC
h0_A3F4:
    movea.l a0,a1
    bsr.s h0_A3CC
h0_A3F8:
    move.l a0,$0004(a2)
h0_A3FC:
    moveq.l #50,d0
    sub.w $0008(a0),d0
    add.w d0,d0
    add.w d0,d0
    subq.w #1,$0008(a0)
    move.l d2,$A(a0,d0.w)
    movea.l (a7)+,a2
    rts
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $A412 is not reached from known entrypoints
    DC.L    $026a671c,$4a2e0104,$6716b03c,$00186710,$b03c000c,$6706d3ae,$4ae8600e
    DC.B    $d3,$ae,$4a,$fc,$b0,$3c,$00,$18,$66,$04,$70,$ff,$4e,$75 ; VIOLATION: orphaned code island at $A430 is not reached from known entrypoints
    DC.B    $70,$00,$4e,$75 ; VIOLATION: orphaned code island at $A43E is not reached from known entrypoints
h0_A442:
    moveq.l #84,d1
    tst.b d0
    beq.s h0_A452
h0_A448:
    moveq.l #68,d1
    cmp.b #$C,d0
    beq.s h0_A452
h0_A450:
    moveq.l #66,d1
h0_A452:
    bsr.w h0_931A
h0_A456:
    bra.w h0_8F18
h0_A45A:
    lea.l dat_A466(pc),a0
    rts
h0_A460:
    lea.l dat_A477(pc),a0
    rts
dat_A466:
    DC.B    "Atari executable",0
dat_A477:
    DC.B    $2e,$50,$52,$47,$00,$12,$d8,$66,$fc,$53,$89,$4e,$75
h0_A484:
    tst.l $01C8(a6)
    bne.w h0_97E4
h0_A48C:
    move.l #$4000,d1
    move.l #$400,d2
    bsr.w h0_C01E
h0_A49C:
    move.l d1,$4B18(a6)
    move.l d1,$4B20(a6)
    bsr.w h0_9146
h0_A4A8:
    move.l a0,$4B1C(a6)
    move.l a0,$4B24(a6)
    rts
h0_A4B2:
    movea.l $4B24(a6),a2
    moveq.l #1,d1
    bsr.w h0_A7A6
h0_A4BC:
    lea.l $0016(a1),a0
    move.b (a0)+,d1
    subq.b #1,d1
    bsr.w h0_A7CE
h0_A4C8:
    move.l a2,$4B24(a6)
    lea.l h0_A57E(pc),a2
    moveq.l #0,d3
    moveq.l #0,d4
h0_A4D4:
    subq.b #1,d4
    move.l a7,$0394(a6)
    movea.l $0008(a1),a0
    bsr.w h0_8AF2
h0_A4E2:
    trap #15
h0_A4E4:
    cmp.b $000C(a1),d4
    bne.s h0_A4D4
h0_A4EA:
    movea.l $0168(a6),a1
    movea.l (a1),a1
    movea.l $4B24(a6),a2
    move.l a1,d0
    beq.s h0_A4FA
h0_A4F8:
    bsr.s h0_A500
h0_A4FA:
    move.l a2,$4B24(a6)
    rts
h0_A500:
    tst.l (a1)
    beq.s h0_A50C
h0_A504:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_A500
h0_A50A:
    movea.l (a7)+,a1
h0_A50C:
    btst.b #4,$000C(a1)
    beq.s h0_A516
h0_A514:
    bsr.s h0_A528
h0_A516:
    tst.l $0004(a1)
    beq.s h0_A526
h0_A51C:
    move.l a1,-(a7)
    movea.l $0004(a1),a1
    bsr.s h0_A500
h0_A524:
    movea.l (a7)+,a1
h0_A526:
    rts
h0_A528:
    moveq.l #16,d1
    bsr.w h0_A7A6
h0_A52E:
    move.w $0014(a1),d1
    bsr.w h0_A7BA
h0_A536:
    lea.l $0016(a1),a0
    move.b (a0)+,d1
    bra.w h0_A7CE
h0_A540:
    movea.l $4B24(a6),a2
    moveq.l #6,d1
    bsr.w h0_A7A6
h0_A54A:
    lea.l $0016(a1),a0
    move.b (a0)+,d1
    bsr.w h0_A7CE
h0_A554:
    move.w $0008(a1),d1
    bsr.w h0_A7BA
h0_A55C:
    move.w $000A(a1),d1
    bsr.w h0_A7BA
h0_A564:
    move.b $000E(a1),d1
    ext.w d1
    cmpi.b #1,$000D(a1)
    beq.s h0_A574
h0_A572:
    moveq.l #0,d1
h0_A574:
    bsr.w h0_A7BA
h0_A578:
    move.l a2,$4B24(a6)
    rts
h0_A57E:
    cmp.b $000E(a0),d4
    beq.s h0_A586
h0_A584:
    rts
h0_A586:
    movem.l a0/a2,-(a7)
    movea.l $4B24(a6),a2
    moveq.l #16,d1
    bsr.w h0_A7A6
h0_A594:
    move.b $000E(a0),d1
    ext.w d1
    bsr.w h0_A7BA
h0_A59E:
    lea.l $0016(a0),a0
    move.b (a0)+,d1
    subq.b #1,d1
    bsr.w h0_A7CE
h0_A5AA:
    move.l a2,$4B24(a6)
    movem.l (a7)+,a0/a2
    movea.l $0394(a6),a7
    bra.w h0_A4E4
h0_A5BA:
    move.l $4B18(a6),d1
    sub.l $4B20(a6),d1
    moveq.l #16,d0
    add.b $05B4(a6),d0
    cmp.l d0,d1
    bne.s h0_A5E0
h0_A5CC:
    tst.l $01B4(a6)
    bne.s h0_A5E0
h0_A5D2:
    move.l $4B1C(a6),$4B24(a6)
    move.l $4B18(a6),$4B20(a6)
    rts
h0_A5E0:
    tst.b $0105(a6)
    beq.s h0_A5EE
h0_A5E6:
    lea.l h0_A5FE(pc),a2
    bsr.w h0_8D7C
h0_A5EE:
    movea.l $4B24(a6),a2
    moveq.l #19,d1
    bsr.w h0_A7A6
h0_A5F8:
    move.l a2,$4B24(a6)
    rts
h0_A5FE:
    cmpi.b #1,$000D(a1)
    bne.s h0_A616
h0_A606:
    moveq.l #-80,d0
    and.b $000C(a1),d0
    bne.s h0_A616
h0_A60E:
    move.l a2,-(a7)
    bsr.w h0_A540
h0_A614:
    movea.l (a7)+,a2
h0_A616:
    rts
h0_A618:
    tst.b $026A(a6)
    beq.s h0_A638
h0_A61E:
    movea.l $4B24(a6),a2
    moveq.l #4,d1
    bsr.w h0_A7A6
h0_A628:
    move.b $014C(a6),d1
    ext.w d1
    bsr.w h0_A7BA
h0_A632:
    move.l a2,$4B24(a6)
    rts
h0_A638:
    rts
h0_A63A:
    lea.l $4B30(a6),a1
    move.l a1,$4B28(a6)
    clr.l (a1)
    lea.l $4CF0(a6),a1
    move.l a1,$4B2C(a6)
    rts
h0_A64E:
    tst.b $0104(a6)
    beq.s h0_A698
h0_A654:
    movea.l $4B28(a6),a0
    move.l a5,(a0)+
    move.l $4B2C(a6),(a0)+
    move.w #$4,(a0)+
    move.l a0,$4B28(a6)
    clr.l (a0)
    movea.l $4B2C(a6),a0
    move.b #$FB,(a0)+
    move.b #$7,(a0)+
    move.l d2,-(a7)
    movea.l a7,a1
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    move.b #$54,(a0)+
    move.b #$2B,(a0)+
    st.b (a0)+
    move.b $014C(a6),(a0)+
    move.b #$FB,(a0)+
    move.l a0,$4B2C(a6)
    addq.l #4,a7
h0_A698:
    rts
h0_A69A:
    moveq.l #-1,d0
    rts
    DC.B    "$nK$r" ; VIOLATION: orphaned code island at $A69E is not reached from known entrypoints
    DC.B    $02
    DC.L    $61000100,$0202007f,$12022049,$6100011c
    DC.B    "-JK$Nu"
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $A6BA is not reached from known entrypoints
    DC.L    $026a6738,$4a2e0104
    DC.B    "g2$nK$r"
    DC.B    $05,$60,$12
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $A6CE is not reached from known entrypoints
    DC.L    $026a6724,$4a2e0104,$671e246e,$4b247203,$610000c4,$22024841,$610000d0,$48416100
    DC.L    $00ca2d4a,$4b247000
    DC.B    $4e,$75
    DC.B    "$nK$&.K S" ; VIOLATION: orphaned code island at $A6FA is not reached from known entrypoints
    DC.B    $81
    DC.L    $650e1018,$6114b03c,$00fb66f2,$610c60ee
    DC.B    $2d,$43,$4b,$20,$2d,$4a,$4b,$24,$4e,$75 ; VIOLATION: orphaned code island at $A714 is not reached from known entrypoints
    DC.B    $53,$83,$65,$04,$14,$c0,$4e,$75 ; VIOLATION: orphaned code island at $A71E is not reached from known entrypoints
    DC.B    $52,$83,$2d,$43,$4b,$20,$61,$00,$00,$bc,$26,$2e,$4b,$20,$60,$e8 ; VIOLATION: orphaned code island at $A726 is not reached from known entrypoints
h0_A736:
    movea.l $4B24(a6),a2
    movea.l $027E(a6),a1
    move.l $4B20(a6),d3
    moveq.l #-5,d2
    tst.l $4B30(a6)
    bne.w h0_A8B6
h0_A74C:
    subq.l #1,d3
    bcs.s h0_A77E
h0_A750:
    move.b (a1)+,d0
    move.b d0,(a2)+
    cmp.b d2,d0
    beq.s h0_A766
h0_A758:
    subq.l #1,d1
    bne.s h0_A74C
h0_A75C:
    move.l d3,$4B20(a6)
    move.l a2,$4B24(a6)
    rts
h0_A766:
    subq.l #1,d3
    bne.s h0_A77A
h0_A76A:
    addq.l #1,d3
    move.l d3,$4B20(a6)
    bsr.w h0_A7EA
h0_A774:
    move.l $4B20(a6),d3
    subq.l #1,d3
h0_A77A:
    move.b d2,(a2)+
    bra.s h0_A758
h0_A77E:
    addq.l #1,d3
    move.l d3,$4B20(a6)
    bsr.w h0_A7EA
h0_A788:
    move.l $4B20(a6),d3
    bra.s h0_A74C
    DC.B    $52,$ae ; VIOLATION: orphaned code island at $A78E is not reached from known entrypoints
    DC.B    "K aVS"
    DC.B    $ae,$4b,$20
    DC.L    $65f414fc,$00fb4e75
h0_A7A0:
    addq.l #2,$4B20(a6)
    bsr.s h0_A7EA
h0_A7A6:
    subq.l #2,$4B20(a6)
    bcs.s h0_A7A0
h0_A7AC:
    move.b #$FB,(a2)+
    move.b d1,(a2)+
    rts
h0_A7B4:
    addq.l #2,$4B20(a6)
    bsr.s h0_A7EA
h0_A7BA:
    subq.l #2,$4B20(a6)
    bcs.s h0_A7B4
h0_A7C0:
    move.w d1,-(a7)
    move.b (a7),(a2)+
    move.b $0001(a7),(a2)+
    addq.l #2,a7
    rts
h0_A7CC:
    bsr.s h0_A7EA
h0_A7CE:
    ext.w d1
    ext.l d1
    cmp.l $4B20(a6),d1
    bge.s h0_A7CC
h0_A7D8:
    sub.l d1,$4B20(a6)
    subq.l #1,$4B20(a6)
    move.b d1,(a2)+
h0_A7E2:
    move.b (a0)+,(a2)+
    subq.b #1,d1
    bne.s h0_A7E2
h0_A7E8:
    rts
h0_A7EA:
    movem.l d0-d2/a0-a1,-(a7)
    bsr.w h0_99D0
h0_A7F2:
    movea.l $4B1C(a6),a0
    move.l $4B18(a6),d1
    sub.l $4B20(a6),d1
    bsr.w h0_84F2
h0_A802:
    movea.l $4B1C(a6),a2
    move.l $4B18(a6),$4B20(a6)
    movem.l (a7)+,d0-d2/a0-a1
    rts
h0_A812:
    bra.s h0_A7EA
h0_A814:
    moveq.l #20,d0
    cmp.b #$1,d3
    bne.s h0_A84A
h0_A81C:
    moveq.l #84,d0
    bra.s h0_A84A
h0_A820:
    moveq.l #1,d0
    bra.s h0_A83A
h0_A824:
    moveq.l #9,d0
    bra.s h0_A83A
h0_A828:
    moveq.l #2,d0
    bra.s h0_A83A
h0_A82C:
    moveq.l #10,d0
    bra.s h0_A83A
h0_A830:
    moveq.l #41,d0
    subq.l #1,d2
    bra.s h0_A84A
h0_A836:
    moveq.l #42,d0
    bra.s h0_A84A
h0_A83A:
    cmp.b #$1,d3
    bne.s h0_A84A
h0_A840:
    move.w d0,-(a7)
    moveq.l #2,d0
    bsr.w h0_8660
h0_A848:
    move.w (a7)+,d0
h0_A84A:
    movea.l $4B28(a6),a0
    move.l a5,(a0)+
    move.w d0,d3
    andi.b #7,d3
    adda.w d3,a5
    move.l $4B2C(a6),(a0)+
    move.w d3,(a0)+
    move.l a0,$4B28(a6)
    clr.l (a0)
    movea.l $4B2C(a6),a0
    move.b #$FB,(a0)+
    move.b #$7,(a0)+
    move.l d2,-(a7)
    movea.l a7,a1
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    move.b d0,(a0)+
    movea.l $47FA(a6),a1
    tst.b $010C(a6)
    beq.s h0_A89A
h0_A888:
    bpl.s h0_A890
h0_A88A:
    move.b #$2D,(a0)+
    bra.s h0_A894
h0_A890:
    move.b #$2B,(a0)+
h0_A894:
    st.b (a0)+
    move.b $014C(a6),(a0)+
h0_A89A:
    move.w (a1)+,d0
    beq.s h0_A8AA
h0_A89E:
    move.b d0,(a0)+
    move.w (a1)+,(a7)
    move.b (a7),(a0)+
    move.b $0001(a7),(a0)+
    bra.s h0_A89A
h0_A8AA:
    move.b #$FB,(a0)+
    move.l a0,$4B2C(a6)
    addq.l #4,a7
    rts
h0_A8B6:
    move.l d4,-(a7)
    lea.l $4B30(a6),a0
h0_A8BC:
    move.l (a0)+,d4
    beq.s h0_A900
h0_A8C0:
    sub.l a1,d4
    bsr.s h0_A910
h0_A8C4:
    movem.l a1/a3,-(a7)
    movea.l (a0)+,a1
    movea.l $4B2C(a6),a3
    move.w (a0)+,d0
    tst.l (a0)
    beq.s h0_A8D8
h0_A8D4:
    movea.l $0004(a0),a3
h0_A8D8:
    move.l a3,d4
    sub.l a1,d4
    cmp.l d3,d4
    ble.s h0_A8EC
h0_A8E0:
    move.l d3,$4B20(a6)
    bsr.w h0_A7EA
h0_A8E8:
    move.l $4B20(a6),d3
h0_A8EC:
    sub.l d4,d3
h0_A8EE:
    move.b (a1)+,(a2)+
    subq.l #1,d4
    bne.s h0_A8EE
h0_A8F4:
    movem.l (a7)+,a1/a3
    ext.l d0
    adda.l d0,a1
    sub.l d0,d1
    bra.s h0_A8BC
h0_A900:
    move.l d1,d4
    bsr.s h0_A910
h0_A904:
    move.l d3,$4B20(a6)
    move.l (a7)+,d4
    move.l a2,$4B24(a6)
    rts
h0_A910:
    tst.l d4
    beq.s h0_A91E
h0_A914:
    exg d4,d1
    sub.l d1,d4
    bsr.w h0_A74C
h0_A91C:
    exg d1,d4
h0_A91E:
    rts
h0_A920:
    move.b d0,d1
    bsr.w h0_8F3C
h0_A926:
    moveq.l #46,d1
    bra.w h0_931A
h0_A92C:
    lea.l dat_A938(pc),a0
    rts
h0_A932:
    lea.l dat_A945(pc),a0
    rts
dat_A938:
    DC.B    $47,$53,$54,$20,$6c,$69,$6e,$6b,$61,$62,$6c,$65,$00
dat_A945:
    DC.B    $2e,$42,$49,$4e,$00
h0_A94A:
    tst.l $01C8(a6)
    bne.w h0_97E4
h0_A952:
    move.l $0184(a6),d1
    add.l d1,d1
    addi.l #100,d1
    bsr.w h0_9146
h0_A962:
    move.l a0,$4AE0(a6)
    move.l a0,$4AEC(a6)
    move.l a0,$027E(a6)
    move.l $0184(a6),d1
    bsr.s h0_A990
h0_A974:
    move.l $0190(a6),d1
    add.l d1,d1
    addi.l #100,d1
    bsr.w h0_9146
h0_A984:
    move.l a0,$4AF4(a6)
    move.l a0,$4B00(a6)
    move.l $0190(a6),d1
h0_A990:
    adda.l d1,a0
    lsr.l #1,d1
    subq.l #1,d1
    bcs.s h0_A9A8
h0_A998:
    moveq.l #0,d0
h0_A99A:
    move.w d0,(a0)+
    dbf.w d1,h0_A99A
h0_A9A0:
    subi.l #65536,d1
    bcc.s h0_A99A
h0_A9A8:
    rts
h0_A9AA:
    tst.b $0104(a6)
    beq.s h0_A9CC
h0_A9B0:
    move.l $0184(a6),d0
    moveq.l #2,d2
    tst.b $014C(a6)
    beq.s h0_A9C2
h0_A9BC:
    move.l $0190(a6),d0
    moveq.l #1,d2
h0_A9C2:
    move.w #$5,$0(a5,d0.l)
    move.w d2,$2(a5,d0.l)
h0_A9CC:
    rts
    DC.B    $d3,$ae,$02,$7e,$1a,$d8,$53,$81,$66,$fa,$4e,$75 ; VIOLATION: orphaned code island at $A9CE is not reached from known entrypoints
h0_A9DA:
    add.l d1,$027E(a6)
    rts
h0_A9E0:
    rts
    DC.B    $70,$ff,$4e,$75 ; VIOLATION: orphaned code island at $A9E2 is not reached from known entrypoints
    DC.B    $b4,$7c ; VIOLATION: orphaned code island at $A9E6 is not reached from known entrypoints
    DC.L    $00066618,$41fa0018,$10194880,$1036007e,$b0186608,$534266f0,$50ee0138
    DC.B    "NuPASCAL"
h0_AA0C:
    addq.l #4,a7
h0_AA0E:
    moveq.l #68,d0
    bra.w h0_8556
h0_AA14:
    tst.b $0104(a6)
    beq.s h0_AA44
h0_AA1A:
    move.l $0184(a6),d2
    tst.b $014C(a6)
    beq.s h0_AA28
h0_AA24:
    move.l $0190(a6),d2
h0_AA28:
    movea.l $47FA(a6),a0
    move.w (a0)+,d0
    cmp.w #$2B2B,d0
    bne.s h0_AA0C
h0_AA34:
    move.w (a0)+,d0
    bpl.s h0_AA3A
h0_AA38:
    rts
h0_AA3A:
    subq.w #1,d0
    add.w d0,d0
    add.w d0,d0
    add.w d0,d0
    rts
h0_AA44:
    addq.l #4,a7
    rts
h0_AA48:
    move.l d2,(a5)+
    bsr.s h0_AA14
h0_AA4C:
    bmi.s h0_AA5E
h0_AA4E:
    move.w #$5,-$4(a5,d2.l)
    ori.b #4,d0
    move.w d0,-$2(a5,d2.l)
    rts
h0_AA5E:
    move.w #$5,-$4(a5,d2.l)
    bsr.s h0_AA8C
h0_AA66:
    move.w d0,-$2(a5,d2.l)
    rts
h0_AA6C:
    move.w d2,(a5)+
    bsr.s h0_AA14
h0_AA70:
    bmi.s h0_AA0E
h0_AA72:
    ori.b #4,d0
    move.w d0,-$2(a5,d2.l)
    rts
h0_AA7C:
    move.w d2,(a5)+
    bsr.s h0_AA14
h0_AA80:
    bmi.s h0_AA0E
h0_AA82:
    ori.b #6,d0
    move.w d0,-$2(a5,d2.l)
    rts
h0_AA8C:
    tst.b d0
    beq.s h0_AA9A
h0_AA90:
    cmp.b #$C,d0
    beq.s h0_AA9E
h0_AA96:
    moveq.l #3,d0
    rts
h0_AA9A:
    moveq.l #2,d0
    rts
h0_AA9E:
    moveq.l #1,d0
    rts
h0_AAA2:
    beq.s h0_AACE
h0_AAA4:
    tst.b $0138(a6)
    beq.s h0_AACE
h0_AAAA:
    movem.l d1/a0,-(a7)
    add.l d1,d1
    bsr.w h0_9146
h0_AAB4:
    movem.l (a7)+,d1/a1
    move.l a0,-(a7)
    move.l d1,d0
    lsr.l #1,d0
    lea.l $0(a1,d1.l),a2
h0_AAC2:
    move.w (a1)+,(a0)+
    move.w (a2)+,(a0)+
    subq.l #1,d0
    bne.s h0_AAC2
h0_AACA:
    movea.l (a7)+,a0
    add.l d1,d1
h0_AACE:
    rts
h0_AAD0:
    bsr.w h0_99D0
h0_AAD4:
    lea.l $05DE(a6),a0
    move.w #$601A,(a0)+
    move.l $0184(a6),(a0)+
    move.l $0190(a6),(a0)+
    move.l $019C(a6),(a0)+
    clr.l (a0)+
    clr.l (a0)+
    clr.l (a0)+
    moveq.l #0,d0
    tst.b $0138(a6)
    beq.s h0_AAFA
h0_AAF6:
    move.w #$4A4C,d0
h0_AAFA:
    move.w d0,(a0)+
    lea.l $05DE(a6),a0
    moveq.l #28,d1
    bsr.w h0_84F2
h0_AB06:
    movea.l $4AE0(a6),a0
    move.l $0184(a6),d1
    bsr.s h0_AAA2
h0_AB10:
    bsr.w h0_84F2
h0_AB14:
    movea.l $4AF4(a6),a0
    move.l $0190(a6),d1
    bsr.s h0_AAA2
h0_AB1E:
    bsr.w h0_84F2
h0_AB22:
    clr.l $4B0C(a6)
    movea.l $0168(a6),a1
    movea.l (a1),a1
    move.l a1,d0
    beq.w h0_AC26
h0_AB32:
    moveq.l #0,d7
    movea.l $0144(a6),a0
    move.w $0014(a0),d6
h0_AB3C:
    cmp.w d6,d7
    beq.w h0_AC26
h0_AB42:
    addq.w #1,d7
    move.l a7,$4B18(a6)
    movea.l $0168(a6),a1
    movea.l (a1),a1
    bsr.s h0_AB9E
h0_AB50:
    trap #15
h0_AB52:
    move.w #$8800,d2
    moveq.l #0,d3
    bsr.s h0_AB5C
h0_AB5A:
    bra.s h0_AB3C
h0_AB5C:
    lea.l $05DE(a6),a0
    moveq.l #0,d0
    move.l d0,(a0)
    move.l d0,$0004(a0)
    move.b $0016(a1),d0
    lea.l $0017(a1),a2
    cmp.w #$9,d0
    bcs.s h0_AB7A
h0_AB76:
    moveq.l #7,d0
h0_AB78:
    move.b (a2)+,(a0)+
h0_AB7A:
    dbf.w d0,h0_AB78
h0_AB7E:
    lea.l $05DE(a6),a0
    move.w d2,$0008(a0)
    move.l d3,$000A(a0)
    moveq.l #14,d1
    add.l d1,$4B0C(a6)
    move.l a1,-(a7)
    bsr.w h0_BFDA
h0_AB96:
    movea.l (a7)+,a1
    bne.w h0_84FA
h0_AB9C:
    rts
h0_AB9E:
    tst.l (a1)
    beq.s h0_ABAA
h0_ABA2:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_AB9E
h0_ABA8:
    movea.l (a7)+,a1
h0_ABAA:
    btst.b #4,$000C(a1)
    beq.s h0_ABBE
h0_ABB2:
    cmp.w $0014(a1),d7
    bne.s h0_ABBE
h0_ABB8:
    movea.l $4B18(a6),a7
    bra.s h0_AB52
h0_ABBE:
    tst.l $0004(a1)
    beq.s h0_ABCE
h0_ABC4:
    move.l a1,-(a7)
    movea.l $0004(a1),a1
    bsr.s h0_AB9E
h0_ABCC:
    movea.l (a7)+,a1
h0_ABCE:
    rts
h0_ABD0:
    move.w #$2000,d2
    btst.b #4,$000C(a1)
    bne.s h0_AC24
h0_ABDC:
    btst.b #5,$000C(a1)
    bne.s h0_ABEC
h0_ABE4:
    moveq.l #0,d2
    tst.b $0105(a6)
    beq.s h0_AC24
h0_ABEC:
    move.b $000D(a1),d0
    cmp.b #$1,d0
    beq.s h0_AC00
h0_ABF6:
    cmp.b #$2,d0
    bne.s h0_AC24
h0_ABFC:
    moveq.l #14,d3
    bra.s h0_AC12
h0_AC00:
    moveq.l #9,d3
    move.b $000E(a1),d0
    beq.s h0_AC12
h0_AC08:
    moveq.l #10,d3
    cmp.b #$C,d0
    beq.s h0_AC12
h0_AC10:
    moveq.l #8,d3
h0_AC12:
    bset d3,d2
    ori.w #32768,d2
    move.l $0008(a1),d3
    move.l a2,-(a7)
    bsr.w h0_AB5C
h0_AC22:
    movea.l (a7)+,a2
h0_AC24:
    rts
h0_AC26:
    movea.l $0144(a6),a1
    lea.l h0_ABD0(pc),a2
    bsr.w h0_8D7C
h0_AC32:
    movea.l $0170(a6),a1
    movea.l (a1),a1
    move.l a1,d0
    beq.s h0_AC40
h0_AC3C:
    bsr.w h0_8D86
h0_AC40:
    tst.b $0138(a6)
    bne.s h0_AC62
h0_AC46:
    movea.l $4AE0(a6),a0
    move.l $0184(a6),d1
    adda.l d1,a0
    bsr.w h0_84F2
h0_AC54:
    movea.l $4AF4(a6),a0
    move.l $0190(a6),d1
    adda.l d1,a0
    bsr.w h0_84F2
h0_AC62:
    tst.l $4B0C(a6)
    beq.s h0_AC78
h0_AC68:
    moveq.l #14,d2
    bsr.w h0_BFFE
h0_AC6E:
    lea.l $4B0C(a6),a0
    moveq.l #4,d1
    bsr.w h0_84F2
h0_AC78:
    rts
h0_AC7A:
    lea.l dat_AC90(pc),a0
    tst.b $0138(a6)
    beq.s h0_AC88
h0_AC84:
    lea.l dat_AC9D(pc),a0
h0_AC88:
    rts
h0_AC8A:
    lea.l dat_ACAA(pc),a0
    rts
dat_AC90:
    DC.B    $44,$52,$49,$20,$6c,$69,$6e,$6b,$61,$62,$6c,$65,$00
dat_AC9D:
    DC.B    $4f,$53,$53,$20,$6c,$69,$6e,$6b,$61,$62,$6c,$65,$00
dat_ACAA:
    DC.L    $2e4f0000
h0_ACAE:
    moveq.l #-1,d0
    move.l a1,-(a7)
h0_ACB2:
    move.b (a1)+,d1
    cmp.b #$D,d1
    beq.s h0_ACC6
h0_ACBA:
    cmp.b #$9,d1
    beq.s h0_ACC6
h0_ACC0:
    cmp.b #$20,d1
    bne.s h0_ACB2
h0_ACC6:
    move.l a1,d3
    movea.l (a7)+,a1
    sub.l a1,d3
    subq.l #1,d3
    beq.s h0_AD00
h0_ACD0:
    moveq.l #0,d2
h0_ACD2:
    addq.l #1,d0
    move.b (a2)+,d2
    beq.s h0_AD00
h0_ACD8:
    cmp.b d2,d3
    bcs.s h0_AD00
h0_ACDC:
    bne.s h0_ACFC
h0_ACDE:
    movem.l d2-d3/a1-a2,-(a7)
h0_ACE2:
    move.b (a1)+,d3
    ext.w d3
    move.b $7E(a6,d3.w),d3
    cmp.b (a2)+,d3
    bne.s h0_ACF8
h0_ACEE:
    subq.b #1,d2
    bne.s h0_ACE2
h0_ACF2:
    movem.l (a7)+,d2-d3/a1-a2
    rts
h0_ACF8:
    movem.l (a7)+,d2-d3/a1-a2
h0_ACFC:
    adda.l d2,a2
    bra.s h0_ACD2
h0_AD00:
    moveq.l #80,d0
    bsr.w h0_8556
h0_AD06:
    moveq.l #-1,d0
    rts
h0_AD0A:
    rts
h0_AD0C:
    rts
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $AD0E is not reached from known entrypoints
    DC.L    $0104671a,$226e01de,$4a2e026a,$6610222e,$026e92a9,$001cd3a9,$00142342,$001c7000
    DC.B    $4e,$75
    DC.B    $4a,$2e ; VIOLATION: orphaned code island at $AD32 is not reached from known entrypoints
    DC.L    $026a6718,$4a2e0104,$6712226e,$01de0c69,$03eb0012,$67069481,$d5ae027e,$70004e75
h0_AD54:
    movea.l $01DE(a6),a0
    cmpi.w #1003,$0012(a0)
    beq.w h0_852A
h0_AD62:
    add.l d1,$027E(a6)
    rts
h0_AD68:
    tst.b $026A(a6)
    bne.w h0_ADCE
h0_AD70:
    bsr.w h0_ADE8
h0_AD74:
    beq.s h0_ADC8
h0_AD76:
    movem.l a0-a1,-(a7)
    moveq.l #36,d1
    bsr.w h0_9146
h0_AD80:
    movem.l (a7)+,a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.l a2,$0004(a0)
    clr.l $0014(a0)
    clr.l $001C(a0)
    clr.l $0018(a0)
    move.l #$3E9,$0010(a0)
    tst.l $01C4(a6)
    beq.s h0_ADC2
h0_ADA6:
    movea.l $01C4(a6),a1
    lea.l dat_AE2E(pc),a2
    bsr.w h0_ACAE
h0_ADB2:
    bne.s h0_ADC2
h0_ADB4:
    add.w d0,d0
    add.w d0,d0
    lea.l dat_AE66(pc),a2
    move.l $0(a2,d0.w),$0010(a0)
h0_ADC2:
    clr.l $0008(a0)
    movea.l a0,a1
h0_ADC8:
    move.l a1,$01DE(a6)
    rts
h0_ADCE:
    bsr.s h0_ADE8
h0_ADD0:
    bne.s h0_AE28
h0_ADD2:
    move.l $000C(a1),$027E(a6)
    bne.s h0_ADE2
h0_ADDA:
    lea.l $05DE(a6),a0
    move.l a0,$027E(a6)
h0_ADE2:
    move.l a1,$01DE(a6)
    rts
h0_ADE8:
    lea.l $01DA(a6),a0
    move.b $000E(a1),d0
h0_ADF0:
    tst.l (a0)
    beq.s h0_AE00
h0_ADF4:
    addq.b #1,d0
    beq.s h0_ADFC
h0_ADF8:
    movea.l (a0),a0
    bra.s h0_ADF0
h0_ADFC:
    movea.l (a0),a1
    rts
h0_AE00:
    moveq.l #-1,d0
    rts
h0_AE04:
    bsr.s h0_ADE8
h0_AE06:
    bne.s h0_AE28
h0_AE08:
    tst.b $026A(a6)
    bne.s h0_AE22
h0_AE0E:
    move.l $026E(a6),d2
    sub.l $001C(a1),d2
    add.l d2,$0014(a1)
    move.l $026E(a6),$001C(a1)
    rts
h0_AE22:
    move.l a5,$000C(a1)
    rts
h0_AE28:
    moveq.l #77,d0
    bra.w h0_853E
dat_AE2E:
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
dat_AE66:
    DC.B    $00,$00
    DC.L    $03eb0000,$03e90000,$03ea4000,$03eb8000,$03eb4000,$03e98000,$03e94000,$03ea8000
    DC.B    $03,$ea
h0_AE8A:
    tst.l $01C8(a6)
    bne.w h0_97E4
h0_AE92:
    move.l a4,-(a7)
    lea.l $01DA(a6),a3
h0_AE98:
    tst.l (a3)
    beq.s h0_AED4
h0_AE9C:
    movea.l (a3),a3
    move.l $0014(a3),d1
    beq.s h0_AED8
h0_AEA4:
    move.l d1,d0
    andi.b #3,d0
    beq.s h0_AEB2
h0_AEAC:
    andi.b #252,d1
    addq.l #4,d1
h0_AEB2:
    move.l d1,$0014(a3)
    cmpi.w #1003,$0012(a3)
    beq.s h0_AED8
h0_AEBE:
    addq.l #8,d1
    bsr.w h0_9146
h0_AEC4:
    move.l a0,$0008(a3)
    move.l a0,$000C(a3)
    adda.l $0014(a3),a0
    clr.l -(a0)
    bra.s h0_AE98
h0_AED4:
    movea.l (a7)+,a4
    rts
h0_AED8:
    clr.l $000C(a3)
    bra.s h0_AE98
h0_AEDE:
    move.b d0,d1
    not.b d1
    bsr.w h0_8F3C
h0_AEE6:
    moveq.l #46,d1
    bra.w h0_931A
h0_AEEC:
    movea.l $01DE(a6),a1
    cmpi.w #1003,$0012(a1)
    rts
h0_AEF8:
    movem.l d6/a0-a2,-(a7)
    movea.l $0004(a0),a0
    move.b $000E(a0),d6
    lea.l dat_AF1A(pc),a2
    movea.l $0144(a6),a1
    moveq.l #0,d0
    bsr.w h0_8DA2
h0_AF12:
    movem.l (a7)+,d6/a0-a2
    tst.l d0
    rts
dat_AF1A:
    DC.L    $52804e75 ; VIOLATION: orphaned code island at $AF1A is not reached from known entrypoints
h0_AF1E:
    bsr.w h0_99D0
h0_AF22:
    cmpi.w #3,$0250(a6)
    bne.s h0_AFA4
h0_AF2A:
    bsr.w h0_B260
h0_AF2E:
    move.l #$3F3,d1
    bsr.w h0_B23E
h0_AF38:
    moveq.l #0,d1
    bsr.w h0_B23E
h0_AF3E:
    moveq.l #0,d1
    lea.l $01DA(a6),a0
h0_AF44:
    movea.l (a0),a0
    tst.l $0014(a0)
    bne.s h0_AF50
h0_AF4C:
    bsr.s h0_AEF8
h0_AF4E:
    beq.s h0_AF52
h0_AF50:
    addq.l #1,d1
h0_AF52:
    tst.l (a0)
    bne.s h0_AF44
h0_AF56:
    bsr.w h0_B23E
h0_AF5A:
    move.l d1,d2
    moveq.l #0,d1
    bsr.w h0_B23E
h0_AF62:
    move.l d2,d1
    subq.l #1,d1
    bsr.w h0_B23E
h0_AF6A:
    lea.l $01DA(a6),a3
h0_AF6E:
    movea.l (a3),a3
    move.l $0014(a3),d1
    bne.s h0_AF7E
h0_AF76:
    movea.l a3,a0
    bsr.w h0_AEF8
h0_AF7C:
    beq.s h0_AF8C
h0_AF7E:
    lsr.l #2,d1
    swap.w d1
    or.w $0010(a3),d1
    swap.w d1
    bsr.w h0_B23E
h0_AF8C:
    tst.l (a3)
    bne.s h0_AF6E
h0_AF90:
    bsr.w h0_B246
h0_AF94:
    tst.b $012B(a6)
    beq.s h0_AF9E
h0_AF9A:
    bsr.w h0_B526
h0_AF9E:
    lea.l $01DA(a6),a3
    bra.s h0_AFD4
h0_AFA4:
    move.l #$3E7,d1
    lea.l $01E2(a6),a1
    tst.b (a1)
    beq.s h0_AFC0
h0_AFB2:
    move.l a1,d0
h0_AFB4:
    tst.b (a1)+
    bne.s h0_AFB4
h0_AFB8:
    subq.l #1,a1
    exg d0,a1
    sub.l a1,d0
    bra.s h0_AFCC
h0_AFC0:
    movea.l $0144(a6),a1
    lea.l $0016(a1),a1
    move.b (a1)+,d0
    subq.b #1,d0
h0_AFCC:
    bsr.w h0_B320
h0_AFD0:
    lea.l $01DA(a6),a3
h0_AFD4:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_AFE6
h0_AFDC:
    movea.l a3,a0
    bsr.w h0_AEF8
h0_AFE2:
    beq.w h0_B152
h0_AFE6:
    cmpi.w #3,$0250(a6)
    beq.s h0_B004
h0_AFEE:
    move.l #$3E8,d1
    movea.l $0004(a3),a1
    lea.l $0016(a1),a1
    move.b (a1)+,d0
    subq.b #1,d0
    bsr.w h0_B320
h0_B004:
    lea.l $0014(a3),a0
    move.l (a0),d0
    lsr.l #2,d0
    move.l d0,(a0)
    subq.l #4,a0
    moveq.l #8,d1
    bsr.w h0_84F2
h0_B016:
    cmpi.w #1003,$0012(a3)
    beq.s h0_B02E
h0_B01E:
    movea.l $0008(a3),a0
    move.l $0014(a3),d1
    add.l d1,d1
    add.l d1,d1
    bsr.w h0_84F2
h0_B02E:
    bsr.w h0_B260
h0_B032:
    tst.l $0018(a3)
    beq.w h0_B0DC
h0_B03A:
    moveq.l #1,d6
    move.l #$3EC,d1
    bsr.s h0_B064
h0_B044:
    cmpi.w #3,$0250(a6)
    beq.w h0_B0DC
h0_B04E:
    move.l #$3F8,d1
    moveq.l #40,d6
    bsr.s h0_B064
h0_B058:
    move.l #$3F9,d1
    moveq.l #41,d6
    bsr.s h0_B064
h0_B062:
    bra.s h0_B0DC
h0_B064:
    moveq.l #0,d3
    move.l d1,-(a7)
    pea.l $01DA(a6)
    clr.l -(a7)
h0_B06E:
    movea.l $0004(a7),a0
h0_B072:
    tst.l (a0)
    beq.s h0_B0CA
h0_B076:
    movea.l (a0),a0
    subq.l #1,d3
    tst.l $0014(a0)
    bne.s h0_B086
h0_B080:
    bsr.w h0_AEF8
h0_B084:
    beq.s h0_B072
h0_B086:
    move.l a0,$0004(a7)
    bsr.w h0_B2B4
h0_B08E:
    beq.s h0_B0BE
h0_B090:
    move.l $0008(a7),d0
    beq.s h0_B0A4
h0_B096:
    move.l d1,-(a7)
    move.l d0,d1
    bsr.w h0_B23E
h0_B09E:
    move.l (a7)+,d1
    clr.l $0008(a7)
h0_B0A4:
    bsr.w h0_B23E
h0_B0A8:
    move.l (a7),d1
    bsr.w h0_B23E
h0_B0AE:
    bsr.w h0_B2E2
h0_B0B2:
    bne.s h0_B0BE
h0_B0B4:
    move.l $0004(a0),d1
    bsr.w h0_B23E
h0_B0BC:
    bra.s h0_B0AE
h0_B0BE:
    addq.l #1,(a7)
    movea.l $0144(a6),a0
    cmp.b $000C(a0),d3
    bne.s h0_B06E
h0_B0CA:
    tst.l $0008(a7)
    lea.l $000C(a7),a7
    bne.s h0_B0DA
h0_B0D4:
    moveq.l #0,d1
    bra.w h0_B23E
h0_B0DA:
    rts
h0_B0DC:
    cmpi.w #3,$0250(a6)
    beq.s h0_B116
h0_B0E4:
    move.l #$3EF,d1
    bsr.w h0_B23E
h0_B0EE:
    movea.l $0004(a3),a0
    move.b $000E(a0),d3
    movea.l $0144(a6),a1
    lea.l h0_B26A(pc),a2
    bsr.w h0_8DCE
h0_B102:
    move.b d3,d6
    lea.l dat_B184(pc),a2
    movea.l $0144(a6),a1
    bsr.w h0_8DA2
h0_B110:
    moveq.l #0,d1
    bsr.w h0_B23E
h0_B116:
    tst.b $0105(a6)
    beq.s h0_B140
h0_B11C:
    movea.l $0004(a3),a0
    move.b $000E(a0),d6
    move.l #$3F0,d1
    bsr.w h0_B23E
h0_B12E:
    movea.l $0144(a6),a1
    lea.l h0_B19C(pc),a2
    bsr.w h0_8D7C
h0_B13A:
    moveq.l #0,d1
    bsr.w h0_B23E
h0_B140:
    tst.b $012B(a6)
    beq.w h0_B150
h0_B148:
    lea.l dat_8BFE(pc),a2
    bsr.w h0_8D20
h0_B150:
    bsr.s h0_B174
h0_B152:
    tst.l (a3)
    bne.w h0_AFD4
h0_B158:
    lea.l $01DA(a6),a3
h0_B15C:
    movea.l (a3),a3
    tst.l $0014(a3)
    bne.s h0_B182
h0_B164:
    movea.l a3,a0
    bsr.w h0_AEF8
h0_B16A:
    bne.s h0_B182
h0_B16C:
    tst.l (a3)
    bne.s h0_B15C
h0_B170:
    bsr.w h0_B260
h0_B174:
    move.l #$3F2,d1
    bsr.w h0_B23E
h0_B17E:
    bra.w h0_B246
h0_B182:
    rts
dat_B184:
    DC.B    $70,$01,$0c,$29,$00,$01,$00,$0d,$67,$02,$70,$02 ; VIOLATION: orphaned code island at $B184 is not reached from known entrypoints
h0_B190:
    bsr.s h0_B1E8
h0_B192:
    move.l $0008(a1),d1
    bra.w h0_B23E
h0_B19A:
    rts
h0_B19C:
    cmp.b $000E(a1),d6
    bne.s h0_B19A
h0_B1A2:
    cmpi.b #1,$000D(a1)
    bne.s h0_B19A
h0_B1AA:
    btst.b #4,$000C(a1)
    bne.s h0_B19A
h0_B1B2:
    cmpi.w #3,$0250(a6)
    beq.s h0_B1CC
h0_B1BA:
    tst.b $0105(a6)
    bpl.s h0_B1C8
h0_B1C0:
    btst.b #5,$000C(a1)
    beq.s h0_B19A
h0_B1C8:
    moveq.l #0,d0
    bra.s h0_B190
h0_B1CC:
    move.w $0012(a3),d0
    cmp.w #$3EA,d0
    beq.s h0_B1E2
h0_B1D6:
    cmp.w #$3E9,d0
    bne.s h0_B1C8
h0_B1DC:
    addq.l #1,$0248(a6)
    bra.s h0_B1C8
h0_B1E2:
    addq.l #1,$0244(a6)
    bra.s h0_B1C8
h0_B1E8:
    moveq.l #0,d1
    move.b $0016(a1),d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_B1FC
h0_B1F6:
    andi.b #252,d1
    addq.l #4,d1
h0_B1FC:
    lsr.l #2,d1
    ror.l #8,d0
    or.l d0,d1
    bsr.s h0_B23E
h0_B204:
    moveq.l #4,d0
    add.b $0016(a1),d0
    cmp.w d0,d4
    bcc.s h0_B210
h0_B20E:
    bsr.s h0_B246
h0_B210:
    lea.l $0016(a1),a0
    move.b (a0)+,d0
h0_B216:
    move.b (a0)+,(a4)+
    subq.w #1,d4
    subq.b #1,d0
    bne.s h0_B216
h0_B21E:
    move.b $0016(a1),d0
    andi.b #3,d0
    beq.s h0_B234
h0_B228:
    clr.b (a4)+
    addq.b #1,d0
    subq.w #1,d4
    cmp.b #$4,d0
    bne.s h0_B228
h0_B234:
    rts
h0_B236:
    addq.w #4,d4
    move.l d1,-(a7)
    bsr.s h0_B246
h0_B23C:
    move.l (a7)+,d1
h0_B23E:
    subq.w #4,d4
    bcs.s h0_B236
h0_B242:
    move.l d1,(a4)+
    rts
h0_B246:
    move.l #$80,d1
    sub.w d4,d1
    beq.s h0_B260
h0_B250:
    movem.l d0/d2/a0-a2,-(a7)
    lea.l $05DE(a6),a0
    bsr.w h0_84F2
h0_B25C:
    movem.l (a7)+,d0/d2/a0-a2
h0_B260:
    lea.l $05DE(a6),a4
    move.w #$80,d4
    rts
h0_B26A:
    movem.l a1-a2,-(a7)
    moveq.l #2,d6
    move.w $0014(a1),d2
    bsr.s h0_B28C
h0_B276:
    moveq.l #4,d6
    bsr.s h0_B28C
h0_B27A:
    moveq.l #5,d6
    bsr.s h0_B28C
h0_B27E:
    moveq.l #7,d6
    bsr.s h0_B28C
h0_B282:
    moveq.l #8,d6
    bsr.s h0_B28C
h0_B286:
    movem.l (a7)+,a1-a2
    rts
h0_B28C:
    bsr.w h0_B2B4
h0_B290:
    beq.s h0_B2B2
h0_B292:
    movem.l d1-d2,-(a7)
    moveq.l #127,d0
    add.b d6,d0
    bsr.w h0_B1E8
h0_B29E:
    movem.l (a7)+,d1-d2
    bsr.s h0_B23E
h0_B2A4:
    bsr.w h0_B2E2
h0_B2A8:
    bne.s h0_B2B2
h0_B2AA:
    move.l $0004(a0),d1
    bsr.s h0_B23E
h0_B2B0:
    bra.s h0_B2A4
h0_B2B2:
    rts
h0_B2B4:
    moveq.l #0,d1
    tst.l $0018(a3)
    beq.s h0_B2CC
h0_B2BC:
    bsr.s h0_B2CE
h0_B2BE:
    beq.s h0_B2CC
h0_B2C0:
    bsr.s h0_B2E2
h0_B2C2:
    bne.s h0_B2C8
h0_B2C4:
    addq.l #1,d1
    bra.s h0_B2C0
h0_B2C8:
    bsr.s h0_B2CE
h0_B2CA:
    tst.l d1
h0_B2CC:
    rts
h0_B2CE:
    movea.l $0018(a3),a5
h0_B2D2:
    moveq.l #10,d5
    lea.l $000A(a5),a0
    move.l a0,$0006(a5)
    sub.w $0004(a5),d5
    rts
h0_B2E2:
    subq.w #1,d5
    bcs.s h0_B312
h0_B2E6:
    movea.l $0006(a5),a0
    addq.l #8,$0006(a5)
    cmp.b (a0),d6
    bne.s h0_B2E2
h0_B2F2:
    cmp.b $0001(a0),d3
    bne.s h0_B2E2
h0_B2F8:
    cmp.b #$1,d6
    beq.s h0_B310
h0_B2FE:
    cmp.b #$28,d6
    beq.s h0_B310
h0_B304:
    cmp.b #$29,d6
    beq.s h0_B310
h0_B30A:
    cmp.w $0002(a0),d2
    bne.s h0_B2E2
h0_B310:
    rts
h0_B312:
    tst.l (a5)
    beq.s h0_B31C
h0_B316:
    movea.l (a5),a5
    bsr.s h0_B2D2
h0_B31A:
    bne.s h0_B2E2
h0_B31C:
    moveq.l #-1,d0
    rts
h0_B320:
    lea.l $05DE(a6),a0
    move.l d1,(a0)+
    moveq.l #0,d1
    move.b d0,d1
    move.l d1,d2
    andi.b #3,d2
    beq.s h0_B338
h0_B332:
    andi.b #252,d1
    addq.l #4,d1
h0_B338:
    lsr.l #2,d1
    move.l d1,(a0)+
    beq.s h0_B34A
h0_B33E:
    move.b (a1)+,(a0)+
    subq.b #1,d0
    bne.s h0_B33E
h0_B344:
    clr.b (a0)+
    clr.b (a0)+
    clr.b (a0)+
h0_B34A:
    add.l d1,d1
    add.l d1,d1
    addq.l #8,d1
    lea.l $05DE(a6),a0
    bra.w h0_84F2
h0_B358:
    movea.l $01DE(a6),a0
    lea.l $0018(a0),a0
    tst.l (a0)
    beq.s h0_B370
h0_B364:
    movea.l (a0),a0
    tst.w $0004(a0)
    bne.s h0_B390
h0_B36C:
    tst.l (a0)
    bne.s h0_B364
h0_B370:
    movem.l d0-d2/a0/a2,-(a7)
    moveq.l #90,d1
    bsr.w h0_9146
h0_B37A:
    movem.l (a7)+,d0-d2/a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.w #$A,$0004(a0)
    lea.l $000A(a0),a1
    move.l a1,$0006(a0)
h0_B390:
    subq.w #1,$0004(a0)
    movea.l $0006(a0),a1
    addq.l #8,$0006(a0)
    movea.l a1,a0
    rts
h0_B3A0:
    movea.l $47FA(a6),a0
    move.w (a0)+,d0
    cmp.w #$2B2B,d0
    bne.s h0_B3D8
h0_B3AC:
    move.w (a0)+,d0
    bpl.s h0_B3D0
h0_B3B0:
    andi.w #255,d0
    cmpi.w #11565,(a0)
    bne.s h0_B3D0
h0_B3BA:
    tst.b $0002(a0)
    bpl.s h0_B3D0
h0_B3C0:
    cmp.b $0003(a0),d0
    bne.s h0_B3D0
h0_B3C6:
    tst.w $0004(a0)
    bne.s h0_B3D8
h0_B3CC:
    addq.l #4,a7
    rts
h0_B3D0:
    tst.w (a0)
    bne.s h0_B3D8
h0_B3D4:
    tst.w -(a0)
    rts
h0_B3D8:
    moveq.l #68,d0
    bra.w h0_8556
h0_B3DE:
    add.l $026E(a6),d2
    add.l a5,d2
    sub.l $027E(a6),d2
h0_B3E8:
    tst.b $0104(a6)
    beq.s h0_B3F8
h0_B3EE:
    bsr.w h0_B358
h0_B3F2:
    move.w d0,(a0)
    move.l d2,$0004(a0)
h0_B3F8:
    rts
h0_B3FA:
    move.l d0,d2
    move.w #$100,d0
    or.b $014C(a6),d0
    bra.s h0_B3E8
h0_B406:
    move.l d2,(a5)+
    bsr.s h0_B3A0
h0_B40A:
    bpl.s h0_B414
h0_B40C:
    ori.w #256,d0
    moveq.l #-4,d2
    bra.s h0_B3DE
h0_B414:
    bsr.w h0_B472
    DC.B    $02,$fc ; VIOLATION: decode failed in reachable code; region emitted as data
h0_B41A:
    move.w d2,(a5)+
    bsr.s h0_B3A0
h0_B41E:
    bmi.s h0_B3D8
h0_B420:
    bsr.w h0_B472
    DC.B    $04,$fe ; VIOLATION: decode failed in reachable code; region emitted as data
h0_B426:
    cmp.b #$1,d3
    bne.s h0_B41A
h0_B42C:
    move.w d2,(a5)+
    bsr.w h0_B3A0
h0_B432:
    bmi.s h0_B438
h0_B434:
    bsr.s h0_B472
    DC.B    $07,$fe ; VIOLATION: decode failed in reachable code; region emitted as data
h0_B438:
    ori.w #10240,d0
    moveq.l #-2,d2
    bra.s h0_B3DE
h0_B440:
    cmp.b #$1,d3
    bne.s h0_B464
h0_B446:
    move.b d2,(a5)+
    bsr.w h0_B3A0
h0_B44C:
    bmi.w h0_B454
h0_B450:
    bsr.s h0_B472
    DC.B    $08,$ff ; VIOLATION: decode failed in reachable code; region emitted as data
h0_B454:
    ori.w #10496,d0
    moveq.l #-1,d2
    bra.s h0_B3DE
h0_B45C:
    sub.l $027E(a6),d2
    add.l a5,d2
    subq.l #2,d2
h0_B464:
    move.b d2,(a5)+
    bsr.w h0_B3A0
h0_B46A:
    bmi.w h0_B3D8
h0_B46E:
    bsr.s h0_B472
    DC.B    $05,$ff ; VIOLATION: decode failed in reachable code; region emitted as data
h0_B472:
    tst.b $0104(a6)
    beq.s h0_B498
h0_B478:
    bsr.w h0_B358
h0_B47C:
    movea.l (a7),a1
    move.b (a1)+,(a0)+
    move.b $014C(a6),(a0)+
    move.w d0,(a0)+
    move.b (a1)+,d2
    ext.w d2
    ext.l d2
    add.l $026E(a6),d2
    add.l a5,d2
    sub.l $027E(a6),d2
    move.l d2,(a0)+
h0_B498:
    addq.l #4,a7
    rts
h0_B49C:
    lea.l dat_B4D4(pc),a0
    cmpi.w #3,$0250(a6)
    beq.s h0_B4AC
h0_B4A8:
    lea.l dat_B4C0(pc),a0
h0_B4AC:
    rts
h0_B4AE:
    lea.l dat_B4D4(pc),a0
    cmpi.w #3,$0250(a6)
    beq.s h0_B4AC
h0_B4BA:
    lea.l dat_B4D1(pc),a0
    rts
dat_B4C0:
    DC.B    "Lattice linkable",0
dat_B4D1:
    DC.B    $2e,$6f,$00
dat_B4D4:
    DC.L    $00002f08,$12d866fc,$137c002c,$ffff205f,$12d866fc,$53894e75,$4a2e0105,$673247ee
    DC.L    $01da2653,$4aab0014,$6608204b,$6100f9f6,$671a302b,$0012b07c,$03ea670c,$b07c03e9
    DC.L    $660a52ae,$02386004,$52ae023c,$4a9366d2
    DC.B    $4e,$75
h0_B526:
    bsr.w h0_C012
h0_B52A:
    move.l d0,$0240(a6)
    moveq.l #11,d1
    add.l $0238(a6),d1
    add.l $023C(a6),d1
    add.l $0234(a6),d1
    lsl.l #2,d1
    movea.l a6,a0
    bsr.w h0_84F2
h0_B544:
    bra.w h0_B260
    DC.L    $242e0240,$61000ab0,$6100fd0e,$223c0000,$03f16100,$fce27209,$d2ae0238,$d2ae023c
    DC.L    $d2ae0234,$6100fcd0,$72006100,$fcca223c ; VIOLATION: orphaned code island at $B548 is not reached from known entrypoints
    DC.B    "HEADa",0
    DC.B    $fc,$c0
    DC.B    $22,"<DBGVa",0
    DC.L    $fcb6223c,$30310000,$6100fcac,$222e0244,$6100fca4,$222e0248,$6100fc9c,$222e0234
    DC.L    $6100fc94,$45fa006c,$6100d532,$222e023c,$6100fc84,$263c0000,$03ea6100,$0018222e
    DC.L    $02386100,$fc72263c,$000003e9,$61000006,$6000fc6c
    DC.L    $4a2e0105,$67367400,$47ee01da,$26534aab,$00146608,$204b6100,$f904671a,$302b0012
    DC.L    $b6406612,$72001202,$e019d2ab,$00201f02,$6100fc30,$141f5202,$4a9366d0 ; VIOLATION: orphaned code island at $B5DC is not reached from known entrypoints
    DC.B    $4e,$75
    DC.B    $74,$00 ; VIOLATION: orphaned code island at $B61A is not reached from known entrypoints
    DC.L    $47ee01da,$26534aab,$00146608,$204b6100,$f8cc6712,$45fa0016,$206b0004,$1c28000e
    DC.L    $6100d6e2,$52024a93,$66da4e75
    DC.L    $72001202,$e019d2a8,$001c2f08,$6100fbe8 ; VIOLATION: orphaned code island at $B648 is not reached from known entrypoints
    DC.B    " _Nu"
dat_B65C:
    DC.L    $809a9083,$8eb68f80,$88898a8b,$8c8d8e8f,$90929293,$99959697,$98999a9b,$9c9d9e9f
    DC.L    $a0a1a2a3,$a5a5a6a7,$a8a9aaab,$acadaeaf,$b7b8b2b2,$b4b4b6b7,$b8b9babb,$bcbdbebf
    DC.L    $c1c1c2c3,$c4c5c6c7,$c8c9cacb,$cccdcecf,$d0d1d2d3,$d4d5d6d7,$d8d9dadb,$dcdddedf
    DC.L    $e0e1e2e3,$e4e5e6e7,$e8e9eaeb,$ecedeeef,$f0f1f2f3,$f4f5f6f7,$f8f9fafb,$fcfdfeff
    DC.L    $00010203,$04050607,$08090a0b,$0c0d0e0f,$10111213,$14151617,$18191a1b,$1c1d1e1f
    DC.B    " !",$22,"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[",$5c,"]^_`ABCDEFGHIJKLMNOPQRSTUVWXYZ{|}~"
    DC.B    $7f
dat_B75C:
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$0101ff01,$00000000,$00000000,$00000101,$01010100
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010100
    DC.L    $01000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010101
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000001,$01010001
    DC.L    $00000000,$00000000,$01010101,$01000101,$00000000,$00000000,$00010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
    DC.L    $01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101,$01010101
h0_B85C:
    move.w d1,-(a7)
    moveq.l #27,d1
    bsr.s h0_B870
h0_B862:
    moveq.l #112,d1
    bsr.s h0_B870
h0_B866:
    move.w (a7)+,d1
    bsr.s h0_B870
h0_B86A:
    moveq.l #27,d1
    bsr.s h0_B870
h0_B86E:
    moveq.l #113,d1
h0_B870:
    andi.w #255,d1
    move.l $01D0(a6),d0
    beq.s h0_B884
h0_B87A:
    movea.l d0,a0
    move.b d1,d0
    movea.l $001C(a0),a0
    jmp (a0)                            ; CANDIDATE: indirect_jump index unresolved
h0_B884:
    move.w d1,-(a7)
    move.w #c_conout,-(a7)
    trap #1
    addq.l #4,a7
    rts
h0_B890:
    move.l d1,-(a7)
    move.l a0,-(a7)
    move.l d1,-(a7)
    move.w d3,-(a7)
    move.w #f_write,-(a7)
    trap #1
    lea.l $000C(a7),a7
    move.l (a7)+,d1
    cmp.l d0,d1
    rts
h0_B8A8:
    tst.w d3
    bmi.s h0_B8B2
h0_B8AC:
    cmp.w #$5,d3
    bcc.s h0_B8BC
h0_B8B2:
    move.w d3,-(a7)
    move.w #f_close,-(a7)
    trap #1
    addq.l #4,a7
h0_B8BC:
    rts
h0_B8BE:
    movea.l (a7)+,a3
    movea.l $0004(a7),a5
    move.l $0004(a5),d0
    sub.l (a5),d0
    bcs.s h0_B918
h0_B8CC:
    cmp.l #$6178,d0
    bcs.s h0_B918
h0_B8D4:
    movea.l $0018(a5),a6
    addq.w #2,a6
    move.l a5,$4EF2(a6)
    lea.l $46F0(a6),a7
    lea.l $0(a5,d0.l),a0
    move.l a0,$4FB0(a6)
    lea.l $50DA(a6),a0
    move.l a0,$4FAC(a6)
    clr.l $4FA8(a6)
    move.l d0,-(a7)
    move.l a5,-(a7)
    clr.w -(a7)
    move.w #m_shrink,-(a7)
    trap #1
    lea.l $000C(a7),a7
    tst.l d0
    bne.s h0_B918
h0_B90A:
    sf.b $4EF1(a6)
    sf.b $4EF0(a6)
    clr.b $4FA6(a6)
    jmp (a3)                            ; CANDIDATE: indirect_jump index unresolved
h0_B918:
    move.w #$FFD9,-(a7)
    move.w #p_term,-(a7)
    trap #1
    pea.l $0000.w
    move.w #super,-(a7)
    trap #1
    addq.l #6,a7
    movea.l $05A0.w,a4
    move.l d0,-(a7)
    move.w #super,-(a7)
    trap #1
    addq.l #6,a7
    move.l a4,d0
    beq.s h0_B952
h0_B940:
    move.l (a4)+,d0
    beq.s h0_B952
h0_B944:
    cmp.l d0,d3
    beq.s h0_B94C
h0_B948:
    addq.l #4,a4
    bra.s h0_B940
h0_B94C:
    move.l (a4)+,d0
    cmp.b d0,d0
    rts
h0_B952:
    moveq.l #-1,d0
    rts
h0_B956:
    movea.l a5,a2
    lea.l dat_BAD6(pc),a1
    bsr.w h0_BB72
h0_B960:
    bne.s h0_B982
h0_B962:
    bsr.w h0_BA94
h0_B966:
    beq.s h0_B982
h0_B968:
    move.l d1,$01D0(a6)
    movea.l d1,a0
    move.l $0028(a0),$01C8(a6)
    move.l $002C(a0),$01CC(a6)
    move.l $003C(a0),$01D4(a6)
    bra.s h0_B99A
h0_B982:
    moveq.l #0,d0
    move.l d0,$01C8(a6)
    move.l d0,$01CC(a6)
    move.l d0,$01D0(a6)
    lea.l $01D8(a6),a0
    move.b d0,(a0)
    move.l a0,$01D4(a6)
h0_B99A:
    clr.b $0750(a6)
    sf.b $024F(a6)
    st.b $0104(a6)
    sf.b $00FE(a6)
    sf.b $0100(a6)
    sf.b $0101(a6)
    sf.b $00FF(a6)
    clr.w $0250(a6)
    move.l $4FB0(a6),d0
    sub.l $4FAC(a6),d0
    move.l d0,$4EF6(a6)
    bsr.w h0_BCA4
h0_B9CA:
    move.l d0,$4FA2(a6)
    tst.l $01C8(a6)
    bne.w h0_B9D6
h0_B9D6:
    movea.l a5,a2
    cmpi.b #127,$0080(a5)
    beq.s h0_B9F4
h0_B9E0:
    lea.l dat_BAE8(pc),a1
    bsr.w h0_BB72
h0_B9E8:
    bne.s h0_BA0A
h0_B9EA:
    bsr.w h0_BA94
h0_B9EE:
    cmp.l $0024(a5),d1
    bne.s h0_BA0A
h0_B9F4:
    lea.l dat_BAE2(pc),a1
    bsr.w h0_BB72
h0_B9FC:
    bne.s h0_BA0A
h0_B9FE:
    tst.b (a0)+
    bne.s h0_B9FE
h0_BA02:
    tst.b (a0)+
    bne.s h0_BA02
h0_BA06:
    bra.w h0_BA1C
h0_BA0A:
    movea.l a5,a0
    lea.l $0080(a0),a0
    moveq.l #0,d0
    move.b (a0)+,d0
    clr.b $0(a0,d0.w)
    clr.b $1(a0,d0.w)
h0_BA1C:
    tst.b (a0)
    bne.s h0_BA74
h0_BA20:
    st.b $4EF1(a6)
    pea.l dat_BCDD(pc)
    move.w #c_conws,-(a7)
    trap #1
    addq.l #6,a7
    movea.l a5,a0
    lea.l $0081(a0),a0
    move.b #$4C,-(a0)
    move.l a0,-(a7)
    move.w #c_conrs,-(a7)
    trap #1
    addq.l #6,a7
    pea.l dat_BCF0(pc)
    move.w #c_conws,-(a7)
    trap #1
    addq.l #6,a7
    movea.l a5,a0
    lea.l $0081(a0),a0
    moveq.l #0,d0
    move.b (a0)+,d0
    bne.s h0_BA64
h0_BA5C:
    sf.b $4EF1(a6)
    moveq.l #-1,d0
    rts
h0_BA64:
    movem.l d0/a0,-(a7)
    bsr.w h0_BCA4
h0_BA6C:
    move.l d0,$4FA2(a6)
    movem.l (a7)+,d0/a0
h0_BA74:
    move.l a0,$025A(a6)
    clr.l $025E(a6)
    clr.l $0262(a6)
    movea.l a5,a2
    lea.l dat_BAEE(pc),a1
    bsr.w h0_BB72
h0_BA8A:
    bne.s h0_BA90
h0_BA8C:
    move.l a0,$025E(a6)
h0_BA90:
    moveq.l #0,d0
    rts
h0_BA94:
    moveq.l #0,d0
    moveq.l #0,d1
h0_BA98:
    move.b (a0)+,d0
    cmp.b #$3A,d0
    bcc.s h0_BAAC
h0_BAA0:
    cmp.b #$30,d0
    bcs.s h0_BAD4
h0_BAA6:
    subi.w #48,d0
    bra.s h0_BACE
h0_BAAC:
    cmp.b #$47,d0
    bcc.s h0_BABE
h0_BAB2:
    cmp.b #$41,d0
    bcs.s h0_BAD4
h0_BAB8:
    subi.w #55,d0
    bra.s h0_BACE
h0_BABE:
    cmp.b #$67,d0
    bcc.s h0_BAD4
h0_BAC4:
    cmp.b #$61,d0
    bcs.s h0_BAD4
h0_BACA:
    subi.w #87,d0
h0_BACE:
    lsl.l #4,d1
    add.l d0,d1
    bra.s h0_BA98
h0_BAD4:
    rts
dat_BAD6:
    DC.B    $5f,$5f,$48,$49,$53,$4f,$46,$54,$5f,$5f,$3d,$00
dat_BAE2:
    DC.B    $41,$52,$47,$56,$3d,$00
dat_BAE8:
    DC.B    $5f,$50,$42,$50,$3d,$00
dat_BAEE:
    DC.B    $47,$45,$4e,$5f,$4f,$50,$54,$3d,$00,$00
h0_BAF8:
    bsr.w h0_BF0C
h0_BAFC:
    tst.l d4
    beq.s h0_BB20
h0_BB00:
    move.l d1,d5
    addq.l #1,d1
    bsr.w h0_9146
h0_BB08:
    move.l d5,d1
    move.l d4,d3
    move.l a0,-(a7)
    bsr.w h0_BFB2
h0_BB12:
    move.l d4,d3
    bsr.w h0_BFAE
h0_BB18:
    movea.l (a7)+,a0
    clr.b $0(a0,d5.l)
    tst.l d5
h0_BB20:
    rts
h0_BB22:
    move.l $0262(a6),d0
    beq.s h0_BB62
h0_BB28:
    st.b $4EF0(a6)
    movea.l d0,a4
h0_BB2E:
    jsr h0_3B4A.l
h0_BB34:
    bne.w h0_BB4A
h0_BB38:
    tst.b d1
h0_BB3A:
    beq.s h0_BB4A
h0_BB3C:
    move.b (a4),d1
    beq.s h0_BB62
h0_BB40:
    cmp.b #$A,d1
    bne.s h0_BB2E
h0_BB46:
    move.b (a4)+,d1
    bra.s h0_BB3A
h0_BB4A:
    sf.b $4EF0(a6)
    rts
h0_BB50:
    movea.l $025A(a6),a4
h0_BB54:
    jsr h0_3B4A.l
h0_BB5A:
    bne.w h0_BB62
h0_BB5E:
    move.b (a4),d1
    bne.s h0_BB54
h0_BB62:
    rts
h0_BB64:
    move.l $025E(a6),d0
    beq.s h0_BB62
h0_BB6A:
    movea.l d0,a4
    jmp h0_3B4A.l
h0_BB72:
    movea.l $002C(a2),a0
    tst.b (a0)
    bne.s h0_BB82
h0_BB7A:
    tst.b $0001(a0)
    beq.s h0_BBA6
h0_BB80:
    addq.l #1,a0
h0_BB82:
    tst.b (a0)
    beq.s h0_BBA6
h0_BB86:
    movem.l a0-a1,-(a7)
h0_BB8A:
    move.b (a1)+,d0
    beq.s h0_BB94
h0_BB8E:
    cmp.b (a0)+,d0
    beq.s h0_BB8A
h0_BB92:
    bra.s h0_BB9C
h0_BB94:
    movem.l (a7)+,d0/a1
    moveq.l #0,d0
    rts
h0_BB9C:
    movem.l (a7)+,a0-a1
h0_BBA0:
    tst.b (a0)+
    bne.s h0_BBA0
h0_BBA4:
    bra.s h0_BB82
h0_BBA6:
    moveq.l #-1,d0
    rts
h0_BBAA:
    lea.l dat_BBD2(pc),a1
    movea.l $4EF2(a6),a2
    bsr.s h0_BB72
h0_BBB4:
    beq.s h0_BBC2
h0_BBB6:
    lea.l dat_BBDA(pc),a1
    movea.l $4EF2(a6),a2
    bsr.s h0_BB72
h0_BBC0:
    bne.s h0_BBD0
h0_BBC2:
    movea.l a0,a4
    lea.l $0868(a6),a3
    st.b $012D(a6)
    bra.w h0_4778
h0_BBD0:
    rts
dat_BBD2:
    DC.B    $49,$4e,$43,$44,$49,$52,$3d,$00
dat_BBDA:
    DC.B    $49,$4e,$43,$4c,$55,$44,$45,$3d,$00,$00
h0_BBE4:
    clr.w -(a7)
    move.l a0,-(a7)
    move.w #f_create,-(a7)
    trap #1
    addq.l #8,a7
    tst.l d0
    bmi.w h0_BBFC
h0_BBF6:
    move.l d0,$4810(a6)
    moveq.l #0,d0
h0_BBFC:
    rts
h0_BBFE:
    tst.b $480F(a6)
    beq.s h0_BC2E
h0_BC04:
    tst.w $4A22(a6)
    bmi.s h0_BC2E
h0_BC0A:
    btst.b #0,$4ADE(a6)
    beq.s h0_BC2E
h0_BC12:
    moveq.l #13,d1
    bsr.w h0_9208
h0_BC18:
    moveq.l #10,d1
    bsr.w h0_9208
h0_BC1E:
    moveq.l #12,d1
    bsr.w h0_9208
h0_BC24:
    clr.w $4A20(a6)
    move.w #$FFFF,$4A22(a6)
h0_BC2E:
    rts
h0_BC30:
    tst.b $0129(a6)
    bne.s h0_BC2E
h0_BC36:
    bsr.s h0_BCA4
h0_BC38:
    move.l d0,-(a7)
    move.l $4EF6(a6),d1
    sub.l $4FB0(a6),d1
    add.l $4FAC(a6),d1
    bsr.w h0_8F8A
h0_BC4A:
    lea.l dat_BCB8(pc),a0
    bsr.w h0_9334
h0_BC52:
    move.l $4EF6(a6),d1
    bsr.w h0_8F8A
h0_BC5A:
    lea.l dat_BCCC(pc),a0
    bsr.w h0_9334
h0_BC62:
    move.l (a7)+,d2
    sub.l $4FA2(a6),d2
    divu.w #$C8,d2
    move.l d2,-(a7)
    moveq.l #0,d1
    move.w d2,d1
    bsr.w h0_8F8A
h0_BC76:
    moveq.l #46,d1
    bsr.w h0_931A
h0_BC7C:
    move.l (a7)+,d2
    clr.w d2
    swap.w d2
    divu.w #$14,d2
    moveq.l #48,d1
    add.b d2,d1
    bsr.w h0_931A
h0_BC8E:
    lea.l dat_BCD4(pc),a0
    bsr.w h0_9334
h0_BC96:
    tst.l $01D0(a6)
    beq.s h0_BCA0
h0_BC9C:
    bsr.w h0_8F12
h0_BCA0:
    bra.w h0_8F12
h0_BCA4:
    pea.l dat_BCB2(pc)
    move.w #supexec,-(a7)
    trap #14
    addq.l #6,a7                        ; KNOWN: stack cleanup for supexec pop 6
    rts
dat_BCB2:
    DC.B    $20,$38,$04,$ba,$4e,$75 ; VIOLATION: orphaned code island at $BCB2 is not reached from known entrypoints
dat_BCB8:
    DC.B    " bytes used out of ",0
dat_BCCC:
    DC.B    $2c,$20,$74,$6f,$6f,$6b,$20,$00
dat_BCD4:
    DC.B    $20,$73,$65,$63,$6f,$6e,$64,$73,$00
dat_BCDD:
    DC.B    "Enter command line:"
dat_BCF0:
    DC.B    $0d,$0a,$00
dat_BCF3:
    DC.B    $0d
    DC.L    $0a507265
    DC.B    "ss a key to exit",0
    DC.B    $00
h0_BD0A:
    tst.b $4EF1(a6)
    beq.s h0_BD3C
h0_BD10:
    pea.l dat_BCF3(pc)
    move.w #c_conws,-(a7)
    trap #1
    addq.l #6,a7
h0_BD1C:
    move.l #$600FF,-(a7)
    trap #1
    addq.l #4,a7
    tst.w d0
    bne.s h0_BD1C
h0_BD2A:
    move.w #c_rawcin,(a7)
    trap #1
    cmp.b #$D,d0
    beq.s h0_BD3C
h0_BD36:
    cmp.b #$20,d0
    bcs.s h0_BD2A
h0_BD3C:
    move.b $026C(a6),d0
    ext.w d0
    move.w d0,-(a7)
    move.w #p_term,-(a7)
    trap #1
h0_BD4A:
    moveq.l #-1,d0
    move.l d0,-(a7)
    move.l d0,-(a7)
    move.l d0,-(a7)
    move.w #keytbl,-(a7)
    trap #14
    lea.l $000E(a7),a7                  ; KNOWN: stack cleanup for keytbl pop 14
    movea.l d0,a0
    movea.l $0004(a0),a0
    cmpi.b #35,$0004(a0)
    seq.b d0
    ext.w d0
    move.w d0,-(a7)
    move.w #t_getdate,-(a7)
    trap #1
    addq.l #2,a7
    move.w d0,d1
    andi.w #31,d1
    move.w d0,d2
    lsr.w #5,d2
    andi.w #15,d2
    tst.b (a7)+
    beq.s h0_BD8A
h0_BD88:
    exg d2,d1
h0_BD8A:
    bsr.s h0_BDDA
h0_BD8C:
    move.b #$2F,(a3)+
    move.w d2,d1
    bsr.s h0_BDDA
h0_BD94:
    move.b #$2F,(a3)+
    move.w d0,d1
    rol.w #7,d1
    andi.w #127,d1
    addi.w #80,d1
    bsr.s h0_BDDA
h0_BDA6:
    move.b #$20,(a3)+
    move.b #$20,(a3)+
    move.w #t_gettime,-(a7)
    trap #1
    addq.l #2,a7
    move.w d0,d1
    rol.w #5,d1
    andi.w #31,d1
    bsr.s h0_BDDA
h0_BDC0:
    move.b #$3A,(a3)+
    move.w d0,d1
    lsr.w #5,d1
    andi.w #63,d1
    bsr.s h0_BDDA
h0_BDCE:
    move.b #$3A,(a3)+
    move.w d0,d1
    andi.w #31,d1
    add.w d1,d1
h0_BDDA:
    swap.w d1
    clr.w d1
    swap.w d1
    divu.w #$A,d1
    addi.b #48,d1
    move.b d1,(a3)+
    swap.w d1
    addi.b #48,d1
    move.b d1,(a3)+
    rts
h0_BDF4:
    addq.l #1,d1
    andi.b #254,d1
    move.l d1,d0
    add.l $4FAC(a6),d0
    cmp.l $4FB0(a6),d0
    bcc.s h0_BE16
h0_BE06:
    movea.l $4FAC(a6),a0
    add.l d1,$4FAC(a6)
h0_BE0E:
    move.l a0,$4FA8(a6)
    moveq.l #-1,d0
    rts
h0_BE16:
    move.l d1,-(a7)
    move.l #$FFFFFFFF,-(a7)
    move.w #m_alloc,-(a7)
    trap #1
    addq.w #6,a7
    move.l (a7),d1
    cmp.l d1,d0
    bcs.s h0_BE4A
h0_BE2C:
    move.l d0,$4FB0(a6)
    move.l d0,-(a7)
    move.w #m_alloc,-(a7)
    trap #1
    addq.w #6,a7
    move.l (a7)+,d1
    movea.l d0,a0
    add.l d0,$4FB0(a6)
    add.l d1,d0
    move.l d0,$4FAC(a6)
    bra.s h0_BE0E
h0_BE4A:
    move.l (a7)+,d1
    moveq.l #0,d0
    rts
h0_BE50:
    cmpa.l $4FA8(a6),a0
    bne.s h0_BE5E
h0_BE56:
    move.l a0,$4FAC(a6)
    clr.l $4FA8(a6)
h0_BE5E:
    rts
h0_BE60:
    lea.l $0016(a1),a0
    moveq.l #0,d0
    move.b (a0)+,d0
    lea.l -$1(a0,d0.w),a1
    clr.b (a1)
    move.l a1,-(a7)
    bsr.s h0_BE98
h0_BE72:
    movea.l (a7)+,a1
    move.b #$B,(a1)
    tst.l d4
    eori #4,ccr
    rts
h0_BE80:
    movem.l d1/a0,-(a7)
h0_BE84:
    move.b (a0)+,d1
    cmp.b #$3A,d1
    beq.s h0_BE92
h0_BE8C:
    tst.b d1
    bne.s h0_BE84
h0_BE90:
    moveq.l #-1,d1
h0_BE92:
    movem.l (a7)+,d1/a0
h0_BE96:
    rts
h0_BE98:
    bsr.s h0_BE80
h0_BE9A:
    beq.s h0_BEE2
h0_BE9C:
    move.l a0,-(a7)
    bsr.w h0_BEE2
h0_BEA2:
    movea.l (a7)+,a0
    tst.l d4
    bne.s h0_BE96
h0_BEA8:
    movea.l $4EFA(a6),a2
    move.l a0,-(a7)
h0_BEAE:
    move.b (a0)+,(a2)+
    bne.s h0_BEAE
h0_BEB2:
    lea.l $4EFE(a6),a0
    move.l $0868(a6),-(a7)
h0_BEBA:
    bsr.s h0_BEE2
h0_BEBC:
    movea.l (a7)+,a1
    movea.l (a7)+,a0
    tst.l d4
    bne.s h0_BEE0
h0_BEC4:
    tst.b (a1)
    beq.s h0_BEE0
h0_BEC8:
    move.l a0,-(a7)
    lea.l $4FB4(a6),a2
h0_BECE:
    move.b (a1)+,(a2)+
    bne.s h0_BECE
h0_BED2:
    subq.l #1,a2
h0_BED4:
    move.b (a0)+,(a2)+
    bne.s h0_BED4
h0_BED8:
    move.l a1,-(a7)
    lea.l $4FB4(a6),a0
    bra.s h0_BEBA
h0_BEE0:
    rts
h0_BEE2:
    tst.b $010B(a6)
    beq.s h0_BF0C
h0_BEE8:
    lea.l $5084(a6),a2
    move.l a0,-(a7)
h0_BEEE:
    move.b (a0)+,(a2)+
    bne.s h0_BEEE
h0_BEF2:
    lea.l $5084(a6),a0
    lea.l dat_975C(pc),a2
    bsr.w h0_46B0
h0_BEFE:
    bsr.w h0_BF0C
h0_BF02:
    movea.l (a7)+,a0
    tst.l d4
    beq.s h0_BF0C
h0_BF08:
    neg.l d1
    rts
h0_BF0C:
    clr.w -(a7)
    move.l a0,-(a7)
    move.w #$3D,-(a7)
    move.l $01D0(a6),d0
    beq.s h0_BF22
h0_BF1A:
    movea.l d0,a0
    movea.l (a0),a0
    jsr (a0)                            ; CANDIDATE: indirect_call index unresolved
h0_BF20:
    bra.s h0_BF24
h0_BF22:
    trap #1
h0_BF24:
    addq.l #8,a7
    moveq.l #0,d4
    tst.l d0
    bmi.s h0_BF66
h0_BF2C:
    move.l d0,d4
    move.l $01D0(a6),d0
    beq.s h0_BF40
h0_BF34:
    movea.l d0,a0
    tst.l $0020(a0)
    beq.s h0_BF40
h0_BF3C:
    moveq.l #-1,d1
    rts
h0_BF40:
    move.w #$2,-(a7)
    move.w d4,-(a7)
    clr.l -(a7)
    move.w #f_seek,-(a7)
    trap #1
    lea.l $000A(a7),a7
    move.l d0,-(a7)
    clr.w -(a7)
    move.w d4,-(a7)
    clr.l -(a7)
    move.w #f_seek,-(a7)
    trap #1
    lea.l $000A(a7),a7
    move.l (a7)+,d1
h0_BF66:
    rts
h0_BF68:
    move.w d2,-(a7)
    move.w #$3E,-(a7)
    move.l $01D0(a6),d0
    beq.s h0_BF7E
h0_BF74:
    movea.l d0,a0
    movea.l $0004(a0),a0
    jsr (a0)                            ; CANDIDATE: indirect_call index unresolved
h0_BF7C:
    bra.s h0_BF80
h0_BF7E:
    trap #1
h0_BF80:
    addq.l #4,a7
    rts
h0_BF84:
    move.l a0,-(a7)
    move.l d1,-(a7)
    move.w d2,-(a7)
    move.w #f_read,-(a7)
    trap #1
    lea.l $000C(a7),a7
    move.l d0,d1
    moveq.l #0,d0
    rts
h0_BF9A:
    move.l d4,-(a7)
    bsr.w h0_BE98
h0_BFA0:
    move.l d1,d2
    move.l d4,d3
    movem.l (a7)+,d4
    eori #4,ccr
    rts
h0_BFAE:
    move.w d3,d2
    bra.s h0_BF68
h0_BFB2:
    move.l a0,-(a7)
    move.l d1,-(a7)
    move.w d3,-(a7)
    move.w #f_read,-(a7)
    trap #1
    lea.l $000C(a7),a7
    rts
h0_BFC4:
    clr.w -(a7)
    move.l a0,-(a7)
    move.w #f_create,-(a7)
    trap #1
    addq.l #8,a7
    tst.l d0
    bmi.s h0_BFD8
h0_BFD4:
    move.l d0,d2
    moveq.l #0,d0
h0_BFD8:
    rts
h0_BFDA:
    tst.l d1
    beq.s h0_BFFC
h0_BFDE:
    movem.l d1-d2,-(a7)
    move.l $01B4(a6),d2
    move.l a0,-(a7)
    move.l d1,-(a7)
    move.w d2,-(a7)
    move.w #f_write,-(a7)
    trap #1
    lea.l $000C(a7),a7
    movem.l (a7)+,d1-d2
    cmp.l d0,d1
h0_BFFC:
    rts
h0_BFFE:
    clr.w -(a7)
    move.w $01B6(a6),-(a7)
    move.l d2,-(a7)
h0_C006:
    move.w #f_seek,-(a7)
    trap #1
    lea.l $000A(a7),a7
    rts
h0_C012:
    move.w #$1,-(a7)
    move.w $01B6(a6),-(a7)
    clr.l -(a7)
    bra.s h0_C006
h0_C01E:
    tst.b $024F(a6)
    bne.s h0_C03A
h0_C024:
    move.l $4FB0(a6),d0
    sub.l $4FAC(a6),d0
    cmp.l #$7D00,d0
    bcs.s h0_C03A
h0_C034:
    asr.l #1,d0
    cmp.l d0,d1
    bcs.s h0_C03C
h0_C03A:
    move.l d2,d1
h0_C03C:
    rts
h0_C03E:
    lea.l $4FB4(a6),a0
h0_C042:
    move.b (a1)+,d1
    beq.s h0_C05C
h0_C046:
    cmp.b #$D,d1
    beq.s h0_C05C
h0_C04C:
    cmp.b #$20,d1
    beq.s h0_C05C
h0_C052:
    cmp.b #$9,d1
    beq.s h0_C05C
h0_C058:
    move.b d1,(a0)+
    bra.s h0_C042
h0_C05C:
    move.b #$3D,(a0)+
    clr.b (a0)
    lea.l $4FB4(a6),a1
    movea.l $4EF2(a6),a2
    bsr.w h0_BB72
h0_C06E:
    movea.l a0,a1
    beq.s h0_C076
h0_C072:
    lea.l dat_C078(pc),a1
h0_C076:
    rts
dat_C078:
    DC.L    $300045f8,$fa404a2e,$4fa6663e,$48e770e8 ; VIOLATION: orphaned code island at $C078 is not reached from known entrypoints
    DC.B    "&<_FPUa",0
    DC.L    $f8924cdf,$170e660c,$08000010
    DC.B    "f p``",0
    DC.B    $c4,$9c
    DC.L    $48e760e0,$487a001a,$3f3c0026,$4e4e5c8f,$4cdf0706,$4a806600,$c48250ee,$4fa64e75 ; VIOLATION: orphaned code island at $C0A4 is not reached from known entrypoints
    DC.L    $007c0700,$45f8fa40,$240f41f8,$00084a78,$059e6706,$4e7a8801,$50482210,$43fa003a
    DC.L    $2089357c,$9000000a,$0c528900,$67fa257c,$00000000,$00104a12,$6bfc357c,$8800000a
    DC.L    $0c528900,$67fa257c,$00000000,$00104a12,$6bfc7000,$20814e75 ; VIOLATION: orphaned code island at $C0C4 is not reached from known entrypoints
    DC.B    $70,$60,$2e,$42,$60,$f6 ; VIOLATION: orphaned code island at $C11C is not reached from known entrypoints
    DC.B    $70,$05 ; VIOLATION: orphaned code island at $C122 is not reached from known entrypoints
    DC.L    $3f006100,$ff52301f,$4880d040,$610000ec,$70001003,$d040303b,$00044efb,$0002000e
    DC.L    $002e005e,$00760094,$004600b8,$357c7000,$000a0c52,$890067fa,$30aa0010,$4a126bfc
    DC.L    $10a80001,$42280001,$70004e75,$357c7000,$000a0c52,$890067fa,$30aa0010,$4a126bfc
    DC.L    $70004e75,$357c6400,$000a0c52,$890067fa,$20aa0010,$4a126bfc,$70004e75,$357c6000
    DC.L    $000a0c52,$890067fa,$20aa0010,$4a126bfc,$70004e75,$357c7400,$000a0c52,$890067fa
    DC.L    $20aa0010,$216a0010,$00044a12,$6bfc7000
    DC.B    "Nu5|l",0
    DC.B    $00,$0a
    DC.L    $0c528900,$67fa20aa,$0010216a,$00100004,$216a0010,$00084a12,$6bfc7000
    DC.B    "Nu5|h",0
    DC.B    $00,$0a
    DC.L    $0c528900,$67fa20aa,$0010216a,$00100004,$216a0010,$00084a12,$6bfc7000
    DC.B    "Nu0;",0
    DC.B    $04,$4e,$fb
    DC.L    $0002000e,$002c005c,$00740092,$004400b6,$10104880,$3080357c,$5000000a,$0c528900
    DC.L    $67fa3550,$00104a12,$6bfc7000
    DC.B    "Nu5|P",0
    DC.B    $00,$0a
    DC.L    $0c528900,$67fa3550,$00104a12,$6bfc7000
    DC.B    "Nu5|D",0
    DC.B    $00,$0a
    DC.L    $0c528900,$67fa2550,$00104a12,$6bfc7000
    DC.B    "Nu5|@",0
    DC.B    $00,$0a
    DC.L    $0c528900,$67fa2550,$00104a12,$6bfc7000
    DC.B    "Nu5|T",0
    DC.B    $00,$0a
    DC.L    $0c528900,$67fa2550,$00102568,$00040010,$4a126bfc,$70004e75,$357c4c00,$000a0c52
    DC.L    $890067fa,$25500010,$25680004,$00102568,$00080010,$4a126bfc,$70004e75,$357c4800
    DC.L    $000a0c52,$890067fa,$25500010,$25680004,$00102568,$00080010,$4a126bfc,$70004e75
    DC.L    $3f036100,$fd76361f,$48833003,$d0406100,$ff0e357c,$001a000a,$4a126bfc,$3003d040
    DC.L    $6000fe18
dat_C324:
    DC.L    dat_C324
dat_C328:
    DC.L    $00000000,$006e0076,$00d600fc,$00ee0162,$01840086,$01d001dc,$01ce01d8,$02460252
    DC.L    $02b80326,$001c0080,$00340036,$00a200e0,$038a0098,$035201e4,$00f600f2,$038c0102
    DC.L    $010c0108,$01560234,$014801ce,$015e015c,$015c016a,$01ca01d4,$01fc0238,$025a023e
    DC.L    $03f00264,$02480000,$02500278,$0268026c,$02c002d0,$041c046e,$02fc0498,$033e02c4
    DC.L    $02c002dc,$031e038a,$03a2033a,$04fa047e,$03900522,$03a203ac,$03c803b2,$03ba03e4
    DC.L    $040c03ee,$03f0043a,$041403fa,$04de0414,$042a0426,$05460442,$043e0524,$044e04a2
    DC.L    $057e048c,$04ac04b6,$056a04c0,$04ee05d8,$056e050e,$0512056e,$05ca05ce,$05ee0580
    DC.L    $05da05e2,$00000604,$05ea0638,$0578058e,$065205ee,$06200654,$065a063c,$064e0662
    DC.L    $065c064e,$00000668,$0662066c,$067a066e,$06d0067a,$0658066c,$06bc066e,$068006ce
    DC.L    $06de0702,$06dc0000,$00000000,$06e606d2,$00000000,$06ee06ca,$06f406ec,$070006e6
    DC.L    $00000706,$00000000,$06e80000,$00000000,$00000000,$00000000,$06ea0000,$0000071a
    DC.L    $00000000,$073e074a,$00020004,$072e0000,$0778073e,$07560748,$07400762,$07680766
    DC.L    $074c0000,$07660762,$079a0764,$07720766,$07820000,$07c00000,$076a0792,$07d007a0
    DC.L    $07d607bc,$000007d6,$07b807c4,$07e007d4,$07dc07ee,$07d40000,$07f4080a,$082e0832
    DC.L    $08440000,$085807e8,$07ec0856,$08ac0812,$0816086e,$085e087a,$08400850,$0856088a
    DC.L    $08ae08ba,$08a808b8,$08ae08b2,$08c408c6,$08ec08e0,$08d608c8,$000008f4,$08d2091a
    DC.L    $091a0928,$092e0916,$093e0000,$09940932,$09340952,$092e094c,$09460000,$00000952
    DC.L    $0974099a,$09b00000,$098209b8,$00000000,$0000099c,$099c09aa,$09a00000,$000009c2
    DC.L    $09b809a4,$09ca09b0,$09d809b8,$09d809ec,$000009ce,$00000000,$000009de,$09f60a0e
    DC.L    $0a160a1c,$0a1e0a2a,$0a2c0a30,$0a340a3a,$0a660000,$09f40a2a,$0a460a1e,$0a280a96
    DC.L    $0a9e0aa0,$0aa80aaa,$0aac0ab0,$0ab40a72,$0a9c0a8a,$0aae0000,$0aa00ac0,$00000ad2
    DC.L    $0ad00ae0,$0ae20000,$00000000,$00000000,$0af00000,$00000ad6,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$0aec0b20,$00000000,$0af40000,$0af20000
    DC.L    $00000af2,$00000afc,$00000000,$00000000,$00000000,$00000000,$0b040b44,$0b1c0b18
    DC.L    $00000b16,$00000000,$00000000,$0b240b26,$0b340b38,$00000000,$00000000,$00000000
    DC.L    $00000000,$0b380b26,$0b2a0b38,$0b340b38,$0b400000,$00000000,$00000b5a,$0b520000
    DC.L    $00000b7c,$00000000,$00000000,$00000000,$0b820b88,$0b760000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000b8a,$0b8c0b94,$00000000
    DC.L    $00000000,$0b920000,$00000000,$00000000,$0b8a0000,$00000b96,$0b9a0000,$00000bb0
    DC.L    $00000000,$00000000,$0bb20bb8,$0be00bc4,$00000b9e,$00000bba,$00000ba4,$0bcc0bf4
    DC.L    $00000000,$0bc00bac,$0be00bea,$00000c0a,$0c0e0c32,$0c160c1c,$0c440000,$0c5c0c04
    DC.L    $00000c16,$0c2c0c38,$0c2e0c52,$00000c2a,$0c7e0c44,$0cba0000,$0c740000,$00000000
    DC.L    $00000c8a,$00000c6c,$0c7c0c9c,$0ca40c98,$0c860000,$00000cb8,$00000cb4,$00000000
    DC.L    $0c8a0ca4,$0cb80cc4,$0cc00ce0,$0cd60000,$0ca80cb8,$00000cd4,$0cc20000,$0cf00000
    DC.L    $0cea0d0a,$0d0e0000,$0d120cfc,$0d0e0000,$0d080000,$00000000,$00000000,$00000000
    DC.L    $00000000,$0d2c0d2a,$0d2e0d18,$00000d3e,$00000d28,$0d380d30,$0d280d3a,$0d860000
    DC.L    $00000000,$00000d30,$0d4c0d52,$0d340000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000d6e,$0d720d9c,$0d9e0da4,$0da80daa
    DC.L    $0dac0d58,$00000dae,$0db00d94,$00000000,$0db60000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000d9e,$0db60dc8,$0dac0000,$0db60000,$00000000
    DC.L    $0dce0dd0,$00000dec,$00000000,$00000000,$0de00000,$00000df0,$0df80dfa,$00000000
    DC.L    $0e360000,$00000000,$00000000,$00000e00,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000dfc,$0e580000,$00000000,$0e1c0e00,$00000000,$0e1e0000,$00000e28,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$0e2c0000,$00000000,$00000e70,$0e740e9a,$0e800000,$0e520000,$0e820000
    DC.L    $0e720e9c,$0eb20000,$00000e96,$00000000,$0e820000,$0e920e7e,$0eb40e8c,$000a0000
    DC.L    $0ea60ec8,$0ea80eb4,$00000000,$00000ecc,$00000ecc,$00000ec6,$0ed60000,$0eee0000
    DC.L    $00000000,$0ef00000,$00000000,$00000000,$00000000,$00000000,$00000000,$0ed60000
    DC.L    $00000000,$00000000,$00000000,$0eea0f36,$0eec0f0a,$0efc0f00,$0f1e0f18,$0f0a0f10
    DC.L    $00000000,$0f240002,$00000000,$00000000,$00000000,$0f0a0f2c,$0f140f1e,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$0f400f4c
    DC.L    $0f4a0f3c,$00000f50,$0fa00f80,$00000000,$0f800000,$0f6e0f80,$00000000,$00000000
    DC.L    $0fb00000,$00000f80,$00000000,$00000000,$00000000,$00000000,$00000fa0,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$0000000e
    DC.L    $0f8c0fa0,$00000000,$00100f9c,$00000000,$0f9e0000,$0f980fb8,$0fac0000,$00000000
    DC.L    $0fa40fb8,$00000ff0,$0fd61014,$100e1024,$0000102a,$0fda100c,$00000000,$101e1028
    DC.L    $0000102c,$00000000,$00000000,$00000000,$10780000,$00001034,$10200000,$00001082
    DC.L    $10841088,$108a108c,$10901092,$109a0000,$10321062,$00000000,$00000000,$00000000
    DC.L    $00000000,$10980000,$00000000,$00000000,$0000109a,$00000000,$00000000,$109c10b2
    DC.L    $10e210f4,$000010a0,$000010bc,$000010aa,$10fe1106,$00000000,$00000000,$10ea0000
    DC.L    $10f60000,$00000000,$0000110a,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$0000110c,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.B    $00,$00
dat_CB06:
    DC.B    $ff,$ff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$033e0340,$06c6ffff,$0706073a,$0740ffff,$ffffffff,$0002ffff,$ffffffff
    DC.L    $00040006,$0008000a,$000c000e,$ffffffff,$00100012,$ffff0014,$00160018,$001a001c
    DC.L    $ffff001e,$00200022,$0024ffff,$ffff0026,$ffffffff,$ffff011a,$0120ffff,$0122ffff
    DC.L    $00040006,$0008000a,$000c000e,$ffffffff,$00100012,$ffff0014,$00160018,$001a001c
    DC.L    $ffff001e,$00200022,$0024ffff,$ffff0026,$0028ffff,$002a011a,$01200030,$01220032
    DC.L    $00340036,$0038011c,$002c003a,$003c003e,$0040002e,$0042ffff,$00440046,$0048009a
    DC.L    $004a011e,$ffffffff,$0124009c,$ffffffff,$0028ffff,$002affff,$01320030,$ffff0032
    DC.L    $00340036,$0038011c,$002c003a,$003c003e,$0040002e,$0042004c,$00440046,$0048009a
    DC.L    $004a011e,$004e0050,$0124009c,$00520054,$00560058,$005a0126,$0132005c,$005e0060
    DC.L    $00620128,$00680146,$006a006c,$0064006e,$01480150,$0152004c,$0070012a,$00720154
    DC.L    $0066ffff,$004e0050,$ffffffff,$00520054,$00560058,$005a0126,$ffff005c,$005e0060
    DC.L    $00620128,$00680146,$006a006c,$0064006e,$01480150,$01520156,$0070012a,$00720154
    DC.L    $00660074,$00760078,$007a007c,$015e007e,$016a0080,$0164016c,$00820084,$00860088
    DC.L    $01660168,$008a008c,$008e0090,$016e0092,$ffffffff,$00940156,$ffff0096,$ffff0098
    DC.L    $ffff0074,$00760078,$007a007c,$015e007e,$016a0080,$0164016c,$00820084,$00860088
    DC.L    $01660168,$008a008c,$008e0090,$016e0092,$00b00160,$009400b2,$009e0096,$00a80098
    DC.L    $00a000b6,$00aa00a2,$017000b4,$014000a4,$01720162,$00a600b8,$00ac00ba,$ffff0142
    DC.L    $00bc0174,$00aeffff,$ffff0144,$ffffffff,$00b00160,$017600b2,$009effff,$00a8ffff
    DC.L    $00a000b6,$00aa00a2,$017000b4,$014000a4,$01720162,$00a600b8,$00ac00ba,$01580142
    DC.L    $00bc0174,$00ae00be,$00c00144,$00c200c4,$00c600d4,$0176015a,$015c00d6,$00c800ca
    DC.L    $0178017a,$017c0196,$00cc00ce,$00d000d8,$00d20198,$019a00da,$00dcffff,$0158019c
    DC.L    $ffffffff,$ffff00be,$00c0019e,$00c200c4,$00c600d4,$01a0015a,$015c00d6,$00c800ca
    DC.L    $0178017a,$017c0196,$00cc00ce,$00d000d8,$00d20198,$019a00da,$00dc00de,$00e0019c
    DC.L    $00e200e4,$00e600e8,$01a2019e,$01dc00ea,$00ec00ee,$01a000f0,$ffff01de,$01a400f2
    DC.L    $00f400f6,$00f8ffff,$ffffffff,$ffffffff,$ffffffff,$ffff01a6,$01e000de,$00e0ffff
    DC.L    $00e200e4,$00e600e8,$01a2ffff,$01dc00ea,$00ec00ee,$01c600f0,$01c801de,$01a400f2
    DC.L    $00f400f6,$00f800fa,$00fc00fe,$01000102,$01040106,$010801a6,$01e001e2,$010a010c
    DC.L    $010e01ee,$011001e4,$01120114,$0116ffff,$0118ffff,$01c60134,$01c80136,$013801d8
    DC.L    $ffff013a,$01da00fa,$00fc00fe,$01000102,$01040106,$0108013c,$013e01e2,$010a010c
    DC.L    $010e01ee,$011001e4,$01120114,$0116012a,$011801e6,$014a0134,$012c0136,$013801d8
    DC.L    $012e013a,$01da01e8,$01300218,$02260130,$014c014e,$ffff013c,$013effff,$ffffffff
    DC.L    $01ea0228,$01ecffff,$ffffffff,$022a012a,$022c01e6,$014affff,$012cffff,$022effff
    DC.L    $012effff,$023001e8,$01300218,$02260130,$014c014e,$017e0236,$01800182,$01840186
    DC.L    $01ea0228,$01ec0188,$018a018c,$022a018e,$022c0190,$02380192,$023e0194,$022e01a8
    DC.L    $01aa01ac,$02300232,$02400246,$01ae0248,$0234024a,$017e0236,$01800182,$01840186
    DC.L    $01b001b2,$ffff0188,$018a018c,$0252018e,$023a0190,$02380192,$023e0194,$023c01a8
    DC.L    $01aa01ac,$02540232,$02400246,$01ae0248,$0234024a,$025a01b4,$01b601b8,$ffff020e
    DC.L    $01b001b2,$01ba0210,$01bc01be,$02520270,$023a01c0,$01c201c4,$01ca01cc,$023c01ce
    DC.L    $02120214,$0254025c,$01d00216,$0272025e,$01d201d4,$025a01b4,$01b601b8,$01d6020e
    DC.L    $ffffffff,$01ba0210,$01bc01be,$02740270,$ffff01c0,$01c201c4,$01ca01cc,$027a01ce
    DC.L    $02120214,$0242025c,$01d00216,$0272025e,$01d201d4,$ffff027c,$ffff01f0,$01d601f2
    DC.L    $01f401f6,$01f801fa,$024401fc,$02740292,$01fe0200,$02020204,$02940206,$027a0208
    DC.L    $020a020c,$0242021a,$021c021e,$ffff0220,$0256ffff,$0258027c,$022201f0,$022401f2
    DC.L    $01f401f6,$01f801fa,$024401fc,$ffff0292,$01fe0200,$02020204,$02940206,$024c0208
    DC.L    $020a020c,$024e021a,$021c021e,$02500220,$02560276,$0258028e,$02220296,$02240260
    DC.L    $02620264,$02b00278,$02c80266,$02980268,$0290029a,$026a02ca,$ffffffff,$024cffff
    DC.L    $ffff026c,$024effff,$ffff026e,$0250ffff,$ffff0276,$ffff028e,$ffff0296,$ffff0260
    DC.L    $02620264,$02b00278,$02c80266,$02980268,$0290029a,$026a02ca,$027e0280,$028202b2
    DC.L    $029c026c,$028402b6,$0286026e,$029e0288,$02a202a4,$02a602a8,$02a002c0,$028a02b4
    DC.L    $ffff02b8,$028c02aa,$02ba02d0,$02bc02b2,$02ac02ae,$ffffffff,$027e0280,$028202b2
    DC.L    $029c02d2,$028402b6,$028602be,$029e0288,$02a202a4,$02a602a8,$02a002c0,$028a02b4
    DC.L    $02c202b8,$028c02aa,$02ba02d0,$02bc02b2,$02ac02ae,$02b402cc,$02d402d8,$02c402c6
    DC.L    $02da02d2,$02dc02de,$02ce02be,$02e202e4,$02e802ec,$02ee02f6,$02d60302,$02e60304
    DC.L    $02c20306,$030c02e0,$031002f4,$030e02ea,$02f002f2,$02b402cc,$02d402d8,$02c402c6
    DC.L    $02da00ae,$02dc02de,$02ceffff,$02e202e4,$02e802ec,$02ee02f6,$02d60302,$02e60304
    DC.L    $03080306,$030c02e0,$031002f4,$030e02ea,$02f002f2,$00fe0312,$02f80104,$01060108
    DC.L    $030a00ae,$031402fa,$02fc010e,$031e02fe,$ffff0320,$03220300,$03280118,$0324032a
    DC.L    $03080316,$0326032c,$032e0330,$03320334,$03360318,$00fe0312,$02f80104,$01060108
    DC.L    $030a031a,$031402fa,$02fc010e,$031e02fe,$031c0320,$03220300,$03280118,$0324032a
    DC.L    $03380316,$0326032c,$032e0330,$03320334,$03360318,$033a033c,$03420344,$034c034e
    DC.L    $0350031a,$03520354,$03560358,$035c035e,$031c0362,$036affff,$0346036c,$036effff
    DC.L    $03380370,$ffff0358,$0348035a,$03600376,$034a0378,$033a033c,$0342037a,$034c034e
    DC.L    $03500364,$03520354,$03560358,$035c035e,$03820362,$036a035a,$0346036c,$036e0366
    DC.L    $03680370,$03720358,$0348035a,$03600376,$034a0378,$037c0388,$038a037a,$038e0384
    DC.L    $03900364,$03740392,$037e0394,$03960398,$03820380,$039a035a,$0386ffff,$039c0366
    DC.L    $0368038c,$037203c2,$ffff039e,$ffffffff,$03c403a2,$037c0388,$038a03a0,$038e0384
    DC.L    $039003de,$03740392,$037e0394,$03960398,$03a40380,$039a03a6,$038603a8,$039c03ac
    DC.L    $03e0038c,$03aa03c2,$03ae039e,$03b203b4,$03c403a2,$03b0ffff,$03c603a0,$03c803b6
    DC.L    $03ba03de,$03bc03e6,$03ec03b8,$03ee03be,$03a403c0,$ffff03a6,$ffff03a8,$03f003ac
    DC.L    $03e0ffff,$03aaffff,$03ae03e2,$03b203b4,$ffffffff,$03b003e4,$03c603e8,$03c803b6
    DC.L    $03ba03ea,$03bc03e6,$03ec03b8,$03ee03be,$03f203c0,$03ca03cc,$03ce03f4,$03f003fa
    DC.L    $03f603d0,$03fc03d2,$03d403e2,$03fe03d6,$03d803da,$03dc03e4,$040003e8,$04020404
    DC.L    $040e03ea,$03f80410,$04120406,$041a0408,$03f2040a,$03ca03cc,$03ce03f4,$041403fa
    DC.L    $03f603d0,$03fc03d2,$03d40416,$03fe03d6,$03d803da,$03dc040c,$04000418,$04020404
    DC.L    $040e041c,$03f80410,$04120406,$041a0408,$0424040a,$04260420,$0430042a,$04140428
    DC.L    $041e0422,$042c0432,$04340416,$0448044a,$042e044c,$044e040c,$04360418,$ffff0438
    DC.L    $ffff041c,$043a043c,$0450ffff,$0452ffff,$04240454,$04260420,$0430042a,$04560428
    DC.L    $041e0422,$042c0432,$04340464,$0448044a,$042e044c,$044e043e,$04360458,$04400438
    DC.L    $0442045a,$043a043c,$04500444,$04520446,$046c0454,$045e0460,$04620466,$04560468
    DC.L    $045c046e,$04700472,$04780464,$047a046a,$0474047c,$047e043e,$04800458,$04400482
    DC.L    $0442045a,$04760484,$04860444,$04880446,$046c048a,$045e0460,$04620466,$048c0468
    DC.L    $045c046e,$04700472,$0478048e,$047a046a,$0474047c,$047e0490,$04800492,$04c20482
    DC.L    $0496049a,$04760484,$0486ffff,$0488049e,$04a2048a,$04a6ffff,$04aa0494,$048c04ae
    DC.L    $0498049c,$04c404c6,$04c8048e,$04ca04a0,$04a4ffff,$04a80490,$04ac0492,$04c204b0
    DC.L    $0496049a,$ffff04b2,$04b404b6,$ffff049e,$04a204b8,$04a604ba,$04aa0494,$04bc04ae
    DC.L    $0498049c,$04c404c6,$04c804be,$04ca04a0,$04a404c0,$04a804ee,$04ac04cc,$04f004b0
    DC.L    $04f204d2,$04d604b2,$04b404b6,$04da04de,$04e204b8,$04e604ba,$04ea04ce,$04bc04f4
    DC.L    $04d004d4,$04d804f6,$04f804be,$04dc04e0,$04e404c0,$04e804ee,$04ec04cc,$04f004fa
    DC.L    $04f204d2,$04d604fc,$05000502,$04da04de,$04e204fe,$04e60504,$04ea04ce,$050604f4
    DC.L    $04d004d4,$04d804f6,$04f80508,$04dc04e0,$04e40514,$04e80516,$04ec0518,$051a04fa
    DC.L    $050a051c,$02e404fc,$05000502,$02f4051e,$050c04fe,$05200504,$05220524,$05060526
    DC.L    $050e0528,$052a0510,$052c0508,$02ee0512,$052e0514,$05300516,$05320518,$051a0534
    DC.L    $050a051c,$02e40536,$02f002f2,$02f4051e,$050c0538,$0520053a,$05220524,$053c0526
    DC.L    $050e0528,$052a0510,$052c0542,$02ee0512,$052e053e,$05300544,$05320540,$05460534
    DC.L    $0548054a,$054c0536,$02f002f2,$054e0550,$05520538,$0554053a,$05560558,$053c056c
    DC.L    $055e056e,$0570ffff,$055a0542,$0568057a,$057c053e,$05720544,$055c0540,$05460560
    DC.L    $0548054a,$054c057e,$0562056a,$054e0550,$05520574,$05540564,$05560558,$0576056c
    DC.L    $055e056e,$05700566,$055a0580,$0568057a,$057c0582,$05720588,$055c0578,$03cc0560
    DC.L    $05840592,$ffff057e,$0562056a,$059405a8,$05860574,$058a0564,$0596058c,$0576058e
    DC.L    $05aa05ac,$05ae0566,$05900580,$0598059a,$05b00582,$05b20588,$05b40578,$03cc059c
    DC.L    $05840592,$05a005ba,$05a2059e,$059405a8,$058605a4,$058a05a6,$0596058c,$05c2058e
    DC.L    $05aa05ac,$05ae05b6,$059005c4,$0598059a,$05b005c6,$05b205b8,$05b405bc,$05be059c
    DC.L    $05c805ca,$05a005ba,$05a2059e,$05cc05ce,$05d005a4,$05dc05a6,$05d805de,$05c205d2
    DC.L    $05d405da,$05e005b6,$05e805c4,$05e205f6,$05d605c6,$05c005b8,$05f805e4,$05fa05f2
    DC.L    $05c805ca,$05fc05ea,$05ec05e6,$05cc05ce,$05d005fe,$05dc05ee,$05d805de,$05f405d2
    DC.L    $05d405da,$05e005f0,$05e80600,$05e205f6,$05d60602,$05c00606,$05f805e4,$05fa05f2
    DC.L    $060a060c,$05fc05ea,$05ec05e6,$060e0610,$060405fe,$060805ee,$06120614,$05f40616
    DC.L    $0618061a,$061c05f0,$061e0600,$06200622,$06240602,$06340606,$06360638,$063affff
    DC.L    $060a060c,$ffff0626,$ffffffff,$060e0610,$0604063c,$06080640,$06120614,$065c0616
    DC.L    $0618061a,$061c0628,$061e062a,$06200622,$0624063e,$06340642,$06360638,$063a062c
    DC.L    $06440648,$062e0630,$064c0632,$06500654,$0658063c,$065e0640,$06600662,$065c0664
    DC.L    $0646064a,$06660628,$064e062a,$06520656,$065a063e,$06680642,$066a066c,$066e062c
    DC.L    $06440648,$062e0630,$064c0632,$06500654,$06580670,$065e0672,$06600662,$06740664
    DC.L    $0646064a,$06660676,$064e0678,$06520656,$065a067a,$06680686,$066a066c,$066e067c
    DC.L    $ffff067e,$0682068e,$06840690,$0692ffff,$06940670,$06960672,$ffff00fe,$067402f8
    DC.L    $01040106,$01080676,$ffff0678,$010a02fc,$010e067a,$02fe0686,$0688ffff,$0300067c
    DC.L    $0680067e,$0682068e,$06840690,$0692068a,$069406ac,$0696068c,$069800fe,$069e02f8
    DC.L    $01040106,$0108069a,$06a806ae,$010a02fc,$010e06b0,$02fe069c,$068806a0,$030006ba
    DC.L    $068006a2,$06b206aa,$06bc06be,$06c0068a,$06a406ac,$06c2068c,$069806b6,$069e06c4
    DC.L    $06a606b4,$06c8069a,$06a806ae,$06ca06ce,$06d006b0,$06d2069c,$06b806a0,$06d406ba
    DC.L    $06cc06a2,$06b206aa,$06bc06be,$06c006d6,$06a406d8,$06c206da,$06dc06b6,$06de06c4
    DC.L    $06a606b4,$06c806e0,$06f406f6,$06ca06ce,$06d0ffff,$06d206f8,$06b8ffff,$06d4ffff
    DC.L    $06cc06fa,$06fc06fe,$07000702,$070406d6,$070806d8,$070a06da,$06dc070c,$06de06e2
    DC.L    $06e406e6,$070e06e0,$06f406f6,$06e80710,$06ea06ec,$071606f8,$071806ee,$06f006f2
    DC.L    $ffff06fa,$06fc06fe,$07000702,$07040712,$0708071a,$070affff,$0714070c,$071c06e2
    DC.L    $06e406e6,$070e072e,$07300732,$06e80710,$06ea06ec,$07160734,$071806ee,$06f006f2
    DC.L    $071e0720,$07220736,$0738073c,$07240712,$0726071a,$03080728,$0714073e,$071c0742
    DC.L    $07440746,$072a072e,$07300732,$072c0748,$074a074c,$030a0734,$074effff,$ffff0756
    DC.L    $071e0720,$07220736,$0738073c,$0724ffff,$0726ffff,$03080728,$0750073e,$07580742
    DC.L    $07440746,$072a0752,$0776ffff,$072c0748,$074a074c,$030a0754,$074e0760,$075a0756
    DC.L    $075c0778,$0762077a,$077c075e,$07660768,$0764076e,$077e0770,$07500788,$0758076a
    DC.L    $0772078a,$07740752,$0776076c,$ffffffff,$ffffffff,$ffff0754,$07ac0760,$075affff
    DC.L    $075c0778,$0762077a,$077c075e,$07660768,$0764076e,$077e0770,$07800788,$07ae076a
    DC.L    $0772078a,$0774078c,$0790076c,$07940798,$079c0782,$07a007a4,$07ac0784,$078607a8
    DC.L    $07b007b2,$07b4078e,$0792ffff,$0796079a,$079e07b6,$07a207a6,$078007ba,$07ae07aa
    DC.L    $07c807b8,$07ca078c,$079007cc,$07940798,$079c0782,$07a007a4,$07bc0784,$078607a8
    DC.L    $07b007b2,$07b4078e,$079207be,$0796079a,$079e07b6,$07a207a6,$07c007ba,$07c407aa
    DC.L    $07c807b8,$07ca07ce,$07c207cc,$07d607d2,$07d807da,$07dcffff,$07bc07c6,$ffffffff
    DC.L    $ffffffff,$07d0ffff,$ffff07be,$07d4ffff,$ffffffff,$ffffffff,$07c0ffff,$07c4ffff
    DC.L    $ffffffff,$ffff07ce,$07c2ffff,$07d607d2,$07d807da,$07dcffff,$ffff07c6,$ffffffff
    DC.L    $ffffffff,$07d0ffff,$ffffffff,$07d4ffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff
    DC.B    $ff,$ff
dat_DE12:
    DC.B    $ff,$ff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffff0000
    DC.L    $00000000,$0168016a,$05bc0000,$062606be,$06c8ffff,$ffffffff,$0000ffff,$ffffffff
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$ffff0000,$ffff0024,$0028ffff,$002affff
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00040000,$00040024,$00280006,$002a0006
    DC.L    $00060006,$00060026,$00040006,$00060006,$00060004,$0006ffff,$00060006,$00060012
    DC.L    $00060026,$ffffffff,$002c0012,$ffffffff,$0004ffff,$0004ffff,$00320006,$ffff0006
    DC.L    $00060006,$00060026,$00040006,$00060006,$00060004,$00060008,$00060006,$00060012
    DC.L    $00060026,$00080008,$002c0012,$00080008,$00080008,$0008002e,$00320008,$000a000a
    DC.L    $000a002e,$000c0038,$000c000c,$000a000c,$003a003e,$00400008,$000c0038,$000c0042
    DC.L    $000affff,$00080008,$ffffffff,$00080008,$00080008,$0008002e,$ffff0008,$000a000a
    DC.L    $000a002e,$000c0038,$000c000c,$000a000c,$003a003e,$00400044,$000c0038,$000c0042
    DC.L    $000a000e,$000e000e,$000e000e,$0048000e,$004e000e,$004c0050,$000e000e,$000e000e
    DC.L    $004c004c,$000e000e,$000e0010,$00520010,$ffffffff,$00100044,$ffff0010,$ffff0010
    DC.L    $ffff000e,$000e000e,$000e000e,$0048000e,$004e000e,$004c0050,$000e000e,$000e000e
    DC.L    $004c004c,$000e000e,$000e0010,$00520010,$0018004a,$00100018,$00140010,$00160010
    DC.L    $0014001a,$00160014,$00540018,$00360014,$0056004a,$0014001a,$0016001a,$ffff0036
    DC.L    $001a0058,$0016ffff,$ffff0036,$ffffffff,$0018004a,$00580018,$0014ffff,$0016ffff
    DC.L    $0014001a,$00160014,$00540018,$00360014,$0056004a,$0014001a,$0016001a,$00460036
    DC.L    $001a0058,$0016001c,$001c0036,$001c001c,$001c001e,$00580046,$0046001e,$001c001c
    DC.L    $005a005c,$005e0062,$001c001c,$001c001e,$001c0064,$0068001e,$001effff,$0046006a
    DC.L    $ffffffff,$ffff001c,$001c006c,$001c001c,$001c001e,$006e0046,$0046001e,$001c001c
    DC.L    $005a005c,$005e0062,$001c001c,$001c001e,$001c0064,$0068001e,$001e0020,$0020006a
    DC.L    $00200020,$00200020,$0070006c,$007e0020,$00200020,$006e0020,$ffff0080,$00720020
    DC.L    $00200020,$0020ffff,$ffffffff,$ffffffff,$ffffffff,$ffff0072,$00820020,$0020ffff
    DC.L    $00200020,$00200020,$0070ffff,$007e0020,$00200020,$00780020,$00780080,$00720020
    DC.L    $00200020,$00200022,$00220022,$00220022,$00220022,$00220072,$00820084,$00220022
    DC.L    $0022008a,$00220084,$00220022,$0022ffff,$0022ffff,$00780034,$00780034,$0034007c
    DC.L    $ffff0034,$007c0022,$00220022,$00220022,$00220022,$00220034,$00340084,$00220022
    DC.L    $0022008a,$00220084,$00220022,$00220030,$00220086,$003c0034,$00300034,$0034007c
    DC.L    $00300034,$007c0086,$003c0090,$00940030,$003c003c,$ffff0034,$0034ffff,$ffffffff
    DC.L    $00880096,$0088ffff,$ffffffff,$00980030,$009a0086,$003cffff,$0030ffff,$009cffff
    DC.L    $0030ffff,$009e0086,$003c0090,$00940030,$003c003c,$006000a2,$00600060,$00600060
    DC.L    $00880096,$00880060,$00600060,$00980060,$009a0060,$00a40060,$00a80060,$009c0074
    DC.L    $00740074,$009e00a0,$00aa00ae,$007400b0,$00a000b2,$006000a2,$00600060,$00600060
    DC.L    $00740074,$ffff0060,$00600060,$00b60060,$00a60060,$00a40060,$00a80060,$00a60074
    DC.L    $00740074,$00b800a0,$00aa00ae,$007400b0,$00a000b2,$00bc0076,$00760076,$ffff008e
    DC.L    $00740074,$0076008e,$00760076,$00b600c2,$00a60076,$00760076,$007a007a,$00a6007a
    DC.L    $008e008e,$00b800be,$007a008e,$00c400be,$007a007a,$00bc0076,$00760076,$007a008e
    DC.L    $ffffffff,$0076008e,$00760076,$00c600c2,$ffff0076,$00760076,$007a007a,$00ca007a
    DC.L    $008e008e,$00ac00be,$007a008e,$00c400be,$007a007a,$ffff00cc,$ffff008c,$007a008c
    DC.L    $008c008c,$008c008c,$00ac008c,$00c600d2,$008c008c,$008c008c,$00d4008c,$00ca008c
    DC.L    $008c008c,$00ac0092,$00920092,$ffff0092,$00baffff,$00ba00cc,$0092008c,$0092008c
    DC.L    $008c008c,$008c008c,$00ac008c,$ffff00d2,$008c008c,$008c008c,$00d4008c,$00b4008c
    DC.L    $008c008c,$00b40092,$00920092,$00b40092,$00ba00c8,$00ba00d0,$009200d6,$009200c0
    DC.L    $00c000c0,$00de00c8,$00ec00c0,$00d600c0,$00d000d6,$00c000ee,$ffffffff,$00b4ffff
    DC.L    $ffff00c0,$00b4ffff,$ffff00c0,$00b4ffff,$ffff00c8,$ffff00d0,$ffff00d6,$ffff00c0
    DC.L    $00c000c0,$00de00c8,$00ec00c0,$00d600c0,$00d000d6,$00c000ee,$00ce00ce,$00ce00e0
    DC.L    $00d800c0,$00ce00e2,$00ce00c0,$00d800ce,$00da00da,$00dc00dc,$00d800e8,$00ce00e0
    DC.L    $ffff00e2,$00ce00dc,$00e200f2,$00e600e8,$00dc00dc,$ffffffff,$00ce00ce,$00ce00e0
    DC.L    $00d800f4,$00ce00e2,$00ce00e6,$00d800ce,$00da00da,$00dc00dc,$00d800e8,$00ce00e0
    DC.L    $00ea00e2,$00ce00dc,$00e200f2,$00e600e8,$00dc00dc,$00ea00f0,$00f600f8,$00ea00ea
    DC.L    $00fa00f4,$00fc00fe,$00f000e6,$01000102,$01060108,$010a010e,$00f60112,$01020114
    DC.L    $00ea0116,$011a00fe,$011c010c,$011a0106,$010a010a,$00ea00f0,$00f600f8,$00ea00ea
    DC.L    $00fa010c,$00fc00fe,$00f0ffff,$01000102,$01060108,$010a010e,$00f60112,$01020114
    DC.L    $01180116,$011a00fe,$011c010c,$011a0106,$010a010a,$0110011e,$01100110,$01100110
    DC.L    $0118010c,$01200110,$01100110,$01240110,$ffff012c,$012e0110,$01360110,$01340138
    DC.L    $01180122,$0134013a,$013c013e,$01420148,$01580122,$0110011e,$01100110,$01100110
    DC.L    $01180122,$01200110,$01100110,$01240110,$0122012c,$012e0110,$01360110,$01340138
    DC.L    $015e0122,$0134013a,$013c013e,$01420148,$01580122,$01640166,$016c0170,$01720174
    DC.L    $01760122,$0178017a,$017c017e,$01800184,$01220186,$018affff,$0170018c,$018effff
    DC.L    $015e0190,$ffff0186,$0170017e,$01840198,$01700198,$01640166,$016c019a,$01720174
    DC.L    $01760188,$0178017a,$017c017e,$01800184,$019e0186,$018a0188,$0170018c,$018e0188
    DC.L    $01880190,$01940186,$0170017e,$01840198,$01700198,$019c01a2,$01a6019a,$01a801a0
    DC.L    $01aa0188,$019401ac,$019c01ae,$01b001b2,$019e019c,$01b40188,$01a0ffff,$01b80188
    DC.L    $018801a6,$019401c6,$ffff01b8,$ffffffff,$01c801ba,$019c01a2,$01a601b8,$01a801a0
    DC.L    $01aa01ce,$019401ac,$019c01ae,$01b001b2,$01ba019c,$01b401bc,$01a001bc,$01b801be
    DC.L    $01d001a6,$01bc01c6,$01be01b8,$01c001c0,$01c801ba,$01beffff,$01ca01b8,$01ca01c0
    DC.L    $01c401ce,$01c401d4,$01d801c0,$01da01c4,$01ba01c4,$ffff01bc,$ffff01bc,$01dc01be
    DC.L    $01d0ffff,$01bcffff,$01be01d2,$01c001c0,$ffffffff,$01be01d2,$01ca01d6,$01ca01c0
    DC.L    $01c401d6,$01c401d4,$01d801c0,$01da01c4,$01de01c4,$01cc01cc,$01cc01e0,$01dc01e4
    DC.L    $01e201cc,$01e601cc,$01cc01d2,$01e801cc,$01cc01cc,$01cc01d2,$01ea01d6,$01ec01ee
    DC.L    $01f201d6,$01e201f4,$01f601ee,$01fc01f0,$01de01f0,$01cc01cc,$01cc01e0,$01fa01e4
    DC.L    $01e201cc,$01e601cc,$01cc01fa,$01e801cc,$01cc01cc,$01cc01f0,$01ea01fa,$01ec01ee
    DC.L    $01f201fe,$01e201f4,$01f601ee,$01fc01f0,$020201f0,$02020200,$02060204,$01fa0202
    DC.L    $01fe0200,$02040208,$020801fa,$020e0210,$02040212,$021401f0,$020801fa,$ffff0208
    DC.L    $ffff01fe,$02080208,$0216ffff,$0218ffff,$0202021e,$02020200,$02060204,$02200202
    DC.L    $01fe0200,$02040208,$02080228,$020e0210,$02040212,$0214020c,$02080220,$020c0208
    DC.L    $020c0222,$02080208,$0216020c,$0218020c,$0232021e,$02240224,$0224022a,$0220022a
    DC.L    $02220234,$02360238,$02400228,$0242022a,$023e0244,$0246020c,$02460220,$020c0248
    DC.L    $020c0222,$023e024a,$024c020c,$024e020c,$02320252,$02240224,$0224022a,$025a022a
    DC.L    $02220234,$02360238,$0240025c,$0242022a,$023e0244,$0246025e,$02460260,$02740248
    DC.L    $02620264,$023e024a,$024cffff,$024e0266,$02680252,$026affff,$026c0260,$025a026e
    DC.L    $02620264,$02760278,$027a025c,$027c0266,$0268ffff,$026a025e,$026c0260,$0274026e
    DC.L    $02620264,$ffff0270,$02700270,$ffff0266,$02680270,$026a0270,$026c0260,$0270026e
    DC.L    $02620264,$02760278,$027a0270,$027c0266,$02680270,$026a028e,$026c027e,$0290026e
    DC.L    $02920280,$02820270,$02700270,$02840286,$02880270,$028a0270,$028c027e,$02700294
    DC.L    $027e0280,$02820298,$029a0270,$02840286,$02880270,$028a028e,$028c027e,$0290029e
    DC.L    $02920280,$028202a0,$02a202a4,$02840286,$028802a0,$028a02b0,$028c027e,$02b60294
    DC.L    $027e0280,$02820298,$029a02d0,$02840286,$028802d8,$028a02dc,$028c02dc,$02e2029e
    DC.L    $02d202e6,$02f802a0,$02a202a4,$02fc02fe,$02d202a0,$030202b0,$030c030e,$02b60310
    DC.L    $02d20312,$032402d2,$032602d0,$02fa02d2,$032802d8,$032a02dc,$032c02dc,$02e2032e
    DC.L    $02d202e6,$02f80330,$02fa02fa,$02fc02fe,$02d2033a,$0302033c,$030c030e,$03420310
    DC.L    $02d20312,$032402d2,$03260350,$02fa02d2,$03280342,$032a0352,$032c0342,$0354032e
    DC.L    $03760378,$037a0330,$02fa02fa,$03840390,$0396033a,$0398033c,$039e03a8,$034203b2
    DC.L    $03aa03b6,$03baffff,$03a80350,$03ae03c4,$03c60342,$03bc0352,$03a80342,$035403aa
    DC.L    $03760378,$037a03c8,$03ac03ae,$03840390,$039603bc,$039803ac,$039e03a8,$03be03b2
    DC.L    $03aa03b6,$03ba03ac,$03a803ca,$03ae03c4,$03c603ce,$03bc03d0,$03a803be,$03d603aa
    DC.L    $03ce03d4,$ffff03c8,$03ac03ae,$03d403de,$03ce03bc,$03d003ac,$03d403d2,$03be03d2
    DC.L    $03e203e4,$03e603ac,$03d203ca,$03d803d8,$03e803ce,$03ea03d0,$03ee03be,$03d603d8
    DC.L    $03ce03d4,$03dc03f2,$03dc03d8,$03d403de,$03ce03dc,$03d003dc,$03d403d2,$03f803d2
    DC.L    $03e203e4,$03e603f0,$03d20402,$03d803d8,$03e80406,$03ea03f0,$03ee03f4,$03f403d8
    DC.L    $0408040a,$03dc03f2,$03dc03d8,$040c040e,$041003dc,$042003dc,$041a0422,$03f80416
    DC.L    $0416041a,$042403f0,$04280402,$04260430,$04160406,$03f403f0,$04320426,$0436042c
    DC.L    $0408040a,$04380428,$042a0426,$040c040e,$0410043c,$0420042a,$041a0422,$042c0416
    DC.L    $0416041a,$0424042a,$04280440,$04260430,$04160442,$03f40444,$04320426,$0436042c
    DC.L    $0448044a,$04380428,$042a0426,$044c0450,$0442043c,$0444042a,$04640466,$042c0468
    DC.L    $046a046e,$0472042a,$04740440,$04760478,$047a0442,$04860444,$0488048a,$048cffff
    DC.L    $0448044a,$ffff047c,$ffffffff,$044c0450,$044204b2,$044404b4,$04640466,$04c20468
    DC.L    $046a046e,$0472047c,$0474047c,$04760478,$047a04b2,$048604b4,$0488048a,$048c047c
    DC.L    $04b604b8,$047c047c,$04ba047c,$04bc04be,$04c004b2,$04c604b4,$04c804ca,$04c204d0
    DC.L    $04b604b8,$04ee047c,$04ba047c,$04bc04be,$04c004b2,$04f004b4,$04f204f4,$04f8047c
    DC.L    $04b604b8,$047c047c,$04ba047c,$04bc04be,$04c00500,$04c60502,$04c804ca,$050604d0
    DC.L    $04b604b8,$04ee0510,$04ba0516,$04bc04be,$04c00518,$04f00542,$04f204f4,$04f8051a
    DC.L    $ffff051a,$052e054c,$052e054e,$0554ffff,$055a0500,$05840502,$ffff0520,$05060520
    DC.L    $05200520,$05200510,$ffff0516,$05200520,$05200518,$05200542,$0544ffff,$0520051a
    DC.L    $0520051a,$052e054c,$052e054e,$05540544,$055a0598,$05840544,$058e0520,$05900520
    DC.L    $05200520,$0520058e,$0594059c,$05200520,$052005a0,$0520058e,$05440590,$052005aa
    DC.L    $05200592,$05a20594,$05b005b4,$05b60544,$05920598,$05b80544,$058e05a4,$059005ba
    DC.L    $059205a2,$05c0058e,$0594059c,$05c205c4,$05c605a0,$05ce058e,$05a40590,$05d205aa
    DC.L    $05c20592,$05a20594,$05b005b4,$05b605d6,$059205d8,$05b805dc,$05e405a4,$05fc05ba
    DC.L    $059205a2,$05c0060c,$06100612,$05c205c4,$05c6ffff,$05ce0614,$05a4ffff,$05d2ffff
    DC.L    $05c20616,$0618061a,$061c061e,$062405d6,$063405d8,$063605dc,$05e40638,$05fc060e
    DC.L    $060e060e,$063a060c,$06100612,$060e065c,$060e060e,$06600614,$0662060e,$060e060e
    DC.L    $ffff0616,$0618061a,$061c061e,$0624065e,$06340666,$0636ffff,$065e0638,$0666060e
    DC.L    $060e060e,$063a066a,$06700674,$060e065c,$060e060e,$06600676,$0662060e,$060e060e
    DC.L    $06680668,$06680686,$069a06c0,$0668065e,$06680666,$06800668,$065e06c2,$066606ca
    DC.L    $06d006d4,$0668066a,$06700674,$066806d6,$06d806e0,$06800676,$06e2ffff,$ffff06e8
    DC.L    $06680668,$06680686,$069a06c0,$0668ffff,$0668ffff,$06800668,$06e606c2,$06e806ca
    DC.L    $06d006d4,$066806e6,$06f4ffff,$066806d6,$06d806e0,$068006e6,$06e206ec,$06ea06e8
    DC.L    $06ea06f6,$06ec06fc,$06fe06ea,$06ee06ee,$06ec06f2,$070206f2,$06e60716,$06e806ee
    DC.L    $06f20718,$06f206e6,$06f406ee,$ffffffff,$ffffffff,$ffff06e6,$073006ec,$06eaffff
    DC.L    $06ea06f6,$06ec06fc,$06fe06ea,$06ee06ee,$06ec06f2,$070206f2,$07100716,$073206ee
    DC.L    $06f20718,$06f2071e,$072006ee,$07220724,$07260710,$0728072a,$07300710,$0710072c
    DC.L    $07440752,$075c071e,$0720ffff,$07220724,$0726075c,$0728072a,$0710075e,$0732072c
    DC.L    $0766075c,$076a071e,$0720076e,$07220724,$07260710,$0728072a,$075e0710,$0710072c
    DC.L    $07440752,$075c071e,$07200760,$07220724,$0726075c,$0728072a,$0760075e,$0762072c
    DC.L    $0766075c,$076a0770,$0760076e,$077c0772,$0780078a,$07b6ffff,$075e0762,$ffffffff
    DC.L    $ffffffff,$0770ffff,$ffff0760,$0772ffff,$ffffffff,$ffffffff,$0760ffff,$0762ffff
    DC.L    $ffffffff,$ffff0770,$0760ffff,$077c0772,$0780078a,$07b6ffff,$ffff0762,$ffffffff
    DC.L    $ffffffff,$0770ffff,$ffffffff,$0772ffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff,$ffffffff
    DC.L    $ffffffff,$ffffffff
    DC.B    $ff,$ff
dat_F11E:
    DC.B    $00,$00
    DC.L    $00000000,$00000e36,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000d2e,$00020000,$00000000,$00000e00,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$80001380,$80000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00002bf6,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$000051c0,$2d6a8000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$50c02d6a,$80000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$000051f8,$303c8000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $50f8303c,$80000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$d000015e,$8000c000,$13808000,$e1002ec0,$8000e000,$2ec08000,$640002f4
    DC.L    $80000000,$00000000,$00000000,$00006500,$02f48000,$670002f4,$80000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00006c00
    DC.L    $02f48000,$00000000,$00006e00,$02f48000,$620002f4,$80000000,$00000000,$6f0002f4
    DC.L    $80006300,$02f48000,$6d0002f4,$80006b00,$02f48000,$660002f4,$80006a00,$02f48000
    DC.L    $600002f4,$80000000,$00000000,$610002f4,$80000000,$2d820000,$00000000,$00006800
    DC.L    $02f48000,$690002f4,$80000000,$00000000,$00000000,$000008c0,$07388000,$41800922
    DC.L    $80000000,$00000000,$4200309a,$8000b000,$0aa48000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$51c80c14,$80000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$50c80c14,$80000000,$00000000
    DC.L    $00000c60,$00000000,$00000000,$00000000,$00000000,$0e1e4000,$b0001380,$80000000
    DC.L    $0e360000,$00000000,$0000c100,$0f6c8000,$48800fc2,$80000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $f0803c7a,$80010000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$f08f3c7a,$80010000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$414a8001,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$000f414a
    DC.L    $80010000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00004cdc,$00000000,$4d120000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00001064,$00000000,$00000000,$00000000
    DC.L    $00004ec0,$11628000,$4e801162,$800041c0,$11728000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$e1082ec0,$8000e008,$2ec08000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$4400309a
    DC.L    $80000000,$00000000,$4e7158a4,$80004600,$309a8000,$00000000,$00000000,$26424000
    DC.L    $00001d36,$00000000,$12fc8000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$48402ada,$80000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00002b8e,$00000000,$00000000,$00000000,$0000e118,$2ec08000,$e0182ec0,$80000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$4e742d18,$80004e73,$58988000,$06c02d36
    DC.L    $80004e77,$58a48000,$4e7558a4,$80000000,$00000000,$54c02d6a,$800055c0,$2d6a8000
    DC.L    $00000000,$000057c0,$2d6a8000,$00002e3e,$00005cc0,$2d6a8000,$5ec02d6a,$800052c0
    DC.L    $2d6a8000,$5fc02d6a,$800053c0,$2d6a8000,$5dc02d6a,$80005bc0,$2d6a8000,$56c02d6a
    DC.L    $80000000,$2f484000,$5ac02d6a,$80000000,$00000000,$9000015e,$800058c0,$2d6a8000
    DC.L    $59c02d6a,$80000000,$00000000,$4ac02fae,$80000000,$00000000,$54f8303c,$800055f8
    DC.L    $303c8000,$00000000,$000057f8,$303c8000,$00000000,$00005cf8,$303c8000,$5ef8303c
    DC.L    $800052f8,$303c8000,$5ff8303c,$800053f8,$303c8000,$5df8303c,$80005bf8,$303c8000
    DC.L    $56f8303c,$80000000,$00000000,$5af8303c,$80000000,$00000000,$00000000,$000050f8
    DC.L    $303c8000,$00000000,$00004a00,$30a68000,$000030ba,$400058f8,$303c8000,$59f8303c
    DC.L    $80000000,$00000000,$00000000,$00000000,$00000000,$00000000,$0000c100,$00088000
    DC.L    $d0c0021e,$80000600,$02a08000,$5000156a,$8000d100,$00028000,$020012fc,$80000840
    DC.L    $06b08000,$088006b0,$80000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$4afa4ae2,$80004848,$04b68000
    DC.L    $08c006b0,$80000800,$06328000,$00000000,$00000000,$00000000,$0cfc079a,$800008c0
    DC.L    $09628000,$00000000,$000000c0,$09628000,$b0c0021e,$80000c00,$02c68000,$b1080b5e
    DC.L    $80000000,$0b920000,$00002d90,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00002d7a,$000054c8,$0c148000,$55c80c14,$800057c8,$0c148000,$5cc80c14,$80005ec8
    DC.L    $0c148000,$52c80c14,$80005fc8,$0c148000,$53c80c14,$80005dc8,$0c148000,$5bc80c14
    DC.L    $800056c8,$0c148000,$5ac80c14,$800051c8,$0c148000,$58c80c14,$800059c8,$0c148000
    DC.L    $81c00a02,$800080c0,$0a028000,$00004f20,$40000000,$4efc0000,$00005528,$00000000
    DC.L    $56ca0000,$0a0012fc,$80000000,$00000000,$00000ef4,$00000000,$0f5e8000,$49c00fdc
    DC.L    $80004880,$0ff48000,$001840a8,$80010000,$00000000,$002240a8,$80010000,$100e4000
    DC.L    $00000000,$00000000,$00000000,$f0813c7a,$8001f093,$3c7a8001,$f0963c7a,$8001f092
    DC.L    $3c7a8001,$f0953c7a,$8001f094,$3c7a8001,$f08e3c7a,$80010000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$0000f087,$3c7a8001,$00000000,$0000f090,$3c7a8001
    DC.L    $00000000,$0000f09f,$3c7a8001,$00000000,$00000000,$00000000,$00000000,$0000f088
    DC.L    $3c7a8001,$003840a8,$8001001d,$40a88001,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$3c828001,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$000f3c82,$80010000,$00000000,$00000000,$00000020
    DC.L    $40a88001,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$3b9e0001,$00000000,$00000000,$00000000,$000140a8,$80010000,$00000000
    DC.L    $002140a8,$80010000,$00000000,$002340a8,$8001001a,$40a88001,$f0804078,$80010000
    DC.L    $3afa4000,$00000000,$00000025,$40a88001,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$0001414a,$80010013,$414a8001
    DC.L    $0016414a,$80010012,$414a8001,$000e40a8,$80010015,$414a8001,$0014414a,$80010000
    DC.L    $00000000,$00000000,$0000000e,$414a8001,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$0007414a,$80010000,$00000000,$00000000,$00000010,$414a8001
    DC.L    $00000000,$00000000,$00000000,$001f414a,$80010000,$00000000,$002840a8,$80010000
    DC.L    $00000000,$00000000,$00000000,$00000000,$0008414a,$8001000f,$40a88001,$00000000
    DC.L    $00000000,$00000000,$003a41f0,$80010000,$00000000,$000015b8,$00000000,$4dbc0000
    DC.L    $00004daa,$00000000,$4da40000,$00004db6,$00000000,$4db00000,$00004ce4,$00000000
    DC.L    $4d260000,$00004dc2,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00004e50,$12208000,$0000ea26,$40000000,$12da4000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$16908000,$c1c00a02,$8000c0c0
    DC.L    $0a028000,$48001cce,$80004000,$309a8000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$81402a9e,$80000000,$2aea4000,$f08744be,$80fff086,$44be80ff
    DC.L    $f08144be,$80fff080,$44be80ff,$f08f44be,$80fff08e,$44be80ff,$f08d44be,$80fff08c
    DC.L    $44be80ff,$f08b44be,$80fff08a,$44be80ff,$f08344be,$80fff082,$44be80ff,$f08544be
    DC.L    $80fff084,$44be80ff,$f08944be,$80fff088,$44be80ff,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$2b0a4000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000007,$494a80ff,$0006494a,$80ff0000,$00000000,$0001494a,$80ff0000,$494a80ff
    DC.L    $000f494a,$80ff000e,$494a80ff,$000d494a,$80ff000c,$494a80ff,$000b494a,$80ff000a
    DC.L    $494a80ff,$0003494a,$80ff0002,$494a80ff,$0005494a,$80ff0004,$494a80ff,$0009494a
    DC.L    $80ff0008,$494a80ff,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $0000557e,$00000000,$00000000,$00002cc0,$0000e110,$2ec08000,$e0102ec0,$80000000
    DC.L    $00000000,$00000000,$00008100,$00088000,$00000000,$00004e72,$2f768000,$90c0021e
    DC.L    $80000400,$02a08000,$5100156a,$80000000,$00000000,$91000002,$80004840,$2fa08000
    DC.L    $08004b12,$80000000,$4b128000,$00000000,$00000000,$2d880000,$5af8303c,$80004e40
    DC.L    $2fba8000,$4e583108,$80008180,$2a9e8000,$00003128,$40000000,$31824000,$eac00566
    DC.L    $8000ecc0,$05668000,$00000000,$0000edc0,$051c8000,$efc004de,$8000eec0,$05668000
    DC.L    $e8c00566,$800006c0,$06fe8000,$00000852,$8000f418,$4b708000,$f4084b94,$8000f410
    DC.L    $4b948000,$00000000,$00000000,$00000000,$00002db8,$80004c40,$09b28000,$4c4009ae
    DC.L    $80000000,$00000000,$00000000,$0000001c,$40a88001,$000c40a8,$8001000a,$40a88001
    DC.L    $f0973c7a,$8001f09c,$3c7a8001,$f0993c7a,$8001f09d,$3c7a8001,$f09a3c7a,$8001f09b
    DC.L    $3c7a8001,$f0833c7a,$8001f086,$3c7a8001,$f0823c7a,$8001f085,$3c7a8001,$f0843c7a
    DC.L    $8001f091,$3c7a8001,$f09e3c7a,$8001f089,$3c7a8001,$f08b3c7a,$8001f08a,$3c7a8001
    DC.L    $f08d3c7a,$8001f08c,$3c7a8001,$001940a8,$8001005c,$409e8001,$0066409e,$80010001
    DC.L    $3c828001,$00133c82,$80010016,$3c828001,$00123c82,$80010015,$3c828001,$00143c82
    DC.L    $8001000e,$3c828001,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00073c82,$80010000,$00000000,$00103c82,$80010000,$00000000,$001f3c82,$80010000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00083c82,$80010064,$409e8001,$00000000
    DC.L    $00000067,$409e8001,$005e409e,$80010000,$00000000,$006c409e,$80010010,$40a88001
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$001640a8,$80010014
    DC.L    $40a88001,$00003c96,$80010000,$00000000,$00000000,$00000058,$409e8001,$0062409e
    DC.L    $8001f100,$412a8001,$00000000,$00000060,$409e8001,$00000000,$00000017,$414a8001
    DC.L    $00000000,$00000000,$00000000,$000240a8,$80010000,$00000000,$0063409e,$8001005a
    DC.L    $409e8001,$001c414a,$80010019,$414a8001,$001d414a,$8001001a,$414a8001,$001b414a
    DC.L    $80010003,$414a8001,$0006414a,$80010002,$414a8001,$0005414a,$80010004,$414a8001
    DC.L    $000440a8,$80010011,$414a8001,$001e414a,$80010000,$00000000,$0068409e,$80010009
    DC.L    $414a8001,$000b414a,$8001000a,$414a8001,$000d414a,$8001000c,$414a8001,$000940a8
    DC.L    $80010000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $4f840000,$00005518,$00000000,$00000000,$00000000,$00002040,$1a828000,$4e7a17e4
    DC.L    $80004880,$19468000,$01081b0c,$80007000,$1bd88000,$0e001c5a,$80000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000007,$44fa80ff,$000644fa,$80ff0001
    DC.L    $44fa80ff,$000044fa,$80ff000f,$44fa80ff,$000e44fa,$80ff000d,$44fa80ff,$000c44fa
    DC.L    $80ff000b,$44fa80ff,$000a44fa,$80ff0003,$44fa80ff,$000244fa,$80ff0005,$44fa80ff
    DC.L    $000444fa,$80ff0009,$44fa80ff,$000844fa,$80ff0000,$00000000,$00000000,$0000f000
    DC.L    $47de80ff,$00000000,$0000f100,$492680ff,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$2b2e4000,$4e705898,$80000000,$00000000,$00002d06,$40000000,$00000000
    DC.L    $00000000,$00000c00,$4b128000,$04004b12,$80000800,$2fe88000,$00002fe8,$80004e76
    DC.L    $58a48000,$ebc0051c,$8000e9c0,$051c8000,$00000000,$0000f438,$4b708000,$f4284b94
    DC.L    $8000f430,$4b948000,$00004f20,$40000000,$0ec80000,$000d40a8,$8001f098,$3c7a8001
    DC.L    $00173c82,$8001001c,$3c828001,$00193c82,$8001001d,$3c828001,$001a3c82,$8001001b
    DC.L    $3c828001,$00033c82,$80010006,$3c828001,$00023c82,$80010005,$3c828001,$00043c82
    DC.L    $80010011,$3c828001,$001e3c82,$80010009,$3c828001,$000b3c82,$8001000a,$3c828001
    DC.L    $000d3c82,$8001000c,$3c828001,$004440a8,$80010045,$409e8001,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000003,$40a88001,$001540a8,$80010000,$00000000,$00000000
    DC.L    $0000c000,$3e748001,$00001016,$40000000,$00000000,$002640a8,$80010000,$00000000
    DC.L    $00000000,$00000000,$00000000,$004040a8,$80010018,$414a8001,$0041409e,$80010000
    DC.L    $00000000,$00000000,$00000000,$41da8001,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$0000000f,$41da8001,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$108e8000,$0000113c,$40000000,$00000000,$00000000,$000001c0
    DC.L    $4af08000,$00000000,$00000000,$15b88000,$f6004bc6,$80000000,$ec1a4000,$00002b02
    DC.L    $40000000,$1cda0000,$00002a6c,$4000f000,$45f680ff,$22004784,$80ff2000,$478480ff
    DC.L    $00000000,$00000000,$00000000,$82004984,$80ff8000,$498480ff,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$f0004a68,$80ff0000,$00000000,$00000000,$00000000,$31024000
    DC.L    $00000bee,$40000018,$3c828001,$000840a8,$8001001e,$40a88001,$001f40a8,$80010005
    DC.L    $40a88001,$f0004028,$80010000,$00000000,$002440a8,$80010027,$40a88001,$f000415e
    DC.L    $80010012,$40a88001,$000141da,$80010013,$41da8001,$001641da,$80010012,$41da8001
    DC.L    $001541da,$80010014,$41da8001,$000e41da,$80010000,$00000000,$00000000,$00000000
    DC.L    $00000000,$00000000,$00000007,$41da8001,$00000000,$00000010,$41da8001,$00000000
    DC.L    $0000001f,$41da8001,$00000000,$00000000,$00000000,$00000000,$00000008,$41da8001
    DC.L    $001140a8,$80014afc,$58a48000,$00001148,$40000000,$00000000,$00001402,$4000f000
    DC.L    $456080ff,$f50045a0,$80fff000,$475a80ff,$f0004736,$80fff000,$47be80ff,$00000000
    DC.L    $00000007,$4a4280ff,$00064a42,$80ff0001,$4a4280ff,$00004a42,$80ff000f,$4a4280ff
    DC.L    $000e4a42,$80ff000d,$4a4280ff,$000c4a42,$80ff000b,$4a4280ff,$000a4a42,$80ff0003
    DC.L    $4a4280ff,$00024a42,$80ff0005,$4a4280ff,$00044a42,$80ff0009,$4a4280ff,$00084a42
    DC.L    $80ff0000,$2cfe4000,$00002e2c,$0000f140,$410a8001,$001741da,$8001001c,$41da8001
    DC.L    $001941da,$8001001d,$41da8001,$001a41da,$8001001b,$41da8001,$000341da,$80010006
    DC.L    $41da8001,$000241da,$80010005,$41da8001,$000441da,$80010011,$41da8001,$001e41da
    DC.L    $80010009,$41da8001,$000b41da,$8001000a,$41da8001,$000d41da,$8001000c,$41da8001
    DC.L    $000012b0,$4000f510,$45dc80ff,$f1404926,$80ff0018,$41da8001
h0_108B8:
    rts
h0_108BA:
    rts
    DC.L    $4a2e0104 ; VIOLATION: orphaned code island at $108BC is not reached from known entrypoints
    DC.B    "g(",$22,"n"
    DC.L    $01de4a2e,$026a6612,$222e026e,$92a9001a,$d3a90012,$2342001a
    DC.B    $60,$0c
    DC.B    $08,$e9,$00,$00,$00,$10,$66,$04,$23,$42,$00,$16,$70,$00,$4e,$75 ; VIOLATION: orphaned code island at $108DE is not reached from known entrypoints
    DC.B    $70,$ff,$4e,$75 ; VIOLATION: orphaned code island at $108EE is not reached from known entrypoints
h0_108F2:
    movea.l $01DE(a6),a0
    btst.b #1,$0010(a0)
    bne.w h0_1090E
h0_10900:
    add.l d1,$027E(a6)
    bset.b #0,$0010(a0)
    beq.s h0_10914
h0_1090C:
    rts
h0_1090E:
    jmp h0_852A.l
h0_10914:
    moveq.l #8,d0
    jmp h0_8660.l
h0_1091C:
    move.b #$E,$0109(a6)
    tst.b $026A(a6)
    bne.s h0_10974
h0_10928:
    move.l a1,d2
    bsr.w h0_ADE8
h0_1092E:
    beq.s h0_1096E
h0_10930:
    movem.l a0-a1,-(a7)
    moveq.l #34,d1
    bsr.w h0_9146
h0_1093A:
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
    bne.s h0_10968
h0_10962:
    bset.b #1,$0010(a0)
h0_10968:
    clr.l $0008(a0)
    movea.l a0,a1
h0_1096E:
    move.l a1,$01DE(a6)
    rts
h0_10974:
    bsr.w h0_ADE8
h0_10978:
    bne.w h0_AE28
h0_1097C:
    move.l $000C(a1),$027E(a6)
    bne.s h0_1098C
h0_10984:
    lea.l $05DE(a6),a0
    move.l a0,$027E(a6)
h0_1098C:
    move.l a1,$01DE(a6)
    tst.l $01C4(a6)
    beq.s h0_109B4
h0_10996:
    movem.l a1/a4,-(a7)
    movea.l $01C4(a6),a4
    move.b (a4)+,d1
    jsr h0_175A.l
h0_109A6:
    movem.l (a7)+,a1/a4
    move.l d2,$001E(a1)
    bset.b #2,$0010(a1)
h0_109B4:
    rts
h0_109B6:
    bsr.w h0_ADE8
h0_109BA:
    bne.w h0_AE28
h0_109BE:
    tst.b $026A(a6)
    bne.s h0_109D8
h0_109C4:
    move.l $026E(a6),d2
    sub.l $001A(a1),d2
    add.l d2,$0012(a1)
    move.l $026E(a6),$001A(a1)
    rts
h0_109D8:
    move.l a5,$000C(a1)
    rts
h0_109DE:
    lea.l $01DA(a6),a3
    moveq.l #26,d4
h0_109E4:
    tst.l (a3)
    beq.s h0_109FE
h0_109E8:
    movea.l (a3),a3
    move.l $0012(a3),d1
    beq.s h0_109FC
h0_109F0:
    btst.b #1,$0010(a3)
    bne.s h0_109FC
h0_109F8:
    add.l d1,d4
    addq.l #8,d4
h0_109FC:
    bra.s h0_109E4
h0_109FE:
    cmp.l $01CC(a6),d4
    bcs.s h0_10A0A
h0_10A04:
    jmp h0_88EA.l
h0_10A0A:
    lea.l $01DA(a6),a3
    movea.l $01C8(a6),a2
    clr.w (a2)+
    clr.l (a2)+
    lea.l $000C(a2),a2
    moveq.l #0,d3
h0_10A1C:
    tst.l (a3)
    beq.s h0_10A50
h0_10A20:
    movea.l (a3),a3
    move.l $0012(a3),d0
    beq.s h0_10A46
h0_10A28:
    btst.b #1,$0010(a3)
    bne.s h0_10A46
h0_10A30:
    addq.l #1,d3
    move.l d0,(a2)+
    clr.l (a2)+
    move.l a2,$0008(a3)
    move.l a2,$000C(a3)
    adda.l d0,a2
    clr.l -$0004(a2)
    bra.s h0_10A1C
h0_10A46:
    clr.l $0008(a3)
    clr.l $000C(a3)
    bra.s h0_10A1C
h0_10A50:
    movea.l $01C8(a6),a0
    addq.l #2,a0
    move.l a2,(a0)+
    clr.l (a2)
    clr.l (a0)+
    clr.l (a0)+
    move.l d3,(a0)
    rts
h0_10A62:
    moveq.l #0,d0
    lea.l $01DA(a6),a3
h0_10A68:
    tst.l (a3)
    beq.s h0_10A8E
h0_10A6C:
    movea.l (a3),a3
    tst.l $0012(a3)
    beq.s h0_10A68
h0_10A74:
    btst.b #1,$0010(a3)
    bne.s h0_10A68
h0_10A7C:
    movea.l $0008(a3),a0
    move.l $0016(a3),d1
    move.l d1,-(a0)
    tst.l d0
    bne.s h0_10A68
h0_10A8A:
    move.l d1,d0
    bra.s h0_10A68
h0_10A8E:
    movea.l $01C8(a6),a0
    move.w #$601B,(a0)+
    move.l (a0),d2
    clr.l (a0)+
    move.l d0,(a0)+
    rts
    DC.B    $4e,$75
h0_10AA0:
    tst.l $01C8(a6)
    bne.w h0_109DE
h0_10AA8:
    lea.l $01DA(a6),a3
h0_10AAC:
    tst.l (a3)
    beq.s h0_10AD4
h0_10AB0:
    movea.l (a3),a3
    move.l $0012(a3),d1
    beq.s h0_10AD2
h0_10AB8:
    btst.b #1,$0010(a3)
    bne.s h0_10AD2
h0_10AC0:
    addq.l #8,d1
    bsr.w h0_9146
h0_10AC6:
    move.l a0,$0008(a3)
    move.l a0,$000C(a3)
    adda.l $0012(a3),a0
h0_10AD2:
    bra.s h0_10AAC
h0_10AD4:
    rts
h0_10AD6:
    movea.l $01DE(a6),a1
    btst.b #1,$0010(a1)
    eori #4,ccr
    rts
h0_10AE6:
    tst.l $01C8(a6)
    bne.w h0_10A62
h0_10AEE:
    bsr.w h0_99D0
h0_10AF2:
    bra.w h0_10B36
    DC.B    $4e,$75
h0_10AF8:
    rts
h0_10AFA:
    move.l d2,(a5)+
    rts
h0_10AFE:
    move.w d2,(a5)+
    rts
h0_10B02:
    move.b d2,(a5)+
    rts
h0_10B06:
    lea.l dat_10B12(pc),a0
    rts
h0_10B0C:
    lea.l dat_10B1B(pc),a0
    rts
dat_10B12:
    DC.B    $53,$2d,$72,$65,$63,$6f,$72,$64,$00
dat_10B1B:
    DC.L    $2e6d7800
dat_10B1F:
    DC.B    "HISOFT DEVPAC",0
    DC.B    $00,$12,$d8
    DC.L    $66fc5389
    DC.B    $4e,$75
h0_10B36:
    bsr.w h0_B260
h0_10B3A:
    lea.l $01E2(a6),a2
    tst.b (a2)
    bne.s h0_10B46
h0_10B42:
    lea.l dat_10B1F(pc),a2
h0_10B46:
    moveq.l #0,d6
    moveq.l #0,d5
    movea.l a2,a0
h0_10B4C:
    tst.b (a0)+
    bne.s h0_10B4C
h0_10B50:
    move.l a0,d2
    sub.l a2,d2
    subq.l #1,d2
    bsr.w h0_10BD0
h0_10B5A:
    lea.l $01DA(a6),a3
h0_10B5E:
    movea.l (a3),a3
    move.l $0012(a3),d3
    beq.s h0_10BC8
h0_10B66:
    btst.b #1,$0010(a3)
    bne.s h0_10BC8
h0_10B6E:
    move.l $0016(a3),d2
    btst.b #2,$0010(a3)
    beq.s h0_10B7E
h0_10B7A:
    move.l $001E(a3),d2
h0_10B7E:
    add.l d3,d2
    moveq.l #3,d5
    cmp.l #$1000000,d2
    bcc.s h0_10B96
h0_10B8A:
    moveq.l #2,d5
    cmp.l #$10000,d2
    bcc.s h0_10B96
h0_10B94:
    moveq.l #1,d5
h0_10B96:
    movea.l $0008(a3),a2
    move.l $0016(a3),d6
    btst.b #2,$0010(a3)
    beq.s h0_10BAA
h0_10BA6:
    move.l $001E(a3),d6
h0_10BAA:
    moveq.l #28,d2
    cmp.l d2,d3
    bge.s h0_10BB2
h0_10BB0:
    move.l d3,d2
h0_10BB2:
    sub.l d2,d3
    bsr.s h0_10BD0
h0_10BB6:
    tst.l d3
    bne.s h0_10BAA
h0_10BBA:
    moveq.l #10,d0
    sub.w d5,d0
    move.w d0,d5
    move.l $0016(a3),d6
    moveq.l #0,d2
    bsr.s h0_10BD0
h0_10BC8:
    tst.l (a3)
    bne.s h0_10B5E
h0_10BCC:
    bra.w h0_B246
h0_10BD0:
    cmp.w #$49,d4
    bcc.s h0_10BDA
h0_10BD6:
    bsr.w h0_B246
h0_10BDA:
    moveq.l #48,d1
    add.b d5,d1
    movea.l a4,a0
    move.b #$53,(a4)+
    move.b d1,(a4)+
    addq.w #2,a4
    moveq.l #0,d7
    move.w d5,d1
    add.w d1,d1
    lea.l dat_10C54(pc,d1.w),a1
    move.b (a1)+,d1
    move.l d6,d0
    lsl.l d1,d0
    move.l d0,-(a7)
    move.b (a1)+,d0
    movea.l a7,a1
h0_10BFE:
    move.b (a1)+,d1
    bsr.s h0_10C40
h0_10C02:
    subq.b #1,d0
    bne.s h0_10BFE
h0_10C06:
    addq.l #4,a7
    add.l d2,d6
    tst.l d2
    bra.s h0_10C14
h0_10C0E:
    move.b (a2)+,d1
    bsr.s h0_10C40
h0_10C12:
    subq.l #1,d2
h0_10C14:
    bne.s h0_10C0E
h0_10C16:
    move.l a4,-(a7)
    move.l a4,d1
    sub.l a0,d1
    addq.l #2,d1
    sub.l d1,d4
    lsr.w #1,d1
    subq.w #2,d1
    lea.l $0002(a0),a4
    bsr.s h0_10C40
h0_10C2A:
    movea.l (a7)+,a4
    not.b d7
    move.b d7,d1
    bsr.s h0_10C40
h0_10C32:
    move.b #$D,(a4)+
    subq.l #1,d4
    move.b #$A,(a4)+
    subq.l #1,d4
    rts
h0_10C40:
    add.b d1,d7
    move.w d1,-(a7)
    lsr.w #4,d1
    bsr.s h0_10C4A
h0_10C48:
    move.w (a7)+,d1
h0_10C4A:
    andi.w #15,d1
    move.b dat_10C68(pc,d1.w),(a4)+
    rts
dat_10C54:
    DC.L    $00021002,$08030004,$00010001,$00010004,$08031002
dat_10C68:
    DC.B    $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46
h0_10C78:
    bsr.w h0_99D0
h0_10C7C:
    movea.l $0170(a6),a1
    movea.l (a1),a1
    move.l #$84034,d2
    lea.l dat_10DDE(pc),a2
    bsr.w h0_10DC0
h0_10C90:
    move.l d1,-(a7)
    lea.l dat_10DDE(pc),a2
    movea.l $0178(a6),a1
    movea.l (a1),a1
    move.l #$3900,d2
    bsr.w h0_10DC0
h0_10CA6:
    add.l (a7)+,d1
    addi.l #10,d1
    jsr h0_9146.l
h0_10CB4:
    movea.l a0,a2
    move.w #$0,(a2)
    lea.l $000A(a0),a0
    move.l #$A,$0002(a2)
    lea.l $0002(a2),a3
    movea.l $0170(a6),a1
    movea.l (a1),a1
    move.l #$84034,d2
    bsr.w h0_10D02
h0_10CDA:
    clr.l (a3)
    lea.l $0006(a2),a3
    movea.l $0178(a6),a1
    movea.l (a1),a1
    move.l #$3900,d2
    bsr.w h0_10D02
h0_10CF0:
    move.l a0,d1
    sub.l a2,d1
    movea.l a2,a0
    jsr h0_84F2.l
h0_10CFC:
    bra.w h0_9B42
h0_10D00:
    rts
h0_10D02:
    move.l a1,d1
    beq.s h0_10D00
h0_10D06:
    move.b $000D(a1),d0
    move.l a1,-(a7)
    btst d0,d2
    beq.s h0_10D58
h0_10D10:
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
h0_10D30:
    move.b (a1)+,(a0)+
    dbf.w d0,h0_10D30
h0_10D36:
    movea.l d1,a1
    move.b $000D(a1),d0
    cmp.b #$8,d0
    beq.s h0_10D66
h0_10D42:
    cmp.b #$B,d0
    bcs.s h0_10D58
h0_10D48:
    cmp.b #$E,d0
    bcc.s h0_10D58
h0_10D4E:
    move.b #$D,$000D(a1)
    clr.l $0098(a1)
h0_10D58:
    movea.l (a7),a1
    movea.l (a1),a1
    bsr.s h0_10D02
h0_10D5E:
    movea.l (a7)+,a1
    movea.l $0004(a1),a1
    bra.s h0_10D02
h0_10D66:
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
h0_10D90:
    move.l $0004(a1),d0
    sub.l (a1),d0
    move.l $0008(a1),-(a7)
    movea.l (a1),a1
    subq.w #1,d0
    bmi.s h0_10DA6
h0_10DA0:
    move.b (a1)+,(a0)+
    dbf.w d0,h0_10DA0
h0_10DA6:
    move.l (a7)+,d0
    beq.s h0_10DAE
h0_10DAA:
    movea.l d0,a1
    bra.s h0_10D90
h0_10DAE:
    move.l a0,d0
    sub.l a2,d0
    movea.l (a7)+,a1
    move.l d0,(a1)
    btst #0,d0
    beq.s h0_10DBE
h0_10DBC:
    addq.w #1,a0
h0_10DBE:
    bra.s h0_10D58
h0_10DC0:
    moveq.l #0,d1
    move.l a1,d0
    beq.s h0_10DDC
h0_10DC6:
    move.l a1,-(a7)
    movea.l (a1),a1
    bsr.s h0_10DC0
h0_10DCC:
    movea.l (a7),a1
    move.l d1,-(a7)
    movea.l $0004(a1),a1
    bsr.s h0_10DC0
h0_10DD6:
    add.l (a7)+,d1
    movea.l (a7)+,a1
    jsr (a2)                            ; CANDIDATE: indirect_call index unresolved
h0_10DDC:
    rts
dat_10DDE:
    DC.B    $10,$29 ; VIOLATION: orphaned code island at $10DDE is not reached from known entrypoints
    DC.L    $000d0102,$6750b03c,$00086714,$b03c000b,$6532b03c,$000e642c,$06810000,$00b24e75
    DC.L    $2f090681,$00000010,$22690008,$d2a90004,$92912029,$00086704,$224060f0 ; VIOLATION: orphaned code island at $10E00 is not reached from known entrypoints
    DC.L    $52810881,$0000225f,$70001029,$00160680,$00000018,$08800000,$d2804e75 ; VIOLATION: orphaned code island at $10E1C is not reached from known entrypoints
h0_10E38:
    move.l d4,d3
    bra.s h0_10E72
h0_10E3C:
    movea.l $507C(a6),a0
h0_10E40:
    tst.b (a0)
    beq.s h0_10E64
h0_10E44:
    lea.l $5084(a6),a1
h0_10E48:
    move.b (a0)+,(a1)+
    bne.s h0_10E48
h0_10E4C:
    move.l a0,-(a7)
    lea.l $5084(a6),a0
    lea.l dat_975C(pc),a2
    jsr h0_46BE.l
h0_10E5C:
    bsr.w h0_10E66
h0_10E60:
    movea.l (a7)+,a0
    bra.s h0_10E40
h0_10E64:
    rts
h0_10E66:
    jsr h0_BF9A.l
h0_10E6C:
    bne.w h0_10EEE
h0_10E70:
    move.l d2,d1
h0_10E72:
    move.l d1,-(a7)
    jsr h0_9146.l
h0_10E7A:
    move.l (a7),d1
    move.l a0,(a7)
    move.l d3,-(a7)
    bsr.w h0_BFB2
h0_10E84:
    move.l (a7)+,d3
    bsr.w h0_BFAE
h0_10E8A:
    movea.l (a7)+,a2
    move.l a2,d2
    move.w (a2),d0
    cmp.w #$0,d0
    bne.s h0_10EF6
h0_10E96:
    movem.l a3-a5,-(a7)
    movea.l $0002(a2),a0
    movea.l $0170(a6),a2
    bsr.s h0_10EBE
h0_10EA4:
    movea.l d2,a0
    movea.l $0006(a0),a0
    movea.l $0178(a6),a2
    bsr.s h0_10EBE
h0_10EB0:
    movem.l (a7)+,a3-a5
h0_10EB4:
    rts
h0_10EB6:
    move.l (a0),d0
    beq.s h0_10EB4
h0_10EBA:
    clr.l (a0)
    movea.l d0,a0
h0_10EBE:
    adda.l d2,a0
    move.l d2,-(a7)
    jsr h0_0BB8.l
h0_10EC8:
    movem.l (a7)+,d2
    beq.s h0_10EB6
h0_10ECE:
    move.l a0,(a1)
    move.b $000D(a0),d1
    cmp.b #$8,d1
    bne.s h0_10EB6
h0_10EDA:
    add.l d2,$0008(a0)
    movea.l $0008(a0),a1
    add.l d2,$0004(a1)
    add.l d2,(a1)
    bra.s h0_10EB6
    DC.B    $70,$05,$60,$02 ; VIOLATION: orphaned code island at $10EEA is not reached from known entrypoints
h0_10EEE:
    moveq.l #27,d0
h0_10EF0:
    jmp h0_853E.l
h0_10EF6:
    moveq.l #103,d0
    bra.s h0_10EF0
    SECTION DATA,data

