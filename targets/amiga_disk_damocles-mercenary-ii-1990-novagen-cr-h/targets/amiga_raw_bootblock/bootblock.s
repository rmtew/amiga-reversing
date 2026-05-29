; OS compatibility
;   minimum required: 1.3
;   observed API availability: 1.3
;   observed FD/interface versions: none
;   max requirement drivers:
;     _LVOFindResident at section_0+$00000010 requires 1.3

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/resident.i"


    SECTION code,code
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $57200F19	; NOTE: boot checksum
	dc.l $00000370	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	lea.l loc_0_00000026(pc),a1
	jsr _LVOFindResident(a6)
	tst.l d0
	beq.b loc_0_00000022
	movea.l d0,a0
	movea.l RT_INIT(a0),a0
	moveq.l #0,d0
loc_0_00000020:
	rts
loc_0_00000022:
	moveq.l #-1,d0
	bra.b loc_0_00000020
loc_0_00000026:
	dc.b "dos.library",$00
	dc.b $00,$00,$69
	dcb.b $3CB,$00
