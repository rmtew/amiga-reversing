; Generated disassembly -- vasm Motorola syntax
; Source: bin\Search for the King, The (1991)(Accolade)(Disk 1 of 5).adf::libs\icon.library
; 4680 bytes, 74 entities, 193 blocks
; OS compatibility floor: 1.3

; Resident structure
;   matchword: 0x4AFC
;   version: 34, type: library, priority: 70
;   flags: 0x80, auto-init: True
;   name: icon.library
;   id string: icon 34.2 (22 Jun 1988)

;   init offset: 0x48

; Library structure
;   entry registers: A6=ExecBase, A6=icon.library base
;   name: icon.library
;   version: 34
;   id string: icon 34.2 (22 Jun 1988)

;   public functions: 12
;   total LVOs: 19
;   exports: BumpRevision, MatchToolValue, FindToolType, FreeDiskObject, PutDiskObject, GetDiskObject, AddFreeList, FreeFreeList

; Hunk 0: 644 bytes, 71 entities, 45 blocks

; Absolute symbols
AbsExecBase	EQU	$4

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/initializers.i"
    INCLUDE "exec/libraries.i"
    INCLUDE "exec/nodes.i"

    section code,code

dat_0000:
    dc.b    $70,$ff,$4e,$75
resident_matchword:
    dc.w    $4afc
resident_matchtag:
    dc.l    resident_matchword
resident_endskip:
    dc.l    dat_0280
resident_flags:
    dc.b    $80
resident_version:
    dc.b    $22
resident_type:
    dc.b    $09
resident_priority:
    dc.b    $46
resident_name_ptr:
    dc.l    dat_001e
resident_idstring_ptr:
    dc.l    dat_002b
resident_init_ptr:
    dc.l    resident_base_size
dat_001e:
    dc.b    "icon.library",0
dat_002b:
    dc.b    "icon 34.2 (22 Jun 1988)"
    dc.b    $0d,$0a
    dcb.b   4,0
resident_base_size:
    dc.l    $0000002e
resident_vectors_ptr:
    dc.l    dat_0058
resident_initstruct_ptr:
    dc.l    dat_00a4
resident_initfunc_ptr:
    dc.l    library_init
dat_0058:
    dc.l    lib_open
    dc.l    lib_close
    dc.l    lib_expunge
    dc.l    lib_extfunc
    dc.l    icon_private_1
    dc.l    icon_private_2
    dc.l    icon_private_3
    dc.l    put_disk_object
    dc.l    free_free_list
    dc.l    icon_private_5
    dc.l    icon_private_6
    dc.l    add_free_list
    dc.l    get_disk_object
    dc.l    put_disk_object
    dc.l    free_disk_object
    dc.l    find_tool_type
    dc.l    match_tool_value
    dc.l    bump_revision
    dc.b    $ff,$ff,$ff,$ff
dat_00a4:
    INITBYTE LN_TYPE,$09
    INITLONG LN_NAME,dat_001e
    INITBYTE LIB_FLAGS,$06
    INITWORD LIB_VERSION,$0022
    INITWORD LIB_REVISION,$0002
    INITLONG LIB_IDSTRING,dat_002b
    dc.b    $00
    dc.b    $00,$00,$00
str_00d0:
    dc.b    "dos.library",0
lib_open:
    addq.w #1,LIB_OPENCNT(a6)
    bclr #3,LIB_FLAGS(a6)
    move.l a6,d0
    rts
lib_close:
    moveq #0,d0
    subq.w #1,LIB_OPENCNT(a6)
    bne.s loc_00fe
loc_00f2:
    btst #3,LIB_FLAGS(a6)
    beq.s loc_00fe
loc_00fa:
    bsr.w lib_expunge
loc_00fe:
    rts
lib_expunge:
    tst.w LIB_OPENCNT(a6)
    bne.s loc_013a
loc_0106:
    move.l 42(a6),-(sp)
    movea.l a6,a1
    movea.l (a1),a0
    movea.l LN_PRED(a1),a1
    move.l a0,(a1)
    move.l a1,LN_PRED(a0)
    movea.l a6,a1
    moveq #0,d0
    moveq #0,d1
    move.w LIB_NEGSIZE(a6),d0
    suba.l d0,a1
loc_0124:
    move.w LIB_POSSIZE(a6),d1
    add.l d1,d0
    move.l a6,-(sp)
    movea.l 34(a6),a6
    jsr -210(a6) ; unresolved_indirect_core:disp
loc_0134:
    movea.l (sp)+,a6
    move.l (sp)+,d0
    bra.s loc_0142
loc_013a:
    bset #3,LIB_FLAGS(a6)
    moveq #0,d0
loc_0142:
    rts
lib_extfunc:
    moveq #0,d0
    rts
library_init:
    move.l a2,-(sp)
    movea.l d0,a2
    move.l a0,42(a2)
    move.l a6,34(a2)
    lea str_00d0(pc),a1 ; OldOpenLibrary: libName
    jsr _LVOOldOpenLibrary(a6)
loc_015c:
    move.l d0,38(a2)
    bne.s loc_017c
loc_0162:
    movem.l d7/a5-a6,-(sp)
    move.l #$9038007,d7 ; Alert: alertNum
    movea.l AbsExecBase,a6
    jsr _LVOAlert(a6)
loc_0174:
    movem.l (sp)+,d7/a5-a6
    moveq #0,d0
    bra.s loc_018e
loc_017c:
    move.l 34(a2),sub_0192
    move.l 38(a2),dat_0196
    move.l a2,d0
loc_018e:
    movea.l (sp)+,a2
    rts
sub_0192:
    dcb.b   4,0
dat_0196:
    dcb.b   4,0
icon_private_1:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr dat_0000
loc_01a4:
    addq.l #8,sp
    rts
icon_private_2:
    movem.l a0-a1,-(sp)
    move.l a6,-(sp)
    jsr dat_00a8
loc_01b4:
    lea 12(sp),sp
    rts
icon_private_3:
    movem.l a0-a2,-(sp)
    move.l a6,-(sp)
    jsr loc_0124
loc_01c6:
    lea 16(sp),sp
    rts
put_disk_object:
    movem.l a0-a1,-(sp)
    move.l a6,-(sp)
    jsr sub_03fe
loc_01d8:
    lea 12(sp),sp
    rts
free_free_list:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr sub_0656
loc_01e8:
    addq.l #8,sp
    rts
icon_private_5:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr sub_0692
loc_01f6:
    addq.l #8,sp
    rts
icon_private_6:
    move.l a6,-(sp)
    jsr sub_06a8
loc_0202:
    addq.l #4,sp
    rts
add_free_list:
    movem.l a0-a2,-(sp)
    move.l a6,-(sp)
    jsr sub_071c
