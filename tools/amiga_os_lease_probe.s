; Normal DOS resource feasibility probe. No payload/takeover or game state writes.
 INCLUDE "exec/exec_lib.i"
 INCLUDE "dos/dos_lib.i"
 SECTION code,code
host_entry:
 movem.l d2-d7/a2-a6,-(sp)
 movea.l 4.w,a6
 lea claims(pc),a2
 moveq #CLAIM_COUNT-1,d7
acquire:
 move.l (a2),a1
 move.l 4(a2),d0
 jsr _LVOAllocAbs(a6)
 move.l d0,8(a2)
 lea 12(a2),a2
 dbra d7,acquire
 lea claims(pc),a2
 lea result_marks(pc),a3
 moveq #CLAIM_COUNT-1,d7
release:
 movea.l 8(a2),a1
 move.l a1,d0
 beq.b unavailable
 move.l 4(a2),d0
 jsr _LVOFreeMem(a6)
 move.b #'O',(a3)
 bra.b next
unavailable:
 move.b #'F',(a3)
next:
 addq.l #1,a3
 lea 12(a2),a2
 dbra d7,release
 lea dos_name(pc),a1
 moveq #0,d0
 jsr _LVOOpenLibrary(a6)
 tst.l d0
 beq.b done
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
done:
 moveq #0,d0
 movem.l (sp)+,d2-d7/a2-a6
 rts
 dos_name: dc.b "dos.library",0
 even
 INCLUDE "claims.i"
