; Memory map
;   Absolute memory refs:
;     absolute[$00040000] refs=2 access=a

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

    INCLUDE "hardware/custom.i"

_custom	EQU	$DFF000
absolute_slot_00040000	EQU	$40000

    SECTION section_0,code
loc_0_00000000:
	lea.l loc_0_000000E8(pc),a0
	lea.l absolute_slot_00040000.l,a1
	move.l (a0)+,d0
	move.l (a0)+,d1
	move.l (a0)+,d5
	movea.l a1,a2
	adda.l d0,a0
	adda.l d1,a2
	move.l -(a0),d0
	eor.l d0,d5
loc_0_0000001A:
	lsr.l #1,d0
	bne.b loc_0_00000022
	bsr.w loc_0_000000C2
loc_0_00000022:
	bcs.b loc_0_00000060
	moveq.l #8,d1
	moveq.l #1,d3
	lsr.l #1,d0
	bne.b loc_0_00000030
	bsr.w loc_0_000000C2
loc_0_00000030:
	bcs.b loc_0_0000008C
	moveq.l #3,d1
	clr.w d4
loc_0_00000036:
	bsr.w loc_0_000000CE
	move.w d2,d3
	add.w d4,d3
loc_0_0000003E:
	moveq.l #7,d1
loc_0_00000040:
	lsr.l #1,d0
	bne.b loc_0_00000048
	bsr.w loc_0_000000C2
loc_0_00000048:
	roxl.l #1,d2
	dbf.w d1,loc_0_00000040
	move.b d2,-(a2)
	dbf.w d3,loc_0_0000003E
	bra.w loc_0_0000009A
loc_0_00000058:
	moveq.l #8,d1
	moveq.l #8,d4
	bra.w loc_0_00000036
loc_0_00000060:
	moveq.l #2,d1
	bsr.w loc_0_000000CE
	cmpi.b #2,d2
	blt.b loc_0_00000082
	cmpi.b #3,d2
	beq.b loc_0_00000058
	moveq.l #8,d1
	bsr.w loc_0_000000CE
	move.w d2,d3
	move.w #$C,d1
	bra.w loc_0_0000008C
loc_0_00000082:
	move.w #$9,d1
	add.w d2,d1
	addq.w #2,d2
	move.w d2,d3
loc_0_0000008C:
	bsr.w loc_0_000000CE
loc_0_00000090:
	subq.w #1,a2
	move.b $0(a2,d2.w),(a2)
	dbf.w d3,loc_0_00000090
loc_0_0000009A:
	nop
	nop
	nop
	cmpa.l a2,a1
	blt.w loc_0_0000001A
	tst.l d5
	bne.b loc_0_000000B0
	jmp $00040000.l
loc_0_000000B0:
	move.w #$FFFF,d0
loc_0_000000B4:
	move.w d0,_custom+color.l	; palette color 0
	dbf.w d0,loc_0_000000B4
	moveq.l #-1,d0
	rts
loc_0_000000C2:
	move.l -(a0),d0
	eor.l d0,d5
	move #$10,ccr
	roxr.l #1,d0
	rts
loc_0_000000CE:
	subq.w #1,d1
	clr.w d2
loc_0_000000D2:
	lsr.l #1,d0
	bne.b loc_0_000000E0
	move.l -(a0),d0
	eor.l d0,d5
	move #$10,ccr
	roxr.l #1,d0
loc_0_000000E0:
	roxl.l #1,d2
	dbf.w d1,loc_0_000000D2
	rts
