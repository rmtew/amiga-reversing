; Own normal-HUNK lifecycle probe, not Pandora or a game entry substitute.
; Tests LoadView/OwnBlitter/Forbid/Supervisor, a temporary owned SSP, RTE and
; observable OS return. Audio/CIA ownership and game exit imports remain separate.
    INCLUDE "exec/exec_lib.i"
    INCLUDE "dos/dos_lib.i"
    INCLUDE "graphics/graphics_lib.i"
    INCLUDE "graphics/gfxbase.i"
    INCLUDE "hardware/custom.i"
CUSTOM_BASE EQU $DFF000
    SECTION code,code
host_entry:
    movem.l d2-d7/a2-a6,-(sp)
    movea.l 4.w,a6
    lea graphics_name(pc),a1
    moveq #0,d0
    jsr _LVOOpenLibrary(a6)
    tst.l d0
    beq.w finish
    lea gfx_base(pc),a0
    move.l d0,(a0)
    movea.l d0,a6
    lea old_view(pc),a0
    move.l gb_ActiView(a6),(a0)
    lea saved_dma(pc),a0
    move.w CUSTOM_BASE+dmaconr,(a0)
    lea saved_irq(pc),a0
    move.w CUSTOM_BASE+intenar,(a0)
    suba.l a1,a1
    jsr _LVOLoadView(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOOwnBlitter(a6)
    jsr _LVOWaitBlit(a6)
    movea.l 4.w,a6
    jsr _LVOForbid(a6)
    lea supervisor_takeover(pc),a5
    jsr _LVOSupervisor(a6)
returned_to_user:
    movea.l gfx_base(pc),a6
    movea.l old_view(pc),a1
    jsr _LVOLoadView(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOWaitTOF(a6)
    jsr _LVOWaitBlit(a6)
    jsr _LVODisownBlitter(a6)
    movea.l 4.w,a6
    jsr _LVOPermit(a6)
    movea.l gfx_base(pc),a1
    jsr _LVOCloseLibrary(a6)
    lea dos_name(pc),a1
    moveq #0,d0
    jsr _LVOOpenLibrary(a6)
    tst.l d0
    beq.b finish
    movea.l d0,a6
    jsr _LVOOutput(a6)
    move.l d0,d1
    lea message(pc),a0
    move.l a0,d2
    move.l #message_end-message,d3
    jsr _LVOWrite(a6)
    movea.l a6,a1
    movea.l 4.w,a6
    jsr _LVOCloseLibrary(a6)
finish:
    moveq #0,d0
    movem.l (sp)+,d2-d7/a2-a6
    rts
supervisor_takeover:
    movem.l d0-d7/a0-a6,-(sp)
    lea saved_ssp(pc),a0
    move.l sp,(a0)
    move #$2700,sr
    lea vector_snapshot(pc),a1
    suba.l a0,a0
    move.w #255,d0
save_next_vector:
    move.l (a0)+,(a1)+
    dbra d0,save_next_vector
wait_before_probe_stop:
    move.w CUSTOM_BASE+dmaconr,d0
    btst #14,d0
    bne.b wait_before_probe_stop
    move.w #$7FFF,CUSTOM_BASE+intena
    move.w #$7FFF,CUSTOM_BASE+dmacon
    move.w #$7FFF,CUSTOM_BASE+intreq
    ; This is our own stack, not a fabricated game checkpoint or game memory.
    lea owned_stack_top(pc),sp
    bsr.b owned_stack_call
    bra.b restore_host_supervisor
owned_stack_call:
    movem.l d0-d7/a0-a6,-(sp)
    movem.l (sp)+,d0-d7/a0-a6
    rts
restore_host_supervisor:
    move #$2700,sr
    lea vector_snapshot(pc),a0
    suba.l a1,a1
    move.w #255,d0
restore_next_vector:
    move.l (a0)+,(a1)+
    dbra d0,restore_next_vector
    movea.l gfx_base(pc),a6
    move.l gb_copinit(a6),CUSTOM_BASE+cop1lc
    move.w #0,CUSTOM_BASE+copjmp1
    move.w saved_dma(pc),d0
    ori.w #$8000,d0
    move.w d0,CUSTOM_BASE+dmacon
    move.w saved_irq(pc),d0
    ori.w #$8000,d0
    move.w d0,CUSTOM_BASE+intena
    movea.l saved_ssp(pc),sp
    movem.l (sp)+,d0-d7/a0-a6
    rte
    even
gfx_base: dc.l 0
old_view: dc.l 0
saved_ssp: dc.l 0
saved_dma: dc.w 0
saved_irq: dc.w 0
graphics_name: dc.b "graphics.library",0
dos_name: dc.b "dos.library",0
message: dc.b "PANDORA HOST: VIEW/SSP RESTORED, NORMAL DOS RETURN",10
message_end:
    even
vector_snapshot: dcb.b 1024,0
owned_stack: dcb.b 512,0
owned_stack_top:
