; Memory map
;   code[$00000000-$00000DDC] -> runtime[$00012F80-$00013D5C] policy materialized
;   Absolute memory refs:
;     absolute[$00000380] refs=1 access=a
;     absolute[$00002558] refs=1 access=a
;     absolute[$00002734] refs=1 access=a
;     absolute[$000034AA] refs=1 access=a
;     absolute[$000034DC] refs=1 access=a
;     absolute[$0000D7AA] refs=1 access=a
;     absolute[$0000D7D8] refs=1 access=a

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

    RSSET 0
    RS.B 104
selected_novella_record_pointer RS.L 1
    RS.B 372
novella_attempts_remaining RS.W 1
    RS.B 35
novella_expected_char_latch RS.B 1
novella_answer_tail_latch RS.B 1
app_SIZEOF EQU __RS

; STRUCT SG2NovellaWordRecord
    RSRESET
SG2NovellaWordRecord_page RS.B 1
SG2NovellaWordRecord_paragraph RS.B 1
SG2NovellaWordRecord_word RS.B 1
SG2NovellaWordRecord_answer_and_fill RS.B 13
SG2NovellaWordRecord_SIZEOF EQU __RS

    SECTION code,code
novella_word_records:
    ORG $12F80
abs_0_00012F80:
	dc.b $05	; page
	dc.b $02	; paragraph
	dc.b $01	; word
	dc.b $48,$45,$41,$44,$53,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0B	; page
	dc.b $06	; paragraph
	dc.b $01	; word
	dc.b $41,$00	; answer_and_fill
	dcb.b $B,$20
	dc.b $05	; page
	dc.b $05	; paragraph
	dc.b $07	; word
	dc.b $42,$4C,$4F,$57,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $05	; page
	dc.b $07	; paragraph
	dc.b $01	; word
	dc.b $48,$45,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $05	; page
	dc.b $09	; paragraph
	dc.b $05	; word
	dc.b $50,$4C,$55,$4E,$47,$45,$52,$53,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $06	; page
	dc.b $04	; paragraph
	dc.b $02	; word
	dc.b $49,$4D,$50,$45,$52,$49,$41,$4C,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $06	; page
	dc.b $04	; paragraph
	dc.b $0D	; word
	dc.b $54,$48,$52,$4F,$41,$54,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $06	; page
	dc.b $05	; paragraph
	dc.b $0D	; word
	dc.b $53,$50,$41,$57,$4E,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $06	; page
	dc.b $06	; paragraph
	dc.b $03	; word
	dc.b $54,$56,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $06	; page
	dc.b $07	; paragraph
	dc.b $09	; word
	dc.b $43,$4F,$4C,$4F,$53,$53,$41,$4C,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $06	; page
	dc.b $0C	; paragraph
	dc.b $0C	; word
	dc.b $47,$52,$4F,$50,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $07	; page
	dc.b $03	; paragraph
	dc.b $0A	; word
	dc.b $43,$48,$41,$49,$4E,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $07	; page
	dc.b $03	; paragraph
	dc.b $0D	; word
	dc.b $42,$45,$44,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $07	; page
	dc.b $0A	; paragraph
	dc.b $0D	; word
	dc.b $53,$48,$52,$49,$56,$45,$4C,$4C,$45,$44,$00,$20,$20	; answer_and_fill
	dc.b $08	; page
	dc.b $01	; paragraph
	dc.b $07	; word
	dc.b $43,$55,$4E,$4E,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $08	; page
	dc.b $04	; paragraph
	dc.b $08	; word
	dc.b $4C,$49,$46,$45,$46,$4F,$52,$4D,$53,$00,$20,$20,$20	; answer_and_fill
	dc.b $08	; page
	dc.b $07	; paragraph
	dc.b $04	; word
	dc.b $53,$50,$52,$45,$41,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $09	; page
	dc.b $01	; paragraph
	dc.b $01	; word
	dc.b $43,$4F,$4E,$54,$52,$41,$43,$54,$4F,$52,$53,$00,$20	; answer_and_fill
	dc.b $09	; page
	dc.b $03	; paragraph
	dc.b $07	; word
	dc.b $50,$52,$45,$53,$53,$49,$4E,$47,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $09	; page
	dc.b $06	; paragraph
	dc.b $08	; word
	dc.b $42,$55,$4C,$4C,$4E,$45,$43,$4B,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $09	; page
	dc.b $09	; paragraph
	dc.b $0E	; word
	dc.b $42,$41,$4C,$4C,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $0A	; page
	dc.b $01	; paragraph
	dc.b $02	; word
	dc.b $45,$4E,$54,$52,$59,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0A	; page
	dc.b $04	; paragraph
	dc.b $03	; word
	dc.b $44,$52,$4F,$47,$55,$45,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0A	; page
	dc.b $04	; paragraph
	dc.b $06	; word
	dc.b $50,$4C,$55,$43,$4B,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0A	; page
	dc.b $06	; paragraph
	dc.b $01	; word
	dc.b $53,$48,$45,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $0A	; page
	dc.b $06	; paragraph
	dc.b $0F	; word
	dc.b $4B,$4E,$4F,$54,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $0B	; page
	dc.b $03	; paragraph
	dc.b $03	; word
	dc.b $42,$4C,$45,$45,$50,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0B	; page
	dc.b $05	; paragraph
	dc.b $08	; word
	dc.b $48,$45,$4C,$4D,$45,$54,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0B	; page
	dc.b $07	; paragraph
	dc.b $03	; word
	dc.b $53,$54,$4F,$4F,$44,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $01	; paragraph
	dc.b $09	; word
	dc.b $53,$4F,$4C,$49,$43,$45,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $02	; paragraph
	dc.b $03	; word
	dc.b $41,$50,$4F,$47,$45,$41,$4E,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $04	; paragraph
	dc.b $05	; word
	dc.b $53,$41,$56,$41,$47,$45,$4C,$59,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $07	; paragraph
	dc.b $03	; word
	dc.b $50,$41,$49,$4E,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $08	; paragraph
	dc.b $0A	; word
	dc.b $48,$41,$4E,$44,$53,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $09	; paragraph
	dc.b $0A	; word
	dc.b $44,$45,$56,$41,$53,$54,$41,$54,$49,$4E,$47,$00,$20	; answer_and_fill
	dc.b $0C	; page
	dc.b $0A	; paragraph
	dc.b $0B	; word
	dc.b $47,$41,$52,$52,$49,$53,$4F,$4E,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $0D	; page
	dc.b $01	; paragraph
	dc.b $02	; word
	dc.b $54,$52,$41,$4E,$53,$50,$4F,$52,$54,$00,$20,$20,$20	; answer_and_fill
	dc.b $0D	; page
	dc.b $01	; paragraph
	dc.b $0A	; word
	dc.b $52,$45,$53,$49,$53,$54,$41,$4E,$43,$45,$00,$20,$20	; answer_and_fill
	dc.b $0D	; page
	dc.b $0A	; paragraph
	dc.b $09	; word
	dc.b $48,$41,$52,$44,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $0D	; page
	dc.b $0B	; paragraph
	dc.b $05	; word
	dc.b $50,$52,$4F,$42,$45,$53,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0D	; page
	dc.b $0B	; paragraph
	dc.b $06	; word
	dc.b $42,$45,$41,$52,$53,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $01	; paragraph
	dc.b $01	; word
	dc.b $4E,$4F,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $0E	; page
	dc.b $02	; paragraph
	dc.b $07	; word
	dc.b $48,$4F,$4C,$4F,$47,$52,$41,$4D,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $03	; paragraph
	dc.b $05	; word
	dc.b $50,$49,$43,$54,$55,$52,$45,$53,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $05	; paragraph
	dc.b $05	; word
	dc.b $42,$52,$4F,$41,$44,$45,$4E,$45,$44,$00,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $06	; paragraph
	dc.b $05	; word
	dc.b $50,$52,$49,$43,$4B,$4C,$45,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $07	; paragraph
	dc.b $04	; word
	dc.b $4D,$41,$47,$4E,$45,$54,$53,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $07	; paragraph
	dc.b $06	; word
	dc.b $51,$55,$45,$45,$52,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0E	; page
	dc.b $09	; paragraph
	dc.b $05	; word
	dc.b $42,$41,$4E,$47,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $0F	; page
	dc.b $02	; paragraph
	dc.b $07	; word
	dc.b $42,$45,$41,$52,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0F	; page
	dc.b $03	; paragraph
	dc.b $07	; word
	dc.b $4D,$4F,$55,$54,$48,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0F	; page
	dc.b $06	; paragraph
	dc.b $11	; word
	dc.b $4C,$4F,$4F,$4E,$45,$59,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $0F	; page
	dc.b $07	; paragraph
	dc.b $0C	; word
	dc.b $41,$52,$4F,$55,$53,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $10	; page
	dc.b $01	; paragraph
	dc.b $09	; word
	dc.b $42,$4C,$4F,$57,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $10	; page
	dc.b $02	; paragraph
	dc.b $0D	; word
	dc.b $4D,$45,$4D,$42,$45,$52,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $10	; page
	dc.b $04	; paragraph
	dc.b $0F	; word
	dc.b $46,$49,$53,$54,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $10	; page
	dc.b $05	; paragraph
	dc.b $0C	; word
	dc.b $43,$48,$41,$49,$52,$4D,$41,$4E,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $10	; page
	dc.b $0B	; paragraph
	dc.b $07	; word
	dc.b $52,$41,$49,$53,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $11	; page
	dc.b $03	; paragraph
	dc.b $12	; word
	dc.b $48,$41,$52,$44,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $11	; page
	dc.b $04	; paragraph
	dc.b $0E	; word
	dc.b $43,$4F,$4D,$49,$4E,$47,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $11	; page
	dc.b $06	; paragraph
	dc.b $06	; word
	dc.b $50,$55,$53,$48,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $11	; page
	dc.b $06	; paragraph
	dc.b $08	; word
	dc.b $47,$49,$52,$4C,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $11	; page
	dc.b $0E	; paragraph
	dc.b $0E	; word
	dc.b $46,$49,$4E,$47,$45,$52,$45,$44,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $12	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $44,$52,$41,$47,$47,$4F,$4E,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $12	; page
	dc.b $04	; paragraph
	dc.b $0E	; word
	dc.b $49,$43,$41,$52,$55,$53,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $12	; page
	dc.b $05	; paragraph
	dc.b $0B	; word
	dc.b $46,$49,$4E,$47,$45,$52,$49,$4E,$47,$00,$20,$20,$20	; answer_and_fill
	dc.b $12	; page
	dc.b $06	; paragraph
	dc.b $04	; word
	dc.b $50,$4C,$45,$41,$53,$55,$52,$45,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $12	; page
	dc.b $0B	; paragraph
	dc.b $05	; word
	dc.b $53,$4C,$45,$45,$4B,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $13	; page
	dc.b $01	; paragraph
	dc.b $06	; word
	dc.b $49,$4E,$43,$4C,$55,$44,$45,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $13	; page
	dc.b $04	; paragraph
	dc.b $04	; word
	dc.b $53,$4B,$49,$4C,$4C,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $13	; page
	dc.b $08	; paragraph
	dc.b $07	; word
	dc.b $54,$45,$53,$54,$49,$4C,$59,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $14	; page
	dc.b $02	; paragraph
	dc.b $03	; word
	dc.b $57,$4F,$52,$53,$45,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $14	; page
	dc.b $04	; paragraph
	dc.b $0D	; word
	dc.b $48,$41,$4D,$4D,$45,$52,$48,$45,$41,$44,$00,$20,$20	; answer_and_fill
	dc.b $14	; page
	dc.b $04	; paragraph
	dc.b $01	; word
	dc.b $4B,$41,$54,$52,$41,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $14	; page
	dc.b $07	; paragraph
	dc.b $04	; word
	dc.b $54,$52,$49,$50,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $15	; page
	dc.b $02	; paragraph
	dc.b $03	; word
	dc.b $54,$57,$45,$4E,$54,$59,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $15	; page
	dc.b $05	; paragraph
	dc.b $02	; word
	dc.b $50,$49,$47,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $15	; page
	dc.b $07	; paragraph
	dc.b $06	; word
	dc.b $49,$4E,$54,$49,$4D,$49,$44,$41,$54,$45,$00,$20,$20	; answer_and_fill
	dc.b $16	; page
	dc.b $01	; paragraph
	dc.b $01	; word
	dc.b $4F,$4E,$45,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $16	; page
	dc.b $02	; paragraph
	dc.b $03	; word
	dc.b $53,$49,$4E,$43,$45,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $16	; page
	dc.b $02	; paragraph
	dc.b $06	; word
	dc.b $48,$41,$52,$44,$43,$4F,$50,$59,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $16	; page
	dc.b $06	; paragraph
	dc.b $08	; word
	dc.b $46,$4F,$55,$52,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $16	; page
	dc.b $09	; paragraph
	dc.b $08	; word
	dc.b $52,$49,$50,$50,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $17	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $4D,$49,$4E,$55,$54,$45,$53,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $17	; page
	dc.b $03	; paragraph
	dc.b $02	; word
	dc.b $53,$4F,$55,$56,$45,$4E,$49,$52,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $17	; page
	dc.b $05	; paragraph
	dc.b $0D	; word
	dc.b $57,$48,$49,$4E,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $17	; page
	dc.b $0A	; paragraph
	dc.b $11	; word
	dc.b $54,$48,$55,$4D,$42,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $18	; page
	dc.b $01	; paragraph
	dc.b $01	; word
	dc.b $53,$49,$52,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $18	; page
	dc.b $05	; paragraph
	dc.b $0A	; word
	dc.b $49,$4D,$50,$45,$52,$49,$41,$4C,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $18	; page
	dc.b $0A	; paragraph
	dc.b $01	; word
	dc.b $4D,$4F,$56,$45,$4D,$45,$4E,$54,$53,$00,$20,$20,$20	; answer_and_fill
	dc.b $18	; page
	dc.b $0B	; paragraph
	dc.b $04	; word
	dc.b $41,$4E,$44,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $18	; page
	dc.b $0F	; paragraph
	dc.b $02	; word
	dc.b $45,$41,$53,$45,$44,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $19	; page
	dc.b $03	; paragraph
	dc.b $01	; word
	dc.b $53,$59,$53,$54,$45,$4D,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $19	; page
	dc.b $04	; paragraph
	dc.b $06	; word
	dc.b $44,$49,$56,$45,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $19	; page
	dc.b $05	; paragraph
	dc.b $03	; word
	dc.b $50,$4F,$50,$55,$4C,$41,$54,$45,$44,$00,$20,$20,$20	; answer_and_fill
	dc.b $19	; page
	dc.b $07	; paragraph
	dc.b $07	; word
	dc.b $53,$45,$4E,$53,$41,$54,$49,$4F,$4E,$53,$00,$20,$20	; answer_and_fill
	dc.b $1A	; page
	dc.b $01	; paragraph
	dc.b $05	; word
	dc.b $42,$55,$52,$53,$54,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1A	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $53,$4C,$4F,$57,$4C,$59,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1A	; page
	dc.b $06	; paragraph
	dc.b $02	; word
	dc.b $50,$4F,$57,$45,$52,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1A	; page
	dc.b $07	; paragraph
	dc.b $05	; word
	dc.b $50,$41,$44,$53,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $1B	; page
	dc.b $03	; paragraph
	dc.b $01	; word
	dc.b $4D,$49,$4E,$45,$52,$41,$4C,$53,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $1B	; page
	dc.b $09	; paragraph
	dc.b $01	; word
	dc.b $44,$41,$4E,$54,$45,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1B	; page
	dc.b $0A	; paragraph
	dc.b $06	; word
	dc.b $59,$41,$4E,$4B,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1B	; page
	dc.b $0B	; paragraph
	dc.b $0C	; word
	dc.b $42,$4C,$4F,$4F,$44,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1C	; page
	dc.b $02	; paragraph
	dc.b $06	; word
	dc.b $42,$55,$47,$47,$59,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1C	; page
	dc.b $04	; paragraph
	dc.b $02	; word
	dc.b $41,$55,$54,$48,$4F,$52,$49,$54,$59,$00,$20,$20,$20	; answer_and_fill
	dc.b $1C	; page
	dc.b $06	; paragraph
	dc.b $09	; word
	dc.b $4C,$4F,$56,$45,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $1C	; page
	dc.b $07	; paragraph
	dc.b $04	; word
	dc.b $42,$41,$54,$54,$4C,$45,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1D	; page
	dc.b $01	; paragraph
	dc.b $01	; word
	dc.b $57,$4F,$4F,$44,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $1D	; page
	dc.b $03	; paragraph
	dc.b $01	; word
	dc.b $46,$4F,$52,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $1D	; page
	dc.b $0C	; paragraph
	dc.b $07	; word
	dc.b $53,$54,$55,$4E,$54,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1D	; page
	dc.b $0C	; paragraph
	dc.b $0F	; word
	dc.b $42,$41,$4E,$4B,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1E	; page
	dc.b $01	; paragraph
	dc.b $02	; word
	dc.b $43,$48,$55,$43,$4B,$4C,$45,$44,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $1E	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $4E,$45,$58,$54,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $1E	; page
	dc.b $0A	; paragraph
	dc.b $0E	; word
	dc.b $43,$52,$45,$41,$4D,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1F	; page
	dc.b $01	; paragraph
	dc.b $02	; word
	dc.b $53,$4F,$55,$56,$45,$4E,$49,$52,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $1F	; page
	dc.b $05	; paragraph
	dc.b $03	; word
	dc.b $53,$4C,$55,$47,$47,$49,$53,$48,$4C,$59,$00,$20,$20	; answer_and_fill
	dc.b $1F	; page
	dc.b $05	; paragraph
	dc.b $06	; word
	dc.b $43,$4C,$4F,$59,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $1F	; page
	dc.b $09	; paragraph
	dc.b $02	; word
	dc.b $50,$45,$45,$4C,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $20	; page
	dc.b $01	; paragraph
	dc.b $02	; word
	dc.b $46,$52,$4F,$57,$4E,$45,$44,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $20	; page
	dc.b $02	; paragraph
	dc.b $0B	; word
	dc.b $43,$48,$45,$57,$45,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $20	; page
	dc.b $03	; paragraph
	dc.b $03	; word
	dc.b $53,$45,$56,$45,$4E,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $20	; page
	dc.b $06	; paragraph
	dc.b $03	; word
	dc.b $42,$4F,$55,$4E,$43,$49,$4E,$47,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $20	; page
	dc.b $02	; paragraph
	dc.b $03	; word
	dc.b $41,$00	; answer_and_fill
	dcb.b $B,$20
	dc.b $21	; page
	dc.b $03	; paragraph
	dc.b $02	; word
	dc.b $55,$50,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $21	; page
	dc.b $05	; paragraph
	dc.b $03	; word
	dc.b $44,$4F,$57,$4E,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $21	; page
	dc.b $06	; paragraph
	dc.b $03	; word
	dc.b $50,$52,$4F,$58,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $22	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $53,$50,$55,$52,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $22	; page
	dc.b $03	; paragraph
	dc.b $0E	; word
	dc.b $49,$4E,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $22	; page
	dc.b $05	; paragraph
	dc.b $02	; word
	dc.b $48,$45,$52,$45,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $22	; page
	dc.b $08	; paragraph
	dc.b $03	; word
	dc.b $44,$45,$53,$50,$45,$52,$41,$54,$45,$00,$20,$20,$20	; answer_and_fill
	dc.b $23	; page
	dc.b $02	; paragraph
	dc.b $01	; word
	dc.b $54,$48,$45,$59,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $23	; page
	dc.b $07	; paragraph
	dc.b $02	; word
	dc.b $54,$48,$4F,$55,$53,$41,$4E,$44,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $23	; page
	dc.b $0C	; paragraph
	dc.b $06	; word
	dc.b $48,$4F,$4C,$44,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $24	; page
	dc.b $01	; paragraph
	dc.b $05	; word
	dc.b $42,$49,$47,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $24	; page
	dc.b $03	; paragraph
	dc.b $03	; word
	dc.b $45,$47,$52,$4F,$4E,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $24	; page
	dc.b $04	; paragraph
	dc.b $01	; word
	dc.b $57,$4F,$57,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $24	; page
	dc.b $05	; paragraph
	dc.b $0A	; word
	dc.b $54,$41,$43,$4B,$4C,$45,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $24	; page
	dc.b $10	; paragraph
	dc.b $05	; word
	dc.b $48,$41,$52,$44,$45,$4E,$45,$44,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $25	; page
	dc.b $01	; paragraph
	dc.b $04	; word
	dc.b $43,$52,$55,$4D,$42,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $25	; page
	dc.b $04	; paragraph
	dc.b $03	; word
	dc.b $50,$4C,$41,$53,$4D,$41,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $25	; page
	dc.b $0F	; paragraph
	dc.b $0D	; word
	dc.b $41,$53,$53,$45,$54,$53,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $26	; page
	dc.b $04	; paragraph
	dc.b $01	; word
	dc.b $57,$49,$54,$48,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $26	; page
	dc.b $05	; paragraph
	dc.b $07	; word
	dc.b $4F,$52,$47,$41,$4E,$49,$43,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $26	; page
	dc.b $07	; paragraph
	dc.b $02	; word
	dc.b $53,$48,$41,$4B,$45,$4E,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $26	; page
	dc.b $09	; paragraph
	dc.b $09	; word
	dc.b $53,$4D,$49,$4C,$45,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $27	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $44,$4F,$55,$42,$54,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $27	; page
	dc.b $04	; paragraph
	dc.b $02	; word
	dc.b $47,$41,$56,$45,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $28	; page
	dc.b $03	; paragraph
	dc.b $02	; word
	dc.b $45,$58,$43,$45,$4C,$4C,$45,$4E,$54,$00,$20,$20,$20	; answer_and_fill
	dc.b $28	; page
	dc.b $08	; paragraph
	dc.b $01	; word
	dc.b $53,$54,$41,$52,$44,$52,$49,$56,$45,$00,$20,$20,$20	; answer_and_fill
	dc.b $28	; page
	dc.b $0B	; paragraph
	dc.b $01	; word
	dc.b $43,$4F,$4E,$54,$41,$43,$54,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $29	; page
	dc.b $05	; paragraph
	dc.b $02	; word
	dc.b $4D,$4F,$4F,$4E,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $29	; page
	dc.b $0A	; paragraph
	dc.b $01	; word
	dc.b $47,$4F,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $29	; page
	dc.b $0D	; paragraph
	dc.b $08	; word
	dc.b $43,$41,$56,$45,$44,$00,$20,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $2A	; page
	dc.b $06	; paragraph
	dc.b $02	; word
	dc.b $49,$54,$00	; answer_and_fill
	dcb.b $A,$20
	dc.b $2A	; page
	dc.b $08	; paragraph
	dc.b $01	; word
	dc.b $54,$48,$45,$00	; answer_and_fill
	dcb.b $9,$20
	dc.b $2A	; page
	dc.b $09	; paragraph
	dc.b $0B	; word
	dc.b $47,$48,$41,$53,$54,$4C,$59,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $2A	; page
	dc.b $0B	; paragraph
	dc.b $06	; word
	dc.b $53,$54,$52,$41,$50,$50,$49,$4E,$47,$00,$20,$20,$20	; answer_and_fill
	dc.b $2A	; page
	dc.b $0D	; paragraph
	dc.b $02	; word
	dc.b $4D,$45,$53,$53,$49,$4E,$47,$00,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $2B	; page
	dc.b $02	; paragraph
	dc.b $02	; word
	dc.b $50,$4F,$44,$53,$00	; answer_and_fill
	dcb.b $8,$20
	dc.b $2B	; page
	dc.b $03	; paragraph
	dc.b $02	; word
	dc.b $43,$55,$42,$4F,$49,$44,$00,$20,$20,$20,$20,$20,$20	; answer_and_fill
	dc.b $2B	; page
	dc.b $08	; paragraph
	dc.b $01	; word
	dc.b $42,$55,$4E,$47,$4C,$45,$52,$53,$00,$20,$20,$20,$20	; answer_and_fill
	dc.b $2B	; page
	dc.b $08	; paragraph
	dc.b $06	; word
	dc.b $43,$52,$45,$54,$49,$4E,$53,$00,$20,$20,$20,$20,$20	; answer_and_fill
