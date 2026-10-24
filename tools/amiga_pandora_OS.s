; Normal DOS HUNK loader. Generated tables come only from the native owner plan.
; Optional reviewed hosted-game mode adds device/takeover and exit ownership.
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/memory.i"
    INCLUDE "dos/dos_lib.i"
    INCLUDE "dos/dos.i"
    INCLUDE "pandora_OS_plan.i"
    IFD HOSTED_GAME
    INCLUDE "devices/audio.i"
    INCLUDE "graphics/graphics_lib.i"
    INCLUDE "graphics/gfxbase.i"
    INCLUDE "hardware/custom.i"
    ENDC
    SECTION code,code_f
host_entry:
    movem.l d2-d7/a2-a6,-(sp)
    lea host_state(pc),a5
    movea.l 4.w,a6
    move.l #$504F5331,(a5) ; POS1; state is owned HUNK storage
    clr.l state_phase-host_state(a5)
    clr.l state_count-host_state(a5)
    move.l #20,state_exit_result-host_state(a5)
    ; PRNG must precede library allocation and retain the uninitialized tail.
    moveq #8,d0
    moveq #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    tst.l d0
    beq.w failed
    move.l d0,state_owners-host_state(a5)
    move.l d0,d2
    moveq #8,d3
    bsr.w remember_lease
    cmpi.l #$7FF8,d2
    bhi.w failed
    move.l d2,d0
    andi.l #7,d0
    bne.w failed
    lea fixed_table(pc),a2
    moveq #FIXED_COUNT-1,d7
fixed_next:
    movea.l (a2)+,a1
    move.l (a2)+,d0
    move.l a1,d2
    move.l d0,d3
    jsr _LVOAllocAbs(a6)
    cmp.l d2,d0
    bne.w failed
    bsr.w remember_lease
    dbra d7,fixed_next
    lea owner_sizes+4(pc),a2
    lea state_owners+4(pc),a3
    moveq #OWNER_COUNT-2,d7
owner_next:
    move.l (a2)+,d3
    move.l d3,d0
    moveq #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    tst.l d0
    beq.w failed
    move.l d0,(a3)+
    move.l d0,d2
    bsr.w remember_lease
    dbra d7,owner_next
    move.l #1,state_phase-host_state(a5)
    lea dos_name(pc),a1
    moveq #0,d0
    jsr _LVOOpenLibrary(a6)
    move.l d0,state_dos-host_state(a5)
    beq.w failed
    movea.l d0,a6
    lea payload_name(pc),a0
    move.l a0,d1
    move.l #MODE_OLDFILE,d2
    jsr _LVOOpen(a6)
    move.l d0,state_file-host_state(a5)
    beq.w failed
    move.l d0,d1
    move.l #INPUT_ADDRESS,d2
    move.l #PAYLOAD_SIZE,d3
    jsr _LVORead(a6)
    cmpi.l #PAYLOAD_SIZE,d0
    bne.w failed
    move.l state_file-host_state(a5),d1
    lea eof_byte(pc),a0
    move.l a0,d2
    moveq #1,d3
    jsr _LVORead(a6)
    tst.l d0
    bne.w failed
    move.l state_file-host_state(a5),d1
    jsr _LVOClose(a6)
    clr.l state_file-host_state(a5)
    ; CRC guards accidental stale media; SHA identities are retained by builder
    ; and the live observer must compare the complete staged bytes before entry.
    movea.l #INPUT_ADDRESS,a0
    move.l #PAYLOAD_SIZE,d7
    moveq #-1,d0
crc_next:
    moveq #0,d1
    move.b (a0)+,d1
    eor.b d0,d1
    lsl.w #2,d1
    lea crc_table(pc),a1
    move.l 0(a1,d1.w),d2
    lsr.l #8,d0
    eor.l d2,d0
    subq.l #1,d7
    bne.b crc_next
    not.l d0
    cmpi.l #PAYLOAD_CRC32,d0
    bne.w failed
    move.l #2,state_phase-host_state(a5)
pre_entry_ready:
    IFD HOSTED_GAME
    bsr.w validate_runtime_fields
    tst.l d0
    beq.w failed
    bsr.w acquire_audio
    tst.l d0
    beq.w failed
    bsr.w open_graphics
    tst.l d0
    beq.w failed
    bsr.w apply_runtime_fields
    bsr.w run_hosted_game
    lea host_state(pc),a5
    clr.l state_exit_result-host_state(a5)
    lea completed_message(pc),a0
    bra.b print_and_unwind
    ENDC
    ; An ordinary DOS return is the only implemented mode in this checkpoint.
    ; Do not start the game without device/takeover and exit ownership.
    clr.l state_exit_result-host_state(a5)
    lea success_message(pc),a0
    bra.b print_and_unwind
