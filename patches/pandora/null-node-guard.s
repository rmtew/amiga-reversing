; Optional replacement for source $867E..$86A6 (40 bytes).
; Preserve the state exchange, but skip node writes when its pointer is NULL.
; A temporary stack push sets Z; MOVEA pops without changing it.
; Requires 12 writable, disjoint stack bytes below entry SP (original uses 8).
        move.l a0,-(sp)
        movea.l $4e(a5),a0
        move.l a0,-(sp)
        move.l $8(a0),-(sp)
        movea.l (sp)+,a0
        beq.b exchange
        bclr.b #0,$a(a0)
        clr.w $10(a0)
exchange:
        movea.l $2c(a5),a0
        move.l (a0),$4e(a5)
        move.l (sp)+,(a0)
        movea.l (sp)+,a0
        rts
