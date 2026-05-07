    INCLUDE "dos/dos_lib.i"
    INCLUDE "exec/alerts.i"
    INCLUDE "exec/devices.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/libraries.i"
    INCLUDE "exec/nodes.i"
    INCLUDE "exec/resident.i"

    RSSET LIB_SIZE
app_ExecBase RS.L 1
app_DOSBase RS.L 1
app_SegList RS.L 1
app_SIZEOF EQU __RS


    SECTION section_0,code
	dc.b $70,$FF,$4E,$75
resident:	; STRUCT RT
	dc.w RTC_MATCHWORD	; UWORD RT_MATCHWORD = RTC_MATCHWORD
	dc.l resident	; APTR RT_MATCHTAG
	dc.l loc_0_00000280	; APTR RT_ENDSKIP
	dc.b RTF_AUTOINIT	; UBYTE RT_FLAGS = RTF_AUTOINIT
	dc.b $22	; UBYTE RT_VERSION
	dc.b NT_LIBRARY	; UBYTE RT_TYPE = NT_LIBRARY
	dc.b $46	; BYTE RT_PRI
	dc.l resident_name	; APTR RT_NAME
	dc.l resident_idstring	; APTR RT_IDSTRING
	dc.l resident_autoinit	; APTR RT_INIT
resident_name:
	dc.b "icon.library",$00
resident_idstring:
	dc.b "icon 34.2 (22 Jun 1988)",$0D,$0A,$00
	dc.b $00,$00,$00
resident_autoinit:	; STRUCT resident_autoinit
	dc.l app_SIZEOF	; ULONG resident_base_size
	dc.l resident_vectors	; APTR resident_vectors
	dc.l resident_init_struct	; APTR resident_init_struct
	dc.l resident_init	; APTR resident_init_function
resident_vectors:
	dc.l icon_lib_open
	dc.l icon_lib_close
	dc.l icon_lib_expunge
	dc.l icon_lib_extfunc
	dc.l icon_private1
	dc.l icon_private2
	dc.l icon_private3
	dc.l icon_private4
	dc.l free_free_list
	dc.l icon_private5
	dc.l icon_private6
	dc.l add_free_list
	dc.l get_disk_object
	dc.l icon_private4
	dc.l free_disk_object
	dc.l find_tool_type
	dc.l match_tool_value
	dc.l bump_revision
	dc.l $FFFFFFFF
resident_init_struct:
	dc.b $E0,$00,$00,$08,$09,$00,$C0,$00,$00,$0A
	dc.l resident_name
	dc.b $E0,$00,$00,$0E,$06,$00,$D0,$00,$00,$14,$00,$22,$D0,$00,$00,$16
	dc.b $00,$02,$C0,$00,$00,$18
	dc.l resident_idstring
	dc.b $00,$00,$00,$00
loc_0_000000D0:
	dc.b "dos.library",$00
    ; KNOWN: base A6=icon.library:LIB
icon_lib_open:
	addq.w #1,LIB_OPENCNT(a6)
	bclr.b #3,LIB_FLAGS(a6)
	move.l a6,d0
	rts
    ; KNOWN: base A6=icon.library:LIB
icon_lib_close:
	moveq.l #0,d0
	subq.w #1,LIB_OPENCNT(a6)
	bne.b loc_0_000000FE
	btst.b #3,LIB_FLAGS(a6)
	beq.b loc_0_000000FE
	bsr.w icon_lib_expunge
loc_0_000000FE:
	rts
    ; KNOWN: base A6=icon.library:LIB
icon_lib_expunge:
	tst.w LIB_OPENCNT(a6)
	bne.b loc_0_0000013A
	move.l app_SegList(a6),-(a7)
	movea.l a6,a1
	movea.l (a1),a0
	movea.l $0004(a1),a1
	move.l a0,(a1)
	move.l a1,$0004(a0)
	movea.l a6,a1
	moveq.l #0,d0
	moveq.l #0,d1
	move.w LIB_NEGSIZE(a6),d0
	suba.l d0,a1
	move.w LIB_POSSIZE(a6),d1
	add.l d1,d0
	move.l a6,-(a7)
	movea.l app_ExecBase(a6),a6
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	move.l (a7)+,d0
	bra.b loc_0_00000142
loc_0_0000013A:
	bset.b #3,$000E(a6)
	moveq.l #0,d0
loc_0_00000142:
	rts
    ; KNOWN: base A6=icon.library:LIB
icon_lib_extfunc:
	moveq.l #0,d0
	rts
    ; KNOWN: base A6=exec.library:LIB; base D0=__amiga_app_base__; type A0=seglist:BPTR
resident_init:
	move.l a2,-(a7)
	movea.l d0,a2
	move.l a0,app_SegList(a2)
	move.l a6,app_ExecBase(a2)
	lea.l loc_0_000000D0(pc),a1
	jsr _LVOOldOpenLibrary(a6)
	move.l d0,app_DOSBase(a2)
	bne.b loc_0_0000017C
	movem.l d7/a5-a6,-(a7)
	move.l #AN_IconLib|AG_OpenLib|AO_DOSLib,d7
	movea.l $0004.w,a6
	jsr _LVOAlert(a6)
	movem.l (a7)+,d7/a5-a6
	moveq.l #0,d0
	bra.b loc_0_0000018E
loc_0_0000017C:
	move.l app_ExecBase(a2),h0dl_ExecBase.l
	move.l app_DOSBase(a2),h0dl_DOSBase.l
	move.l a2,d0
loc_0_0000018E:
	movea.l (a7)+,a2
	rts
h0dl_ExecBase:
	dc.b $00,$00,$00,$00
h0dl_DOSBase:
	dc.b $00,$00,$00,$00
    ; DECL: void iconPrivate1()
    ; KNOWN: base A6=icon.library:LIB
icon_private1:
	move.l a0,-(a7)
	move.l a6,-(a7)
	jsr loc_3_00000000.l
	addq.l #8,a7
	rts
    ; DECL: void iconPrivate2()
    ; KNOWN: base A6=icon.library:LIB
icon_private2:
	movem.l a0-a1,-(a7)
	move.l a6,-(a7)
	jsr loc_3_000000A8.l
	lea.l $000C(a7),a7
	rts
    ; DECL: void iconPrivate3()
    ; KNOWN: base A6=icon.library:LIB
