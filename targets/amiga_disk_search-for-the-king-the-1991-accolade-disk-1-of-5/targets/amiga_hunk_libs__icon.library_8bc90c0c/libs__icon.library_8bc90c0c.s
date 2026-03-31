; Generated disassembly -- vasm Motorola syntax
; Source: bin\Search for the King, The (1991)(Accolade)(Disk 1 of 5).adf::libs\icon.library
; 4732 bytes, 56 entities, 431 blocks
; OS compatibility floor: 1.3

; LVO offsets: icon.library (FD-derived)
_LVOiconPrivate4	EQU	-48
_LVOiconPrivate3	EQU	-42
_LVOiconPrivate2	EQU	-36
_LVOiconPrivate1	EQU	-30

; Target-local struct fields
exec_library_base	EQU	34
field_002a	EQU	42
icon_library_base	EQU	38

; Absolute symbols
AbsExecBase	EQU	$4

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/initializers.i"
    INCLUDE "exec/libraries.i"
    INCLUDE "exec/nodes.i"

; Resident structure
;   matchword: 0x4AFC
;   version: 34, type: library, priority: 70
;   flags: 0x80, auto-init: True
;   name: icon.library
;   id string: icon 34.2 (22 Jun 1988)

;   init offset: 0x48

; Library structure
;   name: icon.library
;   version: 34
;   id string: icon 34.2 (22 Jun 1988)

;   public functions: 12
;   total LVOs: 19
;   exports: BumpRevision, MatchToolValue, FindToolType, FreeDiskObject, PutDiskObject, GetDiskObject, AddFreeList, FreeFreeList

; Hunk 0: 644 bytes, 48 entities, 47 blocks

    section code,code

word_0000:
    dc.w    $70ff
    dc.b    $4e,$75
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
; entry registers: A6=icon.library base
lib_open:
    addq.w #1,LIB_OPENCNT(a6)
    bclr #3,LIB_FLAGS(a6)
    move.l a6,d0
    rts
; entry registers: A6=icon.library base
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
; entry registers: A6=icon.library base
lib_expunge:
    tst.w LIB_OPENCNT(a6)
    bne.s loc_013a
loc_0106:
    move.l field_002a(a6),-(sp)
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
hunk_0_loc_0124:
    move.w LIB_POSSIZE(a6),d1
    add.l d1,d0 ; FreeMem: byteSize
    move.l a6,-(sp)
    movea.l exec_library_base(a6),a6
    jsr _LVOFreeMem(a6)
loc_0134:
    movea.l (sp)+,a6
    move.l (sp)+,d0
    bra.s loc_0142
loc_013a:
    bset #3,LIB_FLAGS(a6)
    moveq #0,d0
loc_0142:
    rts
; entry registers: A6=icon.library base
lib_extfunc:
    moveq #0,d0
    rts
; entry registers: A6=ExecBase, D0=icon.library base
library_init:
    move.l a2,-(sp)
    movea.l d0,a2
    move.l a0,field_002a(a2)
    move.l a6,exec_library_base(a2)
    lea str_00d0(pc),a1 ; OldOpenLibrary: libName
    jsr _LVOOldOpenLibrary(a6)
loc_015c:
    move.l d0,icon_library_base(a2)
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
    move.l exec_library_base(a2),long_0192
    move.l icon_library_base(a2),long_0196
    move.l a2,d0
loc_018e:
    movea.l (sp)+,a2
    rts
long_0192:
    dc.l    0 ; InferredIconLibraryBase.exec_library_base
long_0196:
    dc.l    0 ; InferredIconLibraryBase.icon_library_base
; entry registers: A6=icon.library base
icon_private_1:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr hunk_3_loc_0000
hunk_0_loc_01a4:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base
icon_private_2:
    movem.l a0-a1,-(sp)
    move.l a6,-(sp)
    jsr hunk_3_loc_00a8
loc_01b4:
    lea 12(sp),sp
    rts
; entry registers: A6=icon.library base
icon_private_3:
    movem.l a0-a2,-(sp)
    move.l a6,-(sp)
    jsr hunk_3_loc_0124
loc_01c6:
    lea 16(sp),sp
    rts
; entry registers: A6=icon.library base, A1=DiskObject *
put_disk_object:
    movem.l a0-a1,-(sp)
    move.l a6,-(sp)
    jsr loc_03fe
loc_01d8:
    lea 12(sp),sp
    rts
; entry registers: A6=icon.library base, A0=FreeList *
free_free_list:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr sub_0656
loc_01e8:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base
icon_private_5:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr sub_0692
loc_01f6:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base
icon_private_6:
    move.l a6,-(sp)
    jsr sub_06a8
loc_0202:
    addq.l #4,sp
    rts
; entry registers: A6=icon.library base, A0=FreeList *
add_free_list:
    movem.l a0-a2,-(sp)
    move.l a6,-(sp)
    jsr sub_071c
loc_0212:
    lea 16(sp),sp
    rts
; entry registers: A6=icon.library base
get_disk_object:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr loc_0768
loc_0222:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base, A0=DiskObject *
free_disk_object:
    move.l a0,-(sp)
    move.l a6,-(sp)
    jsr loc_07fc
hunk_0_loc_0230:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base
find_tool_type:
    movem.l a0-a1,-(sp)
    jsr loc_0818
loc_023e:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base
match_tool_value:
    movem.l a0-a1,-(sp)
    jsr loc_0864
loc_024c:
    addq.l #8,sp
    rts
; entry registers: A6=icon.library base
bump_revision:
    movem.l a0-a1,-(sp)
    jsr loc_08d6
