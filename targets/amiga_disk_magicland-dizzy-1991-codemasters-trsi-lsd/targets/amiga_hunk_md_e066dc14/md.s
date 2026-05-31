; Memory map
;   section[$00000052-$0000005C] -> runtime[$00000100-$0000010A] discovered_copy suppressed
;   section[$0000005C-$0000B398] -> runtime[$0005BFF0-$0006732C] discovered_copy materialized
;   section[$000095DA-$000096CA] -> runtime[$00000318-$00000408] discovered_copy suppressed
;   section[$000095DE-$000096CE] -> runtime[$0000031C-$0000040C] discovered_copy suppressed
;   section[$000095E2-$0000965A] -> runtime[$00000320-$00000398] discovered_copy suppressed
;   section[$000095E4-$000096D4] -> runtime[$00000322-$00000412] discovered_copy suppressed
;   section[$000095E8-$000096D8] -> runtime[$00000326-$00000416] discovered_copy suppressed
;   section[$000095EC-$00009664] -> runtime[$0000032A-$000003A2] discovered_copy suppressed
;   Absolute memory refs:
;     absolute[$00000092] refs=3 access=a
;     absolute[$000000C0] refs=1 access=a
;     absolute[$0000017A] refs=1 access=a
;     absolute[$0000048A] refs=1 access=a
;     absolute[$00000494] refs=1 access=a
;     absolute[$000004A8] refs=1 access=a
;     absolute[$000004BC] refs=1 access=a
;     absolute[$000004D0] refs=1 access=a
;     absolute[$000004EE] refs=1 access=a
;     absolute[$0000050C] refs=2 access=a
;     absolute[$00000520] refs=2 access=a
;     absolute[$0000053E] refs=1 access=a
;     absolute[$00000548] refs=1 access=a
;     absolute[$00000570] refs=6 access=a
;     absolute[$00000610] refs=3 access=a
;     absolute[$00000650] refs=2 access=a
;     absolute[$00000790] refs=3 access=a
;     absolute[$000007B0] refs=2 access=a
;     absolute[$000009B0] refs=2 access=a
;     absolute[$00000B90] refs=2 access=a
;     absolute[$00000BB0] refs=2 access=a
;     absolute[$00001140-$00001144] refs=1 access=w
;     absolute[$00001540] refs=2 access=a
;     absolute[$00001940] refs=3 access=a
;     absolute[$00002940] refs=2 access=a
;     absolute[$00003940] refs=4 access=a
;     absolute[$00003B40] refs=5 access=a
;     absolute[$00003B42] refs=3 access=a
;     absolute[$00003D40] refs=2 access=a
;     absolute[$00004048] refs=1 access=a
;     absolute[$00004350] refs=2 access=a
;     absolute[$00004750] refs=3 access=a
;     ... additional absolute memory ranges omitted

; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls

    INCLUDE "hardware/adkbits.i"
    INCLUDE "hardware/cia.i"
    INCLUDE "hardware/custom.i"
    INCLUDE "hardware/dmabits.i"
    INCLUDE "hardware/intbits.i"

_custom	EQU	$DFF000
stack_top_00080000	EQU	$80000
absolute_slot_000000C0	EQU	$C0
runtime_code_00000100	EQU	$100
m68k_vector_trap_0_instruction_vector	EQU	$80
INTF_CLRALL	EQU	$7FFF
DMAF_CLRALL	EQU	$7FFF
_ciaa	EQU	$BFE001
absolute_slot_00004350	EQU	$4350
absolute_slot_00068000	EQU	$68000
absolute_slot_00000122	EQU	$122
absolute_slot_00051618	EQU	$51618
absolute_slot_00003B40	EQU	$3B40
absolute_slot_00026F50	EQU	$26F50
absolute_slot_00003940	EQU	$3940
absolute_slot_000002FE	EQU	$2FE
absolute_slot_000001DE	EQU	$1DE
absolute_slot_0000018C	EQU	$18C
absolute_slot_0000018E	EQU	$18E
absolute_slot_000001CC	EQU	$1CC
absolute_slot_000001CA	EQU	$1CA
m68k_vector_trap_4_instruction_vector	EQU	$90
absolute_slot_000001EA	EQU	$1EA
absolute_slot_000001E6	EQU	$1E6
absolute_slot_000002C2	EQU	$2C2
absolute_slot_000001E4	EQU	$1E4
absolute_slot_000002F6	EQU	$2F6
absolute_slot_00000252	EQU	$252
absolute_slot_00000254	EQU	$254
absolute_slot_00000162	EQU	$162
absolute_slot_0000016A	EQU	$16A
absolute_slot_000002F4	EQU	$2F4
absolute_slot_00000160	EQU	$160
absolute_slot_000001C8	EQU	$1C8
absolute_slot_000002EA	EQU	$2EA
absolute_slot_00000230	EQU	$230
absolute_slot_00000192	EQU	$192
absolute_slot_00000190	EQU	$190
absolute_slot_00000138	EQU	$138
m68k_vector_level_3_interrupt_autovector	EQU	$6C
absolute_slot_00000092	EQU	$92
absolute_slot_00000140	EQU	$140
absolute_slot_00000142	EQU	$142
absolute_slot_00058AB0	EQU	$58AB0
absolute_slot_0000012A	EQU	$12A
absolute_slot_00000126	EQU	$126
absolute_slot_00000132	EQU	$132
absolute_slot_0000012E	EQU	$12E
absolute_slot_00000BB0	EQU	$BB0
absolute_slot_00000116	EQU	$116
absolute_slot_0000014E	EQU	$14E
absolute_slot_00000154	EQU	$154
absolute_slot_00000156	EQU	$156
absolute_slot_00000152	EQU	$152
absolute_slot_00000153	EQU	$153
absolute_slot_00000150	EQU	$150
absolute_slot_00000151	EQU	$151
absolute_slot_00000790	EQU	$790
absolute_slot_00000990	EQU	$990
absolute_slot_000007B0	EQU	$7B0
absolute_slot_00000B90	EQU	$B90
absolute_slot_000009B0	EQU	$9B0
absolute_slot_000001E8	EQU	$1E8
absolute_slot_0000013C	EQU	$13C
absolute_slot_0000011A	EQU	$11A
absolute_slot_00003D40	EQU	$3D40
absolute_slot_00004048	EQU	$4048
absolute_slot_00C00000	EQU	$C00000
absolute_slot_00080000	EQU	$80000
absolute_slot_00200000	EQU	$200000
absolute_slot_0000011E	EQU	$11E
m68k_vector_trap_1_instruction_vector	EQU	$84
m68k_vector_trap_2_instruction_vector	EQU	$88
m68k_vector_trap_3_instruction_vector	EQU	$8C
absolute_slot_00006F50	EQU	$6F50
absolute_slot_0000024A	EQU	$24A
absolute_slot_00000276	EQU	$276
absolute_slot_00000294	EQU	$294
absolute_slot_00000300	EQU	$300
absolute_slot_00000304	EQU	$304
absolute_slot_00000158	EQU	$158
absolute_slot_0000015A	EQU	$15A
absolute_slot_0000015C	EQU	$15C
absolute_slot_0000015E	EQU	$15E
absolute_slot_0000023A	EQU	$23A
absolute_slot_00000182	EQU	$182
absolute_slot_000001E0	EQU	$1E0
absolute_slot_000680AA	EQU	$680AA
absolute_slot_00032DD0	EQU	$32DD0
absolute_slot_0004B470	EQU	$4B470
absolute_slot_0002F490	EQU	$2F490
absolute_slot_00000D40	EQU	$D40
absolute_slot_00001140	EQU	$1140
absolute_slot_00000136	EQU	$136
absolute_slot_00001940	EQU	$1940
absolute_slot_00002940	EQU	$2940
absolute_slot_00001540	EQU	$1540
absolute_slot_0002E6B0	EQU	$2E6B0
absolute_slot_000305B0	EQU	$305B0
absolute_slot_00032DB0	EQU	$32DB0
absolute_slot_0002DA30	EQU	$2DA30
absolute_slot_0002E430	EQU	$2E430
absolute_slot_00000170	EQU	$170
absolute_slot_00000172	EQU	$172
absolute_slot_00000174	EQU	$174
absolute_slot_00000176	EQU	$176
absolute_slot_0000017E	EQU	$17E
absolute_slot_00000180	EQU	$180
absolute_slot_00000181	EQU	$181
absolute_slot_0000017F	EQU	$17F
absolute_slot_00000224	EQU	$224
absolute_slot_0002E6B4	EQU	$2E6B4
absolute_slot_00000220	EQU	$220
absolute_slot_00030943	EQU	$30943
absolute_slot_00000222	EQU	$222
absolute_slot_000308D3	EQU	$308D3
absolute_slot_0000017A	EQU	$17A
absolute_slot_000001C2	EQU	$1C2
absolute_slot_000001BE	EQU	$1BE
absolute_slot_000001C0	EQU	$1C0
absolute_slot_00000196	EQU	$196
absolute_slot_00004750	EQU	$4750
absolute_slot_0000019C	EQU	$19C
absolute_slot_0000019A	EQU	$19A
absolute_slot_00006150	EQU	$6150
absolute_slot_000001C4	EQU	$1C4
absolute_slot_00000198	EQU	$198
absolute_slot_00000184	EQU	$184
absolute_slot_00000188	EQU	$188
absolute_slot_0000018A	EQU	$18A
absolute_slot_00000186	EQU	$186
absolute_slot_000001C6	EQU	$1C6
absolute_slot_000001A8	EQU	$1A8
absolute_slot_000001AA	EQU	$1AA
absolute_slot_000001EC	EQU	$1EC
absolute_slot_0000020C	EQU	$20C
absolute_slot_00000210	EQU	$210
absolute_slot_0000020E	EQU	$20E
absolute_slot_00000260	EQU	$260
absolute_slot_00000264	EQU	$264
absolute_slot_00000262	EQU	$262
absolute_slot_00000266	EQU	$266
absolute_slot_000001D0	EQU	$1D0
absolute_slot_000001F2	EQU	$1F2
absolute_slot_00000200	EQU	$200
absolute_slot_000001FA	EQU	$1FA
absolute_slot_000001F6	EQU	$1F6
absolute_slot_00000204	EQU	$204
absolute_slot_000001F4	EQU	$1F4
absolute_slot_00000202	EQU	$202
absolute_slot_00000208	EQU	$208
absolute_slot_000001EE	EQU	$1EE
absolute_slot_000001F0	EQU	$1F0
absolute_slot_00000209	EQU	$209
absolute_slot_000001FC	EQU	$1FC
absolute_slot_000001FE	EQU	$1FE
absolute_slot_0000020A	EQU	$20A
absolute_slot_0002E330	EQU	$2E330
runtime_code_00000318	EQU	$318
absolute_slot_0000016E	EQU	$16E
absolute_slot_0000028E	EQU	$28E
absolute_slot_0000027E	EQU	$27E
absolute_slot_00000164	EQU	$164
absolute_slot_000002CE	EQU	$2CE
absolute_slot_00000166	EQU	$166
absolute_slot_00000168	EQU	$168
absolute_slot_00000570	EQU	$570
absolute_slot_0000024C	EQU	$24C
absolute_slot_000004BC	EQU	$4BC
absolute_slot_00000236	EQU	$236
absolute_slot_00000227	EQU	$227
absolute_slot_00000282	EQU	$282
absolute_slot_00000228	EQU	$228
absolute_slot_00000244	EQU	$244
absolute_slot_0000021A	EQU	$21A
absolute_slot_00000226	EQU	$226
absolute_slot_000004EE	EQU	$4EE
absolute_slot_00000256	EQU	$256
absolute_slot_000002E2	EQU	$2E2
absolute_slot_00000258	EQU	$258
absolute_slot_000002A0	EQU	$2A0
absolute_slot_00000232	EQU	$232
absolute_slot_0000021C	EQU	$21C
absolute_slot_00000229	EQU	$229
absolute_slot_000002CC	EQU	$2CC
absolute_slot_000001DC	EQU	$1DC
absolute_slot_0000021B	EQU	$21B
absolute_slot_0000022C	EQU	$22C
absolute_slot_0000048A	EQU	$48A
absolute_slot_00000296	EQU	$296
absolute_slot_0000021E	EQU	$21E
absolute_slot_0000021D	EQU	$21D
absolute_slot_0000022B	EQU	$22B
absolute_slot_000001BA	EQU	$1BA
absolute_slot_000001B8	EQU	$1B8
absolute_slot_000001B0	EQU	$1B0
absolute_slot_000002DE	EQU	$2DE
absolute_slot_000001D8	EQU	$1D8
absolute_slot_0000026C	EQU	$26C
absolute_slot_0000026A	EQU	$26A
absolute_slot_00000268	EQU	$268
absolute_slot_000002EE	EQU	$2EE
absolute_slot_0000025E	EQU	$25E
absolute_slot_0000029C	EQU	$29C
absolute_slot_0000025C	EQU	$25C
absolute_slot_0000025A	EQU	$25A
absolute_slot_000001AC	EQU	$1AC
absolute_slot_000001AE	EQU	$1AE
absolute_slot_000001CE	EQU	$1CE
absolute_slot_00000610	EQU	$610
absolute_slot_000001A4	EQU	$1A4
absolute_slot_000001A6	EQU	$1A6
absolute_slot_0000019E	EQU	$19E
absolute_slot_000001A2	EQU	$1A2
absolute_slot_000001D2	EQU	$1D2
absolute_slot_000001D4	EQU	$1D4
absolute_slot_000001D6	EQU	$1D6
absolute_slot_0002E6B6	EQU	$2E6B6
absolute_slot_000309D8	EQU	$309D8
absolute_slot_0002E6BE	EQU	$2E6BE
absolute_slot_0002E7FE	EQU	$2E7FE
absolute_slot_000309DE	EQU	$309DE
absolute_slot_0000023E	EQU	$23E
absolute_slot_00000494	EQU	$494
absolute_slot_00000240	EQU	$240
absolute_slot_000004A8	EQU	$4A8
absolute_slot_00000242	EQU	$242
absolute_slot_00000290	EQU	$290
absolute_slot_00000292	EQU	$292
absolute_slot_000001BC	EQU	$1BC
absolute_slot_000001B6	EQU	$1B6
absolute_slot_0000029E	EQU	$29E
absolute_slot_000004D0	EQU	$4D0
absolute_slot_00000298	EQU	$298
absolute_slot_0000029A	EQU	$29A
absolute_slot_00000238	EQU	$238
absolute_slot_00000218	EQU	$218
absolute_slot_000002DC	EQU	$2DC
absolute_slot_000002C8	EQU	$2C8
absolute_slot_0000053E	EQU	$53E
absolute_slot_000002CA	EQU	$2CA
absolute_slot_0000026E	EQU	$26E
absolute_slot_00000234	EQU	$234
absolute_slot_0000022E	EQU	$22E
absolute_slot_00000650	EQU	$650
absolute_slot_00000248	EQU	$248
absolute_slot_00000246	EQU	$246
absolute_slot_000002E0	EQU	$2E0
absolute_slot_0000024E	EQU	$24E
absolute_slot_00000250	EQU	$250
absolute_slot_000002E4	EQU	$2E4
absolute_slot_000002E6	EQU	$2E6
absolute_slot_0000022A	EQU	$22A
absolute_slot_00000212	EQU	$212
absolute_slot_00000214	EQU	$214
absolute_slot_00000216	EQU	$216
absolute_slot_00000270	EQU	$270
absolute_slot_00000520	EQU	$520
absolute_slot_00000272	EQU	$272
absolute_slot_00000274	EQU	$274
absolute_slot_00000278	EQU	$278
absolute_slot_0000027A	EQU	$27A
absolute_slot_00000280	EQU	$280
absolute_slot_0000027C	EQU	$27C
absolute_slot_0000050C	EQU	$50C
absolute_slot_000002EC	EQU	$2EC
absolute_slot_00000286	EQU	$286
absolute_slot_00000288	EQU	$288
absolute_slot_00000284	EQU	$284
absolute_slot_000002A4	EQU	$2A4
absolute_slot_000002A8	EQU	$2A8
absolute_slot_000002B0	EQU	$2B0
absolute_slot_000002B2	EQU	$2B2
absolute_slot_000002AC	EQU	$2AC
absolute_slot_000002B6	EQU	$2B6
absolute_slot_000002BA	EQU	$2BA
absolute_slot_000002BE	EQU	$2BE
absolute_slot_000002A2	EQU	$2A2
absolute_slot_000002C4	EQU	$2C4
absolute_slot_000002C6	EQU	$2C6
absolute_slot_00000144	EQU	$144
absolute_slot_000002D0	EQU	$2D0
absolute_slot_000002F0	EQU	$2F0
absolute_slot_0000014C	EQU	$14C
absolute_slot_000001B4	EQU	$1B4
absolute_slot_000001B2	EQU	$1B2
absolute_slot_0000023C	EQU	$23C
absolute_slot_000002E8	EQU	$2E8
absolute_slot_000002D2	EQU	$2D2
absolute_slot_00000548	EQU	$548
absolute_slot_0000AF50	EQU	$AF50
absolute_slot_00000146	EQU	$146
absolute_slot_0000014A	EQU	$14A
absolute_slot_0000028A	EQU	$28A
absolute_slot_00000148	EQU	$148
absolute_slot_0000028C	EQU	$28C
absolute_slot_0006B428	EQU	$6B428
absolute_slot_00000112	EQU	$112
absolute_slot_0006B400	EQU	$6B400
absolute_slot_00003B42	EQU	$3B42
absolute_slot_000002D4	EQU	$2D4
absolute_slot_000002D8	EQU	$2D8
absolute_slot_000002D6	EQU	$2D6
absolute_slot_000002DA	EQU	$2DA
absolute_slot_000002FA	EQU	$2FA
absolute_slot_000002FC	EQU	$2FC
absolute_slot_000002F8	EQU	$2F8
absolute_slot_0007A400	EQU	$7A400
absolute_slot_0001A7E0	EQU	$1A7E0
absolute_slot_00000310	EQU	$310
absolute_slot_00000314	EQU	$314
absolute_slot_00000308	EQU	$308
absolute_slot_0000030C	EQU	$30C
_ciab	EQU	$BFD000
ADKF_CLRALL	EQU	$7FFF
absolute_slot_0000013E	EQU	$13E
absolute_slot_000519D6	EQU	$519D6

    SECTION section,code
loc_0_00000000:
	move.l #$7FFF7FFF,_custom+intena.l
	move.w #$0,_custom+dmacon.l
	move.l #$B33C,d7
	lea.l loc_0_0000005C-(*+2)(pc),a4
	lea.l abs_0_0005BFF0.l,a5
	lea.l stack_top_00080000.l,a7
	pea.l absolute_slot_000000C0.l
	movem.w loc_0_00000052(pc),d0-d4
	cmpa.l a5,a4
	bhi.b loc_0_00000040
	eori.w #504,d2
	adda.l d7,a4
	adda.l d7,a5
loc_0_00000040:
	lea.l runtime_code_00000100.w,a1
	movem.w d0-d4,(a1)
	jmp (a1)
	dc.b $42,$45,$45,$52,$31,$39,$39,$31
loc_0_00000052:
	subq.l #1,d7
	bmi.b loc_0_0000005A
	move.b (a4)+,(a5)+
	bra.b loc_0_00000052
loc_0_0000005A:
	rts
loc_0_0000005C:
    ORG $5BFF0
abs_0_0005BFF0:
	lea.l abs_0_0005C004(pc),a0
	move.l a0,m68k_vector_trap_0_instruction_vector.w
	trap #0
	dc.b $00,$8C,$00,$05,$C0,$A4
abs_0_0005C000:
	dc.b $00,$05,$C0,$00
abs_0_0005C004:
	lea.l abs_0_00064446.l,a0
	movem.l (a0)+,d0-d7/a1-a6
	suba.l a0,a0
	lea.l abs_0_0005C000.l,a7
	lea.l _custom.l,a6
	clr.w color(a6)	; palette color 0
	move.w #INTF_CLRALL,intena(a6)
	move.w #DMAF_CLRALL,dmacon(a6)
	move #$2700,sr
	bset.b #CIAB_LED,_ciaa+ciapra.l
	bsr.w abs_0_0005C3D6
	lea.l absolute_slot_00004350.l,a0
	lea.l absolute_slot_00068000.l,a1
	jsr abs_0_00064482.l
	bsr.w abs_0_0005C82A
	bsr.w abs_0_0005C92E
	move.l #$E7190345,absolute_slot_00000122.w
	lea.l abs_0_000621FA(pc),a0
	lea.l absolute_slot_00051618.l,a1
	trap #3
	lea.l absolute_slot_00051618.l,a0
	jsr abs_0_000666B6.l
	bsr.w abs_0_00061EF4
	lea.l absolute_slot_00003B40.l,a0
	bsr.w abs_0_0005C754
	move #$2100,sr
	bsr.w abs_0_0005C2D0
	move.w #$C030,$009A(a6)
	move.w #$30,$009C(a6)
	bsr.w abs_0_00061F82
	bsr.w abs_0_00061F90
	bsr.w abs_0_0005CB28
	bsr.w abs_0_0005D1FA
	bsr.w abs_0_0005D1CC
	bsr.w abs_0_0005CF5E
	bsr.w abs_0_0005C772
	bsr.w abs_0_000616E2
	bsr.w abs_0_0005C966
	bsr.w abs_0_0005C504
	lea.l abs_0_00062201(pc),a0
	lea.l absolute_slot_00026F50.l,a1
	trap #3
	bsr.w abs_0_00061FB4
	bsr.w abs_0_00062096
	lea.l _custom.l,a6
	bsr.w abs_0_0005C3E6
	bsr.w abs_0_0005C950
	bsr.w abs_0_0005C642
	lea.l absolute_slot_00003940.l,a0
	bsr.w abs_0_0005C754
abs_0_0005C0F0:
	clr.w absolute_slot_000002FE.w
	bsr.w abs_0_000613AA
	clr.w absolute_slot_000001DE.w
	bsr.w abs_0_00061350
	bsr.w abs_0_0005D258
	bsr.w abs_0_0005DBD2
	bsr.w abs_0_0005E4E2
	bsr.w abs_0_0005D122
	bsr.w abs_0_0005CEDE
	bsr.w abs_0_0005C992
	move.w #$96,absolute_slot_0000018C.w
	move.w #$80,absolute_slot_0000018E.w
	move.w #$0,absolute_slot_000001CC.w
	move.w #$C8,absolute_slot_000001CA.w
	clr.b m68k_vector_trap_4_instruction_vector.w
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.l
	clr.w absolute_slot_000002C2.w
abs_0_0005C144:
	tst.w absolute_slot_000002FE.w
	bne.b abs_0_0005C0F0
	lea.l _custom.l,a6
abs_0_0005C150:
	tst.w absolute_slot_000001E4.w
	beq.b abs_0_0005C150
	tst.w absolute_slot_000002C2.w
	bne.w abs_0_0005C26C
	bsr.w abs_0_00061DEC
	tst.w absolute_slot_000002F6.w
	bne.b abs_0_0005C144
	clr.w absolute_slot_00000252.w
	clr.w absolute_slot_00000254.w
	bsr.w abs_0_0005C45E
	tst.w absolute_slot_00000162.w
	bne.w abs_0_0005E180
	tst.l absolute_slot_0000016A.w
	bne.w abs_0_0005E498
	bsr.w abs_0_00061CCA
	tst.w absolute_slot_000002F4.w
	bne.b abs_0_0005C144
	bsr.w abs_0_0005C4F2
	tst.b absolute_slot_00000160.w
	bne.b abs_0_0005C144
	bsr.w abs_0_0005F912
	bsr.w abs_0_0005D27E
	bsr.w abs_0_0005D2AA
	bsr.w abs_0_0005D2DA
	bsr.w abs_0_0005D360
	bsr.w abs_0_0005CEFA
	bsr.w abs_0_0005CF82
	bsr.w abs_0_0005D162
	bsr.w abs_0_0005F59A
	tst.w absolute_slot_000001C8.w
	bne.b abs_0_0005C1F4
	tst.w absolute_slot_000002EA.w
	bne.b abs_0_0005C1D8
	cmpi.w #40,absolute_slot_00000230.w
	bge.b abs_0_0005C1D8
	bsr.w abs_0_0005D56C
	bsr.w abs_0_0005D50E
abs_0_0005C1D8:
	bsr.w abs_0_0005D4F0
	bsr.w abs_0_0005D5DC
	bsr.w abs_0_0005D74E
	bsr.w abs_0_0005D808
	bsr.w abs_0_0005D5DC
	bsr.w abs_0_0005F436
	bsr.w abs_0_0005D74E
abs_0_0005C1F4:
	movea.l absolute_slot_00000192.w,a0
	lea.l absolute_slot_00000190.w,a1
	bsr.w abs_0_0005D8AE
	bsr.w abs_0_00060DE4
	bsr.w abs_0_0005FD7E
	bsr.w abs_0_00060A8A
	move.l #abs_0_0005C2F8,absolute_slot_00000138.w
	lea.l abs_0_000624F0(pc),a0
	move.w absolute_slot_000001DE.w,d0
	add.w d0,d0
	add.w d0,d0
	movea.l $0(a0,d0.w),a0
	cmpa.l #$0,a0
	beq.b abs_0_0005C22E
	jsr (a0)
abs_0_0005C22E:
	bsr.w abs_0_0005E562
	bsr.w abs_0_0005D4DA
	bsr.w abs_0_0005F562
	bsr.w abs_0_0005F654
	movea.l absolute_slot_00000138.w,a0
	jsr (a0)
	bsr.w abs_0_000602EC
	cmpi.w #40,absolute_slot_00000230.w
	bge.b abs_0_0005C254
	bsr.w abs_0_0005E002
abs_0_0005C254:
	bsr.w abs_0_000610DA
	bsr.w abs_0_0005E480
	bsr.w abs_0_0005D8E4
	bsr.w abs_0_0005C41C
	clr.w absolute_slot_000001E4.w
	bra.w abs_0_0005C144
abs_0_0005C26C:
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_0005C276:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_0005C276
	bra.w abs_0_0005C0F0
abs_0_0005C280:
	btst.b #4,$00DFF01F.l
	bne.b abs_0_0005C2B8
	btst.b #5,$00DFF01F.l
	beq.b abs_0_0005C2B6
	movem.l d0-d7/a0-a6,-(a7)
	bsr.w abs_0_0005C2FA
	bsr.w abs_0_0005C5CE
	jsr abs_0_000667C0.l
	addq.w #1,absolute_slot_000001E4.w
	movem.l (a7)+,d0-d7/a0-a6
	move.w #INTF_VERTB,_custom+intreq.l
abs_0_0005C2B6:
	rte
abs_0_0005C2B8:
	movem.l d0-d7/a0-a6,-(a7)
	jsr abs_0_00066B1A.l
	movem.l (a7)+,d0-d7/a0-a6
	move.w #INTF_COPER,_custom+intreq.l
	rte
abs_0_0005C2D0:
	move.b #CIAICRF_SETCLR|CIAICRF_SP,_ciaa+ciaicr.l
	move.b #$1,_ciaa+ciatalo.l
	clr.b _ciaa+ciatahi.l
	clr.b _ciaa+ciacra.l
	clr.b m68k_vector_trap_4_instruction_vector.w
	move.l #abs_0_0005C280,m68k_vector_level_3_interrupt_autovector.w
abs_0_0005C2F8:
	rts
abs_0_0005C2FA:
	btst.b #CIAICRB_SP,_ciaa+ciaicr.l
	beq.w abs_0_0005C3CC
	movem.l d0-d1/a0-a1,-(a7)
	moveq.l #0,d0
	move.b _ciaa+ciasdr.l,d0
	move.b #CIACRAF_SPMODE|CIACRAF_LOAD|CIACRAF_OUTMODE|CIACRAF_PBON|CIACRAF_START,_ciaa+ciacra.l
	clr.b _ciaa+ciasdr.l
abs_0_0005C320:
	btst.b #CIAICRB_SP,_ciaa+ciaicr.l
	beq.b abs_0_0005C320
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	clr.b _ciaa+ciacra.l
	eori.b #255,d0
	ror.b #1,d0
	moveq.l #0,d1
	move.b d0,d1
	lea.l absolute_slot_00000092.w,a0
	btst #7,d1
	bne.b abs_0_0005C3C0
	cmp.b #$45,d1
	bne.b abs_0_0005C38C
	move.w #$1,absolute_slot_000002C2.w
abs_0_0005C38C:
	lea.l abs_0_000648C6.l,a1
	move.w absolute_slot_00000140.w,d0
	cmp.b $0(a1,d0.w),d1
	bne.b abs_0_0005C3B8
	addq.w #1,absolute_slot_00000140.w
	cmpi.b #255,$1(a1,d0.w)
	bne.b abs_0_0005C3BC
	st.b absolute_slot_00000142.w
	moveq.l #-1,d0
abs_0_0005C3AE:
	move.w d0,_custom+color.l	; palette color 0
	dbf.w d0,abs_0_0005C3AE
abs_0_0005C3B8:
	clr.w absolute_slot_00000140.w
abs_0_0005C3BC:
	move.b d1,m68k_vector_trap_4_instruction_vector.w
abs_0_0005C3C0:
	bclr #7,d1
	seq.b $0(a0,d1.w)
	movem.l (a7)+,d0-d1/a0-a1
abs_0_0005C3CC:
	move.w #INTF_PORTS,_custom+intreq.l
	rts
abs_0_0005C3D6:
	suba.l a0,a0
	lea.l absolute_slot_00058AB0.l,a1
abs_0_0005C3DE:
	clr.b (a0)+
	cmpa.l a1,a0
	bne.b abs_0_0005C3DE
	rts
abs_0_0005C3E6:
	move.l #$70152,absolute_slot_0000012A.w
	move.l #$78152,absolute_slot_00000126.w
	move.l #$D40,absolute_slot_00000132.w
	move.l #$1140,absolute_slot_0000012E.w
	lea.l absolute_slot_00000BB0.w,a0
	move.w #$C7,d0
	moveq.l #0,d1
abs_0_0005C410:
	move.w d1,(a0)+
	addi.w #168,d1
	dbf.w d0,abs_0_0005C410
	rts
abs_0_0005C41C:
	move.l vposr(a6),d0
	lsr.l #8,d0
	andi.w #511,d0
	cmp.w #$133,d0
	ble.b abs_0_0005C41C
	move.l absolute_slot_00000132.w,d0
	move.l absolute_slot_0000012E.w,absolute_slot_00000132.w
	move.l d0,absolute_slot_0000012E.w
	move.l absolute_slot_0000012A.w,d0
	move.l absolute_slot_00000126.w,absolute_slot_0000012A.w
	move.l d0,absolute_slot_00000126.w
	subi.w #168,d0
	movea.l absolute_slot_00000116.w,a0
	moveq.l #3,d6
	move.w #$E0,d7
	moveq.l #42,d5
	bsr.w abs_0_0005C72C
	rts
abs_0_0005C45E:
	cmpi.b #39,m68k_vector_trap_4_instruction_vector.w
	bne.b abs_0_0005C46E
	clr.b m68k_vector_trap_4_instruction_vector.w
	not.w absolute_slot_0000014E.w
abs_0_0005C46E:
	tst.w absolute_slot_0000014E.w
	bne.b abs_0_0005C4C0
	clr.w absolute_slot_00000154.w
	tst.w absolute_slot_00000156.w
	beq.b abs_0_0005C484
	subq.w #1,absolute_slot_00000156.w
	bra.b abs_0_0005C494
abs_0_0005C484:
	btst.b #CIAB_GAMEPORT1,_ciaa+ciapra.l
	bne.b abs_0_0005C494
	move.w #$1,absolute_slot_00000154.w
abs_0_0005C494:
	move.w joy1dat(a6),d0	; joystick/mouse port 1 data
	btst #9,d0
	sne.b absolute_slot_00000152.w
	btst #1,d0
	sne.b absolute_slot_00000153.w
	move.w d0,d1
	lsr.w #1,d1
	eor.w d0,d1
	btst #8,d1
	sne.b absolute_slot_00000150.w
	btst #0,d1
	sne.b absolute_slot_00000151.w
	rts
abs_0_0005C4C0:
	clr.w absolute_slot_00000154.w
	clr.l absolute_slot_00000150.w
	lea.l absolute_slot_00000092.w,a0
	tst.b $0031(a0)
	beq.b abs_0_0005C4D8
	move.b #$FF,absolute_slot_00000152.w
abs_0_0005C4D8:
	tst.b $0032(a0)
	beq.b abs_0_0005C4E4
	move.b #$FF,absolute_slot_00000153.w
abs_0_0005C4E4:
	tst.b $0044(a0)
	beq.b abs_0_0005C4F0
	move.w #$1,absolute_slot_00000154.w
abs_0_0005C4F0:
	rts
abs_0_0005C4F2:
	cmpi.b #25,m68k_vector_trap_4_instruction_vector.w
	bne.b abs_0_0005C502
	clr.b m68k_vector_trap_4_instruction_vector.w
	not.b absolute_slot_00000160.w
abs_0_0005C502:
	rts
abs_0_0005C504:
	lea.l absolute_slot_00000790.l,a0
	moveq.l #15,d1
abs_0_0005C50C:
	move.w absolute_slot_00000990.l,(a0)+
	dbf.w d1,abs_0_0005C50C
	lea.l absolute_slot_00000990.l,a3
	lea.l absolute_slot_00000790.l,a4
	lea.l absolute_slot_000007B0.l,a2
	bsr.b abs_0_0005C540
	lea.l absolute_slot_00000B90.l,a3
	lea.l absolute_slot_00000790.l,a4
	lea.l absolute_slot_000009B0.l,a2
	bsr.b abs_0_0005C540
	rts
abs_0_0005C540:
	moveq.l #0,d2
abs_0_0005C542:
	moveq.l #15,d6
	movea.l a3,a0
	movea.l a4,a1
abs_0_0005C548:
	move.w (a0)+,d0
	move.w (a1)+,d1
	bsr.w abs_0_0005C560
	move.w d7,(a2)+
	dbf.w d6,abs_0_0005C548
	addq.w #1,d2
	cmp.w #$F,d2
	ble.b abs_0_0005C542
	rts
abs_0_0005C560:
	tst.w d2
	bne.b abs_0_0005C568
	move.w d1,d7
abs_0_0005C566:
	rts
abs_0_0005C568:
	cmp.w #$10,d2
	bne.b abs_0_0005C572
	move.w d0,d7
	bra.b abs_0_0005C566
abs_0_0005C572:
	movem.w d0-d1,-(a7)
	andi.w #3840,d0
	andi.w #3840,d1
	lsr.w #8,d0
	lsr.w #8,d1
	sub.w d1,d0
	muls.w d2,d0
	asr.w #4,d0
	add.w d0,d1
	lsl.w #8,d1
	andi.w #3840,d1
	move.w d1,d7
	movem.w (a7),d0-d1
	andi.w #240,d0
	andi.w #240,d1
	lsr.w #4,d0
	lsr.w #4,d1
	sub.w d1,d0
	muls.w d2,d0
	asr.w #4,d0
	add.w d0,d1
	lsl.w #4,d1
	andi.w #240,d1
	or.w d1,d7
	movem.w (a7)+,d0-d1
	andi.w #15,d0
	andi.w #15,d1
	sub.w d1,d0
	muls.w d2,d0
	asr.w #4,d0
	add.w d0,d1
	andi.w #15,d1
	or.w d1,d7
	rts
abs_0_0005C5CE:
	tst.b absolute_slot_000001E6.l
	beq.b abs_0_0005C5F2
	move.w absolute_slot_000001E8.w,d0
	add.w absolute_slot_000001EA.w,d0
	bmi.b abs_0_0005C5E6
	cmp.w #$F,d0
	ble.b abs_0_0005C5F4
abs_0_0005C5E6:
	sf.b absolute_slot_000001E6.w
	clr.w absolute_slot_000001EA.w
	addq.w #1,absolute_slot_0000013C.w
abs_0_0005C5F2:
	rts
abs_0_0005C5F4:
	move.w d0,absolute_slot_000001E8.w
	lsl.w #5,d0
	tst.w absolute_slot_0000013C.w
	bne.b abs_0_0005C618
	lea.l absolute_slot_000009B0.l,a0
	lea.l absolute_slot_00003940.l,a1
	adda.w d0,a0
	moveq.l #15,d1
abs_0_0005C610:
	addq.w #2,a1
	move.w (a0)+,(a1)+
	dbf.w d1,abs_0_0005C610
abs_0_0005C618:
	lea.l absolute_slot_000007B0.l,a0
	movea.l absolute_slot_0000011A.w,a1
	adda.w d0,a0
	move.l a0,-(a7)
	moveq.l #15,d1
abs_0_0005C628:
	addq.w #2,a1
	move.w (a0)+,(a1)+
	dbf.w d1,abs_0_0005C628
	movea.l (a7)+,a0
	move.w $0018(a0),d0
	moveq.l #3,d1
abs_0_0005C638:
	addq.w #2,a1
	move.w d0,(a1)+
	dbf.w d1,abs_0_0005C638
	rts
abs_0_0005C642:
	lea.l absolute_slot_00003940.l,a0
	moveq.l #15,d7
	move.w #$5AF,d0
	bsr.w abs_0_0005C744
	move.l #$3D40,d0
	moveq.l #1,d6
	move.w #$120,d7
	move.w #$308,d5
	bsr.w abs_0_0005C72C
	move.l #$64446,d0
	moveq.l #5,d6
	move.w #$128,d7
	moveq.l #0,d5
	bsr.w abs_0_0005C72C
	move.l #$8E2C81,(a0)+
	move.l #$902FC1,(a0)+
	move.l #$920038,(a0)+
	move.l #$9400D0,(a0)+
	move.l #$10400FF,(a0)+
	move.l #$1020000,(a0)+
	move.l #$1080000,(a0)+
	move.l #$10A0000,(a0)+
	move.l #$305B0,d0
	moveq.l #3,d6
	move.w #$E0,d7
	move.l #$A00,d5
	bsr.w abs_0_0005C72C
	move.l #$1004200,(a0)+
	move.l #$6C01FF00,(a0)+
	move.l #$1000000,(a0)+
	move.l a0,absolute_slot_00000116.w
	move.l absolute_slot_0000012A.w,d0
	moveq.l #3,d6
	move.w #$E0,d7
	moveq.l #42,d5
	bsr.w abs_0_0005C72C
	move.l a0,absolute_slot_0000011A.w
	moveq.l #19,d7
	move.w #$5AF,d0
	bsr.w abs_0_0005C744
	move.l #$6D01FF00,(a0)+
	move.l #$1080080,(a0)+
	move.l #$10A0080,(a0)+
	move.l #$1004200,(a0)+
	move.l #$C001FF00,(a0)+
	move.w #$9C,(a0)+
	move.w #$8010,(a0)+
	move.l #$D001FF00,(a0)+
	move.w #$9C,(a0)+
	move.w #$8010,(a0)+
	moveq.l #-2,d0
	move.l d0,(a0)+
	rts
abs_0_0005C72C:
	move.w d7,(a0)+
	swap.w d0
	move.w d0,(a0)+
	swap.w d0
	addq.w #2,d7
	move.w d7,(a0)+
	move.w d0,(a0)+
	addq.w #2,d7
	add.l d5,d0
	dbf.w d6,abs_0_0005C72C
	rts
abs_0_0005C744:
	move.w #$180,d1
abs_0_0005C748:
	move.w d1,(a0)+
	move.w d0,(a0)+
	addq.w #2,d1
	dbf.w d7,abs_0_0005C748
	rts
abs_0_0005C754:
	lea.l _custom.l,a6
	cmpi.b #128,vhposr(a6)
	bne.b abs_0_0005C754
	move.l a0,cop1lc(a6)	; copper_list pointer $00003B40
	move.w copjmp1(a6),d0
	move.w #DMAF_SETCLR|DMAF_BLITHOG|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER|DMAF_SPRITE,dmacon(a6)
	rts
abs_0_0005C772:
	lea.l absolute_slot_00003D40.l,a0
	lea.l $0308(a0),a1
	clr.l (a0)+
	clr.l (a1)+
	move.w #$BF,d0
abs_0_0005C784:
	move.w #$8000,(a0)+
	clr.w (a0)+
	move.w #$1,(a1)+
	clr.w (a1)+
	dbf.w d0,abs_0_0005C784
	clr.l (a0)
	clr.l (a1)
	lea.l absolute_slot_00003D40.l,a1
	move.w #$0,d1
	move.w #$42,d2
	move.w #$C0,d3
	bsr.b abs_0_0005C7C2
	lea.l absolute_slot_00004048.l,a1
	move.w #$130,d1
	move.w #$42,d2
	move.w #$C0,d3
	bsr.b abs_0_0005C7C2
	rts
abs_0_0005C7C2:
	movem.l d0-d3/a1,-(a7)
	addi.w #128,d1
	addi.w #44,d2
	moveq.l #0,d0
	move.b d2,(a1)+
	cmp.w #$100,d2
	blt.b abs_0_0005C7DA
	addq.w #4,d0
abs_0_0005C7DA:
	add.w d3,d2
	cmp.w #$100,d2
	blt.b abs_0_0005C7E4
	addq.w #2,d0
abs_0_0005C7E4:
	lsr.w #1,d1
	bcc.b abs_0_0005C7EA
	addq.w #1,d0
abs_0_0005C7EA:
	move.b d1,(a1)+
	move.b d2,(a1)+
	move.b d0,(a1)+
	movem.l (a7)+,d0-d3/a1
	rts
abs_0_0005C7F6:
	movem.l d4-d5,-(a7)
	move.w d0,d5
	move.w d5,d4
	subq.w #1,d4
	move.l absolute_slot_00000122.w,d0
abs_0_0005C804:
	add.l d0,d0
	bhi.b abs_0_0005C80E
	eori.l #495397697,d0
abs_0_0005C80E:
	lsr.w #1,d4
	bne.b abs_0_0005C804
	move.l d0,absolute_slot_00000122.w
	tst.w d5
	bne.b abs_0_0005C81E
	swap.w d0
	bra.b abs_0_0005C820
abs_0_0005C81E:
	mulu.w d5,d0
abs_0_0005C820:
	clr.w d0
	swap.w d0
	movem.l (a7)+,d4-d5
	rts
abs_0_0005C82A:
	lea.l absolute_slot_00C00000.l,a0
	bsr.b abs_0_0005C854
	tst.w d0
	bne.b abs_0_0005C852
	lea.l absolute_slot_00080000.l,a0
	bsr.b abs_0_0005C854
	tst.w d0
	bne.b abs_0_0005C852
	lea.l absolute_slot_00200000.l,a0
	bsr.b abs_0_0005C854
	tst.w d0
	bne.b abs_0_0005C852
	clr.l absolute_slot_0000011E.w
abs_0_0005C852:
	rts
abs_0_0005C854:
	clr.l $0000.w
	cmpi.l #1145392161,(a0)
	beq.b abs_0_0005C886
	move.l #$44454C21,(a0)
	cmpi.l #1145392161,$0000.w
	beq.b abs_0_0005C878
	cmpi.l #1145392161,(a0)
	beq.b abs_0_0005C882
abs_0_0005C878:
	move.l m68k_vector_trap_1_instruction_vector.w,m68k_vector_trap_2_instruction_vector.w
	moveq.l #0,d0
	rts
abs_0_0005C882:
	clr.w $0004(a0)
abs_0_0005C886:
	addq.w #4,a0
	move.l a0,absolute_slot_0000011E.w
	lea.l abs_0_0005C898(pc),a0
	move.l a0,m68k_vector_trap_2_instruction_vector.w
	moveq.l #1,d0
	rts
abs_0_0005C898:
	movem.l d2-d7/a0-a6,-(a7)
	movea.l absolute_slot_0000011E.w,a2
	move.w (a2)+,d1
	beq.b abs_0_0005C8CC
abs_0_0005C8A4:
	movea.l a2,a3
	movea.l a0,a4
abs_0_0005C8A8:
	move.b (a4)+,d0
	beq.b abs_0_0005C8BA
	cmp.b (a3)+,d0
	beq.b abs_0_0005C8A8
	subq.w #1,d1
	beq.b abs_0_0005C8CC
	movea.l $001C(a2),a2
	bra.b abs_0_0005C8A4
abs_0_0005C8BA:
	move.l $0018(a2),d0
	move.l d0,d1
	lea.l $0020(a2),a2
abs_0_0005C8C4:
	move.b (a2)+,(a1)+
	subq.l #1,d0
	bne.b abs_0_0005C8C4
	bra.b abs_0_0005C928
abs_0_0005C8CC:
	trap #1
	tst.w d0
	beq.b abs_0_0005C8EC
abs_0_0005C8D2:
	clr.w _custom+color.l	; palette color 0
	move.w #$F00,_custom+color.l
	btst.b #CIAB_GAMEPORT0,_ciaa+ciapra.l
	bne.b abs_0_0005C8D2
	bra.b abs_0_0005C928
abs_0_0005C8EC:
	movem.l (a7),d2-d7/a0-a6
	movea.l absolute_slot_0000011E.w,a3
	move.w (a3)+,d0
	beq.b abs_0_0005C900
abs_0_0005C8F8:
	movea.l $001C(a3),a3
	subq.w #1,d0
	bne.b abs_0_0005C8F8
abs_0_0005C900:
	movea.l a3,a2
abs_0_0005C902:
	move.b (a0)+,d7
	beq.b abs_0_0005C90A
	move.b d7,(a2)+
	bra.b abs_0_0005C902
abs_0_0005C90A:
	lea.l $0018(a3),a2
	move.l d1,(a2)+
	move.l d1,-(a7)
	adda.l d1,a3
	adda.w #$20,a3
	move.l a3,(a2)+
abs_0_0005C91A:
	move.b (a1)+,(a2)+
	subq.l #1,d1
	bne.b abs_0_0005C91A
	move.l (a7)+,d1
	movea.l absolute_slot_0000011E.w,a0
	addq.w #1,(a0)
abs_0_0005C928:
	movem.l (a7)+,d2-d7/a0-a6
	rte
abs_0_0005C92E:
	lea.l abs_0_0005C938(pc),a0
	move.l a0,m68k_vector_trap_3_instruction_vector.w
	rts
abs_0_0005C938:
	move.l a1,-(a7)
	trap #2
	movea.l (a7)+,a0
	cmpi.l #1296843843,(a0)
	bne.b abs_0_0005C94E
	movea.l a0,a3
	move.l d1,d0
	bsr.w abs_0_000647F2
abs_0_0005C94E:
	rte
abs_0_0005C950:
	movea.l absolute_slot_0000012A.w,a0
	movea.l absolute_slot_00000126.w,a1
	move.w #$1F7F,d0
abs_0_0005C95C:
	clr.l (a0)+
	clr.l (a1)+
	dbf.w d0,abs_0_0005C95C
	rts
abs_0_0005C966:
	lea.l abs_0_000621F0(pc),a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	lea.l abs_0_000621F5(pc),a0
	lea.l absolute_slot_00000990.w,a1
	trap #3
	rts
abs_0_0005C97E:
	clr.w absolute_slot_0000024A.w
	clr.w absolute_slot_00000276.w
	clr.w absolute_slot_00000294.w
	clr.l absolute_slot_00000300.w
	clr.l absolute_slot_00000304.w
abs_0_0005C992:
	clr.b m68k_vector_trap_4_instruction_vector.w
	clr.w absolute_slot_00000154.w
	clr.w absolute_slot_00000158.w
	clr.w absolute_slot_0000015A.w
	clr.w absolute_slot_0000015C.w
	clr.w absolute_slot_0000015E.w
	move.w #$1,absolute_slot_0000023A.w
	clr.l absolute_slot_00000182.w
	bsr.w abs_0_0005D326
	bsr.w abs_0_0005E514
	bsr.w abs_0_0005F502
	lea.l absolute_slot_00026F50.l,a0
	move.w absolute_slot_000001DE.w,d0
	cmp.w #$38,d0
	ble.b abs_0_0005C9D2
	moveq.l #56,d0
abs_0_0005C9D2:
	mulu.w #$1E0,d0
	adda.w d0,a0
	move.l a0,absolute_slot_000001E0.w
	moveq.l #-1,d0
	move.l d0,bltafwm(a6)
	clr.w bltamod(a6)
	move.w #$28,bltdmod(a6)
	move.l #$9F00000,bltcon0(a6)
	movea.l absolute_slot_0000012A.w,a2
	move.w #$1001,d3
	moveq.l #11,d2
abs_0_0005C9FE:
	moveq.l #19,d0
abs_0_0005CA00:
	moveq.l #0,d1
	move.w (a0)+,d1
	lea.l absolute_slot_00006F50.l,a4
	lsl.l #7,d1
	adda.l d1,a4
	move.l a4,bltapt(a6)	; blitter_source pointer
	move.l a2,bltdpt(a6)	; blitter_destination pointer
	move.w d3,bltsize(a6)
	addq.w #2,a2
abs_0_0005CA1C:
	btst.b #DMAB_BLITTER,dmaconr(a6)
	bne.b abs_0_0005CA1C
	dbf.w d0,abs_0_0005CA00
	adda.w #$A58,a2
	dbf.w d2,abs_0_0005C9FE
	bsr.w abs_0_0005CAE0
	movea.l absolute_slot_0000012A.w,a0
	lea.l absolute_slot_000680AA.l,a1
	bsr.b abs_0_0005CAAA
	bsr.w abs_0_0005CEDE
	bsr.w abs_0_0005CEFA
	bsr.w abs_0_0005CEFA
	bsr.w abs_0_0005D5DC
	bsr.w abs_0_0005F436
	bsr.w abs_0_0005D74E
	move.l #abs_0_0005C2F8,absolute_slot_00000138.w
	lea.l abs_0_000624F0(pc),a0
	move.w absolute_slot_000001DE.w,d0
	add.w d0,d0
	add.w d0,d0
	movea.l $0(a0,d0.w),a0
	cmpa.l #$0,a0
	beq.b abs_0_0005CA7A
	jsr (a0)
abs_0_0005CA7A:
	bsr.w abs_0_0005E562
	bsr.w abs_0_0005D4DA
	movea.l absolute_slot_00000138.w,a0
	jsr (a0)
	movea.l absolute_slot_00000132.w,a0
	movea.l absolute_slot_0000012E.w,a1
	move.w #$FF,d0
abs_0_0005CA94:
	move.l (a0)+,(a1)+
	dbf.w d0,abs_0_0005CA94
	movea.l absolute_slot_0000012A.w,a0
	movea.l absolute_slot_00000126.w,a1
	bsr.b abs_0_0005CAAA
	clr.w absolute_slot_0000023A.w
	rts
abs_0_0005CAAA:
	moveq.l #-1,d0
	move.l d0,bltafwm(a6)
	clr.w bltamod(a6)
	move.l #$9F00000,bltcon0(a6)
	clr.w bltdmod(a6)
	suba.w #$A8,a1
	move.l a1,bltdpt(a6)	; blitter_destination pointer
	suba.w #$A8,a0
	move.l a0,bltapt(a6)	; blitter_source pointer
	move.w #(388<<6)|42,bltsize(a6)	; blitter size 388 rows x 42 words (84 bytes/row)
abs_0_0005CAD6:
	btst.b #DMAB_BLITTER,dmaconr(a6)
	bne.b abs_0_0005CAD6
	rts
abs_0_0005CAE0:
	movea.l absolute_slot_0000012A.w,a0
	suba.w #$A8,a0
	movea.l a0,a1
	adda.l #$7EA8,a1
	moveq.l #19,d0
abs_0_0005CAF2:
	move.w #$0,(a0)
	move.w #$0,$002A(a0)
	move.w #$FFFF,$0054(a0)
	move.w #$FFFF,$007E(a0)
	move.w #$0,(a1)
	move.w #$0,$002A(a1)
	move.w #$FFFF,$0054(a1)
	move.w #$FFFF,$007E(a1)
	addq.w #2,a0
	addq.w #2,a1
	dbf.w d0,abs_0_0005CAF2
	rts
abs_0_0005CB28:
	lea.l abs_0_00062205(pc),a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	lea.l abs_0_00064CD8.l,a0
	lea.l absolute_slot_00032DD0.l,a2
	lea.l absolute_slot_0004B470.l,a3
	lea.l absolute_slot_0002F490.l,a4
	bsr.w abs_0_0005CB8E
	movem.l a0-a4,-(a7)
	lea.l abs_0_00062212(pc),a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	movem.l (a7)+,a0-a4
	bsr.w abs_0_0005CB8E
	movem.l a0-a4,-(a7)
	lea.l abs_0_0006221F(pc),a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	movem.l (a7)+,a0-a4
	bsr.w abs_0_0005CB8E
	suba.l #$32DD0,a2
	suba.l #$4B470,a3
	rts
abs_0_0005CB8E:
	cmpi.w #$FFFF,(a0)
	beq.w abs_0_0005CC58
	move.l a2,$0000(a4)
	move.l a3,$0004(a4)
	lea.l absolute_slot_00006F50.l,a1
	move.w $0000(a0),d1
	adda.w d1,a1
	move.w $0002(a0),d1
	mulu.w #$28,d1
	adda.w d1,a1
	move.w $0006(a0),d2
	subq.w #1,d2
abs_0_0005CBBA:
	move.l a1,-(a7)
	move.l a2,-(a7)
	move.l a3,-(a7)
	move.w $0004(a0),d1
	move.w d1,d7
	add.w d7,d7
	move.w $0006(a0),d6
	mulu.w d6,d7
	subq.w #1,d1
abs_0_0005CBD0:
	move.w (a1),d3
	move.w $2800(a1),d4
	move.w $5000(a1),d5
	move.w $7800(a1),d6
	move.l a2,-(a7)
	move.w d3,(a2)
	adda.w d7,a2
	move.w d4,(a2)
	adda.w d7,a2
	move.w d5,(a2)
	adda.w d7,a2
	move.w d6,(a2)
	movea.l (a7)+,a2
	or.w d3,d4
	or.w d4,d5
	or.w d5,d6
	movea.l a1,a5
	adda.l #$A000,a5
	or.w (a5),d6
	move.w d6,(a3)
	addq.w #2,a1
	addq.w #2,a2
	addq.w #2,a3
	dbf.w d1,abs_0_0005CBD0
	movea.l (a7)+,a3
	movea.l (a7)+,a2
	movea.l (a7)+,a1
	lea.l $0028(a1),a1
	move.w $0004(a0),d7
	add.w d7,d7
	adda.w d7,a2
	adda.w d7,a3
	dbf.w d2,abs_0_0005CBBA
	move.w $0006(a0),d6
	mulu.w d6,d7
	mulu.w #$3,d7
	adda.w d7,a2
	move.w $0004(a0),$000C(a4)
	move.w $0006(a0),$000E(a4)
	move.w $0004(a0),d7
	add.w d7,d7
	move.w $0006(a0),d6
	mulu.w d6,d7
	move.w d7,$0008(a4)
	lea.l $0008(a0),a0
	lea.l $0010(a4),a4
	bra.w abs_0_0005CB8E
abs_0_0005CC58:
	addq.w #2,a0
	rts
abs_0_0005CC5C:
	lea.l absolute_slot_0002F490.l,a0
	lsl.w #4,d2
	adda.w d2,a0
	lea.l absolute_slot_00000BB0.w,a1
	movea.l $0000(a0),a3
	movea.l $0004(a0),a4
	move.w $000C(a0),d2
	move.w $000E(a0),d3
	moveq.l #-2,d4
	move.w #$A8,d5
	move.w d2,d7
	addq.w #1,d7
	add.w d7,d7
	sub.w d7,d5
	tst.w d1
	bge.b abs_0_0005CCA2
	neg.w d1
	sub.w d1,d3
	ble.w abs_0_0005CD9C
	move.w $000C(a0),d7
	add.w d7,d7
	mulu.w d1,d7
	adda.w d7,a3
	adda.w d7,a4
	moveq.l #0,d1
abs_0_0005CCA2:
	move.w d1,d7
	add.w d3,d7
	cmp.w #$BF,d7
	ble.b abs_0_0005CCB6
	subi.w #192,d7
	sub.w d7,d3
	ble.w abs_0_0005CD9C
abs_0_0005CCB6:
	move.w d0,d7
	cmp.w #$FFF1,d7
	bge.b abs_0_0005CCD8
	neg.w d7
	lsr.w #4,d7
	sub.w d7,d2
	ble.w abs_0_0005CD9C
	add.w d7,d7
	add.w d7,d4
	add.w d7,d5
	adda.w d7,a3
	adda.w d7,a4
	subq.w #1,d0
	ori.w #65520,d0
abs_0_0005CCD8:
	move.w d0,d7
	asr.w #4,d7
	add.w d2,d7
	cmp.w #$13,d7
	ble.b abs_0_0005CCF4
	subi.w #20,d7
	sub.w d7,d2
	ble.w abs_0_0005CD9C
	add.w d7,d7
	add.w d7,d4
	add.w d7,d5
abs_0_0005CCF4:
	add.w d1,d1
	move.w $0(a1,d1.w),d1
	move.w d0,d6
	asr.w #4,d0
	add.w d0,d0
	add.w d0,d1
	movea.l absolute_slot_0000012A.w,a2
	adda.w d1,a2
	movea.l absolute_slot_00000132.w,a5
abs_0_0005CD0C:
	cmpi.l #$FFFFFFFF,(a5)
	beq.b abs_0_0005CD18
	addq.w #8,a5
	bra.b abs_0_0005CD0C
abs_0_0005CD18:
	move.l #$FFFFFFFF,$0008(a5)
	clr.w $0000(a5)
	move.w d1,$0002(a5)
	move.l #$FFFF0000,bltafwm(a6)
	move.w d4,bltamod(a6)
	move.w d4,bltbmod(a6)
	move.w d5,bltcmod(a6)
	move.w d5,bltdmod(a6)
	subi.w #126,d5
	move.w d5,$0006(a5)
	andi.w #15,d6
	add.w d6,d6
	add.w d6,d6
	move.l abs_0_0005CD9E(pc,d6.w),bltcon0(a6)
	move.w d3,d4
	add.w d4,d4
	move.w d2,d5
	addq.w #1,d5
	move.w abs_0_0005CDDE(pc,d4.w),d4
	move.w d4,d0
	or.w d5,d4
	move.w $0008(a0),d6
	moveq.l #3,d7
abs_0_0005CD6C:
	move.l a4,bltapt(a6)	; blitter_source pointer
	move.l a3,bltbpt(a6)	; blitter_source pointer
	move.l a2,bltcpt(a6)	; blitter_source pointer
	move.l a2,bltdpt(a6)	; blitter_destination pointer
	move.w d4,bltsize(a6)
abs_0_0005CD80:
	btst.b #DMAB_BLITTER,dmaconr(a6)
	bne.b abs_0_0005CD80
	adda.w #$2A,a2
	adda.w d6,a3
	dbf.w d7,abs_0_0005CD6C
	add.w d0,d0
	add.w d0,d0
	or.w d5,d0
	move.w d0,$0004(a5)
abs_0_0005CD9C:
	rts
abs_0_0005CD9E:
	dc.l $0FCA0000,$1FCA1000,$2FCA2000,$3FCA3000	; lookup_table
	dc.l $4FCA4000,$5FCA5000,$6FCA6000,$7FCA7000	; lookup_table
	dc.l $8FCA8000,$9FCA9000,$AFCAA000,$BFCAB000	; lookup_table
	dc.l $CFCAC000,$DFCAD000,$EFCAE000,$FFCAF000	; lookup_table
abs_0_0005CDDE:
	dc.w $0000,$0040,$0080,$00C0,$0100,$0140,$0180,$01C0	; lookup_table
	dc.w $0200,$0240,$0280,$02C0,$0300,$0340,$0380,$03C0	; lookup_table
	dc.w $0400,$0440,$0480,$04C0,$0500,$0540,$0580,$05C0	; lookup_table
	dc.w $0600,$0640,$0680,$06C0,$0700,$0740,$0780,$07C0	; lookup_table
	dc.w $0800,$0840,$0880,$08C0,$0900,$0940,$0980,$09C0	; lookup_table
	dc.w $0A00,$0A40,$0A80,$0AC0,$0B00,$0B40,$0B80,$0BC0	; lookup_table
	dc.w $0C00,$0C40,$0C80,$0CC0,$0D00,$0D40,$0D80,$0DC0	; lookup_table
	dc.w $0E00,$0E40,$0E80,$0EC0,$0F00,$0F40,$0F80,$0FC0	; lookup_table
	dc.w $1000,$1040,$1080,$10C0,$1100,$1140,$1180,$11C0	; lookup_table
	dc.w $1200,$1240,$1280,$12C0,$1300,$1340,$1380,$13C0	; lookup_table
	dc.w $1400,$1440,$1480,$14C0,$1500,$1540,$1580,$15C0	; lookup_table
	dc.w $1600,$1640,$1680,$16C0,$1700,$1740,$1780,$17C0	; lookup_table
	dc.w $1800,$1840,$1880,$18C0,$1900,$1940,$1980,$19C0	; lookup_table
	dc.w $1A00,$1A40,$1A80,$1AC0,$1B00,$1B40,$1B80,$1BC0	; lookup_table
	dc.w $1C00,$1C40,$1C80,$1CC0,$1D00,$1D40,$1D80,$1DC0	; lookup_table
	dc.w $1E00,$1E40,$1E80,$1EC0,$1F00,$1F40,$1F80,$1FC0	; lookup_table
abs_0_0005CEDE:
	move.l #$FFFFFFFF,absolute_slot_00000D40.l
	move.l #$FFFFFFFF,absolute_slot_00001140.l
	move.w #$2,absolute_slot_00000136.w
	rts
abs_0_0005CEFA:
	tst.w absolute_slot_00000136.w
	beq.b abs_0_0005CF06
	subq.w #1,absolute_slot_00000136.w
	rts
abs_0_0005CF06:
	moveq.l #-1,d0
	move.l d0,$0044(a6)
	move.l #$9F00000,$0040(a6)
	movea.l absolute_slot_00000132.w,a0
abs_0_0005CF18:
	move.l (a0),d0
	cmp.l #$FFFFFFFF,d0
	beq.b abs_0_0005CF5C
	move.l #$FFFFFFFF,(a0)
	lea.l absolute_slot_000680AA.l,a1
	movea.l absolute_slot_0000012A.w,a2
	adda.w d0,a1
	adda.w d0,a2
	move.l a1,$0050(a6)
	move.l a2,$0054(a6)
	move.w $0006(a0),$0064(a6)
	move.w $0006(a0),$0066(a6)
	move.w $0004(a0),$0058(a6)
	addq.w #8,a0
abs_0_0005CF52:
	btst.b #6,$0002(a6)
	bne.b abs_0_0005CF52
	bra.b abs_0_0005CF18
abs_0_0005CF5C:
	rts
abs_0_0005CF5E:
	lea.l absolute_slot_00006F50.l,a0
	lea.l absolute_slot_00001940.l,a1
	lea.l absolute_slot_00002940.l,a2
	move.w #$3FF,d0
abs_0_0005CF74:
	move.l a0,(a1)+
	move.l a0,(a2)+
	adda.w #$80,a0
	dbf.w d0,abs_0_0005CF74
	rts
abs_0_0005CF82:
	lea.l abs_0_0005CFD2(pc),a0
	lea.l absolute_slot_00001940.l,a1
	lea.l absolute_slot_00002940.l,a2
abs_0_0005CF92:
	move.l (a0)+,d0
	bmi.b abs_0_0005CFD0
	add.w d0,d0
	add.w d0,d0
	movea.l (a0)+,a5
	lea.l $0006(a5),a4
	move.w (a5),d1
	move.w $0002(a5),d2
	subq.w #1,d2
	bge.b abs_0_0005CFCA
	move.w d1,d2
	move.w $0004(a5),d1
	addq.w #2,d1
abs_0_0005CFB2:
	move.w $0(a4,d1.w),d3
	bge.b abs_0_0005CFBC
	moveq.l #0,d1
	bra.b abs_0_0005CFB2
abs_0_0005CFBC:
	move.w d1,$0004(a5)
	add.w d3,d3
	add.w d3,d3
	move.l $0(a2,d3.w),$0(a1,d0.w)
abs_0_0005CFCA:
	move.w d2,$0002(a5)
	bra.b abs_0_0005CF92
abs_0_0005CFD0:
	rts
abs_0_0005CFD2:
	dc.b $00,$00,$00,$0F,$00,$05,$D0,$46,$00,$00,$01,$ED,$00,$05,$D0,$56
	dc.b $00,$00,$01,$EA,$00,$05,$D0,$66,$00,$00,$02,$B4,$00,$05,$D0,$76
	dc.b $00,$00,$02,$B5,$00,$05,$D0,$86,$00,$00,$02,$B6,$00,$05,$D0,$96
	dc.b $00,$00,$02,$B7,$00,$05,$D0,$A6,$00,$00,$01,$AC,$00,$05,$D0,$B6
	dc.b $00,$00,$01,$AD,$00,$05,$D0,$C2,$00,$00,$01,$AE,$00,$05,$D0,$CE
	dc.b $00,$00,$01,$E0,$00,$05,$D0,$DA,$00,$00,$02,$57,$00,$05,$D1,$12
	dc.b $00,$00,$02,$D2,$00,$05,$D0,$F2,$00,$00,$03,$FC,$00,$05,$D1,$02
	dc.b $FF,$FF,$FF,$FF,$00,$04,$00,$00,$00,$00,$00,$0F,$00,$C7,$00,$D7
	dc.b $00,$E7,$FF,$FF,$00,$04,$00,$00,$00,$00,$01,$ED,$00,$F3,$00,$F7
	dc.b $00,$0E,$FF,$FF,$00,$04,$00,$00,$00,$00,$01,$EA,$00,$D1,$00,$D3
	dc.b $00,$F1,$FF,$FF,$00,$04,$00,$00,$00,$00,$02,$B4,$02,$C4,$02,$D4
	dc.b $02,$E4,$FF,$FF,$00,$04,$00,$00,$00,$00,$02,$B5,$02,$C5,$02,$D5
	dc.b $02,$E5,$FF,$FF,$00,$04,$00,$00,$00,$00,$02,$B6,$02,$C6,$02,$D6
	dc.b $02,$E6,$FF,$FF,$00,$04,$00,$00,$00,$00,$02,$B7,$02,$C7,$02,$D7
	dc.b $02,$E7,$FF,$FF,$00,$06,$00,$00,$00,$00,$01,$AC,$02,$F5,$FF,$FF
	dc.b $00,$06,$00,$00,$00,$00,$01,$AD,$02,$F6,$FF,$FF,$00,$06,$00,$00
	dc.b $00,$00,$01,$AE,$02,$F7,$FF,$FF,$00,$05,$00,$00,$00,$00,$01,$9D
	dc.b $01,$E0,$01,$FF,$01,$EF,$00,$7D,$01,$EF,$01,$FF,$01,$E0,$FF,$FF
	dc.b $00,$04,$00,$00,$00,$00,$02,$D2,$02,$D3,$02,$E2,$02,$E3,$FF,$FF
	dc.b $00,$04,$00,$00,$00,$00,$03,$EC,$03,$ED,$03,$FC,$03,$FD,$FF,$FF
	dc.b $00,$04,$00,$00,$00,$00,$02,$56,$02,$57,$03,$F7,$03,$F8,$FF,$FF
abs_0_0005D122:
	lea.l absolute_slot_00001540.w,a0
	moveq.l #1,d0
	move.b d0,$000F(a0)
	move.b d0,$01AC(a0)
	move.b d0,$01AD(a0)
	move.b d0,$01AE(a0)
	move.b d0,$01E0(a0)
	move.b d0,$01EA(a0)
	move.b d0,$01ED(a0)
	move.b d0,$0257(a0)
	move.b d0,$02B4(a0)
	move.b d0,$02B5(a0)
	move.b d0,$02B6(a0)
	move.b d0,$02B7(a0)
	move.b d0,$02D2(a0)
	move.b d0,$03FC(a0)
	rts
abs_0_0005D162:
	movea.l absolute_slot_000001E0.w,a0
	moveq.l #-1,d0
	move.l d0,bltafwm(a6)
	clr.w bltamod(a6)
	move.w #$28,bltdmod(a6)
	move.l #$9F00000,bltcon0(a6)
	lea.l absolute_slot_00001540.w,a1
	movea.l absolute_slot_0000012A.w,a2
	move.l a2,bltdpt(a6)	; blitter_destination pointer
	lea.l absolute_slot_00001940.w,a3
	move.w #$1001,d3
	lea.l bltsize(a6),a4
	lea.l bltapt(a6),a5
	moveq.l #11,d2
abs_0_0005D19C:
	moveq.l #19,d0
abs_0_0005D19E:
	move.w (a0)+,d1
	tst.b $0(a1,d1.w)
	beq.b abs_0_0005D1BC
	add.w d1,d1
	add.w d1,d1
	move.l $0(a3,d1.w),(a5)
	move.w a2,bltdpt+$02(a6)
	move.w d3,(a4)
abs_0_0005D1B4:
	btst.b #DMAB_BLITTER,dmaconr(a6)
	bne.b abs_0_0005D1B4
abs_0_0005D1BC:
	addq.w #2,a2
	dbf.w d0,abs_0_0005D19E
	lea.l $0A58(a2),a2
	dbf.w d2,abs_0_0005D19C
	rts
abs_0_0005D1CC:
	lea.l abs_0_00062247(pc),a0
	lea.l absolute_slot_0002E6B0.l,a1
	trap #3
	lea.l abs_0_0006222C(pc),a0
	lea.l absolute_slot_000305B0.l,a1
	trap #3
	lea.l absolute_slot_00032DB0.l,a0
	lea.l absolute_slot_00000B90.l,a1
	moveq.l #15,d0
abs_0_0005D1F2:
	move.w (a0)+,(a1)+
	dbf.w d0,abs_0_0005D1F2
	rts
abs_0_0005D1FA:
	lea.l abs_0_00062236(pc),a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	lea.l absolute_slot_00006F50.l,a0
	lea.l absolute_slot_0002DA30.l,a1
	lea.l absolute_slot_0002E430.l,a2
	moveq.l #1,d1
abs_0_0005D21A:
	moveq.l #39,d2
abs_0_0005D21C:
	moveq.l #7,d0
abs_0_0005D21E:
	move.b (a0),(a1)+
	move.b $0280(a0),(a1)+
	move.b $0500(a0),(a1)+
	move.b $0780(a0),(a1)+
	move.b (a0),d3
	or.b $0280(a0),d3
	or.b $0500(a0),d3
	or.b $0780(a0),d3
	not.b d3
	move.b d3,(a2)+
	lea.l $0028(a0),a0
	dbf.w d0,abs_0_0005D21E
	suba.w #$13F,a0
	dbf.w d2,abs_0_0005D21C
	adda.w #$118,a0
	dbf.w d1,abs_0_0005D21A
	rts
abs_0_0005D258:
	move.w #$3,absolute_slot_00000170.w
	move.w #$3F,absolute_slot_00000172.w
	clr.w absolute_slot_00000174.w
	clr.l absolute_slot_00000176.w
	st.b absolute_slot_0000017E.w
	st.b absolute_slot_00000180.w
	st.b absolute_slot_00000181.w
	st.b absolute_slot_0000017F.w
	rts
abs_0_0005D27E:
	tst.b absolute_slot_00000180.w
	beq.b abs_0_0005D2A8
	move.w absolute_slot_00000170.w,d7
	moveq.l #15,d0
	move.w #$410,d1
	moveq.l #2,d6
abs_0_0005D290:
	moveq.l #38,d2
	tst.w d7
	beq.b abs_0_0005D29A
	subq.w #1,d7
	moveq.l #39,d2
abs_0_0005D29A:
	bsr.w abs_0_0005D4AC
	addq.w #1,d0
	dbf.w d6,abs_0_0005D290
	sf.b absolute_slot_00000180.w
abs_0_0005D2A8:
	rts
abs_0_0005D2AA:
	tst.b absolute_slot_00000181.w
	beq.b abs_0_0005D2D8
	move.l absolute_slot_00000176.w,d3
	rol.l #8,d3
	moveq.l #8,d0
	move.w #$410,d1
	moveq.l #5,d4
abs_0_0005D2BE:
	rol.l #4,d3
	move.l d3,d2
	andi.w #15,d2
	addi.w #26,d2
	bsr.w abs_0_0005D4AC
	addq.w #1,d0
	dbf.w d4,abs_0_0005D2BE
	sf.b absolute_slot_00000181.w
abs_0_0005D2D8:
	rts
abs_0_0005D2DA:
	tst.b absolute_slot_0000017F.w
	beq.b abs_0_0005D324
	lea.l abs_0_000622DC(pc),a2
	move.w absolute_slot_00000174.w,d3
	andi.w #31,d3
	add.w d3,d3
	move.w $0(a2,d3.w),d3
	moveq.l #21,d0
	move.w #$438,d1
	move.w d3,d2
	andi.w #255,d2
	subi.w #48,d2
	addi.w #26,d2
	bsr.w abs_0_0005D4AC
	subq.w #1,d0
	lsr.w #8,d3
	move.w d3,d2
	andi.w #255,d2
	subi.w #48,d2
	addi.w #26,d2
	bsr.w abs_0_0005D4AC
	sf.b absolute_slot_0000017F.w
abs_0_0005D324:
	rts
abs_0_0005D326:
	lea.l abs_0_000625F0(pc),a3
	move.w absolute_slot_000001DE.w,d0
	cmp.w #$38,d0
	ble.b abs_0_0005D336
	moveq.l #56,d0
abs_0_0005D336:
	mulu.w #$17,d0
	adda.w d0,a3
	moveq.l #8,d0
	move.w #$668,d1
	lea.l abs_0_00062280(pc),a2
	moveq.l #22,d7
abs_0_0005D348:
	moveq.l #0,d2
	move.b (a3)+,d2
	subi.w #32,d2
	move.b $0(a2,d2.w),d2
	bsr.w abs_0_0005D4AC
	addq.w #1,d0
	dbf.w d7,abs_0_0005D348
	rts
abs_0_0005D360:
	not.w absolute_slot_00000224.w
	bne.w abs_0_0005D3D6
	lea.l absolute_slot_0002E6B4.l,a0
	cmpi.w #4,absolute_slot_00000220.w
	bge.b abs_0_0005D37A
	lea.l $01B8(a0),a0
abs_0_0005D37A:
	lea.l absolute_slot_00030943.l,a1
	moveq.l #10,d0
abs_0_0005D382:
	move.b $0A50(a0),$1E00(a1)
	move.b $06E0(a0),$1400(a1)
	move.b $0370(a0),$0A00(a1)
	move.b (a0)+,(a1)+
	move.b $0A50(a0),$1E00(a1)
	move.b $06E0(a0),$1400(a1)
	move.b $0370(a0),$0A00(a1)
	move.b (a0)+,(a1)+
	lea.l $0026(a0),a0
	lea.l $0026(a1),a1
	dbf.w d0,abs_0_0005D382
	tst.w absolute_slot_00000220.w
	bne.b abs_0_0005D3D0
	move.w #$1FF,d0
	bsr.w abs_0_0005C7F6
	andi.w #15,d0
	addq.w #5,d0
	lsl.w #2,d0
	move.w d0,absolute_slot_00000220.w
abs_0_0005D3D0:
	subq.w #1,absolute_slot_00000220.w
	rts
abs_0_0005D3D6:
	lea.l absolute_slot_0002E6B0.l,a0
	cmpi.w #4,absolute_slot_00000222.w
	bge.b abs_0_0005D3E8
	lea.l $01B8(a0),a0
abs_0_0005D3E8:
	lea.l absolute_slot_000308D3.l,a1
	moveq.l #10,d0
abs_0_0005D3F0:
	move.b $0A50(a0),$1E00(a1)
	move.b $06E0(a0),$1400(a1)
	move.b $0370(a0),$0A00(a1)
	move.b (a0)+,(a1)+
	move.b $0A50(a0),$1E00(a1)
	move.b $06E0(a0),$1400(a1)
	move.b $0370(a0),$0A00(a1)
	move.b (a0)+,(a1)+
	move.b $0A50(a0),$1E00(a1)
	move.b $06E0(a0),$1400(a1)
	move.b $0370(a0),$0A00(a1)
	move.b (a0)+,(a1)+
	move.b $0A50(a0),$1E00(a1)
	move.b $06E0(a0),$1400(a1)
	move.b $0370(a0),$0A00(a1)
	move.b (a0)+,(a1)+
	lea.l $0024(a0),a0
	lea.l $0024(a1),a1
	dbf.w d0,abs_0_0005D3F0
	tst.w absolute_slot_00000222.w
	bne.b abs_0_0005D466
	move.w #$1FF,d0
	bsr.w abs_0_0005C7F6
	andi.w #15,d0
	addq.w #5,d0
	lsl.w #2,d0
	move.w d0,absolute_slot_00000222.w
abs_0_0005D466:
	subq.w #1,absolute_slot_00000222.w
	rts
abs_0_0005D46C:
	movem.l d0/a0-a1,-(a7)
	lea.l absolute_slot_0000017A.w,a1
	movea.l a1,a0
	move.l d0,(a0)+
	abcd -(a0),-(a1)
	abcd -(a0),-(a1)
	abcd -(a0),-(a1)
	abcd -(a0),-(a1)
	movem.l (a7)+,d0/a0-a1
	st.b absolute_slot_00000181.w
	rts
abs_0_0005D48A:
	tst.b absolute_slot_00000142.w
	bne.b abs_0_0005D49A
	add.w d0,$0170.w
	bmi.b abs_0_0005D49A
	st.b absolute_slot_00000180.w
abs_0_0005D49A:
	rts
abs_0_0005D49C:
	addq.w #1,absolute_slot_00000174.w
	st.b absolute_slot_0000017F.w
	moveq.l #20,d0
	bsr.w abs_0_0005FA82
	rts
abs_0_0005D4AC:
	lea.l absolute_slot_000305B0.l,a0
	lea.l absolute_slot_0002DA30.l,a1
	adda.w d0,a0
	adda.w d1,a0
	lsl.w #5,d2
	adda.w d2,a1
	moveq.l #7,d2
abs_0_0005D4C2:
	move.b (a1)+,(a0)
	move.b (a1)+,$0A00(a0)
	move.b (a1)+,$1400(a0)
	move.b (a1)+,$1E00(a0)
	lea.l $0028(a0),a0
	dbf.w d2,abs_0_0005D4C2
	rts
abs_0_0005D4DA:
	move.w absolute_slot_0000018C.w,d0
	move.w absolute_slot_0000018E.w,d1
	subi.w #22,d1
	move.w absolute_slot_00000190.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005D4F0:
	cmpi.w #50,absolute_slot_000001C2.w
	bge.b abs_0_0005D4FC
	addq.w #3,absolute_slot_000001C2.w
abs_0_0005D4FC:
	move.w absolute_slot_0000018E.w,d0
	move.w absolute_slot_000001C2.w,d1
	asr.w #4,d1
	add.w d1,d0
	move.w d0,absolute_slot_0000018E.w
	rts
abs_0_0005D50E:
	tst.w absolute_slot_000001BE.w
	beq.b abs_0_0005D516
	rts
abs_0_0005D516:
	tst.w absolute_slot_000001C0.w
	bne.b abs_0_0005D56A
	tst.w absolute_slot_0000014E.w
	beq.b abs_0_0005D530
	lea.l absolute_slot_00000092.l,a0
	tst.b $0040(a0)
	beq.b abs_0_0005D56A
	bra.b abs_0_0005D536
abs_0_0005D530:
	tst.b absolute_slot_00000150.w
	beq.b abs_0_0005D56A
abs_0_0005D536:
	move.w #$FFC2,absolute_slot_000001C2.w
	moveq.l #2,d0
	lea.l abs_0_0006491C(pc),a0
	tst.b absolute_slot_00000152.l
	bne.b abs_0_0005D55E
	moveq.l #3,d0
	lea.l abs_0_00064936(pc),a0
	tst.b absolute_slot_00000153.l
	bne.b abs_0_0005D55E
	moveq.l #1,d0
	lea.l abs_0_00064950(pc),a0
abs_0_0005D55E:
	move.w d0,absolute_slot_000001C0.w
	bsr.w abs_0_0005D8A2
	move.l a0,absolute_slot_00000192.w
abs_0_0005D56A:
	rts
abs_0_0005D56C:
	clr.w absolute_slot_00000196.w
	tst.w absolute_slot_000001C0.w
	bne.b abs_0_0005D596
	tst.b absolute_slot_00000152.w
	bne.b abs_0_0005D5A8
	tst.b absolute_slot_00000153.w
	bne.b abs_0_0005D5C2
	lea.l abs_0_0006490E(pc),a0
	cmpa.l absolute_slot_00000192.w,a0
	beq.b abs_0_0005D594
	bsr.w abs_0_0005D8A2
	move.l a0,absolute_slot_00000192.w
abs_0_0005D594:
	rts
abs_0_0005D596:
	cmpi.w #2,absolute_slot_000001C0.w
	beq.b abs_0_0005D5BA
	cmpi.w #3,absolute_slot_000001C0.w
	beq.b abs_0_0005D5D4
	rts
abs_0_0005D5A8:
	lea.l abs_0_000648DA(pc),a0
	cmpa.l absolute_slot_00000192.w,a0
	beq.b abs_0_0005D5BA
	bsr.w abs_0_0005D8A2
	move.l a0,absolute_slot_00000192.w
abs_0_0005D5BA:
	move.w #$FFFF,absolute_slot_00000196.w
	rts
abs_0_0005D5C2:
	lea.l abs_0_000648F4(pc),a0
	cmpa.l absolute_slot_00000192.w,a0
	beq.b abs_0_0005D5D4
	bsr.w abs_0_0005D8A2
	move.l a0,absolute_slot_00000192.w
abs_0_0005D5D4:
	move.w #$1,absolute_slot_00000196.w
	rts
abs_0_0005D5DC:
	movea.l absolute_slot_000001E0.w,a0
	lea.l absolute_slot_00004750.l,a1
	move.w absolute_slot_0000018C.w,d0
	addq.w #6,d0
	move.w absolute_slot_0000018E.w,d1
	bsr.b abs_0_0005D610
	move.w d0,-(a7)
	move.w absolute_slot_0000018C.w,d0
	addi.w #16,d0
	move.w absolute_slot_0000018E.w,d1
	bsr.b abs_0_0005D610
	move.w (a7)+,d1
	cmp.w d0,d1
	bgt.b abs_0_0005D60A
	move.w d1,d0
abs_0_0005D60A:
	move.w d0,absolute_slot_000001CA.w
	rts
abs_0_0005D610:
	move.w d0,d6
	move.w d1,d7
	clr.w absolute_slot_0000019C.w
	bsr.b abs_0_0005D642
	cmp.w #$100,d4
	bne.b abs_0_0005D622
	moveq.l #0,d1
abs_0_0005D622:
	tst.w d1
	bne.b abs_0_0005D63E
	move.w d4,absolute_slot_0000019A.w
	subi.w #16,d7
	bsr.b abs_0_0005D642
	tst.w d1
	beq.b abs_0_0005D622
	cmp.w #$100,d4
	bne.b abs_0_0005D63E
	move.w absolute_slot_0000019A.w,d4
abs_0_0005D63E:
	move.w d4,d0
	rts
abs_0_0005D642:
	movea.l absolute_slot_000001E0.w,a0
	lea.l absolute_slot_00004750.l,a1
	move.w d6,d0
	move.w d7,d1
	move.w #$100,d4
	tst.w d0
	bmi.b abs_0_0005D6B6
	cmp.w #$140,d0
	bge.b abs_0_0005D6B6
	tst.w d1
	bmi.b abs_0_0005D6B6
	cmp.w #$C0,d1
	bge.b abs_0_0005D6B6
	lsr.w #4,d1
	mulu.w #$28,d1
	adda.w d1,a0
	move.w d0,d1
	lsr.w #4,d1
	add.w d1,d1
	adda.w d1,a0
	moveq.l #0,d0
	move.w (a0),d0
	andi.w #1023,d0
	add.w d0,d0
	move.w $0(a1,d0.w),d0
	cmp.w #$FFFF,d0
	beq.b abs_0_0005D6B6
	lsl.w #4,d0
	addi.w #2048,d0
	adda.w d0,a1
	move.w d6,d0
	andi.w #15,d0
	moveq.l #0,d1
	move.b $0(a1,d0.w),d1
	bmi.b abs_0_0005D6B6
	move.w d7,d4
	andi.w #65520,d4
	add.w d1,d4
	tst.w absolute_slot_0000019C.w
	bne.b abs_0_0005D6B4
	move.w d4,absolute_slot_0000019C.w
abs_0_0005D6B4:
	rts
abs_0_0005D6B6:
	moveq.l #-1,d1
	rts
abs_0_0005D6BA:
	move.w absolute_slot_0000018E.w,d0
	move.w absolute_slot_0000018C.w,d1
	addq.w #1,d1
	bsr.b abs_0_0005D6E4
	move.w d0,-(a7)
	move.w absolute_slot_0000018E.w,d0
	move.w absolute_slot_0000018C.w,d1
	addi.w #21,d1
	bsr.b abs_0_0005D6E4
	move.w (a7)+,d1
	cmp.w d0,d1
	bgt.b abs_0_0005D6DE
	move.w d0,d1
abs_0_0005D6DE:
	move.w d1,absolute_slot_000001CC.w
	rts
abs_0_0005D6E4:
	movea.l absolute_slot_000001E0.w,a0
	lea.l absolute_slot_00006150.l,a1
	subi.w #22,d0
	tst.w d0
	bmi.b abs_0_0005D748
	cmp.w #$C0,d0
	bge.b abs_0_0005D748
	tst.w d1
	bmi.b abs_0_0005D748
	cmp.w #$140,d1
	bge.b abs_0_0005D748
	move.w d0,d6
	lsr.w #4,d0
	mulu.w #$28,d0
	adda.w d0,a0
	move.w d1,d7
	lsr.w #4,d1
	add.w d1,d1
	adda.w d1,a0
	move.w (a0),d0
	add.w d0,d0
	move.w $0(a1,d0.w),d0
	cmp.w #$FFFF,d0
	beq.b abs_0_0005D748
	lsl.w #4,d0
	addi.w #2048,d0
	adda.w d0,a1
	andi.w #15,d7
	moveq.l #0,d2
	move.b $0(a1,d7.w),d2
	bmi.b abs_0_0005D748
	move.w d6,d0
	ori.w #15,d0
	sub.w d2,d0
	addi.w #22,d0
	rts
abs_0_0005D748:
	move.w #$FFEC,d0
	rts
abs_0_0005D74E:
	clr.w absolute_slot_000001C4.w
	move.w #$1,absolute_slot_000001BE.w
	clr.w absolute_slot_00000198.w
	move.w absolute_slot_0000018E.w,d0
	move.w absolute_slot_000001C2.w,d1
	bmi.w abs_0_0005D7EA
	move.w absolute_slot_000001CA.w,d2
	cmp.w d0,d2
	bgt.b abs_0_0005D7A2
	tst.w absolute_slot_0000024A.w
	bne.b abs_0_0005D790
	move.w absolute_slot_0000018C.w,absolute_slot_00000182.w
	move.w d0,absolute_slot_00000184.w
	move.w absolute_slot_0000018C.w,absolute_slot_00000188.w
	move.w d0,absolute_slot_0000018A.w
	move.w absolute_slot_000001DE.w,absolute_slot_00000186.w
abs_0_0005D790:
	move.w absolute_slot_000001C6.w,d4
	move.w #$4,absolute_slot_000001C6.w
	move.w d0,d3
	sub.w d2,d3
	cmp.w d4,d3
	ble.b abs_0_0005D7A4
abs_0_0005D7A2:
	rts
abs_0_0005D7A4:
	clr.w absolute_slot_000001BE.w
	clr.w absolute_slot_000001C2.w
	move.w d2,d0
	tst.w absolute_slot_000001A8.w
	beq.b abs_0_0005D7C2
	cmpi.w #4,absolute_slot_000001AA.w
	ble.b abs_0_0005D7C2
	clr.w absolute_slot_000001AA.w
	addq.w #1,d0
abs_0_0005D7C2:
	cmpi.w #1,absolute_slot_00000190.w
	beq.b abs_0_0005D7DA
	cmpi.w #31,absolute_slot_00000190.w
	beq.b abs_0_0005D7DA
	cmpi.w #38,absolute_slot_00000190.w
	bne.b abs_0_0005D7E4
abs_0_0005D7DA:
	clr.w absolute_slot_000001C0.w
	move.w #$1,absolute_slot_000001C4.w
abs_0_0005D7E4:
	move.w d0,absolute_slot_0000018E.w
	rts
abs_0_0005D7EA:
	bsr.w abs_0_0005D6BA
	move.w absolute_slot_000001CC.w,d3
	move.w absolute_slot_0000018E.w,d0
	move.w absolute_slot_000001C2.w,d1
	cmp.w d0,d3
	ble.b abs_0_0005D7E4
	move.w d3,d0
	move.w #$1,absolute_slot_00000198.w
	bra.b abs_0_0005D7E4
abs_0_0005D808:
	move.w absolute_slot_00000196.w,d0
	cmp.w #$1,d0
	beq.b abs_0_0005D81A
	cmp.w #$FFFF,d0
	beq.b abs_0_0005D85E
	rts
abs_0_0005D81A:
	tst.w absolute_slot_00000254.w
	bne.b abs_0_0005D846
	move.w absolute_slot_0000018C.w,d0
	addi.w #17,d0
	move.w absolute_slot_0000018E.w,d1
	subi.w #6,d1
	bsr.w abs_0_0005D610
	move.w d4,d5
	move.w absolute_slot_0000018E.w,d0
	subi.w #6,d0
	sub.w d0,d4
	ble.b abs_0_0005D848
abs_0_0005D842:
	addq.w #1,absolute_slot_0000018C.w
abs_0_0005D846:
	rts
abs_0_0005D848:
	cmp.w absolute_slot_0000019C.w,d5
	beq.b abs_0_0005D850
	rts
abs_0_0005D850:
	move.w absolute_slot_0000018E.w,d0
	subi.w #22,d0
	cmp.w d0,d5
	ble.b abs_0_0005D842
	rts
abs_0_0005D85E:
	tst.w absolute_slot_00000252.w
	bne.b abs_0_0005D846
	move.w absolute_slot_0000018C.w,d0
	addi.w #5,d0
	move.w absolute_slot_0000018E.w,d1
	subi.w #6,d1
	bsr.w abs_0_0005D610
	move.w d4,d5
	move.w absolute_slot_0000018E.w,d0
	subi.w #6,d0
	sub.w d0,d4
	ble.b abs_0_0005D88C
abs_0_0005D886:
	subq.w #1,absolute_slot_0000018C.w
	rts
abs_0_0005D88C:
	cmp.w absolute_slot_0000019C.w,d5
	beq.b abs_0_0005D894
	rts
abs_0_0005D894:
	move.w absolute_slot_0000018E.w,d0
	subi.w #22,d0
	cmp.w d0,d5
	ble.b abs_0_0005D886
	rts
abs_0_0005D8A2:
	clr.w $0002(a0)
	move.w #$FFFF,$0004(a0)
	rts
abs_0_0005D8AE:
	cmpa.l #$0,a0
	beq.b abs_0_0005D8E2
	subq.w #1,$0002(a0)
	bge.b abs_0_0005D8E2
	lea.l $0008(a0),a2
	move.w (a0),$0002(a0)
	addq.w #1,$0004(a0)
abs_0_0005D8C8:
	move.w $0004(a0),d0
	add.w d0,d0
	move.w $0(a2,d0.w),d0
	cmp.w #$FFFF,d0
	bne.b abs_0_0005D8E0
	move.w $0006(a0),$0004(a0)
	bra.b abs_0_0005D8C8
abs_0_0005D8E0:
	move.w d0,(a1)
abs_0_0005D8E2:
	rts
abs_0_0005D8E4:
	lea.l abs_0_0005D9F2(pc),a0
	move.w absolute_slot_000001DE.w,d0
	lsl.w #3,d0
	adda.w d0,a0
	movem.w (a0)+,d0-d3
	move.w #$8,absolute_slot_000001C6.w
	cmpi.w #300,absolute_slot_0000018C.w
	bge.b abs_0_0005D924
	cmpi.w #0,absolute_slot_0000018C.w
	ble.b abs_0_0005D956
	cmpi.w #20,absolute_slot_0000018E.w
	ble.b abs_0_0005D988
	cmpi.w #192,absolute_slot_0000018E.w
	bge.w abs_0_0005D9BA
	move.w #$6,absolute_slot_000001C6.w
	rts
abs_0_0005D924:
	cmp.w #$FFFF,d1
	bne.b abs_0_0005D932
	move.w #$12C,absolute_slot_0000018C.w
	rts
abs_0_0005D932:
	move.w #$FFFF,absolute_slot_000001EA.w
	bsr.w abs_0_0005D9E6
	move.w d1,absolute_slot_000001DE.w
	move.w #$1,absolute_slot_0000018C.w
	bsr.w abs_0_0005C97E
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_0005D956:
	cmp.w #$FFFF,d0
	bne.b abs_0_0005D964
	move.w #$0,absolute_slot_0000018C.w
	rts
abs_0_0005D964:
	move.w #$FFFF,absolute_slot_000001EA.w
	bsr.w abs_0_0005D9E6
	move.w d0,absolute_slot_000001DE.w
	move.w #$12B,absolute_slot_0000018C.w
	bsr.w abs_0_0005C97E
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_0005D988:
	cmp.w #$FFFF,d2
	bne.b abs_0_0005D996
	move.w #$14,absolute_slot_0000018E.w
	rts
abs_0_0005D996:
	move.w #$FFFF,absolute_slot_000001EA.w
	bsr.w abs_0_0005D9E6
	move.w d2,absolute_slot_000001DE.w
	move.w #$BE,absolute_slot_0000018E.w
	bsr.w abs_0_0005C97E
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_0005D9BA:
	cmp.w #$FFFF,d3
	bne.b abs_0_0005D9C2
	rts
abs_0_0005D9C2:
	move.w #$FFFF,absolute_slot_000001EA.w
	bsr.w abs_0_0005D9E6
	move.w d3,absolute_slot_000001DE.w
	move.w #$15,absolute_slot_0000018E.w
	bsr.w abs_0_0005C97E
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_0005D9E6:
	st.b absolute_slot_000001E6.w
abs_0_0005D9EA:
	tst.w absolute_slot_000001E6.w
	bne.b abs_0_0005D9EA
	rts
abs_0_0005D9F2:
	dc.b $00,$04,$00,$01,$00,$38,$FF,$FF,$00,$00,$00,$02,$FF,$FF,$FF,$FF
	dc.b $00,$01,$00,$03,$FF,$FF,$FF,$FF,$00,$02,$00,$10,$FF,$FF,$FF,$FF
	dc.b $00,$07,$00,$00,$00,$05,$FF,$FF,$00,$08,$00,$38,$00,$06,$00,$04
	dc.b $00,$09,$00,$39,$FF,$FF,$00,$05,$00,$17,$00,$04,$00,$08,$FF,$FF
	dc.b $00,$20,$00,$05,$00,$09,$00,$07,$00,$3A,$00,$06,$FF,$FF,$00,$08
	dc.b $00,$0E,$00,$0C,$00,$0B,$FF,$FF,$00,$3B,$00,$0D,$FF,$FF,$00,$0A
	dc.b $00,$0A,$00,$1B,$00,$0D,$FF,$FF,$00,$0B,$00,$1C,$FF,$FF,$00,$0C
	dc.b $00,$0F,$00,$0A,$00,$3B,$FF,$FF,$00,$28,$00,$0E,$FF,$FF,$FF,$FF
	dc.b $00,$03,$FF,$FF,$00,$11,$FF,$FF,$FF,$FF,$00,$12,$FF,$FF,$00,$10
	dc.b $00,$11,$00,$13,$FF,$FF,$FF,$FF,$00,$12,$FF,$FF,$FF,$FF,$00,$14
	dc.b $FF,$FF,$FF,$FF,$00,$13,$00,$15,$00,$16,$FF,$FF,$00,$14,$FF,$FF
	dc.b $FF,$FF,$00,$15,$FF,$FF,$FF,$FF,$00,$18,$00,$07,$00,$20,$00,$24
	dc.b $00,$19,$00,$17,$00,$1F,$FF,$FF,$00,$1A,$00,$18,$00,$1E,$00,$26
	dc.b $00,$1B,$00,$19,$FF,$FF,$FF,$FF,$00,$0C,$00,$1A,$00,$1C,$FF,$FF
	dc.b $00,$0D,$00,$1D,$00,$21,$00,$1B,$00,$1C,$00,$1E,$FF,$FF,$FF,$FF
	dc.b $00,$1D,$00,$1F,$00,$22,$00,$19,$00,$1E,$00,$20,$FF,$FF,$00,$18
	dc.b $00,$1F,$00,$08,$00,$3A,$00,$17,$FF,$FF,$FF,$FF,$FF,$FF,$00,$1C
	dc.b $FF,$FF,$FF,$FF,$00,$23,$00,$1E,$FF,$FF,$FF,$FF,$FF,$FF,$00,$22
	dc.b $00,$25,$FF,$FF,$00,$17,$00,$27,$00,$26,$00,$24,$FF,$FF,$FF,$FF
	dc.b $FF,$FF,$00,$25,$00,$19,$FF,$FF,$FF,$FF,$FF,$FF,$00,$24,$FF,$FF
	dc.b $00,$29,$00,$0F,$FF,$FF,$FF,$FF,$00,$2A,$00,$28,$00,$2E,$FF,$FF
	dc.b $FF,$FF,$00,$29,$00,$31,$00,$2B,$FF,$FF,$FF,$FF,$00,$2A,$00,$2C
	dc.b $FF,$FF,$00,$2D,$00,$2B,$FF,$FF,$00,$2C,$FF,$FF,$FF,$FF,$FF,$FF
	dc.b $00,$31,$FF,$FF,$00,$2F,$00,$29,$00,$32,$FF,$FF,$00,$30,$00,$2E
	dc.b $FF,$FF,$FF,$FF,$FF,$FF,$00,$2F,$00,$33,$00,$2E,$00,$32,$00,$2A
	dc.b $FF,$FF,$00,$2F,$FF,$FF,$00,$31,$00,$34,$00,$31,$FF,$FF,$FF,$FF
	dc.b $FF,$FF,$00,$33,$FF,$FF,$FF,$FF,$00,$37,$00,$36,$FF,$FF,$FF,$FF
	dc.b $00,$35,$00,$37,$FF,$FF,$FF,$FF,$00,$36,$00,$35,$FF,$FF,$FF,$FF
	dc.b $00,$05,$FF,$FF,$00,$39,$00,$00,$00,$06,$FF,$FF,$FF,$FF,$00,$38
	dc.b $FF,$FF,$00,$09,$FF,$FF,$00,$20,$FF,$FF,$00,$0B,$FF,$FF,$00,$0E
abs_0_0005DBD2:
	lea.l absolute_slot_000001EC.w,a0
	move.w #$A8,(a0)+
	move.w #$5A,(a0)+
	move.w #$27,(a0)+
	move.w #$1,(a0)+
	clr.w (a0)+
	clr.l (a0)+
	move.w #$118,(a0)+
	move.w #$5A,(a0)+
	move.w #$2B,(a0)+
	move.w #$FFFF,(a0)+
	clr.w (a0)+
	clr.l (a0)
	move.w #$80,absolute_slot_0000020C.w
	move.w #$1,absolute_slot_00000210.w
	move.w #$96,absolute_slot_0000020E.w
	move.w #$1E,absolute_slot_00000260.w
	move.w #$8C,absolute_slot_00000264.w
	move.w #$1,absolute_slot_00000262.w
	move.w #$FFFF,absolute_slot_00000266.w
	rts
abs_0_0005DC2A:
	clr.w absolute_slot_000001D0.w
	lea.l abs_0_0005E17A(pc),a0
	moveq.l #3,d0
abs_0_0005DC34:
	move.w (a0)+,d1
	cmp.w #$2B,d1
	bne.b abs_0_0005DC44
	move.w #$1,absolute_slot_000001D0.w
	bra.b abs_0_0005DC48
abs_0_0005DC44:
	dbf.w d0,abs_0_0005DC34
abs_0_0005DC48:
	bsr.w abs_0_0005DE04
	move.w absolute_slot_000001F2.w,d0
	move.w absolute_slot_000001EC.w,d1
	move.w absolute_slot_00000200.w,d2
	move.w absolute_slot_000001FA.w,d3
	lea.l abs_0_000649A0(pc),a0
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DC6A
	lea.l abs_0_000649E8(pc),a0
abs_0_0005DC6A:
	tst.w d0
	bmi.b abs_0_0005DC7C
	lea.l abs_0_000649B2(pc),a0
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DC7C
	lea.l abs_0_000649FA(pc),a0
abs_0_0005DC7C:
	cmpa.l absolute_slot_000001F6.w,a0
	beq.b abs_0_0005DC8A
	move.l a0,absolute_slot_000001F6.w
	bsr.w abs_0_0005D8A2
abs_0_0005DC8A:
	lea.l abs_0_000649C4(pc),a0
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DC98
	lea.l abs_0_00064A0C(pc),a0
abs_0_0005DC98:
	tst.w d2
	bmi.b abs_0_0005DCAA
	lea.l abs_0_000649D6(pc),a0
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DCAA
	lea.l abs_0_00064A1E(pc),a0
abs_0_0005DCAA:
	cmpa.l absolute_slot_00000204.w,a0
	beq.b abs_0_0005DCB8
	move.l a0,absolute_slot_00000204.w
	bsr.w abs_0_0005D8A2
abs_0_0005DCB8:
	tst.w absolute_slot_000001F4.w
	bne.b abs_0_0005DCC0
	add.w d0,d1
abs_0_0005DCC0:
	tst.w absolute_slot_00000202.w
	bne.b abs_0_0005DCC8
	add.w d2,d3
abs_0_0005DCC8:
	cmp.w #$11A,d3
	bne.b abs_0_0005DCD2
	bsr.w abs_0_0005DDC8
abs_0_0005DCD2:
	cmp.w #$74,d1
	bne.b abs_0_0005DCDC
	bsr.w abs_0_0005DD8C
abs_0_0005DCDC:
	move.w d1,d4
	addi.w #28,d4
	cmp.w d4,d3
	bne.b abs_0_0005DCEE
	bsr.w abs_0_0005DD8C
	bsr.w abs_0_0005DDC8
abs_0_0005DCEE:
	move.w d0,absolute_slot_000001F2.w
	move.w d1,absolute_slot_000001EC.w
	move.w d2,absolute_slot_00000200.w
	move.w d3,absolute_slot_000001FA.w
	tst.b absolute_slot_00000208.w
	beq.b abs_0_0005DD10
	move.w #$64,absolute_slot_000001EC.w
	clr.w absolute_slot_000001F2.w
	bra.b abs_0_0005DD20
abs_0_0005DD10:
	move.w absolute_slot_000001EC.w,d0
	move.w absolute_slot_000001EE.w,d1
	move.w absolute_slot_000001F0.w,d2
	bsr.w abs_0_0005CC5C
abs_0_0005DD20:
	tst.b absolute_slot_00000209.w
	beq.b abs_0_0005DD32
	move.w #$12A,absolute_slot_000001FA.w
	clr.w absolute_slot_00000200.w
	bra.b abs_0_0005DD42
abs_0_0005DD32:
	move.w absolute_slot_000001FA.w,d0
	move.w absolute_slot_000001FC.w,d1
	move.w absolute_slot_000001FE.w,d2
	bsr.w abs_0_0005CC5C
abs_0_0005DD42:
	movea.l absolute_slot_000001F6.w,a0
	lea.l absolute_slot_000001F0.w,a1
	bsr.w abs_0_0005D8AE
	movea.l absolute_slot_00000204.w,a0
	lea.l absolute_slot_000001FE.w,a1
	bsr.w abs_0_0005D8AE
	lea.l abs_0_00062364(pc),a0
	move.w absolute_slot_0000020A.w,d0
	move.w $0(a0,d0.w),d1
	addi.w #80,d1
	move.w d1,absolute_slot_000001EE.w
	addq.w #8,d0
	andi.w #62,d0
	move.w $0(a0,d0.w),d1
	addi.w #80,d1
	move.w d1,absolute_slot_000001FC.w
	addq.w #2,absolute_slot_0000020A.w
	andi.w #62,absolute_slot_0000020A.w
	rts
abs_0_0005DD8C:
	tst.w absolute_slot_000001F4.w
	bne.b abs_0_0005DDA6
	neg.w d0
	move.w #$5,absolute_slot_000001F4.w
	move.w #$2F,absolute_slot_000001F0.w
	clr.l absolute_slot_000001F6.w
	rts
abs_0_0005DDA6:
	subq.w #1,absolute_slot_000001F4.w
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DDC0
	cmpi.w #3,absolute_slot_000001F4.w
	bge.b abs_0_0005DDC0
	move.w #$32,absolute_slot_000001F0.w
	rts
abs_0_0005DDC0:
	move.w #$2F,absolute_slot_000001F0.w
	rts
abs_0_0005DDC8:
	tst.w absolute_slot_00000202.w
	bne.b abs_0_0005DDE2
	neg.w d2
	move.w #$5,absolute_slot_00000202.w
	move.w #$2F,absolute_slot_000001FE.w
	clr.l absolute_slot_00000204.w
	rts
abs_0_0005DDE2:
	subq.w #1,absolute_slot_00000202.w
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DDFC
	cmpi.w #3,absolute_slot_00000202.w
	bge.b abs_0_0005DDFC
	move.w #$32,absolute_slot_000001FE.w
	rts
abs_0_0005DDFC:
	move.w #$2F,absolute_slot_000001FE.w
	rts
abs_0_0005DE04:
	lea.l absolute_slot_00000208.w,a1
	move.w absolute_slot_000001EC.w,d0
	addq.w #6,d0
	moveq.l #40,d1
	move.w absolute_slot_000001EE.w,d2
	moveq.l #36,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	bne.b abs_0_0005DE38
	lea.l absolute_slot_00000209.w,a1
	move.w absolute_slot_000001FA.w,d0
	addq.w #6,d0
	moveq.l #40,d1
	move.w absolute_slot_000001FC.w,d2
	moveq.l #36,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005DE50
abs_0_0005DE38:
	tst.w absolute_slot_000001D0.w
	beq.b abs_0_0005DE52
	tst.b (a1)
	bne.b abs_0_0005DE50
	move.b #$1,(a1)
	move.l #$5000,d0
	bsr.w abs_0_0005D46C
abs_0_0005DE50:
	rts
abs_0_0005DE52:
	tst.b (a1)
	bne.b abs_0_0005DE5C
	moveq.l #-2,d0
	bsr.w abs_0_0005FA82
abs_0_0005DE5C:
	rts
abs_0_0005DE5E:
	addq.w #4,a0
	move.l a0,-(a7)
	bsr.w abs_0_0005DE92
	movea.l (a7),a0
	bsr.w abs_0_0005DEDE
	movea.l (a7)+,a3
	addq.w #8,a3
abs_0_0005DE70:
	move.l a3,d0
	btst #0,d0
	beq.b abs_0_0005DE7A
	addq.w #1,a3
abs_0_0005DE7A:
	move.w (a3)+,d0
	move.w (a3)+,d1
abs_0_0005DE7E:
	moveq.l #0,d2
	move.b (a3)+,d2
	bmi.b abs_0_0005DE90
	tst.b d2
	beq.b abs_0_0005DE70
	bsr.w abs_0_0005DFCA
	addq.w #1,d0
	bra.b abs_0_0005DE7E
abs_0_0005DE90:
	rts
abs_0_0005DE92:
	move.w (a0)+,d0
	move.w (a0)+,d1
	movea.l absolute_slot_0000012A.w,a1
	mulu.w #$540,d1
	adda.w d1,a1
	adda.w d0,a1
	move.w (a0)+,d0
	move.w (a0)+,d1
	subq.w #1,d1
abs_0_0005DEA8:
	move.w d0,d2
	subq.w #1,d2
abs_0_0005DEAC:
	moveq.l #7,d4
	lea.l absolute_slot_0002E330.l,a2
abs_0_0005DEB4:
	move.b (a2)+,(a1)
	move.b (a2)+,$002A(a1)
	move.b (a2)+,$0054(a1)
	move.b (a2)+,$007E(a1)
	adda.w #$A8,a1
	dbf.w d4,abs_0_0005DEB4
	suba.w #$53F,a1
	dbf.w d2,abs_0_0005DEAC
	suba.w d0,a1
	lea.l $0540(a1),a1
	dbf.w d1,abs_0_0005DEA8
	rts
abs_0_0005DEDE:
	movem.w (a0)+,d4-d7
	move.w d4,d0
	move.w d5,d1
	subq.w #1,d1
	move.w d6,d2
	subq.w #1,d2
	bsr.w abs_0_0005DF54
	move.w d4,d0
	add.w d7,d1
	addq.w #1,d1
	move.w d6,d2
	subq.w #1,d2
	bsr.w abs_0_0005DF54
	move.w d4,d0
	subq.w #1,d0
	move.w d5,d1
	move.w d7,d2
	subq.w #1,d2
	bsr.w abs_0_0005DF62
	move.w d4,d0
	add.w d6,d0
	move.w d5,d1
	move.w d7,d2
	subq.w #1,d2
	bsr.w abs_0_0005DF62
	lea.l abs_0_0006231C(pc),a0
abs_0_0005DF1E:
	moveq.l #2,d2
abs_0_0005DF20:
	move.w d4,d0
	add.w (a0)+,d0
	move.w d5,d1
	add.w (a0)+,d1
	move.w (a0)+,d3
	bsr.w abs_0_0005DF70
	dbf.w d2,abs_0_0005DF20
	moveq.l #2,d2
abs_0_0005DF34:
	move.w d4,d0
	add.w d6,d0
	add.w (a0)+,d0
	move.w d5,d1
	add.w (a0)+,d1
	move.w (a0)+,d3
	bsr.w abs_0_0005DF70
	dbf.w d2,abs_0_0005DF34
	add.w d7,d5
	tst.w d7
	beq.b abs_0_0005DF52
	moveq.l #0,d7
	bra.b abs_0_0005DF1E
abs_0_0005DF52:
	rts
abs_0_0005DF54:
	moveq.l #74,d3
	bsr.w abs_0_0005DF70
	addq.w #1,d0
	dbf.w d2,abs_0_0005DF54
	rts
abs_0_0005DF62:
	moveq.l #75,d3
	bsr.w abs_0_0005DF70
	addq.w #1,d1
	dbf.w d2,abs_0_0005DF62
	rts
abs_0_0005DF70:
	movem.l d0-d7/a0-a6,-(a7)
	movea.l absolute_slot_0000012A.w,a1
	adda.w d0,a1
	mulu.w #$540,d1
	adda.w d1,a1
	lea.l absolute_slot_0002DA30.l,a2
	lea.l absolute_slot_0002E430.l,a3
	lsl.w #3,d3
	adda.w d3,a3
	lsl.w #2,d3
	adda.w d3,a2
	moveq.l #7,d4
abs_0_0005DF96:
	move.b (a3)+,d0
	and.b d0,(a1)
	and.b d0,$002A(a1)
	and.b d0,$0054(a1)
	and.b d0,$007E(a1)
	move.b (a2)+,d0
	or.b d0,(a1)
	move.b (a2)+,d0
	or.b d0,$002A(a1)
	move.b (a2)+,d0
	or.b d0,$0054(a1)
	move.b (a2)+,d0
	or.b d0,$007E(a1)
	lea.l $00A8(a1),a1
	dbf.w d4,abs_0_0005DF96
	movem.l (a7)+,d0-d7/a0-a6
	rts
abs_0_0005DFCA:
	movea.l absolute_slot_0000012A.w,a0
	lea.l absolute_slot_0002DA30.l,a1
	lea.l abs_0_00062280(pc),a2
	subi.w #32,d2
	move.b $0(a2,d2.w),d2
	adda.w d0,a0
	adda.w d1,a0
	lsl.w #5,d2
	adda.w d2,a1
	moveq.l #7,d2
abs_0_0005DFEA:
	move.b (a1)+,(a0)
	move.b (a1)+,$002A(a0)
	move.b (a1)+,$0054(a0)
	move.b (a1)+,$007E(a0)
	lea.l $00A8(a0),a0
	dbf.w d2,abs_0_0005DFEA
	rts
abs_0_0005E002:
	tst.l absolute_slot_0000016A.w
	bne.b abs_0_0005E00E
	tst.w absolute_slot_000001C4.w
	bne.b abs_0_0005E010
abs_0_0005E00E:
	rts
abs_0_0005E010:
	tst.w absolute_slot_00000154.w
	bne.w abs_0_0005E172
	tst.w absolute_slot_00000158.w
	bne.b abs_0_0005E020
	rts
abs_0_0005E020:
	clr.w absolute_slot_00000158.w
	tst.w absolute_slot_0000024A.w
	bne.b abs_0_0005E034
	not.w absolute_slot_00000162.w
	bne.b abs_0_0005E036
	bsr.w abs_0_0005C992
abs_0_0005E034:
	rts
abs_0_0005E036:
	bsr.w abs_0_0005E5CA
	tst.w d0
	beq.w abs_0_0005E122
	move.w $0006(a0),d0
	bge.b abs_0_0005E078
	lea.l runtime_code_00000318.w,a1
	move.w $0008(a0),d0
	mulu.w #$A,d0
	move.w #$FFFF,$0(a1,d0.w)
	lea.l abs_0_00062BEE(pc),a0
	move.l a0,absolute_slot_0000016A.w
	bsr.w abs_0_0005DE5E
	not.w absolute_slot_00000162.w
	move.l #$1000,d0
	bsr.w abs_0_0005D46C
	bsr.w abs_0_0005D49C
	rts
abs_0_0005E078:
	lea.l abs_0_0005E17A(pc),a1
	moveq.l #2,d1
abs_0_0005E07E:
	tst.w (a1)
	beq.b abs_0_0005E09C
	addq.w #2,a1
	dbf.w d1,abs_0_0005E07E
	not.w absolute_slot_00000162.w
	lea.l abs_0_0006322E(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	rts
abs_0_0005E09C:
	cmpi.w #46,$0008(a0)
	bne.b abs_0_0005E0AA
	move.w #$1,absolute_slot_0000028E.w
abs_0_0005E0AA:
	tst.w absolute_slot_0000028E.w
	bne.b abs_0_0005E0CC
	cmpi.w #33,$0008(a0)
	bne.b abs_0_0005E0CC
	not.w absolute_slot_00000162.w
	lea.l abs_0_00063560(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	rts
abs_0_0005E0CC:
	cmpi.w #36,$0008(a0)
	bne.b abs_0_0005E0FE
	lea.l abs_0_0005E17A(pc),a2
	cmpi.w #54,(a2)
	beq.b abs_0_0005E0EE
	cmpi.w #54,$0002(a2)
	beq.b abs_0_0005E0EE
	cmpi.w #54,$0004(a2)
	bne.b abs_0_0005E0FE
abs_0_0005E0EE:
	tst.w absolute_slot_00000276.w
	bne.b abs_0_0005E0FE
	move.w #$1,absolute_slot_00000276.w
	addq.w #1,absolute_slot_0000027E.w
abs_0_0005E0FE:
	move.w $0008(a0),(a1)
	lea.l runtime_code_00000318.w,a1
	move.w $0008(a0),d0
	mulu.w #$A,d0
	move.w #$FFFF,$0(a1,d0.w)
	cmpi.w #1,absolute_slot_00000276.w
	bne.b abs_0_0005E122
	not.w absolute_slot_00000162.w
	rts
abs_0_0005E122:
	lea.l abs_0_0005E17A(pc),a0
	lea.l abs_0_000657EE(pc),a1
	lea.l abs_0_00062B4E(pc),a2
	moveq.l #2,d0
abs_0_0005E130:
	move.w (a0)+,d1
	beq.b abs_0_0005E13C
	subi.w #29,d1
	mulu.w #$14,d1
abs_0_0005E13C:
	move.l $0(a1,d1.w),(a2)+
	move.l $4(a1,d1.w),(a2)+
	move.l $8(a1,d1.w),(a2)+
	move.l $C(a1,d1.w),(a2)+
	move.l $10(a1,d1.w),(a2)+
	addq.w #6,a2
	dbf.w d0,abs_0_0005E130
	lea.l abs_0_00062B3E(pc),a0
	bsr.w abs_0_0005DE5E
	lea.l abs_0_00062BBA(pc),a0
	bsr.w abs_0_0005DE5E
	bsr.w abs_0_00060268
	move.w #$3,absolute_slot_00000164.w
	rts
abs_0_0005E172:
	move.w #$1,absolute_slot_00000158.w
	rts
abs_0_0005E17A:
	dc.b $00,$00,$00,$00,$00,$00
abs_0_0005E180:
	bsr.w abs_0_0005E206
	bsr.w abs_0_0005E412
	bsr.b abs_0_0005E19C
	clr.w absolute_slot_000001E4.w
	tst.w absolute_slot_000002CE.w
	beq.b abs_0_0005E198
abs_0_0005E194:
	bra.w abs_0_00061404
abs_0_0005E198:
	bra.w abs_0_0005C144
abs_0_0005E19C:
	tst.w absolute_slot_00000154.w
	bne.b abs_0_0005E1AA
	tst.w absolute_slot_00000158.w
	bne.b abs_0_0005E1B2
	rts
abs_0_0005E1AA:
	move.w #$1,absolute_slot_00000158.w
	rts
abs_0_0005E1B2:
	clr.w absolute_slot_00000158.w
	move.w absolute_slot_00000164.w,d0
	cmp.w #$3,d0
	beq.b abs_0_0005E1FC
	lea.l abs_0_0005E17A(pc),a0
	add.w d0,d0
	adda.w d0,a0
	move.w (a0),d0
	beq.b abs_0_0005E1FA
	clr.w (a0)
	lea.l runtime_code_00000318.w,a1
	mulu.w #$A,d0
	adda.w d0,a1
	bsr.w abs_0_0005FAA4
	tst.w d7
	bne.b abs_0_0005E1FC
	move.w absolute_slot_0000018C.w,d0
	move.w d0,$0002(a1)
	move.w absolute_slot_0000018E.w,d0
	subi.w #16,d0
	move.w d0,$0004(a1)
	move.w absolute_slot_000001DE.w,(a1)
	bra.b abs_0_0005E1FC
abs_0_0005E1FA:
	rts
abs_0_0005E1FC:
	not.w absolute_slot_00000162.w
	bsr.w abs_0_0005C992
	rts
abs_0_0005E206:
	move.w absolute_slot_00000164.w,d0
	lea.l abs_0_0005E2B0(pc),a0
	add.w d0,d0
	move.w $0(a0,d0.w),d0
	move.w absolute_slot_00000166.w,d2
	lea.l abs_0_0005E3D2(pc),a1
	add.w d2,d2
	add.w d2,d2
	movea.l $0(a1,d2.w),a1
	movea.l absolute_slot_00000126.w,a0
	adda.w d0,a0
	move.l a0,-(a7)
	moveq.l #19,d2
abs_0_0005E22E:
	move.w #$2000,d0
	move.w #$DFFF,d1
	jsr (a1)
	adda.w #$1A,a0
	move.w #$4,d0
	move.w #$FFFB,d1
	jsr (a1)
	lea.l $008E(a0),a0
	dbf.w d2,abs_0_0005E22E
	movea.l (a7),a0
	addq.w #2,a0
	moveq.l #11,d2
	move.w #$FFFF,d0
	moveq.l #0,d1
abs_0_0005E25A:
	jsr (a1)
	adda.w #$C78,a0
	jsr (a1)
	suba.w #$C76,a0
	dbf.w d2,abs_0_0005E25A
	movea.l (a7),a0
	move.w #$1FFF,d0
	move.w #$E000,d1
	jsr (a1)
	adda.w #$C78,a0
	jsr (a1)
	movea.l (a7)+,a0
	adda.w #$1A,a0
	move.w #$FFF8,d0
	move.w #$7,d1
	jsr (a1)
	adda.w #$C78,a0
	jsr (a1)
	addq.w #1,absolute_slot_00000168.w
abs_0_0005E296:
	move.w absolute_slot_00000168.w,d0
	lsr.w #1,d0
	add.w d0,d0
	move.w abs_0_0005E2B8(pc,d0.w),d0
	bge.b abs_0_0005E2AA
	clr.w absolute_slot_00000168.w
	bra.b abs_0_0005E296
abs_0_0005E2AA:
	move.w d0,absolute_slot_00000166.w
	rts
abs_0_0005E2B0:
	dc.b $0F,$C6,$1C,$E6,$2A,$06,$37,$26
abs_0_0005E2B8:
	dc.w $0009,$0009,$0009,$000A,$000A,$000A,$000B,$000B	; lookup_table
	dc.w $000B,$000A,$000A,$000A,$FFFF	; lookup_table
abs_0_0005E2D2:
	and.w d1,(a0)
	and.w d1,$002A(a0)
	and.w d1,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E2E2:
	or.w d0,(a0)
	and.w d1,$002A(a0)
	and.w d1,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E2F2:
	and.w d1,(a0)
	or.w d0,$002A(a0)
	and.w d1,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E302:
	or.w d0,(a0)
	or.w d0,$002A(a0)
	and.w d1,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E312:
	and.w d1,(a0)
	and.w d1,$002A(a0)
	or.w d0,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E322:
	or.w d0,(a0)
	and.w d1,$002A(a0)
	or.w d0,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E332:
	and.w d1,(a0)
	or.w d0,$002A(a0)
	or.w d0,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E342:
	or.w d0,(a0)
	or.w d0,$002A(a0)
	or.w d0,$0054(a0)
	and.w d1,$007E(a0)
	rts
abs_0_0005E352:
	and.w d1,(a0)
	and.w d1,$002A(a0)
	and.w d1,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E362:
	or.w d0,(a0)
	and.w d1,$002A(a0)
	and.w d1,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E372:
	and.w d1,(a0)
	or.w d0,$002A(a0)
	and.w d1,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E382:
	or.w d0,(a0)
	or.w d0,$002A(a0)
	and.w d1,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E392:
	and.w d1,(a0)
	and.w d1,$002A(a0)
	or.w d0,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E3A2:
	or.w d0,(a0)
	and.w d1,$002A(a0)
	or.w d0,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E3B2:
	and.w d1,(a0)
	or.w d0,$002A(a0)
	or.w d0,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E3C2:
	or.w d0,(a0)
	or.w d0,$002A(a0)
	or.w d0,$0054(a0)
	or.w d0,$007E(a0)
	rts
abs_0_0005E3D2:
	dc.l abs_0_0005E2D2	; pointer_table
	dc.l abs_0_0005E2E2
	dc.l abs_0_0005E2F2
	dc.l abs_0_0005E302
	dc.l abs_0_0005E312
	dc.l abs_0_0005E322
	dc.l abs_0_0005E332
	dc.l abs_0_0005E342
	dc.l abs_0_0005E352
	dc.l abs_0_0005E362
	dc.l abs_0_0005E372
	dc.l abs_0_0005E382
	dc.l abs_0_0005E392
	dc.l abs_0_0005E3A2
	dc.l abs_0_0005E3B2
	dc.l abs_0_0005E3C2
abs_0_0005E412:
	move.b absolute_slot_00000150.w,d0
	move.b absolute_slot_00000151.w,d1
	tst.w absolute_slot_0000014E.w
	beq.b abs_0_0005E428
	move.b absolute_slot_00000152.w,d0
	move.b absolute_slot_00000153.w,d1
abs_0_0005E428:
	tst.b d0
	bne.b abs_0_0005E444
	tst.w absolute_slot_0000015A.w
	beq.b abs_0_0005E44A
	clr.w absolute_slot_0000015A.w
	tst.w absolute_slot_00000164.w
	beq.b abs_0_0005E44A
	bsr.b abs_0_0005E470
	subq.w #1,absolute_slot_00000164.w
	rts
abs_0_0005E444:
	move.w #$1,absolute_slot_0000015A.w
abs_0_0005E44A:
	tst.b d1
	bne.b abs_0_0005E468
	tst.w absolute_slot_0000015E.w
	beq.b abs_0_0005E46E
	clr.w absolute_slot_0000015E.w
	cmpi.w #3,absolute_slot_00000164.w
	beq.b abs_0_0005E46E
	bsr.b abs_0_0005E470
	addq.w #1,absolute_slot_00000164.w
	rts
abs_0_0005E468:
	move.w #$1,absolute_slot_0000015E.w
abs_0_0005E46E:
	rts
abs_0_0005E470:
	move.w absolute_slot_00000164.w,d0
	move.w #$C,absolute_slot_00000166.w
	bsr.w abs_0_0005E206
	rts
abs_0_0005E480:
	tst.w absolute_slot_0000016E.w
	beq.b abs_0_0005E496
	movea.l absolute_slot_0000016A.w,a0
	bsr.w abs_0_0005DE5E
	clr.w absolute_slot_0000015C.w
	clr.w absolute_slot_0000016E.w
abs_0_0005E496:
	rts
abs_0_0005E498:
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E4C0
	movea.l absolute_slot_0000016A.w,a0
	move.l (a0),absolute_slot_0000016A.w
	beq.b abs_0_0005E4D2
	movea.l absolute_slot_0000016A.w,a0
	move.l absolute_slot_0000012A.w,-(a7)
	move.l absolute_slot_00000126.w,absolute_slot_0000012A.w
	bsr.w abs_0_0005DE5E
	move.l (a7)+,absolute_slot_0000012A.w
abs_0_0005E4C0:
	clr.w absolute_slot_000001E4.w
	tst.w absolute_slot_000002CE.w
	beq.b abs_0_0005E4CE
abs_0_0005E4CA:
	bra.w abs_0_00061404
abs_0_0005E4CE:
	bra.w abs_0_0005C144
abs_0_0005E4D2:
	bsr.w abs_0_0005C992
	move.w #$A,absolute_slot_00000156.w
	clr.w absolute_slot_00000158.w
	bra.b abs_0_0005E4C0
abs_0_0005E4E2:
	lea.l abs_0_0006556E(pc),a0
	lea.l runtime_code_00000318.w,a1
	move.w #$3B,d0
abs_0_0005E4EE:
	move.l (a0)+,(a1)+
	move.l (a0)+,(a1)+
	move.w (a0)+,(a1)+
	dbf.w d0,abs_0_0005E4EE
	lea.l absolute_slot_00000570.w,a0
	moveq.l #15,d0
abs_0_0005E4FE:
	move.l #$FFFFFFFF,(a0)+
	move.l #$FFFFFFFF,(a0)+
	move.w #$FFFF,(a0)+
	dbf.w d0,abs_0_0005E4FE
	rts
abs_0_0005E514:
	lea.l absolute_slot_00000570.w,a0
	moveq.l #15,d0
	moveq.l #-1,d1
abs_0_0005E51C:
	move.l d1,(a0)+
	move.l d1,(a0)+
	move.w d1,(a0)+
	dbf.w d0,abs_0_0005E51C
	lea.l runtime_code_00000318.w,a0
	lea.l absolute_slot_00000570.w,a1
	move.w absolute_slot_000001DE.w,d0
	moveq.l #0,d1
	move.w #$3B,d7
abs_0_0005E538:
	cmp.w (a0),d0
	bne.b abs_0_0005E54E
	move.l (a0),(a1)+
	move.l $0004(a0),(a1)+
	move.w $0008(a0),(a1)+
	addq.w #1,d1
	cmp.w #$F,d1
	beq.b abs_0_0005E558
abs_0_0005E54E:
	lea.l $000A(a0),a0
	dbf.w d7,abs_0_0005E538
	rts
abs_0_0005E558:
	move.w d0,_custom+color.l	; palette color 0
	addq.w #1,d0
	bra.b abs_0_0005E558
abs_0_0005E562:
	bsr.w abs_0_0005E5A4
	lea.l absolute_slot_00000570.w,a0
	moveq.l #15,d7
abs_0_0005E56C:
	tst.w (a0)
	bmi.b abs_0_0005E59A
	move.w $0002(a0),d0
	move.w $0004(a0),d1
	move.w $0006(a0),d2
	bge.b abs_0_0005E586
	neg.w d2
	add.w d2,d2
	move.w abs_0_0005E59C(pc,d2.w),d2
abs_0_0005E586:
	movem.l d0-d7/a0-a6,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d0-d7/a0-a6
	lea.l $000A(a0),a0
	dbf.w d7,abs_0_0005E56C
abs_0_0005E59A:
	rts
abs_0_0005E59C:
	dc.w $0000	; lookup_table
abs_0_0005E59E:
	dc.w $0000
abs_0_0005E5A0:
	dc.w $0000
abs_0_0005E5A2:
	dc.w $0000
abs_0_0005E5A4:
	lea.l abs_0_00064A30(pc),a0
	lea.l abs_0_0005E59E(pc),a1
	bsr.w abs_0_0005D8AE
	lea.l abs_0_00064A4A(pc),a0
	lea.l abs_0_0005E5A0(pc),a1
	bsr.w abs_0_0005D8AE
	lea.l abs_0_00064A64(pc),a0
	lea.l abs_0_0005E5A2(pc),a1
	bsr.w abs_0_0005D8AE
	rts
abs_0_0005E5CA:
	lea.l absolute_slot_00000570.w,a0
	moveq.l #15,d7
	move.w absolute_slot_0000018C.w,d0
	addq.w #5,d0
	move.w absolute_slot_0000018E.w,d1
	subi.w #22,d1
abs_0_0005E5DE:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005E610
	move.w $0002(a0),d2
	sub.w d0,d2
	bge.b abs_0_0005E5EE
	neg.w d2
abs_0_0005E5EE:
	cmp.w #$12,d2
	bge.b abs_0_0005E608
	move.w $0004(a0),d2
	sub.w d1,d2
	bge.b abs_0_0005E5FE
	neg.w d2
abs_0_0005E5FE:
	cmp.w #$12,d2
	bge.b abs_0_0005E608
	moveq.l #1,d0
	rts
abs_0_0005E608:
	lea.l $000A(a0),a0
	dbf.w d7,abs_0_0005E5DE
abs_0_0005E610:
	moveq.l #0,d0
	rts
abs_0_0005E614:
	bsr.w abs_0_0005DC2A
	lea.l abs_0_0005F3B8(pc),a0
	bsr.w abs_0_0005F328
	tst.w absolute_slot_0000024C.w
	bne.b abs_0_0005E62E
	bsr.w abs_0_0005E658
	bsr.w abs_0_0005E630
abs_0_0005E62E:
	rts
abs_0_0005E630:
	lea.l absolute_slot_00000570.w,a0
	moveq.l #15,d7
abs_0_0005E636:
	cmpi.w #42,$0008(a0)
	beq.b abs_0_0005E648
	lea.l $000A(a0),a0
	dbf.w d7,abs_0_0005E636
	rts
abs_0_0005E648:
	lea.l abs_0_0005F3C2(pc),a1
	move.w (a1),d0
	subi.w #15,d0
	move.w d0,$0004(a0)
	rts
abs_0_0005E658:
	lea.l abs_0_0005F3C0(pc),a0
	tst.w $0004(a0)
	beq.b abs_0_0005E68E
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E68E
	lea.l absolute_slot_000004BC.l,a0
	lea.l abs_0_0005E17A(pc),a1
	moveq.l #2,d1
abs_0_0005E676:
	tst.w (a1)
	beq.b abs_0_0005E690
	addq.w #2,a1
	dbf.w d1,abs_0_0005E676
	lea.l abs_0_0006322E(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005E68E:
	rts
abs_0_0005E690:
	move.w $0008(a0),(a1)
	lea.l runtime_code_00000318.w,a1
	move.w $0008(a0),d0
	mulu.w #$A,d0
	move.w #$FFFF,$0(a1,d0.w)
	lea.l abs_0_0005E17A(pc),a0
	lea.l abs_0_000657EE(pc),a1
	lea.l abs_0_00062B4E(pc),a2
	moveq.l #2,d0
abs_0_0005E6B4:
	move.w (a0)+,d1
	beq.b abs_0_0005E6C0
	subi.w #29,d1
	mulu.w #$14,d1
abs_0_0005E6C0:
	move.l $0(a1,d1.w),(a2)+
	move.l $4(a1,d1.w),(a2)+
	move.l $8(a1,d1.w),(a2)+
	move.l $C(a1,d1.w),(a2)+
	move.l $10(a1,d1.w),(a2)+
	addq.w #6,a2
	dbf.w d0,abs_0_0005E6B4
	move.w #$1,absolute_slot_0000024C.w
	lea.l abs_0_000634D4(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	rts
abs_0_0005E6F0:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005E6FE
	bsr.w abs_0_0005FE68
	bsr.w abs_0_0005FB62
abs_0_0005E6FE:
	tst.w absolute_slot_00000236.w
	bne.b abs_0_0005E740
	bsr.w abs_0_0005F2F2
	tst.w absolute_slot_000001C4.w
	beq.b abs_0_0005E740
	tst.b absolute_slot_00000227.w
	bne.b abs_0_0005E740
	move.w #$9A,d0
	moveq.l #35,d1
	moveq.l #120,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005E740
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E740
	st.b absolute_slot_00000227.w
	lea.l abs_0_00062C2C(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005E740:
	rts
abs_0_0005E742:
	bsr.w abs_0_00060D64
	cmpi.w #3,absolute_slot_00000282.w
	bge.b abs_0_0005E78E
	bsr.w abs_0_0005F2D4
	bsr.w abs_0_0005F214
	tst.w absolute_slot_000001C4.w
	beq.b abs_0_0005E78E
	tst.b absolute_slot_00000228.w
	bne.b abs_0_0005E78E
	move.w #$9C,d0
	moveq.l #16,d1
	moveq.l #112,d2
	moveq.l #16,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005E78E
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E78E
	st.b absolute_slot_00000228.w
	lea.l abs_0_00062E50(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005E78E:
	rts
abs_0_0005E790:
	move.w #$B4,d0
	move.w #$81,d1
	moveq.l #99,d2
	bsr.w abs_0_0005CC5C
	tst.w absolute_slot_000001C4.w
	beq.b abs_0_0005E7CC
	move.w #$B2,d0
	moveq.l #8,d1
	moveq.l #116,d2
	moveq.l #16,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005E7CC
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E7CC
	lea.l abs_0_00062F1E(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005E7CC:
	rts
abs_0_0005E7CE:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005E7E0
	bsr.w abs_0_0005FC12
	bsr.w abs_0_0005FC34
	bsr.w abs_0_0005E85A
abs_0_0005E7E0:
	lea.l abs_0_0005F3CA(pc),a0
	bsr.w abs_0_0005F328
	cmpi.w #1,absolute_slot_00000244.w
	ble.b abs_0_0005E7F6
	bsr.w abs_0_0005E888
	bra.b abs_0_0005E824
abs_0_0005E7F6:
	moveq.l #100,d0
	moveq.l #87,d1
	move.w #$97,d2
	bsr.w abs_0_0005CC5C
	subq.b #1,absolute_slot_0000021A.w
	bge.b abs_0_0005E80E
	move.b #$64,absolute_slot_0000021A.w
abs_0_0005E80E:
	cmpi.b #12,absolute_slot_0000021A.w
	bge.b abs_0_0005E824
	move.w #$7D,d0
	moveq.l #102,d1
	move.w #$9D,d2
	bsr.w abs_0_0005CC5C
abs_0_0005E824:
	tst.b absolute_slot_00000226.w
	bne.b abs_0_0005E858
	move.w #$80,d0
	moveq.l #18,d1
	move.w #$8C,d2
	moveq.l #10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005E858
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E858
	lea.l abs_0_0006328A(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	st.b absolute_slot_00000226.w
abs_0_0005E858:
	rts
abs_0_0005E85A:
	cmpi.w #4,absolute_slot_00000244.w
	bne.b abs_0_0005E886
	addq.w #1,absolute_slot_00000244.w
	lea.l abs_0_0006388E(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	lea.l absolute_slot_000004EE.w,a0
	move.w #$2,(a0)
	move.l #$8000,d0
	bsr.w abs_0_0005D46C
abs_0_0005E886:
	rts
abs_0_0005E888:
	lea.l abs_0_00064B98(pc),a0
	lea.l absolute_slot_00000256.w,a1
	bsr.w abs_0_0005D8AE
	moveq.l #100,d0
	moveq.l #87,d1
	move.w absolute_slot_00000256.w,d2
	bsr.w abs_0_0005CC5C
	tst.w absolute_slot_000002E2.w
	beq.b abs_0_0005E8C0
	lea.l abs_0_00064BAA(pc),a0
	lea.l absolute_slot_00000258.w,a1
	bsr.w abs_0_0005D8AE
	moveq.l #103,d0
	move.w #$89,d1
	move.w absolute_slot_00000258.w,d2
	bsr.w abs_0_0005CC5C
abs_0_0005E8C0:
	rts
abs_0_0005E8C2:
	lea.l abs_0_0005F3D4(pc),a0
	bsr.w abs_0_0005F328
	bsr.w abs_0_0006114A
	rts
abs_0_0005E8D0:
	cmpi.w #3,absolute_slot_000002A0.w
	bge.b abs_0_0005E8EA
	bsr.w abs_0_0005EE7A
	bsr.w abs_0_0005F198
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005E8EA
	bsr.w abs_0_0005F1A6
abs_0_0005E8EA:
	bsr.w abs_0_00060F98
	rts
abs_0_0005E8F0:
	move.l #$60216,absolute_slot_00000138.w
	bsr.w abs_0_0005F3EE
	bsr.w abs_0_00060224
	cmpi.w #2,absolute_slot_00000232.w
	beq.b abs_0_0005E94A
	cmpi.w #40,absolute_slot_0000018C.w
	bge.b abs_0_0005E948
	move.w #$27,absolute_slot_0000018C.w
	tst.w absolute_slot_00000232.w
	bne.b abs_0_0005E948
	lea.l abs_0_0005E17A(pc),a0
	cmpi.w #30,(a0)+
	beq.b abs_0_0005E948
	cmpi.w #30,(a0)+
	beq.b abs_0_0005E948
	cmpi.w #30,(a0)
	beq.b abs_0_0005E948
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005E948
	lea.l abs_0_00062FEE(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005E948:
	rts
abs_0_0005E94A:
	cmpi.w #30,absolute_slot_0000018C.w
	bge.b abs_0_0005E966
	cmpi.w #140,absolute_slot_0000018E.w
	bge.b abs_0_0005E966
	cmpi.w #$FFFF,absolute_slot_00000196.w
	bne.b abs_0_0005E966
	addq.w #1,absolute_slot_0000018C.w
abs_0_0005E966:
	cmpi.w #2,absolute_slot_0000018C.l
	ble.b abs_0_0005E980
	cmpi.w #18,absolute_slot_0000018C.w
	bge.b abs_0_0005E97E
	move.w #$FFFF,absolute_slot_0000018C.w
abs_0_0005E97E:
	rts
abs_0_0005E980:
	move.w #$13,absolute_slot_0000018C.w
	cmpi.w #140,absolute_slot_0000018E.w
	bge.b abs_0_0005E994
	move.w #$8C,absolute_slot_0000018E.w
abs_0_0005E994:
	rts
abs_0_0005E996:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005E9A0
	bsr.w abs_0_0005FBBA
abs_0_0005E9A0:
	move.w #$96,d0
	moveq.l #32,d1
	move.w #$81,d2
	bsr.w abs_0_0005CC5C
	subq.b #1,absolute_slot_0000021C.w
	bge.b abs_0_0005E9BA
	move.b #$64,absolute_slot_0000021C.w
abs_0_0005E9BA:
	cmpi.b #7,absolute_slot_0000021C.w
	bge.b abs_0_0005E9D0
	move.w #$A2,d0
	moveq.l #39,d1
	move.w #$94,d2
	bsr.w abs_0_0005CC5C
abs_0_0005E9D0:
	tst.b absolute_slot_00000229.w
	bne.b abs_0_0005EA02
	move.w #$96,d0
	moveq.l #20,d1
	moveq.l #50,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005EA02
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005EA02
	lea.l abs_0_00063016(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	st.b absolute_slot_00000229.w
abs_0_0005EA02:
	rts
abs_0_0005EA04:
	lea.l abs_0_0005EDFA(pc),a0
	bsr.w abs_0_0005ECFE
	lea.l abs_0_0005EE0A(pc),a0
	bsr.w abs_0_0005ECFE
	cmpi.w #3,absolute_slot_000002CC.w
	beq.b abs_0_0005EA20
	bsr.w abs_0_000606D0
abs_0_0005EA20:
	cmpi.w #120,absolute_slot_0000018E.w
	ble.b abs_0_0005EA4C
	cmpi.w #224,absolute_slot_0000018C.w
	ble.b abs_0_0005EA4C
	cmpi.w #3,absolute_slot_000002CC.w
	beq.b abs_0_0005EA3E
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
abs_0_0005EA3E:
	cmpi.w #240,absolute_slot_0000018C.w
	ble.b abs_0_0005EA4C
	move.w #$F0,absolute_slot_0000018C.w
abs_0_0005EA4C:
	lea.l abs_0_00064B20(pc),a0
	lea.l absolute_slot_000001DC.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$100,d0
	move.w #$80,d1
	move.w #$82,d2
	bsr.w abs_0_0005CC5C
	subq.b #1,absolute_slot_0000021B.w
	bge.b abs_0_0005EA74
	move.b #$64,absolute_slot_0000021B.w
abs_0_0005EA74:
	cmpi.b #12,absolute_slot_0000021B.w
	bge.b abs_0_0005EA8C
	move.w #$103,d0
	move.w #$86,d1
	move.w #$83,d2
	bsr.w abs_0_0005CC5C
abs_0_0005EA8C:
	move.w #$119,d0
	move.w #$98,d1
	move.w absolute_slot_000001DC.w,d2
	bsr.w abs_0_0005CC5C
	tst.w absolute_slot_0000022C.w
	bne.b abs_0_0005EAB2
	move.w #$F2,d0
	move.w #$80,d1
	move.w #$92,d2
	bsr.w abs_0_0005CC5C
abs_0_0005EAB2:
	move.w #$D8,d0
	moveq.l #16,d1
	move.w #$8C,d2
	moveq.l #32,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005EAF6
	move.w absolute_slot_0000022C.w,d0
	beq.b abs_0_0005EADA
	subq.w #1,d0
	beq.b abs_0_0005EAF8
	subq.w #1,d0
	beq.b abs_0_0005EB28
	subq.w #1,d0
	beq.b abs_0_0005EB44
	rts
abs_0_0005EADA:
	lea.l abs_0_000630F0(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	lea.l absolute_slot_0000048A.w,a0
	move.w #$15,(a0)
	move.w #$1,absolute_slot_0000022C.w
abs_0_0005EAF6:
	rts
abs_0_0005EAF8:
	lea.l abs_0_0005E17A(pc),a0
	cmpi.w #55,(a0)+
	beq.b abs_0_0005EB0E
	cmpi.w #55,(a0)+
	beq.b abs_0_0005EB0E
	cmpi.w #55,(a0)
	bne.b abs_0_0005EAF6
abs_0_0005EB0E:
	lea.l abs_0_00063EF4(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_0000022C.w
	move.w #$1,absolute_slot_000002CC.w
	rts
abs_0_0005EB28:
	cmpi.w #3,absolute_slot_000002CC.w
	bne.b abs_0_0005EAF6
	lea.l abs_0_00063FEA(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_0000022C.w
	rts
abs_0_0005EB44:
	cmpi.w #30,absolute_slot_00000174.w
	bne.b abs_0_0005EAF6
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005EAF6
	lea.l abs_0_00064084(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_0000022C.w
	move.w #$1,absolute_slot_000002F4.w
	rts
abs_0_0005EB6C:
	cmpi.w #2,absolute_slot_00000296.w
	bge.w abs_0_0005EC00
	move.w #$8C,d0
	moveq.l #100,d1
	move.w #$84,d2
	bsr.w abs_0_0005CC5C
	subq.w #1,absolute_slot_0000021E.w
	bge.b abs_0_0005EB90
	move.w #$28,absolute_slot_0000021E.w
abs_0_0005EB90:
	cmpi.w #20,absolute_slot_0000021E.w
	bge.b abs_0_0005EBA8
	move.w #$92,d0
	move.w #$90,d1
	move.w #$93,d2
	bsr.w abs_0_0005CC5C
abs_0_0005EBA8:
	subq.b #1,absolute_slot_0000021D.w
	bge.b abs_0_0005EBB4
	move.b #$50,absolute_slot_0000021D.w
abs_0_0005EBB4:
	cmpi.b #8,absolute_slot_0000021D.w
	bge.b abs_0_0005EBCC
	move.w #$9E,d0
	move.w #$6E,d1
	move.w #$98,d2
	bsr.w abs_0_0005CC5C
abs_0_0005EBCC:
	tst.b absolute_slot_0000022B.w
	bne.b abs_0_0005EC00
	move.w #$94,d0
	moveq.l #38,d1
	move.w #$82,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005EC00
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005EC00
	st.b absolute_slot_0000022B.w
	lea.l abs_0_00062D4A(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005EC00:
	bsr.w abs_0_00060026
	rts
abs_0_0005EC06:
	cmpi.w #269,absolute_slot_0000018C.w
	ble.b abs_0_0005EC14
	move.w #$10D,absolute_slot_0000018C.w
abs_0_0005EC14:
	rts
abs_0_0005EC16:
	lea.l abs_0_0005EE3A(pc),a0
	bsr.w abs_0_0005ECFE
	lea.l abs_0_0005EE4A(pc),a0
	bsr.w abs_0_0005ECFE
	cmpi.w #269,absolute_slot_0000018C.w
	ble.b abs_0_0005EC34
	move.w #$10D,absolute_slot_0000018C.w
abs_0_0005EC34:
	rts
abs_0_0005EC36:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005EC40
	bsr.w abs_0_0005FD4E
abs_0_0005EC40:
	cmpi.w #222,absolute_slot_0000018C.w
	ble.b abs_0_0005EC4E
	move.w #$DE,absolute_slot_0000018C.w
abs_0_0005EC4E:
	rts
abs_0_0005EC50:
	tst.w absolute_slot_000001BA.w
	bne.b abs_0_0005EC6A
	tst.w absolute_slot_000001B8.w
	bne.b abs_0_0005EC60
	bsr.w abs_0_0005EC6C
abs_0_0005EC60:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005EC6A
	bsr.w abs_0_0005FDBC
abs_0_0005EC6A:
	rts
abs_0_0005EC6C:
	lea.l abs_0_00064B50(pc),a0
	lea.l absolute_slot_000001B0.w,a1
	bsr.w abs_0_0005D8AE
	moveq.l #3,d0
	moveq.l #104,d1
	move.w absolute_slot_000001B0.w,d2
	bsr.w abs_0_0005CC5C
	cmpi.w #32,absolute_slot_0000018C.w
	bge.b abs_0_0005ECB8
	lea.l abs_0_0005E17A(pc),a0
	cmpi.w #45,(a0)+
	beq.b abs_0_0005ECB8
	cmpi.w #45,(a0)+
	beq.b abs_0_0005ECB8
	cmpi.w #45,(a0)
	beq.b abs_0_0005ECB8
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005ECB8
	lea.l abs_0_000635EE(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005ECB8:
	cmpi.w #27,absolute_slot_0000018C.w
	bge.b abs_0_0005ECC6
	move.w #$1B,absolute_slot_0000018C.w
abs_0_0005ECC6:
	rts
abs_0_0005ECC8:
	lea.l abs_0_0005EDAA(pc),a0
	bsr.w abs_0_0005ECFE
	rts
abs_0_0005ECD2:
	lea.l abs_0_0005EDBA(pc),a0
	bsr.w abs_0_0005ECFE
	rts
abs_0_0005ECDC:
	lea.l abs_0_0005EDCA(pc),a0
	bsr.w abs_0_0005ECFE
	rts
abs_0_0005ECE6:
	lea.l abs_0_0005EDDA(pc),a0
	bsr.w abs_0_0005ECFE
	rts
abs_0_0005ECF0:
	lea.l abs_0_0005EDEA(pc),a0
	bsr.w abs_0_0005ECFE
	bsr.w abs_0_00060E18
	rts
abs_0_0005ECFE:
	clr.w absolute_slot_0000024A.w
	move.l a0,-(a7)
	bsr.b abs_0_0005ED0C
	movea.l (a7)+,a0
	bsr.b abs_0_0005ED3A
	rts
abs_0_0005ED0C:
	move.w $000A(a0),d0
	add.w d0,$0002(a0)
	move.w $0002(a0),d0
	cmp.w $0006(a0),d0
	bgt.b abs_0_0005ED24
	neg.w $000A(a0)
	bra.b abs_0_0005ED2E
abs_0_0005ED24:
	cmp.w $0008(a0),d0
	blt.b abs_0_0005ED2E
	neg.w $000A(a0)
abs_0_0005ED2E:
	move.w (a0)+,d0
	move.w (a0)+,d1
	move.w (a0)+,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005ED3A:
	move.w (a0),d0
	bmi.b abs_0_0005ED88
	move.w $000C(a0),d1
	move.w $0002(a0),d2
	add.w $000E(a0),d2
	subq.w #1,d2
	moveq.l #6,d3
	tst.w absolute_slot_000001C2.w
	bmi.b abs_0_0005ED88
	bsr.w abs_0_0005F47C
	tst.w d0
	beq.b abs_0_0005ED88
	move.w $0002(a0),d0
	add.w $000E(a0),d0
	move.w d0,absolute_slot_0000018E.w
	move.w absolute_slot_0000018E.w,absolute_slot_000001CA.w
	tst.w $000A(a0)
	beq.b abs_0_0005ED7A
	move.w #$1,absolute_slot_0000024A.w
abs_0_0005ED7A:
	move.l a0,-(a7)
	bsr.w abs_0_0005D74E
	movea.l (a7)+,a0
	move.w #$10,absolute_slot_000001C2.w
abs_0_0005ED88:
	rts
abs_0_0005ED8A:
	tst.w absolute_slot_000002DE.w
	beq.b abs_0_0005EDA8
	lea.l abs_0_0005EE5A(pc),a0
	bsr.w abs_0_0005ECFE
	lea.l abs_0_0005EE6A(pc),a0
	bsr.w abs_0_0005ECFE
	lea.l abs_0_0006064A(pc),a0
	bsr.w abs_0_00060396
abs_0_0005EDA8:
	rts
abs_0_0005EDAA:
	dc.b $01,$06,$00,$50,$00,$A0,$00,$24,$00,$8C,$00,$01,$00,$1A,$00,$00
abs_0_0005EDBA:
	dc.b $00,$80,$00,$50,$00,$A0,$00,$1E,$00,$96,$00,$01,$00,$1A,$00,$00
abs_0_0005EDCA:
	dc.b $00,$C0,$00,$50,$00,$A0,$00,$1E,$00,$82,$00,$01,$00,$1A,$00,$00
abs_0_0005EDDA:
	dc.b $00,$80,$00,$50,$00,$A0,$00,$1E,$00,$A0,$FF,$FF,$00,$1A,$00,$00
abs_0_0005EDEA:
	dc.b $00,$60,$00,$50,$00,$A0,$00,$1A,$00,$80,$FF,$FF,$00,$1A,$00,$00
abs_0_0005EDFA:
	dc.b $00,$9C,$00,$46,$00,$AC,$00,$46,$00,$82,$00,$01,$00,$1A,$00,$00
abs_0_0005EE0A:
	dc.b $00,$30,$00,$82,$00,$AC,$00,$46,$00,$82,$FF,$FF,$00,$1A,$00,$00
abs_0_0005EE1A:
	dc.b $00,$38,$00,$80,$00,$AC,$00,$46,$00,$80,$FF,$FF,$00,$1A,$00,$00
abs_0_0005EE2A:
	dc.b $00,$E8,$00,$46,$00,$AC,$00,$46,$00,$80,$00,$01,$00,$1A,$00,$00
abs_0_0005EE3A:
	dc.b $00,$DC,$00,$AA,$00,$AC,$00,$AA,$00,$AA,$00,$00,$00,$1A,$00,$00
abs_0_0005EE4A:
	dc.b $00,$A8,$00,$5A,$00,$AC,$00,$5A,$00,$5A,$00,$00,$00,$1A,$00,$00
abs_0_0005EE5A:
	dc.b $00,$68,$00,$0A,$00,$E5,$00,$0A,$00,$64,$00,$01,$00,$22,$00,$08
abs_0_0005EE6A:
	dc.b $00,$B6,$00,$64,$00,$E5,$00,$0A,$00,$64,$FF,$FF,$00,$22,$00,$08
abs_0_0005EE7A:
	lea.l abs_0_00064B0E(pc),a0
	lea.l absolute_slot_000001D8.w,a1
	bsr.w abs_0_0005D8AE
	rts
abs_0_0005EE88:
	bsr.w abs_0_0005EF1C
	bsr.b abs_0_0005EEC0
	bsr.w abs_0_0005EEEC
	moveq.l #120,d0
	move.w absolute_slot_00000260.w,d1
	move.w #$A2,d2
	bsr.w abs_0_0005CC5C
	move.w #$B8,d0
	move.w absolute_slot_00000264.w,d1
	move.w #$A2,d2
	bsr.w abs_0_0005CC5C
	cmpi.w #177,absolute_slot_0000018E.w
	ble.b abs_0_0005EEBE
	moveq.l #-3,d0
	bsr.w abs_0_0005FA82
abs_0_0005EEBE:
	rts
abs_0_0005EEC0:
	lea.l absolute_slot_00000260.w,a0
	bsr.b abs_0_0005EECE
	lea.l absolute_slot_00000264.w,a0
	bsr.b abs_0_0005EECE
	rts
abs_0_0005EECE:
	move.w (a0),d0
	add.w $0002(a0),d0
	cmp.w #$1E,d0
	bge.b abs_0_0005EEDE
	neg.w $0002(a0)
abs_0_0005EEDE:
	cmp.w #$8C,d0
	ble.b abs_0_0005EEE8
	neg.w $0002(a0)
abs_0_0005EEE8:
	move.w d0,(a0)
	rts
abs_0_0005EEEC:
	moveq.l #121,d0
	moveq.l #8,d1
	move.w absolute_slot_00000260.w,d2
	moveq.l #32,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	bne.b abs_0_0005EF14
	move.w #$B9,d0
	moveq.l #8,d1
	move.w absolute_slot_00000264.w,d2
	moveq.l #32,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	bne.b abs_0_0005EF14
	rts
abs_0_0005EF14:
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
	rts
abs_0_0005EF1C:
	cmpi.w #3,absolute_slot_0000026C.w
	beq.b abs_0_0005EF74
	lea.l abs_0_00064B5E(pc),a0
	lea.l absolute_slot_0000026A.w,a1
	bsr.w abs_0_0005D8AE
	tst.w absolute_slot_0000026C.w
	bne.w abs_0_0005EF76
	moveq.l #22,d0
	move.w #$8B,d1
	move.w absolute_slot_0000026A.w,d2
	bsr.w abs_0_0005CC5C
	moveq.l #22,d0
	moveq.l #20,d1
	move.w #$90,d2
	moveq.l #8,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005EF74
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_0005EF74
	lea.l abs_0_0006362A(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$1,absolute_slot_0000026C.w
abs_0_0005EF74:
	rts
abs_0_0005EF76:
	cmpi.w #2,absolute_slot_0000026C.w
	beq.b abs_0_0005EF9E
	moveq.l #8,d1
	moveq.l #42,d2
	move.w #$82,d3
	move.w #$A0,d4
	move.w #$12C,d5
	moveq.l #19,d6
	bsr.w abs_0_0006029C
	move.w #$2,absolute_slot_0000026C.w
	clr.w absolute_slot_00000268.w
abs_0_0005EF9E:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_0005EFC4
	addq.w #1,absolute_slot_00000268.w
	move.w absolute_slot_00000268.w,d0
	andi.w #8,d0
	bne.b abs_0_0005EFC2
	moveq.l #22,d0
	move.w #$8B,d1
	move.w absolute_slot_0000026A.w,d2
	bsr.w abs_0_0005CC5C
abs_0_0005EFC2:
	rts
abs_0_0005EFC4:
	move.w #$3,absolute_slot_0000026C.w
	addq.w #1,absolute_slot_000002EE.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_0005EFDA:
	bsr.w abs_0_0005F02C
	bsr.w abs_0_0005F090
	tst.w absolute_slot_0000025E.w
	bne.b abs_0_0005F02A
	move.w absolute_slot_0000029C.w,d0
	move.w #$75,d1
	move.w #$AA,d2
	bsr.w abs_0_0005CC5C
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005F002
	bsr.w abs_0_0005F04E
abs_0_0005F002:
	move.w absolute_slot_0000018C.w,d0
	move.w absolute_slot_0000029C.w,d1
	sub.w d0,d1
	beq.b abs_0_0005F02A
	bmi.b abs_0_0005F01E
	cmpi.w #0,absolute_slot_0000029C.w
	ble.b abs_0_0005F02A
	subq.w #1,absolute_slot_0000029C.w
	rts
abs_0_0005F01E:
	cmpi.w #250,absolute_slot_0000029C.w
	bge.b abs_0_0005F02A
	addq.w #1,absolute_slot_0000029C.w
abs_0_0005F02A:
	rts
abs_0_0005F02C:
	clr.w absolute_slot_0000025C.w
	lea.l abs_0_0005E17A(pc),a0
	cmpi.w #33,(a0)+
	beq.b abs_0_0005F046
	cmpi.w #33,(a0)+
	beq.b abs_0_0005F046
	cmpi.w #33,(a0)
	bne.b abs_0_0005F04C
abs_0_0005F046:
	move.w #$1,absolute_slot_0000025C.w
abs_0_0005F04C:
	rts
abs_0_0005F04E:
	move.w absolute_slot_0000029C.w,d0
	moveq.l #26,d1
	moveq.l #117,d2
	moveq.l #60,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	bne.b abs_0_0005F062
	rts
abs_0_0005F062:
	tst.w absolute_slot_0000025C.w
	beq.b abs_0_0005F088
	lea.l abs_0_00063828(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$1,absolute_slot_0000025E.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_0005F088:
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
	rts
abs_0_0005F090:
	cmpi.w #297,absolute_slot_0000018C.w
	ble.b abs_0_0005F0A4
	move.w #$115,absolute_slot_0000018C.w
	clr.w absolute_slot_0000029C.w
	rts
abs_0_0005F0A4:
	cmpi.w #277,absolute_slot_0000018C.w
	ble.b abs_0_0005F0B2
	move.w #$12D,absolute_slot_0000018C.w
abs_0_0005F0B2:
	rts
abs_0_0005F0B4:
	bsr.w abs_0_00061C4E
	rts
abs_0_0005F0BA:
	bsr.w abs_0_00061C2C
	cmpi.w #4,absolute_slot_0000018C.w
	bge.b abs_0_0005F0CE
	move.w #$37,absolute_slot_0000018C.w
	rts
abs_0_0005F0CE:
	cmpi.w #54,absolute_slot_0000018C.w
	bge.b abs_0_0005F0DC
	move.w #$FFFF,absolute_slot_0000018C.w
abs_0_0005F0DC:
	rts
abs_0_0005F0DE:
	cmpi.w #14,absolute_slot_0000018C.w
	bge.b abs_0_0005F0EC
	move.w #$E,absolute_slot_0000018C.w
abs_0_0005F0EC:
	lea.l abs_0_0005EE1A(pc),a0
	bsr.w abs_0_0005ECFE
	lea.l abs_0_0005EE2A(pc),a0
	bsr.w abs_0_0005ECFE
	lea.l abs_0_000605D6(pc),a0
	bsr.w abs_0_00060396
	bsr.w abs_0_0005F10A
	rts
abs_0_0005F10A:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005F12A
	cmpi.w #2,absolute_slot_000002CC.w
	bne.b abs_0_0005F12A
	addq.w #1,absolute_slot_000002CC.w
	lea.l abs_0_00063F6E(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005F12A:
	rts
abs_0_0005F12C:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005F136
	bsr.w abs_0_0005FF16
abs_0_0005F136:
	moveq.l #6,d3
	moveq.l #85,d1
	bsr.w abs_0_0005F16A
	move.l #$60206,absolute_slot_00000138.w
	rts
abs_0_0005F148:
	moveq.l #11,d3
	moveq.l #0,d1
	bsr.w abs_0_0005F16A
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0005F15A
	bsr.w abs_0_00060810
abs_0_0005F15A:
	bsr.w abs_0_000607BE
	rts
abs_0_0005F160:
	moveq.l #1,d3
	moveq.l #0,d1
	bsr.w abs_0_0005F16A
	rts
abs_0_0005F16A:
	move.w absolute_slot_0000025A.w,d0
	beq.b abs_0_0005F17A
	cmp.w #$1,d0
	bne.b abs_0_0005F196
	addq.w #1,absolute_slot_0000025A.w
abs_0_0005F17A:
	move.w #$90,d0
	move.w #$AB,d2
abs_0_0005F182:
	movem.w d0-d3,-(a7)
	bsr.w abs_0_0005CC5C
	movem.w (a7)+,d0-d3
	addi.w #16,d1
	dbf.w d3,abs_0_0005F182
abs_0_0005F196:
	rts
abs_0_0005F198:
	moveq.l #48,d0
	moveq.l #68,d1
	move.w absolute_slot_000001D8.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005F1A6:
	cmpi.w #80,absolute_slot_0000018C.w
	ble.b abs_0_0005F1B0
	rts
abs_0_0005F1B0:
	move.w #$50,absolute_slot_0000018C.w
	lea.l abs_0_00062F8A(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$FFC2,absolute_slot_000001C2.w
	lea.l abs_0_00064936(pc),a0
	move.w #$3,absolute_slot_000001C0.w
	bsr.w abs_0_0005D8A2
	move.l a0,absolute_slot_00000192.w
	moveq.l #-6,d0
	bsr.w abs_0_0005FA82
	rts
abs_0_0005F1E4:
	move.w absolute_slot_0000018C.w,d4
	move.w d4,d5
	addi.w #18,d5
	cmp.w d5,d0
	bge.b abs_0_0005F210
	add.w d1,d0
	cmp.w d4,d0
	ble.b abs_0_0005F210
	move.w absolute_slot_0000018E.w,d4
	move.w d4,d5
	subi.w #22,d4
	cmp.w d5,d2
	bge.b abs_0_0005F210
	add.w d3,d2
	cmp.w d4,d2
	ble.b abs_0_0005F210
	moveq.l #1,d0
	bra.b abs_0_0005F212
abs_0_0005F210:
	moveq.l #0,d0
abs_0_0005F212:
	rts
abs_0_0005F214:
	lea.l abs_0_0005F2B6(pc),a0
	moveq.l #2,d7
abs_0_0005F21A:
	tst.w (a0)
	beq.b abs_0_0005F224
	subq.w #1,(a0)
	bra.w abs_0_0005F2AC
abs_0_0005F224:
	subq.w #1,$0004(a0)
	not.w $0008(a0)
	beq.b abs_0_0005F232
	addq.w #1,$0002(a0)
abs_0_0005F232:
	cmpi.w #102,$0004(a0)
	beq.b abs_0_0005F262
	cmpi.w #86,$0004(a0)
	beq.b abs_0_0005F262
	cmpi.w #66,$0004(a0)
	beq.b abs_0_0005F262
	cmpi.w #64,$0004(a0)
	beq.b abs_0_0005F262
	cmpi.w #60,$0004(a0)
	beq.b abs_0_0005F262
	cmpi.w #58,$0004(a0)
	bne.b abs_0_0005F274
abs_0_0005F262:
	cmpi.w #70,$0006(a0)
	bne.b abs_0_0005F270
	move.w #$4E,$0006(a0)
abs_0_0005F270:
	addq.w #1,$0006(a0)
abs_0_0005F274:
	cmpi.w #56,$0004(a0)
	bne.b abs_0_0005F294
	move.w #$2C,(a0)
	move.w #$9B,$0002(a0)
	move.w #$72,$0004(a0)
	move.w #$44,$0006(a0)
	bra.b abs_0_0005F2AC
abs_0_0005F294:
	move.w $0002(a0),d0
	move.w $0004(a0),d1
	move.w $0006(a0),d2
	movem.l d7/a0,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d7/a0
abs_0_0005F2AC:
	lea.l $000A(a0),a0
	dbf.w d7,abs_0_0005F21A
	rts
abs_0_0005F2B6:
	dc.b $00,$00,$00,$9B,$00,$6E,$00,$44,$00,$00,$00,$00,$00,$A0,$00,$62
	dc.b $00,$45,$00,$00,$00,$00,$00,$A5,$00,$56,$00,$45,$00,$00
abs_0_0005F2D4:
	lea.l abs_0_00064A7E(pc),a0
	lea.l absolute_slot_000001AC.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$96,d0
	move.w #$72,d1
	move.w absolute_slot_000001AC.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005F2F2:
	lea.l absolute_slot_000001AE.w,a1
	lea.l abs_0_00064AB2(pc),a0
	cmpi.w #136,absolute_slot_0000018C.w
	ble.b abs_0_0005F312
	lea.l abs_0_00064A96(pc),a0
	cmpi.w #190,absolute_slot_0000018C.w
	bge.b abs_0_0005F312
	lea.l abs_0_00064ACE(pc),a0
abs_0_0005F312:
	bsr.w abs_0_0005D8AE
	move.w #$A0,d0
	move.w #$7C,d1
	move.w absolute_slot_000001AE.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005F328:
	move.l a0,-(a7)
	lea.l abs_0_000623A4(pc),a1
	move.w absolute_slot_000001CE.w,d6
abs_0_0005F332:
	move.w (a0),d0
	bmi.b abs_0_0005F35A
	moveq.l #83,d2
	addq.w #8,d6
	andi.w #62,d6
	move.w $0(a1,d6.w),d1
	add.w $0006(a0),d1
	move.w d1,$0002(a0)
	movem.l d6/a0-a1,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d6/a0-a1
	addq.w #8,a0
	bra.b abs_0_0005F332
abs_0_0005F35A:
	addq.w #2,absolute_slot_000001CE.w
	movea.l (a7)+,a0
	bsr.w abs_0_0005F366
	rts
abs_0_0005F366:
	clr.w absolute_slot_0000024A.w
	moveq.l #0,d7
abs_0_0005F36C:
	move.w (a0)+,d0
	bmi.b abs_0_0005F3B6
	moveq.l #26,d1
	move.w (a0)+,d2
	subq.w #1,d2
	moveq.l #6,d3
	clr.w (a0)
	tst.w d7
	bne.b abs_0_0005F3B2
	tst.w absolute_slot_000001C2.w
	bmi.b abs_0_0005F3B2
	bsr.w abs_0_0005F47C
	tst.w d0
	beq.b abs_0_0005F3B2
	move.w #$1,(a0)
	move.w -$0002(a0),absolute_slot_0000018E.w
	move.w absolute_slot_0000018E.w,absolute_slot_000001CA.w
	move.w #$1,absolute_slot_0000024A.w
	move.l a0,-(a7)
	bsr.w abs_0_0005D74E
	movea.l (a7)+,a0
	moveq.l #1,d7
	move.w #$10,absolute_slot_000001C2.w
abs_0_0005F3B2:
	addq.w #4,a0
	bra.b abs_0_0005F36C
abs_0_0005F3B6:
	rts
abs_0_0005F3B8:
	dc.b $00,$AC,$00,$91,$00,$00,$00,$91
abs_0_0005F3C0:
	dc.b $00,$FC
abs_0_0005F3C2:
	dc.b $00,$91,$00,$00,$00,$91,$FF,$FF
abs_0_0005F3CA:
	dc.b $01,$0A,$00,$91,$00,$00,$00,$91,$FF,$FF
abs_0_0005F3D4:
	dc.b $00,$20,$00,$91,$00,$00,$00,$91,$00,$70,$00,$91,$00,$00,$00,$91
	dc.b $00,$C0,$00,$91,$00,$00,$00,$91,$FF,$FF
abs_0_0005F3EE:
	bsr.w abs_0_00061212
	move.w absolute_slot_0000020C.w,d0
	move.w #$90,d1
	move.w absolute_slot_0000020E.w,d2
	bsr.w abs_0_0005CC5C
	move.w absolute_slot_00000210.w,d0
	add.w d0,$020C.w
	cmpi.w #80,absolute_slot_0000020C.w
	bge.b abs_0_0005F420
	move.w #$1,absolute_slot_00000210.w
	move.w #$96,absolute_slot_0000020E.w
	rts
abs_0_0005F420:
	cmpi.w #244,absolute_slot_0000020C.w
	ble.b abs_0_0005F434
	move.w #$FFFF,absolute_slot_00000210.w
	move.w #$95,absolute_slot_0000020E.w
abs_0_0005F434:
	rts
abs_0_0005F436:
	move.w absolute_slot_000001A8.w,d7
	clr.w absolute_slot_000001A8.w
	tst.w absolute_slot_000001C2.w
	bmi.b abs_0_0005F47A
	lea.l absolute_slot_00000610.w,a0
	moveq.l #7,d6
abs_0_0005F44A:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005F47A
	move.w (a0)+,d0
	move.w (a0)+,d1
	move.w (a0)+,d2
	move.w (a0)+,d3
	bsr.w abs_0_0005F47C
	tst.w d0
	beq.b abs_0_0005F476
	move.w #$1,absolute_slot_000001A8.w
	move.w absolute_slot_0000018E.w,absolute_slot_000001CA.w
	tst.w d7
	beq.b abs_0_0005F47A
	addq.w #1,absolute_slot_000001AA.w
	bra.b abs_0_0005F47A
abs_0_0005F476:
	dbf.w d6,abs_0_0005F44A
abs_0_0005F47A:
	rts
abs_0_0005F47C:
	move.w absolute_slot_0000018C.w,d4
	move.w d4,d5
	addi.w #18,d5
	cmp.w d5,d0
	bge.b abs_0_0005F4A2
	add.w d1,d0
	cmp.w d4,d0
	ble.b abs_0_0005F4A2
	move.w absolute_slot_0000018E.w,d4
	cmp.w d4,d2
	bge.b abs_0_0005F4A2
	add.w d3,d2
	cmp.w d4,d2
	ble.b abs_0_0005F4A2
	moveq.l #1,d0
	bra.b abs_0_0005F4A4
abs_0_0005F4A2:
	moveq.l #0,d0
abs_0_0005F4A4:
	rts
abs_0_0005F4A6:
	dc.b $00,$06,$00,$2C,$00,$44,$00,$60,$00,$0F,$00,$06,$00,$FE,$00,$42
	dc.b $00,$46,$00,$09,$00,$1C,$00,$0F,$00,$40,$00,$73,$00,$0C,$00,$1F
	dc.b $00,$C0,$00,$60,$00,$82,$00,$0D,$00,$20,$00,$21,$00,$7C,$00,$91
	dc.b $00,$0E,$00,$20,$00,$B1,$00,$3A,$00,$B4,$00,$0B,$00,$20,$00,$60
	dc.b $00,$3C,$00,$64,$00,$0B,$00,$20,$00,$C0,$00,$5B,$00,$64,$00,$0B
	dc.b $00,$20,$00,$2D,$00,$3F,$00,$34,$00,$0B,$FF,$FF
abs_0_0005F502:
	lea.l absolute_slot_00000610.w,a0
	moveq.l #7,d0
abs_0_0005F508:
	move.l #$FFFFFFFF,(a0)+
	move.l #$FFFFFFFF,(a0)+
	dbf.w d0,abs_0_0005F508
	lea.l abs_0_0005F4A6(pc),a0
	lea.l absolute_slot_00000610.w,a1
	moveq.l #0,d0
	move.w absolute_slot_000001DE.w,d1
abs_0_0005F526:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005F54E
	cmp.w (a0),d1
	bne.b abs_0_0005F548
	move.w $0002(a0),(a1)+
	move.w $0004(a0),(a1)+
	move.w $0006(a0),(a1)+
	move.w $0008(a0),(a1)+
	addq.w #1,d0
	cmp.w #$8,d0
	beq.b abs_0_0005F54E
abs_0_0005F548:
	lea.l $000A(a0),a0
	bra.b abs_0_0005F526
abs_0_0005F54E:
	rts
abs_0_0005F550:
	move.w d0,absolute_slot_000001A4.w
	move.w d1,absolute_slot_000001A6.w
	move.l a0,absolute_slot_0000019E.w
	bsr.w abs_0_0005D8A2
	rts
abs_0_0005F562:
	tst.l absolute_slot_0000019E.w
	bne.b abs_0_0005F56A
	rts
abs_0_0005F56A:
	movea.l absolute_slot_0000019E.w,a0
	lea.l absolute_slot_000001A2.w,a1
	bsr.w abs_0_0005D8AE
	cmpi.w #87,absolute_slot_000001A2.w
	beq.b abs_0_0005F590
	move.w absolute_slot_000001A4.w,d0
	move.w absolute_slot_000001A6.w,d1
	move.w absolute_slot_000001A2.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005F590:
	clr.l absolute_slot_0000019E.w
	clr.w absolute_slot_000001A2.w
	rts
abs_0_0005F59A:
	movea.l absolute_slot_000001E0.w,a0
	move.w absolute_slot_0000018C.w,d0
	addq.w #8,d0
	lsr.w #4,d0
	add.w d0,d0
	adda.w d0,a0
	move.w absolute_slot_0000018E.w,d0
	lsr.w #4,d0
	mulu.w #$28,d0
	adda.w d0,a0
	move.w (a0),d0
	lea.l abs_0_0005F62E(pc),a0
abs_0_0005F5BC:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005F5DC
	cmp.w (a0),d0
	bne.b abs_0_0005F5D8
	move.w absolute_slot_0000018E.w,d0
	andi.w #15,d0
	move.w $0002(a0),d1
	cmp.w d1,d0
	ble.b abs_0_0005F5DC
	bra.b abs_0_0005F5DE
abs_0_0005F5D8:
	addq.w #6,a0
	bra.b abs_0_0005F5BC
abs_0_0005F5DC:
	rts
abs_0_0005F5DE:
	move.w #$1,absolute_slot_000001C8.w
	bsr.w abs_0_0005F842
	move.w absolute_slot_0000018E.w,d0
	andi.w #65520,d0
	add.w $0002(a0),d0
	addi.w #10,d0
	move.w d0,absolute_slot_0000018E.w
	move.w absolute_slot_0000018C.w,d0
	subq.w #3,d0
	move.w absolute_slot_0000018E.w,d1
	subi.w #36,d1
	move.w $0004(a0),d2
	lea.l abs_0_00064ADC(pc),a0
	tst.w d2
	beq.b abs_0_0005F61A
	lea.l abs_0_00064AEE(pc),a0
abs_0_0005F61A:
	bsr.w abs_0_0005F550
	lea.l abs_0_00064B00(pc),a0
	move.l a0,absolute_slot_00000192.l
	bsr.w abs_0_0005D8A2
	rts
abs_0_0005F62E:
	dc.b $00,$0F,$00,$08,$00,$00,$02,$B4,$00,$08,$00,$00,$02,$B5,$00,$08
	dc.b $00,$00,$02,$B6,$00,$08,$00,$00,$02,$B7,$00,$08,$00,$00,$01,$E0
	dc.b $00,$08,$00,$01,$FF,$FF
abs_0_0005F654:
	tst.w absolute_slot_000001D2.w
	beq.b abs_0_0005F662
	bsr.w abs_0_0005F664
	bsr.w abs_0_0005F7EA
abs_0_0005F662:
	rts
abs_0_0005F664:
	lea.l abs_0_0005F856(pc),a0
	move.w absolute_slot_000001D4.w,d0
	move.w absolute_slot_000001D6.w,d1
abs_0_0005F670:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005F688
	move.w d0,$000E(a0)
	move.w d1,$0010(a0)
	addi.w #18,d0
	lea.l $0012(a0),a0
	bra.b abs_0_0005F670
abs_0_0005F688:
	lea.l abs_0_0005F856(pc),a0
	lea.l abs_0_000623A4(pc),a1
abs_0_0005F690:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005F6D4
	move.w $000A(a0),d0
	add.w d0,$0006(a0)
	andi.w #63,$0006(a0)
	move.w $0006(a0),d0
	andi.w #62,d0
	move.w $0(a1,d0.w),$0002(a0)
	move.w $000C(a0),d0
	add.w d0,$0008(a0)
	andi.w #63,$0008(a0)
	move.w $0008(a0),d0
	andi.w #62,d0
	move.w $0(a1,d0.w),$0004(a0)
	lea.l $0012(a0),a0
	bra.b abs_0_0005F690
abs_0_0005F6D4:
	cmpi.w #64,absolute_slot_000001D6.w
	bge.b abs_0_0005F6E2
	addq.w #2,absolute_slot_000001D6.w
	rts
abs_0_0005F6E2:
	addq.w #1,absolute_slot_000001D2.w
	cmpi.w #40,absolute_slot_000001D2.w
	beq.b abs_0_0005F6F8
	cmpi.w #41,absolute_slot_000001D2.w
	bge.b abs_0_0005F71C
	rts
abs_0_0005F6F8:
	moveq.l #-1,d0
	bsr.w abs_0_0005D48A
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	moveq.l #63,d0
	bsr.w abs_0_0005FA82
	tst.w absolute_slot_00000170.w
	bge.b abs_0_0005F71A
	move.w #$1,absolute_slot_000002F6.w
abs_0_0005F71A:
	rts
abs_0_0005F71C:
	tst.w absolute_slot_000001E6.w
	beq.b abs_0_0005F724
	rts
abs_0_0005F724:
	clr.w absolute_slot_000001D2.w
abs_0_0005F728:
	move.l #abs_0_0006490E,absolute_slot_00000192.w
	movea.l absolute_slot_00000192.w,a0
	bsr.w abs_0_0005D8A2
	clr.w absolute_slot_000001C0.w
	clr.w absolute_slot_000001BE.w
	clr.w absolute_slot_000001C2.w
	clr.w absolute_slot_0000029C.w
	clr.w absolute_slot_00000294.w
	lea.l abs_0_00064BBA(pc),a0
	bsr.w abs_0_0005D8A2
	clr.l absolute_slot_00000300.w
	clr.l absolute_slot_00000304.w
	cmpi.w #36,absolute_slot_000001DE.w
	beq.b abs_0_0005F76C
	cmpi.w #39,absolute_slot_000001DE.w
	bne.b abs_0_0005F780
abs_0_0005F76C:
	move.w #$17,absolute_slot_000001DE.w
	move.w #$75,absolute_slot_0000018C.w
	move.w #$5C,absolute_slot_0000018E.w
	bra.b abs_0_0005F7D6
abs_0_0005F780:
	cmpi.w #27,absolute_slot_000001DE.w
	bne.b abs_0_0005F796
	move.w #$E6,absolute_slot_0000018C.w
	move.w #$A0,absolute_slot_0000018E.w
	bra.b abs_0_0005F7D6
abs_0_0005F796:
	cmpi.w #52,absolute_slot_000001DE.w
	bne.b abs_0_0005F7AC
	move.w #$123,absolute_slot_0000018C.w
	move.w #$B1,absolute_slot_0000018E.w
	bra.b abs_0_0005F7D6
abs_0_0005F7AC:
	move.w absolute_slot_00000182.w,absolute_slot_0000018C.w
	move.w absolute_slot_00000184.w,absolute_slot_0000018E.w
	tst.l absolute_slot_00000182.w
	bne.b abs_0_0005F7D6
	move.w absolute_slot_00000188.l,absolute_slot_0000018C.w
	move.w absolute_slot_0000018A.l,absolute_slot_0000018E.w
	move.w absolute_slot_00000186.l,absolute_slot_000001DE.w
abs_0_0005F7D6:
	clr.w absolute_slot_000001C8.w
	bsr.w abs_0_0005C992
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_0005F7EA:
	lea.l abs_0_0005F856(pc),a0
	lea.l abs_0_0005F8D6(pc),a1
abs_0_0005F7F2:
	cmpi.w #$FFFF,(a0)
	beq.b abs_0_0005F840
	subq.w #1,(a1)
	bne.b abs_0_0005F810
	move.w #$200,d0
	bsr.w abs_0_0005C7F6
	andi.w #7,d0
	addq.w #4,d0
	move.w d0,(a1)
	not.w $0002(a1)
abs_0_0005F810:
	move.w (a0),d2
	tst.w $0002(a1)
	beq.b abs_0_0005F81C
	addi.w #6,d2
abs_0_0005F81C:
	move.w $0002(a0),d0
	move.w $0004(a0),d1
	add.w $000E(a0),d0
	add.w $0010(a0),d1
	movem.l a0-a1,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,a0-a1
	addq.w #4,a1
	lea.l $0012(a0),a0
	bra.b abs_0_0005F7F2
abs_0_0005F840:
	rts
abs_0_0005F842:
	move.w #$64,absolute_slot_000001D4.w
	move.w #$FFF0,absolute_slot_000001D6.w
	move.w #$1,absolute_slot_000001D2.w
	rts
abs_0_0005F856:
	dc.b $00,$57,$00,$00,$00,$00,$00,$20,$00,$00,$FF,$FD,$00,$01,$00,$80
	dc.b $00,$40,$00,$58
	dcb.b $8,$00
	dc.b $FF,$FE,$00,$01,$00,$90,$00,$40,$00,$59
	dcb.b $9,$00
	dc.b $02,$00,$03,$00,$A0,$00,$40,$00,$59
	dcb.b $8,$00
	dc.b $FF,$FC,$00,$03,$00,$B0,$00,$40,$00,$5A
	dcb.b $9,$00
	dc.b $01,$FF,$FD,$00,$C0,$00,$40,$00,$5B
	dcb.b $9,$00
	dc.b $02,$00,$03,$00,$D0,$00,$40,$00,$5C
	dcb.b $9,$00
	dc.b $03,$00,$02,$00,$E0,$00,$40,$FF,$FF
abs_0_0005F8D6:
	dc.b $00,$01,$00,$00,$00,$02,$FF,$FF,$00,$03,$00,$00,$00,$04,$00,$00
	dc.b $00,$05,$FF,$FF,$00,$06,$00,$00,$00,$07,$FF,$FF
abs_0_0005F8F2:
	dc.w $8000,$C000,$E000,$F000,$F800,$FC00,$FE00,$FF00	; lookup_table
	dc.w $FF80,$FFC0,$FFE0,$FFF0,$FFF8,$FFFC,$FFFE,$FFFF	; lookup_table
abs_0_0005F912:
	tst.b absolute_slot_0000017E.w
	bne.b abs_0_0005F91A
	rts
abs_0_0005F91A:
	sf.b absolute_slot_0000017E.w
	lea.l absolute_slot_0002E6B6.l,a0
	lea.l absolute_slot_000309D8.l,a1
	bsr.w abs_0_0005F994
	move.w #$9F0,$0040(a6)
	clr.w $0042(a6)
	move.w #$FFFF,$0044(a6)
	move.w absolute_slot_00000172.w,d0
	move.w d0,d1
	andi.w #15,d0
	add.w d0,d0
	move.w abs_0_0005F8F2(pc,d0.w),$0046(a6)
	andi.w #65520,d1
	lsr.w #4,d1
	addq.w #1,d1
	move.w #$200,d0
	or.w d1,d0
	moveq.l #40,d2
	add.w d1,d1
	sub.w d1,d2
	move.w d2,$0064(a6)
	move.w d2,$0066(a6)
	moveq.l #3,d1
abs_0_0005F96E:
	move.l a0,$0050(a6)
	move.l a1,$0054(a6)
	move.w d0,$0058(a6)
abs_0_0005F97A:
	btst.b #6,$0002(a6)
	bne.b abs_0_0005F97A
	lea.l $0370(a0),a0
	lea.l $0A00(a1),a1
	dbf.w d1,abs_0_0005F96E
	bsr.w abs_0_0005F9CA
	rts
abs_0_0005F994:
	move.w #$100,$0040(a6)
	moveq.l #-1,d0
	move.l d0,$0044(a6)
	clr.w $0042(a6)
	move.w #$20,$0066(a6)
	movea.l a1,a2
	moveq.l #3,d0
abs_0_0005F9AE:
	move.l a2,$0054(a6)
	move.w #$204,$0058(a6)
abs_0_0005F9B8:
	btst.b #6,$0002(a6)
	bne.b abs_0_0005F9B8
	lea.l $0A00(a2),a2
	dbf.w d0,abs_0_0005F9AE
	rts
abs_0_0005F9CA:
	lea.l absolute_slot_0002E6BE.l,a0
	lea.l absolute_slot_000309D8.l,a1
	bsr.b abs_0_0005F9E8
	lea.l absolute_slot_0002E7FE.l,a0
	lea.l absolute_slot_000309DE.l,a1
	bsr.b abs_0_0005F9E8
	rts
abs_0_0005F9E8:
	moveq.l #3,d0
abs_0_0005F9EA:
	move.w $0002(a0),d1
	not.w d1
	and.w d1,(a1)
	move.w (a0),d1
	or.w d1,(a1)
	move.w $002A(a0),d1
	not.w d1
	and.w d1,$0028(a1)
	move.w $0028(a0),d1
	or.w d1,$0028(a1)
	move.w $0052(a0),d1
	not.w d1
	and.w d1,$0050(a1)
	move.w $0050(a0),d1
	or.w d1,$0050(a1)
	move.w $007A(a0),d1
	not.w d1
	and.w d1,$0078(a1)
	move.w $0078(a0),d1
	or.w d1,$0078(a1)
	move.w $00A2(a0),d1
	not.w d1
	and.w d1,$00A0(a1)
	move.w $00A0(a0),d1
	or.w d1,$00A0(a1)
	move.w $00CA(a0),d1
	not.w d1
	and.w d1,$00C8(a1)
	move.w $00C8(a0),d1
	or.w d1,$00C8(a1)
	move.w $00F2(a0),d1
	not.w d1
	and.w d1,$00F0(a1)
	move.w $00F0(a0),d1
	or.w d1,$00F0(a1)
	move.w $011A(a0),d1
	not.w d1
	and.w d1,$0118(a1)
	move.w $0118(a0),d1
	or.w d1,$0118(a1)
	lea.l $0370(a0),a0
	lea.l $0A00(a1),a1
	dbf.w d0,abs_0_0005F9EA
	rts
abs_0_0005FA82:
	st.b absolute_slot_0000017E.w
	add.w d0,$0172.w
	cmpi.w #63,absolute_slot_00000172.w
	ble.b abs_0_0005FA98
	move.w #$3F,absolute_slot_00000172.w
abs_0_0005FA98:
	tst.w absolute_slot_00000172.w
	bge.b abs_0_0005FAA2
	clr.w absolute_slot_00000172.w
abs_0_0005FAA2:
	rts
abs_0_0005FAA4:
	move.l a1,-(a7)
	moveq.l #0,d7
	bsr.w abs_0_0005FAF8
	bsr.w abs_0_0005FB22
	bsr.w abs_0_0005FB86
	bsr.w abs_0_0005FBDC
	bsr.w abs_0_0005FC54
	bsr.w abs_0_0005FC90
	bsr.w abs_0_0005FCCC
	bsr.w abs_0_0005FD0C
	bsr.w abs_0_0005FD6A
	bsr.w abs_0_0005FD98
	bsr.w abs_0_0005FE3E
	bsr.w abs_0_0005FEE2
	bsr.w abs_0_0005FF46
	bsr.w abs_0_0005FFFA
	bsr.w abs_0_000600B4
	bsr.w abs_0_0006012C
	bsr.w abs_0_000600EE
	bsr.w abs_0_000601D6
	bsr.w abs_0_0006010E
	movea.l (a7)+,a1
	rts
abs_0_0005FAF8:
	cmpi.w #30,$0008(a1)
	bne.b abs_0_0005FB20
	cmpi.w #24,absolute_slot_000001DE.w
	bne.b abs_0_0005FB20
	cmpi.w #54,absolute_slot_0000018C.w
	bge.b abs_0_0005FB20
	moveq.l #1,d7
	move.w d7,absolute_slot_00000232.w
	move.l #$5000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FB20:
	rts
abs_0_0005FB22:
	tst.w absolute_slot_0000023E.w
	bne.b abs_0_0005FB60
	cmpi.w #31,$0008(a1)
	bne.b abs_0_0005FB60
	cmpi.w #7,absolute_slot_000001DE.w
	bne.b abs_0_0005FB60
	move.w #$9A,d0
	moveq.l #35,d1
	moveq.l #120,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FB60
	move.w #$1F,(a0)
	move.w #$2,absolute_slot_0000023E.w
	moveq.l #1,d7
	move.l #$5000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FB60:
	rts
abs_0_0005FB62:
	cmpi.w #2,absolute_slot_0000023E.w
	bne.b abs_0_0005FB84
	subq.w #1,absolute_slot_0000023E.w
	lea.l abs_0_00063258(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	lea.l absolute_slot_00000494.w,a0
	move.w #$7,(a0)
abs_0_0005FB84:
	rts
abs_0_0005FB86:
	cmpi.w #39,$0008(a1)
	bne.b abs_0_0005FBB8
	cmpi.w #11,absolute_slot_000001DE.w
	bne.b abs_0_0005FBB8
	move.w #$96,d0
	moveq.l #20,d1
	moveq.l #50,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FBB8
	moveq.l #1,d7
	move.w d7,absolute_slot_00000240.w
	move.l #$5000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FBB8:
	rts
abs_0_0005FBBA:
	tst.w absolute_slot_00000240.w
	beq.b abs_0_0005FBDA
	lea.l absolute_slot_000004A8.w,a0
	move.w #$B,(a0)
	clr.w absolute_slot_00000240.w
	lea.l abs_0_00063068(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005FBDA:
	rts
abs_0_0005FBDC:
	cmpi.w #32,$0008(a1)
	bne.b abs_0_0005FC10
	cmpi.w #2,absolute_slot_000001DE.w
	bne.b abs_0_0005FC10
	move.w #$80,d0
	moveq.l #18,d1
	move.w #$8C,d2
	moveq.l #10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FC10
	moveq.l #1,d7
	move.w d7,absolute_slot_00000242.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FC10:
	rts
abs_0_0005FC12:
	cmpi.w #1,absolute_slot_00000242.w
	bne.b abs_0_0005FC32
	clr.w absolute_slot_00000242.w
	move.w #$1,absolute_slot_00000244.w
	lea.l abs_0_000632FE(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005FC32:
	rts
abs_0_0005FC34:
	cmpi.w #2,absolute_slot_00000242.w
	bne.b abs_0_0005FC52
	clr.w absolute_slot_00000242.w
	addq.w #1,absolute_slot_00000244.w
	lea.l abs_0_0006349E(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005FC52:
	rts
abs_0_0005FC54:
	tst.w absolute_slot_00000244.w
	beq.b abs_0_0005FC8E
	cmpi.w #38,$0008(a1)
	bne.b abs_0_0005FC8E
	cmpi.w #2,absolute_slot_000001DE.w
	bne.b abs_0_0005FC8E
	move.w #$80,d0
	moveq.l #18,d1
	move.w #$8C,d2
	moveq.l #10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FC8E
	moveq.l #2,d7
	move.w d7,absolute_slot_00000242.w
	move.l #$1000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FC8E:
	rts
abs_0_0005FC90:
	tst.w absolute_slot_00000244.w
	beq.b abs_0_0005FCCA
	cmpi.w #41,$0008(a1)
	bne.b abs_0_0005FCCA
	cmpi.w #2,absolute_slot_000001DE.w
	bne.b abs_0_0005FCCA
	move.w #$80,d0
	moveq.l #18,d1
	move.w #$8C,d2
	moveq.l #10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FCCA
	moveq.l #2,d7
	move.w d7,absolute_slot_00000242.w
	move.l #$1000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FCCA:
	rts
abs_0_0005FCCC:
	tst.w absolute_slot_00000244.w
	beq.b abs_0_0005FD0A
	cmpi.w #51,$0008(a1)
	bne.b abs_0_0005FD0A
	cmpi.w #2,absolute_slot_000001DE.w
	bne.b abs_0_0005FD0A
	move.w #$80,d0
	moveq.l #18,d1
	move.w #$8C,d2
	moveq.l #10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FD0A
	moveq.l #1,d7
	move.w d7,absolute_slot_000002E2.w
	addq.w #1,absolute_slot_00000244.w
	move.l #$1000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FD0A:
	rts
abs_0_0005FD0C:
	tst.w absolute_slot_00000290.w
	bne.b abs_0_0005FD4C
	cmpi.w #44,$0008(a1)
	bne.b abs_0_0005FD4C
	cmpi.w #16,absolute_slot_000001DE.w
	bne.b abs_0_0005FD4C
	move.w #$96,d0
	moveq.l #32,d1
	moveq.l #70,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FD4C
	move.w #$FFFF,(a1)
	move.w #$2D,(a0)
	moveq.l #1,d7
	move.w d7,absolute_slot_00000290.w
	move.l #$5000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FD4C:
	rts
abs_0_0005FD4E:
	cmpi.w #1,absolute_slot_00000290.w
	bne.b abs_0_0005FD68
	addq.w #1,absolute_slot_00000290.w
	lea.l abs_0_00063518(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005FD68:
	rts
abs_0_0005FD6A:
	cmpi.w #46,$0008(a1)
	bne.b abs_0_0005FD7C
	move.w #$2E,(a0)
	moveq.l #1,d7
	move.w d7,absolute_slot_00000292.w
abs_0_0005FD7C:
	rts
abs_0_0005FD7E:
	tst.w absolute_slot_00000292.w
	beq.b abs_0_0005FD96
	clr.w absolute_slot_00000292.w
	lea.l abs_0_000635B8(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
abs_0_0005FD96:
	rts
abs_0_0005FD98:
	cmpi.w #45,$0008(a1)
	bne.b abs_0_0005FDBA
	cmpi.w #40,absolute_slot_000001DE.w
	bne.b abs_0_0005FDBA
	cmpi.w #36,absolute_slot_0000018C.w
	bge.b abs_0_0005FDBA
	moveq.l #1,d7
	move.w d7,absolute_slot_000001B8.w
	move.w #$27,(a0)
abs_0_0005FDBA:
	rts
abs_0_0005FDBC:
	tst.w absolute_slot_000001B8.w
	beq.b abs_0_0005FE20
	cmpi.w #2,absolute_slot_000001B8.w
	bge.b abs_0_0005FDF2
	lea.l abs_0_000636F2(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	moveq.l #-12,d1
	moveq.l #28,d2
	move.w #$60,d3
	move.w #$80,d4
	move.w #$12C,d5
	moveq.l #19,d6
	bsr.w abs_0_0006029C
	addq.w #1,absolute_slot_000001B8.w
abs_0_0005FDF2:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_0005FE22
	addq.w #1,absolute_slot_000001BC.w
	move.w absolute_slot_000001BC.w,d0
	andi.w #8,d0
	bne.b abs_0_0005FE20
	lea.l abs_0_00064B50(pc),a0
	lea.l absolute_slot_000001B0.w,a1
	bsr.w abs_0_0005D8AE
	moveq.l #3,d0
	moveq.l #104,d1
	move.w absolute_slot_000001B0.w,d2
	bsr.w abs_0_0005CC5C
abs_0_0005FE20:
	rts
abs_0_0005FE22:
	cmpi.w #3,absolute_slot_000001B8.w
	beq.b abs_0_0005FE20
	addq.w #1,absolute_slot_000001B8.w
	addq.w #1,absolute_slot_000002EE.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_0005FE3E:
	cmpi.w #47,$0008(a1)
	bne.b abs_0_0005FE66
	cmpi.w #7,absolute_slot_000001DE.w
	bne.b abs_0_0005FE66
	move.w #$9A,d0
	moveq.l #35,d1
	moveq.l #120,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FE66
	moveq.l #1,d7
	move.w d7,absolute_slot_000001B6.w
abs_0_0005FE66:
	rts
abs_0_0005FE68:
	tst.w absolute_slot_000001B6.w
	beq.b abs_0_0005FEC4
	cmpi.w #2,absolute_slot_000001B6.w
	bge.b abs_0_0005FEA2
	lea.l abs_0_00063784(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$96,d1
	move.w #$B8,d2
	move.w #$74,d3
	move.w #$96,d4
	move.w #$12C,d5
	moveq.l #19,d6
	bsr.w abs_0_0006029C
	addq.w #1,absolute_slot_000001B6.w
abs_0_0005FEA2:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_0005FEC6
	addq.w #1,absolute_slot_00000236.w
	move.w absolute_slot_00000236.w,d0
	andi.w #8,d0
	bne.b abs_0_0005FEC4
	move.w #$A0,d0
	moveq.l #124,d1
	moveq.l #75,d2
	bsr.w abs_0_0005CC5C
abs_0_0005FEC4:
	rts
abs_0_0005FEC6:
	cmpi.w #3,absolute_slot_000001B6.w
	beq.b abs_0_0005FEC4
	addq.w #1,absolute_slot_000001B6.w
	addq.w #1,absolute_slot_000002EE.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_0005FEE2:
	cmpi.w #34,$0008(a1)
	bne.b abs_0_0005FF14
	cmpi.w #23,absolute_slot_000001DE.w
	bne.b abs_0_0005FF14
	move.w #$81,d0
	moveq.l #16,d1
	moveq.l #86,d2
	moveq.l #10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FF14
	moveq.l #1,d7
	move.w d7,absolute_slot_0000029E.w
	move.l #$1000,d0
	bsr.w abs_0_0005D46C
abs_0_0005FF14:
	rts
abs_0_0005FF16:
	tst.w absolute_slot_0000029E.w
	beq.b abs_0_0005FF44
	clr.w absolute_slot_0000029E.w
	lea.l abs_0_000637E4(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$1,absolute_slot_0000025A.w
	lea.l absolute_slot_000004D0.w,a0
	move.w #$17,(a0)+
	move.w #$90,(a0)+
	move.w #$54,(a0)
abs_0_0005FF44:
	rts
abs_0_0005FF46:
	cmpi.w #53,$0008(a1)
	bne.b abs_0_0005FF74
	cmpi.w #45,absolute_slot_000001DE.w
	bne.b abs_0_0005FF74
	move.w #$88,d0
	move.w #$20,d1
	move.w #$8C,d2
	move.w #$20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0005FF74
	moveq.l #1,d7
	move.w d7,absolute_slot_00000298.w
abs_0_0005FF74:
	rts
abs_0_0005FF76:
	move.w absolute_slot_00000298.w,d0
	beq.b abs_0_0005FF88
	subq.w #1,d0
	beq.b abs_0_0005FF8A
	subq.w #1,d0
	beq.b abs_0_0005FF9E
	subq.w #1,d0
	beq.b abs_0_0005FFBE
abs_0_0005FF88:
	rts
abs_0_0005FF8A:
	lea.l abs_0_00063A56(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_00000298.w
	rts
abs_0_0005FF9E:
	move.w #$7E,d1
	move.w #$B4,d2
	move.w #$7C,d3
	move.w #$B2,d4
	move.w #$12C,d5
	moveq.l #19,d6
	bsr.w abs_0_0006029C
	addq.w #1,absolute_slot_00000298.w
	rts
abs_0_0005FFBE:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_0005FFE6
	addq.w #1,absolute_slot_0000029A.w
	move.w absolute_slot_0000029A.w,d0
	andi.w #8,d0
	bne.b abs_0_0005FF88
	move.w #$96,d0
	move.w #$9A,d1
	move.w #$F4,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_0005FFE6:
	addq.w #1,absolute_slot_00000298.w
	addq.w #1,absolute_slot_000002EE.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_0005FFFA:
	cmpi.w #42,$0008(a1)
	bne.b abs_0_00060024
	cmpi.w #26,absolute_slot_000001DE.w
	bne.b abs_0_00060024
	move.w #$94,d0
	moveq.l #38,d1
	move.w #$82,d2
	moveq.l #20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_00060024
	moveq.l #1,d7
	move.w d7,absolute_slot_00000296.w
abs_0_00060024:
	rts
abs_0_00060026:
	move.w absolute_slot_00000296.w,d0
	beq.b abs_0_00060034
	subq.w #1,d0
	beq.b abs_0_00060046
	subq.w #1,d0
	beq.b abs_0_00060078
abs_0_00060034:
	rts
abs_0_00060036:
	moveq.l #112,d0
	move.w #$8A,d1
	move.w #$D8,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_00060046:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_00060076
	bsr.b abs_0_00060036
	lea.l abs_0_00063AC6(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	moveq.l #112,d1
	move.w #$B4,d2
	moveq.l #96,d3
	move.w #$96,d4
	move.w #$12C,d5
	moveq.l #23,d6
	bsr.w abs_0_0006029C
	addq.w #1,absolute_slot_00000296.w
abs_0_00060076:
	rts
abs_0_00060078:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_000600A0
	addq.w #1,absolute_slot_00000238.w
	move.w absolute_slot_00000238.w,d0
	andi.w #8,d0
	bne.b abs_0_0006009E
	bsr.b abs_0_00060036
	move.w #$8C,d0
	moveq.l #100,d1
	move.w #$84,d2
	bsr.w abs_0_0005CC5C
abs_0_0006009E:
	rts
abs_0_000600A0:
	addq.w #1,absolute_slot_00000296.w
	addq.w #1,absolute_slot_000002EE.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_000600B4:
	cmpi.w #40,$0008(a1)
	bne.b abs_0_000600EC
	cmpi.w #36,absolute_slot_000001DE.w
	bne.b abs_0_000600EC
	move.w #$9D,d0
	move.w #$14,d1
	move.w #$9F,d2
	move.w #$A,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_000600EC
	moveq.l #1,d7
	move.w d7,absolute_slot_00000218.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
abs_0_000600EC:
	rts
abs_0_000600EE:
	cmpi.w #55,$0008(a1)
	bne.b abs_0_0006010C
	cmpi.w #22,absolute_slot_000001DE.w
	bne.b abs_0_0006010C
	cmpi.w #1,absolute_slot_000002CC.w
	bne.b abs_0_0006010C
	addq.w #1,absolute_slot_000002CC.w
	moveq.l #1,d7
abs_0_0006010C:
	rts
abs_0_0006010E:
	cmpi.w #56,$0008(a1)
	bne.b abs_0_0006012A
	cmpi.w #54,absolute_slot_000001DE.w
	bne.b abs_0_0006012A
	tst.w absolute_slot_000002DC.w
	beq.b abs_0_0006012A
	addq.w #1,absolute_slot_000002DC.w
	moveq.l #1,d7
abs_0_0006012A:
	rts
abs_0_0006012C:
	cmpi.w #37,$0008(a1)
	bne.b abs_0_00060142
	cmpi.w #48,absolute_slot_000001DE.w
	bne.b abs_0_00060142
	moveq.l #1,d7
	move.w d7,absolute_slot_000002C8.w
abs_0_00060142:
	rts
abs_0_00060144:
	move.w absolute_slot_000002C8.w,d0
	beq.b abs_0_00060156
	subq.w #1,d0
	beq.b abs_0_00060158
	subq.w #1,d0
	beq.b abs_0_0006017A
	subq.w #1,d0
	beq.b abs_0_0006019E
abs_0_00060156:
	rts
abs_0_00060158:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_00060156
	lea.l abs_0_00063EB2(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_000002C8.w
	lea.l absolute_slot_0000053E.w,a0
	move.w #$30,(a0)
	rts
abs_0_0006017A:
	move.w #$AA,d1
	move.w #$E0,d2
	move.w #$68,d3
	move.w #$9E,d4
	move.w #$12C,d5
	moveq.l #19,d6
	bsr.w abs_0_0006029C
	clr.w absolute_slot_000002CA.w
	addq.w #1,absolute_slot_000002C8.w
	rts
abs_0_0006019E:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_000601C6
	addq.w #1,absolute_slot_000002CA.w
	move.w absolute_slot_000002CA.w,d0
	andi.w #8,d0
	bne.b abs_0_00060156
	move.w #$B4,d0
	move.w #$70,d1
	move.w absolute_slot_0000026E.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_000601C6:
	addq.w #1,absolute_slot_000002C8.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_000601D6:
	cmpi.w #35,$0008(a1)
	bne.b abs_0_00060204
	cmpi.w #14,absolute_slot_000001DE.w
	bne.b abs_0_00060204
	move.w #$BC,d0
	move.w #$10,d1
	move.w #$7D,d2
	move.w #$10,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_00060204
	moveq.l #1,d7
	move.w d7,absolute_slot_000002A0.w
abs_0_00060204:
	rts
	dc.b $30,$3C,$00,$84,$72,$5C,$34,$3C,$00,$AD,$61,$00,$CA,$4A,$4E,$75
	dc.b $70,$10,$72,$70,$34,$3C,$00,$99,$61,$00,$CA,$3C,$4E,$75
abs_0_00060224:
	move.w absolute_slot_00000232.w,d0
	beq.b abs_0_00060232
	cmp.w #$1,d0
	beq.b abs_0_00060240
	rts
abs_0_00060232:
	moveq.l #32,d0
	moveq.l #112,d1
	move.w #$9A,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_00060240:
	lea.l abs_0_00064B3E(pc),a0
	lea.l absolute_slot_00000234.w,a1
	bsr.w abs_0_0005D8AE
	move.w absolute_slot_00000234.w,d2
	cmp.w #$9D,d2
	beq.b abs_0_00060260
	moveq.l #32,d0
	moveq.l #112,d1
	bsr.w abs_0_0005CC5C
	rts
abs_0_00060260:
	move.w #$2,absolute_slot_00000232.w
	rts
abs_0_00060268:
	lea.l abs_0_0005E17A(pc),a0
	lea.l runtime_code_00000318.w,a1
	lea.l abs_0_000624E4(pc),a2
	moveq.l #2,d7
abs_0_00060276:
	move.w (a0)+,d0
	beq.b abs_0_00060294
	mulu.w #$A,d0
	move.w $6(a1,d0.w),d2
	move.w (a2),d0
	move.w $0002(a2),d1
	movem.l d7/a0-a2,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d7/a0-a2
abs_0_00060294:
	addq.w #4,a2
	dbf.w d7,abs_0_00060276
	rts
abs_0_0006029C:
	move.w d6,absolute_slot_0000022E.w
	move.w d5,absolute_slot_00000230.w
	sub.w d1,d2
	sub.w d3,d4
	lea.l absolute_slot_00000650.w,a0
abs_0_000602AC:
	move.w d2,d0
	bsr.w abs_0_0005C7F6
	move.w d0,d7
	add.w d1,d7
	move.w d7,$0000(a0)
	move.w d4,d0
	bsr.w abs_0_0005C7F6
	move.w d0,d7
	add.w d3,d7
	move.w d7,$0002(a0)
	clr.w $0006(a0)
	clr.w $0008(a0)
	clr.w $0004(a0)
	moveq.l #127,d0
	bsr.w abs_0_0005C7F6
	andi.w #31,d0
	move.w d0,$0006(a0)
	lea.l $000A(a0),a0
	dbf.w d6,abs_0_000602AC
	rts
abs_0_000602EC:
	tst.w absolute_slot_00000230.w
	ble.b abs_0_00060368
	subq.w #1,absolute_slot_00000230.w
	lea.l absolute_slot_00000650.w,a0
	move.w absolute_slot_0000022E.w,d7
abs_0_000602FE:
	tst.w $0006(a0)
	beq.b abs_0_0006030A
	subq.w #1,$0006(a0)
	bra.b abs_0_00060360
abs_0_0006030A:
	subq.w #1,$0008(a0)
	bge.b abs_0_00060342
	move.w #$3,$0008(a0)
	cmpi.w #5,$0004(a0)
	ble.b abs_0_0006033E
	move.w #$FFFF,$0004(a0)
	clr.w $0008(a0)
	moveq.l #15,d0
	bsr.w abs_0_0005C7F6
	cmpi.w #100,absolute_slot_00000230.w
	bge.b abs_0_00060338
	moveq.l #127,d0
abs_0_00060338:
	move.w d0,$0006(a0)
	bra.b abs_0_00060360
abs_0_0006033E:
	addq.w #1,$0004(a0)
abs_0_00060342:
	move.w $0000(a0),d0
	move.w $0002(a0),d1
	move.w $0004(a0),d2
	add.w d2,d2
	move.w abs_0_0006036A(pc,d2.w),d2
	movem.l d7/a0,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d7/a0
abs_0_00060360:
	lea.l $000A(a0),a0
	dbf.w d7,abs_0_000602FE
abs_0_00060368:
	rts
abs_0_0006036A:
	dc.w $00A6,$00A7,$00A8,$00A9,$00A8,$00A7,$00A6	; lookup_table
abs_0_00060378:
	moveq.l #0,d0
	tst.w absolute_slot_00000154.w
	bne.b abs_0_0006038E
	tst.w absolute_slot_0000015C.w
	beq.b abs_0_00060394
	clr.w absolute_slot_0000015C.w
	moveq.l #1,d0
	rts
abs_0_0006038E:
	move.w #$1,absolute_slot_0000015C.w
abs_0_00060394:
	rts
abs_0_00060396:
	move.l a0,-(a7)
abs_0_00060398:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_00060416
	tst.w $001A(a0)
	bne.b abs_0_000603C4
	tst.w $0018(a0)
	beq.b abs_0_000603B2
	subq.w #1,$0018(a0)
	bra.b abs_0_00060410
abs_0_000603B2:
	move.w #$1,$001A(a0)
	move.l $0000(a0),$0012(a0)
	move.l $0004(a0),$000E(a0)
abs_0_000603C4:
	move.l $0008(a0),d0
	move.l $0012(a0),d1
	move.l $000E(a0),d2
	move.l $0004(a0),d3
	add.l d0,d1
	add.l d1,d2
	move.l d1,$0012(a0)
	cmp.l d2,d3
	bge.b abs_0_000603EC
	clr.w $001A(a0)
	move.l d3,d2
	move.w $0016(a0),$0018(a0)
abs_0_000603EC:
	move.l d2,$000E(a0)
	move.w $000C(a0),d0
	move.l $000E(a0),d1
	swap.w d1
	move.w absolute_slot_00000248.w,d2
	tst.l $0012(a0)
	bge.b abs_0_00060408
	move.w absolute_slot_00000246.w,d2
abs_0_00060408:
	move.l a0,-(a7)
	bsr.w abs_0_0005CC5C
	movea.l (a7)+,a0
abs_0_00060410:
	lea.l $001C(a0),a0
	bra.b abs_0_00060398
abs_0_00060416:
	movea.l (a7)+,a0
	bsr.w abs_0_0006043A
	bsr.b abs_0_00060420
	rts
abs_0_00060420:
	lea.l abs_0_00064B78(pc),a0
	lea.l absolute_slot_00000246.w,a1
	bsr.w abs_0_0005D8AE
	lea.l abs_0_00064B88(pc),a0
	lea.l absolute_slot_00000248.w,a1
	bsr.w abs_0_0005D8AE
	rts
abs_0_0006043A:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_00060470
	tst.w $001A(a0)
	beq.b abs_0_0006046A
	move.w $000C(a0),d0
	subi.w #3,d0
	moveq.l #13,d1
	move.l $000E(a0),d2
	swap.w d2
	moveq.l #13,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_0006046A
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
	bra.b abs_0_00060470
abs_0_0006046A:
	lea.l $001C(a0),a0
	bra.b abs_0_0006043A
abs_0_00060470:
	rts
abs_0_00060472:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0006047C
	bsr.w abs_0_00060496
abs_0_0006047C:
	bsr.w abs_0_000604E2
	tst.w absolute_slot_000002E0.w
	beq.b abs_0_00060494
	bsr.w abs_0_000604FC
	tst.w absolute_slot_0000024E.w
	beq.b abs_0_00060494
	bsr.w abs_0_0006058C
abs_0_00060494:
	rts
abs_0_00060496:
	tst.w absolute_slot_000002E0.w
	bne.b abs_0_000604E0
	move.w #$118,d0
	moveq.l #14,d1
	move.w #$8C,d2
	moveq.l #8,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_000604E0
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_000604E0
	lea.l abs_0_0006384A(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$1,absolute_slot_000002E0.w
	move.w #$2,absolute_slot_00000250.w
	clr.w absolute_slot_0000024E.w
	move.l #$2000,d0
	bsr.w abs_0_0005D46C
abs_0_000604E0:
	rts
abs_0_000604E2:
	move.w #$C2,d2
	tst.w absolute_slot_000002E0.w
	beq.b abs_0_000604EE
	addq.w #1,d2
abs_0_000604EE:
	move.w #$118,d0
	move.w #$92,d1
	bsr.w abs_0_0005CC5C
	rts
abs_0_000604FC:
	bsr.w abs_0_00060550
	move.w #$D0,d6
	move.w absolute_slot_0000024E.w,d7
	lsr.w #2,d7
	beq.b abs_0_0006052C
	subq.w #1,d7
abs_0_0006050E:
	movem.l d6-d7,-(a7)
	move.w d6,d0
	move.w #$A0,d1
	move.w #$B7,d2
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d6-d7
	subi.w #16,d6
	dbf.w d7,abs_0_0006050E
abs_0_0006052C:
	move.w absolute_slot_0000024E.w,d7
	andi.w #3,d7
	beq.b abs_0_00060548
	subq.w #1,d7
	add.w d7,d7
	move.w abs_0_0006054A(pc,d7.w),d2
	move.w d6,d0
	move.w #$A0,d1
	bsr.w abs_0_0005CC5C
abs_0_00060548:
	rts
abs_0_0006054A:
	dc.w $00B4,$00B5,$00B6	; lookup_table
abs_0_00060550:
	subq.w #1,absolute_slot_00000250.w
	bge.b abs_0_00060588
	move.w #$2,absolute_slot_00000250.w
	move.w abs_0_0006058A(pc),d0
	add.w d0,$024E.w
	cmpi.w #40,absolute_slot_0000024E.w
	ble.b abs_0_00060578
	move.w #$28,absolute_slot_0000024E.w
	neg.w abs_0_0006058A.l
abs_0_00060578:
	tst.w absolute_slot_0000024E.w
	bge.b abs_0_00060588
	clr.w absolute_slot_0000024E.w
	neg.w abs_0_0006058A.l
abs_0_00060588:
	rts
abs_0_0006058A:
	dc.w $0001	; lookup_table
abs_0_0006058C:
	clr.w absolute_slot_0000024A.w
	move.w absolute_slot_0000024E.w,d0
	lsl.w #2,d0
	move.w d0,d1
	move.w #$D0,d0
	sub.w d1,d0
	addi.w #16,d0
	subq.w #6,d1
	move.w #$A0,d2
	moveq.l #6,d3
	tst.w absolute_slot_000001C2.w
	bmi.b abs_0_000605D4
	bsr.w abs_0_0005F47C
	tst.w d0
	beq.b abs_0_000605D4
	move.w #$A0,absolute_slot_0000018E.w
	move.w absolute_slot_0000018E.w,absolute_slot_000001CA.w
	move.w #$1,absolute_slot_0000024A.w
	bsr.w abs_0_0005D74E
	move.w #$10,absolute_slot_000001C2.w
abs_0_000605D4:
	rts
abs_0_000605D6:
	dc.b $FF,$FC,$00,$00,$00,$96,$00,$00,$00,$00,$1B,$58,$00,$30
	dcb.b $9,$00
	dc.b $28,$00,$14,$00,$00,$FF,$FC,$00,$00,$00,$96,$00,$00,$00,$00,$1F
	dc.b $40,$00,$50
	dcb.b $9,$00
	dc.b $28,$00,$14,$00,$00,$FF,$FC,$00,$00,$00,$96,$00,$00,$00,$00,$1B
	dc.b $58,$00,$E0
	dcb.b $9,$00
	dc.b $28,$00,$0A,$00,$00,$FF,$FC,$00,$00,$00,$96,$00,$00,$00,$00,$1F
	dc.b $40,$01
	dcb.b $A,$00
	dc.b $28,$00,$0A,$00,$00,$44,$45,$4C,$21
abs_0_0006064A:
	dc.b $FF,$FC,$00,$00,$00,$82,$00,$00,$00,$00,$1B,$58,$00,$70
	dcb.b $9,$00
	dc.b $3C,$00,$23,$00,$00,$FF,$FC,$00,$00,$00,$82,$00,$00,$00,$00,$1F
	dc.b $40,$00,$90
	dcb.b $9,$00
	dc.b $32,$00,$14,$00,$00,$FF,$FC,$00,$00,$00,$82,$00,$00,$00,$00,$1B
	dc.b $58,$00,$B0
	dcb.b $9,$00
	dc.b $32,$00,$0A,$00,$00,$FF,$FC,$00,$00,$00,$82,$00,$00,$00,$00,$1F
	dc.b $40,$00,$D0
	dcb.b $9,$00
	dc.b $3C,$00,$00,$00,$00,$44,$45,$4C,$21
abs_0_000606BE:
	lea.l abs_0_0006278E(pc),a1
	moveq.l #22,d0
abs_0_000606C4:
	move.b (a0)+,(a1)+
	dbf.w d0,abs_0_000606C4
	move.w d1,absolute_slot_000002DE.w
	rts
abs_0_000606D0:
	lea.l abs_0_000623E4(pc),a0
	moveq.l #7,d5
	move.w absolute_slot_000002E4.w,d3
	move.w d3,d4
	addi.w #64,d4
	move.w absolute_slot_000002E6.w,d6
	lsr.w #2,d6
abs_0_000606E6:
	addi.w #32,d3
	andi.w #254,d3
	move.w $0(a0,d3.w),d0
	addi.w #218,d0
	addi.w #32,d4
	andi.w #254,d4
	move.w $0(a0,d4.w),d1
	addi.w #102,d1
	movem.l d3-d6/a0,-(a7)
	move.w d6,d2
	addi.w #207,d2
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d3-d6/a0
	addq.w #1,d6
	andi.w #3,d6
	dbf.w d5,abs_0_000606E6
	addq.w #2,absolute_slot_000002E4.w
	addq.w #1,absolute_slot_000002E6.w
	andi.w #15,absolute_slot_000002E6.w
	rts
abs_0_00060732:
	bsr.w abs_0_00060144
	cmpi.w #3,absolute_slot_000002C8.l
	bge.b abs_0_00060760
	lea.l abs_0_00064BBA(pc),a0
	lea.l absolute_slot_0000026E.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$B4,d0
	move.w #$70,d1
	move.w absolute_slot_0000026E.w,d2
	bsr.w abs_0_0005CC5C
	bsr.w abs_0_000620E2
abs_0_00060760:
	rts
abs_0_00060762:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_0006076C
	bsr.w abs_0_0005FF76
abs_0_0006076C:
	cmpi.w #3,absolute_slot_00000298.w
	bge.b abs_0_000607BC
	tst.b absolute_slot_0000022A.w
	bne.b abs_0_000607AC
	move.w #$88,d0
	move.w #$20,d1
	move.w #$8C,d2
	move.w #$20,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_000607AC
	bsr.w abs_0_00060378
	tst.w d0
	beq.b abs_0_000607AC
	lea.l abs_0_00063928(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	st.b absolute_slot_0000022A.w
abs_0_000607AC:
	move.w #$88,d0
	move.w #$83,d1
	move.w #$D7,d2
	bsr.w abs_0_0005CC5C
abs_0_000607BC:
	rts
abs_0_000607BE:
	move.w absolute_slot_00000212.w,d0
	move.w absolute_slot_00000214.w,d1
	move.w #$DB,d2
	bsr.w abs_0_0005CC5C
	lea.l abs_0_00064C32(pc),a0
	lea.l absolute_slot_00000216.w,a1
	bsr.w abs_0_0005D8AE
	move.w absolute_slot_00000212.w,d0
	subq.w #5,d0
	move.w absolute_slot_00000214.w,d1
	addq.w #8,d1
	move.w absolute_slot_00000216.w,d2
	bsr.w abs_0_0005CC5C
	tst.w absolute_slot_00000218.w
	bne.b abs_0_0006080E
	move.w absolute_slot_00000212.w,d0
	addi.w #20,d0
	move.w absolute_slot_0000018C.w,d1
	cmp.w d0,d1
	bgt.b abs_0_0006080E
	move.w d0,absolute_slot_0000018C.w
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
abs_0_0006080E:
	rts
abs_0_00060810:
	move.w absolute_slot_00000218.w,d0
	beq.b abs_0_00060826
	subq.w #1,d0
	beq.b abs_0_00060828
	subq.w #1,d0
	beq.b abs_0_00060842
	subq.w #1,d0
	beq.b abs_0_0006085A
	subq.w #1,d0
	beq.b abs_0_0006086C
abs_0_00060826:
	rts
abs_0_00060828:
	lea.l abs_0_00063B86(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_00000218.w
	move.w #$1,absolute_slot_000002EA.w
	rts
abs_0_00060842:
	not.w absolute_slot_00000270.w
	beq.b abs_0_0006084C
	addq.w #1,absolute_slot_00000212.w
abs_0_0006084C:
	cmpi.w #130,absolute_slot_00000212.w
	bne.b abs_0_00060858
	addq.w #1,absolute_slot_00000218.w
abs_0_00060858:
	rts
abs_0_0006085A:
	addq.w #1,absolute_slot_00000214.w
	cmpi.w #192,absolute_slot_00000214.w
	bne.b abs_0_0006086A
	addq.w #1,absolute_slot_00000218.w
abs_0_0006086A:
	rts
abs_0_0006086C:
	lea.l abs_0_00063BBC(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_00000218.w
	clr.w absolute_slot_000002EA.w
	rts
abs_0_00060884:
	dc.b $00,$AA,$00,$21,$00,$DC,$00,$00,$00,$00,$00,$28,$00,$28
	dcb.b $10,$00
abs_0_000608A2:
	dc.b $00,$A0,$00,$00,$00,$DC,$00,$00,$00,$00,$00,$28,$00,$28
	dcb.b $10,$00
abs_0_000608C0:
	lea.l abs_0_00060884(pc),a5
	lea.l abs_0_00064BDE(pc),a3
	lea.l abs_0_00064BF2(pc),a4
	bsr.w abs_0_000608E4
	rts
abs_0_000608D2:
	lea.l abs_0_000608A2(pc),a5
	lea.l abs_0_00064C08(pc),a3
	lea.l abs_0_00064C1C(pc),a4
	bsr.w abs_0_000608E4
	rts
abs_0_000608E4:
	movea.l a5,a0
	bsr.w abs_0_00060F16
	tst.w $000A(a5)
	beq.b abs_0_0006090A
	subq.w #1,$000A(a5)
	bne.w abs_0_000609AC
	movea.l a3,a0
	tst.w $000E(a5)
	beq.b abs_0_00060902
	movea.l a4,a0
abs_0_00060902:
	move.l a0,$0006(a5)
	bsr.w abs_0_0005D8A2
abs_0_0006090A:
	tst.w $0010(a5)
	bne.b abs_0_0006095A
	move.w #$DF,d0
	move.w #$28,d1
	moveq.l #4,d2
	tst.w $000E(a5)
	beq.b abs_0_0006092A
	move.w #$E2,d0
	move.w #$FFF6,d1
	moveq.l #4,d2
abs_0_0006092A:
	cmp.w $0004(a5),d0
	bne.w abs_0_000609AC
	move.w #$1,$0010(a5)
	moveq.l #0,d0
	move.w (a5),d0
	add.w d1,d0
	swap.w d0
	move.l d0,$0012(a5)
	moveq.l #0,d0
	move.w $0002(a5),d0
	add.w d2,d0
	swap.w d0
	move.l d0,$0016(a5)
	move.l #$FFFE0000,$001A(a5)
abs_0_0006095A:
	move.l #$D800,d0
	tst.w $000E(a5)
	beq.b abs_0_00060968
	neg.l d0
abs_0_00060968:
	add.l d0,$0012(a5)
	addi.l #6000,$001A(a5)
	move.l $0016(a5),d0
	add.l $001A(a5),d0
	move.l d0,$0016(a5)
	swap.w d0
	cmp.w #$C0,d0
	ble.b abs_0_00060998
	clr.w $0010(a5)
	move.w $000C(a5),$000A(a5)
	not.w $000E(a5)
	bra.b abs_0_000609AC
abs_0_00060998:
	move.w $0012(a5),d0
	move.w $0016(a5),d1
	move.w #$E3,d2
	move.l a5,-(a7)
	bsr.w abs_0_0005CC5C
	movea.l (a7)+,a5
abs_0_000609AC:
	bsr.w abs_0_000609B2
	rts
abs_0_000609B2:
	tst.l $0006(a5)
	beq.b abs_0_000609C4
	movea.l $0006(a5),a0
	lea.l $0004(a5),a1
	bsr.w abs_0_0005D8AE
abs_0_000609C4:
	move.w (a5),d0
	move.w $0002(a5),d1
	move.w $0004(a5),d2
	cmp.w #$E2,d2
	bne.b abs_0_000609D8
	subi.w #16,d0
abs_0_000609D8:
	bsr.w abs_0_0005CC5C
	rts
abs_0_000609DE:
	bsr.w abs_0_00060A46
	bsr.w abs_0_00060A2A
	lea.l absolute_slot_00000520.w,a0
	cmpi.w #43,(a0)
	beq.b abs_0_00060A28
	lea.l abs_0_0005E17A(pc),a0
	cmpi.w #52,(a0)+
	beq.b abs_0_00060A28
	cmpi.w #52,(a0)+
	beq.b abs_0_00060A28
	cmpi.w #52,(a0)
	beq.b abs_0_00060A28
	cmpi.w #84,absolute_slot_0000018E.w
	ble.b abs_0_00060A28
	move.w absolute_slot_00000272.w,d0
	addi.w #40,d0
	move.w absolute_slot_0000018C.w,d1
	cmp.w d0,d1
	bge.b abs_0_00060A28
	move.w d0,absolute_slot_0000018C.w
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
abs_0_00060A28:
	rts
abs_0_00060A2A:
	lea.l abs_0_00064C4C(pc),a0
	lea.l absolute_slot_00000274.w,a1
	bsr.w abs_0_0005D8AE
	move.w absolute_slot_00000272.w,d0
	moveq.l #117,d1
	move.w absolute_slot_00000274.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_00060A46:
	lea.l absolute_slot_00000520.w,a0
	cmpi.w #43,(a0)
	beq.b abs_0_00060A66
	lea.l abs_0_0005E17A(pc),a0
	cmpi.w #52,(a0)+
	beq.b abs_0_00060A66
	cmpi.w #52,(a0)+
	beq.b abs_0_00060A66
	cmpi.w #52,(a0)
	bne.b abs_0_00060A74
abs_0_00060A66:
	cmpi.w #30,absolute_slot_00000272.w
	ble.b abs_0_00060A82
	subq.w #1,absolute_slot_00000272.w
	rts
abs_0_00060A74:
	cmpi.w #130,absolute_slot_00000272.w
	bge.b abs_0_00060A80
	addq.w #1,absolute_slot_00000272.w
abs_0_00060A80:
	rts
abs_0_00060A82:
	move.w #$1E,absolute_slot_00000272.w
	rts
abs_0_00060A8A:
	move.w absolute_slot_00000276.w,d0
	beq.b abs_0_00060AB2
	subq.w #1,d0
	beq.b abs_0_00060AB4
	subq.w #1,d0
	beq.b abs_0_00060ACA
	subq.w #1,d0
	beq.b abs_0_00060AF6
	subq.w #1,d0
	beq.b abs_0_00060B0A
	subq.w #1,d0
	beq.w abs_0_00060B76
	subq.w #1,d0
	beq.w abs_0_00060B34
	subq.w #1,d0
	beq.w abs_0_00060B76
abs_0_00060AB2:
	rts
abs_0_00060AB4:
	lea.l abs_0_00063BFC(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.l
	addq.w #1,absolute_slot_00000276.w
	rts
abs_0_00060ACA:
	move.w absolute_slot_0000018C.w,d0
	subi.w #24,d0
	move.w d0,absolute_slot_00000278.w
	move.w absolute_slot_0000018E.w,d0
	subi.w #70,d0
	move.w d0,absolute_slot_0000027A.w
	bsr.w abs_0_00060D04
	clr.w absolute_slot_00000280.w
	addq.w #1,absolute_slot_00000276.w
	move.w #$80,absolute_slot_0000027C.w
	rts
abs_0_00060AF6:
	bsr.w abs_0_00060D04
	subq.w #1,absolute_slot_0000027C.w
	tst.w absolute_slot_0000027C.w
	bne.b abs_0_00060B08
	addq.w #1,absolute_slot_00000276.w
abs_0_00060B08:
	rts
abs_0_00060B0A:
	bsr.w abs_0_00060D04
	lea.l abs_0_00063C34(pc),a0
	cmpi.w #2,absolute_slot_0000027E.w
	ble.b abs_0_00060B22
	bsr.w abs_0_00060C66
	lea.l abs_0_00063CA4(pc),a0
abs_0_00060B22:
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.l
	addq.w #1,absolute_slot_00000276.w
	rts
abs_0_00060B34:
	lea.l absolute_slot_0000050C.l,a0
	move.w absolute_slot_000001DE.w,d0
	cmp.w (a0),d0
	bne.b abs_0_00060B60
	move.w $0002(a0),d0
	addi.w #4,d0
	move.w $0004(a0),d1
	addi.w #4,d1
	bsr.w abs_0_00060C92
	addq.w #1,absolute_slot_00000276.w
	bsr.w abs_0_00060D04
	rts
abs_0_00060B60:
	lea.l abs_0_00063CF0(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.l
	clr.w absolute_slot_00000276.w
	rts
abs_0_00060B76:
	tst.w absolute_slot_00000280.w
	beq.w abs_0_00060C60
	bsr.w abs_0_00060D04
	lea.l abs_0_00060CC4(pc),a0
	moveq.l #7,d7
abs_0_00060B88:
	move.w $0004(a0),d0
	move.w $0006(a0),d1
	cmpi.w #1,absolute_slot_00000280.w
	beq.b abs_0_00060BA0
	sub.w d0,(a0)
	sub.w d1,$0002(a0)
	bra.b abs_0_00060BA6
abs_0_00060BA0:
	add.w d0,(a0)
	add.w d1,$0002(a0)
abs_0_00060BA6:
	move.w (a0),d0
	move.w $0002(a0),d1
	move.w #$EC,d2
	movem.l d7/a0,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d7/a0
	lea.l $0008(a0),a0
	dbf.w d7,abs_0_00060B88
	bsr.w abs_0_00060D3A
	cmpi.w #1,absolute_slot_00000280.w
	beq.w abs_0_00060C2A
	lea.l abs_0_00060CC4(pc),a0
	moveq.l #7,d7
	move.w (a0),d0
	move.w $0002(a0),d1
abs_0_00060BDE:
	cmp.w (a0),d0
	bne.b abs_0_00060C28
	cmp.w $0002(a0),d1
	bne.b abs_0_00060C28
	lea.l $0008(a0),a0
	dbf.w d7,abs_0_00060BDE
	cmpi.w #10,absolute_slot_000001DE.w
	bne.b abs_0_00060C24
	lea.l absolute_slot_0000050C.l,a0
	move.w $0002(a0),d0
	move.w $0004(a0),d1
	cmp.w #$64,d1
	ble.b abs_0_00060C24
	cmp.w #$84,d0
	ble.b abs_0_00060C24
	cmp.w #$C0,d0
	bge.b abs_0_00060C24
	tst.w absolute_slot_000002EC.w
	bne.b abs_0_00060C24
	move.w #$1,absolute_slot_00000282.w
abs_0_00060C24:
	clr.w absolute_slot_00000276.w
abs_0_00060C28:
	rts
abs_0_00060C2A:
	lea.l abs_0_00060CC4(pc),a0
	moveq.l #7,d7
	moveq.l #0,d1
abs_0_00060C32:
	move.w (a0),d0
	bmi.b abs_0_00060C5C
	cmp.w #$140,d0
	bge.b abs_0_00060C5C
	move.w $0002(a0),d0
	bmi.b abs_0_00060C5C
	cmp.w #$C0,d0
	bge.b abs_0_00060C5C
abs_0_00060C48:
	lea.l $0008(a0),a0
	dbf.w d7,abs_0_00060C32
	cmp.w #$8,d1
	bne.b abs_0_00060C5A
	addq.w #1,absolute_slot_00000276.w
abs_0_00060C5A:
	rts
abs_0_00060C5C:
	addq.w #1,d1
	bra.b abs_0_00060C48
abs_0_00060C60:
	clr.w absolute_slot_00000276.w
	rts
abs_0_00060C66:
	move.w #$1,absolute_slot_00000280.w
	lea.l abs_0_00060CC4(pc),a0
	moveq.l #7,d7
	move.w absolute_slot_00000278.w,d0
	addi.w #20,d0
	move.w absolute_slot_0000027A.w,d1
	addi.w #28,d1
abs_0_00060C82:
	move.w d0,(a0)
	move.w d1,$0002(a0)
	lea.l $0008(a0),a0
	dbf.w d7,abs_0_00060C82
	rts
abs_0_00060C92:
	move.w #$2,absolute_slot_00000280.w
	lea.l abs_0_00060CC4(pc),a0
	moveq.l #7,d7
abs_0_00060C9E:
	move.w d0,(a0)
	move.w d1,$0002(a0)
	move.w $0004(a0),d2
	muls.w #$64,d2
	add.w d2,(a0)
	move.w $0006(a0),d2
	muls.w #$64,d2
	add.w d2,$0002(a0)
	lea.l $0008(a0),a0
	dbf.w d7,abs_0_00060C9E
	rts
abs_0_00060CC4:
	dc.b $00,$00,$00,$00,$00,$00,$FF,$FE,$00,$00,$00,$00,$00,$02,$FF,$FE
	dc.b $00,$00,$00,$00,$00,$02,$00,$00,$00,$00,$00,$00,$00,$02,$00,$02
	dc.b $00,$00,$00,$00,$00,$00,$00,$02,$00,$00,$00,$00,$FF,$FE,$00,$02
	dc.b $00,$00,$00,$00,$FF,$FE,$00,$00,$00,$00,$00,$00,$FF,$FE,$FF,$FE
abs_0_00060D04:
	lea.l abs_0_000623A4(pc),a0
	move.w absolute_slot_00000286.w,d0
	andi.w #62,d0
	move.w $0(a0,d0.w),d0
	move.w absolute_slot_00000288.w,d1
	andi.w #62,d1
	move.w $0(a0,d1.w),d1
	add.w absolute_slot_00000278.w,d0
	add.w absolute_slot_0000027A.w,d1
	move.w #$EB,d2
	bsr.w abs_0_0005CC5C
	addq.w #1,absolute_slot_00000286.w
	addq.w #2,absolute_slot_00000288.w
	rts
abs_0_00060D3A:
	lea.l abs_0_00060CC4(pc),a0
	moveq.l #7,d7
abs_0_00060D40:
	move.w (a0),d0
	moveq.l #6,d1
	move.w $0002(a0),d2
	moveq.l #4,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_00060D5A
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
	rts
abs_0_00060D5A:
	lea.l $0008(a0),a0
	dbf.w d7,abs_0_00060D40
	rts
abs_0_00060D64:
	move.w absolute_slot_00000282.w,d0
	beq.b abs_0_00060D76
	subq.w #1,d0
	beq.b abs_0_00060D78
	subq.w #1,d0
	beq.b abs_0_00060D8C
	subq.w #1,d0
	beq.b abs_0_00060DAE
abs_0_00060D76:
	rts
abs_0_00060D78:
	lea.l abs_0_00063D58(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_00000282.w
	rts
abs_0_00060D8C:
	move.w #$8C,d1
	move.w #$AA,d2
	move.w #$64,d3
	move.w #$82,d4
	move.w #$12C,d5
	moveq.l #19,d6
	bsr.w abs_0_0006029C
	clr.w absolute_slot_00000284.w
	addq.w #1,absolute_slot_00000282.w
abs_0_00060DAE:
	cmpi.w #80,absolute_slot_00000230.w
	ble.b abs_0_00060DCA
	addq.w #1,absolute_slot_00000284.w
	move.w absolute_slot_00000284.w,d0
	andi.w #8,d0
	bne.b abs_0_00060DC8
	bsr.w abs_0_0005F2D4
abs_0_00060DC8:
	rts
abs_0_00060DCA:
	addq.w #1,absolute_slot_00000282.w
	move.w #$1,absolute_slot_000002EC.w
	addq.w #1,absolute_slot_000002EE.w
	move.l #$10000,d0
	bsr.w abs_0_0005D46C
	rts
abs_0_00060DE4:
	cmpi.w #6,absolute_slot_000002EE.l
	bne.b abs_0_00060E16
	moveq.l #1,d1
	lea.l abs_0_00062B26(pc),a0
	bsr.w abs_0_000606BE
	addq.w #1,absolute_slot_000002EE.l
	lea.l abs_0_00063DD4(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.l #$100000,d0
	bsr.w abs_0_0005D46C
abs_0_00060E16:
	rts
abs_0_00060E18:
	bsr.w abs_0_00060EDE
	lea.l abs_0_00060F3C(pc),a0
abs_0_00060E20:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_00060E56
	tst.w $0008(a0)
	beq.b abs_0_00060E34
	subq.w #1,$0008(a0)
	bra.b abs_0_00060E38
abs_0_00060E34:
	bsr.w abs_0_00060E58
abs_0_00060E38:
	bsr.w abs_0_00060E9E
	move.w $0000(a0),d0
	move.w $0002(a0),d1
	move.w $0004(a0),d2
	move.l a0,-(a7)
	bsr.w abs_0_0005CC5C
	movea.l (a7)+,a0
	lea.l $0016(a0),a0
	bra.b abs_0_00060E20
abs_0_00060E56:
	rts
abs_0_00060E58:
	subq.w #1,$000A(a0)
	bge.b abs_0_00060E9C
	move.w #$3,$000A(a0)
	addq.w #1,$0004(a0)
	cmpi.w #201,$0004(a0)
	ble.b abs_0_00060E9C
	move.w #$C4,$0004(a0)
	move.w $0000(a0),d0
	addq.w #4,d0
	move.w d0,$000C(a0)
	moveq.l #0,d0
	move.w $0002(a0),d0
	addq.w #5,d0
	swap.w d0
	move.l d0,$000E(a0)
	move.l #$6000,$0012(a0)
	move.w $0006(a0),$0008(a0)
abs_0_00060E9C:
	rts
abs_0_00060E9E:
	addi.l #8192,$0012(a0)
	move.l $0012(a0),d0
	add.l d0,$000E(a0)
	move.l $000E(a0),d1
	swap.w d1
	cmp.w #$87,d1
	ble.b abs_0_00060EC4
	clr.w $000C(a0)
	clr.w $000E(a0)
	rts
abs_0_00060EC4:
	move.w $000C(a0),d0
	beq.b abs_0_00060EDC
	move.l $000E(a0),d1
	swap.w d1
	move.w #$CA,d2
	move.l a0,-(a7)
	bsr.w abs_0_0005CC5C
	movea.l (a7)+,a0
abs_0_00060EDC:
	rts
abs_0_00060EDE:
	lea.l abs_0_00060F3C(pc),a0
abs_0_00060EE2:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_00060F14
	move.w $000C(a0),d0
	beq.b abs_0_00060F0E
	subi.w #3,d0
	moveq.l #6,d1
	move.l $000E(a0),d2
	swap.w d2
	moveq.l #13,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_00060F0E
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
	bra.b abs_0_00060F14
abs_0_00060F0E:
	lea.l $0016(a0),a0
	bra.b abs_0_00060EE2
abs_0_00060F14:
	rts
abs_0_00060F16:
	tst.w $0010(a0)
	beq.b abs_0_00060F3A
	move.l $0012(a0),d0
	swap.w d0
	moveq.l #6,d1
	move.l $0016(a0),d2
	swap.w d2
	moveq.l #4,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_00060F3A
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
abs_0_00060F3A:
	rts
abs_0_00060F3C:
	dc.b $00,$CA,$00,$20,$00,$C4,$00,$50,$00,$14
	dcb.b $D,$00
	dc.b $BA,$00,$20,$00,$C4,$00,$50,$00,$28
	dcb.b $D,$00
	dc.b $AA,$00,$20,$00,$C4,$00,$50,$00,$3C
	dcb.b $D,$00
	dc.b $9A,$00,$20,$00,$C4,$00,$50,$00,$50
	dcb.b $C,$00
	dc.b $44,$45,$4C,$21
abs_0_00060F98:
	move.l absolute_slot_000002A4.w,d0
	swap.w d0
	move.l absolute_slot_000002A8.w,d1
	swap.w d1
	move.w absolute_slot_000002B0.w,d2
	bsr.w abs_0_0005CC5C
	movea.l absolute_slot_000002B2.w,a0
	cmpa.l #$0,a0
	beq.b abs_0_00060FC0
	lea.l absolute_slot_000002B0.w,a1
	bsr.w abs_0_0005D8AE
abs_0_00060FC0:
	move.w absolute_slot_000002A0.w,d0
	beq.b abs_0_00060FD4
	subq.w #1,d0
	beq.b abs_0_00060FD6
	subq.w #1,d0
	beq.b abs_0_00061004
	subq.w #1,d0
	beq.w abs_0_00061058
abs_0_00060FD4:
	rts
abs_0_00060FD6:
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_00060FD4
	lea.l abs_0_000640F0(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_000002A0.w
	move.l #$FFFA0000,absolute_slot_000002AC.w
	lea.l abs_0_00064C5A(pc),a0
	move.l a0,absolute_slot_000002B2.w
	bsr.w abs_0_0005D8A2
	rts
abs_0_00061004:
	subi.l #139264,absolute_slot_000002A4.w
	addi.l #14592,absolute_slot_000002AC.w
	move.l absolute_slot_000002A8.w,d0
	add.l absolute_slot_000002AC.w,d0
	move.l d0,absolute_slot_000002A8.w
	move.l absolute_slot_000002A4.w,d0
	swap.w d0
	cmp.w #$54,d0
	bge.b abs_0_00061056
	lea.l abs_0_0006413A(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_000002A0.w
	move.l #$300000,absolute_slot_000002B6.w
	move.l #$440000,absolute_slot_000002BA.w
	move.l #$FFFB0000,absolute_slot_000002BE.w
abs_0_00061056:
	rts
abs_0_00061058:
	tst.w absolute_slot_000002A2.w
	bne.b abs_0_00061098
	subi.l #139264,absolute_slot_000002A4.w
	addi.l #14592,absolute_slot_000002AC.w
	move.l absolute_slot_000002A8.w,d0
	add.l absolute_slot_000002AC.w,d0
	move.l absolute_slot_000002AC.w,d1
	tst.l d1
	bmi.b abs_0_00061094
	move.l d0,d1
	swap.w d1
	cmp.w #$58,d1
	ble.b abs_0_00061094
	move.l #$580000,d0
	move.w #$1,absolute_slot_000002A2.w
abs_0_00061094:
	move.l d0,absolute_slot_000002A8.w
abs_0_00061098:
	subi.l #147456,absolute_slot_000002B6.w
	addi.l #14336,absolute_slot_000002BE.w
	move.l absolute_slot_000002BA.w,d0
	add.l absolute_slot_000002BE.w,d0
	move.l d0,absolute_slot_000002BA.w
	move.l absolute_slot_000002B6.w,d0
	swap.w d0
	move.l absolute_slot_000002BA.w,d1
	swap.w d1
	move.w absolute_slot_000001D8.w,d2
	bsr.w abs_0_0005CC5C
	move.l absolute_slot_000002B6.w,d0
	swap.w d0
	cmp.w #$FFC0,d0
	bge.b abs_0_000610D8
	addq.w #1,absolute_slot_000002A0.w
abs_0_000610D8:
	rts
abs_0_000610DA:
	tst.w absolute_slot_00000172.w
	bgt.b abs_0_00061148
	moveq.l #-1,d0
	bsr.w abs_0_0005D48A
	moveq.l #63,d0
	bsr.w abs_0_0005FA82
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_000610F6:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_000610F6
	tst.w absolute_slot_00000170.w
	bge.b abs_0_0006110A
	move.w #$1,absolute_slot_000002F6.w
	rts
abs_0_0006110A:
	bsr.w abs_0_0005C950
	lea.l abs_0_0006416A(pc),a0
	bsr.w abs_0_0005DE5E
	bsr.w abs_0_0005C41C
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	clr.w absolute_slot_000001E4.w
abs_0_00061128:
	cmpi.w #100,absolute_slot_000001E4.w
	bne.b abs_0_00061128
	clr.w absolute_slot_000001E4.w
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_0006113E:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_0006113E
	bsr.w abs_0_0005F728
abs_0_00061148:
	rts
abs_0_0006114A:
	lea.l abs_0_000611FE(pc),a0
	bsr.w abs_0_000611D4
	lea.l abs_0_000611FE(pc),a0
abs_0_00061156:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_000611BA
	move.w $0004(a0),d0
	add.w d0,(a0)
	cmpi.w #4,(a0)
	bge.b abs_0_0006116E
	neg.w $0004(a0)
abs_0_0006116E:
	cmpi.w #300,(a0)
	ble.b abs_0_00061178
	neg.w $0004(a0)
abs_0_00061178:
	move.w $0006(a0),d0
	add.w d0,$0002(a0)
	cmpi.w #4,$0002(a0)
	bge.b abs_0_0006118C
	neg.w $0006(a0)
abs_0_0006118C:
	cmpi.w #128,$0002(a0)
	ble.b abs_0_00061198
	neg.w $0006(a0)
abs_0_00061198:
	move.w (a0),d0
	move.w $0002(a0),d1
	move.w absolute_slot_000002C4.w,d2
	tst.w $0004(a0)
	bmi.b abs_0_000611AC
	move.w absolute_slot_000002C6.w,d2
abs_0_000611AC:
	move.l a0,-(a7)
	bsr.w abs_0_0005CC5C
	movea.l (a7)+,a0
	lea.l $0008(a0),a0
	bra.b abs_0_00061156
abs_0_000611BA:
	lea.l abs_0_00064C7C(pc),a0
	lea.l absolute_slot_000002C4.w,a1
	bsr.w abs_0_0005D8AE
	lea.l abs_0_00064C8C(pc),a0
	lea.l absolute_slot_000002C6.w,a1
	bsr.w abs_0_0005D8AE
	rts
abs_0_000611D4:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_000611FC
	move.w (a0),d0
	moveq.l #8,d1
	move.w $0002(a0),d2
	moveq.l #6,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_000611F6
	moveq.l #-1,d0
	bsr.w abs_0_0005FA82
	rts
abs_0_000611F6:
	lea.l $0008(a0),a0
	bra.b abs_0_000611D4
abs_0_000611FC:
	rts
abs_0_000611FE:
	dc.b $00,$64,$00,$64,$00,$01,$00,$01,$00,$C8,$00,$14,$FF,$FF,$FF,$FF
	dc.b $44,$45,$4C,$21
abs_0_00061212:
	clr.w absolute_slot_0000024A.w
	lea.l abs_0_0006129C(pc),a0
	cmpi.w #150,absolute_slot_0000020E.w
	beq.b abs_0_00061226
	lea.l abs_0_000612F6(pc),a0
abs_0_00061226:
	move.w #$C8,d6
	move.w #$C8,d7
	move.w absolute_slot_0000020C.w,d2
	addq.w #2,d2
	move.w d2,d3
	addi.w #26,d3
	move.w absolute_slot_0000018C.w,d0
	move.w d0,d1
	addi.w #6,d0
	addi.w #16,d1
	cmp.w d3,d0
	bge.b abs_0_0006129A
	cmp.w d1,d2
	bge.b abs_0_0006129A
	sub.w d2,d0
	bmi.b abs_0_0006125E
	add.w d0,d0
	move.w $0(a0,d0.w),d6
	addi.w #144,d6
abs_0_0006125E:
	sub.w d2,d1
	bmi.b abs_0_0006126C
	add.w d1,d1
	move.w $0(a0,d1.w),d7
	addi.w #144,d7
abs_0_0006126C:
	cmp.w d6,d7
	bgt.b abs_0_00061272
	move.w d7,d6
abs_0_00061272:
	tst.w absolute_slot_000001C2.w
	bmi.b abs_0_0006129A
	move.w absolute_slot_0000018E.w,d0
	sub.w d6,d0
	bmi.b abs_0_0006129A
	cmp.w #$6,d0
	bge.b abs_0_0006129A
	move.w d6,absolute_slot_0000018E.w
	move.w d6,absolute_slot_000001CA.w
	move.w #$1,absolute_slot_0000024A.l
	bsr.w abs_0_0005D74E
abs_0_0006129A:
	rts
abs_0_0006129C:
	dcb.b $B,$00
	dc.b $01,$00,$01,$00,$01,$00,$01,$00,$02,$00,$02,$00,$03,$00,$03,$00
	dc.b $04,$00,$04,$00,$05,$00,$06,$00,$07,$00,$08,$00,$09,$00,$0A,$00
	dc.b $0B,$00,$0C,$00,$0E,$00,$10,$00,$13,$00,$14,$00,$14,$00,$14,$00
	dc.b $14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00
	dc.b $14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14
abs_0_000612F6:
	dc.b $00,$14,$00,$13,$00,$10,$00,$0E,$00,$0C,$00,$0B,$00,$0A,$00,$09
	dc.b $00,$08,$00,$07,$00,$06,$00,$05,$00,$04,$00,$04,$00,$03,$00,$03
	dc.b $00,$02,$00,$02,$00,$01,$00,$01,$00,$01,$00,$01
	dcb.b $9,$00
	dc.b $14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00
	dc.b $14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00,$14,$00
	dc.b $14,$00,$14,$00,$14
abs_0_00061350:
	lea.l absolute_slot_00000144.w,a0
	lea.l runtime_code_00000318.w,a1
abs_0_00061358:
	clr.b (a0)+
	cmpa.l a1,a0
	bne.b abs_0_00061358
	lea.l abs_0_00062B0F(pc),a0
	moveq.l #0,d1
	bsr.w abs_0_000606BE
	move.w #$4A,absolute_slot_00000212.w
	move.w #$81,absolute_slot_00000214.w
	move.w #$1E,absolute_slot_00000272.w
	move.l #$B40000,absolute_slot_000002A4.w
	move.l #$660000,absolute_slot_000002A8.w
	move.w #$EE,absolute_slot_000002B0.w
	clr.l absolute_slot_000002B2.w
	lea.l abs_0_0005E17A(pc),a0
	clr.w (a0)+
	clr.w (a0)+
	clr.w (a0)
	move.w #$40,absolute_slot_000002D0.w
	bsr.w abs_0_00061DD0
	rts
abs_0_000613AA:
	bsr.b abs_0_00061350
	bsr.w abs_0_0005D258
	bsr.w abs_0_0005DBD2
	bsr.w abs_0_0005E4E2
	bsr.w abs_0_0005D122
	move.w #$35,absolute_slot_000001DE.w
	bsr.w abs_0_0005C992
	bsr.w abs_0_0005CEDE
	move.w #$84,absolute_slot_0000018C.w
	move.w #$38,absolute_slot_0000018E.w
	move.w #$0,absolute_slot_000001CC.w
	move.w #$C8,absolute_slot_000001CA.w
	clr.b m68k_vector_trap_4_instruction_vector.w
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.l
	clr.w absolute_slot_000002C2.w
	move.w #$1,absolute_slot_000002CE.w
	lea.l abs_0_00065A1E(pc),a0
	move.l a0,absolute_slot_000002F0.w
abs_0_00061404:
	lea.l _custom.l,a6
abs_0_0006140A:
	tst.w absolute_slot_000001E4.w
	beq.b abs_0_0006140A
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_0006142C
	cmpi.b #64,m68k_vector_trap_4_instruction_vector.w
	beq.w abs_0_00061500
	btst.b #CIAB_GAMEPORT1,_ciaa+ciapra.l
	beq.w abs_0_00061500
abs_0_0006142C:
	bsr.w abs_0_00061772
	tst.w absolute_slot_0000014C.w
	bne.b abs_0_00061404
	clr.w absolute_slot_00000252.w
	clr.w absolute_slot_00000254.w
	bsr.w abs_0_00061660
	tst.w absolute_slot_00000162.w
	bne.w abs_0_0005E180
	tst.l absolute_slot_0000016A.w
	bne.w abs_0_0005E498
	bsr.w abs_0_0005F912
	bsr.w abs_0_0005D27E
	bsr.w abs_0_0005D2AA
	bsr.w abs_0_0005D2DA
	bsr.w abs_0_0005D360
	bsr.w abs_0_0005CEFA
	bsr.w abs_0_0005CF82
	bsr.w abs_0_0005D162
	bsr.w abs_0_0005F59A
	tst.w absolute_slot_000001C8.w
	bne.b abs_0_000614AE
	tst.w absolute_slot_000002EA.w
	bne.b abs_0_00061492
	cmpi.w #40,absolute_slot_00000230.w
	bge.b abs_0_00061492
	bsr.w abs_0_0005D56C
	bsr.w abs_0_0005D50E
abs_0_00061492:
	bsr.w abs_0_0005D4F0
	bsr.w abs_0_0005D5DC
	bsr.w abs_0_0005D74E
	bsr.w abs_0_0005D808
	bsr.w abs_0_0005D5DC
	bsr.w abs_0_0005F436
	bsr.w abs_0_0005D74E
abs_0_000614AE:
	movea.l absolute_slot_00000192.w,a0
	lea.l absolute_slot_00000190.w,a1
	bsr.w abs_0_0005D8AE
	lea.l abs_0_000624F0(pc),a0
	move.w absolute_slot_000001DE.w,d0
	add.w d0,d0
	add.w d0,d0
	movea.l $0(a0,d0.w),a0
	cmpa.l #$0,a0
	beq.b abs_0_000614D4
	jsr (a0)
abs_0_000614D4:
	bsr.w abs_0_0005E562
	bsr.w abs_0_0005D4DA
	bsr.w abs_0_0005F562
	bsr.w abs_0_0005F654
	bsr.w abs_0_0005E002
	bsr.w abs_0_000610DA
	bsr.w abs_0_0005E480
	bsr.w abs_0_0005D8E4
	bsr.w abs_0_0005C41C
	clr.w absolute_slot_000001E4.w
	bra.w abs_0_00061404
abs_0_00061500:
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_0006150A:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_0006150A
	clr.w absolute_slot_000002CE.w
	rts
abs_0_00061516:
	lea.l abs_0_00064C9C(pc),a0
	lea.l absolute_slot_000001B4.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$A2,d0
	move.w #$22,d1
	move.w absolute_slot_000001B4.w,d2
	bsr.w abs_0_0005CC5C
	lea.l abs_0_00064CAA(pc),a0
	lea.l absolute_slot_000001B2.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$11C,d0
	move.w #$22,d1
	move.w absolute_slot_000001B2.w,d2
	bsr.w abs_0_0005CC5C
	lea.l abs_0_00064B5E(pc),a0
	lea.l absolute_slot_0000026A.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$E0,d0
	move.w #$32,d1
	move.w absolute_slot_0000026A.w,d2
	bsr.w abs_0_0005CC5C
	lea.l abs_0_00064CB8(pc),a0
	lea.l absolute_slot_0000023C.w,a1
	bsr.w abs_0_0005D8AE
	moveq.l #60,d0
	moveq.l #3,d1
	move.w absolute_slot_0000023C.w,d2
	bsr.w abs_0_0005CC5C
	move.w #$68,d0
	move.w #$50,d1
	move.w #$F7,d2
	bsr.w abs_0_0005CC5C
	bsr.w abs_0_00061598
	rts
abs_0_00061598:
	lea.l abs_0_00062364(pc),a0
	lea.l abs_0_000615CE(pc),a1
	move.w absolute_slot_000002E8.w,d3
	moveq.l #4,d4
abs_0_000615A6:
	addq.w #6,d3
	andi.w #62,d3
	move.w $0(a0,d3.w),d1
	addi.w #100,d1
	move.w (a1)+,d0
	move.w (a1)+,d2
	movem.l d3-d4/a0-a1,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d3-d4/a0-a1
	dbf.w d4,abs_0_000615A6
	addq.w #2,absolute_slot_000002E8.w
	rts
abs_0_000615CE:
	dc.w $007E,$00FB,$008E,$0100,$0098,$0111,$00A6,$0111	; lookup_table
	dc.w $00B4,$0110	; lookup_table
abs_0_000615E2:
	lea.l abs_0_0006496A(pc),a0
	lea.l absolute_slot_000002D2.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$90,d0
	move.w absolute_slot_000002D0.w,d1
	move.w absolute_slot_000002D2.w,d2
	bsr.w abs_0_0005CC5C
	tst.w absolute_slot_000002DC.w
	bne.b abs_0_0006163C
	cmpi.w #136,absolute_slot_0000018C.w
	ble.b abs_0_0006163C
	move.w #$88,absolute_slot_0000018C.w
	lea.l abs_0_000641AA(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$1,absolute_slot_0000016E.w
	move.w #$1,absolute_slot_000002DC.w
abs_0_00061626:
	cmpi.w #3,absolute_slot_000002DC.w
	bne.b abs_0_0006163A
	cmpi.w #65488,absolute_slot_000002D0.w
	beq.b abs_0_0006163A
	subq.w #1,absolute_slot_000002D0.w
abs_0_0006163A:
	rts
abs_0_0006163C:
	cmpi.w #2,absolute_slot_000002DC.w
	bne.b abs_0_00061626
	tst.w absolute_slot_0000023A.w
	bne.b abs_0_00061626
	lea.l abs_0_000641E4(pc),a0
	move.l a0,absolute_slot_0000016A.w
	move.w #$2,absolute_slot_0000016E.w
	addq.w #1,absolute_slot_000002DC.w
	rts
abs_0_0006165E:
	rts
abs_0_00061660:
	movea.l absolute_slot_000002F0.w,a0
abs_0_00061664:
	move.b (a0)+,d0
	cmp.b #$FF,d0
	bne.b abs_0_000616A0
	clr.w absolute_slot_000002DC.w
	move.w #$40,absolute_slot_000002D0.w
	lea.l absolute_slot_00000548.w,a0
	move.w #$35,(a0)+
	move.w #$2,(a0)+
	move.w #$70,(a0)+
	move.w #$76,(a0)+
	move.w #$1,absolute_slot_0000014C.w
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	lea.l abs_0_00065A1E(pc),a0
	bra.b abs_0_00061664
abs_0_000616A0:
	move.l a0,absolute_slot_000002F0.w
	clr.l absolute_slot_00000150.w
	clr.w absolute_slot_00000154.w
	btst #0,d0
	beq.b abs_0_000616B6
	st.b absolute_slot_00000150.w
abs_0_000616B6:
	btst #1,d0
	beq.b abs_0_000616C0
	st.b absolute_slot_00000151.w
abs_0_000616C0:
	btst #2,d0
	beq.b abs_0_000616CA
	st.b absolute_slot_00000152.w
abs_0_000616CA:
	btst #3,d0
	beq.b abs_0_000616D4
	st.b absolute_slot_00000153.w
abs_0_000616D4:
	btst #4,d0
	beq.b abs_0_000616E0
	move.w #$1,absolute_slot_00000154.w
abs_0_000616E0:
	rts
abs_0_000616E2:
	lea.l abs_0_0006223B(pc),a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	lea.l absolute_slot_00006F50.l,a0
	lea.l absolute_slot_00004750.l,a1
	lea.l $0800(a1),a2
	bsr.w abs_0_00061724
	suba.l #$4750,a2
	lea.l absolute_slot_0000AF50.l,a0
	lea.l absolute_slot_00006150.l,a1
	lea.l $0800(a1),a2
	bsr.w abs_0_00061724
	suba.l #$6150,a2
	rts
abs_0_00061724:
	move.w #$3FF,d7
	moveq.l #0,d6
abs_0_0006172A:
	cmpi.l #$FFFFFFFF,(a0)
	bne.b abs_0_0006175E
	cmpi.l #$FFFFFFFF,$0004(a0)
	bne.b abs_0_0006175E
	cmpi.l #$FFFFFFFF,$0008(a0)
	bne.b abs_0_0006175E
	cmpi.l #$FFFFFFFF,$000C(a0)
	bne.b abs_0_0006175E
	move.w #$FFFF,(a1)+
abs_0_00061754:
	lea.l $0010(a0),a0
	dbf.w d7,abs_0_0006172A
	rts
abs_0_0006175E:
	move.l (a0),(a2)+
	move.l $0004(a0),(a2)+
	move.l $0008(a0),(a2)+
	move.l $000C(a0),(a2)+
	move.w d6,(a1)+
	addq.w #1,d6
	bra.b abs_0_00061754
abs_0_00061772:
	move.w absolute_slot_0000014C.w,d0
	beq.b abs_0_00061794
	subq.w #1,d0
	beq.b abs_0_00061796
	subq.w #1,d0
	beq.w abs_0_00061856
	subq.w #1,d0
	beq.w abs_0_00061932
	subq.w #1,d0
	beq.w abs_0_0006193E
	subq.w #1,d0
	beq.w abs_0_000619B4
abs_0_00061794:
	rts
abs_0_00061796:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_000617BE
	clr.w absolute_slot_00000146.w
	clr.w absolute_slot_0000014A.w
	bsr.w abs_0_000617C0
	bsr.w abs_0_000617E2
	bsr.w abs_0_00061808
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	addq.w #1,absolute_slot_0000014C.w
abs_0_000617BE:
	rts
abs_0_000617C0:
	moveq.l #0,d1
abs_0_000617C2:
	moveq.l #0,d0
abs_0_000617C4:
	moveq.l #32,d2
	bsr.w abs_0_0005DFCA
	addq.w #1,d0
	cmp.w #$28,d0
	bne.b abs_0_000617C4
	addi.w #1344,d1
	cmp.w #$7E00,d1
	bne.b abs_0_000617C2
	bsr.w abs_0_0005CAE0
	rts
abs_0_000617E2:
	lea.l abs_0_00064398(pc),a4
abs_0_000617E6:
	move.l a4,d2
	btst #0,d2
	beq.b abs_0_000617F0
	addq.w #1,a4
abs_0_000617F0:
	move.w (a4)+,d0
	move.w (a4)+,d1
abs_0_000617F4:
	moveq.l #0,d2
	move.b (a4)+,d2
	bmi.b abs_0_00061806
	tst.b d2
	beq.b abs_0_000617E6
	bsr.w abs_0_0005DFCA
	addq.w #1,d0
	bra.b abs_0_000617F4
abs_0_00061806:
	rts
abs_0_00061808:
	movea.l absolute_slot_0000012A.w,a0
	lea.l absolute_slot_000680AA.l,a1
	bsr.b abs_0_00061820
	movea.l absolute_slot_0000012A.w,a0
	movea.l absolute_slot_00000126.w,a1
	bsr.b abs_0_00061820
	rts
abs_0_00061820:
	moveq.l #-1,d0
	move.l d0,$0044(a6)
	clr.w $0064(a6)
	move.l #$9F00000,$0040(a6)
	clr.w $0066(a6)
	suba.w #$A8,a1
	move.l a1,$0054(a6)
	suba.w #$A8,a0
	move.l a0,$0050(a6)
	move.w #$612A,$0058(a6)
abs_0_0006184C:
	btst.b #6,$0002(a6)
	bne.b abs_0_0006184C
	rts
abs_0_00061856:
	bsr.w abs_0_0005CEFA
	bsr.w abs_0_00061C70
	lea.l abs_0_00064216(pc),a0
	bsr.w abs_0_00061870
	bsr.w abs_0_0005C41C
	clr.w absolute_slot_000001E4.w
	rts
abs_0_00061870:
	lea.l abs_0_00062364(pc),a1
	adda.w absolute_slot_0000014A.w,a0
	move.w absolute_slot_00000146.w,d0
	move.w absolute_slot_00000144.w,d6
abs_0_00061880:
	addq.w #2,d6
	andi.w #62,d6
	move.w $0(a1,d6.w),d4
	addi.w #120,d4
	tst.b (a0)
	bmi.b abs_0_000618D0
	bsr.w abs_0_000618E0
	move.w d7,d5
	neg.w d5
	cmp.w d0,d5
	blt.b abs_0_000618A6
	add.w d7,$0146.w
	addq.w #1,absolute_slot_0000014A.w
abs_0_000618A6:
	cmp.b #$1A,d2
	beq.b abs_0_000618BE
	movem.l d0/d6-d7/a0-a1,-(a7)
	move.w d4,d1
	addi.w #248,d2
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d0/d6-d7/a0-a1
abs_0_000618BE:
	add.w d7,d0
	cmp.w #$140,d0
	ble.b abs_0_00061880
	subq.w #2,absolute_slot_00000146.w
	addq.w #2,absolute_slot_00000144.w
	rts
abs_0_000618D0:
	addq.w #1,absolute_slot_0000014C.w
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_000618E0:
	moveq.l #0,d2
	move.b (a0)+,d2
	cmp.b #$20,d2
	bne.b abs_0_000618EE
	move.b #$5B,d2
abs_0_000618EE:
	subi.b #65,d2
	move.w d2,d3
	add.w d3,d3
	move.w abs_0_000618FC(pc,d3.w),d7
	rts
abs_0_000618FC:
	dc.w $000F,$0010,$000D,$0010,$000D,$000E,$000E,$0011	; lookup_table
	dc.w $000A,$000A,$0011,$000B,$0011,$000F,$000F,$0010	; lookup_table
	dc.w $0010,$0011,$000C,$000C,$0011,$000F,$0011,$000F	; lookup_table
	dc.w $0010,$000E,$0010	; lookup_table
abs_0_00061932:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_0006193C
	addq.w #1,absolute_slot_0000014C.w
abs_0_0006193C:
	rts
abs_0_0006193E:
	move.w #$F,absolute_slot_0000028A.w
abs_0_00061944:
	tst.w absolute_slot_000001E4.w
	beq.b abs_0_00061944
abs_0_0006194A:
	cmpi.b #128,_custom+vhposr.l
	bne.b abs_0_0006194A
	bsr.w abs_0_00061A6E
	tst.w absolute_slot_0000028A.w
	beq.b abs_0_00061968
	subq.w #1,absolute_slot_0000028A.w
	clr.w absolute_slot_000001E4.w
	bra.b abs_0_00061944
abs_0_00061968:
	addq.w #1,absolute_slot_0000014C.w
	bsr.w abs_0_00061AC2
	lea.l _custom.l,a6
abs_0_00061976:
	cmpi.b #128,vhposr(a6)
	bne.b abs_0_00061976
	move.l #$3B40,cop1lc(a6)	; copper_list pointer
	move.w copjmp1(a6),d0
	bsr.w abs_0_00061B5A
	clr.w absolute_slot_00000148.w
	clr.w absolute_slot_0000028C.w
	moveq.l #0,d0
	bsr.w abs_0_00061BEE
	move.w #$1,absolute_slot_0000028C.w
	lea.l absolute_slot_00006F50.l,a0
	lea.l absolute_slot_0006B428.l,a1
	bsr.w abs_0_00061C00
	rts
abs_0_000619B4:
	lea.l _custom.l,a6
abs_0_000619BA:
	tst.w absolute_slot_000001E4.w
	beq.b abs_0_000619BA
	addq.w #2,absolute_slot_00000148.w
	bsr.w abs_0_00061BA8
	cmpi.w #320,absolute_slot_00000148.w
	bne.b abs_0_000619D4
	bsr.w abs_0_00061B6E
abs_0_000619D4:
	cmpi.w #640,absolute_slot_00000148.w
	bne.b abs_0_000619F8
	clr.w absolute_slot_00000148.w
	cmpi.w #12,absolute_slot_0000028C.w
	beq.b abs_0_00061A0E
	lea.l absolute_slot_00006F50.l,a0
	lea.l absolute_slot_0006B428.l,a1
	bsr.w abs_0_00061C00
abs_0_000619F8:
	clr.w absolute_slot_000001E4.w
	btst.b #CIAB_GAMEPORT1,_ciaa+ciapra.l
	beq.b abs_0_00061A0E
	cmpi.b #64,m68k_vector_trap_4_instruction_vector.w
	bne.b abs_0_000619B4
abs_0_00061A0E:
	clr.w absolute_slot_0000014C.w
	lea.l _custom.l,a6
abs_0_00061A18:
	cmpi.b #128,vhposr(a6)
	bne.b abs_0_00061A18
	move.l #$3940,cop1lc(a6)	; copper_list pointer
	move.w copjmp1(a6),d0
	bsr.w abs_0_0005C966
	clr.w absolute_slot_0000028A.w
abs_0_00061A34:
	tst.w absolute_slot_000001E4.w
	beq.b abs_0_00061A34
abs_0_00061A3A:
	cmpi.b #128,_custom+vhposr.l
	bne.b abs_0_00061A3A
	bsr.w abs_0_00061A6E
	cmpi.w #15,absolute_slot_0000028A.w
	beq.b abs_0_00061A5A
	addq.w #1,absolute_slot_0000028A.w
	clr.w absolute_slot_000001E4.w
	bra.b abs_0_00061A34
abs_0_00061A5A:
	bsr.w abs_0_0005C992
	clr.w absolute_slot_0000013C.w
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	rts
abs_0_00061A6E:
	move.w absolute_slot_0000028A.w,d0
	move.w #$5AF,d1
	move.w d1,d2
	move.w d1,d3
	andi.w #3840,d1
	andi.w #240,d2
	andi.w #15,d3
	mulu.w d0,d1
	mulu.w d0,d2
	mulu.w d0,d3
	lsr.w #4,d1
	lsr.w #4,d2
	lsr.w #4,d3
	andi.w #3840,d1
	andi.w #240,d2
	andi.w #15,d3
	or.w d2,d1
	or.w d3,d1
	lea.l absolute_slot_00003940.l,a1
	moveq.l #15,d7
abs_0_00061AAA:
	addq.w #2,a1
	move.w d1,(a1)+
	dbf.w d7,abs_0_00061AAA
	movea.l absolute_slot_0000011A.w,a1
	moveq.l #19,d7
abs_0_00061AB8:
	addq.w #2,a1
	move.w d1,(a1)+
	dbf.w d7,abs_0_00061AB8
	rts
abs_0_00061AC2:
	lea.l absolute_slot_00003B40.l,a0
	moveq.l #15,d7
	moveq.l #0,d0
	bsr.w abs_0_0005C744
	move.l #$64446,d0
	moveq.l #7,d6
	move.w #$120,d7
	moveq.l #0,d5
	bsr.w abs_0_0005C72C
	move.l #$8E2C81,(a0)+
	move.l #$902CC1,(a0)+
	move.l #$920030,(a0)+
	move.l #$9400D0,(a0)+
	move.l #$10400FF,(a0)+
	move.l #$1080026,(a0)+
	move.l #$10A0026,(a0)+
	move.l #$10400FF,(a0)+
	move.l a0,absolute_slot_00000112.w
	move.l #$1020000,(a0)+
	move.l #$6B400,d0
	moveq.l #3,d6
	move.w #$E0,d7
	move.l #$5000,d5
	bsr.w abs_0_0005C72C
	move.l #$1004200,(a0)+
	move.l #$C001FF00,(a0)+
	move.w #$9C,(a0)+
	move.w #$8010,(a0)+
	move.l #$D001FF00,(a0)+
	move.w #$9C,(a0)+
	move.w #$8010,(a0)+
	moveq.l #-2,d0
	move.l d0,(a0)+
	rts
abs_0_00061B5A:
	lea.l absolute_slot_0006B400.l,a0
	move.w #$2827,d0
abs_0_00061B64:
	clr.l (a0)+
	clr.l (a0)+
	dbf.w d0,abs_0_00061B64
	rts
abs_0_00061B6E:
	clr.w absolute_slot_000001E4.w
	cmpi.w #12,absolute_slot_0000028C.w
	beq.b abs_0_00061B88
	moveq.l #0,d0
	move.w absolute_slot_0000028C.w,d0
	bsr.w abs_0_00061BEE
	addq.w #1,absolute_slot_0000028C.w
abs_0_00061B88:
	btst.b #CIAB_GAMEPORT1,_ciaa+ciapra.l
	beq.b abs_0_00061BA2
	cmpi.b #64,m68k_vector_trap_4_instruction_vector.w
	beq.b abs_0_00061BA2
	cmpi.w #200,absolute_slot_000001E4.w
	ble.b abs_0_00061B88
abs_0_00061BA2:
	clr.b m68k_vector_trap_4_instruction_vector.w
	rts
abs_0_00061BA8:
	movea.l absolute_slot_00000112.w,a0
	move.w absolute_slot_00000148.w,d0
	move.w d0,d1
	andi.w #15,d0
	move.b abs_0_00061BDE(pc,d0.w),d0
	move.b d0,$0003(a0)
	addq.w #4,a0
	move.l #$6B400,d0
	lsr.w #4,d1
	add.w d1,d1
	add.w d1,d0
	moveq.l #3,d6
	move.w #$E0,d7
	move.l #$5000,d5
	bsr.w abs_0_0005C72C
	rts
abs_0_00061BDE:
	dc.b $FF,$EE,$DD,$CC,$BB,$AA,$99,$88,$77,$66,$55,$44,$33,$22,$11,$00	; lookup_table
abs_0_00061BEE:
	lea.l abs_0_00062267(pc),a0
	add.w d0,d0
	adda.w d0,a0
	lea.l absolute_slot_00006F50.l,a1
	trap #3
	rts
abs_0_00061C00:
	moveq.l #3,d2
abs_0_00061C02:
	move.w #$FF,d1
abs_0_00061C06:
	moveq.l #9,d0
abs_0_00061C08:
	move.l (a0)+,(a1)+
	dbf.w d0,abs_0_00061C08
	adda.w #$28,a1
	dbf.w d1,abs_0_00061C06
	dbf.w d2,abs_0_00061C02
	lea.l absolute_slot_00003B42.l,a1
	moveq.l #15,d0
abs_0_00061C22:
	move.w (a0)+,(a1)
	addq.w #4,a1
	dbf.w d0,abs_0_00061C22
	rts
abs_0_00061C2C:
	clr.w absolute_slot_0000024A.w
	cmpi.w #186,absolute_slot_0000018E.w
	ble.b abs_0_00061C4C
	cmpi.w #281,absolute_slot_0000018C.w
	ble.b abs_0_00061C4C
	move.w #$1,absolute_slot_0000024A.w
	moveq.l #-3,d0
	bsr.w abs_0_0005FA82
abs_0_00061C4C:
	rts
abs_0_00061C4E:
	clr.w absolute_slot_0000024A.w
	cmpi.w #186,absolute_slot_0000018E.w
	ble.b abs_0_00061C6E
	cmpi.w #17,absolute_slot_0000018C.w
	bge.b abs_0_00061C6E
	move.w #$1,absolute_slot_0000024A.w
	moveq.l #-3,d0
	bsr.w abs_0_0005FA82
abs_0_00061C6E:
	rts
abs_0_00061C70:
	lea.l abs_0_000623A4(pc),a0
	move.w absolute_slot_00000288.w,d1
	andi.w #62,d1
	move.w $0(a0,d1.w),d1
	addi.w #62,d1
	move.w d1,absolute_slot_000002D4.w
	move.w d1,absolute_slot_000002D8.w
	lea.l abs_0_0006497C(pc),a0
	lea.l absolute_slot_000002D6.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$F0,d0
	move.w absolute_slot_000002D4.w,d1
	move.w absolute_slot_000002D6.w,d2
	bsr.w abs_0_0005CC5C
	lea.l abs_0_0006498E(pc),a0
	lea.l absolute_slot_000002DA.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$1C,d0
	move.w absolute_slot_000002D8.w,d1
	move.w absolute_slot_000002DA.w,d2
	bsr.w abs_0_0005CC5C
	addq.w #3,absolute_slot_00000288.w
	rts
abs_0_00061CCA:
	move.w absolute_slot_000002F4.w,d0
	beq.b abs_0_00061CDE
	subq.w #1,d0
	beq.b abs_0_00061CE0
	subq.w #1,d0
	beq.b abs_0_00061D2A
	subq.w #1,d0
	beq.w abs_0_00061D50
abs_0_00061CDE:
	rts
abs_0_00061CE0:
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_00061CEA:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_00061CEA
	lea.l abs_0_00062255(pc),a0
	movea.l absolute_slot_00000126.w,a1
	trap #3
	bsr.w abs_0_00061D9C
	lea.l abs_0_00064C9C(pc),a0
	bsr.w abs_0_0005D8A2
	lea.l abs_0_00064CC6(pc),a0
	bsr.w abs_0_0005D8A2
	clr.w absolute_slot_00000146.w
	clr.w absolute_slot_0000014A.w
	clr.w absolute_slot_0000014C.w
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	addq.w #1,absolute_slot_000002F4.w
	rts
abs_0_00061D2A:
	tst.w absolute_slot_0000014C.w
	beq.b abs_0_00061D36
	addq.w #1,absolute_slot_000002F4.w
	rts
abs_0_00061D36:
	bsr.w abs_0_0005CEFA
	bsr.w abs_0_00061D66
	lea.l abs_0_00064302(pc),a0
	bsr.w abs_0_00061870
	bsr.w abs_0_0005C41C
	clr.w absolute_slot_000001E4.w
	rts
abs_0_00061D50:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_00061D50
	clr.w absolute_slot_0000014C.w
	clr.w absolute_slot_000002F4.w
	move.w #$1,absolute_slot_000002FE.w
	rts
abs_0_00061D66:
	lea.l abs_0_00064C9C(pc),a0
	lea.l absolute_slot_000001B4.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$8A,d0
	moveq.l #54,d1
	move.w absolute_slot_000001B4.w,d2
	bsr.w abs_0_0005CC5C
	lea.l abs_0_00064CC6(pc),a0
	lea.l absolute_slot_00000190.w,a1
	bsr.w abs_0_0005D8AE
	move.w #$A3,d0
	moveq.l #54,d1
	move.w absolute_slot_00000190.w,d2
	bsr.w abs_0_0005CC5C
	rts
abs_0_00061D9C:
	movea.l absolute_slot_00000126.w,a0
	movea.l absolute_slot_0000012A.w,a1
	move.w #$BF,d1
abs_0_00061DA8:
	moveq.l #39,d0
abs_0_00061DAA:
	move.b $5A00(a0),$007E(a1)
	move.b $3C00(a0),$0054(a1)
	move.b $1E00(a0),$002A(a1)
	move.b (a0)+,(a1)+
	dbf.w d0,abs_0_00061DAA
	lea.l $0080(a1),a1
	dbf.w d1,abs_0_00061DA8
	bsr.w abs_0_00061808
	rts
abs_0_00061DD0:
	lea.l abs_0_000648DA(pc),a0
abs_0_00061DD4:
	cmpi.l #1145392161,(a0)
	beq.b abs_0_00061DEA
	bsr.w abs_0_0005D8A2
	addq.w #8,a0
abs_0_00061DE2:
	cmpi.w #$FFFF,(a0)+
	bne.b abs_0_00061DE2
	bra.b abs_0_00061DD4
abs_0_00061DEA:
	rts
abs_0_00061DEC:
	move.w absolute_slot_000002F6.w,d0
	beq.b abs_0_00061DFE
	subq.w #1,d0
	beq.b abs_0_00061E00
	subq.w #1,d0
	beq.b abs_0_00061E38
	subq.w #1,d0
	beq.b abs_0_00061E74
abs_0_00061DFE:
	rts
abs_0_00061E00:
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_00061E0A:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_00061E0A
	bsr.w abs_0_000617C0
	bsr.w abs_0_00061808
	move.w #$FF9C,absolute_slot_000002FA.w
	move.w #$177,absolute_slot_000002FC.w
	clr.w absolute_slot_000002F8.w
	move.w #$1,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
	addq.w #1,absolute_slot_000002F6.w
	rts
abs_0_00061E38:
	bsr.w abs_0_0005CEFA
	cmpi.w #120,absolute_slot_000002FA.w
	beq.b abs_0_00061E4C
	addq.w #4,absolute_slot_000002FA.w
	subq.w #4,absolute_slot_000002FC.w
abs_0_00061E4C:
	bsr.w abs_0_00061E82
	cmpi.w #140,absolute_slot_000002F8.w
	bne.b abs_0_00061E66
	addq.w #1,absolute_slot_000002F6.w
	move.w #$FFFF,absolute_slot_000001EA.w
	st.b absolute_slot_000001E6.w
abs_0_00061E66:
	addq.w #1,absolute_slot_000002F8.w
	bsr.w abs_0_0005C41C
	clr.w absolute_slot_000001E4.w
	rts
abs_0_00061E74:
	tst.b absolute_slot_000001E6.w
	bne.b abs_0_00061E74
	move.w #$1,absolute_slot_000002FE.w
	rts
abs_0_00061E82:
	lea.l abs_0_00061EC4(pc),a0
	moveq.l #3,d7
	move.w absolute_slot_000002FA.w,d6
abs_0_00061E8C:
	move.w (a0)+,d0
	add.w d6,d0
	move.w (a0)+,d1
	move.w (a0)+,d2
	movem.l d6-d7/a0,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d6-d7/a0
	dbf.w d7,abs_0_00061E8C
	moveq.l #3,d7
	move.w absolute_slot_000002FC.w,d6
abs_0_00061EAA:
	move.w (a0)+,d0
	add.w d6,d0
	move.w (a0)+,d1
	move.w (a0)+,d2
	movem.l d6-d7/a0,-(a7)
	bsr.w abs_0_0005CC5C
	movem.l (a7)+,d6-d7/a0
	dbf.w d7,abs_0_00061EAA
	rts
abs_0_00061EC4:
	dc.w $0000,$0040,$00FE,$000E,$0040,$00F8,$001A,$0040	; lookup_table
	dc.w $0104,$002A,$0040,$00FC,$0000,$0050,$0106,$000E	; lookup_table
	dc.w $0050,$010D,$001C,$0050,$00FC,$0028,$0050,$0109	; lookup_table
abs_0_00061EF4:
	lea.l absolute_slot_00003B40.l,a0
	moveq.l #31,d7
	moveq.l #0,d0
	bsr.w abs_0_0005C744
	move.l #$64446,d0
	moveq.l #7,d6
	move.w #$120,d7
	moveq.l #0,d5
	bsr.w abs_0_0005C72C
	move.l #$8E2C81,(a0)+
	move.l #$902CC1,(a0)+
	move.l #$920038,(a0)+
	move.l #$9400D0,(a0)+
	move.l #$1080000,(a0)+
	move.l #$10A0000,(a0)+
	move.l #$1040000,(a0)+
	move.l #$1020000,(a0)+
	move.l #$6B400,d0
	moveq.l #5,d6
	move.w #$E0,d7
	move.l #$2800,d5
	bsr.w abs_0_0005C72C
	move.l #$1006200,(a0)+
	move.l #$C001FF00,(a0)+
	move.w #$9C,(a0)+
	move.w #$8010,(a0)+
	move.l #$D001FF00,(a0)+
	move.w #$9C,(a0)+
	move.w #$8010,(a0)+
	moveq.l #-2,d0
	move.l d0,(a0)+
	rts
abs_0_00061F82:
	lea.l abs_0_0006227D(pc),a0
	lea.l absolute_slot_0006B400.l,a1
	trap #3
	rts
abs_0_00061F90:
	clr.w absolute_slot_0000028A.w
	clr.w absolute_slot_000001E4.w
abs_0_00061F98:
	cmpi.w #1,absolute_slot_000001E4.w
	ble.b abs_0_00061F98
	bsr.b abs_0_00062006
	clr.w absolute_slot_000001E4.w
	addq.w #1,absolute_slot_0000028A.w
	cmpi.w #16,absolute_slot_0000028A.w
	bne.b abs_0_00061F98
	rts
abs_0_00061FB4:
	move.w #$F,absolute_slot_0000028A.w
	clr.w absolute_slot_000001E4.w
abs_0_00061FBE:
	cmpi.w #1,absolute_slot_000001E4.w
	ble.b abs_0_00061FBE
	bsr.b abs_0_00062006
	clr.w absolute_slot_000001E4.w
	subq.w #1,absolute_slot_0000028A.w
	bge.b abs_0_00061FBE
	bsr.w abs_0_00061B5A
	clr.w absolute_slot_0000028A.w
	clr.w absolute_slot_000001E4.w
abs_0_00061FDE:
	cmpi.w #1,absolute_slot_000001E4.w
	ble.b abs_0_00061FDE
abs_0_00061FE6:
	cmpi.b #128,_custom+vhposr.l
	bne.b abs_0_00061FE6
	bsr.w abs_0_00062050
	clr.w absolute_slot_000001E4.w
	addq.w #1,absolute_slot_0000028A.w
	cmpi.w #16,absolute_slot_0000028A.w
	bne.b abs_0_00061FDE
	rts
abs_0_00062006:
	lea.l absolute_slot_0007A400.l,a0
	lea.l absolute_slot_00003B42.l,a1
	moveq.l #31,d7
	move.w absolute_slot_0000028A.w,d0
abs_0_00062018:
	move.w (a0)+,d1
	move.w d1,d2
	move.w d1,d3
	andi.w #3840,d1
	andi.w #240,d2
	andi.w #15,d3
	mulu.w d0,d1
	mulu.w d0,d2
	mulu.w d0,d3
	lsr.w #4,d1
	lsr.w #4,d2
	lsr.w #4,d3
	andi.w #3840,d1
	andi.w #240,d2
	andi.w #15,d3
	or.w d2,d1
	or.w d3,d1
	move.w d1,(a1)
	addq.w #4,a1
	dbf.w d7,abs_0_00062018
	rts
abs_0_00062050:
	move.w absolute_slot_0000028A.w,d0
	move.w #$5AF,d1
	move.w d1,d2
	move.w d1,d3
	andi.w #3840,d1
	andi.w #240,d2
	andi.w #15,d3
	mulu.w d0,d1
	mulu.w d0,d2
	mulu.w d0,d3
	lsr.w #4,d1
	lsr.w #4,d2
	lsr.w #4,d3
	andi.w #3840,d1
	andi.w #240,d2
	andi.w #15,d3
	or.w d2,d1
	or.w d3,d1
	lea.l absolute_slot_00003B42.l,a0
	moveq.l #31,d7
abs_0_0006208C:
	move.w d1,(a0)
	addq.w #4,a0
	dbf.w d7,abs_0_0006208C
	rts
abs_0_00062096:
	cmpi.b #70,m68k_vector_trap_4_instruction_vector.w
	bne.b abs_0_000620DC
	lea.l _custom.l,a6
	move.w #$7FFF,(a6)
	move.w #$7FFF,(a6)
	move #$2700,sr
	clr.w aud0+ac_vol(a6)
	clr.w aud1+ac_vol(a6)
	clr.w aud2+ac_vol(a6)
	clr.w aud3+ac_vol(a6)
	lea.l abs_0_0006225F(pc),a0
	lea.l absolute_slot_0001A7E0.l,a1
	lea.l $0024(a1),a2
	move.l a2,m68k_vector_trap_0_instruction_vector.w
	trap #3
	lea.l stack_top_00080000.l,a7
	trap #0
abs_0_000620DC:
	clr.b m68k_vector_trap_4_instruction_vector.w
	rts
abs_0_000620E2:
	move.w absolute_slot_00000294.w,d0
	beq.b abs_0_000620EE
	subq.w #1,d0
	beq.b abs_0_00062138
abs_0_000620EC:
	rts
abs_0_000620EE:
	cmpi.w #214,absolute_slot_0000026E.w
	bne.b abs_0_000620EC
	move.w #$1,absolute_slot_00000294.w
	move.l #$C00000,absolute_slot_00000300.w
	move.l #$890000,absolute_slot_00000304.w
	moveq.l #0,d0
	move.w absolute_slot_0000018C.w,d0
	cmp.w #$BC,d0
	ble.b abs_0_0006211C
	move.w #$AA,d0
abs_0_0006211C:
	swap.w d0
	move.l d0,absolute_slot_00000310.w
	moveq.l #0,d0
	move.w absolute_slot_0000018E.w,d0
	subi.w #10,d0
	swap.w d0
	move.l d0,absolute_slot_00000314.w
	bsr.w abs_0_0006217C
	rts
abs_0_00062138:
	move.l absolute_slot_00000308.w,d0
	add.l d0,$0300.w
	move.l absolute_slot_0000030C.w,d0
	add.l d0,$0304.w
	move.l absolute_slot_00000300.w,d0
	swap.w d0
	tst.w d0
	bmi.b abs_0_00062176
	cmp.w #$140,d0
	bge.b abs_0_00062176
	move.l absolute_slot_00000304.w,d1
	swap.w d1
	tst.w d1
	bmi.b abs_0_00062176
	cmp.w #$C0,d1
	bge.b abs_0_00062176
	move.w #$EC,d2
	bsr.w abs_0_0005CC5C
	bsr.w abs_0_000621D0
	rts
abs_0_00062176:
	clr.w absolute_slot_00000294.w
	rts
abs_0_0006217C:
	move.l absolute_slot_00000300.w,d0
	move.l absolute_slot_00000304.w,d1
	move.l absolute_slot_00000310.w,d2
	move.l absolute_slot_00000314.w,d3
	sub.l d0,d2
	sub.l d1,d3
	move.l d2,d0
	move.l d3,d1
	swap.w d0
	swap.w d1
	ext.l d0
	ext.l d1
	move.w d0,d2
	bge.b abs_0_000621A2
	neg.w d2
abs_0_000621A2:
	move.w d1,d3
	bge.b abs_0_000621A8
	neg.w d3
abs_0_000621A8:
	cmp.w d3,d2
	bgt.b abs_0_000621AE
	exg d2,d3
abs_0_000621AE:
	tst.w d2
	bgt.b abs_0_000621BA
	moveq.l #1,d1
	swap.w d1
	moveq.l #0,d0
	bra.b abs_0_000621C6
abs_0_000621BA:
	move.l #$30000,d3
	divs.w d2,d3
	muls.w d3,d0
	muls.w d3,d1
abs_0_000621C6:
	move.l d0,absolute_slot_00000308.w
	move.l d1,absolute_slot_0000030C.w
	rts
abs_0_000621D0:
	move.l absolute_slot_00000300.w,d0
	swap.w d0
	moveq.l #6,d1
	move.l absolute_slot_00000304.w,d2
	swap.w d2
	moveq.l #4,d3
	bsr.w abs_0_0005F1E4
	tst.w d0
	beq.b abs_0_000621EE
	moveq.l #-3,d0
	bsr.w abs_0_0005FA82
abs_0_000621EE:
	rts
abs_0_000621F0:
	dc.b "BLKS",$00
abs_0_000621F5:
	dc.b "GPAL",$00
abs_0_000621FA:
	dc.b "TUNE00",$00
abs_0_00062201:
	dc.b $4D,$41,$50,$00
abs_0_00062205:
	dc.b "SPRITES1.RAW",$00
abs_0_00062212:
	dc.b "SPRITES2.RAW",$00
abs_0_0006221F:
	dc.b "SPRITES3.RAW",$00
abs_0_0006222C:
	dc.b "PANEL.RAW",$00
abs_0_00062236:
	dc.b "FONT",$00
abs_0_0006223B:
	dc.b "HEIGHT.DATA",$00
abs_0_00062247:
	dc.b "PANELBITS.RAW",$00
abs_0_00062255:
	dc.b "HEART.RAW",$00
abs_0_0006225F:
	dc.b "PIC.HAM",$00
abs_0_00062267:
	dc.b $31,$00,$32,$00,$33,$00,$34,$00,$35,$00,$36,$00,$38,$00,$39,$00
	dc.b $41,$00,$30,$00,$43,$00
abs_0_0006227D:
	dc.b $37,$00,$00
abs_0_00062280:
	dc.b $26,$2B,$24,$26,$26,$26,$26,$24,$2E,$2F,$26,$3B,$28,$39,$29,$26
	dc.b $1A,$1B,$1C,$1D,$1E,$1F,$20,$21,$22,$23,$26,$26,$26,$26,$26,$2A
	dc.b $26,$00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$0A,$0B,$0C,$0D,$0E
	dc.b $0F,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$26,$26,$26,$26,$26
	dc.b $26,$00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$0A,$0B,$0C,$0D,$0E
	dc.b $0F,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$00
abs_0_000622DC:
	dc.b $30,$30,$30,$31,$30,$32,$30,$33,$30,$34,$30,$35,$30,$36,$30,$37
	dc.b $30,$38,$30,$39,$31,$30,$31,$31,$31,$32,$31,$33,$31,$34,$31,$35
	dc.b $31,$36,$31,$37,$31,$38,$31,$39,$32,$30,$32,$31,$32,$32,$32,$33
	dc.b $32,$34,$32,$35,$32,$36,$32,$37,$32,$38,$32,$39,$33,$30,$33,$31
abs_0_0006231C:
	dc.w $FFFF,$FFFF,$0049,$FFFE,$FFFF,$004C,$FFFF,$FFFE	; lookup_table
	dc.w $004E,$0000,$FFFF,$0049,$0001,$FFFF,$004D,$0000	; lookup_table
	dc.w $FFFE,$004E,$FFFF,$0000,$0049,$FFFE,$0000,$004C	; lookup_table
	dc.w $FFFF,$0001,$004F,$0000,$0000,$0049,$0001,$0000	; lookup_table
	dc.w $004D,$0000,$0001,$004F	; lookup_table
abs_0_00062364:
	dc.b $00,$10,$00,$10,$00,$0F,$00,$0F,$00,$0E,$00,$0C,$00,$0B,$00,$0A
	dc.b $00,$08,$00,$06,$00,$05,$00,$04,$00,$02,$00,$01,$00,$01,$00,$00
	dc.b $00,$00,$00,$00,$00,$01,$00,$01,$00,$02,$00,$04,$00,$05,$00,$06
	dc.b $00,$08,$00,$0A,$00,$0B,$00,$0C,$00,$0E,$00,$0F,$00,$0F,$00,$10
abs_0_000623A4:
	dc.b $00,$04,$00,$04,$00,$04,$00,$04,$00,$03,$00,$03,$00,$03,$00,$02
	dc.b $00,$02,$00,$02,$00,$01,$00,$01,$00,$01
	dcb.b $F,$00
	dc.b $01,$00,$01,$00,$01,$00,$02,$00,$02,$00,$02,$00,$03,$00,$03,$00
	dc.b $03,$00,$04,$00,$04,$00,$04
abs_0_000623E4:
	dc.b $00,$50,$00,$50,$00,$50,$00,$50,$00,$4F,$00,$4F,$00,$4E,$00,$4E
	dc.b $00,$4D,$00,$4C,$00,$4B,$00,$4A,$00,$49,$00,$48,$00,$47,$00,$46
	dc.b $00,$44,$00,$43,$00,$41,$00,$40,$00,$3E,$00,$3D,$00,$3B,$00,$39
	dc.b $00,$37,$00,$35,$00,$34,$00,$32,$00,$30,$00,$2E,$00,$2C,$00,$2A
	dc.b $00,$28,$00,$26,$00,$24,$00,$22,$00,$20,$00,$1E,$00,$1C,$00,$1B
	dc.b $00,$19,$00,$17,$00,$15,$00,$13,$00,$12,$00,$10,$00,$0F,$00,$0D
	dc.b $00,$0C,$00,$0A,$00,$09,$00,$08,$00,$07,$00,$06,$00,$05,$00,$04
	dc.b $00,$03,$00,$02,$00,$02,$00,$01,$00,$01
	dcb.b $F,$00
	dc.b $01,$00,$01,$00,$02,$00,$02,$00,$03,$00,$04,$00,$05,$00,$06,$00
	dc.b $07,$00,$08,$00,$09,$00,$0A,$00,$0C,$00,$0D,$00,$0F,$00,$10,$00
	dc.b $12,$00,$13,$00,$15,$00,$17,$00,$19,$00,$1B,$00,$1C,$00,$1E,$00
	dc.b $20,$00,$22,$00,$24,$00,$26,$00,$28,$00,$2A,$00,$2C,$00,$2E,$00
	dc.b $30,$00,$32,$00,$34,$00,$35,$00,$37,$00,$39,$00,$3B,$00,$3D,$00
	dc.b $3E,$00,$40,$00,$41,$00,$43,$00,$44,$00,$46,$00,$47,$00,$48,$00
	dc.b $49,$00,$4A,$00,$4B,$00,$4C,$00,$4D,$00,$4E,$00,$4E,$00,$4F,$00
	dc.b $4F,$00,$50,$00,$50,$00,$50
abs_0_000624E4:
	dc.b $00,$40,$00,$1A,$00,$40,$00,$2E,$00,$40,$00,$42
abs_0_000624F0:
	dc.b $00,$00,$00,$00,$00,$05,$E6,$14,$00,$05,$E7,$CE,$00,$05,$E8,$C2
	dcb.b $D,$00
	dc.b $05,$E6,$F0,$00,$06,$08,$D2,$00,$00,$00,$00,$00,$05,$E7,$42,$00
	dc.b $05,$E9,$96,$00,$05,$E7,$90,$00,$06,$08,$C0,$00,$05,$E8,$D0,$00
	dc.b $00,$00,$00,$00,$05,$EC,$36,$00,$00,$00,$00,$00,$05,$ED,$8A,$00
	dc.b $05,$EC,$06,$00,$05,$EC,$16,$00,$05,$EA,$04,$00,$05,$F0,$DE,$00
	dc.b $05,$F1,$2C,$00,$05,$E8,$F0,$00,$05,$EC,$C8,$00,$05,$EB,$6C,$00
	dc.b $06,$04,$72,$00,$05,$EC,$DC,$00,$00,$00,$00,$00,$05,$EC,$D2
	dcb.b $D,$00
	dc.b $05,$EC,$E6,$00,$00,$00,$00,$00,$05,$F1,$48,$00,$00,$00,$00,$00
	dc.b $05,$EC,$F0,$00,$05,$F1,$60,$00,$05,$EC,$50
	dcb.b $9,$00
	dc.b $06,$09,$DE,$00,$00,$00,$00,$00,$06,$07,$62,$00,$05,$F0,$B4,$00
	dc.b $00,$00,$00,$00,$06,$07,$32,$00,$05,$F0,$BA,$00,$00,$00,$00,$00
	dc.b $05,$EF,$DA,$00,$05,$EE,$88,$00,$06,$15,$16,$00,$06,$15,$E2,$00
	dc.b $06,$16,$5E
	dcb.b $20,$00
abs_0_000625F0:
	dc.b $20,$20,$20,$20,$20,$20,$57,$45,$49,$52,$44,$2D,$48,$45,$4E,$47
	dc.b $45
	dcb.b $9,$20
	dc.b $54,$48,$45,$20,$48,$41,$55,$4E,$54,$45,$44,$20,$53,$57,$41,$4D
	dc.b $50,$20,$20,$20,$20,$20,$47,$4F,$4F,$44,$20,$57,$49,$54,$43,$48
	dc.b $27,$53,$20,$49,$53,$4C,$41,$4E,$44,$20,$20,$20,$20,$20,$54,$48
	dc.b $45,$20,$48,$41,$55,$4E,$54,$45,$44,$20,$53,$57,$41,$4D,$50,$20
	dc.b $20,$20,$54,$48,$45,$20,$4D,$59,$53,$54,$45,$52,$49,$4F,$55,$53
	dc.b $20,$4D,$4F,$4E,$4F,$4C,$49,$54,$48,$20,$20,$20,$20,$55,$50,$20
	dc.b $54,$48,$45,$20,$4D,$4F,$4E,$4F,$4C,$49,$54,$48,$20,$20,$20,$20
	dc.b $20,$20,$54,$4F,$50,$20,$4F,$46,$20,$54,$48,$45,$20,$4D,$4F,$4E
	dc.b $4F,$4C,$49,$54,$48,$20,$20,$20,$20,$20,$20,$54,$48,$45,$20,$42
	dc.b $55,$53,$48,$59,$20,$47,$52,$4F,$56,$45
	dcb.b $B,$20
	dc.b $55,$50,$20,$41,$20,$54,$52,$45,$45
	dcb.b $C,$20
	dc.b $54,$48,$45,$20,$54,$52,$45,$45,$20,$54,$4F,$50,$21
	dcb.b $A,$20
	dc.b $53,$4C,$45,$45,$50,$59,$20,$48,$4F,$4C,$4C,$4F,$57,$20,$20,$20
	dc.b $20,$20,$20,$54,$48,$45,$20,$42,$41,$52,$44,$27,$53,$20,$54,$52
	dc.b $45,$45,$48,$4F,$55,$53,$45,$21,$20,$54,$48,$45,$20,$53,$57,$4F
	dc.b $52,$44,$20,$49,$4E,$20,$54,$48,$45,$20,$53,$54,$4F,$4E,$45,$21
	dc.b $20,$20,$20,$20,$20,$4F,$55,$54,$20,$4F,$4E,$20,$41,$20,$4C,$49
	dc.b $4D,$42
	dcb.b $9,$20
	dc.b $54,$48,$45,$20,$54,$52,$4F,$4C,$4C,$42,$52,$49,$44,$47,$45,$20
	dc.b $20,$20,$20,$20,$20,$20,$41,$43,$52,$4F,$53,$53,$20,$54,$48,$45
	dc.b $20,$42,$52,$49,$44,$47,$45,$20,$20,$20,$20,$20,$54,$48,$45,$20
	dc.b $48,$4F,$54,$20,$57,$41,$54,$45,$52,$20,$47,$59,$53,$45,$52,$20
	dc.b $20,$20,$43,$4C,$49,$4D,$42,$49,$4E,$47,$20,$54,$48,$45,$20,$56
	dc.b $4F,$4C,$43,$41,$4E,$4F,$21,$20
abs_0_0006278E:
	dcb.b $1E,$20
	dc.b $48,$45,$4C,$4C,$20,$47,$41,$54,$45,$20,$20,$20,$20,$20,$20,$20
	dc.b $44,$45,$53,$43,$45,$4E,$54,$20,$49,$4E,$54,$4F,$20,$54,$48,$45
	dc.b $20,$44,$45,$50,$54,$48,$53
	dcb.b $9,$20
	dc.b $48,$41,$44,$45,$53
	dcb.b $A,$20
	dc.b $54,$48,$45,$20,$43,$52,$41,$43,$4B,$53,$20,$4F,$46,$20,$47,$45
	dc.b $48,$45,$4E,$4E,$41,$20,$20,$20,$20,$20,$20,$20,$59,$45,$20,$4F
	dc.b $4C,$44,$20,$57,$45,$4C,$4C
	dcb.b $A,$20
	dc.b $43,$41,$53,$54,$4C,$45,$20,$42,$41,$43,$4B,$44,$4F,$4F,$52
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$47,$52,$41,$4E,$44,$20,$48,$41,$4C,$4C,$21
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$54,$48,$52,$4F,$4E,$45,$20,$52,$4F,$4F,$4D
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$44,$52,$41,$57,$42,$52,$49,$44,$47,$45,$21
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$57,$41,$54,$43,$48,$20,$54,$4F,$57,$45,$52
	dcb.b $A,$20
	dc.b $54,$48,$45,$20,$43,$48,$41,$50,$45,$4C,$21
	dcb.b $9,$20
	dc.b $54,$48,$45,$20,$55,$50,$50,$45,$52,$20,$47,$41,$4C,$4C,$45,$52
	dc.b $59,$20,$20,$20,$20,$20,$41,$20,$54,$4F,$57,$45,$52,$20,$57,$49
	dc.b $54,$48,$20,$41,$20,$56,$49,$45,$57,$20,$20,$20,$20,$20,$20,$20
	dc.b $49,$4E,$20,$54,$48,$45,$20,$43,$4C,$4F,$55,$44,$53
	dcb.b $9,$20
	dc.b $54,$48,$45,$20,$57,$41,$54,$43,$48,$20,$54,$4F,$57,$45,$52,$20
	dc.b $20,$20,$20,$42,$45,$4C,$4F,$57,$20,$54,$48,$45,$20,$54,$41,$4C
	dc.b $4C,$45,$53,$54,$20,$54,$4F,$57,$45,$52,$20,$20,$20,$54,$48,$45
	dc.b $20,$54,$41,$4C,$4C,$45,$53,$54,$20,$54,$4F,$57,$45,$52
	dcb.b $9,$20
	dc.b $44,$4F,$57,$4E,$20,$41,$20,$57,$45,$4C,$4C
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$53,$45,$43,$52,$45,$54,$20,$50,$41,$53,$53,$41
	dc.b $47,$45,$21,$20,$20,$20,$54,$48,$45,$20,$46,$4F,$52,$47,$4F,$54
	dc.b $54,$45,$4E,$20,$44,$55,$4E,$47,$45,$4F,$4E,$20,$20,$20,$20,$20
	dc.b $20,$41,$20,$53,$54,$49,$43,$4B,$59,$20,$45,$4E,$44,$21,$20,$20
	dc.b $20,$20,$20,$20,$20,$49,$43,$45,$20,$50,$41,$4C,$41,$43,$45,$20
	dc.b $45,$4E,$54,$52,$41,$4E,$43,$45,$20,$20,$20,$20,$20,$20,$20,$45
	dc.b $4E,$54,$52,$41,$4E,$43,$45,$20,$48,$41,$4C,$4C
	dcb.b $A,$20
	dc.b $54,$48,$45,$20,$4D,$41,$49,$4E,$20,$48,$41,$4C,$4C
	dcb.b $C,$20
	dc.b $54,$48,$45,$20,$43,$52,$59,$50,$54
	dcb.b $9,$20
	dc.b $54,$48,$45,$20,$44,$45,$45,$50,$45,$53,$54,$20,$44,$55,$4E,$47
	dc.b $45,$4F,$4E,$20,$20,$20,$20,$20,$20,$20,$54,$48,$45,$20,$4F,$55
	dc.b $42,$4C,$49,$45,$54,$54,$45,$20,$20,$20,$20,$20,$20,$20,$43,$4C
	dc.b $49,$4D,$42,$49,$4E,$47,$20,$5A,$41,$4B,$53,$20,$54,$4F,$57,$45
	dc.b $52,$20,$20,$20,$20,$20,$42,$45,$4C,$4F,$57,$20,$5A,$41,$4B,$53
	dc.b $20,$54,$4F,$57,$45,$52,$21
	dcb.b $9,$20
	dc.b $5A,$41,$4B,$53,$20,$54,$4F,$57,$45,$52,$21
	dcb.b $B,$20
	dc.b $4D,$49,$52,$52,$4F,$52,$20,$4D,$49,$52,$52,$4F,$52
	dcb.b $9,$20
	dc.b $54,$48,$45,$20,$57,$45,$53,$54,$20,$54,$4F,$57,$45,$52,$21
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$43,$48,$45,$53,$53,$42,$4F,$41,$52,$44,$21,$20
	dc.b $20,$20,$20,$43,$55,$52,$49,$4F,$55,$53,$45,$52,$20,$41,$4E,$44
	dc.b $20,$43,$55,$52,$49,$4F,$55,$53,$45,$52,$20,$20,$20,$20,$4D,$41
	dc.b $47,$49,$43,$4C,$41,$4E,$44,$20,$44,$49,$5A,$5A,$59
	dcb.b $8,$20
	dc.b $4D,$41,$47,$49,$43,$4C,$41,$4E,$44,$20,$44,$49,$5A,$5A,$59
	dcb.b $8,$20
	dc.b $4D,$41,$47,$49,$43,$4C,$41,$4E,$44,$20,$44,$49,$5A,$5A,$59
	dcb.b $E,$20
	dc.b $53,$4B,$59
	dcb.b $A,$20
abs_0_00062B0F:
	dc.b "  THE DORMANT VOLCANO  "
abs_0_00062B26:
	dc.b "  THE ACTIVE VOLCANO!  ",$00
abs_0_00062B3E:
	dc.b $00,$00,$00,$00,$00,$06,$00,$03,$00,$1C,$00,$0A,$00,$0C,$13,$B0
abs_0_00062B4E:
	dc.b "      NOTHING!      ",$00
	dc.b $00,$00,$0C,$20,$D0,$20,$20,$20,$20,$20,$20,$4E,$4F,$54,$48,$49
	dc.b $4E,$47,$21,$20,$20,$20,$20,$20,$20,$00,$00,$00,$0C,$2D,$F0,$20
	dc.b $20,$20,$20,$20,$20,$4E,$4F,$54,$48,$49,$4E,$47,$21,$20,$20,$20
	dc.b $20,$20,$20,$00,$00,$00,$06,$3B,$10,$20,$20,$20,$20,$20,$45,$58
	dc.b $49,$54,$20,$41,$4E,$44,$20,$44,$4F,$4E,$54,$20,$44,$52,$4F,$50
	dc.b $20,$20,$20,$20,$20,$FF,$00
abs_0_00062BBA:
	dc.b $00,$00,$00,$00,$00,$0C,$00,$11,$00,$10,$00,$02,$00,$0D
	dc.b "Y@CHOOSE ITEM TO",$00
	dc.b $00,$00,$0D,$5F,$28
	dc.b "SELECT OR DROP",$FF
	dc.b $00
abs_0_00062BEE:
	dc.b $00,$00,$00,$00,$00,$0D,$00,$04,$00,$0E,$00,$05,$00,$0F,$17,$A0
	dc.b "WELL DONE!",$00
	dc.b $00,$00,$0D,$22,$20
	dc.b "YOU'VE FOUND A",$00
	dc.b $00,$00,$10,$27,$60
	dc.b "DIAMOND!",$FF
	dc.b $00
abs_0_00062C2C:
	dc.b $00,$06,$2C,$7E,$00,$04,$00,$04,$00,$14,$00,$05,$00,$06,$17,$A0
	dc.b "THE BUSH SPEAKS!",$00
	dc.b $00,$00,$04,$22,$20,$27
	dc.b "HEY DIZZY! THIS IS",$00
	dc.b $00,$04,$27,$60
	dc.b "REALLY HEAVY MAN!!'",$FF
	dc.b $00,$06,$2C,$A4,$00,$06,$00,$09,$00,$14,$00,$01,$00,$06,$2F,$40
	dc.b $27,$44,$59,$4C,$41,$4E,$20,$49,$53,$20,$54,$48,$41,$54,$20,$59
	dc.b $4F,$55,$3F,$27,$FF,$00,$00,$06,$2C,$FC,$00,$0A,$00,$07,$00,$14
	dc.b $00,$04,$00,$0A,$27,$60,$27,$5A,$41,$4B,$53,$20,$54,$55,$52,$4E
	dc.b $45,$44,$20,$4D,$45,$20,$49,$4E,$54,$4F,$00,$00,$00,$0A,$2C,$A0
	dc.b "A BUSH AND I'M LIKE",$00
	dc.b $00,$0A,$31,$E0
	dc.b "ROOTED TO THE SPOT!'",$FF
	dc.b $00,$00,$00,$00,$00,$00,$09,$00,$0A,$00,$14,$00,$04,$00,$0B
	dc.b "7 'I'M REALLY INTO",$00
	dc.b $00,$00,$09,$3C,$60
	dc.b "NATURE MAN, BUT THIS",$00
	dc.b $00,$00,$0C,$41,$A0
	dc.b "IS TOO MUCH!'",$FF
abs_0_00062D4A:
	dc.b $00,$06,$2D,$A4,$00,$03,$00,$02,$00,$18,$00,$05,$00,$04,$0D,$20
	dc.b $27,$54,$48,$45,$20,$57,$49,$5A,$41,$52,$44,$20,$5A,$41,$4B,$53
	dc.b $20,$54,$55,$52,$4E,$53,$00,$00,$00,$06,$12,$60,$41,$4C,$4C,$20
	dc.b $47,$4F,$4F,$44,$20,$54,$4F,$20,$45,$56,$49,$4C,$21,$27,$00,$00
	dc.b $00,$04,$1C,$E0
	dc.b "SAYS PRINCE CHARMING.",$FF
	dc.b $00,$00,$00,$00,$00,$05,$00,$04,$00,$18,$00,$07,$00,$06,$17,$A0
	dc.b $27,$48,$45,$20,$57,$41,$53,$20,$44,$45,$46,$45,$41,$54,$45,$44
	dc.b $20,$59,$45,$41,$52,$53,$00,$00,$00,$05,$1C,$E0
	dc.b "AGO BY A BRAVE HERO, YET",$00
	dc.b $00,$00,$07,$22,$20
	dc.b "HE HAS RETURNED MORE",$00
	dc.b $00,$00,$08,$27,$60
	dc.b "POWERFUL THAN EVER",$00
	dc.b $00,$00,$05,$2C,$A0
	dc.b "BEFORE. THIS WILL BE THE",$00
	dc.b $00,$00,$09,$31,$E0
	dc.b "FINAL CONFLICT!'",$FF
	dc.b $00
abs_0_00062E50:
	dc.b $00,$06,$2E,$8A,$00,$0A,$00,$02,$00,$12,$00,$03,$00,$0A,$0D,$20
	dc.b $27,$48,$45,$59,$20,$44,$4F,$5A,$59,$21,$20,$57,$41,$4B,$45,$20
	dc.b $55,$50,$00,$00,$00,$0B,$12,$60,$59,$4F,$55,$20,$53,$4C,$45,$45
	dc.b $50,$59,$48,$45,$41,$44,$21,$27,$FF,$00,$00,$06,$2E,$E0,$00,$0C
	dc.b $00,$04,$00,$16,$00,$04,$00,$10,$17,$A0
	dc.b "...BUT DOZY IS",$00
	dc.b $00,$00,$0D,$1C,$E0
	dc.b "ABSOLUTELY OUT COLD,",$00
	dc.b $00,$00,$0C,$22,$20
	dc.b "EVEN BY HIS STANDARDS!",$FF
	dc.b $00,$00,$00,$00,$00,$00,$08,$00,$06,$00,$16,$00,$03,$00,$0B,$22
	dc.b $20,$49,$54,$27,$4C,$4C,$20,$54,$41,$4B,$45,$20,$41,$20,$42,$49
	dc.b $47,$00,$00,$00,$08,$27,$60,$53,$48,$4F,$43,$4B,$20,$54,$4F,$20
	dc.b $57,$41,$4B,$45,$20,$48,$49,$4D,$20,$55,$50,$21,$21,$FF,$00
abs_0_00062F1E:
	dc.b $00,$00,$00,$00,$00,$03,$00,$03,$00,$16,$00,$06,$00,$03,$12,$60
	dc.b $2D,$20,$54,$48,$45,$20,$43,$41,$52,$56,$49,$4E,$47,$20,$52,$45
	dc.b $41,$44,$53,$20,$2D,$00,$00,$06,$1C,$E0
	dc.b "WHOSOEVER PULLS",$00
	dc.b $00,$05,$22,$20
	dc.b "EXCALIBUR FROM THE",$00
	dc.b $00,$00,$04,$27,$60
	dc.b "STONE SHALL BE KING.",$FF
	dc.b $00
abs_0_00062F8A:
	dc.b $00,$00,$00,$00,$00,$06,$00,$06,$00,$1C,$00,$05,$00,$09,$22,$20
	dc.b $27,$4F,$59,$27,$20,$47,$52,$55,$4E,$54,$53,$20,$54,$48,$45,$20
	dc.b $54,$52,$4F,$4C,$4C,$2C,$00,$00,$00,$08,$2C,$A0,$27,$59,$4F,$55
	dc.b $20,$43,$41,$4E,$27,$54,$20,$43,$52,$4F,$53,$53,$20,$57,$49,$54
	dc.b $48,$4F,$55,$54,$00,$00,$00,$08,$31,$E0
	dc.b "GIVING ME 30 DIAMONDS!!'",$FF
	dc.b $00
abs_0_00062FEE:
	dc.b $00,$00,$00,$00,$00,$06,$00,$06,$00,$1C,$00,$02,$00,$09,$22,$20
	dc.b $54,$48,$45,$20,$42,$41,$43,$4B,$44,$4F,$4F,$52,$20,$49,$53,$20
	dc.b $4C,$4F,$43,$4B,$45,$44,$FF,$00
abs_0_00063016:
	dc.b $00,$00,$00,$00,$00,$06,$00,$06,$00,$16,$00,$04,$00,$09,$22,$20
	dc.b $54,$48,$45,$20,$42,$41,$52,$44,$20,$49,$47,$4E,$4F,$52,$45,$53
	dc.b $00,$00,$00,$08,$27,$60,$59,$4F,$55,$2C,$20,$48,$45,$27,$53,$20
	dc.b $54,$4F,$4F,$20,$42,$55,$53,$59,$00,$00,$00,$08,$2C,$A0
	dc.b "PLAYING HIS PIPES!",$FF
	dc.b $00
abs_0_00063068:
	dc.b $00,$06,$30,$9A,$00,$06,$00,$06,$00,$12,$00,$03,$00,$09,$22,$20
	dc.b $57,$48,$41,$54,$27,$53,$20,$54,$48,$49,$53,$3F,$00,$00,$00,$08
	dc.b $27,$60,$59,$45,$4C,$4C,$53,$20,$54,$48,$45,$20,$42,$41,$52,$44
	dc.b $FF,$00,$00,$00,$00,$00,$00,$07,$00,$08,$00,$16,$00,$04,$00,$08
	dc.b $2C,$A0,$27,$57,$4F,$57,$21,$20,$52,$4F,$43,$4B,$20,$41,$4E,$44
	dc.b $20,$52,$4F,$4C,$4C,$21,$00,$00,$00,$0A,$31,$E0
	dc.b "EUREKA! I SHAN'T",$00
	dc.b $00,$00,$08
	dc.b "7 NEED THIS ANYMORE!!'",$FF
	dc.b $00
abs_0_000630F0:
	dc.b $00,$06,$31,$76,$00,$06,$00,$06,$00,$1A,$00,$07,$00,$0C,$22,$20
	dc.b $54,$48,$45,$20,$44,$45,$56,$49,$4C,$20,$53,$41,$59,$53,$00,$00
	dc.b $00,$08,$2C,$A0,$27,$5A,$41,$4B,$53,$20,$4D,$41,$44,$45,$20,$41
	dc.b $20,$44,$45,$41,$4C,$20,$57,$49,$54,$48,$00,$00,$00,$08,$31,$E0
	dc.b "ME,I PUT HIS SOUL INTO",$00
	dc.b $00,$00,$0A
	dc.b "7 A RING SO HE COULD",$00
	dc.b $00,$00,$0B,$3C,$60
	dc.b "NEVER BE KILLED'",$FF
	dc.b $00,$00,$06,$31,$DA,$00,$04,$00,$08,$00,$1A,$00,$05,$00,$07,$2C
	dc.b $A0,$27,$48,$45,$20,$42,$45,$54,$52,$41,$59,$45,$44,$20,$4D,$45
	dc.b $20,$41,$4E,$44,$00,$00,$06,$31,$E0
	dc.b "IMPRISONED ME HERE SO",$00
	dc.b $00,$06
	dc.b "7 NO-ONE WOULD KNOW HIS",$00
	dc.b $00,$0D,$3C,$60,$53,$45,$43,$52,$45,$54,$27,$FF,$00,$00,$00,$00
	dc.b $00,$08,$00,$0A,$00,$18,$00,$04,$00,$0A
	dc.b "7 'TAKE MY TRIDENT AND",$00
	dc.b $00,$00,$0A,$3C,$60
	dc.b "KILL ZAKS THEN BRING",$00
	dc.b $00,$00,$0D,$41,$A0
	dc.b "ME THE RING!!'",$FF
	dc.b $00
abs_0_0006322E:
	dc.b $00,$00,$00,$00,$00,$06,$00,$06,$00,$1A,$00,$02,$00,$07,$22,$20
	dc.b $44,$49,$5A,$5A,$59,$27,$53,$20,$48,$41,$4E,$44,$53,$20,$41,$52
	dc.b $45,$20,$46,$55,$4C,$4C,$21,$21,$FF,$00
abs_0_00063258:
	dc.b $00,$00,$00,$00,$00,$04,$00,$06,$00,$14,$00,$03,$00,$09,$22,$20
	dc.b $59,$4F,$55,$20,$43,$55,$54,$20,$41,$00,$00,$05,$27,$60,$4C,$45
	dc.b $41,$46,$20,$4F,$46,$46,$20,$54,$48,$45,$20,$42,$55,$53,$48,$21
	dc.b $FF,$00
abs_0_0006328A:
	dc.b $00,$00,$00,$00,$00,$07,$00,$08,$00,$16,$00,$05,$00,$07,$2C,$A0
	dc.b $27,$4F,$48,$21,$20,$49,$27,$4D,$20,$57,$4F,$52,$52,$49,$45,$44
	dc.b $20,$53,$49,$43,$4B,$00,$00,$09,$31,$E0
	dc.b "ABOUT MY GOBOLINO",$00
	dc.b $00,$07
	dc.b "7 PLEASE FIND HIM FOR ME",$00
	dc.b $00,$00,$07,$3C,$60
	dc.b "IVE LOOKED EVERYWHERE'",$FF
	dc.b $00
abs_0_000632FE:
	dc.b $00,$06,$33,$4E,$00,$06,$00,$06,$00,$12,$00,$04,$00,$07,$22,$20
	dc.b $27,$4F,$48,$20,$54,$48,$41,$4E,$4B,$20,$59,$4F,$55,$20,$53,$4F
	dc.b $00,$00,$00,$07,$27,$60,$4D,$55,$43,$48,$20,$48,$4F,$57,$20,$53
	dc.b $48,$41,$4C,$4C,$20,$49,$00,$00,$00,$06,$2C,$A0
	dc.b "RETURN THE FAVOUR?",$FF
	dc.b $00,$00,$06,$33,$A0,$00,$08,$00,$08,$00,$14,$00,$04,$00,$09,$2C
	dc.b $A0
	dc.b "YOU TELL THE WITCH",$00
	dc.b $00,$00,$09,$31,$E0
	dc.b "WHAT ZAKS HAS DONE",$00
	dc.b $00,$00,$0A
	dc.b "7 TO YOUR FRIENDS,",$FF
	dc.b $00,$00,$06,$34,$0E,$00,$04,$00,$05,$00,$16,$00,$05,$00,$05,$1C
	dc.b $E0,$27,$4D,$59,$20,$4D,$41,$47,$49,$43,$20,$49,$53,$20,$4E,$4F
	dc.b $54,$48,$49,$4E,$47,$00,$00,$00,$07,$22,$20,$43,$4F,$4D,$50,$41
	dc.b $52,$45,$44,$20,$54,$4F,$20,$5A,$41,$4B,$53,$00,$00,$00,$04,$27
	dc.b $60,$50,$4F,$57,$45,$52,$53,$20,$42,$55,$54,$2C,$20,$49,$20,$43
	dc.b $41,$4E,$20,$48,$45,$4C,$50,$00,$00,$00,$06,$2C,$A0
	dc.b "YOUR BUSHY FRIEND",$FF
	dc.b $00,$06,$34,$26,$00,$12,$00,$0E,$00,$0A,$00,$02,$00,$14
	dc.b "L HOW???",$FF
	dc.b $00,$00,$00,$00,$00,$00,$03,$00,$04,$00,$1A,$00,$05,$00,$06,$17
	dc.b $A0,$27,$49,$20,$53,$48,$41,$4C,$4C,$20,$4E,$45,$45,$44,$20,$41
	dc.b $20,$46,$49,$52,$45,$00,$00,$00,$05,$1C,$E0
	dc.b "TO LIGHT MY CAULDRON,A",$00
	dc.b $00,$00,$05,$22,$20
	dc.b "LEAF FROM THE BUSH,AND",$00
	dc.b $00,$00,$06,$27,$60
	dc.b "SOMETHING POISONOUS'",$FF
	dc.b $00
abs_0_0006349E:
	dc.b $00,$00,$00,$00,$00,$05,$00,$06,$00,$15,$00,$03,$00,$06,$22,$20
	dc.b $47,$4C,$45,$4E,$44,$41,$20,$50,$4F,$50,$53,$20,$49,$54,$20,$49
	dc.b $4E,$54,$4F,$00,$00,$09,$27,$60,$54,$48,$45,$20,$43,$41,$55,$4C
	dc.b $44,$52,$4F,$4E,$21,$FF
abs_0_000634D4:
	dc.b $00,$00,$00,$00,$00,$0B,$00,$04,$00,$18,$00,$03,$00,$0C,$17,$A0
	dc.b $27,$52,$49,$42,$42,$45,$54,$21,$20,$49,$54,$27,$53,$20,$4D,$45
	dc.b $20,$44,$4F,$52,$41,$21,$00,$00,$00,$0C,$1C,$E0
	dc.b "SAVE ME DIZZY, CROAK!'",$FF
	dc.b $00
abs_0_00063518:
	dc.b $00,$00,$00,$00,$00,$07,$00,$06,$00,$1A,$00,$03,$00,$08,$22,$20
	dc.b $59,$4F,$55,$20,$46,$49,$4C,$4C,$20,$54,$48,$45,$20,$42,$55,$43
	dc.b $4B,$45,$54,$20,$57,$49,$54,$48,$00,$00,$00,$08,$27,$60,$48,$4F
	dc.b $54,$20,$57,$41,$54,$45,$52,$20,$46,$52,$4F,$4D,$20,$54,$48,$45
	dc.b $20,$47,$59,$53,$45,$52,$FF,$00
abs_0_00063560:
	dc.b $00,$00,$00,$00,$00,$0A,$00,$06,$00,$18,$00,$04,$00,$0B,$22,$20
	dc.b $45,$58,$43,$41,$4C,$49,$42,$55,$52,$20,$57,$4F,$4E,$27,$54,$20
	dc.b $42,$55,$44,$47,$45,$2C,$00,$00,$00,$0C,$27,$60,$59,$4F,$55,$20
	dc.b $4A,$55,$53,$54,$20,$43,$41,$4E,$27,$54,$20,$47,$45,$54,$20,$41
	dc.b $00,$00,$00,$0E,$2C,$A0
	dc.b "GOOD ENOUGH GRIP!",$FF
abs_0_000635B8:
	dc.b $00,$00,$00,$00,$00,$0A,$00,$06,$00,$10,$00,$03,$00,$0A,$22,$20
	dc.b $59,$55,$43,$4B,$21,$20,$49,$54,$27,$53,$20,$53,$54,$55,$43,$4B
	dc.b $00,$00,$00,$0B,$27,$60,$54,$4F,$20,$59,$4F,$55,$52,$20,$47,$4C
	dc.b $4F,$56,$45,$21,$FF,$00
abs_0_000635EE:
	dc.b $00,$00,$00,$00,$00,$0A,$00,$06,$00,$14,$00,$03,$00,$0C,$22,$20
	dc.b $49,$54,$27,$53,$20,$44,$45,$4E,$5A,$49,$4C,$2C,$20,$41,$4E,$44
	dc.b $00,$00,$00,$0A,$27,$60,$48,$45,$20,$46,$45,$45,$4C,$53,$20,$56
	dc.b $45,$52,$59,$20,$43,$4F,$4C,$44,$21,$21,$FF,$00
abs_0_0006362A:
	dc.b $00,$06,$36,$A6,$00,$0A,$00,$06,$00,$17,$00,$06,$00,$0E,$22,$20
	dc.b $27,$57,$45,$4C,$4C,$20,$44,$4F,$4E,$45,$20,$4C,$41,$44,$27,$00
	dc.b $00,$0D,$27,$60,$53,$41,$59,$53,$20,$47,$52,$41,$4E,$44,$20,$44
	dc.b $49,$5A,$5A,$59,$2C,$00,$00,$0C,$2C,$A0,$27,$49,$20,$43,$4F,$55
	dc.b $4C,$44,$4E,$27,$54,$20,$54,$45,$4C,$4C,$20,$49,$46,$00,$00,$0E
	dc.b $31,$E0
	dc.b "I WAS COMING OR",$00
	dc.b $00,$0B
	dc.b "7 GOING IN THIS PLACE!'",$FF
	dc.b $00,$00,$00,$00,$00,$07,$00,$0A,$00,$15,$00,$04,$00,$09
	dc.b "7 'HURRY HOME SON,",$00
	dc.b $00,$00,$08,$3C,$60
	dc.b "I'LL PUT THE KETTLE",$00
	dc.b $00,$0C,$41,$A0
	dc.b "ON FOR YOU!'",$FF
	dc.b $00
abs_0_000636F2:
	dc.b $00,$06,$37,$42,$00,$07,$00,$05,$00,$16,$00,$04,$00,$09,$1C,$E0
	dc.b $27,$48,$4F,$54,$20,$53,$54,$55,$46,$46,$20,$44,$49,$5A,$5A,$21
	dc.b $20,$49,$00,$00,$00,$09,$22,$20,$57,$41,$53,$20,$52,$45,$41,$4C
	dc.b $4C,$59,$20,$43,$48,$49,$4C,$4C,$49,$4E,$47,$00,$00,$0B,$27,$60
	dc.b $4F,$55,$54,$20,$49,$4E,$20,$54,$48,$45,$52,$45,$21,$27,$FF,$00
	dc.b $00,$00,$00,$00,$00,$0A,$00,$07,$00,$18,$00,$03,$00,$0A,$27,$60
	dc.b $27,$48,$45,$59,$20,$4C,$4F,$4F,$4B,$20,$41,$46,$54,$45,$52,$20
	dc.b $54,$48,$49,$53,$20,$46,$4F,$52,$00,$00,$00,$0D,$2C,$A0
	dc.b "ME CATCH YA LATER!'",$FF
abs_0_00063784:
	dc.b $00,$00,$00,$00,$00,$09,$00,$08,$00,$12,$00,$05,$00,$0A,$2C,$A0
	dc.b $27,$48,$45,$59,$20,$57,$4F,$57,$2C,$20,$49,$20,$46,$45,$45,$4C
	dc.b $00,$00,$00,$0B,$31,$E0
	dc.b "FREE,  GROOVY!",$00
	dc.b $00,$00,$0A
	dc.b "7 THANKS. I'LL SEE",$00
	dc.b $00,$00,$0A,$3C,$60
	dc.b "YOU LATER MAN!'",$FF
abs_0_000637E4:
	dc.b $00,$00,$00,$00,$00,$04,$00,$05,$00,$1A,$00,$03,$00,$04,$1C,$E0
	dc.b "YOU WIND UP THE ROPE UNTIL",$00
	dc.b $00,$00,$08,$22,$20
	dc.b "THE BUCKET APPEARS",$FF
	dc.b $00
abs_0_00063828:
	dc.b $00,$00,$00,$00,$00,$04,$00,$04,$00,$14,$00,$02,$00,$06,$17,$A0
	dc.b "KING TAKES QUEEN",$FF
	dc.b $00
abs_0_0006384A:
	dc.b $00,$00,$00,$00,$00,$06,$00,$06,$00,$0F,$00,$04,$00,$06,$22,$20
	dc.b $54,$48,$45,$52,$45,$20,$49,$53,$20,$41,$20,$4C,$4F,$55,$44,$00
	dc.b $00,$07,$27,$60,$43,$4C,$55,$4E,$4B,$2C,$41,$4E,$44,$20,$54,$48
	dc.b $45,$00,$00,$07,$2C,$A0
	dc.b "LEVER STICKS.",$FF
abs_0_0006388E:
	dc.b $00,$00,$00,$00,$00,$03,$00,$04,$00,$1B,$00,$06,$00,$04,$17,$A0
	dc.b $27,$48,$55,$42,$42,$4C,$45,$20,$42,$55,$42,$42,$4C,$45,$20,$41
	dc.b $4E,$44,$20,$53,$49,$4D,$4D,$45,$52,$00,$00,$04,$1C,$E0
	dc.b "OVER A LIGHT CAULDRON FOR",$00
	dc.b $00,$06,$22,$20
	dc.b "TWO MINUTES... THERE,",$00
	dc.b $00,$04,$27,$60
	dc.b "SOAK THIS INTO THE ROOTS",$00
	dc.b $00,$00,$06,$2C,$A0
	dc.b "TO FREE YOUR FRIEND'",$FF
	dc.b $00
abs_0_00063928:
	dc.b $00,$06,$39,$60,$00,$04,$00,$04,$00,$14,$00,$03,$00,$05,$17,$A0
	dc.b $27,$44,$49,$5A,$5A,$59,$20,$4D,$59,$20,$48,$45,$52,$4F,$21,$20
	dc.b $49,$00,$00,$05,$1C,$E0
	dc.b "KNEW YOU'D COME!'",$FF
	dc.b $00,$06,$39,$94,$00,$06,$00,$06,$00,$10,$00,$03,$00,$06,$22,$20
	dc.b $27,$44,$41,$49,$53,$59,$3F,$3F,$20,$59,$4F,$55,$27,$56,$45,$00
	dc.b $00,$07,$27,$60,$50,$55,$54,$20,$4F,$4E,$20,$57,$45,$49,$47,$48
	dc.b $54,$21,$27,$FF,$00,$06,$3A,$00,$00,$02,$00,$08,$00,$14,$00,$05
	dc.b $00,$03,$2C,$A0,$27,$5A,$41,$4B,$53,$20,$43,$41,$53,$54,$20,$41
	dc.b $20,$53,$50,$45,$4C,$4C,$00,$00,$00,$04,$31,$E0
	dc.b "ON ME, LOOK WHAT",$00
	dc.b $00,$00,$02
	dc.b "7 IT DID! I'M TOO BIG",$00
	dc.b $00,$02,$3C,$60
	dc.b "TO GET OUT OF HERE!'",$FF
	dc.b $00,$00,$06,$3A,$18,$00,$12,$00,$0E,$00,$06,$00,$02,$00,$12
	dc.b "L 'WOW!'",$FF
	dc.b $00,$00,$00,$00,$00,$00,$0A,$00,$0C,$00,$14,$00,$03,$00,$0B,$41
	dc.b $A0,$27,$50,$4C,$45,$41,$53,$45,$20,$46,$49,$4E,$44,$20,$41,$20
	dc.b $57,$41,$59,$00,$00,$00,$0A,$46,$E0
	dc.b "TO SHRINK ME AGAIN!'",$FF
	dc.b $00
abs_0_00063A56:
	dc.b $00,$06,$3A,$92,$00,$04,$00,$04,$00,$14,$00,$03,$00,$05,$17,$A0
	dc.b "DAISY SHRINKS BACK",$00
	dc.b $00,$00,$05,$1C,$E0
	dc.b "TO HER NORMAL SIZE",$FF
	dc.b $00,$00,$00,$00,$00,$00,$05,$00,$06,$00,$11,$00,$03,$00,$06,$22
	dc.b $20,$27,$47,$49,$56,$45,$20,$5A,$41,$4B,$53,$20,$4F,$4E,$45,$00
	dc.b $00,$00,$06,$27,$60,$46,$52,$4F,$4D,$20,$4D,$45,$20,$44,$49,$5A
	dc.b $5A,$59,$21,$27,$FF
abs_0_00063AC6:
	dc.b $00,$06,$3B,$10,$00,$04,$00,$04,$00,$11,$00,$04,$00,$05,$17,$A0
	dc.b "PRINCE CHARMING",$00
	dc.b $00,$05,$1C,$E0
	dc.b "KISSES THE FROG",$00
	dc.b $00,$04,$22,$20
	dc.b "AND DORA APPEARS!",$FF
	dc.b $00,$00,$00,$00,$00,$06,$00,$06,$00,$16,$00,$05,$00,$06,$22,$20
	dc.b $27,$54,$48,$41,$4E,$4B,$53,$20,$44,$49,$5A,$5A,$59,$21,$20,$4D
	dc.b $45,$20,$41,$4E,$44,$00,$00,$06,$27,$60,$4D,$52,$20,$43,$48,$41
	dc.b $52,$4D,$49,$4E,$47,$20,$48,$41,$56,$45,$20,$53,$4F,$4D,$45,$00
	dc.b $00,$06,$2C,$A0
	dc.b "BUSINESS TO ATTEND TO!",$00
	dc.b $00,$00,$06,$31,$E0
	dc.b "WE'LL SEE YOU LATER!'",$FF
abs_0_00063B86:
	dc.b $00,$00,$00,$00,$00,$03,$00,$03,$00,$12,$00,$03,$00,$04,$12,$60
	dc.b $59,$4F,$55,$20,$50,$4C,$41,$59,$20,$41,$20,$4D,$45,$52,$52,$59
	dc.b $00,$00,$00,$05,$17,$A0
	dc.b "DIZZY DITTY!!!",$FF
	dc.b $00
abs_0_00063BBC:
	dc.b $00,$00,$00,$00,$00,$03,$00,$03,$00,$16,$00,$03,$00,$04,$12,$60
	dc.b $59,$4F,$55,$20,$43,$48,$41,$52,$4D,$45,$44,$20,$54,$48,$45,$20
	dc.b $52,$41,$54,$00,$00,$03,$17,$A0
	dc.b "WITH THE MAGIC PIPES!!",$FF
	dc.b $00
abs_0_00063BFC:
	dc.b $00,$00,$00,$00,$00,$02,$00,$02,$00,$12,$00,$03,$00,$03,$0D,$20
	dc.b $59,$4F,$55,$20,$52,$55,$42,$20,$54,$48,$45,$20,$4C,$41,$4D,$50
	dc.b $00,$00,$00,$03,$12,$60,$57,$49,$54,$48,$20,$54,$48,$45,$20,$44
	dc.b $55,$53,$54,$45,$52,$21,$FF,$00
abs_0_00063C34:
	dc.b $00,$00,$00,$00,$00,$02,$00,$02,$00,$16,$00,$05,$00,$02,$0D,$20
	dc.b $27,$53,$4F,$52,$52,$59,$20,$4D,$41,$54,$45,$20,$49,$27,$4D,$20
	dc.b $43,$4C,$45,$41,$4E,$00,$00,$04,$12,$60,$4F,$55,$54,$20,$4F,$46
	dc.b $20,$57,$49,$53,$48,$45,$53,$2C,$20,$59,$4F,$55,$00,$00,$00,$03
	dc.b $17,$A0
	dc.b "WEREN'T THE FIRST TO",$00
	dc.b $00,$00,$04,$1C,$E0
	dc.b "FIND ME YOU KNOW!'",$FF
	dc.b $00
abs_0_00063CA4:
	dc.b $00,$00,$00,$00,$00,$02,$00,$02,$00,$12,$00,$04,$00,$03,$0D,$20
	dc.b $27,$48,$4F,$57,$20,$4D,$41,$4E,$59,$20,$54,$49,$4D,$45,$53,$00
	dc.b $00,$02,$12,$60,$44,$4F,$20,$49,$20,$48,$41,$56,$45,$20,$54,$4F
	dc.b $20,$54,$45,$4C,$4C,$00,$00,$03,$17,$A0
	dc.b "YOU? TAKE THAT!'",$FF
	dc.b $00
abs_0_00063CF0:
	dc.b $00,$00,$00,$00,$00,$04,$00,$04,$00,$14,$00,$05,$00,$04,$17,$A0
	dc.b $27,$57,$41,$53,$20,$54,$48,$41,$54,$20,$45,$4E,$4F,$55,$47,$48
	dc.b $20,$54,$4F,$00,$00,$04,$1C,$E0
	dc.b "WAKE YOU UP? LISTEN,",$00
	dc.b $00,$00,$06,$22,$20
	dc.b "I'VE GOT NO MORE",$00
	dc.b $00,$00,$07,$27,$60
	dc.b "WISHES OK????'",$FF
	dc.b $00
abs_0_00063D58:
	dc.b $00,$06,$3D,$70,$00,$02,$00,$02,$00,$09,$00,$02,$00,$03,$0D,$20
	dc.b $27,$4F,$4F,$50,$53,$21,$27,$FF,$00,$00,$00,$00,$00,$04,$00,$04
	dc.b $00,$12,$00,$05,$00,$05,$17,$A0,$27,$59,$49,$4B,$45,$53,$21,$20
	dc.b $54,$48,$41,$54,$20,$57,$41,$53,$00,$00,$00,$04,$1C,$E0
	dc.b "SHOCKING!! I THINK",$00
	dc.b $00,$00,$05,$22,$20
	dc.b "I NEED TO GO TO",$00
	dc.b $00,$05,$27,$60
	dc.b "BED AFTER THAT!'",$FF
	dc.b $00
abs_0_00063DD4:
	dc.b $00,$06,$3E,$32,$00,$03,$00,$03,$00,$19,$00,$04,$00,$03,$12,$60
	dc.b $53,$55,$44,$44,$45,$4E,$4C,$59,$20,$54,$48,$45,$20,$45,$41,$52
	dc.b $54,$48,$20,$53,$48,$41,$4B,$45,$53,$00,$00,$04,$17,$A0
	dc.b "AND ZAKS' FURIOUS VOICE",$00
	dc.b $00,$06,$1C,$E0
	dc.b "BOOMS OVER THE LAND",$FF
	dc.b $00,$00,$00,$00,$00,$05,$00,$05,$00,$19,$00,$05,$00,$05,$1C,$E0
	dc.b $27,$59,$4F,$55,$52,$20,$46,$52,$49,$45,$4E,$44,$53,$20,$4D,$41
	dc.b $59,$20,$42,$45,$20,$46,$52,$45,$45,$00,$00,$06,$22,$20,$4C,$49
	dc.b $54,$54,$4C,$45,$20,$45,$47,$47,$2C,$42,$55,$54,$20,$59,$4F,$55
	dc.b $20,$57,$49,$4C,$4C,$00,$00,$05,$27,$60,$4E,$45,$56,$45,$52,$20
	dc.b $4C,$45,$41,$56,$45,$20,$54,$48,$49,$53,$20,$4C,$41,$4E,$44,$20
	dc.b $41,$53,$00,$00,$00,$06,$2C,$A0
	dc.b "LONG AS I LIVE! HA HA!'",$FF
abs_0_00063EB2:
	dc.b $00,$00,$00,$00,$00,$02,$00,$02,$00,$17,$00,$03,$00,$03,$0D,$20
	dc.b $59,$4F,$55,$20,$44,$52,$49,$56,$45,$20,$54,$48,$45,$20,$54,$52
	dc.b $49,$44,$45,$4E,$54,$00,$00,$02,$12,$60,$44,$45,$45,$50,$20,$49
	dc.b $4E,$54,$4F,$20,$5A,$41,$4B,$53,$27,$20,$48,$45,$41,$52,$54,$21
	dc.b $21,$FF
abs_0_00063EF4:
	dc.b $00,$00,$00,$00,$00,$03,$00,$04,$00,$15,$00,$06,$00,$06,$17,$A0
	dc.b $27,$45,$58,$43,$45,$4C,$4C,$45,$4E,$54,$21,$20,$4E,$4F,$57,$00
	dc.b $00,$07,$1C,$E0
	dc.b "CAST THE RING",$00
	dc.b $00,$04,$22,$20
	dc.b "INTO THE CRACKS OF",$00
	dc.b $00,$00,$04,$27,$60
	dc.b "GEHENNA AND DESTROY",$00
	dc.b $00,$04,$2D
	dc.b "HZAKS SOUL FOREVER!'",$FF
abs_0_00063F6E:
	dc.b $00,$00,$00,$00,$00,$03,$00,$03,$00,$14,$00,$06,$00,$04,$12,$60
	dc.b $59,$4F,$55,$20,$43,$41,$53,$54,$20,$5A,$41,$4B,$53,$20,$52,$49
	dc.b $4E,$47,$00,$00,$00,$05,$17,$A0
	dc.b "INTO THE LAVA! A",$00
	dc.b $00,$00,$04,$1C,$E0
	dc.b "TERRIBLE SCREAMING",$00
	dc.b $00,$00,$05,$22,$20
	dc.b "SOUND MARKS ZAKS",$00
	dc.b $00,$00,$06,$27,$60
	dc.b "FINAL PASSING!",$FF
	dc.b $00
abs_0_00063FEA:
	dc.b $00,$06,$40,$32,$00,$03,$00,$03,$00,$13,$00,$04,$00,$05,$12,$60
	dc.b $27,$46,$52,$45,$45,$20,$41,$54,$20,$4C,$41,$53,$54,$21,$21,$00
	dc.b $00,$04,$17,$A0
	dc.b "FOR ONCE IT SEEMS",$00
	dc.b $00,$06,$1C,$E0
	dc.b "I OWE A DEBT'",$FF
	dc.b $00,$00,$00,$00,$00,$05,$00,$05,$00,$17,$00,$04,$00,$07,$1C,$E0
	dc.b $27,$49,$27,$4C,$4C,$20,$47,$45,$54,$20,$59,$4F,$55,$20,$48,$4F
	dc.b $4D,$45,$2C,$00,$00,$0A,$22,$20,$42,$55,$54,$20,$54,$48,$45,$20
	dc.b $53,$50,$45,$4C,$4C,$00,$00,$05,$27,$60,$52,$45,$51,$55,$49,$52
	dc.b $45,$53,$20,$33,$30,$20,$44,$49,$41,$4D,$4F,$4E,$44,$53,$21,$21
	dc.b $27,$FF
abs_0_00064084:
	dc.b $00,$00,$00,$00,$00,$04,$00,$04,$00,$17,$00,$05,$00,$06,$17,$A0
	dc.b $27,$57,$45,$4C,$4C,$20,$44,$4F,$4E,$45,$21,$20,$49,$20,$53,$48
	dc.b $41,$4C,$4C,$00,$00,$05,$1C,$E0
	dc.b "TRANSPORT YOU TO JOIN",$00
	dc.b $00,$05,$22,$20
	dc.b "YOUR FRIENDS AT HOME!",$00
	dc.b $00,$08,$27,$60
	dc.b "FAREWELL HERO!'",$FF
abs_0_000640F0:
	dc.b $00,$00,$00,$00,$00,$02,$00,$02,$00,$12,$00,$04,$00,$03,$0D,$20
	dc.b $59,$4F,$55,$20,$48,$49,$54,$20,$54,$48,$45,$20,$47,$4F,$41,$54
	dc.b $00,$00,$00,$04,$12,$60,$41,$4E,$44,$20,$49,$54,$20,$43,$48,$41
	dc.b $52,$47,$45,$53,$00,$00,$00,$04,$17,$A0
	dc.b "AT THE TROLL!!",$FF
	dc.b $00
abs_0_0006413A:
	dc.b $00,$00,$00,$00,$00,$02,$00,$02,$00,$10,$00,$03,$00,$03,$0D,$20
	dc.b $54,$48,$45,$20,$47,$4F,$41,$54,$20,$42,$55,$54,$54,$53,$00,$00
	dc.b $00,$05,$12,$60,$54,$48,$45,$20,$54,$52,$4F,$4C,$4C,$21,$FF,$00
abs_0_0006416A:
	dc.b $00,$00,$00,$00,$00,$07,$00,$07,$00,$1A,$00,$06,$00,$08,$2C,$A0
	dc.b "DIZZY RAN OUT OF ENERGY!",$00
	dc.b $00,$00,$0C
	dc.b "7 YOU LOSE A LIFE!",$FF
	dc.b $00
abs_0_000641AA:
	dc.b $00,$00,$00,$00,$00,$03,$00,$03,$00,$14,$00,$03,$00,$04,$12,$60
	dc.b $27,$49,$27,$4C,$4C,$20,$4C,$45,$54,$20,$59,$4F,$55,$20,$50,$41
	dc.b $53,$54,$00,$00,$00,$05,$17,$A0
	dc.b "IF YOU FEED ME!'",$FF
	dc.b $00
abs_0_000641E4:
	dc.b $00,$00,$00,$00,$00,$03,$00,$03,$00,$11,$00,$03,$00,$04,$12,$60
	dc.b $27,$54,$48,$41,$4E,$4B,$20,$59,$4F,$55,$20,$56,$45,$52,$59,$00
	dc.b $00,$05,$17,$A0
	dc.b "MUCH INDEED!'",$FF
abs_0_00064216:
	dcb.b $15,$20
	dc.b $57,$45,$4C,$43,$4F,$4D,$45,$20,$54,$4F,$20,$4D,$41,$47,$49,$43
	dc.b $4C,$41,$4E,$44,$20,$44,$49,$5A,$5A,$59
	dcb.b $15,$20
	dc.b $4F,$52,$49,$47,$49,$4E,$41,$4C,$20,$44,$45,$53,$49,$47,$4E,$20
	dc.b $42,$59,$20,$54,$48,$45,$20,$4F,$4C,$49,$56,$45,$52,$20,$54,$57
	dc.b $49,$4E,$53
	dcb.b $15,$20
	dc.b $41,$4D,$49,$47,$41,$20,$41,$4E,$44,$20,$53,$54,$20,$56,$45,$52
	dc.b $53,$49,$4F,$4E,$53,$20,$50,$52,$4F,$47,$52,$41,$4D,$4D,$45,$44
	dc.b $20,$42,$59,$20,$44,$45,$52,$45,$4B,$20,$4C,$45,$49,$47,$48,$20
	dc.b $47,$49,$4C,$43,$48,$52,$49,$53,$54,$20,$57,$49,$54,$48,$20,$47
	dc.b $52,$41,$50,$48,$49,$43,$53,$20,$42,$59,$20,$4C,$45,$49,$47,$48
	dc.b $20,$43,$48,$52,$49,$53,$54,$49,$41,$4E
	dcb.b $15,$20
	dc.b $FF
abs_0_00064302:
	dcb.b $15,$20
	dc.b $57,$45,$4C,$4C,$20,$44,$4F,$4E,$45,$20,$44,$49,$5A,$5A,$59
	dcb.b $A,$20
	dc.b $59,$4F,$55,$20,$48,$41,$56,$45,$20,$53,$41,$56,$45,$44,$20,$41
	dc.b $4C,$4C,$20,$4F,$46,$20,$59,$4F,$55,$52,$20,$46,$52,$49,$45,$4E
	dc.b $44,$53,$20,$41,$4E,$44,$20,$46,$49,$4E,$49,$53,$48,$45,$44,$20
	dc.b $4F,$46,$46,$20,$54,$48,$45,$20,$45,$56,$49,$4C,$20,$57,$49,$5A
	dc.b $41,$52,$44,$20,$5A,$41,$4B,$53,$20,$46,$4F,$52,$45,$56,$45,$52
	dcb.b $17,$20
	dc.b $FF
abs_0_00064398:
	dc.w $000C,$02A0	; lookup_table
	dc.b "MAGICLAND DIZZY!",$00
	dc.b $00,$00,$05,$15,$00
	dc.b "AMIGA AND ST VERSIONS CODED BY",$00
	dc.b $00,$00,$09,$1C,$E0
	dc.b "DEREK LEIGH-GILCHRIST.",$00
	dc.b $00,$00,$0D,$31,$E0
	dc.b "ALL ARTWORK BY",$00
	dc.b $00,$00,$0C,$39,$C0
	dc.b "LEIGH CHRISTIAN.",$00
	dc.b $00,$00,$00,$76,$20
	dc.b "COPYRIGHT 1991 CODEMASTERS SOFTWARE LTD.",$FF
	dc.b $00
abs_0_00064446:
	dcb.b $3C,$00
abs_0_00064482:
	lea.l _custom.l,a6
	lea.l abs_0_000647D4(pc),a4
	move.l a0,(a4)
	move.l a1,$0004(a4)
	move.b #$3,_ciaa+ciaddra.l
	lea.l _ciab.l,a3
	move.b #$FF,ciaddrb(a3)
	bsr.b abs_0_000644D0
	bsr.w abs_0_000646B2
	move.l #$370,d0
	bsr.w abs_0_000645FC
	movea.l (a4),a0
	lea.l $0200(a0),a1
	moveq.l #127,d7
abs_0_000644BE:
	move.l (a0)+,(a1)+
	dbf.w d7,abs_0_000644BE
	lea.l abs_0_00064504(pc),a0
	move.l a0,m68k_vector_trap_1_instruction_vector.w
	bsr.b abs_0_000644EE
	rts
abs_0_000644D0:
	lea.l ciaprb(a3),a5
	bset.b #6,(a5)
	bset.b #5,(a5)
	bset.b #4,(a5)
	bset.b #3,(a5)
	bclr.b #7,(a5)
	bclr.b #3,(a5)
	rts
abs_0_000644EE:
	lea.l ciaprb(a3),a0
	bset.b #7,(a0)
	bset.b #3,(a0)
	bclr.b #3,(a0)
	bset.b #3,(a0)
	rts
abs_0_00064504:
	lea.l _custom.l,a6
	lea.l abs_0_000647D4(pc),a4
	move.l a7,$0016(a4)
	lea.l _ciab.l,a3
	bsr.b abs_0_000644D0
	move.l a0,$000C(a4)
	move.l a1,$0008(a4)
	movea.l a0,a1
	moveq.l #-1,d7
abs_0_00064526:
	addq.w #1,d7
	tst.b (a1)+
	bne.b abs_0_00064526
	move.w d7,d6
	move.w d7,$0010(a4)
	subq.w #1,d6
abs_0_00064534:
	mulu.w #$D,d7
	moveq.l #0,d0
	move.b (a0)+,d0
	add.w d0,d7
	andi.w #2047,d7
	dbf.w d6,abs_0_00064534
	divu.w #$48,d7
	swap.w d7
	addq.w #6,d7
	movea.l (a4),a0
	lea.l $0200(a0),a0
	add.w d7,d7
	add.w d7,d7
	move.l $0(a0,d7.w),d0
	beq.b abs_0_00064574
abs_0_0006455E:
	bsr.w abs_0_000645FC
	movea.l (a4),a0
	move.w $0010(a4),d0
	cmp.b $01B0(a0),d0
	beq.b abs_0_0006457A
abs_0_0006456E:
	move.l $01F0(a0),d0
	bne.b abs_0_0006455E
abs_0_00064574:
	moveq.l #1,d0
	bra.w abs_0_000645F4
abs_0_0006457A:
	lea.l $01B0(a0),a1
	movea.l $000C(a4),a2
	moveq.l #0,d1
	move.b (a1)+,d1
	subq.w #1,d1
abs_0_00064588:
	moveq.l #0,d3
	move.b (a1)+,d3
	cmp.b #$5A,d3
	ble.b abs_0_00064596
	subi.b #32,d3
abs_0_00064596:
	cmp.b (a2)+,d3
	bne.b abs_0_0006456E
	dbf.w d1,abs_0_00064588
	movea.l $0008(a4),a5
	move.l $0144(a0),d6
	move.l d6,$0012(a4)
	subq.l #1,d6
	move.l $0010(a0),d0
abs_0_000645B0:
	move.l a5,-(a7)
	bsr.b abs_0_000645FC
	movea.l (a7)+,a5
	movea.l (a4),a0
	move.l $000C(a0),d7
	move.l $0010(a0),d0
	lea.l $0018(a0),a0
	move.w d7,d3
	move.w d3,d4
	lsr.w #3,d4
	andi.w #7,d3
	subq.w #1,d4
	bmi.b abs_0_000645DA
abs_0_000645D2:
	move.l (a0)+,(a5)+
	move.l (a0)+,(a5)+
	dbf.w d4,abs_0_000645D2
abs_0_000645DA:
	subq.w #1,d3
	bmi.b abs_0_000645E4
abs_0_000645DE:
	move.b (a0)+,(a5)+
	dbf.w d3,abs_0_000645DE
abs_0_000645E4:
	sub.l d7,d6
	bgt.b abs_0_000645B0
	move.l $0012(a4),d1
	moveq.l #0,d0
abs_0_000645EE:
	bsr.w abs_0_000644EE
	rte
abs_0_000645F4:
	movea.l $0016(a4),a7
	moveq.l #0,d1
	bra.b abs_0_000645EE
abs_0_000645FC:
	move.l d6,-(a7)
	divu.w #$B,d0
	move.l d0,-(a7)
	cmp.w $001A(a4),d0
	beq.b abs_0_00064612
	move.w d0,d6
	bsr.b abs_0_00064620
	bsr.w abs_0_000646E4
abs_0_00064612:
	move.l (a7)+,d0
	swap.w d0
	ext.l d0
	bsr.w abs_0_0006473A
	move.l (a7)+,d6
	rts
abs_0_00064620:
	move.w $001A(a4),d1
	lsr.w #1,d1
	move.w d1,-(a7)
	lea.l ciaprb(a3),a5
	bset.b #2,(a5)
	move.w d6,d0
	lsr.w #1,d0
	bcc.b abs_0_0006463A
	bclr.b #2,(a5)
abs_0_0006463A:
	cmp.w d1,d0
	beq.b abs_0_00064666
	blt.b abs_0_00064648
	bclr.b #1,(a5)
	addq.w #1,d1
	bra.b abs_0_0006464E
abs_0_00064648:
	bset.b #1,(a5)
	subq.w #1,d1
abs_0_0006464E:
	bset.b #0,(a5)
	nop
	nop
	bclr.b #0,(a5)
	nop
	nop
	bset.b #0,(a5)
	bsr.b abs_0_0006468A
	bra.b abs_0_0006463A
abs_0_00064666:
	move.w d6,$001A(a4)
	cmp.w (a7)+,d1
	beq.b abs_0_00064688
abs_0_0006466E:
	move.b #CIACRBF_RUNMODE,ciacrb(a3)
	move.b #CIAICRF_TB,ciaicr(a3)
	move.b #$54,ciatblo(a3)
	move.b #$40,ciatbhi(a3)
	bra.b abs_0_000646A2
abs_0_00064688:
	rts
abs_0_0006468A:
	move.b #CIACRBF_RUNMODE,ciacrb(a3)
	move.b #CIAICRF_TB,ciaicr(a3)
	move.b #$64,ciatblo(a3)
	move.b #$8,ciatbhi(a3)
abs_0_000646A2:
	btst.b #CIAICRB_TB,ciaicr(a3)
	beq.b abs_0_000646A2
	bclr.b #CIACRBB_START,ciacrb(a3)
	rts
abs_0_000646B2:
	lea.l ciaprb(a3),a5
	bset.b #1,(a5)
abs_0_000646BA:
	btst.b #CIAB_DSKTRACK0,_ciaa+ciapra.l
	beq.b abs_0_000646DC
	bset.b #0,(a5)
	nop
	nop
	bclr.b #0,(a5)
	nop
	nop
	bset.b #0,(a5)
	bsr.b abs_0_0006468A
	bra.b abs_0_000646BA
abs_0_000646DC:
	bsr.b abs_0_0006466E
	clr.w $001A(a4)
	rts
abs_0_000646E4:
	move.w #DMAF_SETCLR|DMAF_MASTER|DMAF_DISK,dmacon(a6)
	move.w #ADKF_CLRALL,adkcon(a6)
	move.w #ADKF_SETCLR|ADKF_MFMPREC|ADKF_WORDSYNC|ADKF_FAST,adkcon(a6)
	move.w #$4489,dsksync(a6)	; disk sync word $4489
	move.l $0004(a4),dskpt(a6)	; disk_buffer pointer
	move.w #$4000,dsklen(a6)
abs_0_00064708:
	btst.b #CIAB_DSKRDY,_ciaa+ciapra.l
	bne.b abs_0_00064708
	move.w #$99F0,dsklen(a6)	; disk DMA read 13280 bytes
	move.w #$99F0,dsklen(a6)	; disk DMA read 13280 bytes
	move.w #INTF_DSKBLK,intreq(a6)
abs_0_00064724:
	btst.b #1,$001F(a6)
	beq.b abs_0_00064724
	move.w #INTF_DSKBLK,intreq(a6)
	move.w #$4000,dsklen(a6)
	rts
abs_0_0006473A:
	move.w #$4,$001C(a4)
abs_0_00064740:
	move.w d0,d6
	movea.l (a4),a1
	movea.l $0004(a4),a0
	lsl.w #8,d6
	move.l #$55555555,d7
	move.w #$4489,d4
	move.w #$F00,d5
	moveq.l #10,d3
abs_0_0006475A:
	cmp.w (a0)+,d4
	bne.b abs_0_0006475A
	cmp.w (a0),d4
	bne.b abs_0_00064764
	addq.w #2,a0
abs_0_00064764:
	move.l (a0)+,d1
	move.l (a0)+,d2
	and.w d7,d1
	and.w d7,d2
	add.w d1,d1
	or.w d2,d1
	and.w d5,d1
	cmp.w d1,d6
	beq.b abs_0_00064780
	lea.l $0400(a0),a0
	dbf.w d3,abs_0_0006475A
	bra.b abs_0_000647C2
abs_0_00064780:
	lea.l $0030(a0),a0
	lea.l $0200(a0),a2
	moveq.l #63,d1
	moveq.l #0,d6
abs_0_0006478C:
	movem.l (a2)+,d2-d3
	movem.l (a0)+,d4-d5
	eor.l d4,d6
	eor.l d5,d6
	eor.l d2,d6
	eor.l d3,d6
	and.l d7,d2
	and.l d7,d4
	add.l d4,d4
	or.l d4,d2
	and.l d7,d3
	and.l d7,d5
	add.l d5,d5
	or.l d5,d3
	move.l d2,(a1)+
	move.l d3,(a1)+
	dbf.w d1,abs_0_0006478C
	move.l -$0204(a0),d1
	and.l d7,d1
	and.l d7,d6
	cmp.l d1,d6
	bne.b abs_0_000647C2
	rts
abs_0_000647C2:
	bsr.w abs_0_000646E4
	subq.w #1,$001C(a4)
	bge.w abs_0_00064740
	moveq.l #2,d0
	bra.w abs_0_000645F4
abs_0_000647D4:
	dcb.b $1E,$00
abs_0_000647F2:
	move.l d0,d1
	movea.l a0,a1
	movea.l a0,a2
	move.l $0004(a1),d7
	lea.l $0008(a1),a1
	move.w d1,d2
	lsr.l #4,d1
	subq.w #1,d1
	bmi.b abs_0_00064814
abs_0_00064808:
	move.l (a1)+,(a2)+
	move.l (a1)+,(a2)+
	move.l (a1)+,(a2)+
	move.l (a1)+,(a2)+
	dbf.w d1,abs_0_00064808
abs_0_00064814:
	andi.w #15,d2
	subq.w #1,d2
	bmi.b abs_0_00064822
abs_0_0006481C:
	move.b (a1)+,(a2)+
	dbf.w d2,abs_0_0006481C
abs_0_00064822:
	subq.l #8,d0
	adda.l d0,a0
	lea.l abs_0_000648C2(pc),a5
	move.l d7,(a5)
	moveq.l #1,d4
	moveq.l #1,d5
	moveq.l #3,d6
	moveq.l #7,d7
	movea.l a3,a2
	move.l -(a0),d1
	tst.b d1
	beq.b abs_0_00064842
	bsr.b abs_0_00064866
	sub.l d4,d1
	lsr.l d1,d5
abs_0_00064842:
	lsr.l #8,d1
	adda.l d1,a3
abs_0_00064846:
	bsr.b abs_0_00064866
	bcs.b abs_0_00064888
	moveq.l #0,d2
abs_0_0006484C:
	move.w d4,d0
	bsr.b abs_0_00064874
	add.w d1,d2
	cmp.w d6,d1
	beq.b abs_0_0006484C
abs_0_00064856:
	moveq.l #7,d0
	bsr.b abs_0_00064874
	move.b d1,-(a3)
	dbf.w d2,abs_0_00064856
	cmpa.l a3,a2
	bcs.b abs_0_00064888
	rts
abs_0_00064866:
	lsr.l d4,d5
	beq.b abs_0_0006486C
	rts
abs_0_0006486C:
	move.l -(a0),d5
	roxr.l d4,d5
	rts
abs_0_00064872:
	sub.w d4,d0
abs_0_00064874:
	moveq.l #0,d1
abs_0_00064876:
	lsr.l d4,d5
	beq.b abs_0_00064882
abs_0_0006487A:
	roxl.l d4,d1
	dbf.w d0,abs_0_00064876
	rts
abs_0_00064882:
	move.l -(a0),d5
	roxr.l d4,d5
	bra.b abs_0_0006487A
abs_0_00064888:
	move.w d4,d0
	bsr.b abs_0_00064874
	moveq.l #0,d0
	move.b $0(a5,d1.w),d0
	move.w d1,d2
	cmp.w d6,d2
	bne.b abs_0_000648AE
	bsr.b abs_0_00064866
	bcs.b abs_0_0006489E
	moveq.l #7,d0
abs_0_0006489E:
	bsr.b abs_0_00064872
	move.w d1,d3
abs_0_000648A2:
	moveq.l #2,d0
	bsr.b abs_0_00064874
	add.w d1,d2
	cmp.w d7,d1
	beq.b abs_0_000648A2
	bra.b abs_0_000648B2
abs_0_000648AE:
	bsr.b abs_0_00064872
	move.w d1,d3
abs_0_000648B2:
	add.w d4,d2
abs_0_000648B4:
	move.b $0(a3,d3.w),-(a3)
	dbf.w d2,abs_0_000648B4
	cmpa.l a3,a2
	bcs.b abs_0_00064846
	rts
abs_0_000648C2:
	dc.b $09,$0A,$0C,$0D
abs_0_000648C6:
	dc.b $22,$17,$20,$37,$18,$36,$22,$21,$40,$20,$36,$22,$40,$19,$12,$20
	dc.b $13,$28,$21,$FF
abs_0_000648DA:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$09,$00,$0A,$00,$0B,$00,$0C
	dc.b $00,$0D,$00,$0E,$00,$0F,$00,$10,$FF,$FF
abs_0_000648F4:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$11,$00,$12,$00,$13,$00,$14
	dc.b $00,$15,$00,$16,$00,$17,$00,$18,$FF,$FF
abs_0_0006490E:
	dc.b $00,$06
	dcb.b $9,$00
	dc.b $01,$FF,$FF
abs_0_0006491C:
	dc.b $00,$02,$00,$00,$00,$00,$00,$00,$00,$19,$00,$1A,$00,$1B,$00,$1C
	dc.b $00,$1D,$00,$1E,$00,$1F,$00,$09,$FF,$FF
abs_0_00064936:
	dc.b $00,$02,$00,$00,$00,$00,$00,$00,$00,$20,$00,$21,$00,$22,$00,$23
	dc.b $00,$24,$00,$25,$00,$26,$00,$11,$FF,$FF
abs_0_00064950:
	dc.b $00,$02,$00,$00,$00,$00,$00,$00,$00,$02,$00,$03,$00,$04,$00,$05
	dc.b $00,$06,$00,$07,$00,$08,$00,$01,$FF,$FF
abs_0_0006496A:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$2B,$00,$2C,$00,$2D,$00,$2E
	dc.b $FF,$FF
abs_0_0006497C:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$33,$00,$2C,$00,$34,$00,$2E
	dc.b $FF,$FF
abs_0_0006498E:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$30,$00,$28,$00,$31,$00,$2A
	dc.b $FF,$FF
abs_0_000649A0:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$2B,$00,$2C,$00,$2D,$00,$2E
	dc.b $FF,$FF
abs_0_000649B2:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$27,$00,$28,$00,$29,$00,$2A
	dc.b $FF,$FF
abs_0_000649C4:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$2B,$00,$2C,$00,$2D,$00,$2E
	dc.b $FF,$FF
abs_0_000649D6:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$27,$00,$28,$00,$29,$00,$2A
	dc.b $FF,$FF
abs_0_000649E8:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$33,$00,$2C,$00,$34,$00,$2E
	dc.b $FF,$FF
abs_0_000649FA:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$30,$00,$28,$00,$31,$00,$2A
	dc.b $FF,$FF
abs_0_00064A0C:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$33,$00,$2C,$00,$34,$00,$2E
	dc.b $FF,$FF
abs_0_00064A1E:
	dc.b $00,$03,$00,$00,$00,$00,$00,$00,$00,$30,$00,$28,$00,$31,$00,$2A
	dc.b $FF,$FF
abs_0_00064A30:
	dc.b $00,$05,$00,$00,$00,$00,$00,$00,$00,$35,$00,$36,$00,$37,$00,$38
	dc.b $00,$39,$00,$39,$00,$39,$00,$39,$FF,$FF
abs_0_00064A4A:
	dc.b $00,$05,$00,$00,$00,$00,$00,$00,$00,$3A,$00,$3B,$00,$3C,$00,$3D
	dc.b $00,$3E,$00,$3E,$00,$3E,$00,$3E,$FF,$FF
abs_0_00064A64:
	dc.b $00,$05,$00,$00,$00,$00,$00,$00,$00,$3F,$00,$40,$00,$41,$00,$42
	dc.b $00,$43,$00,$43,$00,$43,$00,$43,$FF,$FF
abs_0_00064A7E:
	dc.b $00,$0A,$00,$00,$00,$00,$00,$00,$00,$47,$00,$47,$00,$48,$00,$49
	dc.b $00,$49,$00,$49,$00,$48,$FF,$FF
abs_0_00064A96:
	dc.b $00,$09,$00,$00,$00,$00,$00,$00,$00,$4A,$00,$4A,$00,$4A,$00,$4A
	dc.b $00,$4A,$00,$4A,$00,$4A,$00,$4A,$00,$4E,$FF,$FF
abs_0_00064AB2:
	dc.b $00,$0C,$00,$00,$00,$00,$00,$00,$00,$4B,$00,$4B,$00,$4B,$00,$4B
	dc.b $00,$4B,$00,$4B,$00,$4B,$00,$4B,$00,$4E,$FF,$FF
abs_0_00064ACE:
	dc.b $00,$05,$00,$00,$00,$00,$00,$00,$00,$4C,$00,$4D,$FF,$FF
abs_0_00064ADC:
	dc.b $00,$07,$00,$00,$00,$00,$00,$00,$00,$54,$00,$55,$00,$56,$00,$57
	dc.b $FF,$FF
abs_0_00064AEE:
	dc.b $00,$07,$00,$00,$00,$00,$00,$00,$00,$85,$00,$86,$00,$87,$00,$57
	dc.b $FF,$FF
abs_0_00064B00:
	dc.b $00,$07,$00,$00,$00,$00,$00,$00,$00,$05,$00,$06,$FF,$FF
abs_0_00064B0E:
	dc.b $00,$08,$00,$00,$00,$00,$00,$00,$00,$66,$00,$64,$00,$65,$00,$64
	dc.b $FF,$FF
abs_0_00064B20:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$88,$00,$89,$00,$8A,$00,$8B
	dc.b $00,$8C,$00,$8D,$00,$8E,$00,$8F,$00,$90,$00,$91,$FF,$FF
abs_0_00064B3E:
	dc.b $00,$0D,$00,$00,$00,$00,$00,$00,$00,$9A,$00,$9B,$00,$9C,$00,$9D
	dc.b $FF,$FF
abs_0_00064B50:
	dc.b $00,$0D,$00,$00,$00,$00,$00,$00,$00,$9E,$00,$9F,$FF,$FF
abs_0_00064B5E:
	dc.b $00,$11,$00,$00,$00,$00,$00,$00,$00,$A4,$00,$A3,$00,$A4,$00,$A3
	dc.b $00,$A4,$00,$A3,$00,$A5,$00,$A3,$FF,$FF
abs_0_00064B78:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$AE,$00,$AF,$00,$B0,$FF,$FF
abs_0_00064B88:
	dc.b $00,$04,$00,$00,$00,$00,$00,$00,$00,$B1,$00,$B2,$00,$B3,$FF,$FF
abs_0_00064B98:
	dc.b $00,$08,$00,$00,$00,$00,$00,$00,$00,$B8,$00,$B9,$00,$BA,$00,$BB
	dc.b $FF,$FF
abs_0_00064BAA:
	dc.b $00,$05,$00,$00,$00,$00,$00,$00,$00,$CB,$00,$CC,$00,$CD,$FF,$FF
abs_0_00064BBA:
	dc.b $00,$0C,$00,$00,$00,$00,$00,$00,$00,$D3,$00,$D3,$00,$D3,$00,$D3
	dc.b $00,$D3,$00,$D3,$00,$D3,$00,$D3,$00,$D3,$00,$D3,$00,$D4,$00,$D5
	dc.b $00,$D6,$FF,$FF
abs_0_00064BDE:
	dc.b $00,$10,$00,$00,$00,$00,$00,$04,$00,$DD,$00,$DE,$00,$DF,$00,$DF
	dc.b $00,$DC,$FF,$FF
abs_0_00064BF2:
	dc.b $00,$10,$00,$00,$00,$00,$00,$05,$00,$DD,$00,$E0,$00,$E1,$00,$E2
	dc.b $00,$E2,$00,$DC,$FF,$FF
abs_0_00064C08:
	dc.b $00,$10,$00,$00,$00,$00,$00,$04,$00,$DD,$00,$DE,$00,$DF,$00,$DF
	dc.b $00,$DC,$FF,$FF
abs_0_00064C1C:
	dc.b $00,$10,$00,$00,$00,$00,$00,$05,$00,$DD,$00,$E0,$00,$E1,$00,$E2
	dc.b $00,$E2,$00,$DC,$FF,$FF
abs_0_00064C32:
	dc.b $00,$07,$00,$00,$00,$00,$00,$00,$00,$E6,$00,$E7,$00,$E8,$00,$E9
	dc.b $00,$EA,$00,$E9,$00,$E8,$00,$E7,$FF,$FF
abs_0_00064C4C:
	dc.b $00,$0A,$00,$00,$00,$00,$00,$00,$00,$E4,$00,$ED,$FF,$FF
abs_0_00064C5A:
	dc.b $00,$04,$00,$00,$00,$00,$00,$0B,$00,$EE,$00,$EF,$00,$F0,$00,$F0
	dc.b $00,$F0,$00,$F1,$00,$F1,$00,$F1,$00,$F2,$00,$F2,$00,$F3,$00,$EE
	dc.b $FF,$FF
abs_0_00064C7C:
	dc.b $00,$08,$00,$00,$00,$00,$00,$00,$00,$BC,$00,$BD,$00,$BE,$FF,$FF
abs_0_00064C8C:
	dc.b $00,$08,$00,$00,$00,$00,$00,$00,$00,$BF,$00,$C0,$00,$C1,$FF,$FF
abs_0_00064C9C:
	dc.b $00,$07,$00,$00,$00,$00,$00,$00,$00,$F5,$00,$F4,$FF,$FF
abs_0_00064CAA:
	dc.b $00,$07,$00,$00,$00,$00,$00,$00,$00,$F6,$00,$DA,$FF,$FF
abs_0_00064CB8:
	dc.b $00,$09,$00,$00,$00,$00,$00,$00,$00,$D8,$00,$D9,$FF,$FF
abs_0_00064CC6:
	dc.b $00,$06
	dcb.b $9,$00
	dc.b $01,$FF,$FF,$44,$45,$4C,$21
abs_0_00064CD8:
	dc.b $00,$00,$00,$00,$00,$02,$00,$16,$00,$04,$00,$00,$00,$02,$00,$16
	dc.b $00,$08,$00,$00,$00,$02,$00,$16,$00,$0C,$00,$00,$00,$02,$00,$16
	dc.b $00,$10,$00,$00,$00,$02,$00,$16,$00,$14,$00,$00,$00,$02,$00,$16
	dc.b $00,$18,$00,$00,$00,$02,$00,$16,$00,$1C,$00,$00,$00,$02,$00,$16
	dc.b $00,$20,$00,$00,$00,$02,$00,$16,$00,$24,$00,$00,$00,$02,$00,$16
	dc.b $00,$00,$00,$16,$00,$02,$00,$16,$00,$04,$00,$16,$00,$02,$00,$16
	dc.b $00,$08,$00,$16,$00,$02,$00,$16,$00,$0C,$00,$16,$00,$02,$00,$16
	dc.b $00,$10,$00,$16,$00,$02,$00,$16,$00,$14,$00,$16,$00,$02,$00,$16
	dc.b $00,$18,$00,$16,$00,$02,$00,$16,$00,$1C,$00,$16,$00,$02,$00,$16
	dc.b $00,$20,$00,$16,$00,$02,$00,$16,$00,$24,$00,$16,$00,$02,$00,$16
	dc.b $00,$00,$00,$2C,$00,$02,$00,$16,$00,$04,$00,$2C,$00,$02,$00,$16
	dc.b $00,$08,$00,$2C,$00,$02,$00,$16,$00,$0C,$00,$2C,$00,$02,$00,$16
	dc.b $00,$10,$00,$2C,$00,$02,$00,$16,$00,$14,$00,$2C,$00,$02,$00,$16
	dc.b $00,$18,$00,$2C,$00,$02,$00,$16,$00,$1C,$00,$2C,$00,$02,$00,$16
	dc.b $00,$20,$00,$2C,$00,$02,$00,$16,$00,$24,$00,$2C,$00,$02,$00,$16
	dc.b $00,$00,$00,$42,$00,$02,$00,$16,$00,$04,$00,$42,$00,$02,$00,$16
	dc.b $00,$08,$00,$42,$00,$02,$00,$16,$00,$0C,$00,$42,$00,$02,$00,$16
	dc.b $00,$10,$00,$42,$00,$02,$00,$16,$00,$14,$00,$42,$00,$02,$00,$16
	dc.b $00,$18,$00,$42,$00,$02,$00,$16,$00,$1C,$00,$42,$00,$02,$00,$16
	dc.b $00,$20,$00,$42,$00,$02,$00,$16,$00,$00,$00,$60,$00,$03,$00,$2B
	dc.b $00,$06,$00,$60,$00,$03,$00,$2B,$00,$0C,$00,$60,$00,$03,$00,$2B
	dc.b $00,$12,$00,$60,$00,$03,$00,$2B,$00,$00,$00,$8B,$00,$03,$00,$2B
	dc.b $00,$06,$00,$8B,$00,$03,$00,$2B,$00,$0C,$00,$8B,$00,$03,$00,$2B
	dc.b $00,$12,$00,$8B,$00,$03,$00,$2B,$00,$18,$00,$60,$00,$03,$00,$2B
	dc.b $00,$00,$00,$B6,$00,$03,$00,$2B,$00,$06,$00,$B6,$00,$03,$00,$2B
	dc.b $00,$0C,$00,$B6,$00,$03,$00,$2B,$00,$12,$00,$B6,$00,$03,$00,$2B
	dc.b $00,$18,$00,$B6,$00,$03,$00,$2B,$00,$00,$00,$F0,$00,$01,$00,$10
	dc.b $00,$02,$00,$F0,$00,$01,$00,$10,$00,$04,$00,$F0,$00,$01,$00,$10
	dc.b $00,$06,$00,$F0,$00,$01,$00,$10,$00,$08,$00,$F0,$00,$01,$00,$10
	dc.b $00,$0A,$00,$F0,$00,$01,$00,$10,$00,$0C,$00,$F0,$00,$01,$00,$10
	dc.b $00,$0E,$00,$F0,$00,$01,$00,$10,$00,$10,$00,$F0,$00,$01,$00,$10
	dc.b $00,$12,$00,$F0,$00,$01,$00,$10,$00,$14,$00,$F0,$00,$01,$00,$10
	dc.b $00,$16,$00,$F0,$00,$01,$00,$10,$00,$18,$00,$F0,$00,$01,$00,$10
	dc.b $00,$1A,$00,$F0,$00,$01,$00,$10,$00,$1C,$00,$F0,$00,$01,$00,$10
	dc.b $00,$18,$00,$90,$00,$01,$00,$07,$00,$1A,$00,$90,$00,$01,$00,$08
	dc.b $00,$1C,$00,$90,$00,$01,$00,$09,$00,$20,$00,$60,$00,$02,$00,$0F
	dc.b $00,$20,$00,$70,$00,$02,$00,$0F,$00,$20,$00,$80,$00,$02,$00,$0F
	dc.b $00,$20,$00,$90,$00,$02,$00,$1A,$00,$24,$00,$90,$00,$02,$00,$1A
	dc.b $00,$24,$00,$50,$00,$02,$00,$1A,$00,$24,$00,$70,$00,$02,$00,$1A
	dc.b $00,$20,$00,$E0,$00,$02,$00,$1A,$00,$1E,$00,$90,$00,$01,$00,$09
	dc.b $00,$1E,$00,$80,$00,$01,$00,$08,$00,$1E,$00,$70,$00,$01,$00,$07
	dc.b $00,$1E,$00,$60,$00,$01,$00,$06,$00,$18,$00,$A0,$00,$02,$00,$08
	dc.b $00,$20,$00,$AF,$00,$02,$00,$19,$00,$24,$00,$AF,$00,$02,$00,$19
	dc.b $00,$20,$00,$C8,$00,$02,$00,$19,$00,$1E,$00,$A0,$00,$01,$00,$0F
	dc.b $00,$1E,$00,$B0,$00,$01,$00,$0F,$00,$1E,$00,$C0,$00,$01,$00,$0F
	dc.b $00,$1E,$00,$D0,$00,$01,$00,$0F,$00,$1E,$00,$E0,$00,$01,$00,$0F
	dc.b $00,$1E,$00,$F0,$00,$01,$00,$0F,$00,$00,$00,$E1,$00,$01,$00,$0F
	dc.b $00,$02,$00,$E1,$00,$01,$00,$0F,$00,$04,$00,$E1,$00,$01,$00,$0F
	dc.b $00,$06,$00,$E1,$00,$01,$00,$0F,$00,$08,$00,$E1,$00,$01,$00,$0F
	dc.b $00,$0A,$00,$E1,$00,$01,$00,$0F,$FF,$FF,$00,$08,$00,$20,$00,$02
	dc.b $00,$10,$00,$22,$00,$0C,$00,$03,$00,$34,$00,$1C,$00,$8C,$00,$03
	dc.b $00,$34,$00,$1C,$00,$0C,$00,$03,$00,$34,$00,$08,$00,$50,$00,$01
	dc.b $00,$10,$00,$0A,$00,$50,$00,$01,$00,$10,$00,$0C,$00,$50,$00,$01
	dc.b $00,$10,$00,$0E,$00,$50,$00,$01,$00,$10,$00,$10,$00,$50,$00,$01
	dc.b $00,$10,$00,$12,$00,$50,$00,$01,$00,$10,$00,$14,$00,$50,$00,$01
	dc.b $00,$10,$00,$16,$00,$50,$00,$01,$00,$10,$00,$18,$00,$50,$00,$01
	dc.b $00,$10,$00,$1A,$00,$50,$00,$01,$00,$10,$00,$1C,$00,$50,$00,$01
	dc.b $00,$10,$00,$1E,$00,$50,$00,$01,$00,$10,$00,$20,$00,$50,$00,$01
	dc.b $00,$10,$00,$22,$00,$50,$00,$01,$00,$10,$00,$0A,$00,$60,$00,$01
	dc.b $00,$10,$00,$0C,$00,$60,$00,$01,$00,$10,$00,$0E,$00,$60,$00,$01
	dc.b $00,$10,$00,$10,$00,$60,$00,$01,$00,$10,$00,$12,$00,$60,$00,$01
	dc.b $00,$10,$00,$14,$00,$60,$00,$01,$00,$10,$00,$16,$00,$60,$00,$01
	dc.b $00,$10,$00,$18,$00,$60,$00,$01,$00,$10,$00,$1A,$00,$60,$00,$01
	dc.b $00,$10,$00,$1C,$00,$60,$00,$01,$00,$10,$00,$1E,$00,$60,$00,$01
	dc.b $00,$10,$00,$20,$00,$60,$00,$01,$00,$10,$00,$0C,$00,$00,$00,$02
	dc.b $00,$30,$00,$00,$00,$20,$00,$02,$00,$30,$00,$06,$00,$24,$00,$01
	dc.b $00,$05,$00,$10,$00,$84,$00,$03,$00,$3C,$00,$22,$00,$90,$00,$02
	dc.b $00,$19,$00,$22,$00,$A9,$00,$02,$00,$19,$00,$22,$00,$C2,$00,$02
	dc.b $00,$19,$00,$24,$00,$40,$00,$01,$00,$10,$00,$24,$00,$50,$00,$01
	dc.b $00,$10,$00,$24,$00,$60,$00,$01,$00,$10,$00,$24,$00,$70,$00,$01
	dc.b $00,$10,$00,$24,$00,$80,$00,$01,$00,$10,$00,$26,$00,$40,$00,$01
	dc.b $00,$10,$00,$26,$00,$50,$00,$01,$00,$10,$00,$26,$00,$60,$00,$01
	dc.b $00,$10,$00,$26,$00,$70,$00,$01,$00,$10,$00,$26,$00,$80,$00,$01
	dc.b $00,$10,$00,$26,$00,$90,$00,$01,$00,$30,$00,$22,$00,$80,$00,$01
	dc.b $00,$10,$00,$04,$00,$20,$00,$01,$00,$04,$00,$08,$00,$09,$00,$02
	dc.b $00,$17,$00,$04,$00,$09,$00,$02,$00,$17,$00,$00,$00,$80,$00,$04
	dc.b $00,$3D,$00,$06,$00,$20,$00,$01,$00,$04,$00,$08,$00,$80,$00,$01
	dc.b $00,$30,$00,$1A,$00,$00,$00,$01,$00,$30,$00,$18,$00,$00,$00,$01
	dc.b $00,$30,$00,$0A,$00,$80,$00,$01,$00,$30,$00,$04,$00,$24,$00,$01
	dc.b $00,$06,$00,$10,$00,$00,$00,$02,$00,$17,$00,$14,$00,$00,$00,$02
	dc.b $00,$17,$00,$00,$00,$00,$00,$02,$00,$09,$00,$00,$00,$09,$00,$01
	dc.b $00,$07,$00,$1A,$00,$70,$00,$01,$00,$22,$00,$04,$00,$30,$00,$02
	dc.b $00,$16,$00,$04,$00,$46,$00,$02,$00,$16,$00,$04,$00,$5C,$00,$02
	dc.b $00,$16,$00,$10,$00,$20,$00,$01,$00,$04,$00,$12,$00,$20,$00,$01
	dc.b $00,$05,$00,$14,$00,$20,$00,$01,$00,$06,$00,$16,$00,$20,$00,$01
	dc.b $00,$07,$00,$0C,$00,$80,$00,$02,$00,$3C,$00,$18,$00,$70,$00,$01
	dc.b $00,$10,$00,$00,$00,$10,$00,$02,$00,$10,$00,$16,$00,$92,$00,$03
	dc.b $00,$22,$00,$16,$00,$80,$00,$01,$00,$0F,$00,$18,$00,$80,$00,$01
	dc.b $00,$0F,$00,$1C,$00,$70,$00,$01,$00,$0F,$00,$1E,$00,$70,$00,$01
	dc.b $00,$0F,$00,$20,$00,$70,$00,$01,$00,$0F,$00,$22,$00,$70,$00,$01
	dc.b $00,$0F,$00,$08,$00,$30,$00,$01,$00,$06,$00,$0A,$00,$30,$00,$01
	dc.b $00,$06,$00,$0C,$00,$30,$00,$01,$00,$06,$00,$0E,$00,$30,$00,$01
	dc.b $00,$06,$00,$00,$00,$C0,$00,$04,$00,$3D,$00,$08,$00,$C0,$00,$04
	dc.b $00,$3D,$00,$10,$00,$C0,$00,$04,$00,$3D,$00,$18,$00,$C0,$00,$04
	dc.b $00,$3D,$00,$10,$00,$30,$00,$01,$00,$0E,$00,$12,$00,$30,$00,$01
	dc.b $00,$0D,$00,$14,$00,$30,$00,$01,$00,$10,$00,$16,$00,$30,$00,$01
	dc.b $00,$0E,$00,$18,$00,$30,$00,$01,$00,$0D,$00,$1A,$00,$30,$00,$01
	dc.b $00,$10,$00,$1E,$00,$42,$00,$01,$00,$0E,$00,$20,$00,$42,$00,$01
	dc.b $00,$0E,$00,$10,$00,$40,$00,$01,$00,$05,$00,$12,$00,$40,$00,$01
	dc.b $00,$07,$00,$14,$00,$40,$00,$01,$00,$09,$00,$16,$00,$40,$00,$01
	dc.b $00,$0B,$00,$18,$00,$40,$00,$01,$00,$0D,$00,$1A,$00,$40,$00,$01
	dc.b $00,$10,$00,$1C,$00,$40,$00,$01,$00,$0B,$00,$20,$00,$E0,$00,$02
	dc.b $00,$0A,$00,$20,$00,$EA,$00,$02,$00,$0A,$00,$20,$00,$F4,$00,$02
	dc.b $00,$0A,$00,$22,$00,$60,$00,$01,$00,$10,$00,$08,$00,$40,$00,$01
	dc.b $00,$10,$00,$0A,$00,$40,$00,$01,$00,$10,$00,$0C,$00,$40,$00,$01
	dc.b $00,$10,$00,$0E,$00,$40,$00,$01,$00,$10,$FF,$FF,$00,$06,$00,$00
	dc.b $00,$03,$00,$30,$00,$06,$00,$30,$00,$03,$00,$30,$00,$06,$00,$60
	dc.b $00,$03,$00,$30,$00,$06,$00,$90,$00,$03,$00,$30,$00,$0C,$00,$3B
	dc.b $00,$03,$00,$2D,$00,$1C,$00,$00,$00,$02,$00,$17,$00,$20,$00,$00
	dc.b $00,$02,$00,$17,$00,$20,$00,$2F,$00,$02,$00,$16,$00,$0C,$00,$00
	dc.b $00,$02,$00,$24,$00,$16,$00,$00,$00,$03,$00,$20,$00,$16,$00,$20
	dc.b $00,$03,$00,$20,$00,$16,$00,$40,$00,$03,$00,$20,$00,$16,$00,$60
	dc.b $00,$03,$00,$20,$00,$16,$00,$80,$00,$03,$00,$20,$00,$16,$00,$A0
	dc.b $00,$03,$00,$20,$00,$14,$00,$C0,$00,$04,$00,$20,$00,$10,$00,$00
	dc.b $00,$01,$00,$07,$00,$00,$00,$00,$00,$03,$00,$37,$00,$10,$00,$A0
	dc.b $00,$03,$00,$12,$00,$1C,$00,$50,$00,$01,$00,$16,$00,$1E,$00,$50
	dc.b $00,$01,$00,$16,$00,$20,$00,$50,$00,$01,$00,$16,$00,$22,$00,$50
	dc.b $00,$01,$00,$16,$00,$24,$00,$50,$00,$01,$00,$16,$00,$00,$00,$9D
	dc.b $00,$03,$00,$3D,$00,$12,$00,$00,$00,$01,$00,$07,$00,$00,$00,$37
	dc.b $00,$03,$00,$37,$00,$12,$00,$10,$00,$02,$00,$20,$00,$12,$00,$30
	dc.b $00,$02,$00,$20,$00,$12,$00,$50,$00,$02,$00,$20,$00,$0C,$00,$A0
	dc.b $00,$02,$00,$20,$00,$0A,$00,$C0,$00,$03,$00,$20,$00,$0A,$00,$E0
	dc.b $00,$03,$00,$20,$00,$1C,$00,$18,$00,$02,$00,$17,$00,$20,$00,$18
	dc.b $00,$02,$00,$17,$00,$1C,$00,$2F,$00,$02,$00,$16,$00,$10,$00,$E0
	dc.b $00,$07,$00,$10,$00,$1C,$00,$70,$00,$01,$00,$10,$00,$1E,$00,$70
	dc.b $00,$01,$00,$10,$00,$20,$00,$70,$00,$01,$00,$10,$00,$22,$00,$70
	dc.b $00,$01,$00,$10,$00,$24,$00,$70,$00,$01,$00,$10,$00,$26,$00,$70
	dc.b $00,$01,$00,$10,$00,$1C,$00,$80,$00,$01,$00,$10,$00,$1E,$00,$80
	dc.b $00,$01,$00,$10,$00,$20,$00,$80,$00,$01,$00,$10,$00,$22,$00,$80
	dc.b $00,$01,$00,$10,$00,$24,$00,$80,$00,$01,$00,$10,$00,$26,$00,$80
	dc.b $00,$01,$00,$10,$00,$1C,$00,$90,$00,$01,$00,$10,$00,$1E,$00,$90
	dc.b $00,$01,$00,$10,$00,$20,$00,$90,$00,$01,$00,$10,$00,$22,$00,$90
	dc.b $00,$01,$00,$10,$00,$24,$00,$90,$00,$01,$00,$10,$00,$26,$00,$90
	dc.b $00,$01,$00,$10,$00,$1C,$00,$A0,$00,$01,$00,$10,$00,$1E,$00,$A0
	dc.b $00,$01,$00,$10,$00,$20,$00,$A0,$00,$01,$00,$10,$00,$22,$00,$A0
	dc.b $00,$01,$00,$10,$00,$24,$00,$A0,$00,$01,$00,$10,$00,$26,$00,$A0
	dc.b $00,$01,$00,$10,$00,$1C,$00,$B0,$00,$01,$00,$10,$00,$1E,$00,$B0
	dc.b $00,$01,$00,$10,$FF,$FF
abs_0_0006556E:
	dc.l $00000093,$0015FFFE,$00000001,$00200082	; lookup_table
	dc.l $FFFF0001,$00040050,$0085FFFD,$00020007	; lookup_table
	dc.l $00700030,$FFFF0003,$00080070,$00AAFFFF	; lookup_table
	dc.l $00040009,$0122002A,$FFFF0005,$0010005A	; lookup_table
	dc.l $0076FFFD,$00060012,$01280050,$FFFD0007	; lookup_table
	dc.l $00130098,$0090FFFE,$00080016,$00A60070	; lookup_table
	dc.l $FFFD0009,$00060046,$0048FFFD,$000A0020	; lookup_table
	dc.l $00480018,$FFFD000B,$000A0119,$0021FFFF	; lookup_table
	dc.l $000C000D,$00290091,$FFFF000D,$000E0012	; lookup_table
	dc.l $0067FFFD,$000E0017,$00240070,$FFFF000F	; lookup_table
	dc.l $001A007A,$0090FFFD,$0010001B,$002D0090	; lookup_table
	dc.l $FFFF0011,$001C0016,$0060FFFD,$0012001F	; lookup_table
	dc.l $00C60070,$FFFD0013,$002200C8,$009FFFFD	; lookup_table
	dc.l $00140024,$00080090,$FFFD0015,$002800C8	; lookup_table
	dc.l $0076FFFF,$00160029,$003000A0,$FFFF0017	; lookup_table
	dc.l $002A004C,$0010FFFD,$0018002B,$00DD0087	; lookup_table
	dc.l $FFFD0019,$002D0101,$00A0FFFF,$001A0030	; lookup_table
	dc.l $00E80090,$FFFD001B,$00320069,$007FFFFF	; lookup_table
	dc.l $001C0034,$00940040,$FFFD001D,$000400A8	; lookup_table
	dc.l $0050006E,$001E0000,$00AA0015,$006B001F	; lookup_table
	dc.l $000600C0,$00300071,$0020000C,$00C50076	; lookup_table
	dc.l $006C0021,$00190094,$00940075,$00220008	; lookup_table
	dc.l $01240079,$006A0023,$00200082,$00820072	; lookup_table
	dc.l $0024FFFF,$00C200A0,$007C0025,$FFFF00A0	; lookup_table
	dc.l $00820077,$0026FFFF,$00080070,$006F0027	; lookup_table
	dc.l $FFFF00B4,$00400080,$0028000A,$00500078	; lookup_table
	dc.l $00700029,$00010104,$0084006D,$002A0021	; lookup_table
	dc.l $00EE00A0,$0074002B,$00270090,$00200069	; lookup_table
	dc.l $002CFFFF,$00000000,$0069002D,$00250058	; lookup_table
	dc.l $00700067,$002EFFFF,$0049007D,$007B002F	; lookup_table
	dc.l $00180032,$00900073,$00300018,$00420090	; lookup_table
	dc.l $00780031,$002300C8,$00600068,$0032002C	; lookup_table
	dc.l $00940050,$00CE0033,$001D00BC,$00A0007D	; lookup_table
	dc.l $00340010,$00860050,$007E0035,$002600AA	; lookup_table
	dc.l $0080007F,$0036FFFF,$00A00090,$00790037	; lookup_table
	dc.l $00350002,$00700076,$0038FFFF,$00000000	; lookup_table
	dc.l $00000000,$FFFF0000,$00000000,$0000FFFF	; lookup_table
	dc.l $00000000,$00000000,$FFFF0000,$00000000	; lookup_table
	dc.l $0000FFFF,$00000000,$00000000,$FFFF0000	; lookup_table
	dc.l $00000000,$0000FFFF,$00000000,$00000000	; lookup_table
abs_0_000657EE:
	dc.b $20,$20,$20,$20,$20,$20,$4E,$4F,$54,$48,$49,$4E,$47,$21
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$42,$41,$43,$4B,$44,$4F,$4F,$52,$20,$4B,$45,$59
	dc.b $20,$20,$20,$20,$20,$20,$20,$54,$48,$45,$20,$44,$41,$47,$47,$45
	dc.b $52
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$42,$4C,$41,$43,$4B,$20,$43,$41,$54,$21,$20,$20
	dc.b $20,$45,$58,$43,$41,$4C,$49,$42,$55,$52,$20,$54,$48,$45,$20,$53
	dc.b $57,$4F,$52,$44,$21,$20,$20,$20,$20,$20,$54,$48,$45,$20,$48,$41
	dc.b $4E,$44,$4C,$45
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$42,$49,$47,$20,$53,$54,$49,$43,$4B,$21
	dcb.b $8,$20
	dc.b $54,$48,$45,$20,$44,$55,$53,$54,$45,$52,$20,$20,$20,$20,$20,$54
	dc.b $48,$45,$20,$44,$45,$56,$49,$4C,$27,$53,$20,$54,$52,$49,$44,$45
	dc.b $4E,$54,$21,$20,$20,$20,$20,$20,$20,$20,$41,$20,$4C,$45,$41,$46
	dcb.b $8,$20
	dc.b $41,$20,$50,$45,$52,$53,$4F,$4E,$41,$4C,$20,$53,$54,$45,$52,$45
	dc.b $4F,$21,$20,$20,$20,$53,$4F,$4D,$45,$20,$4D,$41,$47,$49,$43,$20
	dc.b $50,$49,$50,$45,$53,$20,$20,$20,$20,$41,$20,$50,$4F,$49,$53,$4F
	dc.b $4E,$45,$44,$20,$41,$50,$50,$4C,$45,$20,$20,$20,$20,$20,$44,$4F
	dc.b $52,$41,$20,$54,$48,$45,$20,$46,$52,$4F,$47,$21,$20,$20,$20,$20
	dc.b $20,$20,$20,$41,$20,$50,$4F,$57,$45,$52,$50,$49,$4C,$4C,$21,$20
	dc.b $20,$20,$20,$20,$20,$41,$4E,$20,$45,$4D,$50,$54,$59,$20,$42,$55
	dc.b $43,$4B,$45,$54,$21,$20,$20,$42,$55,$43,$4B,$45,$54,$20,$4F,$46
	dc.b $20,$48,$4F,$54,$20,$57,$41,$54,$45,$52,$21,$20,$20,$53,$4F,$4D
	dc.b $45,$54,$48,$49,$4E,$47,$20,$53,$54,$49,$43,$4B,$59,$20,$20,$20
	dc.b $57,$45,$45,$44,$4B,$49,$4C,$4C,$45,$52,$20,$50,$4F,$54,$49,$4F
	dc.b $4E,$21,$20,$41,$4E,$20,$45,$4D,$50,$54,$59,$20,$4D,$49,$4C,$4B
	dc.b $20,$42,$4F,$54,$54,$4C,$45,$20,$20,$41,$20,$42,$41,$47,$20,$4F
	dc.b $46,$20,$52,$55,$42,$42,$49,$53,$48,$20,$20,$4C,$49,$47,$48,$54
	dc.b $4E,$49,$4E,$47,$20,$43,$4F,$4E,$44,$55,$43,$54,$4F,$52,$21,$20
	dc.b $20,$20,$20,$41,$20,$4C,$49,$54,$20,$54,$4F,$52,$43,$48,$21
	dcb.b $8,$20
	dc.b $41,$20,$47,$4F,$4C,$44,$20,$43,$52,$4F,$53,$53,$20,$20,$20,$20
	dc.b $54,$48,$45,$20,$27,$44,$52,$49,$4E,$4B,$4D,$45,$27,$20,$50,$4F
	dc.b $54,$49,$4F,$4E,$20,$20,$41,$4E,$20,$41,$4E,$43,$49,$45,$4E,$54
	dc.b $20,$4C,$41,$4D,$50,$21,$20,$20,$20,$20,$20,$20,$20,$5A,$41,$4B
	dc.b $53,$20,$52,$49,$4E,$47,$21
	dcb.b $8,$20
	dc.b $41,$20,$59,$55,$4D,$4D,$59,$20,$43,$41,$4B,$45,$21,$21,$20,$20
	dc.b $20
abs_0_00065A1E:
	dcb.b $90,$00
	dcb.b $C,$05
	dc.b $01
	dcb.b $5B,$00
	dcb.b $D3,$08
	dcb.b $39,$00
	dcb.b $A1,$08
	dcb.b $94,$00
	dc.b $10,$10,$10,$10,$10,$10
	dcb.b $37,$00
	dcb.b $72,$04
	dcb.b $26,$00
	dcb.b $57,$04
	dcb.b $10,$05
	dcb.b $D1,$04
	dcb.b $27,$00
	dc.b $10,$10,$10,$10,$10,$10
	dcb.b $53,$00
	dc.b $10,$10,$10,$10,$10,$10,$10
	dcb.b $22,$00
	dcb.b $1A8,$08
	dc.b $00,$00,$00,$00,$00
	dcb.b $9,$10
	dcb.b $24,$00
	dcb.b $9,$01
	dcb.b $2B,$00
	dcb.b $A,$01
	dcb.b $1F,$00
	dcb.b $9,$01
	dcb.b $49,$00
	dc.b $10,$10,$10,$10,$10
	dcb.b $72,$00
	dc.b $10,$10,$10,$10
	dcb.b $A,$00
	dcb.b $152,$08
	dcb.b $24,$00
	dcb.b $11,$09
	dcb.b $69,$08
	dcb.b $1C,$00
	dcb.b $9,$05
	dc.b $01
	dcb.b $2D,$00
	dcb.b $18,$04
	dcb.b $22,$00
	dcb.b $F,$09
	dcb.b $34,$08
	dc.b $09,$09,$09,$09,$09,$09,$09
	dcb.b $4E,$08
	dcb.b $12,$09
	dcb.b $22,$08
	dcb.b $50,$00
	dc.b $FF,$00
abs_0_000666B6:
	lea.l $07C0(a0),a1
	lea.l abs_0_00066CBC(pc),a2
	moveq.l #127,d0
abs_0_000666C0:
	move.l a1,(a2)+
	lea.l $0100(a1),a1
	dbf.w d0,abs_0_000666C0
	lea.l $03BE(a0),a1
	moveq.l #0,d0
	move.b $03BC(a0),d0
	add.w d0,d0
	add.w d0,d0
	subq.w #1,d0
	moveq.l #0,d1
abs_0_000666DC:
	move.b (a1),d2
	cmp.b d1,d2
	bls.b abs_0_000666E4
	move.b d2,d1
abs_0_000666E4:
	addq.l #2,a1
	dbf.w d0,abs_0_000666DC
	addq.w #1,d1
	mulu.w #$100,d1
	lea.l $07C0(a0),a1
	lea.l $0(a1,d1.w),a1
	lea.l $0016(a0),a2
	lea.l abs_0_00066EBC(pc),a3
	moveq.l #30,d0
abs_0_00066702:
	movea.l a3,a4
	move.l a1,(a4)+
	moveq.l #0,d1
	move.w $0016(a2),d1
	move.w d1,(a4)+
	add.l d1,d1
	move.l #$6728C,(a4)+
	move.w $001C(a2),(a4)+
	move.w $0018(a2),(a4)+
	cmpi.w #1,$001C(a2)
	beq.b abs_0_00066734
	moveq.l #0,d2
	move.w $001A(a2),d2
	lea.l $0(a1,d2.l),a6
	move.l a6,-$0008(a4)
abs_0_00066734:
	adda.l d1,a1
	lea.l $001E(a2),a2
	lea.l $0010(a3),a3
	dbf.w d0,abs_0_00066702
	lea.l abs_0_000670CC.l,a1
	moveq.l #13,d0
	moveq.l #1,d2
abs_0_0006674C:
	lea.l abs_0_000670AC(pc),a0
	movea.l a1,a2
	moveq.l #31,d1
abs_0_00066754:
	moveq.l #0,d3
	move.b (a0)+,d3
	mulu.w d2,d3
	lsr.w #8,d3
	move.b d3,(a2)+
	dbf.w d1,abs_0_00066754
	addq.w #1,d2
	lea.l $0020(a1),a1
	dbf.w d0,abs_0_0006674C
	lea.l abs_0_000670AC(pc),a0
	moveq.l #31,d0
abs_0_00066772:
	clr.b (a0)+
	dbf.w d0,abs_0_00066772
	bset.b #CIAB_LED,_ciaa+ciapra.l
	lea.l abs_0_00067318(pc),a5
	clr.l $0000(a5)
	clr.l $0008(a5)
	clr.l $0004(a5)
	move.w #$6,$0006(a5)
	clr.w abs_0_00066B88.l
	rts
	dc.b $33,$FC,$00,$0F,$00,$DF,$F0,$96,$42,$79,$00,$DF,$F0,$A8,$42,$79
	dc.b $00,$DF,$F0,$B8,$42,$79,$00,$DF,$F0,$C8,$42,$79,$00,$DF,$F0,$D8
	dc.b $4E,$75
abs_0_000667C0:
	clr.w absolute_slot_0000013E.w
	lea.l abs_0_00067318(pc),a5
	lea.l _custom.l,a6
	addq.w #1,$0004(a5)
	move.w $0006(a5),d0
	cmp.w $0004(a5),d0
	beq.w abs_0_000669D8
	lea.l aud0+ac_ptr(a6),a1
	lea.l abs_0_00067290(pc),a2
	bsr.b abs_0_00066808
	lea.l aud1+ac_ptr(a6),a1
	lea.l abs_0_000672B2(pc),a2
	bsr.b abs_0_00066808
	lea.l aud2+ac_ptr(a6),a1
	lea.l abs_0_000672D4(pc),a2
	bsr.b abs_0_00066808
	lea.l aud3+ac_ptr(a6),a1
	lea.l abs_0_000672F6(pc),a2
	bsr.b abs_0_00066808
	rts
abs_0_00066808:
	moveq.l #0,d0
	move.b $0016(a2),d0
	add.w d0,d0
	add.w d0,d0
	jmp abs_0_00066816(pc,d0.w)
abs_0_00066816:
	bra.w abs_0_00066856
abs_0_0006681A:
	bra.w abs_0_000668BA
abs_0_0006681E:
	bra.w abs_0_000668DE
abs_0_00066822:
	bra.w abs_0_00066904
abs_0_00066826:
	bra.w abs_0_00066954
abs_0_0006682A:
	bra.w abs_0_000669D6
abs_0_0006682E:
	bra.w abs_0_000669D6
abs_0_00066832:
	bra.w abs_0_000669D6
abs_0_00066836:
	bra.w abs_0_000669D6
abs_0_0006683A:
	bra.w abs_0_000669D6
abs_0_0006683E:
	bra.w abs_0_000669A4
abs_0_00066842:
	bra.w abs_0_000669D6
abs_0_00066846:
	bra.w abs_0_000669D6
abs_0_0006684A:
	bra.w abs_0_000669D6
abs_0_0006684E:
	bra.w abs_0_000669D6
abs_0_00066852:
	bra.w abs_0_000669D6
abs_0_00066856:
	tst.b $0017(a2)
	bne.b abs_0_0006685E
	rts
abs_0_0006685E:
	move.w $0004(a5),d0
	move.b abs_0_0006689A(pc,d0.w),d0
	beq.w abs_0_000669D6
	cmp.b #$2,d0
	beq.b abs_0_00066878
	move.b $0017(a2),d0
	lsr.w #4,d0
	bra.b abs_0_00066880
abs_0_00066878:
	move.b $0017(a2),d0
	andi.w #15,d0
abs_0_00066880:
	lea.l abs_0_00066C26(pc),a0
	add.w d0,d0
	move.w $0018(a2),d1
	add.w d0,d1
	move.w $0(a0,d1.w),d0
	move.w d0,$0006(a1)
	move.w d0,$0000(a2)
	rts
abs_0_0006689A:
	dc.b $00,$01,$02,$00,$01,$02,$00,$01,$02,$00,$01,$02,$00,$01,$02,$00	; lookup_table
	dc.b $01,$02,$00,$01,$02,$00,$01,$02,$00,$01,$02,$00,$01,$02,$00,$01	; lookup_table
abs_0_000668BA:
	moveq.l #0,d0
	move.b $0017(a2),d0
	sub.w d0,$0000(a2)
	move.w $0000(a2),d0
	cmp.w #$71,d0
	bcc.b abs_0_000668D8
	move.w #$71,$0000(a2)
	move.w #$71,d0
abs_0_000668D8:
	move.w d0,$0006(a1)
	rts
abs_0_000668DE:
	moveq.l #0,d0
	move.b $0017(a2),d0
	add.w d0,$0000(a2)
	move.w $0000(a2),d0
	cmp.w #$358,d0
	bmi.b abs_0_000668FE
	andi.w #61440,$0000(a2)
	ori.w #856,$0000(a2)
abs_0_000668FE:
	move.w d0,$0006(a1)
	rts
abs_0_00066904:
	move.b $0017(a2),d0
	beq.b abs_0_00066912
	move.b d0,$001B(a2)
	clr.b $0017(a2)
abs_0_00066912:
	tst.w $001C(a2)
	beq.b abs_0_00066952
	moveq.l #0,d0
	move.b $001B(a2),d0
	tst.b $001A(a2)
	bne.b abs_0_00066934
	add.w d0,$0000(a2)
	move.w $001C(a2),d0
	cmp.w $0000(a2),d0
	bgt.b abs_0_0006694C
	bra.b abs_0_00066942
abs_0_00066934:
	sub.w d0,$0000(a2)
	move.w $001C(a2),d0
	cmp.w $0000(a2),d0
	blt.b abs_0_0006694C
abs_0_00066942:
	move.w $001C(a2),$0000(a2)
	clr.w $001C(a2)
abs_0_0006694C:
	move.w $0000(a2),$0006(a1)
abs_0_00066952:
	rts
abs_0_00066954:
	move.b $0017(a2),d0
	beq.b abs_0_0006695E
	move.b d0,$001E(a2)
abs_0_0006695E:
	move.b $001F(a2),d0
	lsr.w #2,d0
	andi.w #31,d0
	move.b $001E(a2),d1
	andi.w #15,d1
	lsl.w #5,d1
	lea.l abs_0_000670AC(pc),a0
	adda.w d1,a0
	moveq.l #0,d2
	move.b $0(a0,d0.w),d2
	add.w d2,d2
	move.w $0000(a2),d0
	tst.b $001F(a2)
	bmi.b abs_0_0006698E
	add.w d2,d0
	bra.b abs_0_00066990
abs_0_0006698E:
	sub.w d2,d0
abs_0_00066990:
	move.w d0,$0006(a1)
	move.b $001E(a2),d0
	lsr.w #2,d0
	andi.w #60,d0
	add.b d0,$001F(a2)
	rts
abs_0_000669A4:
	moveq.l #0,d0
	move.b $0017(a2),d0
	cmp.b #$10,d0
	bcs.b abs_0_000669C0
	lsr.b #4,d0
	add.w $0002(a2),d0
	cmp.w #$40,d0
	bmi.b abs_0_000669CE
	moveq.l #64,d0
	bra.b abs_0_000669CE
abs_0_000669C0:
	andi.b #15,d0
	neg.w d0
	add.w $0002(a2),d0
	bpl.b abs_0_000669CE
	moveq.l #0,d0
abs_0_000669CE:
	move.w d0,$0002(a2)
	move.w d0,$0008(a1)
abs_0_000669D6:
	rts
abs_0_000669D8:
	clr.w $0004(a5)
	lea.l absolute_slot_000519D6.l,a3
	move.w $0000(a5),d0
	lsl.w #3,d0
	lea.l $0(a3,d0.w),a3
	clr.w $0008(a5)
	lea.l $00A0(a6),a1
	lea.l abs_0_00067290(pc),a2
	moveq.l #1,d7
	bsr.b abs_0_00066A62
	lea.l $00B0(a6),a1
	lea.l abs_0_000672B2(pc),a2
	moveq.l #2,d7
	bsr.b abs_0_00066A62
	lea.l $00C0(a6),a1
	lea.l abs_0_000672D4(pc),a2
	moveq.l #4,d7
	bsr.b abs_0_00066A62
	lea.l $00D0(a6),a1
	lea.l abs_0_000672F6(pc),a2
	moveq.l #8,d7
	bsr.b abs_0_00066A62
	bset.b #CIACRAB_START,_ciab+ciacra.l
	tst.w $000A(a5)
	bne.b abs_0_00066A3A
	addq.w #4,$0002(a5)
	cmpi.w #256,$0002(a5)
	bne.b abs_0_00066A5A
abs_0_00066A3A:
	clr.w $000A(a5)
	clr.w $0002(a5)
	addq.w #1,$0000(a5)
	move.b $000519D4.l,d0
	cmp.b $0001(a5),d0
	bne.b abs_0_00066A5A
	move.b $000519D5.l,$0001(a5)
abs_0_00066A5A:
	ori.w #33280,$0008(a5)
	rts
abs_0_00066A62:
	moveq.l #0,d0
	move.b (a3),d0
	add.w d0,d0
	add.w d0,d0
	lea.l abs_0_00066CBC(pc),a0
	movea.l $0(a0,d0.w),a0
	adda.w $0002(a5),a0
	move.l (a0),$0014(a2)
	tst.b $0015(a2)
	beq.b abs_0_00066AA6
	moveq.l #0,d0
	move.b $0015(a2),d0
	lsl.w #4,d0
	lea.l abs_0_00066EAC.l,a0
	lea.l $0(a0,d0.w),a0
	move.l (a0)+,$0006(a2)
	move.w (a0)+,$000A(a2)
	move.l (a0)+,$000C(a2)
	move.w (a0)+,$0010(a2)
	move.w (a0),$0002(a2)
abs_0_00066AA6:
	move.w $0002(a2),$0008(a1)
	moveq.l #0,d0
	move.b $0014(a2),d0
	cmp.b #$A8,d0
	beq.b abs_0_00066B12
	lea.l abs_0_00066C26(pc),a0
	move.b $0001(a3),d1
	beq.b abs_0_00066AC8
	ext.w d1
	add.w d1,d1
	add.w d1,d0
abs_0_00066AC8:
	move.w d0,$0018(a2)
	move.w $0(a0,d0.w),d0
	cmpi.b #3,$0016(a2)
	bne.b abs_0_00066AF4
	move.w d0,$001C(a2)
	clr.b $001A(a2)
	cmp.w $0000(a2),d0
	beq.b abs_0_00066AEE
	bge.b abs_0_00066B12
	addq.b #1,$001A(a2)
	bra.b abs_0_00066B12
abs_0_00066AEE:
	clr.w $001C(a2)
	bra.b abs_0_00066B12
abs_0_00066AF4:
	move.w d7,$0096(a6)
	move.w d0,$0006(a1)
	move.w d0,$0000(a2)
	clr.b $001F(a2)
	or.w d7,$0008(a5)
	move.l $0006(a2),(a1)
	move.w $000A(a2),$0004(a1)
abs_0_00066B12:
	bsr.w abs_0_00066B8A
	addq.l #2,a3
	rts
abs_0_00066B1A:
	addq.w #1,absolute_slot_0000013E.w
	tst.w abs_0_00066B88.l
	bne.b abs_0_00066B40
	cmpi.w #2,absolute_slot_0000013E.w
	beq.b abs_0_00066B3E
	move.w #$1,abs_0_00066B88.l
	move.w abs_0_00067320(pc),_custom+dmacon.l
abs_0_00066B3E:
	rts
abs_0_00066B40:
	clr.w abs_0_00066B88.l
	movem.l a1-a2,-(a7)
	lea.l _custom+aud0+ac_ptr.l,a1
	lea.l abs_0_00067290(pc),a2
	move.l $000C(a2),(a1)
	move.w $0010(a2),$0004(a1)
	move.l $002E(a2),$0010(a1)
	move.w $0032(a2),$0014(a1)
	move.l $0050(a2),$0020(a1)
	move.w $0054(a2),$0024(a1)
	move.l $0072(a2),$0030(a1)
	move.w $0076(a2),$0034(a1)
	movem.l (a7)+,a1-a2
	rts
abs_0_00066B88:
	dc.w $0000
abs_0_00066B8A:
	moveq.l #0,d0
	move.b $0016(a2),d0
	add.w d0,d0
	add.w d0,d0
	jmp abs_0_00066B98(pc,d0.w)
abs_0_00066B98:
	bra.w abs_0_000669D6
abs_0_00066B9C:
	bra.w abs_0_000669D6
abs_0_00066BA0:
	bra.w abs_0_000669D6
abs_0_00066BA4:
	bra.w abs_0_000669D6
abs_0_00066BA8:
	bra.w abs_0_000669D6
abs_0_00066BAC:
	bra.w abs_0_000669D6
abs_0_00066BB0:
	bra.w abs_0_000669D6
abs_0_00066BB4:
	bra.w abs_0_000669D6
abs_0_00066BB8:
	bra.w abs_0_000669D6
abs_0_00066BBC:
	bra.w abs_0_000669D6
abs_0_00066BC0:
	bra.w abs_0_000669D6
abs_0_00066BC4:
	bra.w abs_0_00066BF2
abs_0_00066BC8:
	bra.w abs_0_00066C0A
abs_0_00066BCC:
	bra.w abs_0_00066BFE
abs_0_00066BD0:
	bra.w abs_0_00066BD8
abs_0_00066BD4:
	bra.w abs_0_00066C1A
abs_0_00066BD8:
	move.b $0017(a2),d0
	beq.b abs_0_00066BE8
	bset.b #CIAB_LED,_ciaa+ciapra.l
	rts
abs_0_00066BE8:
	bclr.b #CIAB_LED,_ciaa+ciapra.l
	rts
abs_0_00066BF2:
	moveq.l #0,d0
	move.b $0017(a2),d0
	subq.b #1,d0
	move.w d0,$0000(a5)
abs_0_00066BFE:
	move.w #$1,$000A(a5)
	clr.l $0014(a2)
	rts
abs_0_00066C0A:
	moveq.l #0,d0
	move.b $0017(a2),d0
	move.w d0,$0008(a1)
	move.w d0,$0002(a2)
	rts
abs_0_00066C1A:
	move.b $0017(a2),d0
	beq.b abs_0_00066C24
	move.w d0,$0006(a5)
abs_0_00066C24:
	rts
abs_0_00066C26:
	dc.b $1A,$C0,$19,$40,$17,$D0,$16,$80,$15,$30,$14,$00,$12,$E0,$11,$D0
	dc.b $10,$D0,$0F,$E0,$0F,$00,$0E,$28,$0D,$60,$0C,$A0,$0B,$E8,$0B,$40
	dc.b $0A,$98,$0A,$00,$09,$70,$08,$E8,$08,$68,$07,$F0,$07,$80,$07,$14
	dc.b $06,$B0,$06,$50,$05,$F4,$05,$A0,$05,$4C,$05,$00,$04,$B8,$04,$74
	dc.b $04,$34,$03,$F8,$03,$C0,$03,$8A,$03,$58,$03,$28,$02,$FA,$02,$D0
	dc.b $02,$A6,$02,$80,$02,$5C,$02,$3A,$02,$1A,$01,$FC,$01,$E0,$01,$C5
	dc.b $01,$AC,$01,$94,$01,$7D,$01,$68,$01,$53,$01,$40,$01,$2E,$01,$1D
	dc.b $01,$0D,$00,$FE,$00,$F0,$00,$E2,$00,$D6,$00,$CA,$00,$BE,$00,$B4
	dc.b $00,$AA,$00,$A0,$00,$97,$00,$8F,$00,$87,$00,$7F,$00,$78,$00,$71
	dc.b $00,$00,$00,$00,$00,$00
abs_0_00066CBC:
	dcb.b $1F0,$00
abs_0_00066EAC:
	dcb.b $10,$00
abs_0_00066EBC:
	dcb.b $1F0,$00
abs_0_000670AC:
	dc.b $00,$18,$31,$4A,$61,$78,$8D,$A1,$B4,$C5,$D4,$E0,$EB,$F4,$FA,$FD
	dc.b $FF,$FD,$FA,$F4,$EB,$E0,$D4,$C5,$B4,$A1,$8D,$78,$61,$4A,$31,$18
abs_0_000670CC:
	dcb.b $1C4,$00
abs_0_00067290:
	dcb.b $22,$00
abs_0_000672B2:
	dcb.b $22,$00
abs_0_000672D4:
	dcb.b $22,$00
abs_0_000672F6:
	dcb.b $22,$00
abs_0_00067318:
	dcb.b $8,$00
abs_0_00067320:
	dc.w $0000,$0000,$0000,$0000,$0000,$03F2	; lookup_table