loc_0_000000E8:
	dc.l $000009D4,$00009AF6,$4473A21E,$0C002C11	; lookup_table
	dc.l $2905032F,$01A974A7,$E0992012,$4BFFE2E6	; lookup_table
	dc.l $940EE900,$142C00A8,$22088402,$00810318	; lookup_table
	dc.l $0388100B,$E0082802,$583D480E,$B04BEA0C	; lookup_table
	dc.l $544B1010,$2107834C,$0A06D160,$80C1A236	; lookup_table
	dc.l $EB00E010,$1C2039A0,$0DB06898,$402DD680	; lookup_table
	dc.l $106A5248,$02815E11,$028197B4,$E641399B	; lookup_table
	dc.l $D0402CA0,$4A158002,$8B0007E8,$3C073083	; lookup_table
	dc.l $10128183,$1D832362,$761292A8,$4802ECC1	; lookup_table
	dc.l $19442015,$2368084C,$CB938860,$90000702	; lookup_table
	dc.l $01880818,$21401011,$10B02080,$D981F878	; lookup_table
	dc.l $860A3423,$02014486,$87046534,$228212C0	; lookup_table
	dc.l $A0C64EE1,$62803010,$00C33050,$37802070	; lookup_table
	dc.l $10C69A82,$40014C08,$17A1002A,$8085201F	; lookup_table
	dc.l $06010200,$84D6840C,$9B50F910,$03FE0045	; lookup_table
	dc.l $B87D020A,$003401CC,$2109C007,$000FBA6B	; lookup_table
	dc.l $CCCDF064,$0906D361,$2FC830E1,$4041C104	; lookup_table
	dc.l $102054C0,$08C8E240,$49806456,$0E062507	; lookup_table
	dc.l $154001D1,$30E216A6,$1E605268,$11402C14	; lookup_table
	dc.l $64522681,$B009E640,$C3459403,$CC918011	; lookup_table
	dc.l $459C2410,$C8330826,$004E66B0,$65740E60	; lookup_table
	dc.l $5369827B,$01803035,$0068305F,$72103098	; lookup_table
	dc.l $280037D8,$B1F8202F,$F7F81F45,$03048040	; lookup_table
	dc.l $410F3061,$0400414F,$E356596F,$04405540	; lookup_table
	dc.l $001523E0,$56A02020,$3A50E950,$AA485CCF	; lookup_table
	dc.l $584815A8,$A82D0A60,$08202010,$47112C70	; lookup_table
	dc.l $1C0D8238,$2C00040E,$01818780,$E043C070	; lookup_table
	dc.l $260ECC04,$18601062,$06082000,$80C082C8	; lookup_table
	dc.l $84002C0E,$41202100,$78168151,$B6762080	; lookup_table
	dc.l $F40C8095,$04190343,$40A06146,$E80CA0C5	; lookup_table
	dc.l $F412BF83,$E0652080,$7D84018A,$8443220C	; lookup_table
	dc.l $00B84973,$2843007F,$8F0D0895,$48833BE0	; lookup_table
	dc.l $76ABC1FE,$0D456998,$01335558,$40D20E50	; lookup_table
	dc.l $EE70DDE9,$EE636972,$80CF1C00,$7EF083CA	; lookup_table
	dc.l $D9018021,$40A61E78,$33DA2DBF,$6601878C	; lookup_table
	dc.l $00606108,$020E30CA,$82665720,$80C00042	; lookup_table
	dc.l $06609C41,$F0A00BC0,$3A9E862A,$25CFFEFF	; lookup_table
	dc.l $85402062,$C0905489,$9480798E,$88A721C1	; lookup_table
	dc.l $0B128A58,$5A980503,$9840C311,$83CCC40C	; lookup_table
	dc.l $D0946D45,$091009D1,$0603B21B,$6C046818	; lookup_table
	dc.l $48003960,$60C57435,$10403838,$42104BE4	; lookup_table
	dc.l $09516061,$DC090339,$781D4040,$02A284FF	; lookup_table
	dc.l $DBF24FF8,$91207F03,$06CA4960,$0B7194A6	; lookup_table
	dc.l $54A1F419,$4B804C0C,$6F850290,$224180A0	; lookup_table
	dc.l $82400A94,$81014000,$80800040,$4E002028	; lookup_table
	dc.l $0196800F,$13804C66,$A500E253,$600A4187	; lookup_table
	dc.l $9048988A,$E456A29D,$4C0040DA,$40C0040D	; lookup_table
	dc.l $6770F902,$5215086E,$40C0006D,$84BE0065	; lookup_table
	dc.l $01D22727,$5BF1B240,$2D456006,$4000142B	; lookup_table
	dc.l $60011420,$190E6032,$91805036,$90180A00	; lookup_table
	dc.l $0C0181AC,$861A1010,$00010080,$6E01001C	; lookup_table
	dc.l $997DFF7F,$87003957,$187C1C90,$7CC0D083	; lookup_table
	dc.l $81FD6367,$3A22F246,$07BC9D3D,$096CE06F	; lookup_table
	dc.l $8040FA63,$81885ED5,$C4C6D3C4,$706DACA1	; lookup_table
	dc.l $67020AB2,$9626EAC6,$A46D2702,$26233C08	; lookup_table
	dc.l $19CC2C08,$D48D89C1,$99E49061,$8140FC80	; lookup_table
	dc.l $0D7302A2,$17AC8438,$3A18F1E0,$30382366	; lookup_table
	dc.l $E967623B,$2103C216,$960EB6AE,$76D6E668	; lookup_table
	dc.l $5839E4E0,$7DC06F93,$04381F33,$4D8D0988	; lookup_table
	dc.l $D6469E80,$C5B7020E,$3C081C90,$10395020	; lookup_table
	dc.l $75969D88,$42822C88,$A0750020,$E1A5A0E1	; lookup_table
	dc.l $6702228C,$CC856D18,$0E71EEA9,$A5A07553	; lookup_table
	dc.l $4B100AA1,$71BC0A07,$54E9A483,$0BA800C5	; lookup_table
	dc.l $C6828151,$36C040CB,$07201924,$53903E88	; lookup_table
	dc.l $A2A0CD65,$7B57170B,$09535E0E,$00154A34	; lookup_table
	dc.l $4EDCC854,$2D9C283F,$415A0606,$12536156	; lookup_table
	dc.l $972A6EE4,$2D4894F5,$3345EE02,$848F5E71	; lookup_table
	dc.l $55170A0F,$882BC905,$D7B0F024,$6260E53A	; lookup_table
	dc.l $044BD919,$19953810,$3CEB685E,$41102764	; lookup_table
	dc.l $2020C748,$1255C0B2,$93A1A1D8,$371140E2	; lookup_table
	dc.l $AAA0928A,$A886812D,$803BBC8C,$0EEA12B4	; lookup_table
	dc.l $CB906019,$607E0C16,$3422A699,$E29A2A08	; lookup_table
	dc.l $8B2A0314,$101BE960,$3DD8C079,$A86CE058	; lookup_table
	dc.l $4822854D,$008A4050,$A5B991BF,$295C1610	; lookup_table
	dc.l $1EACE168,$300E6088,$441153A3,$13A6382E	; lookup_table
	dc.l $2965E86B,$62285640,$7AB722E9,$68648B93	; lookup_table
	dc.l $A793A593,$A413A113,$A2079607,$649BA5A0	; lookup_table
	dc.l $68550AD2,$A6836508,$2800B177,$B637B1B1	; lookup_table
	dc.l $38045803,$51B0E56B,$4F1B4B3B,$53707280	; lookup_table
	dc.l $F34F0050,$A6141C4C,$0F588A99,$D9105650	; lookup_table
	dc.l $74B27617,$610186E6,$827D0C03,$00A06A40	; lookup_table
	dc.l $9E1A41D0,$AE87281C,$54C54032,$5850908A	; lookup_table
	dc.l $BDADAD30,$99170122,$EA05D0DB,$00F6E6A6	; lookup_table
	dc.l $4E34C4C4,$345D8C81,$096A98D9,$DA5B58D1	; lookup_table
	dc.l $994040D6,$A58383A7,$89F83780,$C0F0A1A1	; lookup_table
	dc.l $7B0202C2,$38918013,$271342F2,$8497AB42	; lookup_table
	dc.l $B80F7018,$2360624C,$DEC9C8C4,$1F48D80D	; lookup_table
	dc.l $9705992A,$48967424,$172DC0E0,$70CED05A	; lookup_table
	dc.l $8B93A781,$0B85A5B3,$811090B2,$97013918	; lookup_table
	dc.l $93A9A43E,$95A55DDD,$0D2C5DC8,$090C01C5	; lookup_table
	dc.l $2D49C6CB,$4ACACB4C,$C4C2CCC6,$C0C20E81	; lookup_table
	dc.l $20020022,$1E454CCC,$5C0965ED,$5D9D4C8D	; lookup_table
	dc.l $5C5C5DEC,$EC096808,$65ED0C4C,$09C50D6D	; lookup_table
	dc.l $4C088051,$D3B141D0,$C7800F02,$07013600	; lookup_table
	dc.l $50081D04,$813F9B43,$B2087E0B,$3E683F08	; lookup_table
	dc.l $004600E1,$62180AE8,$6236166E,$3B336EA5	; lookup_table
	dc.l $A0303888,$E0033040,$CE000710,$0B040C70	; lookup_table
	dc.l $1C11B0E3,$FA2E6081,$E78CC0D8,$0503EE2F	; lookup_table
	dc.l $9CE06083,$3A140001,$14180A01,$51F39BDB	; lookup_table
	dc.l $7B390621,$81C801C5,$033E01E4,$32040CB2	; lookup_table
	dc.l $38004010,$30C4C666,$3FF23040,$227E0658	; lookup_table
	dc.l $60A0D040,$C227F02E,$14300092,$043B140C	; lookup_table
	dc.l $34BFF06C,$88010388,$14428C09,$40BF9436	; lookup_table
	dc.l $A75304A7,$95EC41E6,$600DC652,$3C57B7B8	; lookup_table
	dc.l $0A4A248E,$01030880,$2281820D,$E4830503	; lookup_table
	dc.l $7A11010F,$00808E47,$F0F82D0A,$8E59C108	; lookup_table
	dc.l $B0271852,$A34140C0,$E780400B,$00068BB5	; lookup_table
	dc.l $078070B0,$0040C0C0,$1D20B1BB,$BFE3FC47	; lookup_table
	dc.l $2676F7B7,$3C050840,$10304140,$8A060604	; lookup_table
	dc.l $F0206C6B,$66C87CB3,$C46C0262,$83071C31	; lookup_table
	dc.l $20205F81,$00040CEA,$8002061C,$3925331B	; lookup_table
	dc.l $0E40415A,$DFDDC8B0,$9E580901,$B0C08185	; lookup_table
	dc.l $8BFB1980,$C06333FB,$02280286,$00220306	; lookup_table
	dc.l $87C460C0,$80844A00,$A600069B,$EFF0607F	; lookup_table
	dc.l $FFF01002,$06181906,$29DC2819,$E01A0462	; lookup_table
	dc.l $0C0A073A,$21037903,$4C0C1016,$02061404	; lookup_table
	dc.l $0DFC0DF8,$00F09810,$F00D0A14,$040C2446	; lookup_table
	dc.l $20C0A063,$00108011,$800C4600,$10801303	; lookup_table
	dc.l $31E41E4C,$66706410,$21801020,$206EED70	; lookup_table
	dc.l $E011013F,$07614405,$9A10830A,$3E670E08	; lookup_table
	dc.l $FC1E02FC,$0FC0207C,$11DB3C20,$2030040B	; lookup_table
	dc.l $F019F223,$07021F04,$040C7900,$40A06C67	; lookup_table
	dc.l $D0100206,$6C070820,$081B5BFC,$330BF10E	; lookup_table
	dc.l $1B31A350,$602637E6,$03FC2247,$E30180D8	; lookup_table
	dc.l $149C0602,$0302061C,$000F98CD,$975FD242	; lookup_table
	dc.l $07038604,$0C040603,$801B0DA2,$39305037	; lookup_table
	dc.l $F415D555,$D417F605,$00838021,$8100B080	; lookup_table
	dc.l $80444040,$2A202013,$10100B88,$08042404	; lookup_table
	dc.l $02511045,$10C4D201,$41713481,$00092F83	; lookup_table
	dc.l $0049001C,$0029000B,$804010E4,$02200201	; lookup_table
	dc.l $50008080,$0302302C,$020C2602,$81885112	; lookup_table
	dc.l $E0040081,$A8036E40,$7FBFC000,$C0007800	; lookup_table
	dc.l $FF7001FE,$E003FDC0,$07FB800F,$F7001FEE	; lookup_table
	dc.l $003FDC00,$7FB800FF,$7001FEE0,$03FDC007	; lookup_table
	dc.l $FB800FF7,$001FEE00,$3FDC007F,$B800FF70	; lookup_table
	dc.l $01FEE003,$FDC007FB,$800FF700,$1FEE003F	; lookup_table
	dc.l $DC007FB8,$00FF7001,$FEE003FD,$C007FB80	; lookup_table
	dc.l $0FF7001F,$EE003FDC,$007FB800,$FF7001FE	; lookup_table
	dc.l $E003FDC0,$07FB800F,$F7001FEE,$003FDC00	; lookup_table
	dc.l $7FB800FF,$7001FEE0,$03FDC007,$FB800FF7	; lookup_table
	dc.l $001FEE00,$3FDC007F,$B800FF70,$01FEE003	; lookup_table
	dc.l $FDC007FB,$800FF700,$1FEE003F,$DC007FB8	; lookup_table
	dc.l $00FF7001,$FEE003FD,$C007FB80,$0FF7001F	; lookup_table
	dc.l $EE003FDC,$007FB800,$FF7001FE,$E003FDC0	; lookup_table
	dc.l $07FB800F,$F7001FEE,$003FDC00,$7FB800FF	; lookup_table
	dc.l $7001FEE0,$03FDC007,$FB800FF7,$001FEE00	; lookup_table
	dc.l $3FDC007F,$B800FF70,$01FEE003,$FDC007FB	; lookup_table
	dc.l $800FF700,$1FEE003F,$DC007FB8,$00FF7001	; lookup_table
	dc.l $FEE003FD,$C007FB80,$0FF7001F,$EE003FDC	; lookup_table
	dc.l $007FB800,$FF7001FE,$E003FDC0,$07FB800F	; lookup_table
	dc.l $F7001FEE,$003FDC00,$7FB800FF,$7001FEE0	; lookup_table
	dc.l $03FDC007,$FB800FF7,$001FEE00,$3FDC007F	; lookup_table
	dc.l $B800FF70,$01FEE003,$FDC007FB,$800FF700	; lookup_table
	dc.l $1FEE003F,$DC007FB8,$00FF7001,$FEE003FD	; lookup_table
	dc.l $C007FB80,$0FF7001F,$EE003FDC,$007FB800	; lookup_table
	dc.l $FF7001FE,$E003FDC0,$07FB800F,$F7001FEE	; lookup_table
	dc.l $003FDC00,$7FB800FF,$7001FEE0,$03FDC007	; lookup_table
	dc.l $FB800FF7,$001FEE00,$3FDC003F,$03600010	; lookup_table
    SECTION section_1,bss,$4
	DS.L $1
