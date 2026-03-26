; Generated disassembly -- vasm Motorola syntax
; Source: bin\MonAm302
; 35548 bytes, 385 entities, 1492 blocks

; LVO offsets: graphics.library (FD-derived)
_LVOSetDrMd	EQU	-354
_LVOSetAPen	EQU	-342
_LVOPolyDraw	EQU	-336
_LVORectFill	EQU	-306
_LVOMove	EQU	-240
_LVOText	EQU	-60

; LVO offsets: intuition.library (FD-derived)
_LVOActivateWindow	EQU	-450
_LVOSetPointer	EQU	-270
_LVOScreenToFront	EQU	-252
_LVOOpenWindow	EQU	-204
_LVOOpenScreen	EQU	-198
_LVOGetPrefs	EQU	-132
_LVOCloseWindow	EQU	-72
_LVOCloseScreen	EQU	-66

; OS function argument constants
MEMF_PUBLIC	EQU	1
MODE_OLDFILE	EQU	1005
OFFSET_BEGINNING	EQU	-1
OFFSET_CURRENT	EQU	0
OFFSET_END	EQU	1

; App memory offsets (base register A6)
app_exec_base_0054	EQU	84
app_exec_base_005C	EQU	92
app_createproc_stacksize	EQU	178
app_exec_base_00BA	EQU	186
app_intuition_base	EQU	190
app_dos_base	EQU	194
app_graphics_base	EQU	198
app_closescreen_screen	EQU	206
app_setapen_rp	EQU	210
app_rectfill_xmax	EQU	214
app_rectfill_ymax	EQU	216
app_createproc_process	EQU	266
app_addport_port	EQU	274
app_freesignal_signalnum	EQU	289
app_findtask_task	EQU	290
app_freemem_memoryblock	EQU	310
app_read_length	EQU	314
app_write_file	EQU	400
app_allocmem_memoryblock	EQU	1416
app_closewindow_window	EQU	1460
app_console_device_iorequest	EQU	2072
app_rawkeyconvert_buffer	EQU	2150
app_polydraw_polytable	EQU	2164

; Absolute symbols
AbsExecBase	EQU	$4

    INCLUDE "devices/console.i"
    INCLUDE "dos/dos_lib.i"
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/io.i"
    INCLUDE "exec/ports.i"
    INCLUDE "graphics/gfxbase.i"
    INCLUDE "intuition/intuition.i"
    INCLUDE "intuition/intuitionbase.i"
    INCLUDE "intuition/screens.i"

    section code,code

init_app:
    bra.w loc_0094
    dc.l    $4d4f4e20
    dc.l    dat_0024
    dc.b    $00,$00
    dc.w    $0054
dat_0010:
    dc.w    $0000
    dc.b    $00
    dc.b    $00
pcref_0014:
    dcb.b   4,0
pcref_0018:
    dc.l    init_app
    dcb.b   4,0
dat_0020:
    dcb.b   4,0
dat_0024:
    dc.b    $00
pcref_0025:
    dc.b    $ff,$ff
dat_0027:
    dc.b    $00,$00,$20
dat_002a:
    dc.b    $08
pcref_0032:
pcref_0072:
    dc.b    $ff,$ff,$ff,$00,$00,$01
    dc.b    "$VER: MonAm 3.02 (31.1.92)",0
    dc.b    $00
loc_0094:
    movem.l d0/a0,sub_88ec
    move.l #$e1a,d0 ; AllocMem: byteSize
    move.l #$10001,d1 ; AllocMem: attributes
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_00b0:
    movea.l d0,a6
    tst.l d0
    bne.s loc_00ba
loc_00b6:
    moveq #103,d0
    rts
loc_00ba:
    cmpi.l #$44455620,dat_0010 ; 'DEV '
    seq 354(a6) ; app+$162
    bne.s loc_00d0
loc_00ca:
    move.l pcref_0014(pc),350(a6) ; app+$15E
loc_00d0:
    move.l sp,182(a6) ; app+$B6
    move.l 4(sp),app_createproc_stacksize(a6)
    moveq #33,d0 ; OpenLibrary: version
    lea openlibrary_libname_81D9,a1 ; OpenLibrary: libName
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOOpenLibrary(a6) ; app-$228
loc_00ec:
    movea.l (sp)+,a6
    move.l d0,app_intuition_base(a6)
    beq.s loc_0128
loc_00f4:
    moveq #29,d0 ; OpenLibrary: version
    lea openlibrary_libname_81F7,a1 ; OpenLibrary: libName
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOOpenLibrary(a6) ; app-$228
loc_0106:
    movea.l (sp)+,a6
    move.l d0,app_graphics_base(a6)
    beq.s loc_0128
loc_010e:
    moveq #29,d0 ; OpenLibrary: version
    lea openlibrary_libname_81EB,a1 ; OpenLibrary: libName
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOOpenLibrary(a6) ; app-$228
loc_0120:
    movea.l (sp)+,a6
    move.l d0,app_dos_base(a6)
    bne.s loc_012e
loc_0128:
    moveq #122,d4
    bra.w loc_0448
loc_012e:
    lea opendevice_devname,a0 ; OpenDevice: devName
    moveq #-1,d0 ; OpenDevice: unitNumber
    lea app_console_device_iorequest(a6),a1 ; OpenDevice: iORequest
    moveq #0,d1 ; OpenDevice: flags
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOOpenDevice(a6) ; app-$1BC
loc_0146:
    movea.l (sp)+,a6
    tst.l d0
    bne.w loc_0446
loc_014e:
    suba.l a1,a1 ; FindTask: name
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFindTask(a6) ; app-$126
loc_015a:
    movea.l (sp)+,a6
    move.l d0,dat_8956
    move.l d0,app_addport_port+MP_SIGTASK(a6)
    moveq #-1,d0 ; AllocSignal: signalNum
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocSignal(a6) ; app-$14A
loc_0172:
    movea.l (sp)+,a6
    move.b d0,app_addport_port+MP_SIGBIT(a6)
    moveq #-1,d0 ; AllocSignal: signalNum
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocSignal(a6) ; app-$14A
loc_0184:
    movea.l (sp)+,a6
    move.b d0,dat_895e
    lea app_addport_port(a6),a1 ; AddPort: port
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAddPort(a6) ; app-$162
loc_019a:
    movea.l (sp)+,a6
    movea.l AbsExecBase,a0
    move.w 296(a0),d0
    btst #4,d0
    sne dat_8906
    andi.b #$3,d0
    beq.s loc_01e8
loc_01b4:
    lea pcref_159c(pc),a1
    move.l a1,dat_1536
    cmp.b #$1,d0
    bne.s loc_01ce
loc_01c4:
    move.w #$4e71,dat_15b2
    bra.s loc_01e8
loc_01ce:
    lea supervisor_userfunc(pc),a5 ; Supervisor: userFunc
    moveq #0,d0
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSupervisor(a6) ; app-$1E
loc_01de:
    movea.l (sp)+,a6
    andi.b #$1,d0
    move.b d0,309(a6) ; app+$135
loc_01e8:
    bsr.w sub_0526
loc_01ec:
    link a5,#-186
    movea.l sp,a0 ; GetPrefs: PrefBuffer
    move.l #$ba,d0 ; GetPrefs: Size
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOGetPrefs(a6) ; app-$84
loc_0202:
    movea.l (sp)+,a6
    tst.b 185(sp)
    sne 327(a6) ; app+$147
    unlk a5
    bsr.w env_devpac_monam_prefs
loc_0212:
    movea.l app_graphics_base(a6),a0
    movem.w gb_NormalDisplayRows(a0),d0-d1
    move.w #$8000,d2
    move.b dat_0027(pc),d3
    beq.s loc_022c
loc_0226:
    ori.w #$4,d2
    add.w d0,d0
loc_022c:
    lea openscreen_newscreen(pc),a0 ; OpenScreen: NewScreen
    move.w d1,ns_Width(a0)
    move.w d0,ns_Height(a0)
    move.w d2,ns_ViewModes(a0)
    move.b dat_0027(pc),d0
    move.b 327(a6),d1 ; app+$147
    eor.b d1,d0
    moveq #1,d1
    and.l d1,d0
    eor.b d1,d0
    move.l d0,dat_04ba
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOOpenScreen(a6) ; app-$C6
loc_025c:
    movea.l (sp)+,a6
    move.l d0,app_closescreen_screen(a6)
    beq.w loc_03ea
loc_0266:
    movea.l d0,a1
    lea openwindow_newwindow(pc),a0 ; OpenWindow: NewWindow
    move.l a1,nw_Screen(a0)
    moveq #1,d1
    add.b sc_BarHeight(a1),d1
    move.l pcref_0496(pc),nw_Width(a0)
    move.w d1,nw_TopEdge(a0)
    sub.w nw_Height(a0),6(a0)
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOOpenWindow(a6) ; app-$CC
loc_028e:
    movea.l (sp)+,a6
    move.l d0,app_closewindow_window(a6)
    beq.w loc_03da
loc_0298:
    movea.l #init_app,a0
    jsr call_setpointer
loc_02a4:
    bsr.w sub_3e98
loc_02a8:
    bsr.w sub_5cee
loc_02ac:
    move.b #$78,329(a6) ; app+$149
    st 331(a6) ; app+$14B
    sf 228(a6) ; app+$E4
    sf 326(a6) ; app+$146
    move.l #$ffffffff,318(a6) ; app+$13E
    clr.l dat_88f6
    clr.b dat_88f5
    lea 16(a6),a0 ; app+$10
    moveq #15,d0
loc_02d8:
    clr.l (a0)+
    dbf d0,loc_02d8
loc_02de:
    clr.l 80(a6) ; app+$50
    clr.w 90(a6) ; app+$5A
    clr.w 88(a6) ; app+$58
    movea.l AbsExecBase,a0
    move.l a0,app_exec_base_00BA(a6)
    move.l a0,app_exec_base_005C(a6)
    move.l a0,app_exec_base_0054(a6)
    bsr.w sub_3d66
loc_02fe:
    bsr.w sub_3f58
loc_0302:
    lea 1464(a6),a3 ; app+$5B8
    bsr.w call_close_7fb8
loc_030a:
    bsr.w call_rectfill
loc_030e:
    bsr.w sub_09b8
loc_0312:
    lea pcref_0032(pc),a0
    tst.b (a0)
    beq.s loc_031e
loc_031a:
    bsr.w call_ioerr_74ec
loc_031e:
    pea pcref_0554(pc)
    move.l 350(a6),d0 ; app+$15E
    beq.s loc_033e
loc_0328:
    lea str_0336(pc),a3
    movea.l dat_88f0,a4
    bra.w loc_556a
str_0336:
    dc.b    "MEMTASK",0
loc_033e:
    movem.l sub_88ec,d0/a0
    lea 0(a0,d0.l),a1
loc_034a:
    cmpi.b #$20,-(a1)
    dbhi d0,loc_034a
loc_0352:
    clr.b 1(a1)
    cmpa.l a0,a1
    bcs.w loc_550e
loc_035c:
    st d0
loc_035e:
    cmpi.b #$20,(a0)+
    beq.s loc_035e
loc_0364:
    cmpi.b #$22,-1(a0)
    beq.s loc_0370
loc_036c:
    subq.l #1,a0
    sf d0
loc_0370:
    movea.l a0,a3
loc_0372:
    move.b (a0)+,d1
    beq.s loc_0396
loc_0376:
    tst.b d0
    beq.s loc_0382
loc_037a:
    cmp.b #$22,d1
    bne.s loc_0372
loc_0380:
    bra.s loc_0388
loc_0382:
    cmp.b #$20,d1
    bne.s loc_0372
loc_0388:
    clr.b -1(a0)
loc_038c:
    move.b (a0)+,d1
    beq.s loc_0396
loc_0390:
    cmp.b #$20,d1
    beq.s loc_038c
loc_0396:
    lea -1(a0),a4
    bra.w loc_554e
call_closedevice:
    bsr.w call_close_752c
loc_03a2:
    movea.l 182(a6),sp ; app+$B6
    move.l app_read_length(a6),d0
    beq.s loc_03bc
loc_03ac:
    movea.l app_freemem_memoryblock(a6),a1 ; FreeMem: memoryBlock
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_03ba:
    movea.l (sp)+,a6
loc_03bc:
    bsr.w call_unloadseg_7740
loc_03c0:
    jsr sub_81b6
loc_03c6:
    bsr.w sub_0528
loc_03ca:
    movea.l app_closewindow_window(a6),a0 ; CloseWindow: window
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOCloseWindow(a6) ; app-$48
loc_03d8:
    movea.l (sp)+,a6
loc_03da:
    movea.l app_closescreen_screen(a6),a0 ; CloseScreen: Screen
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOCloseScreen(a6) ; app-$42
loc_03e8:
    movea.l (sp)+,a6
loc_03ea:
    move.b 309(a6),d0 ; app+$135
    beq.s loc_0400
loc_03f0:
    lea supervisor_userfunc(pc),a5 ; Supervisor: userFunc
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSupervisor(a6) ; app-$1E
loc_03fe:
    movea.l (sp)+,a6
loc_0400:
    lea app_addport_port(a6),a1 ; RemPort: port
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVORemPort(a6) ; app-$168
loc_040e:
    movea.l (sp)+,a6
    moveq #0,d0
    move.b app_addport_port+MP_SIGBIT(a6),d0 ; FreeSignal: signalNum
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeSignal(a6) ; app-$150
loc_0420:
    movea.l (sp)+,a6
    moveq #0,d0
    move.b dat_895e,d0 ; FreeSignal: signalNum
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeSignal(a6) ; app-$150
loc_0434:
    movea.l (sp)+,a6
    lea app_console_device_iorequest(a6),a1 ; CloseDevice: ioRequest
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOCloseDevice(a6) ; app-$1C2
loc_0444:
    movea.l (sp)+,a6
loc_0446:
    moveq #0,d4
loc_0448:
    move.l app_dos_base(a6),d0
    bsr.s call_closelibrary
loc_044e:
    move.l app_graphics_base(a6),d0
    bsr.s call_closelibrary
loc_0454:
    move.l app_intuition_base(a6),d0
    bsr.s call_closelibrary
loc_045a:
    move.l #$e1a,d0 ; FreeMem: byteSize
    movea.l a6,a1 ; FreeMem: memoryBlock
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_046c:
    movea.l (sp)+,a6
    move.l d4,d0
    rts
call_closelibrary:
    beq.s loc_0482
loc_0474:
    movea.l d0,a1 ; CloseLibrary: library
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOCloseLibrary(a6) ; app-$19E
loc_0480:
    movea.l (sp)+,a6
loc_0482:
    rts
    dc.l    sub_048c
    dc.b    $00,$08,$00,$00
sub_048c:
    dc.b    "topaz",0
openscreen_newscreen:
    dcb.b   4,0
pcref_0496:
    dc.w    $0280,$00c8
    dc.b    $00,$01,$00,$01
    dc.w    $8000
    dc.b    $10,$0f
    dcb.b   4,0
    dc.l    dat_04fa
    dcb.b   8,0
    dc.l    dat_04b6
dat_04b6:
    dc.b    $80,$00,$00,$2c
dat_04ba:
    dc.b    $00,$00,$00,$01
openwindow_newwindow:
dat_04fa:
    dc.b    $6e,$41
sub_04fe:
; --- unverified ---
    blt.s sub_0520
hint_0500:
    dc.b    "versio"
hint_0506:
; --- unverified ---
    bgt.s sub_0528
hint_0508:
    dc.b    "3.02  "
    dc.b    "Copyright "
    dc.b    $a9
    dc.b    " 1992 H"
sub_0520:
    dc.b    $69,$53
hint_0522:
; --- unverified ---
    ble.s hint_058a
    dc.b    $74,$00
sub_0526:
    rts
sub_0528:
    rts
sub_052a:
    lea 1464(a6),a3 ; app+$5B8
    move.w #$1,10(a3)
    move.w 238(a6),12(a3) ; app+$EE
    bra.w loc_5836
hint_053e:
    dc.b    $4a
hint_053f:
    dc.b    $2e,$00,$e5
hint_0544:
; --- unverified ---
    movem.l d1/a3,-(sp)
    bsr.s sub_052a
hint_054a:
    dc.b    $51,$ee,$00,$e5,$4c,$df,$08,$02
hint_0552:
; --- unverified ---
    rts
pcref_0554:
; --- unverified ---
    bsr.w sub_4124
hint_0558:
; --- unverified ---
    bmi.s hint_0590
hint_055a:
; --- unverified ---
    bsr.s hint_053e
hint_055c:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_0584
hint_0562:
; --- unverified ---
    cmp.b #$88,d1
    beq.s hint_058a
hint_0568:
; --- unverified ---
    cmp.b #$87,d1
    beq.w hint_4f2a
hint_0570:
; --- unverified ---
    bra.w hint_05c0
hint_0574:
    dc.b    $20
hint_0575:
    dc.b    $2e,$00,$de
hint_057a:
; --- unverified ---
    movea.l d0,a3
    bsr.w hint_06ac
hint_0580:
; --- unverified ---
    beq.s pcref_0554
hint_0582:
; --- unverified ---
    bra.s hint_055c
hint_0584:
; --- unverified ---
    bsr.w hint_0b40
hint_0588:
; --- unverified ---
    bra.s pcref_0554
hint_058a:
; --- unverified ---
    bsr.w hint_0b70
hint_058e:
; --- unverified ---
    bra.s pcref_0554
hint_0590:
; --- unverified ---
    bsr.s hint_053e
hint_0592:
; --- unverified ---
    move.l 222(a6),d0 ; app+$DE
    beq.s pcref_0554
hint_0598:
; --- unverified ---
    movea.l d0,a3
    cmp.b #$5a,d1
    beq.w hint_0636
hint_05a2:
; --- unverified ---
    cmp.b #$3a,d1
    bcs.s hint_05b6
hint_05a8:
; --- unverified ---
    cmp.b #$48,d1
    beq.w hint_4f2a
hint_05b0:
; --- unverified ---
    bsr.w hint_0720
hint_05b4:
; --- unverified ---
    bra.s pcref_0554
hint_05b6:
; --- unverified ---
    subi.b #$30,d1
    bsr.w sub_0ae8
hint_05be:
; --- unverified ---
    bra.s pcref_0554
hint_05c0:
; --- unverified ---
    move.b d1,d0
    cmp.b #$41,d0
    bcs.s hint_05cc
hint_05c8:
    dc.b    $02,$00,$00,$df
hint_05cc:
    dc.b    $41,$fa,$3d,$a4
hint_05d0:
; --- unverified ---
    move.b (a0)+,d3
    move.b (a0)+,d2
    beq.s hint_0574
hint_05d6:
; --- unverified ---
    cmp.b d0,d2
    beq.s hint_05de
hint_05da:
; --- unverified ---
    addq.w #2,a0
    bra.s hint_05d0
hint_05de:
; --- unverified ---
    tst.b d3
    beq.s hint_062a
hint_05e2:
; --- unverified ---
    subq.b #1,d3
    beq.s hint_060e
hint_05e6:
; --- unverified ---
    subq.b #1,d3
    beq.s hint_0604
hint_05ea:
; --- unverified ---
    subq.b #1,d3
    beq.s hint_05fa
hint_05ee:
; --- unverified ---
    cmpi.b #$1,308(a6) ; app+$134
    beq.s hint_062a
hint_05f6:
; --- unverified ---
    moveq #33,d1
    bra.s hint_0616
hint_05fa:
; --- unverified ---
    tst.b 308(a6) ; app+$134
    beq.s hint_062a
hint_0600:
; --- unverified ---
    moveq #34,d1
    bra.s hint_0616
hint_0604:
; --- unverified ---
    tst.b 308(a6) ; app+$134
    bne.s hint_062a
hint_060a:
; --- unverified ---
    moveq #35,d1
    bra.s hint_0616
hint_060e:
; --- unverified ---
    moveq #36,d1
    tst.b 308(a6) ; app+$134
    bmi.s hint_062a
hint_0616:
; --- unverified ---
    move.w d1,-(sp)
    bsr.w sub_052a
hint_061c:
; --- unverified ---
    move.w (sp)+,d1
    bsr.w sub_6a5a
hint_0622:
; --- unverified ---
    st 229(a6) ; app+$E5
    bra.w pcref_0554
hint_062a:
; --- unverified ---
    adda.w (a0),a0
    movea.l 222(a6),a3 ; app+$DE
    jsr (a0) ; unresolved_indirect_hint:ind
hint_0632:
; --- unverified ---
    bra.w pcref_0554
hint_0636:
; --- unverified ---
    move.l a3,-(sp)
    lea 1464(a6),a3 ; app+$5B8
    bsr.w call_rectfill
hint_0640:
; --- unverified ---
    lea 1856(a6),a3 ; app+$740
    movem.w 2154(a6),d0-d4 ; app+$86A
    bsr.w sub_5690
hint_064e:
    dc.b    $50,$eb,$00,$14,$24,$5f,$41,$eb,$00,$16,$43,$ea,$00,$16,$70,$19
hint_065e:
; --- unverified ---
    move.w (a1)+,(a0)+
    dbf d0,hint_065e
hint_0664:
; --- unverified ---
    st d7
    st d4
    bsr.w sub_5b56
hint_066c:
; --- unverified ---
    move.b 53(a3),-(sp)
    bsr.w sub_5dd2
hint_0674:
; --- unverified ---
    move.b (sp)+,d0
    cmpi.b #$4,52(a3)
    bne.s hint_0682
hint_067e:
    dc.b    $17,$40,$00,$35
hint_0682:
; --- unverified ---
    bsr.w graphics_dispatch
hint_0686:
; --- unverified ---
    bsr.w sub_4120
hint_068a:
; --- unverified ---
    bmi.s hint_06a0
hint_068c:
; --- unverified ---
    cmp.b #$1b,d1
    beq.s hint_0698
hint_0692:
; --- unverified ---
    bsr.s hint_06ac
hint_0694:
; --- unverified ---
    beq.s hint_0686
hint_0696:
; --- unverified ---
    bra.s hint_068c
hint_0698:
; --- unverified ---
    bsr.w sub_5d9c
hint_069c:
; --- unverified ---
    bra.w pcref_0554
hint_06a0:
; --- unverified ---
    cmp.b #$5a,d1
    beq.s hint_0698
hint_06a6:
; --- unverified ---
    bsr.w hint_0720
hint_06aa:
; --- unverified ---
    bra.s hint_0686
hint_06ac:
; --- unverified ---
    pea pcref_070e(pc)
    movea.l 62(a3),a0
    cmp.b #$80,d1
    beq.s hint_06fa
hint_06ba:
; --- unverified ---
    cmp.b #$82,d1
    beq.s hint_06fe
hint_06c0:
; --- unverified ---
    cmp.b #$83,d1
    beq.s hint_0702
hint_06c6:
; --- unverified ---
    cmp.b #$81,d1
    beq.s hint_06f6
hint_06cc:
; --- unverified ---
    cmp.b #$84,d1
    beq.s hint_0706
hint_06d2:
; --- unverified ---
    cmp.b #$85,d1
    beq.s hint_070a
hint_06d8:
; --- unverified ---
    cmp.b #$89,d1
    beq.s hint_0706
hint_06de:
; --- unverified ---
    cmp.b #$8a,d1
    beq.s hint_070a
hint_06e4:
; --- unverified ---
    tst.w 1860(a6) ; app+$744
    beq.s hint_06f0
hint_06ea:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_06f6
hint_06f0:
; --- unverified ---
    addq.l #4,sp
    moveq #0,d1
    rts
hint_06f6:
; --- unverified ---
    jmp 6(a0) ; unresolved_indirect_hint:disp
hint_06fa:
; --- unverified ---
    jmp 4(a0) ; unresolved_indirect_hint:disp
hint_06fe:
; --- unverified ---
    jmp 8(a0) ; unresolved_indirect_hint:disp
hint_0702:
; --- unverified ---
    jmp 10(a0) ; unresolved_indirect_hint:disp
hint_0706:
; --- unverified ---
    jmp 12(a0) ; unresolved_indirect_hint:disp
hint_070a:
; --- unverified ---
    jmp 14(a0) ; unresolved_indirect_hint:disp
pcref_070e:
; --- unverified ---
    bmi.s hint_0712
hint_0710:
; --- unverified ---
    rts
hint_0712:
; --- unverified ---
    clr.l 10(a3)
    movea.l 62(a3),a0
    jsr (a0) ; unresolved_indirect_hint:ind
hint_071c:
; --- unverified ---
    moveq #0,d1
    rts
hint_0720:
; --- unverified ---
    cmp.b #$41,d1
    beq.w hint_0b72
hint_0728:
; --- unverified ---
    cmp.b #$42,d1
    beq.w hint_0828
hint_0730:
; --- unverified ---
    cmp.b #$45,d1
    beq.w hint_07f6
hint_0738:
; --- unverified ---
    cmp.b #$47,d1
    beq.w hint_0bba
hint_0740:
; --- unverified ---
    cmp.b #$4c,d1
    beq.w sub_0d0e
hint_0748:
; --- unverified ---
    cmp.b #$4f,d1
    beq.w hint_12ac
hint_0750:
; --- unverified ---
    cmp.b #$50,d1
    beq.w hint_08ee
hint_0758:
; --- unverified ---
    cmp.b #$52,d1
    beq.s hint_0778
hint_075e:
; --- unverified ---
    cmp.b #$53,d1
    beq.w hint_0bf8
hint_0766:
; --- unverified ---
    cmp.b #$54,d1
    beq.w sub_10b2
hint_076e:
; --- unverified ---
    cmp.b #$57,d1
    beq.w hint_0bfc
hint_0776:
; --- unverified ---
    rts
hint_0778:
; --- unverified ---
    move.l a3,-(sp)
    moveq #4,d3
    lea 32310(pc),a0
    bsr.w sub_1a7e
hint_0784:
; --- unverified ---
    bsr.w loc_59c2
hint_0788:
; --- unverified ---
    bne.s hint_07d2
hint_078a:
; --- unverified ---
    tst.b (a4)
    beq.s hint_07d2
hint_078e:
    dc.b    $24,$4c
hint_0790:
; --- unverified ---
    move.b (a2)+,d1
    beq.s hint_0784
hint_0794:
; --- unverified ---
    cmp.b #$3d,d1
    bne.s hint_0790
hint_079a:
; --- unverified ---
    lea 2772(a6),a1 ; app+$AD4
    move.l a2,d2
    sub.l a1,d2
    subq.w #1,d2
    bsr.w loc_71f2
hint_07a8:
; --- unverified ---
    bne.s hint_0784
hint_07aa:
; --- unverified ---
    movem.l a0/a4,-(sp)
    movea.l a2,a4
    bsr.w hint_6b5c
hint_07b4:
; --- unverified ---
    movem.l (sp)+,a0/a4
    bne.s hint_0784
hint_07ba:
; --- unverified ---
    move.l d2,(a0)
    move.l a0,-(sp)
    bsr.w sub_5d9c
hint_07c2:
; --- unverified ---
    move.l (sp)+,d2
    tst.w 1860(a6) ; app+$744
    bne.s hint_07ce
hint_07ca:
; --- unverified ---
    bsr.w sub_5ede
hint_07ce:
; --- unverified ---
    movea.l (sp)+,a3
    rts
hint_07d2:
; --- unverified ---
    bsr.w sub_5d9c
hint_07d6:
; --- unverified ---
    movea.l (sp)+,a3
    rts
hint_07da:
; --- unverified ---
    move.l a3,-(sp)
    lea 1856(a6),a3 ; app+$740
    tst.w 4(a3)
    bne.s hint_07ee
hint_07e6:
; --- unverified ---
    bsr.w sub_5ede
hint_07ea:
; --- unverified ---
    movea.l (sp)+,a3
    rts
hint_07ee:
; --- unverified ---
    bsr.w graphics_dispatch
hint_07f2:
; --- unverified ---
    movea.l (sp)+,a3
    rts
hint_07f6:
; --- unverified ---
    move.b 52(a3),d0
    cmp.b #$2,d0
    beq.w hint_0778
hint_0802:
; --- unverified ---
    cmp.b #$1,d0
    beq.w hint_6054
hint_080a:
; --- unverified ---
    cmp.b #$4,d0
    beq.s hint_0812
hint_0810:
; --- unverified ---
    rts
hint_0812:
; --- unverified ---
    eori.b #$c,53(a3)
    move.b 53(a3),dat_002a
    bsr.w call_rectfill
hint_0824:
; --- unverified ---
    bra.w graphics_dispatch
hint_0828:
; --- unverified ---
    lea str_863f(pc),a0
    bsr.w hint_0834
hint_0830:
; --- unverified ---
    bne.s hint_07da
hint_0832:
; --- unverified ---
    rts
hint_0834:
; --- unverified ---
    move.l a3,-(sp)
    moveq #4,d3
    bsr.w sub_1a7e
hint_083c:
; --- unverified ---
    bsr.w loc_59c2
hint_0840:
; --- unverified ---
    bne.s hint_08a4
hint_0842:
; --- unverified ---
    tst.b (a4)
    beq.s hint_08a4
hint_0846:
; --- unverified ---
    bsr.w sub_6b70
hint_084a:
; --- unverified ---
    beq.s hint_0856
hint_084c:
; --- unverified ---
    bsr.w sub_5e54
hint_0850:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bra.s hint_083c
hint_0856:
; --- unverified ---
    move.l d2,d5
    moveq #1,d2
    tst.b d1
    beq.s hint_088c
hint_085e:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_084c
hint_0864:
; --- unverified ---
    move.b (a4)+,d1
    cmp.b #$3f,d1
    beq.s hint_08ae
hint_086c:
; --- unverified ---
    cmp.b #$2a,d1
    beq.s hint_08c0
hint_0872:
; --- unverified ---
    cmp.b #$3d,d1
    beq.s hint_08cc
hint_0878:
; --- unverified ---
    cmp.b #$2d,d1
    bne.s hint_0882
hint_087e:
; --- unverified ---
    tst.b (a4)
    beq.s hint_08dc
hint_0882:
; --- unverified ---
    bsr.w loc_6b72
hint_0886:
; --- unverified ---
    bne.s hint_084c
hint_0888:
; --- unverified ---
    tst.b d1
    bne.s hint_084c
hint_088c:
; --- unverified ---
    move.l d2,d6
    bsr.w sub_5d9c
hint_0892:
    dc.b    $24,$06,$76,$01
hint_0896:
; --- unverified ---
    movea.l d5,a1
    bsr.w too_many_breakpoints
hint_089c:
; --- unverified ---
    bne.s hint_08a8
hint_089e:
; --- unverified ---
    movea.l (sp)+,a3
    moveq #1,d0
    rts
hint_08a4:
; --- unverified ---
    bsr.w sub_5d9c
hint_08a8:
; --- unverified ---
    movea.l (sp)+,a3
    moveq #0,d0
    rts
hint_08ae:
; --- unverified ---
    bsr.w sub_6b38
hint_08b2:
; --- unverified ---
    bne.s hint_084c
hint_08b4:
; --- unverified ---
    move.l a4,-(sp)
    bsr.w sub_5d9c
hint_08ba:
; --- unverified ---
    movea.l (sp)+,a4
    moveq #4,d3
    bra.s hint_0896
hint_08c0:
; --- unverified ---
    tst.b (a4)+
    bne.s hint_084c
hint_08c4:
; --- unverified ---
    bsr.w sub_5d9c
hint_08c8:
; --- unverified ---
    moveq #3,d3
    bra.s hint_0896
hint_08cc:
; --- unverified ---
    tst.b (a4)+
    bne.w hint_084c
hint_08d2:
; --- unverified ---
    bsr.w sub_5d9c
hint_08d6:
; --- unverified ---
    moveq #2,d3
    moveq #0,d2
    bra.s hint_0896
hint_08dc:
; --- unverified ---
    bsr.w sub_5d9c
hint_08e0:
; --- unverified ---
    movea.l d5,a1
    bsr.w sub_3e3c
hint_08e6:
; --- unverified ---
    bne.s hint_08a8
hint_08e8:
; --- unverified ---
    bsr.w sub_3e6e
hint_08ec:
; --- unverified ---
    bra.s hint_089e
hint_08ee:
; --- unverified ---
    bsr.w sub_75ac
hint_08f2:
; --- unverified ---
    bne.s hint_08fc
hint_08f4:
; --- unverified ---
    lea str_867f(pc),a0
    bra.w sub_1ad6
hint_08fc:
; --- unverified ---
    st 228(a6) ; app+$E4
    bsr.w graphics_dispatch
hint_0904:
; --- unverified ---
    sf 228(a6) ; app+$E4
    rts
dat_090a:
    dc.l    dat_095e
    dc.b    $e9,$05
    dc.l    dat_0964
    dc.b    $ed,$00
    dc.l    dat_096a
    dc.b    $e0,$0d
    dc.l    dat_0970
    dc.b    $09,$e5
    dc.l    dat_0976
    dc.b    $0d,$e0
    dc.l    dat_097c
    dc.b    $00,$ed
    dc.l    dat_0982
    dc.b    $a9,$65
    dc.l    dat_0989
    dc.b    $ad,$60
    dc.l    dat_0990
    dc.b    $a0,$6d
    dc.l    dat_0997
    dc.b    $b0,$65
    dc.l    dat_099e
    dc.b    $a9,$70
    dc.l    dat_09a5
    dc.b    $b0,$70
    dc.l    dat_09ac
    dc.b    $f0,$00
    dc.l    dat_09b2
    dc.b    $00,$f0
dat_095e:
    dc.b    $8c,$46,$51,$e6,$72,$00
dat_0964:
    dc.b    $8c,$47,$50,$e7
    dc.b    $f0,$00
dat_096a:
    dc.b    $8c,$48,$d0,$e8,$70,$00
dat_0970:
    dc.b    $c6,$54
    dc.b    $ad,$66,$75,$00
dat_0976:
    dc.b    $c7,$53
    dc.b    $ad,$67,$f3,$00
dat_097c:
    dc.b    $c8,$d3
    dc.b    $ad,$68,$73,$00
dat_0982:
    dc.b    $89,$40,$57,$aa
    dc.b    $63,$78
hint_0988:
    dc.b    $00
dat_0989:
    dc.b    $89,$41,$56,$aa,$64
hint_098f:
    dc.b    $00
dat_0990:
    dc.b    $89,$42,$d6,$aa,$65
hint_0996:
    dc.b    $00
dat_0997:
    dc.b    $86,$4c,$d6,$ab,$63
    dc.b    $00
dat_099e:
    dc.b    $8b,$40,$57,$a6,$6d,$f6
hint_09a4:
    dc.b    $00
dat_09a5:
    dc.b    $8a,$4c,$da,$a9,$6d
hint_09ab:
    dc.b    $00
dat_09ac:
    dc.b    $81,$4b,$d1,$eb,$f2
    dc.b    $00
dat_09b2:
    dc.b    $cb,$d4
    dc.b    $a5,$6b,$f5,$00
sub_09b8:
    lea 1560(a6),a3 ; app+$618
    move.l a3,222(a6) ; app+$DE
    lea 1486(a6),a3 ; app+$5CE
    moveq #1,d0
    move.w d0,242(a6) ; app+$F2
    move.w 220(a6),d1 ; app+$DC
    move.w 236(a6),d2 ; app+$EC
    subq.w #2,d2
    move.w d2,254(a6) ; app+$FE
    move.w #$a,d3
    bsr.w sub_565e
loc_09e0:
    move.w #$19,250(a6) ; app+$FA
    move.w 236(a6),d0 ; app+$EC
    subi.w #$1a,d0
    move.w d0,244(a6) ; app+$F4
    move.w 8(a3),d0
    add.w 12(a3),d0
    add.w 220(a6),d0 ; app+$DC
    add.w 220(a6),d0 ; app+$DC
    addq.w #1,d0
    move.w d0,246(a6) ; app+$F6
    neg.w d0
    add.w 234(a6),d0 ; app+$EA
    sub.w 220(a6),d0 ; app+$DC
    ext.l d0
    divu.w app_rectfill_ymax(a6),d0
    move.w d0,260(a6) ; app+$104
    subq.w #1,d0
    lsr.w #1,d0
    move.w d0,258(a6) ; app+$102
    move.w 244(a6),d0 ; app+$F4
    subq.w #3,d0
    move.w d0,252(a6) ; app+$FC
    move.w 258(a6),d0 ; app+$102
    mulu.w app_rectfill_ymax(a6),d0
    add.w 246(a6),d0 ; app+$F6
    add.w 220(a6),d0 ; app+$DC
    addq.w #1,d0
    move.w d0,248(a6) ; app+$F8
    neg.w d0
    add.w 234(a6),d0 ; app+$EA
    sub.w 220(a6),d0 ; app+$DC
    subq.w #1,d0
    ext.l d0
    divu.w app_rectfill_ymax(a6),d0
    move.w d0,256(a6) ; app+$100
    addq.b #2,1538(a6) ; app+$602
    addq.b #3,1612(a6) ; app+$64C
    addq.b #3,1760(a6) ; app+$6E0
    addq.b #1,1686(a6) ; app+$696
    addq.b #1,1834(a6) ; app+$72A
    move.w 240(a6),d0 ; app+$F0
    bsr.w sub_0cfc
loc_0a76:
    moveq #4,d1
loc_0a78:
    movem.w d0-d1,-(sp)
    moveq #5,d0
    sub.b d1,d0
    move.b d0,60(a3)
    suba.l a0,a0
    bsr.w sub_1176
loc_0a8a:
    move.l a0,68(a3)
    cmpi.b #$1,60(a3)
    beq.s loc_0aca
loc_0a96:
    cmpi.b #$2,60(a3)
    bne.s loc_0ab0
loc_0a9e:
    st 66(a3)
    move.l #$70630000,68(a0)
    move.l app_exec_base_0054(a6),56(a3)
loc_0ab0:
    move.w (sp),d0
    rol.w #4,d0
    move.w d0,(sp)
    andi.w #$f,d0
    bne.s loc_0ac2
loc_0abc:
    bsr.w sub_5dd2
loc_0ac0:
    bra.s loc_0ad2
loc_0ac2:
    bsr.w sub_0c90
loc_0ac6:
    bsr.w sub_565e
loc_0aca:
    bsr.w sub_5dd2
loc_0ace:
    bsr.w sub_0c84
loc_0ad2:
    lea 74(a3),a3
    movem.w (sp)+,d0-d1
    dbf d1,loc_0a78
loc_0ade:
    rts
    dc.b    $61,$00,$03,$04,$60,$00,$53,$f8
sub_0ae8:
    dc.b    $47,$ee,$05,$ce,$74,$06
hint_0aee:
; --- unverified ---
    cmp.b 60(a3),d1
    beq.s hint_0afe
hint_0af4:
; --- unverified ---
    lea 74(a3),a3
    dbf d2,hint_0aee
hint_0afc:
; --- unverified ---
    rts
hint_0afe:
; --- unverified ---
    move.l 222(a6),d0 ; app+$DE
    beq.s hint_0b1e
hint_0b04:
; --- unverified ---
    cmp.l a3,d0
    bne.s hint_0b0a
hint_0b08:
; --- unverified ---
    rts
hint_0b0a:
; --- unverified ---
    move.l a3,-(sp)
    movea.l d0,a3
    tst.w 4(a3)
    beq.s hint_0b1c
hint_0b14:
; --- unverified ---
    sf d7
    st d4
    bsr.w sub_5b56
hint_0b1c:
    dc.b    $26,$5f
hint_0b1e:
; --- unverified ---
    movea.l 68(a3),a0
    bsr.w sub_126a
hint_0b26:
; --- unverified ---
    move.l a3,222(a6) ; app+$DE
    tst.w 4(a3)
    bne.s hint_0b38
hint_0b30:
; --- unverified ---
    move.b #$c0,d1
    bra.w sub_0c00
hint_0b38:
; --- unverified ---
    st d7
    st d4
    bra.w sub_5b56
hint_0b40:
; --- unverified ---
    move.w #$78a,d3
    move.l 222(a6),d0 ; app+$DE
    beq.s hint_0b4e
hint_0b4a:
    dc.b    $26,$00,$96,$8e
hint_0b4e:
    dc.b    $74,$06
hint_0b50:
; --- unverified ---
    cmp.w #$78a,d3
    bne.s hint_0b5a
hint_0b56:
    dc.b    $36,$3c,$05,$84
hint_0b5a:
; --- unverified ---
    addi.w #$4a,d3
    tst.w 4(a6,d3.w)
    bne.s hint_0b6a
hint_0b64:
; --- unverified ---
    dbf d2,hint_0b50
hint_0b68:
; --- unverified ---
    rts
hint_0b6a:
; --- unverified ---
    lea 0(a6,d3.w),a3
    bra.s hint_0afe
hint_0b70:
; --- unverified ---
    rts
hint_0b72:
; --- unverified ---
    cmpi.b #$2,52(a3)
    beq.s hint_0b8c
hint_0b7a:
; --- unverified ---
    cmpi.b #$4,52(a3)
    bne.s hint_0b8e
hint_0b82:
; --- unverified ---
    movea.l 68(a3),a0
    bsr.w sub_126a
hint_0b8a:
; --- unverified ---
    bne.s hint_0b8e
hint_0b8c:
; --- unverified ---
    rts
hint_0b8e:
; --- unverified ---
    lea 31142(pc),a0
    bsr.w sub_19e4
hint_0b96:
; --- unverified ---
    bne.s hint_0b8c
hint_0b98:
; --- unverified ---
    cmpi.b #$4,52(a3)
    bne.s hint_0bb2
hint_0ba0:
; --- unverified ---
    movea.l 68(a3),a0
    bsr.w sub_113e
hint_0ba8:
; --- unverified ---
    bsr.w sub_0e96
hint_0bac:
; --- unverified ---
    bsr.w sub_10fe
hint_0bb0:
; --- unverified ---
    bra.s hint_0bb6
hint_0bb2:
    dc.b    $27,$42,$00,$38
hint_0bb6:
; --- unverified ---
    bra.w graphics_dispatch
hint_0bba:
; --- unverified ---
    cmpi.b #$4,52(a3)
    bne.s hint_0bcc
hint_0bc2:
; --- unverified ---
    lea str_854c(pc),a0
    bsr.w sub_19e4
hint_0bca:
; --- unverified ---
    beq.s hint_0bce
hint_0bcc:
; --- unverified ---
    rts
hint_0bce:
; --- unverified ---
    move.l d2,-(sp)
    movea.l 68(a3),a0
    bsr.w sub_113e
hint_0bd8:
; --- unverified ---
    bsr.w loc_0e9a
hint_0bdc:
; --- unverified ---
    move.l (sp)+,d2
    addq.l #1,d2
    bne.s hint_0bf0
hint_0be2:
; --- unverified ---
    move.w 34(a0),d2
    sub.w 6(a3),d2
    addq.w #2,d2
    bsr.w loc_0e9a
hint_0bf0:
; --- unverified ---
    bsr.w sub_10fe
hint_0bf4:
; --- unverified ---
    bra.w graphics_dispatch
hint_0bf8:
; --- unverified ---
    moveq #64,d1
    bra.s sub_0c00
hint_0bfc:
    dc.b    $12,$3c,$00,$80
sub_0c00:
    tst.w 1860(a6) ; app+$744
    bne.s loc_0c1a
loc_0c06:
    move.b 60(a3),d2
    cmp.b #$1,d2
    beq.s loc_0c1a
loc_0c10:
    move.w 240(a6),d0 ; app+$F0
    bsr.w sub_0cd4
loc_0c18:
    bpl.s loc_0c1c
loc_0c1a:
    rts
loc_0c1c:
    move.w d0,240(a6) ; app+$F0
    bsr.w sub_0cfc
loc_0c24:
    lea sub_0c62(pc),a0
    bsr.w sub_0c30
loc_0c2c:
    lea loc_0c78(pc),a0
sub_0c30:
    lea 1560(a6),a3 ; app+$618
    moveq #3,d2
loc_0c36:
    rol.w #4,d0
    rol.w #4,d1
    movem.w d0-d1,-(sp)
    andi.w #$f,d0
    andi.w #$f,d1
    cmp.w d0,d1
    beq.s loc_0c54
loc_0c4a:
    movem.l d2/a0,-(sp)
    jsr (a0)
loc_0c50:
    movem.l (sp)+,d2/a0
loc_0c54:
    lea 74(a3),a3
    movem.w (sp)+,d0-d1
    dbf d2,loc_0c36
loc_0c60:
    rts
sub_0c62:
; --- unverified ---
    tst.b d1
    beq.s loc_0c60
hint_0c66:
; --- unverified ---
    bsr.w call_rectfill
hint_0c6a:
; --- unverified ---
    sf d4
    sf d7
    bsr.w sub_5b56
hint_0c72:
; --- unverified ---
    clr.w 4(a3)
    rts
loc_0c78:
    tst.b d0
    beq.s loc_0c60
loc_0c7c:
    bsr.w sub_0c90
loc_0c80:
    bsr.w sub_565e
sub_0c84:
    movea.l 68(a3),a0
    bsr.w sub_0f9a
loc_0c8c:
    bra.w graphics_dispatch
sub_0c90:
    move.w 246(a6),d1 ; app+$F6
    btst #3,d0
    bne.s loc_0c9e
loc_0c9a:
    move.w 248(a6),d1 ; app+$F8
loc_0c9e:
    move.w d1,-(sp)
    move.w 242(a6),d1 ; app+$F2
    btst #1,d0
    bne.s loc_0cae
loc_0caa:
    move.w 244(a6),d1 ; app+$F4
loc_0cae:
    movem.w d0-d1,-(sp)
    andi.w #$3,d0
    asl.w #1,d0
    addi.w #$fa,d0
    move.w -2(a6,d0.w),d2
    moveq #12,d0
    and.w (sp)+,d0
    asr.w #1,d0
    addi.w #$100,d0
    move.w -2(a6,d0.w),d3
    movem.w (sp)+,d0-d1
    rts
sub_0cd4:
    move.l d2,-(sp)
    bsr.w sub_0cfc
loc_0cda:
    subq.b #2,d2
    asl.b #4,d2
    or.b d1,d2
    move.w d0,d1
loc_0ce2:
    move.w #$f0,d0
    and.b (a0)+,d0
    beq.s loc_0cf4
loc_0cea:
    cmp.b d2,d0
    bne.s loc_0ce2
loc_0cee:
    moveq #15,d0
    and.b -(a0),d0
    bra.s loc_0cf6
loc_0cf4:
    moveq #-1,d0
loc_0cf6:
    movem.l (sp)+,d2
    rts
sub_0cfc:
    mulu.w #$6,d0
    addi.l #dat_090a,d0
    movea.l d0,a1
    movea.l (a1)+,a0
    move.w (a1),d0
    rts
sub_0d0e:
; --- unverified ---
    tst.w 1860(a6) ; app+$744
    bne.w hint_0d98
hint_0d16:
; --- unverified ---
    move.b 52(a3),d0
    cmp.b #$2,d0
    beq.s hint_0d98
hint_0d20:
; --- unverified ---
    cmp.b #$4,d0
    bne.s hint_0d30
hint_0d26:
; --- unverified ---
    movea.l 68(a3),a0
    tst.l 30(a0)
    beq.s hint_0d98
hint_0d30:
; --- unverified ---
    move.l a3,-(sp)
    moveq #4,d3
    lea 31076(pc),a0
    bsr.w sub_1a7e
hint_0d3c:
; --- unverified ---
    movea.l (sp),a0
    clr.b (a4)
    tst.b 66(a0)
    beq.s hint_0d54
hint_0d46:
    dc.b    $20,$68,$00,$44,$41,$e8,$00,$44,$22,$4c
hint_0d50:
; --- unverified ---
    move.b (a0)+,(a1)+
    bne.s hint_0d50
hint_0d54:
; --- unverified ---
    bsr.w loc_59c2
hint_0d58:
; --- unverified ---
    beq.s hint_0d60
hint_0d5a:
; --- unverified ---
    bsr.w sub_5d9c
hint_0d5e:
; --- unverified ---
    bra.s hint_0d96
hint_0d60:
; --- unverified ---
    moveq #0,d0
    tst.b (a4)
    beq.s hint_0d7c
hint_0d66:
; --- unverified ---
    movea.l a4,a0
    movem.l a3/a5,-(sp)
    bsr.w sub_6b38
hint_0d70:
; --- unverified ---
    movem.l (sp)+,a3/a5
    beq.s hint_0d7c
hint_0d76:
; --- unverified ---
    bsr.w sub_5e54
hint_0d7a:
; --- unverified ---
    bra.s hint_0d54
hint_0d7c:
; --- unverified ---
    bsr.w sub_5d9c
hint_0d80:
; --- unverified ---
    movea.l (sp),a3
    st d7
    bsr.w hint_0d9a
hint_0d88:
; --- unverified ---
    tst.b 66(a3)
    beq.s hint_0d96
hint_0d8e:
; --- unverified ---
    bsr.w sub_0de6
hint_0d92:
; --- unverified ---
    bsr.w sub_5ede
hint_0d96:
    dc.b    $26,$5f
hint_0d98:
; --- unverified ---
    rts
hint_0d9a:
; --- unverified ---
    move.w d7,-(sp)
    sf d4
    sf d7
    bsr.w sub_5b56
hint_0da4:
; --- unverified ---
    move.w (sp)+,d7
    sf 66(a3)
    tst.b (a4)
    beq.s hint_0de0
hint_0dae:
    dc.b    $17,$7c,$00,$01,$00,$42,$22,$6b,$00,$44,$41,$e9,$00,$44,$70,$3f
hint_0dbe:
; --- unverified ---
    move.b (a4)+,(a0)+
    dbeq d0,hint_0dbe
hint_0dc4:
; --- unverified ---
    clr.b -(a0)
    move.l 68(a1),d0
    andi.l #$dfdfff00,d0
    cmp.l #$70630000,d0
    bne.s hint_0de0
hint_0dd8:
    dc.b    $23,$40,$00,$44,$50,$eb,$00,$42
hint_0de0:
; --- unverified ---
    st d4
    bra.w sub_5b56
sub_0de6:
    move.l a3,-(sp)
    lea 1782(a6),a3 ; app+$6F6
    moveq #4,d0
loc_0dee:
    move.l d0,-(sp)
    bsr.w sub_113e
loc_0df4:
    move.l 68(a3),d0
loc_0df8:
    movea.l d0,a0
    move.l (a0),d0
    bne.s loc_0df8
loc_0dfe:
    tst.b 9(a0)
    beq.s loc_0e38
loc_0e04:
    bpl.s loc_0e0e
loc_0e06:
    cmpi.b #$3,8(a0)
    beq.s loc_0e56
loc_0e0e:
    bsr.w sub_126a
loc_0e12:
    movem.l d3/a0-a5,-(sp)
    lea 68(a0),a4
    bsr.w sub_6b70
loc_0e1e:
    movem.l (sp)+,d3/a0-a5
    bne.s loc_0e38
loc_0e24:
    move.l d2,d1
    cmpi.b #$4,8(a0)
    bne.s loc_0e34
loc_0e2e:
    bsr.w sub_0e96
loc_0e32:
    bra.s loc_0e38
loc_0e34:
    move.l d1,10(a0)
loc_0e38:
    movea.l 4(a0),a0
    move.l a0,d0
    bne.s loc_0dfe
loc_0e40:
    movea.l 68(a3),a0
    bsr.w sub_10fe
loc_0e48:
    lea -74(a3),a3
    move.l (sp)+,d0
    dbf d0,loc_0dee
loc_0e52:
    movea.l (sp)+,a3
    rts
loc_0e56:
    movem.l d0/d3/d6/a0-a2,-(sp)
    movea.l app_exec_base_0054(a6),a1
    move.l 10(a0),d0
    addq.l #1,d0
    andi.b #$fe,d0
    movea.l d0,a2
    cmpa.l a2,a1
    blt.s loc_0e86
loc_0e6e:
    move.w 6(a3),d6
    subq.w #3,d6
    bcs.s loc_0e86
loc_0e76:
    move.l a1,-(sp)
loc_0e78:
    bsr.w sub_6964
loc_0e7c:
    cmpa.l (sp),a2
    beq.s loc_0e8e
loc_0e80:
    dbf d6,loc_0e78
loc_0e84:
    movea.l (sp)+,a1
loc_0e86:
    move.l a1,d1
    movem.l (sp)+,d0/d3/d6/a0-a2
    bra.s loc_0e34
loc_0e8e:
    movea.l (sp)+,a1
    movem.l (sp)+,d0/d3/d6/a0-a2
    bra.s loc_0e38
sub_0e96:
    bsr.w sub_6ea6
loc_0e9a:
    move.l d2,d1
    beq.s loc_0ecc
loc_0e9e:
    movem.l a0-a2,-(sp)
    cmp.l #$ffff,d1
    bls.s loc_0eac
loc_0eaa:
    moveq #-1,d1
loc_0eac:
    movem.l 18(a0),a1-a2
    move.w 34(a0),d0
    movea.l 14(a0),a0
    bsr.w sub_0ece
loc_0ebe:
    move.l a0,d2
    movem.l (sp)+,a0-a2
    move.w d1,34(a0)
    move.l d2,14(a0)
loc_0ecc:
    rts
sub_0ece:
    cmp.w #$1,d1
    bhi.s loc_0eda
loc_0ed4:
    moveq #1,d1
    movea.l a1,a0
    rts
loc_0eda:
    sub.w d1,d0
    bcs.s loc_0ef6
loc_0ede:
    beq.s loc_0ef4
loc_0ee0:
    subq.w #1,d0
loc_0ee2:
    cmpi.b #$a,-(a0)
    bne.s loc_0ee2
loc_0ee8:
    dbf d0,loc_0ee2
loc_0eec:
    cmpi.b #$a,-(a0)
    bne.s loc_0eec
loc_0ef2:
    addq.l #1,a0
loc_0ef4:
    rts
loc_0ef6:
    neg.w d0
    subq.w #1,d0
loc_0efa:
    cmpi.b #$a,(a0)+
    bne.s loc_0efa
loc_0f00:
    cmpa.l a2,a0
    dbcc d0,loc_0efa
loc_0f06:
    bcs.s loc_0ef4
loc_0f08:
    sub.w d0,d1
    subq.w #1,d1
    subq.l #1,a0
    bra.s loc_0eec
sub_0f10:
; --- unverified ---
    bsr.w sub_113e
hint_0f14:
; --- unverified ---
    movea.l 68(a3),a0
    bsr.w sub_1176
hint_0f1c:
; --- unverified ---
    bne.w loc_0f9e
hint_0f20:
; --- unverified ---
    bra.w sub_5e54
hint_0f24:
; --- unverified ---
    cmpi.b #$4,52(a3)
    bne.s hint_0f34
hint_0f2c:
; --- unverified ---
    sf d4
    sf d7
    bsr.w sub_5b56
hint_0f34:
; --- unverified ---
    movea.l 68(a3),a0
    bsr.w sub_11de
hint_0f3c:
; --- unverified ---
    bne.w loc_0f9e
hint_0f40:
; --- unverified ---
    cmpi.b #$4,52(a3)
    beq.s hint_0f4a
hint_0f48:
; --- unverified ---
    rts
hint_0f4a:
; --- unverified ---
    movea.l 68(a3),a0
    bsr.w sub_1244
hint_0f52:
; --- unverified ---
    moveq #3,d1
    cmpi.b #$1,60(a3)
    bne.s hint_0f5e
hint_0f5c:
    dc.b    $72,$02
hint_0f5e:
; --- unverified ---
    bra.w hint_10f6
hint_0f62:
; --- unverified ---
    movea.l 68(a3),a0
    move.l 4(a0),d0
    beq.s hint_0f70
hint_0f6c:
; --- unverified ---
    movea.l d0,a0
    bra.s sub_0f9a
hint_0f70:
; --- unverified ---
    move.l (a0),d0
    bne.s hint_0f76
hint_0f74:
; --- unverified ---
    rts
hint_0f76:
; --- unverified ---
    movea.l d0,a0
    move.l (a0),d0
    bne.s hint_0f76
hint_0f7c:
; --- unverified ---
    bra.s sub_0f9a
hint_0f7e:
; --- unverified ---
    movea.l 68(a3),a0
    move.l (a0),d0
    beq.s hint_0f8a
hint_0f86:
; --- unverified ---
    movea.l d0,a0
    bra.s sub_0f9a
hint_0f8a:
; --- unverified ---
    move.l 4(a0),d0
    bne.s hint_0f92
hint_0f90:
; --- unverified ---
    rts
hint_0f92:
; --- unverified ---
    movea.l d0,a0
    move.l 4(a0),d0
    bne.s hint_0f92
sub_0f9a:
    bsr.w sub_113e
loc_0f9e:
    move.l a0,-(sp)
    sf d4
    sf d7
    bsr.w sub_5b56
loc_0fa8:
    movea.l (sp),a0
    cmpi.b #$3,8(a0)
    bcc.s loc_0fb6
loc_0fb2:
    bsr.w call_rectfill
loc_0fb6:
    movea.l (sp)+,a0
    moveq #-1,d0
    movea.l a0,a1
loc_0fbc:
    addq.l #1,d0
    move.l (a1),d1
    movea.l d1,a1
    bne.s loc_0fbc
loc_0fc4:
    move.w d0,72(a3)
    bsr.w sub_10fe
loc_0fcc:
    st d4
    cmpa.l 222(a6),a3 ; app+$DE
    seq d7
    bsr.w sub_5b56
loc_0fd8:
    bra.w graphics_dispatch
sub_0fdc:
; --- unverified ---
    move.b 60(a3),d0
    bsr.w sub_12a0
hint_0fe4:
; --- unverified ---
    beq.s hint_0ff0
hint_0fe6:
; --- unverified ---
    lea 30099(pc),a0
    bsr.w hint_4910
hint_0fee:
; --- unverified ---
    beq.s hint_0ff2
hint_0ff0:
; --- unverified ---
    rts
hint_0ff2:
; --- unverified ---
    lea 2772(a6),a0 ; app+$AD4
    bsr.w loc_108c
hint_0ffa:
; --- unverified ---
    movea.l 222(a6),a3 ; app+$DE
    lea 2772(a6),a0 ; app+$AD4
    bsr.w sub_1008
hint_1006:
; --- unverified ---
    bra.s loc_0f9e
sub_1008:
    move.l a0,-(sp)
    bsr.w sub_113e
loc_100e:
    movea.l 68(a3),a0
    tst.l 18(a0)
    beq.s loc_1022
loc_1018:
    bsr.w sub_1176
loc_101c:
    bne.s loc_1022
loc_101e:
    bsr.w sub_1244
loc_1022:
    movea.l (sp)+,a1
    bsr.w sub_1204
loc_1028:
    tst.l 30(a0)
    beq.s loc_1042
loc_102e:
    st 9(a0)
    move.l #$70630000,68(a0)
    move.l app_exec_base_0054(a6),d2
    bsr.w sub_0e96
loc_1042:
    rts
loc_1044:
    tst.b 1413(a6) ; app+$585
    beq.s loc_1050
loc_104a:
    move.l 1400(a6),d0 ; app+$578
    bne.s loc_1052
loc_1050:
    rts
loc_1052:
    movea.l d0,a0
    lea 4(a0),a0
    move.l a0,-(sp)
    bsr.w sub_107c
loc_105e:
    movea.l (sp)+,a0
    bne.s loc_1050
loc_1062:
    lea 1708(a6),a3 ; app+$6AC
    bsr.s sub_1008
loc_1068:
    tst.w 4(a3)
    bne.w loc_0f9e
loc_1070:
    bsr.w sub_10fe
loc_1074:
    move.b #$c0,d1
    bra.w sub_0c00
sub_107c:
    move.l a0,-(sp)
    movea.l a0,a5
    moveq #0,d2
    bsr.w sub_492e
loc_1086:
    movea.l (sp)+,a0
    beq.s loc_108c
loc_108a:
    rts
loc_108c:
    move.l a3,342(a6) ; app+$156
    adda.l d4,a3
    move.l a3,346(a6) ; app+$15A
    bsr.w call_close_7c2c
loc_109a:
    beq.s loc_10a8
loc_109c:
    move.l d0,1404(a6) ; app+$57C
    move.l a0,1408(a6) ; app+$580
    moveq #0,d0
    rts
loc_10a8:
    clr.l 1404(a6) ; app+$57C
    clr.l 1408(a6) ; app+$580
    rts
sub_10b2:
; --- unverified ---
    tst.w 1860(a6) ; app+$744
    bne.s hint_10c8
hint_10b8:
; --- unverified ---
    move.b 52(a3),d1
    move.b 60(a3),d0
    bsr.w sub_12a0
hint_10c4:
; --- unverified ---
    bne.w hint_10ca
hint_10c8:
; --- unverified ---
    rts
hint_10ca:
    dc.b    $20,$6b,$00,$44
hint_10ce:
; --- unverified ---
    addq.b #1,d1
    cmp.b #$4,d1
    bls.s hint_10d8
hint_10d6:
    dc.b    $72,$01
hint_10d8:
; --- unverified ---
    cmp.b #$2,d1
    bne.s hint_10e6
hint_10de:
; --- unverified ---
    cmp.b #$1,d0
    bne.s hint_10ce
hint_10e4:
; --- unverified ---
    beq.s hint_10f2
hint_10e6:
; --- unverified ---
    cmp.b #$4,d1
    bne.s hint_10f2
hint_10ec:
; --- unverified ---
    tst.l 18(a0)
    beq.s hint_10ce
hint_10f2:
; --- unverified ---
    bsr.w sub_113e
hint_10f6:
; --- unverified ---
    move.b d1,8(a0)
    bra.w loc_0f9e
sub_10fe:
    move.l a0,68(a3)
    move.b 8(a0),52(a3)
    bsr.w sub_5dd2
loc_110c:
    movea.l 68(a3),a0
    bsr.w sub_126a
loc_1114:
    move.l 10(a0),56(a3)
    move.b 9(a0),66(a3)
    move.b 8(a0),d0
    cmp.b #$4,d0
    bne.s loc_113c
loc_112a:
    move.l 14(a0),56(a3)
    move.w 34(a0),54(a3)
    move.b 36(a0),53(a3)
loc_113c:
    rts
sub_113e:
    move.l a0,-(sp)
    movea.l 68(a3),a0
    move.b 66(a3),9(a0)
    move.b 52(a3),d0
    move.b d0,8(a0)
    cmp.b #$4,d0
    beq.s loc_1160
loc_1158:
    move.l 56(a3),10(a0)
    bra.s loc_1172
loc_1160:
    move.l 56(a3),14(a0)
    move.w 54(a3),34(a0)
    move.b 53(a3),36(a0)
loc_1172:
    movea.l (sp)+,a0
    rts
sub_1176:
    move.l a0,-(sp)
    move.l #$84,d0
    bsr.w alloc_memory_8160
loc_1182:
    movea.l (sp)+,a1
    beq.s loc_11dc
loc_1186:
    movea.l a0,a2
    move.l #$83,d0
loc_118e:
    clr.b (a2)+
    dbf d0,loc_118e
loc_1194:
    move.b dat_002a,d0
    move.l a1,(a0)
    beq.s loc_11d2
loc_119e:
    movea.l 4(a1),a2
    move.l a0,4(a1)
    move.l a2,4(a0)
    beq.s loc_11ae
loc_11ac:
    move.l a0,(a2)
loc_11ae:
    move.b 8(a1),d1
    moveq #3,d0
    cmp.b #$4,d1
    beq.s loc_11c4
loc_11ba:
    moveq #1,d0
    cmp.b #$2,d1
    beq.s loc_11c4
loc_11c2:
    move.b d1,d0
loc_11c4:
    move.b d0,8(a0)
    move.l 10(a1),10(a0)
    move.b 36(a1),d0
loc_11d2:
    move.b d0,36(a0)
    move.w #$1,34(a0)
loc_11dc:
    rts
sub_11de:
; --- unverified ---
    movem.l (a0),a1-a2
    move.l a1,d0
    beq.s hint_11ee
hint_11e6:
; --- unverified ---
    move.l a2,4(a1)
    bne.s hint_11f2
hint_11ec:
; --- unverified ---
    bra.s hint_11f4
hint_11ee:
; --- unverified ---
    move.l a2,d0
    beq.s hint_1202
hint_11f2:
    dc.b    $24,$89
hint_11f4:
; --- unverified ---
    move.l d0,-(sp)
    bsr.w sub_1244
hint_11fa:
; --- unverified ---
    bsr.w free_memory
hint_11fe:
    dc.b    $20,$5f,$72,$01
hint_1202:
; --- unverified ---
    rts
sub_1204:
    move.l a0,-(sp)
    movea.l a1,a0
    bsr.w sub_1288
loc_120c:
    movea.l (sp),a1
    lea 37(a1),a1
    moveq #30,d0
loc_1214:
    move.b (a0)+,(a1)+
    dbeq d0,loc_1214
loc_121a:
    clr.b -(a1)
    movea.l (sp)+,a0
    movea.l 342(a6),a1 ; app+$156
    move.l a1,18(a0)
    move.l a1,14(a0)
    move.l 346(a6),22(a0) ; app+$15A
    move.l 1408(a6),26(a0) ; app+$580
    move.l 1404(a6),30(a0) ; app+$57C
    move.b #$4,8(a0)
    rts
sub_1244:
    move.l a0,-(sp)
    move.l 18(a0),-(sp)
    movea.l 26(a0),a0
    bsr.w free_memory
loc_1252:
    movea.l (sp)+,a0
    bsr.w free_memory
loc_1258:
    movea.l (sp)+,a0
    clr.l 18(a0)
    clr.l 30(a0)
    move.w #$1,34(a0)
    rts
sub_126a:
    move.l 18(a0),d0
    beq.s loc_1286
loc_1270:
    move.l d0,342(a6) ; app+$156
    move.l 22(a0),346(a6) ; app+$15A
    move.l 26(a0),1408(a6) ; app+$580
    move.l 30(a0),1404(a6) ; app+$57C
loc_1286:
    rts
sub_1288:
    movea.l a0,a1
loc_128a:
    move.b (a1)+,d0
    beq.s loc_129e
loc_128e:
    cmp.b #$3a,d0
    beq.s loc_129a
loc_1294:
    cmp.b #$2f,d0
    bne.s loc_128a
loc_129a:
    movea.l a1,a0
    bra.s loc_128a
loc_129e:
    rts
sub_12a0:
; --- unverified ---
    cmp.b #$3,d0
    beq.s hint_12aa
hint_12a6:
    dc.b    $b0,$3c,$00,$05
hint_12aa:
; --- unverified ---
    rts
hint_12ac:
    dc.b    $2f,$0b
hint_12ae:
; --- unverified ---
    moveq #6,d3
    lea 29691(pc),a0
    bsr.w sub_1a7e
hint_12b8:
; --- unverified ---
    bsr.w loc_59c2
hint_12bc:
; --- unverified ---
    bne.s hint_1324
hint_12be:
; --- unverified ---
    move.b (a4)+,d1
    beq.s hint_1324
hint_12c2:
; --- unverified ---
    bsr.w hint_6b6c
hint_12c6:
; --- unverified ---
    beq.s hint_12ce
hint_12c8:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bra.s hint_12b8
hint_12ce:
; --- unverified ---
    move.l d2,d7
    bsr.w sub_19d4
hint_12d4:
; --- unverified ---
    bsr.w sub_19d4
hint_12d8:
; --- unverified ---
    moveq #61,d1
    bsr.w sub_58ba
hint_12de:
; --- unverified ---
    moveq #36,d1
    bsr.w sub_58ba
hint_12e4:
; --- unverified ---
    move.l d7,d2
    bsr.w hint_6a9a
hint_12ea:
; --- unverified ---
    moveq #18,d1
    bsr.w sub_6a5a
hint_12f0:
; --- unverified ---
    move.l d7,d1
    bsr.w $6adc
hint_12f6:
; --- unverified ---
    move.l d7,d0
    bsr.w hint_7ef8
hint_12fc:
; --- unverified ---
    beq.s hint_130e
hint_12fe:
; --- unverified ---
    move.l d0,-(sp)
    moveq #18,d1
    bsr.w sub_6a5a
hint_1306:
; --- unverified ---
    move.l (sp)+,d0
    moveq #32,d2
    bsr.w sub_7bd8
hint_130e:
; --- unverified ---
    move.w 10(a3),d2
    moveq #4,d3
    bsr.w sub_576e
hint_1318:
; --- unverified ---
    bsr.w sub_4120
hint_131c:
; --- unverified ---
    bmi.s hint_1324
hint_131e:
; --- unverified ---
    cmp.b #$20,d1
    beq.s hint_12ae
hint_1324:
; --- unverified ---
    bsr.w sub_5d9c
hint_1328:
; --- unverified ---
    movea.l (sp)+,a3
    rts
hint_132c:
; --- unverified ---
    sf d4
    sf d7
    bsr.w sub_5b56
hint_1334:
; --- unverified ---
    lea 22(a3),a0
    move.b #$20,(a0)+
    lea dat_850a(pc),a1
    move.b 52(a3),d0
    cmp.b #$1,d0
    beq.s hint_1358
hint_134a:
; --- unverified ---
    lea dat_84fe(pc),a1
    cmp.b #$3,d0
    beq.s hint_1358
hint_1354:
    dc.b    $43,$fa,$71,$c5
hint_1358:
; --- unverified ---
    move.b (a1)+,(a0)+
    bne.s hint_1358
hint_135c:
; --- unverified ---
    move.b #$20,-1(a0)
    clr.b (a0)
    st d4
    st d7
    bra.w sub_5b56
dat_136c:
    dc.w    $0000
    dc.b    $00,$00
dat_13b0:
; --- unverified ---
    move.l d0,-(sp)
    move.l 4(sp),dat_8960
    move.l #dat_14c8,4(sp)
    movem.l d0-d7/a0-a6,-(sp)
    suba.l a1,a1
    movea.l AbsExecBase,a6
    jsr -294(a6) ; app-$126; unresolved_indirect_hint:disp
hint_13d0:
    dc.b    $28,$40,$23,$c0
    dc.l    dat_895a
    dc.b    $22,$3c
    dc.l    dat_1448
    dc.b    $e4,$89,$29,$41,$00,$ac
    dc.b    " zup)h"
hint_13ea:
    dc.b    $00,$98,$00,$98
    dc.b    $00,$32,$70,$ff,$2f,$0e,$2c,$78,$00,$04,$4e,$ae,$fe,$b6
sub_1416:
; --- unverified ---
    movea.l (sp)+,a6
    move.b d0,dat_88f4
    move.l dat_88f6(pc),d0
    lsl.l #2,d0
    addq.l #4,d0
    move.l d0,60(sp)
    movea.l d0,a0
    move.l dat_88fa,(a0)+
    move.w dat_88fe,(a0)
    movem.l (sp)+,d0-d7/a0-a6
    moveq #0,d0
    lea pcref_1488(pc),a0
    move.b (a0)+,d0
    rts
hint_1446:
    dc.b    $00
    dc.b    $00
dat_1448:
    dc.l    init_app
    dcb.b   12,0
dat_1458:
    dcb.b   44,0
dat_1484:
    dcb.b   4,0
pcref_1488:
    dc.b    $00
pcref_1489:
    dcb.b   63,0
dat_14c8:
    dc.b    $50,$f9
    dc.l    dat_88f5
dat_14ce:
    dc.b    $4a,$fc
dat_14d0:
; --- unverified ---
    move.l d0,dat_8916
    move.l (sp)+,d0
    cmp.b #$9,d0
    bne.s hint_14f2
hint_14de:
; --- unverified ---
    cmpi.l #dat_14c8,2(sp)
    bne.s hint_14f2
hint_14e8:
; --- unverified ---
    move.l dat_8916(pc),d0
    bclr #7,(sp)
    rte
hint_14f2:
; --- unverified ---
    cmp.l #$4,d0
    bne.s hint_152e
hint_14fa:
; --- unverified ---
    cmpi.l #dat_173c,2(sp)
    beq.s hint_1512
hint_1504:
; --- unverified ---
    cmpi.l #dat_14ce,2(sp)
    bne.s hint_152e
hint_150e:
; --- unverified ---
    moveq #29,d0
    bra.s hint_152e
hint_1512:
; --- unverified ---
    tst.b dat_8906
    beq.s hint_151e
hint_151a:
    dc.b    $f3,$7a,$74,$7a
hint_151e:
; --- unverified ---
    move.l dat_8916(pc),d0
    move.w dat_8910(pc),(sp)
    move.l dat_890c(pc),2(sp)
    rte
hint_152e:
; --- unverified ---
    move.l d0,dat_8908
    jmp dat_153a
dat_153a:
; --- unverified ---
    cmp.l #$3,d0
    bgt.s hint_157a
hint_1542:
; --- unverified ---
    bne.s hint_1578
hint_1544:
; --- unverified ---
    btst #0,13(sp)
    bne.s hint_1578
hint_154c:
; --- unverified ---
    move.w 6(sp),d0
    move.l a0,-(sp)
    movea.l 14(sp),a0
    addq.l #2,a0
    cmp.w -(a0),d0
    beq.s hint_1570
hint_155c:
; --- unverified ---
    cmp.w -(a0),d0
    beq.s hint_1570
hint_1560:
; --- unverified ---
    cmp.w -(a0),d0
    beq.s hint_1570
hint_1564:
; --- unverified ---
    cmp.w -(a0),d0
    beq.s hint_1570
hint_1568:
; --- unverified ---
    cmp.w -(a0),d0
    beq.s hint_1570
hint_156c:
    dc.b    $20,$6f,$00,$0e
hint_1570:
    dc.b    $2f,$48,$00,$0e,$20,$5f,$70,$03
hint_1578:
    dc.b    $50,$8f
hint_157a:
; --- unverified ---
    move.w (sp),dat_8910
    bclr #7,(sp)
    move.l 2(sp),dat_890c
    move.l sp,dat_8912
    move.l #dat_16cc,2(sp)
    rte
pcref_159c:
; --- unverified ---
    move.w (sp)+,dat_8910
    move.l (sp)+,dat_890c
    cmp.l #$9,d0
    movem.w (sp)+,d0
dat_15b2:
    beq.w hint_16c6
hint_15b6:
; --- unverified ---
    andi.w #$f000,d0
    beq.s hint_15f8
hint_15bc:
; --- unverified ---
    cmp.w #$1000,d0
    beq.s hint_15f8
hint_15c2:
; --- unverified ---
    cmp.w #$2000,d0
    beq.s hint_15f2
hint_15c8:
; --- unverified ---
    cmp.w #$8000,d0
    beq.s hint_15e6
hint_15ce:
; --- unverified ---
    cmp.w #$9000,d0
    beq.s hint_15f2
hint_15d4:
; --- unverified ---
    cmp.w #$a000,d0
    beq.s hint_15ec
hint_15da:
; --- unverified ---
    cmp.w #$b000,d0
    bne.s hint_15f8
hint_15e0:
; --- unverified ---
    lea 84(sp),sp
    bra.s hint_15f8
hint_15e6:
; --- unverified ---
    lea 50(sp),sp
    bra.s hint_15f8
hint_15ec:
; --- unverified ---
    lea 24(sp),sp
    bra.s hint_15f8
hint_15f2:
    dc.b    $23,$df
    dc.l    dat_890c
hint_15f8:
; --- unverified ---
    move.l a0,-(sp)
    tst.b dat_8906
    beq.s sub_1634
hint_1602:
    dc.b    $41,$fa,$73,$92,$f3,$28,$00,$00,$4a,$28,$00,$00,$67,$24
hint_1610:
; --- unverified ---
    moveq #0,d0
    move.b 1(a0),d0
    cmp.b #$18,d0
    beq.s hint_1622
hint_161c:
; --- unverified ---
    cmp.b #$38,d0
    bne.s $1628
hint_1622:
    dc.b    $08,$f0,$00,$03,$00,$00
    dc.b    $f2,$28,$f0,$ff,$00,$e4,$f2,$28,$bc,$00,$00,$d8
sub_1634:
    dc.b    $2f,$01,$20,$78,$00,$04,$32,$28,$01,$28,$41,$fa
    dc.b    "s$Nz",0
    dc.b    $00,$10,$c0,$4e,$7a,$00,$01,$10,$c0,$4e,$7a,$08,$01,$20,$c0,$08
    dc.b    $01,$00,$01,$67,$48
hint_165a:
    dc.b    $4e,$7a,$08,$03,$20,$c0,$4e,$7a,$08,$04,$20,$c0,$4e,$7a,$08,$02
    dc.b    $20,$c0,$08,$01,$00,$03,$66,$30
hint_1672:
    dc.b    $4e,$7a,$00,$02,$30,$c0,$08,$01,$00,$02,$67,$24
    dc.b    $f0,$10,$62,$00,$f0,$28,$42,$00,$00,$02,$f0,$28,$0a,$00,$00,$06
    dc.b    $f0,$28,$0e,$00,$00,$0a,$f0,$28,$4e,$00,$00,$0e,$f0,$28,$4a,$00
    dc.b    $00,$16,$4e,$71
sub_16a2:
; --- unverified ---
    movem.l (sp)+,d1/a0
    move.w #$10,-(sp)
    move.l #dat_16cc,-(sp)
    move.w dat_8910(pc),d0
    bclr #15,d0
    move.w d0,-(sp)
    move.l sp,d0
    addq.l #8,d0
    move.l d0,dat_8912
    rte
hint_16c6:
; --- unverified ---
    addq.l #4,sp
    bra.w hint_15f8
dat_16cc:
; --- unverified ---
    movem.l d1-d7/a0-a7,dat_891a
    cmpi.l #$1d,dat_8908
    bne.s hint_16e8
hint_16e0:
    dc.b    $23,$fa,$72,$7e
    dc.l    dat_890c
hint_16e8:
; --- unverified ---
    movea.l dat_8956(pc),a1
    moveq #0,d0
    move.b dat_895e(pc),d1
    bset d1,d0
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -324(a6) ; app-$144; unresolved_indirect_hint:disp
hint_16fe:
; --- unverified ---
    movea.l (sp)+,a6
    cmpi.l #$1d,dat_8908
    beq.s hint_1736
hint_170c:
; --- unverified ---
    moveq #0,d0
    move.b dat_88f4(pc),d1
    bset d1,d0
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -318(a6) ; app-$13E; unresolved_indirect_hint:disp
hint_171e:
; --- unverified ---
    movea.l (sp)+,a6
    moveq #0,d0
    moveq #0,d1
    move.b dat_88f4(pc),d2
    bset d2,d1
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -306(a6) ; app-$132; unresolved_indirect_hint:disp
hint_1734:
    dc.b    $2c,$5f
hint_1736:
    dc.b    $4c,$fa,$ff,$ff,$71,$dc
dat_173c:
    dc.b    $4a,$fc
pcref_173e:
    dc.b    $10,$02,$0f,$03,$0a,$04,$03,$05,$04,$06,$05,$07,$06,$08,$07,$09
    dc.b    $1f,$0a,$20,$0b,$33,$0d,$34,$0e,$08,$18,$1d,$1d
    dc.b    ",0-1.2/304152658",0
    dc.b    $00
loc_176c:
    movem.l pcref_8914(pc),d0-d7/a0-a5
    movem.l d0-d7/a0-a5,16(a6) ; app+$10
    movem.l pcref_894c(pc),d0-d1
    movem.l d0-d1,72(a6) ; app+$48
    movea.l dat_890c(pc),a1
    move.l a1,app_exec_base_0054(a6)
    move.l dat_8912(pc),80(a6) ; app+$50
    move.w dat_8910,90(a6) ; app+$5A
    move.l dat_8908(pc),d1
    st 308(a6) ; app+$134
    cmp.b #$4,d1
    beq.w loc_1864
loc_17aa:
    cmp.b #$9,d1
    beq.w loc_1812
loc_17b2:
    cmp.b #$1d,d1
    bne.s loc_17c2
loc_17b8:
    sf 308(a6) ; app+$134
    clr.b dat_88f5
loc_17c2:
    lea pcref_173e(pc),a0
    moveq #0,d0
loc_17c8:
    move.b (a0)+,d0
    beq.s loc_17d4
loc_17cc:
    cmp.b (a0)+,d1
    bne.s loc_17c8
loc_17d0:
    move.l d0,d1
    bra.s loc_17d6
loc_17d4:
    moveq #30,d1
loc_17d6:
    clr.l 984(a6) ; app+$3D8
    clr.b 330(a6) ; app+$14A
    move.l 222(a6),-(sp) ; app+$DE
    move.w d1,-(sp)
    bsr.w sub_0de6
loc_17e8:
    bsr.w call_activatewindow
loc_17ec:
    bsr.w sub_5ede
loc_17f0:
    bsr.w sub_052a
loc_17f4:
    move.w (sp)+,d1
    cmp.w #$1d,d1
    bne.s loc_1804
loc_17fc:
    tst.b 354(a6) ; app+$162
    bne.w loc_4462
loc_1804:
    bsr.w sub_6a5a
loc_1808:
    st 229(a6) ; app+$E5
    move.l (sp)+,222(a6) ; app+$DE
    rts
loc_1812:
    bsr.w sub_3f70
loc_1816:
    moveq #7,d1
    tst.l 984(a6) ; app+$3D8
    bne.w loc_1836
loc_1820:
    move.b 330(a6),d0 ; app+$14A
    beq.s loc_17d6
loc_1826:
    bra.s loc_182c
loc_1828:
    moveq #11,d1
    bra.s loc_17d6
loc_182c:
    subq.l #1,404(a6) ; app+$194
    beq.s loc_1828
loc_1832:
    bra.w loc_193c
loc_1836:
    moveq #0,d3
    movea.l 984(a6),a0 ; app+$3D8
    clr.l 984(a6) ; app+$3D8
    movea.l (a0),a1
    move.w #$4afc,(a1)
    move.w 90(a6),d0 ; app+$5A
    andi.w #$7fff,d0
    or.w 988(a6),d0 ; app+$3DC
    move.w d0,90(a6) ; app+$5A
    bpl.w loc_1926
loc_185a:
    tst.b 330(a6) ; app+$14A
    beq.w loc_17d6
loc_1862:
    bra.s loc_1820
loc_1864:
    pea 1374(a6) ; app+$55E
    cmpa.l (sp)+,a1
    beq.s loc_18da
loc_186c:
    cmpa.l 1380(a6),a1 ; app+$564
    beq.s loc_18ee
loc_1872:
    st 1383(a6) ; app+$567
    bsr.w sub_3e3c
loc_187a:
    bne.s loc_18d4
loc_187c:
    movem.l a0-a1,-(sp)
    bsr.w sub_3f70
loc_1884:
    movem.l (sp)+,a0-a1
    move.w 6(a0),d0
    cmp.w #$3,d0
    beq.s loc_18ce
loc_1892:
    cmp.w #$1,d0
    beq.s loc_18c0
loc_1898:
    cmp.w #$2,d0
    beq.s loc_18ba
loc_189e:
    lea 12(a0),a4
    movem.l a0-a1,-(sp)
    bsr.w sub_6b70
loc_18aa:
    movem.l (sp)+,a0-a1
    bne.s loc_18ea
loc_18b0:
    tst.b d1
    bne.s loc_18ea
loc_18b4:
    tst.l d2
    beq.s loc_18ea
loc_18b8:
    bra.s loc_18c6
loc_18ba:
    addq.l #1,8(a0)
    bra.s loc_18ea
loc_18c0:
    subq.l #1,8(a0)
    bne.s loc_18ea
loc_18c6:
    move.w 4(a0),(a1)
    clr.w 6(a0)
loc_18ce:
    moveq #11,d1
    bra.w loc_17d6
loc_18d4:
    moveq #10,d1
    bra.w loc_17d6
loc_18da:
    move.l 1376(a6),app_exec_base_0054(a6) ; app+$560
    bsr.w sub_3f70
loc_18e4:
    moveq #7,d1
    bra.w loc_17d6
loc_18ea:
    moveq #0,d3
    bra.s loc_190a
loc_18ee:
    move.w 1384(a6),(a1) ; app+$568
    moveq #-42,d0
    move.l d0,1380(a6) ; app+$564
    movea.l 1388(a6),a0 ; app+$56C
    movea.l 0(a0),a1
    move.w #$4afc,(a1)
    bsr.w sub_3f70
loc_1908:
    st d3
loc_190a:
    btst #0,87(a6) ; app+$57
    bne.s loc_1926
loc_1912:
    movea.l app_exec_base_0054(a6),a2
    bsr.w call_typeofmem
loc_191a:
    bne.s loc_1926
loc_191c:
    movea.l a2,a1
    bsr.w sub_3e3c
loc_1922:
    beq.w loc_199e
loc_1926:
    tst.b d3
    beq.s loc_193c
loc_192a:
    move.l a3,-(sp)
    bsr.w sub_052a
loc_1930:
    moveq #37,d1
    bsr.w sub_6a5a
loc_1936:
    st 229(a6) ; app+$E5
    movea.l (sp)+,a3
loc_193c:
    movem.l 16(a6),d0-d7/a0-a5 ; app+$10
    movem.l d0-d7/a0-a5,dat_8916
    movem.l 72(a6),d0-d1 ; app+$48
    movem.l d0-d1,dat_894e
    move.l app_exec_base_0054(a6),dat_890c
    move.w 90(a6),dat_8910 ; app+$5A
    moveq #0,d0 ; SetSignal: newSignals
    moveq #0,d1 ; SetSignal: signalMask
    move.b dat_895e(pc),d2
    bset d2,d1
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSetSignal(a6) ; app-$132
loc_197c:
    movea.l (sp)+,a6
    movea.l dat_895a(pc),a1 ; Signal: task
    moveq #0,d0 ; Signal: signalSet
    move.b dat_88f4(pc),d1
    bset d1,d0
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSignal(a6) ; app-$144
loc_1994:
    movea.l (sp)+,a6
    move.b #$1,308(a6) ; app+$134
    rts
loc_199e:
    move.w 90(a6),d0 ; app+$5A
    andi.w #$8000,d0
    move.w d0,988(a6) ; app+$3DC
    move.l a0,984(a6) ; app+$3D8
    move.w 4(a0),(a1)
    bset #7,90(a6) ; app+$5A
    bra.w loc_1926
supervisor_userfunc:
    movec cacr,d1 ; 68010+
    move.l d1,-(sp)
    bclr #0,d1
    or.b d0,d1
    movec d1,cacr ; 68010+
    move.l (sp)+,d0
    rte
sub_19d0:
    pea sub_19d4(pc)
sub_19d4:
    move.w #$4,10(a3)
    move.w app_rectfill_ymax(a6),d0
    add.w d0,12(a3)
    rts
sub_19e4:
; --- unverified ---
    move.l a3,-(sp)
    move.l a0,-(sp)
    moveq #4,d3
    bsr.s esc_to_abort
hint_19ec:
; --- unverified ---
    movea.l (sp)+,a0
    bsr.w sub_6a6a
hint_19f2:
    dc.b    $37,$7c,$00,$04,$00,$0a,$30,$2e,$00,$d8,$d1,$6b,$00,$0c,$49,$ee
    dc.b    $0a,$d4,$42,$14,$78,$00
hint_1a08:
; --- unverified ---
    bsr.w loc_59c2
hint_1a0c:
; --- unverified ---
    bne.s hint_1a34
hint_1a0e:
; --- unverified ---
    tst.b (a4)
    beq.s hint_1a34
hint_1a12:
; --- unverified ---
    bsr.w sub_6b70
hint_1a16:
; --- unverified ---
    bne.s hint_1a1c
hint_1a18:
; --- unverified ---
    tst.b d1
    beq.s hint_1a26
hint_1a1c:
; --- unverified ---
    bsr.w sub_5e54
hint_1a20:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bra.s hint_1a08
hint_1a26:
; --- unverified ---
    move.l d2,-(sp)
    bsr.w sub_5d9c
hint_1a2c:
; --- unverified ---
    move.l (sp)+,d2
    movea.l (sp)+,a3
    moveq #0,d0
    rts
hint_1a34:
; --- unverified ---
    bsr.w sub_5d9c
hint_1a38:
; --- unverified ---
    movea.l (sp)+,a3
    moveq #-1,d2
    rts
esc_to_abort:
    moveq #8,d2
    add.w 226(a6),d2 ; app+$E2
    lea str_8524(pc),a2
sub_1a48:
    movem.w 2158(a6),d0-d1/d4 ; app+$86E
    add.w 2154(a6),d0 ; app+$86A
    add.w 2154(a6),d0 ; app+$86A
    sub.w d2,d0
    lsr.w #1,d0
    sub.w d3,d1
    mulu.w app_rectfill_ymax(a6),d1
    lea 1930(a6),a3 ; app+$78A
    clr.b 60(a3)
    bsr.w sub_5b1e
loc_1a6c:
    sf 20(a3)
    move.w #$4,10(a3)
    move.w app_rectfill_ymax(a6),12(a3)
    rts
sub_1a7e:
    move.l a0,-(sp)
    bsr.s esc_to_abort
loc_1a82:
    movea.l (sp)+,a0
    bsr.w sub_6a6a
loc_1a88:
    bsr.w sub_19d4
loc_1a8c:
    lea 2772(a6),a4 ; app+$AD4
    clr.b (a4)
    moveq #0,d4
    rts
sub_1a96:
    move.l a1,-(sp)
    move.l a0,-(sp)
    movem.w 2158(a6),d0-d1/d4 ; app+$86E
    moveq #30,d2
    moveq #5,d3
    lea pcref_8568(pc),a2
    bsr.s sub_1a48
loc_1aaa:
    movea.l (sp)+,a0
    bsr.s sub_1aba
loc_1aae:
    move.w app_rectfill_ymax(a6),d0
    add.w d0,d0
    add.w d0,12(a3)
    movea.l (sp)+,a0
sub_1aba:
    move.l a0,-(sp)
    movea.l a0,a1
loc_1abe:
    tst.b (a0)+
    bne.s loc_1abe
loc_1ac2:
    lea 30(a1),a1
    suba.l a0,a1
    move.w a1,d0
    lsr.w #1,d0
    move.w d0,10(a3)
    movea.l (sp)+,a0
    bra.w sub_6a6a
sub_1ad6:
    move.l a3,-(sp)
    lea str_855f(pc),a1
    bsr.s sub_1a96
loc_1ade:
    bsr.w sub_4120
loc_1ae2:
    bmi.s loc_1ade
loc_1ae4:
    cmp.b #$1b,d1
    beq.s loc_1af0
loc_1aea:
    cmp.b #$a,d1
    bne.s loc_1ade
loc_1af0:
    bsr.w sub_5d9c
loc_1af4:
    movea.l (sp)+,a3
    rts
loc_1af8:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOIoErr(a6) ; app-$84
loc_1b02:
    movea.l (sp)+,a6
amigados_error_12345:
    move.l a4,-(sp)
    lea str_87fa(pc),a4
    moveq #0,d1
    move.w d0,d1
    lea loc_1b24(pc),a2
    bsr.w sub_6ae0
loc_1b16:
    clr.b (a4)+
    movea.l (sp)+,a4
    bsr.w call_activatewindow
loc_1b1e:
    lea str_87eb(pc),a0
    bra.s sub_1ad6
loc_1b24:
    move.b d1,(a4)+
    rts
sub_1b28:
; --- unverified ---
    lea str_8639(pc),a1
    bsr.w sub_1a96
hint_1b30:
; --- unverified ---
    bsr.w sub_4120
hint_1b34:
; --- unverified ---
    bmi.s hint_1b30
hint_1b36:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$59,d1
    beq.s hint_1b4a
hint_1b40:
; --- unverified ---
    cmp.b #$4e,d1
    beq.s hint_1b4a
hint_1b46:
    dc.b    $b2,$3c,$00,$1b
hint_1b4a:
; --- unverified ---
    move.w d1,-(sp)
    bsr.w sub_5d9c
hint_1b50:
; --- unverified ---
    move.w (sp)+,d1
    cmp.b #$59,d1
    rts
hint_1b58:
; --- unverified ---
    tst.l d1
    bpl.s hint_1ba0
hint_1b5c:
; --- unverified ---
    neg.l d1
    move.b #$2d,(a4)+
    bra.s hint_1ba0
hint_1b64:
; --- unverified ---
    tst.b d1
    bpl.s hint_1b6e
hint_1b68:
    dc.b    $18,$fc,$00,$2d,$44,$01
hint_1b6e:
; --- unverified ---
    andi.l #$ff,d1
    bra.s hint_1ba0
hint_1b76:
; --- unverified ---
    tst.w d1
    bpl.s hint_1b80
hint_1b7a:
    dc.b    $18,$fc,$00,$2d,$44,$41
hint_1b80:
; --- unverified ---
    andi.l #$ffff,d1
    bra.s hint_1ba0
hint_1b88:
; --- unverified ---
    move.l d1,d0
    bsr.w hint_7f7a
hint_1b8e:
; --- unverified ---
    beq.s hint_1ba0
hint_1b90:
; --- unverified ---
    tst.b 1426(a6) ; app+$592
    beq.w hint_7bf0
hint_1b98:
; --- unverified ---
    move.b #$7b,(a4)+
    bra.w hint_7bf0
hint_1ba0:
; --- unverified ---
    cmp.l #$a,d1
    bcc.s hint_1bba
hint_1ba8:
; --- unverified ---
    addi.b #$30,d1
    move.b d1,(a4)+
    rts
hint_1bb0:
; --- unverified ---
    move.l d2,-(sp)
    st d2
    swap d1
    moveq #3,d0
    bra.s hint_1bc4
hint_1bba:
    dc.b    $18,$fc,$00,$24
hint_1bbe:
    dc.b    $2f,$02,$74,$00,$70,$07
hint_1bc4:
; --- unverified ---
    rol.l #4,d1
    move.w d1,-(sp)
    andi.b #$f,d1
    bne.s hint_1bd2
hint_1bce:
; --- unverified ---
    tst.b d2
    beq.s hint_1be2
hint_1bd2:
; --- unverified ---
    st d2
    cmp.b #$9,d1
    ble.s hint_1bdc
hint_1bda:
    dc.b    $5e,$01
hint_1bdc:
    dc.b    $06,$01,$00,$30,$18,$c1
hint_1be2:
; --- unverified ---
    move.w (sp)+,d1
    dbf d0,hint_1bc4
hint_1be8:
; --- unverified ---
    move.l (sp)+,d2
    rts
hint_1bec:
; --- unverified ---
    lea pcref_1c06(pc),a0
    rol.l #1,d1
    move.b 0(a0,d1.w),(a4)+
    move.b 1(a0,d1.w),d0
    beq.s hint_1bfe
hint_1bfc:
    dc.b    $18,$c0
hint_1bfe:
; --- unverified ---
    ror.l #1,d1
    move.b #$20,(a4)+
    rts
pcref_1c06:
    dc.b    $74,$00,$66,$00,$68,$69
hint_1c0c:
    dc.b    $6c,$73
hint_1c0e:
    dc.b    $63,$63
hint_1c10:
    dc.b    $63,$73
hint_1c12:
    dc.b    $6e,$65
hint_1c14:
    dc.b    $65,$71
hint_1c16:
    dc.b    "vcvsplmi"
hint_1c1e:
    dc.b    $67,$65
hint_1c20:
; --- unverified ---
    bge.s loc_1c96
hint_1c22:
; --- unverified ---
    beq.s loc_1c98
hint_1c24:
    dc.b    $6c,$65
hint_1c26:
; --- unverified ---
    lea str_1c3a(pc),a0
    ext.w d5
    move.b #$2e,(a4)+
    move.b 0(a0,d5.w),(a4)+
    move.b #$20,(a4)+
    rts
str_1c3a:
    dc.b    $62,$77
hint_1c3c:
    dc.b    $6c,$3f
hint_1c3e:
; --- unverified ---
    bcc.w loc_5e3a
hint_1c42:
; --- unverified ---
    ori.b #$81,(a2)+
    rol.l #2,d1
    move.b 0(a0,d1.w),(a4)+
    move.b 1(a0,d1.w),(a4)+
    move.b 2(a0,d1.w),(a4)+
    move.b #$20,(a4)+
    ror.l #2,d1
    rts
pcref_1c5c:
; --- unverified ---
    moveq #115,d2
    moveq #32,d2
    bls.s hint_1cca
hint_1c62:
; --- unverified ---
    beq.s loc_1c84
hint_1c64:
; --- unverified ---
    bls.s hint_1cd2
hint_1c66:
    dc.b    $72,$20
    dc.b    $73,$65,$74,$20
sub_1c6c:
    dc.b    $02,$01,$00,$07
hint_1c70:
    dc.b    $06,$01,$00
hint_1c73:
    dc.b    $30
    dc.b    $75
sub_1c78:
    move.w (a5)+,d7
    clr.b 332(a6) ; app+$14C
loc_1c7e:
    lea pcref_379c(pc),a0
    clr.l d0
loc_1c84:
    addq.l #1,d0
    move.w d7,d2
    and.w (a0)+,d2
    cmp.w (a0)+,d2
    bne.s loc_1c84
loc_1c8e:
    moveq #0,d1
    lea pcref_3934(pc),a0
loc_1c94:
    move.b (a0)+,d1
loc_1c96:
    subq.b #1,d0
loc_1c98:
    beq.s loc_1c9e
loc_1c9a:
    adda.l d1,a0
    bra.s loc_1c94
loc_1c9e:
    move.b (a0)+,d2
    lea 2472(a6),a4 ; app+$9A8
    subq.b #2,d1
    bcs.s loc_1cae
loc_1ca8:
    move.b (a0)+,(a4)+
    dbf d1,loc_1ca8
loc_1cae:
    move.b d2,d6
    bsr.s sub_1cd4
loc_1cb2:
    move.b #$a,(a4)+
    clr.l d0
    rts
sub_1cba:
    ext.w d0
    add.w d0,d0
    move.w 0(a0,d0.w),d0
    jmp 0(a0,d0.w) ; unresolved_indirect_core:index.brief
sub_1cc6:
    dc.b    $42,$80,$10,$18
hint_1cca:
    dc.b    $53,$00
hint_1ccc:
; --- unverified ---
    move.b (a0)+,(a4)+
    dbf d0,hint_1ccc
hint_1cd2:
; --- unverified ---
    rts
sub_1cd4:
    lea pcref_1ce6(pc),a0
    move.b d6,d0
    move.w d7,d5
    andi.w #$c0,d5
    lsr.w #6,d5
    bsr.s sub_1cba
loc_1ce4:
    rts
pcref_1ce6:
    dc.b    $ff,$fe,$14,$e8,$00,$72,$00,$cc,$01,$20,$01,$4a,$01,$6e,$01,$de
    dc.b    $01,$e4,$01,$f0,$02,$00,$02,$10,$02,$2a,$02,$58,$02,$68,$02,$78
    dc.b    $03,$40,$03,$7a,$03,$a8,$03,$c4,$03,$f2,$04,$06,$04,$2a,$04,$8e
    dc.b    $05,$06,$05,$1e,$14,$e8,$14,$e8,$05,$7a,$05,$ba,$06,$5a,$06,$4a
    dc.b    $06,$ec,$07,$6c,$07,$72,$08,$d4,$09,$2e,$01,$e4,$09,$36,$09,$46
    dc.b    $09,$58,$13,$44,$13,$b0,$14,$04,$14,$14,$14,$42,$14,$58,$14,$68
    dc.b    $14,$7a,$14,$8c,$0b,$5a,$09,$f2,$0a,$56,$09,$e2,$10,$b0,$07,$e4
    dc.b    $08,$54
sub_1d58:
; --- unverified ---
    bsr.w hint_1c26
hint_1d5c:
; --- unverified ---
    move.b #$23,(a4)+
    tst.b d5
    bne.s hint_1d6c
hint_1d64:
; --- unverified ---
    move.w (a5)+,d1
    bsr.w hint_1b6e
hint_1d6a:
; --- unverified ---
    bra.s hint_1d80
hint_1d6c:
; --- unverified ---
    cmp.b #$1,d5
    beq.s hint_1d7a
hint_1d72:
; --- unverified ---
    move.l (a5)+,d1
    bsr.w hint_1b88
hint_1d78:
; --- unverified ---
    bra.s hint_1d80
hint_1d7a:
; --- unverified ---
    move.w (a5)+,d1
    bsr.w hint_1b80
hint_1d80:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b d7,d0
    andi.b #$3f,d0
    cmp.b #$3c,d0
    bne.s hint_1dac
hint_1d90:
; --- unverified ---
    tst.b d5
    bne.s hint_1da0
hint_1d94:
; --- unverified ---
    lea pcref_1d9c(pc),a0
    bra.w sub_1cc6
pcref_1d9c:
; --- unverified ---
    bchg d1,-(a3)
    bls.s hint_1e12
hint_1da0:
; --- unverified ---
    lea pcref_1da8(pc),a0
    bra.w sub_1cc6
pcref_1da8:
; --- unverified ---
    andi.w #$7200,61(a3,d7.l)
    bra.w hint_31d0
hint_1db2:
; --- unverified ---
    moveq #108,d0
    btst #6,d7
    bne.s hint_1dbc
hint_1dba:
    dc.b    $70,$77
hint_1dbc:
; --- unverified ---
    move.b d0,(a4)+
    move.b #$20,(a4)+
    move.b d7,d2
    move.w d7,d3
    lsr.w #8,d3
    lsr.w #1,d3
    lea pcref_1de2(pc),a0
    lea pcref_1dfc(pc),a1
    btst #7,d7
    beq.s hint_1dda
hint_1dd8:
    dc.b    $c3,$48
hint_1dda:
; --- unverified ---
    jsr (a0) ; unresolved_indirect_hint:ind
hint_1ddc:
; --- unverified ---
    move.b #$2c,(a4)+
    jmp (a1) ; unresolved_indirect_hint:ind
pcref_1de2:
; --- unverified ---
    move.w (a5)+,d1
    bsr.w hint_1b76
hint_1de8:
; --- unverified ---
    move.b #$28,(a4)+
    move.b #$61,(a4)+
    move.b d2,d1
    bsr.w sub_1c6c
hint_1df6:
; --- unverified ---
    move.b #$29,(a4)+
    rts
pcref_1dfc:
; --- unverified ---
    move.b #$64,(a4)+
    move.b d3,d1
    bra.w sub_1c6c
hint_1e06:
; --- unverified ---
    move.b d5,d1
    bsr.w hint_1c40
hint_1e0c:
    dc.b    $42,$05,$18,$fc,$00,$64
hint_1e12:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    lsr.w #1,d1
    bsr.w sub_1c6c
hint_1e1c:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #61,d4
    move.w d7,d0
    andi.b #$c0,d0
    bne.s hint_1e2c
hint_1e2a:
    dc.b    $78,$fd
hint_1e2c:
; --- unverified ---
    bra.w hint_31d0
hint_1e30:
; --- unverified ---
    move.b d5,d1
    bsr.w hint_1c40
hint_1e36:
; --- unverified ---
    clr.b d5
    move.b #$23,(a4)+
    move.w (a5)+,d1
    bsr.w hint_1b6e
hint_1e42:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #61,d4
    move.w d7,d0
    andi.b #$c0,d0
    bne.s hint_1e2c
hint_1e50:
; --- unverified ---
    moveq #125,d4
    bra.s hint_1e2c
hint_1e54:
; --- unverified ---
    move.w d7,d5
    moveq #12,d0
    lsr.w d0,d5
    andi.w #$3,d5
    move.b pcref_1ec0(pc,d5.w),d5
    move.w d7,-(sp)
    moveq #-1,d4
    bsr.w hint_31d0
hint_1e6a:
; --- unverified ---
    move.w (sp)+,d7
    move.b 331(a6),d0 ; app+$14B
    move.l 334(a6),338(a6) ; app+$14E
    sf 331(a6) ; app+$14B
    move.w d0,-(sp)
    move.b #$2c,(a4)+
    move.w d7,d1
    move.b #$9,d0
    lsr.w d0,d1
    andi.w #$7,d1
    move.w d7,d2
    lsr.w #6,d2
    andi.w #$7,d2
    moveq #63,d4
    bsr.w hint_31e2
hint_1e9a:
; --- unverified ---
    move.w (sp)+,d0
    tst.b 331(a6) ; app+$14B
    beq.s hint_1eba
hint_1ea2:
; --- unverified ---
    tst.b d0
    beq.s hint_1ebe
hint_1ea6:
; --- unverified ---
    st 332(a6) ; app+$14C
    movem.l 334(a6),d0-d1 ; app+$14E
    exg
    movem.l d0-d1,334(a6) ; app+$14E
    rts
hint_1eba:
    dc.b    $1d,$40,$01,$4b
hint_1ebe:
; --- unverified ---
    rts
pcref_1ec0:
; --- unverified ---
    btst d1,d0
    andi.b #$1d,d1
    bra.w hint_1b80
hint_1eca:
; --- unverified ---
    andi.b #$7,d7
    addi.b #$30,d7
    move.b d7,(a4)+
    rts
hint_1ed6:
; --- unverified ---
    bsr.s hint_1eca
hint_1ed8:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$23,(a4)+
    move.w (a5)+,d1
    bra.w hint_1b76
hint_1ee6:
; --- unverified ---
    bsr.s hint_1eca
hint_1ee8:
; --- unverified ---
    lea pcref_1ef0(pc),a0
    bra.w sub_1cc6
pcref_1ef0:
; --- unverified ---
    subi.b #$73,28704(a4)
    andi.w #$f,d7
    cmp.b #$a,d7
    bcs.s hint_1f08
hint_1f00:
    dc.b    $18,$fc,$00,$31,$04,$07,$00,$0a
hint_1f08:
; --- unverified ---
    addi.b #$30,d7
    move.b d7,(a4)+
    rts
hint_1f10:
; --- unverified ---
    move.b -(a4),d0
    cmp.b #$2e,d0
    beq.s hint_1f20
hint_1f18:
; --- unverified ---
    addq.l #1,a4
    bsr.w hint_1c26
hint_1f1e:
; --- unverified ---
    bra.s hint_1f22
hint_1f20:
    dc.b    $7a,$02
hint_1f22:
; --- unverified ---
    move.b 2472(a6),d0 ; app+$9A8
    moveq #100,d4
    cmp.b #$6a,d0
    beq.w hint_31d0
hint_1f30:
; --- unverified ---
    cmp.b #$70,d0
    beq.w hint_31d0
hint_1f38:
; --- unverified ---
    moveq #61,d4
    bra.w hint_31d0
hint_1f3e:
; --- unverified ---
    moveq #1,d5
    moveq #-3,d4
    bsr.w hint_31d0
hint_1f46:
; --- unverified ---
    move.b #$2c,(a4)+
    bra.w hint_1d94
hint_1f4e:
; --- unverified ---
    moveq #1,d5
    moveq #-3,d4
    bsr.w hint_31d0
hint_1f56:
; --- unverified ---
    move.b #$2c,(a4)+
    bra.w hint_1da0
hint_1f5e:
; --- unverified ---
    move.b d7,d5
    lsr.b #6,d5
    andi.b #$1,d5
    addq.b #1,d5
    bsr.w hint_1c26
hint_1f6c:
; --- unverified ---
    move.w (a5)+,-(sp)
    moveq #108,d4
    bsr.w hint_31d0
hint_1f74:
    dc.b    $1d,$7c,$00,$03,$01,$4d,$3c,$1f,$18,$fc,$00,$2c
hint_1f80:
    dc.b    $70,$0f
hint_1f82:
; --- unverified ---
    roxl.w #1,d6
    roxr.w #1,d1
    dbf d0,hint_1f82
hint_1f8a:
; --- unverified ---
    move.w d1,d3
    ror.w #8,d3
    move.b #$64,d4
    bsr.s hint_1fa6
hint_1f94:
; --- unverified ---
    tst.b d3
    beq.s hint_1fa0
hint_1f98:
; --- unverified ---
    tst.b d1
    beq.s hint_1fa0
hint_1f9c:
    dc.b    $18,$fc,$00,$2f
hint_1fa0:
    dc.b    $36,$01,$18,$3c,$00,$61
hint_1fa6:
; --- unverified ---
    tst.b d3
    beq.s hint_1fea
hint_1faa:
    dc.b    $70,$07
hint_1fac:
; --- unverified ---
    btst d0,d3
    beq.s hint_201e
hint_1fb0:
; --- unverified ---
    move.b d4,(a4)+
    cmp.b #$66,d4
    bne.s hint_1fbc
hint_1fb8:
    dc.b    $18,$fc,$00,$70
hint_1fbc:
; --- unverified ---
    moveq #55,d6
    sub.b d0,d6
    move.b d6,(a4)+
    tst.b d0
    beq.s hint_1fea
hint_1fc6:
; --- unverified ---
    subq.b #1,d0
    btst d0,d3
    beq.s hint_201a
hint_1fcc:
; --- unverified ---
    tst.b d0
    bne.s hint_1fec
hint_1fd0:
; --- unverified ---
    move.b #$2d,(a4)+
    tst.b 1425(a6) ; app+$591
    beq.s hint_1fe6
hint_1fda:
; --- unverified ---
    move.b d4,(a4)+
    cmp.b #$66,d4
    bne.s hint_1fe6
hint_1fe2:
    dc.b    $18,$fc,$00,$70
hint_1fe6:
    dc.b    $18,$fc,$00,$37
hint_1fea:
; --- unverified ---
    rts
hint_1fec:
; --- unverified ---
    subq.b #1,d0
    btst d0,d3
    bne.s hint_2014
hint_1ff2:
; --- unverified ---
    move.b #$2d,(a4)+
    tst.b 1425(a6) ; app+$591
    beq.s hint_2008
hint_1ffc:
; --- unverified ---
    move.b d4,(a4)+
    cmp.b #$66,d4
    bne.s hint_2008
hint_2004:
    dc.b    $18,$fc,$00,$70
hint_2008:
; --- unverified ---
    moveq #54,d6
    sub.b d0,d6
    move.b d6,(a4)+
    move.b #$2f,(a4)+
    bra.s hint_201e
hint_2014:
; --- unverified ---
    tst.b d0
    beq.s hint_1fd0
hint_2018:
; --- unverified ---
    bra.s hint_1fec
hint_201a:
    dc.b    $18,$fc,$00,$2f
hint_201e:
; --- unverified ---
    subq.b #1,d0
    bcc.s hint_1fac
hint_2022:
; --- unverified ---
    subq.l #1,a4
    rts
hint_2026:
; --- unverified ---
    move.b d7,d5
    lsr.b #6,d5
    andi.b #$1,d5
    addq.b #1,d5
    bsr.w hint_1c26
hint_2034:
; --- unverified ---
    move.w (a5)+,d6
    move.w d7,d2
    andi.b #$38,d2
    cmp.b #$20,d2
    bne.s hint_205a
hint_2042:
; --- unverified ---
    move.w d6,d1
    bsr.w hint_1f8a
hint_2048:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #52,d4
    bsr.w hint_31d0
hint_2052:
; --- unverified ---
    move.b #$3,333(a6) ; app+$14D
    rts
hint_205a:
; --- unverified ---
    bsr.w hint_1f80
hint_205e:
; --- unverified ---
    bra.s hint_2048
hint_2060:
; --- unverified ---
    moveq #1,d5
    btst #7,d7
    bne.s hint_206a
hint_2068:
    dc.b    $7a,$02
hint_206a:
; --- unverified ---
    bsr.w hint_1c26
hint_206e:
; --- unverified ---
    moveq #1,d5
    moveq #-3,d4
    bsr.w hint_31d0
hint_2076:
; --- unverified ---
    lsr.w #1,d7
    lsr.w #8,d7
    andi.b #$7,d7
    addi.b #$30,d7
    move.b #$2c,(a4)+
    move.b #$64,(a4)+
    move.b d7,(a4)+
    rts
hint_208e:
; --- unverified ---
    moveq #2,d5
    moveq #100,d4
    bsr.w hint_31d0
hint_2096:
; --- unverified ---
    move.b #$9,d0
    move.w d7,d1
    lsr.w d0,d1
    move.b #$2c,(a4)+
    move.b #$61,(a4)+
    bra.w sub_1c6c
hint_20aa:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    andi.b #$f,d1
    bsr.w hint_1bec
hint_20b6:
    dc.b    $18,$fc,$00,$64,$02,$07,$00,$07,$06,$07,$00,$30,$18,$c7
hint_20c4:
; --- unverified ---
    move.b #$2c,(a4)+
    move.l a5,d1
    move.w (a5)+,d2
    ext.l d2
    add.l d2,d1
    add.l 4(a6),d1 ; app+$4
    bra.w hint_1b88
hint_20d8:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    andi.w #$f,d1
    bsr.w hint_1bec
hint_20e4:
; --- unverified ---
    clr.b d5
    moveq #61,d4
    bra.w hint_31d0
hint_20ec:
; --- unverified ---
    bsr.w hint_1c26
hint_20f0:
; --- unverified ---
    move.b #$23,(a4)+
    move.w d7,d1
    lsr.w #8,d1
    lsr.w #1,d1
    andi.w #$7,d1
    bne.s hint_2102
hint_2100:
    dc.b    $72,$08
hint_2102:
; --- unverified ---
    bsr.w hint_1c70
hint_2106:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #63,d4
    bra.w hint_31d0
hint_2110:
; --- unverified ---
    move.w d7,d0
    andi.w #$f8,d0
    move.b d7,d2
    move.w d7,d1
    lsr.w #8,d1
    lsr.w #1,d1
    cmp.b #$40,d0
    beq.s hint_213a
hint_2124:
; --- unverified ---
    cmp.b #$48,d0
    beq.s hint_2150
hint_212a:
; --- unverified ---
    cmp.b #$88,d0
    beq.s hint_2162
hint_2130:
; --- unverified ---
    move.b #$3f,(a4)+
    move.b #$3f,(a4)+
    rts
hint_213a:
; --- unverified ---
    move.b #$64,(a4)+
    bsr.w sub_1c6c
hint_2142:
    dc.b    $18,$fc,$00,$2c,$18,$fc,$00,$64
hint_214a:
; --- unverified ---
    move.b d2,d1
    bra.w sub_1c6c
hint_2150:
; --- unverified ---
    move.b #$61,(a4)+
    bsr.w sub_1c6c
hint_2158:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$61,(a4)+
    bra.s hint_214a
hint_2162:
; --- unverified ---
    move.b #$64,(a4)+
    bsr.w sub_1c6c
hint_216a:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$61,(a4)+
    bra.s hint_214a
hint_2174:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    andi.b #$f,d1
    beq.s hint_218a
hint_217e:
; --- unverified ---
    cmp.b #$1,d1
    beq.s hint_2194
hint_2184:
; --- unverified ---
    bsr.w hint_1bec
hint_2188:
; --- unverified ---
    bra.s hint_219c
hint_218a:
; --- unverified ---
    subq.l #1,a4
    move.l #$62726120,(a4)+ ; 'bra '
    bra.s hint_219c
hint_2194:
    dc.b    $53,$8c,$28,$fc,$62,$73,$72,$20
hint_219c:
; --- unverified ---
    move.b d7,d1
    beq.s hint_21e4
hint_21a0:
; --- unverified ---
    cmp.b #$ff,d1
    bne.s hint_21bc
hint_21a6:
; --- unverified ---
    move.b #$2e,-1(a4)
    move.b #$6c,(a4)+
    move.b #$20,(a4)+
    move.l (a5),d1
    add.l a5,d1
    addq.w #4,a5
    bra.s hint_21d0
hint_21bc:
    dc.b    $19,$7c,$00,$2e,$ff,$ff,$18,$fc,$00,$73,$18,$fc,$00,$20,$48,$81
    dc.b    $48,$c1
hint_21ce:
    dc.b    $d2,$8d
hint_21d0:
; --- unverified ---
    add.l 4(a6),d1 ; app+$4
    bsr.w hint_1b88
hint_21d8:
; --- unverified ---
    tst.b 1426(a6) ; app+$592
    beq.s hint_21e2
hint_21de:
    dc.b    $18,$fc,$00,$7d
hint_21e2:
; --- unverified ---
    rts
hint_21e4:
; --- unverified ---
    move.w (a5)+,d1
    ext.l d1
    subq.l #2,d1
    bra.s hint_21ce
hint_21ec:
; --- unverified ---
    move.b d7,d1
    bsr.w hint_1b64
hint_21f2:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$64,(a4)+
    move.w d7,d1
    lsr.w #8,d1
    lsr.w #1,d1
    bra.w sub_1c6c
hint_2204:
; --- unverified ---
    moveq #-1,d0
    cmpi.b #$78,0(a4,d0.w)
    bne.s hint_2212
hint_220e:
; --- unverified ---
    bsr.w hint_1c26
hint_2212:
; --- unverified ---
    move.b d7,d1
    move.w d7,d2
    lsr.w #8,d2
    lsr.w #1,d2
    btst #3,d7
    beq.s hint_2244
hint_2220:
; --- unverified ---
    move.b #$2d,(a4)+
    move.b #$28,(a4)+
    move.b #$61,(a4)+
    bsr.w sub_1c6c
hint_2230:
; --- unverified ---
    lea pcref_225a(pc),a0
    bsr.w sub_1cc6
hint_2238:
; --- unverified ---
    move.b d2,d1
    bsr.w sub_1c6c
hint_223e:
; --- unverified ---
    move.b #$29,(a4)+
    rts
hint_2244:
; --- unverified ---
    move.b #$64,(a4)+
    bsr.w sub_1c6c
hint_224c:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$64,(a4)+
    move.b d2,d1
    bra.w sub_1c6c
pcref_225a:
; --- unverified ---
    btst d2,11309(a1)
    movea.l -(a1),a4
    bsr.w hint_1c26
hint_2264:
; --- unverified ---
    cmp.b #$3,d5
    bne.s hint_2270
hint_226a:
; --- unverified ---
    lea 2472(a6),a4 ; app+$9A8
    bra.s hint_22a0
hint_2270:
; --- unverified ---
    move.w d7,d1
    move.b #$28,(a4)+
    move.b #$61,(a4)+
    bsr.w sub_1c6c
hint_227e:
; --- unverified ---
    lea pcref_229a(pc),a0
    bsr.w sub_1cc6
hint_2286:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    lsr.w #1,d1
    bsr.w sub_1c6c
hint_2290:
; --- unverified ---
    move.b #$29,(a4)+
    move.b #$2b,(a4)+
    rts
pcref_229a:
    dc.b    $05,$29,$2b,$2c,$28,$61
hint_22a0:
; --- unverified ---
    lea pcref_22b2(pc),a0
    move.w d7,d5
    lsr.w #6,d5
    andi.b #$7,d5
    move.b d5,d0
    bra.w sub_1cba
pcref_22b2:
    dc.b    $00,$3a,$00,$3a,$00,$3a,$00,$10,$00,$5a,$00,$5a,$00,$5a,$00,$10
    dc.b    $e4,$0d,$02,$05,$00,$01,$52,$05,$28,$fc
    dc.b    "cmpaa",0
    dc.b    $f9,$54
hint_22d4:
; --- unverified ---
    moveq #-1,d4
    bsr.w hint_31d0
hint_22da:
    dc.b    $18,$fc,$00,$2c,$18,$fc,$00,$61
hint_22e2:
; --- unverified ---
    move.w d7,d1
    lsr.w #1,d1
    lsr.w #8,d1
    bra.w sub_1c6c
hint_22ec:
; --- unverified ---
    lea pcref_2308(pc),a0
    bsr.w sub_1cc6
hint_22f4:
; --- unverified ---
    bsr.w hint_1c26
hint_22f8:
; --- unverified ---
    moveq #-1,d4
    bsr.w hint_31d0
hint_22fe:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$64,(a4)+
    bra.s hint_22e2
pcref_2308:
; --- unverified ---
    bchg d1,-(a3)
    blt.s hint_237c
hint_230c:
; --- unverified ---
    andi.b #$3,d5
    lea pcref_232c(pc),a0
    bsr.w sub_1cc6
hint_2318:
; --- unverified ---
    bsr.w hint_1c26
hint_231c:
; --- unverified ---
    move.b #$64,(a4)+
    bsr.s hint_22e2
hint_2322:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #61,d4
    bra.w hint_31d0
pcref_232c:
; --- unverified ---
    bchg d1,-(a5)
    ble.s hint_23a2
hint_2330:
; --- unverified ---
    bsr.w hint_1c26
hint_2334:
; --- unverified ---
    move.w d7,d0
    andi.w #$100,d0
    bne.s hint_2390
hint_233c:
; --- unverified ---
    moveq #-3,d4
    bra.s hint_237a
hint_2340:
; --- unverified ---
    move.w d7,d0
    andi.w #$f1f8,d0
    cmp.w #$c140,d0
    beq.s hint_2358
hint_234c:
; --- unverified ---
    cmp.w #$c148,d0
    beq.s hint_2358
hint_2352:
; --- unverified ---
    cmp.w #$c188,d0
    bne.s hint_2366
hint_2358:
; --- unverified ---
    lea 2472(a6),a4 ; app+$9A8
    move.l #$65786720,(a4)+ ; 'exg '
    bra.w hint_2110
hint_2366:
; --- unverified ---
    cmp.b #$3,d5
    beq.s hint_23ac
hint_236c:
; --- unverified ---
    bsr.w hint_1c26
hint_2370:
; --- unverified ---
    move.w d7,d0
    andi.w #$100,d0
    bne.s hint_2390
hint_2378:
    dc.b    $78,$ff
hint_237a:
; --- unverified ---
    bsr.w hint_31d0
hint_237e:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$64,(a4)+
    move.w d7,d1
    lsr.w #1,d1
    lsr.w #8,d1
    bra.w sub_1c6c
hint_2390:
; --- unverified ---
    move.b #$64,(a4)+
    move.w d7,d1
    lsr.w #1,d1
    lsr.w #8,d1
    bsr.w sub_1c6c
hint_239e:
    dc.b    $18,$fc,$00,$2c
hint_23a2:
; --- unverified ---
    move.w d7,d0
    move.w #$3c,d4
    bra.w hint_31d0
hint_23ac:
; --- unverified ---
    move.w d7,d5
    lsr.w #8,d5
    andi.b #$1,d5
    addq.b #1,d5
    bsr.w hint_1c26
hint_23ba:
; --- unverified ---
    moveq #-1,d4
    bsr.w hint_31d0
hint_23c0:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$61,(a4)+
    move.w d7,d1
    lsr.w #1,d1
    lsr.w #8,d1
    bra.w sub_1c6c
hint_23d2:
; --- unverified ---
    move.w d7,d1
    cmp.b #$3,d5
    beq.s hint_2416
hint_23da:
; --- unverified ---
    lsr.b #2,d1
    bsr.s hint_2426
hint_23de:
; --- unverified ---
    bsr.w hint_1c26
hint_23e2:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    lsr.w #1,d1
    btst #5,d7
    bne.s hint_240c
hint_23ee:
; --- unverified ---
    move.b #$23,(a4)+
    andi.w #$7,d1
    bne.s hint_23fa
hint_23f8:
    dc.b    $72,$08
hint_23fa:
; --- unverified ---
    bsr.w hint_1c70
hint_23fe:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$64,(a4)+
    move.b d7,d1
    bra.w sub_1c6c
hint_240c:
; --- unverified ---
    move.b #$64,(a4)+
    andi.b #$7,d1
    bra.s hint_23fa
hint_2416:
; --- unverified ---
    lsr.w #8,d1
    bsr.s hint_2426
hint_241a:
; --- unverified ---
    move.b #$20,(a4)+
    moveq #2,d5
    moveq #60,d4
    bra.w hint_31d0
hint_2426:
; --- unverified ---
    andi.w #$6,d1
    lea pcref_244a(pc,d1.w),a0
    move.b (a0)+,(a4)+
    move.b (a0),(a4)+
    cmp.b #$4,d1
    bne.s hint_243c
hint_2438:
    dc.b    $18,$fc,$00,$78
hint_243c:
; --- unverified ---
    moveq #108,d1
    moveq #8,d0
    btst d0,d7
    bne.s hint_2446
hint_2444:
    dc.b    $72,$72
hint_2446:
; --- unverified ---
    move.b d1,(a4)+
    rts
pcref_244a:
    dc.b    $61,$73
hint_244c:
    dc.b    $6c,$73
hint_244e:
; --- unverified ---
    moveq #111,d1
    moveq #111,d1
    move.w d7,d1
    bra.w hint_1b80
hint_2458:
; --- unverified ---
    lea -2(a5),a1
    bsr.w sub_3e3c
hint_2460:
; --- unverified ---
    beq.s hint_2464
hint_2462:
; --- unverified ---
    rts
hint_2464:
; --- unverified ---
    lea 2472(a6),a4 ; app+$9A8
    move.w 4(a0),d7
    move.l a0,-(sp)
    bsr.w loc_1c7e
hint_2472:
; --- unverified ---
    move.b #$20,-1(a4)
    move.b #$5b,(a4)+
    movea.l (sp)+,a0
    move.l 8(a0),d1
    move.w 6(a0),d0
    cmp.w #$1,d0
    beq.s hint_24c0
hint_248c:
; --- unverified ---
    cmp.w #$2,d0
    beq.s hint_24bc
hint_2492:
; --- unverified ---
    cmp.w #$3,d0
    beq.s hint_24b6
hint_2498:
    dc.b    $18,$fc,$00,$3f,$43,$e8,$00,$0c,$70,$07
hint_24a2:
; --- unverified ---
    move.b (a1)+,d1
    beq.s hint_24c4
hint_24a6:
; --- unverified ---
    move.b d1,(a4)+
    dbf d0,hint_24a2
hint_24ac:
; --- unverified ---
    move.b #$2e,(a4)+
    move.b #$2e,(a4)+
    bra.s hint_24c4
hint_24b6:
; --- unverified ---
    move.b #$2a,(a4)+
    bra.s hint_24c4
hint_24bc:
    dc.b    $18,$fc,$00
hint_24bf:
    dc.b    $3d
hint_24c0:
; --- unverified ---
    bsr.w hint_1ba0
hint_24c4:
; --- unverified ---
    move.b #$5d,(a4)+
    rts
hint_24ca:
; --- unverified ---
    move.w d7,d0
    andi.w #$3f,d0
    cmp.w #$2e,d0
    bne.s hint_2534
hint_24d6:
; --- unverified ---
    move.l app_exec_base_0054(a6),d0
    addq.l #2,d0
    cmp.l a5,d0
    bne.s hint_24e8
hint_24e0:
; --- unverified ---
    movea.l 72(a6),a0 ; app+$48
    adda.w (a5),a0
    bra.s hint_2506
hint_24e8:
; --- unverified ---
    tst.b 326(a6) ; app+$146
    beq.s hint_2534
hint_24ee:
; --- unverified ---
    move.l 322(a6),d0 ; app+$142
    beq.s hint_2534
hint_24f4:
; --- unverified ---
    btst #0,d0
    bne.s hint_2534
hint_24fa:
; --- unverified ---
    movea.l d0,a2
    bsr.w call_typeofmem
hint_2500:
; --- unverified ---
    bne.s hint_2534
hint_2502:
    dc.b    $20,$52,$d0,$d5
hint_2506:
; --- unverified ---
    bsr.w sub_80ac
hint_250a:
; --- unverified ---
    beq.s hint_2534
hint_250c:
; --- unverified ---
    move.b #$5f,(a4)+
    move.b #$4c,(a4)+
    move.b #$56,(a4)+
    move.b #$4f,(a4)+
    bsr.w hint_7bf0
hint_2520:
; --- unverified ---
    move.b #$28,(a4)+
    move.b #$61,(a4)+
    move.b #$36,(a4)+
    move.b #$29,(a4)+
    addq.w #2,a5
    rts
hint_2534:
; --- unverified ---
    moveq #100,d4
    bra.w hint_31d0
hint_253a:
; --- unverified ---
    tst.l app_freemem_memoryblock(a6)
    beq.s hint_256e
hint_2540:
; --- unverified ---
    move.w d7,d0
    andi.w #$e00,d0
    cmp.w #$c00,d0
    bne.s hint_256e
hint_254c:
; --- unverified ---
    move.w d7,d0
    andi.w #$3f,d0
    cmp.w #$38,d0
    beq.s hint_2572
hint_2558:
; --- unverified ---
    cmp.w #$39,d0
    beq.s hint_257c
hint_255e:
; --- unverified ---
    cmp.w #$3a,d0
    beq.s hint_2582
hint_2564:
; --- unverified ---
    andi.w #$38,d0
    cmp.w #$28,d0
    beq.s hint_259a
hint_256e:
; --- unverified ---
    bra.w hint_1e54
hint_2572:
; --- unverified ---
    moveq #4,d2
    cmp.w (a5),d2
    bne.s hint_256e
hint_2578:
; --- unverified ---
    moveq #2,d0
    bra.s hint_258a
hint_257c:
; --- unverified ---
    move.l (a5),d2
    moveq #4,d0
    bra.s hint_258a
hint_2582:
    dc.b    $34,$15,$48,$c2,$d4,$8d,$70,$02
hint_258a:
; --- unverified ---
    move.l d2,322(a6) ; app+$142
    add.l a5,d0
    addq.l #2,d0
    move.l d0,318(a6) ; app+$13E
    bra.w hint_1e54
hint_259a:
; --- unverified ---
    move.w d7,d0
    andi.w #$7,d0
    btst d0,329(a6) ; app+$149
    beq.s hint_256e
hint_25a6:
; --- unverified ---
    add.w d0,d0
    add.w d0,d0
    lea 48(a6),a0 ; app+$30
    movea.l 0(a0,d0.w),a0
    adda.w (a5),a0
    move.l a0,d2
    moveq #2,d0
    bra.s hint_258a
hint_25ba:
; --- unverified ---
    move.w (a5)+,d2
    move.w d2,d1
    andi.w #$fff,d2
    rol.w #4,d1
    lea 1932(pc),a0
    btst #0,d7
    bne.s hint_25d8
hint_25ce:
; --- unverified ---
    bsr.s hint_25de
hint_25d0:
; --- unverified ---
    move.b #$2c,(a4)+
    bra.w hint_25fc
hint_25d8:
; --- unverified ---
    bsr.s hint_25fc
hint_25da:
    dc.b    $18,$fc,$00,$2c
hint_25de:
; --- unverified ---
    cmp.w (a0)+,d2
    beq.s hint_25ec
hint_25e2:
; --- unverified ---
    move.b (a0),d0
    beq.s hint_25f6
hint_25e6:
; --- unverified ---
    ext.w d0
    adda.w d0,a0
    bra.s hint_25de
hint_25ec:
    dc.b    $52,$88
hint_25ee:
; --- unverified ---
    move.b (a0)+,(a4)+
    bne.s hint_25ee
hint_25f2:
; --- unverified ---
    subq.l #1,a4
    rts
hint_25f6:
; --- unverified ---
    move.b #$3f,(a4)+
    rts
hint_25fc:
; --- unverified ---
    andi.b #$f,d1
    moveq #97,d0
    subq.b #8,d1
    bcc.s hint_260a
hint_2606:
    dc.b    $50,$01,$70,$64
hint_260a:
; --- unverified ---
    move.b d0,(a4)+
    addi.b #$30,d1
    move.b d1,(a4)+
    rts
hint_2614:
; --- unverified ---
    moveq #2,d5
    moveq #61,d4
    bra.w hint_31d0
hint_261c:
; --- unverified ---
    moveq #37,d4
    bsr.s hint_2648
hint_2620:
; --- unverified ---
    cmp.w #$1000,d7
    bcs.s hint_262a
hint_2626:
    dc.b    $18,$fc,$00,$3f
hint_262a:
; --- unverified ---
    rts
hint_262c:
; --- unverified ---
    moveq #101,d4
    bsr.s hint_2648
hint_2630:
    dc.b    $18,$fc,$00,$2c,$32,$07
hint_2636:
; --- unverified ---
    lsr.w #8,d1
    lsr.w #4,d1
    bra.w hint_26b6
hint_263e:
; --- unverified ---
    move.w (a5),d1
    bsr.s hint_2636
hint_2642:
    dc.b    $18,$fc,$00,$2c,$78,$25
hint_2648:
; --- unverified ---
    moveq #2,d5
    move.w (a5),-(sp)
    addq.w #2,a5
    bsr.w hint_31d0
hint_2652:
; --- unverified ---
    move.b #$7b,(a4)+
    move.w (sp)+,d7
    move.w d7,d1
    lsr.w #6,d1
    btst #11,d7
    bne.s hint_266e
hint_2662:
; --- unverified ---
    andi.l #$1f,d1
    bsr.w hint_269e
hint_266c:
; --- unverified ---
    bra.s hint_2676
hint_266e:
; --- unverified ---
    andi.b #$1f,d1
    bsr.w hint_26b6
hint_2676:
; --- unverified ---
    move.b #$3a,(a4)+
    move.w d7,d1
    andi.l #$1f,d1
    btst #5,d7
    bne.s hint_2694
hint_2688:
; --- unverified ---
    tst.b d1
    bne.s hint_268e
hint_268c:
    dc.b    $72,$20
hint_268e:
; --- unverified ---
    bsr.w hint_269e
hint_2692:
; --- unverified ---
    bra.s hint_2698
hint_2694:
; --- unverified ---
    bsr.w hint_26b6
hint_2698:
; --- unverified ---
    move.b #$7d,(a4)+
    rts
hint_269e:
; --- unverified ---
    divu.w #$a,d1
    tst.w d1
    beq.s hint_26ac
hint_26a6:
    dc.b    $06,$01,$00,$30,$18,$c1
hint_26ac:
; --- unverified ---
    swap d1
    addi.b #$30,d1
    move.b d1,(a4)+
    rts
hint_26b6:
; --- unverified ---
    move.b #$64,(a4)+
    cmp.b #$8,d1
    bcs.s hint_26c4
hint_26c0:
    dc.b    $18,$fc,$00,$3f
hint_26c4:
; --- unverified ---
    bra.w sub_1c6c
hint_26c8:
; --- unverified ---
    moveq #52,d4
    btst #6,d7
    beq.s hint_26d2
hint_26d0:
    dc.b    $78,$6c
hint_26d2:
; --- unverified ---
    moveq #2,d5
    bra.w hint_31d0
hint_26d8:
; --- unverified ---
    move.w d7,d1
    andi.w #$7,d1
    move.w d7,d2
    lsr.w #3,d2
    andi.b #$7,d2
    cmp.b #$1,d2
    beq.s hint_2706
hint_26ec:
; --- unverified ---
    cmp.b #$7,d2
    beq.s hint_271e
hint_26f2:
; --- unverified ---
    move.b #$53,(a4)+
    bsr.w hint_278a
hint_26fa:
; --- unverified ---
    move.b #$20,(a4)+
    moveq #61,d4
    moveq #0,d5
    bra.w hint_31e2
hint_2706:
; --- unverified ---
    move.b #$44,(a4)+
    move.b #$42,(a4)+
    bsr.w hint_278a
hint_2712:
; --- unverified ---
    move.b #$20,(a4)+
    bsr.w hint_3206
hint_271a:
; --- unverified ---
    bra.w hint_20c4
hint_271e:
; --- unverified ---
    cmp.b #$2,d1
    bcs.s hint_26f2
hint_2724:
; --- unverified ---
    move.b #$74,(a4)+
    move.b #$72,(a4)+
    move.b #$61,(a4)+
    move.b #$70,(a4)+
    bsr.w hint_278a
hint_2738:
; --- unverified ---
    bra.w hint_3186
hint_273c:
; --- unverified ---
    andi.w #$7f,d7
    beq.s hint_2774
hint_2742:
; --- unverified ---
    move.b #$62,(a4)+
    bsr.s hint_2794
hint_2748:
; --- unverified ---
    btst #6,d7
    beq.s hint_2764
hint_274e:
; --- unverified ---
    move.b #$2e,(a4)+
    move.b #$6c,(a4)+
    move.b #$20,(a4)+
    move.l (a5),d1
    add.l a5,d1
    addq.w #4,a5
    bra.w hint_21d0
hint_2764:
; --- unverified ---
    move.b #$20,(a4)+
    move.w (a5),d1
    ext.l d1
    add.l a5,d1
    addq.w #2,a5
    bra.w hint_21d0
hint_2774:
; --- unverified ---
    move.w (a5),d1
    tst.w d1
    bne.s hint_2742
hint_277a:
; --- unverified ---
    addq.w #2,a5
    move.b #$6e,(a4)+
    move.b #$6f,(a4)+
    move.b #$70,(a4)+
    rts
hint_278a:
; --- unverified ---
    move.w (a5)+,d7
    cmp.w #$20,d7
    bcc.w hint_367a
hint_2794:
; --- unverified ---
    lea pcref_27bc(pc),a0
    move.w d7,d0
    btst #5,d0
    bne.s hint_27ac
hint_27a0:
    dc.b    $02,$40,$00,$1f,$d0,$40,$d0,$40,$41,$fb,$00,$16
hint_27ac:
; --- unverified ---
    move.b (a0)+,(a4)+
    move.b (a0)+,(a4)+
    beq.s hint_27b8
hint_27b2:
; --- unverified ---
    move.b (a0)+,(a4)+
    beq.s hint_27b8
hint_27b6:
    dc.b    $18,$d8
hint_27b8:
; --- unverified ---
    subq.w #1,a4
    rts
pcref_27bc:
    dc.b    $3f,$3f,$00,$00
pcref_27c0:
    dc.b    $66,$00,$00,$00,$65,$71,$00,$00,$6f,$67,$74,$00,$6f,$67,$65,$00
    dc.b    $6f,$6c,$74,$00,$6f,$6c,$65,$00,$6f,$67,$6c,$00,$6f,$72,$00,$00
    dc.b    $75,$6e,$00,$00,$75,$65,$71,$00,$75,$67,$74,$00,$75,$67,$65,$00
    dc.b    $75,$6c,$74,$00,$75,$6c,$65,$00,$6e,$65,$00,$00,$74,$00,$00,$00
    dc.b    $73,$66,$00,$00,$73,$65,$71,$00,$67,$74,$00,$00,$67,$65,$00,$00
    dc.b    $6c,$74,$00,$00,$6c,$65,$00,$00,$67,$6c,$00,$00,$67,$6c,$65,$00
    dc.b    "nglengl",0
    dc.b    $6e,$6c,$65,$00,$6e,$6c,$74,$00,$6e,$67,$65,$00,$6e,$67,$74,$00
    dc.b    $73,$6e,$65,$00,$73,$74,$00,$00,$41,$fa,$00,$06,$60,$00,$09,$78
    dc.b    $01,$78,$05,$06,$01,$aa,$02,$e4,$03,$e0,$03,$b0
sub_2854:
    dc.b    $04,$a4,$04,$70
hint_2858:
    dc.b    $30,$06
hint_286a:
; --- unverified ---
    move.b (a0)+,(a4)+
    bne.s hint_286a
hint_286e:
; --- unverified ---
    move.b #$2e,-1(a4)
    rts
pcref_2876:
    dc.b    $00,$0a,$00,$0f,$00,$13,$00,$18,$00,$1e,$00,$00,$00,$23,$00,$00
    dc.b    $00,$2a,$00,$31,$00,$36,$00,$00,$00,$3b,$00,$40,$00,$46,$00,$4a
    dc.b    $00,$4e,$00,$53,$00,$5a,$00,$00,$00,$61,$00,$66,$00,$6c,$00,$00
    dc.b    $00,$71,$00,$75,$00,$7a,$00,$00
    dc.b    $00,$7e,$00,$83,$00,$87,$00,$8e,$00,$95,$00,$99,$00,$9d,$00,$a1
    dc.b    $00,$a5,$00,$ac,$00,$b0,$00,$b6,$00,$bd
    dcb.b   15,0
    dc.b    $03,$00,$03,$00,$03,$00,$03,$00,$03,$00,$03,$00,$03,$00,$03,$00
    dc.b    $c1,$00,$00,$00,$c5
    dcb.b   10,0
pcref_28f6:
    dc.b    $3f,$3f,$00
    dc.b    "sincos",0
    dc.b    "move",0
    dc.b    $69,$6e,$74,$00
    dc.b    "sinh",0
    dc.b    "intrz",0
    dc.b    "sqrt",0
    dc.b    "lognp1",0
    dc.b    "etoxm1",0
    dc.b    "tanh",0
    dc.b    "atan",0
    dc.b    "asin",0
    dc.b    "atanh",0
    dc.b    $73,$69,$6e,$00,$74,$61,$6e,$00
    dc.b    "etox",0
    dc.b    "twotox",0
    dc.b    "tentox",0
    dc.b    "logn",0
    dc.b    "log10",0
    dc.b    "log2",0
    dc.b    $61,$62,$73,$00
    dc.b    "cosh",0
    dc.b    $6e,$65,$67,$00
    dc.b    "acos",0
    dc.b    $63,$6f,$73,$00
    dc.b    "getexp",0
    dc.b    "getman",0
    dc.b    $64,$69,$76,$00,$6d,$6f,$64,$00,$61,$64,$64,$00,$6d,$75,$6c,$00
    dc.b    "sgldiv",0
    dc.b    $72,$65,$6d,$00
    dc.b    "scale",0
    dc.b    "sglmul"
sub_29b2:
; --- unverified ---
    ori.w #$7562,99(a3,d0.w)
    blt.s hint_2a2a
hint_29ba:
; --- unverified ---
    ori.w #$7374,0(a4,d0.w)
    bsr.w hint_2858
hint_29c4:
; --- unverified ---
    andi.w #$3f,d7
    beq.s hint_29ce
hint_29ca:
    dc.b    $18,$fc,$00,$3f
hint_29ce:
; --- unverified ---
    move.b #$78,(a4)+
    move.b #$20,(a4)+
    move.w d6,d1
    rol.w #6,d1
    bsr.w hint_2a42
hint_29de:
; --- unverified ---
    btst #5,d6
    bne.s hint_2a1a
hint_29e4:
; --- unverified ---
    move.w d6,d0
    ror.w #7,d0
    sub.b d1,d0
    andi.b #$7,d0
    bne.s hint_2a1a
hint_29f0:
; --- unverified ---
    rts
hint_29f2:
; --- unverified ---
    move.w d6,d1
    rol.w #6,d1
    andi.w #$7,d1
    cmp.b #$7,d1
    beq.w hint_2a8a
hint_2a02:
; --- unverified ---
    bsr.w hint_2858
hint_2a06:
; --- unverified ---
    move.b pcref_2a4e(pc,d1.w),(a4)+
    move.b #$20,(a4)+
    cmp.b #$3c,d7
    beq.s hint_2a56
hint_2a14:
; --- unverified ---
    moveq #-3,d4
    bsr.w hint_2bd2
hint_2a1a:
; --- unverified ---
    move.w d6,d1
    andi.w #$7f,d1
    cmp.b #$3a,d1
    beq.s hint_29f0
hint_2a26:
    dc.b    $18,$fc,$00,$2c
hint_2a2a:
; --- unverified ---
    andi.w #$38,d1
    cmp.b #$30,d1
    bne.s hint_2a3e
hint_2a34:
; --- unverified ---
    move.w d6,d1
    bsr.w hint_2a42
hint_2a3a:
    dc.b    $18,$fc,$00,$3a
hint_2a3e:
    dc.b    $32,$06,$ee,$59
hint_2a42:
; --- unverified ---
    move.b #$66,(a4)+
    move.b #$70,(a4)+
    bra.w sub_1c6c
pcref_2a4e:
    dc.b    $6c,$73
hint_2a50:
    dc.b    $78,$70
    dc.b    $77,$64
sub_2a54:
    dc.b    $62,$3f
hint_2a56:
; --- unverified ---
    move.b #$23,(a4)+
    moveq #0,d2
    move.b pcref_2a7a(pc,d1.w),d2
    beq.s hint_2a72
hint_2a62:
    dc.b    $18,$fc,$00,$24
hint_2a66:
; --- unverified ---
    move.w (a5)+,d1
    bsr.w hint_1bb0
hint_2a6c:
; --- unverified ---
    dbf d2,hint_2a66
hint_2a70:
; --- unverified ---
    bra.s hint_2a1a
hint_2a72:
; --- unverified ---
    move.w (a5)+,d1
    bsr.w hint_1b76
hint_2a78:
; --- unverified ---
    bra.s hint_2a1a
pcref_2a7a:
    dc.b    $01,$01,$05,$05,$00,$03,$00,$00
hint_2a82:
; --- unverified ---
    move.b (a0)+,(a4)+
    bne.s hint_2a82
hint_2a86:
; --- unverified ---
    subq.w #1,a4
    rts
hint_2a8a:
; --- unverified ---
    lea str_2ae2(pc),a0
    bsr.s hint_2a82
hint_2a90:
    dc.b    $32,$06,$02,$41,$00
hint_2a95:
    dc.b    $3f
hint_2a9a:
; --- unverified ---
    move.b #$2c,(a4)+
    bsr.s hint_2a3e
hint_2aa0:
; --- unverified ---
    move.b #$20,(a4)+
    move.b #$3b,(a4)+
    move.w d6,d1
    andi.b #$3f,d1
    cmp.b #$34,d1
    bcc.s hint_2acc
hint_2ab4:
    dc.b    $41,$fa,$00,$38
hint_2ab8:
; --- unverified ---
    move.b (a0)+,d0
    bmi.s hint_2ac8
hint_2abc:
; --- unverified ---
    cmp.b d1,d0
    beq.s hint_2ac6
hint_2ac0:
; --- unverified ---
    tst.b (a0)+
    bne.s hint_2ac0
hint_2ac4:
; --- unverified ---
    bra.s hint_2ab8
hint_2ac6:
; --- unverified ---
    bra.s hint_2a82
hint_2ac8:
; --- unverified ---
    bra.w hint_367a
hint_2acc:
; --- unverified ---
    move.b #$31,(a4)+
    move.b #$65,(a4)+
    move.b d1,d0
    subi.b #$33,d0
    moveq #1,d1
    asl.w d0,d1
    bra.w hint_1b80
str_2ae2:
    dc.b    $6d,$6f
hint_2ae4:
; --- unverified ---
    moveq #101,d3
    bls.s hint_2b5a
hint_2ae8:
    dc.b    ".x #",0
    dc.b    $00,$00,$70,$69,$00,$0b,$6c
hint_2af4:
    dc.b    $6f,$67
hint_2af6:
    dc.b    "10(2)",0
    dc.b    $0c,$65,$00,$0d,$6c,$6f
hint_2b02:
; --- unverified ---
    beq.s hint_2b36
hint_2b04:
    dc.b    $28,$65,$29,$00,$0e
    dc.b    "log10(e)",0
    dc.b    $0f,$30
hint_2b14:
    dc.b    $00,$30,$6c,$6e
hint_2b36:
; --- unverified ---
    ori.w #$18fc,101(a6,d0.w)
    move.b #$2e,(a4)+
    move.w d6,d1
    rol.w #6,d1
    andi.w #$7,d1
    move.b pcref_2b50(pc,d1.w),(a4)+
    bra.w hint_2b58
pcref_2b50:
    dc.b    $6c,$73
hint_2b52:
    dc.b    $78
hint_2b53:
    dc.b    $70
hint_2b56:
; --- unverified ---
    bhi.s hint_2bc8
hint_2b58:
; --- unverified ---
    move.b #$20,(a4)+
    bsr.w hint_2a3e
hint_2b60:
; --- unverified ---
    move.b #$2c,(a4)+
    move.w d6,d1
    rol.w #6,d1
    andi.w #$7,d1
    moveq #61,d4
    bsr.w hint_2bd2
hint_2b72:
; --- unverified ---
    move.w d6,d1
    rol.w #6,d1
    andi.w #$7,d1
    cmp.b #$3,d1
    beq.s hint_2bb0
hint_2b80:
; --- unverified ---
    cmp.b #$7,d1
    bne.s hint_2ba2
hint_2b86:
; --- unverified ---
    move.b #$7b,(a4)+
    move.b #$64,(a4)+
    move.b d6,d1
    ror.b #4,d1
    cmp.b #$10,d1
    bcs.s hint_2b9c
hint_2b98:
    dc.b    $18,$fc,$00,$3f
hint_2b9c:
; --- unverified ---
    bsr.w sub_1c6c
hint_2ba0:
; --- unverified ---
    bra.s hint_2bcc
hint_2ba2:
; --- unverified ---
    move.b d6,d1
    andi.b #$7f,d1
    beq.s hint_2bae
hint_2baa:
    dc.b    $18,$fc,$00,$3f
hint_2bae:
; --- unverified ---
    rts
hint_2bb0:
; --- unverified ---
    move.b #$7b,(a4)+
    move.b d6,d1
    btst #6,d1
    beq.s hint_2bc2
hint_2bbc:
; --- unverified ---
    ori.b #$80,d1
    bra.s hint_2bc6
hint_2bc2:
    dc.b    $02,$01,$00,$7f
hint_2bc6:
    dc.b    $48,$81
hint_2bc8:
; --- unverified ---
    bsr.w hint_1b64
hint_2bcc:
; --- unverified ---
    move.b #$7d,(a4)+
    rts
hint_2bd2:
; --- unverified ---
    moveq #83,d0
    btst d1,d0
    bne.s hint_2be4
hint_2bd8:
; --- unverified ---
    move.b d7,d1
    andi.b #$38,d1
    bne.s hint_2be4
hint_2be0:
    dc.b    $18,$fc,$00,$3f
hint_2be4:
    dc.b    $7a,$01
hint_2be6:
; --- unverified ---
    move.w d6,-(sp)
    bsr.w hint_31d0
hint_2bec:
; --- unverified ---
    move.w (sp)+,d6
    rts
hint_2bf0:
; --- unverified ---
    moveq #125,d4
    bra.s hint_2be6
hint_2bf4:
; --- unverified ---
    moveq #-3,d4
    bra.s hint_2be6
hint_2bf8:
; --- unverified ---
    bsr.w hint_2c8a
hint_2bfc:
; --- unverified ---
    bsr.w hint_2c34
hint_2c00:
; --- unverified ---
    move.b #$2c,(a4)+
    bsr.w hint_2c16
hint_2c08:
    dc.b    $02,$04,$00,$3f
hint_2c0c:
; --- unverified ---
    move.w d3,-(sp)
    bsr.w hint_31d0
hint_2c12:
; --- unverified ---
    move.w (sp)+,d3
    rts
hint_2c16:
; --- unverified ---
    lea pcref_2c20(pc),a0
    move.b 0(a0,d3.w),d4
    rts
pcref_2c20:
    dc.b    $fc,$ff,$fd,$fc,$fd,$fc,$fc,$fc
sub_2c28:
; --- unverified ---
    bsr.w hint_2c8a
hint_2c2c:
; --- unverified ---
    bsr.s hint_2c16
hint_2c2e:
; --- unverified ---
    bsr.s hint_2c0c
hint_2c30:
    dc.b    $18,$fc,$00,$2c
hint_2c34:
; --- unverified ---
    moveq #2,d0
    andi.b #$7,d3
    lea str_2c7a(pc),a0
    beq.w hint_367a
hint_2c42:
; --- unverified ---
    cmp.b #$3,d3
    bcs.s hint_2c68
hint_2c48:
; --- unverified ---
    cmp.b #$4,d3
    beq.s hint_2c68
hint_2c4e:
; --- unverified ---
    btst d0,d3
    beq.s hint_2c5c
hint_2c52:
; --- unverified ---
    bsr.w hint_2a82
hint_2c56:
; --- unverified ---
    move.b #$2f,(a4)+
    bra.s hint_2c60
hint_2c5c:
; --- unverified ---
    tst.b (a0)+
    bne.s hint_2c5c
hint_2c60:
; --- unverified ---
    subq.b #1,d0
    bcc.s hint_2c4e
hint_2c64:
; --- unverified ---
    subq.w #1,a4
    rts
hint_2c68:
; --- unverified ---
    btst d0,d3
    bne.s hint_2c74
hint_2c6c:
; --- unverified ---
    tst.b (a0)+
    bne.s hint_2c6c
hint_2c70:
; --- unverified ---
    subq.b #1,d0
    bra.s hint_2c68
hint_2c74:
; --- unverified ---
    bsr.w hint_2a82
hint_2c78:
; --- unverified ---
    rts
str_2c7a:
; --- unverified ---
    bne.s hint_2cec
hint_2c7c:
; --- unverified ---
    bls.s hint_2cf0
hint_2c7e:
; --- unverified ---
    ori.w #$7073,-(a6)
    moveq #0,d1
    bne.s $2cf6
hint_2c86:
    dc.b    $69,$61
hint_2c88:
    dc.b    $72,$00
hint_2c8a:
; --- unverified ---
    move.b #$6d,(a4)+
    move.b #$6f,(a4)+
    move.b #$76,(a4)+
    move.b #$65,(a4)+
    move.l d6,d3
    rol.w #6,d3
    andi.b #$7,d3
    cmp.b #$3,d3
    bcs.s hint_2cb2
hint_2ca8:
; --- unverified ---
    cmp.b #$4,d3
    beq.s hint_2cb2
hint_2cae:
    dc.b    $18,$fc,$00,$6d
hint_2cb2:
; --- unverified ---
    moveq #2,d5
    bra.w hint_1c26
hint_2cb8:
; --- unverified ---
    bsr.w hint_2d30
hint_2cbc:
; --- unverified ---
    move.b d6,d3
    btst #12,d6
    bne.s hint_2cd6
hint_2cc4:
; --- unverified ---
    btst #11,d6
    bne.s hint_2cd6
hint_2cca:
    dc.b    $12,$06,$70,$07
hint_2cce:
; --- unverified ---
    roxl.b #1,d1
    roxr.b #1,d3
    dbf d0,hint_2cce
hint_2cd6:
; --- unverified ---
    bsr.s hint_2d08
hint_2cd8:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #1,d5
    moveq #52,d4
    btst #12,d6
    bne.s hint_2ce8
hint_2ce6:
    dc.b    $78,$10
hint_2ce8:
; --- unverified ---
    bra.w hint_31d0
hint_2cec:
; --- unverified ---
    bsr.w hint_2d30
hint_2cf0:
; --- unverified ---
    moveq #1,d5
    moveq #108,d4
    bsr.w hint_2be6
hint_2cf8:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b d6,d3
    btst #12,d6
    bne.s hint_2d08
hint_2d04:
    dc.b    $18,$fc,$00,$3f
hint_2d08:
; --- unverified ---
    btst #11,d6
    bne.s hint_2d1a
hint_2d0e:
; --- unverified ---
    moveq #102,d4
    move.w d6,-(sp)
    bsr.w hint_1fa6
hint_2d16:
; --- unverified ---
    move.w (sp)+,d6
    rts
hint_2d1a:
; --- unverified ---
    move.b #$64,(a4)+
    move.b d6,d1
    ror.b #4,d1
    cmp.b #$8,d1
    bcs.s hint_2d2c
hint_2d28:
    dc.b    $18,$fc,$00,$3f
hint_2d2c:
; --- unverified ---
    bra.w sub_1c6c
hint_2d30:
; --- unverified ---
    moveq #120,d0
hint_2d32:
    lea str_2d46(pc),a0
    bsr.w hint_2a82
hint_2d3a:
; --- unverified ---
    move.b d0,(a4)+
    move.b #$20,(a4)+
    rts
hint_2d42:
; --- unverified ---
    moveq #108,d0
    bra.s hint_2d32
str_2d46:
    dc.b    $6d,$6f
hint_2d48:
; --- unverified ---
    moveq #101,d3
    blt.s hint_2d7a
hint_2d4c:
    dc.b    $00,$00,$60,$00,$09,$2a,$00,$00,$06,$53,$46,$43,$00,$00,$00,$01
    dc.b    $06,$44,$46,$43,$00,$00,$00,$02,$06
    dc.b    "CACR",0
    dc.b    $08,$00,$06,$55,$53,$50,$00,$00,$08,$01,$06,$56,$42,$52,$00,$00
hint_2d7a:
    dc.b    $08,$02
    dc.b    $41,$41,$52,$00,$08,$03,$06,$4d,$53,$50,$00,$00,$08,$04,$06,$49
    dc.b    $53,$50,$00,$00,$08,$04,$00,$00,$41,$fa,$00,$06,$60,$00,$04,$22
    dc.b    $00,$b8,$01,$32,$00,$42,$00,$10,$02,$16,$08,$dc,$08,$dc,$08,$dc
    dc.b    $61,$00,$01,$00,$7a,$01,$61,$00,$ee
sub_2db7:
    dc.b    $70
hint_2db8:
    dc.b    $bc
hint_2dbe:
; --- unverified ---
    bsr.w hint_2eaa
hint_2dc2:
    dc.b    $18,$fc,$00,$2c
hint_2dc6:
; --- unverified ---
    lea str_2dce(pc),a0
    bra.w hint_2a82
str_2dce:
    dc.b    $70,$73,$72,$00
hint_2dd2:
; --- unverified ---
    cmp.w #$6200,d6
    bne.w hint_367a
hint_2dda:
; --- unverified ---
    bsr.s hint_2dc6
hint_2ddc:
; --- unverified ---
    bra.w hint_2ea6
hint_2de0:
; --- unverified ---
    bsr.w hint_2eb0
hint_2de4:
; --- unverified ---
    moveq #2,d5
    btst #11,d6
    beq.s hint_2dee
hint_2dec:
    dc.b    $7a,$04
hint_2dee:
; --- unverified ---
    bsr.w hint_1c26
hint_2df2:
; --- unverified ---
    move.w d6,d1
    andi.w #$f0ff,d1
    cmp.w #$4000,d1
    beq.s hint_2e02
hint_2dfe:
    dc.b    $18,$fc,$00,$3f
hint_2e02:
; --- unverified ---
    move.w d6,d1
    andi.w #$300,d1
    cmp.w #$300,d1
    bne.s hint_2e12
hint_2e0e:
    dc.b    $18,$fc,$00,$3f
hint_2e12:
; --- unverified ---
    btst #9,d6
    bne.s hint_2e52
hint_2e18:
; --- unverified ---
    bsr.w hint_2eaa
hint_2e1c:
    dc.b    $18,$fc,$00,$2c
hint_2e20:
; --- unverified ---
    btst #11,d6
    beq.s hint_2e40
hint_2e26:
; --- unverified ---
    btst #10,d6
    bne.s hint_2e32
hint_2e2c:
; --- unverified ---
    move.b #$73,(a4)+
    bra.s hint_2e36
hint_2e32:
    dc.b    $18,$fc,$00,$63
hint_2e36:
; --- unverified ---
    move.b #$72,(a4)+
    move.b #$70,(a4)+
    rts
hint_2e40:
; --- unverified ---
    btst #10,d6
    bne.w hint_367a
hint_2e48:
; --- unverified ---
    move.b #$74,(a4)+
    move.b #$63,(a4)+
    rts
hint_2e52:
; --- unverified ---
    bsr.s hint_2e20
hint_2e54:
; --- unverified ---
    bra.s hint_2ea6
hint_2e56:
; --- unverified ---
    bsr.s hint_2eb0
hint_2e58:
; --- unverified ---
    moveq #2,d5
    bsr.w hint_1c26
hint_2e5e:
; --- unverified ---
    move.w d6,d1
    andi.w #$f8ff,d1
    cmp.w #$800,d1
    beq.s hint_2e6e
hint_2e6a:
    dc.b    $18,$fc,$00,$3f
hint_2e6e:
; --- unverified ---
    move.w d6,d1
    andi.w #$300,d1
    cmp.w #$300,d1
    bne.s hint_2e7e
hint_2e7a:
    dc.b    $18,$fc,$00,$3f
hint_2e7e:
; --- unverified ---
    btst #9,d6
    bne.s hint_2ea4
hint_2e84:
; --- unverified ---
    bsr.s hint_2eaa
hint_2e86:
    dc.b    $18,$fc,$00,$2c
hint_2e8a:
; --- unverified ---
    move.b #$74,(a4)+
    move.b #$74,(a4)+
    btst #10,d6
    beq.s hint_2e9e
hint_2e98:
; --- unverified ---
    move.b #$31,(a4)+
    rts
hint_2e9e:
; --- unverified ---
    move.b #$30,(a4)+
    rts
hint_2ea4:
; --- unverified ---
    bsr.s hint_2e8a
hint_2ea6:
    dc.b    $18,$fc,$00,$2c
hint_2eaa:
; --- unverified ---
    moveq #36,d4
    bra.w hint_2be6
hint_2eb0:
; --- unverified ---
    move.b #$6d,(a4)+
    move.b #$6f,(a4)+
    move.b #$76,(a4)+
    move.b #$65,(a4)+
    btst #8,d6
    beq.s hint_2ece
hint_2ec6:
    dc.b    $18,$fc,$00,$66,$18,$fc,$00,$64
hint_2ece:
; --- unverified ---
    rts
hint_2ed0:
; --- unverified ---
    move.w d6,d1
    rol.w #6,d1
    andi.b #$7,d1
    beq.s hint_2f30
hint_2eda:
; --- unverified ---
    lea str_2f1c(pc),a0
    bsr.w hint_2a82
hint_2ee2:
; --- unverified ---
    cmp.b #$1,d1
    beq.s hint_2f22
hint_2ee8:
; --- unverified ---
    cmp.b #$4,d1
    beq.s hint_2ef6
hint_2eee:
; --- unverified ---
    cmp.b #$6,d1
    bne.w hint_367a
hint_2ef6:
; --- unverified ---
    move.b #$20,(a4)+
    bsr.s hint_2f66
hint_2efc:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$23,(a4)+
    move.w d6,d1
    andi.w #$7,d1
    bsr.w hint_1b80
hint_2f0e:
; --- unverified ---
    btst #11,d6
    beq.w hint_2f2e
hint_2f16:
; --- unverified ---
    move.b #$2c,(a4)+
    bra.s hint_2eaa
str_2f1c:
; --- unverified ---
    bne.s hint_2f8a
    dc.b    $75,$73
sub_2f20:
; --- unverified ---
    bvc.w $481e
hint_2f24:
; --- unverified ---
    ori.w #$bc7c,-(a1)
    move.l d0,d2
    bne.w hint_367a
hint_2f2e:
; --- unverified ---
    rts
hint_2f30:
; --- unverified ---
    lea str_2f60(pc),a0
    bsr.w hint_2a82
hint_2f38:
; --- unverified ---
    btst #9,d6
    bne.s hint_2f44
hint_2f3e:
; --- unverified ---
    move.b #$77,(a4)+
    bra.s hint_2f48
hint_2f44:
    dc.b    $18,$fc,$00,$72
hint_2f48:
; --- unverified ---
    move.b #$20,(a4)+
    bsr.s hint_2f66
hint_2f4e:
; --- unverified ---
    move.w d6,d1
    andi.w #$fde0,d1
    cmp.w #$2000,d1
    bne.w hint_367a
hint_2f5c:
; --- unverified ---
    bra.w hint_2ea6
str_2f60:
    dc.b    $6c,$6f
hint_2f62:
; --- unverified ---
    bsr.s hint_2fc8
hint_2f64:
    dc.b    $00,$00
hint_2f66:
    dc.b    $12,$06
hint_2f6e:
; --- unverified ---
    cmp.b #$8,d1
    beq.s hint_2f8c
hint_2f74:
; --- unverified ---
    cmp.b #$10,d1
    beq.s hint_2f7e
hint_2f7a:
; --- unverified ---
    bra.w hint_367a
hint_2f7e:
; --- unverified ---
    move.b #$23,(a4)+
    move.w d6,d1
    andi.w #$7,d1
    bra.w hint_1b80
hint_2f8c:
; --- unverified ---
    move.b d6,d1
    bra.w hint_3206
hint_2f92:
; --- unverified ---
    move.b d6,d1
    andi.w #$7,d1
    subq.b #1,d1
    bmi.s hint_2fa6
hint_2f9c:
; --- unverified ---
    bne.w hint_367a
hint_2fa0:
; --- unverified ---
    move.b #$64,(a4)+
    bra.s hint_2faa
hint_2fa6:
    dc.b    $18,$fc,$00,$73
hint_2faa:
; --- unverified ---
    move.b #$66,(a4)+
    move.b #$63,(a4)+
    rts
hint_2fb4:
; --- unverified ---
    lea str_2ff6(pc),a0
    bsr.w hint_2a82
hint_2fbc:
; --- unverified ---
    btst #9,d6
    bne.s hint_2fc8
hint_2fc2:
; --- unverified ---
    move.b #$77,(a4)+
    bra.s hint_2fcc
hint_2fc8:
    dc.b    $18,$fc,$00,$72
hint_2fcc:
; --- unverified ---
    move.b #$20,(a4)+
    bsr.s hint_2f66
hint_2fd2:
; --- unverified ---
    bsr.w hint_2ea6
hint_2fd6:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$23,(a4)+
    move.w d6,d1
    rol.w #6,d1
    bsr.w sub_1c6c
hint_2fe6:
; --- unverified ---
    btst #8,d6
    bne.s hint_2ffc
hint_2fec:
; --- unverified ---
    cmp.b #$20,d6
    bcc.w hint_367a
hint_2ff4:
; --- unverified ---
    rts
str_2ff6:
    dc.b    $74,$65
    dc.b    $73,$74
sub_2ffa:
    dc.b    $00,$00
hint_2ffc:
    dc.b    $32,$06
hint_3006:
; --- unverified ---
    move.b d6,d1
    rol.b #3,d1
    move.b #$2c,(a4)+
    move.b #$61,(a4)+
    bra.w sub_1c6c
hint_3016:
; --- unverified ---
    move.w d7,d5
    rol.w #7,d5
    andi.b #$3,d5
    subq.b #1,d5
    bra.w hint_1c26
hint_3024:
; --- unverified ---
    lsr.w #6,d1
    bra.w hint_3206
hint_302a:
; --- unverified ---
    move.w d7,d1
    move.w (a5)+,d6
    andi.w #$3f,d1
    cmp.w #$3c,d1
    beq.s hint_3050
hint_3038:
; --- unverified ---
    bsr.s hint_3016
hint_303a:
; --- unverified ---
    bsr.w hint_3204
hint_303e:
; --- unverified ---
    move.b #$2c,(a4)+
    move.w d6,d1
    bsr.s hint_3024
hint_3046:
; --- unverified ---
    move.b #$2c,(a4)+
    moveq #60,d4
    bra.w hint_31d0
hint_3050:
; --- unverified ---
    move.b #$32,(a4)+
    cmp.w #$afc,d7
    beq.w hint_367a
hint_305c:
; --- unverified ---
    bsr.s hint_3016
hint_305e:
; --- unverified ---
    bsr.w hint_3204
hint_3062:
; --- unverified ---
    move.b #$3a,(a4)+
    move.w (a5),d1
    bsr.w hint_3206
hint_306c:
; --- unverified ---
    move.b #$2c,(a4)+
    move.w d6,d1
    bsr.s hint_3024
hint_3074:
; --- unverified ---
    move.b #$3a,(a4)+
    move.w (a5),d1
    bsr.s hint_3024
hint_307c:
; --- unverified ---
    move.b #$2c,(a4)+
    move.w d6,d1
    bsr.s hint_308a
hint_3084:
    dc.b    $18,$fc,$00,$3a,$32,$1d
hint_308a:
; --- unverified ---
    move.b #$28,(a4)+
    bsr.s hint_30d6
hint_3090:
; --- unverified ---
    move.b #$29,(a4)+
    rts
hint_3096:
; --- unverified ---
    move.w (a5)+,d6
    btst #11,d6
    bne.s hint_30a8
hint_309e:
; --- unverified ---
    move.b #$6d,(a4)+
    move.b #$70,(a4)+
    bra.s hint_30b0
hint_30a8:
    dc.b    $18,$fc,$00,$68,$18,$fc,$00,$6b
hint_30b0:
; --- unverified ---
    move.b #$32,(a4)+
    move.w d7,d5
    rol.w #7,d5
    andi.b #$3,d5
    bsr.w hint_1c26
hint_30c0:
; --- unverified ---
    move.w d6,d1
    andi.w #$3ff,d1
    bne.w hint_367a
hint_30ca:
; --- unverified ---
    moveq #100,d4
    bsr.w hint_2be6
hint_30d0:
    dc.b    $18,$fc,$00,$2c,$32,$06
hint_30d6:
; --- unverified ---
    tst.w d1
    bmi.s hint_30e0
hint_30da:
; --- unverified ---
    move.b #$64,(a4)+
    bra.s hint_30e4
hint_30e0:
    dc.b    $18,$fc,$00,$61
hint_30e4:
; --- unverified ---
    rol.w #4,d1
    bra.w sub_1c6c
hint_30ea:
; --- unverified ---
    bsr.w hint_1c26
hint_30ee:
; --- unverified ---
    bsr.w hint_3776
hint_30f2:
; --- unverified ---
    move.b #$2c,(a4)+
    bra.w hint_2bf0
hint_30fa:
; --- unverified ---
    bsr.w hint_1c26
hint_30fe:
; --- unverified ---
    moveq #-1,d4
    bra.w hint_31d0
hint_3104:
; --- unverified ---
    move.w (a5)+,d6
    btst #11,d6
    beq.s hint_3112
hint_310c:
; --- unverified ---
    move.b #$73,(a4)+
    rts
hint_3112:
; --- unverified ---
    move.b #$75,(a4)+
    rts
hint_3118:
; --- unverified ---
    moveq #2,d5
    bsr.w hint_1c26
hint_311e:
; --- unverified ---
    bsr.w hint_2bf4
hint_3122:
; --- unverified ---
    move.b #$2c,(a4)+
    rts
hint_3128:
; --- unverified ---
    bsr.s hint_3104
hint_312a:
; --- unverified ---
    bsr.s hint_3118
hint_312c:
; --- unverified ---
    btst #10,d6
    beq.s hint_313a
hint_3132:
; --- unverified ---
    bsr.w hint_3204
hint_3136:
    dc.b    $18,$fc,$00,$3a
hint_313a:
; --- unverified ---
    move.w d6,d1
    bra.s hint_30d6
hint_313e:
; --- unverified ---
    bsr.s hint_3104
hint_3140:
; --- unverified ---
    btst #10,d6
    bne.s hint_314a
hint_3146:
    dc.b    $18,$fc,$00,$6c
hint_314a:
; --- unverified ---
    bsr.s hint_3118
hint_314c:
; --- unverified ---
    bra.s hint_3132
hint_314e:
; --- unverified ---
    bsr.w hint_1eca
hint_3152:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$23,(a4)+
    move.l (a5)+,d1
    bra.w hint_1b58
hint_3160:
; --- unverified ---
    bsr.w hint_2212
hint_3164:
; --- unverified ---
    move.b #$2c,(a4)+
    move.b #$23,(a4)+
    move.w (a5)+,d1
    bra.w hint_1b80
hint_3172:
; --- unverified ---
    move.w d7,d1
    lsr.w #8,d1
    andi.b #$f,d1
    bsr.w hint_1bec
hint_317e:
    dc.b    $53,$4c,$32,$07,$02,$01,$00,$07
hint_3186:
; --- unverified ---
    cmp.b #$4,d1
    beq.s hint_31bc
hint_318c:
; --- unverified ---
    move.b #$2e,(a4)+
    cmp.b #$2,d1
    beq.s hint_31a8
hint_3196:
; --- unverified ---
    cmp.b #$3,d1
    bne.w hint_367a
hint_319e:
; --- unverified ---
    move.b #$6c,(a4)+
    move.l (a5)+,d1
    bra.w hint_31b0
hint_31a8:
    dc.b    $18,$fc,$00,$77,$32,$1d,$48,$c1
hint_31b0:
; --- unverified ---
    move.b #$20,(a4)+
    move.b #$23,(a4)+
    bra.w hint_1b88
hint_31bc:
; --- unverified ---
    rts
hint_31be:
; --- unverified ---
    move.w (a5)+,d6
    move.w d6,d1
    rol.w #3,d1
    andi.w #$7,d1
    move.b d1,d0
    bra.w sub_1cba
hint_31ce:
; --- unverified ---
    rts
hint_31d0:
    dc.b    $2d,$4d,$05,$94,$32,$07,$02,$41,$00,$07,$34,$07,$e6,$4a,$02,$02
    dc.b    $00,$07
hint_31e2:
; --- unverified ---
    move.b d2,d0
    move.w d1,d6
    lea pcref_31ee(pc),a0
    bra.w sub_1cba
pcref_31ee:
; --- unverified ---
    ori.b #$20,(a0)
    ori.b #$76,-124(a4,d0.w)
    ori.l #$1920472,1284(a4)
    beq.w hint_367a
hint_3204:
    dc.b    $12,$06
hint_3206:
; --- unverified ---
    move.b #$64,(a4)+
    bra.w sub_1c6c
hint_320e:
; --- unverified ---
    btst d2,d4
    beq.w hint_367a
hint_3214:
; --- unverified ---
    tst.b d5
    beq.w hint_367a
hint_321a:
; --- unverified ---
    move.b #$61,(a4)+
    bra.w sub_1c6c
hint_3222:
; --- unverified ---
    btst d2,d4
    beq.w hint_367a
hint_3228:
; --- unverified ---
    bset #0,331(a6) ; app+$14B
    bne.s hint_3258
hint_3230:
; --- unverified ---
    bsr.s hint_323c
hint_3232:
; --- unverified ---
    move.l d0,334(a6) ; app+$14E
    move.b d5,333(a6) ; app+$14D
    bra.s hint_3258
hint_323c:
; --- unverified ---
    move.w d6,d0
    add.w d0,d0
    add.w d0,d0
    cmp.w #$1c,d0
    bne.s hint_3252
hint_3248:
; --- unverified ---
    btst #5,90(a6) ; app+$5A
    beq.s hint_3252
hint_3250:
    dc.b    $70,$20
hint_3252:
; --- unverified ---
    move.l 48(a6,d0.w),d0
    rts
hint_3258:
; --- unverified ---
    move.b #$28,(a4)+
    bsr.s hint_321a
hint_325e:
; --- unverified ---
    move.b #$29,(a4)+
    rts
hint_3264:
; --- unverified ---
    btst d2,d4
    beq.w hint_367a
hint_326a:
; --- unverified ---
    bsr.s hint_3228
hint_326c:
; --- unverified ---
    move.b #$2b,(a4)+
    rts
hint_3272:
; --- unverified ---
    btst d2,d4
    beq.w hint_367a
hint_3278:
; --- unverified ---
    move.b #$2d,(a4)+
    btst #0,331(a6) ; app+$14B
    bne.s hint_3258
hint_3284:
; --- unverified ---
    bsr.s hint_3228
hint_3286:
; --- unverified ---
    andi.w #$3,d5
    moveq #0,d0
    move.b pcref_3296(pc,d5.w),d0
    sub.l d0,334(a6) ; app+$14E
    rts
pcref_3296:
; --- unverified ---
    btst d0,d2
    subi.b #$4,d0
    beq.w hint_367a
hint_32a0:
; --- unverified ---
    move.w (a5)+,d1
    ext.l d1
    bset #0,331(a6) ; app+$14B
    bne.s hint_32b8
hint_32ac:
; --- unverified ---
    bsr.s hint_323c
hint_32ae:
    dc.b    $d0,$81,$2d,$40,$01,$4e,$1d,$45,$01,$4d
hint_32b8:
; --- unverified ---
    tst.l 174(a6) ; app+$AE
    beq.s hint_3308
hint_32be:
; --- unverified ---
    btst d6,1424(a6) ; app+$590
    beq.s hint_32de
hint_32c4:
; --- unverified ---
    move.w d1,d0
    ext.l d0
    move.l d2,-(sp)
    move.b d6,d2
    addq.b #1,d2
    bsr.w hint_7c28
hint_32d2:
; --- unverified ---
    movem.l (sp)+,d2
    beq.s hint_32de
hint_32d8:
; --- unverified ---
    bsr.w hint_7bf0
hint_32dc:
; --- unverified ---
    bra.s hint_330c
hint_32de:
; --- unverified ---
    tst.b 328(a6) ; app+$148
    beq.s hint_3308
hint_32e4:
; --- unverified ---
    cmp.b #$7,d6
    beq.s hint_3308
hint_32ea:
; --- unverified ---
    move.w d1,d0
    ext.l d0
    move.l d2,-(sp)
    moveq #0,d2
    move.b d6,d2
    lsl.w #2,d2
    add.l 48(a6,d2.w),d0
    move.l (sp)+,d2
    bsr.w hint_7ef8
hint_3300:
; --- unverified ---
    beq.s hint_3308
hint_3302:
; --- unverified ---
    bsr.w hint_7bf0
hint_3306:
; --- unverified ---
    bra.s hint_330c
hint_3308:
; --- unverified ---
    bsr.w hint_1b76
hint_330c:
; --- unverified ---
    move.b d6,d1
    bra.w hint_3258
hint_3312:
; --- unverified ---
    move.b d4,d0
    ext.w d0
    adda.w d0,a0
    move.w d4,d0
    rol.w #6,d0
    andi.w #$3c,d0
    cmp.w #$3c,d0
    bne.s hint_3330
hint_3326:
; --- unverified ---
    btst #5,90(a6) ; app+$5A
    beq.s hint_3330
hint_332e:
    dc.b    $70,$40
hint_3330:
; --- unverified ---
    move.l 16(a6,d0.w),d0
    btst #11,d4
    bne.s hint_333c
hint_333a:
    dc.b    $48,$c0
hint_333c:
; --- unverified ---
    adda.l d0,a0
    move.l a0,334(a6) ; app+$14E
    move.b d5,333(a6) ; app+$14D
    rts
hint_3348:
; --- unverified ---
    st d3
    move.w (a5)+,d4
    btst #8,d4
    bne.w hint_3416
hint_3354:
; --- unverified ---
    move.b d4,d1
    ext.w d1
    ext.l d1
    add.l 1428(a6),d1 ; app+$594
    add.l 4(a6),d1 ; app+$4
    bsr.w hint_1b88
hint_3366:
; --- unverified ---
    move.b #$28,(a4)+
    move.b #$70,(a4)+
    move.b #$63,(a4)+
    move.b #$2c,(a4)+
    bsr.w hint_33be
hint_337a:
; --- unverified ---
    move.b #$29,(a4)+
    rts
hint_3380:
; --- unverified ---
    btst #5,d4
    beq.w hint_367a
hint_3388:
; --- unverified ---
    move.w (a5)+,d4
    sf d3
    btst #8,d4
    bne.w hint_3416
hint_3394:
; --- unverified ---
    move.w #$600,d0
    and.w d4,d0
    beq.w hint_3608
hint_339e:
; --- unverified ---
    move.b d4,d1
    bsr.w hint_1b64
hint_33a4:
; --- unverified ---
    move.b #$28,(a4)+
    move.b #$61,(a4)+
    moveq #48,d1
    add.b d6,d1
    move.b d1,(a4)+
    move.b #$2c,(a4)+
    bsr.s hint_33be
hint_33b8:
; --- unverified ---
    move.b #$29,(a4)+
    rts
hint_33be:
; --- unverified ---
    move.w d4,d0
    rol.w #5,d0
    andi.w #$1e,d0
    move.b str_33f2(pc,d0.w),(a4)+
    move.b 39(pc,d0.w),(a4)+
    move.b #$2e,(a4)+
    moveq #119,d0
    btst #11,d4
    beq.s hint_33dc
hint_33da:
    dc.b    $70,$6c
hint_33dc:
; --- unverified ---
    move.b d0,(a4)+
    move.w #$600,d0
    and.w d4,d0
    beq.s hint_33f0
hint_33e6:
    dc.b    $18,$fc,$00,$2a,$ef,$58,$18,$fb,$00,$23
hint_33f0:
; --- unverified ---
    rts
str_33f2:
; --- unverified ---
    bcc.s hint_3424
hint_33f4:
    dc.b    $64,$31
hint_33f6:
; --- unverified ---
    bcc.s hint_342a
hint_33f8:
    dc.b    $64,$33
hint_33fa:
; --- unverified ---
    bcc.s hint_3430
hint_33fc:
    dc.b    $64,$35
hint_33fe:
; --- unverified ---
    bcc.s hint_3436
hint_3400:
    dc.b    $64,$37
hint_3402:
; --- unverified ---
    bsr.s hint_3434
hint_3404:
    dc.b    $61,$31
hint_3406:
; --- unverified ---
    bsr.s hint_343a
hint_3408:
    dc.b    $61,$33
hint_340a:
; --- unverified ---
    bsr.s hint_3440
hint_340c:
    dc.b    $61,$35
hint_340e:
; --- unverified ---
    bsr.s hint_3446
hint_3410:
    dc.b    $61,$37
hint_3412:
    dc.b    $32,$34,$38,$00
hint_3416:
; --- unverified ---
    move.b #$28,(a4)+
    moveq #7,d0
    and.w d4,d0
    btst #6,d4
    beq.s hint_3428
hint_3424:
    dc.b    $08,$c0,$00
hint_3427:
    dc.b    $03
hint_3428:
    dc.b    $41,$fa
hint_342a:
    dc.b    $00,$0c
hint_342d:
    dc.b    $00,$e8,$8c
hint_3430:
    dc.b    $18,$fc,$00
hint_3433:
    dc.b    $29
hint_3434:
    dc.b    $4e,$75
hint_3436:
    dc.b    $00
hint_3437:
    dc.b    $20,$00
hint_3439:
    dc.b    $30
hint_343a:
    dc.b    $00
hint_343d:
    dc.b    $4a,$00,$e8
hint_3440:
    dc.b    $00
hint_3443:
    dc.b    $8a,$00
hint_3445:
    dc.b    $8a
hint_3446:
    dc.b    $00
hint_3449:
    dc.b    $b6,$00,$cc,$00,$cc,$00,$e8,$00,$e8,$00,$e8,$00,$e8,$61,$00,$00
    dc.b    $cc,$61,$00,$01,$2c
hint_345e:
    dc.b    $61
hint_3462:
; --- unverified ---
    bra.w hint_35fe
hint_3466:
; --- unverified ---
    move.b #$5b,(a4)+
    bsr.w hint_3524
hint_346e:
; --- unverified ---
    bsr.w hint_3588
hint_3472:
; --- unverified ---
    bsr.w hint_35c0
hint_3476:
; --- unverified ---
    bsr.w hint_35fe
hint_347a:
; --- unverified ---
    move.b #$5d,(a4)+
    rts
hint_3480:
; --- unverified ---
    move.b #$5b,(a4)+
    bsr.w hint_3524
hint_3488:
; --- unverified ---
    bsr.w hint_3588
hint_348c:
; --- unverified ---
    bsr.w hint_35c0
hint_3490:
; --- unverified ---
    bsr.w hint_35fe
hint_3494:
; --- unverified ---
    move.b #$5d,(a4)+
    move.b #$2c,(a4)+
    bra.w hint_35e2
hint_34a0:
; --- unverified ---
    move.b #$5b,(a4)+
    bsr.w hint_3524
hint_34a8:
; --- unverified ---
    bsr.w hint_3588
hint_34ac:
; --- unverified ---
    bsr.w hint_35fe
hint_34b0:
; --- unverified ---
    move.b #$5d,(a4)+
    move.b #$2c,(a4)+
    bsr.w hint_35c0
hint_34bc:
; --- unverified ---
    bra.w hint_35fe
hint_34c0:
; --- unverified ---
    move.b #$5b,(a4)+
    bsr.w hint_3524
hint_34c8:
; --- unverified ---
    bsr.w hint_3588
hint_34cc:
; --- unverified ---
    bsr.w hint_35fe
hint_34d0:
; --- unverified ---
    move.b #$5d,(a4)+
    move.b #$2c,(a4)+
    bsr.w hint_35c0
hint_34dc:
; --- unverified ---
    bra.w hint_35e2
hint_34e0:
; --- unverified ---
    bsr.w hint_3524
hint_34e4:
; --- unverified ---
    bsr.w hint_3588
hint_34e8:
; --- unverified ---
    bra.w hint_35fe
hint_34ec:
; --- unverified ---
    move.b #$5b,(a4)+
    bsr.w hint_3524
hint_34f4:
; --- unverified ---
    bsr.w hint_3588
hint_34f8:
; --- unverified ---
    bsr.w hint_35fe
hint_34fc:
; --- unverified ---
    move.b #$5d,(a4)+
    rts
hint_3502:
; --- unverified ---
    move.b #$5b,(a4)+
    bsr.w hint_3524
hint_350a:
; --- unverified ---
    bsr.w hint_3588
hint_350e:
; --- unverified ---
    bsr.w hint_35fe
hint_3512:
; --- unverified ---
    move.b #$5d,(a4)+
    move.b #$2c,(a4)+
    bra.w hint_35e2
hint_351e:
; --- unverified ---
    move.b #$3f,(a4)+
    rts
hint_3524:
; --- unverified ---
    moveq #48,d0
    and.w d4,d0
    beq.s hint_3554
hint_352a:
; --- unverified ---
    lsr.w #4,d0
    subq.b #1,d0
    beq.s hint_3586
hint_3530:
; --- unverified ---
    subq.w #1,d0
    bne.s hint_355a
hint_3534:
; --- unverified ---
    move.w (a5)+,d1
    tst.b d3
    bne.s hint_3540
hint_353a:
; --- unverified ---
    bsr.w hint_1b76
hint_353e:
; --- unverified ---
    bra.s hint_3578
hint_3540:
; --- unverified ---
    ext.l d1
    add.l 4(a6),d1 ; app+$4
    tst.b d4
    bmi.s hint_354e
hint_354a:
    dc.b    $d2,$ae,$05,$94
hint_354e:
; --- unverified ---
    bsr.w hint_1b88
hint_3552:
; --- unverified ---
    bra.s hint_3578
hint_3554:
; --- unverified ---
    move.b #$3f,(a4)+
    bra.s hint_3578
hint_355a:
; --- unverified ---
    move.l (a5)+,d1
    tst.b d3
    beq.s hint_356c
hint_3560:
; --- unverified ---
    add.l 4(a6),d1 ; app+$4
    tst.b d4
    bmi.s hint_356c
hint_3568:
    dc.b    $d2,$ae,$05,$94
hint_356c:
; --- unverified ---
    bsr.w hint_1b88
hint_3570:
    dc.b    $18,$fc,$00,$2e,$18,$fc,$00,$6c
hint_3578:
; --- unverified ---
    tst.b 1426(a6) ; app+$592
    beq.s hint_3582
hint_357e:
    dc.b    $18,$fc,$00,$7d
hint_3582:
    dc.b    $18,$fc,$00,$2c
hint_3586:
; --- unverified ---
    rts
hint_3588:
; --- unverified ---
    tst.b d4
    bpl.s hint_35ae
hint_358c:
; --- unverified ---
    move.b #$7a,(a4)+
    tst.b d3
    bne.s hint_35b2
hint_3594:
; --- unverified ---
    tst.b 1415(a6) ; app+$587
    beq.s hint_35aa
hint_359a:
; --- unverified ---
    move.b #$61,(a4)+
    moveq #48,d0
    add.b d6,d0
    move.b d0,(a4)+
    move.b #$2c,(a4)+
    rts
hint_35aa:
; --- unverified ---
    subq.w #1,a4
    rts
hint_35ae:
; --- unverified ---
    tst.b d3
    beq.s hint_359a
hint_35b2:
; --- unverified ---
    move.b #$70,(a4)+
    move.b #$63,(a4)+
    move.b #$2c,(a4)+
    rts
hint_35c0:
; --- unverified ---
    btst #6,d4
    beq.s hint_35d8
hint_35c6:
; --- unverified ---
    move.b #$7a,(a4)+
    move.b #$64,(a4)+
    move.b #$3f,(a4)+
    move.b #$2c,(a4)+
    rts
hint_35d8:
; --- unverified ---
    bsr.w hint_33be
hint_35dc:
; --- unverified ---
    move.b #$2c,(a4)+
    rts
hint_35e2:
; --- unverified ---
    btst #0,d4
    beq.s hint_35f8
hint_35e8:
; --- unverified ---
    move.l (a5)+,d1
    bsr.w hint_1b88
hint_35ee:
; --- unverified ---
    move.b #$2e,(a4)+
    move.b #$6c,(a4)+
    rts
hint_35f8:
; --- unverified ---
    move.w (a5)+,d1
    bra.w hint_1b76
hint_35fe:
; --- unverified ---
    cmpi.b #$2c,-(a4)
    beq.s hint_3606
hint_3604:
    dc.b    $52,$8c
hint_3606:
; --- unverified ---
    rts
hint_3608:
; --- unverified ---
    bset #0,331(a6) ; app+$14B
    bne.s hint_361a
hint_3610:
; --- unverified ---
    bsr.w hint_323c
hint_3614:
; --- unverified ---
    movea.l d0,a0
    bsr.w hint_3312
hint_361a:
; --- unverified ---
    move.b d4,d1
    bsr.w hint_1b64
hint_3620:
; --- unverified ---
    move.b #$28,(a4)+
    move.b #$61,(a4)+
    move.b d6,d1
    bsr.w sub_1c6c
hint_362e:
; --- unverified ---
    move.b #$2c,(a4)+
    tst.w d4
    bmi.s hint_363c
hint_3636:
; --- unverified ---
    move.b #$64,(a4)+
    bra.s hint_3640
hint_363c:
    dc.b    $18,$fc,$00,$61
hint_3640:
; --- unverified ---
    move.w d4,d1
    moveq #12,d0
    lsr.w d0,d1
    bsr.w sub_1c6c
hint_364a:
; --- unverified ---
    moveq #119,d0
    andi.w #$800,d4
    beq.s hint_3654
hint_3652:
    dc.b    $70,$6c
hint_3654:
; --- unverified ---
    move.b #$2e,(a4)+
    move.b d0,(a4)+
    move.b #$29,(a4)+
hint_365e:
    rts
hint_3660:
; --- unverified ---
    lea pcref_366a(pc),a0
    move.b d1,d0
    bra.w sub_1cba
pcref_366a:
    dc.b    $00,$1a,$00,$46,$00,$5c,$00,$8c,$01,$04,$01,$2c,$01,$2c,$01,$2c
hint_367a:
    dc.b    $18,$fc
hint_3684:
; --- unverified ---
    btst #5,d4
    beq.s hint_367a
hint_368a:
; --- unverified ---
    move.w (a5)+,d1
    ext.l d1
    bsr.s hint_369e
hint_3690:
; --- unverified ---
    bsr.w hint_1b88
hint_3694:
; --- unverified ---
    move.b #$2e,(a4)+
    move.b #$77,(a4)+
    rts
hint_369e:
; --- unverified ---
    bset #0,331(a6) ; app+$14B
    bne.s hint_36ae
hint_36a6:
    dc.b    $2d,$41,$01,$4e,$1d,$45,$01,$4d
hint_36ae:
; --- unverified ---
    rts
hint_36b0:
; --- unverified ---
    btst #5,d4
    beq.s hint_367a
hint_36b6:
; --- unverified ---
    move.l (a5)+,d1
    bsr.s hint_369e
hint_36ba:
; --- unverified ---
    bra.w hint_1b88
pcref_36be:
    dc.b    $05,$28,$70,$63
    dc.b    $29,$7d
sub_36c4:
; --- unverified ---
    move.l d0,d0
    btst #6,d4
    beq.s hint_367a
hint_36cc:
; --- unverified ---
    move.w (a5),d1
    ext.l d1
    add.l a5,d1
    addq.l #2,a5
    add.l 4(a6),d1 ; app+$4
    bsr.s hint_369e
hint_36da:
; --- unverified ---
    bsr.w hint_1b88
hint_36de:
; --- unverified ---
    lea pcref_36f0(pc),a0
    tst.b 1426(a6) ; app+$592
    beq.s hint_36ec
hint_36e8:
    dc.b    $41,$fa,$ff,$d4
hint_36ec:
; --- unverified ---
    bra.w sub_1cc6
pcref_36f0:
; --- unverified ---
    subi.b #$63,10528(a0)
    btst #6,d4
    beq.w hint_367a
hint_36fe:
; --- unverified ---
    move.w (a5),d6
    move.w d6,d4
    move.w #$700,d0
    and.w d4,d0
    bne.w hint_3348
hint_370c:
; --- unverified ---
    move.b d6,d1
    ext.w d1
    ext.l d1
    add.l a5,d1
    addq.l #2,a5
    add.l 4(a6),d1 ; app+$4
    bsr.w hint_1b88
hint_371e:
; --- unverified ---
    lea pcref_3730(pc),a0
    bsr.w sub_1cc6
hint_3726:
; --- unverified ---
    tst.w d6
    bmi.s hint_3736
hint_372a:
; --- unverified ---
    move.b #$64,(a4)+
    bra.s hint_373a
pcref_3730:
    dc.b    $04,$28,$70,$63,$2c,$20
hint_3736:
    dc.b    $18,$fc,$00,$61
hint_373a:
; --- unverified ---
    move.w d6,d1
    moveq #12,d0
    lsr.w d0,d1
    bsr.w sub_1c6c
hint_3744:
; --- unverified ---
    move.b #$2e,(a4)+
    andi.w #$800,d6
    beq.s hint_3754
hint_374e:
; --- unverified ---
    move.b #$6c,(a4)+
    bra.s hint_3758
hint_3754:
    dc.b    $18,$fc,$00,$77
hint_3758:
; --- unverified ---
    move.b #$29,(a4)+
    bset #0,331(a6) ; app+$14B
    beq.s hint_3766
hint_3764:
; --- unverified ---
    rts
hint_3766:
; --- unverified ---
    lea -2(a5),a0
    bra.w hint_3312
hint_376e:
; --- unverified ---
    btst #7,d4
    beq.w hint_367a
hint_3776:
; --- unverified ---
    move.b #$23,(a4)+
    tst.b d5
    bne.s hint_3784
hint_377e:
; --- unverified ---
    move.w (a5)+,d1
    bra.w hint_1b6e
hint_3784:
; --- unverified ---
    cmp.b #$2,d5
    bne.s hint_3790
hint_378a:
; --- unverified ---
    move.l (a5)+,d1
    bra.w hint_1b88
hint_3790:
; --- unverified ---
    move.w (a5)+,d1
    bra.w hint_1b80
hint_3796:
; --- unverified ---
    move.b #$3f,(a4)+
    rts
pcref_379c:
    dc.b    $f1,$38,$01,$08,$f9,$c0,$00,$c0,$ff,$00,$00,$00,$ff,$00,$02,$00
    dc.b    $ff,$00,$04,$00,$ff,$00,$06,$00,$ff,$c0,$0a,$c0,$fd,$c0,$0c,$c0
    dc.b    $ff,$00,$08,$00,$ff,$00,$0a,$00,$ff,$00,$0c,$00,$f1,$00,$01,$00
    dc.b    $f0,$00,$10,$00,$f1,$c0,$20,$40,$f0,$00,$20,$00,$f1,$c0,$30,$40
    dc.b    $f0,$00,$30,$00,$ff,$ff,$4a,$fb,$ff,$ff,$4a,$fc,$ff,$ff,$4e,$70
    dc.b    $ff,$ff,$4e,$71,$ff,$ff,$4e,$72,$ff,$ff,$4e,$73,$ff,$ff,$4e,$74
    dc.b    $ff,$ff,$4e,$75,$ff,$ff,$4e,$76,$ff,$ff,$4e,$77,$ff,$fe,$4e,$7a
    dc.b    $ff,$f8,$48,$40,$ff,$f8,$48,$80,$ff,$f8,$48,$c0,$ff,$f8,$4e,$50
    dc.b    $ff,$f8,$4e,$58,$ff,$f8,$4e,$60,$ff,$f8,$4e,$68,$ff,$f8,$49,$c0
    dc.b    $ff,$f0,$4e,$40,$ff,$c0,$40,$c0,$ff,$c0,$42,$c0,$ff,$f8,$48,$48
    dc.b    $ff,$c0,$44,$c0,$ff,$c0,$46,$c0,$ff,$f8,$48,$08,$ff,$c0,$48,$00
    dc.b    $ff,$c0,$4a,$c0,$ff,$c0,$4e,$80,$ff,$c0,$4e,$c0,$ff,$c0,$4c,$00
    dc.b    $ff,$c0,$4c,$40,$ff,$80,$48,$80,$ff,$80,$4c,$80,$ff,$40,$48,$40
    dc.b    $ff,$00,$40,$00,$ff,$00,$42,$00,$ff,$00,$44,$00,$ff,$00,$46,$00
    dc.b    $ff,$00,$4a,$00,$f1,$40,$41,$00,$f1,$c0,$41,$c0,$f0,$fe,$50,$f8
    dc.b    $f0,$f8,$50,$f8,$f0,$f8,$50,$c8,$f0,$c0,$50,$c0,$f1,$00,$50,$00
    dc.b    $f1,$00,$51,$00,$f0,$00,$60,$00,$f1,$00,$70,$00,$f1,$f0,$81,$00
    dc.b    $f1,$f0,$81,$40,$f1,$f0,$81,$80,$f1,$c0,$80,$c0,$f1,$c0,$81,$c0
    dc.b    $f0,$00,$80,$00,$f0,$c0,$90,$c0,$f1,$30,$91,$00,$f0,$00,$90,$00
    dc.b    $f1,$38,$b1,$08,$f0,$00,$b0,$00,$f1,$f0,$c1,$00,$f1,$c0,$c0,$c0
    dc.b    $f1,$c0,$c1,$c0,$f1,$30,$c1,$00,$f0,$00,$c0,$00,$f0,$c0,$d0,$c0
    dc.b    $f1,$30,$d1,$00,$f0,$00,$d0,$00,$ff,$c0,$e8,$c0,$ff,$c0,$e9,$c0
    dc.b    $ff,$c0,$ea,$c0,$ff,$c0,$eb,$c0,$ff,$c0,$ec,$c0,$ff,$c0,$ed,$c0
    dc.b    $ff,$c0,$ee,$c0,$ff,$c0,$ef,$c0,$f0,$00,$e0,$00,$ff,$c0,$f0,$00
    dc.b    $ff,$c0,$f2,$00,$ff,$c0,$f2,$40,$ff,$80,$f2,$80,$ff,$c0,$f3,$00
    dc.b    $ff,$c0,$f3,$40
    dcb.b   4,0
pcref_3934:
    dc.b    $07,$03
    dc.b    "movep."
    dc.b    $02,$2a,$63,$04,$02,$6f,$72,$69,$05,$02,$61,$6e,$64,$69,$05,$02
    dc.b    $73,$75,$62,$69,$05,$02,$61,$64,$64,$69,$04,$29,$63,$61,$73,$04
    dc.b    $29,$63,$61,$73,$02,$05,$62,$05,$02,$65,$6f,$72,$69,$05,$2b,$63
    dc.b    $6d,$70,$69,$02,$04,$62,$08,$06
    dc.b    "move.b "
    dc.b    $09
    dc.b    "8movea.l "
    dc.b    $08,$06
    dc.b    "move.l "
    dc.b    $09,$06
    dc.b    "movea.w "
    dc.b    $08,$06
    dc.b    "move.w "
    dc.b    $06
    dc.b    "!dc.w "
    dc.b    $08
    dc.b    ""illegal"
    dc.b    $06,$00,$72,$65,$73,$65,$74,$04,$00,$6e,$6f,$70,$07,$07
    dc.b    "stop #"
    dc.b    $04,$00,$72,$74,$65,$06,$07,$72,$74,$64,$20,$23,$04,$00,$72,$74
    dc.b    $73,$06,$00,$74,$72,$61,$70,$76,$04,$00,$72,$74,$72,$07
    dc.b    "#movec "
    dc.b    $07,$08
    dc.b    "swap d"
    dc.b    $08,$08
    dc.b    "ext.w d"
    dc.b    $08,$08
    dc.b    "ext.l d"
    dc.b    $07,$09
    dc.b    "link a"
    dc.b    $07,$08
    dc.b    "unlk a"
    dc.b    $09,$0a
    dc.b    "move.l a"
    dc.b    $0d,$08
    dc.b    "move.l usp,a"
    dc.b    $09
    dc.b    "%extb.l d"
    dc.b    $07,$0b
    dc.b    "trap #"
    dc.b    $0a,$0c
    dc.b    "move sr,."
    dc.b    $0a
    dc.b    "$move ccr,"
    dc.b    $07,$08
    dc.b    "bkpt #"
    dc.b    $08,$0d
    dc.b    "move.b "
    dc.b    $08,$0e
    dc.b    "move.w "
    dc.b    $09
    dc.b    "/link.l a"
    dc.b    $07,$0c
    dc.b    "nbcd ."
    dc.b    $06,$0c,$74,$61,$73,$20,$2e,$05,$37,$6a,$73,$72,$20,$05,$37,$6a
    dc.b    $6d,$70,$20,$04,$2d,$6d,$75,$6c,$04,$2e,$64,$69,$76,$06,$10,$6d
    dc.b    $6f,$76,$65,$6d,$06,$0f,$6d,$6f,$76,$65,$6d,$06,$0c,$70,$65,$61
    dc.b    $20,$2e,$05,$0c,$6e,$65,$67,$78,$04,$0c,$63,$6c,$72,$04,$0c,$6e
    dc.b    $65,$67,$04,$0c,$6e,$6f,$74,$04,$2c,$74,$73,$74,$04,$11,$63,$68
    dc.b    $6b,$05,$12,$6c,$65,$61,$20,$02,$14,$73,$05,$31,$74,$72,$61,$70
    dc.b    $03,$13,$64,$62,$02,$14,$73,$05,$15,$61,$64,$64,$71,$05,$15,$73
    dc.b    $75,$62,$71,$02,$17,$62,$08,$18
    dc.b    "moveq #"
    dc.b    $06,$19,$73,$62,$63,$64,$20,$06
    dc.b    "0pack "
    dc.b    $06
    dc.b    "0unpk "
    dc.b    $05,$11,$64,$69,$76,$75,$05,$11,$64,$69,$76,$73,$03,$1f,$6f,$72
    dc.b    $05,$1e,$73,$75,$62,$61,$05,$19,$73,$75,$62,$78,$04,$1e,$73,$75
    dc.b    $62,$05,$1c,$63,$6d,$70,$6d,$01,$1d,$06,$19,$61,$62,$63,$64,$20
    dc.b    $05,$11,$6d,$75,$6c,$75,$05,$11,$6d,$75,$6c,$73,$05,$16,$65,$78
    dc.b    $67,$20,$04,$1f,$61,$6e,$64,$05,$1e,$61,$64,$64,$61,$05,$19,$61
    dc.b    $64,$64,$78,$04,$1e,$61,$64,$64,$07
    dc.b    "&bftst "
    dc.b    $08
    dc.b    "'bfextu "
    dc.b    $07
    dc.b    "&bfchg "
    dc.b    $08
    dc.b    "'bfexts "
    dc.b    $07
    dc.b    "&bfclr "
    dc.b    $07
    dc.b    "'bfffo "
    dc.b    $07
    dc.b    "&bfset "
    dc.b    $07
    dc.b    "(bfins "
    dc.b    $01,$20,$02,$36,$70,$02,$32,$66,$02,$33,$66,$02,$34,$66,$07
    dc.b    "5fsave "
    dc.b    $0a
    dc.b    "5frestore "
    dc.b    $06
    dc.b    "!dc.w "
sub_3bd6:
; --- unverified ---
    movem.l d3-d7/a3-a5,-(sp)
    move.l 174(a6),-(sp) ; app+$AE
    move.l app_freemem_memoryblock(a6),-(sp)
    clr.l 174(a6) ; app+$AE
    clr.l app_freemem_memoryblock(a6)
    move.l a2,-(sp)
    moveq #3,d4
    lea -12(a2),a5
    movea.l a5,a2
    bsr.w call_typeofmem
hint_3bf8:
; --- unverified ---
    bne.s hint_3c40
hint_3bfa:
; --- unverified ---
    addq.w #2,a5
    movem.l d4/a5,-(sp)
    bsr.w sub_1c78
hint_3c04:
; --- unverified ---
    cmpa.l 8(sp),a5
    movem.l (sp)+,d4/a5
    bne.s hint_3c3c
hint_3c0e:
    dc.b    $43,$ee,$09,$a8
hint_3c12:
; --- unverified ---
    move.b (a1)+,d1
    cmp.b #$5b,d1
    beq.s hint_3c26
hint_3c1a:
; --- unverified ---
    cmp.b #$3f,d1
    beq.s hint_3c3c
hint_3c20:
; --- unverified ---
    cmp.b #$a,d1
    bne.s hint_3c12
hint_3c26:
    dc.b    $58,$8f,$70,$00
hint_3c2a:
; --- unverified ---
    move.l (sp)+,app_freemem_memoryblock(a6)
    move.l (sp)+,174(a6) ; app+$AE
    movea.l a5,a2
    movem.l (sp)+,d3-d7/a3-a5
    tst.b d0
    rts
hint_3c3c:
; --- unverified ---
    dbf d4,hint_3bfa
hint_3c40:
; --- unverified ---
    movea.l (sp)+,a5
    subq.w #2,a5
    moveq #-1,d0
    bra.s hint_3c2a
hint_3c48:
    dc.b    $2d,$4a
hint_3c4a:
    dc.b    $00,$54
hint_3c50:
; --- unverified ---
    move.l a2,app_exec_base_0054(a6)
    bset #7,90(a6) ; app+$5A
    st d3
    bra.w loc_1926
hint_3c60:
; --- unverified ---
    lea 1364(a6),a0 ; app+$554
    move.l #$4e714e71,d0 ; 'NqNq'
    move.l d0,(a0)
    move.l d0,4(a0)
    move.w d0,8(a0)
    move.w #$4afc,10(a0)
    move.w (a2),d0
    cmp.w #$4afc,d0
    beq.s hint_3c48
hint_3c82:
; --- unverified ---
    andi.w #$fff0,d0
    cmp.w #$4e40,d0
    beq.s hint_3cac
hint_3c8c:
; --- unverified ---
    andi.w #$ffc0,d0
    cmp.w #$4e80,d0
    beq.s hint_3cb2
hint_3c96:
; --- unverified ---
    andi.w #$ff00,d0
    cmp.w #$6100,d0
    beq.w hint_3d2e
hint_3ca2:
; --- unverified ---
    andi.w #$f000,d0
    cmp.w #$a000,d0
    bne.s hint_3c50
hint_3cac:
; --- unverified ---
    move.w (a2)+,(a0)
    bra.w hint_3d50
hint_3cb2:
; --- unverified ---
    move.w (a2)+,d0
    move.w d0,(a0)
    move.b d0,d1
    andi.b #$38,d1
    cmp.b #$10,d1
    beq.w hint_3d50
hint_3cc4:
; --- unverified ---
    cmp.b #$28,d1
    beq.s hint_3cf4
hint_3cca:
; --- unverified ---
    cmp.b #$30,d1
    beq.s hint_3cf4
hint_3cd0:
; --- unverified ---
    cmp.b #$38,d1
    bne.s hint_3cf0
hint_3cd6:
; --- unverified ---
    move.b d0,d1
    andi.b #$7,d1
    beq.s hint_3cf4
hint_3cde:
; --- unverified ---
    cmp.b #$4,d1
    bcc.s hint_3cf0
hint_3ce4:
; --- unverified ---
    cmp.b #$1,d1
    bne.s hint_3cfa
hint_3cea:
; --- unverified ---
    move.l (a2)+,2(a0)
    bra.s hint_3d50
hint_3cf0:
; --- unverified ---
    bra.w hint_3c50
hint_3cf4:
    dc.b    $31,$5a
hint_3cf6:
    dc.b    $00,$02
hint_3cfa:
; --- unverified ---
    cmp.b #$2,d1
    bne.s hint_3d0a
hint_3d00:
; --- unverified ---
    move.l a2,d0
    move.w (a2)+,d1
    ext.l d1
    add.l d1,d0
    bra.s hint_3d3a
hint_3d0a:
; --- unverified ---
    move.w (a2)+,d1
    move.b d1,d0
    ext.w d0
    ext.l d0
    add.l a2,d0
    subq.l #2,d0
    move.w d1,d2
    rol.w #6,d2
    andi.w #$3c,d2
    move.l 16(a6,d2.w),d2
    btst #11,d1
    bne.s hint_3d2a
hint_3d28:
    dc.b    $48,$c2
hint_3d2a:
; --- unverified ---
    add.l d2,d0
    bra.s hint_3d3a
hint_3d2e:
; --- unverified ---
    move.w (a2)+,d0
    tst.b d0
    beq.s hint_3d44
hint_3d34:
    dc.b    $48,$80,$48,$c0,$d0,$8a
hint_3d3a:
; --- unverified ---
    move.w #$4eb9,(a0)
    move.l d0,2(a0)
    bra.s hint_3d50
hint_3d44:
; --- unverified ---
    move.w (a2)+,d0
    ext.l d0
    lea -2(a2,d0.w),a1
    move.l a1,d0
    bra.s hint_3d3a
hint_3d50:
; --- unverified ---
    move.l a2,1376(a6) ; app+$560
    move.l a0,-(sp)
    move.l (sp)+,app_exec_base_0054(a6)
    bclr #7,90(a6) ; app+$5A
    st d3
    bra.w loc_1926
sub_3d66:
    moveq #7,d0
    lea 414(a6),a0 ; app+$19E
loc_3d6c:
    clr.w (a0)
    lea 72(a0),a0
    dbf d0,loc_3d6c
loc_3d76:
    rts
sub_3d78:
    moveq #7,d0
    lea 408(a6),a0 ; app+$198
loc_3d7e:
    tst.w 6(a0)
    beq.s loc_3d9e
loc_3d84:
    movea.l (a0),a1
    cmpi.w #$4afc,(a1)
    beq.s loc_3d94
loc_3d8c:
    clr.w 6(a0)
    clr.l (a0)
    bra.s loc_3d9e
loc_3d94:
    lea 72(a0),a0
    dbf d0,loc_3d7e
loc_3d9c:
    moveq #-1,d0
loc_3d9e:
    rts
too_many_breakpoints:
    move.l a1,-(sp)
    bsr.w sub_3e3c
loc_3da6:
    bne.s loc_3dac
loc_3da8:
    bsr.w sub_3e6e
loc_3dac:
    bsr.s sub_3d78
loc_3dae:
    movea.l (sp)+,a1
    lea str_85ee(pc),a2
    bne.s loc_3e06
loc_3db6:
    move.l a1,d0
    btst #0,d0
    lea str_85d6(pc),a2
    bne.s loc_3e06
loc_3dc2:
    cmp.b #$4,d3
    bne.s loc_3dd6
loc_3dc8:
    move.l a0,-(sp)
    lea 12(a0),a0
loc_3dce:
    move.b (a4)+,(a0)+
    bne.s loc_3dce
loc_3dd2:
    movea.l (sp)+,a0
    bra.s loc_3de0
loc_3dd6:
    bsr.w sub_73a4
loc_3dda:
    lea str_85ce(pc),a2
    bne.s loc_3e06
loc_3de0:
    bsr.s call_forbid
loc_3de2:
    move.w (a1),4(a0)
    move.w #$4afc,(a1)
    cmpi.w #$4afc,(a1)
    lea str_85e0(pc),a2
    bne.s loc_3e04
loc_3df4:
    bsr.s call_permit
loc_3df6:
    move.l a1,(a0)
    move.l d2,8(a0)
    move.w d3,6(a0)
    moveq #0,d0
    rts
loc_3e04:
    bsr.s call_permit
loc_3e06:
    movea.l a2,a0
    bsr.w sub_1ad6
loc_3e0c:
    moveq #-1,d0
    rts
call_forbid:
    movem.l d0-d1/a0-a1,-(sp)
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOForbid(a6) ; app-$84
loc_3e1e:
    movea.l (sp)+,a6
    movem.l (sp)+,d0-d1/a0-a1
    rts
call_permit:
    movem.l d0-d1/a0-a1,-(sp)
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOPermit(a6) ; app-$8A
loc_3e34:
    movea.l (sp)+,a6
    movem.l (sp)+,d0-d1/a0-a1
    rts
sub_3e3c:
    moveq #7,d0
    lea 408(a6),a0 ; app+$198
loc_3e42:
    cmpa.l (a0),a1
    bne.s loc_3e50
loc_3e46:
    tst.w 6(a0)
    beq.s loc_3e50
loc_3e4c:
    moveq #0,d0
    rts
loc_3e50:
    lea 72(a0),a0
    dbf d0,loc_3e42
loc_3e58:
    moveq #-1,d0
    rts
sub_3e5c:
    moveq #7,d0
    lea 408(a6),a0 ; app+$198
loc_3e62:
    bsr.s sub_3e6e
loc_3e64:
    lea 72(a0),a0
    dbf d0,loc_3e62
loc_3e6c:
    rts
sub_3e6e:
    bsr.s call_forbid
loc_3e70:
    tst.w 6(a0)
    beq.s loc_3e86
loc_3e76:
    clr.w 6(a0)
    movea.l (a0),a1
    cmpi.w #$4afc,(a1)
    bne.s loc_3e86
loc_3e82:
    move.w 4(a0),(a1)
loc_3e86:
    bra.s call_permit
sub_3e88:
; --- unverified ---
    bsr.s call_forbid
hint_3e8a:
; --- unverified ---
    move.l a1,1380(a6) ; app+$564
    move.w (a1),1384(a6) ; app+$568
    move.w #$4afc,(a1)
    bra.s call_permit
sub_3e98:
    movea.l AbsExecBase,a0
    move.l 62(a0),8(a6) ; app+$8
    lea 322(a0),a1
    move.l a1,12(a6) ; app+$C
    rts
sub_3eac:
; --- unverified ---
    cmpa.l 8(a6),a2 ; app+$8
    bcs.s hint_3ec8
hint_3eb2:
; --- unverified ---
    cmpa.l #$f80000,a2
    bcs.s hint_3ece
hint_3eba:
; --- unverified ---
    cmpa.l #$1000000,a2
    bcc.s hint_3ece
hint_3ec2:
; --- unverified ---
    lea pcref_3f08(pc),a5
    rts
hint_3ec8:
; --- unverified ---
    lea pcref_3ef0(pc),a5
    rts
hint_3ece:
    dc.b    $28,$6e,$00,$0c
hint_3ed2:
; --- unverified ---
    move.l (a4),d0
    beq.s hint_3eec
hint_3ed6:
; --- unverified ---
    movea.l d0,a4
    tst.l (a4)
    beq.s hint_3eec
hint_3edc:
; --- unverified ---
    cmpa.l a4,a2
    bcs.s hint_3ed2
hint_3ee0:
; --- unverified ---
    cmpa.l 24(a4),a2
    bcc.s hint_3ed2
hint_3ee6:
; --- unverified ---
    lea pcref_3f32(pc),a5
    rts
hint_3eec:
; --- unverified ---
    suba.l a2,a2
    bra.s hint_3ec8
pcref_3ef0:
; --- unverified ---
    addq.l #1,a2
    cmpa.l 8(a6),a2 ; app+$8
    bcc.s hint_3efa
hint_3ef8:
; --- unverified ---
    rts
hint_3efa:
; --- unverified ---
    lea pcref_3f08(pc),a5
    movea.l #$f80000,a2
    cmp.b d1,d1
    rts
pcref_3f08:
; --- unverified ---
    addq.l #1,a2
    cmpa.l #$1000000,a2
    bcc.s hint_3f14
hint_3f12:
; --- unverified ---
    rts
hint_3f14:
; --- unverified ---
    movea.l 12(a6),a4 ; app+$C
    tst.l (a4)
    beq.s hint_3f4e
hint_3f1c:
; --- unverified ---
    movea.l (a4),a4
    tst.l (a4)
    beq.s hint_3f4e
hint_3f22:
; --- unverified ---
    cmpa.l 8(a6),a4 ; app+$8
    bcs.s hint_3f1c
hint_3f28:
; --- unverified ---
    movea.l a4,a2
    lea pcref_3f32(pc),a5
    cmp.b d1,d1
    rts
pcref_3f32:
; --- unverified ---
    addq.l #1,a2
    cmpa.l 24(a4),a2
    bcc.s hint_3f3c
hint_3f3a:
; --- unverified ---
    rts
hint_3f3c:
; --- unverified ---
    movea.l (a4),a4
    tst.l (a4)
    beq.s hint_3f4e
hint_3f42:
; --- unverified ---
    cmpa.l 8(a6),a4 ; app+$8
    bcs.s hint_3f3c
hint_3f48:
; --- unverified ---
    cmp.b d1,d1
    movea.l a4,a2
    rts
hint_3f4e:
; --- unverified ---
    suba.l a2,a2
    lea pcref_3ef0(pc),a5
    cmp.b d1,d1
    rts
sub_3f58:
    lea 990(a6),a0 ; app+$3DE
    move.l a0,1360(a6) ; app+$550
    moveq #4,d0
loc_3f62:
    clr.l 70(a0)
    lea 74(a0),a0
    dbf d0,loc_3f62
loc_3f6e:
    rts
sub_3f70:
    movea.l 1360(a6),a0 ; app+$550
    lea 16(a6),a1 ; app+$10
    moveq #15,d0
loc_3f7a:
    move.l (a1)+,(a0)+
    dbf d0,loc_3f7a
loc_3f80:
    move.l 80(a6),(a0)+ ; app+$50
    move.w 90(a6),(a0)+ ; app+$5A
    move.l app_exec_base_0054(a6),(a0)+
    lea 1360(a6),a1 ; app+$550
    cmpa.l a0,a1
    bne.s loc_3f98
loc_3f94:
    lea 990(a6),a0 ; app+$3DE
loc_3f98:
    move.l a0,1360(a6) ; app+$550
    rts
sub_3f9e:
; --- unverified ---
    lea str_8660(pc),a2
    bsr.w hint_5eac
hint_3fa6:
; --- unverified ---
    move.b #$10,53(a3)
    tst.l 1060(a6) ; app+$424
    beq.w hint_40a4
hint_3fb4:
; --- unverified ---
    moveq #48,d4
    moveq #7,d5
    moveq #6,d2
    bra.s hint_3fbe
hint_3fbc:
    dc.b    $74,$08
hint_3fbe:
; --- unverified ---
    bsr.w sub_6a76
hint_3fc2:
; --- unverified ---
    move.b d4,d1
    bsr.w sub_58ba
hint_3fc8:
; --- unverified ---
    addq.b #1,d4
    dbf d5,hint_3fbc
hint_3fce:
; --- unverified ---
    bsr.w hint_6a94
hint_3fd2:
; --- unverified ---
    lea 990(a6),a0 ; app+$3DE
    movea.l a0,a4
    lea 1360(a6),a2 ; app+$550
    tst.l 144(a0)
    beq.s hint_3ff8
hint_3fe2:
; --- unverified ---
    tst.l 218(a0)
    beq.s hint_3ff8
hint_3fe8:
; --- unverified ---
    tst.l 292(a0)
    beq.s hint_3ff8
hint_3fee:
; --- unverified ---
    tst.l 366(a0)
    beq.s hint_3ff8
hint_3ff4:
    dc.b    $28,$6e,$05,$50
hint_3ff8:
; --- unverified ---
    moveq #12,d1
    bsr.w sub_6a5a
hint_3ffe:
    dc.b    $76,$07
hint_4000:
; --- unverified ---
    bsr.w sub_6a82
hint_4004:
; --- unverified ---
    move.l (a4)+,d2
    bsr.w hint_6a9a
hint_400a:
; --- unverified ---
    dbf d3,hint_4000
hint_400e:
; --- unverified ---
    bsr.w hint_5094
hint_4012:
; --- unverified ---
    moveq #13,d1
    bsr.w sub_6a5a
hint_4018:
    dc.b    $76,$07
hint_401a:
; --- unverified ---
    bsr.w sub_6a82
hint_401e:
; --- unverified ---
    move.l (a4)+,d2
    bsr.w hint_6a9a
hint_4024:
; --- unverified ---
    dbf d3,hint_401a
hint_4028:
; --- unverified ---
    bsr.w hint_5094
hint_402c:
; --- unverified ---
    moveq #2,d1
    bsr.w sub_6a5a
hint_4032:
; --- unverified ---
    move.l (a4)+,d2
    bsr.w hint_6a9a
hint_4038:
; --- unverified ---
    bsr.w sub_6a82
hint_403c:
; --- unverified ---
    moveq #1,d1
    bsr.w sub_6a5a
hint_4042:
; --- unverified ---
    move.w (a4),d2
    bsr.w hint_6aa2
hint_4048:
; --- unverified ---
    bsr.w sub_6a82
hint_404c:
; --- unverified ---
    move.w (a4)+,d4
    bsr.w hint_66a2
hint_4052:
; --- unverified ---
    bsr.w hint_5094
hint_4056:
; --- unverified ---
    moveq #0,d1
    bsr.w sub_6a5a
hint_405c:
; --- unverified ---
    move.l (a4),d2
    bsr.w hint_6a9a
hint_4062:
; --- unverified ---
    bsr.w sub_6a82
hint_4066:
; --- unverified ---
    move.b 53(a3),d2
    move.l (a4),d0
    bsr.w hint_7ef8
hint_4070:
; --- unverified ---
    beq.s hint_4076
hint_4072:
; --- unverified ---
    bsr.w sub_7bd8
hint_4076:
; --- unverified ---
    addq.b #1,d2
    bsr.w sub_6a76
hint_407c:
; --- unverified ---
    move.l a2,-(sp)
    movea.l (a4)+,a2
    bsr.w sub_69a6
hint_4084:
; --- unverified ---
    bsr.w loc_5836
hint_4088:
; --- unverified ---
    movea.l (sp)+,a2
    bsr.w hint_5094
hint_408e:
; --- unverified ---
    cmpa.l a4,a2
    bne.s hint_4096
hint_4092:
    dc.b    $49,$ee,$03,$de
hint_4096:
; --- unverified ---
    cmpa.l 1360(a6),a4 ; app+$550
    beq.s hint_40a4
hint_409c:
; --- unverified ---
    tst.l 70(a4)
    bne.w hint_3ff8
hint_40a4:
; --- unverified ---
    bsr.w hint_50a4
hint_40a8:
; --- unverified ---
    bra.w sub_5d9c
call_replymsg:
    movem.l d0-d2/a0-a2,-(sp)
    movea.l app_closewindow_window(a6),a0
    movea.l wd_UserPort(a0),a0
    bsr.w call_forbid_42d6
loc_40bc:
    beq.s loc_40f2
loc_40be:
    move.l 20(a1),d1
    cmp.l #$400,d1
    bne.s loc_40e6
loc_40ca:
    bsr.w call_rawkeyconvert
loc_40ce:
    bmi.s loc_40e6
loc_40d0:
    cmp.w #$1b,d1
    bne.s loc_40e6
loc_40d6:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOReplyMsg(a6) ; app-$17A
loc_40e0:
    movea.l (sp)+,a6
    moveq #0,d0
    bra.s loc_40f4
loc_40e6:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOReplyMsg(a6) ; app-$17A
loc_40f0:
    movea.l (sp)+,a6
loc_40f2:
    moveq #-1,d0
loc_40f4:
    movem.l (sp)+,d0-d2/a0-a2
    rts
call_replymsg_40fa:
    movem.l d0/d2/a0-a2,-(sp)
loc_40fe:
    movea.l app_closewindow_window(a6),a0
    movea.l wd_UserPort(a0),a0
    bsr.w call_forbid_42d6
loc_410a:
    beq.s loc_411a
loc_410c:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOReplyMsg(a6) ; app-$17A
loc_4116:
    movea.l (sp)+,a6
    bra.s loc_40fe
loc_411a:
    movem.l (sp)+,d0/d2/a0-a2
    rts
sub_4120:
    bsr.s call_replymsg_40fa
loc_4122:
    bra.s call_replymsg_412c
sub_4124:
; --- unverified ---
    movem.l d0/d2-d3/d7/a0-a3,-(sp)
    st d7
    bra.s loc_4132
call_replymsg_412c:
    movem.l d0/d2-d3/d7/a0-a3,-(sp)
    sf d7
loc_4132:
    tst.l 1392(a6) ; app+$570
    beq.s loc_413c
loc_4138:
    bsr.w call_move_5940
loc_413c:
    tst.b d7
    beq.s loc_415e
loc_4140:
    moveq #0,d1 ; SetSignal: signalMask
    move.b dat_895e(pc),d0
    bset d0,d1
    moveq #0,d0 ; SetSignal: newSignals
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOSetSignal(a6) ; app-$132
loc_4154:
    movea.l (sp)+,a6
    move.b dat_895e(pc),d1
    btst d1,d0
    bne.s loc_419a
loc_415e:
    movea.l app_closewindow_window(a6),a0
    movea.l wd_UserPort(a0),a0
    bsr.w call_forbid_42d6
loc_416a:
    bne.s loc_41b4
loc_416c:
    moveq #0,d0
    movea.l app_closewindow_window(a6),a0
    movea.l wd_UserPort(a0),a0
    move.b 15(a0),d1
    bset d1,d0
    tst.b d7
    beq.s loc_4186
loc_4180:
    move.b dat_895e(pc),d1
    bset d1,d0
loc_4186:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOWait(a6) ; app-$13E
loc_4190:
    movea.l (sp)+,a6
    move.b dat_895e(pc),d1
    btst d1,d0
    beq.s loc_41a6
loc_419a:
    movem.l d4-d7/a0-a5,-(sp)
    bsr.w loc_176c
loc_41a2:
    movem.l (sp)+,d4-d7/a0-a5
loc_41a6:
    movea.l app_closewindow_window(a6),a0
    movea.l wd_UserPort(a0),a0
    bsr.w call_forbid_42d6
loc_41b2:
    beq.s loc_413c
loc_41b4:
    move.l 20(a1),d1
    cmp.l #$400,d1
    bne.s loc_41e4
loc_41c0:
    bsr.s call_rawkeyconvert
loc_41c2:
    smi -(sp)
    move.w d1,-(sp)
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOReplyMsg(a6) ; app-$17A
loc_41d0:
    movea.l (sp)+,a6
    move.w (sp)+,d1
    move.b (sp)+,d0
    tst.w d1
    beq.w loc_413c
loc_41dc:
    tst.b d0
    movem.l (sp)+,d0/d2-d3/d7/a0-a3
    rts
loc_41e4:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOReplyMsg(a6) ; app-$17A
loc_41ee:
    movea.l (sp)+,a6
    bra.w loc_413c
call_rawkeyconvert:
    move.l a1,-(sp)
    lea 2120(a6),a0 ; app+$848
    move.l a0,-(sp)
    clr.l (a0)+
    move.b #$1,(a0)+
    clr.b (a0)+
    move.w 24(a1),(a0)+
    move.w 26(a1),(a0)+
    movea.l 28(a1),a1
    move.l (a1),(a0)
    movea.l (sp)+,a0 ; RawKeyConvert: event
    lea app_rawkeyconvert_buffer(a6),a1 ; RawKeyConvert: buffer
    clr.l (a1)
    moveq #4,d1 ; RawKeyConvert: length
    suba.l a2,a2 ; RawKeyConvert: keyMap
    move.l a6,-(sp)
    movea.l app_console_device_iorequest+IO_DEVICE(a6),a6
    jsr _LVORawKeyConvert(a6) ; app-$30
loc_4228:
    movea.l (sp)+,a6
    movea.l (sp)+,a1
    tst.l d0
    ble.s loc_428e
loc_4230:
    move.w 26(a1),d3
    lea app_rawkeyconvert_buffer(a6),a0
    move.b (a0)+,d1
    subq.l #1,d0
    beq.s loc_4296
loc_423e:
    cmp.b #$9b,d1
    bne.s loc_4292
loc_4244:
    move.b (a0)+,d2
    lea pcref_42c0(pc),a2
    subq.l #1,d0
    beq.s loc_4276
loc_424e:
    lea pcref_42cf(pc),a2
    subq.l #1,d0
    beq.s loc_4264
loc_4256:
    lea pcref_42d4(pc),a2
    move.b (a0)+,d2
    cmpi.b #$7e,(a0)
    beq.s loc_4276
loc_4262:
    bra.s loc_4292
loc_4264:
    move.w #$87,d1
    cmp.b #$3f,d2
    beq.s loc_4280
loc_426e:
    cmp.b #$20,d2
    bne.s loc_4292
loc_4274:
    move.b (a0)+,d2
loc_4276:
    move.b (a2)+,d0
    beq.s loc_4292
loc_427a:
    move.b (a2)+,d1
    cmp.b d2,d0
    bne.s loc_4276
loc_4280:
    cmp.b #$d,d1
    bne.s loc_4288
loc_4286:
    moveq #10,d1
loc_4288:
    andi.w #$ff,d1
    rts
loc_428e:
    moveq #0,d1
    rts
loc_4292:
    moveq #63,d1
    rts
loc_4296:
    btst #7,d3
    beq.s loc_4280
loc_429c:
    cmp.b #$61,d1
    bcs.s loc_42b8
loc_42a2:
    cmp.b #$7b,d1
    bcc.s loc_42b8
loc_42a8:
    andi.b #$df,d1
    cmp.b #$58,d1
    bne.s loc_42b8
loc_42b2:
    move.w #$86,d1
    rts
loc_42b8:
    andi.w #$ff,d1
    moveq #-1,d0
    rts
pcref_42c0:
    dc.b    $41,$82,$42,$83,$43,$85,$44,$84,$54,$80,$53,$81,$5a,$88,$00
pcref_42cf:
    dc.b    $40,$8a,$41,$89,$00
pcref_42d4:
    dc.b    $00,$00
call_forbid_42d6:
    movem.l d2/a2,-(sp)
    movea.l a0,a2
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOGetMsg(a6) ; app-$174
loc_42e6:
    movea.l (sp)+,a6
    move.l d0,d2
    beq.s loc_436a
loc_42ec:
    movea.l d0,a1
    cmpi.l #$400,20(a1)
    bne.s loc_436a
loc_42f8:
    btst #1,26(a1)
    beq.s loc_436a
loc_4300:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOForbid(a6) ; app-$84
loc_430a:
    movea.l (sp)+,a6
    movea.l 20(a2),a1
    movea.l d2,a2
    bra.s loc_4356
loc_4314:
    cmpi.l #$400,20(a1)
    bne.s loc_4354
loc_431e:
    btst #1,26(a1)
    beq.s loc_4354
loc_4326:
    move.w 24(a1),d0
    cmp.w 24(a2),d0
    bne.s loc_4354
loc_4330:
    movem.l a0-a1,-(sp)
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVORemove(a6) ; app-$FC
loc_433e:
    movea.l (sp)+,a6
    movea.l 4(sp),a1 ; ReplyMsg: message
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOReplyMsg(a6) ; app-$17A
loc_434e:
    movea.l (sp)+,a6
    movem.l (sp)+,a0-a1
loc_4354:
    movea.l a0,a1
loc_4356:
    movea.l (a1),a0
    move.l a0,d0
    bne.s loc_4314
loc_435c:
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOPermit(a6) ; app-$8A
loc_4366:
    movea.l (sp)+,a6
    movea.l d2,a1
loc_436a:
    move.l d2,d0
    movem.l (sp)+,d2/a2
    rts
pcref_4372:
    dc.b    $00,$3e,$cb,$9c,$00,$3c,$cb,$ac,$00,$2e,$cb,$e6,$00,$2c,$cb,$fe
    dc.b    $00,$1b,$c7,$5c,$00,$41,$cc,$54,$00,$42,$05,$26,$00,$44,$09,$cc
    dc.b    $00,$47,$01,$a6,$00,$48,$fc,$06,$00,$49,$09,$60,$00,$4c,$3d,$32
    dc.b    $00,$4d,$c7,$ce,$00,$4e,$02,$dc,$00,$4f,$cf,$00,$00,$50,$0d,$24
    dc.b    $01,$52,$0a,$d0,$00,$53,$0a,$44,$01,$55,$01,$72,$00,$56,$00,$74
    dc.b    $00,$57,$09,$76,$01,$01,$01,$32,$02,$02,$00,$34,$00,$03,$00,$80
    dc.b    $00,$0b,$00,$4e,$03,$0c,$11,$36,$00,$10,$05,$a2,$02,$11,$10,$7e
    dc.b    $01,$12,$00,$e2,$01,$13,$01,$32
sub_43ea:
    dc.b    $01,$14,$00,$aa,$00,$15,$11,$04,$04,$18,$10,$c8,$01,$19,$00,$de
    dc.b    $01,$1a,$00,$da,$00,$00,$0c,$2b,$00,$03,$00,$34,$66,$18
hint_4408:
; --- unverified ---
    movea.l 56(a3),a1
    pea sub_5ede(pc)
    bsr.w sub_3e3c
hint_4414:
; --- unverified ---
    beq.w sub_3e6e
hint_4418:
; --- unverified ---
    moveq #1,d2
    moveq #1,d3
    bra.w too_many_breakpoints
hint_4420:
; --- unverified ---
    rts
hint_4422:
; --- unverified ---
    lea 16896(pc),a0
    bsr.w sub_1b28
hint_442a:
; --- unverified ---
    bne.s hint_4420
hint_442c:
; --- unverified ---
    bsr.w sub_3e5c
hint_4430:
; --- unverified ---
    bra.w sub_5ede
hint_4434:
; --- unverified ---
    bsr.w sub_5e9a
hint_4438:
; --- unverified ---
    lea 17393(pc),a0
    lea pcref_8838(pc),a1
    bsr.w sub_1a96
hint_4444:
; --- unverified ---
    bsr.w sub_4120
hint_4448:
; --- unverified ---
    bsr.w call_activatewindow
hint_444c:
; --- unverified ---
    bra.w sub_5d9c
hint_4450:
; --- unverified ---
    tst.b 308(a6) ; app+$134
    beq.s loc_4462
hint_4456:
; --- unverified ---
    lea 17320(pc),a0
    bsr.w sub_1b28
hint_445e:
; --- unverified ---
    beq.s loc_4462
hint_4460:
; --- unverified ---
    rts
loc_4462:
    bsr.w sub_3e5c
loc_4466:
    bsr.s call_unloadseg
loc_4468:
    bra.w call_closedevice
call_unloadseg:
    move.l dat_88f6(pc),d1
    beq.s loc_4494
loc_4472:
    clr.l dat_88f6
    clr.l 170(a6) ; app+$AA
    tst.b 308(a6) ; app+$134
    bne.s loc_4494
loc_4482:
    tst.l 350(a6) ; app+$15E
    bne.s loc_4494
loc_4488:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOUnLoadSeg(a6) ; app-$9C
loc_4492:
    movea.l (sp)+,a6
loc_4494:
    rts
sub_4496:
; --- unverified ---
    bsr.s hint_44a2
hint_4498:
; --- unverified ---
    bsr.w call_typeofmem
hint_449c:
; --- unverified ---
    beq.w hint_3c60
hint_44a0:
; --- unverified ---
    rts
hint_44a2:
; --- unverified ---
    tst.l 80(a6) ; app+$50
    beq.s hint_44bc
hint_44a8:
; --- unverified ---
    btst #0,87(a6) ; app+$57
    bne.s hint_44bc
hint_44b0:
; --- unverified ---
    movea.l app_exec_base_0054(a6),a2
    bsr.w call_typeofmem
hint_44b8:
; --- unverified ---
    bne.s hint_44bc
hint_44ba:
; --- unverified ---
    rts
hint_44bc:
; --- unverified ---
    addq.l #4,sp
    lea 16643(pc),a0
    bra.w sub_1ad6
hint_44c6:
; --- unverified ---
    bsr.s hint_44a2
hint_44c8:
; --- unverified ---
    move.w (a2),d1
    bclr #7,90(a6) ; app+$5A
    st d3
    bra.w loc_190a
hint_44d6:
; --- unverified ---
    bsr.s hint_44a2
hint_44d8:
; --- unverified ---
    st d3
    bset #7,90(a6) ; app+$5A
    movea.l app_exec_base_0054(a6),a1
    bsr.w sub_3e3c
hint_44e8:
; --- unverified ---
    bne.w loc_1926
hint_44ec:
; --- unverified ---
    cmpi.w #$3,6(a0)
    bne.w loc_1926
hint_44f6:
; --- unverified ---
    bra.w loc_190a
hint_44fa:
; --- unverified ---
    bsr.s hint_44a2
hint_44fc:
; --- unverified ---
    bclr #7,90(a6) ; app+$5A
    bsr.w sub_6964
hint_4506:
; --- unverified ---
    movea.l a2,a1
    moveq #1,d3
    moveq #1,d2
    bsr.w too_many_breakpoints
hint_4510:
; --- unverified ---
    bne.s hint_4518
hint_4512:
; --- unverified ---
    st d3
    bra.w loc_190a
hint_4518:
; --- unverified ---
    rts
hint_451a:
; --- unverified ---
    bsr.s hint_44a2
hint_451c:
; --- unverified ---
    bsr.w sub_6964
hint_4520:
; --- unverified ---
    move.l a2,app_exec_base_0054(a6)
    moveq #84,d2
    bsr.w sub_0de6
hint_452a:
; --- unverified ---
    bra.w sub_5ede
hint_452e:
; --- unverified ---
    lea hint_8604(pc),a0
    bsr.w hint_0834
hint_4536:
; --- unverified ---
    bne.s hint_44c6
hint_4538:
; --- unverified ---
    rts
hint_453a:
; --- unverified ---
    cmpi.b #$2,52(a3)
    bne.s hint_4544
hint_4542:
; --- unverified ---
    rts
hint_4544:
; --- unverified ---
    moveq #5,d3
    bsr.w esc_to_abort
hint_454a:
; --- unverified ---
    lea 16668(pc),a0
    bsr.w sub_6a6a
hint_4552:
; --- unverified ---
    movea.l 222(a6),a0 ; app+$DE
    moveq #84,d1
    cmpi.b #$4,52(a0)
    beq.s hint_45a0
hint_4560:
; --- unverified ---
    moveq #0,d3
    movem.w 10(a3),d2-d3
    divu.w app_rectfill_ymax(a6),d3
    bsr.w sub_576e
hint_4570:
; --- unverified ---
    bsr.w sub_4120
hint_4574:
; --- unverified ---
    bmi.s hint_4570
hint_4576:
; --- unverified ---
    cmp.b #$1b,d1
    beq.w hint_467c
hint_457e:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$42,d1
    beq.s hint_45a0
hint_4588:
; --- unverified ---
    cmp.b #$57,d1
    beq.s hint_45a0
hint_458e:
; --- unverified ---
    cmp.b #$4c,d1
    beq.s hint_45a0
hint_4594:
; --- unverified ---
    cmp.b #$54,d1
    beq.s hint_45a0
hint_459a:
; --- unverified ---
    cmp.b #$49,d1
    bne.s hint_4570
hint_45a0:
; --- unverified ---
    move.b d1,2959(a6) ; app+$B8F
    bsr.w sub_58ba
hint_45a8:
; --- unverified ---
    bsr.w sub_19d4
hint_45ac:
    dc.b    $49,$ee,$0a,$d4,$42,$14,$78,$00,$7c,$01
hint_45b6:
; --- unverified ---
    bsr.w loc_59c2
hint_45ba:
; --- unverified ---
    bne.w hint_467c
hint_45be:
; --- unverified ---
    tst.b (a4)
    beq.w hint_467c
hint_45c4:
; --- unverified ---
    bsr.w sub_19d4
hint_45c8:
; --- unverified ---
    lea 2959(a6),a5 ; app+$B8F
    move.b (a5)+,d5
    cmp.b #$49,d5
    beq.s hint_4638
hint_45d4:
; --- unverified ---
    cmp.b #$54,d5
    beq.s hint_4638
hint_45da:
    dc.b    $42,$2d,$ff,$fc
hint_45de:
; --- unverified ---
    move.b (a4)+,d1
    tst.b (a4)
    bne.s hint_45fc
hint_45e4:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$4c,d1
    beq.s hint_45f8
hint_45ee:
; --- unverified ---
    cmp.b #$57,d1
    bne.s hint_45fc
hint_45f4:
; --- unverified ---
    moveq #2,d6
    bra.s hint_462e
hint_45f8:
; --- unverified ---
    moveq #4,d6
    bra.s hint_462e
hint_45fc:
; --- unverified ---
    subq.w #1,a4
    bsr.w sub_6b70
hint_4602:
; --- unverified ---
    bne.s hint_4624
hint_4604:
; --- unverified ---
    cmp.b #$42,d5
    beq.s hint_4618
hint_460a:
; --- unverified ---
    cmp.b #$57,d5
    beq.s hint_4614
hint_4610:
; --- unverified ---
    move.l d2,(a5)+
    bra.s hint_461a
hint_4614:
; --- unverified ---
    move.w d2,(a5)+
    bra.s hint_461a
hint_4618:
    dc.b    $1a,$c2
hint_461a:
; --- unverified ---
    tst.b d1
    beq.s hint_462e
hint_461e:
; --- unverified ---
    cmp.b #$2c,d1
    beq.s hint_45de
hint_4624:
; --- unverified ---
    bsr.w sub_5e54
hint_4628:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bra.s hint_45b6
hint_462e:
; --- unverified ---
    lea 2960(a6),a0 ; app+$B90
    move.l a5,d0
    sub.l a0,d0
    bra.s hint_466c
hint_4638:
; --- unverified ---
    tst.b 2957(a6) ; app+$B8D
    lea 16598(pc),a0
    bsr.w hint_4b9c
hint_4644:
; --- unverified ---
    beq.s hint_464a
hint_4646:
    dc.b    $5a,$ee,$0b,$8d
hint_464a:
; --- unverified ---
    movea.l a4,a0
    tst.b 2957(a6) ; app+$B8D
    beq.s hint_465e
hint_4652:
; --- unverified ---
    move.b (a4)+,d1
    bsr.w sub_772e
hint_4658:
; --- unverified ---
    move.b d1,(a5)+
    bne.s hint_4652
hint_465c:
; --- unverified ---
    bra.s hint_4662
hint_465e:
; --- unverified ---
    move.b (a4)+,(a5)+
    bne.s hint_465e
hint_4662:
    dc.b    $20,$0c,$90,$88,$53,$80,$42,$2e,$0a,$d4
hint_466c:
; --- unverified ---
    move.b d0,2956(a6) ; app+$B8C
    subq.b #1,d6
    move.b d6,2958(a6) ; app+$B8E
    bsr.w sub_5d9c
hint_467a:
; --- unverified ---
    bra.s hint_4684
hint_467c:
    dc.b    $42,$6e
hint_467e:
    dc.b    $0b,$8c
hint_4684:
; --- unverified ---
    bsr.w sub_052a
hint_4688:
; --- unverified ---
    st 229(a6) ; app+$E5
    moveq #14,d1
    bsr.w sub_6a5a
hint_4692:
; --- unverified ---
    movea.l 222(a6),a0 ; app+$DE
    movea.l 56(a0),a2
    move.b 52(a0),d0
    move.w 54(a0),d4
    cmp.b #$2,d0
    beq.s hint_46d8
hint_46a8:
; --- unverified ---
    move.b d0,-(sp)
    bsr.w sub_3eac
hint_46ae:
; --- unverified ---
    move.b (sp)+,d0
    lea 2956(a6),a3 ; app+$B8C
    moveq #0,d3
    move.b (a3)+,d3
    beq.s hint_46d8
hint_46ba:
; --- unverified ---
    addq.w #1,a3
    moveq #0,d6
    move.b (a3)+,d6
    cmp.b #$4,d0
    beq.w hint_4780
hint_46c8:
; --- unverified ---
    bsr.w hint_46dc
hint_46cc:
; --- unverified ---
    move.b (a3)+,d0
    cmp.b #$49,d0
    bne.s hint_46e0
hint_46d4:
; --- unverified ---
    bra.w hint_47f6
hint_46d8:
; --- unverified ---
    bra.w sub_052a
hint_46dc:
    dc.b    $d5,$c6
dat_46de:
; --- unverified ---
    jmp (a5) ; unresolved_indirect_hint:ind
hint_46e0:
; --- unverified ---
    move.l d6,d4
    not.l d4
    move.l a2,d1
    and.l d1,d4
    movea.l d4,a2
    move.b (a3)+,d4
    subq.b #1,d3
    moveq #0,d5
    tst.b 2957(a6) ; app+$B8D
    beq.s hint_4702
hint_46f6:
; --- unverified ---
    bra.s hint_472e
hint_46f8:
; --- unverified ---
    bsr.w call_replymsg
hint_46fc:
; --- unverified ---
    bne.s hint_4702
hint_46fe:
; --- unverified ---
    move.l a2,d7
    bra.s hint_476c
hint_4702:
; --- unverified ---
    addq.w #1,d5
    beq.s hint_46f8
hint_4706:
; --- unverified ---
    bsr.s hint_46dc
hint_4708:
; --- unverified ---
    cmp.b (a2),d4
    bne.s hint_4702
hint_470c:
; --- unverified ---
    move.l a2,d7
    tst.b d3
    beq.s hint_476c
hint_4712:
    dc.b    $20,$4b,$10,$03
hint_4716:
; --- unverified ---
    jsr dat_46de
hint_471c:
; --- unverified ---
    beq.s hint_472a
hint_471e:
; --- unverified ---
    move.b (a2),d1
    cmp.b (a0)+,d1
    bne.s hint_472a
hint_4724:
; --- unverified ---
    subq.b #1,d0
    bne.s hint_4716
hint_4728:
; --- unverified ---
    bra.s hint_476c
hint_472a:
; --- unverified ---
    movea.l d7,a2
    bra.s hint_4702
hint_472e:
; --- unverified ---
    bra.s hint_473a
hint_4730:
; --- unverified ---
    bsr.w call_replymsg
hint_4734:
; --- unverified ---
    bne.s hint_473a
hint_4736:
; --- unverified ---
    move.l a2,d7
    bra.s hint_476c
hint_473a:
; --- unverified ---
    addq.w #1,d5
    beq.s hint_4730
hint_473e:
; --- unverified ---
    bsr.s hint_46dc
hint_4740:
; --- unverified ---
    move.b (a2),d1
    bsr.w sub_772e
hint_4746:
; --- unverified ---
    cmp.b d1,d4
    bne.s hint_473a
hint_474a:
; --- unverified ---
    move.l a2,d7
    tst.b d3
    beq.s hint_476c
hint_4750:
    dc.b    $20,$4b,$10,$03
hint_4754:
; --- unverified ---
    bsr.s dat_46de
hint_4756:
; --- unverified ---
    beq.s hint_4768
hint_4758:
; --- unverified ---
    move.b (a2),d1
    bsr.w sub_772e
hint_475e:
; --- unverified ---
    cmp.b (a0)+,d1
    bne.s hint_4768
hint_4762:
; --- unverified ---
    subq.b #1,d0
    bne.s hint_4754
hint_4766:
; --- unverified ---
    bra.s hint_476c
hint_4768:
; --- unverified ---
    movea.l d7,a2
    bra.s hint_473a
hint_476c:
    dc.b    $20,$6e,$00,$de,$21,$47,$00,$38
hint_4774:
; --- unverified ---
    bsr.w hint_0544
hint_4778:
; --- unverified ---
    bra.w sub_5ede
hint_477c:
; --- unverified ---
    bra.w hint_0544
hint_4780:
; --- unverified ---
    cmpi.b #$54,(a3)+
    bne.s hint_477c
hint_4786:
; --- unverified ---
    bsr.w hint_68d8
hint_478a:
; --- unverified ---
    beq.s hint_477c
hint_478c:
; --- unverified ---
    movea.l a2,a0
    tst.b 2957(a6) ; app+$B8D
    bne.s hint_47c6
hint_4794:
; --- unverified ---
    move.b (a0)+,d1
    cmp.b #$a,d1
    beq.s hint_4786
hint_479c:
; --- unverified ---
    cmp.b (a3),d1
    bne.s hint_4794
hint_47a0:
    dc.b    $48,$e7,$10,$90,$52,$8b
hint_47a6:
; --- unverified ---
    subq.w #1,d3
    beq.s hint_47b4
hint_47aa:
; --- unverified ---
    cmpm.b (a0)+,(a3)+
    beq.s hint_47a6
hint_47ae:
; --- unverified ---
    movem.l (sp)+,d3/a0/a3
    bra.s hint_4794
hint_47b4:
; --- unverified ---
    movem.l (sp)+,d3/a0/a3
    movea.l 222(a6),a3 ; app+$DE
    move.l a2,56(a3)
    move.w d4,54(a3)
    bra.s hint_4774
hint_47c6:
; --- unverified ---
    move.b (a0)+,d1
    cmp.b #$a,d1
    beq.s hint_4786
hint_47ce:
; --- unverified ---
    bsr.w sub_772e
hint_47d2:
; --- unverified ---
    cmp.b (a3),d1
    bne.s hint_47c6
hint_47d6:
    dc.b    $48,$e7,$10,$90,$52,$8b
hint_47dc:
; --- unverified ---
    subq.w #1,d3
    beq.s hint_47b4
hint_47e0:
; --- unverified ---
    move.b (a0)+,d1
    bsr.w sub_772e
hint_47e6:
; --- unverified ---
    cmp.b (a3)+,d1
    beq.s hint_47dc
hint_47ea:
; --- unverified ---
    movem.l (sp)+,d3/a0/a3
    bra.s hint_47c6
hint_47f0:
; --- unverified ---
    move.l a2,d7
    bra.w hint_476c
hint_47f6:
; --- unverified ---
    move.l a2,d0
    btst #0,d0
    beq.s hint_4802
hint_47fe:
; --- unverified ---
    bsr.w hint_46dc
hint_4802:
; --- unverified ---
    movea.l a2,a1
    lea 9(a2),a2
    bsr.w hint_46dc
hint_480c:
; --- unverified ---
    exg
    suba.l a2,a1
    cmpa.l #$a,a1
    beq.s hint_4820
hint_4818:
; --- unverified ---
    lea 9(a2),a2
    bsr.w hint_46dc
hint_4820:
; --- unverified ---
    bsr.w call_replymsg
hint_4824:
; --- unverified ---
    beq.s hint_47f0
hint_4826:
; --- unverified ---
    movem.l a4-a5,-(sp)
    movea.l a2,a5
    movem.l d6/a2,-(sp)
    bsr.w sub_1c78
hint_4834:
; --- unverified ---
    move.l (sp)+,d6
    moveq #0,d0
    move.b 2956(a6),d0 ; app+$B8C
    subq.b #1,d0
    lea 2472(a6),a1 ; app+$9A8
    lea 2960(a6),a0 ; app+$B90
    move.b (a0)+,d2
    tst.b 2957(a6) ; app+$B8D
    bne.s hint_4888
hint_484e:
; --- unverified ---
    move.b (a1)+,d1
    cmp.b d1,d2
    beq.s hint_485c
hint_4854:
; --- unverified ---
    cmp.b #$a,d1
    bne.s hint_484e
hint_485a:
; --- unverified ---
    bra.s hint_4872
hint_485c:
; --- unverified ---
    tst.b d0
    beq.s hint_4880
hint_4860:
    dc.b    $48,$e7,$80,$c0,$53,$40
hint_4866:
; --- unverified ---
    cmpm.b (a0)+,(a1)+
    dbne d0,hint_4866
hint_486c:
; --- unverified ---
    movem.l (sp)+,d0/a0-a1
    beq.s hint_4880
hint_4872:
; --- unverified ---
    movem.l (sp)+,a2/a4-a5
    bsr.w hint_46dc
hint_487a:
; --- unverified ---
    bsr.w hint_46dc
hint_487e:
; --- unverified ---
    bra.s hint_4802
hint_4880:
; --- unverified ---
    move.l (sp)+,d7
    addq.l #8,sp
    bra.w hint_476c
hint_4888:
; --- unverified ---
    move.b (a1)+,d1
    bsr.w sub_772e
hint_488e:
; --- unverified ---
    cmp.b d1,d2
    beq.s hint_489a
hint_4892:
; --- unverified ---
    cmp.b #$a,d1
    bne.s hint_4888
hint_4898:
; --- unverified ---
    bra.s hint_4872
hint_489a:
; --- unverified ---
    tst.b d0
    beq.s hint_4880
hint_489e:
    dc.b    $48,$e7,$80,$c0,$53,$40
hint_48a4:
; --- unverified ---
    move.b (a1)+,d1
    bsr.w sub_772e
hint_48aa:
; --- unverified ---
    cmp.b (a0)+,d1
    dbne d0,hint_48a4
hint_48b0:
; --- unverified ---
    bra.s hint_486c
hint_48b2:
; --- unverified ---
    lea 15542(pc),a0
    moveq #4,d3
    bsr.w sub_1a7e
hint_48bc:
; --- unverified ---
    bsr.w sub_59c0
hint_48c0:
; --- unverified ---
    bne.w sub_5d9c
hint_48c4:
; --- unverified ---
    tst.b (a4)
    beq.w sub_5d9c
hint_48ca:
    dc.b    $41,$ee,$0a,$d4,$74,$00
hint_48d0:
; --- unverified ---
    move.b (a0)+,d1
    beq.s hint_48f2
hint_48d4:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_48d0
hint_48da:
; --- unverified ---
    movea.l a0,a4
    move.l a0,-(sp)
    bsr.w hint_6b5c
hint_48e2:
; --- unverified ---
    movea.l (sp)+,a0
    beq.s hint_48f0
hint_48e6:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_48ee:
; --- unverified ---
    bra.s hint_48c0
hint_48f0:
    dc.b    $42,$20
hint_48f2:
; --- unverified ---
    bsr.s hint_4922
hint_48f4:
; --- unverified ---
    bne.s hint_490e
hint_48f6:
; --- unverified ---
    move.l a3,2016(a6) ; app+$7E0
    move.l a3,1616(a6) ; app+$650
    move.l a3,1690(a6) ; app+$69A
    adda.l d4,a3
    subq.l #1,a3
    move.l a3,2020(a6) ; app+$7E4
    bra.w sub_5ede
hint_490e:
; --- unverified ---
    rts
hint_4910:
; --- unverified ---
    moveq #4,d3
    bsr.w sub_1a7e
hint_4916:
; --- unverified ---
    bsr.w sub_59c0
hint_491a:
; --- unverified ---
    bne.s sub_4976
hint_491c:
; --- unverified ---
    tst.b (a4)
    beq.s sub_4976
hint_4920:
    dc.b    $74,$00
hint_4922:
; --- unverified ---
    move.l d2,-(sp)
    bsr.w sub_5d9c
    dc.b    $4b,$ee,$0a,$d4,$24,$1f
sub_492e:
    move.l d2,-(sp)
    bsr.w loc_73e2
loc_4934:
    movea.l (sp)+,a0
    bne.s loc_4966
loc_4938:
    move.l a0,-(sp)
    bsr.w call_seek
loc_493e:
    move.l (sp)+,d0
    bne.s loc_4954
loc_4942:
    move.l d4,d0
    addq.l #1,d0
    bsr.w alloc_memory_8160
loc_494a:
    beq.s loc_4964
loc_494c:
    move.b #$a,0(a0,d4.l)
    move.l a0,d0
loc_4954:
    movea.l d0,a3
    movea.l d0,a0
    bsr.w call_read
loc_495c:
    bsr.w call_close
loc_4960:
    moveq #0,d0
    rts
loc_4964:
    moveq #103,d0
loc_4966:
    move.w d0,-(sp)
    bsr.w call_close
loc_496c:
    move.w (sp)+,d0
    bsr.w amigados_error_12345
loc_4972:
    moveq #-1,d0
    rts
sub_4976:
; --- unverified ---
    bsr.w sub_5d9c
hint_497a:
; --- unverified ---
    moveq #-1,d0
    rts
hint_497e:
; --- unverified ---
    moveq #16,d3
    lea 15684(pc),a0
    bsr.w sub_1a7e
hint_4988:
; --- unverified ---
    lea 16133(pc),a0
    tst.b 1413(a6) ; app+$585
    bsr.w hint_4b9c
hint_4994:
; --- unverified ---
    beq.w hint_499c
hint_4998:
    dc.b    $5a,$ee,$05,$85
hint_499c:
; --- unverified ---
    lea str_886c(pc),a0
    bsr.w sub_6a6a
hint_49a4:
; --- unverified ---
    moveq #78,d1
    tst.b 1412(a6) ; app+$584
    beq.s hint_49b6
hint_49ac:
; --- unverified ---
    moveq #68,d1
    tst.b 1412(a6) ; app+$584
    bpl.s hint_49b6
hint_49b4:
    dc.b    $72,$48
hint_49b6:
; --- unverified ---
    bsr.w sub_58ba
hint_49ba:
; --- unverified ---
    subq.w #1,10(a3)
    bsr.w hint_4be8
hint_49c2:
; --- unverified ---
    bsr.w call_replymsg_412c
hint_49c6:
; --- unverified ---
    bmi.s hint_49c2
hint_49c8:
; --- unverified ---
    cmp.b #$1b,d1
    beq.w hint_4b98
hint_49d0:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_4a00
hint_49d6:
; --- unverified ---
    andi.b #$df,d1
    moveq #1,d0
    cmp.b #$44,d1
    beq.s hint_49f2
hint_49e2:
; --- unverified ---
    moveq #0,d0
    cmp.b #$4e,d1
    beq.s hint_49f2
hint_49ea:
; --- unverified ---
    moveq #-1,d0
    cmp.b #$48,d1
    bne.s hint_49c2
hint_49f2:
; --- unverified ---
    move.b d0,1412(a6) ; app+$584
    bsr.w sub_58ba
hint_49fa:
; --- unverified ---
    bsr.w sub_19d4
hint_49fe:
; --- unverified ---
    bra.s hint_4a08
hint_4a00:
; --- unverified ---
    bsr.w hint_4be8
hint_4a04:
; --- unverified ---
    bsr.w sub_19d4
hint_4a08:
; --- unverified ---
    lea 16033(pc),a0
    tst.b 1414(a6) ; app+$586
    bsr.w hint_4b9c
hint_4a14:
; --- unverified ---
    beq.w hint_4a1c
hint_4a18:
    dc.b    $5a,$ee,$05,$86
hint_4a1c:
; --- unverified ---
    lea 15575(pc),a0
    tst.b 230(a6) ; app+$E6
    bsr.w hint_4b9c
hint_4a28:
; --- unverified ---
    beq.w hint_4a30
hint_4a2c:
    dc.b    $5a,$ee,$00,$e6
hint_4a30:
; --- unverified ---
    lea str_8726(pc),a0
    bsr.w sub_6a6a
hint_4a38:
; --- unverified ---
    bsr.w sub_19d4
hint_4a3c:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    move.b #$5c,(a4)+
    moveq #0,d1
    move.w 2070(a6),d1 ; app+$816
    lea loc_1b24(pc),a2
    bsr.w sub_6ae0
hint_4a52:
; --- unverified ---
    clr.b (a4)
    lea 2772(a6),a4 ; app+$AD4
    bsr.w hint_4f1c
hint_4a5c:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_4a64:
; --- unverified ---
    bne.w hint_4b98
hint_4a68:
; --- unverified ---
    bsr.w hint_6b5c
hint_4a6c:
; --- unverified ---
    bne.s hint_4a5c
hint_4a6e:
; --- unverified ---
    cmp.l #$8,d2
    bcs.s hint_4a5c
hint_4a76:
; --- unverified ---
    cmp.l #$78,d2
    bcc.s hint_4a5c
hint_4a7e:
; --- unverified ---
    move.w d2,2070(a6) ; app+$816
    bsr.w sub_19d4
hint_4a86:
; --- unverified ---
    lea str_86d2(pc),a0
    tst.b 328(a6) ; app+$148
    bsr.w hint_4b9c
hint_4a92:
; --- unverified ---
    beq.s hint_4a98
hint_4a94:
    dc.b    $5a,$ee,$01,$48
hint_4a98:
; --- unverified ---
    lea 15923(pc),a0
    tst.b 1415(a6) ; app+$587
    bsr.w hint_4b9c
hint_4aa4:
; --- unverified ---
    beq.s hint_4aaa
hint_4aa6:
    dc.b    $5a,$ee,$05,$87
hint_4aaa:
; --- unverified ---
    lea 15792(pc),a0
    move.b dat_0027(pc),d0
    bsr.w hint_4b9c
hint_4ab6:
; --- unverified ---
    beq.s hint_4abe
hint_4ab8:
    dc.b    $5a,$f9
    dc.l    dat_0027
hint_4abe:
; --- unverified ---
    lea 15703(pc),a0
    bsr.w sub_6a6a
hint_4ac6:
; --- unverified ---
    bsr.w sub_19d4
hint_4aca:
    dc.b    $49,$ee,$0a,$d4,$41,$ee,$08,$84,$22,$4c
hint_4ad4:
; --- unverified ---
    move.b (a0)+,(a1)+
    bne.s hint_4ad4
hint_4ad8:
; --- unverified ---
    bsr.w hint_4f1c
hint_4adc:
; --- unverified ---
    bsr.w loc_59c2
hint_4ae0:
; --- unverified ---
    bne.w hint_4b98
hint_4ae4:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    tst.b (a4)
    beq.s hint_4b0e
hint_4aec:
    dc.b    $43,$ee,$08,$84,$20,$4c
hint_4af2:
; --- unverified ---
    cmpm.b (a0)+,(a1)+
    bne.s hint_4afe
hint_4af6:
; --- unverified ---
    tst.b -1(a0)
    bne.s hint_4af2
hint_4afc:
; --- unverified ---
    bra.s hint_4b16
hint_4afe:
; --- unverified ---
    lea 2772(a6),a0 ; app+$AD4
    bsr.w call_ioerr_74ec
hint_4b06:
; --- unverified ---
    beq.s hint_4b16
hint_4b08:
; --- unverified ---
    bsr.w sub_5e54
hint_4b0c:
; --- unverified ---
    bra.s hint_4adc
hint_4b0e:
; --- unverified ---
    bsr.w call_close_752c
hint_4b12:
    dc.b    $42,$2e,$08,$84
hint_4b16:
; --- unverified ---
    bsr.w sub_19d4
hint_4b1a:
; --- unverified ---
    bsr.w sub_19d4
hint_4b1e:
; --- unverified ---
    lea 15540(pc),a0
    bsr.w sub_6a6a
hint_4b26:
; --- unverified ---
    bsr.w hint_4be8
hint_4b2a:
; --- unverified ---
    bsr.w sub_4120
hint_4b2e:
; --- unverified ---
    bmi.s hint_4b2a
hint_4b30:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$59,d1
    bne.s hint_4b98
hint_4b3a:
; --- unverified ---
    lea str_4cb3(pc),a0
    bsr.w sub_73b6
hint_4b42:
; --- unverified ---
    bne.s hint_4b8e
hint_4b44:
    dc.b    $41,$fa,$b4,$de,$50,$d8,$10,$ee,$01,$48,$10,$ee,$00,$e6,$52,$88
    dc.b    $30,$ee,$08,$16,$41,$fa,$b5,$18,$10,$ee,$05,$84,$10,$ee,$05,$85
    dc.b    $10,$ee,$05,$86,$10,$ee,$05,$87,$30,$ee,$00,$f0,$41,$fa,$b4,$c0
    dc.b    $43,$ee,$08,$84
hint_4b78:
; --- unverified ---
    move.b (a1)+,(a0)+
    bne.s hint_4b78
hint_4b7c:
; --- unverified ---
    lea dat_0024(pc),a0
    moveq #84,d4
    bsr.w call_ioerr_7442
hint_4b86:
; --- unverified ---
    bne.s hint_4b8e
hint_4b88:
; --- unverified ---
    bsr.w call_close
hint_4b8c:
; --- unverified ---
    bra.s hint_4b98
hint_4b8e:
; --- unverified ---
    move.l d0,-(sp)
    bsr.s hint_4b98
hint_4b92:
; --- unverified ---
    move.l (sp)+,d0
    bra.w amigados_error_12345
hint_4b98:
; --- unverified ---
    bra.w sub_5d9c
hint_4b9c:
; --- unverified ---
    sne -(sp)
    bsr.w sub_6a6a
hint_4ba2:
; --- unverified ---
    moveq #78,d1
    tst.b (sp)+
    beq.s hint_4baa
hint_4ba8:
    dc.b    $72,$59
hint_4baa:
; --- unverified ---
    bsr.w sub_58ba
hint_4bae:
; --- unverified ---
    subq.w #1,10(a3)
    bsr.s hint_4be8
hint_4bb4:
; --- unverified ---
    bsr.w sub_4120
hint_4bb8:
; --- unverified ---
    bmi.s hint_4bb4
hint_4bba:
; --- unverified ---
    cmp.b #$1b,d1
    beq.s hint_4c04
hint_4bc0:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_4bfc
hint_4bc6:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$59,d1
    beq.s hint_4bd6
hint_4bd0:
; --- unverified ---
    cmp.b #$4e,d1
    bne.s hint_4bb4
hint_4bd6:
; --- unverified ---
    move.w d1,-(sp)
    bsr.w sub_58ba
hint_4bdc:
; --- unverified ---
    bsr.w sub_19d4
hint_4be0:
; --- unverified ---
    move.w (sp)+,d1
    cmp.b #$4f,d1
    rts
hint_4be8:
; --- unverified ---
    moveq #0,d3
    movem.w 10(a3),d2-d3
    divu.w app_rectfill_ymax(a6),d3
    bsr.w sub_576e
hint_4bf8:
; --- unverified ---
    moveq #0,d1
    rts
hint_4bfc:
; --- unverified ---
    bsr.s hint_4be8
hint_4bfe:
; --- unverified ---
    bsr.w sub_19d4
hint_4c02:
; --- unverified ---
    bra.s hint_4bf8
hint_4c04:
; --- unverified ---
    addq.l #4,sp
    bra.w sub_5d9c
env_devpac_monam_prefs:
    st 1425(a6) ; app+$591
    tst.b 354(a6) ; app+$162
    beq.s loc_4c26
loc_4c14:
    tst.b dat_0024
    bne.s loc_4c62
loc_4c1c:
    move.b 327(a6),dat_0027 ; app+$147
    bra.s loc_4c62
loc_4c26:
    move.b 327(a6),dat_0027 ; app+$147
    lea str_4cb3(pc),a5
    bsr.w loc_73e2
loc_4c36:
    beq.s loc_4c4e
loc_4c38:
    movea.l dat_8956,a0
    moveq #-1,d0
    move.l d0,184(a0)
    lea str_4ca8(pc),a5
    bsr.w loc_73e2
loc_4c4c:
    bne.s loc_4c62
loc_4c4e:
    lea dat_0024(pc),a0
    moveq #84,d4
    bsr.w call_read
loc_4c58:
    bsr.w call_close
loc_4c5c:
    move.b dat_0024(pc),d0
    beq.s loc_4ca6
loc_4c62:
    movea.l dat_8956,a0
    clr.l 184(a0)
    lea pcref_0025(pc),a0
    move.b (a0)+,328(a6) ; app+$148
    move.b (a0)+,230(a6) ; app+$E6
    tst.b (a0)+
    move.w (a0)+,2070(a6) ; app+$816
    lea pcref_0072(pc),a0
    move.b (a0)+,1412(a6) ; app+$584
    move.b (a0)+,1413(a6) ; app+$585
    move.b (a0)+,1414(a6) ; app+$586
    move.b (a0)+,1415(a6) ; app+$587
    move.w (a0)+,240(a6) ; app+$F0
    tst.b dat_002a
    bne.s loc_4ca6
loc_4c9e:
    move.b #$8,dat_002a
loc_4ca6:
    rts
str_4ca8:
    dc.b    "ENV:Devpac/"
str_4cb3:
    dc.b    $4d,$6f,$6e,$41,$6d
sub_4cb8:
    dc.b    ".prefs"
hint_4cbe:
    dc.b    $00,$00
hint_4cc0:
    dc.b    $61,$00
hint_4cc4:
; --- unverified ---
    bne.s hint_4cf0
hint_4cc6:
; --- unverified ---
    tst.b (a4)
    beq.s hint_4cf0
hint_4cca:
; --- unverified ---
    bsr.w sub_6b70
hint_4cce:
; --- unverified ---
    bne.s hint_4cf2
hint_4cd0:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_4cf2
hint_4cd6:
; --- unverified ---
    move.l d2,d5
    bsr.w sub_6b70
hint_4cdc:
; --- unverified ---
    bne.s hint_4cf2
hint_4cde:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_4cf2
hint_4ce4:
; --- unverified ---
    move.l d2,d6
    bsr.w sub_6b70
hint_4cea:
; --- unverified ---
    bne.s hint_4cf2
hint_4cec:
; --- unverified ---
    tst.b d1
    bne.s hint_4cf2
hint_4cf0:
; --- unverified ---
    rts
hint_4cf2:
; --- unverified ---
    bsr.w sub_5e54
hint_4cf6:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bra.s hint_4cc0
hint_4cfc:
; --- unverified ---
    moveq #4,d3
    lea 14906(pc),a0
    bsr.w sub_1a7e
hint_4d06:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.s hint_4cc0
hint_4d0c:
; --- unverified ---
    bne.s sub_4d36
hint_4d0e:
; --- unverified ---
    cmp.l d5,d6
    blt.s hint_4d06
hint_4d12:
; --- unverified ---
    movea.l d2,a2
    movea.l d6,a1
    movea.l d5,a0
    sub.l a0,d6
    beq.s sub_4d36
hint_4d1c:
; --- unverified ---
    addq.l #1,d6
    cmpa.l a0,a2
    bcc.s hint_4d2a
hint_4d22:
; --- unverified ---
    move.b (a0)+,(a2)+
    subq.l #1,d6
    bne.s hint_4d22
hint_4d28:
; --- unverified ---
    bra.s sub_4d36
hint_4d2a:
    dc.b    $52,$89,$45,$f2,$68,$00
hint_4d30:
    dc.b    $15
hint_4d31:
    dc.b    $21
    dc.b    $fa
sub_4d36:
; --- unverified ---
    bra.w sub_5d9c
hint_4d3a:
; --- unverified ---
    moveq #4,d3
    lea str_874c(pc),a0
    bsr.w sub_1a7e
hint_4d44:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w hint_4cc0
hint_4d4c:
; --- unverified ---
    bne.s sub_4d36
hint_4d4e:
; --- unverified ---
    sub.l d5,d6
    blt.s hint_4d44
hint_4d52:
    dc.b    $20,$45
hint_4d54:
; --- unverified ---
    move.b d2,(a0)+
    subq.l #1,d6
    bcc.s hint_4d54
hint_4d5a:
; --- unverified ---
    bra.s sub_4d36
hint_4d5c:
; --- unverified ---
    moveq #4,d3
    lea str_8760(pc),a0
    bsr.w sub_1a7e
hint_4d66:
; --- unverified ---
    bsr.w sub_59c0
hint_4d6a:
; --- unverified ---
    bne.w hint_4df8
hint_4d6e:
; --- unverified ---
    tst.b (a4)
    beq.w hint_4df8
hint_4d74:
; --- unverified ---
    bsr.w sub_5d9c
hint_4d78:
; --- unverified ---
    lea 2772(a6),a0 ; app+$AD4
    tst.b (a0)
    beq.s hint_4df6
hint_4d80:
; --- unverified ---
    move.l a0,d1
    moveq #-2,d2
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr -84(a6) ; app-$54; unresolved_indirect_hint:disp
hint_4d8e:
; --- unverified ---
    movea.l (sp)+,a6
    move.l d0,d4
    beq.w loc_1af8
hint_4d96:
; --- unverified ---
    lea 2480(a6),a0 ; app+$9B0
    move.l a0,d2
    move.l d4,d1
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr -102(a6) ; app-$66; unresolved_indirect_hint:disp
hint_4da8:
; --- unverified ---
    movea.l (sp)+,a6
    tst.l d0
    bne.s hint_4dce
hint_4dae:
; --- unverified ---
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr -132(a6) ; app-$84; unresolved_indirect_hint:disp
hint_4db8:
    dc.b    $2c,$5f
hint_4dba:
; --- unverified ---
    bsr.w amigados_error_12345
hint_4dbe:
; --- unverified ---
    move.l d4,d1
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr -90(a6) ; app-$5A; unresolved_indirect_hint:disp
hint_4dca:
; --- unverified ---
    movea.l (sp)+,a6
    rts
hint_4dce:
; --- unverified ---
    move.l #$d4,d0
    tst.l 2484(a6) ; app+$9B4
    ble.s hint_4dba
hint_4dda:
; --- unverified ---
    move.l d4,d1
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr -126(a6) ; app-$7E; unresolved_indirect_hint:disp
hint_4de6:
; --- unverified ---
    movea.l (sp)+,a6
    move.l d0,d1
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr -90(a6) ; app-$5A; unresolved_indirect_hint:disp
hint_4df4:
    dc.b    $2c,$5f
hint_4df6:
; --- unverified ---
    rts
hint_4df8:
; --- unverified ---
    bra.w sub_5d9c
hint_4dfc:
; --- unverified ---
    moveq #7,d3
    lea str_877c(pc),a0
    bsr.w sub_1a7e
hint_4e06:
; --- unverified ---
    bsr.w loc_59c2
hint_4e0a:
; --- unverified ---
    bne.s hint_4e80
hint_4e0c:
; --- unverified ---
    tst.b (a4)
    beq.s hint_4e80
hint_4e10:
; --- unverified ---
    bsr.w sub_19d0
hint_4e14:
; --- unverified ---
    lea 14716(pc),a0
    bsr.w sub_6a6a
hint_4e1c:
; --- unverified ---
    bsr.w sub_19d4
hint_4e20:
; --- unverified ---
    clr.b 2832(a6) ; app+$B10
    moveq #0,d4
    bra.s hint_4e2c
hint_4e28:
; --- unverified ---
    bsr.w sub_5e54
hint_4e2c:
; --- unverified ---
    lea 2832(a6),a4 ; app+$B10
    bsr.w loc_59c2
hint_4e34:
; --- unverified ---
    bne.s hint_4e80
hint_4e36:
; --- unverified ---
    bsr.w sub_6b70
hint_4e3a:
; --- unverified ---
    bne.s hint_4e28
hint_4e3c:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_4e28
hint_4e42:
; --- unverified ---
    move.l d2,d5
    bsr.w sub_6b70
hint_4e48:
; --- unverified ---
    bne.s hint_4e28
hint_4e4a:
; --- unverified ---
    tst.b d1
    bne.s hint_4e28
hint_4e4e:
; --- unverified ---
    move.l d2,d4
    sub.l d5,d4
    blt.s hint_4e28
hint_4e54:
; --- unverified ---
    addq.l #1,d4
    lea 2772(a6),a0 ; app+$AD4
    bsr.w sub_73b6
hint_4e5e:
; --- unverified ---
    bne.s hint_4e72
hint_4e60:
; --- unverified ---
    movea.l d5,a0
    bsr.w call_ioerr_7442
hint_4e66:
; --- unverified ---
    bne.s hint_4e72
hint_4e68:
; --- unverified ---
    bsr.w call_close
hint_4e6c:
; --- unverified ---
    bsr.w call_activatewindow
hint_4e70:
; --- unverified ---
    bra.s hint_4e80
hint_4e72:
; --- unverified ---
    bsr.w call_activatewindow
hint_4e76:
; --- unverified ---
    move.w d0,-(sp)
    bsr.s hint_4e80
hint_4e7a:
; --- unverified ---
    move.w (sp)+,d0
    bra.w amigados_error_12345
hint_4e80:
; --- unverified ---
    bra.w sub_5d9c
hint_4e84:
; --- unverified ---
    moveq #7,d3
    bsr.w esc_to_abort
hint_4e8a:
; --- unverified ---
    lea 14616(pc),a0
    bsr.w sub_6a6a
hint_4e92:
; --- unverified ---
    bsr.w hint_4be8
hint_4e96:
; --- unverified ---
    bsr.w call_replymsg_412c
hint_4e9a:
; --- unverified ---
    cmp.b #$1b,d1
    beq.w hint_4f18
hint_4ea2:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$47,d1
    beq.s hint_4eb2
hint_4eac:
; --- unverified ---
    cmp.b #$49,d1
    bne.s hint_4e96
hint_4eb2:
; --- unverified ---
    move.w d1,-(sp)
    bsr.w sub_58ba
hint_4eb8:
; --- unverified ---
    bsr.w sub_19d0
hint_4ebc:
; --- unverified ---
    move.w (sp)+,d1
    cmp.b #$47,d1
    beq.s hint_4f12
hint_4ec4:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    move.l 404(a6),d1 ; app+$194
    beq.s hint_4ed2
hint_4ece:
; --- unverified ---
    bsr.w hint_1bbe
hint_4ed2:
; --- unverified ---
    clr.b (a4)
    lea 2772(a6),a4 ; app+$AD4
    bsr.s hint_4f1c
hint_4eda:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_4ee2:
; --- unverified ---
    bne.s hint_4f18
hint_4ee4:
; --- unverified ---
    tst.b (a4)
    beq.s hint_4f18
hint_4ee8:
; --- unverified ---
    bsr.w hint_6b5c
hint_4eec:
; --- unverified ---
    bne.s hint_4eda
hint_4eee:
; --- unverified ---
    move.l d2,404(a6) ; app+$194
    moveq #3,d7
    bsr.w sub_19d0
hint_4ef8:
; --- unverified ---
    move.w d7,-(sp)
    bsr.s hint_4f18
hint_4efc:
; --- unverified ---
    move.w (sp)+,d3
    bsr.w hint_44a2
hint_4f02:
; --- unverified ---
    move.b d3,330(a6) ; app+$14A
    bset #7,90(a6) ; app+$5A
    st d3
    bra.w loc_1926
hint_4f12:
; --- unverified ---
    bsr.s hint_4f18
hint_4f14:
; --- unverified ---
    bra.w hint_44c6
hint_4f18:
; --- unverified ---
    bra.w sub_5d9c
hint_4f1c:
    dc.b    $28,$0c
hint_4f1e:
; --- unverified ---
    tst.b (a4)+
    bne.s hint_4f1e
hint_4f22:
; --- unverified ---
    exg
    sub.l a4,d4
    subq.w #1,d4
    rts
hint_4f2a:
; --- unverified ---
    pea pcref_0554(pc)
    lea str_87b9(pc),a2
    bsr.w hint_5eac
hint_4f36:
; --- unverified ---
    moveq #22,d1
    bsr.w sub_6a5a
hint_4f3c:
    dc.b    $7e,$07,$49,$ee,$01,$98
hint_4f42:
; --- unverified ---
    move.w 6(a4),d1
    beq.s hint_4f9c
hint_4f48:
; --- unverified ---
    move.l (a4),d2
    bsr.w hint_6a9a
hint_4f4e:
; --- unverified ---
    bsr.w sub_6a82
hint_4f52:
; --- unverified ---
    moveq #-1,d2
    moveq #22,d2
    move.l (a4),d0
    bsr.w hint_7ef8
hint_4f5c:
; --- unverified ---
    beq.s hint_4f62
hint_4f5e:
; --- unverified ---
    bsr.w sub_7bd8
hint_4f62:
; --- unverified ---
    addq.b #1,d2
    bsr.w sub_6a76
hint_4f68:
; --- unverified ---
    movea.l (a4),a2
    bsr.w sub_69a6
hint_4f6e:
; --- unverified ---
    cmpi.w #$4,6(a4)
    bne.s hint_4f94
hint_4f76:
; --- unverified ---
    bsr.w hint_5094
hint_4f7a:
; --- unverified ---
    moveq #9,d2
    bsr.w sub_6a76
hint_4f80:
; --- unverified ---
    moveq #63,d1
    bsr.w sub_58ba
hint_4f86:
    dc.b    $45,$ec,$00,$0c
hint_4f8a:
; --- unverified ---
    move.b (a2)+,d1
    beq.s hint_4f94
hint_4f8e:
; --- unverified ---
    bsr.w sub_58ba
hint_4f92:
; --- unverified ---
    bra.s hint_4f8a
hint_4f94:
; --- unverified ---
    bsr.w hint_5094
hint_4f98:
; --- unverified ---
    bsr.w hint_5094
hint_4f9c:
; --- unverified ---
    lea 72(a4),a4
    dbf d7,hint_4f42
hint_4fa4:
; --- unverified ---
    moveq #41,d1
    bsr.w sub_6a5a
hint_4faa:
; --- unverified ---
    moveq #38,d1
    move.b 308(a6),d0 ; app+$134
    beq.s hint_4fba
hint_4fb2:
; --- unverified ---
    moveq #37,d1
    tst.b d0
    bpl.s hint_4fba
hint_4fb8:
    dc.b    $72,$27
hint_4fba:
; --- unverified ---
    bsr.w sub_6a5a
hint_4fbe:
; --- unverified ---
    bsr.w hint_5094
hint_4fc2:
; --- unverified ---
    moveq #42,d1
    bsr.w sub_6a5a
hint_4fc8:
; --- unverified ---
    bsr.w hint_5094
hint_4fcc:
; --- unverified ---
    tst.b 308(a6) ; app+$134
    beq.s hint_5012
hint_4fd2:
    dc.b    $24,$7a,$39,$22
hint_4fd6:
; --- unverified ---
    adda.l a2,a2
    adda.l a2,a2
    moveq #4,d2
    add.l a2,d2
    move.l d2,-(sp)
    bsr.w hint_6a9a
hint_4fe4:
; --- unverified ---
    moveq #45,d1
    bsr.w sub_58ba
hint_4fea:
; --- unverified ---
    move.l (sp),d2
    add.l -4(a2),d2
    subq.l #8,d2
    bsr.w hint_6a9a
hint_4ff6:
; --- unverified ---
    bsr.w sub_6a82
hint_4ffa:
; --- unverified ---
    move.l (sp)+,d0
    bsr.w hint_7ef8
hint_5000:
; --- unverified ---
    beq.s hint_5008
hint_5002:
; --- unverified ---
    moveq #32,d2
    bsr.w sub_7bd8
hint_5008:
; --- unverified ---
    bsr.w hint_5094
hint_500c:
; --- unverified ---
    movea.l (a2),a2
    move.l a2,d0
    bne.s hint_4fd6
hint_5012:
; --- unverified ---
    moveq #40,d1
    bsr.w sub_6a5a
hint_5018:
; --- unverified ---
    moveq #2,d1
    bsr.s hint_5034
hint_501c:
; --- unverified ---
    moveq #44,d1
    bsr.w sub_58ba
hint_5022:
; --- unverified ---
    moveq #4,d1
    bsr.s hint_5034
hint_5026:
; --- unverified ---
    moveq #44,d1
    bsr.w sub_58ba
hint_502c:
; --- unverified ---
    moveq #0,d1
    bsr.s hint_5034
hint_5030:
; --- unverified ---
    bsr.s hint_5094
hint_5032:
; --- unverified ---
    bra.s hint_504a
hint_5034:
; --- unverified ---
    bset #0,d1
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -216(a6) ; app-$D8; unresolved_indirect_hint:disp
hint_5042:
; --- unverified ---
    movea.l (sp)+,a6
    move.l d0,d1
    bra.w $6adc
hint_504a:
; --- unverified ---
    moveq #43,d1
    bsr.w sub_6a5a
hint_5050:
; --- unverified ---
    bsr.s hint_5094
hint_5052:
    dc.b    $20,$78,$00,$04,$24,$68,$01,$42
hint_505a:
; --- unverified ---
    tst.l (a2)
    beq.s hint_508e
hint_505e:
; --- unverified ---
    move.l a2,d2
    cmp.l #$40000,d2
    bcc.s hint_506a
hint_5068:
    dc.b    $74,$00
hint_506a:
; --- unverified ---
    bsr.w hint_6a9a
hint_506e:
; --- unverified ---
    moveq #45,d1
    bsr.w sub_58ba
hint_5074:
; --- unverified ---
    move.l 24(a2),d2
    bsr.w hint_6a9a
hint_507c:
; --- unverified ---
    bsr.w sub_6a82
hint_5080:
; --- unverified ---
    movea.l 10(a2),a0
    bsr.w sub_6a6a
hint_5088:
; --- unverified ---
    bsr.s hint_5094
hint_508a:
; --- unverified ---
    movea.l (a2),a2
    bra.s hint_505a
hint_508e:
; --- unverified ---
    bsr.s hint_50a4
hint_5090:
; --- unverified ---
    bra.w sub_5d9c
hint_5094:
; --- unverified ---
    bsr.w hint_6a94
hint_5098:
; --- unverified ---
    move.w 12(a3),d0
    cmp.w 8(a3),d0
    bge.s hint_50a4
hint_50a2:
; --- unverified ---
    rts
hint_50a4:
    dc.b    $48,$e7,$3f,$3c
hint_50a8:
; --- unverified ---
    bsr.w call_replymsg_412c
hint_50ac:
; --- unverified ---
    bmi.s hint_50ca
hint_50ae:
; --- unverified ---
    cmp.b #$1b,d1
    beq.s hint_50c2
hint_50b4:
; --- unverified ---
    bsr.w call_rectfill
hint_50b8:
; --- unverified ---
    movem.l (sp)+,d2-d7/a2-a5
    clr.l 10(a3)
    rts
hint_50c2:
; --- unverified ---
    movem.l (sp)+,d2-d7/a2-a5
    addq.l #4,sp
    bra.s hint_5090
hint_50ca:
; --- unverified ---
    move.l a3,-(sp)
    bsr.w hint_0720
hint_50d0:
; --- unverified ---
    movea.l (sp)+,a3
    bra.s hint_50a8
hint_50d4:
; --- unverified ---
    lea sub_87be(pc),a0
    moveq #10,d3
    bsr.w sub_1a7e
hint_50de:
; --- unverified ---
    clr.l 372(a6) ; app+$174
    bra.s hint_50e8
hint_50e4:
; --- unverified ---
    bsr.w sub_5e54
hint_50e8:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_50f0:
; --- unverified ---
    bne.w hint_52e8
hint_50f4:
; --- unverified ---
    tst.b (a4)
    beq.w hint_52e8
hint_50fa:
; --- unverified ---
    bsr.w sub_6b70
hint_50fe:
; --- unverified ---
    bne.s hint_50e4
hint_5100:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_50e4
hint_5106:
; --- unverified ---
    addq.l #1,d2
    andi.b #$fe,d2
    move.l d2,364(a6) ; app+$16C
    bsr.w sub_6b70
hint_5114:
; --- unverified ---
    bne.s hint_50e4
hint_5116:
; --- unverified ---
    cmp.l 364(a6),d2 ; app+$16C
    ble.s hint_50e4
hint_511c:
; --- unverified ---
    move.l d2,368(a6) ; app+$170
    movea.l d2,a2
    bsr.w call_typeofmem
hint_5126:
; --- unverified ---
    bne.s hint_50e4
hint_5128:
; --- unverified ---
    movea.l 364(a6),a2 ; app+$16C
    bsr.w call_typeofmem
hint_5130:
; --- unverified ---
    bne.s hint_50e4
hint_5132:
; --- unverified ---
    bsr.w sub_19d4
hint_5136:
; --- unverified ---
    moveq #24,d1
    bsr.w sub_6a5a
hint_513c:
; --- unverified ---
    bsr.w sub_19d4
hint_5140:
; --- unverified ---
    clr.b 2772(a6) ; app+$AD4
    moveq #0,d4
    bra.s hint_514c
hint_5148:
; --- unverified ---
    bsr.w sub_5e54
hint_514c:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_5154:
; --- unverified ---
    bne.w hint_52e8
hint_5158:
; --- unverified ---
    sf 355(a6) ; app+$163
    tst.b (a4)
    beq.s hint_51a6
hint_5160:
; --- unverified ---
    bsr.w sub_6b70
hint_5164:
; --- unverified ---
    bne.s hint_5148
hint_5166:
; --- unverified ---
    move.l d2,356(a6) ; app+$164
    clr.l 360(a6) ; app+$168
    tst.b d1
    beq.s hint_518c
hint_5172:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_5148
hint_5178:
; --- unverified ---
    bsr.w sub_6b70
hint_517c:
; --- unverified ---
    bne.s hint_5148
hint_517e:
; --- unverified ---
    tst.b d1
    bne.s hint_5148
hint_5182:
; --- unverified ---
    cmp.l 356(a6),d2 ; app+$164
    bcs.s hint_5148
hint_5188:
    dc.b    $2d,$42,$01,$68
hint_518c:
; --- unverified ---
    move.l 356(a6),d2 ; app+$164
    btst #0,d2
    bne.s hint_5148
hint_5196:
; --- unverified ---
    move.l d2,d0
    bsr.w sub_73a4
hint_519c:
; --- unverified ---
    bne.s hint_5148
hint_519e:
    dc.b    $52,$2e,$01,$63,$20,$42,$42,$90
hint_51a6:
; --- unverified ---
    bsr.w sub_19d4
hint_51aa:
; --- unverified ---
    moveq #23,d1
    bsr.w sub_6a5a
hint_51b0:
; --- unverified ---
    bsr.w sub_19d4
hint_51b4:
    dc.b    $4b,$ee,$0b,$10
hint_51b8:
; --- unverified ---
    moveq #0,d4
    clr.b 2772(a6) ; app+$AD4
    bra.s hint_51c4
hint_51c0:
; --- unverified ---
    bsr.w sub_5e54
hint_51c4:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_51cc:
; --- unverified ---
    bne.w hint_52e8
hint_51d0:
; --- unverified ---
    tst.b (a4)
    beq.s hint_5234
hint_51d4:
; --- unverified ---
    bsr.w sub_6b70
hint_51d8:
; --- unverified ---
    bne.s hint_51c0
hint_51da:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_51c0
hint_51e0:
; --- unverified ---
    move.l d2,(a5)
    bsr.w sub_6b70
hint_51e6:
; --- unverified ---
    bne.s hint_51c0
hint_51e8:
; --- unverified ---
    cmp.l (a5),d2
    ble.s hint_51c0
hint_51ec:
; --- unverified ---
    moveq #0,d0
    tst.b d1
    beq.s hint_5214
hint_51f2:
; --- unverified ---
    cmp.b #$2c,d1
    bne.s hint_51c0
hint_51f8:
; --- unverified ---
    move.b (a4)+,d1
    andi.b #$df,d1
    cmp.b #$42,d1
    beq.s hint_5214
hint_5204:
; --- unverified ---
    moveq #1,d0
    cmp.b #$57,d1
    beq.s hint_5214
hint_520c:
; --- unverified ---
    moveq #2,d0
    cmp.b #$4c,d1
    bne.s hint_51c0
hint_5214:
; --- unverified ---
    move.l (a5),d1
    addq.l #1,d1
    andi.b #$fe,d1
    move.l d1,(a5)+
    addq.l #1,d2
    andi.b #$fe,d2
    move.l d2,(a5)+
    move.w d0,(a5)+
    move.w #$4,10(a3)
    bsr.w loc_5836
hint_5232:
; --- unverified ---
    bra.s hint_51b8
hint_5234:
; --- unverified ---
    clr.l (a5)
    bsr.w sub_19d4
hint_523a:
; --- unverified ---
    moveq #25,d1
    bsr.w sub_6a5a
hint_5240:
; --- unverified ---
    bsr.w sub_19d4
hint_5244:
    dc.b    $42,$2e,$0a,$d4,$78,$00
hint_524a:
; --- unverified ---
    lea 2772(a6),a4 ; app+$AD4
    bsr.w loc_59c2
hint_5252:
; --- unverified ---
    bne.w hint_52e8
hint_5256:
; --- unverified ---
    tst.b (a4)
    beq.s hint_5270
hint_525a:
; --- unverified ---
    movea.l a4,a0
    bsr.w sub_73b6
hint_5260:
; --- unverified ---
    beq.s hint_5268
hint_5262:
; --- unverified ---
    bsr.w call_activatewindow
hint_5266:
; --- unverified ---
    bra.s hint_524a
hint_5268:
; --- unverified ---
    bsr.w call_activatewindow
hint_526c:
; --- unverified ---
    bsr.w sub_7484
hint_5270:
; --- unverified ---
    movea.l 364(a6),a5 ; app+$16C
    tst.b 355(a6) ; app+$163
    beq.s hint_52bc
hint_527a:
; --- unverified ---
    cmpa.l 368(a6),a5 ; app+$170
    bgt.s hint_52b4
hint_5280:
; --- unverified ---
    bsr.w hint_52fe
hint_5284:
; --- unverified ---
    bne.s hint_52ae
hint_5286:
; --- unverified ---
    move.b 9(a2),d0
    beq.s hint_52a4
hint_528c:
; --- unverified ---
    subq.b #1,d0
    beq.s hint_529a
hint_5290:
; --- unverified ---
    addq.l #4,a5
    cmpa.l 4(a2),a5
    blt.s hint_5290
hint_5298:
; --- unverified ---
    bra.s hint_527a
hint_529a:
; --- unverified ---
    addq.l #2,a5
    cmpa.l 4(a2),a5
    blt.s hint_529a
hint_52a2:
; --- unverified ---
    bra.s hint_527a
hint_52a4:
; --- unverified ---
    addq.l #1,a5
    cmpa.l 4(a2),a5
    blt.s hint_52a4
hint_52ac:
; --- unverified ---
    bra.s hint_527a
hint_52ae:
; --- unverified ---
    bsr.w sub_1c78
hint_52b2:
; --- unverified ---
    bra.s hint_527a
hint_52b4:
    dc.b    $50,$ee,$01,$63,$2a,$6e,$01,$6c
hint_52bc:
; --- unverified ---
    tst.l 372(a6) ; app+$174
    bne.s hint_52de
hint_52c2:
; --- unverified ---
    bsr.w sub_75ac
hint_52c6:
; --- unverified ---
    bne.s hint_52de
hint_52c8:
; --- unverified ---
    sf 228(a6) ; app+$E4
    sf 355(a6) ; app+$163
    bsr.w sub_5d9c
hint_52d4:
; --- unverified ---
    lea str_867f(pc),a0
    bsr.w sub_1ad6
hint_52dc:
; --- unverified ---
    bra.s hint_52f4
hint_52de:
; --- unverified ---
    st 228(a6) ; app+$E4
    bsr.w hint_6a94
hint_52e6:
; --- unverified ---
    bsr.s hint_531e
hint_52e8:
; --- unverified ---
    sf 228(a6) ; app+$E4
    sf 355(a6) ; app+$163
    bsr.w sub_5d9c
hint_52f4:
; --- unverified ---
    tst.l 372(a6) ; app+$174
    bne.w hint_7492
hint_52fc:
; --- unverified ---
    rts
hint_52fe:
    dc.b    $45,$ee,$0b,$10
hint_5302:
; --- unverified ---
    move.l (a2),d0
    beq.s hint_531a
hint_5306:
; --- unverified ---
    cmpa.l d0,a5
    blt.s hint_5314
hint_530a:
; --- unverified ---
    cmpa.l 4(a2),a5
    bge.s hint_5314
hint_5310:
; --- unverified ---
    moveq #0,d0
    rts
hint_5314:
; --- unverified ---
    lea 10(a2),a2
    bra.s hint_5302
hint_531a:
; --- unverified ---
    moveq #-1,d0
    rts
hint_531e:
; --- unverified ---
    cmpa.l 368(a6),a5 ; app+$170
    ble.s hint_5326
hint_5324:
; --- unverified ---
    rts
hint_5326:
; --- unverified ---
    tst.b 228(a6) ; app+$E4
    bpl.s hint_5324
hint_532c:
; --- unverified ---
    bsr.s hint_52fe
hint_532e:
; --- unverified ---
    bne.s hint_53aa
hint_5330:
; --- unverified ---
    move.l a5,-(sp)
    lea 2472(a6),a4 ; app+$9A8
    move.l #$64632e62,(a4)+ ; 'dc.b'
    subq.l #1,a4
    move.b 9(a2),d0
    beq.s hint_5384
hint_5344:
; --- unverified ---
    subq.w #1,d0
    beq.s hint_5366
hint_5348:
    dc.b    $18,$fc,$00,$6c,$18,$fc,$00,$20,$78,$01
hint_5352:
; --- unverified ---
    move.l (a5)+,d1
    bsr.w hint_1b88
hint_5358:
; --- unverified ---
    move.b #$2c,(a4)+
    cmpa.l 4(a2),a5
    dbge d4,hint_5352
hint_5364:
; --- unverified ---
    bra.s hint_53a0
hint_5366:
    dc.b    $18,$fc,$00,$77,$18,$fc,$00,$20,$78,$03
hint_5370:
; --- unverified ---
    move.w (a5)+,d1
    bsr.w hint_1b80
hint_5376:
; --- unverified ---
    move.b #$2c,(a4)+
    cmpa.l 4(a2),a5
    dbge d4,hint_5370
hint_5382:
; --- unverified ---
    bra.s hint_53a0
hint_5384:
    dc.b    $18,$fc,$00,$62,$18,$fc,$00,$20,$78,$07
hint_538e:
; --- unverified ---
    move.b (a5)+,d1
    bsr.w hint_1b6e
hint_5394:
; --- unverified ---
    move.b #$2c,(a4)+
    cmpa.l 4(a2),a5
    dbge d4,hint_538e
hint_53a0:
; --- unverified ---
    move.b #$a,-1(a4)
    movea.l (sp)+,a4
    bra.s hint_53b6
hint_53aa:
; --- unverified ---
    movem.l d3-d7/a5,-(sp)
    bsr.w sub_1c78
hint_53b2:
    dc.b    $4c,$df,$10,$f8
hint_53b6:
; --- unverified ---
    move.l a5,d4
    sub.l a4,d4
    bsr.s hint_53f8
hint_53bc:
    dc.b    $49,$ee,$09,$a8,$74,$ff
hint_53c2:
; --- unverified ---
    addq.b #1,d2
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.s hint_53f0
hint_53cc:
; --- unverified ---
    cmp.b #$20,d1
    bne.s hint_53ea
hint_53d2:
; --- unverified ---
    moveq #7,d0
    sub.b d2,d0
    bcs.s hint_53ea
hint_53d8:
; --- unverified ---
    moveq #9,d1
    tst.l 372(a6) ; app+$174
    bne.s hint_53e8
hint_53e0:
; --- unverified ---
    move.b d0,d2
    bsr.w sub_6a76
hint_53e6:
    dc.b    $72,$20
hint_53e8:
    dc.b    $74,$08
hint_53ea:
; --- unverified ---
    bsr.w sub_58ba
hint_53ee:
; --- unverified ---
    bra.s hint_53c2
hint_53f0:
; --- unverified ---
    bsr.w hint_6a94
hint_53f4:
; --- unverified ---
    bra.w hint_531e
hint_53f8:
; --- unverified ---
    tst.l 372(a6) ; app+$174
    bne.s hint_5442
hint_53fe:
; --- unverified ---
    move.l a4,d2
    bsr.w hint_6a9a
hint_5404:
; --- unverified ---
    bsr.w sub_6a82
hint_5408:
    dc.b    $76,$00
hint_540a:
; --- unverified ---
    cmp.w d4,d3
    bge.s hint_5420
hint_540e:
; --- unverified ---
    move.b 0(a4,d3.w),d2
    bsr.w hint_6aaa
hint_5416:
; --- unverified ---
    addq.w #1,d3
    cmp.w #$a,d3
    bne.s hint_540a
hint_541e:
; --- unverified ---
    bra.s hint_542a
hint_5420:
; --- unverified ---
    bsr.w sub_6a82
hint_5424:
; --- unverified ---
    bsr.w sub_6a82
hint_5428:
; --- unverified ---
    bra.s hint_5416
hint_542a:
; --- unverified ---
    bsr.w sub_6a82
hint_542e:
; --- unverified ---
    moveq #12,d2
    move.l a4,d0
    bsr.w hint_7ef8
hint_5436:
; --- unverified ---
    beq.s hint_543c
hint_5438:
; --- unverified ---
    bsr.w sub_7bd8
hint_543c:
; --- unverified ---
    addq.b #1,d2
    bra.w sub_6a76
hint_5442:
; --- unverified ---
    move.l a4,d0
    bsr.w hint_7ef8
hint_5448:
; --- unverified ---
    beq.s hint_5458
hint_544a:
; --- unverified ---
    movea.l d0,a4
    move.l d4,-(sp)
    move.l (a4)+,d4
    asl.l #2,d4
    bsr.w hint_7c14
hint_5456:
    dc.b    $28,$1f
hint_5458:
; --- unverified ---
    moveq #9,d1
    bra.w sub_58ba
hint_545e:
; --- unverified ---
    lea str_8843(pc),a0
    bsr.w sub_1b28
hint_5466:
; --- unverified ---
    bne.s hint_54a6
hint_5468:
; --- unverified ---
    lea dat_14c8(pc),a4
    moveq #20,d4
    move.b dat_88f5(pc),d0
    bne.s hint_54a6
hint_5474:
; --- unverified ---
    tst.b 308(a6) ; app+$134
    bmi.s hint_54a8
hint_547a:
; --- unverified ---
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -132(a6) ; app-$84; unresolved_indirect_hint:disp
hint_5484:
; --- unverified ---
    movea.l (sp)+,a6
    movea.l dat_895a(pc),a0
    movea.l 54(a0),a0
    move.l a4,(a0)
    bclr #7,4(a0)
    move.l d4,8(a0)
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -138(a6) ; app-$8A; unresolved_indirect_hint:disp
hint_54a4:
    dc.b    $2c,$5f
hint_54a6:
; --- unverified ---
    rts
hint_54a8:
; --- unverified ---
    move.l a4,app_exec_base_0054(a6)
    bclr #7,90(a6) ; app+$5A
    move.l d4,16(a6) ; app+$10
    st d3
    bra.w loc_1926
hint_54bc:
; --- unverified ---
    lea str_8839(pc),a0
    bsr.w sub_1b28
hint_54c4:
; --- unverified ---
    bne.s hint_54a6
hint_54c6:
; --- unverified ---
    move.b dat_88f5(pc),d0
    bne.s hint_54a6
hint_54cc:
; --- unverified ---
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -132(a6) ; app-$84; unresolved_indirect_hint:disp
hint_54d6:
; --- unverified ---
    movea.l (sp)+,a6
    movea.l dat_895a(pc),a0
    movea.l 54(a0),a0
    bset #7,4(a0)
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr -138(a6) ; app-$8A; unresolved_indirect_hint:disp
hint_54f0:
; --- unverified ---
    movea.l (sp)+,a6
    rts
hint_54f4:
; --- unverified ---
    tst.l 350(a6) ; app+$15E
    bne.s hint_550c
hint_54fa:
; --- unverified ---
    tst.l 174(a6) ; app+$AE
    beq.s hint_550c
hint_5500:
; --- unverified ---
    lea 13131(pc),a0
    bsr.w sub_1b28
hint_5508:
; --- unverified ---
    beq.w loc_7744
hint_550c:
; --- unverified ---
    rts
loc_550e:
    moveq #7,d3
    lea str_858f(pc),a0
    bsr.w sub_1a7e
loc_5518:
    bsr.w sub_59c0
loc_551c:
    bne.s sub_554a
loc_551e:
    tst.b (a4)
    beq.s sub_554a
loc_5522:
    bsr.w sub_19d0
loc_5526:
    lea str_85a7(pc),a0
    bsr.w sub_6a6a
loc_552e:
    bsr.w sub_19d4
loc_5532:
    lea 2832(a6),a4 ; app+$B10
    clr.b (a4)
    bsr.w sub_59c0
loc_553c:
    bne.s sub_554a
loc_553e:
    move.l a4,-(sp)
    bsr.s sub_554a
loc_5542:
    movea.l (sp)+,a4
    lea 2772(a6),a3 ; app+$AD4
    bra.s loc_554e
sub_554a:
    bra.w sub_5d9c
loc_554e:
    bsr.w call_unloadseg
loc_5552:
    bsr.w call_unloadseg_7740
loc_5556:
    move.l a3,d1 ; LoadSeg: name
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOLoadSeg(a6) ; app-$96
loc_5562:
    movea.l (sp)+,a6
    tst.l d0
    beq.w loc_1af8
loc_556a:
    move.l d0,dat_88f6
    add.l d0,d0
    add.l d0,d0
    addq.l #4,d0
    move.l d0,170(a6) ; app+$AA
    lea dat_136d(pc),a0
    movea.l a3,a1
    lea dat_136c(pc),a2
    st (a2)
loc_5586:
    addq.b #1,(a2)
    move.b (a1)+,(a0)+
    bne.s loc_5586
loc_558c:
    clr.b -(a0)
    movem.l d4-d7/a3-a5,-(sp)
    move.l a3,-(sp)
    bsr.w sub_052a
loc_5598:
    movea.l (sp)+,a0
    bsr.w call_close_7780
loc_559e:
    bsr.w alloc_memory
loc_55a2:
    bsr.w sub_052a
loc_55a6:
    movem.l (sp)+,d4-d7/a3-a5
    movea.l a4,a0
    lea pcref_1488(pc),a1
    clr.b (a1)+
loc_55b2:
    move.b (a0)+,(a1)+
    bne.s loc_55b2
loc_55b6:
    cmpi.b #$a,-2(a1)
    beq.s loc_55c6
loc_55be:
    move.b #$a,-1(a1)
    clr.b (a1)
loc_55c6:
    move.l a1,d0
    lea pcref_1489(pc),a0
    sub.l a0,d0
    move.b d0,-(a0)
    movea.l 170(a6),a1 ; app+$AA
    move.l a1,1690(a6) ; app+$69A
    moveq #1,d3
    moveq #1,d2
    bsr.w too_many_breakpoints
loc_55e0:
    movea.l 170(a6),a1 ; app+$AA
    move.w (a1),dat_88fa
    move.w #$4ef9,(a1)+
    move.l (a1),dat_88fc
    move.l #dat_13b0,(a1)
    movea.l dat_8956(pc),a0
    move.l 172(a0),d0
    add.l d0,d0
    add.l d0,d0
    movea.l d0,a0
    moveq #15,d0
    lea dat_1448(pc),a1
loc_560e:
    move.l (a0)+,(a1)+
    dbf d0,loc_560e
loc_5614:
    move.l #dat_136c,d1
    lsr.l #2,d1
    move.l d1,dat_1458
    move.l dat_88f6(pc),dat_1484
    move.l a3,d1 ; CreateProc: name
    moveq #0,d2
    movea.l dat_8956(pc),a0
    move.b 9(a0),d2 ; CreateProc: pri
    move.l dat_88f6(pc),d3 ; CreateProc: seglist
    moveq #80,d4
    add.l app_createproc_stacksize(a6),d4 ; CreateProc: stackSize
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOCreateProc(a6) ; app-$8A
loc_564a:
    movea.l (sp)+,a6
    move.l d0,app_createproc_process(a6)
    beq.s loc_565c
loc_5652:
    move.b #$1,308(a6) ; app+$134
    bsr.w loc_1044
loc_565c:
    rts
sub_565e:
    movem.w d2-d3,4(a3)
    movem.w d0-d1,14(a3)
    clr.l 10(a3)
    move.w 14(a3),d0
    move.w d0,18(a3)
    mulu.w app_rectfill_xmax(a6),d0
    move.w d0,14(a3)
    st 20(a3)
    move.w 6(a3),d0
    mulu.w app_rectfill_ymax(a6),d0
    move.w d0,8(a3)
    rts
sub_5690:
    bsr.s sub_565e
loc_5692:
    sf 20(a3)
call_rectfill:
    move.w 8(a3),d3
    move.l a2,-(sp)
    moveq #0,d0 ; SetAPen: pen
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetAPen: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetAPen(a6) ; app-$156
loc_56ac:
    movea.l (sp)+,a6
    movem.w 14(a3),d0-d1
    move.w 4(a3),d2
    mulu.w app_rectfill_xmax(a6),d2
    add.w d0,d2 ; RectFill: xMax
    subq.w #1,d2
    add.w d1,d3 ; RectFill: yMax
    subq.w #1,d3
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; RectFill: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVORectFill(a6) ; app-$132
loc_56d2:
    movea.l (sp)+,a6
    moveq #1,d0 ; SetAPen: pen
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetAPen: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetAPen(a6) ; app-$156
loc_56e4:
    movea.l (sp)+,a6
    movea.l (sp)+,a2
    rts
call_move:
    move.b d1,-(sp)
    mulu.w app_rectfill_xmax(a6),d2
    add.w 14(a3),d2 ; Move: x
    add.w 16(a3),d3
    add.w 218(a6),d3 ; Move: y
    move.w d2,d0 ; Move: x
    move.w d3,d1 ; Move: y
    movea.l a5,a1
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; Move: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOMove(a6) ; app-$F0
loc_5710:
    movea.l (sp)+,a6
    movea.l a5,a1
    tst.b d7
    bne.s loc_5730
loc_5718:
    movea.l sp,a0 ; Text: string
    moveq #1,d0 ; Text: count
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; Text: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOText(a6) ; app-$3C
loc_572a:
    movea.l (sp)+,a6
loc_572c:
    addq.l #2,sp
    rts
loc_5730:
    moveq #5,d0 ; SetDrMd: drawMode
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetDrMd: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetDrMd(a6) ; app-$162
loc_5740:
    movea.l (sp)+,a6
    movea.l sp,a0 ; Text: string
    moveq #1,d0 ; Text: count
    movea.l a5,a1
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; Text: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOText(a6) ; app-$3C
loc_5756:
    movea.l (sp)+,a6
    moveq #1,d0 ; SetDrMd: drawMode
    movea.l a5,a1
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetDrMd: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetDrMd(a6) ; app-$162
loc_576a:
    movea.l (sp)+,a6
    bra.s loc_572c
sub_576e:
    dc.b    $c6,$ee,$00,$d8
call_rectfill_5772:
    movem.w d2-d3,-(sp)
    moveq #3,d0 ; SetDrMd: drawMode
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetDrMd: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetDrMd(a6) ; app-$162
loc_5786:
    movea.l (sp)+,a6
    movem.w (sp)+,d0-d1
    mulu.w app_rectfill_xmax(a6),d0
    add.w 14(a3),d0 ; RectFill: xMin
    add.w 16(a3),d1 ; RectFill: yMin
    move.w d0,d2
    add.w app_rectfill_xmax(a6),d2 ; RectFill: xMax
    subq.w #1,d2
    move.w d1,d3
    add.w app_rectfill_ymax(a6),d3 ; RectFill: yMax
    subq.w #1,d3
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; RectFill: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVORectFill(a6) ; app-$132
loc_57b6:
    movea.l (sp)+,a6
    moveq #1,d0 ; SetDrMd: drawMode
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetDrMd: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetDrMd(a6) ; app-$162
loc_57c8:
    movea.l (sp)+,a6
    rts
sub_57cc:
; --- unverified ---
    movem.l d3-d5,-(sp)
    tst.b d0
    spl d1
    ori.b #$1,d1
    ext.w d1
    muls.w app_rectfill_ymax(a6),d1
    moveq #0,d0
    movem.w 14(a3),d2-d3
    move.w app_rectfill_xmax(a6),d4
    mulu.w 4(a3),d4
    add.w d2,d4
    subq.w #1,d4
    move.w 6(a3),d5
    mulu.w app_rectfill_ymax(a6),d5
    add.w d3,d5
    subq.w #1,d5
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1
    movea.l app_graphics_base(a6),a6
    jsr -396(a6) ; app-$18C; unresolved_indirect_hint:disp
hint_580c:
; --- unverified ---
    movea.l (sp)+,a6
    movem.l (sp)+,d3-d5
    rts
hint_5814:
; --- unverified ---
    moveq #-1,d0
    bsr.s sub_57cc
hint_5818:
; --- unverified ---
    move.w 6(a3),d0
    subq.w #1,d0
    mulu.w app_rectfill_ymax(a6),d0
    move.w d0,12(a3)
    clr.w 10(a3)
    rts
hint_582c:
; --- unverified ---
    moveq #0,d0
    bsr.s sub_57cc
hint_5830:
    dc.b    $42,$ab,$00,$0a
loc_5834:
    rts
loc_5836:
    tst.b 228(a6) ; app+$E4
    bne.s loc_5834
loc_583c:
    tst.l 1392(a6) ; app+$570
    beq.s loc_5846
loc_5842:
    bsr.w call_move_5940
loc_5846:
    moveq #0,d0 ; SetAPen: pen
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetAPen: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetAPen(a6) ; app-$156
loc_5856:
    movea.l (sp)+,a6
    move.w 10(a3),d0
    mulu.w app_rectfill_xmax(a6),d0
    add.w 14(a3),d0
    move.w 12(a3),d1
    add.w 16(a3),d1
    move.w 4(a3),d2
    mulu.w app_rectfill_xmax(a6),d2
    add.w 14(a3),d2
    cmp.w d0,d2
    ble.s loc_5896
loc_587c:
    subq.w #1,d2
    move.w d1,d3
    add.w app_rectfill_ymax(a6),d3 ; RectFill: yMax
    subq.w #1,d3
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; RectFill: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVORectFill(a6) ; app-$132
loc_5894:
    movea.l (sp)+,a6
loc_5896:
    moveq #1,d0 ; SetAPen: pen
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetAPen: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetAPen(a6) ; app-$156
loc_58a6:
    movea.l (sp)+,a6
    rts
sub_58aa:
; --- unverified ---
    addi.b #$30,d1
    bra.w sub_58ba
hint_58b2:
; --- unverified ---
    movem.l d0-d3/d7/a0-a2,-(sp)
    st d3
    bra.s loc_58c0
sub_58ba:
    movem.l d0-d3/d7/a0-a2,-(sp)
    sf d3
loc_58c0:
    tst.b 228(a6) ; app+$E4
    bne.w loc_7544
loc_58c8:
    cmpa.l 1392(a6),a3 ; app+$570
    beq.s loc_58e6
loc_58ce:
    move.w d1,-(sp)
    bsr.s call_move_5940
loc_58d2:
    move.w (sp)+,d1
    tst.b 20(a3)
    beq.s loc_5908
loc_58da:
    move.l a3,1392(a6) ; app+$570
    lea 2372(a6),a0 ; app+$944
    move.l a0,1396(a6) ; app+$574
loc_58e6:
    tst.b d3
    bne.s loc_58f0
loc_58ea:
    cmp.b #$a,d1
    beq.s loc_5900
loc_58f0:
    movea.l 1396(a6),a0 ; app+$574
    move.b d1,(a0)+
    move.l a0,1396(a6) ; app+$574
    movem.l (sp)+,d0-d3/d7/a0-a2
    rts
loc_5900:
    bsr.s call_move_5940
loc_5902:
    move.l a3,1392(a6) ; app+$570
    bra.s loc_5932
loc_5908:
    tst.b d3
    bne.s loc_5912
loc_590c:
    cmp.b #$a,d1
    beq.s loc_5932
loc_5912:
    move.w 10(a3),d0
    cmp.w 4(a3),d0
    beq.s loc_592c
loc_591c:
    movem.w 10(a3),d2-d3
    addq.w #1,10(a3)
    moveq #0,d7
    bsr.w call_move
loc_592c:
    movem.l (sp)+,d0-d3/d7/a0-a2
    rts
loc_5932:
    clr.w 10(a3)
    move.w app_rectfill_ymax(a6),d0
    add.w d0,12(a3)
    bra.s loc_592c
call_move_5940:
    tst.l 1392(a6) ; app+$570
    beq.s loc_59ba
loc_5946:
    movem.l d3/a3,-(sp)
    movea.l 1392(a6),a3 ; app+$570
    movem.w 10(a3),d2-d3
    cmp.w 8(a3),d3
    bge.s loc_59ae
loc_595a:
    mulu.w app_rectfill_xmax(a6),d2
    add.w 14(a3),d2 ; Move: x
    add.w 16(a3),d3
    add.w 218(a6),d3 ; Move: y
    move.w d2,d0 ; Move: x
    move.w d3,d1 ; Move: y
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; Move: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOMove(a6) ; app-$F0
loc_597c:
    movea.l (sp)+,a6
    move.l 1396(a6),d0 ; app+$574
    lea 2372(a6),a0 ; app+$944
    sub.l a0,d0
    beq.s loc_59ae
loc_598a:
    move.w 4(a3),d1
    sub.w 10(a3),d1
    cmp.w d1,d0
    blt.s loc_5998
loc_5996:
    move.w d1,d0
loc_5998:
    add.w d0,10(a3)
    ext.l d0 ; Text: count
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; Text: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOText(a6) ; app-$3C
loc_59ac:
    movea.l (sp)+,a6
loc_59ae:
    lea 2372(a6),a0 ; app+$944
    move.l a0,1396(a6) ; app+$574
    movem.l (sp)+,d3/a3
loc_59ba:
    clr.l 1392(a6) ; app+$570
    rts
sub_59c0:
    moveq #0,d4
loc_59c2:
    movea.l a4,a0
loc_59c4:
    tst.b (a0)+
    bne.s loc_59c4
loc_59c8:
    move.l a0,d5
    sub.l a4,d5
    subq.w #1,d5
    bsr.w sub_5b0c
loc_59d2:
    bsr.w sub_5af6
loc_59d6:
    move.w 12(a3),d3
    moveq #4,d2
    add.w d4,d2
    bsr.w call_rectfill_5772
loc_59e2:
    bsr.w call_replymsg_412c
loc_59e6:
    bmi.s loc_59e2
loc_59e8:
    cmp.b #$a,d1
    beq.w loc_5ad0
loc_59f0:
    cmp.b #$1b,d1
    beq.w loc_5ad0
loc_59f8:
    cmp.b #$8,d1
    beq.w loc_5a98
loc_5a00:
    cmp.b #$7f,d1
    beq.w loc_5ab8
loc_5a08:
    cmp.w #$86,d1
    beq.w loc_5ad8
loc_5a10:
    cmp.w #$84,d1
    beq.s loc_5a68
loc_5a16:
    cmp.w #$85,d1
    beq.s loc_5a74
loc_5a1c:
    cmp.w #$89,d1
    beq.s loc_5a80
loc_5a22:
    cmp.w #$8a,d1
    beq.s loc_5a8c
loc_5a28:
    tst.b d1
    beq.s loc_59e2
loc_5a2c:
    cmp.b #$80,d1
    bcs.s loc_5a38
loc_5a32:
    cmp.b #$a0,d1
    bcs.s loc_59e2
loc_5a38:
    cmp.w 226(a6),d5 ; app+$E2
    beq.s loc_59e2
loc_5a3e:
    move.w d5,d0
    addq.w #1,d5
    sub.w d4,d0
    beq.s loc_5a52
loc_5a46:
    lea -1(a4,d5.w),a0
loc_5a4a:
    move.b -(a0),1(a0)
    subq.w #1,d0
    bne.s loc_5a4a
loc_5a52:
    bsr.w sub_5ae4
loc_5a56:
    move.b d1,0(a4,d4.w)
    addq.w #1,d4
loc_5a5c:
    clr.b 0(a4,d5.w)
loc_5a60:
    bsr.w sub_5af6
loc_5a64:
    bra.w loc_59d6
loc_5a68:
    tst.w d4
    beq.w loc_59e2
loc_5a6e:
    bsr.s sub_5ae4
loc_5a70:
    subq.w #1,d4
    bra.s loc_5a60
loc_5a74:
    cmp.w d4,d5
    beq.w loc_59e2
loc_5a7a:
    bsr.s sub_5ae4
loc_5a7c:
    addq.w #1,d4
    bra.s loc_5a60
loc_5a80:
    tst.w d4
    beq.w loc_59e2
loc_5a86:
    bsr.s sub_5ae4
loc_5a88:
    moveq #0,d4
    bra.s loc_5a60
loc_5a8c:
    cmp.w d4,d5
    beq.w loc_59e2
loc_5a92:
    bsr.s sub_5ae4
loc_5a94:
    move.w d5,d4
    bra.s loc_5a60
loc_5a98:
    tst.w d4
    beq.w loc_59e2
loc_5a9e:
    bsr.s sub_5ae4
loc_5aa0:
    move.w d5,d0
    sub.w d4,d0
    beq.s loc_5ab2
loc_5aa6:
    lea 0(a4,d4.w),a0
loc_5aaa:
    move.b (a0)+,-2(a0)
    subq.w #1,d0
    bne.s loc_5aaa
loc_5ab2:
    subq.w #1,d4
    subq.w #1,d5
    bra.s loc_5a5c
loc_5ab8:
    move.w d5,d0
    sub.w d4,d0
    beq.w loc_59e2
loc_5ac0:
    lea 1(a4,d4.w),a0
loc_5ac4:
    move.b (a0)+,-2(a0)
    subq.w #1,d0
    bne.s loc_5ac4
loc_5acc:
    subq.w #1,d5
    bra.s loc_5a5c
loc_5ad0:
    bsr.s sub_5ae4
loc_5ad2:
    cmp.b #$a,d1
    rts
loc_5ad8:
    bsr.s sub_5b0c
loc_5ada:
    clr.b (a4)
    moveq #0,d4
    moveq #0,d5
    bra.w loc_59d6
sub_5ae4:
    move.w d1,-(sp)
    moveq #4,d2
    add.w d4,d2
    move.w 12(a3),d3
    bsr.w call_rectfill_5772
loc_5af2:
    move.w (sp)+,d1
    rts
sub_5af6:
    move.w 10(a3),-(sp)
    movea.l a4,a0
    bsr.w sub_6a6a
loc_5b00:
    moveq #32,d1
    bsr.w sub_58ba
loc_5b06:
    move.w (sp)+,10(a3)
    rts
sub_5b0c:
    move.w 10(a3),-(sp)
    move.w 226(a6),d2 ; app+$E2
    bsr.w sub_6a76
loc_5b18:
    move.w (sp)+,10(a3)
    rts
sub_5b1e:
    move.l a2,-(sp)
    add.w 220(a6),d1 ; app+$DC
    bsr.w sub_5690
loc_5b28:
    movea.l (sp)+,a2
    lea 22(a3),a0
    moveq #26,d0
    move.b #$20,(a0)+
loc_5b34:
    move.b (a2)+,(a0)+
    dbeq d0,loc_5b34
loc_5b3a:
    move.b #$20,-1(a0)
    clr.b (a0)
    lea pcref_5f32(pc),a0
    move.l a0,62(a3)
    clr.w 66(a3)
    moveq #0,d7
    st d4
    st 20(a3)
sub_5b56:
    move.l a4,-(sp)
    movea.l a3,a4
    lea 1464(a6),a3 ; app+$5B8
    move.w 18(a4),d2
    move.w 16(a4),d3
    sub.w 220(a6),d3 ; app+$DC
    tst.b 60(a4)
    beq.s loc_5ba0
loc_5b70:
    moveq #48,d1
    add.b 60(a4),d1
    bsr.w sub_5c2c
loc_5b7a:
    move.l 68(a4),d0
    beq.s loc_5ba0
loc_5b80:
    movea.l d0,a0
    tst.l 4(a0)
    bne.s loc_5b8c
loc_5b88:
    tst.l (a0)
    beq.s loc_5ba0
loc_5b8c:
    moveq #0,d1
    move.w 72(a4),d1
    divu.w #$1a,d1
    swap d1
    addi.b #$61,d1
    bsr.w sub_5c2c
loc_5ba0:
    moveq #32,d1
    bsr.w sub_5c2c
loc_5ba6:
    lea pcref_5c4e(pc),a0
    lea 22(a4),a1
    move.l a1,(a0)
    moveq #0,d0
    move.b 52(a4),d0
    asl.w #2,d0
    movea.l 0(a0,d0.w),a0
    bsr.w sub_5c1c
loc_5bc0:
    cmpi.b #$4,52(a4)
    bne.s loc_5be4
loc_5bc8:
    movea.l 68(a4),a0
    lea 37(a0),a0
    bsr.w sub_5c1c
loc_5bd4:
    moveq #41,d1
    bsr.w sub_5c2c
loc_5bda:
    movea.l 68(a4),a0
    tst.l 30(a0)
    beq.s loc_5c06
loc_5be4:
    tst.b 66(a4)
    beq.s loc_5c06
loc_5bea:
    cmpi.b #$2,52(a4)
    beq.s loc_5c06
loc_5bf2:
    move.w #$20,d1
    bsr.w sub_5c2c
loc_5bfa:
    movea.l 68(a4),a0
    lea 68(a0),a0
    bsr.w sub_5c1c
loc_5c06:
    move.w #$20,d1
    bsr.w sub_5c2c
loc_5c0e:
    tst.b d4
    beq.w loc_5cc4
loc_5c14:
    bsr.s call_move_5c62
loc_5c16:
    movea.l a4,a3
    movea.l (sp)+,a4
    rts
sub_5c1c:
    move.b (a0)+,d1
    beq.s loc_5c2a
loc_5c20:
    move.l a0,-(sp)
    bsr.w sub_5c2c
loc_5c26:
    movea.l (sp)+,a0
    bra.s sub_5c1c
loc_5c2a:
    rts
sub_5c2c:
    move.w 18(a4),d0
    add.w 4(a4),d0
    cmp.w d0,d2
    bcc.s loc_5c4a
loc_5c38:
    tst.b d4
    bne.s loc_5c3e
loc_5c3c:
    moveq #32,d1
loc_5c3e:
    movem.w d2-d3,-(sp)
    bsr.w call_move
loc_5c46:
    movem.w (sp)+,d2-d3
loc_5c4a:
    addq.w #1,d2
    rts
pcref_5c4e:
    dcb.b   4,0
    dc.l    dat_850a
    dc.l    sub_8511
    dc.l    dat_84fe
    dc.l    dat_851b
call_move_5c62:
    move.w 14(a4),d0 ; Move: x
    subq.w #1,d0
    move.w 16(a4),d1 ; Move: y
    subq.w #1,d1
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; Move: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOMove(a6) ; app-$F0
loc_5c7c:
    movea.l (sp)+,a6
    movea.l app_setapen_rp(a6),a1 ; PolyDraw: rp
    lea app_polydraw_polytable(a6),a0
    move.w 4(a4),d0
    mulu.w app_rectfill_xmax(a6),d0
    add.w 14(a4),d0
    addq.w #1,d0
    move.w d0,(a0)+
    move.w 38(a1),d1
    move.w d1,(a0)+
    add.w 8(a4),d1
    addq.w #1,d1
    move.w d0,(a0)+
    move.w d1,(a0)+
    move.w 36(a1),(a0)+
    move.w d1,(a0)+
    move.l 36(a1),(a0)+
    moveq #4,d0 ; PolyDraw: count
    lea app_polydraw_polytable(a6),a0 ; PolyDraw: polyTable
    move.l a6,-(sp)
    movea.l app_graphics_base(a6),a6
    jsr _LVOPolyDraw(a6) ; app-$150
loc_5cc0:
    movea.l (sp)+,a6
    rts
loc_5cc4:
    moveq #0,d0 ; SetAPen: pen
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetAPen: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetAPen(a6) ; app-$156
loc_5cd4:
    movea.l (sp)+,a6
    bsr.s call_move_5c62
loc_5cd8:
    moveq #1,d0 ; SetAPen: pen
    move.l a6,-(sp)
    movea.l app_setapen_rp(a6),a1 ; SetAPen: rp
    movea.l app_graphics_base(a6),a6
    jsr _LVOSetAPen(a6) ; app-$156
loc_5ce8:
    movea.l (sp)+,a6
    bra.w loc_5c16
sub_5cee:
    movea.l app_closewindow_window(a6),a0
    movea.l wd_RPort(a0),a2
    move.l a2,app_setapen_rp(a6)
    move.w 60(a2),app_rectfill_xmax(a6)
    move.w 58(a2),app_rectfill_ymax(a6)
    move.w 62(a2),218(a6) ; app+$DA
    move.w wd_Height(a0),234(a6) ; app+$EA
    move.w wd_Width(a0),d0
    move.w d0,232(a6) ; app+$E8
    ext.l d0
    divu.w app_rectfill_xmax(a6),d0
    move.w d0,236(a6) ; app+$EC
    move.w d0,d2
    move.w 234(a6),d3 ; app+$EA
    ext.l d3
    divu.w app_rectfill_ymax(a6),d3
    moveq #0,d4
    moveq #0,d0
    moveq #0,d1
    lea 1464(a6),a3 ; app+$5B8
    bset #15,d4
    bsr.w sub_5690
loc_5d42:
    move.w app_rectfill_ymax(a6),d0
    addq.w #1,d0
    move.w d0,220(a6) ; app+$DC
    moveq #6,d0
    lea 1486(a6),a0 ; app+$5CE
loc_5d52:
    clr.w 4(a0)
    lea 74(a0),a0
    dbf d0,loc_5d52
loc_5d5e:
    clr.l 222(a6) ; app+$DE
    lea 2154(a6),a0 ; app+$86A
    move.w #$1,(a0)+
    move.w 220(a6),(a0)+ ; app+$DC
    move.w 236(a6),d0 ; app+$EC
    subq.w #2,d0
    move.w d0,(a0)+
    move.w 234(a6),d0 ; app+$EA
    ext.l d0
    divu.w app_rectfill_ymax(a6),d0
    subq.w #2,d0
    move.w d0,(a0)+
    move.w #$32,226(a6) ; app+$E2
    move.w 234(a6),d0 ; app+$EA
    sub.w app_rectfill_ymax(a6),d0
    move.w d0,238(a6) ; app+$EE
    clr.l 1392(a6) ; app+$570
    rts
sub_5d9c:
    movem.l d4-d7,-(sp)
    pea pcref_5dcc(pc)
    bsr.w call_rectfill
loc_5da8:
    sf d7
    sf d4
    bsr.w sub_5b56
loc_5db0:
    clr.w 4(a3)
    lea 1856(a6),a3 ; app+$740
    tst.w 4(a3)
    beq.w loc_5efa
loc_5dc0:
    st d7
    st d4
    bsr.w sub_5b56
loc_5dc8:
    bra.w graphics_dispatch
pcref_5dcc:
    dc.b    $4c,$df,$00,$f0,$4e,$75
sub_5dd2:
    moveq #0,d1
    move.w 4(a3),d1
    moveq #0,d0
    move.b 52(a3),d0
    add.w d0,d0
    jmp pcref_5de4(pc,d0.w) ; unresolved_indirect_core:pcindex.brief
pcref_5de4:
    rts
    bra.s loc_5dee
    bra.s loc_5dfc
    bra.s loc_5e1c
    bra.s loc_5e42
loc_5dee:
    lea pcref_5fe2(pc),a0
    move.l a0,62(a3)
    subi.w #$a,d1
    bra.s loc_5e08
loc_5dfc:
    lea pcref_66f6(pc),a0
    move.l a0,62(a3)
    subi.w #$26,d1
loc_5e08:
    divu.w #$7,d1
    add.w d1,d1
    cmp.w #$10,d1
    bls.s loc_5e16
loc_5e14:
    moveq #16,d1
loc_5e16:
    move.b d1,53(a3)
    rts
loc_5e1c:
    subi.w #$26,d1
    bcc.s loc_5e24
loc_5e22:
    moveq #0,d1
loc_5e24:
    cmp.b #$6,d1
    bcc.s loc_5e2c
loc_5e2a:
    moveq #0,d1
loc_5e2c:
    cmp.b #$10,d1
    bcs.s loc_5e34
loc_5e32:
    moveq #16,d1
loc_5e34:
    move.b d1,53(a3)
    lea pcref_6782(pc),a0
    move.l a0,62(a3)
    rts
loc_5e42:
    move.b dat_002a,53(a3)
    lea pcref_682e(pc),a0
    move.l a0,62(a3)
    rts
sub_5e54:
    movem.l d0-d1/a0-a1,-(sp)
    movea.l app_closescreen_screen(a6),a0
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr -96(a6)
hint_5e66:
    movea.l (sp)+,a6
    movem.l (sp)+,d0-d1/a0-a1
    rts
call_activatewindow:
    movea.l app_intuition_base(a6),a1
    movea.l app_closescreen_screen(a6),a0
    cmpa.l ib_FirstScreen(a1),a0
    beq.s loc_5e88
loc_5e7c:
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOScreenToFront(a6)
loc_5e86:
    movea.l (sp)+,a6
loc_5e88:
    movea.l app_closewindow_window(a6),a0
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOActivateWindow(a6)
loc_5e96:
    movea.l (sp)+,a6
    rts
sub_5e9a:
    movea.l app_closescreen_screen(a6),a0
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr -246(a6)
hint_5ea8:
    movea.l (sp)+,a6
    rts
hint_5eac:
; --- unverified ---
    move.l a2,-(sp)
    lea 1464(a6),a3 ; app+$5B8
    bsr.w call_rectfill
hint_5eb6:
    dc.b    $47,$ee,$07,$40,$41,$eb,$00,$16,$70,$19
hint_5ec0:
; --- unverified ---
    clr.w (a0)+
    dbf d0,hint_5ec0
hint_5ec6:
; --- unverified ---
    movem.w 2154(a6),d0-d4 ; app+$86A
    sub.w 220(a6),d1 ; app+$DC
    movea.l (sp)+,a2
    bsr.w sub_5b1e
hint_5ed6:
; --- unverified ---
    st d7
    st d4
    bra.w sub_5b56
sub_5ede:
    lea 1486(a6),a3 ; app+$5CE
    moveq #6,d2
loc_5ee4:
    tst.w 4(a3)
    beq.s loc_5ef0
loc_5eea:
    move.w d2,-(sp)
    bsr.s graphics_dispatch
loc_5eee:
    move.w (sp)+,d2
loc_5ef0:
    lea 74(a3),a3
    dbf d2,loc_5ee4
loc_5ef8:
    rts
loc_5efa:
    lea 1486(a6),a3 ; app+$5CE
    moveq #6,d2
loc_5f00:
    tst.w 4(a3)
    beq.s loc_5f18
loc_5f06:
    move.w d2,-(sp)
    cmpa.l 222(a6),a3 ; app+$DE
    seq d7
    st d4
    bsr.w sub_5b56
loc_5f14:
    bsr.s graphics_dispatch
loc_5f16:
    move.w (sp)+,d2
loc_5f18:
    lea 74(a3),a3
    dbf d2,loc_5f00
loc_5f20:
    rts
graphics_dispatch:
    clr.l 10(a3)
    movea.l 62(a3),a0
    jsr 0(a0) ; unresolved_indirect_core:disp
loc_5f2e:
    bra.w call_move_5940
pcref_5f32:
    dc.b    $60,$00,$00,$10,$60,$0c,$60,$0a,$60,$08,$60,$06,$60,$04,$60,$02
    dc.b    $4e,$71,$72,$00,$4e,$75
sub_5f48:
    dc.b    $3e,$2b,$00,$06,$24,$6b,$00,$38
hint_5f50:
; --- unverified ---
    bsr.s hint_5f5c
hint_5f52:
; --- unverified ---
    bsr.w hint_6a94
hint_5f56:
; --- unverified ---
    subq.b #1,d7
    bne.s hint_5f50
hint_5f5a:
; --- unverified ---
    rts
hint_5f5c:
; --- unverified ---
    move.l a2,d2
    bsr.w hint_6a9a
hint_5f62:
; --- unverified ---
    bsr.w sub_6a82
hint_5f66:
; --- unverified ---
    move.b 53(a3),d6
    bsr.s hint_5fa4
hint_5f6c:
; --- unverified ---
    moveq #0,d6
    move.b 53(a3),d6
    bsr.w call_typeofmem
hint_5f76:
; --- unverified ---
    suba.w d6,a2
    bne.s hint_5f96
hint_5f7a:
; --- unverified ---
    bsr.w call_typeofmem
hint_5f7e:
; --- unverified ---
    bne.s hint_5f96
hint_5f80:
; --- unverified ---
    bsr.w sub_6a82
hint_5f84:
; --- unverified ---
    move.b (a2)+,d1
    bne.s hint_5f8c
hint_5f88:
    dc.b    $12,$3c,$00,$b7
hint_5f8c:
; --- unverified ---
    bsr.w hint_58b2
hint_5f90:
; --- unverified ---
    subq.b #1,d6
    bne.s hint_5f84
hint_5f94:
; --- unverified ---
    rts
hint_5f96:
; --- unverified ---
    move.b 53(a3),d2
    addq.b #1,d2
    bsr.w sub_6a76
hint_5fa0:
; --- unverified ---
    adda.w d6,a2
    rts
hint_5fa4:
; --- unverified ---
    tst.b d6
    beq.s hint_5fd0
hint_5fa8:
; --- unverified ---
    bsr.w sub_6a82
hint_5fac:
; --- unverified ---
    bsr.w call_typeofmem
hint_5fb0:
; --- unverified ---
    beq.s hint_5fba
hint_5fb2:
; --- unverified ---
    addq.l #1,a2
    bsr.w sub_6a88
hint_5fb8:
; --- unverified ---
    bra.s hint_5fc0
hint_5fba:
; --- unverified ---
    move.b (a2)+,d2
    bsr.w hint_6aaa
hint_5fc0:
; --- unverified ---
    move.w a2,d0
    btst #0,d0
    bne.s hint_5fcc
hint_5fc8:
; --- unverified ---
    bsr.w sub_6a82
hint_5fcc:
; --- unverified ---
    subq.b #1,d6
    bne.s hint_5fac
hint_5fd0:
; --- unverified ---
    rts
hint_5fd2:
; --- unverified ---
    subq.l #1,56(a3)
    moveq #-1,d0
    rts
hint_5fda:
; --- unverified ---
    addq.l #1,56(a3)
    moveq #-1,d0
    rts
pcref_5fe2:
; --- unverified ---
    bra.w sub_5f48
    dc.b    $60,$0a,$60,$12,$60,$22,$60,$3e,$60,$e2,$60,$e8
sub_5ff2:
; --- unverified ---
    moveq #0,d0
    move.b 53(a3),d0
    neg.w d0
    bra.s hint_6002
hint_5ffc:
; --- unverified ---
    moveq #0,d0
    move.b 53(a3),d0
hint_6002:
    muls.w 6(a3),d0
    add.l d0,56(a3)
    moveq #-1,d1
    rts
hint_600e:
; --- unverified ---
    bsr.w hint_582c
hint_6012:
; --- unverified ---
    moveq #0,d0
    move.b 53(a3),d0
    sub.l d0,56(a3)
    movea.l 56(a3),a2
    bsr.w hint_5f5c
hint_6024:
; --- unverified ---
    bsr.w call_move_5940
hint_6028:
; --- unverified ---
    moveq #0,d1
    rts
hint_602c:
; --- unverified ---
    bsr.w hint_5814
hint_6030:
; --- unverified ---
    moveq #0,d0
    move.b 53(a3),d0
    add.l d0,56(a3)
    move.w 6(a3),d1
    subq.w #1,d1
    mulu.w d0,d1
    movea.l 56(a3),a2
    adda.l d1,a2
    bsr.w hint_5f5c
hint_604c:
; --- unverified ---
    bsr.w call_move_5940
hint_6050:
; --- unverified ---
    moveq #0,d1
    rts
hint_6054:
; --- unverified ---
    movea.l 56(a3),a4
    moveq #0,d6
    moveq #0,d7
    moveq #0,d5
    moveq #0,d4
    move.b 53(a3),d4
    mulu.w #$5,d4
    lsr.w #1,d4
    move.w d4,d3
    bra.s hint_60ce
hint_606e:
; --- unverified ---
    move.w d3,-(sp)
    moveq #10,d2
    tst.b d5
    beq.s hint_607a
hint_6076:
    dc.b    $d4,$44,$52,$42
hint_607a:
; --- unverified ---
    add.w d6,d2
    move.w d7,d3
    bsr.w sub_576e
hint_6082:
; --- unverified ---
    move.w (sp)+,d3
    rts
pcref_6086:
    dc.b    $00,$00,$01,$01,$01,$02,$02,$03,$03,$03,$04,$04,$05,$05,$05,$06
    dc.b    $06,$07,$07,$07,$08,$08,$09,$09,$09,$0a,$0a,$0b,$0b,$0b,$0c,$0c
    dc.b    $0d,$0d,$0d,$0e,$0e,$0f,$0f,$0f
hint_60ae:
    dc.b    $10,$3b,$60,$d6,$48,$80,$4e,$75
hint_60b6:
; --- unverified ---
    not.b d5
    bne.s hint_60c4
hint_60ba:
; --- unverified ---
    mulu.w #$5,d6
    lsr.w #1,d6
    move.w d4,d3
    bra.s hint_60ce
hint_60c4:
; --- unverified ---
    bsr.s hint_60ae
hint_60c6:
    dc.b    $3c,$00,$76,$00,$16,$2b,$00,$35
hint_60ce:
; --- unverified ---
    bsr.s hint_606e
hint_60d0:
; --- unverified ---
    bsr.w call_replymsg_412c
hint_60d4:
; --- unverified ---
    bmi.w hint_61a4
hint_60d8:
; --- unverified ---
    move.w d1,-(sp)
    bsr.s hint_606e
hint_60dc:
; --- unverified ---
    move.w (sp)+,d1
    cmp.b #$1b,d1
    beq.w hint_07da
hint_60e6:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_60b6
hint_60ec:
; --- unverified ---
    cmp.b #$88,d1
    beq.s hint_60b6
hint_60f2:
; --- unverified ---
    cmp.w #$82,d1
    beq.w hint_61c0
hint_60fa:
; --- unverified ---
    cmp.w #$83,d1
    beq.w hint_61e2
hint_6102:
; --- unverified ---
    cmp.w #$85,d1
    beq.w hint_6206
hint_610a:
; --- unverified ---
    cmp.w #$84,d1
    beq.w hint_6236
hint_6112:
; --- unverified ---
    cmp.b #$8,d1
    beq.w hint_6236
hint_611a:
; --- unverified ---
    tst.b d5
    bne.s hint_616e
hint_611e:
; --- unverified ---
    moveq #48,d0
    cmp.b d0,d1
    bcs.s hint_60ce
hint_6124:
; --- unverified ---
    cmp.b #$3a,d1
    bcs.s hint_613c
hint_612a:
; --- unverified ---
    andi.b #$df,d1
    cmp.b #$41,d1
    bcs.s hint_60ce
hint_6134:
; --- unverified ---
    cmp.b #$47,d1
    bcc.s hint_60ce
hint_613a:
    dc.b    $70,$37
hint_613c:
; --- unverified ---
    sub.b d0,d1
    move.b d1,d2
    bsr.w hint_60ae
hint_6144:
; --- unverified ---
    lea 0(a4,d0.w),a0
    move.l a0,d0
    bsr.w sub_73a4
hint_614e:
; --- unverified ---
    bne.w hint_6206
hint_6152:
; --- unverified ---
    bsr.w hint_6216
hint_6156:
; --- unverified ---
    andi.b #$1,d0
    bne.s hint_6164
hint_615c:
; --- unverified ---
    andi.b #$f0,(a0)
    or.b d2,(a0)
    bra.s hint_6184
hint_6164:
; --- unverified ---
    andi.b #$f,(a0)
    lsl.b #4,d2
    or.b d2,(a0)
    bra.s hint_6184
hint_616e:
; --- unverified ---
    tst.b d1
    beq.w hint_60ce
hint_6174:
; --- unverified ---
    lea 0(a4,d6.w),a0
    move.l a0,d0
    bsr.w sub_73a4
hint_617e:
; --- unverified ---
    bne.s hint_6184
hint_6180:
    dc.b    $19,$81,$60,$00
hint_6184:
; --- unverified ---
    clr.w 10(a3)
    movem.l d3-d7/a4,-(sp)
    mulu.w app_rectfill_ymax(a6),d7
    move.w d7,12(a3)
    movea.l a4,a2
    bsr.w hint_5f5c
hint_619a:
; --- unverified ---
    bsr.w call_move_5940
hint_619e:
; --- unverified ---
    movem.l (sp)+,d3-d7/a4
    bra.s hint_6206
hint_61a4:
; --- unverified ---
    move.w d1,-(sp)
    bsr.w hint_606e
hint_61aa:
; --- unverified ---
    move.w (sp)+,d1
    cmp.b #$45,d1
    beq.w hint_07da
hint_61b4:
; --- unverified ---
    move.w d1,-(sp)
    bsr.w hint_07da
hint_61ba:
; --- unverified ---
    move.w (sp)+,d1
    bra.w hint_0720
hint_61c0:
; --- unverified ---
    moveq #0,d0
    move.b 53(a3),d0
    suba.l d0,a4
    subq.w #1,d7
    bcc.w hint_6252
hint_61ce:
; --- unverified ---
    movem.l d3-d7/a4,-(sp)
    bsr.w hint_600e
hint_61d6:
; --- unverified ---
    movem.l (sp)+,d3-d7/a4
    moveq #0,d7
    bsr.w call_replymsg_40fa
hint_61e0:
; --- unverified ---
    bra.s hint_6252
hint_61e2:
; --- unverified ---
    moveq #0,d0
    move.b 53(a3),d0
    adda.l d0,a4
    addq.w #1,d7
    cmp.w 6(a3),d7
    bne.s hint_6252
hint_61f2:
; --- unverified ---
    subq.w #1,d7
    movem.l d3-d7/a4,-(sp)
    bsr.w hint_602c
hint_61fc:
; --- unverified ---
    movem.l (sp)+,d3-d7/a4
    bsr.w call_replymsg_40fa
hint_6204:
; --- unverified ---
    bra.s hint_6252
hint_6206:
; --- unverified ---
    addq.w #1,d6
    bsr.s hint_6216
hint_620a:
; --- unverified ---
    bne.s hint_620e
hint_620c:
    dc.b    $52,$46
hint_620e:
; --- unverified ---
    cmp.w d3,d6
    bne.s hint_6252
hint_6212:
; --- unverified ---
    moveq #0,d6
    bra.s hint_61e2
hint_6216:
; --- unverified ---
    tst.b d5
    bne.s hint_6234
hint_621a:
; --- unverified ---
    moveq #0,d0
    move.w d6,d0
    moveq #1,d1
    btst #0,59(a3)
    beq.s hint_622a
hint_6228:
    dc.b    $72,$03
hint_622a:
    dc.b    $d0,$41,$80,$fc,$00,$05,$48,$40,$4a,$40
hint_6234:
; --- unverified ---
    rts
hint_6236:
; --- unverified ---
    subq.w #1,d6
    bcs.s hint_6242
hint_623a:
; --- unverified ---
    bsr.s hint_6216
hint_623c:
; --- unverified ---
    bne.s hint_6252
hint_623e:
; --- unverified ---
    subq.w #1,d6
    bcc.s hint_6252
hint_6242:
; --- unverified ---
    move.w d3,d6
    subq.w #1,d6
    bsr.s hint_6216
hint_6248:
; --- unverified ---
    bne.w hint_61c0
hint_624c:
; --- unverified ---
    subq.w #1,d6
    bra.w hint_61c0
hint_6252:
; --- unverified ---
    bra.w hint_60ce
hint_6256:
; --- unverified ---
    bsr.w sub_6a82
hint_625a:
; --- unverified ---
    moveq #61,d1
    bsr.w sub_58ba
hint_6260:
; --- unverified ---
    bra.w sub_6a82
hint_6264:
    dc.b    $43,$ee,$00,$10,$7e,$30
hint_626a:
; --- unverified ---
    moveq #100,d1
    bsr.w sub_58ba
hint_6270:
; --- unverified ---
    move.b d7,d1
    bsr.w sub_58ba
hint_6276:
; --- unverified ---
    bsr.s hint_6256
hint_6278:
; --- unverified ---
    movea.l (a1),a2
    move.l a2,d2
    bsr.w hint_6a9a
hint_6280:
; --- unverified ---
    bsr.w sub_6a82
hint_6284:
; --- unverified ---
    bsr.w sub_6a82
hint_6288:
    dc.b    $7c,$03
hint_628a:
; --- unverified ---
    move.b (a1)+,d1
    bne.s hint_6292
hint_628e:
    dc.b    $12,$3c,$00,$b7
hint_6292:
; --- unverified ---
    bsr.w hint_58b2
hint_6296:
; --- unverified ---
    dbf d6,hint_628a
hint_629a:
; --- unverified ---
    bsr.w sub_6a82
hint_629e:
; --- unverified ---
    bsr.w sub_6a82
hint_62a2:
; --- unverified ---
    bsr.w sub_6a82
hint_62a6:
; --- unverified ---
    bsr.w sub_6a82
hint_62aa:
; --- unverified ---
    moveq #97,d1
    bsr.w sub_58ba
hint_62b0:
; --- unverified ---
    move.b d7,d1
    bsr.w sub_58ba
hint_62b6:
; --- unverified ---
    bsr.s hint_6256
hint_62b8:
; --- unverified ---
    movea.l 28(a1),a2
    bsr.w hint_5f5c
hint_62c0:
; --- unverified ---
    bsr.w hint_6a94
hint_62c4:
; --- unverified ---
    addq.b #1,d7
    cmp.b #$38,d7
    bne.s hint_626a
hint_62cc:
; --- unverified ---
    moveq #1,d1
    bsr.w sub_6a5a
hint_62d2:
; --- unverified ---
    move.w 90(a6),d2 ; app+$5A
    bsr.w hint_6aa2
hint_62da:
    dc.b    $7e,$05
hint_62dc:
; --- unverified ---
    bsr.w sub_6a82
hint_62e0:
; --- unverified ---
    dbf d7,hint_62dc
hint_62e4:
; --- unverified ---
    move.w 90(a6),d4 ; app+$5A
    bsr.w hint_66a2
hint_62ec:
; --- unverified ---
    bsr.w hint_6a94
hint_62f0:
; --- unverified ---
    moveq #0,d1
    bsr.w sub_6a5a
hint_62f6:
; --- unverified ---
    move.l app_exec_base_0054(a6),d2
    bsr.w hint_6a9a
hint_62fe:
; --- unverified ---
    bsr.w sub_6a82
hint_6302:
; --- unverified ---
    bsr.w sub_6a82
hint_6306:
; --- unverified ---
    movea.l app_exec_base_0054(a6),a2
    sf 331(a6) ; app+$14B
    bsr.w sub_69a6
hint_6312:
; --- unverified ---
    bset #0,331(a6) ; app+$14B
    beq.s hint_6368
hint_631a:
; --- unverified ---
    moveq #17,d1
    bsr.w sub_6a5a
hint_6320:
; --- unverified ---
    move.l 334(a6),d2 ; app+$14E
    move.l d2,2004(a6) ; app+$7D4
    bsr.w hint_6a9a
hint_632c:
; --- unverified ---
    movea.l 334(a6),a2 ; app+$14E
    moveq #0,d0
    move.b 333(a6),d0 ; app+$14D
    move.b pcref_6376(pc,d0.w),d6
    bsr.w hint_5fa4
hint_633e:
; --- unverified ---
    tst.b 332(a6) ; app+$14C
    beq.s hint_6368
hint_6344:
; --- unverified ---
    moveq #62,d1
    bsr.w sub_58ba
hint_634a:
; --- unverified ---
    move.l 338(a6),d2 ; app+$152
    move.l d2,2004(a6) ; app+$7D4
    bsr.w hint_6a9a
hint_6356:
; --- unverified ---
    movea.l 338(a6),a2 ; app+$152
    moveq #0,d0
    move.b 333(a6),d0 ; app+$14D
    move.b pcref_6376(pc,d0.w),d6
    bsr.w hint_5fa4
hint_6368:
; --- unverified ---
    st 331(a6) ; app+$14B
    bsr.w loc_5836
hint_6370:
; --- unverified ---
    bsr.w hint_6a94
hint_6374:
; --- unverified ---
    bra.s hint_637a
pcref_6376:
    dc.b    $01,$02,$04,$08
hint_637a:
    dc.b    $0c,$6b
hint_6384:
; --- unverified ---
    movea.l AbsExecBase,a0
    move.w 296(a0),d0
    lea pcref_65a2(pc),a1
    btst #0,d0
    beq.s hint_63b4
hint_6396:
; --- unverified ---
    lea pcref_65aa(pc),a1
    btst #1,d0
    beq.s hint_63b4
hint_63a0:
; --- unverified ---
    btst #3,d0
    bne.s hint_63b4
hint_63a6:
; --- unverified ---
    lea pcref_65c4(pc),a1
    btst #2,d0
    beq.s hint_63b4
hint_63b0:
    dc.b    $43,$fa,$02,$44
hint_63b4:
; --- unverified ---
    bsr.w hint_6516
hint_63b8:
; --- unverified ---
    tst.b dat_8906
    beq.w hint_64c2
hint_63c2:
; --- unverified ---
    lea pcref_664c(pc),a1
    bsr.w hint_6516
hint_63ca:
    dc.b    $43,$fa,$26,$ae,$7e,$00
hint_63d0:
; --- unverified ---
    moveq #102,d1
    bsr.w sub_58ba
hint_63d6:
; --- unverified ---
    moveq #112,d1
    bsr.w sub_58ba
hint_63dc:
; --- unverified ---
    move.b d7,d1
    bsr.w sub_58aa
hint_63e2:
; --- unverified ---
    bsr.w hint_6256
    dc.b    $f2,$11,$48,$00,$34,$19,$61,$00,$06,$b4,$72,$20,$61,$00,$f4,$c6
    dc.b    $54,$49,$24,$19,$61,$00,$06,$9e,$72,$20,$61,$00,$f4,$b8,$24,$19
    dc.b    $61,$00,$06,$92,$72,$20,$61,$00,$f4,$ac,$2f,$09,$43,$ee,$05,$9c
    dc.b    $f2,$11
sub_6418:
    dc.b    $6c,$11
hint_641a:
; --- unverified ---
    moveq #32,d1
    btst #7,(a1)
    beq.s hint_6424
hint_6422:
    dc.b    $72,$2d
hint_6424:
; --- unverified ---
    bsr.w sub_58ba
hint_6428:
    dc.b    $32,$19,$00
hint_642b:
    dc.b    $41,$80,$00
hint_6432:
; --- unverified ---
    addq.w #2,a1
    lea str_6661(pc),a0
    btst #6,(a1)
    bne.s hint_644c
hint_643e:
; --- unverified ---
    move.l (a1)+,d1
    lea str_6665(pc),a0
    or.l (a1),d1
    beq.s hint_644c
hint_6448:
    dc.b    $41,$fa,$02,$16
hint_644c:
; --- unverified ---
    bsr.w sub_6a6a
hint_6450:
; --- unverified ---
    bra.s hint_64b2
hint_6452:
; --- unverified ---
    addq.w #1,a1
    move.b (a1)+,d1
    andi.b #$f,d1
    bsr.w sub_58aa
hint_645e:
; --- unverified ---
    moveq #46,d1
    bsr.w sub_58ba
hint_6464:
    dc.b    $3f,$07,$7e,$07
hint_6468:
; --- unverified ---
    move.b (a1)+,d0
    bsr.w hint_6504
hint_646e:
; --- unverified ---
    dbf d7,hint_6468
hint_6472:
; --- unverified ---
    move.w (sp)+,d7
    moveq #101,d1
    bsr.w sub_58ba
hint_647a:
; --- unverified ---
    lea 1436(a6),a1 ; app+$59C
    moveq #43,d1
    btst #6,(a1)
    beq.s hint_6488
hint_6486:
    dc.b    $72,$2d
hint_6488:
; --- unverified ---
    bsr.w sub_58ba
    dc.b    $f2,$00,$a8,$00
sub_6490:
; --- unverified ---
    moveq #0,d1
    btst #13,d0
    beq.s hint_649e
hint_6498:
    dc.b    $e9,$e9,$10,$04,$00,$02
hint_649e:
; --- unverified ---
    bsr.w sub_58aa
hint_64a2:
; --- unverified ---
    move.b (a1)+,d1
    andi.b #$f,d1
    bsr.w sub_58aa
hint_64ac:
; --- unverified ---
    move.b (a1),d0
    bsr.w hint_6504
hint_64b2:
; --- unverified ---
    movea.l (sp)+,a1
    bsr.w hint_6a94
hint_64b8:
; --- unverified ---
    addq.b #1,d7
    cmp.b #$8,d7
    bne.w hint_63d0
hint_64c2:
; --- unverified ---
    bsr.w hint_6a94
hint_64c6:
    dc.b    $1f,$2b,$00,$35,$17,$7c,$00,$10,$00,$35,$7e,$00,$43,$fa,$0e,$82
hint_64d6:
; --- unverified ---
    moveq #109,d1
    bsr.w sub_58ba
hint_64dc:
; --- unverified ---
    moveq #48,d1
    add.b d7,d1
    bsr.w sub_58ba
hint_64e4:
; --- unverified ---
    bsr.w hint_6256
hint_64e8:
; --- unverified ---
    move.w (a1)+,d2
    movea.l 0(a6,d2.w),a2
    bsr.w hint_5f5c
hint_64f2:
; --- unverified ---
    bsr.w hint_6a94
hint_64f6:
; --- unverified ---
    addq.w #1,d7
    cmp.w #$a,d7
    bne.s hint_64d6
hint_64fe:
    dc.b    $17,$5f,$00,$35
hint_6502:
; --- unverified ---
    rts
hint_6504:
    dc.b    $85,$80,$30,$30,$e9,$c2,$14,$08,$61,$00,$f3,$ac
hint_6510:
; --- unverified ---
    move.b d2,d1
    bra.w sub_58ba
hint_6516:
; --- unverified ---
    tst.b (a1)
    bmi.w hint_6a94
hint_651c:
; --- unverified ---
    bsr.s hint_6520
hint_651e:
; --- unverified ---
    bra.s hint_6516
hint_6520:
; --- unverified ---
    moveq #0,d2
    move.b (a1)+,d2
    bne.s hint_652c
hint_6526:
; --- unverified ---
    bsr.w hint_6a94
hint_652a:
; --- unverified ---
    bra.s hint_6530
hint_652c:
; --- unverified ---
    bsr.w sub_6a76
hint_6530:
; --- unverified ---
    lea str_6556(pc),a0
    move.b (a1)+,d1
    bsr.w loc_6a5e
hint_653a:
; --- unverified ---
    bsr.w hint_6256
hint_653e:
    dc.b    $3f,$07,$3e,$19,$45,$fa,$23,$c4,$d4,$d9
hint_6548:
; --- unverified ---
    move.b (a2)+,d2
    bsr.w hint_6aaa
hint_654e:
; --- unverified ---
    dbf d7,hint_6548
hint_6552:
; --- unverified ---
    move.w (sp)+,d7
    rts
str_6556:
    dc.b    $73,$73,$70,$00,$73,$66,$63,$00,$64,$66,$63,$00,$76,$62,$72,$00
    dc.b    $6d,$73,$70,$00,$69,$73,$70,$00
    dc.b    "cacr",0
    dc.b    "caar",0
    dc.b    "mmusr",0
    dc.b    $74,$63,$00,$74,$74,$30,$00,$74,$74,$31,$00,$63,$72,$70,$00,$73
    dc.b    $72,$70,$00
    dc.b    "fpcr",0
    dc.b    "fpsr",0
    dc.b    "fpiar",0
    dc.b    $00
pcref_65a2:
    dc.b    $00,$00,$00,$03,$00,$0a,$ff,$00
pcref_65aa:
    dc.b    $00,$00,$00,$03,$00,$0a,$03,$01,$00,$00,$00,$5c,$00,$03,$00,$03
    dc.b    $00,$5e,$03,$02,$00,$00,$00,$5d,$ff,$00
pcref_65c4:
    dc.b    $00,$00,$00,$03,$00,$0a,$03,$04,$00,$03,$00,$62,$03,$01,$00,$00
    dc.b    $00,$5c,$03,$06,$00,$01,$00,$6e,$00,$03,$00,$03,$00,$5e,$03,$05
    dc.b    $00,$03,$00,$66,$03,$02,$00,$00,$00,$5d,$03,$07,$00,$03,$00,$6a
    dc.b    $ff,$00
pcref_65f6:
    dc.b    $00,$00,$00,$03,$00,$0a,$04,$01,$00,$00,$00,$5c,$06,$08,$00,$01
    dc.b    $00,$70,$07,$0c,$00,$07,$00,$7e,$00,$03,$00,$03,$00,$5e,$04,$02
    dc.b    $00,$00,$00,$5d,$09,$09,$00,$03,$00,$72,$03,$0d,$00,$07,$00,$86
    dc.b    $00,$05,$00,$03,$00,$66,$03,$06,$00,$01,$00,$6e,$06,$0a,$00,$03
    dc.b    $00,$76,$00,$04,$00,$03,$00,$62,$03,$07,$00,$03,$00,$6a,$02,$0b
    dc.b    $00,$03,$00,$7a,$ff,$00
pcref_664c:
    dc.b    $00,$0e,$00,$01,$01,$68,$02,$0f,$00,$03,$01,$6a,$02,$10,$00,$03
    dc.b    $01,$6e,$ff,$00
str_6660:
    dc.b    $73
str_6661:
    dc.b    $6e,$61,$6e,$00
str_6665:
    dc.b    "infinity",0
sub_666e:
; --- unverified ---
    bsr.w sub_6a6a
hint_6672:
; --- unverified ---
    move.l (a1),d2
    bra.w hint_6a9a
hint_6678:
; --- unverified ---
    bsr.w sub_6a6a
hint_667c:
; --- unverified ---
    move.l (a1),d2
    bsr.w hint_6a9a
hint_6682:
; --- unverified ---
    move.l 4(a1),d2
    bra.w hint_6a9a
hint_668a:
; --- unverified ---
    beq.s hint_6698
hint_668c:
; --- unverified ---
    move.b (a0)+,d1
    bsr.w sub_58ba
hint_6692:
; --- unverified ---
    move.b (a0)+,d1
    bra.w sub_58ba
hint_6698:
; --- unverified ---
    addq.l #2,a0
    bsr.w sub_6a82
hint_669e:
; --- unverified ---
    bra.w sub_6a82
hint_66a2:
; --- unverified ---
    lea str_66ec(pc),a0
    btst #15,d4
    bsr.s hint_668a
hint_66ac:
; --- unverified ---
    btst #14,d4
    bsr.s hint_668a
hint_66b2:
; --- unverified ---
    moveq #83,d1
    btst #13,d4
    bne.s hint_66bc
hint_66ba:
    dc.b    $72,$55
hint_66bc:
; --- unverified ---
    bsr.w sub_58ba
hint_66c0:
; --- unverified ---
    moveq #77,d1
    btst #12,d4
    bne.s hint_66ca
hint_66c8:
    dc.b    $72,$49
hint_66ca:
; --- unverified ---
    bsr.w sub_58ba
hint_66ce:
    dc.b    $74,$04
hint_66d0:
; --- unverified ---
    btst #4,d4
    bsr.s hint_66de
hint_66d6:
; --- unverified ---
    add.b d4,d4
    dbf d2,hint_66d0
hint_66dc:
; --- unverified ---
    rts
hint_66de:
; --- unverified ---
    beq.s hint_66e6
hint_66e0:
; --- unverified ---
    move.b (a0)+,d1
    bra.w sub_58ba
hint_66e6:
; --- unverified ---
    addq.l #1,a0
    bra.w sub_6a82
str_66ec:
; --- unverified ---
    addq.b #2,49(a0,d5.w)
    addq.w #4,a6
    addq.w #5,(a6)
    chk.l d0,d1
pcref_66f6:
    bra.w hint_6264
hint_66fa:
; --- unverified ---
    bra.s sub_6708
    dc.b    $60,$0a,$60,$08,$60,$06,$60,$04,$60,$02,$4e,$71
sub_6708:
; --- unverified ---
    moveq #27,d1
    rts
hint_670c:
    dc.b    $24,$6b,$00,$38,$3c,$2b,$00,$06
hint_6714:
; --- unverified ---
    tst.b 53(a3)
    bne.s hint_672e
hint_671a:
; --- unverified ---
    moveq #8,d2
    move.l a2,d0
    bsr.w hint_7ef8
hint_6722:
; --- unverified ---
    bne.s hint_6744
hint_6724:
; --- unverified ---
    move.l a2,d2
    bsr.w hint_6a9a
hint_672a:
; --- unverified ---
    moveq #0,d2
    bra.s hint_6748
hint_672e:
; --- unverified ---
    move.l a2,d2
    bsr.w hint_6a9a
hint_6734:
; --- unverified ---
    bsr.w sub_6a82
hint_6738:
; --- unverified ---
    move.l a2,d0
    move.b 53(a3),d2
    bsr.w hint_7ef8
hint_6742:
; --- unverified ---
    beq.s hint_6748
hint_6744:
; --- unverified ---
    bsr.w sub_7bd8
hint_6748:
; --- unverified ---
    bsr.w sub_6a76
hint_674c:
; --- unverified ---
    moveq #32,d1
    cmpa.l app_exec_base_0054(a6),a2
    bne.s hint_6756
hint_6754:
    dc.b    $72,$3e
hint_6756:
; --- unverified ---
    bsr.w sub_58ba
hint_675a:
; --- unverified ---
    bsr.w hint_69f0
hint_675e:
; --- unverified ---
    move.l a2,-(sp)
    bsr.w loc_5836
hint_6764:
; --- unverified ---
    bsr.w hint_6a94
hint_6768:
; --- unverified ---
    movea.l (sp)+,a2
    subq.b #1,d6
    bne.s hint_6714
hint_676e:
; --- unverified ---
    rts
hint_6770:
; --- unverified ---
    bsr.s hint_67c2
hint_6772:
    dc.b    $55,$8a
hint_6774:
; --- unverified ---
    move.l a2,56(a3)
    moveq #-1,d0
    rts
hint_677c:
; --- unverified ---
    bsr.s hint_67c2
hint_677e:
; --- unverified ---
    addq.l #2,a2
    bra.s hint_6774
pcref_6782:
; --- unverified ---
    bra.w hint_670c
    dc.b    $60,$0a,$60,$18,$60,$4c,$60,$42,$60,$e0,$60,$ea,$30,$2b,$00,$06
    dc.b    $d0,$40,$48,$c0,$91,$ab,$00,$38,$70,$ff,$4e,$75
sub_67a2:
    dc.b    $20,$2b,$00,$38,$52,$80,$08,$80,$00,$00
    dc.b    "$@<+",0
    dc.b    $06
hint_67b2:
; --- unverified ---
    bsr.w sub_6964
hint_67b6:
; --- unverified ---
    subq.b #1,d6
    bne.s hint_67b2
hint_67ba:
; --- unverified ---
    move.l a2,56(a3)
    moveq #-1,d1
    rts
hint_67c2:
; --- unverified ---
    move.l 56(a3),d0
    addq.l #1,d0
    bclr #0,d0
    movea.l d0,a2
    rts
hint_67d0:
; --- unverified ---
    bsr.s hint_67c2
hint_67d2:
; --- unverified ---
    bsr.w sub_6964
hint_67d6:
; --- unverified ---
    bra.s hint_67ba
hint_67d8:
; --- unverified ---
    bsr.s hint_67c2
hint_67da:
; --- unverified ---
    bsr.w sub_3bd6
hint_67de:
; --- unverified ---
    bra.s hint_67ba
hint_67e0:
    dc.b    $24,$6b,$00,$38,$3c,$2b,$00,$06,$38,$2b,$00,$36,$53,$46
hint_67ee:
; --- unverified ---
    bsr.w hint_68ec
hint_67f2:
; --- unverified ---
    dbeq d6,hint_67ee
hint_67f6:
; --- unverified ---
    bne.s hint_6808
hint_67f8:
; --- unverified ---
    tst.w d6
    bmi.s hint_6808
hint_67fc:
; --- unverified ---
    bsr.w loc_5836
hint_6800:
; --- unverified ---
    bsr.w hint_6a94
hint_6804:
; --- unverified ---
    dbf d6,hint_67fc
hint_6808:
; --- unverified ---
    rts
hint_680a:
; --- unverified ---
    cmpa.l 342(a6),a2 ; app+$156
    beq.s hint_6828
hint_6810:
; --- unverified ---
    cmpi.b #$a,-(a2)
    bne.s hint_680a
hint_6816:
; --- unverified ---
    cmpa.l 342(a6),a2 ; app+$156
    beq.s hint_6824
hint_681c:
; --- unverified ---
    cmpi.b #$a,-(a2)
    bne.s hint_6816
hint_6822:
    dc.b    $52,$8a
hint_6824:
    dc.b    $53,$44,$70,$ff
hint_6828:
; --- unverified ---
    rts
hint_682a:
; --- unverified ---
    moveq #0,d0
    rts
pcref_682e:
; --- unverified ---
    bra.w hint_67e0
    dc.b    $60,$32,$60,$46,$60,$06,$60,$64,$60,$ee,$60,$ec
sub_683e:
; --- unverified ---
    movea.l 56(a3),a2
    move.w 54(a3),d4
    bsr.s hint_680a
hint_6848:
; --- unverified ---
    beq.s hint_6862
hint_684a:
; --- unverified ---
    move.l a2,-(sp)
    bsr.w hint_582c
hint_6850:
; --- unverified ---
    bsr.w loc_5836
hint_6854:
; --- unverified ---
    movea.l (sp)+,a2
    move.w d4,54(a3)
    move.l a2,56(a3)
    bsr.w hint_68ec
hint_6862:
; --- unverified ---
    moveq #0,d0
    rts
hint_6866:
    dc.b    $24,$6b,$00,$38,$34,$2b,$00,$06,$38,$2b,$00,$36,$53,$42
hint_6874:
; --- unverified ---
    bsr.s hint_680a
hint_6876:
; --- unverified ---
    dbeq d2,hint_6874
hint_687a:
; --- unverified ---
    bra.s hint_6892
hint_687c:
    dc.b    $24,$6b,$00,$38,$38,$2b,$00,$36,$34,$2b,$00,$06,$53,$42
hint_688a:
; --- unverified ---
    bsr.s hint_68d8
hint_688c:
; --- unverified ---
    beq.s hint_68d4
hint_688e:
; --- unverified ---
    dbf d2,hint_688a
hint_6892:
; --- unverified ---
    move.l a2,56(a3)
    move.w d4,54(a3)
    moveq #-1,d0
    rts
hint_689e:
    dc.b    $24,$6b,$00,$38,$38,$2b,$00,$36,$34,$2b,$00,$06,$53,$42
hint_68ac:
; --- unverified ---
    bsr.s hint_68d8
hint_68ae:
; --- unverified ---
    beq.s hint_68d4
hint_68b0:
; --- unverified ---
    dbf d2,hint_68ac
hint_68b4:
; --- unverified ---
    move.l a2,-(sp)
    bsr.w hint_5814
hint_68ba:
; --- unverified ---
    bsr.w loc_5836
hint_68be:
; --- unverified ---
    movea.l (sp)+,a2
    bsr.s hint_68ec
hint_68c2:
; --- unverified ---
    movea.l 56(a3),a2
    move.w 54(a3),d4
    bsr.s hint_68d8
hint_68cc:
    dc.b    $27,$4a,$00,$38,$37,$44,$00,$36
hint_68d4:
; --- unverified ---
    moveq #0,d0
    rts
hint_68d8:
; --- unverified ---
    cmpa.l 346(a6),a2 ; app+$15A
    beq.w hint_6962
hint_68e0:
; --- unverified ---
    cmpi.b #$a,(a2)+
    bne.s hint_68d8
hint_68e6:
; --- unverified ---
    addq.w #1,d4
    moveq #-1,d0
    rts
hint_68ec:
; --- unverified ---
    cmpa.l 346(a6),a2 ; app+$15A
    beq.s hint_6962
hint_68f2:
; --- unverified ---
    tst.b 1412(a6) ; app+$584
    beq.s hint_6914
hint_68f8:
; --- unverified ---
    bmi.s hint_6908
hint_68fa:
; --- unverified ---
    moveq #0,d1
    move.w d4,d1
    move.l a2,-(sp)
    bsr.w sub_6ace
hint_6904:
; --- unverified ---
    movea.l (sp)+,a2
    bra.s hint_690e
hint_6908:
; --- unverified ---
    move.w d4,d2
    bsr.w hint_6aa2
hint_690e:
; --- unverified ---
    bsr.w sub_6a82
hint_6912:
    dc.b    $76,$00
hint_6914:
; --- unverified ---
    cmpa.l 346(a6),a2 ; app+$15A
    beq.s hint_6962
hint_691a:
; --- unverified ---
    move.b (a2)+,d1
    cmp.b #$d,d1
    beq.s hint_6914
hint_6922:
; --- unverified ---
    cmp.b #$a,d1
    beq.s hint_6952
hint_6928:
; --- unverified ---
    cmp.b #$9,d1
    beq.s hint_6936
hint_692e:
; --- unverified ---
    bsr.w sub_58ba
hint_6932:
; --- unverified ---
    addq.w #1,d3
    bra.s hint_6914
hint_6936:
; --- unverified ---
    move.w d3,d2
    moveq #0,d1
    move.b 53(a3),d1
    subq.w #1,d1
    not.w d1
    and.w d1,d2
    add.b 53(a3),d2
    sub.w d3,d2
    add.w d2,d3
    bsr.w sub_6a76
hint_6950:
; --- unverified ---
    bra.s hint_6914
hint_6952:
; --- unverified ---
    move.l a2,-(sp)
    bsr.w loc_5836
hint_6958:
; --- unverified ---
    movea.l (sp)+,a2
    bsr.w hint_6a94
hint_695e:
    dc.b    $52,$44,$70,$ff
hint_6962:
; --- unverified ---
    rts
sub_6964:
    bsr.w call_typeofmem
loc_6968:
    bne.s loc_69a2
loc_696a:
    lea 10(a2),a2
    bsr.w call_typeofmem
loc_6972:
    lea -10(a2),a2
    bne.s loc_69a2
loc_6978:
    movem.l d4-d7/a3-a5,-(sp)
    movea.l a2,a5
    move.l 174(a6),-(sp) ; app+$AE
    move.l app_freemem_memoryblock(a6),-(sp)
    clr.l 174(a6) ; app+$AE
    clr.l app_freemem_memoryblock(a6)
    bsr.w sub_1c78
loc_6992:
    move.l (sp)+,app_freemem_memoryblock(a6)
    move.l (sp)+,174(a6) ; app+$AE
    movea.l a5,a2
    movem.l (sp)+,d4-d7/a3-a5
    rts
loc_69a2:
    addq.w #2,a2
    rts
sub_69a6:
; --- unverified ---
    move.l a2,d0
    addq.l #1,d0
    bclr #0,d0
    movea.l d0,a2
    bsr.w call_typeofmem
hint_69b4:
; --- unverified ---
    bne.w hint_6a52
hint_69b8:
; --- unverified ---
    lea 10(a2),a2
    bsr.w call_typeofmem
hint_69c0:
; --- unverified ---
    lea -10(a2),a2
    bne.w hint_6a52
hint_69c8:
; --- unverified ---
    movem.l d4-d7/a3-a5,-(sp)
    movea.l a2,a5
    bsr.w sub_1c78
hint_69d2:
    dc.b    $24,$4d,$24,$0c,$94,$8e,$04,$42,$09,$aa,$4c,$df,$38,$f0,$41,$ee
    dc.b    $09,$a8
hint_69e4:
; --- unverified ---
    move.b (a0)+,d1
    bsr.w sub_58ba
hint_69ea:
; --- unverified ---
    dbf d2,hint_69e4
hint_69ee:
; --- unverified ---
    rts
hint_69f0:
; --- unverified ---
    move.l a2,d0
    addq.l #1,d0
    bclr #0,d0
    movea.l d0,a2
    bsr.w call_typeofmem
hint_69fe:
; --- unverified ---
    bne.s hint_6a52
hint_6a00:
; --- unverified ---
    lea 10(a2),a2
    bsr.w call_typeofmem
hint_6a08:
; --- unverified ---
    lea -10(a2),a2
    bne.s hint_6a52
hint_6a0e:
; --- unverified ---
    movem.l d4-d7/a3-a5,-(sp)
    movea.l a2,a5
    bsr.w sub_1c78
hint_6a18:
    dc.b    $24,$4d,$24,$0c,$94,$8e,$04,$42,$09,$aa,$4c,$df,$38,$f0,$41,$ee
    dc.b    $09,$a8
hint_6a2a:
; --- unverified ---
    move.b (a0)+,d1
    cmp.b #$20,d1
    bne.s hint_6a48
hint_6a32:
; --- unverified ---
    move.w d2,-(sp)
    moveq #8,d2
    sub.l a0,d2
    pea 2472(a6) ; app+$9A8
    add.l (sp)+,d2
    bmi.s hint_6a44
hint_6a40:
; --- unverified ---
    bsr.w sub_6a76
hint_6a44:
    dc.b    $34,$1f,$72,$20
hint_6a48:
; --- unverified ---
    bsr.w sub_58ba
hint_6a4c:
; --- unverified ---
    dbf d2,hint_6a2a
hint_6a50:
; --- unverified ---
    rts
hint_6a52:
; --- unverified ---
    addq.l #2,a2
    moveq #42,d1
    bra.w sub_58ba
sub_6a5a:
    lea str_8217(pc),a0
loc_6a5e:
    tst.b d1
    beq.s sub_6a6a
loc_6a62:
    tst.b (a0)+
    bne.s loc_6a62
loc_6a66:
    subq.b #1,d1
    bne.s loc_6a62
sub_6a6a:
    move.b (a0)+,d1
    beq.s loc_6a74
loc_6a6e:
    bsr.w sub_58ba
loc_6a72:
    bra.s sub_6a6a
loc_6a74:
    rts
sub_6a76:
    tst.b d2
loc_6a78:
    beq.s loc_6a80
loc_6a7a:
    bsr.s sub_6a82
loc_6a7c:
    subq.b #1,d2
    bra.s loc_6a78
loc_6a80:
    rts
sub_6a82:
    moveq #32,d1
    bra.w sub_58ba
sub_6a88:
; --- unverified ---
    moveq #42,d1
    bsr.w sub_58ba
hint_6a8e:
; --- unverified ---
    moveq #42,d1
    bra.w sub_58ba
hint_6a94:
; --- unverified ---
    moveq #10,d1
    bra.w sub_58ba
hint_6a9a:
; --- unverified ---
    move.w d2,-(sp)
    swap d2
    bsr.s hint_6aa2
hint_6aa0:
    dc.b    $34,$1f
hint_6aa2:
; --- unverified ---
    move.w d2,-(sp)
    lsr.w #8,d2
    bsr.s hint_6aaa
hint_6aa8:
    dc.b    $34,$1f
hint_6aaa:
; --- unverified ---
    move.w d2,-(sp)
    lsr.b #4,d2
    bsr.s hint_6ab2
hint_6ab0:
    dc.b    $34,$1f
hint_6ab2:
; --- unverified ---
    andi.w #$f,d2
    move.b pcref_6abe(pc,d2.w),d1
    bra.w sub_58ba
pcref_6abe:
    dc.b    "0123456789ABCD"
    dc.b    $45,$46
sub_6ace:
; --- unverified ---
    lea sub_58ba(pc),a2
    lea pcref_6b28(pc),a0
    moveq #-1,d2
    moveq #3,d0
    bra.s loc_6ae8
    dc.b    $45,$fa,$ed,$dc
sub_6ae0:
    lea pcref_6b14(pc),a0
    moveq #1,d2
    moveq #8,d0
loc_6ae8:
    moveq #0,d3
    cmp.l (a0)+,d1
    bcs.s loc_6afa
loc_6aee:
    sub.l -(a0),d1
loc_6af0:
    addq.b #1,d3
    sub.l (a0),d1
    bcc.s loc_6af0
loc_6af6:
    add.l (a0)+,d1
    bra.s loc_6afe
loc_6afa:
    tst.b d2
    bpl.s loc_6b0a
loc_6afe:
    st d2
    addi.b #$30,d3
    exg
    jsr (a2)
loc_6b08:
    exg
loc_6b0a:
    dbf d0,loc_6ae8
loc_6b0e:
    addi.b #$30,d1
    jmp (a2)
pcref_6b14:
    dc.b    $3b,$9a,$ca,$00,$05,$f5,$e1,$00,$00,$98,$96,$80,$00,$0f,$42,$40
    dc.b    $00,$01,$86,$a0
pcref_6b28:
    dc.b    $00,$00,$27,$10,$00,$00,$03,$e8,$00,$00,$00,$64,$00,$00,$00,$0a
sub_6b38:
; --- unverified ---
    move.l a4,-(sp)
    st 2069(a6) ; app+$815
    bsr.w sub_6b70
hint_6b42:
; --- unverified ---
    bne.s hint_6b52
hint_6b44:
; --- unverified ---
    tst.b d1
    bne.s hint_6b52
hint_6b48:
; --- unverified ---
    sf 2069(a6) ; app+$815
    moveq #0,d0
    movea.l (sp)+,a4
    rts
hint_6b52:
; --- unverified ---
    sf 2069(a6) ; app+$815
    moveq #-1,d0
    movea.l (sp)+,a4
    rts
hint_6b5c:
; --- unverified ---
    bsr.s sub_6b70
hint_6b5e:
; --- unverified ---
    bne.s hint_6b64
hint_6b60:
; --- unverified ---
    tst.b d1
    beq.s hint_6b6a
hint_6b64:
; --- unverified ---
    bsr.w sub_5e54
hint_6b68:
    dc.b    $70,$ff
hint_6b6a:
; --- unverified ---
    rts
hint_6b6c:
; --- unverified ---
    bsr.s loc_6b72
hint_6b6e:
; --- unverified ---
    bra.s hint_6b5e
sub_6b70:
    move.b (a4)+,d1
loc_6b72:
    lea 2028(a6),a0 ; app+$7EC
    clr.w (a0)
    lea 2048(a6),a0 ; app+$800
    clr.w (a0)
    clr.b 2068(a6) ; app+$814
    movem.l d4-d7,-(sp)
    bsr.w sub_6c10
loc_6b8a:
    movem.l (sp)+,d4-d7
    tst.w 2028(a6) ; app+$7EC
    bne.s loc_6ba0
loc_6b94:
    tst.w 2048(a6) ; app+$800
    bne.s loc_6ba0
loc_6b9a:
    move.b 2068(a6),d0 ; app+$814
    rts
loc_6ba0:
    moveq #1,d0
    rts
pcref_6ba4:
    dc.b    $13,$2b,$14,$2d,$06,$2a,$07,$2f,$02,$28,$03,$29,$15,$7e,$17,$23
    dc.b    $18,$3f,$0a,$3d,$10,$26,$11,$7c,$11,$21,$12,$5e,$04,$7b,$05,$7d
    dc.b    $fe,$24,$fc,$25,$fa,$40,$f8,$27,$f8,$22,$f6,$5c,$00
pcref_6bd1:
    dcb.b   6,0
    dc.b    $04,$04,$16,$16,$01,$01,$01,$01,$01,$01,$12,$12,$12,$02,$02,$1d
    dc.b    $1e,$1f,$1f
pcref_6bea:
    dc.b    $02,$f0,$02,$36,$02,$54,$02,$58,$02,$5c,$02,$72,$02,$66,$02,$6c
    dc.b    $02,$78,$02,$7e,$02,$48,$02,$4c,$02,$50,$02,$2e,$02,$32,$02,$84
    dc.b    $02,$88,$02,$8c,$02,$bc
sub_6c10:
    lea 2028(a6),a0 ; app+$7EC
    move.w (a0),d0
    addq.w #2,(a0)+
    move.w #$0,0(a0,d0.w)
    moveq #1,d5
    bsr.w sub_6f9c
loc_6c24:
    cmp.b #$2,d5
    bne.s loc_6c3a
loc_6c2a:
    cmp.b #$6,d7
    bcs.w loc_6d88
loc_6c32:
    cmp.b #$19,d7
    bcc.w loc_6d88
loc_6c3a:
    cmp.b #$1,d7
    bne.s loc_6c50
loc_6c40:
    lea 2048(a6),a0 ; app+$800
    move.w (a0),d0
    addq.w #4,(a0)+
    move.l d2,0(a0,d0.w)
    bra.w loc_6d7e
loc_6c50:
    cmp.b #$2,d7
    beq.s loc_6cd0
loc_6c56:
    cmp.b #$4,d7
    beq.w loc_6cf2
loc_6c5e:
    cmp.b #$6,d7
    bcs.w loc_6d9a
loc_6c66:
    cmp.b #$19,d7
    bcc.w loc_6d9a
loc_6c6e:
    cmp.b #$1,d5
    bne.s loc_6ca4
loc_6c74:
    cmp.b #$13,d7
    beq.s loc_6ca4
loc_6c7a:
    cmp.b #$14,d7
    beq.s loc_6ca2
loc_6c80:
    cmp.b #$6,d7
    beq.s loc_6c9c
loc_6c86:
    cmp.b #$17,d7
    beq.s loc_6ca4
loc_6c8c:
    cmp.b #$18,d7
    beq.s loc_6ca4
loc_6c92:
    cmp.b #$15,d7
    bne.w loc_6ba0
loc_6c9a:
    bra.s loc_6ca4
loc_6c9c:
    move.l app_exec_base_0054(a6),d2
    bra.s loc_6c40
loc_6ca2:
    moveq #22,d7
loc_6ca4:
    lea pcref_6bd1(pc),a2
    lea 2028(a6),a0 ; app+$7EC
    move.w (a0),d0
    move.w 0(a0,d0.w),d6
    move.b 0(a2,d6.w),d6
    cmp.b 0(a2,d7.w),d6
    bge.s loc_6cc4
loc_6cbc:
    addq.w #2,(a0)+
    move.w d7,0(a0,d0.w)
    bra.s loc_6cca
loc_6cc4:
    bsr.w loc_6dd0
loc_6cc8:
    bra.s loc_6ca4
loc_6cca:
    moveq #0,d5
    bra.w loc_6d7e
loc_6cd0:
    bsr.w sub_6c10
loc_6cd4:
    lea 2048(a6),a0 ; app+$800
    move.w (a0),d0
    addq.w #4,(a0)+
    move.l d2,0(a0,d0.w)
    cmp.b #$3,d7
    beq.s loc_6cec
loc_6ce6:
    move.b #$2,2068(a6) ; app+$814
loc_6cec:
    moveq #1,d5
    bra.w loc_6d7e
loc_6cf2:
    bsr.w sub_6c10
loc_6cf6:
    cmp.b #$5,d7
    bne.s loc_6ce6
loc_6cfc:
    cmp.b #$2e,d1
    bne.s loc_6d48
loc_6d02:
    move.b (a4)+,d0
    move.b (a4)+,d1
    andi.b #$df,d0
    cmp.b #$42,d0
    beq.s loc_6d24
loc_6d10:
    cmp.b #$57,d0
    beq.s loc_6d34
loc_6d16:
    cmp.b #$4c,d0
    beq.s loc_6d48
loc_6d1c:
    move.b #$7,2068(a6) ; app+$814
    bra.s loc_6d7e
loc_6d24:
    movea.l d2,a2
    bsr.w call_typeofmem
loc_6d2a:
    bne.s loc_6d72
loc_6d2c:
    movea.l d2,a0
    moveq #0,d2
    move.b (a0),d2
    bra.s loc_6d62
loc_6d34:
    btst #0,d2
    bne.s loc_6d72
loc_6d3a:
    movea.l d2,a2
    bsr.w call_typeofmem
loc_6d40:
    bne.s loc_6d72
loc_6d42:
    moveq #0,d2
    move.w (a2),d2
    bra.s loc_6d62
loc_6d48:
    btst #0,d2
    bne.s loc_6d72
loc_6d4e:
    movea.l d2,a2
    bsr.w call_typeofmem
loc_6d54:
    bne.s loc_6d72
loc_6d56:
    addq.l #3,a2
    bsr.w call_typeofmem
loc_6d5c:
    bne.s loc_6d72
loc_6d5e:
    movea.l d2,a0
    move.l (a0),d2
loc_6d62:
    lea 2048(a6),a0 ; app+$800
    move.w (a0),d0
    addq.w #4,(a0)+
    move.l d2,0(a0,d0.w)
    moveq #1,d5
    bra.s loc_6d7e
loc_6d72:
    tst.b 2069(a6) ; app+$815
    bne.s loc_6d62
loc_6d78:
    move.b #$6,2068(a6) ; app+$814
loc_6d7e:
    addq.w #1,d5
    bsr.w sub_6f9c
loc_6d84:
    bra.w loc_6c24
loc_6d88:
    cmp.b #$3,d7
    beq.s loc_6d9a
loc_6d8e:
    cmp.b #$5,d7
    beq.s loc_6d9a
loc_6d94:
    movea.l a0,a4
    move.b -1(a4),d1
loc_6d9a:
    lea pcref_6bd1(pc),a2
loc_6d9e:
    lea 2028(a6),a0 ; app+$7EC
    move.w (a0),d0
    tst.w 0(a0,d0.w)
    beq.s loc_6db0
loc_6daa:
    bsr.w loc_6dd0
loc_6dae:
    bra.s loc_6d9e
loc_6db0:
    subq.w #2,2028(a6) ; app+$7EC
    lea 2048(a6),a0 ; app+$800
    subq.w #4,(a0)
    move.w (a0)+,d0
    move.l 0(a0,d0.w),d2
    rts
sub_6dc2:
    move.w (sp)+,d1
loc_6dc4:
    move.w #$4,(a0)
    move.b #$8,2068(a6) ; app+$814
    rts
loc_6dd0:
    lea 2048(a6),a0 ; app+$800
    subq.w #4,(a0)
    bcs.s loc_6dc4
loc_6dd8:
    move.w (a0)+,d0
    move.l 0(a0,d0.w),d2
    move.w d1,-(sp)
    lea 2028(a6),a1 ; app+$7EC
    subq.w #2,(a1)
    move.w (a1)+,d1
    move.w 0(a1,d1.w),d1
    cmp.b #$15,d1
    bcc.s loc_6dfe
loc_6df2:
    subq.w #4,-(a0)
    bcs.s sub_6dc2
loc_6df6:
    move.w (a0)+,d0
    move.l 0(a0,d0.w),d0
    exg
loc_6dfe:
    lea pcref_6bea(pc),a1
    add.w d1,d1
    move.w -12(a1,d1.w),d1
    jsr 0(a1,d1.w) ; unresolved_indirect_core:index.brief
loc_6e0c:
    move.w (sp)+,d1
    move.w -(a0),d0
    addq.w #4,(a0)+
    move.l d2,0(a0,d0.w)
    rts
sub_6e18:
; --- unverified ---
    add.l d0,d2
    rts
hint_6e1c:
; --- unverified ---
    sub.l d0,d2
    rts
hint_6e20:
; --- unverified ---
    move.l d7,-(sp)
    bsr.w sub_6f0e
hint_6e26:
; --- unverified ---
    movem.l (sp)+,d7
    beq.s hint_6e30
hint_6e2c:
    dc.b    $1d,$40,$08,$14
hint_6e30:
; --- unverified ---
    rts
hint_6e32:
; --- unverified ---
    and.l d0,d2
    rts
hint_6e36:
; --- unverified ---
    or.l d0,d2
    rts
hint_6e3a:
; --- unverified ---
    eor.l d0,d2
    rts
hint_6e3e:
; --- unverified ---
    lsl.l d0,d2
    rts
hint_6e42:
; --- unverified ---
    lsr.l d0,d2
    rts
hint_6e46:
    dc.b    $b4,$80,$57,$c2
hint_6e4a:
; --- unverified ---
    ext.w d2
    ext.l d2
    rts
hint_6e50:
; --- unverified ---
    cmp.l d0,d2
    slt d2
    bra.s hint_6e4a
hint_6e56:
; --- unverified ---
    cmp.l d0,d2
    sgt d2
    bra.s hint_6e4a
hint_6e5c:
; --- unverified ---
    cmp.l d0,d2
    sne d2
    bra.s hint_6e4a
hint_6e62:
; --- unverified ---
    cmp.l d0,d2
    sle d2
    bra.s hint_6e4a
hint_6e68:
; --- unverified ---
    cmp.l d0,d2
    sge d2
    bra.s hint_6e4a
hint_6e6e:
; --- unverified ---
    not.l d2
    rts
hint_6e72:
; --- unverified ---
    neg.l d2
    rts
hint_6e76:
; --- unverified ---
    movem.l d0-d1/a0,-(sp)
    move.l 1404(a6),d1 ; app+$57C
    beq.s hint_6ea2
hint_6e80:
; --- unverified ---
    movea.l 1408(a6),a0 ; app+$580
    cmp.l (a0),d2
    bcs.s hint_6e98
hint_6e88:
; --- unverified ---
    subq.l #1,d1
    bra.s hint_6e90
hint_6e8c:
; --- unverified ---
    cmp.l (a0),d2
    bcs.s hint_6e96
hint_6e90:
; --- unverified ---
    addq.l #8,a0
    dbeq d1,hint_6e8c
hint_6e96:
    dc.b    $51,$88
hint_6e98:
    dc.b    $24,$28,$00,$04
hint_6e9c:
; --- unverified ---
    movem.l (sp)+,d0-d1/a0
    rts
hint_6ea2:
; --- unverified ---
    moveq #0,d2
    bra.s hint_6e9c
sub_6ea6:
    movem.l d0-d1/a0,-(sp)
    move.l 1404(a6),d1 ; app+$57C
    beq.s loc_6ed2
loc_6eb0:
    movea.l 1408(a6),a0 ; app+$580
    cmp.l 4(a0),d2
    bcs.s loc_6ed2
loc_6eba:
    subq.l #1,d1
    bra.s loc_6ec4
loc_6ebe:
    cmp.l 4(a0),d2
    bcs.s loc_6ecc
loc_6ec4:
    addq.l #8,a0
    dbeq d1,loc_6ebe
loc_6eca:
    bne.s loc_6ed2
loc_6ecc:
    move.l -8(a0),d2
    bra.s loc_6ed4
loc_6ed2:
    moveq #0,d2
loc_6ed4:
    movem.l (sp)+,d0-d1/a0
    rts
sub_6eda:
; --- unverified ---
    move.l d2,d6
    eor.l d0,d6
    tst.l d2
    bgt.s hint_6ee4
hint_6ee2:
    dc.b    $44,$82
hint_6ee4:
; --- unverified ---
    tst.l d0
    bgt.s hint_6eea
hint_6ee8:
    dc.b    $44,$80
hint_6eea:
; --- unverified ---
    move.l d2,d3
    swap d3
    mulu.w d0,d2
    swap d0
    tst.w d3
    beq.s hint_6efa
hint_6ef6:
; --- unverified ---
    swap d0
    bra.s hint_6f00
hint_6efa:
; --- unverified ---
    tst.w d0
    beq.s hint_6f06
hint_6efe:
    dc.b    $48,$43
hint_6f00:
    dc.b    $c0,$c3,$48,$40,$d4,$80
hint_6f06:
; --- unverified ---
    tst.l d6
    bpl.s hint_6f0c
hint_6f0a:
    dc.b    $44,$82
hint_6f0c:
; --- unverified ---
    rts
sub_6f0e:
    tst.l d0
    beq.s loc_6f5c
loc_6f12:
    move.l d2,d6
    eor.l d0,d6
    move.l d6,-(sp)
    move.l d2,-(sp)
    tst.l d0
    bpl.s loc_6f20
loc_6f1e:
    neg.l d0
loc_6f20:
    tst.l d2
    bpl.s loc_6f26
loc_6f24:
    neg.l d2
loc_6f26:
    moveq #31,d6
    move.l d0,d7
    moveq #0,d0
loc_6f2c:
    add.l d7,d7
    dbcs d6,loc_6f2c
loc_6f32:
    roxr.l #1,d7
    subi.w #$1f,d6
    neg.w d6
loc_6f3a:
    add.l d0,d0
    cmp.l d7,d2
    bcs.s loc_6f44
loc_6f40:
    addq.l #1,d0
    sub.l d7,d2
loc_6f44:
    lsr.l #1,d7
    dbf d6,loc_6f3a
loc_6f4a:
    move.l (sp)+,d6
    bpl.s loc_6f50
loc_6f4e:
    neg.l d2
loc_6f50:
    move.l (sp)+,d6
    bpl.s loc_6f56
loc_6f54:
    neg.l d0
loc_6f56:
    exg
    cmp.b d0,d0
    rts
loc_6f5c:
    moveq #3,d0
    rts
sub_6f60:
    tst.b d1
    bmi.s loc_6f98
loc_6f64:
    cmp.b #$2e,d1
    beq.s loc_6f98
loc_6f6a:
    cmp.b #$30,d1
    bcs.s loc_6f94
loc_6f70:
    cmp.b #$3a,d1
    bcs.s loc_6f98
loc_6f76:
    cmp.b #$40,d1
    bcs.s loc_6f94
loc_6f7c:
    cmp.b #$5b,d1
    bcs.s loc_6f98
loc_6f82:
    cmp.b #$5f,d1
    beq.s loc_6f98
loc_6f88:
    cmp.b #$61,d1
    bcs.s loc_6f94
loc_6f8e:
    cmp.b #$7b,d1
    bcs.s loc_6f98
loc_6f94:
    moveq #-1,d0
    rts
loc_6f98:
    moveq #0,d0
    rts
sub_6f9c:
    movem.l d5-d6/a1-a2,-(sp)
    move.l a4,-(sp)
    moveq #0,d7
    lea pcref_6ba4(pc),a0
loc_6fa8:
    move.b (a0)+,d7
    beq.s loc_6fba
loc_6fac:
    cmp.b (a0)+,d1
    bne.s loc_6fa8
loc_6fb0:
    tst.b d7
    bmi.w loc_7088
loc_6fb6:
    bra.w loc_703a
loc_6fba:
    cmp.b #$3c,d1
    beq.s loc_700e
loc_6fc0:
    cmp.b #$3e,d1
    beq.s loc_7024
loc_6fc6:
    moveq #0,d2
    cmp.b #$3a,d1
    bcc.s loc_6fd4
loc_6fce:
    cmp.b #$30,d1
    bcc.s loc_7044
loc_6fd4:
    moveq #1,d7
    bsr.s sub_6f60
loc_6fd8:
    bne.s loc_700a
loc_6fda:
    lea -1(a4),a1
    moveq #0,d2
loc_6fe0:
    addq.w #1,d2
    move.b (a4)+,d1
    bsr.w sub_6f60
loc_6fe8:
    beq.s loc_6fe0
loc_6fea:
    bsr.w loc_71f2
loc_6fee:
    bne.s loc_6ff6
loc_6ff0:
    move.l (a0),d2
    bra.w loc_7084
loc_6ff6:
    move.l a1,-(sp)
    bsr.w sub_75b2
loc_6ffc:
    movea.l (sp)+,a1
    beq.w loc_7084
loc_7002:
    movea.l a1,a4
    moveq #0,d2
    bra.w loc_7112
loc_700a:
    moveq #25,d7
    bra.s loc_703c
loc_700e:
    moveq #12,d7
    move.b (a4)+,d1
    cmp.b #$3c,d1
    beq.s loc_7038
loc_7018:
    cmp.b #$3e,d1
    beq.s loc_7020
loc_701e:
    bra.s loc_702e
loc_7020:
    moveq #11,d7
    bra.s loc_703a
loc_7024:
    moveq #13,d7
    move.b (a4)+,d1
    cmp.b #$3e,d1
    beq.s loc_7038
loc_702e:
    cmp.b #$3d,d1
    bne.s loc_703c
loc_7034:
    addq.w #2,d7
    bra.s loc_703a
loc_7038:
    subq.w #4,d7
loc_703a:
    move.b (a4)+,d1
loc_703c:
    movea.l (sp)+,a0
    movem.l (sp)+,d5-d6/a1-a2
    rts
loc_7044:
    moveq #0,d2
    subq.l #1,a4
    moveq #1,d7
    bra.w loc_7112
loc_704e:
    move.b (a4)+,d1
    cmp.b #$30,d1
    bcs.w loc_713e
loc_7058:
    cmp.b #$3a,d1
    bcc.w loc_713e
loc_7060:
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
    bcc.s loc_7084
loc_707e:
    cmp.b #$30,d1
    bcc.s loc_7060
loc_7084:
    moveq #1,d7
    bra.s loc_703c
loc_7088:
    neg.b d7
    ext.w d7
    moveq #0,d2
    moveq #1,d0
    exg
    jmp 0(pc,d0.w) ; unresolved_indirect_core:pcindex.brief
    bra.s loc_7112
    bra.s loc_70c6
    bra.s loc_70ea
    bra.s loc_70a0
    bra.s loc_704e
loc_70a0:
    moveq #4,d0
    move.b d1,d3
loc_70a4:
    move.b (a4)+,d1
    cmp.b #$a,d1
    beq.w loc_713e
loc_70ae:
    cmp.b d3,d1
    bne.s loc_70ba
loc_70b2:
    move.b (a4)+,d1
    cmp.b d3,d1
    beq.s loc_70ba
loc_70b8:
    bra.s loc_703c
loc_70ba:
    subq.b #1,d0
    bcs.w loc_714c
loc_70c0:
    lsl.l #8,d2
    move.b d1,d2
    bra.s loc_70a4
loc_70c6:
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s loc_713e
loc_70ce:
    cmp.b #$2,d1
    bcc.s loc_713e
loc_70d4:
    add.l d2,d2
    bcs.s loc_714c
loc_70d8:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s loc_7130
loc_70e2:
    cmp.b #$2,d1
    bcs.s loc_70d4
loc_70e8:
    bra.s loc_7130
loc_70ea:
    move.b (a4),d0
    subi.b #$30,d0
    bcs.s loc_7138
loc_70f2:
    cmp.b #$9,d0
    bcc.s loc_7138
loc_70f8:
    move.b d0,d1
    addq.l #1,a4
loc_70fc:
    lsl.l #3,d2
    bcs.s loc_714c
loc_7100:
    or.b d1,d2
    move.b (a4)+,d1
    subi.b #$30,d1
    bcs.s loc_7130
loc_710a:
    cmp.b #$9,d1
    bcs.s loc_70fc
loc_7110:
    bra.s loc_7130
loc_7112:
    lea pcref_7150(pc),a0
    moveq #0,d1
    move.b (a4)+,d1
    bmi.s loc_713e
loc_711c:
    move.b 0(a0,d1.w),d1
    bmi.s loc_713e
loc_7122:
    lsl.l #4,d2
    or.b d1,d2
    move.b (a4)+,d1
    bmi.s loc_7130
loc_712a:
    move.b 0(a0,d1.w),d1
    bpl.s loc_7122
loc_7130:
    move.b -1(a4),d1
loc_7138:
    moveq #64,d1
    bra.w loc_6fd4
loc_713e:
    moveq #4,d0
loc_7140:
    tst.b 2068(a6) ; app+$814
    bne.s loc_7130
loc_7146:
    move.b d0,2068(a6) ; app+$814
    bra.s loc_7130
loc_714c:
    moveq #5,d0
    bra.s loc_7140
pcref_7150:
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$0a,$0b,$0c,$0d,$0e,$0f,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$0a,$0b,$0c,$0d,$0e,$0f,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
    dc.b    $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
sub_71d0:
    move.b 1(a1),d0
    subi.b #$30,d0
    bcs.s loc_7202
loc_71da:
    cmp.b #$a,d0
    bcc.s loc_7202
loc_71e0:
    ext.w d0
    add.w d0,d0
    lea pcref_7356(pc),a0
    move.w 0(a0,d0.w),d0
    lea 0(a6,d0.w),a0
    bra.s loc_726a
loc_71f2:
    move.b (a1),d0
    andi.b #$df,d0
    cmp.w #$2,d2
    beq.s loc_7206
loc_71fe:
    bcc.w loc_728a
loc_7202:
    moveq #-1,d0
    rts
loc_7206:
    lea 48(a6),a0 ; app+$30
    cmp.b #$41,d0
    beq.s loc_726e
loc_7210:
    lea 16(a6),a0 ; app+$10
    cmp.b #$44,d0
    beq.s loc_726e
loc_721a:
    cmp.b #$53,d0
    beq.s loc_7242
loc_7220:
    cmp.b #$4d,d0
    beq.s sub_71d0
loc_7226:
    cmp.b #$50,d0
    bne.s loc_7202
loc_722c:
    lea app_exec_base_0054(a6),a0
    cmpi.b #$43,1(a1)
    beq.s loc_726a
loc_7238:
    cmpi.b #$63,1(a1)
    beq.s loc_726a
loc_7240:
    bra.s loc_7202
loc_7242:
    move.b 1(a1),d0
    andi.b #$df,d0
    lea 88(a6),a0 ; app+$58
    cmp.b #$52,d0
    beq.s loc_726a
loc_7254:
    cmp.b #$50,d0
    bne.s loc_7202
loc_725a:
    lea 76(a6),a0 ; app+$4C
    btst #5,90(a6) ; app+$5A
    beq.s loc_726a
loc_7266:
    lea 80(a6),a0 ; app+$50
loc_726a:
    moveq #0,d0
    rts
loc_726e:
    move.b 1(a1),d0
    subi.b #$30,d0
    bcs.s loc_7202
loc_7278:
    cmp.b #$8,d0
    bcc.s loc_7202
loc_727e:
    andi.w #$f,d0
    add.w d0,d0
    add.w d0,d0
    adda.w d0,a0
    bra.s loc_726a
loc_728a:
    movem.l d1/d3/a1,-(sp)
    move.b #$df,d3
    cmp.w #$3,d2
    bne.s loc_72c6
loc_7298:
    move.b (a1)+,d1
    and.b d3,d1
    cmp.b #$53,d1
    bne.s loc_72c2
loc_72a2:
    move.b (a1)+,d1
    and.b d3,d1
    cmp.b #$53,d1
    bne.s loc_72c2
loc_72ac:
    move.b (a1)+,d1
    and.b d3,d1
    cmp.b #$50,d1
    bne.s loc_72c2
loc_72b6:
    lea 80(a6),a0 ; app+$50
    moveq #0,d1
loc_72bc:
    movem.l (sp)+,d1/d3/a1
    rts
loc_72c2:
    moveq #-1,d1
    bra.s loc_72bc
loc_72c6:
    cmp.w #$4,d2
    beq.s loc_72ce
loc_72cc:
    bcs.s loc_72c2
loc_72ce:
    clr.l -(sp)
    movea.l sp,a0
    move.b (a1)+,d1
    and.b d3,d1
    move.b d1,(a0)+
    move.b (a1)+,d1
    and.b d3,d1
    move.b d1,(a0)+
    move.b (a1)+,d1
    and.b d3,d1
    move.b d1,(a0)+
    move.b (a1)+,d1
    and.b d3,d1
    move.b d1,(a0)+
    move.l (sp)+,d1
    cmp.l #$434f4445,d1 ; 'CODE'
    beq.s loc_7304
loc_72f4:
    cmp.l #$48554e4b,d1 ; 'HUNK'
    bne.s loc_72c2
loc_72fc:
    cmp.w #$4,d2
    bne.s loc_7310
loc_7302:
    bra.s loc_72c2
loc_7304:
    cmp.w #$4,d2
    bne.s loc_72c2
loc_730a:
    lea 170(a6),a0 ; app+$AA
    bra.s loc_72bc
loc_7310:
    move.w d2,d0
    subq.w #4,d0
    moveq #0,d3
loc_7316:
    move.b (a1)+,d1
    subi.b #$30,d1
    bcs.s loc_72c2
loc_731e:
    cmp.b #$a,d1
    bcc.s loc_72c2
loc_7324:
    mulu.w #$a,d3
    ext.w d1
    add.w d1,d3
    subq.w #1,d0
    bne.s loc_7316
loc_7330:
    lea dat_88f6(pc),a0
loc_7334:
    subq.w #1,d3
    bmi.s loc_72c2
loc_7338:
    tst.l (a0)
    beq.s loc_72c2
loc_733c:
    movea.l (a0),a0
    adda.l a0,a0
    adda.l a0,a0
    tst.w d3
    bne.s loc_7334
loc_7346:
    addq.l #4,a0
    move.l a0,2024(a6) ; app+$7E8
    lea 2024(a6),a0 ; app+$7E8
    moveq #0,d1
    bra.w loc_72bc
pcref_7356:
    dc.b    $07,$d4,$06,$06,$06,$50,$06,$9a,$06,$e4,$07,$2e,$07,$d8,$07,$dc
    dc.b    $07,$e0,$07,$e4
call_typeofmem:
    move.l a2,d0
    andi.l #$ff000000,d0
    bne.s loc_737c
loc_7374:
    cmpa.l #$f80000,a2
    bcc.s loc_7398
loc_737c:
    movem.l d1/a0-a1/a6,-(sp)
    movea.l AbsExecBase,a6
    move.l a2,d0
    move.w #$8000,d0 ; TypeOfMem: address
    movea.l d0,a1 ; TypeOfMem: address
    jsr _LVOTypeOfMem(a6) ; app-$216
loc_7390:
    movem.l (sp)+,d1/a0-a1/a6
    tst.w d0
    beq.s loc_739c
loc_7398:
    moveq #0,d0
    rts
loc_739c:
    moveq #-1,d0
    rts
    dc.b    $02,$00,$00,$fe
sub_73a4:
    cmp.l #$8,d0
    bcs.s loc_73b0
loc_73ac:
    cmp.b d0,d0
    rts
loc_73b0:
    andi.b
    rts
sub_73b6:
    dc.b    $22,$08,$24,$3c,$00,$00,$03,$ee
call_ioerr:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOOpen(a6) ; app-$1E
loc_73c8:
    movea.l (sp)+,a6
    move.l d0,d3
    bne.s loc_73dc
loc_73ce:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOIoErr(a6) ; app-$84
loc_73d8:
    movea.l (sp)+,a6
    moveq #0,d0
loc_73dc:
    eori.b
    rts
loc_73e2:
    move.l a5,d1
    move.l #$3ed,d2
    bra.s call_ioerr
call_seek:
    move.l d3,-(sp)
    move.l d3,d1 ; Seek: file
    moveq #0,d2 ; Seek: position
    moveq #OFFSET_END,d3 ; Seek: mode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOSeek(a6) ; app-$42
loc_73fe:
    movea.l (sp)+,a6
    move.l (sp),d1 ; Seek: file
    moveq #0,d2 ; Seek: position
    moveq #OFFSET_CURRENT,d3 ; Seek: mode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOSeek(a6) ; app-$42
loc_7410:
    movea.l (sp)+,a6
    move.l d0,d4
    move.l (sp),d1 ; Seek: file
    moveq #0,d2 ; Seek: position
    moveq #OFFSET_BEGINNING,d3 ; Seek: mode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOSeek(a6) ; app-$42
loc_7424:
    movea.l (sp)+,a6
    move.l (sp)+,d3
    rts
call_read:
    move.l d3,-(sp)
    move.l d3,d1 ; Read: file
    move.l a0,d2 ; Read: buffer
    move.l d4,d3 ; Read: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_743c:
    movea.l (sp)+,a6
    move.l (sp)+,d3
    rts
call_ioerr_7442:
    move.l d3,-(sp)
    move.l d3,d1 ; Write: file
    move.l a0,d2 ; Write: buffer
    move.l d4,d3 ; Write: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOWrite(a6) ; app-$30
loc_7454:
    movea.l (sp)+,a6
    move.l (sp)+,d3
    tst.l d0
    bge.s loc_7470
loc_745c:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOIoErr(a6) ; app-$84
loc_7466:
    movea.l (sp)+,a6
    move.w d0,-(sp)
    bsr.s call_close
loc_746c:
    move.w (sp)+,d0
    rts
loc_7470:
    moveq #0,d0
    rts
call_close:
    move.l d3,d1 ; Close: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_7480:
    movea.l (sp)+,a6
    rts
sub_7484:
    dc.b    $2d,$43,$01,$74
sub_7488:
    lea 3080(a6),a0 ; app+$C08
    move.l a0,376(a6) ; app+$178
    rts
hint_7492:
; --- unverified ---
    bsr.s loc_74c0
hint_7494:
; --- unverified ---
    move.l 372(a6),d3 ; app+$174
    bra.s call_close
loc_749a:
    bsr.w call_replymsg
loc_749e:
    beq.w loc_75a0
loc_74a2:
    lea 3592(a6),a0 ; app+$E08
    movea.l 376(a6),a1 ; app+$178
    cmpa.l a0,a1
    bne.s loc_74b6
loc_74ae:
    move.w d1,-(sp)
    bsr.s loc_74c0
loc_74b2:
    move.w (sp)+,d1
    bra.s loc_749a
loc_74b6:
    move.b d1,(a1)+
    move.l a1,376(a6) ; app+$178
    bra.w loc_75a6
loc_74c0:
    move.l 376(a6),d0 ; app+$178
    lea 3080(a6),a0 ; app+$C08
    sub.l a0,d0
    beq.s loc_74e6
loc_74cc:
    movem.l d3-d4,-(sp)
    move.l 372(a6),d3 ; app+$174
    lea 3080(a6),a0 ; app+$C08
    move.l d0,d4
    bsr.w call_ioerr_7442
loc_74de:
    beq.s loc_74e6
loc_74e0:
    bclr #7,228(a6) ; app+$E4
loc_74e6:
    movem.l (sp)+,d3-d4
    bra.s sub_7488
call_ioerr_74ec:
    move.l a0,-(sp)
    bsr.s call_close_752c
loc_74f0:
    move.l (sp),d1 ; Open: name
    move.l #$3ee,d2 ; Open: accessMode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOOpen(a6) ; app-$1E
loc_7502:
    movea.l (sp)+,a6
    tst.l d0
    bne.s loc_751a
loc_7508:
    addq.l #4,sp
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOIoErr(a6) ; app-$84
loc_7514:
    movea.l (sp)+,a6
    tst.l d0
    rts
loc_751a:
    move.l d0,app_write_file(a6)
    lea 2180(a6),a1 ; app+$884
    movea.l (sp)+,a0
loc_7524:
    move.b (a0)+,(a1)+
    bne.s loc_7524
loc_7528:
    moveq #0,d0
    rts
call_close_752c:
    move.l app_write_file(a6),d1
    beq.s loc_7542
loc_7532:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_753c:
    movea.l (sp)+,a6
    clr.l app_write_file(a6)
loc_7542:
    rts
loc_7544:
    tst.b 228(a6) ; app+$E4
    bpl.s loc_75a6
loc_754a:
    cmp.b #$a,d1
    bne.s loc_7558
loc_7550:
    tst.b d3
    beq.s loc_7570
loc_7554:
    moveq #32,d1
    bra.s loc_7570
loc_7558:
    cmp.b #$9,d1
    bne.s loc_7562
loc_755e:
    tst.b d3
    beq.s loc_7570
loc_7562:
    move.b d1,d0
    andi.b #$7f,d0
    cmp.b #$20,d0
    bcc.s loc_7570
loc_756e:
    moveq #32,d1
loc_7570:
    tst.l 372(a6) ; app+$174
    bne.w loc_749a
loc_7578:
    move.b d1,-(sp)
    move.l app_write_file(a6),d1 ; Write: file
    move.l sp,d2 ; Write: buffer
    moveq #1,d3 ; Write: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOWrite(a6) ; app-$30
loc_758c:
    movea.l (sp)+,a6
    move.b (sp)+,d1
    subq.l #1,d0
    bne.s loc_75a0
loc_7594:
    cmp.b #$a,d1
    bne.s loc_75a6
loc_759a:
    bsr.w call_replymsg
loc_759e:
    bne.s loc_75a6
loc_75a0:
    bclr #7,228(a6) ; app+$E4
loc_75a6:
    movem.l (sp)+,d0-d3/d7/a0-a2
    rts
sub_75ac:
; --- unverified ---
    tst.l app_write_file(a6)
    rts
sub_75b2:
    tst.b 1414(a6) ; app+$586
    beq.s sub_75fa
loc_75b8:
    lea 3180(a6),a0 ; app+$C6C
    move.b d2,(a0)
    moveq #0,d0
    move.b (a0)+,d0
    move.b #$5f,(a0)+
    subq.w #1,d0
    bmi.w loc_7c2a
loc_75cc:
    move.b (a1)+,(a0)+
    dbf d0,loc_75cc
loc_75d2:
    lea 3182(a6),a1 ; app+$C6E
    bsr.w sub_75fa
loc_75da:
    beq.w loc_7c2a
loc_75de:
    lea 3180(a6),a1 ; app+$C6C
    move.b (a1)+,d2
    addq.b #1,d2
    bsr.w sub_75fa
loc_75ea:
    beq.w loc_7c2a
loc_75ee:
    lea 3180(a6),a1 ; app+$C6C
    move.b (a1)+,d2
    addq.b #1,d2
    move.b #$40,(a1)
sub_75fa:
    movem.l d1/d4/a2,-(sp)
    lea 174(a6),a2 ; app+$AE
    tst.l (a2)
    beq.w loc_76c2
loc_7608:
    moveq #0,d0
    move.b d2,d0
    cmp.w 2070(a6),d0 ; app+$816
    ble.s loc_7616
loc_7612:
    move.w 2070(a6),d0 ; app+$816
loc_7616:
    tst.b 230(a6) ; app+$E6
    bne.w loc_76ca
loc_761e:
    clr.l -(sp)
    movea.l sp,a0
    moveq #1,d1
    move.b (a1)+,(a0)+
    cmp.b d1,d0
    beq.s loc_7644
loc_762a:
    addq.b #1,d1
    move.b (a1)+,(a0)+
    cmp.b d1,d0
    beq.s loc_7644
loc_7632:
    addq.b #1,d1
    move.b (a1)+,(a0)+
    cmp.b d1,d0
    beq.s loc_7644
loc_763a:
    addq.b #1,d1
    move.b (a1)+,(a0)+
    cmp.b d1,d0
    beq.s loc_7644
loc_7642:
    addq.b #1,d1
loc_7644:
    move.l (sp)+,d1
loc_7646:
    move.l (a2),d3
    beq.s loc_765c
loc_764a:
    asl.l #2,d3
    movea.l d3,a2
    lea 4(a2),a0
    cmpi.l #$3f0,(a0)+
    bne.s loc_7646
loc_765a:
    moveq #1,d3
loc_765c:
    beq.s loc_76c2
loc_765e:
    move.l (a0)+,d3
    beq.s loc_7646
loc_7662:
    asl.l #2,d3
    cmp.l (a0),d1
    bne.s loc_76bc
loc_7668:
    move.w d3,d4
    cmp.w 2070(a6),d3 ; app+$816
    ble.s loc_7674
loc_7670:
    move.w 2070(a6),d4 ; app+$816
loc_7674:
    cmp.w d4,d0
    bgt.s loc_76bc
loc_7678:
    cmp.w #$4,d4
    bne.s loc_7684
loc_767e:
    cmp.w d4,d0
    ble.s loc_76ac
loc_7682:
    bra.s loc_76bc
loc_7684:
    movem.l d0-d1/a0-a1,-(sp)
    addq.l #4,a0
    subq.l #4,d0
    subq.l #4,d4
loc_768e:
    move.b (a0)+,d1
    beq.s loc_76b8
loc_7692:
    cmp.b (a1)+,d1
    bne.s loc_76b8
loc_7696:
    subq.w #1,d0
    beq.s loc_76a0
loc_769a:
    subq.w #1,d4
    bne.s loc_768e
loc_769e:
    bra.s loc_76b8
loc_76a0:
    subq.l #1,d4
    beq.s loc_76a8
loc_76a4:
    tst.b (a0)
    bne.s loc_76b8
loc_76a8:
    movem.l (sp)+,d0-d1/a0-a1
loc_76ac:
    move.l 0(a0,d3.l),d2
    movem.l (sp)+,d1/d4/a2
    moveq #0,d0
    rts
loc_76b8:
    movem.l (sp)+,d0-d1/a0-a1
loc_76bc:
    lea 4(a0,d3.l),a0
    bra.s loc_765e
loc_76c2:
    movem.l (sp)+,d1/d4/a2
    moveq #-1,d0
    rts
loc_76ca:
    move.l (a2),d3
    beq.s loc_76e0
loc_76ce:
    asl.l #2,d3
    movea.l d3,a2
    lea 4(a2),a0
    cmpi.l #$3f0,(a0)+
    bne.s loc_76ca
loc_76de:
    moveq #1,d3
loc_76e0:
    beq.s loc_76c2
loc_76e2:
    move.b (a1),d1
    bsr.w sub_772e
loc_76e8:
    move.l (a0)+,d3
    beq.s loc_76ca
loc_76ec:
    asl.l #2,d3
    move.w d3,d4
    cmp.w 2070(a6),d3 ; app+$816
    ble.s loc_76fa
loc_76f6:
    move.w 2070(a6),d4 ; app+$816
loc_76fa:
    cmp.w d4,d0
    bgt.s loc_7728
loc_76fe:
    movem.l d0-d1/a0-a1,-(sp)
loc_7702:
    move.b (a0)+,d1
    beq.s loc_7724
loc_7706:
    bsr.s sub_772e
loc_7708:
    move.b d1,-(sp)
    move.b (a1)+,d1
    bsr.s sub_772e
loc_770e:
    cmp.b (sp)+,d1
    bne.s loc_7724
loc_7712:
    subq.w #1,d0
    beq.s loc_771c
loc_7716:
    subq.w #1,d4
    bne.s loc_7702
loc_771a:
    bra.s loc_7724
loc_771c:
    subq.l #1,d4
    beq.s loc_76a8
loc_7720:
    tst.b (a0)
    beq.s loc_76a8
loc_7724:
    movem.l (sp)+,d0-d1/a0-a1
loc_7728:
    lea 4(a0,d3.l),a0
    bra.s loc_76e8
sub_772e:
    cmp.b #$61,d1
    bcs.s loc_773e
loc_7734:
    cmp.b #$7b,d1
    bcc.s loc_773e
loc_773a:
    andi.b #$df,d1
loc_773e:
    rts
call_unloadseg_7740:
    bsr.w sub_7de0
loc_7744:
    move.l 174(a6),d1 ; app+$AE
    cmp.l pcref_0018(pc),d1
    beq.s loc_775a
loc_774e:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOUnLoadSeg(a6) ; app-$9C
loc_7758:
    movea.l (sp)+,a6
loc_775a:
    clr.l 174(a6) ; app+$AE
    move.l app_allocmem_memoryblock(a6),d0
    beq.s loc_777e
loc_7764:
    movea.l d0,a1 ; FreeMem: memoryBlock
    move.l 1420(a6),d0 ; app+$58C
    lsl.l #2,d0 ; FreeMem: byteSize
    addq.l #4,d0
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_7778:
    movea.l (sp)+,a6
    clr.l app_allocmem_memoryblock(a6)
loc_777e:
    rts
call_close_7780:
    tst.l 350(a6) ; app+$15E
    bne.w loc_7ace
loc_7788:
    move.l a0,-(sp)
    bsr.s call_unloadseg_7740
loc_778c:
    suba.l a4,a4
    lea dat_88f6(pc),a5
    move.l (sp)+,d1 ; Open: name
    move.l #MODE_OLDFILE,d2 ; Open: accessMode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOOpen(a6) ; app-$1E
loc_77a4:
    movea.l (sp)+,a6
    move.l d0,d4
    beq.w loc_784e
loc_77ac:
    moveq #26,d1
    bsr.w sub_6a5a
loc_77b2:
    bsr.w call_read_7b98
loc_77b6:
    cmp.l #$3f3,d0
    bne.w loc_7840
loc_77c0:
    bsr.w call_read_7b98
loc_77c4:
    beq.s loc_77cc
loc_77c6:
    bsr.w sub_7bd0
loc_77ca:
    bra.s loc_77c0
loc_77cc:
    bsr.w call_read_7b98
loc_77d0:
    bsr.w call_read_7b98
loc_77d4:
    move.l d0,d5
    bsr.w call_read_7b98
loc_77da:
    sub.l d5,d0
    addq.l #1,d0
    bsr.w sub_7bd0
loc_77e2:
    bsr.w call_read_7b98
loc_77e6:
    cmp.l #$3f0,d0
    beq.w loc_788a
loc_77f0:
    cmp.l #$3f1,d0
    beq.w loc_7916
loc_77fa:
    cmp.l #$3ec,d0
    beq.s loc_7860
loc_7802:
    cmp.l #$3f2,d0
    bne.s loc_7822
loc_780a:
    bsr.w call_read_7b98
loc_780e:
    tst.l d1
    bne.s loc_77e6
loc_7812:
    move.l d4,d1 ; Close: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_781e:
    movea.l (sp)+,a6
    rts
loc_7822:
    movea.l (a5),a5
    adda.l a5,a5
    adda.l a5,a5
    cmp.l #$3e9,d0
    beq.s loc_7870
loc_7830:
    cmp.l #$3ea,d0
    beq.s loc_7870
loc_7838:
    cmp.l #$3eb,d0
    beq.s loc_7882
loc_7840:
    move.l d4,d1 ; Close: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_784c:
    movea.l (sp)+,a6
loc_784e:
    rts
loc_7850:
    move.l d4,d1 ; Close: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_785c:
    movea.l (sp)+,a6
    rts
loc_7860:
    bsr.w call_read_7b98
loc_7864:
    beq.w loc_77e2
loc_7868:
    addq.l #1,d0
    bsr.w sub_7bd0
loc_786e:
    bra.s loc_7860
loc_7870:
    bsr.w call_read_7b98
loc_7874:
    andi.l #$3fffffff,d0
    bsr.w sub_7bd0
loc_787e:
    bra.w loc_77e2
loc_7882:
    bsr.w call_read_7b98
loc_7886:
    bra.w loc_77e2
loc_788a:
    bsr.w call_read_7b3e
loc_788e:
    bsr.w sub_7b70
loc_7892:
    move.l d0,d5
    subq.l #4,d5
    moveq #2,d6
loc_7898:
    bsr.w sub_7b7c
loc_789c:
    beq.s loc_78aa
loc_789e:
    add.l d0,d6
    addq.l #2,d6
    addq.l #1,d0
    bsr.w sub_7b88
loc_78a8:
    bra.s loc_7898
loc_78aa:
    asl.l #2,d6
    move.l d5,d0
    bsr.w sub_7bca
loc_78b2:
    bsr.w call_read_78ce
loc_78b6:
    beq.s loc_7850
loc_78b8:
    lea 8(a4),a0
    move.l a5,d1
    addq.l #4,d1
loc_78c0:
    move.l (a0)+,d0
    beq.w loc_77e2
loc_78c6:
    asl.l #2,d0
    adda.l d0,a0
    add.l d1,(a0)+
    bra.s loc_78c0
call_read_78ce:
    moveq #8,d0
    add.l d6,d0 ; AllocMem: byteSize
    moveq #0,d1 ; AllocMem: attributes
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_78de:
    movea.l (sp)+,a6
    tst.l d0
    beq.s loc_7914
loc_78e4:
    movea.l a4,a0
    movea.l d0,a4
    move.l a0,d1
    bne.s loc_78f0
loc_78ec:
    lea 174(a6),a0 ; app+$AE
loc_78f0:
    addq.l #4,d0
    asr.l #2,d0
    move.l d0,(a0)
    moveq #8,d1
    add.l d6,d1
    move.l d1,(a4)+
    clr.l (a4)
    move.l d4,d1 ; Read: file
    move.l a4,d2 ; Read: buffer
    addq.l #4,d2
    move.l d6,d3 ; Read: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_7910:
    movea.l (sp)+,a6
    move.l a4,d0
loc_7914:
    rts
loc_7916:
    bsr.w call_read_7b98
loc_791a:
    lea -16(sp),sp
    asl.l #2,d0
    move.l d0,(sp)
    bsr.w call_seek_7bb6
loc_7926:
    move.l d0,4(sp)
    add.l d0,(sp)
    bsr.w call_read_7b98
loc_7930:
    move.l d0,8(sp)
    bsr.w call_read_7b98
loc_7938:
    bsr.w sub_7ab6
loc_793c:
    bne.w loc_79fe
loc_7940:
    move.l 8(sp),d1
    lea 4(a5,d1.l),a0
    move.l a0,d1
    bsr.w sub_7a80
loc_794e:
    beq.w loc_79fe
loc_7952:
    movea.l a0,a3
    move.l a3,12(sp)
    move.l 4(sp),d0
    addq.l #4,d0
    move.l d0,40(a3)
    cmpi.l #$53524320,36(a3) ; 'SRC '
    beq.s loc_7998
loc_796c:
    bsr.w call_read_7b98
loc_7970:
    bsr.w sub_7a0c
loc_7974:
    bsr.w call_seek_7bb6
loc_7978:
    move.l d0,44(a3)
    sub.l (sp),d0
    neg.l d0
    move.l d0,56(a3)
    cmpi.l #$4c494e45,36(a3) ; 'LINE'
    beq.s loc_79f8
loc_798e:
    bsr.w call_read_7b98
loc_7992:
    addq.l #4,44(a3)
    bra.s loc_79fa
loc_7998:
    moveq #9,d0
    bsr.w sub_7bd0
loc_799e:
    bsr.w call_read_7b3e
loc_79a2:
    bsr.w sub_7b7c
loc_79a6:
    move.l d0,56(a3)
    bsr.w sub_7b7c
loc_79ae:
    bsr.w sub_7b7c
loc_79b2:
    move.l d0,4(sp)
    bsr.w sub_7b70
loc_79ba:
    add.l 4(sp),d0
    move.l d0,44(a3)
    move.l 4(sp),d3
    addq.w #4,a3
    bra.s loc_79da
loc_79ca:
    move.b (a0)+,d0
    beq.s loc_79e4
loc_79ce:
    cmp.b #$3a,d0
    beq.s loc_79da
loc_79d4:
    cmp.b #$2f,d0
    bne.s loc_79de
loc_79da:
    move.l a0,4(sp)
loc_79de:
    dbf d3,loc_79ca
loc_79e2:
    clr.b (a0)
loc_79e4:
    movea.l 4(sp),a0
    moveq #30,d0
loc_79ea:
    move.b (a0)+,(a3)+
    dbeq d0,loc_79ea
loc_79f0:
    movea.l 12(sp),a3
    move.l 56(a3),d0
loc_79f8:
    asr.l #3,d0
loc_79fa:
    move.l d0,52(a3)
loc_79fe:
    move.l (sp),d0
    lea 16(sp),sp
    bsr.w sub_7bca
loc_7a08:
    bra.w loc_77e2
sub_7a0c:
    pea 34(a3)
    move.l a3,-(sp)
    addq.w #4,a3
    bra.s loc_7a44
loc_7a16:
    move.l d0,-(sp)
    bsr.w call_read_7b98
loc_7a1c:
    moveq #3,d1
loc_7a1e:
    rol.l #8,d0
    cmp.b #$3a,d0
    beq.s loc_7a38
loc_7a26:
    cmp.b #$2f,d0
    beq.s loc_7a38
loc_7a2c:
    move.b d0,(a3)+
    cmpa.l 8(sp),a3
    bls.s loc_7a3e
loc_7a34:
    subq.l #1,a3
    bra.s loc_7a3e
loc_7a38:
    movea.l 4(sp),a3
    addq.w #4,a3
loc_7a3e:
    dbf d1,loc_7a1e
loc_7a42:
    move.l (sp)+,d0
loc_7a44:
    dbf d0,loc_7a16
loc_7a48:
    clr.b (a3)
    movea.l (sp)+,a3
    addq.l #4,sp
    rts
sub_7a50:
    movem.l d1/a1,-(sp)
    asl.l #2,d0
    bra.s loc_7a66
loc_7a58:
    cmpi.b #$3a,(a0)+
    beq.s loc_7a66
loc_7a5e:
    cmpi.b #$2f,-1(a0)
    bne.s loc_7a6a
loc_7a66:
    movea.l a0,a1
    move.l d0,d1
loc_7a6a:
    dbf d0,loc_7a58
loc_7a6e:
    movem.l (sp)+,d0/a0
loc_7a72:
    move.b (a1)+,(a0)+
    beq.s loc_7a7e
loc_7a76:
    subq.l #1,d0
    dbls d1,loc_7a72
loc_7a7c:
    clr.b (a1)
loc_7a7e:
    rts
sub_7a80:
    movem.l d0-d1,-(sp)
    moveq #60,d0
    bsr.w alloc_memory_8160
loc_7a8a:
    movem.l (sp)+,d0-d1
    beq.w loc_7ab4
loc_7a92:
    clr.l 40(a0)
    move.l d0,36(a0)
    move.l d1,48(a0)
    lea 1400(a6),a1 ; app+$578
loc_7aa2:
    move.l (a1),d0
    beq.s loc_7ab0
loc_7aa6:
    exg
    cmp.l 48(a1),d1
    bcc.s loc_7aa2
loc_7aae:
    exg
loc_7ab0:
    move.l d0,(a0)
    move.l a0,(a1)
loc_7ab4:
    rts
sub_7ab6:
    cmp.l #$48434c4e,d0 ; 'HCLN'
    beq.s loc_7acc
loc_7abe:
    cmp.l #$4c494e45,d0 ; 'LINE'
    beq.s loc_7acc
loc_7ac6:
    cmp.l #$53524320,d0 ; 'SRC '
loc_7acc:
    rts
loc_7ace:
    lea pcref_0018(pc),a4
    move.l (a4),174(a6) ; app+$AE
loc_7ad6:
    move.l (a4),d0
    beq.s loc_7b3c
loc_7ada:
    asl.l #2,d0
    movea.l d0,a4
    lea 4(a4),a2
    cmpi.l #$3f1,(a2)+
    bne.s loc_7ad6
loc_7aea:
    addq.l #8,a2
    move.l (a2),d0
    bsr.s sub_7ab6
loc_7af0:
    bne.s loc_7ad6
loc_7af2:
    move.l -4(a2),d1
    bsr.s sub_7a80
loc_7af8:
    beq.s loc_7b3c
loc_7afa:
    movea.l a0,a3
    move.l 4(a2),d1
    asl.l #2,d1
    lea 8(a2,d1.l),a0
    cmpi.l #$4c494e45,36(a3) ; 'LINE'
    beq.s loc_7b14
loc_7b10:
    move.l (a0)+,d0
    bra.s loc_7b20
loc_7b14:
    move.l -8(a2),d0
    sub.l 4(a2),d0
    subq.l #3,d0
    asr.l #1,d0
loc_7b20:
    move.l d0,52(a3)
    move.l a0,44(a3)
    move.l 4(a2),d0
    moveq #30,d1
    lea 8(a2),a0
    lea 4(a3),a1
    bsr.w sub_7a50
loc_7b3a:
    bra.s loc_7ad6
loc_7b3c:
    rts
call_read_7b3e:
    bsr.w call_seek_7bb6
loc_7b42:
    move.l d0,-(sp)
    move.l d4,d1 ; Read: file
    lea 3080(a6),a0 ; Read: buffer
    move.l a0,d2 ; Read: buffer
    move.l #$200,d3 ; Read: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_7b5c:
    movea.l (sp)+,a6
    tst.l d0
    bge.s loc_7b64
loc_7b62:
    moveq #0,d0
loc_7b64:
    lea 3080(a6),a0 ; app+$C08
    movea.l (sp)+,a1
    move.l d0,d2
    add.l a0,d2
    rts
sub_7b70:
    move.l a0,d0
    pea 3080(a6) ; app+$C08
    sub.l (sp)+,d0
    add.l a1,d0
    rts
sub_7b7c:
    cmp.l a0,d2
    beq.s loc_7b84
loc_7b80:
    move.l (a0)+,d0
    rts
loc_7b84:
    bsr.s call_read_7b3e
loc_7b86:
    bra.s sub_7b7c
sub_7b88:
    tst.l d0
    beq.s loc_7b96
loc_7b8c:
    move.l d0,-(sp)
    bsr.s sub_7b7c
loc_7b90:
    moveq #-1,d0
    add.l (sp)+,d0
    bne.s loc_7b8c
loc_7b96:
    rts
call_read_7b98:
    move.l d4,d1 ; Read: file
    lea 2472(a6),a0 ; Read: buffer
    move.l a0,d2 ; Read: buffer
    moveq #4,d3 ; Read: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_7bac:
    movea.l (sp)+,a6
    move.l d0,d1
    move.l 2472(a6),d0 ; app+$9A8
    rts
call_seek_7bb6:
    moveq #0,d2
    moveq #0,d3
loc_7bba:
    move.l d4,d1 ; Seek: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOSeek(a6) ; app-$42
loc_7bc6:
    movea.l (sp)+,a6
    rts
sub_7bca:
    moveq #-1,d3
    move.l d0,d2
    bra.s loc_7bba
sub_7bd0:
    moveq #0,d3
    move.l d0,d2
    asl.l #2,d2
    bra.s loc_7bba
sub_7bd8:
    dc.b    $20,$40,$20,$18,$e5,$80,$53,$80
hint_7be0:
; --- unverified ---
    move.b (a0)+,d1
    beq.s hint_7bee
hint_7be4:
; --- unverified ---
    bsr.w sub_58ba
hint_7be8:
; --- unverified ---
    subq.b #1,d2
    dbeq d0,hint_7be0
hint_7bee:
; --- unverified ---
    rts
hint_7bf0:
; --- unverified ---
    movem.l d1/a0,-(sp)
    movea.l d0,a0
    move.l (a0)+,d0
    asl.l #2,d0
    subq.l #1,d0
    cmp.w #$f,d0
    bcs.s hint_7c04
hint_7c02:
    dc.b    $70,$0f
hint_7c04:
; --- unverified ---
    move.b (a0)+,d1
    beq.s hint_7c0e
hint_7c08:
; --- unverified ---
    move.b d1,(a4)+
    dbf d0,hint_7c04
hint_7c0e:
; --- unverified ---
    movem.l (sp)+,d1/a0
    rts
hint_7c14:
    dc.b    $20,$4c,$26,$04,$53,$83
hint_7c1a:
; --- unverified ---
    move.b (a0)+,d1
    beq.s hint_7c26
hint_7c1e:
; --- unverified ---
    bsr.w sub_58ba
hint_7c22:
; --- unverified ---
    dbf d3,hint_7c1a
hint_7c26:
; --- unverified ---
    rts
hint_7c28:
    dc.b    $b0,$00
loc_7c2a:
    rts
call_close_7c2c:
    bsr.w sub_1288
loc_7c30:
    movem.l d2-d5/a0/a2-a4,-(sp)
    moveq #0,d5
    moveq #0,d2
    lea 1400(a6),a2 ; app+$578
loc_7c3c:
    bsr.w sub_7d6c
loc_7c40:
    beq.w loc_7c4c
loc_7c44:
    add.l 52(a2),d5
    addq.l #1,d2
    bra.s loc_7c3c
loc_7c4c:
    move.l d5,d0
    beq.w loc_7d68
loc_7c52:
    asl.l #3,d0
    bsr.w alloc_memory_8160
loc_7c58:
    beq.w loc_7d68
loc_7c5c:
    movea.l a0,a3
    movea.l a0,a4
    tst.l 350(a6) ; app+$15E
    bne.s loc_7c84
loc_7c66:
    move.l #dat_136d,d1 ; Open: name
    move.l #MODE_OLDFILE,d2 ; Open: accessMode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOOpen(a6) ; app-$1E
loc_7c7c:
    movea.l (sp)+,a6
    move.l d0,d4
    beq.w loc_7d62
loc_7c84:
    lea 1400(a6),a2 ; app+$578
loc_7c88:
    movea.l 16(sp),a0
    bsr.w sub_7d6c
loc_7c90:
    beq.w loc_7d36
loc_7c94:
    tst.l 350(a6) ; app+$15E
    beq.s loc_7cbc
loc_7c9a:
    movea.l 44(a2),a0
    move.l 52(a2),d0
    cmpi.l #$48434c4e,36(a2) ; 'HCLN'
    bne.s loc_7cb6
loc_7cac:
    bsr.w sub_7d9e
loc_7cb0:
    bra.s loc_7c88
loc_7cb2:
    move.l (a0)+,(a4)+
    move.l (a0)+,(a4)+
loc_7cb6:
    subq.l #1,d0
    bcc.s loc_7cb2
loc_7cba:
    bra.s loc_7c88
loc_7cbc:
    move.l 40(a2),d0
    bsr.w sub_7bca
loc_7cc4:
    bsr.w call_read_7b98
loc_7cc8:
    cmp.l 36(a2),d0
    bne.w loc_7d54
loc_7cd0:
    move.l 44(a2),d0
    bsr.w sub_7bca
loc_7cd8:
    move.l 56(a2),d3
    cmpi.l #$48434c4e,36(a2) ; 'HCLN'
    bne.s loc_7d10
loc_7ce6:
    move.l d3,d0
    bsr.w alloc_memory_8160
loc_7cec:
    beq.w loc_7d54
loc_7cf0:
    move.l d4,d1 ; Read: file
    move.l a0,d2 ; Read: buffer
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_7cfe:
    movea.l (sp)+,a6
    movea.l d2,a0
    bsr.w sub_7d9e
loc_7d06:
    movea.l d2,a0
    bsr.w free_memory
loc_7d0c:
    bra.w loc_7c88
loc_7d10:
    move.l d4,d1 ; Read: file
    move.l a4,d2 ; Read: buffer
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_7d1e:
    movea.l (sp)+,a6
    move.l 52(a2),d0
    move.l 48(a2),d1
    bra.s loc_7d2e
loc_7d2a:
    addq.l #4,a4
    add.l d1,(a4)+
loc_7d2e:
    subq.l #1,d0
    bcc.s loc_7d2a
loc_7d32:
    bra.w loc_7c88
loc_7d36:
    tst.l 350(a6) ; app+$15E
    bne.s loc_7d4a
loc_7d3c:
    move.l d4,d1 ; Close: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_7d48:
    movea.l (sp)+,a6
loc_7d4a:
    movea.l a3,a0
    move.l d5,d0
loc_7d4e:
    movem.l (sp)+,d2-d5/a1-a4
    rts
loc_7d54:
    move.l d4,d1 ; Close: file
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_7d60:
    movea.l (sp)+,a6
loc_7d62:
    movea.l a3,a0
    bsr.w free_memory
loc_7d68:
    moveq #0,d0
    bra.s loc_7d4e
sub_7d6c:
    move.l (a2),d0
    beq.w loc_7d96
loc_7d72:
    movea.l d0,a2
    movem.l a0/a2,-(sp)
    addq.w #4,a2
loc_7d7a:
    move.b (a0)+,d1
    bsr.w sub_772e
loc_7d80:
    move.b d1,d0
    move.b (a2)+,d1
    bsr.w sub_772e
loc_7d88:
    cmp.b d0,d1
    bne.s loc_7d98
loc_7d8c:
    tst.b d0
    bne.s loc_7d7a
loc_7d90:
    movem.l (sp)+,a0/a2
    moveq #1,d0
loc_7d96:
    rts
loc_7d98:
    movem.l (sp)+,a0/a2
    bra.s sub_7d6c
sub_7d9e:
    move.l a3,-(sp)
    suba.l a1,a1
    movea.l 48(a2),a3
    move.l 52(a2),d1
    add.l d1,d1
    bra.s loc_7dba
loc_7dae:
    move.b (a0)+,d0
    beq.s loc_7dc2
loc_7db2:
    ext.w d0
loc_7db4:
    adda.w d0,a1
loc_7db6:
    move.l a1,(a4)+
    exg
loc_7dba:
    subq.l #1,d1
    bcc.s loc_7dae
loc_7dbe:
    movea.l (sp)+,a3
    rts
loc_7dc2:
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0)+,d0
    bne.s loc_7db4
loc_7dca:
    tst.w d0
    bne.s loc_7db4
loc_7dce:
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0)+,d0
    swap d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0)+,d0
    adda.l d0,a1
    bra.s loc_7db6
sub_7de0:
    clr.l 1400(a6) ; app+$578
    move.l 1400(a6),d0 ; app+$578
    beq.s loc_7df6
loc_7dea:
    movea.l d0,a0
    move.l (a0),-(sp)
    bsr.w free_memory
loc_7df2:
    move.l (sp)+,d0
    bne.s loc_7dea
loc_7df6:
    rts
sub_7df8:
    move.l (a1),d1
    beq.s loc_7e0e
loc_7dfc:
    asl.l #2,d1
    movea.l d1,a1
    lea 4(a1),a0
    cmpi.l #$3f0,(a0)+
    bne.s sub_7df8
loc_7e0c:
    moveq #1,d1
loc_7e0e:
    rts
alloc_memory:
    lea 174(a6),a1 ; app+$AE
    moveq #0,d0
loc_7e16:
    bsr.s sub_7df8
loc_7e18:
    beq.s loc_7e2a
loc_7e1a:
    addq.l #3,d0
    move.l (a0),d1
    asl.l #2,d1
    lea 8(a0,d1.l),a0
    bne.s loc_7e1a
loc_7e26:
    subq.l #3,d0
    bra.s loc_7e16
loc_7e2a:
    tst.l d0
    beq.s loc_7e86
loc_7e2e:
    lsr.l #1,d0
    bset #0,d0
    addq.l #2,d0
    move.l d0,1420(a6) ; app+$58C
    asl.l #2,d0 ; AllocMem: byteSize
    addq.l #4,d0
    move.l #$10000,d1 ; AllocMem: attributes
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_7e4e:
    movea.l (sp)+,a6
    move.l d0,app_allocmem_memoryblock(a6)
    beq.s loc_7e86
loc_7e56:
    movem.l d6-d7,-(sp)
    lea 174(a6),a1 ; app+$AE
loc_7e5e:
    bsr.s sub_7df8
loc_7e60:
    beq.s loc_7e82
loc_7e62:
    move.l a1,-(sp)
loc_7e64:
    move.l (a0),d1
    bne.s loc_7e6c
loc_7e68:
    movea.l (sp)+,a1
    bra.s loc_7e5e
loc_7e6c:
    asl.l #2,d1
    move.l 4(a0,d1.l),d0
    move.l a0,-(sp)
    bsr.s sub_7e88
loc_7e76:
    movea.l (sp)+,a0
    beq.s loc_7e7c
loc_7e7a:
    move.l a0,(a1)
loc_7e7c:
    lea 8(a0,d1.l),a0
    bra.s loc_7e64
loc_7e82:
    movem.l (sp)+,d6-d7
loc_7e86:
    rts
sub_7e88:
    movea.l app_allocmem_memoryblock(a6),a1
    move.l 1420(a6),d2 ; app+$58C
    move.l d0,d6
    divu.w d2,d6
    bvc.s loc_7ea8
loc_7e96:
    movem.l d0/d2,-(sp)
    exg
    bsr.w sub_6f0e
loc_7ea0:
    move.l d0,d6
    swap d6
    movem.l (sp)+,d0/d2
loc_7ea8:
    swap d6
    ext.l d6
    bpl.s loc_7eb0
loc_7eae:
    neg.l d6
loc_7eb0:
    add.l d6,d6
    add.l d6,d6
    add.l d2,d2
    add.l d2,d2
loc_7eb8:
    move.l 0(a1,d6.l),d7
    beq.s loc_7ed8
loc_7ebe:
    movea.l d7,a0
    move.l (a0),d7
    asl.l #2,d7
    cmp.l 4(a0,d7.l),d0
    beq.s loc_7ed4
loc_7eca:
    addq.l #4,d6
    cmp.l d6,d2
    bne.s loc_7eb8
loc_7ed0:
    moveq #0,d6
    bra.s loc_7eb8
loc_7ed4:
    movea.l a0,a1
    rts
loc_7ed8:
    lea 0(a1,d6.l),a1
    moveq #-1,d7
    rts
sub_7ee0:
; --- unverified ---
    movem.l d1-d2/d6-d7/a0-a1,-(sp)
    tst.l d0
    bmi.s hint_7eec
hint_7ee8:
; --- unverified ---
    bsr.s sub_7e88
hint_7eea:
; --- unverified ---
    beq.s hint_7ef0
hint_7eec:
; --- unverified ---
    moveq #0,d0
    bra.s hint_7ef2
hint_7ef0:
    dc.b    $20,$09
hint_7ef2:
; --- unverified ---
    movem.l (sp)+,d1-d2/d6-d7/a0-a1
    rts
hint_7ef8:
; --- unverified ---
    tst.l app_allocmem_memoryblock(a6)
    bne.s sub_7ee0
hint_7efe:
; --- unverified ---
    tst.b 355(a6) ; app+$163
    bne.s hint_7f06
hint_7f04:
; --- unverified ---
    rts
hint_7f06:
; --- unverified ---
    cmp.l 364(a6),d0 ; app+$16C
    bcs.s hint_7f2c
hint_7f0c:
; --- unverified ---
    cmp.l 368(a6),d0 ; app+$170
    bhi.s hint_7f2c
hint_7f12:
; --- unverified ---
    movem.l d1/a0,-(sp)
    tst.b 355(a6) ; app+$163
    bmi.s hint_7f44
hint_7f1c:
    dc.b    $20,$6e,$01,$64
hint_7f20:
; --- unverified ---
    move.l (a0)+,d1
    beq.s hint_7f30
hint_7f24:
; --- unverified ---
    cmp.l d0,d1
    bne.s hint_7f20
hint_7f28:
    dc.b    $4c,$df,$01,$02
hint_7f2c:
; --- unverified ---
    moveq #0,d0
    rts
hint_7f30:
; --- unverified ---
    tst.l 360(a6) ; app+$168
    beq.s hint_7f3c
hint_7f36:
; --- unverified ---
    cmpa.l 360(a6),a0 ; app+$168
    bge.s hint_7f28
hint_7f3c:
; --- unverified ---
    move.l d0,-4(a0)
    clr.l (a0)
    bra.s hint_7f28
hint_7f44:
    dc.b    $20,$6e,$01,$64
hint_7f48:
; --- unverified ---
    move.l (a0)+,d1
    beq.s hint_7f28
hint_7f4c:
; --- unverified ---
    cmp.l d1,d0
    bne.s hint_7f48
hint_7f50:
; --- unverified ---
    lea 384(a6),a0 ; app+$180
    move.b #$6c,(a0)+
    move.l d0,d1
    exg
    bsr.w hint_1bbe
hint_7f60:
; --- unverified ---
    exg
    clr.b (a0)
    move.l a0,d1
    lea 380(a6),a0 ; app+$17C
    sub.l a0,d1
    subq.l #1,d1
    asr.l #2,d1
    move.l d1,(a0)
    move.l a0,d0
    movem.l (sp)+,d1/a0
    rts
hint_7f7a:
; --- unverified ---
    sf 1426(a6) ; app+$592
    move.l d0,-(sp)
    bsr.w hint_7ef8
hint_7f84:
; --- unverified ---
    bne.s hint_7fae
hint_7f86:
; --- unverified ---
    move.l (sp),d0
    move.l a0,(sp)
    btst #0,d0
    bne.s hint_7fb2
hint_7f90:
; --- unverified ---
    bsr.w call_typeofmem
hint_7f94:
; --- unverified ---
    bne.s hint_7fb2
hint_7f96:
; --- unverified ---
    movea.l d0,a0
    cmpi.w #$4ef9,(a0)
    bne.s hint_7fb2
hint_7f9e:
; --- unverified ---
    move.l 2(a0),d0
    movea.l (sp),a0
    bsr.w hint_7ef8
hint_7fa8:
; --- unverified ---
    beq.s hint_7fae
hint_7faa:
    dc.b    $50,$ee,$05,$92
hint_7fae:
; --- unverified ---
    addq.w #4,sp
    rts
hint_7fb2:
; --- unverified ---
    movea.l (sp)+,a0
    moveq #0,d0
    rts
call_close_7fb8:
    tst.b 354(a6) ; app+$162
    beq.s loc_7fe0
loc_7fbe:
    move.l dat_0020,d0
    beq.w loc_80aa
loc_7fc8:
    moveq #0,d4
    movea.l d0,a0
    lea 8(a0),a4
    move.l a4,app_freemem_memoryblock(a6)
    tst.b (a0)
    beq.w loc_80aa
loc_7fda:
    clr.b (a0)
    bra.w loc_807c
loc_7fe0:
    moveq #27,d1
    bsr.w sub_6a5a
loc_7fe6:
    move.l #sub_81cb,d1 ; Open: name
    move.l #MODE_OLDFILE,d2 ; Open: accessMode
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOOpen(a6) ; app-$1E
loc_7ffc:
    movea.l (sp)+,a6
    move.l d0,d4
    bne.s loc_801a
loc_8002:
    move.l #dat_81c6,d1 ; Open: name
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOOpen(a6) ; app-$1E
loc_8012:
    movea.l (sp)+,a6
    move.l d0,d4
    beq.w loc_80aa
loc_801a:
    moveq #28,d1
    bsr.w sub_6a5a
loc_8020:
    lea 2472(a6),a0 ; Read: buffer
    move.l d4,d1 ; Read: file
    move.l a0,d2 ; Read: buffer
    moveq #8,d3 ; Read: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_8034:
    movea.l (sp)+,a6
    subq.l #8,d0
    bne.w loc_809a
loc_803c:
    cmpi.l #$420003f0,2472(a6) ; app+$9A8
    bne.s loc_809a
loc_8046:
    move.l 2476(a6),d0 ; app+$9AC
    beq.s loc_809a
loc_804c:
    move.l d0,app_read_length(a6)
    moveq #0,d1 ; AllocMem: attributes
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_805c:
    movea.l (sp)+,a6
    tst.l d0
    beq.s loc_809a
loc_8062:
    move.l d0,app_freemem_memoryblock(a6)
    movea.l d0,a4 ; Read: buffer
    move.l d4,d1 ; Read: file
    move.l a4,d2 ; Read: buffer
    move.l app_read_length(a6),d3 ; Read: length
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVORead(a6) ; app-$2A
loc_807a:
    movea.l (sp)+,a6
loc_807c:
    move.l (a4)+,d1
    beq.s loc_809a
loc_8080:
    asl.l #2,d1
    adda.l d1,a4
    move.w (a4),d1
    ext.l d1
    move.l (a4),d2
    ext.l d2
    asl.l #2,d1
    lea 182(a6),a0 ; app+$B6
    add.l 0(a0,d1.l),d2
    move.l d2,(a4)+
    bra.s loc_807c
loc_809a:
    move.l d4,d1
    beq.s loc_80aa
loc_809e:
    move.l a6,-(sp)
    movea.l app_dos_base(a6),a6
    jsr _LVOClose(a6) ; app-$24
loc_80a8:
    movea.l (sp)+,a6
loc_80aa:
    rts
sub_80ac:
; --- unverified ---
    move.l app_freemem_memoryblock(a6),d0
    beq.s hint_80d0
hint_80b2:
    dc.b    $48,$e7,$40,$80,$c1,$88
hint_80b8:
; --- unverified ---
    move.l (a0),d1
    beq.s hint_80cc
hint_80bc:
; --- unverified ---
    asl.l #2,d1
    cmp.l 4(a0,d1.l),d0
    beq.s hint_80ca
hint_80c4:
; --- unverified ---
    lea 8(a0,d1.l),a0
    bra.s hint_80b8
hint_80ca:
    dc.b    $20,$08
hint_80cc:
    dc.b    $4c,$df,$01,$02
hint_80d0:
; --- unverified ---
    rts
hint_80d2:
; --- unverified ---
    tst.l 174(a6) ; app+$AE
    beq.w hint_8144
hint_80da:
; --- unverified ---
    lea 1506(pc),a2
    bsr.w hint_5eac
hint_80e2:
    dc.b    $4b,$ee,$00,$ae,$7c,$00
hint_80e8:
; --- unverified ---
    move.l (a5),d0
    beq.s hint_80fe
hint_80ec:
; --- unverified ---
    asl.l #2,d0
    movea.l d0,a5
    lea 4(a5),a4
    cmpi.l #$3f0,(a4)+
    bne.s hint_80e8
hint_80fc:
    dc.b    $70,$01
hint_80fe:
; --- unverified ---
    beq.s hint_813c
hint_8100:
; --- unverified ---
    move.l (a4)+,d4
    beq.s hint_80e8
hint_8104:
; --- unverified ---
    asl.l #2,d4
    move.l 0(a4,d4.l),d2
    bsr.w hint_6a9a
hint_810e:
; --- unverified ---
    bsr.w sub_6a82
hint_8112:
; --- unverified ---
    bsr.w hint_7c14
hint_8116:
; --- unverified ---
    lea 4(a4,d4.l),a4
    bsr.w hint_6a94
hint_811e:
; --- unverified ---
    addq.w #1,d6
    cmp.w 6(a3),d6
    bne.s hint_8100
hint_8126:
; --- unverified ---
    bsr.w sub_4120
hint_812a:
; --- unverified ---
    cmp.b #$1b,d1
    beq.s hint_8140
hint_8130:
; --- unverified ---
    moveq #0,d6
    bsr.w call_rectfill
hint_8136:
; --- unverified ---
    clr.l 10(a3)
    bra.s hint_8100
hint_813c:
; --- unverified ---
    bsr.w sub_4120
hint_8140:
; --- unverified ---
    bsr.w sub_5d9c
hint_8144:
; --- unverified ---
    rts
call_setpointer:
    movem.w (a0)+,d0-d3
    exg
    movea.l a0,a1 ; SetPointer: pointer
    movea.l app_closewindow_window(a6),a0 ; SetPointer: window
    move.l a6,-(sp)
    movea.l app_intuition_base(a6),a6
    jsr _LVOSetPointer(a6) ; app-$10E
loc_815c:
    movea.l (sp)+,a6
    rts
alloc_memory_8160:
    addq.l #8,d0
    move.l d0,-(sp)
    moveq #MEMF_PUBLIC,d1 ; AllocMem: attributes
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOAllocMem(a6) ; app-$C6
loc_8170:
    movea.l (sp)+,a6
    move.l (sp)+,d1
    tst.l d0
    beq.s loc_8188
loc_8178:
    movea.l d0,a0
    move.l 202(a6),(a0) ; app+$CA
    move.l a0,202(a6) ; app+$CA
    addq.l #4,a0
    move.l d1,(a0)+
    rts
loc_8188:
    rts
free_memory:
    move.l a0,d0
    beq.s loc_81b4
loc_818e:
    subq.l #8,a0
    lea 202(a6),a1 ; app+$CA
loc_8194:
    cmpa.l (a1),a0
    beq.s loc_81a0
loc_8198:
    tst.l (a1)
    beq.s loc_81b4
loc_819c:
    movea.l (a1),a1
    bra.s loc_8194
loc_81a0:
    move.l (a0),(a1)
    movea.l a0,a1 ; FreeMem: memoryBlock
    move.l 4(a0),d0 ; FreeMem: byteSize
    move.l a6,-(sp)
    movea.l AbsExecBase,a6
    jsr _LVOFreeMem(a6) ; app-$D2
loc_81b2:
    movea.l (sp)+,a6
loc_81b4:
    rts
sub_81b6:
    move.l 202(a6),d0 ; app+$CA
    beq.s loc_81c4
loc_81bc:
    addq.l #8,d0
    movea.l d0,a0
    bsr.s free_memory
loc_81c2:
    bra.s sub_81b6
loc_81c4:
    rts
dat_81c6:
    dc.b    $4c,$49,$42,$53,$3a
sub_81cb:
    dc.b    "monam.libfile",0
openlibrary_libname_81D9:
    dc.b    "intuition.library",0
openlibrary_libname_81EB:
    dc.b    "dos.library",0
openlibrary_libname_81F7:
    dc.b    "graphics.library",0
opendevice_devname:
    dc.b    "console.device",0
str_8217:
    dc.b    "pc = ",0
    dc.b    "sr = ",0
    dc.b    "a7'= ",0
    dc.b    $44,$69,$76,$69,$64
sub_822e:
; --- unverified ---
    bcs.s hint_8250
hint_8230:
    dc.b    $62,$79
hint_8232:
; --- unverified ---
    movea.l 25970(pc),a0
    ble.w $c580
hint_823a:
    dc.b    $4b
hint_823b:
    dc.b    $20
hint_823c:
; --- unverified ---
    bcs.s hint_82b6
hint_823e:
    dc.b    $63,$65
hint_8240:
    dc.b    $70
hint_8241:
    dc.b    $74
hint_8243:
    dc.b    $6f
hint_8244:
    dc.b    $6e
hint_8245:
    dc.b    $00,$54,$52,$41
hint_8249:
    dc.b    $50,$56,$20,$65,$78
hint_824e:
    dc.b    $63
hint_8250:
    dc.b    $70
hint_8251:
    dc.b    $74
hint_8253:
    dc.b    $6f
hint_8254:
    dc.b    $6e
hint_8255:
    dc.b    $00,$50,$72
hint_8258:
    dc.b    $69
hint_8259:
    dc.b    $76
hint_825a:
    dc.b    $69
hint_825b:
; --- unverified ---
    bge.s $82c2
hint_825d:
; --- unverified ---
    beq.s sub_82c4
hint_825f:
    dc.b    $20
hint_8260:
    dc.b    $76,$69,$6f,$6c
hint_8264:
    dc.b    $61,$74
hint_8266:
    dc.b    $69,$6f
hint_8268:
    dc.b    $6e
hint_826b:
    dc.b    $72
hint_826c:
    dc.b    $61
hint_826e:
    dc.b    $65
hint_826f:
    dc.b    $00,$42,$61
hint_8272:
; --- unverified ---
    bcc.s hint_8294
hint_8274:
; --- unverified ---
    bvs.s hint_82e4
hint_8276:
    dc.b    $74
hint_8277:
    dc.b    $65
hint_8278:
    dc.b    $72
hint_8279:
    dc.b    $72
hint_827b:
    dc.b    $70,$74,$00,$49
hint_827f:
    dc.b    $6e
hint_8280:
    dc.b    $76
hint_8281:
    dc.b    $61,$6c
hint_8283:
    dc.b    $69
hint_8284:
    dc.b    $64
hint_8285:
    dc.b    $20
hint_8286:
    dc.b    $54
    dc.b    $41
sub_8289:
    dc.b    $50,$00
    dc.b    "Illegal"
sub_8292:
    dc.b    $20,$65
hint_8294:
; --- unverified ---
    moveq #99,d4
    bcs.s sub_8308
hint_8298:
; --- unverified ---
    moveq #105,d2
    ble.s hint_830a
hint_829c:
    dc.b    $00,$42,$72,$65,$61,$6b
hint_82a2:
; --- unverified ---
    moveq #111,d0
    bvs.s hint_8314
hint_82a6:
    dc.b    $74
hint_82a7:
    dc.b    $00
hint_82aa:
    dc.b    $3d
hint_82ab:
    dc.b    $00
hint_82ae:
    dc.b    $3d,$00,$53
hint_82b1:
    dc.b    $65
hint_82b3:
    dc.b    $72
hint_82b4:
    dc.b    $63
hint_82b5:
; --- unverified ---
    bvc.s $8320
hint_82b7:
; --- unverified ---
    bgt.s $8320
hint_82b9:
    dc.b    $2e
hint_82ba:
    dc.b    $2e,$2e,$00
hint_82c0:
    dc.b    $72
hint_82c1:
    dc.b    $65
    dc.b    $73
sub_82c4:
    dc.b    $20
hint_82c5:
    dc.b    $65
hint_82c7:
    dc.b    $72
hint_82c8:
    dc.b    $6f
hint_82ca:
    dc.b    $00,$42,$75,$73
hint_82ce:
    dc.b    $20,$65
hint_82d0:
    dc.b    $72
hint_82d1:
    dc.b    $72
hint_82d4:
    dc.b    $00,$20,$20
hint_82d7:
    dc.b    $3b
hint_82da:
    dc.b    $20,$00
    dc.b    "Text: ",0
    dc.b    $44
hint_82e4:
    dc.b    $61,$74
hint_82e6:
; --- unverified ---
    bsr.s sub_8322
hint_82e8:
    dc.b    $20
hint_82e9:
    dc.b    $00
hint_82eb:
    dc.b    $53,$53
hint_82ed:
    dc.b    $20,$3a
hint_82ef:
    dc.b    $20,$00
    dc.b    "Curren"
sub_82f7:
    dc.b    $74
hint_82f8:
    dc.b    $20
hint_82fe:
; --- unverified ---
    moveq #111,d0
    bvs.s hint_8370
hint_8302:
    dc.b    $74,$73
    dc.b    $3a,$0a,$00,$44
sub_8308:
; --- unverified ---
    bsr.s hint_837e
hint_830a:
; --- unverified ---
    bsr.s hint_832c
    dc.b    $73
sub_830d:
    dc.b    "tart,en"
hint_8314:
    dc.b    $64
hint_8315:
    dc.b    $3c
hint_8316:
    dc.b    $2c,$73,$69
hint_831b:
    dc.b    $3e,$00
hint_831e:
    dc.b    $72,$6f
    dc.b    $73,$73
sub_8322:
    dc.b    $2d,$72
hint_8324:
    dc.b    $65,$66
hint_8326:
    dc.b    $65,$72
hint_8328:
    dc.b    $65,$6e
hint_832a:
    dc.b    $63,$65
hint_832c:
    dc.b    " list",0
    dc.b    $46,$69,$6c,$65
hint_8336:
    dc.b    $6e,$61
hint_8338:
    dc.b    $6d
hint_8339:
    dc.b    $65
hint_833a:
    dc.b    $00,$43
hint_833c:
    dc.b    $68
hint_833d:
    dc.b    $65
hint_833e:
    dc.b    $63
hint_833f:
    dc.b    $6b
hint_8340:
; --- unverified ---
    bvs.s $83b0
hint_8342:
; --- unverified ---
    beq.s hint_8364
hint_8344:
    dc.b    $66,$6f
hint_8346:
    dc.b    $72
hint_8347:
    dc.b    $20
hint_834f:
    dc.b    $2e,$2e,$00,$43
    dc.b    $68,$65
sub_8355:
; --- unverified ---
    bls.s hint_83c2
hint_8357:
    dc.b    $69,$6e
hint_8359:
    dc.b    $67
hint_835a:
    dc.b    $20
hint_835b:
; --- unverified ---
    bne.s hint_83cc
hint_835d:
    dc.b    $72
hint_835e:
    dc.b    $20
hint_8361:
    dc.b    $62,$66
hint_8363:
    dc.b    $69
hint_8364:
    dc.b    $6c
hint_8365:
    dc.b    $65
hint_8366:
    dc.b    $2e
hint_8367:
    dc.b    $2e,$0a
hint_8369:
    dc.b    $00,$4c,$6f
hint_836c:
    dc.b    $61
hint_836e:
; --- unverified ---
    bvs.s hint_83de
hint_8370:
; --- unverified ---
    beq.s $8392
hint_8372:
    dc.b    $6c,$69
hint_8374:
; --- unverified ---
    bhi.s hint_83dc
hint_8376:
; --- unverified ---
    bvs.s hint_83e4
hint_8378:
; --- unverified ---
    bcs.s hint_83a8
hint_837a:
    dc.b    $2e
hint_837b:
    dc.b    $0a
hint_837e:
    dc.b    $61,$73
hint_8380:
; --- unverified ---
    bmi.s hint_83a2
hint_8382:
; --- unverified ---
    moveq #101,d2
    moveq #109,d1
    bvs.s $83f6
hint_8388:
; --- unverified ---
    bsr.s hint_83fe
hint_838a:
; --- unverified ---
    bcs.s hint_83f0
hint_838c:
    dc.b    $00,$55,$6e,$6b,$6e
hint_8391:
    dc.b    $6f
hint_8393:
    dc.b    $6e,$20
hint_8395:
    dc.b    $65,$78
hint_8397:
; --- unverified ---
    bls.s hint_83fe
hint_8399:
    dc.b    $70
hint_839a:
    dc.b    $74
hint_839d:
; --- unverified ---
    bgt.w $d008
hint_83a1:
; --- unverified ---
    bgt.s hint_8408
hint_83a3:
    dc.b    $20
hint_83a4:
    dc.b    $41
hint_83a8:
    dc.b    $63,$65
hint_83aa:
    dc.b    $70
hint_83ab:
    dc.b    $74
hint_83ae:
    dc.b    $6e
hint_83af:
    dc.b    $00,$4c,$69
hint_83b2:
    dc.b    $6e,$65
hint_83b4:
    dc.b    $20
hint_83b5:
    dc.b    $46
hint_83b9:
; --- unverified ---
    bls.s hint_8420
hint_83bb:
    dc.b    $70
hint_83bc:
    dc.b    $74
hint_83bf:
; --- unverified ---
    bgt.w $d822
hint_83c4:
; --- unverified ---
    bmi.s hint_83e6
hint_83c6:
    dc.b    $6d,$75
    dc.b    $73
sub_83c9:
    dc.b    $74
hint_83ca:
    dc.b    $20
hint_83cb:
; --- unverified ---
    bhi.s sub_8432
hint_83cd:
    dc.b    $20
hint_83ce:
    dc.b    $72,$75
hint_83d0:
    dc.b    $6e
hint_83d1:
    dc.b    $6e
hint_83d2:
    dc.b    $69
hint_83d3:
    dc.b    $6e
hint_83d4:
    dc.b    $67
hint_83d5:
    dc.b    $21
hint_83d6:
    dc.b    $00
hint_83d8:
    dc.b    $61,$73
hint_83da:
; --- unverified ---
    bmi.s sub_83fc
hint_83dc:
    dc.b    $6c
hint_83dd:
    dc.b    $6f
hint_83de:
; --- unverified ---
    bsr.s hint_8444
hint_83e0:
; --- unverified ---
    bcs.s hint_8446
hint_83e2:
    dc.b    $21
hint_83e3:
    dc.b    $00
hint_83e4:
    dc.b    $4e,$6f
hint_83e6:
    dc.b    " task lo"
hint_83ee:
    dc.b    $61,$64
hint_83f0:
    dc.b    $65,$64
hint_83f2:
    dc.b    $21
hint_83f3:
    dc.b    $00
hint_83f7:
    dc.b    $6b,$20
hint_83f9:
; --- unverified ---
    blt.s hint_8470
    dc.b    $73
sub_83fc:
    dc.b    $74,$20
hint_83fe:
    dc.b    $62,$65
hint_8400:
    dc.b    $20,$73,$75,$73
hint_8404:
    dc.b    $70,$65,$6e,$64
hint_8408:
    dc.b    $65,$64
hint_840a:
    dc.b    $21,$00
    dc.b    $45,$78,$65
sub_840f:
; --- unverified ---
    bls.s hint_8486
hint_8411:
; --- unverified ---
    moveq #105,d2
    bgt.s hint_847c
hint_8415:
    dc.b    $00,$4e,$6f,$6e
hint_8419:
; --- unverified ---
    bcs.w $d790
hint_8420:
; --- unverified ---
    bgt.s hint_8486
hint_8422:
; --- unverified ---
    bcs.s hint_8488
hint_8424:
    dc.b    $00,$46,$72
hint_8427:
    dc.b    $65
hint_8429:
    dc.b    $20
hint_842a:
    dc.b    $6d,$65
hint_842c:
    dc.b    $6d
hint_842e:
    dc.b    $72,$79
    dc.b    $20,$43
sub_8432:
    dc.b    $68,$69
hint_8434:
    dc.b    $70,$2c,$46
hint_8437:
    dc.b    $61
hint_8439:
    dc.b    $74,$2c
    dc.b    $41
sub_843c:
; --- unverified ---
    bge.s hint_84aa
hint_843e:
    dc.b    $3a
hint_843f:
    dc.b    $20
hint_8440:
    dc.b    $00,$54
hint_8442:
    dc.b    $61,$73
hint_8444:
; --- unverified ---
    bmi.s hint_8480
hint_8446:
    dc.b    $20,$00,$48,$75
hint_844a:
    dc.b    $6e,$6b
hint_844c:
    dc.b    $20
hint_844d:
    dc.b    $6c,$69,$73
    dc.b    $74,$3a,$00,$4d
sub_8454:
    dc.b    $65,$6d
hint_8456:
; --- unverified ---
    ble.s hint_84ca
    dc.b    "y list:",0
    dc.b    $55,$6e,$6f,$72,$64
sub_8465:
    dc.b    $65,$72
hint_8467:
    dc.b    $65,$64
hint_8469:
    dc.b    $20,$63,$6f
hint_846c:
    dc.b    $6e
hint_846d:
; --- unverified ---
    bcc.s hint_84d8
hint_846f:
    dc.b    $74
hint_8470:
    dc.b    $69
hint_8472:
; --- unverified ---
    bgt.w $cde2
hint_8476:
; --- unverified ---
    bcs.s hint_84f0
hint_8478:
    dc.b    $61
hint_8479:
    dc.b    $63
hint_847a:
    dc.b    $74
hint_847b:
    dc.b    $20
hint_847c:
    dc.b    $72,$65
hint_8480:
; --- unverified ---
    bge.s $84f6
hint_8482:
    dc.b    $00,$46,$50,$20
hint_8486:
    dc.b    $64,$69
hint_8488:
    dc.b    $76
hint_8489:
    dc.b    $69
hint_848b:
    dc.b    $65
hint_848c:
    dc.b    $20
hint_848d:
; --- unverified ---
    bhi.s $8508
hint_848f:
    dc.b    $20,$7a
hint_8491:
    dc.b    $65,$72
hint_8493:
    dc.b    $6f,$00,$55,$6e
hint_8497:
; --- unverified ---
    bcc.s dat_84fe
hint_8499:
; --- unverified ---
    moveq #102,d1
    bge.s hint_850c
    dc.b    $77,$00,$4f,$70
sub_84a1:
    dc.b    $65,$72
hint_84a3:
    dc.b    $61,$6e
hint_84a5:
    dc.b    $64,$20
hint_84a7:
    dc.b    $65,$72
hint_84a9:
    dc.b    $72
hint_84aa:
    dc.b    $6f
hint_84ac:
    dc.b    $00,$4f,$76,$65
    dc.b    "rflow",0
    dc.b    $53
sub_84b7:
; --- unverified ---
    bvs.s hint_8520
hint_84b9:
; --- unverified ---
    bgt.s hint_851c
hint_84bb:
; --- unverified ---
    bge.s $8526
hint_84bd:
; --- unverified ---
    bgt.s $8526
hint_84bf:
    dc.b    $20
hint_84c0:
    dc.b    $4e
    dc.b    $4e
sub_84c3:
    dc.b    $00,$43,$6f,$2d
hint_84c7:
; --- unverified ---
    moveq #114,d0
    ble.s hint_852e
hint_84cb:
; --- unverified ---
    bcs.s hint_8540
    dc.b    $73,$6f,$72,$20,$76
sub_84d2:
    dc.b    $69,$6f
hint_84d4:
    dc.b    $6c,$61
hint_84d6:
    dc.b    $74,$69
hint_84d8:
; --- unverified ---
    ble.s $8548
hint_84da:
    dc.b    $00
hint_84db:
    dc.b    $46,$6f
hint_84dd:
    dc.b    $72
hint_84e0:
    dc.b    $74
hint_84e1:
    dc.b    $20
hint_84e4:
    dc.b    $72,$6f,$72
hint_84e7:
    dc.b    $00
    dc.b    $4d,$55
sub_84ef:
    dc.b    $20
hint_84f0:
    dc.b    $63
hint_84f1:
    dc.b    $6f
hint_84f2:
    dc.b    $6e
hint_84f3:
; --- unverified ---
    bne.s hint_855e
hint_84f5:
; --- unverified ---
    beq.s hint_856c
hint_84f7:
    dc.b    "ration"
hint_84fd:
    dc.b    $00
dat_84fe:
    dc.b    $44
hint_84ff:
    dc.b    $69,$73
hint_8501:
; --- unverified ---
    bsr.s hint_8576
    dc.b    $73,$65
sub_8505:
    dc.b    $6d,$62
hint_8507:
; --- unverified ---
    bge.s hint_8582
hint_8509:
    dc.b    $00
dat_850a:
    dc.b    $4d,$65
hint_850c:
    dc.b    $6d
hint_850e:
    dc.b    $72,$79
    dc.b    $00
sub_8511:
    dc.b    $52,$65
hint_8513:
; --- unverified ---
    beq.s hint_857e
    dc.b    $73
sub_8516:
    dc.b    "ters",0
dat_851b:
    dc.b    $53
hint_851c:
    dc.b    $6f,$75
hint_851e:
    dc.b    $72,$63
hint_8520:
; --- unverified ---
    bcs.s hint_8542
hint_8522:
    dc.b    $28
hint_8523:
    dc.b    $00
str_8524:
    dc.b    $53
sub_8528:
    dc.b    $43,$20,$74,$6f
hint_852c:
    dc.b    $20,$61
hint_852e:
    dc.b    $62,$6f
hint_8530:
    dc.b    $72
hint_8531:
    dc.b    $74
hint_8537:
    dc.b    $69,$6e
hint_8539:
; --- unverified ---
    bcc.s hint_85aa
    dc.b    $77
sub_853c:
    dc.b    $20,$73,$74,$61
hint_8540:
    dc.b    $72
hint_8541:
    dc.b    $74
hint_8542:
    dc.b    $20
hint_8543:
    dc.b    $61
hint_8545:
    dc.b    $64
hint_8546:
    dc.b    $72
hint_8547:
; --- unverified ---
    bcs.s $85bc
    dc.b    $73,$3f,$00
str_854c:
    dc.b    "Go to sou"
sub_8555:
    dc.b    $72
hint_8556:
    dc.b    $63
hint_8558:
    dc.b    $20
hint_8559:
    dc.b    $6c
hint_855a:
    dc.b    $69
hint_855b:
    dc.b    $6e
hint_855c:
    dc.b    $65
hint_855d:
    dc.b    $3f
hint_855e:
    dc.b    $00
str_855f:
    dc.b    $5b,$52
hint_8561:
    dc.b    $65
    dc.b    "urn]",0
pcref_8568:
    dc.b    $20
sub_8569:
    dc.b    $00,$46
hint_856b:
    dc.b    $69
hint_856c:
    dc.b    $6c
hint_856d:
    dc.b    $65
hint_856e:
    dc.b    $6e
hint_856f:
; --- unverified ---
    bsr.s hint_85de
hint_8571:
    dc.b    $65
hint_8572:
    dc.b    $20
hint_8573:
    dc.b    $74
hint_8574:
    dc.b    $6f
hint_8576:
    dc.b    $6c,$6f
hint_8578:
; --- unverified ---
    bsr.s hint_85de
hint_857a:
    dc.b    $00,$53,$6f,$75
hint_857e:
; --- unverified ---
    moveq #99,d1
    bcs.s hint_85a2
hint_8582:
    dc.b    $66,$69
hint_8584:
    dc.b    $6c
hint_8585:
    dc.b    $65
hint_8586:
    dc.b    $20
hint_8587:
    dc.b    $74,$6f
hint_8589:
    dc.b    $20,$6c,$6f
hint_858e:
    dc.b    $00
str_858f:
    dc.b    $45,$78
hint_8591:
    dc.b    $65
    dc.b    $75
sub_8594:
    dc.b    $74,$61
hint_8596:
; --- unverified ---
    bhi.s hint_8604
hint_8598:
; --- unverified ---
    bcs.s hint_85ba
hint_859a:
    dc.b    $66,$69
hint_859c:
    dc.b    $6c
hint_859d:
    dc.b    $65
hint_859e:
    dc.b    $20
hint_859f:
    dc.b    $74,$6f,$20
hint_85a2:
    dc.b    $6c
hint_85a3:
    dc.b    $6f
hint_85a4:
; --- unverified ---
    bsr.s hint_860a
hint_85a6:
    dc.b    $00
str_85a7:
    dc.b    $43,$6f
hint_85a9:
    dc.b    $6d
hint_85aa:
    dc.b    $6d
hint_85ab:
    dc.b    $61
hint_85ac:
; --- unverified ---
    bgt.s hint_8612
hint_85ae:
    dc.b    $20
hint_85af:
    dc.b    $6c,$69
hint_85b1:
    dc.b    $6e
hint_85b3:
    dc.b    $00,$52,$65
hint_85b6:
    dc.b    $67
    dc.b    $73
sub_85b9:
    dc.b    $74
hint_85ba:
    dc.b    $65
    dc.b    $3d
sub_85bd:
    dc.b    $76,$61
hint_85bf:
; --- unverified ---
    bge.s hint_8636
hint_85c1:
; --- unverified ---
    bcs.w $c924
hint_85c5:
    dc.b    $6e
hint_85c6:
    dc.b    $6e
hint_85c7:
    dc.b    $6f
hint_85c8:
    dc.b    $74
hint_85c9:
    dc.b    $20
hint_85ca:
    dc.b    $72,$75,$6e,$00
str_85ce:
    dc.b    $49
hint_85cf:
    dc.b    $6e
hint_85d0:
    dc.b    $20
hint_85d1:
    dc.b    $52,$4f
hint_85d3:
    dc.b    $4d,$21,$00
str_85d6:
    dc.b    $49
hint_85d7:
    dc.b    $74,$27
    dc.b    $73,$20,$6f,$64
sub_85dd:
; --- unverified ---
    bcc.s hint_8600
hint_85df:
; --- unverified ---
    ori.w #$616e,d3
    bgt.s sub_8654
hint_85e5:
    dc.b    $74,$20
    dc.b    $77,$72,$69,$74
sub_85eb:
; --- unverified ---
    bcs.s hint_860e
hint_85ed:
    dc.b    $00
str_85ee:
    dc.b    $54,$6f,$6f
hint_85f1:
    dc.b    $20
hint_85f2:
    dc.b    $6d,$61
hint_85f4:
    dc.b    $6e
hint_85f6:
    dc.b    " break"
hint_85fc:
; --- unverified ---
    moveq #111,d0
    bvs.s hint_866e
hint_8600:
    dc.b    $74,$73,$21
hint_8603:
    dc.b    $00
hint_8604:
    dc.b    $52,$75
hint_8606:
    dc.b    $6e,$20
    dc.b    $75
sub_8609:
    dc.b    $6e
hint_860a:
    dc.b    $74
hint_860b:
    dc.b    $69,$6c
hint_860d:
    dc.b    $20
hint_860e:
    dc.b    $61
hint_8610:
; --- unverified ---
    bcc.s hint_8684
hint_8612:
    dc.b    $65,$73
    dc.b    $73,$5b,$2c,$70
sub_8618:
; --- unverified ---
    bsr.s hint_868c
hint_861a:
    dc.b    $61
hint_861b:
    dc.b    $6d
hint_861c:
    dc.b    $20
hint_861d:
    dc.b    $6e,$3d,$2a
    dc.b    $3f
sub_8621:
    dc.b    $2d,$5d,$00,$4b,$69,$6c
hint_8627:
    dc.b    $6c
hint_8628:
    dc.b    $20
hint_8629:
    dc.b    $61,$6c
hint_862b:
    dc.b    $6c
hint_862c:
    dc.b    $20
hint_862d:
    dc.b    $62
hint_862e:
    dc.b    $72
hint_862f:
; --- unverified ---
    bcs.s sub_8692
hint_8631:
    dc.b    $6b
hint_8632:
    dc.b    $70
hint_8633:
; --- unverified ---
    ble.s hint_869e
hint_8635:
    dc.b    $6e
hint_8636:
    dc.b    $74
    dc.b    $00
str_8639:
    dc.b    $20,$59,$2f,$4e
sub_863d:
; --- unverified ---
    move.w d0,-(sp)
str_863f:
    clr.w ([27504,a2])
    ble.s hint_86b0
hint_8647:
    dc.b    $6e,$74
hint_8649:
    dc.b    $20,$61,$64,$64
hint_864d:
    dc.b    $72,$65
    dc.b    $73,$73,$5b,$2c,$70
sub_8654:
; --- unverified ---
    bsr.s $86c8
hint_8656:
    dc.b    $61,$6d
hint_8658:
    dc.b    $20
hint_8659:
    dc.b    $6e,$3d,$2a
hint_865c:
; --- unverified ---
    move.w 23808(a5),-(sp)
str_8660:
    pea 29556(a1)
    ble.s sub_86d8
    dc.b    $79
sub_8667:
    dc.b    $00
    dc.b    "Search"
hint_866e:
    dc.b    $20
hint_866f:
; --- unverified ---
    bne.s hint_86e0
hint_8671:
    dc.b    $72
hint_8672:
    dc.b    $20
hint_8674:
    dc.b    $2f
hint_8675:
    dc.b    $57,$2f,$4c
hint_8679:
    dc.b    "T/I? ",0
str_867f:
    dc.b    $4e,$6f,$20,$70,$72
hint_8684:
    dc.b    $69
hint_8686:
    dc.b    $74
hint_8687:
    dc.b    $65
hint_8689:
    dc.b    $20,$64,$65
hint_868c:
    dc.b    $76
hint_868d:
; --- unverified ---
    bvs.s hint_86f2
hint_868f:
    dc.b    $65,$20
    dc.b    $73
sub_8692:
; --- unverified ---
    bcs.s sub_8700
hint_8694:
    dc.b    $65
hint_8695:
    dc.b    $63
hint_8696:
    dc.b    $74
hint_8697:
    dc.b    $65
hint_8698:
; --- unverified ---
    bcc.w $cc12
hint_869c:
    dc.b    $70
hint_869d:
    dc.b    $72
hint_869e:
    dc.b    $65,$73
    dc.b    $73
sub_86a1:
; --- unverified ---
    bvs.s hint_8712
hint_86a3:
    dc.b    $6e
hint_86a4:
    dc.b    $20
hint_86a5:
    dc.b    "to loc"
hint_86ab:
    dc.b    $6b
hint_86ac:
    dc.b    $00,$45,$6e
hint_86af:
    dc.b    $74
hint_86b0:
    dc.b    $65
hint_86b1:
    dc.b    $72
hint_86b2:
    dc.b    $20
hint_86b5:
; --- unverified ---
    moveq #114,d0
    bcs.s hint_872c
    dc.b    $73,$69,$6f,$6e
sub_86bd:
; --- unverified ---
    ori.w #$796d,(a3)
    bhi.s hint_8732
hint_86c3:
; --- unverified ---
    bge.s hint_8738
hint_86c5:
    dc.b    $00,$50,$52,$45
    dc.b    "FERENCES",0
str_86d2:
    dc.b    "Show r"
sub_86d8:
; --- unverified ---
    bcs.s hint_8746
hint_86da:
; --- unverified ---
    bsr.s sub_8750
hint_86dc:
; --- unverified ---
    bvs.s hint_8754
hint_86de:
; --- unverified ---
    bcs.s sub_8700
hint_86e0:
; --- unverified ---
    ble.s $8748
hint_86e2:
    dc.b    $66,$73
hint_86e4:
; --- unverified ---
    bcs.s $875a
hint_86e6:
    dc.b    " symbols"
hint_86ee:
    dc.b    $20,$59,$2f,$4e
hint_86f2:
    dc.b    $3f,$20
hint_86f4:
    dc.b    $00,$43,$61,$73
    dc.b    $65
sub_86f9:
    dc.b    $20
hint_86fa:
    dc.b    $69
hint_86fb:
    dc.b    $6e,$73
hint_86fd:
    dc.b    $65,$6e
    dc.b    $73
sub_8700:
; --- unverified ---
    bvs.s hint_8776
hint_8702:
; --- unverified ---
    bvs.s $877a
hint_8704:
; --- unverified ---
    bcs.s str_8726
    dc.b    $73,$79,$6d,$62,$6f
sub_870b:
; --- unverified ---
    bge.s hint_8780
hint_870d:
    dc.b    $20,$59,$2f,$4e,$3f
hint_8712:
    dc.b    $20
hint_8713:
    dc.b    $00,$49,$67,$6e
hint_8717:
    dc.b    $6f,$72
hint_8719:
    dc.b    $65
hint_871a:
    dc.b    $20
hint_871b:
; --- unverified ---
    bls.s sub_877e
    dc.b    $73
sub_871e:
; --- unverified ---
    bcs.s sub_8740
hint_8720:
    dc.b    $59,$2f,$4e,$3f
hint_8724:
    dc.b    $20,$00
str_8726:
    dc.b    "Symbol"
hint_872c:
    dc.b    " signi"
hint_8732:
    dc.b    $66,$69
hint_8734:
    dc.b    $63,$61
hint_8736:
    dc.b    $6e,$63
hint_8738:
    dc.b    $65,$00,$43
hint_873b:
    dc.b    $6f
hint_873c:
    dc.b    $70,$79
    dc.b    $20,$73
sub_8740:
    dc.b    "tart,e"
hint_8746:
; --- unverified ---
    bgt.s $87ac
    dc.b    $2c,$74,$6f,$00
str_874c:
    dc.b    $46,$69,$6c,$6c
sub_8750:
    dc.b    $20,$73,$74,$61
hint_8754:
    dc.b    $72,$74,$2c
hint_8757:
    dc.b    $65
hint_8759:
    dc.b    $64,$2c
    dc.b    "with",0
str_8760:
    dc.b    $53
sub_8761:
    dc.b    $65,$74
hint_8763:
    dc.b    $20,$63
    dc.b    $75,$72,$72,$65,$6e
sub_876a:
; --- unverified ---
    moveq #32,d2
    bcc.s hint_87e0
hint_876e:
; --- unverified ---
    bvs.s hint_87e6
hint_8770:
    dc.b    $65,$2f
hint_8772:
    dc.b    $64,$69
hint_8774:
    dc.b    $72,$65
hint_8776:
; --- unverified ---
    bls.s hint_87ec
hint_8778:
; --- unverified ---
    ble.s hint_87ec
    dc.b    $79,$00
str_877c:
    dc.b    $53,$61
sub_877e:
    dc.b    $76,$65
hint_8780:
    dc.b    $20
hint_8781:
    dc.b    $62
hint_8783:
; --- unverified ---
    bgt.s hint_87e6
hint_8785:
    dc.b    $72,$79
hint_8787:
; --- unverified ---
    move.l -(a0),d6
    bne.s hint_87f4
hint_878b:
; --- unverified ---
    bge.s hint_87f2
hint_878d:
; --- unverified ---
    bgt.s hint_87f0
hint_878f:
; --- unverified ---
    blt.s hint_87f6
hint_8791:
    dc.b    $00,$73,$74,$61,$72,$74
hint_8797:
    dc.b    $20,$61,$64,$64
hint_879b:
    dc.b    $72,$65
    dc.b    $73,$73,$2c,$65
sub_87a1:
    dc.b    $6e,$64
hint_87a3:
    dc.b    $00,$52,$75,$6e,$3a,$20
    dc.b    $47,$6f,$2c,$49
sub_87ad:
; --- unverified ---
    bgt.s hint_8822
hint_87af:
    dc.b    $74,$72
    dc.b    "uction ",0
str_87b9:
    dc.b    "Help",0
sub_87be:
    dc.b    $44,$69,$73,$61
    dc.b    $73,$73,$65,$6d,$62
sub_87c7:
; --- unverified ---
    bge.s $882e
hint_87c9:
    dc.b    " start,end"
hint_87d3:
    dc.b    $00,$53,$61,$76
hint_87d7:
    dc.b    $65,$20
hint_87d9:
    dc.b    $70
hint_87da:
    dc.b    $72
hint_87dd:
    dc.b    $65
hint_87de:
    dc.b    $72
hint_87df:
    dc.b    $65
hint_87e0:
    dc.b    $6e
hint_87e1:
; --- unverified ---
    bls.s hint_8848
hint_87e4:
    dc.b    $20,$59
hint_87e6:
    dc.b    "/N? ",0
str_87eb:
    dc.b    $41
hint_87ec:
    dc.b    $6d,$69
hint_87ee:
    dc.b    $67,$61
hint_87f0:
    dc.b    $44,$4f
hint_87f2:
    dc.b    $53,$20
hint_87f4:
; --- unverified ---
    bcs.s $8868
hint_87f6:
    dc.b    $72,$6f
hint_87f8:
    dc.b    $72
hint_87f9:
    dc.b    $20
str_87fa:
hint_87ff:
    dc.b    $00,$51,$75,$69,$74,$20
    dc.b    $77,$69
sub_8807:
    dc.b    "th task running",0
    dc.b    $50,$72
hint_8819:
    dc.b    $69,$6e
hint_881b:
; --- unverified ---
    moveq #101,d2
    moveq #32,d1
    bcc.s sub_8886
hint_8821:
    dc.b    $76
hint_8822:
    dc.b    $69
hint_8824:
; --- unverified ---
    bcs.s hint_8846
hint_8826:
    dc.b    $6e,$61
hint_8828:
    dc.b    $6d,$65
hint_882a:
    dc.b    $00,$50,$72
hint_882d:
    dc.b    $65
    dc.b    "s any key"
pcref_8838:
    dc.b    $00
str_8839:
    dc.b    "Stop task",0
str_8843:
    dc.b    $4b,$69
sub_8845:
    dc.b    $6c
hint_8846:
    dc.b    $6c
hint_8847:
    dc.b    $20
hint_8848:
    dc.b    "task",0
    dc.b    $55,$6e
hint_884f:
    dc.b    $6c,$6f
hint_8851:
    dc.b    $61,$64
hint_8853:
    dc.b    $20,$73,$79,$6d
hint_8857:
    dc.b    $62,$6f
hint_8859:
; --- unverified ---
    bge.s hint_88ce
hint_885b:
    dc.b    $00,$49,$6e,$74,$65,$72
hint_8861:
; --- unverified ---
    bge.s hint_88c4
hint_8863:
; --- unverified ---
    bls.s hint_88ca
hint_8865:
    dc.b    " Y/N? "
    dc.b    $00
str_886c:
    dc.b    "Source window line numbers"
sub_8886:
    dc.b    $20
hint_8887:
    dc.b    $44
hint_8889:
    dc.b    $48
hint_888a:
    dc.b    $2f,$4e,$3f
    dc.b    $6f
sub_8893:
    dc.b    $2d
hint_8894:
    dc.b    $6c,$6f
hint_8896:
    dc.b    $61,$64
hint_8898:
    dc.b    $20
hint_88a2:
    dc.b    $6c,$65
hint_88a4:
    dc.b    " Y/N? ",0
    dc.b    $41,$75,$74,$6f,$6d
hint_88b0:
; --- unverified ---
    bsr.s hint_8926
hint_88b2:
    dc.b    $69
hint_88b3:
    dc.b    $63
hint_88b4:
    dc.b    $20
hint_88b5:
    dc.b    $27
hint_88b7:
    dc.b    $27,$20,$6f,$72
hint_88bb:
    dc.b    $20,$27,$40,$27,$20
hint_88c0:
    dc.b    $70
hint_88c1:
    dc.b    $72,$65
hint_88c4:
; --- unverified ---
    bvs.s hint_893e
hint_88c6:
    dc.b    $20,$59
hint_88c8:
    dc.b    $2f,$4e
hint_88ca:
    dc.b    $3f,$20
hint_88ce:
    dc.b    $68,$6f
    dc.b    $77,$20,$5a,$41,$6e
sub_88d5:
; --- unverified ---
    movea.l 28192(a1),a0
    bcc.s hint_8944
    dc.b    "sassembly Y/N? ",0
    dc.b    $00
sub_88ec:
    dcb.b   4,0
dat_88f0:
    dcb.b   4,0
dat_88f4:
    dc.b    $00
dat_88f5:
    dc.b    $00
dat_88f6:
    dc.b    $00,$00
dat_88fa:
    dc.b    $00,$00
dat_88fc:
    dc.b    $00,$00
dat_88fe:
    dcb.b   7,0
hint_8905:
    dc.b    $00
dat_8906:
    dc.b    $00,$00
dat_8908:
    dc.b    $00
hint_8909:
    dc.b    $00
hint_890b:
    dc.b    $00
dat_890c:
    dc.b    $00,$00,$00
dat_8910:
    dc.b    $00,$00
dat_8912:
    dc.b    $00,$00
pcref_8914:
dat_8916:
    dc.b    $00
hint_8917:
    dc.b    $00,$00,$00
dat_891a:
    dc.b    $00,$00,$00
hint_891d:
    dc.b    $00
hint_8926:
    dcb.b   4,0
hint_892a:
    dc.b    $00,$00,$00
hint_892d:
    dc.b    $00
hint_892e:
    dcb.b   16,0
hint_893e:
    dc.b    $00
hint_893f:
    dc.b    $00,$00,$00
hint_8944:
    dcb.b   8,0
pcref_894c:
    dc.b    $00,$00
dat_894e:
    dc.b    $00,$00
dat_8956:
    dcb.b   4,0
dat_895a:
    dcb.b   4,0
dat_895e:
    dc.b    $00,$00
dat_8960:
    dc.b    $00,$00
pcref_8964:
