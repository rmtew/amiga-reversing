; Classic Mac OS target artifact: MPW Tools Asm
; Renderer: amiga_reversing.disasm.macos_target_artifact
; Source image: resources/platform_macos/MPW-GM.img.bin
; HFS path: MPW-GM/MPW/Tools/Asm
; Finder type: MPST
; Finder creator: MPS 
; CNID: 2310
;
; This is an illustrative source artifact, not an MPW round-trip contract.
; Durable input comes from the C-backed HFS/resource/CODE summary and shared m68k listing renderer.

; CODE source body sections

; CODE 0 unknown source section
macos_code_CODE_0:
;   source_section_id: macos-code-CODE-0
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: covered_placeholder
;   resource_type: CODE
;   id: 0
;   name: unknown
;   role: code0_metadata
;   code_kind: jump_table_segment
;   payload_size: 2784
;   payload_sha256: 8413f3bca1604845bb778c2a7701a067aa8b84853e7c77a60e63166d5b6399c1
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:0
;   listing: kind=metadata available=False reason=CODE 0 is jump-table/application metadata, not ordinary m68k code
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 0 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..2784 status=validated parser_use=accepted_parser_output reason=code0_jump_table_metadata
;     source_reference_records:
;       0: kind=code0_routing_table ownership=unknown status=validated parser_use=accepted_parser_output target=CODE resource dispatch table
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..2784) size=2784 entrypoint=False status=validated parser_use=accepted_parser_output evidence=code0_jump_table_metadata fact=macos.code_resource.0.jump_table_metadata
;   structured_CODE0_context:
macos_CODE_0_application_metadata:
;     above/below A5 metadata and jump-table header are accepted CODE 0 metadata.
;     jump_table payload[16..2784) entry_size=8 entry_count=346 status=validated parser_use=accepted_parser_output fact=macos.jump_table.entries.accepted
macos_CODE_0_jump_table:
macos_CODE_0_jump_table_entry_0:
;     payload_offset=16 size=8 raw_entry_bytes=00 00 3F 3C 00 1B A9 F0
;     accepted_layout status=validated parser_use=accepted_parser_output fact=macos.jump_table.entries.accepted
;     candidate_target target_section=macos_code_CODE_27 target_resource_id=27 routine_offset=0 status=candidate parser_use=candidate_only fact=macos.code_resource.jump_table.routine_offsets.candidate
;     generated_xref source=macos_CODE_0_jump_table_entry_0 target=macos_code_CODE_27_routine_candidate_000000cc link_status=linked_candidate
;   byte_preserving_placeholder: CODE 0 payload[0..2784) sha256=8413f3bca1604845bb778c2a7701a067aa8b84853e7c77a60e63166d5b6399c1
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..2784) status=validated parser_use=accepted_parser_output evidence=code0_jump_table_metadata
macos_code_CODE_0_metadata_00000000:
	dc.b $00,$00,$0A,$F0,$00,$00,$39,$20,$00,$00,$0A,$D0,$00,$00,$00,$20
	dc.b $00,$00,$3F,$3C,$00,$1B,$A9,$F0,$00,$00,$FF,$FF,$00,$00,$00,$00
	dc.b $00,$01,$A9,$F0,$00,$00,$60,$1E,$00,$01,$A9,$F0,$00,$00,$00,$3E
	dc.b $00,$01,$A9,$F0,$00,$00,$00,$46,$00,$01,$A9,$F0,$00,$00,$00,$5E
	dc.b $00,$01,$A9,$F0,$00,$00,$00,$76,$00,$01,$A9,$F0,$00,$00,$00,$9A
	dc.b $00,$01,$A9,$F0,$00,$00,$00,$BE,$00,$01,$A9,$F0,$00,$00,$00,$BE
	dc.b $00,$01,$A9,$F0,$00,$00,$01,$08,$00,$01,$A9,$F0,$00,$00,$01,$42
	dc.b $00,$01,$A9,$F0,$00,$00,$01,$66,$00,$01,$A9,$F0,$00,$00,$01,$72
	dc.b $00,$01,$A9,$F0,$00,$00,$01,$90,$00,$01,$A9,$F0,$00,$00,$01,$A4
	dc.b $00,$01,$A9,$F0,$00,$00,$01,$BE,$00,$01,$A9,$F0,$00,$00,$01,$D4
	dc.b $00,$01,$A9,$F0,$00,$00,$01,$D8,$00,$01,$A9,$F0,$00,$00,$02,$44
	dc.b $00,$01,$A9,$F0,$00,$00,$02,$3E,$00,$01,$A9,$F0,$00,$00,$03,$1C
	dc.b $00,$01,$A9,$F0,$00,$00,$03,$D8,$00,$01,$A9,$F0,$00,$00,$04,$0C
	dc.b $00,$01,$A9,$F0,$00,$00,$04,$96,$00,$01,$A9,$F0,$00,$00,$04,$9E
	dc.b $00,$01,$A9,$F0,$00,$00,$05,$78,$00,$01,$A9,$F0,$00,$00,$05,$80
	dc.b $00,$01,$A9,$F0,$00,$00,$06,$06,$00,$01,$A9,$F0,$00,$00,$06,$0E
	dc.b $00,$01,$A9,$F0,$00,$00,$07,$14,$00,$01,$A9,$F0,$00,$00,$07,$1C
	dc.b $00,$01,$A9,$F0,$00,$00,$07,$C8,$00,$01,$A9,$F0,$00,$00,$07,$E4
	dc.b $00,$01,$A9,$F0,$00,$00,$0A,$FE,$00,$01,$A9,$F0,$00,$00,$0F,$60
	dc.b $00,$01,$A9,$F0,$00,$00,$0F,$7A,$00,$01,$A9,$F0,$00,$00,$11,$DC
	dc.b $00,$01,$A9,$F0,$00,$00,$11,$F4,$00,$01,$A9,$F0,$00,$00,$12,$72
	dc.b $00,$01,$A9,$F0,$00,$00,$12,$C2,$00,$01,$A9,$F0,$00,$00,$13,$14
	dc.b $00,$01,$A9,$F0,$00,$00,$13,$3E,$00,$01,$A9,$F0,$00,$00,$1B,$60
	dc.b $00,$01,$A9,$F0,$00,$00,$1B,$26,$00,$01,$A9,$F0,$00,$00,$1C,$72
	dc.b $00,$01,$A9,$F0,$00,$00,$1D,$28,$00,$01,$A9,$F0,$00,$00,$20,$30
	dc.b $00,$01,$A9,$F0,$00,$00,$20,$4A,$00,$01,$A9,$F0,$00,$00,$20,$70
	dc.b $00,$01,$A9,$F0,$00,$00,$20,$A8,$00,$01,$A9,$F0,$00,$00,$21,$F0
	dc.b $00,$01,$A9,$F0,$00,$00,$22,$F6,$00,$01,$A9,$F0,$00,$00,$23,$66
	dc.b $00,$01,$A9,$F0,$00,$00,$24,$92,$00,$01,$A9,$F0,$00,$00,$25,$BA
	dc.b $00,$01,$A9,$F0,$00,$00,$26,$5E,$00,$01,$A9,$F0,$00,$00,$26,$74
	dc.b $00,$01,$A9,$F0,$00,$00,$27,$30,$00,$01,$A9,$F0,$00,$00,$27,$DE
	dc.b $00,$01,$A9,$F0,$00,$00,$28,$2E,$00,$01,$A9,$F0,$00,$00,$28,$B8
	dc.b $00,$01,$A9,$F0,$00,$00,$29,$CA,$00,$01,$A9,$F0,$00,$00,$2B,$AC
	dc.b $00,$01,$A9,$F0,$00,$00,$30,$58,$00,$01,$A9,$F0,$00,$00,$3D,$90
	dc.b $00,$01,$A9,$F0,$00,$00,$4E,$D2,$00,$01,$A9,$F0,$00,$00,$53,$36
	dc.b $00,$01,$A9,$F0,$00,$00,$53,$AC,$00,$01,$A9,$F0,$00,$00,$54,$76
	dc.b $00,$01,$A9,$F0,$00,$00,$55,$1C,$00,$01,$A9,$F0,$00,$00,$57,$A8
	dc.b $00,$01,$A9,$F0,$00,$00,$5F,$BE,$00,$01,$A9,$F0,$00,$00,$61,$12
	dc.b $00,$01,$A9,$F0,$00,$00,$61,$A2,$00,$01,$A9,$F0,$00,$00,$61,$C8
	dc.b $00,$01,$A9,$F0,$00,$00,$61,$EC,$00,$01,$A9,$F0,$00,$00,$62,$CA
	dc.b $00,$01,$A9,$F0,$00,$00,$63,$A2,$00,$01,$A9,$F0,$00,$00,$64,$18
	dc.b $00,$01,$A9,$F0,$00,$00,$64,$56,$00,$01,$A9,$F0,$00,$00,$65,$88
	dc.b $00,$01,$A9,$F0,$00,$00,$68,$32,$00,$01,$A9,$F0,$00,$00,$68,$B4
	dc.b $00,$01,$A9,$F0,$00,$00,$68,$BE,$00,$01,$A9,$F0,$00,$00,$68,$CC
	dc.b $00,$01,$A9,$F0,$00,$00,$69,$04,$00,$01,$A9,$F0,$00,$00,$69,$44
	dc.b $00,$01,$A9,$F0,$00,$00,$69,$56,$00,$01,$A9,$F0,$00,$00,$69,$68
	dc.b $00,$01,$A9,$F0,$00,$00,$69,$7A,$00,$01,$A9,$F0,$00,$00,$69,$94
	dc.b $00,$01,$A9,$F0,$00,$00,$69,$98,$00,$01,$A9,$F0,$00,$00,$69,$DC
	dc.b $00,$01,$A9,$F0,$00,$00,$6A,$12,$00,$01,$A9,$F0,$00,$00,$6A,$36
	dc.b $00,$01,$A9,$F0,$00,$00,$6A,$62,$00,$01,$A9,$F0,$00,$00,$6A,$9C
	dc.b $00,$01,$A9,$F0,$00,$00,$6A,$BC,$00,$01,$A9,$F0,$00,$00,$6A,$DE
	dc.b $00,$01,$A9,$F0,$00,$00,$6B,$16,$00,$01,$A9,$F0,$00,$00,$6B,$2C
	dc.b $00,$01,$A9,$F0,$00,$00,$6B,$42,$00,$01,$A9,$F0,$00,$00,$6B,$54
	dc.b $00,$01,$A9,$F0,$00,$00,$6B,$66,$00,$01,$A9,$F0,$00,$00,$6B,$AE
	dc.b $00,$01,$A9,$F0,$00,$00,$6B,$F6,$00,$01,$A9,$F0,$00,$00,$6C,$36
	dc.b $00,$01,$A9,$F0,$00,$00,$6C,$94,$00,$01,$A9,$F0,$00,$00,$6D,$0E
	dc.b $00,$01,$A9,$F0,$00,$00,$6F,$1C,$00,$01,$A9,$F0,$00,$00,$6F,$2E
	dc.b $00,$01,$A9,$F0,$00,$00,$6F,$64,$00,$01,$A9,$F0,$00,$00,$70,$4C
	dc.b $00,$01,$A9,$F0,$00,$00,$70,$A2,$00,$01,$A9,$F0,$00,$00,$70,$C6
	dc.b $00,$02,$A9,$F0,$00,$00,$00,$28,$00,$02,$A9,$F0,$00,$00,$00,$AC
	dc.b $00,$02,$A9,$F0,$00,$00,$01,$88,$00,$02,$A9,$F0,$00,$00,$01,$C2
	dc.b $00,$02,$A9,$F0,$00,$00,$17,$DA,$00,$02,$A9,$F0,$00,$00,$1B,$4A
	dc.b $00,$02,$A9,$F0,$00,$00,$1B,$F2,$00,$03,$A9,$F0,$00,$00,$00,$40
	dc.b $00,$03,$A9,$F0,$00,$00,$38,$F6,$00,$03,$A9,$F0,$00,$00,$44,$3E
	dc.b $00,$04,$A9,$F0,$00,$00,$00,$28,$00,$04,$A9,$F0,$00,$00,$01,$34
	dc.b $00,$04,$A9,$F0,$00,$00,$01,$EE,$00,$04,$A9,$F0,$00,$00,$02,$40
	dc.b $00,$04,$A9,$F0,$00,$00,$02,$94,$00,$04,$A9,$F0,$00,$00,$02,$EA
	dc.b $00,$04,$A9,$F0,$00,$00,$03,$0C,$00,$04,$A9,$F0,$00,$00,$03,$A6
	dc.b $00,$04,$A9,$F0,$00,$00,$08,$06,$00,$04,$A9,$F0,$00,$00,$0C,$42
	dc.b $00,$04,$A9,$F0,$00,$00,$0E,$82,$00,$04,$A9,$F0,$00,$00,$14,$36
	dc.b $00,$04,$A9,$F0,$00,$00,$15,$AE,$00,$04,$A9,$F0,$00,$00,$15,$E2
	dc.b $00,$04,$A9,$F0,$00,$00,$17,$28,$00,$04,$A9,$F0,$00,$00,$17,$60
	dc.b $00,$04,$A9,$F0,$00,$00,$18,$10,$00,$04,$A9,$F0,$00,$00,$18,$62
	dc.b $00,$04,$A9,$F0,$00,$00,$18,$AA,$00,$04,$A9,$F0,$00,$00,$18,$FE
	dc.b $00,$05,$A9,$F0,$00,$00,$00,$28,$00,$05,$A9,$F0,$00,$00,$00,$D2
	dc.b $00,$05,$A9,$F0,$00,$00,$00,$EA,$00,$05,$A9,$F0,$00,$00,$03,$68
	dc.b $00,$05,$A9,$F0,$00,$00,$03,$6C,$00,$05,$A9,$F0,$00,$00,$05,$9A
	dc.b $00,$05,$A9,$F0,$00,$00,$05,$E8,$00,$05,$A9,$F0,$00,$00,$0A,$48
	dc.b $00,$05,$A9,$F0,$00,$00,$13,$E0,$00,$05,$A9,$F0,$00,$00,$14,$B6
	dc.b $00,$05,$A9,$F0,$00,$00,$15,$EC,$00,$05,$A9,$F0,$00,$00,$16,$FC
	dc.b $00,$05,$A9,$F0,$00,$00,$18,$56,$00,$05,$A9,$F0,$00,$00,$18,$90
	dc.b $00,$05,$A9,$F0,$00,$00,$19,$98,$00,$05,$A9,$F0,$00,$00,$20,$38
	dc.b $00,$05,$A9,$F0,$00,$00,$25,$68,$00,$05,$A9,$F0,$00,$00,$2F,$68
	dc.b $00,$05,$A9,$F0,$00,$00,$3A,$C2,$00,$05,$A9,$F0,$00,$00,$56,$52
	dc.b $00,$05,$A9,$F0,$00,$00,$5C,$AE,$00,$05,$A9,$F0,$00,$00,$5F,$16
	dc.b $00,$05,$A9,$F0,$00,$00,$67,$50,$00,$06,$A9,$F0,$00,$00,$00,$28
	dc.b $00,$06,$A9,$F0,$00,$00,$00,$F0,$00,$06,$A9,$F0,$00,$00,$01,$2A
	dc.b $00,$06,$A9,$F0,$00,$00,$02,$E0,$00,$06,$A9,$F0,$00,$00,$16,$5C
	dc.b $00,$06,$A9,$F0,$00,$00,$05,$74,$00,$06,$A9,$F0,$00,$00,$04,$88
	dc.b $00,$06,$A9,$F0,$00,$00,$16,$8E,$00,$06,$A9,$F0,$00,$00,$3B,$16
	dc.b $00,$07,$A9,$F0,$00,$00,$00,$28,$00,$07,$A9,$F0,$00,$00,$00,$AC
	dc.b $00,$07,$A9,$F0,$00,$00,$01,$72,$00,$07,$A9,$F0,$00,$00,$01,$AC
	dc.b $00,$07,$A9,$F0,$00,$00,$0C,$58,$00,$07,$A9,$F0,$00,$00,$0F,$DE
	dc.b $00,$08,$A9,$F0,$00,$00,$00,$DC,$00,$08,$A9,$F0,$00,$00,$01,$04
	dc.b $00,$08,$A9,$F0,$00,$00,$02,$A6,$00,$08,$A9,$F0,$00,$00,$03,$1A
	dc.b $00,$08,$A9,$F0,$00,$00,$04,$18,$00,$08,$A9,$F0,$00,$00,$04,$6C
	dc.b $00,$08,$A9,$F0,$00,$00,$06,$5E,$00,$09,$A9,$F0,$00,$00,$00,$28
	dc.b $00,$09,$A9,$F0,$00,$00,$00,$CE,$00,$09,$A9,$F0,$00,$00,$00,$EE
	dc.b $00,$09,$A9,$F0,$00,$00,$04,$7A,$00,$09,$A9,$F0,$00,$00,$10,$A0
	dc.b $00,$09,$A9,$F0,$00,$00,$10,$34,$00,$09,$A9,$F0,$00,$00,$0F,$A2
	dc.b $00,$09,$A9,$F0,$00,$00,$31,$BE,$00,$09,$A9,$F0,$00,$00,$36,$50
	dc.b $00,$0A,$A9,$F0,$00,$00,$00,$28,$00,$0A,$A9,$F0,$00,$00,$01,$36
	dc.b $00,$0B,$A9,$F0,$00,$00,$00,$90,$00,$0B,$A9,$F0,$00,$00,$00,$DC
	dc.b $00,$0B,$A9,$F0,$00,$00,$03,$B2,$00,$0B,$A9,$F0,$00,$00,$04,$08
	dc.b $00,$0B,$A9,$F0,$00,$00,$04,$B6,$00,$0B,$A9,$F0,$00,$00,$04,$D2
	dc.b $00,$0B,$A9,$F0,$00,$00,$05,$4A,$00,$0B,$A9,$F0,$00,$00,$05,$9A
	dc.b $00,$0B,$A9,$F0,$00,$00,$06,$98,$00,$0B,$A9,$F0,$00,$00,$07,$86
	dc.b $00,$0B,$A9,$F0,$00,$00,$0A,$52,$00,$0B,$A9,$F0,$00,$00,$0C,$5E
	dc.b $00,$0B,$A9,$F0,$00,$00,$0D,$60,$00,$0B,$A9,$F0,$00,$00,$0D,$D2
	dc.b $00,$0B,$A9,$F0,$00,$00,$0E,$46,$00,$0C,$A9,$F0,$00,$00,$0B,$40
	dc.b $00,$0C,$A9,$F0,$00,$00,$13,$38,$00,$0D,$A9,$F0,$00,$00,$00,$28
	dc.b $00,$0D,$A9,$F0,$00,$00,$11,$32,$00,$0D,$A9,$F0,$00,$00,$21,$FA
	dc.b $00,$0D,$A9,$F0,$00,$00,$22,$A8,$00,$0D,$A9,$F0,$00,$00,$23,$E6
	dc.b $00,$0D,$A9,$F0,$00,$00,$25,$28,$00,$0D,$A9,$F0,$00,$00,$2C,$CE
	dc.b $00,$0D,$A9,$F0,$00,$00,$2D,$0C,$00,$0D,$A9,$F0,$00,$00,$2D,$9C
	dc.b $00,$0D,$A9,$F0,$00,$00,$2E,$06,$00,$0D,$A9,$F0,$00,$00,$67,$A6
	dc.b $00,$0D,$A9,$F0,$00,$00,$6F,$46,$00,$0D,$A9,$F0,$00,$00,$82,$26
	dc.b $00,$0E,$A9,$F0,$00,$00,$00,$28,$00,$0E,$A9,$F0,$00,$00,$01,$00
	dc.b $00,$0E,$A9,$F0,$00,$00,$01,$8C,$00,$0E,$A9,$F0,$00,$00,$02,$06
	dc.b $00,$0E,$A9,$F0,$00,$00,$03,$28,$00,$0E,$A9,$F0,$00,$00,$03,$C6
	dc.b $00,$0E,$A9,$F0,$00,$00,$04,$6A,$00,$0E,$A9,$F0,$00,$00,$04,$98
	dc.b $00,$0E,$A9,$F0,$00,$00,$05,$0E,$00,$0E,$A9,$F0,$00,$00,$06,$44
	dc.b $00,$0E,$A9,$F0,$00,$00,$07,$1C,$00,$0F,$A9,$F0,$00,$00,$01,$C8
	dc.b $00,$0F,$A9,$F0,$00,$00,$08,$F6,$00,$0F,$A9,$F0,$00,$00,$0A,$F2
	dc.b $00,$0F,$A9,$F0,$00,$00,$0B,$10,$00,$0F,$A9,$F0,$00,$00,$0B,$72
	dc.b $00,$0F,$A9,$F0,$00,$00,$0C,$76,$00,$0F,$A9,$F0,$00,$00,$0C,$CA
	dc.b $00,$10,$A9,$F0,$00,$00,$00,$28,$00,$10,$A9,$F0,$00,$00,$01,$32
	dc.b $00,$10,$A9,$F0,$00,$00,$03,$62,$00,$11,$A9,$F0,$00,$00,$0A,$1C
	dc.b $00,$12,$A9,$F0,$00,$00,$00,$28,$00,$12,$A9,$F0,$00,$00,$00,$9A
	dc.b $00,$12,$A9,$F0,$00,$00,$06,$EC,$00,$13,$A9,$F0,$00,$00,$00,$28
	dc.b $00,$14,$A9,$F0,$00,$00,$00,$C4,$00,$14,$A9,$F0,$00,$00,$01,$36
	dc.b $00,$14,$A9,$F0,$00,$00,$01,$CE,$00,$14,$A9,$F0,$00,$00,$02,$66
	dc.b $00,$14,$A9,$F0,$00,$00,$03,$72,$00,$14,$A9,$F0,$00,$00,$05,$80
	dc.b $00,$14,$A9,$F0,$00,$00,$07,$3E,$00,$14,$A9,$F0,$00,$00,$08,$0E
	dc.b $00,$14,$A9,$F0,$00,$00,$0A,$12,$00,$14,$A9,$F0,$00,$00,$0A,$98
	dc.b $00,$14,$A9,$F0,$00,$00,$0A,$9C,$00,$14,$A9,$F0,$00,$00,$0A,$C4
	dc.b $00,$14,$A9,$F0,$00,$00,$0B,$50,$00,$14,$A9,$F0,$00,$00,$0B,$CC
	dc.b $00,$14,$A9,$F0,$00,$00,$0C,$8C,$00,$14,$A9,$F0,$00,$00,$0C,$90
	dc.b $00,$14,$A9,$F0,$00,$00,$0D,$60,$00,$14,$A9,$F0,$00,$00,$0E,$90
	dc.b $00,$14,$A9,$F0,$00,$00,$0F,$04,$00,$14,$A9,$F0,$00,$00,$0F,$DA
	dc.b $00,$14,$A9,$F0,$00,$00,$10,$F6,$00,$14,$A9,$F0,$00,$00,$11,$B0
	dc.b $00,$14,$A9,$F0,$00,$00,$12,$4E,$00,$14,$A9,$F0,$00,$00,$12,$C0
	dc.b $00,$14,$A9,$F0,$00,$00,$13,$62,$00,$14,$A9,$F0,$00,$00,$13,$F0
	dc.b $00,$14,$A9,$F0,$00,$00,$14,$78,$00,$15,$A9,$F0,$00,$00,$07,$22
	dc.b $00,$15,$A9,$F0,$00,$00,$08,$1E,$00,$15,$A9,$F0,$00,$00,$08,$FE
	dc.b $00,$15,$A9,$F0,$00,$00,$0E,$44,$00,$15,$A9,$F0,$00,$00,$0E,$DC
	dc.b $00,$15,$A9,$F0,$00,$00,$0F,$4C,$00,$15,$A9,$F0,$00,$00,$0F,$DE
	dc.b $00,$15,$A9,$F0,$00,$00,$11,$A8,$00,$15,$A9,$F0,$00,$00,$17,$28
	dc.b $00,$15,$A9,$F0,$00,$00,$17,$A2,$00,$15,$A9,$F0,$00,$00,$17,$B8
	dc.b $00,$15,$A9,$F0,$00,$00,$17,$EC,$00,$15,$A9,$F0,$00,$00,$18,$22
	dc.b $00,$15,$A9,$F0,$00,$00,$18,$5A,$00,$15,$A9,$F0,$00,$00,$18,$6C
	dc.b $00,$15,$A9,$F0,$00,$00,$19,$F0,$00,$15,$A9,$F0,$00,$00,$1A,$06
	dc.b $00,$15,$A9,$F0,$00,$00,$1A,$1A,$00,$15,$A9,$F0,$00,$00,$1A,$48
	dc.b $00,$16,$A9,$F0,$00,$00,$00,$44,$00,$17,$A9,$F0,$00,$00,$00,$28
	dc.b $00,$18,$A9,$F0,$00,$00,$00,$28,$00,$18,$A9,$F0,$00,$00,$0A,$2C
	dc.b $00,$18,$A9,$F0,$00,$00,$0A,$6C,$00,$18,$A9,$F0,$00,$00,$0B,$38
	dc.b $00,$18,$A9,$F0,$00,$00,$0B,$9A,$00,$18,$A9,$F0,$00,$00,$0C,$10
	dc.b $00,$18,$A9,$F0,$00,$00,$0C,$B6,$00,$18,$A9,$F0,$00,$00,$0E,$52
	dc.b $00,$18,$A9,$F0,$00,$00,$0F,$56,$00,$18,$A9,$F0,$00,$00,$0F,$78
	dc.b $00,$18,$A9,$F0,$00,$00,$0F,$9C,$00,$18,$A9,$F0,$00,$00,$10,$A8
	dc.b $00,$18,$A9,$F0,$00,$00,$11,$D8,$00,$19,$A9,$F0,$00,$00,$00,$B8
	dc.b $00,$19,$A9,$F0,$00,$00,$00,$7A,$00,$19,$A9,$F0,$00,$00,$00,$E4
	dc.b $00,$1A,$A9,$F0,$00,$00,$00,$28,$00,$1A,$A9,$F0,$00,$00,$01,$BA
	dc.b $00,$1A,$A9,$F0,$00,$00,$03,$0E,$00,$1A,$A9,$F0,$00,$00,$03,$38
	dc.b $00,$1A,$A9,$F0,$00,$00,$03,$70,$00,$1A,$A9,$F0,$00,$00,$05,$18
	dc.b $00,$1A,$A9,$F0,$00,$00,$05,$5A,$00,$1A,$A9,$F0,$00,$00,$05,$F2
	dc.b $00,$1A,$A9,$F0,$00,$00,$07,$DC,$00,$1A,$A9,$F0,$00,$00,$08,$10
	dc.b $00,$1A,$A9,$F0,$00,$00,$08,$36,$00,$1A,$A9,$F0,$00,$00,$08,$C4
	dc.b $00,$1A,$A9,$F0,$00,$00,$09,$12,$00,$1A,$A9,$F0,$00,$00,$09,$58
	dc.b $00,$1A,$A9,$F0,$00,$00,$09,$A6,$00,$1A,$A9,$F0,$00,$00,$0A,$00
	dc.b $00,$1A,$A9,$F0,$00,$00,$0A,$48,$00,$1A,$A9,$F0,$00,$00,$0A,$7E
	dc.b $00,$1A,$A9,$F0,$00,$00,$0A,$C4,$00,$1A,$A9,$F0,$00,$00,$0A,$CC
	dc.b $00,$1A,$A9,$F0,$00,$00,$0A,$FC,$00,$1A,$A9,$F0,$00,$00,$0B,$0E
	dc.b $00,$1A,$A9,$F0,$00,$00,$0B,$20,$00,$1A,$A9,$F0,$00,$00,$0B,$32

