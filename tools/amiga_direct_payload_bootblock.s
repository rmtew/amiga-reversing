; Parameterized direct-payload boot shim. The generic builder supplies every
; target-specific value as a vasm definition and writes this code after the
; 12-byte AmigaDOS boot-block header.

    INCLUDE "exec/exec_lib.i"
    INCLUDE "devices/trackdisk.i"

    SECTION code,code

start:
    IFD RUNTIME_ALLOCATION
    movem.l d0-d6/a0-a4,-(a7)
    ENDC
    movea.l a1,a5
    ; Acquire the complete input backing and declared destination storage before
    ; reading any payload bytes. AllocAbs may write split free-list headers
    ; outside a requested subrange, so no allocations may follow CMD_READ.
    INCLUDE "direct_payload_reservations.i"
    IFD RUNTIME_ALLOCATION
    INCLUDE "amiga_runtime_allocation.i"
    ENDC
    IFND RUNTIME_ALLOCATION
    move.l  #'BOOT',HANDOFF_MARKER-8
    ENDC
    move.w  #CMD_READ,IO_COMMAND(a5)
    move.l  #PAYLOAD_SIZE,IO_LENGTH(a5)
    move.l  #PAYLOAD_ADDRESS,IO_DATA(a5)
    move.l  #PAYLOAD_DISK_OFFSET,IO_OFFSET(a5)

    ; The boot block can run before the emulated floppy has completed its
    ; first ready transition. Retry the same synchronous read; do not select
    ; another launch path or continue after exhaustion.
    moveq   #50,d7
read_payload:
    movea.l a5,a1
    jsr     _LVODoIO(a6)
    tst.l   d0
    beq.b   handoff
    dbra    d7,read_payload
    IFD RUNTIME_ALLOCATION
    bra.w   failed
    ELSE
    bra.b   failed
    ENDC

handoff:
    ; Preserve only declared original-loader byte seeds, before native game
    ; code and before HAND. Destinations were acquired before CMD_READ.
    IFD RUNTIME_ALLOCATION
    INCLUDE "direct_payload_allocation_fixups.i"
    ENDC
    INCLUDE "direct_payload_seed_copies.i"
    IFD RUNTIME_ALLOCATION
    move.l d4,ALLOCATION_RECORD+20
    movem.l (a7)+,d0-d6/a0-a4
    ENDC
    INCLUDE "direct_payload_entry_context.i"
    move.l  #HANDOFF_VALUE,HANDOFF_MARKER
; The control client attaches after the boot code may otherwise have handed
; execution to the payload.  The shared direct-payload protocol holds at this explicit
; marker until the target-aware session has attached and armed its first
; bounded observation.
await_session_release:
    cmpi.l  #HANDOFF_RELEASE_VALUE,HANDOFF_MARKER
    IFD RUNTIME_ALLOCATION
    bne.b   allocation_check_abort
    ELSE
    bne.b   await_session_release
    ENDC
    jmp     PAYLOAD_ENTRY.l
    IFD RUNTIME_ALLOCATION
allocation_check_abort:
    cmpi.l  #'ABRT',HANDOFF_MARKER
    bne.b   await_session_release
    move.l ALLOCATION_RECORD+20,d4
    bra.w allocation_unwind
    ENDC

failed:
    IFD RUNTIME_ALLOCATION
    bra.w allocation_unwind
    ELSE
    move.l  #'FAIL',HANDOFF_MARKER
failed_hold:
    bra.b   failed_hold
    ENDC
    IFD RUNTIME_ALLOCATION
    INCLUDE "amiga_runtime_allocation_unwind.i"
    ENDC
reservation_unowned:
    ; No marker ownership: fail closed without writing into Exec storage.
    bra.b   reservation_unowned
