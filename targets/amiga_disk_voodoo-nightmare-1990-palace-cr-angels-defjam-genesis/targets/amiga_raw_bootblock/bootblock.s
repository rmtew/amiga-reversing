; Memory map
;   code[$00000000-$00000400] -> runtime[$00070000-$00070400] policy materialized

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/resident.i"


    SECTION code,code
    ORG $70000
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $C0200F19	; NOTE: boot checksum
	dc.l $00000370	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	lea.l abs_0_00070026(pc),a1
	jsr _LVOFindResident(a6)
	tst.l d0
	beq.b abs_0_00070022
	movea.l d0,a0
	movea.l RT_INIT(a0),a0
	moveq.l #0,d0
abs_0_00070020:
	rts
abs_0_00070022:
	moveq.l #-1,d0
	bra.b abs_0_00070020
abs_0_00070026:
	dc.b "dos.library",$00	; string
	dcb.b $3CE,$00
