    INCLUDE "exec/exec_lib.i"
    INCLUDE "dos/dos_lib.i"

app_SegList EQU 42
app_ExecBase EQU 34
app_DOSBase EQU 38

    SECTION section,code
h0_0000:
    moveq.l #-1,d0
    rts
resident:
    DC.W    $4afc ; NOTE: resident matchword
    DC.L    resident ; NOTE: resident matchtag
    DC.L    dat_0280 ; NOTE: resident endskip
    DC.B    $80 ; NOTE: resident flags
    DC.B    $22 ; NOTE: resident version
    DC.B    $09 ; NOTE: resident type
    DC.B    $46 ; NOTE: resident priority
    DC.L    dat_001E ; NOTE: resident name
    DC.L    dat_002B ; NOTE: resident id string
    DC.L    resident_autoinit ; NOTE: resident init
dat_001E:
    DC.B    $69,$63,$6f,$6e,$2e,$6c,$69,$62,$72,$61,$72,$79,$00
dat_002B:
    DC.B    "icon 34.2 (22 Jun 1988)"
    DC.B    $0d,$0a
    DC.L    $00000000
resident_autoinit:
    DC.L    $0000002e ; NOTE: resident base size
    DC.L    resident_vectors ; NOTE: resident vectors
    DC.L    resident_init_struct ; NOTE: resident init struct
    DC.L    resident_init ; NOTE: resident init function
resident_vectors:
    DC.L    lib_open
    DC.L    lib_close
    DC.L    lib_expunge
    DC.L    lib_extfunc
    DC.L    icon_private1
    DC.L    icon_private2
    DC.L    icon_private3
    DC.L    icon_private4
    DC.L    free_free_list
    DC.L    icon_private5
    DC.L    icon_private6
    DC.L    add_free_list
    DC.L    get_disk_object
    DC.L    icon_private4
    DC.L    free_disk_object
    DC.L    find_tool_type
    DC.L    match_tool_value
    DC.L    bump_revision
    DC.L    $ffffffff
resident_init_struct:
    DC.L    $e0000008,$0900c000
    DC.B    $00,$0a
    DC.L    dat_001E
    DC.B    $e0,$00
    DC.L    $000e0600,$d0000014,$0022d000,$00160002,$c0000018
    DC.L    dat_002B
    DC.L    $00000000
dat_00D0:
    DC.B    $64,$6f,$73,$2e,$6c,$69,$62,$72,$61,$72,$79,$00
    ; KNOWN: base A6=icon.library:LIB
lib_open:
    addq.w #1,$0020(a6)
    bclr.b #3,$000E(a6)
    move.l a6,d0
    rts
    ; KNOWN: base A6=icon.library:LIB
lib_close:
    moveq.l #0,d0
    subq.w #1,$0020(a6)
    bne.s h0_00FE
h0_00F2:
    btst.b #3,$000E(a6)
    beq.s h0_00FE
h0_00FA:
    bsr.w lib_expunge
h0_00FE:
    rts
    ; KNOWN: base A6=icon.library:LIB
lib_expunge:
    tst.w $0020(a6)
    bne.s h0_013A
h0_0106:
    move.l app_SegList(a6),-(a7)
    movea.l a6,a1
    movea.l (a1),a0
    movea.l $0004(a1),a1
    move.l a0,(a1)
    move.l a1,$0004(a0)
    movea.l a6,a1
    moveq.l #0,d0
    moveq.l #0,d1
    move.w $0010(a6),d0
    suba.l d0,a1
h0_0124:
    move.w $0012(a6),d1
    add.l d1,d0
    move.l a6,-(a7)
    movea.l app_ExecBase(a6),a6
    jsr _LVOFreeMem(a6)
h0_0134:
    movea.l (a7)+,a6
    move.l (a7)+,d0
    bra.s h0_0142
h0_013A:
    bset.b #3,$000E(a6)
    moveq.l #0,d0
h0_0142:
    rts
    ; KNOWN: base A6=icon.library:LIB
lib_extfunc:
    moveq.l #0,d0
    rts
    ; KNOWN: base A6=exec.library:LIB; base D0=__amiga_app_base__; type A0=seglist:BPTR
resident_init:
    move.l a2,-(a7)
    movea.l d0,a2
    move.l a0,app_SegList(a2)
    move.l a6,app_ExecBase(a2)
    lea.l dat_00D0(pc),a1
    jsr _LVOOldOpenLibrary(a6)
h0_015C:
    move.l d0,app_DOSBase(a2)
    bne.s h0_017C
h0_0162:
    movem.l d7/a5-a6,-(a7)
    move.l #$9038007,d7
    movea.l $0004.w,a6
    jsr _LVOAlert(a6)
h0_0174:
    movem.l (a7)+,d7/a5-a6
    moveq.l #0,d0
    bra.s h0_018E
h0_017C:
    move.l app_ExecBase(a2),h0dl_ExecBase.l
    move.l app_DOSBase(a2),h0dl_DOSBase.l
    move.l a2,d0
h0_018E:
    movea.l (a7)+,a2
    rts
h0dl_ExecBase:
    DC.L    $00000000
h0dl_DOSBase:
    DC.L    $00000000
    ; DECL: void iconPrivate1() | KNOWN: base A6=icon.library:LIB
icon_private1:
    move.l a0,-(a7)
    move.l a6,-(a7)
    jsr h3_0000.l
h0_01A4:
    addq.l #8,a7
    rts
    ; DECL: void iconPrivate2() | KNOWN: base A6=icon.library:LIB
icon_private2:
    movem.l a0-a1,-(a7)
    move.l a6,-(a7)
    jsr h3_00A8.l
h0_01B4:
    lea.l $000C(a7),a7
    rts
    ; DECL: void iconPrivate3() | KNOWN: base A6=icon.library:LIB
icon_private3:
    movem.l a0-a2,-(a7)
    move.l a6,-(a7)
    jsr h3_0124.l
h0_01C6:
    lea.l $0010(a7),a7
    rts
    ; DECL: void iconPrivate4() | DECL: BOOL PutDiskObject(UBYTE *name, struct DiskObject *diskobj) | KNOWN: base A6=icon.library:LIB; type A0=name:UBYTE *; type A1=diskobj:struct DiskObject *
icon_private4:
    movem.l a0-a1,-(a7)
    move.l a6,-(a7)
    jsr h3_03FE.l
h0_01D8:
    lea.l $000C(a7),a7
    rts
    ; DECL: void FreeFreeList(struct FreeList *freelist) | KNOWN: base A6=icon.library:LIB; type A0=freelist:struct FreeList *
free_free_list:
    move.l a0,-(a7)
    move.l a6,-(a7)
    jsr h3_0656.l
h0_01E8:
    addq.l #8,a7
    rts
    ; DECL: void iconPrivate5() | KNOWN: base A6=icon.library:LIB
icon_private5:
    move.l a0,-(a7)
    move.l a6,-(a7)
    jsr h3_0692.l
h0_01F6:
    addq.l #8,a7
    rts
    ; DECL: void iconPrivate6() | KNOWN: base A6=icon.library:LIB
icon_private6:
    move.l a6,-(a7)
    jsr h3_06A8.l
h0_0202:
    addq.l #4,a7
    rts
    ; DECL: BOOL AddFreeList(struct FreeList *free, APTR mem, ULONG len) | KNOWN: base A6=icon.library:LIB; type A0=free:struct FreeList *; type A1=mem:APTR; type A2=len:ULONG
add_free_list:
    movem.l a0-a2,-(a7)
    move.l a6,-(a7)
    jsr h3_071C.l
h0_0212:
    lea.l $0010(a7),a7
    rts
    ; DECL: struct DiskObject *GetDiskObject(UBYTE *name) | KNOWN: base A6=icon.library:LIB; type A0=name:UBYTE *
get_disk_object:
    move.l a0,-(a7)
    move.l a6,-(a7)
    jsr h3_0768.l
h0_0222:
    addq.l #8,a7
    rts
    ; DECL: void FreeDiskObject(struct DiskObject *diskobj) | KNOWN: base A6=icon.library:LIB; type A0=diskobj:struct DiskObject *
free_disk_object:
    move.l a0,-(a7)
    move.l a6,-(a7)
    jsr h3_07FC.l
h0_0230:
    addq.l #8,a7
    rts
    ; DECL: char *FindToolType(UBYTE **toolTypeArray, UBYTE *typeName) | KNOWN: base A6=icon.library:LIB; type A0=toolTypeArray:UBYTE **; type A1=typeName:UBYTE *
find_tool_type:
    movem.l a0-a1,-(a7)
    jsr h3_0818.l
h0_023E:
    addq.l #8,a7
    rts
    ; DECL: BOOL MatchToolValue(UBYTE *typeString, UBYTE *value) | KNOWN: base A6=icon.library:LIB; type A0=typeString:UBYTE *; type A1=value:UBYTE *
match_tool_value:
    movem.l a0-a1,-(a7)
    jsr h3_0864.l
h0_024C:
    addq.l #8,a7
    rts
    ; DECL: char *BumpRevision(char *newbuf, UBYTE *oldname) | KNOWN: base A6=icon.library:LIB; type A0=newbuf:char *; type A1=oldname:UBYTE *
bump_revision:
    movem.l a0-a1,-(a7)
    jsr h3_08D6.l
h0_025A:
    addq.l #8,a7
    rts
    DC.B    $00,$00
h0_0260:
    move.l a6,-(a7)
    movea.l $0008(a7),a6
    suba.l a1,a1
    move.l a6,-(a7)
    movea.l app_ExecBase(a6),a6
    jsr _LVOFindTask(a6)
h0_0272:
    movea.l (a7)+,a6
    movea.l d0,a1
    move.l $000C(a7),$0094(a1)
    movea.l (a7)+,a6
    rts
dat_0280:
    DC.L    $00000000
    SECTION section,code
h1_0000:
    movem.l d2-d5,-(a7)
    move.l $0014(a7),d3
    move.l $0018(a7),d4
    move.l $001C(a7),d2
    move.l $0020(a7),-(a7)
    move.l d2,-(a7)
    jsr h9_0000.l
h1_001C:
    move.l d0,d5
    addq.l #8,a7
    beq.s h1_0046
h1_0022:
    move.l d2,-(a7)
    move.l d5,-(a7)
    move.l d4,-(a7)
    move.l d3,-(a7)
    jsr h3_071C.l
h1_0030:
    tst.l d0
    lea.l $0010(a7),a7
    bne.s h1_0046
h1_0038:
    move.l d2,-(a7)
    move.l d5,-(a7)
    jsr h9_0018.l
h1_0042:
    moveq.l #0,d5
h1_0044:
    addq.l #8,a7
h1_0046:
    move.l d5,d0
    movem.l (a7)+,d2-d5
h1_004C:
    rts
h1_004E:
    movem.l d2/a2,-(a7)
    movea.l $0010(a7),a2
    move.l #$10000,-(a7)
    pea.l $0060.w
h1_0060:
    jsr h9_0000.l
h1_0066:
    movea.l d0,a0
    move.l a0,d2
    addq.l #8,a7
    beq.s h1_008A
h1_006E:
    move.w #$A,$000E(a0)
    move.w #$A,(a2)
    move.l a0,-(a7)
    pea.l $0002(a2)
    jsr h9_0044.l
h1_0084:
    moveq.l #1,d0
    addq.l #8,a7
    bra.s h1_008C
h1_008A:
    moveq.l #0,d0
h1_008C:
    movem.l (a7)+,d2/a2
    rts
h1_0092:
    move.l $0008(a7),d0
    move.l $000C(a7),d1
    move.l $0010(a7),-(a7)
    move.l d1,-(a7)
    move.l d0,-(a7)
    jsr h8_0030.l
h1_00A8:
    move.l d0,d1
    cmp.l $001C(a7),d0
    lea.l $000C(a7),a7
    beq.s h1_00B8
h1_00B4:
    moveq.l #0,d0
    bra.s h1_00BA
h1_00B8:
    move.l d1,d0
h1_00BA:
    rts
h1_00BC:
    move.l $0008(a7),d0
    move.l $000C(a7),d1
    move.l $0010(a7),-(a7)
    move.l d1,-(a7)
    move.l d0,-(a7)
    jsr h8_004C.l
h1_00D2:
    move.l d0,d1
    cmp.l $001C(a7),d0
    lea.l $000C(a7),a7
    beq.s h1_00E2
h1_00DE:
    moveq.l #0,d0
    bra.s h1_00E4
h1_00E2:
    move.l d1,d0
h1_00E4:
    rts
    DC.B    $00,$00
    SECTION section,code
h2_0000:
    movem.l d2-d3/a2,-(a7)
    move.l $0010(a7),d2
    move.l $0014(a7),d3
    movea.l $0018(a7),a2