loc_025a:
    addq.l #8,sp
    rts
    dc.b    $00,$00
hunk_0_loc_0260:
    move.l a6,-(sp)
    movea.l 8(sp),a6
    suba.l a1,a1
    move.l a6,-(sp)
    movea.l 34(a6),a6
    jsr -294(a6) ; unresolved_indirect_core:disp
loc_0272:
    movea.l (sp)+,a6
    movea.l d0,a1
    move.l 12(sp),148(a1)
    movea.l (sp)+,a6
    rts
dat_0280:
    dcb.b   4,0

; Hunk 1: 232 bytes, 0 entities, 26 blocks

    section code,code

hunk_1_loc_0000:
    movem.l d2-d5,-(sp)
    move.l 20(sp),d3
    move.l 24(sp),d4
    move.l 28(sp),d2
    move.l 32(sp),-(sp)
    move.l d2,-(sp)
    jsr hunk_9_loc_0000
hunk_1_loc_001c:
    move.l d0,d5
    addq.l #8,sp
    beq.s hunk_1_loc_0046
hunk_1_loc_0022:
    move.l d2,-(sp)
    move.l d5,-(sp)
    move.l d4,-(sp)
    move.l d3,-(sp)
    jsr sub_071c
hunk_1_loc_0030:
    tst.l d0
    lea 16(sp),sp
    bne.s hunk_1_loc_0046
hunk_1_loc_0038:
    move.l d2,-(sp)
    move.l d5,-(sp)
    jsr hunk_9_loc_0018
hunk_1_loc_0042:
    moveq #0,d5
hunk_1_loc_0044:
    addq.l #8,sp
hunk_1_loc_0046:
    move.l d5,d0
    movem.l (sp)+,d2-d5
hunk_1_loc_004c:
    rts
hunk_1_loc_004e:
    movem.l d2/a2,-(sp)
    movea.l 16(sp),a2
    move.l #$10000,-(sp)
    pea $60
    jsr hunk_9_loc_0000
loc_0066:
    movea.l d0,a0
    move.l a0,d2
    addq.l #8,sp
    beq.s loc_008a
loc_006e:
    move.w #$a,14(a0)
    move.w #$a,(a2)
    move.l a0,-(sp)
    pea 2(a2)
    jsr hunk_9_loc_0044
loc_0084:
    moveq #1,d0
    addq.l #8,sp
    bra.s hunk_1_loc_008c
loc_008a:
    moveq #0,d0
hunk_1_loc_008c:
    movem.l (sp)+,d2/a2
    rts
hunk_1_loc_0092:
    move.l 8(sp),d0
    move.l 12(sp),d1
    move.l 16(sp),-(sp)
    move.l d1,-(sp)
    move.l d0,-(sp)
    jsr hunk_8_loc_0030
hunk_1_loc_00a8:
    move.l d0,d1
    cmp.l 28(sp),d0
    lea 12(sp),sp
    beq.s loc_00b8
loc_00b4:
    moveq #0,d0
    bra.s loc_00ba
loc_00b8:
    move.l d1,d0
loc_00ba:
    rts
hunk_1_loc_00bc:
    move.l 8(sp),d0
    move.l 12(sp),d1
    move.l 16(sp),-(sp)
    move.l d1,-(sp)
    move.l d0,-(sp)
    jsr hunk_8_loc_004c
hunk_1_loc_00d2:
    move.l d0,d1
    cmp.l 28(sp),d0
    lea 12(sp),sp
    beq.s loc_00e2
loc_00de:
    moveq #0,d0
    bra.s loc_00e4
loc_00e2:
    move.l d1,d0
loc_00e4:
    rts
    dc.b    $00,$00

; Hunk 2: 640 bytes, 0 entities, 50 blocks

    section code,code

hunk_2_loc_0000:
    movem.l d2-d3/a2,-(sp)
    move.l 16(sp),d2
    move.l 20(sp),d3
    movea.l 24(sp),a2
    moveq #1,d0
    move.l a2,d1
    beq.s loc_0074
loc_0016:
    pea $14
    move.l a2,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_00bc
hunk_2_loc_0026:
    move.l d0,d0
    lea 16(sp),sp
    beq.s loc_0074
hunk_2_loc_002e:
    move.w 4(a2),d1
    ext.l d1
    moveq #15,d0
    add.l d0,d1
    asr.l #3,d1
    andi.l #$fffe,d1
hunk_2_loc_0040:
    move.w 6(a2),d0
    ext.l d0
    jsr hunk_6_loc_0040
hunk_2_loc_004c:
    move.l d0,d1
    move.w 8(a2),d0
    ext.l d0
    jsr hunk_6_loc_0040