; CODE 1 Main source section
macos_code_CODE_1:
;   source_section_id: macos-code-CODE-1
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: selected_full_listing
;   resource_type: CODE
;   id: 1
;   name: Main
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 29024
;   payload_sha256: 4a543f6fd1c542fccd38ec9f469b06f65c797dfd8b226fefc9f576faafbe70f5
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:1
;   listing: kind=full_listing available=True reason=unknown
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 1 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_code span=40..29024 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=1 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_code payload[40..29024) size=28984 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   selected_code_entry_offset: 40
;   selected_code_bytes_size: 28984
;   code_bytes_sha256: 4633044ba0d2a816a0e482a9fb3b65bcd8daf699882df8f95939ad018f51879c
;   listing_rows: 1814
;   CODE_1_layout_context:
macos_CODE_1_far_model_header:
;     payload[0..40) status=validated parser_use=accepted_parser_output reason=far_model_segment_header; documented far-model header, not executable source rows
macos_CODE_1_candidate_entry_stub:
;     payload[40..62) selected_code_bytes[0..22) status=candidate parser_use=candidate_only reason=entry/stub bytes begin at candidate movea.l (a7)+,a0 boundary; accepted byte-entry proof remains deferred
macos_CODE_1_candidate_body_after_stub:
;     payload[62..29024) status=candidate parser_use=candidate_only reason=remaining CODE 1 bytes are owned by candidate executable body; Segment Loader relocation/fixup semantics remain deferred

; CODE 1 Main byte-real source follows.
;   byte_preserving_placeholder: CODE 1 payload[0..29024) sha256=4a543f6fd1c542fccd38ec9f469b06f65c797dfd8b226fefc9f576faafbe70f5
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_1_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$00,$10,$00,$00,$00,$72,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_code payload[40..29024) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=8 labels=1 xrefs=2
macos_code_CODE_1_loc_00000028:
	movea.l (a7)+,a0
	move.l a7,d0
	sub.l $0114.w,d0
	cmpi.l #512,d0
	sge.b d0
	neg.b d0
	move.b d0,(a7)
	jmp (a0)

; CODE 2 FPOpTable source section
macos_code_CODE_2:
;   source_section_id: macos-code-CODE-2
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 2
;   name: FPOpTable
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 7788
;   payload_sha256: a33f1dfe28237a5ee6f9ba7a96540e8e4842a7e6207575db5f0479b8c622a4f2
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:2
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 2 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..374 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=374..7788 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..374) size=334 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[374..7788) size=7414 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 2 payload[0..7788) sha256=a33f1dfe28237a5ee6f9ba7a96540e8e4842a7e6207575db5f0479b8c622a4f2
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_2_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$03,$A0,$00,$00,$00,$07,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..374) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_2_candidate_unresolved_prefix_00000028:
	dc.b $20,$1F,$2F,$40,$00,$10,$30,$2D,$F4,$2A,$D0,$40,$41,$FA,$01,$92
	dc.b $32,$30,$00,$00,$67,$26,$D0,$C1,$42,$41,$22,$57,$70,$00,$10,$10
	dc.b $B3,$08,$56,$C8,$FF,$FC,$67,$1C,$D0,$88,$08,$00,$00,$00,$67,$02
	dc.b $52,$80,$20,$40,$12,$10,$67,$04,$D0,$C1,$60,$DE,$4F,$EF,$00,$10
	dc.b $74,$00,$60,$3A,$20,$08,$08,$00,$00,$00,$67,$02,$52,$80,$52,$80
	dc.b $20,$40,$58,$4F,$12,$18,$24,$08,$22,$5F,$32,$81,$10,$18,$12,$18
	dc.b $22,$5F,$32,$81,$08,$00,$00,$06,$66,$0A,$08,$00,$00,$05,$67,$08
	dc.b $72,$01,$60,$06,$72,$02,$60,$02,$42,$41,$22,$5F,$32,$81,$20,$57
	dc.b $2E,$82,$4E,$D0,$4E,$56,$00,$00,$48,$E7,$1E,$00,$22,$6E,$00,$20
	dc.b $36,$2E,$00,$1A,$38,$2E,$00,$18,$20,$6E,$00,$10,$3A,$10,$20,$49
	dc.b $54,$48,$0C,$6E,$18,$00,$00,$1E,$67,$0C,$30,$10,$02,$40,$08,$00
	dc.b $C0,$6E,$00,$1E,$66,$38,$10,$18,$02,$40,$00,$01,$67,$08,$0C,$6D
	dc.b $00,$20,$F3,$98,$6D,$28,$42,$46,$10,$10,$67,$06,$3C,$05,$CC,$40
	dc.b $67,$1C,$4E,$AD,$05,$7A,$4A,$43,$66,$04,$4A,$81,$67,$04,$07,$01
	dc.b $67,$0C,$4A,$44,$66,$04,$4A,$82,$67,$14,$09,$02,$66,$10,$59,$4F
	dc.b $2F,$09,$4E,$AD,$05,$72,$22,$5F,$66,$A4,$42,$40,$60,$4A,$20,$09
	dc.b $41,$FA,$00,$9E,$90,$88,$20,$6E,$00,$08,$30,$80,$42,$40,$52,$49
	dc.b $20,$6E,$00,$0C,$10,$11,$30,$80,$0C,$06,$00,$07,$6E,$06,$1C,$3B
	dc.b $60,$38,$60,$1C,$0C,$06,$00,$08,$67,$16,$0C,$06,$00,$10,$67,$10
	dc.b $0C,$06,$00,$20,$67,$0A,$0C,$06,$00,$40,$67,$04,$1C,$3C,$00,$20
	dc.b $20,$6E,$00,$10,$30,$86,$70,$01,$4C,$DF,$00,$78,$4E,$5E
;     candidate_code payload[374..7788) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=4 labels=1 xrefs=2
macos_code_CODE_2_loc_00000176:
	movea.l (a7)+,a0
	lea.l $001C(a7),a7
	move.b d0,(a7)
	jmp (a0)

; CODE 3 Init source section
macos_code_CODE_3:
;   source_section_id: macos-code-CODE-3
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 3
;   name: Init
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 18252
;   payload_sha256: 331fc8e7daf79d4e733760cb8ad413ade51431a01dd6c19c4f73720f562b08e4
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:3
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 3 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..302 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=302..18252 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..302) size=262 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[302..18252) size=17950 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 3 payload[0..18252) sha256=331fc8e7daf79d4e733760cb8ad413ade51431a01dd6c19c4f73720f562b08e4
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_3_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$03,$D8,$00,$00,$00,$03,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..302) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_3_candidate_unresolved_prefix_00000028:
	dc.b $91,$C8,$4E,$AD,$06,$1A,$30,$3C,$00,$04,$4E,$AD,$06,$22,$22,$5F
	dc.b $30,$FC,$01,$00,$30,$9F,$4E,$D1,$4E,$56,$FF,$F8,$48,$6D,$D2,$72
	dc.b $4E,$AD,$09,$FA,$4E,$5E,$4E,$75,$8B,$43,$4C,$45,$41,$52,$53,$43
	dc.b $52,$45,$45,$4E,$00,$00,$4E,$56,$FF,$FE,$3B,$7C,$00,$10,$C9,$86
	dc.b $70,$09,$72,$10,$E1,$A9,$3B,$41,$C9,$84,$30,$2D,$C9,$84,$53,$40
	dc.b $3B,$40,$C9,$82,$70,$00,$2B,$40,$C9,$7A,$70,$00,$2B,$40,$C9,$7E
	dc.b $70,$00,$2B,$40,$C9,$76,$70,$00,$2B,$40,$C9,$72,$42,$6D,$CB,$1C
	dc.b $70,$00,$2B,$40,$CB,$1E,$42,$2D,$C9,$71,$2B,$7C,$3F,$3F,$3F,$3F
	dc.b $CA,$CE,$42,$6D,$CA,$CA,$42,$2D,$CA,$CD,$70,$00,$2B,$40,$CA,$88
	dc.b $42,$2D,$C9,$88,$42,$2D,$CB,$1B,$70,$00,$2B,$40,$CB,$16,$4E,$5E
	dc.b $4E,$75,$86,$49,$4E,$49,$54,$49,$4F,$00,$00,$00,$4E,$56,$00,$00
	dc.b $2F,$07,$3E,$2E,$00,$08,$4A,$AD,$C9,$7A,$56,$C0,$4A,$00,$66,$14
	dc.b $72,$06,$B2,$47,$5E,$C1,$80,$01,$66,$0A,$72,$3E,$B2,$47,$5D,$C1
	dc.b $80,$01,$67,$06,$42,$2E,$00,$0A,$60,$28,$1D,$7C,$00,$01,$00,$0A
	dc.b $10,$07,$02,$40,$00,$01,$67,$02,$53,$47,$3B,$47,$C9,$86,$70,$00
	dc.b $30,$2D,$C9,$86,$72,$09,$E3,$A8,$3B,$40,$C9,$84,$53,$40,$3B,$40
	dc.b $C9,$82,$2E,$1F,$4E,$5E
;     candidate_code payload[302..18252) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_3_loc_0000012e:
	movea.l (a7)+,a0
	addq.w #2,a7
	jmp (a0)

; CODE 4 IOMgr source section
macos_code_CODE_4:
;   source_section_id: macos-code-CODE-4
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 4
;   name: IOMgr
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 6426
;   payload_sha256: a697293e579b91031cb9bb37cd80a4f47d2acb9eff60a4f4b7e3cb9a18fd4fca
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:4
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 4 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..468 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=468..6426 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..468) size=428 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[468..6426) size=5958 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 4 payload[0..6426) sha256=a697293e579b91031cb9bb37cd80a4f47d2acb9eff60a4f4b7e3cb9a18fd4fca
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_4_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$03,$F0,$00,$00,$00,$14,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..468) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_4_candidate_unresolved_prefix_00000028:
	dc.b $22,$5F,$20,$1F,$22,$1F,$48,$E7,$04,$78,$24,$40,$28,$41,$30,$2C
	dc.b $01,$0A,$32,$2C,$02,$2E,$4A,$2C,$02,$38,$67,$16,$42,$2C,$02,$38
	dc.b $B0,$41,$6F,$0E,$2F,$0C,$4E,$BA,$11,$BE,$30,$2C,$01,$0A,$32,$2C
	dc.b $02,$2E,$4A,$2C,$02,$38,$67,$2A,$4A,$2C,$02,$24,$67,$18,$30,$2D
	dc.b $CB,$1C,$53,$40,$6F,$10,$55,$4F,$4E,$BA,$0F,$D2,$10,$1F,$67,$06
	dc.b $28,$6D,$CB,$1E,$60,$B8,$52,$6C,$01,$0A,$72,$00,$14,$81,$60,$00
	dc.b $00,$A4,$92,$40,$20,$6C,$01,$06,$D0,$C0,$47,$EA,$00,$01,$74,$0D
	dc.b $0C,$41,$00,$FF,$6C,$2E,$3A,$3C,$00,$FE,$10,$18,$B4,$00,$57,$CD
	dc.b $00,$0C,$2A,$0B,$9A,$8A,$53,$45,$14,$85,$60,$3A,$16,$C0,$51,$C9
	dc.b $FF,$EA,$2F,$0C,$4E,$BA,$11,$50,$20,$6C,$01,$06,$32,$2C,$02,$2E
	dc.b $74,$0D,$60,$D6,$43,$E8,$00,$FF,$10,$11,$12,$82,$60,$02,$16,$C5
	dc.b $1A,$18,$B4,$05,$66,$F8,$2A,$0B,$9A,$8A,$53,$45,$14,$85,$92,$45
	dc.b $12,$C0,$B3,$C8,$66,$1C,$B0,$02,$67,$18,$51,$C9,$00,$12,$2F,$0C
	dc.b $4E,$BA,$11,$14,$20,$6C,$01,$06,$32,$2C,$02,$2E,$74,$0D,$10,$18
	dc.b $60,$E4,$30,$2C,$02,$2E,$90,$41,$52,$40,$39,$40,$01,$0A,$22,$2C
	dc.b $02,$34,$29,$41,$02,$30,$D2,$85,$52,$81,$29,$41,$02,$34,$72,$01
	dc.b $19,$41,$02,$38,$4C,$DF,$1E,$20,$1E,$81,$4E,$D1,$22,$5F,$20,$1F
	dc.b $22,$1F,$48,$E7,$04,$78,$24,$40,$28,$41,$4A,$6C,$02,$16,$67,$16
	dc.b $2F,$01,$2F,$00,$42,$67,$4E,$BA,$14,$92,$2F,$0C,$3F,$3C,$00,$0D
	dc.b $4E,$BA,$12,$DC,$60,$70,$10,$2C,$01,$00,$67,$16,$47,$ED,$D2,$72
	dc.b $2F,$0B,$2F,$0A,$42,$67,$4E,$AD,$0A,$0A,$2F,$0B,$4E,$AD,$09,$F2
	dc.b $60,$54,$26,$6C,$01,$06,$30,$2C,$01,$0A,$D6,$C0,$32,$00,$7A,$00
	dc.b $1A,$1A,$D0,$45,$52,$40,$34,$2C,$02,$2C,$B0,$42,$6F,$28,$94,$41
	dc.b $6F,$12,$9A,$42,$60,$02,$16,$DA,$51,$CA,$FF,$FC,$97,$EC,$01,$06
	dc.b $39,$4B,$01,$0A,$2F,$0C,$4E,$BA,$13,$06,$26,$6C,$01,$06,$D6,$EC
	dc.b $01,$0A,$60,$02,$16,$DA,$51,$CD,$FF,$FC,$16,$FC,$00,$0D,$97,$EC
	dc.b $01,$06,$39,$4B,$01,$0A,$4C,$DF,$1E,$20,$4E,$D1
;     candidate_code payload[468..6426) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=10 labels=2 xrefs=3
macos_code_CODE_4_loc_000001d4:
	movea.l (a7)+,a0
	move.w (a7)+,d0
	move.l a0,-(a7)
	pea.l $0004(a7)
	btst #0,d0
	beq.b loc_0_00000012
	addq.w #1,d0
macos_code_CODE_4_loc_000001e6:
	move.w d0,-(a7)
	jsr $0A4A(a5)
	rts

; CODE 5 Macros source section
macos_code_CODE_5:
;   source_section_id: macos-code-CODE-5
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 5
;   name: Macros
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 26638
;   payload_sha256: 90b898d2148ba2c3b798bed0c8c5dc936fba9ed3e8b958d279db4b279a033dfc
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:5
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 5 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..212 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=212..26638 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..212) size=172 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[212..26638) size=26426 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 5 payload[0..26638) sha256=90b898d2148ba2c3b798bed0c8c5dc936fba9ed3e8b958d279db4b279a033dfc
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_5_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$04,$90,$00,$00,$00,$17,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..212) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_5_candidate_unresolved_prefix_00000028:
	dc.b $24,$1F,$22,$5F,$20,$6D,$EC,$E6,$4A,$28,$00,$2A,$67,$06,$42,$17
	dc.b $20,$42,$4E,$D0,$70,$01,$1E,$80,$2F,$0B,$26,$68,$00,$20,$21,$4B
	dc.b $00,$26,$30,$28,$00,$1E,$31,$40,$00,$24,$3B,$40,$ED,$5E,$52,$40
	dc.b $31,$40,$00,$1E,$42,$40,$10,$1B,$66,$04,$42,$11,$60,$46,$12,$1B
	dc.b $0C,$01,$00,$03,$6F,$0A,$12,$C0,$12,$C1,$55,$40,$6C,$30,$60,$34
	dc.b $41,$ED,$EC,$D0,$6D,$12,$10,$DB,$10,$DB,$10,$DB,$10,$DB,$10,$DB
	dc.b $10,$9B,$5D,$40,$41,$ED,$EC,$CA,$10,$DB,$10,$DB,$10,$DB,$10,$DB
	dc.b $10,$DB,$10,$9B,$5F,$40,$20,$6D,$EC,$E6,$12,$C0,$60,$02,$12,$DB
	dc.b $51,$C8,$FF,$FC,$10,$1B,$66,$0E,$43,$E8,$00,$20,$12,$DB,$12,$DB
	dc.b $12,$DB,$12,$93,$60,$0E,$53,$00,$66,$06,$70,$01,$11,$40,$00,$2A
	dc.b $21,$4B,$00,$20,$26,$5F,$20,$42,$4E,$D0,$24,$1F
;     candidate_code payload[212..26638) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=11 labels=1 xrefs=2
macos_code_CODE_5_loc_000000d4:
	movea.l (a7)+,a0
	movea.l a7,a1
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)
	movea.l a1,a7
	movea.l d2,a0
	jmp (a0)

; CODE 6 OpTable source section
macos_code_CODE_6:
;   source_section_id: macos-code-CODE-6
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 6
;   name: OpTable
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 15158
;   payload_sha256: 75005bca2e9e007ce374020416127735d9096e064806e4e1e1b888cd3ba8a9cf
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:6
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 6 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..58 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=58..15158 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..58) size=18 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[58..15158) size=15100 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 6 payload[0..15158) sha256=75005bca2e9e007ce374020416127735d9096e064806e4e1e1b888cd3ba8a9cf
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_6_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$05,$48,$00,$00,$00,$09,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..58) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_6_candidate_unresolved_prefix_00000028:
	dc.b $20,$1F,$2F,$40,$00,$18,$55,$4F,$2F,$2F,$00,$06,$4E,$AD,$00,$D2
	dc.b $30,$1F
;     candidate_code payload[58..15158) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=76 labels=15 xrefs=21
macos_code_CODE_6_loc_0000003a:
	movea.l (a7)+,a0
	move.w d0,(a0)
	add.w d0,d0
	lea.l loc_0_000022A0(pc),a0
	move.w $0(a0,d0.w),d1
	beq.b loc_0_00000036
	adda.w d1,a0
	clr.w d1
macos_code_CODE_6_loc_0000004e:
	movea.l (a7),a1
	moveq.l #0,d0
	move.b (a0),d0
macos_code_CODE_6_loc_00000054:
	cmpm.b (a0)+,(a1)+
	dbne.w d0,loc_0_0000001A
	beq.b loc_0_0000003E
	add.l a0,d0
	btst #0,d0
	beq.b loc_0_0000002C
	addq.l #1,d0
macos_code_CODE_6_loc_00000066:
	movea.l d0,a0
	move.b (a0),d1
	beq.b loc_0_00000036
	adda.w d1,a0
	bra.b loc_0_00000014
macos_code_CODE_6_loc_00000070:
	lea.l $0014(a7),a7
	moveq.l #0,d2
	bra.b loc_0_000000B0
macos_code_CODE_6_loc_00000078:
	move.l a0,d0
	btst #0,d0
	beq.b loc_0_00000048
	addq.l #1,d0
macos_code_CODE_6_loc_00000082:
	addq.l #1,d0
	movea.l d0,a0
	addq.w #4,a7
	move.b (a0)+,d1
	move.l a0,d2
	movea.l (a7)+,a1
	move.w d1,(a1)
	move.b (a0)+,d0
	move.b (a0)+,d1
	movea.l (a7)+,a1
	move.w d1,(a1)
	btst #6,d0
	bne.b loc_0_00000082
	btst #5,d0
	bne.b loc_0_00000082
	move.b (a0),d1
	andi.b #35,d1
	cmp.w -$0C68(a5),d1
	ble.b loc_0_00000082
	move.b #$1,-$0BD0(a5)
	addq.w #8,a7
	moveq.l #0,d2
	bra.b loc_0_000000B0
macos_code_CODE_6_loc_000000bc:
	movea.l (a7)+,a1
	tst.b -$0C5D(a5)
	bne.b loc_0_00000094
	move.b (a0),d1
	bpl.b loc_0_00000094
	moveq.l #1,d1
	move.b d1,(a1)
	bra.b loc_0_00000096
macos_code_CODE_6_loc_000000ce:
	clr.b (a1)
macos_code_CODE_6_loc_000000d0:
	btst #6,d0
	bne.b loc_0_000000A6
	btst #5,d0
	beq.b loc_0_000000AA
	moveq.l #1,d1
	bra.b loc_0_000000AC
macos_code_CODE_6_loc_000000e0:
	moveq.l #2,d1
	bra.b loc_0_000000AC
macos_code_CODE_6_loc_000000e4:
	clr.w d1
macos_code_CODE_6_loc_000000e6:
	movea.l (a7)+,a1
	move.w d1,(a1)
macos_code_CODE_6_loc_000000ea:
	movea.l (a7),a0
	move.l d2,(a7)
	jmp (a0)
macos_code_CODE_6_loc_000022da:

; CODE 7 POpTable source section
macos_code_CODE_7:
;   source_section_id: macos-code-CODE-7
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 7
;   name: POpTable
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 4142
;   payload_sha256: 3bc5de90c439ad5e0f7e5d4635b445022db8ab231a9b43981dbd95673ac0b78e
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:7
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 7 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..352 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=352..4142 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..352) size=312 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[352..4142) size=3790 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 7 payload[0..4142) sha256=3bc5de90c439ad5e0f7e5d4635b445022db8ab231a9b43981dbd95673ac0b78e
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_7_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$05,$90,$00,$00,$00,$06,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..352) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_7_candidate_unresolved_prefix_00000028:
	dc.b $20,$1F,$2F,$40,$00,$10,$30,$2D,$F4,$2A,$D0,$40,$41,$FA,$01,$7C
	dc.b $32,$30,$00,$00,$67,$26,$D0,$C1,$42,$41,$22,$57,$70,$00,$10,$10
	dc.b $B3,$08,$56,$C8,$FF,$FC,$67,$1C,$D0,$88,$08,$00,$00,$00,$67,$02
	dc.b $52,$80,$20,$40,$12,$10,$67,$04,$D0,$C1,$60,$DE,$4F,$EF,$00,$10
	dc.b $74,$00,$60,$3A,$20,$08,$08,$00,$00,$00,$67,$02,$52,$80,$52,$80
	dc.b $20,$40,$58,$4F,$12,$18,$24,$08,$22,$5F,$32,$81,$10,$18,$12,$18
	dc.b $22,$5F,$32,$81,$08,$00,$00,$06,$66,$0A,$08,$00,$00,$05,$67,$08
	dc.b $72,$01,$60,$06,$72,$02,$60,$02,$42,$41,$22,$5F,$32,$81,$20,$57
	dc.b $2E,$82,$4E,$D0,$4E,$56,$00,$00,$48,$E7,$1E,$00,$22,$6E,$00,$22
	dc.b $36,$2E,$00,$1C,$38,$2E,$00,$1A,$20,$6E,$00,$12,$3A,$10,$20,$49
	dc.b $54,$48,$0C,$6E,$18,$00,$00,$20,$67,$0C,$30,$10,$02,$40,$08,$00
	dc.b $C0,$6E,$00,$20,$66,$34,$10,$18,$12,$2E,$00,$08,$67,$04,$C0,$01
	dc.b $67,$28,$42,$46,$10,$10,$67,$06,$3C,$05,$CC,$40,$67,$1C,$4E,$AD
	dc.b $05,$7A,$4A,$43,$66,$04,$4A,$81,$67,$04,$07,$01,$67,$0C,$4A,$44
	dc.b $66,$04,$4A,$82,$67,$14,$09,$02,$66,$10,$59,$4F,$2F,$09,$4E,$AD
	dc.b $05,$72,$22,$5F,$66,$A8,$42,$40,$60,$38,$20,$09,$41,$FA,$00,$8C
	dc.b $90,$88,$20,$6E,$00,$0A,$30,$80,$42,$40,$52,$49,$20,$6E,$00,$0E
	dc.b $10,$11,$30,$80,$0C,$06,$00,$07,$6E,$06,$1C,$3B,$60,$26,$60,$0A
	dc.b $0C,$06,$00,$10,$67,$04,$1C,$3C,$00,$02,$20,$6E,$00,$12,$30,$86
	dc.b $70,$01,$4C,$DF,$00,$78,$4E,$5E
;     candidate_code payload[352..4142) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=4 labels=1 xrefs=2
macos_code_CODE_7_loc_00000160:
	movea.l (a7)+,a0
	lea.l $001E(a7),a7
	move.b d0,(a7)
	jmp (a0)

; CODE 8 Listing source section
macos_code_CODE_8:
;   source_section_id: macos-code-CODE-8
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 8
;   name: Listing
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 1852
;   payload_sha256: 5b3cd8756213ba73870bb353160d4e5dbb1a3bdd2da93157146d091b6949a2e9
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:8
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 8 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..42 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=42..1852 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..42) size=2 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[42..1852) size=1810 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 8 payload[0..1852) sha256=5b3cd8756213ba73870bb353160d4e5dbb1a3bdd2da93157146d091b6949a2e9
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_8_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$05,$C0,$00,$00,$00,$07,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..42) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_8_candidate_unresolved_prefix_00000028:
	dc.b $22,$5F
;     candidate_code payload[42..1852) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=66 labels=17 xrefs=27
macos_code_CODE_8_loc_0000002a:
	movea.l (a7)+,a0
	movem.l a1-a3,-(a7)
	movea.l a0,a2
	clr.w d2
	move.b (a0)+,d2
	movea.l a0,a1
	bra.w loc_0_000000A0
macos_code_CODE_8_loc_0000003c:
	move.b (a0)+,d0
macos_code_CODE_8_loc_0000003e:
	cmpi.b #39,d0
	bne.b loc_0_0000002E
macos_code_CODE_8_loc_00000044:
	move.b d0,(a1)+
	dbf.w d2,loc_0_00000024
	bra.w loc_0_000000A4
macos_code_CODE_8_loc_0000004e:
	move.b (a0)+,d0
	cmpi.b #39,d0
	bne.b loc_0_0000001A
	bra.b loc_0_0000009E
macos_code_CODE_8_loc_00000058:
	cmpi.b #192,d0
	bne.b loc_0_0000009E
	movea.l a1,a3
macos_code_CODE_8_loc_00000060:
	clr.w d1
macos_code_CODE_8_loc_00000062:
	move.b d0,(a1)+
	dbf.w d2,loc_0_00000040
	bra.b loc_0_00000082
macos_code_CODE_8_loc_0000006a:
	move.b (a0)+,d0
	cmpi.b #64,d0
	blt.b loc_0_0000004E
	cmpi.b #90,d0
	ble.b loc_0_00000036
macos_code_CODE_8_loc_00000078:
	cmpi.b #97,d0
	blt.b loc_0_0000005A
	cmpi.b #122,d0
	ble.b loc_0_00000036
macos_code_CODE_8_loc_00000084:
	cmpi.b #48,d0
	blt.b loc_0_0000006A
	cmpi.b #57,d0
	bgt.b loc_0_0000006A
	addq.w #1,d1
	bra.b loc_0_00000038
macos_code_CODE_8_loc_00000094:
	cmpi.b #95,d0
	beq.b loc_0_00000036
	cmpi.b #36,d0
	beq.b loc_0_00000036
	cmpi.b #35,d0
	beq.b loc_0_00000036
	cmpi.b #37,d0
	beq.b loc_0_00000036
macos_code_CODE_8_loc_000000ac:
	subq.w #4,d1
	blt.b loc_0_00000096
	move.l a1,d1
	sub.l a3,d1
	cmpi.w #5,d1
	blt.b loc_0_00000096
	subq.w #4,a1
	move.b #$40,(a3)
macos_code_CODE_8_loc_000000c0:
	tst.w d2
	bge.w loc_0_00000014
	bra.b loc_0_000000A4
macos_code_CODE_8_loc_000000c8:
	move.b d0,(a1)+
macos_code_CODE_8_loc_000000ca:
	dbf.w d2,loc_0_00000012
macos_code_CODE_8_loc_000000ce:
	move.l a1,d2
	sub.l a2,d2
	subq.b #1,d2
	move.b d2,(a2)
	movem.l (a7)+,a1-a3
	jmp (a1)

; CODE 9 Pass2 source section
macos_code_CODE_9:
;   source_section_id: macos-code-CODE-9
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 9
;   name: Pass2
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 13946
;   payload_sha256: 0361ae9dcb47f31cf559372a3e42c672dcfb8920b332d4f900a7124ab6c70bf3
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:9
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 9 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..712 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=712..13946 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..712) size=672 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[712..13946) size=13234 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 9 payload[0..13946) sha256=0361ae9dcb47f31cf559372a3e42c672dcfb8920b332d4f900a7124ab6c70bf3
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_9_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$05,$F8,$00,$00,$00,$09,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..712) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_9_candidate_unresolved_prefix_00000028:
	dc.b $2B,$48,$F0,$BE,$22,$6D,$F0,$CE,$20,$2D,$F0,$CA,$67,$14,$20,$40
	dc.b $10,$10,$32,$3C,$07,$18,$01,$01,$67,$08,$20,$09,$90,$88,$31,$40
	dc.b $00,$02,$20,$09,$08,$00,$00,$00,$67,$02,$42,$19,$20,$09,$90,$AD
	dc.b $F0,$C6,$6C,$0A,$2B,$49,$F0,$CE,$2B,$49,$F0,$CA,$4E,$75,$4A,$2D
	dc.b $F0,$B1,$66,$2C,$2F,$00,$2F,$3C,$00,$00,$20,$00,$4E,$BA,$31,$48
	dc.b $20,$1F,$22,$6D,$F0,$D2,$20,$49,$D0,$C0,$2B,$48,$F0,$CE,$2B,$48
	dc.b $F0,$CA,$20,$6D,$F0,$C6,$E4,$48,$22,$D8,$51,$C8,$FF,$FC,$4E,$75
	dc.b $20,$6D,$F0,$D2,$2B,$48,$F0,$CE,$2B,$48,$F0,$CA,$20,$09,$90,$88
	dc.b $6F,$06,$2F,$00,$4E,$BA,$31,$10,$4E,$AD,$06,$72,$20,$6D,$F0,$AA
	dc.b $2B,$48,$F0,$A6,$42,$AD,$F0,$A2,$20,$09,$90,$88,$6F,$06,$2F,$00
	dc.b $4E,$AD,$06,$D2,$4E,$75,$20,$6D,$F0,$CE,$22,$48,$D2,$C0,$B3,$ED
	dc.b $F0,$C2,$6D,$0C,$3F,$00,$20,$6D,$F0,$BE,$4E,$90,$30,$1F,$60,$E6
	dc.b $2B,$49,$F0,$CE,$4E,$75,$91,$C8,$4E,$BA,$FF,$36,$22,$1F,$22,$57
	dc.b $2E,$81,$2F,$09,$42,$40,$10,$11,$58,$40,$4E,$BA,$FF,$CA,$20,$FC
	dc.b $03,$00,$00,$00,$22,$5F,$42,$40,$10,$19,$60,$02,$10,$D9,$51,$C8
	dc.b $FF,$FC,$4E,$75,$91,$C8,$4E,$BA,$FF,$08,$30,$3C,$00,$06,$4E,$BA
	dc.b $FF,$A6,$22,$5F,$34,$1F,$32,$1F,$30,$1F,$00,$40,$05,$00,$30,$C0
	dc.b $30,$C1,$30,$82,$4E,$D1,$91,$C8,$4E,$BA,$FE,$E6,$30,$3C,$00,$08
	dc.b $4E,$BA,$FF,$84,$22,$5F,$24,$1F,$32,$1F,$30,$1F,$00,$40,$06,$00
	dc.b $30,$C0,$30,$C1,$20,$82,$4E,$D1,$91,$C8,$4E,$BA,$FE,$C4,$30,$3C
	dc.b $00,$06,$4E,$BA,$FF,$62,$22,$5F,$22,$1F,$30,$1F,$00,$40,$07,$00
	dc.b $30,$C0,$20,$81,$4E,$D1,$2B,$4F,$F0,$BA,$20,$2F,$00,$04,$22,$2D
	dc.b $F0,$CA,$67,$0E,$20,$41,$34,$2F,$00,$08,$00,$42,$08,$08,$B4,$50
	dc.b $67,$08,$2B,$40,$F0,$B2,$61,$26,$60,$06,$B0,$AD,$F0,$B2,$66,$F2
	dc.b $30,$3C,$00,$04,$4E,$BA,$FF,$20,$58,$AD,$F0,$B2,$43,$EF,$00,$0A
	dc.b $10,$D9,$10,$D9,$10,$D9,$10,$99,$20,$57,$2E,$49,$4E,$D0,$41,$FA
	dc.b $FF,$FE,$4E,$BA,$FE,$5C,$30,$3C,$00,$08,$4E,$BA,$FE,$FA,$22,$6D
	dc.b $F0,$BA,$30,$29,$00,$08,$00,$40,$08,$08,$48,$40,$20,$C0,$20,$AD
	dc.b $F0,$B2,$4E,$75,$2B,$4F,$F0,$BA,$20,$2F,$00,$04,$22,$2D,$F0,$CA
	dc.b $67,$0E,$20,$41,$34,$2F,$00,$08,$00,$42,$08,$08,$B4,$50,$67,$08
	dc.b $2B,$40,$F0,$B2,$61,$B8,$60,$06,$B0,$AD,$F0,$B2,$66,$F2,$30,$3C
	dc.b $00,$02,$4E,$BA,$FE,$B2,$54,$AD,$F0,$B2,$43,$EF,$00,$0A,$10,$D9
	dc.b $10,$99,$20,$57,$2E,$49,$4E,$D0,$2B,$4F,$F0,$BA,$20,$2F,$00,$04
	dc.b $22,$2D,$F0,$CA,$67,$0E,$20,$41,$34,$2F,$00,$08,$00,$42,$08,$08
	dc.b $B4,$50,$67,$0A,$2B,$40,$F0,$B2,$61,$00,$FF,$74,$60,$06,$B0,$AD
	dc.b $F0,$B2,$66,$F0,$30,$3C,$00,$01,$4E,$BA,$FE,$6C,$52,$AD,$F0,$B2
	dc.b $22,$5F,$5C,$4F,$10,$9F,$4E,$D1,$2B,$4F,$F0,$BA,$20,$2F,$00,$04
	dc.b $0C,$6F,$00,$01,$00,$0A,$66,$14,$22,$2D,$F0,$CA,$67,$0E,$20,$41
	dc.b $34,$2F,$00,$08,$00,$42,$08,$08,$B4,$50,$67,$08,$2B,$40,$F0,$B2
	dc.b $61,$66,$60,$06,$B0,$AD,$F0,$B2,$66,$F2,$30,$2F,$00,$0C,$6E,$02
	dc.b $44,$40,$4E,$BA,$FE,$22,$30,$2F,$00,$0C,$6E,$1C,$44,$40,$48,$C0
	dc.b $D1,$AD,$F0,$B2,$22,$6F,$00,$0E,$60,$02,$10,$D9,$51,$C8,$FF,$FC
;     candidate_code payload[712..13946) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_9_loc_000002c8:
	movea.l (a7)+,a0
	lea.l $000E(a7),a7
	jmp (a0)

; CODE 10 FinishUp source section
macos_code_CODE_10:
;   source_section_id: macos-code-CODE-10
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 10
;   name: FinishUp
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 1542
;   payload_sha256: 2d5d27affd131aaa28eb0bd33157051e8f30ee3cdc054df4aad3011bdb22c1e1
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:10
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 10 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..148 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=148..1542 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..148) size=108 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[148..1542) size=1394 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 10 payload[0..1542) sha256=2d5d27affd131aaa28eb0bd33157051e8f30ee3cdc054df4aad3011bdb22c1e1
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_10_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$06,$40,$00,$00,$00,$02,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..148) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_10_candidate_unresolved_prefix_00000028:
	dc.b $91,$C8,$4E,$AD,$06,$1A,$4A,$2D,$F0,$B1,$67,$16,$20,$2D,$F0,$CE
	dc.b $90,$AD,$F0,$D2,$6F,$06,$2F,$00,$4E,$AD,$06,$52,$4E,$AD,$06,$7A
	dc.b $4E,$75,$30,$3C,$00,$02,$4E,$AD,$06,$22,$30,$FC,$02,$00,$20,$08
	dc.b $90,$AD,$F0,$D2,$6F,$06,$2F,$00,$4E,$AD,$06,$52,$4E,$75,$4E,$56
	dc.b $00,$00,$10,$2E,$00,$0C,$67,$08,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2
	dc.b $48,$6D,$D2,$6E,$20,$6E,$00,$08,$48,$68,$FF,$AC,$42,$67,$4E,$AD
	dc.b $0A,$0A,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2,$4E,$5E
;     candidate_code payload[148..1542) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_10_loc_00000094:
	movea.l (a7)+,a0
	addq.w #6,a7
	jmp (a0)

; CODE 11 Dbg source section
macos_code_CODE_11:
;   source_section_id: macos-code-CODE-11
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 11
;   name: Dbg
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 3678
;   payload_sha256: 04097ca27d77f09604177ac5e85019ecaed552d68ae2e9d50ae3b5a4e394c503
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:11
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 11 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..836 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=836..3678 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..836) size=796 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[836..3678) size=2842 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 11 payload[0..3678) sha256=04097ca27d77f09604177ac5e85019ecaed552d68ae2e9d50ae3b5a4e394c503
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_11_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$06,$50,$00,$00,$00,$0F,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..836) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_11_candidate_unresolved_prefix_00000028:
	dc.b $2B,$48,$F0,$96,$4E,$BA,$00,$62,$B3,$ED,$F0,$9E,$6D,$50,$2F,$09
	dc.b $20,$2D,$F0,$CA,$67,$14,$20,$40,$10,$10,$32,$3C,$07,$18,$01,$01
	dc.b $67,$08,$20,$09,$90,$88,$31,$40,$00,$02,$20,$09,$08,$00,$00,$00
	dc.b $67,$02,$42,$19,$20,$6D,$F0,$D2,$2B,$48,$F0,$CE,$42,$AD,$F0,$CA
	dc.b $20,$09,$90,$88,$6F,$06,$2F,$00,$4E,$AD,$06,$52,$20,$1F,$90,$AD
	dc.b $F0,$AA,$6F,$0A,$2F,$00,$4E,$BA,$0C,$E0,$22,$6D,$F0,$AA,$2B,$49
	dc.b $F0,$A6,$2B,$49,$F0,$A2,$4E,$75,$22,$6D,$F0,$A6,$20,$2D,$F0,$A2
	dc.b $67,$16,$20,$40,$10,$10,$22,$3C,$00,$1E,$B0,$00,$01,$01,$67,$08
	dc.b $20,$09,$90,$88,$31,$40,$00,$02,$20,$09,$08,$00,$00,$00,$67,$02
	dc.b $42,$19,$4E,$75,$20,$6D,$F0,$A6,$22,$48,$D2,$C0,$B3,$ED,$F0,$9A
	dc.b $6D,$0C,$3F,$00,$20,$6D,$F0,$96,$4E,$90,$30,$1F,$60,$E6,$2B,$49
	dc.b $F0,$A6,$4E,$75,$91,$C8,$4E,$BA,$FF,$48,$30,$3C,$00,$02,$4E,$BA
	dc.b $FF,$D4,$30,$FC,$02,$00,$20,$09,$90,$AD,$F0,$AA,$6F,$06,$2F,$00
	dc.b $4E,$BA,$0C,$66,$4E,$75,$4E,$56,$00,$00,$48,$E7,$01,$08,$4A,$AD
	dc.b $F0,$A2,$67,$20,$20,$6D,$F0,$A2,$1E,$10,$70,$01,$EF,$A8,$C0,$BC
	dc.b $00,$0E,$B0,$00,$67,$0E,$28,$48,$54,$4C,$30,$2D,$F0,$A8,$90,$6D
	dc.b $F0,$A4,$38,$80,$70,$01,$C0,$AD,$F0,$A6,$72,$01,$B2,$80,$66,$0E
	dc.b $20,$6D,$F0,$A6,$42,$10,$20,$2D,$F0,$A6,$52,$AD,$F0,$A6,$2D,$6D
	dc.b $F0,$A6,$00,$08,$4C,$EE,$10,$80,$FF,$F8,$4E,$5E,$4E,$75,$91,$43
	dc.b $4F,$4D,$50,$4C,$45,$54,$45,$44,$42,$47,$48,$45,$41,$44,$45,$52
	dc.b $00,$00,$4E,$56,$00,$00,$48,$E7,$01,$18,$2B,$6E,$00,$08,$F0,$BE
	dc.b $4A,$AD,$F0,$CA,$67,$20,$20,$6D,$F0,$CA,$1E,$10,$70,$01,$EF,$A8
	dc.b $C0,$BC,$00,$00,$07,$18,$67,$0E,$26,$48,$54,$4B,$30,$2D,$F0,$D0
	dc.b $90,$6D,$F0,$CC,$36,$80,$70,$01,$C0,$AD,$F0,$CE,$72,$01,$B2,$80
	dc.b $66,$0E,$20,$6D,$F0,$CE,$42,$10,$20,$2D,$F0,$CE,$52,$AD,$F0,$CE
	dc.b $2E,$2D,$F0,$CE,$9E,$AD,$F0,$C6,$4A,$87,$6C,$08,$2B,$6D,$F0,$CE
	dc.b $F0,$CA,$60,$76,$4A,$2D,$F0,$B1,$67,$2C,$48,$78,$20,$00,$4E,$AD
	dc.b $06,$52,$20,$07,$D0,$AD,$F0,$D2,$2B,$40,$F0,$CE,$2B,$40,$F0,$CA
	dc.b $26,$6D,$F0,$D2,$2F,$07,$2F,$2D,$F0,$C6,$2F,$0B,$4E,$AD,$09,$AA
	dc.b $4F,$EF,$00,$0C,$60,$44,$28,$6D,$F0,$CE,$2E,$0C,$9E,$AD,$F0,$D2
	dc.b $2B,$6D,$F0,$D2,$F0,$CE,$2B,$6D,$F0,$D2,$F0,$CA,$4A,$87,$6F,$06
	dc.b $2F,$07,$4E,$AD,$06,$52,$59,$8F,$4E,$BA,$FE,$DC,$28,$5F,$2B,$6D
	dc.b $F0,$AA,$F0,$A6,$70,$00,$2B,$40,$F0,$A2,$2E,$0C,$9E,$AD,$F0,$A6
	dc.b $4A,$87,$6F,$06,$2F,$07,$4E,$BA,$0B,$20,$4C,$EE,$18,$80,$FF,$F4
	dc.b $4E,$5E,$2E,$9F,$4E,$75,$89,$4E,$45,$57,$48,$45,$41,$44,$45,$52
	dc.b $00,$00,$4E,$56,$00,$00,$48,$E7,$01,$18,$59,$8F,$4E,$BA,$FE,$98
	dc.b $28,$5F,$B9,$ED,$F0,$9E,$65,$76,$4A,$AD,$F0,$CA,$67,$20,$20,$6D
	dc.b $F0,$CA,$1E,$10,$70,$01,$EF,$A8,$C0,$BC,$00,$00,$07,$18,$67,$0E
	dc.b $26,$48,$54,$4B,$30,$2D,$F0,$D0,$90,$6D,$F0,$CC,$36,$80,$70,$01
	dc.b $C0,$AD,$F0,$CE,$72,$01,$B2,$80,$66,$0E,$20,$6D,$F0,$CE,$42,$10
	dc.b $20,$2D,$F0,$CE,$52,$AD,$F0,$CE,$28,$6D,$F0,$CE,$2E,$0C,$9E,$AD
	dc.b $F0,$D2,$2B,$6D,$F0,$D2,$F0,$CE,$70,$00,$2B,$40,$F0,$CA,$4A,$87
	dc.b $6F,$06,$2F,$07,$4E,$AD,$06,$52,$2E,$2D,$F0,$A6,$9E,$AD,$F0,$AA
	dc.b $4A,$87,$6F,$0A,$2F,$07,$4E,$BA,$0A,$80,$28,$6D,$F0,$AA,$2B,$4C
	dc.b $F0,$A6,$2B,$4C,$F0,$A2,$4C,$EE,$18,$80,$FF,$F4,$4E,$5E,$4E,$75
	dc.b $8C,$44,$42,$47,$4E,$45,$57,$48,$45,$41,$44,$45,$52,$00,$00,$00
	dc.b $4E,$56,$00,$00,$48,$E7,$01,$08,$3E,$2E,$00,$08,$48,$C7,$20,$07
	dc.b $D0,$AD,$F0,$CE,$B0,$AD,$F0,$C2,$6D,$06,$20,$6D,$F0,$BE,$4E,$90
	dc.b $28,$6D,$F0,$CE,$48,$C7,$20,$07,$D0,$AD,$F0,$CE,$2B,$40,$F0,$CE
	dc.b $2D,$4C,$00,$0A,$4C,$EE,$10,$80,$FF,$F8,$4E,$5E
;     candidate_code payload[836..3678) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_11_loc_00000344:
	movea.l (a7)+,a0
	addq.w #2,a7
	jmp (a0)

; CODE 12 LoadDump source section
macos_code_CODE_12:
;   source_section_id: macos-code-CODE-12
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 12
;   name: LoadDump
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 6928
;   payload_sha256: 9c563d29bea4465730181b661ea9a3a60d15276aa71a6be399b02b9a4091cbdb
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:12
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 12 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..44 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=44..6928 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..44) size=4 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[44..6928) size=6884 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 12 payload[0..6928) sha256=9c563d29bea4465730181b661ea9a3a60d15276aa71a6be399b02b9a4091cbdb
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_12_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$06,$C8,$00,$00,$00,$02,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..44) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_12_candidate_unresolved_prefix_00000028:
	dc.b $24,$1F,$22,$5F
;     candidate_code payload[44..6928) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=15 labels=2 xrefs=3
macos_code_CODE_12_loc_0000002c:
	movea.l (a7)+,a0
	clr.w d0
	move.b (a1),d0
macos_code_CODE_12_loc_00000032:
	move.b (a1)+,(a0)+
	dbf.w d0,loc_0_00000006
	movea.l (a7)+,a0
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)+
	move.b (a1)+,(a0)
	movea.l (a7)+,a0
	move.b (a1)+,(a0)+
	move.b (a1),(a0)
	movea.l d2,a0
	jmp (a0)

; CODE 13 Directives source section
macos_code_CODE_13:
;   source_section_id: macos-code-CODE-13
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 13
;   name: Directives
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 33354
;   payload_sha256: 1358e27cbf9cb7da402416dfa830bd93f99a23e16da5c9972f63549d171a30c8
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:13
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 13 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..44 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=44..33354 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..44) size=4 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[44..33354) size=33310 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 13 payload[0..33354) sha256=1358e27cbf9cb7da402416dfa830bd93f99a23e16da5c9972f63549d171a30c8
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_13_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$06,$D8,$00,$00,$00,$0D,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..44) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_13_candidate_unresolved_prefix_00000028:
	dc.b $22,$5F,$32,$1F
;     candidate_code payload[44..33354) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=61 labels=14 xrefs=16
macos_code_CODE_13_loc_0000002c:
	movea.l (a7)+,a0
	move.l a1,-(a7)
	lea.l -$0106(a5),a1
	clr.w d0
	move.b (a1)+,d0
	move.w d1,d2
	sub.w d0,d2
	ble.b loc_0_0000007C
	move.l a2,-(a7)
	move.w d3,-(a7)
	suba.w #$100,a7
	movea.l a7,a2
	tst.b -$0C5F(a5)
	bne.b loc_0_00000040
	bra.b loc_0_00000038
macos_code_CODE_13_loc_00000050:
	move.b (a1)+,d3
	cmpi.b #97,d3
	blt.b loc_0_00000036
	cmpi.b #122,d3
	bgt.b loc_0_00000036
	subi.b #32,d3
macos_code_CODE_13_loc_00000062:
	move.b d3,(a2)+
macos_code_CODE_13_loc_00000064:
	dbf.w d0,loc_0_00000024
	bra.b loc_0_00000044
macos_code_CODE_13_loc_0000006a:
	move.b (a1)+,(a2)+
macos_code_CODE_13_loc_0000006c:
	dbf.w d0,loc_0_0000003E
macos_code_CODE_13_loc_00000070:
	subq.w #2,d2
	blt.b loc_0_00000050
macos_code_CODE_13_loc_00000074:
	move.b #$20,(a2)+
	dbf.w d2,loc_0_00000048
macos_code_CODE_13_loc_0000007c:
	move.b #$2E,(a2)
	clr.w d2
	move.b (a0)+,d2
	cmp.w d1,d2
	blt.b loc_0_00000074
	clr.w d0
macos_code_CODE_13_loc_0000008a:
	addq.w #1,d0
	movea.l a7,a2
	move.w d1,d3
	subq.w #1,d3
macos_code_CODE_13_loc_00000092:
	cmpm.b (a2)+,(a0)+
	dbne.w d3,loc_0_00000066
	beq.b loc_0_00000084
	adda.w d3,a0
	sub.w d1,d2
	bge.b loc_0_0000005E
macos_code_CODE_13_loc_000000a0:
	lea.l $0100(a7),a7
	move.w (a7)+,d3
	movea.l (a7)+,a2
macos_code_CODE_13_loc_000000a8:
	movea.l (a7)+,a0
	addq.w #4,a7
	clr.b (a7)
	jmp (a0)
macos_code_CODE_13_loc_000000b0:
	lea.l $0100(a7),a7
	move.w (a7)+,d3
	movea.l (a7)+,a2
	movea.l (a7)+,a0
	movea.l (a7)+,a1
	move.w d0,(a1)
	move.b #$1,(a7)
	jmp (a0)

; CODE 14 MemMgr source section
macos_code_CODE_14:
;   source_section_id: macos-code-CODE-14
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 14
;   name: MemMgr
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 1886
;   payload_sha256: 14e851122fdae5910c2772def35a8b36c30dc7133cb92df8524f8a42ff5f8c70
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:14
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 14 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..236 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=236..1886 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..236) size=196 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[236..1886) size=1650 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 14 payload[0..1886) sha256=14e851122fdae5910c2772def35a8b36c30dc7133cb92df8524f8a42ff5f8c70
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_14_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$07,$40,$00,$00,$00,$0B,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..236) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_14_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$FF,$FC,$2F,$07,$10,$2E,$00,$08,$67,$0A,$48,$6D,$C8,$66
	dc.b $4E,$AD,$0A,$5A,$60,$08,$48,$6D,$C8,$66,$4E,$AD,$0A,$62,$70,$00
	dc.b $2B,$40,$C8,$3E,$70,$00,$2B,$40,$C8,$42,$70,$00,$2B,$40,$C8,$46
	dc.b $70,$00,$2B,$40,$C8,$4A,$42,$6D,$C8,$4E,$70,$00,$2B,$40,$C8,$50
	dc.b $3B,$7C,$03,$F8,$C8,$54,$70,$00,$2B,$40,$C8,$56,$1B,$7C,$00,$01
	dc.b $C8,$5A,$70,$00,$2B,$40,$C8,$3A,$70,$00,$2B,$40,$C8,$36,$70,$00
	dc.b $2B,$40,$C8,$6C,$42,$6D,$C8,$34,$1B,$7C,$00,$01,$C8,$5D,$10,$2E
	dc.b $00,$08,$67,$4C,$20,$7C,$00,$00,$01,$30,$22,$7C,$00,$00,$02,$AA
	dc.b $2E,$10,$9E,$91,$42,$67,$4E,$AD,$08,$82,$10,$1F,$67,$1A,$20,$07
	dc.b $90,$BC,$00,$02,$DD,$78,$2F,$00,$2F,$3C,$00,$00,$03,$F8,$4E,$AD
	dc.b $0A,$7A,$2B,$5F,$C8,$62,$60,$18,$20,$07,$90,$BC,$00,$04,$8C,$18
	dc.b $2F,$00,$2F,$3C,$00,$00,$03,$F8,$4E,$AD,$0A,$7A,$2B,$5F,$C8,$62
	dc.b $2E,$1F,$4E,$5E
;     candidate_code payload[236..1886) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_14_loc_000000ec:
	movea.l (a7)+,a0
	addq.w #2,a7
	jmp (a0)

; CODE 15 Errors source section
macos_code_CODE_15:
;   source_section_id: macos-code-CODE-15
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 15
;   name: Errors
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 3452
;   payload_sha256: ebe2c26fe6fffb8585f7e9e0ebfffa73ca877946c26eab44f0efbd96678018cd
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:15
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 15 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..96 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=96..3452 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..96) size=56 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[96..3452) size=3356 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 15 payload[0..3452) sha256=ebe2c26fe6fffb8585f7e9e0ebfffa73ca877946c26eab44f0efbd96678018cd
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_15_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$07,$98,$00,$00,$00,$07,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..96) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_15_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$00,$00,$2F,$0C,$28,$6E,$00,$0E,$20,$6E,$00,$08,$10,$BC
	dc.b $00,$01,$42,$40,$10,$14,$0C,$40,$00,$FF,$6C,$18,$20,$6E,$00,$08
	dc.b $42,$10,$42,$40,$10,$14,$52,$40,$18,$80,$42,$40,$10,$14,$19,$AE
	dc.b $00,$0D,$00,$00,$28,$5F,$4E,$5E
;     candidate_code payload[96..3452) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_15_loc_00000060:
	movea.l (a7)+,a0
	adda.w #$A,a7
	jmp (a0)

; CODE 16 New source section
macos_code_CODE_16:
;   source_section_id: macos-code-CODE-16
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 16
;   name: New
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 1034
;   payload_sha256: 51e7a7d264825cd4103b31a0bff37ff49fdb64e8ddb299b2a46d4bd3c07f6a37
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:16
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 16 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..246 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=246..1034 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..246) size=206 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[246..1034) size=788 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 16 payload[0..1034) sha256=51e7a7d264825cd4103b31a0bff37ff49fdb64e8ddb299b2a46d4bd3c07f6a37
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_16_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$07,$D0,$00,$00,$00,$03,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..246) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_16_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$FF,$FC,$48,$E7,$01,$08,$3E,$2E,$00,$08,$30,$07,$D0,$40
	dc.b $41,$ED,$EB,$6E,$3B,$70,$00,$00,$ED,$60,$30,$07,$53,$40,$41,$ED
	dc.b $CA,$D2,$E5,$40,$20,$70,$00,$00,$2F,$08,$48,$6D,$ED,$70,$4E,$AD
	dc.b $00,$92,$1B,$7C,$00,$01,$EE,$70,$3B,$6D,$ED,$60,$ED,$5E,$10,$2D
	dc.b $F0,$B1,$67,$0E,$30,$07,$D0,$40,$41,$ED,$EB,$3A,$3B,$70,$00,$00
	dc.b $EB,$5A,$10,$2D,$F3,$A6,$67,$38,$42,$A7,$2F,$2D,$F0,$D6,$42,$40
	dc.b $10,$2D,$ED,$70,$52,$40,$3F,$00,$4E,$AD,$07,$7A,$28,$5F,$20,$0C
	dc.b $66,$08,$48,$7A,$00,$82,$4E,$AD,$01,$D2,$48,$6D,$ED,$70,$2F,$0C
	dc.b $4E,$AD,$00,$92,$2F,$0C,$3F,$2D,$ED,$5E,$42,$67,$4E,$AD,$01,$6A
	dc.b $08,$2D,$00,$02,$ED,$5A,$67,$30,$10,$2D,$EB,$68,$66,$2A,$80,$2D
	dc.b $EB,$69,$66,$24,$48,$6D,$D2,$6E,$48,$7A,$00,$38,$42,$67,$4E,$AD
	dc.b $0A,$0A,$48,$6D,$D2,$6E,$48,$6D,$ED,$70,$42,$67,$4E,$AD,$0A,$0A
	dc.b $48,$6D,$D2,$6E,$4E,$AD,$09,$F2,$4C,$DF,$10,$80,$4E,$5E
;     candidate_code payload[246..1034) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_16_loc_000000f6:
	movea.l (a7)+,a0
	addq.w #2,a7
	jmp (a0)

; CODE 17 DispSymTbl source section
macos_code_CODE_17:
;   source_section_id: macos-code-CODE-17
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 17
;   name: DispSymTbl
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 3674
;   payload_sha256: e4c8e735bff587b55b1482bde5137deec3ae177ea802b09aac3e97401f2905b9
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:17
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 17 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..100 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=100..3674 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..100) size=60 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[100..3674) size=3574 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 17 payload[0..3674) sha256=e4c8e735bff587b55b1482bde5137deec3ae177ea802b09aac3e97401f2905b9
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_17_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$07,$E8,$00,$00,$00,$01,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..100) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_17_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$FF,$FC,$2F,$0C,$42,$A7,$20,$6E,$00,$08,$2F,$28,$00,$1C
	dc.b $3F,$3C,$00,$10,$4E,$AD,$07,$8A,$28,$5F,$2D,$4C,$00,$10,$20,$0C
	dc.b $67,$16,$70,$00,$29,$40,$00,$04,$70,$00,$29,$40,$00,$08,$70,$00
	dc.b $29,$40,$00,$0C,$28,$AE,$00,$0C,$28,$5F,$4E,$5E
;     candidate_code payload[100..3674) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_17_loc_00000064:
	movea.l (a7)+,a0
	addq.w #8,a7
	jmp (a0)

; CODE 18 FinishDirectives source section
macos_code_CODE_18:
;   source_section_id: macos-code-CODE-18
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 18
;   name: FinishDirectives
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 1974
;   payload_sha256: 96d836fa8382f88453204a38fddb5da2e46867767f572482abb8f9cbb5e431c6
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:18
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 18 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..1562 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=1562..1974 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..1562) size=1522 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[1562..1974) size=412 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 18 payload[0..1974) sha256=96d836fa8382f88453204a38fddb5da2e46867767f572482abb8f9cbb5e431c6
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_18_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$07,$F0,$00,$00,$00,$03,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..1562) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_18_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$FF,$F8,$48,$E7,$00,$18,$4A,$AD,$F3,$D8,$67,$06,$42,$67
	dc.b $4E,$AD,$07,$1A,$42,$A7,$2F,$2D,$F3,$EA,$4E,$AD,$01,$22,$28,$5F
	dc.b $20,$2D,$F4,$10,$90,$AD,$F3,$C6,$6A,$02,$44,$80,$28,$80,$10,$2D
	dc.b $F4,$0F,$67,$06,$20,$14,$44,$80,$28,$80,$26,$4C,$58,$8B,$26,$AD
	dc.b $F3,$AC,$42,$2D,$F3,$A2,$2B,$6D,$F3,$FA,$F4,$18,$2B,$6D,$F3,$F6
	dc.b $F4,$10,$1B,$6D,$F3,$D3,$F4,$0F,$4C,$DF,$18,$00,$4E,$5E,$4E,$75
	dc.b $8E,$46,$49,$4E,$49,$53,$48,$54,$45,$4D,$50,$4C,$41,$54,$45,$00
	dc.b $00,$00,$4E,$56,$FE,$CC,$48,$E7,$0F,$18,$10,$2D,$F3,$A3,$67,$30
	dc.b $42,$2D,$F3,$A3,$2B,$6D,$F4,$10,$F4,$06,$2B,$6D,$F4,$02,$F4,$18
	dc.b $2B,$6D,$F3,$FE,$F4,$10,$2B,$6D,$F4,$18,$F4,$14,$42,$2D,$F4,$0F
	dc.b $3B,$7C,$A0,$00,$F3,$E0,$42,$67,$1F,$3C,$00,$01,$4E,$AD,$07,$0A
	dc.b $1D,$6D,$F3,$95,$FF,$E3,$2D,$6D,$ED,$5A,$FF,$EC,$42,$2D,$EC,$FE
	dc.b $4A,$AD,$F4,$1C,$67,$00,$01,$6A,$08,$2D,$00,$00,$F4,$1B,$67,$0E
	dc.b $52,$AD,$F4,$18,$42,$67,$1F,$3C,$00,$01,$4E,$AD,$07,$0A,$10,$2D
	dc.b $EC,$FF,$67,$0A,$08,$2D,$00,$00,$ED,$5A,$56,$C1,$C0,$01,$4A,$00
	dc.b $67,$0A,$08,$2D,$00,$02,$ED,$5C,$56,$C1,$C0,$01,$1D,$40,$FF,$E0
	dc.b $3F,$3C,$00,$40,$4E,$AD,$01,$4A,$1A,$2D,$F3,$95,$30,$2D,$F3,$E0
	dc.b $D0,$7C,$01,$00,$3D,$40,$FF,$FC,$42,$47,$20,$6D,$F4,$1C,$2D,$68
	dc.b $00,$04,$FF,$E4,$20,$6D,$F4,$1C,$21,$6D,$F4,$18,$00,$04,$70,$00
	dc.b $20,$6D,$F4,$1C,$30,$28,$00,$08,$72,$00,$32,$2E,$FF,$FC,$80,$81
	dc.b $20,$6D,$F4,$1C,$31,$40,$00,$08,$20,$6D,$F4,$1C,$42,$40,$10,$28
	dc.b $00,$0C,$3C,$00,$20,$6D,$F4,$1C,$42,$40,$10,$30,$60,$0C,$1D,$40
	dc.b $FF,$E1,$BA,$2E,$FF,$E1,$67,$32,$4A,$47,$6F,$12,$3F,$07,$2F,$3C
	dc.b $00,$00,$00,$02,$3F,$3C,$FF,$FF,$4E,$AD,$01,$5A,$42,$47,$1A,$2E
	dc.b $FF,$E1,$3F,$3C,$00,$06,$10,$05,$48,$80,$48,$C0,$2F,$00,$4E,$AD
	dc.b $01,$42,$3F,$3C,$00,$37,$4E,$AD,$01,$4A,$53,$46,$20,$6D,$F4,$1C
	dc.b $11,$46,$00,$0C,$3F,$3C,$00,$08,$20,$6D,$F4,$1C,$48,$68,$00,$0C
	dc.b $4E,$AD,$01,$42,$3F,$3C,$00,$06,$42,$A7,$4E,$AD,$01,$42,$10,$2E
	dc.b $FF,$E0,$67,$12,$2F,$3C,$00,$02,$00,$01,$2F,$3C,$FF,$FF,$00,$00
	dc.b $4E,$AD,$01,$5A,$60,$1A,$52,$47,$70,$19,$B0,$47,$6C,$12,$3F,$07
	dc.b $2F,$3C,$00,$00,$00,$02,$3F,$3C,$FF,$FF,$4E,$AD,$01,$5A,$42,$47
	dc.b $30,$06,$48,$C0,$D1,$AD,$F4,$18,$2B,$6E,$FF,$E4,$F4,$1C,$66,$00
	dc.b $FF,$1A,$4A,$47,$6F,$10,$3F,$07,$2F,$3C,$00,$00,$00,$02,$3F,$3C
	dc.b $FF,$FF,$4E,$AD,$01,$5A,$2B,$6D,$F4,$18,$F4,$14,$20,$2D,$F4,$18
	dc.b $B0,$AD,$F4,$10,$6F,$06,$2B,$6D,$F4,$18,$F4,$10,$4E,$AD,$07,$12
	dc.b $10,$2D,$F3,$A4,$67,$6A,$10,$2D,$F4,$0F,$67,$18,$70,$00,$20,$6D
	dc.b $F3,$EE,$30,$28,$00,$08,$80,$BC,$FF,$FF,$80,$00,$20,$6D,$F3,$EE
	dc.b $31,$40,$00,$08,$3F,$3C,$00,$06,$70,$01,$2F,$00,$4E,$AD,$01,$42
	dc.b $3F,$3C,$00,$06,$20,$2D,$F4,$10,$6A,$02,$44,$80,$2F,$00,$4E,$AD
	dc.b $01,$42,$3F,$3C,$00,$3C,$4E,$AD,$01,$4A,$42,$A7,$2F,$2D,$F3,$EE
	dc.b $4E,$AD,$01,$22,$26,$5F,$26,$AD,$F4,$10,$10,$2E,$00,$08,$67,$00
	dc.b $00,$9A,$28,$0B,$58,$84,$20,$44,$70,$00,$20,$80,$60,$00,$00,$8C
	dc.b $10,$2D,$F3,$A5,$67,$00,$00,$84,$4A,$AD,$F3,$E6,$67,$46,$3F,$3C
	dc.b $00,$06,$70,$01,$2F,$00,$4E,$AD,$01,$42,$3F,$3C,$00,$06,$20,$2D
	dc.b $F4,$06,$6A,$02,$44,$80,$2F,$00,$4E,$AD,$01,$42,$3F,$3C,$00,$3C
	dc.b $4E,$AD,$01,$4A,$42,$A7,$2F,$2D,$F3,$E6,$4E,$AD,$01,$22,$26,$5F
	dc.b $26,$AD,$F4,$06,$28,$0B,$58,$84,$20,$44,$70,$00,$20,$80,$1B,$6D
	dc.b $F4,$0E,$F4,$0F,$3F,$3C,$00,$06,$42,$A7,$4E,$AD,$01,$42,$3F,$3C
	dc.b $00,$06,$20,$2D,$F4,$10,$6A,$02,$44,$80,$2F,$00,$4E,$AD,$01,$42
	dc.b $3F,$3C,$00,$3C,$4E,$AD,$01,$4A,$10,$2D,$F0,$B1,$67,$0C,$2F,$2D
	dc.b $EB,$5C,$3F,$2D,$DA,$5A,$4E,$AD,$06,$B2,$3F,$3C,$00,$18,$4E,$AD
	dc.b $01,$4A,$3B,$6D,$DA,$5C,$DA,$5A,$10,$2D,$F0,$ED,$67,$00,$00,$A4
	dc.b $1B,$7C,$00,$01,$F0,$EC,$1F,$3C,$00,$01,$48,$6E,$FF,$FA,$4E,$AD
	dc.b $07,$FA,$5B,$6E,$FF,$FA,$42,$6D,$F0,$E6,$20,$6D,$F0,$EE,$2D,$50
	dc.b $FF,$D8,$28,$6E,$FF,$D8,$42,$67,$48,$6D,$EC,$B4,$2F,$2D,$F0,$E8
	dc.b $3F,$3C,$00,$02,$3F,$2D,$F0,$E6,$4E,$AD,$08,$DA,$3D,$5F,$FF,$F6
	dc.b $66,$1A,$B9,$EE,$FF,$D8,$67,$02,$60,$58,$42,$67,$4E,$AD,$09,$02
	dc.b $3D,$57,$FF,$F8,$48,$7A,$03,$18,$4E,$AD,$01,$DA,$30,$2E,$FF,$F6
	dc.b $D1,$6D,$F0,$E6,$2F,$0C,$4E,$AD,$01,$3A,$53,$6E,$FF,$FA,$4A,$6E
	dc.b $FF,$FA,$6E,$02,$60,$2C,$42,$A7,$4E,$AD,$07,$A2,$28,$5F,$20,$0C
	dc.b $66,$02,$60,$1E,$20,$6D,$F0,$EE,$20,$68,$00,$04,$21,$4C,$00,$04
	dc.b $20,$6D,$F0,$EE,$28,$A8,$00,$04,$20,$6D,$F0,$EE,$21,$4C,$00,$04
	dc.b $60,$84,$2F,$2D,$DA,$60,$4E,$AD,$07,$B2,$2F,$2D,$DA,$64,$4E,$AD
	dc.b $07,$B2,$42,$6D,$CD,$68,$42,$6D,$CD,$66,$42,$6D,$CD,$60,$10,$2D
	dc.b $EC,$FF,$67,$50,$2F,$2D,$EB,$60,$1F,$3C,$00,$04,$4E,$AD,$04,$5A
	dc.b $42,$67,$48,$7A,$02,$26,$48,$6D,$EB,$60,$1F,$3C,$00,$04,$42,$A7
	dc.b $4E,$AD,$04,$52,$4A,$5F,$67,$08,$48,$7A,$02,$52,$4E,$AD,$01,$D2
	dc.b $0C,$AD,$00,$00,$00,$80,$E3,$E6,$5E,$C0,$44,$00,$1B,$40,$E3,$E5
	dc.b $2F,$2D,$EB,$8E,$70,$20,$2F,$00,$4E,$AD,$0A,$82,$20,$1F,$44,$80
	dc.b $2B,$40,$E3,$E6,$10,$2D,$E5,$17,$67,$06,$48,$7A,$01,$FC,$AB,$FF
	dc.b $3D,$6D,$F4,$2E,$FF,$FE,$42,$2D,$C8,$5D,$1B,$7C,$00,$01,$CD,$5F
	dc.b $4E,$AD,$06,$32,$42,$2D,$CD,$5F,$1B,$7C,$00,$01,$C8,$5D,$3B,$6E
	dc.b $FF,$FE,$F4,$2E,$10,$2D,$F4,$0F,$67,$34,$10,$2D,$F3,$A4,$67,$10
	dc.b $20,$6D,$F3,$EE,$20,$68,$00,$04,$21,$6D,$F4,$10,$00,$02,$60,$1E
	dc.b $10,$2D,$F3,$A5,$67,$18,$4A,$AD,$F3,$E6,$56,$C1,$C0,$01,$67,$0E
	dc.b $20,$6D,$F3,$E6,$20,$68,$00,$04,$21,$6D,$F4,$06,$00,$02,$1B,$6E
	dc.b $FF,$E3,$F3,$95,$2B,$6E,$FF,$EC,$ED,$5A,$30,$2D,$F0,$E2,$B0,$6D
	dc.b $F0,$E0,$6F,$06,$3B,$6D,$F0,$E2,$F0,$E0,$2B,$7C,$00,$01,$00,$00
	dc.b $F0,$E2,$10,$2D,$F0,$ED,$67,$14,$48,$6D,$EC,$B4,$4E,$AD,$08,$BA
	dc.b $48,$7A,$01,$56,$4E,$AD,$08,$AA,$42,$2D,$F0,$ED,$2F,$2D,$F0,$EE
	dc.b $2F,$2D,$EC,$B0,$4E,$AD,$07,$9A,$4A,$AD,$F0,$7C,$67,$08,$2F,$2D
	dc.b $F0,$7C,$4E,$AD,$07,$72,$70,$00,$2B,$40,$F0,$7C,$70,$00,$2B,$40
	dc.b $F0,$78,$10,$2D,$EC,$FF,$67,$58,$42,$67,$48,$7A,$01,$0E,$48,$6D
	dc.b $EB,$60,$1F,$3C,$00,$03,$42,$A7,$4E,$AD,$04,$52,$4A,$5F,$67,$08
	dc.b $48,$7A,$00,$C6,$4E,$AD,$01,$D2,$70,$00,$2B,$40,$E3,$E6,$42,$2D
	dc.b $E3,$E5,$10,$2D,$F3,$A5,$67,$28,$08,$2D,$00,$04,$ED,$5C,$56,$C0
	dc.b $4A,$00,$67,$1C,$08,$2D,$00,$00,$ED,$5D,$56,$C1,$C0,$01,$67,$10
	dc.b $1F,$3C,$00,$01,$4E,$AD,$08,$0A,$48,$6D,$08,$0A,$4E,$AD,$01,$9A
	dc.b $4A,$AD,$F3,$A8,$67,$08,$2F,$2D,$F3,$A8,$4E,$AD,$07,$72,$70,$00
	dc.b $2B,$40,$F3,$A8,$10,$2D,$F3,$A5,$67,$14,$70,$00,$2B,$40,$EC,$A8
	dc.b $70,$00,$2B,$40,$EC,$A4,$2F,$2D,$F3,$AC,$4E,$AD,$07,$72,$2B,$6D
	dc.b $F3,$B0,$F3,$AC,$1B,$7C,$00,$01,$F3,$A7,$42,$2D,$F3,$A6,$42,$2D
	dc.b $F3,$A5,$42,$2D,$F3,$A4,$42,$2D,$F3,$A3,$70,$00,$2B,$40,$F3,$E6
	dc.b $42,$2D,$F3,$A2,$42,$6D,$F3,$E0,$70,$00,$2B,$40,$F3,$E2,$2B,$6D
	dc.b $F4,$18,$F4,$14,$42,$2D,$F4,$0F,$42,$2D,$E9,$1E,$4C,$DF,$18,$F0
	dc.b $4E,$5E
;     candidate_code payload[1562..1974) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_18_loc_0000061a:
	movea.l (a7)+,a0
	addq.w #2,a7
	jmp (a0)

; CODE 19 SetupArgV source section
macos_code_CODE_19:
;   source_section_id: macos-code-CODE-19
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: covered_placeholder
;   resource_type: CODE
;   id: 19
;   name: SetupArgV
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 556
;   payload_sha256: 46027b8ec8f830b28abc470f5e942b54f7845efd9cf136f68e3b2b8a9873f3ce
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:19
;   listing: kind=structured_placeholder available=False reason=no candidate preview range; classifier deferred byte-entry evidence: missing_m68k_movea_l_stack_to_a0_entry
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 19 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=unknown span=40..556 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     deferred payload[40..556) size=516 entrypoint=False status=deferred parser_use=deferred_only evidence=missing_m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.byte_entry_rule.unknown
;   byte_preserving_placeholder: CODE 19 payload[0..556) sha256=46027b8ec8f830b28abc470f5e942b54f7845efd9cf136f68e3b2b8a9873f3ce
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_19_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$08,$08,$00,$00,$00,$01,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     deferred payload[40..556) status=deferred parser_use=deferred_only evidence=missing_m68k_movea_l_stack_to_a0_entry
macos_code_CODE_19_deferred_00000028:
	dc.b $4E,$56,$FD,$F6,$48,$E7,$07,$00,$20,$6E,$00,$08,$43,$EE,$FF,$00
	dc.b $70,$7F,$32,$D8,$51,$C8,$FF,$FC,$48,$6D,$D2,$72,$48,$6E,$FF,$00
	dc.b $42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$72,$48,$7A,$01,$D4,$42,$67
	dc.b $4E,$AD,$0A,$0A,$48,$6D,$D2,$76,$48,$6E,$FD,$F6,$3F,$3C,$00,$FF
	dc.b $4E,$AD,$09,$E2,$48,$6D,$D2,$76,$4E,$AD,$09,$DA,$48,$6E,$FE,$F6
	dc.b $2F,$3C,$00,$00,$00,$80,$4E,$AD,$0A,$52,$2B,$6E,$FE,$F6,$D2,$C0
	dc.b $70,$00,$2B,$40,$D2,$BC,$42,$40,$10,$2E,$FD,$F6,$52,$40,$41,$EE
	dc.b $FD,$F6,$42,$30,$00,$00,$7C,$01,$42,$40,$10,$2E,$FD,$F7,$3E,$00
	dc.b $70,$1F,$B0,$AD,$D2,$BC,$5E,$C0,$4A,$00,$67,$00,$01,$28,$4A,$47
	dc.b $56,$C1,$C0,$01,$67,$00,$01,$1E,$70,$20,$B0,$47,$57,$C0,$4A,$00
	dc.b $66,$0A,$72,$09,$B2,$47,$57,$C1,$80,$01,$67,$10,$52,$46,$42,$40
	dc.b $41,$EE,$FD,$F6,$10,$30,$60,$00,$3E,$00,$60,$DC,$4A,$47,$67,$C0
	dc.b $52,$AD,$D2,$BC,$20,$6D,$D2,$C0,$20,$2D,$D2,$BC,$E5,$80,$48,$70
	dc.b $08,$00,$2F,$3C,$00,$00,$01,$00,$4E,$AD,$0A,$52,$42,$45,$70,$20
	dc.b $B0,$47,$56,$C0,$4A,$00,$67,$00,$00,$B8,$72,$09,$B2,$47,$56,$C1
	dc.b $C0,$01,$67,$00,$00,$AC,$4A,$47,$56,$C1,$C0,$01,$67,$00,$00,$A2
	dc.b $52,$45,$0C,$47,$00,$B6,$57,$C0,$4A,$00,$67,$70,$32,$06,$52,$41
	dc.b $42,$42,$41,$EE,$FD,$F6,$14,$30,$10,$00,$4A,$42,$56,$C1,$C0,$01
	dc.b $67,$5A,$52,$46,$42,$40,$41,$EE,$FD,$F6,$10,$30,$60,$00,$3E,$00
	dc.b $70,$6E,$B0,$47,$66,$16,$20,$6D,$D2,$C0,$20,$2D,$D2,$BC,$E5,$80
	dc.b $20,$70,$08,$00,$11,$BC,$00,$0D,$50,$00,$60,$42,$70,$74,$B0,$47
	dc.b $66,$16,$20,$6D,$D2,$C0,$20,$2D,$D2,$BC,$E5,$80,$20,$70,$08,$00
	dc.b $11,$BC,$00,$09,$50,$00,$60,$26,$20,$6D,$D2,$C0,$20,$2D,$D2,$BC
	dc.b $E5,$80,$20,$70,$08,$00,$11,$87,$50,$00,$60,$12,$20,$6D,$D2,$C0
	dc.b $20,$2D,$D2,$BC,$E5,$80,$20,$70,$08,$00,$11,$87,$50,$00,$52,$46
	dc.b $42,$40,$41,$EE,$FD,$F6,$10,$30,$60,$00,$3E,$00,$60,$00,$FF,$40
	dc.b $20,$6D,$D2,$C0,$20,$2D,$D2,$BC,$E5,$80,$20,$70,$08,$00,$10,$85
	dc.b $60,$00,$FE,$CE,$52,$AD,$D2,$BC,$20,$6D,$D2,$C0,$20,$2D,$D2,$BC
	dc.b $E5,$80,$72,$00,$21,$81,$08,$00,$20,$6D,$D2,$C0,$2F,$08,$2F,$3C
	dc.b $00,$00,$01,$00,$4E,$AD,$0A,$52,$20,$6D,$D2,$C0,$20,$50,$43,$EE
	dc.b $FF,$00,$70,$7F,$30,$D9,$51,$C8,$FF,$FC,$4C,$DF,$00,$E0,$4E,$5E
	dc.b $2E,$9F,$4E,$75,$89,$53,$45,$54,$55,$50,$41,$52,$47,$56,$00,$04
	dc.b $02,$3F,$20,$00

; CODE 20 INTENV source section
macos_code_CODE_20:
;   source_section_id: macos-code-CODE-20
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 20
;   name: INTENV
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 5262
;   payload_sha256: de9f4a82222f3ff12586a0bb691cc6b5d513777d498d223dfa45311d4a7dc84a
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:20
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 20 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..2876 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2876..5262 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..2876) size=2836 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[2876..5262) size=2386 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 20 payload[0..5262) sha256=de9f4a82222f3ff12586a0bb691cc6b5d513777d498d223dfa45311d4a7dc84a
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_20_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$08,$10,$00,$00,$00,$1B,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..2876) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_20_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$00,$00,$2F,$2E,$00,$10,$2F,$2E,$00,$0C,$2F,$2E,$00,$08
	dc.b $70,$00,$2F,$00,$4E,$BA,$08,$1A,$4E,$5E,$4E,$75,$87,$66,$61,$63
	dc.b $63,$65,$73,$73,$00,$00,$4E,$56,$FF,$F8,$48,$E7,$01,$08,$70,$FF
	dc.b $2D,$40,$FF,$FC,$48,$6E,$FF,$FC,$4E,$BA,$03,$10,$28,$40,$20,$0C
	dc.b $58,$4F,$66,$04,$70,$FF,$60,$42,$30,$2E,$00,$0E,$52,$40,$38,$80
	dc.b $42,$6C,$00,$02,$70,$00,$29,$40,$00,$04,$2F,$0C,$48,$78,$64,$00
	dc.b $2F,$2E,$00,$08,$48,$6E,$FF,$F8,$4E,$BA,$07,$C6,$2E,$00,$4F,$EF
	dc.b $00,$10,$67,$06,$42,$54,$70,$FF,$60,$10,$4A,$AC,$00,$04,$66,$06
	dc.b $29,$6E,$FF,$F8,$00,$04,$20,$2E,$FF,$FC,$4C,$EE,$10,$80,$FF,$F0
	dc.b $4E,$5E,$4E,$75,$84,$6F,$70,$65,$6E,$00,$00,$00,$4E,$56,$00,$00
	dc.b $48,$E7,$01,$08,$4A,$AE,$00,$08,$6C,$12,$70,$00,$2F,$00,$72,$16
	dc.b $2F,$01,$4E,$BA,$06,$22,$70,$FF,$50,$4F,$60,$40,$48,$6E,$00,$08
	dc.b $4E,$BA,$02,$88,$28,$40,$20,$0C,$58,$4F,$66,$04,$70,$FF,$60,$2C
	dc.b $2F,$0C,$20,$6C,$00,$04,$22,$68,$00,$08,$4E,$91,$2E,$00,$42,$54
	dc.b $4A,$87,$58,$4F,$67,$14,$30,$2C,$00,$02,$48,$C0,$2F,$00,$2F,$07
	dc.b $4E,$BA,$05,$E4,$70,$FF,$50,$4F,$60,$02,$70,$00,$4C,$EE,$10,$80
	dc.b $FF,$F8,$4E,$5E,$4E,$75,$85,$63,$6C,$6F,$73,$65,$00,$00,$4E,$56
	dc.b $00,$00,$48,$E7,$03,$08,$2C,$2E,$00,$10,$4A,$AE,$00,$08,$6C,$12
	dc.b $70,$00,$2F,$00,$72,$16,$2F,$01,$4E,$BA,$05,$AC,$70,$FF,$50,$4F
	dc.b $60,$62,$48,$6E,$00,$08,$4E,$BA,$02,$12,$28,$40,$20,$0C,$58,$4F
	dc.b $66,$04,$70,$FF,$60,$4E,$70,$01,$C0,$54,$66,$12,$70,$00,$2F,$00
	dc.b $72,$09,$2F,$01,$4E,$BA,$05,$80,$70,$FF,$50,$4F,$60,$36,$29,$46
	dc.b $00,$0C,$29,$6E,$00,$0C,$00,$10,$2F,$0C,$20,$6C,$00,$04,$22,$68
	dc.b $00,$0C,$4E,$91,$2E,$00,$58,$4F,$67,$14,$30,$2C,$00,$02,$48,$C0
	dc.b $2F,$00,$2F,$07,$4E,$BA,$05,$50,$70,$FF,$50,$4F,$60,$06,$20,$06
	dc.b $90,$AC,$00,$0C,$4C,$EE,$10,$C0,$FF,$F4,$4E,$5E,$4E,$75,$84,$72
	dc.b $65,$61,$64,$00,$00,$00,$4E,$56,$00,$00,$48,$E7,$03,$08,$2C,$2E
	dc.b $00,$10,$4A,$AE,$00,$08,$6C,$12,$70,$00,$2F,$00,$72,$16,$2F,$01
	dc.b $4E,$BA,$05,$14,$70,$FF,$50,$4F,$60,$62,$48,$6E,$00,$08,$4E,$BA
	dc.b $01,$7A,$28,$40,$20,$0C,$58,$4F,$66,$04,$70,$FF,$60,$4E,$70,$02
	dc.b $C0,$54,$66,$12,$70,$00,$2F,$00,$72,$09,$2F,$01,$4E,$BA,$04,$E8
	dc.b $70,$FF,$50,$4F,$60,$36,$29,$46,$00,$0C,$29,$6E,$00,$0C,$00,$10
	dc.b $2F,$0C,$20,$6C,$00,$04,$22,$68,$00,$10,$4E,$91,$2E,$00,$58,$4F
	dc.b $67,$14,$30,$2C,$00,$02,$48,$C0,$2F,$00,$2F,$07,$4E,$BA,$04,$B8
	dc.b $70,$FF,$50,$4F,$60,$06,$20,$06,$90,$AC,$00,$0C,$4C,$EE,$10,$C0
	dc.b $FF,$F4,$4E,$5E,$4E,$75,$85,$77,$72,$69,$74,$65,$00,$00,$4E,$56
	dc.b $FF,$FC,$48,$E7,$03,$18,$2C,$2E,$00,$0C,$26,$6E,$00,$10,$4A,$AE
	dc.b $00,$08,$6C,$14,$70,$00,$2F,$00,$72,$16,$2F,$01,$4E,$BA,$04,$78
	dc.b $70,$FF,$50,$4F,$60,$00,$00,$D2,$48,$6E,$00,$08,$4E,$BA,$00,$DC
	dc.b $28,$40,$20,$0C,$58,$4F,$66,$06,$70,$FF,$60,$00,$00,$BC,$20,$06
	dc.b $04,$80,$00,$00,$66,$01,$67,$32,$2F,$0B,$2F,$06,$2F,$0C,$20,$6C
	dc.b $00,$04,$22,$68,$00,$14,$4E,$91,$2E,$00,$4F,$EF,$00,$0C,$66,$06
	dc.b $70,$00,$60,$00,$00,$94,$30,$2C,$00,$02,$48,$C0,$2F,$00,$2F,$07
	dc.b $4E,$BA,$04,$24,$70,$FF,$50,$4F,$60,$7E,$20,$0B,$6C,$12,$70,$00
	dc.b $2F,$00,$72,$09,$2F,$01,$4E,$BA,$04,$0E,$70,$FF,$50,$4F,$60,$68
	dc.b $70,$FF,$90,$8B,$2D,$40,$FF,$FC,$48,$6E,$FF,$FC,$4E,$BA,$00,$6C
	dc.b $26,$40,$20,$0B,$58,$4F,$66,$04,$70,$FF,$60,$4C,$48,$6E,$00,$08
	dc.b $4E,$BA,$00,$58,$28,$40,$20,$4B,$22,$4C,$70,$04,$20,$D9,$51,$C8
	dc.b $FF,$FC,$70,$00,$2F,$00,$48,$78,$66,$01,$2F,$0C,$20,$6C,$00,$04
	dc.b $22,$68,$00,$14,$4E,$91,$2E,$00,$4F,$EF,$00,$10,$67,$16,$42,$53
	dc.b $30,$2C,$00,$02,$48,$C0,$2F,$00,$2F,$07,$4E,$BA,$03,$AA,$70,$FF
	dc.b $50,$4F,$60,$04,$20,$2E,$FF,$FC,$4C,$EE,$18,$C0,$FF,$EC,$4E,$5E
	dc.b $4E,$75,$85,$69,$6F,$63,$74,$6C,$00,$00,$4E,$56,$FF,$FC,$48,$E7
	dc.b $11,$18,$26,$6E,$00,$08,$4A,$6D,$CF,$92,$66,$04,$4E,$BA,$01,$2A
	dc.b $30,$2D,$CF,$92,$48,$C0,$81,$FC,$00,$14,$48,$C0,$2E,$00,$53,$87
	dc.b $4A,$93,$5C,$C3,$44,$03,$67,$04,$20,$13,$60,$04,$70,$FF,$90,$93
	dc.b $BE,$80,$6C,$14,$70,$00,$2F,$00,$72,$16,$2F,$01,$4E,$BA,$03,$48
	dc.b $70,$00,$50,$4F,$60,$00,$00,$DA,$4A,$93,$6D,$2E,$20,$6D,$CF,$94
	dc.b $20,$13,$E5,$88,$22,$00,$E5,$88,$D0,$81,$49,$F0,$08,$00,$4A,$54
	dc.b $66,$00,$00,$BC,$70,$00,$2F,$00,$72,$09,$2F,$01,$4E,$BA,$03,$18
	dc.b $70,$00,$28,$40,$50,$4F,$60,$00,$00,$A6,$70,$FF,$90,$93,$20,$6D
	dc.b $CF,$94,$E5,$88,$22,$00,$E5,$88,$D0,$81,$49,$F0,$08,$00,$60,$08
	dc.b $4A,$54,$67,$18,$49,$EC,$00,$14,$20,$6D,$CF,$94,$20,$07,$E5,$88
	dc.b $22,$00,$E5,$88,$D0,$81,$D1,$C0,$B1,$CC,$64,$E4,$20,$6D,$CF,$94
	dc.b $20,$07,$E5,$88,$22,$00,$E5,$88,$D0,$81,$D1,$C0,$B1,$CC,$64,$4E
	dc.b $30,$2D,$CF,$92,$48,$C0,$D0,$BC,$00,$00,$01,$90,$2F,$00,$2F,$2D
	dc.b $CF,$94,$4E,$BA,$03,$3C,$2D,$40,$FF,$FC,$50,$4F,$66,$12,$70,$00
	dc.b $2F,$00,$72,$18,$2F,$01,$4E,$BA,$02,$9E,$70,$00,$50,$4F,$60,$30
	dc.b $20,$07,$52,$80,$20,$6E,$FF,$FC,$E5,$88,$22,$00,$E5,$88,$D0,$81
	dc.b $49,$F0,$08,$00,$06,$6D,$01,$90,$CF,$92,$2B,$48,$CF,$94,$20,$6D
	dc.b $CF,$94,$20,$0C,$90,$88,$72,$14,$4E,$AD,$02,$7A,$26,$80,$20,$0C
	dc.b $4C,$EE,$18,$88,$FF,$EC,$4E,$5E,$4E,$75,$8A,$5F,$67,$65,$74,$49
	dc.b $4F,$50,$6F,$72,$74,$00,$00,$00,$4E,$56,$00,$00,$2F,$0C,$3B,$7C
	dc.b $01,$90,$CF,$92,$48,$78,$01,$90,$70,$00,$2F,$00,$4E,$BA,$02,$C2
	dc.b $2B,$40,$CF,$94,$4A,$AD,$CF,$9C,$50,$4F,$67,$46,$22,$6D,$CF,$9C
	dc.b $20,$69,$00,$1C,$22,$6D,$CF,$94,$70,$3C,$A0,$2E,$20,$6D,$CF,$94
	dc.b $49,$D0,$60,$20,$4A,$54,$67,$18,$70,$00,$2F,$00,$48,$78,$66,$01
	dc.b $2F,$0C,$20,$6C,$00,$04,$22,$68,$00,$14,$4E,$91,$4F,$EF,$00,$0C
	dc.b $49,$EC,$00,$14,$20,$6D,$CF,$94,$41,$E8,$00,$28,$B1,$CC,$64,$D4
	dc.b $60,$28,$70,$00,$2F,$00,$48,$7A,$00,$54,$4E,$BA,$FB,$2A,$70,$01
	dc.b $2F,$00,$48,$7A,$00,$48,$4E,$BA,$FB,$1E,$70,$01,$2F,$00,$48,$7A
	dc.b $00,$3C,$4E,$BA,$FB,$12,$4F,$EF,$00,$18,$41,$ED,$08,$5A,$22,$6D
	dc.b $CF,$8E,$23,$48,$00,$04,$4A,$AD,$CF,$8A,$66,$08,$41,$ED,$CE,$46
	dc.b $2B,$48,$CF,$8A,$28,$6E,$FF,$FC,$4E,$5E,$4E,$75,$8D,$5F,$69,$6E
	dc.b $69,$74,$49,$4F,$50,$74,$61,$62,$6C,$65,$00,$0C,$64,$65,$76,$3A
	dc.b $63,$6F,$6E,$73,$6F,$6C,$65,$00,$4E,$56,$00,$00,$48,$E7,$03,$00
	dc.b $30,$2D,$CF,$92,$48,$C0,$81,$FC,$00,$14,$48,$C0,$2C,$00,$53,$86
	dc.b $7E,$00,$60,$0A,$2F,$07,$4E,$BA,$FB,$24,$58,$4F,$52,$87,$BC,$87
	dc.b $6C,$F2,$4A,$AD,$CF,$74,$67,$04,$4E,$AD,$09,$72,$4C,$EE,$00,$C0
	dc.b $FF,$F8,$4E,$5E,$4E,$75,$8B,$5F,$63,$6F,$72,$65,$49,$4F,$45,$78
	dc.b $69,$74,$00,$00,$4E,$56,$00,$00,$2F,$07,$7E,$00,$30,$2E,$00,$0A
	dc.b $04,$40,$FF,$88,$67,$00,$01,$08,$04,$40,$00,$0C,$67,$00,$00,$C4
	dc.b $04,$40,$00,$2F,$67,$00,$00,$F0,$53,$40,$67,$00,$00,$86,$53,$40
	dc.b $67,$00,$00,$A8,$53,$40,$67,$00,$00,$8E,$53,$40,$67,$00,$00,$AC
	dc.b $53,$40,$67,$00,$00,$A2,$53,$40,$67,$00,$00,$C4,$53,$40,$67,$00
	dc.b $00,$AA,$53,$40,$67,$00,$00,$B4,$55,$40,$67,$00,$00,$A6,$53,$40
	dc.b $67,$00,$00,$94,$53,$40,$67,$00,$00,$8A,$53,$40,$67,$50,$53,$40
	dc.b $67,$58,$53,$40,$67,$00,$00,$9C,$53,$40,$67,$52,$53,$40,$67,$00
	dc.b $00,$9A,$53,$40,$67,$4C,$53,$40,$67,$7C,$55,$40,$67,$70,$53,$40
	dc.b $67,$30,$53,$40,$67,$40,$53,$40,$67,$1C,$53,$40,$67,$40,$53,$40
	dc.b $67,$4C,$53,$40,$67,$14,$53,$40,$67,$10,$04,$40,$00,$21,$67,$70
	dc.b $60,$6E,$7E,$14,$60,$6A,$7E,$0E,$60,$66,$7E,$1C,$60,$62,$7E,$11
	dc.b $60,$5E,$7E,$06,$60,$5A,$7E,$14,$60,$56,$7E,$1F,$60,$52,$7E,$10
	dc.b $60,$4E,$7E,$02,$60,$4A,$7E,$09,$60,$46,$7E,$04,$60,$42,$7E,$05
	dc.b $60,$3E,$7E,$0C,$60,$3A,$7E,$06,$60,$36,$7E,$14,$60,$32,$7E,$06
	dc.b $60,$2E,$7E,$1A,$60,$2A,$7E,$16,$60,$26,$7E,$0D,$60,$22,$7E,$1D
	dc.b $60,$1E,$7E,$09,$60,$1A,$7E,$17,$60,$16,$7E,$06,$60,$12,$7E,$10
	dc.b $60,$0E,$7E,$1E,$60,$0A,$7E,$0D,$60,$06,$7E,$1E,$60,$02,$7E,$14
	dc.b $20,$07,$2E,$2E,$FF,$FC,$4E,$5E,$4E,$75,$89,$5F,$6D,$61,$70,$4F
	dc.b $53,$65,$72,$72,$00,$00,$4E,$56,$00,$00,$48,$E7,$11,$00,$3E,$2E
	dc.b $00,$0E,$3B,$47,$CD,$88,$57,$C3,$44,$03,$67,$06,$20,$2E,$00,$08
	dc.b $60,$0C,$48,$C7,$2F,$07,$4E,$BA,$FE,$AC,$4A,$80,$58,$4F,$2B,$40
	dc.b $CD,$8A,$4C,$EE,$00,$88,$FF,$F8,$4E,$5E,$4E,$75,$87,$5F,$75,$65
	dc.b $72,$72,$6F,$72,$00,$00,$4E,$56,$FF,$F8,$48,$E7,$11,$00,$2D,$6E
	dc.b $00,$10,$FF,$F8,$2D,$6E,$00,$0C,$FF,$FC,$48,$6E,$FF,$F8,$48,$78
	dc.b $66,$00,$2F,$2E,$00,$08,$4E,$BA,$FB,$06,$2E,$00,$57,$C3,$44,$03
	dc.b $67,$06,$20,$2E,$FF,$FC,$60,$02,$70,$FF,$4F,$EF,$00,$0C,$4C,$EE
	dc.b $00,$88,$FF,$F0,$4E,$5E,$4E,$75,$85,$6C,$73,$65,$65,$6B,$00,$00
	dc.b $4E,$56,$FF,$FC,$48,$E7,$07,$18,$2C,$2E,$00,$0C,$28,$6E,$00,$08
	dc.b $7E,$00,$20,$0C,$67,$18,$59,$8F,$2F,$0C,$4E,$AD,$02,$C2,$2E,$1F
	dc.b $BE,$86,$6F,$0A,$20,$4C,$20,$06,$A0,$20,$20,$0C,$60,$3C,$20,$06
	dc.b $A1,$1E,$2D,$48,$FF,$FC,$4A,$78,$02,$20,$67,$04,$70,$00,$60,$2A
	dc.b $20,$0C,$67,$0E,$20,$4C,$22,$6E,$FF,$FC,$20,$07,$A0,$2E,$20,$4C
	dc.b $A0,$1F,$2A,$2E,$FF,$FC,$28,$45,$D9,$C7,$26,$45,$D7,$C6,$60,$02
	dc.b $42,$1C,$B7,$CC,$62,$FA,$20,$2E,$FF,$FC,$4C,$EE,$18,$E0,$FF,$E8
	dc.b $4E,$5E,$4E,$75,$8F,$5F,$5F,$67,$72,$6F,$77,$46,$69,$6C,$65,$54
	dc.b $61,$62,$6C,$65,$00,$00,$4E,$56,$FF,$FC,$48,$E7,$01,$18,$26,$6E
	dc.b $00,$0C,$2E,$2E,$00,$10,$28,$6E,$00,$08,$2D,$4C,$FF,$FC,$60,$0E
	dc.b $18,$9B,$4A,$1C,$66,$08,$60,$02,$42,$1C,$53,$87,$6C,$FA,$53,$87
	dc.b $6C,$EE,$20,$2E,$FF,$FC,$4C,$EE,$18,$80,$FF,$F0,$4E,$5E,$4E,$75
	dc.b $8D,$5F,$6C,$69,$62,$5F,$43,$73,$74,$72,$6E,$63,$70,$79,$00,$00
	dc.b $4E,$56,$00,$00,$48,$E7,$03,$18,$2C,$2E,$00,$10,$26,$6E,$00,$0C
	dc.b $4A,$AD,$CF,$98,$66,$08,$41,$ED,$CD,$8E,$2B,$48,$CF,$98,$20,$6D
	dc.b $CF,$98,$49,$D0,$60,$0A,$4A,$AC,$00,$04,$67,$10,$49,$EC,$00,$18
	dc.b $20,$6D,$CF,$98,$41,$E8,$00,$78,$B1,$CC,$62,$EA,$2E,$3C,$40,$00
	dc.b $00,$06,$60,$16,$2F,$2E,$00,$14,$2F,$06,$2F,$0B,$20,$6C,$00,$04
	dc.b $4E,$90,$2E,$00,$4F,$EF,$00,$0C,$6C,$0C,$49,$EC,$FF,$E8,$20,$6D
	dc.b $CF,$98,$B1,$CC,$63,$DE,$4A,$AE,$00,$08,$67,$0E,$20,$6D,$CF,$98
	dc.b $B1,$CC,$62,$06,$20,$6E,$00,$08,$20,$8C,$20,$3C,$40,$00,$00,$00
	dc.b $C0,$87,$66,$04,$20,$07,$60,$1E,$3C,$07,$6C,$04,$7E,$00,$60,$08
	dc.b $02,$87,$BF,$FF,$FF,$FF,$42,$46,$48,$C6,$2F,$06,$2F,$07,$4E,$BA
	dc.b $FE,$06,$70,$FF,$50,$4F,$4C,$EE,$18,$C0,$FF,$F0,$4E,$5E,$4E,$75
	dc.b $88,$5F,$66,$61,$63,$63,$65,$73,$73,$00,$00,$00,$4E,$56,$FF,$FC
	dc.b $48,$E7,$17,$18,$28,$6E,$00,$0C,$2A,$2E,$00,$08,$4A,$AD,$CF,$8A
	dc.b $66,$08,$41,$ED,$CE,$46,$2B,$48,$CF,$8A,$7E,$00,$2C,$05,$60,$16
	dc.b $70,$10,$B0,$87,$6E,$0C,$70,$16,$2B,$40,$CD,$8A,$70,$FF,$60,$00
	dc.b $00,$B6,$52,$87,$E2,$86,$70,$01,$C0,$86,$67,$E4,$20,$07,$E5,$40
	dc.b $41,$ED,$CE,$06,$47,$F0,$00,$00,$20,$6D,$CF,$8A,$70,$00,$30,$28
	dc.b $00,$02,$22,$05,$C2,$80,$66,$08,$70,$03,$2D,$40,$FF,$FC,$60,$16
	dc.b $41,$ED,$02,$8A,$B1,$D3,$57,$C3,$44,$03,$67,$04,$70,$01,$60,$02
	dc.b $20,$13,$2D,$40,$FF,$FC,$B9,$FC,$00,$00,$00,$03,$66,$0E,$20,$6D
	dc.b $CF,$8A,$20,$05,$46,$80,$C1,$68,$00,$02,$60,$56,$B9,$FC,$00,$00
	dc.b $00,$05,$66,$36,$20,$6D,$CF,$8A,$8B,$68,$00,$02,$70,$02,$B0,$85
	dc.b $66,$10,$20,$6D,$CF,$8A,$70,$00,$30,$10,$22,$05,$C2,$80,$66,$F2
	dc.b $60,$30,$20,$6D,$CF,$8A,$4A,$50,$67,$28,$20,$05,$46,$80,$C1,$50
	dc.b $2F,$05,$4E,$BA,$00,$36,$58,$4F,$60,$18,$B9,$FC,$00,$00,$00,$01
	dc.b $57,$C3,$44,$03,$67,$08,$41,$ED,$02,$8A,$20,$08,$60,$02,$20,$0C
	dc.b $26,$80,$20,$2E,$FF,$FC,$4C,$EE,$18,$E8,$FF,$E4,$4E,$5E,$4E,$75
	dc.b $86,$73,$69,$67,$6E,$61,$6C,$00,$00,$00,$4E,$56,$00,$00,$48,$E7
	dc.b $07,$08,$2A,$2E,$00,$08,$4A,$AD,$CF,$8A,$66,$08,$41,$ED,$CE,$46
	dc.b $2B,$48,$CF,$8A,$7E,$00,$2C,$05,$60,$0E,$70,$10,$B0,$87,$6E,$04
	dc.b $70,$FF,$60,$4A,$52,$87,$E2,$86,$70,$01,$C0,$86,$67,$EC,$20,$07
	dc.b $E5,$40,$41,$ED,$CE,$06,$28,$70,$00,$00,$20,$0C,$66,$04,$70,$FF
	dc.b $60,$2C,$20,$6D,$CF,$8A,$70,$00,$30,$28,$00,$02,$22,$05,$C2,$80
	dc.b $66,$06,$8B,$50,$70,$FF,$60,$16,$70,$01,$2F,$00,$2F,$05,$4E,$BA
	dc.b $FE,$9C,$2F,$05,$20,$4C,$4E,$90,$70,$00,$4F,$EF,$00,$0C,$4C,$EE
	dc.b $10,$E0,$FF,$F0,$4E,$5E,$4E,$75,$85,$72,$61,$69,$73,$65,$00,$00
	dc.b $4E,$ED,$02,$B2,$4E,$56,$00,$00,$4A,$AD,$CF,$74,$67,$04,$70,$01
	dc.b $60,$02,$70,$00,$1D,$40,$00,$08,$4E,$5E,$4E,$75,$8C,$49,$45,$53
	dc.b $54,$41,$4E,$44,$41,$4C,$4F,$4E,$45,$00,$00,$00,$4E,$56,$FE,$00
	dc.b $48,$E7,$03,$18,$2E,$2E,$00,$0C,$47,$EE,$FF,$00,$42,$6D,$CD,$88
	dc.b $70,$00,$2B,$40,$CD,$8A,$59,$8F,$48,$6E,$FE,$00,$2F,$2E,$00,$10
	dc.b $4E,$AD,$02,$A2,$59,$8F,$48,$6E,$FE,$00,$4E,$AD,$03,$A2,$0C,$87
	dc.b $00,$00,$64,$02,$50,$4F,$66,$1A,$59,$8F,$2F,$0B,$2F,$2E,$00,$08
	dc.b $4E,$AD,$02,$A2,$59,$8F,$2F,$0B,$4E,$AD,$03,$A2,$28,$4B,$50,$4F
	dc.b $60,$04,$28,$6E,$00,$08,$2F,$0C,$2F,$07,$48,$6E,$FE,$00,$4E,$BA
	dc.b $F5,$00,$2C,$00,$2D,$46,$00,$14,$4F,$EF,$00,$0C,$4C,$EE,$18,$C0
	dc.b $FD,$F0,$4E,$5E
;     candidate_code payload[2876..5262) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_20_loc_00000b3c:
	movea.l (a7)+,a0
	lea.l $000C(a7),a7
	jmp (a0)

; CODE 21 SADEV source section
macos_code_CODE_21:
;   source_section_id: macos-code-CODE-21
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 21
;   name: SADEV
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 6794
;   payload_sha256: 927c28db98eadbc5501e570ada73af8afca05964552a831c02051f6e6fa3b687
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:21
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 21 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..2000 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2000..6794 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..2000) size=1960 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[2000..6794) size=4794 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 21 payload[0..6794) sha256=927c28db98eadbc5501e570ada73af8afca05964552a831c02051f6e6fa3b687
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_21_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$08,$E8,$00,$00,$00,$13,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..2000) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_21_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$FF,$94,$48,$E7,$11,$18,$26,$6E,$00,$08,$28,$6E,$00,$10
	dc.b $70,$00,$2D,$40,$FF,$A0,$3D,$53,$FF,$AA,$42,$6E,$FF,$B0,$2D,$6B
	dc.b $00,$02,$FF,$C4,$20,$4B,$5C,$88,$2D,$48,$FF,$A6,$55,$8F,$48,$6E
	dc.b $FF,$94,$70,$00,$1F,$00,$4E,$AD,$03,$4A,$3E,$1F,$70,$10,$C0,$2E
	dc.b $FF,$B2,$72,$00,$12,$00,$4A,$81,$56,$C3,$44,$03,$18,$83,$67,$08
	dc.b $20,$6E,$00,$14,$42,$10,$60,$18,$30,$3C,$80,$00,$C0,$6E,$FF,$BC
	dc.b $72,$00,$32,$00,$4A,$81,$56,$C3,$44,$03,$20,$6E,$00,$14,$10,$83
	dc.b $4A,$2E,$00,$0F,$67,$00,$00,$9C,$20,$6E,$00,$14,$4A,$10,$67,$00
	dc.b $00,$92,$20,$2E,$FF,$B4,$04,$80,$64,$72,$6F,$70,$67,$7C,$04,$80
	dc.b $01,$EE,$F1,$FD,$67,$74,$04,$80,$00,$00,$02,$07,$67,$6C,$04,$80
	dc.b $00,$00,$00,$FE,$67,$64,$04,$80,$00,$00,$01,$02,$67,$5C,$59,$80
	dc.b $67,$58,$04,$80,$00,$00,$07,$F6,$67,$50,$04,$80,$00,$00,$02,$F8
	dc.b $67,$48,$51,$80,$67,$44,$04,$80,$00,$00,$02,$FA,$67,$3C,$04,$80
	dc.b $00,$00,$00,$0C,$67,$34,$5B,$80,$67,$30,$04,$80,$00,$02,$FE,$F7
	dc.b $67,$28,$04,$80,$00,$07,$F2,$02,$67,$20,$04,$80,$00,$00,$0C,$07
	dc.b $67,$18,$04,$80,$01,$F8,$02,$F2,$67,$10,$04,$80,$0B,$0E,$03,$07
	dc.b $67,$08,$04,$80,$00,$FF,$FC,$F6,$66,$06,$18,$BC,$00,$01,$60,$02
	dc.b $42,$14,$30,$07,$4C,$EE,$18,$88,$FF,$84,$4E,$5E,$4E,$75,$8D,$5F
	dc.b $47,$65,$74,$41,$6C,$69,$61,$73,$49,$6E,$66,$6F,$00,$00,$4E,$56
	dc.b $FF,$BA,$48,$E7,$17,$18,$1A,$2E,$00,$17,$1C,$2E,$00,$1B,$26,$6E
	dc.b $00,$28,$28,$6E,$00,$1C,$55,$8F,$3F,$2E,$00,$0A,$2F,$2E,$00,$0C
	dc.b $2F,$2E,$00,$10,$2F,$0C,$30,$3C,$00,$01,$AA,$52,$3E,$1F,$67,$0C
	dc.b $0C,$47,$FF,$D5,$67,$06,$30,$07,$60,$00,$00,$BC,$4A,$05,$66,$1C
	dc.b $4A,$06,$67,$18,$2F,$0B,$2F,$2E,$00,$20,$70,$01,$2F,$00,$2F,$0C
	dc.b $4E,$BA,$FE,$7E,$3E,$00,$4F,$EF,$00,$10,$60,$54,$41,$EE,$FF,$BA
	dc.b $22,$4C,$70,$10,$20,$D9,$51,$C8,$FF,$FC,$30,$D9,$55,$8F,$2F,$0C
	dc.b $70,$01,$1F,$00,$2F,$2E,$00,$20,$2F,$0B,$70,$0C,$A8,$23,$3E,$1F
	dc.b $4A,$13,$67,$2C,$0C,$47,$FF,$D5,$66,$26,$30,$2E,$FF,$BA,$B0,$54
	dc.b $66,$1E,$20,$2E,$FF,$BC,$B0,$AC,$00,$02,$66,$14,$55,$8F,$48,$6E
	dc.b $FF,$C0,$48,$6C,$00,$06,$4E,$AD,$02,$9A,$4A,$5F,$66,$02,$7E,$F7
	dc.b $4A,$47,$67,$0A,$0C,$47,$FF,$D5,$67,$04,$30,$07,$60,$38,$0C,$47
	dc.b $FF,$D5,$66,$08,$4A,$06,$66,$04,$70,$88,$60,$2A,$4A,$05,$66,$0E
	dc.b $4A,$06,$67,$0A,$4A,$13,$67,$06,$20,$6E,$00,$20,$42,$10,$76,$01
	dc.b $20,$6E,$00,$24,$4A,$10,$66,$06,$4A,$13,$66,$02,$76,$00,$20,$6E
	dc.b $00,$24,$10,$83,$30,$07,$4C,$EE,$18,$E8,$FF,$A2,$4E,$5E,$4E,$75
	dc.b $91,$5F,$52,$65,$73,$6F,$6C,$76,$65,$46,$69,$6C,$65,$41,$6C,$69
	dc.b $61,$73,$00,$00,$4E,$56,$FF,$6E,$48,$E7,$1F,$18,$28,$2E,$00,$0C
	dc.b $3A,$2E,$00,$0A,$4A,$AE,$00,$10,$67,$08,$20,$6E,$00,$10,$4A,$10
	dc.b $66,$4A,$20,$6E,$00,$1C,$42,$10,$20,$6E,$00,$20,$42,$10,$20,$6E
	dc.b $00,$24,$42,$10,$55,$8F,$3F,$05,$2F,$04,$2F,$2E,$00,$10,$2F,$2E
	dc.b $00,$18,$30,$3C,$00,$01,$AA,$52,$3E,$1F,$66,$1A,$2F,$2E,$00,$24
	dc.b $2F,$2E,$00,$1C,$70,$00,$2F,$00,$2F,$2E,$00,$18,$4E,$BA,$FD,$62
	dc.b $3E,$00,$4F,$EF,$00,$10,$30,$07,$60,$00,$02,$46,$42,$47,$70,$00
	dc.b $2D,$40,$FF,$72,$20,$6E,$00,$10,$1D,$50,$FF,$79,$28,$48,$41,$EE
	dc.b $FF,$7A,$2D,$48,$FF,$FC,$42,$10,$20,$6E,$00,$20,$42,$10,$42,$06
	dc.b $60,$00,$01,$FC,$26,$4C,$52,$4B,$60,$02,$52,$4B,$70,$00,$10,$14
	dc.b $D0,$8C,$B0,$8B,$63,$0A,$70,$00,$10,$13,$0C,$40,$00,$3A,$67,$EA
	dc.b $53,$4B,$B9,$CB,$67,$10,$1D,$53,$FF,$77,$70,$00,$10,$14,$22,$0B
	dc.b $92,$8C,$90,$81,$16,$80,$70,$00,$10,$13,$0C,$00,$00,$01,$53,$C3
	dc.b $44,$03,$67,$04,$70,$00,$60,$1A,$70,$00,$10,$13,$2F,$00,$70,$3A
	dc.b $2F,$00,$22,$0B,$52,$81,$2F,$01,$4E,$BA,$04,$96,$4A,$80,$4F,$EF
	dc.b $00,$0C,$2D,$40,$FF,$72,$B9,$CB,$67,$06,$16,$AE,$FF,$77,$60,$48
	dc.b $70,$00,$10,$06,$4A,$80,$66,$40,$70,$00,$10,$2E,$FF,$79,$D0,$AE
	dc.b $00,$10,$B0,$AE,$FF,$72,$66,$30,$55,$8F,$3F,$05,$2F,$04,$2F,$0C
	dc.b $2F,$2E,$00,$18,$30,$3C,$00,$01,$AA,$52,$3E,$1F,$57,$C3,$44,$03
	dc.b $20,$6E,$00,$1C,$10,$83,$20,$6E,$00,$24,$42,$10,$20,$6E,$00,$20
	dc.b $42,$10,$30,$07,$60,$00,$01,$6A,$4A,$AE,$FF,$72,$67,$22,$1D,$54
	dc.b $FF,$78,$20,$2E,$FF,$72,$90,$8C,$53,$80,$18,$80,$70,$00,$10,$2E
	dc.b $FF,$78,$72,$00,$12,$14,$90,$41,$53,$40,$20,$6E,$FF,$72,$10,$80
	dc.b $70,$00,$10,$06,$4A,$80,$66,$3E,$B9,$CB,$66,$3A,$4A,$AE,$FF,$72
	dc.b $67,$34,$70,$00,$10,$14,$52,$40,$48,$C0,$2F,$00,$2F,$0C,$48,$6E
	dc.b $FF,$7A,$4E,$BA,$04,$22,$10,$2E,$FF,$7A,$52,$2E,$FF,$7A,$41,$EE
	dc.b $FF,$7A,$70,$00,$10,$2E,$FF,$7A,$D0,$88,$20,$40,$10,$BC,$00,$3A
	dc.b $4F,$EF,$00,$0C,$60,$32,$70,$00,$10,$14,$52,$40,$48,$C0,$2F,$00
	dc.b $2F,$0C,$2F,$2E,$FF,$FC,$4E,$BA,$03,$EE,$41,$EE,$FF,$7A,$B1,$EE
	dc.b $FF,$FC,$4F,$EF,$00,$0C,$67,$10,$20,$6E,$FF,$FC,$10,$10,$52,$00
	dc.b $D1,$2E,$FF,$7A,$10,$BC,$00,$3A,$2F,$2E,$00,$24,$2F,$2E,$00,$20
	dc.b $2F,$2E,$00,$1C,$2F,$2E,$00,$18,$4A,$AE,$FF,$72,$57,$C3,$44,$03
	dc.b $48,$83,$48,$C3,$2F,$03,$70,$00,$10,$2E,$00,$17,$2F,$00,$48,$6E
	dc.b $FF,$7A,$2F,$04,$48,$C5,$2F,$05,$4E,$BA,$FC,$D4,$3E,$00,$18,$BC
	dc.b $00,$3A,$4A,$47,$4F,$EF,$00,$24,$67,$06,$0C,$47,$FF,$D5,$66,$64
	dc.b $28,$6E,$FF,$72,$20,$0C,$67,$52,$20,$6E,$00,$18,$3A,$10,$28,$28
	dc.b $00,$02,$70,$00,$10,$28,$00,$06,$52,$40,$48,$C0,$2F,$00,$48,$68
	dc.b $00,$06,$41,$EE,$FF,$7A,$52,$48,$2F,$08,$4E,$BA,$03,$5A,$41,$EE
	dc.b $FF,$7A,$52,$48,$2D,$48,$FF,$6E,$10,$10,$52,$00,$1D,$40,$FF,$7A
	dc.b $10,$BC,$00,$3A,$41,$EE,$FF,$7A,$70,$00,$10,$2E,$FF,$7A,$D0,$88
	dc.b $52,$80,$2D,$40,$FF,$FC,$4F,$EF,$00,$0C,$10,$06,$52,$06,$20,$0C
	dc.b $66,$00,$FE,$02,$4A,$47,$67,$0E,$4A,$AE,$FF,$72,$67,$08,$20,$6E
	dc.b $FF,$72,$10,$BC,$00,$3A,$20,$6E,$00,$10,$10,$AE,$FF,$79,$30,$07
	dc.b $4C,$EE,$18,$F8,$FF,$52,$4E,$5E,$4E,$75,$94,$52,$65,$73,$6F,$6C
	dc.b $76,$65,$46,$6F,$6C,$64,$65,$72,$41,$6C,$69,$61,$73,$65,$73,$00
	dc.b $00,$00,$4E,$56,$FF,$BA,$48,$E7,$07,$18,$2A,$2E,$00,$0C,$3C,$2E
	dc.b $00,$0A,$26,$6E,$00,$20,$28,$6E,$00,$14,$55,$8F,$3F,$06,$2F,$05
	dc.b $2F,$2E,$00,$10,$2F,$0C,$30,$3C,$00,$01,$AA,$52,$3E,$1F,$30,$07
	dc.b $04,$40,$FF,$D5,$67,$62,$04,$40,$00,$2B,$66,$6C,$41,$EE,$FF,$BA
	dc.b $22,$4C,$70,$10,$20,$D9,$51,$C8,$FF,$FC,$30,$D9,$55,$8F,$2F,$0C
	dc.b $70,$01,$1F,$00,$2F,$2E,$00,$18,$2F,$0B,$70,$0C,$A8,$23,$3E,$1F
	dc.b $4A,$13,$67,$2C,$0C,$47,$FF,$D5,$66,$26,$30,$2E,$FF,$BA,$B0,$54
	dc.b $66,$1E,$20,$2E,$FF,$BC,$B0,$AC,$00,$02,$66,$14,$55,$8F,$48,$6E
	dc.b $FF,$C0,$48,$6C,$00,$06,$4E,$AD,$02,$9A,$4A,$5F,$66,$02,$7E,$F7
	dc.b $20,$6E,$00,$1C,$10,$93,$60,$34,$42,$13,$20,$6E,$00,$1C,$42,$10
	dc.b $20,$6E,$00,$18,$42,$10,$60,$24,$2F,$0B,$2F,$2E,$00,$1C,$2F,$2E
	dc.b $00,$18,$2F,$0C,$70,$01,$2F,$00,$2F,$2E,$00,$10,$2F,$05,$48,$C6
	dc.b $2F,$06,$4E,$BA,$FC,$70,$3E,$00,$4F,$EF,$00,$20,$30,$07,$4C,$EE
	dc.b $18,$E0,$FF,$A6,$4E,$5E,$4E,$75,$92,$4D,$61,$6B,$65,$52,$65,$73
	dc.b $6F,$6C,$76,$65,$64,$46,$53,$53,$70,$65,$63,$00,$00,$00,$4E,$56
	dc.b $FF,$54,$48,$E7,$07,$18,$47,$EE,$FF,$54,$28,$6E,$00,$4E,$70,$00
	dc.b $10,$2E,$00,$0E,$52,$40,$48,$C0,$2F,$00,$48,$6E,$00,$0E,$2F,$0C
	dc.b $4E,$BA,$01,$D4,$70,$00,$10,$2E,$00,$0E,$52,$40,$48,$C0,$2F,$00
	dc.b $48,$6E,$00,$0E,$2F,$0B,$4E,$BA,$01,$BE,$3D,$6E,$00,$08,$FF,$AA
	dc.b $70,$00,$2D,$40,$FF,$A0,$3D,$7C,$FF,$FF,$FF,$B0,$2D,$4B,$FF,$A6
	dc.b $2D,$6E,$00,$0A,$FF,$C4,$4F,$EF,$00,$18,$55,$8F,$48,$6E,$FF,$94
	dc.b $70,$00,$1F,$00,$4E,$AD,$03,$4A,$3A,$1F,$2D,$6E,$FF,$F8,$FF,$C4
	dc.b $4A,$45,$67,$04,$30,$05,$60,$68,$10,$13,$52,$00,$1E,$00,$10,$14
	dc.b $48,$80,$72,$00,$12,$07,$3C,$01,$DC,$40,$70,$00,$30,$06,$0C,$40
	dc.b $00,$FF,$63,$04,$70,$DB,$60,$48,$10,$14,$48,$80,$48,$C0,$2F,$00
	dc.b $20,$0C,$52,$80,$2F,$00,$70,$00,$10,$07,$D0,$8C,$52,$80,$2F,$00
	dc.b $4E,$BA,$01,$9A,$70,$00,$10,$07,$2F,$00,$2F,$0B,$2F,$0C,$4E,$BA
	dc.b $01,$36,$70,$00,$10,$07,$D0,$8C,$20,$40,$10,$BC,$00,$3A,$18,$86
	dc.b $4F,$EF,$00,$18,$70,$01,$B0,$AE,$FF,$F8,$66,$00,$FF,$7E,$70,$00
	dc.b $4C,$EE,$18,$E0,$FF,$40,$4E,$5E,$4E,$75,$8C,$5F,$46,$53,$53,$70
	dc.b $65,$63,$32,$50,$61,$74,$68,$00,$00,$00,$4E,$56,$FF,$B2,$48,$E7
	dc.b $13,$18,$26,$6E,$00,$10,$28,$6E,$00,$14,$42,$47,$55,$8F,$70,$00
	dc.b $2F,$00,$48,$6E,$FF,$B6,$48,$6E,$FF,$B2,$4E,$AD,$03,$6A,$48,$6E
	dc.b $FF,$FE,$48,$6E,$FF,$FF,$2F,$2E,$00,$0C,$48,$6E,$FF,$B8,$2F,$0C
	dc.b $2F,$2E,$FF,$B2,$30,$2E,$FF,$B6,$48,$C0,$2F,$00,$4E,$BA,$FD,$D4
	dc.b $3C,$00,$20,$6E,$00,$08,$10,$AE,$FF,$FF,$4A,$46,$4F,$EF,$00,$1E
	dc.b $67,$06,$0C,$46,$FF,$D5,$66,$36,$4A,$2E,$FF,$FF,$67,$1A,$2F,$0B
	dc.b $41,$EE,$FF,$FE,$70,$22,$3F,$20,$51,$C8,$FF,$FC,$4E,$BA,$FE,$90
	dc.b $3E,$00,$4F,$EF,$00,$4A,$60,$16,$70,$00,$10,$14,$52,$40,$48,$C0
	dc.b $2F,$00,$2F,$0C,$2F,$0B,$4E,$BA,$00,$6E,$4F,$EF,$00,$0C,$4A,$47
	dc.b $57,$C3,$44,$03,$67,$04,$30,$06,$60,$02,$30,$07,$3D,$40,$00,$18
	dc.b $4C,$EE,$18,$C8,$FF,$9E,$4E,$5E
;     candidate_code payload[2000..6794) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_21_loc_000007d0:
	movea.l (a7)+,a0
	lea.l $0010(a7),a7
	jmp (a0)

; CODE 22 SANELIB source section
macos_code_CODE_22:
;   source_section_id: macos-code-CODE-22
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: covered_placeholder
;   resource_type: CODE
;   id: 22
;   name: SANELIB
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 96
;   payload_sha256: 6929f16d82666fe0f31993c30f2750798bf934a0dcddf3c6eb0adc2c552484f8
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:22
;   listing: kind=structured_placeholder available=False reason=no candidate preview range; classifier deferred byte-entry evidence: missing_m68k_movea_l_stack_to_a0_entry
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 22 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=unknown span=40..96 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     deferred payload[40..96) size=56 entrypoint=False status=deferred parser_use=deferred_only evidence=missing_m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.byte_entry_rule.unknown
;   byte_preserving_placeholder: CODE 22 payload[0..96) sha256=6929f16d82666fe0f31993c30f2750798bf934a0dcddf3c6eb0adc2c552484f8
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_22_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$09,$80,$00,$00,$00,$01,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     deferred payload[40..96) status=deferred parser_use=deferred_only evidence=missing_m68k_movea_l_stack_to_a0_entry
macos_code_CODE_22_deferred_00000028:
	dc.b $4C,$D7,$03,$01,$2F,$00,$48,$6F,$00,$10,$48,$E7,$00,$C0,$70,$03
	dc.b $3F,$00,$A9,$EE,$20,$57,$DE,$FC,$00,$14,$4E,$D0,$4C,$EF,$03,$03
	dc.b $00,$04,$48,$E7,$C0,$C0,$70,$02,$60,$E6,$4C,$EF,$03,$03,$00,$04
	dc.b $48,$E7,$C0,$C0,$70,$04,$60,$D8

; CODE 23 STDCLIB source section
macos_code_CODE_23:
;   source_section_id: macos-code-CODE-23
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: covered_placeholder
;   resource_type: CODE
;   id: 23
;   name: STDCLIB
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 126
;   payload_sha256: ce2eaab2bd782055c6aaaefc223f2e72d4f746e25a05cc8b3599836ecbd41969
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:23
;   listing: kind=structured_placeholder available=False reason=no candidate preview range; classifier deferred byte-entry evidence: missing_m68k_movea_l_stack_to_a0_entry
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 23 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=unknown span=40..126 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     deferred payload[40..126) size=86 entrypoint=False status=deferred parser_use=deferred_only evidence=missing_m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.byte_entry_rule.unknown
;   byte_preserving_placeholder: CODE 23 payload[0..126) sha256=ce2eaab2bd782055c6aaaefc223f2e72d4f746e25a05cc8b3599836ecbd41969
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_23_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$09,$88,$00,$00,$00,$01,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     deferred payload[40..126) status=deferred parser_use=deferred_only evidence=missing_m68k_movea_l_stack_to_a0_entry
macos_code_CODE_23_deferred_00000028:
	dc.b $4C,$EF,$03,$00,$00,$04,$20,$08,$2F,$02,$22,$2F,$00,$10,$0C,$81
	dc.b $00,$00,$00,$11,$6D,$2E,$24,$09,$B1,$02,$E2,$0A,$65,$26,$08,$00
	dc.b $00,$00,$67,$04,$10,$D9,$53,$81,$24,$01,$E8,$8A,$53,$82,$20,$D9
	dc.b $20,$D9,$20,$D9,$20,$D9,$53,$82,$64,$F4,$02,$81,$00,$00,$00,$0F
	dc.b $60,$02,$10,$D9,$53,$81,$64,$FA,$24,$1F,$4E,$75,$86,$6D,$65,$6D
	dc.b $63,$70,$79,$00,$00,$00

