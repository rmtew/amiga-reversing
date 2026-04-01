# Amiga Hardware Register Reference

Extracted from the Amiga Hardware Reference Manual. 245 registers.

Base address: `$DFF000` — add register offset to get 68000 address.

## Register Map (Address Order)

| Address | Name | R/W | Chip | Function |
|---------|------|-----|------|----------|
| `$000` | [BLTDDAT](#bltddat) | ER | A | Blitter destination early read |
| `$002` | [DMACONR](#dmaconr) | R | AP | DMA control (and blitter status) read |
| `$004` | [VPOSR](#vposr) | R | A | Read vert most signif. bit (and frame flop) (ECS) |
| `$006` | [VHPOSR](#vhposr) | R | A | Read vert and horiz. position of beam |
| `$008` | [DSKDATR](#dskdatr) | ER | P | Disk data early read (dummy address) |
| `$00A` | [JOY0DAT](#joy0dat) | R | D | Joystick-mouse 0 data (vert,horiz) |
| `$00C` | [JOY1DAT](#joy1dat) | R | D | Joystick-mouse 1 data (vert,horiz) |
| `$00E` | [CLXDAT](#clxdat) | R | D | Collision data register (read and clear) |
| `$010` | [ADKCONR](#adkconr) | R | P | Audio, disk control register read |
| `$012` | [POT0DAT](#pot0dat) | R | P | Pot counter pair 0 data (vert,horiz) (ECS) |
| `$014` | [POT1DAT](#pot1dat) | R | P | Pot counter pair 1 data (vert,horiz) (ECS) |
| `$016` | [POTGOR](#potgor) | R | P | Pot port data read (formerly POTINP) |
| `$018` | [SERDATR](#serdatr) | R | P | Serial port data and status read |
| `$01A` | [DSKBYTR](#dskbytr) | R | P | Disk data byte and status read |
| `$01C` | [INTENAR](#intenar) | R | P | Interrupt enable bits read |
| `$01E` | [INTREQR](#intreqr) | R | P | Interrupt request bits read |
| `$020` | [DSKPTH](#dskpth) | W | A | Disk pointer (high 3 bits, 5 bits if ECS) (ECS) |
| `$022` | [DSKPTL](#dskptl) | W | A | Disk pointer (low 15 bits) |
| `$024` | [DSKLEN](#dsklen) | W | P | Disk length |
| `$026` | [DSKDAT](#dskdat) | W | P | Disk DMA data write |
| `$028` | [REFPTR](#refptr) | W | A | Refresh pointer |
| `$02A` | [VPOSW](#vposw) | W | A | Write vert most signif. bit (and frame flop) |
| `$02C` | [VHPOSW](#vhposw) | W | A | Write vert and horiz position of beam |
| `$02E` | [COPCON](#copcon) | W | A | Coprocessor control register (CDANG) (ECS) |
| `$030` | [SERDAT](#serdat) | W | P | Serial port data and stop bits write |
| `$032` | [SERPER](#serper) | W | P | Serial port period and control |
| `$034` | [POTGO](#potgo) | W | P | Pot port data write and start |
| `$036` | [JOYTEST](#joytest) | W | D | Write to all four joystick-mouse counters |
| `$038` | [STREQU](#strequ) | S | D | Strobe for horiz sync with VB and EQU |
| `$03A` | [STRVBL](#strvbl) | S | D | Strobe for horiz sync with VB (vert. blank) |
| `$03C` | [STRHOR](#strhor) | S | DP | Strobe for horiz sync |
| `$03E` | [STRLONG](#strlong) | S | D | Strobe for identification of long (ECS) |
| `$040` | [BLTCON0](#bltcon0) | W | A | Blitter control register 0 |
| `$042` | [BLTCON1](#bltcon1) | W | A | Blitter control register 1 (ECS) |
| `$044` | [BLTAFWM](#bltafwm) | W | A | Blitter first word mask for source A |
| `$046` | [BLTALWM](#bltalwm) | W | A | Blitter last word mask for source A |
| `$048` | [BLTCPTH](#bltcpth) | W | A | Blitter pointer to source C (high 3 bits) |
| `$04A` | [BLTCPTL](#bltcptl) | W | A | Blitter pointer to source C (low 15 bits) |
| `$04C` | [BLTBPTH](#bltbpth) | W | A | Blitter pointer to source B (high 3 bits) |
| `$04E` | [BLTBPTL](#bltbptl) | W | A | Blitter pointer to source B (low 15 bits) |
| `$050` | [BLTAPTH](#bltapth) | W | A | Blitter pointer to source A (high 3 bits) (ECS) |
| `$052` | [BLTAPTL](#bltaptl) | W | A | Blitter pointer to source A (low 15 bits) |
| `$054` | [BLTDPTH](#bltdpth) | W | A | Blitter pointer to destination D |
| `$056` | [BLTDPTL](#bltdptl) | W | A | Blitter pointer to destination D |
| `$058` | [BLTSIZE](#bltsize) | W | A | Blitter start and size (window width,height) |
| `$05A` | [BLTCON0L](#bltcon0l) | W | A | Blitter control 0, lower 8 bits (minterms) (ECS) |
| `$05C` | [BLTSIZV](#bltsizv) | W | A | Blitter V size (for 15 bit vertical size) (ECS) |
| `$05E` | [BLTSIZH](#bltsizh) | W | A | Blitter H size and start (for 11 bit H size) (ECS) |
| `$060` | [BLTCMOD](#bltcmod) | W | A | Blitter modulo for source C |
| `$062` | [BLTBMOD](#bltbmod) | W | A | Blitter modulo for source B |
| `$064` | [BLTAMOD](#bltamod) | W | A | Blitter modulo for source A |
| `$066` | [BLTDMOD](#bltdmod) | W | A | Blitter modulo for destination D |
| `$070` | [BLTCDAT](#bltcdat) | W | A | Blitter source C data register |
| `$072` | [BLTBDAT](#bltbdat) | W | A | Blitter source B data register |
| `$074` | [BLTADAT](#bltadat) | W | A | Blitter source A data register |
| `$078` | [SPRHDAT](#sprhdat) | W | A | Ext. logic UHRES sprite pointer and data id (ECS) |
| `$07C` | [DENISEID](#deniseid) | R | D | Chip revision level for Denise (ECS) |
| `$07E` | [DSKSYNC](#dsksync) | W | P | Disk sync pattern register for disk read |
| `$080` | [COP1LCH](#cop1lch) | W | A | Coprocessor first location register (ECS) |
| `$082` | [COP1LCL](#cop1lcl) | W | A | Coprocessor first location register |
| `$084` | [COP2LCH](#cop2lch) | W | A | Coprocessor second location register (ECS) |
| `$086` | [COP2LCL](#cop2lcl) | W | A | Coprocessor second location register |
| `$088` | [COPJMP1](#copjmp1) | S | A | Coprocessor restart at first location |
| `$08A` | [COPJMP2](#copjmp2) | S | A | Coprocessor restart at second location |
| `$08C` | [COPINS](#copins) | W | A | Coprocessor instruction fetch identify |
| `$08E` | [DIWSTRT](#diwstrt) | W | A | Display window start (upper left |
| `$090` | [DIWSTOP](#diwstop) | W | A | Display window stop (lower right |
| `$092` | [DDFSTRT](#ddfstrt) | W | A | Display bitplane data fetch start |
| `$094` | [DDFSTOP](#ddfstop) | W | A | Display bitplane data fetch stop |
| `$096` | [DMACON](#dmacon) | W | ADP | DMA control write (clear or set) |
| `$098` | [CLXCON](#clxcon) | W | D | Collision control |
| `$09A` | [INTENA](#intena) | W | P | Interrupt enable bits (clear or |
| `$09C` | [INTREQ](#intreq) | W | P | Interrupt request bits (clear or |
| `$09E` | [ADKCON](#adkcon) | W | P | Audio, disk, UART control |
| `$0A0` | [AUD0LCH](#aud0lch) | W | A | Audio channel 0 location (high 3 bits, (ECS) |
| `$0A2` | [AUD0LCL](#aud0lcl) | W | A | Audio channel 0 location (low 15 bits) |
| `$0A4` | [AUD0LEN](#aud0len) | W | P | Audio channel 0 length |
| `$0A6` | [AUD0PER](#aud0per) | W | P | Audio channel 0 period (ECS) |
| `$0A8` | [AUD0VOL](#aud0vol) | W | P | Audio channel 0 volume |
| `$0AA` | [AUD0DAT](#aud0dat) | W | P | Audio channel 0 data |
| `$0B0` | [AUD1LCH](#aud1lch) | W | A | Audio channel 1 location (high 3 bits) |
| `$0B2` | [AUD1LCL](#aud1lcl) | W | A | Audio channel 1 location (low 15 bits) |
| `$0B4` | [AUD1LEN](#aud1len) | W | P | Audio channel 1 length |
| `$0B6` | [AUD1PER](#aud1per) | W | P | Audio channel 1 period |
| `$0B8` | [AUD1VOL](#aud1vol) | W | P | Audio channel 1 volume |
| `$0BA` | [AUD1DAT](#aud1dat) | W | P | Audio channel 1 data |
| `$0C0` | [AUD2LCH](#aud2lch) | W | A | Audio channel 2 location (high 3 bits) |
| `$0C2` | [AUD2LCL](#aud2lcl) | W | A | Audio channel 2 location (low 15 bits) |
| `$0C4` | [AUD2LEN](#aud2len) | W | P | Audio channel 2 length |
| `$0C6` | [AUD2PER](#aud2per) | W | P | Audio channel 2 period |
| `$0C8` | [AUD2VOL](#aud2vol) | W | P | Audio channel 2 volume |
| `$0CA` | [AUD2DAT](#aud2dat) | W | P | Audio channel 2 data |
| `$0D0` | [AUD3LCH](#aud3lch) | W | A | Audio channel 3 location (high 3 bits) |
| `$0D2` | [AUD3LCL](#aud3lcl) | W | A | Audio channel 3 location (low 15 bits) |
| `$0D4` | [AUD3LEN](#aud3len) | W | P | Audio channel 3 length |
| `$0D6` | [AUD3PER](#aud3per) | W | P | Audio channel 3 period |
| `$0D8` | [AUD3VOL](#aud3vol) | W | P | Audio channel 3 volume |
| `$0DA` | [AUD3DAT](#aud3dat) | W | P | Audio channel 3 data |
| `$0E0` | [BPL1PTH](#bpl1pth) | W | A | Bitplane 1 pointer (high 3 bits) |
| `$0E2` | [BPL1PTL](#bpl1ptl) | W | A | Bitplane 1 pointer (low 15 bits) |
| `$0E4` | [BPL2PTH](#bpl2pth) | W | A | Bitplane 2 pointer (high 3 bits) |
| `$0E6` | [BPL2PTL](#bpl2ptl) | W | A | Bitplane 2 pointer (low 15 bits) |
| `$0E8` | [BPL3PTH](#bpl3pth) | W | A | Bitplane 3 pointer (high 3 bits) |
| `$0EA` | [BPL3PTL](#bpl3ptl) | W | A | Bitplane 3 pointer (low 15 bits) |
| `$0EC` | [BPL4PTH](#bpl4pth) | W | A | Bitplane 4 pointer (high 3 bits) |
| `$0EE` | [BPL4PTL](#bpl4ptl) | W | A | Bitplane 4 pointer (low 15 bits) |
| `$0F0` | [BPL5PTH](#bpl5pth) | W | A | Bitplane 5 pointer (high 3 bits) |
| `$0F2` | [BPL5PTL](#bpl5ptl) | W | A | Bitplane 5 pointer (low 15 bits) |
| `$0F4` | [BPL6PTH](#bpl6pth) | W | A | Bitplane 6 pointer (high 3 bits) |
| `$0F6` | [BPL6PTL](#bpl6ptl) | W | A | Bitplane 6 pointer (low 15 bits) |
| `$100` | [BPLCON0](#bplcon0) | W | AD | Bitplane control register (ECS) |
| `$102` | [BPLCON1](#bplcon1) | W | D | Bitplane control reg. |
| `$104` | [BPLCON2](#bplcon2) | W | D | Bitplane control reg. (priority control) (ECS) |
| `$106` | [BPLCON3](#bplcon3) | W | D | Bitplane control (enhanced features) (ECS) |
| `$108` | [BPL1MOD](#bpl1mod) | W | A | Bitplane modulo (odd planes) |
| `$10A` | [BPL2MOD](#bpl2mod) | W | A | Bitplane modulo (even planes) |
| `$110` | [BPL1DAT](#bpl1dat) | W | D | Bitplane 1 data (parallel-to-serial convert) |
| `$112` | [BPL2DAT](#bpl2dat) | W | D | Bitplane 2 data (parallel-to-serial convert) |
| `$114` | [BPL3DAT](#bpl3dat) | W | D | Bitplane 3 data (parallel-to-serial convert) |
| `$116` | [BPL4DAT](#bpl4dat) | W | D | Bitplane 4 data (parallel-to-serial convert) |
| `$118` | [BPL5DAT](#bpl5dat) | W | D | Bitplane 5 data (parallel-to-serial convert) |
| `$11A` | [BPL6DAT](#bpl6dat) | W | D | Bitplane 6 data (parallel-to-serial convert) |
| `$120` | [SPR0PTH](#spr0pth) | W | A | Sprite 0 pointer (high 3 bits) |
| `$122` | [SPR0PTL](#spr0ptl) | W | A | Sprite 0 pointer (low 15 bits) |
| `$124` | [SPR1PTH](#spr1pth) | W | A | Sprite 1 pointer (high 3 bits) |
| `$126` | [SPR1PTL](#spr1ptl) | W | A | Sprite 1 pointer (low 15 bits) |
| `$128` | [SPR2PTH](#spr2pth) | W | A | Sprite 2 pointer (high 3 bits) |
| `$12A` | [SPR2PTL](#spr2ptl) | W | A | Sprite 2 pointer (low 15 bits) |
| `$12C` | [SPR3PTH](#spr3pth) | W | A | Sprite 3 pointer (high 3 bits) |
| `$12E` | [SPR3PTL](#spr3ptl) | W | A | Sprite 3 pointer (low 15 bits) |
| `$130` | [SPR4PTH](#spr4pth) | W | A | Sprite 4 pointer (high 3 bits) |
| `$132` | [SPR4PTL](#spr4ptl) | W | A | Sprite 4 pointer (low 15 bits) |
| `$134` | [SPR5PTH](#spr5pth) | W | A | Sprite 5 pointer (high 3 bits) |
| `$136` | [SPR5PTL](#spr5ptl) | W | A | Sprite 5 pointer (low 15 bits) |
| `$138` | [SPR6PTH](#spr6pth) | W | A | Sprite 6 pointer (high 3 bits) |
| `$13A` | [SPR6PTL](#spr6ptl) | W | A | Sprite 6 pointer (low 15 bits) |
| `$13C` | [SPR7PTH](#spr7pth) | W | A | Sprite 7 pointer (high 3 bits) |
| `$13E` | [SPR7PTL](#spr7ptl) | W | A | Sprite 7 pointer (low 15 bits) |
| `$140` | [SPR0POS](#spr0pos) | W | AD | Sprite 0 vert-horiz start position |
| `$142` | [SPR0CTL](#spr0ctl) | W | AD | Sprite 0 vert stop position and (ECS) |
| `$144` | [SPR0DATA](#spr0data) | W | D | Sprite 0 image data register A |
| `$146` | [SPR0DATB](#spr0datb) | W | D | Sprite 0 image data register B |
| `$148` | [SPR1POS](#spr1pos) | W | AD | Sprite 1 vert-horiz start position |
| `$14A` | [SPR1CTL](#spr1ctl) | W | AD | Sprite 1 vert stop position and |
| `$14C` | [SPR1DATA](#spr1data) | W | D | Sprite 1 image data register A |
| `$14E` | [SPR1DATB](#spr1datb) | W | D | Sprite 1 image data register B |
| `$150` | [SPR2POS](#spr2pos) | W | AD | Sprite 2 vert-horiz start position |
| `$152` | [SPR2CTL](#spr2ctl) | W | AD | Sprite 2 vert stop position and |
| `$154` | [SPR2DATA](#spr2data) | W | D | Sprite 2 image data register A |
| `$156` | [SPR2DATB](#spr2datb) | W | D | Sprite 2 image data register B |
| `$158` | [SPR3POS](#spr3pos) | W | AD | Sprite 3 vert-horiz start position |
| `$15A` | [SPR3CTL](#spr3ctl) | W | AD | Sprite 3 vert stop position and |
| `$15C` | [SPR3DATA](#spr3data) | W | D | Sprite 3 image data register A |
| `$15E` | [SPR3DATB](#spr3datb) | W | D | Sprite 3 image data register B |
| `$160` | [SPR4POS](#spr4pos) | W | AD | Sprite 4 vert-horiz start position |
| `$162` | [SPR4CTL](#spr4ctl) | W | AD | Sprite 4 vert stop position and |
| `$164` | [SPR4DATA](#spr4data) | W | D | Sprite 4 image data register A |
| `$166` | [SPR4DATB](#spr4datb) | W | D | Sprite 4 image data register B |
| `$168` | [SPR5POS](#spr5pos) | W | AD | Sprite 5 vert-horiz start position |
| `$16A` | [SPR5CTL](#spr5ctl) | W | AD | Sprite 5 vert stop position and |
| `$16C` | [SPR5DATA](#spr5data) | W | D | Sprite 5 image data register A |
| `$16E` | [SPR5DATB](#spr5datb) | W | D | Sprite 5 image data register B |
| `$170` | [SPR6POS](#spr6pos) | W | AD | Sprite 6 vert-horiz start position |
| `$172` | [SPR6CTL](#spr6ctl) | W | AD | Sprite 6 vert stop position and |
| `$174` | [SPR6DATA](#spr6data) | W | D | Sprite 6 image data register A |
| `$176` | [SPR6DATB](#spr6datb) | W | D | Sprite 6 image data register B |
| `$178` | [SPR7POS](#spr7pos) | W | AD | Sprite 7 vert-horiz start position |
| `$17A` | [SPR7CTL](#spr7ctl) | W | AD | Sprite 7 vert stop position and |
| `$17C` | [SPR7DATA](#spr7data) | W | D | Sprite 7 image data register A |
| `$17E` | [SPR7DATB](#spr7datb) | W | D | Sprite 7 image data register B |
| `$180` | [COLOR00](#color00) | W | D | Color table 00 |
| `$182` | [COLOR01](#color01) | W | D | Color table 01 |
| `$184` | [COLOR02](#color02) | W | D | Color table 02 |
| `$186` | [COLOR03](#color03) | W | D | Color table 03 |
| `$188` | [COLOR04](#color04) | W | D | Color table 04 |
| `$18A` | [COLOR05](#color05) | W | D | Color table 05 |
| `$18C` | [COLOR06](#color06) | W | D | Color table 06 |
| `$18E` | [COLOR07](#color07) | W | D | Color table 07 |
| `$190` | [COLOR08](#color08) | W | D | Color table 08 |
| `$192` | [COLOR09](#color09) | W | D | Color table 09 |
| `$194` | [COLOR10](#color10) | W | D | Color table 10 |
| `$196` | [COLOR11](#color11) | W | D | Color table 11 |
| `$198` | [COLOR12](#color12) | W | D | Color table 12 |
| `$19A` | [COLOR13](#color13) | W | D | Color table 13 |
| `$19C` | [COLOR14](#color14) | W | D | Color table 14 |
| `$19E` | [COLOR15](#color15) | W | D | Color table 15 |
| `$1A0` | [COLOR16](#color16) | W | D | Color table 16 |
| `$1A2` | [COLOR17](#color17) | W | D | Color table 17 |
| `$1A4` | [COLOR18](#color18) | W | D | Color table 18 |
| `$1A6` | [COLOR19](#color19) | W | D | Color table 19 |
| `$1A8` | [COLOR20](#color20) | W | D | Color table 20 |
| `$1AA` | [COLOR21](#color21) | W | D | Color table 21 |
| `$1AC` | [COLOR22](#color22) | W | D | Color table 22 |
| `$1AE` | [COLOR23](#color23) | W | D | Color table 23 |
| `$1B0` | [COLOR24](#color24) | W | D | Color table 24 |
| `$1B2` | [COLOR25](#color25) | W | D | Color table 25 |
| `$1B4` | [COLOR26](#color26) | W | D | Color table 26 |
| `$1B6` | [COLOR27](#color27) | W | D | Color table 27 |
| `$1B8` | [COLOR28](#color28) | W | D | Color table 28 |
| `$1BA` | [COLOR29](#color29) | W | D | Color table 29 |
| `$1BC` | [COLOR30](#color30) | W | D | Color table 30 |
| `$1BE` | [COLOR31](#color31) | W | D | Color table 31 |
| `$1C0` | [HTOTAL](#htotal) | W | A | Highest number count, horiz line (ECS) |
| `$1C2` | [HSSTOP](#hsstop) | W | A | Horizontal line position for HSYNC stop (ECS) |
| `$1C4` | [HBSTRT](#hbstrt) | W | A | Horizontal line position for HBLANK start (ECS) |
| `$1C6` | [HBSTOP](#hbstop) | W | A | Horizontal line position for HBLANK stop (ECS) |
| `$1C8` | [VTOTAL](#vtotal) | W | A | Highest numbered vertical line (ECS) |
| `$1CA` | [VSSTOP](#vsstop) | W | A | Vertical line position for VSYNC stop (ECS) |
| `$1CC` | [VBSTRT](#vbstrt) | W | A | Vertical line for VBLANK start (ECS) |
| `$1CE` | [VBSTOP](#vbstop) | W | A | Vertical line for VBLANK stop (ECS) |
| `$1DC` | [BEAMCON0](#beamcon0) | W | A | Beam counter control register (SHRES,PAL) (ECS) |
| `$1DE` | [HSSTRT](#hsstrt) | W | A | Horizontal sync start (VARHSY) (ECS) |
| `$1E0` | [VSSTRT](#vsstrt) | W | A | Vertical sync start   (VARVSY) (ECS) |
| `$1E2` | [HCENTER](#hcenter) | W | A | Horizontal position for Vsync on interlace (ECS) |
| `$1E4` | [DIWHIGH](#diwhigh) | W | AD | Display window -  upper bits for start, stop (ECS) |
| `$BFE001` | [CIAA_PRA](#ciaa_pra) | R/W | CIA-A | CIA-A: Peripheral Data Register A |
| `$BFE101` | [CIAA_PRB](#ciaa_prb) | R/W | CIA-A | CIA-A: Peripheral Data Register B |
| `$BFE201` | [CIAA_DDRA](#ciaa_ddra) | R/W | CIA-A | CIA-A: Data Direction Register A |
| `$BFE301` | [CIAA_DDRB](#ciaa_ddrb) | R/W | CIA-A | CIA-A: Data Direction Register B |
| `$BFE401` | [CIAA_TALO](#ciaa_talo) | R/W | CIA-A | CIA-A: Timer A Low |
| `$BFE501` | [CIAA_TAHI](#ciaa_tahi) | R/W | CIA-A | CIA-A: Timer A High |
| `$BFE601` | [CIAA_TBLO](#ciaa_tblo) | R/W | CIA-A | CIA-A: Timer B Low |
| `$BFE701` | [CIAA_TBHI](#ciaa_tbhi) | R/W | CIA-A | CIA-A: Timer B High |
| `$BFE801` | [CIAA_TODLOW](#ciaa_todlow) | R/W | CIA-A | CIA-A: Event counter bits 7-0 |
| `$BFE901` | [CIAA_TODMID](#ciaa_todmid) | R/W | CIA-A | CIA-A: Event counter bits 15-8 |
| `$BFEA01` | [CIAA_TODHI](#ciaa_todhi) | R/W | CIA-A | CIA-A: Event counter bits 23-16 |
| `$BFEC01` | [CIAA_SDR](#ciaa_sdr) | R/W | CIA-A | CIA-A: Serial Data Register |
| `$BFED01` | [CIAA_ICR](#ciaa_icr) | R/W | CIA-A | CIA-A: Interrupt Control Register |
| `$BFEE01` | [CIAA_CRA](#ciaa_cra) | R/W | CIA-A | CIA-A: Control Register A |
| `$BFEF01` | [CIAA_CRB](#ciaa_crb) | R/W | CIA-A | CIA-A: Control Register B |
| `$BFD000` | [CIAB_PRA](#ciab_pra) | R/W | CIA-B | CIA-B: Peripheral Data Register A |
| `$BFD100` | [CIAB_PRB](#ciab_prb) | R/W | CIA-B | CIA-B: Peripheral Data Register B |
| `$BFD200` | [CIAB_DDRA](#ciab_ddra) | R/W | CIA-B | CIA-B: Data Direction Register A |
| `$BFD300` | [CIAB_DDRB](#ciab_ddrb) | R/W | CIA-B | CIA-B: Data Direction Register B |
| `$BFD400` | [CIAB_TALO](#ciab_talo) | R/W | CIA-B | CIA-B: Timer A Low |
| `$BFD500` | [CIAB_TAHI](#ciab_tahi) | R/W | CIA-B | CIA-B: Timer A High |
| `$BFD600` | [CIAB_TBLO](#ciab_tblo) | R/W | CIA-B | CIA-B: Timer B Low |
| `$BFD700` | [CIAB_TBHI](#ciab_tbhi) | R/W | CIA-B | CIA-B: Timer B High |
| `$BFD800` | [CIAB_TODLOW](#ciab_todlow) | R/W | CIA-B | CIA-B: Event counter bits 7-0 |
| `$BFD900` | [CIAB_TODMID](#ciab_todmid) | R/W | CIA-B | CIA-B: Event counter bits 15-8 |
| `$BFDA00` | [CIAB_TODHI](#ciab_todhi) | R/W | CIA-B | CIA-B: Event counter bits 23-16 |
| `$BFDC00` | [CIAB_SDR](#ciab_sdr) | R/W | CIA-B | CIA-B: Serial Data Register |
| `$BFDD00` | [CIAB_ICR](#ciab_icr) | R/W | CIA-B | CIA-B: Interrupt Control Register |
| `$BFDE00` | [CIAB_CRA](#ciab_cra) | R/W | CIA-B | CIA-B: Control Register A |
| `$BFDF00` | [CIAB_CRB](#ciab_crb) | R/W | CIA-B | CIA-B: Control Register B |

## Register Details

### BLTDDAT
**Blitter destination early read**

- **Address**: `$000` (`$DFF000`)
- **Access**: ER
- **Chip**: A
- **Flags**: DMA channel only, Not writable by Copper

---

### DMACONR
**DMA control (and blitter status) read**

- **Address**: `$002` (`$DFF002`)
- **Access**: R
- **Chip**: AP
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SET/CLR | Set/clear control bit. Determines if bits written with a 1 get set or cleared.  Bits written with a zero are unchanged. |
| 14 | BBUSY | Blitter busy status bit (read only) |
| 13 | BZERO | Blitter logic  zero status bit (read only). |
| 12 | X |  |
| 11 | X |  |
| 10 | BLTPRI | Blitter DMA priority (over CPU micro) (also called "blitter nasty") (disables /BLS pin, preventing micro from stealing any bus cycles while blitter DMA is running). |
|  9 | DMAEN | Enable all DMA below |
|  8 | BPLEN | Bitplane DMA enable |
|  7 | COPEN | Copper DMA enable |
|  6 | BLTEN | Blitter DMA enable |
|  5 | SPREN | Sprite DMA enable |
|  4 | DSKEN | Disk DMA enable |
|  3 | AUD3EN | Audio channel 3 DMA enable |
|  2 | AUD2EN | Audio channel 2 DMA enable |
|  1 | AUD1EN | Audio channel 1 DMA enable |
|  0 | AUD0EN | Audio channel 0 DMA enable |

---

### VPOSR
**Read vert most signif. bit (and frame flop)**

- **Address**: `$004` (`$DFF004`)
- **Access**: R
- **Chip**: A
- **ECS**: Yes
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | USE |  |
| 14 | LOF-- |  |
|  8 | --,-- |  |
|  1 | V8 |  |

---

### VHPOSR
**Read vert and horiz. position of beam**

- **Address**: `$006` (`$DFF006`)
- **Access**: R
- **Chip**: A
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | USE |  |
| 14 | V7 |  |
| 13 | V6 |  |
| 12 | V5 |  |
| 11 | V4 |  |
| 10 | V3 |  |
|  9 | V2 |  |
|  8 | V1 |  |
|  7 | V0,H8 |  |
|  6 | H7 |  |
|  5 | H6 |  |
|  4 | H5 |  |
|  3 | H4 |  |
|  2 | H3 |  |
|  1 | H2 |  |
|  0 | H1 |  |

---

### DSKDATR
**Disk data early read (dummy address)**

- **Address**: `$008` (`$DFF008`)
- **Access**: ER
- **Chip**: P
- **Flags**: DMA channel only, Not writable by Copper

---

### JOY0DAT
**Joystick-mouse 0 data (vert,horiz)**

- **Address**: `$00A` (`$DFF00A`)
- **Access**: R
- **Chip**: D
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Y7 |  |
| 14 | Y6 |  |
| 13 | Y5 |  |
| 12 | Y4 |  |
| 11 | Y3 |  |
| 10 | Y2 |  |
|  9 | Y1 |  |
|  8 | Y0 |  |
|  7 | X7 |  |
|  6 | X6 |  |
|  5 | X5 |  |
|  4 | X4 |  |
|  3 | X3 |  |
|  2 | X2 |  |
|  1 | X1 |  |
|  0 | X0 |  |

---

### JOY1DAT
**Joystick-mouse 1 data (vert,horiz)**

- **Address**: `$00C` (`$DFF00C`)
- **Access**: R
- **Chip**: D
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Y7 |  |
| 14 | Y6 |  |
| 13 | Y5 |  |
| 12 | Y4 |  |
| 11 | Y3 |  |
| 10 | Y2 |  |
|  9 | Y1 |  |
|  8 | Y0 |  |
|  7 | X7 |  |
|  6 | X6 |  |
|  5 | X5 |  |
|  4 | X4 |  |
|  3 | X3 |  |
|  2 | X2 |  |
|  1 | X1 |  |
|  0 | X0 |  |

---

### CLXDAT
**Collision data register (read and clear)**

- **Address**: `$00E` (`$DFF00E`)
- **Access**: R
- **Chip**: D
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | not | used |
| 14 | Sprite | 4 (or 5) to sprite 6 (or 7) |
| 13 | Sprite | 2 (or 3) to sprite 6 (or 7) |
| 12 | Sprite | 2 (or 3) to sprite 4 (or 5) |
| 11 | Sprite | 0 (or 1) to sprite 6 (or 7) |
| 10 | Sprite | 0 (or 1) to sprite 4 (or 5) |
|  9 | Sprite | 0 (or 1) to sprite 2 (or 3) |
|  8 | Playfield | 2 to sprite 6 (or 7) |
|  7 | Playfield | 2 to sprite 4 (or 5) |
|  6 | Playfield | 2 to sprite 2 (or 3) |
|  5 | Playfield | 2 to sprite 0 (or 1) |
|  4 | Playfield | 1 to sprite 6 (or 7) |
|  3 | Playfield | 1 to sprite 4 (or 5) |
|  2 | Playfield | 1 to sprite 2 (or 3) |
|  1 | Playfield | 1 to sprite 0 (or 1) |
|  0 | Playfield | 1 to playfield 2 |

---

### ADKCONR
**Audio, disk control register read**

- **Address**: `$010` (`$DFF010`)
- **Access**: R
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SET/CLR | Set/clear control bit. Determines if bits written with a 1 get set or cleared. Bits written with a zero are always unchanged. |
| 14 | PRECOMP | Bits 14-13: PRECOMP |
| 13 | PRECOMP | Bits 14-13: PRECOMP |

---

### POT0DAT
**Pot counter pair 0 data (vert,horiz)**

- **Address**: `$012` (`$DFF012`)
- **Access**: R
- **Chip**: P
- **ECS**: Yes
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Y7 |  |
| 14 | Y6 |  |
| 13 | Y5 |  |
| 12 | Y4 |  |
| 11 | Y3 |  |
| 10 | Y2 |  |
|  9 | Y1 |  |
|  8 | Y0 |  |
|  7 | X7 |  |
|  6 | X6 |  |
|  5 | X5 |  |
|  4 | X4 |  |
|  3 | X3 |  |
|  2 | X2 |  |
|  1 | X1 |  |
|  0 | X0 |  |

---

### POT1DAT
**Pot counter pair 1 data (vert,horiz)**

- **Address**: `$014` (`$DFF014`)
- **Access**: R
- **Chip**: P
- **ECS**: Yes
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Y7 |  |
| 14 | Y6 |  |
| 13 | Y5 |  |
| 12 | Y4 |  |
| 11 | Y3 |  |
| 10 | Y2 |  |
|  9 | Y1 |  |
|  8 | Y0 |  |
|  7 | X7 |  |
|  6 | X6 |  |
|  5 | X5 |  |
|  4 | X4 |  |
|  3 | X3 |  |
|  2 | X2 |  |
|  1 | X1 |  |
|  0 | X0 |  |

---

### POTGOR
**Pot port data read (formerly POTINP)**

- **Address**: `$016` (`$DFF016`)
- **Access**: R
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | OUTRY | Output enable for Paula pin 36 |
| 14 | DATRY | I/O data Paula pin 36 |
| 13 | OUTRX | Output enable for Paula pin 35 |
| 12 | DATRX | I/O data Paula pin 35 |
| 11 | OUTLY | Output enable for Paula pin 33 |
| 10 | DATLY | I/O data Paula pin 33 |
|  9 | OUTLX | Output enable for Paula pin 32 |
|  8 | DATLX | I/O data Paula pin 32 |
|  7 | 0 | Bits 7-1: 0 |
|  6 | 0 | Bits 7-1: 0 |
|  5 | 0 | Bits 7-1: 0 |
|  4 | 0 | Bits 7-1: 0 |
|  3 | 0 | Bits 7-1: 0 |
|  2 | 0 | Bits 7-1: 0 |
|  1 | 0 | Bits 7-1: 0 |
|  0 | START | Start pots (dump capacitors, start counters) |

---

### SERDATR
**Serial port data and status read**

- **Address**: `$018` (`$DFF018`)
- **Access**: R
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | 0 |  |
| 15 | OVRUN | Serial port receiver overrun. Reset by resetting bit 11 of INTREQ . |
| 14 | 0 |  |
| 14 | RBF | Serial port receive buffer full (mirror). |
| 13 | 0 |  |
| 13 | TBE | Serial port transmit buffer empty (mirror). |
| 12 | 0 |  |
| 12 | TSRE | Serial port transmit shift register empty. Reset by loading into buffer. |
| 11 | 0 |  |
| 11 | RXD | RXD pin receives UART serial data for direct bit test by the microprocessor. |
| 10 | 0 |  |
| 10 | 0 | Not used |
|  9 | S |  |
|  9 | STP | Stop bit |
|  8 | D8 |  |
|  8 | STP-DB8 | Stop bit if LONG, data bit if not. |
|  7 | D7 |  |
|  7 | DB7 | Data bit |
|  6 | D6 |  |
|  6 | DB6 | Data bit |
|  5 | D5 |  |
|  5 | DB5 | Data bit |
|  4 | D4 |  |
|  4 | DB4 | Data bit |
|  3 | D3 |  |
|  3 | DB3 | Data bit |
|  2 | D2 |  |
|  2 | DB2 | Data bit |
|  1 | D1 |  |
|  1 | DB1 | Data bit |
|  0 | D0 |  |
|  0 | DB0 | Data bit |

---

### DSKBYTR
**Disk data byte and status read**

- **Address**: `$01A` (`$DFF01A`)
- **Access**: R
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | DSKBYT | Disk byte ready (reset on read) |
| 14 | DMAON | Mirror of bit 15 (DMAEN) in  DSKLEN , ANDed with Bit09 (DMAEN) in  DMACON |
| 13 | DISKWRITE | Mirror of bit 14 (WRITE) in  DSKLEN |
| 12 | WORDEQUAL | This bit true only while the DSKSYNC  register equals the data from disk. |
| 11 | X | Bits 11-8: X |
| 10 | X | Bits 11-8: X |
|  9 | X | Bits 11-8: X |
|  8 | X | Bits 11-8: X |
|  7 | DATA | Bits 7-0: DATA |
|  6 | DATA | Bits 7-0: DATA |
|  5 | DATA | Bits 7-0: DATA |
|  4 | DATA | Bits 7-0: DATA |
|  3 | DATA | Bits 7-0: DATA |
|  2 | DATA | Bits 7-0: DATA |
|  1 | DATA | Bits 7-0: DATA |
|  0 | DATA | Bits 7-0: DATA |

---

### INTENAR
**Interrupt enable bits read**

- **Address**: `$01C` (`$DFF01C`)
- **Access**: R
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Level | Description |
|-----|------|-------|-------------|
| 15 | SET/CLR |  | Set/clear control bit. Determines if bits written with a 1 get set or cleared. Bits written with a zero are always unchanged. |
| 14 | INTEN |  | Master interrupt (enable only, no request) |
| 13 | EXTER | 6 | External interrupt |
| 12 | DSKSYN | 5 | Disk sync register ( DSKSYNC ) matches disk data |
| 11 | RBF | 5 | Serial port receive buffer full |
| 10 | AUD3 | 4 | Audio channel 3 block finished |
|  9 | AUD2 | 4 | Audio channel 2 block finished |
|  8 | AUD1 | 4 | Audio channel 1 block finished |
|  7 | AUD0 | 4 | Audio channel 0 block finished |
|  6 | BLIT | 3 | Blitter finished |
|  5 | VERTB | 3 | Start of vertical blank |
|  4 | COPER | 3 | Copper |
|  3 | PORTS | 2 | I/O ports and timers |
|  2 | SOFT | 1 | Reserved for software-initiated interrupt |
|  1 | DSKBLK | 1 | Disk block finished |
|  0 | TBE | 1 | Serial port transmit buffer empty |

---

### INTREQR
**Interrupt request bits read**

- **Address**: `$01E` (`$DFF01E`)
- **Access**: R
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Level | Description |
|-----|------|-------|-------------|
| 15 | SET/CLR |  | Set/clear control bit. Determines if bits written with a 1 get set or cleared. Bits written with a zero are always unchanged. |
| 14 | INTEN |  | Master interrupt (enable only, no request) |
| 13 | EXTER | 6 | External interrupt |
| 12 | DSKSYN | 5 | Disk sync register ( DSKSYNC ) matches disk data |
| 11 | RBF | 5 | Serial port receive buffer full |
| 10 | AUD3 | 4 | Audio channel 3 block finished |
|  9 | AUD2 | 4 | Audio channel 2 block finished |
|  8 | AUD1 | 4 | Audio channel 1 block finished |
|  7 | AUD0 | 4 | Audio channel 0 block finished |
|  6 | BLIT | 3 | Blitter finished |
|  5 | VERTB | 3 | Start of vertical blank |
|  4 | COPER | 3 | Copper |
|  3 | PORTS | 2 | I/O ports and timers |
|  2 | SOFT | 1 | Reserved for software-initiated interrupt |
|  1 | DSKBLK | 1 | Disk block finished |
|  0 | TBE | 1 | Serial port transmit buffer empty |

---

### DSKPTH
**Disk pointer (high 3 bits, 5 bits if ECS)**

- **Address**: `$020` (`$DFF020`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Address register pair (must be even, chip memory), Not writable by Copper

---

### DSKPTL
**Disk pointer (low 15 bits)**

- **Address**: `$022` (`$DFF022`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Not writable by Copper

---

### DSKLEN
**Disk length**

- **Address**: `$024` (`$DFF024`)
- **Access**: W
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | DMAEN | Disk DMA enable |
| 14 | WRITE | Disk write (RAM to disk) if 1 |
| 13 | LENGTH | Bits 13-0: LENGTH |
| 12 | LENGTH | Bits 13-0: LENGTH |
| 11 | LENGTH | Bits 13-0: LENGTH |
| 10 | LENGTH | Bits 13-0: LENGTH |
|  9 | LENGTH | Bits 13-0: LENGTH |
|  8 | LENGTH | Bits 13-0: LENGTH |
|  7 | LENGTH | Bits 13-0: LENGTH |
|  6 | LENGTH | Bits 13-0: LENGTH |
|  5 | LENGTH | Bits 13-0: LENGTH |
|  4 | LENGTH | Bits 13-0: LENGTH |
|  3 | LENGTH | Bits 13-0: LENGTH |
|  2 | LENGTH | Bits 13-0: LENGTH |
|  1 | LENGTH | Bits 13-0: LENGTH |
|  0 | LENGTH | Bits 13-0: LENGTH |

---

### DSKDAT
**Disk DMA data write**

- **Address**: `$026` (`$DFF026`)
- **Access**: W
- **Chip**: P
- **Flags**: DMA channel only, Not writable by Copper

---

### REFPTR
**Refresh pointer**

- **Address**: `$028` (`$DFF028`)
- **Access**: W
- **Chip**: A
- **Flags**: DMA channel only, Not writable by Copper

---

### VPOSW
**Write vert most signif. bit (and frame flop)**

- **Address**: `$02A` (`$DFF02A`)
- **Access**: W
- **Chip**: A
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | USE |  |
| 14 | LOF-- |  |
|  8 | --,-- |  |
|  1 | V8 |  |

---

### VHPOSW
**Write vert and horiz position of beam**

- **Address**: `$02C` (`$DFF02C`)
- **Access**: W
- **Chip**: A
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | USE |  |
| 14 | V7 |  |
| 13 | V6 |  |
| 12 | V5 |  |
| 11 | V4 |  |
| 10 | V3 |  |
|  9 | V2 |  |
|  8 | V1 |  |
|  7 | V0,H8 |  |
|  6 | H7 |  |
|  5 | H6 |  |
|  4 | H5 |  |
|  3 | H4 |  |
|  2 | H3 |  |
|  1 | H2 |  |
|  0 | H1 |  |

---

### COPCON
**Coprocessor control register (CDANG)**

- **Address**: `$02E` (`$DFF02E`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
|  1 | CDANG | Copper danger mode. Allows Copper access to blitter if true. |

---

### SERDAT
**Serial port data and stop bits write**

- **Address**: `$030` (`$DFF030`)
- **Access**: W
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | 0 |  |
| 15 | OVRUN | Serial port receiver overrun. Reset by resetting bit 11 of INTREQ . |
| 14 | 0 |  |
| 14 | RBF | Serial port receive buffer full (mirror). |
| 13 | 0 |  |
| 13 | TBE | Serial port transmit buffer empty (mirror). |
| 12 | 0 |  |
| 12 | TSRE | Serial port transmit shift register empty. Reset by loading into buffer. |
| 11 | 0 |  |
| 11 | RXD | RXD pin receives UART serial data for direct bit test by the microprocessor. |
| 10 | 0 |  |
| 10 | 0 | Not used |
|  9 | S |  |
|  9 | STP | Stop bit |
|  8 | D8 |  |
|  8 | STP-DB8 | Stop bit if LONG, data bit if not. |
|  7 | D7 |  |
|  7 | DB7 | Data bit |
|  6 | D6 |  |
|  6 | DB6 | Data bit |
|  5 | D5 |  |
|  5 | DB5 | Data bit |
|  4 | D4 |  |
|  4 | DB4 | Data bit |
|  3 | D3 |  |
|  3 | DB3 | Data bit |
|  2 | D2 |  |
|  2 | DB2 | Data bit |
|  1 | D1 |  |
|  1 | DB1 | Data bit |
|  0 | D0 |  |
|  0 | DB0 | Data bit |

---

### SERPER
**Serial port period and control**

- **Address**: `$032` (`$DFF032`)
- **Access**: W
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | LONG | Defines serial receive as 9-bit word. |
| 14 | RATE | Bits 14-0: RATE |
| 13 | RATE | Bits 14-0: RATE |
| 12 | RATE | Bits 14-0: RATE |
| 11 | RATE | Bits 14-0: RATE |
| 10 | RATE | Bits 14-0: RATE |
|  9 | RATE | Bits 14-0: RATE |
|  8 | RATE | Bits 14-0: RATE |
|  7 | RATE | Bits 14-0: RATE |
|  6 | RATE | Bits 14-0: RATE |
|  5 | RATE | Bits 14-0: RATE |
|  4 | RATE | Bits 14-0: RATE |
|  3 | RATE | Bits 14-0: RATE |
|  2 | RATE | Bits 14-0: RATE |
|  1 | RATE | Bits 14-0: RATE |
|  0 | RATE | Bits 14-0: RATE |

---

### POTGO
**Pot port data write and start**

- **Address**: `$034` (`$DFF034`)
- **Access**: W
- **Chip**: P
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | OUTRY | Output enable for Paula pin 36 |
| 14 | DATRY | I/O data Paula pin 36 |
| 13 | OUTRX | Output enable for Paula pin 35 |
| 12 | DATRX | I/O data Paula pin 35 |
| 11 | OUTLY | Output enable for Paula pin 33 |
| 10 | DATLY | I/O data Paula pin 33 |
|  9 | OUTLX | Output enable for Paula pin 32 |
|  8 | DATLX | I/O data Paula pin 32 |
|  7 | 0 | Bits 7-1: 0 |
|  6 | 0 | Bits 7-1: 0 |
|  5 | 0 | Bits 7-1: 0 |
|  4 | 0 | Bits 7-1: 0 |
|  3 | 0 | Bits 7-1: 0 |
|  2 | 0 | Bits 7-1: 0 |
|  1 | 0 | Bits 7-1: 0 |
|  0 | START | Start pots (dump capacitors, start counters) |

---

### JOYTEST
**Write to all four joystick-mouse counters**

- **Address**: `$036` (`$DFF036`)
- **Access**: W
- **Chip**: D
- **Flags**: Not writable by Copper

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Y7 |  |
| 14 | Y6 |  |
| 13 | Y5 |  |
| 12 | Y4 |  |
| 11 | Y3 |  |
| 10 | Y2 |  |
|  9 | xx |  |
|  8 | xx |  |
|  7 | X7 |  |
|  6 | X6 |  |
|  5 | X5 |  |
|  4 | X4 |  |
|  3 | X3 |  |
|  2 | X2 |  |
|  1 | xx |  |
|  0 | xx |  |

---

### STREQU
**Strobe for horiz sync with VB and EQU**

- **Address**: `$038` (`$DFF038`)
- **Access**: S
- **Chip**: D
- **Flags**: DMA channel only, Not writable by Copper

---

### STRVBL
**Strobe for horiz sync with VB (vert. blank)**

- **Address**: `$03A` (`$DFF03A`)
- **Access**: S
- **Chip**: D
- **Flags**: DMA channel only, Not writable by Copper

---

### STRHOR
**Strobe for horiz sync**

- **Address**: `$03C` (`$DFF03C`)
- **Access**: S
- **Chip**: DP
- **Flags**: DMA channel only, Not writable by Copper

---

### STRLONG
**Strobe for identification of long**

- **Address**: `$03E` (`$DFF03E`)
- **Access**: S
- **Chip**: D
- **ECS**: Yes
- **Flags**: DMA channel only, Not writable by Copper

---

### BLTCON0
**Blitter control register 0**

- **Address**: `$040` (`$DFF040`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

| Bit | Name | Description |
|-----|------|-------------|
| 15 | ASH3 | BSH3 |
| 14 | ASH2 | BSH2 |
| 13 | ASH1 | BSH1 |
| 12 | ASA0 | BSH0 |
| 11 | USEA | X |
| 10 | USEB | X |
|  9 | USEC | X |
|  8 | USED | X |
|  7 | LF7 | DOFF |
|  6 | LF6 | X |
|  5 | LF5 | X |
|  4 | LF4 | EFE |
|  3 | LF3 | IFE |
|  2 | LF2 | FCI |
|  1 | LF1 | DESC |
|  0 | LF0 | LINE(=0) |

---

### BLTCON1
**Blitter control register 1**

- **Address**: `$042` (`$DFF042`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Copper-writable only with COPCON danger bit set

| Bit | Name | Description |
|-----|------|-------------|
| 15 | ASH3 | BSH3 |
| 14 | ASH2 | BSH2 |
| 13 | ASH1 | BSH1 |
| 12 | ASA0 | BSH0 |
| 11 | USEA | X |
| 10 | USEB | X |
|  9 | USEC | X |
|  8 | USED | X |
|  7 | LF7 | DOFF |
|  6 | LF6 | X |
|  5 | LF5 | X |
|  4 | LF4 | EFE |
|  3 | LF3 | IFE |
|  2 | LF2 | FCI |
|  1 | LF1 | DESC |
|  0 | LF0 | LINE(=0) |

---

### BLTAFWM
**Blitter first word mask for source A**

- **Address**: `$044` (`$DFF044`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTALWM
**Blitter last word mask for source A**

- **Address**: `$046` (`$DFF046`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTCPTH
**Blitter pointer to source C (high 3 bits)**

- **Address**: `$048` (`$DFF048`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTCPTL
**Blitter pointer to source C (low 15 bits)**

- **Address**: `$04A` (`$DFF04A`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTBPTH
**Blitter pointer to source B (high 3 bits)**

- **Address**: `$04C` (`$DFF04C`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTBPTL
**Blitter pointer to source B (low 15 bits)**

- **Address**: `$04E` (`$DFF04E`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTAPTH
**Blitter pointer to source A (high 3 bits)**

- **Address**: `$050` (`$DFF050`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTAPTL
**Blitter pointer to source A (low 15 bits)**

- **Address**: `$052` (`$DFF052`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTDPTH
**Blitter pointer to destination D**

- **Address**: `$054` (`$DFF054`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTDPTL
**Blitter pointer to destination D**

- **Address**: `$056` (`$DFF056`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory), Copper-writable only with COPCON danger bit set

---

### BLTSIZE
**Blitter start and size (window width,height)**

- **Address**: `$058` (`$DFF058`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

| Bit | Name | Description |
|-----|------|-------------|
| 15 | h9 |  |
| 14 | h8 |  |
| 13 | h7 |  |
| 12 | h6 |  |
| 11 | h5 |  |
| 10 | h4 |  |
|  9 | h3 |  |
|  8 | h2 |  |
|  7 | h1 |  |
|  6 | h0,w5 |  |
|  5 | w4 |  |
|  4 | w3 |  |
|  3 | w2 |  |
|  2 | w1 |  |
|  1 | w0 |  |

---

### BLTCON0L
**Blitter control 0, lower 8 bits (minterms)**

- **Address**: `$05A` (`$DFF05A`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTSIZV
**Blitter V size (for 15 bit vertical size)**

- **Address**: `$05C` (`$DFF05C`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Copper-writable only with COPCON danger bit set

| Bit | Name | Description |
|-----|------|-------------|
| 15 | h9 |  |
| 14 | h8 |  |
| 13 | h7 |  |
| 12 | h6 |  |
| 11 | h5 |  |
| 10 | h4 |  |
|  9 | h3 |  |
|  8 | h2 |  |
|  7 | h1 |  |
|  6 | h0,w5 |  |
|  5 | w4 |  |
|  4 | w3 |  |
|  3 | w2 |  |
|  2 | w1 |  |
|  1 | w0 |  |

---

### BLTSIZH
**Blitter H size and start (for 11 bit H size)**

- **Address**: `$05E` (`$DFF05E`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Copper-writable only with COPCON danger bit set

| Bit | Name | Description |
|-----|------|-------------|
| 15 | h9 |  |
| 14 | h8 |  |
| 13 | h7 |  |
| 12 | h6 |  |
| 11 | h5 |  |
| 10 | h4 |  |
|  9 | h3 |  |
|  8 | h2 |  |
|  7 | h1 |  |
|  6 | h0,w5 |  |
|  5 | w4 |  |
|  4 | w3 |  |
|  3 | w2 |  |
|  2 | w1 |  |
|  1 | w0 |  |

---

### BLTCMOD
**Blitter modulo for source C**

- **Address**: `$060` (`$DFF060`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTBMOD
**Blitter modulo for source B**

- **Address**: `$062` (`$DFF062`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTAMOD
**Blitter modulo for source A**

- **Address**: `$064` (`$DFF064`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTDMOD
**Blitter modulo for destination D**

- **Address**: `$066` (`$DFF066`)
- **Access**: W
- **Chip**: A
- **Flags**: Copper-writable only with COPCON danger bit set

---

### BLTCDAT
**Blitter source C data register**

- **Address**: `$070` (`$DFF070`)
- **Access**: W
- **Chip**: A
- **Flags**: DMA channel usually, processor sometimes, Copper-writable only with COPCON danger bit set

---

### BLTBDAT
**Blitter source B data register**

- **Address**: `$072` (`$DFF072`)
- **Access**: W
- **Chip**: A
- **Flags**: DMA channel usually, processor sometimes, Copper-writable only with COPCON danger bit set

---

### BLTADAT
**Blitter source A data register**

- **Address**: `$074` (`$DFF074`)
- **Access**: W
- **Chip**: A
- **Flags**: DMA channel usually, processor sometimes, Copper-writable only with COPCON danger bit set

---

### SPRHDAT
**Ext. logic UHRES sprite pointer and data id**

- **Address**: `$078` (`$DFF078`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Copper-writable only with COPCON danger bit set

---

### DENISEID
**Chip revision level for Denise**

- **Address**: `$07C` (`$DFF07C`)
- **Access**: R
- **Chip**: D
- **ECS**: Yes
- **Flags**: Copper-writable only with COPCON danger bit set

---

### DSKSYNC
**Disk sync pattern register for disk read**

- **Address**: `$07E` (`$DFF07E`)
- **Access**: W
- **Chip**: P
- **Flags**: Copper-writable only with COPCON danger bit set

---

### COP1LCH
**Coprocessor first location register**

- **Address**: `$080` (`$DFF080`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Address register pair (must be even, chip memory)

---

### COP1LCL
**Coprocessor first location register**

- **Address**: `$082` (`$DFF082`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### COP2LCH
**Coprocessor second location register**

- **Address**: `$084` (`$DFF084`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Address register pair (must be even, chip memory)

---

### COP2LCL
**Coprocessor second location register**

- **Address**: `$086` (`$DFF086`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### COPJMP1
**Coprocessor restart at first location**

- **Address**: `$088` (`$DFF088`)
- **Access**: S
- **Chip**: A

---

### COPJMP2
**Coprocessor restart at second location**

- **Address**: `$08A` (`$DFF08A`)
- **Access**: S
- **Chip**: A

---

### COPINS
**Coprocessor instruction fetch identify**

- **Address**: `$08C` (`$DFF08C`)
- **Access**: W
- **Chip**: A

| Bit | Name | Description |
|-----|------|-------------|
| 15 | X | RD15     VP7    BFD *   VP7    BFD * |
| 14 | X | RD14     VP6    VE6     VP6    VE6 |
| 13 | X | RD13     VP5    VE5     VP5    VE5 |
| 12 | X | RD12     VP4    VE4     VP4    VE4 |
| 11 | X | RD11     VP3    VE3     VP3    VE3 |
| 10 | X | RD10     VP2    VE2     VP2    VE2 |
|  9 | X | RD09     VP1    VE1     VP1    VE1 |
|  8 | DA8 | RD08     VP0    VE0     VP0    VE0 |
|  7 | DA7 | RD07     HP8    HE8     HP8    HE8 |
|  6 | DA6 | RD06     HP7    HE7     HP7    HE7 |
|  5 | DA5 | RD05     HP6    HE6     HP6    HE6 |
|  4 | DA4 | RD04     HP5    HE5     HP5    HE5 |
|  3 | DA3 | RD03     HP4    HE4     HP4    HE4 |
|  2 | DA2 | RD02     HP3    HE3     HP3    HE3 |
|  1 | DA1 | RD01     HP2    HE2     HP2    HE2 |
|  0 | 0 | RD00      1      0       1      1 |

---

### DIWSTRT
**Display window start (upper left**

- **Address**: `$08E` (`$DFF08E`)
- **Access**: W
- **Chip**: A

| Bit | Name | Description |
|-----|------|-------------|
| 15 | V7 |  |
| 14 | V6 |  |
| 13 | V5 |  |
| 12 | V4 |  |
| 11 | V3 |  |
| 10 | V2 |  |
|  9 | V1 |  |
|  8 | V0 |  |
|  7 | H7 |  |
|  6 | H6 |  |
|  5 | H5 |  |
|  4 | H4 |  |
|  3 | H3 |  |
|  2 | H2 |  |
|  1 | H1 |  |
|  0 | H0 |  |

---

### DIWSTOP
**Display window stop (lower right**

- **Address**: `$090` (`$DFF090`)
- **Access**: W
- **Chip**: A

| Bit | Name | Description |
|-----|------|-------------|
| 15 | V7 |  |
| 14 | V6 |  |
| 13 | V5 |  |
| 12 | V4 |  |
| 11 | V3 |  |
| 10 | V2 |  |
|  9 | V1 |  |
|  8 | V0 |  |
|  7 | H7 |  |
|  6 | H6 |  |
|  5 | H5 |  |
|  4 | H4 |  |
|  3 | H3 |  |
|  2 | H2 |  |
|  1 | H1 |  |
|  0 | H0 |  |

---

### DDFSTRT
**Display bitplane data fetch start**

- **Address**: `$092` (`$DFF092`)
- **Access**: W
- **Chip**: A

| Bit | Name | Description |
|-----|------|-------------|
|  7 | H8 |  |
|  6 | H7 |  |
|  5 | H6 |  |
|  4 | H5 |  |
|  3 | H4 |  |
|  2 | H3 |  |

---

### DDFSTOP
**Display bitplane data fetch stop**

- **Address**: `$094` (`$DFF094`)
- **Access**: W
- **Chip**: A

| Bit | Name | Description |
|-----|------|-------------|
|  7 | H8 |  |
|  6 | H7 |  |
|  5 | H6 |  |
|  4 | H5 |  |
|  3 | H4 |  |
|  2 | H3 |  |

---

### DMACON
**DMA control write (clear or set)**

- **Address**: `$096` (`$DFF096`)
- **Access**: W
- **Chip**: ADP

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SET/CLR | Set/clear control bit. Determines if bits written with a 1 get set or cleared.  Bits written with a zero are unchanged. |
| 14 | BBUSY | Blitter busy status bit (read only) |
| 13 | BZERO | Blitter logic  zero status bit (read only). |
| 12 | X |  |
| 11 | X |  |
| 10 | BLTPRI | Blitter DMA priority (over CPU micro) (also called "blitter nasty") (disables /BLS pin, preventing micro from stealing any bus cycles while blitter DMA is running). |
|  9 | DMAEN | Enable all DMA below |
|  8 | BPLEN | Bitplane DMA enable |
|  7 | COPEN | Copper DMA enable |
|  6 | BLTEN | Blitter DMA enable |
|  5 | SPREN | Sprite DMA enable |
|  4 | DSKEN | Disk DMA enable |
|  3 | AUD3EN | Audio channel 3 DMA enable |
|  2 | AUD2EN | Audio channel 2 DMA enable |
|  1 | AUD1EN | Audio channel 1 DMA enable |
|  0 | AUD0EN | Audio channel 0 DMA enable |

---

### CLXCON
**Collision control**

- **Address**: `$098` (`$DFF098`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 15 | ENSP7 | Enable sprite 7 (ORed with sprite 6) |
| 14 | ENSP5 | Enable sprite 5 (ORed with sprite 4) |
| 13 | ENSP3 | Enable sprite 3 (ORed with sprite 2) |
| 12 | ENSP1 | Enable sprite 1 (ORed with sprite 0) |
| 11 | ENBP6 | Enable bitplane 6 (match required for collision) |
| 10 | ENBP5 | Enable bitplane 5 (match required for collision) |
|  9 | ENBP4 | Enable bitplane 4 (match required for collision) |
|  8 | ENBP3 | Enable bitplane 3 (match required for collision) |
|  7 | ENBP2 | Enable bitplane 2 (match required for collision) |
|  6 | ENBP1 | Enable bitplane 1 (match required for collision) |
|  5 | MVBP6 | Match value for bitplane 6 collision |
|  4 | MVBP5 | Match value for bitplane 5 collision |
|  3 | MVBP4 | Match value for bitplane 4 collision |
|  2 | MVBP3 | Match value for bitplane 3 collision |
|  1 | MVBP2 | Match value for bitplane 2 collision |
|  0 | MVBP1 | Match value for bitplane 1 collision NOTE:  Disabled bitplanes cannot prevent collisions.  Therefore if all bitplanes are disabled, collisions will be continuous, regardless of the match values. |

---

### INTENA
**Interrupt enable bits (clear or**

- **Address**: `$09A` (`$DFF09A`)
- **Access**: W
- **Chip**: P

| Bit | Name | Level | Description |
|-----|------|-------|-------------|
| 15 | SET/CLR |  | Set/clear control bit. Determines if bits written with a 1 get set or cleared. Bits written with a zero are always unchanged. |
| 14 | INTEN |  | Master interrupt (enable only, no request) |
| 13 | EXTER | 6 | External interrupt |
| 12 | DSKSYN | 5 | Disk sync register ( DSKSYNC ) matches disk data |
| 11 | RBF | 5 | Serial port receive buffer full |
| 10 | AUD3 | 4 | Audio channel 3 block finished |
|  9 | AUD2 | 4 | Audio channel 2 block finished |
|  8 | AUD1 | 4 | Audio channel 1 block finished |
|  7 | AUD0 | 4 | Audio channel 0 block finished |
|  6 | BLIT | 3 | Blitter finished |
|  5 | VERTB | 3 | Start of vertical blank |
|  4 | COPER | 3 | Copper |
|  3 | PORTS | 2 | I/O ports and timers |
|  2 | SOFT | 1 | Reserved for software-initiated interrupt |
|  1 | DSKBLK | 1 | Disk block finished |
|  0 | TBE | 1 | Serial port transmit buffer empty |

---

### INTREQ
**Interrupt request bits (clear or**

- **Address**: `$09C` (`$DFF09C`)
- **Access**: W
- **Chip**: P

| Bit | Name | Level | Description |
|-----|------|-------|-------------|
| 15 | SET/CLR |  | Set/clear control bit. Determines if bits written with a 1 get set or cleared. Bits written with a zero are always unchanged. |
| 14 | INTEN |  | Master interrupt (enable only, no request) |
| 13 | EXTER | 6 | External interrupt |
| 12 | DSKSYN | 5 | Disk sync register ( DSKSYNC ) matches disk data |
| 11 | RBF | 5 | Serial port receive buffer full |
| 10 | AUD3 | 4 | Audio channel 3 block finished |
|  9 | AUD2 | 4 | Audio channel 2 block finished |
|  8 | AUD1 | 4 | Audio channel 1 block finished |
|  7 | AUD0 | 4 | Audio channel 0 block finished |
|  6 | BLIT | 3 | Blitter finished |
|  5 | VERTB | 3 | Start of vertical blank |
|  4 | COPER | 3 | Copper |
|  3 | PORTS | 2 | I/O ports and timers |
|  2 | SOFT | 1 | Reserved for software-initiated interrupt |
|  1 | DSKBLK | 1 | Disk block finished |
|  0 | TBE | 1 | Serial port transmit buffer empty |

---

### ADKCON
**Audio, disk, UART control**

- **Address**: `$09E` (`$DFF09E`)
- **Access**: W
- **Chip**: P

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SET/CLR | Set/clear control bit. Determines if bits written with a 1 get set or cleared. Bits written with a zero are always unchanged. |
| 14 | PRECOMP | Bits 14-13: PRECOMP |
| 13 | PRECOMP | Bits 14-13: PRECOMP |

---

### AUD0LCH
**Audio channel 0 location (high 3 bits,**

- **Address**: `$0A0` (`$DFF0A0`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD0LCL
**Audio channel 0 location (low 15 bits)**

- **Address**: `$0A2` (`$DFF0A2`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD0LEN
**Audio channel 0 length**

- **Address**: `$0A4` (`$DFF0A4`)
- **Access**: W
- **Chip**: P

---

### AUD0PER
**Audio channel 0 period**

- **Address**: `$0A6` (`$DFF0A6`)
- **Access**: W
- **Chip**: P
- **ECS**: Yes

---

### AUD0VOL
**Audio channel 0 volume**

- **Address**: `$0A8` (`$DFF0A8`)
- **Access**: W
- **Chip**: P

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Not | Bits 15-7: Not |
| 14 | Not | Bits 15-7: Not |
| 13 | Not | Bits 15-7: Not |
| 12 | Not | Bits 15-7: Not |
| 11 | Not | Bits 15-7: Not |
| 10 | Not | Bits 15-7: Not |
|  9 | Not | Bits 15-7: Not |
|  8 | Not | Bits 15-7: Not |
|  7 | Not | Bits 15-7: Not |
|  6 | Forces | volume to max (64 ones, no zeros) |
|  5 | Sets | Bits 5-0: Sets |
|  4 | Sets | Bits 5-0: Sets |
|  3 | Sets | Bits 5-0: Sets |
|  2 | Sets | Bits 5-0: Sets |
|  1 | Sets | Bits 5-0: Sets |
|  0 | Sets | Bits 5-0: Sets |

---

### AUD0DAT
**Audio channel 0 data**

- **Address**: `$0AA` (`$DFF0AA`)
- **Access**: W
- **Chip**: P
- **Flags**: DMA channel only

---

### AUD1LCH
**Audio channel 1 location (high 3 bits)**

- **Address**: `$0B0` (`$DFF0B0`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD1LCL
**Audio channel 1 location (low 15 bits)**

- **Address**: `$0B2` (`$DFF0B2`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD1LEN
**Audio channel 1 length**

- **Address**: `$0B4` (`$DFF0B4`)
- **Access**: W
- **Chip**: P

---

### AUD1PER
**Audio channel 1 period**

- **Address**: `$0B6` (`$DFF0B6`)
- **Access**: W
- **Chip**: P

---

### AUD1VOL
**Audio channel 1 volume**

- **Address**: `$0B8` (`$DFF0B8`)
- **Access**: W
- **Chip**: P

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Not | Bits 15-7: Not |
| 14 | Not | Bits 15-7: Not |
| 13 | Not | Bits 15-7: Not |
| 12 | Not | Bits 15-7: Not |
| 11 | Not | Bits 15-7: Not |
| 10 | Not | Bits 15-7: Not |
|  9 | Not | Bits 15-7: Not |
|  8 | Not | Bits 15-7: Not |
|  7 | Not | Bits 15-7: Not |
|  6 | Forces | volume to max (64 ones, no zeros) |
|  5 | Sets | Bits 5-0: Sets |
|  4 | Sets | Bits 5-0: Sets |
|  3 | Sets | Bits 5-0: Sets |
|  2 | Sets | Bits 5-0: Sets |
|  1 | Sets | Bits 5-0: Sets |
|  0 | Sets | Bits 5-0: Sets |

---

### AUD1DAT
**Audio channel 1 data**

- **Address**: `$0BA` (`$DFF0BA`)
- **Access**: W
- **Chip**: P
- **Flags**: DMA channel only

---

### AUD2LCH
**Audio channel 2 location (high 3 bits)**

- **Address**: `$0C0` (`$DFF0C0`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD2LCL
**Audio channel 2 location (low 15 bits)**

- **Address**: `$0C2` (`$DFF0C2`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD2LEN
**Audio channel 2 length**

- **Address**: `$0C4` (`$DFF0C4`)
- **Access**: W
- **Chip**: P

---

### AUD2PER
**Audio channel 2 period**

- **Address**: `$0C6` (`$DFF0C6`)
- **Access**: W
- **Chip**: P

---

### AUD2VOL
**Audio channel 2 volume**

- **Address**: `$0C8` (`$DFF0C8`)
- **Access**: W
- **Chip**: P

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Not | Bits 15-7: Not |
| 14 | Not | Bits 15-7: Not |
| 13 | Not | Bits 15-7: Not |
| 12 | Not | Bits 15-7: Not |
| 11 | Not | Bits 15-7: Not |
| 10 | Not | Bits 15-7: Not |
|  9 | Not | Bits 15-7: Not |
|  8 | Not | Bits 15-7: Not |
|  7 | Not | Bits 15-7: Not |
|  6 | Forces | volume to max (64 ones, no zeros) |
|  5 | Sets | Bits 5-0: Sets |
|  4 | Sets | Bits 5-0: Sets |
|  3 | Sets | Bits 5-0: Sets |
|  2 | Sets | Bits 5-0: Sets |
|  1 | Sets | Bits 5-0: Sets |
|  0 | Sets | Bits 5-0: Sets |

---

### AUD2DAT
**Audio channel 2 data**

- **Address**: `$0CA` (`$DFF0CA`)
- **Access**: W
- **Chip**: P
- **Flags**: DMA channel only

---

### AUD3LCH
**Audio channel 3 location (high 3 bits)**

- **Address**: `$0D0` (`$DFF0D0`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD3LCL
**Audio channel 3 location (low 15 bits)**

- **Address**: `$0D2` (`$DFF0D2`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### AUD3LEN
**Audio channel 3 length**

- **Address**: `$0D4` (`$DFF0D4`)
- **Access**: W
- **Chip**: P

---

### AUD3PER
**Audio channel 3 period**

- **Address**: `$0D6` (`$DFF0D6`)
- **Access**: W
- **Chip**: P

---

### AUD3VOL
**Audio channel 3 volume**

- **Address**: `$0D8` (`$DFF0D8`)
- **Access**: W
- **Chip**: P

| Bit | Name | Description |
|-----|------|-------------|
| 15 | Not | Bits 15-7: Not |
| 14 | Not | Bits 15-7: Not |
| 13 | Not | Bits 15-7: Not |
| 12 | Not | Bits 15-7: Not |
| 11 | Not | Bits 15-7: Not |
| 10 | Not | Bits 15-7: Not |
|  9 | Not | Bits 15-7: Not |
|  8 | Not | Bits 15-7: Not |
|  7 | Not | Bits 15-7: Not |
|  6 | Forces | volume to max (64 ones, no zeros) |
|  5 | Sets | Bits 5-0: Sets |
|  4 | Sets | Bits 5-0: Sets |
|  3 | Sets | Bits 5-0: Sets |
|  2 | Sets | Bits 5-0: Sets |
|  1 | Sets | Bits 5-0: Sets |
|  0 | Sets | Bits 5-0: Sets |

---

### AUD3DAT
**Audio channel 3 data**

- **Address**: `$0DA` (`$DFF0DA`)
- **Access**: W
- **Chip**: P
- **Flags**: DMA channel only

---

### BPL1PTH
**Bitplane 1 pointer (high 3 bits)**

- **Address**: `$0E0` (`$DFF0E0`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL1PTL
**Bitplane 1 pointer (low 15 bits)**

- **Address**: `$0E2` (`$DFF0E2`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL2PTH
**Bitplane 2 pointer (high 3 bits)**

- **Address**: `$0E4` (`$DFF0E4`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL2PTL
**Bitplane 2 pointer (low 15 bits)**

- **Address**: `$0E6` (`$DFF0E6`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL3PTH
**Bitplane 3 pointer (high 3 bits)**

- **Address**: `$0E8` (`$DFF0E8`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL3PTL
**Bitplane 3 pointer (low 15 bits)**

- **Address**: `$0EA` (`$DFF0EA`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL4PTH
**Bitplane 4 pointer (high 3 bits)**

- **Address**: `$0EC` (`$DFF0EC`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL4PTL
**Bitplane 4 pointer (low 15 bits)**

- **Address**: `$0EE` (`$DFF0EE`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL5PTH
**Bitplane 5 pointer (high 3 bits)**

- **Address**: `$0F0` (`$DFF0F0`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL5PTL
**Bitplane 5 pointer (low 15 bits)**

- **Address**: `$0F2` (`$DFF0F2`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL6PTH
**Bitplane 6 pointer (high 3 bits)**

- **Address**: `$0F4` (`$DFF0F4`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPL6PTL
**Bitplane 6 pointer (low 15 bits)**

- **Address**: `$0F6` (`$DFF0F6`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### BPLCON0
**Bitplane control register**

- **Address**: `$100` (`$DFF100`)
- **Access**: W
- **Chip**: AD
- **ECS**: Yes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | HIRES | X           X |
| 14 | BPU2 | X           X |
| 13 | BPU1 | X           X |
| 12 | BPU0 | X           X |
| 11 | HOMOD | X           X |
| 10 | DBLPF | X           X |
|  9 | COLOR | X           X |
|  8 | GAUD | X           X |
|  7 | X | PF2H3        X |
|  6 | X | PF2H2      PF2PRI |
|  5 | X | PF2H1      PF2P2 |
|  4 | X | PF2H0      PF2P1 |
|  3 | LPEN | PF1H3      PF2P0 |
|  2 | LACE | PF1H2      PF1P2 |
|  1 | ERSY | PF1H1      PF1P1 |
|  0 | X | PF1H0      PF1P0 |

---

### BPLCON1
**Bitplane control reg.**

- **Address**: `$102` (`$DFF102`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 15 | HIRES | X           X |
| 14 | BPU2 | X           X |
| 13 | BPU1 | X           X |
| 12 | BPU0 | X           X |
| 11 | HOMOD | X           X |
| 10 | DBLPF | X           X |
|  9 | COLOR | X           X |
|  8 | GAUD | X           X |
|  7 | X | PF2H3        X |
|  6 | X | PF2H2      PF2PRI |
|  5 | X | PF2H1      PF2P2 |
|  4 | X | PF2H0      PF2P1 |
|  3 | LPEN | PF1H3      PF2P0 |
|  2 | LACE | PF1H2      PF1P2 |
|  1 | ERSY | PF1H1      PF1P1 |
|  0 | X | PF1H0      PF1P0 |

---

### BPLCON2
**Bitplane control reg. (priority control)**

- **Address**: `$104` (`$DFF104`)
- **Access**: W
- **Chip**: D
- **ECS**: Yes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | HIRES | X           X |
| 14 | BPU2 | X           X |
| 13 | BPU1 | X           X |
| 12 | BPU0 | X           X |
| 11 | HOMOD | X           X |
| 10 | DBLPF | X           X |
|  9 | COLOR | X           X |
|  8 | GAUD | X           X |
|  7 | X | PF2H3        X |
|  6 | X | PF2H2      PF2PRI |
|  5 | X | PF2H1      PF2P2 |
|  4 | X | PF2H0      PF2P1 |
|  3 | LPEN | PF1H3      PF2P0 |
|  2 | LACE | PF1H2      PF1P2 |
|  1 | ERSY | PF1H1      PF1P1 |
|  0 | X | PF1H0      PF1P0 |

---

### BPLCON3
**Bitplane control (enhanced features)**

- **Address**: `$106` (`$DFF106`)
- **Access**: W
- **Chip**: D
- **ECS**: Yes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | HIRES | X           X |
| 14 | BPU2 | X           X |
| 13 | BPU1 | X           X |
| 12 | BPU0 | X           X |
| 11 | HOMOD | X           X |
| 10 | DBLPF | X           X |
|  9 | COLOR | X           X |
|  8 | GAUD | X           X |
|  7 | X | PF2H3        X |
|  6 | X | PF2H2      PF2PRI |
|  5 | X | PF2H1      PF2P2 |
|  4 | X | PF2H0      PF2P1 |
|  3 | LPEN | PF1H3      PF2P0 |
|  2 | LACE | PF1H2      PF1P2 |
|  1 | ERSY | PF1H1      PF1P1 |
|  0 | X | PF1H0      PF1P0 |

---

### BPL1MOD
**Bitplane modulo (odd planes)**

- **Address**: `$108` (`$DFF108`)
- **Access**: W
- **Chip**: A

---

### BPL2MOD
**Bitplane modulo (even planes)**

- **Address**: `$10A` (`$DFF10A`)
- **Access**: W
- **Chip**: A

---

### BPL1DAT
**Bitplane 1 data (parallel-to-serial convert)**

- **Address**: `$110` (`$DFF110`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel only

---

### BPL2DAT
**Bitplane 2 data (parallel-to-serial convert)**

- **Address**: `$112` (`$DFF112`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel only

---

### BPL3DAT
**Bitplane 3 data (parallel-to-serial convert)**

- **Address**: `$114` (`$DFF114`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel only

---

### BPL4DAT
**Bitplane 4 data (parallel-to-serial convert)**

- **Address**: `$116` (`$DFF116`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel only

---

### BPL5DAT
**Bitplane 5 data (parallel-to-serial convert)**

- **Address**: `$118` (`$DFF118`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel only

---

### BPL6DAT
**Bitplane 6 data (parallel-to-serial convert)**

- **Address**: `$11A` (`$DFF11A`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel only

---

### SPR0PTH
**Sprite 0 pointer (high 3 bits)**

- **Address**: `$120` (`$DFF120`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR0PTL
**Sprite 0 pointer (low 15 bits)**

- **Address**: `$122` (`$DFF122`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR1PTH
**Sprite 1 pointer (high 3 bits)**

- **Address**: `$124` (`$DFF124`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR1PTL
**Sprite 1 pointer (low 15 bits)**

- **Address**: `$126` (`$DFF126`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR2PTH
**Sprite 2 pointer (high 3 bits)**

- **Address**: `$128` (`$DFF128`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR2PTL
**Sprite 2 pointer (low 15 bits)**

- **Address**: `$12A` (`$DFF12A`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR3PTH
**Sprite 3 pointer (high 3 bits)**

- **Address**: `$12C` (`$DFF12C`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR3PTL
**Sprite 3 pointer (low 15 bits)**

- **Address**: `$12E` (`$DFF12E`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR4PTH
**Sprite 4 pointer (high 3 bits)**

- **Address**: `$130` (`$DFF130`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR4PTL
**Sprite 4 pointer (low 15 bits)**

- **Address**: `$132` (`$DFF132`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR5PTH
**Sprite 5 pointer (high 3 bits)**

- **Address**: `$134` (`$DFF134`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR5PTL
**Sprite 5 pointer (low 15 bits)**

- **Address**: `$136` (`$DFF136`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR6PTH
**Sprite 6 pointer (high 3 bits)**

- **Address**: `$138` (`$DFF138`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR6PTL
**Sprite 6 pointer (low 15 bits)**

- **Address**: `$13A` (`$DFF13A`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR7PTH
**Sprite 7 pointer (high 3 bits)**

- **Address**: `$13C` (`$DFF13C`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR7PTL
**Sprite 7 pointer (low 15 bits)**

- **Address**: `$13E` (`$DFF13E`)
- **Access**: W
- **Chip**: A
- **Flags**: Address register pair (must be even, chip memory)

---

### SPR0POS
**Sprite 0 vert-horiz start position**

- **Address**: `$140` (`$DFF140`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR0CTL
**Sprite 0 vert stop position and**

- **Address**: `$142` (`$DFF142`)
- **Access**: W
- **Chip**: AD
- **ECS**: Yes
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR0DATA
**Sprite 0 image data register A**

- **Address**: `$144` (`$DFF144`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR0DATB
**Sprite 0 image data register B**

- **Address**: `$146` (`$DFF146`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR1POS
**Sprite 1 vert-horiz start position**

- **Address**: `$148` (`$DFF148`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR1CTL
**Sprite 1 vert stop position and**

- **Address**: `$14A` (`$DFF14A`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR1DATA
**Sprite 1 image data register A**

- **Address**: `$14C` (`$DFF14C`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR1DATB
**Sprite 1 image data register B**

- **Address**: `$14E` (`$DFF14E`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR2POS
**Sprite 2 vert-horiz start position**

- **Address**: `$150` (`$DFF150`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR2CTL
**Sprite 2 vert stop position and**

- **Address**: `$152` (`$DFF152`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR2DATA
**Sprite 2 image data register A**

- **Address**: `$154` (`$DFF154`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR2DATB
**Sprite 2 image data register B**

- **Address**: `$156` (`$DFF156`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR3POS
**Sprite 3 vert-horiz start position**

- **Address**: `$158` (`$DFF158`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR3CTL
**Sprite 3 vert stop position and**

- **Address**: `$15A` (`$DFF15A`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR3DATA
**Sprite 3 image data register A**

- **Address**: `$15C` (`$DFF15C`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR3DATB
**Sprite 3 image data register B**

- **Address**: `$15E` (`$DFF15E`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR4POS
**Sprite 4 vert-horiz start position**

- **Address**: `$160` (`$DFF160`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR4CTL
**Sprite 4 vert stop position and**

- **Address**: `$162` (`$DFF162`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR4DATA
**Sprite 4 image data register A**

- **Address**: `$164` (`$DFF164`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR4DATB
**Sprite 4 image data register B**

- **Address**: `$166` (`$DFF166`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR5POS
**Sprite 5 vert-horiz start position**

- **Address**: `$168` (`$DFF168`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR5CTL
**Sprite 5 vert stop position and**

- **Address**: `$16A` (`$DFF16A`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR5DATA
**Sprite 5 image data register A**

- **Address**: `$16C` (`$DFF16C`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR5DATB
**Sprite 5 image data register B**

- **Address**: `$16E` (`$DFF16E`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR6POS
**Sprite 6 vert-horiz start position**

- **Address**: `$170` (`$DFF170`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR6CTL
**Sprite 6 vert stop position and**

- **Address**: `$172` (`$DFF172`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR6DATA
**Sprite 6 image data register A**

- **Address**: `$174` (`$DFF174`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR6DATB
**Sprite 6 image data register B**

- **Address**: `$176` (`$DFF176`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR7POS
**Sprite 7 vert-horiz start position**

- **Address**: `$178` (`$DFF178`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR7CTL
**Sprite 7 vert stop position and**

- **Address**: `$17A` (`$DFF17A`)
- **Access**: W
- **Chip**: AD
- **Flags**: DMA channel usually, processor sometimes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 15 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 14 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 14 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 13 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 13 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 12 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 12 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 11 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 11 | EV7-EV0 | Bits 15-8: EV7-EV0 |
| 10 | SV7-SV0 | Bits 15-8: SV7-SV0 |
| 10 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  9 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  9 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  8 | SV7-SV0 | Bits 15-8: SV7-SV0 |
|  8 | EV7-EV0 | Bits 15-8: EV7-EV0 |
|  7 | ATT | Sprite attach control bit (odd sprites) |
|  6 | X | Bits 6-4: X |
|  5 | X | Bits 6-4: X |
|  4 | X | Bits 6-4: X |
|  2 | SV8 | Start vertical value high bit |
|  1 | EV8 | End (stop) vertical value high bit |
|  0 | SH0 | Start horizontal value low bit |

---

### SPR7DATA
**Sprite 7 image data register A**

- **Address**: `$17C` (`$DFF17C`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### SPR7DATB
**Sprite 7 image data register B**

- **Address**: `$17E` (`$DFF17E`)
- **Access**: W
- **Chip**: D
- **Flags**: DMA channel usually, processor sometimes

---

### COLOR00
**Color table 00**

- **Address**: `$180` (`$DFF180`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR01
**Color table 01**

- **Address**: `$182` (`$DFF182`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR02
**Color table 02**

- **Address**: `$184` (`$DFF184`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR03
**Color table 03**

- **Address**: `$186` (`$DFF186`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR04
**Color table 04**

- **Address**: `$188` (`$DFF188`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR05
**Color table 05**

- **Address**: `$18A` (`$DFF18A`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR06
**Color table 06**

- **Address**: `$18C` (`$DFF18C`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR07
**Color table 07**

- **Address**: `$18E` (`$DFF18E`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR08
**Color table 08**

- **Address**: `$190` (`$DFF190`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR09
**Color table 09**

- **Address**: `$192` (`$DFF192`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR10
**Color table 10**

- **Address**: `$194` (`$DFF194`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR11
**Color table 11**

- **Address**: `$196` (`$DFF196`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR12
**Color table 12**

- **Address**: `$198` (`$DFF198`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR13
**Color table 13**

- **Address**: `$19A` (`$DFF19A`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR14
**Color table 14**

- **Address**: `$19C` (`$DFF19C`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR15
**Color table 15**

- **Address**: `$19E` (`$DFF19E`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR16
**Color table 16**

- **Address**: `$1A0` (`$DFF1A0`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR17
**Color table 17**

- **Address**: `$1A2` (`$DFF1A2`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR18
**Color table 18**

- **Address**: `$1A4` (`$DFF1A4`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR19
**Color table 19**

- **Address**: `$1A6` (`$DFF1A6`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR20
**Color table 20**

- **Address**: `$1A8` (`$DFF1A8`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR21
**Color table 21**

- **Address**: `$1AA` (`$DFF1AA`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR22
**Color table 22**

- **Address**: `$1AC` (`$DFF1AC`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR23
**Color table 23**

- **Address**: `$1AE` (`$DFF1AE`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR24
**Color table 24**

- **Address**: `$1B0` (`$DFF1B0`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR25
**Color table 25**

- **Address**: `$1B2` (`$DFF1B2`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR26
**Color table 26**

- **Address**: `$1B4` (`$DFF1B4`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR27
**Color table 27**

- **Address**: `$1B6` (`$DFF1B6`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR28
**Color table 28**

- **Address**: `$1B8` (`$DFF1B8`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR29
**Color table 29**

- **Address**: `$1BA` (`$DFF1BA`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR30
**Color table 30**

- **Address**: `$1BC` (`$DFF1BC`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### COLOR31
**Color table 31**

- **Address**: `$1BE` (`$DFF1BE`)
- **Access**: W
- **Chip**: D

| Bit | Name | Description |
|-----|------|-------------|
| 11 | R3 |  |
| 10 | R2 |  |
|  9 | R1 |  |
|  8 | R0 |  |
|  7 | G3 |  |
|  6 | G2 |  |
|  5 | G1 |  |
|  4 | G0 |  |
|  3 | B3 |  |
|  2 | B2 |  |
|  1 | B1 |  |
|  0 | B0 |  |

---

### HTOTAL
**Highest number count, horiz line**

- **Address**: `$1C0` (`$DFF1C0`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### HSSTOP
**Horizontal line position for HSYNC stop**

- **Address**: `$1C2` (`$DFF1C2`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### HBSTRT
**Horizontal line position for HBLANK start**

- **Address**: `$1C4` (`$DFF1C4`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### HBSTOP
**Horizontal line position for HBLANK stop**

- **Address**: `$1C6` (`$DFF1C6`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### VTOTAL
**Highest numbered vertical line**

- **Address**: `$1C8` (`$DFF1C8`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### VSSTOP
**Vertical line position for VSYNC stop**

- **Address**: `$1CA` (`$DFF1CA`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### VBSTRT
**Vertical line for VBLANK start**

- **Address**: `$1CC` (`$DFF1CC`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### VBSTOP
**Vertical line for VBLANK stop**

- **Address**: `$1CE` (`$DFF1CE`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### BEAMCON0
**Beam counter control register (SHRES,PAL)**

- **Address**: `$1DC` (`$DFF1DC`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | X |  |
| 14 | HARDDIS | Disable hardwired vertical/horizontal blank |
| 13 | LPENDIS | Ignore latched pen value on vertical pos read |
| 12 | VARVBEN | Use VBSTRT/STOP disable hard window stop |
| 11 | LOLDIS | Disable long line/short line toggle |
| 10 | CSCBEN | Composite sync redirection |
|  9 | VARVSYEN | Variable vertical sync enable |
|  8 | VARHSYEN | Variable horizontal sync enable |
|  7 | VARBEAMEN | Variable beam counter comparator enable |
|  6 | DUAL | Special ultra resolution mode enable |
|  5 | PAL | Programmable pal mode enable |
|  4 | VARCSYEN | Variable composite sync |
|  3 | BLANKEN | Composite blank redirection |
|  2 | CSYTRUE | Polarity control for C sync pin |
|  1 | VSYTRUE | Polarity control for V sync pin |
|  0 | HSYTRUE | Polarity control for H sync pin |

---

### HSSTRT
**Horizontal sync start (VARHSY)**

- **Address**: `$1DE` (`$DFF1DE`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### VSSTRT
**Vertical sync start   (VARVSY)**

- **Address**: `$1E0` (`$DFF1E0`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### HCENTER
**Horizontal position for Vsync on interlace**

- **Address**: `$1E2` (`$DFF1E2`)
- **Access**: W
- **Chip**: A
- **ECS**: Yes

---

### DIWHIGH
**Display window -  upper bits for start, stop**

- **Address**: `$1E4` (`$DFF1E4`)
- **Access**: W
- **Chip**: AD
- **ECS**: Yes

| Bit | Name | Description |
|-----|------|-------------|
| 15 | V7 |  |
| 14 | V6 |  |
| 13 | V5 |  |
| 12 | V4 |  |
| 11 | V3 |  |
| 10 | V2 |  |
|  9 | V1 |  |
|  8 | V0 |  |
|  7 | H7 |  |
|  6 | H6 |  |
|  5 | H5 |  |
|  4 | H4 |  |
|  3 | H3 |  |
|  2 | H2 |  |
|  1 | H1 |  |
|  0 | H0 |  |

---

### CIAA_PRA
**CIA-A: Peripheral Data Register A**

- **Address**: `$BFE001` (`$DFFBFE001`)
- **Access**: R/W
- **Chip**: CIA-A

| Bit | Name | Description |
|-----|------|-------------|
|  7 | PA7/FIRE1 | Game port 1, pin 6 (fire button) |
|  6 | PA6/FIRE0 | Game port 0, pin 6 (fire button) |
|  5 | PA5/DSKRDY | Disk ready (active low) |
|  4 | PA4/DSKTRACK0 | Disk track 00 detect (active low) |
|  3 | PA3/DSKPROT | Disk write protect (active low) |
|  2 | PA2/DSKCHANGE | Disk change (active low) |
|  1 | PA1/LED | Power LED (0=bright) |
|  0 | PA0/OVL | Memory overlay bit |

---

### CIAA_PRB
**CIA-A: Peripheral Data Register B**

- **Address**: `$BFE101` (`$DFFBFE101`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_DDRA
**CIA-A: Data Direction Register A**

- **Address**: `$BFE201` (`$DFFBFE201`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_DDRB
**CIA-A: Data Direction Register B**

- **Address**: `$BFE301` (`$DFFBFE301`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TALO
**CIA-A: Timer A Low**

- **Address**: `$BFE401` (`$DFFBFE401`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TAHI
**CIA-A: Timer A High**

- **Address**: `$BFE501` (`$DFFBFE501`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TBLO
**CIA-A: Timer B Low**

- **Address**: `$BFE601` (`$DFFBFE601`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TBHI
**CIA-A: Timer B High**

- **Address**: `$BFE701` (`$DFFBFE701`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TODLOW
**CIA-A: Event counter bits 7-0**

- **Address**: `$BFE801` (`$DFFBFE801`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TODMID
**CIA-A: Event counter bits 15-8**

- **Address**: `$BFE901` (`$DFFBFE901`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_TODHI
**CIA-A: Event counter bits 23-16**

- **Address**: `$BFEA01` (`$DFFBFEA01`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_SDR
**CIA-A: Serial Data Register**

- **Address**: `$BFEC01` (`$DFFBFEC01`)
- **Access**: R/W
- **Chip**: CIA-A

---

### CIAA_ICR
**CIA-A: Interrupt Control Register**

- **Address**: `$BFED01` (`$DFFBFED01`)
- **Access**: R/W
- **Chip**: CIA-A

| Bit | Name | Description |
|-----|------|-------------|
|  7 | IR/S/C | Interrupt (read) / Set-Clear (write) |
|  4 | FLG | FLAG pin interrupt |
|  3 | SP | Serial port interrupt |
|  2 | ALRM | TOD alarm interrupt |
|  1 | TB | Timer B underflow interrupt |
|  0 | TA | Timer A underflow interrupt |

---

### CIAA_CRA
**CIA-A: Control Register A**

- **Address**: `$BFEE01` (`$DFFBFEE01`)
- **Access**: R/W
- **Chip**: CIA-A

| Bit | Name | Description |
|-----|------|-------------|
|  7 | UNUSED |  |
|  6 | SPMODE | 1 = Serial port=output (CNT is the source of the shift clock) |
|  5 | INMODE | 1 = Timer A counts positive CNT transitions, |
|  4 | LOAD | 1 = force load (this is a strobe input, there is no data storage;  bit 4 will always read back a zero and writing a 0 has no effect.) |
|  3 | RUNMODE | 1 = one-shot mode, 0 = continuous mode. |
|  2 | OUTMODE | 1 = toggle, 0 = pulse. |
|  1 | PBON | 1 = Timer A output on PB6, 0 = PB6 is normal operation. |
|  0 | START | 1 = start Timer A, 0 = stop Timer A. This bit is automatically reset (= 0) when underflow occurs during one-shot mode. |
|  0 | = | Timer A counts 02 pulses. |
|  0 | = | Serial port=input  (external shift clock is required) |

---

### CIAA_CRB
**CIA-A: Control Register B**

- **Address**: `$BFEF01` (`$DFFBFEF01`)
- **Access**: R/W
- **Chip**: CIA-A

| Bit | Name | Description |
|-----|------|-------------|
|  4 | LOAD | 1 = force load (this is a strobe input, there is no data storage;  bit 4 will always read back a zero and writing a 0 has no effect.) |
|  3 | RUNMODE | 1 = one-shot mode, 0 = continuous mode. |
|  2 | OUTMODE | 1 = toggle, 0 = pulse. |
|  1 | PBON | 1 = Timer B output on PB7, 0 = PB7 is normal operation. |
|  0 | START | 1 = start Timer B, 0 = stop Timer B. This bit is automatically reset (= 0) when underflow occurs during one-shot mode. |

---

### CIAB_PRA
**CIA-B: Peripheral Data Register A**

- **Address**: `$BFD000` (`$DFFBFD000`)
- **Access**: R/W
- **Chip**: CIA-B

| Bit | Name | Description |
|-----|------|-------------|
|  7 | PA7/DTR | Serial DTR (active low) |
|  6 | PA6/RTS | Serial RTS (active low) |
|  5 | PA5/CD | Serial carrier detect (active low) |
|  4 | PA4/CTS | Serial CTS (active low) |
|  3 | PA3/DSR | Serial DSR (active low) |
|  2 | PA2/SEL | Centronics select |
|  1 | PA1/POUT | Centronics paper out |
|  0 | PA0/BUSY | Centronics busy |

---

### CIAB_PRB
**CIA-B: Peripheral Data Register B**

- **Address**: `$BFD100` (`$DFFBFD100`)
- **Access**: R/W
- **Chip**: CIA-B

| Bit | Name | Description |
|-----|------|-------------|
|  7 | PB7/DSKMOTOR | Disk motor control (active low, latched per-drive) |
|  6 | PB6/DSKSEL3 | Select drive 3 (active low) |
|  5 | PB5/DSKSEL2 | Select drive 2 (active low) |
|  4 | PB4/DSKSEL1 | Select drive 1 (active low) |
|  3 | PB3/DSKSEL0 | Select drive 0 / internal (active low) |
|  2 | PB2/DSKSIDE | Disk head select (0=upper) |
|  1 | PB1/DSKDIREC | Disk seek direction (0=inward) |
|  0 | PB0/DSKSTEP | Disk step pulse (active low, strobe) |

---

### CIAB_DDRA
**CIA-B: Data Direction Register A**

- **Address**: `$BFD200` (`$DFFBFD200`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_DDRB
**CIA-B: Data Direction Register B**

- **Address**: `$BFD300` (`$DFFBFD300`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TALO
**CIA-B: Timer A Low**

- **Address**: `$BFD400` (`$DFFBFD400`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TAHI
**CIA-B: Timer A High**

- **Address**: `$BFD500` (`$DFFBFD500`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TBLO
**CIA-B: Timer B Low**

- **Address**: `$BFD600` (`$DFFBFD600`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TBHI
**CIA-B: Timer B High**

- **Address**: `$BFD700` (`$DFFBFD700`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TODLOW
**CIA-B: Event counter bits 7-0**

- **Address**: `$BFD800` (`$DFFBFD800`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TODMID
**CIA-B: Event counter bits 15-8**

- **Address**: `$BFD900` (`$DFFBFD900`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_TODHI
**CIA-B: Event counter bits 23-16**

- **Address**: `$BFDA00` (`$DFFBFDA00`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_SDR
**CIA-B: Serial Data Register**

- **Address**: `$BFDC00` (`$DFFBFDC00`)
- **Access**: R/W
- **Chip**: CIA-B

---

### CIAB_ICR
**CIA-B: Interrupt Control Register**

- **Address**: `$BFDD00` (`$DFFBFDD00`)
- **Access**: R/W
- **Chip**: CIA-B

| Bit | Name | Description |
|-----|------|-------------|
|  7 | IR/S/C | Interrupt (read) / Set-Clear (write) |
|  4 | FLG | FLAG pin interrupt |
|  3 | SP | Serial port interrupt |
|  2 | ALRM | TOD alarm interrupt |
|  1 | TB | Timer B underflow interrupt |
|  0 | TA | Timer A underflow interrupt |

---

### CIAB_CRA
**CIA-B: Control Register A**

- **Address**: `$BFDE00` (`$DFFBFDE00`)
- **Access**: R/W
- **Chip**: CIA-B

| Bit | Name | Description |
|-----|------|-------------|
|  7 | UNUSED |  |
|  6 | SPMODE | 1 = Serial port=output (CNT is the source of the shift clock) |
|  5 | INMODE | 1 = Timer A counts positive CNT transitions, |
|  4 | LOAD | 1 = force load (this is a strobe input, there is no data storage;  bit 4 will always read back a zero and writing a 0 has no effect.) |
|  3 | RUNMODE | 1 = one-shot mode, 0 = continuous mode. |
|  2 | OUTMODE | 1 = toggle, 0 = pulse. |
|  1 | PBON | 1 = Timer A output on PB6, 0 = PB6 is normal operation. |
|  0 | START | 1 = start Timer A, 0 = stop Timer A. This bit is automatically reset (= 0) when underflow occurs during one-shot mode. |
|  0 | = | Timer A counts 02 pulses. |
|  0 | = | Serial port=input  (external shift clock is required) |

---

### CIAB_CRB
**CIA-B: Control Register B**

- **Address**: `$BFDF00` (`$DFFBFDF00`)
- **Access**: R/W
- **Chip**: CIA-B

| Bit | Name | Description |
|-----|------|-------------|
|  4 | LOAD | 1 = force load (this is a strobe input, there is no data storage;  bit 4 will always read back a zero and writing a 0 has no effect.) |
|  3 | RUNMODE | 1 = one-shot mode, 0 = continuous mode. |
|  2 | OUTMODE | 1 = toggle, 0 = pulse. |
|  1 | PBON | 1 = Timer B output on PB7, 0 = PB7 is normal operation. |
|  0 | START | 1 = start Timer B, 0 = stop Timer B. This bit is automatically reset (= 0) when underflow occurs during one-shot mode. |

---

## Manual Chapters

- **Chapter 1**: Introduction
- **Appendix A**: REGISTER SUMMARY ALPHABETICAL ORDER
- **Chapter 2**: COPROCESSOR HARDWARE
- **Appendix B**: REGISTER SUMMARY ADDRESS ORDER
- **Chapter 3**: PLAYFIELD HARDWARE
- **Appendix C**: ENHANCED CHIP SET
- **Chapter 4**: SPRITE HARDWARE
- **Appendix D**: SYSTEM MEMORY MAPS
- **Chapter 5**: AUDIO HARDWARE
- **Appendix E**: I/O CONNECTORS AND INTERFACES
- **Chapter 6**: BLITTER HARDWARE
- **Appendix F**: 8520 COMPLEX INTERFACE ADAPTERS
- **Chapter 7**: SYSTEM CONTROL HARDWARE
- **Appendix G**: KEYBOARD INTERFACE
- **Chapter 8**: INTERFACE HARDWARE
- **Appendix H**: EXTERNAL DISK CONNECTOR INTERFACE
- **Appendix I**: HARDWARE EXAMPLE INCLUDE FILE
- **Appendix J**: CUSTOM CHIP PIN ALLOCATION LIST
- **Appendix K**: ZORRO EXPANSION BUS