hunk_2_loc_005a:
    move.l d0,-(sp)
    move.l 10(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_00bc
loc_006a:
    move.l d0,d0
    lea 16(sp),sp
    beq.w loc_0074
loc_0074:
    movem.l (sp)+,d2-d3/a2
    rts
hunk_2_loc_007a:
    movem.l d2-d3/a2,-(sp)
    move.l 16(sp),d2
    move.l 20(sp),d3
    movea.l 24(sp),a2
    bra.s loc_00cc
hunk_2_loc_008c:
    pea $10
    move.l a2,-(sp)
hunk_2_loc_0092:
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_00bc
hunk_2_loc_009c:
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
    jsr hunk_1_loc_00bc
loc_00c0:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_00d4
hunk_2_loc_00c8:
    movea.l 12(a2),a2
loc_00cc:
    move.l a2,d0
    bne.s hunk_2_loc_008c
loc_00d0:
    moveq #1,d0
    bra.s loc_00d6
loc_00d4:
    moveq #0,d0
loc_00d6:
    movem.l (sp)+,d2-d3/a2
    rts
loc_00dc:
    movem.l d2-d5/a2,-(sp)
    move.l 24(sp),d2
    move.l 28(sp),d3
    move.l 32(sp),d4
    tst.l 36(sp)
    beq.w hunk_2_loc_019e
loc_00f4:
    move.l #$10000,-(sp)
    pea $14
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0000
loc_0108:
    move.l d0,52(sp)
    lea 16(sp),sp
    beq.w hunk_2_loc_01a4
loc_0114:
    pea $14
    move.l 40(sp),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0092
loc_0126:
    tst.l d0
    lea 16(sp),sp
    beq.w hunk_2_loc_01a4
loc_0130:
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
    jsr hunk_6_loc_0040
hunk_2_loc_0154:
    move.l d0,d5
    movea.l 36(sp),a2
    move.l d5,d1
    move.w 8(a2),d0
    ext.l d0
    jsr hunk_6_loc_0040
loc_0168:
    move.l d0,d5
    movea.l 36(sp),a2
    pea $2
    move.l d5,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0000
loc_017e:
    move.l d0,10(a2)
    move.l d5,-(sp)
    movea.l 56(sp),a2
    move.l 10(a2),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0092
hunk_2_loc_0196:
    tst.l d0
    lea 32(sp),sp
    beq.s hunk_2_loc_01a4
hunk_2_loc_019e:
    move.l 36(sp),d0
    bra.s loc_01a6
hunk_2_loc_01a4:
    moveq #-1,d0
loc_01a6:
    movem.l (sp)+,d2-d5/a2
    rts
hunk_2_loc_01ac:
    movem.l d2-d6/a2,-(sp)
    move.l 28(sp),d2
    move.l 32(sp),d3
    move.l 36(sp),d4
    moveq #0,d6
    bra.w loc_026c
loc_01c2:
    move.l #$10000,-(sp)
    pea $10
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0000
loc_01d6:
    move.l d0,56(sp)
    lea 16(sp),sp
    beq.w loc_0278
loc_01e2:
    tst.l d6
    bne.s loc_01ec
loc_01e6:
    move.l 40(sp),d6
    bra.s loc_01f2
loc_01ec:
    move.l 40(sp),12(a2)
loc_01f2:
    pea $10
    move.l 44(sp),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0092
hunk_2_loc_0204:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_0278
loc_020c:
    movea.l 40(sp),a0
    move.b 7(a0),d5
    ext.w d5
    ext.l d5
    add.l d5,d5
    add.l d5,d5
    movea.l 40(sp),a2
    pea $2
    move.l d5,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0000
hunk_2_loc_0230:
    move.l d0,8(a2)
    movea.l 56(sp),a0
    tst.l 8(a0)
    lea 16(sp),sp
    beq.s loc_0278
loc_0242:
    move.l d5,-(sp)
    movea.l 44(sp),a2
    move.l 8(a2),-(sp)
    move.l d4,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0092
loc_0256:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_0278
loc_025e:
    movea.l 40(sp),a2
    movea.l 40(sp),a0
    move.l 12(a0),40(sp)
loc_026c:
    tst.l 40(sp)
    bne.w loc_01c2
loc_0274:
    move.l d6,d0
    bra.s loc_027a
loc_0278:
    moveq #-1,d0
loc_027a:
    movem.l (sp)+,d2-d6/a2
    rts

; Hunk 3: 2524 bytes, 7 entities, 245 blocks

    section code,code

hunk_3_loc_0000:
    link a6,#-80
    movem.l d2-d4/a2,-(sp)
    move.l 8(a6),d2
    move.l 12(a6),d3
hunk_3_loc_0010:
    move.l d2,-(sp)
    jsr sub_06a8
hunk_3_loc_0018:
    movea.l d0,a2
    move.l a2,d4
hunk_3_loc_001c:
    addq.l #4,sp
    beq.w hunk_3_loc_009c
hunk_3_loc_0022:
    pea 140(a2)
    pea -80(a6)
    move.l d3,-(sp)
hunk_3_loc_002c:
    move.l d2,-(sp)
    jsr hunk_3_loc_0124
loc_0034:
    tst.l d0
    lea 16(sp),sp
    bne.s loc_004a
loc_003c:
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr sub_0692
hunk_3_loc_0046:
    addq.l #8,sp
hunk_3_loc_0048:
    bra.s hunk_3_loc_009c
loc_004a:
    lea -76(a6),a0
hunk_3_loc_004e:
    lea 96(a2),a1
    moveq #10,d0
loc_0054:
    move.l (a0)+,(a1)+
    dbf d0,loc_0054
hunk_3_loc_005a:
    move.b -32(a6),61(a2)
    move.l -30(a6),72(a2)
    move.l -26(a6),92(a2)
hunk_3_loc_006c:
    move.l -22(a6),84(a2)
    move.l -18(a6),88(a2)
    move.l -14(a6),76(a2)
    move.l -10(a6),156(a2)
    move.l -6(a6),160(a2)
    tst.l 76(a2)
    beq.s loc_0098
loc_0090:
    movea.l 76(a2),a0
    dc.b    $21,$4a,$01,$a8
loc_0098:
    move.l a2,d0
    bra.s hunk_3_loc_009e
hunk_3_loc_009c:
    moveq #0,d0
hunk_3_loc_009e:
    movem.l -96(a6),d2-d4/a2
    unlk a6
    rts
hunk_3_loc_00a8:
    link a6,#-80
    movem.l d2/a2,-(sp)
    move.l 8(a6),d1
    move.l 12(a6),d2
    movea.l 16(a6),a0
hunk_3_loc_00bc:
    move.w #$e310,-80(a6)
    move.w #$1,-78(a6)
hunk_3_loc_00c8:
    lea 96(a0),a1
    lea -76(a6),a2
    moveq #10,d0
hunk_3_loc_00d2:
    move.l (a1)+,(a2)+
    dbf d0,hunk_3_loc_00d2
loc_00d8:
    move.l 92(a0),-26(a6)
    move.b 61(a0),-32(a6)
    move.l 84(a0),-22(a6)
    move.l 88(a0),-18(a6)
    move.l 76(a0),-14(a6)
    move.l 72(a0),-30(a6)
    move.l 156(a0),-10(a6)
    move.l 160(a0),-6(a6)
    pea -80(a6)
    move.l d2,-(sp)
    move.l d1,-(sp)
    jsr loc_03fe
loc_0116:
    lea 12(sp),sp
    movem.l -88(a6),d2/a2
    unlk a6
    rts
hunk_3_loc_0124:
    link a6,#-268
    movem.l d2-d5/a2-a5,-(sp)
    move.l 8(a6),d2
    move.l 12(a6),d0
    movea.l 16(a6),a2
    movea.l #hunk_1_loc_0092,a3
    move.l #hunk_1_loc_0000,d3
    lea 4(a2),a4
    move.l d0,-(sp)
    pea -268(a6)
    jsr hunk_5_loc_002c
hunk_3_loc_0154:
    pea dat_0000
    pea -268(a6)
    jsr hunk_5_loc_0038
loc_0164:
    pea $000003ed
    pea -268(a6)
    jsr hunk_8_loc_0000
loc_0172:
    move.l d0,d5
    lea 24(sp),sp
    bne.s loc_0180
loc_017a:
    moveq #0,d4
    bra.w loc_03f2
loc_0180:
    pea hunk_3_loc_004e
    move.l a2,-(sp)
    move.l d5,-(sp)
    move.l d2,-(sp)
    jsr (a3)
loc_018c:
    tst.l d0
    lea 16(sp),sp
    beq.w loc_03ee
hunk_3_loc_0196:
    cmpi.w #$e310,(a2)
    bne.w loc_03ee
hunk_3_loc_019e:
    cmpi.w #$1,2(a2)
    bne.w loc_03ee
loc_01a8:
    clr.l (a4)
    clr.l (a4)
hunk_3_loc_01ac:
    tst.l 66(a2)
    beq.s loc_01fc
loc_01b2:
    move.l #$10002,-(sp)
    pea $000001be
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_0000
loc_01c8:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_03ee
loc_01d2:
    pea $38
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
    jsr hunk_7_loc_0000
loc_01fa:
    addq.l #4,sp
loc_01fc:
    btst #2,13(a4)
    beq.s loc_024a
hunk_3_loc_0204:
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
    jsr hunk_2_loc_01ac
loc_025c:
    move.l d0,d4
    moveq #-1,d0
hunk_3_loc_0260:
    cmp.l d4,d0
    lea 16(sp),sp
    beq.w loc_03ee
loc_026a:
    move.l d4,18(a4)
    move.l 22(a4),-(sp)
    move.l d5,-(sp)
    move.l 20(a6),-(sp)
    move.l d2,-(sp)
    jsr hunk_2_loc_01ac
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
    jsr hunk_1_loc_0000
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
    jsr hunk_1_loc_0000
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
    jsr hunk_1_loc_0000
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
    jsr hunk_1_loc_0000
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
    jsr hunk_8_loc_001c
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
loc_03fe:
    link a6,#-4
    movem.l d2-d6/a2-a4,-(sp)
    move.l 8(a6),d2
    move.l 12(a6),d3
    movea.l 16(a6),a2
    moveq #0,d4
    movea.l #hunk_1_loc_00bc,a4
    clr.l -(sp)
    pea $00000104
    jsr hunk_9_loc_0000
loc_0426:
    move.l d0,d5
    addq.l #8,sp
    bne.s loc_043e
loc_042c:
    pea $67
    move.l d2,-(sp)
    jsr hunk_0_loc_0260
loc_0438:
    moveq #0,d4
    bra.w loc_0648
loc_043e:
    move.l 26(a2),d6
    move.l d3,-(sp)
    move.l d5,-(sp)
    jsr hunk_5_loc_002c
loc_044c:
    pea dat_0006
    move.l d5,-(sp)
    jsr hunk_5_loc_0038
loc_045a:
    pea loc_03ee
    move.l d5,-(sp)
    jsr hunk_8_loc_0000
loc_0466:
    move.l d0,d3
    lea 24(sp),sp
    beq.w loc_0638
loc_0470:
    moveq #0,d1
    move.w 16(a2),d1
    moveq #3,d0
    and.l d0,d1
    moveq #1,d0
    cmp.l d1,d0
    bne.s loc_0484
loc_0480:
    clr.l 26(a2)
loc_0484:
    pea hunk_3_loc_004e
    move.l a2,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_0490:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_0638
loc_049a:
    tst.l 66(a2)
    beq.s loc_04b8
loc_04a0:
    pea $38
    move.l 66(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_04ae:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_0638
loc_04b8:
    btst #2,17(a2)
    beq.s loc_04f2
loc_04c0:
    move.l 22(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_2_loc_0000
loc_04ce:
    move.l d0,d4
    lea 12(sp),sp
    beq.w loc_062e
loc_04d8:
    move.l 26(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_2_loc_0000
loc_04e6:
    move.l d0,d4
    lea 12(sp),sp
    bne.s loc_0522
loc_04ee:
    bra.w loc_062e
loc_04f2:
    move.l 22(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_2_loc_007a
loc_0500:
    move.l d0,d4
    lea 12(sp),sp
    beq.w loc_062e
loc_050a:
    move.l 26(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_2_loc_007a
loc_0518:
    move.l d0,d4
    lea 12(sp),sp
    beq.w loc_062e
loc_0522:
    tst.l 30(a2)
    bne.w loc_052a
loc_052a:
    tst.l 50(a2)
    beq.s loc_0570
loc_0530:
    move.l 50(a2),-(sp)
    jsr hunk_5_loc_0000
loc_053a:
    addq.l #1,d0
    move.l d0,-4(a6)
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_054e:
    move.l d0,d4
    lea 20(sp),sp
    beq.w loc_062e
loc_0558:
    move.l -4(a6),-(sp)
    move.l 50(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_0566:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_062e
loc_0570:
    tst.l 54(a2)
    beq.w loc_05ea
loc_0578:
    movea.l 54(a2),a3
    moveq #4,d1
    move.l d1,-4(a6)
    bra.s loc_058a
loc_0584:
    addq.l #4,a3
    addq.l #4,-4(a6)
loc_058a:
    tst.l (a3)
    bne.s loc_0584
loc_058e:
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_059c:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_062e
loc_05a6:
    movea.l 54(a2),a3
    bra.s loc_05e6
loc_05ac:
    move.l (a3),-(sp)
    jsr hunk_5_loc_0000
loc_05b4:
    addq.l #1,d0
    move.l d0,-4(a6)
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_05c8:
    move.l d0,d4
    lea 20(sp),sp
    beq.s loc_062e
loc_05d0:
    move.l -4(a6),-(sp)
    move.l (a3),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_05dc:
    move.l d0,d4
    lea 16(sp),sp
    beq.s loc_062e
loc_05e4:
    addq.l #4,a3
loc_05e6:
    tst.l (a3)
    bne.s loc_05ac
loc_05ea:
    tst.l 70(a2)
    beq.s loc_062e
loc_05f0:
    move.l 70(a2),-(sp)
    jsr hunk_5_loc_0000
loc_05fa:
    addq.l #1,d0
    move.l d0,-4(a6)
    pea AbsExecBase
    pea -4(a6)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_060e:
    move.l d0,d4
    lea 20(sp),sp
    beq.s loc_062e
loc_0616:
    move.l -4(a6),-(sp)
    move.l 70(a2),-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr (a4)
loc_0624:
    move.l d0,d4
    lea 16(sp),sp
    beq.w loc_062e
loc_062e:
    move.l d3,-(sp)
    jsr hunk_8_loc_001c
loc_0636:
    addq.l #4,sp
loc_0638:
    pea $00000104
    move.l d5,-(sp)
    jsr hunk_9_loc_0018
loc_0644:
    move.l d6,26(a2)
loc_0648:
    addq.l #8,sp
    move.l d4,d0
    movem.l -36(a6),d2-d6/a2-a4
    unlk a6
    rts
sub_0656:
    move.l a2,-(sp)
    movea.l 12(sp),a0
    lea 2(a0),a2
    bra.s loc_066c
loc_0662:
    move.l d0,-(sp)
    jsr hunk_9_loc_0030
loc_066a:
    addq.l #4,sp
loc_066c:
    move.l a2,-(sp)
    jsr hunk_9_loc_005c
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
    jsr hunk_9_loc_0030
loc_068c:
    addq.l #4,sp
loc_068e:
    movea.l (sp)+,a2
    rts
sub_0692:
    move.l 4(sp),d0
    movea.l 8(sp),a0
    pea 140(a0)
    move.l d0,-(sp)
    jsr sub_0656(pc)
loc_06a4:
    addq.l #8,sp
    rts
sub_06a8:
    movem.l d2-d3/a2,-(sp)
    move.l 16(sp),d2
    move.l #$10000,-(sp)
    pea hunk_3_loc_00a8
    jsr hunk_9_loc_0000
loc_06c0:
    movea.l d0,a2
    move.l a2,d3
    addq.l #8,sp
    beq.s loc_0714
loc_06c8:
    pea 142(a2)
    jsr hunk_7_loc_0000
loc_06d2:
    pea 140(a2)
    move.l d2,-(sp)
    jsr hunk_1_loc_004e
loc_06de:
    tst.l d0
    lea 12(sp),sp
    bne.s loc_06f6
loc_06e6:
    pea hunk_3_loc_00a8
    move.l a2,-(sp)
    jsr hunk_9_loc_0018
loc_06f2:
    addq.l #8,sp
    bra.s loc_0714
loc_06f6:
    pea hunk_3_loc_00a8
    move.l a2,-(sp)
    pea 140(a2)
    move.l d2,-(sp)
    jsr sub_071c
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
sub_071c:
    movem.l d2/a2,-(sp)
    move.l 12(sp),d0
    movea.l 16(sp),a2
    move.l 20(sp),d2
    subq.w #1,(a2)
    bgt.s loc_0746
loc_0730:
    move.l a2,-(sp)
    move.l d0,-(sp)
    jsr hunk_1_loc_004e
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
loc_0768:
    movem.l d2-d4/a2,-(sp)
    move.l 20(sp),d2
    move.l 24(sp),d3
    move.l #$10000,-(sp)
    pea $5e
    jsr hunk_9_loc_0000
loc_0784:
    move.l d0,d4
    addq.l #8,sp
    beq.s loc_07e2
loc_078a:
    move.l d4,d0
    moveq #78,d1
    add.l d1,d0
    movea.l d0,a2
    pea 2(a2)
    jsr hunk_7_loc_0000
loc_079c:
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr hunk_1_loc_004e
loc_07a6:
    tst.l d0
    lea 12(sp),sp
    beq.s loc_07e4
loc_07ae:
    pea $5e
    move.l d4,-(sp)
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr sub_071c(pc)
loc_07bc:
    tst.l d0
    lea 16(sp),sp
    beq.s loc_07e4
loc_07c4:
    move.l a2,-(sp)
    move.l d4,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_3_loc_0124(pc)
loc_07d0:
    tst.l d0
    lea 16(sp),sp
    bne.s loc_07e2
loc_07d8:
    move.l a2,-(sp)
    move.l d2,-(sp)
    jsr sub_0656(pc)
loc_07e0:
    bra.s loc_07f0
loc_07e2:
    bra.s loc_07f4
loc_07e4:
    pea $5e
    move.l d4,-(sp)
    jsr hunk_9_loc_0018
loc_07f0:
    moveq #0,d4
    addq.l #8,sp
loc_07f4:
    move.l d4,d0
    movem.l (sp)+,d2-d4/a2
    rts
loc_07fc:
    move.l d2,-(sp)
    move.l 8(sp),d2
    move.l 12(sp),d1
    moveq #78,d0
    add.l d0,d1
    move.l d1,-(sp)
    move.l d2,-(sp)
    jsr sub_0656(pc)
loc_0812:
    addq.l #8,sp
    move.l (sp)+,d2
    rts
loc_0818:
    movem.l d2-d4/a2-a3,-(sp)
    movea.l 24(sp),a2
    move.l 28(sp),d2
    move.l d2,-(sp)
    jsr hunk_5_loc_0000
loc_082c:
    move.l d0,d3
    move.l a2,d4
    addq.l #4,sp
    beq.s loc_085c
loc_0834:
    bra.s loc_0856
loc_0836:
    move.l d3,-(sp)
    move.l d2,-(sp)
    move.l a3,-(sp)
    jsr hunk_5_loc_0048
loc_0842:
    tst.l d0
    lea 12(sp),sp
    bne.s loc_0856
loc_084a:
    adda.l d3,a3
    cmpi.b #$3d,(a3)+
    bne.s loc_0856
loc_0852:
    move.l a3,d0
    bra.s loc_085e
loc_0856:
    movea.l (a2)+,a3
    move.l a3,d0
    bne.s loc_0836
loc_085c:
    moveq #0,d0
loc_085e:
    movem.l (sp)+,d2-d4/a2-a3
    rts
loc_0864:
    movem.l d2-d5,-(sp)
    move.l 20(sp),d2
    move.l 24(sp),d3
    move.l d3,-(sp)
    jsr hunk_5_loc_0000
loc_0878:
    move.l d0,d5
    addq.l #4,sp
    bra.s loc_08ca
loc_087e:
    pea $7c
    move.l d2,-(sp)
    jsr hunk_5_loc_0010
loc_088a:
    move.l d0,d4
    addq.l #8,sp
    beq.s loc_0896
loc_0890:
    move.l d4,d0
    sub.l d2,d0
    bra.s loc_08a0
loc_0896:
    move.l d2,-(sp)
    jsr hunk_5_loc_0000
loc_089e:
    addq.l #4,sp
loc_08a0:
    cmp.l d5,d0
    bne.s loc_08be
loc_08a4:
    move.l d5,-(sp)
    move.l d3,-(sp)
    move.l d2,-(sp)
    jsr hunk_5_loc_0048
loc_08b0:
    tst.l d0
    lea 12(sp),sp
    bne.s loc_08be
loc_08b8:
    moveq #1,d2
    move.l d2,d0
    bra.s loc_08d0
loc_08be:
    tst.l d4
    beq.s loc_08c8
loc_08c2:
    move.l d4,d2
    addq.l #1,d2
    bra.s loc_08ca
loc_08c8:
    moveq #0,d2
loc_08ca:
    tst.l d2
    bne.s loc_087e
loc_08ce:
    moveq #0,d0
loc_08d0:
    movem.l (sp)+,d2-d5
    rts
loc_08d6:
    movem.l d2-d4/a2-a4,-(sp)
    movea.l 28(sp),a2
    movea.l 32(sp),a3
    moveq #30,d4
    movea.l a3,a4
    clr.b 30(a2)
    pea $5
    pea dat_000c
    move.l a4,-(sp)
    jsr hunk_5_loc_0048
loc_08fc:
    tst.l d0
    lea 12(sp),sp
    beq.s loc_0926
loc_0904:
    pea dat_0012
    move.l a2,-(sp)
    jsr hunk_5_loc_002c
loc_0912:
    move.l d4,-(sp)
    move.l a3,-(sp)
    move.l a2,-(sp)
    jsr hunk_5_loc_006c
loc_091e:
    lea 20(sp),sp
    bra.w loc_09b6
loc_0926:
    addq.l #5,a4
    pea $3
    pea dat_001c
    move.l a4,-(sp)
    jsr hunk_5_loc_0048
loc_093a:
    tst.l d0
    lea 12(sp),sp
    bne.s loc_0948
loc_0942:
    moveq #1,d3
    addq.l #3,a4
    bra.s loc_0992
loc_0948:
    moveq #0,d3
    bra.s loc_095c
loc_094c:
    move.l d3,d0
    add.l d0,d0
    move.l d0,d1
    asl.l #2,d0
    add.l d1,d0
    add.l d2,d0
    move.l d0,d3
    addq.l #1,a4
loc_095c:
    move.b (a4),d0
    ext.w d0
    ext.l d0
    move.l d0,-(sp)
    jsr loc_09be
loc_096a:
    move.l d0,d2
    addq.l #4,sp
    bge.s loc_094c
loc_0970:
    tst.l d3
    beq.s loc_0904
loc_0974:
    pea AbsExecBase
    pea dat_0020
    move.l a4,-(sp)
    jsr hunk_5_loc_0048
loc_0986:
    tst.l d0
    lea 12(sp),sp
    bne.w loc_0904
loc_0990:
    addq.l #4,a4
loc_0992:
    move.l d3,d0
    addq.l #1,d0
    move.l d0,-(sp)
    pea dat_0026
    move.l a2,-(sp)
    jsr hunk_6_loc_00c8
loc_09a6:
    move.l d4,-(sp)
    move.l a4,-(sp)
    move.l a2,-(sp)
    jsr hunk_5_loc_006c
loc_09b2:
    lea 24(sp),sp
loc_09b6:
    move.l a2,d0
    movem.l (sp)+,d2-d4/a2-a4
    rts
loc_09be:
    move.l 4(sp),d1
    moveq #48,d0
    cmp.l d1,d0
    bgt.s loc_09d6
loc_09c8:
    moveq #57,d0
    cmp.l d1,d0
    blt.s loc_09d6
loc_09ce:
    move.l d1,d0
    moveq #48,d1
    sub.l d1,d0
    bra.s loc_09d8
loc_09d6:
    moveq #-1,d0
loc_09d8:
    rts
    dc.b    $00,$00

; Hunk 4: 52 bytes, 0 entities, 0 blocks

    section data,data

dat_0000:
    dc.b    ".info",0
dat_0006:
    dc.b    ".info",0
dat_000c:
    dc.b    "copy ",0
dat_0012:
    dc.b    "copy of ",0
    dc.b    $00
dat_001c:
    dc.b    $6f,$66,$20,$00
dat_0020:
    dc.b    " of ",0
    dc.b    $00
dat_0026:
    dc.b    "copy %ld of ",0
    dc.b    $00

; Hunk 5: 164 bytes, 0 entities, 34 blocks

    section code,code

hunk_5_loc_0000:
    movea.l 4(sp),a0
    moveq #-1,d0
loc_0006:
    tst.b (a0)+
    dbeq d0,loc_0006
loc_000c:
    not.l d0
    rts
hunk_5_loc_0010:
    movea.l 4(sp),a0
    move.l 8(sp),d0
hunk_5_loc_0018:
    move.b (a0)+,d1
    beq.s hunk_5_loc_0026
hunk_5_loc_001c:
    cmp.b d0,d1
    bne.s hunk_5_loc_0018
hunk_5_loc_0020:
    subq.l #1,a0
    move.l a0,d0
loc_0024:
    rts
hunk_5_loc_0026:
    moveq #0,d0
    bra.s loc_0024
    dc.b    $00,$00
hunk_5_loc_002c:
    movem.l 4(sp),a0-a1
loc_0032:
    move.b (a1)+,(a0)+
    bne.s loc_0032
hunk_5_loc_0036:
    rts
hunk_5_loc_0038:
    movem.l 4(sp),a0-a1
hunk_5_loc_003e:
    tst.b (a0)+
    bne.s hunk_5_loc_003e
hunk_5_loc_0042:
    subq.l #1,a0
    bra.s loc_0032
    dc.b    $00,$00
hunk_5_loc_0048:
    movem.l 4(sp),a0-a1
    move.l 12(sp),d0
loc_0052:
    subq.l #1,d0
    blt.s hunk_5_loc_0060
hunk_5_loc_0056:
    move.b (a1)+,d1
    cmp.b (a0)+,d1
    bne.s loc_0064
hunk_5_loc_005c:
    tst.b d1
    bne.s loc_0052
hunk_5_loc_0060:
    moveq #0,d0
loc_0062:
    rts
loc_0064:
    moveq #1,d0
    bgt.s loc_0062
loc_0068:
    moveq #-1,d0
    rts
hunk_5_loc_006c:
    movem.l 4(sp),a0-a1
    move.l 12(sp),d0
loc_0076:
    tst.b (a0)+
    beq.s loc_0080
hunk_5_loc_007a:
    subq.l #1,d0
    bgt.s loc_0076
loc_007e:
    bra.s loc_0086
loc_0080:
    subq.l #1,a0
    bsr.w hunk_5_loc_0092
loc_0086:
    rts
    dc.b    $4c,$ef,$03,$00,$00,$04,$20,$2f,$00,$0c
hunk_5_loc_0092:
    subq.l #1,d0
    blt.s loc_00a2
loc_0096:
    move.b (a1)+,(a0)+
    bne.s hunk_5_loc_0092
loc_009a:
    subq.l #1,d0
    ble.s loc_00a2
hunk_5_loc_009e:
    clr.b (a0)+
    bra.s loc_009a
loc_00a2:
    rts

; Hunk 6: 240 bytes, 0 entities, 10 blocks

    section code,code

hunk_6_loc_0000:
    cmpi.l #$ffff,d2
    bgt.s hunk_6_loc_0020
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
hunk_6_loc_0020:
    move.l d1,d0
    clr.w d0
    swap d0
    swap d1
    clr.w d1
    movea.l d2,a1
    moveq #15,d2
hunk_6_loc_002e:
    add.l d1,d1
    addx.l d0,d0
    cmpa.l d0,a1
    bgt.s loc_003a
hunk_6_loc_0036:
    sub.l a1,d0
    addq.w #1,d1
loc_003a:
    dbf d2,hunk_6_loc_002e
hunk_6_loc_003e:
    rts
hunk_6_loc_0040:
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
    dc.b    $2f,$02,$24,$01,$22,$00,$61,$98
hint_0068:
    dc.b    $24,$1f,$4e,$75
hint_006c:
    dc.b    $2f,$02,$24,$01,$22,$00,$61,$8c
hint_0074:
    dc.b    $20,$01,$24,$1f,$4e,$75
hint_007a:
    dc.b    $2f,$02,$24,$01,$6c,$02
hint_0080:
    dc.b    $44,$82
hint_0082:
    dc.b    $22,$00,$70,$00,$4a,$81,$6c,$04
hint_008a:
    dc.b    $44,$81,$46,$80
hint_008e:
    dc.b    $20,$40,$61,$00,$ff,$6e
hint_0094:
    dc.b    $34,$08,$67,$02
hint_0098:
    dc.b    $44,$80
hint_009a:
    dc.b    $24,$1f,$4e,$75
hint_009e:
    dc.b    $2f,$02,$20,$40,$70,$00,$24,$01,$6c,$04
hint_00a8:
    dc.b    $44,$82,$46,$80
hint_00ac:
    dc.b    $22,$08,$6c,$04
hint_00b0:
    dc.b    $44,$81,$46,$80
hint_00b4:
    dc.b    $20,$40,$61,$00,$ff,$48
hint_00ba:
    dc.b    $24,$08,$67,$02
hint_00be:
    dc.b    $44,$81
hint_00c0:
    dc.b    $20,$01,$24,$1f,$4e,$75
    dc.b    $00,$00
hunk_6_loc_00c8:
    movem.l a2-a4/a6,-(sp)
    movea.l 20(sp),a3
    movea.l 24(sp),a0
    lea 28(sp),a1
    lea pcref_00ec(pc),a2
    movea.l AbsExecBase,a6
    jsr -522(a6) ; unresolved_indirect_core:disp
loc_00e6:
    movem.l (sp)+,a2-a4/a6
    rts
pcref_00ec:
    dc.b    $16,$c0,$4e,$75

; Hunk 7: 20 bytes, 0 entities, 1 blocks

    section code,code

hunk_7_loc_0000:
    movea.l 4(sp),a0
    move.l a0,(a0)
    addq.l #4,(a0)
    clr.l 4(a0)
    move.l a0,8(a0)
    rts
    dc.b    $00,$00

; Hunk 8: 104 bytes, 0 entities, 8 blocks

    section code,code

hunk_8_loc_0000:
    movem.l d2/a6,-(sp)
    movea.l long_0196,a6
    movem.l 12(sp),d1-d2
    jsr _LVOiconPrivate1(a6)
loc_0014:
    movem.l (sp)+,d2/a6
    rts
    dc.b    $00,$00
hunk_8_loc_001c:
    move.l a6,-(sp)
    movea.l long_0196,a6
    move.l 8(sp),d1
    jsr _LVOiconPrivate2(a6)
hunk_8_loc_002c:
    movea.l (sp)+,a6
    rts
hunk_8_loc_0030:
    movem.l d2-d3/a6,-(sp)
    movea.l long_0196,a6
    movem.l 16(sp),d1-d3
    jsr _LVOiconPrivate3(a6)
hunk_8_loc_0044:
    movem.l (sp)+,d2-d3/a6
    rts
    dc.b    $00,$00
hunk_8_loc_004c:
    movem.l d2-d3/a6,-(sp)
    movea.l long_0196,a6
    movem.l 16(sp),d1-d3
    jsr _LVOiconPrivate4(a6)
hunk_8_loc_0060:
    movem.l (sp)+,d2-d3/a6
    rts
    dc.b    $00,$00

; Hunk 9: 112 bytes, 1 entities, 10 blocks

    section code,code

hunk_9_loc_0000:
    move.l a6,-(sp)
    movea.l long_0192,a6
    movem.l 8(sp),d0-d1
    jsr _LVOAllocMem(a6)
loc_0012:
    movea.l (sp)+,a6
    rts
    dc.b    $00,$00
hunk_9_loc_0018:
    move.l a6,-(sp)
    movea.l long_0192,a6
    movea.l 8(sp),a1
    move.l 12(sp),d0
    jsr _LVOFreeMem(a6)
hunk_9_loc_002c:
    movea.l (sp)+,a6
    rts
hunk_9_loc_0030:
    move.l a6,-(sp)
    movea.l long_0192,a6
    movea.l 8(sp),a0
    jsr _LVOFreeEntry(a6)
hunk_9_loc_0040:
    movea.l (sp)+,a6
    rts
hunk_9_loc_0044:
    move.l a6,-(sp)
    movea.l long_0192,a6
    movem.l 8(sp),a0-a1
    jsr _LVOAddTail(a6)
hunk_9_loc_0056:
    movea.l (sp)+,a6
    rts
    dc.b    $00,$00
hunk_9_loc_005c:
    move.l a6,-(sp)
    movea.l long_0192,a6
    movea.l 8(sp),a0
    jsr _LVORemTail(a6)
hunk_9_loc_006c:
    movea.l (sp)+,a6
    rts
