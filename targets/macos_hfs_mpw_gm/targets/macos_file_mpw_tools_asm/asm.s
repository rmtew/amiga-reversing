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
;   CODE 27 32-bit bootstrap: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[204..1882); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 1 Main: status=rendered layout=metadata,data,candidate_code reason=expanded below through macos-code listing backend
;   CODE 2 FPOpTable: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[374..7788); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 3 Init: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[302..18252); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 4 IOMgr: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[468..6426); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 5 Macros: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[212..26638); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 6 OpTable: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[58..15158); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 7 POpTable: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[352..4142); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 8 Listing: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[42..1852); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 9 Pass2: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[712..13946); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 10 FinishUp: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[148..1542); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 11 Dbg: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[836..3678); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 12 LoadDump: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[44..6928); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 13 Directives: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[44..33354); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 14 MemMgr: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[236..1886); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 15 Errors: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[96..3452); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 16 New: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[246..1034); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 17 DispSymTbl: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[100..3674); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 18 FinishDirectives: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[1562..1974); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 19 SetupArgV: status=deferred layout=metadata,deferred reason=classifier deferred range: missing_m68k_movea_l_stack_to_a0_entry
;   CODE 20 INTENV: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[2876..5262); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 21 SADEV: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[2000..6794); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 22 SANELIB: status=deferred layout=metadata,deferred reason=classifier deferred range: missing_m68k_movea_l_stack_to_a0_entry
;   CODE 23 STDCLIB: status=deferred layout=metadata,deferred reason=classifier deferred range: missing_m68k_movea_l_stack_to_a0_entry
;   CODE 24 STDIO: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[2950..4970); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 25 SANELib: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[40..246); full per-resource listing deferred until relocation/source-boundary context is represented
;   CODE 26 PASLIB: status=partial layout=metadata,data,candidate_code reason=candidate_code entry payload[198..2940); full per-resource listing deferred until relocation/source-boundary context is represented

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
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_routing_table ownership=unknown status=validated parser_use=accepted_parser_output target=CODE resource dispatch table
;       2: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..40 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=40..29024 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:1
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..374 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=374..7788 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:2
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=374 end=438 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=374 end=378 bytes=00000c12 text=ori.b #$C12,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=378 end=384 bytes=0c300c3e0000 text=cmpi.b #$C3E,$0(a0,d0.w) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=384 end=390 bytes=0c6a0cc20000 text=cmpi.w #3266,$0000(a2) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=390 end=406 bytes=0ce20d9a0dac0dda0dec000000000e1a text=dc.b $0C,$E2,$0D,$9A,$0D,$AC,$0D,$DA,$0D,$EC,$00,$00,$00,$00,$0E,$1A decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=406 end=422 bytes=0e280e4600000e560e7a0e9600000ec0 text=dc.b $0E,$28,$0E,$46,$00,$00,$0E,$56,$0E,$7A,$0E,$96,$00,$00,$0E,$C0 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=422 end=438 bytes=00000ed000000ede0efe0f180f340f58 text=dc.b $00,$00,$0E,$D0,$00,$00,$0E,$DE,$0E,$FE,$0F,$18,$0F,$34,$0F,$58 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..302 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=302..18252 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:3
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=302 end=366 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=302 end=304 bytes=4a9f text=tst.l (a7)+ decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=304 end=306 bytes=6c04 text=bge.b loc_0_00000008 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=306 end=310 bytes=422efefc text=clr.b -$0104(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=310 end=312 bytes=4267 text=clr.w -(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=312 end=316 bytes=486efefc text=pea.l -$0104(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=316 end=320 bytes=486ded70 text=pea.l -$1290(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=320 end=324 bytes=4ead0062 text=jsr $0062(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=324 end=328 bytes=1b5feb69 text=move.b (a7)+,-$1497(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=328 end=330 bytes=7000 text=moveq.l #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=330 end=334 bytes=2b40ed62 text=move.l d0,-$129E(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=334 end=340 bytes=1b7c0001ee70 text=move.b #$1,-$1190(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=340 end=344 bytes=426ded6c text=clr.w -$1294(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=344 end=346 bytes=7000 text=moveq.l #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=346 end=350 bytes=2b40ed68 text=move.l d0,-$1298(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=350 end=354 bytes=422decfe text=clr.b -$1302(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=354 end=356 bytes=7000 text=moveq.l #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=356 end=360 bytes=2b40ecf8 text=move.l d0,-$1308(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=360 end=364 bytes=422df073 text=clr.b -$0F8D(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=364 end=366 bytes=422d text=dc.b $42,$2D decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..468 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=468..6426 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:4
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=468 end=532 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=468 end=470 bytes=fd fc text=dc.w $fdfc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=470 end=472 bytes=48 e7 text=dc.w $48e7 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=472 end=474 bytes=01 08 text=dc.w $0108 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=474 end=476 bytes=28 6e text=dc.w $286e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=476 end=478 bytes=00 0a text=dc.w $000a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=478 end=480 bytes=42 67 text=dc.w $4267 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=480 end=482 bytes=2f 0c text=dc.w $2f0c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=482 end=484 bytes=48 6e text=dc.w $486e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=484 end=486 bytes=ff 00 text=dc.w $ff00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=486 end=488 bytes=48 6e text=dc.w $486e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=488 end=490 bytes=fe fe text=dc.w $fefe decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=490 end=492 bytes=48 6e text=dc.w $486e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=492 end=494 bytes=fe ff text=dc.w $feff decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=494 end=496 bytes=4e ad text=dc.w $4ead decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=496 end=498 bytes=09 0a text=dc.w $090a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=498 end=500 bytes=3e 1f text=dc.w $3e1f decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=500 end=502 bytes=3d 47 text=dc.w $3d47 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=502 end=504 bytes=00 0e text=dc.w $000e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=504 end=506 bytes=10 2e text=dc.w $102e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=506 end=508 bytes=fe ff text=dc.w $feff decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=508 end=510 bytes=67 52 text=dc.w $6752 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=510 end=512 bytes=4a 47 text=dc.w $4a47 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=512 end=514 bytes=57 c0 text=dc.w $57c0 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=514 end=516 bytes=4a 00 text=dc.w $4a00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=516 end=518 bytes=66 0a text=dc.w $660a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=518 end=520 bytes=72 d5 text=dc.w $72d5 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=520 end=522 bytes=b2 47 text=dc.w $b247 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=522 end=524 bytes=57 c1 text=dc.w $57c1 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=524 end=526 bytes=80 01 text=dc.w $8001 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=526 end=528 bytes=67 0c text=dc.w $670c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=528 end=530 bytes=48 6e text=dc.w $486e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=530 end=532 bytes=ff 00 text=dc.w $ff00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..212 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=212..26638 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:5
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=212 end=276 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=212 end=216 bytes=486efdf2 text=pea.l -$020E(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=216 end=220 bytes=486efdf1 text=pea.l -$020F(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=220 end=224 bytes=486efdee text=pea.l -$0212(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=224 end=228 bytes=4ead022a text=jsr $022A(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=228 end=230 bytes=101f text=move.b (a7)+,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=230 end=232 bytes=660a text=bne.b loc_0_0000001E decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=232 end=236 bytes=3f2efdee text=move.w -$0212(a6),-(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=236 end=240 bytes=4ead07ca text=jsr $07CA(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=240 end=242 bytes=6054 text=dc.b $60,$54 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=242 end=246 bytes=102efdf1 text=move.b -$020F(a6),d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=246 end=248 bytes=661a text=bne.b loc_0_0000003E decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=248 end=250 bytes=594f text=subq.w #4,a7 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=250 end=254 bytes=2f2efdf2 text=move.l -$020E(a6),-(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=254 end=258 bytes=4ead00c2 text=jsr $00C2(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=258 end=260 bytes=205f text=movea.l (a7)+,a0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=260 end=262 bytes=7000 text=moveq.l #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=262 end=264 bytes=1018 text=move.b (a0)+,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=264 end=266 bytes=6002 text=bra.b loc_0_00000038 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=266 end=268 bytes=18d8 text=move.b (a0)+,(a4)+ decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=268 end=272 bytes=51c8fffc text=dbf.w d0,loc_0_00000036 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=272 end=274 bytes=6034 text=dc.b $60,$34 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=274 end=276 bytes=5300 text=subq.b #1,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..58 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=58..15158 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:6
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=58 end=122 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=58 end=60 bytes=7400 text=moveq.l #0,d2 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=60 end=76 bytes=60722008080000006702528052802040 text=dc.b $60,$72,$20,$08,$08,$00,$00,$00,$67,$02,$52,$80,$52,$80,$20,$40 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=76 end=92 bytes=584f12182408225f328110181218225f text=dc.b $58,$4F,$12,$18,$24,$08,$22,$5F,$32,$81,$10,$18,$12,$18,$22,$5F decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=92 end=108 bytes=328108000006661e0800000566181210 text=dc.b $32,$81,$08,$00,$00,$06,$66,$1E,$08,$00,$00,$05,$66,$18,$12,$10 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=108 end=122 bytes=02010023b26df3986f0c1b7c0001 text=dc.b $02,$01,$00,$23,$B2,$6D,$F3,$98,$6F,$0C,$1B,$7C,$00,$01 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..352 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=352..4142 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:7
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=352 end=416 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=352 end=356 bytes=00000736 text=ori.b #$736,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=356 end=360 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=360 end=364 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=364 end=368 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=368 end=372 bytes=00000746 text=ori.b #$746,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=372 end=376 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=376 end=380 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=380 end=384 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=384 end=388 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=388 end=392 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=392 end=396 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=396 end=400 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=400 end=404 bytes=00000754 text=ori.b #$754,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=404 end=406 bytes=0762 text=bchg.b d3,-(a2) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=406 end=410 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=410 end=414 bytes=00000000 text=ori.b #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=414 end=416 bytes=0000 text=dc.w $0000 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..42 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=42..1852 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:8
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=42 end=106 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=42 end=44 bytes=66 ee text=dc.w $66ee decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=44 end=46 bytes=60 70 text=dc.w $6070 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=46 end=48 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=48 end=50 bytes=00 c0 text=dc.w $00c0 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=50 end=52 bytes=66 6a text=dc.w $666a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=52 end=54 bytes=26 49 text=dc.w $2649 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=54 end=56 bytes=42 41 text=dc.w $4241 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=56 end=58 bytes=12 c0 text=dc.w $12c0 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=58 end=60 bytes=51 ca text=dc.w $51ca decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=60 end=62 bytes=00 04 text=dc.w $0004 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=62 end=64 bytes=60 42 text=dc.w $6042 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=64 end=66 bytes=10 18 text=dc.w $1018 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=66 end=68 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=68 end=70 bytes=00 40 text=dc.w $0040 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=70 end=72 bytes=6d 06 text=dc.w $6d06 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=72 end=74 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=74 end=76 bytes=00 5a text=dc.w $005a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=76 end=78 bytes=6f e8 text=dc.w $6fe8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=78 end=80 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=80 end=82 bytes=00 61 text=dc.w $0061 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=82 end=84 bytes=6d 06 text=dc.w $6d06 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=84 end=86 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=86 end=88 bytes=00 7a text=dc.w $007a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=88 end=90 bytes=6f dc text=dc.w $6fdc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=90 end=92 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=92 end=94 bytes=00 30 text=dc.w $0030 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=94 end=96 bytes=6d 0a text=dc.w $6d0a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=96 end=98 bytes=0c 00 text=dc.w $0c00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=98 end=100 bytes=00 39 text=dc.w $0039 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=100 end=102 bytes=6e 04 text=dc.w $6e04 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=102 end=104 bytes=52 41 text=dc.w $5241 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=104 end=106 bytes=60 ce text=dc.w $60ce decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..712 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=712..13946 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:9
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=712 end=776 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=712 end=716 bytes=21860000 text=move.l d6,$0(a0,d0.w) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=716 end=732 bytes=6000ff3c0c06001e6d084a2efffe6700 text=dc.b $60,$00,$FF,$3C,$0C,$06,$00,$1E,$6D,$08,$4A,$2E,$FF,$FE,$67,$00 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=732 end=748 bytes=ff2e1d46ffff4886dc463c3b60064efb text=dc.b $FF,$2E,$1D,$46,$FF,$FF,$48,$86,$DC,$46,$3C,$3B,$60,$06,$4E,$FB decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=748 end=764 bytes=60020266037c0388039c03b403ca03d0 text=dc.b $60,$02,$02,$66,$03,$7C,$03,$88,$03,$9C,$03,$B4,$03,$CA,$03,$D0 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=764 end=776 bytes=03d603da03e003ec29102910 text=dc.b $03,$D6,$03,$DA,$03,$E0,$03,$EC,$29,$10,$29,$10 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..148 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=148..1542 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:10
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=148 end=212 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=148 end=150 bytes=4ed0 text=jmp (a0) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=150 end=166 bytes=8957524954454c494e4500004e56fe54 text=dc.b $89,$57,$52,$49,$54,$45,$4C,$49,$4E,$45,$00,$00,$4E,$56,$FE,$54 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=166 end=182 bytes=48e70700102decff6728082d0004ed5c text=dc.b $48,$E7,$07,$00,$10,$2D,$EC,$FF,$67,$28,$08,$2D,$00,$04,$ED,$5C decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=182 end=198 bytes=56c1c0014a00671a082d0000ed5d56c1 text=dc.b $56,$C1,$C0,$01,$4A,$00,$67,$1A,$08,$2D,$00,$00,$ED,$5D,$56,$C1 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=198 end=212 bytes=c001670e42674ead080a486d080a text=dc.b $C0,$01,$67,$0E,$42,$67,$4E,$AD,$08,$0A,$48,$6D,$08,$0A decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..836 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=836..3678 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:11
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=836 end=900 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=836 end=838 bytes=00 0c text=dc.w $000c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=838 end=840 bytes=4e d0 text=dc.w $4ed0 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=840 end=842 bytes=89 43 text=dc.w $8943 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=842 end=844 bytes=44 42 text=dc.w $4442 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=844 end=846 bytes=47 45 text=dc.w $4745 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=846 end=848 bytes=4e 54 text=dc.w $4e54 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=848 end=850 bytes=52 59 text=dc.w $5259 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=850 end=852 bytes=00 00 text=dc.w $0000 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=852 end=854 bytes=4e 56 text=dc.w $4e56 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=854 end=856 bytes=ff fc text=dc.w $fffc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=856 end=858 bytes=4e ba text=dc.w $4eba decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=858 end=860 bytes=fb bc text=dc.w $fbbc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=860 end=862 bytes=59 8f text=dc.w $598f decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=862 end=864 bytes=70 08 text=dc.w $7008 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=864 end=866 bytes=3f 00 text=dc.w $3f00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=866 end=868 bytes=4e ba text=dc.w $4eba decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=868 end=870 bytes=fc b4 text=dc.w $fcb4 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=870 end=872 bytes=20 5f text=dc.w $205f decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=872 end=874 bytes=2d 48 text=dc.w $2d48 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=874 end=876 bytes=ff fc text=dc.w $fffc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=876 end=878 bytes=30 bc text=dc.w $30bc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=878 end=880 bytes=0e 00 text=dc.w $0e00 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=880 end=882 bytes=20 2e text=dc.w $202e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=882 end=884 bytes=ff fc text=dc.w $fffc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=884 end=886 bytes=54 80 text=dc.w $5480 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=886 end=888 bytes=2d 40 text=dc.w $2d40 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=888 end=890 bytes=ff fc text=dc.w $fffc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=890 end=892 bytes=20 40 text=dc.w $2040 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=892 end=894 bytes=30 ae text=dc.w $30ae decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=894 end=896 bytes=00 08 text=dc.w $0008 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=896 end=898 bytes=20 2e text=dc.w $202e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=898 end=900 bytes=ff fc text=dc.w $fffc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..44 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=44..6928 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:12
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=44 end=108 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=44 end=46 bytes=51 c8 text=dc.w $51c8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=46 end=48 bytes=ff fc text=dc.w $fffc decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=48 end=50 bytes=20 5f text=dc.w $205f decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=50 end=52 bytes=12 d8 text=dc.w $12d8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=52 end=54 bytes=12 d8 text=dc.w $12d8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=54 end=56 bytes=12 d8 text=dc.w $12d8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=56 end=58 bytes=12 d0 text=dc.w $12d0 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=58 end=60 bytes=20 5f text=dc.w $205f decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=60 end=62 bytes=12 d8 text=dc.w $12d8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=62 end=64 bytes=12 90 text=dc.w $1290 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=64 end=66 bytes=20 42 text=dc.w $2042 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=66 end=68 bytes=4e d0 text=dc.w $4ed0 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=68 end=70 bytes=4e 56 text=dc.w $4e56 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=70 end=72 bytes=fc ba text=dc.w $fcba decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=72 end=74 bytes=48 e7 text=dc.w $48e7 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=74 end=76 bytes=0f 08 text=dc.w $0f08 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=76 end=78 bytes=28 6e text=dc.w $286e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=78 end=80 bytes=00 0e text=dc.w $000e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=80 end=82 bytes=1b 6e text=dc.w $1b6e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=82 end=84 bytes=00 0c text=dc.w $000c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=84 end=86 bytes=cb 27 text=dc.w $cb27 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=86 end=88 bytes=70 01 text=dc.w $7001 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=88 end=90 bytes=b0 6d text=dc.w $b06d decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=90 end=92 bytes=cb 1c text=dc.w $cb1c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=92 end=94 bytes=6c 16 text=dc.w $6c16 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=94 end=96 bytes=30 2d text=dc.w $302d decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=96 end=98 bytes=cb 1c text=dc.w $cb1c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=98 end=100 bytes=53 40 text=dc.w $5340 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=100 end=102 bytes=53 40 text=dc.w $5340 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=102 end=104 bytes=41 ed text=dc.w $41ed decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=104 end=106 bytes=ca d2 text=dc.w $cad2 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=106 end=108 bytes=e5 40 text=dc.w $e540 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..44 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=44..33354 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:13
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=44 end=108 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=44 end=48 bytes=0c03007a text=cmpi.b #122,d3 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=48 end=50 bytes=6e04 text=bgt.b loc_0_0000000A decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=50 end=54 bytes=04030020 text=subi.b #32,d3 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=54 end=56 bytes=14c3 text=move.b d3,(a2)+ decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=56 end=72 bytes=51c8ffea600614d951c8fffc55426d08 text=dc.b $51,$C8,$FF,$EA,$60,$06,$14,$D9,$51,$C8,$FF,$FC,$55,$42,$6D,$08 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=72 end=88 bytes=14fc002051cafffa14bc002e42421418 text=dc.b $14,$FC,$00,$20,$51,$CA,$FF,$FA,$14,$BC,$00,$2E,$42,$42,$14,$18 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=88 end=104 bytes=b4416d1842405240244f36015343b10a text=dc.b $B4,$41,$6D,$18,$42,$40,$52,$40,$24,$4F,$36,$01,$53,$43,$B1,$0A decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=104 end=108 bytes=56cbfffc text=dc.b $56,$CB,$FF,$FC decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..236 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=236..1886 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:14
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=236 end=300 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=236 end=238 bytes=c8 4a text=dc.w $c84a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=238 end=240 bytes=60 0a text=dc.w $600a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=240 end=242 bytes=20 6c text=dc.w $206c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=242 end=244 bytes=00 0c text=dc.w $000c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=244 end=246 bytes=21 6c text=dc.w $216c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=246 end=248 bytes=00 08 text=dc.w $0008 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=248 end=250 bytes=00 08 text=dc.w $0008 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=250 end=252 bytes=29 6d text=dc.w $296d decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=252 end=254 bytes=c8 3a text=dc.w $c83a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=254 end=256 bytes=00 0c text=dc.w $000c decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=256 end=258 bytes=2b 47 text=dc.w $2b47 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=258 end=260 bytes=c8 3a text=dc.w $c83a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=260 end=262 bytes=4c df text=dc.w $4cdf decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=262 end=264 bytes=18 80 text=dc.w $1880 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=264 end=266 bytes=4e 5e text=dc.w $4e5e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=266 end=268 bytes=2e 9f text=dc.w $2e9f decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=268 end=270 bytes=4e 75 text=dc.w $4e75 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=270 end=272 bytes=88 46 text=dc.w $8846 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=272 end=274 bytes=52 45 text=dc.w $5245 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=274 end=276 bytes=45 5a text=dc.w $455a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=276 end=278 bytes=4f 4e text=dc.w $4f4e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=278 end=280 bytes=45 00 text=dc.w $4500 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=280 end=282 bytes=00 00 text=dc.w $0000 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=282 end=284 bytes=4e 56 text=dc.w $4e56 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=284 end=286 bytes=ff e8 text=dc.w $ffe8 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=286 end=288 bytes=48 e7 text=dc.w $48e7 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=288 end=290 bytes=0f 18 text=dc.w $0f18 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=290 end=292 bytes=38 2e text=dc.w $382e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=292 end=294 bytes=00 08 text=dc.w $0008 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=294 end=296 bytes=28 6e text=dc.w $286e decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=296 end=298 bytes=00 0a text=dc.w $000a decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=298 end=300 bytes=70 04 text=dc.w $7004 decode=fallback_data row_kind=data fallback=preview decode failed: RuntimeError range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..96 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=96..3452 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:15
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=96 end=160 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=96 end=98 bytes=30d9 text=move.w (a1)+,(a0)+ decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=98 end=102 bytes=51c8fffc text=dbf.w d0,loc_0_00000000 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=102 end=106 bytes=206e0008 text=movea.l $0008(a6),a0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=106 end=108 bytes=2c48 text=movea.l a0,a6 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=108 end=112 bytes=4efa0406 text=jmp $406(pc) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=112 end=128 bytes=00003d6e001000124cdf10804e5e205f text=dc.b $00,$00,$3D,$6E,$00,$10,$00,$12,$4C,$DF,$10,$80,$4E,$5E,$20,$5F decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=128 end=144 bytes=defc000a4ed08a47455432424c4f434b text=dc.b $DE,$FC,$00,$0A,$4E,$D0,$8A,$47,$45,$54,$32,$42,$4C,$4F,$43,$4B decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=144 end=160 bytes=5300002e022229002820284261642062 text=dc.b $53,$00,$00,$2E,$02,$22,$29,$00,$28,$20,$28,$42,$61,$64,$20,$62 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..246 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=246..1034 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:16
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=246 end=310 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=246 end=248 bytes=5800 text=addq.b #4,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=248 end=252 bytes=00181653 text=ori.b #$1653,(a0)+ decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=252 end=254 bytes=7069 text=moveq.l #105,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=254 end=270 bytes=6c6c2066696c65207772697465206572 text=dc.b $6C,$6C,$20,$66,$69,$6C,$65,$20,$77,$72,$69,$74,$65,$20,$65,$72 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=270 end=286 bytes=726f72004e56ff50082d0002ed5a6700 text=dc.b $72,$6F,$72,$00,$4E,$56,$FF,$50,$08,$2D,$00,$02,$ED,$5A,$67,$00 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=286 end=302 bytes=00f0102deb68660000e8802deb696600 text=dc.b $00,$F0,$10,$2D,$EB,$68,$66,$00,$00,$E8,$80,$2D,$EB,$69,$66,$00 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=302 end=310 bytes=00e041eeffae43fa text=dc.b $00,$E0,$41,$EE,$FF,$AE,$43,$FA decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..100 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=100..3674 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:17
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=100 end=164 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=100 end=104 bytes=4ead0092 text=jsr $0092(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=104 end=108 bytes=486efdf2 text=pea.l -$020E(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=108 end=112 bytes=486efef2 text=pea.l -$010E(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=112 end=116 bytes=4ead0aca text=jsr $0ACA(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=116 end=118 bytes=101f text=move.b (a7)+,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=118 end=120 bytes=6702 text=beq.b loc_0_00000016 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=120 end=122 bytes=6034 text=dc.b $60,$34 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=122 end=126 bytes=486efdf2 text=pea.l -$020E(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=126 end=130 bytes=486efef2 text=pea.l -$010E(a6) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=130 end=134 bytes=4ead0ae2 text=jsr $0AE2(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=134 end=136 bytes=101f text=move.b (a7)+,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=136 end=138 bytes=6708 text=beq.b loc_0_0000002E decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=138 end=142 bytes=286c0008 text=movea.l $0008(a4),a4 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=142 end=144 bytes=4206 text=clr.b d6 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=144 end=146 bytes=6006 text=bra.b loc_0_00000034 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=146 end=150 bytes=286c0004 text=movea.l $0004(a4),a4 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=150 end=152 bytes=7c01 text=moveq.l #1,d6 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=152 end=154 bytes=200c text=move.l a4,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=154 end=164 bytes=66bc100667082047214b text=dc.b $66,$BC,$10,$06,$67,$08,$20,$47,$21,$4B decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..1562 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=1562..1974 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:18
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=structured_placeholder available=False route=unknown reason=no candidate_code range available for a bounded preview
;     previews: none
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=unknown span=4..556 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:19
;       2: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..2876 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2876..5262 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:20
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=structured_placeholder available=False route=unknown reason=no candidate_code range available for a bounded preview
;     previews: none
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..2000 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2000..6794 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:21
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=2000 end=2064 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=2000 end=2002 bytes=3e1f text=move.w (a7)+,d7 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2002 end=2004 bytes=6612 text=bne.b loc_0_00000016 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2004 end=2008 bytes=202efffc text=move.l -$0004(a6),d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2008 end=2012 bytes=91ac000c text=sub.l d0,$000C(a4) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2012 end=2016 bytes=202efffc text=move.l -$0004(a6),d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2016 end=2020 bytes=d1ac0010 text=add.l d0,$0010(a4) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2020 end=2022 bytes=6004 text=bra.b loc_0_0000001A decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2022 end=2026 bytes=39470002 text=move.w d7,$0002(a4) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2026 end=2028 bytes=4a47 text=tst.w d7 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2028 end=2030 bytes=57c3 text=seq.b d3 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2030 end=2032 bytes=4403 text=neg.b d3 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2032 end=2034 bytes=6704 text=beq.b loc_0_00000026 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2034 end=2036 bytes=7000 text=moveq.l #0,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2036 end=2038 bytes=6002 text=bra.b loc_0_00000028 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2038 end=2040 bytes=7005 text=moveq.l #5,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2040 end=2046 bytes=4cee1088fff0 text=movem.l -$0010(a6),d3/d7/a4 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2046 end=2048 bytes=4e5e text=unlk a6 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2048 end=2050 bytes=4e75 text=rts decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=2050 end=2064 bytes=885f667357726974650000004e56 text=dc.b $88,$5F,$66,$73,$57,$72,$69,$74,$65,$00,$00,$00,$4E,$56 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=unknown span=4..96 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:22
;       2: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=unknown span=4..126 status=deferred parser_use=deferred_only reason=missing_m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=0 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:23
;       2: kind=a5_world_context_placeholder ownership=0 status=deferred parser_use=unknown target=classic_mac_a5_world
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..2950 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=2950..4970 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:24
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=structured_placeholder available=False route=unknown reason=no candidate_code range available for a bounded preview
;     previews: none
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..40 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=40..246 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:25
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=40 end=104 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=40 end=42 bytes=8042 text=or.w d2,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=42 end=44 bytes=3f00 text=move.w d0,-(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=44 end=46 bytes=4857 text=pea.l (a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=46 end=50 bytes=3f3c0001 text=move.w #$1,-(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=50 end=66 bytes=a9eb548f4ed0225f205f121f741fc45f text=dc.b $A9,$EB,$54,$8F,$4E,$D0,$22,$5F,$20,$5F,$12,$1F,$74,$1F,$C4,$5F decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=66 end=82 bytes=2f09558f48573f3c0003a9eb301f4e75 text=dc.b $2F,$09,$55,$8F,$48,$57,$3F,$3C,$00,$03,$A9,$EB,$30,$1F,$4E,$75 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=82 end=98 bytes=205f61ee02409fff341feb4a02426000 text=dc.b $20,$5F,$61,$EE,$02,$40,$9F,$FF,$34,$1F,$EB,$4A,$02,$42,$60,$00 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=98 end=104 bytes=60c461d2e14a text=dc.b $60,$C4,$61,$D2,$E1,$4A decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..198 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=198..2940 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:26
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=198 end=262 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=198 end=202 bytes=4e560000 text=link a6,#0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=202 end=206 bytes=102dd297 text=move.b -$2D69(a5),d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=206 end=208 bytes=6714 text=beq.b loc_0_0000001E decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=208 end=212 bytes=486dd298 text=pea.l -$2D68(a5) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=212 end=214 bytes=7002 text=moveq.l #2,d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=214 end=216 bytes=2f00 text=move.l d0,-(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=216 end=220 bytes=4eba0202 text=jsr $202(pc) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=220 end=224 bytes=206dd298 text=movea.l -$2D68(a5),a0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=224 end=228 bytes=30bcc0da text=move.w #$C0DA,(a0) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=228 end=230 bytes=4e5e text=unlk a6 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=230 end=232 bytes=4e75 text=rts decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=232 end=248 bytes=88534554434845434b0000004e56fff0 text=dc.b $88,$53,$45,$54,$43,$48,$45,$43,$4B,$00,$00,$00,$4E,$56,$FF,$F0 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=248 end=262 bytes=48e70f18282e00102c2e00145fc0 text=dc.b $48,$E7,$0F,$18,$28,$2E,$00,$10,$2C,$2E,$00,$14,$5F,$C0 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
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
;       1: role=data span=4..204 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=204..1882 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:27
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;     listing: kind=candidate_preview available=True route=code_preview reason=bounded candidate preview; full listing remains deferred
;     previews:
;       candidate_code_preview: start=204 end=268 size=64 range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only bounded=True truncated=True reason=bounded to candidate_code range; byte-entry and relocation semantics remain unresolved
;         deferred: scope=relocation_fixups fact=macos.segment_loader.relocation_fixups.deferred status=deferred parser_use=deferred_only reason=Segment Loader relocation/fixup interpretation is not yet represented by the parser
;         row: offset=204 end=208 bytes=48e780c0 text=movem.l d0/a0-a1,-(a7) decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=208 end=210 bytes=4240 text=clr.w d0 decode=decoded row_kind=instruction range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=210 end=226 bytes=610004d0b0fc00006602a9ff598f2f08 text=dc.b $61,$00,$04,$D0,$B0,$FC,$00,$00,$66,$02,$A9,$FF,$59,$8F,$2F,$08 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=226 end=242 bytes=a9a5205fd0f8093490fc001043fa0046 text=dc.b $A9,$A5,$20,$5F,$D0,$F8,$09,$34,$90,$FC,$00,$10,$43,$FA,$00,$46 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=242 end=258 bytes=22884cdf03014e75800e73657475705f text=dc.b $22,$88,$4C,$DF,$03,$01,$4E,$75,$80,$0E,$73,$65,$74,$75,$70,$5F decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only
;         row: offset=258 end=268 bytes=6a745f6c696d69740000 text=dc.b $6A,$74,$5F,$6C,$69,$6D,$69,$74,$00,$00 decode=decoded_data row_kind=data range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate parser_use=candidate_only

; Non-CODE resource placeholders
;   type acur: 1 resource(s), structured placeholder
;   type CURS: 4 resource(s), structured placeholder
;   type cmdo: 1 resource(s), structured placeholder
;   type vers: 1 resource(s), structured placeholder
; Executable resource placeholders
;   executable_resource_placeholder: type=acur id=unknown name=unknown count=1 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:acur:* status=candidate reason=non-CODE resource metadata is inventory-only and not executable CODE
;     reference_site=resource_type_inventory type=acur id=unknown source_offset=unknown reason=No direct CODE source reference site is known for this resource type yet.
;   executable_resource_placeholder: type=CURS id=unknown name=unknown count=4 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:CURS:* status=validated reason=CURS type-level layout is cited; payload bitmap/hotspot bytes are not decoded
;     reference_site=resource_type_inventory type=CURS id=unknown source_offset=unknown reason=No direct CODE source reference site is known for this resource type yet.
;   executable_resource_placeholder: type=cmdo id=unknown name=unknown count=1 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:cmdo:* status=candidate reason=non-CODE resource metadata is inventory-only and not executable CODE
;     reference_site=resource_type_inventory type=cmdo id=unknown source_offset=unknown reason=No direct CODE source reference site is known for this resource type yet.
;   executable_resource_placeholder: type=vers id=unknown name=unknown count=1 size=unknown sha256=unknown identity=macos-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:vers:* status=candidate reason=non-CODE resource metadata is inventory-only and not executable CODE
;     reference_site=resource_type_inventory type=vers id=unknown source_offset=unknown reason=No direct CODE source reference site is known for this resource type yet.

; Unsupported Mac Segment Loader/runtime areas
;   byte-for-byte MPW Link/Rez roundtrip
;   complete Segment Loader behavior
;   overflow_extents
;   segment_loader_relocations
;   source-to-CODE segment mapping

; Selected CODE segment
;   source_kind: macos_code_resource
;   backend: macos-code
;   resource_type: CODE
;   id: 1
;   name: Main
;   fork: resource
;   payload_size: 29024
;   code_entry_offset: 40
;   code_bytes_size: 28984
;   payload_sha256: 4a543f6fd1c542fccd38ec9f469b06f65c797dfd8b226fefc9f576faafbe70f5
;   code_bytes_sha256: 4633044ba0d2a816a0e482a9fb3b65bcd8daf699882df8f95939ad018f51879c
;   restored_source_model:
;     model=restored_source_model_v1 round_trip_required=false
;     coverage ok=true gaps=0 overlaps=0 unknown_detail=0
;     code_resource=CODE 1 name=unknown
;     a5_world status=deferred parser_use=unknown
;     ownership_ranges:
;       0: role=metadata span=0..4 status=validated parser_use=accepted_parser_output reason=nonzero_code_segment_header
;       1: role=data span=4..40 status=candidate parser_use=candidate_only reason=prefix_before_stack_entry
;       2: role=candidate_code span=40..29024 status=candidate parser_use=candidate_only reason=m68k_movea_l_stack_to_a0_entry
;     source_reference_records:
;       0: kind=segment_loader_fixup_placeholder ownership=2 status=deferred parser_use=deferred_only target=unresolved_segment_loader_fixup
;       1: kind=code0_dispatch_reference ownership=unknown status=validated parser_use=accepted_parser_output target=CODE:1
;       2: kind=a5_world_context_placeholder ownership=2 status=deferred parser_use=unknown target=classic_mac_a5_world
;   listing_rows: 1814

; CODE 1 Main listing follows. Offsets are local to the selected CODE resource code bytes.
; Classic Mac OS CODE resource listing
; source kind: macos_code_resource
; HFS path: MPW-GM/MPW/Tools/Asm
; fork: resource
; resource: CODE 1 Main
; classified_range: candidate_code payload[40..29024) evidence=m68k_movea_l_stack_to_a0_entry

loc_0_00000000:
	movea.l (a7)+,a0
	move.l a7,d0
	sub.l $0114.w,d0
	cmpi.l #512,d0
	sge.b d0
	neg.b d0
	move.b d0,(a7)
	jmp (a0)
	dc.b $20,$5F,$22,$57,$2E,$88,$4E,$D1,$20,$5F,$30,$1F,$0C,$00,$00,$61
	dc.b $6D,$0A,$0C,$00,$00,$7A,$6E,$04,$04,$00,$00,$20,$3E,$80,$4E,$D0
	dc.b $20,$5F,$30,$1F,$0C,$00,$00,$41,$6D,$0A,$0C,$00,$00,$5A,$6E,$04
	dc.b $06,$00,$00,$20,$3E,$80,$4E,$D0,$22,$5F,$20,$5F,$42,$41,$12,$18
	dc.b $60,$14,$10,$10,$0C,$00,$00,$61,$6D,$0A,$0C,$00,$00,$7A,$6E,$04
	dc.b $04,$00,$00,$20,$10,$C0,$51,$C9,$FF,$EA,$4E,$D1,$22,$5F,$20,$5F
	dc.b $42,$41,$12,$18,$60,$14,$10,$10,$0C,$00,$00,$41,$6D,$0A,$0C,$00
	dc.b $00,$5A,$6E,$04,$06,$00,$00,$20,$10,$C0,$51,$C9,$FF,$EA,$4E,$D1
	dc.b $24,$1F,$22,$5F,$20,$57,$2E,$82,$42,$42,$14,$10,$B3,$08,$67,$2E
	dc.b $20,$5F,$42,$17,$4E,$D0,$10,$18,$0C,$00,$00,$61,$6D,$0A,$0C,$00
	dc.b $00,$7A,$6E,$04,$04,$00,$00,$20,$12,$19,$0C,$01,$00,$61,$6D,$0A
	dc.b $0C,$01,$00,$7A,$6E,$04,$04,$01,$00,$20,$B2,$00,$66,$D2,$51,$CA
	dc.b $FF,$D6,$20,$5F,$1E,$BC,$00,$01,$4E,$D0,$24,$1F,$20,$5F,$22,$48
	dc.b $42,$41,$12,$18,$60,$0E,$10,$18,$0C,$00,$00,$20,$67,$06,$0C,$00
	dc.b $00,$09,$66,$0A,$51,$C9,$FF,$F0,$42,$11,$20,$42,$4E,$D0,$52,$41
	dc.b $B2,$11,$67,$0C,$12,$C1,$12,$C0,$60,$02,$12,$D8,$51,$C9,$FF,$FC
	dc.b $20,$42,$4E,$D0,$22,$5F,$20,$5F,$42,$41,$12,$10,$70,$20,$74,$09
	dc.b $60,$0C,$B0,$30,$10,$01,$67,$06,$B4,$30,$10,$01,$66,$04,$51,$C9
	dc.b $FF,$F2,$52,$41,$10,$81,$4E,$D1,$2F,$2F,$00,$04,$4E,$BA,$FF,$9C
	dc.b $4E,$FA,$FF,$D2,$24,$1F,$22,$5F,$20,$5F,$42,$40,$10,$10,$42,$41
	dc.b $12,$19,$D3,$18,$D0,$C0,$60,$02,$10,$D9,$51,$C9,$FF,$FC,$20,$42
	dc.b $4E,$D0,$24,$1F,$22,$5F,$20,$5F,$42,$41,$12,$10,$12,$D8,$51,$C9
	dc.b $FF,$FC,$20,$42,$4E,$D0,$24,$1F,$32,$1F,$30,$1F,$22,$5F,$20,$5F
	dc.b $12,$C1,$D0,$C0,$60,$02,$12,$D8,$51,$C9,$FF,$FC,$20,$42,$4E,$D0
	dc.b $24,$1F,$30,$1F,$22,$5F,$20,$5F,$6E,$04,$60,$06,$12,$D8,$51,$C8
	dc.b $FF,$FC,$20,$42,$4E,$D0,$42,$42,$60,$02,$74,$01,$22,$5F,$32,$1F
	dc.b $20,$5F,$30,$1F,$1E,$82,$14,$10,$67,$28,$4A,$41,$6B,$28,$67,$22
	dc.b $94,$41,$6C,$06,$42,$42,$14,$10,$60,$18,$D0,$C1,$32,$02,$4A,$17
	dc.b $66,$08,$B0,$18,$57,$C9,$FF,$FC,$60,$06,$B0,$18,$56,$C9,$FF,$FC
	dc.b $94,$41,$3E,$82,$4E,$D1,$44,$41,$B2,$42,$6F,$04,$72,$01,$60,$1C
	dc.b $D0,$C1,$52,$48,$53,$41,$34,$01,$4A,$17,$66,$08,$B0,$20,$57,$C9
	dc.b $FF,$FC,$60,$06,$B0,$20,$56,$C9,$FF,$FC,$92,$42,$3E,$81,$4E,$D1
	dc.b $20,$1F,$42,$A7,$2F,$00,$4E,$56,$FF,$F4,$48,$E7,$07,$18,$47,$D6
	dc.b $42,$02,$2A,$2E,$00,$0C,$66,$08,$17,$3C,$00,$30,$7C,$01,$60,$66
	dc.b $4A,$2E,$00,$08,$67,$2A,$72,$07,$42,$46,$10,$05,$02,$40,$00,$0F
	dc.b $17,$3B,$00,$0E,$52,$46,$E8,$8D,$67,$4C,$51,$C9,$FF,$EE,$60,$46
	dc.b $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46
	dc.b $7E,$0A,$42,$46,$4A,$85,$6C,$04,$74,$01,$44,$85,$32,$05,$42,$45
	dc.b $48,$45,$8A,$C7,$20,$05,$30,$01,$80,$C7,$48,$45,$3A,$00,$48,$40
	dc.b $06,$40,$00,$30,$17,$00,$52,$46,$4A,$85,$66,$E0,$4A,$02,$67,$06
	dc.b $17,$3C,$00,$2D,$52,$46,$49,$ED,$C7,$34,$2D,$4C,$00,$10,$20,$4C
	dc.b $52,$48,$12,$3C,$00,$20,$3E,$2E,$00,$0A,$6C,$06,$44,$47,$12,$3C
	dc.b $00,$30,$9E,$46,$6F,$20,$0C,$01,$00,$30,$66,$12,$4A,$02,$67,$0E
	dc.b $10,$FC,$00,$2D,$16,$BC,$00,$30,$55,$47,$6B,$0A,$10,$C1,$51,$CF
	dc.b $FF,$FC,$60,$02,$10,$DB,$51,$CE,$FF,$FC,$20,$08,$90,$8C,$53,$00
	dc.b $18,$80,$4C,$DF,$18,$E0,$4E,$5E,$20,$5F,$50,$4F,$4E,$D0,$4E,$56
	dc.b $FE,$FE,$48,$E7,$07,$10,$47,$EE,$FE,$FE,$2F,$2E,$00,$0C,$2F,$0B
	dc.b $4E,$BA,$FE,$60,$2F,$0B,$4E,$BA,$FE,$30,$72,$00,$42,$05,$42,$2E
	dc.b $FF,$FE,$7C,$00,$42,$47,$1E,$1B,$66,$04,$7A,$01,$60,$6E,$1C,$13
	dc.b $0C,$06,$00,$2B,$67,$0A,$0C,$06,$00,$2D,$66,$10,$50,$EE,$FF,$FE
	dc.b $52,$4B,$53,$47,$66,$06,$7A,$02,$72,$00,$60,$50,$53,$47,$1C,$1B
	dc.b $0C,$06,$00,$30,$56,$CF,$FF,$F8,$67,$42,$42,$42,$0C,$06,$00,$30
	dc.b $6D,$E4,$0C,$06,$00,$39,$6E,$DE,$0C,$02,$00,$09,$6F,$06,$7A,$03
	dc.b $72,$00,$60,$28,$66,$10,$0C,$81,$0C,$CC,$CC,$CC,$6E,$F0,$66,$06
	dc.b $0C,$06,$00,$38,$6E,$E8,$D2,$81,$20,$01,$E5,$89,$D2,$80,$04,$46
	dc.b $00,$30,$D2,$86,$52,$42,$1C,$1B,$51,$CF,$FF,$C2,$4A,$2E,$FF,$FE
	dc.b $67,$02,$44,$81,$2D,$41,$00,$10,$20,$6E,$00,$08,$10,$85,$4C,$DF
	dc.b $08,$E0,$4E,$5E,$20,$5F,$50,$4F,$4E,$D0,$20,$5F,$22,$5F,$42,$40
	dc.b $10,$11,$52,$00,$14,$00,$72,$00,$32,$19,$E2,$08,$55,$40,$6D,$08
	dc.b $E7,$59,$D2,$59,$51,$C8,$FF,$FA,$02,$42,$00,$01,$67,$06,$14,$11
	dc.b $E7,$59,$D2,$42,$82,$FC,$00,$FB,$48,$41,$3E,$81,$4E,$D0,$59,$4F
	dc.b $2F,$2F,$00,$14,$42,$40,$20,$6F,$00,$14,$10,$10,$32,$2F,$00,$0E
	dc.b $67,$12,$08,$01,$00,$01,$66,$0C,$08,$01,$00,$0C,$67,$0C,$02,$41
	dc.b $4E,$00,$67,$06,$06,$40,$00,$17,$60,$04,$06,$40,$00,$0F,$3F,$00
	dc.b $4E,$AD,$07,$8A,$22,$1F,$67,$46,$22,$6F,$00,$10,$22,$69,$00,$18
	dc.b $30,$2F,$00,$04,$D0,$40,$D0,$40,$D2,$C0,$20,$41,$20,$91,$22,$88
	dc.b $21,$6F,$00,$08,$00,$04,$31,$6F,$00,$06,$00,$08,$42,$68,$00,$0A
	dc.b $41,$E8,$00,$0C,$22,$6F,$00,$0C,$42,$40,$10,$11,$10,$D9,$51,$C8
	dc.b $FF,$FC,$20,$09,$08,$00,$00,$00,$67,$02,$52,$89,$42,$51,$20,$5F
	dc.b $4F,$EF,$00,$10,$2E,$81,$4E,$D0,$20,$5F,$30,$1F,$2F,$08,$60,$0C
	dc.b $55,$4F,$2F,$2F,$00,$10,$4E,$BA,$FF,$32,$30,$1F,$4E,$56,$00,$00
	dc.b $2F,$0A,$2F,$0B,$2F,$0C,$24,$6E,$00,$16,$34,$2A,$00,$10,$24,$6A
	dc.b $00,$18,$D0,$40,$D0,$40,$D4,$C0,$26,$4A,$28,$6E,$00,$12,$22,$12
	dc.b $67,$2A,$24,$41,$4A,$42,$6B,$08,$08,$2A,$00,$00,$00,$09,$66,$EE
	dc.b $43,$EA,$00,$0C,$20,$4C,$42,$40,$10,$10,$B3,$08,$56,$C8,$FF,$FC
	dc.b $66,$DC,$20,$6E,$00,$08,$70,$01,$10,$80,$60,$6C,$20,$6E,$00,$08
	dc.b $42,$10,$59,$4F,$2F,$2E,$00,$16,$42,$40,$10,$14,$32,$2E,$00,$0C
	dc.b $67,$12,$08,$01,$00,$01,$66,$0C,$08,$01,$00,$0C,$67,$0C,$02,$41
	dc.b $4E,$00,$67,$06,$06,$40,$00,$17,$60,$04,$06,$40,$00,$0F,$3F,$00
	dc.b $4E,$AD,$07,$8A,$22,$1F,$67,$30,$22,$41,$22,$93,$26,$89,$23,$6E
	dc.b $00,$0E,$00,$04,$33,$6E,$00,$0C,$00,$08,$42,$69,$00,$0A,$43,$E9
	dc.b $00,$0C,$42,$40,$10,$14,$12,$DC,$51,$C8,$FF,$FC,$20,$09,$08,$00
	dc.b $00,$00,$67,$02,$52,$89,$42,$51,$28,$5F,$26,$5F,$24,$5F,$4E,$5E
	dc.b $20,$5F,$4F,$EF,$00,$12,$2E,$81,$4E,$D0,$20,$5F,$30,$1F,$2F,$08
	dc.b $60,$0C,$55,$4F,$2F,$2F,$00,$0E,$4E,$BA,$FE,$50,$30,$1F,$4E,$56
	dc.b $00,$00,$2F,$0A,$2F,$0B,$26,$6E,$00,$10,$42,$42,$14,$13,$D0,$40
	dc.b $D0,$40,$24,$6E,$00,$14,$4A,$6A,$00,$10,$24,$6A,$00,$18,$D4,$C0
	dc.b $6A,$18,$22,$12,$67,$42,$24,$41,$43,$EA,$00,$0C,$20,$4B,$30,$02
	dc.b $B3,$08,$56,$C8,$FF,$FC,$66,$EA,$60,$1E,$22,$12,$67,$2A,$24,$41
	dc.b $08,$2A,$00,$00,$00,$09,$66,$F2,$43,$EA,$00,$0C,$20,$4B,$30,$02
	dc.b $B3,$08,$56,$C8,$FF,$FC,$66,$E2,$20,$6E,$00,$0C,$20,$AA,$00,$04
	dc.b $20,$6E,$00,$08,$30,$AA,$00,$08,$26,$5F,$24,$5F,$4E,$5E,$20,$5F
	dc.b $4F,$EF,$00,$10,$2E,$81,$4E,$D0,$20,$5F,$30,$1F,$2F,$08,$60,$0C
	dc.b $55,$4F,$2F,$2F,$00,$14,$4E,$BA,$FD,$C2,$30,$1F,$4E,$56,$00,$00
	dc.b $2F,$0A,$2F,$0B,$2F,$0C,$24,$6E,$00,$1A,$24,$6A,$00,$18,$D0,$40
	dc.b $D0,$40,$D4,$C0,$26,$4A,$28,$6E,$00,$16,$22,$12,$67,$52,$24,$41
	dc.b $43,$EA,$00,$0C,$20,$4C,$42,$40,$10,$10,$B3,$08,$56,$C8,$FF,$FC
	dc.b $66,$E8,$30,$2A,$00,$08,$08,$00,$00,$00,$67,$DE,$20,$6A,$00,$04
	dc.b $02,$40,$0A,$00,$67,$08,$20,$68,$00,$04,$20,$68,$00,$02,$41,$E8
	dc.b $00,$0C,$22,$6E,$00,$12,$43,$E9,$00,$0C,$42,$40,$10,$10,$B3,$08
	dc.b $56,$C8,$FF,$FC,$66,$B4,$20,$6E,$00,$08,$70,$01,$10,$80,$60,$74
	dc.b $20,$6E,$00,$08,$42,$10,$59,$4F,$2F,$2E,$00,$1A,$42,$40,$10,$14
	dc.b $32,$2E,$00,$10,$0C,$01,$00,$01,$67,$12,$08,$01,$00,$01,$66,$0C
	dc.b $08,$01,$00,$0C,$67,$0C,$02,$41,$4E,$00,$67,$06,$06,$40,$00,$17
	dc.b $60,$04,$06,$40,$00,$13,$3F,$00,$4E,$AD,$07,$8A,$22,$1F,$67,$34
	dc.b $22,$41,$22,$93,$26,$89,$23,$6E,$00,$12,$00,$04,$33,$6E,$00,$10
	dc.b $00,$08,$42,$69,$00,$0A,$43,$E9,$00,$0C,$42,$40,$10,$14,$12,$DC
	dc.b $51,$C8,$FF,$FC,$20,$09,$02,$40,$00,$01,$67,$02,$52,$49,$42,$59
	dc.b $22,$AE,$00,$0C,$28,$5F,$26,$5F,$24,$5F,$4E,$5E,$20,$5F,$4F,$EF
	dc.b $00,$16,$2E,$81,$4E,$D0,$20,$5F,$30,$1F,$2F,$08,$60,$0C,$55,$4F
	dc.b $2F,$2F,$00,$12,$4E,$BA,$FC,$B4,$30,$1F,$4E,$56,$00,$00,$2F,$0A
	dc.b $2F,$0B,$2F,$0C,$24,$6E,$00,$1C,$24,$6A,$00,$18,$D0,$40,$D0,$40
	dc.b $D4,$C0,$26,$6E,$00,$14,$28,$6E,$00,$18,$22,$12,$67,$6A,$24,$41
	dc.b $43,$EA,$00,$0C,$20,$4B,$42,$40,$10,$10,$B3,$08,$56,$C8,$FF,$FC
	dc.b $66,$E8,$30,$2A,$00,$08,$08,$00,$00,$00,$67,$DE,$24,$09,$20,$6A
	dc.b $00,$04,$30,$2A,$00,$08,$02,$40,$0A,$00,$67,$08,$20,$68,$00,$04
	dc.b $20,$68,$00,$02,$41,$E8,$00,$0C,$22,$4C,$42,$40,$10,$10,$B3,$08
	dc.b $56,$C8,$FF,$FC,$66,$B4,$20,$6E,$00,$10,$20,$AA,$00,$04,$20,$6E
	dc.b $00,$0C,$30,$AA,$00,$08,$22,$42,$02,$42,$00,$01,$67,$02,$52,$49
	dc.b $42,$59,$20,$6E,$00,$08,$20,$91,$28,$5F,$26,$5F,$24,$5F,$4E,$5E
	dc.b $20,$5F,$4F,$EF,$00,$18,$2E,$81,$4E,$D0,$20,$5F,$22,$5F,$43,$E9
	dc.b $00,$0C,$42,$40,$10,$19,$D2,$C0,$02,$40,$00,$01,$66,$02,$52,$49
	dc.b $54,$49,$2E,$89,$4E,$D0,$22,$5F,$20,$57,$2E,$89,$2F,$0A,$2F,$08
	dc.b $52,$48,$43,$ED,$F6,$42,$24,$49,$42,$1A,$42,$6D,$F5,$40,$42,$6D
	dc.b $F4,$3E,$42,$01,$42,$40,$10,$18,$66,$0E,$42,$12,$24,$0A,$94,$89
	dc.b $53,$02,$12,$82,$60,$00,$02,$C8,$0C,$00,$00,$20,$67,$00,$00,$BE
	dc.b $0C,$00,$00,$09,$67,$00,$00,$B6,$0C,$00,$00,$3A,$67,$00,$00,$AE
	dc.b $0C,$00,$00,$3B,$67,$00,$02,$8A,$14,$C0,$4A,$01,$66,$08,$0C,$00
	dc.b $00,$26,$66,$02,$72,$01,$10,$18,$67,$C0,$4A,$01,$67,$CA,$0C,$00
	dc.b $00,$27,$66,$0E,$14,$C0,$10,$18,$67,$B0,$0C,$00,$00,$27,$66,$F4
	dc.b $60,$D6,$0C,$00,$00,$5B,$66,$34,$74,$01,$14,$C0,$10,$18,$67,$9A
	dc.b $0C,$00,$00,$5B,$66,$04,$52,$42,$60,$F0,$0C,$00,$00,$5D,$66,$06
	dc.b $53,$42,$67,$B4,$60,$E4,$0C,$00,$00,$27,$66,$DE,$14,$C0,$10,$18
	dc.b $67,$00,$FF,$78,$0C,$00,$00,$27,$66,$F2,$60,$CE,$0C,$00,$00,$28
	dc.b $66,$00,$FF,$76,$74,$01,$14,$C0,$10,$18,$67,$00,$FF,$5E,$0C,$00
	dc.b $00,$28,$66,$04,$52,$42,$60,$EE,$0C,$00,$00,$29,$66,$08,$53,$42
	dc.b $67,$00,$FF,$76,$60,$E0,$0C,$00,$00,$27,$66,$DA,$14,$C0,$10,$18
	dc.b $67,$00,$FF,$38,$0C,$00,$00,$27,$66,$F2,$60,$CA,$24,$0A,$94,$89
	dc.b $53,$02,$12,$82,$42,$12,$10,$18,$0C,$00,$00,$20,$67,$F8,$0C,$00
	dc.b $00,$09,$67,$F2,$43,$ED,$F5,$40,$24,$49,$42,$1A,$4A,$00,$67,$00
	dc.b $FF,$0A,$42,$01,$0C,$00,$00,$3B,$67,$00,$01,$B6,$14,$C0,$4A,$01
	dc.b $66,$08,$0C,$00,$00,$26,$66,$02,$72,$01,$10,$18,$67,$00,$FE,$EC
	dc.b $0C,$00,$00,$2E,$66,$12,$4A,$01,$66,$DA,$42,$12,$24,$0A,$94,$89
	dc.b $53,$02,$12,$82,$60,$00,$00,$D0,$0C,$00,$00,$20,$67,$00,$01,$82
	dc.b $0C,$00,$00,$09,$67,$00,$01,$7A,$0C,$00,$00,$3A,$67,$00,$00,$9A
	dc.b $4A,$01,$67,$B0,$0C,$00,$00,$27,$66,$10,$14,$C0,$10,$18,$67,$00
	dc.b $FE,$AA,$0C,$00,$00,$27,$66,$F2,$60,$9A,$0C,$00,$00,$5B,$66,$38
	dc.b $74,$01,$14,$C0,$10,$18,$67,$00,$FE,$92,$0C,$00,$00,$5B,$66,$04
	dc.b $52,$42,$60,$EE,$0C,$00,$00,$5D,$66,$08,$53,$42,$67,$00,$FF,$76
	dc.b $60,$E0,$0C,$00,$00,$27,$66,$DA,$14,$C0,$10,$18,$67,$00,$FE,$6C
	dc.b $0C,$00,$00,$27,$66,$F2,$60,$CA,$0C,$00,$00,$28,$66,$00,$FF,$56
	dc.b $74,$01,$14,$C0,$10,$18,$67,$00,$FE,$52,$0C,$00,$00,$28,$66,$04
	dc.b $52,$42,$60,$EE,$0C,$00,$00,$29,$66,$08,$53,$42,$67,$00,$FF,$36
	dc.b $60,$E0,$0C,$00,$00,$27,$66,$DA,$14,$C0,$10,$18,$67,$00,$FE,$2C
	dc.b $0C,$00,$00,$27,$66,$F2,$60,$CA,$4A,$2D,$F6,$42,$66,$00,$FF,$16
	dc.b $24,$0A,$94,$89,$53,$02,$12,$82,$45,$ED,$F6,$42,$14,$D9,$51,$CA
	dc.b $FF,$FC,$60,$00,$FE,$E0,$43,$ED,$F4,$3E,$24,$49,$42,$1A,$0C,$00
	dc.b $00,$3B,$67,$00,$00,$AC,$10,$18,$67,$00,$FD,$F0,$0C,$00,$00,$20
	dc.b $67,$00,$00,$9E,$0C,$00,$00,$09,$67,$00,$00,$96,$0C,$00,$00,$27
	dc.b $66,$10,$14,$C0,$10,$18,$67,$00,$FD,$D2,$0C,$00,$00,$27,$66,$F2
	dc.b $60,$78,$0C,$00,$00,$5B,$66,$36,$74,$01,$14,$C0,$10,$18,$67,$00
	dc.b $FD,$BA,$0C,$00,$00,$5B,$66,$04,$52,$42,$60,$EE,$0C,$00,$00,$5D
	dc.b $66,$06,$53,$42,$67,$54,$60,$E2,$0C,$00,$00,$27,$66,$DC,$14,$C0
	dc.b $10,$18,$67,$00,$FD,$96,$0C,$00,$00,$27,$66,$F2,$60,$CC,$0C,$00
	dc.b $00,$28,$66,$36,$74,$01,$14,$C0,$10,$18,$67,$00,$FD,$7E,$0C,$00
	dc.b $00,$28,$66,$04,$52,$42,$60,$EE,$0C,$00,$00,$29,$66,$06,$53,$42
	dc.b $67,$18,$60,$E2,$0C,$00,$00,$27,$66,$DC,$14,$C0,$10,$18,$67,$00
	dc.b $FD,$5A,$0C,$00,$00,$27,$66,$F2,$60,$CC,$14,$C0,$60,$00,$FF,$50
	dc.b $42,$12,$24,$0A,$94,$89,$53,$02,$12,$82,$0C,$00,$00,$3B,$67,$0E
	dc.b $10,$18,$0C,$00,$00,$20,$67,$F8,$0C,$00,$00,$09,$67,$F2,$2B,$48
	dc.b $FB,$C2,$22,$5F,$91,$C9,$3B,$40,$FB,$C8,$66,$0C,$53,$48,$3B,$48
	dc.b $FB,$C6,$53,$AD,$FB,$C2,$60,$04,$3B,$48,$FB,$C6,$24,$5F,$4E,$75
	dc.b $2F,$0A,$3F,$03,$3F,$04,$76,$20,$78,$09,$41,$ED,$FC,$E9,$43,$ED
	dc.b $FA,$BE,$24,$49,$42,$1A,$42,$6D,$F9,$BA,$42,$6D,$F8,$B6,$42,$2D
	dc.b $FA,$BD,$42,$2D,$F9,$B9,$42,$2D,$F8,$B5,$42,$2D,$F8,$38,$42,$2D
	dc.b $F7,$BE,$42,$2D,$F7,$44,$72,$01,$42,$40,$10,$18,$66,$0E,$42,$12
	dc.b $24,$0A,$94,$89,$53,$02,$12,$82,$60,$00,$03,$12,$B0,$03,$67,$04
	dc.b $B0,$04,$66,$08,$43,$ED,$F8,$38,$60,$00,$00,$D4,$0C,$00,$00,$3B
	dc.b $67,$00,$02,$CE,$0C,$00,$00,$3A,$67,$00,$00,$B8,$14,$C0,$4A,$2D
	dc.b $FA,$BD,$66,$0A,$0C,$00,$00,$26,$66,$04,$1B,$41,$FA,$BD,$10,$18
	dc.b $67,$BC,$B0,$03,$67,$00,$00,$9C,$B0,$04,$67,$00,$00,$96,$4A,$2D
	dc.b $FA,$BD,$67,$C8,$0C,$00,$00,$27,$66,$0E,$14,$C0,$10,$18,$67,$9E
	dc.b $0C,$00,$00,$27,$66,$F4,$60,$C4,$0C,$00,$00,$5B,$66,$34,$74,$01
	dc.b $14,$C0,$10,$18,$67,$88,$0C,$00,$00,$5B,$66,$04,$52,$42,$60,$F0
	dc.b $0C,$00,$00,$5D,$66,$06,$53,$42,$67,$A2,$60,$E4,$0C,$00,$00,$27
	dc.b $66,$DE,$14,$C0,$10,$18,$67,$00,$FF,$66,$0C,$00,$00,$27,$66,$F2
	dc.b $60,$CE,$0C,$00,$00,$28,$66,$00,$FF,$74,$74,$01,$14,$C0,$10,$18
	dc.b $67,$00,$FF,$4C,$0C,$00,$00,$28,$66,$04,$52,$42,$60,$EE,$0C,$00
	dc.b $00,$29,$66,$08,$53,$42,$67,$00,$FF,$64,$60,$E0,$0C,$00,$00,$27
	dc.b $66,$DA,$14,$C0,$10,$18,$67,$00,$FF,$26,$0C,$00,$00,$27,$66,$F2
	dc.b $60,$CA,$24,$0A,$94,$89,$53,$02,$12,$82,$43,$ED,$F7,$BE,$42,$12
	dc.b $24,$49,$42,$1A,$14,$C0,$10,$18,$B0,$03,$67,$F8,$B0,$04,$67,$F4
	dc.b $24,$0A,$94,$89,$53,$02,$12,$82,$43,$ED,$F9,$BA,$24,$49,$42,$1A
	dc.b $4A,$00,$67,$00,$FE,$EA,$0C,$00,$00,$3B,$67,$00,$01,$D4,$14,$C0
	dc.b $4A,$2D,$F9,$B9,$66,$0A,$0C,$00,$00,$26,$66,$04,$1B,$41,$F9,$B9
	dc.b $10,$18,$67,$00,$FE,$CA,$0C,$00,$00,$2E,$66,$14,$4A,$2D,$F9,$B9
	dc.b $66,$D4,$42,$12,$24,$0A,$94,$89,$53,$02,$12,$82,$60,$00,$00,$D8
	dc.b $B0,$03,$67,$00,$01,$9C,$B0,$04,$67,$00,$01,$96,$0C,$00,$00,$3A
	dc.b $67,$00,$00,$9C,$4A,$2D,$F9,$B9,$67,$AC,$0C,$00,$00,$27,$66,$10
	dc.b $14,$C0,$10,$18,$67,$00,$FE,$88,$0C,$00,$00,$27,$66,$F2,$60,$96
	dc.b $0C,$00,$00,$5B,$66,$38,$74,$01,$14,$C0,$10,$18,$67,$00,$FE,$70
	dc.b $0C,$00,$00,$5B,$66,$04,$52,$42,$60,$EE,$0C,$00,$00,$5D,$66,$08
	dc.b $53,$42,$67,$00,$FF,$72,$60,$E0,$0C,$00,$00,$27,$66,$DA,$14,$C0
	dc.b $10,$18,$67,$00,$FE,$4A,$0C,$00,$00,$27,$66,$F2,$60,$CA,$0C,$00
	dc.b $00,$28,$66,$00,$FF,$52,$74,$01,$14,$C0,$10,$18,$67,$00,$FE,$30
	dc.b $0C,$00,$00,$28,$66,$04,$52,$42,$60,$EE,$0C,$00,$00,$29,$66,$08
	dc.b $53,$42,$67,$00,$FF,$32,$60,$E0,$0C,$00,$00,$27,$66,$DA,$14,$C0
	dc.b $10,$18,$67,$00,$FE,$0A,$0C,$00,$00,$27,$66,$F2,$60,$CA,$4A,$2D
	dc.b $FA,$BE,$66,$00,$FF,$12,$24,$0A,$94,$89,$53,$02,$12,$82,$45,$ED
	dc.b $FA,$BE,$14,$D9,$51,$CA,$FF,$FC,$1B,$6D,$F9,$B9,$FA,$BD,$42,$2D
	dc.b $F9,$B9,$60,$00,$FE,$C6,$43,$ED,$F8,$B6,$24,$49,$42,$1A,$0C,$00
	dc.b $00,$3B,$67,$00,$00,$BC,$10,$18,$67,$00,$FD,$C4,$B0,$03,$67,$00
	dc.b $00,$B0,$B0,$04,$67,$00,$00,$AA,$0C,$00,$00,$27,$66,$10,$14,$C0
	dc.b $10,$18,$67,$00,$FD,$AA,$0C,$00,$00,$27,$66,$F2,$60,$78,$0C,$00
	dc.b $00,$5B,$66,$36,$74,$01,$14,$C0,$10,$18,$67,$00,$FD,$92,$0C,$00
	dc.b $00,$5B,$66,$04,$52,$42,$60,$EE,$0C,$00,$00,$5D,$66,$06,$53,$42
	dc.b $67,$54,$60,$E2,$0C,$00,$00,$27,$66,$DC,$14,$C0,$10,$18,$67,$00
	dc.b $FD,$6E,$0C,$00,$00,$27,$66,$F2,$60,$CC,$0C,$00,$00,$28,$66,$36
	dc.b $74,$01,$14,$C0,$10,$18,$67,$00,$FD,$56,$0C,$00,$00,$28,$66,$04
	dc.b $52,$42,$60,$EE,$0C,$00,$00,$29,$66,$06,$53,$42,$67,$18,$60,$E2
	dc.b $0C,$00,$00,$27,$66,$DC,$14,$C0,$10,$18,$67,$00,$FD,$32,$0C,$00
	dc.b $00,$27,$66,$F2,$60,$CC,$14,$C0,$4A,$2D,$F8,$B5,$66,$00,$FF,$50
	dc.b $0C,$00,$00,$26,$66,$00,$FF,$48,$1B,$41,$F8,$B5,$60,$00,$FF,$40
	dc.b $42,$12,$24,$0A,$94,$89,$53,$02,$12,$82,$0C,$00,$00,$3B,$67,$1C
	dc.b $43,$ED,$F7,$44,$24,$49,$42,$1A,$14,$C0,$10,$18,$B0,$03,$67,$F8
	dc.b $B0,$04,$67,$F4,$24,$0A,$94,$89,$53,$02,$12,$82,$2B,$48,$FB,$D2
	dc.b $43,$ED,$FC,$E8,$91,$C9,$3B,$40,$FB,$D8,$66,$0C,$53,$48,$3B,$48
	dc.b $FB,$D6,$53,$AD,$FB,$D2,$60,$06,$3B,$48,$FB,$D6,$53,$48,$3B,$48
	dc.b $F8,$B2,$38,$1F,$36,$1F,$24,$5F,$4E,$75,$20,$5F,$22,$57,$2E,$88
	dc.b $2F,$09,$42,$19,$74,$00,$41,$ED,$F8,$38,$61,$42,$41,$ED,$EF,$72
	dc.b $61,$3C,$41,$ED,$F7,$BE,$61,$36,$41,$ED,$EE,$72,$61,$30,$41,$ED
	dc.b $F8,$B6,$4A,$10,$67,$06,$12,$FC,$00,$2E,$61,$22,$41,$ED,$F7,$44
	dc.b $61,$1C,$41,$ED,$FC,$E8,$D0,$ED,$F8,$B2,$10,$18,$67,$04,$12,$C0
	dc.b $60,$F8,$20,$5F,$24,$09,$94,$88,$53,$02,$10,$82,$4E,$75,$42,$41
	dc.b $12,$18,$67,$10,$60,$0A,$52,$42,$0C,$42,$00,$FF,$6E,$06,$12,$D8
	dc.b $51,$C9,$FF,$F4,$4E,$75,$20,$5F,$30,$1F,$22,$6D,$F0,$EE,$74,$00
	dc.b $34,$29,$00,$16,$32,$02,$D2,$40,$0C,$41,$03,$F8,$6C,$0E,$20,$29
	dc.b $00,$04,$D0,$82,$2E,$80,$33,$41,$00,$16,$4E,$D0,$2F,$08,$52,$6D
	dc.b $F0,$E2,$50,$40,$33,$40,$00,$16,$20,$69,$00,$04,$D0,$C2,$10,$BC
	dc.b $00,$1D,$59,$4F,$4E,$AD,$07,$AA,$20,$1F,$22,$6D,$F0,$EE,$B0,$91
	dc.b $67,$18,$22,$29,$00,$04,$66,$04,$22,$80,$60,$06,$20,$41,$21,$40
	dc.b $00,$04,$20,$40,$20,$81,$23,$40,$00,$04,$20,$5F,$50,$80,$2E,$80
	dc.b $4E,$D0,$20,$5F,$22,$57,$2E,$88,$20,$6D,$F0,$E8,$50,$48,$50,$49
	dc.b $30,$3C,$00,$FB,$22,$D8,$51,$C8,$FF,$FC,$4E,$75,$22,$5F,$24,$1F
	dc.b $30,$1F,$2F,$09,$2F,$02,$2F,$0B,$47,$EF,$00,$04,$D0,$40,$30,$3B
	dc.b $00,$06,$4E,$FB,$00,$02,$00,$20,$00,$3A,$00,$72,$00,$8C,$00,$E2
	dc.b $01,$2C,$01,$8E,$01,$7C,$01,$6A,$01,$46,$01,$58,$00,$54,$00,$A6
	dc.b $00,$C4,$00,$FC,$01,$14,$59,$4F,$3F,$3C,$00,$01,$4E,$BA,$FF,$38
	dc.b $22,$5F,$10,$2B,$00,$03,$00,$00,$00,$80,$12,$80,$60,$00,$02,$0A
	dc.b $59,$4F,$3F,$3C,$00,$01,$4E,$BA,$FF,$1E,$22,$5F,$10,$2B,$00,$03
	dc.b $00,$00,$00,$88,$12,$80,$60,$00,$01,$F0,$59,$4F,$3F,$3C,$00,$01
	dc.b $4E,$BA,$FF,$04,$22,$5F,$10,$2B,$00,$03,$02,$00,$00,$07,$00,$00
	dc.b $00,$90,$12,$80,$60,$00,$01,$D2,$59,$4F,$3F,$3C,$00,$01,$4E,$BA
	dc.b $FE,$E6,$22,$5F,$10,$2B,$00,$03,$00,$00,$00,$A0,$12,$80,$60,$00
	dc.b $01,$B8,$59,$4F,$3F,$3C,$00,$01,$4E,$BA,$FE,$CC,$22,$5F,$10,$2B
	dc.b $00,$03,$00,$00,$00,$A8,$12,$80,$60,$00,$01,$9E,$59,$4F,$3F,$3C
	dc.b $00,$01,$4E,$BA,$FE,$B2,$22,$5F,$10,$2B,$00,$03,$02,$00,$00,$07
	dc.b $00,$00,$00,$B0,$12,$80,$60,$00,$01,$80,$59,$4F,$3F,$3C,$00,$01
	dc.b $4E,$BA,$FE,$94,$22,$5F,$10,$2B,$00,$03,$02,$00,$00,$07,$00,$00
	dc.b $00,$B8,$12,$80,$60,$00,$01,$62,$59,$4F,$3F,$3C,$00,$01,$4E,$BA
	dc.b $FE,$76,$22,$5F,$10,$2B,$00,$03,$00,$00,$00,$E0,$12,$80,$60,$00
	dc.b $01,$48,$59,$4F,$3F,$3C,$00,$02,$4E,$BA,$FE,$5C,$22,$5F,$12,$FC
	dc.b $00,$09,$12,$AB,$00,$03,$60,$00,$01,$30,$59,$4F,$3F,$3C,$00,$02
	dc.b $4E,$BA,$FE,$44,$22,$5F,$12,$FC,$00,$0A,$12,$AB,$00,$03,$60,$00
	dc.b $01,$18,$59,$4F,$3F,$3C,$00,$05,$4E,$BA,$FE,$2C,$22,$5F,$42,$19
	dc.b $12,$DB,$12,$DB,$12,$DB,$12,$93,$60,$00,$00,$FE,$59,$4F,$3F,$3C
	dc.b $00,$05,$4E,$BA,$FE,$12,$22,$5F,$12,$FC,$00,$07,$60,$E2,$59,$4F
	dc.b $3F,$3C,$00,$05,$4E,$BA,$FE,$00,$22,$5F,$12,$FC,$00,$08,$60,$D0
	dc.b $59,$4F,$3F,$3C,$00,$05,$4E,$BA,$FD,$EE,$22,$5F,$12,$FC,$00,$06
	dc.b $60,$BE,$59,$4F,$3F,$3C,$00,$05,$4E,$BA,$FD,$DC,$22,$5F,$12,$FC
	dc.b $00,$05,$60,$AC,$0C,$82,$00,$00,$00,$0F,$6E,$0A,$0C,$82,$FF,$FF
	dc.b $FF,$F0,$6C,$00,$00,$8A,$0C,$82,$00,$00,$00,$7F,$6E,$08,$0C,$82
	dc.b $FF,$FF,$FF,$80,$6C,$62,$0C,$82,$00,$00,$7F,$FF,$6E,$08,$0C,$82
	dc.b $FF,$FF,$80,$00,$6C,$3A,$0C,$82,$00,$7F,$FF,$FF,$6E,$08,$0C,$82
	dc.b $FF,$80,$00,$00,$6C,$14,$59,$4F,$3F,$3C,$00,$05,$4E,$BA,$FD,$88
	dc.b $22,$5F,$12,$FC,$00,$04,$60,$00,$FF,$58,$59,$4F,$3F,$3C,$00,$04
	dc.b $4E,$BA,$FD,$74,$22,$5F,$12,$FC,$00,$03,$52,$4B,$60,$00,$FF,$44
	dc.b $59,$4F,$3F,$3C,$00,$03,$4E,$BA,$FD,$5E,$22,$5F,$12,$FC,$00,$02
	dc.b $54,$4B,$12,$DB,$12,$93,$60,$30,$59,$4F,$3F,$3C,$00,$02,$4E,$BA
	dc.b $FD,$46,$22,$5F,$12,$FC,$00,$01,$12,$AB,$00,$03,$60,$1A,$59,$4F
	dc.b $3F,$3C,$00,$01,$4E,$BA,$FD,$30,$22,$5F,$10,$2B,$00,$03,$02,$00
	dc.b $00,$1F,$00,$00,$00,$C0,$12,$80,$26,$5F,$58,$4F,$4E,$75,$20,$5F
	dc.b $30,$1F,$2F,$08,$1F,$00,$59,$4F,$3F,$3C,$00,$01,$4E,$BA,$FD,$08
	dc.b $22,$5F,$12,$9F,$4E,$75,$59,$4F,$3F,$3C,$00,$08,$4E,$BA,$FC,$F8
	dc.b $22,$5F,$4A,$2D,$EC,$C2,$67,$06,$12,$FC,$00,$13,$60,$04,$12,$FC
	dc.b $00,$14,$41,$EF,$00,$04,$12,$D8,$12,$D8,$30,$18,$12,$C0,$12,$D8
	dc.b $12,$D8,$30,$18,$4A,$2D,$F3,$BA,$6B,$16,$4A,$2D,$F3,$B7,$67,$22
	dc.b $0C,$40,$00,$10,$66,$04,$30,$3C,$00,$08,$00,$40,$00,$10,$60,$12
	dc.b $0C,$40,$00,$08,$6F,$04,$E8,$48,$50,$40,$10,$3B,$00,$1A,$00,$40
	dc.b $00,$20,$EB,$48,$80,$58,$EB,$48,$80,$50,$30,$80,$12,$D8,$12,$98
	dc.b $22,$57,$2E,$48,$4E,$D1,$00,$01,$02,$00,$03,$00,$00,$00,$04,$05
	dc.b $06,$00,$07,$00,$59,$4F,$3F,$3C,$00,$07,$4E,$BA,$FC,$7A,$22,$5F
	dc.b $12,$FC,$00,$1B,$41,$EF,$00,$04,$12,$D8,$12,$D8,$30,$18,$12,$C0
	dc.b $30,$18,$12,$C0,$12,$D8,$12,$98,$22,$57,$2E,$48,$4E,$D1,$59,$4F
	dc.b $3F,$3C,$00,$05,$4E,$BA,$FC,$50,$22,$5F,$12,$FC,$00,$1A,$41,$EF
	dc.b $00,$04,$12,$D8,$12,$D8,$30,$18,$12,$C0,$30,$18,$12,$80,$22,$57
	dc.b $2E,$48,$4E,$D1,$22,$6D,$F0,$F2,$30,$11,$67,$44,$32,$00,$E5,$49
	dc.b $D0,$41,$5C,$40,$59,$4F,$3F,$00,$4E,$BA,$FC,$1C,$22,$5F,$12,$FC
	dc.b $00,$15,$41,$EF,$00,$04,$30,$18,$12,$C0,$12,$D8,$12,$D8,$30,$10
	dc.b $12,$C0,$20,$6D,$F0,$F2,$32,$10,$12,$C1,$41,$E8,$00,$0A,$60,$0C
	dc.b $30,$18,$12,$C0,$12,$D8,$12,$D8,$12,$D8,$12,$D8,$51,$C9,$FF,$F2
	dc.b $20,$5F,$58,$4F,$4E,$D0,$59,$4F,$3F,$3C,$00,$09,$4E,$BA,$FB,$D8
	dc.b $22,$5F,$12,$FC,$00,$1C,$41,$EF,$00,$04,$12,$D8,$12,$D8,$12,$D8
	dc.b $12,$D8,$12,$D8,$12,$D8,$12,$D8,$12,$98,$22,$57,$2E,$48,$4E,$D1
	dc.b $2F,$04,$3F,$05,$2F,$0C,$20,$6D,$FF,$FC,$28,$50,$3A,$28,$00,$04
	dc.b $78,$00,$18,$28,$00,$07,$4A,$2D,$F3,$A0,$67,$12,$70,$20,$B8,$00
	dc.b $67,$06,$0C,$04,$00,$09,$66,$06,$18,$1C,$52,$45,$60,$F0,$30,$04
	dc.b $D0,$40,$30,$3B,$00,$06,$4E,$FB,$00,$02,$07,$80,$07,$8E,$07,$8E
	dc.b $07,$80,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$80,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$80,$06,$58,$04,$E2
	dc.b $06,$DA,$04,$7C,$04,$34,$02,$2A,$05,$22,$06,$80,$06,$8A,$05,$B0
	dc.b $05,$74,$06,$BC,$05,$92,$06,$C6,$05,$CE,$03,$A4,$03,$C8,$03,$C8
	dc.b $03,$C8,$03,$C8,$03,$C8,$03,$C8,$03,$C8,$03,$C8,$03,$C8,$06,$D0
	dc.b $07,$80,$05,$EC,$06,$6C,$06,$2A,$07,$8E,$02,$2A,$02,$2A,$02,$2A
	dc.b $02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A
	dc.b $02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A
	dc.b $02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A,$02,$2A
	dc.b $06,$94,$06,$EE,$06,$9E,$07,$8E,$02,$2A,$07,$8E,$02,$20,$02,$20
	dc.b $02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20
	dc.b $02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20
	dc.b $02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20,$02,$20
	dc.b $06,$A8,$06,$58,$06,$B2,$06,$76,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$06,$20,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$06,$16
	dc.b $06,$4E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$02,$00,$07,$8E,$06,$E4
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$06,$0C,$06,$44,$07,$8E,$07,$80
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$06,$62,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E
	dc.b $07,$8E,$07,$8E,$07,$8E,$07,$8E,$07,$8E,$4A,$6D,$EC,$E4,$67,$00
	dc.b $05,$88,$60,$20,$43,$ED,$FE,$FB,$12,$FC,$00,$25,$74,$01,$32,$2D
	dc.b $F3,$8E,$4A,$2D,$F3,$A1,$66,$3C,$60,$26,$4A,$2D,$F3,$A1,$67,$04
	dc.b $04,$04,$00,$20,$42,$42,$32,$2D,$F3,$8E,$43,$ED,$FE,$FB,$4A,$2D
	dc.b $F3,$A1,$66,$14,$B4,$41,$6C,$04,$52,$42,$12,$C4,$18,$1C,$52,$45
	dc.b $10,$3B,$40,$5C,$66,$EE,$60,$18,$B4,$41,$6C,$04,$52,$42,$12,$C4
	dc.b $18,$1C,$52,$45,$10,$3B,$40,$48,$6D,$EE,$67,$04,$18,$00,$60,$E8
	dc.b $42,$2D,$FF,$FB,$1B,$42,$FE,$FA,$3B,$42,$FE,$F8,$0C,$2D,$00,$40
	dc.b $FE,$FB,$66,$16,$58,$42,$1B,$42,$FE,$FA,$41,$ED,$F4,$35,$12,$D8
	dc.b $12,$D8,$12,$D8,$12,$90,$60,$00,$05,$0A,$0C,$2D,$00,$C0,$FE,$FB
	dc.b $66,$00,$05,$00,$1B,$7C,$00,$40,$FE,$FB,$60,$00,$04,$F6
	dcb.b $23,$00
	dc.b $FF,$FF,$FF
	dcb.b $A,$00
	dcb.b $A,$FF
	dc.b $00,$00,$00,$00,$00,$00
	dcb.b $1B,$FF
	dc.b $00,$00,$00,$00,$FF,$00,$41,$42,$43,$44,$45,$46,$47,$48,$49,$4A
	dc.b $4B,$4C,$4D,$4E,$4F,$50,$51,$52,$53,$54,$55,$56,$57,$58,$59,$5A
	dcb.b $85,$00
	dc.b $18,$1C,$52,$45,$0C,$04,$00,$30,$67,$F6,$0C,$04,$00,$31,$6D,$06
	dc.b $0C,$04,$00,$39,$6F,$0E,$1B,$7C,$00,$01,$FF,$FB,$42,$AD,$FE,$F0
	dc.b $60,$00,$03,$D2,$1B,$7C,$00,$01,$FF,$FB,$3F,$06,$2F,$07,$42,$46
	dc.b $7E,$00,$72,$30,$74,$39,$0C,$46,$00,$09,$6F,$0E,$3F,$3C,$00,$01
	dc.b $4E,$AD,$07,$CA,$72,$30,$74,$39,$7E,$00,$66,$1E,$0C,$87,$0C,$CC
	dc.b $CC,$CC,$6E,$06,$66,$14,$B8,$02,$6D,$10,$3F,$3C,$00,$01,$4E,$AD
	dc.b $07,$CA,$72,$30,$74,$39,$7E,$00,$60,$0C,$DE,$87,$20,$07,$E5,$8F
	dc.b $DE,$80,$98,$41,$DE,$84,$52,$46,$18,$1C,$52,$45,$B8,$01,$6D,$04
	dc.b $B8,$02,$6F,$B2,$2B,$47,$FE,$F0,$2E,$1F,$3C,$1F,$60,$00,$03,$66
	dc.b $1B,$7C,$00,$01,$FF,$FB,$42,$40,$72,$00,$18,$1C,$52,$45,$0C,$04
	dc.b $00,$30,$67,$0C,$0C,$04,$00,$31,$66,$10,$D2,$81,$52,$81,$60,$02
	dc.b $D2,$81,$52,$40,$18,$1C,$52,$45,$60,$E4,$4A,$40,$67,$00,$FD,$A8
	dc.b $2B,$41,$FE,$F0,$0C,$40,$00,$20,$6F,$00,$03,$2A,$3F,$3C,$00,$02
	dc.b $4E,$AD,$07,$CA,$60,$00,$03,$1E,$1B,$7C,$00,$01,$FF,$FB,$42,$40
	dc.b $72,$00,$18,$1C,$52,$45,$0C,$04,$00,$30,$6D,$06,$0C,$04,$00,$39
	dc.b $6F,$20,$0C,$04,$00,$41,$6D,$0A,$0C,$04,$00,$46,$6E,$04,$5F,$44
	dc.b $60,$10,$0C,$04,$00,$61,$6D,$1A,$0C,$04,$00,$66,$6E,$14,$04,$44
	dc.b $00,$27,$E9,$89,$04,$04,$00,$30,$D2,$84,$52,$40,$18,$1C,$52,$45
	dc.b $60,$C4,$2B,$41,$FE,$F0,$4A,$40,$67,$08,$0C,$40,$00,$08,$6F,$00
	dc.b $02,$C4,$3F,$3C,$00,$04,$4E,$AD,$07,$CA,$60,$00,$02,$B8,$1B,$7C
	dc.b $00,$02,$FF,$FB,$42,$40,$43,$ED,$FD,$ED,$18,$1C,$52,$45,$4A,$04
	dc.b $66,$14,$1B,$40,$FD,$EC,$3B,$40,$FD,$EA,$3F,$3C,$00,$BE,$4E,$AD
	dc.b $07,$CA,$60,$00,$02,$90,$0C,$04,$00,$22,$67,$06,$52,$40,$12,$C4
	dc.b $60,$D8,$1B,$40,$FD,$EC,$3B,$40,$FD,$EA,$60,$00,$02,$74,$1B,$7C
	dc.b $00,$03,$FF,$FB,$42,$40,$43,$ED,$FD,$ED,$18,$1C,$52,$45,$4A,$04
	dc.b $66,$0E,$3F,$00,$3F,$3C,$00,$05,$4E,$AD,$07,$CA,$30,$1F,$60,$16
	dc.b $0C,$04,$00,$27,$66,$0A,$18,$1C,$52,$45,$0C,$04,$00,$27,$66,$06
	dc.b $52,$40,$12,$C4,$60,$D4,$1B,$40,$FD,$EC,$3B,$40,$FD,$EA,$72,$00
	dc.b $53,$40,$66,$04,$12,$2D,$FD,$ED,$2B,$41,$FE,$F0,$60,$00,$02,$26
	dc.b $18,$1C,$52,$45,$0C,$04,$00,$2B,$67,$0A,$1B,$7C,$00,$04,$FF,$FB
	dc.b $60,$00,$02,$12,$1B,$7C,$00,$09,$FF,$FB,$60,$00,$02,$04,$18,$1C
	dc.b $52,$45,$0C,$04,$00,$2D,$67,$0A,$1B,$7C,$00,$05,$FF,$FB,$60,$00
	dc.b $01,$F4,$1B,$7C,$00,$0A,$FF,$FB,$60,$00,$01,$E6,$18,$1C,$52,$45
	dc.b $0C,$04,$00,$2A,$67,$0A,$1B,$7C,$00,$06,$FF,$FB,$60,$00,$01,$D6
	dc.b $1B,$7C,$00,$0B,$FF,$FB,$60,$00,$01,$C8,$18,$1C,$52,$45,$0C,$04
	dc.b $00,$2F,$67,$0A,$1B,$7C,$00,$07,$FF,$FB,$60,$00,$01,$B8,$1B,$7C
	dc.b $00,$08,$FF,$FB,$60,$00,$01,$AA,$18,$1C,$52,$45,$0C,$04,$00,$3C
	dc.b $67,$16,$0C,$04,$00,$3D,$67,$1A,$0C,$04,$00,$3E,$67,$1E,$1B,$7C
	dc.b $00,$0E,$FF,$FB,$60,$00,$01,$8E,$1B,$7C,$00,$13,$FF,$FB,$60,$00
	dc.b $01,$80,$1B,$7C,$00,$11,$FF,$FB,$60,$00,$01,$76,$1B,$7C,$00,$0D
	dc.b $FF,$FB,$60,$00,$01,$6C,$18,$1C,$52,$45,$0C,$04,$00,$3E,$67,$10
	dc.b $0C,$04,$00,$3D,$67,$14,$1B,$7C,$00,$0F,$FF,$FB,$60,$00,$01,$56
	dc.b $1B,$7C,$00,$12,$FF,$FB,$60,$00,$01,$48,$1B,$7C,$00,$10,$FF,$FB
	dc.b $60,$00,$01,$3E,$1B,$7C,$00,$09,$FF,$FB,$60,$00,$01,$34,$1B,$7C
	dc.b $00,$07,$FF,$FB,$60,$00,$01,$2A,$1B,$7C,$00,$0C,$FF,$FB,$60,$00
	dc.b $01,$20,$1B,$7C,$00,$15,$FF,$FB,$60,$00,$01,$16,$1B,$7C,$00,$16
	dc.b $FF,$FB,$60,$00,$01,$0C,$1B,$7C,$00,$17,$FF,$FB,$60,$00,$01,$02
	dc.b $1B,$7C,$00,$18,$FF,$FB,$60,$00,$00,$F8,$1B,$7C,$00,$19,$FF,$FB
	dc.b $60,$00,$00,$EE,$1B,$7C,$00,$1A,$FF,$FB,$60,$00,$00,$E4,$1B,$7C
	dc.b $00,$1B,$FF,$FB,$60,$00,$00,$DA,$1B,$7C,$00,$1C,$FF,$FB,$60,$00
	dc.b $00,$D0,$1B,$7C,$00,$1D,$FF,$FB,$60,$00,$00,$C6,$1B,$7C,$00,$1F
	dc.b $FF,$FB,$60,$00,$00,$BC,$1B,$7C,$00,$20,$FF,$FB,$60,$00,$00,$B2
	dc.b $1B,$7C,$00,$14,$FF,$FB,$60,$00,$00,$A8,$4A,$2D,$EC,$C3,$67,$0E
	dc.b $18,$1C,$52,$45,$1B,$7C,$00,$21,$FF,$FB,$60,$00,$00,$98,$55,$4F
	dc.b $22,$6D,$FF,$FC,$4A,$29,$00,$0F,$67,$06,$4E,$BA,$01,$EA,$60,$06
	dc.b $42,$27,$4E,$BA,$39,$1C,$10,$1F,$67,$62,$22,$6D,$FF,$FC,$20,$69
	dc.b $00,$08,$3A,$3C,$00,$02,$18,$28,$00,$01,$49,$E8,$00,$02,$0C,$04
	dc.b $00,$20,$67,$06,$0C,$04,$00,$09,$66,$06,$18,$1C,$52,$45,$60,$EE
	dc.b $52,$69,$00,$0C,$4A,$29,$00,$0F,$66,$00,$F8,$8E,$4A,$6D,$EC,$E4
	dc.b $67,$00,$F8,$86,$4A,$2D,$EC,$C4,$66,$00,$F8,$7E,$33,$44,$00,$06
	dc.b $67,$00,$F8,$76,$22,$8C,$33,$45,$00,$04,$2F,$08,$4E,$AD,$04,$C2
	dc.b $22,$6D,$FF,$FC,$38,$29,$00,$06,$60,$00,$F8,$5E,$53,$45,$55,$4C
	dc.b $1B,$7C,$00,$1E,$FF,$FB,$60,$00,$00,$0C,$1B,$7C,$00,$23,$FF,$FB
	dc.b $18,$1C,$52,$45,$20,$6D,$FF,$FC,$20,$8C,$31,$45,$00,$04,$31,$44
	dc.b $00,$06,$28,$5F,$3A,$1F,$28,$1F,$4E,$75,$22,$5F,$30,$1F,$20,$6D
	dc.b $FF,$FC,$20,$68,$00,$08,$D0,$C0,$72,$3B,$74,$5C,$10,$18,$67,$20
	dc.b $B0,$01,$67,$1C,$0C,$00,$00,$27,$66,$0C,$10,$18,$67,$12,$0C,$00
	dc.b $00,$27,$66,$F6,$60,$E6,$B0,$02,$66,$E2,$1E,$BC,$00,$01,$4E,$D1
	dc.b $42,$17,$4E,$D1,$22,$5F,$32,$1F,$14,$1F,$20,$5F,$10,$10,$66,$06
	dc.b $1E,$BC,$00,$01,$4E,$D1,$2F,$09,$22,$48,$52,$48,$10,$10,$4A,$01
	dc.b $67,$08,$B0,$01,$66,$00,$00,$E4,$60,$76,$0C,$00,$00,$40,$6D,$06
	dc.b $0C,$00,$00,$5A,$6F,$6A,$0C,$00,$00,$61,$6D,$14,$0C,$00,$00,$7A
	dc.b $6E,$00,$00,$C8,$4A,$02,$67,$58,$04,$00,$00,$20,$10,$80,$60,$50
	dc.b $0C,$00,$00,$5F,$67,$4A,$0C,$00,$00,$25,$66,$38,$12,$11,$B2,$2D
	dc.b $F3,$8F,$63,$14,$12,$AD,$F3,$8F,$48,$E7,$E0,$C0,$3F,$3C,$00,$CE
	dc.b $4E,$AD,$07,$CA,$4C,$DF,$03,$07,$53,$41,$63,$00,$00,$92,$52,$48
	dc.b $10,$10,$0C,$00,$00,$30,$67,$00,$00,$82,$0C,$00,$00,$31,$67,$7A
	dc.b $D0,$C1,$60,$2C,$0C,$00,$00,$C0,$66,$70,$4A,$6D,$EC,$E4,$67,$6A
	dc.b $12,$11,$B2,$2D,$F3,$8F,$63,$14,$12,$AD,$F3,$8F,$48,$E7,$E0,$C0
	dc.b $3F,$3C,$00,$CE,$4E,$AD,$07,$CA,$4C,$DF,$03,$07,$D0,$C1,$53,$41
	dc.b $42,$40,$43,$FA,$F9,$FC,$60,$10,$10,$20,$10,$31,$00,$00,$6D,$08
	dc.b $67,$38,$4A,$02,$67,$02,$10,$80,$51,$C9,$FF,$EE,$10,$20,$0C,$00
	dc.b $00,$40,$67,$0C,$0C,$00,$00,$C0,$66,$24,$10,$BC,$00,$40,$60,$1E
	dc.b $42,$41,$12,$20,$10,$01,$58,$00,$10,$C0,$D0,$C1,$43,$ED,$F4,$35
	dc.b $10,$D9,$10,$D9,$10,$D9,$10,$99,$60,$04,$42,$00,$60,$02,$70,$01
	dc.b $20,$5F,$1E,$80,$4E,$D0,$4A,$2D,$EC,$C1,$67,$08,$48,$7A,$00,$A2
	dc.b $4E,$BA,$08,$14,$22,$5F,$3B,$7C,$00,$01,$FB,$D6,$4A,$2D,$FB,$C0
	dc.b $67,$0C,$10,$2D,$FB,$C1,$0A,$00,$00,$01,$1E,$80,$4E,$D1,$2F,$09
	dc.b $2F,$0B,$20,$6D,$FF,$FC,$26,$68,$00,$08,$4A,$2D,$FB,$C1,$67,$10
	dc.b $42,$1B,$42,$13,$42,$6D,$FC,$E6,$26,$5F,$22,$5F,$42,$17,$4E,$D1
	dc.b $55,$4F,$4A,$AD,$EC,$E6,$67,$1E,$2F,$0B,$4E,$AD,$04,$B2,$10,$1F
	dc.b $66,$38,$4E,$AD,$07,$02,$20,$6D,$F0,$F2,$4A,$50,$67,$E2,$1B,$7C
	dc.b $00,$01,$FB,$C0,$60,$DA,$2F,$2D,$CB,$1E,$2F,$0B,$4E,$AD,$04,$12
	dc.b $10,$1F,$66,$08,$1B,$7C,$00,$01,$FB,$C1,$60,$B4,$30,$2D,$ED,$60
	dc.b $52,$40,$3B,$40,$ED,$60,$3B,$40,$ED,$5E,$42,$40,$10,$1B,$3B,$40
	dc.b $FC,$E6,$D6,$C0,$42,$13,$26,$5F,$22,$5F,$1E,$BC,$00,$01,$4E,$D1
	dc.b $0A,$3C,$3C,$3C,$49,$4E,$54,$52,$3E,$3E,$3E,$00,$4E,$56,$FF,$FC
	dc.b $48,$E7,$1F,$18,$49,$ED,$FA,$BE,$55,$4F,$2F,$0C,$4E,$BA,$E6,$9E
	dc.b $30,$1F,$3D,$40,$FF,$FC,$38,$2E,$00,$0C,$2A,$2E,$00,$0E,$2C,$2E
	dc.b $00,$08,$66,$18,$59,$4F,$2F,$2D,$F3,$AC,$2F,$0C,$2F,$05,$3F,$04
	dc.b $48,$6E,$FF,$FF,$3F,$00,$4E,$BA,$E7,$32,$60,$4C,$4A,$2D,$F3,$A2
	dc.b $67,$08,$59,$4F,$2F,$2D,$F3,$AC,$60,$2C,$48,$E7,$8E,$08,$59,$4F
	dc.b $2F,$2D,$F3,$A8,$2F,$0C,$48,$6E,$00,$0E,$48,$6E,$00,$0C,$3F,$2E
	dc.b $FF,$FC,$4E,$BA,$E7,$E8,$20,$1F,$66,$00,$01,$72,$4C,$DF,$10,$71
	dc.b $59,$4F,$2F,$2D,$F3,$B0,$2F,$0C,$2F,$06,$3F,$04,$2F,$05,$48,$6E
	dc.b $FF,$FF,$3F,$00,$4E,$BA,$E8,$54,$26,$1F,$67,$00,$01,$1A,$2B,$43
	dc.b $F3,$CA,$1E,$2E,$FF,$FF,$67,$00,$00,$C2,$26,$43,$30,$2B,$00,$08
	dc.b $32,$00,$02,$41,$0A,$00,$34,$04,$02,$42,$30,$00,$08,$00,$00,$06
	dc.b $67,$06,$08,$04,$00,$06,$66,$36,$08,$00,$00,$0F,$66,$00,$00,$F0
	dc.b $08,$00,$00,$0A,$66,$00,$00,$E8,$34,$04,$02,$42,$00,$7F,$02,$42
	dc.b $80,$2C,$66,$00,$00,$C2,$08,$04,$00,$0A,$66,$00,$00,$C2,$4A,$41
	dc.b $67,$0C,$34,$04,$02,$42,$30,$00,$C4,$40,$67,$00,$00,$C2,$02,$40
	dc.b $7F,$F3,$80,$44,$37,$40,$00,$08,$4A,$41,$67,$46,$4A,$42,$67,$00
	dc.b $00,$AE,$4A,$2D,$F3,$A5,$67,$14,$20,$6B,$00,$04,$89,$68,$00,$08
	dc.b $20,$68,$00,$04,$21,$45,$00,$02,$60,$00,$00,$D0,$4A,$2D,$F3,$A4
	dc.b $67,$00,$00,$8C,$59,$4F,$2F,$0B,$4E,$BA,$E9,$72,$20,$5F,$20,$85
	dc.b $20,$6B,$00,$04,$30,$04,$02,$40,$FF,$FE,$81,$68,$00,$08,$60,$00
	dc.b $00,$AA,$4A,$86,$66,$08,$27,$45,$00,$04,$60,$00,$00,$9E,$59,$4F
	dc.b $2F,$0B,$4E,$BA,$E9,$48,$20,$5F,$20,$85,$4A,$2D,$F3,$A2,$67,$00
	dc.b $00,$8A,$4A,$AD,$F3,$D8,$67,$00,$00,$82,$59,$4F,$2F,$2D,$F3,$DC
	dc.b $3F,$3C,$00,$08,$4E,$AD,$07,$8A,$20,$1F,$66,$0A,$3F,$3C,$00,$B3
	dc.b $4E,$AD,$07,$CA,$60,$60,$20,$40,$20,$83,$21,$6D,$F3,$D4,$00,$04
	dc.b $2B,$48,$F3,$D4,$60,$54,$3F,$3C,$00,$C5,$42,$47,$60,$42,$3F,$3C
	dc.b $00,$C3,$42,$47,$60,$3A,$3F,$3C,$00,$16,$42,$47,$60,$32,$34,$04
	dc.b $02,$42,$30,$00,$66,$26,$4A,$86,$66,$22,$32,$2B,$00,$08,$02,$41
	dc.b $0A,$00,$66,$18,$B8,$6B,$00,$08,$66,$12,$BA,$AB,$00,$04,$66,$0C
	dc.b $3F,$3C,$00,$EB,$2F,$0C,$4E,$AD,$07,$C2,$60,$0E,$3F,$3C,$00,$08
	dc.b $2F,$0C,$4E,$AD,$07,$C2,$42,$AD,$F3,$CA,$0C,$2D,$00,$40,$FA,$BF
	dc.b $67,$7E,$70,$00,$30,$2D,$F4,$3C,$52,$40,$3B,$40,$F4,$3C,$3B,$40
	dc.b $F4,$3A,$59,$4F,$2F,$00,$3F,$3C,$FF,$FC,$1F,$3C,$00,$01,$4E,$BA
	dc.b $E3,$08,$20,$5F,$43,$ED,$F4,$34,$22,$D8,$32,$90,$08,$2D,$00,$06
	dc.b $ED,$5D,$67,$4C,$4A,$07,$66,$48,$4A,$86,$66,$44,$4A,$2D,$F3,$A5
	dc.b $67,$3E,$59,$4F,$2F,$2D,$F3,$B0,$2F,$0C,$48,$6E,$00,$0E,$48,$6E
	dc.b $00,$0C,$3F,$2E,$FF,$FC,$4E,$BA,$E6,$04,$20,$1F,$67,$22,$34,$2E
	dc.b $00,$0C,$02,$42,$30,$00,$66,$18,$24,$2E,$00,$0E,$BA,$82,$66,$06
	dc.b $3F,$3C,$00,$EB,$60,$04,$3F,$3C,$00,$E9,$2F,$0C,$4E,$AD,$07,$C2
	dc.b $4C,$DF,$18,$F8,$4E,$5E,$20,$5F,$4F,$EF,$00,$0A,$4E,$D0,$41,$FA
	dc.b $00,$4C,$20,$2D,$FE,$FA,$32,$2D,$FE,$F8,$55,$41,$66,$12,$02,$80
	dc.b $FF,$DF,$DF,$00,$B0,$90,$66,$32,$1B,$7C,$00,$09,$FF,$FB,$4E,$75
	dc.b $53,$41,$66,$26,$02,$80,$FF,$DF,$DF,$DF,$58,$48,$B0,$98,$67,$14
	dc.b $B0,$98,$67,$10,$B0,$98,$67,$0C,$B0,$98,$67,$08,$B0,$98,$67,$04
	dc.b $B0,$98,$66,$06,$1B,$68,$00,$1B,$FF,$FB,$4E,$75,$02,$4F,$52,$00
	dc.b $03,$4E,$4F,$54,$03,$41,$4E,$44,$03,$45,$4F,$52,$03,$44,$49,$56
	dc.b $03,$4D,$4F,$44,$03,$58,$4F,$52,$00,$00,$00,$09,$00,$00,$00,$14
	dc.b $00,$00,$00,$0B,$00,$00,$00,$0A,$00,$00,$00,$07,$00,$00,$00,$08
	dc.b $00,$00,$00,$0A,$4E,$56,$00,$00,$2F,$2E,$00,$08,$A9,$F1,$4E,$5E
	dc.b $2E,$9F,$4E,$75,$87,$55,$4E,$4C,$44,$53,$45,$47,$00,$00,$4E,$56
	dc.b $00,$00,$42,$A7,$2F,$2E,$00,$0A,$3F,$2E,$00,$08,$A9,$A0,$2D,$5F
	dc.b $00,$0E,$4E,$5E,$20,$5F,$5C,$4F,$4E,$D0,$87,$47,$45,$54,$52,$53
	dc.b $52,$43,$00,$00,$4E,$56,$FE,$FE,$20,$6E,$00,$08,$43,$EE,$FF,$00
	dc.b $70,$7F,$32,$D8,$51,$C8,$FF,$FC,$48,$6E,$FF,$00,$48,$6E,$FE,$FE
	dc.b $A9,$00,$3D,$6E,$FE,$FE,$00,$0C,$4E,$5E,$2E,$9F,$4E,$75,$8A,$47
	dc.b $45,$54,$46,$4F,$4E,$54,$4E,$42,$52,$00,$00,$00,$4E,$56,$FF,$D6
	dc.b $48,$E7,$0F,$00,$42,$A7,$A9,$75,$28,$1F,$98,$AE,$00,$0C,$2D,$44
	dc.b $00,$10,$4A,$AE,$00,$08,$67,$00,$00,$BE,$2F,$04,$70,$3C,$2F,$00
	dc.b $4E,$AD,$0A,$7A,$20,$1F,$3C,$00,$1D,$7C,$00,$0B,$FF,$EA,$7E,$0B
	dc.b $30,$06,$48,$C0,$81,$FC,$00,$0A,$48,$40,$4A,$40,$D0,$7C,$00,$30
	dc.b $1D,$80,$70,$EA,$53,$47,$30,$06,$48,$C0,$81,$FC,$00,$0A,$3C,$00
	dc.b $66,$DE,$48,$6E,$FF,$EA,$3F,$3C,$00,$01,$3F,$07,$4E,$AD,$0A,$B2
	dc.b $2F,$04,$70,$3C,$2F,$00,$4E,$AD,$0A,$82,$70,$64,$2F,$00,$4E,$AD
	dc.b $0A,$72,$70,$3C,$2F,$00,$4E,$AD,$0A,$7A,$20,$1F,$3A,$00,$2D,$7C
	dc.b $03,$2E,$30,$30,$FF,$E6,$7E,$03,$4A,$45,$67,$22,$30,$05,$48,$C0
	dc.b $81,$FC,$00,$0A,$48,$40,$4A,$40,$D0,$7C,$00,$30,$1D,$80,$70,$E6
	dc.b $53,$47,$30,$05,$48,$C0,$81,$FC,$00,$0A,$3A,$00,$60,$DA,$20,$6E
	dc.b $00,$08,$2F,$08,$48,$6E,$FF,$EA,$48,$6E,$FF,$E6,$48,$6E,$FF,$D6
	dc.b $3F,$3C,$00,$02,$4E,$AD,$0A,$A2,$20,$5F,$43,$EE,$FF,$D6,$70,$07
	dc.b $30,$D9,$51,$C8,$FF,$FC,$4C,$DF,$00,$F0,$4E,$5E,$20,$5F,$50,$4F
	dc.b $4E,$D0,$85,$43,$4C,$4F,$43,$4B,$00,$00,$4E,$56,$00,$00,$22,$6E
	dc.b $00,$08,$20,$69,$00,$08,$30,$2E,$00,$0C,$32,$2E,$00,$0E,$48,$C1
	dc.b $83,$FC,$00,$0A,$D2,$7C,$00,$30,$11,$81,$00,$00,$22,$6E,$00,$08
	dc.b $20,$69,$00,$08,$30,$2E,$00,$0C,$52,$40,$32,$2E,$00,$0E,$48,$C1
	dc.b $83,$FC,$00,$0A,$48,$41,$4A,$41,$D2,$7C,$00,$30,$11,$81,$00,$00
	dc.b $4E,$5E,$20,$5F,$50,$4F,$4E,$D0,$89,$53,$45,$54,$44,$49,$47,$49
	dc.b $54,$53,$00,$00,$4E,$56,$FF,$9E,$2F,$07,$48,$6E,$FF,$F0,$4E,$BA
	dc.b $46,$FC,$20,$6E,$00,$08,$43,$FA,$00,$DE,$70,$09,$30,$D9,$51,$C8
	dc.b $FF,$FC,$3F,$2E,$FF,$F6,$3F,$3C,$00,$01,$2F,$0E,$4E,$BA,$FF,$7C
	dc.b $3F,$2E,$FF,$F8,$3F,$3C,$00,$04,$2F,$0E,$4E,$BA,$FF,$6E,$3F,$2E
	dc.b $FF,$FA,$3F,$3C,$00,$07,$2F,$0E,$4E,$BA,$FF,$60,$41,$EE,$FF,$9E
	dc.b $43,$FA,$00,$7E,$70,$12,$30,$D9,$51,$C8,$FF,$FC,$3F,$2E,$FF,$F4
	dc.b $3F,$3C,$00,$0A,$2F,$0E,$4E,$BA,$FF,$42,$30,$2E,$FF,$F2,$C1,$FC
	dc.b $00,$03,$3E,$00,$55,$47,$20,$6E,$00,$08,$42,$40,$10,$36,$70,$9E
	dc.b $11,$40,$00,$0D,$20,$6E,$00,$08,$30,$07,$52,$40,$42,$41,$12,$36
	dc.b $00,$9E,$11,$41,$00,$0E,$20,$6E,$00,$08,$30,$07,$54,$40,$42,$41
	dc.b $12,$36,$00,$9E,$11,$41,$00,$0F,$30,$2E,$FF,$F0,$48,$C0,$81,$FC
	dc.b $00,$64,$48,$40,$3F,$00,$3F,$3C,$00,$11,$2F,$0E,$4E,$BA,$FE,$EC
	dc.b $2E,$1F,$4E,$5E,$2E,$9F,$4E,$75,$85,$47,$45,$54,$54,$44,$00,$3A
	dc.b $24,$4A,$61,$6E,$46,$65,$62,$4D,$61,$72,$41,$70,$72,$4D,$61,$79
	dc.b $4A,$75,$6E,$4A,$75,$6C,$41,$75,$67,$53,$65,$70,$4F,$63,$74,$4E
	dc.b $6F,$76,$44,$65,$63,$00,$12,$48,$48,$3A,$4D,$4D,$3A,$53,$53,$20
	dc.b $44,$44,$2D,$4D,$4D,$4D,$2D,$59,$59,$00,$4E,$56,$FF,$F8,$48,$E7
	dc.b $01,$18,$28,$6E,$00,$0A,$42,$A7,$4E,$AD,$07,$6A,$28,$9F,$67,$4E
	dc.b $10,$2E,$00,$08,$67,$08,$20,$54,$31,$7C,$FF,$FF,$00,$10,$42,$A7
	dc.b $2F,$14,$3F,$3C,$03,$EC,$4E,$AD,$07,$8A,$26,$5F,$20,$0B,$67,$24
	dc.b $20,$54,$21,$4B,$00,$18,$42,$6E,$FF,$F8,$3E,$2E,$FF,$F8,$60,$0C
	dc.b $30,$07,$E5,$40,$72,$00,$27,$81,$00,$00,$52,$47,$0C,$47,$00,$FA
	dc.b $6F,$EE,$60,$0A,$2F,$14,$4E,$AD,$07,$72,$70,$00,$28,$80,$4C,$DF
	dc.b $18,$80,$4E,$5E,$20,$5F,$5C,$4F,$4E,$D0,$4E,$56,$FF,$FE,$10,$2D
	dc.b $EC,$9B,$67,$42,$10,$2E,$00,$08,$67,$12,$48,$6D,$EC,$9E,$4E,$AD
	dc.b $08,$BA,$48,$6D,$EB,$9A,$4E,$AD,$08,$AA,$60,$26,$4E,$AD,$06,$62
	dc.b $48,$6D,$EC,$9E,$4E,$AD,$08,$BA,$42,$67,$48,$6D,$EB,$9A,$2F,$3C
	dc.b $4F,$42,$4A,$20,$2F,$3C,$4D,$50,$53,$20,$4E,$AD,$04,$32,$3D,$5F
	dc.b $FF,$FE,$42,$2D,$EC,$9B,$10,$2D,$EC,$FF,$67,$3E,$2F,$2D,$EB,$60
	dc.b $1F,$3C,$00,$02,$4E,$AD,$04,$5A,$10,$2D,$EB,$68,$66,$28,$20,$6D
	dc.b $EB,$64,$2F,$08,$3F,$2D,$E5,$1E,$4E,$AD,$04,$9A,$20,$6D,$EB,$64
	dc.b $2F,$08,$2F,$2D,$E5,$1A,$4E,$AD,$04,$A2,$2F,$2D,$EB,$64,$1F,$3C
	dc.b $00,$01,$4E,$AD,$04,$5A,$42,$2D,$EC,$FF,$4A,$AD,$CD,$4E,$67,$1A
	dc.b $20,$6D,$CD,$4E,$2F,$08,$3F,$2D,$E5,$1E,$4E,$AD,$04,$9A,$2F,$2D
	dc.b $CD,$4E,$1F,$3C,$00,$01,$4E,$AD,$04,$5A,$10,$2D,$F0,$ED,$67,$14
	dc.b $48,$6D,$EC,$B4,$4E,$AD,$08,$BA,$48,$7A,$00,$5C,$4E,$AD,$08,$AA
	dc.b $42,$2D,$F0,$ED,$10,$2D,$CD,$59,$67,$0C,$48,$6D,$CD,$5A,$4E,$AD
	dc.b $08,$BA,$42,$2D,$CD,$59,$10,$2D,$CD,$53,$67,$0C,$48,$6D,$CD,$54
	dc.b $4E,$AD,$08,$BA,$42,$2D,$CD,$53,$10,$2D,$CB,$3B,$67,$08,$48,$6D
	dc.b $CB,$3C,$4E,$AD,$08,$BA,$4E,$AD,$04,$3A,$4E,$5E,$20,$5F,$54,$4F
	dc.b $4E,$D0,$90,$43,$4C,$4F,$53,$45,$41,$4C,$4C,$41,$53,$4D,$46,$49
	dc.b $4C,$45,$53,$00,$00,$10,$0E,$23,$41,$73,$6D,$53,$70,$69,$6C,$6C
	dc.b $46,$69,$6C,$65,$23,$00,$4E,$56,$FE,$FE,$2F,$07,$20,$6E,$00,$08
	dc.b $43,$EE,$FF,$00,$70,$7F,$32,$D8,$51,$C8,$FF,$FC,$42,$47,$1E,$2E
	dc.b $FF,$00,$1F,$3C,$00,$04,$4E,$BA,$4C,$12,$4A,$47,$5E,$C0,$4A,$00
	dc.b $66,$08,$4A,$6D,$CD,$64,$5E,$C1,$80,$01,$44,$00,$1F,$00,$4E,$BA
	dc.b $FE,$9A,$4A,$47,$6F,$5A,$48,$6E,$FF,$00,$48,$7A,$00,$D6,$4E,$AD
	dc.b $0A,$C2,$10,$1F,$67,$2C,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2,$48,$6D
	dc.b $D2,$6E,$48,$7A,$00,$B8,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E
	dc.b $48,$6E,$FF,$00,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E,$4E,$AD
	dc.b $09,$F2,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2,$48,$6D,$D2,$6E,$48,$7A
	dc.b $00,$70,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2
	dc.b $70,$01,$B0,$2D,$E4,$F3,$66,$0C,$4A,$47,$66,$34,$1B,$7C,$00,$03
	dc.b $E4,$F3,$60,$2C,$4A,$2D,$E4,$F3,$66,$26,$10,$2D,$EC,$C1,$67,$08
	dc.b $1B,$7C,$00,$F7,$E4,$F3,$60,$18,$4A,$47,$6F,$08,$1B,$7C,$00,$03
	dc.b $E4,$F3,$60,$0C,$4A,$6D,$E4,$F4,$6F,$06,$1B,$7C,$00,$02,$E4,$F3
	dc.b $10,$2D,$E4,$F3,$48,$80,$48,$C0,$2F,$00,$4E,$AD,$08,$7A,$58,$8F
	dc.b $2E,$1F,$4E,$5E,$2E,$9F,$4E,$75,$85,$41,$42,$4F,$52,$54,$00,$2E
	dc.b $1B,$41,$73,$6D,$20,$2D,$20,$45,$78,$65,$63,$75,$74,$69,$6F,$6E
	dc.b $20,$74,$65,$72,$6D,$69,$6E,$61,$74,$65,$64,$21,$04,$23,$23,$23
	dc.b $20,$00,$0A,$3C,$3C,$3C,$49,$4E,$54,$52,$3E,$3E,$3E,$00,$4E,$56
	dc.b $FE,$00,$20,$6E,$00,$08,$43,$EE,$FF,$00,$70,$7F,$32,$D8,$51,$C8
	dc.b $FF,$FC,$3F,$2E,$00,$0C,$48,$6E,$FE,$00,$1F,$3C,$00,$01,$4E,$AD
	dc.b $07,$BA,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2,$48,$6D,$D2,$6E,$48,$7A
	dc.b $00,$6C,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E,$48,$6E,$FF,$00
	dc.b $42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2,$48,$6D
	dc.b $D2,$6E,$48,$7A,$00,$44,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E
	dc.b $48,$6E,$FE,$00,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E,$4E,$AD
	dc.b $09,$F2,$48,$7A,$00,$18,$4E,$BA,$FE,$5E,$4E,$5E,$20,$5F,$5C,$4F
	dc.b $4E,$D0,$87,$49,$4F,$41,$42,$4F,$52,$54,$00,$16,$0A,$3C,$3C,$3C
	dc.b $49,$4E,$54,$52,$3E,$3E,$3E,$00,$02,$23,$20,$00,$04,$23,$23,$23
	dc.b $20,$00,$4E,$56,$00,$00,$1B,$7C,$00,$01,$EC,$C1,$4E,$5E,$4E,$75
	dc.b $84,$49,$4E,$54,$52,$00,$00,$00,$4E,$56,$FF,$FC,$70,$02,$B0,$2D
	dc.b $F3,$95,$66,$10,$52,$6D,$FD,$EA,$30,$2D,$FD,$EA,$41,$ED,$FD,$EC
	dc.b $42,$30,$00,$00,$3D,$6D,$FD,$EA,$FF,$FC,$4A,$2D,$F3,$95,$66,$0A
	dc.b $52,$6E,$FF,$FC,$3D,$6D,$FD,$EA,$FF,$FE,$70,$01,$B0,$6E,$00,$08
	dc.b $67,$50,$08,$2E,$00,$00,$FF,$FD,$67,$14,$52,$6D,$FD,$EA,$30,$2D
	dc.b $FD,$EA,$41,$ED,$FD,$EC,$42,$30,$00,$00,$52,$6E,$FF,$FC,$70,$04
	dc.b $B0,$6E,$00,$08,$57,$C0,$4A,$00,$67,$28,$08,$2E,$00,$01,$FF,$FD
	dc.b $56,$C1,$C0,$01,$67,$1C,$30,$2D,$FD,$EA,$52,$40,$41,$ED,$FD,$EC
	dc.b $42,$30,$00,$00,$30,$2D,$FD,$EA,$54,$40,$42,$30,$00,$00,$54,$6D
	dc.b $FD,$EA,$4A,$2D,$F3,$95,$66,$12,$52,$6D,$FD,$EA,$30,$2D,$FD,$EA
	dc.b $41,$ED,$FD,$EC,$11,$AE,$FF,$FF,$00,$00,$1B,$6D,$FD,$EB,$FD,$EC
	dc.b $4E,$5E,$20,$5F,$54,$4F,$4E,$D0,$89,$46,$4F,$52,$4D,$41,$54,$53
	dc.b $54,$52,$00,$00,$4E,$56,$FF,$F6,$48,$E7,$0F,$08,$28,$6E,$00,$0A
	dc.b $18,$2E,$00,$08,$7E,$00,$70,$04,$B0,$04,$66,$2E,$42,$45,$1A,$14
	dc.b $70,$04,$B0,$45,$6C,$0A,$3F,$3C,$00,$2F,$4E,$AD,$07,$CA,$60,$54
	dc.b $7C,$01,$BA,$46,$6D,$4E,$20,$07,$E1,$88,$42,$41,$12,$34,$60,$00
	dc.b $48,$C1,$2E,$01,$DE,$80,$52,$46,$60,$E8,$70,$05,$B0,$04,$66,$22
	dc.b $42,$A7,$2F,$0C,$48,$6E,$FF,$F7,$4E,$BA,$DB,$96,$2E,$1F,$4A,$2E
	dc.b $FF,$F7,$67,$20,$3F,$3C,$00,$88,$2F,$0C,$4E,$AD,$07,$C2,$7E,$00
	dc.b $60,$12,$3F,$3C,$00,$87,$4E,$AD,$07,$CA,$70,$06,$B0,$04,$67,$04
	dc.b $49,$ED,$FD,$EC,$2D,$47,$00,$0E,$41,$ED,$FD,$EC,$B1,$CC,$67,$0A
	dc.b $2F,$2D,$F0,$D6,$2F,$0C,$4E,$AD,$07,$82,$4C,$DF,$10,$F0,$4E,$5E
	dc.b $20,$5F,$5C,$4F,$4E,$D0,$89,$53,$54,$52,$49,$4E,$47,$43,$56,$54
	dc.b $00,$00,$4E,$56,$FF,$FC,$42,$2E,$00,$0C,$42,$67,$2F,$2E,$00,$08
	dc.b $48,$6E,$FF,$FF,$48,$6E,$FF,$FC,$4E,$BA,$15,$9A,$10,$1F,$67,$1A
	dc.b $70,$04,$B0,$2E,$FF,$FF,$6F,$0A,$3F,$3C,$00,$7A,$4E,$AD,$07,$CA
	dc.b $60,$10,$1D,$7C,$00,$01,$00,$0C,$60,$08,$3F,$2E,$FF,$FC,$4E,$AD
	dc.b $07,$CA,$4E,$5E,$2E,$9F,$4E,$75,$87,$53,$54,$52,$45,$58,$50,$52
	dc.b $00,$00,$4E,$56,$FF,$FC,$42,$2E,$00,$0C,$42,$67,$2F,$2E,$00,$08
	dc.b $48,$6E,$FF,$FF,$48,$6E,$FF,$FC,$4E,$BA,$15,$4A,$10,$1F,$67,$54
	dc.b $4A,$2E,$FF,$FF,$5E,$C0,$4A,$00,$67,$42,$72,$10,$B2,$2E,$FF,$FF
	dc.b $56,$C1,$C0,$01,$67,$36,$70,$04,$B0,$2E,$FF,$FF,$6E,$24,$20,$6E
	dc.b $00,$08,$2F,$08,$42,$A7,$22,$6E,$00,$08,$2F,$11,$1F,$2E,$FF,$FF
	dc.b $4E,$BA,$FE,$B2,$20,$1F,$20,$5F,$20,$80,$1D,$7C,$00,$01,$00,$0C
	dc.b $60,$1A,$3F,$3C,$00,$2E,$4E,$AD,$07,$CA,$60,$10,$1D,$7C,$00,$01
	dc.b $00,$0C,$60,$08,$3F,$2E,$FF,$FC,$4E,$AD,$07,$CA,$4E,$5E,$2E,$9F
	dc.b $4E,$75,$87,$41,$42,$53,$45,$58,$50,$52,$00,$00,$4E,$56,$FF,$FC
	dc.b $2F,$0C,$42,$2E,$00,$0C,$70,$00,$20,$6E,$00,$08,$30,$28,$00,$08
	dc.b $C0,$BC,$00,$00,$94,$02,$0C,$80,$00,$00,$94,$02,$66,$34,$42,$A7
	dc.b $2F,$2E,$00,$08,$4E,$BA,$DE,$E6,$28,$5F,$58,$8C,$20,$0C,$56,$C0
	dc.b $4A,$00,$67,$1E,$22,$14,$B2,$AD,$F3,$AC,$56,$C1,$C0,$01,$67,$12
	dc.b $22,$14,$B2,$AD,$F3,$B0,$56,$C1,$C0,$01,$67,$06,$1D,$7C,$00,$01
	dc.b $00,$0C,$28,$5F,$4E,$5E,$2E,$9F,$4E,$75,$8D,$49,$53,$54,$59,$50
	dc.b $45,$44,$49,$4D,$50,$4F,$52,$54,$00,$00,$4E,$56,$FF,$F2,$48,$E7
	dc.b $00,$18,$42,$2E,$00,$10,$20,$6E,$00,$08,$70,$00,$20,$80,$42,$A7
	dc.b $2F,$2D,$F3,$B0,$20,$6E,$00,$0C,$2F,$10,$48,$6E,$FF,$FA,$48,$6E
	dc.b $FF,$FE,$4E,$BA,$DC,$30,$28,$5F,$20,$0C,$67,$58,$70,$00,$30,$2E
	dc.b $FF,$FE,$72,$00,$32,$3C,$50,$00,$C0,$81,$0C,$80,$00,$00,$50,$00
	dc.b $57,$C0,$4A,$00,$66,$16,$2F,$00,$42,$67,$2F,$0C,$4E,$BA,$FF,$3E
	dc.b $12,$1F,$20,$1F,$80,$01,$02,$40,$00,$01,$67,$28,$42,$A7,$2F,$0C
	dc.b $4E,$BA,$DE,$3A,$26,$5F,$58,$8B,$4A,$93,$67,$18,$20,$53,$41,$E8
	dc.b $00,$0C,$22,$6E,$00,$0C,$22,$88,$20,$6E,$00,$08,$20,$8C,$1D,$7C
	dc.b $00,$01,$00,$10,$4C,$DF,$18,$00,$4E,$5E,$20,$5F,$50,$4F,$4E,$D0
	dc.b $8B,$49,$53,$54,$59,$50,$45,$44,$44,$41,$54,$41,$00,$00,$4E,$56
	dc.b $FF,$F0,$48,$E7,$03,$18,$2E,$2E,$00,$18,$20,$47,$70,$00,$20,$80
	dc.b $20,$6E,$00,$08,$70,$00,$20,$80,$26,$6D,$EC,$A8,$20,$0B,$67,$00
	dc.b $01,$6E,$28,$53,$20,$0C,$67,$00,$01,$5E,$20,$54,$41,$E8,$00,$0C
	dc.b $2D,$48,$FF,$F0,$20,$47,$2F,$08,$42,$A7,$2F,$2C,$00,$04,$2F,$2E
	dc.b $FF,$F0,$2F,$2E,$00,$1E,$2F,$2E,$00,$14,$2F,$2E,$00,$10,$2F,$2E
	dc.b $00,$0C,$3F,$2E,$00,$1C,$4E,$BA,$DC,$F0,$20,$1F,$20,$5F,$20,$80
	dc.b $20,$47,$4A,$90,$57,$C0,$4A,$00,$67,$4A,$12,$2C,$00,$08,$0A,$01
	dc.b $00,$01,$C0,$01,$67,$3E,$42,$67,$48,$6E,$FF,$F0,$2F,$2E,$00,$08
	dc.b $4E,$BA,$FE,$D8,$10,$1F,$67,$2C,$20,$47,$2F,$08,$42,$A7,$2F,$2D
	dc.b $F3,$B0,$2F,$2E,$FF,$F0,$2F,$2E,$00,$1E,$2F,$2E,$00,$14,$2F,$2E
	dc.b $00,$10,$2F,$2E,$00,$0C,$3F,$2E,$00,$1C,$4E,$BA,$DC,$9C,$20,$1F
	dc.b $20,$5F,$20,$80,$20,$47,$4A,$90,$67,$00,$00,$C4,$10,$2C,$00,$08
	dc.b $67,$30,$42,$A7,$2F,$14,$4E,$BA,$DD,$34,$2C,$1F,$20,$46,$4A,$90
	dc.b $6C,$16,$20,$6E,$00,$0C,$22,$46,$20,$10,$90,$91,$D0,$AC,$00,$0E
	dc.b $20,$6E,$00,$0C,$20,$80,$60,$0A,$20,$6E,$00,$0C,$20,$2C,$00,$0E
	dc.b $D1,$90,$20,$6E,$00,$08,$20,$AC,$00,$0A,$20,$6E,$00,$08,$4A,$90
	dc.b $66,$1A,$70,$00,$20,$6E,$00,$10,$30,$10,$22,$3C,$00,$00,$10,$00
	dc.b $46,$81,$C0,$81,$20,$6E,$00,$10,$30,$80,$60,$72,$70,$00,$20,$6E
	dc.b $00,$08,$20,$50,$30,$28,$00,$08,$72,$00,$32,$3C,$50,$00,$C0,$81
	dc.b $0C,$80,$00,$00,$50,$00,$66,$30,$20,$6E,$00,$10,$08,$28,$00,$01
	dc.b $00,$01,$57,$C0,$4A,$00,$67,$20,$72,$00,$32,$10,$74,$00,$34,$3C
	dc.b $10,$01,$C2,$82,$0C,$81,$00,$00,$10,$01,$57,$C1,$C0,$01,$67,$08
	dc.b $20,$6E,$00,$08,$70,$00,$20,$80,$70,$00,$20,$6E,$00,$10,$30,$10
	dc.b $80,$BC,$00,$00,$10,$00,$20,$6E,$00,$10,$30,$80,$60,$10,$28,$6C
	dc.b $00,$12,$60,$00,$FE,$A0,$26,$6B,$00,$04,$60,$00,$FE,$90,$4C,$DF
	dc.b $18,$C0,$4E,$5E,$20,$5F,$DE,$FC,$00,$1A,$4E,$D0,$89,$43,$48,$45
	dc.b $43,$4B,$57,$49,$54,$48,$00,$00,$4E,$56,$00,$00,$70,$1D,$B0,$2D
	dc.b $FF,$FB,$66,$12,$4E,$BA,$E7,$BC,$4A,$2D,$FF,$FB,$67,$02,$60,$06
	dc.b $4E,$BA,$E7,$B0,$60,$E6,$4E,$5E,$4E,$75,$92,$53,$4B,$49,$50,$51
	dc.b $55,$41,$4C,$49,$46,$49,$43,$41,$54,$49,$4F,$4E,$53,$00,$00,$00
	dc.b $4E,$56,$FB,$DE,$48,$E7,$0F,$18,$20,$6E,$00,$08,$70,$00,$20,$80
	dc.b $1D,$7C,$00,$01,$FF,$FB,$78,$01,$20,$6E,$00,$14,$70,$00,$20,$80
	dc.b $7E,$00,$7C,$01,$2F,$2E,$00,$18,$48,$6E,$FD,$DE,$4E,$BA,$D5,$B6
	dc.b $2F,$2E,$00,$18,$48,$6E,$FE,$DE,$4E,$BA,$D5,$AA,$4A,$AD,$EC,$A8
	dc.b $67,$68,$42,$67,$2F,$2E,$00,$18,$4E,$BA,$D7,$E2,$3A,$1F,$2F,$2E
	dc.b $00,$18,$3F,$05,$2F,$2E,$00,$10,$48,$6E,$FF,$EA,$2F,$2E,$00,$0C
	dc.b $48,$6E,$FF,$EE,$2F,$2E,$00,$08,$4E,$BA,$FD,$B4,$20,$6E,$00,$10
	dc.b $4A,$90,$67,$36,$42,$04,$20,$6E,$00,$0C,$08,$10,$00,$07,$66,$00
	dc.b $02,$DE,$3F,$3C,$00,$10,$2F,$2E,$00,$18,$4E,$AD,$07,$C2,$20,$6E
	dc.b $00,$14,$70,$00,$20,$80,$20,$6E,$00,$10,$70,$00,$20,$80,$4E,$BA
	dc.b $FF,$28,$42,$2E,$00,$1C,$60,$00,$03,$DA,$4E,$BA,$E6,$E6,$4A,$2D
	dc.b $FF,$FB,$67,$24,$3F,$3C,$00,$0F,$48,$6E,$FE,$DE,$4E,$AD,$07,$C2
	dc.b $20,$6E,$00,$14,$70,$00,$20,$80,$20,$6E,$00,$10,$70,$00,$20,$80
	dc.b $42,$2E,$00,$1C,$60,$00,$03,$AC,$42,$67,$48,$6D,$FE,$FA,$4E,$BA
	dc.b $D7,$4C,$3A,$1F,$20,$6E,$00,$10,$70,$00,$20,$80,$70,$00,$2D,$40
	dc.b $FF,$EA,$10,$06,$67,$2C,$20,$6E,$00,$10,$2F,$08,$42,$A7,$2F,$2D
	dc.b $F3,$AC,$2F,$2E,$00,$18,$48,$6D,$FE,$FA,$48,$6E,$FF,$EA,$2F,$2E
	dc.b $00,$0C,$48,$6E,$FF,$EE,$3F,$05,$4E,$BA,$DA,$4E,$20,$1F,$20,$5F
	dc.b $20,$80,$10,$04,$67,$00,$00,$EE,$20,$6E,$00,$10,$4A,$90,$57,$C1
	dc.b $C0,$01,$67,$00,$00,$E0,$42,$04,$10,$2D,$F3,$A5,$67,$00,$00,$BA
	dc.b $20,$6E,$00,$10,$2F,$08,$42,$A7,$2F,$2D,$F3,$AC,$2F,$2E,$00,$18
	dc.b $48,$6E,$FF,$F6,$2F,$2E,$00,$0C,$4E,$BA,$D8,$7A,$20,$1F,$20,$5F
	dc.b $20,$80,$20,$6E,$00,$10,$4A,$90,$56,$C0,$4A,$00,$67,$00,$00,$82
	dc.b $72,$00,$20,$6E,$00,$0C,$32,$10,$C2,$BC,$00,$00,$90,$02,$0C,$81
	dc.b $00,$00,$90,$02,$57,$C1,$C0,$01,$67,$66,$42,$A7,$20,$6E,$00,$10
	dc.b $2F,$10,$4E,$BA,$DA,$88,$26,$5F,$58,$8B,$20,$53,$41,$E8,$00,$0C
	dc.b $2D,$48,$00,$18,$42,$A7,$2F,$13,$4E,$BA,$DA,$72,$28,$5F,$42,$67
	dc.b $20,$6E,$00,$10,$2F,$10,$4E,$BA,$FB,$54,$10,$1F,$67,$04,$7E,$00
	dc.b $60,$0A,$4A,$94,$6C,$04,$2E,$14,$60,$02,$7E,$00,$20,$6E,$00,$10
	dc.b $22,$6E,$00,$08,$22,$90,$20,$0C,$58,$80,$2D,$40,$FF,$DE,$20,$6E
	dc.b $FF,$DE,$20,$2D,$F3,$AC,$B0,$90,$57,$C6,$44,$06,$60,$00,$FE,$F6
	dc.b $20,$6E,$00,$10,$70,$00,$20,$80,$20,$6E,$00,$10,$4A,$90,$66,$14
	dc.b $42,$67,$48,$6E,$00,$18,$2F,$2E,$00,$08,$4E,$BA,$FB,$6E,$10,$1F
	dc.b $66,$00,$FE,$D2,$20,$6E,$00,$10,$4A,$90,$57,$C0,$4A,$00,$67,$30
	dc.b $C0,$2D,$F3,$A5,$67,$2A,$2F,$08,$42,$A7,$2F,$2D,$F3,$B0,$2F,$2E
	dc.b $00,$18,$48,$6D,$FE,$FA,$48,$6E,$FF,$EA,$2F,$2E,$00,$0C,$48,$6E
	dc.b $FF,$EE,$3F,$05,$4E,$BA,$D9,$22,$20,$1F,$20,$5F,$20,$80,$42,$06
	dc.b $10,$2E,$FF,$FB,$67,$5C,$20,$6E,$00,$08,$4A,$90,$57,$C1,$C0,$01
	dc.b $4A,$00,$67,$4E,$4A,$AE,$FF,$EA,$56,$C1,$C0,$01,$4A,$00,$67,$42
	dc.b $20,$6E,$00,$0C,$08,$10,$00,$04,$56,$C1,$C0,$01,$67,$34,$70,$00
	dc.b $30,$10,$72,$00,$32,$3C,$0A,$00,$C0,$81,$4A,$80,$66,$0A,$20,$6E
	dc.b $00,$08,$20,$AE,$FF,$EA,$60,$1A,$20,$6E,$00,$0C,$08,$10,$00,$07
	dc.b $67,$10,$20,$6E,$FF,$EA,$20,$68,$00,$04,$22,$6E,$00,$08,$22,$A8
	dc.b $00,$02,$48,$6D,$FE,$FA,$48,$6E,$FE,$DE,$4E,$BA,$D3,$28,$4E,$BA
	dc.b $E4,$D2,$20,$6E,$00,$10,$4A,$90,$57,$C0,$4A,$00,$66,$10,$20,$6E
	dc.b $00,$0C,$08,$10,$00,$07,$57,$C1,$80,$01,$67,$00,$00,$82,$10,$2E
	dc.b $FF,$FB,$67,$2A,$48,$6E,$FD,$DE,$48,$7A,$01,$C0,$48,$6D,$FE,$FA
	dc.b $48,$6E,$FB,$DE,$3F,$3C,$00,$03,$4E,$AD,$0A,$A2,$41,$EE,$FC,$DE
	dc.b $43,$EE,$FB,$DE,$70,$7F,$30,$D9,$51,$C8,$FF,$FC,$60,$28,$48,$6E
	dc.b $FD,$DE,$48,$7A,$01,$92,$48,$6D,$FE,$FA,$48,$6E,$FB,$DE,$3F,$3C
	dc.b $00,$03,$4E,$AD,$0A,$A2,$41,$EE,$FC,$DE,$43,$EE,$FB,$DE,$70,$7F
	dc.b $30,$D9,$51,$C8,$FF,$FC,$3F,$3C,$00,$10,$48,$6E,$FC,$DE,$4E,$AD
	dc.b $07,$C2,$20,$6E,$00,$14,$70,$00,$20,$80,$20,$6E,$00,$10,$70,$00
	dc.b $20,$80,$4E,$BA,$FC,$74,$42,$2E,$00,$1C,$60,$00,$01,$26,$20,$6E
	dc.b $00,$14,$20,$2E,$FF,$EE,$90,$87,$D1,$90,$70,$1D,$B0,$2D,$FF,$FB
	dc.b $66,$00,$00,$88,$20,$6E,$00,$0C,$08,$28,$00,$01,$00,$01,$67,$52
	dc.b $42,$A7,$20,$6E,$00,$10,$2F,$10,$4E,$BA,$D8,$92,$26,$5F,$58,$8B
	dc.b $20,$53,$41,$E8,$00,$0C,$2D,$48,$00,$18,$42,$A7,$2F,$13,$4E,$BA
	dc.b $D8,$7C,$28,$5F,$4A,$94,$6C,$04,$2E,$14,$60,$02,$7E,$00,$10,$06
	dc.b $67,$16,$20,$0C,$58,$80,$2D,$40,$FF,$DE,$20,$6E,$FF,$DE,$20,$2D
	dc.b $F3,$AC,$B0,$90,$57,$C6,$44,$06,$42,$2E,$FF,$FB,$42,$04,$60,$00
	dc.b $FC,$DA,$3F,$3C,$00,$B7,$48,$6E,$FE,$DE,$4E,$AD,$07,$C2,$20,$6E
	dc.b $00,$14,$70,$00,$20,$80,$20,$6E,$00,$10,$70,$00,$20,$80,$4E,$BA
	dc.b $FB,$D8,$42,$2E,$00,$1C,$60,$00,$00,$8A,$20,$6E,$00,$08,$4A,$90
	dc.b $66,$1A,$70,$00,$20,$6E,$00,$0C,$30,$10,$22,$3C,$00,$00,$10,$00
	dc.b $46,$81,$C0,$81,$20,$6E,$00,$0C,$30,$80,$60,$60,$70,$00,$20,$6E
	dc.b $00,$08,$20,$50,$30,$28,$00,$08,$72,$00,$32,$3C,$50,$00,$C0,$81
	dc.b $0C,$80,$00,$00,$50,$00,$66,$30,$20,$6E,$00,$0C,$08,$28,$00,$01
	dc.b $00,$01,$57,$C0,$4A,$00,$67,$20,$72,$00,$32,$10,$74,$00,$34,$3C
	dc.b $10,$01,$C2,$82,$0C,$81,$00,$00,$10,$01,$57,$C1,$C0,$01,$67,$08
	dc.b $20,$6E,$00,$08,$70,$00,$20,$80,$70,$00,$20,$6E,$00,$0C,$30,$10
	dc.b $80,$BC,$00,$00,$10,$00,$20,$6E,$00,$0C,$30,$80,$1D,$7C,$00,$01
	dc.b $00,$1C,$4C,$DF,$18,$F0,$4E,$5E,$20,$5F,$DE,$FC,$00,$14,$4E,$D0
	dc.b $92,$53,$43,$41,$4E,$51,$55,$41,$4C,$49,$46,$49,$43,$41,$54,$49
	dc.b $4F,$4E,$53,$00,$00,$06,$03,$2E,$2E,$2E,$01,$2E,$4E,$56,$FF,$EE
	dc.b $48,$E7,$01,$08,$28,$6E,$00,$18,$42,$67,$2F,$0C,$4E,$BA,$D3,$6E
	dc.b $3E,$1F,$20,$6E,$00,$14,$70,$00,$20,$80,$20,$6E,$00,$08,$42,$10
	dc.b $4A,$AD,$EC,$A8,$67,$30,$2F,$0C,$3F,$07,$2F,$2E,$00,$14,$2F,$2E
	dc.b $00,$10,$2F,$2E,$00,$0C,$48,$6E,$FF,$FA,$48,$6E,$FF,$EE,$4E,$BA
	dc.b $F9,$2E,$20,$6E,$00,$14,$4A,$90,$67,$0C,$20,$6E,$00,$10,$20,$AE
	dc.b $FF,$FA,$60,$00,$01,$08,$10,$2D,$F3,$A2,$67,$30,$20,$6E,$00,$14
	dc.b $2F,$08,$42,$A7,$2F,$2D,$F3,$AC,$22,$6D,$F3,$EA,$48,$69,$00,$0C
	dc.b $2F,$0C,$2F,$2E,$00,$10,$2F,$2E,$00,$0C,$48,$6E,$FF,$FA,$3F,$07
	dc.b $4E,$BA,$D6,$36,$20,$1F,$20,$5F,$20,$80,$60,$5A,$10,$2D,$F3,$A4
	dc.b $67,$54,$20,$6E,$00,$14,$2F,$08,$42,$A7,$2F,$2D,$F3,$A8,$2F,$0C
	dc.b $2F,$2E,$00,$10,$2F,$2E,$00,$0C,$3F,$07,$4E,$BA,$D4,$70,$20,$1F
	dc.b $20,$5F,$20,$80,$20,$6E,$00,$14,$4A,$90,$66,$2A,$2F,$08,$42,$A7
	dc.b $2F,$2D,$F3,$B0,$22,$6D,$F3,$EE,$48,$69,$00,$0C,$2F,$0C,$2F,$2E
	dc.b $00,$10,$2F,$2E,$00,$0C,$48,$6E,$FF,$FA,$3F,$07,$4E,$BA,$D5,$DA
	dc.b $20,$1F,$20,$5F,$20,$80,$20,$6E,$00,$14,$4A,$90,$67,$0A,$20,$6E
	dc.b $00,$10,$20,$AE,$FF,$FA,$60,$34,$20,$6E,$00,$14,$2F,$08,$42,$A7
	dc.b $2F,$2D,$F3,$AC,$2F,$0C,$2F,$2E,$00,$10,$2F,$2E,$00,$0C,$3F,$07
	dc.b $4E,$BA,$D4,$0A,$20,$1F,$20,$5F,$20,$80,$20,$6E,$00,$14,$4A,$90
	dc.b $67,$0A,$20,$6E,$00,$08,$10,$BC,$00,$01,$60,$30,$20,$6E,$00,$14
	dc.b $4A,$90,$57,$C0,$4A,$00,$67,$24,$C0,$2D,$F3,$A5,$67,$1E,$2F,$08
	dc.b $42,$A7,$2F,$2D,$F3,$B0,$2F,$0C,$2F,$2E,$00,$10,$2F,$2E,$00,$0C
	dc.b $3F,$07,$4E,$BA,$D3,$C8,$20,$1F,$20,$5F,$20,$80,$4C,$DF,$10,$80
	dc.b $4E,$5E,$20,$5F,$DE,$FC,$00,$14,$4E,$D0,$88,$4C,$4F,$4F,$4B,$55
	dc.b $50,$49,$44,$00,$00,$00,$4E,$56,$00,$00,$2F,$0C,$28,$6E,$00,$08
	dc.b $20,$6C,$00,$08,$30,$AE,$00,$0C,$20,$6C,$00,$10,$70,$00,$20,$80
	dc.b $20,$6C,$00,$0C,$42,$10,$1B,$6C,$FE,$EF,$F3,$A0,$10,$2D,$EC,$E2
	dc.b $66,$06,$80,$2D,$EC,$E3,$67,$18,$1B,$6C,$FE,$F5,$F3,$57,$1B,$6C
	dc.b $FE,$F7,$F2,$23,$1B,$6C,$FE,$F9,$F3,$6F,$39,$6C,$FE,$FA,$FE,$F2
	dc.b $1B,$6C,$FE,$F1,$EC,$E1,$20,$6E,$00,$08,$42,$28,$00,$14,$20,$6E
	dc.b $00,$08,$2C,$48,$4E,$FA,$12,$14,$00,$00,$28,$5F,$4E,$5E,$20,$5F
	dc.b $5C,$4F,$4E,$D0,$89,$45,$58,$50,$52,$45,$52,$52,$4F,$52,$00,$00
	dc.b $4E,$56,$00,$00,$48,$E7,$00,$28,$28,$6E,$00,$08,$4A,$2C,$FE,$EE
	dc.b $67,$0C,$3F,$3C,$00,$0D,$2F,$2E,$00,$08,$4E,$BA,$FF,$6A,$10,$2D
	dc.b $F3,$6F,$48,$80,$53,$40,$1B,$40,$F3,$6F,$10,$2D,$F3,$57,$48,$80
	dc.b $20,$6C,$00,$0C,$43,$ED,$F2,$24,$10,$B1,$00,$00,$10,$2D,$F3,$57
	dc.b $48,$80,$E5,$40,$20,$6C,$00,$10,$45,$ED,$F2,$62,$20,$B2,$00,$00
	dc.b $1B,$6C,$FE,$EF,$F3,$A0,$10,$2D,$EC,$E2,$66,$06,$80,$2D,$EC,$E3
	dc.b $67,$18,$1B,$6C,$FE,$F5,$F3,$57,$1B,$6C,$FE,$F7,$F2,$23,$1B,$6C
	dc.b $FE,$F9,$F3,$6F,$39,$6C,$FE,$FA,$FE,$F2,$1B,$6C,$FE,$F1,$EC,$E1
	dc.b $20,$6E,$00,$08,$11,$7C,$00,$01,$00,$14,$20,$6E,$00,$08,$2C,$48
	dc.b $4E,$FA,$11,$68,$00,$00,$4C,$DF,$14,$00,$4E,$5E,$2E,$9F,$4E,$75
	dc.b $8B,$52,$45,$54,$55,$52,$4E,$56,$41,$4C,$55,$45,$00,$00,$4E,$56
	dc.b $00,$00,$70,$14,$B0,$2D,$F3,$6F,$66,$0C,$3F,$3C,$00,$0B,$2F,$2E
	dc.b $00,$08,$4E,$BA,$FE,$C2,$10,$2D,$F3,$6F,$48,$80,$52,$40,$1B,$40
	dc.b $F3,$6F,$48,$80,$41,$ED,$F3,$58,$11,$AE,$00,$0C,$00,$00,$70,$00
	dc.b $2B,$40,$F3,$CE,$4E,$5E,$20,$5F,$5C,$4F,$4E,$D0,$87,$53,$54,$41
	dc.b $43,$4B,$4F,$50,$00,$00,$4E,$56,$00,$00,$70,$3C,$B0,$2D,$F3,$57
	dc.b $66,$0C,$3F,$3C,$00,$0A,$2F,$2E,$00,$08,$4E,$BA,$FE,$7A,$10,$2D
	dc.b $F3,$57,$48,$80,$52,$40,$1B,$40,$F3,$57,$48,$80,$E5,$40,$41,$ED
	dc.b $F2,$62,$21,$AE,$00,$0E,$00,$00,$10,$2D,$F3,$57,$48,$80,$43,$ED
	dc.b $F2,$24,$13,$AE,$00,$0C,$00,$00,$4E,$5E,$20,$5F,$DE,$FC,$00,$0A
	dc.b $4E,$D0,$88,$4F,$55,$54,$5F,$4F,$50,$4E,$44,$00,$00,$00,$4E,$56
	dc.b $FF,$FA,$48,$E7,$11,$08,$28,$6E,$00,$0E,$1E,$2E,$00,$12,$70,$04
	dc.b $B0,$14,$57,$C0,$4A,$00,$66,$0A,$72,$05,$B2,$14,$57,$C1,$80,$01
	dc.b $67,$4E,$70,$01,$B0,$07,$5C,$C0,$4A,$00,$66,$28,$12,$2E,$00,$08
	dc.b $0A,$01,$00,$01,$4A,$01,$67,$38,$74,$04,$B4,$07,$57,$C2,$4A,$02
	dc.b $66,$12,$76,$05,$B6,$07,$57,$C3,$84,$03,$C2,$02,$80,$01,$02,$40
	dc.b $00,$01,$67,$1C,$20,$6E,$00,$0A,$2F,$08,$42,$A7,$22,$6E,$00,$0A
	dc.b $2F,$11,$1F,$14,$4E,$BA,$F3,$2E,$20,$1F,$20,$5F,$20,$80,$42,$14
	dc.b $4C,$DF,$10,$88,$4E,$5E,$20,$5F,$DE,$FC,$00,$0C,$4E,$D0,$8B,$43
	dc.b $48,$4B,$4F,$50,$4E,$44,$54,$59,$50,$45,$00,$00,$4E,$56,$FF,$EC
	dc.b $48,$E7,$03,$18,$1E,$2E,$00,$0C,$10,$2D,$F3,$57,$48,$80,$E5,$40
	dc.b $41,$ED,$F2,$62,$2D,$70,$00,$00,$FF,$FC,$10,$2D,$F3,$57,$48,$80
	dc.b $43,$ED,$F2,$24,$1D,$71,$00,$00,$FF,$F7,$70,$10,$B0,$2E,$FF,$F7
	dc.b $66,$18,$2F,$2D,$F0,$D6,$2F,$2E,$FF,$FC,$4E,$AD,$07,$82,$3F,$3C
	dc.b $00,$0C,$2F,$2E,$00,$08,$4E,$BA,$FD,$5E,$70,$16,$B0,$07,$57,$C0
	dc.b $4A,$00,$66,$16,$72,$15,$B2,$07,$57,$C1,$80,$01,$66,$0C,$72,$14
	dc.b $B2,$07,$57,$C1,$80,$01,$67,$00,$00,$90,$42,$67,$48,$6E,$FF,$F7
	dc.b $48,$6E,$FF,$FC,$42,$67,$4E,$BA,$FE,$F6,$70,$16,$B0,$07,$66,$26
	dc.b $70,$01,$B0,$2E,$FF,$F7,$6C,$0C,$3F,$3C,$00,$14,$2F,$2E,$00,$08
	dc.b $4E,$BA,$FD,$14,$20,$2E,$FF,$FC,$44,$80,$2D,$40,$FF,$F8,$42,$2E
	dc.b $FF,$F6,$60,$00,$05,$2E,$70,$15,$B0,$07,$66,$26,$4A,$2E,$FF,$F7
	dc.b $6F,$0C,$3F,$3C,$00,$14,$2F,$2E,$00,$08,$4E,$BA,$FC,$EA,$70,$FF
	dc.b $22,$2E,$FF,$FC,$B3,$80,$2D,$40,$FF,$F8,$42,$2E,$FF,$F6,$60,$00
	dc.b $05,$02,$4A,$2E,$FF,$F7,$6F,$0C,$3F,$3C,$00,$14,$2F,$2E,$00,$08
	dc.b $4E,$BA,$FC,$C4,$70,$01,$22,$2E,$FF,$FC,$B3,$80,$2D,$40,$FF,$F8
	dc.b $42,$2E,$FF,$F6,$60,$00,$04,$DC,$10,$2D,$F3,$57,$48,$80,$53,$40
	dc.b $1B,$40,$F3,$57,$48,$80,$E5,$40,$41,$ED,$F2,$62,$2D,$70,$00,$00
	dc.b $FF,$F8,$10,$2D,$F3,$57,$48,$80,$43,$ED,$F2,$24,$1D,$71,$00,$00
	dc.b $FF,$F6,$70,$10,$B0,$2E,$FF,$F6,$66,$18,$2F,$2D,$F0,$D6,$2F,$2E
	dc.b $FF,$F8,$4E,$AD,$07,$82,$3F,$3C,$00,$0C,$2F,$2E,$00,$08,$4E,$BA
	dc.b $FC,$66,$70,$0C,$B0,$07,$5F,$C0,$4A,$00,$67,$08,$72,$11,$B2,$07
	dc.b $5C,$C1,$C0,$01,$44,$00,$1C,$00,$1F,$2E,$FF,$F6,$48,$6E,$FF,$F7
	dc.b $48,$6E,$FF,$FC,$1F,$06,$4E,$BA,$FE,$06,$1F,$2E,$FF,$F7,$48,$6E
	dc.b $FF,$F6,$48,$6E,$FF,$F8,$1F,$06,$4E,$BA,$FD,$F4,$10,$06,$67,$00
	dc.b $01,$26,$72,$04,$B2,$2E,$FF,$F6,$5F,$C1,$4A,$01,$66,$10,$74,$04
	dc.b $B4,$2E,$FF,$F7,$5F,$C2,$82,$02,$C0,$01,$67,$00,$01,$0A,$28,$6E
	dc.b $FF,$F8,$26,$6E,$FF,$FC,$70,$04,$B0,$2E,$FF,$F6,$6F,$1E,$70,$04
	dc.b $B0,$2E,$FF,$F7,$6E,$0A,$2F,$2D,$F0,$D6,$2F,$0B,$4E,$AD,$07,$82
	dc.b $3F,$3C,$00,$0E,$2F,$2E,$00,$08,$4E,$BA,$FB,$DC,$70,$04,$B0,$2E
	dc.b $FF,$F7,$6F,$16,$2F,$2D,$F0,$D6,$2F,$0C,$4E,$AD,$07,$82,$3F,$3C
	dc.b $00,$0E,$2F,$2E,$00,$08,$4E,$BA,$FB,$BE,$10,$07,$48,$80,$04,$40
	dc.b $00,$0C,$6B,$00,$00,$96,$0C,$40,$00,$05,$6E,$00,$00,$8E,$D0,$40
	dc.b $30,$3B,$00,$06,$4E,$FB,$00,$00,$00,$0E,$00,$22,$00,$36,$00,$4A
	dc.b $00,$5E,$00,$72,$2F,$0C,$2F,$0B,$4E,$AD,$0A,$CA,$10,$1F,$48,$80
	dc.b $48,$C0,$2D,$40,$FF,$F8,$60,$62,$2F,$0C,$2F,$0B,$4E,$AD,$0A,$C2
	dc.b $10,$1F,$48,$80,$48,$C0,$2D,$40,$FF,$F8,$60,$4E,$2F,$0C,$2F,$0B
	dc.b $4E,$AD,$0A,$E2,$10,$1F,$48,$80,$48,$C0,$2D,$40,$FF,$F8,$60,$3A
	dc.b $2F,$0C,$2F,$0B,$4E,$AD,$0A,$D2,$10,$1F,$48,$80,$48,$C0,$2D,$40
	dc.b $FF,$F8,$60,$26,$2F,$0C,$2F,$0B,$4E,$AD,$0A,$EA,$10,$1F,$48,$80
	dc.b $48,$C0,$2D,$40,$FF,$F8,$60,$12,$2F,$0C,$2F,$0B,$4E,$AD,$0A,$DA
	dc.b $10,$1F,$48,$80,$48,$C0,$2D,$40,$FF,$F8,$2F,$2D,$F0,$D6,$2F,$0C
	dc.b $4E,$AD,$07,$82,$2F,$2D,$F0,$D6,$2F,$0B,$4E,$AD,$07,$82,$42,$2E
	dc.b $FF,$F6,$60,$00,$03,$2E,$70,$1C,$B0,$07,$57,$C0,$4A,$00,$66,$16
	dc.b $72,$06,$B2,$07,$5F,$C1,$4A,$01,$67,$2E,$74,$13,$B4,$07,$5C,$C2
	dc.b $C2,$02,$80,$01,$67,$22,$4A,$2E,$FF,$F6,$5E,$C0,$4A,$00,$66,$0A
	dc.b $4A,$2E,$FF,$F7,$5E,$C1,$80,$01,$67,$32,$3F,$3C,$00,$14,$2F,$2E
	dc.b $00,$08,$4E,$BA,$FA,$C2,$60,$24,$70,$01,$B0,$2E,$FF,$F6,$5D,$C0
	dc.b $4A,$00,$66,$0C,$72,$01,$B2,$2E,$FF,$F7,$5D,$C1,$80,$01,$67,$0C
	dc.b $3F,$3C,$00,$87,$2F,$2E,$00,$08,$4E,$BA,$FA,$9C,$10,$07,$48,$80
	dc.b $59,$40,$6B,$00,$02,$BE,$0C,$40,$00,$18,$6E,$00,$02,$B6,$D0,$40
	dc.b $30,$3B,$00,$06,$4E,$FB,$00,$00,$00,$34,$00,$9C,$01,$1E,$01,$32
	dc.b $01,$56,$01,$7A,$01,$8A,$01,$9C,$01,$AC,$01,$C4,$01,$DC,$01,$F4
	dc.b $02,$0C,$02,$24,$02,$3A,$02,$4A,$02,$AC,$02,$AC,$02,$AC,$02,$AC
	dc.b $02,$AC,$02,$AC,$02,$AC,$02,$AC,$02,$5A,$70,$01,$B0,$2E,$FF,$F6
	dc.b $57,$C0,$4A,$00,$67,$2C,$72,$01,$B2,$2E,$FF,$F7,$57,$C1,$C0,$01
	dc.b $67,$20,$20,$2E,$FF,$FC,$22,$2E,$FF,$F8,$B3,$80,$4A,$80,$6D,$0C
	dc.b $3F,$3C,$00,$14,$2F,$2E,$00,$08,$4E,$BA,$FA,$1C,$42,$2E,$FF,$F6
	dc.b $60,$24,$70,$01,$B0,$2E,$FF,$F6,$57,$C0,$4A,$00,$66,$0C,$72,$01
	dc.b $B2,$2E,$FF,$F7,$57,$C1,$80,$01,$67,$08,$1D,$7C,$00,$01,$FF,$F6
	dc.b $60,$04,$42,$2E,$FF,$F6,$20,$2E,$FF,$FC,$D1,$AE,$FF,$F8,$60,$00
	dc.b $02,$12,$70,$01,$B0,$2E,$FF,$F6,$57,$C0,$4A,$00,$67,$46,$72,$01
	dc.b $B2,$2E,$FF,$F7,$57,$C1,$C0,$01,$67,$3A,$20,$2E,$FF,$FC,$22,$2E
	dc.b $FF,$F8,$B3,$80,$4A,$80,$6C,$26,$10,$2D,$F3,$A2,$0A,$00,$00,$01
	dc.b $4A,$00,$66,$0E,$4A,$AD,$F3,$D8,$57,$C1,$80,$01,$02,$40,$00,$01
	dc.b $67,$0C,$3F,$3C,$00,$14,$2F,$2E,$00,$08,$4E,$BA,$F9,$9A,$42,$2E
	dc.b $FF,$F6,$60,$24,$70,$01,$B0,$2E,$FF,$F6,$57,$C0,$4A,$00,$66,$0C
	dc.b $72,$01,$B2,$2E,$FF,$F7,$57,$C1,$80,$01,$67,$08,$1D,$7C,$00,$01
	dc.b $FF,$F6,$60,$04,$42,$2E,$FF,$F6,$20,$2E,$FF,$FC,$91,$AE,$FF,$F8
	dc.b $60,$00,$01,$90,$2F,$2E,$FF,$F8,$2F,$2E,$FF,$FC,$4E,$AD,$0A,$72
	dc.b $2D,$5F,$FF,$F8,$60,$00,$01,$7C,$4A,$AE,$FF,$FC,$66,$0A,$70,$00
	dc.b $2D,$40,$FF,$F8,$60,$00,$01,$6C,$2F,$2E,$FF,$F8,$2F,$2E,$FF,$FC
	dc.b $4E,$AD,$0A,$7A,$2D,$5F,$FF,$F8,$60,$00,$01,$58,$4A,$AE,$FF,$FC
	dc.b $66,$0A,$70,$00,$2D,$40,$FF,$F8,$60,$00,$01,$48,$2F,$2E,$FF,$F8
	dc.b $2F,$2E,$FF,$FC,$4E,$AD,$0A,$82,$2D,$5F,$FF,$F8,$60,$00,$01,$34
	dc.b $20,$2E,$FF,$FC,$80,$AE,$FF,$F8,$2D,$40,$FF,$F8,$60,$00,$01,$24
	dc.b $20,$2E,$FF,$FC,$22,$2E,$FF,$F8,$B3,$80,$2D,$40,$FF,$F8,$60,$00
	dc.b $01,$12,$20,$2E,$FF,$FC,$C0,$AE,$FF,$F8,$2D,$40,$FF,$F8,$60,$00
	dc.b $01,$02,$20,$2E,$FF,$F8,$B0,$AE,$FF,$FC,$57,$C0,$44,$00,$48,$80
	dc.b $48,$C0,$2D,$40,$FF,$F8,$60,$00,$00,$EA,$20,$2E,$FF,$F8,$B0,$AE
	dc.b $FF,$FC,$56,$C0,$44,$00,$48,$80,$48,$C0,$2D,$40,$FF,$F8,$60,$00
	dc.b $00,$D2,$20,$2E,$FF,$F8,$B0,$AE,$FF,$FC,$5D,$C0,$44,$00,$48,$80
	dc.b $48,$C0,$2D,$40,$FF,$F8,$60,$00,$00,$BA,$20,$2E,$FF,$F8,$B0,$AE
	dc.b $FF,$FC,$5E,$C0,$44,$00,$48,$80,$48,$C0,$2D,$40,$FF,$F8,$60,$00
	dc.b $00,$A2,$20,$2E,$FF,$F8,$B0,$AE,$FF,$FC,$5C,$C0,$44,$00,$48,$80
	dc.b $48,$C0,$2D,$40,$FF,$F8,$60,$00,$00,$8A,$20,$2E,$FF,$F8,$B0,$AE
	dc.b $FF,$FC,$5F,$C0,$44,$00,$48,$80,$48,$C0,$2D,$40,$FF,$F8,$60,$72
	dc.b $30,$2E,$FF,$FE,$22,$2E,$FF,$F8,$E0,$A9,$2D,$41,$FF,$F8,$60,$62
	dc.b $30,$2E,$FF,$FE,$22,$2E,$FF,$F8,$E1,$A9,$2D,$41,$FF,$F8,$60,$52
	dc.b $4A,$AE,$FF,$F8,$5D,$C0,$4A,$00,$66,$26,$0C,$AE,$00,$00,$00,$FF
	dc.b $FF,$F8,$5E,$C1,$80,$01,$66,$18,$4A,$AE,$FF,$FC,$5D,$C1,$80,$01
	dc.b $66,$0E,$0C,$AE,$00,$00,$00,$FF,$FF,$FC,$5E,$C1,$80,$01,$67,$0C
	dc.b $3F,$3C,$00,$89,$2F,$2E,$00,$08,$4E,$BA,$F7,$EC,$70,$10,$22,$2E
	dc.b $FF,$F8,$E1,$A9,$82,$AE,$FF,$FC,$2D,$41,$FF,$F8,$1D,$7C,$00,$03
	dc.b $FF,$F6,$10,$2D,$F3,$57,$48,$80,$E5,$40,$41,$ED,$F2,$62,$21,$AE
	dc.b $FF,$F8,$00,$00,$10,$2D,$F3,$57,$48,$80,$43,$ED,$F2,$24,$13,$AE
	dc.b $FF,$F6,$00,$00,$70,$00,$2B,$40,$F3,$CE,$4C,$DF,$18,$C0,$4E,$5E
	dc.b $20,$5F,$5C,$4F,$4E,$D0,$86,$4F,$55,$54,$5F,$4F,$50,$00,$00,$00
	dc.b $4E,$56,$FF,$FE,$10,$2E,$00,$0C,$48,$80,$41,$ED,$F3,$70,$12,$30
	dc.b $00,$00,$48,$81,$3D,$41,$FF,$FE,$10,$2D,$F3,$6F,$48,$80,$41,$ED
	dc.b $F3,$58,$12,$30,$00,$00,$48,$81,$43,$ED,$F3,$70,$10,$31,$10,$00
	dc.b $48,$80,$B0,$6E,$FF,$FE,$6D,$24,$10,$2D,$F3,$6F,$48,$80,$41,$ED
	dc.b $F3,$58,$1F,$30,$00,$00,$2F,$2E,$00,$08,$4E,$BA,$F9,$A0,$10,$2D
	dc.b $F3,$6F,$48,$80,$53,$40,$1B,$40,$F3,$6F,$60,$BC,$4E,$5E,$20,$5F
	dc.b $5C,$4F,$4E,$D0,$8F,$43,$48,$45,$43,$4B,$50,$52,$45,$43,$45,$44
	dc.b $45,$4E,$43,$45,$00,$00,$4E,$56,$FF,$F2,$48,$E7,$03,$18,$26,$6E
	dc.b $00,$14,$2C,$2E,$00,$0C,$20,$46,$42,$10,$42,$47,$2F,$0B,$48,$6E
	dc.b $FF,$F6,$2F,$2E,$00,$10,$48,$6E,$FF,$FC,$48,$6E,$FF,$FB,$4E,$BA
	dc.b $F5,$7C,$4A,$AE,$FF,$F6,$67,$7A,$70,$00,$30,$2E,$FF,$FC,$72,$00
	dc.b $32,$3C,$30,$00,$C0,$81,$4A,$80,$67,$68,$70,$00,$30,$2E,$FF,$FC
	dc.b $72,$00,$32,$3C,$14,$02,$C0,$81,$0C,$80,$00,$00,$14,$02,$67,$52
	dc.b $20,$46,$10,$BC,$00,$01,$70,$00,$30,$2E,$FF,$FC,$72,$00,$32,$3C
	dc.b $0A,$00,$C0,$81,$4A,$80,$67,$3A,$10,$2E,$FF,$FB,$67,$1C,$C0,$2D
	dc.b $F3,$A5,$67,$16,$20,$6E,$FF,$F6,$20,$68,$00,$04,$20,$68,$00,$04
	dc.b $22,$6E,$00,$10,$22,$A8,$00,$02,$60,$18,$08,$2E,$00,$00,$FF,$FD
	dc.b $66,$10,$20,$6E,$FF,$F6,$20,$68,$00,$04,$22,$6E,$00,$10,$22,$A8
	dc.b $00,$02,$4A,$AE,$FF,$F6,$66,$06,$7E,$10,$60,$00,$01,$5C,$08,$2E
	dc.b $00,$07,$FF,$FC,$67,$00,$00,$AC,$70,$00,$30,$2E,$FF,$FC,$C0,$BC
	dc.b $FF,$FF,$04,$AC,$4A,$80,$67,$1E,$70,$00,$30,$2E,$FF,$FC,$72,$00
	dc.b $32,$3C,$14,$02,$C0,$81,$0C,$80,$00,$00,$14,$02,$67,$00,$01,$2A
	dc.b $7E,$11,$60,$00,$01,$24,$08,$2E,$00,$04,$FF,$FD,$67,$00,$01,$1A
	dc.b $0C,$6D,$81,$00,$F3,$BA,$57,$C0,$4A,$00,$67,$60,$20,$6E,$00,$10
	dc.b $4A,$90,$56,$C1,$C0,$01,$67,$54,$42,$A7,$2F,$2D,$F0,$D6,$20,$6E
	dc.b $00,$10,$20,$50,$42,$40,$10,$10,$52,$40,$3F,$00,$4E,$AD,$07,$7A
	dc.b $28,$5F,$20,$0C,$66,$14,$3F,$3C,$00,$1C,$4E,$AD,$07,$CA,$20,$6E
	dc.b $00,$10,$70,$00,$20,$80,$60,$00,$01,$1E,$20,$6E,$00,$10,$2F,$10
	dc.b $2F,$0C,$4E,$BA,$C5,$90,$20,$6E,$00,$10,$20,$8C,$20,$46,$10,$BC
	dc.b $00,$10,$3B,$7C,$81,$01,$F3,$BA,$60,$00,$00,$AE,$7E,$15,$60,$00
	dc.b $00,$A8,$10,$2D,$EC,$A3,$67,$62,$08,$2E,$00,$02,$FF,$FC,$56,$C1
	dc.b $C0,$01,$67,$56,$70,$00,$30,$2E,$FF,$FC,$72,$00,$32,$3C,$30,$00
	dc.b $C0,$81,$4A,$80,$66,$16,$20,$6E,$FF,$F6,$2F,$28,$00,$04,$1F,$3C
	dc.b $00,$02,$2F,$2E,$00,$08,$4E,$BA,$F6,$EE,$60,$10,$2F,$2E,$FF,$F6
	dc.b $1F,$3C,$00,$02,$2F,$2E,$00,$08,$4E,$BA,$F6,$DC,$10,$2D,$F3,$6F
	dc.b $48,$80,$41,$ED,$F3,$58,$22,$6E,$00,$08,$13,$70,$00,$00,$FE,$EE
	dc.b $2F,$2E,$00,$08,$4E,$BA,$F5,$CA,$60,$3E,$10,$2E,$FF,$FB,$67,$36
	dc.b $C0,$2D,$F3,$A5,$67,$30,$42,$A7,$2F,$2D,$F3,$B0,$2F,$0B,$2F,$2E
	dc.b $00,$10,$48,$6E,$FF,$FC,$4E,$BA,$C8,$DC,$2D,$5F,$FF,$F6,$67,$12
	dc.b $3F,$3C,$00,$EA,$2F,$0B,$4E,$AD,$07,$C2,$42,$2E,$FF,$FB,$60,$00
	dc.b $FE,$22,$7E,$10,$60,$02,$7E,$10,$4A,$47,$6F,$12,$3F,$07,$2F,$0B
	dc.b $4E,$AD,$07,$C2,$20,$6E,$00,$10,$70,$00,$20,$80,$60,$38,$08,$2E
	dc.b $00,$06,$FF,$FC,$67,$0A,$20,$6E,$00,$10,$70,$00,$20,$80,$60,$26
	dc.b $08,$2E,$00,$01,$FF,$FD,$67,$1E,$08,$2E,$00,$00,$FF,$FD,$66,$06
	dc.b $2B,$6E,$FF,$F6,$F3,$CE,$08,$2E,$00,$02,$FF,$FC,$67,$08,$20,$6E
	dc.b $00,$10,$70,$00,$20,$80,$4C,$DF,$18,$C0,$4E,$5E,$20,$5F,$DE,$FC
	dc.b $00,$10,$4E,$D0,$89,$4C,$4F,$4F,$4B,$55,$50,$53,$59,$4D,$00,$00
	dc.b $4E,$56,$FF,$F6,$70,$00,$2B,$40,$F3,$CE,$20,$6E,$00,$08,$42,$10
	dc.b $42,$67,$2F,$2E,$00,$10,$2F,$2E,$00,$0C,$48,$6E,$FF,$F6,$48,$6E
	dc.b $FF,$FE,$48,$6E,$FF,$FA,$4E,$BA,$EE,$58,$10,$1F,$67,$1E,$08,$2E
	dc.b $00,$04,$FF,$FE,$56,$C0,$4A,$00,$66,$0A,$4A,$AE,$FF,$FA,$56,$C1
	dc.b $80,$01,$67,$08,$20,$6E,$00,$08,$10,$BC,$00,$01,$4E,$5E,$20,$5F
	dc.b $DE,$FC,$00,$0C,$4E,$D0,$8B,$4C,$4F,$4F,$4B,$55,$50,$46,$49,$45
	dc.b $4C,$44,$00,$00,$4E,$56,$FE,$E8,$48,$E7,$1F,$38,$70,$00,$2B,$40
	dc.b $F3,$CE,$1D,$6D,$EC,$E1,$FE,$F1,$1B,$7C,$00,$01,$EC,$E1,$1D,$7C
	dc.b $00,$01,$00,$14,$1D,$6D,$F3,$A0,$FE,$EF,$42,$6E,$FE,$F2,$10,$2D
	dc.b $EC,$E2,$66,$06,$80,$2D,$EC,$E3,$67,$42,$10,$2D,$F3,$57,$48,$80
	dc.b $3D,$40,$FE,$F4,$10,$2D,$F2,$23,$48,$80,$3D,$40,$FE,$F6,$10,$2D
	dc.b $F3,$6F,$48,$80,$3D,$40,$FE,$F8,$3D,$6E,$FE,$F2,$FE,$FA,$42,$67
	dc.b $4E,$BA,$C2,$3A,$10,$1F,$66,$0A,$3F,$3C,$00,$BB,$2F,$0E,$4E,$BA
	dc.b $F3,$D6,$42,$67,$2F,$0E,$4E,$BA,$F4,$F6,$60,$14,$1B,$7C,$00,$FF
	dc.b $F3,$57,$1B,$7C,$00,$FF,$F2,$23,$42,$2D,$F3,$6F,$42,$2D,$F3,$58
	dc.b $10,$2D,$FF,$FB,$48,$80,$67,$78,$53,$40,$67,$00,$02,$4C,$53,$40
	dc.b $67,$00,$02,$5A,$53,$40,$67,$00,$02,$B4,$53,$40,$67,$1C,$53,$40
	dc.b $67,$24,$53,$40,$67,$00,$02,$E8,$04,$40,$00,$0E,$67,$28,$53,$40
	dc.b $67,$24,$53,$40,$67,$30,$60,$00,$03,$24,$4E,$BA,$D4,$E6,$70,$00
	dc.b $2B,$40,$F3,$CE,$60,$BA,$1F,$3C,$00,$16,$2F,$0E,$4E,$BA,$F4,$90
	dc.b $4E,$BA,$D4,$D0,$60,$AA,$1F,$2D,$FF,$FB,$2F,$0E,$4E,$BA,$F4,$80
	dc.b $4E,$BA,$D4,$C0,$60,$9A,$52,$6E,$FE,$F2,$1B,$7C,$00,$01,$F3,$A0
	dc.b $1F,$3C,$00,$01,$2F,$0E,$4E,$BA,$F4,$66,$4E,$BA,$D4,$A6,$60,$80
	dc.b $70,$03,$B0,$6D,$FE,$F8,$66,$04,$4E,$BA,$E1,$04,$70,$14,$B0,$2D
	dc.b $FF,$FB,$66,$12,$1F,$2D,$FF,$FB,$2F,$0E,$4E,$BA,$F4,$42,$4E,$BA
	dc.b $D4,$82,$60,$00,$FF,$5C,$42,$40,$10,$2D,$FE,$FB,$72,$26,$B2,$40
	dc.b $57,$C0,$44,$00,$1D,$40,$FE,$F0,$48,$6D,$FE,$FA,$48,$6E,$FF,$00
	dc.b $4E,$BA,$C2,$B2,$4E,$BA,$D4,$5C,$70,$1D,$B0,$2D,$FF,$FB,$66,$14
	dc.b $48,$6E,$FF,$00,$48,$6D,$FE,$F0,$2F,$2E,$00,$0C,$4E,$BA,$FE,$32
	dc.b $60,$00,$01,$38,$10,$2E,$FE,$F0,$67,$00,$01,$1E,$2F,$00,$42,$67
	dc.b $48,$6E,$FF,$00,$2F,$2E,$00,$0C,$48,$6D,$FE,$F0,$48,$6E,$FE,$ED
	dc.b $4E,$AD,$05,$22,$12,$1F,$20,$1F,$C0,$01,$67,$00,$00,$FC,$20,$6E
	dc.b $00,$0C,$70,$06,$B0,$10,$57,$C0,$4A,$00,$66,$0A,$72,$05,$B2,$10
	dc.b $57,$C1,$80,$01,$67,$3C,$42,$A7,$2F,$2D,$F0,$D6,$20,$6D,$FE,$F0
	dc.b $42,$40,$10,$10,$52,$40,$3F,$00,$4E,$AD,$07,$7A,$2D,$5F,$FE,$E8
	dc.b $66,$0A,$3F,$3C,$00,$1C,$2F,$0E,$4E,$BA,$F2,$6C,$2F,$2D,$FE,$F0
	dc.b $2F,$2E,$FE,$E8,$4E,$BA,$C2,$1E,$2B,$6E,$FE,$E8,$FE,$F0,$60,$00
	dc.b $00,$BA,$20,$6E,$00,$0C,$70,$07,$B0,$10,$57,$C0,$4A,$00,$66,$0C
	dc.b $72,$08,$B2,$10,$57,$C1,$80,$01,$67,$00,$00,$A0,$70,$37,$B0,$2D
	dc.b $F3,$6F,$66,$0A,$3F,$3C,$00,$39,$2F,$0E,$4E,$BA,$F2,$2A,$10,$2D
	dc.b $F2,$23,$48,$80,$52,$40,$1B,$40,$F2,$23,$48,$80,$41,$ED,$F1,$EA
	dc.b $42,$30,$00,$00,$52,$6E,$FE,$F2,$1B,$7C,$00,$01,$F3,$A0,$22,$6E
	dc.b $00,$0C,$70,$07,$B0,$11,$66,$2E,$10,$2E,$FE,$ED,$48,$80,$48,$C0
	dc.b $2F,$00,$42,$67,$2F,$0E,$4E,$BA,$F3,$5E,$2F,$2D,$FE,$F0,$20,$6E
	dc.b $00,$0C,$1F,$10,$2F,$0E,$4E,$BA,$F3,$4E,$1F,$3C,$00,$1A,$2F,$0E
	dc.b $4E,$BA,$F2,$FC,$60,$1A,$2F,$2D,$FE,$F0,$20,$6E,$00,$0C,$1F,$10
	dc.b $2F,$0E,$4E,$BA,$F3,$32,$1F,$3C,$00,$18,$2F,$0E,$4E,$BA,$F2,$E0
	dc.b $4E,$BA,$D3,$20,$60,$00,$FD,$FA,$48,$6E,$FF,$00,$48,$6D,$FE,$F0
	dc.b $2F,$2E,$00,$0C,$2F,$0E,$4E,$BA,$FA,$7E,$2F,$2D,$FE,$F0,$20,$6E
	dc.b $00,$0C,$1F,$10,$2F,$0E,$4E,$BA,$F2,$FE,$10,$2D,$F3,$6F,$48,$80
	dc.b $41,$ED,$F3,$58,$1D,$70,$00,$00,$FE,$EE,$10,$2D,$EC,$E3,$67,$00
	dc.b $01,$40,$4A,$2E,$FE,$EE,$57,$C1,$C0,$01,$67,$00,$01,$34,$2F,$0E
	dc.b $4E,$BA,$F1,$DE,$60,$00,$01,$2A,$2F,$2D,$FE,$F0,$42,$67,$2F,$0E
	dc.b $4E,$BA,$F2,$C4,$4E,$BA,$D2,$BC,$60,$00,$01,$16,$0C,$6D,$81,$00
	dc.b $F3,$BA,$66,$4A,$42,$A7,$2F,$2D,$F0,$D6,$30,$2D,$FD,$EA,$52,$40
	dc.b $3F,$00,$4E,$AD,$07,$7A,$2D,$5F,$FE,$E8,$66,$0A,$3F,$3C,$00,$1C
	dc.b $2F,$0E,$4E,$BA,$F1,$22,$48,$6D,$FD,$EC,$2F,$2E,$FE,$E8,$4E,$BA
	dc.b $C0,$D4,$2F,$2E,$FE,$E8,$1F,$3C,$00,$10,$2F,$0E,$4E,$BA,$F2,$78
	dc.b $3B,$7C,$81,$01,$F3,$BA,$4E,$BA,$D2,$6A,$60,$00,$00,$C4,$3F,$3C
	dc.b $00,$0C,$2F,$0E,$4E,$BA,$F0,$F0,$60,$00,$FD,$36,$42,$A7,$2F,$2D
	dc.b $F0,$D6,$30,$2D,$FD,$EA,$52,$40,$3F,$00,$4E,$AD,$07,$7A,$2D,$5F
	dc.b $FE,$E8,$66,$0A,$3F,$3C,$00,$1C,$2F,$0E,$4E,$BA,$F0,$CA,$48,$6D
	dc.b $FD,$EC,$2F,$2E,$FE,$E8,$4E,$BA,$C0,$7C,$2F,$2E,$FE,$E8,$1F,$3C
	dc.b $00,$04,$2F,$0E,$4E,$BA,$F2,$20,$4E,$BA,$D2,$18,$60,$72,$10,$2D
	dc.b $F3,$A2,$67,$18,$4A,$AD,$F3,$D8,$66,$08,$20,$6E,$00,$0C,$42,$10
	dc.b $60,$24,$20,$6E,$00,$0C,$10,$BC,$00,$01,$60,$1A,$10,$2D,$F3,$A6
	dc.b $67,$0A,$20,$6E,$00,$0C,$10,$BC,$00,$01,$60,$0A,$3F,$3C,$00,$A0
	dc.b $2F,$0E,$4E,$BA,$F0,$72,$2F,$2D,$F4,$14,$20,$6E,$00,$0C,$1F,$10
	dc.b $2F,$0E,$4E,$BA,$F1,$D2,$4E,$BA,$D1,$CA,$60,$24,$70,$21,$B0,$2D
	dc.b $FF,$FB,$66,$0E,$3F,$3C,$00,$AB,$2F,$0E,$4E,$BA,$F0,$4A,$60,$00
	dc.b $FC,$90,$3F,$3C,$00,$0C,$2F,$0E,$4E,$BA,$F0,$3C,$60,$00,$FC,$82
	dc.b $4A,$2D,$FF,$FB,$57,$C0,$4A,$00,$67,$10,$72,$03,$B2,$6D,$FE,$F8
	dc.b $5C,$C1,$C0,$01,$67,$04,$4E,$BA,$DD,$F6,$10,$2D,$FF,$FB,$48,$80
	dc.b $59,$40,$6B,$00,$02,$50,$04,$40,$00,$0F,$6F,$18,$59,$40,$67,$00
	dc.b $00,$C6,$55,$40,$67,$00,$01,$86,$57,$40,$67,$24,$57,$40,$67,$7C
	dc.b $60,$00,$02,$32,$1F,$2D,$FF,$FB,$2F,$0E,$4E,$BA,$F8,$54,$1F,$2D
	dc.b $FF,$FB,$2F,$0E,$4E,$BA,$F1,$08,$4E,$BA,$D1,$48,$60,$00,$FC,$22
	dc.b $1F,$3C,$00,$17,$2F,$0E,$4E,$BA,$F8,$38,$10,$2D,$F3,$6F,$48,$80
	dc.b $41,$ED,$F3,$58,$1D,$70,$00,$00,$FE,$EE,$70,$18,$B0,$2E,$FE,$EE
	dc.b $56,$C0,$4A,$00,$67,$12,$72,$1A,$B2,$2E,$FE,$EE,$56,$C1,$C0,$01
	dc.b $67,$06,$2F,$0E,$4E,$BA,$F0,$1A,$10,$2D,$F2,$23,$48,$80,$41,$ED
	dc.b $F1,$EA,$12,$30,$00,$00,$48,$81,$52,$41,$10,$2D,$F2,$23,$48,$80
	dc.b $11,$81,$00,$00,$4E,$BA,$D0,$EC,$60,$00,$FB,$C6,$1F,$3C,$00,$1C
	dc.b $2F,$0E,$4E,$BA,$F7,$DC,$10,$2D,$F3,$6F,$48,$80,$41,$ED,$F3,$58
	dc.b $1D,$70,$00,$00,$FE,$EE,$70,$1A,$B0,$2E,$FE,$EE,$67,$06,$2F,$0E
	dc.b $4E,$BA,$EF,$CE,$1F,$3C,$00,$1C,$2F,$0E,$4E,$BA,$F0,$72,$4E,$BA
	dc.b $D0,$B2,$60,$00,$FB,$8C,$1F,$3C,$00,$03,$2F,$0E,$4E,$BA,$F7,$A2
	dc.b $10,$2D,$F3,$6F,$48,$80,$41,$ED,$F3,$58,$1D,$70,$00,$00,$FE,$EE
	dc.b $70,$18,$B0,$2E,$FE,$EE,$66,$4C,$10,$2D,$F3,$57,$48,$80,$3D,$40
	dc.b $FE,$FE,$10,$2D,$F2,$23,$48,$80,$41,$ED,$F1,$EA,$12,$30,$00,$00
	dc.b $48,$81,$52,$41,$3D,$41,$FE,$FC,$42,$67,$1F,$2E,$FE,$FD,$2F,$2E
	dc.b $00,$08,$4E,$AD,$05,$42,$10,$1F,$66,$0C,$20,$6E,$00,$08,$3F,$10
	dc.b $2F,$0E,$4E,$BA,$EE,$E2,$10,$2D,$F2,$23,$48,$80,$53,$40,$1B,$40
	dc.b $F2,$23,$60,$12,$70,$01,$B0,$2E,$FE,$EE,$67,$0A,$3F,$3C,$00,$0D
	dc.b $2F,$0E,$4E,$BA,$EE,$C2,$53,$6E,$FE,$F2,$4A,$6E,$FE,$F2,$66,$06
	dc.b $1B,$6E,$FE,$EF,$F3,$A0,$10,$2D,$F3,$6F,$48,$80,$53,$40,$1B,$40
	dc.b $F3,$6F,$48,$80,$41,$ED,$F3,$58,$1D,$70,$00,$00,$FE,$EE,$10,$2D
	dc.b $EC,$E3,$67,$10,$4A,$2E,$FE,$EE,$57,$C1,$C0,$01,$67,$06,$2F,$0E
	dc.b $4E,$BA,$EE,$FE,$4E,$BA,$CF,$EC,$60,$00,$FE,$46,$1F,$3C,$00,$1B
	dc.b $2F,$0E,$4E,$BA,$F6,$DC,$10,$2D,$F3,$6F,$48,$80,$41,$ED,$F3,$58
	dc.b $1D,$70,$00,$00,$FE,$EE,$70,$1A,$B0,$2E,$FE,$EE,$67,$06,$2F,$0E
	dc.b $4E,$BA,$EE,$CE,$10,$2D,$F3,$57,$48,$80,$3D,$40,$FE,$FE,$10,$2D
	dc.b $F2,$23,$48,$80,$41,$ED,$F1,$EA,$12,$30,$00,$00,$48,$81,$52,$41
	dc.b $3D,$41,$FE,$FC,$42,$67,$1F,$2E,$FE,$FD,$2F,$2E,$00,$08,$4E,$AD
	dc.b $05,$4A,$10,$1F,$66,$0C,$20,$6E,$00,$08,$3F,$10,$2F,$0E,$4E,$BA
	dc.b $EE,$16,$10,$2D,$F2,$23,$48,$80,$53,$40,$1B,$40,$F2,$23,$53,$6E
	dc.b $FE,$F2,$4A,$6E,$FE,$F2,$66,$06,$1B,$6E,$FE,$EF,$F3,$A0,$10,$2D
	dc.b $F3,$6F,$48,$80,$53,$40,$1B,$40,$F3,$6F,$48,$80,$41,$ED,$F3,$58
	dc.b $1D,$70,$00,$00,$FE,$EE,$10,$2D,$EC,$E3,$67,$10,$4A,$2E,$FE,$EE
	dc.b $57,$C1,$C0,$01,$67,$06,$2F,$0E,$4E,$BA,$EE,$46,$4E,$BA,$CF,$34
	dc.b $60,$00,$FD,$8E,$1F,$3C,$00,$02,$2F,$0E,$4E,$BA,$F6,$24,$70,$21
	dc.b $B0,$2D,$FF,$FB,$66,$0A,$3F,$3C,$00,$AB,$2F,$0E,$4E,$BA,$ED,$A8
	dc.b $10,$2D,$F3,$6F,$48,$80,$41,$ED,$F3,$58,$1D,$70,$00,$00,$FE,$EE
	dc.b $2F,$0E,$4E,$BA,$EE,$0C,$60,$00,$FD,$58,$4F,$EE,$FE,$C8,$4C,$DF
	dc.b $1C,$F8,$4E,$5E,$20,$5F,$DE,$FC,$00,$0C,$4E,$D0,$88,$45,$56,$41
	dc.b $4C,$45,$58,$50,$52,$00,$00,$00,$4E,$56,$00,$00,$2F,$0C,$28,$6E
	dc.b $00,$08,$1B,$6C,$FD,$FB,$F3,$A0,$20,$6C,$00,$08,$30,$AE,$00,$0C
	dc.b $20,$6E,$00,$08,$42,$28,$00,$14,$20,$6E,$00,$08,$2C,$48,$4E,$FA
	dc.b $0E,$8C,$00,$00,$28,$5F,$4E,$5E,$20,$5F,$5C,$4F,$4E,$D0,$89,$45
	dc.b $58,$50,$52,$45,$52,$52,$4F,$52,$00,$00,$4E,$56,$00,$00,$2F,$0C
	dc.b $28,$6E,$00,$08,$20,$6C,$00,$10,$10,$AD,$F2,$24,$10,$2C,$FD,$FA
	dc.b $67,$16,$20,$6C,$00,$0C,$20,$AD,$F2,$62,$3F,$2C,$FD,$72,$20,$6C
	dc.b $00,$0C,$2F,$10,$4E,$BA,$CA,$A8,$1B,$6C,$FD,$FB,$F3,$A0,$20,$6E
	dc.b $00,$08,$2C,$48,$4E,$FA,$0E,$36,$00,$00,$28,$5F,$4E,$5E,$2E,$9F
	dc.b $4E,$75,$8B,$52,$45,$54,$55,$52,$4E,$56,$41,$4C,$55,$45,$00,$00
	dc.b $4E,$56,$00,$00,$70,$14,$B0,$2D,$F3,$6F,$66,$0C,$3F,$3C,$00,$0B
	dc.b $2F,$2E,$00,$08,$4E,$BA,$FF,$52,$10,$2D,$F3,$6F,$48,$80,$52,$40
	dc.b $1B,$40,$F3,$6F,$48,$80,$41,$ED,$F3,$58,$11,$AE,$00,$0C,$00,$00
	dc.b $4E,$5E,$20,$5F,$5C,$4F,$4E,$D0,$87,$53,$54,$41,$43,$4B,$4F,$50
	dc.b $00,$00,$4E,$56,$00,$00,$70,$3C,$B0,$2D,$F3,$57,$66,$0C,$3F,$3C
	dc.b $00,$0A,$2F,$2E,$00,$08,$4E,$BA,$FF,$10,$10,$2D,$F3,$57,$48,$80
	dc.b $52,$40,$1B,$40,$F3,$57,$48,$80,$41,$ED,$F2,$24,$11,$AE,$00,$12
	dc.b $00,$00,$22,$6E,$00,$08,$10,$29,$FD,$FA,$67,$28,$10,$2D,$F3,$57
	dc.b $48,$80,$20,$49,$D0,$40,$41,$E8,$FD,$72,$31,$AE,$00,$10,$00,$00
	dc.b $10,$2D,$F3,$57,$48,$80,$E5,$40,$41,$ED,$F2,$62,$21,$AE,$00,$0C
	dc.b $00,$00,$60,$0C,$3F,$2E,$00,$10,$2F,$2E,$00,$0C,$4E,$BA,$C9,$D0
	dc.b $4E,$5E,$20,$5F,$DE,$FC,$00,$0C,$4E,$D0,$88,$4F,$55,$54,$5F,$4F
	dc.b $50,$4E,$44,$00,$00,$00,$4E,$56,$FF,$EC,$48,$E7,$0F,$08,$28,$6E
	dc.b $00,$08,$10,$2D,$F3,$57,$48,$80,$E5,$40,$41,$ED,$F2,$62,$2C,$30
	dc.b $00,$00,$10,$2D,$F3,$57,$48,$80,$43,$ED,$F2,$24,$18,$31,$00,$00
	dc.b $70,$15,$B0,$2E,$00,$0C,$66,$46,$4A,$04,$67,$0C,$3F,$3C,$00,$14
	dc.b $2F,$2E,$00,$08,$4E,$BA,$FE,$62,$42,$05,$10,$2C,$FD,$FA,$67,$00
	dc.b $03,$F0,$20,$06,$72,$FF,$B3,$80,$12,$2D,$F3,$57,$48,$81,$E5,$41
	dc.b $41,$ED,$F2,$62,$21,$80,$10,$00,$10,$2D,$F3,$57,$48,$80,$D0,$40
	dc.b $43,$EC,$FD,$72,$33,$BC,$00,$06,$00,$00,$60,$00,$03,$C4,$70,$14
	dc.b $B0,$2E,$00,$0C,$66,$46,$4A,$04,$67,$0C,$3F,$3C,$00,$14,$2F,$2E
	dc.b $00,$08,$4E,$BA,$FE,$14,$42,$05,$10,$2C,$FD,$FA,$67,$00,$03,$A2
	dc.b $20,$06,$72,$01,$B3,$80,$12,$2D,$F3,$57,$48,$81,$E5,$41,$41,$ED
	dc.b $F2,$62,$21,$80,$10,$00,$10,$2D,$F3,$57,$48,$80,$D0,$40,$43,$EC
	dc.b $FD,$72,$33,$BC,$00,$06,$00,$00,$60,$00,$03,$76,$70,$16,$B0,$2E
	dc.b $00,$0C,$66,$00,$00,$94,$10,$2C,$FD,$FA,$67,$36,$72,$02,$B2,$04
	dc.b $56,$C1,$C0,$01,$67,$2C,$20,$06,$44,$80,$12,$2D,$F3,$57,$48,$81
	dc.b $E5,$41,$41,$ED,$F2,$62,$21,$80,$10,$00,$10,$2D,$F3,$57,$48,$80
	dc.b $D0,$40,$43,$EC,$FD,$72,$33,$BC,$00,$06,$00,$00,$1A,$04,$60,$00
	dc.b $03,$30,$10,$2C,$FD,$FA,$67,$46,$42,$6E,$FF,$F2,$10,$2D,$F3,$57
	dc.b $48,$80,$3D,$40,$FF,$F0,$3D,$6E,$FF,$F2,$FF,$FE,$60,$26,$30,$2E
	dc.b $FF,$FE,$D0,$40,$41,$EC,$FD,$72,$3F,$30,$00,$00,$30,$2E,$FF,$FE
	dc.b $E5,$40,$41,$ED,$F2,$62,$2F,$30,$00,$00,$4E,$BA,$C8,$72,$52,$6E
	dc.b $FF,$FE,$69,$0A,$30,$2E,$FF,$FE,$B0,$6E,$FF,$F0,$6F,$D0,$1A,$04
	dc.b $42,$2C,$FD,$FA,$60,$00,$02,$DA,$10,$2D,$F3,$57,$48,$80,$53,$40
	dc.b $1B,$40,$F3,$57,$48,$80,$E5,$40,$41,$ED,$F2,$62,$2E,$30,$00,$00
	dc.b $10,$2D,$F3,$57,$48,$80,$43,$ED,$F2,$24,$1A,$31,$00,$00,$70,$02
	dc.b $B0,$05,$57,$C0,$4A,$00,$66,$0C,$72,$02,$B2,$04,$57,$C1,$80,$01
	dc.b $67,$00,$00,$C0,$70,$05,$B0,$2E,$00,$0C,$66,$34,$4A,$05,$56,$C0
	dc.b $4A,$00,$67,$28,$4A,$04,$56,$C1,$C0,$01,$67,$20,$42,$05,$70,$02
	dc.b $B0,$6D,$F3,$9C,$66,$0A,$20,$6C,$00,$0C,$70,$01,$20,$80,$60,$3E
	dc.b $20,$6C,$00,$0C,$20,$BC,$00,$00,$80,$00,$60,$32,$7A,$02,$60,$2E
	dc.b $70,$04,$B0,$2E,$00,$0C,$66,$1A,$4A,$05,$66,$04,$7A,$02,$60,$1E
	dc.b $4A,$04,$67,$1A,$3F,$3C,$00,$14,$2F,$2E,$00,$08,$4E,$BA,$FC,$AA
	dc.b $60,$0C,$3F,$3C,$00,$14,$2F,$2E,$00,$08,$4E,$BA,$FC,$9C,$10,$2C
	dc.b $FD,$FA,$67,$48,$42,$6E,$FF,$EE,$10,$2D,$F3,$57,$48,$80,$52,$40
	dc.b $3D,$40,$FF,$EC,$3D,$6E,$FF,$EE,$FF,$FE,$60,$26,$30,$2E,$FF,$FE
	dc.b $D0,$40,$41,$EC,$FD,$72,$3F,$30,$00,$00,$30,$2E,$FF,$FE,$E5,$40
	dc.b $41,$ED,$F2,$62,$2F,$30,$00,$00,$4E,$BA,$C7,$74,$52,$6E,$FF,$FE
	dc.b $69,$0A,$30,$2E,$FF,$FE,$B0,$6E,$FF,$EC,$6F,$D0,$42,$2C,$FD,$FA
	dc.b $60,$34,$70,$06,$B0,$2E,$00,$0C,$5F,$C0,$4A,$00,$67,$28,$72,$13
	dc.b $B2,$2E,$00,$0C,$5C,$C1,$C0,$01,$67,$1C,$4A,$05,$56,$C0,$4A,$00
	dc.b $66,$08,$4A,$04,$56,$C1,$80,$01,$67,$0C,$3F,$3C,$00,$14,$2F,$2E
	dc.b $00,$08,$4E,$BA,$FC,$14,$10,$2C,$FD,$FA,$67,$00,$01,$A4,$10,$2E
	dc.b $00,$0C,$48,$80,$59,$40,$6B,$00,$01,$76,$0C,$40,$00,$0F,$6E,$00
	dc.b $01,$6E,$D0,$40,$30,$3B,$00,$06,$4E,$FB,$00,$00,$00,$22,$00,$70
	dc.b $00,$BE,$00,$CC,$00,$E4,$00,$F8,$00,$FC,$01,$02,$01,$06,$01,$14
	dc.b $01,$22,$01,$30,$01,$3E,$01,$4C,$01,$5A,$01,$60,$70,$01,$B0,$05
	dc.b $57,$C0,$4A,$00,$67,$24,$72,$01,$B2,$04,$57,$C1,$C0,$01,$67,$1A
	dc.b $20,$07,$22,$06,$B3,$80,$4A,$80,$6D,$0C,$3F,$3C,$00,$14,$2F,$2E
	dc.b $00,$08,$4E,$BA,$FB,$A4,$42,$05,$60,$1A,$70,$01,$B0,$05,$57,$C0
	dc.b $4A,$00,$66,$0A,$72,$01,$B2,$04,$57,$C1,$80,$01,$67,$04,$7A,$01
	dc.b $60,$02,$42,$05,$DE,$86,$60,$00,$00,$F6,$70,$01,$B0,$05,$57,$C0
	dc.b $4A,$00,$67,$24,$72,$01,$B2,$04,$57,$C1,$C0,$01,$67,$1A,$20,$07
	dc.b $22,$06,$B3,$80,$4A,$80,$6C,$0C,$3F,$3C,$00,$14,$2F,$2E,$00,$08
	dc.b $4E,$BA,$FB,$56,$42,$05,$60,$1A,$70,$01,$B0,$05,$57,$C0,$4A,$00
	dc.b $66,$0A,$72,$01,$B2,$04,$57,$C1,$80,$01,$67,$04,$7A,$01,$60,$02
	dc.b $42,$05,$9E,$86,$60,$00,$00,$A8,$2F,$07,$2F,$06,$4E,$AD,$0A,$72
	dc.b $2E,$1F,$60,$00,$00,$9A,$4A,$86,$66,$06,$7E,$00,$60,$00,$00,$90
	dc.b $2F,$07,$2F,$06,$4E,$AD,$0A,$7A,$2E,$1F,$60,$00,$00,$82,$4A,$86
	dc.b $66,$04,$7E,$00,$60,$78,$2F,$07,$2F,$06,$4E,$AD,$0A,$82,$2E,$1F
	dc.b $60,$6C,$8E,$86,$60,$68,$20,$06,$B1,$87,$60,$62,$CE,$86,$60,$5E
	dc.b $BC,$87,$57,$C0,$44,$00,$48,$80,$48,$C0,$2E,$00,$60,$50,$BC,$87
	dc.b $56,$C0,$44,$00,$48,$80,$48,$C0,$2E,$00,$60,$42,$BC,$87,$5E,$C0
	dc.b $44,$00,$48,$80,$48,$C0,$2E,$00,$60,$34,$BC,$87,$5D,$C0,$44,$00
	dc.b $48,$80,$48,$C0,$2E,$00,$60,$26,$BC,$87,$5F,$C0,$44,$00,$48,$80
	dc.b $48,$C0,$2E,$00,$60,$18,$BC,$87,$5C,$C0,$44,$00,$48,$80,$48,$C0
	dc.b $2E,$00,$60,$0A,$30,$06,$E0,$AF,$60,$04,$30,$06,$E1,$AF,$10,$2D
	dc.b $F3,$57,$48,$80,$E5,$40,$41,$ED,$F2,$62,$21,$87,$00,$00,$10,$2D
	dc.b $F3,$57,$48,$80,$D0,$40,$43,$EC,$FD,$72,$33,$BC,$00,$06,$00,$00
	dc.b $10,$2C,$FD,$FA,$66,$10,$10,$2E,$00,$0C,$48,$80,$D0,$7C,$00,$1A
	dc.b $3F,$00,$4E,$BA,$C7,$CC,$10,$2D,$F3,$57,$48,$80,$41,$ED,$F2,$24
	dc.b $11,$85,$00,$00,$4C,$DF,$10,$F0,$4E,$5E,$20,$5F,$5C,$4F,$4E,$D0
	dc.b $86,$4F,$55,$54,$5F,$4F,$50,$00,$00,$00,$4E,$56,$FF,$FE,$10,$2E
	dc.b $00,$0C,$48,$80,$41,$ED,$F3,$70,$12,$30,$00,$00,$48,$81,$3D,$41
	dc.b $FF,$FE,$10,$2D,$F3,$6F,$48,$80,$41,$ED,$F3,$58,$12,$30,$00,$00
	dc.b $48,$81,$43,$ED,$F3,$70,$10,$31,$10,$00,$48,$80,$B0,$6E,$FF,$FE
	dc.b $6D,$24,$10,$2D,$F3,$6F,$48,$80,$41,$ED,$F3,$58,$1F,$30,$00,$00
	dc.b $2F,$2E,$00,$08,$4E,$BA,$FB,$40,$10,$2D,$F3,$6F,$48,$80,$53,$40
	dc.b $1B,$40,$F3,$6F,$60,$BC,$4E,$5E,$20,$5F,$5C,$4F,$4E,$D0,$8F,$43
	dc.b $48,$45,$43,$4B,$50,$52,$45,$43,$45,$44,$45,$4E,$43,$45,$00,$00
	dc.b $4E,$56,$FF,$E4,$48,$E7,$07,$18,$26,$6E,$00,$10,$28,$6E,$00,$1A
	dc.b $42,$13,$42,$67,$2F,$0C,$4E,$BA,$B9,$14,$3E,$1F,$42,$6E,$FF,$FC
	dc.b $42,$46,$20,$6E,$00,$14,$70,$00,$20,$80,$70,$00,$2D,$40,$FF,$E8
	dc.b $42,$05,$10,$2E,$00,$18,$67,$40,$4A,$AD,$EC,$A8,$67,$3A,$2F,$0C
	dc.b $3F,$07,$2F,$2E,$00,$14,$48,$6E,$FF,$F6,$48,$6E,$FF,$FC,$2F,$2E
	dc.b $00,$0C,$48,$6E,$FF,$E8,$4E,$BA,$DE,$C6,$20,$6E,$00,$14,$4A,$90
	dc.b $67,$16,$4A,$AE,$FF,$E8,$67,$10,$16,$BC,$00,$0A,$20,$6E,$00,$14
	dc.b $20,$AE,$FF,$E8,$60,$00,$03,$04,$20,$6E,$00,$14,$4A,$90,$66,$00
	dc.b $00,$8E,$10,$2D,$F3,$A2,$67,$2C,$2F,$08,$42,$A7,$2F,$2D,$F3,$AC
	dc.b $22,$6D,$F3,$EA,$48,$69,$00,$0C,$2F,$0C,$48,$6E,$FF,$F6,$48,$6E
	dc.b $FF,$FC,$2F,$2E,$00,$0C,$3F,$07,$4E,$BA,$BB,$BE,$20,$1F,$20,$5F
	dc.b $20,$80,$60,$5A,$10,$2D,$F3,$A4,$67,$54,$20,$6E,$00,$14,$2F,$08
	dc.b $42,$A7,$2F,$2D,$F3,$A8,$2F,$0C,$48,$6E,$FF,$F6,$48,$6E,$FF,$FC
	dc.b $3F,$07,$4E,$BA,$B9,$F8,$20,$1F,$20,$5F,$20,$80,$20,$6E,$00,$14
	dc.b $4A,$90,$66,$2A,$2F,$08,$42,$A7,$2F,$2D,$F3,$B0,$22,$6D,$F3,$EE
	dc.b $48,$69,$00,$0C,$2F,$0C,$48,$6E,$FF,$F6,$48,$6E,$FF,$FC,$2F,$2E
	dc.b $00,$0C,$3F,$07,$4E,$BA,$BB,$62,$20,$1F,$20,$5F,$20,$80,$20,$6E
	dc.b $00,$14,$4A,$90,$67,$0A,$20,$6E,$00,$0C,$2D,$50,$FF,$F6,$60,$22
	dc.b $20,$6E,$00,$14,$2F,$08,$42,$A7,$2F,$2D,$F3,$AC,$2F,$0C,$48,$6E
	dc.b $FF,$F6,$48,$6E,$FF,$FC,$3F,$07,$4E,$BA,$B9,$92,$20,$1F,$20,$5F
	dc.b $20,$80,$20,$6E,$00,$14,$4A,$90,$57,$C0,$4A,$00,$67,$4A,$C0,$2D
	dc.b $F3,$A5,$67,$44,$2F,$08,$42,$A7,$2F,$2D,$F3,$B0,$2F,$0C,$48,$6E
	dc.b $FF,$F6,$48,$6E,$FF,$FC,$3F,$07,$4E,$BA,$B9,$62,$20,$1F,$20,$5F
	dc.b $20,$80,$20,$6E,$00,$14,$4A,$90,$67,$1E,$70,$00,$30,$2E,$FF,$FC
	dc.b $72,$00,$32,$3C,$34,$00,$C0,$81,$4A,$80,$67,$0A,$70,$00,$20,$80
	dc.b $42,$6E,$FF,$FC,$60,$02,$7A,$01,$20,$6E,$00,$14,$4A,$90,$66,$00
	dc.b $00,$B4,$16,$BC,$00,$02,$10,$2D,$F3,$A5,$67,$22,$20,$6E,$00,$14
	dc.b $2F,$08,$42,$A7,$2F,$2D,$F3,$AC,$2F,$0C,$42,$A7,$3F,$2E,$FF,$FC
	dc.b $3F,$07,$4E,$BA,$B7,$9C,$20,$1F,$20,$5F,$20,$80,$60,$68,$3D,$7C
	dc.b $00,$01,$FF,$FC,$10,$2D,$F3,$A2,$67,$2A,$20,$6E,$00,$14,$2F,$08
	dc.b $42,$A7,$2F,$2D,$F3,$AC,$2F,$0C,$2F,$2D,$F3,$EA,$3F,$2E,$FF,$FC
	dc.b $42,$A7,$48,$6E,$FF,$F4,$3F,$07,$4E,$BA,$B9,$60,$20,$1F,$20,$5F
	dc.b $20,$80,$60,$32,$10,$2D,$F3,$A4,$67,$2A,$20,$6E,$00,$14,$2F,$08
	dc.b $42,$A7,$2F,$2D,$F3,$B0,$2F,$0C,$2F,$2D,$F3,$EE,$3F,$2E,$FF,$FC
	dc.b $42,$A7,$48,$6E,$FF,$F4,$3F,$07,$4E,$BA,$B9,$30,$20,$1F,$20,$5F
	dc.b $20,$80,$60,$02,$7C,$10,$4A,$46,$57,$C0,$4A,$00,$67,$00,$00,$9C
	dc.b $20,$6E,$00,$14,$4A,$90,$57,$C1,$C0,$01,$67,$00,$00,$8E,$7C,$16
	dc.b $60,$00,$00,$88,$08,$2E,$00,$07,$FF,$FC,$56,$C0,$4A,$00,$67,$76
	dc.b $08,$2E,$00,$04,$FF,$FC,$57,$C1,$C0,$01,$67,$6A,$10,$2D,$F3,$A5
	dc.b $67,$4A,$08,$2E,$00,$05,$FF,$FC,$67,$38,$16,$BC,$00,$01,$70,$00
	dc.b $30,$2E,$FF,$FC,$72,$00,$32,$3C,$0A,$00,$C0,$81,$4A,$80,$67,$18
	dc.b $20,$6E,$00,$14,$20,$50,$20,$68,$00,$04,$20,$68,$00,$04,$22,$6E
	dc.b $00,$14,$22,$A8,$00,$02,$60,$32,$20,$6E,$00,$14,$20,$AE,$FF,$F6
	dc.b $60,$28,$20,$6E,$00,$14,$20,$AE,$FF,$F6,$60,$1E,$08,$2E,$00,$05
	dc.b $FF,$FC,$67,$06,$16,$BC,$00,$02,$60,$10,$20,$6E,$00,$14,$20,$AE
	dc.b $FF,$F6,$7A,$01,$60,$04,$16,$BC,$00,$02,$4A,$46,$66,$12,$70,$00
	dc.b $30,$2E,$FF,$FC,$C0,$BC,$FF,$FF,$00,$AC,$4A,$80,$67,$02,$7C,$15
	dc.b $4A,$46,$67,$14,$3F,$06,$2F,$0C,$4E,$AD,$07,$C2,$42,$13,$20,$6E
	dc.b $00,$14,$70,$00,$20,$80,$60,$72,$08,$2E,$00,$05,$FF,$FC,$67,$0C
	dc.b $22,$6E,$00,$08,$20,$69,$00,$08,$42,$50,$60,$5E,$10,$05,$0A,$00
	dc.b $00,$01,$4A,$00,$67,$2E,$12,$2D,$F3,$A5,$67,$08,$74,$02,$B4,$13
	dc.b $57,$C2,$C2,$02,$4A,$01,$67,$0A,$08,$2E,$00,$04,$FF,$FC,$56,$C2
	dc.b $C2,$02,$0A,$01,$00,$01,$C0,$01,$67,$0A,$22,$6E,$00,$08,$20,$69
	dc.b $00,$08,$42,$50,$08,$2E,$00,$02,$FF,$FC,$67,$1E,$70,$00,$30,$2E
	dc.b $FF,$FC,$72,$00,$32,$3C,$30,$00,$C0,$81,$4A,$80,$66,$0C,$16,$BC
	dc.b $00,$02,$20,$6E,$00,$14,$20,$AE,$FF,$F6,$4C,$DF,$18,$E0,$4E,$5E
	dc.b $20,$5F,$DE,$FC,$00,$16,$4E,$D0,$89,$4C,$4F,$4F,$4B,$55,$50,$53
	dc.b $59,$4D,$00,$00,$4E,$56,$FE,$F6,$20,$6E,$00,$10,$42,$10,$2F,$2E
	dc.b $00,$18,$48,$6E,$FE,$F6,$4E,$BA,$B3,$3C,$42,$67,$48,$6E,$FE,$F6
	dc.b $2F,$2E,$00,$14,$48,$6E,$FF,$F6,$48,$6E,$FF,$FE,$48,$6E,$FF,$FA
	dc.b $4E,$BA,$DD,$3E,$10,$1F,$67,$46,$4A,$AE,$FF,$FA,$67,$1C,$20,$6E
	dc.b $00,$14,$22,$6E,$00,$0C,$22,$90,$20,$6E,$00,$14,$20,$AE,$FF,$FA
	dc.b $20,$6E,$00,$10,$10,$BC,$00,$0A,$60,$24,$08,$2E,$00,$04,$FF,$FE
	dc.b $67,$12,$20,$6E,$00,$14,$20,$AE,$FF,$F6,$20,$6E,$00,$10,$10,$BC
	dc.b $00,$02,$60,$0A,$22,$6E,$00,$08,$20,$69,$00,$08,$42,$50,$4E,$5E
	dc.b $20,$5F,$DE,$FC,$00,$14,$4E,$D0,$8B,$4C,$4F,$4F,$4B,$55,$50,$46
	dc.b $49,$45,$4C,$44,$00,$00,$4E,$56,$FC,$72,$48,$E7,$1F,$38,$10,$2D
	dc.b $F3,$A5,$48,$80,$20,$6E,$00,$08,$30,$80,$1D,$7C,$00,$01,$00,$14
	dc.b $1D,$6D,$F3,$A0,$FD,$FB,$1D,$7C,$00,$01,$FD,$FA,$42,$6E,$FD,$F6
	dc.b $1B,$7C,$00,$FF,$F3,$57,$10,$2D,$FF,$FB,$48,$80,$67,$6C,$53,$40
	dc.b $67,$00,$01,$62,$55,$40,$67,$00,$01,$74,$53,$40,$67,$1C,$53,$40
	dc.b $67,$1E,$53,$40,$67,$00,$01,$90,$04,$40,$00,$0E,$67,$22,$53,$40
	dc.b $67,$1E,$53,$40,$67,$2A,$60,$00,$02,$8A,$4E,$BA,$C4,$06,$60,$C6
	dc.b $1F,$3C,$00,$16,$2F,$0E,$4E,$BA,$F5,$B8,$4E,$BA,$C3,$F6,$60,$B6
	dc.b $1F,$2D,$FF,$FB,$2F,$0E,$4E,$BA,$F5,$A8,$4E,$BA,$C3,$E6,$60,$A6
	dc.b $52,$6E,$FD,$F6,$1B,$7C,$00,$01,$F3,$A0,$1F,$3C,$00,$01,$2F,$0E
	dc.b $4E,$BA,$F5,$8E,$4E,$BA,$C3,$CC,$60,$8C,$70,$03,$B0,$6D,$FE,$F8
	dc.b $66,$04,$4E,$BA,$D0,$2A,$70,$14,$B0,$2D,$FF,$FB,$66,$12,$1F,$2D
	dc.b $FF,$FB,$2F,$0E,$4E,$BA,$F5,$6A,$4E,$BA,$C3,$A8,$60,$00,$FF,$68
	dc.b $48,$6D,$FE,$FA,$48,$6E,$FF,$00,$4E,$BA,$B1,$EA,$4E,$BA,$C3,$94
	dc.b $70,$1D,$B0,$2D,$FF,$FB,$66,$18,$48,$6E,$FF,$00,$48,$6E,$FD,$FC
	dc.b $2F,$2E,$00,$10,$48,$6E,$FD,$F2,$2F,$0E,$4E,$BA,$FE,$78,$60,$1A
	dc.b $48,$6E,$FF,$00,$1F,$3C,$00,$01,$48,$6E,$FD,$FC,$2F,$2E,$00,$10
	dc.b $48,$6E,$FD,$F2,$2F,$0E,$4E,$BA,$FA,$C8,$20,$6E,$00,$10,$70,$02
	dc.b $B0,$10,$66,$14,$1F,$10,$3F,$3C,$00,$05,$2F,$2E,$FD,$FC,$2F,$0E
	dc.b $4E,$BA,$F5,$40,$60,$00,$01,$CA,$20,$6E,$00,$10,$70,$10,$B0,$10
	dc.b $66,$14,$1F,$10,$3F,$3C,$00,$07,$2F,$2E,$FD,$FC,$2F,$0E,$4E,$BA
	dc.b $F5,$22,$60,$00,$01,$AC,$20,$6E,$00,$10,$70,$0A,$B0,$10,$67,$14
	dc.b $1F,$10,$3F,$3C,$00,$06,$2F,$2E,$FD,$FC,$2F,$0E,$4E,$BA,$F5,$04
	dc.b $60,$00,$01,$8E,$1F,$3C,$00,$02,$3F,$3C,$00,$05,$2F,$2E,$FD,$FC
	dc.b $2F,$0E,$4E,$BA,$F4,$EE,$2F,$3C,$00,$06,$00,$00,$2F,$2E,$FD,$F2
	dc.b $2F,$0E,$4E,$BA,$F4,$DE,$1F,$3C,$00,$04,$2F,$0E,$4E,$BA,$F5,$58
	dc.b $60,$00,$01,$5E,$2F,$3C,$00,$06,$00,$00,$2F,$2D,$FE,$F0,$2F,$0E
	dc.b $4E,$BA,$F4,$C0,$4E,$BA,$C2,$BC,$60,$00,$01,$46,$42,$A7,$48,$6D
	dc.b $FD,$EC,$1F,$3C,$00,$04,$4E,$BA,$D6,$9C,$2B,$5F,$FE,$F0,$2F,$3C
	dc.b $00,$06,$00,$00,$2F,$2D,$FE,$F0,$2F,$0E,$4E,$BA,$F4,$96,$4E,$BA
	dc.b $C2,$92,$60,$00,$01,$1C,$10,$2D,$F3,$A7,$67,$0E,$3F,$3C,$00,$A0
	dc.b $2F,$0E,$4E,$BA,$F3,$A4,$60,$00,$00,$D0,$10,$2D,$F3,$A2,$67,$0A
	dc.b $20,$6E,$00,$10,$42,$10,$60,$00,$00,$C0,$10,$2D,$F3,$A5,$67,$0C
	dc.b $20,$6E,$00,$10,$10,$BC,$00,$01,$60,$00,$00,$AE,$42,$40,$10,$2D
	dc.b $FA,$BE,$3D,$40,$FD,$F8,$66,$52,$52,$6D,$E7,$1A,$48,$7A,$02,$3A
	dc.b $42,$A7,$30,$2D,$E7,$1A,$48,$C0,$2F,$00,$2F,$3C,$00,$00,$FF,$FC
	dc.b $4E,$BA,$B1,$36,$48,$6E,$FC,$72,$3F,$3C,$00,$02,$4E,$AD,$0A,$A2
	dc.b $41,$ED,$FA,$BE,$43,$EE,$FC,$72,$70,$7F,$30,$D9,$51,$C8,$FF,$FC
	dc.b $42,$40,$10,$2D,$FA,$BE,$3D,$40,$FD,$F8,$2F,$2D,$F4,$14,$3F,$2D
	dc.b $F3,$E0,$2F,$2D,$F3,$E2,$4E,$BA,$CB,$E4,$30,$2E,$FD,$F8,$B0,$6D
	dc.b $F3,$8E,$6F,$06,$1B,$6D,$F3,$8F,$FA,$BE,$1B,$6E,$FD,$F9,$FA,$BE
	dc.b $48,$6D,$FA,$BE,$48,$6D,$FE,$FA,$4E,$BA,$B0,$2A,$48,$6D,$FE,$FA
	dc.b $42,$67,$48,$6E,$FD,$FC,$2F,$2E,$00,$10,$48,$6E,$FD,$F2,$2F,$0E
	dc.b $4E,$BA,$F9,$2E,$20,$6E,$00,$10,$1F,$10,$3F,$3C,$00,$05,$2F,$2E
	dc.b $FD,$FC,$2F,$0E,$4E,$BA,$F3,$AC,$20,$6E,$00,$10,$70,$02,$B0,$10
	dc.b $67,$1A,$20,$6E,$00,$08,$42,$50,$20,$6E,$00,$10,$1F,$10,$3F,$3C
	dc.b $00,$09,$2F,$2D,$F4,$14,$2F,$0E,$4E,$BA,$F3,$88,$4E,$BA,$C1,$84
	dc.b $60,$0E,$3F,$3C,$00,$0C,$2F,$0E,$4E,$BA,$F2,$9E,$60,$00,$FD,$38
	dc.b $4A,$2D,$FF,$FB,$57,$C0,$4A,$00,$67,$10,$72,$03,$B2,$6D,$FE,$F8
	dc.b $5C,$C1,$C0,$01,$67,$04,$4E,$BA,$CD,$C6,$10,$2D,$FF,$FB,$48,$80
	dc.b $59,$40,$6B,$00,$00,$DC,$04,$40,$00,$0F,$6F,$08,$59,$40,$67,$20
	dc.b $60,$00,$00,$CE,$1F,$2D,$FF,$FB,$2F,$0E,$4E,$BA,$F8,$2E,$1F,$2D
	dc.b $FF,$FB,$2F,$0E,$4E,$BA,$F2,$EA,$4E,$BA,$C1,$28,$60,$00,$FC,$E8
	dc.b $1F,$3C,$00,$03,$2F,$0E,$4E,$BA,$F8,$12,$10,$2D,$F3,$6F,$48,$80
	dc.b $41,$ED,$F3,$58,$1D,$70,$00,$00,$FD,$F1,$70,$19,$B0,$2E,$FD,$F1
	dc.b $66,$06,$2F,$0E,$4E,$BA,$F2,$64,$53,$6E,$FD,$F6,$4A,$6E,$FD,$F6
	dc.b $66,$06,$1B,$6E,$FD,$FB,$F3,$A0,$4E,$BA,$C0,$E8,$10,$2D,$F3,$6F
	dc.b $48,$80,$53,$40,$1B,$40,$F3,$6F,$70,$18,$B0,$2E,$FD,$F1,$66,$48
	dc.b $4A,$2D,$FF,$FB,$57,$C0,$4A,$00,$67,$10,$72,$03,$B2,$6D,$FE,$F8
	dc.b $5C,$C1,$C0,$01,$67,$04,$4E,$BA,$CD,$26,$70,$04,$B0,$2D,$FF,$FB
	dc.b $5E,$C0,$4A,$00,$66,$0C,$72,$13,$B2,$2D,$FF,$FB,$5D,$C1,$80,$01
	dc.b $67,$06,$2F,$0E,$4E,$BA,$F2,$04,$10,$2D,$F3,$6F,$48,$80,$53,$40
	dc.b $1B,$40,$F3,$6F,$60,$00,$FF,$1A,$70,$01,$B0,$2E,$FD,$F1,$67,$00
	dc.b $FF,$10,$3F,$3C,$00,$0D,$2F,$0E,$4E,$BA,$F1,$9E,$60,$00,$FF,$02
	dc.b $1F,$3C,$00,$02,$2F,$0E,$4E,$BA,$F7,$62,$10,$2D,$F3,$6F,$48,$80
	dc.b $41,$ED,$F3,$58,$1D,$70,$00,$00,$FD,$F1,$56,$C0,$4A,$00,$67,$22
	dc.b $72,$19,$B2,$2E,$FD,$F1,$56,$C1,$C0,$01,$67,$16,$72,$18,$B2,$2E
	dc.b $FD,$F1,$56,$C1,$C0,$01,$67,$0A,$3F,$3C,$00,$0D,$2F,$0E,$4E,$BA
	dc.b $F1,$58,$2F,$0E,$4E,$BA,$F1,$94,$60,$00,$FE,$B6,$4F,$EE,$FC,$52
	dc.b $4C,$DF,$1C,$F8,$4E,$5E,$20,$5F,$DE,$FC,$00,$0C,$4E,$D0,$87,$4F
	dc.b $55,$54,$45,$58,$50,$52,$00,$02,$01,$23,$4E,$56,$FF,$FE,$2F,$07
	dc.b $42,$40,$10,$2D,$FA,$BF,$72,$40,$B2,$40,$67,$52,$10,$2D,$F3,$A5
	dc.b $67,$4C,$12,$2D,$F3,$A2,$66,$04,$82,$2D,$F3,$A3,$0A,$01,$00,$01
	dc.b $C0,$01,$67,$3A,$42,$67,$48,$6D,$FA,$BE,$4E,$AD,$06,$DA,$3E,$1F
	dc.b $66,$16,$3E,$2D,$EC,$B8,$3F,$07,$48,$6D,$FA,$BE,$1F,$3C,$00,$01
	dc.b $4E,$AD,$06,$8A,$52,$6D,$EC,$B8,$3F,$07,$2F,$2D,$F4,$18,$2F,$2D
	dc.b $EB,$5C,$3F,$2D,$EB,$5A,$3F,$2D,$DA,$5E,$4E,$AD,$06,$C2,$2E,$1F
	dc.b $4E,$5E,$4E,$75,$89,$47,$45,$4E,$44,$42,$47,$4C,$42,$4C,$00,$00
	dc.b $4E,$56,$FF,$00,$52,$AD,$EB,$8E,$2F,$2D,$EB,$8E,$4E,$BA,$1C,$92
	dc.b $10,$2D,$EC,$FF,$67,$00,$00,$84,$10,$2E,$00,$08,$0A,$00,$00,$01
	dc.b $4A,$00,$67,$14,$4A,$6D,$FB,$DE,$57,$C1,$C0,$01,$67,$0A,$48,$6E
	dc.b $FF,$00,$4E,$BA,$BA,$A8,$60,$10,$20,$6D,$FF,$FC,$2F,$28,$00,$08
	dc.b $48,$6E,$FF,$00,$4E,$BA,$AD,$9E,$10,$2D,$F3,$A6,$67,$1A,$10,$2D
	dc.b $EB,$21,$67,$06,$C0,$2D,$EC,$FD,$66,$40,$2F,$2D,$EB,$60,$48,$6E
	dc.b $FF,$00,$4E,$AD,$04,$1A,$60,$32,$42,$67,$3F,$2D,$EC,$E4,$4E,$AD
	dc.b $06,$12,$10,$1F,$67,$24,$08,$2D,$00,$00,$ED,$5D,$56,$C1,$C0,$01
	dc.b $67,$18,$42,$A7,$42,$67,$3F,$2D,$EC,$E4,$3F,$2D,$ED,$5E,$48,$6E
	dc.b $FF,$00,$4E,$AD,$06,$0A,$42,$2D,$EB,$25,$20,$6D,$FF,$FC,$2B,$68
	dc.b $00,$08,$EB,$6A,$42,$67,$4E,$BA,$C8,$1E,$1D,$5F,$00,$0A,$4E,$5E
	dc.b $20,$5F,$54,$4F,$4E,$D0,$91,$45,$4E,$44,$4F,$46,$43,$4F,$4E,$54
	dc.b $49,$4E,$55,$41,$54,$49,$4F,$4E,$00,$00,$4E,$56,$00,$00,$2F,$0C
	dc.b $53,$6D,$FB,$D6,$28,$6D,$FF,$FC,$42,$67,$3F,$2C,$00,$04,$4E,$BA
	dc.b $C6,$9A,$10,$1F,$67,$34,$10,$2C,$00,$0F,$66,$06,$80,$2E,$00,$08
	dc.b $67,$0C,$42,$67,$4E,$BA,$C7,$D0,$10,$1F,$66,$12,$60,$1C,$42,$67
	dc.b $1F,$2E,$00,$0A,$4E,$BA,$FE,$FA,$10,$1F,$66,$02,$60,$0C,$52,$6C
	dc.b $00,$0C,$39,$7C,$00,$01,$00,$04,$60,$BE,$28,$5F,$4E,$5E,$2E,$9F
	dc.b $4E,$75,$8A,$53,$55,$43,$4B,$55,$50,$52,$45,$53,$54,$00,$00,$00
	dc.b $4E,$56,$00,$00,$2F,$0C,$28,$6E,$00,$08,$4A,$AC,$00,$08,$67,$08
	dc.b $29,$6C,$00,$08,$FF,$FA,$60,$10,$41,$EC,$FE,$FA,$29,$48,$FF,$FA
	dc.b $2F,$2C,$FF,$FA,$4E,$BA,$B9,$86,$28,$5F,$4E,$5E,$2E,$9F,$4E,$75
	dc.b $8C,$47,$45,$54,$49,$4E,$50,$55,$54,$4C,$49,$4E,$45,$00,$00,$00
	dc.b $4E,$56,$FD,$FA,$48,$E7,$11,$00,$10,$2D,$EB,$24,$67,$04,$60,$00
	dc.b $02,$60,$1B,$7C,$00,$01,$EB,$24,$10,$2D,$EC,$C5,$66,$26,$4A,$AE
	dc.b $00,$08,$56,$C0,$44,$00,$1F,$00,$10,$2D,$EB,$21,$67,$04,$C0,$2D
	dc.b $EC,$FD,$1F,$00,$4E,$BA,$FF,$24,$4A,$AE,$00,$08,$66,$06,$2D,$6D
	dc.b $EB,$6A,$00,$08,$1B,$6D,$EC,$FD,$EB,$21,$52,$AD,$EB,$8E,$2F,$2D
	dc.b $EB,$8E,$4E,$BA,$1A,$DC,$10,$2D,$F3,$A7,$67,$00,$01,$3C,$4A,$6D
	dc.b $CD,$60,$5E,$C7,$44,$07,$10,$2D,$EC,$FF,$66,$06,$80,$07,$67,$00
	dc.b $01,$06,$2F,$0E,$4E,$BA,$FF,$4A,$70,$02,$B0,$6D,$F4,$32,$66,$0A
	dc.b $30,$2D,$F4,$2E,$44,$40,$3B,$40,$F4,$2E,$10,$2D,$EC,$FF,$67,$5E
	dc.b $12,$07,$66,$28,$08,$2D,$00,$00,$ED,$5D,$56,$C2,$4A,$02,$67,$4E
	dc.b $48,$E7,$E0,$00,$42,$67,$3F,$2D,$EC,$E4,$4E,$AD,$06,$12,$16,$1F
	dc.b $4C,$DF,$00,$07,$C4,$03,$82,$02,$C0,$01,$67,$32,$2F,$2D,$F4,$14
	dc.b $1F,$2D,$F3,$A2,$3F,$2D,$EC,$E4,$3F,$2D,$ED,$5E,$2F,$2E,$FF,$FA
	dc.b $4E,$AD,$06,$0A,$08,$2D,$00,$06,$ED,$5C,$67,$0A,$3F,$3C,$00,$0E
	dc.b $4E,$AD,$06,$02,$60,$0E,$20,$6D,$EC,$F8,$42,$10,$60,$06,$20,$6D
	dc.b $EC,$F8,$42,$10,$10,$07,$67,$7E,$72,$CD,$B2,$6D,$F4,$2E,$56,$C1
	dc.b $C0,$01,$67,$72,$48,$7A,$01,$84,$42,$A7,$30,$2D,$ED,$5E,$48,$C0
	dc.b $2F,$00,$2F,$3C,$00,$00,$00,$04,$4E,$BA,$AC,$0E,$48,$7A,$01,$6A
	dc.b $48,$7A,$01,$64,$2F,$2E,$FF,$FA,$48,$6E,$FD,$FA,$3F,$3C,$00,$05
	dc.b $4E,$AD,$0A,$A2,$41,$EE,$FE,$FA,$43,$EE,$FD,$FA,$70,$7F,$30,$D9
	dc.b $51,$C8,$FF,$FC,$10,$2D,$EB,$68,$66,$16,$48,$6D,$D2,$6E,$48,$6E
	dc.b $FE,$FA,$42,$67,$4E,$AD,$0A,$0A,$48,$6D,$D2,$6E,$4E,$AD,$09,$F2
	dc.b $4E,$AD,$07,$E2,$4A,$AD,$CD,$4E,$67,$0C,$2F,$2D,$CD,$4E,$48,$6E
	dc.b $FE,$FA,$4E,$AD,$04,$1A,$10,$07,$67,$00,$00,$F6,$48,$6D,$ED,$70
	dc.b $3F,$2D,$ED,$5E,$2F,$2D,$ED,$68,$3F,$2D,$ED,$66,$1F,$3C,$00,$01
	dc.b $4E,$AD,$07,$EA,$60,$00,$00,$DA,$4A,$6D,$CD,$60,$5E,$C0,$4A,$00
	dc.b $67,$34,$C0,$2D,$EE,$71,$67,$2E,$70,$02,$B0,$6D,$F4,$32,$66,$16
	dc.b $3F,$2D,$FB,$DE,$3F,$2D,$EB,$6E,$30,$2D,$F4,$2E,$44,$40,$3F,$00
	dc.b $4E,$BA,$BB,$E4,$60,$10,$3F,$2D,$FB,$DE,$3F,$2D,$EB,$6E,$3F,$2D
	dc.b $F4,$2E,$4E,$BA,$BB,$D2,$10,$2D,$EC,$FF,$67,$4A,$2F,$0E,$4E,$BA
	dc.b $FD,$E0,$2F,$2D,$EB,$60,$2F,$2E,$FF,$FA,$4E,$AD,$04,$1A,$52,$AD
	dc.b $E3,$E6,$10,$2D,$EE,$71,$67,$6C,$4A,$6D,$CD,$68,$57,$C1,$C0,$01
	dc.b $67,$62,$70,$02,$B0,$6D,$F4,$32,$66,$0A,$30,$2D,$F4,$2E,$44,$40
	dc.b $3B,$40,$F4,$2E,$3F,$2D,$F4,$2E,$3F,$2D,$FB,$DE,$3F,$2D,$EB,$6E
	dc.b $4E,$BA,$BB,$5E,$60,$3E,$10,$2D,$EE,$71,$67,$38,$4A,$6D,$CD,$68
	dc.b $57,$C1,$C0,$01,$4A,$00,$67,$2C,$4A,$6D,$CD,$66,$5E,$C1,$C0,$01
	dc.b $67,$22,$70,$02,$B0,$6D,$F4,$32,$66,$0A,$30,$2D,$F4,$2E,$44,$40
	dc.b $3B,$40,$F4,$2E,$3F,$2D,$F4,$2E,$3F,$2D,$FB,$DE,$3F,$2D,$EB,$6E
	dc.b $4E,$BA,$BB,$1E,$42,$6D,$CD,$68,$42,$6D,$CD,$66,$42,$6D,$CD,$60
	dc.b $4C,$DF,$00,$88,$4E,$5E,$2E,$9F,$4E,$75,$89,$45,$4E,$44,$4F,$46
	dc.b $4C,$49,$4E,$45,$00,$06,$01,$09,$01,$3A,$01,$23,$4E,$56,$00,$00
	dc.b $10,$2D,$FB,$C0,$66,$10,$42,$6D,$FB,$DE,$42,$6D,$CD,$68,$42,$6D
	dc.b $CD,$66,$42,$6D,$CD,$60,$42,$6D,$F3,$BA,$42,$2D,$F3,$B7,$42,$2D
	dc.b $FB,$C0,$42,$2D,$EC,$C5,$42,$2D,$EC,$C4,$3B,$6D,$ED,$5E,$EB,$6E
	dc.b $70,$00,$2B,$40,$EB,$6A,$42,$2D,$EB,$25,$42,$2D,$EB,$24,$1B,$7C
	dc.b $00,$01,$EE,$71,$2B,$6D,$F4,$18,$F4,$14,$3B,$7C,$FF,$82,$F4,$2E
	dc.b $4E,$5E,$4E,$75,$8C,$49,$4E,$49,$54,$53,$57,$49,$54,$43,$48,$45
	dc.b $53,$00,$00,$00,$4E,$56,$FE,$92,$48,$E7,$07,$08,$28,$6E,$00,$0C
	dc.b $3A,$2E,$00,$0A,$3C,$2E,$00,$08,$BA,$46,$6F,$68,$42,$47,$42,$40
	dc.b $10,$14,$4A,$40,$5E,$C0,$4A,$00,$67,$24,$42,$41,$12,$2C,$00,$01
	dc.b $74,$3A,$B4,$41,$57,$C1,$C0,$01,$67,$14,$1D,$7C,$00,$3A,$FF,$85
	dc.b $7E,$01,$2F,$0C,$2F,$3C,$00,$01,$00,$01,$4E,$AD,$0A,$B2,$BA,$46
	dc.b $6F,$0C,$52,$47,$1D,$BC,$00,$20,$70,$84,$52,$46,$60,$F0,$1D,$47
	dc.b $FF,$84,$48,$6E,$FF,$84,$2F,$0C,$48,$6E,$FE,$92,$3F,$3C,$00,$02
	dc.b $4E,$AD,$0A,$A2,$41,$EE,$FE,$92,$22,$4C,$70,$3C,$32,$D8,$51,$C8
	dc.b $FF,$FC,$60,$3A,$BA,$46,$6C,$36,$BA,$46,$5D,$C0,$4A,$00,$67,$2E
	dc.b $42,$41,$12,$14,$74,$01,$B4,$41,$5D,$C1,$C0,$01,$67,$20,$42,$41
	dc.b $12,$2C,$00,$01,$74,$20,$B4,$41,$57,$C1,$C0,$01,$67,$10,$2F,$0C
	dc.b $2F,$3C,$00,$01,$00,$01,$4E,$AD,$0A,$B2,$53,$46,$60,$CA,$4C,$DF
	dc.b $10,$E0,$4E,$5E,$20,$5F,$50,$4F,$4E,$D0,$8B,$41,$44,$4A,$55,$53
	dc.b $54,$46,$49,$45,$4C,$44,$00,$00,$4E,$56,$FF,$FE,$10,$2D,$FA,$BD
	dc.b $67,$36,$4A,$AD,$EC,$E6,$56,$C1,$C0,$01,$67,$2C,$42,$40,$10,$2D
	dc.b $FA,$BE,$3D,$40,$FF,$FE,$48,$6D,$FA,$BE,$4E,$AD,$04,$C2,$10,$2D
	dc.b $EC,$FF,$67,$14,$48,$6D,$F7,$BE,$3F,$2E,$FF,$FE,$42,$40,$10,$2D
	dc.b $FA,$BE,$3F,$00,$4E,$BA,$FE,$EE,$48,$6D,$FA,$BE,$48,$6D,$EF,$72
	dc.b $4E,$BA,$A8,$62,$42,$40,$10,$2D,$FA,$BE,$4A,$40,$6F,$00,$00,$B4
	dc.b $42,$67,$48,$6D,$FA,$BE,$1F,$2D,$F3,$A1,$42,$67,$4E,$BA,$C2,$16
	dc.b $10,$1F,$67,$00,$00,$96,$10,$2D,$F3,$A6,$66,$06,$80,$2D,$F3,$A2
	dc.b $67,$7E,$10,$2D,$F4,$1B,$02,$40,$00,$01,$4A,$00,$67,$56,$C0,$2D
	dc.b $F3,$A5,$4A,$00,$67,$4E,$12,$2D,$F3,$A2,$66,$04,$82,$2D,$F3,$A3
	dc.b $0A,$01,$00,$01,$C0,$01,$67,$3C,$10,$2D,$EB,$93,$67,$2E,$52,$AD
	dc.b $F4,$18,$42,$67,$1F,$3C,$00,$01,$4E,$AD,$07,$0A,$2B,$6D,$F4,$18
	dc.b $F4,$14,$2B,$6D,$F4,$18,$EC,$AC,$42,$40,$10,$2D,$F9,$BA,$4A,$40
	dc.b $66,$12,$3F,$3C,$00,$CD,$4E,$AD,$07,$CA,$60,$08,$3F,$3C,$00,$CC
	dc.b $4E,$AD,$07,$CA,$2F,$2D,$F4,$18,$3F,$2D,$F3,$E0,$2F,$2D,$F3,$E2
	dc.b $4E,$BA,$C3,$5A,$10,$2D,$F0,$B1,$67,$18,$4E,$BA,$F9,$5E,$60,$12
	dc.b $3F,$3C,$00,$A0,$4E,$AD,$07,$CA,$60,$08,$3F,$3C,$00,$07,$4E,$AD
	dc.b $07,$CA,$4E,$5E,$4E,$75,$8A,$50,$52,$4F,$43,$45,$53,$53,$4C,$42
	dc.b $4C,$00,$00,$00,$4E,$56,$FF,$FA,$48,$E7,$07,$08,$28,$6E,$00,$08
	dc.b $4A,$AD,$EC,$E6,$66,$18,$10,$2C,$FF,$FB,$67,$00,$00,$94,$48,$6D
	dc.b $FA,$BE,$48,$6D,$EF,$72,$4E,$BA,$A7,$6C,$60,$00,$00,$84,$10,$2C
	dc.b $FF,$FB,$67,$3E,$10,$2D,$FA,$BD,$67,$2C,$48,$6D,$FA,$BE,$4E,$AD
	dc.b $04,$C2,$42,$47,$1E,$2D,$FA,$BE,$4A,$47,$5E,$C0,$44,$00,$19,$40
	dc.b $FF,$FB,$10,$2D,$EC,$FF,$67,$0E,$48,$6D,$F7,$BE,$3F,$2C,$FF,$F6
	dc.b $3F,$07,$4E,$BA,$FD,$B0,$48,$6D,$FA,$BE,$48,$6D,$EF,$72,$4E,$BA
	dc.b $A7,$24,$10,$2D,$F8,$B5,$67,$30,$42,$45,$1A,$2D,$F8,$B6,$48,$6D
	dc.b $F8,$B6,$4E,$AD,$04,$C2,$42,$46,$1C,$2D,$F8,$B6,$10,$2D,$EC,$FF
	dc.b $67,$16,$48,$6D,$F7,$44,$4A,$46,$57,$C0,$44,$00,$48,$80,$D0,$45
	dc.b $3F,$00,$3F,$06,$4E,$BA,$FD,$6E,$48,$6D,$FC,$E8,$4E,$AD,$04,$C2
	dc.b $10,$2C,$FF,$FB,$67,$26,$42,$67,$48,$6D,$FA,$BE,$1F,$2D,$F3,$A1
	dc.b $42,$67,$4E,$BA,$C0,$A0,$19,$5F,$FF,$FB,$10,$2C,$FF,$FB,$66,$0C
	dc.b $42,$2D,$FA,$BE,$3F,$3C,$00,$07,$4E,$AD,$07,$CA,$4C,$DF,$10,$E0
	dc.b $4E,$5E,$2E,$9F,$4E,$75,$8C,$50,$52,$45,$50,$41,$52,$45,$50,$41
	dc.b $52,$54,$53,$00,$00,$00,$4E,$56,$FF,$F6,$48,$E7,$0F,$00,$42,$67
	dc.b $4E,$BA,$C1,$74,$10,$1F,$67,$00,$04,$98,$4E,$BA,$FC,$A0,$42,$40
	dc.b $10,$2D,$FC,$E9,$38,$00,$42,$40,$10,$2D,$FC,$E8,$4A,$40,$57,$C0
	dc.b $4A,$00,$66,$14,$72,$3B,$B2,$44,$57,$C1,$80,$01,$66,$0A,$72,$2A
	dc.b $B2,$44,$57,$C1,$80,$01,$67,$32,$10,$2D,$EC,$FD,$67,$0E,$1F,$3C
	dc.b $00,$01,$1F,$3C,$00,$01,$4E,$BA,$F9,$32,$60,$B2,$3B,$7C,$00,$02
	dc.b $FB,$D6,$4A,$AD,$EC,$E6,$67,$08,$48,$6D,$FC,$E8,$4E,$AD,$04,$C2
	dc.b $48,$6D,$FC,$E8,$4E,$BA,$F9,$BA,$60,$94,$4E,$BA,$AF,$96,$42,$2D
	dc.b $EF,$72,$42,$2D,$EE,$72,$42,$40,$10,$2D,$FA,$BE,$3D,$40,$FF,$F6
	dc.b $5E,$C0,$44,$00,$1D,$40,$FF,$FB,$42,$05,$20,$6D,$CB,$1E,$2B,$68
	dc.b $02,$30,$EB,$5C,$10,$2E,$FF,$FB,$67,$78,$42,$40,$10,$2D,$FA,$BF
	dc.b $3C,$00,$70,$2E,$B0,$46,$66,$3C,$7A,$01,$48,$6D,$FA,$BE,$48,$6D
	dc.b $EF,$72,$4E,$BA,$A5,$E0,$42,$67,$48,$6D,$FA,$BE,$1F,$3C,$00,$01
	dc.b $3F,$3C,$00,$2E,$4E,$BA,$BF,$9E,$10,$1F,$67,$06,$4E,$AD,$05,$62
	dc.b $60,$08,$3F,$3C,$00,$06,$4E,$AD,$07,$CA,$42,$2E,$FF,$FB,$42,$2D
	dc.b $FA,$BD,$60,$2E,$70,$40,$B0,$46,$66,$28,$10,$2D,$F3,$A7,$67,$22
	dc.b $10,$2D,$EC,$FD,$66,$08,$3F,$3C,$00,$3B,$4E,$AD,$07,$CA,$48,$6D
	dc.b $FA,$BE,$48,$6D,$EF,$72,$4E,$BA,$A5,$8C,$42,$2D,$FA,$BE,$42,$2E
	dc.b $FF,$FB,$42,$40,$10,$2D,$F9,$BA,$4A,$40,$66,$30,$10,$2D,$EC,$FD
	dc.b $67,$04,$60,$00,$FE,$DA,$10,$05,$67,$0C,$2F,$2D,$EB,$6A,$4E,$BA
	dc.b $F8,$F0,$60,$00,$FE,$CA,$4E,$BA,$FC,$B0,$1B,$7C,$00,$01,$EC,$C5
	dc.b $2F,$2D,$EB,$6A,$4E,$BA,$F8,$DA,$60,$00,$FE,$B4,$10,$2D,$F9,$B9
	dc.b $67,$0E,$4A,$6D,$EC,$E4,$5E,$C1,$C0,$01,$67,$04,$4E,$AD,$05,$52
	dc.b $48,$6D,$F9,$BA,$48,$6D,$EE,$72,$4E,$BA,$A5,$2A,$42,$67,$48,$6D
	dc.b $F9,$BA,$1F,$3C,$00,$01,$42,$67,$4E,$BA,$BE,$EA,$10,$1F,$67,$00
	dc.b $02,$CE,$42,$2D,$F4,$30,$42,$A7,$48,$6D,$F4,$32,$48,$6D,$F4,$31
	dc.b $48,$6D,$F4,$2E,$48,$6D,$F4,$2C,$48,$6D,$F9,$BA,$48,$6D,$F4,$2A
	dc.b $4E,$AD,$05,$6A,$2B,$5F,$F4,$26,$66,$5E,$10,$2D,$F3,$C5,$67,$26
	dc.b $42,$A7,$48,$6D,$F4,$32,$48,$6D,$F4,$2E,$48,$6D,$F4,$2C,$48,$6D
	dc.b $F9,$BA,$4E,$AD,$03,$C2,$2B,$5F,$F4,$26,$67,$0A,$3B,$7C,$80,$00
	dc.b $F3,$BA,$42,$2D,$F4,$31,$4A,$AD,$F4,$26,$66,$2C,$10,$2D,$F3,$B9
	dc.b $67,$26,$42,$A7,$48,$6D,$F4,$32,$48,$6D,$F4,$2E,$48,$6D,$F4,$2C
	dc.b $48,$6D,$F9,$BA,$4E,$AD,$05,$B2,$2B,$5F,$F4,$26,$67,$0A,$1B,$7C
	dc.b $00,$01,$F3,$B7,$42,$2D,$F4,$31,$4A,$AD,$F4,$26,$66,$6C,$10,$2D
	dc.b $EC,$FD,$67,$0E,$42,$67,$1F,$3C,$00,$01,$4E,$BA,$F7,$5E,$60,$00
	dc.b $FD,$DE,$3B,$7C,$00,$03,$F4,$32,$3B,$7C,$FF,$81,$F4,$2E,$42,$67
	dc.b $4E,$AD,$05,$5A,$10,$1F,$66,$00,$02,$5C,$2F,$0E,$4E,$BA,$FC,$C6
	dc.b $3B,$7C,$00,$02,$F4,$32,$3B,$7C,$FF,$D2,$F4,$2E,$42,$67,$4E,$AD
	dc.b $07,$42,$10,$1F,$66,$00,$02,$3E,$10,$2D,$F4,$30,$67,$0C,$3F,$3C
	dc.b $00,$36,$4E,$AD,$07,$CA,$60,$00,$02,$2C,$3F,$3C,$00,$5B,$48,$6D
	dc.b $F9,$BA,$4E,$AD,$07,$C2,$60,$00,$02,$1C,$70,$02,$B0,$6D,$F4,$32
	dc.b $66,$00,$00,$8A,$70,$18,$B0,$6D,$F4,$2E,$67,$68,$70,$32,$B0,$6D
	dc.b $F4,$2E,$5F,$C0,$4A,$00,$67,$0A,$72,$50,$B2,$6D,$F4,$2E,$5E,$C1
	dc.b $C0,$01,$44,$00,$1B,$40,$EC,$C4,$70,$3D,$B0,$6D,$F4,$2E,$5E,$C0
	dc.b $4A,$00,$66,$0C,$72,$45,$B2,$6D,$F4,$2E,$5D,$C1,$80,$01,$67,$34
	dc.b $10,$2D,$EC,$FD,$67,$0E,$42,$67,$1F,$3C,$00,$01,$4E,$BA,$F6,$AC
	dc.b $60,$00,$FD,$2C,$10,$2D,$EC,$C4,$67,$14,$10,$2E,$FF,$FB,$67,$14
	dc.b $48,$6D,$FA,$BE,$48,$6D,$EF,$72,$4E,$BA,$A3,$AA,$60,$06,$2F,$0E
	dc.b $4E,$BA,$FC,$12,$4E,$AD,$07,$52,$10,$2D,$EB,$23,$67,$00,$01,$96
	dc.b $2F,$2D,$EB,$6A,$4E,$BA,$F7,$1A,$60,$00,$01,$96,$10,$2D,$EC,$FD
	dc.b $67,$0E,$42,$67,$1F,$3C,$00,$01,$4E,$BA,$F6,$60,$60,$00,$FC,$E0
	dc.b $10,$2D,$F0,$B1,$67,$2A,$C0,$2D,$F3,$A5,$67,$24,$70,$00,$30,$2D
	dc.b $F0,$AE,$C0,$BC,$00,$00,$00,$02,$4A,$80,$66,$14,$2F,$2D,$F4,$14
	dc.b $2F,$2D,$EB,$5C,$3F,$2D,$EB,$5A,$3F,$2D,$DA,$5E,$4E,$AD,$06,$CA
	dc.b $2F,$0E,$4E,$BA,$FB,$B0,$10,$2D,$F3,$A5,$0A,$00,$00,$01,$4A,$00
	dc.b $66,$0E,$80,$2D,$F3,$A2,$4A,$00,$66,$06,$80,$2D,$F3,$A3,$67,$20
	dc.b $10,$2E,$FF,$FB,$67,$0E,$2F,$2D,$F4,$14,$3F,$2D,$F3,$E0,$42,$A7
	dc.b $4E,$BA,$BE,$AA,$3F,$3C,$00,$A5,$4E,$AD,$07,$CA,$60,$00,$01,$06
	dc.b $10,$2D,$F4,$1B,$02,$40,$00,$01,$67,$26,$10,$2D,$EB,$93,$67,$18
	dc.b $52,$AD,$F4,$18,$1F,$2D,$F3,$A4,$1F,$3C,$00,$01,$4E,$AD,$07,$0A
	dc.b $2B,$6D,$F4,$18,$EC,$AC,$60,$08,$3F,$3C,$00,$CC,$4E,$AD,$07,$CA
	dc.b $2B,$6D,$F4,$18,$F4,$14,$10,$2E,$FF,$FB,$67,$54,$2F,$2D,$F4,$14
	dc.b $3F,$2D,$F3,$E0,$42,$A7,$4E,$BA,$BE,$54,$10,$2D,$F0,$B1,$67,$40
	dc.b $70,$40,$B0,$46,$67,$3A,$42,$67,$48,$6D,$FA,$BE,$4E,$AD,$06,$DA
	dc.b $3E,$1F,$66,$16,$3E,$2D,$EC,$B8,$3F,$07,$48,$6D,$FA,$BE,$1F,$3C
	dc.b $00,$01,$4E,$AD,$06,$8A,$52,$6D,$EC,$B8,$3F,$07,$2F,$2D,$F4,$14
	dc.b $2F,$2D,$EB,$5C,$3F,$2D,$EB,$5A,$3F,$2D,$DA,$5E,$4E,$AD,$06,$C2
	dc.b $20,$2D,$F4,$18,$90,$AD,$EC,$AC,$6A,$02,$44,$80,$0C,$80,$00,$00
	dc.b $01,$00,$6F,$10,$1F,$2D,$F3,$A4,$42,$67,$4E,$AD,$07,$0A,$2B,$6D
	dc.b $F4,$18,$EC,$AC,$3F,$2D,$EB,$6E,$4E,$AD,$05,$A2,$60,$46,$10,$2D
	dc.b $EC,$FD,$67,$0E,$42,$67,$1F,$3C,$00,$01,$4E,$BA,$F5,$1E,$60,$00
	dc.b $FB,$9E,$10,$2E,$FF,$FB,$67,$0C,$48,$6D,$FA,$BE,$48,$6D,$EF,$72
	dc.b $4E,$BA,$A2,$22,$3F,$3C,$00,$09,$4E,$AD,$07,$CA,$30,$2D,$FB,$D6
	dc.b $42,$41,$41,$ED,$FC,$E8,$12,$30,$00,$00,$4A,$41,$66,$06,$1B,$7C
	dc.b $00,$01,$EC,$C5,$2F,$2D,$EB,$6A,$4E,$BA,$F5,$86,$60,$00,$FB,$60
	dc.b $10,$2D,$EB,$23,$66,$06,$42,$67,$4E,$AD,$07,$4A,$4C,$DF,$00,$F0
	dc.b $4E,$5E,$4E,$75,$8B,$4D,$41,$49,$4E,$43,$54,$4C,$4C,$4F,$4F,$50
	dc.b $00,$00,$4E,$56,$00,$00,$42,$A7,$4E,$BA,$10,$86,$4E,$BA,$FB,$28
	dc.b $4E,$5E,$4E,$75,$88,$4C,$4F,$41,$44,$4D,$41,$49,$4E,$00,$00,$00
	dc.b $4E,$56,$00,$00,$2F,$0E,$4E,$AD,$05,$AA,$48,$6D,$05,$5A,$4E,$BA
	dc.b $C0,$44,$48,$6D,$07,$CA,$4E,$BA,$C0,$3C,$48,$6D,$06,$0A,$4E,$BA
	dc.b $C0,$34,$48,$6D,$03,$C2,$4E,$BA,$C0,$2C,$48,$6D,$05,$B2,$4E,$BA
	dc.b $C0,$24,$4E,$5E,$4E,$75,$88,$4C,$4F,$41,$44,$53,$45,$47,$53,$00
	dc.b $00,$00,$4E,$BA,$10,$D0,$4E,$56,$00,$00,$2C,$5F,$4E,$BA,$10,$C8
	dc.b $4A,$80,$67,$02,$4E,$75,$70,$00,$2B,$40,$EC,$B4,$70,$00,$2B,$40
	dc.b $EC,$9E,$42,$A7,$4E,$BA,$0F,$3E,$2F,$3C,$00,$00,$77,$10,$2F,$3C
	dc.b $00,$00,$27,$B0,$42,$A7,$1F,$3C,$00,$01,$42,$67,$4E,$AD,$0A,$3A
	dc.b $42,$67,$4E,$AD,$0A,$42,$42,$67,$4E,$AD,$08,$82,$10,$1F,$67,$04
	dc.b $4E,$AD,$03,$FA,$42,$67,$4E,$AD,$08,$82,$10,$1F,$67,$10,$48,$7A
	dc.b $00,$92,$4E,$AD,$08,$2A,$48,$6D,$08,$2A,$4E,$BA,$BF,$A8,$42,$67
	dc.b $48,$7A,$00,$78,$48,$6D,$E3,$EA,$4E,$AD,$08,$9A,$10,$1F,$66,$0C
	dc.b $2F,$2D,$E4,$EE,$48,$6D,$E3,$EA,$4E,$BA,$A0,$EA,$41,$ED,$E3,$EA
	dc.b $2B,$48,$E4,$EA,$1B,$7C,$00,$01,$E4,$FB,$42,$6D,$E4,$F6,$42,$6D
	dc.b $E4,$F4,$1F,$2D,$E4,$FB,$4E,$AD,$07,$62,$1F,$2D,$E4,$FB,$4E,$AD
	dc.b $04,$02,$42,$2D,$E4,$FB,$48,$6D,$04,$02,$4E,$BA,$BF,$58,$4E,$BA
	dc.b $FF,$00,$4E,$AD,$06,$6A,$48,$6D,$06,$6A,$4E,$BA,$BF,$48,$60,$D2
	dc.b $4E,$BA,$10,$66,$4E,$BA,$10,$68,$4E,$75,$4E,$5E,$4E,$75,$89,$41
	dc.b $53,$53,$45,$4D,$42,$4C,$45,$52,$00,$0C,$07,$43,$6F,$6D,$6D,$61
	dc.b $6E,$64,$03,$41,$73,$6D,$4E,$56,$FE,$B0,$20,$6E,$00,$0C,$43,$EE
	dc.b $FF,$AE,$70,$28,$32,$D8,$51,$C8,$FF,$FC,$20,$6E,$00,$08,$43,$EE
	dc.b $FF,$5C,$70,$28,$32,$D8,$51,$C8,$FF,$FC,$20,$6E,$00,$10,$2F,$08
	dc.b $48,$6E,$FF,$AE,$48,$7A,$00,$54,$48,$7A,$00,$46,$48,$7A,$00,$40
	dc.b $48,$6E,$FF,$5C,$48,$6E,$FE,$B0,$3F,$3C,$00,$05,$4E,$AD,$0A,$A2
	dc.b $20,$5F,$43,$EE,$FE,$B0,$1F,$11,$3F,$3C,$00,$50,$4E,$AD,$0A,$92
	dc.b $70,$28,$30,$D9,$51,$C8,$FF,$FC,$4E,$5E,$20,$5F,$50,$4F,$4E,$D0
	dc.b $8B,$47,$45,$54,$43,$4F,$4D,$50,$44,$41,$54,$45,$00,$10,$01,$29
	dc.b $08,$30,$32,$2F,$31,$33,$2F,$39,$35,$00,$02,$20,$28,$00,$20,$2F
	dc.b $00,$04,$22,$2F,$00,$08,$2F,$00,$C0,$C1,$20,$40,$20,$01,$C2,$DF
	dc.b $42,$40,$48,$40,$67,$02,$C0,$D7,$54,$8F,$D0,$41,$48,$40,$42,$40
	dc.b $D0,$88,$4E,$75,$22,$2F,$00,$04,$20,$2F,$00,$08,$41,$FA,$00,$0A
	dc.b $32,$7C,$00,$02,$4E,$F0,$92,$FE,$60,$06,$4C,$41,$08,$01,$4E,$75
	dc.b $4E,$BA,$00,$24,$20,$01,$4E,$75,$22,$2F,$00,$04,$20,$2F,$00,$08
	dc.b $41,$FA,$00,$0A,$32,$7C,$00,$02,$4E,$F0,$92,$FE,$60,$08,$4C,$41
	dc.b $08,$01,$C3,$40,$4E,$75,$4A,$80,$6B,$14,$4A,$81,$6B,$06,$4E,$BA
	dc.b $00,$46,$4E,$75,$44,$81,$4E,$BA,$00,$3E,$44,$81,$4E,$75,$44,$80
	dc.b $4A,$81,$6B,$0A,$4E,$BA,$00,$30,$44,$80,$44,$81,$4E,$75,$44,$81
	dc.b $4E,$BA,$00,$24,$44,$80,$4E,$75,$22,$2F,$00,$04,$20,$2F,$00,$08
	dc.b $41,$FA,$00,$0A,$32,$7C,$00,$02,$4E,$F0,$92,$FE,$60,$08,$4C,$41
	dc.b $00,$01,$C3,$40,$4E,$75,$3F,$01,$48,$41,$4A,$41,$66,$1C,$22,$00
	dc.b $42,$41,$48,$41,$67,$0A,$82,$D7,$48,$41,$48,$40,$30,$01,$48,$40
	dc.b $80,$DF,$32,$00,$42,$40,$48,$40,$4E,$75,$48,$41,$3E,$82,$2F,$03
	dc.b $34,$00,$26,$01,$72,$01,$42,$40,$48,$40,$66,$0C,$48,$40,$30,$02
	dc.b $72,$00,$60,$16,$D2,$41,$65,$12,$D4,$42,$D1,$80,$B0,$83,$65,$F4
	dc.b $90,$83,$D2,$41,$08,$C1,$00,$00,$64,$EE,$26,$1F,$34,$1F,$4E,$75
	dc.b $22,$5F,$20,$57,$48,$D0,$DE,$FC,$70,$00,$4E,$D1,$20,$2F,$00,$08
	dc.b $66,$02,$70,$01,$20,$6F,$00,$04,$4C,$D0,$DE,$FC,$4E,$D1,$4E,$56
	dc.b $00,$00,$48,$E7,$03,$00,$2C,$2E,$00,$08,$4A,$AD,$CF,$8A,$66,$08
	dc.b $41,$ED,$CE,$46,$2B,$48,$CF,$8A,$20,$6D,$CF,$8A,$42,$68,$00,$02
	dc.b $7E,$01,$60,$04,$E2,$86,$52,$87,$70,$01,$C0,$86,$67,$F6,$20,$07
	dc.b $E1,$48,$48,$40,$42,$40,$2F,$00,$4E,$BA,$05,$4C,$58,$4F,$4C,$EE
	dc.b $00,$C0,$FF,$F8,$4E,$5E,$4E,$75,$87,$73,$69,$67,$5F,$64,$66,$6C
	dc.b $00,$00,$4E,$56,$00,$00,$42,$A7,$3F,$3C,$A8,$6E,$1F,$3C,$00,$01
	dc.b $4E,$BA,$05,$B6,$42,$A7,$3F,$3C,$AA,$6E,$1F,$3C,$00,$01,$4E,$BA
	dc.b $05,$A8,$20,$1F,$B0,$9F,$66,$08,$3D,$7C,$02,$00,$00,$08,$60,$06
	dc.b $3D,$7C,$04,$00,$00,$08,$4E,$5E,$4E,$75,$91,$5F,$5F,$4E,$55,$4D
	dc.b $54,$4F,$4F,$4C,$42,$4F,$58,$54,$52,$41,$50,$53,$00,$00,$4E,$56
	dc.b $00,$00,$70,$00,$30,$2E,$00,$08,$C0,$BC,$00,$00,$08,$00,$4A,$80
	dc.b $6F,$08,$1D,$7C,$00,$01,$00,$0A,$60,$04,$42,$2E,$00,$0A,$4E,$5E
	dc.b $20,$5F,$54,$4F,$4E,$D0,$8D,$5F,$5F,$47,$45,$54,$54,$52,$41,$50
	dc.b $54,$59,$50,$45,$00,$00,$4E,$56,$FF,$FE,$48,$E7,$03,$00,$3E,$2E
	dc.b $00,$08,$42,$67,$3F,$07,$4E,$BA,$FF,$B6,$1C,$1F,$70,$01,$B0,$06
	dc.b $66,$1A,$70,$00,$30,$07,$C0,$BC,$00,$00,$07,$FF,$3E,$00,$42,$67
	dc.b $4E,$BA,$FF,$50,$BE,$5F,$6D,$04,$3E,$3C,$A8,$9F,$42,$A7,$3F,$07
	dc.b $1F,$06,$4E,$BA,$05,$04,$42,$A7,$3F,$3C,$A8,$9F,$1F,$3C,$00,$01
	dc.b $4E,$BA,$04,$F6,$20,$1F,$B0,$9F,$56,$C0,$44,$00,$1D,$40,$00,$0A
	dc.b $4C,$DF,$00,$C0,$4E,$5E,$20,$5F,$54,$4F,$4E,$D0,$8D,$54,$52,$41
	dc.b $50,$41,$56,$41,$49,$4C,$41,$42,$4C,$45,$00,$00,$20,$1F,$22,$5F
	dc.b $20,$5F,$2F,$00,$70,$00,$72,$00,$10,$18,$12,$19,$90,$41,$6C,$02
	dc.b $D2,$40,$B0,$00,$60,$02,$B1,$09,$56,$C9,$FF,$FC,$67,$0A,$6D,$04
	dc.b $70,$01,$60,$04,$70,$01,$44,$40,$3F,$40,$00,$04,$4E,$75,$88,$50
	dc.b $4C,$53,$74,$72,$43,$6D,$70,$00,$00,$00,$20,$1F,$22,$5F,$20,$5F
	dc.b $2E,$88,$2F,$00,$70,$00,$10,$19,$10,$C0,$60,$02,$10,$D9,$51,$C8
	dc.b $FF,$FC,$4E,$75,$88,$50,$4C,$53,$74,$72,$43,$70,$79,$00,$00,$00
	dc.b $4E,$56,$FF,$FC,$48,$E7,$03,$18,$4A,$6D,$CF,$72,$66,$00,$00,$BC
	dc.b $59,$8F,$2F,$3C,$43,$4F,$44,$45,$48,$7A,$00,$C8,$A8,$20,$28,$5F
	dc.b $20,$0C,$67,$00,$00,$A6,$55,$8F,$A9,$94,$55,$8F,$2F,$0C,$A9,$A4
	dc.b $30,$1F,$B0,$5F,$66,$00,$00,$94,$41,$ED,$02,$AA,$22,$6D,$CF,$8E
	dc.b $23,$48,$00,$0C,$26,$54,$30,$13,$08,$00,$00,$00,$67,$08,$3B,$7C
	dc.b $00,$28,$CF,$70,$60,$06,$3B,$7C,$00,$04,$CF,$70,$59,$8F,$2F,$0C
	dc.b $4E,$BA,$03,$F8,$30,$2D,$CF,$70,$48,$C0,$22,$1F,$92,$80,$20,$01
	dc.b $72,$04,$4E,$BA,$FC,$D8,$2C,$00,$70,$00,$26,$40,$60,$36,$2F,$0C
	dc.b $A9,$A2,$30,$2D,$CF,$70,$48,$C0,$D0,$94,$2D,$40,$FF,$FC,$30,$2D
	dc.b $CF,$72,$48,$C0,$20,$6E,$FF,$FC,$E5,$80,$30,$30,$08,$00,$48,$C0
	dc.b $2E,$00,$67,$08,$20,$0D,$26,$40,$D7,$C7,$4E,$93,$30,$2D,$CF,$72
	dc.b $52,$6D,$CF,$72,$30,$2D,$CF,$72,$48,$C0,$BC,$80,$6E,$C0,$20,$0B
	dc.b $67,$04,$2F,$0B,$A9,$F1,$2F,$0C,$A9,$A3,$4C,$EE,$18,$C0,$FF,$EC
	dc.b $4E,$5E,$4E,$75,$8B,$5F,$5F,$43,$70,$6C,$75,$73,$49,$6E,$69,$74
	dc.b $00,$2A,$28,$25,$5F,$53,$74,$61,$74,$69,$63,$5F,$43,$6F,$6E,$73
	dc.b $74,$72,$75,$63,$74,$6F,$72,$5F,$44,$65,$73,$74,$72,$75,$63,$74
	dc.b $6F,$72,$5F,$50,$6F,$69,$6E,$74,$65,$72,$73,$00,$4E,$56,$FF,$FC
	dc.b $48,$E7,$01,$18,$4A,$6D,$CF,$72,$67,$64,$59,$8F,$2F,$3C,$43,$4F
	dc.b $44,$45,$48,$7A,$00,$70,$A9,$A1,$28,$5F,$20,$0C,$67,$50,$55,$8F
	dc.b $A9,$94,$55,$8F,$2F,$0C,$A9,$A4,$30,$1F,$B0,$5F,$66,$40,$60,$34
	dc.b $2F,$0C,$A9,$A2,$30,$2D,$CF,$70,$48,$C0,$D0,$94,$2D,$40,$FF,$FC
	dc.b $53,$6D,$CF,$72,$30,$2D,$CF,$72,$48,$C0,$20,$6E,$FF,$FC,$E5,$80
	dc.b $30,$30,$08,$02,$48,$C0,$2E,$00,$20,$0D,$26,$40,$D7,$C7,$4A,$87
	dc.b $67,$02,$4E,$93,$4A,$6D,$CF,$72,$6E,$C6,$2F,$0C,$A9,$A3,$4C,$EE
	dc.b $18,$80,$FF,$F0,$4E,$5E,$4E,$75,$89,$64,$74,$6F,$72,$73,$5F,$5F
	dc.b $46,$76,$00,$2A,$28,$25,$5F,$53,$74,$61,$74,$69,$63,$5F,$43,$6F
	dc.b $6E,$73,$74,$72,$75,$63,$74,$6F,$72,$5F,$44,$65,$73,$74,$72,$75
	dc.b $63,$74,$6F,$72,$5F,$50,$6F,$69,$6E,$74,$65,$72,$73,$00,$4E,$56
	dc.b $00,$00,$48,$E7,$13,$38,$2E,$2E,$00,$18,$26,$6E,$00,$0C,$4E,$AD
	dc.b $04,$0A,$4A,$80,$67,$06,$70,$FF,$60,$00,$01,$C8,$20,$6D,$CF,$8E
	dc.b $20,$AE,$00,$08,$76,$01,$4A,$B8,$03,$16,$67,$2C,$70,$01,$C0,$B8
	dc.b $03,$16,$66,$24,$20,$78,$03,$16,$0C,$90,$4D,$50,$47,$4D,$66,$18
	dc.b $20,$78,$03,$16,$4A,$A8,$00,$04,$67,$0E,$20,$78,$03,$16,$20,$68
	dc.b $00,$04,$4A,$50,$67,$02,$76,$00,$48,$83,$48,$C3,$2B,$43,$CF,$74
	dc.b $67,$60,$41,$ED,$D0,$48,$43,$F8,$09,$10,$70,$07,$20,$D9,$51,$C8
	dc.b $FF,$FC,$30,$D9,$41,$ED,$D0,$48,$22,$6D,$CF,$7E,$22,$88,$4A,$87
	dc.b $66,$0E,$59,$8F,$20,$6D,$CF,$7E,$2F,$10,$4E,$BA,$08,$9C,$58,$4F
	dc.b $20,$0B,$67,$04,$70,$01,$26,$80,$4A,$AE,$00,$10,$67,$08,$20,$6E
	dc.b $00,$10,$20,$AD,$CF,$7E,$4A,$AE,$00,$14,$67,$08,$20,$6E,$00,$14
	dc.b $20,$AD,$CF,$82,$4E,$BA,$FD,$8A,$70,$01,$2B,$40,$CF,$74,$60,$00
	dc.b $01,$22,$20,$78,$03,$16,$20,$68,$00,$04,$30,$2D,$CF,$78,$B0,$50
	dc.b $67,$0C,$2F,$3C,$80,$00,$00,$00,$4E,$BA,$01,$3C,$58,$4F,$41,$ED
	dc.b $CF,$78,$22,$78,$03,$16,$22,$69,$00,$04,$23,$48,$00,$24,$20,$78
	dc.b $03,$16,$2B,$68,$00,$04,$CF,$9C,$20,$78,$03,$16,$20,$68,$00,$04
	dc.b $2B,$68,$00,$02,$CF,$7A,$20,$78,$03,$16,$20,$68,$00,$04,$2B,$68
	dc.b $00,$06,$CF,$7E,$20,$78,$03,$16,$20,$68,$00,$04,$2B,$68,$00,$0A
	dc.b $CF,$82,$4A,$87,$67,$2C,$28,$6D,$CF,$7E,$60,$0C,$59,$8F,$2F,$14
	dc.b $4E,$BA,$07,$C0,$58,$4F,$58,$4C,$4A,$94,$66,$F0,$28,$6D,$CF,$82
	dc.b $60,$0C,$59,$8F,$2F,$14,$4E,$BA,$07,$AA,$58,$4F,$58,$4C,$4A,$94
	dc.b $66,$F0,$20,$0B,$67,$04,$26,$AD,$CF,$7A,$4A,$AE,$00,$10,$67,$08
	dc.b $20,$6E,$00,$10,$20,$AD,$CF,$7E,$4A,$AE,$00,$14,$67,$08,$20,$6E
	dc.b $00,$14,$20,$AD,$CF,$82,$20,$78,$03,$16,$20,$68,$00,$04,$4A,$A8
	dc.b $00,$20,$67,$54,$70,$78,$A1,$1E,$2B,$48,$CF,$98,$66,$0A,$70,$02
	dc.b $2F,$00,$4E,$BA,$00,$82,$58,$4F,$20,$78,$03,$16,$20,$68,$00,$04
	dc.b $26,$68,$00,$20,$7E,$00,$76,$05,$22,$07,$20,$01,$C2,$FC,$00,$18
	dc.b $48,$40,$C0,$FC,$00,$18,$48,$40,$42,$40,$D2,$80,$2C,$01,$20,$6D
	dc.b $CF,$98,$43,$F3,$68,$00,$45,$F0,$68,$00,$70,$05,$24,$D9,$51,$C8
	dc.b $FF,$FC,$52,$87,$B6,$87,$6E,$D0,$4E,$BA,$FC,$66,$70,$00,$2B,$40
	dc.b $CF,$74,$4C,$EE,$1C,$C8,$FF,$E8,$4E,$5E,$4E,$75,$87,$5F,$52,$54
	dc.b $49,$6E,$69,$74,$00,$00,$4E,$56,$00,$00,$20,$3C,$00,$FF,$FF,$FF
	dc.b $C0,$AE,$00,$08,$2F,$00,$4E,$BA,$00,$0E,$4E,$5E,$4E,$75,$84,$65
	dc.b $78,$69,$74,$00,$00,$00,$4E,$56,$00,$00,$2F,$0C,$20,$6D,$CF,$8E
	dc.b $49,$E8,$00,$8C,$60,$0A,$4A,$94,$67,$04,$20,$54,$4E,$90,$59,$4C
	dc.b $20,$6D,$CF,$8E,$B1,$CC,$65,$EE,$4A,$AD,$CF,$9C,$67,$0A,$20,$6D
	dc.b $CF,$9C,$21,$6E,$00,$08,$00,$0E,$4A,$AD,$D0,$82,$66,$0A,$20,$6D
	dc.b $CF,$8E,$22,$50,$4E,$91,$60,$0E,$70,$01,$2F,$00,$48,$6D,$D0,$6A
	dc.b $4E,$BA,$FA,$1A,$50,$4F,$28,$6E,$FF,$FC,$4E,$5E,$4E,$75,$87,$5F
	dc.b $52,$54,$45,$78,$69,$74,$00,$00,$22,$5F,$20,$1F,$A1,$1E,$2E,$88
	dc.b $4E,$D1,$22,$5F,$20,$5F,$A0,$21,$2E,$80,$6A,$02,$42,$97,$4E,$D1
	dc.b $22,$5F,$20,$1F,$20,$5F,$A0,$20,$4E,$D1,$22,$5F,$20,$5F,$A0,$25
	dc.b $2E,$80,$6A,$02,$42,$97,$4E,$D1,$22,$5F,$12,$1F,$30,$1F,$4A,$01
	dc.b $67,$04,$A7,$46,$60,$02,$A3,$46,$2E,$88,$4E,$D1,$22,$5F,$20,$5F
	dc.b $20,$38,$02,$0C,$A9,$C6,$4E,$D1,$20,$6F,$00,$0C,$22,$6F,$00,$08
	dc.b $70,$00,$10,$18,$48,$40,$10,$19,$4A,$2F,$00,$04,$67,$0E,$4A,$2F
	dc.b $00,$06,$67,$04,$A4,$3C,$60,$10,$A0,$3C,$60,$0C,$4A,$2F,$00,$06
	dc.b $67,$04,$A6,$3C,$60,$02,$A2,$3C,$0A,$00,$00,$01,$1F,$40,$00,$10
	dc.b $20,$5F,$4F,$EF,$00,$0C,$4E,$D0,$22,$5F,$10,$1F,$20,$5F,$66,$04
	dc.b $A0,$01,$60,$02,$A4,$01,$3E,$80,$4E,$D1,$22,$5F,$10,$1F,$20,$5F
	dc.b $66,$04,$A0,$0C,$60,$02,$A4,$0C,$3E,$80,$4E,$D1,$22,$5F,$10,$1F
	dc.b $20,$5F,$66,$04,$A0,$12,$60,$02,$A4,$12,$3E,$80,$4E,$D1,$4E,$56
	dc.b $FF,$CE,$20,$4F,$31,$6E,$00,$08,$00,$18,$A0,$01,$3D,$40,$00,$0A
	dc.b $4E,$5E,$20,$5F,$54,$8F,$4E,$D0,$51,$C1,$60,$02,$50,$C1,$4E,$56
	dc.b $FF,$CE,$20,$4F,$21,$6E,$00,$08,$00,$20,$31,$6E,$00,$10,$00,$18
	dc.b $22,$6E,$00,$0C,$21,$51,$00,$24,$42,$68,$00,$2C,$42,$A8,$00,$2E
	dc.b $4A,$01,$66,$04,$A0,$02,$60,$02,$A0,$03,$3D,$40,$00,$12,$22,$6E
	dc.b $00,$0C,$22,$A8,$00,$28,$4E,$5E,$22,$5F,$4F,$EF,$00,$0A,$4E,$D1
	dc.b $4E,$56,$FF,$B0,$20,$4F,$21,$6E,$00,$0E,$00,$12,$31,$6E,$00,$0C
	dc.b $00,$16,$42,$28,$00,$1A,$42,$68,$00,$1C,$A0,$0C,$3D,$40,$00,$12
	dc.b $41,$E8,$00,$20,$22,$6E,$00,$08,$70,$10,$A0,$2E,$4E,$5E,$22,$5F
	dc.b $4F,$EF,$00,$0A,$4E,$D1,$4E,$56,$FF,$CE,$20,$4F,$21,$6E,$00,$0A
	dc.b $00,$12,$31,$6E,$00,$08,$00,$16,$42,$28,$00,$1A,$A0,$09,$3D,$40
	dc.b $00,$0E,$4E,$5E,$22,$5F,$5C,$8F,$4E,$D1,$4E,$56,$FF,$CE,$20,$4F
	dc.b $21,$6E,$00,$0E,$00,$12,$31,$6E,$00,$0C,$00,$16,$42,$28,$00,$1A
	dc.b $21,$6E,$00,$08,$00,$1C,$A0,$0B,$3D,$40,$00,$12,$4E,$5E,$22,$5F
	dc.b $4F,$EF,$00,$0A,$4E,$D1,$4E,$56,$FF,$B0,$20,$4F,$21,$6E,$00,$0E
	dc.b $00,$12,$31,$6E,$00,$0C,$00,$16,$42,$28,$00,$1A,$42,$68,$00,$1C
	dc.b $A0,$0C,$43,$E8,$00,$20,$20,$6E,$00,$08,$70,$10,$A0,$2E,$20,$4F
	dc.b $A0,$0D,$3D,$40,$00,$12,$4E,$5E,$22,$5F,$4F,$EF,$00,$0A,$4E,$D1
	dc.b $4E,$56,$FF,$CE,$20,$4F,$31,$6E,$00,$0C,$00,$18,$21,$6E,$00,$08
	dc.b $00,$1C,$A0,$12,$3D,$40,$00,$0E,$4E,$5E,$22,$5F,$5C,$8F,$4E,$D1
	dc.b $4E,$56,$FF,$CE,$20,$4F,$31,$6E,$00,$0C,$00,$18,$A0,$18,$3D,$40
	dc.b $00,$0E,$22,$6E,$00,$08,$22,$A8,$00,$2E,$4E,$5E,$22,$5F,$5C,$8F
	dc.b $4E,$D1,$4E,$56,$FF,$CE,$20,$4F,$31,$6E,$00,$0E,$00,$18,$31,$6E
	dc.b $00,$0C,$00,$2C,$21,$6E,$00,$08,$00,$2E,$A0,$44,$3D,$40,$00,$10
	dc.b $4E,$5E,$22,$5F,$50,$8F,$4E,$D1,$22,$5F,$10,$1F,$20,$5F,$66,$04
	dc.b $A2,$14,$60,$02,$A6,$14,$3E,$80,$4E,$D1,$22,$5F,$10,$1F,$20,$5F
	dc.b $66,$06,$70,$08,$A2,$60,$60,$04,$70,$08,$A6,$60,$3E,$80,$4E,$D1
	dc.b $22,$5F,$10,$1F,$20,$5F,$66,$06,$70,$09,$A2,$60,$60,$04,$70,$09
	dc.b $A6,$60,$3E,$80,$4E,$D1,$22,$5F,$10,$1F,$20,$5F,$66,$04,$A2,$00
	dc.b $60,$02,$A6,$00,$3E,$80,$4E,$D1,$22,$5F,$10,$1F,$20,$5F,$66,$04
	dc.b $A2,$0A,$60,$02,$A6,$0A,$3E,$80,$4E,$D1,$22,$5F,$10,$1F,$20,$5F
	dc.b $66,$04,$A2,$08,$60,$02,$A6,$08,$3E,$80,$4E,$D1,$22,$5F,$10,$1F
	dc.b $20,$5F,$66,$04,$A2,$09,$60,$02,$A6,$09,$3E,$80,$4E,$D1,$22,$5F
	dc.b $10,$1F,$20,$5F,$66,$04,$A2,$0C,$60,$02,$A6,$0C,$3E,$80,$4E,$D1
	dc.b $22,$5F,$10,$1F,$20,$5F,$66,$04,$A2,$0D,$60,$02,$A6,$0D,$3E,$80
	dc.b $4E,$D1,$4E,$56,$FF,$CC,$2F,$07,$2D,$6E,$00,$10,$FF,$DE,$55,$8F
	dc.b $48,$6E,$FF,$CC,$70,$00,$1F,$00,$4E,$BA,$FF,$3E,$3E,$1F,$20,$6E
	dc.b $00,$0C,$30,$AE,$FF,$E2,$20,$6E,$00,$08,$20,$AE,$FF,$FC,$3D,$47
	dc.b $00,$14,$2E,$2E,$FF,$C8,$4E,$5E,$20,$5F,$4F,$EF,$00,$0C,$4E,$D0
	dc.b $87,$48,$47,$45,$54,$56,$4F,$4C,$00,$00,$4E,$56,$FF,$86,$3D,$6E
	dc.b $00,$10,$FF,$9C,$2D,$6E,$00,$0C,$FF,$B6,$2D,$6E,$00,$08,$FF,$98
	dc.b $42,$2E,$FF,$A0,$55,$8F,$48,$6E,$FF,$86,$70,$00,$1F,$00,$4E,$BA
	dc.b $FF,$5C,$3D,$5F,$00,$12,$4E,$5E,$20,$5F,$4F,$EF,$00,$0A,$4E,$D0
	dc.b $87,$48,$44,$45,$4C,$45,$54,$45,$00,$00,$4E,$56,$FF,$86,$2F,$07
	dc.b $3D,$6E,$00,$14,$FF,$9C,$2D,$6E,$00,$10,$FF,$B6,$2D,$6E,$00,$0C
	dc.b $FF,$98,$42,$2E,$FF,$A0,$42,$6E,$FF,$A2,$55,$8F,$48,$6E,$FF,$86
	dc.b $70,$00,$1F,$00,$4E,$BA,$FF,$28,$3E,$1F,$20,$6E,$00,$08,$43,$EE
	dc.b $FF,$A6,$20,$D9,$20,$D9,$20,$D9,$20,$D9,$3D,$47,$00,$16,$2E,$2E
	dc.b $FF,$82,$4E,$5E,$20,$5F,$4F,$EF,$00,$0E,$4E,$D0,$89,$48,$47,$45
	dc.b $54,$46,$49,$4E,$46,$4F,$00,$00,$4E,$56,$FF,$86,$48,$E7,$03,$00
	dc.b $2C,$2E,$00,$10,$3D,$6E,$00,$14,$FF,$9C,$2D,$46,$FF,$B6,$2D,$6E
	dc.b $00,$0C,$FF,$98,$42,$2E,$FF,$A0,$42,$6E,$FF,$A2,$55,$8F,$48,$6E
	dc.b $FF,$86,$70,$00,$1F,$00,$4E,$BA,$FE,$C6,$3E,$1F,$66,$24,$20,$6E
	dc.b $00,$08,$43,$EE,$FF,$A6,$22,$D8,$22,$D8,$22,$D8,$22,$D8,$2D,$46
	dc.b $FF,$B6,$55,$8F,$48,$6E,$FF,$86,$70,$00,$1F,$00,$4E,$BA,$FE,$B2
	dc.b $3E,$1F,$3D,$47,$00,$16,$4C,$EE,$00,$C0,$FF,$7E,$4E,$5E,$20,$5F
	dc.b $4F,$EF,$00,$0E,$4E,$D0,$89,$48,$53,$45,$54,$46,$49,$4E,$46,$4F
	dc.b $00,$00,$4E,$56,$00,$00,$20,$3C,$00,$00,$A8,$9F,$A7,$46,$2F,$08
	dc.b $20,$3C,$00,$00,$A0,$AD,$A3,$46,$B1,$DF,$67,$0E,$20,$2E,$00,$0C
	dc.b $A1,$AD,$22,$6E,$00,$08,$22,$88,$60,$26,$41,$FA,$00,$36,$30,$3C
	dc.b $EA,$51,$22,$2E,$00,$0C,$B2,$98,$67,$06,$4A,$98,$67,$12,$60,$F6
	dc.b $43,$FA,$00,$20,$D3,$D0,$4E,$D1,$22,$6E,$00,$08,$22,$80,$42,$40
	dc.b $3D,$40,$00,$10,$4E,$5E,$20,$5F,$50,$8F,$4E,$D0,$30,$3C,$EA,$52
	dc.b $60,$EE,$76,$65,$72,$73,$00,$00,$00,$60,$6D,$61,$63,$68,$00,$00
	dc.b $00,$64,$73,$79,$73,$76,$00,$00,$00,$88,$70,$72,$6F,$63,$00,$00
	dc.b $00,$92,$66,$70,$75,$20,$00,$00,$00,$9E,$71,$64,$20,$20,$00,$00
	dc.b $00,$E8,$6B,$62,$64,$20,$00,$00,$01,$1A,$61,$74,$6C,$6B,$00,$00
	dc.b $01,$42,$6D,$6D,$75,$20,$00,$00,$01,$64,$72,$61,$6D,$20,$00,$00
	dc.b $01,$88,$6C,$72,$61,$6D,$00,$00,$01,$88
	dcb.b $8,$00
	dc.b $70,$01,$60,$82,$22,$78,$02,$AE,$70,$04,$0C,$69,$00,$75,$00,$08
	dc.b $67,$12,$0C,$69,$02,$76,$00,$08,$66,$04,$52,$40,$60,$06,$10,$38
	dc.b $0C,$B3,$5C,$80,$60,$00,$FF,$60,$70,$00,$30,$38,$01,$5A,$60,$00
	dc.b $FF,$56,$70,$00,$10,$38,$01,$2F,$52,$40,$60,$00,$FF,$4A,$0C,$38
	dc.b $00,$04,$01,$2F,$67,$38,$08,$38,$00,$04,$0B,$22,$67,$34,$20,$4F
	dc.b $F2,$80,$00,$00,$F3,$27,$30,$17,$2E,$48,$0C,$40,$1F,$18,$67,$16
	dc.b $0C,$40,$3F,$18,$67,$10,$0C,$40,$3F,$38,$67,$0E,$0C,$40,$1F,$38
	dc.b $67,$08,$70,$00,$60,$0E,$70,$01,$60,$0A,$70,$02,$60,$06,$70,$03
	dc.b $60,$02,$70,$00,$60,$00,$FF,$00,$0C,$78,$3F,$FF,$02,$8E,$6E,$1C
	dc.b $30,$3C,$A8,$9F,$A7,$46,$24,$08,$20,$3C,$00,$00,$AB,$03,$A7,$46
	dc.b $20,$3C,$00,$00,$01,$00,$B4,$88,$66,$06,$60,$0A,$70,$00,$60,$06
	dc.b $20,$3C,$00,$00,$02,$00,$60,$00,$FE,$CE,$10,$38,$02,$1E,$41,$FA
	dc.b $00,$16,$22,$48,$12,$18,$67,$00,$FE,$D2,$B2,$00,$66,$F6,$91,$C9
	dc.b $20,$08,$60,$00,$FE,$B2,$03,$13,$0B,$02,$01,$06,$07,$04,$05,$08
	dc.b $09,$00,$70,$00,$4A,$38,$02,$91,$6B,$16,$12,$38,$01,$FB,$02,$01
	dc.b $00,$0F,$0C,$01,$00,$01,$66,$08,$20,$78,$02,$DC,$10,$28,$00,$07
	dc.b $60,$00,$FE,$84,$0C,$38,$00,$02,$01,$2F,$6D,$16,$70,$00,$10,$38
	dc.b $0C,$B1,$0C,$00,$00,$01,$67,$0C,$0C,$00,$00,$03,$6D,$04,$53,$40
	dc.b $60,$02,$70,$00,$60,$00,$FE,$60,$30,$3C,$A8,$9F,$A7,$46,$24,$08
	dc.b $20,$3C,$00,$00,$A8,$8F,$A7,$46,$20,$38,$01,$08,$B4,$88,$67,$0A
	dc.b $59,$8F,$3F,$3C,$00,$16,$A8,$8F,$20,$1F,$60,$00,$FE,$3A,$20,$6F
	dc.b $00,$04,$20,$2F,$00,$08,$42,$67,$A9,$EE,$20,$5F,$50,$4F,$4E,$D0
	dc.b $20,$2F,$00,$04,$2F,$40,$00,$08,$67,$26,$20,$40,$22,$48,$10,$19
	dc.b $67,$1E,$12,$11,$12,$C0,$10,$01,$66,$F8,$93,$C8,$20,$09,$53,$40
	dc.b $0C,$80,$00,$00,$00,$FF,$6F,$06,$20,$3C,$00,$00,$00,$FF,$10,$80
	dc.b $22,$5F,$58,$4F,$4E,$D1,$22,$5F,$20,$1F,$2E,$80,$67,$12,$20,$40
	dc.b $70,$00,$10,$10,$60,$04,$10,$E8,$00,$01,$51,$C8,$FF,$FA,$42,$10
	dc.b $4E,$D1,$22,$1F,$20,$17,$2E,$81,$2F,$0B,$3F,$03,$4A,$80,$66,$00
	dc.b $00,$80,$42,$38,$0A,$5E,$59,$4F,$2F,$3C,$61,$63,$75,$72,$42,$67
	dc.b $A9,$A0,$20,$1F,$67,$12,$26,$40,$42,$43,$55,$4F,$A9,$94,$55,$4F
	dc.b $2F,$0B,$A9,$A4,$BF,$4F,$67,$3C,$59,$4F,$2F,$3C,$61,$63,$75,$72
	dc.b $3F,$3C,$00,$01,$A9,$A0,$20,$1F,$67,$0A,$50,$F8,$0A,$5E,$2B,$40
	dc.b $D0,$A6,$60,$74,$59,$4F,$2F,$3C,$61,$63,$75,$72,$3F,$3C,$00,$02
	dc.b $A9,$A0,$20,$1F,$67,$08,$26,$40,$36,$3C,$00,$02,$60,$06,$50,$F8
	dc.b $0A,$5E,$60,$54,$50,$F8,$0A,$5E,$22,$13,$67,$04,$2F,$0B,$A9,$A3
	dc.b $59,$4F,$2F,$3C,$61,$63,$75,$72,$3F,$03,$A9,$A0,$20,$1F,$67,$38
	dc.b $2B,$40,$D0,$A6,$20,$40,$A0,$29,$26,$6D,$D0,$A6,$26,$53,$36,$13
	dc.b $6F,$26,$30,$03,$D0,$40,$D0,$40,$36,$C0,$58,$40,$36,$C0,$53,$43
	dc.b $59,$4F,$2F,$3C,$43,$55,$52,$53,$3F,$13,$A9,$A0,$26,$DF,$57,$CB
	dc.b $FF,$F0,$66,$04,$42,$AD,$D0,$A6,$36,$1F,$26,$5F,$4E,$75,$20,$5F
	dc.b $24,$1F,$6A,$0C,$02,$42,$00,$1F,$66,$04,$72,$FC,$60,$0A,$4E,$D0
	dc.b $02,$42,$00,$1F,$66,$F8,$72,$04,$2F,$08,$20,$2D,$D0,$A6,$66,$10
	dc.b $3F,$01,$42,$A7,$4E,$BA,$FF,$0C,$32,$1F,$20,$2D,$D0,$A6,$67,$22
	dc.b $22,$40,$22,$51,$34,$29,$00,$02,$D4,$41,$66,$04,$34,$11,$60,$06
	dc.b $B4,$51,$6F,$02,$74,$04,$33,$42,$00,$02,$22,$71,$20,$00,$2F,$11
	dc.b $A8,$51,$4E,$75,$24,$2D,$D0,$AA,$20,$5F,$30,$1F,$48,$C0,$6E,$04
	dc.b $6D,$0C,$74,$00,$D4,$80,$2B,$42,$D0,$AA,$4E,$FA,$FF,$A4,$D4,$80
	dc.b $2B,$42,$D0,$AA,$4E,$FA,$FF,$8E,$20,$5F,$42,$40,$10,$1F,$2F,$08
	dc.b $4A,$00,$67,$1A,$0C,$40,$00,$05,$66,$08,$22,$55,$48,$69,$FF,$94
	dc.b $60,$0A,$59,$4F,$3F,$00,$A9,$B9,$22,$57,$2E,$91,$A8,$51,$A8,$53
	dc.b $4E,$75,$4E,$75,$22,$6F,$00,$04,$48,$78,$00,$01,$48,$6D,$D0,$A2
	dc.b $48,$6D,$D2,$C0,$48,$6D,$D2,$BC,$2F,$09,$4E,$BA,$F5,$30,$72,$FF
	dc.b $B0,$41,$67,$18,$4F,$EF,$00,$14,$48,$6D,$D0,$6A,$4E,$BA,$F1,$90
	dc.b $58,$4F,$4A,$80,$66,$10,$4E,$AD,$0A,$32,$4E,$75,$48,$7A,$00,$0C
	dc.b $30,$3C,$FE,$15,$A9,$C9,$58,$4F,$4E,$75,$1B,$44,$61,$74,$61,$20
	dc.b $69,$6E,$69,$74,$69,$61,$6C,$69,$7A,$61,$74,$69,$6F,$6E,$20,$66
	dc.b $61,$69,$6C,$65,$64,$21,$42,$A7,$4E,$BA,$F6,$DA,$42,$A7,$4E,$BA
	dc.b $F6,$D4