loc_0212:
    lea 16(sp),sp
    rts
get_disk_object:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr sub_0768
loc_0222:
    addq.l #8,sp
    rts
free_disk_object:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr sub_07fc
loc_0230:
    addq.l #8,sp
    rts
find_tool_type:
    movem.l a0-a1,-(sp)
    jsr sub_0818
loc_023e:
    addq.l #8,sp
    rts
match_tool_value:
    movem.l a0-a1,-(sp)
    jsr sub_0864
loc_024c:
    addq.l #8,sp
    rts
bump_revision:
    movem.l a0-a1,-(sp)
    jsr sub_08d6
loc_025a:
    addq.l #8,sp
    rts
sub_025e:
    dc.b    $00,$00,$2f,$0e,$2c,$6f,$00,$08,$93,$c9,$2f,$0e,$2c,$6e,$00,$22
    dc.b    $4e,$ae,$fe,$da
hint_0272:
; --- unverified ---
    movea.l (sp)+,a6
    movea.l d0,a1
    move.l 12(sp),148(a1)
    movea.l (sp)+,a6
    rts
dat_0280:
    dcb.b   4,0

; Hunk 1: 232 bytes, 0 entities, 7 blocks

    section code,code

loc_0000:
    movem.l d2-d5,-(sp)
    move.l 20(sp),d3
    move.l 24(sp),d4
    move.l 28(sp),d2
    move.l 32(sp),-(sp)
    move.l d2,-(sp)
    jsr loc_0000
loc_001c:
    move.l d0,d5
    addq.l #8,sp
    beq.s loc_0046
loc_0022:
    move.l d2,-(sp)
    move.l d5,-(sp)
    move.l d4,-(sp)
    move.l d3,-(sp)
    jsr loc_071c
loc_0030:
    tst.l d0
    lea 16(sp),sp
    bne.s loc_0046
loc_0038:
    move.l d2,-(sp)
    move.l d5,-(sp)
    jsr dat_0018
loc_0042:
    moveq #0,d5
dat_0044:
    addq.l #8,sp
loc_0046:
    move.l d5,d0
    movem.l (sp)+,d2-d5
dat_004c:
    rts
hint_004e:
; --- unverified ---
    movem.l d2/a2,-(sp)
    movea.l 16(sp),a2
    move.l #$10000,-(sp)
    pea ($0060).w
    jsr loc_0000
hint_0066:
; --- unverified ---
    movea.l d0,a0
    move.l a0,d2
    addq.l #8,sp
    beq.s hint_008a
hint_006e:
; --- unverified ---
    move.w #$a,14(a0)
    move.w #$a,(a2)
    move.l a0,-(sp)
    pea 2(a2)
    jsr dat_0044
hint_0084:
; --- unverified ---
    moveq #1,d0
    addq.l #8,sp
    bra.s hint_008c
hint_008a:
    dc.b    $70,$00
hint_008c:
; --- unverified ---
    movem.l (sp)+,d2/a2
    rts
hint_0092:
; --- unverified ---
    move.l 8(sp),d0
    move.l 12(sp),d1
    move.l 16(sp),-(sp)
    move.l d1,-(sp)
    move.l d0,-(sp)
    jsr loc_0030
hint_00a8:
; --- unverified ---
    move.l d0,d1
    cmp.l 28(sp),d0
    lea 12(sp),sp
    beq.s hint_00b8
hint_00b4:
; --- unverified ---
    moveq #0,d0
    bra.s hint_00ba
hint_00b8:
    dc.b    $20,$01
hint_00ba:
; --- unverified ---
    rts
hint_00bc:
; --- unverified ---
    move.l 8(sp),d0
    move.l 12(sp),d1
    move.l 16(sp),-(sp)
    move.l d1,-(sp)
    move.l d0,-(sp)
    jsr dat_004c
hint_00d2:
; --- unverified ---
    move.l d0,d1
    cmp.l 28(sp),d0
    lea 12(sp),sp
    beq.s hint_00e2
hint_00de:
; --- unverified ---
    moveq #0,d0
    bra.s hint_00e4
hint_00e2:
    dc.b    $20,$01
hint_00e4:
; --- unverified ---
    rts
    dc.b    $00,$00

; Hunk 2: 640 bytes, 0 entities, 18 blocks

    section code,code

loc_0000:
    movem.l d2-d3/a2,-(sp)
    move.l 16(sp),d2
    move.l 20(sp),d3
    movea.l 24(sp),a2
    moveq #1,d0
    move.l a2,d1
    beq.s loc_0074
loc_0016:
    pea ($0014).w
    move.l a2,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_00bc
loc_0026:
    move.l d0,d0
    lea 16(sp),sp
    beq.s loc_0074
loc_002e:
    move.w 4(a2),d1
    ext.l d1
    moveq #15,d0
    add.l d0,d1
    asr.l #3,d1
    andi.l #$fffe,d1
loc_0040:
    move.w 6(a2),d0
    ext.l d0
    jsr loc_0040
loc_004c:
    move.l d0,d1
    move.w 8(a2),d0
    ext.l d0
    jsr loc_0040
