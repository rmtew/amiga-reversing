; Typed native field table, validated completely before any payload mutation.
validate_runtime_fields:
    lea state_owners-host_state(a5),a0
    lea owner_sizes(pc),a1
    moveq #OWNER_COUNT-1,d7
validate_actual_owner:
    move.l (a0)+,d0
    cmpi.l #$400,d0
    bcs.w fields_invalid
    move.l d0,d1
    andi.l #7,d1
    bne.w fields_invalid
    add.l (a1)+,d0
    bcs.w fields_invalid
    cmpi.l #$100000,d0
    bhi.w fields_invalid
    dbra d7,validate_actual_owner
    lea runtime_fields(pc),a2
    move.w #FIXUP_COUNT-1,d7
validate_next_field:
    bsr.w decode_runtime_field
    cmpi.w #2,d5
    bne.b validate_LONG_field
    cmpi.l #$7FFF,d0
    bhi.w fields_invalid
    moveq #0,d1
    move.w (a1),d1
    cmp.l d3,d1
    bne.w fields_invalid
    bra.b field_valid
validate_LONG_field:
    cmp.l (a1),d3
    bne.w fields_invalid
field_valid:
    dbra d7,validate_next_field
    moveq #1,d0
    rts
fields_invalid:
    moveq #0,d0
    rts
apply_runtime_fields:
    lea runtime_fields(pc),a2
    move.w #FIXUP_COUNT-1,d7
apply_next_field:
    bsr.b decode_runtime_field
    cmpi.w #2,d5
    bne.b apply_LONG_field
    move.w d0,(a1)
    bra.b field_applied
apply_LONG_field:
    move.l d0,(a1)
field_applied:
    dbra d7,apply_next_field
    ; This is the sole explicitly annotated external service import. The whole
    ; input and original operand were checked before the apply pass.
    lea mission_restart_dispatch(pc),a0
    move.l a0,INPUT_ADDRESS+EXIT_IMPORT_OFFSET
    INCLUDE "pandora_OS_seeds.i"
    rts
decode_runtime_field:
    move.l (a2)+,d2
    move.l (a2)+,d3
    move.w (a2)+,d4
    move.w (a2)+,d5
    move.l (a2)+,d6
    lea state_owners-host_state(a5),a0
    move.l 0(a0,d4.w),d0
    add.l d6,d0
    movea.l #INPUT_ADDRESS,a1
    adda.l d2,a1
    rts
