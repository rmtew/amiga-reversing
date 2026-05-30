; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVOOpenLibrary, _LVOCloseLibrary, _LVOFindResident

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/resident.i"
    INCLUDE "libraries/expansionbase.i"


    SECTION code,code
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $42454552	; NOTE: boot checksum
	dc.l $00000370	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	lea.l loc_0_0000004C(pc),a1
	moveq.l #37,d0
	jsr _LVOOpenLibrary(a6)
	tst.l d0
	beq.b loc_0_00000026
	movea.l d0,a1
	bset.b #6,eb_Flags(a1)
	jsr _LVOCloseLibrary(a6)
loc_0_00000026:
	lea.l loc_0_00000040(pc),a1
	jsr _LVOFindResident(a6)
	tst.l d0
	beq.b loc_0_0000003C
	movea.l d0,a0
	movea.l RT_INIT(a0),a0
	moveq.l #0,d0
	rts
loc_0_0000003C:
	moveq.l #-1,d0
	rts
loc_0_00000040:
	dc.b "dos.library",$00
loc_0_0000004C:
	dc.b "expansion.library",$00
	dc.b $00,$00,$A0,$F7,$C9,$21
	dcb.b $39C,$00