icon_private3:
	movem.l a0-a2,-(a7)
	move.l a6,-(a7)
	jsr loc_3_00000124.l
	lea.l $0010(a7),a7
	rts
    ; DECL: void iconPrivate4()
    ; DECL: BOOL PutDiskObject(UBYTE *name, struct DiskObject *diskobj)
    ; KNOWN: base A6=icon.library:LIB; type A0=name:UBYTE *; type A1=diskobj:struct DiskObject *
icon_private4:
	movem.l a0-a1,-(a7)
	move.l a6,-(a7)
	jsr loc_3_000003FE.l
	lea.l $000C(a7),a7
	rts
    ; DECL: void FreeFreeList(struct FreeList *freelist)
    ; KNOWN: base A6=icon.library:LIB; type A0=freelist:struct FreeList *
free_free_list:
	move.l a0,-(a7)
	move.l a6,-(a7)
	jsr loc_3_00000656.l
	addq.l #8,a7
	rts
    ; DECL: void iconPrivate5()
    ; KNOWN: base A6=icon.library:LIB
icon_private5:
	move.l a0,-(a7)
	move.l a6,-(a7)
	jsr loc_3_00000692.l
	addq.l #8,a7
	rts
    ; DECL: void iconPrivate6()
    ; KNOWN: base A6=icon.library:LIB
icon_private6:
	move.l a6,-(a7)
	jsr loc_3_000006A8.l
	addq.l #4,a7
	rts
    ; DECL: BOOL AddFreeList(struct FreeList *free, APTR mem, ULONG len)
    ; KNOWN: base A6=icon.library:LIB; type A0=free:struct FreeList *; type A1=mem:APTR; type A2=len:ULONG
add_free_list:
	movem.l a0-a2,-(a7)
	move.l a6,-(a7)
	jsr loc_3_0000071C.l
	lea.l $0010(a7),a7
	rts
    ; DECL: struct DiskObject *GetDiskObject(UBYTE *name)
    ; KNOWN: base A6=icon.library:LIB; type A0=name:UBYTE *
get_disk_object:
	move.l a0,-(a7)
	move.l a6,-(a7)
	jsr loc_3_00000768.l
	addq.l #8,a7
	rts
    ; DECL: void FreeDiskObject(struct DiskObject *diskobj)
    ; KNOWN: base A6=icon.library:LIB; type A0=diskobj:struct DiskObject *
free_disk_object:
	move.l a0,-(a7)
	move.l a6,-(a7)
	jsr loc_3_000007FC.l
	addq.l #8,a7
	rts
    ; DECL: char *FindToolType(UBYTE **toolTypeArray, UBYTE *typeName)
    ; KNOWN: base A6=icon.library:LIB; type A0=toolTypeArray:UBYTE **; type A1=typeName:UBYTE *
find_tool_type:
	movem.l a0-a1,-(a7)
	jsr loc_3_00000818.l
	addq.l #8,a7
	rts
    ; DECL: BOOL MatchToolValue(UBYTE *typeString, UBYTE *value)
    ; KNOWN: base A6=icon.library:LIB; type A0=typeString:UBYTE *; type A1=value:UBYTE *
match_tool_value:
	movem.l a0-a1,-(a7)
	jsr loc_3_00000864.l
	addq.l #8,a7
	rts
    ; DECL: char *BumpRevision(char *newbuf, UBYTE *oldname)
    ; KNOWN: base A6=icon.library:LIB; type A0=newbuf:char *; type A1=oldname:UBYTE *
bump_revision:
	movem.l a0-a1,-(a7)
	jsr loc_3_000008D6.l
	addq.l #8,a7
	rts
	dc.b $00,$00
loc_0_00000260:
	move.l a6,-(a7)
	movea.l $0008(a7),a6
	suba.l a1,a1
	move.l a6,-(a7)
	movea.l app_ExecBase(a6),a6
	jsr _LVOFindTask(a6)
	movea.l (a7)+,a6
	movea.l d0,a1
	move.l $000C(a7),$0094(a1)
	movea.l (a7)+,a6
	rts
loc_0_00000280:
	dc.b $00,$00,$00,$00
    SECTION section_1,code
loc_1_00000000:
	movem.l d2-d5,-(a7)
	move.l $0014(a7),d3
	move.l $0018(a7),d4
	move.l $001C(a7),d2
	move.l $0020(a7),-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	move.l d2,-(a7)	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_9_00000000.l
	move.l d0,d5
	addq.l #8,a7
	beq.b loc_1_00000046
	move.l d2,-(a7)
	move.l d5,-(a7)
	move.l d4,-(a7)
	move.l d3,-(a7)
	jsr loc_3_0000071C.l
	tst.l d0
	lea.l $0010(a7),a7
	bne.b loc_1_00000046
	move.l d2,-(a7)	; KNOWN: arg +8 byteSize unsigned long
	move.l d5,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_9_00000018.l
	moveq.l #0,d5
	addq.l #8,a7
loc_1_00000046:
	move.l d5,d0
	movem.l (a7)+,d2-d5
	rts
loc_1_0000004E:
	movem.l d2/a2,-(a7)
	movea.l $0010(a7),a2
	move.l #$10000,-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	pea.l $0060.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_9_00000000.l
	movea.l d0,a0
	move.l a0,d2
	addq.l #8,a7
	beq.b loc_1_0000008A
	move.w #$A,$000E(a0)
	move.w #$A,(a2)
	move.l a0,-(a7)	; KNOWN: arg +8 node LN
	pea.l $0002(a2)	; KNOWN: arg +4 list LH
	jsr loc_9_00000044.l
	moveq.l #1,d0
	addq.l #8,a7
	bra.b loc_1_0000008C
loc_1_0000008A:
	moveq.l #0,d0
loc_1_0000008C:
	movem.l (a7)+,d2/a2
	rts
loc_1_00000092:
	move.l $0008(a7),d0
	move.l $000C(a7),d1
	move.l $0010(a7),-(a7)	; KNOWN: arg +12 length long
	move.l d1,-(a7)	; KNOWN: arg +8 buffer APTR
	move.l d0,-(a7)	; KNOWN: arg +4 file BPTR
	jsr loc_8_00000030.l
	move.l d0,d1
	cmp.l $001C(a7),d0
	lea.l $000C(a7),a7
	beq.b loc_1_000000B8
	moveq.l #0,d0
	bra.b loc_1_000000BA
