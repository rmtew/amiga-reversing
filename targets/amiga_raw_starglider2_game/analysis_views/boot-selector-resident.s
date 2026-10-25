; Memory map
;   code[$00000000-$00000014] -> runtime[$00000380-$00000394] policy materialized
;   Absolute memory refs:
;     absolute[$00002662] refs=1 access=a

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

    SECTION code,code
loc_0_00000000:
    ORG $380
abs_0_00000380:
	cmpi.l #80902,(a7)
	beq.b abs_0_0000038C
	jmp $2662.w
abs_0_0000038C:
	move.l #$91,d0
	rts
