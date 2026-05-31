; Memory map
;   code[$0000004C-$00000400] -> runtime[$00000200-$000005B4] discovered_copy materialized
;   code[$00000038-$0000004C] -> runtime[$00000380-$00000394] conflicting_discovered_copy suppressed
;   Absolute memory refs:
;     absolute[$00024000] refs=1 access=a
;     absolute[$00FC0000] refs=1 access=a

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/dmabits.i"

runtime_address_00024000	EQU	$24000
_custom	EQU	$DFF000
m68k_vector_trap_0_instruction_vector	EQU	$80
runtime_address_0001A000	EQU	$1A000
runtime_address_00FC0000	EQU	$FC0000

    SECTION code,code
	dc.b "DOS",$00	; NOTE: boot magic
	dc.l $DF65C1C7	; NOTE: boot checksum
	dc.l $00000003	; NOTE: boot root block
    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO
boot_entry:
	lea.l loc_0_00000118-(*+2)(pc),a0
	move.l a1,(a0)
	lea.l loc_0_0000004C-(*+2)(pc),a0
	lea.l loc_0_0000011C-(*+2)(pc),a2
	lea.l abs_0_00000200.w,a3
loc_0_0000001E:
	move.l (a0)+,(a3)+
	cmpa.l a2,a0
	ble.b loc_0_0000001E
	lea.l loc_0_00000038(pc),a0
	lea.l abs_0_00000380.w,a2
	moveq.l #4,d0
loc_0_0000002E:
	move.l (a0)+,(a2)+
	dbf.w d0,loc_0_0000002E
	jmp abs_0_00000200.w
loc_0_00000038:
	dc.b $0C,$97,$00,$01,$3C,$06,$67,$04,$4E,$F8,$26,$62,$20,$3C,$00,$00
	dc.b $00,$91,$4E,$75
loc_0_0000004C:
    ORG $200
abs_0_00000200:
	movea.l abs_0_000002CC(pc),a1
	move.w #$2,$001C(a1)
	move.l #$DA00,$0024(a1)
	move.l #$23FF8,$0028(a1)
	move.l #$2C00,$002C(a1)
	jsr -$01C8(a6)
	tst.l d0
	bne.w abs_0_000002C6
	movea.l abs_0_000002CC(pc),a1
	move.w #$9,$001C(a1)
	clr.l $0024(a1)
	jsr -$01C8(a6)
	jsr runtime_address_00024000.l
	move.w #DMAF_RASTER|DMAF_COPPER|DMAF_SPRITE,_custom+dmacon.l
	move.w #$80,_custom+color.l
	movea.l abs_0_000002CC(pc),a1
	move.w #$2,$001C(a1)
	move.l #$64E00,$0024(a1)
	move.l #$1A000,$0028(a1)
	move.l #$16000,$002C(a1)
	jsr -$01C8(a6)
	tst.l d0
	bne.b abs_0_000002C6
	lea.l _custom.l,a6
	move.w #$7FFF,d0
	move.w d0,intreq(a6)
	move.w d0,intena(a6)
	move.w d0,dmacon(a6)
	move.w #$F,color(a6)
	lea.l abs_0_000002A4(pc),a0
	move.l a0,m68k_vector_trap_0_instruction_vector.w
	trap #0
abs_0_000002A4:
	movea.l #runtime_address_0001A000,a0
	movea.l #$1000,a1
	move.l #$19310,d0
abs_0_000002B6:
	move.l (a0)+,(a1)+
	subq.l #1,d0
	bne.b abs_0_000002B6
	move.w #$F00,$0180(a6)
	jmp $1000.w
abs_0_000002C6:
	jmp runtime_address_00FC0000.l
    ORG $118
loc_0_00000118:
    ORG $2CC
abs_0_000002CC:
	dc.l $00000000	; lookup_table
    ORG $11C
loc_0_0000011C:
    ORG $2D0
abs_0_000002D0:
	dcb.b $B0,$00
abs_0_00000380:
	dcb.b $234,$00
