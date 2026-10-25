; Memory map
;   code[$00000000-$00000028] -> runtime[$00000024-$0000004C] policy materialized
;   code[$00000014-$00000028] -> runtime[$00000380-$00000394] discovered_copy suppressed
;   code[$00000018-$00000028] -> runtime[$00000384-$00000394] discovered_copy suppressed
;   Absolute memory refs:
;     absolute[$00000200] refs=1 access=a

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

runtime_code_00000380	EQU	$380

    SECTION code,code
loc_0_00000000:
    ORG $24
abs_0_00000024:
	lea.l abs_0_00000038(pc),a0
	lea.l runtime_code_00000380.w,a2
	moveq.l #4,d0
abs_0_0000002E:
	move.l (a0)+,(a2)+
	dbf.w d0,abs_0_0000002E
	jmp $0200.w
abs_0_00000038:
	dc.b $0C,$97,$00,$01,$3C,$06,$67,$04,$4E,$F8,$26,$62,$20,$3C,$00,$00
	dc.b $00,$91,$4E,$75