protection_incorrect_text:
	dc.b $8C
	dcb.b $8,$0A
	dcb.b $C,$20
	dc.b $49,$6E,$63,$6F,$72,$72,$65,$63,$74,$21,$00
protection_try_again_text:
	dcb.b $C,$20
	dc.b $54,$72,$79,$20,$61,$6E,$6F,$74,$68,$65,$72,$20,$6F,$6E,$65,$0D
	dc.b $0A,$0A,$8A,$20,$20,$20,$20,$20,$20,$20,$50,$72,$65,$73,$73,$20
	dc.b $61,$6E,$79,$20,$6B,$65,$79,$20,$74,$6F,$20,$63,$6F,$6E,$74,$69
	dc.b $6E,$75,$65,$2E,$00
protection_exhausted_text:
	dc.b $8C,$59,$6F,$75,$20,$68,$61,$76,$65,$20,$65,$6E,$74,$65,$72,$65
	dc.b $64,$20,$33,$20,$69,$6E,$63,$6F,$72,$72,$65,$63,$74,$20,$70,$61
	dc.b $73,$73,$77,$6F,$72,$64,$73,$0D,$0A,$0A,$50,$6C,$65,$61,$73,$65
	dc.b $20,$72,$65,$62,$6F,$6F,$74,$20,$61,$6E,$64,$20,$74,$72,$79,$20
	dc.b $61,$67,$61,$69,$6E,$2E,$00
