    INCLUDE "exec/exec_lib.i"
    INCLUDE "hardware/custom.i"

m68k_vector_trap_3_instruction_vector	EQU	$8C
stack_top_0007FDF0	EQU	$7FDF0
stack_top_0007FFF0	EQU	$7FFF0
runtime_code_00000400	EQU	$400
m68k_vector_trap_0_instruction_vector	EQU	$80
_custom	EQU	$DFF000

    SECTION code,code
    ORG $70000
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $36C36F3C	; NOTE: boot checksum
	dc.l $00000000	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	lea.l abs_0_00070018(pc),a0
	move.l a0,m68k_vector_trap_3_instruction_vector.l
	trap #3
abs_0_00070018:
	movea.l #stack_top_0007FDF0,a7
	move a7,usp
	movea.l #stack_top_0007FFF0,a7
	lea.l abs_0_0007020E(pc),a2
	move.l a1,(a2)
	bsr.w abs_0_0007010C
	lea.l abs_0_0007020E(pc),a5
	movea.l (a5),a1
	move.l #$400,$002C(a1)
	move.l #$4E00,$0024(a1)
	move.l #$1E200,$0028(a1)
	move.w #$2,$001C(a1)
	movea.l $0004.w,a6
	jsr _LVODoIO(a6)
	lea.l abs_0_00070068(pc),a0
	move.l a0,m68k_vector_trap_3_instruction_vector.l
	trap #3
abs_0_00070068:
	move #$2700,sr
	lea.l abs_0_0007008C(pc),a0
	lea.l runtime_code_00000400.l,a1
	move.w #$FF,d0
abs_0_0007007A:
	move.l (a0)+,(a1)+
	dbf.w d0,abs_0_0007007A
	move.l #runtime_code_00000400,m68k_vector_trap_0_instruction_vector.l
	trap #0
abs_0_0007008C:
	move.w #$2FFF,d0
	lea.l $00020000.l,a0
	lea.l $00000864.l,a1
abs_0_0007009C:
	move.b (a0)+,(a1)+
	dbf.w d0,abs_0_0007009C
	bsr.w abs_0_00070164
	jsr $0000086C.l
	jsr $00000898.l
	lea.l $00009C78.l,a0
abs_0_000700B8:
	move.l (a0),d0
	beq.b abs_0_000700C2
	lea.l $0008(a0),a0
	bra.b abs_0_000700B8
abs_0_000700C2:
	lea.l -$0008(a0),a0
	lea.l abs_0_00070108(pc),a1
	move.l (a0),(a1)
	move.l #$3864,d3
	lea.l abs_0_00070102(pc),a0
	move.l a0,d1
	move.l abs_0_00070108(pc),d2
	jsr $000008B0.l
	movea.l abs_0_00070108(pc),a0
	jmp (a0)
	dc.b $33,$FC,$0F,$00,$00,$DF,$F1,$80,$33,$FC,$00,$F0,$00,$DF,$F1,$80
	dc.b $33,$FC,$00,$0F,$00,$DF,$F1,$80,$60,$E6
abs_0_00070102:
	dc.b $43,$4F,$44,$45,$00,$00
abs_0_00070108:
	dc.l $00000000	; lookup_table
abs_0_0007010C:
	bsr.b abs_0_00070164
	lea.l $00076CC0.l,a0
	move.w #$7CF,d0
	moveq.l #0,d1
abs_0_0007011A:
	move.l d1,(a0)+
	dbf.w d0,abs_0_0007011A
	bsr.b abs_0_00070164
	lea.l abs_0_000701A6(pc),a0
	lea.l $00077A6A.l,a1
	move.w #$19,d0
abs_0_00070130:
	move.l (a0)+,(a1)+
	lea.l $0024(a1),a1
	dbf.w d0,abs_0_00070130
	lea.l abs_0_00070172(pc),a0
	movea.l #$78C00,a1
	move.l a1,-(a7)
	move.w #$19,d0
abs_0_0007014A:
	move.w (a0)+,(a1)+
	dbf.w d0,abs_0_0007014A
	move.l #$FFFFFFFE,(a1)+
	move.l (a7)+,_custom+cop1lc.l	; copper_list pointer
	move.w d0,_custom+copjmp1.l
	rts
abs_0_00070164:
	move.w _custom+vhposr.l,d0
	cmp.w #$FA00,d0
	ble.b abs_0_00070164
	rts
abs_0_00070172:
	dc.b $00,$8E,$2C,$81,$00,$90,$F4,$C1,$00,$92,$00,$38,$00,$94,$00,$D0
	dc.b $00,$E2,$6C,$C0,$00,$E0,$00,$07,$01,$04,$00,$00,$01,$02,$00,$00
	dc.b $00,$96,$83,$80,$01,$00,$12,$00,$01,$08,$00,$00,$01,$80,$00,$00
	dc.b $01,$82,$0F,$50
abs_0_000701A6:
	dc.b $00,$03,$00,$00,$00,$03,$00,$00,$03,$FF,$FF,$00,$03,$FF,$FF,$00
	dc.b $03,$00,$03,$00,$03,$00,$03,$00,$03,$3F,$F3,$00,$03,$3F,$F3,$00
	dc.b $00,$03,$00,$00,$00,$03,$00,$00,$FF,$F3,$3F,$FC,$FF,$F3,$3F,$FC
	dc.b $C0,$C3,$0C,$0C,$C0,$C3,$0C,$0C,$FF,$F3,$3F,$FC,$FF,$F3,$3F,$FC
	dc.b $00,$03,$00,$00,$00,$03,$00,$00,$03,$3F,$F3,$00,$03,$3F,$F3,$00
	dc.b $03,$00,$03,$00,$03,$00,$03,$00,$03,$FF,$FF,$00,$03,$FF,$FF,$00
	dc.b $00,$03,$00,$00,$00,$03,$00,$00
abs_0_0007020E:
	dc.b $00,$00,$00,$00,$4E,$71,$4E,$71
	dcb.b $6A,$00
	dc.b "The level codes are: Auriga, Cepheus, Apus, Musca, Pyxis,Cetus, Fornax, Caelum, Corvus !",$00	; string
	dcb.b $67,$00
	dcb.b $40,$2D
	dcb.b $1D,$20
	dc.b $46,$55,$53,$49,$4F,$4E
	dcb.b $1D,$20
	dcb.b $40,$2D
