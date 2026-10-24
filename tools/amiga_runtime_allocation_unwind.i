; The game has not been entered on this path: no target DMA was started.
; D4 counts successful static reservations; the first is the owned mailbox.
allocation_unwind:
    cmpi.l #ALLOCATION_STATIC_READY,d4
    bcs.w allocation_unwind_static
    move.l ALLOCATION_RECORD+4,d0
    beq.b allocation_unwind_scratch
    movea.l d0,a1
    move.l #ALLOCATION_SIZE,d0
    jsr _LVOFreeMem(a6)
    clr.l ALLOCATION_RECORD+4
allocation_unwind_scratch:
    move.l ALLOCATION_RECORD+8,d0
    beq.b allocation_unwind_prior
    movea.l d0,a1
    move.l ALLOCATION_RECORD+12,d0
    jsr _LVOFreeMem(a6)
    clr.l ALLOCATION_RECORD+8
allocation_unwind_prior:
    IFD ALLOCATION_CPU
    move.l ALLOCATION_RECORD+24,d0
    beq.b allocation_unwind_static
    movea.l d0,a1
    move.l ALLOCATION_RECORD+28,d0
    jsr _LVOFreeMem(a6)
    clr.l ALLOCATION_RECORD+24
    ENDC
allocation_unwind_static:
    INCLUDE "direct_payload_allocation_static_unwind.i"
allocation_abort_publish:
    move.l #'ABOR',HANDOFF_MARKER
allocation_abort_wait:
    cmpi.l #'FREE',HANDOFF_MARKER
    bne.b allocation_abort_wait
    ; Release the last diagnostic ownership after the observer acknowledges.
    cmpi.l #ALLOCATION_RECORD_OWNED,d4
    bcs.b allocation_record_unowned
    movea.l #ALLOCATION_RECORD,a1
    move.l #$F0,d0
    jsr _LVOFreeMem(a6)
allocation_record_unowned:
    movea.l #HANDOFF_MARKER-8,a1
    moveq #16,d0
    jsr _LVOFreeMem(a6)
    move.l #'FREE',d3
allocation_closed:
    bra.b allocation_closed