h2_0010:
    moveq.l #1,d0
    move.l a2,d1
h2_0014:
    beq.s h2_0074
h2_0016:
    pea.l $0014.w
    move.l a2,-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_00BC.l
h2_0026:
    move.l d0,d0
    lea.l $0010(a7),a7
    beq.s h2_0074
h2_002E:
    move.w $0004(a2),d1
    ext.l d1
    moveq.l #15,d0
    add.l d0,d1
    asr.l #3,d1
    andi.l #65534,d1
h2_0040:
    move.w $0006(a2),d0
    ext.l d0
    jsr h6_0040.l
h2_004C:
    move.l d0,d1
    move.w $0008(a2),d0
    ext.l d0
    jsr h6_0040.l
h2_005A:
    move.l d0,-(a7)
    move.l $000A(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_00BC.l
h2_006A:
    move.l d0,d0
    lea.l $0010(a7),a7
    beq.w h2_0074
h2_0074:
    movem.l (a7)+,d2-d3/a2
    rts
h2_007A:
    movem.l d2-d3/a2,-(a7)
    move.l $0010(a7),d2
    move.l $0014(a7),d3
    movea.l $0018(a7),a2
    bra.s h2_00CC
h2_008C:
    pea.l $0010.w
    move.l a2,-(a7)
h2_0092:
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_00BC.l
h2_009C:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h2_00D4
h2_00A4:
    move.b $0007(a2),d0
    ext.w d0
    ext.l d0
    add.l d0,d0
    add.l d0,d0
    move.l d0,-(a7)
    move.l $0008(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_00BC.l
h2_00C0:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h2_00D4
h2_00C8:
    movea.l $000C(a2),a2
h2_00CC:
    move.l a2,d0
    bne.s h2_008C
h2_00D0:
    moveq.l #1,d0
    bra.s h2_00D6
h2_00D4:
    moveq.l #0,d0
h2_00D6:
    movem.l (a7)+,d2-d3/a2
    rts
h2_00DC:
    movem.l d2-d5/a2,-(a7)
    move.l $0018(a7),d2
    move.l $001C(a7),d3
    move.l $0020(a7),d4
    tst.l $0024(a7)
    beq.w h2_019E
h2_00F4:
    move.l #$10000,-(a7)
    pea.l $0014.w
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h2_0108:
    move.l d0,$0034(a7)
    lea.l $0010(a7),a7
    beq.w h2_01A4
h2_0114:
    pea.l $0014.w
    move.l $0028(a7),-(a7)
    move.l d4,-(a7)
    move.l d2,-(a7)
    jsr h1_0092.l
h2_0126:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h2_01A4
h2_0130:
    movea.l $0024(a7),a0
    move.w $0004(a0),d5
    ext.l d5
    moveq.l #15,d0
    add.l d0,d5
    asr.l #3,d5
    andi.l #65534,d5
    move.l d5,d1
    move.w $0006(a0),d0
    ext.l d0
    jsr h6_0040.l
h2_0154:
    move.l d0,d5
    movea.l $0024(a7),a2
    move.l d5,d1
    move.w $0008(a2),d0
    ext.l d0
    jsr h6_0040.l
h2_0168:
    move.l d0,d5
    movea.l $0024(a7),a2
    pea.l $0002.w
    move.l d5,-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h2_017E:
    move.l d0,$000A(a2)
    move.l d5,-(a7)
    movea.l $0038(a7),a2
    move.l $000A(a2),-(a7)
    move.l d4,-(a7)
    move.l d2,-(a7)
    jsr h1_0092.l
h2_0196:
    tst.l d0
    lea.l $0020(a7),a7
    beq.s h2_01A4
h2_019E:
    move.l $0024(a7),d0
    bra.s h2_01A6
h2_01A4:
    moveq.l #-1,d0
h2_01A6:
    movem.l (a7)+,d2-d5/a2
    rts
h2_01AC:
    movem.l d2-d6/a2,-(a7)
    move.l $001C(a7),d2
    move.l $0020(a7),d3
    move.l $0024(a7),d4
    moveq.l #0,d6
    bra.w h2_026C
h2_01C2:
    move.l #$10000,-(a7)
    pea.l $0010.w
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h2_01D6:
    move.l d0,$0038(a7)
    lea.l $0010(a7),a7
    beq.w h2_0278
h2_01E2:
    tst.l d6
    bne.s h2_01EC
h2_01E6:
    move.l $0028(a7),d6
    bra.s h2_01F2
h2_01EC:
    move.l $0028(a7),$000C(a2)
h2_01F2:
    pea.l $0010.w
    move.l $002C(a7),-(a7)
    move.l d4,-(a7)
    move.l d2,-(a7)
    jsr h1_0092.l
h2_0204:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h2_0278
h2_020C:
    movea.l $0028(a7),a0
    move.b $0007(a0),d5
    ext.w d5
    ext.l d5
    add.l d5,d5
    add.l d5,d5
    movea.l $0028(a7),a2
    pea.l $0002.w
    move.l d5,-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h2_0230:
    move.l d0,$0008(a2)
    movea.l $0038(a7),a0
    tst.l $0008(a0)
    lea.l $0010(a7),a7
    beq.s h2_0278
h2_0242:
    move.l d5,-(a7)
    movea.l $002C(a7),a2
    move.l $0008(a2),-(a7)
    move.l d4,-(a7)
    move.l d2,-(a7)
    jsr h1_0092.l
h2_0256:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h2_0278
h2_025E:
    movea.l $0028(a7),a2
    movea.l $0028(a7),a0
    move.l $000C(a0),$0028(a7)
h2_026C:
    tst.l $0028(a7)
    bne.w h2_01C2
h2_0274:
    move.l d6,d0
    bra.s h2_027A
h2_0278:
    moveq.l #-1,d0
h2_027A:
    movem.l (a7)+,d2-d6/a2
    rts
    SECTION section,code
h3_0000:
    link a6,#-80
h3_0004:
    movem.l d2-d4/a2,-(a7)
    move.l $0008(a6),d2
h3_000C:
    move.l $000C(a6),d3
h3_0010:
    move.l d2,-(a7)
h3_0012:
    jsr h3_06A8.l
h3_0018:
    movea.l d0,a2
    move.l a2,d4
h3_001C:
    addq.l #4,a7
    beq.w h3_009C
h3_0022:
    pea.l $008C(a2)
h3_0026:
    pea.l -$0050(a6)
    move.l d3,-(a7)
h3_002C:
    move.l d2,-(a7)
    jsr h3_0124.l
h3_0034:
    tst.l d0
    lea.l $0010(a7),a7
    bne.s h3_004A
h3_003C:
    move.l a2,-(a7)
    move.l d2,-(a7)
    jsr h3_0692.l
h3_0046:
    addq.l #8,a7
h3_0048:
    bra.s h3_009C
h3_004A:
    lea.l -$004C(a6),a0
h3_004E:
    lea.l $0060(a2),a1
    moveq.l #10,d0
h3_0054:
    move.l (a0)+,(a1)+
    dbf.w d0,h3_0054
h3_005A:
    move.b -$0020(a6),$003D(a2)
    move.l -$001E(a6),$0048(a2)
    move.l -$001A(a6),$005C(a2)
h3_006C:
    move.l -$0016(a6),$0054(a2)
    move.l -$0012(a6),$0058(a2)
    move.l -$000E(a6),$004C(a2)
    move.l -$000A(a6),$009C(a2)
    move.l -$0006(a6),$00A0(a2)
    tst.l $004C(a2)
    beq.s h3_0098
h3_0090:
    movea.l $004C(a2),a0
    move.l a2,$01A8(a0)
h3_0098:
    move.l a2,d0
    bra.s h3_009E
h3_009C:
    moveq.l #0,d0
h3_009E:
    movem.l -$0060(a6),d2-d4/a2
    unlk a6
    rts
h3_00A8:
    link a6,#-80
    movem.l d2/a2,-(a7)
    move.l $0008(a6),d1
    move.l $000C(a6),d2
    movea.l $0010(a6),a0
    move.w #$E310,-$0050(a6)
    move.w #$1,-$004E(a6)
h3_00C8:
    lea.l $0060(a0),a1
    lea.l -$004C(a6),a2
    moveq.l #10,d0
h3_00D2:
    move.l (a1)+,(a2)+
    dbf.w d0,h3_00D2
h3_00D8:
    move.l $005C(a0),-$001A(a6)
    move.b $003D(a0),-$0020(a6)
    move.l $0054(a0),-$0016(a6)
    move.l $0058(a0),-$0012(a6)
    move.l $004C(a0),-$000E(a6)
    move.l $0048(a0),-$001E(a6)
    move.l $009C(a0),-$000A(a6)
    move.l $00A0(a0),-$0006(a6)
    pea.l -$0050(a6)
    move.l d2,-(a7)
    move.l d1,-(a7)
    jsr h3_03FE.l
h3_0116:
    lea.l $000C(a7),a7
    movem.l -$0058(a6),d2/a2
    unlk a6
    rts
h3_0124:
    link a6,#-268
    movem.l d2-d5/a2-a5,-(a7)
    move.l $0008(a6),d2
    move.l $000C(a6),d0
    movea.l $0010(a6),a2
    movea.l #h1_0092,a3
    move.l #h1_0000,d3
    lea.l $0004(a2),a4
    move.l d0,-(a7)
    pea.l -$010C(a6)
    jsr h5_002C.l
h3_0154:
    pea.l h4_0000.l
    pea.l -$010C(a6)
    jsr h5_0038.l
h3_0164:
    pea.l $03ED.w
    pea.l -$010C(a6)
    jsr h8_0000.l
h3_0172:
    move.l d0,d5
    lea.l $0018(a7),a7
    bne.s h3_0180
h3_017A:
    moveq.l #0,d4
    bra.w h3_03F2
h3_0180:
    pea.l $004E.w
    move.l a2,-(a7)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_018C:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_0196:
    cmpi.w #58128,(a2)
    bne.w h3_03EE
h3_019E:
    cmpi.w #1,$0002(a2)
    bne.w h3_03EE
h3_01A8:
    clr.l (a4)
    clr.l (a4)
h3_01AC:
    tst.l $0042(a2)
    beq.s h3_01FC
h3_01B2:
    move.l #$10002,-(a7)
    pea.l $01BE.w
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h3_01C8:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_01D2:
    pea.l $0038.w
    movea.l d4,a5
    pea.l (a5)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_01E0:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_01EA:
    move.l d4,$0042(a2)
    movea.l d4,a5
    pea.l $01AC(a5)
    jsr h7_0000.l
h3_01FA:
    addq.l #4,a7
h3_01FC:
    btst.b #2,$000D(a4)
    beq.s h3_024A
h3_0204:
    move.l $0012(a4),-(a7)
    move.l d5,-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h2_00DC.l
h3_0216:
    move.l d0,d4
    moveq.l #-1,d0
    cmp.l d4,d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_0224:
    move.l d4,$0012(a4)
    move.l $0016(a4),-(a7)
    move.l d5,-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h2_00DC.l
h3_023A:
    move.l d0,d4
    moveq.l #-1,d0
    cmp.l d4,d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
    bra.s h3_028E
h3_024A:
    move.l $0012(a4),-(a7)
    move.l d5,-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h2_01AC.l
h3_025C:
    move.l d0,d4
    moveq.l #-1,d0
h3_0260:
    cmp.l d4,d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_026A:
    move.l d4,$0012(a4)
    move.l $0016(a4),-(a7)
    move.l d5,-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h2_01AC.l
h3_0280:
    move.l d0,d4
    moveq.l #-1,d0
    cmp.l d4,d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_028E:
    move.l d4,$0016(a4)
    tst.l $001A(a4)
    bne.w h3_029A
h3_029A:
    tst.l $0032(a2)
    beq.s h3_02F2
h3_02A0:
    pea.l $0004.w
    pea.l -$0008(a6)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_02AE:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_02B8:
    move.l #$10000,-(a7)
    move.l -$0008(a6),-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h3_02CE:
    move.l d0,$0032(a2)
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_02DA:
    move.l -$0008(a6),-(a7)
    move.l $0032(a2),-(a7)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_02E8:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_02F2:
    tst.l $0036(a2)
    beq.w h3_0392
h3_02FA:
    pea.l $0004.w
    pea.l -$0004(a6)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_0308:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_0312:
    move.l #$10000,-(a7)
    move.l -$0004(a6),-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h3_0328:
    movea.l d0,a4
    move.l a4,d4
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_0334:
    move.l a4,$0036(a2)
    bra.s h3_038A
h3_033A:
    pea.l $0004.w
    pea.l -$0008(a6)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_0348:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_0352:
    clr.l -(a7)
    move.l -$0008(a6),-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h3_0364:
    move.l d0,(a4)
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_036E:
    move.l -$0008(a6),-(a7)
    move.l (a4),-(a7)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_037A:
    tst.l d0
    lea.l $0010(a7),a7
    beq.w h3_03EE
h3_0384:
    subq.l #4,-$0004(a6)
    addq.l #4,a4
h3_038A:
    moveq.l #4,d0
    cmp.l -$0004(a6),d0
    blt.s h3_033A
h3_0392:
    tst.l $0046(a2)
    beq.s h3_03E0
h3_0398:
    pea.l $0004.w
    pea.l -$0008(a6)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_03A6:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h3_03EE
h3_03AE:
    clr.l -(a7)
    move.l -$0008(a6),-(a7)
    move.l $0014(a6),-(a7)
    move.l d2,-(a7)
    jsr h1_0000.l
h3_03C0:
    move.l d0,$0046(a2)
    lea.l $0010(a7),a7
    beq.s h3_03EE
h3_03CA:
    move.l -$0008(a6),-(a7)
    move.l $0046(a2),-(a7)
    move.l d5,-(a7)
    move.l d2,-(a7)
    jsr (a3) ; CANDIDATE: indirect_call index unresolved
h3_03D8:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h3_03EE
h3_03E0:
    moveq.l #1,d4
h3_03E2:
    move.l d5,-(a7)
    jsr h8_001C.l
h3_03EA:
    addq.l #4,a7
    bra.s h3_03F2
h3_03EE:
    moveq.l #0,d4
    bra.s h3_03E2
h3_03F2:
    move.l d4,d0
    movem.l -$012C(a6),d2-d5/a2-a5
    unlk a6
    rts
h3_03FE:
    link a6,#-4
    movem.l d2-d6/a2-a4,-(a7)
    move.l $0008(a6),d2
    move.l $000C(a6),d3
    movea.l $0010(a6),a2
    moveq.l #0,d4
    movea.l #h1_00BC,a4
    clr.l -(a7)
    pea.l $0104.w
    jsr h9_0000.l
h3_0426:
    move.l d0,d5
    addq.l #8,a7
    bne.s h3_043E
h3_042C:
    pea.l $0067.w
    move.l d2,-(a7)
    jsr h0_0260.l
h3_0438:
    moveq.l #0,d4
    bra.w h3_0648
h3_043E:
    move.l $001A(a2),d6
    move.l d3,-(a7)
    move.l d5,-(a7)
    jsr h5_002C.l
h3_044C:
    pea.l h4_0006.l
    move.l d5,-(a7)
    jsr h5_0038.l
h3_045A:
    pea.l $03EE.w
    move.l d5,-(a7)
    jsr h8_0000.l
h3_0466:
    move.l d0,d3
    lea.l $0018(a7),a7
    beq.w h3_0638
h3_0470:
    moveq.l #0,d1
    move.w $0010(a2),d1
    moveq.l #3,d0
    and.l d0,d1
    moveq.l #1,d0
    cmp.l d1,d0
    bne.s h3_0484
h3_0480:
    clr.l $001A(a2)
h3_0484:
    pea.l $004E.w
    move.l a2,-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_0490:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.w h3_0638
h3_049A:
    tst.l $0042(a2)
    beq.s h3_04B8
h3_04A0:
    pea.l $0038.w
    move.l $0042(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_04AE:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.w h3_0638
h3_04B8:
    btst.b #2,$0011(a2)
    beq.s h3_04F2
h3_04C0:
    move.l $0016(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h2_0000.l
h3_04CE:
    move.l d0,d4
    lea.l $000C(a7),a7
    beq.w h3_062E
h3_04D8:
    move.l $001A(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h2_0000.l
h3_04E6:
    move.l d0,d4
    lea.l $000C(a7),a7
    bne.s h3_0522
    bra.w h3_062E
h3_04F2:
    move.l $0016(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h2_007A.l
h3_0500:
    move.l d0,d4
    lea.l $000C(a7),a7
    beq.w h3_062E
h3_050A:
    move.l $001A(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h2_007A.l
h3_0518:
    move.l d0,d4
    lea.l $000C(a7),a7
    beq.w h3_062E
h3_0522:
    tst.l $001E(a2)
    bne.w h3_052A
h3_052A:
    tst.l $0032(a2)
    beq.s h3_0570
h3_0530:
    move.l $0032(a2),-(a7)
    jsr h5_0000.l
h3_053A:
    addq.l #1,d0
    move.l d0,-$0004(a6)
    pea.l $0004.w
    pea.l -$0004(a6)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_054E:
    move.l d0,d4
    lea.l $0014(a7),a7
    beq.w h3_062E
h3_0558:
    move.l -$0004(a6),-(a7)
    move.l $0032(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_0566:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.w h3_062E
h3_0570:
    tst.l $0036(a2)
    beq.w h3_05EA
h3_0578:
    movea.l $0036(a2),a3
    moveq.l #4,d1
    move.l d1,-$0004(a6)
    bra.s h3_058A
h3_0584:
    addq.l #4,a3
    addq.l #4,-$0004(a6)
h3_058A:
    tst.l (a3)
    bne.s h3_0584
h3_058E:
    pea.l $0004.w
    pea.l -$0004(a6)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_059C:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.w h3_062E
h3_05A6:
    movea.l $0036(a2),a3
    bra.s h3_05E6
h3_05AC:
    move.l (a3),-(a7)
    jsr h5_0000.l
h3_05B4:
    addq.l #1,d0
    move.l d0,-$0004(a6)
    pea.l $0004.w
    pea.l -$0004(a6)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_05C8:
    move.l d0,d4
    lea.l $0014(a7),a7
    beq.s h3_062E
h3_05D0:
    move.l -$0004(a6),-(a7)
    move.l (a3),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_05DC:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.s h3_062E
h3_05E4:
    addq.l #4,a3
h3_05E6:
    tst.l (a3)
    bne.s h3_05AC
h3_05EA:
    tst.l $0046(a2)
    beq.s h3_062E
h3_05F0:
    move.l $0046(a2),-(a7)
    jsr h5_0000.l
h3_05FA:
    addq.l #1,d0
    move.l d0,-$0004(a6)
    pea.l $0004.w
    pea.l -$0004(a6)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_060E:
    move.l d0,d4
    lea.l $0014(a7),a7
    beq.s h3_062E
h3_0616:
    move.l -$0004(a6),-(a7)
    move.l $0046(a2),-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr (a4) ; CANDIDATE: indirect_call index unresolved
h3_0624:
    move.l d0,d4
    lea.l $0010(a7),a7
    beq.w h3_062E
h3_062E:
    move.l d3,-(a7)
    jsr h8_001C.l
h3_0636:
    addq.l #4,a7
h3_0638:
    pea.l $0104.w
    move.l d5,-(a7)
    jsr h9_0018.l
h3_0644:
    move.l d6,$001A(a2)
h3_0648:
    addq.l #8,a7
    move.l d4,d0
    movem.l -$0024(a6),d2-d6/a2-a4
    unlk a6
    rts
h3_0656:
    move.l a2,-(a7)
    movea.l $000C(a7),a0
    lea.l $0002(a0),a2
    bra.s h3_066C
h3_0662:
    move.l d0,-(a7)
    jsr h9_0030.l
h3_066A:
    addq.l #4,a7
h3_066C:
    move.l a2,-(a7)
    jsr h9_005C.l
h3_0674:
    move.l d0,d0
    addq.l #4,a7
    beq.s h3_0680
h3_067A:
    cmpa.l $0008(a2),a2
    bne.s h3_0662
h3_0680:
    tst.l d0
    beq.s h3_068E
h3_0684:
    move.l d0,-(a7)
    jsr h9_0030.l
h3_068C:
    addq.l #4,a7
h3_068E:
    movea.l (a7)+,a2
    rts
h3_0692:
    move.l $0004(a7),d0
    movea.l $0008(a7),a0
    pea.l $008C(a0)
    move.l d0,-(a7)
    jsr h3_0656(pc)
h3_06A4:
    addq.l #8,a7
    rts
h3_06A8:
    movem.l d2-d3/a2,-(a7)
    move.l $0010(a7),d2
    move.l #$10000,-(a7)
    pea.l $00A8.w
    jsr h9_0000.l
h3_06C0:
    movea.l d0,a2
    move.l a2,d3
    addq.l #8,a7
    beq.s h3_0714
h3_06C8:
    pea.l $008E(a2)
    jsr h7_0000.l
h3_06D2:
    pea.l $008C(a2)
    move.l d2,-(a7)
    jsr h1_004E.l
h3_06DE:
    tst.l d0
    lea.l $000C(a7),a7
    bne.s h3_06F6
h3_06E6:
    pea.l $00A8.w
    move.l a2,-(a7)
    jsr h9_0018.l
h3_06F2:
    addq.l #8,a7
    bra.s h3_0714
h3_06F6:
    pea.l $00A8.w
    move.l a2,-(a7)
    pea.l $008C(a2)
    move.l d2,-(a7)
    jsr h3_071C.l
h3_0708:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h3_0714
h3_0710:
    move.l a2,d0
    bra.s h3_0716
h3_0714:
    moveq.l #0,d0
h3_0716:
    movem.l (a7)+,d2-d3/a2
    rts
h3_071C:
    movem.l d2/a2,-(a7)
    move.l $000C(a7),d0
    movea.l $0010(a7),a2
    move.l $0014(a7),d2
    subq.w #1,(a2)
    bgt.s h3_0746
h3_0730:
    move.l a2,-(a7)
    move.l d0,-(a7)
    jsr h1_004E.l
h3_073A:
    tst.l d0
    addq.l #8,a7
    bne.s h3_0744
h3_0740:
    moveq.l #0,d0
    bra.s h3_0762
h3_0744:
    subq.w #1,(a2)
h3_0746:
    movea.l $000A(a2),a1
    move.w (a2),d0
    ext.l d0
    asl.l #3,d0
    move.l d2,$10(a1,d0.l)
    move.w (a2),d0
    ext.l d0
    asl.l #3,d0
    move.l $0018(a7),$14(a1,d0.l)
    moveq.l #1,d0
h3_0762:
    movem.l (a7)+,d2/a2
    rts
h3_0768:
    movem.l d2-d4/a2,-(a7)
    move.l $0014(a7),d2
    move.l $0018(a7),d3
    move.l #$10000,-(a7)
    pea.l $005E.w
    jsr h9_0000.l
h3_0784:
    move.l d0,d4
    addq.l #8,a7
    beq.s h3_07E2
h3_078A:
    move.l d4,d0
    moveq.l #78,d1
    add.l d1,d0
    movea.l d0,a2
    pea.l $0002(a2)
    jsr h7_0000.l
h3_079C:
    move.l a2,-(a7)
    move.l d2,-(a7)
    jsr h1_004E.l
h3_07A6:
    tst.l d0
    lea.l $000C(a7),a7
    beq.s h3_07E4
h3_07AE:
    pea.l $005E.w
    move.l d4,-(a7)
    move.l a2,-(a7)
    move.l d2,-(a7)
    jsr h3_071C(pc)
h3_07BC:
    tst.l d0
    lea.l $0010(a7),a7
    beq.s h3_07E4
h3_07C4:
    move.l a2,-(a7)
    move.l d4,-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h3_0124(pc)
h3_07D0:
    tst.l d0
    lea.l $0010(a7),a7
    bne.s h3_07E2
h3_07D8:
    move.l a2,-(a7)
    move.l d2,-(a7)
    jsr h3_0656(pc)
h3_07E0:
    bra.s h3_07F0
h3_07E2:
    bra.s h3_07F4
h3_07E4:
    pea.l $005E.w
    move.l d4,-(a7)
    jsr h9_0018.l
h3_07F0:
    moveq.l #0,d4
    addq.l #8,a7
h3_07F4:
    move.l d4,d0
    movem.l (a7)+,d2-d4/a2
    rts
h3_07FC:
    move.l d2,-(a7)
    move.l $0008(a7),d2
    move.l $000C(a7),d1
    moveq.l #78,d0
    add.l d0,d1
    move.l d1,-(a7)
    move.l d2,-(a7)
    jsr h3_0656(pc)
h3_0812:
    addq.l #8,a7
    move.l (a7)+,d2
    rts
h3_0818:
    movem.l d2-d4/a2-a3,-(a7)
    movea.l $0018(a7),a2
    move.l $001C(a7),d2
    move.l d2,-(a7)
    jsr h5_0000.l
h3_082C:
    move.l d0,d3
    move.l a2,d4
    addq.l #4,a7
    beq.s h3_085C
h3_0834:
    bra.s h3_0856
h3_0836:
    move.l d3,-(a7)
    move.l d2,-(a7)
    move.l a3,-(a7)
    jsr h5_0048.l
h3_0842:
    tst.l d0
    lea.l $000C(a7),a7
    bne.s h3_0856
h3_084A:
    adda.l d3,a3
    cmpi.b #61,(a3)+
    bne.s h3_0856
h3_0852:
    move.l a3,d0
    bra.s h3_085E
h3_0856:
    movea.l (a2)+,a3
    move.l a3,d0
    bne.s h3_0836
h3_085C:
    moveq.l #0,d0
h3_085E:
    movem.l (a7)+,d2-d4/a2-a3
    rts
h3_0864:
    movem.l d2-d5,-(a7)
    move.l $0014(a7),d2
    move.l $0018(a7),d3
    move.l d3,-(a7)
    jsr h5_0000.l
h3_0878:
    move.l d0,d5
    addq.l #4,a7
    bra.s h3_08CA
h3_087E:
    pea.l $007C.w
    move.l d2,-(a7)
    jsr h5_0010.l
h3_088A:
    move.l d0,d4
    addq.l #8,a7
    beq.s h3_0896
h3_0890:
    move.l d4,d0
    sub.l d2,d0
    bra.s h3_08A0
h3_0896:
    move.l d2,-(a7)
    jsr h5_0000.l
h3_089E:
    addq.l #4,a7
h3_08A0:
    cmp.l d5,d0
    bne.s h3_08BE
h3_08A4:
    move.l d5,-(a7)
    move.l d3,-(a7)
    move.l d2,-(a7)
    jsr h5_0048.l
h3_08B0:
    tst.l d0
    lea.l $000C(a7),a7
    bne.s h3_08BE
h3_08B8:
    moveq.l #1,d2
    move.l d2,d0
    bra.s h3_08D0
h3_08BE:
    tst.l d4
    beq.s h3_08C8
h3_08C2:
    move.l d4,d2
    addq.l #1,d2
    bra.s h3_08CA
h3_08C8:
    moveq.l #0,d2
h3_08CA:
    tst.l d2
    bne.s h3_087E
h3_08CE:
    moveq.l #0,d0
h3_08D0:
    movem.l (a7)+,d2-d5
    rts
h3_08D6:
    movem.l d2-d4/a2-a4,-(a7)
    movea.l $001C(a7),a2
    movea.l $0020(a7),a3
    moveq.l #30,d4
    movea.l a3,a4
    clr.b $001E(a2)
    pea.l $0005.w
    pea.l h4_000C.l
    move.l a4,-(a7)
    jsr h5_0048.l
h3_08FC:
    tst.l d0
    lea.l $000C(a7),a7
    beq.s h3_0926
h3_0904:
    pea.l h4_0012.l
    move.l a2,-(a7)
    jsr h5_002C.l
h3_0912:
    move.l d4,-(a7)
    move.l a3,-(a7)
    move.l a2,-(a7)
    jsr h5_006C.l
h3_091E:
    lea.l $0014(a7),a7
    bra.w h3_09B6
h3_0926:
    addq.l #5,a4
    pea.l $0003.w
    pea.l h4_001C.l
    move.l a4,-(a7)
    jsr h5_0048.l
h3_093A:
    tst.l d0
    lea.l $000C(a7),a7
    bne.s h3_0948
h3_0942:
    moveq.l #1,d3
    addq.l #3,a4
    bra.s h3_0992
h3_0948:
    moveq.l #0,d3
    bra.s h3_095C
h3_094C:
    move.l d3,d0
    add.l d0,d0
    move.l d0,d1
    asl.l #2,d0
    add.l d1,d0
    add.l d2,d0
    move.l d0,d3
    addq.l #1,a4
h3_095C:
    move.b (a4),d0
    ext.w d0
    ext.l d0
    move.l d0,-(a7)
    jsr h3_09BE.l
h3_096A:
    move.l d0,d2
    addq.l #4,a7
    bge.s h3_094C
h3_0970:
    tst.l d3
    beq.s h3_0904
h3_0974:
    pea.l $0004.w
    pea.l h4_0020.l
    move.l a4,-(a7)
    jsr h5_0048.l
h3_0986:
    tst.l d0
    lea.l $000C(a7),a7
    bne.w h3_0904
h3_0990:
    addq.l #4,a4
h3_0992:
    move.l d3,d0
    addq.l #1,d0
    move.l d0,-(a7)
    pea.l h4_0026.l
    move.l a2,-(a7)
    jsr h6_00C8.l
h3_09A6:
    move.l d4,-(a7)
    move.l a4,-(a7)
    move.l a2,-(a7)
    jsr h5_006C.l
h3_09B2:
    lea.l $0018(a7),a7
h3_09B6:
    move.l a2,d0
    movem.l (a7)+,d2-d4/a2-a4
    rts
h3_09BE:
    move.l $0004(a7),d1
    moveq.l #48,d0
    cmp.l d1,d0
    bgt.s h3_09D6
h3_09C8:
    moveq.l #57,d0
    cmp.l d1,d0
    blt.s h3_09D6
h3_09CE:
    move.l d1,d0
    moveq.l #48,d1
    sub.l d1,d0
    bra.s h3_09D8
h3_09D6:
    moveq.l #-1,d0
h3_09D8:
    rts
    DC.B    $00,$00
    SECTION section,data
h4_0000:
    DC.B    ".info",0
    DC.B    ".info",0
    DC.B    "copy ",0
    DC.B    "copy of ",0
    DC.B    $00
    DC.L    $6f662000
    DC.B    " of ",0
    DC.B    $00
    DC.B    "copy %ld of ",0
    DC.B    $00
    SECTION section,code
h5_0000:
    movea.l $0004(a7),a0
    moveq.l #-1,d0
h5_0006:
    tst.b (a0)+
    dbeq.w d0,h5_0006
h5_000C:
    not.l d0
    rts
h5_0010:
    movea.l $0004(a7),a0
    move.l $0008(a7),d0
h5_0018:
    move.b (a0)+,d1
    beq.s h5_0026
h5_001C:
    cmp.b d0,d1
    bne.s h5_0018
h5_0020:
    subq.l #1,a0
    move.l a0,d0
h5_0024:
    rts
h5_0026:
    moveq.l #0,d0
    bra.s h5_0024
    DC.B    $00,$00
h5_002C:
    movem.l $0004(a7),a0-a1
h5_0032:
    move.b (a1)+,(a0)+
    bne.s h5_0032
h5_0036:
    rts
h5_0038:
    movem.l $0004(a7),a0-a1
h5_003E:
    tst.b (a0)+
    bne.s h5_003E
h5_0042:
    subq.l #1,a0
    bra.s h5_0032
    DC.B    $00,$00
h5_0048:
    movem.l $0004(a7),a0-a1
    move.l $000C(a7),d0
h5_0052:
    subq.l #1,d0
    blt.s h5_0060
h5_0056:
    move.b (a1)+,d1
    cmp.b (a0)+,d1
    bne.s h5_0064
h5_005C:
    tst.b d1
    bne.s h5_0052
h5_0060:
    moveq.l #0,d0
h5_0062:
    rts
h5_0064:
    moveq.l #1,d0
    bgt.s h5_0062
    moveq.l #-1,d0
    rts
h5_006C:
    movem.l $0004(a7),a0-a1
    move.l $000C(a7),d0
h5_0076:
    tst.b (a0)+
    beq.s h5_0080
h5_007A:
    subq.l #1,d0
    bgt.s h5_0076
h5_007E:
    bra.s h5_0086
h5_0080:
    subq.l #1,a0
    bsr.w h5_0092
h5_0086:
    rts
    DC.B    $4c,$ef,$03,$00,$00,$04,$20,$2f,$00,$0c ; VIOLATION: orphaned code island at $0088 is not reached from known entrypoints
h5_0092:
    subq.l #1,d0
    blt.s h5_00A2
h5_0096:
    move.b (a1)+,(a0)+
    bne.s h5_0092
h5_009A:
    subq.l #1,d0
    ble.s h5_00A2
h5_009E:
    clr.b (a0)+
    bra.s h5_009A
h5_00A2:
    rts
    SECTION section,code
h6_0000:
    cmpi.l #65535,d2
    bgt.s h6_0020
h6_0008:
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
h6_0020:
    move.l d1,d0
    clr.w d0
    swap.w d0
    swap.w d1
    clr.w d1
    movea.l d2,a1
    moveq.l #15,d2
h6_002E:
    add.l d1,d1
    addx.l d0,d0
    cmpa.l d0,a1
    bgt.s h6_003A
h6_0036:
    sub.l a1,d0
    addq.w #1,d1
h6_003A:
    dbf.w d2,h6_002E
h6_003E:
    rts
h6_0040:
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
    DC.B    $2f,$02,$24,$01,$22,$00,$61,$98,$24,$1f,$4e,$75 ; VIOLATION: orphaned code island at $0060 is not reached from known entrypoints
    DC.B    $2f,$02,$24,$01,$22,$00,$61,$8c,$20,$01,$24,$1f,$4e,$75 ; VIOLATION: orphaned code island at $006C is not reached from known entrypoints
    DC.B    $2f,$02 ; VIOLATION: orphaned code island at $007A is not reached from known entrypoints
    DC.L    $24016c02,$44822200,$70004a81,$6c044481,$46802040,$6100ff6e,$34086702,$4480241f
    DC.B    $4e,$75
    DC.B    $2f,$02 ; VIOLATION: orphaned code island at $009E is not reached from known entrypoints
    DC.L    $20407000,$24016c04,$44824680,$22086c04,$44814680,$20406100,$ff482408,$67024481
    DC.L    $2001241f,$4e750000
h6_00C8:
    movem.l a2-a4/a6,-(a7)
    movea.l $0014(a7),a3
    movea.l $0018(a7),a0
    lea.l $001C(a7),a1
    lea.l h6_00EC(pc),a2
    movea.l $00000004.l,a6
    jsr _LVORawDoFmt(a6)
h6_00E6:
    movem.l (a7)+,a2-a4/a6
    rts
h6_00EC:
    move.b d0,(a3)+
    rts
    SECTION section,code
h7_0000:
    movea.l $0004(a7),a0
    move.l a0,(a0)
    addq.l #4,(a0)
    clr.l $0004(a0)
    move.l a0,$0008(a0)
    rts
    DC.B    $00,$00
    SECTION section,code
h8_0000:
    movem.l d2/a6,-(a7)
    movea.l h0dl_DOSBase.l,a6
    movem.l $000C(a7),d1-d2
    jsr _LVOOpen(a6)
h8_0014:
    movem.l (a7)+,d2/a6
    rts
    DC.B    $00,$00
h8_001C:
    move.l a6,-(a7)
    movea.l h0dl_DOSBase.l,a6
    move.l $0008(a7),d1
    jsr _LVOClose(a6)
h8_002C:
    movea.l (a7)+,a6
    rts
h8_0030:
    movem.l d2-d3/a6,-(a7)
    movea.l h0dl_DOSBase.l,a6
    movem.l $0010(a7),d1-d3
    jsr _LVORead(a6)
h8_0044:
    movem.l (a7)+,d2-d3/a6
    rts
    DC.B    $00,$00
h8_004C:
    movem.l d2-d3/a6,-(a7)
    movea.l h0dl_DOSBase.l,a6
    movem.l $0010(a7),d1-d3
    jsr _LVOWrite(a6)
h8_0060:
    movem.l (a7)+,d2-d3/a6
    rts
    DC.B    $00,$00
    SECTION section,code
h9_0000:
    move.l a6,-(a7)
    movea.l h0dl_ExecBase.l,a6
    movem.l $0008(a7),d0-d1
    jsr _LVOAllocMem(a6)
h9_0012:
    movea.l (a7)+,a6
    rts
    DC.B    $00,$00
h9_0018:
    move.l a6,-(a7)
    movea.l h0dl_ExecBase.l,a6
    movea.l $0008(a7),a1
    move.l $000C(a7),d0
    jsr _LVOFreeMem(a6)
h9_002C:
    movea.l (a7)+,a6
    rts
h9_0030:
    move.l a6,-(a7)
    movea.l h0dl_ExecBase.l,a6
    movea.l $0008(a7),a0
    jsr _LVOFreeEntry(a6)
h9_0040:
    movea.l (a7)+,a6
    rts
h9_0044:
    move.l a6,-(a7)
    movea.l h0dl_ExecBase.l,a6
    movem.l $0008(a7),a0-a1
    jsr _LVOAddTail(a6)
h9_0056:
    movea.l (a7)+,a6
    rts
    DC.B    $00,$00
h9_005C:
    move.l a6,-(a7)
    movea.l h0dl_ExecBase.l,a6
    movea.l $0008(a7),a0
    jsr _LVORemTail(a6)
h9_006C:
    movea.l (a7)+,a6
    rts
