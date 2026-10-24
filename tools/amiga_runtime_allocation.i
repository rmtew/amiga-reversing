; Optional direct-payload allocation, before CMD_READ. Native plan fields supply
; size, exclusion ranges and LONG-data fixups. No target operands are scanned.
    INCLUDE "exec/memory.i"
allocation_acquire:
    clr.l ALLOCATION_RECORD+4
    clr.l ALLOCATION_RECORD+8
    clr.l ALLOCATION_RECORD+12
    clr.l ALLOCATION_RECORD+16
    IFD ALLOCATION_CPU
    clr.l ALLOCATION_RECORD+24
    clr.l ALLOCATION_RECORD+28
    ENDC
    move.l #'ALLO',ALLOCATION_RECORD
    IFD ALLOCATION_FAIL_BEFORE
    bra.w failed
    ENDC
    IFD ALLOCATION_CPU
    IFNE ALLOCATION_PRIOR_BYTES
    ; A real prior lease changes allocator state; it is never a selected base.
    move.l #ALLOCATION_PRIOR_BYTES,d0
    move.l #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    move.l d0,ALLOCATION_RECORD+24
    tst.l d0
    beq.w failed
    move.l #ALLOCATION_PRIOR_BYTES,ALLOCATION_RECORD+28
    ENDC
    ENDC
allocation_request_owner:
    move.l #ALLOCATION_SIZE,d0
    move.l #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    move.l d0,ALLOCATION_RECORD+4
    tst.l d0
    beq.w failed
    move.l d0,d2
    move.l d0,d3
    addi.l #ALLOCATION_SIZE,d3
    INCLUDE "direct_payload_allocation_exclusions.i"
allocation_owner_valid:
    move.l #1,ALLOCATION_RECORD+16
    IFD ALLOCATION_FAIL_AFTER
    bra.w failed
    ENDC
    bra.w allocation_acquired
allocation_collision:
    ; Free only the just-returned owner. The exclusion scratch lease is a real
    ; allocation, not a chosen owner base; refuse an unexpected allocator choice.
    movea.l d2,a1
    move.l #ALLOCATION_SIZE,d0
    jsr _LVOFreeMem(a6)
    clr.l ALLOCATION_RECORD+4
    tst.l ALLOCATION_RECORD+8
    bne.w failed
    ; A second collision must retain the first lease's exact FreeMem size.
    ; D2/D6 survive Exec calls; only initialize this after proving no lease.
    move.l d6,ALLOCATION_RECORD+12
    sub.l d2,ALLOCATION_RECORD+12
    addi.l #ALLOCATION_SCRATCH_EXTRA,ALLOCATION_RECORD+12
    move.l ALLOCATION_RECORD+12,d0
    move.l #MEMF_CHIP,d1
    jsr _LVOAllocMem(a6)
    move.l d0,ALLOCATION_RECORD+8
    tst.l d0
    beq.w failed
    cmp.l d2,d0
    bne.w failed
    bra.w allocation_request_owner
allocation_acquired:
