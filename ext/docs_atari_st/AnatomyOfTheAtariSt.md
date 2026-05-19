<!-- source-pdf: resources/platform_atari_st/docs/AnatomyOfTheAtariSt.ocr.pdf -->
<!-- source-pages: 454 -->

<!-- source-page: 1 -->
## Page 1

iJ
=
ao =
=
an
s
xs
=
a
=
wa
se
=

<!-- source-page: 2 -->
## Page 2

ATARIIKS
INTERNALS
The authoritative insider's guide
By K. Gerits, L. Englisch, R. Bruckmann
A Data Becker Book
Published by
First Publishing Ltd
Unit 20B
Horseshoe Park
Pangbourne
Berks.

<!-- source-page: 3 -->
## Page 3

Copyright © 1985
Data Becker GmbH
Merowingerstr. 30
4000 Dusseldorf, West Germany
Copyright © 1985
ABACUS Software, Inc.
P.O. Box 7219
Grand Rapids, MI 49510
Copyright © 1986
First Publishing Ltd.
20B Horseshoe Park
Horseshoe Rd
Pangbourne, Reading
This book is copyrighted. No part of this book may be reproduced, stored ina
retrieval system, or transmitted in any form or by any means, electronic,
mechanical, photocopying, recording or otherwise without the prior written
permission of First Publishing or Data Becker, GmbH.
Every effort has been made to insure complete and accurate information
concerning the material presented in this book. However First Publishing can
neither guarantee nor be held legally responsible for any mistakes in printing
or faulty instructions contained in this book. The authors will always appre-
ciate receiving notice of subsequent mistakes.
ATARI, 520ST, ST, TOS, ST BASIC and ST LOGO are trademarks or
registered trademarks of Atari Corp.
GEM, GEM Draw and GEM Write are trademarks or registered trademarks
of Digital Research Inc.
IBM is a registered trademark of International Business Machines.
ISBN 0 948015 56X
Printed in Great Britain by
Paradigm Print, Gateshead, Tyne and Wear.

<!-- source-page: 4 -->
## Page 4

fend peek feed
font peel peed
pmeb ph
pee
a
a
—_
pm heh peek
et
—y
IY
ADD
UNH
BRR
WHWW
Wb
—
NON
N
NNN
ON
Re
W
NH
Ree
Re
N
in
beh tek ek
WN
N=
Nr
WN
re
Ne
Table of Contents
The Integerated Circuits
The 68000 Processor
The 68000 Registers
Exceptions on the 68000
The 68000 Connections
The Custom Chips
The WD 1772 Floppy Disk Controller
1772 Pins
1772 Registers
Programming the FDC
The MFP 68901
68901 Connections
The MFP Registers
The 6850 ACIAs
The Pins of the 6850
The Registers of the 6850
The YM-2149 Sound Generator
Sound Chip Pins
The 2149 Registers and their Functions
1/O Register Layout of the ST
The Interfaces
The Keyboard
The mouse
Keyboard commands
The Video Connection
The Centronics Interface
The RS-232 Interface
The MIDI Connections
—y
SB
WW

<!-- source-page: 5 -->
## Page 5

2.6
2.7
2.8
3.1
3.1.1
The Cartridge Slot
The Floppy Disk Interface
The DMA Interface
The ST Operating System
The GEMDOS
GEMDOS error codes and their meaning
The BIOS Functions of the Atari ST
The XBIOS
The Graphics
An overview of the "line-A" variables
Examples for using line-A opcodes
The Exception Vectors
The interrupt structure of theST
The ST VT52 Emulator
The ST System Variables
The 68000 Instruction Set
Addressing modes
The instructions
The BIOS listing
Appendix - The System Fonts
The System Fonts
il

<!-- source-page: 6 -->
## Page 6

SPARED
DEEP EEAAYEL DPPH E
—
omy
t
‘(p(B
oo
List of Figures
68000 Registers
GLUE
MMU
SHIFTER
DMA
FDC 1772
MFP 68901
ACIA 6850
Sound Chip YM-2149
Envelopes of the PSG
6850 Interface to 68000
Block Diagram of Keyboard Circuit
The Mouse
Mouse control port
Atari ST Key Assignments
Diagram of Video Interface
Monitor Connector
Printer Port Pins
Centronics Connection
RS-232 Connection
MIDI System Connection
The Cartridge Slot
Disk Connection
DMA Port
DMA Connections
Lo-Res-Mode
Medium-Res-Mode
Hi-Res-Mode

<!-- source-page: 8 -->
## Page 8

Chapter One
The Integrated Circuits
Ne
Ne
WNe
td
No be
oe
a SS
ee
bo ee
NADA
RRL LW
E EB
The 68000 Processor
The 68000 Registers
Exceptions on the 68000
The 68000 Connections
The Custom Chips
The WD 1772 Floppy Disk Controller
1772 Pins
1772 Registers
Programming the FDC
The MFP 68901
68901 Connections
The MFP Registers
The 6850 ACIAs
The Pins of the 6850
The Registers of the 6850
The YM-2149 Sound Generator
Sound Chip Pins
The 2149 Registers and their Functions
V/O Register Layout of the ST

<!-- source-page: 10 -->
## Page 10

‘rst Publishing
Atari ST Internals
rhe Integrated Circuits
1.1 The 68000 Processor
The 68000 microprocessor is the heart of the entire Atari ST system. This
16-bit chip is in a class by itself; programmers and hardware designers alike
find the chip very easy to handle. From its initial development by Motorola
in 1977 to its appearance on the market in 1979, the chip was to be a
competitor to the INTEL 8086/8088 (the processor used in the IBM-PC and
its many clones). Before the Atari ST's arrival on the marketplace, there
were no affordable 68000 machines available to the home user.
Now,
though, with 16-bit computers becoming more affordable to the common
man, the 8-bit machines won't be around much longer.
What does the 68000 have that's so special? Here's a very incomplete list
of features:
16 data bits
24 address bits (16-megabyte address range!!)
all signals directly accessible without multiplexer
hassle-free operation of “old” 8-bit peripherals
|
powerful machine language commands
|
easy-to-learn assembler syntax
14 different types of addressing
|
17 registers each having 32-bit widths
These specifications (and many yet to be mentioned here) make the 68000
an incredibly good microprocessor for home and personal computers.
In
fact, as the price of memory drops, you'll soon be seeing 68000-based 64K
machines for the same price as present-day 8-bit computers with the same
amount of memory.

<!-- source-page: 11 -->
## Page 11

First Publishing
Atari ST Internal
1.1.1 The 68000 Registers
Let's take a look at 68000 design.
Figure 1.1-1 shows the 17 onboan
32-bit registers, the program counter and the status register.
The eight data registers can store and perform calculations, as well as the
normal addressing tasks. Eight-bit systems use the accumulators for this
which limits the programmer to a total of 8 accumulators. Our 68000 dat:
registers are quite flexible;
data can be handled in. 1-, 8-, 16- and 32- bi:
sizes.
Even four-bit operations are possible (within the limits of Bin
Coded Decimal counting). When working with 32-bit data, all 32 bits car
be handled with a single operation. With 8- and 16-bit data, only the 8th o1
16th bit of the data register can be accessed.
The address registers aren't as flexible for data access as are the data
registers. These registers are for addressing, not calculation.
Processing
data is possible only with word (16-bit) and longword (32-bit) operations.
The address registers must be looked at as two distinct groups, the most
versatile being the registers AO-A6. Registers A7 and A7' fulfill a special
need. These registers are used as the stack pointer by the processor. Two
stack pointers are needed to allow the 68000 to run in USER MODE and
SUPERVISOR MODE.
Register A7 declares whether the system is in
USER or SUPERVISOR mode. Note that the two registers work "under"
A7, but the register contents are only available to the respective operating
mode. We'll discuss these operating modes later.
The program counter is also considered a 32-bit register.
It is theoretically
possible to handle an address range of over 4 gigabytes.
But the address
bits A24-A31 aren't used, which "limits" us to 16 megabytes.
The 68000 status register comprises 16 bits, of which only 10 bits are used.
This status register is divided into two halves: The lower eight bits (bits 0
to 4 proper) is the "user byte". These bits, which act as flags most of the
time, show the results of arithmetical and comparative operations, and can
be used for program branches hinging on those results.
We'll look at the
user byte in more detail later; for now, here is a brief list:
BIT
0
= Carry
flag
BIT
1
= Overflow
flag
BIT
2
=
Zero
flag
BIT
3
= Negative
flag
BIT
4
= eXtend flag

<!-- source-page: 12 -->
## Page 12

‘irst Publishing
Atari ST Internals
Figure 1.1-1
68000 Registers
31
16
15
8
7
0
DO—
D1
D2
DATA
D3
REGISTERS
D4
D5
D6
D7__J
31
0
A 0O—
Al
A2
|ADDRESS
a3.
| REGISTERS
A4
A5
A6—_
31
0
System
Stack
Pointer
SSP
User
Stack
Pointer
USP
Al
STACK
POINTER
31
24
23
0
PC
PROGRAM
is
—_
0
COUNTER
Sys
Byte
User
Byte
SR
STATUS
REGISTER

<!-- source-page: 13 -->
## Page 13

First Publishing
Atari ST Interna
Bits 8-10,
13 and 15 make up the status register's system byte.
Th
remaining bits are unused.
Bit 15 works as a trace bit, which lets you do
software controlled single-step execution of any program.
Bit 13 is th
supervisor bit. When this bit is set, the 68000 is in supervisor mode. Thi
is the normal operating mode; all commands are executed in this mode.
I
user mode, in which programs normally run, privileged instructions ar
inoperative. A special hardware design allows access into the other memor
range while in user mode (e.g., important system variables, I/O registers’
The system byte of the status register can only be manipulated in supervisc
mode; but there's a simple method of switching between modes.
Bits 8 and 10 show the interrupt mask, and run in connection with pin
IPLO-IPL2.
The 68000 has great potential for handling interrupts.
Seven differen
interrupt priorities exist, the highest being the "non-maskable interrupt"
NMI. This interrupt recognizes when all three IPL pins simultaneously rea
low (0).
If, however, all three IPL pins read high, there is no interrupt, anc
the system operates normally.
The other six priorities can be masked by
appropriate setting of the system byte of the status register. For example, i
bit 12 of the interrupt mask is set, while 10 and I1 are off, only levels 7,
¢
and 5 (000, 001 and 010) are recognized.
All other combinations fron
IPLO-IPL2 are ignored by the processor.

<!-- source-page: 14 -->
## Page 14

irst Publishing
Atari ST Internals
1.2 Exceptions on the 68000
Ne've spoken
of interrupts
as
if the 68000 behaves
like
other
nicroprocessors. Interrupts, according to Motorola nomenclature, are an
‘xternal form of an exception (the machine can interrupt what it's doing,
io something else, and return to the interrupted task if needed). The 68000
listinguishes between normal operation and exception handling, rather than
yetween user
and supervisor mode.
One such set of exceptions is the
nterrupts. Other things which cause exceptions are undefined opcodes, and
word or longword access to a prohibited address.
To make exception handling quicker and easier, the 68000 reserves the first
1K of memory (1024 bytes, $000000-$0003FF).
The exception table is
located here. Exceptions are all coded as one of four bytes of a longword.
Encountering an exception triggers the 68000, and the address of the
corresponding table entry is output.
A special exception occurs on reset, which requires
8 bytes (two
longwords); the first longword contains the standard initial value of the
supervisor stack pointer, while the second longword contains the address of
the reset routine itself.
See Chapter 3.3 for the design and layout of the
exception table.
1.1.3 The 68000 Connections
The connections on the 68000 are divided into eight groups (see Figure
1.1-3 on page 11).
The first group combines data and address busses. The data bus consists of
pins DO-D15, and the address bus Al-A23. Address bit AO is not available
to the 68000. Memory can be communicated with words rather than bytes
(1 word=2 bytes=16 bits, as opposed to 1 byte=8 bits).
Also, the 68000
can access data located on odd addresses as well as even addresses.
The
signals will be dealt with later.
It's important to remember in connection with this, that by word access to
memory, the byte of the odd address is treated as the low byte, and the even
7

<!-- source-page: 15 -->
## Page 15

First Publishing
Atari ST Interna
address is the high byte. Word access shouldn't stray from even addresses
That means that opcodes (whether all words or a single word) must alway
be located at an even addresses.
When the data and address bus are in "tri-state" condition, a third conditio:
(in addition to high and low) exists, in which the pins offer high resistance
and thus are inactive on the bus. This is important in connection with Direc
Memory Access (DMA).
The second group of connections comprise the signals for asynchronou:
bus control.
This group has five signals, which we'll now look
at
individually:
1) R/W (READ/WRITE)
The R/W signal
is
a familiar one to all microprocessors. This
indicates to memory and peripherals whether the processor is writing
to or reading data from the address on the bus.
2) AS
(ADDRESS STROBE)
Every processor has a signal which it sends along the data lines
signaling whether the address is ready to be used. On the 68000, this
is known as the ADDRESS STROBE (low active).
3) UDS (UPPER DATA STROBE)
4) LDS (LOWER DATA STROBE)
If the 68000 could only process an entire memory word (two bytes)
simultanesouly, this signal wouldn't be necessary.
However, for
individual access to the low-byte and high-byte of a word, the
processor must be able to distinguish between the two bytes. This is
the task performed by UDS and LDS. When a word is accessed,
both strobes are activated simultaneously (active=low). Accessing
the data at an odd address activates the Lower Data Strobe only, while
accessing data atan even address activates the Upper Data Strobe.
Bit AO from the address bus is used in this case. After every access
when the system must distinguish between three conditions (word,
even byte, odd byte), AO determines how to complete the access.
LDS and UDS are tri-state outputs.
8

<!-- source-page: 16 -->
## Page 16

‘irst Publishing
Atari ST Internals
3) DTACK
The above signals (with the exception of UDS and LDS) are needed
by an 8-bit processor. DTACK takes a different path; DTACK must
be low for any write or read access to take place.
If the signal is not
low within a bus cycle, the address and data lines "freeze up" until
DTACK turns low. This can also occur ina WAIT loop. This way,
the processor can slow down memory and peripheral chips while
performing other tasks.
If no wait cycles are used on the ST, the
processor moves "at full tilt’.
The third group of connections, the signals VMA, VPA and E
are for
synchronous bus control.
A computer is more than memory and
a
microprocessor; interfaces to keyboard, screen, printer, etc. must be
available for communication.
In most cases, interfacing is handled by
special ICs, but the 68000 has a huge selection of interfaces chips onboard.
For hardware designers we'll take a little time explaining these synchronous
bus signals.
The signal E (also known as ®2 or phi 2) represents the reference count for
peripherals.
Users of 6800 and 6502 machines know this signal as the
system counter. Whereas most peripheral chips have a maximum frequency
of only
1 or 2 mHz, the 68000 has a working speed of 8 mHz, which can
increased to 10 by the E signal. The frequency of E in the ST is 800 kHz.
The E output is always active; it is not capable of
a TRI- STATE condition.
The
signal VPA (Valid Peripheral Address) sends data over the
synchronous bus, and delegates this transfer to specific sections of the chip.
Without this signal, data transfer is performed by the asynchronous bus.
VPA also plays a role in generating interrupts, as we'll soon see.
VMA (Valid Memory Address) works in conjunction with the VPA to
produce the CHIP-select signal for the synchronous bus.
The fourth group of 68000 signals allows simple DMA operation in the
68000 system. DMA (Direct Memory Access) directly accesses the DMA
controllers, which control computer memory, and which is the fastest
method of data transfer within a computer system.
To execute the DMA, the processor must be in an inactive state. But for the
processor to be signaled, it must be in a "sleep" state; the low BR signal
9

<!-- source-page: 17 -->
## Page 17

First Publishing
Atari ST Internal:
(Bus Request) accomplishes this.
On recognizing the BR signal, the
68000's read/write cycle ends, and the BG signal (Bus Grant) is activated
Now the DMA-requested chip waits until the signals AS, DTACK anc
(when possible) BGACK are rendered inactive. As soon as this occurs, the
BGACK (Bus Grant Acknowledge) is activated by the requested chip
, anc
takes over the bus. All essential signals on the processor are made high; ir
particular, the data, address and control busses are no longer influenced by
the processor. The DMA controller can then place the desired address or
the bus, and read or write data. When the DMA chip is finished with its
task, the BGACK signal returns to its inactive state, and the processor again
takes over the bus.
The fifth group of signals on the 68000 control interrupt generation. The
68000's "user's choice" interrupt concept is one of its most extraordinary
performing qualities; you have 199 (!) interrupt vectors from which to
choose. These interrupt vectors are divided into 7 non-auto-vectors and 192
auto-vectors, plus 7 different priority lines.
Interrupts are triggered by signals from the three lines IPLO to IPL2; these
three lines give you eight possible combinations.
The combination
determines the priority of the interrupt. That is, if IPLO, IPL1 and IPL2 are
all set high, then the lowest priority is set ("no interrupt"). However, if all
three lines are low, then highest priority takes over,
to execute
a
non-maskable interrupt. All the combinations in between affect special bits
in the 68000's status register;
these, in turn, affect program control,
regardless of whether or not a chosen interrupt is allowable.
Wait -- what are auto-vectors and non-auto-vectors? What do these terms
mean?
If requesting an interrupt on IPLO-IPL2 while VPA is active (low), the
desired code is directly converted from the IPL pins into a vector number.
All seven interrupt codes on the IPL pins have their own vectors, though.
The auto-vector concept automatically gives the vector number of the IPL
interrupt code needed.
When DTACK, instead of VPA, is active on an interrupt request, the
interrupt is handled as a non-auto-vector.
In this case, the vector number
from the triggered chip is produced by DTACK on the 8 lowest bits of the
data bus. Usually (though not important here), the vector number is placed
into the user-vector range ($40--$FF).
10

<!-- source-page: 18 -->
## Page 18

‘irst Publishing
Atari ST Internals
‘he sixth set of connections
are the three "function code" outputs FCO to
'C2. These lines handle the status display of the processor. With the help
if these lines, the 68000 can expand to four times 16 megabytes (64
negabytes).
This extension requires the MMU (Memory Management
Jnit). This MMU does more than handle memory expansion on the ST; it
lso recognizes whether access is made to memory in user or supervisor
node. This information is conveyed to a memory range only accessible in
upervisor mode. Also, the interrupt verification uses this information on
he FC line.
The figure below shows the possible combinations of
unctions.
Supervisor data access
Supervisor program
Interrupt verification
Figure 1.1-3
FC2. FC]
FCO
Status
0
0
0
unused
)
0
1
User-mode
data access
0
1
0
User-mode program
0
1
1
unused
1
0
0
unused
1
0
1
1
1
0
1
1
1
he seventh group contains system control signals. This group applies to
he input CLK and BERR, as well as the bidirectional lines RESET and
HALT,
The input CLK will generate the working frequency of the processor. The
58000 can operate at different speeds; but the operating frequency must be
specified (4, 6, 8, 10, or even 12.5 mHz).
The ST has 8 mHz built in,
while the minimum operating frequency is
2 mHz. The ST's 8 mHz was
chosen as a "middle of the road" frequency to avoid losing data at higher
frequencies.
:
The RESET line is necessary to check for system power-up. The 68000's
data page distinguishes between two different reset conditions.
On
power-up, RESET and HALT
are switched low
for
at
least
100
milliseconds, to set up a proper initialization.
Every other initialization
requires a low impulse of at least 4 "beats" on the 68K.
Here is what RESET does in detail. The system byte of the status register is
loaded with the value $27. Once the processor is brought into supervisor
11

<!-- source-page: 19 -->
## Page 19

First Publishing
Atari ST Internal
Status, the Trace flag in the status register is cleared, and the interrupt leve
is set to 7 (lowest priority, all lines allowable). Additionally, the superviso
Stack pointer and program counter are loaded with the contents of the first
.
bytes of memory, whereby the value of the program counter is set to th
beginning of the reset routine.
However, since the RESET line is bi-directional, the processor can als«
have RESET under program control during the time the line is low. Th
RESET instruction serves this purpose, when the connection is low for 12:
"beats".
It's possible to re-initialize the peripheral ICs at any time, withou
resetting the computer itself. RESET time puts the 68000 into a NOP state
-- a reset is unstoppable once it occurs.
The HALT pin is important to the RESET line's existence (as. we mentionec
above), in order to initialize things properly.
This pin has still more
functions: when the pin is low while RESET is high, the processor goes
into a halt state. This state causes the DMA pin to set the processor into the
tri-state condition. The HALT condition ends when HALT is high again.
This signal can be used in the design of single-step control.
HALT is also bi-directional. When the processor signals this line to become
low,
it means that a major error has occurred (e.g., doubled bus and
address errors).
A low State on the BERR pin will call up exception handling, which runs
basically like an external interrupt. In an orderly system, every access to the
asynchronous bus quits with the DTACK signal.
When DTACK
is
outputting, however, the hardware can produce a BERR, which informs the
processor of any errors found.
A further use for BERR is in connection
with the MMU, to test for proper memory access of a specific range; this
access is signaled by the FC pins.
If protected memory is tried for in user
mode, a BERR will turn up.
When both BERR and HALT are low, the processor will "re-execute" the
instruction at which it stopped.
If it doesn't run properly on the second
"go-round", then it's called a doubled bus error, and the processor halts.
The eighth group of connections are for voltage and ground.
12

<!-- source-page: 20 -->
## Page 20

first Publishing
Atari ST Internals
|.2 The Custom Chips
[he Atari ST has four specially developed ICs.
These chips (GLUE,
VIMU, DMA and SHIFTER) play a major role in the low price of the ST,
since each chip performs several hundred overlapping functions. The first
srototype of the ST was 5 X 50 X 30 cm. in size, mostly to handle all those
ITL ICs. Once multiple functions could be crammed into four ICs, the ST
yecame a saleable item. Then again, the present ST hasn't quite reached the
iltimate goal -- it still has eight TTLs.
Naturally, since these chips were specifically designed by Atari for the ST,
they haven't been publishing any spec sheets. Even without any data specs,
we can give you quite a bit of information on the workings of the ICs.
An interesting fact about these ICs is that they're designed to work in
concert with one another. For example, the DMA chip can't operate alone.
[t hasn't an address counter, and is incapable of addressing memory on its
own (functions which are taken care of by the MMU).
It's the same with
SHIFTER -- it controls video screen and color, but it can't address video
RAM. Again, MMU handles the addressing.
The system programmer can easily figure out which IC has which register.
It is only essential to be able to recognize the address of the register, and
how to control it. We're going to spend some time in this chapter exploring
the pins of the individual ICs.
fin most important IC of the "foursome" is GLUE.
Its title speaks for the
unction -- a glue or paste.
This IC, with its 68 pins, literally holds the
entire system together, including decoding the address range and working
the peripheral ICs.
urthermore, the DMA handshake signals BR, BG and BGACK are
produced/output by GLUE. The time point for DMA request is dictated by
GLUE by the signal from the DMA controller. GLUE also has a BG (Bus
Grant) input, as well as
a BGO (Bus Grant Out).
The interrupt signal is produced by GLUE; in the ST, only IPL1 and IPL2
are used for this.
Without other hardware, you can't use NMI (interrupt
level 7). The pins MFPINT and JACK are used for interrupt control.
13

<!-- source-page: 21 -->
## Page 21

First Publishing
Atari ST Internal:
BGI*
RDY
VPA*
BEER*
DTACK*
IPL
1*
IPL
2*
8MHZ
in
GND
BLANK*
HSYNC
VSYNC
DE
BR*
BGACK*
6850CS*
500HZ
out
Figure 1.2-1 GLUE
x
HOnAAMY
HSEkG
xk OxndN
SSeaz
kN
SCEPC
PEPE ne
a
CKKKKP
Besa
OMNEMNHOMDARUNEMNNHAO
NNNNNANN
A ad dtd add dae
p
3
.e)
e
Ss a
MFPINT*
BGO*
LDS*
UDS*
DO
D1
IACK*
ME PPCS*
GND
SNDCS*
Al
A2
A3
A4
A5
14
RPM W
&
UI oO
~I
©
Oo
HDAAWA
ADO
MR
W
&
UI Oy
~]
©
A21
A20
Al19
A18
Al7
Al16
Al15
Al4
Vee
Al3
Al12
All
A10
A9
A8
A7
A6

<!-- source-page: 22 -->
## Page 22

First Publishing
Atari ST Internals
The function code pins are guided by GLUE, where memory access tasks
ire performed (range testing and access authorization). Needless to say, the
BERR signal is also handled by this chip. VPA is particularly important to
he peripheral ICs and the appropriate select signals.
GLUE generates a timing frequency of
8 mHz.
Frequencies between 2
mHz (sound chip's operating frequency) and 500 kHz (timing for keyboard
and MIDI interface) can be produced.
HSYNC, VSYNC, BLANK and DE (Display Enable) are generated by
GLUE for monitor operation. The synchronous timing can be switched on
and off, and external sync-signals sent to the monitor. This will allow you
to synchronize the ST's screen with a video camera.
The MMU also has a
total of 68 pins.
This IC performs three vital tasks.
The most important task is coupling the multiplexed address bus of dynamic
RAM with the processor's bus (handled by address lines Al to A21). This
gives us an address range totaling 4 megabytes.
Dynamic RAM
is
controlled by RASO, RAS1, CASOL, CASOH, CAS1L and CAS1H, as
well as the multiplexed address bus on the MMU. DTACK, R/W, AS, LDS
and UDS are also controlled by MMU.
We've already mentioned another important function of the MMU:
it works
with the SHIFTER to produce the video signal (the screen information is
addressed in RAM, and SHIFTER conveys the information). Counters are
incorporated in the MMU for this; a starting value is loaded, and within 500
nanoseconds, a word is addressed in memory and the information is sent
over DCYC.
The starting value of the video counter (and the screen
memory position) can be shifted in 256-byte increments.
Another integrated counter in MMU, as mentioned earlier, is for addressing
memory using the DMA. This counter begins with every DMA access (disk
or hard disk), loading the address of the data being transferred.
Every
transfer automatically increments the counter.
The SHIFTER converts the information in video RAM into impulses
readable on a monitor.
Whether the ST is in 640 X 200 or 320 X 200
resolution, SHIFTER is involved.
15

<!-- source-page: 23 -->
## Page 23

First Publishing
Atari ST Internal
GND*
CMPCS
pcyc*
RDAT*
DEV*
RAM*
R/W*
Al5
Al4
Al3
Al2
All
Al0
Ag
A8
Al
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
DAA
NMOANMADAAANANANAAN
Figure 1.2-2 MMU
i
eee)
vuogs
x
HHOO
neds
dONNae
x
VHODOArwWwU
ETP LEEEED DEEPER
DEA
o°
Haake
Aha AD
oy
ONIN
oA MDRONYINAHO
ANNAN ANG ddd ddd
16
NW
&
UI g
~1 ©
wo
=
68
67
66
65
64
63
62
61
LATCH
RASO
CASOLOW
CASOHIGH
16MHZ
IN
D7
D6
D5
D4
D3
D2
Di
DO
MAD
9
MAD
8
MAD
7
GND

<!-- source-page: 24 -->
## Page 24

irst Publishing
Atari ST Internals
Figure 1.2-3 SHIFTER
XTL
0
q
vec
XTL
1 vez A
¢
Soe
out
D1
<
)) PE
D2
‘
D:
1
D4
C
wy)
a
3
D5
C
tr
a
4
D6
‘
HK
>:
5
D7
tr
R/W*
LOAD *(
HJ
)) "ono
D8
‘
eg
DR
0
D9
‘
Wy
D
1
bar
(
co
piz
(
Ne
1
D13
C
Ds
2
D14
C
)
8
)
D15
C
) B
1
GND
q
) 8
2
17

<!-- source-page: 25 -->
## Page 25

First Publishing
Atari ST Interna
The information from RAM is transferred to SHIFTER on the signi
LOAD. A
resolution of 640 X 400 points sends the video signal over tl
MONO connector.
Since color is impossible in that mode, the RG
connection is rendered inactive.
The other two resolutions set MON
output to inactive, since all screen information is being sent out the RG
connection in those cases.
The third color connection works together with external equipment as
digital/analog converter. Individual colors are sent out over different pin:
to give us color on our monitor.
Pins R1- R5 on the address bus make u
the "palette registers". These registers contain the color values, which ar
placed in individual bit patterns. The 16 palette registers hold a total of 1
colors for 320 X 200 mode.
Note, however, that since these are based o
the “primary” colors red, green and blue, these colors can be adjusted in
steps of brightness, bringing the color total to 512.
The DMA controller is like SHIFTER, only in a 40-pin housing; it is use
to oversee the floppy disk controller, the hard disk, and any othe
peripherals that are likely to appear.
The speed of data transfer using the floppy disk drive offers no problems t
the processor.
It's different with hard disks; data moves at such high spee
that the 68000 has to send a "pause" over the 8 mHz frequency. This pac
is made possible by the DMA.
The DMA is joined to the processor's data bus to help transfer data. Tw
registers within the machine act as a bi-directional buffer for data throug]
the DMA port; we'll discuss these registers later.
One interesting point
The processor's 16-bit data bus is reduced to 8 bits for floppy/hard dis.
work. Data transfer automatically transfers two bytes per word.
The signals CA1, CA2, CR/W, FDCS and FDRQ manage the floppy dis:
controller.
CAt and CA2 are signals which the floppy disk controlle
(FDC) uses to select registers.
CR/W determine the direction of dat
transfer from/to the FDC, and other peripherals connected to the DMA port
The RDY signal communicated with GLUE (DMA-request) and MMI
(address counter). This signal tells the DMA to transfer a word.
As you can see, these ICs work in close harmony with one another, anc
each would be almost useless on its own.
18

<!-- source-page: 26 -->
## Page 26

rst Publishing
Atari ST Internals
Figure 1.2-4 DMA
R/W
€
Al
FCS*
D0
D1
D2
D3
D4
D5
D
6
D7
D8
D9
D10
D121
D12
D13
D14
D15
DA DTV OA OA LNA LALLA LN
NNN ONL LQLY
GND
YW
19

<!-- source-page: 27 -->
## Page 27

First Publishing
Atari ST Interr
1.3 The WD 1772 Floppy Disk Controller
Although the 1772 from Western Digital has only 28 pins, this chip conta
a complete floppy disk controller (FDC) with capabilities matching 40-r
controllers.
This IC is software-compatible with the 1790/2790 seri
Here are some of the 1772's features:
Simple 5-volt current
Built-in data separator
Built-in copy compensation logic
Single and double density
Built-in motor controls
Although the user has his/her choice of disk format, e.g. sector lengt
number of sectors per track and number of tracks per diskette, the "norm
format is the optimum one for data transfer.
So, Apple or Commodo
diskettes can't be used.
Before going on to details of the FDC, let's take a moment to look at the:
pins of this IC.
1.3.1 1772 Pins
These pins can be placed in three categories. The first group consists of t
power connections.
Vee:
+5 volts current.
GND:
Ground connection.
MR:
Master reset. FDC reinitializes when this is low.
The second set are processor interface pins. These pins carry data betwe
the processor and the FDC.
|
20

<!-- source-page: 28 -->
## Page 28

irst Publishing
Atari ST Internals
Figure 1.3-1 FDC 1772
css
C|
)
INTR
R/W*
=
;.
DRQ
A0
DD*
Al
|
N
WP*
DAL
0
=
>
5
INDEX
DAL
1
C |
~
D)
TRKO
|
ri
DAL
2
=
5
WD
DAL
3
WG
DAL
4
|
@)
)
MO
DAL
5
=
>
)
RD*
DAL
6
Cc
')
CLK
DAL
7
Cc]
D)
DIRC
MR*
Cc
D)
STEP
GND
C
|
)
Vee
21

<!-- source-page: 29 -->
## Page 29

First Publishing
Atari ST Intern:
DO0-D7:
CS:
R/W:
A0,A1:
DRQ:
CLK:
Eight-bit bi-directional
bus;
data, commands
and
stat
information go between FDC and system.
FDC can only access registers when this line is low.
Read/Write. This pin states data direction. HIGH= read by FD
LOW=write from FDC.
These bits determine which register is accessed (in conjunctic
with R/W). The 1772 has a total of five registers which can bo
read and write to some degree. Other registers can only read O
write. Here is a table to show how the manufacturer designe
them:
Al
AQ
R/W=1
R/W=0
0
0
Status
Reg.
Command Reg.
0
1
Track
Reg.
Track
Reg.
1
0
Sector
Reg.
Sector
Reg.
1
1
Data
Reg.
Data
Reg.
Data Request. When this output is high, either the data register
full (from reading), and must be "dumped", or the data register
empty (writing), and can be refilled.
This connection aids tt
DMA operation of the FDC.
Clock.
The clock signal counts only to the processor bus.
/
input frequency of 8 mHz must be on, for the FDC's intern
timing to work.
The third group of signals make up the floppy interface.
STEP:
DIRC:
Sends an impulse for every step of the head motor.
Direction. This connection decides the direction of the head; hig
moves the head towards center of the diskette.
22

<!-- source-page: 30 -->
## Page 30

irst Publishing
Atari ST Internals
D:
"ROO:
VPRT:
IDEN:
Read Data.
Reads data from the diskette.
This information
contains both timing and data impulses -- it is sent to the internal
data separator for division.
Motor On. Controls the disk drive motor, which is automatically
started during read/write/whatever operations.
Write Gate. WG will be low before writing to diskette.
Write
logic would be impossible without this line.
Write Data. Sends serial data flow as data.and timing impulses.
Track 00. This moves read/write head to track 00. TROO would
be low in this case.
Index Pulse. The index pulses mark the physical beginnings of
every track on a diskette.
When formatting a disk, the FDC
marks the start of each track before formatting the disk.
Write Protect.
If the diskette is write-protected, this input will
react.
Double Density Enable.
This signal is confined to floppy disk
control;
it allows you to switch between single-density and
double-density formats.
23

<!-- source-page: 31 -->
## Page 31

First Publishing
Atari ST Intern:
1.3.2 1772 Registers
CR (Command Register):
Commands are written in this 8-bit register. Commands shou
only be written
in CR when no other command
is und
execution. Although the FDC only understands 11 commanc
we actually have a large number of possibilities for the:
commands (we'll talk about those later).
STR (Status Register):
Gives different conditions of the FDC, coded into individual bit
Command writing depends on the meaning of each bit.
Tt
Status register can only be read.
TR (Track Register):
Contains the current position of the read/write head.
Ever
movement of the head raises
or lowers
the value of T
appropriately.
Some commands will read the contents of T!
along with information read from the disk. The result affects tt
Status Register. TR can be read/written.
SR (Sector Register):
SR contains the number of sectors desired from read/wri:
operations. Like TR, it can be used for either operation.
DR (Data Register):
DR is used for writing data to/ reading data from diskette.
24

<!-- source-page: 32 -->
## Page 32

st Publishing
3.3 Programming the FDC
ogramming this chip is no big deal for a system programmer. Direct (and
most Cases, unnecessary) programming is made somewhat harder AND
astically simpler by the DMA chip. The 11 FDC commands are divided
0 four types.
ea}
Rew
nee
ng
Function
Restore, look for track 00
Seek, look for a track
Step, a track in previous direction
Read Sector
Write Sector
Read Address, read ID
Read Track, read entire track
Force Interrupt
ype |
Commands
nese commands position the read/write head. The bit patterns of these five
ymmands look like this:
BIT
7
6
5
4
3
2
1
Restore
0
0
0
O
H
V
RI
Seek
0
0
0
1
H
V
R11
Step
0
O
1
U
H
V
RI
Step
In
Oo
1
0
U
H
V
Ri
Step Out
0
1
1
U
4H
V
Ri
25
Step In, move head one track in (toward disk hub)
Step Out, move head one track out (toward edge of disk)
Write Track, write entire track (format)
0
RO
‘RO
RO
RO
RO
Atari ST Internals

<!-- source-page: 33 -->
## Page 33

First Publishing
Atari ST Intert
All five commands have several variable bits; bits RO and R1 give the ti
between two step impulses. The possible combinations are:
Rl
RO
STEP
RATE
0
O
2 milliseconds
6)
1
3 milliseconds
1
O
5 milliseconds
1
1
6 milliseconds
These bits must be set by the command bytes to the disk drive. The V-bi
the so-called "verify flag".
When set, the drive performs an automa
verify after every head movement.
The H-bit contains the spin-
sequence. The system delays disk access until the disk motor has reach
300 rpm.
If the H-bit is cleared, the FDC checks for activation of
|
motor-on pins. When the motor is off, this pin will be set high (motor o
and the FDC waits for 6 index impulses before executing the command.
the motor is already running, then there will be no waiting time.
The three different step commands have bit 4 designated a U- bit.
Eve
step and change of the head appears here.
Type 2 Commands
These commands deal with reading and writing sectors. They also ha
individual bits with special meanings.
BIT
7
6
5
4
3
2
1
0
Read Sector
1
0
0M
H
E
OQ
QO
Write
Sector 10
1M
H
E
Pp
AQ
The H-bit is the previously described start-up bit. When the E-bit is set,
|
FDC waits 30 milliseconds before starting the command.
This delay
important for some disk drives, since it takes time for the head to char
tracks. When the E-bit reads null, the command will run irnmediately.
The M-bit determines whether one or several sectors are read one af
another.
On a null reading, only one sector will be read from/written
Multi-sector reading sets the bit, and the FDC increments the counter at e:
new sector read.
Bits 0 and 1 must be cleared for sector reading. Writing has its own spec
meaning:
the AQ bit conveys to bit
0 whether a cleared or normal d
|
26

<!-- source-page: 34 -->
## Page 34

rst Publishing
Atari ST Internals
idress mark is to be written. Most operating systems don't use this option
. normal data address mark is written).
he P-bit (bit 1) dictates whether pre-compensation for writing data is
imed on or off. Pre-compensation is normally set on; it supplies a higher
egree of protection to the inner tracks of a diskette.
‘ype 3
Commands
‘ead Address gives program information about the next ID field on the
iskette.
This ID field describes track, sector, disk side and sector length.
‘ead Track gives all bytes written to a formatted diskette, and the data
between sectors". Write Track formats a track for data storage. Here are
1e bit patterns for these commands:
‘IT
765432410
tead Address
110e0H8HEOO
tead Track
1110O0O0H8HEOO
Irite
Track
11i131H8HEP
O
The H- and E-bits also belong to the Type 2 command set (spin-up and
lead-settle time). The P-bit has the same function as in writing sectors.
[ype
4 Commands
Phere's only one command in this set: Force Interrupt. This command can
work with individual bits during another FDC command.
When this
ommand comes into play, whatever command was currently running is
nded.
BIT
7
6
5
4
3
2
1 =0
Force
Interrupt
1
1
0
1
13
12
11
I0
Bits I0-I3 present the conditions under which the interrupt is pressed.
10
and I1 have no meaning to the 1772, and remain low.
If I2 is set, an
interrupt will be produced with every index impulse.
This allows for
oftware controlled disk rotation.
If I3
is set, an interrupt is forced
immediately, and the currently-running command ends. When all bits are
null, the command ends without interruption.
27

<!-- source-page: 35 -->
## Page 35

First Publishing
Atari ST Interna
1.4 The MFP 68901
MFP is the abbreviation for Multi-Function Peripheral.
This name is r
exaggeration; wait until you see what it can do!
Here's a brief list of tt
most noteworthy features:
8-bit parallel port
Data direction of every port bit is individually programmabk
Port bits usable as interrupt input
16 possible interrupt sources
Four universal timers
Built-in serial interface
1.4.1
The 68901 Connections
The 48 pins of the MFP are set apart in function groups. The first functio
group is the power connection set:
GND, Vcc, CLK:
Vcc and GND carry voltage to and from the MFP. CLK is th
clock input; this clock signal must not interfere with the syste1
timer of the processor. The ST's MFP operates at a frequency «
4 mHz.
Communication with the data bus of the processor is maintained wit
D0-D7, DTACK, RS1-RS5 and RESET.
D0-D7:
These bi-directional pins normally work with the 8 lowest dai
bits of the 68000.
It is also possible to connect with D8 throug
D15, but it's impossible to produce non-auto interrupts.
Thu
interrupt vectors travel along the low order 8 data bits.
28

<!-- source-page: 36 -->
## Page 36

irst Publishing
Atari ST Internals
R/W*
Al
A2
A 3
A
4
A5
Tc
so
s.r
RC
Vec
Nc.
TA
TB
TC
o
oOo
98
98
TD
XTALI
XTAL2
TA
H
i
w
La
RESET
ro
rid
rI2
Figure 1.4-1 MFP 68901
wy
nnAnAnNAAAANANANANANNn
NAN f)
68901
U
UQUUUUJUUUUUUUUUUUUUUU
UU
29

<!-- source-page: 37 -->
## Page 37

First Publishing
Atari ST Intern:
CS
(Chip
Select):
This line is necessary to communication with the MFP.
CS
active when low.
DS (Data Strobe):
This pin works with either LDS or UDS on the processc
Depending on the signal, MFP will operate either the lower
upper half of the data bus.
DTACK (Data Transfer ACKnoledge):
This signal shows the status of the bus cycle of the process:
(read or write).
RS1-RS5
(Register
Select):
These pins normally connect with to the bottom five address lin
of the processor, and serve to choose from the 24 intern.
registers.
RESET:
If this pin is low for at least
2 microseconds, the MFP initialize
This occurs on power-up and a system reset.
The next group of signals cover interrupt connections (IRQ, IACK, IEI ar
IEO).
IRQ (Interrupt ReQuest):
IRQ will be low when an interrupt is triggered in the MFP. Th
informs the processor of interrupts.
IACK (Interrupt ACKnowledge):
On an interrupt (IRQ and IEI), the MFP sends a low signal ov
TACK and DS on the data lines.
Since 16 different interru
sources are available, this makes handling interrupts muc
simpler.
IEI, IEO (Interrupt Enable In/ Out):
These two lines permit daisy-chaining of several MFPs, ar
determine MFP priority by their positioning in this chain.
IE
would work through the MFP with the highest priority. IEO
«
the second MFP would remain unswitched.
On an interrupt,
signal is sent over IACK, and the first MFP in the chain wi
acknowledge with a high IEO.
|
30

<!-- source-page: 38 -->
## Page 38

irst Publishing
Atari ST Internals
Text, we'll look at the eight I/O lines.
00-7 (Input/Output):
These pins use one or all normal I/O lines. The data direction of
each port bit is set up in a data direction register of its own.
In
addition, though, every port bit can be programmed to be an
interrupt input.
he timer pins make up yet another group of connections:
XTAL1,2 (Timer Clock Crystal):
A quartz crystal can be connected to these lines to deliver a
working frequency for the four timers.
YAI,TBI (Timer Input):
Timers A and B can not only be used as real counters differently
from timers C and D with the frequency from XTALI and 2, but
can also be set up for event counting and impulse width
measurement.
In both these cases, an external signal (Timer
Input) must be used.
TAO,TBO,TCO,TDO (Timer Output):
Every timer can send out its status on each peg (from 01 to 00).
Each impulse is equal to 01.
The second-to-last set of signals are the connections to the universal serial
interface. The built-in full duplex of the MFP can be run synchronously or
asynchronously, and in different sending and receiving baud rates.
SI (Serial Input):
An incoming bit current will go up the SI input.
SO (Serial Output):
Outgoing bit voltage (reverse of SI).
RC (Receiver Clock):
Transfer speed of incoming data is determined by the frequency
of this input; the source of this signal can, for example, be one of
the four timers.
TC (Transmitter Clock):
|
Similar to RC, but for adjusting the baud-rate of data being
|
transmitted.
31

<!-- source-page: 39 -->
## Page 39

First Publishing
Atari ST Intern:
The final group of signals aren't used in the Atari ST. They are necessa
when the serial interface is operated by the DMA.
RR (Receiver Ready):
This pin gives the status of the receiving data registers.
If
character is completely received, this pin sends current.
TR (Transmitter Ready):
This line performs a similar function for the sender section of tt
serial interface.
Low tells the DMA controller that a ne
character in the MFP must be sent.
1.4.2 The MFP Registers
As we've already mentioned, the 68901 has a total of 24 different register:
This
large number, together with
the logical arrangement, make
programming the MFP much easier.
Reg
1 GPIP, General Purpose I/O Interrupt Port
This is the data register for the 8-bit ports, where data from th
port bits is sent and read.
Reg
2 AER, Active Edge Register
When port bits are used for input, this register dictates whethe
the interrupt will be a low-high- or high-low conversion. Zero i
used in the high-low change, one for low-high.
Reg
3 DDR, Data Direction Register
We've already said that the data direction of individual port bit
can be fixed by the user.
When
a DDR bit equals 0, th
corresponding pin becomes an input, and
1 makes it an output
Port bit positions are influenced by AER and DDR bits.
32

<!-- source-page: 40 -->
## Page 40

irst Publishing
Atari ST Internals
teg 4,5 IERA,IERB, Interrupt Enable Register
Every interrupt source of the MFP can be separately switched on
and off.
With a total of 16 sources, two 8-bit registers are
needed to control them.
If a
1 has been written to IERA or
TERB,
the corresponding channel
is enabled (turned on).
Conversely, a zero disables the channel.
If it comes upon a
closed channel caused by an interrupt, the MFP will completely
ignore it.
The following table shows which bit is coordinated
with which interrupt occurrence:
IERA
Bit
7:
I/O port bit
7
(highest priority)
Bit
6:
I/O port
bit
6
Bit
5:
Timer
A
Bit
4:
Receive buffer
full
Bit
3:
Receive error
Bit
2:
Sender buffer empty
Bit
1:
Sender error
Bit
0:
Timer
B
IERB
Bit
7:
I/O port bit
5
Bit
6:
I/O port bit
4
Bit
5:
Timer
C
Bit
4:
Timer
D
Bit
3:
I/O port
bit
3
Bit
2:
I/O port
bit
2
Bit
1:
I/O port
bit
1
Bit
0:
I/O port
bit
0,
lowest priority
This arrangement applies to the IP-, IM- and IS-registers discussed below.
Reg 6,7 IPRA,IPRB, Interrupt Pending Register
When an interrupt occurs on an open channel, the appropriate bit
in the Interrupt Pending Register is set to 1. When working with
a system that allows vector creation, this bit will be automatically
cleared when the MFP puts the vector number on the data bus.
If
this possibility doesn’t exist, the IPR must be cleared using
software. To clear a bit, a byte in the MFP will show the location
of the specific bit.
The bit arrangement of the IPR is shown in the table for registers
4 and 5 (see above).
33

<!-- source-page: 41 -->
## Page 41

First Publishing
Atari ST Interna
Reg 8,9 ISRA,ISRB, Interrupt In-Service Register
The function of these registers is somewhat complicated, an
depends upon bit 3 of register 12.
This bit is an S-bit, whic
determines whether the 68901 is working in "Software End-o!
Interrupt" mode (SED) or in "Automatic End-of-Interrupt" mod
(AED). AEI mode clears the IPR (Interrupt Pending Bit), whe:
the processor gets the vector number from the MEP during ai
TACK cycle. The appropriate In-Service bit is cleared at the sam
time. Now a new interrupt can occur, even when the previou
interrupt hasn't finished its work.
SEI mode sets the corresponding ISR-bit when the vecto
number of the interrupt is requested by the processor.
At the
interrupt routine's end, the bit designated within the MEP mus
be cleared.
As long as the Interrupt In-Service bit is set, al
interrupts of lower priority are masked out by the MFP. Once thx
Pending-bit of the active channel is cleared, the same sort of
interrupt can occur a second time, and interrupts of lesser priority
can occur as well.
Reg 10,11 IMRA,IMRB Interrupt Mask Register
Individual interrupt sources switched on by IER can be masked
with the help of this register.
That means that the interrupt is
recognized from within and is signalled in the IPR, even if the
IRQ line remains high.
Reg 12 VR
Vector Register
In the cases of interrupts, the 68901 can generate a vector number
corresponding to the interrupt source requested by the processor
during an Interrupt Acknowledge Cycle.
All
16 interrupt
channels have their own vectors, with their priorities coded into
the bottom four bits of the vector number (the upper four bits of
the vector are copied from the vector register). These bits must
be set into VR, therefore.
Bit 3 of VR is the previously mentioned S-bit.
If this bit is set
(like in the ST), then the MFP operates in “Software End-of-
Interrupt" mode; a cleared bit puts the system into "Automatic
End-of-Interrupt"' mode.
34

<!-- source-page: 42 -->
## Page 42

‘irst Publishing
Atari ST Internals
Reg 13,14 TACR,TBCR
Timer A/B Control Register
Before proceeding with these registers, we should talk for a
moment about the timer.
Timers A and B
are both identical.
Every timer consists of a data register, a programmable feature
and an 8-bit count-down counter. Contents of the counters will
decrease by one every impulse. When the counter stands at 01,
the next impulse changes the corresponding timer to the output of
its pins.
At the same time, the value of the timer data register is
loaded into the timer.
If this channel is set by the IER bit, the
interrupt will be requested.
The source of the timer beats will
usually be those quartz frequencies from XTAL1 and 2.
This
operating mode is called delay mode, and is available to timers C
and D.
Timers A and B
can also be fed external impulses using timer
inputs TAI and TBI (in event count mode).
The maximum
frequency on timer inputs should not surpass 1/4 of the MFP's
operating frequency (that is,
1 mHz).
Another peculiarity of this operating mode is the fact that the
timer inputs for the interrupts are I/O pins
13 and 14.
By
programming the corresponding bits in the AER, a pin-jump can
be used by the timer inputs to request an interrupt. TAI is joined
with pin 13, TBI by pin 14. Pins 13 and 14 can also be used as
VO lines without interrupt capability.
Timers A and B have yet a third operating mode (pulse-length
measurement). This is similar to Delay Mode, with the difference
that the timer can be turned on and off with TAI and TBI. Also,
when pins
13 and 14 are used, the AER-bits can determine
whether the timer inputs are high or low.
If, say, AER-bit 4 is
set, the counter works when TAI is high. When TAI changes to
low, an interrupt is created.
Now we come to TACR and TBCR. Both registers only use the
fifth through eighth bits.
Bits 0 to 3 determine the operating
mode of each timer:
35

<!-- source-page: 43 -->
## Page 43

First Publishing
Atari ST Internal
tw
tH
H
es)
PRPPRPPPEROOCOCOCCSO
NO
PrRFrRPrRPFODW
OW OrRFPFRPFOOO COO
i
Oo
Timer
Delay
Delay
Delay
Delay
Delay
Delay
Delay
Delay
Event
Pulse
Pulse
Pulse
Pulse
Pulse
Pulse
Pulse
FPROOPRFPOOHPRPOORKFEHROO
HOPOPOPORPOFRORHPOFO
Function
stop,
mode,
mode,
mode,
mode,
mode,
mode,
mode,
mode,
no function executed
subdivider
subdivider
subdivider
subdivider
subdivider
subdivider
subdivider
subdivider
divides
divides
divides
divides
divides
divides
divides
divides
by
by
by
by
by
by
by
4
10
16
16
50
64
100
200
Count Mode
extension
extension
extension
extension
extension
extension
extension
mode, subdivider
mode, subdivider
mode, subdivider
mode, subdivider
mode, subdivider
mode, subdivider
mode, subdivider
by
divides
divides
divides
divides
divides
divides
divides
by
by
by
by
by
by
by
4
10
16
50
64
10(
20(
Bit 4 of the Timer Control Register has a particular function
This bit can produce a low reading for the timer being used with
it at any time. However, it will immediately go high when the
timer runs.
Reg 15 TCDCR Timers C and D Control Register
Timers C and D
are available only in delay mode; thus, one byte
controls both timers.
The control information is programmec
into the lower three bits of the nibbles (four- bit halves).
Bits C
and 2 arrange Timer D, Timer C
is influenced by bits 4 and 6.
Bits 3 and 7 in this register have no function.
Bit
Bit
PrPrFrPOODDOMAN
FPROORRPOOUK
FPOFROFOrFOBO
Function
-
Function
-
Timer
Stop
Delay Mode,
Delay Mode,
Delay Mode,
Delay Mode,
Delay Mode,
Delay Mode,
Delay Mode,
3
Timer
D
Timer
C
division
by
division
by
division
by
division
by
division
by
division
by
division
by
6
10
16
50
64
100
200

<!-- source-page: 44 -->
## Page 44

first Publishing
Atari ST Internals
Reg 16-19 TADR,TBDR,TCDR,TDDR Timer Data Registers
The four Timer Data Registers are loaded with a value from the
counter. When a condition of 01 is reached, an impulse occurs.
A continuous countdown will stem from this value.
Reg 20 SCR Synchronous Character Register
A value will be written to this register by synchronous data
transfer, so that the receiver of the data will be alerted. When
synchronous mode is chosen, all characters received will be
stored in the SCR, after first being put into the receive buffer.
Reg 21 UCR,USART Control Register
USART
is short for Universal Synchronous/Asynchronous
Receiver/Transmitter.
The UCR allows you to set all the
operating parameters for the interfaces. Parameters can also be
coded in with the timers.
Bit
0
>:
unused
Bit
1
:
O=Odd parity
1=Even parity
Bit
2
:
O=No parity
(bit
1
is
ignored)
1=Parity according
to bit
1
Bits
3,4
:
These bis
control
the number
of
start-
and stopbits
and the
format desired.
Start
Stop Format
0
0)
Synchronous
1
1
Asynchronous
1
1,5 Asynchronous
1
2
Asynchronous
Bit
PROOW;
rPOrFOW
Bits
5,6
:
These bits
give
the
“wordlength"
of
the
data bits
to
be transferred.
Word
length
8
bits
7
bits
6 bits
5
bits
Bits
rFRrROOS
POrROYN

<!-- source-page: 45 -->
## Page 45

First Publishing
Atari ST Interna
Bit
7
:
O=Frequency
from TC
and RC
directly used
as transfer
frequency
(used only
for
synchronous transfer}
1l=Frequency
in
TC and
RC
internally divided by
16.
Reg 22 RSR Receiver Status Register
The RSR gives information concerning the conditions of a
receivers.
Again, the different conditions are coded int
individual bits.
Bit 0 Receiver Enable Bit
When this bit is cleared, receipt is immediately turned off
All flags in RSR are automatically cleared. A set bit mean
that the receiver is behaving normally.
Bit 1 Synchronous Strip Enable
This bit allows synchronous data transfer to determin
whether or not a character in the SCR is identical to ;
character in the receive buffer.
Bit 2 Match/Character in Progress
When in synchronous transfer format, this bit signals that.
character identical with the SCR byte would be received
In asynchronous mode, this bit is set as soon as the startbi
is recognized. A stopbit automatically clears this bit.
Bit 3 Found - Search/Break Detected
This bit is set in synchronous transfer format, when
character received coincides with one stored in the SC
This condition can be treated as an interrupt over th
receiver's error channel. Asynchronous mode will caus
the bit to set when a BREAK is received.
The bre
condition
is fulfilled when only zeroes are receive
following a
startbit.
To distinguish between
a BREA
from a "real" null, this line should be low.
Bit 4 Frame Error
A frame error occurs when a byte received is not a null, bu
the stopbit of the byte IS a null.
|
38

<!-- source-page: 46 -->
## Page 46

First Publishing
Atari ST Internals
Bit 5 Parity Error
The condition of this bit gives information as to whether
parity on the last received character was correct.
If the
parity test is off, the PE bit is untouched.
Bit 6 Overrun Error
This bit will be set when a complete character is in the
receiver floating range but not read into the receive buffer.
This error can be operated as an interrupt.
Bit 7 Buffer Full
This bit is set when a character is transferred from the
floating register to the receive buffer.
As soon as the
processor reads the byte, the bit is cleared.
Reg 23 TSR Transmitter Status Register
Whereas the RSR sends receiver information, the TSR handles
transmission information.
Bit O Transmitter Enable
The sending section is completely shut off when this bit is
cleared. At the same time the End-bit is cleared and the UE-
bit is set (see below).
The output to the receiver is set in
the corresponding H- and L-bits.
Bits 1,2 High- and Low-bit
These bits let the programmer decide which mode of output
the switched-off transmitter will take on.
If both bits are
cleared,the output is high. High-bit only will create high
output; low-bit, low output.
Both bits on will switch on
loop-back-mode.
This state loops the output from the
transmitter with receiver input. The output itself is on the
high-pin.
Bit 3 Break
The break-bit has no function in synchronous data transfer.
In asynchronous mode, though, a break condition is sent
when the bit is set.
39

<!-- source-page: 47 -->
## Page 47

First Publishing
Atari ST Internal
Bit 4 End of Transmission
If the sender is switched off during running transmissior
the end-bit will be set as soon as the current character ha:
been sent in its entirety. When no character is sent, the bi
is immediately set.
Bit
5 Auto Turnaround
When this bit is set, the receiver is automatically switchec
on when the transmitter
is
off, and
a character will
eventually be sent.
Bit 6 Underrun Error
This bit is switched on when a character in the sender
floating register will be sent, before a new character is
written into the send buffer.
Bit 7 Buffer Empty
This bit will be set when a character from the send buffer
will be transferred to the floating register.
The bit is
cleared when new data is written to the send buffer.
|
Reg 24 UDR, USART Data Register
Send/receive data is sent over this register. Writing sends data in
the send buffer, reading gives you the contents of the receive
buffer.
40

<!-- source-page: 48 -->
## Page 48

First Publishing
Atari ST Internals
1.5 The 6850 ACIAs
ACIA is short for "Asynchronous Communications Interface Adapter".
This 24-pin IC has all the components necessary for operating a serial
interface, as well as error-recognizing and data-formatting capabilities.
Originally for 6800-based computers, this chip can be easily tailored for
6502 and 68000 systems.
The ST has two of these chips.
One of them
communicates with the keyboard, mouse, joystick ports, and runs the
clock. Keyboard data travels over a serial interface to the 68000 chip. The
second ACIA is used for operating the MIDI interface.
Parameter changes in the keyboard ACIA are not recommended:
The
connection between keyboard and ST can be easily disrupted. The MIDI
interface is another story, though -- we can create all sorts of practical
applications.
Incidentally, nowhere else has it been mentioned that the
MIDI connections can be used for other purposes. One idea would be to
use the MIDI interfaces of several STs to link them together (for schools or
offices, for example).
1.5.1 The Pins of the 6850
For those of you readers who aren't very well-acquainted with the
principles of serial data transfer, we've included some fairly detailed
descriptions in the pin layout which follows.
Vss
This connection is the "ground wire” of the IC.
RX DATA Receive Data
This pin receives data; a start-bit must precede the least significant
data-bit before receipt.
41

<!-- source-page: 49 -->
## Page 49

First Publishing
Atari ST Internal:
Figure 1.5-1 ACIA 6850
Vss
‘Gi
D)
cTs*
seQ
oo
B=
Cc
In)
)
TX
CLK
Cc
ee
D)
D
RTS*
C}
iO
-)
D
2
TX
DATA =
5
D
3
IRQ*
D
4
cs
0
Kt
D
5
cs
2s
=
HI
:
D
6
cs
1
C |
U
D)
D
7
RS
C |
ct
)
E
Vee
C |
)
R/W*
42

<!-- source-page: 50 -->
## Page 50

‘irst Publishing
Atari ST Internals
<X CLK Receive Clock
This pin signal determines baud-rate (speed at which the data is
received), and
is synchronize
to the incoming data.
The
frequency of RX CLK is patterned after the desired transfer
speed and after the internally programmed division rate.
rX CLK Transmitter Clock
Like RX CLK, only used for transmission speed.
RTS Request To Send
This output signals the processor whether the 6850 is low or
high; mostly used for controlling data transfer.
A low output
will, for example, signal a modem that the computer is ready to
transmit.
TX DATA Transmitter Data
This pin sends data bit-wise (serially) from the computer.
IRQ Interrupt Request
Different circumstances set this pin low, signaling the 68000
processor. Possible conditions include completed transmission
or receipt of a character.
CS
0,1,2 Chip Select
"
These three lines are needed for ACIA selection. The relatively
high number of CS signals help minimize the amount of
|
hardware needed for address decoding, particularly in smaller
computer systems.
RS Register Select
This signal communicates with internal registers, and works
closely with the R/W signal. We shall talk about these registers
|
later.
Vee Voltage
ans pin is required of all ICs -- this pin gets an operating voltage
of 5V.
R/W Read/Write
This tells the processor the "direction" of data traveling through
|
the ACIA. A
high signal tells the processor to read data, and low
writes data in the 6850.
43

<!-- source-page: 51 -->
## Page 51

First Publishing
Atari ST Internal
E Enable
The E-signal determines the time of reading/writing.
Al
read/write processes with this signal must be synchronous.
DO
- D7 Data
These data lines are connected to those of the 68000. Until thi
ACIA is accessed, these bidirectional lines are all high.
DCD Data Carrier Detect
A modem control signal, which detects incoming data. Wher
DCD is high, serial data cannot be received.
CTS Clear To Send
CTS
answers the computer on the signal RTS. Data transmissiot
is possible only when this pin is low.
1.5.2 The Registers of the 6850
The 6850 has four different registers. Two of these are read only. Two of
them are write only.
These registers are distinguished by R/W and RS,
after the table below:
R/W
RS
Register
Access
0
0
Control Register
write
0
1
Sender Register
write
1
0
Status Register
read
1
1
Receive Register
read
The sender/receiver registers (also known as the RX- and TX- buffers)
for data transfer. When receiving is possible, the incoming bits are put in
shift register. Once the specified number of bits has arrived, the contents o
the shift register are transferred to the TX buffer.
The sender works i
much the same way, only in the reverse direction (RX buffer to sender shifi
register).

<!-- source-page: 52 -->
## Page 52

‘irst Publishing
Atari ST Internals
The Control Register
The eight-bit control register determines internal operations. To solve the
problem of controlling diverse functions with one byte, single bits are set up
as below:
CR
0,1
These bits determine by which factor the transmitter and receiver
clock will be divided. These bits also are joined with a master
reset function. The 6850 has no separate reset line, so it must be
accomplished through software.
CR1
CRO
0
0
RXCLK/TXCLK without
division
0
1
RXCLK/TXCLK
by
16
(for
MIDI)
1
0
RXCLK/TXCLK by
64
(for keyboard)
1
1
Master RESET
CR
2,3,4
These so-called Word Select bits tell whether 7 or 8 data-bits are
involved; whether 1 or 2 stop-bits are transferred; and the type of
parity.
CR4
CR3
CR2
0
0
0
7 databits,
2
stopbits,
even parity
0
0
1
7 databits,
2
stopbits,
odd
parity
0)
1
0
7 databits,
1 stopbit,
even parity
0
1
1
7 databits,
1 stopbit,
odd
parity
1
0
0
8 databits,
2
stopbit,
no
parity
1
0
1
8 databits,
1 stopbit,
no
parity
1
1
0
8 databits,
1 stopbit,
even parity
1
1
1
8 databits,
1 stopbit,
odd
parity
CR 6,5
These Transmitter Control bits set the RTS output pin, and allow
or prevent an interrupt through the ACIA when the send register
is emptied.
Also, BREAK signals can be sent over the serial
output by this line.
A BREAK signal is nothing more than a long
sequence of null bits.
45

<!-- source-page: 53 -->
## Page 53

First Publishing
Atari ST Internal
CR6
CR5
0
0
RTS low, transmitter IRQ disabled
0
1
RTS low, transmitter IRQ enabled
1
0
RTS high,
transmitter
IRQ disabled
1
1
RTS low, transmitter
IRQ disabled, BREAK
sent
CR 7
The Receiver Interrupt Enable bit determines whether the receiver
interrupt will be on. An interrupt can be caused by the DCD line
changing from low to high, or by the receiver data buffer filling.
Besides that, an interrupt can occur from an OVERRUN (a
received character isn't properly read from the processor).
CR7
0
Interrupt disabled
1
Interrupt
enabled
The Status Register
The Status Register gives information about the status of the chip.
It also
has its information coded into individual bytes.
|
SRO
When this bit is high, the RX data register is full. The byte must
be read before a new character can be received (otherwise an
OVERRUN happens).
SRI
This bit reflects the status of the TX data buffer.
An empty
register sets the bit.
SR2
A low-high change on pin DCD sets SR2.
If the receiver
interrupt is allowable, the IRQ will be cancelled.
The bit is
cleared when the status register and the receiver register are read.
This also cancels the IRQ.
SR2 register remains high if the
signal on the DCD pin is still high; SR2 registers low if DCD
becomes low.
46

<!-- source-page: 54 -->
## Page 54

First Publishing
Atari ST Internals
SR3
This line shows the status of CTS. This signal cannot be altered
|
by a master reset, or by ACIA programming.
'SR4
Shows "Frame errors".
Frame errors are when no stop-bit is
|
recognized in receiver switching.
It can be set with every new
character.
‘SRS
i
This
bit displays
the previously mentioned OVERRUN
condition. SRS5 is reset when the RX buffer is read.
| SR6
This bit recognizes whether the parity of a received character is
correct. The bit is set on an error.
SR
7
This signals the state of the IRQ pins; this bit makes it possible to
switch several IRQ lines on one interrupt input.
In cases where
an interrupt is program-generated, SR7 can tell which IC cut off
the interrupt.
The
ACJAs
in the ST
The ACIAs have lots of extras unnecessary to the ST.
In fact, CTS, DCD
and RTS are not connected.
The keyboard ACIA lies at the addresses $FFFCOO and $FFFCO02. Built-in
parameters are:
8-bit word,
1 stopbit, no parity, 7812.5 baud (500
|
kHz/64).
The parameters are the same for the MIDI chip, EXCEPT for the baud rate,
which runs at 31250 baud (500 kHz/16).
47

<!-- source-page: 55 -->
## Page 55

First Publishing
Atari ST Internal
1.6 The YM-2149 Sound Generator
The Yamaha YM-2149, a PSG (programmable sound generator) in the same
family as the General Instruments AY-3-8190,
is
a first-class sound
synthesis chip.
It was developed to produce sound for arcade games. The
PSG also has remarkable capabilities for generating/altering sounds.
Additionally, the PSG can be easily controlled by joysticks, the computer
keyboard, or external keyboard switching. The PSG has two bidirectional
8-bit parallel ports. Here's some general data on the YM-2149:
* three independently programmable tone generators
* a programmable noise generator
* complete software-controlled analog output
* programmable mixer for tone/noise
* 15 logarithmically raised volume levels
* programmable envelopes (ASDR)
* two bidirectional 8-bit data ports
¢ TTL-compatible
¢ simple 5-volt power
The YM-2149 has a
total of 16 registers.
All sound capabilities are
controlled by these registers.
The PSG has several "functional blocks" each with its own job. The tone
generator block produces a square-wave sound by means of a time signal.
The noise generator block produces a frequency-modulated square-wave
signal, whose pulse-width simulates a noise generator. The mixer couples
the three tone generators' output with the noise signal. The channels may
be coupled by programming.
The amplitude control block controls the output volume of the three
channels with the volume registers; or creates envelopes (Attack, Decay,
Sustain, Release, or ADSR), which controls the volume and alters the
sound quality.
The D/A converter translates the volume and envelope information into
digital form, for external use. Finally one function block controls the two
1/O ports.
48

<!-- source-page: 56 -->
## Page 56

‘irst Publishing
Atari ST Internals
Figure 1.6-1 Sound chip YM-2149
vss
(|
Nc.
ANALOG
B
ANALOG
A C
67TC-WA
D) RESET*
D) CLOCK
D IOAO
49

<!-- source-page: 57 -->
## Page 57

First Publishing
Atari ST Internal
1.6.1 Sound Chip Pins
Vss:
This is the PSG ground connection.
NC.:
Not used.
ANALOG B:
This is the channel B output. Maximum output voltage is 1 vss.
ANALOG A:
Works like pin 3, but for channel A.
NC.:
Not used.
IOB7
- 0:
The IOB connections make up one of the two 8-bit ports on the
chip. These pins can be used for either input or output. Mixed
operation (input and output combined) is impossible within one
port, however both ports are independent of one another.
IOA7
- 0:
Like IOB, but for port A.
CLOCK:
All tone frequencies are divided by this signal.
This signal
operates at a frequency between 1 and 2 mHz.
RESET:
A low signal from this pin resets all internal registers. Without a
reset, random numbers exist in all registers, the result being a
rather unmusical "racket".
A9:
This pin acts as a chip select-signal. When it is low, the PSG
registers are ready for communication.
50

<!-- source-page: 58 -->
## Page 58

‘jrst Publishing
Atari ST Internals
\8:
C(EST2:
3DIR &
DAO
- 7:
Similar to A9, only it is active when high.
Test2 is used for testing in the factory, and is unused in normal
operation.
BC1,2:
The BDIR (Bus DiRection), BC1 and BC2 (Bus Control) pins
control the PSG's register access.
DIR
P
nection
Inactive
Latch address
Inactive
Read
from PSG
Latch address
Inactive
Write
to
PSG
Latch address
rPrRRPRPODOO
PRPOOrRROO
POrRPOrFOrF
Om
Only four of these combinations are of any use to us; those with a
5+ voltage running over BC2.
So, here's what we have left:
BDIR
BCl Function
0
Inactive,
PSG data
bus
high
1
Read PSG registers
i)
Write
PSG registers
1
Latch,
write
register number(s)
These pins connect the sound chip to the processor, through the
data bus. The identifier DA means that both data and (register)
addresses can be sent over these lines.
ANALOG C:
FEST 1:
Vice:
Works with channel C (see ANALOG B, above).
See TEST2.
+5 volt pin.
51

<!-- source-page: 59 -->
## Page 59

First Publishing
Atari ST Interna
1.6.2 The 2149 Registers and their Functions
Now let's look at the functions of the individual registers.
a
One point c
interest:
the contents of the address register remain unaltered unt
reprogrammed. You can use the same data over and over, without havin
to send that data again.
These register determine the period length, and the pitch o
ANALOG A.
Not all 16 bits are used here; the eight bits o
register 0 (set frequency) and the four lowest bits of register
(control step size). The lower the 12-bit value in the register, th
higher
the tone.
Same as registers 0 and 1, only for channel B.
Same as registers 0 and 1, only for channel C.
The five lowest bits of this register control the noise generator
Again, the smaller the value, the higher the noise "pitch".
Reg
0,1:
Reg
2,3:
Reg
4,5:
Reg 6:
Reg 7:
Bit
Bit
Bit
Bit
Bit
Bit
Bit
Bit
“TAO BWNE
©
:Channel
:Channel
:Channel
:Channel
:Channel
:Channel
:Port
A in/output
:Port
B in/output
AWPraAw
Pp
tone on/off
tone on/off
tone on/off
noise
on/off
noise
on/off
noise
on/off
52
O=on
O=on
Q=on
O=on
O=on
Q=on
QO=in
O=in
/1=o0f:
/1=o0f:
/1=o0f:
/1l=of
/1=of
/1=o0f
/1=0u1
/1=o0u

<!-- source-page: 60 -->
## Page 60

first Publishing
Atari ST Internals
Figure 1.6-2 Envelopes of the PSG
REG
15
B3
B2
BL
BO
A
Cc
Le
°
Tt
N
A
E
Tr
Tt
R
I
T
N
H
N
A
A
°
Uv
Cc
Tv
i
Jetx
le
|p.
ojo
]-|-
53

<!-- source-page: 61 -->
## Page 61

First Publishing
Atari ST Internal
Reg 8:
Bits 0-3 of this register contrrol the signal volume of channel A
When bit 4 is set, the envelope register is being used and th
contents of bits 0-3 are ignored
Reg 9:
Same as register 8, but for channel B.
Reg
10:
Same as register 8, but for channel C.
Reg
11,12:
The contents of register 11 are the low-byte and the contents 0
register 12 are the high-byte of the sustain.
Reg
13:
Bits 0-3 determine the waveform of the envelope generator. Th
possible envelopes are pictured in Figure 1.6-2.
Reg
14,15:
These registers comprise the two 8-bit ports.
Register 14
i:
connected to Port A and register 15 is connected to Port B.
I
these ports are programmed as output (bits 7 and 8 of register 7
then values may be sent through these registers.
54

<!-- source-page: 62 -->
## Page 62

First Publishing
Atari ST Internals
1.7 I/O Register Layout in the ST
The entire I/O range (all peripheral ICs and other registers) is controlled by a
32K address register
-- $FF8000 - $FFFFFF. Below is a complete table of
the different registers. CAUTION: The I/O section can be accessed only in
supervisor mode. Any access in user mode results in a bus-error.
SFF8000
SFF8200
SFF8400
SFF8600
SFF8800
SFFFAOO
SFFFCOO
Memory configuration
Video display register
Reserved
DMA/disk controller
Sound chip
MFP
68901
ACIAs
for MIDI
and keyboard
The addresses given refer only to the start of each register, and supply no
hint as to the size of each. More detailed information follows.
$FF8000___
Memory Configuration
There
is
a single 8-bit register
at $FF8001
in which the memory
configuration is set up (four lowest bits).
The MMU-IC is designed for
maximum versatility within the ST.
It lets you use three different types of
memory expansion chips: 64K, 256K, and the 1M chips. Since all of these
ICs are bit-oriented instead of byte-oriented, 16 memory chips of each type
are required for memory expansion.
The identifier for 1€ such chips
(regardless of memory capacity) is BANK.
So, expansion is possible to
128 Kbyte,
512 Kbyte or even 2 Megabytes.
MMU can control two banks at once, using the RAS- and CAS- signals.
The table on the next page shows the possible combinations:
55

<!-- source-page: 63 -->
## Page 63

First Publishing
Atari ST Internal
SFF8001
Bit
Memory configuration
3-0
Bank
0
Bank
1
0000
128K
128K
0001
128K
512K
0010
128K
2M
0011
reserved
0100
512K
128K
0101
512K
512K
0100
512K
2 M,normally reserved
0100
reserved
1000
2M
128K
1001
2M
512K
1010
2M
2M
1011
reserved
11XX
reserved
The memory configuration can be read from or written to.
$FF8200
Video
Display
Resist
This register is the storage area that determines the resolution and the colo.
palette of the video display.
SFF8201
8-bit
Screen memory position
(high-byte)
SFF8203
8-bit
Screen memory position
(low-byte)
These two read/write registers are located at the beginning of the 32K video
RAM.
In order to relocate video RAM, another register is used. This register is
three bytes long and is located at $FF8205. Video RAM can be relocated in
256-byte incremeents.
Normally the starting address of video RAM is
$78000.
SFF8205
8-bit
Video address pointer
(high-byte)
SFF8207
8-bit
Video address pointer
(mid-byte)
SFF8209
8-bit
Video address pointer
(low-byte)
These three registers are read ONLY.
Every three microseconds, the
contents of these registers are incremented by 2.
56

<!-- source-page: 64 -->
## Page 64

irst Publishing
Atari ST Internals
iFF820A BIT
Synchronization mode
10
:
i-- O=internal,1=external synchronization
:----
0=60
Hz,
1=50Hz
screen
frequency
[he bottom two bits of this register control synchronization mode; the
emaining bits are unused.
If bit 0 is set, the HSync and VSync impulses
ure shut off, which allows for screen synchronization from external sources
‘monitor jack).
This offers new realm of possibilities
in video,
synchronization of your ST and a video camera, for example.
Bit 1 of the sync-mode register handles the screen frequency.
This bit is
aseful only in the two "lowest" resolutions. High-res operation puts the ST
at a 70 Hz screen frequency.
Sync mode can be read/written.
SFF8240
16-bit
Color palette register
0
SFF8242
16-bit
Color palette register
1
Color palette registers
2-13
SFF825C
16-bit
Color palette register
14
SFF825E
16-bit
Color palette register
15
Although the ST has a total of 512 colors, only 16 different colors can be
displayed on the screen at one time. The reason for this is that the user has
16 color pens on screen, and each can be one of 512 colors.
The color
palette registers represent these pens. All 16 registers contain 9 bits which
affect the color:
FEDCBA9876543210
wee XXX.XXX.
XXX
The bits marked X control the registers.
Bits 0-2 adjust the shade of blue
desired; 4-6, green hue; and 8-A, red.
The higher the value in these three
bits, the more intense the resulting color.
Middle resolution (640 X 200 points) offers four different colors; colors 4
through 15 are ignored by the palette registers.
When you want the maximum of 16 colors, it's best to zero-out the contents
of the palette registers.
57

<!-- source-page: 65 -->
## Page 65

First Publishing
Atari ST Interna
High-res (640 X 400 points) gives you a choice on only one "color"; bit:
of palette register 0 is set to the background color.
If the bit is cleared, the
the text is black on a light background. A
set bit reverses the screen (ligh
characters, black background). The color register is a read/write register.
SFF8260
Bit
Resolution
10
0
0
320
X
200 points,
four
focal planes
O
1
640
X 200 points,
two
focal planes
1
0
640
X
400 points,
one
focal planes
This register sets up the appropriate hardware for the graphic resolutio1
desired.
SFF8600__
DM A/Disk_Controller
SFF8600
reserved
SFF8602
reserved
SFF8604
16-bit
FDC access/sector
count
The lowest 8 bits access the FDC registers.
The upper 8 bits contain nc
information, and consistently read 1. Which register of the FDC is usec
depends upon the information in the DMA mode control register a
$FF8606. The FDC can also be accessed indirectly.
The sector count-register under $FF8604 can be accessed when the
appropriate bit in the DMA control register is set.
The contents of these
addresses are both read/write.
SFF8606
16-bit
DMA mode/status
When this register is read, the DMA status is found in the lower three bits o
the register.
Bit
O
O=no
error,
1=DMA error
Bit
1
O=sector
count
= null,
1=sector count<>null
Bit
2
Condition
of
FDC DATA REQUEST
Signal
Write access to this address controls the DMA mode register.
58

<!-- source-page: 66 -->
## Page 66

rst Publishing
Atari ST Internals
Bit
0
unused
Bit
1
O=pin
AO
is
low
1=pin
AO
is
high
Bit
2
O=pin
Al
is
low
l=pin
Al
is high
Bit
3
O=FDC access
1=HDC access
Bit
4
O=access
to FDC register
l=access
to
sector
count
register
Bit
5
O,
reserved
Bit
6
O=DMA
on
1=no
DMA
Bit
7
O=hard disk controller
access
(HDC)
1=FDC access
Bit
8
O=read FDC/HDC registers
l=write
to FDC/HDC registers
‘FEF8609
8-bit
DMA basis
and counter high-byte
‘FE 860B
8-bit
DMA basis
and counter mid-byte
‘FF 860D
8-bit
DMA basis
and counter
low-byte
JMA transfer will tell the hardware at which address the data is to be
noved. The initialization of the three registers must begin with the low-byte
f the address, then mid-byte, then high-byte.
|
‘
fhe YM-2149 has 16 internal registers which can't be directly addressed.
nstead, the number for the desired register is loaded into the select register.
The chosen registers can be read/write, until a new register number is
vritten to the PSG.
FF 8800
8-bit
Read data/Register select
ceading this address gives you the last register used (normally port A), by
vhich disk drive is selected. This can be accomplished with write-protect
ignals, although these protected contents can be accessed by another
egister. Port A is used for multiple control functions, while port B is the
inter data port.
59

<!-- source-page: 67 -->
## Page 67

First Publishing
Atari ST Intern:
PORT
A
Bit
0
Page-choice
signal
for double-sided
floppy drive
Bit
1
Drive
select
signal
--
floppy drive
0
Bit
2
Drive
select
signal
--
floppy drive
1
Bit
3
RS-232 RTS-output
Bit
4
RS-232 DTR output
Bit
5
Centronics
strobe
Bit
6
Freely usable output
(monitor
jack)
Bit
7
reserved
When $FF8800 is written to, the select register of the PSG is alerted.
TI
information in the bottom four bits are then considered as register numbe1
The necessary four-bit number serves for writing to the PSG.
SFF8802
8-bit
Write data
Attempting to read this address after writing to it will give you $FF onl
while BDIR and BC1 are nulls.
Writing register numbers and data can be performed with a single MOVE
instruction.
S$SFFFA00_
MFP 68901
The
MEFP's
24
registers
are
found
at
uneven
addresses
fro:
$FFFAO1-$FFFA2F:
SFFFAO1
8-bit
Parallel port
SFFFA03
8-bit
Active
Edge
register
SFFFAO05
8~bit
Data direction
SFFFA0O7
8-bit
Interrupt
enable
A
SFFFAO9
8-bit
Interrupt
enable
B
SFFFAOB
8-bit
Interrupt pending
A
SFFFAOD
8-bit
Interrupt pending
B
SFFFAOF
8-bit
Interrupt
in-service
A
SFFFA11
8-bit
Interrupt
in-service
B
SFFFA13
8-bit
Interrupt mask
A
SFFFA15
8-bit
Interrupt
mask
B
SFFFA17
8-bit
Vector register
SFFFA19
8-bit
Timer
A control
SFFFAI1B
8-bit
Timer
B
control
60

<!-- source-page: 68 -->
## Page 68

irst Publishing
Atari ST Internals
FFFAID
8-bit
Timer
C
&
D
control
FFFAILF
8-bit
Timer
A data
FFFA21
88-bit
Timer
B
data
FFFA23
8-bit
Timer
C
data
(FFFA25
B8-bit
Timer
D
data
iFFFA27
8-bit
Sync character
iFFFA29
8-bit
USART control
i3FFFA2B
8-bit
Receiver
status
3FFFA2D
88-bit
Transmitter
status
3FFFA2F
8-bit
USART
data
see the chapter on the MFP for details on the individual registers.
[I/O Port
3it
0
Centronics busy
Zit
1
RS-232
data carrier detect
-
input
Bit
2
RS~232
clear
to
send
-
input
Bit
3
reserved
Bit
4
keyboard and MIDI
interrupt
Bit
5
FDC and HDC interrupt
Bit
6
RS-232
ring indicator
Bit
7
Monochrome monitor detect
Timers A and B each have an input which can be used by external timer
control, or send a time impulse from an external source. Timer A is unused
in the ST, which means that the input is always available, but it isn't
connected to the user port, so the Centronics busy pin is connected instead.
You can use it for your own purposes.
Timer B is used for counting screen lines in conjunction with DE (Display
Enable).
The timer outputs in A-C are unused. Timer D, on the other hand, sends
the timing signal for the MFP's built-in serial interface.
61

<!-- source-page: 69 -->
## Page 69

First Publishing
Atari ST Intern:
FFF
a
The communications between
the
ST,
the keyboard,
and music
instruments are handled by two registers in the ACIAS.
SFFFCOO
8-bit
Keyboard ACIA control
SFFFCO2
8-bit
Keyboard ACIA data
SFFFCO04
8-bit
MIDI ACIA control
SFFFCO06
8-bit
MIDI ACIA data
Figure 1.7-1 I/O Assignments
SFFFCOD
2 ACIA’s 6580
MFP 68901
$FFFA00
|
SOUND AY-3-8910
$FF8800
DMA / WD 1770
$FF8600
:
RESERVED
$FF8400
VIDEO CONTROLLER
$FF 8200
DATA CONFIGURATION
$FF 38000
62

<!-- source-page: 70 -->
## Page 70

lirst Publishing
Atari ST Internals
Figure 1.7-2 Memory Map of the ATARI ST
$FF FCOO
$FF
SFF
FAGO
8800
8600
8400
8200
$FF 8000
SFE FFFF
$FC 0000
$FA 0000
$07 FFFF
$00 0000
VO - Area
192 K
System ROM
128
K ROM
Expansion Cartridge
312 K RAM
63
16776192
16775680
16746496
16745984
16745472
16744960
16744448
16711679
16515072
16384000
924287

<!-- source-page: 71 -->
## Page 71

First Publishing
Atari ST Intern:
7

<!-- source-page: 72 -->
## Page 72

irst Publishing
Atari ST Internals
Chapter Two
|
The Interfaces
1
The Keyboard
1.1
The Mouse
.1.2 Keyboard commands
2
The Video Connection
2.3
The Centronics Interface
2.4
The RS-232 Interface
2.5
The MIDI Connections
2.6
The Cartridge Slot
2.7
The Floppy Disk Interface
2.8
The DMA Interface

<!-- source-page: 73 -->
## Page 73

First Publishing
Atari ST Interna
a

<!-- source-page: 74 -->
## Page 74

‘irst Publishing
Atari ST Internals
The Interfaces
2.1 The Keyboard
Do you think it's really necessary to give a detailed report on something
as
trivial as the keyboard, since keyboards all function the same way? Actually
the title should read "Keyboard Systems" or something similar. The
keyboard is controlled by its own processor. You will soon see how this
affects the assembly language programmer.
.
The keyboard processor is single-chip computer (controller) from the 6800
family, the 6301. Single chip means that everything needed for operation is
found on a single IC. In actuality, there are some passive components in the
keyboard circuit along with the 6301.
The 6301 has ROM, RAM, some I/O lines, and even a serial interface on
the chip. The serial interface handles the traffic to and from the main board.
The advantage of this design is easy to see. The main computer is not
burdened by having to continually poll the keyboard. Instead it can dedicate
itself completely to processing your programs. The keyboard processor
notifies the system if an event occurs that the operating system should be
aware of.
The 6301 is not only responsible for the relatively boring task of reading the
keyboard, however. It also takes care of the rather complicated tasks
required in connection with the mouse. The main processor is then fed
simply the new X and Y coordinates when the mouse is moved. Naturally,
anything to do with the joysticks is also taken care of by the keyboard
controller.
In addition, this controller contains
a real-time clock which counts in
one-second increments.
67

<!-- source-page: 75 -->
## Page 75

First Publishing
Atari ST Internal
Figure 2.1-1 6850 Interface to 68000
nm
<<
|
+
har
Mw
MM
H
mM
142
wy)
Ow
p<
Ce)
qwnn
fd
F&F WN
oD
&
€
|
A
o
S
1
&
i=]
in
~
©
oO
(sy
©
A
oO
9)
oO
wn
|
68

<!-- source-page: 76 -->
## Page 76

‘irst Publishing
Atari ST Internals
n Figure 2.1-1 is an overview of the interface to the 68000. As you see, the
nain processors is burdened as little as possible. The ACIA 6850 ensures
hat it is disturbed only when a byte has actually been completely received
rom the keyboard. The ACIA, by the way, can be accessed at addresses
3FFFCO0 (control register) and $FFFCO2 (data register). The individual
-onnection to the keyboard takes place over lines K14 and K15. K indicates
he plug connection by which the keyboard is connected to the main board.
The signal that the ACIA has received a byte is first sent over line 14 to the
MFP 68901 which then generates an interrupt to the 68000. The clock
frequency of 500KHz comes from GLUE. From this results the "odd"
transfer rate of 7812.5 baud.
In case you were surprised that data can also be sent to the keyboard
processor, you will find the solution to the puzzle in Chapter 2.1.2.
The block diagram of the keyboard circuit is found in Figure 2.1-2. The
function is as simple as the figure is easy to read. The processor has 4K of
ROM available. The 128 bytes of RAM is comparitively small, but it is used
only as a buffer and for storing pointers and counters.
The lines designated with K are again the plug connections assigned to the
main board. With few exceptions, the connections for the joystick and
mouse are also put through. K16 is the reset line from the 68000. K15
carries the send data from the 6850, K14 the send data from the 6301.
The I/O ports 1(0-7), 3(1-7), and 4(0-7) are responsible for reading the
keyboard matrix. One line from ports 3 and 4 is pulled low in a cycle. The
state of port
1 is the checked. If a key is pressed, the low signal comes
through on port 1.
Each key can be identified from the combination of value placed on ports 3
and 4 and the value read from port 1.
If none of the lines of Port 3 and 4 are placed low and a
bit of port
1 still
equals zero, a joystick is active on the outer connecter 1. The data from
outer connector 0, to which a mouse or a joystick can be connected, does
not come through by chance since it must first be switched through the
NAND gate with port 2 (bit 0). The buttons on the mouse or the joystick
then arrive at port 2 (1 and 2).
69

<!-- source-page: 77 -->
## Page 77

First Publishing
Atari ST Interna
Figure 2.1-2 Block Diagram of Keyboard Circuit
16
15
14
a
OK
N
fo)
a
orn
se my
ea
a
qd
a
70
“tI
ball
rs.
rel
Cr)

<!-- source-page: 78 -->
## Page 78

‘irst Publishing
Atari ST Internals
The assignments of the K lines to the signal names on the outer connecter
tre found in the next section.
[he processor 6301 is completely independent, but it can also be configured
30 that it works with an external ROM. Some of the port lines are then
reconfigured to act as address lines. The configuration the processor
assumes (one of eight possibilities) depends on the logical signal placed on
port 2 (bits 0-2) during the reset cycle. All three lines high puts the
processor in mode 7, the right one for the task intended here. But bits
1 and
2 depend on the buttons on the mouse. If you leave the mouse alone while
powering-up, everything will be in order. If you hold the two buttons
down, however, the processors enters mode
1 and makes a magnificent
belly-flop, since the hardware for this operating mode is not provided. You
notice this by the fact that the mouse cursor does not move on the screen if
you move the mouse. Only the reset button will restore the processor.
2.1.1 The Mouse
The construction of this
little device
is quite simple, but effective.
Essentially, it consists of four light barriers, two encoder wheels, and a
drive mechanism.
The task of the mouse is to give the computer information about its
movements. This information consists of the components: direction on the
X-axis, direction on the Y-axis, and the path traveled on each axis.
In order to do this, the rubber-covered ball visible from the outside drives
two encoder wheels whose drive axes are at angle of 90 degrees to each
other. The one or the other axis rotates more or less, forwards
or
backwards, depending on the direction the mouse is moved.
It is no problem to determine the absolute movement on each axis. The
encoder wheels alternately interrupt the light barriers. One need only count
the pulses from each wheel to be informed about the path traveled on each
axis.
71

<!-- source-page: 79 -->
## Page 79

First Publishing
Atari ST Interna
a
Figure 2.1.1-1_ The Mouse
ol
XA
ae
XB
O—0
Oo]
lo
0
60
O40
29 8
ol>
YA
OP
213
4
#7
~~
8
6
9
72

<!-- source-page: 80 -->
## Page 80

first Publishing
Atari ST Internals
[t is more difficult when the direction of movement is also required. The
designers of the mouse used a convenient trick for this. There are not one,
but two light barriers on each encoder wheel. They are arranged such that
they are not shielded by the wheel at precisely the same time, but one
shortly after the other. This arrangement may not be so clear in Figure
2.1.1-1, so we'll explain it in more detail The direction can be determined
by noticing which of the two light barriers is interrupted first. This is why
the pulses from both light barriers are sent out, making a total of four.
Corresponding to their significance they carry the names XA, XB, YA, YB.
The two contacts which you see on the picture represent the two buttons.
The large box on the picture is a quad operational amplifier which converts
the rather rough light-barrier pulses into square wave signals.
In Figure 2.1.1-2 is the layout of the control port on the computer, as you
see it when you look at it from the outside. The designation behind the slash
applies when a joystick is connected and the number in parentheses is the
pin number of the keyboard connector.
Port 0
1
XB/UP
(K12)
2
XA/DOWN
(K10)
3
YA/LEFT
(K9)
4
YB/RIGHT
(K8)
6
LEFT BUTTON/FIRE
(K11)
7
+5V
(K13)
8
GND
(K1)
9
RIGHT BUTTON
(K6)
Port 1
1
UP
(K7)
2
DOWN
(KS)
3
LEFT
(K4)
4
RIGHT
(K3)
5
Port 0 enable
(K17)
6
FIRE
(K6)
7
+5V
(K13)
8
GND
(K1)
73

<!-- source-page: 81 -->
## Page 81

First Publishing
Atari ST Internal
Figure 2.1.1-2 Mouse control port
XS
6
9
2.1.2 Keyboard commands
The keyboard processor "understands" some commands pertaining to such
things as how the mouse is to be handled, etc. You can set the clock time,
read the internal memory, and so on. You can find an application example in
the assembly language listing on page 80 (after command $21).
The "normal" action of the processor consists of keeping an eye on the
keyboard and announcing each keypress. This is done by outputting the
number of the key when the key is pressed. When the key is released the
number is set again, but with bit 7 set. The result of this is that no key
numbers greater than 127 are possible. You can find the assignment of the
key numbers to the keys at the end of this section in figure 2.1.2-1. In
reality these numbers only go up to 117 because values from $F6 up are
reserved for other purposes. There must be a way to pass more information
than just key numbers to the main processor, information such as the clock
time or the current position of the mouse. This cannot be handled in a single
byte but only in something called a package, so the bytes at $F6 signal the
Start of
a package. Which header comes before which package is explained
along with the individual commands.
A command to the keyboard processor consists of the command code (a
byte) and any parameters required. The following description is sorted
according to command bytes.
$07
Returns
the result of pressing one of the two mouse buttons. A parameter
byte with the following format is required:
74

<!-- source-page: 82 -->
## Page 82

first Publishing
Atari ST Internals
3it
0
=1:
The absolute position
is
returned when
a
mouse button
is pressed.
Bit
2 must
=0.
Bit
1
=1:
The absolute position
is returned when
a
mouse button
is
released.
Bit
2 must
=0.
Bit
2
=1:
The mouse buttons
are treated like
normal
keys.
The
left button
is
key
number
$74,
the
right
is
$75.
Bits
3-7
must
always
be
zero.
$08
Returns the relative mouse position from now on. This command tells the
keyboard processor to automatically return the relative position (the distance
from the previous position) whenever the mouse is moved.
A movement is
given when the number of encoder wheel pulses has reached a given
threshold. See also $0B. A
relative mouse package looks like this:
l byte
Header
in range $F8-SFB.
The two
lowest
bits
of the header
indicate the condition
of
the
two mouse buttons.
l byte
Relative X-position
(signed!)
1 byte
Relative Y-position
(signed!)
If the relative position changes substantially between two packages so that
the distance can no longer be expressed in one byte, another package is
automatically created which makes up for the remainder.
$09
Returns the absolute mouse position from now on. This command also sets
the coordinate maximums. The internal coordinate pointers are at the same
time set to zero. The following parameters are required:
1
word
Maximum X~coordinate
1
word
Maximum Y-coordinate
Mouse movements under the zero point or over the maximums are not
returned.
$0A
With this command it is possible to get the key numbers of the cursor keys
instead of the coordinates.
A mouse movement then appears to the operating
system as if the corresponding cursor keys had been pressed. These
parameters are necessary:
75

<!-- source-page: 83 -->
## Page 83

First Publishing
Atari ST Internal
1 byte
Number
of pulses
(X)
after which the
key
number
for cursor
left
(or right)
will
be
sent.
1
byte
Number
of pulses
(Y)
after which the
key
number
for
cursor
up
(or
down)
will
be
sent.
$O0B
This command sets the trigger threshold, above which movements will bi
announced. A certain number of encoder pulses elapse before a package i:
sent. This functions only in the relative operating mode. The following ar
the parameters:
1 byte
Threshold
in X-direction
1
byte
Threshold
in Y-direction
$0C
Scale mouse. Here is determined how many encoder pulses will go by
before the coordinate counter is changed by 1. This command is valid onl;
in the absolute. The following parameters are required:
1 byte
X scaling
1 byte
Y scaling
$0D
Read absolute mouse position. No parameters are required, but a package o
the following form is sent:
1 byte
Header
=
SF7
1
byte
Button
status
Bit
0
=
1:
Right button
was pressed
since
the
last
read
Bit
1
=
1:
Right button
was
not pressed
Bit
2
=
1:
Left button
was pressed since
the
last
read
Bit
3
=
1:
Left
button
was
not pressed
From this strange arrangement you can determine that the state of a butto
has changed since the last read if the two bits pertaining to it are zero.
1
word
Absolute
X-coordinate
1
word
Absolute
Y-coordinate
76

<!-- source-page: 84 -->
## Page 84

First Publishing
Atari ST Internals
$0E
Set the internal coordinate counter. The following parameters are required:
1 byte
=0
as
fill byte
1
word
X-coordinate
1 word
Y-coordinate
$OF
Set the origin for the Y-axis is down (next to the user).
$10
Set the origin for the Y-axis is up.
$11
The data transfer to the main processor is permitted again (see $13).
Any command other than $13 will also restart the transfer.
$12
Turn mouse off. Any mouse-mode command ($08, $09, $0A) turns the
mouse back on. If the mouse is in mode $0A, this command has no effect.
$13
_ Stop data transfer to main processor.
NOTE: Mouse movements and key presses will be stored as long as the
| small buffer of the 6301 allows. Actions beyond the capacity of the buffer
will be lost.
$14
Every joystick movement is automatically returned. The packages sent have
the following format:
1 byte
Header
=
SFE
or
SFF
for
joystick
0/1
1 byte
Bits
0-3
for
the position
(a bit
for
each
direction),
bit
7
for the button
$15
End the automatic-return mode for the joystick. When needed, a package
must be requested with $16.
$16
Read joystick. After this command the keyboard sends
a package as
described above.
77

<!-- source-page: 85 -->
## Page 85

First Publishing
Atari ST Internal:
$17
Joystick duration message. One parameter is required.
1 byte
Time between two messages
in
1/100
sec.
From this point on, packages of the following form are sent continuously
(as long as no other mode is selected):
1 byte
Bit
0
for
the button
on
joystick
1,
bit
1
for that
of
joystick
0
1 byte
Bits
0-3
for
the position
of
joystick
1,
bits
4-7
for
the position
of
joystick
0
NOTE: The read interval should not be shorter than the transfer channel
needs to send the two bytes of the package.
$18
Fire button duration message. The condition of the button in joystick 1 (!) is
continually tested and the result packed into a byte. This means that a
message byte contains 8 such tests, whereby bit 7 is the most recent. The
keyboard controller determines the time between byte fetches by the main
processor. This time is divided into eight equal intervals in which the button
is polled. The polling then takes place as regularly as possible. This mode
remains active until another command is received.
$19
Cursor key simulation mode for joystick 0 (!). The current position of the
joystick is sent to the main processor as if the corresponding cursor keys
had been pressed (as often as necessary). To avoid having to explain the
same things for the following parameters, here are the most important: All
times are assumed to be in tenths of seconds. R indicates the time, when
reached, cursor clicks will be sent in intervals of T. After this the interval is
V. If R=0, only V is responsible for the interval. Naturally, this mechanism
comes into play only when the joystick is held in the same position for
longer than T or R.
|
1
byte
RX
1
byte
RY
1
byte
TX
1
byte
TY
1
byte
VX
1
byte
VY
78

<!-- source-page: 86 -->
## Page 86

First Publishing
Atari ST Internals
$1A
Turn off joysticks. Any other joystick command turns them on again.
$1B
Set clock time. This command sets the internal real-time clock in the
keyboard processor. The values are passed in packed BCD, meaning a digit
0-9 for each half byte, yielding a two-digit decimal number per byte. The
following parameters are necessary:
1 byte
Year,
two digit
(85,
86,
etc.)
1 byte
Month,
two digit
(12,
01,
etc.)
1 byte
Day,
two digit
(31,01,02,
etc.)
1 byte
Hours,
two digit
1 byte
Minutes,
two digit
1 byte
Seconds,
two digit
Any half byte which does not contain a valid BCD digit (such as F) is
ignored. This makes it possible to change just part of the date or clock time.
, $1C
Read clock time. After receiving this command the keyboard processor
returns a package having the same format as the one described above. A
header is added to the package, however, having the value $FC.
$20
Load memory. The internal memory of the keyboard processor (naturally
only the RAM in the range $80 to $FF makes sense) can be written with this
command. It is not clear to us of what use this is since according to our
investigations (we have disassembled the operating system of the 6301), no
RAM is available to be used as desired. Perhaps certain parameters can be
changed in this manner which are not accessible through "legal" means.
Here are the parameters:
1
word
Start
address
1 byte
Number
of bytes
(max.
128)
Data bytes
(corresponding
to
the number)
The interval at which the data bytes will be sent must be less than 20 msec.
79

<!-- source-page: 87 -->
## Page 87

First Publishing
Atari ST Internal:
$21
Read memory. This command is the opposite of $20. These parameters are
required:
1
word
Address
at which
to
read
A package having the following format is returned:
1 byte
Header
1
=SF6.
This
is the
status header
which precedes
all packages containing
any
operating conditions
of the keyboard
processor.
We will
come
to the general
status messages
shortly.
1 byte
Header
2
=$20
as indicator that this
package
carries
the memory
contents.
6 bytes
Memory contents
starting with the address
given
in
the
command.
Here is a small program which we used to read the ROM in the 6301 and
output it to a printer. Here you also see how the status packages arrive from
the keyboard. These are normally thrown away by the 68000 operating
system. Section 3.1 contains information about the GEMDOS and XBIOS
calls used.
1
prt
equ
0
2
chout
equ
3
3
gemdos
equ
1
4
bios
equ
13
5
xbios
equ
14
6
stvec
equ
12
7
rdm
equ
$21
8
wrkbd
equ
25
9
kbdvec
equ
34
10
term
equ
0
11
start:
12
00000000
3F3C0022
move.w
#kbdvec,-(a7)
13
00000004
4E4E
trap
#xbios
14
00000006
548F
addgq.1
#2,a7
15
00000008 41F900000000
lea
0,a0
16
QOOOO00OE 43F9000000D6
lea
keyin,al
17
00000014
23C000000104
move.l
d0,savea
18
O000001A 23F0000C00000100
move.l
stvec(a0,d0),save
19
00000022
2189000C
move.l
al,stvec(a0,d0)
80

<!-- source-page: 88 -->
## Page 88

first Publishing
Atari ST Internals
20
00000026 383CF000
move.w
#$£000,d4
21
loop:
22
0000002A 33C40000010A
move.w
d4,tbuf+l
23
00000030
61000084
bsr
keyout
24
wait:
25
00000034 0c390000000000F8
cmpi.b
#0,rbuf
26 0000003C
67F6
beq
wait
27
0000003E 3C3C0006
move.w
#6,d6
28
00000042
610A
bsr
bufout
29 00000044
5c44
addq.w
#6,d4
30
00000046 OC44FFFF
cmpi.w
#Sffff,d4
31
O000004A
6DDE
blt
loop
32
0000004C
6052
bra
exit
33
bufout:
34
OCOOCOO4E 49F9000000F9
lea
rouf+1,a4
35
bytout:
36
00000054
101¢
move.b
(a4)+,da0
37
00000056
6106
bsr
hexout
38
00000058
5306
subq.b
#1,d6
39
OOOD0COSA
6EF8
bne
bytout
40
0000005C
4E75
rts
41
hexout:
42
QOOO0OSE
3240
movea.w d0,al
43
00000060 E808
lsr.b
#4,a0
44
00000062
02800000000F
andi.1
#15,d0
45
00000068
47F9000000E8
lea
table, a3
46 OOO0006E 14330000
move.b
0(a3,d0),d2
47
00000072
E14A
lsl.w
#8,d2
48
00000074
3009
move.w
al,d0
49
00000076 02800000000F
andi.l
#15,d0
50
0000007C
14330000
move.b
0(a3,d0),d2
51
00000080
3002
move.w
d2,d0
52
00000082
3F02
move.w
d2,~-{(a7)
53
00000084
F048
isr.w
#8,d0
54
00000086
6108
bsr
chrout
55
00000088
301F
move.w
(a7) +,d0
56
OQOOO008A
6104
bsr
chrout
57
0000008C
103c0020
move,b
#"
",d0
58
chrout:
539
00000090
3F00
move.w
d0,~-(a7)
60
00000092
3F3Cc0000
move.w
#prt,-(a7)
61
00000096 3F3C0003
move.w
#chout,-(a7)
62
QOQOOOOSA
4E4D
trap
#bios
63
0000009C
5C8F
addq.1
#6,a7
64
QOO0009E
4F75
rts
65
exit:
66
OO0000A0
307900000104
movea
savea,a0
81

<!-- source-page: 89 -->
## Page 89

First Publishing
Atari ST Internal
67
68
69
70
71
72
73
74
75
76
77
78
19
80
81
82
83
84
85
86
87
88
88
a9
90
91
92
93
94
95
OOO000AG6
OOOOCOOAC
O00000B0
OO00000B4
OOO000B6
OOOQOOOBE
000000C4
o000000C8
ooo0000cc
QO0000CE
Q00000D4
Oo0000DE
OOOO00DA
OOO000EO
OOO0000E2
OO00000E4
OOCOO0E6
QOOOOCOES
COOO0OFO
oooooors
00000100
00000104
00000108
00000109
OOO0010A
0000010C
203900000100
2140000C
3F3C0000
4E41
13FCO000000000F8
487900000109
3F3C0002
3F3C0019
4E4k
DFFCO00000008
4E75
103C0008
43F9000000F8
12D8
5300
66FA
4E75
3031323334353637
3839414243444546
21
keyout:
keyin:
repin:
table;
rbuf:
save
savea
dummy
tbuf
82
move.1
move.1
move .w
trap
move .b
pea
move .w
move .w
trap
adda.1
rts
move.b
lea
move .b
subq.b
bne
rts
Q
w
ooo HPS
-end
save, do
do, stvec (a0)
#term,
- (a7)
#gemdces
#0,rbuf
thuf
#2,-(a7)
#wrkbd,
- (a7)
#xbios
#8,a7
#8,d0
rbuf,al
(a0)
+, (al)+
#1,d0
repin
"012345678 9ABCDEF"
rR eo
rdm

<!-- source-page: 90 -->
## Page 90

‘irst Publishing
Atari ST Internals
522
xecute routine. With this command you can execute a subroutine in the
9301. Naturally, you must know exactly what it does and where it is
ocated, so long as you have not transferred it yourself to RAM with $20
assuming you found some free space). The only required parameters are:
lL
word
Start
address
Status messages
You can at any time read the operating parameters of the keyboard by
simply adding $80 to the command byte with which you would to set the
yperating mode (whose parameters you want to know). You then get a
status package back (header=$F6), whose format corresponds exactly to
those which would be necessary for setting the operating mode.
An example makes it clearer: you want to know how the mouse is scaled.
So you send as the command the value $8C (since $0C sets the scaling).
You get the following back:
1 byte
Status header =SF6
1 byte X-scaling
1 byte
Y-scaling
This is the same format which would be necessary for the command $0C.
For commands which do not require parameters, you get the evoked
ommand back as such. For example, say you want to know what operating
mode the joystick is in ($14 or $15). You send the value $94 (or $95, it
makes no difference). As status package you receive, in addition to the
neader, either $14 or $15 depending on the operating mode of the joystick
andler.
llowed status checks are: $87, $88, $89, $8A, $8B, $8C, $8F, $90, $92,
94, $99, and $9A.
n conclusion we have a
tip for those for whom the functions of the
eyboard are too meager and who want to give it more "intelligence". The
rocessor 6301
is also available in "piggy-back" version, the 63P01
(Hitachi). This model does not have ROM built in, but has a socket on the
top for an EPROM of type 2732 or 2764 (8K!). You can then realize your
own ideas and, for example, use the two joystick connections as universal
4-bit I/O ports, for which you can also extend the command set in order to
access the new functions from the XBIOS as well.
83

<!-- source-page: 91 -->
## Page 91

First Publishing
Atari ST Internal
Figure 2.1.2-1 ATARI ST Key Assignments
N
°}
°
>
fa)
OT
n
DSN
Oo
w
wo
w
a
°
©
o
H
Nn
w
°
PSN
w
a
x)
°
a
tad
w
an
Lad
w
o-?
is}
N
°
So
n
4
»
i)
w
°
m
Nn
°
hs
uw
nd
w
w
rors
my
tw
°
L)
e
n
N
-~
Dad
N
o
w
°
°
e
ae)
w
nN
w
»
©
w
al
w
°
ns
ro)
w
a
»
~
is)
w
°
w
-
©
lad
~~
~
w
w
w
°
w
aa
»
Nn
«©
>
an
~
w
°
oo
B
wo
wn
©
wl]
w
°
a
‘a
a
Ld
»
)
w
°
»
i-]
w
w
an
w
u
©
a
°
w
nv
w
w
w
~
w
w
&
a
ww
w
°
~
an
-
e
0
_
an
n
rN
n
a)
Ss
»
~~
wo
°
an
n
a
n
wa
wo
2
~
“1
a
a
a
an
ay
a
©
w
~
~
~
a
N
"
»
an
84

<!-- source-page: 92 -->
## Page 92

‘irst Publishing
Atari ST Internals
2.2 The Video Connection
Without this, nothing would be displayed. You would be tapping in the
dark in the truest sense of the word. Conspicuous are the many pins on the
connection. Naturally more lines are required for hooking up an RGB
monitor than for
a monochrome screen, but seven would be enough. There
is also something special about the remaining lines. In Figure 2.2-1 you
find a block diagram in which you can see how the video connection is tied
to the system. The numbering of the pins is given on the figure on the next
page, aS you can see, when you look at the connector from the outside.
Here is the pin layout:
1
AUDIO OUT. This connection comes from the amplifier
connected to the output of the sound chip. A high-impedance
earphone can be attached here if you do not use the original
monitor.
2
Not used
3
GPO, General Purpose Output. This connection is available for
your use. The line has TTL levels and comes from I/O port A
bit 6
of the sound chip.
4 MONOCHROME DETECT. If this line, which leads to the I7
input of the MFP 68901,
is low, the computer enters
the
high-resolution monochrome mode. If the state of the line changes
during operation, a cold start is generated.
5
AUDIO IN leads to the input of the amplifier described in 1 and is
there mixed with the output of the sound chip.
GREEN is the analog green output of the video shifter.
RED. Red output.
GROUND.
o
oOo
NN
WN
HORIZONTAL SYNC is responsible for the horizontal beam
return of the monitor.
85

<!-- source-page: 93 -->
## Page 93

First Publishing
Atari ST Internal
Figure 2.2-1 Diagram of Video Interface
16MHz
+5V__»¢
7
-pcyce
-CMPCS
R/-W
—
>
$
SHIFT
|
Al-5
BZ
ct
——
>— 10
Do-15
AAAS
+—{
I}
——{_}
32MHz
>
14
+ ¥¥
-BLANK__
4-4
GPO
3
AUDIO
ovuT
1
HSYNC
9
VSYNC
12
4
5
1. aupro.—sX—IN
~MONOMON
86

<!-- source-page: 94 -->
## Page 94

first Publishing
Atari ST Internals
10 BLUE is the analog blue output of the video shifter.
11 MONOCHROME provides
a monochrome monitor with the
intensity signal.
12 VERTICAL SYNC takes care of the beam return at the end of the
screen.
13 GROUND.
A
tip for the hardware hobbyist:
A plug to fit this connector is not available. If you want to make a plug for
connecting other monitors, simply use a piece of perf board in which you
have soldered pins, since the pins are fortunately organized in a 1/10" array.
Pin 13 is out of order, but it is not needed since pin 8 is also available for
ground.
Figure 2.2-2 Monitor Connector
4
1
8
5
12
9
13
87

<!-- source-page: 95 -->
## Page 95

First Publishing
Atari ST Interna:
2.3 The Centronics Interface
A standard Centronics parallel printer can be connected to this interface
provided that you have the proper cable. As you can see in Figure 2.3-2, th
connection to the system is somewhat unusual. The data lines and the strobe
of the universal port of the sound chip are used. So you find these too o1
the picture, in which the other lines, which will not be described in the
section, will not disturb you. They belong to the disk drive and RS-237
interface and are handled there.
Here is the pin description:
1
-STROBE indicates the validity of the byte on the data lines
to the connected device by a low pulse.
2-9
DATA
11
BUSY is always placed high by the printer when it is not
able to receive additional data. This can have various causes.
|
Usually the buffer is full or the device is off line.
18-15
GROUND.
All other pins are unused.
A
tip for making a cable. Get flat-cable solderless connectors. You need
type D25-subminiature, a Cinch 36-pin (3M,AMP) and the appropriat
length of 25-conductor flat ribbon cable. You squeeze the connectors on th
cable so that pins
1 match up on both sides (they are connected together).
The other connections then match automatically. Note that there will
naturally be some pins free on the printer side.
|
Figure 2.3-1 Printer Port Pins
13
1
enueeeeeeee|.P
oe "/
ne
ee
ee
ee
ee
ee
25
14
88

<!-- source-page: 96 -->
## Page 96

‘irst Publishing
Atari ST Internals
Figure 2.3-2 Centronics Connection
R/-W
;
3
r
-swoes
4
|
;
6
Al
—_—
7
SOUND
8
2MHz
9
-RESET
1
11
| ps-15
&&
‘~—== TO/TA1
-—— cpo
H——  DRIVEO
H——— DRIVE1
SIDEO
r——— RTS
L—__ nTR
a
AUDIO
OUT
AUDIO
IN
89

<!-- source-page: 97 -->
## Page 97

First Publishing
Atari ST Internal
2.4 The RS-232 Interface
This interface usually serves for communication with other computers anc
modems. You can also connect a printer here. Note the description of pin 5!
Figure 2.4-1 shows the connection to the system. Normally you don't have
to do any special programming to use this interface. It is taken care of by the
operating system. Here the control of the interface is not controlled by 2
special IC (UART) as is usually the case, but the lines are serviced more o1
less "by hand." The shift register in the MFP is used for this purpose. The
handshake lines however come from a wide variety of sources. Note this in
the following pin description:
1
CHASSIS GROUND (shield)
This is seldom used.
2
TxD
Send data
3
RxD
Receive data
4
RTS
Ready to send comes from I/O port A bit 3 of the sound
chip and is always high when the computer is ready to
receive a byte. On the Atari, this signal is first placed low
after receiving a byte and is kept low until the byte has
been processed.
5
CTS
Clear to send of a connected device is read at interrupt
input 12 of the MFP. At the present time this signal is
handled improperly dy the operating system. Therefore it
is possible to connect only devices which "rattle" the line
after every received byte (like the 520ST with RTS). It
goes to input 12 of the MFP, but unfortunately is there
tested only for the signal edge. You will not have any luck
connecting a printer because they usually hold the CTS
signal high as long as the buffer is not full. There is no
signal edge after each byte, which means that only the
first byte of a text is transmitted, and then nothing.
90

<!-- source-page: 98 -->
## Page 98

irst Publishing
GND
Signal ground.
DCD
Carrier signal detected. This line, which goes to interrupt
input I1 of the MFP, is normally serviced by a modem,
which tells the computer that connection has been made
with the other party.
DTR
Device ready. This line signals to
a device that the
computer is turned on and the interface will be serviced as
required. It comes from V/O port A bit 4 of the sound
chip.
RI
Ring indicator is a rather important interrupt on I6 of the
MFP and is used by a modem to tell the computer that
another party wishes connection, that is, someone called.
91
Atari ST Internals

<!-- source-page: 99 -->
## Page 99

First Publishing
Atari ST Interna
Figure 2.4-1 RS-232 Connection
SO —>-
=
2
I/OA4 —|>
ork
20
1/0A3 —|>
RYS
4
SI «(+
RxD
3
16 ——«<}
RI
22
- xT
<TS
5
Il «<7
ded
8
1
13
ee
/
4
25
92

<!-- source-page: 100 -->
## Page 100

rst Publishing
Atari ST Internals
.5 The MIDI Connections
‘he term MIDI is probably unknown to many of you. It is an abbreviation
nd stands for Musical Instrument Digital Interface, an interface for musical
nstruments.
t is certainly clear that we can't simply hook up a flute to this port. So first
t little history. Music professionals (more precisely: keyboardists,
nusicians who play the synthesizer) demanded agreement between the
rarious manufacturers to interface computers to musical instruments. They
‘ound it absurd to connect complicated set-ups with masses of wire. The
dea was to service several synthesizers from one keyboard.
The tone created was basically analog (and still is, to a degree), so that the
manafacturers agreed that a control voltage difference of 1V corresponded to
a difference in tone of 1 octave. This way one could play several devices
under "remote control," but not service them.
This changed substantially when the change was made to digital tone
creation. Here one didn't have to turn a bunch of knobs, there were buttons
to press, whereby the basis for digital control was created.
Some manufacturers got together and designed a digital interface, the basic
commands of which would be the same throughout, but which would still
support the additional features of a given device.
The device is based on the teletype, the current-loop principle, which is not
very susceptible to noise, but significantly faster. The transfer rate is 31250
baud (bits per second). The data format is set at one start bit, eight data bits,
and one stop bit.
An IC can therefore be used for control which would otherwise be used for
RS-232 purposes. You see the connection to the system in figure 2.5-1.
Logically, MIDI is multi-channel system, meaning that 16 devices can be
serviced by one master, or a device with 16 voices. These devices are all
connected to the same line (bus principle). To identify which device or
which voice is intended,
each data packet is preceded by the channel
number. The device which recognizes this number as its own then executes
the desired action.
93

<!-- source-page: 101 -->
## Page 101

First Publishing
Atari ST Intern:
You may now ask what such an interface is doing in a computer. Qui
simple: A computer, because of its high speed and memory capacity, is ve1
well suited to providing an entire arsenal of synthesizers with settings ¢
complete melodies (sequencer) or to record and store such things from
keyboard.
For this purpose the ST has the interfaces MIDI-IN and MIDI-OUT. Th
interfaces are even supported by the XBIOS so you don't have to worr
about their actual operation.
The current loop travels on pins
4 and 5, out through pin 4 (+)
0
MIDI-OUT and in at 5, when a device is connected.
For MIDI-IN the situation is reversed because the current flows in througl
pin 4 and back out through pin 5. It goes though something called a1
optocoupler which electrically isolates the computer from the sender.
The receive data are looped back to MIDI-OUT (pins
1 and 3), whicl
implements the MIDI-THRU function, although not entirely according tc
the standard.
|
94

<!-- source-page: 102 -->
## Page 102

‘irst Publishing
Atari ST Internals
Figure 2.5-1 MIDI System Connection
.
4
E
>
5
6850S
——__——
a
Al
|
ACIA
R/-W
6850
rl
D8-15
E
——
5
500KHz
I4
eee)
0
O
4
5
O/3
2
95

<!-- source-page: 103 -->
## Page 103

First Publishing
Atari ST Internz
2.6 The Cartridge Slot
The cartridge slot can be used exclusively for inserting ROM cartridges. L
to 128K in the address space $FA0000 to $FBFFFE can be addressed. Ti
reason we stressed the exclusivity of the read access is the following. W
thought it would be practical to outfit a cartridge with RAM and then loz
programs into it after the system start which would still remain after a rese
In order to try this we brought the R/-W signal to the outside. Th
experience taught us, however, that a write access to these addresses create
a bus error. The GLUE takes care of this. As you see, nothing is left
t
chance in the Atari.
Figure 2.6-1 The Cartridge Slot
+5V
1
21
A8
+5V
2
22
Al4
D14
3
23
A7
d15
4
24
A
9
D12
5
25
Aé6
D13
6
26
Alo
bp10
7
27
a5
pil
8
28
Al2
Ds
9
29
All
D9
10
30
A4
D6
11
31
-~ROM3
D7
12
32
A
3
ba
13
33
-ROM4
D5
14
34
A2
D2
15
35
-UDSs
D3
16
36
Al
bo
17
37
-LpDs
D1
18
38
GND
Al13
19
39
GND
Al16
20
40
GND
Position:
Beene eeeeeeeeeeeee ee
20
21
BEeBeReHHEemRBeeeaemeaenmreeeaeeeeee,e
40
96

<!-- source-page: 104 -->
## Page 104

‘irst Publishing
Atari ST Internals
1.7 The Floppy Disk Interface
The interface for floppy disk drives is conspicuous because of the unusual
connector, a 14-pin DIN connector. All of the signals required for the
operation of two disk drives are available on it.
You know most of the signals from the description of the disk controller
1772, since nine of the available connections are directly or via a buffer
connected to the controller. Only the drive select 1 and drive select 2 signals
and the side 0 select are not derived from the disk controller. These signals
come from port A of the sound chip.
Pinout of the disk connector:
1
READ DATA
8 MOTOR
ON
2
SIDE
0
SELECT
9 DIRECTION
IN
3
GND
10
STEP
4
INDEX
11
WRITE
DATA
5
DRIVE
0
SELECT
12
WRITE
GATE
6 DRIVE
1
SELECT
13
TRACK
00
7
GND
14 WRITE PROTECT
97

<!-- source-page: 105 -->
## Page 105

First Publishing
Atari ST Interna
CDO-7
CA2
CAL
CR/-W
-FDCS
-RESET
8MHz
I/OA2
I/OA1
I/OAO
Figure 2.7-1 Disk Connection
ZA,
FDC
14
13
>—— 12
>—
11
> 10
nN
UW
OF
FF
FDRQ
INTR
98

<!-- source-page: 106 -->
## Page 106

‘irst Publishing
Atari ST Internals
1.8 The DMA Interface
Jp to 8 external devices can be connected to this 19-pin subminiature D
sonnector.
Such
devices
include
hard
disks, networks,
and
also
>oprocessors. The communication between the external devices and the ST
‘uns
at speeds up to
1 million bytes per second. Unfortunately, no
2xperiments with DMA devices could be performed at the time this was
printed. For this reason we cannot make the following statements with one
hundred percent certainty.
The RESET line on pin 12 permits devices to be reset by the Atari. If this
pin is low, as is the case when the Atari is turned on or when executing a
RESET command, external devices are placed in a defined power-up state,
without having to individually turn each device off and then on again.
Since most of the external devices will use a controller IC, the signal CS,
Chip Select on pin 9, must also be available. The signal A1 is also to be
seen in connection with this, because it is then important if the controller has
more than just one register. This signal can distinguish between two
registers.
The data transfer takes place over the bidirectional data bus on pins 1
to 8.
The R/W line on the DMA bus determines the direction of the data transfer.
The DMA chip can either write data to the bus (R/W is high), or read data
from the bus (R/W is low). Data can be read or written only on the request
of the external device. The release of a transfer is signaled by the signal
DRQ (pin 19).
The ACK signal on pin 14 appears to be a purely hardware-dependent
confirmation of the DRQ signal. The actual significance could not be
checked however.
The last signal on the DMA port is the INT input. A low on this connection
can generate an interrupt. The hard disk, for example, signals the end of the
command through a low. The interrupt uses the same interrupt input on the
MFP as the disk controller. This is input I/O 5. This means the at the floppy
disk drive and the hard disk cannot transfer data together. The DMA is also
not in such a position since it has only one DMA channel available.
The interrupt of this input is disabled in the MFP internally because the
floppy as well as the hard disk routines check the port bit in a loop in order
99

<!-- source-page: 107 -->
## Page 107

First Publishing
Atari ST Interna.
to determine the end of the command. This simplifies the implementation c
the time out, which is always generated when the floppy or hard disk ha
not reacted to the command within a certain length of time.
Figure 2.8-1 DMA Port
10
1
RBenmBREREeAasEeEeR
se
=memereenensen
19
11
Figure 2.8-2 DMA Connections
DO-15
LEE,
-FDCS
CA2
CR/-W
RDV
_——_
19
DMA
18
8MHz
16
Al
14
FDRQ
————~¥+|
9
|
8
1
-RESET
12
<(}L
10
ZN
-—
15
INTR
100

<!-- source-page: 108 -->
## Page 108

‘irst Publishing
Atari ST Internals
Chapter 3
(
The ST Operating System )
The GEMDOS
GEMDOS error codes and their meaning
The BIOS Functions
The XBIOS
The Graphics
An overview of the line-A variables
Examples for using the line-A opcodes
The Exception Vectors
The interrupt structure of the ST
The ST VT52 Emulator
The ST System Variables
The 68000 Instruction Set
Addressing modes
The instructions
The BIOS listing
s
bom
GR GR GG
Ga Gs a
ad GG
GG
oD ODOIANHEDRAWNEE
N=
jm
bo

<!-- source-page: 109 -->
## Page 109

First Publishing
Atari ST Interna
a

<!-- source-page: 110 -->
## Page 110

‘irst Publishing
Atari ST Internals
The ST Operating System
SEMDOS--what is it? Is it in the ST? The operating system is supposed to
oe TOS, though. Or CP/M 68K? Or what?
This question can be answered with few words. The operating system in the
ST is named TOS--Tramiel Operating System--after the head of Atari. This
TOS, in contrast to earlier information has nothing to do with CP/M 68K
from Digital Research. At the start of development of the ST, CP/M 68K
was implemented on it, but this was later changed because CP/M 68K is not
exactly a model of speed and efficiency. A 68000 running at 8MHz and
provided with DMA would be slowed considerably by the operating
system.
At the beginning of 1985, Digital Research began developing a new
operating system for 68000 computers, which would include a user-level
interface. This operating system was named GEMDOS. It is exactly this
GEMDOS which makes up the hardware-independent part of TOS. Like
‘CP/M, TOS consists of a hardware-dependent and a hardware-independent
part. The hardware-dependent part is the BIOS and the XBIOS, while the
hardware-independent part is called GEMDOS. A
large number of functions
are built into GEMDOS, through which the programmer can control the
actual input/output functions of the computer. Functions for keyboard input,
text output on the screen or printer, and the operation of the various other
interfaces are all present. Another quite important group contains the
functions for file handling and for logical file and disk management.
103

<!-- source-page: 111 -->
## Page 111

First Publishing
Atari ST Intern:
3.1 The GEMDOS
When you look at the functions available under GEMDOS, you wi
eventually come to the conclusion that the whole thing is not really new. A
the functions in GEMDOS are very similar to the functions of the MS-DO
operating system. Even the functions numbers used correspond to those ¢
MS-DOS. But not all MS-DOS functions are implemented in GEMDO‘
Especially in the area of file management, only the UNIX compatibl
functions are implemented in GEMDOS.
The "old" block-oriente
functions which are included in MS-DOS to maintain compatibility wit:
CP/M are missing from GEMDOS. Also, special functions relating to th
hardware of MS-DOS computers (8088 processor) are missing.
Another essential difference between MS-DOS and GEMDOS is that fo
GEMDOS calls as well as for the BIOS and XBIOS, the function number
the number of the desired GEMDOS routine, and the required parameter
are placed on the stack and are not passed in the registers. The 68000 i:
particularly suited to this type of parameters passing. GEMDOS is callec
with TRAP
#1
and the function is executed according to the contents of
the parameter list. After the call, the programmer must put the stack back ir
order himself, by clearing the parameters from memory.
The basic call of GEMDOS functions differs from the BIOS and XBIOS
calls only in the trap number.
In regard to all GEMDOS calls, it must be noted that registers DO and AC
are changed in all cases. If a value is returned, it is returned in DO, or DC
may contain an error number, and after the call AO (usually) points to the
stack address of the function number. Any parameters required in DO or AC
must be placed there before GEMDOS is called.
The remainder of this section describes the individual GEMDOS functions.
104

<!-- source-page: 112 -->
## Page 112

First Publishing
Atari ST Internals
$00 TERM
Calling GEMDOS with function number 0 ends the running program and
returns
to the program from which
it was started. For applications,
programs started from the desktop, program control is returned to the
desktop. If the program was called from a different program, execution is
passed back to the calling program. This point is important for chaining
program segments.
CLR.W
-(SP)
TRAP
| $01 CONIN
CONIN fetches a single character from the keyboard. The routine waits
until
a character is available. The result, the character read from the
keyboard, is returned in the DO register. The ASCII code of the pressed key
is returned in the low byte of the low word, while the low byte of the high
word of the register contains the scan code returned from the keyboard.
This is important when reading keys which have no ASCII code. This
applies to the 10 function keys or the keys of the cursor block, for example.
These keys return the ASCII value zero when pressed.
If needed, the scan code can be used to determine if the digits on the keypad
or the main keyboard were pressed, since these keys have identical ASCH
codes, but return different scan codes.
MOVE .W
#1,-(SP)
*
Function number
on
the
stack
TRAP
#1
*
Call GEMDOS
ADDQ.L
#2,SP
*
Correct
stack
105

<!-- source-page: 113 -->
## Page 113

First Publishing
Atari ST Internal
$02 CONOUT
CONOUT represents the simplest and most primitive character output o:
GEMDOS. With this function only one character is printed on the screen
The character to be displayed is placed on the stack as the first word. The
ASCII value of the character to be printed must be in the low byte of the
word and the high byte should be zero.
The character printed by CONOUT is outputted to device number 2, the
normal console output. Control characters and escape sequences are
interpreted normally.
MOVE.W #'A',-(SP)
* Output
an
A
MOVE .W #2,-(SP)
*
CONOUT
TRAP
#1
*
Call GEMDOS
ADDQ.L #4,SP
* Correct
stack
$03 AUXILLIARY INPUT
Under the designation "auxilliary port"
is the RS-232 interface of the ST.
A character can be read from the interface with the function CAUXIN. The
function returns when
a character has been completely received. The
character is returned in the lower eight bits of register DO.
$04 AUXILLIARY OUTPUT
Similar to the input of characters via the serial interface, a character can be
sent with this function. With this function the programmer should clear the
upper eight bits of the word and pass the character to be sent in the lower
eight bits.
106

<!-- source-page: 114 -->
## Page 114

First Publishing
Atari ST Internals
$05 PRINTER OUTPUT
PRINTER OUTPUT is the simplest method of operating a printer connected
to the Centronics interface. One character is printed with each call.
An important part of PRINTER OUTPUT is the return value in DO. If the
character was sent to the printer, the value -1 (SFFFFFFFF) is returned in
DO. If, after 30 seconds, the printer was unable to accept the character (not
turned on, OFF LINE, no paper, etc.), GEMDOS returns a time out to the
program. DO then contains a zero.
MOVE.W #'A',-(SP)
* Output
an
A
MOVE.W #5,-(SP)
* Function number
TRAP
#1
* Call GEMDOS,
output character
ADDQ.L #4,SP
* Correct
stack
| TSsT.W
DO
* Affect
flags
BEQ
printererror
$06 RAWCONIO
RAWCONIO is a somewhat unusual mixture of keyboard input and screen
output and receives a parameter on the stack.
With a function value of $FF the keyboard is tested. If a character is
present, the ASCII code and scan code are passed in DO as described for
CONIN. But if no key value is present, the value zero is passed as both the
ASCII code and the scan code in DO. The call to RAWCONIO with
parameter $FF is comparable to the BASIC INKEY$ function.
If a value other than $FF is passed to the function, the value is interpreted as
a character to be printed and it is output at the current cursor position. This
output also interprets the control characters and escape sequences properly.
107

<!-- source-page: 115 -->
## Page 115

First Publishing
Atari ST Internal
START:
MOVE .W
MOVE .W
TRAP
ADDQ.L
TST .W
BEQ
CMP .B
BEQ
MOVE
MOVE
TRAP
ADDQ.L
BRA
#SFF,-(SP)
#6,-(SP)
#1
#4,SP
DO
START
#3,D0
END
DO,-(SP)
#6,-(SP)
#1
#4,SP
START
+
+
ee
FF
OF
+
*
+
F
F
Function value test keyboard
Function number
Call GEMDOS,
test keyboard
Correct
stack
Character arrived?
Not
yet
“C selected
as
the
end marker
Character
for output
on the
stack
Function number
Call GEMDOS,
test keyboard
Correct
stack
Get
new character
$07 DIRECT CONIN WITHOUT ECHO
The function $07 differs from $01 only in that the character received fro
the keyboard is not displayed on the screen. It waits for a key just as does
CONIN.
$08 CONIN WITHOUT ECHO
Function $08 does not differ from function $07. Both function calls have
exactly the same effect. The reason for this seemingly nonsensical behavior
lies in the mentioned compatibility to MS-DOS. Under MS-DOS the two
functions are different in that with $08, certain keys not present on the
ATARI are evaluated correctly, while this evaluation does not take place
with function $07.
108

<!-- source-page: 116 -->
## Page 116

First Publishing
Atari ST Internals
$09 PRINT LINE
You have already become familiar with functions to output individual
characters on the screen with CONOUT and RAWCONIO. PRINT LINE
offers you an easy way to output text. An entire string can be printed at the
current cursor position with this function. To do this, the address of the
string is placed on the stack as a parameter. The string itself is concluded
with a zero byte. Escape sequences and control characters can also be
evaluated with this function,
After the call, DO contains the number of characters which were printed.
The length of the string is not limited.
MOVE.L
#text,-(SP)
* Address
of the string on the stack
' MOVE
#$09,-(SP)
* Function number PRT LINE
TRAP
#1
*
Call GEMDOS
ADDQ.L
#6,SP
*
"Clean up"
the stack
text
-DC.B
'This
is the string to be printed',$0D,$0A,0
$0A READLINE
READLINE is a very easy-to-use function for reading characters from the
keyboard. In contrast to the "simpler" character-oriented input functions, an
entire input line can be fetched from the keyboard with READLINE, The
characters entered are displayed on the screen at the same time.
The address of an input buffer is passed to the function as the parameter.
The value of the first byte of the input buffer determines the maximum
length of the input line and must be initialized before the call. At the end of
the routine, the second byte of the buffer contains the number of characters
entered. The characters themselves start with the third byte.
The routine used by READLINE for keyboard input is quite different from
the character-oriented console inputs. Escape sequences are not interpreted
during the output. Only control characters like control-H (backspace) and
control-f (TAB) are recognized and handled appropriately. The following
control characters are possible:
109

<!-- source-page: 117 -->
## Page 117

First Publishing
Atari ST Internal
“C
Ends
input
AND program
(!)
“H
Backspace one position
“TI
TAB
“J
 Linefeed,
end input
“M
CR,
end input
“R
Entered line
is printed
in new
line
“U
Don't
count
line,
start
new line
“X
Clear
line,
cursor
at
start
of
line
A function like H, deleting a character entered, is useful, but for large
programs you should write your own input routine because “C is very
"dangerous." Unlike CP/M, the program will be ended even if the cursor is
not at the very start of the input line.
If more characters are entered than were indicated in the first byte of the
buffer at the initialization, the input is automatically terminated. If the input
is terminated by ENTER, “J, or “M, the terminating character will not be
put in the buffer.
After the input, DO contains the number of characters entered, excluding.
ENTER, which can be found at buffer+1.
$0B CONSTAT
All key actions are first stored in a buffer in the operating system. This
storage is 64 bytes in length. The key values stored there are taken from the
buffer when a call toa GEMDOS output routine is made.
|
CONSTAT can be used to check if characters are stored in the keyboard
buffer. After the call, DO contains the value zero or $FFFF. A zero in DO
indicates that no characters are available.
$0OE SETDRV
The current drive can be determined with the function SETDRV. A 16-bit
parameter containing the drive specification is pased to the routine. Drive A
is addressed with the number 0 and drive B with the number 1.
After the call, DO contains the number of the drive active before the call.
110

<!-- source-page: 118 -->
## Page 118

First Publishing
Atari ST Internals
$10 CONOUT STAT
CONOUT STAT returns the status of the console in DO. If the value $FFFF
is returned, a character can be displayed on the screen. If the returned value
is zero, however, no character output is possible on the screen at that time.
Incidently, all attempts to create a not-ready status at the console failed. The
only imaginable possibility for the not-ready status would be if the output of
the individual bit pattern of a character was interrupted and the interrupt
routine itself tried to output a character. This case could not, however, be
created.
$11 PRTOUT STAT
This function returns the status, the condition of the Centronics interface. If
. No printer is connected (or turned off, or off line), DO contains the value
zero after the call to indicate "printer not available." If, however, the printer
is ready to receive, DO contains the value $FFFF.
$12 AUXIN STAT
By calling AUXIN STAT you can determine if a character is available from
the receiver of the serial interface ($FFFF) or not ($0000). As with all other
functions, the value is returned in DO.
$13 AUXOUT STAT
AUXOUT STAT gives information about the state of the serial bus.
A value
of $FFFF indicates that the serial interface can send a character, while zero
indicates that no characters can be sent at this time.
$19 CURRENT DISK
For many applications it is necessary to know which drive is currently
active. The current drive can be determined by the function $19. After the
call, DO contains the number of the drive. The significance of the drive
numbers is the same as for $0E, SET DRIVE (0=A, 1=B).
11]

<!-- source-page: 119 -->
## Page 119

First Publishing
Atari ST Internal:
$1A SET DISK TRANSFER ADDRESS
The disk transfer address is the address of a 44-byte buffer required for
various disk operations (especially directory operations). Along with the
GEMDOS functions SEARCH FIRST and SEARCH NEXT are examples
for using the DTA.
MOVE.L #DTADDRESS,-(SP)
* Address
of
the
44-byte DTA buffer
MOVE .W #$1A,-(SP)
* Function number
SET DTA
TRAP
#1
*
Set
DTA
ADDQ.L
#6,SP
* Clean
up the
stack
$20 SUPER
This function is especially interesting for programmers who want to access
the peripheral components or system variables available only in the
supervisor mode while running a program in the user mode. After calling
this function from the user mode, the 68000 is placed in the supervisor
mode. In contrast to the XBIOS routine for enabling the supervisor mode,
additional GEMDOS, BIOS, and XBIOS calls can be made after
a
successful SUPER call.
First we will look at the case in which the SUPER function is called from a
program in the user mode with a value of zero on the stack. In this case the
program finds itself in the supervisor mode after the call. The supervisor
stack pointer is set to the value of the user stack pointer and the original
value of the supervisor stack pointer is returned in DO. This value should be.
stored by the program in order to get back into the user mode later.
If a value other than zero is passed to the SUPER function the first time it is
called, this value is interpreted as the desired value of the supervisor stack
pointer. In this case as well, DO contains the original value of the supervisor
stack pointer, which the program should save.
Before a program ends, the user mode should be reenabled. This change of
operating modes requires the address acquired the first time the routine was
called in order to set the supervisor stack pointer back to its original value.
112

<!-- source-page: 120 -->
## Page 120

First Publishing
Atari ST Internals
The SUPER function differs from all other GEMDOS functions in one very
important respect. Under certain circumstances, this call can also change the
contents of Al and D1. If you store important values in these registers, you
must save the values somewhere before calling the SUPER function.
The
6800
is
in the user mode
User stack becomes supervisor stack
Call
SUPER
The supervisor mode
is
active
after the TRAP
DO
= old supervisor stack
Save value
CLR.L
-(SP)
MOVE.W #$20,-(SP)
TRAP
#1
ADD.L
$6,SP
MOVE.L DO, SAVE SSP
+
*
*
&
Fe
HF
F
Here processing can
be done
in the supervisor mode
MOVE.L _SAVE_SSP,-(SP)
* Old supervisor stack pointer
MOVE .W #$20,-(SP)
* Call SUPER
TRAP
#1
* Now
we
are back
in the user mode
ADD.L
#6,SP
$2A GET DATE
You have no doubt experimented with the status field at one time or another.
In addition to various other functions, the status field contains a clock with
clock time and date. It can be useful for some applications to have the data
available. The date can be easily determined by the GET DATE function.
This function call requires no parameters and makes the date available in the
low word of register DO. It is rather thoroughly encoded, though, so that
the result in DO must be prepared in order to get the correct date.
The day in the range
1 to 31 is coded in the lower five bits. Bits 5 to 8
contain the month in the value range
1 to 12, and the year is contained in
113

<!-- source-page: 121 -->
## Page 121

First Publishing
Atari ST Internal
bits 9 to 15. The value range in these "year bits" goes from 0 to 119. The
value of these bits must be added to the value 1980 in order to get the actua
year. The date 12/12/1992, for example, would result in $198C in DO. This
can be represented in binary as %0001100.1100.01100. The lengths of the
three fields are marked with periods.
$2B SET DATE
The clock time and date can also be set from application programs. This is
particularly interesting for programs which use the date and/or clock time.
An example of this would be invoice processing in which the current date is
inserted in the invoice. Such programs can then ask the user to enter the
date. This avoids the problems that occur if the user forgets to set the date
and clock time on the status field beforehand.
The date must be passed to the function SET DATE in the same format as it
is received from GET DATE, bits 0-4 = day, bits 5-8 = month, bits 9-15 =
year- 1980.
MOVE.W #3101101011001,-(SP)
Set date
to 10/25/1985
*
MOVE.W #$2A,-(SP)
* Function number
of
SET DATE
TRAP
#1
*
Set date
x
ADDQ.L
#6,SP
Repair stack
$2C GET TIME
The function GET TIME returns the current (read: set) time from the
GEMDOS clock. Similar to the date, the clock time is coded in a special
pattern in individual bits of the register DO after the call. The seconds are
represented in bits 0-4. But since only values from 0 to 31 can be
represented in 5 bits, the internal clock runs in two second increments. In
order to get the correct seconds-result the contents of these five bits must be
multiplied by two. The number of minutes is contained in bits 5 to 10, while
the remaining bits 11-15 give information about the hour (in 24-hour
format).
114

<!-- source-page: 122 -->
## Page 122

first Publishing
Atari ST Internals
$2D SET TIME
[t is also possible to set the clock time under GEMDOS. The function SET
TIME expects a 16-bit value (word) on the stack, in which the time is coded
in the same form as that in which GET TIME returns the clock time.
MOVE .W #%1000101010111101,~(SP)
* Clock time 17:21:58
MOVE .W #$2D,—-(SP)
* Function
#
of GET TIME
TRAP
#1
*
Set date
ADDQ.L #6,SP
* Repair stack
$2F GET DTA
The function $2F is the counterpart of function $1A, SET DTA. A
call to
this function returns the address of the current disk transfer buffer in DO.
An exact explanation of this buffer is found together with the functions
SEARCH FIRST and SEARCH NEXT.
$30 GET VERSION NUMBER
Calling this function returns in DO the version number of GEMDOS. In the
version of GEMDOS currently in release, this question is always answered
with $0D00, corresponding to version 13.00. Official Atari documentation
claims that a value of $0100 should be returned for this version, though
perhaps the value should indicate that the present GEMDOS version is the
$D = diskette version.
$31 KEEP PROCESS
This function is comparable to the GEMDOS function TERM $00. The
program is also ended after a call to this function. $31 does differ from $00
in several important points.
After processing TRAP
#1, like TERM, control is passed back to the
program which started the program just ended. In contrast to TERM, a
termination condition can be communicated to the caller. While TERM
115

<!-- source-page: 123 -->
## Page 123

First Publishing
Atari ST Interna
returns the termination value zero (no error), zero or one may be selected ¢
the termination value for $31. A value other than zero means that an errc
occurred during program processing.
Another essential point lies in the memory management of GEMDOS. Whe
a program is started, the entire available memory space is made available t
it. If the program is ended with TERM, the memory space is released an
made available to GEMDOS. The entire area of memory released is als
cleared, filled with zeros. The program actually physically disappears fron
the memory. With function $31, however, an area of memory can bi
protected at the start address of the program. This memory area is no
released when the program is ended and it is also not cleared. The progran
could be restarted without having to load it in again.
KEPP PROCESS is called with two parameters. The example program:
shows the parameter passing.
MOVE.W #0,~(SP)
MOVE.L #$1000,-(SP)
MOVE.W #$31,-(SP)
TRAP
#1
Error code
no error,
else
1
Protect
$1000 bytes
at program start
Function number,
end program
+
*
F
now
|
$36 GET DISK FREE SPACE
:
It can be very important for disk-oriented programs to determine the amoun
of free space on the diskette. Then you have the ability to request that th
user change disks at the appropriate time. "Disk full" messages or even da
loss can then be avoided.
Function $36 returns exactly this information. The number of the desir
disk drive and the address of a 16-byte buffer must be passed to th
function. If the value 0 is passed as the drive number, the information i
fetched from the active drive, a 1 takes the information from drive A, and
2 from drive B.
The information passed in the buffer is divided into four long words. The
first long word contains the number of free allocation units. Each file, even
if it is only eight bytes long, requires at least one such allocation unit.
116

<!-- source-page: 124 -->
## Page 124

‘irst Publishing
Atari ST Internals
The second long word gives information about the number of allocation
units present on the disk, regardless of whether they are already used or are
still free. For the "small," single-sided diskettes this value is $15C or 351,
while the double-sided disks have $2C7 = 711 allocation units. The third
long word contains the size of a disk sector in bytes. For the Atari this is
always 512 bytes ($200 bytes).
In the last word is the number physical sectors belonging to an allocation
unit. This is normally 2. Two sectors form one allocation unit.
The number of available bytes of disk space can easily be calculated from
this information.
MOVE .W #0,~(SP)
*
Information
from the active drive
‘MOVE.L #BUFFER,
~- (SP)
Address
of
the
l1é6-byte buffer
|
MOVE
#$36,~(SP)
Function number
+
+
TRAP
#1
ADDQ.L
#8,SP
* Clean
up
stack
-bss
BUFFER:
freal:
.ds.l
1
*
Free allocation units
total:
.ds.l
1
*
Total allocation units
bps:
.ds.l
1
* Bytes/physical sector
pspal:
.ds.l
1
*
Phys.
sectors/alloc.
unit
$39 MKDIR
A subdirectory can be created from the desktop with the menu option “NEW
FOLDER". Such a subdirectory can also be created from -n application
program with a call to $39.
In order to create a new folder, the function $39 is given the address of the
folder name, also called the pathname. This name may consist of 8
characters and a three-character extension. The same limitations apply to
pathnames as do to filenames. The pathname must be terminated with a zero
byte when calling MKDIR.
117

<!-- source-page: 125 -->
## Page 125

First Publishing
Atari ST Interna
After the
call, DO indicates whether the operation was performe
successfully. If DO contains a zero, the call was successful. Errors ar
indicated through a negative number in DO. At the end of this chapter yor
will find an overview of all of the error messages occurring on connectio1
with GEMDOS functions.
+
MOVE.L #pathname
Address
of
the pathname
MOVE
#$39,-(SP)
* Function number
TRAP
#1
ADDO.L
#6,SP
* Repair stack
TST.W
DO
* Error occurred?
BNE
error
* Apparently
pathname:
-de.b
'‘'private.dat',0
$3A RMDIR
A subdirectory created with MKDIR can be removed again with $3A. A
before, the pathname, terminated with a zero, is passed to RMDIR. Th
error messages also correspond to those for MKDIR, with zero for succes
or a negative value for errors. An important error message should b
mentioned at this point. It is the message -36 (SFFFFFFCA). This is th
error message you get when the subdirectory you are trying to remov
contains files.
Only empty subdirectories can be removed with RMDIR. In the event of th
described error message, one must first erase all of the files in the directo
with UNLINK
($41) and then call RMDIR again.
118

<!-- source-page: 126 -->
## Page 126

‘irst Publishing
Atari ST Internals
53B CHDIR
The system of subdirectories available under GEMDOS is exactly the same
‘orm available under UNIX. This system is now running on systems with
liskette drives, but its advantages become noticeable first when a large mass
storage device such as a hard disk with several megabytes of storage
capacity is connected to the system. After a while, most of the time would
probably be spent looking for files in the directory.
To
better organize
the data, subdirectories can
be placed within
subdirectories.
It can therefore become necessary to specify several
subdirectories until one has the directory in which the desired file is stored.
An example might be:
/hugos.dat/cfiles.s/csorts.s/cqsort.s
Translated this would mean: load the file cqsort .s from the subdirectory
csorts.s. This subdirectory
csorts.s
is found in the subdirectory
cfiles.s, which in turn is a subdirectory of hugos .dat. If the whole
expression is given as a filename, the desired file will actually be loaded
(assuming that the file and all of the subdirectories are present). If you want
to access another file via the same path (do you understand the term
pathname’), the entire path must be entered again. But you can also make
the subdirectory specified in the path into the current directory, by calling
CHDIR with the specification of the desired path. After this, all of the files
in the selected subdirectory can be accessed just by the filenames. The path
is set by the function.
MOVE.L #path,-(SP)
* Address
of
the path
MOVE.W #$3B,-(SP)
* Function number
TRAP
#1
ADDQ.L
#6,SP
* Repair
stack
TST.W
DO
* Error occurred?
BNE
error
* Apparently
path:
-de.b
'/huges.dat/private.dat/',0
119

<!-- source-page: 127 -->
## Page 127

First Publishing
Atari ST Intern:
$3C CREATE
In all operating systems, the files are accessed through the sequence
opening the file, accessing the data, (reading or writing), and then closir
the file. This "trinity" also exists under GEMDOS, although there is a
exception. Under CP/M, for example,
a non-existing file can also
b
opened. When a
file which does not exist is opened, it is created. Unde
GEMDOS, the file must first be created. The call $3C, CREATE, is use
for this purpose. Two parameters are passed to this GEMDOS function: th
address of the desired filename, and an attribute word.
If a zero is passed as the attribute word, a normal file is created, a file whic
can be written to as well as read from. If the value
1
is passed as th
attribute, the file will only be able to be read after it is closed. This is a typ
of software write-protect (which naturally cannot prevent the file fron
disappearing if the disk is formatted).
Other possible attributes are $02, $04, and $08. Attribute $02 creates
;
"hidden" file and attribute $02 a "hidden" system file. Attribute $08 create:
a file with a “volume label." The volume label is the (optional) name whicl
a disk can be given when it is formatted. The disk name is then created fron
the maximum of 11 characters in the name and the extension. Files with one
of the last three attributes are excluded from the normal directory search. Or
the ST, however, they do appear in the directory.
When the function CREATE is ended, a
file descriptor, also called a
file
handle, is returned in DO. All additional accesses to the file take place ove:
this file handle (a numerical value bewteen 6 and 45). The handle must be
given when reading, writing, or closing files. A total of $28 = 40 files car
be opened at the same time.
If CREATE is called and a file with this name already exists, it is cut off a
zero length. This is equivalent to the sequence delete the old file and create :
new file with the same name, but it goes much faster.
If after calling CREATE you get a handle number back in D0, the file neec
not be opened again with $3D OPEN.
120

<!-- source-page: 128 -->
## Page 128

‘irst Publishing
Atari ST Internals
AOVE.W #$0,-(SP)
* File should have R/W status
4OVE.L #filename,-(SP)
* Address
of
the filename
on stack
MOVE .W #$3C,-(SP)
* Function number
TRAP
#1
*
Call GEMDOS
ADDQ.L #8,SP
* Clean
up stack
Ist
DO
* Error occurred?
BMI
error
*
It appears
so
MOVE
DO,handle
*
Save
file handle
filename:
* Don't
forget
zero byte
.de.b
'myfile.dat',0
handle:
.ds.w
il
$3D OPEN
You can create only new files with CREATE, or shorten existing files to
length zero. But you must be able to process existing files further as well.
To do this, such files must be opened with the OPEN function.
The first parameter of the OPEN function is the mode word. With a zero in
the mode word, the opened file can only be read, with one it can only be
written. With a value of 2, the file can be read as well as written. The
filename, terminated with zero byte in the usual manner, is passed as the
second parameter.
The OPEN function returns the handle number in D0 as the result if the file
is present and the desired access mode is possible. Otherwise DO contains
an error number. See the end of the chapter for a list of the error numbers.
121

<!-- source-page: 129 -->
## Page 129

First Publishing
Atari ST Interna
MOVE.W #$2,-(SP)
* Pile
read and write
MOVE.L #filename
* Address
of
the filename
on
the
stac
MOVE.W #$3D,-(SP)
* Function number
TRAP
#1
*
Call GEMDOS
ADDQ.L
#8,SP
* Clean
up the stack
TST.W
DO
* Error occurred?
BMI
error
* Apparently
*
MOVE
D0,handle
Save
file handle
for later accesses
filename:
* Don't
forget
zero byte!
-de.b
'myfile.dat',0
handle:
-ds.w
1
$3E CLOSE
Every opened file should be closed when it will no longer be accesse
within a program, or when the program itself is ended. Especially whe
writing, files must absolutely be closed before the program ends or dat
may be lost.
Files are closed by a call to CLOSE, to which the handle number is passe
as a parameter. The return value will be zero if the file was closed correctly.
MOVE.W handle,
- (SP)
* Handle number
MOVE .W #$3E,-(SP)
* Function number
TRAP
#1
*
Call
GEMDOS
ADDQ.L #4,SP
* Error occurred?
BMI
error
* Apparently
handle:
.ds.w
1
122

<!-- source-page: 130 -->
## Page 130

rst Publishing
Atari ST Internals
3F READ
ipening and closing files is naturally only half of the matter. Data must be
cored and the retrieved later. Reading such files can be done in a very
legant manner with the function READ. READ expects three parameters:
rst the address of a buffer in which the data is to be read, then the number
f bytes to be read from the file, and finally the handle number of the file.
‘his number you have (hopefully) saved from the previous OPEN.
Ve mentioned the possible handle numbers in conjunction with CREATE.
Vhat we didn't mention, however, is why the first handle number is six.
‘he cause of this is that things called devices, like the keyboard, the screen,
ne printer, and the serial interface, are also accessed via handle numbers for
EAD and WRITE operations. The device assignments are:
Console
input
Console output
RS-232
Printer
WNRrO
fo
od
Numbers 4 and 5 also function as console input and output. When using
hese handle numbers, the system sometimes returns "invalid handle
1umber". The correct programming and the exact purpose of these two
1umbers is not known.
As return value, DO contains either an error number (hopefully not) or the
1umber of bytes read without error. No message regarding the end of the
‘ile is returned. This is not necessary, however, since the size of the file is
-ontained in the directory entry (see SEARCH FIRST/SEARCH NEXT). If
he file is read past the logical end, no message is given. The reading will be
nterrupted at the end of the last occupied allocation unit of the file. The
number of bytes read in this case is always divisible by $400.
123

<!-- source-page: 131 -->
## Page 131

First Publishing
Atari ST Interna
MOVE.L #buffer,-(SP)
* Address
of the data buffer
MOVE.L #$100,~(SP)
* Read 256 bytes
MOVE .W handle,-(SP)
*
Space
for the handle number
MOVE.W #S$3F,-(SP)
* Function number
TRAP
#1
ADD.L
#12,SP
TST.L
DO
* Did
an error occur
BMI
error
* Apparently
handle:
-ds.w
1
*
Space
for the handle number
buffer:
-ds.b
$100
*
Suffices
in our example
$40 WRITE
Writing to a file is just as simple as reading from it. The parameters requir
are also the same as those required for reading. The file descriptors fro
OPEN and CREATE calls can be used as the handle, but the devic
numbers listed for READ can also be used. The output of a program can
sent to the screen, the printer, or in a file just by changing the handl
number.
$41 UNLINK
Files which are no longer needed can be deleted with UNLINK. To do thi
the address of the filename or, if necessary, the complete pathname must b
passed to the function. If the DO register contains a zero after the call, th
file has been deleted. Otherwise DO will contain an error number.
124

<!-- source-page: 132 -->
## Page 132

‘irst Publishing
Atari ST Internals
{(OVE.L pathname,-(SP)
* Address
of
the data buffer
1OVE.W #$41,-(SP)
* Function number
*RAP
#1
D.L
#6,SP
(ST.W
DO
* Did
an error occur?
3MI
error
* Apparently
pathname:
-dce.b
'/rolli/private/pacman.prg’,0
$42 LSEEK
Up to now we have become acquainted only with sequential data accesses.
We can read through any file from the beginning until we come the desired
information. An internal file pointer which points to the next byte to be read
goes along with each read. We can only move this pointer continusouly in
the direction of the end of file by reading. A few bytes forward or
backward, setting the pointer as desired, is not something we can do. This
is required for many applications, however.
LSEEK offers an extraordinarily easy-to-use method of setting the file
pointer to any desired byte within the file and to read or write at this
point. This UNIX-compatible option of GEMDOS is much easier to use that
the methods available under CP/M for relative file management, for
instance.
A total of three parameters are passed to the LSEEK function. The first
parameter specifies the number of bytes by which the pointer should be
moved. An additional parameter is the handle number of the file. The last
parameter is a mode word which describes how the file is to be moved. A
zero as the mode moves the pointer to the start of the file and from there the
given number of bytes toward the end of the file. Only positive values may
be used as the number. With a mode value of 1, the pointer is moved the
desired positive or negative amount from the current position, and a 2 as the
mode value means the distance specified is from the end of the file. Only
negative values are allowed in this mode.
125

<!-- source-page: 133 -->
## Page 133

First Publishing
Atari ST Intern:
After the call, DO contains the absolute position of the pointer from the st:
of the file, or an error message.
MOVE .W #1,-(SP)
* Relative
from the current
file ptr
MOVE.W handle,-(SP)
*
File handle
MOVE.L #$-20,-(SP)
*
32 bytes back
MOVE .W #$42,-(SP)
* Function number
TRAP
#1
ADD.L
#10,SP
TST.W
DO
*
Did
an error occur?
BMI
error
* Apparently
handle:
-ds.w
il
*
Space
for the handle number
$43 CHANGE MODE (CHMOD)
With the CREATE function a file can be assigned a specific attribute. Thi:
attribute can be determined and subsequently changed only with the functio:
CHANGE MODE. The name of the file must be known because the addres:
of the name or the complete pathname must be passed to CHMOD. Anothe
parameter word specifies whether the file attribute is to be read or se
Moreover, a word must be passed which contains the new attribute. Whe
reading the attribute of a file this word is not necessary, but should b
passed to the routine as
a dummy value. We indicated the possible fil
attributes in our discussion of the function CREATE, but here they are agai
in a table:
$00
= normal
file
status,
read/write possible
$01
= File
is READ ONLY
$02
=
"hidden"
file
$04
= system
file
$08
=
file
is
a volume
label,
contains
disk
name
$10
=
file
is
a subdirectory
$20
=
file
is
written
and closed correctly
Attributes $10 and $20 cannot be specified when the file is created. Attribut
$20 is granted by the operating system, while the GEMDOS functior
126

<!-- source-page: 134 -->
## Page 134

‘irst Publishing
Atari ST Internals
VMKDIR is used to create a subdirectory. The MKDIR function creates not
ynly the directory entry with the appropriate attribute, it also arranges the
subdirectory on the disk physically.
After the call, DO will contain the current attribute value, which will be the
new value after setting the attribute, or, as with all other function calls, a
negative error number.
First example:
MOVE .W #1,-(SP)
*
Give
file READ ONLY attribute
MOVE.W #1,-({SP)
*
Set attribute
MOVE.L #pathname,~-(SP)
*
We also need the pathname
MOVE.W #$43,~(SP)
* Function number
TRAP
#1
ADD.L
#10,SP
TST.W
DO
*
Did
an error occur?
BMI
error
* Apparently
pathname:
* Don't
forget
zero byte
at
end!
|
.de.b
'killme.not',0
Second example:
MOVE .W #0,-(SP)
* Dummy value,
not actually required
MOVE.W #0,-(SP)
* Read attribute
MOVE.L #pathname,-(SP)
*
and the pathname
MOVE.W #$43,-(SP)
* Function number
TRAP
#1
ADD.L
#10,SP
TST.W
DO
*
Did
an error occur?
BMI
error
* Apparently
pathname:
* Don't
forget
zero byte
at
the
end!
-dc.b
'what-am.i',0O
127

<!-- source-page: 135 -->
## Page 135

First Publishing
Atari ST Intern:
$45 DUP
AS mentioned in connection with the functions READ and WRITE, tk
devices console, line printer, and RS-232
are also available
to
th
programmer. This permits input and output to be redirected to these device
One of the devices can be assigned a file handle number with the DU
function. After the call the next free handle number is returned.
$46 FORCE
The FORCE function allows further manipulation of the handle numbers. I
mM a program the console input and output are used exclusively via thi
READ and WRITE functions with the handle numbers 0 and 1, the input o
Output can be redirected with a call to this function. Screen outputs are
written to a file, inputs are not taken from the keyboard, but from
;
previously-opened file.
$47 GETDIR
A given subdirectory can be made into the current directory with the
function $37. All file accesses with a pathname then run only in the set
subdirectory. Under certain presumptions it can be possible to determine the
pathname to the current subdirectory. This is accomplished by the function
call GETDIR, $47. This call requires the designation of the desired disk
drive (O=current drive, 1=drive A, 2=drive B, etc.) and a pointer to
a
64-byte buffer. The complete pathname to the current directory will be
placed in this buffer. The pathname will be terminated by a zero byte. If the
function is called when the main directory is active, no pathname will be
returned. In this case, the first byte in the buffer will contain zero. After the
call, DO must contain the value zero. If the value is negative, an error
occurred, for example if an incorrect drive number was passed.
|
128

<!-- source-page: 136 -->
## Page 136

‘irst Publishing
Atari ST Internals
MOVE .W #0,~(SP)
*
Get pathname
of the current drive
MOVE.L #buffer,~(SP)
* Address
of
the
64-byte buffer
MOVE .W #$47,-(SP)
* Function number
TRAP
#21
ADDQ.L
#8,SP
TST.L
DO
* Error?
BNE
error
* DO<>0
if error
buffer:
.as.b
64
*
Buffer
for pathname
$48 MALLOC
The MALLOC function and
the two that follow
it, MFREE and
SETBLOCK, are concerned with the memory organization of GEMDOS.
As already mentioned in conjunction with function $31, KEEP PROCESS,
a program is assigned all of the entire memory space available after it is
loaded. This is uncritical in many cases, because only a single program is
running. But there are applications under GEMDOS
in which such
organization is not sensible. An accessory such as the VT-52 emulator may
be called from within a program, for example. Such a program also requires
memory space, but the memory might not be available. No further program
modules can be loaded if the entire memory is occupied. For this reason,
each program should reserve only the space which it actually needs for the
program and data. The memory not required can be given back to
GEMDOS.
If the program should need some of the memory it gave back, it can request
memory from GEMDOS via the function MALLOC (memory allocate). The
number of bytes required is passed to MALLOC. After the call, DO contains
the starting address of the memory area reserved by the call or an error
message if an attempt is made to reserve more memory than is actually
available.
If -1L is passed as the number of bytes to be allocated, the number of bytes
available is returned in DO.
129

<!-- source-page: 137 -->
## Page 137

First Publishing
Atari ST Interna
First example:
MOVE.L #-1,-(SP)
MOVE .W #$48,-(SP)
TRAP
#1
ADDQ.L #6,SP
Second example:
MOVE.L #$1000,-(SP)
MOVE .W #$48,~(SP)
TRAP
#1
ADDQ.L
#6,SP
TST.W
DO
BMI
error
MOVE.L DO,mstart
mstart:
.das.1
1
Determine number
of
free bytes
Function number
Number
of
free bytes
in
DO
Get
hex
1000 bytes
for the program
* Function number
Error
or address
of memory?
Negative
long word
= error!
Else
start
addr
of the reserved area
$49 MFREE
An area of memory reserved with MALLOC can be released at any time
with MFREE. To do this, GEMDOS is passed the address of the memory
to be released. The value will usually be the address returned by MALLOC.
If a value of zero is returned in DO, the memory was released by GEMDOS
without error. A negative values indicates errors.
130

<!-- source-page: 138 -->
## Page 138

First Publishing
Atari ST Internals
MOVE.L mstart,~(SP)
* Addr of
a previously allocated area
MOVE .W #$49,-(SP)
* Function number
TRAP
#1
ADDQ.L #6,SP
* Number
of
free bytes
in DO
TST.L
bDO
* Error?
BNE
error
* DO<>0
is error!
mstart:
-ds.l
ol
'$4A SETBLOCK
In contrast to the MALLOC function, a specific area of memory can be
reserved with the function SETBLOCK. The memory beginning at the
specified address is returned to GEMDOS, even if it was reserved before.
This function can be used to reserve the actual memory requirements of a
program and release the remaining memory.
The parameters the function requires are the starting address and the length
of the area to be reserved. The area specified with these parameters is then
reserved by GEMDOS and is not released again until the end of the program
or after calling the MFREE function.
Usually programs will begin with the following command sequence or
something similar. After the call, DO must contain zero, otherwise an error
occurred.
131

<!-- source-page: 139 -->
## Page 139

First Publishing
Atari ST Internal:
MOVE.L A7,A5
*
Save stack pointer
in
A5
MOVE.L #USTCK,A7
*
Set
up stack
for the program
MOVE.L 4(A5),A5
*
A5
now points
to
the base-page start
* exactly $100 bytes below the prg start
MOVE.L $C(A5),D0
*
$C(A5)
contains
length
of
the prg area
ADD.L
$14(A5),D0
*
$14(A5)
containg the
length
of the
* initialized data
area
ADD.L
$1C(A5),D0
*
$1C(A5)
contains
length
of the
* uninitialized data
area
ADD.L
#$100,D0
* Reserve
$100 bytes base page
MOVE.L DO,-(SP)
*
DO contains
the length
of the area
*
to
be reserved
MOVE.L A5,-(SP)
*
AS contains
the
start
of
the area
*
to
be reserved
MOVE .W #0,-(SP)
* Meaningless word,
but
still necessary!
MOVE.W #S$4A,-(SP)
* Function number
TRAP
#1
ADD.L
#12,SP
* Clean
up the stack
as usual
TST.L
DO
*
Did an error occur?
BNE
error
*
Stop
*
Here
the program continues...
$4B EXEC
The EXEC function permits loading and chaining programs. If desired, the
program loaded can be automatically started. In addition to the function
number, the addresses of three strings and a mode word are expected on the
stack.
The first address is a pointer to something called an "environment" string, a
string which describes the "environment." If the environment is not set, the
address of a null string, the address of a zero byte, will suffice.
The second pointer contains
a command line for the program being called. A
command line is comparable to the line which may be entered from the
command mode when you have selected the point "TOS -takes parameters”
from the option "Options".
132

<!-- source-page: 140 -->
## Page 140

First Publishing
Atari ST Internals
The third pointer points to the filename or pathname of the file. All three
strings must be terminated with a zero byte or consist of only a zero byte.
The mode word can be either zero or three. The standard value zero starts
the loaded program automatically, while a three loads the program without
automatically executing it. In this last case, either the address of the base
page or an error message is returned in DO.
MOVE.L #env,-(SP)
* Environment
MOVE.L #com,-(SP)
* Command line
MOVE.L
#f£11,-(SP)
* Filename
MOVE .W #0,-(SP)
*
Load and start,
please
MOVE .W #$4B,-(SP)
* Function number
TRAP
#1
ADD.L
#14,SP
*
Here
we
come
to the end
of
the
* chained program or postloaded module
fil:
*
Load sort
routine
-dc.b
‘'qsort.prg',0
com:
*
Sort
the
file
in ascending order
-dce.b
‘up data.asc',0
env:
*
No environment
-de.b
0
$4C TERM
TERM $4C represents the third method, after TERM $00 and TERM $31,
of ending a program. TERM $4C automatically makes the memory used by
the program available to GEMDOS again. Different from TERM $00,
however, a programmer-defined return value other than zero can be returned
to the caller. This allows a short message to be passed back to the calling
program.
133

<!-- source-page: 141 -->
## Page 141

First Publishing
Atari ST Internal
MOVE.W #37,-(SP)
*
Any 2-byte value
MOVE.W #S$4C,-(SP)
*
End program
TRAP
#1
*
now
*
We never get
here
$ 4E SFIRST
The SFIRST function can be used to check to see if a file with the given
name is present in the directory. If a file with the same name is found, the
filename, the file attribute, data and time of creation, and the size of the file
in bytes is returned. This information is placed in the DTA buffer, whose
address is set with the SETDTA function, by GEMDOS.
One feature of this function is that the filename need not be specified in its
entirety. Individual characters in the filename can be exchanged for a
question mark "?", but entire groups of letters can also be replaced by a"*".
In the extreme form a filename would be reduced to the string "*.*". In this
case the first file in the directory would satisfy the conditions and the
filename would appear in the DTA buffer along with the other information.
In addition to the filename, the SFIRST function must also be given a
search attribute. The possible parameters of the search attribute correspond
to the attributes which can be specified in CHMOD function:
$00
= Normal
access,
read/write possible
$01
= Normal
access,
write protected
$02
= Hidden entry
(ignored by the
ST desktop)
$04
= Hidden
system file
(ignored
like
$02)
$08
= Volume
label,
diskette name
$10
= Subdirectory
$20
= File will
be written and closed
The following rules apply when searching for files:
If the attribute word is zero, only normal files are recognized.
System files or subdirectories are not recognized.
System files, hidden files, and subdirectories are found when
the corresponding attribute bits are set. Volume labels are not
recognized, however.
134

<!-- source-page: 142 -->
## Page 142

First Publishing
Atari ST Internals
In order to get the volume label, this option must be expressly
set in the attribute word. All other files are then ignored.
After the call, DO contains the value zero if a corresponding file
has been found.
In this case the 44-byte DTA buffer is
constructed as follows:
Bytes
0-20
Reserved for GEMDOS
Byte
21
File attribute
Bytes
22-23
Clock time
of
file creation
Bytes
24-25
Date
of file creation
Bytes
26-29
File
size
in bytes
(long)
Bytes
30-43
Name
and extension
of the
file
If, however, no file is found which corresponds to the specified search
string, the error message -33, file not found, is returned.
MOVE.L #dta,-(SP)
*
Set
up DTA buffer
MOVE.W #1A,-(SP)
* Function number SETDTA
TRAP
#1
ADDQ.L
#6,SP
MOVE.W #attrib,~-(SP)
* Attribute value
MOVE.L #filnam,-— (SP)
* Name
of
file
to search
for
MOVE.W #$4E,-(SP)
* Function number
TRAP
#1
ADDQ.L
#8,SP
TST
DO
* File found?
BNE
notfound
* Apparently not
attrib:
-dc.b
0
*
Search
for normal
files
only
filnam:
-de.b
'*.*',Q
* Search for the
lst possible
file
data:
.ds.b
44
*
Space
for the DTA buffer
135

<!-- source-page: 143 -->
## Page 143

First Publishing
Atari ST Internal
$4F SNEXT
The SNEXT function (Search next) can be used to see if there are other file;
on the disk which match the filename given. To do this, only the functior
number need be passed; SNEXT does not require any parameters. All of the
parameters are set from the SFIRST call.
If the search string is very global, as in the previous example, all of the files
on a diskette can be determined and displayed one after the other with
SFIRST and SNEXT. This makes it rather easy to display a directory
within a program. The SNEXT function is called repeatedly and the
contents of DO are check afterwards. If DO contains a value other than zero,
either an error occurred, or all of the directory entries have been searched.
$56 RENAME
A RENAME function is found in almost every disk-oriented operating
system in one form or another, since renaming files is required fairly often .
|
Under GEMDOS, files are renamed with the RENAME function, which
requires two pointer to file or pathnames. The first pointer points to the new
name, with the specification of the pathname of the file if necessary, and
the second pointer points to the previous name. A 2-byte parameter is
required in addition to the two pointers. We were not able to determine the
significance of the additional word parameter. Different values had no
(recognizable) effect.
|
As a return value, DO contains either zero, meaning that the name was
changed correctly, or an error code.
|
136

<!-- source-page: 144 -->
## Page 144

First Publishing
Atari ST Internals
MOVE.L #newnam,
— (SP)
* New filename
MOVE.L #oldname,-(SP)
* File
to
rename
MOVE.W #0,~(SP)
* Dummy?
MOVE.W #$56,-(SP)
* Function number
TRAP
#1
ADD.L
#12,SP
TST.L
bO
*
Test
for error
oldnam:
* Don't
forget
zero byte
at
end!
.de.b
‘oldfile.dat',0
newnam:
-de.b
'newname.dat',0
$57 GSDTOF
If the directory is displayed as text rather than icons on the desktop, the date
and time of file creation as well as the size of the file in bytes is shown. The
time and date can either be set or read with function $57. To do this it is
necessary that the file be already opened with OPEN or CREATE. The
handle number obtained at the opening must be passed to the function.
Additional parameters are a word which acts as a flag as to whether the time
and data are to be set (0) or read (1), and a pointer to a 4-byte buffer which
either contains the result data or will be provided with the required data
before the call.
This date buffer contains the time in the first two byes and the date in the
last two. The format of the data is identical to that of the functions for
setting/reading the time and date.
137

<!-- source-page: 145 -->
## Page 145

First Publishing
Atari ST Internal:
Example 1:
MOVE
MOVE
MOVE
MOVE
TRAP
-W #1,-(SP)
-W #handle,-(SP)
-L #buff,-(SP)
-W #857,-(SP)
#1
ADD.L
#10,SP
handle:
-ds.b
2
buff:
-ds.b
4
Example 2:
MOVE .W
#0,-(SP)
MOVE.W #handle,-(SP)
MOVE.L #buff,-(SP)
MOVE.W #$57,-(SP)
TRAP
#1
ADD.L
#10,SP
handle:
buff
-ds.b
2
.
.
-ds.b
4
* Read time and date
*
*
*
+
FF
Fe
File must
first
be opened
4 byte buffer
Function number
Set
time
and date
File must
first
be opened
4 byte buffer
Function number
138

<!-- source-page: 146 -->
## Page 146

First Publishing
Atari ST Internals
3.1.1 GEMDOS error codes and their meaning
The GEMDOS functions return a value giving information about whether or
not an error occurred during the execution of the function. A value of zero
means no error; negative values have the following meanings:
-32
-33
-34
-35
-36
-37
-39
-40
-46
-49
3.3
Invalid function number
File
not
found
Pathname
not
found
Too many
files
open
(no more handles
left)
Access
not possible
Invalid handle number
Not
enough memory
Invalid memory block address
Invalid drive
specification
No more
files
In addition to these error messages, the BIOS error messages may occur.
These error messages have numbers -1 to -31 and are described in section
139

<!-- source-page: 147 -->
## Page 147

First Publishing
Atari ST Internal
3.2 The BIOS Functions
The software interface between the GEMDOS and the hardware of the
computer is the BIOS (Basic Input Output System). The BIOS, as the nam
suggests, is concerned with the fundamental input/output functions. Thi:
includes screen output, keyboard input, printer output, as well as the
RS-232 interface and, of course, input/output to the disk.
The BIOS functions are also available to user programs. The TRAP
instruction of the 68000 processor is used to call them. Any data required is
passed through the stack and the result of the function is returned in the DC
register. The machine language programmer should be aware that the
contents of DO-D2 and AO-A2 are changed when calling BIOS functions;
the remaining registers remain unchanged.
BIOS function calls are even simpler if you program in C. Here you can use
simple function calls with the corresponding parameter lists. The function
calls are stored as macros in an include file. In the examples, the definition
of the function and its parameters in C will be shown. For assembly
language programmers, the use is described in an example.
TRAP
#13
is reserved for the BIOS functions.
140

<!-- source-page: 148 -->
## Page 148

First Publishing
Atari ST Internals
0 getmpb
get memory parameter block
C:
void getmpb (pointer)
long pointer;
Assembler:
move.l
pointer,~(SP)
move.w
#0,-(SP)
trap
#13
addq.1
#6,sp
This function fills a 12-byte block whose address is contained in pointer
| with the memory parameter block. This block contains three pointers itself:
long
mfl
Memory free list
long
mal
Memory allocated list
long
rover
Roving pointer
The structures to which each pointer points are constructed as follows:
long
link
Pointer
to next block
long
start
Start
address
of
the block
long
length
Length
of the block
in bytes
long
own
Process descriptor
Example:
move.l #buffer,-(sp)
Buffer
for MPB
move.w #0,-(sp)
getmpb
trap
#13
Call BIOS
addq.1
#6,sp
Stack correction
Wh get the values $48E, 0, and $48E. The following data are at address
A48E:
link
0
No additional block
start
$3B900
Start
address
of
the
free memory
length
$3C700
Length
of
the
free memory
own
0
No process descriptor
141

<!-- source-page: 149 -->
## Page 149

First Publishing
Atari ST Internal
1 bconstat
return input device status
C:
int bconstat (dev)
int
dev;
Assembler:
move.w dev,-(sp)
move.w #1,-(sp)
trap
#13
addq.1
#4,sp
This function returns the status of an input device which is defined as
follows:
Status
0
No characters
ready
Status
-1
(at
least)
one character ready
The parameter dev specifies the input device:
dev
Input device
0
PRT:,
Centronics
interface
1
AUX:,
RS~232
interface
2
CON:,
Keyboard and screen
3
MIDI,
MIDI
interface
4
IKBD,
Keyboard port
The following table lists the allowed accesses to these devices:
Operation
PRT:
AUX:
CON:
Input
status
no
yes
yes
Input
yes
yes
yes
Output
status
yes
yes
yes
Output
yes
yes
yes
MIDI
yes
yes
yes
yes
IKBD
no
yes
yes
yes
This example waits until a character from the RS-232 interface is ready.
wait move.w
#1,-(sp)
RS-232
move.w #1,-(sp)
beonstat
trap
#13
addq.1
#4,sp
tst
do
character available?
beq
wait
no,
wait
142

<!-- source-page: 150 -->
## Page 150

First Publishing
Atari ST Internals
2 conin
read character from device
C:
long conin (dev)
int
dev;
Assembler:
move.w dev,- (sp)
move.w #2,-(sp)
trap
#13
addq.1
#4,sp
| This function fetches a character from an input device. The parameter dev
| has the same meaning as in the previous function. The function does not
return until a character is ready.
The character received is in the lowest byte of the result. If the input device
was the keyboard (con, 2), the key scan code is also returned in the lower
byte of the upper word (see description of the keyboard processor).
Example:
move.w
#2,-(sp)
con
move.w
#2,-(sp)
beonin
trap
#13
addq.1
#4,sp
143

<!-- source-page: 151 -->
## Page 151

First Publishing
Atari ST Internal
3 bconout
write character to device
C:
void bconout (dev,
c)
int
dev,
c;
Assembler:
move.w
c,~-(sp)
move.w dev,-(sp)
move.w #3,-(sp)
trap
#13
addq.1
#6,sp
This function serves to output a character "c" to the output device dev
(meaning is the same as for the previous function). The function returns
when the character has been outputted.
Example:
move.w #'A',-(sp)
move.w #0,-(sp)
PRT:
move.w #3,-(sp)
beonout
trap
#13
addq.1 #6,sp
The example outputs the letter "A" to the printer.
144

<!-- source-page: 152 -->
## Page 152

First Publishing
Atari ST Internals
4 rwabs
read and write disk sector
C:
long rwabs(rwflag,
buffer,
number,
recno,dev)
long buffer;
int
rwflag,
number,
recno,
dev;
Assembler:
move.w dev,-—(sp)
move.w recno,-(sp)
move.w number,
- (sp)
move.l buffer,-(sp)
move.w rwflag,- (sp)
move.w #4,-(sp)
trap
#13
add.l
#14,sp
This function serves to read and write sectors on the disk. The parameters
have the following meaning:
rwfilag
Meaning
0
Read sector
1
Write sector
2
Read sector,
ignore disk change
3
Write sector,
ignore disk change
The parameter buffer is the address of a buffer into which the data will be
read from the disk or from which the data will be written to the disk. The
buffer should begin at an even address, or the transfer will run very slowly.
The parameter number specifies how many sectors should be read or written
during the call. The parameter recno specifies which logical sector the
process will start with.
The parameter dev determines which disk drive will be used:
dev
Drive
0
Drive
A
1
Drive
B
2
Hard disk
145

<!-- source-page: 153 -->
## Page 153

First Publishing
Atari ST Internal
The function returns an error code as the result. If this value is zero, the
operation was performed without error. The returned value will be negativi
if an error occurred. The error code has the following meaning:
0
OK,
no error
-1
General error
~2
Drive not
ready
-3
Unknown command
~4
CRC error
-5
Bad request,
invalid command
-6
Seek error,
track
not
found
-7
Unknown media
(invalid boot
sector)
-8
Sector not
found
-9
(No paper)
-10 Write error
-11l Read error
-12 General error
-13 Diskette write protected
-14 Diskette was changed
-15 Unknown device
-16
Bad sector
(during verify)
-17
Insert diskette
(for connected drive)
Example:
move.w #0,-(sp)
Drive
A
move.w #10,-(sp)
Start
at
logical
sector
10
move.w #2,-(sp)
Read
2
sectors
move.l #buffer,-(sp)
Buffer address
move.w
#0,-—(sp)
Read sectors
move.w #4,-(sp)
rwabs
trap
#13
add.1
#14,sp
buffer
ds.b
2%*512
146

<!-- source-page: 154 -->
## Page 154

First Publishing
Atari ST Internals
5 setexec
set exception vectors
C:
long setexec(number,
vector)
int
number;
long vector;
Assembler:
move.l vector,-(sp)
move.w number,-~-(sp)
move.w #5,-(sp)
trap
#13
addq.1
#8,sp
The function setexec allows one of the exception vectors of the 68000
processor to be changed. The number of the vector must be passed in
number and the address of the routine pertaining to it in vector. The
function returns the old vector as the result. If you just want to read the
vector, pass the value -1 as the new address. The 256 processor vectors as
well as 8 vectors for GEM, which numbers $100 to $107 (address $400 to
$41C) can be changed with this function.
Example:
move.l #buserror,-(sp)
move.w #2,-(sp)
move.w #5,-(sp)
trap
#13
addq.1
#8,sp
buserror
147

<!-- source-page: 155 -->
## Page 155

First Publishing
Atari ST Internals
6 tickcal
return millisecond per tick
C:
long tickcal()
Assembler:
move.w #6,-(sp)
trap
#13
addq.1
#2,sp
This function returns the number of milliseconds between two system timer
calls.
Example:
move.w #6,-(sp)
trap
#13
addq.1
#2,sp
Result: 20 ms
148

<!-- source-page: 156 -->
## Page 156

First Publishing
Atari ST Internals
7 getbpb
get BIOS parameter block
C:
long getbpb (dev)
int
dev;
Assembler:
move.w dev,-(sp)
move.w #7,-(sp)
trap
#13
addq.1
#4,sp
This function returns a pointer to the BIOS Parameter Block of the drive
dev (O=drive A, 1=drive B).
The BPB (BIOS Parameter Block ) is constructed as follows:
int
recsiz
Sector
size
in bytes
int
clsiz
Cluster
size
in sectors
int
clsizb
Cluster
size
in bytes
int
xrdlen
Directory length
in sectors
int
fsiz
FAT
size
in sectors
int
fatrec
Sector number
of
the
second FAT
int
datrec
Sector number
of
the
first data cluster
int
numcl
Number
of data clusters
on the disk
int
bflags
Misc.
flags
The function returns the address $3E3E for drive A and the address $3E5E
for drive B. An address of zero indicates an error.
Example:
move.w #0,-(sp)
Drive
A
move.w #7,-(sp)
getbpb
trap
#13
addq.1
#4,sp
149

<!-- source-page: 157 -->
## Page 157

First Publishing
Atari ST Internals
Here are the BPB data for 80 track single and double-sided disk drives:
Parameter
80
track
SS
80 track DS
recsiz
512
512
clsiz
2
2
clsizb
1024
1024
rdlen
7
7
fsiz
5
5
fatrec
6
6
datrec
18
18
numel
351
711
150

<!-- source-page: 158 -->
## Page 158

First Publishing
Atari ST Internals
8 bcostat
return output device status
C:
long bcostat (dev)
int
dev;
Assembler:
move.w dev,-(sp)
move.w #8,-(sp)
trap
#13
addq.1
#4,sp
This function tests to see if the output device specified by dev is ready to
output the next character. dev can accept the values which are described in
function one. The result of this function is either -1 if the output device is
ready, or zero if it must wait.
Example:
move.w #0,~(sp)
Printer ready?
move.w #8,-(sp)
bcostat
trap
#13
addq.1
#4,sp
151

<!-- source-page: 159 -->
## Page 159

First Publishing
Atari ST Internals
9 mediach
inquire media change
C:
long mediach (dev)
int
dev;
Assembler:
move.w dev,~(sp)
move.w #9,—(sp)
trap
#13
addq.1
#4,sp
This function determined if the disk was changed in the meantime. The
parameter dev, the drive number (O=drive A, 1=drive B), must be passed to
the routine. One of three values can occur as the result:
0
Diskette was definitely not changed
1
Diskette may have been changed
|
2
Diskette was definitely changed
|
|
Example:
|
move.w #1,-(sp)
Drive
B
move.w #9,-(sp)
mediach
trap
#13
addq.1 #4,sp
152

<!-- source-page: 160 -->
## Page 160

First Publishing
Atari ST Internals
10 drvmap
.
inquire drive status
C:
long drvmap
()
Assembler:
move.w #10,-(sp)
trap
#13
addq.1
#2,sp
This function returns a bit vector which contains the connected drives. The
bit number n
is set if drive n is available (0 means A, etc.). Even if only one
drive is connected, %11
is still returned, since two logical drives are
assumed.
Example:
move.w #10,-(sp)
drvmap
trap
#13
addq.1
#2,sp
153

<!-- source-page: 161 -->
## Page 161

First Publishing
Atari ST Internals
11 kbshift
C:
long kbshift (mode)
int mode;
Assembler:
move.w mode, —-(sp)
mode.w #11,-(sp)
trap
#13
addq.1
#4,sp
inquire/change keyboard status
With this function you can change or determine the status of the special keys
on the keyboard. If mode
is -1, you get the status, a positive value is
accepted as the status. The status is a bit vector which is constructed as
follows:
B
ct
SHOP
WN
FE
O Fb-
Example:
move .w
move .w
trap
addq.1
Meaning
Right
shift
key
Left
shift
key
Control
key
ALT
key
Caps
Lock
on
Right mouse button
(CLR/HOME)
Left mouse button
(INSERT)
Unused
#-1,-(sp)
Read shift
status
#11,-(sp)
kbshift
#13
#4,sp
154

<!-- source-page: 162 -->
## Page 162

‘irst Publishing
Atari ST Internals
3 The XBIOS
Co support the special hardware features of the Atari ST, there are extended
3IOS functions, which are called via
a TRAP
#14
instruction. The
‘unctions, like the normal BIOS functions,
can be called from assembly
anguage as well as from C. When calling from C, a small TRAP handler in
nachine language is again necessary, which can look like this:
srapl4:
move.1
(sp)+,retsave
Save return address
trap
#14
Call XBIOS
move.l
retsave,-(sp)
Restore
return
address
rts
.bss
retsave
ds.l
1
Space
for the
return address
acro functions can be used in C which allow the extended BIOS functions
(eXtended BIOS, XBIOS) to be called by name. The appropriate function
umber and TRAP call will be created when the macro is expanded.
hen working in assembly language, the function number of the XBIOS
routine need simply be passed on the stack. The XBIOS has 40 different
functions whose signficance and use are described on the following pages.
155

<!-- source-page: 163 -->
## Page 163

First Publishing
Atari ST Internal
0 initmous
initialize mouse
C:
void initmous(type,
parameter,
vector)
int
type;
long parameter,
vector;
Assembler:
move.1l vector,-(sp)
move.l parameter,-(sp)
move.w type,-(sp)
move.w
#0, (~sp)
trap
#14
add.1
#12,sp
This XBIOS function initializes the routines for mouse processing. The
parameter vector is the address of a routine which will be executec
following a mouse-report from the keyboard processor. The parameter t yp:
selects from among the following alternatives:
type
0
Disable mouse
1
Enable mouse,
relative mode
2
Enable mouse,
absolute mode
*
3
unused
4
Enable mouse,
keyboard mode
This allows you to select if mouse movements are to be reported and
i
what manner this will occur.
The parameter parameter points to a parameter block, which is constructec
as follows:
char topmode
char buttons
char xparam
char yparam
The parameter t opmode determines the layout of the coordinate system. A (
means that Y=0 lies in the lower corner,
1 means that Y=0 lies in the uppe:
corner.
156

<!-- source-page: 164 -->
## Page 164

First Publishing
Atari ST Internals
The parameter buttons
is a parameter for the command "set mouse
buttons” of the keyboard processor (see description of the IKBD, intelligent
keyboard).
The parameters xparam and yparam
are scaling factors for the mouse
ovement. If you have selected 2 as the type, the absolute mode, the
arameter block determines four more parameters:
int
int
int
int
xmax
ymax
xstart
ystart
These are the X and Y-coordinates of the maximal value which the mouse
position can assume, as well as the start value to which the mouse will be
set.
Example:
move.
move.
move.
move.
trap
1
#vector,-(sp)
Address
of
the mouse position
1 #parameter,-(sp)
Address
of
the parameter block
w
#1,-(sp)
Enable
relative mouse mode
w #0,-(sp)
Init mouse
#14
add.l
#12,sp
parameter dc.b
......
vector
Mouse interrupt
routine
157

<!-- source-page: 165 -->
## Page 165

First Publishing
Atari ST Internal
=
1 ssbrk
save memory space
C:
long ssbrk (number)
int number;
Assembler:
move.w number,
- (sp)
move.w #1,-(sp)
trap
#14
addq.1
#4,sp
This function reserves memory space. The number of bytes must be passes
in number. The memory space is prepared at the upper end of memory. Th
function returns the address of the reserved memory area as the result. Thi
function must be called before initializing the operating system, meanin;
that is must be called from the boot ROM, before the operating system i:
loaded.
Example:
move.w #$400,-(sp)
Reserve
1K
move.w
#1,-(sp)
ssbrk
trap
#14
addq.1
#4,sp
158

<!-- source-page: 166 -->
## Page 166

First Publishing
Atari ST Internals
2 physbase
return screen RAM base address
C:
long physbase()
Assembler:
move
#2,-(sp)
trap
#14
addq.1
#2,sp
This function returns the base of the physical screen RAM. The physical
screen RAM is the area of memory which is displayed by the video shifter.
The result is a long word.
Example:
$78000,
base address
of
the
screen ‘for
512K RAM
159

<!-- source-page: 167 -->
## Page 167

First Publishing
Atari ST Internal
3 logbase
set logical screen base
C:
long logbase()
Assembler:
move
#3,-(sp)
trap
#14
addq.1
#2,sp
The logical screen base is the address which is used for all output functions
as the screen base. If the physical and logical screen bases are different, one
screen will be displayed while another picture is being constructed in a
different area of RAM, which will be displayed later. The result of this
function call is again a longword.
Example:
$78000,
base
address
of
the
screen
for
512K RAM
160

<!-- source-page: 168 -->
## Page 168

First Publishing
Atari ST Internals
4 getrez
return screen resolution
=:
int getrez()
Assembler:
move.w #4,-(sp)
trap
#14
addq.l1 #2,sp
This function call returns the screen resolution:
Low resolution,
320*200 pixels,
16 colors
6)
=
1
:=
Medium resultion,
640*200 pixels,
4
colors
2
:=
High resolution,
640*400,
pixels,
monochrome
Example:
2,
monochrome
161

<!-- source-page: 169 -->
## Page 169

First Publishing
Atari ST Internal
5 setscreen
Set Screen parameters
C:
void setscreen(logadr,
physadr,
res)
long logadr,
physadr;
int
res;
Assembler:
move.w res,~(sp)
move.l physadr,-(sp)
move.l logadr,-(sp)
move.w #5,-(sp)
trap
#14
add.1
#12,sp
This function changes the screen parameters which can be read with the
previous three functions. If a parameter should not be set, a negative value
must be passed. The parameters are set in the next VBL routine so that no
disturbances appear on the screen.
Example:
Set the physical and the logical screen address to $70000, retain the
resolution.
move.w #-1,-(sp)
Retain resolution
move.1 #$70000,-(sp)
Physical base
move.l1 #$70000,-(sp)
Logical base
move.w #5,-(sp)
setscreen
trap
#14
add.1
#12,sp
162

<!-- source-page: 170 -->
## Page 170

First Publishing
Atari ST Internals
6 setpalette
set color palette
C:
void setpalette (paletteptr)
long paletteptr;
Assembler:
move.l paletteptr,-(sp)
move.w #6,-(sp)
,
trap
#14
addq.1
#6,sp
A new color palette can be loaded with this function.
The parameter
paletteptr must be a pointer to a table with 16 colors (each a word). The
address of the table must be even. The colors will be loaded at the start of
the next VBL. Example:
move.l #palette,-(sp)
Address
of the
new color palette
move.w
#6,-~-(sp)
set palette
trap
#14
addq.1
#6,sp
‘palette
de.w
$777,$700,$070,$007,
$111, $222, $333,$444,
|
$555, $000, $001, $010, $100,$200,$020,$002,
$123,$456
163

<!-- source-page: 171 -->
## Page 171

First Publishing
Atari ST Internals
—
7 setcolor
set color
C:
int setcolor(colornum,
color)
int colornum,
color
Assembler:
move
move
move
trap
addq.
~W
W
oW
1
color,-(sp)
colornum,
- (sp)
#7,-(sp)
#14
#6,sp
This function allows just one color to be changed. The color number (0-15)
and the color belonging to it (0-$777) must be specified. If -1 is given as the
color, the color is not set but the previous color is returned.
Example:
move.
move.
move.
trap
addq.
a
=
#$777,-(sp)
Color white
#1,-(sp)
As color number
1
#7,-(sp)
#14
#6, sp
164

<!-- source-page: 172 -->
## Page 172

First Publishing
Atari ST Internals
8 floprd
read diskette sector
fal Cc:
int floprd(buffer,
filler,
dev,
sector,
track,
side,
count)
long buffer,
filler;
int
dev,
sector,
track,
side,
count;
Assembler:
move.w count,~(sp)
move.w side,-(sp)
move.w track,~(sp)
move.w sector,-(sp)
move.w dev,-(sp)
clr.1
-(sp)
move.1 buffer,-(sp)
move.w #8,-(sp)
trap
#14
add.1
#20,sp
This function reads one or more sectors in from the diskette. The parameters
have the following meaning:
count:
Specifies how many sectors are to be read. Values between
one and nine (number of sectors per track) are possible.
side:
Selects the diskette side, zero for single-sided drives and
zero or one for double-sided drives.
track:
Determines the track number (0-79 for 80-track drives or
0-39 for 40-track drives).
sector: The sector number of the first sector to be read (0-9).
dev:
| Determine drive number, 0 for drive A and 1 for drive B.
filler: Unused long word.
buffer: Buffer in which the diskette data should be written. The
buffer must begin on a word boundary and be large enough
for the data to be read (512 bytes times the number of
sectors).
165

<!-- source-page: 173 -->
## Page 173

First Publishing
Atari ST Internal
The function returns an error code which has the following meaning:
0
OK,
no error
-1
General error
-2
Drive
not
ready
-3
Unknown command
-4
CRC error
-5
Bad request,
invalid command
-6
Seek error,
track
not
found
-7
Unknown media
(invalid boot
sector)
-8
Sector not
found
-9
(No paper)
-10 Write error
~11 Read error
-12 General error
~13 Diskette write protected
~14 Diskette
was changed
-15 Unknown device
-16 Bad sector
(during verify)
-17
Insert diskette
(for connected drive)
Example:
move.w #1,-(sp)
Read
a sector
move.w #0,-(sp)
Page
zero
move.w #0,-(sp)
Track
zero
move.w #1,-(sp)
Sector
one
move.w #1,-(sp)
Drive
B
clr.1l
-(sp)
move.l #buffer,-(sp)
move.w
#8,-(sp)
floprd
trap
#14
add.1
#20,sp
tst
dao
Did error occur?
bmi
error
yes
buffer
ds.b
512
Buffer
for
a
sector
166

<!-- source-page: 174 -->
## Page 174

First Publishing
Atari ST Internals
9 flopwr
write diskette sector
C:
int
floprd(buffer,
filler,
dev,
sector,
track,
side,
count)
long buffer,
filler;
int
dev,sector,track,side,count;
Assembler:
move.w count,-(sp)
move.w
side,- (sp)
move.w track,-~(sp)
move.w sector,-(sp)
move.w dev,-(sp)
clr.l
-(sp)
move.1l buffer,-(sp)
move.w #9,-(sp)
trap
#14
add.l
#20,sp
One or more sectors can be written to disk with this XBIOS function. The
parameters have the same meaning as for the function 8 floprd. The function
returns an error code which also has the same meaning as for reading
sectors. Example:
move.w #3,-(sp)
Write three
sectors
move.w #0,-~(sp)
Side
zero
move.w #7,-(sp)
Track seven
move.w
#1,-~(sp)
Sector one
move.w #0,~(sp)
Drive
A
clr.1
-(sp)
move.1
#buffer,-(sp)
Address
of
the buffer
move.w #9,-(sp)
flopwr
trap
#14
add.1
#20,sp
tst
dao
Did an error occur?
bmi
error
yes
buffer
ds.b
3*512
Buffer
for three
sectors
167

<!-- source-page: 175 -->
## Page 175

First Publishing
Atari ST Internal
10 flopfmt
format diskette
C:
int
flopfmt (buffer,
filler,
dev,
spt,
track,
side,
interleave,
magic,
virgin)
long buffer,
filler,
magic;
int
dev,
spt,
track,
side,
interleave,
virgin;
Assembler:
move.
move.
move.
move.
move.
move.
move.
clr.l
move.1
move .w
trap
add.1
ZEEE
Zz ZrE
virgin,-(sp)
magic,
- (sp)
interleave,-(sp)
side,-(sp)
track,-(sp)
spt,-(sp)
dev,- (sp)
~ (sp)
buffer,-(sp)
#10,-(sp)
#14
#26,sp
This routine serves to format a track on the diskette. The parameters have
the following meanings:
virgin:
The sectors are formatted with
this value. The
standard value is $ESES. The high nibble of each byte
may not contain the value $F.
magic:
The constant $87654321 must be used as magic or
formatting will be stopped.
interleave:
Determines in which order the sectors on the disk will
be written, usually one.
side:
Selects the disk side (0 or 1).
track:
The number of the track to be formatted (0-79).
spt:
Sectors per track, normally 9.
dev:
The drive, 0 for A and
1 for B.
168

<!-- source-page: 176 -->
## Page 176

First Publishing
Atari ST Internals
filler:
Unused long word.
buffer:
Buffer for the track data; for 9 sectors per track the
buffer mst be at least 8K large.
The function returns an error code as its result. The value -16, bad sectors,
means that data in some sectors could not be read back correctly. In this
case the buffer contains a list of bad sectors (word data, terminated by
zero). You can format these again or mark the sectors as bad.
Example:
move.w #S5E5E5,-(sp)
Initial data
move.1l #$87654321,-(sp)
magic
move.w #1,-(sp)
interleave
move.w #0,-(sp)
side
0
move.w #79,-(sp)
track
79
move.w #9,-(sp)
9
sector per track
move.w #0,-~(sp)
drive
A
clr.l1
-(sp)
move.w #buffer,-(sp)
move.w #10,-(sp)
flopfimt
trap
#14
add.1
#26,sp
tst
do
bmi
error
buffer
ds.b
$2000
8K buffer
11 unused
169

<!-- source-page: 177 -->
## Page 177

First Publishing
Atari ST Internals
12 midiws
write string to MIDI interface
C:
void midiws(count,
ptr)
int
count;
long ptr;
Assembler:
move.l ptr,-(sp)
move.w count,-(sp)
move.w #12,-(sp)
trap
#14
addq.1 #8,sp
With this function it is possible to output a string to the MIDI interface
(MIDI OUT). The parameter ptr must point to a string, count must contain
the number of characters to be sent minus 1.
Example:
move.l #string,-(sp)
Address
of the string
move.w #stringend-string-1,-(sp)
Length
move.w #12,-(sp)
midiws
trap
#14
addq.1
#8,sp
string
dc.b
'MIDI
data"
stringend equ
*
170

<!-- source-page: 178 -->
## Page 178

First Publishing
Atari ST Internals
13 mfpint
initialize MFP format
C:
void mfpint (number,
vector)
int
number;
long vector;
Assembler:
move.l1 vector,-(sp)
move .w number,
-— (sp)
move.w #13,-(sp)
trap
#14
addq.1
#8,sp
This function initializes an interrupt routine in the MFP. The number of the
MFP interrupt is in number while vector contains the address of the
corresponding interrupt routine. The old interrupt vector is overwritten.
Example:
move.1
#busy,- (sp)
Busy interrupt
routine
move.w #0,~(sp)
Vector number
0
move.w #13,-(sp)
mfpint
trap
#14
addq.1
#8,sp
busy:
171

<!-- source-page: 179 -->
## Page 179

First Publishing
Atari ST Internals
14 iorec
return record buffer
C:
long
iorec (dev)
int
dev;
Assembler:
move.w dev,-(sp)
move.w #14,-(sp)
trap
#14
addq.1
#4,sp
This function fetches a pointer to a buffer data record for an input device.
The following input devices can be specified:
dev
Input device
RS-232
Keyboard
MIDI
NF
oO
O
The buffer record for an input device has the following layout:
long
ibuf
Pointer
to
an input buffer
int
ibufsize Size
of the input buffer
int
ibufhd
Head index
int
ibuftl
Tail index
int
ibuflow
Low water mark
int
ibufhi
High water mark
The input buffer is a circular buffer; the head index specifies the next write
position (the buffer is filled by an interrupt routine) and the tail index
specifies from where the buffer can be read. If the head and tail indices are
the same, the buffer is empty. The low and high marks are used in
connection with the communications status for the RS-232 (KON/XOFF or
RTS/CTS). If the input buffer is filled up to the high
water
mark, the
sender is informed via XON or CTS that the computer cannot receive any
more data. When data received by the computer can be processed again, so
that the buffer contents sink below the low water mark, the transfer is
resumed.
There is an identically-constructed buffer record for the RS-232 output
which is located directly behind the input record.
172

<!-- source-page: 180 -->
## Page 180

First Publishing
Atari ST Internals
Example:
move.w #1,~-({sp)
Buffer record for keyboard
move.w #14,-(sp)
jorec
trap
#14
addq.1
#4,sp
Result: $9F2
The following table contains the data for all devices:
RS-232
input
RS-232
output
Keyboard
MIDI
Address
$9D0
($9DE)
$942
$A00
Buffer address
$6D0
$7D0
$8D0
$950
Buffer length
$100
$100
$80
$80
Head index
0
0
0
0
Tail
index
0
0
0
0
Low water mark
$40
$40
$20
$20
High water mark
$C0
$c0
$20
$20
Head and tail indices are naturally dependent on the current operating mode.
High and low water marks are set at 3/4 and 1/4 of the buffer size. They
have significance only for XON/XOFF or RTS/CTS in connection with
RS-232.
173

<!-- source-page: 181 -->
## Page 181

First Publishing
Atari ST Internals
15 rsconf
set RS-232 configuration
C:
void rsconf (baud,
ctrl,
ucr,
rsr,
tsr,
scr)
int baud,
ctrl,
ucr,
rsr,
tsr,
scr;
Assembler:
move.w scr,-(sp)
move.w tsr,-(sp)
move.w rsr,-(sp)
move.w ucr,-(sp)
move.w ctrl,-(sp)
move.w baud,-(sp)
move.w #15,-(sp)
trap
#14
add.i1
#14,sp
This XBIOS function serves to configure the RS-232 interface. The
parameters have the following signifcance:
scr:
Synchronous Character Register
in the MFP
tsr:
Transmitter Status Register
in the MFP
rsr:
Receiver Status Register
in
the MFP
ucr:
USART Control Register
in the MFP
ctrl:
Communications parameters
baud:
Baud rate
See the section on the MFP 68901 for information on the MFP registers. If
one of the parameters is -1, the previous value is retained. The handshake
mode can be selected with the ct r1 parameter:
ctrl
Meaning
0
No handshake,
default
after power-up
1
XON/XOFF
2
RTS/CTS
3
XON/XOFF
and RTS/CTS
(not useful)
174

<!-- source-page: 182 -->
## Page 182

First Publishing
Atari ST Internals
The baud parameter contains an indicator for the baud rate:
baud
Baud rate
aoa~Tn
UP WNYE
O
oR
pt
RA
RE
pe
OpwryrHow
Example:
move.
move.
move.
move.
move.
move.
move.
trap
add.1
fee
ez tetz
ez
19200
9600
4800
3600
2400
2000
1800
1200
600
300
200
150
134
110
75
50
#~1,~(sp)
#-1,-(sp)
#-1,-(sp)
#-1,~-(sp)
#1,-(sp)
#9,-(sp)
#15,~-(sp)
#14
#14,sp
Don't change MFP
registers
XON/XOFF
300 baud
rscont
175

<!-- source-page: 183 -->
## Page 183

First Publishing
Atari ST Internals
16 keytbl
set keyboard table
C:
long keytbl(unshift,
shift,
capslock)
long unshift,
shift,
capslock;
Assembler:
move.
move.
move.
move.
trap
addi.
See EY
1
capslock,
- (sp)
shift,-(sp)
unshift,-(sp)
#16,-(sp)
#14
#14,sp
With this function it is possible to create a new keyboard layout. To do this
you must pass the address of the new tables which contain the key codes for
normal keys (without shift), shifted keys, and keys with caps lock. The
function returns the address of the vector table in which the three keyboard
|
table pointers are located. If a table should remain unchanged, -1 must be
passed as the address. A keyboard table must be 128 bytes long. It is
addressed via the key scan code and returns the ASCII code of the given
key.
Example:
move.
move.
move.
move.
trap
addi.
shift:
unshift:
a
ke
#-1,-(sp)
Don't
change caps
lock
#shift,-(sp)
Shift table
#unshift,-(sp)
Table without
shift
#16,-(sp)
#14
#14,sp
176

<!-- source-page: 184 -->
## Page 184

First Publishing
Atari ST Internals
17 random
return random number
C:
long random()
Assembler:
move.w #17,~(sp)
trap
#14
addq.1l #2,sp
This function returns a 24-bit random number. Bits 24-31 are zero. With
each call you receive a different result. After turning on the computer a
different seed is created.
Example:
move.w #17,-(sp)
random
trap
#14
addq.1
#2,sp
177

<!-- source-page: 185 -->
## Page 185

First Publishing
Atari ST Internals
18 protobt
produce boot sector
C:
void protobt (buffer,
serialno,disktype,
execfilag)
long buffer,
serialno;
int
disktype,
execflag;
Assembler:
move.w execflag,-~(sp)
move.w disktype,~-(sp)
move.1l serialno,~(sp)
move.l buffer,-(sp)
move.w #18,-(sp)
trap
#14
add.1l
#14,sp
This function serves to create a boot sector. A boot setor is located on track
0, sector 1 on side 0 of a diskette and gives the DOS information about the
disk type. If the boot sector is executable, it can be be used to load the
|
operating system. With this function you can create a new boot sector, for a
different disk format or to change an existing boot sector. The parameters:
execflag: determines if the boot sector is executable.
0
not
executable
1
executable
-l1
boot
sector remains
as
it
was
The disk type can assume the following values:
40
track,
single
sided
(180
k)
40
track,
double
sided
(360
K)
80
track,
single
sided
(360
K)
80
track,
double sided
(720
K)
Disk type
remains unchanged
HY WNH
Oo
The parameter serialno
is a 24-bit serial number which is written in the
boot sector. If the serial number is greater than 24 bits ($01000000), a
random serial number is created (with the above function). A value of -1
means that the serial number will not be changed.
The parameter buffer is the address of a 512-byte buffer which contains
the boot sector or in which the boot sector will be created.
178

<!-- source-page: 186 -->
## Page 186

First Publishing
Atari ST Internals
A boot sector has the following construction:
Address
40
track
SS
40
track
DS
80 track
SS
80 track
DS
o-
1
2-
7
8-10
11-12
13
14-15
16
17- 18
19-20
21
22-23
24-25
26-27
28-29
510-511 CHECKSUM
Branch instruction
to boot program
if executable
*Loader'
24-bit
serial number
BPS
512
512
512
512
SPC
1
2
2
2
RES
1
1
1
1
FAT
2
2
2
2
DIR
64
112
112
112
SEC
360
720
720
1440
MEDIA 252
253
248
249
SPF
2
2
5
5
SPT
9
9
9
)
SIDE
1
2
1
2
HID
0
0
0
0
The abbreviations have the following meanings:
BPS:
SPC:
RES:
FAT:
DIR:
SEC:
Bytes per sector. The sector size is
512 bytes for all formats
Sectors per cluster. The number of sectors which are combined
into one block by the DOS, 2 sectors equals 1K.
Number of reserved sectors at the start of the disk including the
boot sector.
The number of file allocation tables on the disk.
The maximum number of directory entries.
The total number of sectors on the disk.
MEDIA: Media descriptor byte, not used by the ST-BIOS.
SPF:
SPT:
Number of sectors in each FAT.
Number of sectors per track.
179

<!-- source-page: 187 -->
## Page 187

First Publishing
Atari ST Internals
SIDE:
HID:
Number of sides of the diskette.
Number of hidden sectors on the disk.
The boot sector is compatible with MS-DOS 2.x. This is why all 16-bit
words are stored in 8086 format (first low byte, then high byte).
If the checksum of the whole boot sector is $1234, the sector is executable.
In this case the boot program is located at address 30. Example:
move.
move.
move.
move.
move.
trap
add.1
free
«€
#-1,-(sp)
#3,-(sp)
#-1,-(sp)
#buffer,-(sp)
#18,-(sp)
#14
#14,sp
buffer ds.b
512
Don't
change executability
80
tracks
DS
Don't change serial number
protobt
This example program can be used to adapt an existing boot sector for 80
tracks, double sided.
180

<!-- source-page: 188 -->
## Page 188

First Publishing
Atari ST Internals
19 flopver
verify diskette sector
C:
int
flopver(buffer,
filler,
dev,
sector,
track,
side,
count)
long buffer,
filler;
int
dev,
sector,
track,
side,
count;
Assembler:
move.w count,-(sp)
move.w side,-(sp)
move.w track,-(sp)
move.w sector,-(sp)
move.w dev,-(sp)
clr.1l
-(sp)
move.l1 buffer,-(sp)
move.w #19,-(sp)
trap
#14
add.1
#16,sp
This function serves to verify one or more sectors on the disk. The sectors
are read from the disk and compared with the buffer contents in memory.
The parameters have the same meaning as for reading and writing sectors. If
the sector and buffer contents agree, the result of the function will be zero.
If an error occurs, the error number will be returned in DO that has the
following meaning:
0
OK,
no error
-1
General error
-2
Drive
not
ready
-3
Unknown command
-4
CRC error
-5
Bad request,
invalid command
-6
Seek error,
track
not
found
-7
Unknown media
(invalid boot
sector)
-~8
Sector
not
found
-9
(No paper)
~10
Write error
~11
Read error
-12 General error
-13 Diskette write protected
-14 Diskette
was
changed
-15 Unknown device
181

<!-- source-page: 189 -->
## Page 189

First Publishing
Atari ST Internals
-16
Bad sector
(during verify)
-17
Insert diskette
(for connected drive)
In the case of an error, the buffer will contain a list of erroneous sectors
(16-bit values), terminated by a zero word. If the BIOS function 4 rwabs
was used to write the sectors and if the variable fverify ($444) is set, the
sectors will automatically be verified after they are written.
Example:
move.w #1,-(sp)
A sector
move.w #0,-(sp)
Side
zero
move.w #39,-(sp)
Track
39
move.w #1,-(sp)
Sector
1
move.w #0,-(sp)
Drive
A
clr.l
-(sp)
move.l1
#buffer,-(sp)
Buffer address
move.w #19,-(sp)
flopver
trap
#14
add.l
#16,sp
tst
do
Error?
bmi
error
182

<!-- source-page: 190 -->
## Page 190

First Publishing
Atari ST Internals
20 scrdmp
output screen dump
C:
void scrdmp
()
Assembler:
move.w #20,-(sp)
trap
#14
addq.1
#2,sp
This function outputs a hardcopy of the screen to a connected printer. The
previously-set printer parameters (‘desktop Printer setup") are used. You
can also perform this function by simultaneously pressing the ALT and
HELP keys or from the desktop through "Print Screen" from the "Options"
menu.
Example:
move.w
#20,-(sp)
Hardcopy
trap
#14
Call XBIOS
addq.1
#2,sp
183

<!-- source-page: 191 -->
## Page 191

First Publishing
Atari ST Internals
21
cursconf
set cursor configuration
C:
int
cursconf (function,
rate)
int
function,
rate;
Assembler:
move.
move.
move.
trap
addq.
=
=
re
rate,- (sp)
function, ~(sp)
#21,-(sp)
#14
#6,sp
This XBIOS function serves to set the cursor function. The parameter
function can have a value from 0-5, which have the following meanings:
function
0
om
WN
PF
Meaning
Disable
cursor
Enable cursor
Flash
cursor
Steady cursor
Set
cursor flash
rate
Get
cursor
flash
rate
You can use this function to set whether the cursor is visible, and whether it
is flashing or steady. Thie XBIOS function returns a result only if you fetch
the old baud rate. The unit of the flash frequency is dependent on the screen
frequency: It is 70 Hz for a monochrome monitor or 50 Hz for a color
monitor. You can set a new flash rate with function number 5. You need
only use the parameter rate if you want to pass a new flash rate.
Example:
move.
move.
move.
trap
addq.
eS
=
=
nd
#20,-(sp)
#4,-(sp)
#21,-(sp)
#14
#6,sp
20/70
seconds
Set
flash
rate
cursconft
184

<!-- source-page: 192 -->
## Page 192

First Publishing
Atari ST Internals
22 settime
set clock time and date
C:
void settime (time)
long time;
Assembler:
move.l1 time,- (sp)
move.w #22,-(sp)
trap
#14
add.l
#6,sp
This function is used to set the clock time and date. The time is passed in the
lower word of time and the date in the upper word. The time and date are
coded as follows:
bits
O-
4
bits
5-10
bits
11~15
bits
16-20
bits
21-24
bits
25-31
Example:
Seconds
in two-second increments
Minutes
Hours
Day
1-31
Month
1-12
Year
(minus
offset
1980)
move.1 #%1011001100000100000000000000,-(sp)
move.w #22,-(sp)
settime
trap
#14
addq.1
#6,sp
This call sets the date to the 16th of September, 1985, and the clock time to
8 o'clock.
185

<!-- source-page: 193 -->
## Page 193

First Publishing
Atari ST Internals
23 gettime
return clock time and date
C:
long gettime()
Assembler:
move.w #23,-(sp)
trap
#14
addq.1
#2,sp
This function returns the current date and the clock time in the followin g
format:
bits
0O-
4
Seconds
in two-second increments
bits
5-10
Minutes
bits
11-15
Hours
bits
16-20
Day
1-31
bits 21-24
Month
1-12
bits
25-31
Year
(minus
offset
1980)
Example:
move.w #23,-(sp)
gettime
trap
#14
addq.1
#2,sp
move.1 d0,time
Save time
and date
186

<!-- source-page: 194 -->
## Page 194

First Publishing
Atari ST Internals
24 bioskeys
restore keyboard table
C:
void bioskeys
()
Assembler:
move.w #24,-~(sp)
trap
#14
addq.1
#2,sp
If you have selected a new keyboard layout with the XBIOS function 16,
keytbl, this function will restore the standard BIOS keyboard layout. You
can call this function, for example, before exiting a program of your own
which changed the keyboard layout.
Example:
move.w #24,-(sp)
bioskeys
trap
#14
addg.1
#2,sp
187

<!-- source-page: 195 -->
## Page 195

First Publishing
Atari ST Internals
—
25 ikbdws
intelligent keyboard send
C:
void ikbdws (number,
pointer)
int
number;
long pointer;
Assembler:
move.l1 pointer,-(sp)
move.w number, -(sp)
move.w #25,-(sp)
trap
#14
addq.1
#8,sp
This XBIOS function serves to transmit commands to the keyboard
processor (intelligent keyboard). The parameter pointer is the address of 2
string to be sent, number is the length of a string minus 1.
Example:
|
move.l
#string,-(sp)
Address
of
the string
move.w #strend-string-1,-(sp)
Length minus
1
move.w
#25,-—(sp)
ikbdws
trap
#14
addq.1
#8,sp
string
de.b
$80,1
strend
equ
*
188

<!-- source-page: 196 -->
## Page 196

First Publishing
Atari ST Internals
26 jdisint
disable interrupts on MF P
C:
void jdisint (number)
int number;
‘Assembler:
move.w number,
- (sp)
move.w #26,-(sp)
trap
#14
addq.1
#4,sp
This function makes it possible to selectively disable interrupts on the MFP
68901. The parameter is the MFP interrupt number (0-15). The significance
of the individual interrupts is described in the section on interrupts.
Example:
move.w #10,-(sp)
Disable RS-232 transmitter interrupt
move.w #26,-(sp)
Disable interrupt
trap
#14
addq.1
#4,sp
189

<!-- source-page: 197 -->
## Page 197

First Publishing
Atari ST Internal
27 jenabint
enable interrupts on MFP
C:
void jenabint (number)
int number;
Assembler:
move.w number,
— (sp)
move.w #27,-(sp)
trap
#14
addq.1
#4,sp
This function can be used to re-enable an interrupt on the MFP. The
parameter is again the number of the interrupt, 0-15.
Example:
move.w #12,-(sp)
Enable RS-232
receiver interrupt
move.w #27,-(sp)
Enable interrupt
trap
#14
addgq.1
#4,sp
190

<!-- source-page: 198 -->
## Page 198

First Publishing
Atari ST Internals
28 giaccess
access GI sound chip
C:
char giaccess(data,
register)
char data;
register;
int
Assembler:
move.
move.
move.
trap
addq.
=z
=
=z
1
#register,-
(sp)
#data,—-(sp)
#28,-(sp)
#14
#6,sp
This function allows access to the registers of the GI sound chip.
register must contain the register number of the sound chip (0-15). The
meaning of the individual registers is given in the hardware description of
the sound chip. Bit 7 of the register number determines whether the
specified register will be written or read:
Bit
7
:
Read
1:
Write
When writing, an 8-bit value is passed in data; when reading, the function
returns the contents of the corresponding register.
Example:
move.
move.
move.
trap
addq.
=
2
=
| aoe
#$80+3,-(sp)
Write register
3
#$50,-(sp)
Value
to write
#28,-(sp)
#14
#6,sp
191

<!-- source-page: 199 -->
## Page 199

First Publishing
Atari ST Internal
29
offgibit
reset Port A GI sound chip
C:
void offgibit (bitnumber)
int bitnumber;
Assembler:
move.w #bitnumber,
- (sp)
move.w #29,-(sp)
trap
#14
addq.1
#4,sp
A
bit of port A of the sound chip can be selectively set with this function
call. Port A is an 8-bit output port in which the individual bits have the
following funtion:
.
Bit
0:
Select disk side 0/side
1
Bit
1:
Select drive
A
Bit
2:
Select drive
B
Bit
3:
RS-232
RTS
(Request
To
Send)
Bit
4:
RS~232 DTR
(Data Terminal Ready)
Bit
5:
Centronics
strobe
Bit
6:
General Purpose Output
Bit
7:
unused
Example:
move.w #4,-(sp)
DTR bit
move.w #29,-(sp)
offgibit
trap
#14
addq.1
#4,sp
192

<!-- source-page: 200 -->
## Page 200

First Publishing
Atari ST Internals
30 ongibit
clear Port A of GI sound chip
C:
void ongibit (bitnumber)
int bitnumber;
Assembler:
move.w #bitnumber,
- (sp)
move.w #30,-(sp)
trap
#14
addq.1
#4,sp
This function is the counterpart of the previous function. With this it is
possible to clear a bit of port A in the sound chip.
Example:
move.w #4,-(sp)
DTR bit
move.w #30,-(sp)
ongibit
trap
#14
addg.1 #4,sp
193

<!-- source-page: 201 -->
## Page 201

First Publishing
Atari ST Internals
31 xbtimer
start MFP timer
C:
void xbtimer(timer,
control,
data,
vector)
int
timer,
control,
data;
long vector;
Assembler:
move.1l vector,-(sp)
move.w data,-(sp)
move.w control,-(sp)
move.w timer,-—(sp)
move.w #31,-(sp)
trap
#14
add.l
#12,sp
This function allows you to start a timer in the MFP 68901 and assign an
interrupt routine to it. timer
is the number of the timer in the MFP:
Timer
Timer
Timer
Timer
9A WD
WNR
OS
The parameters data and control
are the values which are placed in the
corresponding control and data registers of the timer. We refer you to the
hardware description of the MFP 68901.
The parameter vector
is the address of the interrupt routine which will be
executed when the timer runs out. The four timers in the MFP are already
partly used by the operating system:
Timer
A:
Reserved for the end user
Timer
B:
Horizontal blank counter
Timer
C:
200
Hz
system timer
Timer
D:
RS-232
baud rate generator
(the interrupt
vector
is
free)
194

<!-- source-page: 202 -->
## Page 202

First Publishing
Atari ST Internals
Example:
move.
move.
move.
move.
move.
trap
add.1
feet er
#vector,- (sp)
data,-(sp)
control,-(sp)
#0,-(sp)
#31,-~(sp)
#14
#12,sp
Interrupt
routine
Data
and
Control registers
Timer
A
xbtimer
195

<!-- source-page: 203 -->
## Page 203

First Publishing
Atari ST Internals
32 dosound
set sound parameters
C:
void dosound (pointer)
long pointer;
Assembler:
move.1 pointer, ~-(sp)
move.w
#32,-(sp)
trap
#14
addq.1
#6,sp
This function allows for easy sound processing. The parameter pointer
must point to a string of sound commands. The following commands can be
used:
Commands: $00-$0F
These commands are interpreted as register numbers of the sound
chip. A byte following this is loaded into the corresponding register.
Command $80
An argument follows this command which will be loaded into a
temporary register.
Command $81
Three arguments must follow this command. The first argument is the
number of the register in the sound chip in which the contents of the
temporary register will be loaded. The second argument
is
a
two's-complement value which will be added to the temporary
register. The third argument contains an end criterium. The end is
reached when the content of the temporary register is equal to the end
criterium.
Commands $82-$FF
One argument follows each of these commands. If this argument is
zero, the sound processing
is halted. Otherwise this argument
specifies the number of timer ticks (20ms, 50Hz) until the next sound
processing.
196

<!-- source-page: 204 -->
## Page 204

First Publishing
Atari ST Internals
Example:
move.l #pointer,-(sp)
Pointer
to sound command
move.w #32,-(sp)
dosound
trap
#14
addq.1 #6,sp
pointer
dc.b 0,10,1,50,.
197

<!-- source-page: 205 -->
## Page 205

First Publishing
Atari ST Internal
33 setprt
Set printer configuration
C:
void setptr (config)
int config;
Assembler:
move.w config,-(sp)
move.w #33,-(sp)
trap
#14
addq.1
#4,sp
This function allows the printer configuration to be read or changed. If
config contains the value -1, the current value is returned, otherwise the
value is accepted as the new printer configuration. The printer configuration
is a bit vector with the following meaning:
Bit number
0
1
0
matrix printer
daisy-wheel
1
monochrome printer color printer
2
Atari printer
Epson printer
3
Test mode
Quality mode
4
Centronics port
RS-232 port
5
Continuous paper
Single-sheet
6-14
reserved
15
always
0
Example
move.w #%000100,-(sp)
Epson printer
move.w #33,-(sp)
setprt
trap
#14
addq.1
#4,sp
198

<!-- source-page: 206 -->
## Page 206

First Publishing
Atari ST Internals
34 kbdvbase
return keyboard vector table
C:
long kbdvbase
()
Assembler:
move.w #34,-(sp)
trap
#14
addq.1
#2,sp
This XBIOS function returns a pointer to a vector table which contains the
address of routines which process the data from the keyboard processor.
The table is constructed as follows:
long
midivec
MIDI input
long
vkbderr
Keyboard error
long
vmiderr
MIDI error
iong
statvec
IKBD status
long
mousevec
Mouse routines
long
clockvec
Clock time routine
long
joyvec
Joystick routines
The parameter midivec points to a routine which writes data received from
the MIDI input (byte in DO) to the MIDI buffer.
The parameters vkbderr
and vmiderr
are called when an overflow is
signaled by the keyboard or MIDI ACIA.
The remaining four routines stat vec, mousevec, clockvec, and joyvec
process the corresponding data packages which come from the keyboard
ACIA. A pointer to the packaged received is passed to these routines in AO.
The mouse vector is used by GEM. If you want to use your own routine,
you must terminate it with RTS and it may not require more than one
mullisecond of processing time.
Example:
move.w #34,-(sp)
kbdvbase
trap
#14
addq.1
#2,sp
199

<!-- source-page: 207 -->
## Page 207

First Publishing
Atari ST Internak
We get SAOE as the result. The vector field contains the following values:
AOE
Al2
Al16
AlA
A1E
A22
A26
A2A
A2E
midivec
vkbderr
vmiderr
statvec
mousevec
clockvec
joyvec
MIDI
keyboard
200
$79C6
$759C
$759C
$7034
$15296
$6A46
$7034
$7556
$7568

<!-- source-page: 208 -->
## Page 208

Oe
First Publishing
Atari ST Internals
35 kbrate
set keyboard repeat rate
C:
int kbrate(delay,
repeat)
int delay,
repeat;
Assembler:
move.w repeat,-(sp)
move.w delay,~-(sp)
move.w #35,-(sp)
trap
#14
addq.1
#6,sp
The keyboard repeat can be controlled with this function. The parameter
delay specifies the delay time after a key is pressed before the key will
automatically be repeated. The parameter repeat determines the time span
after which the key will be repeated again. These values can be changed
from the desktop by means of the two slide controllers on the control panel.
The times are based on the 50 Hz system clock. If -1 is specified for one of
the parameters, the corresponding value is not set. The function returns the
previous values as the result; bits 0-7 contain the repeat value and bits
8-15 the value of delay.
Example:
move.w #-1,-(sp)
Read old values
move.w #-1,-(sp)
move.w #35,-(sp)
kbrate
trap
#14
addq.1 #6,sp
Result: DO = $0B03
201

<!-- source-page: 209 -->
## Page 209

First Publishing
Atari ST Internals
36 prtblk
C:
void prtblk (parameter)
long parameter;
Assembler:
move.l1 parameter, -—(sp)
move.w #36,-(sp)
trap
#14
addq.1l
#6,sp
output block to printer
This function resembles the function scrdmp(20) and is used by it. The
function expects a parameter list, however, whose address is passed to it.
This list is constructed as follows:
Screen resolution
(0,
1,
Printer port
(0=Centronics,
Pointer
to half-tone mask
Address
of
the screen RAM
or
2)
resultion
(0
or
1)
of
the color palette
(0-3)
1=RS232)
long
blkprt
int
offset
int
width
Screen width
int
height
Screen height
int
left
int
right
int
scrres
int
dstres
Printer
long
colpal
Address
int
type
Printer type
int
port
long
masks
Assembler:
move.1]1 #parameter,
— (sp)
move.w
#36,-(sp)
trap
#14
addq.1
#6,sp
parameter
dce.l
Address
of
the parameter block
prtblik
202

<!-- source-page: 210 -->
## Page 210

First Publishing
Atari ST Internals
37 wvbl
wait for video
C:
void wvbl()
Assembler:
move.w #36,-(sp)
trap
#14
addq.1
#2,sp
This function waits for the next picture return. It can be used to synchronize
graphic outputs with the beam return, for example.
Example:
move.w #36,-(sp)
wait
for wvbl
trap
#14
addq.1
#2,sp
203

<!-- source-page: 211 -->
## Page 211

First Publishing
Atari ST Internals
38 supexec
set supervisor execution
C:
void supexec (address)
long address;
Assembler:
move.1 address,-(sp)
move.w #38,~(sp)
trap
#14
addq.1
#6,sp
If a routine is to be executed in the supervisor mode of the 68000 processor,
you can accomplish this with this function. Simply pass the address of the
routine to the function. Example:
move.l #address,-(sp)
move.w #38,-(sp)
trap
#14
addq.1l
#6,sp
address
move.1
$400,00
204

<!-- source-page: 212 -->
## Page 212

First Publishing
Atari ST Internals
39 puntaes
disable AES
C:
void puntaes
()
Assembler:
move.w #39,-(sp)
trap
#14
addq.1l
#2,sp
The AES can be disabled with this function, provided it is not in ROM.
Example:
move.w #39,-(sp)
trap
#14
addq.1l
#2,sp
205

<!-- source-page: 213 -->
## Page 213

First Publishing
Atari ST Internals
3.4 The Graphics
Next to the high processing speed and the large memory available, the
graphics capability is certainly the most fascinating aspect of the ST. With
the standard monochrome monitor and the resolution of 640x400 points, it
creates a whole new price/performance class for itself. But also in the color
resoultion the ST can display 16 colors with 320x200 screen points.
In this chapter we want to explain how the graphics are organized and how
you can create fast and effective graphics without using the GEM graphics
package, which is rather complicated for beginners. The ST offers the
programmer (assembler and C) very useful routines, with whose help
graphics programming isn't quite child's play, but they can take away a
good deal of the programming work. Unfortunately, some of these
functions are so comprehensive that a detailed description would exceed the
scope of this book. We have therefore had to limit ourselves to the simpler,
but no less interesting functions.
These graphics routines are called in a very elegant manner. The software
developers have made use of the fact that there are two groups of opcodes in
the 68000 which the 68000 does not "understand" and which generate a
trap, or software interrupt, when they are encountered in a program. These
are the two groups of opcodes which begin with $Axxx and $Fxxx. In the
ST, the $Axxx opcode trap is used in order to access the graphics routines.
The trap handler, the program called by the trap, checks the lowest byte of
the "command" to see what value it has. Values between zero and $E are
permissable here. This gives a total of 14 graphics routines, which should
first be presented in an overview. Later we will talk about the actual
commands in detail.
SA000 Determine address
of required variable
range
SA001 Set point
on
the screen
SA002 Determine color
of
a
screen point
$A003 Draw
a
line
on
the
screen
SA004 Draw
a horizontal
line
(very fast!)
$A005 Fill rectangle with color
$A006 Fill polygon
line by
line
SA007 Bit block transfer
$A008 Text block transfer
SA009 Enable mouse
cursor
SAOOA Disable mouse
cursor
206

<!-- source-page: 214 -->
## Page 214

First Publishing
Atari ST Internals
SAOOB Change mouse cursor form
SAOQ00C Clear sprite
SA00D Enable sprite
SAOOE Copy raster form
These routines are the ground work for the hardware-dependent part of
GEM. All GEM graphic and text output is performed by the routines of the
$Axxx opcodes. The set of A-opcodes are very useful in games. In games
windows are needed only in the rarest cases. Another important point is the
speed of the A-instructions. Using the graphic routines directly is clearly
faster than if the output is handled by GEM. Before we describe the
individual commands in detail, we will take a brief look at the construction
of graphics in the various graphic modes of the ST.
Immediately after turning the ST on, an area of 32K bytes is initialized at the
upper memory border as the video RAM. In normal operation this results in
addresses $78000 to $7FFFF acting as the screen RAM. This video RAM
can be viewed as a window in the ST. We will start with the simplest mode,
the 640x400 mode. In this case each 80 bytes, or better, each 40 words
forms one screen line. The word with the lowest address is displayed on the
left edge of the screen, the additional words are displayed in order from left
to right. Within a word, the highest-order bit lies at the left and the
lowest-order bit at the right.
With this data, any point on the screen can be easily controlled or read. For
example, to set the first screen point, the value $8000 must be written into
memory location $78000. Therefore you might store $8000 into memory
location $78000. But this isn't recommended.
You might recall that the screen RAM in the ST can be moved quite easily.
Then the absolute address of $78000 is no longer correct, of course. For
this reason, it is usually more advantageous to set the the point with the "A"
function $A001. Function $A001 assumes an X-Y coordinate system with
origin in the upper left-hand corner, and determines the position of the video
RAM itself in order to set the point at the proper screen location.
In this resolution mode, each screen point is represented by a bit. If the bit
is set, the point appears dark, or bright if the the inverse display mode is
selected in color palette register 0. The screen consists of only one bit plane.
Different colors cannot be represented with just one plane, however. This is
why when the resolution increases in the color modes, the number of
displayable colors decreases.
207

<!-- source-page: 215 -->
## Page 215

First Publishing
Atari ST Internals
Figure 3.4-1 LO-RES-MODE (0)
0
iil
«©
ee
ee
eo eee
e@
@
@
319
OPTTTH
..
cee ce
ec cece cece
eee ee eeee
1
fo:
VIDEO
SCREEN
.
:
°
°
e
°
e
e
°
°
r)
°
e
199
COLOR
NUMBER
VIDEO-RAM
208

<!-- source-page: 216 -->
## Page 216

First Publishing
Atari ST Internals
Four colors possible in the 640x200 resolution mode. In this mode, two
contiguous memory words form a single logical entity. The color of a point
is determined by the value of the two corresponding bits in the two words.
If both bits are zero, the background color results. Therefore two sequential
words are used together for pixel representation. For the colors, however,
all odd words belong to a plane. The second plane is made up of the even
words. In this mode, there are two planes available.
Things become quite colorful in the mode with "only" 320x200 points. In
this operating mode, 4 contiguous memory words form one entity which
detemines the color of the 16 pixels. To stick to the example we used
before: in order to set the point in the upper left-hand corner, the topmost
bits of words $78000, $78002, $78004, and $78006 must be manipulated.
The desired color results from the bit pattern in the words. It naturally
requires some computer time to set a point in the desired color, independent
of the mode. All of this work is handled by the $A001 routine, however.
This routine sets all of the pertaining bits for the desired color in the current
_ fesolution. Naturally, all four planes are present in this mode. The first
|
Plane, keeping to our example, made up of the words at address $7F000,
$7F008, $7F010,
..., and the other planes are composed of the other
addresses correspondingly.
Another point to be clarified concerns the fonts or character sets. Since the
ST does not have a text mode, only a gtaphics mode, the text output is
created in high-resolution graphics. There are three different fonts built into
the ST. You can load additional fonts from disk. Each font has a header
which contains important information about the displayable characters.
Since the important data are contained in the font header, there are unusually
few limits for display. The characters can be arbitrarily high or wide. The
age of the 8x8 matrix for character output is over. Genuine proportional
type on the screen (!) is even possible.
The three built-in fonts use relatively few of the many possibilities which
GEM allows for character generation. All three fonts are mono-spaced
fonts, meaning they have a fixed defined size in pixels and a defined pitch.
The smallest font has a matrix of 6x6. With a resolution of 640x400 points,
66 lines of 106 characters each can be displayed. This font is only
accessible for output under GEM, not for output under TOS, and is used in
the output of the directory in the icon form, for example. The next-largest
type is composed of 8x8 points. This type is used when a color monitor is
connected to the ST, while the third and largest font is used for the normal
black-and-white mode. This font uses a matrix of 8x16 points.
209

<!-- source-page: 217 -->
## Page 217

First Publishing
Atari ST Internals
Figure 3.4-2 MEDIUM-RES-MODE (1)
0
122
ee
ef
@
ee
©
ee
eh
639
U0
ee
ee eee Ce
1
a
i
VIDEO
SCREEN
.
.
°
e
°
°
e
e
e
°
199
rt)
CULL
COL
COLOR
NUMBER
po
om
2
l},-;
VIDEO-RAM
210

<!-- source-page: 218 -->
## Page 218

First Publishing
Atari ST Internals
The exact layout of the font header is found under command $A008, which
represents a very versatile text output which goes far beyond what is
possible with the routine of the BIOS and GEMDOS.
Finally, we must clarify some of the terms which will come up often in the
following descriptions, whose meaning may not be so clear. These are the
terms CONTRL array, INTIN array, INTOUT array, PTSIN array and
PTSOUT array. These arrays are mainly used by GEM to pass parameters
to individual GEM functions or to store results from these functions. But
line-A functions use parts of these arrays to pass parameters also. The
arrays are defined in memory as data areas, whereby each element in the
array consists of 2 bytes.
For GEM functions, the CONTRL array always contains the number
desired in the first element (CONTRL(0)). This parameter is not used by the
line-A commands, however. CONTRL(1) contains the number of XY
\coordinates required for the function. These coordinates must be placed in
the PTSIN array before the call. The element CONTRL(2) is not supplied
before the call. After the call it contains the number of XY coordinates in the
PTSOUT array. CONTRL(3) specifies how many parameters will be
passed to the function in the INTIN array, while CONTRL(4) contains the
number of parameters in the INTOUT array after the call. The additional
parameters of the CONTRL array are not relevant for users of the line A.
Unfortunately, not all of the parameters for the A opcodes can be in these
arrays. For this reason there is another memory area which used as
a
variable area for (almost) all graphic outputs. The function and use of these
over 50 variables is found in a table at the end of this chapter. Important
variables are also explained in conjunction with the functions which require
them.
By the way, you should be aware that registers DO to D2 and AO to A2 are
changed by calling the functions. Important values contained in these
registers should be saved before a call.
211

<!-- source-page: 219 -->
## Page 219

First Publishing
Atari ST Internal:
Figure 3.4-3 HI-RES-MODE (2)
012
oe
e@#
@
©
©
©
©
©
©
©
&
639
an
VIDEO
SCREEN
399
COLOR
NUMBER
VIDEO-RAM
212

<!-- source-page: 220 -->
## Page 220

First Publishing
Atari ST Internals
$A000
Initialize
Initialize is really the wrong expression for this function. After the call, the
addresses of the more important data areas are returned in registers DO and
AO to A2. This function does not require input parameters.
The program is informed of the starting address of the line-A variables in
DO and AO. After the call, Al points to a table with three addresses. These
three addresses are the starting address of the three system font headers.
Register A2 points to a table with the starting addresses of the 15 line-A
routines.
This opcode destroys (at least) the contents of registers DO to D2 and AO to
A2. Important values should be saved before the call.
-$A001 PUT PIXEL
This opcode sets a point at the coordinates specified by the coordinates in
PTSIN(0) and PTSIN(1). The color is passed in INTIN(0). PTSIN(0)
contains X-coordinate, PTSIN (1) the Y-coordinate.
The coordinate system used has its origin in the upper left corner. The
possible range of the X and Y coordinates is naturally set according to the
graohic mode enabled. Overflows in the X range are not handled as errors.
Instead, the Y coordinate is simply incremented by the appropriate amount.
No output is made if the Y range is exceeded.
The color in INTIN (0)
is dependent on the mode used. When driving the
monochrome monitor, only bit zero of the value of INTIN(0) is evaluated.
$A002 GET PIXEL
The color of a pixel can be determined with this opcode. As with $A001,
the XY coordinates are passed in PTSIN(0) and PTSIN (1); the color value
is returned in the DO register.
213

<!-- source-page: 221 -->
## Page 221

First Publishing
Atari ST Internals
$A003 LINE
With the LINE opcode a line can be drawn bewteen the points with
coordinates xl,yl and x2,y2. The parameters for this function are not
passed via the parameter arrays, but must be transferred to the line-A
variables before the call. The variables used are:
_Xl
= xl coordinate
_Y1l
= yl coordinate
_X2
=
x2 coordinate
_Y2
= yl coordinate
_FG_ BP_1
= Plane
1
(all three modes)
_FG_ BP
2
= Plane
2
(640x200,
320x200)
_FG
BP 3
= Plane
3
(only 320x200)
_FG BP_4
= Plane
4
(only 320x200)
_LN_MASK
= Bit pattern
of the line
For example:
$FFFF
= filled
$cccc
= broken
_WRT_MOD
= Determines the write mode
_LUSTLIN
= This variable should be set
to
-1
(SFFFF)
One point to be noted for some applications is the fact that when drawing a
line, the highest bit of the line bit pattern is always set on the left screen
edge. The line is always drawn from left to right and from top to bottom,
not from x1,y1 to x2,y2.
Range overflows are handled as for PUT PIXEL. If an attempt is made to
draw a
line from 0,0 to 650,50, a line is actually drawn from, 0,0 to
639,48. The "remainder" results in an additional line from 0,49 to 10,50.
A total of four different write modes, with values 0 to 3, are available for
drawing lines. With write mode zero, the original bit pattern "under" the line
is erased and the bit pattern determined by _LN_MAsK is put in its place
(replace mode). In the transparent mode (_WRT_MoD=1), the background, the
old bit pattern, is ORed with the new line pattern so only additional points
are set. In the XOR mode (_wRT_MOD=2), the background and the line
pattern are exclusive-ored. The last mode (_wRT_MOD=3) is the so-called
"inverse transparent mode." As in the transparent mode, it involves an OR
combination of the foreground and background data,
in which the
foreground data, the bit pattern determined by _LN_MASK, are inverted
before the OR operation.
214

<!-- source-page: 222 -->
## Page 222

First Publishing
Atari ST Internals
$4004 HORIZONTAL LINE
This function draws a line from x1,y1 to x2,y1. Drawing a horizontal line is
significantly faster than when a line must be drawn diagonally. Diagonal
lines are also created with this function, in which the line is divided into
multiple horizontal lines segments. The parameters are entered directly into
the required variables.
_X1
=
xl coordinate
_Yl
= yl coordinate
_X2
=
x2 coordinate
_FG BP_1
= Plane
1
(all three modes)
_FG_BP_2
= Plane
2
(640x200,
320x200)
_FG BP
3
= Plane
3
(only 320x200)
_FG BP_4
= Plane
4
(only 320x200)
_WRT_MOD
= Determines the write mode
_patptr
= Pointer to the line pattern to use
_patmsk
= "Mask"
for the
line pattern
The valid values in _wrt_Mop also lie between 0 and 3 for this call. The
contents of the variable patptr is the address at which the desired line
pattern or fill pattern is located. The H-line function is very well-suited to
creating filled surfaces. The variable _patmsk plays an important role in
this. The number of 16-bit values at the address in_patptr
is dependent
on the its value.
If, forexample, patmsk contains the value 5, six 16-bit
values should be located at the address in_patptr
as the line pattern. Ifa
horizontal line with the Y-coordinate value zero is to be drawn, the first bit
pattern is taken as the line pattern. The second word is taken as the pattern
for a line drawn at Y-coordinate 1, and so on. The pattern for a line with
Y-coordinate 6 is again determined by the first value in the bit table. In this
manner, very complex fill patterns can be created with relatively little effort.
215

<!-- source-page: 223 -->
## Page 223

First Publishing
Atari ST Internals
$4005 FILLED RECTANGLE
The opcode $A005 represents an extension, or more exactly a special use,
of opcode $A004. It is used to created filled rectangles. The essential
parameters are the coordinates of the upper left and lower right corners of
the of the rectangle.
_X1
= xl coordinate,
left upper
_Y1
= yl coordinate
_X2
=
x2 coordinate,
right
lower
_Y2
= y2 coordinate
_FG
BP 1
= Plane
1
(all three modes)
_FG BP_2
= Plane
2
(640x200,
320x200)
_FG_ BP_3
= Plane
3
(only 320x200)
_FG_BP_3
= Plane
4
(only 320x200)
_WRT_MOD
= Determines
the write mode
_patptr
= Pointer
to the fill pattern used
_patmsk
= "Mask"
for the
fill pattern
_CLIP
= Clipping flag
_XMN_CLIP
=
X minimum for clipping
_XMX_CLIP
=
X maximum for clipping
_YMN_CLIP
=
Y minimum for clipping
_YMX_ CLIP
=
Y maximum for clipping
We have already explained all of the variables except the "clipping"
variables. What is clipping? Clipping creates extracts or clippings of the
total picture. If the clipping flag is set to one (or any value not equal to
zero), the rectangle, drawn by $A005,
is displayed only in the area defined
by the clipping-area variables. An example may explain this behavior better:
The values 100,100 and 200,200 are specified as the coordinates. The clip
flag is
1 and the clip variables contain the values 150,150 for xmn_cLIp and
YMN_CLIP as well as 300,300 for xmx_cLIp and yMx_ CLIP. The value
SFFFF will be chosen as the fill value for all of the lines. With these values,
the rectangle will have the coordinate 150,150 as the upper left corner and
200,200 as the lower right. The "missing" area is not drawn because of the
clip specifications. Clearing the clip flag draws the rectangle in the originally
desired size.
216

<!-- source-page: 224 -->
## Page 224

First Publishing
Atari ST Internals
$4006 FILLED POLYGON
$A006 is also an extension of $4004. Arbitrary surfaces can be filled with a
pattern with this function. The entire surface is not filled with the call: just
one raster line is filled, a horizontal line with a width of one point. The
result is that there are significantly more options for influencing the fill
pattern.
The necessary variables are:
PTSIN
= Array with
the
XY coordinates
CONTRL(1)
= Number
of coordinate pairs
_Y¥1
=
yl coordinate
_FG_BP_1
= Plane
1
(all three modes)
_FG BP_2
= Plane
2
(640x200,
320x200)
_FG BP_3
= Plane
3
(only 320x200)
_FG_BP_3
= Plane
4
(only 320x200)
_WRT_MOD
= Determines the write mode
_patptr
= Pointer
to the
fill pattern used
_patmsk
= "Mask"
for the fill pattern
_CLIP
= Clipping flag
_XMN CLIP
=
X minimum for clipping
_XMX_ CLIP
= X maximum for clipping
_YMN_CLIP
=
Y minimum for clipping
_YMX_CLIP
=
Y maximum for clipping
Basically, all of the parameters here are to be set exactly as they might be for
a call to $A005. Only the first three coordinates are different. The XY
coordinates are stored in the pTSIN array. It is important you specify the
start coordinate again as the last coordinate as well. In order to fill a triangle,
you must, for example, enter the coordinates (320,100), (120,300),
(520,300), and (320,100). The number of effective coordinate pairs, three
in our example, must be placed in ConTRL (1), the second element of the
array. With
a call to the $A006 function you must also specify the
Y-coordinate of the line to be drawn. Naturally you can fill all Y-coordinates
from 0 to 399 (0 to 199 in the color modes) in order. But it is faster to find
the largest and smallest of the XY values and call the funtion with only these
as the range.
217

<!-- source-page: 225 -->
## Page 225

First Publishing
Atari ST Internal:
$A007 BITBLT
The bit block transfer is used by the text block transfer, $A008, and copy
raster form, $AOQOE. Register A6 must contain a pointer to a parameter table
Unfortunately, the construction of this parameter table could not be
determined definitively. Our attempts led to classic system crashes about
70% of the time. For this reason, we cannot say much about the function.
$A008 TEXTBLT
A character from any desired text font can be printed at any graphic position
with the TEXT BLock Transfer function. In addition, the form of the
character can be changed. The character can be displayed in italics,
boldface, outlines, enlarged, or rotated. These things cannot be achieved
with the "normal" character outputs via the BIOS or GEMDOS. But to do
this, a large number of parameters must be set and controlled. A rather
complicated program must be written in order to output text with this
function. If the additional options are not absolutely necessary,
it is
advisable not to use this function. But please decide for yourself.
Before we produce
a character on the screen, we must first concern
ourselves with the organization of the fonts. We must take an especially
close look at the font header because the font is describe in detail by the
information contained in it.
Basically,
a font consists of four sets of data: font header, font data,
character offset table, and horizontal offset table. The font header contains
general data about the font, such as its name and size, the number of
characters it contains, and various other aspects. This information takes upa
total of 88 bytes. The font data contains the bit pattern of the existing,
displayable characters. These data are organized so as to save as much space
as possible.
In order to be able to better describe the organization, we will imagine a font
with only two characters, such as "A" and "B". These characters are to be
displayed in a 9x9 matrix. The font data are now in memory so that the bit
pattern of the top scan line of the "A" is stored starting at a word boundary.
Since our font is 9 pixels = 9 bits wide, one byte is completely used, but
only the top bit of the following byte. 7 bits must be wasted if the top scan
line of the "B"
is also to begin on
a word boundary. This
is not so,
however, and the first scan line of the "B" starts with bit 6 of the second
218

<!-- source-page: 226 -->
## Page 226

First Publishing
Atari ST Internals
byte of the font data. Only the data of the second and further scan lines
always start on a word boundary. In this manner, almost no bits are wasted
in the font. Only the start of the scan lines of the first character actually
begin on a word boundary; all other scan lines can begin at any bit position.
Because of this space-saving storage, the position of each character within
the font must be calculated. The calculation of the scan-line positions is
possible through the character offset table. This table contains one entry for
each displayable character. For our example, such a table would contain the
entries $0000, $0009, $0012. Through the direction of this table, it is
possible to create true proportional type on the screen since the width of
each character can be calculated. One subtracts the entry of the character to
be displayed from the entry of the next character. The last entry is present so
that the width of the last character can also be determined, although it is not
assigned to a character.
In addition to the character offset table there is the horizontal offset table.
This table is not used by most of the fonts, however. The fonts present in
the ST do not use all the possibilities of this table either. If this table were
present,
it would contain a positive or negative offset value for each
character, in order to shift the character to the right or left during output.
At the end of the description of the font construction are the meanings of the
variables in the font header.
Bytes
O-
1
: Font
identifier.
A number
which describes
the
font.
l=system font
Bytes
2-
3
: Font
size
in
points
(point
is
a
measure
used
in type-setting).
Bytes
4-35
:The name
of the
font
as
an ASCII
string.
Bytes 36-37
:The
lowest
ASCII
value
of
the
displayable
characters.
Bytes 38-39
:The
highest
ASCII
value
of
the
displayable
characters.
Bytes
40-49
:Relative
distances
of
top,
ascent,
half,
descent,
and bottom line
from the base
line.
Bytes
50-51
: Width
of
the broadest character
in
the
font.
Bytes
52-53
: Width
of
the broadest character cell.
The
cell
is
always
at
least
one
pixel
wider
than
the
actual
character
so
that
two
characters
next
to each other
are separated from each other.
Bytes
54-55
: Linker offset.
219

<!-- source-page: 227 -->
## Page 227

First Publishing
Atari ST Internals
—
Bytes
56-57
:Right
offset.
The
two
offset
values
are
only
used
for
displaying
the
font
in
italics
(skewing).
Bytes
58-59
: Thickening.
If
a
character
is
to
be
displayed
in
boldface,
the
value
of
this
variable
is
used.
Bytes
60-61
:Underline.
Contains
the
height
of
the
underline
in pixels.
Bytes
62-63
: Lightening mask.
"Light"
characters
are
founc
on
the
desktop
when
an
option
on
a
pull-dowr
menu
is
not
available.
This
light
grey
character
consists
of
masking
the
bits
with
the
lightening
mask.
Usually
the
value
is
$5555.
Bytes
64-65
:Skewing
mask.
As
before,
only
for
displaying
characters
in italics.
Bytes
66-67
:Flag.
Bit
0
is
set
if
the
font
is
a
system
font.
Bit
1
must
be
set
if
the
horizontal
offset
table
is present.
Bit
2
is
the
so-called byte-swap
flag.
If
it
is
set,
the
bytes
in
memory
are
in
6800
format
(low
byte-high
byte).
A
cleared
swa
flag
signals
that
the
data
is
in
INTEL
format,
reversed
in
memory.
With
this
bit
the
font
from the
IBM version
of
GEM can
be
used
on
th
ST
and vice versa.
|
Bit
3
is
set
if
the width
of
all characters
in
the
font
is equal.
|
Bytes
68-71
: Pointer
to
the
horizontal
offset
table
or
zero.
Bytes
72-75
: Pointer
to the character offset
table.
Bytes
76-79
: Pointer
to
the
font data.
Bytes
80-81
: Form width.
This
variable
contains
the
sum
of
widths
of
all
the
characters.
The
value
represents
the
length
of
the
scan
lines
of
all
of
the
characters
and thereby
the
start
of
the
next
line.
Bytes
82-83
: Form height.
This
variable
contains
the
numbex
of
scan
lines
for this
font.
Bytes
84-87
:Contain
a pointer
to
the
next
font.
220

<!-- source-page: 228 -->
## Page 228

First Publishing
Atari ST Internals
After so much talk, we should now list the parameters which must be noted
lor prepared for the $A008 opcode.
_WRT_MODE
= Write mode
_TEXT_FG
= Text foreground color
_TEXT_BG
= Text background color
_FBASE
= Pointer
to the start
of the font data
_FWIDTH
= Width
of the
font
_SOURCEX
= X-coordinate
of the char
in the
font
_SOURCEY
= Y-coordinate
of the char
in the
font
_DESTX
= X-coordinate
of the char
on the screen
_DESTY
= Y-coordinate
of the char
on the screen
_DELX
= Width
of the character
in pixels
_DELY
= Height
of the character
in pixels
_STYLE
= Bit-wise coded flag for special effects
_LITEMASK
= Bit pattern used for "lightening"
_SKEWMASK
= Bit pattern used for skewing
_WEIGHT
= Factor for character enlargement
_R_OFF
= Right
offset
of
the
char
for skewing
_L OFF
= Left offste
of the char
for skewing
_SCALE
= Flag for scaling
_XACC _DDA
= Accumulator
for scaling
_DDA_INC
= Scaling factor
_T_SCLSTS
= Scaling direction flag
_CHUP
= Character rotation vector
_MONO_STATUS
= Flag for monospaced type
_S8certchp
= Pointer
to buffer
for effects
_serpt2
= Offset scaling buffer
in _scrtchp
The five clip variables are also evaluated.
As you can see, an enormous number of variables are evaluated for the
output of graphic text. Here we can go into only the essential (and those we
explored) variables.
The write mode allows the output of characters in the four known modes,
replace, OR, XOR, and inverse OR. There are 16 other modes available
whose effects are not yet known. The variable Ext
Fc
is in connection
with first four write modes. They form the foreground color used for
display. The background color _TEXxT_BG plays a role only with the 16
additional modes. It is clear that the additional modes are relevant only in
connection with a color screen.
221

<!-- source-page: 229 -->
## Page 229

First Publishing
Atari ST Internal
The variables _FBASE and _FWIDTH are set according to the desired font
You can find the start of the font data from the header of the desired fon
(bytes 76-79 in the header). FWIDTH must be loaded with the contents o
the bytes 80 and 81 of the header.
The parameter _SOURCEX determines which character you output. It shoulc
contain the ASCII value of the desired character.
The parameter _SOURCEY is usually zero because the character is to be
generated from the top to the bottom scan line.
The parameter _DELX can be be calculated as the width of the character ir
which the entry in the character offset table of the desired character ix
subtracted from the next entry. The result is the width of the character ir
pixels. DELY must be loaded with the value of byte 82-83 of the header.
The STYLE is something special. Here you can specify if characters shoulc
be displayed normally or changed. The possible changes are boldface
(thicken, bit 0), shading (lighten, bit 1), italic (bit 2), and outline (bit 4).
The given change is enabled by setting the corresponding bit. Anothe:
change is scaling. The size of a character can be changed through scaling
Unfortunately, characters can only be enlarged on the ST.
If the scaling flag is cleared (zero), the character is displayed in its origina
size. The
_T scusts flag determines if the font is to be reduced o
enlarged. A value other than zero must be placed here for enlarging.
_DDA_INC should contain the value of the enlargement or reduction. Ar
enlargement could be produced only with a value of $FFFF.
Another interesting variable is
_cHup. With the help of this variable,
characters can be rotated on the screen. The angle must be given in the rang:
0 to 360 degrees in tenths of a degree. A restriction must also be made for
this function. Usuable results are obtainable only with rotations by 9C
degrees. The values are $0000 for normal, $0384 for 90-degree rotation.
$0704 (upside-down type), and $0A8C for 270 degrees.
To work with the effects, scrchp must contain a pointer to a buffer in
which TEXTBLT can store temporary values. The exact size of this buffer
is not known, but we always found a buffer of 1K to be sufficient. Another:
buffer must be specified for enlargement (_scrtpt2). An offset is passed a:
a parameter which refers to the start of the _scrtchp buffer. A value of $4
proved to be sufficient here.
222

<!-- source-page: 230 -->
## Page 230

First Publishing
Atari ST Internals
$4009 SHOW MOUSE
Calling this opcode enables the display of the mouse cursor. The cursor
follows the mouse when it is moved. If the mouse cursor is disabled, the
mouse can be used in programs which abandon the user interface GEM.
This option is particularly useful for games.
The parameters required are passed in the INTIN and CONTRL arrays.
CONTRL (1) should be cleared before the call and contrL(3)
set to one.
INTIN (0) has a special significance. The routine for managing the mouse
cursor counts the number of calls to remove and enable the cursor. If the
cursor is disabled twice, two calls must be made to re-enable it before it will
actually appear on the screen. This behavior can be changed by clearing
INTIN(0). With this parameter the cursor is immediately set independent of
the number of previous HIDE CURSOR calls. If the value in IntTIN (0)
is
not equal to zero the actually required number of $A009 calls must be made
in order to make the cursor visible.
$A00A HIDE CURSOR
This functions hides the cursor. If this function is called repeatedly, the
number is recorded by the operating system and determines the number of
calls of SHOW CURSOR before the cursor actually appears.
$400B TRANSFORM MOUSE
Is the arrow unsuited as a mouse cursor for games? Simply make your own
cursor. How would it be if a little car moved across the screen instead of an
arrow? The opcode $A00B gives your fantasy free reign, at least as far as it
concerns the mouse cursor.
The parameters must be passed in the INTIN array. A
total of 34 words are
necessary. The following table gives information about the use and possible
values:
INTIN(3)
Mask color
index,
normally
0
INTIN(4)
Data color index,
normally
1
INTIN(5)
to
INTIN(20)
contain
16 words
of
the cursor mask
INTIN(21)
to
INTIN
(36)
contain
16 words
of cursor data
223

<!-- source-page: 231 -->
## Page 231

First Publishing
Atari ST Internal:
The form of the cursor is determined by the cursor data. Each 1 in the date
creates a point on the screen. If a cursor is placed over a letter or pattern or
the screen, the border between the cursor and the background cannot be
determined. The mask enters at this point. Each set bit in the mask clears the
background at the given location. This permits a light border to be drawn
around the cursor. Take a look at the normal arrow cursor in order to see the
operation of the mask.
$A00C UNDRAW SPRITE
This opcode is related to $A00D, DRAW SPRITE. The ST actually has no
hardware sprites in sense in which sprite is used on something like the
Commodore 64. The ST sprites are organized purely in software. Each
sprite is 16x16 pixels large. One example of an ST sprite is the mouse
cursor. It is created with this function.
In order to clear a previously-drawn sprite, the address of a buffer in which
the background was saved when the sprite was drawn is passed in register
A2. The opcode simply transfers the contents of the background buffer t
the right spot on the screen. The buffer itself must be 64 bytes large for eac
plane. Another 10 bytes are used, independent of the number of planes. Fo
monochrome display, the buffer is a total of 74 bytes long, while in th
320x200 pixel resolution (for planes), it is 4x64+10=266 bytes large.
$A400D DRAW SPRITE
This function draws the desired sprite on the screen. Parameters must be
passed in the DO, D1, AO, and A2 registers.
DO and D1 contain the X and Y-coordinates of the position of the sprite on
the screen, called the hot spot. AO is
a pointer to the so-called sprite
definition block and A2 contains the address of the sprite buffer in which
the backgroud will be saved for erasing the sprite later.
The sprite definition block must have the following construction:
Word
1
:
X
offset
to
hot
spot
Word
2
:
Y offset
to
hot
spot
Word
3
:
Format
flag
0=VDI
format,
1=XOR format
Word
4
:
Background color
(bg)
Word
5
:
Foreground color
(fg)
224

<!-- source-page: 232 -->
## Page 232

First Publishing
Atari ST Internals
Following this are 32 words which contain the sprite pattern. The pattern
must be in memory in the following order:
Word
6
:
Background pattern
of the top
line
Word
7
:
Foreground pattern
of
the
top
line
Word
8
:
Background pattern
of the second line
Word
9
:
Foreground pattern
of the
second line
etc.
The information in the format flag has the following significance:
VDI Format
Result
The background appears
The color
in word
4 appears
The color
in word
5
appears
The color
in word
5 appears
rFPRoOoOYWy
HOF
OW
XOR Format
Result
The background appears
The color
in word
4 appears
The pixel
on the screen
is XORed with
the
fb
bit
1
1
The color
in word
5 appears
rFoOoOW
OoOrPOW
$A00E COPY RASTER FORM
Arbitrary areas of the screen can be copied with the $AQOE opcode. Not
only areas within the screen, but also from the screen into free RAM, and
even more important, from the RAM to the screen. Even complete screen
pages can be copied very quickly with the COPY RASTER opcode. The
name RASTER FORM does express one limitation of the function,
however. Each raster form to be copied must begin on a word boundary and
must be a set of words.
The parameters are quite numerous and are passed in the CONTRL, PTSIN,
and INTIN arrays. In addition, two "memory fom definition" blocks must
be in memory for COPY RASTER. We will start with the MED blocks.
Since a copy operation must always have a source and a destination, one
block describes the source memory range and the second describes the
destination. Each block consists of 10 words. The address of the memory
225

<!-- source-page: 233 -->
## Page 233

First Publishing
Atari ST Internals
described by the block is contained in the first two words. The third word
specifies the height of the form in pixels. Word 4 determines the width of
the form in words. Word 6 should be set to
1 and word 7 specifies the
number of planes of which the form is composed. The remaining words
should be set to zero because they are reserved for future extensions.
3.4.1
An overview of the "line-A" variables
After the initialization $4000, DO and AO contain the address of a variable
area which contains more than 50 line-A variables. The essential variables
have been described along with the various calls, but not the location of the
variables within the variable block. We will present this list shortly. When
naming the variables we have remained with the names used in the official
Atari documentation.
Offset is the value which must be given to access the value register relative.
Variables supplied with a question mark could not be definitively explained.
Offset
Name
Size
Function
0
v_planes
word
Number
of planes
2
v_lin_wr
word
Bytes
per
scan
line
4
CONTRL
long
Pointer
to the CONTRL array
8
INTIN
long
Pointer
to
the
INTIN array
12
PTSIN
long
Pointer
to the PTSIN array
16
INTOUT
long
Pointer
to
the
INTOUT array
20
PTSOUT
long
Pointer
to
the PTSOUT
array
24
_FG BP_1
word
Plane
0 color value
26
_FG BP 2
word
Plane
1
color value
28
_FG BP
2
word
Plane
2 color value
28
_FG BP_2
word
Plane
3 color value
32
_LSTLIN
word
Should be
-1
(S$FFFF)
(?)
34
_LN_MASK
word
Line pattern
for $A003
36
_WRT_MODE
word
Write mode
(0=write mode
l=transparent
2=XOR mode
3=Inverse
trans.)
38
_xXl
word
Xi-coordinate
40
_Yl
word
Yl-coordinate
42
_X2
word
X2-coordinate
44
Y2
word
Y2-coordinate
226

<!-- source-page: 234 -->
## Page 234

First Publishing
Atari ST Internals
46
50
52
54
56
58
60
62
64
66
68
70
72
74
76
78
80
82
_patptr
long
Pointer
to
the
fill pattern
(see
$A004)
_patmsk
word
Fill pattern
"mask"
(see
$A004)
_multifill
word
0O=fill pattern
is
only for
one plane
1=fi11 pattern
is
for multi-
plane
_CLIP
word
0=no clipping
(see
$A005)
not
0=clipping
_XMN_CLIP
word
and
_YMN_ CLIP
word
define upper left corner
of
the visible area
for clipping
_XMX_ CLIP
word
and
_YMX CLIP
word
define lower right corner
of
the visible
area
for clipping
_XACC_DDA
word
Should be
set
to
$8000 before
each
call
to TXTBLT
(?)
_DDA_INC
word
Enlargement/reduction factor
SFFFF
for enlargement,
reduction doesn't
work
(?)
_T_ SCLSTS
word
0Q=reduction
(?)
l=enlargement
_MONO_STATUS
word
1 =not proportional
font
0=proportional
type
or width
of character changed by bold
or italics
_SOURCEX
word
X-coordinate
of
char
in font
_ SOURCEY
word
Y-coord
of
char
in
font
(0)
Note:
SOURCEX
is
the
value
of
the
character
from
the
horizontal
offset
table
(HOT)
and
can
be
calculated witht
he following formula:
SOURCEX
=
HOT-element
(ASCII
value
minus
FIRST
ADE)
The
variable
FIRST
ADE
is
contained
in
bytes
36,37
of
the
font
header
(see
example)
_DESTX
word
X-position
of char
on screen
_DESTY
word
Y-position
of
char
on screen
_DELX
word
Width
of the character
_DELY
word
Height
of
the character
227

<!-- source-page: 235 -->
## Page 235

First Publishing
Atari ST Internals
84
88
90
92
94
96
98
100
102
104
106
108
112
114
116
Note:
DELX
can
be
calculated with
this
formula:
DELX
= SOURCEX+1 minus
SOURCEX
(see
$A008)
DELY
is
the value FORM height
from bytes
82,83
of
the
font header.
_FBASE
long
_FWIDTH
long
_STYLE
word
_LITEMASK
word
_SKEWMASK
word
_WEIGHT
word
_R_OFF
word
_L OFF
word
Note:
Pointer
to
start
of
font
data
Width
of
font
form
Flags
for special effects
(see
SA008)
Mask
for shading
Mask
for italic type
Number
of bits
by which the
character will
be expanded
Offset
for italic type
Offset
for italic type
The above
five variables
should be
loaded with
the corresponding values
from the
font header.
_ SCALE
word
_CHUP
word
_TEXT_FG
word
_scrtchp
long
_scrpt2
word
_TEXT_BG
word
_COPYTRAN
word
0=no
scaling
l=scaling
(enlarge/reduce)
Angle
for character rotation
O=normal
char representation
$384=rotated
90
degrees
$708=rotated
180
degrees
SA8C=rotated 270 degrees
Foreground color
for text
display
Address
of buffer required
for creating special text
effects
Offset
of
the enlargement
buffer
in
the
scrtchp buffer |
Background color
for text
rep
(?)
228

<!-- source-page: 236 -->
## Page 236

First Publishing
Atari ST Internals
3.4.2
Examples for using the line-A opcodes
In order to ease your first experiments with the line-A opcodes, we have
given a few examples which can serve as a starting-point for you. In the
first example, a point is set on the screen with $A001, and then the color of
the point is determined with $A002.
He
Fe te te te
a IK
KK RIK ROK KIO KIO RRR II
OR IO
IO
IO
koe
*
Demo
of the
$A000,S$A001
and
$A002
functions
*
*
rbr 09/28/85
FOR TI RI
IK
KR KKK
KK KK KKK IK KK II KK
IK
KIO CK KK tk
intin
equ
8
ptsin
equ
12
init
equ
$a000
setpix
equ
$a001
getpix
equ
$a002
start:
.dc.w
init
*
call
S$A000
move ,1
intin(a0),a3
*
address
of
INTIN-arrays
move ,1
ptsin(a0),a4
*
address
of PTSIN-arrays
move
#300, (a4)
*
X coordinate
move
#100,2 (a4)
*
Y coordinate
move
#1, (a3)
*
color
set,
pixel
set
*
0 erase pixel
.dc.w
setpix
* pixel
set
move
#300, (a4)
*
X coordinate
move
#100, 2 (a4)
*
y coordinate
.dc.w
getpix
*
get
color value
dO contains prersent
color value
Only color values zero and one make sense for
a monochrome monitor.
Other values can be entered when working in one of the color modes,
however.
229

<!-- source-page: 237 -->
## Page 237

First Publishing
Atari ST Internals
The next example shows how a triangle can be drawn on the screen with the
function FILLED POLYGON.
Rk
kok
kK
RK RK RR KR KK RK RR KK RK RK RK Kk
Ok
KK
*
aQ006
- filled pologyn
KARKKKAKKKKKEKKKKKKK
KKK KKK
RK
kk KKK KA K KR RK
KR KKK
contrl
equ
4
ptsin
equ
12
fg bpl
equ
24
fg_bp2
equ
26
fg_bp3
equ
28
fg_bp4
equ
30
wrt_mod
equ
36
yl
equ
40
patptr
equ
46
patmsk
equ
50
multifill
equ
52
clip
equ
54
xmn_clip
equ
56
ymn_ clip
equ
58
xmx_Clip
equ
60
ymx_ clip
equ
62
init
equ
$a000
polygon
equ
$a006
.dc.w
init
*
address
of variable block
*
from
AO
move .w
#1,f9_bp1 (a0)
*set
colors
for monochrome
clr.w
fg_bp2 (a0)
clr.w
fg_bp3 (a0)
clr.w
fg_bp4 (a0)
move .W
#2,wrt_mod(a0}
*
replace mode
230

<!-- source-page: 238 -->
## Page 238

First Publishing
Atari ST Internals
loop
loopi
fill:
tab:
move.1
move .w
clr.w
clr.w
move.1l
addq.1
move .W
move.l
move.1
move.w
move .w
dbra
move .w
move .wW
move .1
move.1
addq.w
cmp .w
bne
move .w
trap
addgq.1
rts
dc.
de.
de,
de.
<2
ze
=
de.
de.
de.
EEE
#fi11,patptr
(ad)
#4,patmsk (a0)
multifill (ao)
clip (a0)
contrl(a0),a6
#2,a6
#3, (a6)
ptsin(a0),a6
#tab,aS
#8,a3
(a5)
+, (a6) +
d3,loop
#100,d3
d3,y1{a0)
a0,~(sp)
polygon
(sp) +,a0
#1,d3
#301,da3
loopl
#1,-(sp)
#1
#2,sp
%1100110011001100
%0110110110110110
%0011001100110011
%1001100110011001
320,100
120, 320
520,300
320,100
231
e
e+
&
pointer
of
the
fill pattern
four
fill patterns
for monochrome
no clipping
adddress
of
CONTRL array
from
A6
A6
> CONTRL(1)
the
XY pair
in
PTSIN
address
PTSIN
array
from
A6
table
of coordinates
recieve
8 coordinates
first
scanline
from
Yl
restore
address
variable
block
fill
scanline,
AO destroyed
AO
restored
calculate
next
sacanline
last
scan
line?
no,
next
scanline
Code CONIN wait
for keypress
Call GEMDOS
stack correction
all done

<!-- source-page: 239 -->
## Page 239

First Publishing
Atari ST Internals
The next example shows how the mouse form can be manipulated and how
the mouse can be enabled.
The example waits for a key press before
returning.
ite
eee
ee eee
eee Ce
SSeS SSCS CSSSCC SSS Se ee eS ee
*
*
*
show mouse
- transform mouse
*
*
* KOK a
ke
kkk
kk RO
OK CK
KK
RR
KR IO
RO Kk kk kk
OK
eK
intin
equ
8
init_a
equ
$a000
show_mouse
equ
$a009
transmouse
equ
$a00b
start:
.dc.w
init_a
*
address
INIT
from
A5
move.1
intin(a0),a5
move
#0,6(a5)
*
INTIN
(3)
= mask
color value
move
#1,8 (a5)
*
INTIN
(4)
= data
color value
add.1l
#10,a5
*
a5
>
INTIN
(5)
lea
maus, a4
*
data
for
new cursor
move
#16,d0
*
32 words
=
16
longs
loop:
move.1
(a4) +, (aS)+
*
transfer
INTIN array
dbra
a0, loop
.dc.w
transmouse
*
and
set
form
-dc.w
init_a
move.1
intin(a0Q),a0
clr.w
(a0)
*
Number
Hide Cursor
-ignore
call
-dc.w
show_mouse
*
now the
new cursor
232

<!-- source-page: 240 -->
## Page 240

First Publishing
Atari ST Internals
maus:
maske:
daten:
move .w
trap
addq.1
rts
.
.
.
een tun zteecenezeuzez
.
Eetenece
ee zcezee ee
#1,-~(sp)
%0000000110000000
%0000011111100000
%0001111111111000
%02111111111111110
%1111111111111111
%1111001111001111
%$1111001111001111
%1111001111001111
$0000001111000000
%0000001111000000
%0000001111000000
%0000001111000000
%0000001111000000
%0000001111000000
%0000000000000000
%0000000000000000
%0000000000000000
%0000000110000000
%0000011001100000
%0110000110000110
%0110000110000110
%0000000110000000
%0000000110000000
%0000000110000000
%0000000110000000
%0000000110000000
%0000000110000000
%0000000110000000
%0000000000000000
%0000000000000000
233
*
Code
CONIN wait
for keypress
#1
* Call GEMDOS
#2,8p
*
stack correction

<!-- source-page: 241 -->
## Page 241

First Publishing
Atari ST Internals
3.5 The Exception Vectors
The first 1024 bytes in the address range of the 68000 processor are
reserved for the exception vectors. Here the addresses are stored for the
routines which lead to exception handling under certain circumstances.
A condition which leads to an exception can come either from the processor
itself or from the peripheral components and controls units connected to it.
The interrupts, described in the next section, belong to the class of external
events. In addition, a so-called bus error can be created externally.
A bus error can be created by many circumstances. For one, certain memory
areas can be protected from unauthorized access by it. As you may already
know, the 68000 can run in one of two operating modes. The operating
system is driven at the first level, the supervisor mode. The user mode is
intended for user programs. In order that a user program not be able to
access important system variables as well as the system components in an
uncontrolled fashion, such an access in the user mode leads to a bus error.
If such an error occurs, the processor stops execution of the instruction,
saves the program counter and status register on the stack, and branches to a
routine, the address of which it fetches from the lowest 1024 bytes of
memory. In the case of the bus error, the address is at memory location 8
(one long word). What happens in this routine?
First the vector number of the interrupt is determined. In the case of a bus
error, this is 2. Mushroom clouds are then displayed on the screen. The
user can determine the vector number by counting the number of mushroom
pictures. Execution then returns to the GEM desktop.
The following table contains all of the exception vectors.
234

<!-- source-page: 242 -->
## Page 242

First Publishing
Atari ST Internals
Vector number
Address
Exception vector meaning
0
$000
Stack pointer after reset
1
$004
Program counter after
reset
2
$008
Bus error
3
$00c
Address error
4
$010
Illegal instruction
5
$014
Division by
zero
6
$018
CHK instruction
7
solic
TRAPV instruction
8
$020
Priviledge violation
9
$024
Trace
10
$028
Line
A emulator
11
$02C
Line
F emulator
12-14
$030-$038
reserved
15
$03C
Uninitialized interrupt
16-23
$040-S$05C
reserved
24
$060
Spurious interrupt
25
$064
Level
1
interrupt
26
$068
Level
2 interrupt
27
$06C
Level
3 interrupt
28
$070
Level
4
interrupt
29
$074
Level
5
interrupt
30
$078
Level
6 interrupt
31
$07C
Level
7 interrupt
32
$080
TRAP
#0
instruction
33
$084
TRAP
#1
instruction
34
$088
TRAP
#2
instruction
35
$08c
TRAP
#3
instruction
36
$090
TRAP
#4
instruction
37
$094
TRAP
#5 instruction
38
$098
TRAP
#6 instruction
39
$09C
TRAP
#7
instruction
40
$OA0
TRAP
#8
instruction
41
$0A4
TRAP
#9
instruction
42
SOA8
TRAP
#10
instruction
43
SOAC
TRAP
#11
instruction
44
S0BO
TRAP
#12 instruction
45
$OB4
TRAP
#13 instruction
46
S0B8
TRAP
#14
instruction
47
SOBC
TRAP
#15
instruction
48-63
SOCO-SOFC
reserved
64~-255
$100-$3FC
User interrupt
vectors
235

<!-- source-page: 243 -->
## Page 243

First Publishing
Atari ST Internals
The following vectors are used on the ST:
Line
A emulator
SEB9IA
Level
2 interrupt
$543C
Level
4
interrupt
$5452
TRAP
#1 GEMDOS
$965E
TRAP
#2
GEM
$2A338
TRAP
#13 BIOS
$556C
TRAP
#14
XBIOS
$5566
The vector for division by zero points to rte and returns directly to the
interrupted program. Vectors 64-79 are reserved for the MFP 68901
interrupts. All other vectors point to $5838 which outputs the vector number
and ends the program as described for the bus error.
All of the unused vectors can be used for your own purposes, such as the
line F emulator or the 12 unused traps.
3.5.1 The interrupt structure of the ST
The interrupt possibilities which the 6800 microprocessor offers are put to
good use in the ST. As you may have already gathered from the hardware
description of the processor, the processor has seven interrupt levels with
different priorities. The interrupt mask in the system byte of the status
register determines which levels can generate an interrupt. An interrupt can
only be generated by a level higher than the current contents of the mask in
the status register. A interrupt of a certain priority is communicated to the
processor by the three interrupt priority level inputs. The following
assignment results:
Level
IPL
2
1
0
7
(NMI)
0
0
Q
6
0
Oo
1
5
0
1
0
4
Oo
1
ii
3
1
0
0
2
1
01
1
1
1
0
0
111
236

<!-- source-page: 244 -->
## Page 244

First Publishing
Atari ST Internals
If all three lines are
1 (interrupt level 0), no interrupt is present. Interrupt
level 7 is the NMI (non-maskable interrupt), which is executed even if the
interrupt mask in the status register contains seven. Which interrupt is
assigned which vector (that is, the address of the routine which will process
the interrupt) depends on the peripheral component which generates the
interrupt. For auto-vectors, the processor itself derives the interrupt number
from the interrupt level. The following table is used in this process:
Level
Vector number
Vector
address
IPL
1
25
$64
IPL
2
26
$68
IPL
3
27
$6C
IPL
4
28
$70
IPL
5
29
$74
IPL
6
30
$78
IPL
7
31
$7C
Only lines IPL
1 and IPL
2 are used on the Atari ST; Line IPL is
permanently set to a 1 level so that only levels 2, 4 and 6 are available. The
results in the following assignment:
IPL
2
HBL,
horizontal blank,
line
return
IPL
4
VBL,
vertical blank,
picture
return
IPL
6
MFP
68901
The HPL interrupt is generated on each line return from the video section. It
is generated every 50 to 64 ps depending on the monitor connected
(monochrome or color). It occurs very often and is normally not permitted
by an interrupt mask of three. The standard HBL routine therefore only has
the task of setting the interrupt mask to three if it is zero and allows the HBL
interrupt so that no more HBL interrupts will occur. One use of the HBL
interrupt could be for special screen effects. With the help of this routine,
you know exactly which line of the screen has just been displayed. Of much
greater importance, however, is the VBL interrupt, which is generated on
each picture return. This occurs 50, 60, or 70 times per second depending
on the monitor.
The vertical blank interrupt (VBL) routine accomplishes a whole set of a
tasks which must be periodically executed or which concern the screen
display. When entering the routine, the frame counter £rclock ($466) is
first incremented. Next,
a test is made to see if the VBL interrupt is
software-disabled. This
is the case if
vbl sem
($452) (vertical blank
semaphor) is zero or negative. In this case the routine is exited immediately
237

<!-- source-page: 245 -->
## Page 245

First Publishing
Atari ST Internals
and execution returns to the interrupted program. Otherwise, all of the
registers are saved on the stack and the counter vbclock ($462), which
counts the executed VBL routines, is incremented. Next, a check is made to
see if a different monitor has been connected in the meantime. If a change
was made from a monochrome to color monitor, the video shifter is
reprogrammed accordingly. This is necessary because the high screen
frequency of 70 Hz of the monochrome monitor could damage a color
monitor. The routine to flash the cursor is called next. If you load a new
color palette via the appropriate BIOS functions or want to change the
screen address, this happens here in the VBL routine. Since nothing is
displayed at this time, a change can be made here without disturbing
anything else. If colorpt
r ($45A) is not equal to zero, it is interpreted as
a pointer to a new color palette, and this is loaded into the video shifter. The
pointer is then cleared again. If screenptr is set, this value is used as the
new base address of the screen. This takes care of the screen specific
portions.
Now the floppy VBL routine is called, which with help the of the write
protect status, determines if a diskette was changed. An additional task of
this routine is to deselect the drives after the disk controller has turned the
drive motor off.
Now comes the most interesting part for the programmer, the processing of
the VBL queue. There is a way to tell the operating system to execute your
own routines within the VBL interrupt. The maximum number of routines
possible is in nvb1s ($454). This value is normally initialized to 8, but it
can be increased if required. Address vb lqueue ($456) contains a pointer
to a vector array which contains the (8) addresses of the VBL routines. Each
address is tested within the VBL routine and the corresponding routine
executed if the address is not zero.
If you want to install your own VBL routine, check the 8 entries until you
find one which contains a zero. At this address you can write a pointer to
your routine which from now on will be executed in every VBL interrupt.
In all 8 entries are already occupied, you can copy the entries into a free area
of memory, append the address of your routine, and redirect
vb queue to
point to the new vector array. Naturally, you must not forget to increment
vb1s, the number of routines, correspondingly. Your routine may change
all registers with the exception of the USP.
As soon as the VBL routine is done, the dmpf 1g ($4EE) is checked. If this
memory location is zero, a hardcopy of the screen is outputted. The flag is
set in the keyboard interrupt routine if the keys ALT and HELP are pressed
238

<!-- source-page: 246 -->
## Page 246

First Publishing
Atari ST Internals
at the same time. Finally, the register contents are restored, vblsem is
released and execution returns to the interrupted routine.
The MFP 68901 occupies interrupt level six in our previous table. This
component is in the position to create interrupt vectors on its own. These are
referred to non-auto vectors in contrast to the auto vectors used above,
because the processor does not generate the vector itself. In the Atari ST,
the MFP 68901 works as the interrupt controller. It manages the interrupt
requests of all peripheral components including its own.
The MFP can manage sixteen interrupts which are prioritized in reference to
each other, similar to the seven levels of the processor. All MFP interrupts
appear on level 6 to the 68000, therefore prioritized higher than HBL and
VBL interrupts. The following table contains the assignments within the
MFP.
Level
Assignment
15
Monochrome monitor detect
14
RS-232
ring indicator
13
System clock timer
A
12
RS-232
receive buffer
full
11
RS-232
receive error
10
RS-232 transmit buffer empty
9
RS-232 transmit error
8
Line
return counter,
timer
B
7
Floppy controller
and DMA
6
Keyboard and MIDI ACIAs
5
Timer
C
4
RS-232
baud
rate generator,
timer
D
3
unused
2
RS~232
CTS
1
RS~232 DCD
0
Centronics busy
Not all of these possible interrupt sources are enabled, however. Some
signals are processed through polling. The following is a description of the
interrupts which are used by the operating system.
239

<!-- source-page: 247 -->
## Page 247

First Publishing
Atari ST Internals
Level
2, RS-232 CTS, Address $73C0
This interrupt is generated every time the RS-232 interface is informed via
the CTS line that a connected receiver is ready to receive additional data.
The routine then sends the next character from the RS-232 transmit buffer.
Level
5, Timer C, Address $7C5C
This timer runs at 200 Hz. The 200 Hz counter at $4BA is first incremented
in the interrupt routine. The next actions are performed only every fourth
call to the interrupt routine, that is, only every 20ms (50 Hz). First a routine
is called which handles the sound processing. Another task of this interrupt
is the keyboard repeat when a key is pressed and initial repeat. Finally, the
evt timer routine of GEM is called, which is accessed via vector $400.
Level
6, Keyboard and Midi, Address $752A
Two peripheral components are connected to this interrupt level of the MFP,
the two ACIAs which receive data from the keyboard and the MIDI
interface. In order to decide which of the two components has requested an
interrupt, the interrupt request bits in the status registers of the ACIAs are
tested and the received byte is fetched if required. If it comes from the
keyboard, the scan code is converted to the ASCII code by means of the
keyboard table and written into the receive buffer, which happens
immediately for MIDI data. Mouse and joystick data also come from the
keyboard ACIA and are also prepared accordingly.
Level
9, RS-232 transmit error, Address $7426
If an error occurs while sending RS-232 data, this interrupt routine is
activated. Here the transmitter status register is read and the status is saved
in the RS-232 parameter block.
Level
10, RS-232 transmit buffer empty, Address $7374
Each time the MFP has completely outputted a data byte via the RS-232
interface, it generates this interrupt. It is then ready to send the next byte. If
data is still in the transmit buffer, the next byte is written into the transmit
register, which can now be shifted out according to the selected baud rate.
240

<!-- source-page: 248 -->
## Page 248

First Publishing
Atari ST Internals
Level
11, RS-232 receive error, Address $7408
If an error occurs when receiving RS-232 data, this interrupt routine is
activated. This may involve a parity error or an overflow. The routine only
clears the receiver status register and then returns.
Level
12, RS-232 receive buffer
full, Address $72C0
If the MFP has received a complete byte, this interrupt occurs. Here the
character can be fetched and written into the receive buffer (if there is still
room). This routine takes into account the active handshake mode (sending
XON/XOFF or RTS/CTS).
The other interrupt possibilities of the MFP are not used, but they can be
used for your own routines. For example, interrupt level 0, Centronics
strobe, can be used for buffered printer output.
241

<!-- source-page: 249 -->
## Page 249

First Publishing
Atari ST Internals
3.6 The Atari ST VT52 Emulator
There are two options for text output on the ST. You can work with the
GEMDOS functions by means of TRAP
#1 or a direct BIOS call with
TRAP
#13. The other possibility consists of using the VDI functions.
You have special possibilities for screen control with both variants. We will
first take a look at output using the normal DOS or BIOS calls. Here a
terminal of type VT52, which offers a wide variety of control functions, is
emulated for screen output. These control characters are prefixed with a
special character, the escape code. Escape, also shortened to ESC, has
ASCH code 27. Following the escape code is a letter which determines the
function, as well as additional parameters if required. The following list
contains all of the control codes and their significance.
ESC A Cursor up
This function moves the cursor up one line. If the cursor was already
on the top line, nothing happens.
ESC B Cursor down
This ESC sequence positions the cursor one line down. If the cursor
is already on the bottom line, nothing happens.
ESC C Cursor right
This sequence moves the cursor one column to the right.
ESC D Cursor left
Moves the cursor one position to the left. This function is identical to
the control code backspace (BS, ASCII code 8). If the cursor is
already in the first column, nothing happens.
ESC E Clear Home
This control sequence clears the entire screen and positions the cursor
in the upper left corner of the screen (home position).
242

<!-- source-page: 250 -->
## Page 250

First Publishing
Atari ST Internals
ESC H Cursor home
With this function you can place the cursor in the upper left corner of
the screen without erasing the contents of the screen.
ESC
I Cursor up
This sequence moves the cursor one line towards the top. In contrast
to ESC A, however, if the cursor is already in the top line, a blank
line is inserted and the remainder of the screen is scrolled down a line
correspondingly. The column position of the cursor remains
unchanged.
ESC J Clear below cursor
By means of this function, the rest of the screen below the current
cursor position is cleared. The cursor position itself is not changed.
ESC K Clear remainder of line
This ESC sequence clears the rest of the line in which the cursor is
found. The cursor position itself is also cleared, but the position is
not changed.
ESC L
Insert line
This makes it possible to insert a blank line at the current cursor
position. The remainder of the screen is shifted down; the lowest line
is then lost. The cursor is placed at the start of the new line after the
insertion.
ESC M Delete line
This function clears the line in which the cursor is found and moves
the rest of the screen up one line. The lowest screen line then
becomes free. After the deletion, the cursor is located in the first
column of the line moved up to take the place of the old one.
243

<!-- source-page: 251 -->
## Page 251

First Publishing
Atari ST Internals
ESC Y
Position cursor
This
is the most important function.
It allows the cursor to be
positioned at any place on the screen. The function needs the cursor
line and column as parameters, which are expected in this order with
an offset of 32. If you want to set the cursor to line 7, column 40,
you must output the sequence ESC Y CHR$(32+7) CHR$(32+40).
Lines and columns are counter starting at zero; for an 80x25 screen
the lines are numbered from 0 to 24 and the columns from 0 to 79.
The additional ESC sequences of the VT52 terminal start with a lower case
letter.
ESC b
Select character color
With this function you can select the character color for further
output. With a monochrome monitor you have choice between just
0=white and 1=black. For color display you can select from 4 or 16
colors depending on the mode. Only the lowest four bits of the
parameters are evaluated (mod 16). You can use the digit "1" for the
color 1 as well as the letters "A" or "a" in addition to binary one.
ESC
c Select background color
This function serves to select the background color in a similar
manner. If you choose the same color for character and background,
you will, of course, not be able to see text output any more.
ESC d Clear screen to cursor position
This sequence causes the screen to be erased starting at the top and
going to the current position of the cursor, inclusive. The position of
the cursor is not changed.
ESC
e Enable cursor
Through this escape sequence the cursor becomes visible. The cursor
can, for example, be enabled when waiting for input from the user.
ESC
f Disable cursor
Turns the cursor off again.
244

<!-- source-page: 252 -->
## Page 252

First Publishing
Atari ST Internals
ESC
j Save cursor position
ESC
If you want to save the current position of the cursor, you can use
this sequence to do so.
k Set cursor to the saved position
This is the counterpart of the above function. It sets the cursor to the
position which was previously saved with ESC j.
ESC
1 Clear line
Clears the line in which the cursor is located. The remaining lines
remain unaffected. After the line is cleared, the cursor is located in the
first column of the line.
ESC o Clear from start
ESC
ESC
ESC
ESC
This clears the current cursor line from the start to the cursor position,
inclusive. The position of the cursor remains unchanged.
p Reverse on
The reverse (inverted) output is enabled with this sequence. For all
further output, the character and background colors are exchanged.
With
a monochrome monitor you get white type on
a black
background.
q Reverse off
This sequence serves to re-enable the normal character display mode.
v Automatic overflow on
After executing this sequence, an attempted output beyond the end of
line will automatically start a new line.
w Automatic overflow off
This deactivates the above sequence. An attempt to write beyond the
line will result in all following characters being written in the last
column.
245

<!-- source-page: 253 -->
## Page 253

First Publishing
Atari ST Internals
Similar functions are available to you under VDI. The VDI escape functions
(opcode 5) serve this purpose. The appropriate screen function is selected
by choosing the proper function number. Note, however, that under VDI
the line and column numbering does not begin with zero but with one.
Under VDI there is also a function which outputs a string at specific screen
coordinates. If necessary, you can use the ESC functions of the VT52
emulation in addition.
The output of "unprintable" control characters
The three system fonts of the ST have also been supplied with characters for
the ASCII codes zero to 31, which are normally interpreted as control
codes. On the ST, only codes 7 (BEL), 8 (BS backspace), 9 (TAB), as well
as
10,
11, and 12 (LF linefeed, VT vertical tab, and FF form feed all
generate a linefeed) plus 13 (CR carriage return) have effect, in addition to
ESC. The remaining codes have no effect. How does one access the
characters below 32?
To do this, an additional device number is provided in the BIOS function 3
"conout". Normally number 2 "con" serves for output to the screen. If one
selects number 5, however, all the codes from, 0 to 255 are outputted as
printable characters, control codes are no longer taken into account.
In the appendix you find the three ST system fonts pictured.
246
|

<!-- source-page: 254 -->
## Page 254

First Publishing
Atari ST Internals
3.7 The ST System Variables
The ST uses a set of system variables whose significance and addresses will
not change in future versions of the operating system. If you use other
variables, such as those from the BIOS listing which are not listed here, you
should always remember that these could have a different meaning in a new
version of the operating system. The system variables are in the lower RAM
area directly above the 68000 exception vectors, at address $400 to 1024.
The address range from 0 to $800 (2048) can be accessed only in the
supervisor mode. An access in the user mode of the 68000 leads to a bus
error.
In the following listing we will use the original names from Atari. In
addition to the address of the given variable, typical contents and the
significance will be described.
Address
length name
Sample contents
$400
L
etv_timer
$F526
This is the event timer vector of the GEM. It takes care of the periodic
tasks of GEM.
$404
L
etv_critic
$5562
Critical error handler. Under GEM this pointer points to $2A156.
There an attempt is made to correct disk errors, such as if a another
disk is requested in a single-drive system.
$408
UL
etv_term
$5328
This is the GEM vector for ending a program.
$40C
5L
etv xtra
Here is space for 5 additional GEM vectors, which at the time are not
yet used.
247

<!-- source-page: 255 -->
## Page 255

First Publishing
Atari ST Internals
$420
L
memvalid
$752019F3
If the memory location contains the given value, the configuration of
the memory controller is valid.
$424
WwW
memctr1
$0400
This is a copy of the configuration value in the memory controller.
The value given applies for
a 512K machine.
$426
L
resvalid
$31415926
If the given value is located here, a jump is made at a reset via the
reset vector in address $42A.
$42A
2
resvector
$FC0008
See above.
$42E
L
phystop
$80000
This is the physical end of the RAM memory; $80000 for a 512K
machine.
$432
L
_membot
$3B900
The user memory begins here (TPA, transient program area).
$436
L
_memt op
$78000
This is the upper end of the user memory.
$43A
L
memval2
$237698AA
This "magic" value together with "memvalid" declares the memory
configuration valid.
$43E
Ww
flock
0
If this variable contains a value other than zero, a disk access is in
progress and the VBL disk routine is disabled.
248

<!-- source-page: 256 -->
## Page 256

First Publishing
Atari ST Internals
$440
Ww
seekrate
3
The seek rate (the time it takes to move the read/write head to the next
track) is determined according to the following table:
Seek
rate
Time
0
6
ms
1
12
ms
2
2
ms
3
3
ms
$442
Ww
_timer ms
$14,
20
ms
The time span between two timer calls, 20 ms corresponds to 50 Hz.
$444
WwW
_fverify
SFF
If this memory location contains a value other than zero, a verify is
performed after every disk write access.
| $446
W
_bootdev
0
Contains the device number of the drive from the operating system
was loaded.
|
$448
Ww
palmode
0
If this variable contains a value other than zero, the system is in the
PAL mode (50 Hz); if the value is zero, it means the NTSC mode.
S44A
Ww
defshiftmod
0
If the Atari is switched from monochrome to color, it gets the new
resolution from here (O=low,
1 medium resolution).
$44c
WwW
sshiftmod
$200
Here is a copy of the register contents for the screen resolution.
0
320x200,
low resolution
1
640x200,
medium resolution
2
640x400,
high
resolution
249

<!-- source-page: 257 -->
## Page 257

First Publishing
Atari ST Internals
$44E
L
_v_bas_ad
$78000
This variable contains a pointer to the video RAM (logical screen
base). The screen address must always begin on
a 256 byte
boundary.
$452
WwW
vblsem
1
If this variable is zero, the vertical blank routine is not executed.
$454
WwW
nvbls
8
Number of vertical blank routines.
$456
L
_vblqueue
$4CE
Pointer to a list of nvb1s
routines which will be executed during the
VBL.
$45A
UL
colorptr
0
If this value is not zero, it is interpreted as a pointer to a color palette
which will be loaded at the next VBL.
$45E
L
screenpt
0
This is a pointer to the start of the video RAM, which will be set
during the next VBL (zero if no new address is to be set).
$462
L
_vbelock
©
$2D26A
Counter for the number of VBL interrupts.
$466
L
_frclock
$2D267
|
Number of VBL routines executed (not disabled by vblsem).
$46A
iL
hdv_init
SSAE8
Vector for hard disk initialization.
250

<!-- source-page: 258 -->
## Page 258

‘irst Publishing
Atari ST Internals
46E
6
swv_vec
$501E
Vector for changing the screen resolution. A branch is made via this
vector with the screen resolution is changed (default is reset).
3472
OL
hdv_bpb
$5BG6E
Vector to fetch the BIOS parameter block for a hard disk.
$476
hdv_rw
$5D88
Read/write routine for a hard disk.
S47A
L
hdv_boot
$60B2
Vector to a routine to reboot the hard disk.
S47E
LL
hdv_mediach
$5D1E
Media change routine for hard disk.
482
W
_comload
0
If this variable is set to a value other than zero by the boot program,
an attempt will be made to load a program called "COMMAND.PRG"
after the operating system is loaded.
$484
B
conterm
6
Attribute vector for console output
Bit
Meaning
0
Key click on/off
1
Key repeat on/off
2
Tone after CTRL
G on/off
3
“kbshift™
is retured
in bits 24-31
for the
BIOS
function "conin"
$485
B
unused,
reserved
$486
L
trpl4éret
0
Return address for TRAP #14 call.
251

<!-- source-page: 259 -->
## Page 259

First Publishing
Atari ST Internal:
$48A
I
criticret
0
Return address of the critical error handler
$48—
4L
themd
0
Memory descriptor, filled out by the BIOS function get mpb.
$49E
2W
___md
0
Space for additional memory descriptors.
$422
L
savptr
$SCE
Pointer to a save area for the processor registers after a BIOS call.
$4A6
W
_nflops
2
Number of connected floppy disk drives.
$4a8
L
con_state
$8AEE
Vector for screen output; set by ESC functions to the appropriat
routine, for example.
$4aAac
w
save_row
0
Temporary storage for cursor line when positioning the cursor with
ESC Y.
$4AE
L
sav_context
0
Pointer to a temporary areas for exception handling.
$4B2
2L
_bufl
$4F9E,
S4FB2
Pointer to two buffer list headers of GEMDOS. The first header
i
responsible for data sectors, the second for the FAT (file allocatio
table) and the directory. Each buffer control block (BCB)
ij
constructed as follows:
252

<!-- source-page: 260 -->
## Page 260

First Publishing
Atari ST Internals
long
BCB
S4F8A,
pointer
to next BCB
int
drive
-1l,
drive number
or
-1
int
type
2
buffer type
int
rec
$41¢c
record number
in
this buffer
int
dirty
0
dirty flag
(buffer changed)
long
DMD
$2854
pointer to drive media descriptor
long
buffer $4292
pointer
to
the buffer itself
$4BA
L
_hz 200
$71280
Counter for 200 Hz system clock
$4BC
4B
the_env
0
|
Default environment string, four zero bytes.
$4c2.
iL
_drvbits
3
32-bit vector for connected drives. Bit 0 stands for drive A, bit 1 for
drive B, and so on.
$4c6
L
_dskbufp
$12BC
Pointer to a 1024-byte disk buffer. The buffer is used for GSX
graphic operations and should not be used by interrupt routines.
$4CA
L
_autopath
0
Pointer to autoexecute path.
$4CE
8L
_vbl_ list
$15398,0,0...
List of the standard VBL routines.
S4EE
W
_dumpflg
SFFFF
This flag is incremented by one when the ALT and HELP keys are
pressed simultaneously. A value of one generates a hardcopy of the
screen on the printer. A hardcopy can be interrupted by pressing ALT
HELP again.
253

<!-- source-page: 261 -->
## Page 261

First Publishing
Atari ST Internal
$4F0
wW
_prtabt
0
Printer abort flag due to time-out.
$4F2
_sysbase
$5000
Pointer to start of the operating system.
$4F6
L
_shell_p
0
Global shell information.
S$4FA
OL
end_os
$3B900
Pointer to the end of the operating system in RAM, start of the TPA.
$4FE
IL
exec_os
$1EB00
Pointer to the start of the AES. Normally branched to after th
initialization of the BIOS.
254

<!-- source-page: 262 -->
## Page 262

First Publishing
Atari ST Internals
3.8 The 68000 Instruction Set
(f you are already familiar with the machine language of some 8-bit
srocessor: Forget everything you know. If you do, it will make it easier to
inderstand the following material!
The 68000 processor
is fundamentally different in construction and
architecture from previous processors (including the 8086!). The essential
difference does not lie in the fact that the standard processing width is 16
and not
8
bits (which
is sometimes
a drawback and can lead
to
programming errors), but in the fact that, with certain exceptions, the
internal registers are not assigned to a specific purpose, but can be viewed
as general-purpose registers, with which almost anything is possible.
In eariler processors, the accumulator was always the destination for
arithmetic operations, but it is completely absent in the 68000. There are
eight data registers (DO-D7) with a width of 32 bits, and as a general rule, at
least one of these is involved in an operation. There are also eight address
registers (AQ-A7), each with 32 bits, which are usually used for generating
complex addresses. Register A7 has a set assignment--it serves as the stack
pointer. It is also present twice, once as the user stack pointer (USP) and
once as the supervisor stack pointer (SSP). The distinction is made because
there are also two operating modes, namely the user mode and the
supervisor mode.
These two are not only different in that they use different stack pointers, but
in that certain instructions are not legal in the user mode. These are the
so-called priviledged instructions (see also instruction description), with
whose help an unwary programmer can easily "crash" the system rather
spectacularly. This is why these instructions create an exception in the user
mode. An exception, by the way, is the only way to get from the user mode
to the supervisor mode.
In addition there is the status register, the upper half of which is designated
as the system byte because it contains such things as the interrupt mask,
things which do not concern the "normal" user, making access to this byte
also one of the priviledged instructions. The lower byte, the user byte,
contains the flags which are set or cleared based on the result of operations,
such as the carry flag, zero flag, etc. As a general rule, the programmer
works with these flags indirectly, such as when the execution of a branch is
made conditional on the state of a flag.
255

<!-- source-page: 263 -->
## Page 263

First Publishing
Atari ST Internal
Two things should be mentioned yet: Multi-byte values (addresses o
operands) are not stored in memory as they are with 8-bit processors, in thi
order low byte/high byte, but the other way around. Four-byte expression:
(long word) are stored in memory (and the registers of course) with th
highest-order byte first.
The second is that unsupported opcodes do not lead to a crash, but cause :
Special exception, whose standard handling must naturally be performed by
the operating system.
3.8.1 Addressing modes
This is probably the most interesting theme of the 68000 because the
enormous capability first takes effect through the many various addressing
modes.
The effective address (the address which, sometimes composed of several
components, finally determines the operand) is fundamentally 32 bits wide,
even if one or more the components specified in the instruction is shorter.
These are always sign-extended to the full 32-bit width.
|
The charm of the addressing lies in the fact that almost all instructions
(naturally with exceptions), both the source and destination operands, can
be specified with one of the addressing modes. This means that eve
memory operations do not necessarily have to use one of the registers
memory-to-memory operations are possible.
In the assembler syntax, the source operand is given first, followed by the
destination operand (behind the comma).
|
256

<!-- source-page: 264 -->
## Page 264

First Publishing
Atari ST Internals
Register Direct
The operand is located in a register. There are two kinds of register direct
addressing: data register direct and address register direct.
In the first case, the operand may be bit, byte, word, or long word-oriented;
in the second case a word or long word is required, in case the address
register is the destination of the operation.
Example:
ADD.B DO,D1
or ADDA.W DO,A2
Absolute Data Addressing
The operand is located in the address space of memory. This can also be a
peripheral component, naturally (see MOVEP). The address is specified in
absolute form.
This can have a width of a a long word, whereby the entire address space
can be accessed,
or
it can be only one word wide.
In this case
is
sign-extended (the sign being the highest-order bit) to 32 bits. For example,
the word $7FFF becomes
the long word $00007FFF, while $FFFF
becomes $FFFFFFFF. Only the lower 32K and the upper 32K of the
address space can be accessed with the short form. This addressing mode is
often used in the operating system of the ST because important system
variables are stored low in memory and all peripheral components are
decoded at the top.
Example:
MOVE.L $7FFF,$01234567
Instructions in which both operands are addressed with a long word are the
longest instructions in the set, consisting of 10 bytes.
257

<!-- source-page: 265 -->
## Page 265

First Publishing
Atari ST Internal:
Program Counter Relative Addressing
This addressing mode allows even constants to be addressed in a completely
relocatable program, since the base of the address calculation is the current
state of the program counter.
The are two variations. In the first, a 16-bit signed offset is added to the
program
counter,
and
in
the
second,
the
contents
of
a
register
(sign-extended if only one word is specified) are also added in, though here
the offset may be only 8 bits long.
Example: MOVE.B $1234 (PC) ,$12(PC,DO.W)
Register Indirect Addressing
There are several variations of this, and they will be discussed individually.
Register Indirect
Here the operand address is located in an address register.
Example: CLR.L
(A0)
Postincrement Register Indirect
The operand is addressed as above, but the contents of the address register
are then incremented by the length of the operand, by
1 for xxx.B or 4 for
xxx.L,
Example: BSET.B
#0, (AO)+
or BCLR.L
#23, (Al)+
Predecrement Register Indirect
Here the address register is decrement by the length of the operand before
the addressing.
Example: EOR.L DO,$1234 (A4)
258

<!-- source-page: 266 -->
## Page 266

First Publishing
Atari ST Internals
Indexed Register Indirect with Offset
As above, but the contents of another register (address or data) are also
added in, taking the sign into account. The offset may have a width of 8 bits
here, however.
Example: MOVE.W $12(A5,A6.L),D1
Immediate Addressing
Here the operand is contained as such in the instruction itself. Naturally, an
operand specified in this manner can serve only as a source. The immediate
operands can, as a general rule, be any of the allowed widths.
Example: ADDI.W #$1234,D5
In the variant QUICK, the constant may be only 3 bits long, therefore
having a value from 0-7. An exception is the MOVE command, where the
constant may have 8 bits, but in which only a data register is allowed as the
destination.
Example: ADDQ.L #1,A0
or MOVEQ #123,D1
Implied Register
This addressing mode is mentioned only for the sake of completeness and in
it, an operand address is already determined by the instruction itself. The
operands are either in the program counter, in the status register, or the
system stack pointer.
Example: MOVE SR,D6
Regarding the offsets, it should be noted that they are signed numbers in
two's complement. Their highest-order bit forms the sign. With an 8-bit
value, an offset of +127/-128 is possible, and about +32K with 16 bits.
259

<!-- source-page: 267 -->
## Page 267

First Publishing
Atari ST Internals
3.8.2 The instructions
In the following instruction description, the individual bit patterns are not
listed since this would lead to far in this connection. Additonal information
can be gathered from books like the M68000 16/32-Bit Microprocessor
Programmer's Reference Manual (Motorola).
The instructions are also explained only in their base form and variations are
mentioned only in name. We will briefly explain what the individual
variations can look like here.
The variations are indicated by letter after the operand. This can be one of
the following:
A
indicates that the destination of the operation is an address register.
Word operations are sign-extended to 32 bits.
I
indictaes an immediate operand as the source of the operation. I
operands may assume all widths as a general width.
Q_
means quick and represents a special form of immediate addressing.
Such an operand is usually three bits wide, corresponding to a value
range of 0 to 7. This limited range has the advantage that the operand
will
fit into the opcode. Since there
is no special command for
incrementing a register, something like ADDQ.L #1,A0 works well in
its place. An exception is MOVEQ. Here the operand may have a value
of 0-255.
X
indicates arithmetic operations which use the X flag. This flag has a
special significance. It is set equal to the carry flag for all arithmetic
operations. The carry flag, however,
is also affected by transfer
operations while the X flag is not so that it remains available for further
calculations. This is especially useful for computations with higher
precision than the standard 32 bits, where temporary results must first
be saved, and where the carry flag can be changed as a result.
All instructions have a suffix after the opcode of the form .B, .W, or .L.
This suffix indicates the processing width of the operation. Although a data
register, for example, has a width of 32 bits = 4 bytes =
1 long word, the
:nstruction CLR.B D0 clears only the lowest-order byte of the register. For
registers, .W specifies the lower word. The higher-order word
is not
260

<!-- source-page: 268 -->
## Page 268

First Publishing
Atari ST Internals
explicitly addressable. If the operand is in memory, it is imporant to know
that .W and .L operands must begin on an even address. The same applies
for the opcode as such, which also always comprises one word.
If the destination of an operation is an address register, only operands of
type .W and .L are allowed, whereby the first is sign-extended to a long
word.
Some listings contain instructions of the form MOVE.L #27,D0. The
programmer then assumes that the assembler will produce #$0000001B
from #27.
Now to the individual instructions:
ABCD Add Decimal with Extend
There is one data format which we have not yet discussed: the BCD
format. This means nothing more than "Binary-Coded Decimal" and it
uses digits in the range 0-9. Since this information requires only 4 bits,
a byte can store a two-digit decimal number. The instruction ABCD can
then add two such numbers. The processing width is always 8 bits.
ADD Add Binary
This instruction simply adds two operands.
Variations are ADDA, ADDQ, ADDI, and ADDX.
AND Logical AND
Two operand are logically combined with each other according the
AND function.
Variation: ANDI
ASL Arithmetic Shift Left
The operand is shifted to the left byte by the number of positions given,
whereby the highest-order bit is copied into the C and X flags. A 0 is
shifted in at the right. If a data register is shifted, the processing width
can be any. The number of places to be shifted is either specified as an I
operand (3 bits) or is placed in an additional register. If a memory
location is shifted, the processing width is always one word. A counter
is then not given; it is always =1.
ASR Arithmetic Shift Right
The operand is shifted to the right, whereby the lowest bit is copied to
C and X. The sign bit is shifted over from the left. See ASL for
information about processing width and counter.
261

<!-- source-page: 269 -->
## Page 269

First Publishing
Atari ST Internals
Bee Branch Conditionally
The branch destination is always a relative address which is either one
byte
or one word long (signed!). Correspondingly, the branch can
jump over a range of +127/-128 bytes or +32K-1/-32K. The point of
reference is the address of the following instruction.
Whether or not this instruction is actually executed depends on the
required condition, which is verified by means of the flags. Here are the
variations and their conditions. A minus sign before a flag indicates that
it must be cleared to satisdy the condition. Logical operations are
indicated with "*" for AND and "/" for OR.
BRA
Bcc
BCS
BEQ
BGE
BGT
BHI
BLE
BLS
BLT
BMI
BNE
BPL
BVC
BVS
Branch
Branch
Branch
Branch
Brangh
Branch
Branch
Branch
Branch
Branch
Branch
Branch
Branch
Branch
Branch
Always
Carry Clear
Carry
Set
Equal
Greater
or Equal
Greater Than
Higher
Less
or Equal
Lower
or
Same
Less
Than
Minus
Not
Equal
Plus
Overflow Clear
Overflow
Set
BCHG Bit Test and Change
The specified bit of the operand will be inverted. The original state can
be determined from the Z flag. The operand is located either in memory
(width=.B) or in a data register (width=.L). The bit number is given
either as an I operand or is located in a data register.
BCLR Bit Test and Clear
The specified bit is cleared. Everything else is handled as per BCHG.
BSET Bit Test and Set
The specified bit is set. Boundary conditions are per BCHG.
BSR Branch to Subroutine
This is an unconditional branch to a subroutine. Branch distances as for
Bec.
262
no condition
-c
Cc
Z
N*V/-N*-V
N*V*-Z/-N*-V*-Z
~C*=-Z
Z/N*-V/-N*V
C/Z
N*-V/-N*V
N
-Z
-N
-V
Vv

<!-- source-page: 270 -->
## Page 270

First Publishing
Atari ST Internals
BTST Bit Test
The bit is only checked as to its condition. Everything else as per
BCHG.
CHK Check Register Against Boundaries
A data register is checked to see if its contents are less than zero or
greater than the operand. Should this be the case, the processor
executes an exception. The program is continued at the address in
memory location $18 (vector 6). Otherwise no action is taken. The
processing width is only word.
CLR Clear Operand
The specified operand is cleared (set to zero).
CMP Compare
The first operand is subtracted from the second without changing either
of the two operands. Only the flags are set, according to the result.
Variations: CMPA and CMPI
Both operands are addresses with the addressing mode (Ax)+ with the
variant CMPM.
DBcc Test Condition, Decrement and Branch
A data register is decremented and the flags are checked for the
specified condition. A branch is performed if either the condition is
fulfilled or the register is -1. Branch conditions and ranges as per Bcc.
DIVS Divide Signed
The second operand is divided by the first operand, taking the sign into
account. Afterwards the second operand contains the integer quotient in
the lower word and the remainder in the upper word, which has the
same sign as the quotient. The data width of the first operand is set at
.W and at .L for the second.
DIVU Divide Unsigned
Operation as above, but the sign is ignored.
EOR Exclusive OR
The two operands are logically combined according to the rules of
EXOR.
Variations: EORI
EXG Exchange Registers
The two registers specified are exchanged with each other.
263

<!-- source-page: 271 -->
## Page 271

First Publishing
Atari ST Internals
EXT Sign Extend
The operand is filled to the given processing width with its bit 7 (in the
case of .B) or bit 15 (.W).
JMP Jump
Unconditional jump to the specified address. The difference between
this and BRA is that here the address is not relative but absolute, that is,
the actual jump destination.
JSR Jump to Subroutine
Jump to a subroutine. The difference from BSR is as above.
LEA Load Effective Address
This often-misunderstood instruction loads an address register not with
the contents of the specified operand address as is normal for the other
instructions, but with the address as such!
LINK Link Stack
This instruction first places the given address register on the stack. The
contents of the stack pointer (A7) are then placed in this register and the
offset specified is added to the stack pointer.
With this practical instruction, data areas can be reserved for
a
subroutine, without having to make room in the program itself, which
would also be impossible in programs which run in ROM. The
C-compiler makes extensive use of this capability for local variables.
LSL Logical Shift Left
Function and limitations as per ASL.
LSR Logical Shift Right
Function and limitations as per ASR, except here the sign is not shifted
in on the left, but a 0.
MOVE
The first operand is transferred to the second.
Variations: MOVEA, MOVEQ
MOVEM Move Mulitple Registers
Here an operand can consist of a list of registers. This can be used to
place all of the registers on the stack, for instance.
Example: MOVEM.L AO-A6/D0-D7,-(A7)
264

<!-- source-page: 272 -->
## Page 272

First Publishing
Atari ST Internals
MOVEP Move Peripheral Data
This speciality
is made expressly for the operation of peripheral
components. As a general rule, these work only with an 8-bit data bus,
and are are then connected only to the upper or lower 8
bits of the
68000's data bus. If a word or long word is to be transferred, the bytes
must be passed over either the upper or lower byte of the data bus,
depending on whether the address is even or odd. The address is then
always incremented by two so that the transfer always continues on the
same half of the data bus on which it was begun. Corresponding to the
purpose of this instruction, one operand is always a data register, and
the other is always of type register indirect with offset.
MULS Multiply Signed
Signed multiplication of two operands.
MULU Multiply Unsigned
Multiplication of two operands, ignoring the sign.
NBCD Negate Decimal with Extend
A BCD operand is subjected to the operation 0-operand X.
NEG Negate Binary
The operand is subjected to the treatment 0-operand.
Variations: NEGX
NOP No Operation
As the name says, this instruction doesn't do anything.
NOT One's Complement
The operand is inverted.
OR Logical OR
The two operands are combined according to the rule for logical OR.
PEA Push Effective Address
The address itself, not its contents, is placed on the stack.
RESET Reset External Devices
The reset line on the 68000 is bidirectional. Not only can the processo.
be externally reset, but it can also use this instruction to reset all of the
peripheral devices connected to the reset line.
This is a priviledged instruction!
265

<!-- source-page: 273 -->
## Page 273

First Publishing
Atari ST Internals
ROL Rotate Left
The operand is shifted to the left, whereby the bit shifted out on the left
will be shifted back in on the right and the carry flag is affected.
Processing widths and shift counter as per ASL.
ROR Rotate Right
As above, but shift from left to right.
ROXL Rotate Left with Extend
As ROL, but the shifted bit is first placed in the
X flag, the previous
value of which is shifted in on the right.
ROXR Rotate Right with Extend
As above, but reversed shift direction.
RTE Return from Exception
Return from an exception routine to the location at which the exception
occurred.
RTS Return from Subroutine
Return froma subroutine to the location at which it was called.
RTR Return and Restore
As above, but the CC register (the one with the flags) is first fetched
from the stack (on which it must have first been placed, because
—
otherwise execution will not return to the proper address.
SBCD Subtract Decimal with Extend
The first operand is subtracted from the second. Refer to ABCD for
information on the data format.
Sce Set Conditionally
The operand (only .B)
is set to $FF if the condition is fulfilled.
Otherwise it is cleared. Refer to Bcc for the possible condition codes.
STOP
The processor is stopped and can only be called back to life through an
external interrupt.
This is a priviledged instruction!
SUB Subtract Binary
The first operand is subtracted from the second.
266

<!-- source-page: 274 -->
## Page 274

First Publishing
Atari ST Internals
SWAP Swap Register Halves
The two halves of a data register are exchanged with each other.
TAS Test and Set Operand
The operand (only .B) is checked for sign and 0 (affecting the C and N
flags). Bit 7 is then set to 1.
TRAP
The applications programmer uses this instruction when he wants to call
functions of the operating systems. This instruction generates an
exception, which consists of continuing the program at the address
determined by the given vector number. See the chapter on the BIOS
and XBIOS for the use of this instruction.
TRAPV Trap on Overflow
If the V flag is set, an exception is generated by this instruction,
resulting in program execution continuing at the address in vector 7
($1C).
TST Test
Action like TAS, but the operand is not changed.
UNLK Unlink
This instruction is the counterpart of LINK. The stack pointer (A7) is
loaded with the given address register and this is supplied with the last
stack entry. In this manner the area reserved with LINK is released.
Addendum to the condition codes: The conditions listed under Bcc are not
complete, because the additional conditions do not make sense at that point.
But the instrutions DBcc and Scc have the additional variations T (DBT,
ST) and F (DBF, SF). T stands for true and means that the condition is
always fulfilled. F stands for false and is the opposite: the condition is never
fulfilled.
267

<!-- source-page: 275 -->
## Page 275

Atari ST Internals
First Publishing
3.9 The BIOS Listings
- Version
1
&é peyorar
pug
abuexy
Azrowsw
resto
od 2P8TD
weqsks
butyeredo
ayq
go
42P4qS
sotTqetTiea weysks SuTyeredo
ayq
jo
pug
GV
4TP98TO
ZOTOO ven
aqqyeted
IoToS prot
eTqe} AoTOoO
ayy
jo
sseaippy
SIOTOO
9T
QIOTOCO
sserppy
apowsuAS
setddo[Tjy
JoeTeseqd
W
.z0d
AoeTAEaS
qyndyno
of
q@ pue
yy
yiod
dty2 punos ay
jo
sssippy
pTTeAsaea
03 OTbeusoy
IOYISASIT
peoyT
sqjdnizajut
ou
‘epow rosTAzedns
S86T/OZ/9
Beep
UOT IeeID
sseippe
jesay
weqsAs
Hutqyezedo
ayq
jo
pug
wejsks
Butyeredo ey
jo
47e4S
ssoaippe
josey
[
uotTsian
qazeqs
weifoid
of
SOId
LS
IYVLV
Tw‘ov
+ (OW) ‘Od
0G ‘O#
TW‘O00S$#
OW ‘OASS#
Gv ‘GW
mancatlan
aga7uso
vu
+ (Tw)
4+ (OW)
OW! (Od) OTHSS
od’As#
TW ‘OP78a4ddd$
WOC8AAIAS
‘TH
090c$
(Dd) WIOSS ‘OF
(OW) 2414
(OW) ‘a$S#
(OW) 2‘0DS#
(OW) “L#
Ov ‘0088444d$
97PS “9ZOSTUTES#
W2bS“ATOSS
Us ‘OOLz$#
0)
G86T0Z90$
bad6$
ATOSS
0OD6TS
000S$
atoss
O‘T
ATOSS
T° dwo
M* @A0U
T° baaow
M* SAU
M*3AOU
PaT
q* saow
baq
38 1q
q* aaow
q* aaow
q* sAow
q*aaoul
POT
T° saou
T° eaou
4° ACW
atop
T°op
Top
Top
T°op
T'op
T°op
q°op
eid
Bde
OD0E
OOOL
OOOSOILZE
DdSODLOE
qdd6
Ode OVATG
JOOODEOE
OPC8dddd6
AED
VO7TBAAAAZOOOOFET
80L9
BDAAO00OVEBO
ZOOOLOOOILTIT
qo000od0T
ZOOOODOOOLTT
LQQ0ad0T
0088444 46ST
9ZPOOOOO9ZESTPTEOFES
VZPOOOOOUTOSO0006AEC
OOLZOAIY
0000
$86T0c90
bad6 TO00
ATOSOOO00
0056 TO000
00050000
ATOSO000
OoTO
oT09
280500
080500
ALOSO0O0
WL0S00
9L0S00
pLOSO00
GLOSOO
490S00
V¥90G00
990500
090500
8soso0d
9960500
0S0sS00
WPosood
970500
oposoo
2€0S00
9E0S00
9720500
f20S00
ATOSOO
3T0S00
8TOSO0
PTOSOO
OTOSOO
200500
800500
700S00
200500
olonencyore)
KOO
KO
ORO
OE RO ROK OR ORR OE
OR
OE OR OER OR OR
268

<!-- source-page: 276 -->
## Page 276

697
005084
005086
00508A
005090
005094
06509C
OO50A4
OO5O0A8
OOSOAA
OOSOAC
OOSOAE
0050B0
OO50B4
O050B8
OOSOBE
0050Cc0
0050C4
0050CC
0050D4
0O050DC
OOSOE4
OO50EC
OO50F4
0050FC
005102
005108
OO510E
005114
005118
OOSIIE
005126
00512C
66FA
206D042E
91FCO0008000
2B48044E
13EDO44FFFFF8201
13ED0450FFFF8203
323CO7FF
20c0
20Cc0
20C0
20c0
SICSOFFF6
207AFFSE
0€9087654321
6704
41 FAFF46
23E80004000004FA
23E80008000004FE
2BICOOO00SAE8046A
2B7C00005D880476
2B/CO0005BEE0472
2B7COO0O0SDIEO4TE
2B7CO00060B2047A
2B6D044E0436
2B6D04FA0432
4FF900003E2A
3B7C00080454
SOEDO444
3B7C00030440
2B7C000012BC04C6
3BICFFFFO4EER
2B7C0000500004F2
bne
move.l
sub.l
move.
move,
move.
move.
move,
move.
move,
PREP
£Oo oF
move.
dbra
move .1
cmp.1
beg
lea
move .1
move .1
move,1
move .1
move.1
move .1
move.1
move.1
move.1
lea
move .w
st
move .w
move.1
move .W
move.1
$5080
$42E(A5),A0
#$8000,A0
AO, $44E(A5)
$44F (A5), SFFFF8201
$450 (A5), $FFFF8203
#S7FF,D1
DO, (A0)+
DO, (AQ) +
DO, (AOQ)+
DO, (AQ) +
D1, $50A8
$5014 (PC)
, AO
#$87654321,
(AO)
$50C4
$5008 (PC)
, AO
4(A0),S4FA
8 (AO) ,S4FE
#S$5AE8,$46A
(AS)
#$5D88,$476(A5)
#SSB6E,
$472 (A5)
#SSD1E,$47E
(AS)
#$60B2,S47A(A5)
$44E (A5)
, $436 (AS)
S4FA(A5)
, $432 (A5)
$3E2A,A7
#8, $454 (AS)
$444 (A5)
#3,$440(A5)
#$12BC,$4C6(A5)
#SFFFF,
$S4EE (AS)
#$5000,
S4F2 (A5)
No
Phystop,
end
of
RAM
Minus
32
K
As video address
v
bs
ad
Dbaseh,
video address
for hardware
Dbasel
(S7FF+1)*16
=
32
K video
RAM
Clear
screen
Next
16
K bytes
End
os
Exec
os
Hav
init
Hdv
rw
Hdv bpb
Hdv mediach
Hdv boot
V
bs
ad
as memory
top
End
os
as memory bottom
Initialize stack pointer
Nvbls,
number
of
VBL routines
Fverify,
Floppy Verify
after
write
Seekrate
for
floppy
to
3
ms
Dskbufp
to
$12BC,
disk buffer
Clear dumpflg
for
hardcopy
Sysbase,
start
of
the operating
system
Surysyqnd S114
gjeurojuy FS Wey

<!-- source-page: 277 -->
## Page 277

OLZ
005134
00513¢C
005144
005148
0o514C
005156
005158
00515C
005162
005168
00516C
OO5S16E
005174
005178
OOS5SI7E
005186
00518E
005192
00519A
0051A2
OOS1AA
OOSIAE
0051B6
0051BA
0051BE
o0s1c2
0051C6
0051C8
oo51icc
0051D0
0051D2
0O051D6
2B7CO00005FCO4A2
2B7C00005328046E
47FAQ3FC
49FAQ1DE
OCB9FA52235F00FA0000
6726
43FA06DE
D3FC02000000
41F 900000008
303C003D
20C9
D3FC01000000
S1C8FFF6
23CB00000014
2B7C000054520070
2B7C0000543C0068
2B4B0088
2B7C0000556C00B4
2B7C0000556600B8
2B7COQ000EB3A0028
2B4C0400
2B7C000055620404
2B4C0408
41EDO4CE
2B480456
4298
51C8FFFC
61001D14
7002
6100012A
9BCD
#S5FC,$4A2
(A5)
#$5328,$46E(A5)
$5542 (PC) ,A3
$5328 (PC) ,A4
#SFA52235F, $FA0000
SS17E
$5838 (PC) ,Al
#$2000000,Al
$8,A0
#$3D,D0
Al, (AO) +
#51000000,A1
DO,$516C
A3,$14
#$5452,$70(A5)
$$543C,
$68 (A5)
A3,$88 (A5)
#$556C,
$B4 (A5)
#$5566,
$B8 (AS)
#SEB9A,
$28 (A5)
A4,$400(AS)
#$5562,$404
(A5)
A4,$408(A5)
$4CE (A5) ,A0
AO, $456(A5)
#7, 006
(AO) +
DO, $51C6
S6EER2
#2,D0
$52FE
AS,AS
Savptr
for TRAPs
to
$5FC
Hdv dsb
auf
rts
Pointer
to
rte
Pointer
to
rts
Cartbase,
Diagnostic cartrige
inserted?
Yes,
don't
initialize vectors
Terminate process
Vector number
is
in bits
24-31
Start with bus error
Number
of vectors
Set vector
Increment number
in bits
24-31
Next
vector
"Division by
zero'
to
rte
Vertical Blank Interrupt,
IPL4
Horizontal Blank Interrupt,
IPL2
TRAP
#2
to
rte
TRAP
#13 vector
TRAP
#14 vector
LINE
A vector
Etv timer to
rts
Etv critic vector
Etv term to
rts
Vbl
list
As pointer
to vblqueue
8&8 vectors
Clear
list
Next
vector
Initialize MFP
Bit number
Cart
scan,
test
cartridge
Clear
AS
Surysyqng ISI]
yeusaUy LS Hey

<!-- source-page: 278 -->
## Page 278

Atari ST Internals
First Publishing
»DUd* GNYWWOD
1
aueu
[TON
aueU
TINN
Dexe ony
Zosino etTqeuy
ON
2
¥STpP worlZ
[TeSys peoT
“peroTpuy
qooqysd
Sod e2TTeTarul
abptaqies
ysaq
‘ueosqre)D
[
iequnu
4TYW
€
01 ‘Tdi
abptaqies
ysaq
‘ueosqie)
Q
zequnu jt
TGA B07
‘WaSTAA
qsp APH
yndyno
usezos
azTTeTatTur
€
TOTOO
03
(ASPTQ)
GT
zotoo Adop
ON
&é
UOTANTOsSSr uNnTpeN
Teqyjtus
werboiad
‘puqytTys
PUATTYUSS
SARS
UOTINTOSeT MOT
JOSTes |esTMIaTIO
soz
&
apow TOTO
puyAITyUsJep
48D
&
JojTUCW ewoTySouoU
ON
qoaysep ewozyoouow dtdb
qin
4seL
awoTyIouowW Oo
UOT INToOsaZ
y[Nejag
umInqjez eznyjotd
yxeau
ATOZ
ATEM
‘“TOAM
uanqez ainqotd
yxeu
103
ATeM
‘“TQAM
(L¥)-
(Dd) Wazs$
(Dd) dazg$
(Dd) G3Z7S$
Ap6ss
ogaes
Z9eG$
Z8b$
OdZS$
OLb6$
BAZS$
Od‘T#
Us ‘OOETS#
adzgs
od
7GbS ‘TH
(SV) 39bS‘ATOSS#
pO94$
OPZ8dddd$ ‘ASTBAIIIS
bIZS$
oa‘T#
09 784ddd$
“0d
(GY) DPBS ‘0d
od
WdATSS
od‘Z#
Od‘ (SU) WbES
WdTSs
TOWdd
dd ad$ ‘LH
od‘c#
peSss
pesss
M* ITO
ead
ead
vod
aisq
isq
beq
A°qsd
isq
isq
Isq
T’ beaow
M*aAoU
aisq
M*ITO
M* oAoU
T° eaou
as
M* eAoU
auq
q° duo
q*aaou
q*eaow
Q* ato
314
q*dwo
q* anow
baq
4asaq
q* aaou
Aisq
Isq
L9OCD
ALOOVL8P
S600VL8P
6600VL8P
Ad9000T9
P9DCOOTS
8TL9
cBPOOOOO6LWPE
odo0o00
Ts
PEZPOOTS
990000T9
TOOL
O0ECOAIP
oqooootgs
OCD
ZTSPOOQOOTOOODAEE
49 POATOSOOD0DLES
bO9400006EdE
9PC8AdAdAS
CB AATIO AEE
W099
Tooooeod
O9CBAATAOOET
OvPOODET
00¢Pb
c0d9
cO00DEOE
Wpvodcot
SOLIS
TOWAATTALOONGEBO
cOO0DEOT
99€000T9
VW9EOOOTS
ASéSoo
VScS00
992500
CSCS00
dvcSO00
VpcSo0
8bc2S00
CPCSOO
ae¢eSo0o
WECSO0
9ES00
bECSOO
O€eS00
9¢ES00
We2TS00
22900
V1IZSO00
bTeSO0
WO7cSO0
807500
bOzSO00
Adtsoo
V4ITSO00
B4TS00
9ATSOO
CATSOO
JATSOO
DATSOO
baTtsoo
OATSOO
3daTSoo
8a TSo00
271

<!-- source-page: 279 -->
## Page 279

CLE
005260
005262
005266
00526A
OOS26E
005272
005274
005276
005278
OOS27A
005280
005284
005286
00528C
005292
905296
00529A
005298
0052A0
0052A4
0052A6
OO52AE
0052B4
0052B6
0OS2BA
0052RBF.
0052C2
0052C4
0052C8
0052CE
0052D4
0052DA
605C
bra
610006EA
bsr
41FA0066
lea
32700502
move .W
0C100023
cmp.b
6602
bne
2449
move.
12D8
move .b
6AF4
bpl
103900000446
move .b
DO3C0041
add.b
1480
move .b
487900000502
pea
4879000052ED
pea
487A0059
pea
3F3C0005
move .W
3F3C004B
move
.W
4E41
trap
DEFCOOOE
add.w
2040
move
.1
2179000004FE0008
move.1
487900000502
pea
2F08
move .1
487A0035
pea
3F3C0004
move .W
3F3CO004B
move .W
4E41
trap
DEFCOOOE
add.w
4EF90000501E
jmp
504154483D00
dc.b
233A5COOFF
de.b
434F4D4D414E442E5052
dc.b
$52BE
$594E
$52CE(PC),A0
#$502,A1
#35, (AO)
$5276
Al,A2
(AO)
+, (Al) +
$526E
$446,D0
#$41,D0
DO, (A2)
$502
$52ED
$52ED (PC)
#5,-(AT)
#$4B,-(A7)
#1
#SE,A7
DO, AO
S4FE,
8 (AO)
$502
AO, -(A7)
$52ED (PC)
#4,-(A7T)
$$4B,-{A
#1
#SE,A7
S$SO1E
"PATH=", 0:1=92
'#:1',0,S$FF
"COMMAND .PRG', 0
‘#'
drive indicator
?
No
Address
of
the drive indicator
Copy drive number
Copy entire string
Bootdev
"At,
calculate drive number
Insert
in filename
Enviroment
string
Null
name
Null
name
Exec,
load program
GEMDOS
call
Correct
stack pointer
Save base page address
Exec
os
Exec,
load program
GEMDOS
call
Correct
stack
If
return,
then
Reset
SUTYsTqNg ISI]
BUI; TS Leyy

<!-- source-page: 280 -->
## Page 280

Atari ST Internals
First Publishing
[7
sseippe eseq
oO}
JeszjJo ppv
qyseq Arowey
AOIOSA ATNeJEC
uoTyeotTtTdde
yxeu
uot yezTTeTqaTul
ssoippe
XUTT
295
abpTzqzeo
ut
uoTjeot{dde TeuotITppy
siaysTtbezr
aiojssy
UOTISZTTPTATUT wiojiad
auTyNor
4TuT By
jo sseappy
szieqjstbar
anaes
ON
&é vUoTIeZTTeT
ATUL
ON
é payresut ebptzaqieo
azesn
aseqqieo
aebptaqieo
ysoL
qdueqje
.zeqs
puy
JO}DeA
YOoG
peotT
‘3000 APH
ebpTayieo
yseL
€
Jequnu
itd
YSTP wory
yooq
‘jooqysq
ov‘ia
T° ppe
TOTd ¥ZES00
ORO OOOO RRO OO OO OCR URS
URE OR OE
EOE ORE ROR ROR ORF
sya
GLabv 8cesoo
OR OOO
OR OO
EO OOOO
LURE R ORE RO REE EE KURO EF
sqi
GLUb 9ZES00
DOESS
auq
9499
¥ZES00
ow’ (ov)
T° aaow
osoz ZZ€S00
(ow)
T’3s83
C6Yb OZESOO
9V-OW/LO-00’+
(LW) T*weaou
JadLAIdOb DTESOO
(ow)
asf
064b VIESOO
ow‘ (OW)
T'eAow
p0008902 9TESOO
(LW) -‘9W-OW/LG-00 T*weaow
AdiILABH
ZTESOO
OzES$s
beq
AOLI OTESOO
(OW)
‘0d
3830
pOOOBZTO DOESOO
9ZES$
auq
W199 WOESOO
+(0W) ‘Zpamadodvs#
 T*duo
ZPAMAOAVBEOO
POESOO
ow ‘0000vdS
Ret
OOOOVAOOE6ATH AACSOO
FOR OR ROO
ORR
UR ORR RRO ORE
IR OEE
EE
Si
SLab 047500
(ow)
asf
0643b VAZS00
OW‘WLPS
T*eaou
WLPOOOOOGLOZ
PAZSOO
FAzS$
1sq
WOT9
Z4zZS00
oa‘e# T*beaow
COOL O04ZS00
OTE PrEevrCTETVTTTOCELCCOLO
Lee ee eee SS StS Se
ee
000000
dxz@soo
LECSOSAZAPSHLE
9A7SO0
OOLb’
bAcSOO
273

<!-- source-page: 281 -->
## Page 281

Atart ST Internals
First Publishing
ATAPI] PIOM
AOF
enTea seTqneg
IT
pue
0
sitq ayeTos]
uoTANTOSeT
CepTA
49D
‘pwuqITus
ZTRAUOW
PT TeAuey
ssoippe
HuTtTTeo
syq
of
yor”
4soq
enuTAUOD
‘ON
& peyoeer
sserzppe pug
udzaqgqed
4seq
yxXeu
33e87D
aqjeutTwiey
‘Tenbeun
sqjuequos
Axjoweu
4sey
4seq eyq
jo
sseippe pug
udeqjed
4saqj
ieeToD
od
ow’ (M* 749d) WOESS
98ES$
Ov ‘OF
W6eSSs
ow ’0008s#
bu‘ea
pa‘e#
ba ‘09z8adda$
T*ato
M‘3A0u
eauq
T° dwo
TyUq
T° dua
A*ppe
M*pue
q*enouw
O8cP
9B0PAL0E
099
000000000ATE
0¢¢9
00080000DA
TE
pbed
E000DLBO
O9C8dddI6E8T
98€S00
c8esod
O8€sod
WLESGOO0
BLESOO
ZLESOO
OLESOO
I9ESOO
99€S00
RRR
OR
OR
OR OR ORR OR ORO
OR
OR
RO
ORO
OR OEE OE
00000000
00000000
00000000
00000000
c9€S00
aASEsSOO
WSESO0O0
9S€S00
RK
OR
LOR OL
LOR REE LOR LOR ROR RO ROE
OE OR OK
(9W)
(SW) VERS ‘O68bL606S#
pcess
(SV) OZb$ ‘LOOBE0S96T#
Gv ‘Sv
du
T° dus
auq
T‘ dws
T'qns
9qqdb
VEPOWVV869LECAWDO
8099
O2POE
AGB TOCSLAYOO
doe
BSESOO
3P7ESOO
WpEesood
2vESOO
ObESoOO0
KR RR LO ROR LOR IE KOR KR OR OR
OR OK OE KOK ROE OR EF
(SW)
ZEESS
Tv ‘ow
Od‘ pSVas#
aqeess
od ‘+ (ow)
tw‘ (OW) B4T$
od
du
auq
T° duo
a’ppe
auq
M* duo
eeT
M*aqTo
odab
bA99
goCd
PSVdOLOG
8099
8S0d
BATOSAED
ObeD
aeesoo
9e€S00
WEEesood
9eEesoe
yeesoo
fEESO0O
AZESOO
9ZESOO
274

<!-- source-page: 282 -->
## Page 282

Atari ST Internals
First Publishing
+(0W) ‘TG
M*eAcw
TOOE
cdaesoo
uOoTANTOSeZT WNTpEn
WOT CTeTe TT TEC
TET SCE CESS SESS TESTES EEL TTT eS SS SS |
OdESS
PIG
3009
OdESo0o
+(0W) ‘Od
9M" eacw
OD0€
FDeSoOo
+(0W) 70d
«=A eAOW
QD0€ DDESG00
+(OV) ‘0d
9 M*eAcU
OD0E WOESOO
+(O0W) ‘OG
=M*eAcU
OD0€ 8DES00
UOTANTOSear
MOT
ECE
ETT TT TTT TTT TTT TEC
ECP SCT ETE SSeS TLE
Le Lee Le ee ee eS SS
uoTynTosez
YySTtH
DAESS
BIg
PIO9
9DEGOO
uoTAINTOSSsr
WNnTpen
edess
e1qg
9009
bOESOO
uoTANTOSet
MOT
BDESS
eB1ig
PO09
¢DES00
(M° $d ‘Dd) ZDESS
dul
coOrddab
AGESOO
od‘ (tw)
M’*eaow
TTOE
DAESOO
CHESS
emg
9€09
WHESO00
GW’ (0d) DEESS
eat
pooowdsdb
9aESoo
oa’ (TW)T
q*eacu
TOOO6ZOT
CHESOO
Ta‘zq
M*eacw
ZOZE OMESOO
CHESS
Pig
7709
AVESOO
GW‘ (Dd) OM ESS
eeT
bpOOOWdEP VVESOO
oa‘ (tv)
q°eacu
TIOT
8VEGOO
ZW‘ (M* pd ‘Dd) OTPSS
M*ppe
VW9OVaGAIPad
PYESOO
zw‘ow
T'eaow
BbbC ZVESOO
eq’‘scq
M*aAoU
SO9E OVESOO
9a‘ (M*Pa‘Dd)9TPSS
M*eAOU
BLOPAEDE D6ES00
La‘ST# T*beaow
JOAL WEESOO
ow‘’od
T’ppe
OOTd
86£S00
oa‘s#
T° TST
881d
96ES00
Teseqg
Od’e0@Bdddds
q'eAaou
COCBAATAGEOT
O6ES00
oa ‘s8#
M° TST
8bla
ABEesSoO
yeseqq
od ‘TOz@8dddd$
= eAow
TOZ8A4Add46E0T
88500
275

<!-- source-page: 283 -->
## Page 283

Atari ST Internals
First Publishing
oot
09T
9E09T
eLogt
cLogot
Mop
M'op
mop
Mop
arey®)
OWOO
2TbPSOO
OWOO
OTbSOO
PYHE AOPSOO
B8Da€
900%S00
gaye Yorsod
POrerer errr TePPTESTErerrerreLoee
le ss Se 22 2 tS eee ee
Treo
02 yor”
(Su)
duf
Saab 80bsoo
eq‘ew
T'eaow
d09z 906500
gaecs ‘ea
eaqp
bAITAOTS 70500
Za‘T#
= M*TKOZ
ZSEA 00500
beTy ATV v104seyY
us'+(L¥)
Mt eaow
309’ AAESOO
za‘Tt#
M*TxO7
ZGEX DGES00
Bety Aries anes
{LW)-
‘aS
 M*eAoU
LA0b WdESO0
oa‘T#
q*TxOZ
OTEA BAES00
ea‘L# T*baaou
LO9L 94ES00
Za ‘O#
T° beaow
OOPL
PAESOO
ev‘ed
T*aaou
€b9% ZAES00
(9¥)
duit
9qa% OF€S00
deeS$ ‘id
eiqp
AVIdIOTS OAESOO
Tw’z#
mM bppe
6bPS WHESGOO
owess ‘9G
ezqp
8dddZOTS 9AESOO
ow’z¥
T°’ eaow
WbO?
paesSOO
BVESS ‘EC
erap
9DadADTS OFESOO
+(0¥) ‘7a
M*eaou
ZO0E AAESOO
+(0W) ‘TQ
AM‘ aaou
TOOE OdESOO
uoT IRTOser
uSTH
SRR
OE
OR
ROR
OE
OR
OR
ER
ORE RE
EE
oaeSs
eiq
p009 Wdesod
+(0¥) ‘7G
MT SACU
ZOOE BAESOO
+(0¥) ‘Za
M* aACw
ZOOE 9AESOO
+(0W) ‘TQ
M*aaow
TOO€
paesoo
276

<!-- source-page: 284 -->
## Page 284

LLZ
005414
005416
005418
OO541A
FORO TIO
I RO
I IO ITO
I IO EI IOI
RIO I
IOI
I OI IO
tok te ted oe
00541C
005418
005420
005422
005424
005426
005428
00542A
00542C
00542E
005430
005432
005434
005436
005438
00543A
FOR III
II IOI IO III
TOR IOI IR IO RII
IRI
I
I
aK
RK
RK
00543Cc
00543E
005442
005446
005448
00544E
005450
0050
0000
0000
0001
0777
0700
0070
0770
0007
0707
0077
0555
0333
0733
0373
0773
0337
0737
0377
0000
3F00
302F0002
cO7CO700
6606
006F03000002
301F
4E73
dc.
dc.
dc.
dc.
x
££
=
=
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
dc.w
move.w
move.wWw
and.w
bne
Or.w
move .W
rte
$777
$700
$070
$770
$007
$707
$077
$555
$333
$733
$373
$773
$337
$737
$377
$000
DO, -(A7)
2(A7) ,DO
#5700,
D0
$544E
#$300,2(A7)
(A7)
+, D0
Color palatte
White
Red
Green
Yellow
Blue
Magenta
Blue-green
Light
grey
Grey
Light
red
Light
green
Light
yellow
Light
blue
Light magenta
Light blue-gree
black
HBL interrupt
Save
DO
Get
status
from stack
Isolate
IPL mask
Not
equal
to
zero
?
Otherwise
IPL
tp
3
Restore
DO
Burysyqng ISI
sjeuiazuy LS Livy

<!-- source-page: 285 -->
## Page 285

Atari ST Internals
First Publishing
SIOTOD
OT
AJSYJTYUS OSPTA
ayy
UT sserppe
‘OQTOTOD
eqjeTed meu ey
jo
sserppe
‘1Ad10[oOD
ON
é
eqgjetTed
z0oToo
peotarz
‘/‘1qdiojToop
GW 2eeTS
TOsIndD
UusPT dT
auT4Nor aynoexg
abueyd votyNn[Tosax
TOF 1049S,
Iaqytys werboid
‘pwyjtus
PWAITYSS
SAPS
UOTINTOSeA MOT
ast”
On
é sworyoouoW
uoTanTosex
ToTooS
4ab
‘puqytysjed
&
103yUOW sWCTYOoUCW
qoejep ewozyoouow
‘dtdb djw
uotTyntoseaz
ySty
Jo jTUOU AOTOO
ON
qoajep eworyoouow
‘dTdb djw
soz
é
votynjTosez
YyOTH
puqyyTys peoy
GW AesTD
uay\YIe YOTOGA AuUSUaTOUT
SieqstTbaz
aaes
& paTqestp yJdnzzajut dA
WesTaA
yooToijy
yuSewaTOUL
qdnaizsqut
Ida
od’as#
TW ‘Op78addd$s
ow! (GW) YSbS
gapss
(GW) UShS
Sv ‘cv
8548s
(ow)
ow’ (GU) 96s
0978dddad$
“Od
(cw) ObPSs ‘0d
od
pwess
0d ’z#
od’ (GY) PPS
barss
TOWddd
dS “LE
bWESs
0d ‘z#
bass
TOWAdd
AIS ‘LF
asepss
oa ‘z#
od’E#
0d ‘097844445
GV ‘GY
TObS ‘TH
(LW) - ‘9V-oW/Ld-04
DESSS
cous ‘TF
99S ‘T#
M*anou
PaT
T*aaow
baq
T°3s3
T*qns
isq
asf
T° Ssaow
q*aaou
q* eAou
q°iqto
4T4
q* dus
q*eaou
baq
4s1q
e1mq
q*enou
auq
4s 3q
abq
q: duo
q°pue
q*aaou
T'qns
T’‘bppe
T*weaaou
Tw
a*bans
T' bppe
JOQOIENE
OFC8ddTIE
AED
WSPOd907~
8TL9
VSPOCYYP
qod6
a9b0090Z2
09 €84dd 400ET
OPbOOraT
00¢cF
c0a9
c000D€08
Wevodcot
OTLY
TOWd Id dAIL0006E80
9TO9
cOO00DEOT
9¢99
TOWddATAALOOOGEBO
OT29
c000DE0E
€Q000DE09D
O98
AIMEE OT
q5d6
c9bO0000682S
FAI LAG
20000089
CSVOOOOOGLES
99PO00006E2S
VWOrso0
bOPSO00
09%S00
aadpsoo
Warsoo
8adrsSo0
va7soo
caPS00
AVpSOO
8V7S00
bWbSO00
cWPsoo0
OWbDSO00
267500
86FS00
96bS00
a8pSo0
28'S00
88hS00
98PS00
ALbS00
OLbPSOO0
BLPSOO
bLbSOO
49bS00
999S00
990500
c9bS00
aS %S00
857500
fSbS00
ore
e
Tee Teer ererrrr ere ele Le ee Lee Se ee See See,
278

<!-- source-page: 286 -->
## Page 286

6L7
0OS5S4CE
0054D0
0054D4
0054D8
0054DC
0054DE
0054E4
0054E8
OOS4EA
OO54FO
0054F2
OO54F8
OO54FC
005502
005504
005506
00550C
OO550E
005514
005516
OOSS1A
00551C
005520
005524
005526
00552A
00552C
005530
005538
00553C
005542
32D8
SICBFFFC
42AD045A
4AADO45E
671A
2BEDO45E044E
202D044E
E048
13COFFFF8203
E048
13COFFFF8201
610011EA
363900000454
6720
5387
207900000456
2258
B3FCO0000000
670A
48E70180
4E91
4CDFO180
SICFFFEA
9BCD
4A6D04EE
660C
61000532
33FCFFFFOQOOQ04EE
4CDFUFFF
527900000452
4E73
move .W
dbra
clr.1
tst.l
beq
move
.1
move.1
lsr.w
move .b
lisr.w
move.b
bsr
move .W
beq
subq.1
move.1
move.1
emp. 1
beq
movem.1
jsxr
movem.1
dbra
sub.1
tst.w
bne
bsr
move .W
movem.1
addq.w
rte
(AQ)
+, (Al) +
DO, $54CE
$45A(A5)
$45E(A5)
$54F8
$45E (AS)
, $44E(A5)
$44E(A5),DO
#8,D0
DO, $FFFF8203
#8,D0
DO, $FFFF8201
$66E4
$454,D7
$5524
#1,D7
$456,A0
(A0)+,Al
#50,Al
$5520
D7/A0,~(A7)
(Al)
(A7T)+,D7/A0
D7, $550C
AS,A5
S4EE (A5)
$5538
S5SA60
#SFFFF,S4EE
(A7) +,D0-D7/A0-A6
#1,5452
Copy
Next
color
Clear colorptr again
Screenpt,
new video
address
?
No
Copy screenpt
tp
v
bs
ad
V
bs
ad
Bits
8-15
To dbasel
Bits
16-24
To dbaseh
VBL routine
for floppies
Nvbls,
number
of VBL routines
No vectors
?
Convert
to dbra counter
Address
of
the vblqueue
Get vector
zero
?
Don't execute routine
Save registers
Execute routine
Restore registers
Test
next vector
Clear
A5
Dumpflg,
hardcopy desired
?
No
Hardcopy
Clear dumpflg again
Restore
registers
Vblsem,
restore VBL again
Surysyqng ISI]
sjeuiayuy TS uey

<!-- source-page: 287 -->
## Page 287

087
kK
KK KR ORK
KK
kk kk kok kkk kok kk kkk koko
kok kkk
ke
005544
40E7
move.w
SR,
—({A?7)
005546 O27CF8FF
and.w
#SF8FF,SR
00554A 203900000466
move.,1
$466,D0
005550 BOB900000466
emp.1
$466,D0
005556
67F8
beq
$5550
005558
46DF
move.w
 (A7)+,SR
OOS55A 4E75
rts
HK
KK
KK
IK KK IR KK IK KKK KKK III KK KEK EK KKK KKK KEK KAKKE KE
00555C 2F3900000404
move.l
$404,-(A7)
005562
70FF
moveq.1
#-1,D0
005564
4E75
rts
ROK KKK I
KA KK
KI KK KK KI KKK
KKKKK KKK KKK KKK KR KK KK RK
005566 41FA0084
lea
S55EC (PC)
, AO
00556A
6004
bra
$5570
FI KO
KIO et
tO KK KI KI IK KK KKK IK KI KKK IKK KKK KKK KEK KKK AK
00556C 41FA004C
lea
$55BA(PC)
, AO
005570 2279000004A2
move.1
$4A2,A1
005576
301F
move.w
(A7)+,D0
005578
3300
move.w
DOQ,-({(A1)
OO557A 231F
move.l]
(A7)+,-(A1)
00557C 48E11FIF
movem.1 D3-D7/A3-A7,-{A1)
005580 23C9000004A2
move.1
Al,$4A2
005586 O800000D
btst
#13,D0
OO558A
6602
bne
$558E
00558C
4E6F
move.1
USP,A7
00558E
301F
move.w
 (A7)+,D0
005590 BO58
cmp.w
(A0}+,D0
005592
6C10
bge
$55A4
Wvbl,
wait
for
next
V-sync
Save
status
IPL
0,
allow interrupts
Load frclock
Frelock
Still equal
?
Restore
status
Critical error handler
Etv critic
TRAP
#14
Address
of the TRAP
#14
routines
TRAP
#13
Address
of the TRAP
#13 routines
Savptr,
pointer to
save
area
Status register to
DO
Save
in
save
area
Save
PC
And save
C register
Update
savptr
Call
from supervisor mode
?
Yes
Else
use USP
Get
function
number
from
stack
Compare with maximal number
Too
large,
stop
Surysyqng ISI
S[eui9zuy LS BBV

<!-- source-page: 288 -->
## Page 288

Atari ST Internals
First Publishing
asqus
‘IT
dewaip
‘OT
yoretTpeu
(4OeTTput)
76
yeysooq
‘8
qdqqeb
(joertTpuy)
‘2
TeoyOTI
“9
oaxeqes
‘¢
sqemzi
(jOerTpUT)
“F
qnoucsq
‘¢
ujTuooq
‘Z
qeqsuosq
‘T
qduyei
‘o
sauT
NOT
Jo
ISsqUNN
STT@2
ET#
TWYL
ayy
Jo sassaippy
TTeo
OF We
aydaes
a yepdn
yorys
uo snes
yorqys
uo
Od
szaqisther
ai1ojssy
aydaes
499
euTQNO’
|aANdexg
GW 1P8TD
ATJOaITpUT
ssaippe
esn
ssTa
é pereeTo
Te 3d
OW
OL
auT Anos
ey.
jo
sssippe
395
r3equNnod
Huot
qo
zyequnu
JTSsAUOD
OTLS$
9TLSS
coooooosstdLbs
owoss
COOOODOBS+ZLbS
eLLSS
WSLSS
COO0000BS+9L
FS
9¥9G$S
Wo9cs
b69S$
az2Lss
et
T'op
T’op
T’op
Top
T'9p
T"9p
T'op
T’op
T'op
T*op
T'op
T’op
Mop
ITLS0000
9TLS0000
ALv00008
ow9S0000
ZL¥00008
ZLLS0000
¥SLS0000
91700008
9W9S0000
v69S0000
p69S0000
azLS0000
3000
84SS00
baSSo00
0ussoo
20dSS00
gassoo
bdassoo
oassoo
995500
895500
BOSSO00
9o6S00
3dSS00
wassoo
MK
KOO
OE
OR ROR
ROR
ROR ER ROR ROR ERE RR EE OF
7wes ‘TY
(Lw)-4+ (TY)
(Lv)
- 4+ (TW)
Lv-ew/La-€a
‘+ (TY)
tw ’2v7s
(Ov)
cw ‘SW
ow’ (OW)
ovsss
ow‘od
oa‘ (#00 ‘0u) 0
0d ‘z#
e4qz
T*aaow
M* OACU
T*aaow
T waaou
T° aaow
isl
T"qns
T° asaow
Tdq
T'saou
T° eaouw
M°TST
eLay
2WPOOOO06GIES
6THE
6Tdé
B8A8d600P
TWPOOOODELZE
O64P
qoe6
Osod
cOw9
OP07~
OOODDED?
8bSa
gdssoo
ZdSS00
oadssoo
avssoo
WWSS00
PYSSO0O
ZVSS00
ovssoo
46 S500
265500
w6esosS00
966500
b6SS00
281

<!-- source-page: 289 -->
## Page 289

C87
Kok KR
KK
RKO
kkk kk
Ok
kkk
Ok kk kkk ok kkk kk
kk kk ke
dc.
dc.
de.
de.
OOSSEC
OOSSEE
OO55F2
OOSSF6
OOSSFA
OOSSFE
005602
005606
0O0560A
OOS60E
005612
005616
0O561A
OOS61E
005622
005626
00562A
00562E
005632
005636
OO563A
00563E
005642
005646
ANOCAR
VUIOFTA
OOS64E
005652
005656
OO565A
00565E
005662
6028
00007ACO
00005328
OOOO5STIA
0000578E
00005794
000057A0
OOOOSTER
OOO0057F6
000062D2
000063B0
00006468
00005B64
00006B74
00007138
00007440
00007468
00007BC6
00006062
O000614A
00006602
OOOOSA4E
00009024
OOOO6AAA
ANAHORAD
VVUVVOAIY
QO0007BF2
OOO006CE6
00007162
0000719C
00007A30
OO0007A9A
a
ee
ee
=
40
$7ACO
$5328
S577A
$578E
$5794
$57A0
SSTEE
$57F6
$62D2
$63B0
$6468
$5B64
$6B74
$7138
$7440
$7468
$7BC6
$6062
S614A
$6602
SSA4E
$9024
S6AAA
56A390
$7BF2
S6CE6
$7162
$719C
$7A30
S7TA9A
Addresses
of
the
TRAP
#14
calls
Number
of routines
0,
i,
2,
3,
4,
5,
6,
7,
8,
9,
10,
1i,
12,
13,
14,
15,
16,
17,
18,
19,
20,
21,
22,
23,
24,
25,
26,
27,
28,
29,
initmouse
rts
physbase
logbase
getrez
setscreen
setpalette
setcolor
floprd
flopwr
flopfmt
getdsb
midiws
mfpint
iorec
rsconf
keytrans
rand
protobt
flopver
dumpit
curscont
settime
gettime
bioskeys
ikbdws
jdisint
jenabint
giaccess
offgibit
SuTysyqng ISiy
sjeuiojuy [LS LWejyy

<!-- source-page: 290 -->
## Page 290

Atari ST Internals
First Publishing
qand3no
‘/qnouceq
eTqey snqeqs
snqejqs
andqno
3e5
‘ jeqs0oq
aTqey ynduy
qandut
‘uTuosq
eTqey snqeis
sTqzeqs
jandut eb
“Ae ysucog
apow JosfTAtedns
ut
aut ANor
aynosexy
yoeys
wory
sseippe
4ey
apow Jostaaedns
uy euTynor
‘ooxedns
seeqund
’6¢
oexedns
‘gE
TQAM
‘LE
yTqqyad
‘9¢
aqzeirqy
‘GE
SOBAPAAT
‘VE
qidjes
‘EE
punosop
‘ZE
TaWTAGX
‘TE
atazbuo
‘o¢
OV‘ (Dd) d49G$
eet
9S00VATY 9V9S00
SPELLS PETES
TST EPecrr eee eT eC eee Ler eS ee
SS
Se
ee ee
SS
vw9acs
erg
F009
¥Y9S00
OW’ (Dd) 949965
eeT
PROOWHTP
OV9S00
PoCPCTTT CSE TEPC
C SPELT
PCE PTL eS ee Le. eee See Se ee
Ww9Gs
eigq
¥O09 369500
ov‘ (Dd) aD9G$
eT
TEOOVATY W69S00
KK RR
KO
OR LOR OE
OE EL
KOK
OR OLR OR ROR KOE
OR EEF
Ww9cs
e1gq
OTO9
869500
ow’ (Dd) 9496S
eeT
OZOOWHTP
¥69S00
DOOR
KOR
OR OR OR
UR
ACU
IE CE AE IE OK
(ow)
duf
Oddy
2695900
ow’ (4¥)b
T*eaow
po00d90z 389500
ROR RO
OR OR
LOR ROR OE LOR ORE
OR
OE
OR
OR OE
OR
OR
OR OE OF
oTS8s$
Top
DT8S0000 W89S00
agass
T°9P
H89G0000 989500
bmSSS
T*9p
bPSSO000
289500
76QL$
T°9op
76GL0000 AL9GOO
ZEOLS
T°9p
ZEDLOOOO WL9S00
PSOLS
T°9p
BSOL0000 919500
OZOLS
T°9P
OZDL0000 £9900
D09L$
T°9p
90540000 A99G00
V8dds
Top
V8dL0000
V¥99S00
PLYLS
T°9p
PLYLOO0O 999500
283

<!-- source-page: 291 -->
## Page 291

Atari ST Internals
First Publishing
$q2i
snqeqs
IdIW
snjejs paeoqkay
snyeys
ajTosuop
sn3eqs
Ze?
Sd
snyeqs
soTuoiquep
snqeqs
yndyno
Siu
Siu
qndut
IdIW
qnduT
eTosuog
qandut
zez
su
qazod
fTeTTeired
qndut
sila
SLY
snqeqs
IdIW
snqeqs
aeTosuoD
snqeqs
¢cez
Su
sa
stqeqs
qndul
auTyNoI aqnoexg
auT
NET
ay}
Jo
sseippe
4ag
p
Sout
qequnu
soTAep
4385
4noucg
8ZESS
bags
wdo9$
9bags
9699$
g99$
T*op
T'2p
T'op
T'2p
T’op
T°op
82£S0000
87a90000
vd90000
9'd90000
96290000
96990000
V49S00
949500
249500
da9 S900
Wd9s00
949500
PoCETET TTT TTT EC EST ETE SSS
T
SET
T ESS
L SLES
e Lee Se
ee ee
acess
BZESS
pvags
otag$
9809$
DEDIS
Top
T’op
T’op
T°op
T*9p
T'op
8ceS0000
8ceso0dd
bWa90000
otq90000
98930000
9€990000
ca9S00
dd9S00
wa9s00
949500
209500
499500
OR ROOK
ORR
OL OOOO
OR
OR
ORO
UE ROL ROE ROR RE AOR OR OR EF
ezess
BzES$
esdgs
Wdo9$
OLO9S
BzESs
T'op
T’2p
T'op
T'2p
Top
T’op
82£S0000
8ZES0000
88890000
VWAD90000
O0LD90000
8zES0000
WO9S00
999500
299500
ag9so0
Va9S00
9a9S00
OK
EK
OE
RK
OE
OE
RE
KE KO
HOR
(ow)
ow’ (M°0a‘0W) 0
Od’ z#
Od‘ (LW) F
dul
[T° aaow
M'TST
M* 2A0OW
oddp
O0000L02
8bSA
POODAZOE
bagscoo
089500
AW3S00
WWV9S00
OCLC
E
Se SCC
See Lee ee ee
ee
2
Se
Se
eS
eS
ee
2
eee
284

<!-- source-page: 292 -->
## Page 292

Atari ST Internals
First Publishing
O1eZ
=
UMO
W
yjqbueT
uw
se
yqbuey
qoqueu snuTW
do quey
qaieqsu
se
joquey
YUTT
W reset
CW
ey.
JO
ssezppe
=
Jaaor
dw
OI9az
Tew
dW
GW eu}
Jo ssorppe
= TJu dy
zoyjdTiosep
Aiowep_
‘pusuL
adW MON
yootd
reqeweieg Aroway
‘qduyje9
ll
aitusqy
se ydeooy
Jes vay
‘aaT
eben
yoeqs
worg
sJaqoweized
4e9
snqeqs
qgtus yb
“azTUsy
snjejs paevogkay
‘3zTUS
JojoeA
ATq Wb
“sy ATqazd
setddo[y
eatqor
yeh
‘dewaiq
qYnoyno
TIOSY
qndjzno paeogksey
qyndqno
IdIW
qandyno
eTosuoD
yndqno
zez
Su
qndyno
soTuozqUseD
and no
(TW) eT
(tw)
8 ‘oa
od’ (Sw) Zens
0d’ (SY) 9EbS
(TW) b‘ (SW) ERS
(Tw)
(OW)
8 ‘TY
(OW)
(ov) ‘TY
Tw‘ (GW) a8Ps
OW
(LWP
Tato
T° aaou
T'qns
T* saou
T’ aaou
Tato
T° aaow
Tato
T*eaow
PeT
T* saow
D000ENCH
so0d0drec
ce bodvose
9eb0dz0~
bOOOZEROCIEZ
T6cp
B0006bTZ
pOOO8WCP
6802
dsvodder
70004902
&SLS00
0SLS00
ObLS00
8bLS00
7PLSOO
O%LS00
DELSO0
BELSOO
9€LS500
ZELSOO
azLS00
PoC
CT STE TET eC ET STS PES PTET LEST Se
LSS eee SS
ee eS Se
(sv) acws ‘Td
DeZLS$
Ta‘ (Lv)P
oa‘ (sv) asws
0g ‘0#
sya
q*aaow
qyuq
M*aAo0ul
q* aaow
T*baaow
SLap
asvotPral
bod9
DOOOACCE
asvodqzot
OOOL
92LS00
82LS00
9@LS00
ZCLSO00
aTLSO00
DTLSOO
OLR
OO
OR
OR
OR
IR
EE IE
OE OE OR IEC
OO IO HOE OH
0d’ (SW) ZObS
sqI
T° aaouw
SLab
70'0ac0~
YTLS00
9TLS00
or
Cer err TTC TETerrrereLe re rele. 2a Ss
SS eee ee
zaves
2D99$
wsd9$
aaves
AWO9S
padgas
T'op
T'9op
T°op
T'9p
T'9p
T*op
zavso000
99990000
wsd90000
aqvso000
aAV990000
'qd30000
ZTLSOO0
qOLsoo
WOLSOO
90LS00
ZOLS00
3A9S00
DOR OR OK OR OR ROKR UR ORE ORO RE OR
OE
OE YOR
ROE
OR RO
OR
OE
285

<!-- source-page: 293 -->
## Page 293

Atari ST Internal:
First Publishing
UOTANTOSeT
o@pTaA eb
‘zaxzje9
pe
sq
A 4e5
sseippe
oapta TeoTboT
‘aseqhoy
0d
UT sseippe oapta
Taseqq
yeseaqq
ssoippe
ooepta
[TeotsAyd
‘aseqsAud
su IWwT ey
SPUODSSTTTTW
UT ONTeA ASUT
‘TeOYOTL
IOWeA
39S
jes
4, Uuop ueyq
‘eat ebay
IOJO2A MAN
0d
OF AORD9A PTO
IOJO9A PTO
ayy
JO
ssairppe
yay
OW
4P98TD
sseippe
sjTenbe
p7
sauTl
IequUNU TOJDSA
Yay
JO4D8A UOTAdaoKS
Jas
‘/Oxayes
0a’0#
T° beaow
QOOL
F6LS00
MR
ROK OR OR OE OL
OE
RO
OE KORE KR
OK
KK
sya
GLAb
26LS00
oa’ (GW) abps
T° eaow
abpodzo~
Agiscoo
FERRO
OR OOO ORE OOO
ROR ORR
OUR
UR
OO OC
ERK
sa
SLAP
381500
od’s#
T°TST
881A W8Lso0
Od‘€028dddd$
q*aaou
E0CBAATIEEOT
PBLSOO
Od‘8#
AM*TST
8PTA Z8LS00
Od‘lo¢@8d4add$
gq" eaow
TO784dId6EOT OLLS00
Od‘o# T*beaow
000L WLLSOO
Pee ST SP eTT CECT ESC CSCC SS CSCC STS SESE
S CSET SSL eS See)
sj1
SL4b
8LLS00
Od‘ (Su) 7hr$
M*SAow
ebVOdZOE
PLLSOO
od
T*aqo
O8¢b
ZLLS00
RK KK RO
OE LO
OR
OR OO
LOR OKO OO
ORE ORO ROOK OE
sji
GLAUb OLLSOO
(ov) ‘Td
T° eAaow
T80Z A9LG00
OLLSS
yuq
ZOG9 292500
Ta‘(ivW)9
T° eaou
90004772 891500
od’(ov)
T’eaow
OTTO? 994500
ow‘ (M"00’0¥) 0
Pat
OOO00AT
Z9LS00
ov ‘OW
T’qns
89DT6
094500
od’z#
=A“ TST
8hSA ASLSOO
Oa‘ (LV)b
Mm eaow
PpOOOAZOE WSLS00
Peer eeee ee eeCeSCCE LOCC
CeCe
Se See eee
eee eee.
sqi
SL4b
852500
286

<!-- source-page: 294 -->
## Page 294

L8¢
005796 102D8260
move.b
SFFFF8260(A5)
,DO
00579A C03C0003
and.b
#$3,D0
OOST9E
4E75
rts
FOI
KO ROI
II
IO IO
a
ok dO
ako
kok
oe
OO057A0
4AAFO004
tst.l
4(A7)
OOS7TA4
6B06
bmi
S57AC
OOS7TA6 2BEFO004044E
move.l
4{A7),$44E(A5)
OO57AC 4AAFO0008
tst.l
8(A7)
0057B0
6B10
bmi
$57C2
0057B2
13EFOO09FFFF8201
move.b
9(A7),$FFFF8201
0057BA 13EFOO0AFFFF8203
move.b
10(A7),$FFFF8203
0057C2
4A6FO00C
tst.w
12 (A7)
0057C6
6B24
bmi
$57EC
0057C8 1B6FOOOD044C
move.b
13(A7),$44C(AS)
OO57CE 6100FD74
bsr
$5544
0057D2 13ED044CFFFF8260
move.b
$44C(A5),$FFFF8260
OOS7IDA 426D0452
clr.w
$452 (AS)
OOSTDE 4EB90000F6C4
jsr
SF6C4
OOS7E4 33FC000100000452
move.w
#1,$452
OOSTEC
4E75
rts
FO
IO
IO
IOI
III II
I
I
III II I IOI III IOI II I
IK KKK KK
OO57EE 2B6FO0004045A
move.l
4(A7),$45A(A5)
OO57F4
4E75
rts
FOO
TO TO
FOI
IOI TO RI IR II
IO
OI IO IIR
IO RO
I IO
II
a
IK
OOS7TFE 322F0004
move.w
4(A7),D1
OOS7TFA D241
add.w
Di,D1
OOS57FC C27CO01F
and.w
#S1F,D1
005800
41 F9FFFF8240
lea
SFFFF8240,A0
005806 30301000
move.w
0(A0,D1.w),DO
Load
shiftmd
Isolate
bits
0
and
l
Setscreen,
set
screen
address
Logical
address
Negatice,
don’t
set
Set
v bs
ad
Physical address
Negative,
don't
set
Dbaseh
Dbasel
Video resolution
Negative,
don't
set
Sshiftmd
Wvbl,
wait
for
VBL
Sshiftmd to shiftmd
Vblsem,
VBL disabled
Initialize
screen output
Vblsem,
permit VBL again
Setpalette,
load
new color palette
Set colorptr
(execution
in VBL)
Setcolor,
set
single color
Color
number
Times
2
Limit
to valid number
Address
color0
Get
old color
Surysyqnd }Si1y
sjeui9juy TS eV

<!-- source-page: 295 -->
## Page 295

887
OOS80A CO7TCOT7?
and.w
#$777,D0
OOS80E
4A6F0006
tst.w
6 (A7)
005812
6B06
bmi
$581A
005814
31AF00061000
move.w
6(A7),0(A0,D1.w)
OOS81A
4E75
rts
KKK RR
ROK kok
kok
ok
kok ok kkk ka aKa KKK RK
KR
K KK aK KK AK
KE KEK
OOSB1IC 207AFTFE
move.1
$5014(PC),A0
005820 009087654321
emp.1
#$87654321,
(AO)
005826
660E
bne
$5836
005828 B1F90000042E
emp.1
$42E,A0
00582E
6C06
bge
$5836
005830
4290
clr.l
(AQ)
005832
6000F7EA
bra
SSOLE
005836
4E75
rts
KKKKKARKKKKK KKK KK KKK KKK KR KR Kk
Kak RR Kk
KK Rk
KK
005838
6102
bsr
§583C
00583A
4E71
nop
00583C 23DF000003C4
move.1
(A7)+,$3C4
005842
48F9FFFFO0000384
movem.1 DO-D7/A0-A7,$384
OOS584A
4E68
move.l
USP,A0O
00584C 23C8000003C8
move.l
A0O,$3C8
005852
303C000F
move.w
#SF,D0
005856 41F9000003CC
lea
$3CC,A0
00585C
224F
move.1l
A?,Al
00585E
30D9
move.w
(Al)+, (A0)+
005860
51C8FFFC
dbra
DO, $585E
005864
23FC1234567800000380 move.1
#$12345678,$380
O0586E
7200
moveq.1
#0,D1
005870
1239000003C4
move.b
$3C4,D1
005876 5341
subq.w
#1,D1
Clear irrelavant
bits
Test
new
color
value
Negative,
dont
set
Set
new
color
Puntaes,
clear
AES
and restart
os magic
Already there
?
No,
done
In
ROM
?
Yes,
do nothing
Clear magic
To
reset
Term,
interrupt
running program
PC
on
stack
Save
PC including vector number
Save registers
USP
Save
16 words
Save
area
Get
SP
to
Al
Save
word
from stack
Next
word
Magic
for
saved registers
Get vector
number
to
D1
Convert
in dbra counter
Surysyqng 3SI
yeuioUy TS wey

<!-- source-page: 296 -->
## Page 296

687
005878
OOS87A
005884
005888
OO588A
00588C
005890
005896
00589A
00589C
00589E
0058A4
OO58A6
O0O058AC
OOS8AE
0058B0
0058B4
0058B8
0O058BC
O0OS8BE
0058C0
0058C4
0058C6
OOS5S8CA
OO58CE
0058D0
0058D4
0058D6
Oo58DA
6116
23FCOQOO0005FCO00004A2
3F3C0001
42A7
4E41
6000F790
LEZ 9FFFF 8260
CE7CO003
DE47
4280
1039FFFF8201
E148
1039FFFF8203
E188
2040
DOFB702A
43FA0038
3C3COQ00F
3401
2448
3A3B7020
S1CDFFFC
SICAFFF4
5449
D4FB7016
204A
51CEFFE4
4E75
bsr
move.1
move .W
elr.l
trap
bra
move .b
and.w
add.w
clr.1
move.b
lsl.w
move .b
lsl.1
move.1l
add.w
lea
move.
move.
move.
move.
f£egre
«
move.
dbra
dbra
addq.w
add.w
move.1
dbra
rts
$5890
#$5FC,S$4A2
#1,-(A7)
~(AT)
#1
SSOLE
OI IO
I IO
IOI
IC III IOI CII IO IOI
ICICI
a
a Ia IK
Ie
SFFFF8260,D7
#3,D7
D7,D7
DO
SFFPFF8201,D0
#8,D0
SFFFF8203,D0
#8,D0
DO, A0
$58DC (PC,D7.w)
, AO
$58EE (PC) ,A1l
#SF,D6
D1,D2
AO, A2
$58E2 (PC,D7.w),D5
(Al), (AO) +
D5,$58C4
D2,$58CO0
#2,Al
$58E8(PC,D7.w)
,A2
A2,A0
D6, $58BC
Output appropriate
#
of
'‘'mushrooms'
Reset
savptr
for BIOS
Return
code
for error
Terminate process
GEMDOS
call
If
return,
then
reset
Write
'mushrooms'
on
screen
Shiftmd,
get
resolution
Isolate significant
bits
Times
2
for word access
Dbaseh
Dbasel
Screen
address
To
AO
Plus
offset
for middle
of
screen
Address
of
bit pattern
for
"mushroom"
16 raster lines
Save pointer
to start
of
line
Number
of words
(screen planes)
Write
a raster
line
A
complete mushroom
The next
on the
same line
Next
word
of
the
bit pattern
Next destination address
Restore
start
of
the
line
Next
raster
line
Surysyqng 3s.
sjeusayuy LS Wey

<!-- source-page: 297 -->
## Page 297

Atari ST Internals
First Publishing
T-
,swoorzysnw,
urzeqqed
31¢
uoTantTosel
yOTtH
uOT4ANTOSSZ PTW
uoT ANTOSsr MOT
yqbueT euTT
uotantosaz
yStH
uoT 4Nn[Osel PTW
UOTANTOSel MOT
soueTd
uaeios
Jo
7Tequnn
uoTANToOssel
ySTtH
uoTantosel
PTW
uoTINTOSel
MOT
Za4Uuso
UuseTDS
OOOOOTOOTOOTOOO0NS
M*Op
0260 306500
OOOODOTOOTOOTOO00%
M*op
0760 Y06S00
OOOOOTOOTOTOO000S
Mop
O2S0
806500
OOODOOOTOTOTOOND0S
a"op
ObSO 906500
COOOOOTOOOTOO0O0NS
Mop
ObPvO
bO06S00
OQDODOTOOOTONDDNNS
acop
ObFO
c06S00
OODODCOTOTOCOSSOS
a°op
08é0 006S00
OOOTOOOTOTOOTTOOS
M°Op
88cE AABSO0
OOTTTITTOTIOOITO%
M*op
9499 DABSOO
OTTOTTTTTTTTTOTIs
Mop
9440 WAI8so00
OTOTTTTTITOTTIOTS
a" op
Wddd 848500
OTOTETTTTTTOTTOTS
MOD
VALE 948500
OOTOTITTITTITOTTTOS
M°op
bali
bassoo
OOOTTITTTTOTTIOOS
M*Op
84d
cAssoo
OOOOTTTITITTTOO0%
a"op
OddT
048500
OOOOOOTTTTTOO000S
M°op
09L0 dassoo
MRR ORO
OE ROR LO
OE OR OO
OE
OR KO
LEE
IR ROR
OR RF
08
Mop
OSg00 948500
o9T
M°OD
owvoo WdAgsoo
O9T
Mop
OWOO
848500
PoeT eC CCE CC eT EC EST SST STC
PTET ST EL eS
ee
eS
ee SS
0)
aap
0000 348500
T
M*Op
TOOO
¥ABSOO
€
M" Op
€000
2dgsoo
ORK KOR
OR ROO OO
OE
OE OR
OR
ORR OER
OR OK OE
OE
OK
08x00¢
Mop
O8Hde
0ABS0O0
O9T*O0O0T
A
oOp
Osae
AGsSOo
O9T*O00T
M*Op
Ogade
Da8S00
OOK KO
OR
OK OKO
OO
OR
OR
KKK
OE KEE
290

<!-- source-page: 298 -->
## Page 298

Atari ST Internals
First Publishing
aweueT
ta
aweuyyed
GY 1PeTO
ssaippe uinqoy
Dud‘
x, BWeUSsTTJ
Jo
sseippy
aueuyjed
jo
sseippy
wezboid
e&
aynoexe pue
jieqs
‘o4ny
auTyNor
of dune
yorqys
vo TUT
APH
UOTIeZTTeTATUT
ASTP PAPH
soqkq
g
2XeN
so yhq
g
Adoo
saykq
ZIG
=
8x (Ttl€9)
ssaippe
uot }eutqysseg
ssaippe
eornes
Jojoas
ystp
Adoo
‘Adoojsedg
(SW) PpO9S‘TW
T° eaow
pO906baC
296500
(S¥)009$‘0W
T*eacu
OO908PH2 AS6S00
cu ‘Gy
T*qns
dod6
296500
DaG$4+(L¥)
 T*eacu
DASOOOOOAdE?
9596500
TW‘ (Dd) OF6S$
BeT
DdddAVAEP
2S6S00
ow’ (Dd)
€7S$
eeT
VWaddIVIty
476Ss00
rrr rTrTeEeTTTTTCCLOC
OLE
C SELES SSeS ee EES Se
OFAADAVESLOSPECT 9F6S00
04, 9Ud* x1
g*op
OOLPCSOSACYe OFGS00
1TOLOAWT.
g"op
OGHPPSSSTRPOIS VE6S00
CETTE TTT CET eT eT TT ET SLICES eS LCP
e LSS TESS SS
ES Se Se tS
OdAAdDAVES
“BLOGTETTS
T'op
sa
GLU’
8E€6S00
(LW) -‘vW9bS
T° eau
¥V9POOD00G6ESZ Z€6S00
Ore re re eee TTP
e
Pere Le tes See
2
SS Se
ee
sqi
SLab 0€6S00
DT6S$ ‘0d
eiqp
AAIIBOTS DZ6S00
+(Tw) ‘+(0W)
q° eacw
gdzl vz6soo
+(Tw) ’+(0W)
q°eaou
gdqzt
8z6soo
+(Tw) 4+(0W)
q'aaou
edqazl
9726S00
+(TW)
7+ (OW)
gq’ eaou
8azZTt
PZ6S00
+(TW)
‘+ (OW)
q° Saou
gdzt
z26s00
+(Tw) ‘+(0¥)
q* Saou
8dZT
026500
+(Tv¥)
4+ (OW)
q’aaou
gdzil At6S00
+(Tw) ‘+(0¥)
q’ Saou
8dZ2T DT6S00
od‘aes#
M* sao
JEOODEDE 816500
Iwi (L¥)8
T'eaow
800049722
P16S00
ow‘ (LV)
b
T*eaow
FO00d902 OT6G00
OR KOR RRO
EO YOR
LO
OR
ROR
RR
ORE RK OR
OR OR
OK
OE
NOOOTOOTOTOOTONNS
Mop
O6¢T
FO06S00
291

<!-- source-page: 299 -->
## Page 299

C67
005966
OOSS6A
905970
005972
005974
005978
OO597A
00597C
OOS97TE
005982
005986
005988
00598C
00598E
005996
005998
00599A
00599C
0059A0
0059A4
0059A6
OO59AA
FOI
IOI
IOI IOI
TO
I
IO
I
ok
a a
kkk
ak
0059AC
OO59AE
0059B2
0059B4
OO59B6
0059B8
0059BC
0059C0
202D04C2
323900000446
0300
6736
41 FAF977
2F08
2F08
2F08
3F3C0005
3F3C004B
4E41
DEFCO0010
2040
217C000059AC0008
2F0B
2F00
2F0B
3F3C0004
3F3C004B
4E41
DEFC0010
4E75
42A7
3F3C0020
4E41
SC4F
2840
2A6F0004
4FEDO100
2F3C00000100
move.1
move .w
btst
beg
lea
move,
move,
move,
move.
En
a
od
move.
trap
add.w
move.1
move.1
move.1l
move.1
move .1
move .W
move .W
trap
add.w
rts
clir.1
move .W
trap
addq.w
move.1
move .1
lea
move.1j
$4C2 (AS) ,D0
$446,D1
B1,bpo
$59AA
$52ED (PC)
, AO
AO, -(A7)
AO, -(A7)
AQ, -(A7)
#5,~(A7)
#$4B,-(A?7)
#1
#$10,A7
DO, AQ
#S$59AC,
8 (AO)
A3,-(A7)
DO, -(A7)
A3,- (A7)
#$4,-(A7)
#$4B,-(A7)
#1
#$10,A7
-(AT)
#$20,-(A7)
#1
#6,A7
DO, A4
4(A7),A5
$100(A5),A7
#$100, -(A7)
Drvbits,
vector
with
active drives
Bootdev
Drive
active
?
No,
done
Pointer
to
null name
Environment
Command tail
Shell
name
Create
PSP
Exec,
load program
GEMDOS
call
Correct
stack
PSP
PC
for
auto exec program
Null
string
PSP
Shell
name
Exec,
load program
GEMDOS
call
Correct
stack pointer
Start
auto
exec program
super,
enter supervisor mode
GEMDOS
call
Correct
stack pointer
Saved stack pointer
Base page address
Space
for base page
$100 bytes
Surysyqng Iss]
s[eusayUy LS Heyy

<!-- source-page: 300 -->
## Page 300

€67
0059C6
0059C8
0059CA
0059CE
0OS59D0
0059D2
0059D4
0059D6
0059DA
0059E0
0059E4
0059E6
OOS9EC
0O59FO
0059F2
0059F4
00S9F6
0059F8
OOS9OFA
OO59FC
00SA02
OOSA08
OOSAOE
005A10
005A12
005A14
OOSA1A
OOSAIC
OOSALE
005A22
0OSA26
OOSA2C
2F0D
4267
3F3C004A
4E41
SC4F
4A40
666A
3F3C0007
2F3900000600
3F3C004E
7E08
487900000608
3F3CO01A
4E41
SC4F
4E41
DEC7
4A40
6644
207900000600
247900000604
43F900000634
12D8
B5C8
66FA
41F 900000626
12D8
66FC
487AF8CD
487AF8C9
487900000634
4267
move.1
clr.w
move .W
trap
addq.w
tst.w
bne
move .W
move.1
move .W
moveq.1
pea
move .W
trap
addq.w
trap
add.w
tst.w
bne
move,1
move.1
lea
move .b
cmp.1
bne
lea
move .b
bne
pea
pea
pea
clr.w
AS,-(A7)
~(A7)
#S4A,-(A7)
#1
#6,A7
DO
$5A40
#7,-(A7)
$600,-(A7)
#$4E,~(A7)
#8,D7
$608
#$1A,~(A7T)
#1
#6,A7
#1
D7,A7
DO
$5A40
$600,A0
$604,A2
$634,Al
(AO)
+, (A1) +
AO, A2
$5A0E
$626, A0
(AO)
+, (Al) +
SSALA
$52ED (PC)
$52ED (PC)
$634
~(AT)
Start
of
the memory
area
Setblock
GEMDOS
call
Correct
stack pointer
Error
?
Yes
R/O,
hidden
and system files
Filename
Search
first
Bytes
for
stack correction
DMA address
for
DOS
Setdta
GEMDOS
call
Correct
stack pointer
GEMDOS
call
Correct
stack pointer
File
found
?
No
Pathname
Filename
Auto
name
Copy path part
Name
from DMA buffer
Append
to path
Null
name
Null
name
Filename
Load
and start program
Surysyqng 38114
sjeusayuy 1S Hey

<!-- source-page: 301 -->
## Page 301

Atari ST Internals
First Publishing
uoTyeinbTyuoo Jequtad
4a9g
Jaqutod ysew 1veTD
aqqetTed
IoToo
oj
ssserzppy
oraz
03
AYUHTA puy
qJOT
qy6Teay
ueaios
4a5
UIPTM UBEIOS 4a
uoT4n{osar
usastOs
AOJ
aTqeyI
Z SoUTL
BARS
uOT4yNTOSeI
usaeios
‘pwqasTuss
TION
072
398SFFO
qndyjno
useios
‘pe
sq
a
GV
A2P98TD
Adoopiey
‘dupiss
bTydunp
izeaeTo
Adoopiaey
S{zdunp
2es
Adoopiey
userzos
‘4Tdwng
ssoippe
uAinjal
prot
aNTeA
4zeYS
OF
YORq AaquTOd
yore As
STTF
FXON
qxou yorras
aaqutod yoeqs
120g
saqdg
Jaqyutod
yoeqs
4oerIOD
T1Ie2 SOGWNAD
weiboid
peotT
‘/oaxg
Ta‘ (sw)osvs
= M*eaou
(GW) G99$
AMATO
(GW)999S‘OPZ84aS#
T° eaocw
(S¥)099$
M*2TS
(GY) aS9$
MATS
(sv) 999$‘/(M°00‘0V)9
M*eAcU
(cy) ¥cos‘(M°Od‘0¥)0
AM" aAoWw
ow’ (Dd) pass
eaT
oqd‘oq
=M*ppe
(Sv) z799$‘0d
M*enou
Od’ (S¥)OPpbS
q°eacu
od
M°ITO
(SW)8S9$
MATOS
(SW) pG9S‘(GW)Apb$
T° eaow
cv‘Sv
- T’qns
O8WOdeZE D6VS00
A990097F 86YS00
99900PCB8AM00OLEZ
ObVSO00
099009¢h D8VS00
aAS90d0972b
88VvS00
DS9O90000LHE
¢BYWS0O0
weannnnndlde QLYSOO
WSOOWHTP
8LYS00
Opod 9LVSO00
c9900bPHE
cLY¥SO00
ObbOdcOT AVWSOO
Ob2b
O9NSO00
8590097 89NS00
PS90APPOd9ES
C9VSO00
dod6
09¥S00
ORO
RO KORE
ROR OE
OR OK
ER ORR RR ORE OR YO ORR OF
sql
qqgp$‘T-#
M°saow
og¥ss
isgq
ages
MIT
SLap asvsoo
AAPOCOOOddAAOAEE ISVSOO
WOT
&SYSO0O
aaPoo00deL
2b AbWSOO
DO
OR
OO OE ORO
EO
ORR OR OR ORO
OR OREO
KOE
sqz
(LV) -‘OdG$
9 T* aAou
LW‘WCHES
eet
9465S
e1g
(LW) -‘dp$#
MB aAoUW
La‘z#
T° beaow
LV‘OTS#
M*ppe
1#
deiq
(LU) -‘aps#
M*aaow
GL4b
OFWSOO
DASOOOOO6EdZ
BPYSOO
Wedeo000eddb
OFYSOO
9¥09
HEVSOO
ApOOOEAE
VEVSOO
cOdL
BEVSOO
OTOODAEd
bEVSOO
Tbay
cewsoo
adpoooede
acvsoo
294

<!-- source-page: 302 -->
## Page 302

Atari ST Internals
First Publishing
(jaeyum Astep
rOTOS
uosdq)
(xTaqew zoTOO
uosdq)
(Teeua Astep M/a uosdg)
XTijzew M/a uosdy
(é
Teeum Astep
A10TOO
TyWLyY)
XTAqew
AoToo TUL
Teaym Astep M/d IXVLY
xTTq\eW M/d
ITYVLV
(pejuewatdut
jou
=
[-)
sedAQ
rzequTiad
sqybtay
ueeizo0s
SUIPTM UseIDS
Adoopiey
10OJ
aTqeyz
Jeqjoweiedg
Iajutod yoeqs
4o9etI0D
Adoopiey wiojisg
XOOTC Aeqjewezed ayy
jo ssaippy
doopziey
zojJ
saes puy
aTqey worly
quewubtsse
4a9
adky
zayutTaid
ayzejTos]{
Adoospiey
2OJ
saePs
puy
a jeTosy
TeTzes
/
TeTTeied
uot yeanbtjuoa
AJequtid 489
GAPS PUY
Tq
a VepTos]
apow Ayttenb
/
Asal
q°op
q*op
q‘op
q*op
q'op
q'op
q°op
q'op
da
dd
dd
£0
dd
TO
ae)
00
Lavsoo
9AYSOO
Gav¥Soo
bawsSoo
eavsoo
7aAvS00
Tavsoo0
OaVSOO
MRR ROOK ROE ORR OR OR OE
OR
OR OR OR EE ERE
ERE
00F ‘007 “002
09 ‘089 “0ZE
M°op
M°op
061085008900
08Z008Z00FTO
gavsoo
bawsoo
SORE CST TCT TT TTT
ES TT STE STL
eS
ee
ee
LW‘ bt
z6aL$
(GW) BS9S
w99$ ‘0d
od‘ (m° Ta ‘Od) OaNS$
Ta‘L#
(S¥)999$
‘0d
od‘ t#
od‘ b#
od‘ta
ta’ (Gv) O8u$
(S¥) 999$ ‘Id
Ta‘T#
Ta ‘e#
sya
mM*bppe
1isq
Pad
4° BAOU
q*aaow
aA*pue
M* QoAOUW
M*pue
M*IsT
M* SACU
M* OAOU
M* 3AOU
M*pue
M*IST
SLAG
Aves
PIZZOOTY
bS90098b
V9SODDQ00DEE
OcoTaEeNt
LOOQ0DLZO
O9900PEE
TOOODLOO
8bed
TOOE
OBVodeze
POIOTPAE
TOQ0ILEZD
6094
cavsoo
oavsoo
DOVS00
goVvS00
7OWS00
aagvsoo
Wavso0o
9qaV¥S00
cadvS00
OdVS00
avwsoo
Wvv¥Soo
9¥WS00
CUWSOO
OVWS00
295

<!-- source-page: 303 -->
## Page 303

967
eK
KOK Ok
i
kk
ie kkk
kk ak ek
ke ie dee
OO5AE8
OOSAEC
OOSAFE6
OOSAFS8
OOSAFE
OOSB04
OO5B08
OCSBOA
005B10
005B14
0OS5B16
0O5B18
OOSBLA
ooSB1Cc
OOSBIE
005B22
0O5B24
005B26
OOSB2C
005B32
005B34
005B38
0O5B3A
005B40
005B42
0O05B44
OOSB4A
OO5B54
OO5B58
OOSBSE
0OSB60
4E56FFFO
23FC0000012C000025F6
4240
33C0000004A6
33C000004692
3D40FFFE
604E
207CO00003E2A
326EFFFE
D1ICcgY
4210
4257
4267
4267
3F2EFFFE
42A7
42A7
4EB90000628C
DFFCOOQOO000E
3F00
306EFFFE
pics
D1FC00004910
309F
6610
5279000004A6
00B900000003000004C2
S26EFFFE
OCEEOOO2FFFE
6DAA
4E5E
link
move.1
clr.w
move.
=
move.
=
move.
=
bra
PR
move.
move .wW
add.
elr.
clr.
elr.
clr.
move .w
elr.
clr.
£££
7
a
jsr
add.1l
move .W
move .w
add.l
add.l
move.w
bne
addq.w
or.l
addq.w
cmp.w
bit
unlk
A6, #-16
#300, $25F6
DO
DO, $4A6
DO, $4692
DO,
-2 (A6)
$5B58
#S3E2A,A0
-2(A6),Al
Al, AO
(AO)
(A7)
~(AT)
- (AT)
~2 (A6)
,- (A7)
-(A7)
-(A7)
$628C
#SE,A7
DO,
- (A7)
~2 (A6) ,A0
AO, AO
#$4910,A0
(A7)
+, (AO)
SSB54
#1,54A6
#3,$4C2
#1,-2 (A6)
#2,-2 (A6)
SSBOA
A6
hdv init
maxacctim to
300*20
ms
nfiops
Start
with drive
A
Address
of
the
dsb
Drive number
Drive number
flopini
Correct
stack pointer
Save
error
code
Drive number
Error
code
Drive
not present
?
Increment nflops
drvbits
Increment drive number
Not
yet
2
Initialize next drive
Surysyqng ISL
seusaju] [S Ley

<!-- source-page: 304 -->
## Page 304

L67
OOSB62
4E75
rts
GOI
IO III
IOI IG
IO
I
IO IO IOI
II
IIR TOR I
IC III I
OO5B64
005B68
OOSB6A
OOSBEC
4ES6PFFC
4280
4ESE
4E715
Link
AG, #-4
eclr.l
DO
unlk
A6
rts
OR
IORI
OOK IR
ICICI IO
IOI IO III II IO I
IOI
I IK
OOSB6E
005B72
005B76
OOS5BIC
OOSB7E
005B80
005B84
005B88
OO5B8A
OO5B8C
OOSB8E
005B94
O0S5SB96
OOSB9A
OOSB9C
OOSB9IE
OOSBA2
OOSBA6
OO5BA8
OOSBAE
OOSBB4
OOSBBA
OOSBBE
4E56FFF4
48E7070C
OC6E00020008
6D06
4280
60000192
302E0008
EB40
48C0
2A40
DBFCOOQ03E3E
284D
3EBC0001
4267
4267
3F3C0001
3F2E0008
42a7
2F3C000012BC
4FB9000062D2
DFFCO0000010
2D40FFF4
4AAEFFF4
link
Ao, #-12
movem.1 D5-D7/A4-AS, -(A7)
cmp.w
#2,8 (AG)
bit
$5B84
clir.1
DO
bra
$5D14:1n1:fp5
move.w
8(A6),D0
asl.w
#5,D0
ext.1
DO
move.1
D0O,A5
add.l
#S3E3E,A5
move.l
A5,A4
move.w
#1, (A7)
clr.w
~(A7)
clr.w
~(A7)
move.w
#1,-(A7)
move.w
8(A6),-(A7)
clr.1
~ (AT)
move.l
#$12BC,-({A7)
jsr
$62D2
add.1
#$10,A7
move.,l
DO,-12(A6)
tst.1l
~12 (A6)
getdsb
Zero
getbpb,
get
BIOS parameter block
Save registers
Drive number
<
2,
ok
Else
zero
Drive number
Timers
32
Plus
base address
Count,
read
a
sector
Side
0
Track
0
Sector
1
Drive number
Filler
Sector buffer
Read
sector
Correct
stack pointer
Save
error
code
And test
Burysyqng ISIy
sjeaioyay TS Wey

<!-- source-page: 305 -->
## Page 305

867
OO5BC2
OO5BC4
OO5BC8
OOSBCC
OOSBCE
OO5BD4
OOSBD6
OOSBDA
OOSBDE
OOSBE4
OOSBE6
OOSBEA
OOSBEC
OOSBEE
OOSBF2
OOS5BF8
OO5BFC
OOSBFE
005Cc00
005Cc06
005C08
005c0C
OOSCOE
005C10
005C14
005016
OOSC1A
005C20
005C24
005C28
005c2Cc
6C16
3EAE0008
202EFFF4
3F00
4EB90000555C
548F
2D40FFF4
202EFFF4
BOBCO00010000
67B0
4RAEFFF4
6C06
4280
60000124
2EBC000012C7
6100066C
3E00
670E
1€39000012C9
4886
CCTCOOFF
6606
4280
60000102
3887
39460002
2EBC000012D2
61000644
39400008
302C0008
5240
bge
move.w
=
move.
move .w
jsr
addq.1
move.
—
move .]
cmp.1
beq
tst.l
bge
clr.1
bra
move.1
bsr
move .W
beq
move.b
ext.w
and.w
bne
elr.1
bra
move .W
move .W
move .1
bsr
move .wW
move .W
addq.w
SSBDA
8(A6), (A7)
~12 (A6),DO
DO,
- (A7)
$555c
$2,A7
DO,-12 (A6)
~12 (A6) ,DO
#$10000,D0
$5B96
-12 (A6é)
SSBF2
DO
$5D14
#$12C7, (AT)
$6266
DO,D7
$5COE
$1209,
D6
D6
#SFF,D6
$5C14
DO
$5D14
D7, (A4)
D6,2(A4)
#$12D2, (A7)
$6266
DO,
8 (A4)
8(A4) ,DO
#1,D0
ok
?
Drive
number
Error
code
Critical error handler
Correct
stack pointer
Save
error
code
Read boot
sector
again
ok
?
Buffer+1ll,
bytes
per
sector
u2i,
convert
8086 integer
to
68000
int
Save bytes
per
sector
Buffer+13,
sectors
per
cluster
clsiz
Buffer+22,
sectors
per
FAT
u2i,
convert
8086 integer
to
68000
int
fsiz
plus
1
Surysyqng ISIN]
sjeuioyuy LS ejy

<!-- source-page: 306 -->
## Page 306

Atari ST Internals
First Publishing
QUT
00089
03
JebeqUutT
si0}0es UsppTy
Jo
3UT
00089
03 JebequT
yoezy rad
AUT
00089
03 2abequT
septs
jo
qUT 00089
03 azabaqut
$10jDas
FO
quT
00089
09 1ebequyT
setiqua Ajoqjoaitp
jo
useppT
yp
9808
3zAeAU0D
‘TZN
qzoequnu
‘g¢+ieyjng
odsp spletA
jdsp
souTtlL
soptsup
qdsp
9808
3aAeAU0D
‘Tgn
qrozoes
‘pz+rTsezTjNg
soptsup
9808
31eAU0D
‘TZN
zequnu
‘/97+TeyIng
Tounu
spTetA
zTstTo
Aq paptatd
oerjep
snuTtn
9808
37eAU0D
‘TZN
zequnu
‘g§[+79eyINg
Der yep
sprTetsz
zysjJ
sntd
ueTpl
sntd
2073e]
usTPl
SPTETA
ztsoea
Aq peptatad
ze Sout L
9808
3JTeAUOCD
‘TEN
Zequnu
/47+1eyjng
qZTSTO
SpTeTtaA
ZTSTO
sautL
@ZTSooI
dar\ej
(sw)
97 ‘0d
997295
(LW) ‘BaZTS#
(Gv) 270d
0d‘ (SY) bz
oa’ (Gv) 0z
(SW)
bz ‘od
9929S
(LV) ‘pazTS#
(sw)
oz ‘od
997Z9$
(LY) ‘90ZTS#
(pW)
pT ‘od
od‘ (pv)z
od
0d‘ (PY) 2T
9929S
(LY) ‘dOZTS#
(pW)
ZT ‘0G
0d’ (p¥)8
od‘ (pw)9
od‘ (pW) OT
(pw)
9 ‘0G
od‘ (f¥)
od
oa‘S#
9929S
(LV) ‘GOZ1S#
(pW)
’ ‘od
od‘ (pw)z
od‘ (#¥)
(pv)
OT ‘0d
M*aAou
Isq
T° saow
M* AOU
A*sTnw
M*aAoU
M*oAOw
Isq
T*saow
M*aAou
asq
T‘saou
M*aAou
MA‘ SATP
T° 4x9
a‘qns
1sq
T‘ eaow
M* 3AoU
M‘ppe
A’ ppe
A‘ 3AoU
M*S9AOU
M'SATD
T° 4x9
M°TSe
asq
T* eaaow
M*aAow
MA’ sTnu
M*aAoU
M*oaAou
VTOOOpaEe
adsooolg
gdztooo0oddc
9TOOOPHE
sTooddto
PTOOGZOE
BTOOOPEE
gasooot9
paz Tooooodae
PTOOOPEE
93S000T9
9azT0000Ddae
AOOOODGE
Z00004T8
0D8b
30009906
aASO001?
JOIZTONNOOdAC
SOO0OD6E
g000D900
90009900
WOOODCOE
90000P6E
Fats
0D8F
opda
77900019
qdzTodoood
ad
POOOOPGE
Z000DdTO
PLOE
WOOOCOVGE
WWOSO00
9¥9S00
O¥DS00
969500
869500
P69S00
069500
989500
989S500
789500
aLOG00
8L9900
6L9500
0495900
AIDGO0
¥99DS00
999500
099500
959500
859500
7S9S00
0S9500
3bPOS00
WPOGOO0
8b2S00
9POS00
@bOS00
DEISOO
BEOSON
bEOSOO
7EDS00
azZ9S00
299

<!-- source-page: 307 -->
## Page 307

00¢
OOSCAE
OOSCB4
CO5CB8
OO5CBA
OOSCBE
005CC2
ooscc4
O05CC6
005CC8
OOS5CCA
oosccc
OO5CCE
0O5CcD4
OOSCDA
ooscDpe
OOSCEO
OOSCE2
OOSCE8
OO5CEC
OOSCEE
OO5CF4
OOSCF8
OOSCFA
OOSCFC
OOSCFE
0O5D00
005D02
005D04
OOSDOA
OO5DOE
005D10
005D12
2EBCO00012CF
610005B0
48C0
81ED0016
3B400012
424)
6016
204D
3247
D1ic9
3247
D3FC000012BC
11690008001C
5247
BE7C0003
6DE4
207C00000676
326E0008
D1c9
227000000674
346E0008
D3CA
1091
6704
7001
6002
4240
227C00003E2A
346E0008
D3CA
1280
200D
move.1
bsr
ext.1
divs .w
move .w
clr.w
bra
move .1
move .W
add.l
move .W
add.1
move .b
addq.w
cmp.w
blt
move.1
move .W
add.1
move.1
move .W
add.l
move .b
beq
moveq.1
bra
clr.w
move .1
move .w
add.1
move .b
move.1
#512CF, (A7)
$6266
DO
22(A5),DO
DO,18(A5)
D?
$5CDC
A5,A0
D7,Al
A1,A0
D7,Al
#$12BC,Al1
8(A1),28(A0)
#1,D7
#3,D7
$5CC6
#$676,A0
8(A6),Al
Al1,A0
#$674,Al
8(A6) ,A2
A2,A1
(Al), (AQ)
$5D02
#1,D0
$5D04
DO
#$$3E2A,Al
8(A6) ,A2
A2,Al
DO, (Al)
AS, DO
Buffer+19,
number
of
sectors
on
disk
u2i,
convert
8086
integer
to
68000
int
Divided
by dspc
Yields dntracks
Counter
to
zero
Jump
to
end
of
loop
Buffer pointer
Loop counter
Plus
BPB address
Loop counter
Plus buffer address
Copy byte
of
the
serial number
Next
byte
Three bytes
already
?
No
cdev
wpstatus
Disk
status uncertain
Status certain
Address
of
BPB
as
result
Surysyqng ISILy
sjeaiojuy TS Weyy

<!-- source-page: 308 -->
## Page 308

Atari ST Internals
First Publishing
wT oOPKeW
wy 4o0R
002
24
yo eds
ayequnu aaTid
youerzq
r0l11g
,99TAep UMOUXUN,
ce
>
Jaqunu 8ATId
SieystTbar
aaes
yoreTpow
silaystTber
ei0jsey
wuass
oa’9aSc$
oq‘ta
Ta‘ (TW)
TW‘8Los#
Tv’1Wv
tw‘Tw
Tw‘La
od’wars
(SY) ‘T#
esass
(m°La‘ow)o
OW ‘9L9S#
aLass
0a‘ z#
8pdss
(SV) ‘74
Gv‘vZaes#
Gw‘ia
La‘ (9¥)8
aLaG$
oa’St-#
zEass
(9¥) 8°7#
(LW) ~‘SW/Ld-94
OF ‘OU
OW
GV-pW/L0-90
‘+ (LY)
+ (LY)
abq
T° dwo
T*qns
T*‘eaouw
T°ppe
T*ppe
T’ppe
M*SAOU
T°’ aaow
q*eaou
beq
q°4sq
T° aaow
emg
T* baaou
auq
q‘duo
T'ppe
M* SAOW
M* SAOU
Reiq
T° baeaow
ITO
mM* duo
T*weaow
HUTT
si
xTUNn
[T‘weaow
T° 4s9
bOD9
bLdS00
946700006808 A90S00
T806
290500
Ttze wW9dS00
gL9000000MEd
b90S00
69€d
790500
69€d 090500
Lece ASASOO
wapoooo06eoz 8sasao
TOOODEWT
&SaS00
bOL9
ZGdS00
OOOLOEVP
ApaSO00
9L9QOOOODLOZ
8FASO0O
9€09 9PdS00
ZOOL
bbASOO
bo99
2@bdasoo
ZOOOSTOO FEdSOO
Vcageooo0osdd BEaSOO
LEWE
9€dsS00
eooouere
zcedsoo
3P09
O€dS00
TdHOL
¥20S00
bods
22dsS00
800070008990
9720500
POCOLABE
¢2aS00
O0009GHrP ATdSOO
SOOTe ere Serre rrererererertererer
eee Lele 2 SS See ee Se
GLOb
OTASO00
acgab
vtdqsoo
OS0€ddar
9TASOO
J6Vb
PTdSOO
301

<!-- source-page: 309 -->
## Page 309

Atari ST Internals
First Publishing
youriq 10272q
101278 abueyo eTpey
ON
bet yaa
iequnu
esATAp aces
youeiq 1011q
SoTASp uMOUyUN
‘ON
éZ
>
zequnu eatig
szZeqstbezr
aaes
(Ss) 1O}0eS aYTIM/peel
‘sqeai
sZaqstTbhal
azojssy
wwags
Od‘ p1-#
rAatater-)
La‘c#
.a‘od
atass
(LW) ‘9d
Gv‘ aedes#
sv‘od
od
oa‘s#
oa’9qd
8Lass
(9W) 8‘c#
9a’ (9¥) 8T
vwacs
oa‘st-#
a6acs
(9)
81 ’°7#
(LW) -‘SW/Ld-5a
p-# ‘OW
PIq
{T*baaouw
auq
M* aud
M* aAoU
asq
M* 3AOU
T° ppe
T° aaow
T’3x%a
a‘ Tse
M* aAou
aig
ma‘ dwo
M* 9A0U
BIg
[T* beaouw
aTa
M* duo
T‘weaou
AUT
4d000009
cdOL
Vo99
Z0000LdE
oode
o9A4d00T9
98aE
ae aeooo00odda
ObWZ
008F
Opdd
900E
49000059
800070004990
cTOOECIE
a0T00009
Td0L
90a9
2T0020004950
bOFOLA8b
Dddd9GAd
WoaGoo
89dS00
99aS00
290500
99qaS00
o8qg00
waaqasoo
yadqsoo
cadgsoo
oaasoo
aAvdsoo
ovdsoo
gvasoo
c¥asgoo
46dqs00
W6dS00
86d0S00
960500
06qdS00
280500
g8dsoo
FRE
ER
OR
RRR ROR KOR
ROR ORR RRR ORE RR OR RE
ORR
ROE
hd
Gw/La‘+ (LY)
+(LW)
od
od‘ (c¥)
acags
od
sya
xqun
T*weaow
T° 4s 3
M° xe
q*aaou
Big
M°ITO
Slap
asap
O80CA00P
46VP
0886
STOt
boos
ObCP
98qaS00
b8asoo
o8dqsoo
aLaqsgoo
oLaS00
wiqasoo
BLasS00
9LQg00
302

<!-- source-page: 310 -->
## Page 310

coe
OOSDCE
O05DD2
OOSDD6
OOSDDA
OOSDDE
OOSDEO
OOSDE2
OOSDE6
OO5DE8
OOSDEA
OOS5DFO
OOS5DF6
OOSDFC
OO5E00
0O5E04
OO05E06
OO5E08
OOSEOC
OOSEOE
OOSE14
OO5SE16
OOSE1LA
OOSELE
O05E24
OO5E26
OOSE2A
OOS5SE2C
005E30
005E34
OO5E36
600000A8
BE?7COO001
660000A0
3EBCOO01
4267
4267
3F3C0001
3F06
42A7
2F3CO000012BC
4EB9000062D2
DFFCO00000010
2D40FFFC
4AAEFFFC
6c14
3E86
202EFFFC
3F00
4£B90000555C
548F
2D40FFFC
202EFFFC
BOBCO00010000
67B4
4AAEFFFC
6c08
202EFFFC
60000078
4247
601C
bra
cmp .w
bne
move .W
clr.w
clr.w
move .W
move .W
elr.1
move.1
jsr
add.1
move.1
tst.1
bge
move .W
move.
move .w
jsr
addq.1
move.
move.1
cmp.1
beq
tst.l
bge
move.1
bra
a
i
clr.w
bra
S5E78
#1,D7
$SE78
#1, (A7)
-(A7)
{AT}
#1,-(A7)
D6,
- (A?)
-(A7)
#$12BC,~-(A7)
$62D2
#$10,A7
DO,
-4 (A6)
-4(A6)
SSE1A
D6, (A7)
-4(A6) ,DO
DO,- {A7)
$555¢
#2,AT7
DO,
-4 (A6)
-4 (A6) ,DO
#$10000,D0
SSDDA
-4 (A6)
$5E34
-4(A6) ,DO
S$SEAA
D?
$5E54
Disk possibly changed
?
No
Read
a
sector
(Boot
sector)
Side
0
Track
O
Sector
1
Drive number
Filler
Sector buffer
floprd
Correct
stack pointer
Save error
number
And test
Ok
?
Error
Pass
an
critical
error handler
Correct
stack pointer
Read again
Error
number
Ok
?
Error
number
Error branch
Clear media change
status
Surysyqng ISiLy
sjeuiaquy ES yey

<!-- source-page: 311 -->
## Page 311

voc
OOSE38
OOSE3E
OO5E42
OOSE44
OO5E48
OOSE4A
OOSE4C
OO5E4E
005E50
O005E52
005E54
005E58
QOSESA
OO5ESC
OOSE62
OO5E64
OO5SE6A
QO5E6C
QOSEGE
OO5E70
OOSETES
OOSE78
OOSETE
0O5SE80
OO5E82
005E84
OOSE8A
OOSE8C
005890
005E94
207C000012BC
10307008
4880
1235701C
4881
BO41
6704
70F2
6058
5247
BE7C0003
6DDE
3046
D1FCO0000676
3246
D3FC00000674
1091
660A
3046
DIFCOOQO003E2A
4210
4A79000004A6
6604
TOFE
6026
0C6E00010008
6F04
55650008
3EAEOOOE
3F06
move.1
move.b
ext.w
move.b
ext.w
cmp.w
beq
moveq.1
bra
addq.w
cmp.w
bit
move.w
add.1
move .w
add.l
move .b
bne
move .W
add.1
clr.b
tst.w
bne
moveq.1
bra
cmp.w
ble
subq.w
move .W
move .W
#$12BC,A0
8{A0,D7.w),DO
DO
28(A5,D7.w),D1
D1
D1,D0
$5E52
#-14,D0
SSEAA
#1,D7
#3,D7
$5E38
D6,A0
#$676,A0
D6,Al
#$674,A1
(Al)
, (AO)
$SE78
D6, A0
#$3E2A,A0
(A0}
$4A6
S5SE84
#-2,D0
SSEAA
#1,
8 (A6)
$5E90
#2,
8 (A6)
14 (A6), (A7)
D6, -(A7)
Address
of
the
sector
buffer
Serial
number
Compare
With previous value
Ok
?
Media change
Error branch
Next
byte
of the
serial number
All
3 bytes tested
?
No
Drive number
wplatch
Drive number
wpstatus
Drive not
ready
Surysyqnd IST
S[BUI9ay LS Wey

<!-- source-page: 312 -->
## Page 312

Atari ST Internals
First Publishing
odsp puy
adsp
sw
6
S7FQ OSTA
soz
é
yas
odsp
aaes puy
BeTjppo es
beTIppo 1esTo
sox
é
uaae
jou ssaippe
Jaejjng
ddd
sseippe eseq
snitd
Ze
SoUTL
qjequnu
eaTig
szaqstTbaz
aaes
g10}0es SyTIM/peel
‘midoTj
szaqsTbhal
a10 say
azaqutod
yoreqjs
4OoetI0D
midoTj
betjar
ABTING
ousad
apo9s
(Sv) bz‘0d
(Sv)
Zz ‘od
oa‘6#
aagass
(SW) 22
(9¥) Z2-‘od
od‘t#
waass
oa
gaas$
(OW)
ET ‘OF
cv ‘deaess
Gw‘od
od
oa ‘S#
Od’ (9¥) 9T
(LW) -‘SW/Ld-2d
9-# ‘OV
eiq
4ST00009
M* OAOU
BTOOOPEE
M°SAOUW
9TOOOPHE
T‘ baaow
600L
auq
Wo99
aA‘ysy
9TOOdIYE
M*OAOW
ad4190 dE
T* boaow
TOOL
P1q
Z009
M‘AITo
OreF
euq
7099
4as4q
d00000004280
T’ppe
aqeqeooo0o
ddd
T° eaow
OPV
T’1x9
0086
M°Tse
Opadd
M* SACU
OTOOAZOE
T° weaow
FOFTELABY
YUTT
Wddd9 GAD
aadasoo0
Waasoo
944500
badsoo
7adS00
aqdsoo
vwagsoo
gqasoo
9qqgs00
bpaasoo
7adS00
394500
9354S00
POdS00
7O8S00
00aS00
9daS00
Badsoo
padsoo
OREO
OR OR ROO ORO
ORR
OR
OR LORE
ROR
OR ENCE
OR ORE
OE
OW
Gw/Ld-Sd
‘+ (LW)
+(LW)
LY ‘VS#
paass
(LW)
-‘4 (9) 8
(LW)
-4 (9) OT
(2W)-‘ (9¥) 9T
sj4
GLAD
xTun
acad
T° weaow
OF0cAdOF
T'3s3
J6VP
T° ppe
wooooo00oddd
Asq
OTT9
M*SAOU
gooodcde
T° eaow
WOO0OTAT
M*9A0U
oToodZde
7aads00
ogdsoo
OVdS00
wwaso00
PWASOO
7WASOO
a6 aS00
VW6aS00
964500
305

<!-- source-page: 313 -->
## Page 313

90¢
OOSEF2
OOSEFS
OOSEFS
OOSEFE
O05F00
OO5F04
OO5F08
OO5F0C
OOSFOER
OOS5F12
OOSF16
O05F18
OOS5FIC
OO5F1E
OO5F22
005F24
OO5F26
OOSF28
OOSF2A
OOSF2E
005F32
OO5F34
005F36
OO5F38
OO5F3C
OOSF3E
OOSF42
OOSF44
OOSF48
OOSF4A
OO5SF4C
4AGEFFPFE
6708
203C000012BC
6004
202E000A
2D40FFFA
3C2E000E
48C6
8DEDO0016
382E000E
48C4
89ED0016
4844
B86D0018
6C04
4245
6006
TAOL
986D0018
4A6EFFFE
6704
7601
6018
302D0018
9044
BOGEOO12
6c08
362D0018
9644
6004
362E0012
tst.w
beq
move.1
bra
move.1
move.1
move .W
ext.1
divs.w
move .W
ext.1
divs.w
swap
cmp.w
bge
clr.w
bra
moveq.1
sub.w
tst.w
beq
moveq.1
bra
move .W
sub.w
cmp.w
bge
move .wW
sub.w
bra
move .wW
-2 (AG)
S$5F00
#$12BC,D0
$5F04
10(A6),DO
DO,
-6 (A6)
14 (A6) ,D6
D6
22(A5),D6
14 (A6) ,D4
D4
22(A5),D4
D4
24(A5) ,D4
S5F28
DS
SSF2E
#1,D5
24(A5) ,D4
-2 (A6)
$5F38
#1,D3
$5F50
24(A5) ,DO
D4,D0
18 {(A6) ,DO
SSF4C
24 (A5) ,D3
D4,D3
$SF50
18 {(A6) ,D3
oddflag
set
?
No
Sector buffer
Get buffer
address
And
save
recno,
logical
sector
number
Divided by
dspc yields track number
recno,
logical
sector
number
Divided by dspc,
sector per track
Remainder
of division
as
sector number
Compare with dspt
Greater than
or equal
?
Side
0
Side
1
Subtract
dspt
oddflag
set
?
No
Set
counter
to
l
dspt
Minus
Sector
number
Compare with number
of
sectors
Greater
or
equal
?
dspt
Minus
sector
number equals counter
Number
of sectors
as
counter
Surysyqnd Isa
speaiejay LS Heyy

<!-- source-page: 314 -->
## Page 314

LOE
OOSF50
OO5F52
OOSF56
OOSFS5A
OOSFS5E
0OS5F62
OO5F64
OOSF68
OOSF6C
OOSF72
OO5F74
OOSF76
OOSF78
OOSF7A
OOSF7C
OOSF80
OOSF82
OOSF86
OOSF8C
OOSF92
00SF94
OOS5SF96
OOS5F98
OOSF9E
OOSFAO
OOSFA2
OOSFA4
OOSFAG6
OOSFA8
OOSFAC
OOSFAE
OO5FB4
5244
4A6E0008
67000080
202EFFFA
BOAEOOQOA
6710
2EAEFFFA
2F2EQ00A
4EB900005910
588F
3E83
3F05
3F06
3F04
3F2E0010
42A7
2F2EFFFA
4EB9000063B0
DFFCO0000010
2E00
4A87
663E
4A79000004
44
6736
3E83
3F05
3F06
3FO4
3F2E0010
42A7
2F3C000012BC
4EB900006602
addq.w
tst.w
beq
move.1
cmp.1
beq
move.
be
move.
jsr
addq.
move.
move,
move.
move,
=~£
2
e€£
ft
fr
move.
clr...
move.1
jsr
add.1
move .1
tst.l
bne
tst.w
beq
move.
move.
move.
move.
xf fees
move.
clr.l
move .1
jsxr
#1,D4
8 (A6)
S5FD8
-6(A6) ,DO
10 (A6) ,DO
$5F74
-6(A6), (A7)
10 (A6)
,- (A7)
$5910
#4,A7
D3, (A7)
D5,-(A7)
D6,-(A7)
D4,-{A7)
16 (A6) ,-(A7)
-(A7)
~6(A6) ,-(A7)
$63B0
#$10,A7
DO,D?
D7
SSFD6
$444
S5FD6
D3, (A7)
D5,-(A7)
D6,-(A7)
D4,-(A7)
16 (A6) ,~-(A7)
-(AT)
#$12BC,-(A7)
$6602
Increment
sector
#
(lst number
is
1)
Test
read-write
flag
Read
Buffer pointer
Equals
buffer
address
Yes
Source
address
Destination address
fastcpy,
copy
a sector
Correct
stack pointer
Number
of
sectors
Side
Track
Sector
Drive
Filler
Sector buffer
flopwr,
read
sector
Correct
stack pointer
Error
code
Ok
?
No
fverify,
verify required
?
No
Number
of
sectors
Side
Track
Sector
Drive
Filler
Sector buffer
flopver,
verify sector
—
Surysyqng Isi1y
s[eulayuy] JS Wey

<!-- source-page: 315 -->
## Page 315

80t
COSFBA
OO5FCO
OOSFC2
OO0SFCA4
OO5FC6
OOSFCC
OO5FDO
OOSFD2
OOSFD4
OO5FD6
OOSFD8
OOSFDA
OOSFDC
OOSFDE
OOSFEO
OOSFE4
OOSFEG6
OOSFEA
OOSFFO
OOSFF6
OOSFF8
OOSFFC
006000
006002
GO6006
OO600A
006010
006012
006014
006016
OO601A
DFFCO0000010
2E00
4A87
6610
2EBCO000012BC
61000298
4A40
6702
TEFO
603A
3E83
3F05
3F06
3F04
3F2E0010
42A7
2P2EFFFA
4EB9000062D2
DFFCO0000010
2E00
202EFFFA
BOAEOOOA
6710
2EAEOO0A
2FZ2EFFFA
4£B900005910
588F
4A87
6C12
3EAE0010
2007
add.1
move.1l
tst.l
bne
move. 1
bsr
tst.w
beq
moveq.1
bra
move.
move.
move.
move.
move.
clr.1
move .1
jsr
add.1
move.1
move.1
cmp.1
beg
move.1
move .1
jsx
addq.l
tst.1
bge
move.w
move.1
fetes
#$10,A7
DO,D7
D7
SSPD6
#$12BC, (A7)
$6266
DO
SSFD6
#~16,D7
$6012
D3, (A7)
D5,-(A7)
D6,-(A7)
D4,-(A7)
16{A6) ,~-(A7)
-(A7)
-6(A6)
,- (AT)
$62D2
#$10,A7
DO,D7
-6(A6) ,DO
10(A6) ,DO
$6012
10 (A6), (A7)
-6{(A6) ,-(A7)
$5910
#4,A7
D7
$6028
16(A6), (A7)
D7,D0
Correct
stack pointer
Error
code
Ok
?
No
Sector buffer
u2i,
convert
8086 integer
to
68000
int
Bad sector
list
Sectors
OK
?
Bad sectors
Number
of sectors
Side
Track
Sector
Drive
Filler
Sector buffer
floprd,
read sector
Correct
stack pointer
Save
error
code
User buffer
Equals desired buffer
?
Yes
Source address
Destination
fastcpy,
copy
sector
Correct
stack pointer
Test error
code
Ok
?
Drive number
Error
code
Suyystqnd Is1y
yeaa] LS Wey

<!-- source-page: 316 -->
## Page 316

Atari ST Internals
First Publishing
qaqunoo
2H
00Z2
£
018Z
JON
jequnu wopuez 4se 7
zequnu wopurz
ejerjeueb
‘wopuez
sieqjsTber a10jsey
x40
sax
&é
83TIM/peezr
04 eA
si09jDaS
sseo0id
oj sazojoes
Jo equnu
jUuseUezDaq
Zayunos
sn{d requnu Iojoes
TeRoOTbHboT
ssaippe Jajygnq yuUSwsetDUT
71S
SOUT,
ABANED
IO IIS
qInser
se
apod 1011g
pte)
@pod 1011
sox
é
utebe
ydueqqy
apoo OIE
485
Zajyutod
yoeqys
2Oa770D
ZetTpuey 1OIJa TeOTATAD
yoeqs
uo
Ta‘9T#
T°’ baacu
od‘vdbs
T° sAow
7809S
auq
WadSzs
T’4s9
b-#‘9W
MUTT
OT?2L
VdbPOoo0dbE0Z
9199
VAS TOOO06aUE
O4d19 SAP
bLO900
490900
290900
990900
290900
CETTE Ce TCE TEV ETT TPC eL ELT CSET ESS Pee ee ee See SS
eS
sqi
OW
xTuN
GY/LO-E0’+
(LW) T*weaow
+ (LY)
T°383
od
T*aqto
7AdS$
auq
(9W) 8T
M°4SQ
(9W) 8T “Ea
m°qns
(9¥)bT‘Ead
M*ppP
(9¥)OT‘0d
T’'PppP
oa‘td
T'tse
Ta‘6¢
[T° beaow
oa
T°3xe
oa‘eaq
AM eaow
8s09$
e1q
Od’iaq)
«T" eA
WEO9S
abg
Ld
T° 459
eGdss
beq
La‘oo000ts#
T° duo
La‘oqd
T° eAaou
Lv‘z#
T° bppe
agsgss
asf
(LW)-‘0G
M*eaow
SLAP
acay
B8A0 CHOP
46W?
O8cb
H6FI0099
ZTOOUIUE
ZTOOU9LE
40008940
woooavtd
owed
602L
0D8P
EO0E
aTo09
L00¢e
099
LEVP
CCAAOOLY
O000TO00Desa
O0d2
A180S
oSSSO0006Hab
OOode
090900
aS0900
Wso900
850900
950900
250900
4¥0900
V¥b0900
970900
7¥0900
060900
a€0900
SE0900
WE0900
8£0900
9€0900
bE0900
ZE0900
420900
8z0900
920900
'20900
d1T0900
210900
309

<!-- source-page: 317 -->
## Page 317

Atari ST Internals
First Publishing
0 xorIL
0 apts
Zo joes
BUCO
& a17eXSTP ON
Aap 00g
sdotyu
SJOTIe BARS
,PATIP
OU,
1PROT
4, UPTNOS,
& paeyauuod
asATIAp
ON
sdotju
FUT Apy
sieqsTbal
aaes
JojOas
4Ood peoT
‘peoTtjoog
ATasezl
se Jequnu wopuez 4Tq-9Z
O-€¢
OF
B8-TE
Sita
ONTeA RAPS
MoU
sy
T
sn{d
aqtnsey
Jayutod
yoeqys
497100
uoTyeoTTATAT
NU
ATG
ZE
x
ZE
AnTRA wWopUueT
4seT
T29C6STHTE
aNTeA Aes
se
asg
azaqunos
ZH
OOZ
SNTd
TE-9T
93
ST-O
S4Td
(LW)-
(LW) -
(LW) ‘T#
DTI9$
9bbS ‘7H
OTI9$
Auta
Juve
La‘od
od ‘z#
qD09$
oa‘t#
2909$
9uPs
ZE6SS
(LW) -‘La-9d
O# ‘9W
OW
00‘
dd ddd I$ $¢
0a‘s#
od ‘waszs
wWdG7z$ ‘0d
od‘T#
LW‘84
Wdb6s
(LY) -‘WASes
(LW) -‘az9dovdds#
wac7s ‘0d
od‘vars
oa’td
M*ITO
M‘IToO
M* OAOW
Yexed
a? dus
baq
A°4S
M*SAOU
T° boaou
eIq
T°’ beaou
baq
A’ ys
asf
T' weaow
AUTT
sya
xTuN
T'pue
T’ase
T* Saou
T*aaou
T'bppe
T’ bppe
asl
T*aaow
T*’saow
T° aaow
[T° 10
T’Tse
L9O@D
L9O?P
ToOOoDdaE
Weoo
96 F0000020006L90
bPL9
SV VOOOCOGLY?
OOdE
cOOL
2009
TOOL
OL9
9WPOOCOOO6LYE
ZEBSOO00GEAP
OOEOLABD
00009SHP
SLAG
aSdp
Add FI000d09
080d
WAS ZTOOONGEDZ
WAS CO0000DES
O8¢S
A80S
VWipeo000eddy
VdSCO0006E
AZ
d29d0 PAGOE TS
WdSCO0000SEC
Va poooo0GHos
oved
840900
940900
240900.
040900
8d0900
900900
490900
990900
WO0900
890900
990900
030900
vaos0o
940900
€€0900
OR ORR
KOR
OR ORR RRO
OR EO
OR OR OO
OR
OR RE
OE EE
0@0900
avo900
gv03900
90900
ovo900
V60900
860900
960900
060900
¥80900
780900
aL0300
820300
9L0900
310

<!-- source-page: 318 -->
## Page 318

ITe
OO60EA
OO6OEE
OO060F4
O060F6
O060FC
006102
006108
O0610A
00610C
OO610E
006110
006116
006118
OO611A
00611C
00611E
006120
006122
006124
006128
00612E
006132
006134
006138
O0613A
00613C
00613E
006140
006142
3F3C0001
3F3900000446
42A7
2F3C000012BC
4EB9000062D2
DFFCOQ000010
480
6604
4247
600C
443900000674
6604
7003
6024
4A47
6704
3007
601C
3EBCO100
2F3C000012BC
61000106
588F
BO7C1234
6604
4240
6002
7004
4A9F
4CDFO0080
move .W
move .W
clr.l
move.
sr
add.1
tst.l
bne
clr.w
bra
tst.b
bne
moveq.1
bra
tst.w
beg
move .W
bra
move .W
move .1
bsr
addq.1
cmp.w
bne
clr.w
bra
moveq.1
tst.1
movem. 1
#1,-(A7)
$446,-(A7)
-(A7)
#$12BC,-(A7)
$62D2
#$10,A7
DO
$6110
D7
$611c
$674
$611c
#3,D0
$6140
D7
$6124
D7, D0
$6140
#$100, (A7)
#$12BC,~(A7)
$6236
#4,A7
#$1234,D0
$613E
DO
$6140
#4,D0
{(A7) +
(A7)+,D7
Sector
1
bootdev
as
drive number
Filler
Sector
buffer
floprd,
read
sector
Correct
stack pointer
Error
?
No
wpstatus
‘unreadable’
Get
old error
code
$100 words
Sector buffer
Calculate checksum
Correct
stack pointer
Compare with checksum for boot
sector
Not
equal
?
OK
‘ot
valid boot
sector'
Restore registers
Surysyqng 3s1J
sjeuio}uy LS Fey

<!-- source-page: 319 -->
## Page 319

rats
006146
006148
4E5E
4E75
unlk
rts
A6
Ye
IO IO
kkk kk kok kk kok kkk kok okokokok ok kok kok kok ok kok
ke &
00614A
00614E
006152
006156
006158
00615C
006160
006164
006166
00616A
00616C
00616E
006170
006172
006176
OO6GLTA
00617C
006180
006186
006188
00618C
006190
006192
006194
006198
O0619E
4ES6FFFA
48E70704
4A6E0012
6C1E
3EBCO100
2F2E0008
610000D4
588P
BO7C1234
6704
4240
6002
7001
3D400012
4AAE000C
6D3E
202E000C
BOBCOOFFFFFF
6F08
6100FED8
2D40000C
4247
6020
202E000C
COBCOQOQQOOFF
3247
link
movem.1
tst.w
bge
move .w
move .L
bsr
addq.1
cmp .w
beg
clr.w
bra
movegq.1
move .w
tst.1
blt
move.1
emp.1
ble
bsr
move.1
elriw
bra
move.1
and.
move .W
AG, #-6
D5-D7/A5,-(A7)
18 (A6)
$6176
#$100, (A7)
8 (A6) ,-(A7)
$6236
#4,A7
#$1234,D0
$6170
DO
$6172
#1,D0
DO,18(A6)
12 (A6)
S61BA
12 (A6) ,DO
#SFFFFFF,DO
$6190
$6062
DO,
12 (A6)
ov
$61B4
12 (A6) ,DO
#SFF,DO
D7, Al
proto
bt,
generate
boot
sector
Save registers
Test
execflg
Maintain executability
§100 words
Address
of
the
sector buffer
Calculate checksum
Correct
stack pointer
Equals
checksum
for
boot
sector?
Yes
Not executable
Executable
execflg
to
1
= boot
sector executable
Serial number
Negative,
don't change
Serial number
>
SFFFFFF
?
No
rand,
generate random number
Save
Clear
counter
Random number
Bits
0-7
Pointer
to next byte
in buffer
SuTysyqnd ISI
sjeu8yuy LS Heyy

<!-- source-page: 320 -->
## Page 320

Atari ST Internals
first Publishing
PIOM
3X8N
uoTyereueb unsyoeyo
oj
wns
Jajjnq wory
piomM
4e9
ssoippe
rzejyjng
ON
é
61
Apeaity
layUNoS YUseUaToUT
daa Adoo
dag edAjojoI1d ayy
Jo
sseippy
gzayynq ayy
go sseippe
sntd
zequno
zaqyunoo
ieeToD
daq adAjoj01d
0} aaqufod stenbe
6T
SeUTL
aztTs aqqeystd
abueyo
4,u0p
‘aaT eben
ezTs
aqqexstad
ON
¢
Apeeite petdoo
seqAq ee1UL
qaqunos
yuSEWwseirsuUT
anTeA Meu
eaAesS
PUY
AUT
saTq
g
AJTUS
OF 29pPIO
UT
aJequnu wopuey
gajjnq
ut
ZJequnu [eTzes
jo
aqAq
e1TIaM
ssaappe aseq
sntd
(9W)
b- °Z#
(9v)9- ‘od
oa‘ (ov)
Ov‘ (9V) b-
zZOZ9$
(9¥)
b-’ (9¥)8
(9¥) 9-
DOT9$
La‘ETS#
La‘T#
oa‘T#
(OW)
TT‘ (TW)
TW‘OOd9TS#
Tw‘/9d
ov’ (9¥)8
ow‘id
Za19$
La
Oa ‘ETS#
90% (9W)9T
BAT9$
(QV) 9T
p6T9$
La‘es$#
La‘T#
(9v)
ZT ‘od
0d‘8¢
od‘ (9¥) 2T
(Tv)
8 ‘od
Iw‘ (9¥)8
T bppe
M’ppe
M' oAOU
T* aaow
eq
T° aaow
M* ITO
3T4
mM? duo
m* bppe
ma’ bppe
q* aaow
T'ppe
M* AOU
Tepe
M* aAOU
emg
M'3TO
M’sTnuw
M* DAOW
ATA
M°
SQ
ATA
a* duo
a‘ bppe
T* aaow
{'ase
T‘aaow
q*aaow
T° ppe
DAdATAV
PS
VWddda9
Td
OTOoEe
ddI IAI 0~
4009
D418 00089 TC
VdAdd9
eb
pad9
ETOOOLEE
LbesS
9b2S
aOooTtstt
00d9TO00D4Ed
99CE
so000ddtd
LDOE
9109
LbCD
ETOODATS
OTOOACOE
8cd9
OTOOU9VE
Wada
€O000oLda
LOcS
30000 bd
0804
D000A CO?
BO000RET
soooddEed
adT900
V4IT900
847900
bAT900
€AT900
O4dT900
841900
94T900
7AT900
04T900
agT900
Wdt900
paT900
cQT900
FDT900
99T900
YOT900
B9T900
POT90O
09T900
FaT900
VAT900
8aT900
baT900
fHT900
AVT900
OYT9IO0
8VT900
bYT9OO
OWT900
313

<!-- source-page: 321 -->
## Page 321

ass
006202
006206
00620C
006210
606212
006216
00621A
0O0621E
006220
006224
006226
00622A
00622C
00622E
006232
006234
202E0008
DOBCOOOO01FE
BOAEFFFC
62E2
303€1234
906EFFFA
226EFFFC
3280
4AR6E0012
6606
206EFFFC
5250
4A9F
4CDF20C0
4E5E
4E75
move.1
add.1
emp.1
bhi
move .w
sub.w
move.1
move .W
tst.w
bne
move.1
addq.w
tst.1
movem.1
unlk
rts
8(A6),D0O
#S1FE,
DO
-4(A6),D0
$61F4
#$1234,D0
-6(A6) ,DO
-4(A6),Al
DO, (Al)
18 (A6)
$622C
~4 (A6) ,A0
#1, (AO)
(A7) +
(A7) +,D6-D7/A5
A6
FOO I
kk
Rk
OO
ke
kk aka KK RIK KR KEK EK
006236
00623A
00623E
006240
006242
006246
006248
006244
00624E
006252
006256
006258
00625A
00625C
4E560000
48E70300
4247
600C
206E0008
3010
DE40
S4AE0008
302E000C
536E000C
4A40
66E8
3007
4A9F
link
movem.1
clr.w
bra
move .1
move .w
add.w
adaq.i
move .W
subq.w
tst.w
bne
move .W
tst.l
AG, #0
D6-D7,-(A7)
D7
$624E
8(A6)
, AO
(AQ)
, DO
bDO,D7
#2,
8 (A6)
12 (A6) ,DO
#1,12 (A6)
DO
$6242
D7,D0
(A7) +
Buffer
address
Plus
$1FE
Last
word already
Checksum
for
boot
sector
Subtract
from previous value
Checksum
in buffer
execflg
Boot
sector executable
?
Increment
checksum,
not
executable
Restore registers
Calculate checksum
Save registers
Clear
sum
Address
of
the buffer
Get word
And
sum
Pointer
to next word
Number
of words
Minus
1
All words added already
?
No
Result
to
do
Surysyqng ISN
jeurajuy 1S ery

<!-- source-page: 322 -->
## Page 322

Atari ST Internals
First Publishing
BIO Asst
apts
pue
eATIp
4sTes
sJajoweied
qas
‘yooTdoTz
o27ez
Of TEquNU
yorReAyl
qJaequnu
101Ia
ATnejeq
ea .eriyeas
@ PATIp worz qsa axeq
‘TqQSp
SOz
é
WV eAtig
W SATIP asd
0} AequTod
‘oqsp
@ATIP ezTTeTATUT
‘TuTdoyTyZ
GT-8
S4Tq YITM sUTqUuoD
L-O
SATQ a2eTOS]
p10M
OF pusyxg
ayAq MOT
199
qJequnu
ayy
jo
sseappy
SI-g uoTyqTsod ut 4sTuS
L~-O
S3TQ BIeTOST
PIOM
O02 PUusqXg
aykq ybTy 389
Jequnu
ayq
jo
sseippy
qaqunu
900089
O21 Jequnu
980g
4AeAU0D
‘Ten
szaysTbel
a10489y
La‘9# T*beaow
9044 FdzZ900
pas9$
isq
819000T9 vAz900
(Tw) 0‘00dd$#
M*eacu
COOOO0AMTILEE
PAzZ900
8469S
isq
96900019 0dz900
B89L9S
isg
Waroool9s ovz900
(TW)O
 M*°aTo
000069Z2b
BVvZ900
od‘1t-# T*beaow
dd0L 9¥Z7900
(Tv) Z‘Opp$
M*eaow
ZOOOCOPPOOOCOOELEE 367900
TW‘909$
eeT
DO9O0000E
AER 862900
F629$
baq
90L9 962900
(4v)7T
wt asa
D000M9Vb
7267900
TW‘8D9$
eeT
8990000064Eb 387900
ROR OR
ROR
KOE ROR
OE OREO
OR EO
ROR OR
OO
OE
sj2
GLb W8z900
OW
yTun
ASIP 88z900
oa‘ta
M*JO
TPO8 982900
Td‘ dds#
M*pue
JIOODLZID 782900
Taq
M°4xe
T88b 082900
Ta’(tw)
q*eaou
TT2@t 947900
Tw‘/(9¥)8
T° eaow
8000R9ZZ VLZ900
oa‘s#
A‘ Tse
OvTA 812900
0d‘ aa$¢
a" puPe
4d009L09
£42900
0g
= =M* Axe
088b
217900
og‘ (oW)T
q*eacu
Toooszot 497900
ov’ (9¥)8
T° Saou
go0c0d902 v972900
b-# ‘OW
yUTT
Dddd9GAb 997900
RE OR KR
ROR
OR OR OR OR OR ORR ORO
LOE KORO ROR RF
sqi
SLAb
p9Z900
OV
xTun
ASH’
797900
La0‘+(LY)
T° weaou
OB8004d06 4¢z900
315

<!-- source-page: 323 -->
## Page 323

OI¢
0062C0
0062C4
O0C062C6
0062CA
0062CE
610005A0
6608
6100060C
67000542
60000530
bsr
bne
bsr
beq
bra
$6862
$62CE
$68D4
$680E
$6800
FORO
IO
IO
IO
IK
TOKO
TOR RK
IR FORK
TO
IKK KR
RR IOI
IK KR IK
0062D2
0062D6
0062D8
0062DC
0062E0
0062E4
0062E8
0062F0
0062F4
0062F8
0062FC
006304
006308
00630C
006310
006316
OO631A
006322
006324
006326
006328
006330
006338
006340
006344
6100071E
7OF5
6100048E
6100066A
610005CC
66000090
33FCFFFFO00006A2
3CBC0090
3CBC0190
3CBC0090
33ED068CFFFF8604
3CBC0080
3E3C0090
61000€B6
2E3C00040000
246D0692
08390005FFFFFAO01
6734
5387
6724
1B7 9FFFF8609069D
1B79FFFF860B069E
1B79FFFF860D069F
BSED069C
6ED4
bsr
moveq.1
bsr
bsr
bsr
bne
move.
move.
move.
move.
move.
move.
move.
bsr
move.
move.
btst
beq
subq.
beq
move.
move,
move.
cmp.1
bgt
£e
ff
££
=
Pe
S69F2
#-11,D0
$6768
$6948
S68AE
$6376
#-1, $6A2
#590, (A6)
#$190, (A6)
#590, (AG)
$68C (A5)
, SFFFF8604
#580, (A6)
#$90,D7
$69C4
#$40000,D7
$692 (A5) ,A2
#5, $FFFFFAO1
$6358
#1,D7
$634C
SFFFF8609,
$69D (A5)
SFFFF860B,
$69E (A5)
SFFFF860D,
$69F (A5)
$69C (A5)
, A2
$631A
Restore
flopok,
no
error
flopfail,
error
floprd,
read
sector(s)
from disk
Change,
test
for
disk
change
Error number
to read error
floplock,
set
parameters
Select drive
and
side
go2track,
search
for track
Try again
if
error
currerr
to default error
Clear
DMA status
Data direction
to READ
ccount
to dskctl,
sector
counter
Read
sector
command
for
1772
Read multiple
wdiskctl,
pass
D7
to
1772
Initialize timeout counter
edma,
destination
address
for
DMA
mfp gpip,
1772 done
?
Yes
Decrement timeout
counter
Timed-out
?
dmahigh
dmamid
dmalow
Current
DMA address equal edma?
No,
continue
to wait
Surysyqn 3SI1
S[feurojyuy LS weyy’

<!-- source-page: 324 -->
## Page 324

Lie
006346
00634A
00634C
006352
006356
006358
00635C
00635E
006362
006364
006368
00636C
006370
006374
006376
00637C
00637E
006382
006386
00638A
BKK
IK I IK
KK KK RIK IKK IKK IIT KK TI IK IKK IO IK IK I
IK IK AK
00638E
006390
006394
006396
006398
00639C
00639E
0063A0
0063A4
0063A6
610005E6
600C
3BICFFFEO6A2
610005DA
601E
3CBC0090
3016
08000000
6712
3CBC0080
6100066E
C03C0018
6700049C
6118
0c6D00010672
6604
610004FA
536D0672
6GAOOFF54
60000474
72F3
08000006
6614
72F8
08000004
660C
72FC
08000003
6704
322D06A0
bsr
bra
move .W
bsr
bra
move .W
move .W
btst
beg
move .W
bsr
and.b
beq
bsr
cmp.w
bne
bsr
subq.w
bpl
bra
moveq.1
btst
bne
moveq.]
btst
bne
moveq.1
btst
beq
move .W
$692E
$6358
#~2,$6A2(A5)
$692E
$6376
#$90, (AG)
(A6) ,DO
#0,D0
$6376
#$80, (A6)
$69D8
#$18,D0
$680E
$638E
#1,$672(A5)
$6382
$687A
#1,$672(A5)
$62DC
$6800
#-13,D1
#6,D0
$S63AA
#-8,D1
#4,D0
$63AA
#~4,D1
#3,D0
S63AA
$6A0(A5)
,D1
Reset,
end transfer
currerr
to timeout
Reset,
end transfer
Start
next
attempt
Select
DMA status
register
Read status
DMA rrror
?
Yes,
try again
Select
1772
status register
rdiskctl,
read register
RNF,
isolate checksum und lost data
flopok,
no error
errbits,
determine error number
retrycnt
to
second attempt
?
No
reseek,
home
and
reseek
retrycnt,
decrement
attempt
counter
Another
attempt
?
No,
flopfail
errbits,
1772
status
in error number
Write protect
?
Yes
Record
not
found
?
Yes
CRC error
?
Yes
deferror,
take default
error
Surysyqnd ISI
syewszajuy LS Wey

<!-- source-page: 325 -->
## Page 325

8T¢
CO63AA
O0063AE
3B4106A2
4E75
move.w
D1,$6A2(A5)
rts
ok kok ok koko kkk kk kok kok
kk kk kkk kok kkk kkk
kkk kK KK KK
0063B0
0063B4
0063B6
0063BA
0063BE
0063C0
0063C4
0063CB8
0063CA
0063CC
0063D0
0063D4
0063D8
0063DC
0063E2
0063E6
0063EA
0063EE
0063F2
O063F6
O063FA
0063FE
006402
006408
006410
006412
006414
006416
61000640
TOF6
610003B0
302D0688
5340
806D0686
806D068A
6606
7002
6100065C
61000576
610004D8
6600007E
3B7CFFFFO6A2
3CBC0190
3CBC0090
3CBCO0190
3E3C0001
610005D0
3CBC0180
3E3CO0A0
610005C4
2E3C00040000
O8390005FFFFFA01
670A
5387
66F2
61000516
bsr
S69F2
movegq.1 #-10,D0
bsr
$6768
move.w
$688(A5),D0O
subq.w
#1,D0
or.w
$686 (A5) ,DO
Or.w
$68A (A5)
, DO
bne
$63D0
moveq.1
#2,D0
bsr
S6A2A
bsr
$6948
bsr
S68AE
bne
$6458
move.w
 #-1,$6A2(A5)
move.w
#5190, (A6)
move.w  #$90, (A6)
move.w
#$190, (A6)
move.w
#1,D7
bsr
$69C4
move.w
#$180, (A6)
move.w
 #SA0,D7
bsr
$69C4
move.1
#$40000,D7
btst
#5, SFFFFFAO1]
beg
$641C
subq.1
#1,D7
jne
$6408
bsr
$692E
As
currerr
flopwr,
write sector(s)
on disk
Change,
test
for
disk change
Default error
to write wrror
floplock,
set parameters
csect,
sector number
1?
ctrack,
track number
0?
cside,
side
0?
No,
not
boot
sector
Media change
Set
to
'unsure'
select,
select
drive
and
seide
go2track,
search
for track
Error,
try
again
currerr
to default
error
Clear
DMA
status
Data direction
to WRITE
Sector
count
register
wdiskctl,
D7
to
1772
Selects1772
Write Sector
wdiskctl,
D7
to
1772
Timeout
counter
mfp,
gpip,
1772 done
?
Yes
Decrement timeout counter
Not timed-out
yet
?
reset,
end transfer
Surysyqng Is1yq
seusaju] TS Wey

<!-- source-page: 326 -->
## Page 326

6I¢
OO641A
00641C
006420
006424
006428
00642C
006430
006434
006436
00643A
006442
006446
00644A
00644E
006450
006456
006458
00645C
006460
006464
6034
3CBC0180
610005B6
6100FF68
08000006
660003D2
CO3C005C
661A
526D0688
06AD00000200068E
536D068C
670003C6
61000524
608C
0C6D00010672
6604
61000420
536D0672
6A00FF6E
6000039A
bra
move .w
bsr
bsr
btst
bne
and.b
bne
addq.w
add.1
subq.w
beg
bsr
bra
cmp.w
bne
bsr
subq.w
bpl
bra
$6450
#$180, (A6)
$69D8
$638E
#6,D0
$6800
#$5C,D0
$6450
#1, $688 (A5)
#512, $68E(A5)
#1,$68C(A5)
$680E
$6970
$63DC
#1,$672(A5)
$645C
S687A
#1,$672(A5)
$63D0
$6800
ROOK
IK KE
IIR
II
kk kk
kkk
kkk RK
006468
006470
006474
006478
O0647A
OO647E
006482
006488
OO0648E
OCAF 876543210016
6600038E
6100057C
70FF
610002EC
610004C8
3B6FO00E0696
3B6F00140698
3BEFOO1LA069A
cmp.1
bne
bsr
moveq.1
bsr
bsr
move
.W
move.w
move .wW
#$87654321,22(A7)
$6800
$69F2
#-1,D0
$6768
$6948
14 (A7) ,$696(A5)
20(A7)
, $698 (A5)
26(A7) ,$69A(A5)
Select
1772
status register
rdiskctl,
read
1772
registers
errbits,
calculate error
number
Write protect
?
flopfail,
no further attempt
Write protect,
RNF,
checksum
and
lost
data
Error,
try again
csect,
increment
sector number
cdma,
DMA address
to next
sector
ccount,
decrement number
of sectors
flopok,
all
sectors,
then done
selectl,
sector
number
and DMA pointer
Write next
sector without
seek
retrycnt,
second attempt
?
No
ressek,
home
and
seek
retrycnt,
decrement
attempt
counter
Another
attempt
?
flopfail,
error
flopfmt,
format track
Magic number
?
No,
flopfail
Change,
test
for disk change
Default
error number
floplock,
set parameters
select,
select
drive
and
side
spt,
sectors
per
track
interlv,
interleave
factor
virgin,
sector data
for
formatting
Surysyqng IS1Lq
gjeaioyuy TS Wey

<!-- source-page: 327 -->
## Page 327

07
006494
006496
00649A
00649E
O064A2
0064A8
OO064AE
0064B0
0064B4
0064BA
0064C0
0064C4
0064C8
0064CA
0064CE
0064D4
7002
61000592
610003C0
66000360
336D06860000
3B7CFFFFO6A2
6128
6600034E
3BED0696068C
3B7C00010688
6100015C
246D068E
4A52
67000342
3B7CFFFOO6A2
6000032A
moveq.1
#2,D0
bsr
bsr
bne
move.
move.
bsr
bne
move.
move.
bsr
move.
tst.w
beq
move.
bra
Ww
S6A2A
$685C
$6800
$686(A5) ,0(A1)
#-1,$6A2 (A5)
$64D8
$6800
$696 (A5)
, $68C(A5)
#1,$688(A5)
S661E
S68E(A5)
,A2
(A2)
$680E
#-16, $6A2 (A5)
$6800
OR
RK
OK KR RK
RI
RO
ok
kk kk tk
kk
ke
0064D8
0064DE
0064E2
0064E6
OO64EA
0064EE
0064F2
0064F4
0064F8
OOG4FA
OO64FE
006502
006506
00650A
3B7CFFF606A0
363C0001
246D068E
323C003B
103C004E
6100010A
3803
323C000B
4200
610000FE
323C0002
103CO0F5
610000F2
14FCOOFE
move,
move.
move,
move.
move.
bsr
move.
move,
Ww
cere
=
=<
clir.b
bsr
move,
move.
bsr
move.b
Ww
b
#-10, $6A0 (A5)
#1,D3
$68E(A5)
,A2
#$3B,D1
#$4E,D0
S65FA
D3,D4
#S5B,D1
DO
S65FA
#2,D1
#SF5,D0
S65FA
#SFE, (A2) +
'changed'
Diskette changed
hseek,
search
for track
flopfail,
not
found
ctrack,
write
current
track
in
DSB
currerr
to default
error
Format
track
flopfail,
error
spt
sectors
per track
as
ccount
counter
csect,
start
with
sector
1
verify,
verify sector
cdma,
list with bad sectors
Bad sector
?
No
currerr
to
'Bad Sector'
flopfail,
error
fmtrack,
format
track
deferror,
default error number
Start
with
sector
1
cdma,
buffer
for
track
data
60 times
$4E,
track header
wmult,
write
in buffer
Save
sector
number
12 times
0
wmult,
write
in buffer
3 times
SF5
wmult,
write
in buffer
SFE,
address
mark
Surysyqnd ISI]
seuisyay LS Wey

<!-- source-page: 328 -->
## Page 328

Tee
OO650E
006514
OOG651A
00651C
006520
006524
006528
00652C
006530
006534
006536
00653A
00653E
006542
006546
QO654A
00654E
006552
006556
O0655A
OO655E
006562
006566
OO0656A
OO656E
006572
006574
006576
OO657A
OO6STE
006582
006586
14F900000687
14F90000068B
14C4
14FC0002
14FCOOF?
323C0015
103C0O04E
610000CC
323C000B
4200
610000C2
323C0002
103C00F5
610000B6
14FCOOFB
323CO0OFF
14ED069A
14ED06SB
S1C9FFF6
14FCOOF7
323C0027
103C004E
61000092
D86éD0698
B86D0696
6F80
5243
B66D0698
6FOOFF76
323C0578
103CO004E
6172
move.
move.
move.
move.
move.
move .w
move.b
bsr
move .W
clr.b
bsr
move.
move.
bsr
move.
move.
move.
move.
dbra
move.
move.
move.
bsr
add.w
cmp.W
ble
addq.w
cmp.w
ble
move .W
ToT
oT ST
o
oz
Y,oOzS
oz
oe
move .b
bsr
$687, (A2)+
$68B, (A2) +
D4, (A2)+
#2, (A2)+
#SF7, (A2)+
#$15,D1
#54E,D0
S65FA
#$B,D1
DO
S65FA
#2,D1
#5F5,D0
S65PA
#SFB, (A2) +
#SFF,D1
$69A (AS), (A2)+
$69B(A5), (A2)+
D1, $654E
#SF7, (A2) +
#$27,D1
#$4E,D0
S65FA
$698 (A5) ,D4
$696(A5)
,D4
S64F4
#1,D3
$698 (A5) ,D3
$64F2
#$578,D1
#$4E,D0
S6S5FA
Track
Side
Sector
Sector size
(512 bytes)
Write checksum
22 times
S4E
wmult,
write
in buffer
12 times
0
wmult,
write
in buffer
3 times
SF5
wmult,
write
in buffer
SFB,
data block mark
256 times
virgin,
initial data
in buffer
Next
word
Write checksum
40 times
$4E
wmult,
write
in buffer
Add interlv,
next
sector
spt,
largest
sector
number
?
No,
next
sector
Start
sector
plus
one
interlv
Next
sector
1401
times
(until track
end)
S4E
wmult,
write
in buffer
suysyqnd ISity
sjeusajyuy FS ey

<!-- source-page: 329 -->
## Page 329

Atari ST Internals
First Publishing
aqAq
7xXON
Jajjnq
ut
elep
oO ATIM
PIep ASOT
pue
4O9a {0d |aqTIM
4seL
Jaqunu
rJoize aye[noTeo
‘sytqize
saeqstber peal
‘T \OYNsTpa
ZeqstTHar
snqyeqs
ZiLT
ye TES
sax
é
101198 WNG
snjeqs
peasy
snqeqjs WWd 3eTeS
aorzqia
‘4TQ-Z
7eAaTD
aqeuTWwise}
‘AJese7z
é
3Mo-pauyty ISA ION
ZTazUNOS
4NoawTy
JueUsr598eq
sox
2
euop ZiLt
‘dtd6 dyu
aaquNnoo
jNosutl
ZLLT
O02
LA
*TIOXSTPM
puewwos
yorzy
yeWwI0OY
éLLT
J9TPS
ZLLT
OF
L0
*TIOXSTPM
TE
OF Taqunos
Sj OSS
QLIYUM
OF} voT_OSITp
eyeG
snqeqs WNC 2PeTO
ystyeup
ptuewp
MOoTeUp
Wds9s ‘Td
+(Z¥) ‘0d
Od‘bES#
ABEIS
geqgas
BuUIss
(9W) ‘OSTS#
gasc9s
od ‘oF
oa‘ (9W)
(9W) “O6TS#
La‘t#
Az69$
9959$
La‘T#
oas9$s
TOWddd
dS ‘SH
La‘oO000br$#
¥069$
La‘Od$#
(OV) ‘O8TS#
bO69$
LO‘ ATS#
(9¥) ‘O6TS#
(9V) ‘06S#
(9¥) ‘O6TS#
6098ddd4$
* (SW) d89$
d098ddda$
* (SY) 069$
Go9sdddds
* (SW) T6E9$
eaqp
q* aaow
sqi
q*pue
asq
isa
M* SACU
baq
as aq
M* 9A0OU
M* oAOU
sqa
T* beaow
isq
aug
T°’ bans
baq.
qasaq
T° eaou
isq
M*OAOU
M* BAOU
Isq
Mt SACU
M* SACU
M* 3AOU
M* 9AOU
q*aaow
q' aaow
q* aaow
Idd 469TS
OOPT
SLIP
PPOQDEOOD
26G400T9
MICANATA
Vaeooots
O8TOOMSE
O4L9
00000080
9TOE
06 TOOHOE
SLab
TOSL
BSe000T9
2.499
L8ES
90L9
TOWAAATATSOO06EBO
0000 F0000E AC
908000TS
OdADOOEME
O8TOOPDE
ZTPOOOTS
JTOOOERE
06 TQOOEDE
0600089
06 TODHIE
609 844d d4890CH
ET
Goo ssds4oegoagdet
G09 8dddd T6900H ET
946900
W4s900
845900
badS900
046900
AgWerann
vas azUuYU
845900
949900
caS900
04S900
20¢900
vasg900
8qas900
¥as900
705900
0a5900
A9G900
995900
095900
3aS900
Bas900
vaS900
0€S900
O¥S900
8V¥S900
bYS900
OWS900
865900
065900
885900
322

<!-- source-page: 330 -->
## Page 330

€ce
006600
4E75
rts
Rk
I
IK
OO
OK
OO
kok kk
kk kkk oe
006602
006606
006608
00660C
006610
006614
006618
OO661A
610003EE
TOFS
6100015E
6100033A
6100029C
660001EA
6104
600001F2
bsr
moveq.1
bsr
bsr
bsr
bne
bsr
bra
$69F2
#~-11,D0
$6768
$6948
$68AE
$6800
$661E
$680E
KK KK
IK
KK KK KKK KIKI KKK KKK KEK KK IKK KKK KKK KK KK
OO661E
006624
006628
006630
006636
00663A
00663E
006642
00664A
006652
OO665A
OO665E
006662
006666
00666A
OOGEG6E
006672
006676
OO6E7A
3B7CFFF506A0
246D068E
O€6AD00000200068E
3B7C00020672
3CBC0084
3E2D0688
61000384
13EDO691FFFF860D
13ED0690FFFF860B
13ED068FFFFF8609
3CBCO0090
3CBCO0190
3CBC0090
3E3C0001
61000358
3CBC0080
3E3C0080
6100034C
2E3C00040000
move .w
move .1
add.1
-mMove .W
move .W
move .wW
bsr
move .b
move .b
move .b
move
.w
move .w
move .w
move
.W
bsr
move .w
move .W
bsr
move.1
#-11,$6A0 (A5)
$S68E (A5)
, A2
#$200,
$68E (A5)
#2,$672(A5)
#$84, (AG)
$688 (A5) ,D7
$69C4
$691 (A5)
, SFFFF860D
$690 (A5)
, SFFFF860B
$68F (AS)
, SFFFF8609
#$90, (A6)
#$190, (A6)
#$90, (A6)
#1,D7
$69C4
#S80, (A6)
#$80,D7
$69C4
#$40000,D7
flopver,
verfiy sector(s)
Change,
test
for
disk
change
‘read error',
as default
error
floplock,
set parameters
Select
go2track,
search
for
track
flopfail,
error
verifyl,
verify sectors
flopok,
done
deferror
to
'read error'
cdma,
DMA buffer
for
bad
sector
list
cdma
to
next
sector
retrycnt,
2
attempts
Select
sector register
csect,
sector
number
wdiskctl,to disk controller
dmalow
dmamid
dmahigh
Clear
DMA status
Data direction
to READ
Sector
counter
to
1
wdiskctl
Select
1772
command register
Read
sector
command
wdiskctl
Timeout counter
Surysyqng S114
sjeusayuy LS Wey

<!-- source-page: 331 -->
## Page 331

pce
CO6E8G
006688
COEEBA
00668C
O0668E
006692
006694
006698
OO0669A
O0669E
0066A0
OO66A4
O066A8
0066AC
0066BO
0066B2
0066B6
0066BA
OO 66BE
O0066CE6
0066C8
OO66CA
0066D0
ANLEND
vyuQuUuve
0066D6
OO66DA
OO66DE
0066E2
O8390005FFFFFA01
670A
5387
66F2
6100029E
6036
3CBC0090
3016
08000000
672A
3CBCO080
61000332
6100FCE4
co3coolc
6618
526D0688
536D068C
6600FF74
O4AD00000200068E
4252
4E75
0C6D00010672
6604
LYNAARIAE
VLYVVYVILIAD
536D0672
6AOOFF66
34ED0688
60CE
btst
beq
subq.1
bne
bsr
bra
move .W
move .W
btst
beq
move .W
bsr
bsr
and.b
bne
addq.w
subq.w
bne
sub.1
clr.w
rts
cmp.w
bne
bsr
subg.w
bpl
move .wW
bra
#5, SFFFFFAOL
$6694
#1,D7
$6680
$692E
S66CA
#590, (A6)
(A6) ,DO
#0,D0
S66CA
#$80, (A6)
$69D8
$638E
#$1C,D0
S66CA
#1, $688(A5)
#1,568C(A5)
$6630
#5200,
$68E (AS)
(A2)
#1,$672 (AS)
$66D6
arnIT
Sé687A
#1,$672(A5)
$6642
$688 (A5), (A2)+
$66B2
mfp gpip,
1772
done
?
Yes
Decrement timeout
counter
Timed-out
yet
?
Reset
1772
Next
attempt
Select
DMA status
register
Reat
status
DMA error
?
Yes,
try again
Select
1772
status
register
rdiskctl,
read status
errbits,
calculate
error
number
Test
RNF,
CRC
and
lost
data
Error,
next
attempt
csect,
next
sector
ccount,
decrement
sector
counter
Another sector
?
cdma,
Reset
DMA pointer
bad sector
list
mit
Null abschlie@en
retrycnt,
2ns
attempt
?
No
reseek
Decrement
retrycnt
Another
attempt
?
csect,
sector
number
in
bad sector
list
Next
sector
Sulysyqng SIL]
seaiojuy TS Wey

<!-- source-page: 332 -->
## Page 332

sce
FOTO
OK II TO
TO
FOI RI
OI ROK IORI TI
IK
IIR
IR
III I TO
ROI
IOI
O066H4
O066E6
OO66EC
O066F0
O066F4
OO66F6
OO66FC
OOG6FE
006702
006704
006708
0O670A
OO670E
006712
006714
OO671A
00671C
OO671E
006720
006722
006726
00672A
006730
006734
006736
006738
00673C
006740
006744
006748
OO674A
9BCD
4DFOFFFF8606
SOEDO680
4A€D043E
6670
203900000466
1200
C23C0007
6638
3CBCO0080
£608
co7c0001
41ED0674
Doco
BO79000004A6
6602
4240
5200
E308
0A000007
6100026C
303 9FFFF8604
08000006
56DO
1002
6100025A
302D0674
816D0676
4A6D0682
6618
6100028C
sub.1
lea
st
tst.w
bne
move.1
move .b
and,b
bne
move .W
lsr.b
and.w
lea
add.w
cmp.W
bne
clr.w
addq.b
lsl.b
eor.b
bsr
move .W
btst
sne
move.b
bsr
move .W
Or .w
tst.w
bne
bsr
A5,A5
SFFFF8606,A6
$680 (A5)
$43E(A5)
$6766
$466,D0
po, D1
#7,D1
$673C
#580, (A6)
#3,D0
#1,D0
$674 (A5)
, AO
DO, AO
$4A6,D0
S671E
DO
#1,D0
#1,D0
#7,D0
$6994
SFFFF8604,D0
#6,D0
(AO)
D2,D0
$6994
$674 (A5) ,DO
DO, $676(A5)
$682 (AS)
$6762
$69D8
flopvbl,
floppy vertical
blank
handler
Clear
A5
Address
of the floppy register
Set motoron
flag
flock,
disks
busy
?
Yes,
do
nothing
f£rclock
Calculate mod
8
Not
yet
8th interrupt
?
Select
1772
status register
Use bit
4
as
drive number
wpstatus,
write protect
status table
Index with drive number
nflops,
number
of
floppies
Drive
select
bit
Shift
in position
Invert
for hardware
Select drive
dskctl,
read
1772
status
Test write rpotect
bit
And save
Previous select
status
Recreate
wpstatus
Write wplatch
deslflg,
floppies already deselected?
Yes
Raed 1772
status
register
Surysyqng ISI]
speuiajuy LS Heyy

<!-- source-page: 333 -->
## Page 333

9¢E
O0674E
006752
006754
006758
00675C
006762
006766
Fo
IKK
IKK KKK KR IK KK
IK KKK KKK KK KKK KKK KKK EKER KKK K KEKE
movem.1 D3-D7/A3-A6,
$6A4
006768
006770
006772
006778
OO67T7E
006782
006786
00678C
006792
006798
00679E
OO6TAA
OO67AA
0067B0
0067B6
O0067BA
OO67BE
0067C0
0067C4
0067C6
OO67CA
0067CC
OO67CE
08000007
6612
103C0007
6100023A
3B7C00010682
426D0680
4B75
48F978F8000006A4
9BCD
4DF9OFFFF8606
50F900000680
3B4006A0
3B4006A2
3B7C0001043E
2B6FO0008068E
3B6F00100684
3B6F00120688
3B6F00140686
3B6F0016068A
3B6F0018068C
3B7C00020672
43ED06CB8
4A6D0684
6704
43EDO6CC
7E00
3E2D068C
E14F
E34F
206D068E
btst
bne
move .b
bsr
move .W
clr.w
rts
sub.1
lea
st
move .W
move .wW
move .W
move.1
move .w
move .w
move .W
move .W
move .w
move .wW
lea
tst.w
beq
lea
moveq.1
move .wW
lsl.w
lsl.w
move .1
#7,D0
$6766
#7,D0
$6994
#1,$682 (A5)
$680 (A5)
A5,A5
SFFFF8606,A6
$680
DO, $6A0 (A5)
DO, $6A2 (A5)
#1,$43E(A5)
8(A7),
$68E (A5)
16(A7) ,$684 (AS)
18 (A7)
, $688 (A5)
20(A7)
, $686 (AS)
22 (AT)
, $68A(A5)
24(A7),$68C(A5)
#2,$672 (A5)
$6C8 (A5) ,Al
$684 (AS)
$671C4
$6CC(A5)
,Al
#0,D7
$68C (A5) ,D7
#8,D7
#1,D7
$68E (A5) ,A0
Motor
on bit
set
?
Yes,
then
don't
deselect
Both drives
Deselect
Set
deslflg
Clear motoron
flag
floplock
regsave
Clear
A5
Address
of the floppy register
Set motoron
flag
deferror
currerr
flock,
disable floppy-vbl
routine
cdma
cdev
csect
ctrack
cside
ecount
retrycnt
dsb0
cdev
Drive
0
?
dsbl
ccount,
number
of
sectors
Times
512
cdma,
start
DMA address
Surysyqng 31
youu] TS Wey

<!-- source-page: 334 -->
## Page 334

Atari ST Internals
First Publishing
zequnu
asatap
‘aepo
swodo
Tj
puewucos
yaes
TaTToTquCD
YsTp
OF puss
‘TIOYSTPpA
qJequnu
yorez3z 4ey
@LLT
WeTSS
yo
autqnor
Addo,Tj
eeij-I0IIE
*yodoTj
Ii97INO
39S
,eInsun,
03 abueyo
eTpey
eutTynoz Addoyy
uy
r01ze
‘TTesdoTJ
lorie
‘ayerqtTT essay
é
MO
azo 4say
é
4OIIAT
OT yoeIA yeas
é
40
018Z
YORI
OF peay
‘e707 say
OJeZ
OF yoRr eS
QoetTas
‘On
é0
=<
yORIy Quezino
“yoerINOp
sseippe WWd pus spTaTA
‘eupe
zoyoes
Jo
yAbueT
snitd
0d‘Ps9s
Was9s
9d‘OTS#
7069$
La‘ (two
(ow) ‘98S#
(LW) -0d
oa
M*aaou
Isq
M* aAow
asq
M* aAOW
M* aAOUw
T° aaow
T’aTo
PBIDDDDDGEDE
990000T9
OTOODEDE
BYTOOOTS
oo000e cae
9B800DHIE
00d
O82P
928900
268900
AT8900
WT8900
978900
218900
0T8900
408900
Pore CCC CES ESET ECE PST SST SPL
Le Lt
ee
SS
OT89$
oq
od‘ (sv) 2w9s
wzwos
eg
T'qxe
M* aac
Isq
Oa‘T#
T° boaow
2009
008F
eWIOATZOE
97200019
TOOL
908900
VO8900
908900
208900
008900
ere eT TCT ECT ELEC CET CTS SESS ET SCE LL LSS
SS Se
$s 2
(IV) 0/004dS#
M°eACw
TALg$
beq
pasa$
isq
B4ILOS
auq
79895
isq
La‘OT#
T° baaow
TALIS
baq
pasos
aisq
(Tv¥)O
Mato
8h69S
Asq
BAL9$
Tdq
(T¥)0
M°383
(SW) Z69$ ‘OW
T° aac
ow‘La
T'ppe
SLap
O00000HAOLEE
90L9
omoo000TS
9099
zLt9
WOde
eUlgo
DHOO00TS
000069¢P
B9TOOOTS
o¢cyv9
O00069NP
C6908 PEC
Lord
adL900
841900
941900
ZAL900
04L900
aaL900
2aL900
Val900
941900
7AL900
aqL900
9dL300
8di900
7dL900
cdL900
327

<!-- source-page: 335 -->
## Page 335

Bee
C0682C
00682E
006834
00683A
006842
006844
O0684A
00684C
006854
00685A
E548
41F900000678
21AD04BA0000
0C790001000004A6
6606
216D04BA0004
201F
4CF97 8F8000006A4
42790000043E
4E75
lsl.
lea
Ww
move.1
cmp.
bne
Ww
move.1]
move.1
movem,. 1
clr.
rts
Ww
#2,D0
$678, A0
$4BA (A5) ,0(A0,D0.w)
#1,54A6
$684A
$4BA (AS)
,
4 (A0)
(A7)+,D0
$6A4,D3-D7/A3-A6
$43E
KKK KK KKK KK IK KK
KK KE KK KK KEK KEK KEK KEKE KKK KEKE KIKKKKK KKK KKK K
00685C
006862
OO686A
OO686E
006872
006876
383900000686
33FCFFFA000006A2
3CBCO086
61000154
3€3C0010
60000072
move .W
move .W
move .W
bsr
move .w
bra
$686,D7
#-10,$6A2
#886, (A6)
$69C4
#$10,D6
S68EA
KK AK IK KH KK IK KKK KK IKK
KE KKK KKK KKK KKK KKKKKEKKKKKEKKKEK
00687A
006882
006884
006886
00688A
O0688E
006890
006894
006898
00689C
0068A0
O068A4
33FCFFFA000006A2
6150
664C
42690000
3CBCO0082
4247
61000132
3CBCO086
3E3C0005
61000126
3€3C0010
6144
move .w
bsr
bne
clr. Ww
move .w
alr
cir
bsr
cag
move .w
move .w
bsr
move .w
bsr
#-10,$6A2
$68D4
$68D2
0(Al)
#$82, (A6)
$69C4
#586, (A6)
#5,D7
$69C4
#$10,D6
S68EA
As
index
acctim
200
Hz
counter
as
last
access
time
nflops
20
Hz counter
for other drives
Restore error
number
regsave
Clear
flock,
release vbl routine
hseek,
head
to track
ctrack
currerr
to
‘seek error’
Pass track number
wdsikctl
Seek command
flopcmds
ressek,
home
and
seek
currerr
to
‘seek
error’
Restore
Error
?
Current track
to
zero
Select track register
Track
zero
wdisketl
Select data register
Track
5
waiskctl
Seek command
flopcmds
Surysyqng Is1ly
yeusojUy LS Wey

<!-- source-page: 336 -->
## Page 336

67E
OO068A6
662A
bne
$68D2
0068A8 337000050000
move.w
#5,0(A1)
II
IO
IOI
II GIO
I
III IOI
IOI
III
dO
I
kk kk oe
OOG8AE 33FCFFFAQ00006A2
move.w
#-10,$6A2
0068B6 3CBCO086
move.w
#586, (A6)
OO68BA 3E2D0686
move.w
$686(A5),D7
OO68BE
61000104
bsr
$69C4
o0o068c2
7¢014
moveq.1
#$14,D6
o068c4
6124
bsr
S68EA
OOG8CE
660A
bne
$68D2
0068C8 336D06860000
move.w
$686(A5),0(Al)
OO68CE CE3CO018
and.b
#$18,D7
0068D2
4E75
rts
De
I FI TOI IOI TOOK TOIT TOR ITI II TOI TI IOI I TOK I IK III IK IKK
IK IK
0068D4
4246
clr.w
D6
0068D6
6112
bsr
S68EA
0068D8
660E
bne
$S68E8
OO68DA 08070002
btst
#2,D7
O068DE 0A3C0004
eor.b
#4,5R
OO68E2
6604
bne
S68E8
OC68E4
42690000
clr.w
0 (Al)
OO68E8
4E75
rts
KK
KK TOI SOK TORT TOK TOK TOTO KT TIKI
TOT IKK IK IK II AK AIK KK KKK EEK
OO68EA 30290002
move.w
2{A1),D0
OO68EE CO03C0003
and.b
#$3,D0
O0068F2
8CO0
or.b
DO,D6é
OO68F4
2E3C00040000
move.l1
#540000,D?
OO68FA 3CBCO080
move.w
#580, (A6)
CO68FE
610000D8
bsr
$69D8
Error
Track
number
to
5
go2track,
search
for trak
currerr
to
'seek error’
Select
data register
ctrack,
load track number
wdiskctl
Seek with verify command
flopcmds
Error
ctrack,
Save track number
Test
RNF,
CRC
lost
data
restore,
seek track
zero
restore
command
flopcmds
Error
Test track
zero bit
Z-Flag invertieren
nicht
Track Null
?
current Track
auf Null
flopcmds
Seek
rate
Bits
0
and
1
OR
in command word
Timeout counter
—
Select
1772
register
rdiskctl
Burysyqng ISI
sjeuiauy LS Heyy

<!-- source-page: 337 -->
## Page 337

Oce
006902
006906
006908
OQ630E
006912
006914
006916
O0691E
006920
006924
006926
006928
00692A
00€692C
08000007
6606
2E3C00060000
610000AA
5387
6712
08390005FFFFFA01
66F2
61 0000AC
4246
4E75
6104
7C01
4E75
btst
#7,D0
bne
S690E
move.l
#$60000,D7
bsr
S69BA
subg.1
#1,D7
beg
$6928
btst
#5, SFFFFFAOL
bne
$6912
bsr
$69CE
clr.w
D6
rts
bsr
$692E
moveq.1]
#1,D6
rts
KOK KK KK KKK KK KKK KKK KKK KK KKK KKK KEK KKK KKK KKK KEK KK KK KKK
00692E
006932
006936
00693A
00693E
006946
3CBC0080
3E3CO0D0
6100008C
3E3COO0F
S1CFFFFE
4E75
move.w
#580, (A6)
move.w
#5$D0,D7
bsr
$69C4
move.w
#SF,D7
dbra
D7, $693E
rts
ok
kk
ok
kkk kkk kok kkk kk kkk kkk kk bak
006948
00694C
006950
006952
006954
006958
00695C
426D0682
302D0684
5200
E308
806D068A
0A000007
C03C0007
~~
or
CFOs
tance
clr.w
yo0"e {AO}
move.w
$684(A5),D0
addq.b
#1,D0
lsl.b
#1,D0
or.w
$68A(A5),DO
eor.b
#7,D0
and.b
#7,D0
Motor
on
?
Yes
Else longer timeout
wdiskct16,
write command
in
D6
Decrement timeout counter
Timed-out
?
mfp gpip,
1772 done
?
No,
wait
rdiskctl?
OK
Reset
1772
Error
Reset
1772,
reset
floppy controller
Select
command register
Reset
command
wdiskctl
Delay
counter
Timed-out
?
read status
select,
select drive and side
Clear
desifig
edev,
drive number
Calculate bit
number
cside,
side
in
bit
0
Invert bits
for hardware
SurysTqng ISIN
S[BUIDJOT ES Wey

<!-- source-page: 338 -->
## Page 338

Atari ST Internals
First Publishing
T3OxSP
ABT Toauos
ystp
10xy
dootT
AeqtTeq
T39AXS TPM
A@TTor14ues
ystp 10z
dooyt Avted
TqOXSsp
As@{TTo1q4uoes
ystp Joy
doo,
Aejteq
9 JO¥STPM
snqeqjs aioqssy
W
qaod
04
4TNser
aqtimM
sitq mau
3S
Z-0
S3TQ 2P8TO
BA00DEZD W¥69007G
OF PUY
W
yrod pesy
i Td
snqeqs
aaes
dtyo punos
ut
y
qiod
jes
‘ejiodjes
ybotyeup
pywuewp
MoTeup
TIOASTPA
aaqunu
zojoS8s
jab
‘joes
Zeysthal
TOROas
YoeyTses
Te-pe
sitq aeeTo
‘eupduy
TIOYSPA
qequnu yoezq
49D
TeqystThber
yoezq
4oeTes
djyo punos
ut
sqtq
38g
po9sdddds
“La
= M* eAOW
POOSATTALIEE 956900
0469S
Isq
VWTI9
b96900
OCT TCCTCTOCT CLIT
COCO
ES TCL LL
eS SS ee
od69s$
eaq
OT09
756900
pO98dddd$
‘9G
= M*eACW
bOOSAATAIDEE DA6900
0469S
ASq
bCT9 Vd6900
PoP CCTCCCT CTO CTT TCT TSI SCTE CCPC LL
ee SS See
eles
s qi
GLb 86900
us‘+(iv)
A&°*eaou
4Iq9p 946900
ZO88addd$
‘TA
q°eaou
ZOS8AATATOET 086900
Ta’od
q' 20
00z8 aVv6900
Ta‘sds#
q'pue
WdOODETO VV6900
za‘Iq
q‘eaow
TOPT
8V¥6900
Td‘ooseddad$
q*eaow
OO8BAMTI6ETI
7¥6900
us ‘OOLS#
M* IO
OO0L0DL00 966900
(LW)-
‘YS
M* eco
La0b
766900
ETE
CTT CETTE ET ECCT SPOS LC LLL LET ESS SS ee
sa
SLab
766900
6098ddddS
’ (GY) A89S
A oAoUW
6098dIIF1890dHET V86900
aO9sdddds$ “(G¥)069S
'eAou
GO9SITAIOG9OAAET
7286900
do9sdddds
“(GW) T69$
= q°eAow
Co98daIATEIOdHTET
VL6E900
po69$
Isq
WbT9 816900
La‘ (GW)889$
M*eAow
gg90dzae
bL6900
(OV) ‘b8S#
AM*eAoUW
PBOO0DEDE 016900
(gw)969$
Q°4T9
D6900ZZP 296900
7269$
Isq
8ST9 W96900
La‘ (T¥)o0
0 &*aAow
O0006zHE 996900
(ov) ‘7es#
MM‘ eAoW
ZBO00DEDE
796900
b669$
iIsq
ZET9 096900
331

<!-- source-page: 339 -->
## Page 339

(633
oO69CC
6012
bra
$63E0
BOO
OI
I II
TIO
IR
IO
III
IO
Oa
kk ded doe doe
0069CE
6110
bsr
$69E0
0069D0 3E39FFFF8604
move.w
SFFFF8604,D7
0069D6
6008
bra
$69E0
DORK KI
IO
IOI
OK RII
OK RR RK
IK EK RR
RR
O0O069D8
6106
bsr
S69EO0
OO069DA 3039FFFF8604
move.w
SFFFF8604,D0
OO69EO
40E7
move.w
SR,
-(A7)
OO69E2
3F07
move.w
D7,-(A?7)
0069E4
3E3C0020
move.w
#$20,D7
QO69E8
51CFFFFE
dbra
D7,$69E8
OQO6SEC 3E1F
move.w
 (A7)+,D7
OO6SEE
46DF
move.w
(A7)+,SR
OO69FO
4E75
rts
FOO
I
III
IOI
OR
IO
tk Ok
a dOk
a tok
a tek
hk
O069F2 0C790001000004A6
cmp.w
#1,$4A6
OO69FA
662C
bne
$6A28
O069FC 302F0010
move.w
16(A7),D0
OOGA00 BO7900004692
cmp.w
$4692,D0
OO6A06
671C
beq
$6A24
OO6A08
3F00
move.w
DO0,-{(A7)
OOSACA 3P3CFFEF
move.w
 #-i7,-{(A7)
OO6A0E
6100EB4C
bsr
$555C
OC6A12
584F
addq.w
#4,A?
006A14 33FCFFFF00000676
move.w
#SFFFF,$676
OOGAIC 33EF001000004
692
move.w
16(A7),$4692
OO6A24
426F0010
clr.w
16(A7)
OO6A28
4E75
rts
Delay
loop
for disk controller
rdiskct?
Delay
loop
for disk controller
dskctl
Delay
loop
for disk controller
rdiskctl
Delay
loop
for disk controller
dskctl
Save
status
Save
D7
Counter
Delay
loop
D7? back
Status back
change,
tets
disk
change
nflops
None
or
2
floppies,
done
Drive number
Equals diskette number
?
Yes
Drive number
*insert
disk'
Critical error handler
Correct
stack pointer
wplatch,
Status
for both drives
unsure
Save diskette number
Drive number
to
zero
Surysyqng IIL]
Sfeusouy LS Wey

<!-- source-page: 340 -->
## Page 340

Atari ST Internals
First Publishing
Aep ppy
uTqpoq
uoTATsod
ut
AsTYS
Puy
yquou ppy
uTqpoq
uotytsod
ut
ajzytus
TeaR
0g
JO JeszJo
JoeRTIQNS
uTqpoq
AajJJnq suUTA-yOoTS
of Asqutod
SY 2Pe8TO
yeuIOJ
SOd
UT eWIOJ
daNI
‘ewTasopl
sbetj ASTP
‘IxSP
epow sATIP es
zequnu
eATip
3eb6
‘aepo
apow saes
aTqey epou
yxsTtd
apow ehueyo aaTip
jes
‘aspoupyes
za‘oad
ocags
z7d’S#
za‘od
ocags
7d‘ b#
za‘od
oa ‘os#
oeggs
ow’ (GW) EbWS
cv‘0$
q°ppe
aisq
T'1se
q°*ppe
Isq
T'Tse
q*aaou
q°qns
isq
eat
eeT
00rd
WO0000T9
c8ad
o0opd
ZQ0000T9
786d
OObT
0S000060
aqoo00tg
EbWOaATD
000000006
44Pr
89V¥900
p97900
Z9¥900
09900
254900
¥svg00
8svg900
bSW900
osv900
OPW900
9bY900
errr Tere Ter eTrPeTErrIPere re. eS SSeS
ES SSS
ee
0
OTTOOTOTS
TTOTOTOOS
OTOTOTTOS
Ood0000TS
TTOTTITT%
TTTOTOOOS
OOTTOOOTS
OTTOTOTTS
OTTTOTOTS
q'op
q°op
q*op
q°op
q°op
q*op
q°op
q°op
q*op
q°op
00
OW
24
v9
08
aa
LT
28
94d
qv
Sbw900
pbv900
€bwW900
ZbW900
Tpw900
ObW900
JEW900
aew900
dev900
DEWI00
SOR
OR
ORO
ROL RO
OR OR ORE IA
OR ROR
EA
IO
EE HF
(m°0d
‘0W) 07+ (LY)
0a’ (Gv) b89$
(LW) -‘0G
ow‘vzaes
sja
q°* aaow
M* aAoU
q* aaou
RaT
SLab
OO00METT
bpsg0dcoe
O0dT
VCACOOONS6
ATH
VeEwg900
9€V900
cEV900
oev900
Wewgane
JER KER
OR
OL OE
OR
OR OR
OE
ICC
OE
OR
KO
333

<!-- source-page: 341 -->
## Page 341

Atari ST Internals
First Publishing
UOT ANTOsaL puovas-Z
spucoss
‘7-9
SATQ
a zejTos]
OP
OL
4TseAUOD
Of AUITA
4285
Z3JJNq out}
Jo pus
o4 AsqUTod
suT
AP qyT
aUT
 sseg
ajep pue
awt} yooTS
jes
‘euwTqIes
Od
UF eWTR
4°85
a7em
‘ON
& PSATAIS SUT MON
puss
pueuwos Aep
jo aut
4305
OWT} AOJ
HeTy syeyspury
ysonbeay
ajyep pue sUT
 YOOTS quezino
yeh
‘ouytq Web
HeTzy
ayeyspuey
AeseTo
SUT} MOU SAeS
spuodes ppe puy
UOFINTOSeA puoosss-Z
uTqpog
uoTqTsod
ut
4sTYUSs
puy
oqnutTwu PPpY
uTqpoq
uoTtytsed
ut
3yJTYys
puy
anoy PPV
uTqpsq
uoTyTsod
ut
3yiTus puy
od‘T#
od‘ te¢
oa‘za
za‘ (S¥) OSWS
ov ‘¥Svs
q’* {Tse
q’pue
q*anou
T° eaou
POT
o0td
AT0000C¢0
ZOOT
OSVOdd
YSVOOO006dTD
0OV900
OdV9 00
Wav900
98900
OuV900
ROR KR
AK RR
KOR
RE
ROO OEE ORR KOR ORE OE OR KE EOF
(S¥) OSWS ‘(LW)E
T* eacw
OSVOPOO0dSEZ Vvv900
RR ER OR
OR ORR EO OO ORE YOR ORE
LOE OR EE OR OE
0d’ (GY) Dpvs
AGIOS
(Sv) a8ws
oao9$
Ta‘Ots#
(S¥) a8vS ‘T-#
sql
T* enow
auq
q°4sy
Isq
q* sAow
q* SAow
SLap
opwodco~
VdA99
ABVOUCWP
pECOOOTS
DTOODE
CT
d8wOddddOLaT
8vv900
pvVv900
ewv900
46V¥900
W6Vv900
96¥900
06V900
MR RMR RRO
EO
OR OR OR OE
OR OR OE OK OR IE
aE
OK
(Sv) A8ws ‘OS#
(SW) Opws ‘7a
za‘oa
oa‘T#
o£dgs
Za ‘SH
z7a‘od
OEM9S
7a ‘OF
za‘od
oecdgs
7a ‘GH
$qa
q*eaow
T° aaow
q*ppe
q° ast
asq
T'Tse
q*ppe
asq
T'Tse
q*ppe
1Isq
T'Tse
GLab
A8YOO000DLET
OPWOCDAC
00rd
8074
cdOO00TS
csdd
ood
Vd0O00TS
esdd
o0bd
ZQ0000T9
e8dd
48V900
88v900
b8v900
28V¥900
o8v900
OLVI00
VLV900
8LV900
bLYI00
éL¥900
OLVY900
O9V300
V9V900
334

<!-- source-page: 342 -->
## Page 342

Atari ST Internals
First Publishing
dduI
oF pues
puewwos Aeq
Jo owTL
229
puss
YOOT Jaqjewered ay}
jo sseippy
pues
03
saqAq
jo
7ASsquNN
deur
OF pues
puewwos
Aeq
JO eUTL
2eS
L-0
€-0
5-0
b-0
qeszyo ppy
4raeAuoD
S}Tq a3eTOST
zeaz
qzaauog
SATQ aqeTOsS]
yquoW
YIBAUOD
S1Tq a3eTOS]
Keg
qzeAUOD
SITQ aQeTOs]
sinoy
qazeauoD
sjTq aqeTos]
o3nutW
qzeauo5
0aD9$
Ta‘OTs#
04D9$
cw ‘SVs
€a’s#
0aa9$
Ta‘als#
(OW) ‘O8S#
STagos
Oa‘ dist
oa‘za
7d‘ oe
BTa9$
oa‘sT#
oa‘’za
za‘S#
stags
od‘TeF
oa‘za
za ‘GH
8189s
oa‘Tte#
oa‘za
7a‘9o#
8Ta9$
od ‘E9F
oa‘za
za‘s#
8Tdg9s
sya
aisq
q* aaow
isq
eat
TT‘ beaow
iIsq
q’*saow
q*ppe
Isq
q*pue
q°*aaouw
T°4sT
Isq
g*pue
q° aaow
T°ast
Asq
q*pue
q*aaow
T° ast
Isq
q°pue
q*aaoul
T°4sT
Asq
q*pue
q‘aaouw
T°4sT
Isq
Slap
Da TO00TS
DTOODE
CT
vATOOOTS
bsvoooo06
dsp
SO9L
oaToooTs
ATOOoE
eT
O8000T90
cclo
431000020
co0ot
Vesa
I2T9
41000000
coot
W8va
9ETO
AT000020
coot
VW8Va
Opto
4IT000020
coot
W800
WPl9
4000020
z0ot
vevd
6ST9
9TE900
cTd900
400900
Wod900
v0d900
Z0d900
AAV9I00
VWdv900
9.4900
baAv900
O4V900
aaIV900
OaV900
Waw900
94V900
vav900
7AV900
Oav900
2av900
Wav300
gaqaw900
9qv900
z7av300
odv900
AOW900
99900
8O¥900
9OV900
bOW900
T3300
335

<!-- source-page: 343 -->
## Page 343

Atari ST Internals
First Publishing
WO
Jou
snyeqs
30
q4so} puy
snqeqs YIOW-IGIN pes
MO
07 ATRejod
snqjeqys
yndano
[qin
‘3sOTpTW
soe{d
s,ueq
sttd
aovrtd
s,auo
ayejTos]
aoetd
s,ua]
aqdq aod
AreuTq 01 Gq WeAUOD
/uTqpoq
Zajjnq
ut
4TNsear S3TIM
souo ppe puy
aeTaqtu
zaddn
ut
suaz
Jayunods
s,eu0 aje138Uay
ZTa4unoD ¢,ueQ
4yUusWaeIOUI
Ol JoPA3GNS
OT peot
zJaqunoo
s,uay,
ddqd
02 a4Aq
YIeAUOCD
“poquTq
oa‘o¢ T*’beacu
8SH9s
auq
ca‘t#
481q
70‘POOddAAIS =" BAOW
oa’t-# T*baaow
OOOL
2099
TOO00Z080
PODTIAIA6
EFT
4d0L
959900
6Sd900
0Sa900
Wva900
8ba900
JOO
ROO YOO
ER OOOO
OOO ORR OEE RR RR RE RR
RF
sji
oda‘ta
M*ppe
Ta‘St#
4° pue
Ta‘+(ow)
q*aaow
od‘ta
q*ppe
od‘z¢#
q°[se
Ta‘oq
q*aaou
Od’ T#
Q°Tst
0d‘ bF
q°* ast
oa’ (ov)
q*eaou
od‘o#
T*baaou
SLab
Tpod
JOOOTHZO
Stet
Tood
o0Ssd
00¢cT
g0ea
808d
OTOT
O00L
978900
bPa900
0bd900
G€8900
3€8900
Wead900
8Ed900
9€H900
Pead9I00
ce€a9 00
O€d900
OR KORE OR ROE RKO
LOR ORO
OO OR YOR
OL OR YOR
OR OE ROE OR OE
sii
(OW)-‘0d
q°eacu
oq‘ta
q'ppe
Ta‘b#
Tse
oa‘OT#
 a'ppe
ota9$
e1q
Ta‘t#
a°bppe
pcags
yugq
oaq’eq
=
agq'qns
€qa‘OT#
T° beaow
Ta‘o#
T°’ beacw
GLab
ooTT
T00d
To6d
0000090
8409
TQCS
pods
£006
WOOL
002L
4720900
228900
VW2ad900
8cH900
bcad900
ccd900
0cd900
aATa900
3Td900
VTd900
8Td900
Perr rTeTererere rer errrrerereLe Lele 22
2
SS
SS See
ee
336

<!-- source-page: 344 -->
## Page 344

Atari ST Internals
First Publishing
YO
JON
Tenbe
10N
qseq etTqeyjdnazzequtun
xOpul
[Tel
XOpul peaH
aqTnejep
se 40
VIOW-IGIW
0}
228RUTOd
IGIN 103
90810T
SNAPS
ASATED8T
JCIW
’3eqspTw
aqyAq
7XON
IGIW 03 3nd NO
Huti4s wor
aykq 3a
Hutiz4s
ayy
Jo sseippy
[- BuTz4s
Jo yybuey
IGIN
©} 6uyaqs pues
‘SMTpTw
WIDOW 03 e7Aq yndyno
yO
TTRUN
ATeEM
SOL
snqeqs IdIW
3°89
VIOV-IGIW
0} JejUTOd
qeqorieyos 4a
IGIW
0} Zeqoereys qndyno
‘omMTpTwW
sqi
oa‘o#
T*beacu
7wd9s
auq
+(2u)
“+ (Ev)
wtuduo
ew‘! (0W) 8
POT
ev‘ (ow)9
eoT
oda‘T-#
T*baaow
TW’ pO0TT AAAS
PoT
ow‘ (S¥) OOWS
eet
SLaP
OOO0L
Z099
apsa
80008HLP
90008dSP
ATdOL
boOodd
dd 46 JEP
oowoddTp
Z7WA900
owdg00
468900
268900
868900
peédgoo
768900
288900
88a900
SO OR OR OOOE
O ROR OOOO
ORO
ROR ROR
CIE ORR
RF
sqi
aLags$ ’€a
eiqp
asags
aisq
Ta‘+(Zv)
q°saaou
av‘ (4W)9
T° eAow
eq’ (iv)
Ms’ Baow
eaq‘o#
T°’ beaow
SLAP
Vdd
dd ots
3aTt9
Varal
900049
FZ
POOOAZIE
OO9L
98a900
288900
088900
aL8d900
WLa900
9La900
'La900
PPP PETETe TESTES TOC TIS Lee
eS 2S Se ee ee ee
$s qa
(tw) z‘Ta
q*eaow
p9ao$
beq
za‘T#
4834
za’(T¥)O
gq’ eacu
TW‘ poddddddS
eeT
Ta‘(4W¥)9
= M* BAC
GLap
cOOOTPET
9AL9
TO000Z080
o0006ZFT
PODMdII
46 TED
9000A22E
7La900
498900
398900
898900
'94900
4Sd900
¥Sd900
PCT TCT ECCT TOC TTPO
L
ESP TEL ee
eee ee ee
sa
SLAY
8Sd900
337

<!-- source-page: 345 -->
## Page 345

Atari ST Internals
First Publishing
peyoeaz
4aA ON
é
spuooes
OF
auT.
4qzeq4s
snuTW
TayuNneds
ZH
00Z
¢
Apeai
za 4uTig
qsoQ puy
snqypias
asna
3285
zeyo sty OJ
awTQ
4yreys
‘Jaqunoo
2H 00Z
qno owt
‘saz
é
spuoses
g uey Siow
pa Tem
4noewt} Jequtid snutW
Zayunod
ZH
00Z
soTUOI4UaD
oj
JaqyoeRATPYO
Yndyqno
‘44NoyAST
snqeys 310489y
XOepuT pesy Mau eAeS
ZeJIngq woray
AB_oPAPyo 4s
Z3jJjnq IGIW OF ASAUTOd
ujTebe
4yieqys
Jejgng
ye
utTbeq
ON
é
eZTs eying ueyy
1s jes15
XOpUuT peasy jUsWeToOUT
X@pPUT TT YATA ateduocg
XapuT
peoeHy
sqdnizequt etqestp
‘i TdI
snjeqs
anaes
ON
¢
Apeaxr
za,oereyD
Ze aspTw
IGIN wory
raqoeTeyo
Job
‘uTptw
saqgo$
414
€q’0009#
tT'duo
€q’zq
ss T*qns
eq‘ (sv)vap$
T° eacu
9009$
auq
oad
=4°483
3g09$
isq
za‘ (sw)vaps
T*eaow
PECCE
sog
za‘ooot#
 T'dwo
za‘ (G¥) O8vs
T’qns
za‘ (Gv)wars
T° eaow
ogq9
OLLTOOOOE8D0
7896
Varodcgd
8199
ObWP
eLtg
Warodeez
BTS9
84€0000072890
Oswodvbe
Warodzye
WiId3 00
7.18900
7489 00
Fdd9 00
0dd9 00
Wada900
8ad900
bad900
cda900
3083900
8dgq900
7dqdg900
HORROR
OR ORO
OR
OR
ORE ROR
ROE
sq
US‘+(LV)
M*eaow
(0W)9’°Td
mM aaou
oa‘ (M*Ta‘Ty)O
4 q*eaow
Tw‘ (OV)O
T° eacw
Ta‘O#
T° boaow
pOdgs
“saq
Ta‘(owp
«duo
Ta‘T#
Ms bppe
0adg$
beg
ta‘(ow)g
sa‘duo
Ta‘(ow)9
=A eAou
US /OOLS#
M* ZO
(LW)-
‘as
At eaaou
pwagas
baq
og
Massy
ggags
sq
SLap
Ad9 0
9OOOTHTE
OOOTTEOT
000089¢¢
00¢eL
Z0S9
yooos97d
Lees
9TL9
800089
ca
90008C2E
OOLOOLOO
La0v
VAL
OVD
calg
z7aq900
0dg900
3924900
go8900
p2a900
298900
028900
288900
WaH900
gus900
paa900
oaag00
D¥a9.00
WV¥A900
BYa900
ava900
p¥a900
Pee TE CeCe Cee
C eS eee TS
Pee Le eee
ee
SS
eS
ee
338

<!-- source-page: 346 -->
## Page 346

6ce
OO6BFC
OO6BFE
006C04
006C06
006C08
006C0C
OO6COE
006C12
006C16
006C18
006C1C
O06CIE
006C22
006C24
006C28
O06C2A
006C2C
006C2E
7000
2B6D04BA0A80
4E75
40C3
007C0700
7207
61000E28
00000080
7287
61LQ000E1E
46C3
302F0006
728F
61000E12
610C
6104
7OFF
4E75
moveq.1
move.1
rts
move .W
Or.w
moveq.1
bsr
or.b
moveq.1
bsr
move.w
move .wW
moveq.1
bsr
bsr
bsr
moveq.1
rts
#0,00
S4BA (A5)
, $A80 (A5)
SR,
D3
#$700,SR
#7,D1
$7A38
#$80,D0
#$87,D1
$7A38
D3,SR
6(A7) ,DO
#$8F,D1
$7A38
$6C36
$6C30
#-1,D0
COOK IO
RIK IO Ok
kk
kkk tok kk ka ke
006C30
006C32
7420
60000846
moveq.1
bra
#$20,D2
STATA
KOK KKK IKK K KK IK KKK IK II KK IK KK KK KKK KK KKK KK KEKE KK KEK
006C36
006C38
74DF
60000E66
moveq.1
bra
#SDF,D2
$7AA0
ok OO
kkk kok
tok kkk kak kkk RR
RR
006C3C 7207
006C3E
006C42
61000DF8
0200007F
006C46
7287
moveq.1
bsr
and.b
moveq.1
#7,D1
$7A38
#S$7F,DO
#$87,D1
Flag
for time
out
200
Hz
conter
as
last time-out
time
Save
status
IPL
7,
no interrupts
Mixer
Select
registers
Port
B
to
output
Write enable
Restore
status
Character
to
output
Write
to port
B
Strobe
low
Strobe
high
Flag
for
OK
Strobe high
Bit
5
Set
Strobe
low
Bit
5
Clear
listin,
Get character
from parallel
port
Mixer
Select
register
Port
B to input
Surystyqnd ISI,
sjemssyuy LS Wey

<!-- source-page: 347 -->
## Page 347

Atari ST Internal
First Publishing
Zeqoerzeyo
yob
‘jabzezs7z
afem
‘ON
é
Apeazr
Jaqoezeyo
‘uTxne
Zez-Su
Taqyorzeys
job
‘utTxne
aay AsAeIPYS
ON
ON
é
JaaT
tozgng
xopul ITeL
XO@PUT PPeH
yo 02 4Tneyed
ZEZSY OJ DaI0y
snqeqs
yndut
zezsu
‘}eqasTxne
Asnq TIt3s
40
Asnq
3se]
yo 02 ATNeJaq
ddW ey}
Jo
ssozppy
snqeqys
qaod TaTTezed
‘jeq4sOCqST
yaod woiy
3ajhq peasy
@q
yaod
4aTes
Asnq
=
MOT
eqor3S
S8ATIIS AajoereYyoO
TTIun
ATeM
snjeis
qzod TetTezed
1a5
Asnq
jou
=
ySty
aqozys
8aS000T9
285900
WAlL9 W89900
ObWP
889900
992L$
1sq
9899$
baq
od
= 3sy
0LD9$
asq
8aTt9
989900
OREO
OR
OO KORO
OR OR
SOR OR
OOOO OE KOR OF
od ‘0¢
b8D9$
+ (Z¥)
4+ (EW)
ev‘ (ov) 8
zw‘ (ow) 9
od‘t-#
ow’ (sw) 0d6$
sya
T’ baaow
auq
awd
eet
PaT
T‘baaou
eat
GLap
bEDgO0
O00L
289900
2099
080900
absd 719900
800084Lb VL9900
900084Sb 919900
dd0L
6L9900
Od60daTh 0L5900
DOR KOR LOR
OE
OE OOO
OR
EOE ROORKEE
OR RE
0a ’0o#
a999$
(OV)
0 “OF
Od‘ t-#
OV‘ TOWd
dd Ia$
si
T' beaou
baq
4s 4q
T° baaou
eoT
GLa’ 499900
O00L 999900
Z0L9 Y¥99900
000000008280
#95900
JAI0L
7299900
TOWAATITI6ITH DS9900
POPC
ETE TELOSe TPCT TSSOLOS SSS TEL LES ELS ESE ES SS
SS
BEWLS
Ta‘St#
9£D9$
BpO9S
od
3S99$
O£D9$
BEYLS
eg
T° baaow
Isq
auq
M*48S)
aisq
asq
asq
Aqd00009
859900
JO7L 959900
OdT9
€90900
VA99
59900
OPWh
050900
30T9
AvO900
faT9
970900
FACOOOTS
8bI900
340

<!-- source-page: 348 -->
## Page 348

Atari ST Internals
rst Publishing
onan
~~.
Apeau
snqeqs
3e5
VIovw preogqkay ayy
jo ssoippy
eyhq
2209
CGYI
oj
TayoOeTeys
pues
‘OMpPQyT
Apeez ON
MO
q4soL
snqeqs WIOW dayl
yo
oF ATNeZEq
snjzeqs
qndyjno day
‘3s0pqyTt
utebe AIL
qndyjno pue
‘qndzezsi
ayf4q e1ep
48D
euTynozr
jandyno
zEezsy
‘ynoxne
Jayjng
ut
eoeds
siow ON
Tenbe
ION
xapuyT peey
YRTM ezeduloD
punoze
deim
toy
4se]
XepuT
TTeL
yo
o3 3TNejEqd
ZETSY
AOJF
DOICT
snqeays
yndqno
zezsu
43e3soxne
L-0 S3FQ GIeTOSI
za‘t#
353q
za‘(tv)o
q°saow
TW ‘0007 ddd a$
Pet
Ta‘(iv¥)9
M*eaou
T0007Z080 YQ9900
o0006zFT 909900
O0DTdMAIdAEAE
009900
9000d2ZE 295900
PoRETPET TTC CTOSELET ESOC
LL SS
ee
SS
ee
2 eee
S$ yz
oa‘o#
T° beacw
WOO9$
auq
za‘T#
asaq
7q‘o000ddaddI$
=F" SAOU
oda‘’T-#
{*baaouw
GLap WOO900
000L 895900
Z099 999900
TO00Z080
295900
OODATALI6E
PT 989900
Ad0L W900
POUT
ETE TST TTT OT TT PTET
T
TT SSL LST ee ee
$3z
avo9$
soq
WOZLS
isq
Ta‘ (L¥)9
M*eAoW
GLab
889900
9459
989900
9SS000T9
2@49900
9000M¢¢2E FYO900
POPE
ECE TT STP TPCT TET TTS
T LLL
Se Se ee
si
od/o#
T° besow
DWD9$
aug
za‘(ow)oz
m*duo
BISL$
asq
za‘(ow)
cz
=f eAOU
od‘Tt-# T'beacw
ov‘ (SW) 0d6$
eet
GLab IWD900
000L ¥¥5900
7099
8WO900
PTOO89PE PYO900
DLB000T9
OVO900
9TOO8ZPE 969900
dd0L Y69900
od60dadTtb 965900
OO
ROR OR KOR
OR OREO OEE AOR ROR AOR OR UR ER ROR
ROR OR
RE
sqa
oa’ sas#
M°pue
SLdb
b69900
JIOOORZO
069900
341

<!-- source-page: 349 -->
## Page 349

Atari ST Internal
First Publishing
xXOpuT
TTe YRTA ezeduog
xeputT peep
sqdnizaqut eTqestp
’/ TdI
snjeqs
aaes
aes
‘ON
é passaid Aay
‘Reqysuoo
paeogqkey wory zayoereyo
yeh
‘uqtuoo
azr9sy4 srajoReyo ON
ON
é
JaetT
ryjjng
xopuT
TTeL
XapuT peey
yo
of 4TRejEq
pazreoqhay
TOF
DerOT
snqeqjs
yndut pieoqkay
‘ze jsuoo
aqAq
3xXON
qandjno puy
butzqs
woiz
a3Aq
3e5
Hutazys
syQ
jo
sseippy
[- siejyorieyoS
jo
rzSquNN
preoghsx%
09
Bbutaqys
puss
‘sapqyt
Zajoerreyo
y3ndyno
qTeM
‘ON
zpags
baq
DTL9
¥zaG900
Ta‘(ow)g
a*duo
go00089zd 0za900
Ta‘(ov)9
#*aaou
90008ZZE DTa900
US ‘OOLS#
M°I0
00L09L00 8ta900
(LW)-
‘YS
M*eaow
La30b
9140900
oTa9$
baq
W4IL9
bTAG900
od
=f 4s
OPW
ZTG900
Wdo9$
4Isq
8419 010900
FEO RL
OR
ROR
OR
OR ROE
ORE
sja
SLab 30a900
od‘o#
T° beaow
000L 200900
H0a9$
auq
Z099 ¥YOd900
+(2W)
4+ (ev)
9 acudus
aysd 800900
ew’ (ov)
Bat
B000B8SLb)
¥Od900
ew’ (OW) 9
eeT
90008ASb 00a900
od‘T-# T’beaow
Ad0L 719900
ow‘ (SY) 246$
aT
ZA600ATP WAD9IOO
ROR OR LOR
OR OR RO OE
OR
OE
OE ORE KR OR
RE ER
sqz
Giab 849900
0499$ ‘Ed
ezqp
Widddots bdd900
oqa9$
asq
2aTt9
249900
Ta’+(zZv)
 q*aaou
WIZT 049900
zw’ (4W)9
«= *aaow
900049h2 949900
ea‘ (LV) pb
AM’ eaou
POOOAT9E 830900
€a‘o#
T° beaow
0094 949900
ER
ORK OE RR OR OE OER OE ORR KORE
OR OR
OE OF
sz
GL4b
b4D900
(TW) Z‘Ta
9 =q*eaou
ZOOOTPET
039900
9dD9$
baq
94L9
3d9900
342

<!-- source-page: 350 -->
## Page 350

Atari ST Internals
rst Publishing
ii
00$ ‘00S %i-a ‘a's
d
a
i
1H. 4,U,
Gd
hg
nn
Kn
An
aT
1008
Ha
al
Paar
ar
ere
a
a
SR
or
1844281
“00S
Toate
fed
a
Sede
1a Oe
Ta
aa
Za
da
te
en
Ma
By
qe‘
SQ
gn ta
100
160
18s
“ads
191
1G
ba
Ea
aa “ats “989400$
peasytusun
‘atqez preoghay
Jawty punos
41eIsS
{Taq OJ
atTqey punos
0} ASeqUTO”d
ON
& petqeuea suoy
) TYLD 1eqze
auoq
‘TeqbuT1
yo sAeaty
snqeqs
yndyjno
ajtosuos
‘ys jnouoD
snjeqs
a704Ss0y
L~O
SATQ
93
BPOS
TIOSV
€Z-9T SITG 07 SpoouPDS
XOpuT peey Mau
ears
apos
ueos
pue Jaqzorreyo
499
lajjnq pieogqkay
of
TeqUToOg
4ze js
02
YORQ IsjuTod tezgng
ON
azts
zayjng
Tenbse
Io vey
139e3515
Z
+ XepuT pesHy
(Sv) Waws ‘OS#
(S¥) 98WS ‘WSALS#
09ag9$
(SU) bBbS ‘ZH
od’t-#
T° beaow
us /+ (LW)
0a‘8#
0a ‘SF
(ov)
9 ‘TC
od‘ (M*Td‘Tw)0
0d ‘OF
tw‘ (ow) 0
Ta ‘o#
oeags
Ta‘ (OW) &
1d’c#
q'op
q'op
q‘op
q'op
q°op
q'op
q°op
ce §
q*eaou
T* aaou
baq
asqq
RR MR
MR
ROR OER OE KO
ROR
LORIE
OR
OR ROR KOR OE
sqz
sya
M*OAoU
M*IST
T°TST
M* aAoU
M* SACU
T' baaow
T*aaow
T’ baaow
soq
a duo
a*bppe
0000022970949
Z9
9LESBLELALOOECHR
069989 V989L999 9
ELT9OOCOAZTBOLAI
69GLVLPLZLS9OLLTL
6080L7TH60EGEBELE
9ESEPECECETEATON
SLap
W8VOOO0O0DLET
9BVOVSGLOO00DLEZ
A0L9
b8b070000780
GLav
JAOL
SLab
409%
8b0ad
asta
QOOOTPTE
OOOTIEOE
000L
00008922
00zL
z0s9
po00s9za
Tbs
760900
¥8a900
280900
VLQ900
@L0900
W9a900
790900
PEeCTCrCTTT TET Te TOTO CTOCS OCIS CSL OT SSS TELL ESS SS ES eT
094900
WSa900
7S0900
0S0900
wpaso00
8ba900
970900
ROR RE OR
OR LOR RO
RR
ROR OR ROR AO
OR OR OR
AIR IR RR CE
§Pa900
2'a900
0P7a900
ad€q900
WEa900
9£a900
bEdI00
0€d900
420900
920960
8cd900
920900
343

<!-- source-page: 351 -->
## Page 351

Atari ST Internal
First Publishing
yoo],
sdey
‘atTqey pioceqkay
peartus
‘aTqeq parrogqkay
Za
Oe
Za
aba
et
ee
aM
1 Oe
qe Qs
On
000
56
Ba
aks
190
Ga
Ba
cba
Se
a Ta {9894008
00$ ‘00$ ‘00$ ‘00$ ‘00$ ‘00$ ‘00$ “00$
00$400$‘00$/00$700$4
494,74 4101
la
Sa
aT
Oe
Ga
a
ba
0G
Ba
platen
afin
le (a0)
1 4008 4008 4aK<1
00$ ‘00$ ‘00$ ‘00$ ‘00$ ‘00S 700$ ‘00$
00$ ‘00$ ‘00$ 700$ ‘TEP 4101 “0084121
00S
ata (192
008
2 ba
ama
(005 418:
1L£1 400$ ‘00$ ‘00$ ‘00
’00$ ‘00$ “00$
00$‘00$
‘008 ‘00$ ‘00$‘00$%,
1 “00$
0084008 4aTa ‘eta fafa
aWa “aNa ‘aa
Aa
On
Xa
aKa
Te (008 4a
fala
Na
Te
Me
ela eH
De
eda
Ma
192.44 “00$
4T94 ema
sada
ede 4101
Da
Oe
Ze
De
Me
Re
Me 418
Ted
sq
eta
eda
esa
a
(a
ede ase
a
Ke
Se
aT
a
i
(988400$
00$ /00$ 100$ ‘00$ “00S ‘00$ 00$ ‘008
008/008 400$‘00$/00$
4297.54 4108
oy
Ae Oe: Pe
nee
3
2)
phate
fala
(a
1184
(008
4008
71>.
00$ /00$ ‘00$ ‘00$ ‘00$ “00$ ‘00$ ‘00S
00$ ‘008 /00$ ‘00$ ‘TEP “00$ “00$ “008
00$ 414s {008 ‘00$ ‘00$ “a-s ‘008 “008
00$ ‘00$ ‘00$ ‘00$ 00S ‘00
“008 “00S
00$ ‘00$ ‘00$‘00$
‘008 ‘00$%,.
«00S
q'op
q'op
q'op
q'op
q'op
q'op
q°op
q°op
q°op
q'op
q'op
q'op
q'op
q°op
q'op
q°op
q*op
q°op
q°op
qrop
q'op
q'op
q*op
q'op
q'op
q'op
gq’ op
q’op
6PSSWSPSCSSPLSTS
6O80LTAGOLEEBELE
9EGEPECECETERTOO
Oo
oO
0000000000
n900000000
LEW7ACE CBCOOOORE
0000000000000000
OOOOD000ALOEOOCE
OORCIEOOPEAZOOBE
££00000000000000
0000000000000200
OOOOASVEMEGPARCH
9SEbPSS6SOLOOdSas
6690PESUVPSPLEO
PDE
ESTPOOCOWZVE0SAP
6RSSWSPVSZSSPLSTS
608009 FEaE6 78 7dz~
97g7epcadecTcadtoo
0000000000000000
OOCdDOONOOdONZOE
ECC TETEICSEPEGEBE
LEWCA7E
78 COOO0DE
0000000000000000
000000004L000000
008Z0000000Z0000
0000000000000000
0000000000000200
2L4900
W94900
94900
DOR
KOR ORR OR OOOO OORT
RR IOR RR ROR OR RE
oF
VSa900
7OWANN
Gausuyv
Wba900
264900
WEd900
c€4900
Wed900
€24900
WTA900
cTd900
VOud900
204900
ViId900
7410900
Wiqg00
cda900
PeCETE TTC TTS
ST
Tee Te
Te SCTE TELE Tee See
ee ee
wadqs 00
2dq300
WOd9 00
€00900
wdaq900
c8qa900
Vvq900
Z¥Q900
Veas00
344

<!-- source-page: 352 -->
## Page 352

Atari ST Internals
first Publishing
SpucoesTTTTu
OZ
OR
sw IBUTL
Wa-s yes
‘gpg OF
# TOIYEAOANe-UON ddW
ddW 842
jo ssoippy
10689
ddW ezTTeTatuy
‘dyuqrtut
q tawtTy 4oeTeES
oa‘e#
qdnazzequt [Te3sut
“4uTyAyuT
OPTLS
zequnu ydnizequt
2 1eUTL
0a‘S#
euTynor
ydnazzequt
Dp TewWTL
zZ¥‘OSOL$S
JojoeA 4YdnzzeqUyT pue zewT. szTTeTqtul
O60L$
.
cé6T
70 ‘0D$4
ZH
002
203
69/
Ta ‘Ost
9) Jawt WeTES
oa‘z#
(SW) Cbs ’07#
(SW) beWS ‘TTTIS#
(OW)
22 ‘8 bS4
JA 04 Qist
(oW) OTS “0d
qis}T
04 QieT
(ow)
8 ‘0a
erst
oj dtdb
(ow)
0 ‘0d
O198Z UTM sieqysTber azytTeTazul
oa‘o#
OW
‘ TOWd
dd dd
00$ ‘00$ ‘00$ ‘00$ ‘00$ “00$ *00$ ’00$
00$‘00$‘00$00$‘400$"%
4941°4 4101
0
Sa
Te
608
Ge
a Ba 06s “1 Bs
pha faee
i a/a‘ (140) 2400$400$
14>.
00$ ‘00$ 400$ 700$ ‘00S “00$ ‘00$ 700$
00$ ‘00$ ‘00$ ‘00$ ‘TAP “00$ ‘00$ “00$
00$ ‘14. ‘008 ‘00$ ‘00S %1-1 ‘00$ “008
00$ ‘00$ ‘008 ‘00$ ‘00S ‘00$ ‘00$ ‘00$
00$ ‘00$ ‘00$ ‘00$ ‘00$ ‘00$ “00$ ’00$
00$ ‘00$ ‘00$’00$
‘008 ‘00$‘4,
4 “00$
0084008 fama
fa
a
fa
fa SW
“aN
“2G
tA
Da
Xa
ke fT
(00S aH
ete
Ne
Te
Ma
ee
eH
Da
ad
“0a
15a aWs
008
(TD
ete
ed]
eds 7101
T* beaow
Isq
T° beaou
eeT
4Isq
M*oAOU
T' beaou
T' boeaou
M*aAoU
M° SACU
q' aAou
[T° daaou
tT‘ deaow
T° daaou
T° baaow
RPeT
q'op
q'op
q’op
qrop
q'op
q'op
q'op
q'op
q°op
q'op
q'op
q'op
q'op
q'op
€O0L
ezzoo0ts
SOOL
DGOLOOO06
ASE
ALTOOOTS
OD00DE
FE
OSéL
ZOOL
2bPOPTIOOOLEE
PEVOTTTTOLaE
9TOOBPOODLTIT
oTOOsoTO
80008DTO
000080TO
OOOL
TOWA
IAI 16 ATP
0000000000000000
O000D00000dOAZOE
EEZTETESESEPEGEBE
LEWCI76 CBCOOQODE
0000000000000000
0000000042000000
00d20000000z0000
0000000000000000
0000000000000000
0000000000000¢00
O00O0dZaAZIZabav
ey
9SEPBS9ESTLOOECAB
66DVEPVESELEIPID
EST POOdOCEZW6E0SAb
024900
3T4900
VT4900
bT4900
OTA900
20.1900
W04900
804900
204900
249900
944900
?44900
ad4900
Vad900
844900
7ag900
errr rrrr eT Te TT PeTPSTICereE Pee LeLeLe
Le re sy See
ee
Se
eS
Wad900
7dd900
WOd900
294900
waa900
7d4d900
wvwd900
7WA900
464900
Y¥6d900
764900
Wea900
784900
VL4900
345

<!-- source-page: 353 -->
## Page 353

Ore
O06F22
OOGF24
O06F26
OO6F2A
O06F30
006F34
006F38
OO6F3C
O06F40
O06F46
O06F48
OOEF4C
OO6F50
OO6F56
OO6F58
O06F5C
O06F 62
OO6F66
OO6FE6EA
OO6F72
OO6FTA
QO6F82
OOGFBA
O06F392
OO6F98
OO6FAG
OO6FAG6
OOGFAA
OO6FAE
O06FB2
OO6FB4
OO6FB8
7201
7402
61000168
203C00980101
01€80026
61000B3A
61000B2E
41EDO9D0
43F90000705E
7021
610QQ00EC
41 EDOAOGO
43F900007050
700D
610000DC
203C0000759C
2B400A12
2B400A16
2B7C000079C60A0E
2B7C000075580A2A
2B7C000075680A2E
L3FCOOO3FFFFFCO4
13FCOO9SFFFFFCO4
1B7C00070484
2B7C00006A4 60A22
2B400A1A
2B400A1E
2B400A26
7000
2B400A86
1B400A8A
moveq.i
#1,D1
moveq.1
#2,D2
bsr
$7080
move.1
#5980101,D0
movep.1
DO,$26(A0)
bsr
S7A70
bsr
S7A68
lea
$9D0(A5)
,A0
lea
$705E,Al1
moveq.1
#33,D0
bsr
$7036
lea
$A00(A5)
,A0
lea
$7050,A1
moveq.1
#13,D0
bsr
$7036
move.l1
#$759C,D0
move.1
DO0O,$A12(A5)
move.1
D0O,$A16(A5)
move.1
#579C6,SA0E(A5)
move.l
#$7558,$A2A(A5)
move.1
#$7568,S$A2E(AS)
move.b
#3,SFFFFFCO4
move.b
#$95,S$FFFFFC04
move.b
#7,$484(A5)
move.1
#56A46,$A22(A5)
move.1
#$7034,D0
move.l
DO,SA1A(A5)
move.l
D0O,S$A1E(A5)
move.1
DO0O,$A26(A5)
moveq.1
#0,D0
move.1
DQ,SA86(A5)
move.b
D0O,SA8A(A5)
/4
for
9600
Baud
9600
baud
Initialize timer
and interrupt
vector
$00,
$98,
$01,
$01
To
scr,
ucr,
rsr,
tsr
DTR
on
RTS
on
Pointer
to
iorec
for RS232
Start
data
for
tiorec
34
bytes
Copy
into RAM
Pointer
to iorec MIDI
Start
data
for jorec
14
bytes
Copy
into RAM
Keyboard and
MIDI
error vector
Pointer
to
error
routine keyboard
Pointer
to error routine MIDI
MIDI
interrupt vector
MIDI-ACIA master
reset
/16,
8
bit,
1
stop bit,
no parity
Key click,
repeat
und bell enable
clockvec
joyvec
&
statvec
Clear
sound variables
Sound pointer
Delay timer
Surysyqng 3S.
jeuiajuy TS wey

<!-- source-page: 354 -->
## Page 354

Lye
OO6FBC
OO6FCO
OO6FC4
OO6FC8
OO6FCE
OO6FD4
OO6FD8
OO6FDE
OO6FEO
OO6FE2
OO6FE6
OO6FEE
OOGFF6
OO6FFC
OO6FFE
007000
007002
007006
007008
00700C
007010
007014
007018
OO701A
OO701E
007022
007024
007028
0O702E
007030
007034
1B400A8B
2B400A80
6100FC6A
1B7COOOFOA7TE
1B7CO0020A7F
41ED09F2
43F900007042
700D
6154
61000COE
13FCOO03FFFFFCOO
13FCOO096FFFFFC0O
267000007080
7203
2401
2001
06000009
E582
24732000
61000138
SICQPFEC
45ED752A
7006
6100012A
45ED73C0
7002
61000120
247C0000703E
7603
6100FCBE
4E75
move.b
move.1
bsr
move.b
move .b
lea
lea
moveq.1
bsr
bsr
move.b
move.b
move .1
moveq.1
move .1
move.1
add.b
asl.1
move.1
bsr
dbra
lea
moveq.1
bsr
lea
moveq.1
bsr
move.1
moveq.1
bsr
rts
DO, SA8B(A5)
DO, $A80(A5)
$6C30
#$F, SATE (AS)
#2, SATF (AS)
$9F2 (A5) ,A0
$7042,Al
#13,D0
$7036
S7BF2
#3, SFFFFFCOO
#596, SFFFFFCOO
#$7080,A3
#3,D1
bD1,D2
D1,D0
#9,D0
#2,D2
0(A3,D2.w)
,A2
$7146
D1, S6FFE
$752A(A5)
,A2
#6,D0
$7146
$73C0 (AS)
, A2
#2,D0
$7146
#S703E,A2
#3,D3
S6CFO
Temp value
Printer
timeout
Strobe
to
high
Pointer
to iorec to keyboard
Start
data
for iorec
14 bytes
Copy
into RAM
Pointer
to
BIOS keyboard table
Reset
keyboard ACIA
/64,
8 bits,
1 top bit,
no arity
Pointer
to
MFP
Interrupt
vectors
Initialize
four vectors
Interrupt
number
Plus
offset
Get
vector
from table
initint,
install
interrupt
Next
vector
MIDI
and keyboard vector
Vector
number
6
initint,
install interrupt vector
CTS interrupt
routine
Vector
number
2
initint,
install interrupt
Pointer
to
init data
for
IKBD
4
bytes
Send string
to
IKBD
Surysyqng 3sa1;
sjeuiajuy TS Wey

<!-- source-page: 355 -->
## Page 355

Bre
007036
007038
00703C
10D9
SICBFFFC
4E75
move.b
dbra
rts
(Al)
+, (AO) +
DO, $7036
ee
ee
ee ee
ee
eee ee
ee ee
ee
ee ee ee
ee ed
007038
8001121A
dc.b
$80,$01,$12,S51A
ee eee
ee eee eee eee
ee eee
ee ee
ee
ee
el
007042
007046
007048
0O0704A
00704C
OO704E
ooo008Dpo
0080
0000
0000
0020
0060
de.l
dc.w
dc.w
dc.w
dc.w
dc.w
$8D0
128
0
0
32
96
OKI RI IOI
IO
I TI
IR
IORI
I
IO
KK
IO
te kk te
007050
007054
007056
007058
OO705A
QO705C
00000950
0080
0000
0000
0020
0060
de.l
dc.w
dc.w
dc.w
dc.w
dc.w
$950
128
0
0
32
96
eC TT CCT eC
eT CCC ee
Se CPPS EPCS
eC ee
ee Se ee
SS
kD
OO7TO5E
007062
007064
007066
007068
0O706A
00706C
007070
000006D0
0100
0000
0000
0040
00co
000007D0
0100
de.l
dc.w
dc.w
dc.w
dc.w
dc.w
de.
dc.w
$éDO
256
0)
10)
64
192
$7D0
256.
Block
move
Next
byte
Reset
keyboard,
disable
mouse
und
joystick
iorec
for keyboard
Keyboard buffer
Length
of
the
keyboard buffer
Head index
Tail
index
Low water
mark,
1/4
buffer
length
High
water
mark,
3/4 buffer
length
ierec
for MIDI
MIDI
buffer
Length
of
the
MIDI
buffer
Head index
Tail
index
Low water mark,
1/4
buffer
length
High water mark,
3/4 buffer length
iorec
for RS232
RS232
input buffer
Length
of
the
input buffer
Head index
Tail
index
Low water mark,
1/4
buffer length
High water mark,
3/4 buffer length
RS232
output
buffer
Length
of
the
output buffer
Surystiqnd ISA]
yeusajuy TS uey

<!-- source-page: 356 -->
## Page 356

6re
007072
007074
007C76E
007078
OOT07A
00707B
00707C
00707D
OO7TO7E
00707F
FOI
IO III I
III OI IOI OIG IOI
I IO IOI
III I I I I II
$7426
$7374
$7408
$72C0
007080
007084
007088
00708C
FOO IOI
IO
IO IO
OO
I
IO IOI
IO
III IIR ICI
aaa
movem.1 DO-D4/A0-A3,-(A7)
007090
007094
00709A
0070A0
OO70A6
0070A8
0070AE
0070B4
0070B6
0070BC
0070C2
0070C4
0070CA
0070D0
0000
0000
0040
00CcO
00
00
00
00
01
00
00007426
00007374
00007408
000072C0
48E7F8F0
207CFFFFFAO1
267000007124
247000007128
615A
267000007118
247000007128
614C
267C0000711C
247000007128
613E
267000007120
247000007128
6130
dc.
dc.
dc.
dec.
de.
de.
de.
dc.
dc.
dc.
voor
r oz
ef
£
=z
dc.l
de.l
de.l
dc.l1
move.
move.
move.
bsr
move.
move.
bsr
move.
move.
bsr
move,
move,
bsr
1
1
1
64
192
oroo
©
#SFFFFFAO1,A0
#$7124,A3
#$7128,A2
$7102
#$7118,A3
#$7128,A2
$7102
#$711C,A3
#$7128,A2
$7102
#$7120,A3
#$7128,A2
$7102
Head
index
Tail
index
Low water mark,
1/4 buffer length
High water mark,
3/4 buffer length
rsrbyte,
receiver
status
tsrbyte,
transmitter status
rxoff,
txoff
rsmode,
XON/XOFF mode
filler
Interrupt vectors
for
MFP
#9,
transmitter
error
#10,
transmitter interrupt
#11,
receiver error
#12,
receiver interrupt
setimer,
initialize timer
in
MFP
Save registers
Address
MFP
Burysyqnd 3S,
gjeusayuy TS ey

<!-- source-page: 357 -->
## Page 357

Atari ST Internal
First Publishing
ZU‘ZT ‘OT OT
q*op
D0D0WOWO OTTLOO
8/8/99
q*op
80809090 SIIL00
RE
OO
OR OE OR OE KORE OR OR
OR KOR
RE
sql
GL4b 9TTLOO
zv‘oqd
=
=A*ppe
OD'd PITLOO
ev’ead
Teaco
€p9z2 ZITLOO
€d’ow
T'ppe
889d OLTLO0
ea’ (ev)
q*eaouw
ET9T FOTLOO
ev‘od
«*ppe
099d DOTLOO
€d‘o# T*baacu
009L VOTLOO
sji
GLa’ 80TLO00
(ev) ‘eq
q*pue
ETLO 9OTLOO
€aq’(z¥)
 q*eaow
ZT9T
POTLOO
WOTLS
isq
90T9
ZOTLOO
sqi
SLAP OOTLOO
siaqstTbhar e10jsey
€V-OW/Pd-Od‘+
(Lv)
T° weaou
ATIOIGIb DAOLOO
(ev) ‘Ta
q*izo
€TE8 WAOLOO
TW7ew
fixe
6FLO BAOLOO
yojew TTIun
SAOLS
euq
9499 940100
ezeduos puy
za‘ (M*ea‘ov)o
8=6a‘duo
OOOECEPA ZA0L00
dau
ut eqep aqTim
(M°Ed‘OW) O47G
«=A eacw
OOOEZBIT AIOLOO
ed’ (M‘od‘Eew)o
q'aaow
OOOOEE9T WAOLOO
€d‘o# T*beacu
0094 8H0L00
ew‘ PELLS
Pat
DELLOOOOGALD
Z40L00
Tv ‘ew
xa
6PLO OFOLOO
ZOTLS
1sq
2219 FdOLOO
ZW‘OETLS#
T*eaow
O€TLOOOODLHZ
BAO0L00
EW‘OZTLS#
T° aaow
D~TLOOOODLIZ
ZAO0LOO
350

<!-- source-page: 358 -->
## Page 358

Atari ST Internals
first Publishing
Testo
oF} Aequnu
YTq SsyeTNoTeD
eiwt
sseippy
ddW ey sseippy
szaeqsTbeai
anaes
X@PUT PIOM HuoT
OF
7ABAUOD
zequnu
ydnitequt
429
sqdnizequt
daw eTqestp
‘quTsTp
siaysTbel a10jsey
sqdnazequt aTqeug
IOWOSA MBU
42S
soippe
10709,
$I0}098A
ddW 24}
JO aseq sntd
p10oM Huot
1OJF
xXepuTt
sv
requnu
10
eA
sqdniiequt eTqestd
siaysTbezl
anaes
JO}DSA YdnT9AUT
ddW
2eS
“qUTIATUT
piom Huot
‘4ST-9o
2equNN
qZoqoen
ydnizzs4uyT
zequnu
yAdnarzaquy
z0o4OeA YdnzzeAUT
dJW
yes
‘/juUTdzu
9DTLS
isq
Wb19 WLTLOO
TW‘ (OW) 8T
eat
ZTLOOBAE YLTLOO
Ow‘ TOWA TITIES
eal
TOWAdddI6dTP OLTLOO
OD0DLE8b D9TLOO
oa‘St#
T*pue
JO00000008Z0 99TLOO
oa‘ (L¥)p
M*eAoW
POOOAZOE
Z9TLOO
PRCT
TC COT CCC CCCP SCS
L CLE LL ELS SS Se ee
(L¥)-‘TW-OW/Td-0d T"weaow
sj2
GLAP O9TLOO
ZW-OW/ 70-00 ‘+ (LY)
T° weaow
LOLOAGDP OSTLOO
SUTLS
1sq
WbT9 YSTLOO
(lw) ‘@w
T° eaow
W827 BSTLOO
tlw'zq
T*eaouw
fbZe 9STLOO
za‘oots#
 T'PPe
00T00000Z890 OSTLOO
ca’z#
= MB“ TSB
ZSH APTLOO
za‘oqd
T*eaow
OO0PZ DPTLOO
29TL$
asq
OZ19 WPTLOO
(Lv) -‘cv-oW/Zd-0d T*weaow
OHOALASh 9PTLOO
PPP ePCCTECT CCC CCT OCT EL CSS
C LC LES SEES
2
eS ee
J000000008Z0 OFTLOO
zv‘(LW)9
«T° eAow
9000A9F2 DETLOO
og‘ (LW)p
M*aAcU
POOOAZOE BETLOO
POeT OCTETS TET TCT TET TTT TTT Te
LS
Se ee
oa‘ST#
T’pue
p7s ‘77s ‘07$ ‘ats
q°op
PCZZOTAT
VETLOO
B4$ ‘ABS 4070
q*op
84480000 OETLOO
DIS ‘OTS “WIS “BTS
q°op
DTIOTWI8T IZTLO0
dag ‘ads ‘aas “ddqs
q°op
ddddaddd 8ZTLO0
PIPTCTZT
beTLOO
OTOTHORO OCTLOO
oz‘02‘8l ‘8st
qg°op
OTOL‘ OL ‘PT
q’op
351

<!-- source-page: 359 -->
## Page 359

cSE
oo717C
OO7T1TE
007182
007184
007186
00718A
00718C
00718E
007192
007194
007196
00719A
0391
43E80006
6142
0331
43E8000A
613A
0391
43E8000E
6132
0391
4CDF0303
4E75
belr
D1, (Al)
lea
6(A0),Al
bsr
$71C6
belr
D1, (Al)
lea
10(A0),Al
bsr
$71C6
belir
D1, (Al)
lea
14 (A0),Al
bsr
$71C6
belr
D1, (Al)
movem.1
(A7)+,D0-D1/A0~Al
rts
aK
KR KKK KK RK KKK Rk
kk kk kak
kk KKK
00719C
OO71AG0
OO7T1A6
OO71AA
0071B0
0071B4
0071B6
0071B8
0071BC
0071BE
0071C0
NOATVICA
VVbAS
302F0004
02800000000F
48E7COCO
41 F9ORFFFFAOL
43E80006
6110
03D1
43E80012
6108
03D1
4CDF0303
ARTE
Siro
move.w
4{A7),D0
and.1l
#15,D0
movem.1 DO-D1/A0-Ai,~(A7)
lea
SFFFFFAO1,AQO
lea
6(A0}),Al
bsr
$71C6
bset
D1, (Al)
lea
18(A0),Al
bsr
$71C6
bset
D1, (Al)
movem.1
(A7)+,D0-D1/A0-Al1
rts
KKK
KR KEK KKK KEK KK KEK KARE KKK KKK KK KKK KKK KKK KK IK
0071C6
0071C8
0071CC
1200
0c000008
6D02
move.b
DO0,DI1
cmp.b
#8,D0
blt
$71D0
And clear
bit
Address
iera
Calculate bit
number
And clear bit
Address
ipra
Calculate bit
number
And clear bit
Address
isra
Calculate bit
number
And clear bit
Restore registers
jenabint,
enable
MFP
Vector
number
In
long word index
Restore registers
Address
MFP
Address
iera
Calculate bit
number
And set
bit
Address
imra
Calculate bit
number
And
set
bit
Restore registers
to
clear
to
clear
to
clear
interrupts
to
set
to
set
bselect,
calculate
bit
and register
number
Save interrupt
number
Greater
than
8
?
No
Burysyqnd ISA]
(eulouy TS Wey

<!-- source-page: 360 -->
## Page 360

ESE
OOTICE 5141
subq.w
#8,D1
0071D0 0c000008
emp.b
#8,D0
0071D4
€6C02
bge
$71D8
0071D6 5449
addq.w
#2,Al
0O071D8
4E75
rts
SOOO
IO
IGOR ITO
OI TOO III IOI
I
IIR IOI IOI IOI IK IK I Ik
QO7T1DA 41F9000009D0
lea
$9D0,A0
OO7LEO 43F9FFFFFAO1
lea
SPFFFFAO1,
Al
OO71E6
4E75
rts
BO
IO
IO
IO
IO
IO III
OR
I RII OI IOI TOI IO III OK
te teak
OO7T1E8 34280008
move.w
8(A0),D2
OOTIEC 36280006
move.w
6(A0),D3
QO71FO
B443
cmp.w
D3,D2
OO7T1F2
6204
bhi
$71F8
OO71F4 D4680004
add.w
4(A0),D2
OO7T1F8
9443
sub.w
D3,D2
OOT1FA
4E75
rts
YO
IO
IO IOI TO
IO
I IO III OI III IO
ITI TOR IK IO
IK I
0071FC 082800010020
btst
#1,32 (AQ)
007202
6704
beq
$7208
007204
61000862
bsr
S7A68
007208
4E75
rts
RO IO IO IOI
II
I IOI
IO
II IO
IO II IOI IO
II II IOI
IO
AI
ae
OO720A
40E7
move.w
SR,
~(A7)
00720C 007C0700
or.w
#$700,SR
607210
61C8
bsr
S7T1DA
007212 082800000020
bt st
#0,
32 (AQ)
ON7218
6706
beg
$7220
Else
subtract
offset
Greater
than
8
?
Yes
Pointer
from
a to
b register
rs232ptr
Pointer
to RS232
iorec
Pointer
to MFP
rs232ibuf
Tail
index
Head index
Head
>
tail
?
No
Add buffer
size
Tail
-
head
rtschk
RTS/CTS mode
?
No
rtson
rs232put,
RS232
output
Save
status
IPL
7,
disable interrupts
rs232ptr,
get buffer pointer
XON/XOFF
mode
?
No
BurysTqnd Iss,
sjeusazuy LS ueIy

<!-- source-page: 361 -->
## Page 361

ySe
00721A 4A28001F
tst.b
OO721E
6618
bne
007220 082390007002C
btst
007226
6710
beq
007228 34280014
move .W
00722C B4680016
cmp .W
007230
6606
bne
007232
1341002E
move .b
007236
601A
bra
007238 34280016
move .W
00723C
610002E0
bsr
007240 B4680014
cmp.w
007244
6716
beq
007246 2268000E
move .1
00724A 13812000
move .b
O0724E 31420016
move .w
007252
61A8
bsr
007254
46DF
move .W
007256 O23CO0FE
and.b
00725A 4E75
rts
00725C
619E
bsr
OO725E
46DF
move .w
007260 003c0001
or.b
007264
4E75
rts
Te OO
rk
a
KK
IK
KKK
KE KKK KKK KEK KK KK KKK
007266
40E7
move.w
007268
007C0700
or.w
00726C
6100FFEC
bsr
007270
32280006
move .wW
31 (AQ)
$7238
#7,44 (Al)
$7238
20(A0) ,D2
22 (AO) ,D2
$7238
D1,46(Al)
$7252
22 (AO) ,D2
$751E
20 (A0) ,D2
$725C
14 (A0),AL
D1,0{Al1,D2.w)
D2,22(A0)
$71FC
(A7)+,SR
#254,5R
ST1FC
{A7) +,S5R
#1,5R
SR,
-(A7)
#$700,SR
S71DA
6(A0),D1
XON
active
?
Yes
Is
MFP
still
sending
?
Yes
Head index
Tail
index
Still characters
in buffer?
Pass
byte
to
MFP
Tail
index
Test
for wrap around
Compare with
head index
Same,
buffer
full
Get
current buffer address
Write character
in buffer
Save
new tail
index
rtschk,
set
RTS
?
Restore
status
flag
Clear
carry
flag
rtschk,
set
RTS
?
Restore
status
Set
carry flag,
don't output
char
rs232get,
RS232
input
Save
status
IPL
7,
disable interrupts
rs232ptr,
get
RS232 pointer
Head index
Surysyqng ISI
peu] TS Very

<!-- source-page: 362 -->
## Page 362

cS¢
007274
007278
OOT27A
OOT27E
007282
007284
007288
00728C
00728E
007292
007294
007296
00729A
0072A0
OO072A2
OO72A6
0072A8
0072AC
0072B0
0072B2
0072B6
OO72BA
OO72BE
KK KKK KIKI KIT BIT KTR TK
I
OR ROR KI TOK
IOI TI
ROR IO
KK KK
movem.1 DO-D3/A0-A2,-(A7)
0072Cc0
0072C4
0072C8
OO72CE
0072D4
0072D8
B2680008
671A
61000296
22680000
7000
10311000
31410006
4é6DF
023CO0FE
6006
4é6DF
003C0001
082800000020
671C
4A28001E
6716
6100FF3E
B468000A
660C
123c0011
6100FF52
4228001E
4E75
48E7FOEO
6100FF14
1169002A001C
08280007001C
67000092
082800010020
cmp .Ww
beg
bsr
move.1
moveq.1
move .b
move .W
move .w
and.b
bra
move .W
or.b
btst
beq
tst.b
beq
bsr
cmp.w
bne
move .b
bsr
clr.b
rts
bsr
move .b
btst
beg
btst
8 (AO) ,D1
$7294
$7512
0(A0),Al
#0,D0
0(A1,D1.w)
,DO
D1,
6 (AQ)
(A7)+,5R
#254,5R
$7290
(A7)+,5R
#1,SR
#0,
32 (AO)
$72BE
30 (AQ)
$72BE
$71E8
10(A0) ,D2
$72BE
#$11,D1
$720A
30 (A0)
$71DA
42 (A1),28 (AO)
#7,28(A0)
$7368
#1,32 (AO)
Tail
index
No character
in buffer
?
Test
for
wrap
around
Get buffer
address
Get
character
from buffer
Set
new head index
Restore
status
Clear
carry
flag,
OK
Restore
status
Set
carry
flag,
no
character
there
XON/XOFF mode
?
No
XON active?
No
Get
input
biffer
length
used
Equal
low water mark
?
No
XON
Send
Clear
XON
flag
revint,
RS232
receiver interrupt routine
Save registers
rs232ptr,
get
RS232
pointer
Read receiver
status register
Interrupt through receiver buffer
full
?
No
RTS/CTS
mode
?
SULysqng ISI}
syewiaquy LS wey

<!-- source-page: 363 -->
## Page 363

9S¢e
0CO072DE
0072E0
OO072E4
OO72E8
OO72EE
0Q72F0
0072F6
OO72F8
0072FC
OO72FE
007304
007306
0O730A
00730C
007312
007314
007318
00731¢C
007320
007322
007326
OO732A
00732E
007332
007336
007338
00733E
007340
007346
007348
6704
61000782
1029002E
082800010020
6624
082800000020
671C
oco0gdl1
6608
11 7CQQ00001F
6062
0c000013
6608
117COOFFOOI1F
6054
32280008
610001F8
B2680006
6746
24680000
15801000
31410008
6100FEB8
B468000C
6624
082800010020
6628
082800000020
6714
4A28001E
beg
ber
move .b
btst
bne
btst
beq
emp .b
bne
move .b
bra
cmp.b
bne
move.b
bra
move .W
bsr
cmp.w
beq
move .1
move.b
move .W
bsr
cmp .w
bne
btst
bne
btst
beq
tst.b
$72E4
S7A64
46(Al1),DO
#1,32 (AO)
$7314
#0,
32 (AO)
$7314
#17,D0
$7306
#$0,
31 (A0)
$7368
#19,D0
$7314
#SFF,31(A0)
$7368
8(A0),D1
$7512
6(AQ),D1
$7368
0(AQ) ,A2
DO,0(A2,D1.w)
D1,8 (AO)
$71E8
12 (AQ) ,D2
$735C
#1,
32 (A0)
$7368
#0,
32 (AO)
$735C
30 (A0)
No
rtsoff
Read
data
from receiver
register
RTS/CTS mode
?
Yes
XON/XOFF mode
?
No
XON received
?
No
Clear
XOFF
flag
Character
not
in buffer
Receive
XOFF
?
No
Set
XOFF
flag
Character
not
in buffer
Tail
index
Test
for wrap around
Head equal
tail
?
Yes
Get
buffer
address
Received byte
in buffer
Save
new tail
index
Get
input buffer
length used
Equal
high water mark
?
No
RTS/CTS mode
?
Yes
XON/XOFF mode
?
No
XOFF
already
sent
?
Surysyqng ISI]
jeusoyy LS Wey

<!-- source-page: 364 -->
## Page 364

LS¢
00734C
00734E
007354
007358
00735C
007362
007364
007368
00736E
007372
660E
117COOFFOOLE
123C0013
6100FEBO
082800010020
6704
61000702
08A90004000E
4CDFO70F
4E73
bne
$735C
move.b
#SFF,30(A0)
move.b
#$13,D1
bsr
$720A
btst
#1,32 (AO)
beq
$7368
bsr
S7TA68
belr
#4,14 (Al)
movem.1
(A7)+,D0-D3/A0-A2
rte
FOO III
IO IOI
IOI
IG
kkk kkk kok kkk
kk kkk
007374
007378
00737C
007382
007384
00738A
00738C
007390
007392
007398
00733C
0073A0
0073A2
0073A6
OO73AA
0073B0
0073B4
0073BA
0073BE
48E720E0
6100FE60
082800010020
6630
082800000020
6706
4A28001F
6622
1169002C001D
34280014
B4680016
6712
6100017A
2468000E
13722000002E
31420014
O8A90002000E
4CDFO704
4E73
movem,1 D2/A0-A2,-(A7)
bsr
S71DA
btst
#1,
32 (AO)
bne
$73B4
btst
#0,
32 (AO)
beq
$7392
tst.b
31(A0)
bne
$73B4
move.b
44(A1),29(A0)
move.w
20(A0),D2
cmp.w
22 (AQ) ,D2
beq
$73B4
bsr
S751E
move.1
14(A0),A2
move.b
0O(A2,D2.w) ,46(Al1)
move.w
D2,20(A0)
belr
#2,14 (Al)
movem.1
(A7)+,D2/A0-A2
rte
Yes
Set
flag
for
XOFF
XOFF
Send
RTS/CTS
mode
?
No
rtson
Clear
interrupt
service
bit
Restore registers
txrint,
tramsmitter buffer
empty
Save registers
?
rs232ptr,
get
RS232 pointer
RTS/CTS mode
?
Yes,
then
use this interrupt
XON/XOFF mode
?
No
XOFF active
?
Yes
Save transmitter
status
register
Head index
Compare with tail
index
Send buffer empty
Test
for wrap arround
Pointer
to
send buffer
Pass
byte
to MFP
for sending
Save new head index
Clear
interrupt service bit
Restore registers
Surysyqngd Say
sjeussjuy LS wey

<!-- source-page: 365 -->
## Page 365

8S¢
wa KK KAKA KKK KR KKK KK RK KR
KKK Kak
a
KKK
KK
Rk kkk
0073C0
0073C4
0073C8
0O073CE
0073D0
0073D6
0073DC
0073DE
0073E2
0073E6
0073E8
0Q73EC
0073F0
0073F6
OO73FA
007400
007404
007406
48E720E0
6100FE14
082800010020
672A
1169002C001D
08280007001D
67F8
34280014
B4680016
671E
61000134
2468000E
13722000002E
31420014
08A900020010
4CDFO704
4E73
60F2
movem.1
bsr
btst
beq
move .b
btst
beq
move .W
cmp.w
beq
bsr
move .1
move .b
move .wW
belr
movem, 1
rte
bra
D2/A0-A2, -(A7)
$71DA
#1,
32 (AO)
$73FA
44(A1) ,29(A0)
#7,29 (AO)
$73D6
20(A0) ,D2
22 (AO) ,D2
$7406
$751E
14 (AQ) ,A2
0(A2,D2.w) ,46(A1)
D2,20(A0)
#2,16(A1)
(A7) +,D2/A0-A2
$73FA
KK KK
KK IK KKK I KKK KK KKK KK KAKI KKK KKK KKK AK KHAKI KKK KEKE KKEEKE
007408
00740C
007410
007416
OO741A
007420
007424
48E780C0
6100FDCC
1169002A001C
1029002E
08A90003000E
4CDF0301
4E73
movem.1
bsr
move .b
move .b
belr
DO/AO-Al,~(A7)
S71DA
42 (Al)
,28 (AO)
46(A1),D0
#3,14 (Al)
movem.1
(A7)+,D0O/A0-Al
rte
Ken
KK KK KK KKK KKK IK KKK KKK KEK KKK KKK KEKKKKKKKKKKKK AKA KKKEK
movem.1 AQ-Al,-(A7)
007426 48E700C0
ctsint,
CTS
interrupt
routine
Save registers
rs232ptr,
get
RS232 pointer
RTS/CTS mode
?
No,
then
ignore
interrupt
Save transmitter
status
Transmitter buffer
empty
?
No,
wait
(must
jump
to
$73D0!)
Head index
Compare with tail index
Transmit buffer empty
Test
for wrap arround
Pointer
to transmit buffer
Pass byte
to MFP
for sending
Save new head index
Clear interrupt
service bit
Restore registers
Transmit buffer empty
rxerror,
receive error
Save registers
rs232ptr,
get RS232 pointer
Save
receiver
status
Read data register
(clears
status)
Clear interrupt
service bit
Restore registers
txerror,
transmit error
Save
registers
SuTYystqng ISILT
[eut9}Uy LS Heyy

<!-- source-page: 366 -->
## Page 366

Atari ST Internals
rst Publishing
o—
apouszl
.esey
jes
4,u0p uayq
‘ant eben
apon
ZaqyjTusueIy eTqestd
T@aTeoel
aTqestad
Zos
‘43sq
‘asa
‘19n
eaes
tequtod zezsu
706
‘1zy4dzezsa
sqdnizjaqut aTqestp
an TdI
ZEZSU
sanbtjuoo
‘juoosz
IGIW
dgur
cECSH
aTqey o810T
snjzeqjs
ar0j4say
2eA10T
03 AajuTod
499
prom Huot
10jy
p
south
atTqey ey
Jo
sseippe
eseg
sqdnizeyut
aTqestp
“ft
TdI
snyejs
eaes
qaqunu eoTaep
3e5
aTqez
of zequtod
yeb
‘sa10T
slaystTbar
aiojsey
ATqQ soTATes
Jdnizsequy
7e8eTD
snqjeqs Jaqqtwsuerq aaes
azaqutod zezsu
386
‘zadzezsa
(ow) Ze’(LW)L
q*eacw
0Z00L00049TT
b8hL00
agp.
yuq
VOd9
Z8PLOO
(LW)9
4° 489
S000d9VF ALPLOO
(tw) bb/od
q*saou
DZOOOPET WLPLOO
(TW) Zb‘od
q*eaou
WZOOOPEL 9LPLOO
oa‘o# T*baaou
OO0L
PLELOO
La‘{tw)sz$ T*deaou
8Z006P40 OLPLOO
WaTtus
48q
D9dA00T9 29hL00
us ‘OOLS#
M* IO
OOLODLOO 89FL00
PoC
ECE CEPTS
ET ET SST ST STE SECC SSL TE
LP SST SSS SS
OOWOO0CO
F9FL00
ed6$
T°9P
24600000 09FL00
oa6s
T*9p
04600000 DSPLO0
PoCETe Ce PeP TEC EC EP eS TET TTS
S SSL PS PLS Lee SSS SSS EEE
oovs
T°9pP
sql
SLAP WSPLOO
us‘+(Lv)
A‘ eAoU
dd9b 8SPL00
od‘(T'Ta‘zv)o
T° saow
OOBTZEO?
PSPLOO
Ta‘c#
T'Tse
T8Sa
72S¥L00
eW‘OSPLS
Pol
DSPLOOOOG
ASH DHFLOO
us ‘O0LS#
M* 10
OOLODLOO BHFLOO
(tLW)-
‘YS
M*eaow
LA0b 9PPLOO
Ta’(iW)b
M*SAcW
pOOOdZZE
ZPPLOO
Ta‘o# T*beaow
OOZL OFPLOO
RR
ROR OE OR
EO
ORR
OL OR ROR OE OR OLE KR LORE ROE ORR
OE OF
oya
€Lad AEVLOO
TW-OW/+ (LY)
T° weaow
OOECORGDb VERLOO
(TW) PU‘ TH
ITq
AOOOTOOOEYBO
PEPLOO
(ow)6z‘ (Tv) bb
gq°saow
GTOODZOO69TT
AZ¥LOO
WOTLS
Asq
AVGA00TS WepLoo
359

<!-- source-page: 367 -->
## Page 367

09¢
00748A
7000
moveq.1
#0,D0
00748C
7400
moveg.1
#0,D2
CO748E
4A6F0004
tst.w
4(A7)
Baud
rate
007492
6B20
bmi
$74B4
Negativce,
then don't
change
007494
322F0004
move.w
4(A7),D1
Get
baud rate number
007498
45F9000074F2
lea
$74F2,A2
Table
for
baud rate control
00749E
10321000
move.b
0O(A2,D1.w),DO
Get
value
from table
0074A2
45F900007502
lea
$7502,A2
Table
for baud rate
data
OO74A8
14321000
move.b
O({(A2,Dl.w),D2
Get value
from table
O074AC 2200
move.l
DO,Di
OO7T4AE
7003
moveq.1
#3,D0
Pointer
to timer
D
0074BO
6100FBDE
bsr
$7090
Set
timer
D
for
new baud
rate
0074B4
4A6F0008
tst.w
8(A7)
Set
ucr
?
0074B8
6B06
bmi
$74CO
No
0O074BA 136F00090028
move.b
9(A7),40(Al1)
Set
ucr
0074CO 4A6FO00A
tst.w
10 (A7)
Set
rsr
?
0074C4
6BO06
bmi
$74CC
No
0074C6 136F000B002A
move.b
11(A7),42(Al)
Set
rsr
0074CC 4A6F000C
tst.w
12 (A7)
Set
tsr
?
0074D0
6B06
bmi
$74D8
No
0074D2
136F000D002C
move.b
13(A7),44(Al1)
Set
tsr
0074D8
4A6FOO0E
tst.w
14 (A7)
Set
scr
?
O074DC
6BO06
bmi
$74E4
No
OO74DE 136F000F0026
move.b
15(A7),38(A1)
Set
scr
0074E4
7001
moveq.1
#1,D0
OO74E6
1340002A
move.b
DO, 42(A1)
Enable
receiver
QO74FA 1340002C
move.b
D0, 44(A1)
Enable transmitter
OO74EE 2007
move.l
D7,D0
Old value
of
the control register
OO074FO
4E75
rts
AO
RR
IO OOK kok kk kkk ko kkk kok k kk kk kkk ak kkk ee
Timer
values
fox
RS-232
baud
rates
0074F2 0101010101010101
dc.b
1,1,1,1,1,1,1
High byte
Surysyqnd ISI]
[eurajuy TS ueyy

<!-- source-page: 368 -->
## Page 368

19¢
OO74FA 0101010101010202
007502 01020405080A0B10
00750B 204060808FAF4060
dc.b
1,1,1,1,1,2,2
dc.b
1,2,4,5,8,10,11,16
Low byte
dc.b
32,64, 96,128,143,175,
64, 96
FRO IOI
OI
I IOI
IO IOI IO
OR IIA OI
IOI I III TOI I IOI HI
007512
5241
007514 B2680004
007518
6502
00751A 7200
00751C
4E75
addq.w
#1,D1
cmp.wW
4(A0),D1
bes
$751C
movegq.1
#0,D1
rts
errr
rr rTrrrrrrrrre cet rere Pere Le Se LSE PEL
The Seed
OO751E
5242
007520 B4680012
007524
6502
007526 7400
007528
4E75
addq.w
#1,D2
cmp.w
18 (AO) ,D2
bes
$7528
moveq.1
#0,D2
. rts
RO
OR III
III
II
IO
IOI IO IOI
IO
TO II II I IO III IK I I IC III
00752A 48E7FFFE
00752E 4BF900000000
007534 246D0A2A
007538
4E92
00753A 246D0A2E
00753E
4E92
007540 08390004FFFFFA01
007548
67EA
00754A O8B90006FFFFFAI1
007552
4CDF7FFF
007556
4E73
movem.1 DO-D7/A0-A6,-(A7)
lea
$0,A5
move.1
SA2A(A5),A2
jsr
(A2)
move.l1
$A2E(A5),A2
jsr
(A2)
btst
#4, SFFFFPAO1]
beg
$7534
belr
#6, SFFFFFAL1
movem.1
(A7)+,D0-D7/A0-A6
rte
wrapin,
test
for wrap arround
Head index
+
1
Equal
to buffer
size
?
No
Else
start with
zero again
wrapout,
test
for
wrap arround
Tail
index
+
1
Equals buffer
size
?
No
Else
start with
zero again
midikey,
keyboard
+ MIDI interrupt
Save registers
Clear
A5
mbufrec,
$7558
Interrupt
from MIDI-ACIA
?
kbufrec,
$7568
Interrupt vfromon Keyboard~-ACIA
?
Still
interrupt
?
Yes
Clear
interrupt
service
bit
Restore
registers
Surysyqng SI
syeulajuy TS Wey

<!-- source-page: 369 -->
## Page 369

COE
Bek KK
III IO
I
Ok I
kkk ek
I
kk det
i
ak
ae
007558
41EDOA00
00755C
43F9FFFFFCO4
007562
246D0A16
007566
600E
lea
SA00 (A5) ,A0
lea
SFFFFFCO4,A1
move.1
$A16{A5),A2
bra
$7576
KK
KK IR
KK RK
KR RK RRR KK KE KK KK RK KK KR KKK
007568
41EDO9F2
00756C 43F9FFFFFCOO
007572
246D0A12
007576 14290000
O0757A 08020007
OOT57E
671C
007580
08020000
007584
670A
007586 48E720E0
OO758A
6112
00758C 4CDF0704
007590
02020020
007594
6706
007596 10290002
O00759A 4ED2
00759C 4E75
lea
S9F2 (A5)
, AO
lea
SFFFFFCO0,A1l
move.l
$A12(A5),A2
move.b
O(Al1),D2
btst
#7,D2
beg
$759C
btst
#0,D2
beq
$7590
movem.1 D2/A0-A2,-(A7)
bsr
$759E
movem.1l
(A7)+,D2/A0-A2
and.b
#$20,D2
beq
$759C
move.b
2(A1),D0
jmp
{A2)
rts
ka kkk kik kkk kkkk kk kk kkk kkk kkk kkk kkk kkk kkk kkk kk kkk
OO7S9E 10290002
OO75A2 BLFCO00009F2
OOT5A8
66000416
OO75AC 4A2D0A32
OO75BO
6654
O075B2
O0COO000F6
OO75BE
650000F4
move.b
2(A1),D6
emp.1
#$9F2,A0
bne
$79C0
tst.b
$A32 (A5)
bne
$7606
cmp.b
#SF6,D0
bes
$76AC
MIDI
interrupt
jerec
for
MIDI
Address
of
the
MIDI
ACIA
$759C,
MIDI
error
routine
Keyboard interrupt
jorec
for keyboard
Address
of
the keyboard-ACIA
$759C,
Keyboard error routine
Get
ACIA
status
Interrupt
request
?
No
Receiver buffer
full
?
No
Save registers
arcvint,
get
byte
Restore registers
Mark
bit tested
No error
Read data clear status
Execute error routine
arevint,
get byte
from ACIA
Get
data
from ACIA
Keyboard ACIA
?
No,
MIDI
Keyboard
state
Keypress
?
Yes
Surysyqng ISI
sjeaig}0y TS ue

<!-- source-page: 370 -->
## Page 370

COE
OO75BA O40000F6
sub.b
#SF6,D0
OOTSBE O280000000FF
anda.1
#SFF,DO
0075C4
47F9000075F2
lea
$75F2,A3
OO75CA 1B7300000A32
move.b
0(A3,D0.w) ,$A32(A5)
0O075DO 47F9000075FC
lea
$75FC,A3
0075D6 1B7300000A33
move.b
0(A3,D0.w),$A33(A5)
OO75DC 064000F6
add.w
#SF6,D0
OO075EO
OCOQO0OF8
cmp.b
#SF8,D0
OO75E4
6DOA
blt
$75F0
OOT5E6 OCOOOOFB
cmp.b
#SFB,DO
OO75EA
6E04
bgt
$75F0
OO75EC 1B400A40
move.b
DO,$A40(A5)
OO75FO
4E75
rts
RO IO
ROR KOK
OOK RR
III
I
aK
aK
KK kK KK
0075F2 01020303030304050607
OO7T5FC 07050202020206020101
ROK IK ITF
RIK IO I
IOI
I IO
RR IO
IO
IOI
IK a
IO
ok
ok
007606 OC2D00060A32
cmp.b
#6, $A32 (A5)
00760C 64000084
bec
$7692
007610 45F900007656
lea
$7656,
A2
007616
7400
moveq.1
#0,D2
007618 142D0A32
move.b
$A32(A5),D2
00761C 5302
subq.b
#1,D2
00761E E342
asl.w
#1,D2
007620 D42D0A32
add.b
$A32 (A5)
, D2
007624
5302
subq.b
#1,D2
007626 E542
asl.w
#2,D2
007628 20722000
move.1
0O(A2,D2.w),A0
00762C 22722004
move.1
4(A2,D2.w),Al
007630 24722008
move.1
8(A2,D2.w),A2
Subtract
offset
Pointer
to
IKBD
code table
Save
IKBD merken
Pointer
to
IKBD lengths table
IKBD index
Add offset
again
Mouse position record
?
No
Mouse position record
?
No
Save mouse position
IKBD parameter
Status
codes
Lengths
Joystick record
?
Yes
Pointer
to
IKBD parameter
table
Kstate
1-5=>0-
4
Times
2
+1
1-5=>0-4
Times
4
IKBD record pointer
IKBD
index base
IKBD interrupt routine
Surysyqnd S1q
speusayuy TS Wey

<!-- source-page: 371 -->
## Page 371

Atari ST Internals
First Publishing
OGNI
203
STQey
rejQowePreE,
aqeqs
dadMI
2"8TD
Zayutod yorqs
4oae1I0D
aUT
NOI
AdnzzsequT
ay4Noexg
JeqyuTod pzose1a
sseg
XOPUT
4SeL
[ snuyw xeput day
aseq snuTW
XOPUT GENI
229
Ao YoOeA YdnzsquT
485
er
TET
Se STE TTT ETT CCT TCLS TE TEL LL
ee ees SS
eS See ee
9eVs
aps
66S
72S
ocounw
OVS
evs
atws
CpWS
ONS
ays
OWS
aevs
VIVs
aevs
pews
.
QO
daa dd
v0 000000080
000290
io Tic © TEC
@ HA © HM © HIM © HM © HC © HEE
© 2
© HIM
© HM © HEM © EL © HEE ©]
Coon
en OO oe Be
oe
oe
ot
92700000
aPvooo00d
6bYO0000
@e¥00000
6pvo0000
epvooooo
dTWO0000
EpYOOO00
Qpwoo00d
aTwo0000
OvwvOO000
aevoo000
vIVO0000
@evoo00d
bEWOOO0O
489200
W89200
989200
789400
ALILOO
WL9L00
9L9L00
7L9L00
A99L00
V99L00
999400
2992400
4AS9L00
¥S9L00
9S9L00
OE OR
OE OE
OR OE
KOR
ROR RO
OE
EE EK
(Sw) ZEWS
LW ‘oF
(ZW)
(LV)
- ‘OW
SOLS
(Sw) C£WS
(SW) EES ‘TH
(TW) ‘od
tw‘7q
za‘ (SW) EEWS
za‘0#
ew‘ (ZW)
sqz
q' ato
M*bppe
asf
T° aaou
auq
q°4sd
q‘ bans
q*aacu
T°qns
q°aacu
T’ boaow
T° eaow
GLav
TEVOUCED
Ab8s
cédp
B0AC
Vo99
cewodevyp
ecvodces
Osct
ZIEG
ecvodcrt
OObL
CSU
bS9L00
0S9L00
aAp9L00
279L00
Wb9LOO
8h9L00
bp9LOO
Ob9L00
aE€3L00
2€9L00
8E9L00
9€9L00
bEgLOO
364

<!-- source-page: 372 -->
## Page 372

Atari ST Internals
First Publishing
é paseater Asx TuLd
Aex TAL TOF
AFA 3S
ON
é
pesseid
Avy THLO
Aeyx
asytys
3ybTr
AOF
ATA APAaTD
ON
é
peseejtez
Avy
astys
aybTY
Aey ayyus
ayb6Taz 10x
ATW 39S
ON
&
passeid
Aay
aytus
3uoTY
Aex
AFJTUS
JJST
AOZ TQ TeSTO
ON
é peseater
Asay
ayyus
AjeT
Key JTYUS
YeT
2OF
ATA
39S
ON
é
passeid Aay
3AZTYs
AEST
snqejs
4yyTYys peoT
sepoo pivoqksy
paeaTscel
sses0idg
eqep
yOTAsAOol
Jo
sserppy
euT ano’
ydnaxzeyut
yoT ysAor
oa ’d6$s#
OELLS
Ta‘z#
Da9L$
oa‘als#
OELLS
Ta‘o#
Oa9LS
oa‘9as#
OELLS
1d ‘oF
PagLs
OG ‘9ES#
OELLS
ta‘t#
BD9L$
od ‘wws#
O€LL$
Ta‘t#
Da9L$
Od ‘W7Zs#
Ta’ (sv) asv$
q°dwo
Pig
qesq
auq
q* duo
PIq
aApToq
auq
q° duo
eq
Jesq
auq
q’ duo
Pig
AToq
auq
q* duo
eiq
yesgq
auq
q:duo
q* aaow
a6000050
'b09
Z000TI80
9099
ato000000
0509
Q000T880
9099
94000090
3509
0000TD80
9099
9€000000
8909
TOOOT880
9099
wWv000090
PLO9
TOOOTIB0O
9099
W2000050
acwodzé2ét
949 L00
Wad9L00
949100
bd9L00
049400
4a9 200
Wa9400
809200
pd9L00
cqgLoo
499 L00
999400
899400
9D9L00
299100
099400
989200
Wd9L00
989200
bd9L00
0€9L00
OW9 1.00
ROR OR
OR
RO ROR
ORE
KOR ROE ERR OER
ORE ORK OR ERE
WbOLs
ow’ (Gv)
6 bws
ew’ (SY) 97ZWS
(ZW) ‘oa
ew‘td
Ta‘9#
ta‘ (cw) ZEws
Ta‘Wews#
eig
eaT
T° saow
q°’ aaow
T° eaou
q:baqns
q*ppe
T*’ aaow
41609
6PWOddTh
9¢WOd9I
Fe
O8bT
Teh?
Tods
zewodced
WPVOOQQ0DE
CZ
¥W9LOO0
9V¥9L00
fV9L00
OV9LO00
d69L00
3692100
869200
769100
365

<!-- source-page: 373 -->
## Page 373

99¢
OO7T6FO
0076F2
OO76F6
OO76F8
OO7T6FC
OO76FE
007702
007704
007708
0O770A
OOTTOE
007710
007714
007716
00771C
OO771E
007726
00772C
007730
007734
007736
00773A
00773C
007740
007742
007746
OO7T74E
007756
007758
OOTTISE
6606
08810002
6038
0c000038
6606
08C10003
602C
OCO000B8
6606
08810003
6020
0CcO00003A
6620
082D00000484
670E
2B7C00007D780A86
1B7COOQ000A8A
08410004
1B410A5D
4E75
08000007
662A
4A2D0A7B
6616
1B400A7B
1B7900000A7E0A7C
1B790Q000A7FOA7D
603A
1B7COOOQ00A7TC
LB7COOQOQOQO0ATD
bne
belr
bra
emp.b
bne
bset
bra
cmp.b
bne
belr
bra
cmp.b
bne
btst
beq
move.
move.
behg
move.
rts
btst
bne
tst.b
bne
move.
move.
move.
bra
move.
move.
$76F8
#2,D1
$7730
#$38,D0
$7704
#3,D1
$7730
#$B8,D0
$7710.
#3,D1
$7730
#$3A,D0
$7736
#0, $484 (A5)
$772C
#$7D78,
SA86 (A5)
#$0, SA8A (A5)
#4,D1
D1, $A5D(A5)
#7,D0
$7766
$A7B(AS)
$7758
DO, SA7B(A5)
SATE, SA7TC (A5)
SATF, $A7D (A5)
$7792
#$0, $A7C (A5)
$$0,$A7D (AS)
No
Clear
bit
for CTRL key
ALT
key pressed
?
No
Set
bit
for
ALT key
ALT
key
released
?
No
Clear bit
for ALT key
CAPS
LOCK key pressed
?
No
Get console configuration
No
key click
Addrss
of
the
key
click
sound table
Start
sound
Invert
CAPS
LOCK
status
Save new shift
status
Was
key released
?
Yes
Repeat
.?
Yes
Save
key code
for
repeat
Delay
1
Delay
2
Clear
delay counter
Clear
delay counter
Burysyqnd ISILy
s[eusajuy ES Wey

<!-- source-page: 374 -->
## Page 374

L9¢
007764
007766
OO77T6A
00776C
007 76E
007772
007776
OOTTTA
OOTTIE
007780
007784
007788
00778E
007792
007798
OO7T79A
OO7T7A2
OO7T7TA8
OO77AA
OOTTAC
OO77AE
0077B2
0077B6
0077BC
007 7BE
0077C2
0077C8
OO77TCA
0077D0
602C
4A2D0A7B
670E
7200
1B410A7B
1B410A7C
1B410A7D
ocoo00c?
6708
ocodeoD2
66000238
082D00030A5D
6700022E
082D00000484
670E
2B7CO0007D780A86
1B7COO000A8A
2F08
7200
1200
206D0A5E
0240007F
082D00040A5D
6704
206D0AG6
O82D00000A5D
6608
O82D00010A5D
671A
bra
tst.b
beq
moveq.1
move .b
move.b
move .b
cmp.b
beg
cmp.b
bne
btst
beq
btst
beq
move.1
move .b
move.l
moveq.1
move .b
move.1
and.w
btst
beq
move.1
btst
bne
btst
beq
$7792
SA7B(A5)
STTTA
#0,D1
D1,$A7B(A5)
D1,$A7C(A5)
D1,$A7D(A5)
#$C7,D0
$7788
#$D2,D0
$79BE
#3,$A5D(A5)
S79BE
#0,$484 (A5)
$7738
#$7D78,S5A86
(A5)
#50, SA8A (A5)
AQ, -(A7)
#0,D1
po, D1
SA5E (A5)
, A0
#$7F,D0
#4, SA5D (AS)
$77C2
$A66 (A5)
, AO
#0, $A5D(A5)
$77D2
#1,$A5D(A5)
STTEC
HOME
key released
?
Yes
INSERT
key released
?
No
ALTkey still pressed
?
No
Console
status
No
key
click
Address
of
the
sound table
for
key
click
Start
sound
Save iorec
for keybaord
Scan
code
to
Dil
Address
of
the standard keyboard table
CAPS
LOCK active
?
No
Address
of
the CAPS
LOCK keyboard table
Right
shift
key pressed
?
Yes
Left
shift
key pressed
?
No
Surysyqng 3S1Ly
speusayuy LS Wery

<!-- source-page: 375 -->
## Page 375

g9¢
0077D2
0077D6
007708
0O77DC
OOTTIDE
0O7T7E2
OO7TTEA
0077E8
0077EC
0O77F0O
OO77F6
OOTTES
OOTTFC
OO77FE
007800
007802
007806
007808
00780C
007810
007814
007816
007818
OO781A
00781E
007822
007824
007826
007828
00782C
007830
007832
0C00003B
6510
oco00044
620A
06410019
7000
600001B2
206D0A62
10300000
082D00020A5D
6760
0c00000D
6604
700A
672A
0c010047
6608
06410030
6000018A
0C01004B
6608
7273
7000
6000017C
0C01004D
6608
7274
7000
6000016E
0c000032
6606
7000
cmp.b
bcs
emp.b
bhi
add.w
moveq.i
bra
move.1
move.b
btst
beq
cmp.b
bne
moveq.1
beq
cmp.b
bne
add.w
bra
cmp.b
bne
moveq.1
moveq.1
bra
emp.b
bne
moveg.1
moveq.1
bra
cmp.b
bne
moveq.1
#59,D0
ST7E8
#68,D0
S$TTE8
#25,D1
#0,D0
$7998
$A62 (A5)
, AO
0(A0,DO.w)
, DO
#2,5A5D(A5)
$7858
#13,D0
$7802
#10,D0
$782C
#$47,D1
$7810
#$30,D1
$7998
#$45,D1
$781E
#$73,D1
#0,D0
$7998
#$4D,D1
$782C
$$74,D1
#0,D0
$7998
#$32,D0
$7838
#0,D0
Function
key
?
No
Function
key
?
No
Add offset
to
GSX standard
Address
of the
shift keyboard table
Get ASCII
code
from
the
table
CTRL
key pressed
?
No
Carriage return
No
Convert
to linefeed
CTRL
HOME
?
No
Add $30
to GSX standard
CTRL
cursor
left
?
Convert
to
GSX standard
CTRL cursor
right
?
Convert
to
GSX standard
Surysyqng ISILy
s[eusayuy JS Wey

<!-- source-page: 376 -->
## Page 376

Atari ST Internals
First Publishing
oda
ON
Epasseid
Aayx
4JTYys
AYHTT
TO/pue
IST
snzeqs
3ITYUS
oda
ON
&é
+Qe
Na
ON
épasseid Aey
asyus
yybTA
roO/pue Aey
snqeqs
33TuUS
101
ON
é
aQ
ON
é passeid
Aay
LIV
oa’ascs#
oases
Td’S7s#
866L$
Od‘aLs#
866L$
za‘e#
za’ (cw) asws
oa‘ass#
q68L$
Ta’L7st
866L$
oa‘ocs#
866L$
cd ‘CF
za‘ (Sv) aSv$
0d‘0ORS#
O88L$
Ta’Wts#
8661S
(Sv) ASUS ‘EF
B866L$
Od‘ aATS#
866L$
oa‘ ats#
OSB8Ls
oa‘azs#
866L$
od‘ats#
pPaLs
oa‘9E$#
B66L$
q*eaow
auq
q*duo
Pig
q*eaow
baq
q°*pue
q*aaow
q*eaaow
auq
q* duo
eIq
q*aaow
baq
Q*pue
q*aaow
q*aaow
auq
q‘duo
baq
4s 3q
Rig
M*pue
eig
T‘ baaou
auq
q* dws
Rig
T° baaow
auq
q‘ dus
eiq
dsoode0T
8T99
8Z00TO0D0
24000009
ALOODENT
POTOOOLS
€0002020
acwodzbt
aASO0DE0T
8199
LZ00T090
VTTO0009
ISGOODENT
c2TOOOLY
€0002020
ascvodzbr
OBOODSEDT
8199
WTOOTOD0
8ETOOOLS
aswoeoo0dzso0
cbT00009
AITO00vZ0
VbTOO009
ATOL
9099
az000090
9ST00009
aTOL
9099
9€000050
c9T00009
PY¥8L00
eW8L00
468L00
VW68L00
968200
768L00
488200
W88L00
988400
b88L00
088200
9L8L00
818400
yL8L00
OL8L00
998400
898200
998L00
c98L00
4IS8L00
858200
pSBL00
0S8L00
308L00
VP8Lo0
8b8L00
bvBLOO
OVSLOO
de€8L00
9€8L00
BE8L00
VEBLOO
369

<!-- source-page: 377 -->
## Page 377

OLE
0078A8
0078AC
0078B0
0078B4
0078B8
0078BC
0078C0
0078C2
0078C6
0078CB
0078CC
0078D2
0078D4
0078D8
0078DC
0078E0
0078E4
0078E6
0078EA
0O078EE
0078F2
0078F6
OO78FA
0078FE
007902
007906
007908
00790C
007910
007914
007918
142D0A5D
02020003
670000E6
103C007D
600000DE
0C010062
660A
526D04EE
205F
600000F4
45F900007A2C
7403
B2322000
6700010E
51CAFFF6
0C010048
661C
123C0000
143CFFF8
102D0A5D
02000003
6700010E
143CFFFF
60000106
0C01004B
661C
143C0000
123CFFF8
102D0A5D
02000003
670000EC
SASD (A5)
, D2
#3,D2
$7998
#$7D, D0
$7998
#$62,D1
$78CC
#1,$4EE(A5)
(A7) +,A0
S79BE
STA2C,
A2
#3,D2
0(A2,D2.w),D1
$79E8
D2,$78D4
#$48,D1
$7902
#0,D1
#-8,D2
SA5D (A5) ,DO
#3,D0
$7A06
#-1,D2
$7A06
#$4B,D1
$7924
#0,D2
#-8,D1
SA5D(A5) ,DO
#3,D0
$7A06
Shift
status
Left
and/or
right
shift
key pressed?
No
‘})
ATL HELP
?
No
Set
dumpfig
for hardcopy
Restore
keyboard
iorec
Done
Pointer
to mouse scancode table
Test
4
values
Value
found
?
Yes
Next
value
Cursor
up
?
No
X offset
for cursor
up
Y offset
for cursor
up
Get
shift
status
Left
and/or
right
shift
key pressed?
No
Only
one pixel
up with shift
Y
offset
for
cursor
left
X offset
for
cursor
left
Get
shift
status
Left
and/or
right
shift
key pressed?
No
Surysyqng ISI]
speuiguy TS Wey

<!-- source-page: 378 -->
## Page 378

ILe
00791C
007920
007924
007928
00792A
00792E
007932
007936
00793A
00793E
007942
007946
O0794A
00794C
007950
007954
007958
00795C
007960
007964
007968
00796C
00796E
007972
007974
007978
OO797A
OO797E
007980
007984
007986
007988
L23CFFFF
600000E4
0c01004D
661C
123C0008
14300000
102D0A5D
02000003
670000CA
123c0001
600000C2
0€010050
661C
123c0000
143C0008
102DO0A5D
02000003
670000A8
143c0001
600000A0
0c010002
650C
0c01000D
6206
06010076
600C
0c000041
650A
OCOO00SA
6204
7000
600E
move.b
bra
ecmp.b
bne
move .b
move.b
move.b
and.b
beq
move.b
bra
emp.b
bne
move.b
move.b
move .b
and.b
beq
move .b
bra
cmp.b
bcs
cmp.b
bhi
add.b
bra
cmp.b
bes
emp.b
bhi
moveq.1
bra
#$-1,D1
$7A06
#$4D,D1
$7946
#8,D1
#0,D2
SA5D (A5)
, DO
#3,D0
$7A06
#1,D1
$7A06
#$50,D1
$7968
#0,D1
#8,D2
$A5D (A5)
, DO
#3,D0
$7A06
#1,D2
$7A06
#2,D1
ST97A
#$D,D1
ST97A
#$76,D1
$7986
#$41,D0
$798A
#$5A, D0
$798A
#0,D0
$7998
Only
one pixels
left
with
shift
Cursor
right
?
No
X offset
for cursor
right
Y offset
for cursor
right
Shift
status
Left
and/or
right
shift
key pressed?
No
Only
one pixel
right
with
shift
Cursor
down
?
No
X
offset
for
cursor
down
Y
offset
for
cursor
down
Shift
status
Left
and/or
right
shift
key pressed?
No
Only
one pixel down with
shift
1&5
Not
greater
or equal
Not
less
or
equal
Surystiqng sal;
s[eusayuy LS Hey

<!-- source-page: 379 -->
## Page 379

Atari ST Internal
First Publishing
TINjJ Teygnq
‘saz
é
Tye} Tenba peoy
yzeys
03
yoeq AequTod
Tesjng
ON
é
payorexr
zayjnq
jo pug
quSWwsADUT
xepuy TTeL
Tptusds
auT ANA
a34noaXxg
JeTpuey
ydnizy4ut
IdIW
OF
1997uUTOd
a kqtpTw
xOpUuT TTR MON
zejjnq
ut eep
SITIM
ssaippe
rajyjnd
[Inj
razgnq
‘saz
é Tye Tenbe pesy
qieys
Zeyyjnq
oj
yoeq Taqutod
rseyjng
ON
& peyoreer
zajgnq
jo pug
@
sntd
xeput
TTeL
ZJaqutod
9e70T
485
L-O0
S3TQ 03 Bpod
TIOSY
SI-8
S2TQ
0} epoouRos
9A6LS
ta’ (ow)9
 a’0#
Pd6LS
Ta’ (ow) b
1a‘t#
ta‘ (ow)s
baq
a*duo
T beaouw
$oq
a‘ duo
a*bppe
MM‘ aAou
90L9
900089¢a
00¢L
c0G9
'00089
728
Tbes
B0008CCE
8qd6 200
bd6L00
706 L00
0d6200
936100
WO6L00
996200
SCTE
eT CT CT CECT ET ELECT ISTIC Le SLE
L
eS Tee SS SS
(ZW)
ew‘ (cv) gows
dul
T° aco
cddp
qOWOdI
PS
726200
096200
POETT ESET SST PCCP CTE C TC PSPS Le Le Le TS SE SET
ee
(ov) 8‘Ta
(M*Td’zv)
0 ‘0d
ew’ (OW) 0
qa6Ls
Ta‘ (ow)9
Ta‘o#
OV6LS
Ta‘ (ow) P
Ta‘Z#
Ta’ (0W)8
ow’+ (LY)
od‘ ta
Ta‘8#
986L$
866L$
OG‘WLS#
866L$
oa‘Tos#
$l
M* eAOU
M*SAOU
T*' aaow
baq
at duo
T’ beaou
soq
a? dus
a*bppe
M* OAOU
T° eaow
M‘*ppe
M*Tse
eiq
Tq
q’° duo
soq
q'duo
SLap
BOO00THTE
oooTOBSE
Q00089
be
20L9
9000897
OO?ZL
2059
bO0089
ca
Tbs
80008CCE
Asgozd
Tpod
Told
ada09
c0c9
WLO00090
8059
T9000000
ag6100
wae2o0
946200
cd6200
odeLoo
OV6L00
vv6L00
8V6L00
PWOLOO0
eWeLoo
a66L00
266L00
V66L00
866L00
966L00
766100
066L00
d86L00
V86L00
372

<!-- source-page: 380 -->
## Page 380

Atari ST Internals
First Publishing
pirogqhsy
IoJ
oaATOT |104S9y
euTANOI
Adnazzejuy
esnow
[TPS
anTeA
- a10NS
anTPA
X 9104S
Jajjgng
ut
aqkq
apesey esnow
eaT eTeT
sntd
0
aTq OF UOAQNG AYSTA
AOZ
ATE
suojqng ,esnow,
eyz
jo
snjeqs 4a
Jo
aA YdnzeAUT
ssnopw
Jajynq 103eTNWs-ssnow
of
TaqUutTog
snewkosy
Aay IOJ
ATT 39S
Kay oy AT 7eETO
passoig
é
peseatei
Jo pesseid
uoqqng
AyeaT
(LO$/L¥$)
UO RING AYbTA
st
uojyng
qybtzI
ydaooy
TsnewAay
XOpUuT [Te] MAN
qajjnq
ut
a3Aq paaTe0er
SBS RTIM
ssoippe
rzejjng
ow‘
+ (LW)
(Zw)
(ow) ‘za
(ow)
T ‘td
(ov) 0/00
od ‘sas#
oa‘s#
od‘ (sv) asws
od
zw‘ (SW) ATWS
ov‘ (cv) wsws
sya
T° aaow
as
q* aaow
q*aaou
q* aaocu
q*ppe
qrasy
q°* ano
[°4To
qT" aaow
eet
SLav
ASO0¢
codap
cooocPrit
TOOOTHIT
OOO0OFIT
84000090
80Va
aswodazot
082d
ATWOd9IFZ
VSVOdaTP
WVCWLOO
8cVLO00
9¢VL00
7CWLOO
ATWLOO
VTWLOO
9TWLOO
PTWLOO
OTWLOO
AOWLOO
VOWLOO
9O0WLOO
PeCCrT CT TET eT ECT ETE
C
SS SC STS Te Le Le
Le
SS ee SS
za ‘OF
Ta ‘o#
(Sv) aSws ‘Eq
ZOWLS
(sw) asws ‘eq
AIG LS
Ta‘ L¥
€a‘9F
746 L$
1G’ b#
€a’s#
T°’ beaow
T° beaow
qesq
eg
IToOQ
baq
4s4q
T' beaouw
baq
4s qq
T° beaow
OOPL
00?L
aSswoddlo
poo9
aSVOaGvLO
90L9
LOOOTO80
909L
cOL9
pOOOTO8O
GO9L
pOWLOO
ZOWLOO
446 L00
246L00
846200
946L00
€46L00
046L00
a2d6 200
Wd6L00
846L00
OR OO
OE EO
OO KOK
OR OR
LOR
OR
OR EOE
EO
OK
(ow)
8 ‘Td
(a°Ta’2v) 00d
zw‘ (OW) 0
coe
Bed
M' SAOUW
q’ aaou
T° eaow
Slav
BO000TPTE
OoOTOSBST
000089b2
9ad6L00
fd6L00
4ad6200
Vd6L00
373

<!-- source-page: 381 -->
## Page 381

ple
ok
kkk kok kkk
kkk kok kok
kok ok
ok
ok kkk kok kook kook
k kkk kkk
OOTA2C
47C7
dc.b
$47,$C7,$52,$D2
kK KK kok kK kkk KR kok
kok kok kk kkk kok ok kok ok kok kk kok kkk kkk kk kok kkk
OO7A30
302F0004
move.w
4(A7),DO
O0O7A38
40E7
move.w
SR,
~-(A7)
OO7A3A 00700700
or.w
#$700,SR
OO7TA3E 48E76080
movem.1 D1-D2/A0,-(A7)
OO7A42
41F9FFFF8800
lea
SFFFF8800,A0
OO7A48
1401
move.b
D1,D2
OO7A4A 0201000F
and.b
#15,D1
OO7TA4E
1081
move.b
D1, (AQ)
OO7TASO E302
asl.b
#1,D2
OO7A52
6404
bec
$7A58
OO7A54
11400002
OOTASS
7000
move.b
D0,
2 (AO)
moveq.1
#0,D0
OO7A5A 1010
move.b
(AQ),DO
OO7ASC 4CDFO106
movem.1
(A7)+,D1-D2/A0
OO7TA60
46DF
move.w
(A7)+,SR
OO7A62
4E75
rts
tok
ok
kk kkk kok kkk kkk kok ek kkk ok kkk kkk eR KR KKK KK RIK
0O07A64
7408
moveq.1
#8,D2
OOTAGE
6012
bra
STATA
RIK KK KK KEK KK KKK KK KI KKK KKK
KKK KK KKK KKKKK KKK KKK AKER
OO7A68B
74F7
moveq.1
#SF7,D2
OO7A6A
6034
bra
$7AA0
FO
I TOKO
KK
KR KKK KK IKK
KKK EK KKK KKK KKK KKKEK KKK KKK KKK IK
OO7A6C
7410
moveq.1
#16,D2
OO7AG6E
600A
bra
STATA
muskeyl
Scan
code mouse substitute
giaccess,
read/write sound chip
Data
Save
status
IPL
7,
disable interrupts
Save registers
Address
of
the sound chip
Get
register number
Registers
0-15
Select
register
Test
read/write bit
Read
Write
data byte
in
sound chip register
Read byte
from sound chip register
Restore registers
Restore
status
rts
off,
disable RTS
Set bit
in port
A
rts
on,
enable RTS
Clear
bit
in port
A
dtr
off,
disable
DTR
Set bit
in port
A
Surysyqnd Isa
yeulszu] LS Wey

<!-- source-page: 382 -->
## Page 382

SLE
FORK
IK IOI
TOR
III
Ok
kk kk tk tok kok koe
OO7A70
74EF
moveq.1
#-17,D2
OO7TA7T2
602C
bra
$7AA0
KKK
IORI
III
I
IO
IO
tok kk koe
datroff,
enable
DTR
Clear
bit
in port
A
ongibit,
set
bit
in
sound chip port
A
OO7A74
7400
movegq.1
#0,D2
OO7A76 342F0004
move.w
4(A7?),D2
OOTATA 48E7E000
movem.1
DO-D2,-(A7)
OOTATE
40E7
move.w
SR,
-(A7)
OO7A80
00700700
or.w
#$700,SR
OO7A84
720E
moveq.1
#14,D1
OOTA86
2F02
move.l
D2,-~(A7)
OCO7A88
61AE
bsr
$7TA38
OO7TA8A 241F
move.]1
(A7)+,D2
OO7TA8C
8002
or.b
D2,D0
OO7A8E
728E
moveq.1
#$8E,D1
OO7A90
61A6
bsr
$7A38
OO7A92
46DF
move.w
{(A7)+,SR
007A94
4CDFO007
movem.1
(A7)+,D0-D2
OO7A98
4E75
rts
RK KK KK I IOI KKK IK IKK
IK KKK KK KK KKK IKK KEK KEKE KKK KKK KKK
QOTA9A
7400
moveq.1
#0,D2
OOTA9C 342F0004
move.w
4{A7),D2
OO7AAO 48E7E000
movem.1 DO-D2,-(A7)
OO7AA4
40E7
move.w
SR,
-(A7)
OOTAAG
00700700
Or .w
#$700,SR
OO7AAA 720E
moveq.1
#14,D1
OO7TAAC
2F02
move.l
D2,-(A7)
OO7TAAE
6188
bsr
$7TA38
OO7ABO
241F
move.l
(A7)+,D2
Get bit pattern
Save registers
Save
status
IPL
7,
disable interrupts
Port
A
Save bit number
Select
port
A
Bit number back
Set
bit (s)
Write
to port
A
Write
new value
Restore
status
Restore registers
offgibit,
clear bit
in
sound chip port
A
Get
bit pattern
Save
registers
Save
status
IPL
7,
disable interrupts
Port
A
Save bit pattern
Select
port
A
Restore bit pattern
Surystqnd 3S114
syeussjuy LS eV

<!-- source-page: 383 -->
## Page 383

OLE
OOTAB2Z
C002
OO7AB4
728E
OO7AB6
6180
OO7AB8
46DF
OO7ABA 4CDFO007
OO7ABE
4E75
OR
IO
Ok kok kok ko kk
kk kkk kak kK kK RR KK KEK KR KR KK KKK
OO7ACO
4A6F0004
OO7TAC4
6726
OO7AC6 2B6EFOOQ0A0AIE
COTACC 266F0006
OOTADO OCEFO0010004
OOTAD6
6724
OO7ADS8 OC6FO0020004
OO7ADE
6736
OO7AEO OC6F00040004
OO7TAE6
6770
OO7AE8
7000
OO7AEA 4E75
and.b
b2,D0
moveq.1
#S$8E,D1
bsr
$7A38
move.w
(A7)+,SR
movem.1
(A7)+,D0-D2
rts
tst.w
4(A7)
beg
S7AEC
move.l
10(A7),$5A1E(A5)
move.l
6(A7),A3
cmp.w
#1,4 (AT)
beg
STAFC
cmp.wW
#2,4 (AT)
beq
$7B16
cmp.w
#4,4(A7)
beg
$7B58
moveq.1
#0,D0
rts
COU
a
kk
kk kaa kkk kkk kk kk ke kkk kick kkk
OO7TAEC
7212
OO7TAEE
6100F1E0
OO7AF2 2B7CO0007BCOOAIE
QOOTAFA
6070
moveq.1
#$12,D1
bsr
$6CDO
move.l
#$7BC0O,$A1E(A5)
bra
$7B6C
KK KK KKK RK KKK KKK KR RK KKK KEE KKK
KK RK RK RK RK RK
OOTAFC 45EDOA6A
0O07B00 14FC0008
007B04
1L4FCO00B
OO7BO8
6166
lea
SAGA (A5)
, A2
move.b
#$8, (A2)+
move.b
#$B, (A2)+
bsr
$7B70
Clear
bit(s)
Write
to
port
A
Write new value
Restore
status
Restore registers
initmouse
Disable mouse
?
Yes disable mouse
Mouse interrupt vector
Address
of
the paramater block
Relative mouse
?
Yes
Absolute mouse
?
Yes
Keycode mouse
?
Yes
Error,
invalid
Disable mouse
Disable mouse command
Send
to.
IKBD
Mouse
interrupt vector
to
RTS
Relative mouse
Transfer buffer pointer
Relative mouse
Relative mouse threshold
x,
y
Set mouse paramaters
Surysyqng ISIy
BULAN LS UeIy

<!-- source-page: 384 -->
## Page 384

LLe
OO7BOA
007B0C
007B10
007B14
7606
4SEDOA6A
6100F1DE
6056
moveq.1
lea
bsr
bra
#6,D3
SAGA (A5)
, A2
S6CFO
$7B6C
FOI
IO
IO FO
OI OIRO
IO
IOI II
IOI
IO
te kt
007B16
OO7BIA
OO7BI1E
007B22
007B26
OO7B2A
007B2E
007B32
007B34
007B38
007B3C
007B40
007B44
007B48
007B4C
CO7B4E
007B52
007B56
007B58
007BSC
007B60
007B62
007B64
007B68
007B6C
OO7B6E
4S5EDOAG6A
14FC0009
14EB0004
14EBO005
14EBO0006
14EB0007
14FC000C
613C
14FCOOOE
14FCcO000
14EB0008
14EBO0009
14EBOOOA
14EBO00B
7610
45EDOA6A
6100F19C
6014
45EDOA6A
14FCOOOA
610E
7605
45EDOA6A
6100F186
TOFF
4E75
lea
move.
move,
move,
move,
move.
move.
bsr
move.
move,
v,rorrese
move.
move.
move.
cor
TFT oO
DF
move.
moveq.1
lea
bsr
bra
lea
move .b
bsr
moveq.1
lea
bsr
moveq.1
rts
SAG6A (AS) ,A2
#9, (A2)+
4(A3), (A2)+
5(A3), (A2) +
6(A3), (A2) +
7(A3), (A2)+
#SC, (A2) +
$7B70
#SE, (A2) +
#0, (A2) +
8(A3), (A2) +
9(A3), (A2)+
10 (A3), (A2) +
11(A3), (A2)+
#16,D3
SA6A(A5)
, A2
$6CFO
S7B6C
SA6A(A5) ,A2
#SA, (A2) +
$7B70
#5,D3
SAG6A(A5)
, A2
S6CFO
#~-1,D0
Length
of
the
strings
-
1
Transfer buffer pointer
Send string
to
IKBD
Absolute mouse
Transfer buffer pointer
Absolute mouse
xmax
msb
xmax
lsb
ymax
msb
ymax
lsb
Absolute mouse
scale
Set
mouse parameters
Initial absolute mouse position
Fill byte
Start position
x msb
Start position
x
lsb
Start position
y msb
Start position
y
lsb
String length
-1
Transfer buffer pointer
Send string
to IKBD
Transfer buffer pointer
Mouse
keycode
mode
Set
mouse parameters
Length
of the
string
~-1
Transfer buffer pointer
Send string
to
IKBD
Flag
for
OK
Surysyqn ISA
sjeusayuy TS wery

<!-- source-page: 385 -->
## Page 385

BLE
oe
RK
IK
kk kok kk kok kkk
kk keke ke tek
oe
007B70
14EB0002
move.b
2(A3), (A2)+
007B74
14EB0003
move.b
3(A3), (A2)+
007B78
7210
moveq.l
#16,D1
OO7B7A
922B0000
sub.b
0(A3),D1
OO7B7E
14c1
move.b
D1, (A2)+
007B80
14FC0007
move.b
#7, (A2)+
007B84
14EB0001
move.b
1{(A3), (A2)+
Q0O7B88
4E75
rts
ROR I OK I KO
OR IO
IO
FOR
IRI
IOI IO
OO
kk IO
ee
007B8A 7000
moveq.1
#0,D0
0O07B8C
7200
moveq.1
#0,D1
OO7B8E
7400
moveq.1
#0,D2
007B90
302F0004
move.w
4(A7),DO
007B94
322F0006
move.w
6(A7),D1
007B98
342F0008
move.w
8(A7),D2
007B9C
6100F4F2
bsr
$7090
OO7BAO
4AAFOO0A
tst.1
10 (A7)
OO7BA4
6B1A
bmi
$7BCO
OO7BA6 246F000A
move.l
10(A7),A2
OOTBAA 7200
moveq.1
#0,D1
OO7TBAC 43F900007BC2
lea
$7BC2,A1
OO7TBB2
O280000000FF
and.l
#SFF,D0
OO7BB8
10310000
move.b
O(Ai,D0O.w),DO
OOTBBC
6100FD88
bsr
$7146
0. 7BCO
4E75
rts
FOR
IO
OK ROO
FOR RK ERK
Rk
kk tke
O0O07BC2 OD080504
dc.b
13,8,5,4
setmouse,
set
mouse parameters
x threshold,
scale,
delta
y threshold,
scale,
delta
Top/bottom
?
xbtimer,
initialize timer
Timer number
(0-3
=>
A
-
D)
Value
for control
register
Value
for data register
Set
timer values
Interrupt vector
Not
used
?
Interrupt vector
Table
for determining interrupt
number
Get interrupt
number
initint,
set
MFP interrupt
Interrupt numbers
of
the MFP timers
Sulysyqng ISI]
yeulaquy TS wey

<!-- source-page: 386 -->
## Page 386

Atari ST Internals
lirst Publishing
uoTyeainbtyjuoo Jejutid yes
qes
3,U0p
‘eat
eben
aNnTePA MON
uoTyeinbTyjuos
zaquytad
 4a5H
uoTyeinbtjuoo
Jaquytid yebsyes
‘jIdJes
eTqe} punos
47e4S
aTqey punos Man
qes
qy,u0p
‘aaT eben
eTqe} punos
eyj
jo ssaippy
snqjeys punos
4a5
punos
32e4s
‘punosop
eTqe3 MOOT
SdVo
eTqeq
3sTUS
aeTqeq pazepueys
aTqey preoqkey piepurjs
yes
‘skaysotq
aTqei
syR
Jo
ssazippe
03 AEqUTOd
aTqe} MOOT
SdV¥D ey
jo ssoippy
ON
2 eTqei WOOT sdyo ebueyo
aTqey asyTus ayy
jo sseippy
ON
é
eTqey astus ebueyo
aTqey pzepuejs
ayy
jo
sseippy
ON
é
eTqey piepueys
ebueyo
atqey
preogqhkay
jes
‘sueijAoyx
(Sv) o8vs
‘ (LW) P
OEDLS
(LY) P
0G’ (Gv) o8ws
M°OAOU
Twa
4°
Sy
M* DAOW
D8WOPOOOAIEE
9089
vOOOdIYE
OBWOAZOE
WZ9L00
829L00
¥ZOL00
O¢OL00
TPCT re rrrTTeTTTT CST OST TELT TELE LT Les ee See ee
(SY) Vews
(cv) 98W$ ‘Td
ATOL$
Ta‘ (Lw)b
0d‘ (Gv) 98VS
sqi
q’ato
T° aaow
Tug
T* eaow
T° aaow
SLab
wewodc7zp
gevoTtbdc
809
booode
22
98WOdc07d
ATIL00
WTOLOO
9TILOO0
PTILOO
OTSL00
909400
ORO
LORE ORO
OO
OR ERE
OUR OR ORO
IR OE IIE OR
RE ROE KOR RE
(GW) 99U$ “7999$S#
(GW) Z9VS ‘7aq9$S4
(SW) ASWS$ ‘Z9a9S#
$42
T‘saow
T’ aaow
T°’ aaow
SLAP
99WOTIAQOQO0OLEC
79VOTAACIOONOILEZ
AGWOC9AIOQO0OLEC
WOOLOO
209L00
Vdd L00
cHadL00
PoC
ETS
eT TCT eC TCE TELS
PL e LS eee Se
eS ee
og ‘asvs#
(Gv) 99WS‘
(LY) 2T
VaaLs
(Lv) 2T
(cv) 2ows ‘(LW)8
add.$
(408
(Sv) aSv$
‘ (LW) b
cages
(LW)0
sa
T* Saou
T* eaou
yuq
T’4sa
T*‘ eaow
yuq
T’asq
T° Saou
Tug
T*4s4
SLAp
AGYOOQO0IED?S
99WODQN00AIES
9009
DOOOAVUE
COWOBOO0AIAC
9089
8Q004UVP
aASWOPOOOA9IEC
9089
DOOOAWWE
O4dL00
VWadL00
badLoo
CaALOO
adqLoo
sddLoo
9dadL00
édadL00
9DaL00
VYOULoo
9D8L00
DE
OR OO
ROR OR A
OR KE RO OO
379

<!-- source-page: 387 -->
## Page 387

O8¢
Se
RKO
OO
I
RO IIR RII
II IOI IOI
III II III
I III Ie ea
ae
007C32
302DO0ATE
move.w
SA7E(A5),DO
007C36 4A6F0004
tst.w
4(A7)
OO7TC3A 6B16
bmi
$7052
007C3C 322F0004
move.w
4(A7),D1
Q0O7C40 1B410ATE
move.b
D1,$A7TE(AS)
007C44
4A6F0006
tst.w
6(A7)
CO7C48
6BO8
bmi
$7052
O07C4A 322F0006
move.w
6(A7),D1
O07C4E 1B410A7F
move.b
D1,S$A7F(A5)
007C52
4875
rts
OK
RKO
IK
TI IO
I I II I
I
I KO
OR
IA
I IIR IO
II
III
Fe IC
IO
ee
007C54
203C00000A0E
move.1
#SAO0E,D0O
OO7CS5SA 4E75
rts
FORO
ROI
III
III
II
IOI I
TOI
II
II
I
KK
007C5C 52B9000004BA
addq.1
#1,$4BA
007C62 ETF900000A84
rol.w
SA84
007C68
6A4E
bpl
$7CB8
QO7C6A 48E7FFFE
movem.1 DO-D7/A0-A6, -(A?)
OO7C6E 4BF900000000
lea
$0,A5
007074
614C
bsr
$7CC2
007076 082D00010484
btst
#1,9484 (AS)
OO7TCTC
672A
beq
$7CAB
OO7C7TE 4A2D0A7B
tst.b
$A7B(A5)
007C82
6724
beq
$7CA8
007C84
4A2DO0A7C
tst.b
SA7TC (AS)
007C88
6706
beq
$7090
NOOTCRA 5S32D0A7C
suba.b
#1,$A7C(A5)
kbrate,
set/get keyboard
repeat
Delay before
key
repeat
Test
new value
Negative,
don't
set
Set
new value
Repeat
rate
Negative,
don't
set
Set
new value
ikbdvecs,
pointers
to
IKBD
+ MIDI vectors
Address
of
the vector table
timercint,
timer
C
interrupt
Increment
200
Hz
counter
Rotate divisor
bit
Not
fourth
interrupt,
then done
Save registers
Clear
A5
Process
sound
Key repeat
enabled
?
No
Key pressed
?
No
Counter
for
start
delay
Not active
Decrement
counter
Surysyqng ISI]
jeur2,UT TS Wey

<!-- source-page: 388 -->
## Page 388

T8¢
OO7CBE
007C90
007094
007C96
oo7Ccg9e
IO7TCAO
OO7CA4
007CA8
0O7CAC
007CBO
OO7CB2
007CB4
007CB8
0o7CCO
6618
532DO0A7D
6612
1B6EDOATFOA7D
102DO0A7B
4 EDO9F2
6100FAEC
3F2D0442
206D0400
4E90
544F
4CDF7FFF
O8B90005FFFFFAI1L
4E73
bne
subq.b
bne
move .b
move .b
lea
bsr
move .W
move.1
jsr
addq.w
movem.1
belr
rte
$7CA8
#1,SA7D(A5)
S7TCA8
SATF (A5)
, SA7D(A5)
SA7B (A5) ,DO
S9F2 (A5) ,A0
$7792
$442 (A5) ,- (A7)
$400 (A5)
, AO
(AO)
#2,A7
(A7) +, DO-D7/A0~A6
#5,$FFFFFA11
eR KOO
IO
IOI IO ORI
IOI IO
ROI
OI I III
III
I
tee a
007CC2
007CCE
OO7CCA
OO7CCE
007CDO
007CD4
007CD6
007CD8
O07CDC
OO7CDE
OO7CEO
OOTCE2
OO7CE8
OOTCEC
OO7TCEE
48E7C080
202D0A86
67000088
2040
102DO0A8A
6708
5300
1B400A8A
6076
1018
6B2E
13COFFFF8800
0c000007
661A
1218
movem. 1
move.1
beq
move.1
move .b
beq
subq.b
move .b
bra
move .b
bmi
move .b
cmp.b
bne
move .b
DO-D1/A0,~(A7)
$A86(A5)
,DO
$7D54
DO, AO
SA8A (A5)
, DO
$S7CDE
#1,D0
DO, SA8A(A5)
$7D54
(AO) +,D0
$7D10
DO, SFFFF8800
#7,D0
$7D08
(AQ) +,D1
Not
run
out
?
Decrement
counter
for
repeat
delay
Not
run
out
Reload counter
Key
to
repeat
Pointer
to
iorec keyboard
Key code
in keyboard buffer
20 millseconds
per
call
Get event timer vector
Execute routine
Correct
stack pointer
Restore registers
Clear
interrupt service
bit
sndirg,
sound interrupt
routine
Restore registers
Pointer
to
sound table
No sound active
?
Pointer
to
AO
Load timer value
New
sound started
?
Else decrement timer
And save value
Done
Get
sound command
Bit
7
set,
then special
command
Select
register
in
sound chip
Register
7?
No
Data
for
register
7
Surysyqnd S11
sjeulsjuy TS Wey

<!-- source-page: 389 -->
## Page 389

Atari ST Interna
First Publishing
sZaystbel
aro say
aares
puy
O19aZ
OF
AB UTOd puNOS
Zeuty AeTep
se anTea
4xeN
puewwoo sues
O02 yorq AaquTOd punos
soz
é
payoreld anTea pug
Zaystbar
drys punos
ut
anTea o3TIM
eNnTeA pug
ANTRA-4UaUeTOUT
pPpY
qaqystThar
yawpas
Jawty
Jas
‘saz
é
T8$
< pueuuod
puewwos punos
4xeNn
TBReT
A0J
a Aq
oars
ON
&
O8$
PpUeWUOD
seM
sox
é
dag pueuwod
sem
puewwos punos
4xeN
dtyS
punos
ut
AT 4oerTp
aqAq 33TIM
puewwos punos
Man
ZJeysthez
dtTyo punos
ut
aqAq a3TIM
eq ep Yo
L-9
SATO
Ss VeTOsS]T
JaxTu peay
S
-
0
$3TqQ aQeTOST
oW/Td-00
‘+ (LY)
(SV) 98S ‘OW
ov ‘O#
OSaL$
(sv) v8us
‘+ (OW)
OSGL$
OW ‘oF
OSaL$
Od‘ (cu) devs
COSBATIIS
4 (GY) ABS
oa’+ (ow)
(sv) aews ‘0d
oa’+ (OW)
0088adad4a$
“+ (0)
9PaL$
oa‘zss#
AdOL$
(GW)
devs ‘+ (OW)
ozaLs
od‘tss#
9PGLS
oa’T#
adoL$
ZOBS8ATTTS
“+ (OW)
BqOL$
ZOS8AdA4$
‘0d
oa‘ta
od‘oos#
0d ‘0088444
4$
Ta‘aes#
T*weaou
T‘ aaou
M* SACU
auq
q* asAou
eaiq
a*bqns
beq
q*duo
q* aaou
q* aAow
q*ppe
q°aaow
q* saou
auq
q* duo
eiq
q* enow
euq
q: duo
dq
q'bppe
eiq
q' eaow
e1ig
q’aaow
q' io
q*pue
q* aaow
q*pue
COTOAGOH
9BVO8 PEC
OOO0DLOE
099
vsvossdr
Vvoo9
8P6S
qOL9
aevodcod
TOSSA
Hd ATASVOCHET
STOT
aevwodctd
8TOT
OOS8AATABAET
0299
28000090
ado9
aswossat
9099
T80000090
cews
00¢S
409
COBSBdddA8E T
9009
COB SHddATHOOET
TO08
03000020
O08 8dddH6E0T
Jedotoco
pSAL00
OSdLO00
27daLo0
WPALOO0
9bdL00
ppaLoo
cbALO00
OPdLO00
SEGLOO
pEdLOO
Z€al00
a2dqL00
220400
9e€aL00
’cdL00
ocaqLoo
aTGL00
Wtqazoo
8Taz00
bTAL00
7TAL00
oTaLoo
A0GL00
g0dazoo
900100
OOdL00
AIOLOO
WADL00
7ADLOO
OSDL00
382

<!-- source-page: 390 -->
## Page 390

Atari ST Internals
irst Publishing
yoeqje
eThSuts
edoTsaug
Ww Tauueyo sdoTaaug
yoTTO Aay
‘yxTOKay
yw Teuueyo adoTeaug
9 THLO Jeyye suc
‘pusTtTeq
aes ‘o
q°op
q*op
q'op
q'op
q'op
q'op
q‘op
q'op
q7op
q'op
q'op
q°op
TOD0
08do
€0d00
OT80
adal0
0090
00S0
000
00£0
00¢0
0oTo
ae00
aBdLOO
380100
W8daL00
88dL00
98daL00
b8dqLoo
Z8dL00
080400
aL0L00
OLAGLOO
WLAL00
BLAL00
PeCTTET TET PTET ELOCC CS OLES ECE SCTE ES Le SESS SS
ee
0 ‘das
6 ‘ET
Os ‘Zt
O‘TT
0’OT
06
ots ’s
Keen
bes ‘0
q’op
q'op
q'op
q'op
q°op
gop
q’op
q'op
q'op
q'op
q'op
q'op
q'op
q’op
q'op
elercecs
60d0
0T30
000
oovo
0060
oT8o0
aAdlo
0090
0050
00b0
OO£Od
00c0
OOTO
bead
940400
pLALOO
7LALOO
OLGLOO
a9dLoo
D9aL00
¥9dL00
890400
99d4L00
p90L00
Z9GL00
03dL00
aSaLOO
2GdL00
¥SdL00
FER OO
OR OO
OL RO
OR OR OE
OR ORE
KOE
OLE ROE
OR OR OER EOE EOF
sa
GLAD
8SGL00
383

<!-- source-page: 391 -->
## Page 391

P8e
ODIDBS
FFOO
dc.b
SFF,O
eR
OK IK
ORI
kk kk kk
kkk ee
de
O07D92
OO7D9IE
OOTDIA
OO7TDIE
OO7DA4
OO7TDAG
007DA8
OO7DAA
OO7TDAC
OO7DAE
0O07DBO
007DB6
007DB8
OO7DBE
oo7DCO
OO7DCE
007DCC
0O7DD4
OO7DD6
OO7TDDS8
0O07DDC
OO7DE2
OO7DE4
OOTDEG6
OO7DES8
OO7DEA
007DFO
OO7DFE6E
4E560000
48E7070C
Z2A6E0008
287000002600
TELE
6004
18DD
5347
4A47
6EF8
4AB90000261A
6708
20390000261A
6006
203C00016D4C
23C00000261A
0€79000100002618
6306
JOFF
60000BC6
4A7900002618
6704
4240
6002
7001
13C0000025FE
4A7900002608
6642
link
movem.1
move.1
move.1
moveq.1
bra
move.b
subq.w
tst.w
bgt
tst.l1
beq
move .1
bra
move .1
move.1
cmp.w
bls
moveq.1l
bra
tst.w
beq
clr.w
bra
moveq.1
move .b
tst.w
bne
A6, #0
D5-D7/A4~-A5,-(A7)
8(A6),A5
#82600,A4
#30,D7
$7DAC
(AS)
+, (A4) +
#1,D7
D7
$7DA8
$261A
$7DCO
$261A,
D0
$7DC6
#$16D4C,
D0
DO,$261A
#1,$2618
$7DDC
#-1,D0
$89A0
$2618
$7DE8
DO
S7DEA
#1,D0
DO, $25FE
$2608
S7E3A
Hardcopy
Save
registers
Address
if
the parameter
block
Address
of
the working memory
30 bytes
Put parameters
in working memory
Next
byte
p masks,
half-tone
mask
Not
used
?
Load mask
Default
mask
p masks
p
port
Set
flag
Error,
stop
p port
Centronics
?
O= RS232
1= Centronics
Printer port
Height
Not
zero
?
Sulysyqng Isiy
eulsjuy TS uBy

<!-- source-page: 392 -->
## Page 392

S8e
COTDES
OO7DFA
0O07E00
OOTEO2
OO7EO8
OOTEOA
OO7EOC
OO7EOE
CO7TE12
007E18
OOTELA
OOTEIC
OOTELE
OOTE2Z2
OO7E24
OO7E2A
007E30
O07E32
007E34
OO07E36
OO7TE3A
OOTE42
OO7E44
OO7TE46
OOTE4A
OOTES2
DOTES4
OOTESE
6028
4A79000004EE
6632
207900002600
1010
4880
3E80
61000B9A
52B900002600
4A40
6706
TOFF
60000B80
4240
303900002606
537900002606
4A40
66C6
4240
60000B68
0C79000300002616
6306
JOFF
60000B58
0C79000100002610
6306
TOFF
60000B48
bra
tst.w
bne
move.1
move.b
ext.w
move .W
bsr
addq.1
tst.w
beq
moveq.1
bra
clr.w
move .W
-subq.w
tst.w
bne
clr.w
bra
cmp.wW
bis
moveq.1
bra
cmp. w
bls
moveq.1
bra
S7E22
S4EE
$7E34
$2600,A0
(AQ) ,DO
DO
DO, (AT)
S89AA
#1,$2600
DO
$7E22
#-1,D0
$89A0
DO
$2606,D0
#1,$2606
DO
S7TDFA
DO
$89A0
#3,$2616
S7E4A
#-1,D0
$89A0
#1,$2610
S7E5A
#-1,D0
$89A0
scrdump
flag,
ALT
HELP
pressed again?
Yes,
stop
bikptr
Get byte
from video RAM
On
the
stack
Output
byte
Increment blkptr
Output
OK
?
Yes
Set
flag
Error,
stop
width,
screen
width
Decrement width
Already
zero
?
No,
output
next
byte
Flag
for
OK
Done
p type,
Epson
B/W matrix
Set
flag
Error,
stop
dstres,
printer resolution
Set
flag
Error,
stop
Surysi[qng 3S.
sfeuisjyoy TS wey

<!-- source-page: 393 -->
## Page 393

98¢
OO7ESA
OOTE62
OOTE64
OO7E66
OO7E6A
OO07TE72
007E74
OO7TE7E
OO7TETA
OO7E80O
OO7TE82
OO7E84
OOTE86
OO7TES88
OO7E8E
OO7E96
OO7E98
OOTE9SA
OO7E9C
OO7TE9E
OO7TEA4
OO7EAC
OO7EAE
OOTERO
OOTEB2
OQTEB4
OO7EBA
OO7ECO
OO7TEC2
OO7EC4
0€7900020000260E
6306
TOFF
60000B38
0€79000700002604
6306
7OFF
60000B28
4R790000260E
6704
4240
6002
7001
13C000004F82
0C7900010000260E
6704
4240
6002
7001
13C000004ED6
0C7900020000260E
6704
4240
6002
CUMS
7001
13CQ00004ED8
447900002610
6704
4240
6002
cmp.w
bls
moveq.1
bra
cmp.w
bls
moveq.1
bra
tst.w
beq
clr.w
bra
moveq.1
move .b
cmp.w
beq
clr.w
bra
moveq.1
move.b
cmp.w
beq
clr.w
bra
moveg.1
move .b
tst.w
beq
cir.w
bra
#2,5260E
STE6A
#-1,D0
$89A0
#7,$2604
STEVA
#-1,D0
$89A0
$260E
$7E86
DO
$7E88
#1,D0
DO, $4F82
#1,$260E
S7E9C
ete)
S7E9E
#1,D0
DO, S4ED6
#2,$260E
STEB2
DO
S7TEB4
#1,D0
DO, $4ED8
$2610
STEC6
DO
STEC8
sreres,
screen resolution
Set
flag
Error,
stop
Test
offset
Set
flag
Error,
stop
srcres,
screen resolutionm
Low resolution
?
Flag
for
low resolution
srcres
Medium resolution
?
Flag
for medium resolution
sreres,
screen resolution
High resolution
?
Flag
for high resolution
dstres,
printer resolution
Test
mode
?
Quality mode
SurysTqng ISIN]
youu, LS uey

<!-- source-page: 394 -->
## Page 394

L8e
OOCTECE
OO7TEC8
OOTECE
OOTEDE
OOTED8
OOTEDA
QO7EDC
OO7EDE
OOTEES
OO7ERC
OO7ERE
OO7EFO
OO7TEF2
OOTEF4
OO7VEFA
OO7TFO2
OOTFO4
OO7TFO6
007FO8
OOTFOA
OO7F10
OO7TF16
0O7F18
OO7TF1A
OOTFLE
007F24
OO7TF26
OOTF2C
OO7TF2E
007F30
OOTF32
7001
13CO00004EE8
0€79000100002616
6704
4240
6002
7001
13C0000047CE
0C79000200002616
6704
4240
6002
7001
13C000004F84
0€79000300002616
6704
4240
6002
7001
13€0000047D0
4A3900004F84
6706
TOFF
60000A84
4A39000047D0
670C
4A3900004EE8
6604
7TOO1
6008
103900004EE8
moveq.1
#1,D0
move.b
DO,S$4EE8
cmp.w
#1,$2616
beq
STEDC
clr.w
DO
bra
STEDE
moveq.1
#1,D0
move.b
DO0,$47CE
cmp.Ww
#2,92616
beq
STEF2
clr.w
bo
bra
STEF4
moveq.1l
#1,D0
move.b
DO,S$4F84
cmp.W
#3,5$2616
beq
$7F08
-
clr.w
DO
bra
S7FOA
moveq.1
#1,D0
move.b
DO,$47D0
tst.b
S4F84
beq
STF1E
moveq.1
#-1,D0
bra
$89A0
tst.b
$47D0
beq
$7F32
tst.b
S4EE8
bne
$7F32
moveq.1
#1,D0
bra
STF3A
move.b
S4EE8,D0O
Printer
mode
p type,
ATARI
color matrix
ATARI
color dot-matrix printer
p type,
ATARI
daisy wheel
?
Yes
Flag
for ATARI daisy wheel printer
p type,
Epson
B/W Matrix
?
Yes
Flag
for Epson B/W dot matrix
ATARI daisy wheel printer
?
No
Error,
stop
Epson
B/W dot-matrix printer
?
No
Printer test
mode
?
No
Printer resolution
Surysyqng ISI
s[euiayuy LS wey

<!-- source-page: 395 -->
## Page 395

88e
COTE 38
OOTF3A
OO7TF40
OO7F46
007F48
OO7F50
OOTFS2
OO7TF54
OO7FSA
OO7FSE
OO7F64
OO7FE6C
OO7F6E
OOTF76
OOTF73
OOTETA
OO7F80
OO7F84
OO7F8A
OO7TF92
OO7F98
OO7TF9C
OOTESE
OOTFA2
OO7FA8
OO7FAA
0O7FAC
OO7FBO
OO7FB6
OO7FBC
OOTFC4
OOTFC8
4880
13COQ00004EE8
4A3900004F82
6726
0C€79014000002606
631C
4240
303900002606
DO7CFECO
D1790000260C
33FC014000002606
6024
0C79028000002606
631A
4240
303900002606
DO7CFD80
D1790000260C
33FC028000002606
4A3900004ED8
660001E6
4247
600001D8
207900002612
4240
an19
oVav
cO7C07177
33C0000047BA
54B900002612
0€790777000047BA
67000194
3039000047BA
DO
DO, S4EE8
S4F82
STF6E
#320,$2606
S7F6E
DO
$2606,D0
#SPECO,DO
DO, $260C
#320,$2606
S7TF92
#640,$2606
S7F92
dO
$2606,
D0
#SFD80,D0
DO, $260C
#640,$2606
S4ED8
$8180
D7
$8178:1n1l
$2612,A0
DO
{AO}
, DO
#$777,D0
DO,$47BA
#2,$2612
#8777, S47BA
S815A
S47BA,D0
Printer resolution
Low resolution
?
No
width,
320 points
per
line
width
-320
Plus
right
width,
320 points
per
line
width,
640 points
per
line
width
-640
Plus
right
Width
to
640
High resolution
?
Yes
Clear
color
counter
colpal
Get
coior
Mask irrelavant bits
Save
color
colpal pointer
to
next
color
Color equal white
?
Yes
Load
color
Surystqng Ist
sjeusajuy ES Ley

<!-- source-page: 396 -->
## Page 396

68¢
OO7FCE
OO7FD2
OO7FD8
OO7FDE
OO7FEQ
OOTFE4
OO7FEA
OO7FFO
OO7FF2
OOTFF6
OOTFFC
008002
008006
008008
O0800A
008010
008016
008018
OO801A
008020
008024
00802A
oo8o2c
008032
008034
008036
008038
00803E
008042
008044
008046
00804Cc
c07C0007
33C0000035C2
3039000047BA
E840
C07C0007
33C000004EDA
3039000047BA
E040
co7c0007
33C000004694
4A39000047CE
67000114
3047
D1ic8
D1FCO0004EEC
30B900004694
3047
D1c8
227COO004EEC
30309800
B07900004EDA
6F08
303900004EDA
600E
3047
D1c8
227CO0004EEC
30309800
3247
D3C9
D3FCOOOQ04EEC
3280
and.w
move .W
move .W
asr.w
and.w
move .w
move .W
asr.w
and.w
move .W
tst.b
beq
move .W
add.1
add.l
move .W
move .W
add.
move.1
move .w
cmp.w
ble
move.w
bra
move .W
add.1l
move .1
move .W
move .W
add.1
add.1
move .W
#7,D0
DO, $35C2
$47BA,
DO
#4,D0
#7,D0
DO, S4EDA
$47BA,
DO
#8,D0
#7,D0
DO, $4694
$47CE
$8118
D7,A0
AO, AO
#$4EERC,A0
$4694, (AO)
D7,A0
AO, AO
#$4EEC,Al1
0(AO,Al.1),D0
$4EDA,
DO
$8034
S4EDA,
DO
$8042
D?7,A0
AO, AO
#$4EEC,Al1
0(A0,A1.1),D0
D7,Al
Al,Al
#S4EEC,A1
DO, (Al)
Isolate blue
level
And
save
Load color
Isolate green
level
And
save
Load color
Isolate
red
level
And
save
ATARI
color dot-matrix printer
?
No
Red level
Green
level
Green
level
Surystjqng 38114
sjeuiayuy PS Weyy

<!-- source-page: 397 -->
## Page 397

Atari ST Internal
First Publishing
{eaaeT
useaI5
TeAasT poy
TeaeT pox
TeaeT pay
TaaaeTt
enta
TWOdabS#
Tw‘IW
Tw‘id
od ‘vaars
b69b$ ‘Od
od‘ T#
pvoss
od
cwORss
oa‘tad
Ta‘t#
Ta‘ (TY)
TW‘OURbSH
TW‘TW
Tw‘iG
0d‘ b69P$
(Tv) ‘od
TW ‘Oda bS#
Tw/TW
Tw‘id
od’ (T‘Tw‘ov)o
TW‘Odab
SH
ov ‘ow
ow‘id
WLO8$
0a‘ zosEs
2908S
od‘ zoGEes
od‘ (T*Tv‘0¥)9O
TW ‘OaabS#
ow ‘ow
ov‘iad
T’ppe
T'ppe
M*SAOU
A*aaou
M* aAOU
T* beaou
eg
M‘1IToO
bq
a‘qns
M*bppe
M* 2AOW
T’ppe
T’ppe
M* SAOW
M* aAou
M*SAOU
T° ppe
T"ppe
M* aAoU
M* SAOU
T* aaou
T'ppe
M* SAOUL
PIq
M* @A0OU
eTq
M* duo
M*OAOU
T° eaow
T'ppe
M*OAOUW
OFT dOO00DTED
60€ed
LocE
YVAIAPOOOOGEOE
'69 POO0D0DEE
TOOL
rAavels)
Ob?d
b0a9
Tb06
Tbes
TICE
ekctce Zelolererer: tai¢!
60d
LUCE
b69POOOO6EOE
O8ceE
oda pooodo4ed
60€d
LUCE
OO860E0E
OAAPOODDIL
Ze
89Td
LUOE
FOo9
COGEQOOOGEDE
8049
cOSEQOO0G
LOE
OOBGOEOE
OFAAPOOONIL
eZ
BOTd
LBOE
badOso00
cd0800
0d0800
WVO800
PYO800
cW0800
AWVOoSNAN
veivouy
d60800
260800
Y60800
860800
960800
060800
480800
980800
980800
b80800
aL0800
9L0800
WLO800
9L0800
0L0800
490800
990800
¥90800
b90800
290800
950800
850800
cSO0800
OSsoBod
abO800
390

<!-- source-page: 398 -->
## Page 398

Atari ST Internals
Fit Publishing
[aaeT poy
Teast
enta
TeAeT
useIyD
TaaaT pey
TaaAeT entd
TaaaT pew
Teast
uselt5
0d‘ 69S
BcTss
(ty) ‘oa
Tw‘S69PS#
Iv ‘TW
tw’Ld
od’ zoses
oa‘ta
Ta‘t#
ta “wdaps
oa‘z#
Od’ h69bS
zases ‘0d
od‘T#
Dg08$
od
wa08s
oa‘td
Ta‘t#
ta‘ (Tw)
Tw ‘Oda
s#
Tw‘TW
Tw‘La
oa‘zoses
wdaaps ‘od
od‘ T#
g208$
oa
9908$
oa‘ta
ta‘t#
ta’ (tw)
mM‘ oAoU
BIg
M*oACU
T*ppe
T*ppe
M* aA0U
M*ppe
A*ppe
M*Tse
M* aAou
A‘Tse
M* 8A0Ul
M* SACU
T* beaow
eiq
M‘2ToO
bq
a‘qns
a*bppe
M*aAoU
T*ppe
T*ppe
M* BAOW
M* BAOU
M*SA0U
T’ beaow
eIq
M*ITO
bq
a'qns
a*bppe
A* SAOU
769 POOODGEDE
009
O82E
869P00000TE0
60€d
LUCE
7OL200006L00
Tpod
Tred
VAAPOOOOGEZE
ObSa
PE9DOOOOGEDE
ZISEQOOOOSEE
TOOL
c009
Obed
bods
Th06
Tes
TT¢e
Daa POOOOoMED
60d
LbcEe
ZISEQOOOOGEOE
VAI
OOCOOQIEE
TOOL
2009
ORD
bods
1b06
Tbs
TIce
8TT8O0
9TT800
bIT800
A0TBOO
20T800
VoT800
vOTS&OO
ZOT8OO
OOoTts8od
VI0800
840800
7410800
940800
VWA0800
840800
940800
¥40800
240800
040800
4d0800
8d0800
9d0800
’qdosoo
ID0800
820800
990800
£50800
f30800
090800
aAdosoo
240800
vVdos8o0
391

<!-- source-page: 399 -->
## Page 399

Atari ST Internal
First Publishing
Od‘p# T*beaou
POOL 88T800
ON
q6TS$
baq
9TL9 981800
é UOTINTOSeT MOT
c8dP$
9°98
ZBAPOOOOGEVPY 081800
ToTOo yxeu
‘ON
ZWAL$
374
pZHA0009 OLTBOO
é
Apeairle paetTpuey sAoToo
gf
La‘OTS#
M* duo
OTOODLSA 8LT800
IsVUNODS
AOTOO
AUSswsrsuyt
La‘t#
ma*bppe
LePZS
9LT800
(ay) ‘@¢
M* Saou
SOCODGOCE
ZLTSOO
Ow‘ORarS#
© T° ppe
Oda PO000DATA 39T800
ov‘ow
T°ppe
89Td W9ITB8OO
ov‘i.q)
s*aacw
LPOE 89TB800
(OW) “Le
0M" SACU
LOOODHOE ¥9T800
OV’869bS#
T°ppe
869P0000D4TA ASTB8O0
ov ‘ow
T’ppe
8OTd 9ST800
ov‘tg
= BAW
LPOE WSTB00
TUT? 9LT8S
BAq
STO9 8ST800
(ov)
M*°ITO
OSZb 9ST800
OV’S69bS#
T° ppe
869PO000DATA OST800
ov‘ow
T'ppe
891d Av”T8OO
ow’Ld
=M*eAOW
LPOE DPT800
(T¥) ‘oq
M*eaou
O8ze WFT8O00
Tw/OagbS$
T'ppe
DFAPOOOOOMEA PPTBOO
Iv‘Tw
 T'ppe
6DEd ZPT800
Ty‘iq
M‘eAou
LYZE
OPTBOO
puTTeos
‘ooT
Aq apTtata
Od‘’p9S#
MM SATP
p9OO0DMTB8 DET8CO
oq
= =T'3x%e
OD8h VET8O0
od‘Tad
=A’ ppe
Tpod 8€Ts800
Hut IYhTom
FTl
“TT
sowtL
Ta‘as#
a*stToaw
d000DFED PETBOO
TeAeT
ent”
Ta‘ZOSES
MM’ SAOW
ZOSEOCOO6EZE AZTBOO
Od‘Taq
A‘ppe
Tod Dz1800
butqyhtom
365
‘6g
SeUTL
Ta‘aes#
a’ stow
GEOODIED 821800
TaAeT
YweeI5
Ta‘vadps
Mm’ eaow
WAHPOOOO6EZE 721800
Sutqubtom
zoe
‘OE
SaUTL
Od‘ats#
a sTnu
ALOODALO ATI80O
392

<!-- source-page: 400 -->
## Page 400

Atari ST Internals
First Publishing
oda‘cagbs
ac stn
ZaavVOOOOGATO 022800
0d’7969b$
M°eAow
969POOOOGEOE VIZ800
969~S$’0d
M*aAoU
96E9POOOOODSEE
PIZB8CO
oa’be
= MAST
8P8d Z1Z800
od‘s9Lb$S
MT aTnw
89Lb00006409 207800
qw5Ty
oa‘o09z$
=
A Ppe
309700006400 902800
qybT eH
0a‘9092$
A*ppe
909Z00006L00 00z800
3yeT
oad‘wo9zg$
9=M* BAOU
WO9ZTOODOGEDE YATBCO
og
=
=A*ato
Ov2b 8AT800
D04P$’0d
A*eaou
DOAPOOOOODEE ZATBOO
od‘+(L¥)
A SATP
J0T8 041800
oq
=1° 4x8
0D8b AAT800
od‘D04p$
M* SAU
DOAPOOOOBEOE 8AT800
(Lv)-‘T#
M7 eAOU
TOOODEME PATSOO
Sates
eq
p009
241800
(LV) -‘7#
= O-M* BAU.
ZOOODEME AATSOO
ON
Patses
baq
90L9 DaT800
&
zJequtiad xtaqjew-~jop M/d
uosdq
OaLes
q°4s
OGLPOOOOG6EVE
9GTS00
DOMbS/TH
BM BACW
DOAPOOOOZOOODAEE AOTSOO
THabS “B#
<M” BAOU
TAAPOOOOBOOODTEE 9DTBOO
BOLES‘T#
M*aAoU
B9LPOOOOTOOODMEE TATSOO
TUT: 9aT8$
BIg
8109 DATs00
ZAaPS ‘be
= M* BAOU
TAAPOOOOPOOODHEE
FPATSCO
B9Lb$‘0d
M*eAcU
B9I9LPOOOOODEE AVT8OO
20ap$ ‘0d
A‘ eAow
DOAPOOOOODEE BVTs00
oa‘z#
T° beacw
ZOOL 9¥T800
ON
qatss
baq
8TL9
PYT800
é
uvotynptoser wuntpey
9qars
q°4s4
9CAPOOOOG6EVD AGTBOO
9aTss
eiq
8E09
361800
89LbS‘0d
M*eacu
B9LPOOODDDEE 961800
Zaae$ ‘OQ
M*eAoW
ZAAPOOOOODEE 061800
Dodrs ‘od
M'*eAou
DOATPOOOOODEE W81800
393

<!-- source-page: 401 -->
## Page 401

v6e
008226
00822C
008232
008238
00823E
008244
00824A
00824C
00824E
008254
008256
008258
00825E
008260
008266
00826C
008270
008276
OO827A
008282
008284
00828A
008290
008292
008298
00829A
00829C
008295
0082A0
0082A6
0082AC
OO82AE
33C000003E80
203900002600
COBCFFFFFPFE
23C000004
6B8
203900002600
BOB9000046B8
660A
4240
303900002604
600A
4240
303900002604
5040
33€0000047BC
4279000012EA
60000716
4A79000004EE
6600071E
13FC000100003628
4240
303900002606
COF 900004768
E848
907900004768
E348
4840
4240
4840
DOB9000046B8
23C000004EDC
700F
4241
move .w
move.1
and.l
move.l
move.1
emp.1
bne
clr.w
move .W
bra
clr.w
move .w
addq.w
move .W
clr.w
bra
tst.w
bne
move .b
clr.w
move .w
mulu.w
isr.w
sub.w
lsl.w
swap
clr.w
swap
add.l
move.1
moveq.1
clr.w
DO, $3E80
$2600,D0
#SFFFFFFFE,
DO
DO, $46B8
$2600,D0
$46B8,D0
$8256
DO
$2604,D0
$8260
DO
$2604,
DO
#8,D0
DO, $47BC
S12EA
$8984
S4EE
$8996
#1,$3628
DO
$2606,
D0
$4768,
D0
#4,D0
$4768,
D0
#1,D0
DO
DO
Do
$46B8,D0
DO, $4EDC
#15, D0
D1
blkptr
Create
even
address
And
save
bikptr
Offset
Offset
dumpfilg,
ALT
HELP pressed again
?
Yes,
terminate
width
Pointer
to video
RAM
Surysyqng 3saly
sjeuisjyay TS UByy

<!-- source-page: 402 -->
## Page 402

Atari ST Internals
Fi
t Publishing
Ta ‘elaps
Ta‘St#
oa’ (ow)
ov ‘SaLPs
p9ess
9d
FaLys ‘OC6 rs
qOavs “TH
W1Iap$
padess
La
D6
b$ ‘Odar$
zdaps ‘0G
Od ‘Wazt$
qybtey
0a‘809z$
od
ZOE8S
od‘ caaps
bdzes
oa‘zaaps
od
oa
od
Od ‘VazT$
qybtey
oa‘8o09z$
od
7AEBS
YUIPTA
DTae$ “9097S
ZTdp$ ‘0d
oa‘td
Td‘ ase
yqPtsa
Ta‘9092$
a*qns
T* beaouw
M* 9A0U
T° eaouw
eiq
M*ITO
T' eaou
M*SAOW
M°IToO
e1iq
M* ITO
T° aaou
M*3AOU
a‘qns
M* aAOU
M*ITO
eiq
M* SAOW
baq
M*nATP
demas
M‘2TO
dems
mM‘qns
M* SAOU
M*ITO
eg
M* aA0U
M*3AOU
a‘qns
m*pue
M*oAOW
7TAPO0006L26
do7el
OTOE
FAL POOOOGLO?S
0€09
9b¢cP
FAL POO0ODE6 POOOOE AEC
FOAPOOOOTOOODAEE
VIAbOOO06L2P
46000009
Lech
DE6 POOOODdAPONNNEGHEC
TOAPOOOOODEE
WAZTO0006L06
B09 COOOOGEDE
OpcY
a009
TAAPOQOOGEDE
80L9
2440700006408
Ob8P
ObcP
Ob8P
WAZTO0006L06
B09 ZOQOO0GEDE
OCD
beTO0009
IZAEOONOO9O9ZOOONGAEE
ZTIAPOOQOOODEE
TPO06
AQ00DLZO
909 ZOO000GECE
aEesoo0
3€€800
WEEs8O0
peesoo
Z7EEBOO
oceso0
9Z€800
aTesoo
8TEs00
PTE800
ZTE800
80€800
Z0€800
3472800
942800
¥12800
€4 7800
972800
WaAcsB00
bazsoo
7a7800
Ouc800
Adz800
gdqzs00
7dz2800
oagéso00
392800
292800
3dz800
vdzs800
9d72800
Odzs00
395

<!-- source-page: 403 -->
## Page 403

Atari ST Internals
First Publishing
1a
ON
uoTynjtoser
YSTtH
Daees
8Z9E$
BTEBs
ia‘cdaps
La‘T#
De6
Ps ‘0d
od
oa‘t#
0a‘9699S
aaess
ez9e$
ewess
(OW) ‘8#
OW ORAS #
ov ‘ow
OW ‘VTAbS
zvess
aaess
gz9es
P8Ees
Wars
9B8E8$
eaaes
pEeess
90‘B89L5$
9a‘T#
qOaPs
qaL
ps ‘7H
VI4ps ‘0d
od‘d0aes
od‘T#
oa‘ta
beq
q°ysy
ATO
m*duo
ma‘ bppe
T'ppe
T° 3x8
A°Tse
M* SaAOU
eg
q°’aqo
baq
a4‘ duo
T'ppe
T° ppe
M*aAOW
ePmq
Pig
q’ato
baq
a° ys
baq
g°4sy
ATO
M*duo
M*bppe
M’TsSe
T bppe
M*ppe
A‘sTou
M*pue
M*Ise
9EL9o
BZIEOOOOG
EVD
3Gd40009
20a P0006
LAE
Lvcs
3€6 7oO0006aTA
098>b
Obed
969 FOOO06EDE
oT09
BZICOOOOGECH
80L9
80000590
949 P00000KTA
gota
VTAPOOOOGLOE
2T09
Weo9
BCIEQOOOGECH
80L9
VIAPOOOOGLYD
eTLg
BACAPOOOOGENP
god9
89LFOO006LO8
9b¢S
dAOApOO006ATA
Hal booo006abS
VIdpooo0eLtd
FOAPOOO0E
ATO
TOO09DL09D
0924
pOEBOO
adesoo
vdes8o0
Pade 800
cade 800
OVE800
WVE800
BYE800
eWE800
OVE BOO
V6es800
86E800
b6E800
a8sesoo
D8E800
98€800
p8esod
Z8€800
ILEBO0
VLEBOO
VLEBOO
ZLE80O
39€800
W9E800
P9E8O00
e9€800
OSE800
9S€800
OSEsOD
VPE8OO
97€800
bPEBOO
396

<!-- source-page: 404 -->
## Page 404

Atari ST Internals
First Publishing
vases
Big
9VP00009
ZhP800
ZaLp$
=
==M*ATO
TALPOOOO6LZ DEHBOO
esaes‘od
q*aaow
S8ACOOOOOSET 9EPR00
Od‘OOTS#
A’ SATP
OOTODATS ZEPB00
oad
st" 3x8
Od8b O£PB00
oqd‘iaq
4° aAoU
LOOE FZv800
osaes‘od
q*eaow
O9BALEQOOOODET 8ZH800
od
dems
Ob8Sh 972800
Od‘OOTS#
M*SATP
OOTODAT8 22800
oq
=1°3xe
OD8b OZP800
oq‘id
= M*eAou
LOOE ATP8OO
Ld‘0gd)
ss A" ppe
Obad OTF800
Od
= M*2TO
ObZb WIP800
OT PBs
BIg
7009 81800
oa‘z#
A’ SATp
ZOO0DATS
PTP8OO
oad
=1°3x%e
OD8b
ZTP800
oad‘iq
= M*eaou
LOOE
OTP800
ON
WTbas
baq
WOL9 AOvsoo
&
zaqutad xtijyew-Jop m/q
uosdg
OdGLbS$
q°4sq
OGLbPOQOOSEVE
807800
La‘o0dbs
Ac SsT nw
D0AP000064dD 20800
La‘OTaES
=A AAO
DZACOOOOGERE OAEBOO
odzss
bq
9da40099 84200
ozdes
=
WM 4SQ
DZMECOOCELYE ZAE80O
ozaes’T#
At bqns
DZAEQOOOGLES DAEBOO
ZTdb$ ‘A$$
= SACU
TTAPOOOOMOOODUEE
bAEBOO
oaaps‘oqd
= T*ans
DGAPOOOO6GAT6 AGEBOO
oad
=
1°3x%e
08h
OaE8s00
Od‘Tt#
M°Tse
Obed vaEeBoO
oa‘s9Llbs
M*eacu
B9LPOOOOGEDE
PAESOO
DaE8S
abq
8109
zaesno
ZTab$
= MSA
TTAPOOOO6LVP ODE800
ZLdAbS‘T#
A bans
TIAVOOOO6LES 9D€800
397

<!-- source-page: 405 -->
## Page 405

86¢
008446
00844c
008450
008456
008458
00845E
008460
008466
008468
OO846E
008472
008474
008476
008478
00847C
O0847E
008486
008488
00848E
008492
008494
008496
008498
00849C
00849E
0084A4
0084A8
OO84AA
0084AC
427900004F88
60000450
4A39000047CE
675A
4A3900004ED8
6652
4A7900004F88
6616
2EBCO00016D5E
6100058E
4A40
6706
70FF
60000526
6034
0€79000100004F88
6616
2EBCO00016D63
6100056E
4A40
6706
TOFF
60000506
6014
2EBC00016D68
61000558
4A40
6706
TOFF
clr.w
bra
tst.b
beq
tst.b
bne
tst.w
bne
move,1
bsr
tst.w
beq
moveq.1
bra
bra
cmp.w
bne
move.1
bsr
tst.w
beq
moveg.1
bra
bra
move.1
bsr
tst.w
beq
moveq.1
S4F88
$889E
S47CE
$84B2
S4ED8
$84B2
$4F88
$847E
#S16D5E, (A7)
$89FE
DO
$847C
#-1,D0
$89A0
$84B2
#1,$4F88
$849F
#$16D63, (AT)
589FE
DO
$849C
#-1,D0
$89A0
$84B2
#$16D68, (A7)
$89FE
DO
$84B2
#-1,D0
ATARI
color
dot matrix printer
?
No
High resolution
?
Yes
ESC
'X'
6
Output
string
to
Error
?
No
Flag
for error
Error,
terminate
ESC
'X'
5
Output
string
to
Error
?
No
Flag
for error
Error,
terminate
ESC
'X'
3
Output
string
to
Error
?
No
Flag
for error
the printer
printer
printer
surysyqng ISI]
sjeusayuy ES Hey

<!-- source-page: 406 -->
## Page 406

66€
OO84AE
0084B2
0084B8
OO84BA
0084C0
0084C2
0084C8
0084cc
0084CE
0084D0
0084D2
0084D6
0084DC
0084DE
0084E0
0084E4
0084E6
0084E8
OO84EA
OO84EE
O08 4F4
0084F6
OO84F8
O084FC
OO84FE
008500
008502
008506
600004F0
4A39000047D0
6708
2EBCOO016D6D
6006
2EBCO0016D71
61000534
4A40
6706
7OFF
600004CC
103900003E86
4880
3E80
610004C8
4A40
6706
TOFF
600004B4
103300003E88
4880
3E80
610004B0
4A40
6706
TOFF
6000049C
13FCOQOO0100004ERA
bra
$89A0
tst.b
$47D0
beq
$84C2
move.1
#516D6D, (A7)
bra
$84C8
move.1
#$16D71, (A7)
bsr
S89FE
tst.w
DO
beq
$84D6
moveq.1
#-1,D0
bra
$89A0
move.b
$3E86,D0
ext.w
DO
move.w
DO, (A7)
bsr
S$89AA
tst.w
DO
beq
$84EE
moveg.1
#-1,D0
bra
$89A0
move.b
$3E88,D0
ext.w
DO
move.w
DO, (A7)}
bsr
S89AA
tst.w
DO
beq
$8506
moveq.1
#-1,D0
bra
$89A0
move.b
#1,S4EEA
Error,
terminate
Epson
B/W dot-matrix printer?
No
ESC
'L',
Bit
image
960 points/line
esc
'Y¥',
Bit
image
960 points/line
Output
string
to printer
Error
?
No
Flag
for error
Error,
terminate
Get byte
Low byte
of
the number
On
stack
Output
Error
?
No
Flag
for error
Error terminate
Get
byte
High byte
of
the number
On
stack
Output
Error
?
No
Flag
for error
Error,
terminate
Burystqng SA,
speuiojuy TS Wey

<!-- source-page: 407 -->
## Page 407

OOP
OO850E
008518
008522
008528
00852C
CO852E
008530
008532
008538
00853A
00853C
008540
008542
008544
008546
008548
00854A
008550
008554
008556
0O0855A
00855C
QO855E
008564
00856A
00856C
00856E
008570
008576
008578
OO857E
23F9000046B800004EDC move.1
33F9000047BCOO0004F12 move.w
4279000012E8
clr.w
6000034C
bra
4247
clr.w
600C
bra
3047
move .W
D1FC000047D4
add.l
4210
clr.b
5247
addq.w
BE7CO008
cmp.W
6DEE
bit
4247
clr.w
6010
bra
3047
move .wW
D1c8
add.1l
DIFCOO003E8A
add.1
30BC0007
move .W
5247
addq.w
BE7C0004
cmp.W
6DEA
bit
4240
clr.w
303900002608
move .W
9079000012EA
sub.w
4840
swap
4240
clr.w
4840
swap
80F 900004EE2
divu.w
6708
beq
303900004EE2
move .W
600E
bra
$46B8,S4EDC
$47BC, S4F12
$12E8
$8876
D7
$853C
D7,A0
#$47D4,A0
(AQ)
#1,D7
#8,D7
$8530
DT
$8556
D7,A0
AO, AO
#S3E8A,A0
#7, (AQ)
#1,D7
#4,D7
$8546
DO
$2608,D0
height .
$12EA,D0
Do
Do
DO
$4FE2,D0
$8580
$4EE2,D0
$858E
Burystqnd Si
speuszayuy LS Bey

<!-- source-page: 408 -->
## Page 408

Atari ST Internals
First Publishing
G6
sysew
d
ON
uotyntosez
YyStH
qubTey
od’ (ow)
ow ‘W197Z$
bI98s
VIdes
7798S
Baars
0os8s
90‘B89L6S
9a‘T#
aOdbS
qaL
bs ‘7H
WTa4es ‘od
0d ‘a0arS
od‘T#
oa‘1td
Ta‘Z1ab$
ta‘Gl#
od’ (OW)
OV ‘AALS
0468S
9d
AGLb$ ‘DE6HS
d0dps ‘T#
VI4ps
v698S
La
DEG PS {OGAPS
caps ‘0d
od ‘wats
oqa‘s09¢s
od
q* aaou
T° saou
baq
A'4s3
baq
gq°4s
4Tq
a* duo
a‘ bppe
A'Tse
T’bppe
M'ppe
A‘ syTnuw
M*pue
M*ise
a‘qns
T° bseacw
M*SAOU
T* aaou
BIg
M*ITO
T° Saou
M* SACU
M*ITO
PIG
M‘A3TO
T° eaou
M* BAOU
a‘qns
M* SACU
M°aTo
OTOT
VT9ZO0006L0Z
2019
VIAPOOOO6LVE
ccLgo
BACAPOOOOGEVD
80dg
89Lb00006LO"8
99¢S
q0dp00006dTaA
adl pooooedrs
VTd? 2000621
A0dPpO0006dTO
TOO00DLOD
09¢4
7TAPOOODELZE
AOL
OTOE
Gal bOOOdE
LO?
0£09
9bCb
AGL POOO0DE6 POOO0GAETS
AOFPOOCOOTOOODMEE
ULAvVOOO06LZE
84000009
LeCY
DES POOOODIGAPOOONGHEC
TAUAPVOOOOODEE
Va2TOO006L06
809 ZO00006E0E
Oh A
409800
809800
902800
009800
AdS800
819800
949800
04S800
dgqseoo
8aS800
7dS800
OGS800
9qS800
caS800
0dS800
YOSB00
895800
995800
095800
GdSsoo
985800
745800
VWS800
pYS800
owS800
d6S800
b6S800
4186800
88S800
c8S800
08S800
401

<!-- source-page: 409 -->
## Page 409

Atari ST Internal:
First Publishing
syseu
d
Tw’ (ty)
TW ‘OddES#
tw‘TW
Tw ‘Wades
OW
PAaLbS#
ow‘ OV
ow‘ id
(ov)
’ (TW)
TW‘W19Zz$
TW‘TW
Tw’ (TW)
Tw/Odaes#
TW‘TW
TW‘VTdes
OW‘ PAL est
ow ‘OV
ow‘d
(ow)
¢ (TW)
TW‘869DS#
Tw‘T¥
TW‘UTdbs
ov ‘veaEes#
ov ‘Ov
ow‘i.d
898s
(tw) ‘od
TW/DCLbS#
Tw‘id
oa
9198S
od
M°’ SAOUW
T'ppe
T*ppe
M° SACU
T*ppe
A‘ ppe
q’eaou
T*ppe
M'ppe
M° SAOU
T'ppe
T"ppe
M* SACU
T*ppe
M*ppe
M* SAOU
M*SA0U
T"ppe
T"ppe
M* OSAOU
T*ppe
T'ppe
M*SAOU
emg
q* aaou
T'ppe
m* sAoU
M*ITO
eiq
M‘4x9
TSZE
DFAPOOOOOTEC
60€d
UTAPOOOOSLZE
bd Po0000aTd
g90d
prac
Eve
T60T
VI9z00006dEd
60¢d
TSZE
OATPOOOOIAEG
60€d
VIFPOOOOGLCE
bd bo000DATd
890d
LVOE
T6Oe
869 PO00007Ed
60€d
VIAPOOOOGLZE
wsadeoo00oaTd
BO1d
LVOE
9909
OgseT
PaLvoooooOded
LUCE
ObCE
2009
O88P
819800
€L9800
049800
V99800
699800
299800
0396860
adS9800
859800
999800
6S9800
309800
309800
969860
069800
ae9800
9€9800
¥eg9Bo0
bE9800
Z£9800
229800
9¢9800
bc9800
€79800
029800
dT9800
819800
979800
#19800
cT9800
0Tt9800
402

<!-- source-page: 410 -->
## Page 410

tari ST Internals
‘irst Publishing
| —
SOR
é
uot yntosaz
yStH
ON
&
taqyutTid xtajzew-jop AOTOO
TewvLV
syseu
d
PPLES
B84b$ “TH
OSLES
OdabS ‘TSF
ag9es
od
od
oa‘zs#
od
od‘ (T'Tw’o0w)o
Tw‘weaes#
ov ‘OV
ow‘ia
0498S
B8adPs
Oaabs
O8L8$s
La
W8L8S
saars
W8L8S
AOLeS
pwses
La‘7aaps
La‘t#
2e6b$ “0d
oa
oa‘ t#
0a ‘9696S
(ow)
T4 (TW) T
Tw ‘Wl97zs
Tw ‘wv
auq
a*duo
Paq
q*aaoul
baq
A° ASQ
demas
M*SATD
T°
xe
M*SAOU
[T* eaaou
T"ppe
M*OAOU
auq
A*qSQ
q°aqto
eq
M°ITO
auq
q°4sy
baq
q°4s.
4TO
a‘ dud
M*bppe
T°ppe
T°axe
M‘Tse
M*SAOU
q*saou
T*ppe
M*ppe
Wp99
88APO000TO006LI0
9909
ORAPOOOOTOOODAET
8019
ODVE
OvSh
c000DdT8
0O8b
OOBGOEDE
V8AEQO00DLZE
goTd
LbOE
'299
88APO0006LYP
OdAbOOOOGE
CD
b5000009
LbCD
Pd000099
8daPOOOOGEUD
Aqddo000Lgo
SOLPOOOOGEWE
70410009
edd Pp00006
Lda
LbCS
26 po0odd6aTd
08h
Obed
969POO006E0E
TOOOTOOOG9TT
VT9c00006dEd
60¢d
849800
049800
ad9800
949800
pa9800
cd9800
049800
909800
¥a9800
909800
0da9800
499800
999800
W¥99800
BD9800
4Ad9 800
vd9800
8a39800
pa9 800
dAW9 800
VV9800
pW9800
ow9800
W69800
869800
769800
069800
489800
889800
289800
949800
¥L9800
403

<!-- source-page: 411 -->
## Page 411

Atari ST Internal:
First Publishing
ow ‘OW
ov ‘id
aALL8$
Oars
OmdapS ‘TSt
Dg.8$
(ow) ‘EF
ow’Vedes#
ov ‘OV
ov ‘id
DGLBS
odaps ‘TS#
ZHLBS
(OW) ‘LE
ov‘ VeaEes#
ov ‘ov
ow‘ia
VELBS
(OW) ‘94
ov vedes¢
ov ‘OV
ov‘ad
VELBS
(OV) ‘EF
ov ‘Weades#
ov’ov
ow ‘Ld
VWELBS
(OW) ‘c#
Ov ‘YBAES#
ow ‘ow
ov‘La
aA’ ppe
M* OAOU
baq
q° 4s
q* aaow
eTO
mM* duo
T’ppe
T’ppe
M*a@Aow
Pig
q* aaow
aug
mM*duwo
T
ppe
T’ppe
M* DAOQW
baq
a" dwo
T°ppe
T*ppe
M* aAoU
baq
M* duo
T° ppe
T’ppe
M* AOU
baq
m* duo
T’ppe
T’ppe
M* Q@AOW
good
LBOE
WIL9
OdDAPOOOOGEUD
OFAPOOOOTOOODAET
809
€0000S00
WBqEO00000RTA
BOTG
LVOE
8To9
OAAPOOOOTOOODAET
8099
£0000S90
WBsEOOOODATG
gotd
LbOE
OTL9
90000590
W8qde0000odTd
goTd
LPOE
O2L9
€0000S90
V8HEO00000RTd
goTd
LpOEe
OEL9
20000590
V8HE00000dTA
gold
LOE
994800
991800
791800
DSL800
§SL800
254800
AbL800
BbLB09
9PLBOO
bVLBOO
CLSOC
WELBOO
Beceoo
vELBOO
Ae€LBoo
O92L800
WEL8B00
82L800
¥CLB00
ATL800
OTL800
WIL800
8TL800
bTL800
dO0L800
201800
VOL800
802800
FOL800
449800
949800
W4i9800
404

<!-- source-page: 412 -->
## Page 412

SOP
008768
OO876E
008770
008772
008774
OO877A
OO877E
008780
008786
00878A
00878C
008790
008796
00879E
0O087A0
0087A2
0087A8
0O087AC
QO87AE
0087B0
0087B2
0087B4
0087B8
0087BE
0087C4
0087C6
0087CC
0087D2
0087D4
0087D8
0087DE
0087E0
DIFCOO00047D4
4210
3047
Docs
DiFfcoo00d4d7D4
42280001
5247
BE7900004ED2
6DOOFF36
7E04
60000086
4239000035BE
33FCO08000004F10
4246
603E
207C€000047D4
10306000
4880
7207
9247
E260
co7Cc0001
C1F900004F10
1239000035BE
D200
13C€1000035BE
303900004F10
48C0
81FC0002
33C000004F10
5246
BC7C0008
add.1
clr.b
move .W
add.w
add.l
clr.b
addq.w
cmp.w
blt
moveq.1
bra
elr.b
move .W
clr.w
bra
move .1
move .b
ext.w
moveq.1
sub.w
asr.w
and.w
muls.w
move.b
add.b
move .b
move .W
ext.1
divs.w
move .W
addq.w
cmp.wW
#$47D4,A0
(AO)
D7, A0
AQ, AO
#$47D4,A0
1(A0)
#1,D7
$4ED2,D7
S86BE
#4,D7
$8814
$35BE
#$80,$4F10
D6
$87E0
#547D4,A0
0(A0,D6.w)
, DO
DO
#7,D1
D7,D1
D1,DO
#$1,D0
$4F10,D0
$35BE,D1
DO,D1
Di, $35BE
$4F10,D0
DO
#$2,D0
DO, $4F10
#1,D6
#$8,D6
surysyqng send
sjewsayuy LS uery

<!-- source-page: 413 -->
## Page 413

907
0087E4
OO87E6
0087EC
OO87EE
0087F0
0087F4
0087F6
0087F8
OO87FA
0087FE
008804
008806
008808
00880A
00880C
008812
008814
00881A
00881C
O0881E
008822
008828
00882A
008830
008832
008838
00883A
00883C
008840
008842
008844
6DBC
1039000035BE
4880
3E80
610001B8
4A40
6706
TOFF
600001A4
4A3900004EEA
6704
4240
6002
7001
13COQ0004EEA
5247
303900004F0C
5840
BE40
6DOOFF70
4A39000047D0
6720
4A3900004EEA
4880
3E80
6100016C
4A40
6706
70FF
blt
$87A2
move.b
S$35BE,D0
ext .w
DO
move.w
D0, (A7)
bsr
S89AA
tst.w
DO
beq
S87FE
moveg.1
#-1,D0
bra
$89A0
tst.b
S4EEA
beq
$880A
clr.w
DO
bra
$880C
moveq.1
#1,D0
move.b
DO,S4EEA
addq.w
#1,D7
move.w
$4F0C,D0
addq.w
#4,D0
cmp.W
bOo,D7
bit
$8790
tst.b
$47D0
beg
S884A
tst.b
S4EEA
beq
$884A
move.b
$35BE,D0
ext.w
DO
move.w
DO, (A7)
bsr
$89AA
tst.w
DO
beq
$884A
moveq.1
#-1,D0
Output
Error,
terminate
Epson
B/W dot-matrix printer
?
No
Output
OK
?
Yes
Set
flag
speUlazU] LS Heyy
Surysyqnd Isa

<!-- source-page: 414 -->
## Page 414

Atari ST Internals
First Publishing
G
Huyoeds auTT y9TZ/T
‘T
1.€s
OSd
sax
é-uotTyantTosez
yBTH
ON
requtid xTijzew-jop
TOToOO
[YWLY
aqeuTwiay
/7021g
betz es
Sox
é
XO
qyndqno
wo
ayeuTwzey
‘1011
(LW) “SLA
TS#
OSbss
0d ‘88aPps
od’T#
passes
oda‘e#
zasss
saaes
z7a8es
AQLbS
B84b$ ‘TH
ovess
od’I-#
8688S
od
WW68$
(LW) ‘as#
2ZS8s
oa ‘ozaes
od’sazts
BATTS ‘TH
ZTAPS
oaaPrs ‘0G
od
oa‘ t#
0d‘89LPbs
OL88s
ZTAS ‘STH
ZTABS ‘TH
ow6B8s
T‘aaou
369
mM’ duo
T° baaow
Pig
T*baaou
auq
q° 3s
baq
q°4s3
a*bppe
eq
T° boaow
baq
A* ys
Isq
M* SAU
aTa
M* dud
M* SAQU
A*bppe
M‘ITO
T*ppe
T° 3x9
A'Tse
M‘aAOw
aT
M° dws
mM*bppe
eiq
GLA9 TOO0OdaZ
peds00d9
88AP00006L0E8
TOOL
2009
€00L
7099
SCAPOOOOGEVP
D0L9
ADL POOOOGEVP
B88APO0006LES
VOTOOOQYS
AMOL
90L9
OVP
atTtooolg
qooo0odue
BYII0009
972d€00006L048
BACTOOOOGEDE
B8ACTOOO0GLES
CTABOOOOGLZD
odapoo00edtd
0O8F
Oped
89LDOOOOGEDE
9TH9
Z7TAPOOOOAO006L00
CTAPOOOOGLZS
8sTa0009
Adssoo
Wads8soo
pdesoo
cadssoo
0a8s00
avsso0o
OV8800
9¥8800
yW8800
468800
868800
v68800
768800
068800
488800
V88800
988800
c88800
248800
948800
018800
¥98800
798800
798800
098800
¥S8800
858800
0S8800
Wps8so0
948800
407

<!-- source-page: 415 -->
## Page 415

807
0088C4
0088C8
0088CA
0088CC
0088CE
0088D2
0088D6
0088DA
o0gsBDC
OO88DE
008BE0
O0088E4
OO8S8EA
O088F0
O088F2
O088F4
OO88F6
OO88F8
O08 8FE
008902
008908
00890A
00890C
Nnoaant
VvosuL
008914
008918
00891A
00891C
OO891E
61000138
4A40
6706
TOFF
600000D0
3EBCOOOA
610000D2
4A40
6706
TOFF
600000BE
5279000047D2
4A3900004EE8
6704
7001
6002
7002
B079000047D2
6E0OFB46
4A3900004EE8
673E
4247
6028
2EBCOOOLSEDTA
610000E8
4A40
6706
JOFF
60000080
bsr
tst.w
beq
moveq.1
bra
move .W
bsr
tst.w
beq
moveq.1
bra
addq.w
tst.b
beq
moveq.1
bra
moveq.1
cmp.w
bgt
tst.b
beq
clr.w
bra
move.
bsr
tst.w
beq
moveq.1
bra
S$89FE
DO
$88D2
#-1,D0
$89A0
#SA, (A7)
S$89AA
DO
S88E4
#-1,D0
$89A0
#1,$47D2
S4EE8
S88F6
#1,D0
$88F8
#2,D0
$47D2,D0
$8446
$4EE8
$8948
D7
$8936
#S16D7A, (A7)
$89FE
DO
$8922
#-1,D0
$89A0
Output
string to printer
Set
flag
Error,
terminate
LF
Output
OK
?
Yes
Set
flag
Error,
terminate
Printer resolution
Printer resolution
ESC
'3'
1,
1/216"
line spacing
Output
string
to printer
Error
on
output
?
No
Set
flag
Error,
terminate
Surysyqng ISI]
yeuisuy TS Wey

<!-- source-page: 416 -->
## Page 416

Atari ST Internals
first Publishing
“
aqeuTwzey
/101TIg
ON
é
yndqno butanp 10129
qndqno
aT
aqyeuTwiey
‘10rITg
Betsy
29S
ON
é
yndqno butanp 10219
qaqutad
03
butTzqys
yndyno
butoeds auTT uZl/Ll
“111
OSA
ON
azequtad xtTajeu-jop M/d
uosdg
ayeutTwizay
410719
beTjJ
38s
ON
é
yndqno
butainp
19149
yndyno
a1
od
od’Tt#
od‘osaes
ov6ss
oa‘ t-#
8968S
od
WW68S
(LY) “WS#
ovess
od‘T-#
WS68S
od
34686
(LY) “ALd9TS#
qO068$
La‘oG
od’T#
bb6ss
oa ‘zt
chess
OdLb$s
La‘Tt#
ovess
Od ‘i-#
PE6BS
OG
VWV68S
(LW) “WS#
T°2xe
028%
A*TSse
Oped
M* SACU
OB8AEOOODSBLOE
eaiq
8e09
T' beaow
IAL
baq
POLS
M° 4S)
ObWD
AISq
WPT9
M* SA0U
WOOOODEHHE
Pig
9609
T° beaow
AdOL
beq
bOL9
M°384
ObWD
aisq
dAVOO000T9
T*eaow
4209 TO0QDEAS
aq
92a9
aM* duo
Opa
7° beaow
TOOL
Piq
Z009
T’ boaow
ZOOL
baq
bOL9
q°4s
OGLPOOOOGEWE
a" bope
LbCS
Pig
49000009
T' beaow
JAIOL
bag
3019
M'RS9Q
OWE
Asg
ZB8O0000TS
M* BAOU
VOOOQOEEE
0L6800
496800
8968C°C
996800
§96800
296800
0968C0
aG6800
¥S6800
856800
956800
bS6800
€S6800
Ab6800
8P6800
9b6800
776300
7V6800
066809
ae6800
3f6800
9€6800
bEEB00
QO fo
NOG
NAAM
Kx
MN ON
00
a
a)
Gas
3
390
on
N
OO
NN
HDnon
oO
ie)
409

<!-- source-page: 417 -->
## Page 417

Oly
008972 D1B9000046B8
008978
303900004EE2
O0897E D179000012EA
008984
4240
008986 303900002608
00898C BO79000012EA
008992
6200F8DC
008996 2EBCO0016D83
00899C
6160
00899E
4240
O089A0
4A9F
0089A2
4CDF30C0
O0089A6
4E5E
0O089A8
4E75
add.l
move.w
add.w
clr.w
move .W
cmp .W
bhi
move.1
bsr
clr.w
tst.l
movem.1
unlk
rts
DO, $46B8
$4EE2,
D0
DO,$12EA
DO
$2608,
D0
$12EA,D0
$8270
#$16D83, (A7)
S89FE
DO
(A7) +
(A7) +, D6-D7/A4~AS
A6
oT
rrr Teer rr errr re reel
e
ee See
eS ELS
SS Se oe
es
OO89AA 4E56FFFC
OOBSAE 4A39000025FR
0089B4
6722
0089B6
102E0009
0089BA 4880
0089BC 3E80
O089BE
102E0009
0089C2
4880
0089C4
3F00
0089C6 4EB9S0U008AZC
0089CC 548F
O089CE
4A40
0089D0
6604
0089D2
70OFF
O0838D4
6024
0089D6
6020
link
tst.b
beq
move .b
ext.w
move .W
move.b
ext .w
move .w
jsr
addq.1
tst.w
bne
moveq.1
bra
bra
AG, #-4
S25FE
$89D8
9(A6) ,DO
DO
DO, (A7)
9(A6) ,DO
DO
DO, -(A7)
$8A2C
#2,A7
DO
$89D6
#-1,D0
S89FA
$89F8
height
ESC
'2',
1/6"
line spacing
Output
string
to printer
Flag
for
OK
Restore registers
Output
a character
Printer port
RS232
?
Character
to output
Extend to word
On
the
stack
Character
to
output
Extend to word
And back
on
stack
(?)
Output
via Centronics port
Correct
stack pointer
OK
?
Yes
Flag
for
error
Done
Error-free termination
Surysyqnd ISI]
feuisj0gy LS Wey

<!-- source-page: 418 -->
## Page 418

Atari ST Internals
irst Publishing
AoyeoTpuT
pua
se
Jas
HuTays
Of
Taq\uTod
qAndyno
ayjeutwiay,
IOI
sox
é
3Ndgno
saerjy-A0j1g
ZayoRIeyO
yxau
oO]
AejuTod
zeyoerzeys
yadyno
Pp1OM
03
pUuayXY
qeqoereyo buyays
sseippe
butaqs
4a9
zaqutid
oj
buyaqs
yndqno
beTJ
z0IIe
49S
soz
é
WoO
ZeaqutTod
yoeRys
4oerI9D
ZET-SU
BTA yndyno
(é)
yoeqs
uo yoeq puy
P10M
0}
pusaIxXg”
andqno
03 7aVORPIeYD
yoeqs
uo puy
p10OM
0} puaqxXg
qyndyno
of
TayoRexreYyD
(OV)
“TAS #
ov‘ (9¥)8
Beves
oa‘t-¥
owes
od
(9) 8‘T#
ww6es
(LW) fod
od
oa’ (ow)
ow’ (9v)8
owes
p-# ‘OW
q'dwo
T*‘ aaow
e1q
T*' baaow
baq
a°ysy
T' bppe
asq
aayitel)
mM°4xa
q’aaow
T* aaow
e1q
XUTT
JANOOTIO
go00d90d
3009
RECA
bOL9
OOVY
8O000aVNES
W619
OBdEe
O88b
OTOT
80004902
8109
DAIAIIGAP
O¢cwsoo
OTWBOO
vTv800
8Tvso0
9TV800
PIY800
OTW800
aowsoo
90¥800
wovsoo
80V¥800
bowvs00
cowsoo0
446800
PeOCETT TCE
CEP PETE TET ECP
C CLES ee
eS SS
ee
ee Se
OW
od
VdI68$
od‘t-#
84685
oa
LY‘ CH
9PY8s
(LW)
~ ‘od
od
od‘ (9W)6
(Lv) “od
od
od’ (94) 6
si
yTUN
M°ITO
eiq
T' boaow
auq
ac ys
T' bppe
ais
M* 9AOU
A‘ Axa
q’ aaow
M’OAOU
M°3xa
q’ aaow
SLAP
acap
Obcy
z009
ddoe
b099
ObWD
AGES
9bWB800006ddy
O0de
088b
6000acOT
O8de
O88y
6goggdcot
946800
WiI6800
846800
946800
646800
f46800
046800
4136800
846800
946800
b4A6800
046800
306800
206800
806800
411

<!-- source-page: 419 -->
## Page 419

Atari ST Interna!
First Publishing
é
6T
uUPYyQ
18989815
Jequnu
voz joungy
AeLAe JALNOD
OF AS\UTO,
suofqouny
adWosad
IGA
siJayspTber
arojysay
zayutod
yoeqs
4991105
ZEZ-SU
PTA JaqoRzeYys
yndjno
SW 2P8TO
qadyno
of
rajoRPIeYUD
szaqjsjpTbar
anaes
ynd3no
07
Za qoerzPYD
qndyno
zezsu
SieqsTbaer
a10jseay
zaqujtod
yoeqs
39ae7I0D
qiod SOTUOTAUED
OF
ASQoORARYOS
Andjno
SW
2898TS
qandqno
03
29899e87eUD
siaysTbe1r
aaes
qndyno
of
7zaqoRPrPYD
qgndyno
softuorqusg
x40
ZaVoeeyYyoO
YX3N
9VW8S
Tuq
Oa‘Els#
a-duo
od‘ (oviot
M'aaow
ov‘ossz$
T° eacw
96729
€ TOODLOW
VOOO8ZOE
085700006102
d9vgo0
v9v800
99V800
o9vso00
ORO
OR
OR OR OOK OO
ROR
OR OR KR OR OR
sja
9VW-CW/LO-€qa’+(
(LV)
T° weaaow
LV‘b#
Mt bppe
aWo9s
asq
sv ‘swv
T’qns
(tW)-‘od
M'aaow
(Lv) -‘00
M*eAcU
(LW) -“9WV-EW/LG-Ed
T° weacu
oa’ (tv)9
mM*eaaocu
Glab
848 Ld09F
JAp8s
8Scd00T9
doe
oode
OO4e
STAT Lage
9000AZ0E
AGYBNO
Wsv8s00
8SV800
bSY800
eSvso0o
osvsgo0
abweoo
YPVs800
9bY800
FO
OO OOO ORR OR ROR OR OR ROR
OR LOR KORO ORR ORR KOE
EK
sya
OW-EW/LG-£0‘+
(LY)
T° waaou
Lv‘b#
aA bppe
pagos
isq
Gv ‘Sv
T’qns
(LW) -‘O0d
MA‘ aaow
(LW) -‘O0d
M*aaow
(LW) -‘9W-EV/Ld-€d T*weaow
odg‘(4¥)9
MM‘ eaow
Slap
848 LA09F
Apes
B6TAOOTS
dows
OOdE
Qoue
dTdIT lds ep
9000AZ0E
bewso00
opvso0d
aewso0o0
Vevso0
BEVBO0
9EVB00
pevedd
oevso0
o¢cV800
MOR
OR
OO
OO
LOE KOR
OR
ORK
sq1
OW
Tun
0G
M*AaTO
bouss
aug
Slab
asap
Ober
agg9
vevs0o0
8cV¥800
977800
bzvso0
412

<!-- source-page: 420 -->
## Page 420

ely
OQO8A72
307BO000A
move.w
S8A7E(PC,DO.w)
,A0O
Get
relative
address
from table
OO8A76 DIFCOOO08CTA
add.1
#S8C7A,A0
Add base address
QO8A7C
4EDO
jmp
(AO)
Execute routine
OO8ATE
0000
dc.w
S8C7TA-S8C7TA
0,
rts
QO8A80
FFD8
dc.w
$8C52-S8C7A
1,
Inquire addressable
alpha
character
cells
OOBA8B2
0012
de.w
$8C8C-S8C7TA
2,
Exit
alpha mode
0O08A84
O00C
de.w
S8C86-S8C7TA
3,
Enter alpha mode
QO8A86
OO1A
dc.w
$8C94-S8C7A
4,
Alpha cursor
up
0O08A88
002E
dc.w
$8CA8-S8CT7A
5,
Alpha cursor down
OO8A8A 0048
de.w
$8CC2-S8C7A
6,
Alpha cursor right
OO8A8C 0062
dc.w
S8CDC-S8C7A
7,
Alpha cursor
left
OO8A8E
0076
dc.w
S8CFO-S8C7A
8,
Home alpha cursor
008A90
OO7E
dc.w
S8CF8-S8C7A
9,
Erase
to
end
of
alpha
screen
OO8A92
OOAA
dc.w
$8D24-S8C7A
10,
Erase
to end
of
alpha text
line
008A94
0114
dc.w
S8D8E-S8C7A
11,
Direct
alpha cursor address
OO8A96
0128
.dc.w
$8DA2-S8C7A
12,
Output
cursor addressable alpha text
QO8A98
014E
dc.w
S8DC8-S8C7A
13,
Reverse video
on
OO8A9A
0158
dc.w
S8DD2-S8C7A
14,
Reverse video
off
OO8A9C
0162
dc.w
$8DDC-S8C7A
15,
Inquire current
alpha
cursor address
OOBAIE
018C
dc.w
S$8E06-S8C7A
16,
Inquire tablet
status
OO8AAO
0002
dc.w
$8C7C-S8C7A
17,
Hardcopy
OO8AA2
01A4
dc.w
S8E1E-S8C7A
18,
Place graphic cursor
at location
OO8AA4
01B4
dc.w
S8E2E-S8CTA
19,
Remove
last graphic cursor
FO
IO
IO
I
IO
IK ta
aR RK RK
KR CK
KR
eK
OOSAA6 BO7CO0ES
cmp.W
#101,D0
ESC VDI
101
?
OOBAAA 670A
beq
S8ABG
OOBAAC BO7TCO06E
cmp.W
#102,D0
ESC
VDI
102
?
OO8ABO 6700094F
beq
$9400
Yes,
initialize
font data
OO8AB4
4E75
rts
Surysyqng ysl,
sjeusojuy TS Wey

<!-- source-page: 421 -->
## Page 421

Atari ST Internal:
First Publishing
SLY
‘aroUubT
é
€T
ueyq reqVesi
SLY
/‘e10b6uL
é
L ueyy
ssoyt
saepod TYLD
sse00r1g
buTssasoid ogg
093
10 4DeA JNOUOD
SOpod THLO Jeyzo sseooid
‘ON
é
OSa
zayoezeyo
yjndyno
‘on
é
epoo
ToOrTqUCD
ynoucs pzepuejs
auTynor aynoexs puy
JOJOBA YNoUGD
4a5H
aqAq mot
ATuo
ssaeo0ig
yoeys wory
Tayoezeyo
485
qnouos
Zeqorzeyo
yndyno
aqdq mot
Atuo
sseo0rg
yoejs
worzy
ZeQoereYyo
4eD
4noose
aUTT
usez0s
ted
sajhAq
Jo
AJaquNnu
SoOWTL
szeqjewerzed
4a5
Xezie® NILNI
OF
29qUuTOd
jyo
zosing
TOl
OSH
TCA
azaes
36q
OTd9
OTA800
Ta‘9#
a* duo
90000L7EH 908800
azaes
Tug
czd9 YOUso0
Ta‘z.#
atbans
Teas 80a800
OR
ROE ORE LOR ORR OR OOOO OER OE
UR OER AAR
OR ROR ER OF
sii
SLab 908800
BVPS‘WPass#
T'eaow gvpOOOOOVPaB00000MEZ IDAVE00
goass
auq
2099 WAvs800
Ta’adis#
 q*duo
atoooeza 9aveo0
awo6s
ahq
vadso00n9
zdvs0o0
Ta‘ocs#
m*duo
OzZ00DLza AXY800
WEP
Tere TeTTeTEeererererrr
ts ts tes SS ES ST Se
ee
Odabr
O8VE800
B8YPOOOO06LOZ 9AVB00
Td ‘das #
M*pue
JI0OTHZO
CAV800
Ta‘(4W)9
M*eAow
900047@ZE€ Advso0
EEC TT SCT CTT CTT Pe CST eT EPEC eS eee LL
Se See
2 ee
ee
(ow)
auf
ow‘BY>S
T° eAcU
zqgoo0009 wawe0o
Ta‘ dds¢
M*pue
AJI00TPZO
9AVBOO
Ta‘ (4¥)9
M*aAoU
90004@7E
cdveod
OCrrr rrr Tere TCC CSTE CPP Eee. St
2s
tS ee SS
eS
aw06$
eaq
aqags
Big
ALpOOCOS ADWECO
qg¢z$‘oq
M*eaou
ASSZOOOOODEE
BOVBON
oad‘aLgzs
sat nT nw
ALSZOON06SOD ZOVBOO
oa’{(0Vv¥)
M°eAcw
OTO€
OOVE8OO
ow‘psc7s
T° eAow
78SZ00006L0¢
VHV800
0048S
ASG
BPPOCOTI
91VB00
a
a
ee
ee
eee
ee ee
414

<!-- source-page: 422 -->
## Page 422

Atari ST Internals
‘irst Publishing
iW.
aroubT
uayq
‘sseT
iW.
SNUTW
peirpurys
04
YOeq JOJOBA
YNnouCD
49q
leqye Tayoezeyo sseo0ig
Tosino
 jesay
aUTT
TOSsSanD
8 ppe puy
g
Aq aTqesTaATp
tequnu
oF
qTeAUCD
uuwnTods
1Osz0D
awd
Quo}
yndyno
14a
wo
‘ET
dd
‘21
LA
‘TI
aT
‘OT
aqvb
‘6
sd
‘8
Tad
’L
sapood
qTorqUoD
ios
eTqeq
dunce
auTynor HuTpuodsezi0D
|ByNndexKe Puy
3T
0} ssoippe eseq pPpy
aqTqe} woljy
sseiIppe
SAT ReTsrT 38
butTsseooid
pz0mM
OF butag
Ta/Os#
m* duo
D000DL7Za YSds800
azass
Tug
bade
ecagoo
Ta‘tes#
a" qns
TPOODLZE
FSA800
BVPS
aaves#
T° eaow gvpooodcomavs0000DME7 VhHd8O0
RARE OR OR OR OOOO
IO
RE ORE EEE
OR EF
69200009 9bd800
79SGZOOODGEZE OFA8OO
opos wedso0
owz6$
Pig
Ta‘z9cc$
|= M* SACU
oa‘s#
«a bppe
Od‘sddds#
MA pure
Bddd0bZ0 WEASOO
oq‘09Sz$
= M* aaoU
O9SZOOOO06EOE
VERBOO
ORR OOO
OOOO OOO
OR
EOE
RR
OE
EE EE
weags
Pig
B8TZa0009
O£A800
PPOPPTCCTE CO TOC TCC TIS ICL ICL
E LE
eS eee
ee eee
sa
GLab AZA800
SOOO
OOOO
OO
OR OREORR IORRR
HOE EEE EF
O€as8$-ToASs
M°Op
a6b0 978800
oedss-Vvadss
"Op
wvpo Wz7as00
ocass-wddss
a*op
wvro 8zds00
ocds$-Vd4es
mop
wvpo 97d800
ocass-redas
M*Op
bOOO
'cads800
oeass-Od08Bs
M*Op
OYTO
@¢2ds800
O€adss-Oedes
m*op
0000
O0c8800
POPCPPCTT TEC CCTOCET OOOO LOL S22 2
eee
odadb atasoo
O€d800000RTA BTABOO
VOOTELOE
PTA800
6pea CTAB0O
(ow)
dwt
ow‘ocass#
 T'PPe
ow’ {MA'Td‘dd)o0zaes
4° eAou
Ta‘t#
MIST
415

<!-- source-page: 423 -->
## Page 423

Atari ST Internal
First Publishing
auT NOT
|ay4noaexae puy
ssaippe aseq ppy
eTqej worly
sserppe asaTIeTeA
495
$9002 PIOM
JOZ
Z
SaWTQ apog
aspoieddn
osd
aouenbes
ssao0id
‘Tenbse
20
uPYyy
ssey
A,
1G,
@SPOT@MOT
a10UbT
JesJFFJO YORAAQNS
@SPOTAMOT 2S
JOT
ysey
Zosino
yas puy
piepueys 0 yoeq IO}OSeA YNoUCS
SUuTT PUY
anTeA uwnToo
qeszjo
yoerzqqns
RK
OSa reqye uwnjtoo
sseooig
UWNTOS
O3 1OJDS9A
4YNOUOD ssaD07g
eNnTeA SUTT
eAeS PUY
Jeszyo
yoeszqyqns
kh
OSH
JaqRje
SsutT{T
ssso00ig
Kk DSY
ACJ
JOYOSeA
YNnouocsd
S$19]1@T BsSeOTOMOT
AOJ
3893/ON
é
AOSAInd
4es
AOJ
ik,
SIOIT
TeqytTdeo
1ojJ
STQGeR
OSg
OL
(ow)
duf
Ow‘azass#
tT ppe
Od4ab
Sagd800
aAcads800000dTA 98a800
OW’ (M°TO‘Dd) 9008S
M*aAow
SSOTALOE
cddsoo
Ta‘T#
M°TST
60Ed
OFH8O0O
RKO RO
LO OO
ROO
OO OO
OR RO
aE
sqz
GLb avesco
aaass
eTq
OTA9 OVABOO
Ta‘GTS#
= am*duo
STOODLZA swasoo
azaes
quq
9849 9VE800
Ta‘tz7s#
sans
TZOO0OLZ6
Zwagoo
SER OR KOR ROR KOR
ER KOR OE ORR
OR ORE
EO
OR KOR OR RE OR OR
ROR ROR
RRR
owZ6$
Reig
20100009
a36a800
BVES‘ARWES#
T° PACU BYPOOOOOMAVB0000DTEZ
P6a800
Ta‘OWP$
9 M*eA0u
OVPOOOODGEZE ABasCO
od‘Iq
M*eaou
TOOE
28a800
Ta‘ozs#
s*qns
OZOODLZE 88800
DE
OE OR OR
RO ERO ORR
OR
OR OO OR
OER ORR OE
sya
GLA’ 988800
BVPS‘SBdsS#
T° SAW gyPpO00008BA80000IMEZ DLa800
OWes‘Td
mM‘ eaow
OVPOOOOOTSEE
9218800
Ta‘ozs#
s*qns
OZ00DLZ6
ZL8800
RR
OR ORK
RRR ROR
OR
OR OR ROR OR ORR ROO
OR OE OR OK OK
sya
SLA’
OL8800
BWPS‘ZLEBS#
T° PAOW BYPOOOOOTLEBODNODMEZ 994800
cvass
aug
D699
£98800
Ta‘sts#
M* dup
8TOODLZA
098800
odass
eTq
OS49
FSas800
416

<!-- source-page: 424 -->
## Page 424

Atari ST Internals
First Publishing
qa
Osa
dq
osa
3D Osa
a
osd
YW osd
aseo
azaddn
9Ssqy
10jJ
eTqeq ssaippy
ZJoTOo punozbyoeq
4as
qesjyjo yoerzqqns
JOJDeA YNoUCS prepue
AS
JOYVA YNouos
4asg
ZOTOO punorzbyoeq
Jes
oO OSE
AJOTOO
Jay,oeRITeYyoO as
qesyyo yorzqqns
IOJOISA BNOUCD peApueyAs
29S
JOJO@8A YNoucd
3esS
ZOTOO AejORIeYS
Yes
q OS
euTyANOAT
esynosxse
puy
ssouppe
eseq ppv
aTqey
worij
ssaippe
asAT ReTer
4eD
SSQDDP PIOM
AOJ
Z
SaWT I
apod
@SPOTSMOT
OSH
a7adss-aAzaes
m°Op
Z9T0
bTO800
aZass-Azdss
M*op
AYTO
2T9800
aZass$-AZdss
M*OD
b6TO OTO800
A2ass-AzZdss
M*Op
WLTO FOD800
aZaes~aAzass
a°op
99TO
9300800
AOE
LOR
OO
OREO
OE
OR OO
ORO
OE
OR EOE
OR
OR
OR EE
ALZ00009
809800
od‘Td
&*eaou
TOOE 909800
Ta‘O2$#
a°qns
OZ00DLZ6
2090800
SVPS‘aaAVaS#
T° SAOW BYPOOOOONAVB80000IME7 B4AB00
ROR
KOR ROR YOR ROE OE OR
OR OO
OR
OR ORE OR OE
OR LORE ORE ERE EE
eBaes
erg
si
SLab 948800
BYES ‘SAass#
T° saow gypooodOsddB0000DME? OadB00
OO
OR
LOR ORO
OR
OR OR
UR ORE
OE
OE ER
ROE
ER RO
76200009 8adB00
od‘tad
m*eaocu
TOOE 998800
Ta ‘o7s#
a’gqns
OZO0DLZ6
24800
BVPS‘ASVSS#
T'eaow gyPOOOOOaAWsO000DNEZ 8dds00
WOReTeTTCrTETEeTETTCPPTECTESICLEse
cree Le Le SS Se ESS eS
DLa8$
Pig
sya
Slap 908800
BWPS‘sdass#
T° eaow gyPOOOOOSdHB00000HEZ DD8800
Wrrrerere Terr TTT TCCTESTOCLOCT OCC SELLS TL LL Ee ES SST ee Se SS
Odgap wOaso00
AZHBO0O000DATA FOE800
ow’ (M°Td‘od)9zD8¢
8M eACU
PIOTELOE ODdB00
Ta‘T#
AM°TST
6bea aAgdsoo
PoCTE TTC CTO
Te TTC eT EC ECS
T CSTE CELE Lee
2
SS
eS
Se eS
(ow)
dul
ow‘azass#
 T'ppe
417

<!-- source-page: 425 -->
## Page 425

SIP
OO8C1E
008C18
OO8ClA
oo8scic
OO8C1E
008C20
008C22
008C24
ok
kk kok kkk kkk
kok kkk
doko doko
kok kkk kok kk kkk kkk kkk kK KK
008C26
008C28
O08C2A
008C2C
0O8C2E
008C30
008C32
008C34
008C36
008C38
008C3A
008C3C
008C3E
008C40
008C42
008C44
008C46
008C48
008C4A
oosc4c
008C4E
008C50
0000
0000
01C2
0306
O1CA
O1F6
0320
033E
OO09E
OOBE
0366
0382
03D2
0000
0000
0000
03F2
O40E
0428
0000
0000
0446
O29A
O2A4
0000
0000
0000
0000
048C
0496
een
ee EE
de.
de.
de.
dc
dc.
de.
de.
dc.
de.
dc.
dc.
dc.
dc.
dc
dec.
=
Ee
EES
KR
HE EEE
RE REE EE
$8B2E-S8B2E
S8B2E~S8B2E
S8B2E-S8B2E
$8B2E-S8B2E
S8B2E~S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-$8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
$8B2E-S8B2E
S$8B2E-S8B2E
S8B2E-S8B2E
S8B2E-S8B2E
S8B2E-S8B2E
S8B2E-S8B2E
S8B2E-S8B2E
S$8B2E-S8B2E
S8B2E-S8B2E
$8B2E-S8B2E
S8B2E-S8B2E
S8B2E-S8B2E
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
Address
table
for
ESC
lowercase
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
ESC
F,
G,
Ser
aH
b
“
.
Pw
e
FQ
hoa
goo
s
8
ct mW
a
u,
Vv
Ww
rts
rts
rts
rts
rts
rts
rts
rts
rts
rts
rts
Surysyqng Isiy
jeus9U, [S Wey

<!-- source-page: 426 -->
## Page 426

Atari ST Internals
First Publishing
Apeeite
suop
ueyQ
‘01987
BUTT
AOsanD
b
OSa
IGA
‘dn
azosind
‘W OSs
ugeios
Jo
4sezr
rPaTD
‘Pf
OSA
auoy
TOsinND
‘H
OSG
awoH AveTD
‘A Osa
jyo 3OsinD
‘J Osa
epow eydte
3txgd
‘2
OSA
IGA
uo
zosainp
‘e OSa
ewoH IPeTD
‘F OST
apow eydtTe
jequgq
‘€
OSH
IGA
qepxio
ut
yoeq youys
yng
Adoopiey
LT
oSad
IGA
ATnsezl
4ysAaTj
SV
S@UTT
Jo
Jequnu
stenbe
[
sntd
(pz)
@uTT
tosaino wunuTxeW
q[Nsez puooss
sy
suuntToo
jo Jequnu
stenbe
[
sntd
(6L)
uwnTos Zosins wnutxeW
Aexze
JNOLNI
0}
A9qUTO”d
SAaNnTeA Y[nsel
Z
Kearaze TLNOD
OF
AaeqAUTOg
azTs
UseIDS
qa6
‘T
OSa
IGA
WLOBS
bag
AGLI
WedHco
Ta‘zasz$
= w aAOUW
ZEGZOOOQGEZE
769800
FOR ROR
OL OOK
OR ORO
ORR
OR
OR ARR
OR OO
KORE ROR RE
BAD8$
erg
6909
¢62800
0dD8$
ASQ
AST9
069800
HOR OOO
SOR
ORE
OR EURO
OR SORE ER RR UR IORI
 EEE
oodgs
Asq
ZLZOOOTI
D8D800
PoPETeTETTCTCCT
CEST OLS LET Ee
ee ee eee ee
ee
odass
e1q
97700009
889800
0698$
ISq
80T9
985800
YORE OR OR OOOO OEE ORR
RIEU
UO AR
OR
OE EO
OE
Si.
GLa’
¥89800
LW‘tw#
T’bppe
86S 280800
DT#
dery
Apab 089800
(LV) ~‘bTS#
MM’ SAOU
PIOODEAE OLOBOO
PeCEEe PETS CECE TEESE TS Lee LL
ee eS Se
s qi
GLA’ VLO800
(ov) ‘OG
M°eAow
O80E 8L9800
oqa’T#
&‘bppe
ObZS 9L9800
oa‘zgszg) 0M BAO!
ZGSTOOONSEDE OL9800
(ov) z‘0qd
M*eacw
ZOOOOPTE 999800
oa‘T#
a bppe
OPeS ¥9D800
OSSZOOG06GEDE 799800
DBSZO0006LOZ ASD800
(ov) e8‘7#
MM OAOU
B000ZO00DLTE BS2800
ow‘oRszs
T*asow
O8BSZOO0N0GLOZ 259800
PPT CeTTECErTerrerrrer
eT ee. ta ts ts 2
2 te SS eee
ee
ee
od‘oss7s
9 M*eAcw
ow‘DeSscs
T° eAoU
419

<!-- source-page: 427 -->
## Page 427

Atari ST Internals
First Publishing
ZJOSINDS
4ss
O2J9Z
OF
SUTT
PUY
uWwnTod
8 OSH
IGA
‘awoH Josind
‘H Osa
ZTosino
3ag
@UTT
tTosand
auo
Aq Aueuar9q
~
or0z
Apeasrty
uWwNTOD Zosing
L OSH
IGA
4330T JosanD
‘Tad
‘d Osa
Josino
yes puy
OUTT
zOsano
4895
auo
Aq quowerouy
(6L)
ANTeA unutTxew YITA ezeduo)
uwnToo
Tosing
9
OSH
IGA
‘3USbTA
ZosanDd
‘D Osa
TOSAIND
4asg
uuntToo
zosang
euo
Aq
jZUueWarOUL
auop
‘auTT
4seMOT
UT ApeeiTy
aUTT TOsano unuTxew
oF oeteduoD
@UTT
zosing
S$
OSH
IGA
‘UMOp Josind
‘aq
Osa
zosino
jes
puy
uunTOo
ZJosino
.ayg
auo
4oRrAAqnNS
9dS00009
#40800
OOZE
€49800
O0OL
049800
Perre eee re rTere Te TES PPPS SCE
Le SS SSS
Se SS
ee
OVZ6S
Pig
ta’‘0q
M°*enow
od‘o#
T*beaou
DVZ6S
Pig
agsoo009
DAOKR00
Td’z9gz$
= M4 BAOW
ZIGZOOOOGEZE 940800
oa‘t#
a‘bqns
OPES
#PADB00
WLOSS
bag
96L9
7240800
oa’‘09Szs
=m" eAOW
O9GZO0D06EOE
2C0N800
PSCCErerreeeTerrTeTPEIPrrreCeLeLele
ss
ee eS SS ee
avz6$
eiq
ZdS00009
8dD800
Ta‘’z9c¢$
9M" aac
Z9SZO00006EZE
7ZdD800
oad‘T#
s'bppe
OPZS 009800
WLoss
baq
WWL9 AD2800
od‘osszs
s-*duo
OSSZOO0DE6LOA 8DD800
oad‘o9¢z$
Maaco
O9SZO0DD6EDE
7DD800
SOOT
rrr rT TTT Tere TCrrreer rere eee Le LS
2 StS SSS eS
owz6s
Big
DES00009 AAOsO0
oa‘o09Szs =" aac
O9SZTOOODBEDE
SAdDg00
Ta‘T#
M*bppe
Tp2S 980800
VWLOBS
beq
pOL9
paogsoo
Ta‘zsczs
m* duo
7SS7O0006LZA AVIBOO
Ta‘z9czs
=" eA0U
Z9GZOOD00GECE
BVYO800
ME RRR
OR KO
OR OR OR ORR KERR RO
OR RE ER
OvzZ6$
BIg
90900009
bYD800
od‘o9szs
= M*eaoU
O9GZOODDGEOE HOD800
Ta‘t#
m*bgns
TVES
3969800
420

<!-- source-page: 428 -->
## Page 428

a
uwnTOo TOSAino wnwyTxXeW
za‘ossz$
=" eAoU
OSSZOOD0GEFE 990800
=
za
dems
Zpebh b9d800
=
Tq
deus
Tb8b 790800
ev
za‘Ttq
#*eaow
Tore o9ag00
n
aUTT TosinD
ta‘z9gzs
9M saw
zaszoocoseze wSas00
=
Ta
dems
Lp8p gsagoo
=
uwnToo Josing
Ta‘09GzZg
-M* BAOU
o9gzo00o06eze z5a800
qndjno
avo6$
asq
3SEQOOT9 APaB00
aoeds
Ta‘ozs#
m*eaow
OZO0DEZE WHA800
eoeds yndqno
uaeyy
‘uwATOD
4seT
Ul
psass
beg
WEL
8baBs00
(6£)
anTea unwyTxew yyTM areduod
ta‘osszg
= av dwo
osszoo0o06.za za800
gsaes
baq
9TL9 0Fd800
Ta‘o#
qsaq
0000TO8O DEa8B00
!
uwNnTOo TOsAND
Ta‘o9¢z$
= MB" eAOU
o9szoooa6eze 9€a800
|
uotqtsod rosino eaes
‘f
Osa
ozass
asq
DETOOOTS ZEags0O
JjO Zosany
‘J Osa
0048$
asq
CatoooT9 azzaso00
@NTPA PTO eves
(L¥)-
‘YS  M* enou
La0b Oz7a800
MOTJIOAO BUTT TOZ
HheTy AwVeTD
9LGZ$‘e#
azqoq
9LSZ0000E000EN80 bzd800
OL
DSA
IGA
“@UTT
JO
4seT
APeTD
‘*¥ OSA
PEPerrerererreverrrrrrerrtiriri lilies
et eee See ee,
BST6$
Big
9€600009 0zd800
(6)
uwntoo zosino wnuTxeW
za‘oggz$ =M BAOW
OSSZOOQOO6EFE YTIAB00
za
dems
ZP8h 8Ta800
aUTT Zosano wnwyXeW
za’zggzg
|= A eAOU
ZSSZO0006EFE ZTAB00
Ta‘0#
= M*aAOU
ooooDEzE FTOABOO
Ta
dems
Trsb 900800
Be
Ta‘T#
mM‘ bppe
Tpzs wOdsoo
=
WLO8$
baq
ZLAZOOLY 900800
=
SUTT TOsino wnwTxew YyITM azedwod
Ta‘zggzg
=
M* duro
ZGSZOO006GLZH 000800
&
aUTT rtosang
Ta’z9czs
A" eAoU
Z9SZOO006EZE WADB0O
¥
BUTT
JO 4SeI VETO
‘HM OSE
pzdes
asq
WZI9 840800
=
6
IdA
‘UeeIDS
Jo
4ser
WeEeTD
‘fC
OST
POC PETETETECT OT TTT TT TTT TES TT ELS
Le See
ee
421

<!-- source-page: 429 -->
## Page 429

q
V
Atari ST Internal
First Publishing
gayoezeyo
}xeu
yndano
yoeq
sieqstbhoay
Td
uT
zaqyoereyo
ynd no
sleqstbexr
ar1oj4say
Td
03
ZJaqjuTod
4a5
Aerie
NILNI
0}
2ZequTog
szaqZoerrzeyo
jo
AT3squUunn
Aezze TALNOD
OF
As juTod
qnoyno
4xe]
“ZT
Osa IdA
JOSINoO
49s
qesjjo
snutwW
uwn[OD
485
qesyjo
snutW
aUuTT
2°89
Aezze
NILNI
03 JeqUTOg
zosino
yes
‘TT
OSG IGA
qndq4no
goeds
AOSAIND sTqeus-sy
uoTytsod rosind
32104s898y
‘y
OSd
qasoy
é
38S
JON
HeTy
e10489y
paass “0d
ow/0d‘+ (LW)
ZAVSS
(L¥)-‘ow/od
Ta‘+ (OW)
zoaes
ow‘ bseses
oa’ (ow)9
ow ‘oss7s
sji
eiqp
T*waaow
isq
T’*weaow
A‘ SAOU
eq
T* aaou
M* QAOU
T* aaou
GLab
Oddd BOTS
TOTOAGO
92dsd00T9
O808LH8p
BI Ce
aoo9
PESZOO006LOC
90008Z0E
O8SZ00006L0C
990800
290800
qFadaso0o
waasoo
9aq800
Padsoo
7adqs0o0
DV¥d800
svaso0
cvaso00
OKO OE
OR OO
OE OR ROR
OE
OR OE ORR RRR
EE
OF
Ovz6$
oa‘T#
oa‘ (ow)z
Td’t#
Ta’ (ov)
ow‘ psses
eq
a*bans
M*SAOU
a*baqns
M*aAOU
T° eaow
30500009
OvES
ZOOOBZOE
ThES
OTZE
P8SCOO006LOE
460800
36d800
860800
960800
b6d800
a28ds00
DER ER OER
UR
OR OR ORR AR RF OR OR
aE ROR AR OR
ROR IE ROR LOR
OR OR LOR OR OF OF
OLG8BS
aV06$
Ta‘O?S#
agag$
DEa8$s
OLSZ$ ‘EF
2La8$
woo
’+ (Ly)
Bgtes
e1gq
isq
M* BAU
Big
Isq
qesq
baq
M* SA0W
isq
caog
PcEQOOTS
OZOODECE
S9T00009
qddTOools
SLSGCOOOODED0064BO
8019
Aavey
waeo0ots
380800
g8aso00
b8d800
08a800
3La800
pLG800
cLaso0
OLG800
390800
422

<!-- source-page: 430 -->
## Page 430

Atari ST Internals
first Publishing
zosano
otTydeib
yas
sanTeA
3TNSer
ON
Aeazie
NILNI
©F ASqUTO”
eaTqetTeae
4eTQeL
Aezie
LNOLNI
23 qequtog
anTeA }INsel
V
Aezrie TYLNOD
OF
ASBqUTO”_
snjeqs
qyeTqe} aitnbul
‘91
OSA IGA
qInsei pucoes
sy
qeszyjo
sntd
uunToo
2oOsing
qINsez
3SATZ
sv
JeszsJo
sntd
eUTT
Josano
Aezae
INOLNI
©} Asqutog
sanTePA 4TNsel
Z
Aerie THLNOD
03 AaQuTog
uoTyTsod zosano
305
‘SGT
OSad
IGA
asieaaz
Joy
beTJ
2eaTS
PL
OSH
IGA
‘Jjo aszaaezl
‘b OSE
asiaaez
oj
SeTy
yas
EL
DSA
IdA
‘uo eszener
‘d Osa
OSAI00006AaP BZABOO
(OW) ‘0#
M*SAoU
OOOODHOE
¥Za800
ow’psSzs
T°" eaow
P8SZOO0006LOZ ATAB0O
TOCOTE STE SCT CEPT PELL
TPES ESL
Lee ee ee
ee
ee ee
osads
dul
s]1
SLOb OTABOO
(OW)
‘T#
M*eAoU
TOOODHOE
8Tasod
ow‘o8c7¢s
[T° eAow
D8SZ00006L0Z ZTAsco
(OV) 8’T#
M*eAow
B000TOOODLTE 204800
ov‘oss7s
T° esow
O8SZO0006L0Z 904800
SCTE
STS CSET TST EP eC PSP L ee Le Le eee ee
sql
GLEb bOa80O
(OW) Z’0d
=M*eAou
ZOOOOPTE 003800
oa‘t#
M‘bppe
Ores FAGsO0
oq‘o9gz$
9 =M*eAoW
O9SZOODO6EDE 8Ad800
(ov) ‘0d
M*eAou
oso0e 940800
oa‘T#
aM*bppe
Opes padsoo
ZISZOOOOGEOE FIGB0O
ow‘o8sz$
T° eAou
D8SZ00006L02
8aa8o00
(ow) 8‘Z#
M*eACU
BO0O0ZOODODLTE
z7aagoo
ov‘ossz$
T° eAouw
o8SZ00006LoOzZ
9daq800
CCT
ET ST SECS
TE TOTES
EC TLE TLL
2
ee
ee ee
od’z9gz¢s
9 M°aAoW
sya
Slap
wadaso0o
OLG7S ‘bt
ATOG
9LSTOGOOPOO0EEBO
7das00
eCeET SESE CeCe TESTE PTS
ee ee ee
ee ee ee ee
ee
ee
sya
Giab
010800
9LGtS ‘bE
Jasgq
945Z20000P0006480
850800
ORE ORR
KO
OR LOL OR OK
KORO
LORIE OE
OE
RE ORR
OR ROR
OE OEE
423

<!-- source-page: 431 -->
## Page 431

Atari ST Interna)
First Publishing
ZOTOO Jajoereyo aaes
GT°"O
‘9T
pow
ZoToo TaqjoRIeYo
4as
BACge
39S
dn
useios
jo
zepuTewery ATS
@UTT
z0sinD
JJO tosand
“J
Osa
BUTT TeeTD
‘W OSa
TOSIND
sTqeus—o2y
Iosino
.as
aUuTT
roSsiNng
QO
uwnToo
uT
Tosiand
UMOP UsaIOS
JO AspuTewsr
AITUS
auTT
Atosingd
yyjo
zosind
’j
Osa
eUuTT
Ylesul
“T OSa
Zosino as
O0198Z
O} BUTT
ZOsAnyD
uun{ToOo
ToOsino a10jsey
aUuTT
3zesUuT
“IT OSa
UUNTOS
TOSAINS
SAPS
dn
Josaino
uvey.
‘0
SUuTT
UT
JON
@UTT
Zosang
papesu
Jt
T[Tozos‘’dn
JosanD
‘I
Osa
Zosino oTydeib reaTD
‘6T
OSA
IGA
8SSz$ ‘Od
od‘ as#
oG48S
O8e6s
Ta‘z9s7zs
0048S
aayss
OVZ6$
Ta’z9cg7$s
od
BDE6S
Ta‘z9s7¢s
0048$
DWZ6$
Ta‘o#
oda‘+(L¥)
apaes
(L¥)-‘09S2$
2698$
Ta’z9sz$
BLdad$
sql
M° SACU
MA*pue
eg
aisq
M* 9AOU
Isq
eiq
Isq
M*aAow
M‘ITO
isq
AM‘ eAOU
Isq
Pig
T baaou
M*OAOU
isq
Mt eA0U
euq
MA‘ SAOU
dw
SLAP
8SGZO0000DEE
AO009L090
OW09
80S000T9
Z9GCOOD0GECE
c60000T9
b8000009
9PbOOOTS
f9SCONONGECE
OPch
A9SO000T9
CI9SZOOODGECE
OdOO00TI
09700009
00eL
ATOE
80193
OOSZOODDSEME
09440099
COGCOOD0GECE
BL4A400006da4
984800
084800
OL4800
OR
LLL
LOR OR
ROR YORE OR
OR
OR OL
OE URE OR OE OE
VL4800
914800
OLA800
994800
KE
OR
ROE OE
RR
OE
OR ROR ORO
ORE
OR RIE OF
894800
b94800
aASasoo
254800
8S4800
254800
avdsoo
RO
OR
ORO
OR
KOO
OO
OE KOO
OR ROE OK
Vvdasoo
8bPaA800
9b¥a800
bPa800
dea9800
VeEasoo
bea800
OK ORO
KORE OR
ORR ORO OR OKO
OR
OE
ORE RK EE
Azd800
ORK
RR
OO
RK KER
ROK
424

<!-- source-page: 432 -->
## Page 432

Atari ST Internals
first Publishing
uoT{Tsod Josino
ye
Je ,OeTeYyS
4AeAUT
uotytsod dosino
qe reqyoezeyo 4leau]
UuoTyTsod Josaino a\eTNoTeD
BUTT zZOsanD
uwnjToo
1O6saind
uo zosano
20Z
HeTd
auop
‘saz
~
uo Apearzjte
josingD
uo
zosind
‘8
oSsg
uWNTOS
ZOSZzNoO
WhUTXeYW
auop
‘orez
Apeerly
aUTT
rOSaNnyS
AJOSAND
O34 BUTT
APATO
‘oO
OST
ZJosino
oj ueatOs
A7eaTD
“Pp OS
AOTOO punorzbyoeq aaes
ST°°O
‘9T pow
ToOTOS punozbyorq
4asS
(OW) ‘7#
(OW) ‘T#
qOaes
aATe6s
8aAl6S
Ta‘z9c¢s
0a‘09S2S
(OW) *7#
cages
(OW) ‘O#
ow ‘9LG2S
e2bCS
7648S
Zebes
sa
qesq
qesq
Isq
emg
Isq
M* eAoU
M* anoul
esq
ouq
4s3q
PeT
M’°ITO
baq
M°4S)
SLab
70000080
TO000d80
vals
aEp00009
OTEOOOTYS
ZISZTOOOOGECE
O9SZOOOOGEDE
20000080
8199
00000T80
9LSZOOO006ATE
TERCOOOOE
LCE
WaL9
ZZHCOOOOGLYD
O8F800
Bada800
vadsood
7a4800
aqdas0o
vqasoo
'd4800
Aad800
YOU800
894800
bO4800
adasoo
8a2800
984800
084800
OR AOR
ROR OR LOR YOR OR OR OR ORR OE
ROR
ROE ROR
ROR OR OL
IE OF OE EF
BSTé6s
eig
10‘0#
T° baacu
Za’0SSzs
=" BAOW
rAGi
dems
za‘T#
Ms bqns
7648S
baq
za‘z9cc$
= M* AOU
bLASS
Asg
wWve00009
002@L
OSGCOOO0GEDE
cbep
TbES
74LO
ZISZTOOOOGEPE
adqgoao0tgs
OWAB00
vwas00
pWA800
cWd800
OWA800
464800
864800
p6a800
ECO CETTSCETT CT TPE TCS SS TT CPE
TLL Le
ee
9gSz$ ‘0d
od ‘as#
sya
M* OAOW
M’pue
SLAD
9SGSZQ00000EE
764800
384800
JOOQDLOD 88aA800
PEPEE EES SS
TSE
T ETE
T Le
EL. ee eS
ee eS ee ee
425

<!-- source-page: 433 -->
## Page 433

9¢P
Ok
kk ok kk ki koko
kok koko
ok kok
kok ok kok koko koko
kok kak
ok koe
OO8EERE
COBERS4
OO8ErG
OO8EFC
OO8EFE
4A7900002422
679C
537900002422
67C0
4E75
tst.w
$2422
beq
$8E92
subgq.w
#1,$2422
beq
S8EBE
rts
KR
KR Rk Kk KR OK kk kok kk kk kk OO
kkk kok ak kek
kkk kkk
OO8FO0
OO08F06
OO8FOC
0O8F10
OO8F12
OO8F1IE
COBFi8
OO8FIC
OO8FIE
ko
Ok kk koko
koko
kk kk kkokokok koko ok okokokok kok kok kok kok kok kkk
OC8F20
008F28
OO8F2E
O08F34
OO8F3A
Ce ee
ee ed
OO8F3C
OO8F44
OO8F48
OO8F4E
0O08F50
008F52
527900002422
41F 900002576
08900002
6780
08100006
67B6
08900001
66B0
4ET5
08F9000500002576
41F90000242E
30F 900002560
30B900002562
4E75
08B9000500002576
6700FDAA
41F90000242E
3018
3210
60000358
addq.w
#1,$2422
lea
$2576,A0
belr
#2, (AO)
beg
$8E92
btst
#0, (AO)
beg
S8ECE
belr
#1, (AQ)
bne
S8ECE
rts
bset
#5,$2576
lea
$242E,A0
move.w
$2560, (AQ)+
move.w
$2562, (AQ)
rts
RRA
KK RRR RK RK KKK RK KKK KKK KEKE KK KKKKKKKK
belr
#5,$2576
beq
$8CFO
lea
$242E,A0
move.w
(A0}+,D0
move.w
(A0),D1
bra
$92AC
Cursor
enabled
?
Yes,
rts
See
above
ESC
f,
Cursor
off
Flag
for
cursor
off
Clear
flag
for
cursor
Cursor
was
already
off,
rts
ESC
j,
Save cursor position
Flag
for cursor
saved
Address
of
the
temp.
storage
Cursor
column
Cursor
line
ESC
k,
Cursor
to
saved position
Was
cursor position
saved
?
No
Address
of
the temp.
stroage
Cursor column
Cursor
line
Set
cursor
Surysyqnd 31
jeurauy 1S ery

<!-- source-page: 434 -->
## Page 434

Atari ST Internals
First Publishing
aoeds
uo
yoeq Iosino
uiny puy
uoTjtsod Josino erojsey
‘4%
OSa
@UTT
ZOsaInyD
uwnTOO
ZOsINgO
andqno
goeds
suop
usyy
4/0797
uwnTos
zosinod
uotytsod
zosaino
aaes
‘Cf
Osa
Jyo
Zosino
uin,
‘J
Osa
IOSINO
Oj BUTT
azeeTD
‘oO
OST
oz98z
uwNToo
UT
Aasind
UWUNTOS
TOSTNO
wnwTxeW
eaUTT
JosiIND
Jjo
zosaino
uing
‘43
Osa
auTT seTEp
‘T
OSA
Td‘o2s#
aaaes
DEA8$
8S16$
Td
Id
za
ta‘za
2a‘29ces
za
ca‘7#
za‘o9Sz$
aAvO6S
Td ‘o7s#
9648S
7d ‘O¢
odass
2a ‘09GZ$
OzZA8$
o0a8$s
M* SAOUW
P1g
Isq
1Isq
M‘1aqto
deas
dems
A OAOW
M*OAOW
dems
a‘bqns
M* SACU
isq
M* OAOW
aBuq
qsaq-
baq
M* SACU
asq
aisq
OCOODE
CE
Ovadoos
o6t9
odToooTs
Tece
TbSP
chSh
cOCE
ZISTOOODGE
PE
CUS?
cuGS
O9STOOOOGEDE
7elooots
OCOODECE
OT99
00002080
OCL9
O9GZOOO0GEDE
BvT9
Veto
OHEBOU
DVA8O9
WVABOG
9VABOO
vWVA800
7WAB00
OVABO0
4164800
864800
96.1860
b6 4800
484800
V84g00
984800
bB4A800
0841800
ALABOO
8LA800
9LABC0
yLA8OO
OR
MO
OK ROR
OE
OR
ROR
OO
OE
oSg8$
estes
ea ‘oggzs
cd
Td
amel
za‘ta
Ta‘z9s7s
00d8$
Piq
Asq
M* SAOW
dems
M'ITO
dems
M* OAOU
M* SAOU
Aisq
Waad0009
VWatooots
OSSZOOOQOGEPE
CSD
Lecp
Thsy
TOPE
ZIGZCOOOOGECE
BYt9
OL4800
09 1800
99.4800
694800
294800
094800
a¢4800
BS4800
9941800
ORK OR OOO
OR
OR
OR
OR
OR OK
LOR OO KORE EIR
ORR RRR ROR
OF
427

<!-- source-page: 435 -->
## Page 435

Atari ST Internals
First Publishing
qajunos yseTy
ey}
jo sseippy
ON
é
bBuTyseTy
Josing
ON
é
uo
Iosing
piom
beTJ sy
jo
ssoippy
aosaino yseta
uo
yoreq Tosino urn puy
UMOp UseIOS
TTOI9S
JJo
ZOsind
uin,
‘3
Osa
umop Zosino
ysn{
‘awutT
}seMoT
UT
ION
aUTT tosin> wnwtTxeu y4TM ereduoD
aUTT
zosanD
umop zosind
‘(dd
‘LA)
‘dT
ATOSANd
439g
ol9zZ
O03 UWNTOD
aUTT
azosanyD
O1ez
uwNTOO
uT
JosaznD
’xYd
6e[y
APeto
aUTT
JO pus
Ye
SUTT
MoU
ON
‘M OST
Bets 4s
aUTT
JO
pus
Ve
SUTT
MON
“A
O80
and 4no
TW‘S9SZ$
Pat
G9SGZ000064Eb YO0600
7206$
baq
8IL9 800600
(ow) ‘O#
qasaq
COOCOT8O #00600
ZZ06$
baq
ATL9 700600
(OW) ‘Z#
4813q
ZOOOOT8O F44800
ow ‘9LSZ$
eaT
91GZ00006ATb 844800
ore eee eee ee eee eee Te eee Tee
ee
2
eS SS ee ee
agaes
eig
84240009
bad800
Ose6s
1sq
ABECOCOOTY 044800
Taq
-M°aTS
Tp2b Adi800
0048$
asq
vlddOOT9 Vad800
ewoes
auq
09940099 944800
oa‘’zsses
4° duo
ZSSZO0006L08 OAA800
oa’z9s7$
|=
BM aAOU
Z9GZOOODGEDE WAA800
Perrer rrr CT CETertrTrrerrerrert
lee Le tS SS SoS eS ee ee
bdazo0009 904800
od
MATS
Obcb
padsoo
Ta‘z9sgzv$
= M" BAOW
C9SZOOOOGEZE ADA800
Orne rer errr erererre ere ret Le te
Se
2S
SS
Te
Se
ee
de
DVZ6S
Big
sya
GLAb 204800
OLGZS ‘CH
ATO"
9LSZOOOOEOO06E8O
POABOO
PovCErCC Terre Pere rerrereer ere eh eee Le eS Se See ee
sqia
SLAv
cO4800
OLGZ$ ‘EH
qesq
9LSZONOCEQONGA8N
YAHAs00
SO
OR SOR KORE
OOK RRR OLR OR KOR OR ROR ER ROR AOR LOR IER OR CG OR ROR EF
wwass
RIG
0409
884800
av06$
Asq
840000T9
bdds800
428

<!-- source-page: 436 -->
## Page 436

Atari ST Internals
First Publishing
uo
zosaino
uinE,
‘38
OSa
T
yyo
zosaino
uin],
‘3
OSd
0)
sauT NOI ay
Jo ssorppy
uoTyOUNZ a4noexg
ssoippe
eaT eter
sntd
eaTqe} xy.
jo
sseippe
eseg
aztoubt
‘sax
é
G
uey. Jaqeer5
atloubt
‘eat eben
yoreqs
worjz
Aequnu
.4a5
IZ
‘ON SOIGX
‘UOT eANHTJZuos
ATOsANyD
jyo
zosaino
ulin]
aseud
zosanD
4x7eAUT
Zejunoo yseTy
proTterd
é
umop
unz
jad
ION
zayunod yuewer90q
odaes
eiq
09440009 4P0600
SRO SOKO
ORR OR
OR AOR
OR
OE OREO
OREO ER ER OE OR OER EOE EF
0048$
e1iq
paddoo09 WPO600
PEC CECT OCC TTT CTC CPT
ee LL.
ee eee ee ee
eel
WhO6S-9LOES
Wh06$-4906$
Wp06$-0906$
WP06S-Z2S06$
WhO6$-AP06S
WPO6S-WPO6S
m*op
9200
M*op
¥200
a°op
9T00
M*Op
8000
M*oOp
7000
M*OPp
0000
8p0600
90600
¥b0600
270600
0b0600
d£0600
PPePeTCCTT TET
CC TESOL
OSS SELL
Ee 2
2k
2
Se eS ee ee ee
(ov)
ow’ (M*°00‘Dd) HE06S
ov ‘woes
od‘ T#
2Z06$
od‘c#
ez06$
od’ (LY) P
duit
Odar
M*ppe
poood4od
eeT
WPO6O00006ATD
A‘yTse
Ores
bq
Cda9
ma‘ dus
SOO0DLOd
Fug
sda
M* 9AOU
pOOOdzZ0E
2€0600
ge€o600
c£0600
0£0600
470600
¥720600
820600
§ 20600
PPOCTCCC CCC CECE
TST LSE
ee eee eee
ee eee ee
qoass
(OW) ‘T#
(TW) 499S7$
ZZ06$
(TW) ‘TH
sya
GLAD
eiq
aVad0009
byog
TO0000S80
q°* saow
b9S7O0006GECT
auq
4099
q‘ bans
TIES
€20600
aAT0600
WTQ600
7T0600
eT0600
oT0600
429

<!-- source-page: 437 -->
## Page 437

OeP
FI II
RI
I
I FI IO
IOI IO
I II III I
III II III RO IE
I I ar
QO9052
6lLOOFEAC
bsr
$8F00
009056
OBEDO0002576
bset
#0,$2576{(A5)
O00905C
6000FE90
bra
S8EEE
FO
III
III
OI III II
OI
III III I IO II
I I
IK ae kk
CO9060
6LOOFESE
bsr
$S8F00
009064
O8AD00002576
belr
#0, $2576 (A5)
00906A 6000FE82
bra
S8EEE
dk
a
a aK
aK
RE KKK KK
KK
KKK RI KKK KE KKK
KK KKK KK KKK
O00906E 1B6F00072564
move.b
7(A7),$2564(A5)
009074
4E75
rts
KKK KK KKK KAKA
KKK KKK KKK KK
KR KKK aK KK AKRKRRK
R IK RA RK K
009076
7000
movegq.1
#0,D0
009078
102D2564
move.b
$2564 (A5),D0
00307C
4E75
rts
BORK
RK
IK
KK KK KEKE KKK KR EK KK KK
0O0907E 36390000256C
move.w
$256C,D3
009084
B243
cmp.W
D3,D1
009086
6522
bes
S90AA
009088 B2790000256A
cmp.w
$256A,D1
OO908E
621A
bhi
SSOAA
009030 207900002572
move.1
$2572,
A0
009096 D241
add.w
D1,D1
009098 32301000
move.w
(A0,D1.w),D1
00909C E649
lsr.w
#3,D1
00909E 207900002566
move.l1
$2566,A0
0090A4
DOC]
add.w
D1,A0
OO90A6G
4243
clr.w
D3
2
ESC
f,
Turn
cursor
off
Turn
cursor
back
on
3
ESC
f,
Turn
cursor
off
Turn
cursor
back
on
4
Set
cursor
flash
rate
Load
cursor
flash
rate
Calculate
font data
for
character
in
Di
Smallest ASCCI code
in
font
Compare
with character
to
output
Character
not
in
font
Largest
ASCII
code
in
font
Character
not
in
font
Load
font
offset pointer
Code times
two
Yields
bit
number
in
font
Divided by
8 yields byte number
Pointer
to
font data
Yields pointer
to data
for this character
Flag
for character
in
font
‘sjeuiajuy PS Wey
Surysyqnd ISN

<!-- source-page: 438 -->
## Page 438

Tey
0090A8
OO90AA
OOS0AC
4E75
7601
4E75
rts
moveg.1
#1,D3
rts
FFI
I
IO FOI
II
II I I
III
II IORI
III
II ICI I
dome
OO90AE
0030B0
0090B2
O090B4
O0090BA
0090C0
0090C2
0090C8
o090D0
0090DB2
0090D4
0090DC
OO90DE
0099E2
OOS0E8
OO90EE
OO090F4
OO90F8
OO90FA
009100
009102
009108
00910A
00910C
009112
009114
61CE
6702
4E7S
22790000255A
3£3900002556
4847
3E3900002558
0839000400002576
6702
4847
08B9000200002576
40E7
61000160
22790000255A
303900002560
323900002562
61000252
6732
303900002554
cocl
22790000044E
D3co
4240
B27900002552
640A
D2F900002554
bsr
beg
rts
move.1
move .wW
swap
move .W
btst
beq
swap
belr
move
.W
bsr
move.L
move .W
move .w
bsr
beq
move .w
mulu.w
move.1
add.1l
clr.w
cmp.W
bee
add.w
S907E
$90B4
$255A,Al
$2556,D7
D?
$2558,D7
#4,$2576
$90D4
D7
#2,$2576
SR,
-(A7)
$9240
$255A,Al
$2560,D0
$2562,D1
$9348
$912C
$2554,
D0
D1,DO
$44E,Al
DO, Al
DO
$2552,D1
$S911E
$2554,Al
Character
not present
in
font
ascout,
ignore
control
codes
Character present
in
font
?
Yes
Screen
address
of
the
character
Background color
In
upper word
Character color
in
lower word
Reverse turned
on
?
No
Exchange character
and background colors
Save
status
Calculate new position
Screen
address
Cursor
column
Cursor
line
Calculate relative
screen address
Number
of bytes per character
line
Address
of
the
screen
RAM
Compare with maximum cursor
line
Plus
number
of
bytes
per
character
line
Surysyqng 3st]
sjeuiaquy TS Ley

<!-- source-page: 439 -->
## Page 439

Atari ST Internals
First Publishing
aUT[
ueazos
red
sajkg
(p
TO
7’T)
seuetTd uasizos
jo requay
uoTyTsod Josind ayeTnoTeD
snqjejs o104say
SUTT
zosaNnD
uun{Too
7oOsanyD
ssoippe
ueeios
siaqjstber
azo say
SISASTH9r
SAPS
za
ta‘2q
ew‘ta
ZW‘ ALGZS
ta‘eq
Ta‘
T#
Ta‘zaq
ea‘
T#
ZLT6$
€a‘b#
eaq‘oLses
ca‘T#
B4T6$
ta
oa‘ta
za‘ta
9LS7S ‘7
OLSZS ‘TE
aTEe6$
9S16$
HOD
‘+ (LW)
z9szs ‘Td
o9szs$ “od
wss7$‘1w
T¥/Td-0d
‘+ (LW)
O8Ees
Ta ‘OF
(iv) - ‘T¥/Td-00
I2T6$
Ta‘ T#
dems
M*SA0U
M‘qns
M* Saou
M*TSe
M* bppe
M*SoAOU
m*bans
auq
m* duo
M* SAOU
A‘ise
Isq
dems
M* BAW
T*qns
sqz
Jesq
qesq
asq
baq
M* aAoU
M* SAOU
M*SAOW
T° aaow
T* weaaow
aisq
T° beaou
T*weaow
Reig
a bppe
cpad
cOcE
TOP6
ALSZOOOOGLEE
T9Lla
Tees
cOcE
EvES
2099
vOOOEBOO
DLSZOOOOGESE
coca
860000T9
Tbsp
TOOE
T8h6
GLab
9L92000020006480
9LSCO000TO006A80
WAaLOOOTS
BILLS
AGG?
Z9SCOODOTOEE
O9SZO0D00DEE
¥SSZO0006DES
€0720Ad
OP
WSZOO00TS9
OOcL
OFOOLA8E
3009
Tees
7BTE0O
08Té00
aLT600
8LT600
9LT600
bLT600
cLT600
OLT600
a9T600
W9T600
b2T600
c9T600
dST600
3ST600
¥ST600
8ST600
9ST600
apyteoo
9b1t600
cVTE00
061600
aET6OO
8ET600
ZET6OO
22T600
87T600
¥71600
e2T600
ATT600
DTT600
WTTE0O
432

<!-- source-page: 440 -->
## Page 440

Atari ST Internals
First Publishing
od
Ga‘t#
od
od
Gd’T#
sales ‘zd
Tw‘7wv
WaT6$ ‘Sa
+(TW) ‘EG
+(TW) ‘od
sa‘ta
eq
sa‘t#
eq
€a
ca‘t#
ed
od
Sa‘Tt#
od
od
sa‘t#
YWOT6sS
pales
STeAST
UseTDS
Jo
TEeqUNN
DLSZ$ ‘7H
IOTOO punoibyoerg
Ga‘9Sszs
od
ca‘ T#
qayorreyo
e
Jo 4bToy sowTy
cq‘aps7s
za‘t#
M* x6boau
Mise
dems
m*xbou
M°ISe
sqi
eiqp
T"ppe
eigqp
[T° aaow
T°’ aacwu
A*eaAoU
a*xbeu
a‘ise
dems
M*xdau
M‘1ise
T°aTo
m*xbou
A‘ise
dems
a*xbau
M'Ise
baq
TWO
a* duo
AM’ BAU
T°atTo
m*bqns
Ao npTnwy
M’bppe
ObOF
Sheu
Ob8F
ObOF
Gbéa
SLap
CHIAAWOTS
woed
Vdd dots
£022
0222
TOVE
€vOp
Stead
€v8b
Cbor
Sbdd
E8¢h
Ob0F
Sbcd
Ob8F
Ob0F
Sbea
8219
bva9
9LS7000020006L90
9SSZOOOOGEVE
O82b
CHES
aAvSZ000064bO
ches
cate00
odtedod
doT600
991600
VOT600
89T600
poteood
z9T600
qaTe0o
DAaT600
WET600
sat6o0
9dT600
pateoo
7aT600
odT600
avt600
OVT600
WvT600
BVT6E00
9¥T600
pwt600
ZYT600
OVT600
46 T600
96T600
061600
d8t600
28T600
98T600
b8T600
433

<!-- source-page: 441 -->
## Page 441

Atari ST Internals.
First Publishing
ANTPA WNWUTXeW
SoUTL
Gq 03 uuntoo
os
ga
zraquins
AocMWnin
sauPpTd uaal
anTeA wnUTXeW asn
osTY
&
JaTTeuws
eNnfea aUTT
eUTT
Zosaino umwtTxey
anTeA XBW asn
osTy
&
JaTTewus
anTea uwntos
uunjToo
27Osano wnwuTxeW
(Iag/0d)
uot3tsod
zosand ajeTNoTeD
ca‘t#
9226S
0a ‘0#
ea‘sa
Sa ‘OF
sa‘od
€a“SiSZs
ta‘edq
OTzZ6$
eq’ta
€a‘esc7s
oa‘ed
pOz6$
€q‘od
€a‘oS¢z$s
T’ bppe
baq
4s4q
anton
IToq
M*OAOUl
A’ SACU
M*SAOW
Tdq
mM‘ duo
M*aAOW
M*@AOU
tdq
mM? duo
M*eAOW
€8¢S
cOL9
00000080
$999
0000S880
OOovEe
DLSZOOOOEESE
€OcE
cOw9d
Tb9d
ZSSZOOOOGEDE
cOoe
cOwo
0p9d
OSGSCOO006E9E
922600
2¢2600
AT2600
2T2600
812600
9T2600
0T¢600
402600
902600
WOz600
602600
207600
002600
H4T600
84T600
RK
ROR
ROR
OE ERE
ORE EO
OR ROR
ORR
LOR
KOR OR OF
8a16$ ‘zd
tw ‘7@w
Wa16$ ‘Sd
+(Twv) ‘0G
sa‘ta
oa
Sa’
bal6$ ‘za
Tw ‘7v
gates ‘Sd
+(TW) ‘oa
cd‘ta
$yi
eigqp
T*ppe
eiqp
MA* SACU
M* DAOW
M*xbou
M°ise
sya
ezqp
T'ppe
eiqp
T° saow
M*SAOW
GLAD
pAdTAVOTS
woed
Ddd
Ad OTS
OOZ¢E
TOVE
OpOd
Sbed
SLAY
PddAVOTS
word
O4ddG9DTS
Qdc2
TOWe
94T600
ZAT600
0dT600
D4T600
WadT600
8aT600
94T600
palteood
7ATOOO
2zaT600
DaT600
8aTteoo
9aTteo0o
baT6d0
434

<!-- source-page: 442 -->
## Page 442

Sev
009226
00922C
00922E
009234
009236
009238
C0923E
009240
009246
00924C
009252
009254
00925A
00925C
00925E
009260
009262
009264
009268
CO926A
00926C
00926E
009270
009272
009274
009276
009278
00927C
003927E
009282
3A3900002554
CAC1
22790000044E
D3C5
D3C3
D2F90000255E
4E75
34790000256E
36790000257E
38390000254E
5344
3€390000257C
5346
3A04
2848
2A49
E287
C807000F
6706
642A
76FF
6004
6512
7600
1A83
DACB
S51CDFFFA
5449
SICEFFDC
4E75
move .w
mulu.w
move ,1
add.1
add.l
add.w
rts
move .w
move .W
move .W
subg.w
move .W
subq.w
move .w
move.1
move.1
asr.l
btst
beg
bcc
moveq.1
bra
bcs
moveq.1
move .b
add.w
dbra
addq.w
dbra
rts
$2554,D5
D1,D5
$44E,Al
D5,Al
D3,Al
$255E,Al
$256E,A2
$257E,A3
$254E,D4
#1,D4
$257C,D6
#1,D6
D4,D5
AO, A4
Al,A5
#1,D7
#15,D?7
$9270
$9296
#-1,D3
$9274
$9284
#0,D3
D3, (A5)
A3,A5
DS, $9274
#2,Al
D6, $925C
Number
of
bytes
per
character
line
Times
line
value
Base
address
of
the
screen
RAM
Plus
offset
for
line
Plus
offset
for
column
Plus
number
of
bytes
per
raster
line
formwidth
Bytes
per
screen
line
Height
of
a
character
Number
of
screen planes
Surystiqnd SIL]
s[eusaju] LS eV

<!-- source-page: 443 -->
## Page 443

Atari ST tnternal
First Publishing
saz
ZUOT ITSOd pToO
je paqyreAUT TsjOPIeYO
BeTy Josino
ayy
jo sserppy
aUuTT
Josino
aaes
UUNTOS Tosino eaes
anTeA wNuTxXeU
aesn
asTd
é ateTTews
anTeA wnuTxew YATM
aUuTT azedwod
anTeA uNnwTxew esn asTq
&
TeTTeus
ANTRA WUNWTXeU YITA UUNTOCO eiedwoD
zosino
39S
OA26$
(ov) ‘O#
ZTE6$
(OV) “z#
ow /9LS2$
c9Gz$ ‘Ta
é
nacze¢é
oq
Vea
ta‘ess7es
8976$
Ta’zsszs
oa’aogs7es
Va26$
oa‘oss¢$s
baq
33g
beq
4s 3¢
RoT
M* QA0OW
M*3A0U
sTq
M* duo
M* aAoU
stq
M* duo
VOL?
00000T80
ceLo
ZOO000TS8O
9LSTOOOO0GATY
Z9SZOOOOTOEE
og
ZSSTOQODGECE
90€9
ZSS700006L¢CE
OSSZOQOOGEOE
90t9
0SSZ00006L08
bAc600
04¢600
aqc600
vdz600
7ac6o0
a37600
807600
292600
0972600
vaz600
pacooo
ZEZ600
OVZ600
Orr
e
ee Tee Pee TPErrrreeP rere lee. ee ee Se SS See ee ee
3676$ 490
lw’7c#
96726$ ‘Sd
bw ‘2wv
Gv‘ev
(cw) ‘ed
ed
ea‘ (pw)
2676$ ‘90
Tw ‘t#
b8z6s ‘Sa
pw ‘cu
cv ‘ew
(Gv)
‘ (pw)
sqz
erqp
a’ bppe
eaqp
aA*ppe
M*ppe
q* aaou
q* you
q*eaow
sji
eadp
sa bppe
eigp
M*ppe
M*ppe
q* aaou
Slab
paAdADTS
60bS
PddddOTS
vosd
aqovd
eevt
£090
DIST
SLA’
WOITASTS
6b0S
B8ddA09TS
yosd
dowd
peu
¥wee00
9V2600
bWC600
oWZ600
467600
962600
V6 e600
86c600
9672600
62600
0672600
482600
VW8C600
88c600
98¢600
'87¢600
436

<!-- source-page: 444 -->
## Page 444

Atari ST Internals
‘irst Publishing
TaAeT usaIOS
4XOeN
SUTT Aeqsel
4XON
aUTT
JeyserT
4xXSu
OF TaqQUTOd
Jayoerzeyo ey
Jo euTT
Jeqjsez
e
4rTSAUT
qa oOPAeYO syy
Jo ssaippe
useai5s
S@UTT Zeqsez
AojJ
TejuNED
zejunos
eizqp
sv
soue[Td ueeros
Jo
rASequNN
zaqunoS
elqp
sv
aUT[
useaTas
eB
Jo
jYybTEH
aUTT
Ueaetos
Jed
seqAg
uoTtytTsod Zosano
je zejOeTeYyS
J1eAUT
uoTjtsod zosino
ey}
JO sseippe
use1oS
uoT3Tsod Josino Meu azeTNoTeD
PeRIBAUT
sft Ae_OPAPYS TOJ
Held
uoTyTsod Josino
qe
TeyJORITeYS
JLeAUT
IOSIND
ay}
Jo sserppe
useel0s
sSaippe JOSINO MEU aReTNOTeO
uoTytsod Joszno
ye
Ja ,OeTeYyo
AIeAUT
IosSAIno p[o
Jo ssaippe
useeIoS
PPE eTerrerrrrrerErrrrrer
el er ee
2 2S 2S 2
2k
peees 90
Tw /7t
geees ‘sd
pw/7w
(pW)
pw ‘TW
sa‘ea
9a‘T#
90‘OLSZ$
pa‘t#
pa‘apszs
ZW ‘ALGCS
$i
eaqp
a*bppe
eaqp
M*ppe
q* jou
T° aaow
M° SACU
a‘baqns
M*aAoUu
a* bans
M* aAou
M* Saou
GLav
Odd
dd OTS
6PbS
Wad
dd 1S
wosd
pl9b
6082
BOWE
9FES
DLSGZOOOOGEDE
PRES
AbSZOOOOGEBE
ALGZOQOOGLFE
9FE600
cveE0d
0FE600
2€€600
VWEE600
8EE600
9€€600
beeedo
Z€€600
27€600
V2E600
bZE600
ATE600
PoP CECE CET TCT CCL SLTOSCT LL ELE. SSS
SS
SS ee ee
wss7zs ‘TV
BAT6S
(ow) ‘2#
OLS7S$ ‘CH
aTe6s
wSG7e$ ‘TV
84T6$s
aTe6$
Tw‘wSoczs
FOES
(ow) ‘TH
(OW) ‘24
sqi
T°’ eacw
Isq
qesq
sqi
qesq
isq
T*‘aaou
Isq
Isq
T' eaow
beq
qsaq
Ijpoq
GLav
WSSZTOOO0B
IES
paadootg
7000080
SLab
9LS2000070006480
VI19
WSGZOO006DEC
HAaAOOT9
9cT9
WSSGCOOO0GLZE
a1L9
TOOOOT8O
70000680
2T€600
9TE600
ZTE600
A0€600
20€600
bOE€600
C0600
947600
842600
9472600
047600
497600
W4e600
947600
437

<!-- source-page: 445 -->
## Page 445

Atari ST internal
First Publishing
“BUTT
zeqoereyo ied seyAq
Jo
TequUnN
aUTT Josaino wnutTxeW
aUuTT
qyuezIND
AUTT PUR
JO SS@Ippe SPTETX
seuTT
go
zequnu
Aq ATdITITON
aUTT
Tej}OeARYyO red sazAq Jo
rTSequNN
WYY ueezos ey}
Jo ssezppy
IG ®UTT
}@ UMOP UseTDS TTOIIS
s[T@aaT
ueseros
Jo
TaequnNn
SOK
&
JOS MOTJTPAO
BUTT
AOZ
HeTA
uwnTOS
AOsiIno
wnuTxep
€q‘vGc7s
ta‘zgszs
sxe
ew‘ (mM ed‘ew) 0
ea‘tad
€q’bsscs
ev ‘apps
M° SACU
aA*ppe
M* Dau
eoT
ae ntow
M* DAOW
{T* eaou
DSSTOOOOGESE
fSS7Q0006L20
Toop
OOOEEALD
T9939
PSSZTOOO0GESE
ap POooo0cELgazd
Woeooo
76600
26£600
48600
28€600
98£600
08£600
CT eC TET TST CSTT ECS
C LOSSLESS
SS
SS
SS ee
ed
tw’ed
eq’
t#
ea‘ l#
€d/9L62$
ed
TW‘T#
OLE6S
0a ’0#
oa‘T#
ea‘t#
€qa
aSe6s
9LGTS ‘EF
Z9C6$
od ‘oss/¢s
$a
M°a4ToO
MA’ ppe
m*bqns
M’Tse
M° 3JAOU
$2
M*ITO
mM’ bppe
baq
4s4q
a’ bppe
sqz
T* boaow
sql
M°ATO
auq
483q
auq
m° dud
SLab
epcv
goed
cvES
eved
DLSZOOOOGESE
SLab
CbcP
67S
90L9
00000080
OCS
SLab
TO9L
SLAD
€bce
b099
9LGZOOOOEOO0GEBO
e199
0SSZ00006L08
ale6oo
DLE600
WLE6O0
8LE600
91L€600
OLE600
49€600
99€600
V9€600
89€600
b9t600
79€600
09€600
ase6o0o
oSt600
¥Ste00
8SE600
OSE600
adpeeo0d
87E600
438

<!-- source-page: 446 -->
## Page 446

6tV
0093A0
0093A4
0093A6
0093A8
0093AA
0093AC
0093B0
0093B6
0093B8
0093BA
0093BC
0093BE
0093C4
errr rrrcrrcrrrrrcrerre
eee See eee Se eS Se Se SE
SSP Se
0093C8
0093CE
0093D4
0093DA
0093DE
0093E4
009358
0093EA
0093EC
0093F2
0093F4
0093F6
0093F8
0093FA
0093FE
45F33000
cécl
E443
6002
26DA
SICBFFFC
323900002552
3401
4841
4842
4241
343900002550
6000FD92
26790000044E
363900002552
C6éF900002554
47F33000
363900002554
45F33000
3001
4440
DO7900002552
CcéCO
B443
6002
2523
SICBFFFC
60B6
lea
mulu.w
asr.w
bra
move.
dbra
move .W
move .W
swap
swap
c1lr.w
move .w
bra
move.
move
mulu.
lea
move.
lea
move
.W
neg.w
add.w
mulu.
asr.w
bra
move.
dbra
bra
1
oW
Ww
w
1
0(A3,D3.w)
,A2
bD1,D3
#2,D3
$93AC
(A2)+, (A3) +
D3, $93AA
$2552,D1
D1,D2
D1
D2
D1
$2550,D2
$9158
$44E,A3
$2552,D3
$2554,D3
(A3,D3.w)
,A3
$2554,D3
(A3,D3.w)
,A2
D1,D0
DO
$2552,D0
DO,D3
#2,D3
$93FA
-(A3),-(A2)
D3, $93F8
$93B6
Yields address
of
line
1
Number
of bytes
to move
Number
of
long words
Copy
screen
lines
Maximum cursor line
Maximum cursor column
Scroll
screen
at
line
D1
up
Address
of
the
screen
RAM
Maximum cursor
line
Mult
by number
of
bytes
per character
line
Yields
address
of
last
character line
Number
of bytes per
line
Yields address
of
line
1
Current
line
Add maximum cursor
line
Divide
by
4
for
long word transfer
Copy
screen
lines
Surysyqng Is,
sjeusayuy LS Leyy

<!-- source-page: 447 -->
## Page 447

Atari ST Internal
First Publishing
STGP
Jessjo
oF ASAUTOd
ezep
quozZ
Of
Tae\UTOg
quoj
UT
epoo
T[oOsy ysebzeT
quoj
uy epoo IIOsw yseTTews
quoj
ayy
Jo YIPTAM
‘YIpTAWIOJ
uuntToOo
rTosans
WHUTKeW
SPTSTA
[T
snutw
YUIPTM Jeqoezeyo wnuTxeu
Aq
epTtatd
sqTq ut Y3PTA useez0S
SUTT
ZOSINS wnwtxew
spTsTyx
snuTW
ayStey quoy
Aq eptata
uaerzos
ayy
VO
SeUTT
Jaqsezr
Jo
TSquinn
aUTT
Taqoezeyo
tad
saqkq
spTetA
Zeqoezreyo
jo
.wybtey
seutL
@UTT
ueezos
Jad
saqdg
usyIew
gejoereyo
e
jo
qubtsy
“qubteywioj
Jepeay yoy
ayy
jo
ssarzppy
Aezie®
NILNI
03
2equToOg
sioqeweied
quoj
eztTetatut
‘Zo tT OSH
IGA
ZLGZ$‘ (OW) ZL
99G2$4 (OW) 9L
w9Sz$’ (OW) BE
29GZ$‘ (OW) 9E
a9Gz$‘ (OW) 08
osszs/1a
ta‘T#
Td’ (ow) 2S
1a ‘OLGZ$
Ta ‘o#
2sszs ‘Ta
Ta‘T#
Ta‘oad
Ta‘BLSZ$
Td‘o¥¢
pSScs ‘Td
ta‘od
Ta‘aALSZ$
apszs ‘od
od‘ (OW) 28
ow‘ (OW)
ow‘ be8Szs
$4
T° eaow
T° eaow
M°SAOW
M° DAOU
M*OAOU
M* SAOUW
a*bans
M'NATP
M*SAOU
T* beaou
M* 3A0U
m‘bans
M°NATD
M*SOAOU
T° beaou
M*OAOW
sa apnw
M*OAOW
M*OAOW
M*OAOW
T° eaou
T*aaow
SLav
TLGZTOONOSPOOSAES
99SZ700009P008AE?
WISTOOOOICOOBSHEE
DIGZOOOOPZOOBHEE
AISCOOOONSOOBAEE
OSSZOOD0TOEE
TBES
beoosdcs
OLSZOOOQ0GEZE
OO0ZL
ZSGZOOOOTOEE
Tpes
0978
BLSCOOODGEZE
OO0cL
PSSZOO00TIEE
09¢)D
ALG ZOOO0GE
CE
APSTOOD00DEE
ZSO0B8COE
OS0¢
b8S7O000GL0C
496600
99600
aSb600
9S9b600
466600
9%600
OPb6E00
ae b600
Wereoo
PEb600
c£b600
926600
W2p600
8727600
eC b600
02b600
VTP600
81 b600
cT7600
207600
80b600
900600
00%600
FOE
LOR OE
OR OR OR OE OR
ORO
ROE OE OR
ROR KOR OR OR OR OR EOE OOK
440

<!-- source-page: 448 -->
## Page 448

Atari ST Internals
First Publishing
piepuejs
oj 10498A
yNoUOCD
uesei10s
IeeTD
SPp1IOM HUOT
0008
uO
ZoSinD
AoJ
beTz
yes
O€
OF BIST YSeTJ
AOSInD
O€
OF AaQUNOS YseTJ
A0sinoD
6ety
zosaino
4as
Zosino
ayj
Jo ssaippe uaeios
sy
WWY CAPTA ayy
Jo
Ssseappy
O198Z
BUTT
JoOsino
olez
uwntToo
zosino
SITYA
IJOTOO punorzbyoeq
AORTA
0}
TJOTOO Aaq\oPreyD
eyep 4uoy
azTTeTIATUL
quoj woysks
91[x%g ey}
jo ssaippy
ON
&
wuotyantosez
ybty
quoj waysks
gxg eu
jo ssoippy
uoTyNTosadl
alo soy
uOoT4NTOseZ ueios
AOJ
sisaqewered jas
UOTIANTOSeZ SARS
(uoTyNTosal ySTY)
Z
YRTM soPTday
ON
é€
T
pue
go
sitq aqeTost
uoTyNToser
ueerios
‘puqjtyss
qndqno
uvsertos
ezTeT ATUL
BS ‘AAV8S#
8PLA$ ‘Ta
+(ow) ‘od
Ta‘ deats#
T7H7S ‘TH
b9G7S$ ‘AIS#
S9SZ$‘ATS#
9LGZ$‘T#
WSSZ$ ‘OW
OV’ADHS
assz$ ‘od
z9Sz$ ‘0G
09S2$ ‘0d
9gSz$ ‘0d
od‘o#
BSG7$ ‘ddd dS Ft
B0r6$
ov‘9068T$
7419 4$
od‘z¢
OW
WWALTS
od’+ (2¥)
WSLd$
(LW) -‘0d
0a‘z#
gq9.a$
oa‘e#
oa‘e#
oa‘apbs
syi
[' aaow
eagqp
T*aaow
M*aAow
M*39A0U
q*aaouw
q*eaow
q*aaow
T° aaow
T° aaow
M*SAQU
M*OAOU
M*9A0U
M* SAU
T* beaou
M*OAOUW
isq
eaT
auq
4° dus
eoT
M* aAoU
1Isq
M*OAOW
M* SAOU
auq
m* duo
M*pue
q*‘aaow
SLAP
BYPOOO0ORTAT8O0000TEZ
DATAGOTS
0302
AEATIEZE
7CHZONOOTOQOOAEE
P9ISZOOO0TTOOIAET
S9GZO000ETOODIET
9LSZOOOOTOOODAET
WSSZO0008DEZ
ab PO00006L0Z
ASS ZOQ000DEE
79SZOOO00DEE
O09SZOO000DEE
9SSZOOOD0DDEE
OO0L
BSS 7O000FATAIOGEE
pTd600T9
9068 TOO0GHTE
9099
70000408
VWALTOOOGATP
dT0€
ALOOOOTS
OOdE
ZOOODEDE
b099
€0009L0E
€0009L09
OPPOOOOOGEOT
8SLA00
ApLA00
Woca400
8hL400
bDLAOO
9€LA00
pe Lj0od
92L400
¥2L400
aATLAo0o
8TLA00
ZLLAO0
90L100
904400
O00LA00
add9 100
949400
749400
049 400
Wdi3 400
949700
Od9T00
aqd9.400
was 400
gq9400
'd9 400
cd9 400
499 400
YO9A00
pO9 A100
FE
OR ROE
KO
ROR
LOR
ROE
KOR OR LOK
OR KORO ORR OR KOK OF
441

<!-- source-page: 449 -->
## Page 449

CoP
ROKK kk eK ek
KK KKK RK KKK KKK KKK KKK KEK KI
OOFTSA
OOFT5C
OOF760
OOF 766
OOF 76A
OOFT70
OOF776
OOF778
OOFT7C
OOF 782
OOF 786
OOF 78C
7200
123B0030
33C10000257C
123B0029
33C1L0000257E
33C10000257A
E340
323B001A
33€100002578
323B0016
33€100002570
4E75
moveq.l
#0,D1
move.
move.
move.
move.
move.
£e
vz
oO
asl.w
move.
move.
move,
move.
rts
Ww
Ww
Ww
Ww
SF78E(PC,DO,
D1,$257C
$F791 (PC,DO.
D1L,S257E
D1,$257A
#1,D0
$F794 (PC,DO.
D1,$2578
SF79A(PC,DO.
D1, $2570
w),D1
w),D1
w),D1
w),D1
RAK KK
KK KKK
KKK KKK KKK KKK KKK KKK KKK KK KK KEKE KEK
OOFT8E
OOF791
OOF 794
OOF 79A
040201
AOA050
00C800C80190
014002800280
dc.b
dc.b
dc.w
dc.w
4,2,1
160,160,
80
200,200,
400
320, 640, 640
Initialize
screen
output
DO
contains
screen
resolution
Get
And
Get
And
Get
And
Get
And
number
of
screen planes
save
bytes
per
screen
line
save
screen
height
save
screen height
save
Screen parameters
Number
of
screen planes
Bytes
per screen
line
Screen heights
Screen widths
Note: This BIOS listing contains some of the most important sections of TOS Version
1. Later versions of TOS may have some minor differences, but this listing should still
prove valuable.
Burysyqng Is1Ly
yeusayay LS Heyy

<!-- source-page: 450 -->
## Page 450

irst Publishing
Atari ST Internals
Chapter Four
Appendix
4.1
The System Fonts

<!-- source-page: 451 -->
## Page 451

First Publishing
Atari ST Interna

<!-- source-page: 452 -->
## Page 452

first Publishing
Atari ST Internals
1.1
8
The System Fonts
[he operating system contains three system fonts for character output.
The 6X6 font is used by the Icons, the 8X8 font is the standard font for
butput on the color monitor, and the 8X16 font is used for the monochrome
monitor output. The chart on the next page includes the characters with the
ASCH codes
1 to 255.
445

<!-- source-page: 453 -->
## Page 453

Atari ST Internal
First Publishing
|
8X16 System Font
—
8X8 System Font
6X6 System Font
uszut
=U30H990OLNOF#
JsvooY SLLOL LUALEXGMOCUCC OWE LULECK(L OOb., .OYYTDeGoe<1%%+-70
PSAAFINOhnngooyRIyY Tt t Lago seeeeanjv~{ | }ZAxmanyssbdouw Dyf tybgapaqe YY CV] ZAXMANLSYD
scent tw Nw
Rweeiesw
S Asewes os
dONWTNPIH9SIOIQUOE <=>! SGSZISGHEZTOZ
= '4H0) BKSHui
ae 7 SEEBUISHES OAS Arto
HE tUS
ee XEN FTF
=UJO $HUGSLMOTMIgXvGA LOL LUMLERGMTOTULCs MULEULE CNAME:
,..
ALYY PBS HCE!
HKt4 7GENUOS!
22
SSPAFINOHIN
COOP RVY EL
EVTISSS
CLS PNG T~
C1) ZAXMANISIDAOUWT
Hy 6ry6seaprge wy (NI ZAXMANLSYO
dOWNW INC LHDABAIAVDE
<=>
£ EBLISHLTTGZ *— (FHC) BASRA:
REC SEGSLISHES! CWk
lf HOA
OOO
meet roete FITS
FUZSOFSTVSCLWHTALSP
OV FA LSLIVALERGHAAUCURCLAULIUELE ERA
wOORs
.
SRY DPSTIE ASIN ITOENUDGS
SFAARFPNDSEQOSOSMSAFHLILSSSTETETEMSYN CEPTAXMAN DS UDGOUWT
NE TUGs PP IAG. ~VENIZAKMANLSAD
AONHAINCITHOATODSVDE
CEL SESLISVEZIOS*
—- SHR OD CBKS Hai
AKCINCHTLISIEZTA VEU
COCKE DE TE
446

<!-- source-page: 454 -->
## Page 454

The Anatomy of the Atari ST
. This Anatomy volume is
a welcome addition to any ST programmer'slibrary.
Inside you'll find important hardware and programming information for your ST.
Contains valuable information for the professional programmer and ST novice.
Here is a shortlist of some of the things you can expect to read about
@ 68000 processor
@ Custom chips
@ WD.1772 disk controller
@ MFP 68901
@ ACIAS6850_.
@ YM-2149 sound generator
@ Centronics interface
@ RS-232
@ MIDI-interface
@ DMAcontroller
e@ GEMDOS
e@ BIOS &XBIOS
@ Interrupt instructions
@ Error codes
@ BlOS listing
x
Aboutthe authors:
:
The authors, Klaus Gerits, Lothar Englisch and Rolf Bruckmann, are all part of
the experienced Data Becker Product Development Team, based in
Dusseldorf, W. Germany. They are all best selling computer book authors and
very knowledgeable concerning the subjects presented in this book
Other books in series:
A Data Becker
First Atari ST Book
Book from
Tips & Tricks on the Atari ST
GEMontheAtari
First Publishing
Limited
FIRST PUBLISHING ITD