protection_instructions_text:
	dc.b $89,$50,$72,$6F,$67,$72,$61,$6D,$20,$50,$72,$6F,$74,$65,$63,$74
	dc.b $69,$6F,$6E,$0D,$0A,$0A,$8F,$59,$6F,$75,$20,$61,$72,$65,$20,$72
	dc.b $65,$71,$75,$69,$72,$65,$64,$20,$74,$6F,$20,$65,$6E,$74,$65,$72
	dc.b $20,$61,$20,$77,$6F,$72,$64,$20,$66,$72,$6F,$6D,$0D,$0A,$74,$68
	dc.b $65,$20,$6E,$6F,$76,$65,$6C,$6C,$61,$2C,$20,$77,$68,$69,$63,$68
	dc.b $20,$69,$73,$20,$61,$74,$20,$74,$68,$65,$20,$70,$61,$67,$65,$2C
	dc.b $0D,$0A,$70,$61,$72,$61,$67,$72,$61,$70,$68,$20,$61,$6E,$64,$20
	dc.b $77,$6F,$72,$64,$20,$73,$70,$65,$63,$69,$66,$69,$65,$64,$20,$62
	dc.b $65,$6C,$6F,$77,$2E,$0D,$0A,$50,$75,$6E,$63,$74,$75,$61,$74,$69
	dc.b $6F,$6E,$2C,$20,$63,$68,$61,$70,$74,$65,$72,$20,$6E,$75,$6D,$62
	dc.b $65,$72,$73,$20,$61,$6E,$64,$20,$62,$6F,$6C,$64,$0D,$0A,$74,$79
	dc.b $70,$65,$20,$73,$68,$6F,$75,$6C,$64,$20,$62,$65,$20,$69,$67,$6E
	dc.b $6F,$72,$65,$64,$21,$0D,$0A,$0A,$59,$6F,$75,$20,$68,$61,$76,$65
	dc.b $20,$33,$20,$61,$74,$74,$65,$6D,$70,$74,$73,$20,$74,$6F,$20,$66
	dc.b $69,$6E,$64,$20,$74,$68,$65,$20,$72,$69,$67,$68,$74,$0D,$0A,$77
	dc.b $6F,$72,$64,$20,$62,$65,$66,$6F,$72,$65,$20,$74,$68,$65,$20,$70
	dc.b $72,$6F,$67,$72,$61,$6D,$20,$69,$73,$20,$63,$6C,$65,$61,$72,$65
	dc.b $64,$2E,$0D,$0A,$0A,$8C,$45,$67,$2E,$20,$50,$41,$47,$45,$20,$31
	dc.b $35,$2C,$20,$50,$41,$52,$41,$47,$52,$41,$50,$48,$20,$31,$2C,$20
	dc.b $57,$4F,$52,$44,$20,$34,$0D,$0A,$8F,$6F,$66,$20,$74,$68,$65,$20
	dc.b $6E,$6F,$76,$65,$6C,$6C,$61,$20,$69,$73,$20,$2D,$20,$8A,$53,$4D
	dc.b $49,$4C,$45,$8F,$0D,$0A,$0A,$50,$6C,$65,$61,$73,$65,$20,$65,$6E
	dc.b $74,$65,$72,$20,$74,$68,$65,$20,$77,$6F,$72,$64,$20,$61,$74,$20
	dc.b $2D,$0D,$0A,$0A,$8C,$50,$41,$47,$45,$20