loc_005a:
    move.l d0,-(sp)
    move.l 10(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_00bc
loc_006a:
    move.l d0,d0
    lea 16(sp),sp
    beq.w loc_0074
loc_0074:
    movem.l (sp)+,d2-d3/a2
    rts
hint_007a:
; --- unverified ---
    movem.l d2-d3/a2,-(sp)
    move.l 16(sp),d2
    move.l 20(sp),d3
    movea.l 24(sp),a2
    bra.s loc_00cc
loc_008c:
    pea ($0010).w
    move.l a2,-(sp)
dat_0092:
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_00bc
loc_009c:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_00d4
loc_00a4:
    move.b 7(a2),d0
    ext.w d0
    ext.l d0
    add.l d0,d0
    add.l d0,d0
    move.l d0,-(sp)
    move.l 8(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_00bc
loc_00c0:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_00d4
loc_00c8:
    movea.l 12(a2),a2
loc_00cc:
    move.l a2,d0
    bne.s loc_008c
loc_00d0:
    moveq #1,d0
    bra.s loc_00d6
loc_00d4:
    moveq #0,d0
loc_00d6:
    movem.l (sp)+,d2-d3/a2
    rts
hint_00dc:
; --- unverified ---
    movem.l d2-d5/a2,-(sp)
    move.l 24(sp),d2
    move.l 28(sp),d3
    move.l 32(sp),d4
    tst.l 36(sp)
    beq.w hint_019e
hint_00f4:
; --- unverified ---
    move.l #$10000,-(sp)
    pea ($0014).w
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0000
hint_0108:
; --- unverified ---
    move.l d0,52(sp)
    lea 16(sp),sp
    beq.w hint_01a4
hint_0114:
; --- unverified ---
    pea ($0014).w
    move.l 40(sp),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr dat_0092
hint_0126:
; --- unverified ---
    tst.l d0
    lea 16(sp),sp
    beq.w hint_01a4
hint_0130:
; --- unverified ---
    movea.l 36(sp),a0
    move.w 4(a0),d5
    ext.l d5
    moveq #15,d0
    add.l d0,d5
    asr.l #3,d5
    andi.l #$fffe,d5
    move.l d5,d1
    move.w 6(a0),d0
    ext.l d0
    jsr loc_0040
hint_0154:
; --- unverified ---
    move.l d0,d5
    movea.l 36(sp),a2
    move.l d5,d1
    move.w 8(a2),d0
    ext.l d0
    jsr loc_0040
hint_0168:
; --- unverified ---
    move.l d0,d5
    movea.l 36(sp),a2
    pea ($0002).w
    move.l d5,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0000
hint_017e:
; --- unverified ---
    move.l d0,10(a2)
    move.l d5,-(sp)
    movea.l 56(sp),a2
    move.l 10(a2),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr dat_0092
hint_0196:
; --- unverified ---
    tst.l d0
    lea 32(sp),sp
    beq.s hint_01a4
hint_019e:
; --- unverified ---
    move.l 36(sp),d0
    bra.s hint_01a6
hint_01a4:
    dc.b    $70,$ff
hint_01a6:
; --- unverified ---
    movem.l (sp)+,d2-d5/a2
    rts
hint_01ac:
; --- unverified ---
    movem.l d2-d6/a2,-(sp)
    move.l 28(sp),d2
    move.l 32(sp),d3
    move.l 36(sp),d4
    moveq #0,d6
    bra.w hint_026c
hint_01c2:
; --- unverified ---
    move.l #$10000,-(sp)
    pea ($0010).w
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0000
hint_01d6:
; --- unverified ---
    move.l d0,56(sp)
    lea 16(sp),sp
    beq.w hint_0278
hint_01e2:
; --- unverified ---
    tst.l d6
    bne.s hint_01ec
hint_01e6:
; --- unverified ---
    move.l 40(sp),d6
    bra.s hint_01f2
hint_01ec:
    dc.b    $25,$6f,$00,$28,$00,$0c
hint_01f2:
; --- unverified ---
    pea ($0010).w
    move.l 44(sp),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr dat_0092
hint_0204:
; --- unverified ---
    tst.l d0
    lea 16(sp),sp
    beq.s hint_0278
hint_020c:
; --- unverified ---
    movea.l 40(sp),a0
    move.b 7(a0),d5
    ext.w d5
    ext.l d5
    add.l d5,d5
    add.l d5,d5
    movea.l 40(sp),a2
    pea ($0002).w
    move.l d5,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0000
hint_0230:
; --- unverified ---
    move.l d0,8(a2)
    movea.l 56(sp),a0
    tst.l 8(a0)
    lea 16(sp),sp
    beq.s hint_0278
hint_0242:
; --- unverified ---
    move.l d5,-(sp)
    movea.l 44(sp),a2
    move.l 8(a2),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr dat_0092
hint_0256:
; --- unverified ---
    tst.l d0
    lea 16(sp),sp
    beq.s hint_0278
hint_025e:
    dc.b    $24,$6f,$00,$28,$20,$6f,$00,$28,$2f,$68,$00,$0c,$00,$28
hint_026c:
; --- unverified ---
    tst.l 40(sp)
    bne.w hint_01c2
hint_0274:
; --- unverified ---
    move.l d6,d0
    bra.s hint_027a
hint_0278:
    dc.b    $70,$ff
hint_027a:
; --- unverified ---
    movem.l (sp)+,d2-d6/a2
    rts

; Hunk 3: 2524 bytes, 2 entities, 108 blocks

; Absolute symbols
AbsExecBase	EQU	$4

    section code,code

loc_0000:
    link a6,#-80
    movem.l d2-d4/a2,-(sp)
    move.l 8(a6),d2
dat_000c:
    move.l 12(a6),d3
dat_0010:
    move.l d2,-(sp)
dat_0012:
    jsr loc_06a8
loc_0018:
    movea.l d0,a2
    move.l a2,d4
loc_001c:
    addq.l #4,sp
    beq.w loc_009c
loc_0022:
    pea 140(a2)
dat_0026:
    pea -80(a6)
    move.l d3,-(sp)
loc_002c:
    move.l d2,-(sp)
    jsr loc_0124
loc_0034:
    tst.l d0
    lea 16(sp),sp
    bne.s loc_004a
loc_003c:
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr loc_0692
loc_0046:
    addq.l #8,sp
dat_0048:
    bra.s loc_009c
loc_004a:
    lea -76(a6),a0
loc_004e:
    lea 96(a2),a1
    moveq #10,d0
loc_0054:
    move.l (a0)+,(a1)+
    dbf d0,loc_0054
loc_005a:
    move.b -32(a6),61(a2)
    move.l -30(a6),72(a2)
    move.l -26(a6),92(a2)
dat_006c:
    move.l -22(a6),84(a2)
    move.l -18(a6),88(a2)
    move.l -14(a6),76(a2)
    move.l -10(a6),156(a2)
    move.l -6(a6),160(a2)
    tst.l 76(a2)
    beq.s loc_0098
loc_0090:
    movea.l 76(a2),a0
loc_0098:
loc_009c:
    moveq #0,d0
loc_009e:
    movem.l -96(a6),d2-d4/a2
    unlk a6
    rts
dat_00a8:
    dc.b    $4e,$56,$ff,$b0,$48,$e7
    dc.b    "  ",$22,".",0
    dc.b    $08,$24,$2e,$00,$0c,$20,$6e,$00,$10
dat_00bc:
    dc.b    $3d,$7c,$e3,$10,$ff,$b0,$3d,$7c,$00,$01,$ff,$b2
dat_00c8:
    dc.b    $43,$e8,$00,$60,$45,$ee,$ff,$b4,$70,$0a
hint_00d2:
; --- unverified ---
    move.l (a1)+,(a2)+
    dbf d0,hint_00d2
hint_00d8:
    dc.b    $2d,$68,$00,$5c
loc_00dc:
    dc.b    $ff,$e6
    dc.b    $1d,$68,$00,$3d,$ff,$e0,$2d,$68,$00,$54,$ff,$ea,$2d,$68,$00,$58
    dc.b    $ff,$ee,$2d,$68,$00,$4c,$ff,$f2,$2d,$68,$00,$48,$ff,$e2,$2d,$68
    dc.b    $00,$9c,$ff,$f6,$2d,$68,$00,$a0,$ff,$fa,$48,$6e,$ff,$b0,$2f,$02
    dc.b    $2f,$01,$4e,$b9
    dc.l    dat_03fe
hint_0116:
; --- unverified ---
    lea 12(sp),sp
    movem.l -88(a6),d2/a2
    unlk a6
    rts
loc_0124:
    link a6,#-268
    movem.l d2-d5/a2-a5,-(sp)
    move.l 8(a6),d2
    move.l 12(a6),d0
    movea.l 16(a6),a2
    movea.l #loc_0092,a3
    move.l #loc_0000,d3
    lea 4(a2),a4
    move.l d0,-(sp)
    pea -268(a6)
    jsr loc_002c
loc_0154:
    pea loc_0000
    pea -268(a6)
    jsr dat_0038
loc_0164:
    pea ($03ed).w
    pea -268(a6)
    jsr loc_0000
loc_0172:
    move.l d0,d5
    lea 24(sp),sp
    bne.s loc_0180
loc_017a:
    moveq #0,d4
    bra.w loc_03f2
loc_0180:
    pea loc_004e
    move.l a2,-(sp)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3)
loc_018c:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_0196:
    cmpi.w #$e310,(a2)
    bne.w loc_03ee
loc_019e:
    cmpi.w #$1,2(a2)
    bne.w loc_03ee
loc_01a8:
    clr.l (a4)
    clr.l (a4)
loc_01ac:
    tst.l 66(a2)
    beq.s loc_01fc
loc_01b2:
    move.l #$10002,-(sp)
    pea ($01be).w
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_0000
loc_01c8:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_03ee
loc_01d2:
    pea dat_0038
    movea.l d4,a5
    pea (a5)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3)
