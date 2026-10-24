; Bounded Exec allocation/free diagnostic, not Pandora gameplay code.
; The normal direct-payload builder owns input and handoff markers. D5 is an
; explicit prior scratch request; PROBE_SIZE comes from the canonical owner.
; Results are retained in the owned input backing, after both leases are freed.
    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/memory.i"
    ORG $20000
    movea.l 4.w,a6
    move.l d5,$20108
    tst.l d5
    beq.b allocate_owner
    move.l d5,d0
    move.l #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    move.l d0,$20104
    tst.l d0
    beq.b finish
allocate_owner:
    move.l #PROBE_SIZE,d0
    move.l #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    move.l d0,$20100
    tst.l d0
    beq.b free_padding
    movea.l d0,a1
    move.l #PROBE_SIZE,d0
    jsr _LVOFreeMem(a6)
    move.l #1,$2010c
free_padding:
    move.l $20104,d0
    beq.b finish
    movea.l d0,a1
    move.l d5,d0
    jsr _LVOFreeMem(a6)
finish:
    move.l #'DONE',$7fff8
hold:
    bra.b hold
    dcb.b $100-(*-$20000),0
    dc.l 0,0,0,0
    dcb.b $200-(*-$20000),0
