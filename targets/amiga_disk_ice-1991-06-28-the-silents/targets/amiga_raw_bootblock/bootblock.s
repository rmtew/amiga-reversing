; Memory map
;   Absolute memory refs:
;     absolute[$00040000] refs=1 access=a

; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVODoIO

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/io.i"

runtime_address_00040000	EQU	$40000

    SECTION code,code
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $A382070F	; NOTE: boot checksum
	dc.l $00000370	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	movem.l d0-d7/a0-a6,-(a7)
	move.w #$2,IO_COMMAND(a1)
	move.l #$40000,IO_DATA(a1)
	move.l #$5400,IO_LENGTH(a1)
	move.l #$400,IO_OFFSET(a1)
	jsr _LVODoIO(a6)
	jmp runtime_address_00040000.l
	dc.b $4C,$DF,$7F,$FF,$43,$FA,$00,$10,$4E,$AE,$FF,$A0,$20,$40,$20,$68
	dc.b $00,$16,$70,$00,$4E,$75,$64,$6F,$73,$2E,$6C,$69,$62,$72,$61,$72
	dc.b $79
	dcb.b $3A7,$00