loc_01e0:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_01ea:
    move.l d4,66(a2)
    movea.l d4,a5
    pea 428(a5)
    jsr loc_0000
loc_01fa:
    addq.l #4,sp
loc_01fc:
    btst #2,13(a4)
    beq.s loc_024a
loc_0204:
    move.l 18(a4),-(sp)
    move.l d5,-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_00dc
loc_0216:
    move.l d0,d4
    moveq #-1,d0
    cmp.l d4,d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_0224:
    move.l d4,18(a4)
    move.l 22(a4),-(sp)
    move.l d5,-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_00dc
loc_023a:
    move.l d0,d4
    moveq #-1,d0
    cmp.l d4,d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_0248:
    bra.s loc_028e
loc_024a:
    move.l 18(a4),-(sp)
    move.l d5,-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_01ac
loc_025c:
    move.l d0,d4
    moveq #-1,d0
dat_0260:
    cmp.l d4,d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_026a:
    move.l d4,18(a4)
    move.l 22(a4),-(sp)
    move.l d5,-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_01ac
loc_0280:
    move.l d0,d4
    moveq #-1,d0
    cmp.l d4,d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_028e:
    move.l d4,22(a4)
    tst.l 26(a4)
    bne.w loc_029a
loc_029a:
    tst.l 50(a2)
    beq.s loc_02f2
loc_02a0:
    pea AbsExecBase
    pea -8(a6)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_02ae:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_02b8:
    move.l #$10000,-(sp)
    move.l -8(a6),-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_0000
loc_02ce:
    move.l d0,50(a2)
    lea 16(sp),sp
    beq.w loc_03ee
loc_02da:
    move.l -8(a6),-(sp)
    move.l 50(a2),-(sp)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_02e8:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_02f2:
    tst.l 54(a2)
    beq.w loc_0392
loc_02fa:
    pea AbsExecBase
    pea -4(a6)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_0308:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_0312:
    move.l #$10000,-(sp)
    move.l -4(a6),-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_0000
loc_0328:
    movea.l d0,a4
    move.l a4,d4
    lea 16(sp),sp
    beq.w loc_03ee
loc_0334:
    move.l a4,54(a2)
    bra.s loc_038a
loc_033a:
    pea AbsExecBase
    pea -8(a6)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_0348:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_0352:
    clr.l -(sp)
    move.l -8(a6),-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_0000
loc_0364:
    move.l d0,(a4)
    lea 16(sp),sp
    beq.w loc_03ee
loc_036e:
    move.l -8(a6),-(sp)
    move.l (a4),-(sp)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_037a:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_0384:
    subq.l #4,-4(a6)
    addq.l #4,a4
loc_038a:
    moveq #4,d0
    cmp.l -4(a6),d0
    blt.s loc_033a
loc_0392:
    tst.l 70(a2)
    beq.s loc_03e0
loc_0398:
    pea AbsExecBase
    pea -8(a6)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_03a6:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_03ee
loc_03ae:
    clr.l -(sp)
    move.l -8(a6),-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr loc_0000
loc_03c0:
    move.l d0,70(a2)
    lea 16(sp),sp
    beq.s loc_03ee
loc_03ca:
    move.l -8(a6),-(sp)
    move.l 70(a2),-(sp)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3) ; unresolved_indirect_core:ind
loc_03d8:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_03ee
loc_03e0:
    moveq #1,d4
loc_03e2:
    move.l d5,-(sp)
    jsr loc_001c
loc_03ea:
    addq.l #4,sp
    bra.s loc_03f2
loc_03ee:
    moveq #0,d4
    bra.s loc_03e2
loc_03f2:
    move.l d4,d0
    movem.l -300(a6),d2-d5/a2-a5
    unlk a6
    rts
dat_03fe:
; --- unverified ---
    link a6,#-4
    movem.l d2-d6/a2-a4,-(sp)
    move.l 8(a6),d2
    move.l 12(a6),d3
    movea.l 16(a6),a2
    moveq #0,d4
    movea.l #dat_00bc,a4
    clr.l -(sp)
    pea ($0104).w
    jsr loc_0000
hint_0426:
; --- unverified ---
    move.l d0,d5
    addq.l #8,sp
    bne.s hint_043e
hint_042c:
; --- unverified ---
    pea ($0067).w
    move.l d2,-(sp)
    jsr dat_0260
hint_0438:
; --- unverified ---
    moveq #0,d4
    bra.w hint_0648
hint_043e:
; --- unverified ---
    move.l 26(a2),d6
    move.l d3,-(sp)
    move.l d5,-(sp)
    jsr loc_002c
hint_044c:
; --- unverified ---
    pea dat_0006
    move.l d5,-(sp)
    jsr dat_0038
hint_045a:
; --- unverified ---
    pea loc_03ee
    move.l d5,-(sp)
    jsr loc_0000
hint_0466:
; --- unverified ---
    move.l d0,d3
    lea 24(sp),sp
    beq.w hint_0638
