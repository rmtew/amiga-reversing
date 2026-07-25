; Parameterized direct-payload boot shim. The generic builder supplies every
; target-specific value as a vasm definition and writes this code after the
; 12-byte AmigaDOS boot-block header.

    INCLUDE "exec/exec_lib.i"
    INCLUDE "devices/trackdisk.i"

    SECTION code,code

start:
    move.l  #'BOOT',HANDOFF_MARKER-8
    movea.l a1,a5
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
    move.l  #HANDOFF_VALUE,HANDOFF_MARKER
    jmp     PAYLOAD_ENTRY.l

failed:
    moveq   #1,d0
    rts
