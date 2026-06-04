; Memory map
;   code[$000001A6-$0000020E] -> runtime[$00077A6A-$00077AD2] discovered_copy suppressed
;   code[$0000008C-$00000400] -> runtime[$00000400-$00000774] discovered_copy suppressed
;   code[$00000172-$000001A6] -> runtime[$00078C00-$00078C34] discovered_copy suppressed
;   code[$00000174-$000001A8] -> runtime[$00078C02-$00078C36] discovered_copy suppressed
;   Absolute memory refs:
;     absolute[$00000864] refs=1 access=a
;     absolute[$0000086C] refs=1 access=a
;     absolute[$00000898] refs=1 access=a
;     absolute[$000008B0] refs=1 access=a
;     absolute[$00009C78] refs=1 access=a
;     absolute[$00020000] refs=1 access=a
;     absolute[$00076CC0] refs=1 access=a
;     absolute[$0007FDF0] refs=1 access=r
;     absolute[$0007FFF0] refs=1 access=r

; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVODoIO

    INCLUDE "exec/exec_lib.i"
    INCLUDE "exec/io.i"
    INCLUDE "hardware/custom.i"

m68k_vector_trap_3_instruction_vector	EQU	$8C
stack_top_0007FDF0	EQU	$7FDF0
stack_top_0007FFF0	EQU	$7FFF0
runtime_code_00000400	EQU	$400
m68k_vector_trap_0_instruction_vector	EQU	$80
absolute_slot_00020000	EQU	$20000
absolute_slot_00000864	EQU	$864
absolute_slot_00009C78	EQU	$9C78
absolute_slot_00076CC0	EQU	$76CC0
runtime_code_00077A6A	EQU	$77A6A
runtime_code_00078C00	EQU	$78C00
_custom	EQU	$DFF000

    SECTION code,code
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $36C36F3C	; NOTE: boot checksum
	dc.l $00000000	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	lea.l loc_0_00000018(pc),a0
	move.l a0,m68k_vector_trap_3_instruction_vector.l
	trap #3
loc_0_00000018:
	movea.l #stack_top_0007FDF0,a7
	move a7,usp
	movea.l #stack_top_0007FFF0,a7
	lea.l loc_0_0000020E(pc),a2
	move.l a1,(a2)
	bsr.w loc_0_0000010C
	lea.l loc_0_0000020E(pc),a5
	movea.l (a5),a1
	move.l #$400,IO_OFFSET(a1)
	move.l #$4E00,IO_LENGTH(a1)
	move.l #$1E200,IO_DATA(a1)
	move.w #$2,IO_COMMAND(a1)
	movea.l $0004.w,a6
	jsr _LVODoIO(a6)
	lea.l loc_0_00000068(pc),a0
	move.l a0,m68k_vector_trap_3_instruction_vector.l
	trap #3
loc_0_00000068:
	move #$2700,sr
	lea.l loc_0_0000008C(pc),a0
	lea.l runtime_code_00000400.l,a1
	move.w #$FF,d0
loc_0_0000007A:
	move.l (a0)+,(a1)+
	dbf.w d0,loc_0_0000007A
	move.l #runtime_code_00000400,m68k_vector_trap_0_instruction_vector.l
	trap #0
loc_0_0000008C:
	move.w #$2FFF,d0
	lea.l absolute_slot_00020000.l,a0
	lea.l absolute_slot_00000864.l,a1
loc_0_0000009C:
	move.b (a0)+,(a1)+
	dbf.w d0,loc_0_0000009C
	bsr.w loc_0_00000164
	jsr $0000086C.l
	jsr $00000898.l
	lea.l absolute_slot_00009C78.l,a0
loc_0_000000B8:
	move.l (a0),d0
	beq.b loc_0_000000C2
	lea.l $0008(a0),a0
	bra.b loc_0_000000B8
loc_0_000000C2:
	lea.l -$0008(a0),a0
	lea.l loc_0_00000108(pc),a1
	move.l (a0),(a1)
	move.l #$3864,d3
	lea.l loc_0_00000102(pc),a0
	move.l a0,d1
	move.l loc_0_00000108(pc),d2
	jsr $000008B0.l
	movea.l loc_0_00000108(pc),a0
	jmp (a0)
	dc.b $33,$FC,$0F,$00,$00,$DF,$F1,$80,$33,$FC,$00,$F0,$00,$DF,$F1,$80
	dc.b $33,$FC,$00,$0F,$00,$DF,$F1,$80,$60,$E6
loc_0_00000102:
	dc.b $43,$4F,$44,$45,$00,$00
loc_0_00000108:
	dc.l $00000000	; pointer_table
loc_0_0000010C:
	bsr.b loc_0_00000164
	lea.l absolute_slot_00076CC0.l,a0
	move.w #$7CF,d0
	moveq.l #0,d1
loc_0_0000011A:
	move.l d1,(a0)+
	dbf.w d0,loc_0_0000011A
	bsr.b loc_0_00000164
	lea.l loc_0_000001A6(pc),a0
	lea.l runtime_code_00077A6A.l,a1
	move.w #$19,d0
loc_0_00000130:
	move.l (a0)+,(a1)+
	lea.l $0024(a1),a1
	dbf.w d0,loc_0_00000130
	lea.l loc_0_00000172(pc),a0
	movea.l #runtime_code_00078C00,a1
	move.l a1,-(a7)
	move.w #$19,d0
loc_0_0000014A:
	move.w (a0)+,(a1)+
	dbf.w d0,loc_0_0000014A
	move.l #$FFFFFFFE,(a1)+
	move.l (a7)+,_custom+cop1lc.l	; copper_list pointer
	move.w d0,_custom+copjmp1.l
	rts
loc_0_00000164:
	move.w _custom+vhposr.l,d0
	cmp.w #$FA00,d0
	ble.b loc_0_00000164
	rts
loc_0_00000172:
	dc.b $00,$8E,$2C,$81,$00,$90,$F4,$C1,$00,$92,$00,$38,$00,$94,$00,$D0
	dc.b $00,$E2,$6C,$C0,$00,$E0,$00,$07,$01,$04,$00,$00,$01,$02,$00,$00
	dc.b $00,$96,$83,$80,$01,$00,$12,$00,$01,$08,$00,$00,$01,$80,$00,$00
	dc.b $01,$82,$0F,$50
loc_0_000001A6:
	dc.b $00,$03,$00,$00,$00,$03,$00,$00,$03,$FF,$FF,$00,$03,$FF,$FF,$00
	dc.b $03,$00,$03,$00,$03,$00,$03,$00,$03,$3F,$F3,$00,$03,$3F,$F3,$00
	dc.b $00,$03,$00,$00,$00,$03,$00,$00,$FF,$F3,$3F,$FC,$FF,$F3,$3F,$FC
	dc.b $C0,$C3,$0C,$0C,$C0,$C3,$0C,$0C,$FF,$F3,$3F,$FC,$FF,$F3,$3F,$FC
	dc.b $00,$03,$00,$00,$00,$03,$00,$00,$03,$3F,$F3,$00,$03,$3F,$F3,$00
	dc.b $03,$00,$03,$00,$03,$00,$03,$00,$03,$FF,$FF,$00,$03,$FF,$FF,$00
	dc.b $00,$03,$00,$00,$00,$03,$00,$00
loc_0_0000020E:
	dc.b $00,$00,$00,$00,$4E,$71,$4E,$71
	dcb.b $6A,$00
	dc.b "The level codes are: Auriga, Cepheus, Apus, Musca, Pyxis,Cetus, Fornax, Caelum, Corvus !",$00
	dcb.b $67,$00
	dcb.b $40,$2D
	dcb.b $1D,$20
	dc.b $46,$55,$53,$49,$4F,$4E
	dcb.b $1D,$20
	dcb.b $40,$2D