hint_0470:
; --- unverified ---
    moveq #0,d1
    move.w 16(a2),d1
    moveq #3,d0
    and.l d0,d1
    moveq #1,d0
    cmp.l d1,d0
    bne.s hint_0484
hint_0480:
    dc.b    $42,$aa,$00,$1a
hint_0484:
; --- unverified ---
    pea loc_004e
    move.l a2,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_0490:
; --- unverified ---
    move.l d0,d4
    lea 16(sp),sp
    beq.w hint_0638
hint_049a:
; --- unverified ---
    tst.l 66(a2)
    beq.s hint_04b8
hint_04a0:
; --- unverified ---
    pea dat_0038
    move.l 66(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_04ae:
; --- unverified ---
    move.l d0,d4
    lea 16(sp),sp
    beq.w hint_0638
hint_04b8:
; --- unverified ---
    btst #2,17(a2)
    beq.s hint_04f2
hint_04c0:
; --- unverified ---
    move.l 22(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0000
hint_04ce:
; --- unverified ---
    move.l d0,d4
    lea 12(sp),sp
    beq.w hint_062e
hint_04d8:
; --- unverified ---
    move.l 26(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0000
hint_04e6:
; --- unverified ---
    move.l d0,d4
    lea 12(sp),sp
    bne.s hint_0522
hint_04ee:
; --- unverified ---
    bra.w hint_062e
hint_04f2:
; --- unverified ---
    move.l 22(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr dat_007a
hint_0500:
; --- unverified ---
    move.l d0,d4
    lea 12(sp),sp
    beq.w hint_062e
hint_050a:
; --- unverified ---
    move.l 26(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr dat_007a
hint_0518:
; --- unverified ---
    move.l d0,d4
    lea 12(sp),sp
    beq.w hint_062e
hint_0522:
; --- unverified ---
    tst.l 30(a2)
    bne.w hint_052a
hint_052a:
; --- unverified ---
    tst.l 50(a2)
    beq.s hint_0570
hint_0530:
; --- unverified ---
    move.l 50(a2),-(sp)
    jsr loc_0000
hint_053a:
; --- unverified ---
    addq.l #1,d0
    move.l d0,-4(a6)
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_054e:
; --- unverified ---
    move.l d0,d4
    lea 20(sp),sp
    beq.w hint_062e
hint_0558:
; --- unverified ---
    move.l -4(a6),-(sp)
    move.l 50(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_0566:
; --- unverified ---
    move.l d0,d4
    lea 16(sp),sp
    beq.w hint_062e
hint_0570:
; --- unverified ---
    tst.l 54(a2)
    beq.w hint_05ea
hint_0578:
; --- unverified ---
    movea.l 54(a2),a3
    moveq #4,d1
    move.l d1,-4(a6)
    bra.s hint_058a
hint_0584:
    dc.b    $58,$8b,$58,$ae,$ff,$fc
hint_058a:
; --- unverified ---
    tst.l (a3)
    bne.s hint_0584
hint_058e:
; --- unverified ---
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_059c:
; --- unverified ---
    move.l d0,d4
    lea 16(sp),sp
    beq.w hint_062e
hint_05a6:
; --- unverified ---
    movea.l 54(a2),a3
    bra.s hint_05e6
hint_05ac:
; --- unverified ---
    move.l (a3),-(sp)
    jsr loc_0000
hint_05b4:
; --- unverified ---
    addq.l #1,d0
    move.l d0,-4(a6)
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_05c8:
; --- unverified ---
    move.l d0,d4
    lea 20(sp),sp
    beq.s hint_062e
hint_05d0:
; --- unverified ---
    move.l -4(a6),-(sp)
    move.l (a3),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_05dc:
; --- unverified ---
    move.l d0,d4
    lea 16(sp),sp
    beq.s hint_062e
hint_05e4:
    dc.b    $58,$8b
hint_05e6:
; --- unverified ---
    tst.l (a3)
    bne.s hint_05ac
hint_05ea:
; --- unverified ---
    tst.l 70(a2)
    beq.s hint_062e
hint_05f0:
; --- unverified ---
    move.l 70(a2),-(sp)
    jsr loc_0000
hint_05fa:
; --- unverified ---
    addq.l #1,d0
    move.l d0,-4(a6)
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_060e:
; --- unverified ---
    move.l d0,d4
    lea 20(sp),sp
    beq.s hint_062e
hint_0616:
; --- unverified ---
    move.l -4(a6),-(sp)
    move.l 70(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4) ; unresolved_indirect_hint:ind
hint_0624:
; --- unverified ---
    move.l d0,d4
    lea 16(sp),sp
    beq.w hint_062e
hint_062e:
; --- unverified ---
    move.l d3,-(sp)
    jsr loc_001c
hint_0636:
    dc.b    $58,$8f
hint_0638:
; --- unverified ---
    pea ($0104).w
    move.l d5,-(sp)
    jsr loc_0018
hint_0644:
    dc.b    $25,$46,$00,$1a
hint_0648:
; --- unverified ---
    addq.l #8,sp
    move.l d4,d0
    movem.l -36(a6),d2-d6/a2-a4
    unlk a6
    rts
loc_0656:
    move.l a2,-(sp)
    movea.l 12(sp),a0
    lea 2(a0),a2
    bra.s loc_066c
loc_0662:
    move.l d0,-(sp)
    jsr dat_0030
loc_066a:
    addq.l #4,sp
loc_066c:
    move.l a2,-(sp)
    jsr dat_005c
loc_0674:
    move.l d0,d0
    addq.l #4,sp
    beq.s loc_0680
loc_067a:
    cmpa.l 8(a2),a2
    bne.s loc_0662
loc_0680:
    tst.l d0
    beq.s loc_068e
loc_0684:
    move.l d0,-(sp)
    jsr dat_0030
loc_068c:
    addq.l #4,sp
loc_068e:
    movea.l (sp)+,a2
    rts
loc_0692:
    move.l 4(sp),d0
    movea.l 8(sp),a0
    pea 140(a0)
    move.l d0,-(sp)
    jsr loc_0656(pc)
loc_06a4:
    addq.l #8,sp
    rts
loc_06a8:
    movem.l d2-d3/a2,-(sp)
    move.l 16(sp),d2
    move.l #$10000,-(sp)
    pea dat_00a8
    jsr loc_0000
loc_06c0:
    movea.l d0,a2
    move.l a2,d3
    addq.l #8,sp
    beq.s loc_0714
loc_06c8:
    pea 142(a2)
    jsr loc_0000
loc_06d2:
    pea 140(a2)
    move.l d2,-(sp)
    jsr loc_004e
loc_06de:
    tst.l d0
    lea 12(sp),sp
    bne.s loc_06f6
loc_06e6:
    pea dat_00a8
    move.l a2,-(sp)
    jsr loc_0018
loc_06f2:
    addq.l #8,sp
    bra.s loc_0714
loc_06f6:
    pea dat_00a8
    move.l a2,-(sp)
    pea 140(a2)
    move.l d2,-(sp)
    jsr loc_071c
loc_0708:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_0714
loc_0710:
    move.l a2,d0
    bra.s loc_0716
loc_0714:
    moveq #0,d0
loc_0716:
    movem.l (sp)+,d2-d3/a2
    rts
loc_071c:
    movem.l d2/a2,-(sp)
    move.l 12(sp),d0
    movea.l 16(sp),a2
    move.l 20(sp),d2
    subq.w #1,(a2)
    bgt.s loc_0746
loc_0730:
    move.l a2,-(sp)
    move.l d0,-(sp)
    jsr loc_004e
loc_073a:
    tst.l d0
    addq.l #8,sp
    bne.s loc_0744
loc_0740:
    moveq #0,d0
    bra.s loc_0762
loc_0744:
    subq.w #1,(a2)
loc_0746:
    movea.l 10(a2),a1
    move.w (a2),d0
    ext.l d0
    asl.l #3,d0
    move.l d2,16(a1,d0.l)
    move.w (a2),d0
    ext.l d0
    asl.l #3,d0
    move.l 24(sp),20(a1,d0.l)
    moveq #1,d0
loc_0762:
    movem.l (sp)+,d2/a2
    rts
hint_0768:
; --- unverified ---
    movem.l d2-d4/a2,-(sp)
    move.l 20(sp),d2
    move.l 24(sp),d3
    move.l #$10000,-(sp)
    pea ($005e).w
    jsr loc_0000
hint_0784:
; --- unverified ---
    move.l d0,d4
    addq.l #8,sp
    beq.s hint_07e2
hint_078a:
; --- unverified ---
    move.l d4,d0
    moveq #78,d1
    add.l d1,d0
    movea.l d0,a2
    pea 2(a2)
    jsr loc_0000
hint_079c:
; --- unverified ---
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr loc_004e
hint_07a6:
; --- unverified ---
    tst.l d0
    lea 12(sp),sp
    beq.s hint_07e4
hint_07ae:
; --- unverified ---
    pea ($005e).w
    move.l d4,-(sp)
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr loc_071c(pc)
hint_07bc:
; --- unverified ---
    tst.l d0
    lea 16(sp),sp
    beq.s hint_07e4
hint_07c4:
; --- unverified ---
    move.l a2,-(sp)
    move.l d4,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr loc_0124(pc)
hint_07d0:
; --- unverified ---
    tst.l d0
    lea 16(sp),sp
    bne.s hint_07e2
hint_07d8:
; --- unverified ---
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr loc_0656(pc)
hint_07e0:
; --- unverified ---
    bra.s hint_07f0
hint_07e2:
; --- unverified ---
    bra.s hint_07f4
hint_07e4:
; --- unverified ---
    pea ($005e).w
    move.l d4,-(sp)
    jsr loc_0018
hint_07f0:
    dc.b    $78,$00,$50,$8f
hint_07f4:
; --- unverified ---
    move.l d4,d0
    movem.l (sp)+,d2-d4/a2
    rts
hint_07fc:
; --- unverified ---
    move.l d2,-(sp)
    move.l 8(sp),d2
    move.l 12(sp),d1
    moveq #78,d0
    add.l d0,d1
    move.l d1,-(sp)
    move.l d2,-(sp)
    jsr loc_0656(pc)
hint_0812:
; --- unverified ---
    addq.l #8,sp
    move.l (sp)+,d2
    rts
hint_0818:
; --- unverified ---
    movem.l d2-d4/a2-a3,-(sp)
    movea.l 24(sp),a2
    move.l 28(sp),d2
    move.l d2,-(sp)
    jsr loc_0000
hint_082c:
; --- unverified ---
    move.l d0,d3
    move.l a2,d4
    addq.l #4,sp
    beq.s hint_085c
hint_0834:
; --- unverified ---
    bra.s hint_0856
hint_0836:
; --- unverified ---
    move.l d3,-(sp)
    move.l d2,-(sp)
    move.l a3,-(sp)
    jsr dat_0048
hint_0842:
; --- unverified ---
    tst.l d0
    lea 12(sp),sp
    bne.s hint_0856
hint_084a:
; --- unverified ---
    adda.l d3,a3
    cmpi.b #$3d,(a3)+
    bne.s hint_0856
hint_0852:
; --- unverified ---
    move.l a3,d0
    bra.s hint_085e
hint_0856:
; --- unverified ---
    movea.l (a2)+,a3
    move.l a3,d0
    bne.s hint_0836
hint_085c:
    dc.b    $70,$00
hint_085e:
; --- unverified ---
    movem.l (sp)+,d2-d4/a2-a3
    rts
hint_0864:
; --- unverified ---
    movem.l d2-d5,-(sp)
    move.l 20(sp),d2
    move.l 24(sp),d3
    move.l d3,-(sp)
    jsr loc_0000
hint_0878:
; --- unverified ---
    move.l d0,d5
    addq.l #4,sp
    bra.s hint_08ca
hint_087e:
; --- unverified ---
    pea ($007c).w
    move.l d2,-(sp)
    jsr dat_0010
hint_088a:
; --- unverified ---
    move.l d0,d4
    addq.l #8,sp
    beq.s hint_0896
hint_0890:
; --- unverified ---
    move.l d4,d0
    sub.l d2,d0
    bra.s hint_08a0
hint_0896:
; --- unverified ---
    move.l d2,-(sp)
    jsr loc_0000
hint_089e:
    dc.b    $58,$8f
hint_08a0:
; --- unverified ---
    cmp.l d5,d0
    bne.s hint_08be
hint_08a4:
; --- unverified ---
    move.l d5,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr dat_0048
hint_08b0:
; --- unverified ---
    tst.l d0
    lea 12(sp),sp
    bne.s hint_08be
hint_08b8:
; --- unverified ---
    moveq #1,d2
    move.l d2,d0
    bra.s hint_08d0
hint_08be:
; --- unverified ---
    tst.l d4
    beq.s hint_08c8
hint_08c2:
; --- unverified ---
    move.l d4,d2
    addq.l #1,d2
    bra.s hint_08ca
hint_08c8:
    dc.b    $74,$00
hint_08ca:
; --- unverified ---
    tst.l d2
    bne.s hint_087e
hint_08ce:
    dc.b    $70,$00
hint_08d0:
; --- unverified ---
    movem.l (sp)+,d2-d5
    rts
hint_08d6:
; --- unverified ---
    movem.l d2-d4/a2-a4,-(sp)
    movea.l 28(sp),a2
    movea.l 32(sp),a3
    moveq #30,d4
    movea.l a3,a4
    clr.b 30(a2)
    pea ($0005).w
    pea dat_000c
    move.l a4,-(sp)
    jsr dat_0048
hint_08fc:
; --- unverified ---
    tst.l d0
    lea 12(sp),sp
    beq.s hint_0926
hint_0904:
; --- unverified ---
    pea dat_0012
    move.l a2,-(sp)
    jsr loc_002c
hint_0912:
; --- unverified ---
    move.l d4,-(sp)
    move.l a3,-(sp)
    move.l a2,-(sp)
    jsr dat_006c
hint_091e:
; --- unverified ---
    lea 20(sp),sp
    bra.w hint_09b6
hint_0926:
; --- unverified ---
    addq.l #5,a4
    pea ($0003).w
    pea loc_001c
    move.l a4,-(sp)
    jsr dat_0048
hint_093a:
; --- unverified ---
    tst.l d0
    lea 12(sp),sp
    bne.s hint_0948
hint_0942:
; --- unverified ---
    moveq #1,d3
    addq.l #3,a4
    bra.s hint_0992
hint_0948:
; --- unverified ---
    moveq #0,d3
    bra.s hint_095c
hint_094c:
    dc.b    $20,$03,$d0,$80,$22,$00,$e5,$80,$d0,$81,$d0,$82,$26,$00,$52,$8c
hint_095c:
; --- unverified ---
    move.b (a4),d0
    ext.w d0
    ext.l d0
    move.l d0,-(sp)
    jsr dat_09be
hint_096a:
; --- unverified ---
    move.l d0,d2
    addq.l #4,sp
    bge.s hint_094c
hint_0970:
; --- unverified ---
    tst.l d3
    beq.s hint_0904
hint_0974:
; --- unverified ---
    pea AbsExecBase
    pea dat_0020
    move.l a4,-(sp)
    jsr dat_0048
hint_0986:
; --- unverified ---
    tst.l d0
    lea 12(sp),sp
    bne.w hint_0904
hint_0990:
    dc.b    $58,$8c
hint_0992:
; --- unverified ---
    move.l d3,d0
    addq.l #1,d0
    move.l d0,-(sp)
    pea dat_0026
    move.l a2,-(sp)
    jsr dat_00c8
hint_09a6:
; --- unverified ---
    move.l d4,-(sp)
    move.l a4,-(sp)
    move.l a2,-(sp)
    jsr dat_006c
hint_09b2:
    dc.b    $4f,$ef,$00,$18
hint_09b6:
; --- unverified ---
    move.l a2,d0
    movem.l (sp)+,d2-d4/a2-a4
    rts
dat_09be:
; --- unverified ---
    move.l 4(sp),d1
    moveq #48,d0
    cmp.l d1,d0
    bgt.s hint_09d6
hint_09c8:
; --- unverified ---
    moveq #57,d0
    cmp.l d1,d0
    blt.s hint_09d6
hint_09ce:
; --- unverified ---
    move.l d1,d0
    moveq #48,d1
    sub.l d1,d0
    bra.s hint_09d8
hint_09d6:
    dc.b    $70,$ff
hint_09d8:
; --- unverified ---
    rts
    dc.b    $00,$00

; Hunk 5: 164 bytes, 0 entities, 3 blocks

    section code,code

loc_0000:
    movea.l 4(sp),a0
    moveq #-1,d0
loc_0006:
    tst.b (a0)+
    dbeq d0,loc_0006
loc_000c:
    not.l d0
    rts
hint_0010:
    dc.b    $20,$6f,$00,$04,$20,$2f,$00,$08
hint_0018:
; --- unverified ---
    move.b (a0)+,d1
    beq.s hint_0026
hint_001c:
; --- unverified ---
    cmp.b d0,d1
    bne.s hint_0018
hint_0020:
    dc.b    $53,$88,$20,$08
hint_0024:
; --- unverified ---
    rts
hint_0026:
; --- unverified ---
    moveq #0,d0
    bra.s hint_0024
hint_002a:
    dc.b    $00,$00,$4c,$ef,$03,$00,$00,$04
hint_0032:
    dc.b    $10,$d9
hint_0036:
; --- unverified ---
    rts
hint_0038:
    dc.b    $4c,$ef,$03,$00,$00,$04
hint_003e:
; --- unverified ---
    tst.b (a0)+
    bne.s hint_003e
hint_0042:
; --- unverified ---
    subq.l #1,a0
    bra.s hint_0032
hint_0046:
    dc.b    $00,$00,$4c,$ef,$03,$00,$00,$04,$20,$2f,$00,$0c,$53,$80,$6d,$0a
hint_0056:
; --- unverified ---
    move.b (a1)+,d1
    cmp.b (a0)+,d1
    bne.s hint_0064
hint_005c:
; --- unverified ---
    tst.b d1
    bne.s $52
hint_0060:
    dc.b    $70,$00
hint_0062:
; --- unverified ---
    rts
hint_0064:
; --- unverified ---
    moveq #1,d0
    bgt.s hint_0062
hint_0068:
; --- unverified ---
    moveq #-1,d0
    rts
hint_006c:
    dc.b    $4c,$ef,$03,$00,$00,$04,$20,$2f,$00,$0c
hint_0076:
; --- unverified ---
    tst.b (a0)+
    beq.s hint_0080
hint_007a:
; --- unverified ---
    subq.l #1,d0
    bgt.s hint_0076
hint_007e:
; --- unverified ---
    bra.s hint_0086
hint_0080:
; --- unverified ---
    subq.l #1,a0
    bsr.w hint_0092
hint_0086:
; --- unverified ---
    rts
hint_0088:
    dc.b    $4c,$ef,$03,$00,$00,$04,$20,$2f,$00,$0c
hint_0092:
; --- unverified ---
    subq.l #1,d0
    blt.s hint_00a2
hint_0096:
; --- unverified ---
    move.b (a1)+,(a0)+
    bne.s hint_0092
hint_009a:
; --- unverified ---
    subq.l #1,d0
    ble.s hint_00a2
hint_009e:
; --- unverified ---
    clr.b (a0)+
    bra.s hint_009a
hint_00a2:
; --- unverified ---
    rts

; Hunk 6: 240 bytes, 0 entities, 7 blocks

    section code,code

loc_0000:
    cmpi.l #$ffff,d2
    bgt.s loc_0020
loc_0008:
    movea.w d1,a1
    clr.w d1
    swap d1
    divu.w d2,d1
    move.l d1,d0
    swap d1
    move.w a1,d0
    divu.w d2,d0
    move.w d0,d1
    clr.w d0
    swap d0
    rts
loc_0020:
    move.l d1,d0
    clr.w d0
    swap d0
    swap d1
    clr.w d1
    movea.l d2,a1
    moveq #15,d2
loc_002e:
    add.l d1,d1
    addx.l d0,d0
    cmpa.l d0,a1
    bgt.s loc_003a
loc_0036:
    sub.l a1,d0
    addq.w #1,d1
loc_003a:
    dbf d2,loc_002e
loc_003e:
    rts
hint_0040:
; --- unverified ---
    move.l d2,-(sp)
    move.l d0,d2
    mulu.w d1,d2
    movea.l d2,a0
    move.l d0,d2
    swap d2
    mulu.w d1,d2
    swap d1
    mulu.w d1,d0
    add.l d2,d0
    swap d0
    clr.w d0
    adda.l d0,a0
    move.l a0,d0
    move.l (sp)+,d2
    rts
hint_0060:
; --- unverified ---
    move.l d2,-(sp)
    move.l d1,d2
    move.l d0,d1
    bsr.s loc_0000
hint_0068:
; --- unverified ---
    move.l (sp)+,d2
    rts
hint_006c:
; --- unverified ---
    move.l d2,-(sp)
    move.l d1,d2
    move.l d0,d1
    bsr.s loc_0000
hint_0074:
; --- unverified ---
    move.l d1,d0
    move.l (sp)+,d2
    rts
hint_007a:
; --- unverified ---
    move.l d2,-(sp)
    move.l d1,d2
    bge.s hint_0082
hint_0080:
    dc.b    $44,$82
hint_0082:
; --- unverified ---
    move.l d0,d1
    moveq #0,d0
    tst.l d1
    bge.s hint_008e
hint_008a:
    dc.b    $44,$81,$46,$80
hint_008e:
; --- unverified ---
    movea.l d0,a0
    bsr.w loc_0000
hint_0094:
; --- unverified ---
    move.w a0,d2
    beq.s hint_009a
hint_0098:
    dc.b    $44,$80
hint_009a:
; --- unverified ---
    move.l (sp)+,d2
    rts
hint_009e:
; --- unverified ---
    move.l d2,-(sp)
    movea.l d0,a0
    moveq #0,d0
    move.l d1,d2
    bge.s hint_00ac
hint_00a8:
    dc.b    $44,$82,$46,$80
hint_00ac:
; --- unverified ---
    move.l a0,d1
    bge.s hint_00b4
hint_00b0:
    dc.b    $44,$81,$46,$80
hint_00b4:
; --- unverified ---
    movea.l d0,a0
    bsr.w loc_0000
hint_00ba:
; --- unverified ---
    move.l a0,d2
    beq.s hint_00c0
hint_00be:
    dc.b    $44,$81
hint_00c0:
; --- unverified ---
    move.l d1,d0
    move.l (sp)+,d2
    rts
hint_00c6:
    dc.b    $00,$00,$48,$e7,$00,$3a,$26,$6f,$00,$14,$20,$6f,$00,$18,$43,$ef
    dc.b    $00,$1c,$45,$fa,$00,$12,$2c,$79,$00,$00,$00,$04,$4e,$ae,$fd,$f6
hint_00e6:
; --- unverified ---
    movem.l (sp)+,a2-a4/a6
    rts
pcref_00ec:
; --- unverified ---
    move.b d0,(a3)+
    rts

; Hunk 7: 20 bytes, 0 entities, 1 blocks

    section code,code

loc_0000:
    movea.l 4(sp),a0
    move.l a0,(a0)
    addq.l #4,(a0)
    clr.l 4(a0)
    move.l a0,8(a0)
    rts
    dc.b    $00,$00

; Hunk 8: 104 bytes, 0 entities, 2 blocks

    section code,code

loc_0000:
    movem.l d2/a6,-(sp)
    movea.l dat_0196,a6
    movem.l 12(sp),d1-d2
    jsr -30(a6) ; unresolved_indirect_core:disp
loc_0014:
    movem.l (sp)+,d2/a6
    rts
hint_001a:
    dc.b    $00,$00,$2f,$0e,$2c,$79
    dc.l    dat_0196
    dc.b    $22,$2f,$00,$08,$4e,$ae,$ff,$dc
hint_002c:
; --- unverified ---
    movea.l (sp)+,a6
    rts
hint_0030:
; --- unverified ---
    movem.l d2-d3/a6,-(sp)
    movea.l dat_0196,a6
    movem.l 16(sp),d1-d3
    jsr -42(a6) ; unresolved_indirect_hint:disp
hint_0044:
; --- unverified ---
    movem.l (sp)+,d2-d3/a6
    rts
hint_004a:
    dc.b    $00,$00,$48,$e7,$30,$02,$2c,$79
    dc.l    dat_0196
    dc.b    $4c,$ef,$00,$0e,$00,$10,$4e,$ae,$ff,$d0
hint_0060:
; --- unverified ---
    movem.l (sp)+,d2-d3/a6
    rts
    dc.b    $00,$00

; Hunk 9: 112 bytes, 1 entities, 2 blocks

    section code,code

loc_0000:
    move.l a6,-(sp)
    movea.l dat_0192,a6
    movem.l 8(sp),d0-d1
    jsr -198(a6) ; unresolved_indirect_core:disp
loc_0012:
    movea.l (sp)+,a6
    rts
hint_0016:
    dc.b    $00,$00,$2f,$0e,$2c,$79
    dc.l    dat_0192
    dc.b    $22,$6f,$00,$08,$20,$2f,$00,$0c,$4e,$ae,$ff,$2e
hint_002c:
; --- unverified ---
    movea.l (sp)+,a6
    rts
hint_0030:
; --- unverified ---
    move.l a6,-(sp)
    movea.l dat_0192,a6
    movea.l 8(sp),a0
    jsr -228(a6) ; unresolved_indirect_hint:disp
hint_0040:
; --- unverified ---
    movea.l (sp)+,a6
    rts
hint_0044:
; --- unverified ---
    move.l a6,-(sp)
    movea.l dat_0192,a6
    movem.l 8(sp),a0-a1
    jsr -246(a6) ; unresolved_indirect_hint:disp
hint_0056:
; --- unverified ---
    movea.l (sp)+,a6
    rts
hint_005a:
    dc.b    $00,$00,$2f,$0e,$2c,$79
    dc.l    dat_0192
    dc.b    $20,$6f,$00,$08,$4e,$ae,$fe,$f8
hint_006c:
; --- unverified ---
    movea.l (sp)+,a6
    rts
