; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVOSupervisor

    INCLUDE "exec/exec_lib.i"

    RSSET 0
    RS.B 297
app_0129 RS.B 1
app_SIZEOF EQU __RS


    SECTION section,code
loc_0_00000000:
	movea.l $0004.w,a6
	btst.b #1,app_0129(a6)
	beq.b loc_0_00000014
	lea.l loc_0_00000018(pc),a5
	jsr _LVOSupervisor(a6)
loc_0_00000014:
	clr.l d0
	rts
loc_0_00000018:
	dc.b $4E,$7A,$00,$02,$02,$40,$EE,$EE,$4E,$7B,$00,$02,$4E,$73,$00,$00