protection_page_number_text:
	dc.b $20,$20,$20,$20,$20,$20,$50,$41,$52,$41,$47,$52,$41,$50,$48,$20
protection_paragraph_number_text:
	dc.b $20,$20,$20,$20,$20,$20,$57,$4F,$52,$44,$20
protection_word_number_text:
	dc.b $20,$20,$20,$20,$20,$0D,$0D,$0A,$0A,$0A,$8F,$3A,$8A,$00,$00
request_novella_word:
	move.w #$3,novella_attempts_remaining(a6)
abs_0_00013C02:
	bsr.w abs_0_00013D38
abs_0_00013C06:
	cmp.w #$93,d0
	bcc.w abs_0_00013C02
	andi.l #255,d0
	lsl.l #4,d0
	lea.l abs_0_00012F80(pc),a0
	adda.l d0,a0
remember_selected_novella_record:
	move.l a0,selected_novella_record_pointer(a6)
	bsr.w abs_0_00013D44
abs_0_00013C24:
	movea.l selected_novella_record_pointer(a6),a0
	moveq.l #0,d0
	move.b (a0)+,d0
	lea.l abs_0_00012F80+3154(pc),a1
	bsr.w abs_0_00013D3E
abs_0_00013C34:
	movea.l $0058(a6),a1
	move.b #$20,-(a1)
	moveq.l #0,d0
	move.b (a0)+,d0
	lea.l abs_0_00012F80+3170(pc),a1
	bsr.w abs_0_00013D3E
