; Own normal AmigaDOS entry/RTS probe. No game code or takeover is involved.
; PROBE_INDEX selects the two sequential Startup-Sequence witnesses.
    INCLUDE "exec/exec_lib.i"
    INCLUDE "dos/dos_lib.i"
    SECTION code,code
entry:
    movem.l d2-d7/a2-a6,-(a7)
    movea.l $4.w,a6
    lea dos_name(pc),a1
    moveq #0,d0
    jsr _LVOOpenLibrary(a6)
    tst.l d0
    beq.b failed
    movea.l d0,a6
    jsr _LVOOutput(a6)
    move.l d0,d1
    lea message(pc),a0
    move.l a0,d2
    moveq #message_end-message,d3
    jsr _LVOWrite(a6)
    movea.l a6,a1
    movea.l $4.w,a6
    jsr _LVOCloseLibrary(a6)
    moveq #0,d0
    bra.b done
failed:
    moveq #20,d0
done:
    movem.l (a7)+,d2-d7/a2-a6
    rts
dos_name:
    dc.b "dos.library",0
message:
    dc.b "PANDORA HOST ENTRY "
    dc.b '0'+PROBE_INDEX
    dc.b " - NORMAL CLI EXECUTABLE",10
message_end:
