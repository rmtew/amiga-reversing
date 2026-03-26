; Generated disassembly -- vasm Motorola syntax
; Source: bin\GenAm
; 64920 bytes, 486 entities, 2840 blocks

; OS function argument constants
ACCESS_READ	EQU	-2
MEMF_PUBLIC	EQU	1
MODE_OLDFILE	EQU	1005
OFFSET_BEGINNING	EQU	-1
OFFSET_CURRENT	EQU	0
SIGBREAKF_CTRL_C	EQU	4096

; App memory offsets (base register A6)
app_freemem_memoryblock	EQU	-2
app_open_file	EQU	2390
app_dos_base	EQU	3286
app_output_file	EQU	3290
app_subtime_src	EQU	4264
app_subtime_dest	EQU	4272
app_timer_device_iorequest	EQU	4280

; Absolute symbols
AbsExecBase	EQU	$4

    INCLUDE "devices/timer.i"
    INCLUDE "dos/dos_lib.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/io.i"
    INCLUDE "exec/libraries.i"

    section code,code

entry_point:
    bra.s loc_0036
    dc.b    $94,$4f
    dc.l    $7a3085c2
    dc.b    "$VER: GenAm 3.18 (2.8.94)",0
    dc.b    "(C) HiSoft 1985-1997"
loc_0036:
    jsr init_app
loc_003c:
    jsr sub_9106
loc_0042:
    move.l sp,564(a6) ; app+$234
    subq.l #4,564(a6) ; app+$234
    movea.l #sub_a664,a0
    lea app_freemem_memoryblock(a6),a1
    moveq #63,d0
loc_0056:
    move.l (a0)+,(a1)+
    dbf d0,loc_0056
loc_005c:
    lea 254(a6),a0 ; app+$FE
    move.w #$94,d0
loc_0064:
    clr.w (a0)+
    dbf d0,loc_0064
loc_006a:
    sf 570(a6) ; app+$23A
    sf 568(a6) ; app+$238
    clr.b 1273(a6) ; app+$4F9
    jsr sub_90a8
loc_007c:
    lea 584(a6),a1 ; app+$248
    clr.l (a1)
    move.l a1,370(a6) ; app+$172
    lea 580(a6),a1 ; app+$244
    clr.l (a1)
    move.l a1,362(a6) ; app+$16A
    bsr.w sub_6e42
loc_0094:
    clr.b 1736(a6) ; app+$6C8
    lea app_timer_device_iorequest+IO_DATA(a6),a3
    bsr.w sub_4668
loc_00a0:
    lea 2098(a6),a3 ; app+$832
    bsr.w sub_4668
loc_00a8:
    clr.b 2016(a6) ; app+$7E0
    lea 2208(a6),a0 ; app+$8A0
    move.l a0,2368(a6) ; app+$940
    clr.w 596(a6) ; app+$254
    move.b #$64,570(a6) ; app+$23A
    jsr open_device
loc_00c4:
    bne.w loc_046e
loc_00c8:
    clr.b 1934(a6) ; app+$78E
    st 2112(a6) ; app+$840
    sf 2113(a6) ; app+$841
    sf 2114(a6) ; app+$842
    st 2115(a6) ; app+$843
    jsr sub_ab0e
loc_00e2:
    sf 258(a6) ; app+$102
    jsr sub_ab00
loc_00ec:
    sf 258(a6) ; app+$102
    lea 2016(a6),a0 ; app+$7E0
    tst.b (a0)
    beq.s loc_0110
loc_00f8:
    jsr sub_b0ac
loc_00fe:
    beq.w loc_0174
loc_0102:
    move.l a0,560(a6) ; app+$230
    jsr sub_ab08
loc_010c:
    bne.w loc_0170
loc_0110:
    jsr sub_ab2a
loc_0116:
    tst.b 1273(a6) ; app+$4F9
    beq.w loc_0178
loc_011e:
    tst.b 295(a6) ; app+$127
    bne.s loc_012c
loc_0124:
    moveq #0,d0
    jsr sub_8e7a
loc_012c:
    jsr sub_4590
loc_0132:
    bne.w loc_016c
loc_0136:
    jsr sub_fcda
loc_013c:
    sf 570(a6) ; app+$23A
    lea 2208(a6),a0 ; app+$8A0
    move.l a0,2368(a6) ; app+$940
    clr.b 266(a6) ; app+$10A
    lea 1268(a6),a0 ; app+$4F4
    jsr sub_8856
loc_0156:
    beq.s loc_01c8
loc_0158:
    moveq #10,d0
    jsr sub_8e7a
loc_0160:
    bsr.s sub_0184
loc_0162:
    move.b #$64,570(a6) ; app+$23A
    bra.w loc_046e
loc_016c:
    moveq #26,d0
    bra.s loc_017a
loc_0170:
    moveq #24,d0
    bra.s loc_017a
loc_0174:
    moveq #25,d0
    bra.s loc_017a
loc_0178:
    moveq #23,d0
loc_017a:
    jsr sub_8e7a
loc_0180:
    bra.w loc_046e
sub_0184:
    lea 1268(a6),a0 ; app+$4F4
    moveq #0,d0
    move.b 5(a0),d0
    subq.w #2,d0
    bmi.s loc_01a0
loc_0192:
    addq.w #6,a0
loc_0194:
    move.b (a0)+,d1
    jsr sub_8e98
loc_019c:
    dbf d0,loc_0194
loc_01a0:
    jmp sub_8e8c
sub_01a6:
    move.w 536(a6),-(sp) ; app+$218
    clr.w 536(a6) ; app+$218
    jsr sub_ab00
loc_01b4:
    bne.s loc_0178
loc_01b6:
    jsr sub_ab08
loc_01bc:
    bne.s loc_0170
loc_01be:
    move.w (sp)+,536(a6) ; app+$218
    sf 258(a6) ; app+$102
    rts
loc_01c8:
    tst.l 382(a6) ; app+$17E
    bne.s loc_01d2
loc_01ce:
    moveq #29,d0
    bra.s loc_017a
loc_01d2:
    movea.l 1268(a6),a1 ; app+$4F4
    move.b 1273(a6),d0 ; app+$4F9
    subq.b #1,d0
loc_01dc:
    move.l a1,d2
    move.b d0,d3
loc_01e0:
    subq.b #1,d0
    bcs.s loc_01fa
loc_01e4:
    move.b (a1)+,d1
    cmp.b #$5c,d1
    beq.s loc_01dc
loc_01ec:
    cmp.b #$2f,d1
    beq.s loc_01dc
loc_01f2:
    cmp.b #$3a,d1
    beq.s loc_01dc
loc_01f8:
    bra.s loc_01e0
loc_01fa:
    lea 1406(a6),a0 ; app+$57E
    movea.l d2,a1
    move.b d3,(a0)+
loc_0202:
    beq.s loc_020a
loc_0204:
    move.b (a1)+,(a0)+
    subq.b #1,d3
    bra.s loc_0202
loc_020a:
    move.b #$a,(a0)
    bsr.w sub_0496
loc_0212:
    sf 2112(a6) ; app+$840
    st 2113(a6) ; app+$841
    st 2114(a6) ; app+$842
    jsr sub_ab0e
loc_0224:
    sf 258(a6) ; app+$102
    lea 1448(a6),a0 ; app+$5A8
    move.l a0,588(a6) ; app+$24C
    tst.b 295(a6) ; app+$127
    bne.s loc_024a
loc_0236:
    moveq #27,d0
    jsr sub_8e7a
loc_023e:
    bsr.w sub_0184
loc_0242:
    moveq #1,d0
    jsr sub_8e7a
loc_024a:
    move.b 2388(a6),2389(a6) ; app+$954
    sf 2112(a6) ; app+$840
    st 2113(a6) ; app+$841
    st 2114(a6) ; app+$842
    sf 2115(a6) ; app+$843
    bsr.w sub_01a6
loc_0264:
    bsr.w loc_06ac
loc_0268:
    bne.s loc_02b0
loc_026a:
    move.l sp,564(a6) ; app+$234
    subq.l #4,564(a6) ; app+$234
    sf 2116(a6) ; app+$844
    bsr.w loc_09c8
loc_027a:
    bsr.w loc_07f8
loc_027e:
    tst.b 2116(a6) ; app+$844
    beq.s loc_0298
loc_0284:
    sf 2112(a6) ; app+$840
    st 2113(a6) ; app+$841
    sf 2114(a6) ; app+$842
    sf 2115(a6) ; app+$843
    bsr.w sub_01a6
loc_0298:
    move.l sp,564(a6) ; app+$234
    subq.l #4,564(a6) ; app+$234
loc_02a0:
    bsr.w loc_06ac
loc_02a4:
    bne.s loc_02b0
loc_02a6:
    bsr.w loc_09c8
loc_02aa:
    bsr.w loc_07f8
loc_02ae:
    bra.s loc_02a0
loc_02b0:
    tst.b 268(a6) ; app+$10C
    bne.w loc_03b0
loc_02b8:
    bsr.w sub_0590
loc_02bc:
    sf 2389(a6) ; app+$955
    tst.b 295(a6) ; app+$127
    bne.s loc_02ce
loc_02c6:
    moveq #2,d0
    jsr sub_8e7a
loc_02ce:
    tst.b 277(a6) ; app+$115
    bgt.w loc_06a4
loc_02d6:
    move.b 2388(a6),2389(a6) ; app+$954
    jsr sub_ab50
loc_02e2:
    st 568(a6) ; app+$238
    bsr.w sub_0496
loc_02ea:
    tst.b 2388(a6) ; app+$954
    beq.s loc_02f8
loc_02f0:
    sf 2106(a6) ; app+$83A
    st 256(a6) ; app+$100
loc_02f8:
    lea 2098(a6),a3 ; app+$832
    bsr.w sub_4678
loc_0300:
    sf 2112(a6) ; app+$840
    st 2113(a6) ; app+$841
    sf 2114(a6) ; app+$842
    st 2115(a6) ; app+$843
    jsr sub_ab0e
loc_0316:
    sf 2113(a6) ; app+$841
    jsr sub_ab00
loc_0320:
    jsr sub_ab08
loc_0326:
    sf 258(a6) ; app+$102
    jsr sub_ab2a
loc_0330:
    lea 1268(a6),a0 ; app+$4F4
    clr.b 266(a6) ; app+$10A
    jsr sub_8856
loc_033e:
    beq.s loc_0346
loc_0340:
    jmp loc_846e
loc_0346:
    st 2113(a6) ; app+$841
    sf 2115(a6) ; app+$843
    bsr.w sub_01a6
loc_0352:
    bsr.w loc_06ac
loc_0356:
    bne.s loc_0386
loc_0358:
    sf 2116(a6) ; app+$844
    bsr.w loc_09c8
loc_0360:
    bsr.w loc_08dc
loc_0364:
    tst.b 2116(a6) ; app+$844
    beq.s loc_0376
loc_036a:
    bsr.w sub_01a6
loc_036e:
    move.l sp,564(a6) ; app+$234
    subq.l #4,564(a6) ; app+$234
loc_0376:
    bsr.w loc_06ac
loc_037a:
    bne.s loc_0386
loc_037c:
    bsr.w loc_09c8
loc_0380:
    bsr.w loc_08dc
loc_0384:
    bra.s loc_0376
loc_0386:
    bsr.w sub_057a
loc_038a:
    bsr.w sub_79cc
loc_038e:
    bsr.w sub_79da
loc_0392:
    jsr sub_9898
loc_0398:
    tst.b 255(a6) ; app+$FF
    beq.s loc_03a4
loc_039e:
    jsr sub_8f60
loc_03a4:
    tst.b 265(a6) ; app+$109
    beq.s loc_03b0
loc_03aa:
    jsr sub_fb16
loc_03b0:
    sf 2389(a6) ; app+$955
    jsr sub_9158
loc_03ba:
    jsr sub_98ae
loc_03c0:
    jsr sub_8a06
loc_03c6:
    tst.b 295(a6) ; app+$127
    beq.s loc_03d4
loc_03cc:
    move.b 268(a6),d1 ; app+$10C
    beq.w loc_046e
loc_03d4:
    jsr sub_8e8c
loc_03da:
    moveq #0,d1
    move.b 268(a6),d1 ; app+$10C
    jsr sub_8f04
loc_03e6:
    moveq #3,d0
    cmpi.b #$1,268(a6) ; app+$10C
    bne.s loc_03f2
loc_03f0:
    addq.b #1,d0
loc_03f2:
    jsr sub_8e7a
loc_03f8:
    move.l 544(a6),d1 ; app+$220
    subq.l #1,d1
    jsr sub_8f04
loc_0404:
    moveq #5,d0
    jsr sub_8e7a
loc_040c:
    move.l 548(a6),d1 ; app+$224
    jsr sub_8f04
loc_0416:
    moveq #12,d0
    jsr sub_8e7a
loc_041e:
    jsr gen_symbol
loc_0424:
    moveq #22,d0
    tst.b 274(a6) ; app+$112
    bne.s loc_0436
loc_042c:
    moveq #18,d0
    tst.b 276(a6) ; app+$114
    beq.s loc_0436
loc_0434:
    moveq #17,d0
loc_0436:
    jsr sub_8e7a
loc_043c:
    moveq #19,d0
    jsr sub_8e7a
loc_0444:
    moveq #0,d1
    move.w 402(a6),d1 ; app+$192
    beq.s loc_046e
loc_044c:
    jsr sub_8f04
loc_0452:
    moveq #13,d0
    jsr sub_8e7a
loc_045a:
    moveq #0,d0
    move.w 404(a6),d1 ; app+$194
    jsr sub_8f04
loc_0466:
    moveq #14,d0
    jsr sub_8e7a
loc_046e:
    jsr sub_916a
loc_0474:
    jsr call_closedevice
loc_047a:
    move.l 394(a6),d3 ; app+$18A
    beq.s loc_048a
loc_0480:
    jsr sub_aff2
loc_0486:
    clr.l 394(a6) ; app+$18A
loc_048a:
    jsr sub_90f2
loc_0490:
    jsr cleanup_app
sub_0496:
    moveq #0,d0
    move.w d0,536(a6) ; app+$218
    move.l d0,548(a6) ; app+$224
    move.l d0,544(a6) ; app+$220
    move.l d0,572(a6) ; app+$23C
    move.l d0,346(a6) ; app+$15A
    move.l d0,354(a6) ; app+$162
    move.l d0,398(a6) ; app+$18E
    move.w d0,2174(a6) ; app+$87E
    move.w d0,2176(a6) ; app+$880
    move.l d0,2178(a6) ; app+$882
    move.b d0,262(a6) ; app+$106
    move.b d0,274(a6) ; app+$112
    move.b d0,2107(a6) ; app+$83B
    move.b d0,289(a6) ; app+$121
    sf 291(a6) ; app+$123
    move.b d0,290(a6) ; app+$122
    sf 292(a6) ; app+$124
    sf 300(a6) ; app+$12C
    st 302(a6) ; app+$12E
    sf 301(a6) ; app+$12D
    move.w #$200,304(a6) ; app+$130
    move.b d0,306(a6) ; app+$132
    move.b d0,307(a6) ; app+$133
    move.b #$1,2140(a6) ; app+$85C
    move.b #$ff,2156(a6) ; app+$86C
    sf 293(a6) ; app+$125
    move.b d0,303(a6) ; app+$12F
    move.w d0,270(a6) ; app+$10E
    move.w #$ffff,272(a6) ; app+$110
    move.b d0,263(a6) ; app+$107
    move.l d0,2192(a6) ; app+$890
    move.w d0,2200(a6) ; app+$898
    move.w d0,2202(a6) ; app+$89A
    move.l d0,2122(a6) ; app+$84A
    moveq #1,d0
    move.l d0,2118(a6) ; app+$846
    st 2106(a6) ; app+$83A
    st 261(a6) ; app+$105
    move.w #$80,542(a6) ; app+$21E
    jsr sub_8d82
loc_0542:
    sf 276(a6) ; app+$114
    sf 277(a6) ; app+$115
    sf 280(a6) ; app+$118
    sf 279(a6) ; app+$117
    sf 257(a6) ; app+$101
    sf 281(a6) ; app+$119
    sf 285(a6) ; app+$11D
    st 286(a6) ; app+$11E
    st 287(a6) ; app+$11F
    sf 294(a6) ; app+$126
    move.b #$2e,278(a6) ; app+$116
    move.b #$1,264(a6) ; app+$108
    bra.w loc_78e0
sub_057a:
    tst.w 2174(a6) ; app+$87E
    bne.s loc_0582
loc_0580:
    rts
loc_0582:
    move.w #$ffff,536(a6) ; app+$218
    moveq #50,d0
    jmp loc_8486
sub_0590:
    bsr.s sub_057a
loc_0592:
    bsr.w sub_79cc
loc_0596:
    bsr.w sub_79da
loc_059a:
    jsr sub_8a06
loc_05a0:
    bsr.s sub_05c2
loc_05a2:
    jsr sub_8a5a
loc_05a8:
    cmpi.w #$3,540(a6) ; app+$21C
    bne.s loc_05b6
loc_05b0:
    jsr sub_a3f4
loc_05b6:
    jsr sub_9682
loc_05bc:
    clr.l 378(a6) ; app+$17A
    rts
sub_05c2:
    movea.l 370(a6),a3 ; app+$172
    movea.l (a3),a3
    bsr.s sub_05cc
loc_05ca:
    rts
sub_05cc:
    tst.l (a3)
    beq.s loc_05d8
loc_05d0:
    move.l a3,-(sp)
    movea.l (a3),a3
    bsr.s sub_05cc
loc_05d6:
    movea.l (sp)+,a3
loc_05d8:
    cmpi.b #$9,13(a3)
    bne.s loc_05e6
loc_05e0:
    movea.l 8(a3),a2
    bsr.s sub_05f8
loc_05e6:
    tst.l 4(a3)
    beq.s loc_05f6
loc_05ec:
    move.l a3,-(sp)
    movea.l 4(a3),a3
    bsr.s sub_05cc
loc_05f4:
    movea.l (sp)+,a3
loc_05f6:
    rts
sub_05f8:
    tst.l (a2)
    beq.s loc_0604
loc_05fc:
    move.l a2,-(sp)
    movea.l (a2),a2
    bsr.s sub_05f8
loc_0602:
    movea.l (sp)+,a2
loc_0604:
    clr.l 8(a2)
    tst.l 4(a2)
    beq.s loc_0618
loc_060e:
    move.l a2,-(sp)
    movea.l 4(a2),a2
    bsr.s sub_05f8
loc_0616:
    movea.l (sp)+,a2
loc_0618:
    rts
sub_061a:
    tst.l 2192(a6) ; app+$890
    bne.s loc_063e
loc_0620:
    tst.b 257(a6) ; app+$101
    bne.s loc_0662
loc_0626:
    movea.l 382(a6),a1 ; app+$17E
    movea.l 158(a1),a0
    cmpa.l 162(a1),a0
    bcc.s loc_067e
loc_0634:
    move.b (a0),d0
    cmp.b d0,d0
    rts
hint_063a:
; --- unverified ---
    moveq #-1,d0
    rts
loc_063e:
    tst.b 257(a6) ; app+$101
    beq.s loc_064e
loc_0644:
    move.w 2200(a6),d0 ; app+$898
    cmp.w 2202(a6),d0 ; app+$89A
    bhi.s loc_0662
loc_064e:
    movea.l 2192(a6),a1 ; app+$890
    movea.l 2196(a6),a0 ; app+$894
    cmpa.l 4(a1),a0
    bne.s loc_0634
loc_065c:
    movea.l 8(a1),a0
    bra.s loc_0634
loc_0662:
    movea.l 2178(a6),a2 ; app+$882
    movea.l 4(a2),a1
    movea.l 16(a2),a0
    cmpa.l 4(a1),a0
    bne.s loc_0634
loc_0674:
    movea.l 8(a1),a1
    movea.l 0(a1),a0
    bra.s loc_0634
loc_067e:
    moveq #70,d0
    jmp loc_846e
    dc.b    $4a,$fb
    dc.b    "include_longmac",0
sub_0698:
    tst.b 277(a6) ; app+$115
    beq.w loc_06c6
loc_06a0:
    bpl.s loc_06a4
loc_06a2:
    rts
loc_06a4:
    moveq #79,d0
    jmp loc_846e
loc_06ac:
    tst.b 277(a6) ; app+$115
    bne.s loc_06a0
loc_06b2:
    addq.l #1,544(a6) ; app+$220
    tst.b 257(a6) ; app+$101
    bne.w loc_702a
loc_06be:
    tst.l 2192(a6) ; app+$890
    bne.w sub_743c
loc_06c6:
    moveq #10,d1
    move.w #$fe,d2
    addq.w #1,536(a6) ; app+$218
loc_06d0:
    movea.l 382(a6),a1 ; app+$17E
    movea.l 158(a1),a4
    cmpa.l 162(a1),a4
    bcc.w loc_0754
loc_06e0:
    move.w #$fc,d0
    moveq #10,d2
    move.l a4,576(a6) ; app+$240
    movea.l a4,a2
loc_06ec:
    cmp.b (a2)+,d2
    dbeq d0,loc_06ec
loc_06f2:
    beq.s loc_070c
loc_06f4:
    cmpa.l 162(a1),a2
    bhi.s loc_071a
loc_06fa:
    move.b #$2a,-(a2)
    move.b #$a,-1(a2)
    move.l a2,158(a1)
    moveq #0,d0
    rts
loc_070c:
    cmpa.l 162(a1),a2
    bhi.s loc_071a
loc_0712:
    move.l a2,158(a1)
    moveq #0,d0
    rts
loc_071a:
    move.l 166(a1),d1
    movea.l 8(a1),a2
    adda.l d1,a2
    cmpa.l 162(a1),a2
    bne.s loc_0776
loc_072a:
    move.l 162(a1),d2
    sub.l a4,d2
    beq.s loc_0754
loc_0732:
    move.l d2,-(sp)
    subq.l #1,d2
    movea.l a4,a0
    movea.l 8(a1),a2
    move.l a2,158(a1)
loc_0740:
    move.b (a0)+,(a2)+
    dbf d2,loc_0740
loc_0746:
    move.l 166(a1),d1
    sub.l (sp)+,d1
    jsr sub_89b0
loc_0752:
    bra.s loc_076c
loc_0754:
    movea.l 8(a1),a2
    move.l a2,158(a1)
    adda.l 166(a1),a2
    cmpa.l 162(a1),a2
    bne.s loc_0776
loc_0766:
    jsr sub_89ba
loc_076c:
    beq.w loc_06d0
loc_0770:
    jmp loc_846e
loc_0776:
    move.w 156(a1),536(a6) ; app+$218
    clr.w 156(a1)
    tst.b 308(a6) ; app+$134
    beq.s loc_0792
loc_0786:
    tst.b 568(a6) ; app+$238
    beq.s loc_0792
loc_078c:
    move.b #$fe,14(a1)
loc_0792:
    cmpi.b #$c,13(a1)
    beq.s loc_07ae
loc_079a:
    move.l 152(a1),d2
    beq.s loc_07ae
loc_07a0:
    move.l a1,-(sp)
    jsr call_close_afb8
loc_07a8:
    movea.l (sp)+,a1
    clr.l 152(a1)
loc_07ae:
    move.l 16(a1),382(a6) ; app+$17E
    bne.w sub_0698
loc_07b8:
    moveq #-1,d0
    rts
hint_07bc:
; --- unverified ---
    st 275(a6) ; app+$113
    tst.b 568(a6) ; app+$238
    beq.s hint_07da
hint_07c6:
; --- unverified ---
    cmp.b #$2b,d1
    beq.s hint_07e4
hint_07cc:
; --- unverified ---
    cmp.b #$2d,d1
    beq.s hint_07de
hint_07d2:
; --- unverified ---
    moveq #10,d1
    st 256(a6) ; app+$100
    rts
hint_07da:
; --- unverified ---
    moveq #10,d1
    rts
hint_07de:
; --- unverified ---
    subq.b #1,2106(a6) ; app+$83A
    bra.s hint_07e8
hint_07e4:
    dc.b    $52,$2e,$08,$3a
hint_07e8:
    dc.b    $5a,$ee,$01,$00,$12,$1c
sub_07ee:
    rts
sub_07f0:
    tst.b 568(a6) ; app+$238
    bne.w loc_08dc
loc_07f8:
    tst.b 297(a6) ; app+$129
    beq.w loc_08c6
loc_0800:
    tst.l 386(a6) ; app+$182
    beq.w loc_08c6
loc_0808:
    cmpi.b #$1,264(a6) ; app+$108
    bne.s sub_07ee
loc_0810:
    move.l 382(a6),d0 ; app+$17E
    beq.s sub_07ee
loc_0816:
    move.b 326(a6),d6 ; app+$146
    movea.l d0,a0
    move.l 174(a0),d0
    beq.s loc_082a
loc_0822:
    movea.l d0,a0
    cmp.b 4(a0),d6
    beq.s loc_087a
loc_082a:
    movea.l 382(a6),a0 ; app+$17E
    lea 170(a0),a0
loc_0832:
    move.l (a0),d0
    beq.s loc_0842
loc_0836:
    movea.l d0,a0
    cmp.b 4(a0),d6
    beq.s loc_0872
loc_083e:
    lea (a0),a0
    bra.s loc_0832
loc_0842:
    move.l a0,-(sp)
    moveq #32,d1
    jsr sub_90ba
loc_084c:
    movea.l (sp)+,a1
    move.l a0,(a1)
    clr.l (a0)
    move.b d6,4(a0)
    move.l #$ffffffff,6(a0)
    clr.l 10(a0)
    clr.w 18(a0)
    clr.l 14(a0)
    clr.l 20(a0)
    clr.l 24(a0)
loc_0872:
    movea.l 382(a6),a1 ; app+$17E
    move.l a0,174(a1)
loc_087a:
    move.l 572(a6),d0 ; app+$23C
    sub.l 386(a6),d0 ; app+$182
    cmp.l 6(a0),d0
    beq.s loc_08c6
loc_0888:
    moveq #0,d1
    move.w 536(a6),d1 ; app+$218
    cmp.l 10(a0),d1
    beq.s loc_08c6
loc_0894:
    tst.b 298(a6) ; app+$12A
    beq.s loc_08ba
loc_089a:
    addq.w #1,18(a0)
    lea 10(a0),a1
    move.l d0,-(sp)
    move.l d1,d0
    jsr sub_8ada
loc_08ac:
    move.l (sp)+,d0
    lea 6(a0),a1
    jsr sub_8ada
loc_08b8:
    bra.s loc_08c6
loc_08ba:
    addq.l #8,24(a0)
    move.l d0,6(a0)
    move.l d1,10(a0)
loc_08c6:
    tst.b 258(a6) ; app+$102
    bne.w loc_09a4
loc_08ce:
    tst.b 538(a6) ; app+$21A
    beq.w loc_0996
loc_08d6:
    bra.w loc_09a4
sub_08da:
    rts
loc_08dc:
    tst.b 297(a6) ; app+$129
    beq.w loc_0972
loc_08e4:
    tst.l 386(a6) ; app+$182
    beq.w loc_0972
loc_08ec:
    cmpi.b #$1,264(a6) ; app+$108
    bne.s loc_0972
loc_08f4:
    move.l 382(a6),d0 ; app+$17E
    beq.s sub_08da
loc_08fa:
    movea.l d0,a0
    move.b 326(a6),d6 ; app+$146
    movea.l 174(a0),a0
    cmp.b 4(a0),d6
    beq.s loc_091e
loc_090a:
    movea.l 382(a6),a1 ; app+$17E
    lea 170(a1),a0
loc_0912:
    movea.l (a0),a0
    cmp.b 4(a0),d6
    bne.s loc_0912
loc_091a:
    move.l a0,174(a1)
loc_091e:
    move.l 572(a6),d0 ; app+$23C
    sub.l 386(a6),d0 ; app+$182
    cmp.l 6(a0),d0
    beq.s loc_0972
loc_092c:
    moveq #0,d1
    move.w 536(a6),d1 ; app+$218
    cmp.l 10(a0),d1
    beq.s loc_0972
loc_0938:
    tst.b 298(a6) ; app+$12A
    beq.s loc_095e
loc_093e:
    lea 10(a0),a1
    move.l d0,-(sp)
    move.l d1,d0
    jsr sub_8b10
loc_094c:
    move.l a1,20(a0)
    move.l (sp)+,d0
    lea 6(a0),a1
    jsr sub_8b10
loc_095c:
    bra.s loc_096e
loc_095e:
    movea.l 20(a0),a1
    move.l d0,6(a0)
    move.l d1,10(a0)
    move.l d1,(a1)+
    move.l d0,(a1)+
loc_096e:
    move.l a1,20(a0)
loc_0972:
    tst.b 258(a6) ; app+$102
    bne.s loc_09a4
loc_0978:
    tst.b 256(a6) ; app+$100
    beq.s loc_0996
loc_097e:
    tst.b 275(a6) ; app+$113
    bne.s loc_0996
loc_0984:
    tst.b 257(a6) ; app+$101
    beq.s loc_09a4
loc_098a:
    tst.b 280(a6) ; app+$118
    bne.s loc_09a4
loc_0990:
    tst.b 279(a6) ; app+$117
    bne.s loc_09a4
loc_0996:
    sf 275(a6) ; app+$113
    clr.b 2107(a6) ; app+$83B
    sf 280(a6) ; app+$118
    rts
loc_09a4:
    sf 258(a6) ; app+$102
    jsr sub_92a0
loc_09ae:
    bra.s loc_0996
sub_09b0:
; --- unverified ---
    st 275(a6) ; app+$113
    moveq #10,d1
    tst.b 568(a6) ; app+$238
    beq.s hint_09c4
hint_09bc:
    dc.b    $51,$ee,$01,$00,$50,$ee,$08,$3a
hint_09c4:
; --- unverified ---
    rts
sub_09c6:
    rts
loc_09c8:
    movea.l 588(a6),a5 ; app+$24C
    move.l a5,592(a6) ; app+$250
    clr.l 386(a6) ; app+$182
    sf 269(a6) ; app+$10D
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s sub_09c6
loc_09e0:
    cmp.b #$9,d1
    beq.s loc_09ec
loc_09e6:
    cmp.b #$20,d1
    bne.s loc_0a08
loc_09ec:
    clr.l 1000(a6) ; app+$3E8
    bra.w loc_0a2a
loc_09f4:
    cmp.b #$3b,d1
    beq.w loc_0c44
loc_09fc:
    cmp.b #$2a,d1
    beq.w loc_0c44
loc_0a04:
    bra.w loc_8432
loc_0a08:
    st d2
    lea 1000(a6),a0 ; app+$3E8
    clr.b 4(a0)
    bsr.w sub_76b8
loc_0a16:
    bne.s loc_09f4
loc_0a18:
    cmp.b #$3a,d1
    bne.s loc_0a2c
loc_0a1e:
    move.b (a4)+,d1
    cmp.b #$3a,d1
    bne.s loc_0a2c
loc_0a26:
    st 1004(a6) ; app+$3EC
loc_0a2a:
    move.b (a4)+,d1
loc_0a2c:
    cmp.b #$9,d1
    beq.s loc_0a2a
loc_0a32:
    cmp.b #$20,d1
    beq.s loc_0a2a
loc_0a38:
    cmp.b #$3d,d1
    beq.w loc_748a
loc_0a40:
    subq.l #1,a4
    move.l a4,-(sp)
    moveq #0,d2
    movea.l #sub_b21e,a0
    movea.l #dat_cd3c,a1
    movea.l #dat_ba08,a2
    moveq #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w 0(a0,d2.w),d1
    cmp.w 0(a1,d1.w),d2
    bne.s loc_0ab2
loc_0a68:
    move.w 0(a2,d1.w),d2
    bmi.s loc_0ae8
loc_0a6e:
    moveq #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w 0(a0,d2.w),d1
    cmp.w 0(a1,d1.w),d2
    bne.s loc_0ab2
loc_0a7e:
    move.w 0(a2,d1.w),d2
    bmi.s loc_0ae8
loc_0a84:
    moveq #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w 0(a0,d2.w),d1
    cmp.w 0(a1,d1.w),d2
    bne.s loc_0ab2
loc_0a94:
    move.w 0(a2,d1.w),d2
    bmi.s loc_0ae8
loc_0a9a:
    moveq #0,d1
    move.b (a4)+,d1
    add.w d1,d1
    add.w 0(a0,d2.w),d1
    cmp.w 0(a1,d1.w),d2
    bne.s loc_0ab2
loc_0aaa:
    move.w 0(a2,d1.w),d2
    bpl.s loc_0a9a
loc_0ab0:
    bra.s loc_0ae8
loc_0ab2:
    move.w d2,d1
    add.w d1,d1
    add.w d1,d2
    movea.l #sub_e070,a0
    adda.w d2,a0
    tst.w 2(a0)
    beq.s loc_0ae8
loc_0ac6:
    move.b -1(a4),d1
    cmp.b #$2e,d1
    beq.s loc_0ae2
loc_0ad0:
    cmp.b #$a,d1
    beq.s loc_0ae2
loc_0ad6:
    cmp.b #$9,d1
    beq.s loc_0ae2
loc_0adc:
    cmp.b #$20,d1
    bne.s loc_0ae8
loc_0ae2:
    move.l (sp)+,d2
    bra.w loc_74a2
loc_0ae8:
    movea.l (sp)+,a4
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.w loc_0c44
loc_0af4:
    cmp.b #$3b,d1
    beq.w loc_0c44
loc_0afc:
    cmp.b #$2a,d1
    beq.w loc_0c44
loc_0b04:
    lea 866(a6),a0 ; app+$362
    bsr.w sub_7680
loc_0b0c:
    bne.w loc_8432
loc_0b10:
    movea.l 370(a6),a2 ; app+$172
    move.l a1,d4
    movem.l d2/a3-a5,-(sp)
    bsr.w sub_0b88
loc_0b1e:
    movem.l (sp)+,d2/a3-a5
    beq.w loc_6e5c
loc_0b26:
    movea.l d4,a4
    move.b -1(a4),d1
    cmp.b #$3a,d1
    bne.w loc_8446
loc_0b34:
    lea 1000(a6),a1 ; app+$3E8
    tst.l (a1)
    bne.w loc_8446
loc_0b3e:
    move.b d2,5(a0)
    bsr.s sub_0b4e
loc_0b44:
    movea.l a1,a0
    clr.b 4(a0)
    bra.w loc_0a1e
sub_0b4e:
    move.b 5(a0),5(a1)
    tst.b 254(a6) ; app+$FE
    bne.s loc_0b64
loc_0b5a:
    move.l (a0),(a1)
    move.b 6(a0),6(a1)
    rts
loc_0b64:
    move.b 5(a0),d0
    lea 6(a1),a2
    move.l a2,(a1)
    addq.w #6,a0
loc_0b70:
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s loc_0b70
loc_0b76:
    rts
sub_0b78:
    move.l (a2),d0
    beq.s loc_0bc8
loc_0b7c:
    movea.l d0,a1
    move.b 22(a0),d2
    lea 23(a0),a5
    bra.s loc_0b9c
sub_0b88:
    move.l (a2),d0
    beq.s loc_0bc8
loc_0b8c:
    movea.l d0,a1
    move.b 5(a0),d2
    movea.l (a0),a5
    bra.s loc_0b9c
loc_0b96:
    move.l (a1),d0
    beq.s loc_0bc4
loc_0b9a:
    movea.l d0,a1
loc_0b9c:
    cmp.b 22(a1),d2
    bcs.s loc_0b96
loc_0ba2:
    bhi.s loc_0bb8
loc_0ba4:
    move.b d2,d3
    lea 23(a1),a3
    movea.l a5,a4
loc_0bac:
    cmpm.b (a3)+,(a4)+
    bcs.s loc_0b96
loc_0bb0:
    bhi.s loc_0bb8
loc_0bb2:
    subq.b #1,d3
    bne.s loc_0bac
loc_0bb6:
    rts
loc_0bb8:
    move.l 4(a1),d0
    beq.s loc_0bc2
loc_0bbe:
    movea.l d0,a1
    bra.s loc_0b9c
loc_0bc2:
    addq.w #4,a1
loc_0bc4:
    moveq #3,d0
    rts
loc_0bc8:
    movea.l a2,a1
    moveq #3,d0
    rts
sub_0bce:
    movem.l a3-a5,-(sp)
    move.l 346(a6),d0 ; app+$15A
    beq.s loc_0be2
loc_0bd8:
    movea.l d0,a2
    bsr.s sub_0b88
loc_0bdc:
    beq.s loc_0bfc
loc_0bde:
    move.l a1,350(a6) ; app+$15E
loc_0be2:
    movea.l 354(a6),a2 ; app+$162
    bsr.s sub_0b88
loc_0be8:
    beq.s loc_0bfc
loc_0bea:
    move.l a1,358(a6) ; app+$166
    movea.l 362(a6),a2 ; app+$16A
    bsr.s sub_0b88
loc_0bf4:
    beq.s loc_0bfc
loc_0bf6:
    move.l a1,366(a6) ; app+$16E
    moveq #-1,d0
loc_0bfc:
    movem.l (sp)+,a3-a5
    rts
sub_0c02:
    bsr.s sub_0bce
loc_0c04:
    bne.w loc_843a
loc_0c08:
    bset #6,12(a1)
    bne.w loc_8436
loc_0c12:
    move.b 264(a6),d3 ; app+$108
    cmp.b 13(a1),d3
    bne.w loc_8436
loc_0c1e:
    cmp.l 8(a1),d4
    bne.w loc_843e
loc_0c26:
    move.b 23(a1),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.s loc_0c42
loc_0c30:
    tst.b 4(a0)
    beq.s loc_0c3a
loc_0c36:
    bsr.w sub_4e4c
loc_0c3a:
    lea 16(a1),a0
    move.l a0,346(a6) ; app+$15A
loc_0c42:
    rts
loc_0c44:
    move.l 572(a6),d4 ; app+$23C
    lea 1000(a6),a0 ; app+$3E8
    tst.l (a0)
    bne.s loc_0c84
loc_0c50:
    rts
sub_0c52:
    btst #0,575(a6) ; app+$23F
    bne.w loc_0c5e
loc_0c5c:
    rts
loc_0c5e:
    jmp sub_9746
loc_0c64:
    lea 1000(a6),a0 ; app+$3E8
    tst.l (a0)
    beq.s sub_0c52
loc_0c6c:
    move.l 572(a6),d4 ; app+$23C
    btst #0,d4
    beq.s loc_0c84
loc_0c76:
    jsr sub_9746
loc_0c7c:
    lea 1000(a6),a0 ; app+$3E8
    move.l 572(a6),d4 ; app+$23C
loc_0c84:
    tst.b 568(a6) ; app+$238
    bne.w sub_0c02
loc_0c8c:
    bsr.w sub_0bce
loc_0c90:
    beq.w loc_8436
loc_0c94:
    move.b 264(a6),d3 ; app+$108
    move.b 6(a0),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.s loc_0cac
loc_0ca2:
    pea loc_0c3a(pc)
    lea 354(a6),a2 ; app+$162
    bra.s sub_0cb6
loc_0cac:
    lea 346(a6),a2 ; app+$15A
    tst.l (a2)
    beq.w loc_8442
sub_0cb6:
    movea.l 4(a2),a1
sub_0cba:
    cmpi.w #$98,328(a6) ; app+$148
    bcc.s loc_0cd0
loc_0cc2:
    movem.l d3/a0-a1,-(sp)
    jsr sub_90a8
loc_0ccc:
    movem.l (sp)+,d3/a0-a1
loc_0cd0:
    movea.l 314(a6),a2 ; app+$13A
    move.l a2,(a1)
    movea.l a2,a1
    moveq #0,d0
    move.l d0,(a2)
    move.l d0,4(a2)
    move.l d4,8(a2)
    move.b d3,13(a2)
    move.w d0,20(a2)
    move.b d0,12(a2)
    move.b 326(a6),14(a2) ; app+$146
    move.l d0,16(a2)
    lea 22(a2),a2
    move.b 5(a0),d0
    movea.l (a0),a0
    move.b d0,(a2)+
loc_0d06:
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s loc_0d06
loc_0d0c:
    move.l a2,d0
    sub.l a1,d0
    addq.l #1,d0
    bclr #0,d0
    sub.w d0,328(a6) ; app+$148
    add.l d0,314(a6) ; app+$13A
    rts
sub_0d20:
    cmp.w 328(a6),d0 ; app+$148
    bcs.s loc_0d34
loc_0d26:
    movem.l d0/d3/a0-a1,-(sp)
    jsr sub_90a8
loc_0d30:
    movem.l (sp)+,d0/d3/a0-a1
loc_0d34:
    move.l d0,-(sp)
    bsr.s sub_0cba
loc_0d38:
    sub.l d0,314(a6) ; app+$13A
    add.w d0,328(a6) ; app+$148
    move.l (sp)+,d0
    sub.w d0,328(a6) ; app+$148
    add.l d0,314(a6) ; app+$13A
    rts
sub_0d4c:
; --- unverified ---
    movea.l 4(a2),a1
    cmpi.w #$98,328(a6) ; app+$148
    bcc.s hint_0d66
hint_0d58:
; --- unverified ---
    movem.l d3/a0-a1,-(sp)
    jsr sub_90a8
hint_0d62:
    dc.b    $4c,$df,$03,$08
hint_0d66:
    dc.b    $24,$6e,$01,$3a,$22,$8a,$22,$4a,$70,$00,$24,$80,$25,$40,$00,$04
    dc.b    $25,$44,$00,$08,$15,$43,$00,$0d,$35,$40,$00,$14,$15,$40,$00,$0c
    dc.b    $15,$6e,$01,$46,$00,$0e,$25,$40,$00,$10,$45,$ea,$00,$16,$10,$28
    dc.b    $00,$05,$20,$50,$14,$c0
hint_0d9c:
; --- unverified ---
    move.b (a0)+,(a2)+
    subq.b #1,d0
    bne.s hint_0d9c
hint_0da2:
; --- unverified ---
    move.l a2,d0
    sub.l a1,d0
    addq.l #1,d0
    bclr #0,d0
    sub.w d0,328(a6) ; app+$148
    add.l d0,314(a6) ; app+$13A
    rts
sub_0db6:
    bsr.s sub_0dcc
loc_0db8:
    cmp.b #$f,d3
    bcs.s loc_0dca
loc_0dbe:
    cmp.b #$13,d3
    bcc.s loc_0dca
loc_0dc4:
    moveq #98,d0
    bra.w loc_8486
loc_0dca:
    rts
sub_0dcc:
    bsr.w sub_79e6
loc_0dd0:
    lea 1576(a6),a0 ; app+$628
    clr.w (a0)
    lea 1616(a6),a0 ; app+$650
    clr.w (a0)
    moveq #0,d4
    movem.l d5-d7,-(sp)
    moveq #1,d5
    bsr.w sub_1208
loc_0de8:
    cmp.b #$1,d7
    bne.s loc_0e2c
loc_0dee:
    movem.l d2-d3,-(sp)
    addq.b #1,d5
    bsr.w sub_1208
loc_0df8:
    cmp.b #$4,d7
    bcs.w loc_0e50
loc_0e00:
    cmp.b #$16,d7
    bcc.w loc_0e50
loc_0e08:
    lea 1576(a6),a0 ; app+$628
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,0(a0,d0.w)
    lea 1616(a6),a0 ; app+$650
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l (sp)+,0(a0,d0.w)
    move.l (sp)+,4(a0,d0.w)
    bsr.w sub_0eda
loc_0e2a:
    bra.s loc_0e3e
loc_0e2c:
    lea 1576(a6),a0 ; app+$628
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,0(a0,d0.w)
    bsr.w sub_0f0a
loc_0e3e:
    movem.l (sp)+,d5-d7
    tst.w 1576(a6) ; app+$628
    bne.s loc_0e62
loc_0e48:
    tst.w 1616(a6) ; app+$650
    bne.s loc_0e62
loc_0e4e:
    rts
loc_0e50:
    movem.l (sp)+,d2-d3
    movem.l (sp)+,d5-d7
    movea.l a0,a4
    move.b -1(a4),d1
    moveq #0,d0
    rts
loc_0e62:
    moveq #18,d0
    bra.w loc_8482
    dc.b    $11,$2b,$12,$2d,$04,$2a,$05,$2f,$02,$28,$03,$29,$13,$7e,$08,$3d
    dc.b    $0e,$26,$ea,$21,$10,$5e,$0f,$7c,$fe,$24,$fa,$25,$f8,$40,$f4,$27
    dc.b    $f4,$22,$00
pcref_0e8b:
    dcb.b   4,0
    dc.b    $04,$04,$16,$16,$14,$14,$14,$14,$14,$14,$12
jt_0e9a:
    dc.w    sub_20b4-pcref_0ea2
    dc.w    sub_10a4-pcref_0ea2
    dc.w    sub_2bc0-pcref_0ea2
    dc.w    loc_2ca2-pcref_0ea2
pcref_0ea2:
    dc.w    sub_10da-pcref_0ea2
    dc.w    sub_10f8-pcref_0ea2
    dc.w    sub_1120-pcref_0ea2
    dc.w    sub_1124-pcref_0ea2
    dc.w    sub_1128-pcref_0ea2
    dc.w    sub_1150-pcref_0ea2
    dc.w    sub_1156-pcref_0ea2
    dc.w    sub_115c-pcref_0ea2
    dc.w    sub_1162-pcref_0ea2
    dc.w    sub_1168-pcref_0ea2
    dc.w    sub_1114-pcref_0ea2
    dc.w    sub_1118-pcref_0ea2
    dc.w    sub_111c-pcref_0ea2
    dc.w    sub_1050-pcref_0ea2
    dc.w    sub_1096-pcref_0ea2
    dc.w    sub_116e-pcref_0ea2
    dc.w    sub_117a-pcref_0ea2
    dc.w    sub_1178-pcref_0ea2
sub_0ec6:
    lea 1576(a6),a0 ; app+$628
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,0(a0,d0.w)
    moveq #1,d5
    bsr.w sub_1208
sub_0eda:
    cmp.b #$2,d5
    bne.s loc_0ef0
loc_0ee0:
    cmp.b #$4,d7
    bcs.w loc_0fc4
loc_0ee8:
    cmp.b #$16,d7
    bcc.w loc_0fc4
loc_0ef0:
    cmp.b #$1,d7
    bne.s sub_0f0a
loc_0ef6:
    lea 1616(a6),a0 ; app+$650
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l d2,0(a0,d0.w)
    move.l d3,4(a0,d0.w)
    bra.w loc_0fba
sub_0f0a:
    cmp.b #$2,d7
    beq.w loc_0f8a
loc_0f12:
    cmp.b #$4,d7
    bcs.w loc_0fca
loc_0f1a:
    cmp.b #$16,d7
    bcc.w loc_0fca
loc_0f22:
    cmp.b #$1,d5
    bne.s loc_0f60
loc_0f28:
    cmp.b #$11,d7
    beq.s loc_0f5a
loc_0f2e:
    cmp.b #$12,d7
    beq.s loc_0f5e
loc_0f34:
    cmp.b #$4,d7
    beq.s loc_0f44
loc_0f3a:
    cmp.b #$13,d7
    bne.w loc_0e62
loc_0f42:
    bra.s loc_0f60
loc_0f44:
    move.l 572(a6),d2 ; app+$23C
    moveq #0,d3
    move.b 264(a6),d3 ; app+$108
    cmp.b #$1,d3
    bne.s loc_0f58
loc_0f54:
    addq.b #1,267(a6) ; app+$10B
loc_0f58:
    bra.s loc_0ef6
loc_0f5a:
    moveq #21,d7
    bra.s loc_0f60
loc_0f5e:
    moveq #20,d7
loc_0f60:
    lea pcref_0e8b(pc),a2
    lea 1576(a6),a0 ; app+$628
    move.w (a0),d0
    move.w 0(a0,d0.w),d6
    move.b 0(a2,d6.w),d6
    cmp.b 0(a2,d7.w),d6
    bge.s loc_0f80
loc_0f78:
    addq.w #2,(a0)+
    move.w d7,0(a0,d0.w)
    bra.s loc_0f86
loc_0f80:
    bsr.w loc_0ffa
loc_0f84:
    bra.s loc_0f60
loc_0f86:
    moveq #0,d5
    bra.s loc_0fba
loc_0f8a:
    bsr.w sub_0ec6
loc_0f8e:
    bsr.w sub_1208
loc_0f92:
    lea 1616(a6),a0 ; app+$650
    move.w (a0),d0
    addq.w #8,(a0)+
    move.l d2,0(a0,d0.w)
    move.l d3,4(a0,d0.w)
    tst.w d3
    bpl.s loc_0fac
loc_0fa6:
    moveq #42,d0
    bsr.w loc_8486
loc_0fac:
    cmp.b #$3,d7
    beq.s loc_0fb8
loc_0fb2:
    moveq #19,d0
    bra.w loc_8482
loc_0fb8:
    moveq #1,d5
loc_0fba:
    addq.w #1,d5
    bsr.w sub_1208
loc_0fc0:
    bra.w sub_0eda
loc_0fc4:
    movea.l a0,a4
    move.b -1(a4),d1
loc_0fca:
    lea pcref_0e8b(pc),a2
loc_0fce:
    lea 1576(a6),a0 ; app+$628
    move.w (a0),d0
    tst.w 0(a0,d0.w)
    beq.s loc_0fe0
loc_0fda:
    bsr.w loc_0ffa
loc_0fde:
    bra.s loc_0fce
loc_0fe0:
    subq.w #2,1576(a6) ; app+$628
    lea 1616(a6),a0 ; app+$650
    subq.w #8,(a0)
    move.w (a0)+,d0
    move.l 0(a0,d0.w),d2
    move.l 4(a0,d0.w),d3
    rts
sub_0ff6:
    bra.w loc_0e62
loc_0ffa:
    lea 1616(a6),a0 ; app+$650
    subq.w #8,(a0)
    bcs.s sub_0ff6
loc_1002:
    move.w (a0)+,d0
    move.l 0(a0,d0.w),d2
    move.l 4(a0,d0.w),d3
    move.w d1,-(sp)
    lea 1576(a6),a1 ; app+$628
    subq.w #2,(a1)
    move.w (a1)+,d1
    move.w 0(a1,d1.w),d1
    cmp.b #$13,d1
    bcc.s loc_1032
loc_1020:
    subq.w #8,-(a0)
    bcs.s sub_0ff6
loc_1024:
    move.w (a0)+,d0
    move.l 4(a0,d0.w),d6
    move.l 0(a0,d0.w),d0
    exg
    exg
loc_1032:
    lea pcref_0ea2(pc),a1
    add.w d1,d1
    move.w -8(a1,d1.w),d1
    jsr 0(a1,d1.w)
loc_1040:
    move.w (sp)+,d1
    move.w -(a0),d0
    addq.w #8,(a0)+
    move.l d2,0(a0,d0.w)
    move.l d3,4(a0,d0.w)
    rts
sub_1050: ; jt: pcref_0ea2
    add.l d0,d2
    cmp.b #$1,d3
    beq.s loc_1066
loc_1058:
    cmp.b #$1,d6
    beq.s loc_106c
loc_105e:
    andi.w #$ff00,d6
    or.w d6,d3
    rts
loc_1066:
    cmp.b #$1,d6
    beq.s sub_1072
loc_106c:
    move.b #$1,d3
    bra.s loc_105e
sub_1072:
    tst.b 263(a6) ; app+$107
    bne.s loc_1086
loc_1078:
    tst.b 568(a6) ; app+$238
    beq.s loc_108a
loc_107e:
    moveq #21,d0
loc_1080:
    bsr.w loc_8486
loc_1084:
    st d4
loc_1086:
    moveq #2,d3
    rts
loc_108a:
    tst.b 344(a6) ; app+$158
    bne.s loc_107e
loc_1090:
    bra.s loc_1084
sub_1092:
    moveq #20,d0
    bra.s loc_1080
sub_1096: ; jt: pcref_0ea2
    sub.l d0,d2
    move.w d3,d0
    or.w d6,d0
    andi.w #$8000,d0
    tst.w d6
    bmi.s loc_10d4
sub_10a4: ; jt: pcref_0ea2
    cmp.b #$1,d6
    bne.s loc_10c0
loc_10aa:
    btst #1,540(a6) ; app+$21C
    bne.s loc_10bc
loc_10b2:
    btst #15,d3
    beq.s loc_10bc
loc_10b8:
    add.l 572(a6),d2 ; app+$23C
loc_10bc:
    subq.b #2,267(a6) ; app+$10B
loc_10c0:
    cmp.b d3,d6
    beq.s loc_10cc
loc_10c4:
    cmp.b #$1,d6
    bne.s loc_10d0
loc_10ca:
    bsr.s sub_1072
loc_10cc:
    move.b #$2,d3
loc_10d0:
    or.w d0,d3
    rts
loc_10d4:
    bsr.w sub_7a20
loc_10d8:
    bra.s loc_10c0
sub_10da: ; jt: pcref_0ea2
    bsr.s loc_10e4
loc_10dc:
    bsr.w sub_117e
loc_10e0:
    moveq #2,d3
    rts
loc_10e4:
    cmp.b #$1,d6
    beq.s sub_1072
loc_10ea:
    or.w d3,d6
    bmi.s sub_1092
loc_10ee:
    cmp.b #$1,d3
    beq.w sub_1072
loc_10f6:
    rts
sub_10f8: ; jt: pcref_0ea2
    bsr.s loc_10e4
loc_10fa:
    move.l d7,-(sp)
    bsr.w sub_11b2
loc_1100:
    movem.l (sp)+,d7
    bne.s loc_1108
loc_1106:
    rts
loc_1108:
    tst.b 568(a6) ; app+$238
    bne.w loc_1080
loc_1110:
    bra.w loc_108a
sub_1114: ; jt: pcref_0ea2
    and.l d0,d2
    bra.s loc_10e4
sub_1118: ; jt: pcref_0ea2
    or.l d0,d2
    bra.s loc_10e4
sub_111c: ; jt: pcref_0ea2
    eor.l d0,d2
    bra.s loc_10e4
sub_1120: ; jt: pcref_0ea2
    lsl.l d0,d2
    bra.s loc_10e4
sub_1124: ; jt: pcref_0ea2
    lsr.l d0,d2
    bra.s loc_10e4
sub_1128: ; jt: pcref_0ea2
    cmp.l d0,d2
    seq d2
loc_112c:
    ext.w d2
    ext.l d2
    move.w d3,d0
    or.w d6,d0
    bmi.w sub_1092
loc_1138:
    cmp.b d3,d6
    beq.s loc_114c
loc_113c:
    cmp.b #$1,d3
    beq.w sub_1072
loc_1144:
    cmp.b #$1,d6
    beq.w sub_1072
loc_114c:
    moveq #2,d3
    rts
sub_1150: ; jt: pcref_0ea2
    cmp.l d0,d2
    sne d2
    bra.s loc_112c
sub_1156: ; jt: pcref_0ea2
    cmp.l d0,d2
    slt d2
    bra.s loc_112c
sub_115c: ; jt: pcref_0ea2
    cmp.l d0,d2
    sgt d2
    bra.s loc_112c
sub_1162: ; jt: pcref_0ea2
    cmp.l d0,d2
    sle d2
    bra.s loc_112c
sub_1168: ; jt: pcref_0ea2
    cmp.l d0,d2
    sge d2
    bra.s loc_112c
sub_116e: ; jt: pcref_0ea2
    not.l d2
loc_1170:
    cmp.w #$1,d3
    beq.w sub_1072
sub_1178: ; jt: pcref_0ea2
    rts
sub_117a: ; jt: pcref_0ea2
    neg.l d2
    bra.s loc_1170
sub_117e:
    move.l d2,d6
    eor.l d0,d6
    tst.l d2
    bgt.s loc_1188
loc_1186:
    neg.l d2
loc_1188:
    tst.l d0
    bgt.s loc_118e
loc_118c:
    neg.l d0
loc_118e:
    move.l d2,d3
    swap d3
    mulu.w d0,d2
    swap d0
    tst.w d3
    beq.s loc_119e
loc_119a:
    swap d0
    bra.s loc_11a4
loc_119e:
    tst.w d0
    beq.s loc_11aa
loc_11a2:
    swap d3
loc_11a4:
    mulu.w d3,d0
    swap d0
    add.l d0,d2
loc_11aa:
    tst.l d6
    bpl.s loc_11b0
loc_11ae:
    neg.l d2
loc_11b0:
    rts
sub_11b2:
    tst.l d0
    beq.s loc_1200
loc_11b6:
    move.l d2,d6
    eor.l d0,d6
    move.l d6,-(sp)
    move.l d2,-(sp)
    tst.l d0
    bpl.s loc_11c4
loc_11c2:
    neg.l d0
loc_11c4:
    tst.l d2
    bpl.s loc_11ca
loc_11c8:
    neg.l d2
loc_11ca:
    moveq #31,d6
    move.l d0,d7
    moveq #0,d0
loc_11d0:
    add.l d7,d7
    dbcs d6,loc_11d0
loc_11d6:
    roxr.l #1,d7
    subi.w #$1f,d6
    neg.w d6
loc_11de:
    add.l d0,d0
    cmp.l d7,d2
    bcs.s loc_11e8
loc_11e4:
    addq.l #1,d0
    sub.l d7,d2
loc_11e8:
    lsr.l #1,d7
    dbf d6,loc_11de
loc_11ee:
    move.l (sp)+,d6
    bpl.s loc_11f4
loc_11f2:
    neg.l d2
loc_11f4:
    move.l (sp)+,d6
    bpl.s loc_11fa
loc_11f8:
    neg.l d0
loc_11fa:
    exg
    cmp.b d0,d0
    rts
loc_1200:
    moveq #61,d0
    rts
sub_1204:
; --- unverified ---
    movea.l a4,a0
    rts
sub_1208:
    moveq #0,d7
    ext.w d1
    bmi.s loc_1232
loc_120e:
    move.b pcref_1252(pc,d1.w),d7
    beq.s loc_1220
loc_1214:
    bpl.s loc_1226
loc_1216:
    cmp.b #$ff,d7
    bne.s loc_123c
loc_121c:
    bra.w loc_1246
loc_1220:
    movea.l a4,a0
    moveq #22,d7
    rts
loc_1226:
    cmp.b #$1,d7
    beq.s loc_1232
loc_122c:
    movea.l a4,a0
    move.b (a4)+,d1
    rts
loc_1232:
    movem.l d5-d6/a1-a2,-(sp)
    move.l a4,-(sp)
    bra.w loc_12d2
loc_123c:
    movem.l d5-d6/a1-a2,-(sp)
    move.l a4,-(sp)
    bra.w loc_13b8
loc_1246:
    movem.l d5-d6/a1-a2,-(sp)
    move.l a4,-(sp)
    moveq #0,d2
    bra.w loc_1324
pcref_1252:
    dcb.b   33,0
    dc.b    $ea,$f4,$00,$fe,$fa,$0e,$f4,$02,$03,$04,$11,$00,$12,$01,$05,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$00,$00,$f2,$08,$ee,$00,$f8
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$00,$00,$00,$10,$01,$00
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$00,$0f,$00,$13,$00
loc_12d2:
    lea 1134(a6),a0 ; app+$46E
    bsr.w sub_76b8
loc_12da:
    beq.w loc_1530
loc_12de:
    moveq #22,d7
    bra.s loc_131c
loc_12e2:
    move.b (a4)+,d1
    cmp.b #$3d,d1
    beq.s loc_1300
loc_12ea:
    moveq #15,d7
    bra.s loc_131c
loc_12ee:
    moveq #10,d7
    move.b (a4)+,d1
    cmp.b #$3c,d1
    beq.s loc_1318
loc_12f8:
    cmp.b #$3e,d1
    beq.s loc_1300
loc_12fe:
    bra.s loc_130e
loc_1300:
    moveq #9,d7
    bra.s loc_131a
loc_1304:
    moveq #11,d7
    move.b (a4)+,d1
    cmp.b #$3e,d1
    beq.s loc_1318
loc_130e:
    cmp.b #$3d,d1
    bne.s loc_131c
loc_1314:
    addq.w #2,d7
    bra.s loc_131a
loc_1318:
    subq.w #4,d7
loc_131a:
    move.b (a4)+,d1
loc_131c:
    movea.l (sp)+,a0
    movem.l (sp)+,d5-d6/a1-a2
    rts
loc_1324:
    move.b 303(a6),d7 ; app+$12F
    beq.s loc_1330
loc_132a:
    subq.l #1,a4
    bra.w loc_13b8
loc_1330:
    lea -1(a4),a0
loc_1334:
    add.l d2,d2
    move.l d2,d0
    add.l d0,d0
    add.l d0,d0
    add.l d0,d2
    subi.b #$30,d1
    andi.l #$f,d1
    add.l d1,d2
    move.b (a4)+,d1
    cmp.b #$3a,d1
    bcc.s loc_1358
loc_1352:
    cmp.b #$30,d1
    bcc.s loc_1334
loc_1358:
    moveq #1,d7
    moveq #2,d3
    cmp.b #$24,d1
    bne.s loc_131c
loc_1362:
    bra.w loc_166a
loc_1366:
    moveq #4,d0
    move.b d1,d3
loc_136a:
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.w loc_1434
loc_1374:
    cmp.b d3,d1
    bne.s loc_1382
loc_1378:
    move.b (a4)+,d1
    cmp.b d3,d1
    beq.s loc_1382
loc_137e:
    moveq #2,d3
    bra.s loc_131c
loc_1382:
    subq.b #1,d0
    bcs.w loc_143e
loc_1388:
    lsl.l #8,d2
    move.b d1,d2
    bra.s loc_136a
loc_138e:
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.w loc_1434
loc_1398:
    cmp.b #$2,d1
    bcc.w loc_1434
loc_13a0:
    add.l d2,d2
    bcs.w loc_143e
loc_13a6:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s loc_142c
loc_13b0:
    cmp.b #$2,d1
    bcs.s loc_13a0
loc_13b6:
    bra.s loc_142c
loc_13b8:
    neg.b d7
    ext.w d7
    moveq #0,d2
    moveq #2,d3
    moveq #1,d0
    exg
    jmp 0(pc,d0.w) ; unresolved_indirect_core:pcindex.brief
    bra.w loc_140e
    bra.s loc_138e
    bra.w loc_13e6
    bra.s loc_1366
    bra.w loc_12ee
    bra.w loc_1304
    bra.w loc_12e2
loc_13e0:
    moveq #64,d1
    bra.w loc_12d2
loc_13e6:
    move.b (a4),d0
    subi.b #$30,d0
    bcs.s loc_13e0
loc_13ee:
    cmp.b #$9,d0
    bcc.s loc_13e0
loc_13f4:
    move.b d0,d1
    addq.l #1,a4
loc_13f8:
    lsl.l #3,d2
    bcs.s loc_143e
loc_13fc:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s loc_142c
loc_1406:
    cmp.b #$9,d1
    bcs.s loc_13f8
loc_140c:
    bra.s loc_142c
loc_140e:
    lea pcref_1442(pc),a0
    moveq #0,d1
    move.b (a4)+,d1
    bmi.s loc_1434
loc_1418:
    move.b 0(a0,d1.w),d1
    bmi.s loc_1434
loc_141e:
    lsl.l #4,d2
    or.b d1,d2
    move.b (a4)+,d1
    bmi.s loc_142c
loc_1426:
    move.b 0(a0,d1.w),d1
    bpl.s loc_141e
loc_142c:
    move.b -1(a4),d1
    bra.w loc_131c
loc_1434:
    moveq #22,d0
loc_1436:
    bsr.w loc_8486
loc_143a:
    st d4
    bra.s loc_142c
loc_143e:
    moveq #23,d0
    bra.s loc_1436
pcref_1442:
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$0a,$0b,$0c,$0d,$0e,$0f,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$0a,$0b,$0c,$0d,$0e,$0f,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
sub_14c2:
    movea.l (a0),a1
    subq.l #4,sp
    move.b (a1)+,2(sp)
    move.b (a1)+,3(sp)
    move.b (a1)+,(sp)
    move.b (a1)+,1(sp)
    move.l (sp)+,d0
    cmp.l #$52474e41,d0 ; 'RGNA'
    beq.s loc_151e
loc_14de:
    cmp.w #$5f5f,d0
    bne.s loc_151c
loc_14e4:
    swap d0
    cmp.w #$5253,d0
    beq.s loc_1516
loc_14ec:
    cmp.w #$4732,d0
    beq.s loc_1504
loc_14f2:
    cmp.w #$4c4b,d0
    beq.s loc_14fa
loc_14f8:
    bne.s loc_151c
loc_14fa:
    moveq #0,d2
    move.w 540(a6),d2 ; app+$21C
    addq.w #1,d2
    bra.s loc_1512
loc_1504:
    move.l #$1002b,d2
    move.b 289(a6),d0 ; app+$121
    lsl.w #8,d0
    or.w d0,d2
loc_1512:
    moveq #0,d0
    rts
loc_1516:
    move.l 2122(a6),d2 ; app+$84A
    bra.s loc_1512
loc_151c:
    rts
loc_151e:
    moveq #0,d2
    tst.b 257(a6) ; app+$101
    beq.s loc_151c
loc_1526:
    movea.l 2178(a6),a1 ; app+$882
    move.w 8(a1),d2
    bra.s loc_1512
loc_1530:
    moveq #1,d7
    seq 4(a0)
    cmp.b #$23,d1
    bne.s loc_1542
loc_153c:
    move.b (a4)+,d1
    st 4(a0)
loc_1542:
    cmpi.b #$4,5(a0)
    bne.s loc_1556
loc_154a:
    bsr.w sub_14c2
loc_154e:
    bne.s loc_1556
loc_1550:
    moveq #2,d3
    bra.w loc_15c8
loc_1556:
    tst.b 568(a6) ; app+$238
    bne.w loc_1606
loc_155e:
    bsr.w sub_0bce
loc_1562:
    beq.s loc_156c
loc_1564:
    moveq #0,d2
    st d4
    moveq #2,d3
    bra.s loc_15c8
loc_156c:
    move.l 8(a1),d2
    moveq #0,d3
    move.b 13(a1),d3
    btst #4,12(a1)
    bne.s loc_15d0
loc_157e:
    cmp.b #$2,d3
    beq.s loc_15c8
loc_1584:
    cmp.b #$e,d3
    beq.s loc_15c8
loc_158a:
    cmp.b #$1,d3
    beq.s loc_15f2
loc_1590:
    cmp.b #$f,d3
    bcs.s loc_15b8
loc_1596:
    cmp.b #$13,d3
    bcc.s loc_15b8
loc_159c:
    lea 2162(a6),a0 ; app+$872
    move.l a0,d2
    move.l 8(a1),(a0)+
    move.b 14(a1),(a0)+
    move.b 15(a1),(a0)+
    move.l 16(a1),(a0)+
    move.w 20(a1),(a0)
    bra.s loc_15c8
loc_15b8:
    cmp.b #$5,d3
    bne.w loc_1696
loc_15c0:
    moveq #2,d3
    moveq #7,d0
    bsr.w sign_extended_operand
loc_15c8:
    move.b -1(a4),d1
    bra.w loc_131c
loc_15d0:
    st d4
    swap d3
    move.w 20(a1),d3
    bsr.w sub_79f6
loc_15dc:
    swap d3
    move.b -1(a4),d1
    tst.b 568(a6) ; app+$238
    beq.w loc_131c
loc_15ea:
    ori.w #$8000,d3
    bra.w loc_131c
loc_15f2:
    tst.b 14(a1)
    beq.s loc_15c8
loc_15f8:
    move.b 326(a6),d0 ; app+$146
    cmp.b 14(a1),d0
    beq.s loc_15c8
loc_1602:
    st d4
    bra.s loc_15c8
loc_1606:
    bsr.w sub_0bce
loc_160a:
    sne d0
    move.b -1(a4),d1
    cmp.b #$23,d1
    bne.s loc_1618
loc_1616:
    move.b (a4)+,d1
loc_1618:
    tst.b d0
    bne.w loc_16a4
loc_161e:
    btst #7,12(a1)
    beq.s loc_1630
loc_1626:
    btst #6,12(a1)
    beq.w loc_16a4
loc_1630:
    move.l 8(a1),d2
    moveq #0,d3
    move.b 13(a1),d3
    btst #4,12(a1)
    bne.s loc_15d0
loc_1642:
    cmp.b #$1,d3
    bne.w loc_157e
loc_164a:
    move.b 326(a6),d0 ; app+$146
    cmp.b 14(a1),d0
    bne.s loc_165c
loc_1654:
    addq.b #1,267(a6) ; app+$10B
    bra.w loc_131c
loc_165c:
    ori.w #$8000,d3
    st d4
    bsr.w sub_7a0c
loc_1666:
    bra.w loc_131c
loc_166a:
    movea.l a0,a1
    lea 1134(a6),a0 ; app+$46E
    lea 6(a0),a2
    move.l a2,(a0)
    sf 4(a0)
    move.b 278(a6),(a2)+ ; app+$116
    move.l a4,d0
    sub.l a1,d0
    move.b d0,5(a0)
    subq.b #1,d0
loc_1688:
    move.b (a1)+,(a2)+
    subq.b #1,d0
    bne.s loc_1688
loc_168e:
    move.b (a4)+,d1
    moveq #1,d7
    bra.w loc_1556
loc_1696:
    moveq #24,d0
loc_1698:
    moveq #2,d3
    st d4
    bsr.w loc_8486
loc_16a0:
    bra.w loc_131c
loc_16a4:
    moveq #3,d0
    bra.s loc_1698
sub_16a8:
    bsr.w sub_0db6
loc_16ac:
    tst.w d3
    bmi.s loc_16c4
loc_16b0:
    cmp.b #$f,d3
    bcs.s loc_16c2
loc_16b6:
    cmp.b #$13,d3
    bcc.s loc_16c2
loc_16bc:
    moveq #98,d0
    bra.w loc_8486
loc_16c2:
    rts
loc_16c4:
    st d4
    moveq #20,d0
    bra.w loc_8486
sub_16cc:
    bsr.s sub_16a8
loc_16ce:
    cmp.b #$1,d3
    bne.s loc_16dc
loc_16d4:
    tst.b 263(a6) ; app+$107
    beq.w loc_8452
loc_16dc:
    moveq #0,d0
    rts
hint_16e0:
; --- unverified ---
    movea.l (sp),a0
    addq.l #2,(sp)
    bra.s hint_16ec
hint_16e6:
    dc.b    $20,$57,$54,$97,$3a,$c6
hint_16ec:
; --- unverified ---
    move.w (a0),d0
    move.w d0,-(sp)
    btst #6,d0
    beq.s hint_16fe
hint_16f6:
; --- unverified ---
    bsr.w sub_1872
hint_16fa:
; --- unverified ---
    move.w (sp)+,d0
    bra.s hint_1704
hint_16fe:
; --- unverified ---
    bsr.w hint_187e
hint_1702:
    dc.b    $30,$1f
hint_1704:
    dc.b    $20,$6e,$02,$4c,$8b,$50
hint_170a:
; --- unverified ---
    cmp.b #$30,d5
    bcs.s hint_1738
hint_1710:
; --- unverified ---
    cmp.b #$3a,d5
    bcs.s hint_172a
hint_1716:
; --- unverified ---
    cmp.b #$3c,d5
    beq.s hint_1732
hint_171c:
; --- unverified ---
    btst #6,d5
    bne.s hint_1748
hint_1722:
; --- unverified ---
    btst #6,d0
    beq.s hint_1742
hint_1728:
; --- unverified ---
    rts
hint_172a:
; --- unverified ---
    btst #5,d0
    beq.s hint_1742
hint_1730:
; --- unverified ---
    rts
hint_1732:
; --- unverified ---
    tst.b d0
    bpl.s hint_1742
hint_1736:
; --- unverified ---
    rts
hint_1738:
; --- unverified ---
    move.b d5,d2
    lsr.b #3,d2
    btst d2,d0
    beq.s hint_1742
hint_1740:
; --- unverified ---
    rts
hint_1742:
; --- unverified ---
    moveq #17,d0
    bra.w loc_8486
hint_1748:
; --- unverified ---
    andi.w #$bf,d5
    move.w d5,d2
    rol.w #8,d2
    and.w d2,d0
    beq.s hint_1742
hint_1754:
; --- unverified ---
    movea.l (sp)+,a0
    jmp 2(a0) ; unresolved_indirect_hint:disp
sub_175a:
    moveq #37,d0
    bra.w loc_8482
loc_1760:
    bsr.s sub_177e
loc_1762:
    bne.s sub_175a
loc_1764:
    tst.b d0
    bne.s sub_175a
loc_1768:
    rts
sub_176a:
; --- unverified ---
    bsr.s sub_177e
hint_176c:
; --- unverified ---
    bne.s hint_177a
hint_176e:
; --- unverified ---
    tst.b d0
    bne.s hint_1778
hint_1772:
; --- unverified ---
    moveq #16,d0
    bsr.w loc_8486
hint_1778:
    dc.b    $b0,$00
hint_177a:
; --- unverified ---
    rts
hint_177c:
; --- unverified ---
    bra.s hint_1772
sub_177e:
    move.b d1,d0
    movea.l a4,a0
    ext.w d0
    move.b 126(a6,d0.w),d0
loc_1788:
    cmp.b #$41,d0
    beq.s loc_17b6
loc_178e:
    cmp.b #$44,d0
    beq.s loc_17b6
loc_1794:
    cmp.b #$52,d0
    beq.s loc_17e4
loc_179a:
    cmp.b #$53,d0
    bne.w loc_181a
loc_17a2:
    move.b (a0)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b #$50,d0
    bne.s loc_181a
loc_17b0:
    moveq #1,d0
    moveq #7,d2
    bra.s loc_17ca
loc_17b6:
    move.b (a0)+,d2
    cmp.b #$37,d2
    bhi.s loc_181a
loc_17be:
    subi.b #$30,d2
    bcs.s loc_181a
loc_17c4:
    cmp.b #$41,d0
    seq d0
loc_17ca:
    andi.b #$1,d0
    moveq #0,d1
    move.b (a0)+,d1
    movea.l #sub_a764,a1
    tst.b 0(a1,d1.w)
    beq.s loc_181a
loc_17de:
    movea.l a0,a4
    cmp.b d0,d0
    rts
loc_17e4:
    move.b (a0)+,d2
    cmp.b #$39,d2
    bhi.s loc_181a
loc_17ec:
    cmp.b #$30,d2
    bcs.s loc_181a
loc_17f2:
    cmp.b #$31,d2
    bne.s loc_180e
loc_17f8:
    move.b (a0),d0
    cmp.b #$36,d0
    bcc.s loc_180e
loc_1800:
    cmp.b #$30,d0
    bcs.s loc_180e
loc_1806:
    addi.b #$a,d0
    move.b d0,d2
    addq.l #1,a0
loc_180e:
    subi.b #$30,d2
    cmp.b #$8,d2
    scc d0
    bra.s loc_17ca
loc_181a:
    lea 1134(a6),a0 ; app+$46E
    movem.l a2/a4,-(sp)
    move.b -1(a4),d1
    bsr.w sub_7680
loc_182a:
    bne.s loc_1866
loc_182c:
    movea.l 362(a6),a2 ; app+$16A
    movem.l d1/d3/a3-a5,-(sp)
    bsr.w sub_0b88
loc_1838:
    movem.l (sp)+,d1/d3/a3-a5
    bne.s loc_1866
loc_183e:
    cmpi.b #$4,13(a1)
    bne.s loc_1866
loc_1846:
    move.b 9(a1),d0
    move.b 11(a1),d2
    tst.b 568(a6) ; app+$238
    beq.s loc_185c
loc_1854:
    btst #6,12(a1)
    beq.s loc_1866
loc_185c:
    movem.l (sp)+,a0/a2
    movea.l a0,a2
    cmp.b d0,d0
    rts
loc_1866:
    movem.l (sp)+,a2/a4
    move.b -1(a4),d1
    moveq #-1,d0
    rts
sub_1872:
; --- unverified ---
    tst.b 281(a6) ; app+$119
    beq.s hint_187e
hint_1878:
; --- unverified ---
    st 282(a6) ; app+$11A
    bra.s hint_1882
hint_187e:
    dc.b    $51,$ee,$01,$1a
hint_1882:
; --- unverified ---
    bsr.w sub_177e
hint_1886:
; --- unverified ---
    bne.s hint_18a0
hint_1888:
    dc.b    $7a,$00,$8a,$02
hint_188c:
; --- unverified ---
    tst.b d0
    beq.s hint_189e
hint_1890:
; --- unverified ---
    ori.b #$8,d5
    cmpi.b #$1,569(a6) ; app+$239
    beq.w loc_844a
hint_189e:
; --- unverified ---
    rts
hint_18a0:
; --- unverified ---
    movea.l a4,a2
    cmp.b #$28,d1
    beq.w hint_1a3c
hint_18aa:
; --- unverified ---
    cmp.b #$2d,d1
    beq.w hint_1a78
hint_18b2:
; --- unverified ---
    cmp.b #$23,d1
    beq.w hint_1a9a
hint_18ba:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$43,d1
    beq.s hint_1908
hint_18c6:
; --- unverified ---
    cmp.b #$53,d1
    beq.s hint_18f4
hint_18cc:
; --- unverified ---
    cmp.b #$55,d1
    bne.s hint_192a
hint_18d2:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$53,d1
    bne.s hint_192a
hint_18e0:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$50,d1
    bne.s hint_192a
hint_18ee:
; --- unverified ---
    moveq #4,d5
    bra.w hint_1cfe
hint_18f4:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$52,d1
    bne.s hint_192a
hint_1902:
; --- unverified ---
    moveq #2,d5
    bra.w hint_1cfe
hint_1908:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$43,d1
    bne.s hint_192a
hint_1916:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$52,d1
    bne.s hint_192a
hint_1924:
; --- unverified ---
    moveq #1,d5
    bra.w hint_1cfe
hint_192a:
    dc.b    $28,$4a,$12,$2c,$ff,$ff
hint_1930:
; --- unverified ---
    bsr.w sub_0db6
hint_1934:
; --- unverified ---
    cmp.b #$28,d1
    beq.w hint_1b08
hint_193c:
; --- unverified ---
    cmp.b #$2e,d1
    beq.s hint_1988
hint_1942:
; --- unverified ---
    cmp.b #$5c,d1
    beq.s hint_1988
hint_1948:
; --- unverified ---
    tst.b 284(a6) ; app+$11C
    bne.s hint_19a0
hint_194e:
; --- unverified ---
    btst #2,271(a6) ; app+$10F
    beq.s hint_197e
hint_1956:
; --- unverified ---
    movea.w d2,a0
    cmpa.l d2,a0
    bne.s hint_197e
hint_195c:
; --- unverified ---
    tst.b d4
    bne.s hint_197e
hint_1960:
; --- unverified ---
    cmp.b #$1,d3
    beq.s hint_197e
hint_1966:
; --- unverified ---
    bsr.w sub_8dce
hint_196a:
; --- unverified ---
    bne.s hint_197e
hint_196c:
; --- unverified ---
    move.w d2,(a5)+
    bset #15,d4
    bsr.w hint_19ea
hint_1976:
; --- unverified ---
    moveq #56,d5
    moveq #14,d0
    bra.w hint_8808
hint_197e:
; --- unverified ---
    tst.b 282(a6) ; app+$11A
    beq.s hint_19c2
hint_1984:
; --- unverified ---
    bra.w hint_1c16
hint_1988:
; --- unverified ---
    move.b (a4),d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b #$4c,d0
    beq.s hint_19b8
hint_1996:
; --- unverified ---
    cmp.b #$57,d0
    bne.s hint_19c2
hint_199c:
    dc.b    $52,$8c,$12,$1c
hint_19a0:
; --- unverified ---
    moveq #56,d5
    tst.b 568(a6) ; app+$238
    beq.s hint_19b4
hint_19a8:
; --- unverified ---
    bsr.w hint_78b6
hint_19ac:
; --- unverified ---
    bclr #14,d4
    bsr.w hint_19ea
hint_19b4:
; --- unverified ---
    move.w d2,(a5)+
    rts
hint_19b8:
; --- unverified ---
    addq.l #1,a4
    move.b (a4)+,d1
    bclr #15,d4
    bra.s hint_19c6
hint_19c2:
    dc.b    $08,$c4,$00,$0f
hint_19c6:
; --- unverified ---
    moveq #57,d5
    tst.b 568(a6) ; app+$238
    beq.s hint_19e6
hint_19ce:
; --- unverified ---
    tst.w d3
    bpl.s hint_19d8
hint_19d2:
; --- unverified ---
    jmp sub_98fc
hint_19d8:
; --- unverified ---
    bsr.s hint_19ea
hint_19da:
; --- unverified ---
    cmp.b #$1,d3
    bne.s hint_19e6
hint_19e0:
; --- unverified ---
    jsr dat_9962
hint_19e6:
; --- unverified ---
    move.l d2,(a5)+
    rts
hint_19ea:
; --- unverified ---
    tst.b 571(a6) ; app+$23B
    bne.s hint_1a34
hint_19f0:
; --- unverified ---
    cmpi.b #$1,569(a6) ; app+$239
    beq.s hint_1a04
hint_19f8:
; --- unverified ---
    tst.b 287(a6) ; app+$11F
    beq.s hint_1a04
hint_19fe:
; --- unverified ---
    btst #0,d2
    bne.s hint_1a36
hint_1a04:
; --- unverified ---
    btst #15,d4
    beq.s hint_1a34
hint_1a0a:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_1a34
hint_1a10:
; --- unverified ---
    tst.b 285(a6) ; app+$11D
    beq.s hint_1a34
hint_1a16:
; --- unverified ---
    move.w 540(a6),d0 ; app+$21C
    cmp.w #$2,d0
    bcs.s hint_1a2e
hint_1a20:
; --- unverified ---
    cmp.w #$4,d0
    bcc.s hint_1a2e
hint_1a26:
; --- unverified ---
    cmp.l #$4,d2
    beq.s hint_1a34
hint_1a2e:
; --- unverified ---
    moveq #82,d0
    bsr.w loc_8486
hint_1a34:
; --- unverified ---
    rts
hint_1a36:
; --- unverified ---
    moveq #35,d0
    bra.w loc_8486
hint_1a3c:
; --- unverified ---
    move.b (a4)+,d1
    tst.b 289(a6) ; app+$121
    bne.w hint_4f2a
hint_1a46:
; --- unverified ---
    bsr.w sub_176a
hint_1a4a:
; --- unverified ---
    bne.w hint_192a
hint_1a4e:
; --- unverified ---
    move.b d2,d4
    cmp.b #$29,d1
    beq.s hint_1a66
hint_1a56:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_845e
hint_1a5e:
; --- unverified ---
    clr.l -(sp)
    moveq #2,d3
    bra.w hint_1b70
hint_1a66:
; --- unverified ---
    move.b (a4)+,d1
    moveq #16,d5
    cmp.b #$2b,d1
    bne.s hint_1a74
hint_1a70:
    dc.b    $7a,$18,$12,$1c
hint_1a74:
; --- unverified ---
    or.b d4,d5
    rts
hint_1a78:
; --- unverified ---
    cmpi.b #$28,(a4)+
    bne.w hint_192a
hint_1a80:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_176a
hint_1a86:
; --- unverified ---
    bne.w hint_192a
hint_1a8a:
; --- unverified ---
    cmp.b #$29,d1
    bne.w hint_845e
hint_1a92:
; --- unverified ---
    move.b (a4)+,d1
    moveq #32,d5
    or.b d2,d5
    rts
hint_1a9a:
    dc.b    $12,$1c
hint_1a9c:
; --- unverified ---
    bsr.w sub_0db6
hint_1aa0:
; --- unverified ---
    moveq #60,d5
    move.b 569(a6),d0 ; app+$239
    beq.s hint_1ad0
hint_1aa8:
; --- unverified ---
    subq.b #1,d0
    beq.s hint_1ae8
hint_1aac:
; --- unverified ---
    subq.b #1,d0
    beq.s hint_1ad0
hint_1ab0:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_1acc
hint_1ab6:
; --- unverified ---
    tst.w d3
    bpl.s hint_1ac0
hint_1aba:
; --- unverified ---
    jmp sub_98fc
hint_1ac0:
; --- unverified ---
    cmp.b #$1,d3
    bne.s hint_1acc
hint_1ac6:
; --- unverified ---
    jsr dat_9962
hint_1acc:
; --- unverified ---
    move.l d2,(a5)+
    rts
hint_1ad0:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_1ae4
hint_1ad6:
; --- unverified ---
    tst.w d3
    bpl.s hint_1ae0
hint_1ada:
; --- unverified ---
    jmp dat_9938
hint_1ae0:
; --- unverified ---
    bsr.w hint_789c
hint_1ae4:
; --- unverified ---
    move.w d2,(a5)+
    rts
hint_1ae8:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_1ae4
hint_1aee:
; --- unverified ---
    tst.w d3
    bmi.s hint_1afe
hint_1af2:
; --- unverified ---
    bsr.w sub_788c
hint_1af6:
; --- unverified ---
    andi.w #$ff,d2
    move.w d2,(a5)+
    rts
hint_1afe:
    dc.b    $1a,$fc
hint_1b00:
    dc.b    $00,$00
hint_1b08:
; --- unverified ---
    move.b (a4)+,d1
    move.l d2,-(sp)
    bsr.w sub_177e
hint_1b10:
; --- unverified ---
    bne.w hint_1bec
hint_1b14:
; --- unverified ---
    bsr.w hint_176e
hint_1b18:
; --- unverified ---
    cmp.b #$29,d1
    bne.s hint_1b68
hint_1b1e:
; --- unverified ---
    btst #1,271(a6) ; app+$10F
    beq.s hint_1b4a
hint_1b26:
; --- unverified ---
    tst.b d4
    bne.s hint_1b4a
hint_1b2a:
; --- unverified ---
    tst.l (sp)
    bne.s hint_1b4a
hint_1b2e:
; --- unverified ---
    moveq #16,d5
    or.b d2,d5
    move.l (sp)+,d2
    bsr.w sub_8dce
hint_1b38:
; --- unverified ---
    bne.s hint_1b42
hint_1b3a:
; --- unverified ---
    move.b (a4)+,d1
    moveq #13,d0
    bra.w hint_8808
hint_1b42:
    dc.b    $2f,$02,$14,$05,$02,$02,$00,$07
hint_1b4a:
; --- unverified ---
    moveq #40,d5
    or.b d2,d5
    move.l (sp)+,d2
    move.b (a4)+,d1
    tst.w d3
    bpl.s hint_1b5c
hint_1b56:
; --- unverified ---
    jmp dat_991c
hint_1b5c:
; --- unverified ---
    move.w d2,(a5)+
    tst.b 568(a6) ; app+$238
    bne.w hint_78b6
hint_1b66:
; --- unverified ---
    rts
hint_1b68:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_1b70:
; --- unverified ---
    moveq #48,d5
    or.b d2,d5
    move.b (a4)+,d1
    bsr.w sub_177e
hint_1b7a:
; --- unverified ---
    bne.w hint_845e
hint_1b7e:
; --- unverified ---
    lsl.b #3,d0
    or.b d2,d0
    lsl.b #4,d0
    swap d3
    move.b d0,d3
    move.l (sp)+,d2
    cmp.b #$2e,d1
    beq.s hint_1b96
hint_1b90:
; --- unverified ---
    cmp.b #$5c,d1
    bne.s hint_1bb2
hint_1b96:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s hint_1bb0
hint_1ba4:
; --- unverified ---
    cmp.b #$4c,d1
    bne.w hint_8466
hint_1bac:
    dc.b    $00,$03,$00,$08
hint_1bb0:
    dc.b    $12,$1c
hint_1bb2:
; --- unverified ---
    tst.b 289(a6) ; app+$121
    beq.s hint_1bc8
hint_1bb8:
; --- unverified ---
    cmp.b #$2a,d1
    bne.s hint_1bc8
hint_1bbe:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5740
hint_1bc4:
    dc.b    $d0,$00,$86,$00
hint_1bc8:
; --- unverified ---
    cmp.b #$29,d1
    bne.w loc_0fb2
hint_1bd0:
; --- unverified ---
    move.b (a4)+,d1
    move.b d3,(a5)+
    swap d3
    tst.w d3
    bpl.s hint_1be0
hint_1bda:
; --- unverified ---
    jmp dat_9946
hint_1be0:
; --- unverified ---
    move.b d2,(a5)+
    tst.b 568(a6) ; app+$238
    bne.w hint_78b0
hint_1bea:
; --- unverified ---
    rts
hint_1bec:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$50,d1
    bne.w hint_845e
hint_1bfa:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$43,d1
    bne.w hint_845e
hint_1c0a:
; --- unverified ---
    move.l (sp)+,d2
    move.b (a4)+,d1
    cmp.b #$29,d1
    bne.s hint_1c58
hint_1c14:
    dc.b    $12,$1c
hint_1c16:
; --- unverified ---
    moveq #58,d5
    tst.b 568(a6) ; app+$238
    beq.s hint_1c54
hint_1c1e:
; --- unverified ---
    tst.w d3
    bpl.s hint_1c28
hint_1c22:
; --- unverified ---
    jmp loc_98ee
hint_1c28:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_1c48
hint_1c2e:
; --- unverified ---
    bclr #15,d4
    bsr.w hint_19ea
hint_1c36:
; --- unverified ---
    sub.l 572(a6),d2 ; app+$23C
    move.l a5,d0
    sub.l 588(a6),d0 ; app+$24C
    sub.l d0,d2
    move.w d2,(a5)+
    bra.w sub_78bc
hint_1c48:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_1c2e
hint_1c4e:
; --- unverified ---
    moveq #33,d0
    bsr.w loc_8486
hint_1c54:
; --- unverified ---
    move.w d2,(a5)+
    rts
hint_1c58:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_845e
hint_1c60:
; --- unverified ---
    moveq #59,d5
    move.l d2,-(sp)
    move.b (a4)+,d1
    bsr.w sub_177e
hint_1c6a:
; --- unverified ---
    bne.w hint_845e
hint_1c6e:
; --- unverified ---
    lsl.b #3,d0
    or.b d2,d0
    lsl.b #4,d0
    move.b d0,d4
    cmp.b #$2e,d1
    beq.s hint_1c82
hint_1c7c:
; --- unverified ---
    cmp.b #$5c,d1
    bne.s hint_1c9e
hint_1c82:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s hint_1c9c
hint_1c90:
; --- unverified ---
    cmp.b #$4c,d1
    bne.w hint_8466
hint_1c98:
    dc.b    $00,$04,$00,$08
hint_1c9c:
    dc.b    $12,$1c
hint_1c9e:
; --- unverified ---
    move.l (sp)+,d2
    tst.b 289(a6) ; app+$121
    beq.s hint_1cb6
hint_1ca6:
; --- unverified ---
    cmp.b #$2a,d1
    bne.s hint_1cb6
hint_1cac:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5740
hint_1cb2:
    dc.b    $d0,$00,$88,$00
hint_1cb6:
; --- unverified ---
    move.b d4,(a5)+
    tst.b 568(a6) ; app+$238
    beq.s hint_1cf0
hint_1cbe:
; --- unverified ---
    tst.w d3
    bmi.s hint_1ce2
hint_1cc2:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_1cce
hint_1cc8:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_1cea
hint_1cce:
; --- unverified ---
    sub.l 572(a6),d2 ; app+$23C
    move.l a5,d0
    sub.l 588(a6),d0 ; app+$24C
    sub.l d0,d2
    addq.l #1,d2
    bsr.w hint_78b0
hint_1ce0:
; --- unverified ---
    bra.s hint_1cf0
hint_1ce2:
; --- unverified ---
    jsr dat_98e0
hint_1ce8:
; --- unverified ---
    bra.s hint_1cf2
hint_1cea:
; --- unverified ---
    moveq #33,d0
    bsr.w loc_8486
hint_1cf0:
    dc.b    $1a,$c2
hint_1cf2:
; --- unverified ---
    cmp.b #$29,d1
    bne.w loc_0fb2
hint_1cfa:
; --- unverified ---
    move.b (a4)+,d1
    rts
hint_1cfe:
; --- unverified ---
    moveq #0,d1
    move.b (a4)+,d1
    movea.l #sub_a764,a1
    tst.b 0(a1,d1.w)
    beq.w hint_192a
hint_1d10:
; --- unverified ---
    bset #6,d5
str_1d14:
    rts
hint_1d16:
; --- unverified ---
    bsr.w hint_4f1a
hint_1d1a:
; --- unverified ---
    bra.s hint_1d20
hint_1d1c:
; --- unverified ---
    bsr.w hint_2372
hint_1d20:
; --- unverified ---
    bsr.w hint_187e
hint_1d24:
; --- unverified ---
    move.b d5,d0
    andi.w #$78,d0
    beq.s hint_1d38
hint_1d2c:
; --- unverified ---
    cmp.b #$20,d0
    bne.w hint_1742
hint_1d34:
    dc.b    $00,$06,$00,$08
hint_1d38:
; --- unverified ---
    andi.w #$7,d5
    or.w d5,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_1d46:
; --- unverified ---
    move.b (a4)+,d1
    move.w d0,-(sp)
    bsr.w hint_187e
hint_1d4e:
; --- unverified ---
    move.b d5,d0
    andi.w #$78,d0
    cmp.w (sp)+,d0
    bne.w hint_1742
hint_1d5a:
; --- unverified ---
    andi.w #$7,d5
    ror.w #7,d5
    or.w d5,d6
    move.w d6,(a5)+
    rts
hint_1d66:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_1d6c:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_1dd6
hint_1d72:
; --- unverified ---
    tst.b d4
    bne.s hint_1dd6
hint_1d76:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_1dd6
hint_1d7c:
; --- unverified ---
    cmp.l #$9,d2
    bcc.s hint_1dea
hint_1d84:
; --- unverified ---
    tst.l d2
    ble.s hint_1dea
hint_1d88:
; --- unverified ---
    subq.l #2,a5
    bsr.w sub_8dce
hint_1d8e:
; --- unverified ---
    bne.s hint_1dd4
hint_1d90:
; --- unverified ---
    andi.w #$4000,d6
    bchg #14,d6
    lsr.w #6,d6
    ori.w #$5000,d6
    bsr.w hint_4f1a
hint_1da2:
; --- unverified ---
    cmp.b #$8,d2
    bne.s hint_1daa
hint_1da8:
    dc.b    $74,$00
hint_1daa:
; --- unverified ---
    ror.w #7,d2
    or.w d2,d6
    move.b (a4)+,d1
    bsr.w hint_16e6
    dc.b    $00,$3f
sub_1db6:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_1dca
hint_1dbc:
    dc.b    $70,$00,$10,$2e,$02,$39,$10,$3b,$00,$0c,$d1,$6e,$01,$94
hint_1dca:
; --- unverified ---
    moveq #16,d0
    bra.w hint_8808
pcref_1dd0:
    dc.b    $02,$02,$02,$04
hint_1dd4:
    dc.b    $54,$8d
hint_1dd6:
    dc.b    $12,$1c
hint_1dd8:
; --- unverified ---
    bsr.w hint_1aa0
hint_1ddc:
; --- unverified ---
    bra.w hint_1e9c
hint_1de0:
; --- unverified ---
    btst #14,d6
    bne.s hint_1dd6
hint_1de6:
; --- unverified ---
    neg.l d2
    bra.s hint_1dd6
hint_1dea:
; --- unverified ---
    btst #1,270(a6) ; app+$10E
    beq.s hint_1dd6
hint_1df2:
; --- unverified ---
    btst #14,d6
    bne.s hint_1dfa
hint_1df8:
    dc.b    $44,$82
hint_1dfa:
; --- unverified ---
    movea.w d2,a0
    cmpa.l d2,a0
    bne.s hint_1de0
hint_1e00:
; --- unverified ---
    movem.l d2/d6,-(sp)
    cmp.b #$2c,d1
    bne.w hint_8462
hint_1e0c:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_4f1a
hint_1e12:
; --- unverified ---
    movem.l d1/a4,-(sp)
    bsr.w sub_177e
hint_1e1a:
; --- unverified ---
    bne.w hint_1e5e
hint_1e1e:
; --- unverified ---
    tst.b d0
    beq.w hint_1e5e
hint_1e24:
; --- unverified ---
    subq.l #2,a5
    bsr.w sub_8dce
hint_1e2a:
; --- unverified ---
    bne.s hint_1e5c
hint_1e2c:
; --- unverified ---
    addq.w #8,sp
    bsr.w hint_188c
hint_1e32:
; --- unverified ---
    ext.w d2
    move.w #$41e8,d6
    or.w d2,d6
    ror.w #7,d2
    or.w d2,d6
    move.w d6,(a5)+
    movem.l (sp)+,d2/d6
    move.w d2,(a5)+
    moveq #0,d0
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_1e52
hint_1e50:
    dc.b    $70,$02
hint_1e52:
; --- unverified ---
    add.w d0,404(a6) ; app+$194
    moveq #21,d0
    bra.w hint_8808
hint_1e5c:
    dc.b    $54,$4d
hint_1e5e:
; --- unverified ---
    movem.l (sp)+,d1/a4
    movem.l (sp)+,d2/d6
    btst #14,d6
    bne.s hint_1e6e
hint_1e6c:
    dc.b    $44,$82
hint_1e6e:
; --- unverified ---
    bra.w hint_1dd8
hint_1e72:
; --- unverified ---
    addq.l #2,a5
    cmp.b #$23,d1
    bne.s hint_1e8e
hint_1e7a:
; --- unverified ---
    btst #4,271(a6) ; app+$10F
    bne.w hint_1d66
hint_1e84:
; --- unverified ---
    btst #1,270(a6) ; app+$10E
    bne.w hint_1d66
hint_1e8e:
; --- unverified ---
    bsr.w sub_1872
hint_1e92:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_1e9a:
    dc.b    $12,$1c
hint_1e9c:
; --- unverified ---
    move.w d5,-(sp)
    bsr.w hint_187e
hint_1ea2:
; --- unverified ---
    move.w (sp)+,d4
    movea.l 588(a6),a0 ; app+$24C
    move.b d5,d2
    andi.b #$78,d2
    cmp.b #$8,d2
    beq.w hint_1f00
hint_1eb6:
; --- unverified ---
    cmp.b #$3c,d4
    beq.s hint_1eec
hint_1ebc:
; --- unverified ---
    bsr.w hint_4f1a
hint_1ec0:
; --- unverified ---
    move.w d6,(a0)
    tst.b d2
    bne.s hint_1ed6
hint_1ec6:
; --- unverified ---
    add.b d5,d5
    or.b d5,(a0)+
    cmp.b #$40,d4
    bcc.w hint_1742
hint_1ed2:
; --- unverified ---
    or.b d4,(a0)
    rts
hint_1ed6:
; --- unverified ---
    move.b d4,d0
    andi.b #$78,d0
    bne.w hint_1742
hint_1ee0:
; --- unverified ---
    add.b d4,d4
    addq.b #1,d4
    or.b d4,(a0)+
    or.b d5,(a0)
    moveq #60,d0
    bra.s hint_1efc
hint_1eec:
; --- unverified ---
    ror.w #5,d6
    andi.w #$700,d6
    bsr.w hint_4f1a
hint_1ef6:
    dc.b    $8c,$05,$30,$86,$70,$3d
hint_1efc:
; --- unverified ---
    bra.w hint_170a
hint_1f00:
; --- unverified ---
    ori.b #$c0,d6
    or.b d4,d6
    andi.w #$7,d5
    ror.w #7,d5
    or.w d5,d6
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_1f1a
hint_1f16:
    dc.b    $08,$c6,$00,$08
hint_1f1a:
; --- unverified ---
    move.w d6,(a0)
    move.w d4,d5
    cmp.b #$40,d5
    bcc.w hint_1742
hint_1f26:
; --- unverified ---
    cmpi.b #$1,569(a6) ; app+$239
    beq.w loc_844a
hint_1f30:
; --- unverified ---
    rts
hint_1f32:
; --- unverified ---
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_1f3e
hint_1f3a:
    dc.b    $00,$46,$01,$00
hint_1f3e:
; --- unverified ---
    bsr.w hint_16e6
    dc.b    $00,$ff
sub_1f44:
; --- unverified ---
    movem.l d3-d4,-(sp)
    cmp.b #$2c,d1
    bne.w hint_8462
hint_1f50:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_176a
hint_1f56:
; --- unverified ---
    movem.l (sp)+,d3-d4
    bne.w hint_1772
hint_1f5e:
; --- unverified ---
    add.b d2,d2
    movea.l 588(a6),a0 ; app+$24C
    or.b d2,(a0)
    bsr.s hint_1f26
hint_1f68:
; --- unverified ---
    btst #3,270(a6) ; app+$10E
    beq.s hint_1fb2
hint_1f70:
; --- unverified ---
    tst.b d4
    bne.s hint_1fb2
hint_1f74:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_1fb2
hint_1f7a:
; --- unverified ---
    move.w (a0),d3
    andi.w #$1ff,d3
    cmp.w #$1fc,d3
    bne.s hint_1fb2
hint_1f86:
; --- unverified ---
    move.l 2(a0),d0
    movea.w d0,a1
    cmp.l a1,d0
    bne.s hint_1fb2
hint_1f90:
; --- unverified ---
    movem.l d0/a0,-(sp)
    move.l d0,d2
    subq.w #2,a5
    bsr.w sub_8dce
hint_1f9c:
; --- unverified ---
    movem.l (sp)+,d0/a0
    bne.s hint_1fb0
hint_1fa2:
; --- unverified ---
    bclr #0,(a0)
    move.w d0,2(a0)
    moveq #23,d0
    bra.w hint_8808
hint_1fb0:
    dc.b    $54,$4d
hint_1fb2:
; --- unverified ---
    rts
hint_1fb4:
; --- unverified ---
    bsr.w hint_4f1a
hint_1fb8:
; --- unverified ---
    move.w d6,(a5)+
    cmp.b #$23,d1
    bne.w hint_846a
hint_1fc2:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_1a9c
hint_1fc8:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_1fd0:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
    dc.b    $00,$3d,$4e,$75,$0c,$2e,$00,$14,$01,$21,$6d,$d2,$61,$00,$2f,$36
    dc.b    $3a,$c6,$b2,$3c,$00,$23,$66,$00,$64,$7c,$12,$1c,$61,$00,$fa,$a8
    dc.b    $b2,$3c,$00,$2c,$66,$00,$64,$66,$12,$1c,$61,$00,$f6,$de,$00,$7d
    dc.b    $4e,$75
sub_2008:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    beq.w hint_20ca
hint_2010:
; --- unverified ---
    cmp.b #$1,d0
    beq.s hint_2064
hint_2016:
; --- unverified ---
    cmp.b #$2,d0
    beq.w hint_20b0
hint_201e:
; --- unverified ---
    tst.b 292(a6) ; app+$124
    bne.w hint_20b0
hint_2026:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.s hint_205c
hint_202e:
    dc.b    $50,$c6
hint_2030:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w sub_16a8
hint_2036:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_2058
hint_203c:
; --- unverified ---
    tst.b d4
    bne.s hint_2058
hint_2040:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_2052
hint_2046:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_2052
hint_204c:
; --- unverified ---
    moveq #30,d0
    bsr.w loc_8486
hint_2052:
    dc.b    $94,$ae,$02,$3c,$55,$82
hint_2058:
; --- unverified ---
    move.l d2,(a5)+
    rts
hint_205c:
; --- unverified ---
    moveq #5,d0
    bsr.w sign_extended_operand
hint_2062:
; --- unverified ---
    bra.s hint_20b0
hint_2064:
; --- unverified ---
    bsr.w hint_2130
hint_2068:
; --- unverified ---
    beq.s hint_2098
hint_206a:
; --- unverified ---
    lsr.w #8,d6
    move.b d6,(a5)+
    tst.w d3
    bmi.w dat_98e0
hint_2074:
; --- unverified ---
    tst.l d2
    bne.s hint_20a8
hint_2078:
; --- unverified ---
    cmp.b #$61,d6
    beq.s hint_209e
hint_207e:
; --- unverified ---
    btst #6,271(a6) ; app+$10F
    bne.s hint_208e
hint_2086:
; --- unverified ---
    moveq #83,d0
    bsr.w loc_8486
hint_208c:
; --- unverified ---
    bra.s hint_2094
hint_208e:
; --- unverified ---
    moveq #18,d0
    bsr.w hint_8808
hint_2094:
    dc.b    $2a,$6e,$02,$4c
hint_2098:
; --- unverified ---
    move.w #$4e71,(a5)+
    rts
hint_209e:
; --- unverified ---
    move.b #$ff,(a5)+
    moveq #63,d0
    bra.w loc_8486
hint_20a8:
; --- unverified ---
    bsr.w hint_78b0
hint_20ac:
; --- unverified ---
    move.b d2,(a5)+
    rts
hint_20b0:
; --- unverified ---
    bsr.w hint_2130
sub_20b4: ; jt: pcref_0ea2
    beq.s loc_20c6
loc_20b6:
    move.w d6,(a5)+
    tst.w d3
    bmi.w loc_98ee
loc_20be:
    bsr.w sub_78bc
loc_20c2:
    move.w d2,(a5)+
    rts
loc_20c6:
    addq.l #4,a5
    rts
hint_20ca:
; --- unverified ---
    tst.b 300(a6) ; app+$12C
    bmi.s hint_2064
hint_20d0:
; --- unverified ---
    bne.w hint_2026
hint_20d4:
; --- unverified ---
    btst #0,271(a6) ; app+$10F
    beq.s hint_20b0
hint_20dc:
; --- unverified ---
    bsr.w sub_0db6
hint_20e0:
; --- unverified ---
    tst.b d4
    bne.s hint_212a
hint_20e4:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_20f0
hint_20ea:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_212a
hint_20f0:
; --- unverified ---
    move.l d2,-(sp)
    sub.l 572(a6),d2 ; app+$23C
    subq.l #4,d2
    beq.s hint_2128
hint_20fa:
; --- unverified ---
    bpl.s hint_20fe
hint_20fc:
    dc.b    $54,$82
hint_20fe:
; --- unverified ---
    move.b d2,d0
    ext.w d0
    ext.l d0
    cmp.l d0,d2
    bne.s hint_2128
hint_2108:
; --- unverified ---
    bsr.w sub_8dce
hint_210c:
; --- unverified ---
    bne.s hint_211a
hint_210e:
; --- unverified ---
    addq.l #4,sp
    or.b d2,d6
    move.w d6,(a5)+
    moveq #12,d0
    bra.w hint_8808
hint_211a:
; --- unverified ---
    btst #5,271(a6) ; app+$10F
    beq.s hint_2128
hint_2122:
; --- unverified ---
    moveq #17,d0
    bsr.w hint_8808
hint_2128:
    dc.b    $24,$1f
hint_212a:
; --- unverified ---
    pea sub_20b4(pc)
    bra.s hint_2134
hint_2130:
; --- unverified ---
    bsr.w sub_0db6
hint_2134:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_214a
hint_213a:
; --- unverified ---
    tst.b d4
    bne.s hint_216c
hint_213e:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_216c
hint_2144:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_216c
hint_214a:
; --- unverified ---
    tst.w d3
    bmi.s hint_216c
hint_214e:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_215a
hint_2154:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_2172
hint_215a:
; --- unverified ---
    btst #0,d2
    beq.s hint_2166
hint_2160:
; --- unverified ---
    moveq #35,d0
    bsr.w loc_8486
hint_2166:
    dc.b    $94,$ae,$02,$3c,$55,$82
hint_216c:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    rts
hint_2172:
; --- unverified ---
    moveq #33,d0
    bsr.w loc_8486
hint_2178:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    rts
hint_217e:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_2186:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_218c:
; --- unverified ---
    tst.l d2
    bmi.s hint_219e
hint_2190:
; --- unverified ---
    cmp.l #$8,d2
    bcc.s hint_219e
hint_2198:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    rts
hint_219e:
; --- unverified ---
    move.w d6,(a5)+
    moveq #29,d0
    bra.w loc_8486
hint_21a6:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_21b0:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    beq.w sub_3132
hint_21ba:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_21c2:
; --- unverified ---
    bsr.w loc_1760
hint_21c6:
; --- unverified ---
    andi.w #$ff,d2
    ror.w #4,d2
    move.w d2,d5
    cmp.b #$2c,d1
    bne.w hint_8462
hint_21d6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_2258
hint_21da:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w d5,2(a0)
    rts
hint_21e4:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_21ee:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    beq.w sub_3132
hint_21f8:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_2200:
; --- unverified ---
    move.w d6,(a5)+
    addq.l #2,a5
    bsr.w hint_16e0
hint_2208:
; --- unverified ---
    ori.w #$7a00,-(a5)
    bsr.s hint_2266
hint_220e:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2216:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_221c:
; --- unverified ---
    andi.w #$ff,d2
    ror.w #4,d2
    or.w d2,d5
    movea.l 588(a6),a0 ; app+$24C
    move.w d5,2(a0)
    rts
hint_222e:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_2238:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    beq.w sub_3132
hint_2242:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_224a:
; --- unverified ---
    moveq #0,d5
    bsr.s hint_2258
hint_224e:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w d5,2(a0)
    rts
hint_2258:
; --- unverified ---
    move.w d6,(a5)+
    addq.l #2,a5
    move.w d5,-(sp)
    bsr.w hint_16e0
hint_2262:
    dc.b    $00,$25,$3a,$1f
hint_2266:
; --- unverified ---
    cmp.b #$7b,d1
    bne.s loc_2286
hint_226c:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_177e
hint_2272:
; --- unverified ---
    bne.s hint_228c
hint_2274:
; --- unverified ---
    tst.b d0
    bne.s loc_2286
hint_2278:
; --- unverified ---
    bset #11,d5
    andi.w #$ff,d2
    lsl.w #6,d2
    or.w d2,d5
    bra.s hint_22ae
loc_2286:
    moveq #85,d0
    bra.w loc_8482
hint_228c:
; --- unverified ---
    bsr.w sub_16cc
hint_2290:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_22ae
hint_2296:
; --- unverified ---
    tst.l d2
    bmi.s hint_22a2
hint_229a:
; --- unverified ---
    cmp.l #$20,d2
    bcs.s hint_22a6
hint_22a2:
; --- unverified ---
    bsr.w sub_78c6
hint_22a6:
    dc.b    $ed,$4a,$02,$42,$07,$c0,$8a,$42
hint_22ae:
; --- unverified ---
    cmp.b #$3a,d1
    bne.s loc_2286
    dc.b    $12,$1c
loc_22b6:
    bsr.w sub_177e
loc_22ba:
    bne.s loc_22c8
loc_22bc:
    tst.b d0
    bne.s loc_2286
loc_22c0:
    bset #5,d5
    or.b d2,d5
    bra.s loc_22ea
loc_22c8:
    bsr.w sub_16cc
loc_22cc:
    tst.b 568(a6) ; app+$238
    beq.s loc_22ea
loc_22d2:
    tst.l d2
    bne.s loc_22dc
loc_22d6:
    tst.b 288(a6) ; app+$120
    bne.s loc_22ea
loc_22dc:
    ble.s loc_22f4
loc_22de:
    cmp.l #$20,d2
    beq.s loc_22ea
loc_22e6:
    bgt.s loc_22f4
loc_22e8:
    or.w d2,d5
loc_22ea:
    cmp.b #$7d,d1
    bne.s loc_2286
loc_22f0:
    move.b (a4)+,d1
    rts
loc_22f4:
    bsr.w sub_78c6
loc_22f8:
    bra.s loc_22ea
    dc.b    $50,$ee,$02,$3b,$b2,$3c,$00
    dc.b    "#g",$22,"a",0
    dc.b    $f4,$5a,$2f,$0c,$b2,$3c,$00,$2c,$66,$00,$61,$52,$12,$1c,$d4,$02
    dc.b    $52,$02,$42,$67,$1a,$c2,$1a,$c6,$61,$00,$f3,$c0,$00,$fd,$60,$20
    dc.b    $3a,$c6,$12,$1c,$61,$00,$ea,$8a,$2f,$0c,$3f,$02,$61,$00,$f7,$b4
    dc.b    $b2,$3c,$00,$2c,$66,$00,$61,$26,$12,$1c,$61,$00,$f3,$9e,$00,$7d
hint_2346:
; --- unverified ---
    move.w (sp)+,d2
    movea.l (sp)+,a2
    andi.w #$38,d5
    bne.s hint_2356
hint_2350:
; --- unverified ---
    moveq #3,d0
    bra.w hint_2ff2
hint_2356:
; --- unverified ---
    cmp.w #$8,d2
    bcs.s hint_2372
hint_235c:
; --- unverified ---
    tst.b 286(a6) ; app+$11E
    beq.s hint_2372
hint_2362:
; --- unverified ---
    movea.l a2,a4
    bpl.s hint_236c
hint_2366:
; --- unverified ---
    moveq #106,d0
    bra.w loc_8486
hint_236c:
; --- unverified ---
    moveq #9,d0
    bsr.w sign_extended_operand
hint_2372:
; --- unverified ---
    moveq #1,d0
    bra.w hint_2ff2
hint_2378:
; --- unverified ---
    st 571(a6) ; app+$23B
    cmp.b #$23,d1
    beq.s hint_23a4
hint_2382:
; --- unverified ---
    bsr.w loc_1760
hint_2386:
; --- unverified ---
    move.l a4,-(sp)
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2390:
; --- unverified ---
    move.b (a4)+,d1
    add.b d2,d2
    addq.b #1,d2
    clr.w -(sp)
    move.b d2,(a5)+
    move.b d6,(a5)+
    bsr.w hint_16e0
    dc.b    $00,$3d,$60,$a2
hint_23a4:
; --- unverified ---
    move.w d6,(a5)+
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_23ac:
; --- unverified ---
    move.l a4,-(sp)
    move.w d2,-(sp)
    bsr.w hint_1ae8
hint_23b4:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_23bc:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
    dc.b    $00,$3d,$60,$80
hint_23c6:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_23d0:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    beq.s hint_23da
hint_23d6:
; --- unverified ---
    bsr.w loc_844a
hint_23da:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_23e2:
; --- unverified ---
    move.b (a4)+,d1
    move.w d6,(a5)+
    bsr.w sub_0db6
hint_23ea:
; --- unverified ---
    bsr.w hint_1ae8
hint_23ee:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_23f6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
hint_23fc:
; --- unverified ---
    ori.w #$4e75,-(a4)
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_240a:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    beq.w sub_3132
hint_2414:
; --- unverified ---
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    add.w d0,d0
    or.w pcref_2454(pc,d0.w),d6
    bsr.w loc_1760
hint_2424:
; --- unverified ---
    moveq #0,d5
    move.b d2,d5
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2430:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_2436:
; --- unverified ---
    andi.w #$ff,d2
    lsl.w #6,d2
    or.w d2,d5
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2446:
; --- unverified ---
    move.b (a4)+,d1
    move.w d5,-(sp)
    bsr.w hint_16e6
hint_244e:
; --- unverified ---
    ori.b
    rts
pcref_2454:
    dc.b    $04,$00,$02,$00,$04,$00,$06,$00
hint_245c:
; --- unverified ---
    moveq #86,d0
    bra.w loc_8482
hint_2462:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_246c:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    beq.w sub_3132
hint_2476:
; --- unverified ---
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    cmp.b #$1,d0
    beq.w loc_844a
hint_2484:
; --- unverified ---
    cmp.b #$3,d0
    bne.s hint_248e
hint_248a:
    dc.b    $08,$c6,$00,$09
hint_248e:
; --- unverified ---
    move.w d6,(a5)+
    moveq #0,d5
    moveq #0,d6
    bsr.w loc_1760
hint_2498:
; --- unverified ---
    or.b d2,d5
    cmp.b #$3a,d1
    bne.s hint_245c
hint_24a0:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_24a6:
; --- unverified ---
    or.b d2,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_24b0:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_24e4
hint_24b4:
; --- unverified ---
    or.w d2,d5
    cmp.b #$3a,d1
    bne.s hint_245c
hint_24bc:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_24e4
hint_24c2:
; --- unverified ---
    or.w d2,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_24cc:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_24f0
hint_24d0:
; --- unverified ---
    or.w d2,d5
    cmp.b #$3a,d1
    bne.s hint_245c
hint_24d8:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_24f0
hint_24dc:
; --- unverified ---
    or.w d2,d6
    move.w d5,(a5)+
    move.w d6,(a5)+
    rts
hint_24e4:
; --- unverified ---
    bsr.w loc_1760
hint_24e8:
; --- unverified ---
    andi.w #$ff,d2
    lsl.w #6,d2
    rts
hint_24f0:
; --- unverified ---
    cmp.b #$28,d1
    bne.s hint_2516
hint_24f6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_177e
hint_24fc:
; --- unverified ---
    bne.s hint_2516
hint_24fe:
; --- unverified ---
    andi.w #$ff,d2
    tst.b d0
    beq.s hint_250a
hint_2506:
    dc.b    $00,$02,$00,$08
hint_250a:
; --- unverified ---
    ror.w #4,d2
    cmp.b #$29,d1
    bne.s hint_2516
hint_2512:
; --- unverified ---
    move.b (a4)+,d1
    rts
hint_2516:
; --- unverified ---
    bra.w loc_8432
hint_251a:
; --- unverified ---
    moveq #4,d7
    cmp.b #$23,d1
    bne.s hint_2534
hint_2522:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_2528:
; --- unverified ---
    move.l d2,d7
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2532:
    dc.b    $12,$1c
hint_2534:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_2596
hint_253a:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_2596
hint_2540:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_2596
hint_2546:
; --- unverified ---
    lea 1134(a6),a0 ; app+$46E
    bsr.w sub_76b8
hint_254e:
; --- unverified ---
    bne.w loc_8432
hint_2552:
; --- unverified ---
    moveq #2,d6
    cmp.b #$2e,d1
    bne.s hint_257a
hint_255a:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$42,d1
    beq.s hint_257c
hint_2568:
; --- unverified ---
    cmp.b #$57,d1
    beq.s hint_257c
hint_256e:
; --- unverified ---
    moveq #4,d6
    cmp.b #$4c,d1
    bne.w loc_844a
hint_2578:
; --- unverified ---
    bra.s hint_257c
hint_257a:
    dc.b    $53,$8c
hint_257c:
; --- unverified ---
    move.b (a4)+,d1
    move.l d7,d4
    add.l d6,d7
    movem.l d1/d7,-(sp)
    bsr.s hint_2598
hint_2588:
; --- unverified ---
    movem.l (sp)+,d1/d7
    cmp.b #$2c,d1
    bne.s hint_2596
hint_2592:
; --- unverified ---
    move.b (a4)+,d1
    bra.s hint_2546
hint_2596:
; --- unverified ---
    rts
hint_2598:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_25c8
hint_259e:
; --- unverified ---
    bsr.w sub_0bce
hint_25a2:
; --- unverified ---
    beq.w loc_8436
hint_25a6:
; --- unverified ---
    moveq #2,d3
    move.b 6(a0),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.s hint_25ba
hint_25b2:
; --- unverified ---
    lea 362(a6),a2 ; app+$16A
    bra.w sub_0cb6
hint_25ba:
; --- unverified ---
    lea 346(a6),a2 ; app+$15A
    tst.l (a2)
    bne.w sub_0d4c
hint_25c4:
; --- unverified ---
    bra.w loc_8442
hint_25c8:
; --- unverified ---
    bsr.w sub_0bce
hint_25cc:
; --- unverified ---
    bne.w loc_843a
hint_25d0:
; --- unverified ---
    bset #6,12(a1)
    bne.w loc_8436
hint_25da:
; --- unverified ---
    cmpi.b #$2,13(a1)
    bne.w loc_8436
hint_25e4:
; --- unverified ---
    cmp.l 8(a1),d4
    bne.w loc_843e
hint_25ec:
; --- unverified ---
    rts
hint_25ee:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w hint_274e
hint_25f8:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    beq.s hint_2610
hint_25fe:
; --- unverified ---
    cmp.b #$2,d0
    beq.s hint_2610
hint_2604:
; --- unverified ---
    cmp.b #$3,d0
    bne.w loc_844a
hint_260c:
    dc.b    $08,$86
hint_260e:
    dc.b    $00,$07
hint_2610:
; --- unverified ---
    bsr.w hint_16e6
hint_2618:
; --- unverified ---
    ori.b #$0,24134(a4)
    move.b (a4)+,d1
    bsr.w loc_1760
hint_2624:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    add.b d2,d2
    or.b d2,(a0)
    rts
hint_262e:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_2638:
; --- unverified ---
    move.w d6,d5
    bclr #11,d6
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    add.w d0,d0
    or.w pcref_2672(pc,d0.w),d6
    move.w d6,(a5)+
    andi.w #$800,d5
    move.w d5,(a5)+
    bsr.w hint_16e0
hint_2656:
; --- unverified ---
    ori.w #$b23c,-(a4)
    ori.b #$0,24068(a4)
    move.b (a4)+,d1
    bsr.w hint_4a3c
hint_2666:
; --- unverified ---
    asl.b #4,d2
    movea.l 588(a6),a0 ; app+$24C
    or.b d2,2(a0)
    rts
pcref_2672:
; --- unverified ---
    andi.b #$0,d0
    andi.b #$0,d0
    moveq #0,d5
    bra.s hint_2682
hint_267e:
; --- unverified ---
    move.w #$800,d5
hint_2682:
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_268c:
; --- unverified ---
    bsr.w hint_2350
hint_2690:
; --- unverified ---
    move.w d6,(a5)+
    move.w d5,(a5)+
    bsr.w hint_16e0
hint_269c:
; --- unverified ---
    ori.b #$0,24002(a4)
    move.b (a4)+,d1
    bsr.w loc_1760
hint_26a8:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    cmp.b #$3a,d1
    bne.s hint_26c8
hint_26b2:
; --- unverified ---
    move.b (a4)+,d1
    or.b d2,3(a0)
    bsr.w loc_1760
hint_26bc:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    lsl.b #4,d2
    or.b d2,2(a0)
    rts
hint_26c8:
; --- unverified ---
    moveq #37,d0
    bra.w loc_8486
hint_26ce:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.s hint_274e
hint_26d6:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    beq.s hint_274e
hint_26dc:
; --- unverified ---
    cmp.b #$2,d0
    beq.s hint_274e
hint_26e2:
; --- unverified ---
    cmp.b #$3,d0
    bne.w loc_844a
hint_26ea:
; --- unverified ---
    btst #8,d6
    sne d5
    ext.w d5
    andi.w #$800,d5
    btst #14,d6
    seq d6
    ext.w d6
    andi.w #$40,d6
    ori.w #$4c00,d6
    move.w d6,(a5)+
    move.w d5,(a5)+
    bsr.w hint_16e0
hint_2718:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_271e:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    cmp.b #$3a,d1
    beq.s hint_2734
hint_2728:
; --- unverified ---
    or.b d2,3(a0)
    lsl.b #4,d2
    or.b d2,2(a0)
    rts
hint_2734:
; --- unverified ---
    move.b (a4)+,d1
    or.b d2,3(a0)
    bsr.w loc_1760
hint_273e:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    lsl.b #4,d2
    bset #2,d2
    or.b d2,2(a0)
    rts
hint_274e:
; --- unverified ---
    bsr.w hint_16e6
    dc.b    $00,$fd
hint_2754:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_275c:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_2762:
    dc.b    $20,$6e,$02,$4c,$d4,$02,$85,$10
hint_276a:
; --- unverified ---
    moveq #2,d0
    bra.w hint_2ff2
hint_2770:
; --- unverified ---
    bsr.w hint_4f1a
hint_2774:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w sub_1872
hint_277a:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2782:
; --- unverified ---
    move.b (a4)+,d1
    move.w d5,-(sp)
    bsr.w hint_187e
hint_278a:
; --- unverified ---
    move.w (sp)+,d4
    movea.l 588(a6),a0 ; app+$24C
    move.w d5,d0
    andi.b #$78,d0
    beq.s hint_27e2
hint_2798:
; --- unverified ---
    cmp.b #$8,d0
    beq.s hint_27f2
hint_279e:
; --- unverified ---
    cmp.b #$3c,d4
    beq.s hint_2818
hint_27a4:
; --- unverified ---
    move.b d4,d0
    andi.b #$78,d0
    cmp.b #$18,d0
    bne.s hint_27de
hint_27b0:
; --- unverified ---
    move.b d5,d0
    andi.b #$78,d0
    cmp.b #$18,d0
    bne.s hint_27de
hint_27bc:
; --- unverified ---
    move.w #$b108,d6
    bsr.w hint_4f1a
hint_27c4:
; --- unverified ---
    move.b d4,d0
    andi.b #$7,d0
    or.b d0,d6
    move.b d5,d0
    andi.w #$7,d0
    ror.w #7,d0
    or.w d0,d6
    movea.l 588(a6),a0 ; app+$24C
    move.w d6,(a0)
    rts
hint_27de:
; --- unverified ---
    bra.w hint_1742
hint_27e2:
; --- unverified ---
    add.b d5,d5
    or.b d5,(a0)
    move.w d4,d5
    or.w d5,(a0)
    move.w #$ff,d0
    bra.w hint_170a
hint_27f2:
; --- unverified ---
    andi.b #$7,d5
    add.b d5,d5
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_2802
hint_2800:
    dc.b    $52,$05
hint_2802:
; --- unverified ---
    or.b d5,(a0)
    move.w d4,d5
    ori.w #$c0,d4
    or.w d4,(a0)
    move.w #$ff,d0
    bsr.w hint_170a
hint_2814:
; --- unverified ---
    bra.w hint_1f26
hint_2818:
; --- unverified ---
    move.w #$c00,d6
    bsr.w hint_4f1a
hint_2820:
; --- unverified ---
    or.w d5,d6
    move.w d6,(a0)
    moveq #61,d0
    bra.w hint_170a
hint_282a:
; --- unverified ---
    bsr.w hint_4f1a
hint_282e:
; --- unverified ---
    bsr.s hint_2846
hint_2830:
; --- unverified ---
    or.b d5,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_283a:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_2846
hint_283e:
; --- unverified ---
    ror.w #7,d5
    or.w d5,d6
    move.w d6,(a5)+
    rts
hint_2846:
; --- unverified ---
    bsr.w hint_187e
hint_284a:
; --- unverified ---
    move.b d5,d0
    andi.b #$78,d0
    cmp.b #$18,d0
    bne.w hint_1742
hint_2858:
; --- unverified ---
    andi.w #$7,d5
    rts
hint_285e:
; --- unverified ---
    bsr.w hint_6ad2
hint_2862:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_286a:
; --- unverified ---
    move.b (a4)+,d1
    move.l d2,d5
    bsr.w hint_6ad2
hint_2872:
; --- unverified ---
    move.l d2,d0
    beq.s hint_288e
hint_2876:
; --- unverified ---
    bmi.s hint_28b4
hint_2878:
; --- unverified ---
    move.l d2,-(sp)
    move.l 572(a6),d2 ; app+$23C
    move.l (sp),d0
    bsr.w sub_11b2
hint_2884:
; --- unverified ---
    move.l (sp)+,d2
    tst.l d0
    beq.s hint_288e
hint_288a:
    dc.b    $90,$82,$44,$80
hint_288e:
; --- unverified ---
    add.l d5,d0
    move.l d0,d4
    beq.s hint_28a4
hint_2894:
; --- unverified ---
    cmp.l #$80,d0
    bcc.s hint_28b4
hint_289c:
; --- unverified ---
    move.b #$0,(a5)+
    subq.b #1,d0
    bne.s hint_289c
hint_28a4:
; --- unverified ---
    add.l 572(a6),d4 ; app+$23C
    lea 1000(a6),a0 ; app+$3E8
    tst.l (a0)
    bne.w loc_0c84
hint_28b2:
; --- unverified ---
    rts
hint_28b4:
; --- unverified ---
    moveq #29,d0
    bra.w loc_8486
hint_28ba:
; --- unverified ---
    lea -1(a4),a1
    cmp.b #$a,d1
    beq.s hint_28de
hint_28c4:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    bne.s hint_28c4
hint_28cc:
; --- unverified ---
    move.l a4,d2
    sub.l a1,d2
    subq.w #1,d2
    tst.b 568(a6) ; app+$238
    beq.s hint_28de
hint_28d8:
; --- unverified ---
    bsr.w hint_96ec
hint_28dc:
    dc.b    $72,$0a
hint_28de:
; --- unverified ---
    rts
hint_28e0:
; --- unverified ---
    bsr.w loc_1760
hint_28e4:
; --- unverified ---
    or.b d2,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_28ee:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_276a
hint_28f4:
; --- unverified ---
    bra.w hint_20b0
hint_28f8:
; --- unverified ---
    move.w d1,-(sp)
    move.b 569(a6),d0 ; app+$239
    beq.s hint_2906
hint_2900:
; --- unverified ---
    cmp.b #$1,d0
    beq.s hint_2916
hint_2906:
; --- unverified ---
    bsr.w loc_0c64
hint_290a:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    bne.s hint_2912
hint_2910:
    dc.b    $70,$02
hint_2912:
; --- unverified ---
    move.w (sp)+,d1
    rts
hint_2916:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    tst.l (a0)
    beq.s hint_2926
hint_291e:
; --- unverified ---
    move.l 572(a6),d4 ; app+$23C
    bsr.w loc_0c84
hint_2926:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    bra.s hint_2912
hint_292c:
; --- unverified ---
    bsr.s hint_28f8
hint_292e:
; --- unverified ---
    bsr.w hint_6ad2
hint_2932:
; --- unverified ---
    cmp.b #$2c,d1
    beq.s hint_293e
hint_2938:
; --- unverified ---
    move.l d2,-(sp)
    moveq #0,d2
    bra.s hint_2946
hint_293e:
; --- unverified ---
    move.b (a4)+,d1
    move.l d2,-(sp)
    bsr.w hint_6ad2
hint_2946:
    dc.b    $76,$00,$41,$fa,$01,$8e,$22,$02,$16,$2e,$02,$39,$16,$30,$30,$00
    dc.b    $28,$1f
hint_2958:
; --- unverified ---
    clr.l 386(a6) ; app+$182
    tst.b 259(a6) ; app+$103
    beq.s hint_2968
hint_2962:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_297e
hint_2968:
; --- unverified ---
    lsl.l d3,d4
    bpl.w hint_2974
hint_296e:
; --- unverified ---
    moveq #84,d0
    bra.w loc_8482
hint_2974:
    dc.b    $2d,$44,$01,$8e
pcref_2978:
; --- unverified ---
    move.b -1(a4),d1
    rts
hint_297e:
; --- unverified ---
    move.b #$ff,2107(a6) ; app+$83B
    move.l 572(a6),2108(a6) ; app+$23C
    bsr.w sub_972e
hint_298e:
; --- unverified ---
    beq.s hint_2968
hint_2990:
; --- unverified ---
    clr.l 398(a6) ; app+$18E
    subq.l #1,d4
    bcs.s pcref_2978
hint_2998:
; --- unverified ---
    pea pcref_2978(pc)
    subq.b #1,d3
    bcs.s hint_29ca
hint_29a0:
; --- unverified ---
    beq.s hint_29b6
hint_29a2:
; --- unverified ---
    move.l d1,(a5)+
    moveq #4,d5
    bsr.s hint_29de
hint_29a8:
; --- unverified ---
    dbf d4,hint_29a2
hint_29ac:
; --- unverified ---
    subi.l #$10000,d4
    bcc.s hint_29a2
hint_29b4:
; --- unverified ---
    rts
hint_29b6:
; --- unverified ---
    move.w d1,(a5)+
    moveq #2,d5
    bsr.s hint_29de
hint_29bc:
; --- unverified ---
    dbf d4,hint_29b6
hint_29c0:
; --- unverified ---
    subi.l #$10000,d4
    bcc.s hint_29b6
hint_29c8:
; --- unverified ---
    rts
hint_29ca:
; --- unverified ---
    move.b d1,(a5)+
    moveq #1,d5
    bsr.s hint_29de
hint_29d0:
; --- unverified ---
    dbf d4,hint_29ca
hint_29d4:
; --- unverified ---
    subi.l #$10000,d4
    bcc.s hint_29ca
hint_29dc:
; --- unverified ---
    rts
hint_29de:
; --- unverified ---
    move.l d1,-(sp)
    move.l d5,d1
    move.l 572(a6),d2 ; app+$23C
    add.l 398(a6),d2 ; app+$18E
    bsr.w loc_970e
hint_29ee:
; --- unverified ---
    add.l d5,398(a6) ; app+$18E
    move.l (sp)+,d1
    movea.l 588(a6),a5 ; app+$24C
    rts
hint_29fa:
; --- unverified ---
    bsr.w hint_28f8
hint_29fe:
; --- unverified ---
    cmp.b #$1,d0
    beq.w hint_2a62
hint_2a06:
; --- unverified ---
    cmp.b #$3,d0
    beq.s hint_2a26
hint_2a0c:
; --- unverified ---
    cmp.b #$2,d0
    beq.s hint_2a1a
hint_2a12:
; --- unverified ---
    bsr.w hint_5b16
hint_2a16:
; --- unverified ---
    bsr.s hint_2a32
hint_2a18:
; --- unverified ---
    bra.s hint_2a12
hint_2a1a:
; --- unverified ---
    bsr.w sub_0db6
hint_2a1e:
; --- unverified ---
    bsr.w hint_1ad0
hint_2a22:
; --- unverified ---
    bsr.s hint_2a32
hint_2a24:
; --- unverified ---
    bra.s hint_2a1a
hint_2a26:
; --- unverified ---
    bsr.w sub_0db6
hint_2a2a:
; --- unverified ---
    bsr.w hint_1ab0
hint_2a2e:
; --- unverified ---
    bsr.s hint_2a32
hint_2a30:
; --- unverified ---
    bra.s hint_2a26
hint_2a32:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_2a5e
hint_2a38:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s hint_2a48
hint_2a40:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_2a48
hint_2a46:
; --- unverified ---
    rts
hint_2a48:
; --- unverified ---
    moveq #11,d0
    bsr.w sign_extended_operand
hint_2a4e:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s hint_2a4e
hint_2a56:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_2a4e
hint_2a5c:
; --- unverified ---
    rts
hint_2a5e:
; --- unverified ---
    addq.l #4,sp
    rts
hint_2a62:
; --- unverified ---
    cmp.b #$27,d1
    beq.s hint_2a8c
hint_2a68:
; --- unverified ---
    cmp.b #$22,d1
    beq.s hint_2a8c
hint_2a6e:
; --- unverified ---
    bsr.w sub_0db6
hint_2a72:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_2a80
hint_2a78:
; --- unverified ---
    tst.w d3
    bmi.s hint_2a86
hint_2a7c:
; --- unverified ---
    bsr.w sub_788c
hint_2a80:
    dc.b    $1a,$c2
hint_2a82:
; --- unverified ---
    bsr.s hint_2a32
hint_2a84:
; --- unverified ---
    bra.s hint_2a62
hint_2a86:
; --- unverified ---
    bsr.w dat_9954
hint_2a8a:
; --- unverified ---
    bra.s hint_2a82
hint_2a8c:
    dc.b    $16,$01,$48,$e7,$00,$0c
hint_2a92:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_2ad0
hint_2a9a:
; --- unverified ---
    cmp.b d3,d1
    bne.s hint_2aa4
hint_2a9e:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b d1,d3
    bne.s hint_2aa8
hint_2aa4:
; --- unverified ---
    move.b d1,(a5)+
    bra.s hint_2a92
hint_2aa8:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_2ac8
hint_2aae:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_2ac8
hint_2ab4:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_2ac8
hint_2aba:
; --- unverified ---
    cmp.b #$2c,d1
    beq.s hint_2ac8
hint_2ac0:
; --- unverified ---
    movem.l (sp)+,a4-a5
    move.b d3,d1
    bra.s hint_2a6e
hint_2ac8:
; --- unverified ---
    addq.l #8,sp
    bsr.w hint_2a32
hint_2ace:
; --- unverified ---
    bra.s hint_2a62
hint_2ad0:
; --- unverified ---
    addq.l #8,sp
    moveq #55,d0
    bra.w loc_8486
pcref_2ad8:
; --- unverified ---
    btst d0,d0
    btst d0,d2
    bsr.w hint_28f8
hint_2ae0:
; --- unverified ---
    ext.w d0
    move.b pcref_2ad8(pc,d0.w),d6
    bsr.w hint_6ad2
hint_2aea:
; --- unverified ---
    tst.l d2
    beq.s hint_2af8
hint_2aee:
; --- unverified ---
    move.l d2,d4
    move.b d6,d3
    moveq #0,d1
    bra.w hint_2958
hint_2af8:
; --- unverified ---
    rts
hint_2afa:
; --- unverified ---
    st 277(a6) ; app+$115
    moveq #10,d1
    rts
hint_2b02:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    tst.l (a0)
    beq.s hint_2b0c
hint_2b0a:
; --- unverified ---
    rts
hint_2b0c:
; --- unverified ---
    moveq #41,d0
    bra.w loc_8482
hint_2b12:
; --- unverified ---
    bsr.s hint_2b02
hint_2b14:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_2b4a
hint_2b1a:
; --- unverified ---
    move.l a0,-(sp)
    bsr.w hint_6ab2
hint_2b20:
; --- unverified ---
    movea.l (sp)+,a0
    movem.l d2-d3,-(sp)
    bsr.w sub_0bce
hint_2b2a:
; --- unverified ---
    movem.l (sp)+,d4-d5
    beq.w loc_8436
hint_2b32:
; --- unverified ---
    move.b d5,d3
    pea pcref_2b7a(pc)
    lea 362(a6),a2 ; app+$16A
    subq.b #2,d5
    beq.w sub_0cb6
hint_2b42:
; --- unverified ---
    lea 354(a6),a2 ; app+$162
    bra.w sub_0cb6
hint_2b4a:
; --- unverified ---
    bsr.w sub_0bce
hint_2b4e:
; --- unverified ---
    bne.w loc_844e
hint_2b52:
; --- unverified ---
    btst #6,12(a1)
    bne.w loc_8436
hint_2b5c:
; --- unverified ---
    move.l a1,-(sp)
    bsr.w sub_16a8
hint_2b62:
; --- unverified ---
    movea.l (sp)+,a1
    cmp.l 8(a1),d2
    bne.w loc_843e
hint_2b6c:
; --- unverified ---
    cmp.b 13(a1),d3
    bne.w loc_8436
hint_2b74:
    dc.b    $08,$e9,$00,$06,$00,$0c
pcref_2b7a:
    dc.b    $12,$2c,$ff,$ff
hint_2b7e:
; --- unverified ---
    move.b #$3d,2107(a6) ; app+$83B
    move.l d2,2108(a6) ; app+$83C
    rts
hint_2b8a:
; --- unverified ---
    moveq #45,d0
    bra.w loc_8486
hint_2b90:
; --- unverified ---
    moveq #46,d0
    bra.w loc_8486
hint_2b96:
; --- unverified ---
    bsr.w hint_2b02
hint_2b9a:
; --- unverified ---
    bsr.w sub_177e
hint_2b9e:
; --- unverified ---
    bne.s hint_2b90
hint_2ba0:
; --- unverified ---
    swap d2
    move.w d0,d2
    swap d2
    andi.l #$ff00ff,d2
    movea.l 362(a6),a2 ; app+$16A
    lea 1000(a6),a0 ; app+$3E8
    movem.l d2/a3-a5,-(sp)
    tst.b 568(a6) ; app+$238
    bne.s sub_2bd4
    dc.b    $61,$00
sub_2bc0: ; jt: pcref_0ea2
    adda.l a0,a7
    movem.l (sp)+,d4/a3-a5
    beq.w loc_8436
loc_2bca:
    moveq #4,d3
    bsr.w sub_0cba
loc_2bd0:
    moveq #10,d1
    rts
sub_2bd4:
; --- unverified ---
    bsr.w sub_0b88
hint_2bd8:
; --- unverified ---
    movem.l (sp)+,d4/a3-a5
    bne.w loc_843a
hint_2be0:
; --- unverified ---
    cmpi.b #$4,13(a1)
    bne.w loc_8436
hint_2bea:
; --- unverified ---
    cmp.l 8(a1),d4
    bne.w loc_8436
hint_2bf2:
; --- unverified ---
    bset #6,12(a1)
    bne.w loc_8436
hint_2bfc:
; --- unverified ---
    moveq #10,d1
    rts
hint_2c00:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_2c08:
; --- unverified ---
    move.w #$a,d1
    rts
hint_2c0e:
; --- unverified ---
    bsr.w hint_2350
hint_2c12:
; --- unverified ---
    bsr.w sub_177e
hint_2c16:
; --- unverified ---
    bne.s hint_2c5c
hint_2c18:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2c20:
; --- unverified ---
    move.b (a4)+,d1
    movem.w d0/d2,-(sp)
    bsr.w sub_177e
hint_2c2a:
; --- unverified ---
    movem.w (sp)+,d3-d4
    bne.s hint_2c5c
hint_2c30:
; --- unverified ---
    cmp.b d0,d3
    beq.s hint_2c4c
hint_2c34:
; --- unverified ---
    ori.b #$88,d6
    tst.b d3
    beq.s hint_2c3e
hint_2c3c:
    dc.b    $c9,$42
hint_2c3e:
; --- unverified ---
    or.b d2,d6
    andi.w #$7,d4
    ror.w #7,d4
    or.w d4,d6
    move.w d6,(a5)+
    rts
hint_2c4c:
; --- unverified ---
    ori.b #$40,d6
    tst.b d0
    beq.s hint_2c3e
hint_2c54:
; --- unverified ---
    ori.b #$8,d6
    exg
    bra.s hint_2c3e
hint_2c5c:
; --- unverified ---
    addq.l #2,a5
    moveq #46,d0
    bra.w loc_8486
hint_2c64:
; --- unverified ---
    bsr.w hint_1f26
hint_2c68:
; --- unverified ---
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_2c74
hint_2c70:
    dc.b    $00,$06,$00,$40
hint_2c74:
; --- unverified ---
    bsr.w loc_1760
hint_2c78:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    rts
hint_2c7e:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_2c88:
; --- unverified ---
    bsr.w hint_2350
sub_2c8c:
    bsr.w loc_1760
loc_2c90:
    or.b d2,d6
    move.w d6,(a5)+
    rts
    dc.b    $10,$2e,$02,$39,$67,$f0,$b0,$3c,$00,$02,$67,$ea
loc_2ca2: ; jt: pcref_0ea2
    cmp.b #$3,d0
    bne.w loc_844a
loc_2caa:
    bset #6,d6
    bra.s sub_2c8c
sub_2cb0:
; --- unverified ---
    moveq #10,d1
    moveq #56,d0
    bra.w loc_8486
hint_2cb8:
    dc.b    $41,$ee,$0c,$24
hint_2cbc:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_2cfe
hint_2cc2:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_2cfe
hint_2cc8:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_2cfe
hint_2cce:
; --- unverified ---
    subi.b #$30,d1
    bcs.s hint_2d00
hint_2cd4:
; --- unverified ---
    cmp.b #$8,d1
    bcc.s hint_2d00
hint_2cda:
; --- unverified ---
    moveq #7,d0
    sub.b d1,d0
    move.b (a4)+,d1
    cmp.b #$2b,d1
    beq.s hint_2cf0
hint_2ce6:
; --- unverified ---
    cmp.b #$2d,d1
    bne.s hint_2d00
hint_2cec:
; --- unverified ---
    bclr d0,(a0)
    bra.s hint_2cf2
hint_2cf0:
    dc.b    $01,$d0
hint_2cf2:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$2c,d1
    bne.s hint_2cfe
hint_2cfa:
; --- unverified ---
    move.b (a4)+,d1
    bra.s hint_2cbc
hint_2cfe:
; --- unverified ---
    rts
hint_2d00:
; --- unverified ---
    moveq #76,d0
    bra.w loc_8486
hint_2d06:
; --- unverified ---
    bsr.w hint_6ad2
hint_2d0a:
; --- unverified ---
    tst.l d2
    beq.w loc_0c44
hint_2d10:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_2d1c
hint_2d16:
; --- unverified ---
    cmp.b #$20,d1
    bne.s hint_2d20
hint_2d1c:
; --- unverified ---
    move.b (a4)+,d1
    bra.s hint_2d10
hint_2d20:
; --- unverified ---
    bsr.w loc_0a38
hint_2d24:
; --- unverified ---
    lea pcref_2d2e(pc),a0
    move.l a0,378(a6) ; app+$17A
    moveq #10,d1
pcref_2d2e:
    rts
hint_2d30:
; --- unverified ---
    tst.b 283(a6) ; app+$11B
    bne.w sub_845a
hint_2d38:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    moveq #0,d3
    bsr.w sub_7818
hint_2d42:
; --- unverified ---
    lea 1006(a6),a0 ; app+$3EE
    clr.b 266(a6) ; app+$10A
    jsr sub_afde
hint_2d50:
; --- unverified ---
    bne.w hint_2dd8
hint_2d54:
; --- unverified ---
    move.l d3,394(a6) ; app+$18A
    move.l d2,398(a6) ; app+$18E
    beq.s hint_2dc6
hint_2d5e:
; --- unverified ---
    cmp.l #$ffffffff,d2
    bne.s hint_2d90
hint_2d66:
; --- unverified ---
    movea.l 418(a6),a0 ; app+$1A2
    move.l 12(a0),d1
    movea.l 8(a0),a0
    sub.l a0,d1
    move.l d1,398(a6) ; app+$18E
    tst.b 568(a6) ; app+$238
    beq.s hint_2dc6
hint_2d7e:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s hint_2dc6
hint_2d84:
; --- unverified ---
    move.l 572(a6),d2 ; app+$23C
    bsr.w sub_9772
hint_2d8c:
; --- unverified ---
    bra.w hint_2dc6
hint_2d90:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_2dc6
hint_2d96:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s hint_2dc6
hint_2d9c:
; --- unverified ---
    move.l d2,d1
    bsr.w sub_90ba
hint_2da2:
; --- unverified ---
    move.l a0,-(sp)
    move.l 398(a6),d1 ; app+$18E
    move.l 394(a6),d3 ; app+$18A
    jsr call_read_aff6
hint_2db2:
; --- unverified ---
    move.l 398(a6),d1 ; app+$18E
    movea.l (sp),a0
    move.l 572(a6),d2 ; app+$23C
    bsr.w sub_9772
hint_2dc0:
; --- unverified ---
    movea.l (sp)+,a0
    bsr.w hint_90ce
hint_2dc6:
; --- unverified ---
    move.l 394(a6),d3 ; app+$18A
    clr.l 394(a6) ; app+$18A
    jsr sub_aff2
hint_2dd4:
; --- unverified ---
    moveq #10,d1
    rts
hint_2dd8:
; --- unverified ---
    moveq #26,d0
    bra.w loc_8486
hint_2dde:
; --- unverified ---
    lea 2098(a6),a3 ; app+$832
    st 299(a6) ; app+$12B
    bra.w loc_4698
hint_2df4:
; --- unverified ---
    st 266(a6) ; app+$10A
    bsr.w sub_8856
hint_2dfc:
; --- unverified ---
    bne.w loc_846e
hint_2e00:
; --- unverified ---
    moveq #10,d1
    rts
hint_2e04:
; --- unverified ---
    bsr.w hint_16e6
hint_2e08:
; --- unverified ---
    ori.w #$4a2e,-(a4)
    andi.b #$0,$563a4e75
    st 571(a6) ; app+$23B
    bsr.w hint_16e6
hint_2e1c:
    dc.b    $00,$64,$51,$ee,$02,$3b,$b2,$3c,$00,$2c,$66,$00,$56,$3a
hint_2e2a:
; --- unverified ---
    movem.l d3-d4,-(sp)
    move.b (a4)+,d1
    bsr.w sub_177e
hint_2e34:
; --- unverified ---
    movem.l (sp)+,d3-d4
    bne.w hint_1772
hint_2e3c:
; --- unverified ---
    tst.b d0
    beq.w hint_1772
hint_2e42:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    add.b d2,d2
    or.b d2,(a0)
    bsr.w hint_2350
pcref_2e4e:
; --- unverified ---
    btst #2,270(a6) ; app+$10E
    beq.s hint_2ec0
hint_2e56:
; --- unverified ---
    tst.b d4
    bne.s hint_2ec0
hint_2e5a:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_2ec0
hint_2e60:
; --- unverified ---
    move.w (a0),d3
    andi.w #$38,d3
    cmp.b #$28,d3
    bne.s hint_2ec0
hint_2e6c:
; --- unverified ---
    move.w 2(a0),d0
    beq.s hint_2ec0
hint_2e72:
; --- unverified ---
    cmp.w #$8,d0
    bgt.s hint_2ec0
hint_2e78:
; --- unverified ---
    cmp.w #$fff8,d0
    blt.s hint_2ec0
hint_2e7e:
; --- unverified ---
    move.w (a0),d3
    andi.w #$7,d3
    add.w d3,d3
    cmp.b d3,d2
    bne.s hint_2ec0
hint_2e8a:
; --- unverified ---
    movem.l d0/a0,-(sp)
    move.l d0,d2
    subq.w #2,a5
    bsr.w sub_8dce
hint_2e96:
; --- unverified ---
    movem.l (sp)+,d0/a0
    bne.s hint_2ebe
hint_2e9c:
; --- unverified ---
    lsr.w #1,d3
    tst.w d0
    bpl.s hint_2ea8
hint_2ea2:
    dc.b    $08,$c3,$00,$08,$44,$40
hint_2ea8:
; --- unverified ---
    andi.w #$7,d0
    ror.w #7,d0
    or.w d0,d3
    ori.w #$5048,d3
    move.w d3,(a0)
    moveq #22,d0
    bra.w hint_8808
hint_2ebc:
; --- unverified ---
    rts
hint_2ebe:
    dc.b    $54,$4d
hint_2ec0:
; --- unverified ---
    rts
hint_2ec2:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.s hint_2f12
hint_2eca:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    beq.s hint_2f1a
hint_2ed0:
; --- unverified ---
    cmp.b #$2,d0
    beq.s hint_2f1a
hint_2ed6:
; --- unverified ---
    cmp.b #$3,d0
    bne.w loc_844a
hint_2ede:
; --- unverified ---
    move.w #$4808,d6
    bsr.w sub_176a
hint_2ee6:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2ef2:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$23,d1
    bne.w hint_846a
hint_2efc:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_2f02:
; --- unverified ---
    bsr.w hint_1ab0
hint_2f06:
; --- unverified ---
    btst #0,d2
    bne.s hint_2f4a
hint_2f0c:
; --- unverified ---
    tst.l d2
    bgt.s hint_2f4a
hint_2f10:
; --- unverified ---
    rts
hint_2f12:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_2f1a:
; --- unverified ---
    bsr.w sub_176a
hint_2f1e:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2f2a:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$23,d1
    bne.w hint_846a
hint_2f34:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_2f3a:
; --- unverified ---
    bsr.w hint_1ad0
hint_2f3e:
; --- unverified ---
    btst #0,d2
    bne.s hint_2f4a
hint_2f44:
; --- unverified ---
    tst.w d2
    bgt.s hint_2f4a
hint_2f48:
; --- unverified ---
    rts
hint_2f4a:
; --- unverified ---
    moveq #3,d0
    bra.w sign_extended_operand
hint_2f50:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_2f56:
; --- unverified ---
    bsr.w sub_788c
hint_2f5a:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_2f70
hint_2f60:
; --- unverified ---
    tst.b 2389(a6) ; app+$955
    beq.s hint_2f70
hint_2f66:
; --- unverified ---
    move.w d1,-(sp)
    move.b d2,d1
    bsr.w sub_917c
hint_2f6e:
    dc.b    $32,$1f
hint_2f70:
; --- unverified ---
    cmp.b #$2c,d1
    beq.s hint_2f50
hint_2f76:
; --- unverified ---
    st 275(a6) ; app+$113
    rts
hint_2f7c:
; --- unverified ---
    bsr.w hint_6ad2
hint_2f80:
; --- unverified ---
    cmp.l #$26,d2
    bcs.w hint_4814
hint_2f8a:
; --- unverified ---
    cmp.l #$ff,d2
    bcc.w hint_4814
hint_2f94:
; --- unverified ---
    move.w d2,2914(a6) ; app+$B62
    st 275(a6) ; app+$113
    rts
hint_2f9e:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_2fa6:
; --- unverified ---
    move.b (a4)+,d1
hint_2fa8:
    bsr.w hint_4f1a
hint_2fac:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w hint_1a9c
hint_2fb2:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_2fba:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
    dc.b    $03,$3d,$4e,$75
sub_2fc4:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    addq.l #1,a0
    subq.b #1,d5
    beq.s hint_2fe2
hint_2fce:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_2fda
hint_2fd4:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_2fda:
; --- unverified ---
    move.b #$7c,(a0)
    moveq #2,d0
    bra.s hint_2ff2
hint_2fe2:
; --- unverified ---
    move.b #$3c,(a0)+
    cmpi.b #$3,569(a6) ; app+$239
    beq.w loc_844a
hint_2ff0:
; --- unverified ---
    rts
hint_2ff2:
; --- unverified ---
    cmp.b 569(a6),d0 ; app+$239
    beq.s hint_3004
hint_2ff8:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_3000:
    dc.b    $1d,$40,$02,$39
hint_3004:
; --- unverified ---
    rts
hint_3006:
; --- unverified ---
    move.b (a4)+,d1
    move.w d6,d0
    move.w #$200,d6
    cmp.w #$c000,d0
    beq.s hint_2fa8
hint_3014:
; --- unverified ---
    moveq #0,d6
    cmp.w #$8000,d0
    beq.s hint_2fa8
hint_301c:
; --- unverified ---
    move.w #$a00,d6
    bra.s hint_2fa8
hint_3022:
; --- unverified ---
    cmp.b #$23,d1
    beq.s hint_3006
hint_3028:
; --- unverified ---
    bsr.w hint_4f1a
hint_302c:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w sub_1872
hint_3032:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_303a:
; --- unverified ---
    move.b (a4)+,d1
    move.b d5,d0
    andi.b #$78,d0
    bne.w hint_3086
hint_3046:
; --- unverified ---
    add.b d5,d5
    addq.b #1,d5
    or.b d5,-2(a5)
    bsr.w hint_187e
hint_3052:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w #$3c,d0
    move.b d5,d2
    andi.b #$78,d2
    bne.s hint_3080
hint_3062:
; --- unverified ---
    move.w #$fd,d0
    btst #13,d6
    bne.s hint_3080
hint_306c:
; --- unverified ---
    move.b (a0),d0
    lsr.b #1,d0
    andi.w #$7,d0
    or.w d0,(a0)
    add.b d5,d5
    andi.w #$f0ff,(a0)
    or.b d5,(a0)
    rts
hint_3080:
; --- unverified ---
    or.w d5,(a0)
    bra.w hint_170a
hint_3086:
; --- unverified ---
    btst #13,d6
    bne.w hint_1742
hint_308e:
; --- unverified ---
    move.w #$fd,d0
    bsr.w hint_1704
hint_3096:
; --- unverified ---
    bsr.w loc_1760
hint_309a:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    add.b d2,d2
    or.b d2,(a0)
    rts
hint_30a4:
    dc.b    $22,$4c,$41,$fa,$00,$ba
hint_30aa:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b (a0)+,d1
    bne.w hint_3144
hint_30b6:
; --- unverified ---
    move.b (a4)+,d1
    tst.b (a0)
    bne.s hint_30aa
hint_30bc:
; --- unverified ---
    subi.b #$30,d1
    bcs.s sub_3132
hint_30c2:
; --- unverified ---
    cmp.b #$a,d1
    bcc.s sub_3132
hint_30c8:
; --- unverified ---
    moveq #0,d2
    move.b d1,d2
    mulu.w #$a,d2
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s sub_3132
hint_30d8:
; --- unverified ---
    cmp.b #$a,d1
    bcc.s sub_3132
hint_30de:
; --- unverified ---
    ext.w d1
    add.w d1,d2
    move.b (a4)+,d1
    mulu.w #$a,d2
    subi.b #$30,d1
    bcs.s sub_3132
hint_30ee:
; --- unverified ---
    cmp.b #$a,d1
    bcc.s sub_3132
hint_30f4:
; --- unverified ---
    ext.w d1
    add.w d1,d2
    move.b (a4)+,d1
    tst.w d2
    beq.s hint_313a
hint_30fe:
; --- unverified ---
    cmp.w #$8,d2
    beq.s hint_3138
hint_3104:
; --- unverified ---
    cmp.w #$a,d2
    beq.s hint_313a
hint_310a:
; --- unverified ---
    cmp.w #$14,d2
    beq.s hint_313a
hint_3110:
; --- unverified ---
    cmp.w #$1e,d2
    beq.s hint_313a
hint_3116:
; --- unverified ---
    cmp.w #$14c,d2
    beq.s hint_315e
hint_311c:
; --- unverified ---
    cmp.w #$28,d2
    beq.s hint_3128
hint_3122:
; --- unverified ---
    cmp.w #$3c,d2
    bne.s sub_3132
hint_3128:
; --- unverified ---
    move.b d2,289(a6) ; app+$121
    st 290(a6) ; app+$122
    rts
sub_3132:
    moveq #34,d0
    bra.w loc_8486
hint_3138:
    dc.b    $74,$00
hint_313a:
; --- unverified ---
    move.b d2,289(a6) ; app+$121
    sf 290(a6) ; app+$122
    rts
hint_3144:
    dc.b    $28,$49,$12,$2c,$ff,$ff,$41,$fa,$00,$1b
hint_314e:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b (a0)+,d1
    bne.s sub_3132
hint_3158:
; --- unverified ---
    move.b (a4)+,d1
    tst.b (a0)
    bne.s hint_314e
hint_315e:
; --- unverified ---
    moveq #32,d2
    bra.s hint_313a
str_3162:
    dc.b    "MC68",0
str_3167:
    dc.b    "CPU32",0
    dc.b    $00
sub_316e:
    moveq #0,d2
loc_3170:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.s loc_3194
loc_3178:
    cmp.b #$3a,d1
    bcc.s loc_3194
loc_317e:
    subi.b #$30,d1
    ext.w d1
    ext.l d1
    add.l d2,d2
    move.l d2,d0
    add.l d2,d2
    add.l d2,d2
    add.l d0,d2
    add.l d1,d2
    bra.s loc_3170
loc_3194:
    subi.l #$109a0,d2
    bcs.s loc_31e2
loc_319c:
    beq.s loc_3204
loc_319e:
    cmp.l #$384,d2
    bgt.s loc_31e2
loc_31a6:
    cmp.w #$8,d2
    beq.s loc_3204
loc_31ac:
    cmp.w #$a,d2
    beq.s loc_3204
loc_31b2:
    cmp.w #$14,d2
    beq.s loc_3204
loc_31b8:
    cmp.w #$1e,d2
    beq.s loc_3204
loc_31be:
    cmp.w #$14c,d2
    beq.s loc_31e4
loc_31c4:
    cmp.w #$28,d2
    beq.s loc_31fe
loc_31ca:
    cmp.w #$3c,d2
    beq.s loc_31fe
loc_31d0:
    cmp.w #$371,d2
    beq.s loc_31f6
loc_31d6:
    cmp.w #$372,d2
    beq.s loc_31ee
loc_31dc:
    cmp.w #$353,d2
    beq.s loc_31e8
loc_31e2:
    rts
loc_31e4:
    moveq #32,d2
    bra.s loc_3204
loc_31e8:
    st 291(a6) ; app+$123
    bra.s loc_320c
loc_31ee:
    move.b #$52,290(a6) ; app+$122
    bra.s loc_320c
loc_31f6:
    move.b #$51,290(a6) ; app+$122
    bra.s loc_320c
loc_31fe:
    st 290(a6) ; app+$122
    bra.s loc_3208
loc_3204:
    sf 290(a6) ; app+$122
loc_3208:
    move.b d2,289(a6) ; app+$121
loc_320c:
    cmp.b #$2f,d1
    beq.w sub_316e
loc_3214:
    moveq #0,d0
    rts
    dc.b    $61,$00,$1d,$00,$b2,$3c,$00,$23,$66,$00,$52,$48,$12,$1c,$61,$00
    dc.b    $e4,$a4,$61,$16,$ee,$5a,$8c,$42,$b2,$3c,$00,$2c,$66,$00,$52,$2c
    dc.b    $12,$1c,$61,$00,$e4,$aa,$00,$3f,$4e,$75
sub_3242:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_3258
hint_3248:
; --- unverified ---
    tst.l d2
    beq.s hint_325a
hint_324c:
; --- unverified ---
    cmp.l #$8,d2
    bhi.s hint_3260
hint_3254:
; --- unverified ---
    bne.s hint_3258
hint_3256:
    dc.b    $74,$00
hint_3258:
; --- unverified ---
    rts
hint_325a:
; --- unverified ---
    tst.b 288(a6) ; app+$120
    bne.s hint_3258
hint_3260:
; --- unverified ---
    moveq #29,d0
    bra.w loc_8486
hint_3266:
; --- unverified ---
    bsr.w hint_4e06
hint_326a:
; --- unverified ---
    move.w 540(a6),d2 ; app+$21C
    cmp.w #$3,d2
    beq.s hint_3294
hint_3274:
; --- unverified ---
    btst #1,d2
    bne.s hint_329c
hint_327a:
; --- unverified ---
    cmp.w #$5,d2
    beq.s hint_329c
hint_3280:
; --- unverified ---
    tst.w d2
    bne.s hint_3296
hint_3284:
; --- unverified ---
    bsr.w sub_79da
hint_3288:
; --- unverified ---
    movea.l a4,a0
    move.b -1(a4),d1
    bsr.w loc_78e8
hint_3292:
    dc.b    $72,$0a
hint_3294:
; --- unverified ---
    rts
hint_3296:
; --- unverified ---
    moveq #6,d0
    bra.w sign_extended_operand
hint_329c:
; --- unverified ---
    lea 430(a6),a2 ; app+$1AE
    bsr.w hint_4dae
hint_32a4:
; --- unverified ---
    sf 275(a6) ; app+$113
    rts
hint_32aa:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_32b0:
; --- unverified ---
    tst.b d4
    bne.w hint_3336
hint_32b6:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_3336
hint_32bc:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_3336
hint_32c2:
; --- unverified ---
    move.l d2,d4
    move.l a4,-(sp)
    move.b (a4)+,d1
    bsr.w sub_177e
hint_32cc:
; --- unverified ---
    bne.s hint_3330
hint_32ce:
; --- unverified ---
    tst.b d0
    bne.s hint_3302
hint_32d2:
; --- unverified ---
    move.l d4,d0
    ext.w d0
    ext.l d0
    cmp.l d0,d4
    bne.s hint_3330
hint_32dc:
; --- unverified ---
    btst #3,271(a6) ; app+$10F
    beq.w hint_3330
hint_32e6:
; --- unverified ---
    subq.l #2,a5
    bsr.w sub_8dce
hint_32ec:
; --- unverified ---
    bne.s hint_332e
hint_32ee:
; --- unverified ---
    addq.l #4,sp
    ori.b #$38,d2
    add.b d2,d2
    lsl.w #8,d2
    or.b d4,d2
    move.w d2,(a5)+
    moveq #15,d0
    bra.w hint_8808
hint_3302:
; --- unverified ---
    movea.w d4,a0
    cmp.l a0,d4
    bne.s hint_3330
hint_3308:
; --- unverified ---
    btst #3,270(a6) ; app+$10E
    beq.w hint_3330
hint_3312:
; --- unverified ---
    subq.l #2,a5
    bsr.w sub_8dce
hint_3318:
; --- unverified ---
    bne.s hint_332e
hint_331a:
; --- unverified ---
    addq.l #4,sp
    add.b d2,d2
    lsl.w #8,d2
    ori.w #$307c,d2
    move.w d2,(a5)+
    move.w d4,(a5)+
    moveq #23,d0
    bra.w hint_8808
hint_332e:
    dc.b    $54,$8d
hint_3330:
    dc.b    $28,$5f,$72,$2c,$24,$04
hint_3336:
; --- unverified ---
    bsr.w hint_1aa0
hint_333a:
; --- unverified ---
    bra.s hint_3376
pcref_333c:
; --- unverified ---
    move.w d0,d0
    move.b d0,d0
    move.w d0,d0
    move.l d0,d0
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    add.b d0,d0
    or.w pcref_333c(pc,d0.w),d6
    move.w d6,(a5)+
    cmp.b #$6,d0
    bne.s hint_3372
hint_3358:
; --- unverified ---
    cmp.b #$23,d1
    bne.s hint_3372
hint_335e:
; --- unverified ---
    btst #3,271(a6) ; app+$10F
    bne.w hint_32aa
hint_3368:
; --- unverified ---
    btst #3,270(a6) ; app+$10E
    bne.w hint_32aa
hint_3372:
; --- unverified ---
    bsr.w sub_1872
hint_3376:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_337e:
; --- unverified ---
    move.b (a4)+,d1
    btst #6,d5
    bne.w hint_3432
hint_3388:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    or.w d5,(a0)
    bsr.w hint_187e
hint_3392:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    btst #6,d5
    bne.s hint_33c2
hint_339c:
; --- unverified ---
    move.w d5,d2
    move.w d5,d0
    andi.b #$7,d0
    add.b d0,d0
    or.b d0,(a0)
    andi.w #$38,d5
    add.w d5,d5
    add.w d5,d5
    add.w d5,d5
    or.w d5,(a0)
    andi.w #$3f,d2
    cmp.w #$3a,d2
    bcc.w hint_1742
hint_33c0:
; --- unverified ---
    rts
hint_33c2:
; --- unverified ---
    move.w (a0),d4
    lsr.b #1,d5
    bcs.s hint_33f4
hint_33c8:
; --- unverified ---
    lsr.b #1,d5
    bcs.s hint_341c
hint_33cc:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_33d8
hint_33d2:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_33d8:
; --- unverified ---
    move.b d4,d0
    andi.b #$38,d0
    cmp.b #$8,d0
    bne.w hint_1742
hint_33e6:
; --- unverified ---
    andi.w #$7,d4
    ori.w #$4e60,d4
    move.w d4,(a0)
    bra.w hint_2350
hint_33f4:
; --- unverified ---
    move.w #$44c0,d6
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_3404
hint_3400:
; --- unverified ---
    bsr.w loc_844a
hint_3404:
; --- unverified ---
    andi.w #$3f,d4
    move.b d4,d0
    andi.b #$38,d0
    cmp.b #$8,d0
    beq.w hint_1742
hint_3416:
; --- unverified ---
    or.w d4,d6
    move.w d6,(a0)
    rts
hint_341c:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_3428
hint_3422:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_3428:
; --- unverified ---
    bsr.w hint_276a
hint_342c:
; --- unverified ---
    move.w #$46c0,d6
    bra.s hint_3404
hint_3432:
; --- unverified ---
    movea.l 588(a6),a2 ; app+$24C
    lsr.b #1,d5
    bcs.s sub_3474
hint_343a:
; --- unverified ---
    lsr.b #1,d5
    bcs.s hint_345a
hint_343e:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_344a
hint_3444:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_344a:
; --- unverified ---
    bsr.w sub_176a
hint_344e:
; --- unverified ---
    move.w #$4e68,d6
    or.b d2,d6
    move.w d6,(a2)
    bra.w hint_2350
hint_345a:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_3466
hint_3460:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_3466:
; --- unverified ---
    move.w #$40c0,(a2)
    bsr.w hint_16e0
    dc.b    $00,$3d,$60,$00,$f2,$f8
sub_3474:
; --- unverified ---
    tst.b 289(a6) ; app+$121
    bne.s hint_3482
hint_347a:
; --- unverified ---
    bsr.s hint_3466
hint_347c:
; --- unverified ---
    moveq #4,d0
    bra.w sign_extended_operand
hint_3482:
; --- unverified ---
    move.w #$42c0,(a2)
    bsr.w hint_16e0
    dc.b    $00,$3d
sub_348c:
; --- unverified ---
    cmpi.b #$3,569(a6) ; app+$239
    beq.w loc_844a
hint_3496:
; --- unverified ---
    rts
hint_3498:
; --- unverified ---
    tst.b 289(a6) ; app+$121
    beq.w sub_3132
hint_34a0:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_34ac
hint_34a6:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_34ac:
; --- unverified ---
    bsr.w hint_2350
hint_34b0:
; --- unverified ---
    bsr.w sub_177e
hint_34b4:
; --- unverified ---
    bne.s hint_34dc
hint_34b6:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_34be:
; --- unverified ---
    move.b (a4)+,d1
    move.w #$4e7b,(a5)+
    lsl.b #3,d0
    or.b d0,d2
    andi.w #$f,d2
    ror.w #4,d2
    move.w d2,d3
    bsr.s hint_3508
hint_34d2:
; --- unverified ---
    bne.w hint_845e
hint_34d6:
; --- unverified ---
    or.w d3,d2
    move.w d2,(a5)+
    rts
hint_34dc:
; --- unverified ---
    bsr.s hint_3508
hint_34de:
; --- unverified ---
    bne.w hint_845e
hint_34e2:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_34ea:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,d3
    bsr.w sub_177e
hint_34f2:
; --- unverified ---
    bne.w hint_845e
hint_34f6:
; --- unverified ---
    move.w d6,(a5)+
    lsl.b #3,d0
    or.b d0,d2
    andi.w #$f,d2
    ror.w #4,d2
    or.w d2,d3
    move.w d3,(a5)+
    rts
hint_3508:
    dc.b    $10,$01,$48,$80,$10,$36,$00,$7e,$41,$fa,$00,$b4,$74,$00
hint_3516:
; --- unverified ---
    move.b (a0)+,d2
    beq.w hint_35c2
hint_351c:
; --- unverified ---
    cmp.b (a0),d0
    bne.w hint_35ba
hint_3522:
    dc.b    $48,$e7,$a0,$88,$52,$88
hint_3528:
; --- unverified ---
    move.b (a4)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b (a0)+,d0
    bne.w hint_35b6
hint_3536:
; --- unverified ---
    subq.b #1,d2
    bne.s hint_3528
hint_353a:
; --- unverified ---
    lea 16(sp),sp
    move.b (a0)+,d2
    lsl.w #8,d2
    move.b (a0)+,d2
    move.b (a4)+,d1
    move.b 289(a6),d0 ; app+$121
    beq.s hint_356a
hint_354c:
; --- unverified ---
    cmp.b #$28,d0
    beq.s hint_358e
hint_3552:
; --- unverified ---
    cmp.b #$3c,d0
    beq.s hint_3574
hint_3558:
; --- unverified ---
    cmp.b #$20,d0
    beq.s hint_3564
hint_355e:
; --- unverified ---
    cmp.b #$a,d0
    bne.s hint_35a2
hint_3564:
; --- unverified ---
    cmp.b #$2,d2
    bcs.s hint_3570
hint_356a:
; --- unverified ---
    moveq #34,d0
    bsr.w loc_8486
hint_3570:
; --- unverified ---
    moveq #0,d0
    rts
hint_3574:
; --- unverified ---
    cmp.w #$803,d2
    beq.s hint_356a
hint_357a:
; --- unverified ---
    cmp.w #$804,d2
    beq.s hint_356a
hint_3580:
; --- unverified ---
    cmp.w #$805,d2
    beq.s hint_356a
hint_3586:
; --- unverified ---
    cmp.w #$802,d2
    bne.s hint_3570
hint_358c:
; --- unverified ---
    bra.s hint_356a
hint_358e:
; --- unverified ---
    cmp.w #$8,d2
    beq.s hint_356a
hint_3594:
; --- unverified ---
    cmp.w #$808,d2
    beq.s hint_356a
hint_359a:
; --- unverified ---
    cmp.w #$802,d2
    bne.s hint_3570
hint_35a0:
; --- unverified ---
    bra.s hint_356a
hint_35a2:
; --- unverified ---
    cmp.w #$805,d2
    bcc.s hint_356a
hint_35a8:
; --- unverified ---
    cmp.w #$800,d2
    bcc.s hint_3570
hint_35ae:
; --- unverified ---
    cmp.w #$3,d2
    bcs.s hint_3570
hint_35b4:
; --- unverified ---
    bra.s hint_356a
hint_35b6:
    dc.b    $4c,$df,$11,$05
hint_35ba:
; --- unverified ---
    lea 3(a0,d2.w),a0
    bra.w hint_3516
hint_35c2:
; --- unverified ---
    moveq #-1,d0
    rts
pcref_35c6:
    dc.b    $02,$53,$46,$43,$00,$00,$02,$44,$46,$43,$00,$01,$03,$43
    dc.b    $41,$43,$52,$00,$02,$02,$55,$53,$50,$08,$00,$02,$56,$42,$52,$08
    dc.b    $01,$03,$43,$41,$41,$52,$08,$02,$02,$4d,$53,$50,$08,$03,$02,$49
    dc.b    $53,$50,$08,$04,$01,$54,$43,$00,$03,$03
    dc.b    "ITT0",0
    dc.b    $04,$03
    dc.b    "ITT1",0
    dc.b    $05,$03
    dc.b    "DTT0",0
    dc.b    $06,$03
    dc.b    "DTT1",0
    dc.b    $07,$04,$4d,$4d
sub_361c:
    dc.b    $55,$53,$52,$08,$05,$02,$55,$52,$50,$08,$06,$02,$53,$52,$50,$08
    dc.b    $07,$04
    dc.b    "BUSCR",0
    dc.b    $08,$02,$50,$43,$52,$08,$08,$00,$10,$2e,$02,$39,$67,$12,$b0,$3c
    dc.b    $00,$02,$67,$0c
hint_3648:
; --- unverified ---
    cmp.b #$3,d0
    bne.w loc_844a
hint_3650:
    dc.b    $00,$06,$00,$40
hint_3654:
; --- unverified ---
    bsr.s hint_36c8
hint_3656:
; --- unverified ---
    bne.w hint_36a2
hint_365a:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_3662:
; --- unverified ---
    move.b (a4)+,d1
    move.w d6,(a5)+
    move.w d4,(a5)+
    bsr.w hint_187e
hint_366c:
; --- unverified ---
    cmp.w #$40,d5
    bcc.w hint_1742
hint_3674:
; --- unverified ---
    move.b d5,d2
    andi.b #$38,d2
    cmp.b #$20,d2
    bne.s hint_369c
hint_3680:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_369c
hint_3686:
    dc.b    $20,$6e,$02,$4c,$20,$10,$74,$00,$76,$0f
hint_3690:
; --- unverified ---
    lsl.w #1,d0
    roxr.w #1,d2
    dbf d3,hint_3690
hint_3698:
    dc.b    $31,$42,$00,$02
hint_369c:
; --- unverified ---
    moveq #52,d0
    bra.w hint_1704
hint_36a2:
; --- unverified ---
    ori.w #$400,d6
    move.w d6,(a5)+
    addq.l #2,a5
    bsr.w hint_16e0
hint_36ae:
; --- unverified ---
    ori.w #$b23c,44(a4)
    bne.w hint_8462
hint_36b8:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_36c8
hint_36bc:
; --- unverified ---
    bne.s hint_3736
hint_36be:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w d4,2(a0)
    rts
hint_36c8:
; --- unverified ---
    moveq #0,d4
    bsr.w sub_177e
hint_36ce:
; --- unverified ---
    beq.s hint_3718
hint_36d0:
; --- unverified ---
    lea 1134(a6),a0 ; app+$46E
    movem.l d1/a4,-(sp)
    bsr.w sub_76b8
hint_36dc:
; --- unverified ---
    bne.s hint_3712
hint_36de:
; --- unverified ---
    movea.l 362(a6),a2 ; app+$16A
    movem.l d1/d3/a3-a5,-(sp)
    bsr.w sub_0b88
hint_36ea:
; --- unverified ---
    movem.l (sp)+,d1/d3/a3-a5
    bne.s hint_3712
hint_36f0:
; --- unverified ---
    cmpi.b #$5,13(a1)
    bne.s hint_3712
hint_36f8:
; --- unverified ---
    move.l 8(a1),d4
    tst.b 568(a6) ; app+$238
    beq.s hint_370a
hint_3702:
; --- unverified ---
    btst #6,12(a1)
    beq.s hint_3710
hint_370a:
; --- unverified ---
    addq.l #8,sp
    moveq #0,d0
    rts
hint_3710:
    dc.b    $70,$ff
hint_3712:
; --- unverified ---
    movem.l (sp)+,d1/a4
    rts
hint_3718:
; --- unverified ---
    lsl.b #3,d0
    add.b d2,d0
    cmp.b #$2d,d1
    beq.s hint_373c
hint_3722:
    dc.b    $01,$c4
hint_3724:
; --- unverified ---
    cmp.b #$2f,d1
    beq.s hint_372e
hint_372a:
; --- unverified ---
    moveq #0,d0
    rts
hint_372e:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_177e
hint_3734:
; --- unverified ---
    beq.s hint_3718
hint_3736:
; --- unverified ---
    moveq #57,d0
    bra.w loc_8482
hint_373c:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$38,d1
    bcc.s hint_375a
hint_3744:
; --- unverified ---
    cmp.b #$30,d1
    bcs.s hint_375a
hint_374a:
; --- unverified ---
    move.b d0,d3
    andi.b #$8,d0
    subi.b #$30,d1
    add.b d1,d0
    move.b (a4)+,d1
    bra.s hint_3768
hint_375a:
; --- unverified ---
    move.w d0,-(sp)
    bsr.w sub_177e
hint_3760:
; --- unverified ---
    bne.s hint_3736
hint_3762:
    dc.b    $e7,$08,$d0,$02,$36,$1f
hint_3768:
; --- unverified ---
    cmp.b d3,d0
    bcs.s hint_3736
hint_376c:
    dc.b    $52,$00
hint_376e:
; --- unverified ---
    bset d3,d4
    addq.b #1,d3
    cmp.b d0,d3
    bne.s hint_376e
hint_3776:
; --- unverified ---
    bra.s hint_3724
hint_3778:
; --- unverified ---
    bsr.w hint_16e6
hint_378a:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_176a
hint_3790:
; --- unverified ---
    movem.l (sp)+,d3-d4
    add.b d2,d2
    movea.l 588(a6),a0 ; app+$24C
    or.b d2,(a0)
    move.b 569(a6),d0 ; app+$239
    beq.s hint_37b0
hint_37a2:
; --- unverified ---
    cmp.b #$3,d0
    beq.s hint_37b6
hint_37a8:
; --- unverified ---
    cmp.b #$2,d0
    bne.w loc_844a
hint_37b0:
; --- unverified ---
    ori.b #$10,(a0)
    rts
hint_37b6:
; --- unverified ---
    btst #3,270(a6) ; app+$10E
    beq.s hint_3800
hint_37be:
; --- unverified ---
    tst.b d4
    bne.s hint_3800
hint_37c2:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_3800
hint_37c8:
; --- unverified ---
    move.w (a0),d3
    andi.w #$3f,d3
    cmp.b #$3c,d3
    bne.s hint_3800
hint_37d4:
; --- unverified ---
    move.l 2(a0),d0
    movea.w d0,a1
    cmp.l a1,d0
    bne.s hint_3800
hint_37de:
; --- unverified ---
    movem.l d0/a0,-(sp)
    move.l d0,d2
    subq.w #2,a5
    bsr.w sub_8dce
hint_37ea:
; --- unverified ---
    movem.l (sp)+,d0/a0
    bne.s hint_37fe
hint_37f0:
; --- unverified ---
    ori.b #$10,(a0)
    move.w d0,2(a0)
    moveq #23,d0
    bra.w hint_8808
hint_37fe:
    dc.b    $54,$4d
hint_3800:
; --- unverified ---
    rts
hint_3802:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    cmp.b #$1,d0
    beq.w loc_844a
hint_380e:
; --- unverified ---
    cmp.b #$3,d0
    bne.s hint_3818
hint_3814:
    dc.b    $00,$06,$00,$40
hint_3818:
; --- unverified ---
    bsr.w sub_177e
hint_381c:
; --- unverified ---
    bne.s hint_3842
hint_381e:
; --- unverified ---
    tst.b d0
    bne.w hint_385c
hint_3824:
; --- unverified ---
    ori.b #$80,d6
    andi.w #$7,d2
    ror.w #7,d2
    or.w d2,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_3838:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_3862
hint_383c:
; --- unverified ---
    move.w d6,(a5)+
    move.w d3,(a5)+
    rts
hint_3842:
; --- unverified ---
    bsr.s hint_3862
hint_3844:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_384c:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_3852:
; --- unverified ---
    andi.w #$7,d2
    ror.w #7,d2
    or.w d2,d6
    bra.s hint_383c
hint_385c:
; --- unverified ---
    moveq #47,d0
    bra.w loc_8486
hint_3862:
; --- unverified ---
    moveq #0,d2
    cmpi.b #$14,289(a6) ; app+$121
    blt.s hint_38a6
hint_386c:
; --- unverified ---
    cmp.b #$28,d1
    bne.s hint_38ac
hint_3872:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,d3
    bsr.w sub_176a
hint_387a:
; --- unverified ---
    bne.s hint_3892
hint_387c:
; --- unverified ---
    or.b d2,d6
    cmp.b #$2c,d1
    bne.s hint_38c4
hint_3884:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16a8
hint_388a:
; --- unverified ---
    bsr.w hint_78b6
hint_388e:
; --- unverified ---
    move.w d2,d3
    bra.s hint_38c4
hint_3892:
; --- unverified ---
    bsr.w sub_16a8
hint_3896:
; --- unverified ---
    bsr.w hint_78b6
hint_389a:
; --- unverified ---
    move.w d2,d3
    cmp.b #$2c,d1
    bne.s hint_385c
hint_38a2:
; --- unverified ---
    bra.w hint_38ba
hint_38a6:
; --- unverified ---
    cmp.b #$28,d1
    beq.s hint_38ba
hint_38ac:
; --- unverified ---
    bsr.w sub_16a8
hint_38b0:
; --- unverified ---
    bsr.w hint_78b6
hint_38b4:
; --- unverified ---
    cmp.b #$28,d1
    bne.s hint_385c
hint_38ba:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,d3
    bsr.w sub_176a
hint_38c2:
    dc.b    $8c,$02
hint_38c4:
; --- unverified ---
    cmp.b #$29,d1
    bne.s hint_385c
hint_38ca:
; --- unverified ---
    move.b (a4)+,d1
    rts
hint_38ce:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_38d6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_38dc:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_3910
hint_38e2:
; --- unverified ---
    bsr.w hint_78d8
hint_38e6:
; --- unverified ---
    tst.w d3
    bmi.s hint_392c
hint_38ea:
; --- unverified ---
    move.b d2,d0
    ext.w d0
    ext.l d0
    cmp.l d0,d2
    beq.s hint_3910
hint_38f4:
; --- unverified ---
    cmp.l #$100,d2
    bcs.s hint_3902
hint_38fc:
; --- unverified ---
    bsr.w sub_8456
hint_3900:
; --- unverified ---
    bra.s hint_3910
hint_3902:
; --- unverified ---
    cmpi.b #$3,569(a6) ; app+$239
    beq.s hint_3910
hint_390a:
; --- unverified ---
    moveq #1,d0
    bsr.w sign_extended_operand
hint_3910:
; --- unverified ---
    move.b d2,d6
    cmp.b #$2c,d1
    bne.w hint_8462
hint_391a:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_3920:
; --- unverified ---
    add.b d2,d2
    moveq #112,d0
    or.b d2,d0
    move.b d0,(a5)+
    move.b d6,(a5)+
    rts
hint_392c:
; --- unverified ---
    move.l d2,-(sp)
    cmp.b #$2c,d1
    bne.w hint_8462
hint_3936:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_393c:
; --- unverified ---
    add.b d2,d2
    moveq #112,d0
    or.b d2,d0
    move.b d0,(a5)+
    move.l (sp)+,d2
    bra.w dat_9954
hint_394a:
; --- unverified ---
    cmpi.b #$a,289(a6) ; app+$121
    blt.w sub_3132
hint_3954:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_3960
hint_395a:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_3960:
; --- unverified ---
    bsr.w hint_4f1a
hint_3964:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w sub_177e
hint_396a:
; --- unverified ---
    bne.s hint_3984
hint_396c:
; --- unverified ---
    moveq #1,d3
    bsr.s hint_39ac
hint_3970:
; --- unverified ---
    move.w d3,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_397a:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
hint_3980:
    dc.b    $00,$3c,$4e,$75
hint_3984:
; --- unverified ---
    addq.l #2,a5
    bsr.w hint_16e0
hint_398a:
; --- unverified ---
    ori.b
    ori.b #$0,19152(a4)
    move.b (a4)+,d1
    bsr.w sub_177e
hint_399a:
; --- unverified ---
    bne.w hint_2b90
hint_399e:
; --- unverified ---
    moveq #0,d3
    bsr.s hint_39ac
hint_39a2:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w d3,2(a0)
    rts
hint_39ac:
; --- unverified ---
    add.b d2,d2
    tst.b d0
    sne d0
    andi.b #$10,d0
    or.b d0,d3
    or.b d2,d3
    ror.w #5,d3
    rts
hint_39be:
; --- unverified ---
    bsr.w hint_2372
hint_39c2:
; --- unverified ---
    bsr.w hint_16e6
    dc.b    $00,$3d,$4e,$75
sub_39ca:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_39d6
hint_39d0:
; --- unverified ---
    cmp.b #$20,d1
    bne.s hint_39da
hint_39d6:
; --- unverified ---
    move.b (a4)+,d1
    bra.s sub_39ca
hint_39da:
; --- unverified ---
    moveq #0,d2
    cmp.b #$a,d1
    beq.s hint_39f2
hint_39e2:
; --- unverified ---
    cmp.b #$2a,d1
    beq.s hint_39f2
hint_39e8:
; --- unverified ---
    cmp.b #$3b,d1
    beq.s hint_39f2
hint_39ee:
; --- unverified ---
    bsr.w hint_6ad2
hint_39f2:
; --- unverified ---
    move.l d2,-(sp)
    bsr.w sub_79cc
hint_39f8:
    dc.b    $24,$1f,$43,$ee,$02,$56,$2d,$49,$01,$42,$23,$42,$00,$08,$42,$29
    dc.b    $00,$0e,$2d,$42,$02,$3c,$41,$ee,$05,$a8,$2d,$48,$02,$4c,$1d,$7c
    dc.b    $00,$02,$01,$08,$50,$ee,$01,$1b,$12,$2c,$ff,$ff
sub_3a24:
    rts
hint_3a26:
; --- unverified ---
    bsr.w hint_6ad2
hint_3a2a:
; --- unverified ---
    move.l d2,-(sp)
    bsr.w hint_999e
hint_3a30:
; --- unverified ---
    movem.l (sp)+,d2
    bne.s hint_3a66
hint_3a36:
; --- unverified ---
    move.l d2,572(a6) ; app+$23C
    lea pcref_9884(pc),a0
    move.l a0,378(a6) ; app+$17A
    move.b -1(a4),d1
    st 274(a6) ; app+$112
    sf 284(a6) ; app+$11C
    move.b #$e,264(a6) ; app+$108
    move.b 569(a6),d0 ; app+$239
    beq.s hint_3a64
hint_3a5a:
; --- unverified ---
    cmp.b #$3,d0
    beq.s hint_3a64
hint_3a60:
    dc.b    $50,$ee,$01,$1c
hint_3a64:
; --- unverified ---
    rts
hint_3a66:
; --- unverified ---
    moveq #69,d0
    bra.w loc_8486
sub_3a6c:
    move.b (a4)+,d1
    beq.s loc_3a90
loc_3a70:
    cmp.b #$20,d1
    beq.s sub_3a6c
loc_3a76:
    cmp.b #$a,d1
    beq.s loc_3a90
loc_3a7c:
    cmp.b #$2b,d1
    beq.s loc_3a92
loc_3a82:
    cmp.b #$2d,d1
    bne.w loc_3a98
loc_3a8a:
    bsr.w sub_3b98
loc_3a8e:
    beq.s sub_3a6c
loc_3a90:
    rts
loc_3a92:
    bsr.w sub_3e98
loc_3a96:
    bra.s sub_3a6c
loc_3a98:
    movem.l d1/a4,-(sp)
    ext.w d1
    move.b 126(a6,d1.w),d1
    bsr.w sub_3ed6
loc_3aa6:
    beq.s loc_3ab6
loc_3aa8:
    bpl.s loc_3ab0
loc_3aaa:
    tst.b 2113(a6) ; app+$841
    beq.s loc_3ab2
loc_3ab0:
    jsr (a0)
loc_3ab2:
    addq.w #8,sp
    bra.s loc_3abe
loc_3ab6:
    movem.l (sp)+,d1/a4
    bsr.w sub_3ac2
loc_3abe:
    subq.w #1,a4
    bra.s sub_3a6c
sub_3ac2:
    tst.b 2112(a6) ; app+$840
    beq.w loc_432c
loc_3aca:
    lea 1818(a6),a1 ; app+$71A
    lea 1274(a6),a2 ; app+$4FA
    move.l a2,1268(a6) ; app+$4F4
    clr.b 1273(a6) ; app+$4F9
    lea 3120(a6),a3 ; app+$C30
    moveq #0,d2
    cmp.b #$22,d1
    bne.s loc_3aee
loc_3ae6:
    move.b d1,d2
    move.b (a4)+,d1
    beq.w loc_3d00
loc_3aee:
    moveq #0,d3
loc_3af0:
    move.b d1,(a2)+
    move.b d1,(a1)+
    move.b d1,(a3)+
    addq.b #1,1273(a6) ; app+$4F9
    move.b (a4)+,d1
    beq.s loc_3b26
loc_3afe:
    cmp.b #$a,d1
    beq.s loc_3b26
loc_3b04:
    cmp.b #$20,d1
    beq.s loc_3b22
loc_3b0a:
    cmp.b #$2f,d1
    beq.s loc_3aee
loc_3b10:
    cmp.b d1,d2
    beq.s loc_3b1e
loc_3b14:
    cmp.b #$2e,d1
    bne.s loc_3af0
loc_3b1a:
    move.l a1,d3
    bra.s loc_3af0
loc_3b1e:
    move.b (a4)+,d1
    bra.s loc_3b26
loc_3b22:
    tst.b d2
    bne.s loc_3af0
loc_3b26:
    tst.l d3
    bne.s loc_3b3a
loc_3b2a:
    clr.b (a1)
    move.b #$2e,(a2)+
    move.b #$73,(a2)+
    addq.b #2,1273(a6) ; app+$4F9
    bra.s loc_3b44
loc_3b3a:
    movea.l d3,a1
    clr.b (a1)
    lea 1302(a1),a1
    clr.b (a1)
loc_3b44:
    move.b #$b,(a2)
    addq.b #1,1273(a6) ; app+$4F9
    clr.b (a3)
    lea 3120(a6),a0 ; app+$C30
    bsr.w sub_3b6a
loc_3b56:
    move.l a0,3116(a6) ; app+$C2C
    lea 1900(a6),a3 ; app+$76C
loc_3b5e:
    move.b (a0)+,(a3)+
    bne.s loc_3b5e
loc_3b62:
    movea.l 3116(a6),a0 ; app+$C2C
    clr.b (a0)
    rts
sub_3b6a:
    moveq #0,d0
    movea.l a0,a1
loc_3b6e:
    move.b (a0)+,d1
    beq.s loc_3b88
loc_3b72:
    cmp.b #$5c,d1
    beq.s loc_3b84
loc_3b78:
    cmp.b #$2f,d1
    beq.s loc_3b84
loc_3b7e:
    cmp.b #$3a,d1
    bne.s loc_3b6e
loc_3b84:
    move.l a0,d0
    bra.s loc_3b6e
loc_3b88:
    tst.l d0
    bne.s loc_3b92
loc_3b8c:
    movea.l a1,a0
    moveq #-1,d0
    rts
loc_3b92:
    movea.l d0,a0
    moveq #0,d0
    rts
sub_3b98:
    move.b (a4)+,d1
    beq.s loc_3ba8
loc_3b9c:
    cmp.b #$20,d1
    beq.s loc_3ba8
loc_3ba2:
    cmp.b #$a,d1
    bne.s loc_3bac
loc_3ba8:
    moveq #0,d0
    rts
loc_3bac:
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$5b,d1
    bcc.s loc_3bca
loc_3bb8:
    subi.b #$41,d1
    bcs.s loc_3c02
loc_3bbe:
    add.b d1,d1
    ext.w d1
    lea pcref_3c12(pc,d1.w),a2
    adda.w (a2),a2
    jmp (a2) ; unresolved_indirect_core:ind
loc_3bca:
    cmp.b #$7c,d1
    bne.s loc_3c0e
loc_3bd0:
    lea pcref_1442(pc),a0
    moveq #0,d1
    move.b (a4)+,d1
    bmi.s loc_3c0e
loc_3bda:
    move.b 0(a0,d1.w),d1
    bmi.s loc_3c0e
loc_3be0:
    moveq #0,d2
loc_3be2:
    lsl.l #4,d2
    or.b d1,d2
    move.b (a4)+,d1
    bmi.s loc_3bf0
loc_3bea:
    move.b 0(a0,d1.w),d1
    bpl.s loc_3be2
loc_3bf0:
    subq.w #1,a4
    tst.l 418(a6) ; app+$1A2
    bne.s loc_3bfe
loc_3bf8:
    jmp loc_a986
loc_3bfe:
    moveq #0,d1
    rts
loc_3c02:
    addi.b #$41,d1
    cmp.b #$2e,d1
    beq.w loc_3c96
loc_3c0e:
    bra.w loc_3d00
pcref_3c12:
    dc.w    loc_3d00-*
    dc.w    loc_3c86-*
    dc.w    loc_3c5c-*
    dc.w    loc_3c68-*
    dc.w    loc_3e06-*
    dc.w    loc_3d00-*
    dc.w    loc_3c9c-*
    dc.w    loc_3d68-*
    dc.w    loc_3d4a-*
    dc.w    loc_3d00-*
    dc.w    loc_3d00-*
    dc.w    loc_3cb0-*
    dc.w    loc_3c80-*
    dc.w    loc_3d00-*
    dc.w    sub_3d78-*
    dc.w    loc_3dbc-*
    dc.w    loc_3c62-*
    dc.w    loc_3d00-*
    dc.w    loc_3c4a-*
    dc.w    loc_3d04-*
    dc.w    loc_3d00-*
    dc.w    sub_3e98-*
    dc.w    loc_3d72-*
    dc.w    loc_3c7a-*
    dc.w    loc_3d00-*
    dc.w    loc_3cf8-*
    dc.w    loc_ac46-*
    dc.b    $4e,$75
loc_3c4a: ; jt: pcref_3c12
    lea 255(a6),a1 ; app+$FF
loc_3c4e:
    tst.b 2112(a6) ; app+$840
    beq.w sub_3b98
loc_3c56:
    st (a1)
    bra.w sub_3b98
loc_3c5c: ; jt: pcref_3c12
    lea 254(a6),a1 ; app+$FE
    bra.s loc_3c4e
loc_3c62: ; jt: pcref_3c12
    lea 3110(a6),a1 ; app+$C26
    bra.s loc_3c4e
loc_3c68: ; jt: pcref_3c12
    tst.b 2112(a6) ; app+$840
    beq.w sub_3b98
loc_3c70:
    move.b #$1,260(a6) ; app+$104
    bra.w sub_3b98
loc_3c7a: ; jt: pcref_3c12
    lea 260(a6),a1 ; app+$104
    bra.s loc_3c4e
loc_3c80: ; jt: pcref_3c12
    lea 539(a6),a1 ; app+$21B
    bra.s loc_3c4e
loc_3c86: ; jt: pcref_3c12
    tst.b 2112(a6) ; app+$840
    beq.w sub_3b98
loc_3c8e:
    sf 259(a6) ; app+$103
    bra.w sub_3b98
loc_3c96:
    lea 295(a6),a1 ; app+$127
    bra.s loc_3c4e
loc_3c9c: ; jt: pcref_3c12
    tst.b 2112(a6) ; app+$840
    beq.w sub_3b98
loc_3ca4:
    sf 259(a6) ; app+$103
    st 265(a6) ; app+$109
    bra.w sub_3b98
loc_3cb0: ; jt: pcref_3c12
    tst.b 2112(a6) ; app+$840
    beq.w loc_3cbe
loc_3cb8:
    move.w #$2,540(a6) ; app+$21C
loc_3cbe:
    move.b (a4),d0
    subi.b #$30,d0
    bls.w sub_3b98
loc_3cc8:
    subq.b #1,d0
    ext.w d0
    cmp.w #$7,d0
    bcc.w sub_3b98
loc_3cd4:
    btst d0,#$6c
    beq.w loc_3d00
loc_3cdc:
    cmp.b #$6,d0
    bne.w loc_3ce6
loc_3ce4:
    moveq #2,d0
loc_3ce6:
    addq.w #1,a4
    tst.b 2112(a6) ; app+$840
    beq.w sub_3b98
loc_3cf0:
    move.w d0,540(a6) ; app+$21C
    bra.w sub_3b98
loc_3cf8: ; jt: pcref_3c12
    lea 538(a6),a1 ; app+$21A
    bra.w loc_3c4e
loc_3d00: ; jt: pcref_3c12
    moveq #-1,d0
    rts
loc_3d04: ; jt: pcref_3c12
    moveq #0,d2
    move.b (a4)+,d2
    subi.b #$30,d2
    bcs.s loc_3d00
loc_3d0e:
    cmp.b #$a,d2
    bcc.s loc_3d00
loc_3d14:
    move.b (a4),d1
    cmp.b #$30,d1
    bcs.s loc_3d36
loc_3d1c:
    cmp.b #$3a,d1
    bcc.s loc_3d36
loc_3d22:
    mulu.w #$a,d2
    subi.b #$30,d1
    andi.w #$ff,d1
    add.w d1,d2
    move.w d2,2924(a6) ; app+$B6C
    addq.w #1,a4
loc_3d36:
    tst.w d2
    beq.s loc_3d00
loc_3d3a:
    tst.b 2112(a6) ; app+$840
    beq.w sub_3b98
loc_3d42:
    move.w d2,2924(a6) ; app+$B6C
    bra.w sub_3b98
loc_3d4a: ; jt: pcref_3c12
    lea 2098(a6),a3 ; app+$832
    st 299(a6) ; app+$12B
    tst.b 2115(a6) ; app+$843
sub_3d56:
    beq.w loc_3d62
loc_3d5a:
    bsr.w sub_4696
loc_3d5e:
    moveq #0,d0
    rts
loc_3d62:
    bsr.w sub_470a
loc_3d66:
    bra.s loc_3d5e
loc_3d68: ; jt: pcref_3c12
    lea app_timer_device_iorequest+IO_DATA(a6),a3
    sf 299(a6) ; app+$12B
    bra.s sub_3d56
loc_3d72: ; jt: pcref_3c12
    lea 2016(a6),a1 ; app+$7E0
    bra.s sub_3d7c
sub_3d78: ; jt: pcref_3c12
    lea 1736(a6),a1 ; app+$6C8
sub_3d7c:
    moveq #81,d0
    moveq #0,d2
    cmpi.b #$22,(a4)
    bne.s loc_3d88
loc_3d86:
    move.b (a4)+,d2
loc_3d88:
    move.b (a4)+,d1
    beq.s loc_3dae
loc_3d8c:
    cmp.b #$a,d1
    beq.s loc_3dae
loc_3d92:
    cmp.b d2,d1
    beq.s loc_3db0
loc_3d96:
    cmp.b #$20,d1
    bne.s loc_3da0
loc_3d9c:
    tst.b d2
    beq.s loc_3dae
loc_3da0:
    tst.b 2112(a6) ; app+$840
    beq.w loc_3daa
loc_3da8:
    move.b d1,(a1)+
loc_3daa:
    subq.b #1,d0
    bne.s loc_3d88
loc_3dae:
    subq.w #1,a4
loc_3db0:
    tst.b 2112(a6) ; app+$840
    beq.w loc_3dba
loc_3db8:
    clr.b (a1)
loc_3dba:
    rts
loc_3dbc: ; jt: pcref_3c12
    tst.b 2112(a6) ; app+$840
    beq.w loc_3dd2
loc_3dc4:
    st 256(a6) ; app+$100
    move.l app_output_file(a6),app_open_file(a6)
    st 2388(a6) ; app+$954
loc_3dd2:
    move.b (a4),d1
    beq.w sub_3b98
loc_3dd8:
    cmp.b #$20,d1
    beq.w sub_3b98
loc_3de0:
    cmp.b #$a,d1
    beq.w sub_3b98
loc_3de8:
    lea 1934(a6),a1 ; app+$78E
    bra.s sub_3d7c
sub_3dee:
    move.b (a4)+,d1
    beq.s loc_3e04
loc_3df2:
    cmp.b #$a,d1
    beq.s loc_3e04
loc_3df8:
    cmp.b #$9,d1
    beq.s sub_3dee
loc_3dfe:
    cmp.b #$20,d1
    beq.s sub_3dee
loc_3e04:
    rts
loc_3e06: ; jt: pcref_3c12
    tst.b 2114(a6) ; app+$842
    bne.w loc_3e38
loc_3e0e:
    bsr.s sub_3dee
loc_3e10:
    beq.s loc_3e34
loc_3e12:
    move.b (a4)+,d1
    beq.s loc_3e34
loc_3e16:
    cmp.b #$a,d1
    beq.s loc_3e34
loc_3e1c:
    cmp.b #$9,d1
    beq.w loc_3e34
loc_3e24:
    cmp.b #$20,d1
    beq.w loc_3e34
loc_3e2c:
    cmp.b #$2c,d1
    bne.s loc_3e12
loc_3e32:
    bra.s loc_3e0e
loc_3e34:
    subq.w #1,a4
    rts
loc_3e38:
    bsr.s sub_3dee
loc_3e3a:
    beq.s loc_3e96
loc_3e3c:
    st d2
    lea 1000(a6),a0 ; app+$3E8
    clr.b 4(a0)
    bsr.w sub_76b8
loc_3e4a:
    bne.s loc_3e90
loc_3e4c:
    cmp.b #$3d,d1
    beq.s loc_3e58
loc_3e52:
    moveq #1,d2
    moveq #2,d3
    bra.s loc_3e68
loc_3e58:
    move.b (a4)+,d1
    bsr.w sub_0db6
loc_3e5e:
    tst.b d4
    bne.s loc_3e90
loc_3e62:
    cmp.b #$2,d3
    bne.s loc_3e90
loc_3e68:
    lea 1000(a6),a0 ; app+$3E8
    movem.l d1-d2,-(sp)
    bsr.w sub_0bce
loc_3e74:
    movem.l (sp)+,d1/d4
    beq.s loc_3e90
loc_3e7a:
    lea 362(a6),a2 ; app+$16A
    moveq #2,d3
    move.w d1,-(sp)
    bsr.w sub_0cb6
loc_3e86:
    move.w (sp)+,d1
    cmp.b #$2c,d1
    bne.s loc_3e96
loc_3e8e:
    bra.s loc_3e38
loc_3e90:
    moveq #81,d0
    bra.w loc_8486
loc_3e96:
    bra.s loc_3eae
sub_3e98: ; jt: pcref_3c12
    tst.b 2113(a6) ; app+$841
    bne.s loc_3eb4
loc_3e9e:
    move.b (a4)+,d1
    beq.s loc_3eae
loc_3ea2:
    cmp.b #$20,d1
    beq.s loc_3eae
loc_3ea8:
    cmp.b #$a,d1
    bne.s loc_3e9e
loc_3eae:
    subq.w #1,a4
    moveq #0,d0
    rts
loc_3eb4:
    bsr.w loc_4334
loc_3eb8:
    bra.s loc_3eae
sub_3eba:
; --- unverified ---
    move.l a4,-(sp)
    clr.w 536(a6) ; app+$218
    bsr.s hint_3ece
hint_3ec2:
; --- unverified ---
    movea.l (sp)+,a4
    addq.w #1,536(a6) ; app+$218
    sf 258(a6) ; app+$102
    rts
hint_3ece:
; --- unverified ---
    move.l sp,564(a6) ; app+$234
    bra.w loc_4334
sub_3ed6:
    lea pcref_3f3c(pc),a0
    moveq #0,d2
loc_3edc:
    move.b (a0)+,d2
    beq.s loc_3f04
loc_3ee0:
    cmp.b (a0),d1
    blt.s loc_3f04
loc_3ee4:
    bne.s loc_3efe
loc_3ee6:
    lea 1(a0),a1
    movea.l a4,a2
    move.b d2,d3
loc_3eee:
    subq.b #1,d3
    beq.s loc_3f08
loc_3ef2:
    move.b (a2)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b (a1)+,d0
    beq.s loc_3eee
loc_3efe:
    lea 2(a0,d2.w),a0
    bra.s loc_3edc
loc_3f04:
    moveq #0,d0
    rts
loc_3f08:
    move.b (a2),d0
    beq.s loc_3f26
loc_3f0c:
    cmp.b #$a,d0
    beq.s loc_3f26
loc_3f12:
    cmp.b #$2c,d0
    beq.s loc_3f26
loc_3f18:
    cmp.b #$9,d0
    beq.s loc_3f26
loc_3f1e:
    cmp.b #$20,d0
    beq.s loc_3f26
loc_3f24:
    bra.s loc_3efe
loc_3f26:
    move.b (a1)+,d0
    lsl.w #8,d0
    move.b (a1)+,d0
    lea -2(a1,d0.w),a0
    movea.l a2,a4
    move.b (a4)+,d1
    lea 925(pc),a2
    cmpa.l a2,a0
    rts
pcref_3f3c:
    dc.b    $05,$41,$4c,$49,$4e,$4b
    dc.w    sub_4200-*
    dc.b    $09
    dc.b    "ALLOWZERO"
    dc.w    sub_42a2-*
    dc.b    $05,$41,$4d,$49,$47,$41
    dc.w    sub_41f8-*
    dc.b    $06
    dc.b    "AUTOPC"
    dc.w    sub_424e-*
    dc.b    $03,$42,$44,$4c
    dc.w    sub_423c-*
    dc.b    $03,$42,$44,$57
    dc.w    sub_4236-*
    dc.b    $03,$42,$52,$42
    dc.w    sub_4218-*
    dc.b    $03,$42,$52,$4c
    dc.w    loc_4224-*
    dc.b    $03,$42,$52,$53
    dc.w    sub_4218-*
    dc.b    $03,$42,$52,$57
    dc.w    sub_421e-*
    dc.b    $04,$43,$41,$53,$45
    dc.w    sub_4162-*
    dc.b    $06
    dc.b    "CHKBIT"
    dc.w    sub_428e-*
    dc.b    $06
    dc.b    "CHKIMM"
    dc.w    sub_4276-*
    dc.b    $05,$43,$48,$4b,$50,$43
    dc.w    sub_425a-*
    dc.b    $01,$44
    dc.w    sub_4178-*
    dc.b    $05,$44,$45,$42,$55,$47
    dc.w    sub_4178-*
    dc.b    $04,$45,$56,$45,$4e
    dc.w    sub_4282-*
    dc.b    $04,$46,$52,$4f,$4d
    dc.w    sub_431a-*
    dc.b    $06
    dc.b    "GENSYM"
    dc.w    sub_4168-*
    dc.b    $04,$48,$43,$4c,$4e
    dc.w    sub_42ba-*
    dc.b    $06
    dc.b    "HEADER"
    dc.w    loc_42e8-*
    dc.b    $06
    dc.b    "INCDIR"
    dc.w    sub_42f6-*
    dc.b    $07
    dc.b    "INCONCE"
    dc.w    sub_42ae-*
    dc.b    $07
    dc.b    "LATTICE"
    dc.w    sub_41d8-*
    dc.b    $04,$4c,$49,$4e,$45
    dc.w    sub_42c4-*
    dc.b    $04,$4c,$49,$53,$54
    dc.w    sub_41b6-*
    dc.b    $05,$4c,$49,$53,$54,$31
    dc.w    sub_41c2-*
    dc.b    $08
    dc.b    "LOCALDOT"
    dc.w    sub_426e-*
    dc.b    $06
    dc.b    "LOCALU"
    dc.w    sub_4266-*
    dc.b    $06
    dc.b    "LOWMEM"
    dc.w    sub_430e-*
    dc.b    $03,$4d,$45,$58
    dc.w    sub_41da-*
    dc.b    $0b
    dc.b    "NOALLOWZERO"
    dc.w    sub_42a8-*
    dc.b    $08
    dc.b    "NOAUTOPC"
    dc.w    sub_4254-*
    dc.b    $06
    dc.b    "NOCASE"
    dc.w    sub_4172-*
    dc.b    $08
    dc.b    "NOCHKBIT"
    dc.w    sub_4294-*
    dc.b    $08
    dc.b    "NOCHKIMM"
    dc.w    sub_427c-*
    dc.b    $07
    dc.b    "NOCHKPC"
    dc.w    sub_4260-*
    dc.b    $07
    dc.b    "NOCODES"
    dc.w    sub_4186-*
    dc.b    $07
    dc.b    "NODEBUG"
    dc.w    sub_418c-*
    dc.b    $06
    dc.b    "NOEVEN"
    dc.w    sub_4288-*
    dc.b    $06
    dc.b    "NOHCLN"
    dc.w    sub_42ce-*
    dc.b    $09
    dc.b    "NOINCONCE"
    dc.w    sub_42b4-*
    dc.b    $06
    dc.b    "NOLINE"
    dc.w    sub_42ce-*
    dc.b    $06
    dc.b    "NOLIST"
    dc.w    sub_41bc-*
    dc.b    $07
    dc.b    "NOLIST1"
    dc.w    sub_41c8-*
    dc.b    $05,$4e,$4f,$4d,$45,$58
    dc.w    sub_41e0-*
    dc.b    $08
    dc.b    "NOSYMTAB"
    dc.w    sub_41b0-*
    dc.b    $09
    dc.b    "NOTRACEIF"
    dc.w    sub_41d4-*
    dc.b    $06
    dc.b    "NOTYPE"
    dc.w    sub_4198-*
    dc.b    $06
    dc.b    "NOWARN"
    dc.w    sub_41a4-*
    dc.b    $03,$4f,$44,$4c
    dc.w    sub_4248-*
    dc.b    $03,$4f,$44,$57
    dc.w    sub_4242-*
    dc.b    $03,$4f,$4c,$44
    dc.w    sub_41e6-*
    dc.b    $05,$51,$55,$49,$45,$54
    dc.w    sub_4314-*
    dc.b    $04,$53,$52,$45,$43
    dc.w    sub_41fc-*
    dc.b    $05,$53,$55,$50,$45,$52
    dc.w    sub_41ec-*
    dc.b    $06
    dc.b    "SYMTAB"
    dc.w    sub_41aa-*
    dc.b    $02,$54,$4f
    dc.w    sub_42d4-*
    dc.b    $07
    dc.b    "TRACEIF"
    dc.w    sub_41ce-*
    dc.b    $04,$54,$59,$50,$45
    dc.w    sub_4192-*
    dc.b    $04,$55,$53,$45,$52
    dc.w    sub_41f2-*
    dc.b    $04,$57,$41,$52,$4e
    dc.w    sub_419e-*
    dc.b    $07
    dc.b    "WARNBIT"
    dc.w    sub_429a-*
    dc.b    $04,$57,$49,$54,$48
    dc.w    sub_4322-*
    dc.b    $06
    dc.b    "XDEBUG"
    dc.w    sub_4180-*
    dc.b    $00
    dc.b    $00
sub_4162: ; jt: pcref_3f3c
    sf 254(a6) ; app+$FE
    rts
sub_4168: ; jt: pcref_3f3c
    st 265(a6) ; app+$109
    sf 259(a6) ; app+$103
    rts
sub_4172: ; jt: pcref_3f3c
    st 254(a6) ; app+$FE
    rts
sub_4178: ; jt: pcref_3f3c
    move.b #$1,260(a6) ; app+$104
    rts
sub_4180: ; jt: pcref_3f3c
    st 260(a6) ; app+$104
    rts
sub_4186: ; jt: pcref_3f3c
    st 296(a6) ; app+$128
    rts
sub_418c: ; jt: pcref_3f3c
    sf 260(a6) ; app+$104
    rts
sub_4192: ; jt: pcref_3f3c
    sf 263(a6) ; app+$107
    rts
sub_4198: ; jt: pcref_3f3c
    st 263(a6) ; app+$107
    rts
sub_419e: ; jt: pcref_3f3c
    st 261(a6) ; app+$105
    rts
sub_41a4: ; jt: pcref_3f3c
    sf 261(a6) ; app+$105
    rts
sub_41aa: ; jt: pcref_3f3c
    st 255(a6) ; app+$FF
    rts
sub_41b0: ; jt: pcref_3f3c
    sf 255(a6) ; app+$FF
    rts
sub_41b6: ; jt: pcref_3f3c
    st 256(a6) ; app+$100
    rts
sub_41bc: ; jt: pcref_3f3c
    sf 256(a6) ; app+$100
    rts
sub_41c2: ; jt: pcref_3f3c
    st 538(a6) ; app+$21A
    rts
sub_41c8: ; jt: pcref_3f3c
    sf 538(a6) ; app+$21A
    rts
sub_41ce: ; jt: pcref_3f3c
    st 294(a6) ; app+$126
    rts
sub_41d4: ; jt: pcref_3f3c
    sf 294(a6) ; app+$126
sub_41d8: ; jt: pcref_3f3c
    rts
sub_41da: ; jt: pcref_3f3c
    st 279(a6) ; app+$117
    rts
sub_41e0: ; jt: pcref_3f3c
    sf 279(a6) ; app+$117
    rts
sub_41e6: ; jt: pcref_3f3c
    st 292(a6) ; app+$124
    rts
sub_41ec: ; jt: pcref_3f3c
    sf 293(a6) ; app+$125
    rts
sub_41f2: ; jt: pcref_3f3c
    st 293(a6) ; app+$125
    rts
sub_41f8: ; jt: pcref_3f3c
    moveq #3,d0
    bra.s loc_4202
sub_41fc: ; jt: pcref_3f3c
    moveq #5,d0
    bra.s loc_4202
sub_4200: ; jt: pcref_3f3c
    moveq #2,d0
loc_4202:
    move.w d0,540(a6) ; app+$21C
    tst.l 548(a6) ; app+$224
    bne.w loc_43d2
loc_420e:
    tst.b 568(a6) ; app+$238
    beq.w loc_44e4
loc_4216:
    rts
sub_4218: ; jt: pcref_3f3c
    st 300(a6) ; app+$12C
    rts
sub_421e: ; jt: pcref_3f3c
    sf 300(a6) ; app+$12C
    rts
loc_4224: ; jt: pcref_3f3c
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
loc_422e:
    move.b #$1,300(a6) ; app+$12C
    rts
sub_4236: ; jt: pcref_3f3c
    st 301(a6) ; app+$12D
    rts
sub_423c: ; jt: pcref_3f3c
    sf 301(a6) ; app+$12D
    rts
sub_4242: ; jt: pcref_3f3c
    st 302(a6) ; app+$12E
    rts
sub_4248: ; jt: pcref_3f3c
    sf 302(a6) ; app+$12E
    rts
sub_424e: ; jt: pcref_3f3c
    st 281(a6) ; app+$119
    rts
sub_4254: ; jt: pcref_3f3c
    sf 281(a6) ; app+$119
    rts
sub_425a: ; jt: pcref_3f3c
    st 262(a6) ; app+$106
    rts
sub_4260: ; jt: pcref_3f3c
    sf 262(a6) ; app+$106
    rts
sub_4266: ; jt: pcref_3f3c
    move.b #$5f,278(a6) ; app+$116
    rts
sub_426e: ; jt: pcref_3f3c
    move.b #$2e,278(a6) ; app+$116
    rts
sub_4276: ; jt: pcref_3f3c
    st 285(a6) ; app+$11D
    rts
sub_427c: ; jt: pcref_3f3c
    sf 285(a6) ; app+$11D
    rts
sub_4282: ; jt: pcref_3f3c
    st 287(a6) ; app+$11F
    rts
sub_4288: ; jt: pcref_3f3c
    sf 287(a6) ; app+$11F
    rts
sub_428e: ; jt: pcref_3f3c
    st 286(a6) ; app+$11E
    rts
sub_4294: ; jt: pcref_3f3c
    sf 286(a6) ; app+$11E
    rts
sub_429a: ; jt: pcref_3f3c
    move.b #$1,286(a6) ; app+$11E
    rts
sub_42a2: ; jt: pcref_3f3c
    st 288(a6) ; app+$120
    rts
sub_42a8: ; jt: pcref_3f3c
    sf 288(a6) ; app+$120
    rts
sub_42ae: ; jt: pcref_3f3c
    st 308(a6) ; app+$134
    rts
sub_42b4: ; jt: pcref_3f3c
    sf 308(a6) ; app+$134
    rts
sub_42ba: ; jt: pcref_3f3c
    st 297(a6) ; app+$129
    st 298(a6) ; app+$12A
    rts
sub_42c4: ; jt: pcref_3f3c
    st 297(a6) ; app+$129
    sf 298(a6) ; app+$12A
    rts
sub_42ce: ; jt: pcref_3f3c
    sf 297(a6) ; app+$129
    rts
sub_42d4: ; jt: pcref_3f3c
    bsr.w sub_3dee
loc_42d8:
    subq.w #1,a4
    tst.b 2112(a6) ; app+$840
    beq.w loc_432c
loc_42e2:
    bsr.w sub_3d78
loc_42e6:
    bra.s loc_4330
loc_42e8: ; jt: pcref_3f3c
    move.b 2112(a6),-(sp) ; app+$840
    lea app_timer_device_iorequest+IO_DATA(a6),a3
    sf 299(a6) ; app+$12B
    bra.s loc_4302
sub_42f6: ; jt: pcref_3f3c
    move.b 2115(a6),-(sp) ; app+$843
    lea 2098(a6),a3 ; app+$832
    st 299(a6) ; app+$12B
loc_4302:
    bsr.w sub_3dee
loc_4306:
    subq.w #1,a4
    tst.b (sp)+
    bra.w sub_3d56
sub_430e: ; jt: pcref_3f3c
    st 539(a6) ; app+$21B
    rts
sub_4314: ; jt: pcref_3f3c
    st 295(a6) ; app+$127
    rts
sub_431a: ; jt: pcref_3f3c
    bsr.w sub_3dee
loc_431e:
    bra.w sub_3ac2
sub_4322: ; jt: pcref_3f3c
    bsr.w sub_3dee
loc_4326:
    subq.w #1,a4
    lea 2016(a6),a1 ; app+$7E0
loc_432c:
    bsr.w sub_3d7c
loc_4330:
    move.b (a4)+,d1
    rts
loc_4334:
    move.b (a4)+,d1
    st 2116(a6) ; app+$844
    cmp.b #$a,d1
    beq.w sub_3a24
loc_4342:
    cmp.b #$9,d1
    beq.w sub_3a24
loc_434a:
    cmp.b #$20,d1
    beq.w sub_3a24
loc_4352:
    ext.w d1
    move.b 126(a6,d1.w),d1
    beq.w sub_3a24
loc_435c:
    move.b (a4),d0
    cmp.b #$2b,d0
    beq.s loc_4374
loc_4364:
    cmp.b #$2d,d0
    beq.s loc_4374
loc_436a:
    bsr.w sub_3ed6
loc_436e:
    beq.s loc_4374
loc_4370:
    jsr (a0)
loc_4372:
    bra.s loc_4390
loc_4374:
    subi.b #$41,d1
    bcs.s loc_4398
loc_437a:
    cmp.b #$1a,d1
    bcc.s loc_4398
loc_4380:
    ext.w d1
    add.w d1,d1
    move.w pcref_439e(pc,d1.w),d0
    beq.s loc_4398
loc_438a:
    move.b (a4)+,d1
    jsr pcref_439e(pc,d0.w) ; unresolved_indirect_core:pcindex.brief
loc_4390:
    cmp.b #$2c,d1
    beq.s loc_4334
loc_4396:
    rts
loc_4398:
    moveq #58,d0
    bra.w loc_8482
pcref_439e:
    dc.w    sub_4438-pcref_439e
    dc.b    $00,$00
    dc.w    sub_445e-pcref_439e
    dc.w    sub_43ec-pcref_439e
    dc.w    sub_4448-pcref_439e
    dcb.b   6,0
    dc.w    sub_4440-pcref_439e
    dcb.b   4,0
    dc.w    sub_4490-pcref_439e
    dc.w    sub_4402-pcref_439e
    dc.b    $00,$00
    dc.w    sub_4504-pcref_439e
    dc.w    sub_440a-pcref_439e
    dcb.b   4,0
    dc.w    sub_4420-pcref_439e
    dc.w    sub_43fa-pcref_439e
    dc.w    sub_4450-pcref_439e
    dc.b    $00,$00
    dc.w    sub_4428-pcref_439e
    dc.w    sub_4430-pcref_439e
    dc.w    sub_43d8-pcref_439e
    dc.b    $00,$00
loc_43d2:
    moveq #64,d0
    bra.w loc_8486
sub_43d8: ; jt: pcref_439e
    move.b (a4)+,d0
    exg
    cmp.b #$2b,d0
    beq.s loc_43ea
loc_43e2:
    cmp.b #$2d,d0
    bne.s loc_4398
loc_43e8:
    tst.b d0
loc_43ea:
    rts
sub_43ec: ; jt: pcref_439e
    bsr.s sub_43d8
loc_43ee:
    seq d0
    andi.b #$1,d0
    move.b d0,260(a6) ; app+$104
    rts
sub_43fa: ; jt: pcref_439e
    bsr.s sub_43d8
loc_43fc:
    sne 263(a6) ; app+$107
    rts
sub_4402: ; jt: pcref_439e
    bsr.s sub_43d8
loc_4404:
    seq 279(a6) ; app+$117
    rts
sub_440a: ; jt: pcref_439e
    cmp.b #$3d,d1
    bne.s loc_4418
loc_4410:
    bsr.w sub_316e
loc_4414:
    bne.s loc_4398
loc_4416:
    rts
loc_4418:
    bsr.s sub_43d8
loc_441a:
    seq 262(a6) ; app+$106
    rts
sub_4420: ; jt: pcref_439e
    bsr.s sub_43d8
loc_4422:
    seq 255(a6) ; app+$FF
    rts
sub_4428: ; jt: pcref_439e
    bsr.s sub_43d8
loc_442a:
    seq 261(a6) ; app+$105
    rts
sub_4430: ; jt: pcref_439e
    bsr.s sub_43d8
loc_4432:
    seq 260(a6) ; app+$104
    rts
sub_4438: ; jt: pcref_439e
    bsr.s sub_43d8
loc_443a:
    seq 281(a6) ; app+$119
    rts
sub_4440: ; jt: pcref_439e
    bsr.s sub_43d8
loc_4442:
    seq 285(a6) ; app+$11D
    rts
sub_4448: ; jt: pcref_439e
    bsr.s sub_43d8
loc_444a:
    seq 287(a6) ; app+$11F
    rts
sub_4450: ; jt: pcref_439e
    moveq #95,d2
    bsr.s sub_43d8
loc_4454:
    beq.s loc_4458
loc_4456:
    moveq #46,d2
loc_4458:
    move.b d2,278(a6) ; app+$116
    rts
sub_445e: ; jt: pcref_439e
    bsr.w sub_455a
loc_4462:
    bne.s loc_447a
loc_4464:
    cmp.w #$8,d2
    bcs.w loc_4398
loc_446c:
    cmp.w #$80,d2
    bcc.w loc_4398
loc_4474:
    addq.w #1,d2
    move.w d2,542(a6) ; app+$21E
loc_447a:
    cmp.b #$2b,d1
    beq.s loc_4488
loc_4480:
    cmp.b #$2d,d1
    bne.s loc_448e
loc_4486:
    tst.b d1
loc_4488:
    sne 254(a6) ; app+$FE
    move.b (a4)+,d1
loc_448e:
    rts
sub_4490: ; jt: pcref_439e
    tst.l 548(a6) ; app+$224
    bne.w loc_43d2
loc_4498:
    move.b d1,d0
    move.b (a4)+,d1
    tst.b 568(a6) ; app+$238
    bne.s loc_4502
loc_44a2:
    cmp.b #$2b,d0
    beq.s loc_44e0
loc_44a8:
    cmp.b #$2d,d0
    beq.s loc_44dc
loc_44ae:
    subi.b #$30,d0
    bcs.w loc_4398
loc_44b6:
    ext.w d0
    beq.s loc_44da
loc_44ba:
    subq.w #1,d0
    cmp.w #$7,d0
    bcc.w loc_4398
loc_44c4:
    btst d0,#$6c
    beq.w loc_4398
loc_44cc:
    cmp.b #$6,d0
    bne.s loc_44d4
loc_44d2:
    moveq #2,d0
loc_44d4:
    move.w d0,540(a6) ; app+$21C
    bra.s loc_44e4
loc_44da:
    bra.s loc_44e4
loc_44dc:
    moveq #3,d0
    bra.s loc_44d4
loc_44e0:
    moveq #2,d0
    bra.s loc_44d4
loc_44e4:
    movea.l 322(a6),a1 ; app+$142
    movea.l 318(a6),a0 ; app+$13E
    clr.l 406(a6) ; app+$196
    tst.b 568(a6) ; app+$238
    bne.s loc_44fa
loc_44f6:
    clr.l 422(a6) ; app+$1A6
loc_44fa:
    bsr.w sub_79a6
loc_44fe:
    move.b -1(a4),d1
loc_4502:
    rts
sub_4504: ; jt: pcref_439e
    lea 270(a6),a1 ; app+$10E
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$57,d1
    bne.s loc_451a
loc_4514:
    lea 272(a6),a1 ; app+$110
    move.b (a4)+,d1
loc_451a:
    cmp.b #$2d,d1
    beq.s loc_454e
loc_4520:
    cmp.b #$2b,d1
    beq.s loc_4552
loc_4526:
    bsr.w sub_455a
loc_452a:
    subq.w #1,d2
    bmi.w loc_4398
loc_4530:
    cmp.w #$b,d2
    bhi.w loc_4398
loc_4538:
    bsr.w sub_43d8
loc_453c:
    beq.s loc_4546
loc_453e:
    move.w (a1),d0
    bclr d2,d0
    move.w d0,(a1)
    rts
loc_4546:
    move.w (a1),d0
    bset d2,d0
    move.w d0,(a1)
    rts
loc_454e:
    clr.w (a1)
    bra.s loc_4556
loc_4552:
    move.w #$ffff,(a1)
loc_4556:
    move.b (a4)+,d1
    rts
sub_455a:
    cmp.b #$30,d1
    bcs.s loc_458e
loc_4560:
    cmp.b #$39,d1
    bhi.s loc_458e
loc_4566:
    moveq #0,d2
    subi.b #$30,d1
    move.b d1,d2
loc_456e:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.s loc_458c
loc_4576:
    cmp.b #$3a,d1
    bcc.s loc_458c
loc_457c:
    mulu.w #$a,d2
    subi.b #$30,d1
    andi.w #$f,d1
    add.w d1,d2
    bra.s loc_456e
loc_458c:
    moveq #0,d0
loc_458e:
    rts
sub_4590:
    tst.b 2388(a6) ; app+$954
    beq.s loc_45c6
loc_4596:
    lea 1934(a6),a0 ; app+$78E
    tst.b (a0)
    bne.s loc_45c2
loc_459e:
    lea 1268(a6),a1 ; app+$4F4
    moveq #0,d0
    move.b 5(a1),d0
    subq.b #1,d0
    bmi.s loc_45b4
loc_45ac:
    movea.l (a1),a1
loc_45ae:
    move.b (a1)+,(a0)+
    dbf d0,loc_45ae
loc_45b4:
    clr.b (a0)
    lea 1934(a6),a0 ; app+$78E
    lea str_45c8(pc),a2
    bsr.w sub_45ce
loc_45c2:
    bra.w loc_ab2c
loc_45c6:
    rts
str_45c8:
    dc.b    ".lst",0
    dc.b    $00
sub_45ce:
    bsr.s sub_45e2
loc_45d0:
    beq.s loc_45d4
loc_45d2:
    movea.l d2,a1
loc_45d4:
    subq.w #1,a1
loc_45d6:
    move.b (a2)+,(a1)+
    bne.s loc_45d6
loc_45da:
    rts
sub_45dc:
    bsr.s sub_45e2
loc_45de:
    beq.s loc_45d4
loc_45e0:
    rts
sub_45e2:
    movea.l a0,a1
loc_45e4:
    moveq #0,d2
loc_45e6:
    move.b (a1)+,d1
    beq.s loc_4606
loc_45ea:
    cmp.b #$5c,d1
    beq.s loc_45e4
loc_45f0:
    cmp.b #$2f,d1
    beq.s loc_45e4
loc_45f6:
    cmp.b #$3a,d1
    beq.s loc_45e4
loc_45fc:
    cmp.b #$2e,d1
    bne.s loc_45e6
loc_4602:
    move.l a1,d2
    bra.s loc_45e6
loc_4606:
    tst.l d2
loc_4608:
    rts
sub_460a:
    tst.b 299(a6) ; app+$12B
    beq.s loc_4608
loc_4610:
    movea.l (a3),a0
    move.b -1(a0,d3.w),d0
    cmp.b #$3a,d0
    beq.s loc_4608
loc_461c:
    cmp.b #$2f,d0
    beq.s loc_4608
loc_4622:
    cmp.b #$5c,d0
    beq.s loc_4608
loc_4628:
    moveq #47,d1
sub_462a:
    movea.l (a3),a0
    cmp.w 4(a3),d3
    bcs.s loc_4660
loc_4632:
    movem.l d0-d2/a1-a2,-(sp)
    moveq #100,d1
    add.w 4(a3),d1
    bsr.w sub_90ba
loc_4640:
    movea.l (a3),a1
    move.l a0,(a3)
    move.w 4(a3),d1
    lsr.w #2,d1
    beq.s loc_4654
loc_464c:
    subq.w #1,d1
loc_464e:
    move.l (a1)+,(a0)+
    dbf d1,loc_464e
loc_4654:
    movem.l (sp)+,d0-d2/a1-a2
    addi.w #$64,4(a3)
    movea.l (a3),a0
loc_4660:
    move.b d1,0(a0,d3.w)
    addq.w #1,d3
    rts
sub_4668:
    moveq #4,d1
    move.w d1,4(a3)
    bsr.w sub_90ba
loc_4672:
    move.l a0,(a3)
    clr.b (a0)
    rts
sub_4678:
    movea.l (a3),a0
    clr.b (a0)
sub_467c:
    moveq #0,d3
    tst.w 4(a3)
    beq.s loc_4694
loc_4684:
    movea.l (a3),a0
loc_4686:
    tst.b (a0)+
    beq.s loc_4694
loc_468a:
    addq.w #1,d3
    tst.b (a0)+
    bne.s loc_468a
loc_4690:
    addq.w #1,d3
    bra.s loc_4686
loc_4694:
    rts
sub_4696:
    move.b (a4)+,d1
loc_4698:
    bsr.s sub_467c
loc_469a:
    moveq #0,d2
    cmp.b #$22,d1
    beq.s loc_46a8
loc_46a2:
    cmp.b #$27,d1
    bne.s loc_46ac
loc_46a8:
    move.b d1,d2
loc_46aa:
    move.b (a4)+,d1
loc_46ac:
    beq.s loc_46f6
loc_46ae:
    cmp.b #$a,d1
    beq.s loc_46f6
loc_46b4:
    cmp.b #$20,d1
    bne.s loc_46c0
loc_46ba:
    tst.b d2
    bne.s loc_46da
loc_46be:
    bra.s loc_46f6
loc_46c0:
    cmp.b #$9,d1
    beq.s loc_46f6
loc_46c6:
    cmp.b d2,d1
    beq.s loc_46e0
loc_46ca:
    cmp.b #$3b,d1
    beq.s loc_46d6
loc_46d0:
    cmp.b #$2c,d1
    bne.s loc_46da
loc_46d6:
    tst.b d2
    beq.s loc_46e8
loc_46da:
    bsr.w sub_462a
loc_46de:
    bra.s loc_46aa
loc_46e0:
    move.b (a4)+,d1
    cmp.b #$2c,d1
    bne.s loc_46f6
loc_46e8:
    bsr.w sub_460a
loc_46ec:
    moveq #0,d1
    bsr.w sub_462a
loc_46f2:
    move.b (a4)+,d1
    bra.s loc_469a
loc_46f6:
    bsr.w sub_460a
loc_46fa:
    moveq #0,d1
    bsr.w sub_462a
loc_4700:
    bsr.w sub_462a
loc_4704:
    move.b -1(a4),d1
    rts
sub_470a:
    move.b (a4)+,d1
loc_470c:
    moveq #0,d2
    cmp.b #$22,d1
    beq.s loc_471a
loc_4714:
    cmp.b #$27,d1
    bne.s loc_471e
loc_471a:
    move.b d1,d2
loc_471c:
    move.b (a4)+,d1
loc_471e:
    beq.s loc_4730
loc_4720:
    cmp.b #$a,d1
    beq.s loc_4730
loc_4726:
    cmp.b #$20,d1
    bne.s loc_4732
loc_472c:
    tst.b d2
    bne.s loc_471c
loc_4730:
    rts
loc_4732:
    cmp.b #$9,d1
    beq.s loc_4730
loc_4738:
    cmp.b d2,d1
    beq.s loc_474c
loc_473c:
    cmp.b #$3b,d1
    beq.s loc_4748
loc_4742:
    cmp.b #$2c,d1
    bne.s loc_471c
loc_4748:
    tst.b d2
    bne.s loc_471c
loc_474c:
    move.b (a4)+,d1
    cmp.b #$2c,d1
    bne.s loc_4730
loc_4754:
    move.b (a4)+,d1
    bra.s loc_470c
sub_4758:
; --- unverified ---
    lea 1736(a6),a0 ; app+$6C8
    moveq #0,d2
    tst.b (a0)
    beq.s hint_4766
hint_4762:
; --- unverified ---
    moveq #10,d1
    rts
hint_4766:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_4786
hint_476c:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_4786
hint_4772:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_4786
hint_4778:
; --- unverified ---
    move.b d1,(a0)+
    move.b (a4)+,d1
    addq.b #1,d2
    cmp.b #$52,d2
    bne.s hint_4766
hint_4784:
    dc.b    $72,$0a
hint_4786:
; --- unverified ---
    clr.b (a0)
    rts
hint_478a:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_4794:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    beq.w sub_3132
hint_479e:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_47a6:
; --- unverified ---
    bsr.w hint_1d20
hint_47aa:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_47b2:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$23,d1
    bne.w hint_846a
hint_47bc:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_47c2:
; --- unverified ---
    bra.w hint_1ad0
hint_47c6:
; --- unverified ---
    bsr.w hint_2350
hint_47ca:
; --- unverified ---
    st 571(a6) ; app+$23B
    bsr.w hint_16e6
hint_47d2:
; --- unverified ---
    ori.w #$4e75,-(a4)
    tst.b 568(a6) ; app+$238
    beq.s hint_47e6
hint_47dc:
; --- unverified ---
    bset #0,3108(a6) ; app+$C24
    bsr.w sub_ab50
hint_47e6:
; --- unverified ---
    moveq #10,d1
    st 275(a6) ; app+$113
    rts
hint_47ee:
; --- unverified ---
    bclr #0,3108(a6) ; app+$C24
    rts
hint_47f6:
; --- unverified ---
    bsr.w hint_6ad2
hint_47fa:
; --- unverified ---
    cmp.l #$c,d2
    bcs.s hint_4814
hint_4802:
; --- unverified ---
    cmp.l #$ff,d2
    bcc.s hint_4814
hint_480a:
; --- unverified ---
    move.w d2,2916(a6) ; app+$B64
    st 275(a6) ; app+$113
    rts
hint_4814:
; --- unverified ---
    moveq #75,d0
    bra.w loc_8486
hint_481a:
; --- unverified ---
    moveq #0,d2
    subi.b #$30,d1
    bcs.s hint_486e
hint_4822:
; --- unverified ---
    cmp.b #$a,d1
    bcc.s hint_486e
hint_4828:
; --- unverified ---
    move.b d1,d2
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_4856
hint_4832:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_4856
hint_4838:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_4856
hint_483e:
; --- unverified ---
    subi.b #$30,d1
    bcs.s hint_486e
hint_4844:
; --- unverified ---
    cmp.b #$a,d1
    bcc.s hint_486e
hint_484a:
    dc.b    $c4,$fc,$00,$0a,$02,$41,$00,$0f,$d4,$41,$12,$1c
hint_4856:
; --- unverified ---
    moveq #-4,d0
    subq.l #2,d2
    beq.s hint_4874
hint_485c:
; --- unverified ---
    moveq #-6,d0
    subq.l #6,d2
    beq.s hint_4874
hint_4862:
; --- unverified ---
    moveq #0,d0
    subq.l #2,d2
    beq.s hint_4874
hint_4868:
; --- unverified ---
    moveq #-2,d0
    subq.l #6,d2
    beq.s hint_4874
hint_486e:
; --- unverified ---
    moveq #90,d0
    bra.w loc_8486
hint_4874:
; --- unverified ---
    move.b d0,303(a6) ; app+$12F
    rts
hint_487a:
; --- unverified ---
    bsr.w hint_2b02
hint_487e:
; --- unverified ---
    bsr.w hint_36c8
hint_4882:
; --- unverified ---
    bne.w hint_3736
hint_4886:
; --- unverified ---
    moveq #0,d2
    move.w d4,d2
    movea.l 362(a6),a2 ; app+$16A
    lea 1000(a6),a0 ; app+$3E8
    movem.l d2/a3-a5,-(sp)
    tst.b 568(a6) ; app+$238
    bne.s hint_48b4
hint_489c:
; --- unverified ---
    bsr.w sub_0b88
hint_48a0:
; --- unverified ---
    movem.l (sp)+,d4/a3-a5
    beq.w loc_8436
hint_48a8:
; --- unverified ---
    moveq #5,d3
    bsr.w sub_0cba
hint_48ae:
; --- unverified ---
    move.b -1(a4),d1
    rts
hint_48b4:
; --- unverified ---
    bsr.w sub_0b88
hint_48b8:
; --- unverified ---
    movem.l (sp)+,d4/a3-a5
    bne.w loc_843a
hint_48c0:
; --- unverified ---
    cmpi.b #$5,13(a1)
    bne.w loc_8436
hint_48ca:
; --- unverified ---
    cmp.l 8(a1),d4
    bne.w loc_8436
hint_48d2:
; --- unverified ---
    bset #6,12(a1)
    bne.w loc_8436
hint_48dc:
; --- unverified ---
    bra.s hint_48ae
pcref_48de:
; --- unverified ---
    btst d0,d0
    btst d0,d2
    lea 1000(a6),a0 ; app+$3E8
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    cmp.b #$1,d0
    beq.s hint_4902
hint_48f2:
; --- unverified ---
    btst #0,2125(a6) ; app+$84D
    beq.s hint_4902
hint_48fa:
    dc.b    $24,$2e,$08,$46,$d5,$ae,$08,$4a
hint_4902:
; --- unverified ---
    tst.l (a0)
    bne.s hint_492c
hint_4906:
; --- unverified ---
    bsr.w sub_16cc
hint_490a:
; --- unverified ---
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    move.b pcref_48de(pc,d0.w),d0
    lsl.l d0,d2
    tst.b 2118(a6) ; app+$846
    bpl.s hint_491e
hint_491c:
    dc.b    $44,$82
hint_491e:
; --- unverified ---
    move.l 2122(a6),d0 ; app+$84A
    add.l d2,2122(a6) ; app+$84A
    move.l d0,d2
    bra.w hint_2b7e
hint_492c:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_497a
hint_4932:
; --- unverified ---
    move.l a0,-(sp)
    bsr.w sub_16cc
hint_4938:
; --- unverified ---
    movea.l (sp)+,a0
    bne.s hint_49aa
hint_493c:
; --- unverified ---
    tst.b d4
    bne.s hint_49aa
hint_4940:
; --- unverified ---
    move.l d2,d5
    bsr.w sub_0bce
hint_4946:
; --- unverified ---
    beq.w loc_8436
hint_494a:
; --- unverified ---
    lea 362(a6),a2 ; app+$16A
    moveq #2,d3
    move.l 2122(a6),d4 ; app+$84A
    move.b 6(a0),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.s hint_496a
hint_495e:
; --- unverified ---
    bsr.w sub_0cb6
hint_4962:
; --- unverified ---
    move.l d5,d2
    move.b -1(a4),d1
    bra.s hint_490a
hint_496a:
; --- unverified ---
    lea 346(a6),a2 ; app+$15A
    tst.l (a2)
    beq.w loc_8442
hint_4974:
; --- unverified ---
    bsr.w sub_0d4c
hint_4978:
; --- unverified ---
    bra.s hint_4962
hint_497a:
; --- unverified ---
    bsr.w sub_0bce
hint_497e:
; --- unverified ---
    bne.w loc_844e
hint_4982:
; --- unverified ---
    cmpi.b #$2,13(a1)
    bne.w loc_844e
hint_498c:
; --- unverified ---
    move.l 8(a1),d0
    cmp.l 2122(a6),d0 ; app+$84A
    bne.w loc_843e
hint_4998:
; --- unverified ---
    bset #6,12(a1)
    bne.w loc_8436
hint_49a2:
; --- unverified ---
    bsr.w sub_16cc
hint_49a6:
; --- unverified ---
    bra.w hint_490a
hint_49aa:
; --- unverified ---
    rts
hint_49ac:
; --- unverified ---
    bsr.w hint_6ac8
hint_49b0:
; --- unverified ---
    tst.l d2
    bmi.w hint_3a66
hint_49b6:
; --- unverified ---
    move.l d2,-(sp)
    bsr.w hint_99b8
hint_49bc:
; --- unverified ---
    movem.l (sp)+,d2
    bne.w hint_3a66
hint_49c4:
; --- unverified ---
    clr.l 386(a6) ; app+$182
    sub.l 572(a6),d2 ; app+$23C
    move.l d2,398(a6) ; app+$18E
    move.b -1(a4),d1
    rts
hint_49d6:
; --- unverified ---
    sub.l d1,d2
    bcs.s hint_49e8
hint_49da:
; --- unverified ---
    beq.s hint_49e6
hint_49dc:
; --- unverified ---
    move.l d2,d4
    moveq #0,d3
    moveq #0,d1
    bsr.w hint_2958
hint_49e6:
    dc.b    $70,$00
hint_49e8:
; --- unverified ---
    rts
hint_49ea:
; --- unverified ---
    clr.l 2122(a6) ; app+$84A
    moveq #10,d1
    rts
hint_49f2:
; --- unverified ---
    bsr.w sub_16cc
hint_49f6:
; --- unverified ---
    bne.s hint_49ea
hint_49f8:
; --- unverified ---
    tst.b d4
    bne.s hint_49ea
hint_49fc:
; --- unverified ---
    move.l d2,2122(a6) ; app+$84A
    bra.w hint_2b7e
hint_4a04:
; --- unverified ---
    cmpi.b #$a,289(a6) ; app+$121
    blt.w sub_3132
hint_4a0e:
; --- unverified ---
    move.w d6,(a5)+
    cmp.b #$23,d1
    bne.w hint_846a
hint_4a18:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_4a1e:
; --- unverified ---
    bra.w hint_1ad0
hint_4a22:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_4a2c:
; --- unverified ---
    bsr.s hint_4a3c
hint_4a2e:
; --- unverified ---
    or.w d2,d6
    move.w d6,(a5)+
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_4a3a:
; --- unverified ---
    rts
hint_4a3c:
; --- unverified ---
    bsr.w sub_177e
hint_4a40:
; --- unverified ---
    bne.s hint_4a50
hint_4a42:
; --- unverified ---
    andi.w #$7,d2
    andi.w #$1,d0
    lsl.w #3,d0
    or.w d0,d2
    rts
hint_4a50:
; --- unverified ---
    moveq #46,d0
    bra.w loc_8486
hint_4a56:
; --- unverified ---
    bsr.w hint_2372
hint_4a5a:
; --- unverified ---
    st 571(a6) ; app+$23B
    bsr.w hint_16e6
    dc.b    $00,$3d,$4e,$75,$61,$1c
    dc.b    "DATA",0
    dc.b    $00,$61,$14,$42,$53,$53,$00,$61,$0e
    dc.b    "TEXT",0
    dc.b    $00,$61,$06,$43,$4f
sub_4a80:
    dc.b    $44,$45,$00,$00,$20,$5f,$43,$ee,$04,$6e,$61,$00,$4b,$e8
hint_4a8e:
    dc.b    $12,$fc,$00,$0a
hint_4a92:
; --- unverified ---
    movem.l d1/a4,-(sp)
    lea 1134(a6),a4 ; app+$46E
    move.b (a4)+,d1
    bsr.s hint_4b18
hint_4a9e:
; --- unverified ---
    movem.l (sp)+,d1/a4
    rts
hint_4aa4:
    dc.b    $41,$ee,$04,$6e,$10,$c1
hint_4aaa:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s hint_4afe
hint_4ab2:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_4afe
hint_4ab8:
; --- unverified ---
    cmp.b #$2c,d1
    beq.s hint_4ac8
hint_4abe:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_4afe
hint_4ac4:
; --- unverified ---
    move.b d1,(a0)+
    bra.s hint_4aaa
hint_4ac8:
; --- unverified ---
    move.b (a4)+,d0
    lea str_4b04(pc),a1
    subi.b #$30,d0
    bcs.s hint_4b12
hint_4ad4:
; --- unverified ---
    beq.s hint_4ae6
hint_4ad6:
; --- unverified ---
    lea 49(pc),a1
    subq.b #1,d0
    beq.s hint_4ae6
hint_4ade:
; --- unverified ---
    lea str_4b0e(pc),a1
    subq.b #1,d0
    bne.s hint_4b12
hint_4ae6:
; --- unverified ---
    move.b #$2c,(a0)+
    btst #1,541(a6) ; app+$21D
    bne.s hint_4af6
hint_4af2:
    dc.b    $41,$ee,$04,$6e
hint_4af6:
    dc.b    $12,$1c
hint_4af8:
; --- unverified ---
    move.b (a1)+,(a0)+
    bne.s hint_4af8
hint_4afc:
    dc.b    $53,$88
hint_4afe:
; --- unverified ---
    move.b #$a,(a0)
    bra.s hint_4a92
str_4b04:
    dc.b    $43,$4f
sub_4b06:
    dc.b    $44,$45,$00
    dc.b    "DATA",0
str_4b0e:
    dc.b    $42,$53,$53,$00
hint_4b12:
; --- unverified ---
    moveq #102,d0
    bra.w loc_8482
hint_4b18:
; --- unverified ---
    bsr.w sub_79cc
hint_4b1c:
; --- unverified ---
    move.b -1(a4),d1
    moveq #1,d3
    bsr.w sub_7952
hint_4b26:
; --- unverified ---
    moveq #10,d1
    rts
hint_4b2a:
; --- unverified ---
    bsr.w hint_2b02
hint_4b2e:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_4b7c
hint_4b34:
; --- unverified ---
    move.l a0,-(sp)
    bsr.w hint_6ab2
hint_4b3a:
; --- unverified ---
    movea.l (sp)+,a0
    movem.l d2-d3,-(sp)
    bsr.w sub_0bce
hint_4b44:
; --- unverified ---
    movem.l (sp)+,d4-d5
    bne.s hint_4b5a
hint_4b4a:
; --- unverified ---
    btst #7,12(a1)
    beq.w loc_8436
hint_4b54:
; --- unverified ---
    move.b d5,d3
    move.l d4,d2
    bra.s hint_4b9c
hint_4b5a:
; --- unverified ---
    pea pcref_4b72(pc)
    move.b d5,d3
    lea 362(a6),a2 ; app+$16A
    subq.b #2,d5
    beq.w sub_0cb6
hint_4b6a:
; --- unverified ---
    lea 354(a6),a2 ; app+$162
    bra.w sub_0cb6
pcref_4b72:
; --- unverified ---
    bset #7,12(a1)
    bra.w pcref_2b7a
hint_4b7c:
; --- unverified ---
    bsr.w sub_0bce
hint_4b80:
; --- unverified ---
    bne.w loc_844e
hint_4b84:
; --- unverified ---
    btst #7,12(a1)
    beq.w loc_844e
hint_4b8e:
; --- unverified ---
    move.l a1,-(sp)
    bsr.w sub_16a8
hint_4b94:
    dc.b    $22,$5f,$08,$e9,$00,$06,$00,$0c
hint_4b9c:
; --- unverified ---
    move.l d2,8(a1)
    cmp.b 13(a1),d3
    bne.w loc_8436
hint_4ba8:
; --- unverified ---
    bra.w hint_2b7e
hint_4bac:
; --- unverified ---
    cmp.b #$23,d1
    beq.s hint_4c0e
hint_4bb2:
; --- unverified ---
    addq.l #2,a5
    bsr.w sub_1872
hint_4bb8:
; --- unverified ---
    move.b d5,d0
    andi.b #$78,d0
    beq.s hint_4bec
hint_4bc0:
; --- unverified ---
    move.w d6,d2
    andi.w #$18,d2
    lsl.w #6,d2
    andi.w #$ff00,d6
    ori.w #$c0,d6
    or.w d2,d6
    movea.l 588(a6),a0 ; app+$24C
    move.w d6,(a0)
    bsr.w hint_276a
hint_4bdc:
; --- unverified ---
    moveq #60,d0
    bra.w hint_1704
hint_4be2:
; --- unverified ---
    ori.w #$200,d6
    or.b d5,d6
    move.w d6,(a5)+
    rts
hint_4bec:
; --- unverified ---
    movea.l 588(a6),a5 ; app+$24C
    bsr.w hint_4f1a
hint_4bf4:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_4be2
hint_4bfa:
; --- unverified ---
    ori.b #$20,d6
    move.w d6,(a5)
    add.b d5,d5
    or.b d5,(a5)+
    move.b (a4)+,d1
    bsr.w loc_1760
hint_4c0a:
; --- unverified ---
    or.b d2,(a5)+
    rts
hint_4c0e:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_4c14:
; --- unverified ---
    bsr.w sub_3242
hint_4c18:
; --- unverified ---
    ror.w #7,d2
    or.w d2,d6
    bsr.w hint_4f1a
hint_4c20:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_4c28:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_4c2e:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    rts
hint_4c34:
; --- unverified ---
    bsr.w sub_16cc
hint_4c38:
; --- unverified ---
    cmp.l #$ff,d2
    bcc.w hint_4814
hint_4c42:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_4c58
hint_4c48:
; --- unverified ---
    tst.b 2389(a6) ; app+$955
    beq.s hint_4c58
hint_4c4e:
    dc.b    $38,$02
hint_4c50:
; --- unverified ---
    bsr.w sub_8e8c
hint_4c54:
; --- unverified ---
    subq.w #1,d4
    bne.s hint_4c50
hint_4c58:
; --- unverified ---
    move.b -1(a4),d1
    st 275(a6) ; app+$113
    rts
hint_4c62:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_4c6e
hint_4c68:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_4c6e:
; --- unverified ---
    move.w d6,(a5)+
    cmp.b #$23,d1
    bne.w hint_846a
hint_4c78:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_0db6
hint_4c7e:
; --- unverified ---
    bsr.w hint_1ad0
hint_4c82:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_4c8a:
; --- unverified ---
    rts
hint_4c8c:
; --- unverified ---
    bsr.w hint_276a
hint_4c90:
; --- unverified ---
    bsr.w loc_1760
hint_4c94:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    rts
hint_4c9a:
; --- unverified ---
    bsr.w hint_2372
hint_4c9e:
; --- unverified ---
    bsr.w hint_16e6
    dc.b    $00,$3d,$4e,$75
sub_4ca6:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_4cae:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_4cb6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16a8
hint_4cbc:
; --- unverified ---
    bsr.w hint_78d8
hint_4cc0:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    cmp.l #$10,d2
    bcc.s hint_4cce
hint_4ccc:
; --- unverified ---
    rts
hint_4cce:
; --- unverified ---
    moveq #29,d0
    bra.w loc_8486
hint_4cd4:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_4cde:
; --- unverified ---
    bsr.w hint_2350
hint_4ce2:
; --- unverified ---
    move.w #$4c40,(a5)+
    move.w d6,(a5)+
    bsr.w hint_16e0
hint_4cf6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_4cfc:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    cmp.b #$3a,d1
    beq.s hint_4d12
hint_4d06:
; --- unverified ---
    or.b d2,3(a0)
    lsl.b #4,d2
    or.b d2,2(a0)
    rts
hint_4d12:
; --- unverified ---
    move.b (a4)+,d1
    or.b d2,3(a0)
    bsr.w loc_1760
hint_4d1c:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    lsl.b #4,d2
    or.b d2,2(a0)
    rts
hint_4d28:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    blt.w sub_3132
hint_4d32:
    dc.b    $3a,$c6
hint_4d34:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    addq.l #1,a0
    move.b 569(a6),d0 ; app+$239
    beq.s hint_4d7a
hint_4d40:
; --- unverified ---
    cmp.b #$3,d0
    beq.s hint_4d64
hint_4d46:
; --- unverified ---
    cmp.b #$2,d0
    bne.w loc_844a
hint_4d4e:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_4d56:
; --- unverified ---
    move.b (a4)+,d1
    ori.b #$2,(a0)
    bsr.w sub_0db6
hint_4d60:
; --- unverified ---
    bra.w hint_1ad0
hint_4d64:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_4d6c:
; --- unverified ---
    move.b (a4)+,d1
    ori.b #$3,(a0)
    bsr.w sub_0db6
hint_4d76:
; --- unverified ---
    bra.w hint_1ab0
hint_4d7a:
; --- unverified ---
    cmp.b #$23,d1
    beq.s hint_4d4e
hint_4d80:
; --- unverified ---
    ori.b #$4,(a0)
    rts
hint_4d86:
; --- unverified ---
    bsr.w hint_4f1a
hint_4d8a:
; --- unverified ---
    bsr.w hint_16e6
    dc.b    $00,$3d,$4e,$75,$0c,$2e,$00,$14,$01,$21,$6d,$ec,$61,$00,$01,$7e
    dc.b    $61,$00,$c9,$46,$00,$ff,$4e,$75
sub_4da6:
    dc.b    $45,$ee,$0b,$82
hint_4daa:
    dc.b    $50,$ee,$01,$13
hint_4dae:
; --- unverified ---
    moveq #0,d2
    moveq #10,d3
    tst.b 568(a6) ; app+$238
    bne.s hint_4dc0
hint_4db8:
; --- unverified ---
    tst.b (a2)
    beq.s hint_4dc0
hint_4dbc:
; --- unverified ---
    moveq #10,d1
    rts
hint_4dc0:
; --- unverified ---
    cmp.b #$27,d1
    bne.s hint_4dca
hint_4dc6:
    dc.b    $76,$27
hint_4dc8:
    dc.b    $12,$1c
hint_4dca:
; --- unverified ---
    cmp.b d1,d3
    beq.s hint_4de2
hint_4dce:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_4dea
hint_4dd4:
; --- unverified ---
    move.b d1,(a2)+
    addq.b #1,d2
    cmp.b #$50,d2
    bne.s hint_4dc8
hint_4dde:
; --- unverified ---
    moveq #10,d1
    bra.s hint_4dea
hint_4de2:
; --- unverified ---
    cmp.b #$a,d3
    beq.s hint_4dea
hint_4de8:
    dc.b    $12,$1c
hint_4dea:
; --- unverified ---
    clr.b (a2)
    rts
hint_4dee:
; --- unverified ---
    lea 3027(a6),a2 ; app+$BD3
    bra.s hint_4daa
hint_4df4:
; --- unverified ---
    bsr.w sub_176a
hint_4df8:
; --- unverified ---
    or.b d2,d6
    move.w d6,(a5)+
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_4e04:
; --- unverified ---
    rts
hint_4e06:
; --- unverified ---
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s hint_4e10
hint_4e0e:
; --- unverified ---
    rts
hint_4e10:
; --- unverified ---
    addq.l #4,sp
    moveq #10,d1
    rts
hint_4e16:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_4e06
hint_4e1a:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    bsr.w sub_76b8
hint_4e22:
; --- unverified ---
    bne.w loc_8486
hint_4e26:
; --- unverified ---
    move.w d1,-(sp)
    bsr.s hint_4e34
hint_4e2a:
; --- unverified ---
    move.w (sp)+,d1
    cmp.b #$2c,d1
    beq.s hint_4e16
hint_4e32:
; --- unverified ---
    rts
hint_4e34:
; --- unverified ---
    move.b 6(a0),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.w loc_8442
hint_4e40:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s loc_4e60
hint_4e46:
; --- unverified ---
    bsr.w sub_0bce
hint_4e4a:
; --- unverified ---
    bne.s loc_4e62
sub_4e4c:
    move.b 12(a1),d0
    andi.b #$90,d0
    bne.s loc_4e62
loc_4e56:
    bset #5,12(a1)
    beq.w loc_96d6
loc_4e60:
    rts
loc_4e62:
    moveq #44,d0
    bra.w loc_8486
hint_4e68:
; --- unverified ---
    moveq #43,d0
    bra.w loc_8482
hint_4e6e:
; --- unverified ---
    move.b (a4)+,d1
    bra.s hint_4e76
hint_4e72:
; --- unverified ---
    moveq #44,d5
    bsr.s hint_4e06
hint_4e76:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    bsr.w sub_76b8
hint_4e7e:
; --- unverified ---
    bne.w loc_8486
hint_4e82:
; --- unverified ---
    move.b 6(a0),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.s hint_4e68
hint_4e8c:
; --- unverified ---
    moveq #1,d3
    cmpi.b #$3,569(a6) ; app+$239
    bne.s hint_4e98
hint_4e96:
    dc.b    $76,$02
hint_4e98:
; --- unverified ---
    move.w d1,-(sp)
    move.w d3,-(sp)
    bsr.w sub_0bce
hint_4ea0:
; --- unverified ---
    movem.w (sp)+,d3
    beq.s hint_4eb0
hint_4ea6:
; --- unverified ---
    movea.l 358(a6),a1 ; app+$166
    moveq #0,d4
    bsr.w sub_0cba
hint_4eb0:
; --- unverified ---
    bsr.s hint_4ec4
hint_4eb2:
; --- unverified ---
    move.w (sp)+,d1
    move.b d1,d5
    cmp.b #$2c,d1
    beq.s hint_4e6e
hint_4ebc:
; --- unverified ---
    cmp.b #$3d,d1
    beq.s hint_4e6e
hint_4ec2:
; --- unverified ---
    rts
hint_4ec4:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.s hint_4f12
hint_4ecc:
; --- unverified ---
    cmp.b 13(a1),d3
    bne.s hint_4f12
hint_4ed2:
; --- unverified ---
    btst #5,12(a1)
    bne.s hint_4f12
hint_4eda:
; --- unverified ---
    btst #7,12(a1)
    bne.s hint_4f12
hint_4ee2:
; --- unverified ---
    move.b 23(a1),d0
    cmp.b 278(a6),d0 ; app+$116
    beq.s hint_4f12
hint_4eec:
; --- unverified ---
    bset #4,12(a1)
    bne.s hint_4f10
hint_4ef4:
; --- unverified ---
    movea.l 318(a6),a0 ; app+$13E
    cmp.b #$2c,d5
    beq.s hint_4f06
hint_4efe:
; --- unverified ---
    bset #2,12(a1)
    bra.s hint_4f0a
hint_4f06:
    dc.b    $52,$68,$00,$14
hint_4f0a:
    dc.b    $33,$68,$00,$14,$00,$14
hint_4f10:
; --- unverified ---
    rts
hint_4f12:
; --- unverified ---
    move.w #$2b,d0
    bra.w loc_8486
hint_4f1a:
; --- unverified ---
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    or.b pcref_4f26(pc,d0.w),d6
    rts
pcref_4f26:
    dc.b    $40,$00,$40,$80
hint_4f2a:
; --- unverified ---
    move.l a5,2158(a6) ; app+$86E
    cmp.b #$5b,d1
    beq.w hint_4fdc
hint_4f36:
; --- unverified ---
    moveq #0,d7
    lea 2126(a6),a3 ; app+$84E
    lea 2208(a6),a0 ; app+$8A0
    move.l a0,2368(a6) ; app+$940
    pea -1(a4)
    bsr.w hint_53ae
hint_4f4c:
; --- unverified ---
    movea.l (sp)+,a2
    bne.w hint_56b8
hint_4f52:
; --- unverified ---
    btst #0,d7
    bne.s hint_4f8c
hint_4f58:
; --- unverified ---
    cmp.b #$29,d1
    bne.w hint_500e
hint_4f60:
; --- unverified ---
    btst #1,d7
    beq.w hint_5026
hint_4f68:
; --- unverified ---
    tst.b 9(a3)
    bne.w hint_5026
hint_4f70:
; --- unverified ---
    move.b 8(a3),d0
    bmi.w hint_5026
hint_4f78:
; --- unverified ---
    moveq #16,d5
    or.b d0,d5
    move.b (a4)+,d1
    cmp.b #$2b,d1
    bne.s hint_4f8a
hint_4f84:
    dc.b    $08,$c5,$00,$03,$12,$1c
hint_4f8a:
; --- unverified ---
    rts
hint_4f8c:
; --- unverified ---
    cmp.b #$2c,d1
    beq.w hint_5014
hint_4f94:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$2e,d1
    bne.w hint_4fac
hint_4f9e:
; --- unverified ---
    move.l (a3),d2
    move.w 4(a3),d3
    move.b 6(a3),d4
    bra.w hint_1988
hint_4fac:
; --- unverified ---
    cmp.b #$9,d1
    beq.w hint_4fca
hint_4fb4:
; --- unverified ---
    cmp.b #$20,d1
    beq.w hint_4fca
hint_4fbc:
; --- unverified ---
    cmp.b #$2c,d1
    beq.s hint_4fca
hint_4fc2:
; --- unverified ---
    cmp.b #$a,d1
    bne.w hint_192a
hint_4fca:
; --- unverified ---
    movea.l a2,a4
    move.b -1(a4),d1
    bsr.w sub_1208
hint_4fd4:
; --- unverified ---
    bsr.w hint_1930
hint_4fd8:
; --- unverified ---
    bra.w sub_1208
hint_4fdc:
    dc.b    $7e,$00,$47,$ee,$08,$4e
hint_4fe2:
; --- unverified ---
    swap d7
    bset #7,d7
    bne.w hint_56b8
hint_4fec:
    dc.b    $47,$ee,$08,$5e,$41,$ee,$08,$f0,$2d,$48,$09,$40,$12,$1c
hint_4ffa:
; --- unverified ---
    cmp.b #$5d,d1
    beq.s hint_5034
hint_5000:
; --- unverified ---
    cmp.b #$29,d1
    beq.s hint_5026
hint_5006:
; --- unverified ---
    bsr.w hint_53ae
hint_500a:
; --- unverified ---
    bne.w hint_56b8
hint_500e:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_4ffa
hint_5014:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$5b,d1
    bne.s hint_5006
hint_501c:
; --- unverified ---
    tst.b 14(a3)
    bgt.s hint_4fe2
hint_5022:
; --- unverified ---
    bra.w hint_56b8
hint_5026:
; --- unverified ---
    tst.b 14(a3)
    ble.w hint_56b8
hint_502e:
; --- unverified ---
    move.b (a4)+,d1
    bra.w hint_504e
hint_5034:
; --- unverified ---
    tst.b 14(a3)
    bge.w hint_56b8
hint_503c:
; --- unverified ---
    swap d7
    lea 2126(a6),a3 ; app+$84E
    lea 2208(a6),a0 ; app+$8A0
    move.l a0,2368(a6) ; app+$940
    move.b (a4)+,d1
    bra.s hint_500e
hint_504e:
; --- unverified ---
    tst.b 14(a3)
    bge.s hint_5062
hint_5054:
    dc.b    $48,$47,$47,$ee,$08,$4e,$41,$ee,$08,$a0,$2d,$48,$09,$40
hint_5062:
; --- unverified ---
    move.l d7,d2
    andi.l #$70007,d2
    move.l d2,d0
    swap d0
    lsl.w #3,d0
    or.w d2,d0
    add.w d0,d0
    add.w d0,d0
    moveq #48,d5
    btst #3,d7
    beq.s hint_5080
hint_507e:
    dc.b    $7a,$3b
hint_5080:
; --- unverified ---
    btst #23,d7
    beq.w hint_5552
hint_5088:
; --- unverified ---
    move.b 289(a6),d4 ; app+$121
    cmp.b #$20,d4
    beq.w sub_3132
hint_5094:
; --- unverified ---
    move.w #$1d0,d4
    move.l pcref_50ba(pc,d0.w),d2
    or.w d2,d4
    swap d2
    move.l a5,-(sp)
    move.w d4,(a5)+
    jsr pcref_50ba(pc,d2.w) ; unresolved_indirect_hint:pcindex.brief
hint_50a8:
; --- unverified ---
    movea.l (sp)+,a0
    btst #6,d4
    beq.s hint_50b4
hint_50b0:
    dc.b    $08,$84,$00,$02
hint_50b4:
; --- unverified ---
    move.w d4,(a0)
    moveq #0,d0
    rts
pcref_50ba:
    dc.b    $01,$20,$00,$01,$01,$20,$00,$01,$01,$00,$00,$01,$01,$00,$00,$01
    dc.b    $01,$20,$00,$01,$01,$20,$00,$01,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$20,$00,$05,$01,$20,$00,$05,$01,$00,$00,$05,$01,$00,$00,$05
    dc.b    $01,$20,$00,$05,$01,$20,$00,$05,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$20,$00,$05,$01,$20,$00,$05,$01,$00,$00,$05,$01,$00,$00,$05
    dc.b    $01,$20,$00,$05,$01,$20,$00,$05,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$20,$00,$05,$01,$20,$00,$05,$01,$00,$00,$05,$01,$00,$00,$05
    dc.b    $01,$20,$00,$05,$01,$20,$00,$05,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$62,$00,$01,$01,$62,$00,$01,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$62,$00,$01,$01,$62,$00,$01,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$62,$00,$01,$01,$62,$00,$01,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $01,$62,$00,$01,$01,$62,$00,$01,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00,$05,$fe,$00,$00
    dc.b    $08,$87,$00,$01,$08,$c7,$00,$02,$70,$08,$d0,$2e,$08,$56,$1d,$40
    dc.b    $08,$58,$1d,$6e,$08,$57,$08,$69,$51,$ee,$08,$5a,$51,$ee,$08,$5b
    dc.b    $47,$ee,$08,$5e,$41,$ee,$08,$f0,$2d,$48,$09,$40,$08,$07,$00,$10
    dc.b    $67,$04
hint_51ec:
; --- unverified ---
    bsr.w hint_5274
hint_51f0:
; --- unverified ---
    btst #17,d7
    beq.s hint_51fa
hint_51f6:
; --- unverified ---
    bsr.w hint_525e
hint_51fa:
; --- unverified ---
    lea 2126(a6),a3 ; app+$84E
    lea 2208(a6),a0 ; app+$8A0
    move.l a0,2368(a6) ; app+$940
    btst #2,d7
    beq.s hint_5210
hint_520c:
; --- unverified ---
    bsr.w hint_530a
hint_5210:
; --- unverified ---
    btst #0,d7
    beq.s hint_521a
hint_5216:
; --- unverified ---
    bsr.w hint_5334
hint_521a:
; --- unverified ---
    rts
hint_521c:
; --- unverified ---
    lea 2142(a6),a3 ; app+$85E
    lea 2288(a6),a0 ; app+$8F0
    move.l a0,2368(a6) ; app+$940
    btst #16,d7
    beq.s hint_5232
hint_522e:
; --- unverified ---
    bsr.w hint_5274
hint_5232:
; --- unverified ---
    btst #17,d7
    beq.s hint_523c
hint_5238:
; --- unverified ---
    bsr.w hint_525e
hint_523c:
; --- unverified ---
    btst #18,d7
    beq.s hint_5246
hint_5242:
; --- unverified ---
    bsr.w hint_530a
hint_5246:
; --- unverified ---
    lea 2126(a6),a3 ; app+$84E
    lea 2208(a6),a0 ; app+$8A0
    move.l a0,2368(a6) ; app+$940
    btst #0,d7
    beq.s hint_525c
hint_5258:
; --- unverified ---
    bsr.w hint_5334
hint_525c:
; --- unverified ---
    rts
hint_525e:
; --- unverified ---
    tst.b 9(a3)
    bne.s hint_5272
hint_5264:
; --- unverified ---
    bclr #7,d4
    btst #3,d7
    bne.s hint_5272
hint_526e:
    dc.b    $8a,$2b,$00,$08
hint_5272:
; --- unverified ---
    rts
hint_5274:
; --- unverified ---
    move.l (a3),d2
    move.w 4(a3),d3
    btst #7,271(a6) ; app+$10F
    beq.s hint_52c2
hint_5282:
; --- unverified ---
    cmp.b #$1,d3
    bne.s hint_52a4
hint_5288:
; --- unverified ---
    move.l d2,-(sp)
    sub.l 572(a6),d2 ; app+$23C
    move.l 2158(a6),d0 ; app+$86E
    sub.l 588(a6),d0 ; app+$24C
    sub.l d0,d2
    movea.w d2,a0
    cmpa.l d2,a0
    movem.l (sp)+,d2
    bne.s hint_52c2
hint_52a2:
; --- unverified ---
    bra.s hint_52aa
hint_52a4:
; --- unverified ---
    movea.w d2,a0
    cmpa.l d2,a0
    bne.s hint_52c2
hint_52aa:
; --- unverified ---
    tst.b 6(a3)
    bne.s hint_52c2
hint_52b0:
; --- unverified ---
    bsr.w sub_8dce
hint_52b4:
; --- unverified ---
    bne.s hint_52c2
hint_52b6:
; --- unverified ---
    move.b #$1,7(a3)
    moveq #19,d0
    bsr.w hint_8808
hint_52c2:
; --- unverified ---
    move.b 7(a3),d0
    cmp.b #$3,d0
    beq.w hint_5694
hint_52ce:
; --- unverified ---
    subq.b #1,d0
    beq.s hint_52f6
hint_52d2:
; --- unverified ---
    bpl.s hint_52da
hint_52d4:
; --- unverified ---
    tst.b 301(a6) ; app+$12D
    bne.s hint_52f6
hint_52da:
; --- unverified ---
    ori.b #$30,d4
    btst #3,d7
    beq.w hint_1ab0
hint_52e6:
; --- unverified ---
    tst.b 9(a3)
    bne.w hint_1ab0
hint_52ee:
; --- unverified ---
    bset #0,d5
    bra.w hint_5706
hint_52f6:
; --- unverified ---
    bset #5,d4
    bclr #4,d4
    btst #3,d7
    beq.w hint_1ad0
hint_5306:
; --- unverified ---
    bra.w hint_56c4
hint_530a:
; --- unverified ---
    tst.b 11(a3)
    bne.s hint_5332
hint_5310:
    dc.b    $08,$84,$00,$06,$70,$0f,$c0,$2b,$00,$0a,$e8,$58,$88,$40,$70,$01
    dc.b    $c0,$2b,$00,$0c,$ea,$58,$88,$40,$70,$03,$c0,$2b,$00,$0d,$ee,$58
    dc.b    $88,$40
hint_5332:
; --- unverified ---
    rts
hint_5334:
; --- unverified ---
    bset #1,d4
    move.l (a3),d2
    move.w 4(a3),d3
    move.b 7(a3),d0
    bne.s hint_5386
hint_5344:
; --- unverified ---
    btst #0,270(a6) ; app+$10E
    beq.s hint_5386
hint_534c:
; --- unverified ---
    move.l d2,-(sp)
    sub.l 572(a6),d2 ; app+$23C
    move.l 2158(a6),d0 ; app+$86E
    sub.l 588(a6),d0 ; app+$24C
    sub.l d0,d2
    movea.w d2,a0
    cmpa.l d2,a0
    movem.l (sp)+,d2
    bne.s hint_5386
hint_5366:
; --- unverified ---
    bra.s hint_536e
hint_5368:
; --- unverified ---
    movea.w d2,a0
    cmpa.l d2,a0
    bne.s hint_5386
hint_536e:
; --- unverified ---
    tst.b 6(a3)
    bne.s hint_5386
hint_5374:
; --- unverified ---
    bsr.w sub_8dce
hint_5378:
; --- unverified ---
    bne.s hint_5386
hint_537a:
; --- unverified ---
    move.b #$1,7(a3)
    moveq #20,d0
    bsr.w hint_8808
hint_5386:
; --- unverified ---
    move.b 7(a3),d0
    cmp.b #$3,d0
    beq.w hint_5694
hint_5392:
; --- unverified ---
    subq.b #1,d0
    beq.s hint_53a6
hint_5396:
; --- unverified ---
    bpl.s hint_539e
hint_5398:
; --- unverified ---
    tst.b 302(a6) ; app+$12E
    bne.s hint_53a6
hint_539e:
; --- unverified ---
    bset #0,d4
    bra.w hint_1ab0
hint_53a6:
    dc.b    $08,$84
hint_53a8:
    dc.b    $00,$00
hint_53ae:
; --- unverified ---
    moveq #0,d3
    clr.l 1134(a6) ; app+$46E
    bsr.w sub_177e
hint_53b8:
; --- unverified ---
    bne.w hint_5462
hint_53bc:
; --- unverified ---
    add.b d0,d0
    add.b d0,d0
    add.b d0,d0
    add.b d2,d0
    cmp.b #$2e,d1
    beq.s hint_540a
hint_53ca:
; --- unverified ---
    cmp.b #$2a,d1
    beq.s hint_5404
hint_53d0:
; --- unverified ---
    cmp.b #$8,d0
    bcc.s hint_53f0
hint_53d6:
; --- unverified ---
    move.b d0,10(a3)
    move.b d3,11(a3)
    sf 12(a3)
    sf 13(a3)
    bset #2,d7
    bne.w hint_56b8
hint_53ee:
; --- unverified ---
    rts
hint_53f0:
; --- unverified ---
    subq.b #8,d0
    move.b d0,8(a3)
    move.b d3,9(a3)
    bset #1,d7
    bne.w hint_56b8
hint_5402:
; --- unverified ---
    rts
hint_5404:
    dc.b    $51,$eb
hint_5406:
    dc.b    $00,$0c
hint_540a:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    sf 12(a3)
    cmp.b #$57,d1
    beq.s hint_5428
hint_541c:
; --- unverified ---
    addq.b #1,12(a3)
    cmp.b #$4c,d1
    bne.w hint_56b8
hint_5428:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$2a,d1
    beq.s hint_5446
hint_5430:
; --- unverified ---
    move.b d0,10(a3)
    sf 13(a3)
    move.b d3,11(a3)
    bset #2,d7
    bne.w hint_56b8
hint_5444:
; --- unverified ---
    rts
hint_5446:
; --- unverified ---
    move.b d3,11(a3)
    move.b d0,10(a3)
    move.b (a4)+,d1
    bsr.w hint_5740
hint_5454:
; --- unverified ---
    move.b d0,13(a3)
    bset #2,d7
    bne.w hint_56b8
hint_5460:
; --- unverified ---
    rts
hint_5462:
; --- unverified ---
    move.l 1134(a6),d0 ; app+$46E
    beq.w hint_5506
hint_546a:
; --- unverified ---
    lea -1(a4),a0
    move.b 1139(a6),d0 ; app+$473
    subq.b #2,d0
    beq.w hint_54d6
hint_5478:
; --- unverified ---
    subq.b #1,d0
    bne.w hint_5506
hint_547e:
; --- unverified ---
    move.b (a0)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b #$5a,d0
    bne.w hint_5506
hint_548e:
; --- unverified ---
    move.b (a0)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    subi.b #$44,d0
    sne d2
    beq.s hint_54e8
hint_549e:
; --- unverified ---
    addq.b #3,d0
    beq.s hint_54e8
hint_54a2:
; --- unverified ---
    cmp.b #$f,d0
    bne.w hint_5506
hint_54aa:
    dc.b    $50,$c3
hint_54ac:
; --- unverified ---
    move.b (a0)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b #$43,d0
    bne.s hint_5506
hint_54ba:
; --- unverified ---
    movea.l a0,a4
    move.b (a4)+,d1
    st 8(a3)
    move.b d3,9(a3)
    ori.l #$80008,d7
    bset #1,d7
    bne.w hint_56b8
hint_54d4:
; --- unverified ---
    rts
hint_54d6:
; --- unverified ---
    move.b (a0)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    moveq #0,d3
    cmp.b #$50,d0
    beq.s hint_54ac
hint_54e6:
; --- unverified ---
    bra.s hint_5506
hint_54e8:
; --- unverified ---
    move.b (a0)+,d0
    subi.b #$30,d0
    bcs.s hint_5506
hint_54f0:
; --- unverified ---
    cmp.b #$8,d0
    bcc.s hint_5506
hint_54f6:
; --- unverified ---
    st d3
    movea.l a0,a4
    move.b (a4)+,d1
    andi.b #$1,d2
    exg
    bra.w hint_53bc
hint_5506:
; --- unverified ---
    move.l a3,-(sp)
    bsr.w sub_0db6
hint_550c:
; --- unverified ---
    movea.l (sp)+,a3
    move.l d2,(a3)
    move.w d3,4(a3)
    move.b d4,6(a3)
    moveq #0,d0
    cmp.b #$2e,d1
    bne.s hint_5544
hint_5520:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    moveq #1,d0
    cmp.b #$57,d1
    beq.s hint_5542
hint_5530:
; --- unverified ---
    moveq #2,d0
    cmp.b #$4c,d1
    beq.s hint_5542
hint_5538:
; --- unverified ---
    moveq #3,d0
    cmp.b #$42,d1
    bne.w hint_56b8
hint_5542:
    dc.b    $12,$1c
hint_5544:
; --- unverified ---
    move.b d0,7(a3)
    bset #0,d7
    bne.w hint_56b8
hint_5550:
; --- unverified ---
    rts
hint_5552:
; --- unverified ---
    move.w #$1d0,d4
    move.l pcref_556e(pc,d0.w),d0
    or.w d0,d4
    swap d0
    move.l a5,-(sp)
    move.w d4,(a5)+
    jsr pcref_5576(pc,d0.w) ; unresolved_indirect_hint:pcindex.brief
hint_5566:
; --- unverified ---
    movea.l (sp)+,a0
    btst #6,d4
    beq.s hint_5572
pcref_556e:
    dc.b    $08,$84,$00,$02
hint_5572:
; --- unverified ---
    move.w d4,(a0)
    rts
pcref_5576:
    dc.b    $00,$18,$00,$00,$00,$34,$00,$00,$00,$ba,$00,$00,$00,$ba,$00,$00
    dc.b    $00,$78,$00,$00,$00,$ba,$00,$00,$4a,$2b,$00,$09,$66,$00,$00,$9c
    dc.b    $4a,$2b,$00,$08,$6a,$00,$00,$94
hint_559e:
; --- unverified ---
    moveq #58,d5
    subq.l #2,a5
    addq.l #8,sp
    move.w #$fffe,(a5)+
    rts
hint_55aa:
; --- unverified ---
    tst.b 9(a3)
    bne.w hint_5630
hint_55b2:
; --- unverified ---
    cmpi.b #$2,7(a3)
    beq.w hint_5630
hint_55bc:
; --- unverified ---
    subq.l #2,a5
    addq.l #8,sp
    move.l (a3),d2
    move.w 4(a3),d3
    move.b 6(a3),d4
    bclr #0,d5
    btst #3,d7
    bne.w hint_56c4
hint_55d6:
; --- unverified ---
    moveq #40,d5
    or.b 8(a3),d5
    tst.w d3
    bmi.w dat_991c
hint_55e2:
; --- unverified ---
    move.w d2,(a5)+
    tst.b 568(a6) ; app+$238
    bne.w hint_78b6
hint_55ec:
; --- unverified ---
    rts
hint_55ee:
; --- unverified ---
    tst.b 9(a3)
    bne.s hint_5630
hint_55f4:
; --- unverified ---
    tst.b 11(a3)
    bne.s hint_5630
hint_55fa:
; --- unverified ---
    btst #3,d7
    bne.s hint_5630
hint_5600:
; --- unverified ---
    clr.b 3(a3)
    bsr.s hint_560e
hint_5606:
; --- unverified ---
    addq.w #4,sp
    movea.l (sp)+,a0
    move.w d4,(a0)
    rts
hint_560e:
    dc.b    $8a,$2b,$00,$08
hint_5612:
; --- unverified ---
    moveq #15,d4
    and.b 10(a3),d4
    ror.w #4,d4
    tst.b 12(a3)
    beq.s hint_5624
hint_5620:
    dc.b    $08,$c4,$00,$0b
hint_5624:
; --- unverified ---
    moveq #3,d0
    and.b 13(a3),d0
    ror.w #7,d0
    or.w d0,d4
    rts
hint_5630:
; --- unverified ---
    cmpi.b #$3,7(a3)
    bne.s hint_5698
hint_5638:
; --- unverified ---
    move.l (a3),d2
    move.w 4(a3),d3
    btst #2,d7
    beq.w hint_5694
hint_5646:
; --- unverified ---
    btst #1,d7
    beq.w hint_5694
hint_564e:
; --- unverified ---
    btst #3,d7
    bne.w hint_5660
hint_5656:
; --- unverified ---
    bsr.s hint_560e
hint_5658:
; --- unverified ---
    bsr.w hint_78aa
hint_565c:
; --- unverified ---
    move.b d2,d4
    bra.s hint_5606
hint_5660:
; --- unverified ---
    bsr.s hint_5612
hint_5662:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_5692
hint_5668:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_5686
hint_566e:
; --- unverified ---
    move.l (a3),d2
    sub.l 572(a6),d2 ; app+$23C
    move.l 2158(a6),d0 ; app+$86E
    sub.l 588(a6),d0 ; app+$24C
    sub.l d0,d2
    bsr.w hint_78b0
hint_5682:
; --- unverified ---
    move.b d2,d4
    bra.s hint_5606
hint_5686:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_566e
hint_568c:
; --- unverified ---
    moveq #33,d0
    bsr.w loc_8486
hint_5692:
; --- unverified ---
    rts
hint_5694:
; --- unverified ---
    bra.w hint_56b8
hint_5698:
; --- unverified ---
    btst #0,d7
    beq.s hint_56a2
hint_569e:
; --- unverified ---
    bsr.w hint_5274
hint_56a2:
; --- unverified ---
    btst #2,d7
    beq.s hint_56ac
hint_56a8:
; --- unverified ---
    bsr.w hint_530a
hint_56ac:
; --- unverified ---
    btst #1,d7
    beq.s hint_56b6
hint_56b2:
; --- unverified ---
    bsr.w hint_525e
hint_56b6:
; --- unverified ---
    rts
hint_56b8:
; --- unverified ---
    moveq #91,d0
    bra.w loc_8482
hint_56be:
; --- unverified ---
    moveq #68,d0
    bra.w loc_8482
hint_56c4:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_5702
hint_56ca:
; --- unverified ---
    tst.w d3
    bmi.w loc_98ee
hint_56d0:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_56f6
hint_56d6:
; --- unverified ---
    move.w d4,-(sp)
    bclr #15,d4
    bsr.w hint_19ea
hint_56e0:
; --- unverified ---
    move.w (sp)+,d4
    sub.l 572(a6),d2 ; app+$23C
    move.l 2158(a6),d0 ; app+$86E
    sub.l 588(a6),d0 ; app+$24C
    sub.l d0,d2
    move.w d2,(a5)+
    bra.w sub_78bc
hint_56f6:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_56d6
hint_56fc:
; --- unverified ---
    moveq #33,d0
    bsr.w loc_8486
hint_5702:
; --- unverified ---
    move.w d2,(a5)+
    rts
hint_5706:
; --- unverified ---
    move.w d4,-(sp)
    tst.b 568(a6) ; app+$238
    beq.s hint_573a
hint_570e:
; --- unverified ---
    tst.w d3
    bmi.w hint_56be
hint_5714:
; --- unverified ---
    move.b 6(a3),d4
    bne.s hint_573a
hint_571a:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_572c
hint_5720:
; --- unverified ---
    tst.b 263(a6) ; app+$107
    bne.s hint_572c
hint_5726:
; --- unverified ---
    moveq #30,d0
    bsr.w loc_8486
hint_572c:
    dc.b    $94,$ae,$02,$3c,$20,$2e,$08,$6e,$90,$ae,$02,$4c,$94,$80
hint_573a:
; --- unverified ---
    move.l d2,(a5)+
    move.w (sp)+,d4
    rts
hint_5740:
; --- unverified ---
    movem.l d2-d4/a2-a3,-(sp)
    bsr.w loc_0dd0
hint_5748:
; --- unverified ---
    tst.w d3
    bmi.s hint_5774
hint_574c:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_577a
hint_5752:
; --- unverified ---
    cmp.b #$2,d3
    bne.s hint_5774
hint_5758:
; --- unverified ---
    tst.b d4
    bne.s hint_5774
hint_575c:
; --- unverified ---
    tst.l d2
    bmi.s hint_5774
hint_5760:
; --- unverified ---
    cmp.l #$9,d2
    bcc.s hint_5774
hint_5768:
; --- unverified ---
    move.b 23(pc,d2.w),d0
    bmi.s hint_5774
hint_576e:
; --- unverified ---
    movem.l (sp)+,d2-d4/a2-a3
    rts
hint_5774:
; --- unverified ---
    moveq #92,d0
    bsr.w loc_8486
hint_577a:
; --- unverified ---
    movem.l (sp)+,d2-d4/a2-a3
    moveq #0,d0
    rts
hint_5782:
    dc.b    $00,$01,$ff,$02
    dc.b    $ff,$ff,$ff,$03
hint_578a:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    bra.s hint_5796
hint_5792:
    dc.b    $41,$f1,$20,$00
hint_5796:
; --- unverified ---
    movea.l a0,a1
    move.w (a0)+,d2
    beq.s hint_57d4
hint_579c:
; --- unverified ---
    cmp.b (a0)+,d1
    bcs.s hint_57d4
hint_57a0:
; --- unverified ---
    bne.s hint_5792
hint_57a2:
    dc.b    $48,$e7,$40,$08
hint_57a6:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b (a0)+,d1
    beq.s hint_57a6
hint_57b2:
; --- unverified ---
    tst.b -(a0)
    beq.s hint_57bc
hint_57b6:
; --- unverified ---
    movem.l (sp)+,d1/a4
    bra.s hint_5792
hint_57bc:
; --- unverified ---
    lea sub_a764(pc),a0
    tst.b 0(a0,d1.w)
    beq.s hint_57b6
hint_57c6:
; --- unverified ---
    addq.l #8,sp
    move.w -2(a1,d2.w),d2
    move.b -1(a4),d1
    moveq #0,d0
    rts
hint_57d4:
; --- unverified ---
    move.b -1(a4),d1
    moveq #-1,d0
    rts
hint_57dc:
; --- unverified ---
    lea pcref_5868(pc),a0
    bsr.s hint_5828
hint_57e2:
; --- unverified ---
    beq.s hint_5808
hint_57e4:
; --- unverified ---
    lea str_586c(pc),a0
    bsr.s hint_5828
hint_57ea:
; --- unverified ---
    beq.s hint_5802
hint_57ec:
; --- unverified ---
    lea 137(pc),a0
    bsr.s hint_5828
hint_57f2:
; --- unverified ---
    bne.s hint_5822
hint_57f4:
    dc.b    $1d,$40,$01,$33
hint_57f8:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_5820
hint_57fe:
; --- unverified ---
    move.b (a4)+,d1
    bra.s hint_57dc
hint_5802:
    dc.b    $1d,$40
hint_5804:
    dc.b    $01,$32
hint_5808:
; --- unverified ---
    bsr.w sub_16cc
hint_580c:
; --- unverified ---
    tst.l d2
    bmi.s hint_5822
hint_5810:
; --- unverified ---
    cmp.l #$8,d2
    bcc.s hint_5822
hint_5818:
; --- unverified ---
    ror.w #7,d2
    move.w d2,304(a6) ; app+$130
    bra.s hint_57f8
hint_5820:
; --- unverified ---
    rts
hint_5822:
; --- unverified ---
    moveq #58,d0
    bra.w loc_8482
hint_5828:
    dc.b    $43,$ec,$ff,$ff
hint_582c:
; --- unverified ---
    move.b (a1)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    move.b (a0)+,d0
    beq.s hint_583e
hint_5838:
; --- unverified ---
    cmp.b d0,d1
    beq.s hint_582c
hint_583c:
; --- unverified ---
    rts
hint_583e:
; --- unverified ---
    cmp.b #$3d,d1
    bne.s hint_583c
hint_5844:
; --- unverified ---
    movea.l a1,a4
    move.b (a4)+,d1
    tst.b (a0)
    bpl.s hint_5850
hint_584c:
; --- unverified ---
    moveq #0,d0
    rts
hint_5850:
    dc.b    $70,$00,$48,$81,$12,$36,$10,$7e
hint_5858:
; --- unverified ---
    move.b (a0)+,d2
    beq.s hint_5822
hint_585c:
; --- unverified ---
    addq.b #1,d0
    cmp.b d1,d2
    bne.s hint_5858
hint_5862:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b d0,d0
    rts
pcref_5868:
    dc.b    $49,$44,$00,$ff
str_586c:
; --- unverified ---
    addq.w #1,sp
    subq.w #2,a6
    neg.b d0
    link a0,#19802
    ori.w #$5245,(a0)
    chk.l d0,d1
    addq.w #4,d4
    subq.b #1,d0
    bsr.w hint_2b02
hint_5884:
; --- unverified ---
    move.b 569(a6),d3 ; app+$239
    bne.s hint_5890
hint_588a:
    dc.b    $1d,$7c,$00,$07,$02,$39
hint_5890:
; --- unverified ---
    cmp.b #$4,d3
    bcs.w hint_2b14
hint_5898:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_58f0
hint_589e:
; --- unverified ---
    move.l a0,-(sp)
    bsr.w hint_5f9c
hint_58a4:
; --- unverified ---
    movea.l (sp)+,a0
    bne.w loc_8482
hint_58aa:
; --- unverified ---
    movem.l d2-d3,-(sp)
    bsr.w sub_0bce
hint_58b2:
; --- unverified ---
    movem.l (sp)+,d2-d3
    beq.w loc_8436
hint_58ba:
; --- unverified ---
    lea 362(a6),a2 ; app+$16A
    move.l d2,-(sp)
    move.b 569(a6),d3 ; app+$239
    addi.b #$b,d3
    bsr.w sub_0cb6
hint_58cc:
; --- unverified ---
    movea.l (sp)+,a2
    move.l (a2),8(a1)
    move.b 4(a2),14(a1)
    move.b 5(a2),15(a1)
    move.l 6(a2),16(a1)
    move.w 10(a2),20(a1)
    move.b -1(a4),d1
    rts
hint_58f0:
; --- unverified ---
    bsr.w sub_0bce
hint_58f4:
; --- unverified ---
    bne.w loc_844e
hint_58f8:
; --- unverified ---
    btst #6,12(a1)
    bne.w loc_8436
hint_5902:
; --- unverified ---
    move.b 569(a6),d3 ; app+$239
    move.l a1,-(sp)
    bsr.w hint_5f9c
hint_590c:
; --- unverified ---
    movea.l (sp)+,a1
    bne.w loc_8482
hint_5912:
; --- unverified ---
    movea.l d2,a0
    move.l 8(a1),d0
    cmp.l (a0),d0
    bne.s hint_5958
hint_591c:
; --- unverified ---
    move.b 14(a1),d0
    cmp.b 4(a0),d0
    bne.s hint_5958
hint_5926:
; --- unverified ---
    move.b 15(a1),d0
    cmp.b 5(a0),d0
    bne.s hint_5958
hint_5930:
; --- unverified ---
    move.l 16(a1),d0
    cmp.l 6(a0),d0
    bne.s hint_5958
hint_593a:
; --- unverified ---
    move.w 20(a1),d0
    cmp.w 10(a0),d0
    bne.s hint_5958
hint_5944:
; --- unverified ---
    cmp.b 13(a1),d3
    bne.w loc_8436
hint_594c:
; --- unverified ---
    bset #6,12(a1)
    move.b -1(a4),d1
    rts
hint_5958:
; --- unverified ---
    bra.w loc_843e
hint_595c:
; --- unverified ---
    or.w 304(a6),d6 ; app+$130
    bra.w hint_61c6
hint_5964:
; --- unverified ---
    move.w d6,d5
    move.w #$f048,d6
    or.w 304(a6),d6 ; app+$130
    swap d5
    move.w d6,d5
    swap d5
    bra.w hint_620e
hint_5978:
; --- unverified ---
    move.w #$f000,d6
    or.w 304(a6),d6 ; app+$130
    move.w d6,(a5)+
    bsr.w hint_5f20
hint_5986:
; --- unverified ---
    bne.s hint_59a8
hint_5988:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5990:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,d3
    bsr.w hint_5f20
hint_5998:
; --- unverified ---
    bne.w hint_5a28
hint_599c:
; --- unverified ---
    lsl.w #3,d3
    or.w d3,d2
    lsl.w #7,d2
    move.w d2,(a5)+
    bra.w hint_5d68
hint_59a8:
; --- unverified ---
    lea pcref_5ac2(pc),a0
    bsr.w hint_578a
hint_59b0:
; --- unverified ---
    beq.s hint_59e2
hint_59b2:
; --- unverified ---
    move.w #$4000,d5
    bsr.w hint_5f7c
hint_59ba:
; --- unverified ---
    move.w d5,(a5)+
    bsr.w hint_5b04
hint_59c0:
; --- unverified ---
    moveq #-3,d0
    bsr.w hint_1704
hint_59c6:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_59ce:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f20
hint_59d4:
; --- unverified ---
    bne.s hint_5a02
hint_59d6:
; --- unverified ---
    lsl.w #7,d2
    movea.l 588(a6),a0 ; app+$24C
    or.w d2,2(a0)
    rts
hint_59e2:
; --- unverified ---
    bsr.w hint_2350
hint_59e6:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_59ee:
; --- unverified ---
    move.b (a4)+,d1
    ror.w #6,d2
    ori.w #$a000,d2
    move.w d2,(a5)+
    bsr.w hint_5aa0
hint_59fc:
; --- unverified ---
    moveq #61,d0
    bra.w hint_1704
hint_5a02:
; --- unverified ---
    lea pcref_5ac2(pc),a0
    bsr.w hint_578a
hint_5a0a:
; --- unverified ---
    bne.s hint_5a22
hint_5a0c:
; --- unverified ---
    bsr.w hint_5aa4
hint_5a10:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    ror.w #6,d2
    bset #15,d2
    move.w d2,2(a0)
    bra.w hint_2350
hint_5a22:
; --- unverified ---
    moveq #87,d0
    bra.w loc_8486
hint_5a28:
; --- unverified ---
    move.w #$6000,d5
    bsr.w hint_5f7c
hint_5a30:
; --- unverified ---
    lsl.w #7,d3
    or.w d3,d5
    move.w d5,(a5)+
    bsr.w hint_5b04
hint_5a3a:
; --- unverified ---
    moveq #61,d0
    bsr.w hint_1704
hint_5a40:
; --- unverified ---
    cmpi.b #$5,569(a6) ; app+$239
    beq.s hint_5a4a
hint_5a48:
; --- unverified ---
    rts
hint_5a4a:
; --- unverified ---
    cmp.b #$7b,d1
    bne.s hint_5a48
hint_5a50:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$23,d1
    beq.s hint_5a7e
hint_5a58:
; --- unverified ---
    bsr.w sub_177e
hint_5a5c:
; --- unverified ---
    bne.s hint_5a9a
hint_5a5e:
; --- unverified ---
    tst.b d0
    bne.s hint_5a9a
hint_5a62:
    dc.b    $02,$42,$00,$07,$e9,$0a,$08,$c2,$00,$0c
hint_5a6c:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    or.w d2,2(a0)
    cmp.b #$7d,d1
    bne.s hint_5a9a
hint_5a7a:
; --- unverified ---
    move.b (a4)+,d1
    rts
hint_5a7e:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_5a84:
; --- unverified ---
    cmp.l #$ffffffc0,d2
    blt.s hint_5a9a
hint_5a8c:
; --- unverified ---
    cmp.l #$3f,d2
    bgt.s hint_5a9a
hint_5a94:
; --- unverified ---
    andi.w #$7f,d2
    bra.s hint_5a6c
hint_5a9a:
; --- unverified ---
    moveq #97,d0
    bra.w loc_8486
hint_5aa0:
; --- unverified ---
    bsr.w hint_5b04
hint_5aa4:
; --- unverified ---
    moveq #56,d0
    and.w d5,d0
    subq.w #8,d0
    beq.s hint_5aae
hint_5aac:
; --- unverified ---
    rts
hint_5aae:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    btst #2,2(a0)
    beq.s hint_5abc
hint_5aba:
; --- unverified ---
    rts
hint_5abc:
; --- unverified ---
    moveq #95,d0
    bra.w loc_8486
pcref_5ac2:
    dc.b    $00,$0c
    dc.b    "CONTROL",0
    dc.b    $00,$04,$00,$0a,$46,$50
    dc.b    $43,$52,$00,$00,$00,$04,$00,$0a
    dc.b    "FPIAR",0
    dc.b    $00,$01,$00,$0a
    dc.b    "FPSR",0
    dc.b    $00,$00,$02,$00,$0a
    dc.b    "IADDR",0
    dc.b    $00,$01,$00,$0c,$53,$54,$41,$54
hint_5afc:
    dc.b    $55,$53,$00,$00,$00,$02,$00,$00
hint_5b04:
    dc.b    $b2,$3c
hint_5b0a:
; --- unverified ---
    move.b 569(a6),d3 ; app+$239
    cmp.b #$4,d3
    bcs.s hint_5b3a
hint_5b14:
    dc.b    $12,$1c
hint_5b16:
; --- unverified ---
    move.b 569(a6),d3 ; app+$239
    bsr.w hint_5f9c
hint_5b1e:
; --- unverified ---
    bne.w loc_8482
hint_5b22:
; --- unverified ---
    addi.b #$f5,d3
    move.b d3,d0
    move.b 569(a6),d3 ; app+$239
    movea.l d2,a0
    bsr.w hint_b168
hint_5b32:
; --- unverified ---
    bne.s hint_5b54
hint_5b34:
; --- unverified ---
    moveq #60,d5
    bra.w hint_6188
hint_5b3a:
; --- unverified ---
    bsr.w hint_187e
hint_5b3e:
; --- unverified ---
    cmp.w #$10,d5
    bcc.s hint_5b54
hint_5b44:
; --- unverified ---
    moveq #78,d0
    move.b 569(a6),d2 ; app+$239
    btst d2,d0
    bne.s hint_5b54
hint_5b4e:
; --- unverified ---
    moveq #94,d0
    bsr.w loc_8486
hint_5b54:
; --- unverified ---
    rts
hint_5b56:
; --- unverified ---
    move.w #$f000,d6
    or.w 304(a6),d6 ; app+$130
    move.w d6,(a5)+
    move.b 569(a6),d0 ; app+$239
    cmp.b #$3,d0
    beq.w hint_5c84
hint_5b6c:
; --- unverified ---
    bsr.w hint_5d68
hint_5b70:
; --- unverified ---
    move.w #$e000,d5
    bsr.w hint_5c44
hint_5b78:
; --- unverified ---
    bne.s hint_5ba4
hint_5b7a:
; --- unverified ---
    move.w d5,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5b84:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5b04
hint_5b8a:
; --- unverified ---
    moveq #52,d0
    bsr.w hint_1704
hint_5b90:
; --- unverified ---
    bsr.w hint_5c22
hint_5b94:
; --- unverified ---
    beq.s hint_5ba2
hint_5b96:
; --- unverified ---
    move.w 2(a0),d5
    bsr.w hint_5c30
hint_5b9e:
    dc.b    $31,$45,$00,$02
hint_5ba2:
; --- unverified ---
    rts
hint_5ba4:
; --- unverified ---
    bsr.w hint_5f68
hint_5ba8:
; --- unverified ---
    bne.s hint_5bd4
hint_5baa:
; --- unverified ---
    bset #11,d5
    lsl.b #4,d2
    or.b d2,d5
    move.w d5,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5bbc:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5b04
hint_5bc2:
; --- unverified ---
    moveq #52,d0
    bsr.w hint_1704
hint_5bc8:
; --- unverified ---
    bsr.s hint_5c22
hint_5bca:
; --- unverified ---
    beq.s hint_5bd2
hint_5bcc:
    dc.b    $08,$e8,$00,$04,$00,$02
hint_5bd2:
; --- unverified ---
    rts
hint_5bd4:
; --- unverified ---
    move.w #$d000,(a5)+
    bsr.w hint_5b04
hint_5bdc:
; --- unverified ---
    moveq #125,d0
    bsr.w hint_1704
hint_5be2:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5bea:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f68
hint_5bf0:
; --- unverified ---
    bne.s hint_5c06
hint_5bf2:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    andi.w #$f,d2
    lsl.w #4,d2
    bset #11,d2
    or.w d2,2(a0)
    rts
hint_5c06:
; --- unverified ---
    move.w #$d000,d5
    bsr.w hint_5c44
hint_5c0e:
; --- unverified ---
    bne.s hint_5c1c
hint_5c10:
; --- unverified ---
    bsr.s hint_5c30
hint_5c12:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w d5,2(a0)
    rts
hint_5c1c:
; --- unverified ---
    moveq #57,d0
    bra.w loc_8486
hint_5c22:
; --- unverified ---
    moveq #56,d0
    and.w d5,d0
    movea.l 588(a6),a0 ; app+$24C
    cmp.w #$20,d0
    rts
hint_5c30:
    dc.b    $10,$05,$e0,$4d,$74,$07
hint_5c36:
; --- unverified ---
    roxr.b #1,d0
    roxl.w #1,d5
    dbf d2,hint_5c36
hint_5c3e:
; --- unverified ---
    bset #12,d5
    rts
hint_5c44:
; --- unverified ---
    bsr.w hint_5f20
hint_5c48:
; --- unverified ---
    beq.s hint_5c4c
hint_5c4a:
; --- unverified ---
    rts
hint_5c4c:
    dc.b    $36,$02,$05,$c5
hint_5c50:
; --- unverified ---
    cmp.b #$2f,d1
    bne.s hint_5c5e
hint_5c56:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5c5c:
; --- unverified ---
    bra.s hint_5c4c
hint_5c5e:
; --- unverified ---
    cmp.b #$2d,d1
    bne.s hint_5c80
hint_5c64:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5c6a:
; --- unverified ---
    cmp.w d3,d2
    blt.s hint_5c7a
hint_5c6e:
; --- unverified ---
    bset d3,d5
    addq.w #1,d3
    cmp.w d2,d3
    ble.s hint_5c6e
hint_5c76:
; --- unverified ---
    move.w d2,d3
    bra.s hint_5c50
hint_5c7a:
; --- unverified ---
    moveq #57,d0
    bra.w loc_8482
hint_5c80:
; --- unverified ---
    moveq #0,d0
    rts
hint_5c84:
; --- unverified ---
    move.w #$a000,d5
    lea pcref_5ac2(pc),a0
    bsr.w hint_578a
hint_5c90:
; --- unverified ---
    bne.s hint_5cc4
hint_5c92:
; --- unverified ---
    ror.w #6,d2
    or.w d2,d5
    cmp.b #$2f,d1
    bne.s hint_5cae
hint_5c9c:
; --- unverified ---
    move.b (a4)+,d1
    lea pcref_5ac2(pc),a0
    bsr.w hint_578a
hint_5ca6:
; --- unverified ---
    beq.s hint_5c92
hint_5ca8:
; --- unverified ---
    moveq #57,d0
    bra.w loc_8486
hint_5cae:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5cb6:
; --- unverified ---
    move.b (a4)+,d1
    move.w d5,(a5)+
    bsr.w hint_5b04
hint_5cbe:
; --- unverified ---
    moveq #-1,d0
    bra.w hint_1704
hint_5cc4:
; --- unverified ---
    move.w d5,(a5)+
    bsr.w hint_5b04
hint_5cca:
; --- unverified ---
    moveq #-1,d0
    bsr.w hint_1704
hint_5cd0:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5cd8:
; --- unverified ---
    move.b (a4)+,d1
    move.w #$8000,d5
    lea pcref_5ac2(pc),a0
    bsr.w hint_578a
hint_5ce6:
; --- unverified ---
    bne.s hint_5ca8
hint_5ce8:
; --- unverified ---
    ror.w #6,d2
    or.w d2,d5
    cmp.b #$2f,d1
    bne.s hint_5d00
hint_5cf2:
; --- unverified ---
    move.b (a4)+,d1
    lea pcref_5ac2(pc),a0
    bsr.w hint_578a
hint_5cfc:
; --- unverified ---
    beq.s hint_5ce8
hint_5cfe:
; --- unverified ---
    bra.s hint_5ca8
hint_5d00:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w d5,2(a0)
    rts
hint_5d0a:
; --- unverified ---
    or.w 304(a6),d6 ; app+$130
    move.b 569(a6),d0 ; app+$239
    beq.s hint_5d18
hint_5d14:
; --- unverified ---
    bsr.w hint_5d68
hint_5d18:
; --- unverified ---
    move.w d6,(a5)+
    cmp.b #$23,d1
    bne.w hint_846a
hint_5d22:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_5d28:
; --- unverified ---
    tst.l d2
    bmi.s hint_5d34
hint_5d2c:
; --- unverified ---
    cmp.l #$40,d2
    bcs.s hint_5d3a
hint_5d34:
; --- unverified ---
    moveq #29,d0
    bsr.w loc_8486
hint_5d3a:
; --- unverified ---
    andi.w #$3f,d2
    ori.w #$5c00,d2
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5d4a:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,d3
    bsr.w hint_5f14
hint_5d52:
; --- unverified ---
    lsl.w #7,d2
    or.w d2,d3
    move.w d3,(a5)+
    rts
hint_5d5a:
; --- unverified ---
    or.w 304(a6),d6 ; app+$130
    swap d6
    clr.w d6
    move.l d6,(a5)+
    moveq #10,d1
    rts
hint_5d68:
; --- unverified ---
    cmpi.b #$7,569(a6) ; app+$239
    beq.s hint_5d7e
hint_5d70:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_5d78:
    dc.b    $1d,$7c,$00,$07,$02,$39
hint_5d7e:
; --- unverified ---
    rts
hint_5d80:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.w hint_5d94
hint_5d8a:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w sub_3132
hint_5d94:
; --- unverified ---
    move.w d6,d5
    move.w #$f000,d6
    or.w 304(a6),d6 ; app+$130
    swap d5
    move.w d6,d5
    swap d5
    bsr.w hint_5f20
hint_5da8:
; --- unverified ---
    bne.s hint_5dc8
hint_5daa:
; --- unverified ---
    ror.w #6,d2
    or.w d2,d5
    rol.w #6,d2
    bsr.s hint_5d68
hint_5db2:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_5dbe
hint_5db8:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5dbe:
; --- unverified ---
    move.w d6,(a5)+
    rol.w #7,d2
    or.w d2,d5
    move.w d5,(a5)+
    rts
hint_5dc8:
; --- unverified ---
    bset #14,d5
    bsr.w hint_5f7c
hint_5dd0:
; --- unverified ---
    move.l d5,(a5)+
    bsr.w hint_5b04
hint_5dd6:
; --- unverified ---
    moveq #-3,d0
    bsr.w hint_1704
hint_5ddc:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5de4:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5dea:
; --- unverified ---
    lsl.w #7,d2
    movea.l 588(a6),a0 ; app+$24C
    or.w d2,2(a0)
    rts
hint_5df6:
; --- unverified ---
    or.w 304(a6),d6 ; app+$130
    tst.b 293(a6) ; app+$125
    beq.s hint_5e06
hint_5e00:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_5e06:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_5e0e:
; --- unverified ---
    bsr.w hint_16e6
hint_5e12:
; --- unverified ---
    ori.w #$4e75,-29586(a4)
    btst d0,46(a0,d4.l)
    btst d0,-(a5)
    beq.s hint_5e26
hint_5e20:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_5e26:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_5e2e:
; --- unverified ---
    bsr.w hint_16e6
hint_5e32:
; --- unverified ---
    ori.b #$75,6(a4,d3.l)
    move.w #$f040,d6
    or.w 304(a6),d6 ; app+$130
    swap d5
    move.w d6,d5
    swap d5
    bra.w hint_669c
hint_5e4a:
; --- unverified ---
    or.w 304(a6),d6 ; app+$130
    move.w d6,(a5)+
    moveq #48,d5
    bsr.w hint_5f20
hint_5e56:
; --- unverified ---
    bne.s hint_5e86
hint_5e58:
; --- unverified ---
    ror.w #6,d2
    or.w d2,d5
    bsr.w hint_5d68
hint_5e60:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5e68:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5e6e:
; --- unverified ---
    or.w d2,d5
    cmp.b #$3a,d1
    bne.w hint_245c
hint_5e78:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5e7e:
; --- unverified ---
    lsl.w #7,d2
    or.w d2,d5
    move.w d5,(a5)+
    rts
hint_5e86:
; --- unverified ---
    bset #14,d5
    bsr.w hint_5f7c
hint_5e8e:
; --- unverified ---
    move.w d5,(a5)+
    bsr.w hint_5b04
hint_5e94:
; --- unverified ---
    moveq #-3,d0
    bsr.w hint_1704
hint_5e9a:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_5ea2:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5ea8:
; --- unverified ---
    move.w d2,d5
    cmp.b #$3a,d1
    bne.w hint_245c
hint_5eb2:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5f14
hint_5eb8:
; --- unverified ---
    lsl.w #7,d2
    or.w d2,d5
    movea.l 588(a6),a0 ; app+$24C
    or.w d5,2(a0)
    rts
hint_5ec6:
; --- unverified ---
    move.w d6,d5
    move.w #$f078,d6
    or.w 304(a6),d6 ; app+$130
    swap d5
    move.w d6,d5
    swap d5
    move.l d5,(a5)+
    bra.w hint_4d34
hint_5edc:
; --- unverified ---
    move.w d6,d5
    move.w #$f000,d6
    or.w 304(a6),d6 ; app+$130
    swap d5
    move.w d6,d5
    swap d5
    bsr.w hint_5f20
hint_5ef0:
; --- unverified ---
    bne.s hint_5f00
hint_5ef2:
; --- unverified ---
    ror.w #6,d2
    or.w d2,d5
    bsr.w hint_5d68
hint_5efa:
; --- unverified ---
    move.w d6,(a5)+
    move.w d5,(a5)+
    rts
hint_5f00:
; --- unverified ---
    bset #14,d5
    bsr.w hint_5f7c
hint_5f08:
; --- unverified ---
    move.l d5,(a5)+
    bsr.w hint_5b04
hint_5f0e:
; --- unverified ---
    moveq #-3,d0
    bra.w hint_1704
hint_5f14:
; --- unverified ---
    bsr.s hint_5f20
hint_5f16:
; --- unverified ---
    bne.s hint_5f1a
hint_5f18:
; --- unverified ---
    rts
hint_5f1a:
; --- unverified ---
    moveq #87,d0
    bra.w loc_8482
hint_5f20:
; --- unverified ---
    move.b d1,d0
    movea.l a4,a0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b #$46,d0
    bne.s hint_5f64
hint_5f30:
; --- unverified ---
    move.b (a0)+,d0
    ext.w d0
    move.b 126(a6,d0.w),d0
    cmp.b #$50,d0
    bne.s hint_5f64
hint_5f3e:
; --- unverified ---
    move.b (a0)+,d2
    subi.b #$30,d2
    bcs.s hint_5f64
hint_5f46:
; --- unverified ---
    cmp.b #$8,d2
    bcc.s hint_5f64
hint_5f4c:
; --- unverified ---
    ext.w d2
    moveq #0,d0
    move.b (a0)+,d0
    lea sub_a764(pc),a1
    tst.b 0(a1,d0.w)
    beq.s hint_5f64
hint_5f5c:
; --- unverified ---
    move.b d0,d1
    movea.l a0,a4
    cmp.b d0,d0
    rts
hint_5f64:
; --- unverified ---
    moveq #-1,d0
    rts
hint_5f68:
; --- unverified ---
    bsr.w sub_177e
hint_5f6c:
; --- unverified ---
    bne.s hint_5f7a
hint_5f6e:
; --- unverified ---
    tst.b d0
    beq.s hint_5f7a
hint_5f72:
    dc.b    $28,$48,$12,$2c,$ff,$ff,$70,$ff
hint_5f7a:
; --- unverified ---
    rts
hint_5f7c:
; --- unverified ---
    moveq #0,d0
    move.b 569(a6),d0 ; app+$239
    beq.w loc_844a
hint_5f86:
; --- unverified ---
    add.w d0,d0
    or.w pcref_5f8c(pc,d0.w),d5
pcref_5f8c:
    rts
hint_5f8e:
    dc.b    $18,$00,$10,$00,$00,$00,$14,$00,$0c,$00
hint_5f98:
    dc.b    $04,$00,$08,$00
hint_5f9c:
    dc.b    $41,$ee
hint_5fb2:
; --- unverified ---
    cmp.b #$3a,d1
    beq.w hint_60fc
hint_5fba:
; --- unverified ---
    cmp.b #$2d,d1
    beq.w hint_5fe2
hint_5fc2:
; --- unverified ---
    cmp.b #$30,d1
    bcs.s hint_5fce
hint_5fc8:
; --- unverified ---
    cmp.b #$3a,d1
    bcs.s hint_5ffe
hint_5fce:
; --- unverified ---
    bsr.w sub_1208
hint_5fd2:
; --- unverified ---
    cmp.b #$f,d3
    bcs.s hint_5ffa
hint_5fd8:
; --- unverified ---
    cmp.b #$13,d3
    bcc.s hint_5ffa
hint_5fde:
; --- unverified ---
    moveq #0,d0
    rts
hint_5fe2:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_5f9c
hint_5fe6:
; --- unverified ---
    bne.s hint_5ff8
hint_5fe8:
; --- unverified ---
    movea.l d2,a0
    addi.b #$f5,d3
    bsr.w sub_b1fa
hint_5ff2:
    dc.b    $04,$03,$00,$f5,$4a,$00
hint_5ff8:
; --- unverified ---
    rts
hint_5ffa:
; --- unverified ---
    moveq #100,d0
    rts
hint_5ffe:
    dc.b    $3f,$03,$56,$88,$50,$c2,$76,$01,$78,$ff,$7a,$00,$7c,$00
hint_600c:
; --- unverified ---
    subi.b #$30,d1
    bne.s hint_6020
hint_6012:
; --- unverified ---
    tst.b d5
    bne.s hint_6020
hint_6016:
; --- unverified ---
    cmp.b #$1,d3
    beq.s hint_6030
hint_601c:
; --- unverified ---
    subq.w #1,d4
    bra.s hint_6030
hint_6020:
; --- unverified ---
    bsr.w hint_60e2
hint_6024:
; --- unverified ---
    st d5
    cmp.b #$ff,d3
    bne.s hint_602e
hint_602c:
    dc.b    $76,$00
hint_602e:
    dc.b    $d8,$43
hint_6030:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$2e,d1
    bne.s hint_6042
hint_6038:
; --- unverified ---
    cmp.b #$1,d3
    bne.s hint_608c
hint_603e:
; --- unverified ---
    move.b d5,d3
    bra.s hint_6030
hint_6042:
; --- unverified ---
    cmp.b #$30,d1
    bcs.s hint_604e
hint_6048:
; --- unverified ---
    cmp.b #$3a,d1
    bcs.s hint_600c
hint_604e:
; --- unverified ---
    cmp.b #$45,d1
    beq.s hint_605a
hint_6054:
; --- unverified ---
    cmp.b #$65,d1
    bne.s hint_608c
hint_605a:
; --- unverified ---
    moveq #0,d3
    move.b (a4)+,d1
    cmp.b #$2d,d1
    seq d2
    bne.s hint_6068
hint_6066:
    dc.b    $12,$1c
hint_6068:
; --- unverified ---
    cmp.b #$30,d1
    bcs.s hint_6084
hint_606e:
; --- unverified ---
    cmp.b #$3a,d1
    bcc.s hint_6084
hint_6074:
; --- unverified ---
    subi.b #$30,d1
    andi.w #$ff,d1
    mulu.w #$a,d3
    add.w d1,d3
    bra.s hint_6066
hint_6084:
; --- unverified ---
    tst.b d2
    beq.s hint_608a
hint_6088:
    dc.b    $44,$43
hint_608a:
    dc.b    $d8,$43
hint_608c:
; --- unverified ---
    lea 2162(a6),a0 ; app+$872
    moveq #0,d6
    tst.b d5
    beq.s hint_60cc
hint_6096:
; --- unverified ---
    tst.w d4
    bpl.s hint_60a0
hint_609a:
    dc.b    $08,$d0,$00,$06,$44,$44
hint_60a0:
; --- unverified ---
    st d2
    andi.l #$ffff,d4
    divu.w #$3e8,d4
    move.w d4,d5
    clr.w d4
    swap d4
    divu.w #$64,d4
    bsr.s hint_60e0
hint_60b8:
; --- unverified ---
    clr.w d4
    swap d4
    divu.w #$a,d4
    bsr.s hint_60e0
hint_60c2:
; --- unverified ---
    clr.w d4
    swap d4
    bsr.s hint_60e0
hint_60c8:
    dc.b    $12,$2c,$ff,$ff
hint_60cc:
; --- unverified ---
    lea 2162(a6),a0 ; app+$872
    move.w (sp)+,d3
    bsr.w hint_b12c
hint_60d6:
; --- unverified ---
    addi.w #$b,d3
    move.l a0,d2
    tst.w d0
    rts
hint_60e0:
    dc.b    $12,$04
hint_60e2:
; --- unverified ---
    tst.b d2
    beq.s hint_60ee
hint_60e6:
; --- unverified ---
    or.b d1,(a0)+
    addq.b #1,d6
    not.b d2
    rts
hint_60ee:
; --- unverified ---
    cmp.b #$9,d6
    beq.s hint_60fa
hint_60f4:
    dc.b    $e9,$49,$83,$10,$46,$02
hint_60fa:
; --- unverified ---
    rts
hint_60fc:
    dc.b    $24,$4c,$43,$fa,$b3,$42
hint_6102:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    bmi.s hint_6114
hint_6108:
; --- unverified ---
    move.b 0(a1,d1.w),d2
    bmi.s hint_6114
hint_610e:
; --- unverified ---
    moveq #4,d0
    bsr.s hint_613a
hint_6112:
; --- unverified ---
    bra.s hint_6102
hint_6114:
; --- unverified ---
    moveq #0,d0
    move.b 25(pc,d3.w),d0
    beq.s hint_6130
hint_611c:
    dc.b    $74,$00
hint_611e:
; --- unverified ---
    move.w d0,-(sp)
    cmp.w #$20,d0
    blt.s hint_6128
hint_6126:
    dc.b    $70,$10
hint_6128:
; --- unverified ---
    sub.w d0,(sp)
    bsr.s hint_613a
hint_612c:
; --- unverified ---
    move.w (sp)+,d0
    bne.s hint_611e
hint_6130:
; --- unverified ---
    bra.s hint_60d6
hint_6132:
    dc.b    "XP@ ",0
    dc.b    $40,$00,$00
hint_613a:
; --- unverified ---
    move.l a1,-(sp)
    tst.w d0
    beq.s hint_615a
hint_6140:
    dc.b    $48,$40,$42,$40,$d1,$00,$48,$40
hint_6148:
; --- unverified ---
    lea 2174(a6),a0 ; app+$87E
    movea.l a0,a1
    addx.l -(a0),-(a1)
    addx.l -(a0),-(a1)
    addx.l -(a0),-(a1)
    bcs.s hint_617e
hint_6156:
; --- unverified ---
    subq.w #1,d0
    bne.s hint_6148
hint_615a:
; --- unverified ---
    addx.b d0,d0
    ext.w d2
    ext.l d2
    lea 2174(a6),a0 ; app+$87E
    move.l -(a0),d0
    addx.l d2,d0
    move.l d0,(a0)
    moveq #0,d2
    move.l -(a0),d0
    addx.l d2,d0
    move.l d0,(a0)
    move.l -(a0),d0
    addx.l d2,d0
    bcs.s hint_617e
hint_6178:
; --- unverified ---
    move.l d0,(a0)
    movea.l (sp)+,a1
    rts
hint_617e:
; --- unverified ---
    moveq #93,d0
    bsr.w loc_8486
hint_6184:
; --- unverified ---
    movea.l (sp)+,a1
    rts
hint_6188:
; --- unverified ---
    movea.l d2,a0
    ext.w d3
    move.b 19(pc,d3.w),d0
    bmi.s hint_619a
hint_6192:
; --- unverified ---
    move.w (a0)+,(a5)+
    subq.b #1,d0
    bne.s hint_6192
hint_6198:
; --- unverified ---
    rts
hint_619a:
; --- unverified ---
    moveq #0,d0
    move.b (a0)+,d0
    move.w d0,(a5)+
    rts
    dc.b    $ff,$01
hint_61a4:
; --- unverified ---
    andi.b #$2,d4
    addi.b #$2e,d0
    btst d0,-(a3)
    bne.s hint_61ba
hint_61b0:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_61ba:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_61c6
hint_61c0:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_61c6:
; --- unverified ---
    move.b 569(a6),d0 ; app+$239
    beq.s hint_61e2
hint_61cc:
; --- unverified ---
    cmp.b #$2,d0
    beq.s hint_61e2
hint_61d2:
; --- unverified ---
    cmp.b #$3,d0
    bne.w loc_844a
hint_61da:
; --- unverified ---
    bset #6,d6
    bra.w hint_2030
hint_61e2:
; --- unverified ---
    bra.w hint_20b0
hint_61e6:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_61f6
hint_61ec:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_61f6:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6202
hint_61fc:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6202:
    dc.b    $3a,$06,$3c,$3c,$f0,$48,$48,$45,$3a,$06,$48,$45
hint_620e:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_6216:
; --- unverified ---
    bsr.w loc_1760
hint_621a:
; --- unverified ---
    swap d5
    or.b d2,d5
    swap d5
    move.l d5,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_622a:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_2130
hint_6230:
; --- unverified ---
    bne.s hint_6236
hint_6232:
; --- unverified ---
    addq.l #2,a5
    rts
hint_6236:
; --- unverified ---
    subq.l #2,d2
    tst.w d3
    bmi.w loc_98ee
hint_623e:
; --- unverified ---
    bsr.w sub_78bc
hint_6242:
; --- unverified ---
    move.w d2,(a5)+
    rts
hint_6246:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.s hint_6258
hint_624e:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w hint_626a
hint_6258:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6264
hint_625e:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6264:
; --- unverified ---
    move.w #$f518,(a5)+
    rts
hint_626a:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_627a
hint_6270:
; --- unverified ---
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_627a:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6286
hint_6280:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6286:
; --- unverified ---
    move.w d6,(a5)+
    move.w #$2400,(a5)+
    rts
hint_628e:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.s hint_62a0
hint_6296:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w sub_3132
hint_62a0:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_62ac
hint_62a6:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_62ac:
    dc.b    $3a,$c6
hint_62ae:
; --- unverified ---
    bsr.w hint_187e
hint_62b2:
; --- unverified ---
    move.b d5,d0
    andi.b #$38,d0
    cmp.b #$10,d0
    bne.s hint_62cc
hint_62be:
; --- unverified ---
    andi.b #$7,d5
    movea.l 588(a6),a0 ; app+$24C
    or.w (a0),d5
    move.w d5,(a0)
    rts
hint_62cc:
; --- unverified ---
    moveq #104,d0
    bra.w loc_8486
hint_62d2:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.s hint_62e4
hint_62da:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w sub_3132
hint_62e4:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_62f0
hint_62ea:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_62f0:
; --- unverified ---
    move.w d6,(a5)+
    rts
hint_62f4:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.s hint_6306
hint_62fc:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w hint_6318
hint_6306:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6312
hint_630c:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6312:
; --- unverified ---
    move.w #$f508,d6
    bra.s hint_62ac
hint_6318:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_6328
hint_631e:
; --- unverified ---
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_6328:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6334
hint_632e:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6334:
    dc.b    $34,$3c,$30,$00
hint_6338:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w hint_6398
hint_633e:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_6346:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$23,d1
    bne.w hint_846a
hint_6350:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,-(sp)
    bsr.w sub_16cc
hint_6358:
    dc.b    $36,$1f,$4a,$2e,$01,$23,$56,$c0,$02,$80,$00,$00,$00,$08,$00,$00
    dc.b    $00,$07,$4a,$82,$6b,$04
hint_636e:
; --- unverified ---
    cmp.l d0,d2
    ble.s hint_637a
hint_6372:
; --- unverified ---
    moveq #89,d0
    bsr.w loc_8486
hint_6378:
    dc.b    $74,$00
hint_637a:
; --- unverified ---
    lsl.w #5,d2
    or.w d3,d2
    cmp.b #$2c,d1
    beq.s hint_6388
hint_6384:
; --- unverified ---
    move.w d2,(a5)+
    rts
hint_6388:
; --- unverified ---
    move.b (a4)+,d1
    bset #11,d2
    move.w d2,(a5)+
    bsr.w hint_16e0
hint_6394:
    dc.b    $00,$24,$4e,$75
hint_6398:
; --- unverified ---
    cmp.b #$23,d1
    beq.s hint_640c
hint_639e:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$53,d1
    beq.s hint_63ea
hint_63aa:
; --- unverified ---
    cmp.b #$44,d1
    bne.s hint_6406
hint_63b0:
; --- unverified ---
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s hint_6406
hint_63b8:
; --- unverified ---
    cmp.b #$8,d1
    bcs.s hint_63e0
hint_63be:
; --- unverified ---
    cmp.b #$16,d1
    beq.s hint_63ca
hint_63c4:
; --- unverified ---
    cmp.b #$36,d1
    bne.s hint_6406
hint_63ca:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$43,d1
    beq.s hint_63d8
hint_63d2:
; --- unverified ---
    cmp.b #$63,d1
    bne.s hint_6406
hint_63d8:
    dc.b    $00,$42,$00,$01
hint_63dc:
; --- unverified ---
    move.b (a4)+,d1
    rts
hint_63e0:
; --- unverified ---
    bset #3,d1
    or.b d1,d2
    move.b (a4)+,d1
    rts
hint_63ea:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$46,d1
    beq.s hint_63f8
hint_63f2:
; --- unverified ---
    cmp.b #$66,d1
    bne.s hint_6406
hint_63f8:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$43,d1
    beq.s hint_63dc
hint_6400:
; --- unverified ---
    cmp.b #$63,d1
    beq.s hint_63dc
hint_6406:
; --- unverified ---
    moveq #89,d0
    bra.w loc_8482
hint_640c:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,-(sp)
    bsr.w sub_16cc
hint_6414:
    dc.b    $4a,$2e,$01,$23,$56,$c0,$02,$80,$00,$00,$00,$08,$00,$00,$00,$07
    dc.b    $4a,$82,$6b,$04
hint_6428:
; --- unverified ---
    cmp.l d0,d2
    ble.s hint_6434
hint_642c:
; --- unverified ---
    moveq #89,d0
    bsr.w loc_8486
hint_6432:
    dc.b    $74,$00
hint_6434:
; --- unverified ---
    or.w (sp)+,d2
    bset #4,d2
    rts
hint_643c:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_644c
hint_6442:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_644c:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6458
hint_6452:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6458:
; --- unverified ---
    move.w #$3400,d2
    bra.w hint_6338
hint_6460:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_6470
hint_6466:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_6470:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_647c
hint_6476:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_647c:
; --- unverified ---
    move.w d6,(a5)+
    move.w #$a000,(a5)+
    bsr.w hint_16e0
hint_6486:
    dc.b    $00,$fc,$4e,$75,$4a,$2e,$01,$23,$66,$0a
hint_6490:
; --- unverified ---
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_649a:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_64a6
hint_64a0:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_64a6:
; --- unverified ---
    move.w #$f000,(a5)+
    move.w d6,d2
    bsr.w hint_6398
hint_64b0:
; --- unverified ---
    move.w d2,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_64ba:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
hint_64c0:
; --- unverified ---
    ori.b #$75,-(a4)
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_64ce:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_64da
hint_64d4:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_64da:
; --- unverified ---
    move.w #$f000,(a5)+
    move.w #$100,d2
    bra.s hint_652c
hint_64e4:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_64f4
hint_64ea:
; --- unverified ---
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_64f4:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6500
hint_64fa:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6500:
; --- unverified ---
    move.w #$f000,(a5)+
    bsr.s hint_655e
hint_6506:
; --- unverified ---
    bne.s hint_652a
hint_6508:
; --- unverified ---
    bset #9,d2
    move.w d2,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_6516:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_5b04
hint_651c:
; --- unverified ---
    moveq #63,d0
    tst.b 291(a6) ; app+$123
    bne.s hint_6526
hint_6524:
    dc.b    $70,$24
hint_6526:
; --- unverified ---
    bra.w hint_1704
hint_652a:
    dc.b    $74,$00
hint_652c:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    beq.w loc_844a
hint_6534:
; --- unverified ---
    move.w d2,(a5)+
    bsr.w hint_5b04
hint_653a:
; --- unverified ---
    moveq #36,d0
    bsr.w hint_1704
hint_6540:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_6548:
; --- unverified ---
    move.b (a4)+,d1
    bsr.s hint_655e
hint_654c:
; --- unverified ---
    bne.s hint_6558
hint_654e:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    or.w d2,2(a0)
    rts
hint_6558:
; --- unverified ---
    moveq #88,d0
    bra.w loc_8486
hint_655e:
; --- unverified ---
    lea pcref_65ae(pc),a0
    bsr.w hint_578a
hint_6566:
; --- unverified ---
    bne.s hint_65ac
hint_6568:
; --- unverified ---
    move.b d2,d0
    bpl.s hint_658a
hint_656c:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_657c
hint_6572:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_657c:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6588
hint_6582:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6588:
; --- unverified ---
    bra.s hint_659a
hint_658a:
; --- unverified ---
    btst #6,d0
    beq.s hint_659a
hint_6590:
; --- unverified ---
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_659a:
; --- unverified ---
    clr.b d2
    add.w d2,d2
    add.w d2,d2
    andi.b #$3f,d0
    cmp.b 569(a6),d0 ; app+$239
    bne.w loc_844a
hint_65ac:
; --- unverified ---
    rts
pcref_65ae:
    dc.b    $00,$08,$41,$43,$00,$00,$17,$82,$00,$08,$42,$41,$43,$00,$1d,$82
    dc.b    $00,$08,$42,$41,$44,$00,$1c,$82,$00,$08,$43,$41
    dc.b    $4c,$00,$14,$81,$00,$08,$43,$52,$50,$00,$13,$04,$00,$08,$44,$52
    dc.b    $50,$00,$11,$84,$00,$0a
    dc.b    "MMUSR",0
    dc.b    $18,$02,$00,$0a
    dc.b    "PCSR",0
    dc.b    $00,$19,$82,$00,$08,$50,$53,$52,$00,$18,$02,$00,$08,$53,$43,$43
    dc.b    $00,$16,$81,$00,$08,$53,$52,$50,$00,$12,$04,$00,$08,$54,$43,$00
    dc.b    $00,$10,$03,$00,$08,$54,$54,$30,$00,$02,$43,$00,$08,$54,$54,$31
    dc.b    $00,$03,$43,$00,$08,$56,$41,$4c,$00,$2b,$81,$00,$00,$4a,$2e,$01
    dc.b    $23,$66,$0a,$0c,$2e,$00,$14,$01,$21,$66,$00,$ca,$f8,$4a,$2e,$01
    dc.b    $25,$67,$06,$70,$65,$61,$00,$1e,$40,$61,$00,$b0,$9c,$00,$6c,$4e
    dc.b    $75,$4a,$2e,$01,$23,$66,$0a,$0c,$2e,$00,$14,$01,$21,$66,$00,$ca
    dc.b    $d4,$4a,$2e,$01,$25,$67,$06,$70,$65,$61,$00,$1e,$1c,$61,$00,$b0
    dc.b    $78,$00,$34,$4e,$75,$4a,$2e,$01,$23,$66,$0a,$0c,$2e,$00,$14,$01
    dc.b    $21,$66,$00,$ca,$b0,$4a,$2e,$01,$25,$67,$06,$70,$65,$61,$00,$1d
    dc.b    $f8,$3a,$06,$3c,$3c,$f0,$40,$48,$45,$3a,$06,$48,$45
hint_669c:
; --- unverified ---
    move.l d5,(a5)+
    bsr.w hint_2372
hint_66a2:
; --- unverified ---
    st 571(a6) ; app+$23B
    bsr.w hint_16e0
    dc.b    $00,$3d,$4e,$75
hint_66ae:
; --- unverified ---
    btst #15,d6
    beq.w hint_66e2
hint_66b6:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w hint_6700
hint_66c0:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_66cc
hint_66c6:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_66cc:
; --- unverified ---
    btst #9,d6
    bne.s hint_66da
hint_66d2:
; --- unverified ---
    move.w #$f548,d6
    bra.w hint_62ac
hint_66da:
; --- unverified ---
    move.w #$f568,d6
    bra.w hint_62ac
hint_66e2:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    bne.w sub_3132
hint_66ec:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_66f8
hint_66f2:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_66f8:
; --- unverified ---
    ori.w #$f588,d6
    bra.w hint_62ac
hint_6700:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_6710
hint_6706:
; --- unverified ---
    cmpi.b #$1e,289(a6) ; app+$121
    bne.w sub_3132
hint_6710:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_671c
hint_6716:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_671c:
; --- unverified ---
    tst.b 569(a6) ; app+$239
    bne.w loc_844a
hint_6724:
; --- unverified ---
    move.w #$f000,(a5)+
    move.w d6,d2
    bsr.w hint_6398
hint_672e:
; --- unverified ---
    move.w d2,(a5)+
    cmp.b #$2c,d1
    bne.w hint_8462
hint_6738:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
hint_673e:
; --- unverified ---
    ori.b #$3c,-(a4)
    ori.b #$0,7452(a4)
    move.b (a4)+,d1
    cmp.b #$23,d1
    bne.w hint_846a
hint_6752:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_16cc
hint_6758:
; --- unverified ---
    tst.l d2
    bmi.s hint_6764
hint_675c:
; --- unverified ---
    cmp.l #$8,d2
    bcs.s hint_676c
hint_6764:
; --- unverified ---
    moveq #29,d0
    bsr.w loc_8486
hint_676a:
    dc.b    $74,$00
hint_676c:
; --- unverified ---
    ror.w #6,d2
    cmp.b #$2c,d1
    bne.s hint_6788
hint_6774:
; --- unverified ---
    move.b (a4)+,d1
    move.w d2,d3
    bsr.w sub_176a
hint_677c:
    dc.b    $08,$c3,$00,$08,$02,$42,$00,$07,$eb,$4a,$84,$43
hint_6788:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    or.w d2,2(a0)
    rts
hint_6792:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_67a2
hint_6798:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_67a2:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_67ae
hint_67a8:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_67ae:
; --- unverified ---
    move.w #$f078,(a5)+
    move.w d6,(a5)+
    bra.w hint_4d34
hint_67b8:
; --- unverified ---
    tst.b 291(a6) ; app+$123
    bne.s hint_67c8
hint_67be:
; --- unverified ---
    cmpi.b #$14,289(a6) ; app+$121
    bne.w sub_3132
hint_67c8:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_67d4
hint_67ce:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_67d4:
; --- unverified ---
    move.w #$f000,(a5)+
    bsr.w sub_177e
hint_67dc:
; --- unverified ---
    bne.s hint_6802
hint_67de:
; --- unverified ---
    tst.b d0
    beq.s hint_67fc
hint_67e2:
    dc.b    $36,$3c,$2c,$00,$86,$02,$3a,$c3
hint_67ea:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_67f2:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w hint_16e0
hint_67f8:
    dc.b    $00,$24,$4e,$75
hint_67fc:
; --- unverified ---
    moveq #14,d0
    bra.w loc_8486
hint_6802:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$56,d1
    bne.s hint_67fc
hint_680e:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$41,d1
    bne.s hint_67fc
hint_681c:
; --- unverified ---
    move.b (a4)+,d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$4c,d1
    bne.s hint_67fc
hint_682a:
; --- unverified ---
    move.b (a4)+,d1
    move.w #$2800,(a5)+
    bra.s hint_67ea
hint_6832:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    bne.w sub_3132
hint_683c:
; --- unverified ---
    move.w d6,(a5)+
    rts
hint_6840:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.w hint_6854
hint_684a:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    bne.w sub_3132
hint_6854:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_6860
hint_685a:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_6860:
; --- unverified ---
    cmp.b #$23,d1
    bne.w hint_846a
hint_6868:
; --- unverified ---
    move.b (a4)+,d1
    move.w #$f800,(a5)+
    move.w d6,(a5)+
    bsr.w hint_1a9c
hint_6874:
; --- unverified ---
    bra.w hint_276a
hint_6878:
; --- unverified ---
    cmpi.b #$20,289(a6) ; app+$121
    bne.w sub_3132
hint_6882:
; --- unverified ---
    bsr.w hint_4f1a
hint_6886:
; --- unverified ---
    move.w #$f800,(a5)+
    move.w d6,(a5)+
    bsr.w hint_16e0
hint_6890:
    dc.b    $00,$65,$20,$6e,$02,$4c,$30,$10,$02,$00,$00,$38,$66,$18
hint_689e:
; --- unverified ---
    cmp.b #$3a,d1
    bne.w hint_245c
hint_68a6:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_68ac:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    or.b d2,3(a0)
    bra.s hint_68bc
hint_68b6:
    dc.b    $08,$e8,$00,$00,$00,$02
hint_68bc:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_68c4:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w loc_1760
hint_68ca:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    lsl.b #4,d2
    or.b d2,2(a0)
    rts
hint_68d6:
; --- unverified ---
    cmpi.b #$3c,289(a6) ; app+$121
    beq.s hint_68e8
hint_68de:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w sub_3132
hint_68e8:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_68f4
hint_68ee:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_68f4:
; --- unverified ---
    lea pcref_6912(pc),a0
    bsr.w hint_578a
hint_68fc:
; --- unverified ---
    or.w d2,d6
    move.w d6,(a5)+
    rts
hint_6902:
; --- unverified ---
    bsr.s hint_68d6
hint_6904:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_690c:
; --- unverified ---
    move.b (a4)+,d1
    bra.w hint_62ae
pcref_6912:
    dc.b    $00,$08,$42,$43,$00,$00,$00,$c0,$00,$08,$44,$43,$00,$00,$00,$40
    dc.b    $00,$08,$49,$43,$00,$00,$00,$80,$00,$08,$4e,$43
    dcb.b   6,0
    dc.b    $0c,$2e,$00,$3c,$01,$21,$67,$00,$00,$0c
hint_693e:
; --- unverified ---
    cmpi.b #$28,289(a6) ; app+$121
    bne.w sub_3132
hint_6948:
; --- unverified ---
    move.w d6,(a5)+
    bsr.w hint_187e
hint_694e:
; --- unverified ---
    cmp.b #$2c,d1
    bne.w hint_8462
hint_6956:
; --- unverified ---
    move.b (a4)+,d1
    move.b d5,d0
    andi.b #$3f,d0
    cmp.b #$39,d0
    beq.s hint_69ce
hint_6964:
; --- unverified ---
    andi.b #$30,d0
    cmp.b #$10,d0
    bne.w hint_845e
hint_6970:
; --- unverified ---
    move.w d5,-(sp)
    bsr.w hint_187e
hint_6976:
; --- unverified ---
    move.w d5,d0
    andi.b #$38,d0
    cmp.b #$18,d0
    bne.s hint_69b2
hint_6982:
; --- unverified ---
    move.b d5,d0
    andi.w #$7,d0
    ror.w #4,d0
    ori.w #$8000,d0
    move.w d0,(a5)+
    move.w (sp)+,d5
    bset #5,d5
    btst #3,d5
    beq.w hint_845e
hint_699e:
    dc.b    $02,$45,$00,$27
hint_69a2:
; --- unverified ---
    movea.l 588(a6),a0 ; app+$24C
    move.w (a0),d0
    andi.w #$ffc0,d0
    or.w d0,d5
    move.w d5,(a0)
    rts
hint_69b2:
; --- unverified ---
    move.w d5,d0
    andi.w #$3f,d0
    cmp.b #$39,d0
    bne.w hint_845e
hint_69c0:
; --- unverified ---
    move.w (sp)+,d5
    btst #3,d5
    beq.s hint_69a2
hint_69c8:
; --- unverified ---
    andi.w #$7,d5
    bra.s hint_69a2
hint_69ce:
; --- unverified ---
    bsr.w hint_187e
hint_69d2:
; --- unverified ---
    move.w d5,d0
    andi.w #$38,d0
    cmp.b #$10,d0
    bne.s hint_69e8
hint_69de:
    dc.b    $70,$18
hint_69e0:
; --- unverified ---
    andi.w #$7,d5
    or.w d0,d5
    bra.s hint_69a2
hint_69e8:
; --- unverified ---
    cmp.b #$18,d0
    bne.w hint_845e
hint_69f0:
; --- unverified ---
    moveq #8,d0
    bra.s hint_69e0
hint_69f4:
; --- unverified ---
    moveq #55,d0
    bra.w loc_8482
hint_69fa:
; --- unverified ---
    move.b d1,d2
    cmp.b #$22,d1
    beq.s hint_6a08
hint_6a02:
; --- unverified ---
    cmp.b #$27,d1
    bne.s hint_69f4
hint_6a08:
    dc.b    $24,$4c
hint_6a0a:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_69f4
hint_6a12:
; --- unverified ---
    cmp.b d2,d1
    bne.s hint_6a0a
hint_6a16:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b d2,d1
    beq.s hint_6a0a
hint_6a1c:
; --- unverified ---
    move.l a4,d4
    sub.l a2,d4
    subq.w #1,d4
    cmp.b #$2c,d1
    bne.w hint_8462
hint_6a2a:
; --- unverified ---
    move.b (a4)+,d1
    move.b d1,d3
    cmp.b #$27,d1
    beq.s hint_6a3a
hint_6a34:
; --- unverified ---
    cmp.b #$22,d1
    bne.s hint_69f4
hint_6a3a:
; --- unverified ---
    subq.w #1,d4
    bcs.s hint_6a44
hint_6a3e:
; --- unverified ---
    cmpm.b (a4)+,(a2)+
    beq.s hint_6a3a
hint_6a42:
; --- unverified ---
    rts
hint_6a44:
; --- unverified ---
    moveq #10,d0
    exg
    cmp.b d3,d0
    bne.s hint_6a52
hint_6a4c:
    dc.b    $52,$8c,$12,$1c,$70,$00
hint_6a52:
; --- unverified ---
    rts
hint_6a54:
; --- unverified ---
    bsr.s hint_69fa
hint_6a56:
; --- unverified ---
    seq d0
    bra.w hint_6b32
hint_6a5c:
; --- unverified ---
    bsr.s hint_69fa
hint_6a5e:
; --- unverified ---
    sne d0
    bra.w hint_6b32
hint_6a64:
; --- unverified ---
    bsr.w sub_14c2
hint_6a68:
; --- unverified ---
    beq.s hint_6a88
hint_6a6a:
; --- unverified ---
    bsr.w sub_0bce
hint_6a6e:
; --- unverified ---
    bne.s hint_6a88
hint_6a70:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_6a88
hint_6a76:
; --- unverified ---
    move.b 12(a1),d0
    btst #7,d0
    beq.s hint_6a88
hint_6a80:
    dc.b    $02,$00,$00,$40,$b0,$3c,$00,$40
hint_6a88:
; --- unverified ---
    rts
hint_6a8a:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    bsr.w sub_76b8
hint_6a92:
; --- unverified ---
    bne.w loc_8486
hint_6a96:
; --- unverified ---
    bsr.s hint_6a64
hint_6a98:
; --- unverified ---
    seq d0
    bra.w hint_6b32
hint_6a9e:
; --- unverified ---
    lea 1000(a6),a0 ; app+$3E8
    bsr.w sub_76b8
hint_6aa6:
; --- unverified ---
    bne.w loc_8486
hint_6aaa:
; --- unverified ---
    bsr.s hint_6a64
hint_6aac:
; --- unverified ---
    sne d0
    bra.w hint_6b32
hint_6ab2:
; --- unverified ---
    st 344(a6) ; app+$158
    bsr.w sub_0db6
hint_6aba:
; --- unverified ---
    sf 344(a6) ; app+$158
    tst.w d3
    bmi.s hint_6aee
hint_6ac2:
; --- unverified ---
    tst.b d4
    bne.s hint_6aee
hint_6ac6:
; --- unverified ---
    rts
hint_6ac8:
; --- unverified ---
    bsr.s hint_6ab2
hint_6aca:
; --- unverified ---
    cmp.b #$2,d3
    beq.s hint_6aee
hint_6ad0:
; --- unverified ---
    rts
hint_6ad2:
; --- unverified ---
    st 344(a6) ; app+$158
    bsr.w sub_0db6
hint_6ada:
; --- unverified ---
    sf 344(a6) ; app+$158
    tst.w d3
    bmi.s hint_6aee
hint_6ae2:
; --- unverified ---
    cmp.b #$1,d3
    beq.s hint_6aee
hint_6ae8:
; --- unverified ---
    tst.b d4
    bne.s hint_6aee
hint_6aec:
; --- unverified ---
    rts
hint_6aee:
; --- unverified ---
    moveq #62,d0
    bra.w loc_8482
hint_6af4:
; --- unverified ---
    bsr.s hint_6ad2
hint_6af6:
; --- unverified ---
    move.b #$3d,2107(a6) ; app+$83B
    move.l d2,2108(a6) ; app+$83C
    rts
hint_6b02:
; --- unverified ---
    moveq #51,d0
    bra.w loc_8482
loc_6b08:
    move.w #$34,d0
    bra.w loc_846e
hint_6b10:
; --- unverified ---
    bsr.s hint_6af4
hint_6b12:
; --- unverified ---
    sgt d0
    bra.s hint_6b32
hint_6b16:
; --- unverified ---
    bsr.s hint_6af4
hint_6b18:
; --- unverified ---
    sge d0
    bra.s hint_6b32
hint_6b1c:
; --- unverified ---
    bsr.s hint_6af4
hint_6b1e:
; --- unverified ---
    slt d0
    bra.s hint_6b32
hint_6b22:
; --- unverified ---
    bsr.s hint_6af4
hint_6b24:
; --- unverified ---
    sle d0
    bra.s hint_6b32
hint_6b28:
; --- unverified ---
    bsr.s hint_6af4
hint_6b2a:
; --- unverified ---
    seq d0
    bra.s hint_6b32
hint_6b2e:
; --- unverified ---
    bsr.s hint_6af4
hint_6b30:
    dc.b    $56,$c0
hint_6b32:
; --- unverified ---
    addq.w #1,2174(a6) ; app+$87E
    tst.b d0
    beq.s hint_6b42
hint_6b3a:
; --- unverified ---
    bsr.w hint_6cac
hint_6b3e:
; --- unverified ---
    moveq #10,d1
    rts
hint_6b42:
; --- unverified ---
    bsr.w hint_6cac
hint_6b46:
; --- unverified ---
    bsr.w sub_07f0
hint_6b4a:
    dc.b    $3e,$2e,$08,$7e
hint_6b4e:
; --- unverified ---
    bsr.w loc_06ac
hint_6b52:
; --- unverified ---
    bne.s loc_6b08
hint_6b54:
; --- unverified ---
    bsr.s hint_6bca
hint_6b56:
; --- unverified ---
    beq.s hint_6bc4
hint_6b58:
; --- unverified ---
    tst.l d2
    beq.s hint_6b74
hint_6b5c:
; --- unverified ---
    cmp.l #$454c5345,d1 ; 'ELSE'
    bne.s hint_6bc4
hint_6b64:
; --- unverified ---
    cmp.l #$49460000,d2
    bne.s hint_6bc4
hint_6b6c:
; --- unverified ---
    cmp.w 2174(a6),d7 ; app+$87E
    beq.s hint_6b3a
hint_6b72:
; --- unverified ---
    bra.s hint_6bc4
hint_6b74:
; --- unverified ---
    cmp.l #$454c5345,d1 ; 'ELSE'
    beq.s hint_6b6c
hint_6b7c:
; --- unverified ---
    cmp.l #$454e4443,d1 ; 'ENDC'
    beq.s hint_6b96
hint_6b84:
; --- unverified ---
    cmp.l #$454e444d,d1 ; 'ENDM'
    bne.s hint_6baa
hint_6b8c:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    beq.s hint_6bc4
hint_6b92:
; --- unverified ---
    bra.w hint_7294
hint_6b96:
; --- unverified ---
    move.w 2174(a6),d0 ; app+$87E
    subq.w #1,2174(a6) ; app+$87E
    cmp.w d0,d7
    bne.s hint_6bc4
hint_6ba2:
; --- unverified ---
    bra.s hint_6b3a
hint_6ba4:
; --- unverified ---
    bsr.w hint_6c86
hint_6ba8:
; --- unverified ---
    bra.s hint_6bc4
hint_6baa:
; --- unverified ---
    swap d1
    cmp.w #$4946,d1
    bne.s hint_6bc4
hint_6bb2:
    dc.b    $48,$41,$41,$fa,$08,$b2
hint_6bb8:
; --- unverified ---
    move.w (a0)+,d0
    beq.s hint_6bc4
hint_6bbc:
; --- unverified ---
    cmp.w d0,d1
    bne.s hint_6bb8
hint_6bc0:
    dc.b    $52,$6e,$08,$7e
hint_6bc4:
; --- unverified ---
    bsr.w sub_07f0
hint_6bc8:
; --- unverified ---
    bra.s hint_6b4e
hint_6bca:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.w hint_6c66
hint_6bd4:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_6c08
hint_6bda:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_6c08
hint_6be0:
; --- unverified ---
    cmp.b #$2a,d1
    beq.w hint_6c66
hint_6be8:
; --- unverified ---
    cmp.b #$3b,d1
    beq.s hint_6c66
hint_6bee:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_6c66
hint_6bf6:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_6c08
hint_6bfc:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_6c08
hint_6c02:
; --- unverified ---
    cmp.b #$3a,d1
    bne.s hint_6bee
hint_6c08:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_6c66
hint_6c10:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_6c08
hint_6c16:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_6c08
hint_6c1c:
; --- unverified ---
    cmp.b #$2a,d1
    beq.s hint_6c66
hint_6c22:
; --- unverified ---
    cmp.b #$3b,d1
    beq.s hint_6c66
hint_6c28:
; --- unverified ---
    lea 1448(a6),a0 ; app+$5A8
    clr.l -(a0)
    clr.l -(a0)
    moveq #7,d0
    bra.s hint_6c4e
hint_6c34:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_6c5e
hint_6c3c:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_6c5e
hint_6c42:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_6c5e
hint_6c48:
; --- unverified ---
    cmp.b #$2e,d1
    beq.s hint_6c5e
hint_6c4e:
; --- unverified ---
    ext.w d1
    move.b 126(a6,d1.w),d1
    move.b d1,(a0)+
    dbf d0,hint_6c34
hint_6c5a:
; --- unverified ---
    moveq #0,d0
    rts
hint_6c5e:
    dc.b    $4c,$ee,$00,$06,$05,$a0,$70,$ff
hint_6c66:
; --- unverified ---
    rts
hint_6c68:
; --- unverified ---
    move.w 2174(a6),d0 ; app+$87E
    beq.s hint_6c86
hint_6c6e:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    beq.s hint_6c7e
hint_6c74:
; --- unverified ---
    movea.l 2178(a6),a2 ; app+$882
    cmp.w 14(a2),d0
    beq.s hint_6c86
hint_6c7e:
; --- unverified ---
    subq.w #1,2174(a6) ; app+$87E
    bra.w hint_6b3a
hint_6c86:
; --- unverified ---
    moveq #48,d0
    bra.w loc_8486
hint_6c8c:
; --- unverified ---
    move.w 2174(a6),d0 ; app+$87E
    beq.s hint_6ca6
hint_6c92:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    beq.s hint_6ca2
hint_6c98:
; --- unverified ---
    movea.l 2178(a6),a2 ; app+$882
    cmp.w 14(a2),d0
    beq.s hint_6ca6
hint_6ca2:
; --- unverified ---
    bra.w hint_6b42
hint_6ca6:
; --- unverified ---
    moveq #49,d0
    bra.w loc_8486
hint_6cac:
; --- unverified ---
    tst.b 294(a6) ; app+$126
    beq.s hint_6cd4
hint_6cb2:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    bne.s hint_6cd4
hint_6cb8:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    beq.s hint_6cc4
hint_6cbe:
; --- unverified ---
    tst.b 279(a6) ; app+$117
    beq.s hint_6cd4
hint_6cc4:
; --- unverified ---
    move.w 2174(a6),d0 ; app+$87E
    addi.b #$30,d0
    move.b d0,2107(a6) ; app+$83B
    bra.w sub_92a0
hint_6cd4:
; --- unverified ---
    rts
hint_6cd6:
; --- unverified ---
    move.l #$1388,d1
    move.w d1,334(a6) ; app+$14E
    bsr.w sub_90ba
hint_6ce4:
; --- unverified ---
    move.l a0,330(a6) ; app+$14A
    rts
hint_6cea:
; --- unverified ---
    moveq #54,d0
    bra.w loc_8486
hint_6cf0:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    bne.s hint_6cea
hint_6cf6:
; --- unverified ---
    tst.l 2192(a6) ; app+$890
    bne.s hint_6cea
hint_6cfc:
; --- unverified ---
    bsr.w hint_2b02
hint_6d00:
; --- unverified ---
    movea.l 370(a6),a2 ; app+$172
    movem.l a4-a5,-(sp)
    bsr.w sub_0b88
hint_6d0c:
; --- unverified ---
    sne d0
    movem.l (sp)+,a4-a5
    tst.b 568(a6) ; app+$238
    bne.w hint_6e06
hint_6d1a:
; --- unverified ---
    tst.b d0
    beq.w loc_8436
hint_6d20:
; --- unverified ---
    moveq #8,d3
    clr.l d4
    bsr.w sub_0cba
hint_6d28:
; --- unverified ---
    pea 8(a1)
    move.b 569(a6),d0 ; app+$239
    beq.s hint_6d3e
hint_6d32:
; --- unverified ---
    cmp.b #$1,d0
    beq.s hint_6d3e
hint_6d38:
    dc.b    $08,$e9,$00,$03,$00,$0c
hint_6d3e:
; --- unverified ---
    movea.l 330(a6),a0 ; app+$14A
    cmpi.w #$110,334(a6) ; app+$14E
    bcc.s hint_6d4c
hint_6d4a:
; --- unverified ---
    bsr.s hint_6cd6
hint_6d4c:
    dc.b    $22,$5f,$22,$88,$42,$a8,$00,$08,$43,$e8,$00,$10,$20,$89,$21,$49
    dc.b    $00,$04,$21,$48,$00,$0c,$2d,$49,$01,$4a,$04,$6e,$00,$10,$01,$4e
    dc.b    $26,$48
hint_6d6e:
; --- unverified ---
    bsr.w loc_07f8
hint_6d72:
; --- unverified ---
    bsr.w sub_0698
hint_6d76:
; --- unverified ---
    bne.w loc_6b08
hint_6d7a:
; --- unverified ---
    bsr.s hint_6dac
hint_6d7c:
; --- unverified ---
    bsr.w hint_6bca
hint_6d80:
; --- unverified ---
    beq.s hint_6d6e
hint_6d82:
; --- unverified ---
    cmp.l #$454e444d,d1 ; 'ENDM'
    bne.s hint_6d6e
hint_6d8a:
; --- unverified ---
    tst.l d2
    bne.s hint_6d6e
hint_6d8e:
; --- unverified ---
    movea.l 12(a3),a0
    move.l 330(a6),4(a0) ; app+$14A
    moveq #10,d1
    btst #0,333(a6) ; app+$14D
    beq.s hint_6daa
hint_6da2:
    dc.b    $53,$6e,$01,$4e,$52,$ae,$01,$4a
hint_6daa:
; --- unverified ---
    rts
hint_6dac:
; --- unverified ---
    cmpi.w #$102,334(a6) ; app+$14E
    bcc.s hint_6de8
hint_6db4:
; --- unverified ---
    movea.l 12(a3),a0
    move.l 330(a6),4(a0) ; app+$14A
    bsr.w hint_6cd6
hint_6dc2:
    dc.b    $22,$6b,$00,$0c,$23,$48,$00,$08,$27,$48,$00,$0c,$43,$e8,$00,$0c
    dc.b    $20,$89,$42,$a8,$00,$04,$42,$a8,$00,$08,$70,$0c,$d0,$c0,$d1,$ae
    dc.b    $01,$4a,$91,$6e,$01,$4e
hint_6de8:
    dc.b    $20,$6e,$01,$4a,$22,$4c,$72,$0a
hint_6df0:
; --- unverified ---
    move.b (a1)+,d0
    move.b d0,(a0)+
    cmp.b d0,d1
    bne.s hint_6df0
hint_6df8:
; --- unverified ---
    move.l a0,330(a6) ; app+$14A
    move.l a1,d2
    sub.l a4,d2
    sub.w d2,334(a6) ; app+$14E
    rts
hint_6e06:
; --- unverified ---
    tst.b d0
    bne.w loc_843a
hint_6e0c:
; --- unverified ---
    cmpi.b #$8,13(a1)
    bne.w loc_8436
hint_6e16:
; --- unverified ---
    bset #6,12(a1)
    bne.w loc_8436
hint_6e20:
; --- unverified ---
    bsr.w loc_08dc
hint_6e24:
; --- unverified ---
    bsr.w sub_0698
hint_6e28:
; --- unverified ---
    bne.w loc_6b08
hint_6e2c:
; --- unverified ---
    bsr.w hint_6bca
hint_6e30:
; --- unverified ---
    beq.s hint_6e20
hint_6e32:
; --- unverified ---
    cmp.l #$454e444d,d1 ; 'ENDM'
    bne.s hint_6e20
hint_6e3a:
; --- unverified ---
    tst.l d2
    bne.s hint_6e20
hint_6e3e:
; --- unverified ---
    moveq #10,d1
    rts
sub_6e42:
    move.l #$1f40,d1
    move.w d1,2182(a6) ; app+$886
    bsr.w sub_90ba
loc_6e50:
    move.l a0,2184(a6) ; app+$888
    rts
loc_6e56:
    moveq #78,d0
    bra.w loc_846e
loc_6e5c:
    cmpi.w #$244,2182(a6) ; app+$886
    bcs.s loc_6e56
loc_6e64:
    movem.l d1/a1,-(sp)
    btst #3,12(a1)
    beq.s loc_6e76
loc_6e70:
    bsr.w loc_0c64
loc_6e74:
    bra.s loc_6e7a
loc_6e76:
    bsr.w loc_0c44
loc_6e7a:
    movem.l (sp)+,d1/a1
    tst.b 568(a6) ; app+$238
    beq.s loc_6e8e
loc_6e84:
    btst #6,12(a1)
    beq.w loc_844e
loc_6e8e:
    moveq #87,d0
    cmp.b #$a,d1
    beq.s loc_6eac
loc_6e96:
    cmp.b #$9,d1
    beq.s loc_6eac
loc_6e9c:
    cmp.b #$20,d1
    beq.s loc_6eac
loc_6ea2:
    cmp.b #$2e,d1
    bne.w loc_8446
loc_6eaa:
    moveq #0,d0
loc_6eac:
    movea.l 2184(a6),a0 ; app+$888
    sf 12(a0)
    move.l 2178(a6),(a0) ; app+$882
    move.l a0,2178(a6) ; app+$882
    move.w 2176(a6),10(a0) ; app+$880
    movea.l 8(a1),a1
    move.l a1,4(a0)
    move.l (a1),16(a0)
    move.w 2174(a6),14(a0) ; app+$87E
    lea 8(a0),a1
    clr.w (a1)
    lea 278(a0),a0
    move.b d0,(a0)+
    bne.s loc_6efe
loc_6ee2:
    subq.l #1,a0
loc_6ee4:
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s loc_6efe
loc_6eec:
    cmp.b #$9,d1
    beq.s loc_6efc
loc_6ef2:
    cmp.b #$20,d1
    beq.s loc_6efc
loc_6ef8:
    move.b d1,(a0)+
    bra.s loc_6ee4
loc_6efc:
    move.b (a4)+,d1
loc_6efe:
    clr.b (a0)+
loc_6f00:
    cmp.b #$a,d1
    beq.w loc_6f88
loc_6f08:
    cmp.b #$2a,d1
    beq.s loc_6f88
loc_6f0e:
    cmp.b #$3b,d1
    beq.s loc_6f88
loc_6f14:
    cmp.b #$9,d1
    beq.s loc_6f20
loc_6f1a:
    cmp.b #$20,d1
    bne.s loc_6f24
loc_6f20:
    move.b (a4)+,d1
    bra.s loc_6f00
loc_6f24:
    addq.w #1,(a1)
    cmp.b #$2c,d1
    beq.s loc_6f72
loc_6f2c:
    cmp.b #$a,d1
    beq.s loc_6f72
loc_6f32:
    cmp.b #$3c,d1
    bne.s loc_6f54
loc_6f38:
    move.b (a4)+,d1
    beq.s loc_6f38
loc_6f3c:
    cmp.b #$a,d1
    beq.s loc_6f72
loc_6f42:
    cmp.b #$3e,d1
    bne.s loc_6f50
loc_6f48:
    move.b (a4)+,d1
    cmp.b #$3e,d1
    bne.s loc_6f72
loc_6f50:
    move.b d1,(a0)+
    bra.s loc_6f38
loc_6f54:
    move.b d1,(a0)+
loc_6f56:
    move.b (a4)+,d1
    beq.s loc_6f56
loc_6f5a:
    cmp.b #$a,d1
    beq.s loc_6f72
loc_6f60:
    cmp.b #$9,d1
    beq.s loc_6f72
loc_6f66:
    cmp.b #$20,d1
    beq.s loc_6f72
loc_6f6c:
    cmp.b #$2c,d1
    bne.s loc_6f54
loc_6f72:
    clr.b (a0)+
    cmp.b #$2c,d1
    bne.s loc_6f88
loc_6f7a:
    move.b (a4)+,d1
    cmp.b #$a,d1
    bne.s loc_6f24
loc_6f82:
    bra.s loc_6fb4
loc_6f84:
    move.l (sp)+,2178(a6) ; app+$882
loc_6f88:
    move.l a0,d0
    addq.l #1,d0
    bclr #0,d0
    move.l 2184(a6),-(sp) ; app+$888
    move.l d0,2184(a6) ; app+$888
    sub.l (sp)+,d0
    sub.w d0,2182(a6) ; app+$886
    move.w 2200(a6),d0 ; app+$898
    bne.s loc_6fa8
loc_6fa4:
    st 280(a6) ; app+$118
loc_6fa8:
    st 257(a6) ; app+$101
    addq.w #1,d0
    move.w d0,2200(a6) ; app+$898
    rts
loc_6fb4:
    movea.l 2178(a6),a2 ; app+$882
    move.l a2,-(sp)
    move.l (a2),2178(a6) ; app+$882
    movem.l a0-a1,-(sp)
    bsr.w sub_061a
loc_6fc6:
    movem.l (sp)+,a0-a1
    bne.s loc_6f84
loc_6fcc:
    cmp.b #$26,d0
    bne.s loc_6f84
loc_6fd2:
    movem.l a0-a1,-(sp)
    bsr.w sub_07f0
loc_6fda:
    bsr.w loc_06ac
loc_6fde:
    movem.l (sp)+,a0-a1
    movea.l (sp)+,a2
    bne.w loc_6b08
loc_6fe8:
    move.l a2,2178(a6) ; app+$882
    move.b (a4)+,d1
    cmp.b #$26,d1
    beq.s loc_6ffa
loc_6ff4:
    moveq #70,d0
    bsr.w loc_8486
loc_6ffa:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s loc_6ffa
loc_7002:
    cmp.b #$20,d1
    beq.s loc_6ffa
loc_7008:
    bra.w loc_6f24
loc_700c:
    move.w 2200(a6),d0 ; app+$898
    cmp.w 2202(a6),d0 ; app+$89A
    bhi.s loc_7030
loc_7016:
    bsr.w sub_743c
loc_701a:
    movea.l a4,a0
    movea.l 2178(a6),a2 ; app+$882
    lea 20(a2),a1
    moveq #0,d2
    bra.w loc_710c
loc_702a:
    tst.l 2192(a6) ; app+$890
    bne.s loc_700c
loc_7030:
    movea.l 2178(a6),a2 ; app+$882
    movea.l 4(a2),a1
    movea.l 16(a2),a0
    cmpa.l 4(a1),a0
    bne.s loc_704c
loc_7042:
    movea.l 8(a1),a1
    move.l a1,4(a2)
    movea.l (a1),a0
loc_704c:
    moveq #10,d0
    movea.l a0,a4
    moveq #92,d2
loc_7052:
    move.b (a0)+,d1
    cmp.b d0,d1
    beq.s loc_705e
loc_7058:
    cmp.b d2,d1
    bne.s loc_7052
loc_705c:
    bra.s loc_707a
loc_705e:
    tst.l 2192(a6) ; app+$890
    beq.s loc_706e
loc_7064:
    move.w 2200(a6),d0 ; app+$898
    cmp.w 2202(a6),d0 ; app+$89A
    bls.s loc_7072
loc_706e:
    move.l a0,16(a2)
loc_7072:
    move.l a4,576(a6) ; app+$240
    moveq #0,d0
    rts
loc_707a:
    lea 20(a2),a1
    move.l a0,d2
    sub.l a4,d2
    subq.w #1,d2
    beq.s loc_7094
loc_7086:
    move.l a0,d1
    move.w d2,d0
    movea.l a4,a0
loc_708c:
    move.b (a0)+,(a1)+
    subq.w #1,d0
    bne.s loc_708c
loc_7092:
    movea.l d1,a0
loc_7094:
    move.b (a0)+,d1
    cmp.b #$a,d1
    beq.w loc_7126
loc_709e:
    cmp.b #$40,d1
    beq.w loc_7190
loc_70a6:
    cmp.b #$3c,d1
    beq.w loc_71f6
loc_70ae:
    cmp.b #$3f,d1
    beq.w loc_713c
loc_70b6:
    moveq #48,d0
    cmp.b d0,d1
    bcs.s loc_7132
loc_70bc:
    cmp.b #$3a,d1
    bcs.s loc_70de
loc_70c2:
    moveq #55,d0
    cmp.b #$41,d1
    bcs.s loc_7106
loc_70ca:
    cmp.b #$5b,d1
    bcs.s loc_70de
loc_70d0:
    moveq #87,d0
    cmp.b #$61,d1
    bcs.s loc_7106
loc_70d8:
    cmp.b #$7b,d1
    bcc.s loc_7106
loc_70de:
    sub.b d0,d1
    move.l a0,-(sp)
    lea 278(a2),a0
    ext.w d1
    beq.s loc_70f8
loc_70ea:
    cmp.w 8(a2),d1
    bgt.s loc_7102
loc_70f0:
    tst.b (a0)+
    bne.s loc_70f0
loc_70f4:
    subq.w #1,d1
    bne.s loc_70f0
loc_70f8:
    addq.b #1,d2
    beq.s loc_711e
loc_70fc:
    move.b (a0)+,(a1)+
    bne.s loc_70f8
loc_7100:
    subq.l #1,a1
loc_7102:
    movea.l (sp)+,a0
    bra.s loc_710c
loc_7106:
    addq.b #1,d2
    beq.s loc_7120
loc_710a:
    move.b d1,(a1)+
loc_710c:
    move.b (a0)+,d1
    cmp.b #$a,d1
    beq.s loc_7126
loc_7114:
    cmp.b #$5c,d1
    bne.s loc_7106
loc_711a:
    bra.w loc_7094
loc_711e:
    movea.l (sp)+,a0
loc_7120:
    cmpi.b #$a,(a0)+
    bne.s loc_7120
loc_7126:
    move.b #$a,(a1)+
    lea 20(a2),a4
    bra.w loc_705e
loc_7132:
    cmp.b #$23,d1
    beq.w loc_7270
loc_713a:
    bra.s loc_7106
loc_713c:
    move.b (a0)+,d1
    moveq #48,d0
    cmp.b d0,d1
    bcs.s loc_7132
loc_7144:
    cmp.b #$3a,d1
    bcs.s loc_7166
loc_714a:
    moveq #55,d0
    cmp.b #$41,d1
    bcs.s loc_7106
loc_7152:
    cmp.b #$5b,d1
    bcs.s loc_7166
loc_7158:
    moveq #87,d0
    cmp.b #$61,d1
    bcs.s loc_7106
loc_7160:
    cmp.b #$7b,d1
    bcc.s loc_7106
loc_7166:
    sub.b d0,d1
    move.l a0,-(sp)
    lea 278(a2),a0
    ext.w d1
    beq.s loc_7180
loc_7172:
    cmp.w 8(a2),d1
    bgt.s loc_718a
loc_7178:
    tst.b (a0)+
    bne.s loc_7178
loc_717c:
    subq.w #1,d1
    bne.s loc_7178
loc_7180:
    moveq #0,d1
loc_7182:
    tst.b (a0)+
    beq.s loc_718c
loc_7186:
    addq.l #1,d1
    bra.s loc_7182
loc_718a:
    moveq #0,d1
loc_718c:
    bra.w loc_71c4
loc_7190:
    tst.b 12(a2)
    bne.s loc_71a2
loc_7196:
    st 12(a2)
    addq.w #1,2176(a6) ; app+$880
    addq.w #1,10(a2)
loc_71a2:
    cmp.b #$f9,d2
    bcc.w loc_7120
loc_71aa:
    addq.b #1,d2
    move.b #$5f,(a1)+
    move.l a0,-(sp)
    moveq #0,d1
    move.w 10(a2),d1
    cmp.w #$a,d1
    bcs.s loc_71e2
loc_71be:
    cmp.w #$64,d1
    bcs.s loc_71e8
loc_71c4:
    movem.l d4/a2-a3,-(sp)
    movea.l a1,a3
    move.w d2,d4
    lea loc_71f0(pc),a2
    bsr.w sub_8f08
loc_71d4:
    movea.l a3,a1
    move.w d4,d2
    movem.l (sp)+,d4/a2-a3
    movea.l (sp)+,a0
    bra.w loc_710c
loc_71e2:
    addq.b #1,d2
    move.b #$30,(a1)+
loc_71e8:
    addq.b #1,d2
    move.b #$30,(a1)+
    bra.s loc_71c4
loc_71f0:
    addq.b #1,d4
    move.b d1,(a3)+
    rts
loc_71f6:
    cmp.b #$f5,d2
    bcc.w loc_7120
loc_71fe:
    move.b (a0)+,d1
    movem.l d2/d4/a0-a4,-(sp)
    cmp.b #$24,d1
    seq d4
    bne.s loc_7214
loc_720c:
    move.b (a0)+,d1
    bra.s loc_7214
loc_7210:
    move.l d2,d1
    bra.s loc_7236
loc_7214:
    movea.l a0,a4
    lea 1000(a6),a0 ; app+$3E8
    bsr.w sub_76b8
loc_721e:
    bne.s loc_7262
loc_7220:
    cmp.b #$3e,d1
    bne.s loc_7262
loc_7226:
    bsr.w sub_14c2
loc_722a:
    beq.s loc_7210
loc_722c:
    bsr.w sub_0bce
loc_7230:
    bne.s loc_7262
loc_7232:
    move.l 8(a1),d1
loc_7236:
    movea.l 12(sp),a3
    lea loc_71f0(pc),a2
    tst.b d4
    beq.s loc_724a
loc_7242:
    move.l (sp),d4
    bsr.w sub_8ed8
loc_7248:
    bra.s loc_7250
loc_724a:
    move.l (sp),d4
    bsr.w sub_8f08
loc_7250:
    move.l a3,d1
    move.w d4,d2
    move.l a4,d3
    movem.l (sp)+,d0/d4/a0-a4
    movea.l d1,a1
    movea.l d3,a0
    bra.w loc_710c
loc_7262:
    movem.l (sp)+,d2/d4/a0-a4
    moveq #73,d0
    bsr.w loc_8486
loc_726c:
    bra.w loc_710c
loc_7270:
    cmp.b #$fc,d2
    bcc.w loc_7120
loc_7278:
    moveq #0,d1
    move.w 8(a2),d1
    move.l a0,-(sp)
    bra.w loc_71c4
sub_7284:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    beq.s hint_72de
hint_728a:
    dc.b    $24,$6e,$08,$82,$3d,$6a,$00,$0e,$08,$7e
hint_7294:
; --- unverified ---
    tst.b 257(a6) ; app+$101
    beq.s hint_72de
hint_729a:
; --- unverified ---
    tst.b 279(a6) ; app+$117
    bne.s hint_72a4
hint_72a0:
    dc.b    $50,$ee,$01,$13
hint_72a4:
; --- unverified ---
    subq.w #1,2200(a6) ; app+$898
    movea.l 2178(a6),a2 ; app+$882
    move.l a2,d0
    sub.l 2184(a6),d0 ; app+$888
    sub.w d0,2182(a6) ; app+$886
    move.l a2,2184(a6) ; app+$888
    move.w 14(a2),d0
    cmp.w 2174(a6),d0 ; app+$87E
    beq.s hint_72ce
hint_72c4:
; --- unverified ---
    move.w d0,2174(a6) ; app+$87E
    moveq #10,d0
    bsr.w sign_extended_operand
hint_72ce:
; --- unverified ---
    move.l (a2),d0
    move.l d0,2178(a6) ; app+$882
    bne.s hint_72da
hint_72d6:
    dc.b    $51,$ee,$01,$01
hint_72da:
; --- unverified ---
    moveq #10,d1
    rts
hint_72de:
; --- unverified ---
    moveq #53,d0
    bra.w loc_8486
hint_72e4:
; --- unverified ---
    moveq #59,d0
    bra.w loc_846e
hint_72f6:
; --- unverified ---
    bsr.w loc_0c84
hint_72fa:
; --- unverified ---
    tst.l 2192(a6) ; app+$890
    bne.w hint_7336
hint_7302:
; --- unverified ---
    bsr.w hint_6ad2
hint_7306:
; --- unverified ---
    move.l d2,2188(a6) ; app+$88C
    bgt.s hint_733c
hint_730c:
; --- unverified ---
    bsr.w sub_07f0
hint_7310:
; --- unverified ---
    bsr.w loc_06ac
hint_7314:
; --- unverified ---
    bne.w loc_6b08
hint_7318:
; --- unverified ---
    bsr.w hint_6bca
hint_731c:
; --- unverified ---
    beq.s hint_730c
hint_731e:
; --- unverified ---
    tst.l d2
    bne.s hint_730c
hint_7322:
; --- unverified ---
    cmp.l #$52455054,d1 ; 'REPT'
    beq.s hint_7336
hint_732a:
; --- unverified ---
    cmp.l #$454e4452,d1 ; 'ENDR'
    bne.s hint_730c
hint_7332:
; --- unverified ---
    moveq #10,d1
    rts
hint_7336:
; --- unverified ---
    moveq #71,d0
    bra.w loc_8486
hint_733c:
; --- unverified ---
    movea.l 330(a6),a0 ; app+$14A
    cmpi.w #$110,334(a6) ; app+$14E
    bcc.s hint_734c
hint_7348:
; --- unverified ---
    bsr.w hint_6cd6
hint_734c:
    dc.b    $2d,$48,$08,$90,$3f,$2e,$01,$4e,$42,$a8,$00,$08,$43,$e8,$00,$10
    dc.b    $20,$89,$21,$49,$00,$04,$21,$48,$00,$0c,$2d,$49,$01,$4a,$04,$6e
    dc.b    $00,$10,$01,$4e,$26,$48
hint_7372:
; --- unverified ---
    bsr.w sub_07f0
hint_7376:
; --- unverified ---
    clr.l 2192(a6) ; app+$890
    bsr.w loc_06ac
hint_737e:
; --- unverified ---
    bne.w loc_6b08
hint_7382:
; --- unverified ---
    move.l a3,2192(a6) ; app+$890
    bsr.w hint_6dac
hint_738a:
; --- unverified ---
    bsr.w hint_6bca
hint_738e:
; --- unverified ---
    beq.s hint_7372
hint_7390:
; --- unverified ---
    cmp.l #$454e4452,d1 ; 'ENDR'
    bne.s hint_7372
hint_7398:
; --- unverified ---
    tst.l d2
    bne.s hint_7372
hint_739c:
; --- unverified ---
    bsr.w sub_07f0
hint_73a0:
; --- unverified ---
    st 275(a6) ; app+$113
    movea.l 12(a3),a0
    move.l 330(a6),4(a0) ; app+$14A
    btst #0,333(a6) ; app+$14D
    beq.s hint_73ca
hint_73b6:
; --- unverified ---
    subq.w #1,334(a6) ; app+$14E
    addq.l #1,330(a6) ; app+$14A
    tst.b 257(a6) ; app+$101
    beq.s hint_73ca
hint_73c4:
    dc.b    $3d,$6e,$08,$98,$08,$9a
hint_73ca:
; --- unverified ---
    subq.l #1,2188(a6) ; app+$88C
    bcs.s hint_740c
hint_73d0:
    dc.b    $2d,$4b,$08,$90,$43,$eb,$00,$10,$2d,$49,$08,$94
hint_73dc:
; --- unverified ---
    bsr.w loc_06ac
hint_73e0:
; --- unverified ---
    bne.w loc_6b08
hint_73e4:
; --- unverified ---
    movem.l a3-a4,-(sp)
    bsr.w hint_6bca
hint_73ec:
; --- unverified ---
    movem.l (sp)+,a3-a4
    beq.s hint_73fe
hint_73f2:
; --- unverified ---
    cmp.l #$454e4452,d1 ; 'ENDR'
    bne.s hint_73fe
hint_73fa:
; --- unverified ---
    tst.l d2
    beq.s hint_73ca
hint_73fe:
; --- unverified ---
    st 275(a6) ; app+$113
    move.l a3,-(sp)
    bsr.w loc_09c8
hint_7408:
; --- unverified ---
    movea.l (sp)+,a3
    bra.s hint_73dc
hint_740c:
; --- unverified ---
    move.w (sp)+,d0
    move.w 334(a6),d2 ; app+$14E
    tst.l 8(a3)
    beq.s hint_741a
hint_7418:
    dc.b    $70,$00
hint_741a:
; --- unverified ---
    sub.w d0,d2
    sub.w d2,334(a6) ; app+$14E
    ext.l d2
    add.l d2,330(a6) ; app+$14A
    clr.l 2192(a6) ; app+$890
    lea pcref_9884(pc),a0
    move.l a0,378(a6) ; app+$17A
    moveq #10,d1
    rts
hint_7436:
; --- unverified ---
    moveq #72,d0
    bra.w loc_8486
sub_743c:
    movea.l 2192(a6),a1 ; app+$890
    movea.l 2196(a6),a0 ; app+$894
    cmpa.l 4(a1),a0
    bne.s loc_7454
loc_744a:
    movea.l 8(a1),a1
    move.l a1,2192(a6) ; app+$890
    movea.l (a1),a0
loc_7454:
    movea.l a0,a4
    moveq #10,d0
loc_7458:
    cmp.b (a0)+,d0
    bne.s loc_7458
loc_745c:
    move.l a0,2196(a6) ; app+$894
    move.l a4,576(a6) ; app+$240
    moveq #0,d0
    rts
str_7468:
    dc.b    "NEEQC",0
    dc.b    $4e,$43,$44,$00
    dc.b    "NDGTGELTLE",0
    dc.b    $00
loc_747e:
    move.l d2,-(sp)
    bra.w loc_0ae8
pcref_7484:
    dc.b    $00,$00,$0d,$fe,$00,$00
loc_748a:
    lea pcref_7484(pc),a0
    tst.b 568(a6) ; app+$238
    beq.s loc_749c
loc_7494:
    bsr.w sub_9700
loc_7498:
    move.b -1(a4),d1
loc_749c:
    moveq #0,d0
    bra.w loc_752e
loc_74a2:
    tst.b 568(a6) ; app+$238
    beq.s loc_74b0
loc_74a8:
    bsr.w sub_9700
loc_74ac:
    move.b -1(a4),d1
loc_74b0:
    cmp.b #$2e,d1
    bne.s loc_7502
loc_74b6:
    move.b (a4)+,d1
    bmi.s loc_74d2
loc_74ba:
    ext.w d1
    lea pcref_7578(pc),a1
    adda.w d1,a1
    move.b 5(a0),d0
    bne.s loc_74d6
loc_74c8:
    move.b (a1),d0
    bmi.s loc_74f6
loc_74cc:
    cmp.b #$4,d0
    bcs.s loc_7518
loc_74d2:
    bra.w loc_844a
loc_74d6:
    bmi.s loc_74e6
loc_74d8:
    tst.b 290(a6) ; app+$122
    bne.w loc_74e6
loc_74e0:
    subq.w #1,d0
loc_74e2:
    beq.s loc_747e
loc_74e4:
    bra.s loc_74c8
loc_74e6:
    move.b (a1),d0
    bpl.s loc_7518
loc_74ea:
    addq.w #2,d0
    beq.s loc_7514
loc_74ee:
    addq.b #1,d0
    bne.s loc_74d2
loc_74f2:
    moveq #6,d0
    bra.s loc_752e
loc_74f6:
    addq.b #2,d0
    beq.s loc_7514
loc_74fa:
    addq.b #1,d0
    bne.s loc_74d2
loc_74fe:
    moveq #1,d0
    bra.s loc_7518
loc_7502:
    move.b 5(a0),d0
    subq.w #1,d0
    bne.s loc_7510
loc_750a:
    tst.b 290(a6) ; app+$122
    beq.s loc_74e2
loc_7510:
    moveq #0,d0
    bra.s loc_752e
loc_7514:
    moveq #2,d0
    subq.l #1,a4
loc_7518:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s loc_752e
loc_7520:
    cmp.b #$20,d1
    beq.s loc_752e
loc_7526:
    cmp.b #$a,d1
    bne.w loc_844a
loc_752e:
    cmp.b #$a,d1
    beq.s loc_7542
loc_7534:
    move.b (a4)+,d1
    cmp.b #$9,d1
    beq.s loc_752e
loc_753c:
    cmp.b #$20,d1
    beq.s loc_752e
loc_7542:
    move.b d0,569(a6) ; app+$239
    sf 571(a6) ; app+$23B
    move.w (a0)+,d6
    move.w (a0)+,d3
    move.w (a0)+,d2
    pea pcref_7614(pc)
    lea str_1d14(pc),a0
    adda.w d3,a0
    move.l a0,-(sp)
    move.w d1,-(sp)
    btst #15,d2
    beq.s loc_756a
loc_7564:
    bsr.w loc_0c64
loc_7568:
    bra.s loc_7574
loc_756a:
    btst #14,d2
    beq.s loc_7574
loc_7570:
    bsr.w loc_0c44
loc_7574:
    move.w (sp)+,d1
    rts
pcref_7578:
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$fe,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $fe,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$01,$ff,$04,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$03,$ff,$ff,$ff
    dc.b    $05,$ff,$ff,$fd,$ff,$ff,$ff,$02,$07,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$01,$ff,$04,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$03,$ff,$ff,$ff
    dc.b    $05,$ff,$ff,$fd,$ff,$ff,$ff,$02,$07,$ff,$ff,$ff,$ff,$ff,$ff,$ff
sub_75f8:
; --- unverified ---
    tst.b 293(a6) ; app+$125
    beq.s hint_7604
hint_75fe:
; --- unverified ---
    moveq #101,d0
    bsr.w loc_8486
hint_7604:
; --- unverified ---
    move.w d6,(a5)+
    moveq #10,d1
    rts
hint_760a:
    dc.b    $20,$6e
hint_760c:
    dc.b    $01,$7a
pcref_7614:
hint_761a:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_7638
hint_7620:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_7638
hint_7626:
; --- unverified ---
    cmp.b #$2a,d1
    beq.s hint_7638
hint_762c:
; --- unverified ---
    cmp.b #$3b,d1
    beq.s hint_7638
hint_7632:
; --- unverified ---
    moveq #14,d0
    bsr.w loc_8486
hint_7638:
; --- unverified ---
    tst.l 378(a6) ; app+$17A
    bne.s hint_760a
hint_763e:
; --- unverified ---
    tst.l 398(a6) ; app+$18E
    beq.s hint_765e
hint_7644:
; --- unverified ---
    move.l 398(a6),d1 ; app+$18E
    clr.l 398(a6) ; app+$18E
    add.l d1,572(a6) ; app+$23C
    tst.l d1
    bmi.s hint_7658
hint_7654:
    dc.b    $d3,$ae,$02,$24
hint_7658:
; --- unverified ---
    clr.l 386(a6) ; app+$182
    rts
hint_765e:
; --- unverified ---
    move.l a5,d1
    sub.l 588(a6),d1 ; app+$24C
    move.l d1,386(a6) ; app+$182
    beq.s hint_767e
hint_766a:
; --- unverified ---
    move.l 572(a6),d2 ; app+$23C
    add.l d1,572(a6) ; app+$23C
    add.l d1,548(a6) ; app+$224
    tst.b 568(a6) ; app+$238
    bne.w loc_970e
hint_767e:
; --- unverified ---
    rts
sub_7680:
    bsr.s sub_76b8
loc_7682:
    bne.s loc_76a0
loc_7684:
    movea.l (a0),a1
    move.b 5(a0),d0
    moveq #46,d2
    addq.l #1,a1
    bra.s loc_7694
loc_7690:
    cmp.b (a1)+,d2
    beq.s loc_76a2
loc_7694:
    subq.b #1,d0
    bne.s loc_7690
loc_7698:
    move.b 5(a0),d2
    movea.l a4,a1
    moveq #0,d0
loc_76a0:
    rts
loc_76a2:
    movea.l a4,a1
    move.b 5(a0),d2
    sub.b d0,5(a0)
    ext.w d0
    suba.w d0,a4
    move.b -1(a4),d1
    moveq #0,d0
    rts
sub_76b8:
    andi.w #$ff,d1
    lea sub_a764(pc),a2
    tst.b 0(a2,d1.w)
    beq.s loc_76f4
loc_76c6:
    bpl.s loc_7736
loc_76c8:
    move.b (a4),d1
    ext.w d1
    move.b 126(a6,d1.w),d1
    cmp.b #$57,d1
    beq.s loc_76e2
loc_76d6:
    cmp.b #$42,d1
    beq.s loc_76e2
loc_76dc:
    cmp.b #$4c,d1
    bne.s loc_76f0
loc_76e2:
    move.b 1(a4),d1
    tst.b 0(a2,d1.w)
    ble.s loc_76f0
loc_76ec:
    moveq #46,d1
    bra.s loc_7736
loc_76f0:
    moveq #46,d1
    bra.s loc_773c
loc_76f4:
    cmp.b #$3a,d1
    bcc.s loc_773c
loc_76fa:
    lea -1(a4),a1
    movea.l a4,a2
loc_7700:
    move.b (a2)+,d1
    cmp.b #$24,d1
    beq.s loc_7714
loc_7708:
    cmp.b #$3a,d1
    bcc.s loc_7736
loc_770e:
    cmp.b #$30,d1
    bcc.s loc_7700
loc_7714:
    movea.l a2,a4
    move.l a2,d0
    sub.l a1,d0
    move.b d0,5(a0)
    lea 6(a0),a2
    move.l a2,(a0)
    move.b 278(a6),(a2)+ ; app+$116
    subq.b #1,d0
loc_772a:
    move.b (a1)+,(a2)+
    subq.b #1,d0
    bne.s loc_772a
loc_7730:
    move.b (a4)+,d1
    moveq #0,d0
    rts
loc_7736:
    clr.l (a0)
    moveq #41,d0
    rts
loc_773c:
    tst.b 254(a6) ; app+$FE
    bne.w loc_77b0
loc_7744:
    move.b d1,6(a0)
    lea -1(a4),a1
    move.l a1,(a0)
    moveq #0,d1
    moveq #0,d2
loc_7752:
    move.b (a4)+,d1
    tst.b 0(a2,d1.w)
    beq.s loc_7752
loc_775a:
    bpl.s loc_7794
loc_775c:
    move.l a4,d2
    bra.s loc_7752
loc_7760:
    sub.l a4,d2
    addq.l #2,d2
    bne.s loc_7798
loc_7766:
    move.b -2(a4),d2
    cmp.b #$4c,d2
    beq.s loc_778e
loc_7770:
    cmp.b #$6c,d2
    beq.s loc_778e
loc_7776:
    cmp.b #$57,d2
    beq.s loc_778e
loc_777c:
    cmp.b #$77,d2
    beq.s loc_778e
loc_7782:
    cmp.b #$42,d2
    beq.s loc_778e
loc_7788:
    cmp.b #$62,d2
    bne.s loc_7798
loc_778e:
    subq.l #2,a4
    moveq #46,d1
    bra.s loc_7798
loc_7794:
    tst.l d2
    bne.s loc_7760
loc_7798:
    move.l a4,d0
    sub.l (a0),d0
    cmp.w 542(a6),d0 ; app+$21E
    bcs.s loc_77a6
loc_77a2:
    move.w 542(a6),d0 ; app+$21E
loc_77a6:
    subq.b #1,d0
    move.b d0,5(a0)
    moveq #0,d0
    rts
loc_77b0:
    lea 6(a0),a1
    move.l a1,(a0)
    moveq #1,d2
    moveq #0,d0
loc_77ba:
    ext.w d1
    move.b 126(a6,d1.w),d1
    move.b d1,(a1)+
    moveq #0,d1
    move.b (a4)+,d1
    tst.b 0(a2,d1.w)
    bgt.s loc_77e4
loc_77cc:
    bmi.s loc_77d6
loc_77ce:
    addq.b #1,d2
    bpl.s loc_77ba
loc_77d2:
    moveq #127,d2
    bra.s loc_77dc
loc_77d6:
    move.l a4,d0
    addq.b #1,d2
    bpl.s loc_77ba
loc_77dc:
    move.b (a4)+,d1
    tst.b 0(a2,d1.w)
    ble.s loc_77dc
loc_77e4:
    tst.l d0
    beq.s loc_7810
loc_77e8:
    sub.l a4,d0
    addq.l #2,d0
    bne.s loc_7810
loc_77ee:
    move.b -2(a4),d0
    cmp.b #$4c,d0
    beq.s loc_780a
loc_77f8:
    cmp.b #$6c,d0
    beq.s loc_780a
loc_77fe:
    cmp.b #$57,d0
    beq.s loc_780a
loc_7804:
    cmp.b #$77,d0
    bne.s loc_7810
loc_780a:
    moveq #46,d1
    subq.l #2,a4
    subq.b #2,d2
loc_7810:
    move.b d2,5(a0)
    moveq #0,d0
    rts
sub_7818:
    moveq #0,d0
    move.b d1,d2
    cmp.b #$22,d1
    beq.s loc_782c
loc_7822:
    cmp.b #$27,d1
    beq.s loc_782c
loc_7828:
    moveq #0,d2
    subq.l #1,a4
loc_782c:
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s loc_7870
loc_7834:
    cmp.b d1,d2
    beq.s loc_7880
loc_7838:
    cmp.b #$9,d1
    beq.s loc_7844
loc_783e:
    cmp.b #$20,d1
    bne.s loc_7848
loc_7844:
    tst.b d2
    beq.s loc_7870
loc_7848:
    cmp.b #$2c,d1
    bne.s loc_785a
loc_784e:
    btst #16,d3
    beq.s loc_785a
loc_7854:
    move.l a4,406(a6) ; app+$196
    bra.s loc_7870
loc_785a:
    btst #17,d3
    bne.s loc_7866
loc_7860:
    ext.w d1
    move.b 126(a6,d1.w),d1
loc_7866:
    move.b d1,6(a0,d0.w)
    addq.b #1,d0
    bpl.s loc_782c
loc_786e:
    moveq #126,d0
loc_7870:
    lea 5(a0),a1
    addq.b #1,d0
    move.b d0,(a1)+
    move.b d3,5(a0,d0.w)
    move.l a1,(a0)
    rts
loc_7880:
    cmpi.b #$2c,(a4)+
    bne.s loc_7870
loc_7886:
    bra.s loc_7854
pcref_7888:
    dc.b    $ff,$ff,$ff,$00
sub_788c:
; --- unverified ---
    move.l d2,d0
    and.l pcref_7888(pc),d0
    beq.s hint_78d8
hint_7894:
; --- unverified ---
    cmp.l pcref_7888(pc),d0
    beq.s hint_78d8
hint_789a:
; --- unverified ---
    bra.s sub_78c6
hint_789c:
; --- unverified ---
    move.l d2,d0
    swap d0
    tst.w d0
    beq.s hint_78d8
hint_78a4:
; --- unverified ---
    addq.w #1,d0
    beq.s hint_78d8
hint_78a8:
; --- unverified ---
    bra.s sub_78c6
hint_78aa:
; --- unverified ---
    cmp.b #$1,d3
    beq.s sub_78cc
hint_78b0:
; --- unverified ---
    move.b d2,d0
    ext.w d0
    bra.s loc_78be
hint_78b6:
; --- unverified ---
    cmp.b #$1,d3
    beq.s sub_78cc
sub_78bc:
    move.w d2,d0
loc_78be:
    ext.l d0
    cmp.l d0,d2
    bne.s sub_78c6
loc_78c4:
    rts
sub_78c6:
    moveq #29,d0
    bra.w loc_8486
sub_78cc:
; --- unverified ---
    moveq #30,d0
    tst.b 263(a6) ; app+$107
    beq.w loc_8486
hint_78d6:
; --- unverified ---
    rts
hint_78d8:
; --- unverified ---
    cmp.b #$1,d3
    beq.s sub_78cc
hint_78de:
; --- unverified ---
    rts
loc_78e0:
    movea.l a4,a0
    lea 1407(a6),a4 ; app+$57F
    move.b (a4)+,d1
loc_78e8:
    move.l a0,-(sp)
    bsr.s sub_7902
loc_78ec:
    lea pcref_78fc(pc),a4
    move.b (a4)+,d1
    moveq #1,d3
    bsr.w sub_7952
loc_78f8:
    movea.l (sp)+,a4
    rts
pcref_78fc:
    dc.b    "TEXT",$0a,0
sub_7902:
    clr.l 346(a6) ; app+$15A
    lea 1000(a6),a0 ; app+$3E8
    moveq #9,d3
    bsr.w sub_7818
loc_7910:
    movea.l 370(a6),a2 ; app+$172
    movem.l a3-a5,-(sp)
    bsr.w sub_0b88
loc_791c:
    sne d0
    movem.l (sp)+,a3-a5
    tst.b 568(a6) ; app+$238
    bne.s loc_7942
loc_7928:
    tst.b d0
    beq.s loc_7942
loc_792c:
    moveq #0,d4
    moveq #9,d3
    bsr.w sub_0cba
sub_7934:
    move.l a1,318(a6) ; app+$13E
    lea 16(a1),a1
    move.l a1,354(a6) ; app+$162
    rts
loc_7942:
    tst.b d0
    bne.s loc_794c
loc_7946:
    bsr.s sub_7934
loc_7948:
    bra.w loc_96a4
loc_794c:
    moveq #11,d0
    bra.w loc_846e
sub_7952:
    sf 283(a6) ; app+$11B
    sf 284(a6) ; app+$11C
    move.b d3,264(a6) ; app+$108
    lea 1000(a6),a0 ; app+$3E8
    clr.l 406(a6) ; app+$196
    bset #16,d3
    btst #1,541(a6) ; app+$21D
    beq.s loc_7976
loc_7972:
    bset #17,d3
loc_7976:
    bsr.w sub_7818
loc_797a:
    movea.l 318(a6),a2 ; app+$13E
    addq.w #8,a2
    movem.l d3/a3-a5,-(sp)
    bsr.w sub_0b88
loc_7988:
    sne d0
    movem.l (sp)+,d3/a3-a5
    tst.b 568(a6) ; app+$238
    bne.s loc_79c6
loc_7994:
    tst.b d0
    beq.s loc_79b2
loc_7998:
    moveq #0,d4
    bsr.w sub_0cba
loc_799e:
    movea.l 318(a6),a0 ; app+$13E
    subq.b #1,12(a0)
sub_79a6:
    move.b 12(a0),d0
    bsr.w sub_79e4
loc_79ae:
    move.b d0,14(a1)
loc_79b2:
    move.l a1,322(a6) ; app+$142
    move.l 8(a1),572(a6) ; app+$23C
    move.b 14(a1),326(a6) ; app+$146
    bra.w loc_988a
loc_79c6:
    tst.b d0
    beq.s loc_79b2
loc_79ca:
    bra.s loc_794c
sub_79cc:
    movea.l 322(a6),a1 ; app+$142
    move.l 572(a6),8(a1) ; app+$23C
    bra.w loc_9864
sub_79da:
    tst.b 568(a6) ; app+$238
    bne.w loc_96be
loc_79e2:
    rts
sub_79e4:
    rts
sub_79e6:
    movea.l 2368(a6),a0 ; app+$940
    clr.w (a0)
    move.l a0,2204(a6) ; app+$89C
    sf 267(a6) ; app+$10B
    rts
sub_79f6:
    move.l a0,-(sp)
    movea.l 2204(a6),a0 ; app+$89C
    move.w #$2b2b,(a0)+
    move.w d3,(a0)+
loc_7a02:
    move.l a0,2204(a6) ; app+$89C
    clr.w (a0)
    movea.l (sp)+,a0
    rts
sub_7a0c:
    move.l a0,-(sp)
    move.b 14(a1),d0
    movea.l 2204(a6),a0 ; app+$89C
    move.w #$2b2b,(a0)+
    st (a0)+
    move.b d0,(a0)+
    bra.s loc_7a02
sub_7a20:
    move.l a0,-(sp)
    movea.l 2204(a6),a0 ; app+$89C
    move.w #$2d2d,-4(a0)
    movea.l (sp)+,a0
    rts
str_7a30:
    dc.b    "line malformed",0
    dc.b    "out of memory",0
    dc.b    "undefined symbol",0
    dc.b    "additional symbol on pass 2",0
    dc.b    "symbol defined twice",0
    dc.b    "phasing error",0
    dc.b    "local not allowed",0
    dc.b    "INTERNAL:invalid hashing",0
    dc.b    "instruction not recognised",0
    dc.b    "invalid size",0
    dc.b    "duplicate MODULE name",0
    dc.b    "forward reference",0
    dc.b    "invalid section name, TEXT assumed",0
    dc.b    "garbage following instruction",0
    dc.b    "addressing mode not recognised",0
    dc.b    "address register expected",0
    dc.b    "addressing mode not allowed",0
    dc.b    "expression mismatch",0
    dc.b    "missing close bracket",0
    dc.b    "imported label not allowed",0
    dc.b    "illegal type combination",0
    dc.b    "invalid number",0
    dc.b    "number too large",0
    dc.b    "misuse of label",0
    dc.b    "include file read error",0
    dc.b    "file not found",0
    dc.b    "header file not found",0
    dc.b    "repeated include file",0
    dc.b    "data too large",0
    dc.b    "relative not allowed",0
    dc.b    "comma expected",0
    dc.b    ".W or .L expected as index size",0
    dc.b    "absolute not allowed",0
    dc.b    "wrong processor",0
    dc.b    "odd address",0
    dc.b    "immediate data expected",0
    dc.b    "data register expected",0
    dc.b    "BSS or OFFSET section cannot contain data",0
    dc.b    "during writing binary file",0
    dc.b    "cannot create binary file",0
    dc.b    "symbol expected",0
    dc.b    "XREFs not allowed within brackets",0
    dc.b    "cannot import symbol",0
    dc.b    "cannot export symbol",0
    dc.b    "not yet implemented",0
    dc.b    "register expected",0
    dc.b    "invalid MOVEP addressing mode",0
    dc.b    "spurious ENDC",0
    dc.b    "spurious ELSE",0
    dc.b    "missing ENDC",0
    dc.b    "invalid IF expression, ignored",0
    dc.b    "source expired prematurely",0
    dc.b    "spurious ENDM or MEXIT",0
    dc.b    "cannot nest MACRO definitions or define in REPTs",0
    dc.b    "missing quote",0
    dc.b    "user error",0
    dc.b    "invalid register list",0
    dc.b    "invalid option",0
    dc.b    "fatally bad conditional",0
    dc.b    "relocation not allowed",0
    dc.b    "division by zero",0
    dc.b    "absolute expression MUST evaluate",0
    dc.b    "illegal BSR.S",0
    dc.b    "option must be at start",0
    dc.b    "INTERNAL:invalid optimisation",0
    dc.b    "can only assemble executable code to memory",0
    dc.b    "program buffer full",0
    dc.b    "linker format restriction",0
    dc.b    "ORG/RORG not allowed",0
    dc.b    "INTERNAL:invalid multi-line macro call",0
    dc.b    "cannot nest repeat loops",0
    dc.b    "spurious ENDR",0
    dc.b    "invalid numeric expansion",0
    dc.b    "during listing output",0
    dc.b    "invalid printer parameter",0
    dc.b    "invalid FORMAT parameter",0
    dc.b    "INTERNAL:bad section",0
    dc.b    "INTERNAL:macro memory",0
    dc.b    "assembly interrupted",0
    dc.b    "invalid section type",0
    dc.b    "in command-line symbol",0
    dc.b    "# probably missing",0
    dc.b    "short branch cannot be 0 bytes",0
    dc.b    "DCB or DS count must not be negative",0
    dc.b    "invalid bitfield specification",0
    dc.b    "colon (:) expected",0
    dc.b    "floating-point register expected",0
    dc.b    "MMU register expected",0
    dc.b    "invalid MMU function code",0
    dc.b    "invalid radix",0
    dc.b    "invalid 68020 addressing mode",0
    dc.b    "invalid index scale",0
    dc.b    "hex floating point number too large",0
    dc.b    "invalid opcode size for data/address register",0
    dc.b    "only FPIAR allowed",0
    dc.b    "maths co-processor required",0
    dc.b    "invalid k-factor",0
    dc.b    "floating point constant not allowed",0
    dc.b    "floating point constant too large",0
    dc.b    "bad floating point expression",0
    dc.b    "privileged instruction",0
    dc.b    "invalid section specified",0
    dc.b    "invalid pre-assembled file",0
    dc.b    "only (An) allowed for this instruction",0
    dc.b    "INTERNAL:memory list corrupt",0
    dc.b    "bit number shoul"
sub_840c:
; --- unverified ---
    bcc.s loc_842e
hint_840e:
    dc.b    $62,$65
hint_8410:
; --- unverified ---
    move.l ([543584114,a0],d2.l*4,543324532),d0
    bcs.w sub_f446
hint_8420:
; --- unverified ---
    bra.s loc_846e
sub_8422:
    bsr.w call_write_b024
loc_8426:
    bne.s loc_842a
loc_8428:
    rts
loc_842a:
    bsr.w sub_98ae
loc_842e:
    moveq #39,d0
    bra.s loc_846e
loc_8432:
    moveq #1,d0
    bra.s loc_8486
loc_8436:
    moveq #5,d0
    bra.s loc_8486
loc_843a:
    moveq #4,d0
    bra.s loc_8486
loc_843e:
    moveq #6,d0
    bra.s loc_8486
loc_8442:
    moveq #7,d0
    bra.s loc_8486
loc_8446:
    moveq #9,d0
    bra.s loc_8486
loc_844a:
    moveq #10,d0
    bra.s loc_8486
loc_844e:
    moveq #12,d0
    bra.s loc_8486
loc_8452:
    moveq #33,d0
    bra.s loc_8486
sub_8456:
; --- unverified ---
    moveq #29,d0
    bra.s loc_8486
sub_845a:
    moveq #38,d0
    bra.s loc_8486
hint_845e:
; --- unverified ---
    moveq #15,d0
    bra.s loc_8482
hint_8462:
; --- unverified ---
    moveq #31,d0
    bra.s loc_8482
hint_8466:
; --- unverified ---
    moveq #32,d0
    bra.s loc_8482
hint_846a:
; --- unverified ---
    moveq #36,d0
    bra.s loc_8482
loc_846e:
    sf 2389(a6) ; app+$955
    move.b #$14,570(a6) ; app+$23A
    bsr.s loc_8486
loc_847a:
    jmp loc_03b0
line_malformed:
    rts
loc_8482:
    movea.l 564(a6),sp ; app+$234
loc_8486:
    tst.b 269(a6) ; app+$10D
    bne.s line_malformed
loc_848c:
    st 269(a6) ; app+$10D
    cmpi.b #$a,570(a6) ; app+$23A
    bcc.s loc_849e
loc_8498:
    move.b #$a,570(a6) ; app+$23A
loc_849e:
    move.l a4,340(a6) ; app+$154
    movem.l d1-d3/a0-a3,-(sp)
    move.w d0,-(sp)
    moveq #6,d0
    bsr.w sub_8e7a
loc_84ae:
    lea str_7a30(pc),a0
    addq.b #1,268(a6) ; app+$10C
    moveq #0,d2
loc_84b8:
    move.w (sp)+,d0
loc_84ba:
    subq.w #1,d0
    beq.w loc_84c6
loc_84c0:
    tst.b (a0)+
    bne.s loc_84c0
loc_84c4:
    bra.s loc_84ba
loc_84c6:
    tst.l 418(a6) ; app+$1A2
    beq.s loc_8530
loc_84cc:
    movem.l d1-d3/a0-a2,-(sp)
    moveq #0,d3
    move.w 536(a6),d3 ; app+$218
    moveq #0,d2
    movea.l 382(a6),a1 ; app+$17E
    move.l a1,d1
    beq.s loc_8520
loc_84e0:
    cmpi.b #$c,13(a1)
    bne.s loc_852c
loc_84e8:
    move.l 152(a1),d2
    tst.b 257(a6) ; app+$101
    bne.s loc_8516
loc_84f2:
    tst.l 2192(a6) ; app+$890
    bne.w loc_8516
loc_84fa:
    move.l 576(a6),d1 ; app+$240
    beq.s loc_852c
loc_8500:
    movea.l d1,a2
    moveq #0,d0
    move.l 340(a6),d1 ; app+$154
loc_8508:
    cmpa.l d1,a2
    beq.s loc_851a
loc_850c:
    cmp.b #$a,d0
    beq.s loc_852c
loc_8512:
    move.b (a2)+,d0
    bra.s loc_8508
loc_8516:
    move.l 158(a1),d1
loc_851a:
    sub.l 8(a1),d1
    subq.l #1,d1
loc_8520:
    movea.l 418(a6),a1 ; app+$1A2
    moveq #0,d0
    movea.l 4(a1),a1
    jsr (a1) ; unresolved_indirect_core:ind
loc_852c:
    movem.l (sp)+,d1-d3/a0-a2
loc_8530:
    bsr.w sub_9292
loc_8534:
    move.w 536(a6),d0 ; app+$218
    beq.s loc_8584
loc_853a:
    cmp.w #$ffff,d0
    beq.s loc_8576
loc_8540:
    moveq #9,d0
    bsr.w sub_8e7a
loc_8546:
    moveq #0,d1
    move.w 536(a6),d1 ; app+$218
    bsr.w sub_8f04
loc_8550:
    tst.l 382(a6) ; app+$17E
    beq.s loc_8576
loc_8556:
    moveq #11,d0
    bsr.w sub_8e7a
loc_855c:
    movea.l 382(a6),a1 ; app+$17E
    moveq #0,d2
    move.b 22(a1),d2
    subq.b #2,d2
    lea 23(a1),a1
loc_856c:
    move.b (a1)+,d1
    bsr.w sub_8e98
loc_8572:
    dbf d2,loc_856c
loc_8576:
    bsr.w sub_8e8c
loc_857a:
    st 258(a6) ; app+$102
    movem.l (sp)+,d1-d3/a0-a3
loc_8582:
    rts
loc_8584:
    moveq #28,d0
    bsr.w sub_8e7a
loc_858a:
    bra.s loc_8576
sign_extended_operand:
    tst.b 568(a6) ; app+$238
    beq.s loc_8582
loc_8592:
    tst.b 261(a6) ; app+$105
    beq.s loc_8582
loc_8598:
    cmpi.b #$5,570(a6) ; app+$23A
    bcc.s loc_85a6
loc_85a0:
    move.b #$5,570(a6) ; app+$23A
loc_85a6:
    move.l a4,340(a6) ; app+$154
    movem.l d1-d3/a0-a3,-(sp)
    move.w d0,-(sp)
    moveq #8,d0
    bsr.w sub_8e7a
loc_85b6:
    lea str_85c2(pc),a0
    move.w #$8000,d2
    bra.w loc_84b8
str_85c2:
    dc.b    "sign extended operand",0
    dc.b    "relative cannot be relocated",0
    dc.b    "invalid LINK displacement",0
    dc.b    "68010 instruction, converted to MOVE SR",0
    dc.b    "size should be .W",0
    dc.b    "directive ignored",0
    dc.b    "misuse of register list",0
    dc.b    "no ORG specified",0
    dc.b    "bit number should be 0-7 for byte",0
    dc.b    "missing ENDC at end of macro",0
    dc.b    "trailing comma at end of DC directive",0
    dc.b    "branch made short",0
    dc.b    "offset removed",0
    dc.b    "short word addressing used",0
    dc.b    "MOVEQ substituted",0
    dc.b    "quick form used",0
    dc.b    "branch could be short",0
    dc.b    "short branch converted to NOP",0
    dc.b    "base displacement shortened",0
    dc.b    "outer displacement shortened",0
    dc.b    "ADD/SUB converted to LEA"
sub_87cc:
    dc.b    $00
    dc.b    "LEA con"
hint_87d4:
; --- unverified ---
    moveq #101,d3
    moveq #116,d1
    bcs.s hint_883e
hint_87da:
; --- unverified ---
    movea.l (16708,a4,d6.l*8),a0
    neg.w (a1)
    move.l (a3),21826(sp)
    subq.b #8,d0
    movea.l a4,sp
    movea.l -(a3),a0
    ble.s loc_885c
hint_87ee:
; --- unverified ---
    moveq #101,d3
    moveq #116,d1
    bcs.s loc_8858
hint_87f4:
    dc.b    " to .W",0
    dc.b    $00,$02,$02,$02,$04,$00,$ff,$00,$02,$02,$00,$02,$02
hint_8808:
    dc.b    $4a,$2e
hint_880e:
; --- unverified ---
    movem.w d0-d1,-(sp)
    subi.w #$c,d0
    move.b -28(pc,d0.w),d0
    bmi.s hint_8826
hint_881c:
    dc.b    $48,$80,$d1,$6e,$01,$94,$52,$6e,$01,$92
hint_8826:
; --- unverified ---
    move.w (sp),d0
    subi.w #$c,d0
    move.w 272(a6),d1 ; app+$110
    btst d0,d1
    movem.w (sp)+,d0-d1
    bne.w sign_extended_operand
hint_883a:
; --- unverified ---
    rts
hint_883c:
; --- unverified ---
    moveq #67,d0
hint_883e:
    bra.w loc_846e
sub_8842:
    movem.l a3-a5,-(sp)
    movea.l 370(a6),a2 ; app+$172
    jsr sub_0b88
loc_8850:
    movem.l (sp)+,a3-a5
    rts
sub_8856:
    tst.b 568(a6) ; app+$238
    bne.w loc_8950
loc_885e:
    bsr.s sub_8842
loc_8860:
    bne.s loc_8880
loc_8862:
    tst.b 308(a6) ; app+$134
    bne.s loc_887c
loc_8868:
    cmpi.b #$d,13(a1)
    beq.s loc_887c
loc_8870:
    tst.w 156(a1)
    bne.w loc_8a02
loc_8878:
    bra.w loc_8958
loc_887c:
    moveq #0,d0
    rts
loc_8880:
    moveq #0,d4
    moveq #11,d3
    moveq #89,d0
    add.l d0,d0
    jsr sub_0d20
loc_888e:
    clr.l 152(a1)
    clr.l 170(a1)
    clr.l 174(a1)
    move.l a1,-(sp)
    bsr.w sub_ae7c
loc_88a0:
    movea.l (sp)+,a1
    bne.w loc_89fe
loc_88a6:
    tst.l d1
    bpl.s loc_88c4
loc_88aa:
    cmp.l #$ffffffff,d1
    beq.s loc_88c4
loc_88b2:
    move.b #$d,13(a1)
    neg.l d1
    jsr sub_fcd6
loc_88c0:
    moveq #0,d0
    rts
loc_88c4:
    move.l d4,152(a1)
    move.l 382(a6),16(a1) ; app+$17E
    move.l a1,382(a6) ; app+$17E
    tst.l d1
    bmi.s loc_8914
loc_88d6:
    addq.l #3,d1
    bclr #0,d1
    move.l #$1200,d2
    bsr.w check_memory
loc_88e6:
    move.l a1,-(sp)
    move.l d1,d3
    bsr.w sub_90ba
loc_88ee:
    movea.l (sp)+,a1
    move.l a0,8(a1)
    move.l d3,166(a1)
    adda.l d3,a0
    move.l a0,162(a1)
    move.l a0,158(a1)
    move.w 536(a6),156(a1) ; app+$218
    clr.w 536(a6) ; app+$218
    st 14(a1)
    bra.w sub_89ba
loc_8914:
    move.b #$c,13(a1)
    movea.l 418(a6),a0 ; app+$1A2
    move.l 8(a0),8(a1)
    move.l 8(a0),158(a1)
    movea.l 12(a0),a2
    cmpi.b #$a,-1(a2)
    beq.s loc_893a
loc_8936:
    move.b #$a,(a2)+
loc_893a:
    move.l a2,162(a1)
    move.w 536(a6),156(a1) ; app+$218
    clr.w 536(a6) ; app+$218
    clr.b 14(a1)
    moveq #0,d0
    rts
loc_8950:
    bsr.w sub_8842
loc_8954:
    bne.w loc_8a02
loc_8958:
    move.b 14(a1),d0
    cmp.b #$fe,d0
    beq.s loc_899a
loc_8962:
    cmpi.b #$d,13(a1)
    beq.s loc_899a
loc_896a:
    move.l 382(a6),16(a1) ; app+$17E
    move.l a1,382(a6) ; app+$17E
    tst.b d0
    beq.s loc_899c
loc_8978:
    move.l a1,-(sp)
    bsr.w sub_ae7c
loc_897e:
    movea.l (sp)+,a1
    bne.w loc_89fe
loc_8984:
    move.l d4,152(a1)
    move.l 8(a1),158(a1)
    move.w 536(a6),156(a1) ; app+$218
    clr.w 536(a6) ; app+$218
    bra.s sub_89ba
loc_899a:
    rts
loc_899c:
    move.l 8(a1),158(a1)
    move.w 536(a6),156(a1) ; app+$218
    clr.w 536(a6) ; app+$218
    moveq #0,d0
    rts
sub_89b0:
    move.l 8(a1),158(a1)
    movea.l a2,a0
    bra.s loc_89c6
sub_89ba:
    movea.l 8(a1),a0
    move.l a0,158(a1)
    move.l 166(a1),d1
loc_89c6:
    move.l 152(a1),d2
    movem.l d1/a0-a1,-(sp)
    bsr.w call_read
loc_89d2:
    movem.l (sp)+,d2/a0-a1
    bne.s loc_89fa
loc_89d8:
    lea 0(a0,d1.l),a2
    cmp.l d1,d2
    beq.s loc_89ee
loc_89e0:
    clr.b (a2)
    cmpi.b #$a,-1(a2)
    beq.s loc_89ee
loc_89ea:
    move.b #$a,(a2)+
loc_89ee:
    move.l a2,162(a1)
    addq.b #1,14(a1)
    moveq #0,d0
    rts
loc_89fa:
    moveq #25,d0
    rts
loc_89fe:
    moveq #26,d0
    rts
loc_8a02:
    moveq #28,d0
    rts
sub_8a06:
    moveq #11,d3
    lea loc_8a0e(pc),a2
    bra.s sub_8a26
loc_8a0e:
    move.l 152(a0),d2
    beq.s loc_8a24
loc_8a14:
    clr.l 152(a0)
    movem.l a0/a2,-(sp)
    bsr.w call_close_afb8
loc_8a20:
    movem.l (sp)+,a0/a2
loc_8a24:
    rts
sub_8a26:
    move.l 370(a6),d0 ; app+$172
    beq.s loc_8a58
loc_8a2c:
    movea.l d0,a0
    move.l (a0),d0
    beq.s loc_8a58
loc_8a32:
    movea.l d0,a0
sub_8a34:
    tst.l (a0)
    beq.s loc_8a40
loc_8a38:
    move.l a0,-(sp)
    movea.l (a0),a0
    bsr.s sub_8a34
loc_8a3e:
    movea.l (sp)+,a0
loc_8a40:
    tst.b d3
    beq.s loc_8a4a
loc_8a44:
    cmp.b 13(a0),d3
    bne.s loc_8a4c
loc_8a4a:
    jsr (a2)
loc_8a4c:
    tst.l 4(a0)
    beq.s loc_8a58
loc_8a52:
    movea.l 4(a0),a0
    bra.s sub_8a34
loc_8a58:
    rts
sub_8a5a:
    lea 1268(a6),a0 ; app+$4F4
    move.l d4,-(sp)
    bsr.w sub_8842
loc_8a64:
    move.l (sp)+,d4
    move.l a1,1402(a6) ; app+$57A
    moveq #0,d3
    lea loc_8a72(pc),a2
    bra.s sub_8a26
loc_8a72:
    move.b 13(a0),d0
    cmp.b #$b,d0
    beq.s loc_8a82
loc_8a7c:
    cmp.b #$c,d0
    bne.s loc_8ad8
loc_8a82:
    move.l a0,-(sp)
    lea 170(a0),a0
loc_8a88:
    move.l (a0),d0
    beq.s loc_8ad6
loc_8a8c:
    movea.l (a0),a0
    move.l 24(a0),d1
    move.l d1,d0
    andi.b #$3,d0
    beq.s loc_8aa0
loc_8a9a:
    andi.b #$fc,d1
    addq.l #4,d1
loc_8aa0:
    move.l d1,24(a0)
    movem.l a0/a2,-(sp)
    bsr.w sub_90ba
loc_8aac:
    movea.l a0,a1
    movem.l (sp)+,a0/a2
    move.l a1,14(a0)
    move.l a1,20(a0)
    move.l #$ffffffff,6(a0)
    clr.l 10(a0)
    lea (a0),a0
    cmpi.w #$3,540(a6) ; app+$21C
    bne.s loc_8a88
loc_8ad0:
    addq.l #1,512(a6) ; app+$200
    bra.s loc_8a88
loc_8ad6:
    movea.l (sp)+,a0
loc_8ad8:
    rts
sub_8ada:
    move.l (a1),d1
    bpl.s loc_8ae2
loc_8ade:
    move.l d0,(a1)
    bra.s loc_8ae6
loc_8ae2:
    move.l d0,(a1)
    sub.l d1,d0
loc_8ae6:
    beq.s loc_8b08
loc_8ae8:
    move.l 24(a0),d1
    addq.l #1,d1
    cmp.l #$80,d0
    bcs.s loc_8b02
loc_8af6:
    addq.l #2,d1
    cmp.l #$8000,d0
    bcs.s loc_8b02
loc_8b00:
    addq.l #4,d1
loc_8b02:
    move.l d1,24(a0)
    rts
loc_8b08:
    move.l 24(a0),d1
    addq.l #7,d1
    bra.s loc_8b02
sub_8b10:
    move.l (a1),d1
    bpl.s loc_8b18
loc_8b14:
    move.l d0,(a1)
    bra.s loc_8b1c
loc_8b18:
    move.l d0,(a1)
    sub.l d1,d0
loc_8b1c:
    movea.l 20(a0),a1
    beq.s loc_8b48
loc_8b22:
    cmp.w #$80,d0
    bcs.s loc_8b44
loc_8b28:
    clr.b (a1)+
    cmp.l #$8000,d0
    bcs.s sub_8b3e
loc_8b32:
    clr.b (a1)+
    clr.b (a1)+
    swap d0
    bsr.w sub_8b3e
loc_8b3c:
    swap d0
sub_8b3e:
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a1)+
loc_8b44:
    move.b d0,(a1)+
    rts
loc_8b48:
    clr.b (a1)+
    bra.s loc_8b32
loc_8b4c:
    movea.l a0,a2
    cmpi.w #$3,540(a6) ; app+$21C
    bne.s loc_8b6a
loc_8b56:
    bsr.w sub_a0f6
loc_8b5a:
    movem.l d2/a0-a2,-(sp)
    bsr.w call_seek_b054
loc_8b62:
    movem.l (sp)+,d2/a0-a2
    move.l d0,28(a2)
loc_8b6a:
    move.l #$3f1,d1
    bsr.w loc_a0ee
loc_8b74:
    bsr.s sub_8bd4
loc_8b76:
    bsr.w loc_a0ee
loc_8b7a:
    moveq #0,d1
    bsr.w loc_a0ee
loc_8b80:
    move.l #$4c494e45,d1 ; 'LINE'
    tst.b 298(a6) ; app+$12A
    beq.s loc_8b92
loc_8b8c:
    move.l #$48434c4e,d1 ; 'HCLN'
loc_8b92:
    bsr.w loc_a0ee
loc_8b96:
    moveq #0,d0
    bsr.w sub_a098
loc_8b9c:
    addq.b #1,22(a1)
    tst.b 298(a6) ; app+$12A
    beq.s loc_8bb0
loc_8ba6:
    moveq #0,d1
    move.w 18(a2),d1
    bsr.w loc_a0ee
loc_8bb0:
    bsr.w sub_a0f6
loc_8bb4:
    movea.l 14(a2),a0
    move.l 24(a2),d1
    movem.l a1-a2,-(sp)
    bsr.w sub_8422
loc_8bc4:
    movem.l (sp)+,a1-a2
    bsr.w sub_a110
loc_8bcc:
    movea.l a2,a0
    lea loc_8b4c(pc),a2
    rts
sub_8bd4:
    moveq #0,d1
    move.b 22(a1),d1
    subq.b #1,d1
    move.b d1,22(a1)
    move.l d1,d0
    andi.b #$3,d0
    beq.s loc_8bee
loc_8be8:
    andi.b #$fc,d1
    addq.l #4,d1
loc_8bee:
    add.l 24(a2),d1
    lsr.l #2,d1
    addq.l #3,d1
    tst.b 298(a6) ; app+$12A
    beq.s loc_8bfe
loc_8bfc:
    addq.l #1,d1
loc_8bfe:
    rts
loc_8c00:
    movea.l a0,a2
    bsr.s sub_8bd4
loc_8c04:
    move.l d1,-(sp)
    addq.l #2,d1
    add.l d1,d1
    add.l d1,d1
    moveq #0,d0
    bsr.w alloc_memory
loc_8c12:
    move.l (sp),d1
    move.l a4,(sp)
    movea.l a0,a4
    move.l #$3f1,(a4)+
    move.l d1,(a4)+
    tst.b 298(a6) ; app+$12A
    beq.s loc_8c64
loc_8c26:
    move.l 8(a3),(a4)+
    move.l #$48434c4e,(a4)+ ; 'HCLN'
    bsr.w sub_9d46
loc_8c34:
    addq.b #1,22(a1)
    moveq #0,d1
    move.w 18(a2),d1
    move.l d1,(a4)+
    movea.l 14(a2),a0
    move.l 24(a2),d1
    lsr.l #2,d1
    subq.l #1,d1
loc_8c4c:
    move.l (a0)+,(a4)+
    dbf d1,loc_8c4c
loc_8c52:
    subi.l #$10000,d1
    bcc.s loc_8c4c
loc_8c5a:
    movea.l (sp)+,a4
    movea.l a2,a0
    lea loc_8c00(pc),a2
    rts
loc_8c64:
    clr.l (a4)+
    move.l #$4c494e45,(a4)+ ; 'LINE'
    bsr.w sub_9d46
loc_8c70:
    addq.b #1,22(a1)
    movea.l 14(a2),a0
    move.l 24(a2),d1
    lsr.l #3,d1
    subq.l #1,d1
    move.l 8(a3),d2
loc_8c84:
    move.l (a0)+,(a4)+
    move.l (a0)+,d0
    add.l d2,d0
    move.l d0,(a4)+
    dbf d1,loc_8c84
loc_8c90:
    subi.l #$10000,d1
    bcc.s loc_8c84
loc_8c98:
    bra.s loc_8c5a
sub_8c9a:
    movea.l 1402(a6),a0 ; app+$57A
    bsr.w sub_8cdc
loc_8ca2:
    movea.l 370(a6),a0 ; app+$172
    movea.l (a0),a0
sub_8ca8:
    tst.l (a0)
    beq.s loc_8cb4
loc_8cac:
    move.l a0,-(sp)
    movea.l (a0),a0
    bsr.s sub_8ca8
loc_8cb2:
    movea.l (sp)+,a0
loc_8cb4:
    move.b 13(a0),d0
    cmp.b #$b,d0
    beq.s loc_8cc4
loc_8cbe:
    cmp.b #$c,d0
    bne.s loc_8cce
loc_8cc4:
    cmpa.l 1402(a6),a0 ; app+$57A
    beq.s loc_8cce
loc_8cca:
    bsr.w sub_8cdc
loc_8cce:
    tst.l 4(a0)
    beq.s loc_8cda
loc_8cd4:
    movea.l 4(a0),a0
    bra.s sub_8ca8
loc_8cda:
    rts
sub_8cdc:
    movea.l a0,a1
    move.l 170(a1),d0
loc_8ce2:
    beq.s loc_8cf2
loc_8ce4:
    movea.l d0,a0
    cmp.b 4(a0),d6
    beq.s loc_8cf0
loc_8cec:
    move.l (a0),d0
    bra.s loc_8ce2
loc_8cf0:
    jsr (a2)
loc_8cf2:
    movea.l a1,a0
    rts
sub_8cf6:
    tst.l 16(a1)
    beq.s loc_8d1a
loc_8cfc:
    movea.l 16(a1),a1
sub_8d00:
    tst.l (a1)
    beq.s loc_8d0c
loc_8d04:
    move.l a1,-(sp)
    movea.l (a1),a1
    bsr.s sub_8d00
loc_8d0a:
    movea.l (sp)+,a1
loc_8d0c:
    jsr (a2)
loc_8d0e:
    tst.l 4(a1)
    beq.s loc_8d1a
loc_8d14:
    movea.l 4(a1),a1
    bra.s sub_8d00
loc_8d1a:
    rts
sub_8d1c:
    move.l a3,-(sp)
    movea.l a2,a3
    lea loc_8d36(pc),a2
    bsr.s sub_8cf6
loc_8d26:
    movea.l 362(a6),a1 ; app+$16A
    tst.l (a1)
    beq.s loc_8d32
loc_8d2e:
    movea.l (a1),a1
    bsr.s sub_8d00
loc_8d32:
    movea.l (sp)+,a3
    rts
loc_8d36:
    btst #5,12(a1)
    beq.s loc_8d46
loc_8d3e:
    cmp.b 14(a1),d6
    bne.s loc_8d46
loc_8d44:
    jsr (a3)
loc_8d46:
    rts
sub_8d48:
    tst.l 16(a1)
    beq.s loc_8d6c
loc_8d4e:
    movea.l 16(a1),a1
sub_8d52:
    tst.l (a1)
    beq.s loc_8d5e
loc_8d56:
    move.l a1,-(sp)
    movea.l (a1),a1
    bsr.s sub_8d52
loc_8d5c:
    movea.l (sp)+,a1
loc_8d5e:
    bsr.s sub_8d6e
loc_8d60:
    tst.l 4(a1)
    beq.s loc_8d6c
loc_8d66:
    movea.l 4(a1),a1
    bra.s sub_8d52
loc_8d6c:
    rts
sub_8d6e:
    btst #4,12(a1)
    beq.s loc_8d80
loc_8d76:
    btst #2,12(a1)
    bne.s loc_8d80
loc_8d7e:
    jsr (a2)
loc_8d80:
    rts
sub_8d82:
    tst.b 568(a6) ; app+$238
    bne.s loc_8da0
loc_8d88:
    move.l #$196,d1
    bsr.w sub_90ba
loc_8d92:
    move.l a0,2376(a6) ; app+$948
    move.l a0,2380(a6) ; app+$94C
    clr.l (a0)+
    clr.w (a0)
    rts
loc_8da0:
    movea.l 2380(a6),a0 ; app+$94C
    move.w 4(a0),d0
    lea 6(a0,d0.w),a0
    move.l a0,2384(a6) ; app+$950
    movea.l 2376(a6),a0 ; app+$948
    move.l a0,2380(a6) ; app+$94C
    moveq #-1,d0
    tst.w 4(a0)
    beq.s loc_8dc8
loc_8dc0:
    clr.w 4(a0)
    move.l 6(a0),d0
loc_8dc8:
    move.l d0,2372(a6) ; app+$944
    rts
sub_8dce:
; --- unverified ---
    move.l a5,d0
    sub.l 588(a6),d0 ; app+$24C
    add.l 548(a6),d0 ; app+$224
    tst.b 568(a6) ; app+$238
    bne.s hint_8e22
hint_8dde:
; --- unverified ---
    move.l d0,-(sp)
    movea.l 2380(a6),a0 ; app+$94C
    addq.l #4,a0
    move.w (a0)+,d0
    cmp.w #$190,d0
    beq.s hint_8dfe
hint_8dee:
; --- unverified ---
    move.l (sp)+,0(a0,d0.w)
    move.l d2,4(a0,d0.w)
    addq.w #8,d0
    move.w d0,-(a0)
    moveq #0,d0
    rts
hint_8dfe:
; --- unverified ---
    movem.l d1-d2/a1-a2,-(sp)
    move.l #$196,d1
    bsr.w sub_90ba
hint_8e0c:
; --- unverified ---
    movea.l 2380(a6),a1 ; app+$94C
    move.l a0,(a1)
    move.l a0,2380(a6) ; app+$94C
    clr.l (a0)+
    clr.w (a0)+
    moveq #0,d0
    movem.l (sp)+,d1-d2/a1-a2
    bra.s hint_8dee
hint_8e22:
; --- unverified ---
    cmp.l 2372(a6),d0 ; app+$944
    bne.s hint_8e5a
hint_8e28:
; --- unverified ---
    movea.l 2380(a6),a0 ; app+$94C
    addq.l #4,a0
    move.w (a0)+,d0
    cmp.l 4(a0,d0.w),d2
    beq.s hint_8e40
hint_8e36:
; --- unverified ---
    move.w d0,-(sp)
    moveq #65,d0
    bsr.w loc_8486
hint_8e3e:
    dc.b    $30,$1f
hint_8e40:
; --- unverified ---
    addq.w #8,d0
    cmp.w #$190,d0
    beq.s hint_8e5c
hint_8e48:
; --- unverified ---
    move.w d0,-2(a0)
    adda.w d0,a0
    cmpa.l 2384(a6),a0 ; app+$950
    beq.s hint_8e70
hint_8e54:
    dc.b    "-P",$09,"Dp",0
hint_8e5a:
; --- unverified ---
    rts
hint_8e5c:
; --- unverified ---
    movea.l 2380(a6),a0 ; app+$94C
    tst.l (a0)
    beq.s hint_8e70
hint_8e64:
; --- unverified ---
    movea.l (a0),a0
    move.l a0,2380(a6) ; app+$94C
    addq.w #6,a0
    moveq #0,d0
    bra.s hint_8e48
hint_8e70:
; --- unverified ---
    moveq #-1,d0
    move.l d0,2372(a6) ; app+$944
    moveq #0,d0
    rts
sub_8e7a:
    lea pcref_93fe(pc),a0
    tst.w d0
loc_8e80:
    beq.w sub_9292
loc_8e84:
    tst.b (a0)+
    bne.s loc_8e84
loc_8e88:
    subq.w #1,d0
    bra.s loc_8e80
sub_8e8c:
    moveq #10,d1
    bra.w loc_9288
sub_8e92:
    bsr.w sub_8e96
sub_8e96:
    moveq #32,d1
sub_8e98:
    movem.l d0-d2/a0-a2,-(sp)
    bsr.w loc_9288
loc_8ea0:
    movem.l (sp)+,d0-d2/a0-a2
    rts
sub_8ea6:
    move.w d1,-(sp)
    swap d1
    bsr.s sub_8eae
loc_8eac:
    move.w (sp)+,d1
sub_8eae:
    move.w d1,-(sp)
    lsr.w #8,d1
    bsr.s sub_8eb6
loc_8eb4:
    move.w (sp)+,d1
sub_8eb6:
    move.w d1,-(sp)
    lsr.w #4,d1
    bsr.s sub_8ebe
loc_8ebc:
    move.w (sp)+,d1
sub_8ebe:
    andi.w #$f,d1
    move.b pcref_8ec8(pc,d1.w),d1
    bra.s sub_8e98
pcref_8ec8:
    dc.b    "0123456789ABCDEF"
sub_8ed8:
    moveq #6,d3
    moveq #0,d2
loc_8edc:
    rol.l #4,d1
    move.l d1,-(sp)
    andi.w #$f,d1
    bne.s loc_8eea
loc_8ee6:
    tst.b d2
    beq.s loc_8ef2
loc_8eea:
    st d2
    move.b pcref_8ec8(pc,d1.w),d1
    jsr (a2)
loc_8ef2:
    move.l (sp)+,d1
    dbf d3,loc_8edc
loc_8ef8:
    rol.l #4,d1
    andi.w #$f,d1
    move.b pcref_8ec8(pc,d1.w),d1
    jmp (a2)
sub_8f04:
    lea sub_8e98(pc),a2
sub_8f08:
    lea pcref_8f3c(pc),a0
    moveq #1,d2
    moveq #8,d0
loc_8f10:
    moveq #0,d3
    cmp.l (a0)+,d1
    bcs.s loc_8f22
loc_8f16:
    sub.l -(a0),d1
loc_8f18:
    addq.b #1,d3
    sub.l (a0),d1
    bcc.s loc_8f18
loc_8f1e:
    add.l (a0)+,d1
    bra.s loc_8f26
loc_8f22:
    tst.b d2
    bpl.s loc_8f32
loc_8f26:
    st d2
    addi.b #$30,d3
    exg
    jsr (a2)
loc_8f30:
    exg
loc_8f32:
    dbf d0,loc_8f10
loc_8f36:
    addi.b #$30,d1
    jmp (a2)
pcref_8f3c:
    dc.b    $3b,$9a,$ca,$00,$05,$f5,$e1,$00,$00,$98,$96,$80,$00,$0f,$42,$40
    dc.b    $00,$01,$86,$a0,$00,$00,$27,$10,$00,$00,$03,$e8,$00,$00,$00,$64
    dc.b    $00,$00,$00,$0a
sub_8f60:
    moveq #20,d0
    bsr.w sub_8e7a
loc_8f66:
    movea.l 362(a6),a2 ; app+$16A
    lea loc_8f90(pc),a4
    bsr.w loc_8fd2
loc_8f72:
    moveq #9,d3
    lea loc_8f98(pc),a2
    lea sub_8f80(pc),a4
    bra.w sub_8a26
sub_8f80:
; --- unverified ---
    cmpi.b #$2,13(a3)
    beq.s loc_8f90
hint_8f88:
; --- unverified ---
    move.b 14(a3),d0
    bra.w loc_9786
loc_8f90:
    bsr.w sub_8e96
loc_8f94:
    bra.w sub_8e92
loc_8f98:
    movem.l d3/a0/a2,-(sp)
    move.l a0,-(sp)
    moveq #21,d0
    bsr.w sub_8e7a
loc_8fa4:
    movea.l (sp),a0
    lea 22(a0),a0
    move.b (a0)+,d2
loc_8fac:
    move.b (a0)+,d1
    bsr.w sub_8e98
loc_8fb2:
    subq.b #1,d2
    bgt.s loc_8fac
loc_8fb6:
    bsr.w sub_8e8c
loc_8fba:
    bsr.w sub_8e8c
loc_8fbe:
    movea.l (sp)+,a0
    lea 16(a0),a2
    bsr.s loc_8fd2
loc_8fc6:
    movem.l (sp)+,d3/a0/a2
    rts
dos_dispatch:
    jmp loc_06a4
loc_8fd2:
    move.l a2,d0
    beq.s loc_904c
loc_8fd6:
    move.l (a2),d0
    beq.s loc_904c
loc_8fda:
    movea.l d0,a2
    suba.l a3,a3
    lea 1470(a6),a0 ; app+$5BE
    moveq #127,d0
    move.b d0,(a0)+
loc_8fe6:
    st (a0)+
    dbf d0,loc_8fe6
loc_8fec:
    tst.b 277(a6) ; app+$115
    bgt.s dos_dispatch
loc_8ff2:
    lea 1448(a6),a3 ; app+$5A8
    move.b 23(a3),d3
    bsr.s sub_904e
loc_8ffc:
    lea 1448(a6),a0 ; app+$5A8
    cmpa.l a3,a0
    beq.s loc_904c
loc_9004:
    bset #0,12(a3)
    btst #4,12(a3)
    bne.s loc_8fec
loc_9012:
    move.l 8(a3),d1
    bsr.w sub_8ea6
loc_901a:
    bsr.w sub_8e92
loc_901e:
    jsr (a4)
loc_9020:
    moveq #0,d1
    move.b 13(a3),d1
    lea str_909a(pc),a0
    move.b 0(a0,d1.w),d1
    bsr.w sub_8e98
loc_9032:
    bsr.w sub_8e92
loc_9036:
    lea 22(a3),a0
    move.b (a0)+,d4
loc_903c:
    move.b (a0)+,d1
    bsr.w sub_8e98
loc_9042:
    subq.b #1,d4
    bne.s loc_903c
loc_9046:
    bsr.w sub_8e8c
loc_904a:
    bra.s loc_8fec
loc_904c:
    rts
sub_904e:
    tst.l (a2)
    beq.s loc_905a
loc_9052:
    move.l a2,-(sp)
    movea.l (a2),a2
    bsr.s sub_904e
loc_9058:
    movea.l (sp)+,a2
loc_905a:
    btst #0,12(a2)
    bne.s loc_9088
loc_9062:
    cmp.b 23(a2),d3
    bcs.s loc_9088
loc_9068:
    lea 22(a3),a0
    lea 22(a2),a1
    move.b (a0)+,d0
    move.b (a1)+,d1
loc_9074:
    cmpm.b (a1)+,(a0)+
    bcs.s loc_9088
loc_9078:
    bne.s loc_9082
loc_907a:
    subq.b #1,d0
    beq.s loc_9088
loc_907e:
    subq.b #1,d1
    bne.s loc_9074
loc_9082:
    movea.l a2,a3
    move.b 23(a3),d3
loc_9088:
    tst.l 4(a2)
    beq.s loc_9098
loc_908e:
    move.l a2,-(sp)
    movea.l 4(a2),a2
    bsr.s sub_904e
loc_9096:
    movea.l (sp)+,a2
loc_9098:
    rts
str_909a:
    dc.b    "?RA?rl??????O",0
sub_90a8:
    move.l #$2800,d1
    move.w d1,328(a6) ; app+$148
    bsr.s sub_90ba
loc_90b4:
    move.l a0,314(a6) ; app+$13A
    rts
sub_90ba:
    addq.l #4,d1
    bsr.w alloc_memory_ae42
loc_90c0:
    beq.s loc_90ec
loc_90c2:
    move.l 310(a6),(a0) ; app+$136
    move.l a0,310(a6) ; app+$136
    addq.w #4,a0
    rts
hint_90ce:
    dc.b    $59,$48,$43,$ee,$01,$36
hint_90d4:
; --- unverified ---
    move.l (a1),d0
    beq.s hint_90e6
hint_90d8:
; --- unverified ---
    cmpa.l d0,a0
    beq.s hint_90e0
hint_90dc:
; --- unverified ---
    movea.l d0,a1
    bra.s hint_90d4
hint_90e0:
; --- unverified ---
    move.l (a0),(a1)
    bra.w free_memory
hint_90e6:
; --- unverified ---
    moveq #105,d0
    bra.w loc_846e
loc_90ec:
    moveq #2,d0
    bra.w loc_846e
sub_90f2:
    movea.l 310(a6),a0 ; app+$136
    bra.s loc_9100
loc_90f8:
    move.l (a0),-(sp)
    bsr.w free_memory
loc_90fe:
    movea.l (sp)+,a0
loc_9100:
    move.l a0,d0
    bne.s loc_90f8
loc_9104:
    rts
sub_9106:
    sf 2388(a6) ; app+$954
    sf 2389(a6) ; app+$955
    clr.l app_open_file(a6)
    lea 2394(a6),a0 ; app+$95A
    lea 2906(a6),a1 ; app+$B5A
    move.l a0,(a1)
    move.l a1,2910(a6) ; app+$B5E
    move.w #$84,2914(a6) ; app+$B62
    move.w #$3c,2916(a6) ; app+$B64
    clr.w 2918(a6) ; app+$B66
    move.w #$ffff,2920(a6) ; app+$B68
    clr.w 2922(a6) ; app+$B6A
    clr.b 2946(a6) ; app+$B82
    clr.b 3027(a6) ; app+$BD3
    st 3108(a6) ; app+$C24
    move.w #$8,2924(a6) ; app+$B6C
    lea 2926(a6),a3 ; app+$B6E
    bsr.w call_datestamp
loc_9154:
    clr.b (a3)
    rts
sub_9158:
    tst.l app_open_file(a6)
    beq.s loc_9168
loc_915e:
    bsr.w sub_ab56
loc_9162:
    bsr.w sub_919e
loc_9166:
    bsr.s sub_916a
loc_9168:
    rts
sub_916a:
    tst.l app_open_file(a6)
    beq.s loc_9168
loc_9170:
    move.l app_open_file(a6),d3
    clr.l app_open_file(a6)
    bra.w loc_a900
sub_917c:
    movea.l 2906(a6),a0 ; app+$B5A
    cmpa.l 2910(a6),a0 ; app+$B5E
    beq.s loc_918e
loc_9186:
    move.b d1,(a0)+
    move.l a0,2906(a6) ; app+$B5A
    rts
loc_918e:
    move.w d1,-(sp)
    bsr.s sub_919e
loc_9192:
    bne.s loc_9198
loc_9194:
    move.w (sp)+,d1
    bra.s sub_917c
loc_9198:
    moveq #74,d0
    bra.w loc_846e
sub_919e:
    move.l d3,-(sp)
    move.l app_open_file(a6),d3
    lea 2394(a6),a0 ; app+$95A
    move.l 2906(a6),d1 ; app+$B5A
    sub.l a0,d1
    beq.s loc_91bc
loc_91b0:
    lea 2394(a6),a1 ; app+$95A
    move.l a1,2906(a6) ; app+$B5A
    bsr.w call_write
loc_91bc:
    movem.l (sp)+,d3
    rts
sub_91c2:
    btst #0,3108(a6) ; app+$C24
    bne.s loc_91cc
loc_91ca:
    rts
loc_91cc:
    addq.w #1,2922(a6) ; app+$B6A
    moveq #16,d0
    bsr.w sub_8e7a
loc_91d6:
    lea 2926(a6),a0 ; app+$B6E
    bsr.w sub_9292
loc_91de:
    moveq #15,d0
    bsr.w sub_8e7a
loc_91e4:
    moveq #0,d1
    move.w 2922(a6),d1 ; app+$B6A
    move.l d3,-(sp)
    bsr.w sub_8f04
loc_91f0:
    move.l (sp)+,d3
    bsr.w sub_8e8c
loc_91f6:
    lea 2946(a6),a0 ; app+$B82
    tst.b (a0)
    beq.s loc_9204
loc_91fe:
    bsr.w sub_9292
loc_9202:
    bra.s loc_9224
loc_9204:
    tst.l 382(a6) ; app+$17E
    beq.s loc_9224
loc_920a:
    movea.l 382(a6),a1 ; app+$17E
    moveq #0,d2
    move.b 22(a1),d2
    subq.b #2,d2
    lea 23(a1),a1
loc_921a:
    move.b (a1)+,d1
    bsr.w sub_8e98
loc_9220:
    dbf d2,loc_921a
loc_9224:
    bsr.w sub_8e8c
loc_9228:
    lea 3027(a6),a0 ; app+$BD3
    bsr.w sub_9292
loc_9230:
    bsr.w sub_8e8c
loc_9234:
    bra.w sub_8e8c
sub_9238:
    tst.w 2920(a6) ; app+$B68
    bpl.s loc_924a
loc_923e:
    clr.w 2920(a6) ; app+$B68
    move.w d1,-(sp)
    bsr.w sub_91c2
loc_9248:
    move.w (sp)+,d1
loc_924a:
    cmp.b #$a,d1
    bne.s loc_926c
sub_9250:
    clr.w 2918(a6) ; app+$B66
    move.w 2920(a6),d0 ; app+$B68
    addq.w #1,2920(a6) ; app+$B68
    cmp.w 2916(a6),d0 ; app+$B64
    beq.w sub_ab56
loc_9264:
    moveq #10,d1
    bsr.w sub_917c
loc_926a:
    rts
loc_926c:
    move.w 2918(a6),d0 ; app+$B66
    cmp.w 2914(a6),d0 ; app+$B62
    blt.s loc_927e
loc_9276:
    move.w d1,-(sp)
    bsr.s sub_9250
loc_927a:
    move.w (sp)+,d1
    bra.s sub_9238
loc_927e:
    bsr.w sub_917c
loc_9282:
    addq.w #1,2918(a6) ; app+$B66
    rts
loc_9288:
    tst.b 2389(a6) ; app+$955
    bne.s sub_9238
loc_928e:
    bra.w sub_a89e
sub_9292:
    move.b (a0)+,d1
    beq.s loc_929e
loc_9296:
    move.l a0,-(sp)
    bsr.s loc_9288
loc_929a:
    movea.l (sp)+,a0
    bra.s sub_9292
loc_929e:
    rts
sub_92a0:
    movem.l d7/a3,-(sp)
    move.b 3108(a6),d7 ; app+$C24
    add.b d7,d7
    bcc.s loc_92e4
loc_92ac:
    move.w 536(a6),d2 ; app+$218
    cmp.w #$2710,d2
    bcc.s loc_92d8
loc_92b6:
    bsr.w sub_8e96
loc_92ba:
    cmp.w #$3e8,d2
    bcc.s loc_92d8
loc_92c0:
    bsr.w sub_8e96
loc_92c4:
    cmp.w #$64,d2
    bcc.s loc_92d8
loc_92ca:
    bsr.w sub_8e96
loc_92ce:
    cmp.w #$a,d2
    bcc.s loc_92d8
loc_92d4:
    bsr.w sub_8e96
loc_92d8:
    moveq #0,d1
    move.w d2,d1
    bsr.w sub_8f04
loc_92e0:
    bsr.w sub_8e96
loc_92e4:
    move.l 386(a6),d4 ; app+$182
    add.b d7,d7
    bcc.s loc_932e
loc_92ec:
    move.b 326(a6),d0 ; app+$146
    move.b 2107(a6),d1 ; app+$83B
    beq.s loc_9318
loc_92f6:
    cmp.b #$ff,d1
    beq.s loc_9312
loc_92fc:
    bsr.w sub_8e92
loc_9300:
    move.b 2107(a6),d1 ; app+$83B
    bsr.s loc_9288
loc_9306:
    move.l 2108(a6),d1 ; app+$83C
    bsr.w sub_8ea6
loc_930e:
    moveq #0,d4
    bra.s loc_932e
loc_9312:
    bsr.w sub_9780
loc_9316:
    bra.s loc_9306
loc_9318:
    bsr.w sub_9780
loc_931c:
    move.l 386(a6),d4 ; app+$182
    movea.l 592(a6),a3 ; app+$250
    move.l 572(a6),d1 ; app+$23C
    sub.l d4,d1
    bsr.w sub_8ea6
loc_932e:
    moveq #32,d1
    tst.b 257(a6) ; app+$101
    beq.s loc_933e
loc_9336:
    tst.b 280(a6) ; app+$118
    bne.s loc_933e
loc_933c:
    moveq #43,d1
loc_933e:
    bsr.w loc_9288
loc_9342:
    add.b d7,d7
    bcc.s loc_936c
loc_9346:
    moveq #5,d3
    cmpi.w #$51,2914(a6) ; app+$B62
    bcs.s loc_9352
loc_9350:
    moveq #9,d3
loc_9352:
    tst.l d4
loc_9354:
    beq.s loc_9364
loc_9356:
    move.b (a3)+,d1
    bsr.w sub_8eb6
loc_935c:
    subq.l #1,d4
    dbf d3,loc_9354
loc_9362:
    bra.s loc_936c
loc_9364:
    bsr.w sub_8e92
loc_9368:
    dbf d3,loc_9364
loc_936c:
    bsr.w sub_8e96
loc_9370:
    movea.l 576(a6),a3 ; app+$240
    moveq #0,d2
    moveq #0,d3
    tst.b 269(a6) ; app+$10D
    beq.s loc_9388
loc_937e:
    tst.b 2389(a6) ; app+$955
    bne.s loc_9388
loc_9384:
    move.l 340(a6),d3 ; app+$154
loc_9388:
    move.b (a3)+,d1
    cmp.l a3,d3
    bne.s loc_93c4
loc_938e:
    movem.l d0-d2/a0-a2,-(sp)
    cmp.b #$a,d1
    beq.s loc_939e
loc_9398:
    cmp.b #$9,d1
    bne.s loc_93a0
loc_939e:
    moveq #32,d1
loc_93a0:
    tst.b 296(a6) ; app+$128
    bne.s loc_93ac
loc_93a6:
    bsr.w sub_a8c4
loc_93aa:
    bra.s loc_93b0
loc_93ac:
    bsr.w sub_a89e
loc_93b0:
    movem.l (sp)+,d0-d2/a0-a2
    cmp.b #$a,d1
    beq.s loc_93f4
loc_93ba:
    cmp.b #$9,d1
    beq.s loc_93c4
loc_93c0:
    addq.w #1,d2
    bra.s loc_9388
loc_93c4:
    cmp.b #$a,d1
    beq.s loc_93f4
loc_93ca:
    cmp.b #$9,d1
    bne.s loc_93ec
loc_93d0:
    moveq #0,d0
    move.w d2,d0
    divu.w 2924(a6),d0 ; app+$B6C
    swap d0
    sub.w 2924(a6),d0 ; app+$B6C
    neg.w d0
loc_93e0:
    bsr.w sub_8e96
loc_93e4:
    addq.w #1,d2
    subq.w #1,d0
    bne.s loc_93e0
loc_93ea:
    bra.s loc_9388
loc_93ec:
    addq.w #1,d2
    bsr.w sub_8e98
loc_93f2:
    bra.s loc_9388
loc_93f4:
    bsr.w loc_9288
loc_93f8:
    movem.l (sp)+,d7/a3
    rts
pcref_93fe:
    dc.b    "GenAm Macro Assembler Copyright "
    dc.b    $a9
    dc.b    " HiSoft 1985-1997"
    dc.b    $0a
    dc.b    "All Rights Reserved - version 3.18"
    dc.b    $0a,$0a,$00
    dc.b    "Pass 1"
    dc.b    $0a,$00
    dc.b    "Pass 2"
    dc.b    $0a,$00
    dc.b    " errors found"
    dc.b    $0a,$00
    dc.b    " error found"
    dc.b    $0a,$00
    dc.b    " lines assembled into ",0
    dc.b    "Error: ",0
    dc.b    "Locals:"
    dc.b    $0a,$00
    dc.b    "Warning: ",0
    dc.b    " at line ",0
    dc.b    "Could not open file ",0
    dc.b    " in file ",0
    dc.b    " bytes, ",0
    dc.b    " optimisations saving ",0
    dc.b    " bytes"
    dc.b    $0a,$00
    dc.b    "  Page ",0
    dc.b    "HiSoft GenAm 680x0 Macro Assembler v3.18   ",0
    dc.b    " relocatable",0
    dc.b    " position-independent",0
    dc.b    $20,$63,$6f,$64,$65,$0a,$00,$0a,$09
    dc.b    "GLOBAL SYMBOLS"
    dc.b    $0a,$0a,$00,$0a,$09
    dc.b    "MODULE ",0
    dc.b    " absolute",0
    dc.b    "Bad arguments"
    dc.b    $0a,$00
    dc.b    "Error in WITH file",0
    dc.b    "WITH file not found",0
    dc.b    "Could not open listing device"
    dc.b    $0a,$00
    dc.b    "Assembling ",0
    dc.b    " in assembly options",0
    dc.b    "Main file already included in header file"
    dc.b    $0a,$00
gen_symbol:
    pea sub_9292(pc)
    tst.b 265(a6) ; app+$109
    beq.s loc_963c
loc_9636:
    lea str_965a(pc),a0
    rts
loc_963c:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f9aa
loc_9646:
    bra.w loc_a396
sub_964a:
    tst.b 265(a6) ; app+$109
    beq.s loc_9666
loc_9650:
    lea str_9656(pc),a0
    rts
str_9656:
    dc.b    $2e,$67,$73,$00
str_965a:
    dc.b    "Gen symbol",0
    dc.b    $00
loc_9666:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f9b0
loc_9670:
    bra.w loc_a3a8
hint_9674:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w hint_f9d2
hint_967e:
; --- unverified ---
    bra.w hint_a3de
sub_9682:
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s loc_9690
loc_968a:
    tst.l 410(a6) ; app+$19A
    bne.s loc_969e
loc_9690:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f954
loc_969a:
    bra.w loc_9bc6
loc_969e:
    moveq #66,d0
    bra.w loc_846e
loc_96a4:
    tst.b 259(a6) ; app+$103
    beq.s loc_96bc
loc_96aa:
    movea.l 318(a6),a1 ; app+$13E
    btst #2,541(a6) ; app+$21D
    bne.w loc_f82e
loc_96b8:
    bra.w loc_9a2c
loc_96bc:
    rts
loc_96be:
    tst.b 259(a6) ; app+$103
    beq.s loc_96bc
loc_96c4:
    movea.l 318(a6),a1 ; app+$13E
    btst #2,541(a6) ; app+$21D
    bne.w loc_f82e
loc_96d2:
    bra.w loc_9a2c
loc_96d6:
    tst.b 259(a6) ; app+$103
    beq.s loc_96ea
loc_96dc:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f830
loc_96e6:
    bra.w loc_9a2e
loc_96ea:
    rts
hint_96ec:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s loc_96ea
hint_96f2:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w loc_f82e
hint_96fc:
; --- unverified ---
    bra.w loc_9a2c
sub_9700:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f830
loc_970a:
    bra.w loc_9a2e
loc_970e:
    tst.b 283(a6) ; app+$11B
    bne.s loc_9728
loc_9714:
    tst.b 259(a6) ; app+$103
    beq.s loc_96ea
loc_971a:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f868
loc_9724:
    bra.w loc_9a90
loc_9728:
    moveq #38,d0
    bra.w loc_8486
sub_972e:
    cmpi.b #$ff,283(a6) ; app+$11B
    beq.s loc_9744
loc_9736:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f982
loc_9740:
    bra.w loc_9c38
loc_9744:
    rts
sub_9746:
    move.l 572(a6),d2 ; app+$23C
    moveq #1,d1
    clr.b (a5)+
    add.l d1,572(a6) ; app+$23C
    add.l d1,548(a6) ; app+$224
    tst.b 568(a6) ; app+$238
    beq.s loc_9768
loc_975c:
    tst.b 259(a6) ; app+$103
    beq.s loc_9768
loc_9762:
    bsr.s sub_972e
loc_9764:
    beq.s loc_9768
loc_9766:
    bsr.s loc_970e
loc_9768:
    movea.l 588(a6),a5 ; app+$24C
    move.l a5,592(a6) ; app+$250
    rts
sub_9772:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w hint_9a62
hint_977c:
; --- unverified ---
    bra.w hint_9a54
sub_9780:
    tst.b 283(a6) ; app+$11B
    bne.s loc_9794
loc_9786:
    btst #2,541(a6) ; app+$21D
    bne.w loc_9c2a
loc_9790:
    bra.w loc_9c2a
loc_9794:
    moveq #79,d1
    bsr.w loc_9288
loc_979a:
    bra.w sub_8e92
sub_979e:
    moveq #40,d0
    jmp loc_846e
loc_97a6:
    tst.l 390(a6) ; app+$186
    bne.s loc_97c2
loc_97ac:
    movem.l d1-d2/a0-a2,-(sp)
    lea 1736(a6),a0 ; app+$6C8
    bsr.w sub_97c4
loc_97b8:
    bne.s sub_979e
loc_97ba:
    move.l d2,390(a6) ; app+$186
    movem.l (sp)+,d1-d2/a0-a2
loc_97c2:
    rts
sub_97c4:
    lea 1818(a6),a1 ; app+$71A
    move.b (a0),d0
    beq.s loc_97e4
loc_97cc:
    cmp.b #$2e,d0
    bne.s loc_9826
loc_97d2:
    move.b 1(a0),d0
    cmp.b #$2e,d0
    beq.s loc_9826
loc_97dc:
    cmp.b #$5c,d0
    beq.s loc_9826
loc_97e2:
    move.b (a0),d0
loc_97e4:
    move.l a1,d2
loc_97e6:
    tst.b (a1)+
    bne.s loc_97e6
loc_97ea:
    sub.l a1,d2
    neg.l d2
    tst.b d0
    bne.s loc_97f6
loc_97f2:
    bsr.w sub_964a
loc_97f6:
    subq.l #1,a1
    subq.b #1,d2
    bsr.w sub_9812
loc_97fe:
    bsr.w call_open
loc_9802:
    lea 1818(a6),a0 ; app+$71A
    rts
sub_9808:
    lea 1736(a6),a0 ; app+$6C8
    lea 1818(a6),a1 ; app+$71A
    moveq #0,d2
sub_9812:
    cmp.b #$52,d2
    beq.s loc_9820
loc_9818:
    addq.b #1,d2
    move.b (a0)+,d1
    move.b d1,(a1)+
    bne.s sub_9812
loc_9820:
    lea 1818(a6),a0 ; app+$71A
    rts
loc_9826:
    tst.b (a0)+
    bne.s loc_9826
loc_982a:
    move.b -2(a0),d0
    cmp.b #$2f,d0
    beq.s loc_9856
loc_9834:
    cmp.b #$3a,d0
    beq.s loc_9856
loc_983a:
    lea 1736(a6),a0 ; app+$6C8
    bsr.w call_open
loc_9842:
    beq.w loc_985e
loc_9846:
    bsr.s sub_9808
loc_9848:
    move.b #$2f,-1(a1)
loc_984e:
    lea 1900(a6),a0 ; app+$76C
    bsr.s sub_9812
loc_9854:
    bra.s loc_97f2
loc_9856:
    bsr.s sub_9808
loc_9858:
    subq.w #1,a1
    subq.b #1,d2
    bra.s loc_984e
loc_985e:
    lea 1736(a6),a0 ; app+$6C8
    rts
loc_9864:
    lea pcref_9884(pc),a0
    move.l a0,378(a6) ; app+$17A
    move.l 588(a6),d1 ; app+$24C
    tst.b 283(a6) ; app+$11B
    bne.s loc_9888
loc_9876:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f92c
loc_9880:
    bra.w loc_9b40
pcref_9884:
    dc.b    $42,$ae,$01,$82
loc_9888:
    rts
loc_988a:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f892
loc_9894:
    bra.w loc_9aa4
sub_9898:
    tst.b 259(a6) ; app+$103
    beq.s loc_98ac
loc_989e:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f992
loc_98a8:
    bra.w loc_9da6
loc_98ac:
    rts
sub_98ae:
    move.l 390(a6),d2 ; app+$186
    beq.s loc_98bc
loc_98b4:
    bsr.w call_close_afb8
loc_98b8:
    clr.l 390(a6) ; app+$186
loc_98bc:
    rts
sub_98be:
    dc.b    $2f,$02
hint_98c0:
; --- unverified ---
    move.l #$113e,d0
    sub.l d0,d1
    bcc.s hint_98ce
hint_98ca:
    dc.b    $d0,$81,$72,$00
hint_98ce:
; --- unverified ---
    movea.l a6,a0
    move.l d1,-(sp)
    move.l d0,d1
    bsr.w sub_8422
hint_98d8:
; --- unverified ---
    move.l (sp)+,d1
    bne.s hint_98c0
hint_98dc:
; --- unverified ---
    move.l (sp)+,d2
    rts
dat_98e0:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w sub_f9a6
hint_98ea:
; --- unverified ---
    bra.w hint_a356
loc_98ee:
    btst #2,541(a6) ; app+$21D
    bne.w loc_f9a2
loc_98f8:
    bra.w loc_a2ca
sub_98fc:
; --- unverified ---
    tst.b 274(a6) ; app+$112
    bne.s hint_991a
hint_9902:
; --- unverified ---
    cmp.b #$1,d3
    bne.s hint_990c
hint_9908:
    dc.b    $50,$ee,$01,$14
hint_990c:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w hint_f99e
hint_9916:
; --- unverified ---
    bra.w hint_a2b6
hint_991a:
; --- unverified ---
    rts
dat_991c:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w loc_f9a2
hint_9926:
; --- unverified ---
    bra.w sub_a2d6
hint_992a:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w loc_f9a2
hint_9934:
; --- unverified ---
    bra.w loc_a2ca
dat_9938:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w loc_f9a2
hint_9942:
; --- unverified ---
    bra.w loc_a2ca
dat_9946:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w sub_f9a6
hint_9950:
; --- unverified ---
    bra.w hint_a32e
dat_9954:
; --- unverified ---
    btst #2,541(a6) ; app+$21D
    bne.w sub_f9a6
hint_995e:
; --- unverified ---
    bra.w hint_a35e
dat_9962:
; --- unverified ---
    tst.b 262(a6) ; app+$106
    beq.s hint_996e
hint_9968:
; --- unverified ---
    moveq #60,d0
    bra.w loc_8486
hint_996e:
; --- unverified ---
    tst.b 274(a6) ; app+$112
    bne.s hint_999c
hint_9974:
; --- unverified ---
    movem.l d1-d2,-(sp)
    st 276(a6) ; app+$114
    move.l a5,d0
    sub.l 588(a6),d0 ; app+$24C
    add.l 572(a6),d0 ; app+$23C
    pea pcref_9998(pc)
    btst #2,541(a6) ; app+$21D
    bne.w sub_f99c
hint_9994:
; --- unverified ---
    bra.w hint_a2aa
pcref_9998:
    dc.b    $4c,$df,$00,$06
hint_999c:
; --- unverified ---
    rts
hint_999e:
; --- unverified ---
    moveq #0,d0
    move.b 326(a6),d0 ; app+$146
    move.l d2,d1
    sub.l 572(a6),d1 ; app+$23C
    btst #2,541(a6) ; app+$21D
    bne.w sub_f832
hint_99b4:
; --- unverified ---
    bra.w sub_9a30
hint_99b8:
; --- unverified ---
    moveq #0,d0
    move.b 326(a6),d0 ; app+$146
    move.l 572(a6),d1 ; app+$23C
    btst #2,541(a6) ; app+$21D
    bne.w hint_f864
hint_99cc:
; --- unverified ---
    bra.w hint_9a6e
sub_99d0:
    moveq #-1,d0
    move.l a1,-(sp)
loc_99d4:
    move.b (a1)+,d1
    cmp.b #$a,d1
    beq.s loc_99e8
loc_99dc:
    cmp.b #$9,d1
    beq.s loc_99e8
loc_99e2:
    cmp.b #$20,d1
    bne.s loc_99d4
loc_99e8:
    move.l a1,d3
    movea.l (sp)+,a1
    sub.l a1,d3
    subq.l #1,d3
    beq.s loc_9a22
loc_99f2:
    moveq #0,d2
loc_99f4:
    addq.l #1,d0
    move.b (a2)+,d2
    beq.s loc_9a22
loc_99fa:
    cmp.b d2,d3
    bcs.s loc_9a22
loc_99fe:
    bne.s loc_9a1e
loc_9a00:
    movem.l d2-d3/a1-a2,-(sp)
loc_9a04:
    move.b (a1)+,d3
    ext.w d3
    move.b 126(a6,d3.w),d3
    cmp.b (a2)+,d3
    bne.s loc_9a1a
loc_9a10:
    subq.b #1,d2
    bne.s loc_9a04
loc_9a14:
    movem.l (sp)+,d2-d3/a1-a2
    rts
loc_9a1a:
    movem.l (sp)+,d2-d3/a1-a2
loc_9a1e:
    adda.l d2,a2
    bra.s loc_99f4
loc_9a22:
    moveq #80,d0
    bsr.w loc_8486
loc_9a28:
    moveq #-1,d0
    rts
loc_9a2c:
    rts
loc_9a2e:
    rts
sub_9a30:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s hint_9a50
hint_9a36:
; --- unverified ---
    movea.l 426(a6),a1 ; app+$1AA
    tst.b 568(a6) ; app+$238
    bne.s hint_9a50
hint_9a40:
    dc.b    $22,$2e,$02,$3c,$92,$a9,$00,$1c,$d3,$a9,$00,$14,$23,$42,$00,$1c
hint_9a50:
; --- unverified ---
    moveq #0,d0
    rts
hint_9a54:
; --- unverified ---
    movea.l 426(a6),a1 ; app+$1AA
    cmpi.w #$3eb,18(a1)
    beq.w sub_845a
hint_9a62:
    dc.b    $d3,$ae,$02,$4c
hint_9a66:
; --- unverified ---
    move.b (a0)+,(a5)+
    subq.l #1,d1
    bne.s hint_9a66
hint_9a6c:
; --- unverified ---
    rts
hint_9a6e:
; --- unverified ---
    tst.b 568(a6) ; app+$238
    beq.s hint_9a8c
hint_9a74:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s hint_9a8c
hint_9a7a:
; --- unverified ---
    movea.l 426(a6),a1 ; app+$1AA
    cmpi.w #$3eb,18(a1)
    beq.s hint_9a8c
hint_9a86:
    dc.b    $94,$81,$d5,$ae,$02,$4c
hint_9a8c:
; --- unverified ---
    moveq #0,d0
    rts
loc_9a90:
    movea.l 426(a6),a0 ; app+$1AA
    cmpi.w #$3eb,18(a0)
    beq.w sub_845a
loc_9a9e:
    add.l d1,588(a6) ; app+$24C
    rts
loc_9aa4:
    tst.b 568(a6) ; app+$238
    bne.w loc_9b0a
loc_9aac:
    bsr.w sub_9b24
loc_9ab0:
    beq.s loc_9b04
loc_9ab2:
    movem.l a0-a1,-(sp)
    moveq #36,d1
    bsr.w sub_90ba
loc_9abc:
    movem.l (sp)+,a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.l a2,4(a0)
    clr.l 20(a0)
    clr.l 28(a0)
    clr.l 24(a0)
    move.l #$3e9,16(a0)
    tst.l 406(a6) ; app+$196
    beq.s loc_9afe
loc_9ae2:
    movea.l 406(a6),a1 ; app+$196
    lea pcref_9b6a(pc),a2
    bsr.w sub_99d0
loc_9aee:
    bne.s loc_9afe
loc_9af0:
    add.w d0,d0
    add.w d0,d0
    lea pcref_9ba2(pc),a2
    move.l 0(a2,d0.w),16(a0)
loc_9afe:
    clr.l 8(a0)
    movea.l a0,a1
loc_9b04:
    move.l a1,426(a6) ; app+$1AA
    rts
loc_9b0a:
    bsr.s sub_9b24
loc_9b0c:
    bne.s loc_9b64
loc_9b0e:
    move.l 12(a1),588(a6) ; app+$24C
    bne.s loc_9b1e
loc_9b16:
    lea 1448(a6),a0 ; app+$5A8
    move.l a0,588(a6) ; app+$24C
loc_9b1e:
    move.l a1,426(a6) ; app+$1AA
    rts
sub_9b24:
    lea 422(a6),a0 ; app+$1A6
    move.b 14(a1),d0
loc_9b2c:
    tst.l (a0)
    beq.s loc_9b3c
loc_9b30:
    addq.b #1,d0
    beq.s loc_9b38
loc_9b34:
    movea.l (a0),a0
    bra.s loc_9b2c
loc_9b38:
    movea.l (a0),a1
    rts
loc_9b3c:
    moveq #-1,d0
    rts
loc_9b40:
    bsr.s sub_9b24
loc_9b42:
    bne.s loc_9b64
loc_9b44:
    tst.b 568(a6) ; app+$238
    bne.s loc_9b5e
loc_9b4a:
    move.l 572(a6),d2 ; app+$23C
    sub.l 28(a1),d2
    add.l d2,20(a1)
    move.l 572(a6),28(a1) ; app+$23C
    rts
loc_9b5e:
    move.l a5,12(a1)
    rts
loc_9b64:
    moveq #77,d0
    bra.w loc_846e
pcref_9b6a:
    dc.b    $03,$42,$53,$53,$04,$43,$4f,$44,$45,$04,$44,$41,$54,$41,$05,$42
    dc.b    $53,$53,$5f,$43,$05,$42,$53,$53,$5f,$46,$06
    dc.b    "CODE_C"
    dc.b    $06
    dc.b    "CODE_F"
    dc.b    $06
    dc.b    "DATA_C"
    dc.b    $06
    dc.b    "DATA_F",0
    dc.b    $00
pcref_9ba2:
    dc.b    $00,$00,$03,$eb,$00,$00,$03,$e9,$00,$00,$03,$ea,$40,$00,$03,$eb
    dc.b    $80,$00,$03,$eb,$40,$00,$03,$e9,$80,$00,$03,$e9,$40,$00,$03,$ea
    dc.b    $80,$00,$03,$ea
loc_9bc6:
    move.l a4,-(sp)
    movea.l 410(a6),a4 ; app+$19A
    lea 422(a6),a3 ; app+$1A6
loc_9bd0:
    tst.l (a3)
    beq.s loc_9c20
loc_9bd4:
    movea.l (a3),a3
    move.l 20(a3),d1
    beq.s loc_9c24
loc_9bdc:
    move.l d1,d0
    andi.b #$3,d0
    beq.s loc_9bea
loc_9be4:
    andi.b #$fc,d1
    addq.l #4,d1
loc_9bea:
    move.l d1,20(a3)
    tst.l 410(a6) ; app+$19A
    beq.s loc_9c02
loc_9bf4:
    move.w 16(a3),d0
    bsr.w alloc_memory
loc_9bfc:
    bne.w loc_90ec
loc_9c00:
    bra.s loc_9c10
loc_9c02:
    cmpi.w #$3eb,18(a3)
    beq.s loc_9c24
loc_9c0a:
    addq.l #8,d1
    bsr.w sub_90ba
loc_9c10:
    move.l a0,8(a3)
    move.l a0,12(a3)
    adda.l 20(a3),a0
    clr.l -(a0)
    bra.s loc_9bd0
loc_9c20:
    movea.l (sp)+,a4
    rts
loc_9c24:
    clr.l 12(a3)
    bra.s loc_9bd0
loc_9c2a:
    move.b d0,d1
    not.b d1
    bsr.w sub_8eb6
loc_9c32:
    moveq #46,d1
    bra.w loc_9288
loc_9c38:
    movea.l 426(a6),a1 ; app+$1AA
    cmpi.w #$3eb,18(a1)
    rts
loc_9c44:
    movea.l 414(a6),a4 ; app+$19E
    tst.b 260(a6) ; app+$104
    beq.s loc_9c9e
loc_9c4e:
    lea 422(a6),a3 ; app+$1A6
loc_9c52:
    movea.l (a3),a3
    movea.l 4(a3),a0
    move.b 14(a0),d6
    movea.l 318(a6),a1 ; app+$13E
    lea loc_9d02(pc),a2
    moveq #0,d7
    bsr.w sub_8cf6
loc_9c6a:
    tst.l d7
    beq.s loc_9c9a
loc_9c6e:
    move.l d7,d1
    addq.l #8,d1
    moveq #0,d0
    bsr.w alloc_memory
loc_9c78:
    bne.w loc_90ec
loc_9c7c:
    move.l a4,-(sp)
    movea.l a0,a4
    move.l #$3f0,(a4)+
    lea loc_9d2a(pc),a2
    movea.l 318(a6),a1 ; app+$13E
    movea.l 4(a3),a0
    bsr.w sub_8cf6
loc_9c96:
    clr.l (a4)
    movea.l (sp)+,a4
loc_9c9a:
    tst.l (a3)
    bne.s loc_9c52
loc_9c9e:
    tst.b 297(a6) ; app+$129
    beq.s loc_9cbe
loc_9ca4:
    lea 422(a6),a3 ; app+$1A6
loc_9ca8:
    movea.l (a3),a3
    movea.l 4(a3),a0
    move.b 14(a0),d6
    lea loc_8c00(pc),a2
    bsr.w sub_8c9a
loc_9cba:
    tst.l (a3)
    bne.s loc_9ca8
loc_9cbe:
    lea 422(a6),a3 ; app+$1A6
loc_9cc2:
    movea.l (a3),a3
    tst.l 24(a3)
    beq.s loc_9cfc
loc_9cca:
    moveq #0,d3
    lea 422(a6),a2 ; app+$1A6
    moveq #1,d6
loc_9cd2:
    movea.l (a2),a2
    movea.l 4(a2),a0
    move.b 14(a0),d3
    bsr.w sub_a164
loc_9ce0:
    beq.s loc_9cf8
loc_9ce2:
    bsr.w sub_a192
loc_9ce6:
    bne.s loc_9cf8
loc_9ce8:
    movea.l 4(a0),a1
    adda.l 8(a3),a1
    move.l 8(a2),d1
    add.l d1,(a1)
    bra.s loc_9ce2
loc_9cf8:
    tst.l (a2)
    bne.s loc_9cd2
loc_9cfc:
    tst.l (a3)
    bne.s loc_9cc2
loc_9d00:
    rts
loc_9d02:
    cmp.b 14(a1),d6
    bne.s loc_9d00
loc_9d08:
    cmpi.b #$1,13(a1)
    bne.s loc_9d00
loc_9d10:
    moveq #0,d1
    move.b 22(a1),d1
    move.l d1,d2
    andi.b #$3,d2
    beq.s loc_9d24
loc_9d1e:
    andi.b #$fc,d1
    addq.l #4,d1
loc_9d24:
    add.l d1,d7
    addq.l #8,d7
    rts
loc_9d2a:
    cmp.b 14(a1),d6
    bne.s loc_9d00
loc_9d30:
    cmpi.b #$1,13(a1)
    bne.s loc_9d00
loc_9d38:
    bsr.s sub_9d46
loc_9d3a:
    move.l 8(a1),d0
    add.l 8(a3),d0
    move.l d0,(a4)+
    rts
sub_9d46:
    moveq #0,d1
    move.b 22(a1),d1
    move.l d1,d2
    andi.b #$3,d2
    beq.s loc_9d5a
loc_9d54:
    andi.b #$fc,d1
    addq.l #4,d1
loc_9d5a:
    lsr.l #2,d1
    move.l d1,(a4)+
    lea 22(a1),a0
    move.b (a0)+,d0
loc_9d64:
    move.b (a0)+,(a4)+
    subq.b #1,d0
    bne.s loc_9d64
loc_9d6a:
    move.b 22(a1),d0
    andi.b #$3,d0
    beq.s loc_9d7e
loc_9d74:
    clr.b (a4)+
    addq.b #1,d0
    cmp.b #$4,d0
    bne.s loc_9d74
loc_9d7e:
    rts
sub_9d80:
    movem.l d6/a0-a2,-(sp)
    movea.l 4(a0),a0
    move.b 14(a0),d6
    lea loc_9da2(pc),a2
    movea.l 318(a6),a1 ; app+$13E
    moveq #0,d0
    bsr.w sub_8d1c
loc_9d9a:
    movem.l (sp)+,d6/a0-a2
    tst.l d0
    rts
loc_9da2:
    addq.l #1,d0
    rts
loc_9da6:
    tst.l 410(a6) ; app+$19A
    bne.w loc_9c44
loc_9dae:
    bsr.w loc_97a6
loc_9db2:
    cmpi.w #$3,540(a6) ; app+$21C
    bne.s loc_9e34
loc_9dba:
    bsr.w sub_a110
loc_9dbe:
    move.l #$3f3,d1
    bsr.w loc_a0ee
loc_9dc8:
    moveq #0,d1
    bsr.w loc_a0ee
loc_9dce:
    moveq #0,d1
    lea 422(a6),a0 ; app+$1A6
loc_9dd4:
    movea.l (a0),a0
    tst.l 20(a0)
    bne.s loc_9de0
loc_9ddc:
    bsr.s sub_9d80
loc_9dde:
    beq.s loc_9de2
loc_9de0:
    addq.l #1,d1
loc_9de2:
    tst.l (a0)
    bne.s loc_9dd4
loc_9de6:
    bsr.w loc_a0ee
loc_9dea:
    move.l d1,d2
    moveq #0,d1
    bsr.w loc_a0ee
loc_9df2:
    move.l d2,d1
    subq.l #1,d1
    bsr.w loc_a0ee
loc_9dfa:
    lea 422(a6),a3 ; app+$1A6
loc_9dfe:
    movea.l (a3),a3
    move.l 20(a3),d1
    bne.s loc_9e0e
loc_9e06:
    movea.l a3,a0
    bsr.w sub_9d80
loc_9e0c:
    beq.s loc_9e1c
loc_9e0e:
    lsr.l #2,d1
    swap d1
    or.w 16(a3),d1
    swap d1
    bsr.w loc_a0ee
loc_9e1c:
    tst.l (a3)
    bne.s loc_9dfe
loc_9e20:
    bsr.w sub_a0f6
loc_9e24:
    tst.b 297(a6) ; app+$129
    beq.s loc_9e2e
loc_9e2a:
    bsr.w sub_a42e
loc_9e2e:
    lea 422(a6),a3 ; app+$1A6
    bra.s loc_9e64
loc_9e34:
    move.l #$3e7,d1
    lea 430(a6),a1 ; app+$1AE
    tst.b (a1)
    beq.s loc_9e50
loc_9e42:
    move.l a1,d0
loc_9e44:
    tst.b (a1)+
    bne.s loc_9e44
loc_9e48:
    subq.l #1,a1
    exg
    sub.l a1,d0
    bra.s loc_9e5c
loc_9e50:
    movea.l 318(a6),a1 ; app+$13E
    lea 22(a1),a1
    move.b (a1)+,d0
    subq.b #1,d0
loc_9e5c:
    bsr.w sub_a1d0
loc_9e60:
    lea 422(a6),a3 ; app+$1A6
loc_9e64:
    movea.l (a3),a3
    tst.l 20(a3)
    bne.s loc_9e76
loc_9e6c:
    movea.l a3,a0
    bsr.w sub_9d80
loc_9e72:
    beq.w loc_9ff8
loc_9e76:
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s loc_9e94
loc_9e7e:
    move.l #$3e8,d1
    movea.l 4(a3),a1
    lea 22(a1),a1
    move.b (a1)+,d0
    subq.b #1,d0
    bsr.w sub_a1d0
loc_9e94:
    lea 20(a3),a0
    move.l (a0),d0
    lsr.l #2,d0
    move.l d0,(a0)
    subq.l #4,a0
    moveq #8,d1
    bsr.w sub_8422
loc_9ea6:
    cmpi.w #$3eb,18(a3)
    beq.s loc_9ebe
loc_9eae:
    movea.l 8(a3),a0
    move.l 20(a3),d1
    add.l d1,d1
    add.l d1,d1
    bsr.w sub_8422
loc_9ebe:
    bsr.w sub_a110
loc_9ec2:
    tst.l 24(a3)
    beq.w loc_9f6c
loc_9eca:
    moveq #1,d6
    move.l #$3ec,d1
    bsr.s sub_9ef4
loc_9ed4:
    cmpi.w #$3,540(a6) ; app+$21C
    beq.w loc_9f6c
loc_9ede:
    move.l #$3f8,d1
    moveq #40,d6
    bsr.s sub_9ef4
loc_9ee8:
    move.l #$3f9,d1
    moveq #41,d6
    bsr.s sub_9ef4
loc_9ef2:
    bra.s loc_9f6c
sub_9ef4:
    moveq #0,d3
    move.l d1,-(sp)
    pea 422(a6) ; app+$1A6
    clr.l -(sp)
loc_9efe:
    movea.l 4(sp),a0
loc_9f02:
    tst.l (a0)
    beq.s loc_9f5a
loc_9f06:
    movea.l (a0),a0
    subq.l #1,d3
    tst.l 20(a0)
    bne.s loc_9f16
loc_9f10:
    bsr.w sub_9d80
loc_9f14:
    beq.s loc_9f02
loc_9f16:
    move.l a0,4(sp)
    bsr.w sub_a164
loc_9f1e:
    beq.s loc_9f4e
loc_9f20:
    move.l 8(sp),d0
    beq.s loc_9f34
loc_9f26:
    move.l d1,-(sp)
    move.l d0,d1
    bsr.w loc_a0ee
loc_9f2e:
    move.l (sp)+,d1
    clr.l 8(sp)
loc_9f34:
    bsr.w loc_a0ee
loc_9f38:
    move.l (sp),d1
    bsr.w loc_a0ee
loc_9f3e:
    bsr.w sub_a192
loc_9f42:
    bne.s loc_9f4e
loc_9f44:
    move.l 4(a0),d1
    bsr.w loc_a0ee
loc_9f4c:
    bra.s loc_9f3e
loc_9f4e:
    addq.l #1,(sp)
    movea.l 318(a6),a0 ; app+$13E
    cmp.b 12(a0),d3
    bne.s loc_9efe
loc_9f5a:
    tst.l 8(sp)
    lea 12(sp),sp
    bne.s loc_9f6a
loc_9f64:
    moveq #0,d1
    bra.w loc_a0ee
loc_9f6a:
    rts
loc_9f6c:
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s loc_9fa6
loc_9f74:
    move.l #$3ef,d1
    bsr.w loc_a0ee
loc_9f7e:
    movea.l 4(a3),a0
    move.b 14(a0),d3
    movea.l 318(a6),a1 ; app+$13E
    lea loc_a11a(pc),a2
    bsr.w sub_8d48
loc_9f92:
    move.b d3,d6
    lea loc_a034(pc),a2
    movea.l 318(a6),a1 ; app+$13E
    bsr.w sub_8d1c
loc_9fa0:
    moveq #0,d1
    bsr.w loc_a0ee
loc_9fa6:
    tst.l 524(a6) ; app+$20C
    beq.s loc_9fbc
loc_9fac:
    movem.l d2/a0-a1,-(sp)
    bsr.w call_seek_b054
loc_9fb4:
    movem.l (sp)+,d2/a0-a1
    move.l d0,32(a3)
loc_9fbc:
    tst.b 260(a6) ; app+$104
    beq.s loc_9fe6
loc_9fc2:
    movea.l 4(a3),a0
    move.b 14(a0),d6
    move.l #$3f0,d1
    bsr.w loc_a0ee
loc_9fd4:
    movea.l 318(a6),a1 ; app+$13E
    lea loc_a04c(pc),a2
    bsr.w sub_8cf6
loc_9fe0:
    moveq #0,d1
    bsr.w loc_a0ee
loc_9fe6:
    tst.b 297(a6) ; app+$129
    beq.w loc_9ff6
loc_9fee:
    lea loc_8b4c(pc),a2
    bsr.w sub_8c9a
loc_9ff6:
    bsr.s sub_a01a
loc_9ff8:
    tst.l (a3)
    bne.w loc_9e64
loc_9ffe:
    lea 422(a6),a3 ; app+$1A6
loc_a002:
    movea.l (a3),a3
    tst.l 20(a3)
    bne.s loc_a028
loc_a00a:
    movea.l a3,a0
    bsr.w sub_9d80
loc_a010:
    bne.s loc_a028
loc_a012:
    tst.l (a3)
    bne.s loc_a002
loc_a016:
    bsr.w sub_a110
sub_a01a:
    move.l #$3f2,d1
    bsr.w loc_a0ee
loc_a024:
    bra.w sub_a0f6
loc_a028:
    tst.l 524(a6) ; app+$20C
    beq.s loc_a032
loc_a02e:
    bsr.w sub_a450
loc_a032:
    rts
loc_a034:
    moveq #1,d0
    cmpi.b #$1,13(a1)
    beq.s loc_a040
loc_a03e:
    moveq #2,d0
loc_a040:
    bsr.s sub_a098
loc_a042:
    move.l 8(a1),d1
    bra.w loc_a0ee
loc_a04a:
    rts
loc_a04c:
    cmp.b 14(a1),d6
    bne.s loc_a04a
loc_a052:
    cmpi.b #$1,13(a1)
    bne.s loc_a04a
loc_a05a:
    btst #4,12(a1)
    bne.s loc_a04a
loc_a062:
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s loc_a07c
loc_a06a:
    tst.b 260(a6) ; app+$104
    bpl.s loc_a078
loc_a070:
    btst #5,12(a1)
    beq.s loc_a04a
loc_a078:
    moveq #0,d0
    bra.s loc_a040
loc_a07c:
    move.w 18(a3),d0
    cmp.w #$3ea,d0
    beq.s loc_a092
loc_a086:
    cmp.w #$3e9,d0
    bne.s loc_a078
loc_a08c:
    addq.l #1,532(a6) ; app+$214
    bra.s loc_a078
loc_a092:
    addq.l #1,528(a6) ; app+$210
    bra.s loc_a078
sub_a098:
    moveq #0,d1
    move.b 22(a1),d1
    move.l d1,d2
    andi.b #$3,d2
    beq.s loc_a0ac
loc_a0a6:
    andi.b #$fc,d1
    addq.l #4,d1
loc_a0ac:
    lsr.l #2,d1
    ror.l #8,d0
    or.l d0,d1
    bsr.s loc_a0ee
loc_a0b4:
    moveq #4,d0
    add.b 22(a1),d0
    cmp.w d0,d4
    bcc.s loc_a0c0
loc_a0be:
    bsr.s sub_a0f6
loc_a0c0:
    lea 22(a1),a0
    move.b (a0)+,d0
loc_a0c6:
    move.b (a0)+,(a4)+
    subq.w #1,d4
    subq.b #1,d0
    bne.s loc_a0c6
loc_a0ce:
    move.b 22(a1),d0
    andi.b #$3,d0
    beq.s loc_a0e4
loc_a0d8:
    clr.b (a4)+
    addq.b #1,d0
    subq.w #1,d4
    cmp.b #$4,d0
    bne.s loc_a0d8
loc_a0e4:
    rts
sub_a0e6:
    addq.w #4,d4
    move.l d1,-(sp)
    bsr.s sub_a0f6
loc_a0ec:
    move.l (sp)+,d1
loc_a0ee:
    subq.w #4,d4
    bcs.s sub_a0e6
loc_a0f2:
    move.l d1,(a4)+
    rts
sub_a0f6:
    move.l #$80,d1
    sub.w d4,d1
    beq.s sub_a110
loc_a100:
    movem.l d0/d2/a0-a2,-(sp)
    lea 1448(a6),a0 ; app+$5A8
    bsr.w sub_8422
loc_a10c:
    movem.l (sp)+,d0/d2/a0-a2
sub_a110:
    lea 1448(a6),a4 ; app+$5A8
    move.w #$80,d4
    rts
loc_a11a:
    movem.l a1-a2,-(sp)
    moveq #2,d6
    move.w 20(a1),d2
    bsr.s sub_a13c
loc_a126:
    moveq #4,d6
    bsr.s sub_a13c
loc_a12a:
    moveq #5,d6
    bsr.s sub_a13c
loc_a12e:
    moveq #7,d6
    bsr.s sub_a13c
loc_a132:
    moveq #8,d6
    bsr.s sub_a13c
loc_a136:
    movem.l (sp)+,a1-a2
    rts
sub_a13c:
    bsr.w sub_a164
loc_a140:
    beq.s loc_a162
loc_a142:
    movem.l d1-d2,-(sp)
    moveq #127,d0
    add.b d6,d0
    bsr.w sub_a098
loc_a14e:
    movem.l (sp)+,d1-d2
    bsr.s loc_a0ee
loc_a154:
    bsr.w sub_a192
loc_a158:
    bne.s loc_a162
loc_a15a:
    move.l 4(a0),d1
    bsr.s loc_a0ee
loc_a160:
    bra.s loc_a154
loc_a162:
    rts
sub_a164:
    moveq #0,d1
    tst.l 24(a3)
    beq.s loc_a17c
loc_a16c:
    bsr.s sub_a17e
loc_a16e:
    beq.s loc_a17c
loc_a170:
    bsr.s sub_a192
loc_a172:
    bne.s loc_a178
loc_a174:
    addq.l #1,d1
    bra.s loc_a170
loc_a178:
    bsr.s sub_a17e
loc_a17a:
    tst.l d1
loc_a17c:
    rts
sub_a17e:
    movea.l 24(a3),a5
sub_a182:
    moveq #10,d5
    lea 10(a5),a0
    move.l a0,6(a5)
    sub.w 4(a5),d5
    rts
sub_a192:
    subq.w #1,d5
    bcs.s loc_a1c2
loc_a196:
    movea.l 6(a5),a0
    addq.l #8,6(a5)
    cmp.b (a0),d6
    bne.s sub_a192
loc_a1a2:
    cmp.b 1(a0),d3
    bne.s sub_a192
loc_a1a8:
    cmp.b #$1,d6
    beq.s loc_a1c0
loc_a1ae:
    cmp.b #$28,d6
    beq.s loc_a1c0
loc_a1b4:
    cmp.b #$29,d6
    beq.s loc_a1c0
loc_a1ba:
    cmp.w 2(a0),d2
    bne.s sub_a192
loc_a1c0:
    rts
loc_a1c2:
    tst.l (a5)
    beq.s loc_a1cc
loc_a1c6:
    movea.l (a5),a5
    bsr.s sub_a182
loc_a1ca:
    bne.s sub_a192
loc_a1cc:
    moveq #-1,d0
    rts
sub_a1d0:
    lea 1448(a6),a0 ; app+$5A8
    move.l d1,(a0)+
    moveq #0,d1
    move.b d0,d1
    move.l d1,d2
    andi.b #$3,d2
    beq.s loc_a1e8
loc_a1e2:
    andi.b #$fc,d1
    addq.l #4,d1
loc_a1e8:
    lsr.l #2,d1
    move.l d1,(a0)+
    beq.s loc_a1fa
loc_a1ee:
    move.b (a1)+,(a0)+
    subq.b #1,d0
    bne.s loc_a1ee
loc_a1f4:
    clr.b (a0)+
    clr.b (a0)+
    clr.b (a0)+
loc_a1fa:
    add.l d1,d1
    add.l d1,d1
    addq.l #8,d1
    lea 1448(a6),a0 ; app+$5A8
    bra.w sub_8422
sub_a208:
    movea.l 426(a6),a0 ; app+$1AA
    lea 24(a0),a0
    tst.l (a0)
    beq.s loc_a220
loc_a214:
    movea.l (a0),a0
    tst.w 4(a0)
    bne.s loc_a240
loc_a21c:
    tst.l (a0)
    bne.s loc_a214
loc_a220:
    movem.l d0-d2/a0/a2,-(sp)
    moveq #90,d1
    bsr.w sub_90ba
loc_a22a:
    movem.l (sp)+,d0-d2/a1-a2
    move.l a0,(a1)
    clr.l (a0)
    move.w #$a,4(a0)
    lea 10(a0),a1
    move.l a1,6(a0)
loc_a240:
    subq.w #1,4(a0)
    movea.l 6(a0),a1
    addq.l #8,6(a0)
    movea.l a1,a0
    rts
sub_a250:
    movea.l 2368(a6),a0 ; app+$940
    move.w (a0)+,d0
    cmp.w #$2b2b,d0
    bne.s loc_a288
loc_a25c:
    move.w (a0)+,d0
    bpl.s loc_a280
loc_a260:
    andi.w #$ff,d0
    cmpi.w #$2d2d,(a0)
    bne.s loc_a280
loc_a26a:
    tst.b 2(a0)
    bpl.s loc_a280
loc_a270:
    cmp.b 3(a0),d0
    bne.s loc_a280
loc_a276:
    tst.w 4(a0)
    bne.s loc_a288
loc_a27c:
    addq.l #4,sp
    rts
loc_a280:
    tst.w (a0)
    bne.s loc_a288
loc_a284:
    tst.w -(a0)
    rts
loc_a288:
    moveq #68,d0
    bra.w loc_8486
sub_a28e:
    dc.b    $d4,$ae,$02,$3c,$d4,$8d,$94,$ae,$02,$4c
hint_a298:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s hint_a2a8
hint_a29e:
; --- unverified ---
    bsr.w sub_a208
hint_a2a2:
    dc.b    $30,$80,$21,$42,$00,$04
hint_a2a8:
; --- unverified ---
    rts
hint_a2aa:
; --- unverified ---
    move.l d0,d2
    move.w #$100,d0
    or.b 326(a6),d0 ; app+$146
    bra.s hint_a298
hint_a2b6:
; --- unverified ---
    move.l d2,(a5)+
    bsr.s sub_a250
hint_a2ba:
; --- unverified ---
    bpl.s hint_a2c4
hint_a2bc:
; --- unverified ---
    ori.w #$100,d0
    moveq #-4,d2
    bra.s sub_a28e
hint_a2c4:
; --- unverified ---
    bsr.w sub_a36c
    dc.b    $02,$fc
loc_a2ca:
    move.w d2,(a5)+
    bsr.s sub_a250
loc_a2ce:
    bmi.s loc_a288
loc_a2d0:
    bsr.w sub_a36c
    dc.b    $04,$fe
sub_a2d6:
; --- unverified ---
    cmpi.w #$3,540(a6) ; app+$21C
    bne.w hint_a312
hint_a2e0:
; --- unverified ---
    move.w d2,(a5)+
    cmp.b #$1,d3
    beq.s loc_a288
hint_a2e8:
; --- unverified ---
    movea.l 2368(a6),a0 ; app+$940
    move.w (a0)+,d0
    cmp.w #$2b2b,d0
    bne.s loc_a288
hint_a2f4:
; --- unverified ---
    move.w (a0)+,d0
    bpl.s loc_a288
hint_a2f8:
    dc.b    $0c,$50,$2d,$2d
hint_a2fc:
; --- unverified ---
    bne.s loc_a288
hint_a2fe:
; --- unverified ---
    tst.b 2(a0)
    bpl.s loc_a288
hint_a304:
; --- unverified ---
    cmp.b 3(a0),d0
    bne.s hint_a2fc
hint_a30a:
; --- unverified ---
    tst.w 4(a0)
    bne.s hint_a2fc
hint_a310:
; --- unverified ---
    rts
hint_a312:
; --- unverified ---
    cmp.b #$1,d3
    bne.s loc_a2ca
hint_a318:
; --- unverified ---
    move.w d2,(a5)+
    bsr.w sub_a250
hint_a31e:
; --- unverified ---
    bmi.s sub_a324
hint_a320:
; --- unverified ---
    bsr.s sub_a36c
    dc.b    $07,$fe
sub_a324:
; --- unverified ---
    ori.w #$2800,d0
    moveq #-2,d2
    bra.w sub_a28e
hint_a32e:
; --- unverified ---
    cmpi.w #$3,540(a6) ; app+$21C
    beq.w loc_a288
hint_a338:
; --- unverified ---
    cmp.b #$1,d3
    bne.s hint_a35e
hint_a33e:
; --- unverified ---
    move.b d2,(a5)+
    bsr.w sub_a250
hint_a344:
; --- unverified ---
    bmi.w sub_a34c
hint_a348:
; --- unverified ---
    bsr.s sub_a36c
    dc.b    $08,$ff
sub_a34c:
; --- unverified ---
    ori.w #$2900,d0
    moveq #-1,d2
    bra.w sub_a28e
hint_a356:
    dc.b    $94,$ae,$02,$4c,$d4,$8d,$55,$82
hint_a35e:
; --- unverified ---
    move.b d2,(a5)+
    bsr.w sub_a250
hint_a364:
; --- unverified ---
    bmi.w loc_a288
hint_a368:
; --- unverified ---
    bsr.s sub_a36c
    dc.b    $05,$ff
sub_a36c:
    tst.b 259(a6) ; app+$103
    beq.s loc_a392
loc_a372:
    bsr.w sub_a208
loc_a376:
    movea.l (sp),a1
    move.b (a1)+,(a0)+
    move.b 326(a6),(a0)+ ; app+$146
    move.w d0,(a0)+
    move.b (a1)+,d2
    ext.w d2
    ext.l d2
    add.l 572(a6),d2 ; app+$23C
    add.l a5,d2
    sub.l 588(a6),d2 ; app+$24C
    move.l d2,(a0)+
loc_a392:
    addq.l #4,sp
    rts
loc_a396:
    lea str_a3cc(pc),a0
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s loc_a3a6
loc_a3a2:
    lea str_a3ba(pc),a0
loc_a3a6:
    rts
loc_a3a8:
    lea pcref_a3dd(pc),a0
    cmpi.w #$3,540(a6) ; app+$21C
    beq.s loc_a3a6
loc_a3b4:
    lea pcref_a3c9(pc),a0
    rts
str_a3ba:
    dc.b    "Amiga linkable",0
pcref_a3c9:
    dc.b    $2e,$6f,$00
str_a3cc:
    dc.b    "Amiga execut"
sub_a3d8:
; --- unverified ---
    bsr.s loc_a43c
hint_a3da:
    dc.b    $6c,$65
hint_a3dc:
    dc.b    $00
pcref_a3dd:
    dc.b    $00
hint_a3de:
    dc.b    $2f,$08
hint_a3e0:
; --- unverified ---
    move.b (a0)+,(a1)+
    bne.s hint_a3e0
hint_a3e4:
    dc.b    $13,$7c,$00,$2c,$ff,$ff,$20,$5f
hint_a3ec:
; --- unverified ---
    move.b (a0)+,(a1)+
    bne.s hint_a3ec
hint_a3f0:
; --- unverified ---
    subq.l #1,a1
    rts
sub_a3f4:
    tst.b 260(a6) ; app+$104
    beq.s loc_a42c
loc_a3fa:
    lea 422(a6),a3 ; app+$1A6
loc_a3fe:
    movea.l (a3),a3
    tst.l 20(a3)
    bne.s loc_a40e
loc_a406:
    movea.l a3,a0
    bsr.w sub_9d80
loc_a40c:
    beq.s loc_a428
loc_a40e:
    move.w 18(a3),d0
    cmp.w #$3ea,d0
    beq.s loc_a424
loc_a418:
    cmp.w #$3e9,d0
    bne.s loc_a428
loc_a41e:
    addq.l #1,516(a6) ; app+$204
    bra.s loc_a428
loc_a424:
    addq.l #1,520(a6) ; app+$208
loc_a428:
    tst.l (a3)
    bne.s loc_a3fe
loc_a42c:
    rts
sub_a42e:
    bsr.w call_seek_b054
loc_a432:
    move.l d0,524(a6) ; app+$20C
    moveq #11,d1
    add.l 516(a6),d1 ; app+$204
loc_a43c:
    add.l 520(a6),d1 ; app+$208
    add.l 512(a6),d1 ; app+$200
    lsl.l #2,d1
    movea.l a6,a0
    bsr.w sub_8422
loc_a44c:
    bra.w sub_a110
sub_a450:
    move.l 524(a6),d2 ; app+$20C
    bsr.w call_seek
loc_a458:
    bsr.w sub_a110
loc_a45c:
    move.l #$3f1,d1
    bsr.w loc_a0ee
loc_a466:
    moveq #9,d1
    add.l 516(a6),d1 ; app+$204
    add.l 520(a6),d1 ; app+$208
    add.l 512(a6),d1 ; app+$200
    bsr.w loc_a0ee
loc_a478:
    moveq #0,d1
    bsr.w loc_a0ee
loc_a47e:
    move.l #$48454144,d1 ; 'HEAD'
    bsr.w loc_a0ee
loc_a488:
    move.l #$44424756,d1 ; 'DBGV'
    bsr.w loc_a0ee
loc_a492:
    move.l #$30310000,d1
    bsr.w loc_a0ee
loc_a49c:
    move.l 528(a6),d1 ; app+$210
    bsr.w loc_a0ee
loc_a4a4:
    move.l 532(a6),d1 ; app+$214
    bsr.w loc_a0ee
loc_a4ac:
    move.l 512(a6),d1 ; app+$200
    bsr.w loc_a0ee
loc_a4b4:
    lea loc_a522(pc),a2
    bsr.w sub_8a26
loc_a4bc:
    move.l 520(a6),d1 ; app+$208
    bsr.w loc_a0ee
loc_a4c4:
    move.l #$3ea,d3
    bsr.w sub_a4e4
loc_a4ce:
    move.l 516(a6),d1 ; app+$204
    bsr.w loc_a0ee
loc_a4d6:
    move.l #$3e9,d3
    bsr.w sub_a4e4
loc_a4e0:
    bra.w sub_a0f6
sub_a4e4:
    tst.b 260(a6) ; app+$104
    beq.s loc_a520
loc_a4ea:
    moveq #0,d2
    lea 422(a6),a3 ; app+$1A6
loc_a4f0:
    movea.l (a3),a3
    tst.l 20(a3)
    bne.s loc_a500
loc_a4f8:
    movea.l a3,a0
    bsr.w sub_9d80
loc_a4fe:
    beq.s loc_a51a
loc_a500:
    move.w 18(a3),d0
    cmp.w d0,d3
    bne.s loc_a51a
loc_a508:
    moveq #0,d1
    move.b d2,d1
    ror.b #8,d1
    add.l 32(a3),d1
    move.b d2,-(sp)
    bsr.w loc_a0ee
loc_a518:
    move.b (sp)+,d2
loc_a51a:
    addq.b #1,d2
    tst.l (a3)
    bne.s loc_a4f0
loc_a520:
    rts
loc_a522:
    moveq #0,d2
    lea 422(a6),a3 ; app+$1A6
loc_a528:
    movea.l (a3),a3
    tst.l 20(a3)
    bne.s loc_a538
loc_a530:
    movea.l a3,a0
    bsr.w sub_9d80
loc_a536:
    beq.s loc_a54a
loc_a538:
    lea loc_a550(pc),a2
    movea.l 4(a3),a0
    move.b 14(a0),d6
    bsr.w sub_8c9a
loc_a548:
    addq.b #1,d2
loc_a54a:
    tst.l (a3)
    bne.s loc_a528
loc_a54e:
    rts
loc_a550:
    moveq #0,d1
    move.b d2,d1
    ror.b #8,d1
    add.l 28(a0),d1
    move.l a0,-(sp)
    bsr.w loc_a0ee
loc_a560:
    movea.l (sp)+,a0
    rts
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dcb.b   23,0
    dc.b    $01
    dcb.b   31,0
    dc.b    $01
    dcb.b   8,0
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$00,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01
    dcb.b   26,0
    dc.b    $01,$01,$01,$01,$00,$01
    dcb.b   26,0
    dc.b    $01,$01,$01,$01,$01
sub_a664:
    dc.b    $80,$81,$82,$83,$84,$85,$86,$87,$88,$89,$8a,$8b,$8c,$8d,$8e,$8f
    dc.b    $90,$91,$92,$93,$94,$95,$96,$97,$98,$99,$9a,$9b,$9c,$9d,$9e,$9f
    dc.b    $a0,$a1,$a2,$a3,$a4,$a5,$a6,$a7,$a8,$a9,$aa,$ab,$ac,$ad,$ae,$af
    dc.b    $b0,$b1,$b2,$b3,$b4,$b5,$b6,$b7,$b8,$b9,$ba,$bb,$bc,$bd,$be,$bf
    dc.b    $c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7,$c8,$c9,$ca,$cb,$cc,$cd,$ce,$cf
    dc.b    $d0,$d1,$d2,$d3,$d4,$d5,$d6,$d7,$d8,$d9,$da,$db,$dc,$dd,$de,$df
    dc.b    $c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7,$c8,$c9,$ca,$cb,$cc,$cd,$ce,$cf
    dc.b    $d0,$d1,$d2,$d3,$d4,$d5,$d6,$f7,$d8,$d9,$da,$db,$dc,$dd,$de,$ff
    dc.b    $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$0a,$0b,$0c,$0d,$0e,$0f
    dc.b    $10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$1a,$1b,$1c,$1d,$1e,$1f
    dc.b    " !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLM"
sub_a732:
    dc.b    $4e,$4f
    dc.b    "PQRSTUVWXYZ[\]^_`ABCDEFGHIJKLMNOPQRSTUVWXYZ{|}~"
    dc.b    $7f
sub_a764:
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $ff,$01
    dcb.b   10,0
    dc.b    $01,$01,$01,$01,$01
    dcb.b   28,0
    dc.b    $01,$01,$01,$01,$00,$01
    dcb.b   26,0
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01,$01
    dc.b    $01,$01,$01,$01,$01
    dcb.b   23,0
    dc.b    $01
    dcb.b   31,0
    dc.b    $01
    dcb.b   8,0
call_output:
    move.l d3,-(sp)
    move.l app_output_file(a6),d1
    bne.s loc_a878
loc_a86c:
    moveq #_LVOOutput,d0
    bsr.w dos_dispatch_b0d6
loc_a872:
    move.l d0,app_output_file(a6)
    move.l d0,d1
loc_a878:
    lea 3574(a6),a0 ; app+$DF6
    move.l a0,d2
    moveq #0,d3
    move.w 3566(a6),d3 ; app+$DEE
    moveq #_LVOWrite,d0
    bsr.w dos_dispatch_b0d6
loc_a88a:
    move.l (sp)+,d3
    bsr.w check_signals
loc_a890:
    clr.w 3566(a6) ; app+$DEE
    lea 3574(a6),a0 ; app+$DF6
    move.l a0,3568(a6) ; app+$DF0
    rts
sub_a89e:
    cmpi.w #$82,3566(a6) ; app+$DEE
    beq.s loc_a8bc
loc_a8a6:
    movea.l 3568(a6),a0 ; app+$DF0
    move.b d1,(a0)+
    move.l a0,3568(a6) ; app+$DF0
    addq.w #1,3566(a6) ; app+$DEE
    cmp.b #$a,d1
    beq.s call_output
loc_a8ba:
    rts
loc_a8bc:
    move.w d1,-(sp)
    bsr.s call_output
loc_a8c0:
    move.w (sp)+,d1
    bra.s sub_a89e
sub_a8c4:
    move.w d1,-(sp)
    lea pcref_a8de(pc),a0
loc_a8ca:
    move.b (a0)+,d1
    beq.s loc_a8da
loc_a8ce:
    bpl.s loc_a8d2
loc_a8d0:
    move.w (sp),d1
loc_a8d2:
    move.l a0,-(sp)
    bsr.s sub_a89e
loc_a8d6:
    movea.l (sp)+,a0
    bra.s loc_a8ca
loc_a8da:
    addq.l #2,sp
    rts
pcref_a8de:
    dc.b    $1b
    dc.b    "[33;7m"
    dc.b    $ff,$1b,$5b,$30,$6d,$00,$00
call_write:
    move.l d1,-(sp)
    exg
    move.l a0,d2
    moveq #_LVOWrite,d0
    bsr.w dos_dispatch_b0d6
loc_a8f8:
    bsr.w check_signals
loc_a8fc:
    cmp.l (sp)+,d1
    rts
loc_a900:
    cmp.l app_output_file(a6),d3
    beq.s loc_a90e
loc_a906:
    move.l d3,d1
    moveq #_LVOClose,d0
    bsr.w dos_dispatch_b0d6
loc_a90e:
    rts
init_app:
    movea.l (sp)+,a3
    clr.b -1(a0,d0.l)
    movea.l a0,a4
    moveq #MEMF_PUBLIC,d1 ; AllocMem: attributes
    move.l #$1140,d0 ; AllocMem: byteSize
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_a928:
    tst.l d0
    bne.s loc_a930
loc_a92c:
    moveq #103,d0
    rts
loc_a930:
    movea.l d0,a6
    addq.l #2,a6
    clr.l 418(a6) ; app+$1A2
    clr.l app_output_file(a6)
    lea openlibrary_libname(pc),a1 ; OpenLibrary: libName
    moveq #0,d0 ; OpenLibrary: version
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOOpenLibrary(a6) ; app-$228
loc_a94c:
    movea.l (sp)+,a6
    tst.l d0
    bne.s loc_a968
loc_a952:
    lea app_freemem_memoryblock(a6),a1 ; FreeMem: memoryBlock
    move.l #$1140,d0 ; FreeMem: byteSize
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_a964:
    moveq #127,d0
    rts
loc_a968:
    move.l d0,app_dos_base(a6)
    clr.b 3572(a6) ; app+$DF4
    move.l a4,552(a6) ; app+$228
    move.l sp,3294(a6) ; app+$CDE
    move.l #$1140,3562(a6) ; app+$DEA
    move.l a3,-(sp)
    bra.w loc_a890
loc_a986:
    movea.l d2,a0
    cmpi.l #$44455620,(a0) ; 'DEV '
    bne.s loc_a9b8
loc_a990:
    move.l a0,418(a6) ; app+$1A2
    clr.l 18(a0)
    clr.l 22(a0)
    clr.l 26(a0)
    clr.l 30(a0)
    tst.b 16(a0)
    bne.s loc_a9b8
loc_a9aa:
    lea 18(a0),a0
    move.l a0,410(a6) ; app+$19A
    addq.w #4,a0
    move.l a0,414(a6) ; app+$19E
loc_a9b8:
    moveq #0,d0
    rts
open_device:
    movea.l 552(a6),a0 ; app+$228
    move.b (a0),d0
    cmp.b #$3f,d0
    bne.s loc_aa08
loc_a9c8:
    lea str_aab6(pc),a0
    bsr.w sub_9292
loc_a9d0:
    bsr.w call_output
loc_a9d4:
    move.l #$100,d1
    bsr.w sub_90ba
loc_a9de:
    move.l a0,-(sp)
    moveq #_LVOInput,d0
    bsr.w dos_dispatch_b0d6
loc_a9e6:
    move.l d0,d1
    move.l (sp),d2
    move.l #$100,d3
    moveq #_LVORead,d0
    bsr.w dos_dispatch_b0d6
loc_a9f6:
    cmp.b #$1,d0
    ble.w loc_aaae
loc_a9fe:
    movea.l (sp)+,a0
    move.l a0,552(a6) ; app+$228
    clr.b -1(a0,d0.w)
loc_aa08:
    sf 2112(a6) ; app+$840
    sf 2113(a6) ; app+$841
    sf 2114(a6) ; app+$842
    jsr sub_ab00
loc_aa1a:
    clr.b 1818(a6) ; app+$71A
    clr.b 539(a6) ; app+$21B
    sf 3110(a6) ; app+$C26
    st 259(a6) ; app+$103
    sf 254(a6) ; app+$FE
    sf 255(a6) ; app+$FF
    sf 256(a6) ; app+$100
    lea opendevice_devname(pc),a0 ; OpenDevice: devName
    moveq #0,d0
    lea app_timer_device_iorequest(a6),a1 ; OpenDevice: iORequest
    moveq #0,d0 ; OpenDevice: unitNumber
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOOpenDevice(a6) ; app-$1BC
loc_aa4c:
    movea.l (sp)+,a6
    tst.b d0
    bne.s loc_aa70
loc_aa52:
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a0
    cmpi.w #$24,LIB_VERSION(a0)
    bcs.w loc_aa70
loc_aa60:
    lea app_subtime_src(a6),a0 ; GetSysTime: dest
    pea (a6)
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVOGetSysTime(a6) ; app-$42
loc_aa6e:
    movea.l (sp)+,a6
loc_aa70:
    move.w #$3,540(a6) ; app+$21C
    clr.l 556(a6) ; app+$22C
    clr.l 560(a6) ; app+$230
    tst.l 418(a6) ; app+$1A2
    bne.s loc_aa9c
loc_aa84:
    lea str_aaf4(pc),a0
    bsr.w sub_b0ac
loc_aa8c:
    bne.s loc_aa98
loc_aa8e:
    lea str_aae9(pc),a0
    bsr.w sub_b0ac
loc_aa96:
    beq.s loc_aa9c
loc_aa98:
    move.l a0,556(a6) ; app+$22C
loc_aa9c:
    moveq #0,d0
    rts
opendevice_devname:
    dc.b    "timer.device",0
    dc.b    $00
loc_aaae:
    bsr.w sub_90f2
loc_aab2:
    bra.w cleanup_app
str_aab6:
    dc.b    "FROM/A,TO/K,WITH/K,INCDIR/K/M,HEADER/K/M,QUIET/S: ",0
str_aae9:
    dc.b    "ENV:devpac/"
str_aaf4:
    dc.b    "genam.opts",0
    dc.b    $00
sub_ab00:
    movea.l 552(a6),a4 ; app+$228
    bra.w loc_ab16
sub_ab08:
    move.l 560(a6),d0 ; app+$230
    bra.s loc_ab12
sub_ab0e:
    move.l 556(a6),d0 ; app+$22C
loc_ab12:
    beq.s loc_ab28
loc_ab14:
    movea.l d0,a4
loc_ab16:
    jsr sub_3a6c
loc_ab1c:
    bne.w loc_ab28
loc_ab20:
    tst.b d1
    beq.s loc_ab28
loc_ab24:
    move.b (a4),d1
    bne.s loc_ab16
loc_ab28:
    rts
sub_ab2a:
    rts
loc_ab2c:
    move.l a0,d1
    move.l #$3ee,d2
    move.l d3,-(sp)
    moveq #0,d3
    moveq #_LVOOpen,d0
    bsr.w dos_dispatch_b0d6
loc_ab3e:
    move.l (sp)+,d3
    tst.l d0
    beq.w loc_ab4a
loc_ab46:
    move.l d0,app_open_file(a6)
loc_ab4a:
    eori.b
    rts
sub_ab50:
    tst.b 2389(a6) ; app+$955
    beq.s loc_ab84
sub_ab56:
    tst.w 2920(a6) ; app+$B68
    bmi.s loc_ab84
loc_ab5c:
    moveq #10,d1
    bsr.w sub_917c
loc_ab62:
    move.l app_open_file(a6),d1
    cmp.l app_output_file(a6),d1
    beq.s loc_ab7a
loc_ab6c:
    cmpi.w #$2a00,1934(a6) ; app+$78E
    beq.s loc_ab7a
loc_ab74:
    moveq #12,d1
    bsr.w sub_917c
loc_ab7a:
    clr.w 2918(a6) ; app+$B66
    move.w #$ffff,2920(a6) ; app+$B68
loc_ab84:
    rts
check_signals:
    movem.l d0-d2/a0-a2,-(sp)
    moveq #0,d0 ; SetSignal: newSignals
    moveq #0,d1 ; SetSignal: signalMask
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSetSignal(a6) ; app-$132
loc_ab98:
    movea.l (sp)+,a6
    btst #12,d0
    beq.s loc_abba
loc_aba0:
    ori.b #$7f,277(a6) ; app+$115
    moveq #0,d0 ; SetSignal: newSignals
    move.l #SIGBREAKF_CTRL_C,d1 ; SetSignal: signalMask
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSetSignal(a6) ; app-$132
loc_abb8:
    movea.l (sp)+,a6
loc_abba:
    movem.l (sp)+,d0-d2/a0-a2
loc_abbe:
    rts
call_closedevice:
    tst.b 295(a6) ; app+$127
    bne.s loc_abbe
loc_abc6:
    move.l 3562(a6),d1 ; app+$DEA
    bsr.w sub_8f04
loc_abce:
    lea str_ac70(pc),a0
    bsr.w sub_9292
loc_abd6:
    tst.b app_timer_device_iorequest+IO_ERROR(a6)
    bne.w loc_ac68
loc_abde:
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a0
    cmpi.w #$24,LIB_VERSION(a0)
    bcs.w loc_ac58
loc_abec:
    lea app_subtime_dest(a6),a0 ; GetSysTime: dest
    pea (a6)
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVOGetSysTime(a6) ; app-$42
loc_abfa:
    movea.l (sp)+,a6
    lea app_subtime_dest(a6),a0 ; SubTime: dest
    lea app_subtime_src(a6),a1 ; SubTime: src
    pea (a6)
    movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVOSubTime(a6) ; app-$30
loc_ac0e:
    movea.l (sp)+,a6
    lea str_ac7c(pc),a0
    bsr.w sub_9292
loc_ac18:
    move.l app_subtime_dest(a6),d1
    bsr.w sub_8f04
loc_ac20:
    moveq #46,d1
    bsr.w loc_9288
loc_ac26:
    clr.l -(sp)
    clr.l -(sp)
    move.l #$30303030,d0 ; '0000'
    move.l d0,-(sp)
    move.w d0,-(sp)
    lea 6(sp),a3
    lea loc_ac6c(pc),a2
    move.l app_subtime_dest+TV_MICRO(a6),d1
    bsr.w sub_8f08
loc_ac44:
    lea -6(a3),a0
    dc.b    $61,$00,$e6,$48
loc_ac4c:
    lea 14(sp),sp
    lea str_ac84(pc),a0
    bsr.w sub_9292
loc_ac58:
    lea app_timer_device_iorequest(a6),a1 ; CloseDevice: ioRequest
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOCloseDevice(a6) ; app-$1C2
loc_ac66:
    movea.l (sp)+,a6
loc_ac68:
    bra.w sub_8e8c
loc_ac6c:
    move.b d1,(a3)+
    rts
str_ac70:
    dc.b    " bytes used",0
str_ac7c:
    dc.b    ", took ",0
str_ac84:
    dc.b    " seconds",0
str_ac8d:
    dc.b    "Press any key to exit",0
    dc.b    $00
cleanup_app:
    bsr.w call_output
loc_aca8:
    tst.b 3110(a6) ; app+$C26
    beq.s loc_acc2
loc_acae:
    lea str_ac8d(pc),a0
    move.l a0,d2
    moveq #21,d3
    move.l app_output_file(a6),d1
    moveq #_LVOWrite,d0
    bsr.w dos_dispatch_b0d6
loc_acc0:
    bsr.s call_input
loc_acc2:
    movea.l 3294(a6),sp ; app+$CDE
    movea.l app_dos_base(a6),a1 ; CloseLibrary: library
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOCloseLibrary(a6) ; app-$19E
loc_acd4:
    movea.l (sp)+,a6
    move.b 570(a6),d4 ; app+$23A
    lea app_freemem_memoryblock(a6),a1 ; FreeMem: memoryBlock
    move.l #$1140,d0 ; FreeMem: byteSize
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_acec:
    move.b d4,d0
    ext.w d0
    ext.l d0
    rts
call_input:
    moveq #_LVOInput,d0
    bsr.w dos_dispatch_b0d6
loc_acfa:
    move.l d0,d1
    clr.w -(sp)
    move.l sp,d2
    moveq #1,d3
    moveq #_LVORead,d0
    bsr.w dos_dispatch_b0d6
loc_ad08:
    move.b (sp)+,d1
    rts
call_datestamp:
    lea -12(sp),sp
    move.l sp,d1
    move.l #_LVODateStamp,d0
    bsr.w dos_dispatch_b0d6
loc_ad1c:
    move.l (sp),d0
    lea 12(sp),sp
    divu.w #$5b5,d0
    add.w d0,d0
    add.w d0,d0
    addi.w #$4e,d0
    move.w d0,d1
    swap d0
loc_ad32:
    tst.w d0
    beq.s loc_ad52
loc_ad36:
    move.w #$16d,d2
    btst #1,d1
    bne.s loc_ad48
loc_ad40:
    btst #0,d1
    bne.s loc_ad48
loc_ad46:
    addq.w #1,d2
loc_ad48:
    cmp.w d2,d0
    blt.s loc_ad52
loc_ad4c:
    sub.w d2,d0
    addq.w #1,d1
    bra.s loc_ad32
loc_ad52:
    addq.w #1,d0
    lea pcref_add2(pc),a0
    moveq #1,d4
loc_ad5a:
    moveq #0,d2
    move.b (a0)+,d2
    cmp.b #$2,d4
    bne.s loc_ad72
loc_ad64:
    btst #0,d1
    bne.s loc_ad72
loc_ad6a:
    btst #1,d1
    bne.s loc_ad72
loc_ad70:
    addq.w #1,d2
loc_ad72:
    cmp.w d2,d0
    ble.s loc_ad80
loc_ad76:
    sub.w d2,d0
    addq.w #1,d4
    cmp.w #$d,d4
    bne.s loc_ad5a
loc_ad80:
    move.w d1,-(sp)
    move.w d4,d1
    add.w d1,d1
    add.w d4,d1
    lea pcref_addb(pc,d1.w),a0
    move.w (sp)+,d1
    move.b (a0)+,(a3)+
    move.b (a0)+,(a3)+
    move.b (a0)+,(a3)+
    move.b #$20,(a3)+
    cmp.w #$a,d0
    blt.s loc_ada2
loc_ad9e:
    bsr.s sub_adbc
loc_ada0:
    bra.s loc_ada4
loc_ada2:
    bsr.s sub_adca
loc_ada4:
    move.b #$20,(a3)+
    move.w d1,d0
    ext.l d0
    addi.w #$76c,d0
    divu.w #$64,d0
    move.l d0,d1
    bsr.s sub_adbc
loc_adb8:
    move.l d1,d0
    swap d0
sub_adbc:
    swap d0
    clr.w d0
    swap d0
    divu.w #$a,d0
    bsr.s sub_adca
loc_adc8:
    swap d0
sub_adca:
    addi.b #$30,d0
    move.b d0,(a3)+
    rts
pcref_add2:
    dc.b    $1f,$1c,$1f,$1e,$1f,$1e,$1f,$1f,$1e
pcref_addb:
    dc.b    $1f,$1e,$1f
    dc.b    "JanFebMarAprMayJunJulAugSepOctNovDec"
alloc_memory:
    addq.l #8,d1
    movem.l d1/a1,-(sp)
    rol.w #3,d0 ; AllocMem: byteSize
    andi.l #$6,d0
    ori.l #$10001,d0
    exg
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_ae22:
    movea.l (sp)+,a6
    movem.l (sp)+,d1/a1
    tst.l d0
    beq.s loc_ae3e
loc_ae2c:
    movea.l d0,a0
    move.l d1,(a0)+
    lsr.l #2,d0
    addq.l #1,d0
    move.l d0,(a4)
    movea.l a0,a4
    clr.l (a0)+
    moveq #0,d0
    rts
loc_ae3e:
    moveq #-1,d0
    rts
alloc_memory_ae42:
    addq.l #4,d1
    move.l d1,-(sp)
    move.l d1,d0 ; AllocMem: byteSize
    moveq #MEMF_PUBLIC,d1 ; AllocMem: attributes
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_ae54:
    movea.l (sp)+,a6
    move.l (sp)+,d1
    tst.l d0
    beq.s loc_ae64
loc_ae5c:
    movea.l d0,a0
    move.l d1,(a0)+
    add.l d1,3562(a6) ; app+$DEA
loc_ae64:
    rts
free_memory:
    movea.l a0,a1 ; FreeMem: memoryBlock
    move.l -(a1),d0 ; FreeMem: byteSize
    sub.l d0,3562(a6) ; app+$DEA
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_ae78:
    movea.l (sp)+,a6
    rts
sub_ae7c:
    lea 22(a1),a0
    moveq #0,d0
    move.b (a0)+,d0
    lea -1(a0,d0.w),a1
    clr.b (a1)
    move.l a1,-(sp)
    bsr.s sub_aeb4
loc_ae8e:
    movea.l (sp)+,a1
    move.b #$b,(a1)
    tst.l d4
    eori.b
    rts
sub_ae9c:
    movem.l d1/a0,-(sp)
loc_aea0:
    move.b (a0)+,d1
    cmp.b #$3a,d1
    beq.s loc_aeae
loc_aea8:
    tst.b d1
    bne.s loc_aea0
loc_aeac:
    moveq #-1,d1
loc_aeae:
    movem.l (sp)+,d1/a0
loc_aeb2:
    rts
sub_aeb4:
    bsr.s sub_ae9c
loc_aeb6:
    beq.s sub_aefe
loc_aeb8:
    move.l a0,-(sp)
    bsr.w sub_aefe
loc_aebe:
    movea.l (sp)+,a0
    tst.l d4
    bne.s loc_aeb2
loc_aec4:
    movea.l 3116(a6),a2 ; app+$C2C
    move.l a0,-(sp)
loc_aeca:
    move.b (a0)+,(a2)+
    bne.s loc_aeca
loc_aece:
    move.l 2098(a6),-(sp) ; app+$832
    lea 3120(a6),a0 ; app+$C30
loc_aed6:
    bsr.s sub_aefe
loc_aed8:
    movea.l (sp)+,a1
    movea.l (sp)+,a0
    tst.l d4
    bne.s loc_aefc
loc_aee0:
    tst.b (a1)
    beq.s loc_aefc
loc_aee4:
    move.l a0,-(sp)
    lea 3704(a6),a2 ; app+$E78
loc_aeea:
    move.b (a1)+,(a2)+
    bne.s loc_aeea
loc_aeee:
    subq.l #1,a2
loc_aef0:
    move.b (a0)+,(a2)+
    bne.s loc_aef0
loc_aef4:
    move.l a1,-(sp)
    lea 3704(a6),a0 ; app+$E78
    bra.s loc_aed6
loc_aefc:
    rts
sub_aefe:
    tst.b 266(a6) ; app+$10A
    beq.s call_close
loc_af04:
    lea 4328(a6),a2 ; app+$10E8
    move.l a0,-(sp)
loc_af0a:
    move.b (a0)+,(a2)+
    bne.s loc_af0a
loc_af0e:
    lea 4328(a6),a0 ; app+$10E8
    lea str_9656(pc),a2
    bsr.w sub_45ce
loc_af1a:
    bsr.w call_close
loc_af1e:
    movea.l (sp)+,a0
    tst.l d4
    beq.s call_close
loc_af24:
    neg.l d1
    rts
call_close:
    move.l a0,-(sp)
    move.l a0,d1
    move.l #MODE_OLDFILE,d2
    moveq #_LVOOpen,d0
    bsr.w dos_dispatch_b0d6
loc_af38:
    move.l (sp)+,d1
    move.l d0,d4
    beq.w loc_afb6
loc_af40:
    move.l 418(a6),d0 ; app+$1A2
    beq.s loc_af52
loc_af46:
    movea.l d0,a0
    tst.l 8(a0)
    beq.s loc_af52
loc_af4e:
    moveq #-1,d1
    rts
loc_af52:
    move.l d4,-(sp)
    moveq #ACCESS_READ,d2
    moveq #_LVOLock,d0
    bsr.w dos_dispatch_b0d6
loc_af5c:
    move.l d0,d4
    beq.w loc_af8a
loc_af62:
    move.l d0,d1
    lea 3298(a6),a0 ; app+$CE2
    move.l a0,d2
    move.l d2,d0
    andi.b #$3,d0
    beq.s loc_af78
loc_af72:
    andi.b #$fc,d2
    addq.l #4,d2
loc_af78:
    moveq #_LVOExamine,d0
    bsr.w dos_dispatch_b0d6
loc_af7e:
    move.l d0,-(sp)
    move.l d4,d1
    moveq #_LVOUnLock,d0
    bsr.w dos_dispatch_b0d6
loc_af88:
    move.l (sp)+,d0
loc_af8a:
    movem.l (sp)+,d4
    beq.s loc_afac
loc_af90:
    lea 3298(a6),a0 ; app+$CE2
    move.l a0,d0
    move.l d0,d2
    andi.b #$3,d2
    beq.s loc_afa4
loc_af9e:
    andi.b #$fc,d0
    addq.l #4,d0
loc_afa4:
    movea.l d0,a0
    move.l 124(a0),d1
    bne.s loc_afb6
loc_afac:
    move.l d4,d1
    moveq #_LVOClose,d0
    bsr.w dos_dispatch_b0d6
loc_afb4:
    moveq #0,d4
loc_afb6:
    rts
call_close_afb8:
    move.l d2,d1
    moveq #_LVOClose,d0
    bsr.w dos_dispatch_b0d6
loc_afc0:
    rts
call_read:
    move.l d3,-(sp)
    move.l d1,d3
    move.l d2,d1
    move.l a0,d2
    moveq #_LVORead,d0
    bsr.w dos_dispatch_b0d6
loc_afd0:
    tst.l d0
    bmi.s loc_afd8
loc_afd4:
    move.l d0,d1
    moveq #0,d0
loc_afd8:
    movem.l (sp)+,d3
    rts
sub_afde:
    move.l d4,-(sp)
    bsr.w sub_aeb4
loc_afe4:
    move.l d1,d2
    move.l d4,d3
    movem.l (sp)+,d4
    eori.b
    rts
sub_aff2:
    move.l d3,d2
    bra.s call_close_afb8
call_read_aff6:
    exg
    move.l a0,d2
    moveq #_LVORead,d0
    bsr.w dos_dispatch_b0d6
loc_b000:
    rts
call_open:
    move.l a0,d1
    move.l #$3ee,d2
    move.l d3,-(sp)
    moveq #-1,d3
    moveq #_LVOOpen,d0
    bsr.w dos_dispatch_b0d6
loc_b014:
    move.l (sp)+,d3
    tst.l d0
    beq.s loc_b020
loc_b01a:
    move.l d0,d2
    moveq #0,d0
    rts
loc_b020:
    moveq #-1,d0
    rts
call_write_b024:
    tst.l d1
    beq.s loc_b040
loc_b028:
    movem.l d1-d3,-(sp)
    move.l d1,d3
    move.l 390(a6),d1 ; app+$186
    move.l a0,d2
    moveq #_LVOWrite,d0
    bsr.w dos_dispatch_b0d6
loc_b03a:
    movem.l (sp)+,d1-d3
    cmp.l d0,d1
loc_b040:
    rts
call_seek:
    move.l d3,-(sp)
    moveq #OFFSET_BEGINNING,d3
    move.l 390(a6),d1 ; app+$186
    moveq #_LVOSeek,d0
    bsr.w dos_dispatch_b0d6
loc_b050:
    move.l (sp)+,d3
    rts
call_seek_b054:
    move.l d3,-(sp)
    move.l 390(a6),d1 ; app+$186
    moveq #0,d2
    moveq #OFFSET_CURRENT,d3
    moveq #_LVOSeek,d0
    bsr.w dos_dispatch_b0d6
loc_b064:
    move.l (sp)+,d3
    rts
check_memory:
    tst.b 539(a6) ; app+$21B
    bne.s loc_b09a
loc_b06e:
    movem.l d1-d2/a0-a2,-(sp)
    move.l #$20001,d1 ; AvailMem: attributes
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAvailMem(a6) ; app-$D8
loc_b082:
    movea.l (sp)+,a6
    movem.l (sp)+,d1-d2/a0-a2
    cmp.l #$7d00,d0
    bcs.s loc_b096
loc_b090:
    asr.l #1,d0
    cmp.l d0,d1
    bcs.s loc_b098
loc_b096:
    move.l d2,d1
loc_b098:
    rts
loc_b09a:
    cmp.l d2,d1
    ble.s loc_b098
loc_b09e:
    bra.s loc_b096
openlibrary_libname:
    dc.b    "dos.library",0
sub_b0ac:
    bsr.w call_close
loc_b0b0:
    tst.l d4
    beq.s loc_b0d4
loc_b0b4:
    move.l d1,d5
    addq.l #1,d1
    bsr.w sub_90ba
loc_b0bc:
    move.l d5,d1
    move.l d4,d3
    move.l a0,-(sp)
    bsr.w call_read_aff6
loc_b0c6:
    move.l d4,d3
    bsr.w sub_aff2
loc_b0cc:
    movea.l (sp)+,a0
    clr.b 0(a0,d5.l)
    tst.l d5
loc_b0d4:
    rts
dos_dispatch_b0d6:
    move.l a6,-(sp)
    tst.l 418(a6) ; app+$1A2
    beq.s loc_b0f0
loc_b0de:
    movea.l 418(a6),a0 ; app+$1A2
    movea.l 4(a0),a0
    movea.l app_dos_base(a6),a6
    jsr (a0) ; unresolved_indirect_core:ind
loc_b0ec:
    movea.l (sp)+,a6
    rts
loc_b0f0:
    movea.l app_dos_base(a6),a6
    jsr 0(a6,d0.w) ; unresolved_indirect_core:index.brief
loc_b0f8:
    movea.l (sp)+,a6
    rts
sub_b0fc:
; --- unverified ---
    tst.b 3572(a6) ; app+$DF4
    bne.s hint_b124
hint_b102:
; --- unverified ---
    movem.l d0/a0,-(sp)
    movea.l AbsExecBase,a0
    move.b 297(a0),d0
    btst #4,d0
    beq.s hint_b126
hint_b114:
; --- unverified ---
    btst #1,d0
    beq.s hint_b126
hint_b11a:
    dc.b    $1d,$7c,$00,$01,$0d,$f4,$4c,$df,$01,$01
hint_b124:
; --- unverified ---
    rts
hint_b126:
; --- unverified ---
    moveq #96,d0
    bra.w loc_846e
hint_b12c:
; --- unverified ---
    tst.w d5
    beq.s sub_b166
hint_b130:
; --- unverified ---
    bsr.s sub_b0fc
    dc.b    $f2,$3c,$88
    dcb.b   5,0
    dc.b    $ba,$7c,$00,$0a,$64,$00,$00,$56,$ca,$fc,$03,$e8,$08,$10,$00,$06
    dc.b    $67,$02,$44,$45,$f2,$3c,$50,$80,$00,$01,$f2,$05,$50,$92,$f2,$10
    dc.b    $4c,$00,$f2,$00,$04,$23,$60,$00,$00,$1e,$4e,$75
sub_b166:
    dc.b    $70,$05
hint_b168:
; --- unverified ---
    move.w d0,-(sp)
    bsr.s sub_b0fc
    dc.b    $f2,$3c,$88
    dcb.b   5,0
    dc.b    $30,$1f,$48,$80,$c0,$fc,$00,$06,$61,$00,$00,$20,$30,$03,$d0,$40
    dc.b    $d0,$43,$d0,$40,$61,$00,$00,$18,$f2,$00,$a8,$00
sub_b190:
; --- unverified ---
    btst #6,d0
    beq.s hint_b19a
hint_b196:
; --- unverified ---
    moveq #99,d0
    rts
hint_b19a:
; --- unverified ---
    moveq #0,d0
    rts
hint_b19e:
; --- unverified ---
    jmp pcref_b1ca(pc,d0.w) ; unresolved_indirect_hint:pcindex.brief
    dc.b    $4e,$fb,$00,$fc,$f2,$10,$78,$00,$4e,$75,$f2,$10,$70,$00,$4e,$75
    dc.b    $f2,$10,$60,$00,$4e,$75,$f2,$10,$74,$00,$4e,$75,$f2,$10,$6c,$00
    dc.b    $4e,$75,$f2,$10,$64,$00,$4e,$75
pcref_b1ca:
    dc.b    $f2,$10,$68,$00,$4e,$75,$f2,$10,$58,$00,$4e,$75,$f2,$10,$50,$00
    dc.b    $4e,$75,$f2,$10,$40,$00,$4e,$75,$f2,$10,$54,$00,$4e,$75,$f2,$10
    dc.b    $4c,$00,$4e,$75,$f2,$10,$44,$00,$4e,$75,$f2,$10,$48,$00,$4e,$75
sub_b1fa:
; --- unverified ---
    move.w d3,-(sp)
    bsr.w sub_b0fc
    dc.b    $f2,$3c,$88
    dcb.b   5,0
    dc.b    $36,$1f,$48,$83,$30,$03,$d0,$40,$d0,$43,$d0,$40,$61,$88,$f2,$00
    dc.b    $00,$1a,$60,$00,$ff,$6c
sub_b21e:
    dcb.b   5,0
    dc.b    $6e,$00,$76,$00,$d6,$00,$fc,$00,$ee,$01,$62,$01,$84,$00,$86,$01
    dc.b    $d0,$01,$dc,$01,$ce,$01,$d8,$02,$46,$02,$52,$02,$b8,$03,$26,$00
    dc.b    $1c,$00,$80,$00,$34,$00,$36,$00,$a2,$00,$e0,$03,$8a,$00,$98,$03
    dc.b    $52,$01,$e4
    dc.b    $00,$f6,$00,$f2,$03,$8c,$01,$02,$01,$0c,$01,$08,$01,$56,$02,$34
    dc.b    $01,$48,$01,$ce,$01,$5e,$01,$5c,$01,$5c,$01,$6a,$01,$ca,$01,$d4
    dc.b    $01,$fc,$02,$38,$02,$5a,$02,$3e,$03,$f0,$02,$64,$02,$48,$00,$00
    dc.b    $02,$50,$02,$78,$02,$68,$02,$6c,$02,$c0,$02,$d0,$04,$1c,$04,$6e
    dc.b    $02,$fc,$04,$98,$03,$3e,$02,$c4,$02,$c0,$02,$dc,$03,$1e,$03,$8a
    dc.b    $03,$a2,$03,$3a,$04,$fa,$04,$7e,$03,$90,$05,$22,$03,$a2,$03,$ac
    dc.b    $03,$c8,$03,$b2,$03,$ba,$03,$e4,$04,$0c,$03,$ee,$03,$f0,$04,$3a
    dc.b    $04,$14,$03,$fa,$04,$de,$04,$14,$04,$2a,$04,$26,$05,$46,$04,$42
    dc.b    $04,$3e,$05,$24,$04,$4e,$04,$a2,$05,$7e,$04,$8c,$04,$ac,$04,$b6
    dc.b    $05,$6a,$04,$c0,$04,$ee,$05,$d8,$05,$6e,$05,$0e,$05,$12,$05,$6e
    dc.b    $05,$ca,$05,$ce,$05,$ee,$05,$80,$05,$da,$05,$e2,$00,$00,$06,$04
    dc.b    $05,$ea,$06,$38,$05,$86,$06,$02,$06,$52,$06,$06,$06,$56,$06,$56
    dc.b    $06,$60,$06,$40,$06,$50,$06,$68,$06,$5e,$06,$50,$00,$00,$06,$6a
    dc.b    $06,$64,$06,$a2,$06,$66,$06,$70,$06,$ce,$06,$7c,$06,$5c,$06,$6e
    dc.b    $06,$bc,$06,$d8,$06,$82,$06,$9a,$06,$ce,$07,$22,$06,$ce
    dcb.b   6,0
    dc.b    $06,$e4,$06,$d8
    dcb.b   4,0
    dc.b    $06,$ee,$06,$d0,$07,$00,$06,$f2,$07,$06,$07,$06,$00,$00,$07,$3a
    dcb.b   4,0
    dc.b    $07,$20
    dcb.b   14,0
    dc.b    $07,$22
    dcb.b   4,0
    dc.b    $07,$2c
    dcb.b   4,0
    dc.b    $07,$3e,$07,$4a,$00,$02,$00,$04,$07,$2e,$00,$00,$07,$8a,$07,$3e
    dc.b    $07,$56,$07,$48,$07,$40,$07,$62,$07,$68,$07,$6a,$07,$50,$00,$00
    dc.b    $07,$84,$07,$9c,$07,$ac,$07,$66,$07,$70,$07,$64,$07,$7c,$00,$00
    dc.b    $07,$ba,$00,$00,$07,$9e,$07,$7c,$07,$d0,$07,$c6,$07,$d4,$07,$be
    dc.b    $00,$00,$07,$e2,$07,$c2,$07,$d2,$07,$ea,$07,$e2,$07,$ea,$07,$fc
    dc.b    $07,$e4,$00,$00,$08,$04,$08,$1a,$08,$3a,$08,$28,$08,$4a,$00,$00
    dc.b    $08,$60,$08,$2a,$08,$32,$08,$56,$08,$b4,$08,$4e,$08,$36,$08,$4a
    dc.b    $08,$66,$08,$64,$08,$50,$08,$86,$08,$84,$08,$8e,$08,$b6,$08,$c2
    dc.b    $08,$b0,$08,$c6,$08,$b6,$08,$b8,$08,$c8,$08,$cc,$09,$20,$08,$e8
    dc.b    $08,$de,$08,$d2,$00,$00,$09,$22,$08,$dc,$09,$2c,$09,$1e,$09,$36
    dc.b    $09,$38,$09,$1a,$09,$8c,$00,$00,$09,$a2,$09,$26,$09,$36,$09,$58
    dc.b    $09,$36,$09,$42,$09,$3a
    dcb.b   4,0
    dc.b    $09,$48,$09,$9a,$09,$a8,$09,$be,$00,$00,$09,$6e,$09,$c6
    dcb.b   6,0
    dc.b    $09,$a6,$09,$98,$09,$b0,$09,$aa
    dcb.b   4,0
    dc.b    $0a,$04,$09,$c8,$09,$b2,$09,$d6,$09,$fc,$09,$e2,$09,$c8,$0a,$04
    dc.b    $0a,$16,$00,$00,$09,$fe
    dcb.b   6,0
    dc.b    $0a,$0c,$0a,$18,$0a,$26,$0a,$2c,$0a,$34,$0a,$36,$0a,$38,$0a,$3a
    dc.b    $0a,$44,$0a,$6e,$0a,$70,$0a,$a0,$00,$00,$0a,$18,$0a,$28,$0a,$44
    dc.b    $0a,$46,$0a,$20,$0a,$28,$0a,$a6,$0a,$8a,$0a,$a2,$0a,$b4,$0a,$b6
    dc.b    $0a,$b8,$0a,$ba,$0a,$c4,$0a,$72,$0a,$c0,$0a,$ac,$0a,$e2,$00,$00
    dc.b    $0a,$ce,$0b,$06,$00,$00,$0b,$06,$0a,$fe,$0b,$0e,$0b,$1a
    dcb.b   10,0
    dc.b    $0b,$1e
    dcb.b   4,0
    dc.b    $0b
    dcb.b   25,0
    dc.b    $0b,$0c,$0b,$48
    dcb.b   4,0
    dc.b    $0b,$0e,$00,$00,$0b,$14
    dcb.b   4,0
    dc.b    $0b,$06,$00,$00,$0b,$14
    dcb.b   16,0
    dc.b    $0b,$1e,$0b,$38,$0b,$32,$0b,$2e,$00,$00,$0b,$28
    dcb.b   8,0
    dc.b    $0b,$36,$0b,$38,$0b,$46,$0b,$50
    dcb.b   16,0
    dc.b    $0b,$66,$0b,$52,$0b,$68,$0b,$76,$0b,$70,$0b,$70,$0b,$7a
    dcb.b   8,0
    dc.b    $0b,$8a,$0b,$80
    dcb.b   4,0
    dc.b    $0b,$a6
    dcb.b   12,0
    dc.b    $0b,$a2,$0b,$9e,$0b,$8a
    dcb.b   32,0
    dc.b    $0b,$a2,$0b,$a4,$0b,$ae,$00,$00,$0b,$b6
    dcb.b   6,0
    dc.b    $0b,$a8
    dcb.b   10,0
    dc.b    $0b,$a2
    dcb.b   4,0
    dc.b    $0b,$ae,$0b,$b0
    dcb.b   4,0
    dc.b    $0b,$c4
    dcb.b   8,0
    dc.b    $0b,$c8,$0b,$d0,$0c,$06,$0b,$ec,$00,$00,$0b,$ba,$00,$00,$0b,$e0
    dc.b    $00,$00,$0b,$d2,$0c,$18,$0c,$1a
    dcb.b   4,0
    dc.b    $0c,$06,$0b,$f2,$0c,$1e,$0c,$06,$00,$00,$0c,$22,$0c,$32,$0c,$3a
    dc.b    $0c,$52,$0c,$30,$0c,$8a,$00,$00,$0c,$94,$0c,$12,$00,$00,$0c,$1a
    dc.b    $0c,$34,$0c,$40,$0c,$38,$0c,$70,$00,$00,$0c,$48,$0c,$8e,$0c,$6c
    dc.b    $0c,$d8,$00,$00,$0c,$9a
    dcb.b   8,0
    dc.b    $0c,$ac,$00,$00,$0c,$96,$0c,$9a,$0c,$ba,$0c,$ba,$0c,$ae,$0c,$9c
    dcb.b   4,0
    dc.b    $0c,$c2,$00,$00,$0c,$da
    dcb.b   4,0
    dc.b    $0c,$a2,$0c,$ba,$0c,$cc,$0d,$06,$0c,$ec,$0d,$18,$0c,$ee,$00,$00
    dc.b    $0c,$d2,$0c,$da,$00,$00,$0d,$0e,$0d,$00,$00,$00,$0d,$22,$00,$00
    dc.b    $0d,$06,$0d,$22,$0d,$34,$00,$00,$0d,$22,$0d,$1a,$0d,$24,$00,$00
    dc.b    $0d,$1e
    dcb.b   18,0
    dc.b    $0d,$3a,$0d,$3a,$0d,$3c,$0d,$28,$00,$00,$0d,$54,$00,$00,$0d,$42
    dc.b    $0d,$58,$0d,$56,$0d,$4e,$0d,$60,$0d,$bc
    dcb.b   8,0
    dc.b    $0d,$54,$0d,$6e,$0d,$86,$0d,$6a
    dcb.b   36,0
    dc.b    $0d,$9e,$0d,$a0,$0d,$a2,$0d,$a6,$0d,$a8,$0d,$ac,$0d,$ba,$0d,$c4
    dc.b    $0d,$72,$00,$00,$0d,$a8,$0d,$ec,$0d,$ea,$0d,$ce
    dcb.b   4,0
    dc.b    $0d,$ee
    dcb.b   28,0
    dc.b    $0d,$d2,$0d,$dc,$0e,$02,$0d,$e8,$00,$00,$0d,$fc
    dcb.b   6,0
    dc.b    $0e,$00,$0e,$00,$00,$00,$0e,$1a
    dcb.b   8,0
    dc.b    $0e,$06
    dcb.b   4,0
    dc.b    $0e,$14,$0e,$16,$0e,$18
    dcb.b   4,0
    dc.b    $0e,$7a
    dcb.b   12,0
    dc.b    $0e,$36
    dcb.b   18,0
    dc.b    $0e,$30,$0e,$5c
    dcb.b   6,0
    dc.b    $0e,$42,$00,$00,$0e,$3e
    dcb.b   4,0
    dc.b    $0e,$66
    dcb.b   4,0
    dc.b    $0e,$6e
    dcb.b   40,0
    dc.b    $0e,$70
    dcb.b   8,0
    dc.b    $0e,$9a,$0e,$86,$0e,$a6,$0e,$c2,$00,$00,$0e,$76,$00,$00,$0e,$9e
    dc.b    $00,$00,$0e,$8a,$0e,$d2,$0e,$d4
    dcb.b   4,0
    dc.b    $0e,$d6
    dcb.b   4,0
    dc.b    $0e,$cc,$00,$00,$0e,$dc,$0e,$c8,$0e,$fe,$0e,$d0,$00,$0a,$00,$00
    dc.b    $0e,$e6,$0f,$0a,$0e,$e0,$0e,$ec
    dcb.b   6,0
    dc.b    $0f,$08,$00,$00,$0f,$02,$00,$00,$0e,$ec,$0e,$fa,$00,$00,$0f,$10
    dcb.b   6,0
    dc.b    $0f,$18
    dcb.b   22,0
    dc.b    $0e,$fe
    dcb.b   14,0
    dc.b    $0f,$0a,$0f,$52,$0f,$0e,$0f,$30,$0f,$22,$0f,$1e,$0f,$44,$0f,$3e
    dc.b    $0f,$54,$0f,$5a
    dcb.b   4,0
    dc.b    $0f,$76,$00,$02
    dcb.b   12,0
    dc.b    $0f,$5c,$0f,$7c,$0f,$60,$0f,$62
    dcb.b   32,0
    dc.b    $0f,$80,$0f,$74
    dcb.b   4,0
    dc.b    $0f,$86,$0f,$76,$00,$00,$0f,$76,$0f,$da,$0f,$8e
    dcb.b   4,0
    dc.b    $0f,$9c,$00,$00,$0f,$a0,$0f,$aa
    dcb.b   8,0
    dc.b    $0f,$c8
    dcb.b   4,0
    dc.b    $0f,$a4
    dcb.b   10,0
pcref_b8bc:
    dcb.b   8,0
    dc.b    $0f,$e0
    dcb.b   35,0
    dc.b    $0e,$0f,$d0,$0f,$d8
    dcb.b   5,0
    dc.b    $10,$0f,$d2
    dcb.b   4,0
    dc.b    $0f,$d4,$00,$00,$0f,$ce,$0f,$e4,$0f,$de
    dcb.b   6,0
    dc.b    $0f,$d6,$0f,$e8,$00,$00,$10,$34,$10,$1a,$10,$0a,$10,$02,$10,$54
    dc.b    $00,$00,$10,$5e,$0f,$e2,$0f,$fe
    dcb.b   4,0
    dc.b    $10,$44,$10,$68,$00,$00,$10,$64
    dcb.b   12,0
    dc.b    $10,$7e
    dcb.b   4,0
    dc.b    $10,$6a,$10,$50
    dcb.b   4,0
    dc.b    $10,$72,$10,$80,$10,$b8,$10,$c2,$10,$c4,$10,$c6,$10,$c8,$10,$ca
    dc.b    $00,$00,$10,$5c,$10,$76
    dcb.b   16,0
    dc.b    $10,$8a
    dcb.b   12,0
    dc.b    $10,$8c
    dcb.b   8,0
    dc.b    $10,$ea,$10,$d2,$10,$ec,$10,$ee,$00,$00,$10,$be,$00,$00,$10,$e8
    dc.b    $00,$00,$10,$da,$10,$fc,$11,$18
    dcb.b   8,0
    dc.b    $10,$f4,$00,$00,$10,$fe
    dcb.b   8,0
    dc.b    $11,$1c
    dcb.b   42,0
    dc.b    $11,$34
    dcb.b   38,0
dat_ba08:
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$03,$40,$03,$42,$06,$d2,$ff,$ff,$07,$12
    dc.b    $07,$46,$07,$4c,$ff,$ff,$ff,$ff,$ff,$ff,$00,$02,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$00,$04,$00,$06,$00,$08,$00,$0a,$00,$0c,$00,$0e,$ff,$ff
    dc.b    $ff,$ff,$00,$10,$00,$12,$ff,$ff,$00,$14,$00,$16,$00,$18,$00,$1a
    dc.b    $00,$1c,$ff,$ff,$00,$1e,$00,$20,$00,$22,$00,$24,$ff,$ff,$ff,$ff
    dc.b    $00,$26,$ff,$ff,$ff,$ff,$ff,$ff,$01,$1a,$01,$20,$ff,$ff,$01,$22
    dc.b    $ff,$ff,$00,$04,$00,$06,$00,$08,$00,$0a,$00,$0c,$00,$0e,$ff,$ff
    dc.b    $ff,$ff,$00,$10,$00,$12,$ff,$ff,$00,$14,$00,$16,$00,$18,$00,$1a
    dc.b    $00,$1c,$ff,$ff,$00,$1e,$00,$20,$00,$22,$00,$24,$ff,$ff,$ff,$ff
    dc.b    $00,$26,$00,$28,$ff,$ff,$00,$2a,$01,$1a,$01,$20,$00,$30,$01,$22
    dc.b    $00,$32,$00,$34,$00,$36,$00,$38,$01,$1c,$00,$2c,$00,$3a,$00,$3c
    dc.b    $00,$3e,$00,$40,$00,$2e,$00,$42,$ff,$ff,$00,$44,$00,$46,$00,$48
    dc.b    $00,$9a,$00,$4a,$01,$1e,$ff,$ff,$ff,$ff,$01,$24,$00,$9c,$ff,$ff
    dc.b    $ff,$ff,$00,$28,$ff,$ff,$00,$2a,$ff,$ff,$01,$32,$00,$30,$ff,$ff
    dc.b    $00,$32,$00,$34,$00,$36,$00,$38,$01,$1c,$00,$2c,$00,$3a,$00,$3c
    dc.b    $00,$3e,$00,$40,$00,$2e,$00,$42,$00,$4c,$00,$44,$00,$46,$00,$48
    dc.b    $00,$9a,$00,$4a,$01,$1e,$00,$4e,$00,$50,$01,$24,$00,$9c,$00,$52
    dc.b    $00,$54,$00,$56,$00,$58,$00,$5a,$01,$26,$01,$32,$00,$5c,$00,$5e
    dc.b    $00,$60,$00,$62,$01,$28,$00,$68,$01,$46,$00,$6a,$00,$6c,$00,$64
    dc.b    $00,$6e,$01,$48,$01,$50,$01,$52,$00,$4c,$00,$70,$01,$2a,$00,$72
    dc.b    $01,$54,$00,$66,$ff,$ff,$00,$4e,$00,$50,$ff,$ff,$ff,$ff,$00,$52
    dc.b    $00,$54,$00,$56,$00,$58,$00,$5a,$01,$26,$ff,$ff,$00,$5c,$00,$5e
    dc.b    $00,$60,$00,$62,$01,$28,$00,$68,$01,$46,$00,$6a,$00,$6c,$00,$64
    dc.b    $00,$6e,$01,$48,$01,$50,$01,$52,$01,$56,$00,$70,$01,$2a,$00,$72
    dc.b    $01,$54,$00,$66,$00,$74,$00,$76,$00,$78,$00,$7a,$00,$7c,$01,$5e
    dc.b    $00,$7e,$01,$6a,$00,$80,$01,$64,$01,$6c,$00,$82,$00,$84,$00,$86
    dc.b    $00,$88,$01,$66,$01,$68,$00,$8a,$00,$8c,$00,$8e,$00,$90,$01,$6e
    dc.b    $00,$92,$ff,$ff,$ff,$ff,$00,$94,$01,$56,$ff,$ff,$00,$96,$ff,$ff
    dc.b    $00,$98,$ff,$ff,$00,$74,$00,$76,$00,$78,$00,$7a,$00,$7c,$01,$5e
    dc.b    $00,$7e,$01,$6a,$00,$80,$01,$64,$01,$6c,$00,$82,$00,$84,$00,$86
    dc.b    $00,$88,$01,$66,$01,$68,$00,$8a,$00,$8c,$00,$8e,$00,$90,$01,$6e
    dc.b    $00,$92,$00,$b0,$01,$60,$00,$94,$00,$b2,$00,$9e,$00,$96,$00,$a8
    dc.b    $00,$98,$00,$a0,$00,$b6,$00,$aa,$00,$a2,$01,$70,$00,$b4,$01,$40
    dc.b    $00,$a4,$01,$72,$01,$62,$00,$a6,$00,$b8,$00,$ac,$00,$ba,$ff,$ff
    dc.b    $01,$42,$00,$bc,$01,$74,$00,$ae,$ff,$ff,$ff,$ff,$01,$44,$ff,$ff
    dc.b    $ff,$ff,$00,$b0,$01,$60,$01,$76,$00,$b2,$00,$9e,$ff,$ff,$00,$a8
    dc.b    $ff,$ff,$00,$a0,$00,$b6,$00,$aa,$00,$a2,$01,$70,$00,$b4,$01,$40
    dc.b    $00,$a4,$01,$72,$01,$62,$00,$a6,$00,$b8,$00,$ac,$00,$ba,$01,$58
    dc.b    $01,$42,$00,$bc,$01,$74,$00,$ae,$00,$be,$00,$c0,$01,$44,$00,$c2
    dc.b    $00,$c4,$00,$c6,$00,$d4,$01,$76,$01,$5a,$01,$5c,$00,$d6,$00,$c8
    dc.b    $00,$ca,$01,$78,$01,$7a,$01,$7c,$01,$96,$00,$cc,$00,$ce,$00,$d0
    dc.b    $00,$d8,$00,$d2,$01,$98,$01,$9a,$00,$da,$00,$dc,$ff,$ff,$01,$58
    dc.b    $01,$9c,$ff,$ff,$ff,$ff,$ff,$ff,$00,$be,$00,$c0,$01,$9e,$00,$c2
    dc.b    $00,$c4,$00,$c6,$00,$d4,$01,$a0,$01,$5a,$01,$5c,$00,$d6,$00,$c8
    dc.b    $00,$ca,$01,$78,$01,$7a,$01,$7c,$01,$96,$00,$cc,$00,$ce,$00,$d0
    dc.b    $00,$d8,$00,$d2,$01,$98,$01,$9a,$00,$da,$00,$dc,$00,$de,$00,$e0
    dc.b    $01,$9c,$00,$e2,$00,$e4,$00,$e6,$00,$e8,$01,$a2,$01,$9e,$01,$dc
    dc.b    $00,$ea,$00,$ec,$00,$ee,$01,$a0,$00,$f0,$ff,$ff,$01,$de,$01,$a4
    dc.b    $00,$f2,$00,$f4,$00,$f6,$00,$f8,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$01,$a6,$01,$e0,$00,$de,$00,$e0
    dc.b    $ff,$ff,$00,$e2,$00,$e4,$00,$e6,$00,$e8,$01,$a2,$ff,$ff,$01,$dc
    dc.b    $00,$ea,$00,$ec,$00,$ee,$01,$c6,$00,$f0,$01,$c8,$01,$de,$01,$a4
    dc.b    $00,$f2,$00,$f4,$00,$f6,$00,$f8,$00,$fa,$00,$fc,$00,$fe,$01,$00
    dc.b    $01,$02,$01,$04,$01,$06,$01,$08,$01,$a6,$01,$e0,$01,$e2,$01,$0a
    dc.b    $01,$0c,$01,$0e,$01,$ee,$01,$10,$01,$e4,$01,$12,$01,$14,$01,$16
    dc.b    $ff,$ff,$01,$18,$ff,$ff,$01,$c6,$01,$34,$01,$c8,$01,$36,$01,$38
    dc.b    $01,$d8,$ff,$ff,$01,$3a,$01,$da,$00,$fa,$00,$fc,$00,$fe,$01,$00
    dc.b    $01,$02,$01,$04,$01,$06,$01,$08,$01,$3c,$01,$3e,$01,$e2,$01,$0a
    dc.b    $01,$0c,$01,$0e,$01,$ee,$01,$10,$01,$e4,$01,$12,$01,$14,$01,$16
    dc.b    $01,$2a,$01,$18,$01,$e6,$01,$4a,$01,$34,$01,$2c,$01,$36,$01,$38
    dc.b    $01,$d8,$01,$2e,$01,$3a,$01,$da,$01,$e8,$01,$30,$02,$18,$02,$26
    dc.b    $01,$30,$01,$4c,$01,$4e,$ff,$ff,$01,$3c,$01,$3e,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$01,$ea,$02,$28,$01,$ec,$ff,$ff,$ff,$ff,$ff,$ff,$02,$2a
    dc.b    $01,$2a,$02,$2c,$01,$e6,$01,$4a,$ff,$ff,$01,$2c,$ff,$ff,$02,$2e
    dc.b    $ff,$ff,$01,$2e,$ff,$ff,$02,$30,$01,$e8,$01,$30,$02,$18,$02,$26
    dc.b    $01,$30,$01,$4c,$01,$4e,$01,$7e,$02,$36,$01,$80,$01,$82,$01,$84
    dc.b    $01,$86,$01,$ea,$02,$28,$01,$ec,$01,$88,$01,$8a,$01,$8c,$02,$2a
    dc.b    $01,$8e,$02,$2c,$01,$90,$02,$38,$01,$92,$02,$3e,$01,$94,$02,$2e
    dc.b    $01,$a8,$01,$aa,$01,$ac,$02,$30,$02,$32,$02,$40,$02,$46,$01,$ae
    dc.b    $02,$48,$02,$34,$02,$4a,$01,$7e,$02,$36,$01,$80,$01,$82,$01,$84
    dc.b    $01,$86,$01,$b0,$01,$b2,$ff,$ff,$01,$88,$01,$8a,$01,$8c,$02,$52
    dc.b    $01,$8e,$02,$3a,$01,$90,$02,$38,$01,$92,$02,$3e,$01,$94,$02,$3c
    dc.b    $01,$a8,$01,$aa,$01,$ac,$02,$54,$02,$32,$02,$40,$02,$46,$01,$ae
    dc.b    $02,$48,$02,$34,$02,$4a,$02,$5a,$01,$b4,$01,$b6,$01,$b8,$ff,$ff
    dc.b    $02,$0e,$01,$b0,$01,$b2,$01,$ba,$02,$10,$01,$bc,$01,$be,$02,$52
    dc.b    $02,$70,$02,$3a,$01,$c0,$01,$c2,$01,$c4,$01,$ca,$01,$cc,$02,$3c
    dc.b    $01,$ce,$02,$12,$02,$14,$02,$54,$02,$5c,$01,$d0,$02,$16,$02,$72
    dc.b    $02,$5e,$01,$d2,$01,$d4,$02,$5a,$01,$b4,$01,$b6,$01,$b8,$01,$d6
    dc.b    $02,$0e,$ff,$ff,$ff,$ff,$01,$ba,$02,$10,$01,$bc,$01,$be,$02,$74
    dc.b    $02,$70,$ff,$ff,$01,$c0,$01,$c2,$01,$c4,$01,$ca,$01,$cc,$02,$7c
    dc.b    $01,$ce,$02,$12,$02,$14,$02,$42,$02,$5c,$01,$d0,$02,$16,$02,$72
    dc.b    $02,$5e,$01,$d2,$01,$d4,$ff,$ff,$02,$7e,$ff,$ff,$01,$f0,$01,$d6
    dc.b    $01,$f2,$01,$f4,$01,$f6,$01,$f8,$01,$fa,$02,$44,$01,$fc,$02,$74
    dc.b    $02,$94,$01,$fe,$02,$00,$02,$02,$02,$04,$02,$96,$02,$06,$02,$7c
    dc.b    $02,$08,$02,$0a,$02,$0c,$02,$42,$02,$1a,$02,$1c,$02,$1e,$ff,$ff
    dc.b    $02,$20,$02,$56,$ff,$ff,$02,$58,$02,$7e,$02,$22,$01,$f0,$02,$24
    dc.b    $01,$f2,$01,$f4,$01,$f6,$01,$f8,$01,$fa,$02,$44,$01,$fc,$ff,$ff
    dc.b    $02,$94,$01,$fe,$02,$00,$02,$02,$02,$04,$02,$96,$02,$06,$02,$4c
    dc.b    $02,$08,$02,$0a,$02,$0c,$02,$4e,$02,$1a,$02,$1c,$02,$1e,$02,$50
    dc.b    $02,$20,$02,$56,$02,$76,$02,$58,$02,$90,$02,$22,$02,$98,$02,$24
    dc.b    $02,$60,$02,$62,$02,$64,$02,$b2,$02,$78,$02,$7a,$02,$66,$02,$9a
    dc.b    $02,$68,$02,$92,$02,$9c,$02,$6a,$02,$ca,$ff,$ff,$ff,$ff,$02,$4c
    dc.b    $ff,$ff,$ff,$ff,$02,$6c,$02,$4e,$ff,$ff,$ff,$ff,$02,$6e,$02,$50
    dc.b    $ff,$ff,$ff,$ff,$02,$76,$ff,$ff,$02,$90,$ff,$ff,$02,$98,$ff,$ff
    dc.b    $02,$60,$02,$62,$02,$64,$02,$b2,$02,$78,$02,$7a,$02,$66,$02,$9a
    dc.b    $02,$68,$02,$92,$02,$9c,$02,$6a,$02,$ca,$02,$80,$02,$82,$02,$84
    dc.b    $02,$b4,$02,$9e,$02,$6c,$02,$86,$02,$b8,$02,$88,$02,$6e,$02,$a0
    dc.b    $02,$8a,$02,$a4,$02,$a6,$02,$a8,$02,$aa,$02,$a2,$02,$c2,$02,$8c
    dc.b    $02,$b6,$ff,$ff,$02,$ba,$02,$8e,$02,$ac,$02,$bc,$02,$cc,$02,$be
    dc.b    $02,$b4,$02,$ae,$02,$b0,$ff,$ff,$ff,$ff,$02,$80,$02,$82,$02,$84
    dc.b    $02,$b4,$02,$9e,$02,$d2,$02,$86,$02,$b8,$02,$88,$02,$c0,$02,$a0
    dc.b    $02,$8a,$02,$a4,$02,$a6,$02,$a8,$02,$aa,$02,$a2,$02,$c2,$02,$8c
    dc.b    $02,$b6,$02,$c4,$02,$ba,$02,$8e,$02,$ac,$02,$bc,$02,$cc,$02,$be
    dc.b    $02,$b4,$02,$ae,$02,$b0,$02,$b6,$02,$ce,$02,$d4,$02,$d6,$02,$c6
    dc.b    $02,$c8,$02,$da,$02,$d2,$02,$dc,$02,$de,$02,$d0,$02,$c0,$02,$e0
    dc.b    $02,$e4,$02,$e6,$02,$ea,$02,$ee,$02,$f6,$02,$f8,$02,$d8,$03,$04
    dc.b    $02,$e8,$02,$c4,$03,$06,$03,$08,$ff,$ff,$ff,$ff,$03,$12,$02,$e2
    dc.b    $00,$ae,$02,$ec,$ff,$ff,$02,$b6,$02,$ce,$02,$d4,$02,$d6,$02,$c6
    dc.b    $02,$c8,$02,$da,$03,$14,$02,$dc,$02,$de,$02,$d0,$02,$f0,$02,$e0
    dc.b    $02,$e4,$02,$e6,$02,$ea,$02,$ee,$02,$f6,$02,$f8,$02,$d8,$03,$04
    dc.b    $02,$e8,$03,$0a,$03,$06,$03,$08,$02,$f2,$02,$f4,$03,$12,$02,$e2
    dc.b    $00,$ae,$02,$ec,$00,$fe,$03,$16,$02,$fa,$01,$04,$01,$06,$01,$08
    dc.b    $03,$20,$03,$0c,$03,$14,$02,$fc,$02,$fe,$01,$0e,$02,$f0,$03,$00
    dc.b    $03,$0e,$03,$22,$ff,$ff,$03,$02,$03,$10,$01,$18,$03,$24,$03,$26
    dc.b    $03,$2a,$03,$0a,$ff,$ff,$03,$28,$02,$f2,$02,$f4,$03,$2c,$03,$2e
    dc.b    $03,$30,$ff,$ff,$00,$fe,$03,$16,$02,$fa,$01,$04,$01,$06,$01,$08
    dc.b    $03,$20,$03,$0c,$03,$18,$02,$fc,$02,$fe,$01,$0e,$03,$32,$03,$00
    dc.b    $03,$0e,$03,$22,$03,$1a,$03,$02,$03,$10,$01,$18,$03,$24,$03,$26
    dc.b    $03,$2a,$03,$34,$03,$1c,$03,$28,$03,$36,$03,$38,$03,$2c,$03,$2e
    dc.b    $03,$30,$03,$1e,$03,$3a,$03,$3c,$03,$3e,$03,$44,$ff,$ff,$03,$4e
    dc.b    $03,$50,$03,$52,$03,$18,$03,$54,$03,$56,$03,$58,$03,$32,$03,$46
    dc.b    $03,$5a,$03,$5e,$03,$1a,$ff,$ff,$03,$6c,$03,$6e,$03,$70,$03,$72
    dc.b    $ff,$ff,$03,$34,$03,$1c,$03,$7c,$03,$36,$03,$38,$03,$48,$03,$60
    dc.b    $03,$5c,$03,$1e,$03,$3a,$03,$3c,$03,$3e,$03,$44,$03,$4a,$03,$4e
    dc.b    $03,$50,$03,$52,$03,$4c,$03,$54,$03,$56,$03,$58,$03,$62,$03,$64
    dc.b    $03,$5a,$03,$5e,$ff,$ff,$03,$66,$03,$6c,$03,$6e,$03,$70,$03,$72
    dc.b    $03,$74,$03,$5a,$03,$78,$03,$7c,$03,$7a,$03,$5c,$03,$48,$03,$60
    dc.b    $03,$5c,$03,$68,$03,$6a,$03,$7e,$03,$86,$03,$8c,$03,$4a,$03,$88
    dc.b    $03,$76,$03,$80,$03,$4c,$03,$8e,$03,$92,$03,$82,$03,$62,$03,$64
    dc.b    $03,$94,$03,$96,$03,$84,$03,$66,$03,$8a,$03,$98,$03,$9a,$03,$9c
    dc.b    $03,$74,$03,$5a,$03,$78,$03,$9e,$03,$7a,$03,$5c,$ff,$ff,$03,$a0
    dc.b    $03,$90,$03,$68,$03,$6a,$03,$7e,$03,$86,$03,$8c,$03,$a2,$03,$88
    dc.b    $03,$76,$03,$80,$03,$a6,$03,$8e,$03,$92,$03,$82,$03,$a4,$ff,$ff
    dc.b    $03,$94,$03,$96,$03,$84,$03,$b0,$03,$8a,$03,$98,$03,$9a,$03,$9c
    dc.b    $03,$b2,$03,$a8,$03,$aa,$03,$9e,$03,$ac,$03,$c6,$03,$b4,$03,$a0
    dc.b    $03,$90,$03,$ae,$03,$b6,$03,$b8,$03,$c8,$03,$ca,$03,$a2,$03,$cc
    dc.b    $03,$e2,$03,$e4,$03,$a6,$03,$ba,$03,$e6,$03,$be,$03,$a4,$03,$c0
    dc.b    $03,$ea,$03,$bc,$03,$e8,$03,$b0,$03,$c2,$03,$f0,$03,$c4,$ff,$ff
    dc.b    $03,$b2,$03,$a8,$03,$aa,$03,$ec,$03,$ac,$03,$c6,$03,$b4,$03,$ee
    dc.b    $ff,$ff,$03,$ae,$03,$b6,$03,$b8,$03,$c8,$03,$ca,$ff,$ff,$03,$cc
    dc.b    $03,$e2,$03,$e4,$03,$f2,$03,$ba,$03,$e6,$03,$be,$03,$f4,$03,$c0
    dc.b    $03,$ea,$03,$bc,$03,$e8,$03,$f6,$03,$c2,$03,$f0,$03,$c4,$03,$ce
    dc.b    $03,$d0,$03,$d2,$03,$f8,$03,$ec,$03,$fe,$03,$fa,$03,$d4,$03,$ee
    dc.b    $03,$d6,$03,$d8,$04,$00,$04,$02,$03,$da,$03,$dc,$03,$de,$03,$e0
    dc.b    $04,$04,$04,$06,$03,$f2,$04,$08,$ff,$ff,$04,$12,$03,$f4,$03,$fc
    dc.b    $04,$14,$04,$0a,$04,$16,$03,$f6,$04,$1e,$ff,$ff,$ff,$ff,$03,$ce
    dc.b    $03,$d0,$03,$d2,$03,$f8,$ff,$ff,$03,$fe,$03,$fa,$03,$d4,$ff,$ff
    dc.b    $03,$d6,$03,$d8,$04,$00,$04,$02,$03,$da,$03,$dc,$03,$de,$03,$e0
    dc.b    $04,$04,$04,$06,$04,$0c,$04,$08,$04,$0e,$04,$12,$04,$18,$03,$fc
    dc.b    $04,$14,$04,$0a,$04,$16,$04,$20,$04,$1e,$04,$1a,$04,$24,$04,$34
    dc.b    $04,$28,$04,$4c,$04,$2a,$04,$2e,$04,$26,$04,$1c,$04,$10,$04,$2c
    dc.b    $04,$30,$04,$4e,$04,$22,$ff,$ff,$ff,$ff,$04,$50,$04,$32,$04,$52
    dc.b    $04,$54,$04,$56,$04,$0c,$ff,$ff,$04,$0e,$04,$58,$04,$18,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$04,$20,$04,$68,$04,$1a,$04,$24,$04,$34
    dc.b    $04,$28,$04,$4c,$04,$2a,$04,$2e,$04,$26,$04,$1c,$04,$10,$04,$2c
    dc.b    $04,$30,$04,$4e,$04,$22,$04,$36,$04,$38,$04,$50,$04,$32,$04,$52
    dc.b    $04,$54,$04,$56,$04,$5a,$04,$42,$04,$3a,$04,$58,$04,$44,$04,$3c
    dc.b    $04,$46,$04,$5e,$04,$3e,$04,$40,$04,$68,$04,$48,$04,$70,$04,$4a
    dc.b    $04,$72,$04,$5c,$04,$62,$04,$64,$04,$66,$04,$6a,$04,$74,$04,$6c
    dc.b    $04,$60,$04,$76,$ff,$ff,$04,$36,$04,$38,$04,$7c,$04,$7e,$04,$6e
    dc.b    $04,$80,$ff,$ff,$04,$5a,$04,$42,$04,$3a,$04,$86,$04,$44,$04,$3c
    dc.b    $04,$46,$04,$5e,$04,$3e,$04,$40,$04,$88,$04,$48,$04,$70,$04,$4a
    dc.b    $04,$72,$04,$5c,$04,$62,$04,$64,$04,$66,$04,$6a,$04,$74,$04,$6c
    dc.b    $04,$60,$04,$76,$04,$78,$04,$8a,$04,$8c,$04,$7c,$04,$7e,$04,$6e
    dc.b    $04,$80,$04,$82,$04,$8e,$04,$84,$04,$7a,$04,$86,$04,$90,$04,$92
    dc.b    $04,$94,$04,$96,$ff,$ff,$ff,$ff,$04,$88,$04,$9a,$04,$9e,$04,$a2
    dc.b    $04,$a6,$04,$c6,$04,$c8,$04,$ca,$04,$cc,$04,$aa,$04,$ce,$04,$d0
    dc.b    $ff,$ff,$04,$98,$04,$78,$04,$8a,$04,$8c
pcref_c4e2:
    dc.b    $04,$9c,$04,$a0,$04,$a4,$04,$a8,$04,$82,$04,$8e,$04,$84,$04,$7a
    dc.b    $04,$ac,$04,$90,$04,$92,$04,$94,$04,$96,$04,$ae,$04,$b2,$ff,$ff
    dc.b    $04,$9a,$04,$9e,$04,$a2,$04,$a6,$04,$c6,$04,$c8,$04,$ca,$04,$cc
    dc.b    $04,$aa,$04,$ce,$04,$d0,$04,$d8,$04,$98,$04,$b0,$04,$b4,$04,$f4
    dc.b    $04,$9c,$04,$a0,$04,$a4,$04,$a8,$04,$b6,$04,$b8,$04,$ba,$04,$dc
    dc.b    $04,$ac,$04,$d2,$04,$bc,$04,$da,$04,$be,$04,$ae,$04,$b2,$04,$c0
    dc.b    $04,$e0,$04,$e4,$04,$e8,$04,$ec,$04,$f6,$04,$f8,$04,$c2,$04,$de
    dc.b    $04,$f0,$04,$d4,$04,$c4,$04,$d8,$04,$d6,$04,$b0,$04,$b4,$04,$f4
    dc.b    $04,$e2,$04,$e6,$04,$ea,$04,$ee,$04,$b6,$04,$b8,$04,$ba,$04,$dc
    dc.b    $04,$f2,$04,$d2,$04,$bc,$04,$da,$04,$be,$04,$fa,$04,$fc,$04,$c0
    dc.b    $04,$e0,$04,$e4,$04,$e8,$04,$ec,$04,$f6,$04,$f8,$04,$c2,$04,$de
    dc.b    $04,$f0,$04,$d4,$04,$c4,$04,$fe,$04,$d6,$05,$00,$05,$02,$05,$06
    dc.b    $04,$e2,$04,$e6,$04,$ea,$04,$ee,$05,$04,$05,$08,$05,$0a,$05,$0c
    dc.b    $04,$f2,$05,$0e,$05,$1a,$ff,$ff,$05,$20,$04,$fa,$04,$fc,$ff,$ff
    dc.b    $05,$1c,$05,$22,$05,$1e,$02,$e6,$02,$f0,$02,$f6,$05,$24,$05,$26
    dc.b    $05,$10,$05,$28,$05,$2a,$04,$fe,$05,$2c,$05,$00,$05,$02,$05,$06
    dc.b    $05,$12,$05,$2e,$02,$f2,$02,$f4,$05,$04,$05,$08,$05,$0a,$05,$0c
    dc.b    $05,$14,$05,$0e,$05,$1a,$05,$16,$05,$20,$05,$30,$05,$32,$05,$18
    dc.b    $05,$1c,$05,$22,$05,$1e,$02,$e6,$02,$f0,$02,$f6,$05,$24,$05,$26
    dc.b    $05,$10,$05,$28,$05,$2a,$05,$34,$05,$2c,$05,$36,$05,$38,$05,$3a
    dc.b    $05,$12,$05,$2e,$02,$f2,$02,$f4,$05,$3c,$05,$3e,$05,$40,$05,$42
    dc.b    $05,$14,$05,$48,$05,$4a,$05,$16,$05,$4c,$05,$30,$05,$32,$05,$18
    dc.b    $05,$4e,$05,$50,$05,$44,$05,$52,$05,$54,$05,$56,$05,$46,$05,$58
    dc.b    $05,$5a,$05,$5c,$05,$5e,$05,$34,$05,$60,$05,$36,$05,$38,$05,$3a
    dc.b    $05,$66,$05,$74,$ff,$ff,$05,$62,$05,$3c,$05,$3e,$05,$40,$05,$42
    dc.b    $05,$76,$05,$48,$05,$4a,$05,$64,$05,$4c,$05,$78,$05,$70,$05,$68
    dc.b    $05,$4e,$05,$50,$05,$44,$05,$52,$05,$54,$05,$56,$05,$46,$05,$58
    dc.b    $05,$5a,$05,$5c,$05,$5e,$05,$6a,$05,$60,$05,$72,$05,$82,$05,$84
    dc.b    $05,$66,$05,$74,$05,$6c,$05,$62,$05,$7a,$05,$7e,$05,$86,$05,$88
    dc.b    $05,$76,$05,$8a,$05,$6e,$05,$64,$03,$d0,$05,$78,$05,$70,$05,$68
    dc.b    $05,$8c,$05,$90,$05,$b0,$05,$7c,$05,$80,$05,$94,$05,$b2,$05,$96
    dc.b    $05,$8e,$05,$b4,$05,$b6,$05,$6a,$05,$98,$05,$72,$05,$82,$05,$84
    dc.b    $05,$92,$05,$b8,$05,$6c,$05,$9a,$05,$7a,$05,$7e,$05,$86,$05,$88
    dc.b    $05,$9c,$05,$8a,$05,$6e,$ff,$ff,$03,$d0,$05,$ba,$05,$9e,$05,$bc
    dc.b    $05,$8c,$05,$90,$05,$b0,$05,$7c,$05,$80,$05,$94,$05,$b2,$05,$96
    dc.b    $05,$8e,$05,$b4,$05,$b6,$05,$c2,$05,$98,$05,$a0,$05,$a2,$05,$be
    dc.b    $05,$92,$05,$b8,$05,$a8,$05,$9a,$05,$aa,$05,$ca,$05,$a4,$05,$c0
    dc.b    $05,$9c,$05,$ac,$05,$cc,$05,$ae,$05,$a6,$05,$ba,$05,$9e,$05,$bc
    dc.b    $05,$c4,$05,$c6,$05,$ce,$05,$d0,$05,$d2,$05,$d4,$05,$d6,$05,$d8
    dc.b    $05,$da,$05,$dc,$05,$e4,$05,$c2,$05,$e6,$05,$a0,$05,$a2,$05,$be
    dc.b    $05,$e8,$05,$de,$05,$a8,$05,$e0,$05,$aa,$05,$ca,$05,$a4,$05,$c0
    dc.b    $05,$e2,$05,$ac,$05,$cc,$05,$ae,$05,$a6,$05,$c8,$05,$f0,$05,$fa
    dc.b    $05,$fe,$06,$00,$05,$ce,$05,$d0,$05,$d2,$05,$d4,$05,$d6,$05,$d8
    dc.b    $05,$da,$05,$dc,$05,$e4,$05,$ea,$05,$e6,$05,$f2,$05,$fc,$06,$02
    dc.b    $05,$e8,$05,$de,$05,$ec,$05,$e0,$05,$f4,$06,$04,$06,$06,$06,$08
    dc.b    $05,$e2,$06,$0a,$05,$ee,$05,$f6,$06,$12,$05,$c8,$05,$f0,$05,$fa
    dc.b    $05,$fe,$06,$00,$06,$0e,$05,$f8,$06,$14,$06,$16,$06,$18,$06,$1a
    dc.b    $06,$0c,$06,$1c,$06,$1e,$05,$ea,$06,$20,$05,$f2,$05,$fc,$06,$02
    dc.b    $06,$22,$06,$10,$05,$ec,$06,$24,$05,$f4,$06,$04,$06,$06,$06,$08
    dc.b    $06,$26,$06,$0a,$05,$ee,$05,$f6,$06,$12,$06,$28,$06,$2a,$06,$2c
    dc.b    $06,$3c,$06,$3e,$06,$0e,$05,$f8,$06,$14,$06,$16,$06,$18,$06,$1a
    dc.b    $06,$0c,$06,$1c,$06,$1e,$06,$40,$06,$20,$06,$42,$ff,$ff,$06,$64
    dc.b    $06,$22,$06,$10,$06,$2e,$06,$24,$ff,$ff,$06,$44,$06,$48,$06,$4c
    dc.b    $06,$26,$06,$50,$06,$54,$06,$66,$06,$58,$06,$28,$06,$2a,$06,$2c
    dc.b    $06,$3c,$06,$3e,$06,$30,$06,$5c,$06,$32,$06,$46,$06,$4a,$06,$4e
    dc.b    $06,$60,$06,$52,$06,$56,$06,$40,$06,$5a,$06,$42,$06,$34,$06,$64
    dc.b    $ff,$ff,$06,$36,$06,$38,$06,$5e,$06,$3a,$06,$44,$06,$48,$06,$4c
    dc.b    $06,$62,$06,$50,$06,$54,$06,$66,$06,$58,$06,$6c,$06,$6e,$06,$70
    dc.b    $06,$72,$06,$74,$06,$30,$06,$5c,$06,$32,$06,$46,$06,$4a,$06,$4e
    dc.b    $06,$60,$06,$52,$06,$56,$06,$68,$06,$5a,$06,$76,$06,$34,$06,$78
    dc.b    $06,$6a,$06,$36,$06,$38,$06,$5e,$06,$3a,$06,$7a,$06,$7c,$06,$7e
    dc.b    $06,$62,$06,$80,$06,$82,$06,$84,$06,$86,$06,$6c,$06,$6e,$06,$70
    dc.b    $06,$72,$06,$74,$06,$88,$ff,$ff,$06,$8a,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$06,$92,$06,$9a,$06,$68,$ff,$ff,$06,$76,$ff,$ff,$06,$78
    dc.b    $06,$6a,$06,$8e,$06,$94,$06,$90,$ff,$ff,$06,$7a,$06,$7c,$06,$7e
    dc.b    $06,$9c,$06,$80,$06,$82,$06,$84,$06,$86,$06,$96,$06,$9e,$06,$a0
    dc.b    $06,$a2,$06,$98,$06,$88,$00,$fe,$06,$8a,$02,$fa,$01,$04,$01,$06
    dc.b    $01,$08,$06,$92,$06,$9a,$06,$aa,$01,$0a,$02,$fe,$01,$0e,$06,$b8
    dc.b    $03,$00,$06,$8e,$06,$94,$06,$90,$03,$02,$06,$a4,$06,$8c,$06,$ba
    dc.b    $06,$9c,$06,$bc,$06,$ac,$06,$ae,$06,$a6,$06,$96,$06,$9e,$06,$a0
    dc.b    $06,$a2,$06,$98,$06,$b0,$00,$fe,$06,$a8,$02,$fa,$01,$04,$01,$06
    dc.b    $01,$08,$06,$b4,$06,$b2,$06,$aa,$01,$0a,$02,$fe,$01,$0e,$06,$b8
    dc.b    $03,$00,$06,$be,$06,$c2,$06,$c6,$03,$02,$06,$a4,$06,$8c,$06,$ba
    dc.b    $06,$b6,$06,$bc,$06,$ac,$06,$ae,$06,$a6,$06,$c8,$06,$ca,$06,$cc
    dc.b    $06,$c0,$06,$c4,$06,$b0,$06,$ce,$06,$a8,$06,$d0,$06,$d4,$06,$da
    dc.b    $06,$dc,$06,$b4,$06,$b2,$06,$d6,$06,$de,$06,$e0,$06,$e2,$06,$e4
    dc.b    $06,$e6,$06,$be,$06,$c2,$06,$c6,$06,$e8,$06,$d8,$06,$ea,$06,$ec
    dc.b    $06,$b6,$07,$00,$ff,$ff,$ff,$ff,$07,$02,$06,$c8,$06,$ca,$06,$cc
    dc.b    $06,$c0,$06,$c4,$07,$04,$06,$ce,$07,$06,$06,$d0,$06,$d4,$06,$da
    dc.b    $06,$dc,$07,$08,$07,$0a,$06,$d6,$06,$de,$06,$e0,$06,$e2,$06,$e4
    dc.b    $06,$e6,$06,$ee,$06,$f0,$06,$f2,$06,$e8,$06,$d8,$06,$ea,$06,$ec
    dc.b    $06,$f4,$07,$00,$06,$f6,$06,$f8,$07,$02,$07,$0c,$07,$0e,$06,$fa
    dc.b    $06,$fc,$06,$fe,$07,$04,$07,$10,$07,$06,$07,$14,$07,$16,$07,$18
    dc.b    $07,$1a,$07,$08,$07,$0a,$07,$1c,$07,$22,$07,$24,$07,$3a,$07,$1e
    dc.b    $07,$26,$06,$ee,$06,$f0,$06,$f2,$07,$20,$07,$28,$07,$3c,$ff,$ff
    dc.b    $06,$f4,$ff,$ff,$06,$f6,$06,$f8,$ff,$ff,$07,$0c,$07,$0e,$06,$fa
    dc.b    $06,$fc,$06,$fe,$07,$3e,$07,$10,$07,$40,$07,$14,$07,$16,$07,$18
    dc.b    $07,$1a,$07,$42,$03,$0a,$07,$1c,$07,$22,$07,$24,$07,$3a,$07,$1e
    dc.b    $07,$26,$07,$2a,$07,$2c,$07,$2e,$07,$20,$07,$28,$07,$3c,$07,$30
    dc.b    $07,$44,$07,$32,$03,$0c,$07,$48,$07,$34,$07,$4a,$07,$4e,$07,$50
    dc.b    $07,$52,$07,$54,$07,$3e,$07,$36,$07,$40,$07,$56,$07,$58,$07,$38
    dc.b    $07,$5a,$07,$42,$03,$0a,$07,$6c,$07,$82,$07,$66,$07,$84,$07,$68
    dc.b    $07,$6e,$07,$2a,$07,$2c,$07,$2e,$07,$6a,$07,$62,$07,$70,$07,$30
    dc.b    $07,$44,$07,$32,$03,$0c,$07,$48,$07,$34,$07,$4a,$07,$4e,$07,$50
    dc.b    $07,$52,$07,$54,$07,$5c,$07,$36,$07,$64,$07,$56,$07,$58,$07,$38
    dc.b    $07,$5a,$07,$5e,$07,$86,$07,$6c,$07,$82,$07,$66,$07,$84,$07,$68
    dc.b    $07,$6e,$07,$60,$07,$72,$07,$74,$07,$6a,$07,$62,$07,$70,$07,$7a
    dc.b    $07,$88,$07,$7c,$07,$8a,$07,$76,$07,$94,$07,$96,$07,$7e,$07,$98
    dc.b    $07,$80,$07,$78,$07,$5c,$07,$8c,$07,$64,$07,$b8,$07,$9c,$ff,$ff
    dc.b    $ff,$ff,$07,$5e,$07,$86,$ff,$ff,$07,$ba,$07,$bc,$07,$be,$07,$9a
    dc.b    $07,$8e,$07,$60,$07,$72,$07,$74,$07,$90,$07,$92,$07,$9e,$07,$7a
    dc.b    $07,$88,$07,$7c,$07,$8a,$07,$76,$07,$94,$07,$96,$07,$7e,$07,$98
    dc.b    $07,$80,$07,$78,$07,$a0,$07,$8c,$ff,$ff,$07,$b8,$07,$9c,$07,$a4
    dc.b    $07,$a8,$07,$ac,$07,$b0,$07,$b4,$07,$ba,$07,$bc,$07,$be,$07,$9a
    dc.b    $07,$8e,$07,$c6,$07,$a2,$07,$d4,$07,$90,$07,$92,$07,$9e,$07,$a6
    dc.b    $07,$aa,$07,$ae,$07,$b2,$07,$b6,$07,$d6,$07,$c0,$07,$ca,$07,$d0
    dc.b    $07,$c8,$07,$d8,$07,$a0,$ff,$ff,$07,$c2,$07,$cc,$07,$da,$07,$a4
    dc.b    $07,$a8,$07,$ac,$07,$b0,$07,$b4,$07,$c4,$07,$ce,$07,$d2,$07,$e2
    dc.b    $07,$e4,$07,$c6,$07,$a2,$07,$d4,$07,$de,$07,$dc,$07,$e6,$07,$a6
    dc.b    $07,$aa,$07,$ae,$07,$b2,$07,$b6,$07,$d6,$07,$c0,$07,$ca,$07,$d0
    dc.b    $07,$c8,$07,$d8,$07,$e8,$07,$e0,$07,$c2,$07,$cc,$07,$da,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$07,$c4,$07,$ce,$07,$d2,$07,$e2
    dc.b    $07,$e4,$ff,$ff,$ff,$ff,$ff,$ff,$07,$de,$07,$dc,$07,$e6,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$07,$e8,$07,$e0,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
dat_cd3c:
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dcb.b   6,0
    dc.b    $01,$68,$01,$6a,$05,$c4,$00,$00,$06,$2e,$06,$ca,$06,$d4,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$00,$00,$ff,$ff,$ff,$ff,$ff,$ff
    dcb.b   48,0
    dc.b    $ff,$ff,$00,$00,$ff,$ff,$00,$24,$00,$28,$ff,$ff,$00,$2a,$ff,$ff
    dcb.b   49,0
    dc.b    $04,$00,$00,$00,$04,$00,$24,$00,$28,$00,$06,$00,$2a,$00,$06,$00
    dc.b    $06,$00,$06,$00,$06,$00,$26,$00,$04,$00,$06,$00,$06,$00,$06,$00
    dc.b    $06,$00,$04,$00,$06,$ff,$ff,$00,$06,$00,$06,$00,$06,$00,$12,$00
    dc.b    $06,$00,$26,$ff,$ff,$ff,$ff,$00,$2c,$00,$12,$ff,$ff,$ff,$ff,$00
    dc.b    $04,$ff,$ff,$00,$04,$ff,$ff,$00,$32,$00,$06,$ff,$ff,$00,$06,$00
    dc.b    $06,$00,$06,$00,$06,$00,$26,$00,$04,$00,$06,$00,$06,$00,$06,$00
    dc.b    $06,$00,$04,$00,$06,$00,$08,$00,$06,$00,$06,$00,$06,$00,$12,$00
    dc.b    $06,$00,$26,$00,$08,$00,$08,$00,$2c,$00,$12,$00,$08,$00,$08,$00
    dc.b    $08,$00,$08,$00,$08,$00,$2e,$00,$32,$00,$08,$00,$0a,$00,$0a,$00
    dc.b    $0a,$00,$2e,$00,$0c,$00,$38,$00,$0c,$00,$0c,$00,$0a,$00,$0c,$00
    dc.b    $3a,$00,$3e,$00,$40,$00,$08,$00,$0c,$00,$38,$00,$0c,$00,$42,$00
    dc.b    $0a,$ff,$ff,$00,$08,$00,$08,$ff,$ff,$ff,$ff,$00,$08,$00,$08,$00
    dc.b    $08,$00,$08,$00,$08,$00,$2e,$ff,$ff,$00,$08,$00,$0a,$00,$0a,$00
    dc.b    $0a,$00,$2e,$00,$0c,$00,$38,$00,$0c,$00,$0c,$00,$0a,$00,$0c,$00
    dc.b    $3a,$00,$3e,$00,$40,$00,$44,$00,$0c,$00,$38,$00,$0c,$00,$42,$00
    dc.b    $0a,$00,$0e,$00,$0e,$00,$0e,$00,$0e,$00,$0e,$00,$48,$00,$0e,$00
    dc.b    $4e,$00,$0e,$00,$4c,$00,$50,$00,$0e,$00,$0e,$00,$0e,$00,$0e,$00
    dc.b    $4c,$00,$4c,$00,$0e,$00,$0e,$00,$0e,$00,$10,$00,$52,$00,$10,$ff
    dc.b    $ff,$ff,$ff,$00,$10,$00,$44,$ff,$ff,$00,$10,$ff,$ff,$00,$10,$ff
    dc.b    $ff,$00,$0e,$00,$0e,$00,$0e,$00,$0e,$00,$0e,$00,$48,$00,$0e,$00
    dc.b    $4e,$00,$0e,$00,$4c,$00,$50,$00,$0e,$00,$0e,$00,$0e,$00,$0e,$00
    dc.b    $4c,$00,$4c,$00,$0e,$00,$0e,$00,$0e,$00,$10,$00,$52,$00,$10,$00
    dc.b    $18,$00,$4a,$00,$10,$00,$18,$00,$14,$00,$10,$00,$16,$00,$10,$00
    dc.b    $14,$00,$1a,$00,$16,$00,$14,$00,$54,$00,$18,$00,$36,$00,$14,$00
    dc.b    $56,$00,$4a,$00,$14,$00,$1a,$00,$16,$00,$1a,$ff,$ff,$00,$36,$00
    dc.b    $1a,$00,$58,$00,$16,$ff,$ff,$ff,$ff,$00,$36,$ff,$ff,$ff,$ff,$00
    dc.b    $18,$00,$4a,$00,$58,$00,$18,$00,$14,$ff,$ff,$00,$16,$ff,$ff,$00
    dc.b    $14,$00,$1a,$00,$16,$00,$14,$00,$54,$00,$18,$00,$36,$00,$14,$00
    dc.b    $56,$00,$4a,$00,$14,$00,$1a,$00,$16,$00,$1a,$00,$46,$00,$36,$00
    dc.b    $1a,$00,$58,$00,$16,$00,$1c,$00,$1c,$00,$36,$00,$1c,$00,$1c,$00
    dc.b    $1c,$00,$1e,$00,$58,$00,$46,$00,$46,$00,$1e,$00,$1c,$00,$1c,$00
    dc.b    $5a,$00,$5c,$00,$5e,$00,$62,$00,$1c,$00,$1c,$00,$1c,$00,$1e,$00
    dc.b    $1c,$00,$64,$00,$68,$00,$1e,$00,$1e,$ff,$ff,$00,$46,$00,$6a,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$00,$1c,$00,$1c,$00,$6c,$00,$1c,$00,$1c,$00
    dc.b    $1c,$00,$1e,$00,$6e,$00,$46,$00,$46,$00,$1e,$00,$1c,$00,$1c,$00
    dc.b    $5a,$00,$5c,$00,$5e,$00,$62,$00,$1c,$00,$1c,$00,$1c,$00,$1e,$00
    dc.b    $1c,$00,$64,$00,$68,$00,$1e,$00,$1e,$00,$20,$00,$20,$00,$6a,$00
    dc.b    $20,$00,$20,$00,$20,$00,$20,$00,$70,$00,$6c,$00,$7e,$00,$20,$00
    dc.b    $20,$00,$20,$00,$6e,$00,$20,$ff,$ff,$00,$80,$00,$72,$00,$20,$00
    dc.b    $20,$00,$20,$00,$20,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$00,$72,$00,$82,$00,$20,$00,$20,$ff,$ff,$00
    dc.b    $20,$00,$20,$00,$20,$00,$20,$00,$70,$ff,$ff,$00,$7e,$00,$20,$00
    dc.b    $20,$00,$20,$00,$78,$00,$20,$00,$78,$00,$80,$00,$72,$00,$20,$00
    dc.b    $20,$00,$20,$00,$20,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00
    dc.b    $22,$00,$22,$00,$22,$00,$72,$00,$82,$00,$84,$00,$22,$00,$22,$00
    dc.b    $22,$00,$8a,$00,$22,$00,$84,$00,$22,$00,$22,$00,$22,$ff,$ff,$00
    dc.b    $22,$ff,$ff,$00,$78,$00,$34,$00,$78,$00,$34,$00,$34,$00,$7c,$ff
    dc.b    $ff,$00,$34,$00,$7c,$00,$22,$00,$22,$00,$22,$00,$22,$00,$22,$00
    dc.b    $22,$00,$22,$00,$22,$00,$34,$00,$34,$00,$84,$00,$22,$00,$22,$00
    dc.b    $22,$00,$8a,$00,$22,$00,$84,$00,$22,$00,$22,$00,$22,$00,$30,$00
    dc.b    $22,$00,$86,$00,$3c,$00,$34,$00,$30,$00,$34,$00,$34,$00,$7c,$00
    dc.b    $30,$00,$34,$00,$7c,$00,$86,$00,$3c,$00,$90,$00,$94,$00,$30,$00
    dc.b    $3c,$00,$3c,$ff,$ff,$00,$34,$00,$34,$ff,$ff,$ff,$ff,$ff,$ff,$00
    dc.b    $88,$00,$96,$00,$88,$ff,$ff,$ff,$ff,$ff,$ff,$00,$98,$00,$30,$00
    dc.b    $9a,$00,$86,$00,$3c,$ff,$ff,$00,$30,$ff,$ff,$00,$9c,$ff,$ff,$00
    dc.b    $30,$ff,$ff,$00,$9e,$00,$86,$00,$3c,$00,$90,$00,$94,$00,$30,$00
    dc.b    $3c,$00,$3c,$00,$60,$00,$a2,$00,$60,$00,$60,$00,$60,$00,$60,$00
    dc.b    $88,$00,$96,$00,$88,$00,$60,$00,$60,$00,$60,$00,$98,$00,$60,$00
    dc.b    $9a,$00,$60,$00,$a4,$00,$60,$00,$a8,$00,$60,$00,$9c,$00,$74,$00
    dc.b    $74,$00,$74,$00,$9e,$00,$a0,$00,$aa,$00,$ae,$00,$74,$00,$b0,$00
    dc.b    $a0,$00,$b2,$00,$60,$00,$a2,$00,$60,$00,$60,$00,$60,$00,$60,$00
    dc.b    $74,$00,$74,$ff,$ff,$00,$60,$00,$60,$00,$60,$00,$b6,$00,$60,$00
    dc.b    $a6,$00,$60,$00,$a4,$00,$60,$00,$a8,$00,$60,$00,$a6,$00,$74,$00
    dc.b    $74,$00,$74,$00,$b8,$00,$a0,$00,$aa,$00,$ae,$00,$74,$00,$b0,$00
    dc.b    $a0,$00,$b2,$00,$bc,$00,$76,$00,$76,$00,$76,$ff,$ff,$00,$8e,$00
    dc.b    $74,$00,$74,$00,$76,$00,$8e,$00,$76,$00,$76,$00,$b6,$00,$c2,$00
    dc.b    $a6,$00,$76,$00,$76,$00,$76,$00,$7a,$00,$7a,$00,$a6,$00,$7a,$00
    dc.b    $8e,$00,$8e,$00,$b8,$00,$be,$00,$7a,$00,$8e,$00,$c4,$00,$be,$00
    dc.b    $7a,$00,$7a,$00,$bc,$00,$76,$00,$76,$00,$76,$00,$7a,$00,$8e,$ff
    dc.b    $ff,$ff,$ff,$00,$76,$00,$8e,$00,$76,$00,$76,$00,$c6,$00,$c2,$ff
    dc.b    $ff,$00,$76,$00,$76,$00,$76,$00,$7a,$00,$7a,$00,$ca,$00,$7a,$00
    dc.b    $8e,$00,$8e,$00,$ac,$00,$be,$00,$7a,$00,$8e,$00,$c4,$00,$be,$00
    dc.b    $7a,$00,$7a,$ff,$ff,$00,$cc,$ff,$ff,$00,$8c,$00,$7a,$00,$8c,$00
    dc.b    $8c,$00,$8c,$00,$8c,$00,$8c,$00,$ac,$00,$8c,$00,$c6,$00,$d2,$00
    dc.b    $8c,$00,$8c,$00,$8c,$00,$8c,$00,$d4,$00,$8c,$00,$ca,$00,$8c,$00
    dc.b    $8c,$00,$8c,$00,$ac,$00,$92,$00,$92,$00,$92,$ff,$ff,$00,$92,$00
    dc.b    $ba,$ff,$ff,$00,$ba,$00,$cc,$00,$92,$00,$8c,$00,$92,$00,$8c,$00
    dc.b    $8c,$00,$8c,$00,$8c,$00,$8c,$00,$ac,$00,$8c,$ff,$ff,$00,$d2,$00
    dc.b    $8c,$00,$8c,$00,$8c,$00,$8c,$00,$d4,$00,$8c,$00,$b4,$00,$8c,$00
    dc.b    $8c,$00,$8c,$00,$b4,$00,$92,$00,$92,$00,$92,$00,$b4,$00,$92,$00
    dc.b    $ba,$00,$c8,$00,$ba,$00,$d0,$00,$92,$00,$d6,$00,$92,$00,$c0,$00
    dc.b    $c0,$00,$c0,$00,$de,$00,$c8,$00,$c8,$00,$c0,$00,$d6,$00,$c0,$00
    dc.b    $d0,$00,$d6,$00,$c0,$00,$ec,$ff,$ff,$ff,$ff,$00,$b4,$ff,$ff,$ff
    dc.b    $ff,$00,$c0,$00,$b4,$ff,$ff,$ff,$ff,$00,$c0,$00,$b4,$ff,$ff,$ff
    dc.b    $ff,$00,$c8,$ff,$ff,$00,$d0,$ff,$ff,$00,$d6,$ff,$ff,$00,$c0,$00
    dc.b    $c0,$00,$c0,$00,$de,$00,$c8,$00,$c8,$00,$c0,$00,$d6,$00,$c0,$00
    dc.b    $d0,$00,$d6,$00,$c0,$00,$ec,$00,$ce,$00,$ce,$00,$ce,$00,$e0,$00
    dc.b    $d8,$00,$c0,$00,$ce,$00,$e2,$00,$ce,$00,$c0,$00,$d8,$00,$ce,$00
    dc.b    $da,$00,$da,$00,$dc,$00,$dc,$00,$d8,$00,$e8,$00,$ce,$00,$e0,$ff
    dc.b    $ff,$00,$e2,$00,$ce,$00,$dc,$00,$e2,$00,$ee,$00,$e6,$00,$e8,$00
    dc.b    $dc,$00,$dc,$ff,$ff,$ff,$ff,$00,$ce,$00,$ce,$00,$ce,$00,$e0,$00
    dc.b    $d8,$00,$f2,$00,$ce,$00,$e2,$00,$ce,$00,$e6,$00,$d8,$00,$ce,$00
    dc.b    $da,$00,$da,$00,$dc,$00,$dc,$00,$d8,$00,$e8,$00,$ce,$00,$e0,$00
    dc.b    $ea,$00,$e2,$00,$ce,$00,$dc,$00,$e2,$00,$ee,$00,$e6,$00,$e8,$00
    dc.b    $dc,$00,$dc,$00,$ea,$00,$f0,$00,$f4,$00,$f6,$00,$ea,$00,$ea,$00
    dc.b    $f8,$00,$f2,$00,$fa,$00,$fc,$00,$f0,$00,$e6,$00,$fe,$01,$00,$01
    dc.b    $02,$01,$06,$01,$08,$01,$0c,$01,$0e,$00,$f6,$01,$12,$01,$02,$00
    dc.b    $ea,$01,$14,$01,$16,$ff,$ff,$ff,$ff,$01,$1c,$00,$fe,$01,$0c,$01
    dc.b    $06,$ff,$ff,$00,$ea,$00,$f0,$00,$f4,$00,$f6,$00,$ea,$00,$ea,$00
    dc.b    $f8,$01,$1e,$00,$fa,$00,$fc,$00,$f0,$01,$0a,$00,$fe,$01,$00,$01
    dc.b    $02,$01,$06,$01,$08,$01,$0c,$01,$0e,$00,$f6,$01,$12,$01,$02,$01
    dc.b    $18,$01,$14,$01,$16,$01,$0a,$01,$0a,$01,$1c,$00,$fe,$01,$0c,$01
    dc.b    $06,$01,$10,$01,$20,$01,$10,$01,$10,$01,$10,$01,$10,$01,$24,$01
    dc.b    $18,$01,$1e,$01,$10,$01,$10,$01,$10,$01,$0a,$01,$10,$01,$1a,$01
    dc.b    $2c,$ff,$ff,$01,$10,$01,$1a,$01,$10,$01,$2e,$01,$34,$01,$36,$01
    dc.b    $18,$ff,$ff,$01,$34,$01,$0a,$01,$0a,$01,$38,$01,$3a,$01,$3c,$ff
    dc.b    $ff,$01,$10,$01,$20,$01,$10,$01,$10,$01,$10,$01,$10,$01,$24,$01
    dc.b    $18,$01,$22,$01,$10,$01,$10,$01,$10,$01,$3e,$01,$10,$01,$1a,$01
    dc.b    $2c,$01,$22,$01,$10,$01,$1a,$01,$10,$01,$2e,$01,$34,$01,$36,$01
    dc.b    $42,$01,$22,$01,$34,$01,$48,$01,$58,$01,$38,$01,$3a,$01,$3c,$01
    dc.b    $22,$01,$5e,$01,$64,$01,$66,$01,$6c,$ff,$ff,$01,$72,$01,$74,$01
    dc.b    $76,$01,$22,$01,$78,$01,$7a,$01,$7c,$01,$3e,$01,$70,$01,$7e,$01
    dc.b    $80,$01,$22,$ff,$ff,$01,$8a,$01,$8c,$01,$8e,$01,$90,$ff,$ff,$01
    dc.b    $42,$01,$22,$01,$9a,$01,$48,$01,$58,$01,$70,$01,$84,$01,$7e,$01
    dc.b    $22,$01,$5e,$01,$64,$01,$66,$01,$6c,$01,$70,$01,$72,$01,$74,$01
    dc.b    $76,$01,$70,$01,$78,$01,$7a,$01,$7c,$01,$84,$01,$86,$01,$7e,$01
    dc.b    $80,$ff,$ff,$01,$88,$01,$8a,$01,$8c,$01,$8e,$01,$90,$01,$94,$01
    dc.b    $86,$01,$98,$01,$9a,$01,$98,$01,$88,$01,$70,$01,$84,$01,$7e,$01
    dc.b    $88,$01,$88,$01,$9c,$01,$9e,$01,$a2,$01,$70,$01,$a0,$01,$94,$01
    dc.b    $9c,$01,$70,$01,$a6,$01,$a8,$01,$9c,$01,$84,$01,$86,$01,$aa,$01
    dc.b    $ac,$01,$9c,$01,$88,$01,$a0,$01,$ae,$01,$b0,$01,$b2,$01,$94,$01
    dc.b    $86,$01,$98,$01,$b4,$01,$98,$01,$88,$ff,$ff,$01,$b8,$01,$a6,$01
    dc.b    $88,$01,$88,$01,$9c,$01,$9e,$01,$a2,$01,$b8,$01,$a0,$01,$94,$01
    dc.b    $9c,$01,$ba,$01,$a6,$01,$a8,$01,$9c,$01,$b8,$ff,$ff,$01,$aa,$01
    dc.b    $ac,$01,$9c,$01,$be,$01,$a0,$01,$ae,$01,$b0,$01,$b2,$01,$be,$01
    dc.b    $ba,$01,$bc,$01,$b4,$01,$bc,$01,$c6,$01,$be,$01,$b8,$01,$a6,$01
    dc.b    $bc,$01,$c0,$01,$c0,$01,$c8,$01,$ca,$01,$b8,$01,$ca,$01,$ce,$01
    dc.b    $d0,$01,$ba,$01,$c0,$01,$d2,$01,$c4,$01,$b8,$01,$c4,$01,$d4,$01
    dc.b    $c0,$01,$d2,$01,$be,$01,$c4,$01,$d8,$01,$c4,$ff,$ff,$01,$be,$01
    dc.b    $ba,$01,$bc,$01,$d6,$01,$bc,$01,$c6,$01,$be,$01,$d6,$ff,$ff,$01
    dc.b    $bc,$01,$c0,$01,$c0,$01,$c8,$01,$ca,$ff,$ff,$01,$ca,$01,$ce,$01
    dc.b    $d0,$01,$da,$01,$c0,$01,$d2,$01,$c4,$01,$dc,$01,$c4,$01,$d4,$01
    dc.b    $c0,$01,$d2,$01,$de,$01,$c4,$01,$d8,$01,$c4,$01,$cc,$01,$cc,$01
    dc.b    $cc,$01,$e0,$01,$d6,$01,$e4,$01,$e2,$01,$cc,$01,$d6,$01,$cc,$01
    dc.b    $cc,$01,$e6,$01,$e8,$01,$cc,$01,$cc,$01,$cc,$01,$cc,$01,$ea,$01
    dc.b    $ec,$01,$da,$01,$ee,$ff,$ff,$01,$f2,$01,$dc,$01,$e2,$01,$f4,$01
    dc.b    $ee,$01,$f6,$01,$de,$01,$fc,$ff,$ff,$ff,$ff,$01,$cc,$01,$cc,$01
    dc.b    $cc,$01,$e0,$ff,$ff,$01,$e4,$01,$e2,$01,$cc,$ff,$ff,$01,$cc,$01
    dc.b    $cc,$01,$e6,$01,$e8,$01,$cc,$01,$cc,$01,$cc,$01,$cc,$01,$ea,$01
    dc.b    $ec,$01,$f0,$01,$ee,$01,$f0,$01,$f2,$01,$fa,$01,$e2,$01,$f4,$01
    dc.b    $ee,$01,$f6,$01,$fe,$01,$fc,$01,$fa,$02,$00,$02,$06,$02,$02,$02
    dc.b    $0e,$02,$02,$02,$04,$02,$00,$01,$fa,$01,$f0,$02,$02,$02,$04,$02
    dc.b    $10,$01,$fe,$ff,$ff,$ff,$ff,$02,$12,$02,$04,$02,$14,$02,$16,$02
    dc.b    $18,$01,$f0,$ff,$ff,$01,$f0,$02,$1e,$01,$fa,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$01,$fe,$02,$28,$01,$fa,$02,$00,$02,$06,$02,$02,$02
    dc.b    $0e,$02,$02,$02,$04,$02,$00,$01,$fa,$01,$f0,$02,$02,$02,$04,$02
    dc.b    $10,$01,$fe,$02,$08,$02,$08,$02,$12,$02,$04,$02,$14,$02,$16,$02
    dc.b    $18,$02,$20,$02,$0c,$02,$08,$02,$1e,$02,$0c,$02,$08,$02,$0c,$02
    dc.b    $22,$02,$08,$02,$08,$02,$28,$02,$0c,$02,$32,$02,$0c,$02,$34,$02
    dc.b    $20,$02,$24,$02,$24,$02,$24,$02,$2a,$02,$36,$02,$2a,$02,$22,$02
    dc.b    $38,$ff,$ff,$02,$08,$02,$08,$02,$40,$02,$42,$02,$2a,$02,$44,$ff
    dc.b    $ff,$02,$20,$02,$0c,$02,$08,$02,$48,$02,$0c,$02,$08,$02,$0c,$02
    dc.b    $22,$02,$08,$02,$08,$02,$4a,$02,$0c,$02,$32,$02,$0c,$02,$34,$02
    dc.b    $20,$02,$24,$02,$24,$02,$24,$02,$2a,$02,$36,$02,$2a,$02,$22,$02
    dc.b    $38,$02,$3e,$02,$4c,$02,$4e,$02,$40,$02,$42,$02,$2a,$02,$44,$02
    dc.b    $46,$02,$52,$02,$46,$02,$3e,$02,$48,$02,$5a,$02,$5c,$02,$5e,$02
    dc.b    $60,$ff,$ff,$ff,$ff,$02,$4a,$02,$62,$02,$64,$02,$66,$02,$68,$02
    dc.b    $74,$02,$76,$02,$78,$02,$7a,$02,$6a,$02,$7c,$02,$7e,$ff,$ff,$02
    dc.b    $60,$02,$3e,$02,$4c,$02,$4e,$02,$62,$02,$64,$02,$66,$02,$68,$02
    dc.b    $46,$02,$52,$02,$46,$02,$3e,$02,$6a,$02,$5a,$02,$5c,$02,$5e,$02
    dc.b    $60,$02,$6c,$02,$6e,$ff,$ff,$02,$62,$02,$64,$02,$66,$02,$68,$02
    dc.b    $74,$02,$76,$02,$78,$02,$7a,$02,$6a,$02,$7c,$02,$7e,$02,$82,$02
    dc.b    $60,$02,$6c,$02,$6e,$02,$90,$02,$62,$02,$64,$02,$66,$02,$68,$02
    dc.b    $70,$02,$70,$02,$70,$02,$84,$02,$6a,$02,$80,$02,$70,$02,$82,$02
    dc.b    $70,$02,$6c,$02,$6e,$02,$70,$02,$86,$02,$88,$02,$8a,$02,$8c,$02
    dc.b    $92,$02,$94,$02,$70,$02,$84,$02,$8e,$02,$80,$02,$70,$02,$82,$02
    dc.b    $80,$02,$6c,$02,$6e,$02,$90,$02,$86,$02,$88,$02,$8a,$02,$8c,$02
    dc.b    $70,$02,$70,$02,$70,$02,$84,$02,$8e,$02,$80,$02,$70,$02,$82,$02
    dc.b    $70,$02,$96,$02,$9a,$02,$70,$02,$86,$02,$88,$02,$8a,$02,$8c,$02
    dc.b    $92,$02,$94,$02,$70,$02,$84,$02,$8e,$02,$80,$02,$70,$02,$9c,$02
    dc.b    $80,$02,$a0,$02,$a2,$02,$a4,$02,$86,$02,$88,$02,$8a,$02,$8c,$02
    dc.b    $a2,$02,$a6,$02,$b2,$02,$b8,$02,$8e,$02,$d2,$02,$da,$ff,$ff,$02
    dc.b    $e4,$02,$96,$02,$9a,$ff,$ff,$02,$de,$02,$e8,$02,$de,$02,$fa,$02
    dc.b    $fc,$02,$fe,$03,$00,$03,$04,$02,$d4,$03,$0e,$03,$10,$02,$9c,$03
    dc.b    $12,$02,$a0,$02,$a2,$02,$a4,$02,$d4,$03,$14,$02,$fc,$02,$fc,$02
    dc.b    $a2,$02,$a6,$02,$b2,$02,$b8,$02,$d4,$02,$d2,$02,$da,$02,$d4,$02
    dc.b    $e4,$03,$26,$03,$28,$02,$d4,$02,$de,$02,$e8,$02,$de,$02,$fa,$02
    dc.b    $fc,$02,$fe,$03,$00,$03,$04,$02,$d4,$03,$0e,$03,$10,$03,$2a,$03
    dc.b    $12,$03,$2c,$03,$2e,$03,$30,$02,$d4,$03,$14,$02,$fc,$02,$fc,$03
    dc.b    $32,$03,$3c,$03,$3e,$03,$44,$02,$d4,$03,$52,$03,$54,$02,$d4,$03
    dc.b    $56,$03,$26,$03,$28,$02,$d4,$03,$78,$03,$7a,$03,$44,$03,$7c,$03
    dc.b    $80,$03,$88,$03,$44,$03,$94,$03,$9a,$03,$9c,$03,$a2,$03,$2a,$03
    dc.b    $ac,$03,$2c,$03,$2e,$03,$30,$03,$ae,$03,$b6,$ff,$ff,$03,$ac,$03
    dc.b    $32,$03,$3c,$03,$3e,$03,$44,$03,$ba,$03,$52,$03,$54,$03,$ac,$03
    dc.b    $56,$03,$be,$03,$b2,$03,$ae,$03,$78,$03,$7a,$03,$44,$03,$7c,$03
    dc.b    $80,$03,$88,$03,$44,$03,$94,$03,$9a,$03,$9c,$03,$a2,$03,$b0,$03
    dc.b    $ac,$03,$b2,$03,$c8,$03,$ca,$03,$ae,$03,$b6,$03,$b0,$03,$ac,$03
    dc.b    $c0,$03,$c2,$03,$cc,$03,$ce,$03,$ba,$03,$d2,$03,$b0,$03,$ac,$03
    dc.b    $da,$03,$be,$03,$b2,$03,$ae,$03,$d2,$03,$d4,$03,$e2,$03,$c0,$03
    dc.b    $c2,$03,$d6,$03,$e6,$03,$d6,$03,$d2,$03,$e8,$03,$ea,$03,$b0,$03
    dc.b    $d6,$03,$b2,$03,$c8,$03,$ca,$03,$d4,$03,$ec,$03,$b0,$03,$d8,$03
    dc.b    $c0,$03,$c2,$03,$cc,$03,$ce,$03,$d8,$03,$d2,$03,$b0,$ff,$ff,$03
    dc.b    $da,$03,$ee,$03,$d8,$03,$f2,$03,$d2,$03,$d4,$03,$e2,$03,$c0,$03
    dc.b    $c2,$03,$d6,$03,$e6,$03,$d6,$03,$d2,$03,$e8,$03,$ea,$03,$f6,$03
    dc.b    $d6,$03,$dc,$03,$dc,$03,$f4,$03,$d4,$03,$ec,$03,$e0,$03,$d8,$03
    dc.b    $e0,$03,$fc,$03,$dc,$03,$f4,$03,$d8,$03,$e0,$04,$06,$03,$e0,$03
    dc.b    $dc,$03,$ee,$03,$d8,$03,$f2,$03,$f8,$03,$f8,$04,$0a,$04,$0c,$04
    dc.b    $0e,$04,$10,$04,$12,$04,$14,$04,$1a,$04,$1a,$04,$24,$03,$f6,$04
    dc.b    $26,$03,$dc,$03,$dc,$03,$f4,$04,$28,$04,$1a,$03,$e0,$04,$1e,$03
    dc.b    $e0,$03,$fc,$03,$dc,$03,$f4,$04,$1e,$03,$e0,$04,$06,$03,$e0,$03
    dc.b    $dc,$03,$f8,$04,$2c,$04,$30,$04,$34,$04,$36,$04,$0a,$04,$0c,$04
    dc.b    $0e,$04,$10,$04,$12,$04,$14,$04,$1a,$04,$1a,$04,$24,$04,$2a,$04
    dc.b    $26,$04,$2c,$04,$30,$04,$3a,$04,$28,$04,$1a,$04,$2a,$04,$1e,$04
    dc.b    $2e,$04,$3c,$04,$40,$04,$44,$04,$1e,$04,$46,$04,$2a,$04,$2e,$04
    dc.b    $4c,$03,$f8,$04,$2c,$04,$30,$04,$34,$04,$36,$04,$48,$04,$2e,$04
    dc.b    $4e,$04,$50,$04,$54,$04,$68,$04,$46,$04,$6a,$04,$6c,$04,$2a,$04
    dc.b    $6e,$04,$2c,$04,$30,$04,$3a,$04,$72,$04,$48,$04,$2a,$04,$76,$04
    dc.b    $2e,$04,$3c,$04,$40,$04,$44,$04,$78,$04,$46,$04,$2a,$04,$2e,$04
    dc.b    $4c,$04,$7a,$04,$7c,$04,$7e,$04,$8a,$04,$8c,$04,$48,$04,$2e,$04
    dc.b    $4e,$04,$50,$04,$54,$04,$68,$04,$46,$04,$6a,$04,$6c,$04,$8e,$04
    dc.b    $6e,$04,$90,$ff,$ff,$04,$c6,$04,$72,$04,$48,$04,$80,$04,$76,$ff
    dc.b    $ff,$04,$b6,$04,$b8,$04,$ba,$04,$78,$04,$bc,$04,$be,$04,$ca,$04
    dc.b    $c0,$04,$7a,$04,$7c,$04,$7e,$04,$8a,$04,$8c,$04,$80,$04,$c2,$04
    dc.b    $80,$04,$b6,$04,$b8,$04,$ba,$04,$c4,$04,$bc,$04,$be,$04,$8e,$04
    dc.b    $c0,$04,$90,$04,$80,$04,$c6,$ff,$ff,$04,$80,$04,$80,$04,$c2,$04
    dc.b    $80,$04,$b6,$04,$b8,$04,$ba,$04,$c4,$04,$bc,$04,$be,$04,$ca,$04
    dc.b    $c0,$04,$ce,$04,$d0,$04,$d6,$04,$f4,$04,$f6,$04,$80,$04,$c2,$04
    dc.b    $80,$04,$b6,$04,$b8,$04,$ba,$04,$c4,$04,$bc,$04,$be,$04,$cc,$04
    dc.b    $c0,$04,$f8,$04,$80,$04,$fa,$04,$cc,$04,$80,$04,$80,$04,$c2,$04
    dc.b    $80,$04,$fe,$05,$06,$05,$08,$04,$c4,$05,$0c,$05,$16,$05,$1c,$05
    dc.b    $1e,$04,$ce,$04,$d0,$04,$d6,$04,$f4,$04,$f6,$05,$20,$ff,$ff,$05
    dc.b    $20,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$05,$48,$05,$52,$04,$cc,$ff
    dc.b    $ff,$04,$f8,$ff,$ff,$04,$fa,$04,$cc,$05,$34,$05,$4a,$05,$34,$ff
    dc.b    $ff,$04,$fe,$05,$06,$05,$08,$05,$56,$05,$0c,$05,$16,$05,$1c,$05
    dc.b    $1e,$05,$4a,$05,$5c,$05,$62,$05,$8c,$05,$4a,$05,$20,$05,$26,$05
    dc.b    $20,$05,$26,$05,$26,$05,$26,$05,$26,$05,$48,$05,$52,$05,$98,$05
    dc.b    $26,$05,$26,$05,$26,$05,$a0,$05,$26,$05,$34,$05,$4a,$05,$34,$05
    dc.b    $26,$05,$96,$05,$26,$05,$a4,$05,$56,$05,$a8,$05,$98,$05,$9a,$05
    dc.b    $96,$05,$4a,$05,$5c,$05,$62,$05,$8c,$05,$4a,$05,$9a,$05,$26,$05
    dc.b    $96,$05,$26,$05,$26,$05,$26,$05,$26,$05,$9c,$05,$9a,$05,$98,$05
    dc.b    $26,$05,$26,$05,$26,$05,$a0,$05,$26,$05,$aa,$05,$ac,$05,$b2,$05
    dc.b    $26,$05,$96,$05,$26,$05,$a4,$05,$9c,$05,$a8,$05,$98,$05,$9a,$05
    dc.b    $96,$05,$b8,$05,$bc,$05,$be,$05,$aa,$05,$ac,$05,$9a,$05,$c0,$05
    dc.b    $96,$05,$c2,$05,$c8,$05,$cc,$05,$ce,$05,$9c,$05,$9a,$05,$ca,$05
    dc.b    $d6,$05,$da,$05,$de,$05,$e0,$05,$e4,$05,$aa,$05,$ac,$05,$b2,$05
    dc.b    $ec,$05,$ca,$06,$04,$06,$14,$05,$9c,$06,$18,$ff,$ff,$ff,$ff,$06
    dc.b    $1a,$05,$b8,$05,$bc,$05,$be,$05,$aa,$05,$ac,$06,$1c,$05,$c0,$06
    dc.b    $1e,$05,$c2,$05,$c8,$05,$cc,$05,$ce,$06,$20,$06,$22,$05,$ca,$05
    dc.b    $d6,$05,$da,$05,$de,$05,$e0,$05,$e4,$06,$16,$06,$16,$06,$16,$05
    dc.b    $ec,$05,$ca,$06,$04,$06,$14,$06,$16,$06,$18,$06,$16,$06,$16,$06
    dc.b    $1a,$06,$24,$06,$26,$06,$16,$06,$16,$06,$16,$06,$1c,$06,$2c,$06
    dc.b    $1e,$06,$3c,$06,$3e,$06,$40,$06,$42,$06,$20,$06,$22,$06,$64,$06
    dc.b    $6c,$06,$6e,$06,$76,$06,$66,$06,$72,$06,$16,$06,$16,$06,$16,$06
    dc.b    $66,$06,$72,$06,$7c,$ff,$ff,$06,$16,$ff,$ff,$06,$16,$06,$16,$ff
    dc.b    $ff,$06,$24,$06,$26,$06,$16,$06,$16,$06,$16,$06,$80,$06,$2c,$06
    dc.b    $82,$06,$3c,$06,$3e,$06,$40,$06,$42,$06,$92,$06,$8c,$06,$64,$06
    dc.b    $6c,$06,$6e,$06,$76,$06,$66,$06,$72,$06,$74,$06,$74,$06,$74,$06
    dc.b    $66,$06,$72,$06,$7c,$06,$74,$06,$a6,$06,$74,$06,$8c,$06,$cc,$06
    dc.b    $74,$06,$ce,$06,$d6,$06,$dc,$06,$e0,$06,$e2,$06,$80,$06,$74,$06
    dc.b    $82,$06,$e4,$06,$ec,$06,$74,$06,$ee,$06,$92,$06,$8c,$06,$f8,$07
    dc.b    $00,$06,$f6,$07,$02,$06,$f6,$06,$f8,$06,$74,$06,$74,$06,$74,$06
    dc.b    $f6,$06,$f4,$06,$f8,$06,$74,$06,$a6,$06,$74,$06,$8c,$06,$cc,$06
    dc.b    $74,$06,$ce,$06,$d6,$06,$dc,$06,$e0,$06,$e2,$06,$f2,$06,$74,$06
    dc.b    $f4,$06,$e4,$06,$ec,$06,$74,$06,$ee,$06,$f2,$07,$08,$06,$f8,$07
    dc.b    $00,$06,$f6,$07,$02,$06,$f6,$06,$f8,$06,$f2,$06,$fa,$06,$fa,$06
    dc.b    $f6,$06,$f4,$06,$f8,$06,$fe,$07,$0a,$06,$fe,$07,$0e,$06,$fa,$07
    dc.b    $22,$07,$24,$06,$fe,$07,$2a,$06,$fe,$06,$fa,$06,$f2,$07,$1c,$06
    dc.b    $f4,$07,$3c,$07,$2c,$ff,$ff,$ff,$ff,$06,$f2,$07,$08,$ff,$ff,$07
    dc.b    $3e,$07,$50,$07,$5e,$07,$2a,$07,$1c,$06,$f2,$06,$fa,$06,$fa,$07
    dc.b    $1c,$07,$1c,$07,$2c,$06,$fe,$07,$0a,$06,$fe,$07,$0e,$06,$fa,$07
    dc.b    $22,$07,$24,$06,$fe,$07,$2a,$06,$fe,$06,$fa,$07,$2e,$07,$1c,$ff
    dc.b    $ff,$07,$3c,$07,$2c,$07,$30,$07,$32,$07,$34,$07,$36,$07,$38,$07
    dc.b    $3e,$07,$50,$07,$5e,$07,$2a,$07,$1c,$07,$6a,$07,$2e,$07,$72,$07
    dc.b    $1c,$07,$1c,$07,$2c,$07,$30,$07,$32,$07,$34,$07,$36,$07,$38,$07
    dc.b    $76,$07,$68,$07,$6c,$07,$6e,$07,$6a,$07,$7a,$07,$2e,$ff,$ff,$07
    dc.b    $68,$07,$6c,$07,$7c,$07,$30,$07,$32,$07,$34,$07,$36,$07,$38,$07
    dc.b    $68,$07,$6c,$07,$6e,$07,$88,$07,$8c,$07,$6a,$07,$2e,$07,$72,$07
    dc.b    $7e,$07,$7c,$07,$96,$07,$30,$07,$32,$07,$34,$07,$36,$07,$38,$07
    dc.b    $76,$07,$68,$07,$6c,$07,$6e,$07,$6a,$07,$7a,$07,$c2,$07,$7e,$07
    dc.b    $68,$07,$6c,$07,$7c,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$07
    dc.b    $68,$07,$6c,$07,$6e,$07,$88,$07,$8c,$ff,$ff,$ff,$ff,$ff,$ff,$07
    dc.b    $7e,$07,$7c,$07,$96,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$07,$c2,$07,$7e,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff
sub_e070:
    dcb.b   8,0
    dc.b    $0d,$fe
    dcb.b   286,0
    dc.b    $0c,$e6,$00,$02
    dcb.b   8,0
    dc.b    $0d,$c8
    dcb.b   130,0
    dc.b    $4e,$1a
    dcb.b   116,0
    dc.b    $80,$00,$13,$0e,$80,$00,$00,$00
sub_e2a6:
    dcb.b   90,0
    dc.b    $2b,$ce
    dcb.b   26,0
    dc.b    $51,$c0,$2d,$42,$80
    dcb.b   37,0
    dc.b    $50,$c0,$2d,$42,$80
    dcb.b   49,0
    dc.b    $51,$f8,$30,$14,$80
    dcb.b   49,0
    dc.b    $50,$f8,$30,$14,$80
    dcb.b   31,0
    dc.b    $d0,$00,$01,$5e,$80,$00,$c0,$00,$13,$0e,$80,$00,$e1,$00,$2e,$98
    dc.b    $80,$00,$e0,$00,$2e,$98,$80,$00,$64,$00,$02,$f4
hint_e3f2:
    dc.b    $80
    dcb.b   13,0
    dc.b    $65,$00,$02,$f4
hint_e404:
; --- unverified ---
    or.b d0,d0
    beq.w hint_e6fc
hint_e40a:
    dc.b    $80
    dcb.b   37,0
    dc.b    $6c,$00,$02,$f4
hint_e434:
    dc.b    $80
    dcb.b   7,0
    dc.b    $6e,$00,$02,$f4,$80,$00,$62,$00,$02,$f4,$80
    dcb.b   7,0
    dc.b    $6f,$00,$02,$f4
hint_e452:
; --- unverified ---
    or.b d0,d0
    bls.w hint_e74a
hint_e458:
; --- unverified ---
    or.b d0,d0
    blt.w hint_e750
hint_e45e:
; --- unverified ---
    or.b d0,d0
    bmi.w hint_e756
hint_e464:
; --- unverified ---
    or.b d0,d0
    bne.w hint_e75c
hint_e46a:
; --- unverified ---
    or.b d0,d0
    bpl.w hint_e762
hint_e470:
; --- unverified ---
    or.b d0,d0
    bra.w hint_e768
hint_e476:
    dc.b    $80
    dcb.b   7,0
    dc.b    $61,$00,$02,$f4,$80,$00,$00,$00,$2d,$5a
    dcb.b   8,0
    dc.b    $68,$00
    dc.b    $02,$f4,$80,$00,$69,$00,$02,$f4,$80
    dcb.b   13,0
    dc.b    $08,$c0,$06,$ec,$80,$00,$41,$80,$08,$da,$80
    dcb.b   7,0
    dc.b    $42,$00,$30,$72,$80,$00,$b0,$00,$0a,$5c,$80
    dcb.b   49,0
    dc.b    $51,$c8,$0b,$cc,$80
    dcb.b   43,0
    dc.b    $50,$c8,$0b,$cc,$80
    dcb.b   9,0
    dc.b    $0c,$18
    dcb.b   16,0
    dc.b    $0d,$e6,$40,$00,$b0,$00,$13,$0e,$80,$00,$00,$00,$0d,$fe
    dcb.b   8,0
    dc.b    $c1,$00,$0e,$fa,$80,$00,$48,$80,$0f,$50,$80
    dcb.b   43,0
    dc.b    $f0,$80,$3c,$48,$80,$01
    dcb.b   30,0
    dc.b    $f0,$8f,$3c,$48,$80,$01
    dcb.b   158,0
    dc.b    $41,$22,$80,$01
    dcb.b   49,0
    dc.b    $0f,$41,$22,$80,$01
    dcb.b   44,0
    dc.b    $4d,$40
    dcb.b   4,0
    dc.b    $4d,$76,$00,$00
sub_e6ca:
    dcb.b   26,0
hint_e6e4:
    dc.b    $0f,$f2
hint_e6f6:
    dc.b    $10,$f0,$80,$00,$4e,$80
hint_e6fc:
    dc.b    $10,$f0,$80,$00,$41,$c0,$11,$00,$80
    dcb.b   25,0
    dc.b    $e1,$08,$2e,$98,$80,$00,$e0,$08
hint_e726:
    dc.b    $2e,$98,$80
    dcb.b   27,0
hint_e744:
    dc.b    $00,$00
hint_e74a:
    dcb.b   4,0
    dc.b    $44,$00
hint_e750:
    dc.b    $30,$72,$80
    dc.b    $00
    dc.b    $00,$00
hint_e756:
    dc.b    $00,$00
hint_e75c:
    dc.b    $58,$f0,$80,$00,$46,$00
hint_e762:
    dc.b    $30,$72,$80
    dc.b    $00
    dc.b    $00,$00
hint_e768:
    dc.b    $00,$00
hint_e870:
    dc.b    $58,$e4,$80,$00,$06,$c0,$2d,$0e,$80,$00,$4e,$77
hint_e87c:
; --- unverified ---
    svc 0(a0,a0.w)
    rts
hint_e882:
    dc.b    $58,$f0,$80
    dcb.b   7,0
    dc.b    $54,$c0,$2d,$42,$80,$00,$55,$c0,$2d,$42,$80
    dcb.b   7,0
    dc.b    $57,$c0,$2d,$42,$80,$00,$00,$00,$2e,$16,$00,$00,$5c,$c0,$2d,$42
    dc.b    $80,$00,$5e,$c0,$2d,$42,$80,$00,$52,$c0,$2d,$42,$80,$00,$5f,$c0
    dc.b    $2d,$42,$80,$00,$53,$c0,$2d,$42,$80,$00,$5d,$c0,$2d,$42,$80,$00
    dc.b    $5b,$c0,$2d,$42,$80,$00,$56,$c0,$2d,$42,$80,$00,$00,$00,$2f,$20
    dc.b    $40,$00,$5a,$c0,$2d,$42,$80
    dcb.b   7,0
    dc.b    $90,$00,$01,$5e,$80,$00,$58,$c0,$2d,$42,$80,$00,$59,$c0,$2d,$42
    dc.b    $80
    dcb.b   7,0
    dc.b    $4a,$c0,$2f,$86,$80
    dcb.b   7,0
    dc.b    $54,$f8,$30,$14,$80,$00,$55,$f8,$30,$14,$80
    dcb.b   7,0
    dc.b    $57,$f8,$30,$14,$80
    dcb.b   7,0
    dc.b    $5c,$f8,$30,$14,$80,$00,$5e,$f8,$30,$14,$80,$00,$52,$f8,$30,$14
    dc.b    $80,$00,$5f,$f8,$30,$14,$80,$00,$53,$f8,$30,$14,$80,$00,$5d,$f8
    dc.b    $30,$14,$80,$00,$5b,$f8,$30,$14,$80,$00,$56,$f8,$30,$14,$80
    dcb.b   7,0
    dc.b    $5a,$f8,$30,$14,$80
    dcb.b   13,0
    dc.b    $50,$f8,$30,$14,$80
    dcb.b   7,0
    dc.b    $4a,$00
    dc.b    $30,$7e,$80,$00,$00,$00,$30,$92,$40,$00,$58,$f8,$30,$14,$80,$00
    dc.b    $59,$f8,$30,$14,$80
    dcb.b   25,0
    dc.b    $c1,$00,$00,$08,$80,$00,$d0,$c0,$02,$1e,$80,$00,$06,$00,$02,$a0
    dc.b    $80,$00,$50,$00,$15,$04,$80,$00,$d1,$00,$00,$02,$80,$00,$02,$00
    dc.b    $12,$8a,$80,$00,$08,$40,$06,$64,$80,$00,$08,$80,$06,$64,$80
    dcb.b   43,0
    dc.b    $4a,$fa,$4b,$1e,$80,$00,$48,$48,$04,$6a,$80,$00,$08,$c0,$06,$64
    dc.b    $80,$00,$08,$00,$05,$e6,$80
    dcb.b   13,0
    dc.b    $0c,$fc,$07,$4e,$80,$00,$08,$c0,$09,$1a,$80
    dcb.b   8,0
    dc.b    $c0,$09,$1a,$80,$00,$b0,$c0,$02,$1e,$80,$00,$0c,$00,$02,$c6,$80
    dc.b    $00,$b1,$08,$0b,$16,$80,$00,$00,$00,$0b,$4a
    dcb.b   4,0
    dc.b    $2d,$68
    dcb.b   22,0
    dc.b    $2d,$52,$00,$00,$54,$c8,$0b,$cc,$80,$00,$55,$c8,$0b,$cc,$80,$00
    dc.b    $57,$c8,$0b,$cc,$80,$00,$5c,$c8,$0b,$cc,$80,$00,$5e,$c8,$0b,$cc
    dc.b    $80,$00,$52,$c8,$0b,$cc,$80,$00,$5f,$c8,$0b,$cc,$80,$00,$53,$c8
    dc.b    $0b,$cc,$80,$00,$5d,$c8,$0b,$cc,$80,$00,$5b,$c8,$0b,$cc,$80,$00
    dc.b    $56,$c8,$0b,$cc,$80,$00,$5a,$c8,$0b,$cc,$80,$00,$51,$c8,$0b,$cc
    dc.b    $80,$00,$58,$c8,$0b,$cc,$80,$00,$59,$c8,$0b,$cc,$80,$00,$81,$c0
    dc.b    $09,$ba,$80,$00,$80,$c0,$09,$ba,$80,$00,$00,$00,$4f,$78,$40,$00
    dc.b    $00,$00,$4f,$54
    dcb.b   10,0
    dc.b    $55,$80
    dcb.b   4,0
    dc.b    $57,$22,$00,$00,$0a,$00,$12,$8a,$80
    dcb.b   9,0
    dc.b    $0e,$82
    dcb.b   4,0
    dc.b    $0e,$ec,$80,$00,$49,$c0,$0f,$6a,$80,$00,$48,$80,$0f,$82,$80,$00
    dc.b    $00,$18,$40,$80,$80,$01
    dcb.b   7,0
    dc.b    $22,$40,$80,$80,$01,$00,$00,$0f,$9c,$40
    dcb.b   13,0
    dc.b    $f0,$81,$3c,$48,$80,$01,$f0,$93,$3c,$48,$80,$01,$f0,$96,$3c,$48
    dc.b    $80,$01,$f0,$92,$3c,$48,$80,$01,$f0,$95,$3c,$48,$80,$01,$f0,$94
    dc.b    $3c,$48,$80,$01,$f0,$8e,$3c,$48,$80,$01
    dcb.b   24,0
    dc.b    $f0,$87,$3c,$48,$80,$01
    dcb.b   6,0
    dc.b    $f0,$90,$3c,$48,$80,$01
    dcb.b   6,0
    dc.b    $f0,$9f,$3c,$48,$80,$01
    dcb.b   18,0
    dc.b    $f0,$88,$3c,$48,$80,$01,$00,$38,$40,$80,$80,$01,$00,$1d,$40,$80
    dc.b    $80,$01
    dcb.b   20,0
    dc.b    $3c,$50,$80,$01
    dcb.b   37,0
    dc.b    $0f,$3c,$50,$80,$01
    dcb.b   13,0
    dc.b    $20,$40,$80,$80,$01
    dcb.b   32,0
    dc.b    $3b,$6c,$00,$01
    dcb.b   13,0
    dc.b    $01,$40,$80,$80,$01
    dcb.b   7,0
    dc.b    $21,$40,$80,$80,$01
    dcb.b   7,0
    dc.b    $23,$40,$80,$80,$01,$00,$1a,$40,$80,$80,$01,$f0,$80,$40,$46,$80
    dc.b    $01,$00,$00,$3a,$c8,$40
    dcb.b   8,0
    dc.b    $25,$40,$80,$80,$01
    dcb.b   37,0
    dc.b    $01,$41,$22,$80,$01,$00,$13,$41,$22,$80,$01,$00,$16,$41,$22,$80
    dc.b    $01,$00,$12,$41,$22,$80,$01,$00,$0e,$40,$80,$80,$01,$00,$15,$41
    dc.b    $22,$80,$01,$00,$14,$41,$22,$80,$01
    dcb.b   13,0
    dc.b    $0e,$41,$22,$80,$01
    dcb.b   25,0
    dc.b    $07,$41,$22,$80,$01
    dcb.b   13,0
    dc.b    $10,$41,$22,$80,$01
    dcb.b   13,0
    dc.b    $1f,$41,$22,$80,$01
    dcb.b   7,0
    dc.b    $28,$40,$80,$80,$01
    dcb.b   19,0
    dc.b    $08,$41,$22,$80,$01,$00,$0f,$40,$80,$80,$01
    dcb.b   13,0
    dc.b    $3a,$41,$c8,$80,$01
    dcb.b   8,0
    dc.b    $15,$52
    dcb.b   4,0
    dc.b    $4e,$14
    dcb.b   4,0
    dc.b    $4e,$02
    dcb.b   4,0
    dc.b    $4d,$fc
    dcb.b   4,0
    dc.b    $4e,$0e
    dcb.b   4,0
    dc.b    $4e,$08
    dcb.b   4,0
    dc.b    $4d,$48
    dcb.b   4,0
    dc.b    $4d,$8a
    dcb.b   4,0
    dc.b    $4e,$1a
    dcb.b   26,0
    dc.b    $4e,$50,$11,$ae,$80,$00,$00,$00,$ea,$a8,$40,$00,$00,$00,$12,$68
    dc.b    $40
    dcb.b   33,0
    dc.b    $16,$30,$80,$00,$c1,$c0,$09,$ba,$80,$00,$c0,$c0,$09,$ba,$80,$00
    dc.b    $48,$00,$1c,$aa,$80,$00,$40,$00,$30,$72,$80
    dcb.b   25,0
    dc.b    $81,$40,$2a,$76,$80,$00,$00,$00,$2a,$c2,$40,$00,$f0,$87,$44,$96
    dc.b    $80,$ff,$f0,$86,$44,$96,$80,$ff,$f0,$81,$44,$96,$80,$ff,$f0,$80
    dc.b    $44,$96,$80,$ff,$f0,$8f,$44,$96,$80,$ff,$f0,$8e,$44,$96,$80,$ff
    dc.b    $f0,$8d,$44,$96,$80,$ff,$f0,$8c,$44,$96,$80,$ff,$f0,$8b,$44,$96
    dc.b    $80,$ff,$f0,$8a,$44,$96,$80,$ff,$f0,$83,$44,$96,$80,$ff,$f0,$82
    dc.b    $44,$96,$80,$ff,$f0,$85,$44,$96,$80,$ff,$f0,$84,$44,$96,$80,$ff
    dc.b    $f0,$89,$44,$96,$80,$ff,$f0,$88,$44,$96,$80,$ff
    dcb.b   56,0
    dc.b    $2a,$e2,$40
    dcb.b   26,0
    dc.b    $07,$49,$60,$80,$ff,$00,$06,$49,$60,$80,$ff
    dcb.b   7,0
    dc.b    $01,$49,$60,$80,$ff,$00,$00,$49,$60,$80,$ff,$00,$0f,$49,$60,$80
    dc.b    $ff,$00,$0e,$49,$60,$80,$ff,$00,$0d,$49,$60,$80,$ff,$00,$0c,$49
    dc.b    $60,$80,$ff,$00,$0b,$49,$60,$80,$ff,$00,$0a,$49,$60,$80,$ff,$00
    dc.b    $03,$49,$60,$80,$ff,$00,$02,$49,$60,$80,$ff,$00,$05,$49,$60,$80
    dc.b    $ff,$00,$04,$49,$60,$80,$ff,$00,$09,$49,$60,$80,$ff,$00,$08,$49
    dc.b    $60,$80,$ff
    dcb.b   26,0
    dc.b    $55,$d6
    dcb.b   10,0
    dc.b    $2c,$98,$00,$00,$e1,$10,$2e,$98,$80,$00,$e0,$10,$2e,$98,$80
    dcb.b   13,0
    dc.b    $81,$00,$00,$08,$80
    dcb.b   7,0
    dc.b    $4e,$72,$2f,$4e,$80,$00,$90,$c0,$02,$1e,$80,$00,$04,$00,$02,$a0
    dc.b    $80,$00,$51,$00,$15,$04,$80
    dcb.b   7,0
    dc.b    $91,$00,$00,$02,$80,$00,$48,$40,$2f,$78,$80,$00,$08,$00,$4b,$64
    dc.b    $80,$00,$00,$00,$4b,$64,$80
    dcb.b   9,0
    dc.b    $2d,$60,$00,$00,$5a,$f8,$30,$14,$80,$00,$4e,$40,$2f,$92,$80,$00
    dc.b    $4e,$58,$30,$e0,$80,$00,$81,$80,$2a,$76,$80,$00,$00,$00,$31,$04
    dc.b    $40,$00,$00,$00,$31,$5e,$40,$00,$ea,$c0,$05,$1a,$80,$00,$ec,$c0
    dc.b    $05,$1a,$80
    dcb.b   7,0
    dc.b    $ed,$c0,$04,$d0,$80,$00,$ef,$c0,$04,$92,$80,$00,$ee,$c0,$05,$1a
    dc.b    $80,$00,$e8,$c0,$05,$1a,$80,$00,$06,$c0,$06,$b2,$80,$00,$00,$00
    dc.b    $08,$06,$80,$00,$f4,$18,$4b,$c2,$80,$00,$f4,$08,$4b,$ee,$80,$00
    dc.b    $f4,$10,$4b,$ee,$80
    dcb.b   15,0
    dc.b    $2d,$90,$80,$00,$4c,$40,$09,$6a,$80,$00,$4c,$40,$09,$66,$80
    dcb.b   9,0
    dc.b    $4f,$54
    dcb.b   9,0
    dc.b    $1c,$40,$80,$80,$01,$00,$0c,$40,$80,$80,$01,$00,$0a,$40,$80,$80
    dc.b    $01,$f0,$97,$3c,$48,$80,$01,$f0,$9c,$3c,$48,$80,$01,$f0,$99,$3c
    dc.b    $48,$80,$01,$f0,$9d,$3c,$48,$80,$01,$f0,$9a,$3c,$48,$80,$01,$f0
    dc.b    $9b,$3c,$48,$80,$01,$f0,$83,$3c,$48,$80,$01,$f0,$86,$3c,$48,$80
    dc.b    $01,$f0,$82,$3c,$48,$80,$01,$f0,$85,$3c,$48,$80,$01,$f0,$84,$3c
    dc.b    $48,$80,$01,$f0,$91,$3c,$48,$80,$01,$f0,$9e,$3c,$48,$80,$01,$f0
    dc.b    $89,$3c,$48,$80,$01,$f0,$8b,$3c,$48,$80,$01,$f0,$8a,$3c,$48,$80
    dc.b    $01,$f0,$8d,$3c,$48,$80,$01,$f0,$8c,$3c,$48,$80,$01,$00,$19,$40
    dc.b    $80,$80,$01,$00,$5c,$40,$6c,$80,$01,$00,$66,$40,$6c,$80,$01,$00
    dc.b    $01,$3c,$50,$80,$01,$00,$13,$3c,$50,$80,$01,$00,$16,$3c,$50,$80
    dc.b    $01,$00,$12,$3c,$50,$80,$01,$00,$15,$3c,$50,$80,$01,$00,$14,$3c
    dc.b    $50,$80,$01,$00,$0e,$3c,$50,$80,$01
    dcb.b   25,0
    dc.b    $07,$3c,$50,$80,$01
    dcb.b   7,0
    dc.b    $10,$3c,$50,$80,$01
    dcb.b   7,0
    dc.b    $1f,$3c,$50,$80,$01
    dcb.b   19,0
    dc.b    $08,$3c,$50,$80,$01,$00,$64,$40,$6c,$80,$01
    dcb.b   7,0
    dc.b    $67,$40,$6c,$80,$01,$00,$5e,$40,$6c,$80,$01
    dcb.b   7,0
    dc.b    $6c,$40,$6c,$80,$01,$00,$10,$40,$80,$80,$01
    dcb.b   25,0
    dc.b    $16,$40,$80,$80,$01,$00,$14,$40,$80,$80,$01,$00,$00,$3c,$64,$80
    dc.b    $01
    dcb.b   13,0
    dc.b    $58,$40,$6c,$80,$01,$00,$62,$40,$6c,$80,$01,$f1,$00,$41,$02,$80
    dc.b    $01
    dcb.b   7,0
    dc.b    $60,$40,$6c,$80,$01
    dcb.b   7,0
    dc.b    $17,$41,$22,$80,$01
    dcb.b   13,0
    dc.b    $02,$40,$80,$80,$01
    dcb.b   7,0
    dc.b    $63,$40,$6c,$80,$01,$00,$5a,$40,$6c,$80,$01,$00,$1c,$41,$22,$80
    dc.b    $01,$00,$19,$41,$22,$80,$01,$00,$1d,$41,$22,$80,$01,$00,$1a,$41
    dc.b    $22,$80,$01,$00,$1b,$41,$22,$80,$01,$00,$03,$41,$22,$80,$01,$00
    dc.b    $06,$41,$22,$80,$01,$00,$02,$41,$22,$80,$01,$00,$05,$41,$22,$80
    dc.b    $01,$00,$04,$41,$22,$80,$01,$00,$04,$40,$80,$80,$01,$00,$11,$41
    dc.b    $22,$80,$01,$00,$1e,$41,$22,$80,$01
    dcb.b   7,0
    dc.b    $68,$40,$6c,$80,$01,$00,$09,$41,$22,$80,$01,$00,$0b,$41,$22,$80
    dc.b    $01,$00,$0a,$41,$22,$80,$01,$00,$0d,$41,$22,$80,$01,$00,$0c,$41
    dc.b    $22,$80,$01,$00,$09,$40,$80,$80,$01
    dcb.b   62,0
    dc.b    $4f,$dc
    dcb.b   4,0
    dc.b    $55,$70
    dcb.b   14,0
    dc.b    $20,$40,$1a,$64,$80,$00,$4e,$7a,$17,$84,$80,$00,$48,$80,$19,$28
    dc.b    $80,$00,$01,$08,$1a,$ee,$80,$00,$70,$00,$1b,$ba,$80,$00,$0e,$00
    dc.b    $1c,$36,$80
    dcb.b   26,0
    dc.b    $07,$44,$d2,$80,$ff,$00,$06,$44,$d2,$80,$ff,$00,$01,$44,$d2,$80
    dc.b    $ff,$00,$00,$44,$d2,$80,$ff,$00,$0f,$44,$d2,$80,$ff,$00,$0e,$44
    dc.b    $d2,$80,$ff,$00,$0d,$44,$d2,$80,$ff,$00,$0c,$44,$d2,$80,$ff,$00
    dc.b    $0b,$44,$d2,$80,$ff,$00,$0a,$44,$d2,$80,$ff,$00,$03,$44,$d2,$80
    dc.b    $ff,$00,$02,$44,$d2,$80,$ff,$00,$05,$44,$d2,$80,$ff,$00,$04,$44
    dc.b    $d2,$80,$ff,$00,$09,$44,$d2,$80,$ff,$00,$08,$44,$d2,$80,$ff
    dcb.b   13,0
    dc.b    $40,$49,$9a,$80,$ff,$00,$00,$49,$9a,$80,$ff,$f0,$00,$47,$d0,$80
    dc.b    $ff
    dcb.b   6,0
    dc.b    $f1,$00,$49,$3c,$80,$ff
    dcb.b   20,0
    dc.b    $2b,$06,$40,$00,$4e,$70,$58,$e4,$80
    dcb.b   9,0
    dc.b    $2c,$de,$40
    dcb.b   13,0
    dc.b    $0c,$00,$4b,$64,$80,$00,$04,$00,$4b,$64,$80,$00,$08,$00,$2f,$c0
    dc.b    $80,$00,$00,$00,$2f,$c0,$80,$00,$4e,$76,$58,$f0,$80,$00,$eb,$c0
    dc.b    $04,$d0,$80,$00,$e9,$c0,$04,$d0,$80
    dcb.b   7,0
    dc.b    $f4,$38,$4b,$c2,$80,$00,$f4,$28,$4b,$ee,$80,$00,$f4,$30,$4b,$ee
    dc.b    $80,$00,$00,$00,$4f,$78,$40,$00,$00,$00
sub_f446:
    dc.b    $0e,$76,$00,$00,$00,$0d,$40,$80,$80,$01,$f0,$98,$3c,$48
hint_f454:
    dc.b    $80,$01,$00,$17,$3c,$50,$80,$01,$00,$1c,$3c,$50,$80,$01,$00,$19
    dc.b    $3c,$50,$80,$01,$00,$1d,$3c,$50,$80,$01,$00,$1a,$3c,$50,$80,$01
    dc.b    $00,$1b,$3c,$50,$80,$01,$00,$03,$3c,$50,$80,$01,$00,$06,$3c,$50
    dc.b    $80,$01,$00,$02,$3c,$50,$80,$01,$00,$05,$3c,$50,$80,$01,$00,$04
    dc.b    $3c,$50,$80,$01,$00,$11,$3c,$50,$80,$01,$00,$1e,$3c,$50,$80,$01
    dc.b    $00,$09,$3c,$50,$80,$01,$00,$0b,$3c,$50,$80,$01,$00,$0a,$3c,$50
    dc.b    $80,$01,$00,$0d,$3c,$50,$80,$01,$00,$0c,$3c,$50,$80,$01,$00,$44
    dc.b    $40,$80,$80,$01,$00,$45,$40,$6c,$80,$01
    dcb.b   19,0
    dc.b    $03,$40,$80,$80,$01,$00,$15,$40,$80,$80,$01
    dcb.b   12,0
    dc.b    $c0,$00,$3e,$42,$80,$01,$00,$00,$0f,$a4,$40
    dcb.b   8,0
    dc.b    $26,$40,$80,$80,$01
    dcb.b   19,0
    dc.b    $40,$40,$80,$80,$01,$00,$18,$41,$22,$80,$01,$00,$41,$40,$6c,$80
    dc.b    $01
    dcb.b   14,0
    dc.b    $41,$b2,$80,$01
    dcb.b   31,0
    dc.b    $0f,$41,$b2,$80,$01
    dcb.b   20,0
    dc.b    $10,$1c,$80,$00,$00,$00,$10,$ca,$40
    dcb.b   13,0
    dc.b    $01,$c0,$4b,$2c,$80
    dcb.b   9,0
    dc.b    $15,$52,$80,$00,$f6,$00,$4c,$20,$80,$00,$00,$00,$ec,$9c,$40,$00
    dc.b    $00,$00,$2a,$da,$40,$00,$00,$00,$1c,$b6
    dcb.b   4,0
    dc.b    $2a,$44,$40,$00
    dc.b    $f0,$00,$45,$e0,$80,$ff,$22,$00,$47,$76,$80,$ff,$20,$00,$47,$76
    dc.b    $80,$ff
    dcb.b   12,0
    dc.b    $82,$00,$49,$9a,$80,$ff,$80,$00,$49,$9a,$80,$ff
    dcb.b   48,0
    dc.b    $f0,$00,$4a,$a4,$80,$ff
    dcb.b   14,0
    dc.b    $30,$da,$40,$00,$00,$00,$0b,$a6,$40,$00,$00,$18,$3c,$50,$80,$01
    dc.b    $00,$08,$40,$80,$80,$01,$00,$1e,$40,$80,$80,$01,$00,$1f,$40,$80
    dc.b    $80,$01,$00,$05,$40,$80,$80,$01,$f0,$00,$3f,$f6,$80,$01
    dcb.b   7,0
    dc.b    $24,$40,$80,$80,$01,$00,$27,$40,$80,$80,$01,$f0,$00,$41,$36,$80
    dc.b    $01,$00,$12,$40,$80,$80,$01,$00,$01,$41,$b2,$80,$01,$00,$13,$41
    dc.b    $b2,$80,$01,$00,$16,$41,$b2,$80,$01,$00,$12,$41,$b2,$80,$01,$00
    dc.b    $15,$41,$b2,$80,$01,$00,$14,$41,$b2,$80,$01,$00,$0e,$41,$b2,$80
    dc.b    $01
    dcb.b   25,0
    dc.b    $07,$41,$b2,$80,$01
    dcb.b   7,0
    dc.b    $10,$41,$b2,$80,$01
    dcb.b   7,0
    dc.b    $1f,$41,$b2,$80,$01
    dcb.b   19,0
    dc.b    $08,$41,$b2,$80,$01,$00,$11,$40,$80,$80,$01,$4a,$fc,$58,$f0,$80
    dc.b    $00,$00,$00,$10,$d6,$40
    dcb.b   9,0
    dc.b    $13,$90,$40,$00,$f0,$00,$45,$32,$80,$ff,$f5,$00,$45,$7a,$80,$ff
    dc.b    $f0,$00,$47,$4c,$80,$ff,$f0,$00,$47,$28,$80,$ff,$f0,$00,$47,$b0
    dc.b    $80,$ff
    dcb.b   7,0
    dc.b    $07,$4a,$7e,$80,$ff,$00,$06,$4a,$7e,$80,$ff,$00,$01,$4a,$7e,$80
    dc.b    $ff,$00,$00,$4a,$7e,$80,$ff,$00,$0f,$4a,$7e,$80,$ff,$00,$0e,$4a
    dc.b    $7e,$80,$ff,$00,$0d,$4a,$7e,$80,$ff,$00,$0c,$4a,$7e,$80,$ff,$00
    dc.b    $0b,$4a,$7e,$80,$ff,$00,$0a,$4a,$7e,$80,$ff,$00,$03,$4a,$7e,$80
    dc.b    $ff,$00,$02,$4a,$7e,$80,$ff,$00,$05,$4a,$7e,$80,$ff,$00,$04,$4a
    dc.b    $7e,$80,$ff,$00,$09,$4a,$7e,$80,$ff,$00,$08,$4a,$7e,$80,$ff,$00
    dc.b    $00,$2c,$d6,$40,$00,$00,$00,$2e,$04,$00,$00,$f1,$40,$40,$e2,$80
    dc.b    $01,$00,$17,$41,$b2,$80,$01,$00,$1c,$41,$b2,$80,$01,$00,$19,$41
    dc.b    $b2,$80,$01,$00,$1d,$41,$b2,$80,$01,$00,$1a,$41,$b2,$80,$01,$00
    dc.b    $1b,$41,$b2,$80,$01,$00,$03,$41,$b2,$80,$01,$00,$06,$41,$b2,$80
    dc.b    $01,$00,$02,$41,$b2,$80,$01,$00,$05,$41,$b2,$80,$01,$00,$04,$41
    dc.b    $b2,$80,$01,$00,$11,$41,$b2,$80,$01,$00,$1e,$41,$b2,$80,$01,$00
    dc.b    $09,$41,$b2,$80,$01,$00,$0b,$41,$b2,$80,$01,$00,$0a,$41,$b2,$80
    dc.b    $01,$00,$0d,$41,$b2,$80,$01,$00,$0c,$41,$b2,$80,$01,$00,$00,$12
    dc.b    $3e,$40,$00,$f5,$10,$45,$be,$80,$ff,$f1,$40,$49,$18,$80,$ff,$00
    dc.b    $18,$41,$b2,$80,$01
loc_f82e:
    rts
loc_f830:
    rts
sub_f832:
; --- unverified ---
    tst.b 259(a6) ; app+$103
    beq.s hint_f860
hint_f838:
; --- unverified ---
    movea.l 426(a6),a1 ; app+$1AA
    tst.b 568(a6) ; app+$238
    bne.s hint_f854
hint_f842:
; --- unverified ---
    move.l 572(a6),d1 ; app+$23C
    sub.l 26(a1),d1
    add.l d1,18(a1)
    move.l d2,26(a1)
    bra.s hint_f860
hint_f854:
; --- unverified ---
    bset #0,16(a1)
    bne.s hint_f860
hint_f85c:
    dc.b    $23,$42,$00,$16
hint_f860:
; --- unverified ---
    moveq #0,d0
    rts
hint_f864:
; --- unverified ---
    moveq #-1,d0
    rts
loc_f868:
    movea.l 426(a6),a0 ; app+$1AA
    btst #1,16(a0)
    bne.w loc_f884
loc_f876:
    add.l d1,588(a6) ; app+$24C
    bset #0,16(a0)
    beq.s loc_f88a
loc_f882:
    rts
loc_f884:
    jmp sub_845a
loc_f88a:
    moveq #8,d0
    jmp sign_extended_operand
loc_f892:
    move.b #$e,264(a6) ; app+$108
    tst.b 568(a6) ; app+$238
    bne.s loc_f8ea
loc_f89e:
    move.l a1,d2
    bsr.w sub_9b24
loc_f8a4:
    beq.s loc_f8e4
loc_f8a6:
    movem.l a0-a1,-(sp)
    moveq #34,d1
    bsr.w sub_90ba
loc_f8b0:
    movem.l (sp)+,a1-a2
    move.l a0,(a1)
    clr.l (a0)
    clr.b 16(a0)
    clr.l 22(a0)
    move.l a2,4(a0)
    clr.l 18(a0)
    clr.l 26(a0)
    movea.l d2,a2
    cmpi.l #$4425353,22(a2)
    bne.s loc_f8de
loc_f8d8:
    bset #1,16(a0)
loc_f8de:
    clr.l 8(a0)
    movea.l a0,a1
loc_f8e4:
    move.l a1,426(a6) ; app+$1AA
    rts
loc_f8ea:
    bsr.w sub_9b24
loc_f8ee:
    bne.w loc_9b64
loc_f8f2:
    move.l 12(a1),588(a6) ; app+$24C
    bne.s loc_f902
loc_f8fa:
    lea 1448(a6),a0 ; app+$5A8
    move.l a0,588(a6) ; app+$24C
loc_f902:
    move.l a1,426(a6) ; app+$1AA
    tst.l 406(a6) ; app+$196
    beq.s loc_f92a
loc_f90c:
    movem.l a1/a4,-(sp)
    movea.l 406(a6),a4 ; app+$196
    move.b (a4)+,d1
    jsr sub_16cc
loc_f91c:
    movem.l (sp)+,a1/a4
    move.l d2,30(a1)
    bset #2,16(a1)
loc_f92a:
    rts
loc_f92c:
    bsr.w sub_9b24
loc_f930:
    bne.w loc_9b64
loc_f934:
    tst.b 568(a6) ; app+$238
    bne.s loc_f94e
loc_f93a:
    move.l 572(a6),d2 ; app+$23C
    sub.l 26(a1),d2
    add.l d2,18(a1)
    move.l 572(a6),26(a1) ; app+$23C
    rts
loc_f94e:
    move.l a5,12(a1)
    rts
loc_f954:
    lea 422(a6),a3 ; app+$1A6
loc_f958:
    tst.l (a3)
    beq.s loc_f980
loc_f95c:
    movea.l (a3),a3
    move.l 18(a3),d1
    beq.s loc_f97e
loc_f964:
    btst #1,16(a3)
    bne.s loc_f97e
loc_f96c:
    addq.l #8,d1
    bsr.w sub_90ba
loc_f972:
    move.l a0,8(a3)
    move.l a0,12(a3)
    adda.l 18(a3),a0
loc_f97e:
    bra.s loc_f958
loc_f980:
    rts
loc_f982:
    movea.l 426(a6),a1 ; app+$1AA
    btst #1,16(a1)
    eori.b
    rts
loc_f992:
    bsr.w loc_97a6
loc_f996:
    bra.w loc_f9da
    dc.b    $4e,$75
sub_f99c:
; --- unverified ---
    rts
hint_f99e:
; --- unverified ---
    move.l d2,(a5)+
    rts
loc_f9a2:
    move.w d2,(a5)+
    rts
sub_f9a6:
; --- unverified ---
    move.b d2,(a5)+
    rts
loc_f9aa:
    lea str_f9b6(pc),a0
    rts
loc_f9b0:
    lea str_f9bf(pc),a0
    rts
str_f9b6:
    dc.b    "S-record",0
str_f9bf:
    dc.b    $2e,$6d,$78,$00
str_f9c3:
    dc.b    "HISOFT DEVPAC"
sub_f9d0:
    dc.b    $00,$00
hint_f9d2:
    dc.b    $12,$d8
hint_f9d6:
; --- unverified ---
    subq.l #1,a1
    rts
loc_f9da:
    bsr.w sub_a110
loc_f9de:
    lea 430(a6),a2 ; app+$1AE
    tst.b (a2)
    bne.s loc_f9ea
loc_f9e6:
    lea str_f9c3(pc),a2
loc_f9ea:
    moveq #0,d6
    moveq #0,d5
    movea.l a2,a0
loc_f9f0:
    tst.b (a0)+
    bne.s loc_f9f0
loc_f9f4:
    move.l a0,d2
    sub.l a2,d2
    subq.l #1,d2
    bsr.w sub_fa74
loc_f9fe:
    lea 422(a6),a3 ; app+$1A6
loc_fa02:
    movea.l (a3),a3
    move.l 18(a3),d3
    beq.s loc_fa6c
loc_fa0a:
    btst #1,16(a3)
    bne.s loc_fa6c
loc_fa12:
    move.l 22(a3),d2
    btst #2,16(a3)
    beq.s loc_fa22
loc_fa1e:
    move.l 30(a3),d2
loc_fa22:
    add.l d3,d2
    moveq #3,d5
    cmp.l #$1000000,d2
    bcc.s loc_fa3a
loc_fa2e:
    moveq #2,d5
    cmp.l #$10000,d2
    bcc.s loc_fa3a
loc_fa38:
    moveq #1,d5
loc_fa3a:
    movea.l 8(a3),a2
    move.l 22(a3),d6
    btst #2,16(a3)
    beq.s loc_fa4e
loc_fa4a:
    move.l 30(a3),d6
loc_fa4e:
    moveq #28,d2
    cmp.l d2,d3
    bge.s loc_fa56
loc_fa54:
    move.l d3,d2
loc_fa56:
    sub.l d2,d3
    bsr.s sub_fa74
loc_fa5a:
    tst.l d3
    bne.s loc_fa4e
loc_fa5e:
    moveq #10,d0
    sub.w d5,d0
    move.w d0,d5
    move.l 22(a3),d6
    moveq #0,d2
    bsr.s sub_fa74
loc_fa6c:
    tst.l (a3)
    bne.s loc_fa02
loc_fa70:
    bra.w sub_a0f6
sub_fa74:
    cmp.w #$49,d4
    bcc.s loc_fa7e
loc_fa7a:
    bsr.w sub_a0f6
loc_fa7e:
    moveq #48,d1
    add.b d5,d1
    movea.l a4,a0
    move.b #$53,(a4)+
    move.b d1,(a4)+
    addq.w #2,a4
    moveq #0,d7
    move.w d5,d1
    add.w d1,d1
    lea pcref_faf2(pc,d1.w),a1
    move.b (a1)+,d1
    move.l d6,d0
    lsl.l d1,d0
    move.l d0,-(sp)
    move.b (a1)+,d0
    movea.l sp,a1
loc_faa2:
    move.b (a1)+,d1
    bsr.s sub_fade
loc_faa6:
    subq.b #1,d0
    bne.s loc_faa2
loc_faaa:
    addq.l #4,sp
    add.l d2,d6
    tst.l d2
    bra.s loc_fab8
loc_fab2:
    move.b (a2)+,d1
    bsr.s sub_fade
loc_fab6:
    subq.l #1,d2
loc_fab8:
    bne.s loc_fab2
loc_faba:
    move.l a4,-(sp)
    move.l a4,d1
    sub.l a0,d1
    addq.l #2,d1
    sub.l d1,d4
    lsr.w #1,d1
    subq.w #2,d1
    lea 2(a0),a4
    bsr.s sub_fade
loc_face:
    movea.l (sp)+,a4
    not.b d7
    move.b d7,d1
    bsr.s sub_fade
loc_fad6:
    move.b #$a,(a4)+
    subq.l #1,d4
    rts
sub_fade:
    add.b d1,d7
    move.w d1,-(sp)
    lsr.w #4,d1
    bsr.s sub_fae8
loc_fae6:
    move.w (sp)+,d1
sub_fae8:
    andi.w #$f,d1
    move.b str_fb06(pc,d1.w),(a4)+
    rts
pcref_faf2:
    dc.b    $00,$02,$10,$02,$08,$03,$00,$04,$00,$01,$00,$01,$00,$01,$00,$04
    dc.b    $08,$03,$10,$02
str_fb06:
    dc.b    "0123456789ABCDEF"
sub_fb16:
    bsr.w loc_97a6
loc_fb1a:
    movea.l 362(a6),a1 ; app+$16A
    movea.l (a1),a1
    move.l #$84034,d2
    lea loc_fc7c(pc),a2
    bsr.w sub_fc5e
loc_fb2e:
    move.l d1,-(sp)
    lea loc_fc7c(pc),a2
    movea.l 370(a6),a1 ; app+$172
    movea.l (a1),a1
    move.l #$3900,d2
    bsr.w sub_fc5e
loc_fb44:
    add.l (sp)+,d1
    addi.l #$a,d1
    jsr sub_90ba
loc_fb52:
    movea.l a0,a2
    move.w #$0,(a2)
    lea 10(a0),a0
    move.l #$a,2(a2)
    lea 2(a2),a3
    movea.l 362(a6),a1 ; app+$16A
    movea.l (a1),a1
    move.l #$84034,d2
    bsr.w loc_fba0
loc_fb78:
    clr.l (a3)
    lea 6(a2),a3
    movea.l 370(a6),a1 ; app+$172
    movea.l (a1),a1
    move.l #$3900,d2
    bsr.w loc_fba0
loc_fb8e:
    move.l a0,d1
    sub.l a2,d1
    movea.l a2,a0
    jsr sub_8422
loc_fb9a:
    bra.w sub_98ae
sub_fb9e:
    rts
loc_fba0:
    move.l a1,d1
    beq.s sub_fb9e
loc_fba4:
    move.b 13(a1),d0
    move.l a1,-(sp)
    btst d0,d2
    beq.s loc_fbf6
loc_fbae:
    move.l a0,d1
    sub.l a2,d1
    move.l d1,(a3)
    move.l a0,d1
    moveq #0,d0
    move.b 22(a1),d0
    addq.l #8,a1
    movea.l a0,a3
    clr.l (a0)+
    clr.l (a0)+
    addi.l #$e,d0
    bset #0,d0
loc_fbce:
    move.b (a1)+,(a0)+
    dbf d0,loc_fbce
loc_fbd4:
    movea.l d1,a1
    move.b 13(a1),d0
    cmp.b #$8,d0
    beq.s loc_fc04
loc_fbe0:
    cmp.b #$b,d0
    bcs.s loc_fbf6
loc_fbe6:
    cmp.b #$e,d0
    bcc.s loc_fbf6
loc_fbec:
    move.b #$d,13(a1)
    clr.l 152(a1)
loc_fbf6:
    movea.l (sp),a1
    movea.l (a1),a1
    bsr.s loc_fba0
loc_fbfc:
    movea.l (sp)+,a1
    movea.l 4(a1),a1
    bra.s loc_fba0
loc_fc04:
    move.l a0,d0
    sub.l a2,d0
    movea.l 8(a1),a0
    move.l d0,8(a1)
    add.l a2,d0
    movea.l a0,a1
    movea.l d0,a0
    pea 4(a0)
    move.l a0,d0
    addi.l #$10,d0
    sub.l a2,d0
    move.l d0,(a0)
    clr.l 8(a0)
    lea 16(a0),a0
loc_fc2e:
    move.l 4(a1),d0
    sub.l (a1),d0
    move.l 8(a1),-(sp)
    movea.l (a1),a1
    subq.w #1,d0
    bmi.s loc_fc44
loc_fc3e:
    move.b (a1)+,(a0)+
    dbf d0,loc_fc3e
loc_fc44:
    move.l (sp)+,d0
    beq.s loc_fc4c
loc_fc48:
    movea.l d0,a1
    bra.s loc_fc2e
loc_fc4c:
    move.l a0,d0
    sub.l a2,d0
    movea.l (sp)+,a1
    move.l d0,(a1)
    btst #0,d0
    beq.s loc_fc5c
loc_fc5a:
    addq.w #1,a0
loc_fc5c:
    bra.s loc_fbf6
sub_fc5e:
    moveq #0,d1
    move.l a1,d0
    beq.s loc_fc7a
loc_fc64:
    move.l a1,-(sp)
    movea.l (a1),a1
    bsr.s sub_fc5e
loc_fc6a:
    movea.l (sp),a1
    move.l d1,-(sp)
    movea.l 4(a1),a1
    bsr.s sub_fc5e
loc_fc74:
    add.l (sp)+,d1
    movea.l (sp)+,a1
    jsr (a2)
loc_fc7a:
    rts
loc_fc7c:
    move.b 13(a1),d0
    btst d0,d2
    beq.s loc_fcd4
loc_fc84:
    cmp.b #$8,d0
    beq.s loc_fc9e
loc_fc8a:
    cmp.b #$b,d0
    bcs.s loc_fcc2
loc_fc90:
    cmp.b #$e,d0
    bcc.s loc_fcc2
loc_fc96:
    addi.l #$b2,d1
    rts
loc_fc9e:
    move.l a1,-(sp)
    addi.l #$10,d1
    movea.l 8(a1),a1
loc_fcaa:
    add.l 4(a1),d1
    sub.l (a1),d1
    move.l 8(a1),d0
    beq.s loc_fcba
loc_fcb6:
    movea.l d0,a1
    bra.s loc_fcaa
loc_fcba:
    addq.l #1,d1
    bclr #0,d1
    movea.l (sp)+,a1
loc_fcc2:
    moveq #0,d0
    move.b 22(a1),d0
    addi.l #$18,d0
    bclr #0,d0
    add.l d0,d1
loc_fcd4:
    rts
sub_fcd6:
    move.l d4,d3
    bra.s loc_fd10
sub_fcda:
    movea.l app_timer_device_iorequest+IO_DATA(a6),a0
loc_fcde:
    tst.b (a0)
    beq.s loc_fd02
loc_fce2:
    lea 4328(a6),a1 ; app+$10E8
loc_fce6:
    move.b (a0)+,(a1)+
    bne.s loc_fce6
loc_fcea:
    move.l a0,-(sp)
    lea 4328(a6),a0 ; app+$10E8
    lea str_9656(pc),a2
    jsr sub_45dc
loc_fcfa:
    bsr.w sub_fd04
loc_fcfe:
    movea.l (sp)+,a0
    bra.s loc_fcde
loc_fd02:
    rts
sub_fd04:
    jsr sub_afde
loc_fd0a:
    bne.w loc_fd8c
loc_fd0e:
    move.l d2,d1
loc_fd10:
    move.l d1,-(sp)
    jsr sub_90ba
loc_fd18:
    move.l (sp),d1
    move.l a0,(sp)
    move.l d3,-(sp)
    bsr.w call_read_aff6
loc_fd22:
    move.l (sp)+,d3
    bsr.w sub_aff2
loc_fd28:
    movea.l (sp)+,a2
    move.l a2,d2
    move.w (a2),d0
    cmp.w #$0,d0
    bne.s loc_fd94
loc_fd34:
    movem.l a3-a5,-(sp)
    movea.l 2(a2),a0
    movea.l 362(a6),a2 ; app+$16A
    bsr.s loc_fd5c
loc_fd42:
    movea.l d2,a0
    movea.l 6(a0),a0
    movea.l 370(a6),a2 ; app+$172
    bsr.s loc_fd5c
loc_fd4e:
    movem.l (sp)+,a3-a5
loc_fd52:
    rts
sub_fd54:
    move.l (a0),d0
    beq.s loc_fd52
loc_fd58:
    clr.l (a0)
    movea.l d0,a0
loc_fd5c:
    adda.l d2,a0
    move.l d2,-(sp)
    jsr sub_0b78
loc_fd66:
    movem.l (sp)+,d2
    beq.s sub_fd54
loc_fd6c:
    move.l a0,(a1)
    move.b 13(a0),d1
    cmp.b #$8,d1
    bne.s sub_fd54
loc_fd78:
    add.l d2,8(a0)
    movea.l 8(a0),a1
    add.l d2,4(a1)
    add.l d2,(a1)
    bra.s sub_fd54
    dc.b    $70,$05,$60,$02
loc_fd8c:
    moveq #27,d0
loc_fd8e:
    jmp loc_846e
loc_fd94:
    moveq #103,d0
    bra.s loc_fd8e