abs_0_00013C48:
	movea.l $0058(a6),a1
	move.b #$20,-(a1)
	clr.l d0
	move.b (a0)+,d0
	lea.l abs_0_00012F80+3181(pc),a1
	bsr.w abs_0_00013D3E
abs_0_00013C5C:
	movea.l $0058(a6),a1
	move.b #$20,-(a1)
	movem.l a0-a1,-(a7)
	lea.l abs_0_00012F80+2776(pc),a1
	bsr.w abs_0_00013D2C
abs_0_00013C70:
	movem.l (a7)+,a0-a1
	movea.l a0,a1
	movea.l protection_input_limit_pointer(pc),a0
	move.w #$10,(a0)
	lea.l protection_answer_buffer(pc),a0
	bsr.w abs_0_00013D32
abs_0_00013C86:
	movem.l a0-a1,-(a7)
	bsr.w abs_0_00013D44
abs_0_00013C8E:
	lea.l novella_answer_tail_latch(a6),a3
	movem.l (a7)+,a0-a1
	lea.l novella_expected_char_latch(a6),a2
compare_novella_answer:
	move.b (a1)+,d0
	move.b d0,(a2)
	beq.w abs_0_00013CA8
	cmp.b (a0)+,d0
	beq.b compare_novella_answer
	bra.b retry_novella_answer