loc_1_000000B8:
	move.l d1,d0
loc_1_000000BA:
	rts
loc_1_000000BC:
	move.l $0008(a7),d0
	move.l $000C(a7),d1
	move.l $0010(a7),-(a7)	; KNOWN: arg +12 length long
	move.l d1,-(a7)	; KNOWN: arg +8 buffer APTR
	move.l d0,-(a7)	; KNOWN: arg +4 file BPTR
	jsr loc_8_0000004C.l
	move.l d0,d1
	cmp.l $001C(a7),d0
	lea.l $000C(a7),a7
	beq.b loc_1_000000E2
	moveq.l #0,d0
	bra.b loc_1_000000E4
loc_1_000000E2:
	move.l d1,d0
loc_1_000000E4:
	rts
	dc.b $00,$00
    SECTION section_2,code
loc_2_00000000:
	movem.l d2-d3/a2,-(a7)
	move.l $0010(a7),d2
	move.l $0014(a7),d3
	movea.l $0018(a7),a2
	moveq.l #1,d0
	move.l a2,d1
	beq.b loc_2_00000074
	pea.l $0014.w
	move.l a2,-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_000000BC.l
	move.l d0,d0
	lea.l $0010(a7),a7
	beq.b loc_2_00000074
	move.w $0004(a2),d1
	ext.l d1
	moveq.l #15,d0
	add.l d0,d1
	asr.l #3,d1
	andi.l #65534,d1
	move.w $0006(a2),d0
	ext.l d0
	jsr loc_6_00000040.l
	move.l d0,d1
	move.w $0008(a2),d0
	ext.l d0
	jsr loc_6_00000040.l
	move.l d0,-(a7)
	move.l $000A(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_000000BC.l
	move.l d0,d0
	lea.l $0010(a7),a7
	beq.w loc_2_00000074
loc_2_00000074:
	movem.l (a7)+,d2-d3/a2
	rts
loc_2_0000007A:
	movem.l d2-d3/a2,-(a7)
	move.l $0010(a7),d2
	move.l $0014(a7),d3
	movea.l $0018(a7),a2
	bra.b loc_2_000000CC
loc_2_0000008C:
	pea.l $0010.w
	move.l a2,-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_000000BC.l
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_2_000000D4
	move.b $0007(a2),d0
	ext.w d0
	ext.l d0
	add.l d0,d0
	add.l d0,d0
	move.l d0,-(a7)
	move.l $0008(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_000000BC.l
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_2_000000D4
	movea.l $000C(a2),a2
loc_2_000000CC:
	move.l a2,d0
	bne.b loc_2_0000008C
	moveq.l #1,d0
	bra.b loc_2_000000D6
loc_2_000000D4:
	moveq.l #0,d0
loc_2_000000D6:
	movem.l (a7)+,d2-d3/a2
	rts
loc_2_000000DC:
	movem.l d2-d5/a2,-(a7)
	move.l $0018(a7),d2
	move.l $001C(a7),d3
	move.l $0020(a7),d4
	tst.l $0024(a7)
	beq.w loc_2_0000019E
	move.l #$10000,-(a7)
	pea.l $0014.w
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,$0034(a7)
	lea.l $0010(a7),a7
	beq.w loc_2_000001A4
	pea.l $0014.w
	move.l $0028(a7),-(a7)
	move.l d4,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000092.l
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_2_000001A4
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
	jsr loc_6_00000040.l
	move.l d0,d5
	movea.l $0024(a7),a2
	move.l d5,d1
	move.w $0008(a2),d0
	ext.l d0
	jsr loc_6_00000040.l
	move.l d0,d5
	movea.l $0024(a7),a2
	pea.l $0002.w
	move.l d5,-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,$000A(a2)
	move.l d5,-(a7)
	movea.l $0038(a7),a2
	move.l $000A(a2),-(a7)
	move.l d4,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000092.l
	tst.l d0
	lea.l $0020(a7),a7
	beq.b loc_2_000001A4
loc_2_0000019E:
	move.l $0024(a7),d0
	bra.b loc_2_000001A6
loc_2_000001A4:
	moveq.l #-1,d0
loc_2_000001A6:
	movem.l (a7)+,d2-d5/a2
	rts
loc_2_000001AC:
	movem.l d2-d6/a2,-(a7)
	move.l $001C(a7),d2
	move.l $0020(a7),d3
	move.l $0024(a7),d4
	moveq.l #0,d6
	bra.w loc_2_0000026C
loc_2_000001C2:
	move.l #$10000,-(a7)
	pea.l $0010.w
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,$0038(a7)
	lea.l $0010(a7),a7
	beq.w loc_2_00000278
	tst.l d6
	bne.b loc_2_000001EC
	move.l $0028(a7),d6
	bra.b loc_2_000001F2
loc_2_000001EC:
	move.l $0028(a7),$000C(a2)
loc_2_000001F2:
	pea.l $0010.w
	move.l $002C(a7),-(a7)
	move.l d4,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000092.l
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_2_00000278
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
	jsr loc_1_00000000.l
	move.l d0,$0008(a2)
	movea.l $0038(a7),a0
	tst.l $0008(a0)
	lea.l $0010(a7),a7
	beq.b loc_2_00000278
	move.l d5,-(a7)
	movea.l $002C(a7),a2
	move.l $0008(a2),-(a7)
	move.l d4,-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000092.l
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_2_00000278
	movea.l $0028(a7),a2
	movea.l $0028(a7),a0
	move.l $000C(a0),$0028(a7)
loc_2_0000026C:
	tst.l $0028(a7)
	bne.w loc_2_000001C2
	move.l d6,d0
	bra.b loc_2_0000027A
loc_2_00000278:
	moveq.l #-1,d0
loc_2_0000027A:
	movem.l (a7)+,d2-d6/a2
	rts
    SECTION section_3,code
loc_3_00000000:
	link a6,#-80
	movem.l d2-d4/a2,-(a7)
	move.l $0008(a6),d2
	move.l $000C(a6),d3
	move.l d2,-(a7)
	jsr loc_3_000006A8.l
	movea.l d0,a2
	move.l a2,d4
	addq.l #4,a7
	beq.w loc_3_0000009C
	pea.l $008C(a2)
	pea.l -$0050(a6)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_3_00000124.l
	tst.l d0
	lea.l $0010(a7),a7
	bne.b loc_3_0000004A
	move.l a2,-(a7)
	move.l d2,-(a7)
	jsr loc_3_00000692.l
	addq.l #8,a7
	bra.b loc_3_0000009C
loc_3_0000004A:
	lea.l -$004C(a6),a0
	lea.l $0060(a2),a1
	moveq.l #10,d0
loc_3_00000054:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_3_00000054
	move.b -$0020(a6),$003D(a2)
	move.l -$001E(a6),$0048(a2)
	move.l -$001A(a6),$005C(a2)
	move.l -$0016(a6),$0054(a2)
	move.l -$0012(a6),$0058(a2)
	move.l -$000E(a6),$004C(a2)
	move.l -$000A(a6),$009C(a2)
	move.l -$0006(a6),$00A0(a2)
	tst.l $004C(a2)
	beq.b loc_3_00000098
	movea.l $004C(a2),a0
	move.l a2,$01A8(a0)
loc_3_00000098:
	move.l a2,d0
	bra.b loc_3_0000009E
loc_3_0000009C:
	moveq.l #0,d0
loc_3_0000009E:
	movem.l -$0060(a6),d2-d4/a2
	unlk a6
	rts
loc_3_000000A8:
	link a6,#-80
	movem.l d2/a2,-(a7)
	move.l $0008(a6),d1
	move.l $000C(a6),d2
	movea.l $0010(a6),a0
loc_3_000000BC:
	move.w #$E310,-$0050(a6)
	move.w #$1,-$004E(a6)
	lea.l $0060(a0),a1
	lea.l -$004C(a6),a2
	moveq.l #10,d0
loc_3_000000D2:
	move.l (a1)+,(a2)+
	dbf.w d0,loc_3_000000D2
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
	jsr loc_3_000003FE.l
	lea.l $000C(a7),a7
	movem.l -$0058(a6),d2/a2
	unlk a6
	rts
loc_3_00000124:
	link a6,#-268
	movem.l d2-d5/a2-a5,-(a7)
	move.l $0008(a6),d2
	move.l $000C(a6),d0
	movea.l $0010(a6),a2
	movea.l #loc_1_00000092,a3
	move.l #loc_1_00000000,d3
	lea.l $0004(a2),a4
	move.l d0,-(a7)
	pea.l -$010C(a6)
	jsr loc_5_0000002C.l
	pea.l loc_4_00000000.l
	pea.l -$010C(a6)
	jsr loc_5_00000038.l
	pea.l $03ED.w	; KNOWN: arg +8 accessMode long dos.open.access_mode
	pea.l -$010C(a6)	; KNOWN: arg +4 name STRPTR string_ptr
	jsr loc_8_00000000.l
	move.l d0,d5
	lea.l $0018(a7),a7
	bne.b loc_3_00000180
	moveq.l #0,d4
	bra.w loc_3_000003F2
loc_3_00000180:
	pea.l $004E.w
	move.l a2,-(a7)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	cmpi.w #58128,(a2)
	bne.w loc_3_000003EE
	cmpi.w #1,$0002(a2)
	bne.w loc_3_000003EE
	clr.l (a4)
	clr.l (a4)
	tst.l $0042(a2)
	beq.b loc_3_000001FC
	move.l #$10002,-(a7)
	pea.l $01BE.w
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	pea.l $0038.w
	movea.l d4,a5
	pea.l (a5)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l d4,$0042(a2)
	movea.l d4,a5
	pea.l $01AC(a5)
	jsr loc_7_00000000.l
	addq.l #4,a7
loc_3_000001FC:
	btst.b #2,$000D(a4)
	beq.b loc_3_0000024A
	move.l $0012(a4),-(a7)
	move.l d5,-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_2_000000DC.l
	move.l d0,d4
	moveq.l #-1,d0
	cmp.l d4,d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l d4,$0012(a4)
	move.l $0016(a4),-(a7)
	move.l d5,-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_2_000000DC.l
	move.l d0,d4
	moveq.l #-1,d0
	cmp.l d4,d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	bra.b loc_3_0000028E
loc_3_0000024A:
	move.l $0012(a4),-(a7)
	move.l d5,-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_2_000001AC.l
	move.l d0,d4
	moveq.l #-1,d0
	cmp.l d4,d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l d4,$0012(a4)
	move.l $0016(a4),-(a7)
	move.l d5,-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_2_000001AC.l
	move.l d0,d4
	moveq.l #-1,d0
	cmp.l d4,d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
loc_3_0000028E:
	move.l d4,$0016(a4)
	tst.l $001A(a4)
	bne.w loc_3_0000029A
loc_3_0000029A:
	tst.l $0032(a2)
	beq.b loc_3_000002F2
	pea.l $0004.w
	pea.l -$0008(a6)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l #$10000,-(a7)
	move.l -$0008(a6),-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,$0032(a2)
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l -$0008(a6),-(a7)
	move.l $0032(a2),-(a7)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
loc_3_000002F2:
	tst.l $0036(a2)
	beq.w loc_3_00000392
	pea.l $0004.w
	pea.l -$0004(a6)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l #$10000,-(a7)
	move.l -$0004(a6),-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	movea.l d0,a4
	move.l a4,d4
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l a4,$0036(a2)
	bra.b loc_3_0000038A
loc_3_0000033A:
	pea.l $0004.w
	pea.l -$0008(a6)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	clr.l -(a7)
	move.l -$0008(a6),-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,(a4)
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	move.l -$0008(a6),-(a7)
	move.l (a4),-(a7)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.w loc_3_000003EE
	subq.l #4,-$0004(a6)
	addq.l #4,a4
loc_3_0000038A:
	moveq.l #4,d0
	cmp.l -$0004(a6),d0
	blt.b loc_3_0000033A
loc_3_00000392:
	tst.l $0046(a2)
	beq.b loc_3_000003E0
	pea.l $0004.w
	pea.l -$0008(a6)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_3_000003EE
	clr.l -(a7)
	move.l -$0008(a6),-(a7)
	move.l $0014(a6),-(a7)
	move.l d2,-(a7)
	jsr loc_1_00000000.l
	move.l d0,$0046(a2)
	lea.l $0010(a7),a7
	beq.b loc_3_000003EE
	move.l -$0008(a6),-(a7)
	move.l $0046(a2),-(a7)
	move.l d5,-(a7)
	move.l d2,-(a7)
	jsr (a3)
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_3_000003EE
loc_3_000003E0:
	moveq.l #1,d4
loc_3_000003E2:
	move.l d5,-(a7)	; KNOWN: arg +4 file BPTR
	jsr loc_8_0000001C.l
	addq.l #4,a7
	bra.b loc_3_000003F2
loc_3_000003EE:
	moveq.l #0,d4
	bra.b loc_3_000003E2
loc_3_000003F2:
	move.l d4,d0
	movem.l -$012C(a6),d2-d5/a2-a5
	unlk a6
	rts
loc_3_000003FE:
	link a6,#-4
	movem.l d2-d6/a2-a4,-(a7)
	move.l $0008(a6),d2
	move.l $000C(a6),d3
	movea.l $0010(a6),a2
	moveq.l #0,d4
	movea.l #loc_1_000000BC,a4
	clr.l -(a7)
	pea.l $0104.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_9_00000000.l
	move.l d0,d5
	addq.l #8,a7
	bne.b loc_3_0000043E
	pea.l $0067.w
	move.l d2,-(a7)
	jsr loc_0_00000260.l
	moveq.l #0,d4
	bra.w loc_3_00000648
loc_3_0000043E:
	move.l $001A(a2),d6
	move.l d3,-(a7)
	move.l d5,-(a7)
	jsr loc_5_0000002C.l
	pea.l loc_4_00000006.l
	move.l d5,-(a7)
	jsr loc_5_00000038.l
	pea.l $03EE.w	; KNOWN: arg +8 accessMode long dos.open.access_mode
	move.l d5,-(a7)	; KNOWN: arg +4 name STRPTR string_ptr
	jsr loc_8_00000000.l
	move.l d0,d3
	lea.l $0018(a7),a7
	beq.w loc_3_00000638
	moveq.l #0,d1
	move.w $0010(a2),d1
	moveq.l #3,d0
	and.l d0,d1
	moveq.l #1,d0
	cmp.l d1,d0
	bne.b loc_3_00000484
	clr.l $001A(a2)
loc_3_00000484:
	pea.l $004E.w
	move.l a2,-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.w loc_3_00000638
	tst.l $0042(a2)
	beq.b loc_3_000004B8
	pea.l $0038.w
	move.l $0042(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.w loc_3_00000638
loc_3_000004B8:
	btst.b #2,$0011(a2)
	beq.b loc_3_000004F2
	move.l $0016(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_2_00000000.l
	move.l d0,d4
	lea.l $000C(a7),a7
	beq.w loc_3_0000062E
	move.l $001A(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_2_00000000.l
	move.l d0,d4
	lea.l $000C(a7),a7
	bne.b loc_3_00000522
	bra.w loc_3_0000062E
loc_3_000004F2:
	move.l $0016(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_2_0000007A.l
	move.l d0,d4
	lea.l $000C(a7),a7
	beq.w loc_3_0000062E
	move.l $001A(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_2_0000007A.l
	move.l d0,d4
	lea.l $000C(a7),a7
	beq.w loc_3_0000062E
loc_3_00000522:
	tst.l $001E(a2)
	bne.w loc_3_0000052A
loc_3_0000052A:
	tst.l $0032(a2)
	beq.b loc_3_00000570
	move.l $0032(a2),-(a7)
	jsr loc_5_00000000.l
	addq.l #1,d0
	move.l d0,-$0004(a6)
	pea.l $0004.w
	pea.l -$0004(a6)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0014(a7),a7
	beq.w loc_3_0000062E
	move.l -$0004(a6),-(a7)
	move.l $0032(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.w loc_3_0000062E
loc_3_00000570:
	tst.l $0036(a2)
	beq.w loc_3_000005EA
	movea.l $0036(a2),a3
	moveq.l #4,d1
	move.l d1,-$0004(a6)
	bra.b loc_3_0000058A
loc_3_00000584:
	addq.l #4,a3
	addq.l #4,-$0004(a6)
loc_3_0000058A:
	tst.l (a3)
	bne.b loc_3_00000584
	pea.l $0004.w
	pea.l -$0004(a6)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.w loc_3_0000062E
	movea.l $0036(a2),a3
	bra.b loc_3_000005E6
loc_3_000005AC:
	move.l (a3),-(a7)
	jsr loc_5_00000000.l
	addq.l #1,d0
	move.l d0,-$0004(a6)
	pea.l $0004.w
	pea.l -$0004(a6)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0014(a7),a7
	beq.b loc_3_0000062E
	move.l -$0004(a6),-(a7)
	move.l (a3),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.b loc_3_0000062E
	addq.l #4,a3
loc_3_000005E6:
	tst.l (a3)
	bne.b loc_3_000005AC
loc_3_000005EA:
	tst.l $0046(a2)
	beq.b loc_3_0000062E
	move.l $0046(a2),-(a7)
	jsr loc_5_00000000.l
	addq.l #1,d0
	move.l d0,-$0004(a6)
	pea.l $0004.w
	pea.l -$0004(a6)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0014(a7),a7
	beq.b loc_3_0000062E
	move.l -$0004(a6),-(a7)
	move.l $0046(a2),-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr (a4)
	move.l d0,d4
	lea.l $0010(a7),a7
	beq.w loc_3_0000062E
loc_3_0000062E:
	move.l d3,-(a7)	; KNOWN: arg +4 file BPTR
	jsr loc_8_0000001C.l
	addq.l #4,a7
loc_3_00000638:
	pea.l $0104.w	; KNOWN: arg +8 byteSize unsigned long
	move.l d5,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_9_00000018.l
	move.l d6,$001A(a2)
loc_3_00000648:
	addq.l #8,a7
	move.l d4,d0
	movem.l -$0024(a6),d2-d6/a2-a4
	unlk a6
	rts
loc_3_00000656:
	move.l a2,-(a7)
	movea.l $000C(a7),a0
	lea.l $0002(a0),a2
	bra.b loc_3_0000066C
loc_3_00000662:
	move.l d0,-(a7)	; KNOWN: arg +4 entry ML
	jsr loc_9_00000030.l
	addq.l #4,a7
loc_3_0000066C:
	move.l a2,-(a7)	; KNOWN: arg +4 list LH
	jsr loc_9_0000005C.l
	move.l d0,d0
	addq.l #4,a7
	beq.b loc_3_00000680
	cmpa.l $0008(a2),a2
	bne.b loc_3_00000662
loc_3_00000680:
	tst.l d0
	beq.b loc_3_0000068E
	move.l d0,-(a7)	; KNOWN: arg +4 entry ML
	jsr loc_9_00000030.l
	addq.l #4,a7
loc_3_0000068E:
	movea.l (a7)+,a2
	rts
loc_3_00000692:
	move.l $0004(a7),d0
	movea.l $0008(a7),a0
	pea.l $008C(a0)
	move.l d0,-(a7)
	jsr loc_3_00000656(pc)
	addq.l #8,a7
	rts
loc_3_000006A8:
	movem.l d2-d3/a2,-(a7)
	move.l $0010(a7),d2
	move.l #$10000,-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	pea.l $00A8.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_9_00000000.l
	movea.l d0,a2
	move.l a2,d3
	addq.l #8,a7
	beq.b loc_3_00000714
	pea.l $008E(a2)
	jsr loc_7_00000000.l
	pea.l $008C(a2)
	move.l d2,-(a7)
	jsr loc_1_0000004E.l
	tst.l d0
	lea.l $000C(a7),a7
	bne.b loc_3_000006F6
	pea.l $00A8.w	; KNOWN: arg +8 byteSize unsigned long
	move.l a2,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_9_00000018.l
	addq.l #8,a7
	bra.b loc_3_00000714
loc_3_000006F6:
	pea.l $00A8.w
	move.l a2,-(a7)
	pea.l $008C(a2)
	move.l d2,-(a7)
	jsr loc_3_0000071C.l
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_3_00000714
	move.l a2,d0
	bra.b loc_3_00000716
loc_3_00000714:
	moveq.l #0,d0
loc_3_00000716:
	movem.l (a7)+,d2-d3/a2
	rts
loc_3_0000071C:
	movem.l d2/a2,-(a7)
	move.l $000C(a7),d0
	movea.l $0010(a7),a2
	move.l $0014(a7),d2
	subq.w #1,(a2)
	bgt.b loc_3_00000746
	move.l a2,-(a7)
	move.l d0,-(a7)
	jsr loc_1_0000004E.l
	tst.l d0
	addq.l #8,a7
	bne.b loc_3_00000744
	moveq.l #0,d0
	bra.b loc_3_00000762
loc_3_00000744:
	subq.w #1,(a2)
loc_3_00000746:
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
loc_3_00000762:
	movem.l (a7)+,d2/a2
	rts
loc_3_00000768:
	movem.l d2-d4/a2,-(a7)
	move.l $0014(a7),d2
	move.l $0018(a7),d3
	move.l #$10000,-(a7)	; KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	pea.l $005E.w	; KNOWN: arg +4 byteSize unsigned long
	jsr loc_9_00000000.l
	move.l d0,d4
	addq.l #8,a7
	beq.b loc_3_000007E2
	move.l d4,d0
	moveq.l #78,d1
	add.l d1,d0
	movea.l d0,a2
	pea.l $0002(a2)
	jsr loc_7_00000000.l
	move.l a2,-(a7)
	move.l d2,-(a7)
	jsr loc_1_0000004E.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.b loc_3_000007E4
	pea.l $005E.w
	move.l d4,-(a7)
	move.l a2,-(a7)
	move.l d2,-(a7)
	jsr loc_3_0000071C(pc)
	tst.l d0
	lea.l $0010(a7),a7
	beq.b loc_3_000007E4
	move.l a2,-(a7)
	move.l d4,-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_3_00000124(pc)
	tst.l d0
	lea.l $0010(a7),a7
	bne.b loc_3_000007E2
	move.l a2,-(a7)
	move.l d2,-(a7)
	jsr loc_3_00000656(pc)
loc_3_000007E0:
	bra.b loc_3_000007F0
loc_3_000007E2:
	bra.b loc_3_000007F4
loc_3_000007E4:
	pea.l $005E.w	; KNOWN: arg +8 byteSize unsigned long
	move.l d4,-(a7)	; KNOWN: arg +4 memoryBlock APTR
	jsr loc_9_00000018.l
loc_3_000007F0:
	moveq.l #0,d4
	addq.l #8,a7
loc_3_000007F4:
	move.l d4,d0
	movem.l (a7)+,d2-d4/a2
	rts
loc_3_000007FC:
	move.l d2,-(a7)
	move.l $0008(a7),d2
	move.l $000C(a7),d1
	moveq.l #78,d0
	add.l d0,d1
	move.l d1,-(a7)
	move.l d2,-(a7)
	jsr loc_3_00000656(pc)
	addq.l #8,a7
	move.l (a7)+,d2
	rts
loc_3_00000818:
	movem.l d2-d4/a2-a3,-(a7)
	movea.l $0018(a7),a2
	move.l $001C(a7),d2
	move.l d2,-(a7)
	jsr loc_5_00000000.l
	move.l d0,d3
	move.l a2,d4
	addq.l #4,a7
	beq.b loc_3_0000085C
	bra.b loc_3_00000856
loc_3_00000836:
	move.l d3,-(a7)
	move.l d2,-(a7)
	move.l a3,-(a7)
	jsr loc_5_00000048.l
	tst.l d0
	lea.l $000C(a7),a7
	bne.b loc_3_00000856
	adda.l d3,a3
	cmpi.b #61,(a3)+
	bne.b loc_3_00000856
	move.l a3,d0
	bra.b loc_3_0000085E
loc_3_00000856:
	movea.l (a2)+,a3
	move.l a3,d0
	bne.b loc_3_00000836
loc_3_0000085C:
	moveq.l #0,d0
loc_3_0000085E:
	movem.l (a7)+,d2-d4/a2-a3
	rts
loc_3_00000864:
	movem.l d2-d5,-(a7)
	move.l $0014(a7),d2
	move.l $0018(a7),d3
	move.l d3,-(a7)
	jsr loc_5_00000000.l
	move.l d0,d5
	addq.l #4,a7
	bra.b loc_3_000008CA
loc_3_0000087E:
	pea.l $007C.w
	move.l d2,-(a7)
	jsr loc_5_00000010.l
	move.l d0,d4
	addq.l #8,a7
	beq.b loc_3_00000896
	move.l d4,d0
	sub.l d2,d0
	bra.b loc_3_000008A0
loc_3_00000896:
	move.l d2,-(a7)
	jsr loc_5_00000000.l
	addq.l #4,a7
loc_3_000008A0:
	cmp.l d5,d0
	bne.b loc_3_000008BE
	move.l d5,-(a7)
	move.l d3,-(a7)
	move.l d2,-(a7)
	jsr loc_5_00000048.l
	tst.l d0
	lea.l $000C(a7),a7
	bne.b loc_3_000008BE
	moveq.l #1,d2
	move.l d2,d0
	bra.b loc_3_000008D0
loc_3_000008BE:
	tst.l d4
	beq.b loc_3_000008C8
	move.l d4,d2
	addq.l #1,d2
	bra.b loc_3_000008CA
loc_3_000008C8:
	moveq.l #0,d2
loc_3_000008CA:
	tst.l d2
	bne.b loc_3_0000087E
	moveq.l #0,d0
loc_3_000008D0:
	movem.l (a7)+,d2-d5
	rts
loc_3_000008D6:
	movem.l d2-d4/a2-a4,-(a7)
	movea.l $001C(a7),a2
	movea.l $0020(a7),a3
	moveq.l #30,d4
	movea.l a3,a4
	clr.b $001E(a2)
	pea.l $0005.w
	pea.l loc_4_0000000C.l
	move.l a4,-(a7)
	jsr loc_5_00000048.l
	tst.l d0
	lea.l $000C(a7),a7
	beq.b loc_3_00000926
loc_3_00000904:
	pea.l loc_4_00000012.l
	move.l a2,-(a7)
	jsr loc_5_0000002C.l
	move.l d4,-(a7)
	move.l a3,-(a7)
	move.l a2,-(a7)
	jsr loc_5_0000006C.l
	lea.l $0014(a7),a7
	bra.w loc_3_000009B6
loc_3_00000926:
	addq.l #5,a4
	pea.l $0003.w
	pea.l loc_4_0000001C.l
	move.l a4,-(a7)
	jsr loc_5_00000048.l
	tst.l d0
	lea.l $000C(a7),a7
	bne.b loc_3_00000948
	moveq.l #1,d3
	addq.l #3,a4
	bra.b loc_3_00000992
loc_3_00000948:
	moveq.l #0,d3
	bra.b loc_3_0000095C
loc_3_0000094C:
	move.l d3,d0
	add.l d0,d0
	move.l d0,d1
	asl.l #2,d0
	add.l d1,d0
	add.l d2,d0
	move.l d0,d3
	addq.l #1,a4
loc_3_0000095C:
	move.b (a4),d0
	ext.w d0
	ext.l d0
	move.l d0,-(a7)
	jsr loc_3_000009BE.l
	move.l d0,d2
	addq.l #4,a7
	bge.b loc_3_0000094C
	tst.l d3
	beq.b loc_3_00000904
	pea.l $0004.w
	pea.l loc_4_00000020.l
	move.l a4,-(a7)
	jsr loc_5_00000048.l
	tst.l d0
	lea.l $000C(a7),a7
	bne.w loc_3_00000904
	addq.l #4,a4
loc_3_00000992:
	move.l d3,d0
	addq.l #1,d0
	move.l d0,-(a7)	; KNOWN: arg +12 PutChProc void (*)() code_ptr
	pea.l loc_4_00000026.l	; KNOWN: arg +8 DataStream APTR
	move.l a2,-(a7)	; KNOWN: arg +4 FormatString STRPTR string_ptr
	jsr loc_6_000000C8.l
	move.l d4,-(a7)
	move.l a4,-(a7)
	move.l a2,-(a7)
	jsr loc_5_0000006C.l
	lea.l $0018(a7),a7
loc_3_000009B6:
	move.l a2,d0
	movem.l (a7)+,d2-d4/a2-a4
	rts
loc_3_000009BE:
	move.l $0004(a7),d1
	moveq.l #48,d0
	cmp.l d1,d0
	bgt.b loc_3_000009D6
	moveq.l #57,d0
	cmp.l d1,d0
	blt.b loc_3_000009D6
	move.l d1,d0
	moveq.l #48,d1
	sub.l d1,d0
	bra.b loc_3_000009D8
loc_3_000009D6:
	moveq.l #-1,d0
loc_3_000009D8:
	rts
	dc.b $00,$00
    SECTION section_4,data
loc_4_00000000:
	dc.b ".info",$00	; string
loc_4_00000006:
	dc.b ".info",$00	; string
loc_4_0000000C:
	dc.b "copy ",$00	; string
loc_4_00000012:
	dc.b "copy of ",$00	; string
	dc.b $00
loc_4_0000001C:
	dc.b $6F,$66,$20,$00
loc_4_00000020:
	dc.b $20,$6F,$66,$20,$00,$00
loc_4_00000026:
	dc.b "copy %ld of ",$00	; string
	dc.b $00
    SECTION section_5,code
loc_5_00000000:
	movea.l $0004(a7),a0
	moveq.l #-1,d0
loc_5_00000006:
	tst.b (a0)+
	dbeq.w d0,loc_5_00000006
	not.l d0
	rts
loc_5_00000010:
	movea.l $0004(a7),a0
	move.l $0008(a7),d0
loc_5_00000018:
	move.b (a0)+,d1
	beq.b loc_5_00000026
	cmp.b d0,d1
	bne.b loc_5_00000018
	subq.l #1,a0
	move.l a0,d0
loc_5_00000024:
	rts
loc_5_00000026:
	moveq.l #0,d0
	bra.b loc_5_00000024
	dc.b $00,$00
loc_5_0000002C:
	movem.l $0004(a7),a0-a1
loc_5_00000032:
	move.b (a1)+,(a0)+
	bne.b loc_5_00000032
	rts
loc_5_00000038:
	movem.l $0004(a7),a0-a1
loc_5_0000003E:
	tst.b (a0)+
	bne.b loc_5_0000003E
	subq.l #1,a0
	bra.b loc_5_00000032
	dc.b $00,$00
loc_5_00000048:
	movem.l $0004(a7),a0-a1
	move.l $000C(a7),d0
loc_5_00000052:
	subq.l #1,d0
	blt.b loc_5_00000060
	move.b (a1)+,d1
	cmp.b (a0)+,d1
	bne.b loc_5_00000064
	tst.b d1
	bne.b loc_5_00000052
loc_5_00000060:
	moveq.l #0,d0
loc_5_00000062:
	rts
loc_5_00000064:
	moveq.l #1,d0
	bgt.b loc_5_00000062
	moveq.l #-1,d0
	rts
loc_5_0000006C:
	movem.l $0004(a7),a0-a1
	move.l $000C(a7),d0
loc_5_00000076:
	tst.b (a0)+
	beq.b loc_5_00000080
	subq.l #1,d0
	bgt.b loc_5_00000076
	bra.b loc_5_00000086
loc_5_00000080:
	subq.l #1,a0
	bsr.w loc_5_00000092
loc_5_00000086:
	rts
	dc.b $4C,$EF,$03,$00,$00,$04,$20,$2F,$00,$0C
loc_5_00000092:
	subq.l #1,d0
	blt.b loc_5_000000A2
	move.b (a1)+,(a0)+
	bne.b loc_5_00000092
loc_5_0000009A:
	subq.l #1,d0
	ble.b loc_5_000000A2
	clr.b (a0)+
	bra.b loc_5_0000009A
loc_5_000000A2:
	rts
    SECTION section_6,code
	dc.b $0C,$82,$00,$00,$FF,$FF,$6E,$18,$32,$41,$42,$41,$48,$41,$82,$C2
	dc.b $20,$01,$48,$41,$30,$09,$80,$C2,$32,$00,$42,$40,$48,$40,$4E,$75
	dc.b $20,$01,$42,$40,$48,$40,$48,$41,$42,$41,$22,$42,$74,$0F,$D2,$81
	dc.b $D1,$80,$B3,$C0,$6E,$04,$90,$89,$52,$41,$51,$CA,$FF,$F2,$4E,$75
loc_6_00000040:
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
	dc.b $2F,$02,$24,$01,$22,$00,$61,$98,$24,$1F,$4E,$75,$2F,$02,$24,$01
	dc.b $22,$00,$61,$8C,$20,$01,$24,$1F,$4E,$75,$2F,$02,$24,$01,$6C,$02
	dc.b $44,$82,$22,$00,$70,$00,$4A,$81,$6C,$04,$44,$81,$46,$80,$20,$40
	dc.b $61,$00,$FF,$6E,$34,$08,$67,$02,$44,$80,$24,$1F,$4E,$75,$2F,$02
	dc.b $20,$40,$70,$00,$24,$01,$6C,$04,$44,$82,$46,$80,$22,$08,$6C,$04
	dc.b $44,$81,$46,$80,$20,$40,$61,$00,$FF,$48,$24,$08,$67,$02,$44,$81
	dc.b $20,$01,$24,$1F,$4E,$75,$00,$00
loc_6_000000C8:
	movem.l a2-a4/a6,-(a7)
	movea.l $0014(a7),a3
	movea.l $0018(a7),a0
	lea.l $001C(a7),a1
	lea.l loc_6_000000EC(pc),a2
	movea.l $00000004.l,a6
	jsr _LVORawDoFmt(a6)
	movem.l (a7)+,a2-a4/a6
	rts
loc_6_000000EC:
	dc.b $16,$C0,$4E,$75
    SECTION section_7,code
loc_7_00000000:
	movea.l $0004(a7),a0
	move.l a0,(a0)
	addq.l #4,(a0)
	clr.l $0004(a0)
	move.l a0,$0008(a0)
	rts
	dc.b $00,$00
    SECTION section_8,code
loc_8_00000000:
	movem.l d2/a6,-(a7)
	movea.l h0dl_DOSBase.l,a6
	movem.l $000C(a7),d1-d2	; KNOWN: arg +4 name STRPTR string_ptr | KNOWN: arg +8 accessMode long dos.open.access_mode
	jsr _LVOOpen(a6)
	movem.l (a7)+,d2/a6
	rts
	dc.b $00,$00
loc_8_0000001C:
	move.l a6,-(a7)
	movea.l h0dl_DOSBase.l,a6
	move.l $0008(a7),d1	; KNOWN: arg +4 file BPTR
	jsr _LVOClose(a6)
	movea.l (a7)+,a6
	rts
loc_8_00000030:
	movem.l d2-d3/a6,-(a7)
	movea.l h0dl_DOSBase.l,a6
	movem.l $0010(a7),d1-d3	; KNOWN: arg +4 file BPTR | KNOWN: arg +8 buffer APTR | KNOWN: arg +12 length long
	jsr _LVORead(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
loc_8_0000004C:
	movem.l d2-d3/a6,-(a7)
	movea.l h0dl_DOSBase.l,a6
	movem.l $0010(a7),d1-d3	; KNOWN: arg +4 file BPTR | KNOWN: arg +8 buffer APTR | KNOWN: arg +12 length long
	jsr _LVOWrite(a6)
	movem.l (a7)+,d2-d3/a6
	rts
	dc.b $00,$00
    SECTION section_9,code
loc_9_00000000:
	move.l a6,-(a7)
	movea.l h0dl_ExecBase.l,a6
	movem.l $0008(a7),d0-d1	; KNOWN: arg +4 byteSize unsigned long | KNOWN: arg +8 attributes ULONG exec.allocmem.attributes
	jsr _LVOAllocMem(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_9_00000018:
	move.l a6,-(a7)
	movea.l h0dl_ExecBase.l,a6
	movea.l $0008(a7),a1	; KNOWN: arg +4 memoryBlock APTR
	move.l $000C(a7),d0	; KNOWN: arg +8 byteSize unsigned long
	jsr _LVOFreeMem(a6)
	movea.l (a7)+,a6
	rts
loc_9_00000030:
	move.l a6,-(a7)
	movea.l h0dl_ExecBase.l,a6
	movea.l $0008(a7),a0	; KNOWN: arg +4 entry ML
	jsr _LVOFreeEntry(a6)
	movea.l (a7)+,a6
	rts
loc_9_00000044:
	move.l a6,-(a7)
	movea.l h0dl_ExecBase.l,a6
	movem.l $0008(a7),a0-a1	; KNOWN: arg +4 list LH | KNOWN: arg +8 node LN
	jsr _LVOAddTail(a6)
	movea.l (a7)+,a6
	rts
	dc.b $00,$00
loc_9_0000005C:
	move.l a6,-(a7)
	movea.l h0dl_ExecBase.l,a6
	movea.l $0008(a7),a0	; KNOWN: arg +4 list LH
	jsr _LVORemTail(a6)
	movea.l (a7)+,a6
	rts
