; Exclusive original-chipset hosted profile, not universal OS/RTG portability.
; All system calls that may wait happen before Forbid or after Supervisor RTE.
CUSTOM_BASE EQU $DFF000
open_graphics:
    movea.l 4.w,a6
    lea graphics_name(pc),a1
    moveq #0,d0
    jsr _LVOOpenLibrary(a6)
    move.l d0,state_gfx-host_state(a5)
    rts
run_hosted_game:
    movea.l state_gfx-host_state(a5),a6
    move.l gb_ActiView(a6),state_old_view-host_state(a5)
    suba.l a1,a1
    jsr _LVOLoadView(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOOwnBlitter(a6)
    jsr _LVOWaitBlit(a6)
    movea.l 4.w,a6
    jsr _LVOForbid(a6)
    lea supervisor_game_entry(pc),a5
    jsr _LVOSupervisor(a6)
host_user_return:
    lea host_state(pc),a5
    movea.l state_gfx-host_state(a5),a6
    movea.l state_old_view-host_state(a5),a1
    jsr _LVOLoadView(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOWaitBlit(a6)
    jsr _LVODisownBlitter(a6)
    movea.l 4.w,a6
    jsr _LVOPermit(a6)
    rts
supervisor_game_entry:
    movem.l d0-d7/a0-a6,-(sp)
    lea state_saved_ssp(pc),a0
    move.l sp,(a0)
    move #$2700,sr
    lea state_vector_snapshot(pc),a1
    suba.l a0,a0
    move.w #255,d0
save_host_vectors:
    move.l (a0)+,(a1)+
    dbra d0,save_host_vectors
    lea host_state(pc),a5
    move.w CUSTOM_BASE+dmaconr,state_saved_dma-host_state(a5)
    move.w CUSTOM_BASE+intenar,state_saved_irq-host_state(a5)
    move.w CUSTOM_BASE+adkconr,state_saved_adk-host_state(a5)
    move.b $BFEE01,state_saved_cra-host_state(a5)
    move.b $BFE001,d0
    andi.b #2,d0
    move.b d0,state_saved_LED-host_state(a5)
    move.w #$7FFF,CUSTOM_BASE+intena
    move.w #$7FFF,CUSTOM_BASE+dmacon
    move.w #$7FFF,CUSTOM_BASE+intreq
    ; Ordinary call link permits read-only host provenance at payload entry.
    ; The retained bootstrap changes to the original owned runtime stack itself.
    jsr INPUT_ADDRESS.l
unexpected_payload_return:
    bra.w restore_host_supervisor
mission_restart_dispatch:
    IFD IMAGE_ALLOCATED
    ; Reserve a tail-return target without changing CCR. The first dispatch
    ; restores the incoming registers/SR and consumes exactly this slot.
    pea 0.w
    ENDC
    move.w sr,-(sp)
    movem.l d0/a0,-(sp)
    lea state_dispatch_count(pc),a0
    tst.l (a0)
    bne.b mission_session_finished
    addq.l #1,(a0)
    IFD IMAGE_ALLOCATED
    move.l state_image_initializer(pc),d0
    move.l d0,10(sp)
    ENDC
    movem.l (sp)+,d0/a0
    move.w (sp)+,sr
    IFD IMAGE_ALLOCATED
    rts
    ELSE
    jmp ORIGINAL_WORLD_INITIALIZER.l
    ENDC
mission_session_finished:
    ; The old game stack is abandoned only at the explicit lifecycle import.
    ; The original first world initializer was never skipped or host-called.
    move #$2700,sr
restore_host_supervisor:
    move #$2700,sr
    ; Finish active blitter work while its DMA is still enabled.
wait_game_blitter:
    move.w CUSTOM_BASE+dmaconr,d0
    btst #14,d0
    bne.b wait_game_blitter
    move.w #$7FFF,CUSTOM_BASE+intena
    move.w #$7FFF,CUSTOM_BASE+dmacon
    move.w #$7FFF,CUSTOM_BASE+intreq
game_DMA_quiescent:
    lea host_state(pc),a5
    ; Restore the game's writable serial-control/LED state, not fabricated CIA
    ; timer counter/latch identity. Keyboard recovery must be observed at CLI.
    move.b state_saved_cra-host_state(a5),$BFEE01
    move.b $BFE001,d0
    andi.b #$FD,d0
    or.b state_saved_LED-host_state(a5),d0
    move.b d0,$BFE001
    lea state_vector_snapshot(pc),a0
    suba.l a1,a1
    move.w #255,d0
restore_host_vectors:
    move.l (a0)+,(a1)+
    dbra d0,restore_host_vectors
    move.w #$7FFF,CUSTOM_BASE+adkcon
    move.w state_saved_adk-host_state(a5),d0
    ori.w #$8000,d0
    move.w d0,CUSTOM_BASE+adkcon
    movea.l state_gfx-host_state(a5),a6
    move.l gb_copinit(a6),CUSTOM_BASE+cop1lc
    move.w #0,CUSTOM_BASE+copjmp1
    move.w state_saved_dma-host_state(a5),d0
    andi.w #$07FF,d0
    ori.w #$8000,d0
    move.w d0,CUSTOM_BASE+dmacon
    move.w state_saved_irq-host_state(a5),d0
    ori.w #$8000,d0
    move.w d0,CUSTOM_BASE+intena
    movea.l state_saved_ssp-host_state(a5),sp
    movem.l (sp)+,d0-d7/a0-a6
    rte
graphics_name: dc.b "graphics.library",0
    even