abs_0_00013CA8:
	move.b (a0),(a3)
	bne.b retry_novella_answer
	bsr.w abs_0_00013D26
abs_0_00013CB0:
	rts
retry_novella_answer:
	subq.w #1,novella_attempts_remaining(a6)
	beq.b protection_attempts_exhausted
	lea.l abs_0_00012F80+2608(pc),a1
	bsr.w abs_0_00013D2C
abs_0_00013CC0:
	bsr.w abs_0_00013D4A
abs_0_00013CC4:
	bsr.w abs_0_00013D44
abs_0_00013CC8:
	bra.w abs_0_00013C24
protection_attempts_exhausted:
	lea.l abs_0_00012F80+2705(pc),a1
	bsr.w abs_0_00013D2C
abs_0_00013CD4:
	bra.b abs_0_00013CD4
protection_answer_buffer:
	dcb.b $3E,$00
	dc.b $36,$9B,$D0,$CC,$36,$9B,$B0,$CC
	dcb.b $A,$00
abs_0_00013D26:
	jmp $000034DC.l
abs_0_00013D2C:
	jmp $00002734.l
abs_0_00013D32:
	jmp $0000D7D8.l
abs_0_00013D38:
	jmp $00000380.l
abs_0_00013D3E:
	jmp $00002558.l
abs_0_00013D44:
	jmp $000034AA.l
abs_0_00013D4A:
	jmp $0000D7AA.l
protection_input_limit_pointer:
	dc.l $0000D904	; Input-limit pointer and unentered bridge-shaped bytes; raw suffix has no execution claim
protection_unentered_bridge_bytes:
	dc.b $4E,$F9,$00,$00,$C4,$FC,$00,$00	; Input-limit pointer and unentered bridge-shaped bytes; raw suffix has no execution claim
