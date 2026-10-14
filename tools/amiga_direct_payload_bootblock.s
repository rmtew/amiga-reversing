; Parameterized direct-payload boot shim. The generic builder supplies every
; target-specific value as a vasm definition and writes this code after the
; 12-byte AmigaDOS boot-block header.

    INCLUDE "exec/exec_lib.i"
    INCLUDE "devices/trackdisk.i"

    SECTION code,code

start:
    movea.l a1,a5
    ; Acquire the complete input backing and declared destination storage before
    ; reading any payload bytes. AllocAbs may write split free-list headers
    ; outside a requested subrange, so no allocations may follow CMD_READ.
    INCLUDE "direct_payload_reservations.i"
    move.l  #'BOOT',HANDOFF_MARKER-8
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
    bra.b   failed

handoff:
    INCLUDE "direct_payload_entry_context.i"
    move.l  #HANDOFF_VALUE,HANDOFF_MARKER
; The control client attaches after the boot code may otherwise have handed
; execution to the payload.  The shared direct-payload protocol holds at this explicit
; marker until the target-aware session has attached and armed its first
; bounded observation.
await_session_release:
    cmpi.l  #HANDOFF_RELEASE_VALUE,HANDOFF_MARKER
    bne.b   await_session_release
    jmp     PAYLOAD_ENTRY.l

failed:
    move.l  #'FAIL',HANDOFF_MARKER
failed_hold:
    bra.b   failed_hold
reservation_unowned:
    ; No marker ownership: fail closed without writing into Exec storage.
    bra.b   reservation_unowned