failed:
    lea failure_message(pc),a0
print_and_unwind:
    move.l a0,state_message-host_state(a5)
    IFD HOSTED_GAME
    bsr.w release_audio
    movea.l 4.w,a6
    move.l state_gfx-host_state(a5),d0
    beq.b graphics_closed
    movea.l d0,a1
    jsr _LVOCloseLibrary(a6)
    clr.l state_gfx-host_state(a5)
graphics_closed:
    ENDC
    move.l state_dos-host_state(a5),d0
    beq.b unwind
    movea.l d0,a6
    move.l state_file-host_state(a5),d1
    beq.b no_open_file
    jsr _LVOClose(a6)
    clr.l state_file-host_state(a5)
no_open_file:
    jsr _LVOOutput(a6)
    move.l d0,d1
    move.l state_message-host_state(a5),d2
    movea.l d2,a0
    moveq #0,d3
message_size:
    tst.b (a0)+
    beq.b message_write
    addq.l #1,d3
    bra.b message_size
message_write:
    jsr _LVOWrite(a6)
    movea.l state_dos-host_state(a5),a1
    movea.l 4.w,a6
    jsr _LVOCloseLibrary(a6)
    clr.l state_dos-host_state(a5)
unwind:
    movea.l 4.w,a6
    move.l state_count-host_state(a5),d7
    beq.b finish
    lsl.w #3,d7
    lea state_leases-host_state(a5),a2
    adda.w d7,a2
free_next:
    subq.l #8,a2
    movea.l (a2),a1
    move.l 4(a2),d0
free_owned_lease_call:
    jsr _LVOFreeMem(a6)
free_owned_lease_return:
    subq.l #1,state_count-host_state(a5)
    bne.b free_next
finish:
    move.l state_exit_result-host_state(a5),d0
    movem.l (sp)+,d2-d7/a2-a6
    rts
remember_lease:
    move.l state_count-host_state(a5),d0
    lsl.w #3,d0
    lea state_leases-host_state(a5),a0
    move.l d2,0(a0,d0.w)
    move.l d3,4(a0,d0.w)
    addq.l #1,state_count-host_state(a5)
    rts
    IFD HOSTED_GAME
    INCLUDE "amiga_pandora_OS_fields.i"
    INCLUDE "amiga_pandora_OS_audio.i"
    INCLUDE "amiga_pandora_OS_takeover.i"
    ENDC
    even
    INCLUDE "pandora_OS_tables.i"
dos_name: dc.b "dos.library",0
payload_name: dc.b "Pandora.payload",0
success_message: dc.b "PANDORA OS: SIX OWNERS AND PAYLOAD READY, PRE-ENTRY ONLY",10,0
completed_message: dc.b "PANDORA OS: GAME RETURNED, HARDWARE RESTORED",10,0
failure_message: dc.b "PANDORA OS: REFUSED, OWNED LEASES UNWOUND",10,0
    even
immutable_code_end:
host_state: dc.l 0
state_phase: dc.l 0
state_count: dc.l 0
state_dos: dc.l 0
state_file: dc.l 0
state_message: dc.l 0
state_owners: dcb.l OWNER_COUNT,0
state_leases: dcb.l (OWNER_COUNT+FIXED_COUNT)*2,0
state_leases_end:
state_exit_result: dc.l 20
    IFD HOSTED_GAME
state_gfx: dc.l 0
state_old_view: dc.l 0
state_saved_ssp: dc.l 0
state_dispatch_count: dc.l 0
state_saved_dma: dc.w 0
state_saved_irq: dc.w 0
state_saved_adk: dc.w 0
state_saved_cra: dc.b 0
state_saved_LED: dc.b 0
state_signal: dc.l -1
state_audio_open: dc.l 0
state_audio_lock: dc.l 0
state_audio_port: dcb.b MP_SIZE,0
    even
state_audio_request: dcb.b ioa_SIZEOF,0
    even
state_audio_lock_request: dcb.b ioa_SIZEOF,0
    even
state_vector_snapshot: dcb.b 1024,0
    ENDC
    even
eof_byte: dc.b 0
    even