; CODE 24 STDIO source section
macos_code_CODE_24:
;   source_section_id: macos-code-CODE-24
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 24
;   name: STDIO
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 4970
;   payload_sha256: f98dfc823a565d6502fa4ac1feb7b616b397ba9a918ce2c5f47b274e99a9026a
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:24
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 24 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..2950 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2950..4970 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..2950) size=2910 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[2950..4970) size=2020 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 24 payload[0..4970) sha256=f98dfc823a565d6502fa4ac1feb7b616b397ba9a918ce2c5f47b274e99a9026a
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_24_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$09,$90,$00,$00,$00,$0D,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..2950) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_24_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$00,$00,$2F,$0C,$49,$ED,$D0,$B2,$60,$0C,$2F,$0C,$4E,$BA
	dc.b $02,$86,$58,$4F,$49,$EC,$00,$16,$B9,$ED,$D0,$AE,$65,$EE,$28,$6E
	dc.b $FF,$FC,$4E,$5E,$4E,$75,$89,$5F,$5F,$63,$6C,$65,$61,$6E,$75,$70
	dc.b $00,$00,$4E,$56,$FF,$FC,$48,$E7,$13,$08,$28,$6E,$00,$08,$41,$ED
	dc.b $09,$B2,$22,$6D,$CF,$8E,$23,$48,$00,$08,$2C,$2D,$CD,$8A,$3E,$2D
	dc.b $CD,$88,$70,$00,$30,$2C,$00,$12,$72,$04,$C2,$40,$67,$10,$42,$6C
	dc.b $00,$10,$41,$ED,$D2,$6A,$29,$48,$00,$08,$60,$00,$00,$B2,$70,$00
	dc.b $30,$2C,$00,$10,$4A,$80,$66,$44,$70,$00,$29,$40,$00,$08,$72,$00
	dc.b $32,$2C,$00,$12,$74,$40,$C4,$41,$67,$08,$39,$7C,$00,$64,$00,$10
	dc.b $60,$2A,$48,$6E,$FF,$FC,$48,$78,$66,$03,$70,$00,$30,$2C,$00,$14
	dc.b $2F,$00,$4E,$AD,$08,$4A,$4A,$80,$4F,$EF,$00,$0C,$6D,$08,$39,$6E
	dc.b $FF,$FE,$00,$10,$60,$06,$39,$7C,$04,$00,$00,$10,$4A,$AC,$00,$08
	dc.b $66,$5C,$72,$00,$32,$2C,$00,$10,$20,$01,$A1,$1E,$29,$48,$00,$08
	dc.b $66,$38,$70,$00,$30,$2C,$00,$10,$0C,$40,$00,$64,$63,$2C,$70,$00
	dc.b $30,$2C,$00,$10,$0C,$40,$04,$00,$52,$C3,$44,$03,$67,$08,$20,$3C
	dc.b $00,$00,$04,$00,$60,$02,$70,$64,$39,$40,$00,$10,$72,$00,$32,$2C
	dc.b $00,$10,$20,$01,$A1,$1E,$29,$48,$00,$08,$4A,$AC,$00,$08,$67,$08
	dc.b $00,$6C,$00,$08,$00,$12,$60,$06,$00,$6C,$00,$04,$00,$12,$70,$00
	dc.b $30,$2C,$00,$10,$D0,$AC,$00,$08,$29,$40,$00,$0C,$29,$6C,$00,$08
	dc.b $00,$04,$70,$00,$2F,$00,$48,$78,$66,$02,$72,$00,$32,$2C,$00,$14
	dc.b $2F,$01,$4E,$AD,$08,$4A,$4A,$80,$4F,$EF,$00,$0C,$6D,$06,$00,$6C
	dc.b $01,$00,$00,$12,$2B,$46,$CD,$8A,$3B,$47,$CD,$88,$4C,$EE,$10,$C8
	dc.b $FF,$EC,$4E,$5E,$4E,$75,$88,$5F,$66,$69,$6E,$64,$62,$75,$66,$00
	dc.b $00,$00,$4E,$56,$00,$00,$48,$E7,$00,$18,$26,$6E,$00,$08,$70,$00
	dc.b $30,$2B,$00,$12,$32,$3C,$00,$81,$C2,$40,$70,$00,$30,$01,$4A,$80
	dc.b $66,$06,$70,$FF,$60,$00,$00,$EC,$00,$6B,$00,$01,$00,$12,$70,$00
	dc.b $30,$2B,$00,$12,$72,$10,$C2,$40,$67,$06,$70,$FF,$60,$00,$00,$D4
	dc.b $4A,$AB,$00,$08,$66,$08,$2F,$0B,$4E,$BA,$FE,$78,$58,$4F,$70,$00
	dc.b $30,$2B,$00,$12,$32,$3C,$01,$00,$C2,$40,$67,$3C,$49,$ED,$D0,$B2
	dc.b $60,$30,$70,$00,$30,$2C,$00,$12,$32,$3C,$01,$02,$C2,$40,$70,$00
	dc.b $30,$01,$0C,$80,$00,$00,$01,$02,$66,$14,$2F,$0C,$4E,$BA,$01,$3E
	dc.b $72,$FF,$B2,$80,$58,$4F,$66,$06,$70,$FF,$60,$00,$00,$86,$49,$EC
	dc.b $00,$16,$B9,$ED,$D0,$AE,$65,$CA,$27,$6B,$00,$08,$00,$04,$70,$00
	dc.b $30,$2B,$00,$12,$72,$04,$C2,$40,$67,$04,$70,$01,$60,$08,$70,$00
	dc.b $30,$2B,$00,$10,$4A,$80,$2F,$00,$2F,$2B,$00,$08,$70,$00,$30,$2B
	dc.b $00,$14,$2F,$00,$4E,$AD,$08,$3A,$26,$80,$53,$93,$4A,$93,$4F,$EF
	dc.b $00,$0C,$6D,$10,$20,$6B,$00,$04,$52,$AB,$00,$04,$70,$00,$10,$10
	dc.b $4A,$80,$60,$2E,$70,$FF,$B0,$93,$66,$1C,$00,$6B,$00,$10,$00,$12
	dc.b $70,$00,$30,$2B,$00,$12,$32,$3C,$00,$80,$C2,$40,$67,$0E,$02,$6B
	dc.b $FF,$FE,$00,$12,$60,$06,$00,$6B,$00,$20,$00,$12,$70,$00,$26,$80
	dc.b $70,$FF,$4C,$EE,$18,$00,$FF,$F8,$4E,$5E,$4E,$75,$87,$5F,$66,$69
	dc.b $6C,$62,$75,$66,$00,$00,$4E,$56,$00,$00,$48,$E7,$01,$08,$28,$6E
	dc.b $00,$08,$7E,$FF,$20,$0C,$66,$04,$70,$FF,$60,$6C,$70,$00,$30,$2C
	dc.b $00,$12,$32,$3C,$00,$83,$C2,$40,$67,$36,$70,$00,$30,$2C,$00,$12
	dc.b $72,$04,$C2,$40,$67,$04,$70,$00,$60,$0A,$2F,$0C,$4E,$BA,$00,$5E
	dc.b $4A,$80,$58,$4F,$2E,$00,$70,$00,$30,$2C,$00,$14,$2F,$00,$4E,$AD
	dc.b $08,$32,$4A,$80,$58,$4F,$6C,$08,$7E,$FF,$70,$02,$2B,$40,$CD,$8A
	dc.b $70,$00,$30,$2C,$00,$12,$72,$08,$C2,$40,$67,$0C,$20,$6C,$00,$08
	dc.b $A0,$1F,$70,$00,$29,$40,$00,$08,$42,$6C,$00,$12,$70,$00,$28,$80
	dc.b $29,$6C,$00,$08,$00,$04,$20,$07,$4C,$EE,$10,$80,$FF,$F8,$4E,$5E
	dc.b $4E,$75,$86,$66,$63,$6C,$6F,$73,$65,$00,$00,$00,$4E,$56,$00,$00
	dc.b $48,$E7,$11,$18,$28,$6E,$00,$08,$7E,$00,$20,$0C,$66,$3A,$47,$ED
	dc.b $D0,$B2,$60,$1E,$70,$00,$30,$2B,$00,$12,$72,$02,$C2,$40,$67,$0E
	dc.b $2F,$0B,$4E,$BA,$FF,$D8,$4A,$80,$58,$4F,$67,$02,$7E,$01,$47,$EB
	dc.b $00,$16,$B7,$ED,$D0,$AE,$65,$DC,$4A,$87,$57,$C3,$44,$03,$67,$04
	dc.b $70,$00,$60,$6A,$70,$FF,$60,$66,$70,$00,$30,$2C,$00,$12,$72,$02
	dc.b $C2,$40,$66,$20,$70,$00,$28,$80,$70,$00,$60,$52,$2E,$2C,$00,$04
	dc.b $2F,$0C,$4E,$BA,$01,$D0,$72,$FF,$B2,$80,$58,$4F,$66,$06,$BE,$AC
	dc.b $00,$04,$67,$28,$70,$00,$30,$2C,$00,$12,$72,$04,$C2,$40,$66,$1C
	dc.b $70,$00,$30,$2C,$00,$12,$72,$02,$C2,$40,$67,$10,$4A,$AC,$00,$08
	dc.b $67,$0A,$20,$2C,$00,$04,$B0,$AC,$00,$08,$62,$C0,$70,$00,$30,$2C
	dc.b $00,$12,$72,$20,$C2,$40,$67,$04,$70,$FF,$60,$02,$70,$00,$4C,$EE
	dc.b $18,$88,$FF,$F0,$4E,$5E,$4E,$75,$86,$66,$66,$6C,$75,$73,$68,$00
	dc.b $00,$00,$4E,$56,$FF,$FE,$48,$E7,$11,$08,$1E,$2E,$00,$0B,$28,$6E
	dc.b $00,$0C,$70,$00,$30,$2C,$00,$12,$72,$52,$C2,$40,$70,$00,$30,$01
	dc.b $72,$42,$B2,$80,$66,$4C,$20,$2C,$00,$04,$B0,$AC,$00,$0C,$64,$00
	dc.b $00,$8E,$20,$6C,$00,$04,$52,$AC,$00,$04,$10,$87,$70,$00,$10,$07
	dc.b $0C,$40,$00,$0D,$67,$0A,$70,$00,$10,$07,$4A,$80,$60,$00,$01,$12
	dc.b $2F,$0C,$4E,$BA,$01,$20,$72,$FF,$B2,$80,$57,$C3,$44,$03,$58,$4F
	dc.b $67,$04,$70,$FF,$60,$06,$70,$00,$10,$07,$4A,$80,$48,$C0,$60,$00
	dc.b $00,$F0,$70,$00,$30,$2C,$00,$12,$72,$16,$C2,$40,$70,$00,$30,$01
	dc.b $72,$06,$B2,$80,$66,$38,$1D,$47,$FF,$FF,$70,$01,$2F,$00,$48,$6E
	dc.b $FF,$FF,$72,$00,$32,$2C,$00,$14,$2F,$01,$4E,$AD,$08,$42,$72,$01
	dc.b $B2,$80,$4F,$EF,$00,$0C,$66,$0A,$70,$00,$10,$07,$4A,$80,$60,$00
	dc.b $00,$B0,$00,$6C,$00,$20,$00,$12,$70,$FF,$60,$00,$00,$A4,$76,$01
	dc.b $70,$00,$30,$2C,$00,$12,$72,$12,$C2,$40,$70,$00,$30,$01,$72,$02
	dc.b $B2,$80,$66,$22,$4A,$AC,$00,$08,$67,$1C,$20,$2C,$00,$04,$B0,$AC
	dc.b $00,$08,$66,$10,$4A,$94,$66,$0C,$70,$00,$30,$2C,$00,$12,$72,$44
	dc.b $C2,$40,$67,$02,$76,$00,$4A,$03,$67,$0C,$2F,$0C,$4E,$BA,$01,$4A
	dc.b $4A,$80,$58,$4F,$60,$02,$70,$00,$67,$04,$70,$FF,$60,$52,$2F,$0C
	dc.b $4E,$BA,$00,$62,$72,$FF,$B2,$80,$58,$4F,$67,$2C,$53,$94,$4A,$94
	dc.b $5C,$C3,$44,$03,$67,$12,$20,$6C,$00,$04,$52,$AC,$00,$04,$10,$87
	dc.b $70,$00,$10,$07,$4A,$80,$60,$10,$2F,$0C,$70,$00,$10,$07,$2F,$00
	dc.b $4E,$BA,$FE,$C0,$4A,$80,$50,$4F,$70,$00,$30,$2C,$00,$12,$72,$20
	dc.b $C2,$40,$67,$04,$70,$FF,$60,$06,$70,$00,$10,$07,$4A,$80,$48,$C0
	dc.b $4C,$EE,$10,$88,$FF,$F2,$4E,$5E,$4E,$75,$87,$5F,$66,$6C,$73,$62
	dc.b $75,$66,$00,$00,$4E,$56,$FF,$FC,$48,$E7,$17,$18,$28,$6E,$00,$08
	dc.b $2D,$6C,$00,$04,$FF,$FC,$2A,$14,$26,$6C,$00,$08,$2E,$2C,$00,$04
	dc.b $9E,$8B,$29,$4B,$00,$04,$70,$00,$30,$2C,$00,$12,$72,$44,$C2,$40
	dc.b $67,$04,$70,$00,$60,$08,$70,$00,$30,$2C,$00,$10,$4A,$80,$72,$00
	dc.b $32,$00,$28,$81,$20,$2C,$00,$0C,$90,$AC,$00,$04,$4A,$94,$5D,$C3
	dc.b $44,$03,$67,$04,$72,$00,$60,$02,$22,$14,$B2,$80,$6F,$08,$2F,$0C
	dc.b $4E,$BA,$01,$28,$58,$4F,$4A,$87,$6F,$56,$2F,$07,$2F,$0B,$70,$00
	dc.b $30,$2C,$00,$14,$2F,$00,$4E,$AD,$08,$42,$2C,$00,$BC,$87,$4F,$EF
	dc.b $00,$0C,$67,$3C,$00,$6C,$00,$20,$00,$12,$4A,$86,$6E,$0A,$29,$6E
	dc.b $FF,$FC,$00,$04,$28,$85,$60,$24,$20,$07,$90,$86,$28,$80,$D0,$AC
	dc.b $00,$08,$29,$40,$00,$04,$2F,$14,$20,$06,$D0,$AC,$00,$08,$2F,$00
	dc.b $2F,$2C,$00,$08,$4E,$AD,$09,$12,$4F,$EF,$00,$0C,$70,$FF,$60,$02
	dc.b $70,$00,$4C,$EE,$18,$E8,$FF,$E4,$4E,$5E,$4E,$75,$88,$5F,$78,$66
	dc.b $6C,$73,$62,$75,$66,$00,$00,$00,$4E,$56,$00,$00,$48,$E7,$10,$08
	dc.b $28,$6E,$00,$08,$70,$00,$30,$2C,$00,$12,$72,$12,$C2,$40,$70,$00
	dc.b $30,$01,$72,$02,$B2,$80,$67,$2E,$70,$00,$30,$2C,$00,$12,$32,$3C
	dc.b $00,$82,$C2,$40,$66,$0A,$00,$6C,$00,$20,$00,$12,$70,$FF,$60,$66
	dc.b $70,$00,$30,$2C,$00,$12,$72,$EF,$C2,$40,$70,$00,$30,$01,$72,$02
	dc.b $82,$40,$39,$41,$00,$12,$4A,$AC,$00,$04,$66,$08,$2F,$0C,$4E,$BA
	dc.b $F9,$A2,$58,$4F,$20,$2C,$00,$04,$B0,$AC,$00,$08,$66,$36,$70,$00
	dc.b $30,$2C,$00,$12,$72,$44,$C2,$40,$66,$2A,$70,$00,$30,$2C,$00,$10
	dc.b $28,$80,$20,$2C,$00,$0C,$90,$AC,$00,$04,$4A,$94,$5D,$C3,$44,$03
	dc.b $67,$04,$72,$00,$60,$02,$22,$14,$B2,$80,$6F,$08,$2F,$0C,$4E,$BA
	dc.b $00,$1A,$58,$4F,$70,$00,$4C,$EE,$10,$08,$FF,$F8,$4E,$5E,$4E,$75
	dc.b $87,$5F,$77,$72,$74,$63,$68,$6B,$00,$00,$4E,$56,$00,$00,$48,$E7
	dc.b $01,$08,$28,$6E,$00,$08,$2E,$2C,$00,$0C,$9E,$AC,$00,$04,$4A,$87
	dc.b $6C,$08,$29,$6C,$00,$0C,$00,$04,$60,$06,$BE,$94,$6C,$02,$28,$87
	dc.b $4C,$EE,$10,$80,$FF,$F8,$4E,$5E,$4E,$75,$88,$5F,$62,$75,$66,$73
	dc.b $79,$6E,$63,$00,$00,$00,$4E,$56,$00,$00,$48,$E7,$1F,$08,$28,$2E
	dc.b $00,$10,$2A,$2E,$00,$0C,$28,$6E,$00,$08,$02,$6C,$FF,$EF,$00,$12
	dc.b $70,$00,$30,$2C,$00,$12,$4A,$80,$08,$00,$00,$00,$67,$00,$00,$A8
	dc.b $70,$02,$B0,$84,$6F,$6A,$4A,$AC,$00,$08,$67,$64,$70,$00,$30,$2C
	dc.b $00,$12,$72,$04,$C2,$40,$66,$58,$2E,$14,$2C,$05,$4A,$84,$66,$20
	dc.b $70,$01,$2F,$00,$72,$00,$2F,$01,$74,$00,$34,$2C,$00,$14,$2F,$02
	dc.b $4E,$AD,$08,$62,$22,$07,$92,$80,$DC,$81,$4F,$EF,$00,$0C,$60,$02
	dc.b $9A,$87,$70,$00,$30,$2C,$00,$12,$32,$3C,$00,$80,$C2,$40,$66,$20
	dc.b $4A,$87,$6F,$1C,$BE,$86,$6D,$18,$20,$2C,$00,$08,$90,$AC,$00,$04
	dc.b $B0,$86,$6E,$0C,$DD,$AC,$00,$04,$9D,$94,$70,$00,$60,$00,$00,$92
	dc.b $70,$00,$30,$2C,$00,$12,$32,$3C,$00,$80,$C2,$40,$67,$0C,$29,$6C
	dc.b $00,$08,$00,$04,$02,$6C,$FF,$FE,$00,$12,$2F,$04,$2F,$05,$70,$00
	dc.b $30,$2C,$00,$14,$2F,$00,$4E,$AD,$08,$62,$2C,$00,$70,$00,$28,$80
	dc.b $4F,$EF,$00,$0C,$60,$4A,$70,$00,$30,$2C,$00,$12,$32,$3C,$00,$82
	dc.b $C2,$40,$67,$3C,$2F,$0C,$4E,$BA,$FB,$24,$70,$00,$30,$2C,$00,$12
	dc.b $32,$3C,$00,$80,$C2,$40,$58,$4F,$67,$10,$70,$00,$28,$80,$02,$6C
	dc.b $FF,$FD,$00,$12,$29,$6C,$00,$08,$00,$04,$2F,$04,$2F,$05,$70,$00
	dc.b $30,$2C,$00,$14,$2F,$00,$4E,$AD,$08,$62,$2C,$00,$4F,$EF,$00,$0C
	dc.b $70,$FF,$B0,$86,$57,$C3,$44,$03,$67,$04,$70,$FF,$60,$02,$70,$00
	dc.b $4C,$EE,$10,$F8,$FF,$E8,$4E,$5E,$4E,$75,$85,$66,$73,$65,$65,$6B
	dc.b $00,$00,$4E,$56,$00,$00,$48,$E7,$03,$08,$28,$6E,$00,$08,$4A,$94
	dc.b $6C,$04,$70,$00,$28,$80,$70,$00,$30,$2C,$00,$12,$4A,$80,$08,$00
	dc.b $00,$00,$67,$08,$20,$14,$44,$80,$2E,$00,$60,$48,$70,$00,$30,$2C
	dc.b $00,$12,$32,$3C,$00,$82,$C2,$40,$67,$30,$7E,$00,$70,$00,$30,$2C
	dc.b $00,$12,$72,$02,$C2,$40,$67,$2C,$4A,$AC,$00,$08,$67,$26,$70,$00
	dc.b $30,$2C,$00,$12,$72,$04,$C2,$40,$70,$00,$30,$01,$4A,$80,$66,$14
	dc.b $2E,$2C,$00,$04,$9E,$AC,$00,$08,$60,$0A,$70,$16,$2B,$40,$CD,$8A
	dc.b $70,$FF,$60,$28,$70,$01,$2F,$00,$72,$00,$2F,$01,$74,$00,$34,$2C
	dc.b $00,$14,$2F,$02,$4E,$AD,$08,$62,$2C,$00,$4F,$EF,$00,$0C,$6D,$04
	dc.b $DC,$87,$60,$06,$70,$16,$2B,$40,$CD,$8A,$20,$06,$4C,$EE,$10,$C0
	dc.b $FF,$F4,$4E,$5E,$4E,$75,$85,$66,$74,$65,$6C,$6C,$00,$00,$4E,$56
	dc.b $00,$00,$48,$E7,$01,$08,$2E,$2E,$00,$14,$28,$6E,$00,$08,$4A,$AC
	dc.b $00,$08,$67,$1A,$70,$00,$30,$2C,$00,$12,$72,$08,$C2,$40,$67,$0E
	dc.b $2F,$0C,$4E,$BA,$F9,$F8,$20,$6C,$00,$08,$A0,$1F,$58,$4F,$02,$6C
	dc.b $FE,$B3,$00,$12,$30,$2E,$00,$12,$81,$6C,$00,$12,$0C,$87,$00,$00
	dc.b $FF,$FF,$63,$08,$39,$7C,$FF,$FF,$00,$10,$60,$04,$39,$47,$00,$10
	dc.b $29,$6E,$00,$0C,$00,$08,$2F,$0C,$4E,$BA,$F6,$C8,$0C,$87,$00,$00
	dc.b $FF,$FF,$58,$4F,$63,$08,$20,$3C,$00,$00,$FF,$FF,$60,$02,$70,$00
	dc.b $4C,$EE,$10,$80,$FF,$F8,$4E,$5E,$4E,$75,$87,$73,$65,$74,$76,$62
	dc.b $75,$66,$00,$00,$4E,$56,$00,$00,$48,$E7,$01,$08,$2E,$2E,$00,$08
	dc.b $28,$6E,$00,$0C,$70,$FF,$B0,$87,$66,$04,$70,$FF,$60,$42,$70,$00
	dc.b $30,$2C,$00,$12,$72,$01,$C2,$40,$70,$00,$30,$01,$4A,$80,$67,$0A
	dc.b $20,$2C,$00,$04,$B0,$AC,$00,$08,$62,$18,$20,$2C,$00,$04,$B0,$AC
	dc.b $00,$08,$66,$0A,$4A,$94,$66,$06,$52,$AC,$00,$04,$60,$04,$70,$FF
	dc.b $60,$0E,$53,$AC,$00,$04,$20,$6C,$00,$04,$10,$87,$52,$94,$20,$07
	dc.b $4C,$EE,$10,$80,$FF,$F8,$4E,$5E,$4E,$75,$86,$75,$6E,$67,$65,$74
	dc.b $63,$00,$00,$00,$4E,$56,$00,$00,$2F,$0C,$28,$6E,$00,$08,$20,$54
	dc.b $2F,$28,$00,$04,$4E,$BA,$F8,$80,$20,$54,$70,$00,$30,$28,$00,$0C
	dc.b $72,$08,$C2,$40,$58,$4F,$66,$08,$22,$48,$20,$69,$00,$10,$A0,$1F
	dc.b $28,$6E,$FF,$FC,$4E,$5E,$4E,$75,$89,$5F,$62,$75,$66,$43,$6C,$6F
	dc.b $73,$65,$00,$00,$4E,$56,$00,$00,$48,$E7,$11,$18,$28,$6E,$00,$08
	dc.b $20,$54,$20,$68,$00,$08,$26,$68,$00,$08,$20,$0B,$67,$30,$20,$54
	dc.b $70,$00,$30,$28,$00,$0C,$72,$10,$C2,$40,$70,$00,$30,$01,$4A,$80
	dc.b $66,$06,$2F,$0C,$4E,$93,$58,$4F,$20,$54,$70,$00,$30,$28,$00,$0C
	dc.b $72,$10,$C2,$40,$67,$04,$70,$00,$60,$72,$70,$01,$60,$6E,$20,$54
	dc.b $26,$68,$00,$04,$70,$00,$30,$2B,$00,$12,$32,$3C,$00,$80,$C2,$40
	dc.b $67,$1E,$70,$00,$30,$2B,$00,$12,$72,$02,$C2,$40,$67,$12,$70,$01
	dc.b $2F,$00,$72,$00,$2F,$01,$2F,$0B,$4E,$BA,$FC,$6C,$4F,$EF,$00,$0C
	dc.b $53,$93,$4A,$93,$5C,$C3,$44,$03,$67,$10,$20,$6B,$00,$04,$52,$AB
	dc.b $00,$04,$70,$00,$10,$10,$4A,$80,$60,$0A,$2F,$0B,$4E,$BA,$F6,$94
	dc.b $4A,$80,$58,$4F,$2E,$00,$70,$FF,$B0,$87,$66,$04,$70,$01,$60,$0C
	dc.b $2F,$0B,$2F,$07,$4E,$BA,$FE,$9E,$70,$00,$50,$4F,$4C,$EE,$18,$88
	dc.b $FF,$F0,$4E,$5E,$4E,$75,$87,$5F,$62,$75,$66,$45,$4F,$46,$00,$00
	dc.b $4E,$56,$00,$00,$2F,$0C,$28,$6E,$00,$10,$4A,$94,$66,$0C,$42,$6D
	dc.b $CD,$88,$70,$09,$2B,$40,$CD,$8A,$60,$2E,$42,$6D,$CD,$88,$70,$00
	dc.b $2B,$40,$CD,$8A,$30,$2E,$00,$08,$48,$C0,$2F,$00,$70,$00,$30,$2E
	dc.b $00,$0A,$2F,$00,$2F,$2E,$00,$0C,$20,$54,$20,$50,$2F,$28,$00,$04
	dc.b $4E,$BA,$FD,$BC,$4F,$EF,$00,$10,$28,$6E,$FF,$FC,$4E,$5E
;     candidate_code payload[2950..4970) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=3 labels=1 xrefs=2
macos_code_CODE_24_loc_00000b86:
	movea.l (a7)+,a0
	lea.l $000C(a7),a7
	jmp (a0)

; CODE 25 SANELib source section
macos_code_CODE_25:
;   source_section_id: macos-code-CODE-25
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 25
;   name: SANELib
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 246
;   payload_sha256: c87908dd286d0e5fdcab70725ec20e98a37cca1357f18132809c3ab9e7562090
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:25
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 25 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_code span=40..246 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=1 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_code payload[40..246) size=206 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 25 payload[0..246) sha256=c87908dd286d0e5fdcab70725ec20e98a37cca1357f18132809c3ab9e7562090
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_25_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$09,$F8,$00,$00,$00,$03,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_code payload[40..246) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=13 labels=4 xrefs=5
macos_code_CODE_25_loc_00000028:
	movea.l (a7)+,a0
	moveq.l #31,d2
	and.w (a7)+,d2
	bra.b loc_0_00000010
macos_code_CODE_25_loc_00000038:
	bsr.b loc_0_00000044
	clr.w (a7)
	and.w d2,d0
	beq.b loc_0_0000001A
	addq.b #1,(a7)
macos_code_CODE_25_loc_00000042:
	jmp (a0)
macos_code_CODE_25_loc_0000006c:
	subq.l #2,a7
	pea.l (a7)
	move.w #$3,-(a7)

; CODE 26 PASLIB source section
macos_code_CODE_26:
;   source_section_id: macos-code-CODE-26
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 26
;   name: PASLIB
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 2940
;   payload_sha256: 62b8ca8b968fab6a003f39717b671f9c6cae8d20a9c77cb7ab41fd0315a229ae
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:26
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 26 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..198 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=198..2940 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..40) size=40 entrypoint=False status=validated parser_use=accepted_parser_output evidence=far_model_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[40..198) size=158 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[198..2940) size=2742 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   byte_preserving_placeholder: CODE 26 payload[0..2940) sha256=62b8ca8b968fab6a003f39717b671f9c6cae8d20a9c77cb7ab41fd0315a229ae
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..40) status=validated parser_use=accepted_parser_output evidence=far_model_segment_header
macos_code_CODE_26_metadata_00000000:
	dc.b $FF,$FF,$00,$00,$00,$00,$0A,$10,$00,$00,$00,$18,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	dc.b $00,$00,$00,$00,$00,$00,$00,$00
;     candidate_unresolved_prefix payload[40..198) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_26_candidate_unresolved_prefix_00000028:
	dc.b $4E,$56,$00,$00,$2B,$7C,$00,$00,$13,$88,$D2,$B8,$42,$2D,$D2,$B3
	dc.b $42,$2D,$D2,$B2,$70,$00,$2B,$40,$D2,$AC,$70,$00,$2B,$40,$D2,$A8
	dc.b $70,$00,$2B,$40,$D2,$9C,$70,$00,$2B,$40,$D2,$98,$1B,$7C,$00,$01
	dc.b $D2,$97,$70,$00,$2B,$40,$D2,$B4,$70,$00,$2B,$40,$D2,$92,$4E,$5E
	dc.b $4E,$75,$89,$25,$49,$4E,$49,$54,$48,$45,$41,$50,$00,$00,$4E,$56
	dc.b $FF,$F4,$48,$E7,$03,$18,$2C,$2E,$00,$08,$42,$6D,$D2,$B0,$10,$2D
	dc.b $D2,$B3,$67,$5C,$28,$6D,$D2,$AC,$20,$0C,$67,$22,$2E,$2C,$00,$04
	dc.b $20,$46,$20,$0C,$72,$0C,$D0,$81,$B0,$90,$5F,$C0,$20,$46,$22,$0C
	dc.b $D2,$87,$B2,$90,$5C,$C1,$C0,$01,$66,$1A,$28,$54,$60,$DA,$3B,$7C
	dc.b $FB,$E4,$D2,$B0,$4A,$AD,$D2,$B4,$67,$2C,$2F,$2D,$D2,$B4
;     candidate_code payload[198..2940) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=7 labels=2 xrefs=3
macos_code_CODE_26_loc_000000c6:
	movea.l (a7)+,a0
	jsr (a0)
	bra.b loc_0_00000028
macos_code_CODE_26_loc_000000ee:
	movem.l (a7)+,d6-d7/a3-a4
	unlk a6
	move.l (a7)+,(a7)
	rts

; CODE 27 32-bit bootstrap source section
macos_code_CODE_27:
;   source_section_id: macos-code-CODE-27
;   source_kind: macos_code_resource
;   backend: macos-code
;   status: semantic_source
;   resource_type: CODE
;   id: 27
;   name: 32-bit bootstrap
;   role: code_segment
;   code_kind: code_segment
;   payload_size: 1882
;   payload_sha256: f683b4c722b40eda686a3074d68910f8316ecd373798c1a5834df64d8b757352
;   presentation: kind=c_owned_restored_source_packet status=covered visible=True identity=macos-code:CODE:27
;   listing: kind=semantic_listing available=True reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 27 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=candidate_unresolved_prefix span=4..204 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=204..1882 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:27
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   source_body_ranges:
;     metadata payload[0..4) size=4 entrypoint=False status=validated parser_use=accepted_parser_output evidence=nonzero_code_segment_header fact=macos.code_resource.nonzero.segment_header
;     candidate_unresolved_prefix payload[4..204) size=200 entrypoint=False status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;     candidate_code payload[204..1882) size=1678 entrypoint=True status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry fact=macos.code_resource.movea_stack_a0.boundary.candidate
;   incoming_CODE0_xrefs:
macos_code_CODE_27_routine_candidate_000000cc:
;     from=macos_CODE_0_jump_table_entry_0 source_payload=16 target_payload=204 status=candidate parser_use=candidate_only fact=macos.code_resource.jump_table.routine_offsets.candidate
;   byte_preserving_placeholder: CODE 27 payload[0..1882) sha256=f683b4c722b40eda686a3074d68910f8316ecd373798c1a5834df64d8b757352
;   placeholder_reason: semantic CODE disassembly remains deferred; current source body renders exact bytes for C-owned ranges and evidence status without promoting byte-entry, A5, or Segment Loader semantics.
;   byte_real_source:
;     metadata payload[0..4) status=validated parser_use=accepted_parser_output evidence=nonzero_code_segment_header
macos_code_CODE_27_metadata_00000000:
	dc.b $00,$00,$00,$01
;     candidate_unresolved_prefix payload[4..204) status=candidate parser_use=candidate_only evidence=prefix_before_stack_entry
macos_code_CODE_27_candidate_unresolved_prefix_00000004:
	dc.b $70,$30,$A3,$1E,$4A,$40,$66,$72,$30,$38,$09,$34,$2B,$88,$00,$0C
	dc.b $4A,$78,$02,$8E,$6D,$2E,$30,$3C,$A8,$9F,$A7,$46,$22,$48,$30,$3C
	dc.b $A0,$90,$A3,$46,$B3,$C8,$67,$1C,$9E,$FC,$00,$10,$41,$D7,$70,$02
	dc.b $A0,$90,$0C,$68,$00,$01,$00,$06,$56,$C0,$41,$FA,$00,$52,$10,$80
	dc.b $4F,$EF,$00,$10,$61,$00,$01,$BC,$61,$00,$00,$F4,$61,$00,$01,$46
	dc.b $41,$FA,$00,$24,$20,$97,$20,$4D,$D0,$F8,$09,$34,$4E,$A8,$00,$12
	dc.b $61,$00,$01,$EC,$20,$4D,$D0,$F8,$09,$34,$20,$68,$00,$0C,$A0,$1F
	dc.b $20,$7A,$00,$04,$4E,$D0,$00,$00,$00,$00,$4E,$75,$80,$0E,$33,$32
	dc.b $5F,$62,$69,$74,$5F,$73,$74,$61,$72,$74,$75,$70,$00,$00,$00,$00
	dc.b $08,$3A,$00,$00,$FF,$FA,$67,$1E,$0C,$38,$00,$00,$01,$2F,$67,$16
	dc.b $30,$3C,$A1,$98,$A3,$46,$22,$48,$30,$3C,$A8,$9F,$A7,$46,$B3,$C8
	dc.b $67,$04,$70,$01,$A1,$98,$4E,$75,$80,$0B,$66,$6C,$75,$73,$68,$5F
	dc.b $63,$61,$63,$68,$65,$00,$00,$00
;     candidate_code payload[204..1882) status=candidate parser_use=candidate_only evidence=m68k_movea_l_stack_to_a0_entry
;     semantic_source: kind=macos_code_semantic_source_v1 status=decoded instructions=4 labels=1 xrefs=2
macos_code_CODE_27_loc_000000cc:
	movea.l (a7)+,a0
	addq.w #4,a7
	clr.w (a7)
	jmp (a0)


; Source quality gate
;   kind: macos_source_quality_gate_v1
;   status: byte_real_baseline
;   semantic_closeout_status: blocked_residual_decode_gaps
;   baseline_status: passed_with_deferred_semantics
;   baseline_status_meaning: byte preservation, source ordering, labels, and residual accounting are present; this is not semantic source closeout
;   scope: current MPW Tools Asm fixture
;   semantic_components:
;     byte_preservation_status: byte_real_complete
;     label_xref_status: generated_labels_and_xrefs_present
;     residual_status: explicit
;     semantic_disassembly_status: residual_decode_gaps_present
;     source_ordering_status: source_first
;   checklist:
;     all_code_sections_visible: True
;     no_fake_disassembly: True
;     no_vague_orphan_bucket: True
;     range_ownership_complete: True
;     reachable_code_evidence_recorded: True
;     residuals_explicit: True
;     source_first_artifact: True
;     stable_labels_present: True
;   does_not_claim:
;     accepted byte-entry proof
;     decoded Segment Loader relocation/fixup semantics
;     A5 lifetime proof
;     resource-fork round trip
;   non_blocking_for_semantic_disassembly:
;     missing human semantic names
;     missing original source symbols
;     deferred A5 lifetime proof
;     deferred Segment Loader fixup decoding for current zero-offset fixture spans
;   resource_review:
;     CODE 0: section=macos-code-CODE-0 ownership=metadata coverage=True labels=5 xrefs=0 instructions=0 body_spans=0 byte_real_only_body=False reachable_evidence=4 residuals=0
;       next: decode CODE 0 dispatch target semantics only where accepted target evidence exists
;     CODE 1: section=macos-code-CODE-1 ownership=candidate_code,metadata coverage=True labels=6 xrefs=2 instructions=8 body_spans=1 byte_real_only_body=False reachable_evidence=3 residuals=338
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual semantic_decode_gap payload[62..29024) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=337 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 2: section=macos-code-CODE-2 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=4 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=23
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..374) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[384..7788) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=21 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 3: section=macos-code-CODE-3 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=78
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..302) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[308..18252) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=76 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 4: section=macos-code-CODE-4 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=3 instructions=10 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=59
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..468) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[494..6426) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=57 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 5: section=macos-code-CODE-5 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=11 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=169
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..212) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[234..26638) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=167 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 6: section=macos-code-CODE-6 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=21 instructions=76 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=41
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..58) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[240..15158) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=39 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 7: section=macos-code-CODE-7 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=4 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=15
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..352) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[362..4142) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=13 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 8: section=macos-code-CODE-8 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=27 instructions=66 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=17
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..42) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[220..1852) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=15 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 9: section=macos-code-CODE-9 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=39
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..712) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[720..13946) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=37 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 10: section=macos-code-CODE-10 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=6
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..148) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[154..1542) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=4 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 11: section=macos-code-CODE-11 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=49
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..836) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[842..3678) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=47 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 12: section=macos-code-CODE-12 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=3 instructions=15 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=51
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..44) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[76..6928) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=49 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 13: section=macos-code-CODE-13 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=16 instructions=61 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=166
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..44) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[196..33354) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=164 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 14: section=macos-code-CODE-14 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=24
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..236) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[242..1886) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=22 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 15: section=macos-code-CODE-15 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=41
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..96) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[104..3452) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=39 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 16: section=macos-code-CODE-16 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=8
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..246) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[252..1034) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=6 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 17: section=macos-code-CODE-17 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=32
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..100) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[106..3674) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=30 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 18: section=macos-code-CODE-18 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=4
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..1562) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[1568..1974) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=2 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 19: section=macos-code-CODE-19 ownership=deferred,metadata coverage=True labels=3 xrefs=0 instructions=0 body_spans=0 byte_real_only_body=False reachable_evidence=1 residuals=1
;       next: extend C-owned CODE layout and reference analysis before promoting semantic source rows
;       residual deferred payload[40..556) status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     CODE 20: section=macos-code-CODE-20 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=37
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..2876) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[2884..5262) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=35 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 21: section=macos-code-CODE-21 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=39
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..2000) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[2008..6794) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=37 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 22: section=macos-code-CODE-22 ownership=deferred,metadata coverage=True labels=3 xrefs=0 instructions=0 body_spans=0 byte_real_only_body=False reachable_evidence=1 residuals=1
;       next: extend C-owned CODE layout and reference analysis before promoting semantic source rows
;       residual deferred payload[40..96) status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     CODE 23: section=macos-code-CODE-23 ownership=deferred,metadata coverage=True labels=3 xrefs=0 instructions=0 body_spans=0 byte_real_only_body=False reachable_evidence=1 residuals=1
;       next: extend C-owned CODE layout and reference analysis before promoting semantic source rows
;       residual deferred payload[40..126) status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     CODE 24: section=macos-code-CODE-24 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=2 instructions=3 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=25
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..2950) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[2958..4970) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=23 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 25: section=macos-code-CODE-25 ownership=candidate_code,metadata coverage=True labels=3 xrefs=5 instructions=13 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=13
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual semantic_decode_gap payload[48..56) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual semantic_decode_gap payload[68..108) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual semantic_decode_gap payload[116..246) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=10 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 26: section=macos-code-CODE-26 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=4 xrefs=3 instructions=7 body_spans=1 byte_real_only_body=False reachable_evidence=2 residuals=58
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[40..198) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[204..238) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual semantic_decode_gap payload[248..2940) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=55 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments
;     CODE 27: section=macos-code-CODE-27 ownership=candidate_code,candidate_unresolved_prefix,metadata coverage=True labels=5 xrefs=2 instructions=4 body_spans=1 byte_real_only_body=False reachable_evidence=3 residuals=21
;       next: extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans
;       residual candidate_unresolved_prefix payload[4..204) status=candidate parser_use=candidate_only reason=bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through loader/stack/fixup flow not yet modeled
;       residual semantic_decode_gap payload[212..1882) status=candidate parser_use=candidate_only reason=decoder did not emit an instruction/data row for this exact executable subrange
;       residual_summary candidate_unvisited_entry_pattern count=19 status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain structured residuals, not rendered as source comments


; Supporting evidence follows after the source body.

; File forks
;   data: role=data_fork size=10752 sha256=ac751c25db1546ffcf35acae2873379816323de4910d3481eae5528841d85eb0
;   resource: role=executable_resource_fork size=213850 sha256=c2f0dba686c522ce8c912b872e8b119e2377daf45a13061d2986b84253ccba26

; Resource fork
;   resource_count: 35
;   type_count: 5
;   type CODE: count=28
;   type acur: count=1
;   type CURS: count=4
;   type cmdo: count=1
;   type vers: count=1

; CODE 0 jump-table/application metadata
CODE 0 unknown: payload_size=2784 sha256=8413f3bca1604845bb778c2a7701a067aa8b84853e7c77a60e63166d5b6399c1
;   above_a5_size: 2800
;   below_a5_size: 14624
;   jump_table_length: 2768
;   jump_table_offset_from_a5: 32

; CODE resources
;   CODE 0 unknown: payload_size=2784 sha256=8413f3bca1604845bb778c2a7701a067aa8b84853e7c77a60e63166d5b6399c1
;   CODE 27 32-bit bootstrap: payload_size=1882 sha256=f683b4c722b40eda686a3074d68910f8316ecd373798c1a5834df64d8b757352
;   CODE 1 Main: payload_size=29024 sha256=4a543f6fd1c542fccd38ec9f469b06f65c797dfd8b226fefc9f576faafbe70f5 selected
;   CODE 2 FPOpTable: payload_size=7788 sha256=a33f1dfe28237a5ee6f9ba7a96540e8e4842a7e6207575db5f0479b8c622a4f2
;   CODE 3 Init: payload_size=18252 sha256=331fc8e7daf79d4e733760cb8ad413ade51431a01dd6c19c4f73720f562b08e4
;   CODE 4 IOMgr: payload_size=6426 sha256=a697293e579b91031cb9bb37cd80a4f47d2acb9eff60a4f4b7e3cb9a18fd4fca
;   CODE 5 Macros: payload_size=26638 sha256=90b898d2148ba2c3b798bed0c8c5dc936fba9ed3e8b958d279db4b279a033dfc
;   CODE 6 OpTable: payload_size=15158 sha256=75005bca2e9e007ce374020416127735d9096e064806e4e1e1b888cd3ba8a9cf
;   CODE 7 POpTable: payload_size=4142 sha256=3bc5de90c439ad5e0f7e5d4635b445022db8ab231a9b43981dbd95673ac0b78e
;   CODE 8 Listing: payload_size=1852 sha256=5b3cd8756213ba73870bb353160d4e5dbb1a3bdd2da93157146d091b6949a2e9
;   CODE 9 Pass2: payload_size=13946 sha256=0361ae9dcb47f31cf559372a3e42c672dcfb8920b332d4f900a7124ab6c70bf3
;   CODE 10 FinishUp: payload_size=1542 sha256=2d5d27affd131aaa28eb0bd33157051e8f30ee3cdc054df4aad3011bdb22c1e1
;   CODE 11 Dbg: payload_size=3678 sha256=04097ca27d77f09604177ac5e85019ecaed552d68ae2e9d50ae3b5a4e394c503
;   CODE 12 LoadDump: payload_size=6928 sha256=9c563d29bea4465730181b661ea9a3a60d15276aa71a6be399b02b9a4091cbdb
;   CODE 13 Directives: payload_size=33354 sha256=1358e27cbf9cb7da402416dfa830bd93f99a23e16da5c9972f63549d171a30c8
;   CODE 14 MemMgr: payload_size=1886 sha256=14e851122fdae5910c2772def35a8b36c30dc7133cb92df8524f8a42ff5f8c70
;   CODE 15 Errors: payload_size=3452 sha256=ebe2c26fe6fffb8585f7e9e0ebfffa73ca877946c26eab44f0efbd96678018cd
;   CODE 16 New: payload_size=1034 sha256=51e7a7d264825cd4103b31a0bff37ff49fdb64e8ddb299b2a46d4bd3c07f6a37
;   CODE 17 DispSymTbl: payload_size=3674 sha256=e4c8e735bff587b55b1482bde5137deec3ae177ea802b09aac3e97401f2905b9
;   CODE 18 FinishDirectives: payload_size=1974 sha256=96d836fa8382f88453204a38fddb5da2e46867767f572482abb8f9cbb5e431c6
;   CODE 19 SetupArgV: payload_size=556 sha256=46027b8ec8f830b28abc470f5e942b54f7845efd9cf136f68e3b2b8a9873f3ce
;   CODE 20 INTENV: payload_size=5262 sha256=de9f4a82222f3ff12586a0bb691cc6b5d513777d498d223dfa45311d4a7dc84a
;   CODE 21 SADEV: payload_size=6794 sha256=927c28db98eadbc5501e570ada73af8afca05964552a831c02051f6e6fa3b687
;   CODE 22 SANELIB: payload_size=96 sha256=6929f16d82666fe0f31993c30f2750798bf934a0dcddf3c6eb0adc2c552484f8
;   CODE 23 STDCLIB: payload_size=126 sha256=ce2eaab2bd782055c6aaaefc223f2e72d4f746e25a05cc8b3599836ecbd41969
;   CODE 24 STDIO: payload_size=4970 sha256=f98dfc823a565d6502fa4ac1feb7b616b397ba9a918ce2c5f47b274e99a9026a
;   CODE 25 SANELib: payload_size=246 sha256=c87908dd286d0e5fdcab70725ec20e98a37cca1357f18132809c3ab9e7562090
;   CODE 26 PASLIB: payload_size=2940 sha256=62b8ca8b968fab6a003f39717b671f9c6cae8d20a9c77cb7ab41fd0315a229ae

; CODE resource coverage
;   total_code_resources: 28
;   CODE 0 unknown: status=metadata-only layout=metadata reason=CODE 0 jump-table/application metadata
;   CODE 27 32-bit bootstrap: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[204..1882); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 1 Main: status=rendered layout=metadata,candidate_code reason=expanded below through macos-code listing backend
;   CODE 2 FPOpTable: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[374..7788); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 3 Init: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[302..18252); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 4 IOMgr: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[468..6426); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 5 Macros: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[212..26638); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 6 OpTable: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[58..15158); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 7 POpTable: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[352..4142); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 8 Listing: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[42..1852); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 9 Pass2: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[712..13946); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 10 FinishUp: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[148..1542); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 11 Dbg: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[836..3678); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 12 LoadDump: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[44..6928); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 13 Directives: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[44..33354); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 14 MemMgr: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[236..1886); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 15 Errors: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[96..3452); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 16 New: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[246..1034); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 17 DispSymTbl: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[100..3674); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 18 FinishDirectives: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[1562..1974); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 19 SetupArgV: status=deferred layout=metadata,deferred reason=classifier deferred range: missing_m68k_movea_l_stack_to_a0_entry
;   CODE 20 INTENV: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[2876..5262); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 21 SADEV: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[2000..6794); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 22 SANELIB: status=deferred layout=metadata,deferred reason=classifier deferred range: missing_m68k_movea_l_stack_to_a0_entry
;   CODE 23 STDCLIB: status=deferred layout=metadata,deferred reason=classifier deferred range: missing_m68k_movea_l_stack_to_a0_entry
;   CODE 24 STDIO: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[2950..4970); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 25 SANELib: status=partial layout=metadata,candidate_code reason=candidate_code entry payload[40..246); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 26 PASLIB: status=partial layout=metadata,candidate_unresolved_prefix,candidate_code reason=candidate_code entry payload[198..2940); full per-resource listing deferred until relocation/source-boundary context is represented

; CODE segment/routine map
;   CODE 27: jt_first=0 jt_count=1 jt_span_size=8 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     routine_candidate index=0 jt_offset=0 code0_offset=16 routine_offset=0 fact=macos.code_resource.jump_table.routine_offsets.candidate status=candidate
;   CODE 1: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 2: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 3: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 4: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 5: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 6: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 7: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 8: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 9: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 10: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 11: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 12: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 13: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 14: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 15: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 16: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 17: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 18: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 19: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 20: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 21: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 22: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 23: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 24: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 25: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;   CODE 26: jt_first=65535 jt_count=0 jt_span_size=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated

; CODE resource detail subviews
;   CODE 0 unknown: role=code0_metadata kind=jump_table_segment payload_size=2784 sha256=8413f3bca1604845bb778c2a7701a067aa8b84853e7c77a60e63166d5b6399c1 fact=macos.code_resource.0.jump_table_metadata status=validated
;     jump_table: start=16 size=2768 entries=346 fact=macos.jump_table.entries.accepted status=validated
;     jump_table_rows:
;       entry=0 code0_offset=16 entry_size=8 target_CODE=27 routine_offset=0 layout_fact=macos.jump_table.entries.accepted layout_status=validated target_fact=macos.code_resource.jump_table.routine_offsets.candidate target_status=candidate target_parser_use=candidate_only
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:0 visible=True
;     anchors:
;       accepted_metadata: label=CODE 0 metadata offset=unknown fact=macos.code_resource.0.jump_table_metadata status=validated parser_use=accepted_parser_output
;       accepted_jump_table: label=CODE 0 jump table offset=16 fact=macos.jump_table.entries.accepted status=validated parser_use=accepted_parser_output
;       candidate_routine_jump_table_entry: label=CODE 27 routine candidate 0 offset=16 fact=macos.code_resource.jump_table.routine_offsets.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 0 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..2784 status=validated parser_use=accepted_parser_output reason=code0_jump_table_metadata
;     source_reference_records:
;       0: kind=code0_routing_table ownership=unknown status=validated parser_use=accepted_parser_output target=CODE resource dispatch table
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=metadata available=False route=unknown reason=CODE 0 is jump-table/application metadata, not ordinary m68k code
;     previews: none
;   CODE 1 Main: role=code_segment kind=code_segment payload_size=29024 sha256=4a543f6fd1c542fccd38ec9f469b06f65c797dfd8b226fefc9f576faafbe70f5 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:1 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 1 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 1 candidate code offset=40 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 1 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_code span=40..29024 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=1 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=full_listing available=True route=listing reason=unknown
;     previews: none
;   CODE 2 FPOpTable: role=code_segment kind=code_segment payload_size=7788 sha256=a33f1dfe28237a5ee6f9ba7a96540e8e4842a7e6207575db5f0479b8c622a4f2 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:2 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 2 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 2 candidate code offset=374 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 2 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..374 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=374..7788 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 3 Init: role=code_segment kind=code_segment payload_size=18252 sha256=331fc8e7daf79d4e733760cb8ad413ade51431a01dd6c19c4f73720f562b08e4 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:3 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 3 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 3 candidate code offset=302 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 3 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..302 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=302..18252 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 4 IOMgr: role=code_segment kind=code_segment payload_size=6426 sha256=a697293e579b91031cb9bb37cd80a4f47d2acb9eff60a4f4b7e3cb9a18fd4fca fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:4 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 4 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 4 candidate code offset=468 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 4 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..468 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=468..6426 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 5 Macros: role=code_segment kind=code_segment payload_size=26638 sha256=90b898d2148ba2c3b798bed0c8c5dc936fba9ed3e8b958d279db4b279a033dfc fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:5 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 5 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 5 candidate code offset=212 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 5 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..212 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=212..26638 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 6 OpTable: role=code_segment kind=code_segment payload_size=15158 sha256=75005bca2e9e007ce374020416127735d9096e064806e4e1e1b888cd3ba8a9cf fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:6 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 6 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 6 candidate code offset=58 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 6 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..58 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=58..15158 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 7 POpTable: role=code_segment kind=code_segment payload_size=4142 sha256=3bc5de90c439ad5e0f7e5d4635b445022db8ab231a9b43981dbd95673ac0b78e fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:7 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 7 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 7 candidate code offset=352 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 7 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..352 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=352..4142 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 8 Listing: role=code_segment kind=code_segment payload_size=1852 sha256=5b3cd8756213ba73870bb353160d4e5dbb1a3bdd2da93157146d091b6949a2e9 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:8 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 8 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 8 candidate code offset=42 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 8 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..42 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=42..1852 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 9 Pass2: role=code_segment kind=code_segment payload_size=13946 sha256=0361ae9dcb47f31cf559372a3e42c672dcfb8920b332d4f900a7124ab6c70bf3 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:9 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 9 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 9 candidate code offset=712 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 9 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..712 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=712..13946 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 10 FinishUp: role=code_segment kind=code_segment payload_size=1542 sha256=2d5d27affd131aaa28eb0bd33157051e8f30ee3cdc054df4aad3011bdb22c1e1 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:10 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 10 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 10 candidate code offset=148 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 10 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..148 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=148..1542 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 11 Dbg: role=code_segment kind=code_segment payload_size=3678 sha256=04097ca27d77f09604177ac5e85019ecaed552d68ae2e9d50ae3b5a4e394c503 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:11 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 11 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 11 candidate code offset=836 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 11 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..836 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=836..3678 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 12 LoadDump: role=code_segment kind=code_segment payload_size=6928 sha256=9c563d29bea4465730181b661ea9a3a60d15276aa71a6be399b02b9a4091cbdb fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:12 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 12 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 12 candidate code offset=44 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 12 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..44 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=44..6928 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 13 Directives: role=code_segment kind=code_segment payload_size=33354 sha256=1358e27cbf9cb7da402416dfa830bd93f99a23e16da5c9972f63549d171a30c8 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:13 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 13 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 13 candidate code offset=44 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 13 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..44 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=44..33354 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 14 MemMgr: role=code_segment kind=code_segment payload_size=1886 sha256=14e851122fdae5910c2772def35a8b36c30dc7133cb92df8524f8a42ff5f8c70 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:14 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 14 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 14 candidate code offset=236 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 14 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..236 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=236..1886 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 15 Errors: role=code_segment kind=code_segment payload_size=3452 sha256=ebe2c26fe6fffb8585f7e9e0ebfffa73ca877946c26eab44f0efbd96678018cd fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:15 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 15 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 15 candidate code offset=96 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 15 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..96 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=96..3452 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 16 New: role=code_segment kind=code_segment payload_size=1034 sha256=51e7a7d264825cd4103b31a0bff37ff49fdb64e8ddb299b2a46d4bd3c07f6a37 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:16 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 16 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 16 candidate code offset=246 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 16 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..246 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=246..1034 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 17 DispSymTbl: role=code_segment kind=code_segment payload_size=3674 sha256=e4c8e735bff587b55b1482bde5137deec3ae177ea802b09aac3e97401f2905b9 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:17 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 17 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 17 candidate code offset=100 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 17 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..100 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=100..3674 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 18 FinishDirectives: role=code_segment kind=code_segment payload_size=1974 sha256=96d836fa8382f88453204a38fddb5da2e46867767f572482abb8f9cbb5e431c6 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:18 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 18 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 18 candidate code offset=1562 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 18 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..1562 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=1562..1974 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 19 SetupArgV: role=code_segment kind=code_segment payload_size=556 sha256=46027b8ec8f830b28abc470f5e942b54f7845efd9cf136f68e3b2b8a9873f3ce fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:19 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 19 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 19 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=unknown span=40..556 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=structured_placeholder available=False route=unknown reason=no candidate preview range; classifier deferred byte-entry evidence: missing_m68k_movea_l_stack_to_a0_entry
;     previews: none
;   CODE 20 INTENV: role=code_segment kind=code_segment payload_size=5262 sha256=de9f4a82222f3ff12586a0bb691cc6b5d513777d498d223dfa45311d4a7dc84a fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:20 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 20 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 20 candidate code offset=2876 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 20 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..2876 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2876..5262 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 21 SADEV: role=code_segment kind=code_segment payload_size=6794 sha256=927c28db98eadbc5501e570ada73af8afca05964552a831c02051f6e6fa3b687 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:21 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 21 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 21 candidate code offset=2000 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 21 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..2000 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2000..6794 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 22 SANELIB: role=code_segment kind=code_segment payload_size=96 sha256=6929f16d82666fe0f31993c30f2750798bf934a0dcddf3c6eb0adc2c552484f8 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:22 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 22 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 22 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=unknown span=40..96 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=structured_placeholder available=False route=unknown reason=no candidate preview range; classifier deferred byte-entry evidence: missing_m68k_movea_l_stack_to_a0_entry
;     previews: none
;   CODE 23 STDCLIB: role=code_segment kind=code_segment payload_size=126 sha256=ce2eaab2bd782055c6aaaefc223f2e72d4f746e25a05cc8b3599836ecbd41969 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:23 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 23 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 23 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=unknown span=40..126 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=structured_placeholder available=False route=unknown reason=no candidate preview range; classifier deferred byte-entry evidence: missing_m68k_movea_l_stack_to_a0_entry
;     previews: none
;   CODE 24 STDIO: role=code_segment kind=code_segment payload_size=4970 sha256=f98dfc823a565d6502fa4ac1feb7b616b397ba9a918ce2c5f47b274e99a9026a fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:24 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 24 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 24 candidate code offset=2950 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 24 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..2950 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2950..4970 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 25 SANELib: role=code_segment kind=code_segment payload_size=246 sha256=c87908dd286d0e5fdcab70725ec20e98a37cca1357f18132809c3ab9e7562090 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:25 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 25 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 25 candidate code offset=40 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 25 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_code span=40..246 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=1 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 26 PASLIB: role=code_segment kind=code_segment payload_size=2940 sha256=62b8ca8b968fab6a003f39717b671f9c6cae8d20a9c77cb7ab41fd0315a229ae fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=65535 jt_count=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:26 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 26 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_code_range: label=CODE 26 candidate code offset=198 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 26 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header
;       1: role=candidate_unresolved_prefix span=40..198 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=198..2940 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds
;   CODE 27 32-bit bootstrap: role=code_segment kind=code_segment payload_size=1882 sha256=f683b4c722b40eda686a3074d68910f8316ecd373798c1a5834df64d8b757352 fact=macos.resource_fork.code_resources.accepted status=validated
;     segment: jt_first=0 jt_count=1 fact=macos.code_resource.segment_jump_table_span.accepted status=validated
;     source_presentation: kind=c_owned_restored_source_packet status=covered stable_identity=macos-code:CODE:27 visible=True
;     anchors:
;       accepted_segment_metadata: label=CODE 27 segment metadata offset=0 fact=macos.code_resource.segment_jump_table_span.accepted status=validated parser_use=accepted_parser_output
;       candidate_routine_entry: label=CODE 27 routine candidate 0 offset=0 fact=macos.code_resource.jump_table.routine_offsets.candidate status=candidate parser_use=candidate_only
;       candidate_code_range: label=CODE 27 candidate code offset=204 fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;     restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 27 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=candidate_unresolved_prefix span=4..204 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=204..1882 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:27
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=semantic_listing available=True route=listing reason=C-owned semantic rows from generated loader/CODE0 entry seeds

; Non-CODE resource placeholders
;   type acur: 1 resource(s), structured placeholder
;   type CURS: 4 resource(s), structured placeholder
;   type cmdo: 1 resource(s), structured placeholder
;   type vers: 1 resource(s), structured placeholder
; Executable resource placeholders
;   executable_resource_placeholder: type=acur id=unknown name=unknown count=1 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:acur:* status=candidate source_context=unlinked reason=non-CODE resource metadata is inventory-only and not executable CODE
;     reference_site=resource_type_inventory type=acur id=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:acur:* link_status=unlinked source_offset=unknown reason=No direct CODE routing, fixup, or restored-source reference targets this resource type yet.
;   executable_resource_placeholder: type=CURS id=unknown name=unknown count=4 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:CURS:* status=validated source_context=unlinked reason=CURS type-level layout is cited; payload bitmap/hotspot bytes are not decoded
;     reference_site=resource_type_inventory type=CURS id=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:CURS:* link_status=unlinked source_offset=unknown reason=No direct CODE routing, fixup, or restored-source reference targets this resource type yet.
;   executable_resource_placeholder: type=cmdo id=unknown name=unknown count=1 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:cmdo:* status=candidate source_context=unlinked reason=non-CODE resource metadata is inventory-only and not executable CODE
;     reference_site=resource_type_inventory type=cmdo id=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:cmdo:* link_status=unlinked source_offset=unknown reason=No direct CODE routing, fixup, or restored-source reference targets this resource type yet.
;   executable_resource_placeholder: type=vers id=unknown name=unknown count=1 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:vers:* status=candidate source_context=unlinked reason=non-CODE resource metadata is inventory-only and not executable CODE
;     reference_site=resource_type_inventory type=vers id=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:vers:* link_status=unlinked source_offset=unknown reason=No direct CODE routing, fixup, or restored-source reference targets this resource type yet.

; Unsupported Mac Segment Loader/runtime areas
;   byte-for-byte MPW Link/Rez roundtrip
;   complete Segment Loader behavior
;   overflow_extents
;   segment_loader_relocations
;   source-to-CODE segment mapping
