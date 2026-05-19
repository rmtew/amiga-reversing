<!-- source-pdf: resources/platform_atari_st/docs/The_Concise_Atari_ST_68K_Prog_Ref_Guide.pdf -->
<!-- source-pages: 405 -->

<!-- source-page: 3 -->
## Page 3

The Concise Atari ST Reference Guide
The Concise
Atari ST
Reference Guide

<!-- source-page: 4 -->
## Page 4

The Concise Atari ST Reference Guide

<!-- source-page: 5 -->
## Page 5

The Concise Atari ST Reference Guide
THE
CONCISE
ATARI
ST
REFERENCE
GUIDE
by
K.D. Peel
Glentop Press Ltd

<!-- source-page: 6 -->
## Page 6

The Concise Atari ST Reference Guide
JANUARY 1988
All programs in this book have been written expressly to illustrate specific
teaching points. They are not warranted as being suitable for any particular
application. Every care has been taken in the writing and presentation of this
bookbut no responsibility is assumed by the author or publishers for any errors
or omissions contained herein.
Copyright
© Glentop Press Ltd 1986
World rights reserved
No part of this publication may be copied, transmitted or stored in a retrieval
system or reproduced in any way including but not limited to photography,
photocopy, magnetic or other recording means, without prior permission from
the publishers, with the exception of material entered and executed on a
computer system for the readers own use.
First printed
August 1986
Revised and reprinted
May 1987
Fully revised and reprinted
January 1988
ISBN 1 85181 172 9
Published by:
Glentop Press Ltd
Standfast House
Bath Place
High Street
Barnet
Herts
EN5 5XE
TEL: 01-441-4130
Written using Wordstar, diagrams GEMDRAWand typeset from Ventura
Printed in Great Britain by Bell and Bain Ltd., Glasgow

<!-- source-page: 7 -->
## Page 7

The Concise Atari ST Reference Guide
CONTENTS
Preface
Acknowledgements
Chapter 1 - Atari ST Hardware
Atari ST block diagram
1.2
General hardware description
1.3
Main system & device subsystem diagram
1.4
Atari ST console I/O
1.6
Monitor/TV output
1.6
Monochrome monitor
1.6
Colour monitor
1.6
Television
1.6
Monitor output
1.7
Parallel printer interface
1.8
RS232 modem interface
1.9
RS232signal levels
1.9
Floppy disk controller interface
1.10
Direct memory access port (DMA)
1.11
Command modes
1.11
Musical instruments digital interface (MIDI)
1.13
Midi signal levels
1.13
Plug-incartridgeport
1.14
Intelligent keyboard I/O (ikbd)
1.15
Mouse/joystick interface
1.16
PortO
1.16
Portl
1.16
Power supply
1.17
Power levels
1.17
Processor device outlines
1.18
MC68000 16-bit microprocessor (CPU)
1.19
WD1772A floppy disk controller (FDC)
1.21
FDC instruction bytes
1.21

<!-- source-page: 8 -->
## Page 8

The Concise Atari ST Reference Guide
MK68901 multi-function processor (MFP)
1.23
MFP hardware interrupts
1.24
MFP configuration registers
1.24
MC6850 asynchronous communications interface
adaptor (ACIA) 1.27
ACIA control/status register
1.28
YM2149programmable sound generator (PSG)
1.29
Direct memory access controller (DMA)
1.30
Memory management unit (MMU)
1.30
Video controller (Shifter)
1.31
General housekeeping (Glue)
1.31
Chapter 2 - THE OPERATING SYSTEM (TOS) OVERVIEW
Operatingsystemoverview
2.3
Basicinput/output system (BIOS)
GEM BIOS
2.4
2.4
XBIOS
2.4
Line-A routines
2.4
Basic disk operating system (BDOS)
2.4
Virtual device interface (VDI)
2.4
Application environment services (AES)
2.5
Application programs
2.5
Memory allocations
2.6
Memory map
2.6
System tables
2.7
Configuration registers
2.8
Resource mangement overview
2.9
CPU resources
2.9
Graphics concept overview
2.10
Overview of screens
2.12
High resolution screen
2.12
Medium resolution screen
2.12
Low resolution screen
2.12
Color palette table
2.13
Physical to logical screen transposition
2.13
High resolution screen
2.13
Medium resolution screen
2.14
Low resolution screen
2.14
Colour generation
2.15
Colour changing
2.15
Animation
2.15
VI

<!-- source-page: 9 -->
## Page 9

The Concise Atari ST Reference Guide
Sound concept overview
2.16
Sound control register
2.16
Parallel data I/O
2.17
Sound configuration registers
2.18
Tone frequency calculations
2.18
Noisefrequency calculations
2.18
Envelope calculations
2.19
Shape
2.19
Period/cycle
2.19
GEM disk operating system (GEMDOS)
2.20
Memory model
2.21
Base page
2.21
CP/M 68K format
2.22
File header format
2.22
Symbol table
2.23
Relocation table
2.23
ST file system
2.25
ST disk system
2.26
ST BIOS comparisons
2.27
Interrupt handler overview
2.27
System initialization
2.28
Cartridge software
2.31
Boot sectors
2.32
Boot loader
2.34
Boot ROM
2.35
Implemented functions
2.35
Peripheral device communications
2.36
Communications overview
2.36
RS232 interface
2.37
Parallel port interface
2.38
Midi interface
2.39
Control/status register functions
2.40
Intelligent keyboard interface
2.41
Keyboard
2.41
Mouse
2.41
Joystick
2.41
clock/program control
2.42
Floppy disk interface
2.43
Formatting a floppy disk
2.44
WD 1772A DMA channel interface
2.45
DMA interface
2.47
DMA bus boot code
2.48
Hard disk partitioning
2.50
VII

<!-- source-page: 10 -->
## Page 10

The Concise Atari ST Reference Guide
Chapter 3 - The ATARI Operating System
General
3.2
Register usage
3.2
Traps
3.3
Trap #13 access
3.3
BIOScalls (trap #13)
3.3
Critical interrupt handlers
3.6
Trap #14 access
3.7
XBIOS calls (trap #14)
3.7
Trap #1 access
3.15
GEMDOS calls (trap #1)
3.15
Supervisor/user toggle
3.23
Test for mode
3.23
User to supervisor mode
3.23
Supervisor to user mode
Extended BDOScalls (trap #2)
3.23
3.24
GEM VDI access
3.24
GEM AES access
3.24
Interrupt Handler (VBI)
3.26
Chapter 4 - GEM VDI
GEM VDI function calls
4.2
VDI parameter blocks
4.3
Control table
4.3
Attribute table
4.4
Points table
4.4
Parameter block sizes
4.5
The GEM VDI calls
4.8
Workstation function calls
4.8
Output functions
4.10
General drawing primitives
4.11
Attribute functions
4.13
Raster operations
4.16
Input functions
4.18
implemented
4.18
not implemented
4.20
Inquire functions
4.22
VDI style patterns
VDI text alignment
4.26
4.46
Escape functions
4.27
implemented
4.27
not implemented
4.30
VIM

<!-- source-page: 11 -->
## Page 11

The Concise Atari ST Reference Guide
File formats
4.33
Bit image
4.33
File header
4.33
Data encoding
4.33
Meta file Sub Op codes
4.35
Output page
4.35
GEM draw
4.36
Chapter 5 - GEM AES
GEM AES function calls
5.2
General
5.2
AES parameter block
5.3
Control table
5.3
Global array
5.3
Typical AES application call
5.4
Handles and coordinates
5.4
AES parameter block sizes
5.5
GEM AES components
5.5
The GEM AES Libraries
5.6
Application library
5.6
Event library
5.8
Keystroke selection
5.11
Icon selection
5.11
Menu library
Menu bar control
5.12
5.13
Object library
5.14
Object tree
5.14
Object library tables
5.15
Font types
5.16
Colour fields
5.16
Form library
5.20
Edit keys
5.21
Alerts
5.22
Graphic library
5.24
Scrap library
5.27
Fileselector library
5.28
Window library
5.29
Window parts bit representation
5.30
Resource library
5.35
Data structure types
5.36
Shell library
5.37
IX

<!-- source-page: 12 -->
## Page 12

The Concise Atari ST Reference Guide
Chapter 6 - The IKBD commands
General
6.2
Keycodes
6.2
Data packets
6.2
Commands
6.3
. Reset
6.3
Set mouse button action
6.3
Set mouse relative position reporting
6.3
Set mouse absolute positioning
6.3
Set mouse keycode mode
6.3
Set mouse threshold
6.3
Set mouse scale
6.3
Interrogate mouse position
6.3
Load mouse position
6.4
Sey y base position
6.4
Set y base position at top
6.4
Resume
6.4
Disable mouse
6.4
Pause output
6.4
Set joystick event reporting
6.4
Set joystick interrogation mode
6.4
Joystick interrogation
6.4
Set joystick monitoring
6.4
Set fire button
6.4
Set joystick keycode mode
6.5
Disable joysticks
6.5
Set time of day clock
6.5
Interrogate time of day clock
6.5
Memory load
6.5
Memory read
6.6
Controller execute
6.6
Status inquiries
6.6
Data packet functions
6.7

<!-- source-page: 13 -->
## Page 13

The Concise Atari ST Reference Guide
Chapter 7 - The Line-A calls
General
7.2
Line-A access
7.2
Initialization pointers
7.2
The Line-A routines
7.3
Put pixel
7.3
Get pixel
7.3
Line
7.3
Horizontal line
7.3
Filled rectangle
7.4
Line-by-line filled polygon
7.4
Bitblt
7.5
Textblt
7.5
Show mouse
7.5
Hide mouse
7.5
Transform mouse
7.6
Undraw sprite
7.6
Draw sprite
7.6
Copy raster
7.6
Contour fill
7.6
Logic table
7.6
Line-A parameter blocks
7.7
Sprite definition block
7.7
Format flag
7.7
Memory definition block
7.7
Line-A parameter table
7.8
Bitblt table
7.10
Chapter 8 - The Blitter calls
General
8.2
Blitter operation
8.2
Clipping
8.2
Skew
8.2
Endmasks
8.2
Overlap
8.2
Blitter control/status
8.3
HOG bit
8.3
BUSY bit
8.3
Blitter access
8.3
Blitter flow diagram
8.4
Blitter parameter table
8.6
XI

<!-- source-page: 14 -->
## Page 14

Xii
The Concise Atari ST Reference Guide
APPENDICES
A
System variables
Exception vectors
A.2
Hardware bound interrupts
A.3
Application interrupts
A.3
Error processor state dump
A.3
System variables
A.4
Bomb error codes
A.6
B
Configuration registers
Memory
B.2
Display
B.2
DMA/disk
B.3
Sound
B.4
Blitter
B.5
MK68901
B.6
MC6850
B.6
C
Printer and terminal escape codes
C.2
Typical Epson printer codes
C.4
VT52 terminal escape codes
C.5
D
Keycode definitions
D.2
ASCII codes
D.3
GSX compatible keyscan codes
D.4
VDI standard keyboard codes
D.5
Keyboard codes
D.7
E
Callable functions
E.2
BIOSTrap #13
E.2
XBIOSTrap #14
E.2
GEMDOS Trap #1
E.4
Extended BDOS Trap #2
E.5
GEM VDI
E.6
GEM AES
E.9
IKBD command set
E.12
Line-A routines
E.13
F
Parameter blocks
F.2
System start-up block
F.2
Device drivers
F.3
Device state block
F.3
Program parameter blocks
F.5

<!-- source-page: 15 -->
## Page 15

The Concise Atari ST Reference Guide
VDI parameter block
F.7
AES parameter block
F.8
Line-A tables
F.9
Sprite definition block
F.12
Header blocks
F.13
Cartridge header block
F.13
Application header block
F.13
G
MC68000 instruction summary
G.2
Address modes
G.21
Allowable address mode types
G.22
Data storage
G.23
Data types
G.24
H
MC68000 instruction codes
H.2
Bit manipulation, move peripheral,
H.4
immediate instructions
Move byte instruction
H.5
Move longword instruction
H.5
Move word instruction
H.5
Miscellaneous instructions
H.6
Add Quick, subtract quick, set conditionally H.7
and decrement instructions
Branch conditionally instructions
H.8
Conditional tests
H.8
Move quick instructions
H.9
OR, divide and subtract decimal instructions H.9
Subtract and subtract extended instructions
H.9
Emulation instruction (Line-A)
H.10
Compare, exclusive OR instructions
H.10
AND, multiply, add decimal, exchange
H.ll
instructions
Add, add extended instructions
H.ll
Shift/rotate instructions
H.12
Emulation instruction (Line-F)
H.13
Address mode encoding
H.14
I
Error codes
1.2
BIOS error codes
1.2
BDOS error codes
1.3
Miscellaneous error codes
1.4
XIII

<!-- source-page: 16 -->
## Page 16

The Concise Atari ST Reference Guide
J
BASIC GEM
J-2
GEMSYS
J2
VDISYS
J-2
SYSTAB
J-2
BASIC assembler
J.6
Hand coding
J.7
K
Program development tools
K.2
Atari MC68000 assemblers
K.2
Seka
K.2
Hisoft
K.4
GST
K.5
Metacomco
K.6
Digital Research
K.7
General assembler compatibility
K.9
Assembler directives compatibility
K.10
Assembler conversions
K.11
Calling procedures
K.14
C compilers
K.16
L
Example programs
L.2
GEM
L.3
Application and accessory header file
GEM demonstration program
L.3
L.8
GEM demonstration assembly program
L.9
TOS
L.17
Display demonstration program
TOS header file
L.17
L.19
Character printing program
L.20
Sound demonstration program
L.22
Line-A
L.26
Line-A parameter table
L.26
Sprite demonstration
L.28
M
Glossary
M.2
N
Schematic diagrams
N.2
ST schematic diagram
N.2
ROM cartridge
N.4
Index
XIV

<!-- source-page: 17 -->
## Page 17

The Concise Atari ST Reference Guide
PREFACE
This book is intended as a compact reference guide to the Atari ST range of
computers, it provides detailed information on the Atari ST hardware, an
overview of the operating systems and the operating system calls. It also covers
all types of machine including the Megas and blitters as well as the three
generations of operating system used in the ST's todate:
a)
OS supplied on disk
b)
TOS in ROM
c)
'New TOS' in ROM
The majority of the book has been prepared in both decimal and hexadecimal
notation to make reading and data entry less complicated for the beginner, and
those who wish to use the VDI and AES tables from BASIC. I hope the use of
decimal will not be too distressful to the purists, but most assemblers will accept
either format as an input. The diagramatic presentation of data in memory and of
stacks follows the Motorola MC68000 user's manual format of low memory
towards the
top
of the
page;
presentation of memory maps follows
the
convention of high
memory towards the
top
of the
page.
All memory
representations are annotated to avoid confusion.
The Atari ST range of computers contain one of the largest ROM's (192K) of
the current range of home/low cost business computers available. This offers an
enormous wealth of data and routines that the user may wish to access; about six
times that of most computers. This information is presented in a condensed
group tabular form to provide association between the different types of calls
available, and to get it all in. General descriptions of all the facilities available
(disk, file, interfaces etc) are provided to present the reader with at least an
outline understanding of their operation.
The book covers the programming of the Atari ST in three parts:
Chapter 1 gives an overview of the Atari ST hardware and expansion ports,
also included is a short description of the peripheral interface circuits.
Chapter 2 presents an overview of the operating systems, the management of
memory and resources, control of serial I/O, screen functions and file handling.
The following chapters provide the operating system calls for the Atari OS,
GEM, the
line-A graphic
functions, the
intelligent
keyboard
command
instructions and the blitter.
The Appendices contain the system variables, configuration registers and a
summary of the MC68000 instruction set.
XV

<!-- source-page: 18 -->
## Page 18

The Concise Atari ST Reference Guide
Acknowledgements
The author wishes to thank Atari Corp. (UK) Limited for its assistance in the
preparation of this book by providing much of the technical data, which is
reproduced with the kind permission of Atari Corp. (UK) Limited.
The contents of the Atari STROM are the copyright of Atari Corp.
Atari STand TOSare the trademarks of Atari Corp.
CP/M and CP/M 68K are the registeredtrademarksof Digital Research Inc.
GEMand GEMDesktop are trademarks of Digital Research Inc.
MS is a trademark of Microsoft Corporation.
IBM is a registered trademark of International Business Machines
Corporation.
Epson is a trademark of Epson Corporation.
Motorola is a registered trademark of Motorola Inc.
Metacomco is a trademark of Tenchstar Ltd.
GSTis a trademark of GSTHoldings Ltd.
Kseka is a trademark of Andelos Software 1985
Devpak is a trademark of Hisoft Ltd.
Disclaimer
Neither Atari nor the author make any representation or warranty with
respect to the contents hereof and specifically disclaims any implied warranties of
merchantability or fitness for any particular purpose. No responsibility for the
use of the information contained hereto, nor for any infringements of patents or
other rights of third parties which result from such use shall be assumed.
XVI

<!-- source-page: 19 -->
## Page 19

The Concise Atari ST Reference Guide
Foreword
by JackTramiel
When we introduced the ST series of computers at Atari, we coined the
phrase 'Power without the Price'. This sums up all that had been in our minds
when we decided to design a range of powerful but low-cost machines that could
be used for all applications ranging from sophisticated games to complex
business and scientific uses.
During the past few years, ever since I was responsible for bringing the first
mass-produced electronic calculators and then the first true computers to the
public at an affordable price, my whole aim has been to bring the benefits of
technology to thoseofaverage income. Wehave to get high technology out ofthe
hands of the few into the hands of the many. As I have said before we want
'classes forthemasses'. Ifyougive somebody some sophisticated machinery then
you'll be surprised what they can do with it. Time and again we have been
amazed at what users have done with the technology when it is made freely
available at an affordable price.
And that bringsme on to this series ofbooks, edited by my old acquaintance
Robin Bradbeer. It is impossible to give all the information necessary to
completely cover all the uses of a computer in the instruction manual. Also, if
more than one person explains something they bring out differing strengths of
the system. Thisseries ofbooks should help all usersof the ST to get to know the
machinebetter and therefore use it more productively. Who knows, we at Atari
may yet again be surprised by what you, the user, can do with the affordable
technology that we have provided.
JackTramiel
1986
XVII

<!-- source-page: 20 -->
## Page 20

The Concise Atari ST Reference Guide
XVIII

<!-- source-page: 21 -->
## Page 21

The Atari ST Hardware
Chapter 1
Atari ST Hardware
Atari ST block diagram
1.2
Generalhardware description
Main system & device subsystem diagram
1.3
1.4
Atari ST console I/O
1.6
Monitor/TV output
1.6
Monochrome monitor
1.6
Colour monitor
1.6
Television
1.6
Monitor output
1.7
Parallel printer interface
1.8
RS232 modem interface
1.9
RS232 signal levels
1.9
Floppy disk controller interface
1.10
Direct memory access port (DMA)
1.11
Command modes
1.11
Musical instruments digital interface (MIDI)
1.13
Midi signal levels
1.13
Plug-in cartridge port
Intelligent keyboard I/O (ikbd)
1.14
1.15
Mouse/joystick interface
1.16
PortO
1.16
Portl
1.16
Power supply
1.17
Power levels
1.17
Processor device outlines
1.18
MC6800016-bit microprocessor (CPU)
1.19
WD1772A floppy disk controller (FDC)
1.21
FDC instruction bytes
1.21
MK68901 multi-function processor (MFP)
1.23
MFP hardware interrupts
1.24
MFP configuration registers
1.24
MC6850 asynchronous communications interface
adaptor (ACIA)
1.27
ACIA control/status register
1.28
YM2149programmable sound generator (PSG)
1.29
Direct memory access controller (DMA)
1.30
Memory management unit (MMU)
1.30
Video controller (Shifter)
1.31
General housekeeping (Glue)
1.31
1.1

<!-- source-page: 22 -->
## Page 22

The Concise Atari ST Reference Guide
Atari ST Block Diagram
MC 68000
MPU
Control Logic
1.2
Memory
Controller
Buffer
ACIA
MC685tf
ACIA
MC685fj
MFP
MC689(lt
PSG
YM21'49
FDC
WD1 772A
DMA Interfase
ROM
Cartridge ROM
192K
RAM
51
to 4Mbyte
2r^
Video Shifttr
R£B Analogue
—- Monochrme
(Modulator)
J Keyboard
Interface
RS232
Interfacfe
Parallel
Interface
Sound
Channel
Floppy dish:
Interface'
Hard disk
Interface?
Keyboard
,
Input
MIDI lnterfa^e_
Output
-
Modem
Printer
Audio
Floppy disk
Hard disk

<!-- source-page: 23 -->
## Page 23

The Atari ST Hardware
General Hardware Description
The Atari STcomputer system consists of a consoleunit featuring an integral
keyboard, a display screen, sound subsystem, peripheral input/output and an
operating system. Expansion ports are provided for the connection of a variety of
peripheral devices i.e. a mouse, joystick, printer, modem, external floppy disk,
ROM cartridge application program etc.
The Atari ST console contains an 8MHz MC68000 16 bit microprocessor, at
least 512K of resident RAM and a 192K ROM operating system. A Mostek
MK68901 multi function peripheral (MFP) device provides the general purpose
interrupt control and timers and a single direct main memory access channel,
givingboth high (hard disk)and low speed (external floppy disk)access support,
through a 32-bit FIFO to the 8 bit device controllers.
User input is via the integral intelligent keyboard, an external mechanical and
or optical mouse, or a switch type joystick. The keyboard communicates with the
main console section bidirectionally at 7 Kbits/s via a 1MHz HD6301 8 bit
microprocessor
in
the
keyboard
unit,
and
a
MC6850
asynchronous
communications interface adapter (ACIA) in the console.
The display may be either a monitor, high resolution black and white or
colour (The Atari STM also caters for a standard television display unit). The
consoleinterrogates the display device to determine the type attatched, ensuring
the high frequency syncsignals are not sent to low frequency monitors. There are
three display resolutions, 320x200 16 colour low resolution, 640x200 4 colour
medium resolution and 640x400 high resolution monochrome. The display
memory is part of the main memory and provides a matching bit-pixel
relationship to the physical screen in high resolution mode.
The music system sound effects and audio feedback output are created
through the monitor or television speaker, at frequencies in the range of 30Hz to
128Khz, via three independant voice channels. The programmable sound
generator outputs may consist of a noise and a tone mixed at a fixed or variable
amplitude defined by the envelope generator.
1.3

<!-- source-page: 24 -->
## Page 24

The Concise Atari ST Reference Guide
Main System and Device Subsystems
MONITOR
RGB COMPOSITE
GRAPHIC
SYSTEM
SHIFTER
32K BIT MAP
320X200 16 COLOUR
640 X 200 4 COLOUR
640 X 400 MONO
DMA
INTERFACE
(DIRECT MEMORY
ACCESS)
HARD DISK
CONTROLLER
PARALLEL
INTERFACE
CENTRONICS
PRINTER
8-BIT BIDIRECTIONAL
MC68901
MFP
MIDI
INTERFACE
OMNI-POLY
AND
MONO NETWORK
INPUT/OUTPUT
1.4
PLUG-IN
CARTRIDGE
APPLICATIONS,
LANGUAGES ETC.
128k ROM MAX
MAIN SYSTEM
8 MHZ M68000
PROCESSOR
16 MBYTE ADDRESS
RANGE
SOUND SYSTEM
PROGRAMMABLE
SOUND
GENERATOR (PSG]
YAMAHA YM 2149
3-INDEPENDANT
VOICES
192K ROM
512KRAM (MIN)
MC6850 ACIA
MC 6850 ACIA
FLOPPY DISK
INTERFACE
SUPPORTS 2 DRIVES
WD1772AFDC
FLOPPY DISK
DRIVE
360/720 KBYTES
FORMATTED
RS232
INTERFACE
RTS/DTR/CTS/DCD/
RING
50-19200 BAUD
MC68901 MFP
KEYBOARD
INTERFACE
HD 6301
MOUSE/JOYSTK
PORT
2 BUTTON MOUSE
JOYSTICK
PORT
KEYBOARD

<!-- source-page: 25 -->
## Page 25

The Atari ST Hardware
The musical instruments digital interface (MIDI) enables the ST to integrate
with music synthesisers, sequencers, drum boxes etc. which incorporate the MIDI
interface;enabling OMNI, POLY and MONO networking.
Printer output is achieved via the parallel and RS232 interfaces, the latter also
being available for modem and general communication.
The floppy and hard disk interfaces provide the off-line data and program
mass storage facilities. The hard disk drive interface is accessed through the DMA
controller but the hard disk controller itself is off board. An on-board Western
Digital WD1772A interfaces the floppy disk drive, which may be either integral
or the Atari ST 3 1/2" disk drives SF 354 or SF 314.
Theoperatingsystemmaybe eitherin 192K of ROM, or an imagefile on disk,
loaded by the disks boot sector, featuring the GEM operating environment of
windows, icons, pull down menus. The STis also supplied with two language
implementations, an interpreted BASIC and Atari LOGO.
The ST can accept other operating systems loaded via the boot sector or
brought up by a driver in an 'AUTO' folder.
1.5

<!-- source-page: 26 -->
## Page 26

The Concise Atari ST Reference Guide
Atari ST Console I/O
MONITOR/TV OUTPUT
Monochrome Monitor
Atari SMI 24
71.25 Hz scan rate
Colour Monitor
Atari SC1224 RGB
50/60 Hz scan rate
13 way DIN 13S socket
Pin Function
1
Audio out
2
Composite video
3
General purpose output
4
Monochrome detect
5
Audio in
6
Green
7
Red
8
Ground
10
Blue
11
Monochrome
12
Vertical sync
13
Ground
Television
(where fitted)
RCA pin jack
Core : RF modulated video
Shield: Ground
Sync 5V active low 3.3Kohm
Audio IV pk-pk lOKohm
Video IV pk-pk 75ohm
ST signal processing device
(Reserved in older models)
TTL
PSG I/O A
TTL
MFP active low, 1K pull up to 5V
(+12V, 10mA shell for SCART connector)
** Note: Older versions of the ST reserved pin 2 and pin 8, this could be a
source of trouble with some peripherals. Always use pin 13 for ground if possible
1.6

<!-- source-page: 27 -->
## Page 27

The Atari ST Hardware
MONITOR OUTPUT
The monitor output supports either a high resolution black and white
monitor (Atari SM124) or a medium resolution colour monitor (Atari SC1224).
Sound is reproduced through the display device speaker.
Any suitable monitor may be attached, typical performance parameters of
such monitors are as follows:
Resolution
Video Bandwidth
Slot pitch (typ)
Input video
audio
Sync
Vertical scan
Horizontal scan
Low
452x585
Medium
653x585
High
895x585 pixels
lOMhz
18Mhz
18Mhz
0.64mm
0.41mm
0.31mm
1 VDC pk-pk
1 VDC pk-pk
5 VDC active low
50/60Hz
50/60Hz
71.2Hz
15.7Khz
35.7Khz
1.7

<!-- source-page: 28 -->
## Page 28

The Concise Atari ST Reference Guide
PARALLEL PRINTER INTERFACE
MFP
-—
0
0
0
PSG I/O port B
I/O port A E
Main Console
I/O port
I
Strobe
The paranel port interface
provides
an
8-bit
data
communication
channel
2-9
Data
controlled by a
strobe signal
II
Busy
generated by the ST, indicating
that data bits are available on
the data lines for transfer to the
peripheral, and a busy signal
generated by the peripheral (usually a printer) indicating either that it is busy,
has a fault or possibly out of paper if a printer.
13
1
OOOOOOOOOOOOO)
OOOOOOOOOOO
0/
Pin
Function
1
Strobe
2
Data 1
\
3
Data 2
1
4
Data 3
1
5
Data 4
1
6
Data 5
1
7
Data 6
1
8
Data 7
1
9
Data 8
/
10
n.c
11
Busy
12-17 n.c
18-25 Ground
25
14
25 way DB 25S socket
Data generated at a
typical rate of 4kbytes/s
by the PSG I/O port B
Acknowledge is not supported
The parallel port strobe signal generated by the PSG I/O port A (pin 1),
supplies thedata transfer synchronization. The busysignal (pin11) isreadbythe
console MFP and provides the handshake control.
Thestrobesignalis active low,the busy signalactive high, with a IKohmpull
up resistor to +5V. All signals are at TTL levels.
1.8

<!-- source-page: 29 -->
## Page 29

The Atari ST Hardware
RS232/MODEM INTERFACE
.
o
0
MFP
o
o
0
PSG
write only
I/O port A3
o
(FF8802)
Main Console
I/O port
2
Tx
transmit
Thfi
RS232
3
Rx
receive
interface is controlled
5
CTS clear to send
viathePSG I/O portA
8
DCD data carrier detect (RTS and DTR) and the
22
Rl
ring indicator
MFP (CTS, DCD and
RI)
transmitting
and
receiving data within
4
RTS ready tosend
the range 50 to 192K
20 DTR data terminal readibaud'
the
timinS
synchronization
is
generated
by
the
multi-function
processor (MFP) timer D. (Only the 'New TOS' supports RTS/CTShandshaking.)
The interface supports hardware handshake control:
RTS
\
Transmit
DTR / PSG I/O port A
CTS
\
DCD I
Ring /
Receive
MFP inputs
and software control through Xon/Xoff protocol.
Pin
Function
1
Grd
Protective ground
2
Tx
Transmit data
3
Rx
Receive data
4
RTS Ready to send
5
CTS
Clear to send
6
n.c
7
Gnd Signal ground
8
DCD Data carrier detect
9-19
n.c
20
DTR Data terminal ready
21
n.c
22
Ri
Ring indicator
23-25 n.c
13
25
14
25 way DB 25P plug
RS232 Signal Levels
Zero +3v
One
-3v
to +12v
to -12v
1.9

<!-- source-page: 30 -->
## Page 30

The Concise Atari ST Reference Guide
FLOPPY DISK INTERFACE
0
0
WD1772A
0
0
0
0
0
PSG
0
0
Main Console
I/O port
4
index pulse
8
motor on
9
direction in
10
step
12
write gate
2
select side
5
drive 0
6
drive 1
Note that the DIN socket shield must not be
connected on the ST side
The
floppy
disk
interface
is
based
on
an
on-board
Western
Digital WD1772A disk
controller
and
supports a maximum
of two drives. There is
no hardware sensing
of disk removal.
The
drives
provide
fast
storage and retrieval of
data and programs on
3
1/2"
flexible
micro
disks.
Pin
Function
1
read data
TTL
2
select side 0
TTL
3
4
logic ground
index pulse
TTL
5
select drive 0
TTL
6
select drive 1
TTL
7
8
logic ground
motor on
TTL
9
direction in
TTL
10
11
step
write data
TTL
TTL
12
write gate
TTL
13
track 00
TTL
14
write protect
TTL
14 way DIN 14S socket
1.10
active low, IK pull up
active high (high sys reset)
pair with read data
active low, IK pull up
active low (high sys reset)
active low (high sys reset)
pair with write data
active low \
active low
I
active low
I- (inverted)
active low
I
active low /
active low, IK pull up
active low, IK pull up
Data is written to 512 byte sectors.

<!-- source-page: 31 -->
## Page 31

The Atari ST Hardware
DIRECT MEMORY ACCESS PORT
This port canbe used to provideaccess to a hard disk or a compact disk. The
hard disk controller (target), not supplied with the basic ST system, is
communicated with-by a sequence of six bytes (from initiator system) which
provides format,read and writefacilities etc. in one direction only. Thecommand
protocol used is referred to as ANSI X3T9.2, a SCSI-like smallcomputersystems
interface, of which the STsupports a small subset.
The Atari hard disk descriptor block consists of a six byte command packet
conforming to the following:
Six byte command packet
Byte Bit
Function
no.
no.
range
0
0-4
5-7
Operation code
U-31
Controller number
0-7
1
0-4
Head number
0-31
5-7
Drive number
0-7
2
0-5
Sector number
0-63
6-7
3
0-7
4
0-7
Cylinder number high
Cylinder number low
Sector count
5
0-7
Control byte
Hard disk command code summary
Op code
Commanc
Dec Hex
5
05
Verify track
\ Multi-sector
6
06
Format track
1
transfer
8
08
Read sector
1
with
10
0A
Write sector
/ implied seek
11
0B
Seek
13
0D
Correction pattern
26
1A
Mode sense
There is only one DMA channel, it is shared by both high speed (upto
8Mbit/s) and low speed (250 to 500Kbit/s) 8-bit device controllers.
1.11

<!-- source-page: 32 -->
## Page 32

The Concise Atari ST Reference Guide
DMA interface port socket
10
Coooooooooo^
\o OOOOOOO 0/
19
11
19 way DB 19S socket
Pin
1
Function
data
0
\
Signal type
2
data
1
1
3
data
2
1
4
data 3
l_
TTL
5
data
4
1
6
data
5
1
7
data 6
1
8
data 7
/
9
chip select
TTL active low
10
11
12
13
14
15
16
interrupt request
ground
reset
ground
acknowledge
ground
Al
TTL active low, IK pull up
TTL active low (system reset)
TTL active low
TTL
17
18
ground
read/write
TTL
19
data request
TTL active low, IK pull up
The 'New TOS' supports more than one device attatched to the DMA port,
without the need for special software, on power up.
1.12

<!-- source-page: 33 -->
## Page 33

The Atari ST Hardware
MUSICAL INSTRUMENT INTERFACE (MIDI)
Main Console
o
0
Rx
receive data
return
I/O port
The
MIDI
interface
functions
through
an
MC6850
asynchronous
communications interface adaptor (ACIA) whose control/status register is
located at $FFFC04 (16776196); data is passed in the register at offset2 from the
control/status register.
Data is transmitted serially via the MIDI ports through two pins
asynchronously using the protocol:
One start bit, 8 data bits, One stop bit and no parity at 31.25 Kbaud.
The MIDI OUT port also supports the optional through port which merely
provides the MIDI IN signals through an opto-coupled isolator at the MIDI OUT
connector.
Control of the port is available through the ST's extended BIOS.
MIDI in
MIDI out
5 way DIN 5S socket
5 way DIN 5S socket
Pin
Function
Pin
Function
1
n.c
1
Thru tx data
2
n.c
2
Shield ground
3
n.c
3
Thru loop return
4
In rx data
4
Out tx data
5
In loop return
5
Out loop return
The Midi ports may be used to network data between connected computers,
they operate in RS232 current loop mode'.That is;
Signal levels
zero 5ma
one
zero current
1.13

<!-- source-page: 34 -->
## Page 34

The Concise Atari ST Reference Guide
PLUG-IN CARTRIDGE PORT
This port provides a plug-in cartridge facility that does not sense in hardware
the presence of a cartridge. The cartridge ROM occupies addresses in the range:
$FA0000 (16384000) to $FBFFFF
(16515071) - 128 Kbyte, Bank switching
provides a means of accessing even more.
1
39
iiiiiiiiiiiii
n
inn
hhlililililililililililiL,
lililililililllililih •i' i
2
40
40 way socket
Pin
Function
Pin
Function
1
power +5 Vdc
21
address
8
2
power +5 Vdc
22
address
14
3
data
14
23
address
7
4
data
15
24
address
9
5
data
12
25
address
6
6
data
13
26
address
10
7
data
10
27
address
5
8
data
11
28
address
12
9
data
8
29
address
11
10
data
9
30
address
4
11
data
6
31
ROM3 select
12
data
7
32
address
3
13
data
4
33
ROM4 select
14
data
5
34
address
2
15
data
2
35
upper data strobe
16
data
3
36
address
1
17
data
0
37
lower data strobe
18
data
1
38
ground
19
address 13
39
ground
20
address 15
40
ground
Only the lower 15 address lines are available to the ROM cartridge which
does not provide a 'write' line.
1.14

<!-- source-page: 35 -->
## Page 35

The Atari ST Hardware
INTELLIGENT KEYBOARD (ikbd) INTERFACE
The Atari intelligent keyboard performs a variety of functions that include
the decoding of the key switch matrix, decoding mouse, trackerball and joystick
data and providing the time of day. It communicates with the main processor
over
a
high
speed
bi-directional
serial
link
providing
a
convenient
mouse/joystick interface.
The keyboard consists of a series of make/break key switches for which the
ikbd generates keyboard scan codes for each key press and release, chosen
mainly for compatibility with the Digital Research graphic system (GSX). The key
codes, table Appx D.4, are defined for the whole range of international keyboards
such that each code has a predefined key press meaning, irrespective of the
presence of the key switch. The break code for each key is signified by bit 7 of the
corresponding make code for the key being set; the codes #$F6 to #$FF are
reserved for keyboard system functions.
The keyboard controller contains a 1 MHz HD6301 8-bit microprocessor that
communicates with the ST's MC6850 asynchronous communications interface
adaptor (ACIA) at a fixed 7.8 Kbit/s. The keyboard not only transmits the
encoded key scan codes (with a two key rollover), it also enables the programmer
to interrogate the status, define the read rates and sensitivity of the mouse and
joysticks under software control.
The time-of-day clock incorporated in the keyboard controller is held to a
resolution of 1 second and may be read and set from software. The keyboard may
be reset, without affecting the time held by the clock, to its power-up parameters.
When reset, the keyboard controller performs a simple ROM (checksum),
RAM and key (stuck) series of checks, correct operation is indicated by the return
of the version/release number of the ikbd controller.
1.15

<!-- source-page: 36 -->
## Page 36

The Concise Atari ST Reference Guide
MOUSE/JOYSTICK INTERFACE
The mouse and joysticks work on the basic unit of an 'event', this is defined
as either the opening or closing of a switch, or of motion beyond a predefined
programmable threshold level. The mouse is capableof a resolution of 200 events
per inch (4 events/mm) and is scanned at such a rate as to permit tracking
velocities of up to 10 in/s (250mm/s).
Motion,which produces make then break cursor keycodes, can be reported in
three different ways; relative, absolute and cursor key motion (motion per
keystroke is independently programmable in both axes). The mouse buttons can
also be treated as part of the mouse or as additional keyboard keys.
1
5
\.. • •/
6
9
9 way DB 9P plug
Joystick
Pin
Function
Mouse/Jstk 0
Function
XB/Up
XA/Down
YA/Left
YB/Right
n.c
left button/Fire
+5v
Gnd
right button/Joy 1
1
2
3
4
5
6
7
Up
Down
Left
Right
reserved
Fire
Power
Gnd
n.c
Port 0 is configured
for mouse operation
Port 1 is the second
joystick interface
The mouse unit provides
interactive input to programs
like the desktop applications,
permitting a convenient method
of selecting from a menu of
facilities shown symbolically
as icons or simply as text.
Port zero is configured for
the mouse, but may also be
fire connected to a joystick.
The joystick is invariably used in games applications; but may also be used
instead of the cursor keys, for fine control of the screen cursor position (one pixel
movement).
The joystickfire and mouse buttons close to ground.
1.16

<!-- source-page: 37 -->
## Page 37

The Atari ST Hardware
POWER SUPPLY
The seperate power supply provides power for the main system board, the
keyboard controller,any connectedexpansion ROM and expansion RAM.
The supply is fused, the levels are regulated for over-voltage and incorporate
over-current protection.
7 way DIN 7P plug
The power levels are:
5VDC @ 3A
5%
+12VDC @ 0.03A 10%
-12VDC @ 0.03A 10%
Pin
1
+5 VDC
2
n.c
3
Ground
4
+12 VDC
5
-12 VDC
6
+5 VDC
7
Ground
The power supply may be integral with the main unit (1040ST, Mega ST).
1.17

<!-- source-page: 38 -->
## Page 38

The Concise Atari ST Reference Guide
PROCESSOR DEVICE OUTLINES
MC68000 8 MHz microprocessor
WD1772A floppy disk controller
MK68901 multi-function processor
MC6850 asynchronous communications interface adaptor
YM2149 programmable sound generator
CUSTOM DESIGNED DEVICES (ULAS)
Direct memory access controller (DMA)
Memory management unit (MMU)
Video controller (Shifter)
General housekeeping (Glue)
Blitter
There have been three generations of operating system for the Atari ST
todate:
a) OS supplied on disk
b) TOS in ROM
c) 'New TOS' in ROM
The blitter chip requires the 'New TOS', but the 'New TOS' does not
necessarily require the blitter chip.
1.18

<!-- source-page: 39 -->
## Page 39

The Atari ST Hardware
MOTOROLA MC68000 MICROPROCESSOR
Signal I/O
The following is a very brief description of the signal I/O of the Motorola
MC68000.
Vcc
Ground
Clock
Processor / pQ1 "-l
status
T pQ2
Synchronous
control
a
s»<*-p
AO
to
Address bus [_)
A23
w
— DO
to
O
Da^ bus D
-
D15
r—\ Asynchronous
L-/
control
o
Bus arbitration
control
IPLO \
. .
IPL1
I-
'nterruPt
IPL2 /
control
A high-density, N-channel, silicon-gate depletion load 16-bit Microprocessor
in a 64 pin DIL package.
The Address bus (AO - A23) enables the MC68000 to address 16 megabyte of
data or 8 Megaword of instructions. The address bus provides the level being
serviced, during an interrupt, on address lines AO to A3 while A4 to A23 are held
high.
The Data bus (DO - D15) enables the transfer of word and byte-sized chunks
of data. During an interrupt acknowlege, a vector number may be placed on lines
DO to D7 by a peripheral device.
1.19

<!-- source-page: 40 -->
## Page 40

The Concise Atari ST Reference Guide
Bus arbitration control allows a peripheral device to control the MC68000
bus (bus master); any externalrequestwillbe granted on a priority basisbetween
the competing devices.
Interrupt control provides a priority level from peripherals requesting
processor control enabling selection of multiple interrupts on a priority basis.
Zero implies that there is no interrupt present and 7 is a non maskableinterrupt.
Level
Autovector
7 high
6
5
Non maskable interrupt
MC68901 multi function processor
4
3
Vertical blanking sync
2
1 low
Horizontal blanking sync.
System control informs the processor that bus errors have occurred and also
resets or halts the processor.
Processor status: each time a memory or I/O call is made the processor
provides the following information on the processor status lines to a peripheral
device: whether the processor is accessing data or program memory space or
servicing an interrupt; and whether the processor is in user or supervisor mode.
The Motorola MC68000's separate parallel address and data buses are used to
transfer data using an asynchronous bus structure controlled by the processor,
internal or external, which has current bus control.
Interfacing with the 8-bitM6800 and 6500 family of synchronous peripheral
devices is catered for through the use of memory-mapped I/O and a modified
bus cycle.
1.20

<!-- source-page: 41 -->
## Page 41

The Atari ST Hardware
WD1772A
FLOPPY DISK CONTROLLER
$FF8604
7
Access
data
0
byte
$FF8606
8
Mode
control
2
1
C
r/w
A1
AO
Status,
reg
Cmd
reg
Sector
reg
Track
reg
Data
reg
ommands are passed to the FDC (and an external HDC), by selecting the
appropriate FDC or HDC function (Read status/write command, sector, track or
data) through the configuration register ($FF8606) and sending instructions or
data via the access byte ($FF8604).
MODE BYTE ($FF8606)
Bits
1 0
00
01
1 0
1 1
Register
Read
'
Write
Status
Track
Sector
Data
Command
Track
Sector
Data
Bit 7 selects Write (1) or Read (0)
The WD1772A floppy disk controller supports eleven instructions, these
should only be loaded into the data byte register when the status bit (bit 5,
$FFFA01) is off. The instructions enable head location, reading and writing
sectors, tracks and the forced interrupt of a disk operation:
1.21

<!-- source-page: 42 -->
## Page 42

The Concise Atari ST Reference Guide
INSTRUCTION BYTE ($FF8604)
1.22
Type 1 command
0000
0001
001 .
010.
011.
1
0
0
0
0
0
0
.00
.01
. 1 0
. 11
1..
1
Restore\ To track 0 position
Seek
/ Track position
Step
Towards last track
Step in
Towards inner track
Step out
Towards outer track
Update track register
Toggle bit
2ms
\
3ms
Step
12ms
rate
6ms
/
With verify
\ Toggle
Without Spin-up disable
/
bits
Type 2 command
10 0
Read Sector
10 1
Write Sector
... 1
write 'deleted data' mark \
• • 1 .
precompensation enabled
•1 •.
30msdelay
1 .. .
without'spin-up' delay
• •• 1
••••
multiple sector read/write /
Toggle
bits
Type 3 command
110.
..00
Read address
111.
..00
Read track
1111
0
Write track
Read diskette ID
... 1
write 'deleted data' mark \
• • 1 .
precompensation enabled
•1 •.
30msdelay
1 ...
without'spin-up' disable
/
Type 4 command
110 1
..00
Force interrupt
0 0..
end with no interrupt
0 1..
interrupt on index pulse
10..
immediate interrupt
Toggle
bits

<!-- source-page: 43 -->
## Page 43

The Atari ST Hardware
MC68901 MULTI-FUNCTION PROCESSOR
Data^
(8)
-
RS1 -
RS5^
CS^
R/W^
DS -
DTACK^
Reset
set
CI
Clock
Internal
control logic
IEI
IRQ
IEO
IACK
Daisy chain
Timer
C&D
_OSC
Timer
A&B
USART,
GP~
I/O
TCO
TDO
Xtah
Xtal2
TAO
TAI
TBO
TBI
Serial in
Tx clock
Serial out
Serial clock
Rx ready
Tx ready
I0-I7
Bit I/O interrupts
& modem control
The MC68901 contains a single channel USART capable of operating in full
duplex, at a rate of 62.5Kb/s asynchronous, IMb/s synchronous from an internal
or external Baud rate generator. The USART also supports DMA handshake
signals and modem control.
There are four timers with independant operation and vectored interrupts,
the timers have the following preferred timer uses:
Timer
A: Stand alone applications and independent software vendor.
B:Primarily Screen Graphics (hblank, sync etc.)
C: System timing (GSX, GEM, Desktop, etc). Suitable for delays and
general timing applications (200Hz).
D: RS 232 port baud rate control.
Eight individually programmable I/O pins with interrupt capabilities are also
available.
1.23

<!-- source-page: 44 -->
## Page 44

The Concise Atari ST Reference Guide
MC68901 INTERRUPT CONTROL
MFP HARDWARE BOUND INTERRUPTS
Priority
Function
15 high
14
13
12
Monochrome monitor detect
RS232 ring indicator
Timer A
RS232 receive buffer full
GPI (7)
GPI (6)
Timer A
11
10
9
8
RS232 receive error
RS232transmit buffer empty
RS232 transmit error
Horizontal blanking counter
Timer B
7
6
5
4
3
2
1
0 low
FDC/HDC - Interrupt
'Keyboard and MIDI
Timer C (system clock)
RS232baud rata generator
Blitter interrupt (reserved)
RS232 clear to send
RS232 data carrier detect
Parallel port busy
GPI (5)
GPI (4)
Timer C
Timer D
GPI (3)
GPI (2)
GPI (1)
GPI (0)
*Test MC6850 status bit to differentiate between keyboard and MIDI interrupts.
MFP CONFIGURATION REGISTERS
These are located at address $FFFA01-16775681 and may be accessed via the
following offsets:
Offset
Function
Offset
Function
Dec
Hex
Dec
Hex
1
01
Gen purpose I/O
25
19
Timer A control
3
03
Active edge
27
IB
Timer B control
5
05
Data direction
29
ID
Timer C & D control
7
07
Interrupt enable A
31
IF
Timer A data
9
09
Interrupt enable B
33
21
Timer B data
11
0B
Interrupt pending A
35
23
Timer C data
13
0D
Interrupt pending B
37
25
Timer D data
15
OF
Interrupt m-serv A
39
27
Sync character
17
11
Interrupt in-serv B
41
29
Usart control
19
13
Interrupt mask A
43
2B
Receiver status
21
15
Interrupt mask B
Vector base address
45
2D
Transmitter status
23
17
47
2F
Usart data
1.24

<!-- source-page: 45 -->
## Page 45

The Atari ST Hardware
TheMC68901 usart registers are accessible from ExtendedBIOS (XBIOS)
SYNCHRONOUS CHARACTER REGISTER
I7l6l5l4l3l2l1l0~l
SCR = $FFFA27
Used to synchronize incoming received data acting as the matching character
USART CONTROL REGISTER
7l6l5l4l3l2l1l0l
UCR = $FFFA29
0
0 = odd, 1 = even
off, 1 = enable
•async
•async
async
0
0
-sync
8 bits per word
1 - 7 bits per word
0 - 6 bits per word
1 - 5 bits per word
0 = normal, 1 = Divide by 16
Start
1
2
and
1
1/2 used by div by 16
stop
1 1
bits
0
0
TRANSMIT STATUS REGISTER
7|6|5|4|3|2|1|0~|
TSR = $FFFA2D
Interrupt
generated
END
B
TE
0 = disable Tx and clear flag
1 = enable normal operations
0
0
high imp
\
Configure Tx
0
1
low
o/p when
1 0
high
/
Tx disabled
1
1
loopback async (connect o/p to i/p)
Normal Tx
Send a break
0
Tx enabled
1
Tx disabled after last character sent
Disable Tx
Enable Rx when Tx disabled after last character sent
0
Tx status register read
1
Word transmitted and Tx buffer empty
Tx buffer read
Tx word transferred to Tx shift register
10
1.25

<!-- source-page: 46 -->
## Page 46

The Concise Atari ST Reference Guide
RECEIVE STATUS REGISTER
I 7 I 6 I 5
3 12 11
OS
PE|
FE]
F/S(
M
S3
RET
0 = disable Rx and clear flag
1 = enable normal operations
0
strip sync character (sync)
1
sen sync character
0
stop bit Rx (async)
1
word being Rx
0
no character match (sync)
no break (async)
1
word match
break Rx
RSR = $FFFA2B
no frame error in word in Rx buffer (async)
frame error in Rx buffer word
0
no parity error inword in Rx buffer
1
parity error in Rx buffer word
0
Rx status register read
1
Word received and Rx buffer empty
Rx buffer read
\
Read
Rx word transferred to Rx buffer /
only
Interrupt
generated
11
11
12
11
Timer A uses register B ($FFFA19), timer B register 14 ($FFFA1B), timers C
and D both use register 15 ($FFFA1D). Timer C bits 4 to 6 and timer D bits 0 to 2,
both operate delay mode only.
7 16 15
1.26
0
0
0
0
0
0
Timer stop
Event #
0
0
0
1
1
1
1
1
0
-
4
0
-
10
1
-
16
0
-
50
1
-
64
0
-
100
1
-
200
0
delay mode
1
pulse width mode
delay

<!-- source-page: 47 -->
## Page 47

The Atari ST Hardware
MC6850
ASYNCHRONOUS COMMUNICATIONS
INTERFACE ADAPTOR
D0-D7
Tx clock
Tx
shift
register
IX
IX
•H^^-
data
shift
^
[register
[registei
Data
bus
buffed
Rx clock
Status^
register
Control
register
Rx
data
register
Rx
shift
register
Tx data
CTS
DCD
-
RTS
Rx data
The MC6850 ACIAprovides data formatting and control of a serial interface
to an 8-bit bidirectional data bus. At the bus interface, the four ACIA registers,
the status and receive data -read only and the control and transmit data-write
only registers, appear as two addressable memory locations.
The programmable ACIA control register, which sets the format of the serial
link, is located at
$FFFC00 (16776192) for the intelligent keyboard serial
communications link, and at $FFFC04 (16776196) for the MIDI interface.
The ACIA supports peripheral/modem control through:
and
RTS request to send,
CTS clear to send
DCD data carrier detect.
Protocols for 8 and 9 bit transmission using an optional odd or even parity,
and one or two stop bits, are available through the programmable control
register.
The MIDI port may be configured as a second serial port (for networking) but
the intelligent keyboard interface is not accessible.
1.27

<!-- source-page: 48 -->
## Page 48

The Concise Atari ST Reference Guide
ACIA CONTROL/STATUS REGISTER
Interrupt request
Parity error
Rx overrun (character lost)
Framing error
CTS
DCD
Tx data register empty
Rx data register full
'READ'
RECEIVE STATUS
REGISTER
0
0
1
1
Rx
"Rx
1.28
5
4
0
0
1
1
0
0
1
1
RTS low
RTS low
1
$FFFC00-$FFFC04
0
0 \
normal
\
Divide
0
1
Divby16
select
1
0 /
Div by64 /
bits
1
1
Master reset
7 bits, even, 2 stop bits
7 bits, odd, 2 stop bits
7 bits, even, 1 stop bit
7 bits, odd, 1 stop bit
8 bits, 2 stop bits
8 bits, 1 stop bit
8 bits, even, 1 stop bit
8 bits, odd, 1 stop bit
0
RTS low, Tx interrupt disable
1
RTS low, Tx interrupt enable
0
RTS high, Tx interrupt disable
1
RTS low, Tx a break onto data output. Tx interrupt disable
interrupt disable
interrupt enable (Rx data register full overrun. DCD low to high transition)
'WRITE'
TRANSMIT CONTROL
REGISTER

<!-- source-page: 49 -->
## Page 49

The Atari ST Hardware
YAMAHA YM2149 PROGRAMMABLE SOUND
GENERATOR
Channel A [tone
Channel B Itone
Channel CItone
NOISEH
Mixer
ENVELOP
Generator
-Iaj^p-
JA^P-
D/A
D/A
D/A
Sounp
O/P
Port
CPU bus
CPU bus
I/O
Register
I/O
Register
8 bit I/O
port A
8 bit I/O
portB
The programmable sound generator control registers are located as follows:
RAM offset
Function
Bits used
reg addf
BasP address SFF8800-16746596 | 7654
37.1 f)
0
1
2
3
4
5
6
7
0
Channel A fine tune
1
Channel A coarse tune
2
Channel B fine tune
3
Channel B coarse tune
4
Channel C fine tune
5
Channel C coarse tune
6
Noise period
7
Mixer cntrl-I/O enable
Fixedamplitude
8
Channel A amplitude
9
Channel B amplitude
A
Channel C amplitude
Variable amplitude
B
Envelope period fine
C
Envelope period coarse
D
Envelope shape
E
I/O port A (output only)
F
I/O port B (Centronics)
fixed/variable C=cycle A=alternate x-
xxxx
xxxx
xxxx
xxxx
xxxx
xxxx
xxxx
xxxx
xxxx
x
xxxx
I/O noise tone
M
xxxx
M
xxxx
M
xxxx
xxxx
xxxx
xxxx
xxxx
CRAH
9
10
11
12
13
14
15
M=mode
data
bits used R=ramp H=hold
1.29

<!-- source-page: 50 -->
## Page 50

The Concise Atari ST Reference Guide
1.30
DIRECT MEMORY ACCESS CONTROLLER (DMA)
RAV
1
40
A1
2
39
FCS
3
38
DO
4
37
D1
5
36
D2
6
35
D3
7
34
D4
8
33
D5
9
32
D6
10
31
D7
11
30
D8
12
29
D9
13
28
D10
14
27
D11
15
26
D12
16
25
D13
17
24
D14
18
23
D15
19
22
Gnd
20
21
+5v
elk 8Mhz
RDY
ACK
CDO
CD1
CD2
CD3
CD4
CD5
CD6
CD7
Gnd
CA2
CA1
CRAV
HDCS
HDRQ
FDCS
FDRQ
MEMORY MANAGEMENT UNIT (MMU)
26
10
27
9
1
68
43
61
44
60
1
D4
18
RAS1
35
A15
52
DE
2
D5
19
4Mhz Out
36
A14
53
DTACK
3
D6
20
8Mhz Out
37
A13
54
MAD5
4
D7
21
CASH
38
A12
55
MAD4
5
16MhzlN
22
CAS1H
39
A11
56
MAD3
6
CAS0H
23
WE*
40
A10
57
MAD2
7
CAS0L
24
DMA
41
A9
58
MAD1
8
RAS0
25
WDAT*
42
A8
59
MAD0
9
LATCH
26
UDS*
43
A7
60
MAD6
10
VCCA
27
Gnd
44
+5v VCCB
61
Gnd
11
A16
28
CMPCS*
45
A6
62
MAD7
12
A17
29
DCYC*
46
A5
63
MAD8
13
A18
30
RDAT*
47
A4
64
MAD9
14
A19
31
DEV*
48
A3
65
DO
15
A20
32
AS*
49
A2
66
D1
16
A21
33
RAM*
50
A1
67
D2
17
LDS*
34
RAW*
51
VSYNC
68
D3

<!-- source-page: 51 -->
## Page 51

The Atari ST Hardware
VIDEO CONTROLLER (SHIFTER)
XTLO
1
1
40
32Mhz XTL1
2
39
DO
3
38
D1
4
37
D2
5
36
D3
6
35
D4
7
34
D5
8
33
D6
9
32
D7
10
31
load
11
30
D8
12
29
D9
13
28
D10
14
27
D11
15
26
D12
16
25
D13
17
24
D14
18
23
D15
19
22
Gnd
20
21
+5v
16Mhzclk
CS
DE
A1
A2
A3
A4
A5
RA/V
Mono
R0
R1
R2
GO
G1
G2
BO
B1
B2
GENERAL HOUSEKEEPING (GLUE)
+5v Vcc
A14
A15
A16
A17
6
A18
7
A19
8
A20
9
A21
10
A22
11
A23
12
AS*
13
FC2
14
FC1
15
FCO
16
VMA*
17
ROM4
26
10
27
9
1
68
43
61
44
60
18
ROM3
19
ROM2
20
ROM1
21
ROMO
22
RESET*
23
RAM*
24
DMA*
25
DEV*
26
FCS*
27
BGI*
28
RDY
29
VPA*
30
BERR*
31
DTACK*
32
IPL1*
33
IPL2*
34
8Mhz In
35
Gnd
36
BLANK*
37
HSYNC
38
VSYNC
39
DE
40
BR*
41
BGACK*
42
6850CS*
43
500Khz out 60
44
MFPINT*
61
45
BGO*
46
LDS*
47
UDS*
48
DO
49
D1
50
IACK*
51
MFPCS*
52
53
54
55
56
57
58
59
62
63
64
65
66
67
68
Gnd
SNDCS*
2Mhz out
RAW*
A1
A2
A3
A4
A5
A6
A7
A8
A9
A10
A11
A12
A13
1.31

<!-- source-page: 52 -->
## Page 52

The Concise Atari ST Reference Guide
1.32

<!-- source-page: 53 -->
## Page 53

Operating System Overview
Chapter 2
The operating system (TOS) overview
Operating system overview
2.3
Basicinput/output system (BIOS)
2.4
GEM BIOS
2.4
XBIOS
2.4
Line-A routines
2.4
Basic disk operating system (BDOS)
2.4
Virtual device interface (VDI)
2.4
Application environment services (AES)
2.5
Application programs
2.5
Memory allocations
2.6
Memory map
2.6
System tables
2.7
Configuration registers
2.8
Resource mangement overview
2.9
CPU resources
2.9
Graphics concept overview
2.10
Overview of screens
2.12
High resolution screen
2.12
Medium resolution screen
2.12
Low resolution screen
2.12
Color palette table
2.13
Physical to logical screen transposition
2.13
High resolution screen
2.13
Medium resolution screen
2.14
Low resolution screen
2.14
Colour generation
2.15
Colour changing
2.15
Animation
2.15
2.1

<!-- source-page: 54 -->
## Page 54

The Concise Atari ST Reference Guide
2.2
Sound concept overview
2.16
Sound control register
2.16
Parallel data I/O
2.17
Sound configuration registers
2.18
Tone frequency calculations
2.18
Noise frequency calculations
2.18
Envelope calculations
2.19
Shape
2.19
Period/cycle
2.19
GEM disk operating system (GEMDOS)
2.20
Memory model
2.21
Base page
2.21
CP/M 68K format
2.22
File header format
2.22
Symbol table
2.23
Relocation table
2.23
STfile system
2.25
ST disk system
2.26
ST BIOS comparisons
2.27
Interrupt handler overview
2.27
System initialization
2.28
Cartridge software
2.31
Boot sectors
2.32
Boot loader
2.34
Boot ROM
2.35
Implemented functions
2.35
Peripheral device communications
2.36
Communications overview
2.36
RS232 interface
2.37
Parallel port interface
2.38
Midi interface
2.39
Control/status register functions
2.40
Intelligent keyboard interface
2.41
Keyboard
2.41
Mouse
2.41
Joystick
2.41
clock/program control
2.42
Floppy disk interface
2.43
Formatting a floppy disk
2.44
WD 1772A DMA channel interface
2.45
DMA interface
2.47
DMA bus boot code
2.48
Hard disk partitioning
2.50

<!-- source-page: 55 -->
## Page 55

Operating System Overview
Operating system overview
The Atari ST operating system is in many ways functionally similar to
MS-DOS, with extensions for handling a mouse, sound, the midi interface, an
intelligent keyboard and joysticks. The source is based on a CP/M 68K related
operating system referred to as the TOS (Tramiel Operating System). A graphics
environment manager
(GEM)
provides additional single-user support for
windows and communications via VDI and AES extensions, which support
graphics
and
an
applications environment.
Program
transportability is
maintained by splitting the operating systems into machine independant (BDOS,
VDI and AES) and machine dependant basic input/output utilities (BIOS and
line-A routines).
The ST programmer is given access to the VDI primitives via the line-A
routines for much greater graphic application speed.
Thedisk operatingsystem (DOS) contains routines that provideaccess to the
disc drives and support existing single user programs, file locking to ensure safe
updating, unlock and read only facilities. Disk operation errors are trapped
(where possible) and corrected.
Machine/
dependant
input/outputl
routinesx
General/
operating!
systems\
BIOS
GEMDOS
Basic
disk
operating
system
LINE-A
routines
GEM VDI
Virtua
device
interface
GElVl
AESl
Programmable segments of TOS
The application environment (AES) multitasks using a timeslicing technique
and supports a database file management system, real time data aquisition,
communications and process control.
The virtual device interface (VDI) allows the use of peripheral independant
device drivers and provides a high degree of support for advanced user
interfaces.
2.3

<!-- source-page: 56 -->
## Page 56

The Concise Atari ST Reference Guide
BASIC INPUT/OUTPUT SYSTEM (BIOS)
The BIOS consists of all the machine dependent I/O routines of Digital
Research's GEM and additionally provides access to the line-A routines for fast
graphics. The I/O functions can be categorized as follows:
GEM BIOS:
System I/O:
Console I/O:
Disk I/O:
ST XBIOS:
Port I/O:
Screen I/O:
Disk I/O:
Keyboard I/O:
Line-A routines:
Pixel graphics
Line graphics
Sprite graphics
Bit block transfer
Mouse handler
Parameter block initialization
DataI/O &query
Memory/disk transfers
Configure RS232, mouse, midi & sound port
Get screen parameters
Memory/disk transfers
Keyboard communications
BASIC DISK OPERATING SYSTEM (GEMDOS)
The disk operating systems permits the machine independent routines to
access the disk drives and handle file management through the following
functions:
Set/get time and date
Tree directory management
File attribute management
Create/open/close files and disk transfers.
Current versions of GEMDOS impose a limit of 40 folders>
2.4

<!-- source-page: 57 -->
## Page 57

Operating System Overview
Virtual device interface (VDI)
The VDI provides a set of graphic function calls that allow portability across
physical hardware. Not all the standard VDI calls are implemented on all the
operating systems available for the ST, the VDI tables Chapter 3 are annotated to
show those that are missing from the various systems.
Control I/O:
Initialize graphics & set defaults.
Graphics I/O:
Primitives, lines, polygons, bars, arcs & pies.
Attribute I/O:
Set colour and style.
Raster I/O:
Bit block transfers, fill, font and cursor forms.
Input I/O:
Keyboard/mouse interaction with console.
Inquire I/O:
Get attributes, resolution, style etc.
Special I/O:
Permits specialized functions to be performed.
Application Environment Services (AES)
The AES (application environment services) are a series of utilities that
handle graphic based inputs to the user application. For example, instead of
asking for INPUT - the screen displays graphically a menu of options which may
include a clock, a file and perhaps a disk, these items being given a pictorial
representation that is called generically an 'Icon'. To select one, the user simply
moves the cursor, which may look remarkably like an arrow, and places it on the
required icon by moving the mouse and pressing a trigger button on the mouse.
The AESroutines are put into groups called libraries as follows:
Application:
Provide access to AES routines.
Event:
React to user inputs
Menu:
Translate defined text to menu format.
Object:
Substitute graphic-icon for its label
Form:
Handle text input automatically when needed.
Graphic:
Primitive graphic functions.
Scrap:
Management of cut and paste.
File Selector:
Creation/display of user selected file.
Window:
Handle windowing ofqueried input responses.
Resource:
Interface device dependant drivers to applications.
Shell:
Enable one program to call another.
Application programs
The desktop application is part of the operating system and is the base user
interface when other application programs are not running. It provides a
calculator, alarm and clock; and through manipulation of icons via the mouse,
disk directories, disk and file copy and deletions, disk formatting, as well as other
activities such as communications, data output and window control
2.5

<!-- source-page: 58 -->
## Page 58

The Concise Atari ST Reference Guide
MEMORY ALLOCATIONS
SFFFFFF
$FF8800
$FA0000
$400000
$100000
$080000
$000400
$000000
Memory
mapped
input/
output
ROM
Area
4M RAN
max
1024K
RAM
512K
RAM
OSBSS
user R
variables
Supervisor
RAM
variables
16777215
16746596
16384000
4194304
1048576
524288
2048
\
Supervisor
access
1024
on|y
$FFFFFF
$FFFC00
$FFFA00
$FFBA00
$FF8800
$FF8600
$FF8400
$FF8200
$FF8000
MC6850
MK68901
Blitter
SOUND
DMA/Disk
Reserved
Display
Memory
16777215
16776192
16775680
16747108
16746596
16746084
16745572
16745060
16744448
MEMORY MAPPED I/O
CONFIGURATION REGISTERS
$FF0000
$FC0000
$FA0000
192K
system
ROM
128K
cartridge
ROM
16711680
16515072
16384000
ROM CONFIGURATION
IN MEMORY
References to the bottom 2K of memory and the I/O space are classed as
supervisor references and attempted access from user mode will cause an error
exception trap.
2.6

<!-- source-page: 59 -->
## Page 59

$800
$400
$200
$100
$0BC
$0B8
$0B4
$0B0
$08C
$088
$084
$080
$07C
$078
$074
$070
$06C
$068
$064
$060
$03C
$02C
$028
$024
$020
$01C
$018
$014
$010
$00C
$008
$000
Operating System Overview
SYSTEM TABLES
Operating system block storage segment
Trap #15 vector
Trap #14 vector
Trap #13 vector
Trap #12 vector
Trap #3 vector
Trap #2 vector
Trap #1 vector
Trap #0 vector
Interrupt level 7
Interrupt level 6
Interrupt level 5
Interrupt level 4
Interrupt level 3
Interrupt level 2
Interrupt level 1
Spurious intrpt
Uninit int vector
Emulation 1111
Emulation 1010
Trace
Privilege violation
Trap instruction
CHK instruction
Divide by zero
Illegal instruction
Address error
Bus error
Initialise PC
Reset init SSP
1024
System parameters
and variables
512
Reserved for OEMs
Supervisor
space
256
MFP vectored interrupts
188
184
180
176
172
140
136
132
128
124
120
116
112
108
104
100
96
60
48
44
40
36
32
28
24
20
16
12
XBIOS (ST extended BIOS)
BIOS
BDOS
GEMDOS interface
Non maskable interrupt
68901 MFP
Vertical blank sync
Normal interrupt level
Horizontal blank sync
Unused vectors point to the
system critical error handler
Used by some AES functions
Line-A routines entry
The system variables are in
the supervisor space and can
be accessed only In supervisor
mode
2.7

<!-- source-page: 60 -->
## Page 60

The Concise Atari ST Reference Guide
$FFFC0(l
$FFFA0Cl
SFF8800
$FF8600
SFF8400
$FF8200
$FF8000.
2.8
CONFIGURATION REGISTERS
ACIA
MFP
Blitter
Sound
DMA/Disk
Reserved
Display
Memory
Functions controlled
.-.-,-.-,-.,.
Keyboard and MIDI I/O
167761Q2
System checks, system interrupts
16747108
16746596
16746084
16745572
16745060
16744448
PSG 3 channel sound, noise, tone,
amplitude and envelope
Floppy/hard disk, DMA
Video address, field rate,
video made and palette
Memory size

<!-- source-page: 61 -->
## Page 61

Operating System Overview
Resource management overview
The pseudo multitasking kernal can support one primary application and
one of a number of desk accessory programs. The main application may be GEM
or DOS such as GEM desktop application or a word processing package etc.
Primary
application
A minimum space
allocation of 128K
Screen
environment
Desk
ace 1
A desk accessory is an application that does not take over the entire display
screen, running in a specially designed window. The calculator is a typical
accessory.
Onlyonedeskaccessory program maybe active at a time, and willonlyload
if at least128K ofRAM isleftfortheprimaryapplication.
CPU resources
The dispatcher divides CPU time between primary applications and
background processes. These jobs are put into lists; 'Ready for processing' and
'Not ready7, and are serviced on a round robin schedule with the current process
at the head of the list running. Not ready processes may be waiting for a key
press, mouse movement or trigger, time lapse etc.
2.9

<!-- source-page: 62 -->
## Page 62

The Concise Atari ST Reference Guide
Graphics Concept Overview
The Atari ST graphics is supported at a primitive level through the line-A
routines and at a higher level through a limited version of the Digital Research
graphic system extension (GSX), which is based on the ANSI virtual device
interface (VDI). VDI provides a set ofgraphic primitives(GDOS) and a libraryof
device drivers (GIOS) for the preparation of transportable software. The whole of
GDOS and GIOS are not included in the ROM based ST operating system and
there is no support for a small number of the VDIfunctions. These mainly cover
lack of support for multiple fonts, the driving of 'non-standard' output devices
and the use of 'normalised device coordinates.
The VDI interface provides output primitives of lines, arcs, polygons etc. and
input primitives to point symbolically, get co- ordinates of joystick/mouse or
keyboard input etc. It also supports the control of multiple output devices using
raster screens.
The line-A routines give very fast access to the primitive pixel, line, sprite
and bit block transfer graphic functions at the expense of portability
RASTER COORDINATES are based on screen pixels.
0,0
640,400
GEMprograms are portable but must take into account two possible problem
areas:
Screen aspect ratio: Different hardware systems and displays (screen,
printer, plotter or another computer) may have differentaspectratios. Producing
similar screen designs requires the programmer to scale the data sent to the
displaydeviceusing the aspectratio returned from the open workstationcall.
Language implementations: Different language implementations of a
program will require different length text strings to be fitted into windows. The
inquire character cell width call in conjunction withthe window sizereturned by
the wind_get call will enable the programmer to determine the number of
characters acceptable.
2.10

<!-- source-page: 63 -->
## Page 63

Operating System Overview
Alert and Dialog boxes have predetermined responses set up using the
resource construction set and therefore do not present a language problem.
The missing part of GDOS is available as part of the code supplied in Ct* ictin
Digital Research products and may at a later date become more generally
available for the ST (as 'AUTOXGDOS.PRG' file). On this premise, the details of
the missing parts are given coupled to a rider that they are not available on the
basic system.
GEM usually provides two graphic coordinate systems to the programmer,
raster and normalized.
Raster is based on the computers screen resolution, in the case of the Atari ST
600 x 400 pixels (monochrome).
NDC (not implemented) is based on a notional screen of32767 x32767 points,
the points beingtranslated to the actual screen of the targetsystem by oneof the
GIOS device drivers. The idea behind this is to write software independant of
specific screen resolutions.
NORMALIZED
DEVICE
COORDINATES
are
based
on
a
screen
of
32767x32767 pixel dimensions.
32767,32767
0,0
Graphic Coordinate Computation
32767,32767
640,400
Full NDC mapped to
full RC space
2.11

<!-- source-page: 64 -->
## Page 64

The Concise Atari ST Reference Guide
Overview of screens
The Atari ST screen may be operated in three different resolution modes, the
colours may be chosen from a palette of 512 colours:
High:
640 x 400 pixel, black and white display
Medium:
640 x 200 pixel, 4 colour display
Low:
320 x 200 pixel, 16 colour display
High Resolution 640 x 400 pixels
Origin
SINGLE
PLANE
Black border
Medium Resolution 640 x 200 pixels
Origin
TWO
PLANES
Border is palette colour zero
Low Resolution 320 x 200 pixels
Origin
No colour but inverse video is
available determined by the
condition of bit zero of palette
colour zero
Only the first four lookup table
entries are available.
16 word lookup table of 9 bits/entry
3 red, 3 green and 3 blue on low
nibble boundaries, giving 8x8x8
possible colours (512).
Border is palette colour zero
It is not possible to change resolutionwhile using GEM
2.12

<!-- source-page: 65 -->
## Page 65

Operating System Overview
Colour Palette Table
Palette colour
15
12
11
0
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
8
7
4
3
I
Not used
Blue
Green
Red
Colour nibbles
Palette colour
/zero, bit colour
0
\
1
2
3
/
MSB
Medium
resolution
palette
LSB
Colour nibble
8 levels of colour
x = bit not used
Physical to logical screen transposition
High resolution mode 640 x 400
PHYSICAL SCREEN
1
314
641643
pixels
L16117
LOGICAL SCREEN
bit 15
bitO
MSB word 1
LSB
MSB word 41 LSB
MSB word 2
LSB
400 words
40 words -
MSB word 16000 LSB
Low memory
word 1
word 2
word 3
TjjgTi
low
word 15991)
word 16000
Screen in
memory
Border always set black
Bit zero of the colour
palette provides inverse
video
2.13

<!-- source-page: 66 -->
## Page 66

The Concise Atari ST Reference Guide
Medium resolution mode 640 x 200
PHYSICAL SCREEN
plane
1
2
3 I 4 I
8
I 9
I
641 642
pixels
LOGICAL SCREEN
bit 15
bitO
MSB word 1
LSB I MSB word 3
LSB
Plane 1
Plane 2
MSB word 2
LSB
MSB wo -d4
LSB
200 words
80 words •
Low memory
word 1
word 2
word 3
jTigh
low
word 1599E
word 1600C
Screen in
memory
MSB word 16000 LSB
15
13
Border set by colour palette zero
2
1
0
Plane 1 word
Plane 2 word
Colours generated by interleaved bits of words
Low resolution mode 320 x 200
Plane
1
2
Palette
colour
0
0
0
1
1
0
1
1
0
1
2
3
PHYSICAL SCREEN
Colours generated by
interleaved bits of the
fourplanes. Plane 1
provides the least
significant bit in the
palette table pointer
2.14
1
321 32:
8 I 9
pixels
LOGICAL SCREEN
bit 15
bitO
Plane 1
"
Plane 2
MSB word 1
LSB I MSB word 5
LSB
MSB word 2
LSB
MSB word 6
LSB
Plane 3
Plane 4
MSB word 3
LSB I MSB word 7
LSB
MSB word 4
LSB I MSBTwd-d 8
LSB
200 words
0
80 words
MSB word 16000 LSB
Border set by colour palette zero

<!-- source-page: 67 -->
## Page 67

Operating System Overview
Color generation
A word from each plane is taken from the video display file and placed in rhe
video shift register from where the bits are collectively used to index into the
colour palette table. The colour code generated is supplied to a 3-bit digital to
analogue convertor to produce the RGBsignals.
Logical bit-map
planes
1
Video display
memory
12 3
4
Video shift
register
.1.x
.2.x
.3.x
.4.x
Colour palette
and 3-bit DAC's
16x9
lookup
table
Inverter
-
R
-
G
^
B
Mono
In high resolution monochrome mode, the video shift register passes its data
to the inverter and not the palette lookup table.
Colour changing
To prevent jitter when changing colors using the Hblank ($068) and Hsync
($120) interrupt vectors, programmers should use the following procedure:
1) Revector keyboard/MIDI interrupt to a routine that lowers the IPL to 5
and then jumps through the original vector.
2) During the critical section of screen, revector the system 200Hz clock
interrupt vector to a routine that increments a counter and then RTEs.
3) After the critical section, blockinterrupts (at IPL 6)and calla systemclock
handler that jumps through the interrupt vector with a fake SR and return
address on the stack,the number of timesindicatedby the counter.
Animation
Animation is most easily achieved by switching alternately between two
screens; one on display, the other being updated in the background. Initially
write two identical screens and display one while modifying the other, swap the
screens over and display the modified screen while updating the one previously
on display. The technique will produce a very stable display with quite slow
switching rates.
2.15

<!-- source-page: 68 -->
## Page 68

The Concise Atari ST Reference Guide
Sound concept overview
Sound is generated via a Yamaha YM2149 programmable sound generator.
The PSG contains three tone generators that produce the basic square wave tone
frequencies for the A, Band C channels and a noise generator, that produces a
frequency modulated pseudo random pulse width square wave, which may be
combined with the tone generator outputs using the channel mixer. The output
level can befixed via the channel amplitude control using one ofthe three sixteen
level D/A converters or varied by using the output of the envelope generator,
which maybe usedto amplitude modulate theoutputofeach mixer.
Sound control registers
The frequency of each tone generator (30Hz to 125KHz) is obtained by
counting-down the 12-bit value of the tone registers (the coarse register sets the
upper 4 bits and the fine register setsthe lower 8 bits, range 001H to FFFH (1 to
4095). The standard PSG format is to produce a lower note for a higher count
whenever a register count-down is performed.
The noise generator frequency is controlled by a 5-bit noise period register,
value01H to 1FH (1 to31), producing a frequency rangeof4Khz to 125Khz.
The mixer control register is a multi-function register that mixes the noise
channels (definedby bits 3 to 5)and the tone channels (defined by bits 0 to 2)in
all possiblecombinationsto the input/output ports (bit6 I/O, bit 7 port A or B).
The amplitude of a channel is controlled to one of sixteen fixed levels by the
channel D/A converter register (lower 4 bits of the register) and only by setting
the register to zero can the channel be turned off. The fifth bit of the amplitude
control register is set to select the variable level output defined by the envelope
generator.
The envelope generator comprises of three registers, two provide the
frequency variation and the third the format of the envelope. The frequency is
determined by counting down the 16-bit value of the coarse and fine envelope
registers range 0001H to FFFFH (1 to 65535). The shape and cyclic pattern of the
envelope is defined by the lower 4 bits of the shape register (the amplitude
register setting the level), the four bits provide for combinations of hold/cycle,
reverse cycle on/off, ramp up/down and cycle hold pattern/reset to zero.
2.16

<!-- source-page: 69 -->
## Page 69

Operating System Overview
Parallel data I/O
The I/O register in the PSG is not associated with sound production, it
provides a register to transfer 8-bit parallel data to and from the CPU bus to the
I/O port A, there is no affect on any of the PSG's other functions.
Port A is controlled through functions 'ONGBIT' and 'OFFGBIT' (See page
B.4 for bit functions and 3.12 for calls).
Port B read/write is controlled through BIOS functions BCONOUT and
BCONIN (See page 3.4 for calls)
Data is written to a peripheral device from the bus using the following steps:
Select enable register (mixer register)
Set bit 6 to T (set I/O port A to output)
Select I/O port A data store (I/O port A register)
Write data to PSG (write data to I/O port A register)
Once data has been loaded into the register, the data remains until further
data is loaded, the system is reset, or
the register is switched to input mode.
Data is read from a peripheral device to the bus with the following steps:
Select enable register (mixer register)
Set bit 6 to '0' (set I/O port A to input)
Select I/O port A data store (I/O port A register)
Read data from PSG (read data in I/O port A register)
The register follows signals applied to the port, only by reading will the data be
transferred to the bus.
2.17

<!-- source-page: 70 -->
## Page 70

The Concise Atari ST Reference Guide
Sound configuration registers
Access to the PSG should be in supervisor mode as the SR register is
modified. The PSG registers are located for write at address ($FF8800-16746596)
as follows:
offset
Channel A fine tune
(8 bit)
Channel A coarse tune
(4 bit)
Channel B fine tune
(8 bit)
Channel B coarse tune
(4 bit)
Channel C fine tune
(8 bit)
Channel C coarse tune
(4 bit)
Noise generator control
(5 bit)
Mixer control, I/O enable
(8 bit)
Channel A amplitude
(5 bit)
Channel B amplitude
(5 bit)
Channel C amplitude
(5 bit)
Envelope period fine tune
(8 bit)
Envelope period coarse tune
(8 bit)
Envelope shape
(4 bit)
I/O port A
Tone frequency calculations (registers 0 to 5)
The tone frequency is in the range 30.5Hz to 125Khz and may be calculated from
the formula:
(=
2JLID6
16*(256 * CT + FT)
where
CT=coarse tone period
FT=fine tone period
Noise frequency calculations (register 6)
The noise frequency is in the range 4Khz to 125Khz and may be calculated
from the formula:
.
f = 2*106
16*Np
where
Np=noise period
0
$0
1
$1
2
$2
3
$3
4
S4
5
$5
6
$6
7
$7
8
$8
9
$9
10
$A
11
$B
12
$C
13
$D
14
$E
2.18

<!-- source-page: 71 -->
## Page 71

The mixer control I/O enable
(register 7) bit functions take
the following format:
0
1
2
3
4
5
6
7
Tone
channels
Noise
channel;
I/O
port
ABC
A
B
C
A
B
If the bit is zero
the channel is on
If bit (i
port i/o
Envelope calculations
Operating System Overview
The channel amplitude
(registers 8-11) bits have
the following function:
I- I- I- I Mlx I x| x| x|
M = 0 Fixed amplitude level
0-lowto 15-high (xxxx)
M = 1 Amplitude determined
by envelope shape
Period
The envelope period (registers 11 & 12) of the shape is based on the 16-bit
register value:
fe =
fclock
where Ep =envelope period
fclock =i/p clockfrequency
256 * Ep
Shape/cycle
The envelope shape/cycle control (register 13) bit settings produce the
following range of sound envelopes:
Bits
3
2 10
Function
Bits
3
2 10
Function
0
0
x
x
0
1
x
x
10 0
0
10 0
1
10 10
\
10 11
110 0
110
1
1110
1111
7\\
A_
Bit 0 = Hold/_cycle
Bit 1 = Reverse on/_off
1 bit set
0 bit clear
x don't care
Bit2 = Ramp up/_down
Bit3 = Cycle hold/_reset zero
2.19

<!-- source-page: 72 -->
## Page 72

The Concise Atari ST Reference Guide
GEM disk operating system GEMDOS
Overview
For those systems supplied with the operating system on disk; the system
disk contains on the first two tracks, a cold start loader that loads the operating
system image file (TOS,IMG) into high memory and then block loads it down
into RAM memory at address $5000.
The TOS image file contains both the GEM and Atari ST extended operating
systems, including:
BDOS Basic disk operating system
Access functions to the file system
BIOS Basic I/O system
-Functions that interface peripheral device drivers
The operating system is always in memory above $400 and all modules
reside permanently in memory, even those of disk based systems (unless the
power is removed). After TOS is loaded, the remaining contiguous address space
is called the transient program area (TPA) where TOS loads
executable
(command) files. The command files (programs) should not access absolute
addresses or default TOS variables but use the BIOS and GEMDOS function calls,
except those system variables documented in Appendix A (upto address $04xx).
Each transient program loaded into memory consists of the program
segments (Text, Data and BSS), a user stack and a Base Page. The 256 byte Base
Page contains the direct memory address (DMA) buffer, at base page offset $80;
the buffer contains the command tail, typically the input typed to an application
installed as a TOS Takes Parameters program. Before the loaded program takes
control, the address of the transient programs base page and a return address are
pushed onto the user stack, 4(A7) and (A7) respectively.
Although the OS can only load one program; the transient program itself can
load further programs using GEMDOS function $4B, but must specifically supply
the base page and return address if they are required.
A return from a transient program may be achieved by:
An RTS as the last statement, returning via the return pushed onto the stac
the load function.
Execute warm boot by calling extended BDOS function 0.
Type Control_C from the console during the execution of console
output, printing a string or reading from the console buffer (functions 2,9 and 10)
2.20

<!-- source-page: 73 -->
## Page 73

Operating System Overview
GEMDOS Memory model
Low memory
0
Exception
vectors
System
Base paqe
\
/
Text
Data
Loaded
BSS
transient
GEMDOS
application
Free
memory
program
User stack
ST OS
BIOS
System
High memory
BDOS
Command file
The format of a command file is that of a header, two program segments (text
and initialized data segments) and optionally a symbol table and relocation
information. After the program is linked and loaded into memory, it contains
additionally a zeroed uninitialized data (BSS) program segment and starts
execution at the beginning of the text segment.
Not all assemblers provide for an uninitialised data section within the source
code, this results in executable GEM based program files on disk that are much
larger than necessary.
The operating system holds information on the data segments in a descriptor
block (256 byte base page data structure) at the bottom of the TPA. The base page
does not reside at a fixed address, its position is determined when it is created by
the load a process function (GEMDOS function #$4B) and held in register DO.L.
The base page contents are initialized by the GEMDOS load function:
Base page format initialized by GEMDOS
$00
$04
$08
$0C
$10
$14
$18
$1C
0
Base address of TPA
4
End address of TPA + 1
8
Base address of text (code)
12
Length of text (code)
16
Base address of initialised data
20
Length of data
24
Base address of BSS uninitialised data
28
Length of BSS uninitialised data
2.21

<!-- source-page: 74 -->
## Page 74

The Concise Atari ST Reference Guide
There are slight differences between small sectionsof the original CP/M 68K
and GEMDOS base page formats as follows:
CP/M 68K format
$20
$24
$25
$38
$5C
$80
GEMDOS format
$20
$24
$28
$2C
$80
32
Length of free memory after BSS
36
Drive from which program loaded
37
Reserved by BDOS
56
2nd parsed FCB from command line \
Set
92
1st parsed FCB from command line
by
128
Command tail and default DMA buffer/
OS
32
DTA address pointer
36
Parent's base page pointer
40
Reserved
44
Pointer to environmental string
128
Command line image (typically the entry to a
dialog box for a TTP application)
File header format
GEMDOS file header and program segments take the format:
0
Data and BSS contiguous 601 AH
2
Number of bytes in text segment
6
Number of bytes in data segment
10
Number of bytes in BSS
14
Number of bytes in symbol table
18
Reserved
22
Reserved
26
Reserved
28
Beginning of text segment
NOTE that 601AH is a BRA.S instruction that bypasses the file header data
segment. The Atari OS does not support segmented files.
$00
$02
$06
$0A
$0E
$12
$16
$1A
$1Q
2.22

<!-- source-page: 75 -->
## Page 75

Operating System Overview
Symbol table
The symbol table consists of fourteen bytes that specify a null padded
character name, the type of symbol and the symbol value (address etc).
hex
Symbol type
$100
BSS
$200
Text
relocatable
$400
Data
$800
External reference
$1000
Equated register
$2000
Global
$4000
Equated
$8000
Defined
Relocation table
$00
ASCII
$07
name
null padded
$08
$09
Type.W
$0A
Value.L-
$0b
The linker optionally produces a relocatable executable file and places the
relocation information in the GEM file header.
GEMDOS header file
$1A
Offset. L
$1E
Offset 1
$1F
Offset 2
$20
$00
26
30
31
32
Byte
sized
offset
data
/
No more offsets
Longword
offset
Byte
offset 1
Byte
offset 2
Text
start
1st
2nd
3rd
Longword to relocate
2.23

<!-- source-page: 76 -->
## Page 76

The Concise Atari ST Reference Guide
If the offset byte is 1, then a multiple byte offset based on the following table
is used to determine the actual offset.
Offset
Relocation data
byte value
$00
End of relocation data
$01
Add 254 from current location and decode next byte
$02....$FE
Add byte value from current location
Other odd numbers are not used (reserved)
When the program is loaded into memory at a location other than where it
was linked, BDOS computes an offset and adds the offset to the address of the
relocation words in the text and or data segments.
GEMDOS function $4B (75 decimal) loads or executes a program.
2.24

<!-- source-page: 77 -->
## Page 77

Operating System Overview
Atari ST file system
GEM contains a fairly comprehensive sets of file manipulation facilities, they
enable the programmer to write software that provides multiple access file
sharing and file protection, periodic file updates and selective backups. The file
facilities are:
Code
GEMDOS function
Dec
Hex
60
3C
Create file
61
3D
Open file
Close file
Invoked by filling a
62
3E
parameter block with the
63
3F
Read a file
number of the function,
64
40
Write a file
the parameters and any
65
41
Delete file
other relevant data.
66
42
Seek file pointer
67
43
Get/set attributes
Returns are in DO.L
Zero indicates o'k
69
45
Duplicate file handle
Where data is returned,
70
46
Force file handle
DO contains the address
of the data return block
78
4E
Search for first
79
4F
Search for next
GEM uses the stack as
96
56
Rename file
the parameter block.
97
57
Get/set
date/timestamp
2.25

<!-- source-page: 78 -->
## Page 78

The Concise Atari ST Reference Guide
Atari ST disk system
The AtariST3 1/2" disk uses softsectoreddisks of the following format:
Bytes/sector
512
Sectors/track
9
Tracks/side
80
Sides/media
1
2
Unformatted
360K
720K
Kbytes
The GEM BIOS interfaces (Basic input/output systems) make the hardware
dependent interface to the floppy disk drives. These communicate with the drives
as follows:
Select the drive, the side, the track and then the number ofsectors from the track that
will be read toa buffer orwritten from the buffer tothe disk.
GEMDOS is fairly basic in terms of disk operations but has extensions to
handle tree type directories.
Code
GEMDOS function
Dec
Hex
14
0E
Set default drive
25
19
Get default drive
54
36
Get drive free space
57
58
59
71
39
3A
3B
47
Create a subdirectory
Delete a subdirectory
Set current directory
Get current directory
A file does not use consecutive disk sectors as there is insufficient time to
identify, read and or write a record via software, and to locate a specific track via
hardware. The record spacing (skew) is usually 6 sectors between adjacent file
segments.
2.26

<!-- source-page: 79 -->
## Page 79

Operating System Overview
Atari ST BIOS comparisons
The ST contains device dependant input/output utilities that handle the
interface between the device independant routines and the hardware, the ST
BIOS and GEM BIOS utilities are supplemented by the line-A primitives which
provide rapid screen control.
The GEM type BIOS handles the input/output to the peripheral devices:
parallel port, RS232 port, console, midi interface and intelligent keyboard. There
is also a basic disk read/write to sector and a facility to check that the disk has
not been removed or replaced.
The ST extended BIOS also controls the input/output to the midi interface,
intelligent keyboard, console and disk read/write, but additionally includes the
control of a mouse, joysticks, sound and of the screen colours.
The line-A routines are the VDI graphic primitives which are not program
transportable and therefore included here, they enable control of the mouse and
pixel-line-sprite-screen graphics.
Interrupt handler overview
The operating system provides the machine code programmer with access to
the interrupt handler.
Every l/50th of a second control is transferred from the operating system to
a routine at the address designated in the system variables at $68 (104 decimal),
the system interrupt handler (vertical blank interrupts). The handler provides a
timing facility, sets the screen parameters and current device driver installation
and entry points.
2.27

<!-- source-page: 80 -->
## Page 80

The Concise Atari ST Reference Guide
System Initialisation
The ST in general follows a predefined initialization sequence on power-up,
with variations for the different operating systems, typically:
System reset
ssp~>
$60xxxxxx
pc—>
$00FC0020
move.w
#$2700,SR
reset
cmpi.l
#$FA52235F,$FA
bne
cmpi nxt
lea
$8(PC),A6
jmp
$FA0004
cmpi.l
#$31415926,$426
bne
psgset
move.l
$42A,D0
tst.b
$42A
bne
psgset
btst
#$0,D0
bne
psgset
movea.l
D0,A0
lea
$4(PC),A6
jmp
(AO)
lea
$FFFF8800,A0
move.b
#$7,(A0)
move.b
#$C0,$2(A0)
move.b
#$E,(A0)
move.b
#$7,$2(A0)
move.b
#$0,$FFFF820A
lea
$FFFF8240,A1
move.w
#$F,D0
lea
$28A(PC),A0
move.w
(A0)+,(A1)+
dbf
D0,loop
2.28
The supervisor stack pointer (SSP) and
program counter (PC) are set from $0
and $4 respectively, the SSP is
garbage until the system is sized. The
Interrupt priority level (IPL) is set
to seven and a hardware reset executed
A check is made for a diagnostic
cartridge, which if present will cause
a return address to be set in A6 and
execution of the diagnostic routines
commenced.
A check is made to see if memory has
previously been sized (warmstart). If
not jump past memory sizing routine.
If this is a soft reset, the bailout
vector may be valid. First check that
the MSBis zero, secondly that the
vector is to an even address, if not,
jump past the reset handler.
Set AO to point to the reset handler,
set A6 to the return address and
jump to reset handler.
Set AO to PSG configuration register
base and set port A & port B to output,
activate general purpose output and
through output port A deselect the
disks.
Set sync mode to external 50/60Hz and
Al to base of pallette table.
Set up a count in DO to shift the
default hardware palette colors to
AO which points to the default color
table.

<!-- source-page: 81 -->
## Page 81

move.l
move.l
move.l
lea
move.l
move.l
move.l
move.l
move.l
move.l
move.l
move.l
move.l
move.l
suba.l
suba.l
move.w
lsl.w
move.w
bsr
and.l
btst
beq
ddq.w
movea.l
suba.l
move.l
move.l
rts
move.l
subq
clr.b
dbf
#$752019F3,$420
#$237698AA,$43A
#$8900,$432(A5)
$D50,A7
rte,$14
#$FC0324,$70(A5)
rte,$68(A5)
rte,$88(A5)
#$FC03C0,$B4(A5)
#$FC03BA,$B8(A5)
rts, $400(A5)
#$FC03B6,$404(A5)
rts,$408(A5)
#$550,$4A2(A5)
A5,A5
A5,A5
$454(A5),D0
#2,D0
D0,D1
make_spc
#$FFFF,D0
#$0,D0
jumpl
#$1,D0
$436,A0
D0,A0
A0,$436
A0,D0
A0,$456(A5)
#$1,D1
(A0)+
Dl,clr_byte
Operating System Overview
Size both memory banks and perform a
memory test. Set 'memory sized' and
'memory tested' flags in the system
variables table. Set up screen, vblank
queue entries, BIOS entry point and
supervisor stack.
Run type '0' cartridge applications.
Point A3 and A4 at RTE and RTS resply
Test diagnostic cartridge.
Initialise exception vectors to
terminate process handler except for
divide by zero which is RTE'd.
Set vblank handler entry address.
Kill hblank handler entry address.
Initially empty trap#2 handler.
Set up trap#13 handler address.
Set up trap#14 handler address.
Default timer tick vector to RTS.
Set up the critical error handler
and default the terminate vector.
Set up BIOS register save area pntr
Zero page pointer.
Intialize vblank vector list.
8 nvbls into DO
multiply by four to
create queue length in Dl.
Routine to create a space of
8 longwords in high memory.
\make
Iaddress
/even
current memory top
'come on down'
reset memory top
and put in DO
vblqueue start address
I zero the queue
/
2.29

<!-- source-page: 82 -->
## Page 82

The Concise Atari ST Reference Guide
Initialize screen resolution,
move.w
#$F8FF,SR
2.30
Enable all interrupts except Hblank
by setting IPL to 3.
Run type T cartridge applications
InitializeGEMDOS- set up a DOS
disk buffer chain &memory manager.
Run type '3' cartridge applications
Attempt to boot from floppy and
executeif successful,if not poll
devices on DMA bus for logical boot
sector zero, execute if successful,
(checksum$1234). Any 'returns'
continue pollingthedevices in sequence.
Turn on the cursor.
Execute file COMMAND.PRG? otherwise
construct a default environment and
execute AES.
Initiate a RESET on a return.

<!-- source-page: 83 -->
## Page 83

Operating System Overview
Cartridge Software
There are two types of cartridge which may be plugged into the ST;
diagnostic and program cartridges. The cartridge program header format is as
follows:
c_flag
$00
c_next
$04
c_init
$08
c_run
$0C
cjime
$0E
c_date
$10
c_bsiz
$14
c_name
4
Only the first header contains a flag which denotes the
presence of a cartridge.
Flag: #$FA52255F=diagnostics
#$ABCDEF42=program/data
0
Pointer to next application header, a null indicates no
additional applications
4
Pointer to application initialisation code, if zero there is no
initialisation code. The longword high byte is unused in the
24-bit address and starts applications as follows:
bit 0-set, run before interrupt vectors & memory initialised
bit 1-set, run before GEMDOS initialised
bit 2-unused
bit 3-set, run before disk boot
bit 4-unused
bit 5-set, application is a desk accessory
bit 6-set, not a GEM application (no AES calls)
bit 7-set, needs command line parameters before execution
8
Pointer to application entry point
12
Time
14
Date
DOS format time and date stamps
16
The size of the application BSS segment allocation. The OS
must allocate the BSS before invoking any run code. Set to
zero if not applicable.
20
The ASCII name (max 12 characters) terminated by a zero
nnnnnnnn.eee
Diagnostic cartridge: The ST hardware will not be initialised and a return
address is held in A6, the stack pointer is trashed. The cartridge software is
responsible for sizing memory and setting the hardware registers as required.
Cartridge software: Application headers are strung together in a linked list,
so there may be any number of applications on one cartridge.
2.31

<!-- source-page: 84 -->
## Page 84

The Concise Atari ST Reference Guide
Boot Sectors
To write software that will auto run from disk, the programmer must
produce a boot sector that contains a loader program which transfers the
program fromdisk to memorybeforebringingup GEM.
The boot sector follows IBM PC format and contains:
The volume serial number
24 bit number generated when the media is formatted
BIOS parameter block (BPB)
Sector size in bytes
Number of sectors/cluster
Cluster size in bytes
Length of root directory in sectors
Size of a File Allocation Table (FAT-in sectors)
Sector# of start of second FAT
Sector# of first data sector
Number of data clusters on disk
Flags
Optional boot code and boot parameters
During initialization the boot sector is loaded into a buffer and the executable
boot sector code tested for a word checksum of #$1234. If satisfactory a
subroutine jump is made to the beginning of the position- independent code in
the buffer.
When a 'get BIOS parameter block' call is made, the BIOS reads the boot
sector (normally created when the volume is formatted), and returns an error
indication if any critical parameter fields are zero.
The 24-bit volume serial number, written when the media is formatted, is
used to determine whether or not a disk has been changed.
The 'protobt' extended BIOS call (dec 18) is used to create the boot sector (pg
3.8), which is written to track_0 side_0 sector_l.
2.32

<!-- source-page: 85 -->
## Page 85

Operating System Overview
BIOS boot parameter block
Normally written when the volume is formatted.
$00
$02
$08
$0B
$0D
$0E
$10
$11
$13
$15
$16
$18
$1A
$1C
$1E
$1FE
$200
bra.s
oem_space
Vol serial*
#$000000
BPS
#$00 #$02
SPC
#$02
RES
#$01
#$00
NFATS
#$02
NDIRS
#$70 #$00
NSECTS
#$D0 #$02
MEDIA
#$F8
SPF
#$05 #$00
SPT
#$09 #$00
NSIDES
#$01 #$00
NHID
#$00 #$00
boot code
last word
0
Branch to boot code
2
Space reserved for OEMs use
8
24-bit volume serial number.
(used to determine disk changes)
11
Number of bytes/sector
13
Number of sectors/cluster
14
Number of reserved sectors
(at start of media including boot)
16
Number of file allocation tables on media
17
Number of directory entries
19
Number of sectors on media
(including reserved)
21
Media descriptor
(not used by ST)
22
Number of sectors/FAT
24
N1, imber of sectors/track
26
Number of sides on media
28
Number of hidden sectors
(not used)
30
Start of code, if any
510
Checksum
512
Note: Word storage is low byte at the low address (even) as per Intel 8088 format
and not the usual 68000 mode.
The BIOS parameter block is compatible with MS-DOS versions of the BPB, but
will only read and write sectors written by another WD1772A disk controller.
2.33

<!-- source-page: 86 -->
## Page 86

The Concise Atari ST Reference Guide
Boot loader
The boot loader resides in the boot sector and is used during system
initialization to load an image file or a contiguous set of sectors; it is also used to
load GEM from disk on early STmodels. The format of the loader is:
$00
boot sector
$1E
execflq
$20
Idmode
$22
ssect
$24
sectcnt
$26
Idaddr
$2A
fatbuf
$2E
fname
$39
reserved
$3A
boot code
0
The standard BIOS parameter block
30
The word copied to 'cmdjoad' flag
32
If lmode=0 load file
34
If ImodeoO load from here
36
If ImodeoO load 'sectcnt' sectors
38
Load address of file or sectors
42
Address for FAT and DIR sectors
46
Filename: 8 Character name. 3 Character extension
(valid if 'Imode' is zero)
57
Reserved
58
The executable code
Some software tools require the six bytes reserved for OEMs at offset $2 to
contain the ASCII text 'loader'.
The loader can load any file from disk regardless of where it appears in the
directory or whether it has the form of contiguous sectors or not.
An image file contains no header or relocation information and is an exact
copy of the program to be executed.
2.34

<!-- source-page: 87 -->
## Page 87

Operating System Overview
Boot ROM
The initialization of the system from the boot ROM follows the predefined
pattern of a RESET with some system variables installed and pretty color screen
graphics to keep the operator from getting bored.
The boot directory and second FAT buffer are read into memory starting at
membot. TOS.IMG is loaded starting at $40000 and an error code produced if the
file is not found. The memory $10000 to $20000 is used for screen buffers and
should not be used initially for any code or data.
The first ST's sold contained a small 32K boot ROM that loaded the operating
system from disk. The boot ROM contains a small sub-set of the BIOS, just
sufficient to read an 80 track, BPB floppy disk boot sector from either drive into
memory and then execute it.
Trap 13 GEM BIOS functions implemented
code
function
4
rwabs
Read/write sectors (read only)
7
getbpb
Get BIOSparameter block
Trap 14 extended functions implemented
code
function
1
ssbrk
Reserve x bytes from top of memory
8
floprd
Read sectors from floppy disk
All other BIOSfacilities are not loaded into the system until a later stage. The
first 100 bytes of disk TOS relocate TOS.IMG at $5000 from where it takes control.
The first TOS implementation uses the following disk parameters:
80 track, single sided BIOS parameter block
Bytes/sector
512
#sides/media
1
Sectors/cluster
2
#hiddensectocrs
0
Reserved sectors
1
Load address
$40000
# of FATs
2
FAT/directory buffer
$8000
# of root dir entries
7
Volume serial number
0
# of sectors on media
720
Media descriptor byte
F8H
# sectors/FAT
5
Filename
TOS.IMG
# sectors/track
9
2.35

<!-- source-page: 88 -->
## Page 88

The Concise Atari ST Reference Guide
Atari ST peripheral device
communications
Communications overview
The ST supports serial and parallel communications through dedicated
RS232 and parallel ports, and permits two further communicaton channels to be
opened through the MIDI and DMA ports.
The serial RS232 communication port accomodates hardware data control
based on the PSG I/O port A, RTS and DTR outputs, and the MFP MK68901,
CTS, DCD and RI inputs, and Xon/Xoff software data protocol at transmit and
receive baud rates in the range 50 to 19200 baud. The port is generally used to
interface with a printer, modem or another computer. The MFP is located at
$FFFA00 (16775680) and the $PSG at $FF8814 (16746610).
The general purpose parallel port interface provides bi-directional 8 bit
communications for printer operation. The port is based on the MFP MK68901
(busy control), the PSG I/O port A bit 5 (strobe control) and the PSG I/O port B
(data transfer). The control is limited to a busy signal, acknowledge is not
supported and data transfer is at a typical rate of 4000bytes/s.
The MIDI interface provides an asynchronous, current loop, serial data (one
start bit, eight data bits and one stop bit) communications channel at 31.25Kbaud.
The MC6850 port controller may be reconfigured for most forms of RS232
interface via the control/status register situated at address $FFFC04(16776196).
The intelligent keyboard interface is also controlled by an MC6850 ACIA, but
there is no external access provided to the port, which is of limited use other than
accessing the ikbd command set; for reading and or writing to the clock, joysticks,
mouse and perhaps reconfiguring the keyboard. The transfer rate is fixed at
7812.5 baud.
The floppy disk interface is based on the Western Digital WD1772A disk
controller and is limited to supporting two drives.
The DMA interface is provided by a ULA device, access is through the
control/status configuration registers at $FF8600 (16746084) et seq. The DMA or
Hard disk port uses an Atari version of the SCSI interface and can support a
maximum of 8 peripheral devices. Theoretically data may pass either way
through the interface so it should be possible to use it for high speed networking,
remembering that the DMA controller also supports the Floppy Disk Controller.
2.36

<!-- source-page: 89 -->
## Page 89

Operating System Overview
RS232 interface
General
Data is transmitted and received via an RS232 interface as a sequence of ones
and zeroes (bits) along a three wire link, one wire being ground, one for
transmitted data and the other for the received data. Information is sent as
'characters' and each character is prefixed by a start bit (a one) and terminated
with either one or two stop bits (zeroes). Providing the sending and receiving
devices are set to the same speed (baud), then the stop and start bits act as a
timing
signal
to
each
'character'
sent.
Occassionally
error
detection
is
incorporated in the form of a parity bit. If the count of ones in the character is
even, then the eighth bit is set to a one (even parity), an alternative process is odd
parity where if the one count is odd, the eighth bit is set to a one. Personal
computers work without parity which is used in general as a warning of data
errors in the transmission. Providing the transmitting and receiving station agree
on the protocol used, then communications will be reasonably straight forward !!!
The portis reconfigured using thesequence:
a)
Save current MK68901 register contents
b)
Disable Rx and Tx enable bits
c)
Set flow control mode
d)
Set baud rate
e)
Set RS232 registers
f)
Re-enable Rx and Tx enable bits
The extended BIOS call #$0F (15) enables selective reconfiguration of the
RS232port according to a block of parameters pushed onto the stack:
move.w
sync_char,-(SP)
*Pushing
\
move.w
tx_status,-(SP)
* -1
I (page
move.w
rx_status,-(SP)
* leaves
I 3.10)
move.w
usrt_cntl,-(SP)
*parameter
I
move.w
flow_cntl,-(SP)
*unchanged
/
move.w
baud_rate,-(SP)
* Set timer D
move.w
#15,-(SP)
*push RS232 config
trap
#14
*call function
add.w
#14,SP
*tidy stack, jump 7 words
tst.w
DO
* test for error
rts
Data is passed through the interface using the extended BDOS calls to the
auxiliary device (RS232 port). Only the 'New
TOS' supports RTS/CTS
handshaking.
2.37

<!-- source-page: 90 -->
## Page 90

The Concise Atari ST Reference Guide
Parallel port interface
General
Data is transmitted and received via a parallel port interface in blocks of 8
(sometimes 7) data bits, set eitheras ones or zeroes to form a character byte. The
character is 'framed' by a strobe signal enabling the receiving device to read the
character transmitted, which maybe printed immediately or savedin a buffer for
subsequent printing. At some stage theprinter will not be able to accept further
input and will send a 'busy' signal to stop the transmitter from sending
additional data. The acknowledge signal is sometimes used to indicate that the
printeris no longer busy,occasionally this signal line isomitted and thebusyline
also provides the 'not busy' signal.
Datais passedto and from the interface usingthefollowing procedures:
Write data
a)
Checkthe busy linefor high
Ifline low, monitor until high
or time out set CPU DO register to 0
When high
b)
Set PSGI/O B port to output, use IPL7
c)
Place data intothe PSG's Boutput register 15
d)
Switch strobe line on, Port A bit 5
e)
Switchstrobelineoff, set CPUDO registerto -1
Read data
a)
Set PSG I/O Bport to input
b)
Switch strobe line off
c)
Checkbusy linefor highloop tillhigh
d)
Switch strobe on
e)
Get data from PSG's Boutput register
As the status register is affected, the above procedures should be performed
in supervisor mode.
2.38

<!-- source-page: 91 -->
## Page 91

Operating System Overview
MIDI interface
General
The MIDI (musical instument digital interface) sequential circuits provide for
integrated operation of music synthesizers, sequencers, drum boxes etc. which
have the MIDI interface. The ST operates as a data store for a large number of
notes/voices which may be sent to different instruments (channels), and played
together in sequence and time as music. The data may be 'recorded' from a tune
previously played, edited and/or synthesized by entering new data in steptime-note format into the store for later retrieval.
The MIDI bus provides 16 channels in one of three networking modes.
OMNI, the default where all units are addressed together and transmit and
receive on all channels. POLY where all the units are individually addressed and
receive on one channel only, data assigned to non-existant channels is ignored.
MONO where the voice of each unit is addressed seperately, providing different
channels for individual voices within one synthesizer.
The information transmitted is priortised and sent as bytes, the most
significant bit signifying either status (1) or data (0). The priority order is:
System reset
Set defaults
System exclusive
Manufacturers unique data
Sequential circuits
Roland, Yamaha etc.
System real time
Synchronization
System common
Broadcast
Channel
Note selection, prog data etc.
The MIDI port supports the optional through port which merely provides the
MIDI in signals at the MIDI out port.
The MIDI interface operate in RS232 current loop mode at 31.25K baud. It
may be reconfigured by resetting the control/status registers.
The Atari ST's extended BIOS enables the programmer to reconfigure the
MIDI port.
2.39

<!-- source-page: 92 -->
## Page 92

The Concise Atari ST Reference Guide
MIDI control/status register functions
Controlregister functions (write only) $FFFC04
Divide
Bit selec
0 1
0 0
by 1
0 1 by 11
1 0 by "
Bit
Data format
Bit RTS format Bit
Interrupt
2 3 4 #bit Parity Stop 5 6
Tx on/off
7
enable
000
00 1
1 0
0 1 1
00
1 0 1
1 1 0
1 1 1
640
7
even
2
7
odd
2
7
even
1
7
odd
1
8
-
2
8
-
1
8
even
1
8
odd
1
0 0
off
RTS=
0 1 on
low
1 0
off
RTS:
high
1 1
off
RTS=
low
Tx break level
on Tx data o/p
Interrupts
enabled by
bit 7 - 1.
Rx data
register full,
Overrun,
DCD low to
high step.
1 1 master!
reset
Status register functions (read only) $FFFC06
Bit
Name and function
0
1
2
3
4
5
6
7
2.40
Rx data register full
Rx data in register ready for CPU read
Tx data register empty
Transmitted data sent, load with next character to transmit
Data carrier detect
Indicates modem state, carrier present
Clear to send
Indicates modem state, Master reset - no change.
Frame error
Character synchronisation error
Rx over-run
Characters have been lost from stream
Parity error
Only active if parity selected
Interrupt request
Read received data register or write to transmit data register.

<!-- source-page: 93 -->
## Page 93

Operating System Overview
Intelligent keyboard interface (IKBD)
The intelligent keyboard functions through a MC6850 ACIA device whose
control/status register is located at address $FFFC00 (16776192), and functions
like the MIDI interface. There is no external access to this port so there is little
point in reconfiguring, but it can be used to transmit and receive data or
commands from the keyboard, mouse, joystick and clock using the following
facilities:
Keyboard
Return keycodes
Mouse
Setmousebutton action (keys, onpress/on release)
Set mouse position relative (default)
Set threshold level per 'click'
Set mouse position absolute
Set scale ('clicks' per movement)
Read/write mouse position
Set mouse to simulate cursor motion codes
Set Y origin top/bottom
Disable/pause/resume mouse operation
Joystick
Enable joystick (default)
Disable, act on request only
Interrogate joystick
Set monitoring
(serial line, joystick and clock)
(serial line, button 1 and clock)
Set keycode mode (variable 'click' rate)
Disable joystick
2.41

<!-- source-page: 94 -->
## Page 94

The Concise Atari ST Reference Guide
Clock
Set date and time
Read date and time
Program control
Load data into ikbd memory
Read data from ikbd memory
Execute ikbd program
A status inquiry command returns a null padded 8-byte packet detailing the
current mode and parameters of a specific function, the packet may be stored and
later used to restore the status of the keyboard by modifying the header byte and
returning the data as a command.
The keyboard scancodes do not maintain complete compatibility with IBM
PC key scancodes. Appendix D.6 provides the major differences due to the non
availability of certain keys on the ST keyboard. The additional ST keys are
mapped into unused CTL_ and ALT_ function scancodes.
To detect ALT_ and CTL_ function key combinations, execute a BDOS or
BIOS 'getchar' call followed by a BIOS 'kbshft' call (#$0B).
2.42

<!-- source-page: 95 -->
## Page 95

Operating System Overview
Floppy disk interface
The floppy disk interface is based on an on-board Western Digital WD1772A
disk controller and can support a maximum of two drives.
Thefloppy disk read/write sequence ofevents is:
a)
select floppy drive 0 or 1 (PSGI/O port A)
b)
select floppy side 0 or 1 (PSGI/O port A)
c)
load DMAbase address and counter register
d)
toggle read/write to clearstatus (DMA mode control reg)
e)
select DMA read or write (DMA mode control register)
f)
select DMAsector count register (DMAmode control reg)
g)
selectFDCinternal command reg (DMA mode control reg)
h)
issue FDCread or write command (Diskcontroller reg)
i)
DMA active until sector count zero (DMAstatus reg)
do NOT poll during DMA active,
j)
issue FDCinterrupt command after sector data transfers,
except at track boundaries (Disk Ctrl reg)
k)
CheckMFPbit 5 ($FFFA01) for interrupt
1)
checkDMAerror status, non destructive (DMA stat reg)
The DMA configuration registers are at the base address $FF8600 (16746084)
and the following offsets:
Disk controller data access
DMA read_mode control, write_FIFO
DMA base high
\ set last
DMA base medium
I
DMA base low
/ set first
The PSG configuration registers are at base address $FF8800 (16746596) and
the following offset:
2
$2
PSGwrite port
Bit 0 floppy side
Bit 1 floppy drive 0
Bit 2 floppy drive 1
There is no hardware support for sensing disk removal, therefore this facility
must be performed in software.
4
$4
6
$6
9
$9
11
$B
13
$D
2.43

<!-- source-page: 96 -->
## Page 96

The Concise Atari ST Reference Guide
disk:
Formatting a floppy disk
The following procedure illustrates the technique used in formatting a floppy
flopfmt $A
Sides: 1 or 2
Sectors/track: 9
Tracks: 80
No interleave and the first two tracks zeroed (to 0 FAT and
directory sectors), either sector bad and the media is unusable
Use disk type parameter 2 or 3
Drotobt $12
Serial number parameter, random or #$1000000
M
f
Executeflag usually zero, non zero if itcontains loader code
etc. that is to execute when the disk is booted.
flopwr $9
Write boot sector (prototyped in buffer to track 0, side 0,
sector 1 of disk
Do not use 'rwabs' call
XBIOS calls
The WD1772 'write track' codes used to format a track are:
Double density format: issue a write track command and load the following
values into the data register. There is a data request for every byte written.
^
ID field
^
#bytes
data #$4Fj#$0fl#$F3#$FE
60
12
ID
Trek
#
Side
#
Sect
#
0-$4F
0-1
1-9
Len
#
#bytes 22J 12
3
ID
512
dataJ$4F#$00#$F5#$Frldatal
CRQCRG 40
1
2 |#$4E|
^- Data field
—"^
* length = #512 bytes/sector (usually 2)
CRC's written $F7
Note that early versions of TOS do not report CRC errors in all cases causing
reduced reliability of the disk system.
2.44
CRQ
RCJ,
140
[#$4
End of
track

<!-- source-page: 97 -->
## Page 97

Operating System Overview
WD1772 DMA channel interface
The WD1772 is interfaced through the DMA channel via the following
procedure:
To initialize the WD1772:
move.w
move.w
move.b
move.b
move.b
#$190,$FF8606
#$90,$FF8606
#xx,dmalow
#xx,dmamid
#xx,dmahigh
Clear the fifo by toggling r/w
and leave in the write state.
Set up dma address pointer in
low to high order
$FF860D, $FF860B &$FF8609 resply
The following addresses are used by the WD1772
$80
128
command/status register
$82
130
track register
$84
132
sector register
$86
134
data register
To address the WD1772:
move.w
move.w
delay
rts
#$yy,$FF8606
The FDC rquires two writes to
#$zz,D7
accessthe registers, the first
write selects the FDC register
and the second write modifies
the register
To transfer from memory to floppy the values must be ORed with #$100 and
#$FF writtento $43E toprevent TOS from changing thevaluein address $FF8606.
When the operationis complete the byte in $43E, the floppy lock variable, must
immediately be zeroed.
To seek to a track:
move.w
#$86,$FF8606
Select the data register
move.w
#$4F,$FF8604
Write seek track ($4F last track)
move.w
#$80,$FF8606
Selectcommand register
delay
Wait for drives
move.w
#$17,$FF8604
Seek with verify (pg 1.23 Type 1 command)
2.45

<!-- source-page: 98 -->
## Page 98

The Concise Atari ST Reference Guide
The FDCwill generate an interrupt when the seek is finished, it can be polled
at $FFFA01 where bit 5 is zeroed. Errors are read from $FF8604, the read clearing
the interrupt bit.
To transfer data:
move.b
#$xx,dma
set up dma address, clear fifo
move.w
#$190,$FF8606
move.w
#$1,$FF8604
512byte size limit of transfer write sector# (1..9)
write track* (#$00.#$27)
use #$A6
write track# (#$28.#$4F)
use #$A4
read track*,
use #$84
Do not use read/write multiple sector commands as they require a force
interrupt command which is slower than re-executing a read or write.
To format a track
write track* (#$00,#$27)
use #$F6
write track* (#$28,#$4F)
use #$F4
Write data to the drive beginning and ending with the index pulse. It takes
about #$1A00 bytes to fill a drive running at 3%.
The existing format command produces 9 sectors per track.
Do not change the id-field, the fourth byte is used to count the number of
bytes to transfer, and
to locate the CRC data
field. It may produce
incompatibilities with TOS if changed.
To write an entire track:
The entire track can be written as one long sector and then read back, without
any errorchecking, usingtheread trackcommand ifthefollowing format is used:
Index pulse followed by
#$00
a minimum of 12 bytes for lock-on
#$F5
3 bytes for synchronization
2.46

<!-- source-page: 99 -->
## Page 99

Operating System Overview
DMA interface
There is only one direct memory access (DMA) channel which is shared by
both low and high speed 8 bit device controllers. The configuration registers hold
the 3 register MMU base address of the DMA operation which is performed
through a 32 bit FIFO programmed by the DMA mode control register.
The hard diskread/write sequence ofeventsis:
a)
load DMA base address
b)
toggle read/write toclear status(DMA mode Ctrl reg)
c)
select DMA read or write (DMA mode control register)
d)
select DMA sector count register (DMA mode cntrol reg)
e)
load DMA sector count register (DMA mode trigger)
f)
select HDC internal command reg (DMA mode control reg)
g)
issue HDC read or write command (Disk controller reg)
1st cmd AO set to 0, set to 1 for remaining commands
Each byte command is acknowledged with an interrupt
After last cmd byte set hard disk sector count bit 1
h)
DMA active until sector count zero (DMA status reg)
do NOT poll during DMA active,
i)
check DMA error status, non destructive (DMA stat reg)
j)
check HDC status byte and if necessary perform an ECC
correction following a verify track or read sector command.
The DMA configuration registers are at the base address $FF8600 (16746084)
and the following offsets:
4
$4
Disk controller data access
6
$6
DMA read_mode control, write_FIFO
9
$9
DMA base high
11
$B
DMA base medium
13
$D
DMA base low
The DMA registers are used to perform the floppy disk data transfers but
may also be used for hard disk and other high speed data interfaces, bearing in
mind the restriction of one DMA operation at a time.
Any modification of the DMA base address or counter register requires that
they be set in low-mid-high order.
2.47

<!-- source-page: 100 -->
## Page 100

The Concise Atari ST Reference Guide
DMA bus boot code
The following code, which is typical of the ST's BIOS, attempts to loadboot
sectors from devices on the DMA bus. The code shows typically how the DMA
bus is used and provides the timeout and the command characteristics expected
from bootable DMA bus devices.
gpip
equ
$FFFFFA01
*.B
68901 input register
dskctl
equ
$FFFF8604
*.W controller data access
fifo
equ
$FFFF8606
*.W DMA mode control
dmahigh
equ
$FFFF8609
*.B
DMA basehigh
dmamid
equ
$FFFF860B
*.B
DMA base mid
dmalow
equ
$FFFF860D
*.B
DMA base low
flock
equ
$43E
*.W DMA chiplock variable
dskbuf
equ
$4C6
*.L
IK disk buffer
Hz_200
equ
$4BA
*.L
200 Hz counter
bootmg
equ
#$1234
*.W boot checksum
Try to boot from DMA device
dmaboot
moveq
#0,D7
dmb_l
bsr
dmaread
bne
dmb_2
move.l
dskbuf,A0
move.w
#$00FF,D1
moveq
#0,D0
dmb_3
add.w
(A0)+,D0
dbra
Dl,dmb_3
cmp.w
#bootmg,D0
bne
dmb_2
move.l
dskbuf,A0
jsr
(AO)
dmb_2
add.b
#$20,D7
bne
dmb_l
rts
Try to read DMA bus device boot sector
dmaread
2.48
lea
lea
st
move.l
move.b
move.b
move.b
fifo,A6
dskctl,A5
flock
dskbuf,-(SP)
3(SP),dmalow
2(SP),dmamid
l(SP),dmahigh
*# devices to try (eight)
* try to read boot sector
* failed —next device
*disk buffer pointer in AO
* checksum #$100 words
* initialize checksum
* add a word
* until #$100 counted
* Is it a boot sector
* No ~ next device
*disk buffer pointer in A0
* run the code.
* next device
*DMA control register
*DMA data register
*DMA lock against vblank
*set up DMA pointer

<!-- source-page: 101 -->
## Page 101

Operating System Overview
addq
#4,sp
*
move.w
#$098,(A6)
*toggle r/w, leave at read
move.w
#$198,(A6)
*
move.w
#$098,(A6)
*
move.w
#1,(A5)
*write sector count reg - 1
move.w
#$088,(A6)
* DMA bus select (not SCR ?)
move.b
D7,D0
* D0.1 to device* + command
or.b
#$08,D0
*
swap
DO
* D0.1=xxxxxxxxDDD01000
move.w
#$088,D0
*
xxxxxxxxOl0001010
bsr
wcbyte
* write cmd and wait for IRQ
bne
dmr q
* error exit on timeout
moveq
move.l
#3,D6
*write cmd $00
#$00008A,D0
*
cntl $8A
dmr_lp
bsr
wcbyte
*
four times
bne
dmr_q
* error exit on timeout
dbra
D6,dmr lp
*
move.l
#$00000A,(A5)
*write final byte
move.w
#400,D1
* 2s timeout limit
bsr
wwait
*
bne
dmr q
* error exit on timeout
move.w
#$08A,(A6)
* select status register
move.w
(A5),D0
*get DMA return code
and.w
#$00FF,D0
*mask for error code only
beq
dmr r
* return if o'k
dmr_q
moveq
#-l,D0
* set error return (-1)
dmr_r
move.w
#$080,(A6)
*reset DMA chip for drivr
tst.b
DO
* test for error return
sf
flock
* unlock DMA chip
*
Write ASCII command byte and wait for IRQ
wcbyte
move.l
D0,(A5)
* write disk controller data
moveq
#10,D1
* wait 0.05s
wwait
add.l
Hz_200,Dl
* set Dl to timeout
ww_l
btst.b
#5,gpip
* disk finished
beq
WW
w
* o'k return
cmp.l
Hz_200,Dl
* timeout yet?
bne
WW
1
*no —try again
moveq
#-l,Dl
* set error return (-1)
WW
w
rts
2.49

<!-- source-page: 102 -->
## Page 102

The Concise Atari ST Reference Guide
Hard disk partitioning
Logical sector #0 contains information on the four possible hard disk
partitions:
hd_siz
p0_st.
p0_siz
PX-flg
px-id
px_st
X_S1Z
sl_st
bsl cnt
offset
$1C2
$1C6
$1C7
$1CE
Total size of the disk in sectors
Non zero to show partition exists,
bit_7set for BIOS boot partition
Partition start logicalsector number
Sizeof partition in logical sectors
Three further optional partitions
$1D2 \
$1DE\
$1EA\
$1D3 l2nd$lDF 13rd $1EB 14th
$1D6 I
$1E2 I
$1EE I
$1DA/
$1E6 /
$1F2 /
$1F6
Staringsectorof the bad sectorlist
$1FA
Number of bad sectors
$200
reserved
is a An ST disk may contain up to four partitions, the first sector of each partition
bootsector and contains a BIOS parameter block.
Root
boot
Partition 0
Partition 1
Partition 2
Partition 3
Optional
bad sector
list
2.50
Thepartitionsare describedby
the 12 byte structure above.
Optional partitions
The bad sector list is usually held at the end of the device.
If the parameter 'bsl_cnt' is zero, there are no bad sectors.

<!-- source-page: 103 -->
## Page 103

The Atari Operating System
Chapter 3
The Atari Operating System
General
3.2
Register usage
3.2
Traps
3.3
Trap #13 access
3.3
BIOScalls (trap #13)
3.3
Critical interrupt handlers
3.6
Trap #14 access
3.7
XBIOS calls (trap #14)
3.7
Trap #1 access
3.15
GEMDOS calls (trap #1)
3.15
Supervisor/user toggle
3.23
Test for mode
3.23
User to supervisor mode
3.23
Supervisor to user mode
Extended BDOS calls (trap #2)
3.23
3.24
GEM VDI access
3.24
GEM AES access
3.24
Interrupt Handler (VBI)
3.26
System interrupt functions
3.26
3.1

<!-- source-page: 104 -->
## Page 104

The Concise Atari ST Reference Guide
GENERAL
The operating system (TOS) is a mixture of GEM and an Atari OS (GEMDOS,
BIOS and XBIOS as well as the line-A routines). Any of the OS's can completely
control the system and although calls to the various types of utilities can be
mixed without restriction, the programmer is advised to use a consistent set of
calls. There are many reasons for using a consistent set of calls, not the least being
that the programmer can write programs which are portable to other computers
that contain the same operating systems. Although the writers present intention
may not be to provide the program on an alternative computer system, it is wise
to adhere preferably to the basic OS or GEM calls if possible. Those who have
programs generated on older 8-bit machines, and now find that they cannot be
translated easily,will understand the need for portability.
The line-A routines provide access to the graphic primitives; they will not
produce portable code but will give very rapid execution of graphic functions.
Register usage
The BIOS, XBIOS and GEMDOS routines use and preserve registers in a
specificmanner; dO, dl, d2, aO, al and a2 must always be considered trashed and
should never be used even though a particular version of TOS does not change
them, the next version probably will.
$13 BIOS calls
$14 XBIOS calls
preserve d3 to d7 / a3 to a7
$1 GEMDOS calls
Replies are normally held in register DO on return.
A word of warning. GEM was developed for use on the IBM PC, and as such
was designed to run the Intel 8088 processor, which stores addresses in memory
low word first. 68000 GEM uses the same convention in some of the tables and
parameter blocks, it is a point programmers should be aware of, as a mixture of
conventions of this kind is likely to cause problems.
Note that Appendix E provides a list of all the functions and may be used as
an index to the calls in this and the following chapters.
3.2

<!-- source-page: 105 -->
## Page 105

The Atari Operating System
Traps
BIOS calls (trap #13)
Trap #13 access
To access the BIOS functions, push the parameters in the order given onto the
stackand then call trap#13. Reply or statusis returnedin register DO and the data
placed on the stack trashed.
Typical use might be:
move.w
driveA,-(sp)
move.w
record,-(sp)
move.w
count, -(sp)
move.l
addrss,-(sp)
move.w
#0, -(sp)
move.w
#4, -(sp)
trap
#13
add.w
#14,sp
tst.w
DO
rts
*push device code
*push record to start
*push number of sectors
*push buffer address
*push read data
*push rwabs function call
* call the function
*tidy the stack
* test for error
It is the programmers responsibility to tidy the stackafter the call. TheBIOS,
accessible from user mode, is re-entrant to three levels of calls, users are advised
that this non-standard feature should be used wisely where program portability
is required.
3.3

<!-- source-page: 106 -->
## Page 106

The Concise Atari ST Reference Guide
BIOS calls (Trap #13)
Param.Size
Description of parameter to push
pmpb.L:
Pointer to
empty memory
parameter block
to be filled
[SeeAppendix F.7]
(MD=memory descriptor)
MPB structure:
MemoryJreejist
Memory_alloc_list
Roving_pointer
MD structure:
NextJinkJAD
Start_addr_block
No._bytes__ block
->
->
->
->
->
->
->
Owner^description —
getmpb
0
Get/fill a memory parameter block
(#$00)
(Tidy #6)
(No return)
Use this function BEFORE initialising GEMDOS and only with ROM based systems.
dev.W:
device code
range
(No range error checking)
bconstat
1
(#$01)
0 printer
parallel port
1 aux
RS232port
2 console
screen
3 midi
4 keyboard
Return character_device input status
(Tidy #4)
(Return DO.L)
dev.W:
device code 0 to 3
Ifdev2,also
return IBM-PC compatible code hijword lojbyte
bconin
2
Input character from device
(#$02)
(Tidy #4)
(Return Ascii DO.W)
Ifconterm.b ($484) bit 3 set, also returns the keyboard shift status (kbshiftJBlOS #11) in
highest byte (See Appendix A.5for meaning).
Notes
Initial values:
MD in BSS
0
MD in BSS
0
mbottom
mtop-mbot
0
Operations
0 and 4 are
illegal in
this mode.
Return DO.L
0 no character
-1 Char_ready
WAIT for a
character
DO.L reply.
char.W:
character to be sent
(Appendix C.4 for
WAITuntil
dev.W:
device code 0 to 4
escape codes)
character
bconout
3
Output character to device
sent.
(#$03)
(Tidy #6)
(Return none)
dev.w may also use code 5 which outputs toa screen without control characters.
3.4

<!-- source-page: 107 -->
## Page 107

The Atari Operating System
BIOS calls (trap #13)
cont.
Param.Size
Description of parameter to push
Notes
driv.W:
device code
0 floppy drive A
0 return o'k
1floppy driveB
2+ disKS, networks etc.
negative error
recn.W:
logical sector number to start at
read/write mode
secn.W:
number of sectors to transfer
2 & 3 allow
buf.L:
buffer address (very slow if odd)
formatter
rwfl.W:
read/write flag 0 read
to read & write
1 write
and allow
2 read
\ do not affect
BIOS to
3 write
/media-change
recognize
rwabs
4
Read/write logical sectors on a device
formatted disk
(#$04)
(Tidy #14)
(Return DO.L)
mediachange
vec.L:
vector slot address (-1Lno change)
0 to FF system
vecn.W:
vectornumber to set/get
Set exception vector
(see below)
to $1FF GEM
setexc
5
to $FFFF OEMs
(#$05)
(Tidy #8)
(Return DO.L)
(not with GEM)
tickcal
6
Return system elapsed time mS
(#$06)
(Tidy #2)
(Return DO.L)
driv.W:
device code (0 to 2+, as per rwabs)
Boot on $446
getbpb
7
(#$07)
Get BIOS parameter block pointer
D0.L=address
(Tidy #4)
(Return DO.L)
0=not found
dev.W:
device code_as per bconstat 0 to 4
0=not ready
bcostat
8
Return device char output status
-l=ready to send
(#$08)
(Tidy #4)
(Return DO.L)
driv.W:
device code (0 to 2+, as per rwabs)
GEMDOS will
mediach
9
Get media status
try to read
(#$09)
0_Media no change
l_Media maybe changed
media with a
status value of 1
2 Media has changed
(Tidy #4)
(Return (DO.L)
BIOS level character output is much faster when implemented through the
'NEW TOS' ROM's.
3.5

<!-- source-page: 108 -->
## Page 108

The Concise Atari ST Reference Guide
BIOS calls (trap #13)
cont.
Param.Size
Description of parameter to push
Notes
must be updatedby installablediskdrives
Bits 0 - 31 ($4C2)
drvmap
10
Get bitmap of drives
l=drive in
(#$0A)
(Tidy #2)
(Return DO.L)
0=drive out
mode.W:
Mode bits 7 reserved (zero)
If mode negative
get IBM-PC
6 ALT - Insert
Note: Not
5 ALT - Clr/home
state of
all GEMs will
4 CAPS-lock
shift keys
read bits 5 & 6
3 ALT key
as bit vector
2 CONTROL key
in DO.L low
1 left shift key
byte.
0 right shift key
Critical
kbshift
11
Set keyboard shift bits
code for
(#$0B)
(Tidy #4)
(Return old shift bits DO.L)
portability
Critical interrupt handlers
The extended GEMDOS vectors (Appendix A.4) may be employed by user
programs but should take note of the following:
$100 etv_timer:
Word value on stack is number of millisecs since last tick.
Save all registers
$101 etv_critic:
Stack word value is error number, save registers used.
To ignore an error set D0.L=0
To retry an error set D0.L=$10000
To abort an error set D0.L=sign extend stack parameter.
$102 etv_term:
Abort termination by a longword jump back to the top of the
calling application or terminate via an RTS
3.6

<!-- source-page: 109 -->
## Page 109

The Atari Operating System
XBIOS
calls (Trap #14)
Trap #14 access
To access the extended BIOS functions, push the parameters in the order
given onto the stack and then call trap#14 from user or supervisor mode. Reply
or status is returned in register DO.
Typical use might be:
move.l
vector,-(sp)
*push vector address
move.l
parblk,-(sp)
*push parameterblockaddr
move.w
type, -(sp)
*push type of mouse action
move.w
#0, -(sp)
*push initmouse call
trap
#14
*call the function
add.w
#12,sp
*tidy the stack
tst.w
DO
* test for error
rts
Param.Size
Description of parameter to push
Notes
vect.L:
para.L:
(Block
contains
4 bytes)
type.W:
initmous
0
(#$00)
vector address (mouse interrupt handler)
parameterl_y=0top,0_y=0 bottom
block
Mouse button command (6.3_#7)
address
x parameter thresh/scale/delta
y parameter thresh/scale/delta
mode 0 disable mouse
1 enable relative mouse
2 enable absolute mouse
3 unused
4 enable keycode mouse
Initialize mouse packet handler
(Tidy #12)
(No return)
Ifmode = 2
then extra
word sized
parameters
required in
parameter block
xmax
ymax
xinitial
yinitial
See call #34
re vector address
numb.W:
Bytes from memory top to be saved
MUST call
ssbrk
1
Reserve block of memory at high RAM
before OS
(#$01)
(Tidy #4)
(Return DO.L)
initialized
_physbase 2
Get screen physical base address
(#$02)
(Tidy #2)
(Return DO.L)
At next
vblank
3.7

<!-- source-page: 110 -->
## Page 110

The Concise Atari ST Reference Guide
XBIOS
calls
(Trap#14)cont.
Param.Size
Description of parameter tc push
Notes
logbase
3
(#$03)
Get screen logical base address i
(Tidy #2)
(Return DO.L)
low
Used by GSX
on screen
_getRez
4
(#$04)
Get screen resolution
(Tidy #2)
(Return DO.W)
Ret
0 320x200
1 640x200
2
640x400
rez.W:
Set screen resolution (0,1 or 2)
Negative
clear screen, home cursor, reset VT52
parameters
ploc.L:
Set screen physical location (next vblnk)
areignored
lloc.L:
Setscreen logicallocation (now)
so a single
_setScreen 5
Set screen parameters
parameter
(#$05)
(Tidy #12)
(No return)
can be set
palp.L:
Set palette pointer (word boundary)
At next
_setPalette 6
Set palette hardware register contents
vblank, all
(#$06)
(Tidy #6)
(Noreturn)
change.
colr.W:
Set colour format -16 bit colour word
If colour
coln.W:
Setcolournumber (0to 15)
negative
_setColor 7
Set a colour in hardware palette
ignore.
(#$07)
(Tidy #6)
Return old colour DO.W
(with $777 mask)
secn.W:
number of sectors to be read
sidn.W:
side number selected (0 or 1)
trkn.W:
track number to seek to
stsc.W:
sector to start reading from (1 to 9)
devn.W:
floppy device number (0 or 1)
scrt.L:
#0, not used at present.
buff.L:
word aligned sized buffer address -
_floprd
8
Read sectors from a floppy drive
(#$08)
(Tidy #20)
3.8
Return D0.W=0
for o'k
else failed
error number
must be big
enough

<!-- source-page: 111 -->
## Page 111

The Atari Operating System
XBIOS
calls
(Trap#14)cont.
Param.Size
Descriptionof parameter to push
secn.W:
number of sectors to write (<=sectors/track)
sidn.W:
side number selected
trk.nW:
track number to seek to
stsc.W:
sector to start writing to (1 to 9)
devn.W:
floppy device number (0 or 1)
scrt.L:
#0, not used at present.
buff.L:
word aligned buffer address
_flopwr
9
Write sectors to a floppy drive
(#$09)
(Tidy #20)
(Return DO.W)
fcod.W:
magc.L:
intl.W:
sidn.W:
trkn.W:
sptk.W:
devn.W:
scrt.L:
buff.L:
_flopfmt
10
(#$0A)
$E5E5 format code (not 0 or FxFx)
$87654321
Sectorinterleave factor (say 1)
side number to format (0 or 1)
track number to format (0 to 79)
number sectors/track toformat (say9)
floppy device number (0 or 1)
#0, not used at present.
word aligned buffer address (8K-9track)
Format a floppy disk
The 'NEW TOS' formats afloppy disk with track skew (-1) and alongword pointer to a
one word per sector skew table in the previously unused scrt.L parameter
Notes
Return D0.W=0
for o'k
else failed
error number
Writing to
boot 1,0,0
sets 'maybe'
mediachange (1)
Return D0.W=0
for o'k
else failed
error number.
Buffer holds
Zero terminated
list of bad
sectors.
Formatting
sets
mediachange (2)
getdsb
(#$0B)
11
Get device status block pointer
(Tidy #2)
(RTS call only)
Obsolete
function.
ptr.L:
Pointer to character vector
cnt.W:
number characters to write less one.
midiws
12
Write a string to midi port
(#$0C)
(Tidy #8)
(No return)
vect.L:
intn.W:
_mfpint
13
(#$0D)
Address ofinterrupt routine
Interrupt number (0 to 15)
Set MFP interrupt
(Tidy #8)
(No return)
Old vector
is lost.
3.9

<!-- source-page: 112 -->
## Page 112

The Concise Atari ST Reference Guide
XBIOS
calls
(Trap#14)cont.
Param.Size
Description of parameter to push
Notes
devn.W:
Serial device
0: RS232
For RS232
1: Keyboard
identical
2: Midi
o/p buffer
follows i/p
Returna pointer.L
( L.pntr to device buffer
to a serial device's
(W.size of buffer
input buffer record
(W.head index
High & low
parameter block (brpb)
(W.tail index
water start
(W.low-water mark
RS232 Xon/Xoff
(W.high-water mark
if flow control
iorec
14
Get pointer to serial device i/p brpb
enabled.
(#$0E)
(Tidy #4)
(Return DO.L)
scr.W:
Sync character
\
68901
-1 parameters
tsr.W:
Tx status
1
MFP register
do not
rsr.W:
Rx status
1
settings
change
usr.W:
Usart control
/
(page 1.25)
registers
flow.W:
0 No flow control (default)
1 Xon/Xoff
(AS/AQ)
2 RTS/CTS
3 Xon/Xoff & RTS/CTS
baud.W:
0=19200
5=2000 (1920)
10=200
1=9600
6=1800(1745)
11=150
Actual
2=4800
7=1200
12=134
baud in
3=3600 (3840)
8=600
13=110
brackets
4=2400
9=300
14=75 (120)
rsconf
15
Configure RS232 port
15=50(801
(#$0F)
(Tidy #14)
(No return)
capl.L:
Caps lock \
Set pointers to128 byte
Shift
1
Keyboard translation
Return pointer
shft.L:
to structure:
unsh.L:
Unshifted
/
tables.
Unshft tab
keytbl
16
Set/get keyboard translation table pointer
Shiftjabl
(#$10)
(Tidy #14)
(Return DO.L)
Capslk_tab
-1 not to change characters
Bitzero poor distribution
random
17
Get 24-bit pseudo random number
Bits 24-31
(#$11)
(Tidy #2)
(Return DO.L)
are zero
3.10

<!-- source-page: 113 -->
## Page 113

The Atari Operating System
XBIOS
calls
(Trap#14)cont.
Param.Size
Description of parameter to push
Notes
exfl.W:
1 = boot sector executable
-1 retains
0 = non-executable boot sector
old values.
dskt.W:
0=40 track SS
2=80 track SS
1=40 track DS
3=80 track DS
Image is
sern.L:
random boot serial no. if=#$1000000
written
buf.L:
pointer to any 512-byte buffer
to volumes
protobt
18
Prototype a boot sector image
boot sector
(#$12)
(Tidy #14)
(No return)
secn.W:
number sectors to verify (<=sectors/track)
Return D0.W=0
sidn.W:
side number selected
for o'k
trkn.W:
track number to seek to
else failed
stsc.W:
sector to start reading from (1 to 9)
error number
devn.W:
floppy device number (0 or 1)
scrt.L:
#0, not used at present.
Buffer holds
buff.L:
word aligned 1024 byte buffer address
0 terminated
flopver
19
Verify sectors from a floppy drive
list of bad
(#$13)
(Tidy #20)
sectors.W
scrdmp
20
Dump screen to printer
At present
(#$14)
(Tidy #2)
(No return)
mono only.
rate.W:
Rate =1/2 cycle time
-1 retains
60/50 Hz color 70 Hz monochrome
old values.
attr.W:
0_Hide cursor
4J3et rate
1JShow cursor
5_Get rate
Returns
2_Blink cursor
6_unused
old rate High
3_Noblink cursor
7_unused
old attribute low
cursconf
21
Set/get cursor blink rate & attribs
word byte.
(#$15)
(Tidy #6)
(Return DO.W)
date.L:
32-bit DOS format date and time
Date Hiword
settime
22
Set ikbd time and date
Time Loword
(#$16)
(Tidy #6)
(No return)
(See page 3.22
1 for the format.
Thesefunctions use
gettime
23
Get ikbd 32-bit format date & time
(#$17)
(Tidy #2)
(Return DO.L)
the real time clock
3.11

<!-- source-page: 114 -->
## Page 114

The Concise Atari ST Reference Guide
XBIOS
calls
(Trap#14)cont.
Param.Size
Description of parameter to push
bioskey
24
Restore power up keyboard setting
(#$18)
(Tidy #2)
(No return)
pntr.L:
Pointer to character string vector
nch.W:
Count of characters to send -1
ikbdws
25
Write a string to intelligent kybd
(#$19)
(Tidy #8)
(No return)
intn.W:
MK68901 interrupt number
jdisint
26
Disable a MK68901 interrupt
(#$1A)
(Tidy #4)
(No return)
intn.W:
jenabint
27
(#$1B)
MK68901 interrupt number
Enable a MK68901 interrupt
(Tidy #4)
(No return)
Notes
Reset translation
tabs
Send command
to ikbd
regn.W:
PSG register number (00 to OFH)
Register ORed
data.B:
Byte to write to register
#$00 read
giaccess
28
Read/writea sound chip register
#$80 write
(#$1C)
Atomic access only
(Return D0.B)
bitn.W:
Bit number to be set (Mask AND)
offgibit
29
Atomically set PORT A bit to zero
(#$1D)
(Tidy #4)
(No return)
bitn.W:
Bit number to be set (Mask OR)
ongibit
30
Atomically set PORT A bit to one
(#$1E)
(Tidy #4)
(No return)
vec.L:
Pointer to an interrupt handler
data.W:
Byte placed in timer's data register
cntl.W:
Timers control register setting
timr.W:
Timer number allocations are:
0_A Reserved for end-users & applications
1_B Reserved for graphics primarily
2_C System timer (GEM, DESKTOPetc)
3_D RS232 baud rate and mere users
xbtimer
31
Provide control timing facility
(#$1F)
(Tidy #12)
(No return)
3.12

<!-- source-page: 115 -->
## Page 115

The Atari Operating System
XBIOS
calls
(Trap#14)cont.
Param.Size
Description of parameter to push
Notes
ptr.L :
Pointer to table of bytes (command-data)
cmd 0 to 15load register0 to 15with data
Oxx
cmd 128 load tempreg with databyte
128 xx
cmd 129 reg # contents to load into tempreg (rr)
129 rr cc ee dd
two'sc value to add to tempreg (cc)
time delay between steps (dd/50)
terminate on value (ee)
cmd 130-255set delay data (ticks) [0=stop]
130 xx
dosound
32
Produce a sound
(See Appendix
(#$20)
(Tidy #6)
L.22 et seq.)
conf.W:
Bit 0 0=dot matrix,
l=daisy wheel
-1 returns
1
0=colour device l=monochrome
configuration
2
0=1280.dots/line l=960.dots/line
byte else
3
0=draft,
1=NLQ
change and
4
0=parallel,
l=RS232port
5
0=formfeed,
l=single sheet
return the
old value.
6-14 reserved
15
must be zero
setprt
33
Get/set printer configuration byte
(#$21)
(Tidy #4)
(Return DO.W)
Structure
MIDIJnput (BIOS buffer routine)
-> DO.B character
longword
keybrd_err \ Called when
-
\
68901
format
MIDI_err
/ overrun detected
/
or 6850's
ikbd_stat
\
Pointer to packet
mous_pack 1
handlers (pointer to
(mouse vector
clocl;_pack 1
packet received in
used by
joyst_pack /
AO & on stack.L)
GEM & GSX)
MIDI vec
\
Call when character
ikbd_vec
/
available on 6850
Handlers to
kbdvbase
34
Return pointer to structure base
return by RTS
(#$22)
(Tidy #2)
(Return DO.L)
within 1ms
rept W:
Rate of key-repeats (System ticks)
-1 parameters
init.W:
Delay before key-repeat starts
no change.
kbrate
35
Get/set keyboard repeat rate
Delay high byte
(#$23)
(Tidy #6)
(Return DO.W)
repeat low byte
3.13

<!-- source-page: 116 -->
## Page 116

The Concise Atari ST Reference Guide
XBIOS
calls
(Trap#14)cont.
Param.Size
Description of parameter to push
prt.L:
_prtblk
36
(#$24)
Pointer to parameter block
Hard copy routine
(Tidy #6)
(No return)
vsync
(#$25)
37
Wait till next vblank and return
(Tidy #2)
(No return)
Notes
Graphics
synchronize
code.L:
Pointer to code ending with RTS
Must not
Hackers access tohardware &protected locations call BIOS
superx
38
Execute code in supervisor mode
or GEMDOS
(#$26)
(Tidy #6)
functions
puntaes
39
Switch off AES, when not in ROM
(#$27)
(Tidy #2)
otherwise perform a RESET.
flag.W:
Blitter status word
bit 0- set to enable blitter
1-14 reserved
15 0_clear
or -l_Get blitter status
blitmode
64
Get/set blitter status
(#$40)
(Tidv #4)
(Return DO.W)
The reserved fields arefor future blitter capabilities
andwill be used infuture.
3.14
bit
Automatic
operation
through line-A
and VDI calls.
Return DO
0_set (blit on)
l_set (if blit there)
2-14 reserved
15 clear

<!-- source-page: 117 -->
## Page 117

The Atari Operating System
GEMDOS calls
(Trap #1)
Trap #1 access
To access GEM BDOS functions, push the parameters in the order given onto
the current stack and then call trap#l. Any byte, word or longword reply or the
address of a parameter block will be returned in register DO.
*push drive number (2)
*push setdrv function call
* call the function
*tidy stack
*return with bitmap in DO
It is the programmers responsibility to maintain the stack integrity (tidy) after
the call.
Param.Size
Description of parameter to push
Notes
p_term_o
0
End process and return to parent.
Return code
(#$00)
(Tidy #2)
(use $4c)
zero.
c_conin
1
Read character from standard i/p & echo
The console
(#$01)
(Tidy #2)
(Return DO.L)
scan code
1 (Appendix
char.W:
Character to be printed
Page d.3)
c_conout
2
Write character to standard output
is returned
(#$02)
(Tidy #4)
(No return)
in the low
| byte of the
c_auxin
3
Read character from auxiliary port
high word.
(#$03)
(Tidy #2)
(Return DO.L)
(RS232)
The upper
1 byte of the
char.W:
Character to be printed
word sent
c_auxout
4
Write character to standard aux device
MUST be 0
(#$04)
(Tidy #4)
(No return)
(RS232)
for future
1 compatibility
char.W:
Character to be printed
c_prnout
5
Write character to standard print device
(#$05)
(Tidy #4)
(Return-l_o'k, 0_after30mstime out)
move.W
driveB,-(SP)
move.W
#13,-(SP)
trap
#1
add.W
#4,SP
rts
3.15

<!-- source-page: 118 -->
## Page 118

The Concise Atari ST Reference Guide
GEMDOS calls (Trap#1)
cont.
Param.Size
Descriptionof parameter to push
parm.W:
If parm.W=255 ($00FF) then read else
parmeter is character to be written
Raw I/O to standard input/output
(Tidy #4)
(Return DO.L)
c_rawio
(#$06)
c_rawcin
7
Raw input from standard input
(#$07)
(Tidy #2)
(Return DO.L)
c_necm
(#$08)
8
Read a character from standard input
(Tidy #2)
(No return)
addr.L:
Address of null terminated string
c_conws
9
Write string to standard output
(#$09)
(Tidy #6)
(Return D0.L=# char sent)
addr.L:
Address of input buffer
(Firstbyte data portion length)
Read edited string from standard input
(Tidy #6)
(Buffer returns)
c_conrs
(#$0A)
10
c_conis
11
Check status of standard input
(#$0B)
(Tidy #2)
(Return DO.L)
driv.W:
Drive number: 0=A, 1=B....15=P
d_setdrv
14
Set default drive
(#$0E)
(Tidy #4)
(Return DO.L)
c_conos
16
Check status of standard output
(#$10)
(Tidy #2)
(Return DO.L)
Notes
If no character
then D0.L=0
Character as
per c_conin
No echo to screen
Pass controls
No echo. AC
AQ & AS active
Character bytes
terminated
by a zero.
On return
2nd length read
3-n characters
n+1 zero
*C,AH,AI,*J,*M,AR,AU,andAXhave their normal 'edit' meaning.
Terminate editusing: RETURN, A/or AM
character ready
-l_yes,0_no
Return bitmap
of drives
present
-1 ready
0 not ready
c_prnos
17
Check status of standard print device
-1 ready
(#$11)
(Tidy #2)
(Return DO.L)
0notready
c_auxis
(#$12)
3.16
18
Check status of standard aux device i/p
(Tidy #2)
(Return DO.L)
-1 char received
0 no characters

<!-- source-page: 119 -->
## Page 119

The Atari Operating System
GEMDOS calls (Trap#1)
cont.
Param.Size
Description of parameter to push
Notes
c auxos
19
(#$13)
Check status of standard aux device o/p
(Tidy #2)
(Return DO.L)
-1 ready
0 not ready
d_getdrv
25
(#$19)
Get current drive
(Tidy #2)
(Return DO.L)
drive A=0
B=l...etc.
addr.L:
f setdta
26
(#$1A)
Disk transfer address
Set disk transfer address
(Tidy #6)
(No return)
Address
used by
sfirst (#78)
t getdate
42
* (#$2A)
Get date
(Tidy #2)
(as per set date format)
(Return DO.L)
Date return
in low word
date.W:
t setdate
43
*(#$2B)
Date format
Set date
(Tidy #4)
date: bits 0-4,1 to 31
mnth bits 5-8,1 to 12
year: bits 9-15,1980 - 2100
Error return
if date not
valid
t gettime
44
* (#$2C)
Get time
(Tidy #2)
(as per set time format)
(Return DO.L)
Time return
in low word
time.W:
t settime
45
*(#$2D)
Time format
Set date
(Tidy #4)
sees: bits 0-4, step 2s
mins:bits 5-10
hour: bits 11-15
Error return
if date not
(DO.L) valid
f getdta
47
(#$2F)
Get disk transfer address
(Tidy #2)
(Return DO.L)
s version
48
(#$30)
Get version no
(Tidy #2)
(1.00lo-hi byte)
(Return DO.W)
0001H for
first release
exit.W:
Exit code (process return code)
keep.L:
# bytes to keep in process description
p_termres 49
Terminate and stay resident
(#$31)
(Tidy #8)
(No return)
May cause
problems
for future
conversions
Updated from RTC on the termination of every process
3.17

<!-- source-page: 120 -->
## Page 120

The Concise Atari ST Reference Guide
GEMDOS calls (Trap#1)
cont.
Param.Size
Description of parameter to push
Notes
driv.W:
Drive number: 0=current, 1=A, 2=B..
Buffer pb.I,
info.L:
Address of drive information buffer
ttfree clusters
d
free
54
Get drive free space (data in buffer
ttclusters total
(#$36)
4 x longwords)
#bytes/sector
(Tidy #8)
(Return D0=0_o'k else error) #sectors/cluster
path.L:
Address of string containing pathname
Pathname is
d
create
57
Create a subdirectory
terminated
(#$39)
(Tidy #6)
(Return DO.L)
in a null.
path.L:
__
_
Address of string containing pathname
d
delete
58
Delete a subdirectory
0 ret o'k
(#$3A)
(Tidy #6)
(Return DO.L)
negative error
path.L:
Address of string containing pathname
d setpath 59
Set current directory
(#$3B)
(Tidy #6)
(Return DO.L)
attr.W:
File attributes:
01H read only
02H hidden file
Return file
handle if o'k,
04H hidden system file
negative error
08H File, vol label in first 11 bytes
path.L:
Address of string containing pathname
f
create
60
Create a file
Pathname
(#$3C)
(Tidy #8)
(Return DO.L)
ends in a zero
attr.W:
File read-write mode
Return file
0=file open for read only
handle if o'k,
1=file open for write only
negative if
2=file open read and write
error.
path.L:
Address of string containing pathname
f open
61
Open file
Pathname
(#$3D)
(Tidy #8)
(Return DO.L)
ends in a zero
hndl.W:
File handle
0 ret o'k
f close
62
Close file
-errors maycrash system
negative error.
(#$3E)
(Tidy #4)
(Return DO.L)
3.18

<!-- source-page: 121 -->
## Page 121

The Atari Operating System
GEMDOS calls (Trap#1)
cont.
Param.Size
.
Description of parameter to push
Notes
buff.L:
Address of buffer to store bytes
DO contains the
byts.L:
Number of bytes to read (never 0)
number of bytes
hndl.W:
File handle
read.
f read
63
Read file
Negative on
(#$3F)
(Tidy #12)
(Return DO.L)
error.
buff.L:
Address of buffer storing bytes
DO contains the
byts.L:
Number of bytes to write
(never 0)
number of bytes
hndl.W:
File handle
(errors may crash thesystem)
written. Negative
f write
64
Write file
on error, i.e
(#$40)
(Tidy #12)
(Return DO.L)
disk full.
path.L:
Address of string containing pathname
0 return o'k
f delete
65
Delete file
negative on error.
(#$41)
(Tidy #6)
(Return DO.L)
fmod.W:
0: move n bytes from beginning
Positive moves
1: move n bytes from current position
to end of
2: move n bytes from end of file
file, negative
hndl.W:
File handle
to beginning
nbyt.L:
Signed number of bytes argument
f seek
66
Seek file pointer
D0=Absolute file
(#$42)
(Tidy #10)
(Return DO.L)
pointer location
attr.W:
File attributes:
#$01 read only
Return file
#$02 hidden file
#$04 hidden system file
handle if o'k,
#$08 File, vol label in 1st 11 bytes
negative if error
#$10 File is a subdirectory
#$20 File has been written & closed
Pathname is
wrt.W:
0_get/l_set file attributes
terminated
path.L:
Address of string containing pathname
in a null.
f attrib
67
Get/set file attributes
(#$43)
(Tidy #10)
(Return DO.L)
Get in DO.L
shnd.W:
Standard file handle to duplicate
Error return
f dup
69
Duplicate file handle
page 1.3
(#$45)
(Tidy #4)
(Return DO.L)
3.19

<!-- source-page: 122 -->
## Page 122

The Concise Atari ST Reference Guide
GEMDOS calls (Trap#1) cont.
Param.Size
Descriptionof parameter to push
Notes
shnd.W:
Standard file handletoforce
0console i/p
nhnd.w:
Non-standard file handle
-1 console o/p
f_force
70
Force point file handle
to non-standard
-2 serial
(#$46)
(Tidy #6)
handlefile or device
-3parallel
driv.W:
Drive number: 0=default, l=A...etc.
path.L:
Address of 64byte buffer for pathname
d_getpath 71
Get current directory
(#$47)
(Tidy #8)
(Return DO.L)
Buffer minimum
64 bytes.
Return 0 o'k
nbyt.L:
m_alloc
72
* (#$48)
or
frad.L:
m_free
73
* (#$49)
rmem.L:
mmem.L:
zero.W:
m_shrink 74
* (#$4A)
Allocated block may not be ona word boundary
Bytes to allocate or -1 return maximum available
D0.L=0 if
Allocate memory (DO.L start pointer)
allocation fails
Read free memory (DO.L bytes available)
or pointer to
(Tidy #6)
(Return DO.L)
block.
Address of memory to free
Free allocated memory
(Tidy #6)
(Return DO.L)
Length of retained memory
Start of memory space to modify
zero (reserved)
Shrink size of allocated memory
(Tidy #12)
(No return)
0 return o'k
negative on error
Reallocates
unused memory
for GEMDOS.
0 return o'k
negative on error
penv.L:
Pointer toenvironmental string, 0forparent
pcmd.L:
Pointer to command tail including redirection
path.L:
Address of string containing pathname
mode.W:
0=load & execute, return terminal child code
3=load only, return DO.L base page address
4=create basepage,
5=execute only
P_exec
75
Load or execute a process
(#$4B)
(Tidy #16)
(Return DO.L)
Insufficient memory error returned as $000000D9.
Mode 3 is
used for
overlays,
Return DO.L
error if
load fails.
These functions are unreliable in early versions of TOS.
3.20

<!-- source-page: 123 -->
## Page 123

The Atari Operating System
GEMDOS calls (Trap#1) cont.
Param.Size
Description of parameter to push
stat.W:
p_term
76
(#$4C)
Interrogation code for parent
Terminate process,
control to parent
(Tidy #4)
(Return DO.L)
Notes
0 Return o'k
non-zero error
satt.W:
Search attributes
Filename
#$00 normal files:
#$01 read only
may include
#$02 hidden files:
#$04 hidden system file
'*' or'?'
#$08 volume label file #$10 subdirectory files
wildcards.
#$20 File has been written & closed
path.L:
Address ofstring containing pathname
Iffilenot
f_sfirst
78
Search for 1st occurence filespec
found return
(#$4E)
44-byte DTAbuffer created if found
-33code
0-20 OS reserved:
21 file attributes
in DO.L
22-23 Time stamp:
24-25 Date stamp
(filenot found)
26-29 Filesize.L (Lo-Hi):
30-43 Name.extension
(Tidy #8)
(Return DO.L)
f_snext
79
Search for next occurence filespec
First 20bytes
(#$4F)
(Uses first20 bytesofDTA buffer,
DTA buffer
name.extension updated on success)
must not be
(Tidy #2)
(Return DO.L)
altered.
pth2.L:
Pointer to 'new' file string
pthl.L:
Pointer to 'old' filestring
zero.W:
zero
f_rename
86
Rename a file
(#$56)
(Tidy#12)
(ReturnDO.L)
Rename a
file
Return DO
error number
or 0=o'k
3.21

<!-- source-page: 124 -->
## Page 124

The Concise Atari ST Reference Guide
GEMDOS calls (Trap#1) cont.
Param.Size
Description of parameter to push
info.W:
0_set/l_get date and time
hndl.W:
File handle
buff.L:
Time and date buffer pointer
f_datime
87
Get/set file date and time stamp
(#$57)
Buffer first word
Bit format days 0-4
1 to 31
mnth5-8
1 to 12
year 9-15, 1980 to 2100
Buffer second word
Bit format sees
0-4 in 2 sec steps
mins 5-10
hour 11-15
(Tidy #10)
(No return)
Notes
$00
$15
$16
$18
$1A
$1E
21
22
24
26
30
OS reserved
File attributes
File time stamp
File date stamp
Longword file size
Name and ext. of file found
(7 words)
DTA buffer
Use function #$1A (dec 26) to set DTA buffer address and functions #$2F
(dec 47) to get DTA address.
3.22

<!-- source-page: 125 -->
## Page 125

The Atari Operating System
Supervisor/User toggle
Thisspecialfunction allows users to get in and out of supervisor mode»from
GEMDOS.
Param.Size
'
Description of parameter to push
Notes
stck.L:
-l_get mode:
Return
0_user
(DO.L)
1 supervisor
<>-l switch mode
Return
a) User to supervisor mode
value of
0_set supervisor stack equal
old super
to user stack before call
stack in
<>0_set supervisor stack equal
to stck.L
DO.L
b) Supervisor to user mode
The old
set supervisor stack from
value of
stck.L which must be the first
super stack
SMODE function call or the
MUST be
system will crash.
restored on
smode
32
Set/get supervisor/user mode
process
(#$20)
(Tidy #6)
(Return DO.L)
termination
Test for mode
move.L
#$l,-(sp)
*Returns DO.L
move.W
#32,-(sp)
*
$0= user mode
trap
#1
*
$FF=supervisor mode
addq
#6,sp
User to supervisor mode
clr.L
-(sp)
move.W
#32,-(sp)
trap
#1
addq
#6,sp
move.L
D0,save_stk
Supervisor to user mode
move.L
save__stk,-(sp)
move.w
#32,-(sp)
trap
#1
addq
#6,sp
Set supervisor stack equal to
user stack before this call,
Save old supervisor stack value
Recover old supervisor stack
and back into user mode.
3.23

<!-- source-page: 126 -->
## Page 126

The Concise Atari ST Reference Guide
Extended BDOS calls (Trap #2)
To access the extended BDOS functions, the DO.W register is loaded with the
function code, an address pointer is placed in DLL and trap #2 called. A return, if
any, is placed in DO.W.
GEM VDI and AESmay be accessed by loading the relevant parameter block
address into Dl, the function number into dO and making an extended BDOS call:
GEM VDI access
move.l
#contrl, pblock
move.l
#pblock,dl
*addressofVDI paramblock
move.w
#$73,d0
*set dOequal to 115 and
trap
#2
*execute an extended BDOScall
GEM AES access
move.l
#control, c
move.l
# c,dl
move.w
#$c8,d0
trap
#2
3.24
*address of AES param block
*set dO equal to 200 and
* execute an extended BDOS call

<!-- source-page: 127 -->
## Page 127

The Atari Operating System
Extended BDOS calls (Trap #2) cont.
Code#
Hex Dec
Function
Notes
DO.W :
#$00 0
Terminate current program and
The function
return to CP level
does not return
TraP #2
RESET
tocalling program.
DLL:
#pblock
VDIparameter block pointer
DO.W :
#$73 115
VDI function number
Trap #2:
GEM VDI access
DLL:
#control
AES param blockpointer
DO.W :
#$c8 200
AES function number
Trap #2:
GEM AES access
DO.W:
Trap #2
DO.W:
Trap #2
#$c9 201
#$fe -2
Test for GDOS version
Return D0.W=-2
if GDOS not
installed.
The trap #2 RESET call simply calls the GEMDOS trap #1 process terminate
function #$4C.
*Test for GDOS, looks for Atari GDOS version 1.0 which does not contain all
the VDI functions.
3.25

<!-- source-page: 128 -->
## Page 128

The Concise Atari ST Reference Guide
Interrupt Handler
The standard system interrupt is level 2, vector $68 (104) and takes the
following sequence every interrupt:
Vertical blank interrupt (VBI)
Order
Function
System variable
1
Increment the frame counter
FRCLOCK.L
$466
2
Test for mutual exclusion
VBSLEM.W
$452
if = 0 return
3
Save all the registers on stack
4
Increment'Vblank counter'
VBCLOCK.L
$462
5
Testfor high resolutionmode
SHFTMD.W
$44C
if shftmd<2 then goto 6,
test for low resolution monitor attatched
if yes set mode to zero
DEFSHFTMD.B $44A
6
Call cursor blink routine
7
Test for new colour pallette
COLORPTR.L
$45A
if colorptr=0 then goto 8
Load pallette with 16 words pointed to
by colorptr and then zero it.
8
Test for new screen
SCREENPTR.L
$45E
if screenptr=0 then goto 9
Set screen physical base to screen
pointer and then zero pointer.
9
Run deferred VBI vectors
# of deferred VBI vectors
nvbls.W
$454
Pointer to VBIvector array
vblqueue.L
$456
10
Return
There are eight VBI vectors available in the default array, the first is reserved
for GEM's VBI code. Pointers to new handlers are placed in the spare slots.
Handler code ends in RTS and may use any register except the user stack pointer.
Larger arrays can be allocated by redefining nvbls and vblqueue, copying the
current vectors to the new array. An application that returns, should tidy up the
VBI queue.
Do not make VDI or Line-A calls via an Interrupt as the results are
unpredictable if the SThas a blitter chip installed.
3.26

<!-- source-page: 129 -->
## Page 129

GEM VDI
Chapter 4
GEM VDI
GEM VDI function calls
4.2
VDI parameter blocks
4.3
Control table
4.3
Attribute table
4.4
Points table
4.4
Parameter block sizes
4.5
The GEM VDI calls
4.8
Workstation function calls
4.8
Output functions
4.10
General drawing primitives
4.11
Attribute functions
4.13
Raster operations
4.16
Input functions
4.18
implemented
4.18
not implemented
4.20
Inquire functions
4.22
VDI style patterns
4.26
VDI text alignment
4.46
Escape functions
4.27
implemented
4.27
not implemented
4.30
File formats
4.33
Bit image
4.33
File header
4.33
Data encoding
i
4.33
Meta file Sub Op codes
4.35
Output page
4.35
GEM draw
4.36
4.1

<!-- source-page: 130 -->
## Page 130

The Concise Atari ST Reference Guide
GEM VDI function calls
Digital Research's GEM VDI (Virtual Device Interface) provides graphic
capabilities
and
a
device
independent
operating
environment
for
the
development of programs that are transportable to other operating systems. It is
therefore a pity that the initial ROM implementations of the Atari ST did not
include that portion of code which provided the transportability.
The VDI comprises GDOS, the Graphics Device Operating System and GIOS,
the Graphics Input/Output System.
GDOS consists of the basic and device independent graphic functions that are
called by applications and functions without reference to any specific hardware
in a manner similar to the disk operating system. The GIOS consists of the device
specific code that is needed to interface to each specific graphic device (device
drivers). The OS needs a device driver for every different graphics device
attatched to the system, unfortunately only one is supplied - for the screen. This
limitation, the drivers restriction of only two fonts per screen resolution and the
absence of support for the normalised device coordinate system means that the
ST does not have a device independent capability.
Appendix E lists all the GEM VDI functions. As a general rule, only those
functions associated with the screen are implemented (virtually all are), those
associated with either a printer, plotter or meta-file are not implemented.
It may be possible to obtain the file GDOS.PRG which when placed in an
AUTO folder, provides the ST with the missing facilities of GDOS. Atari have
made the file available to registered software developers for a nominal sum but
the code (and that means small parts of it as well) is subject to a single fixed
licence fee if used in commercial programs.
4.2

<!-- source-page: 131 -->
## Page 131

GEM VDI
GEM VDI function calls
The VDI functions are accessed through an extended BDOS call and the VDI
parameter block (five longword pointers to the word tables; cntrl, input attribute
and points, output attribute and points). The parameter and array blocks, which are
usually initialized by an AES call to APPLJNIT, have the following formats:
$00
$04
$08
$0C
$10
$00
$02
$04
$06
$08
$0A
$0C
$0E
Control
pointer table
Input attribute
table pointer
Input points
table pointer
Output attribute
table pointer
Output points
table pointer
Opcode
Length of input
coordinate table
Length of output
coordinate table
Length of input
attribute table
Length of output
attribute table
Subfunction
ident number
Device handle
Opcode depend
information
control
intin
ptsin
intout
ptsout
VDI parameter
block
Control table
\
/
Length in
word pairs
Length in
words
Zero ifcan not be opened
It is the programmers responsibility to define the correct number of arguments
to be passed and the array size (1 to n) required by the function on return.
4.3

<!-- source-page: 132 -->
## Page 132

The Concise Atari ST Reference Guide
Attribute table
intin
intout
$00
$02
$04
$06
$08
$0A
Points table
ptsin
ptsout
$00
$02
$04
$06
$08
$0A
Typical usage
device ID (handle)
line type
line colour
mark type
mark colour
font
Typical usage
x coordinate
y coordinate
word
pair
width
height
word
pair
Note:
These parameters
are held in word sized tables.
Assembler and BASIC use the
actual offset whereas 'C, Pascal
and GFA Basic etc. use word
sized offsets, i.e half the actual
value I have used in this book.
A minimum application stack space of 128 bytes is required, plus space for
theGEM arrays. The VDI function calls havebeendetailed in groups asfollows:
Workstation control functions:
Define the workstation parameters and defaults; these govern the font and
the window size to be used and the generation of virtual screens.
Output functions:
Thesefunctions draw the graphic primitive on the specifiedoutput device.
General drawing primitive functions:
Contain the basic graphic primitives of line, arc, filled and unfilled ellipse
and rectangle, and of justified text.
Attribute functions:
Define the output style of the graphic primitives; the line, marker, text cell
and polygon for colour, size and fill.
4.4

<!-- source-page: 133 -->
## Page 133

GEM VDI
Raster operations:
Provide the ability to transpose a source block of pixels to a destination
location on the basis of a logical operation between the bits comprising the source
and destination.
Input functions:
Enable the programmer to provide the user with both a 'request and wait on
event' and a 'request, sample and return' mode of inquiry.
Inquire functions:
Return the status or attributes of a specific device
Escape functions:
Enable the application to access special features applicable to certain graphic
devices.
VDI Parameter block sizes
The numbers of parameters required by the various functions are detailed in
the tabular format:
Control table
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
The table contains details of the parameter input and output word sizes; note
that the points value is half the table size (a point is defined by a pair of x and y
word-sized coordinates - a longword). All data is assumed to be 2 byte integer
including string characters.
Open workstation function v_opnwk
The major VDI function in terms of size is the 'open workstation function',
which sets up a named screen, (device handle) the desktop window, identified as
device name zero. The new screen is initialized to graphics mode, cleared and the
parameter table outputs initialized. The v_opnwk (op_l) function is not available
on the Atari ST (only with GDOS.PRG), programmers should use the virtual
workstation function v_opnvwk (op_100).
4.5

<!-- source-page: 134 -->
## Page 134

The Concise Atari ST Reference Guide
The control table
Control
offset
Data
entered
Array
size.B
Function
$0
0
1
$2
2
0
0
$4
4
6
24
$6
6
11
22
$8
8
45
90
$A
10
$C
12
X
Opcode for 'open workstation'
# ofi/p pointpairs
ptsin
#ofo/ppoint pairs
ptsout
Length ofi/p attribute table
intin
Length ofo/p attribute table
intout
Not used
Handle for this device
(out)
Attribute input table (intin)
Intin
Initialdefaults (style,colour etc.)
VDI Op
Offset
code
$0
0
Device driver
(screen = 1)
$2
2
Linetype
(solid = 1)
15
$4
4
Polyline colour index
-
$6
6
Marker type
(dot = 1)
Polymarker colour index
18
$8
8
20
$A
10
Text face
21
$C
12
Text colour index
$E
14
Fill interior style
23
$10
16
Fill style index
24
$12
18
Fill colour index
$14
20
NDC to RDC transform flag (2 only)
0 map full NDC to full RC
1 reserved
2 Raster coordinates
The input ranges required to open a workstation with a specific attribute can
be found, in the table box for that attribute, later in this chapter.
The procedure names are limited to the maximum of eight unique characters
supported by the most C compilers. Note that C external names are prefixed by a
'_' which reduces the uniqueness to seven characters.
4.6

<!-- source-page: 135 -->
## Page 135

GEM VDI
Attribute output table (intout)
Intout
Offset
Default output parameters
Typical b&w
values
$0
0
Maximum pixel width
$27f
639
$2
2
Maximum pixel height
$18f
399
$4
4
Device coordinate flag (0=fine, l=coarse)
always 0
$6
6
Pixel height, microns
mm/1000
Pixel width, microns
mm/1000
372
$8
8
372
$A
10
# character heights (0=continuous)
3
$C
12
# linetypes
7
$E
14
# line widths (0=continuous)
0
$10
16
# marker types
6
$12
18
# marker sizes (0=continuous)
8
$14
20
# faces supported (fonts)
1
$16
22
# patterns
# hatch styles
$18
24
$18
24
$c
12
$1A
26
# simultaneous colours (2=mono)
2
$1C
28
# generalized drawing primitives
Listof thefirst 10 GDP's (-1 ends list)
$a
10
$lE-$30
l=Bar
6=Elliptical arc
2=Arc
7=Elliptical pie
1 to 10
30-48 3=Pie slice 8=Rounded rectangle
4=Circle
9=Filled rounded rectangle
303
5=Ellipse
10=Justified graphic text
330
Attribute listforGDP's
303
$32-$44
0=Polyline
l=Polymarker
2
50-68 2=Text
3=Fill araea
4=None
$46
70
Colour
\ 0=no, l=yes
0
$48
72
Text rotation
1Capability
1
$4A
74
Fill area
1 flags
1
$4C
76
Cell array operation
/
0
$4E
78
# colours (2=mono, 4,16)
2
$50
80
# locatordevices
l=keyboard only
2=keyboard +i/p (
2
mouse)
$52
82
# valuator devices
l=keyboard
1
$54
84
# choice devices
l=function keys
2=button device
1
$56
86
# string devices
l=keyboard
1
$58
88
# Workstation type
0=output only
l=i/p only,
2=input/output
3=reserved,
4=metafile output
2
4.7

<!-- source-page: 136 -->
## Page 136

The Concise Atari ST Reference Guide
Output points table (ptsout)
Ptsout
Output points table
Typical
Offset
values
$0
0
Minimum character width
5
$2
2
Minimum character height
4
$4
4
Maximum character width
7
$6
6
Maximum character height
$d
13
$8
8
Minimum line width
1
'
$A
10
Zero
0
$C
12
Maximum line width
$28
40
$E
14
Zero
0
$10
16
Minimum marker width
$f
15
$12
18
Minimum marker height
$b
11
$14
20
Maximum marker width
$78
120
$16
22
Maximum marker height
$58
88
The GEM VDI calls
Workstation control functions
The following functions set the workstation parameters and defaults for use
by the application:
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
Open
1
0
6
11
45
zero
Set up desktop window
workstation
(device zero) to graphics
*v_opnwk
Call only with GDOS.PRG installed
mode & initialise tables
* Not implemented on the Atari ST
4.8

<!-- source-page: 137 -->
## Page 137

GEM VDI
Workstation control functions cont.
Function
Op
$0
Pointpair
in
out
$2
$4
Integers
in
out
GDP
$6
$8
$A
Device
name
$C
Comments
Close
2
workstation
* v_clswk
0
0
Call only
0
0
with GDOS.PRG installed
Return to alpha mode
Close device and
flush buffers.
Open
100
virtual
screen
vjopnvwk
0
6
11
45
parameters
as opcode 1
(pg 4.6 Intin)
i/p screen
o/p new
window
Permits multiple
windows based on
one screen with
different attributes
Close
101
virtual screen
v_clsvwk
0
0
0
0
Close virtual screens
first to stop further
output to screen.
Clear
3
workstation
v_clrwk
0
0
0
0
Clear the screen.
New page if possible.
Delete buffer data
Update
4
0
0
0
0
-
Execute graphic
workstation
commands waiting.
No effect on screen.
v_updwk
Use to print data
Load
119
0
0
1
1
-
Load additional
font
intin (0)=0, reserved
fonts.
intout(0)=# fonts loaded
intin(O) reserved
*vstjoadjonts
for future use.
Unload
120
0
0
1
0
-
Unload font from
font
intin (0)=0,reserved
memory if no other
live users.
*vstjunloadjonts
intin(O) reserved
Set
129
2
0
1
0
-
Disable/enable
clipping
a,b ——
intin(0)=0_off (default)
clipping of
rectangle
j
<>0_on
output primitive.
vs_clip
L—Cd
ptsin a,b,c,d
* Not implemented on the Atari ST
4.9

<!-- source-page: 138 -->
## Page 138

The Concise Atari ST Reference Guide
Output Functions
The following functions draw the graphic primitives (lines, arc etc.) on the
current device using the current attributes.
Function
Pointpair
Integers
Device
Op
in
out
in
out
GDP name
$0
$2
$4
$6
$8
$A
$C
Comments
Polyline
vjpline
6
n
0
0
0
min of 2 coord pairs
xl,yl x2,y2
etc .
Draw line between
n pairs of points
Poly
marker
vjpmarker
7
n
0
0
0
xl,yl x2,y2
etc.
Draw marker at
each of n pairs
of points.
Text
v_gtext
1
0
n
0
intin (0)=text string (n=string length)
ptsin (0)=lower left corner
ptsin (2)=upper right corner
Filled
9
n
0
0
0
area
n* x,ypoints asper polyline
vjillarea
Uses Op #25 vsf_color for fill colour
Write character string
to device. 0-255
Intin word LSByte
contains character.
Outline if device
can not fill. Close
area if open.
Fill
114
2
rectangle
a,b
0
0
0
Rectangular area fill
ptsin (0)=a ptsin (4)=c
ptsin a,b,c,d
ptsin (2)=b ptsin (6)=d
Uses Op #25 vsf_color for fill colour
vrjecfl
------
array
CD,
I
c,d
4.10
10
2
I—
a,b
Row length'Xc
Cntrl
#Words/row
Cntrl
# Rows Xc
Cntrl
Writing mode
Cntrl
v_cellarray
Contour~~103~T"
fill
intin
ptsin
v_contour
ptsin
Rect
array
0
n
0
-C,d n=length ofcolour index
Colour
Xc
$E
index
$10
array
i
yc
$12
(Intin 0 .. .n)
$14
Not implemented in all systems
..
_.
.„
.
(0)=colour index
(0)=xcoordinate "1Starting
(2)=y coordinate J point
<c
,
CD,
Draw rectangular
cell array,
ptsin a,b,c,d
based on colour
cells Xc * Yc
Writing mode see
Op #32
Flood fill area bound
by edge or colour.
There must not be
a gap

<!-- source-page: 139 -->
## Page 139

GEM VDI
General drawing primitive functions (GDP's)
The GDP's provide the basic graphic primitives of line, arc, ellipse etc.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
GDP
11
n
-
-
-
x
-
(General format)
Bar
11
2
0
0
0
1-
Area attributes
ptsin (0)=comer x coordinate
ptsin (2)=corner y coordinate
Uses Op #25
ptsir (4)=diagonally opposite x coordinate
vsf color attributes
vjoar
ptsir (6)=diagonally opposite y coordinate
Arc
11
4
0
2
0
2-
Line attributes
ptsin (0)=centrex coordinate
ptsin (C) =radius
ptsin (2)=centre y coordinate
ptsin (E):=0
ptsin (4)=0
ptsin (8)=0
intin (0)==start angle"] 0 to
v_arc
ptsin (6)=0
ptsin (A)=0
intin (2)==endangleJ 3600
'New TOS' clears reliability problems ofsmall angles.
Pie
11
4
0
2
0
3-
Area attributes
vjpieslice
Parameters as per arc above
Circle
11
3
0
0
0
4-
Area attributes
ptsin (0)=centre x coordinate
ptsin (6)=0
ptsin (2)=centre y coordinate
ptsi n (8)=radius
v_circle
ptsin (4)=0
ptsin (A)=0
Ellipse
11
2
0
0
0
5-
ptsin (0)=centre x coordinate
ptsin (2)=centre y coordinate
ptsin (4)=radius x axis
Area attributes
vjzllipse
ptsin (6)=radius y axis
Elliptic
11
2
0
2
0
6-
Line attributes
arc
ptsin (0)=centre x coor
intin (0)==start angle-i 0 to
=end angle J 3600
ptsin (2)=centre y coor
intin (2)=
ptsin (4)=radius x axis
vjzllarc
ptsin (6)=radius y axis
4.11

<!-- source-page: 140 -->
## Page 140

The Concise Atari ST Reference Guide
GDP's cont.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
$0
$2
$4
$6
$8
$A
$C
Comments
GDP
11
n
(General format)
-
X
Elliptic pie 11
2
0
2
v_ellpie
Parameters as
0
7
per elliptic arc above
Area attributes
Rounded
11
2
0
0
0
8
-
Line attributes
rectangle
ptsin (0)=corner x coordinate
ptsin (2)=corner y coordinate
ptsin (4)=diagonally opposite x coordinate
vjrbox
ptsin (6)=diagonally opposite y coordinate
Filled
rounded
rectangle
vjfbox
11
Justified
11
graphics
text
vJustified
0
0
0
Area attributes
Parameters as per rounded rectangle
"i" ' 0
2+n~0"
10
-
Text attributes
intin (0)=interword spaceflag
"| zero to
intin (2)=intercharacter space flagj keep as is
intin (4)=first character
"i
Null terminated
intin (4+n)=last characterj string
ptsin (0)= x alignment
ptsin (2)= y alignment
ptsin (4)= string length
ptsin (6)= zero
Intin uses least significant byte of word for character
900
Notation used for
angular specification
1800
270CF
4.12

<!-- source-page: 141 -->
## Page 141

GEM VDI
Attribute functions
The attribute functions determine the output style of all the graphic
primitives; that is colour, line style, character size etc.
Function
Op
$0
Pointpair
in
out
$2
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Comments
Set
writing
mode
vswr mode
Seta
colour
vs color
32
0
0
11*
intin(0)=1,replace
=2,transparent (mask l's)
=3,XOR
=4,reverse transparent (mask 0's)
Out of range uses
replace mode
Modes 2,3 and 4
based on line or
fill pattern mask
14
0
0
4
0
-
Redefine a colour.
v_opnvwk (intout $1A)gives # colours
No action if lookup
intin (0)=colour index
In mono
table is not available
intin (2)=red
\ Colour
any colour or 'out of range'
intin (4)=green
I intensity isset to
Thenumberof colours
intin (6)=blue
/ 0 to 1000 white
is device dependent.
Set
15
0
0
1
1*
polyline
v_opnvwk (intout $C) gives # linetypes
line type
intin (0)=line style
l=solid
2=longdash
3=dot
4=dash-dot
vsljype
5=dash
6=dash-dot-dot 7=user defined.
Most devices support
at least six line styles
Set user
defined
polyline
vsljudsty
113
0
0
1
0
Sets linetype #7
intin (0)=line pattern (16bits)
User defined pattern
for line,
MSB is first pixel.
Set
polyline
width
vsl width
16
1
1
0
0
ptsin (0)=line width
ptsin (2)=zero
On error width is set
to the nearest below
ptsout(0)=width Use odd numbers
ptsout(2)=zero
>= three.
Set polylinel7
colour
vsl color
0
0
11*
intin (0)=colour index
Set
polyline
end style
vsl ends
108
0
0
2
0
intin (0)=start
intin (2)=end
*denotes intoutQ is actual value of intin() used.
Set colour for polyline
operations
0=square (default)
l=arrow
2=rounded
4.13

<!-- source-page: 142 -->
## Page 142

The Concise Atari ST Reference Guide
Attribute functions cont.
Function
Op
$0
Pointpair
in
out
$2
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Comments
0
0
1
Set
18
polymarker
type
vsmjype
intin (0)=marker type
l=dot
2=plus
4=square
5=cross
Set
19
1
polymarker
height
ptsin (0)=zero
vsmjieight
ptsin (2)=y-axis height
Set poly-
20
0
marker colour
vsmjzolor
intin (0)=colour index
1
0
0
0
1"
Set
12
1
2
0
0
character height ptsin (0)=zero
pfsout(O):
ptsin (2)=height ptsout(2>
ptsout(4)
vstjieight
ptsout(6)
Set
107
0
2
1
1*
character cell
intin (0)=cellht ptsout(O):
height
in point size
ptsout(2):
(1 point= 172 inch)
ptsout(4>
vstjpoint
ptsout(6)
All devices support
at least six markers
Defaults on error
^asterisk
to asterisk.
=diamond
Height set is nearest
below on error.
ptsout(0)=x-axis width
ptsout(2)=y-axis height
Set colour for
polymarker
operations.
Size of character
character width
^character height
=cell width
=cell height
All i/p's in raster units
V
character
..
""STze'of cell
^character width
character height
=cell width
=cell height
Ptsout in raster units
V
cell
13
0
0
1
1*
v_opnvwk (intout $48)givescapability
intin (0)=angle requested
Set char
baseline
vector
vst rotation
Angular range
0 to 3600
Not supported by
all devices.
Set text
face
vstjont
21
Set graph
22
text colour
vst color
0
0
11*
intin (0)=face selection
0
0
intin (0)=text colour index
* denotes intoutO is actual value of intinO used.
4.14
Face 1 is built-in
(System face)
Set colour for
next text,
default 1

<!-- source-page: 143 -->
## Page 143

GEM VDI
Attribute functions cont.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
Set text
special
effect
vst_effects
106
0
0
1
r
Default to standard
text
intin (0):bits 0 to 5 set effects
Effect 'on' if bit = 1
Thick, light, skew, underline, outline, shadow respectively
Set
39
0
0
2
2*
graphic text
intin (0)=0,left1,centre 2,right
position
intin (2)=3,4,0,1,2,5 respectively
vst_alignment
bottom, descent, base, half, ascent, top
Set fill
23
0
0
1
1*
interior style
intin (0)=0 to 4 respectively
vsfjnterior
Hollow, solid,pattern, hatch, user-defined
Set fill
24
0
0
1
1*
style
intin (0)=0solid colour
index
2,1 to 24 patterns
vsfjstyle
3,1 to 12 hatch
\
Seepg 4.26
Set fill
25
colour index
vsfjcolor
Set fill
104
peri visible
vsf_perimeter
Set user
112
6
-defined
fill pattern
vsfjudpat
0
0
11*
intin (0)=colour index
0
0
11*
intin (0)=0_invisible, <>0_visible
0
16*n
0
intin (0-15)=lst plane
intin (16-31)=2nd plane etc.
900
Left/right/centre
justify. Vertical position
defaults to base (zero)
Seepg 4.26
Set future polygon
fill style
Set pattern or hatch
type. No effect if
interior hollow, solid
or user defined.
Set future polygon
fill colour
Set on/off
fill outline
Pattern 16 words/plane
Bit 15 of word_l upper
left bit, Bit 0 last_word
lower right bit
Notation used for
1800_
angular specification
270(7
♦0
* denotes intoutQ is actual value of intin() used.
4.15

<!-- source-page: 144 -->
## Page 144

The Concise Atari ST Reference Guide
Raster operations
Raster operations are the manipuation of rectangular blocks of bits in
memory or pixels on screen, the area is defined in memory form definition blocks
(MFDB) that consists of:
$00
$04
$06
$08
$0A
$0C
$0E
Memory pointer
Width in pixels
Height in pixels
Word width
Format flag
Memory planes
Reserved
32-bit address of pixel 0,0
Raster area dimensions
Pixel width/word size
1=standard, 0=device specific
#planes in raster area
3 reserved words
The raster planes word-bit-pixel relationship follows the format shown in the
TOS overview 2.13, the top left hand corner pixeladdress being 0,0
Colour index table
Pixel
Index Colour
Pixel
Index Colour
0000
0
white
1000
9
grey
0001
2
red
1001
10
light red
0010
0011
3
6
green
yellow
blue
1010
1011
11
14
tight green
light yellow
light blue
0100
4
1100
12
0101
0110
0111
7
5
8
magenta
cyan
low white
1101
1110
1111
15
13
1
light magenta
light cyan
black
Raster operations perform logical translations of the source to the destination
over the original destination pixel area. The required logic operation is passed as
an argument in intin(O) as follows:
Mode
Function
Mode
Function
0
D'=0 (all white)
8
D'=NOT [S OR D]
1
D'=S AND D
9
D'=NOT [S XOR D]
2
D'=S AND [NOT D]
10
D'=D INVERT
3
D'=S
11
D'=NOT D
4
D'=[NOT S] AND D
12
D'=S OR [NOT D]
5
D'=D
13
D'=[NOT S] OR D
6
D'=S XOR D
14
D'=NOT [S AND D]
7
D'=S OR D
15
D'=l (all black)
S=Source
Mode 3=replace
D=Destination
Mode 4=erase
D'=Destination pixel final state
Mode 6=XOR
4.16

<!-- source-page: 145 -->
## Page 145

Raster operations
Function
Op
$0
Pointpair
in
out
$2
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Copy
109
4
0
1
0
raster
ptsin ()=a,b,c,d,e,f,g,h order
opaque
intin (0)=logic operation
cntrl $E=Address.L of source MFDB
cntrl $12=Address.L of destination MFDB
vrojzpyfm
Copy
raster
transparent
vrt
Transform
form
121
4
0
3
0
ptsin ()=a,b,c,d,e,f,g,h order
intin (0)=write mode
intin (2)=colour for l's
intin (4)=colour for 0's
cntrl $E=Address.L of source MFDB
cntrl $12=Address.L of destination MFDB
write_mode a replace
b transparent (mask l's)
c XOR mode
cpyfm
d reverse transparent (mask 0's) e,f
110
0
0
0
0
V
a,b-
r
e,f'
r
a,b-
r
vrjrnfm
cntrl $E=Address.L of source MFDB
cntrl $12=Address.L of destination MFDB
The destination block must be verified
GEM VDI
Comments
Copy rectangular
block from source to
destination.
If source <> dest
then source size used
—c,d
Source
•g,h
Destination
Copy mono block
from source to
destination
If source <> dest
then source size used
—c,d
Source
-g,h
Destination
Toggle raster area
from standard to
device-specific form.
Get
pixel
105
1
0
0
I
-
Return pixel value
and colour index
ptsin (0)=x coordinate intout(0)=pixel value (0 or 1)
v_get_pixel
ptsin (2)=y coordinate intout(2)=colour index
Background colouris accessible on only somedevices.
4.17

<!-- source-page: 146 -->
## Page 146

The Concise Atari ST Reference Guide
Input functions
There are two types of input function generally provided by GEM:
'Request and wait' for reply
and
'Request and sample' current status.
Pointpair
Integers
Device
Function
Jp
in
out
in
out
GDP name
Comments
W
$2
$4
$6
$8
$A
$C
Set
111
0
0
37
0
Redefine cursor pattern
mouse
mtin (0)=x coordinate
Bit 15 of word 1 upper
form
ntin (2)=y coordinate
left bit of pattern.
ntin (4)=1, reserved
ntin (6)=mask colour
ntin (8)=data colour (usually 1)
ntin ($A-$28)=16 word mask bits pixel.
Data under mask is
vscjorm
ntin ($2A-$48)=16 word data bits
saved.
Exchange
118
0
0
0
1
Goto user-written
timer interrupt
cntrl $E=Address.L of new routine
interrupt routine
vector
re•turn
cntrl $12=Address.L of old routine
on timer tick.
vexjimv
intout(0)=milliseconds per tick
Disable interrupts
Show
122
0
0
10
Show cursor if
cursor
intin (0)=0, show cursor
'show'='hide' or
<> 0, show if # of
intin(0)=zero
v_show_c
show calls = # hide calls
Hide cursor 123
0
0
0
0
Hide cursor (default)
v_hide_c
Operates as per 'show cursor'
Sample
124
0
10
1
Return button state
mouse
ptsout(0)=x coor \ cursor
0==none
l=left key
button state
ptsout(2)=y coor /
2-bright key 3=both keys
vqjnouse
intout(0)=return button state
Exchange
125
0
0
0
0
Go to routine on
button
cntrl $E=Address.L user routine
button state change
change retu rn
cntrl $12=Address.L old routine
Uses DO.W for button
vector
keys as above.
vex_butv
(Save and restore registers)
Disable interrupts
4.18

<!-- source-page: 147 -->
## Page 147

Function
Op
$0
Input functions cont.
Pointpair
Integers
in '
out
in
out
$2
$4
$6
$8
Device
GDP name
$A
$C
Exchange
126
0
0
0
0
mouse
cntrl $E=Addr.L user routine
movement return
$12=Addr.L old routine
vector
x an y coords maybechanged
vexjnotv
after being stored inhardware register
Exchange
127
0
0
0
0
cursor
cntrl $E=Addr.L user routine
change
return
$12=Addr.L old routine
vector
routine can be used to draw
vexjzurv
specialcursor.
Sample
128
keyboard
state
information
vq_key_s
0
0
0
intout(O),
bit
1
0, right shift
1, left shift
2, Control
3, Alternate
GEM VDI
Comments
Goto routine on
mouse movement.
Uses DO.W &D1.W
to store x & y.
Disable interrupts
Goto routine on
cursor state change
Uses DO.W &D1.W
to store x & y.
Disable interrupts
Return current state
of Keyboard shift-alt
- control keys.
Zero bit key up
One bit key down.
Functionscallinguser written codeshould not enable interrupts
Registers may need to be restored.
4.19

<!-- source-page: 148 -->
## Page 148

The Concise Atari ST Reference Guide
Thefollowing GEM VDI functions arenot implemented in the AtariST ROM,
but are included for completeness:
Input functions (Not implemented)
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
Set
33
0
0
2
1
Set i/p mode for device
input
intin (0)=Logical input device
to request or sample.
mode
l=locator, 2=valuator
(locator is mouse or
3=choice,
4=string
cursor keys) Intout
vsinjnode
intin (2)=input mode (l=req, 2=sample) shows mode selected.
Input
28
110
1
Return position of
locator,
ptsin (0)=initial x coor
intout(0)=
locator device.
request
ptsin (2)=initial y coor
terminate
Screen tracks cursor
mode
ptsout(0)=final x coor
character
till terminated by
vrqjocator
ptsout(2)=final y coor
(LSByte)
key/button press
Input
28
1
1/0
0
0/1
Return position (NDC)
locator,
ptsin (0)=init x coor
intout(0)=
of locator device
sample
mode
ptsin (2)=init y coor
terminate
ptsout(0)=new x coor
character
If set
o/p's
new coor
1
0
(cursor
ptsout(2)=new y coor
(LSByte)
key press
no i/p
0
1
change/
(A tablet or a mouse terminate
0
0
event)
characters begin at 20H, 32dec)
key press &
vsmjocator
If 2 locators, either may input
new coor
1
1
Input
29
0
0
12
Return value of
valuator,
intin (0)=initial value
valuator device.
request mode
intout(0)=output value
arrow keys, range
vrqjvaluator
intout(2)=terminator
1 to 100.
Input
valuator,
29
0
0
10/2
Return value of
intin (0)=initial value
valuator device.
sample
mode
intout(0)=new valuator value
intout(2)=keypress, if event
cntrl $8
event
0
nothing
occured
1
valchange
vsm_valuator
2
key press
4.20

<!-- source-page: 149 -->
## Page 149

GEM VDI
Input functions (Not implemented) cont.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
Input
30
0
0
11
Return choice status
choice,
intin (0)=lnitial choice number
of device chosen.
request mode
(range 1 to device - Atrari ST 10 -
If invalid return
dependent maximum)
choice number
vrq_choice
intout(0)=terminator key (1-10) or ASCII code
Input
30
0
0
0
1
Return choice status
choice,
intout(0)=0, choice number (1 to 10)
of device chosen.
sample mode
cntrl $8=0, nothingoccured
=1, sampled o'k
intout(0)=0 if
vsmjkoice
unsuccessful.
Input
31
1
0
2
L
Return a string from
string,
ptsin (0)=screen x coor
L=array
specified device.
request
ptsin (2)=screen y coor
length
Terminate on CR
mode
intin (0)=maximum string length
or intout full. If
intin (2)=0, no echo
intin(O) is negative
vrq_string
1, echo at ptsin
pg D4 defines keyboard
Input
31
10
2
0/0
Return a string from
string
ptsin (0)=screen x coordinate
specified device.
sample
mode
ptsin (2)=screen y coordinate
Terminate on CR,
intin (0)=max string length (absolute)
intout full or
intin (2)=0, no echo
no more data. If
1, echo at ptsin
intin(O) is negative
vsm_string
cntil(8)=0, no characters returned
pg D.4 defines keyboard
4.21

<!-- source-page: 150 -->
## Page 150

The Concise Atari ST Reference Guide
Inquire functions
The inquire functions return the current attribute settings ofa specific device.
Function
Op
$0
Pointpair
in
out
$2
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Comments
Extended
inquire
function
vqjzxtnd
4.22
102
0
6
1
45
intin (0)
=0 open workstation values
=1 extended inquire
intout(O)
=0 not screen
=1 separate screen
\ Alpha &
=2 common screen
/ graphics
=3 separate image mem \Common alpha &
=4 common image mem /graphic controller
=# pallette background colours
(may not be same
=Text effects supported (op 106)
as $4E(78)
=Scaling 0=no 1= yes
v_opnwk
=Number ofplanes
=Support looxup table 0=no l=yes
intout(2)
intout(4)
intout(6)
intout(8)
intout($A)
intout($C) =# 16x16 pixelraster operations/sec (Speedfactor)
intout($E) =Contour fill capability 0=nol=yes
intout($10) ^Character rotate 0=no, 1=90' steps only, 2=cont.
intout($12) =# writing modes available
intout($14) =Input mode 0=none, l=request, 2=sample
intout($16) =Text alignment 0=no, l=yes
intout($18) =Inking ability 0=no, l=yes (Plotter - colour pen)
intout($lA) =Rubberbanding 0=no, l=lines,
2=lines & rectangles (Printer - colour ribbon)
intout($lC)=Maximum ptsin -l=no max
intout($lE) =Maximum intin -l=no max
intout($20) =Number of keys on mouse
intout($22) =Styles for wide lines 0=no, l=yes
intout($24) =Writing modes for wide lines
intout($26-$58)
reserved, contains zero words
ptsout(0-$16)
reserved, contains zero words
Return extra device
information not in the
open workstation call or
return open workstation
values.

<!-- source-page: 151 -->
## Page 151

Function
Op
$0
Inquire
26
colour
representation
vqjzolor
Inquire
35
current
polyline
attributes
vql_attributes
Inquire
36
current
polymarker
attributes
vqm_attributes
GEM VDI
Inquire function cont.
Pointpair
in
out
$2
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Comments
0
0
2
4
intin (0)=request colour index
intin (2)=0_return colour value request
l_return colour values available
intout(0)=colour index
intout(2)=red intensity (0-1000)
intout(4)=green intensity (0-1000)
intout(6)=blue intensity (0-1000)
Return value of colour
index in RGB units
Intout(0)=-1 'out
of range'
0
1
ptsout(O):
ptsout(2)=
intout(0)=
intout(2)=
intout(4)=
0
5
dine width
=zero
line type
line colour
write mode
Return all attributes
that affect polylines
intout(6)=Start end style
intout(8)=Finish end style
0
10
3
ptsout(0)=width
ptsout(2)=height
intout(0)=marker type
intout(2)=marker colour
intout(4)=writing mode
Return all attributes
that affect polymarkers
Inquire
37
0
0
0
5
current
intout(0)=interior style (Op #23)
fill area
intout(2)=colour
attributes
intout(4)=fill style (Op #24)
intout(6)=writing mode (Pg 4.13)
vqfjxttributes
intout(8)=fill perimeter status
Return all attributes
that affect fill areas
4.23

<!-- source-page: 152 -->
## Page 152

The Concise Atari ST Reference Guide
Function
Op
$0
Inquire function cont.
Pointpair
in
out
$2
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Inquire
38
0
2
0
6
current
ptsout(0)=character width
graphic
ptsout(2)=character height
text
ptsout(4)=cell width
attributes
ptsout(6)=cellheight
intout(0)=current graphic text face
intout(2)=current graphic text colour
intout(4)=baseline angular rotation (0-3600)
intout(6)=horizontal alignment
intout(8)=vertical alignment
intout($A)=writing mode (op #32 Pg 4.13)
Comments
Return all attributes
that affect
graphic text.
vqt_attributes
Inquire
116
text
extent
0
4
intinQ =
n
0
# words in text (low bytes)
ptsout(0)=x coordinate
\ bottom
ptsout(2)=y coordinate
/ left
ptsout(4)=x coordinate
\ bottom
ptsout(6)=y coordinate
/ right
ptsout(8)=x coordinate
\ top
ptsout($A)=y coordinate
/ right
ptsout($C)=x coordinate
\ top
ptsout($E)=y coordinate
/ left
Return a rectangle
that encloses the
specified string.
Yaxis
vqt_extent
Inquire
117
0
3
1
1
character
intin (0)=character value in ADE form
cell
ptsout(0)=cell width
ptsout(2)=0
width
ptsout(4)=left char delta
ptsout(6)=0
ptsout(8)=right char delta
ptsout($A)=0
vqtjvidth
intout(0)=ADE of inquire value
-1 if invalid character
Inquire
130
6
6
1
33
Return 32 character face
facename
intin (0)=elementnumber
descriptor (text),
and index
intout(0)=ID number
First 16 characters face
vqtjxame
intout(2-$40) 32 ADE code
Second 16 style and weight
(lowbytes)
4.24
TEXT
Xaxis
Return the character cell
width for specified
character in current
text face.
Rotation and special
affectsignored/.

<!-- source-page: 153 -->
## Page 153

Function
Op
$0
Inquire function cont.
Pointpair
in
out
$2_
$4
Integers
in
out
$6
$8
Device
GDP name
$A
$C
Inquire
27
2
0
0
n
cell
cntrl $E=row length
\colour index
array
cntrl $10=# rows
/array
return
cntrl $12=# elements/row
\used in colour
return
cntrl $14=# rows
/index array
return
cntrl $16=errors, 0=no errors, l=pixel colour indeterminate
ptsin (0)=x coor
ptsin (2)=y coor (lower left)
ptsin (4)=x coor
ptsin (6)=y coor (upper right)
intout colour index array (1 row at a time)
-1 indicates indeterminate pixel colour
vqjzellarray
Inquire
115
input
mode
vqinjnode
0
0
11
intin (0)=logical device
l=locator
2=valuator 3=choice,
4=string
intout(0)=i/p mode
l=request, 2=sample
GEM VDI
Comments
Return cell array
definition of pixels
Return current i/p
mode for device.
Inquire
131
0
5
0
2
-
Return current face
current
ptsout(0)=maximum normal cell width size information.
face
ptsout(2)=baseline to bottom
information
ptsout(4)=maximum extra skew width
ptsout(6)=baseline to descent line
ptsout(8)=left skew extra
seepg4.26
ptsout($A)=baseline to half distance
ptsout($C)=right skew extra
ptsout($E)=baseline to ascent
ADE=
ASCII
ptsout($10)=zero
decimal
ptsout($12)=baseline to top distance
equivalent
intout(0)=first character
\ in face
vqtjontinfo
intout(2)=last character
/ ADE
4.25

<!-- source-page: 154 -->
## Page 154

The Concise Atari ST Reference Guide
VDI
Style Index patterns
0,n
VDI
Text
alignment
CHARACTER
WIDTH
TOP
ASCENT
HALF
BASE
DESCENT.
BOTTOM-
'•'•'•TTTT
Cr^C05±[
5SS
2.9
vyyyyv
:jr
•SKkkkKR
'!•;•:•:•"•:•'
2,16
2,24
igtonp^Bj
TOP
A3CENT
4.26
CELL
WIDTH
3,8
3J0
3,11
3,12
3,5
3,6
V////A
3,7
3,8
CHARACTER
POSITION
LEFT
OFFSEw
, V
/
RIGHT
LEADING
OFFSET

<!-- source-page: 155 -->
## Page 155

GEM VDI
Escape functions
The escape functions allow
the programmer to access special device
functions.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
$0
$2
$4
$6
$8
$A
$C
Escape
5
(General format)
id
Inquire
5
addressable
alpha
character cells
vq_chcells
0
0
0
2
1-
intout(0)=# rows
intout(2)=# columns
-1 no cursor addressing
Comments
Get number of vertical
rows and horizontal
columns for alpha
cursor.
Exit
5
alpha mode
v_exit_cur
0
0
0
0
2-
Enter graphics mode
and exit alphanumeric
mode.
Enter
5
alpha mode
v_enter_cur
0
0
0
0
3-
cursor set to upper leftofcharacter cell
Exit graphics mode
and enter
alphanumeric mode.
Alpha
5
cursor up
vjcurup
0
0
0
0
4-
Do nothing ifat top
Move alpha cursor
up one row.
Alpha
5
cursor down
vjzurdown
0
0
0
0
5-
Do nothing if at bottom
Move alpha cursor
down one row
Alpha
5
cursor right
v_curright
0
0
0
0
6-
Donothing ifat right edge
Move alpha cursor
right one column.
Alpha
5
cursor left
v_curleft
0
0
0
0
7-
Do nothing ifat left edge
Move alpha cursor
left one column.
Home
5
alpha cursor
v_curhome
0
0
0
0
8
Homeusuallytop left
Move cursor to
home position.
4.27

<!-- source-page: 156 -->
## Page 156

The Concise Atari ST Reference Guide
Escape functions cont.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
$0
$2
$4
$6
$8
$A
$C
Comments
Erase from current
cursor position
to end of screen.
Erase to
5
end of
alpha screen
v
eeos
Erase to
5
end of
alpha text line
v eeol
Direct
5
alpha cursor
address
vs curaddress
Output
5
cursor
addressable
alpha text
v
curtext
0
0
0
0
9
No cursor position change
0
0
0
0
10
No cursor position change
0
0
2
0
11
intin (0)=row (1 to n)
intin (2)=column (1 to n)
0
0
n
0
12
-
n=number of characters in string
intin ()=text string in ADE
Erase from current
cursor position to
end of line.
Place cursor at the
specified row and
column.
Displaya string of
alpha text from
current cursor
position.
Reverse
5
video on
v_rvon
0
0
0
0
13
-
Display following
text in reverse video.
Reverse
5
video off
vjrvoff
0
0
0
0
14
-
Display following
text in normal video.
Inquire
5
current
alpha cursor
address
vq_curaddress
4.28
0
0
0
2
15
-
Return current
intout(0)=row# (minimum one)
alpha cursor
intout(2)=column# (minimum one)
position.

<!-- source-page: 157 -->
## Page 157

GEM VDI
Escape functions cont
Function
Op
$0
Pointpair
Integers
in
out
in
out
GDP
$2 "
$4
$6
$8
$A
Device
name
$c
Comments
Inquire
5
tablet
status
vq_tabstatus
0
0
0
1
16
intout(0)=0, not available
-1, available
Return availability
status of tablet,
mouse, joystick etc.
Hard
5
copy
vjiardcopy
0
0
0
0
17
Copy screen to
specific printer.
Place
5
graphic
cursor at
location
vjispcursor
2
0
0
0
18
ptsin (0)=x coordinate
ptsin (2)=y coordinate
The positioning function
Place crosshair
on screen.
is not accurate
Remove
5
last graphic
cursor
vjrmcursor
0
0
0
0
19
4.29

<!-- source-page: 158 -->
## Page 158

The Concise Atari ST Reference Guide
Escape functions (Not implemented)
The following Escape functions are available when loaded via the expanded
GDOS file, they are included for completeness; as is a discussion on VDI bit
image file format.
Pointpair
Integers
Device
Function
Op
in
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
Form
5
0
0
0
0
20
-
Pages printer but
advance
keeps screen display
vjormjidv
Output
5
2
0
0
0
21
-
Copies specified
window
ptsin (0)=xcoordinate Window
window to printer
ptsin (2)=y coordinate / corner
Adjacent pictures
ptsin (4)=x coordinate \opposite
may not join.
vjjutputjvindow ptsin (6)=y coordinate / corner
Clear
5
0
0
0
0
22
-
Empty the VDI
display list
v_clear_disp_lis
printer buffer
Output
5
0-2
0
L+2
0
23
-
Enables printer
bit
cntrl (2)
=0, get coordinates from file to process bit
image
=1, upper left specified
image file.
file
=2, user specified coords
Page placement
ptsin (0)=x upper left
\ coordinates
by specifying
ptsin (2)=y upper left
1if
or by default
ptsin (4)=x lower right 1specified
ptsin (6)=y lower right /
intin (0)=Aspect ratio flag
Pixel ratio
provides for
0_ignore, l_pixel ratio, 2_
intin (2)=Scaling 0_uniform, l_x and
intin (4)=First character of file name
page ratio
printing
y
circles
(length L)
vjbitjmage
intin (2n+2)=Last (nth) character file name
Select
5
0
0
1
1
60
-
Allows IBM
palette
intin (0)=0_use red, green, brown
compatable
=1, use cyan, magenta, white
palette
vsjpalette
intout(0)=palette selected
selection.
4.30

<!-- source-page: 159 -->
## Page 159

GEM VDI
Escape functions (Not implemented)
Function
Pointpair
Integers
Device
Op
in •
out
in
out
GDP name
Comments
$0
$2
$4
$6
$8
$A
$C
Inquire
palette
film types
vqpjilms
5
0
0
0
125
91
-
Return film driver
intout 5 sets of 25 ADE byte descriptor strings
Inquire
palette
driver
state
vqpjstate
Set
palette
driver
state
0
0
0
20
92
-
Return film driver
intout(0)=port # 0=first comms port
status block.
intout(2)=film number (0 to s)
intout(4)=lightness control(-3 +3) 1/3 f_stop steps
intout(6)=0_noninterlace, l_interlace
intout(8)=planes(l to 4)
(ADE format)
intout($0A-$28)=colour codes for 16 colours.
0
0
0
20
93
-
Set film driver
intout(0)=port # 0=first comms port
status block.
intout(2)=film number (0 to 4)
intout(4)=lightness control(-3 +3)1/3 f stop steps
intout(6)=0_noninterlace, l_interlace
vspjstate
intc)Ut($ 3-$26)=color codes for 16 colon
Save
5
palette
driver state
vspjsave
0
0
0
0
94
-
Save current
driver state to
disk
Supress
5
palette
messages
vspjnessage
0
0
0
0
95
-
Supress user
prompts and error
messages
4.31

<!-- source-page: 160 -->
## Page 160

The Concise Atari ST Reference Guide
Function
Op
$0
Palette
error
inquire
vqp_error
Update
"jf"
metafile
extents
vjnetajzxtents
Write
metafile
item
v
write meta
Change
5
GEM VDI
filename
vmjilename
Pointpair
Integers
in
out
in
out
$2
$4
$6
$8
Device
GDP name
$A
$C
0
0
0
1
96
-
intout(O) =0, no error
=1, open dark slide for print film
=2, no port at specified location
=3,palette not found at port specified
=4, video cable disconnected
=5,OS does not allow memory allocation
=6, not enough memory for buffer
=7, memory not deallocated
=8, driver file not found
=9, driver file incorrect type
=10, prompt user to process print film
2
0
0
0
ptsin (0)=min x value
ptsin (2)=min y value
ptsin (4)=max x value
ptsin (6)=max y value
98
-
\
I bounding
I rectangle
n
0
1
0
99
-
ptsin user defined data
intin user defined data
intin(O)=sub-opcode
Sub opcodes 0 to 100 reserved
0
0
1
0
100
-
intin ()=path/filename
upto 74 characters
Notation used for
angular specification
1800
•4-
900
270CF
4.32
Comments
Return error code
Update file
header enabling
application to
get indication of
a minimum window.
Intin and ptsin
data written to
metafile with a
sub opcode >100
see pages 4.35 to 4.36
Rename metafile
from GEMFILE.GEM
to
,GEM

<!-- source-page: 161 -->
## Page 161

$00
$02
$04
$06
$08
$0A
$0C
$0E
$10
$12
to
$20
GEM VDI
Bit image file format
There are two parts to the bit image
Header
file, a 16 word header, and a block of
raw pixel data
codified raw data.
0
2
4
6
8
10
12
14
16
18
to
32
File header
upper left x
upper left y
lower right x
lower right y _
page width
page height
pixel width ~|
pixel height J
bitsper pixel
Bit
image
in microns
Zero, reserved
Raw data formats
Source
device
The four methods of data coding may be mixed in any desired combination
within a file.
$00
$01
$00
$01
$02
<128bvtes
<256
-1
<128bvtes
<256
Run length encoding (default)
Run length
colour index data
Use a two byte subheader to define
the data, which must be less than 128.
The pixels may line wrap.
Extended run length encoding
Opcode
^° cater f°r pixel runs >127, the
extended run length extended run includes a count of 128
colour index data
providing a range of 128 to 255 pixels.
The pixel line may wrap.
4.33

<!-- source-page: 162 -->
## Page 162

The Concise Atari ST Reference Guide
Raster encoding
$00
-2
$01
$02
1
2
Op code
# pixels in stream
packed colour indices
6
00 0I10 1I00Q1 01 1 001 OH 0
0
11
I
Use either:
Raster
encoding
packs color indices into
bytes in
the
following
format:
Pixels
Bits
Bytes
1
(black and white)
3
(four colour)
or
4
(sixteen colour)
bits per pixels format (offset $10in the header).
Raster run encoding
$00
$01
$02
$03
4.34
<256
Op code
repeat count
# pixels in stream
packed colour indices
Raster run encoding permits
the efficient coding of repeated
pixel patterns. It is in the same
form
as
raster
encoding
but
includes a repeat count in the
header.

<!-- source-page: 163 -->
## Page 163

GEM VDI
Metafile Sub opcodes
The Metafile functions are not implemented on the Atari ST,but are included
for completeness of the GEM operating environment. Installation of the file
Meta.sys will provide the functions, if you can get it?
Output page (Not implemented)
There are two reserved GEM output codes for configuring the output page:
Physical page size, which defines the output area and Coordinate window,
specifying the coordinate system used in the metafile.
Function
Op
$0
Pointpair
Integers
in
out
in
out
$2
$4
$6
$8
Device
GDP name
$A
$C
Physical
5
0
0
3
0
99
-
page
intin (0)=sub opcode 0
size
intin (2)=page width
\ tenths of
intin (4)=page height / millimeters
Coordinates
6"
6
5
0
99
-
Sub opcode T
window
intin (0)=sub opcode 1
intin (2)=x coordinate \ lower left corner
intin (4)=y coordinate / of window
intin (6)=x coordinate \ upper right corner
intin (8)=y coordinate / of window
Comments
Sub opcode 0
4.35

<!-- source-page: 164 -->
## Page 164

The Concise Atari ST Reference Guide
Metafile sub opcodes (Not implemented) cont.
GEM Draw
There are a number ofreserved GEM output codes used byGEM draw:
Group:Start and end enclosea set of primitives.
Draw area type primitive: Start and end indicate that enclosed functions are
subject to the area type primitive block that follows the start function.
Attribute shadow: On and offindicate enclosedprimitives are ignored as they
areused to draw a drop shadowfor thefirstprimitive following'off.
Set no line style: Subsequent area type primitives arenot outlined.
Function
Op
$0
Pointpair
Integers
Device
in
out
in
out
GDP name
$2
$4
$6
$8
$A
$C
Comments
Start
5
group
0
0
1
0
99
-
intin (0)=sub opcode 10
Bracket a set of
primitives as a
group for a
End
5
group
0
0
1
0
99
-
intin (0)=subopcode 11
GEM DRAW
application
Start draw 5
area type
primitive
0
0
1
0
99
-
intin (0)=sub opcode 80
Use the vertices
of the first
primitive (except text)
End draw
5
area type
primitive
0
0
1
0
99
-
intin (0)=subopcode 81
to define a
GEM DRAW area
type primitive.
Set
5
attribute
shadow on
0
0
1
0
99
-
intin (0)=sub opcode 50
Only draw a drop
shadow on the first
primitive, ignore
Set
5
attribute
shadow off
0
0
1
0
99
-
intin (0)=sub opcode 51
remaining shadow
primitives until next
off sub-opcode.
Set no
5
line style
0
0
1
0
99
-
intin (0)=sub opcode 49
Subsequent area
type primitives
not to be outlined
4.36

<!-- source-page: 165 -->
## Page 165

GEM AES
Chapter 5
GEM AES
GEM AES function calls
5.2
General
5.2
AES parameter block
5.3
Control table
5.3
Global array
5.3
Typical AES application call
5.4
Handles and coordinates
5.4
AES parameter block sizes
5.5
GEM AES components
5.5
The GEM AES Libraries
5.6
Application library
5.6
Event library
5.8
Keystroke selection
5.11
Icon selection
5.11
Menu library
5.12
Menu bar control
5.13
Object library
5.14
Object tree
5.14
Object library tables
5.15
Font types
5.16
Colour fields
5.16
Form library
5.20
Edit keys
5.21
Alerts
5.22
Graphic library
5.24
Scrap library
5.27
File selector library
5.28
Window library
5.29
Window parts bit representation
5.30
Resource library
5.35
Data structure types
5.36
Shell library
5.37
5.1

<!-- source-page: 166 -->
## Page 166

The Concise Atari ST Reference Guide
GEM AES function calls
A set of application environment services (AES) function calls are available to
the programmer, they consist of routines that make extensive use of the VDI
function calls, and a dispatcher that provides a limited multitasking capability.
The GEM VDI calls generally manage graphic outputs to peripheral devices,
screen, printer etc. whereas GEM AES calls usually handle graphics input. The
calls are grouped into eleven libraries that provide a varietyoffacilities:
Application library: controls the access to the other AES libraries.
Event library:responds to user inputs from mouse,keyboard or elapsed time.
Menu library: text options.
Object library: data collections that describes a displayed object, eg a box, an
icon.
Form library: a means ofobtaining information by the use ofa list ofquestions.
Graphics library: a set of routines for manipulating the outline of a rectangular
box.
Scrap library:routines that allow the interchange of data between applications.
File selector library: user selection of a file from a displayed directory or a file
via a filename and path.
Window library: manages up toeight GEM AES windows.
Resource library: provides the interface between the application and its data and
files.
Shell library: enables an application to invoke another application and to keep
track of the calling command and tail.
Within GEM AES there is a limited multitasking environment created by the
dispatcher;
a routine
that
activates
processes sequentially
simulating
a
multitasking environment. The dispatcher maintains two process queues, the
'ready' for processing list and the 'not ready' list, where processes are typically
waiting for a user input, an input from another process or a specified time delay.
Each 'ready' process is allowed a predefined period of CPU time before being
returned to the end of the 'ready' queue, the environment is saved, the queues
updated and control passed to the next item in the 'ready' queue.
Access to the AES functions is through an extended BDOS call and the AES
parameter block (six longword pointers to the tables; cntrl, global array, input
and output attributes and input and output addresses). The AES parameter
block, control table and global array have the following formats:
5.2

<!-- source-page: 167 -->
## Page 167

AES parameter block
$00
Control
table pointer
$04
Global
array
$08
I/P attribute
table pointer
$0C
O/P attribute
table pointer
$10
I/P addlress
table pointer
$14
O/P address
table pointer
$18
control
global
int
in
int out
addr_in
addr_out$08
$0A
Control table
$00
$02
$04
$06
Op code
Length of i/p
coordinate table
Length of o/p
coordinate table
Length of i/p
address table
Length of o/p
address table
GEM AES
Table
length
in
words
Table
length
in
longwords
Global array
0
GEM AES version identification word
2
Max # concurrent applications supported
4
Unique application identifier
6
Longword user data as required
10
Pointer to resource load address tree, initially zero
14
Zero, address of memory allocations
18
Zero, memory length, screen colours
22
Zero
26
Zero
30
The minimum size of an input table is one word, which must contain zero if
no parameters are being passed.
$00
version
$02
count
$04
id
$06
private
$0A
ptree
$0E
reserved
$12
reserved
$16
reserved
$1A
reserved
$1E
5.3

<!-- source-page: 168 -->
## Page 168

The Concise Atari ST Reference Guide
Typical AES application call
A typical sequence ofcalls for an application might be:
a) Initialize and free unused memory, set up GEM parameter blocks and
tables APPLJNIT [10] must be called first).
b) Open (virtual)workstation and get the screenresolution,.
c) Load a resource file, applicable to the current screen resolution and
number of colours available, into memory.
d)Gettheaddress ofspecific resource objects andstorethem in memory.
e)Get the address of the resourcemenu bar and call'display menu'.
f) Find the size and location of window WINDGET, identify window as a
desktop (handle=0), get the windowswidth/height (get_field=4) and draw icons.
g) Wait for a user action, a keystroke, mouse button click or movement, GEM
AES message or a specified time delay as either individual occurences or
combined events.
h) Select from the menu, normally by moving the mouse to the menu bar.
The message buffer is updated automatically and the process waiting for the
input is moved to the 'ready list' and progressed to the next stage.
i) Reserveand then box a space to hold the dialog which is tested for an exit.
On exit, any highlighting should be deselected.
j) Further user selections, could entail keyboard entries, icon selection etc.
...program...
One of the first operations of an application is to create an active window,
which may be sized, redrawn, updated and finally closed.
Handles and coordinates
Note that VDI calls use 'device' handles and AES 'window' handles - further
confusion may arise in the use of 'file' handles - they are all different, beware !!!!
The coordinate systems differ also !
x,y
width
x1,y1
height
AES
VDI
x2,y2
5.4

<!-- source-page: 169 -->
## Page 169

GEM AES
AES Parameter block sizes
The numbers of parameters required by the various functions are detailedin
the tabular format:
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
The table contains details of the parameter inputs and outputs; note that a
zero indicates a block filled with a zero.
GEM AES components
Library
Subroutines
Limited multitasking
kernal and dispatcher
Desk accessory
buffer
Menu alert
buffer
Monitor mouse
movement and
display error and
system messages.
Draw objects
Resident in
memory at
all times
Up to six
desk accessories
Desk accessories run in a
specially designed window
on top of the GEM desktop
or any other application
Dispatcher
PRIMARY •
APPLICATION
word processor
spreadsheet
database etc.
Contains the .ACC
files for the desk
accessories.
Up to 6, the files
remain in memory
until the user
exits from AES.
Screen manager
Monitor mouse action
when outside the
work area.
The screen manager
handles all events in the
border area of the top
window, the menu bar
and the drop down menus.
Update 'ready' and 'not-ready'
lists of the processes on each
AES call.
Use EVNTTIME tc
ensure a sequencing ifthere
are no AES calls.
Drop down menus
and alert boxes always
appear on top of a
window, Icon or dialog.
AES redraws these
from this buffer when
the menu is erased.
Up to 1/4 screen
capability and faster
than an application
redraw.
Shell
Runs on top of the limited
multitasking kernal.
Handles the passing of control
from and to applications as
they are called and terminated
The shell also provides a
graphic or text window as
required by the application
through a VDI open
workstation call.
5.5

<!-- source-page: 170 -->
## Page 170

The Concise Atari ST Reference Guide
The GEM AES libraries
Application library
The application library functions initialize memory and data structures,
terminate processes, communicate with other processes and record/replay user
actions.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
APPLJNIT
10
0
1
0
0
Initializeapplication and
int_out(0)=application_ID
generate data structures
-1 failure, >=0 o'k
prior to other AES
placed in global array
function calls.
MUST call before any other AESfunction call
APPL READ
APPL WRITE
APPL FIND
11
2
1
1
0
Read n bytes from message
int_in(0)=the'from'pipe ID
pipe-
int_in(2)=number of bytes to read (n)
int_out(0)=0_error, >0_o'k
addr_in(0)=buffer address of the data to be read
12
2
1
1
0
Write n bytes to message
int_in(0)=the'to' pipe ID
pipe.
int_in(2)=number of bytes to write (n)
int_out(0)=0_error, >0_o'k
addr_in(0)=buffer address of the data to be written
13
0
1
1
0
int_out(0)=application ID
=-1, not found
addr_in(0)=address of a null
terminated filename
Find the ID of another
application in the system.
The filename must be 8
characters long, blank fill.
Handles SCRENMGR, CONTROL and EMULATOR may exist
5.6

<!-- source-page: 171 -->
## Page 171

GEM AES
Application library cont.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
APPL_TPLAY
14
2
1
1
0
*
int_in(0)=number of actions
int_in(2)=speed(l-10000)
int_out(0)=one (always)
addr_in(0)=address of memory
holding recording
aFpL^rec6rdT5""i
T
I
o
*
(6 byte record
int_in(0)=number of actions
word-longword) int_out(0)=number recorded
addr_in(0)=address in memory
to store records
Comments
Replay a series of user
actions.
speed 50=half
100=full
200=twice
Record a series of actions
First word
Ilow longword high
0=timer
l=button
2=mouse
3=keyboard
elapsed time ms
O=up,l=down/#clicks
x pixels / y pixels
char/ keyboard_status
APPL EXIT
19
int
0
put(0)=
1
0
0_error
>0 o'k
0
Let application library
cleanup environmentwhen
the appliction has finshed
making calls
It is possible to terminate an application with an illegal call
* Note that functions APPL_TPLAY and APPL_TRECORD do not work on
early SToperating systems (pre 'NEW TOS')
5.7

<!-- source-page: 172 -->
## Page 172

The Concise Atari ST Reference Guide
Event library
The event library routines monitor multiple and individual user inputs
providing efficient polling of the clock, keyboard, mouse and messagepipes.
Integers
Addresses
Function
(
*Dp
in
out
in
out
£0
$2
$4
$6
$8
Comments
EVNT_KEY
>0
0
1
0
0
Return standard keyboard
: nt_out(0)=keycode press
code (Appendix D)
EVNT BUTTON 21
3
5
0
0
Return mouse status on
*
int_in(0)=wait a #clicks
button event
: nt_in(2)=buttmask
nt_in(4)=button state
Mask
buttmask
Keystate
bitO
button left
right_shift
nt_out(0)=number clicks >=1
bitl
2nd button
left_shift
nt_out(2)=x coor
\
on
bit 2
3rd button
Ctrl
mt_out(4)=y coor
/ event
bit 3
up to 16
Alt
int_out(6)=button state
Buttonstate bits 0=up,l=down
mt_out(8)=keystate
EVNT_MOUSE
22
5
5
0
0
Return mouse status on
int_in(0)=return flag
leaving specified area.
mt_in(2)=x coor \ area
Return flag =1, on area exit
mt_in(4)=y coor 1position
=0, on area entry
mt_in(6)=width
1pixel
mt_in(8)=height /coordinate
Mask
Buttmask
Keystate
bitO
button left
right_shift
mt_out(0)=Reserved (=1)
bitl
2nd button
left shift
mt_out(2)=x coor
\
on
bit 2
3rd button
Ctrl
mt_out(4)=y coor
/ event
bit 3
up to 16
Alt
mt_out(6)=button state
Button state bits 0=up,l=down
nt_out(8)=keystate
5.8

<!-- source-page: 173 -->
## Page 173

GEM AES
Event library cont.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
EVNT_MESAG
23
0
1
1
int_out(0)=Reserved (=
16
\ addr_in(0)=message type ID—•
byte
I addr_in(2)=ID of sender
buffer/ addr_in(4)=0 or length of
message over 16 bytes
addr_in(6-14)=extra words
0
Rag message, up to eight
=1)
words, in message pipe.
extra
words
Message
function
ID
TTj
GH
Selected menu
20
ABCDE
Redraw window
21
A
Move work area to top
22
A
Close window
23
A
Toggle full size window
24
AF
Scroll/page window
25
AJ
Move window horizontally
26
AJ
Move window vertically
27
ABCDE
Re-size window
28
ABCDE
Move window
29
A
Set new top window
40
I
Desk_accessory open mess
41
I
Desk_accessory close mess
50
ct_update
51
ct_move
52
ctjnewtop
Addr_in() extra word entries
A=windw_
B=x coor
C=y coor
D=width
E=height
F=Page
Row
. Column
hand! u=UDject index title
\
H=Object index item
Iactive I=menu item ID
Iarea
/
0_up
4_left
2
6
_up
left
(op#35 call return)
J=top/left 0-1000
l_down
\ Mouse
5_right
Iarrow
3_down
Iclick
7 right
/message
Messages entered FIFO, where message
length >16 byte use APPL_READ.
Reading kills a message.
EVNT TIMER
24
2
1
0
0
int_in(0)=low
\ longword
int_in(2)=high
/ time ms
int_out(0)=Reserved (=1)
Flag application that a
specified length of time
has past.
5.9

<!-- source-page: 174 -->
## Page 174

The Concise Atari ST Reference Guide
Event library cont.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
EVNTJvlULTI
25
16
7
1
0
*
int_in(0)=Standard keycode
int_in(2)=number of clicks
int_in(4)=buttmask
int_in(6)=button state
int_in(8)=flags
\Mouse
int_in($A)=x coor
I
1
int_in($C)=y coor
I area
int_in($E)=width
I event
int_in($10)=height
/
int_in($12)=flags
\Mouse
int_in($14)=x coor
I
2
int_in($16)=y coor
I area
int_in($18)=width
I event
int_in($lA)=height
/
int_in($lC)=low \ longword
int_in($lE)=high/ timems
int_out(0)=flag
int_out(2)=x coordinate
int_out(4)=y coordinate
int_out(6)=button state
int_out(8)=keystate
int_out($A)=keycode press
int_out($C)=number clicks >=1
addr_in(0)=16 byte buffer
(see
EVNT_DCLICK 26
2
1
0
0
int_in(0)=slow 0 to 4 fast
int_in(2)=0_get, l_set
int_out(0)=speed l_new 0_old
Comments
Application waiting on one or
more events.
Button state 0_up, l_down
Mask
buttmask
flags
bitO
button left
Keyboard
bitl
2nd button
Button
bit 2
3rd button
Mouse 1
bit 3
Mouse 2
bit 4
Message
bit 5
Time
Flags show the type of
event the application is
waiting for or occurred
Keystate
bit 0
right shift
bit 1
left shift
bit 2
Ctrl
bit 3
Alt
Retn standard keyboard code
# of button events/time
EVNT_MESAG op 23)
Get/set double click
speed
' The 'NEW TOS' processes requests for single clicks correctly
5.10

<!-- source-page: 175 -->
## Page 175

GEM AES
Event Library cont.
Most
applications
will
wait
for
a
combination
of
events
using
the
EVNT_MULTI call. When a required event occurs, the application will be moved
from the 'not ready' list to the 'ready' list by the dispatcher, respond to the event
and then return to the 'not ready' list to wait for the next event in the
EVNT_MULTI sequence.
Be careful in using the right hand Atari mouse button if writing portable
code, not all versions of GEM have two buttons.
Keystroke selection
Some menu items support keystoke selection through the EVNT_MULTIcall.
On
receipt
of
the
specified
key
selection,
the
application
should
call
MENUJTNORMAL to highlight the title to enable the user to see the selection
actually made; deselect highlighting when the application has finished with the
menu.
The 16-bit keyboard event codes are given in Appendix D; use
GRAF_MKSTATE to decode Control, Alternate and left and right Shift keys.
Icon selection
The bits for the required icon selection sequence are set by the application in
the EVNT_MULTI call, button up or down state and a predefined number of
clicks within a given space of time. On the event taking place, a bit value for the
mouse and keyboard state is returned; the application needs to also call
GRAFJMKSTATE to obtain the mouse's x and y coordinates and then make an
OBJC_FIND call passing the x and y coordinates and the address of the window,
desktop or application object tree containing it's icons.
If OBJC_FIND reports the mouse covering an icon, its state should be
changed to selected.
If the mouse does not cover an icon, the application should assume the user
will select a group of icons by drawing an expanding rectangle around them. Call
GRAF_MKSTATE to
ensure
the
button is still
depressed
and
then call
GRAF_RUBBERBOX to provide the extent of the box when the button is released.
The application should look for icons within the rectangle and change each icon
from normal to selected via OBJC_CHANGE calls.
5.11

<!-- source-page: 176 -->
## Page 176

The Concise Atari ST Reference Guide
Menu library
The menu library routines provide the user with a textural menu choice from
within an application, placing the mouse cursor over an enabled item and
clicking the mouse button to make the selection.
Integers
Addresses
Function
Op
in
out
in
out
Comments
$0
$2
$4
$6
$8
MENUJ3AR ""30 ~~i
l" ~~1
0™
"Display/erasemenubar"'
int_in(0)=menu bar 0_erase, l_draw
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address that forms this menu
MENUJCHECK~~3T~T
T
1
0
"b~G^y/exs^metxii^m
int_in(0)=menu item ID
check mark.
int_in(2)=0_clear, ldisplay (check mark)
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address that forms this menu
MENUJENABLE 32
2
110
Disable/enable menu item
int_in(0)=menu item ID
int_in(2)=0_disabled, l_enabled (light/dark text)
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address that forms this menu
MENU"tNORMAL33 2"
1
1
0
Displaymeriu title in
int_in(0)=menu item ID
reverse video.
int_in(2)=0_reverse, l_normal video
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address that forms this menu
MT3NU~TEXf "34 " 1
T~~ ~~2~ ~"o"
"Change"text olmenu item."
int_in(0)=menu item ID
reverse video.
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Address of new text string for this item
addr_in(4)=Object tree address that forms this menu
M^NtJMgIsTER 35~I
T
i
0
mce~desk^cces¥o^mem
int_in(0)=Desk accessory
item string on desk menu
process ID
and return ace's menu ID
int_out(0)=menu item ID (0-5)
addr_in(0)=address of desk accessory menu text string.
5.12

<!-- source-page: 177 -->
## Page 177

GEM AES
Menu library cont.
To display a menu bar, call the resource function RSRC_GADDR with the
menu bar's (object) details to obtain the long address of the object tree root, call
MENU_BAR with the address and set the routine to draw.
Menu bar control
The AES screen manager controls all user interaction with the menu bar in
the following manner:
The user touches an item in the menu bar using the mouse cursor
The screen manager receives a message that the cursor has entered the menu
bar and enters the 'ready list'. It determines which item in the title bar the cursor
touched, saves the screen under and displays the 'titles' menu; highlighting menu
items as the cursor passes over them.
The application is held in the 'not ready' list while the screen manager has
initiated open menus. When the user clicks the mouse on a menu item, the screen
manager sends details of the object tree of the menu selected to the primary
application's message buffer.
The dispatcher checks the 'not ready' list for the application process waiting
for the message and moves it to the 'ready' list.
The EVNT_MULTI callreturns a flag of the events that occurred, whichmay
be read by the application and any action deemed appropriate by the application
taken.
When the action is complete, the menu title is de-highlighted by the
application making a MENU_TNORMALcall.
5.13

<!-- source-page: 178 -->
## Page 178

The Concise Atari ST Reference Guide
Object library
An object, described by a collection of data in a linked list (object tree), can be
created, deleted, edited, drawn on the screen, and the object's position on the
screen found, using the object library routines.
Object tree
An object comprises of a parent and perhaps a number of different levels of
children, who always reside within the parents display space. The tree is created
by making seperate calls to the OBJC_ADDroutine for each child or loaded from
disk using RSRC_LOAD.
. child
Each child points to a
brother in a chain, if it
has one? The last one
points back to its parent
Different objects may
be created by only
using parts of the tree.
. Child
Level n+1
Text
L_ 1
5.14
Parent
Child d
Boxtext type object
Child c2 Box type object
Child c3 Box type object
d
Parent
c2
c3

<!-- source-page: 179 -->
## Page 179

GEM AES
The object library uses a number of additional tables, as well as the parameter
block, control table and global arrays, to describe objects. The tables are accessed
via the resource library routines and are as follows:
Additional object library word tables
(bracketed items are longwords)
offset
Object
Iconblk
Tedinfo
Bitblk
Applblk
Parmblk
(0)
Nextchild
\Text
\Mask
\Image
\Code
\Tree
(2)
Firstchild
/string
/string
/pointer
/pointer
/pointer
(4)
Lastchild
\Template \Data
W_<irray
\Loparm
Objindex
(6)
Otype
/string
/string
H_pixel
/Hiparm
Oldst
(8)
Oflag
Wchar
\Text
x_source
-
Newst
($A)
OState
/pointer
/string
y_source
-
x_coor
($C)
\OSpec
Font
Icon_c
fg colour
-
y_coor
($D)
/
Reserved
x_cpos
0
-
W_pixel
($10)
x_coor
Justify
y_cpos
-
-
H_pixel
($12)
y coor
Colour
x_ipos
-
-
x_cpos
($14)
Width
Reserved
y_ipos
-
-
y_cpos
($16)
Height
Borderthk i_wide
-
-
W cpxl
($18)
textlength i_height
tmplength x_tpos
H_cpxl
($1A)
Prefixes
Loparm
($1C)
(x&y
y_tpos
0=object
Hiparm
($1E)
relative to
t_wide
c=character
0
($20)
parent
t height
i=icon -
($22)
or screen)
0
t=text
-
The tables, filled by the object library routines, are used in performing
various functions:
Object: Provides data that describes each object,its tree relationship to other
objects and its location relativeto parent (screen if the root).The predefined
object values on next page.
Tedinfo> Allows object types Text(21), Boxtext (22), Ftext(29) and Fboxtext (30)
to be edited, using the object tablespecpointer to point to the Tedinfo table. The
'NEW TOS'allows the underscore to be used in the textstring.
Iconblk: Is used to hold icon (31)data definitions. Object type Icon points here
with its spec pointer.
Bitblk: Object type Image (23)uses this to draw bit images like cursors and icons.
Applblk: Is usedto locate and call an application defined routine that draws and
or changes an object. The object type Progdef (24)spec pointer points here.
Parmblk: Storage of data used by the application defined routine above
(applblk) and pointed to by the code pointer.
5.15

<!-- source-page: 180 -->
## Page 180

The Concise Atari ST Reference Guide
Object libraries
cont.
Routines which edit, create and draw data describing objects that appearon
the screen: boxes, characters, icons etc.
There are some predefined values for the table entries:
Graphic types
of objects
(Otype)
Ospec
points
to
Object flags
(Oflag)
Object colours
(color)
20=Box
-
Ox0000=none
0=white
21=Text
Tedinfo
0x0001 =selectable
l=black
22=Boxtext
Tedinfo
0x0002=default
2=red
23=Image
Bitblk
0x0004=exit
3=green
24=Progdef
Applblk
0x0008=editable
4=blue
25=Invisbox
0x0010=rbutton
5=cyan
26=Button
Nstrg
0x0020=lastobj
6=yellow
27=Boxchar
0x0040=touchexit
7=magenta
28=String
Nstrg
0x0080=hidetree
8=white
29=Ftext
Tedinfo
0x0100=indirect
9=black
30=Fboxtext
Tedinfo
10=lred
31=Icon
Iconblk
ll=lgreen
32=Title
Nstrg
12=lblue
13=lcyan
14=lyellow
Font types
Colour fields
15=lmagenta
3=system font
5=small font
15
1211
8
4
3
border
colour
Object states
(Ostate)
0x0000=
0x0001=
0x0002=
0x0004=
0x0008=
0x0010=
0x0020=
5.16
normal
selected
crossed
checked
disabled
outlined
shadowed
text
colour
0_trans
1_replaos type
colour
Ospec 32-bit word/byte values
Loword
Highword
Lobyte
hibyte
Box
Invisbox
Boxchar
colour
colour
colour
0
borderthk
0
0
0
character

<!-- source-page: 181 -->
## Page 181

GEM AES
Editable text
field definitions
justification
0=edstart
l=edinit
2=edchar
3=edend
(Justfy)
0=left justified
l=right justified
2=centered
Borderthk
0
1 to 128
-1 to -127
9
only digits 0 to 9
A
only uppercase A to Z and space
a
upper and lowercase A to Z and space
N
0 to 9, uppercase A to Z and space
n
0 to 9, upper and lowercase and space
F
all valid DOS filename characters, plus ? * :
P
all valid DOS pathname characters, plus \ :
p
all valid DOSpathname characters, plus \ :
X
anything
none
inside
outside
(in pixels)
Allowable valid
characters
(Vchar pointer)
5.17

<!-- source-page: 182 -->
## Page 182

The Concise Atari ST Reference Guide
Object library
cont.
Function
Integers
Addresses
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
OBJC_ADD
40
2
1
1
0
int in(0)=Parent ID
int_in(2)=Child ID (item to add)
Add an object to an object
tree.
OBJC_DELETE
41
1
1
1
0
Delete an object from an
int_in(0)=Object to delete
object tree.
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address with object in it
OBJC_DRAW
OBJC_FIND
42
6
1
1
0
Draw an object in an
int_in(0)=start object
object tree.
int_in(2)=draw 0_object only, nth_level
int_in(4)=x coordinate \
int_in(6)=y coordinate I Clip
int_in(8)=width
I rectangle
int_in($A)=height
/
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address with object in it
43
4
1
1
0
int_in(0)=search start object
int_in(2)=levels of search
int_in(4)=x coordinate \ mouse
int_in(6)=y coordinate / location
int_out(0)=-l_no object, 0 to n # of object in tree
addr_in(0)=Object tree address of search start object
Find an object under the
mouse form.
OBJC_OFFSET
44
1
3
1
0
int_in(0)=object to locate
int_out(0)=error 0_yes, +ve_no
int_out(2)=x coordinate
\ relative
int_out(4)=y coordinate
/ to screen
addr_in(0)=Object tree address with int_in(0) in it
Find objects screen relative
x and y coordinates
5.18

<!-- source-page: 183 -->
## Page 183

Object library
cont.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
GEM AES
OBJC_ORDER
45
2
1
1
0
Reorder an object within a list
int_in(0)=Object to be moved
int_in(2)=new position (0_bottom level, l_next etc. to -1 top)
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address with int_in(0) in it
6BJC"_~EDi¥
46
4
2
1
0
¥dit"objecTText7""
int_in(0)=text object to be edited
int_in(2)=user input character
int_in(4)=next character index in text string
int_in(6)=0_reserved
=l_format string using text and template strings
=2_validate against Tedinfo valid_char,
update and display.
=3_turn off text cursor
int_out(0)=error 0_yes, +ve_no
int_out(2)=next character index after operation
addr_in(0)=Object tree address of object with text in it
Changes an objects state
value.
OBJC_CHANGE 47
8
1
1
0
int_in(0)=objectto be changed
int_in(2)=zero, reserved
int_in(4)=x coordinate \
int_in(6)=y coordinate I Clip
int_in(8)=width
I rectangle
int_in($A)=height
/
int_in($C)=object state new value
int_in($E)=redraw 0_no, l_yes
int_out(0)=error 0_yes, +ve_no
addr_in(0)=Object tree address
To display an icon, calculate the desktop windows work area using a
WIND_GET call and use OBJC_DRAW to draw the icon in the work area. The
icons position within the window is held by the 'Iconblk' structure.
5.19

<!-- source-page: 184 -->
## Page 184

The Concise Atari ST Reference Guide
Form library
A set of routines that enable the user to replyto a list of questions, either by
checking off boxes or entering text.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
FORM DO
50
1
1
1
0
Monitor users interaction
int_in(0)=object number
with a form.
int_out(0)=object number that caused the exit
addr_in(0)=object tree address
FORM DIAL
51
9
1
int_in(0)=flag
int_in(2)=x coordinate \
int_in(4)=y coordinate I small
int_in(6)=width
i box
int_in(8)=height
/
int_in($A)=x coordinate \
int_in($C)=y coordinate I large
int_in($E)=width
I box
int_in($10)=height
/
int_out(0)=error 0_yes, l_no
0
0
Reserve or free dialog box
screen area.
Hag:
0=reserve screen space
for dialog box
l=draw expanding box
2=draw shrinking box
3=free screen space
FORM_ALERT
52
1
1
1
0
Display an alert.
int_in(0)=exit button
0=no default exit
int_out(0)=chosen exit
l=first exit button
addr_in(0)=address of alert string
2=2nd exit button etc.
FOmlE"RROR""53
1
r~~0"
0
Dispia^anCTror box
int_in(0)=DOS error code
int_out(0)=exit button code (as above)
FORM_CENTER 54
0
5
1
0
int_out(0)=one, reserved
int_out(2)=x coordinate
int_out(4)=y coordinate
int_out(6)=width
int_out(8)=height
Centre a dialog box on the
screen
\Of
I centered
I object
/
tree
addr_in(0)=dialog object tree address
5.20

<!-- source-page: 185 -->
## Page 185

GEM AES
The forms library routines enable the user to respond to a typical printed
style of form on the screenin a question and answer mode without tying up the
applications
resources.
The
forms
library
also
provides
a
consistent
application/user response format. The forms have three optional types of user
response, they are:
Check a single box,
Check a combination of boxes,
Provide a typed response;
These may be used any number of times in any combination. Finally the user
exits typically via an "o'k" or "cancel"button.
Taking a dialog as an example:
To display a dialog, which will appear in the centre of the screen, call
resource function RSRC_GADDR to get the address of the dialogs object tree. Call
FORM_DIAL to reserve screen space and then call OBJC_DRAW to draw the
dialog.
The application should call FORM_DO to monitor user interaction with the
dialog box. Where user changes have been made, the application may use
OBJC_CHANGE to reset initial values, in particular dehighlight selected buttons.
It may also be necessary to save some changes made to dialogs.
To exit from the dialog, call FORM_DIAL to release the screen space, the
application which should be in an EVNT_MULTI wait state can redraw the
screen using an OBJC_DRAW call.
A nicer display may be achieved if FORMDIAL is used to draw expanding
and shrinking boxes on start up and finish of the dialog sequence.
Edit keys
Keys have certain specified meanings for editting the text fields of forms and
dialog boxes:
Left and right arrow: Move left or right within the field.
Down arrow and tab: Move to first free space of the next field.
Up arrow: Move to first free space of previous field.
Delete: Delete character following cursor without moving cursor.
Backspace: Delete character to the left of the cursor, move cursor and
following text one space left.
Return: End edit and terminate if either "o'k" or "cancel" type buttons are
default objects, otherwise ignore.
Escape: Clear all characters from the field.
5.21

<!-- source-page: 186 -->
## Page 186

The Concise Atari ST Reference Guide
Form library cont.
Alerts
Alerts, which are used by GEM AES to handle error conditions, contain one
of three pictorial designs; note icon, wait icon and the stop icon, and up to a
maximum of 5 lines of 30 character width text (each line being seperated by the
"I"
bar symbol) and up to 3 exit buttons, each containing up to 20 characters of
text.
A special case alert is the error box which reports errors in TOS terminology
(appendix I).
A typical set of object structures for an alert box with some textural
information and "o'k" and "cancel" buttons might be:
More than 30 characters/line could crash early TOS systems. 'NEW TOS'
truncates the line and remains solid.
Object
Comments
structure
"help"
"o'k"
"cancel"
element
Box
Text
Boxtext
Boxtext
Pntr to next obj.
0
nextchild
-1
2
3
0
<
- -
-1 root
2
firstchild
1
-1
-1
-1
\ -1 lowest
4
lastchild
3
-1
-1
-1
/
level
6
Otype
Oflag
20
21
22
22
8
0
0
5
27
Seepage 5.16
for details
$A
Ostate
0
0
0
0
$C
Ospec
00020007L 0L
0L
0L
$10
x-coor
90 Relative 86
374
374
$12
y coor
150
to
16
18
50
$14
width
454.screen 272
64
54
$16
height
98
64
16
16
[ Relative to parent (Box)]
The o'k button takes Oflag attributes selectable and exit.
The cancel button takes Oflag attributes selectable, default, exit and lastobj.
5.22

<!-- source-page: 187 -->
## Page 187

GEM AES
Tedinfo
"help"
"o'k"
"cancel"
Offset
structure
element
Box
Text
Boxtext
Boxtext
0
Text string
help
o'k
cancel
4
Tmplate string
-
0
0
0
8
Vchar pointer
0
0
0
$C
Font
3
3
3
$D
Reserved
0
0
0
$10
Justify
0 left
2_center
2 center
$12
Colour
00020000L 00020000L 00020000L
$14
Reserved
0
0
0
$16
Borderthk
0
-2
-2
$18
textlength
0
0
0
$1A
tmplength
0
0
0
Theform libraryfollows the treefrom root to childrenin displaying the form
objects.
5.23

<!-- source-page: 188 -->
## Page 188

The Concise Atari ST Reference Guide
Graphics library
The graphics library routines enable the programmer to manipulate the
rectangular outline of a box.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
GRAF_RUBBERBOX 70 4
int_in(0)=
int_in(2)=
int_in(4)=
int in(6)=
3
0
0
x coordinate \ of
•y coordinate / box
minimum pixel width
minimum pixel height
Draw a box that expands
and contracts from a fixed
point as the mouse moves.
GRAF
int_out(0)=error 0_yes, +ve_no
int_out(2)=width
\ when button
int_out(4)=height
/ last released
DRAGBOX 71
8
3
0
0
int_in(0)=width
\ Of
int_in(2)=height
I box
int_in(4)=x coordinate I being
int_in(6)=y coordinate / dragged
int_in(8)=x coordinate \
Move a box and keep the
mouse pointer at the same
position inside the box.
Height and width
in pixels
int_in($A)=y coordinate I
int_in($C)=width
I
int_in($E)=height
/
int_out(0)=error 0_yes, +ve_
int_out(2)=x coordinate
int_out(4)=y coordinate
Boundary
rectangle
no
\ When button
/
released
GRAF_MOVEBOX 72
6
1
0
0
int_in(0)=width
int_in(2)=height
int_in(4)=x coordinate \
Initial
int_in(6)=y coordinate /
position
int_in(8)=x coordinate \
Final
int_in($A)=y coordinate /
position
int_out(0)=error 0_yes, +ve_no
5.24
Draw a moving box
Height and width
in pixels

<!-- source-page: 189 -->
## Page 189

GEM AES
Graphics library cont.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
GRAF_GROWBOX 73 8
1
0
0
int_in(0)=x coordinate \
int_in(2)=y coordinate I
Initial
int_in(4)=width
I position
int_in(6)=height
/
int_in(8)=x coordinate \
int_in($A)=y coordinate I
Final
int_in($C)=width
I position
int_in($E)=height
/
int_out(0)=error 0_yes, +ve_no
Draw an expanding box
outline
GRAF_SHRINKBOX 74 8
1
0
0
int_in(0)=x coordinate \
int_in(2)=y coordinate I
int_in(4)=width
I
int_in(6)=height
/
int_in(8)=x coordinate \
int_in($A)=y coordinate I
int_in($C)=width
I
int_in($E)=height
/
int_out(0)=error 0_yes, +ve_
Height and width
in pixels
Draw a shrinking box
outline
Final
position
Initial
position
no
Height and width
in pixels
GRAF_WATCHBOX 75 4
1
1
0
int_in(0)=reserved
int_in(2)=object tree index
int_in(4)=in the box
\ object
int_in(6)=out of box
/ state
int_out(0)=0_outside, linside the box
addr_in(0)=addressobject tree containing box
Track the mouse pointer
and button inside and
outside the box.
GRAF_SLIDEBOX 76
3
1
1
0
int_in(0)=parent index
int_in(2)=object index (slider)
int_in(4)=motion 0_horizontal, l_vertical
int_out(0)=0_left/top to 1000_right/bottom
addr_in(0)=Address of objecttree containing slider & parent
Keep sliding box inside
parent box.
5.25

<!-- source-page: 190 -->
## Page 190

The Concise Atari ST Reference Guide
Graphics library
cont.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
GRAF_HANDLE 77
0
5
0
0
Return GEM VDI handle for
int_out(0)=VDI handle
open screen workstation.
int_out(2)=width
\ character cell
int_out(4)=height
/ system font
int_out(6)=width
\ box for
int_out(8)=height
/ system font
GRAF MOUSE
78
int
1
.in(0) 110
Permit application to
=0_arrow
change predefined mouse.
=l_text cursor (vertical bar)
=2_bee (hourglass-IBM GEM)
=3_hand with pointing finger
=4_flat hand, extended fingers
=5_thin cross hair
=6_thick cross hair
=7__outline cross hair
=255_mouse form stored in addr_in(0)
=256_hide mouse form
=257_show mouse form
int_out(0)=error 0_yes, +ve_no
(VDI op 111)
addr_in(0)=35 word buffer for mouse form definition block
0
0
GRAF MKSTATE 79
0
int_out(0)=l, reserved
int_out(2)=x coor
\mouse
int_out(4)=y coor
/location
int_out(6)=Butonstate \ 0_up
int_out(8)=keystate
/l_down
Return current mouse location
button and keyboard state.
Mask
Buttonstate
keystate
bitl
butt left
right_shift
bit 2
2nd button
left_shift
bit 3
3rd button
Ctrl
bit 4
Alt
GEM AES provides the graphic routines to manipulate the rectangular
outline of a box which are based on GEM VDI routines. Graphics applications
should use GEM VDI directly for graphic output to avoid any loss in
performance through the AES overhead.
5.26

<!-- source-page: 191 -->
## Page 191

GEM AES
Scrap library
The scrap library consists of routines that manage the interchange of
information between applications. Data is either deleted or copied from the
source to the clipboard (disk file named scrap), which only holds one document;
and then pasted (copied) fromthe clipboard(disk) to the target application.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
SCRP_READ
80
0
1
1
0
int_out(0)=error 0_yes
+ve_no
addr_in(0)=buffer address into which
scrap directory is copied.
SCRP_WRITE
81
0
1
1
0
int_out(0)=error 0_yes
+ve_no
addr_in(0)=buffer address from which
scrap directory is copied to clipboard.
Comments
Read the current scrap
directory on the clipboard
Writenew scrap directory
to clipboard. (Cut & Copy)
The scrap data is held on disk in a file named scrap,the extension identifies
the type of data:
.txt
ASCII text string
.dif
Spreadsheet data
.gem
Metafile- GEM VDI type graphic images
img
Bit image - GEM VDI standard form
Applications access the data viaGEM BDOS file system calls to:
Search
Create a file
Open a file
Read a file
Write a file
Close a file
Delete a file and
Get file size.
5.27

<!-- source-page: 192 -->
## Page 192

The Concise Atari ST Reference Guide
File selector library
The file selector library routine enables the programmer to select file from a
displayed directory or to type in a filename and path.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
FSELJNPUT
90
0
2
2
0
int_out(0)=error 0_yes
+ve_no
int_out(2)=exit button 0_cancel
l_o'k
addr_in(0)=buffer address of initial directory specification
(If not updated holds last dir spec user selected)
addr_in(4)=buffer address of initial selection displayed
in file selector dialog box.
(If not updated holds last selection)
Comments
Display file selector
box and monitor user
interaction with it.
This routine displays a file directory dialog box, the user either selects a
filename directly from the directory list using a mouse or types in a filename to
create a new file.
The file directory dialog box displays the name of the current directory path,
a selection field, a scrollable directory listing and two buttons to terminate the
routine. The user interacts with the dialog box in the standard manner, changing
the directory being displayed, selecting an item from the directory list or typing
in a user selection and then exiting via the "o'k" or "cancel" button.
The file selector library returns the filename selected or entered, in the buffer
at addr_in(4), the directory path of the file in the buffer at addr_in(0) and whether
the selection is o'k or to be cancelled. The application acts upon the information
as required.
Entering the underscore into the directory string may cause older versions of
the TOS to crash the ST.
5.28

<!-- source-page: 193 -->
## Page 193

GEM AES
Window Library
The window library routines permit the creation, opening, closing and
deletion of windows to a maximum of eight active windows. The window
parameters can be recovered or set, the window under the mouse cursor found, a
flag set to indicate that a window is being updated and the size of a window
determined.
Function
Integers
Addresses
Op
in
out
in
out
$0
$2
$4
$6
$8
WIND_CREATE 100
5
10
0
int_in(0)=window parts
int_in(2)=x coordinate \ Of
int_in(4)=y coordinate I full
int_in(6)=width sizeallocated.
int_in(8)=height/window
int_out(0)=window handle (-ve, no windows available)
Comments
Allocate window size
including border & return
window handle. Window open
must set size < = to that
WIND_OPEN
101
5
1
0
0
Open a window at it's
int_in(0)=window handle
initial size and location,
int_in(2)=x coor \
- not necessarily it's
int in(4)=ycoor 1Window
full size.
int in(6)=width
1 initial
int_in(8)=height /
size
int_out(0)=error 0_yes,+ve_no
WIND_CLOSE
102
1
1
0
0
Close window, does not
int_in(0)=window handle
deallocate the window or
int_out(0)=error 0_yes, +ve_no
handle.
WIND_DELETE 103
1
1
0
0
Free space occupied by
int in(0)=window handle
window and handle.
int_out(0)=error 0_yes, +ve_no
5.29

<!-- source-page: 194 -->
## Page 194

The Concise Atari ST Reference Guide
Window parts (bit representation)
bit 0
Name (name and title bar)
bit 1
Close (close box)
bit 2
Full (full box)
bit 3
Move (move box)
bit 4
Info (information line)
bit 5
Size (size box)
bit 6
Uparrow (up arrow)
bit 7
Dnarrow (down arrow)
bit 8
Vslide (vertical slider)
bit 9
Lfarrow (left arrow)
bit 10
Rtarrow (right arrow)
bit 11
Hslide (horizontal slider)
Window library cont.
Function
wTnd"get~"
Integers
Addresses
Op
in
out
in
out
$0
$2
$4
$6
$8
104
2
5
0
0
int_in(0)=window handle
int_in(2)=getjield
int_out(0)=error 0_yes, +ve_no
int_out(2)=
\ Data
int_out(4)=
I specified
int_out(6)=
I by Get
int_out(8)=
/ field
WIND_SET
105
6
1
0
0
int_in(0)=window handle
int_in(2)=set_field
int_in(4)=
\ Data
int_in(6)=
I specified
int_in(8)=
I by Set
int_in($A)=
/ field
int_out(0)=error 0_yes, +ve_no
5.30
Comments
Get window data specified
field
Set displayed window
parameters

<!-- source-page: 195 -->
## Page 195

Get
field (2)
4
5
6
7
8
9
10
11
12
13
15
16
17
xcoor
xcoor
x coor
xcoor
1-1000
1-1000
handle
xcoor
xcoor
reserved
1-1000
1-1000
Set
field (4)
int_out()
(4)
(6)
(8)
GEM AES
Associated function
ycoor
width
height
Window work area
y coor
width
height
current
\ size including
y coor
width
height
previous
/ border title
y coor
_ width
height
maximum poss window size
relative horiz slider position
relative vertical slider position
top window handle
ycoor
width
height
first rectangle in window list
ycoor
width
height
next rectangle in window list
relative horizontal slider size
relative vertical slider size
screen
Heft, 1000right
1 top, 1000 bottom
(-1 default minimum sq box)
(-1 default minimum sq box)
(6)
int_in()
(8)
($A)
Associated function
1
2
3
5
8
9
10
14
15
16
17
Parts
Name pointer
Info pointer
see pg 5.30
y coor
width
1 left, 1000right
1 top, 1000 bottom
height
window components
address of name strng
address info line string
current window size
relative horiz slider position
relative vertical slider pos
top window handle
GEM desktop to draw
relative horiz slider size
relative vert slider size
screen
xcoor
1-1000
1-1000
handle
lo-word
1-1000
1-1000
hi-word
strtobj
(-1 default minimum sq box)
(-1 default minimum sq box)
5.31

<!-- source-page: 196 -->
## Page 196

The Concise Atari ST Reference Guide
Window library cont.
Function
Integers
Addresses
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
WIND_FIND
106
2
1
0
0
int_in(0)=x coordinate \ mouse
int_in(2)=y coordinate / position
int_out(0)=window handle
Find window under mouse
WINDJJPDATE 107 110
0
Flag about to update window
int_in(0)=update 0_end, l_begin (window locking)
2_end, 3_begin (usual mouse control)
int_out(0)=error 0_yes, +ve_no
Do notalter sizewhile update proceeding
WIND"CALC " 108~~6
5~~ ~0~ "o"
" RTt"wriidow¥OTdr7work area
int_in(0)=area 0_work->-border, l_border->-work
int_in(2)=parts
(see pg5.30 -same aswindow create)
int_in(4)=x coordinate \
int_in(6)=y coordinate Iborder/work
int_in(8)=width
Iarea values
int_in($A)=height
/
int_out(0)=error 0_yes, +ve_no
int_out(2)=x coor
\
int_out(4)=y coor
Iwork/border
int_out(6)=width
I area values
int_out(8)=height
/
To calculate work
area,inputborder
area values.
To calculate border
areainputwork
area values.
Note that AES windows do not use the same coordinates as VDI
AES x, y, width, height
VDI xl,yl,x2,y2
5.32

<!-- source-page: 197 -->
## Page 197

GEM AES
The desktop window is always present in the AES environment and supports
a maximum of eight windows at a time. The AES screen manager handles all the
user interaction outside the border area and the sizing, dragging and scrolling
actions requested from within the border. The contents of the border area
determine which of these functions are available.
Each user action sends a message through the message pipe to the
applications 'EVNT_MESAG' buffer where it is stacked on a first in-first out
basis. In order to perform the requested function, the message must first be read
and then the window management action may be either programmed to be
performed or ignored. The assembler GEM program (Appendix L) demonstrates
the effect of creating a window with the facilities, but not incorporating any code
to handle the screen managers requests. The example also shows the parts
handled by the screen manager, moving sliders, rubber boxing windows etc.
The application handles all activities within the window work area.
To create a window, the application calls WIND_CREATE defining the type
(only those facilities that the application supports) and position of the window
required, returning the window handle to be used in all subsequent actions on
the window. An application call to WIND_CALC may be used to return the size
of the window work area. A call to WINDOPEN will get AES to draw the
window's border area on the screen and send a message to the application to
draw the windows work area.
WIND_SET calls are used to set the size and location of the vertical and
horizontal sliders. If the window is resized, the application must decide if the
preview rubber box size is valid. If not, the application may resize to the nearest
valid size or display a warning dialog message. If valid, the application must
issue a WIND_SET call to change the window size. A reduced window size does
not require the work area to be redrawn, but if larger, GEM AES will send a
message to the application to redraw the windows work area (EVNT_MESAG
ID=20).
The application is responsible for redrawing and updating the visible parts of
its windows, which it divides into the smallest number of non-overlapping
rectangles, found by a series of WIND_GET calls. Initially to the 'first' rectangle
in the window list and subsequently to the 'next' rectangle until the returned
width and height are both zero. Note that if the window is not covered, say by
the control panel, that there will be only one rectangle.
5.33

<!-- source-page: 198 -->
## Page 198

The Concise Atari ST Reference Guide
Before updating the window, the application makes a WINDJJPDATE call
to freeze all other rectangle lists and to prevent menus and alerts from being
displayed
during
the update.
On completion of the update,
another
WINDJJPDATE call permits further change tothedisplay and rectangle lists.
To redraw the window work area, each rectangle in the rectangle list is
compared with the update rectangle in turn, and any common portionredrawn.
To make
a window active, the application (which must
include an
EVNTJMULTI call that includes a mouse button event) will receive a 'button
pressed' messagefrom the screen manager - the event occurred outside the active
window and is therefore detected by the screen manager. The application calls
WIND_FIND using the mouse x and y coordinates to obtain the handle of the
window under the mouse. If it is the desktop, handle 0,a rubber box is drawn in
expectation of the user selecting desktop icons. If the handle is that of an inactive
window, the screen manager sendsa message (EVNT_MESAG ID=29) to request
thewindow bebrought tothetop. The application calls WIND_SET tocomply.
To close a window via the windows border or menu command, the screen
manager sends a message to the application which should make a WIND_CLOSE
call; a WIND_DELETE call will then free the handle.
5.34

<!-- source-page: 199 -->
## Page 199

GEM AES
Resource library
The resource library provides the interface between the application and its
file resources, trees, objects, icons and pictures etc. providing the means to port
an application to a different environment by simply changing the resource file
data.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
, $4
$6
$8
Comments
RSRC LOAD
110
0
1
1
0
Allocate memory and load a
resource file into memory.
int_out(0)=error 0_yes, +ve_no
addr_in(0)=ASCII filename string address
RSRC_FREE
111
0
1
0
0
int_out(0)=error 0_yes, +ve_no
RSRC_GADDR
112
2
1
0
1
int_in(0)=type
int_in(2)=structure index
int_out(0)=error 0_yes, +ve_no
addr_out(0)=address of specified structure
Onlyfunctions withobject types R_TREE andR_FRSTR
Free the memory space
allocated by rsrc_load.
Get address of data
structure (object)
loaded in memory.
RSRC SADDR
113
2
1
1
0
Store the address of a
int_in(0)=type
data structure in memory.
int_in(2)=structure location index
int_out(0)=error 0_yes, +ve_no
addr_in(0)=address of the data structure
RSRCJDBFIX
114
1
1
1
0
int_in(0)=object index
int_out(0)=l, reserved to pixels.
addr_in(0)=object tree address
Convert objects location
and size from character
coordinates
5.35

<!-- source-page: 200 -->
## Page 200

The Concise Atari ST Reference Guide
Type (of data structure)
0
tree
8
text string
(tedinfo)
1
object
9
template string
(tedinfo)
2
tedinfo
10
valid chars
(tedinfo)
3
icon blk
11
mask string
(iconblk)
4
bitblk
12
data string
(iconblk)
5
string
13
text string
(iconblk)
6
imagedata
14
image pointer
(bitblk)
7
obspec
15
pointer address of free string
16
pointer address of free image
To isolate an application from device, user and country specific data and
provide program portability; GEM AES supports resource files that contain the
variable parts of the application code.
To use a resource file, the application makes a RSRC_LOAD call to find the
total file size in bytes, allocate the memory space for the resource file and update
the file for screen resolution. The pointers to the object and the tree structures are
also updated and the address of the tree array stored in the applications 'Global
array'.
Access to the object library table pointers may be through RSRC_GADDR
and RSRC_SADDR calls. The tree index may be accessed via FORM_DO and
MENU_BAR calls among others.
RSRC_FREE deallocates the resource file memory and zeroes the tree array
address in the Global array.
Resource files are generated using the Atari ST icon edit and resource utility
program.
5.36

<!-- source-page: 201 -->
## Page 201

GEM AES
Shell library
The shell library routines enable one application to call another and keep
track of command and command tails.
Integers
Addresses
Function
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
SHEL READ
SHEL WRITE
120
0
1
2
0
Let application identify
int_out(0)=error 0_yes,
command that called it in
+ve_no
format of GEM BDOS func 75
addr_in(0)=buffer address of command string
addr_in(4)=buffer address of command tail
"521™3
T" ~~2~ ~0"~
"inform GEM ~wfu~ch7~iFany~
int_in(0)=0_exit, ljrun
application to run or exit
int_in(2)=graphic 0_no, l_yes
GEM AES.
int_in(4)=GEM application 0_no, l_yes
int_out(0)=error 0_yes, +ve_no
addr_in(0)=new executable command file address
addr_in(4)=command tail address of next program
SHEL_GET
122
1
1
1
0
int_in(0)=length
int_out(0)=error code
addr_in(0)=buffer address
SHELJPUT
123
1
1
1
0
int_in(0)=length
int_out(0)=error code
addr_in(0)=buffer address
SHEL_FIND
124
0
1
1
0
int_out(0)=error 0_yes,
+ve_no
addr_in(0)=address 80 character buffer minimum
i/p search filename
o/p full DOS filename
Read data from the
GEMDOS environmental
string buffer
Write data to the
GEMDOS environmental
string buffer
Search for filename and
return full DOS specification
SHEL ENVRN
125
0
1
2
0
int_out(0)=l, reserved
Search for environment
parameter and store
address of following byte
addr_in(0)=pointer to byte storage address
addr_in(4)=search parameter string
5.37

<!-- source-page: 202 -->
## Page 202

The Concise Atari ST Reference Guide
The shell library routines use a single buffer containing the command and
command tail that invoked the current application.A typical sequenceto calland
run another application might be:
Call SHEL_WRITE with a command, command tail and the home directory
addresses; also define graphic/character or GEM/Not GEM application. On
completion of the current application, the shell library will start the requested
application.
Exit from GEM AES by making a SHEL_WRITE call with the int_in(0)
parameter set to zero.
5.38

<!-- source-page: 203 -->
## Page 203

The IKBD commands
Chapter 6
Intelligent keyboard commands
General
6.2
Keycodes
6.2
Data packets
6.2
Commands
6.3
Reset
6.3
Set mouse button action
6.3
Set mouse relative position reporting
6.3
Set mouse absolute positioning
6.3
Set mouse keycode mode
6.3
Set mouse threshold
6.3
Set mouse scale
6.3
Interrogate mouse position
6.3
Load mouse position
6.4
Sey y base position
6.4
Set y base position at top
6.4
Resume
6.4
Disable mouse
6.4
Pauseoutput
6.4
Set joystick event reporting
6.4
Set joystickinterrogation mode
6.4
Joystick interrogation
6.4
Set joystickmonitoring
6.4
Set fire button
6.4
Set joystick keycode mode
6.5
Disable joysticks
6.5
Set time of day clock
6.5
Interrogate time of day clock
6.5
Memory load
6.5
Memory read
6.6
Controller execute
6.6
Status inquiries
6.6
Data packet functions
6.7
6.1

<!-- source-page: 204 -->
## Page 204

The Concise Atari ST Reference Guide
Intelligent keyboard commands
General
The Atari ST keyboard unit contains a 1MHz HD 6301 8-bit microprocessor
with some on-board memory storage to maintain the time of day clock etc. The
keyboard and its peripheral items, joystick and
mouse may be initialized,
monitored for position or status and the time of day clock read or set.
The intelligent keyboard (ikbd) communicates with the main processor over
a 7.8Kbit/s bidirectional serial link, sending individual keycodes or receiving
instructions and returning status codes in packets of data through a pair of
addresses, one for transmit and one for receive.
Characters can be read from the keyboard input queue in main system RAM,
it is filled by an interrupt routine that transfers data from the ikbd to memory
automatically. Characters are written to the keyboard by placing the character
code in the keyboard data register after bit 1 of the keyboard command/status
register is set.
Keycodes
The keyboard transmits make and break keycodes for each key press and
release. Appendix D provides the codes for the individual keys, bit 7 being set for
break and cleared for make.
Data packets
To differentiate the keyboard codes from the data packets transmitted to and
from the ikbd to the main processor; the codes #$F6 to #$FF precede status
information packets. The packets provide reports of mouse position and status,
time of day and joystick status. The packets may be stored and used later, with
the header byte removed, to restore the condition of the ikbd.
6.2

<!-- source-page: 205 -->
## Page 205

The IKBD commands
Ikbd commands
Input
op code
string
Output
databyte
string
Function
#$80
#$01
Reset.
Return keyboard to power-up status without
affecting clock. A break 200ms also causes a reset
#$07
Set mouse button action.
OOOOOaaa
default %00000000
bit 0 l_press
\ Mousepositionreport on
bit 1 l_release
/ (only relevant in absolute mode)
bit 2 0_button, l_key type operation.
#$08
Set mouse relative position reporting (default).
Position
packet generated asynchronously
when threshold exceeded
#$09
Set mouse absolute positioning.
Xmsb
\ X maximum
Resets ikbd x and y coordinates.
Xlsb
/
The x and y values in
Y msb
\ Y maximum
scaled mouse 'clicks' do
Ylsb
/
not wrap, ignore <0 & >max
#$0A
Set mouse keycode mode.
Return mouse motion in cursor
X step
keycodes instead of relative or
Y step
absolute motion records.
#$0B
Set mouse threshold.
Before move event is generated
X level
Default value 1
Y level
(Relative motion only)
#$0C
Set mouse scale.
Set X and Y scale factors for
X
absolute mousepositioning -
Y
'clicks' per coordinate change.
#$0D
#$F7
Interrogate mouse position
OOOOxxxx
bit 0 right button down since last interrogation
bit 1 right button up
\
bit 2
left button down I since last
bit 3 left button up
/ report
X msb
\ X coor
X lsb
/
Only valid in absolute
Y msb
\ Y coor
mode, regardless of mouse
Y lsb
/
button action setting.
6.3

<!-- source-page: 206 -->
## Page 206

The Concise Atari ST Reference Guide
Ikbd commands cont.
Input
Output
op code
databyte
Function
string
string
#$0E
Load mouse position.
#$00
filler (null)
Enables the user
Xmsb\
X coor
\ in scaled
to preset the
Xlsb
/
1 coordinate
internal absolute
Ymsb\
Y coor
/ system
mouse position
Ylsb
/
#$0F
#$10
#$iT
#$12"
#$13"
#$14
#$15'
#$16
#$17
rate
OOOOOOab
aaaabbbb
Set Y = 0 at bottom
SetY =0attop'WefauTtf
Set for relative and
absolute mouse motions.
I
Resume sending data back.
Resume.
Disable mouse.
Stop mouse event reports. Resume
on any mouse mode command.
Pause output.
Stop sending further reports,
queue them in a (short) buffer.
Set joystick event reporting (default)
Set joystick interrogation mode. Disable joystick event
reporting, use interrogate to
sense joystick state.
Joystick interrogation.
Set joystick monitoring.
[packets of two bytes]
bit 0 Joystick 1
\ Fire
bit 1 Joystick 0
/ button
bits 0-3
bits 4-7
Return a record of current
joystick state.
(sample rate of .01s)
Set ikbd to monitor
serial command line
and joystick, update
Joystick 1
\ Position time of day clock
Joystick 0
/ only
#$18
cccccccc
Set fire button monitoring
Set ikbd to monitor serial
packed8-
command lineand firebutton of
bits/byte
joystick 1, update time of day clock.
6.4

<!-- source-page: 207 -->
## Page 207

The IKBD commands
Ikbd commands cont.
Input
Output
op code
databyte
Function
string
string
#$19
Set joystick keycode mode
(Joystick 0)
Rx
(provides a velocity autorepeat facility)
Ry
initial rate final rate
Tx
Tn
Tn
Tn
Vn
Vn
If Rn zero
Ty
I-— |
|
|-— |
|
|-
onlyVn
Vx
I <
Rn
>
I
times in .Is
matters.
Vy
length of time
Directions x & y set individually.
#$1A
Disable joysticks.
Disable any joystick event generation.
Valid joystick commands resumes generation
#$1B
Set time of day clock
YY
year
\ " (86,87,88 etc)
Aninvalid
MM
month
I
BCD digit
DD
day
I
Data sent in packed
does not
hh
hour
I
BCD format.
alter the
mm
minute
I
existing
ss
second
/
value.
#$1C
#$FC
Interrogate time of day clock
YY
year
\
MM
month
I
DD
day
I
Data in returned in
hh
hour
I
packed BCD format.
mm
minute
I
ss
second
/
#$20
Memory load
Addr msb
\ ikbd controller address
Addr lsb
/
to be loaded.
Numb
Number of data bytes (0-128)
(data)
6.5

<!-- source-page: 208 -->
## Page 208

The Concise Atari ST Reference Guide
Input
op code
string
Output
databyte
string
#$21
#$F6
Addr msb #$20
Addr lsb
data
data
data
data
data
data
#$22
Addr msb
Addr lsb
OR80""
with the
#$F6
set
mode
command param 1
param 2
param 3
param 4
param 5
param 6
6.6
#$F6
mode
param 1
param 2
param 3
param 4
param 5
param 6
Not valid if in joystick or fire button monitoring mode.
Ikbd commands cont.
Function
Memory read
\ ikbd controller
/ address to be read.
\
I 6 bytes of
I data starting
I at address
I (addr)
/
Status header
memory access
Controller execute
\ ikbd controller
/ subroutine address
Allows main system
to call an ikbd
subroutine.
Status inquiries.
#$7
#$8
#$9
Code
0
Xmaxh
0
Xmaxl
0
Ymaxh
0
Ymaxl
0
0
0
0
Packet header
#$0F #$10 #$12
\
/ \
Inquiry
returns
correct
mode
Get 8 byte data packet. Strip
packet header and return to
#$A
#$0B #$0C
recover
Xstep Xthresh Xtick
status
Ystep YthreshYrick
0
0
0
0
0
0
ONLY one
0
0
0
inquiry
0
0
0
at a
time.
#$14 #$15
/
on
<—
#$00 off
#$19 #$1A
Rx
on
Ry
«
Tx
#$00
Ty
off
Vx
Vy

<!-- source-page: 209 -->
## Page 209

The IKBD commands
Data packet function
When preceding a data packet returned from the keyboard, the special
keycodes #$F6 to #$FF give the following meanings to the data packets:
. Code
Data packet function
Dec
Hex
Status report
Absolute mouse position record
\ Relative mouse positionrecord
I 11111Oxx (xx=left-right button state)
I delta x,
2's complement
/ delta y,
2's complement
Time of day
(resolution of 1 second)
Joystick report header
(both sticks)
254
FE
xOOOyyyy
\ x=trigger
Joystick 0 event
255
FF
xOOOyyyy
/ y=stick position
Joystick 1 event
246
F6
247
F7
248
F8
to
FB
252
FC
253
FD
6.7

<!-- source-page: 210 -->
## Page 210

The Concise Atari ST Reference Guide
6.8

<!-- source-page: 211 -->
## Page 211

The Line-A routines
Chapter 7
The Line-A routines
General
7.2
Line-A access
7.2
Initialization pointers
7.2
The Line-A routines
7.3
Put pixel
7.3
Get pixel
7.3
Line
7.3
Horizontal line
7.3
Filled rectangle
7.4
Line-by-line filled polygon
7.4
Bitblt
7.5
Textblt
7.5
Show mouse
7.5
Hide mouse
7.5
Transform mouse
7.6
Undraw sprite
7.6
Draw sprite
7.6
Copy raster
7.6
Contour fill
7.6
Logic table
7.6
Line-A parameter blocks
7.7
Sprite definition block
7.7
Format flag
7.7
Memory definition block
7.7
Line-A parameter table
Bitblt table
7.8
7.10
7.1

<!-- source-page: 212 -->
## Page 212

The Concise Atari ST Reference Guide
The Line-A routines
Atari ST programmers have access to the VDI primitives via the line-A
exception routines; they provide a faster performance than the VDI routines,
additional facilities and use less code to implement. Theline-A routines maybe
mixed with VDI calls or used entirely on their own, but program portability to
other systems will not be possible.
Line-A access
The line-A routines operate from a set of variables contained in a data table
(Page7.8 - 7.9). The table is initialized by activating the line-Aexception vectorin
passing the word #$A000. The programmer may then alter or insert variables into
the data table and call the required function by passing the appropriate function
call word.
dew
#$A000
; initialize data table
move.w
#n,d(A0)
; set function at offset d
; to value n
dew
#$A00m
; call function
Initialization pointers
Initialization creates the following pointers:
dO=base address of line-A variables
aO=base address of line-A variables
al=array of pointers to the 3 system font headers
a2=array of pointers to the 15 line-A routines
(a2 is not returned correctly on disk based versions of TOS)
If VDI and AES are not used, the variables should be fairly static. If they are
used, the variables may be changed, registers d0-d2 and a0-a2 will be trashed.
7.2

<!-- source-page: 213 -->
## Page 213

The Line-A routines
Line-A routines
Function
Pointpair
Integers
Op
in
out
in
out
$0
$2
$4
$6
$8
Comments
Put
pixel
#$A001
10
10
ptsin (0)=X_msbyte, Y_lsbyte
intin (0)=pixel value
Plot a pixel at x,y
Get
pixel
#$A002
10
0
0
ptsin (0)=X_msbyte, Y_lsbyte
Get the pixel at x,y
Return d0=pixel value
Function
Parameters
Comments
Line
#$A003
offset
output
Horizontal #$A004
Line
offset
output
$26 XI coordinate
$28 Yl coordinate
$2A X2 coordinate
$2C Y2 coordinate
$18 plane 0
\
$1A plane 1
I
$1C plane 2
I
$lEplane3
/
$22 line style mask <•
$24 writing mode
$20 -1 for XOR mode
else ignore
$22 line style mask
Bit
value
$26 XI coordinate
$28 Yl coordinate
$2A X2 coordinate
$18 plane 0
\
$1A plane 1
I Bit
$1C plane 2
I value
$lEplane3
/
$24 writing mode
$2E Fill pattern pointer
$32 Fill pattern mask
$34 Multi-plane fill flag
none
Draw a line between
X1,Y1 and X2,Y2
The line is ALWAYS drawn
from left to right and the
mask applied left to right
also- so watch the phase.
/ Mask is word aligned
I pattern forhorizontal
• I lines, i.e. any bit of
I mask may be used at the
\ left-most endpoint.
Mask is rotated to align
with rightmost endpoint.
Draw a line between
X1,Y1 and X2,Y1
The line is ALWAYS drawn
from left to right
7.3

<!-- source-page: 214 -->
## Page 214

The Concise Atari ST Reference Guide
Line-A routines
cont.
Function
Filled"
rectangle
Parameters
Comments
#$A005
offset
output
$26 XI coordinate
$28 Yl coordinate
$2A X2 coordinate
$2C Y2 coordinate
$18 plane 0
\
$1A plane 1
I Bit
$1C plane 2
I value
$1E plane 3
/
$24 writing mode
$2E Fill pattern pointer
$32Fillpattern mask
$34 Multi-plane fill flag
$36 Clipping flag
$38 minimum X clipping value
$3A maximum Xclipping value
$3C minimum Y clipping value
$3E maximum Y clipping value
none
Line-by
#$A006
n
-
-
-
-line
ptsin (0)=X,Y array of
filled
polygon vertices
polygon
offset
$28 Yl coordinate
$18 plane 0
\
$1A plane 1
I Bit
$1C plane 2
I value
$1E plane 3
/
$24 writing mode
$2E Fill pattern pointer
$32 Fillpattern mask
$34 Multi-plane fill flag
$36 Clipping flag
$38 minimum X clipping value
$3A maximum X clipping value
$3C minimum Y clipping value
$3E maximum Y clipping value
Draw a filled rectangle
with upper lefthand corner
X1,Y1 and lower righthand
corner X2,Y2.
Draw one scan-line of a
filled polygon.
Polygon
Xl,Yl...Xn,Yn...Xl,Yl
Start point must be
repeated at the end
of the list.
Yl is the Y coordinate
of the line to fill.
output
none
XI and X2 trashed on return
7.4

<!-- source-page: 215 -->
## Page 215

The Line-A routines
Line-A routines
cont.
Function
Parameters
Comments
Bitblt
#$A007
Bit block transfer
input
a6=i/p parameter table pointer
See page 7.10
output
none
for table entries
Textblt
#$A008
offset
Perform a Text block
transfer of one character.
\Text
/ colour
$24=writing mode
$6A=Foreground
$72=Background
$54=Pointer
$58=Width
$48=X coor
$4A=Y coor
$4C=X coor
$4E=Y coor
$50=width
$52=height
$5A=Style flag
$5C=Lighten text mask
$5E=Skew text mask
$60=Thickening text width
$62=above \ Character offset
$64=below / from baseline
$66=Scaling flag (0=none)
$40=Accumulator for x dda
$42=Textblt scale factor
$44=Scale direction (down 0)
$68=Character rotation vector
$46=Font status
$6C=Special effects buffer pointer
$70=Scaling buffer offset in above pointer
\
I
I
/
\ Character
/ on screen
\ Character
/
Font
form
Writing mode
0-3 VDI modes
4-19 Bitblt modes
output
none
Show
mouse
#$A009
input
output
none
none
Show the mouse, if # of
'show' calls >= # of
'hide' calls.
Hide
mouse
#$A00A
input
output
none
none
Hide the mouse, if # of
'hide' calls exceeds #
of 'show' calls.
7.5

<!-- source-page: 216 -->
## Page 216

The Concise Atari ST Reference Guide
Line-A routines
cont.
Function
Parameters
Comments
Trans
-form
mouse
#$A00B
output
Transform mouse form
cntrl $E=Addr.L source MFDB
cntrl $12=Addr.L destination MFDB
none
Undraw
sprite
#$A00C
input a2=
output
sprite slave block
none
Undraw previously drawn
pointer
sprite
The sprite save block saves the
screen underneath the sprite and is
(lObytes + 648 # planes)bytesin size.
*** a6 smashed ***
Draw
sprite
#$A00D
input
output
Draw a sprite
dO=X hot spot
(Function not available
dl=Y hot spot
on disk based versions
a0=pointer to sprite definition block
of TOS)
a2=pointer to sprite save block
none
*** a6 smashed ***
Copy
raster
form
#$A00E
output
Copy a raster from source
cntrl $E=Addr.L source MFDB
to destination,
cntrl $12=Addr.L destination MFDB
none
Contour
fill
#$A00F
output
Contour fill
intin (0)=colour index
input may be +ve or -ve.
none
Logic table
%
bg
10
11
12
13
$0A
$0B
$0C
$0D
Op 0
0
Op 1
0
Op 2
1
Op 3
1
0
1
0
1
The logic operation bytes specify the effect of the foreground and
background colour bits on the current plane.
7.6

<!-- source-page: 217 -->
## Page 217

The Line-A routines
Line-A parameter blocks
Sprite definition block
0
$00
X offset of hot-spot
2
$02
Y offset of hot-spot
4
$04
Format flag
6
$06
Background
\ Colour
8
$08
Foreground
/ table index
Interleaved
\ Background line 0
10
$0A
12
$0C
background/
1Foreground line 0
foreground
1...
74
$4A
image (32words)
/ Foreground line If
76
$4C
Format flag
+ve
-ve
colour
Fg
Bg
Fg
Bg
plotted
0
0
1
0
1
1
0
0
1
0
1
1
Transparent
Background
Foreground
1
0
1
0
Foreground
XOR screen
Memory form definition block (MFDB)
0
$00
4
$04
8
$08
12
$0C
16
$10
20
$14
24
$18
28
$1C
32
$20
36
$24
Memory pointer to 32-bit address of pixel 0,0
Width
\ Raster area
Height
/ dimensions
Word width
Pixel width/word size
Format flag
1=standard, 0=device specific
Memory planes
# planes in raster area
\ Three
I reserved
/ words
7.7

<!-- source-page: 218 -->
## Page 218

The Concise Atari ST Reference Guide
Line-A parameter table
offset
Function
$00
0
Number ofvideo planes
\ Canproduce special
Number ofbytes/video line / effects.
$02
2
$04
4
Pointer to cntrl array
$08
8
Pointer to intin array
$0C
12
Pointer to ptsin array
$10
16
Pointer to intout array
$14
20
Pointer to ptsout array
$18
24
Bit plane_0
\ current
$1A
26
Bitplane_l
1colour
$1C
28
Bit plane 2
1value
$1E
30
Bit plane 3
/
$20
32
-1
$22
34
VDI line style equivalent
$24
36
Writing mode
0_replace
l_transparent
2_XOR mode
3_inverse transparent
$26
38
XI coordinate
$28
40
Yl coordinate
$2A
42
X2 coordinate
$2C
44
Y2 coordinate
$2E
46
Pointer to current fill pattern
$32
50
Fill pattern mask (length of pattern)
Multi-plane fill pattern
$34
52
0_current fill pattern is single plane
l_current fill pattern is multi-plane
$36
54
Clipping flag 0_no clipping
Minimum x clipping value
$38
56
$3A
58
Minimum y clipping value
$3C
60
Maximum x clipping value
$3E
62
Maximum y clipping value
$40
64
Accumulator for textblt x dda
initialize to 8000H before each call
$42
66
Textblt scale factor
$44
68
Scale direction 0_down
7.8

<!-- source-page: 219 -->
## Page 219

The Line-A routines
Line-A parameter table
cont.
offset
Function
$46
70
Font status
l_solid
0_proportional or variable
X coordinate of character in font form
Y coordinate of character in font form (typically 0)
X coordinate of character on screen
Y coordinate of character on screen
Character width
Character height
Pointer to start of font data (font form)
Width of font form
Style
bit 0_Thicken,
bit ljighten,
bit 2_skew
bit 3_underline (ignored),
bit 4_outline
Lighten text mask
Skew text mask
Text thickening additional width
Offset above character baseline for skew
Offset below character baseline for skew
Scaling flag 0_no scaling
Character rotation vector 0_horizontal 900_vertically down etc.
Text foreground colour
Special effects buffer pointer
Scaling buffer offset in above buffer
Text background colour (RAM VDIonly)
Copy raster form type flag (RAMVDIonly)
0_opaque type
n-plane source to n-plane destination bitblt write mode
<>0_transparent type
1-plane source to n-plane destination VDI write mode
$76
118
Abort fill routine pointer (Function not available on disk based
versions of TOS)
$48
72
$4A
74
$4C
76
$4E
78
$50
80
$52
82
$54
84
$58
88
$5A
90
$5C
92
$5E
94
$60
96
$62
98
$64
100
$66
102
$68
104
$6A
106
$6C
108
$70
112
$72
114
$74
116
7.9

<!-- source-page: 220 -->
## Page 220

The Concise Atari ST Reference Guide
BITBLT table used in block transfers (routine $A008)
Parameter block length must be 76 bytes, the first 52 bytes being set by the
user and the remainder by the bit. Address register a6 is used as a pointer to the
table, a point C programmers should note.
width
\ of block in
height
/ pixels
# of cosecutive planes to bit
foreground colour - high bit \ logic operation
background colour - low bit / index
logic operation— Table of 4 raster operation code
bytes, each containing one of sixteen
logical operations. They are indexed
by fg*2 + bg for each plane (see pg7.6).
minimum source x
minimum source y
source form base address (word boundary)
# word in line
\ next offset (2hi-4med-81ow rez)
# lines in plane
/in bytes (90hi-160med/lowrez)
next plane offset from current (always 2)
minimum destination x
minimum destination y
destination form base address (word boundary)
# word in line
\ next offset (2hi-4med-81ow rez)
# lines in plane
/ in bytes (90hi-160med/low rez)
next plane offset from current (always 2)
address of pattern buffer (0=no pattern)
Aword size repetative, word aligned pattern
that is ANDed with the source before being
logically combined with the destination,
next line in pattern
\ offset (2,4,6 etc)
next plane in pattern
/ in bytes (0=1 plane)
pattern index mask length
*may be altered during bitblt execution
Thesourcebit defined by s_xmin, s_ymin, b_width,b_heightis transfered to
destination d_xmin, d_ymin by the number of planes iterations (#planes). There
is no clipping or check that bit blocks are within the encompassing memory
forms.
0
$00
b_width
2
$02
b_height
4
$04
#planes
6
$06
fg_col
8
$08
bg_col
10
$0A
op_table
11
$0B
12
$0C
13
$0D
14
$0E
s_xmin
16
$10
s_ymin
18
$12
s_form
22
$16
s_nxwd
24
$18
s_nxln
26
$1A s_nxpl
28
$1C
d_xmin
30
$1E
d_ymin
32
$20
d_form
36
$24
d_nxwd
38
$26
d_nxln
40
$28
d_nxpl
42
$2A
p_addr
46
$2D pnxln
48
$30
p_nxpl
50
$32
pjmask
7.10

<!-- source-page: 221 -->
## Page 221

The Blitter
Chapter 8
The Blitter
General
8.2
Blitter operation
8.2
Clipping
8.2
Skew
8.2
Endmasks
8.2
Overlap
8.2
Blitter control/status
8.3
HOG bit
8.3
BUSY bit
8.3
Blitter access
8.3
Blitter flow diagram
8.4
Blitter parameter table
8.6
8.1

<!-- source-page: 222 -->
## Page 222

The Concise Atari ST Reference Guide
The Blitter
General
The New TOS versions of the Atari ST contain a hardware bit block transfer
processor (blitter) which operates automatically on certain line-A and VDI
functions, providing a considerable increase in the speed at which blocks of
memory can be manipulated. The blitter can be switched off, or tested for
presence, through the XBIOS $40 blitmode function. An attempt to 'turn on' the
blit mode in a system which does not contain a blitter is ignored by the OS. The
blitter should not be used from within an interrupt context where multiple blitter
operations may conflict and cause unpredictable results.
The blitter device moves bit aligned data in memory using one of sixteen
logic operations. It can be used to provide rapid implementation of the following
functions:
Area seed fill
Rotation and magnification
Brush line drawing
Text transformations eg. Bold, italic, outline
Textscrolling
Window updating
Pattern filling
Memory to memory block copying
Blitter operation
The blitter operates as follows,:
Initially the transfer parameters are
calculated before the data is moved, the parameters involved are:
Clipping, sets the source and destination blocks to a predefined clipping
rectangle size, the transfer is omitted ifthe block size issetto zero. Although the
blocks are the same 'size', they may have different increments.
Skew, the source to destination horizontal bit offset.
Endmasks, provide start, intermediate and finish word masks to define the
portion of the word in each line to be operated on.
Overlap, a check that source data will not be overwritten before the transfer
is complete, overlap reverses the default left to right transfer mode if necessary.
The transfer is effected after the parameters have been calculated:
8.2

<!-- source-page: 223 -->
## Page 223

The Blitter
Blitter Control/Status
Two bits in the blitter configuration registers are used to provide the
programmer with control and the status of the blitter.
The HOG bit when clear gives equal processor/blitter bus access (64 bus
cycle segments), when set the processor is stopped until the blitter transfer is
complete although other DMA processes can always interrupt the blitter.
The BUSY bit is set after the other registers are initialised and is only cleared
when the transfer is complete. Bus arbitration can still be used to initiate
processor instructions, which means that the next instruction after the transfer is
not necessarily that which set the BUSYbit.
The blitter is usually operated with the HOG flag cleared. In this mode the
blitter and the ST's CPU share the bus equally, each taking 64 bus cycles while the
other is halted. This mode allows interrupts.
Blitter access
Use of the blitter generally entails access to hardware registers and so blitter
routines are normally executed in supervisor mode. The following short
assembly language routine ensures that the blitter is switched on and saves the
original system state on the stack for later recovery. Note that if a blitter is not
present, then this code will have no affect other than to waste a small amount of
processor time.
move.w
#-l,-(sp)
; push get blitter status flag
move.w
#$40,-(sp)
; push get/set blitter function call
trap
#14
; call function
addq
#4,sp
; tidystack
move.w
dO,-(sp)
; push blitter status for later use
or.w
#l,dO
; set blitter on bit, do not touch other bits
move.w
dO,-(sp)
; push blitter on word
move.w
#$40,-(sp)
; push function call
trap
#14
; call function
addq
#4,sp
; tidy stack
Do something, remembering that the stack contains the original system state
which must not be destroyed if we wish to return to that state via something like:
move.w
trap
addq
#$40,-(sp)
#14
#4,sp
; push function call
; call function
; tidy stack
8.3

<!-- source-page: 224 -->
## Page 224

The Concise Atari ST Reference Guide
Blitter flow diagram
Source
X incr
(FF8A201
Y incr
(FF8A22)
Y incr
One word
at a time
The X incr and Y incr are
15-bit 2's complement
values (in bytes) of the
offset to the next word
or line respectively.
The SOURCE ADDRESS is
a 23-bit word containing
the address of the next
word to be used. Updated
by sign-extended Xincr
or Y incr as appropriate
immediately after the
source word fetch.
- Left to right, +ve incr's
Right to left, -ve incr's
SOURCE BUFFER
Primarily used where
the blocks are not
aligned and two
words need to be
read.
,
32-tyit source buffer
31
16
15
FXSR
register
FF8A3D
bit 7
The FXSR bit primes the source
buffer with a dummy read so
that the data may be 'skewed'
within the buffer and a valid
word passed.
Smudge
register
FF8A3C
bit 5
SMUDGE uses the least
significant nibble of the
skewed data as the
halftone offset address
8.4
NFSR
register
FF8A3D
bit 6
(SET BY OVERLAP TO PROTECT SOURCE,
BUFFER TRANSFERS REVERSED HI-LO).
The SKEW is the bit shift in
the buffer of the source
Source
beforebeing combined with
Skew
^destination data and
Req'd destination
\
halftone masks.
Skew register
FF8A3D
bits 0-3
The NFSR bit cancels the
last read when the skew and
endmask invalidate the last
word in the line, although
the buffer transfer still occurs
(FXSR and NFSR require Yincr and the Source Address registers to be amended)
LINE NUMBER defines which
word is to be used for the
current halftone line.
Increasing or decreasing
following the sign ofthe
destination Y incr register.
Line number
register
FF8A3C
bits0-3
Halftone
patterns
register
FF8A00
Line number wraps through zero.
HALFTONE is a set of
sixteen word patterns in RAM
that may be used with the
source or simply on its own
as a mask. The mask is
repeated every 16 lines.

<!-- source-page: 225 -->
## Page 225

The Blitter
Blitter flow diagram
cont.
Original
destination
16-bit destination
write masks
Endmask 1
000
111
FF8A28
Endmask 2
010
101
FF8A2A
Endmask 3
111
000
FF8A2C
NEW
DESTINATION
(d)
X incr
Y incr
Y| count
lines)
Source
HOP
register
FF8A3A
bits 0-1
(s)
LogicOP
register
FF8A3B
bits 0-3
X count
(words)
Halftone
HOP defines the source/halftone
combination to be used as source
in the logical operation.
0
All 1's
1
halftone
2 source
3 source AND halftone
Logic Operations
All 0's
sANDd
s AND NOT d
s
NOTsANDd
d
sXORd
sORd
8
NOT s AND NOT d
9
NOTsXORd
A NOTd
B s OR NOT d
C
NOTs
D NOTsORd
E NOTsORNOTd
F AIM'S
Line first write and single word line
mask only
Line
intermediate
word
Only the bits
corresponding to
a '1' in the
endmask will be
updated.
Line
last
write
Y incr
X count (words) and
Y count (lines) define the
size of the block and are
counted down, reading
the number still to be
written.
X count wraps on zero
to its original value.
A Y count of zero shows
transfer complete.
X incr and Y incr are
15-bit 2's complement
values (bytes) of the
offset to the next word
or line respectively.
The destination address is a 23-bit word containing the address of the next word to
be used. Itis automatically updated bysign-extending Xincror Y incras appropriate
(Yincr if Xcount is one) immediately after the destination write.
8.5

<!-- source-page: 226 -->
## Page 226

The Concise Atari ST Reference Guide
Blitter parameter table
The blitter configuration registers are located at address $FF8A00
Blitter offsets
0
$00
halftone
16 x 16 word pattern masks
32
$20
src_xinc
15-bit 2's complement increment of next word in source
34
$22
src_yinc
15-bit 2's complement increment of next line in source
36
$24
src_addr
23-bit address of next word to be used in source
40
$26
endmaskl destination write mask for first and single word lines
42
$28
endmask2 destination mask for intermediate words on a line
44
$2A
endmask3 destination mask for the last word on a line
46
$2C dst_xinc
15-bit 2's complement incr of next word in destination
48
$30
dst_yinc
15-bit 2's complement incr of next line in destination
50
$32
dst_addr
23-bit address of next word to be used in destination
54
$36
x_count
number of words in line yet to be written, wraps on zero.
56
$38
y_count
number of lines yet to be written
58
$3A HOP
Halftone operation options
0
All l's
1
halftone
2
source
3
source AND halftone
59
$3B OP
Logic operations
0
All 0's
8
NOTs AND NOTd
1
sANDd
9
NOTs XORd
2
s AND NOTd
A
NOTd
3
s
B
s OR NOTd
4
NOTsANDd
C
NOTs
5
d
D
NOTs ORd
6
sXORd
E
NOTs OR NOTd
7
sORd
F
All l's
60
$3C
line_num
Halftone mask line number
bit 0-3 line number (0 to 15) - halftone index
bit 5 Smudge - skew data nibble used as halftone index
bit 6 HOG - l_halt processor while transfer. 0_share bus
bit 7 BUSY - l_when registers initialised. 0_transfer over
61
$3D
skew
Source buffer bit shift
bit 0-3 bit shift (0 to 15) - source skew
bit 6 NFSR - l_no final source read. 0_normal
bit 7 FXSR -1 force initial extra source read. 0_normal
8.6

<!-- source-page: 227 -->
## Page 227

Appendices
System Variables
A
Configuration Registers
B
Printer and terminal escape codes
C
Keycode definitions
D
Callable functions
E
Parameter blocks
F
MC68000 instruction summary
G
MC68000 instruction codes
H
Error codes
I
BASIC GEM
J
Program development tools
K
Example programs
L
Glossary
M
Appendix

<!-- source-page: 228 -->
## Page 228

The Concise Atari ST Reference Guide

<!-- source-page: 229 -->
## Page 229

System Variables
Appendix A
System variables
Exception vectors
A.2
Hardware bound interrupts
A.3
Application interrupts
A.3
Error processing state dump
A.3
System variables
A.4
Bomb error codes
A.6
A.1

<!-- source-page: 230 -->
## Page 230

The Concise Atari ST Reference Guide
Thefollowing tables present the system variables in lowsupervisor space $0
to $7FF (0 to 2047):
Exception vectors
o
4
8
12
16
20
24
28
32
36
40
44
48
52
56
60
64
$000
$004
$008
$00C
$010
$014
$018
$01C
$020
$024
$028
$02C
$030
$034
$038
$03C
$040
82
$05C
96
$060
100
$064
104
$068
108
$06C
112
$070
116
$074
120
$078
124
$07C
128
$080
132
$084
136
$088
140
$08C
176
$0B0
180
$0B4
184
$0B8
188
$0BC
192
$0C0
Reset initial SSP value
(ROM)
Reset initial PC address
(ROM)
Bus error
\ Dump state
Address error
I and terminate
Illegal instruction
/ routine pointer
Divide by zero
(Pointer to an RTE)
Chk instruction
\ Dump state
Trapv instruction
I and terminate
Privilege violation
I routine pointer
Trace mode
/
Line 1010
line-A routine pointer
Line 1111
Used by AES
Unassigned
Coprocessor protocol violation (MC68020)
Format error (MC68020)
Uninitialized interrupt vector
Unassigned
\
I Reserved
Unassigned
/
Spurious interrupt (Hacked to level 3)
Int level 1
Int level 2
Int level 3
Int level 4
Int level 5
Int level 6
Int level 7
Trap #0
Trap #1
Trap #2
Trap #3
Trap #12
Trap #13
Trap #14
Trap #15
Unassigned
(Used if user wants Hblanks)
Horizontal blank sync (Hblank)
Normal processor interruptlevel
Vertical blank sync (Vblank)
MK68901 MFP interrupts
Non maskable interrupt
GEMDOS interface calls
Extended DOS calls (AES, VDI)
252
$0FC
Unassigned
GEM BIOS calls
Atari extended BIOS calls (XBIOS)
\
I Reserved
/
A.2

<!-- source-page: 231 -->
## Page 231

System Variables
MFP hardware bound interrupt vectors
*
256
$100
Parallel port interrupts (Centronics busy)
*
260
$104
RS232 carrier detect (dcd)
interrupt_l
*
264
$108
RS232 clear to send (cts)
interrupt_2
*
268
$10C
Graphics bit done
interrupt_3
*
272
$110
RS232 baud rate generator
(Timer D)
276
$114
200Hz system clock
(Timer C)
280
$118
Keyboard/MIDI (6850)
interrupt^
*
284
$11C
Polled fdc/_hdc
interrupts
*
288
$120
Horizontal blank counter
(Timer B)
292
$124
RS232transmit error interrupt
296
$128
RS232 transmit buffer empty interrupt
300
$12C
RS232receive error interrupt
304
$130
RS232receive buffer full interrupt
*
308
$134
User/application
(Timer A)
*
312
$138
RS232 ring indicator
interrupt_6
*
316
$13C
Polled monochrome monitor detect
interrupt_7
320
$140
508
$1FF
Priority levels (7 high)
*Initially disabled
The polled fdc/_hdc interrupt must be disabled on return.
Applicationinterrupts
512
$200
\
I Reserved for OEMs
892
$37C
/
After an uncaught trap, the processor state is dumped as follows:
Processor state
896
$380
proc_lives
Processor state saved if system
variable set to $12345678
900
$384
proc_regs
D0-D7/A0-A6, A7_ssp
964
$3C4
proc_pc
First byte exception number
968
$3C8
proc_usp
USP
972
$3CC
proc_stk
sixteen words of superstack
The above values are not overwritten by a system reset, but are by a further
crash.
A.3

<!-- source-page: 232 -->
## Page 232

The Concise Atari ST Reference Guide
System variables
Address
Size
Function
1024 $400
1028 $404
1032 $408
1036 $40C
L
L
L
5xL
etv_timer
etvcritic
etv_term
etv_xtra
1056 $420
1060 $424
L
B
memvalid
memcntlr
1062 $426
1066 $42A
L
L
resvalid
resvector
1070 $42E
1074 $432
1078 $436
1082 $43A
L
L
L
L
phystop
_membot
_memtop
memval2
1086 $43E
1088 $440
1090 $442
1092 $444
1094 $446
W
W
w
w
w
flock
seekrate
_timr_ms
_fverify
_bootdev
1096 $448
1098 $44A
1100 $44C
w
B
B
palmode
defshftmd
sshiftmd
1102 $44E
L
_v_bas_ad
1106 $452
W
vblsem
1108 $454
1110 $456
1114 $45A
w
L
L
nvbls
_vblqueue
colorptr
1118 $45E
1122 $462
1126 $466
L
L
L
screenpt
_vbclock
frclock
A.4
Timer handoff (logical vector $100)
Critical error handoff vector ($101)
Process terminate handoff vector ($102)
Space for reserved logical
vectors ($103-$107)
#$752019F3 (cold start o'k)
memory controller low nibble
0=128K, 4=512K, (0=256K, 5=1MB 2 banks)
#$31415926 to jump through resvector
System reset bailout vector
Physical RAMtop (points tofirst unusable byte
Available memory bottom (getmpb uses)
Available memory top (getmpb uses)
#$237698AA for legal memory configuration.
Floppy FIFO lock variable
0=6ms, l=12ms, 2=2ms, 3=3ms default
20 (#$14) system timer calibration
0=no write-verify else verify (default)
System boot device number
0=NTSC, 60Hz else PAL, 50Hz
Default video resolution if monitor changed
Shadow shiftmd hardware register
0=320x200x4 1=640x200x2 2=640x400x1
Screen memory base pointer (32Kcontiguous)
on a 512 byte boundary
Vert blank mutual exclusion semaphore
l_vblank enabled
8 (No. longwords vblqueue points to)
Vblank handler pointer to pointers
0 null else pointer to 16 word vector
for hardware palette next vblank
Pntr to screen base next vblank or 0
Vertical blank interrupt count
Count vblank interrupts not vblsem'd

<!-- source-page: 233 -->
## Page 233

System Variables
Address
System variables
cont.
Size
Function
1130 $46A
1134 $46E
1138 $472
1142 $476
1146 $47A
1150 $47E
1154 $482
1156 $484
1157 $485
1158 $486
1162 $48A
1166 $48E
L
L
L
L
L
L
W
B
L
L
1182 $49E
W
1186 $4A2
1190 $4A6
1192 $4A8
1196 $4AC
1198 $4AE
L
W
L
W
L
1202 $4B2
L
hdv_init
Hard disk initialize vector else zero
swv_vec
'Monitor changed' vector to follow
hdv_bpb
Hard disk vector to return bpb else 0
hdv_rw
Hard disk rd/wr routine vector else 0
hdv_boot
Hard disk boot routine vector else 0
hdv_mediach Disk media change routine vector else 0
_cmdload
<>0 load & exe COMMAND.PRG (boot device)
conterm
Attribute bits for console system, bit:
0_bell on (AG)
l_keyrepeat
2_keyclick
3_bios conin() function
kbshft in bits 24 to 31 of DO.L
trpl4ret
criticret
themd
md
reserved
Saved trap 14 return address
Saved return address for etv_critic
GEMDOS memory descriptors (don't change)
Structure MD
m_link
Next MD/null
m_start
Start of TPA
m_length
Byte size of TPA
m_own
MD's owner/null
? reserved
sayptr
BIOS register save area pointer
_nflops
# floppies attached 0,1 or 2
con_state
State of conoutO parser (VT52emulation)
save_row
Save row# for x-y addressing
sav_contxt Pointer to saved processor context
bufl
GEMDOS two buffer-list pointers
1st buffers data sectors
2nd buffers FAT and DIR sectors
Structure BCB
b link
Next BCB
b bufdrv
Drive#/-1
b_buftyp
Buffer type
b
bufrec
Record# cached
b__dirty
Dirty flag
b dm
Drive media descriptor
b_bufr
Buffer pointer
A.5

<!-- source-page: 234 -->
## Page 234

The Concise Atari ST Reference Guide
Address
1210 $4BA
1214 $4BE
1218 $4C2
1222 $4C6
1226 $4CA
1230 $4CE
1262 $4EE
1264 $4F0
1266 $4F2
1270 $4F6
1274 $4FA
1278 $4FE
2048 $800
System variables
cont.
Size
L
L
L
L
L
8xL
_hz_200
the_env
_drvbits
_dskbufp
autopath
vbl list
W
_prt_cnt
W
L
L
L
L
prtabt
_sysbase
_shell_p
end_os
exec os
Function
Raw 200Hz timer tick
Default environment string $00000000
32 bit vector of live block devices
Pointer to common disk buffer,
1 Kbyte in systems BSS.
(Do notusebyaninterrupt routine)
Pointer to autoexec path (or null)
Initial vblqueue
Initially set -1, ALT_HELP increments
screen-dump flag (0 abort)
Printer abort flag
Base of OS pointer (RAM or ROM)
Globalshell information pointer
Pointer to end of OS memory usage
Pointer to shell address to execute on startup
(normally1st byte of AES text seg).
Start of user RAM
Bomb error codes
# bombs
2
3
4
5
6
7
8
9
A.6
meaning
Bus error
Address error (odd address)
Illegal instruction
Division by zero
CHK exception
TRAPV exception
Privilege violation
Trace exception

<!-- source-page: 235 -->
## Page 235

Configuration Registers
Appendix B
Configuration registers
Memory configuration registers
B.2
Displayconfiguration registers
B.2
Reserved configuration register space
B.3
DMA/Disk configuration registers
B.3
Sound configuration registers
B.4
Blitter configuration registers
B.5
MK68901 configuration registers
B.6
MC6850 configuration registers
B.6
B.1

<!-- source-page: 236 -->
## Page 236

The Concise Atari ST Reference Guide
Configuration Registers (one/_zero)
MEMORY
16744452
FF8004
r/w
....XXXX 1
0
1
2
3
4
5
6
7
8
9
10
11
12+
Memory configurations
Bank 0
Bank 1 (not used)
128Kbyte
128Kbyte
128Kbyte
512Kbyte
128Kbyte
2Mbyte
reserved
512Kbyte
128Kbyte
512Kbyte
512Kbyte
512Kbyte
2Mbyte
reserved
2Mbyte
128Kbyte
2Mbyte
512Kbyte
2Mbyte
2Mbyte
reserved
reserved
DISPLAY
16745061
FF8201
r/w
XXXXXXXX1
Video base high
16745063
FF8203
r/w
xxxxxxxx1
Video base low
16745065
FF8205
r
XXXXXXXX1
Video address counter high
16745067
FF8207
r
XXXXXXXX1
Video address counter mid
16745069
FF8209
r
XXXXXXXX1
Video address counter low
16745071
FF820A
r/w
XX 1
bitO
bitl
Sync mode
External/ Internal sync
50Hz/_60Hz field rate
16745124
FF8240
r/w
XXX.XXX.XXX
bitO
Palette colour 0/0 (border)
Invert/ normal mono
bit 0-2
Blue
bit 4-6
Green
bit 8-10
Red
16745126
FF8242
r/w
XXX.XXX.XXX
Palette colour 1/1
16745128
FF8244
r/w
XXX.XXX.XXX
Palette colour 2/2
16745130
FF8246
r/w
XXX.XXX.XXX
Palette colour 3/3
16745132
FF8248
r/w
XXX.XXX.XXX
Palette colour 4
16745134
FF824A
r/w
XXX.XXX.XXX
Palette colour 5
16745136
FF824C
r/w
XXX.XXX.XXX
Palette colour 6
16745138
FF824E
r/w
XXX.XXX.XXX
Palette colour 7
16745140
FF8250
r/w
XXX.XXX.XXX
Palette colour 8
B.2

<!-- source-page: 237 -->
## Page 237

Configuration Registers
Configuration Registers ( Dne/_zero)
cont.
16745142
FF8252
r/w
1 ....XXX.XXX.XXX 1
Palette colour 9
16745144
FF8254
r/w
1 ....XXX.XXX.XXX 1
Palette colour 10
16745146
FF8256
r/w
1 ....XXX.XXX.XXX 1
Palette colour 11
16745148
FF8258
r/w
1 ....XXX.XXX.XXX 1
Palette colour 12
16745150
FF825A
r/w
1 ....XXX.XXX.XXX 1
Palette colour 13
16745152
FF825C
r/w
1 ....XXX.XXX.XXX 1
Palette colour 14
16745154
FF825E
r/w
1 ....XXX.XXX.XXX 1
Palette colour 15
16745156
FF8260
r/w
1
XX 1
Shift mode
0
320x200,
4 plane
1
640x200,
2 plane
2
640x400,
1 plane
3
Reserved
Reserved
16745572
FF8400
sk
1
1
DMA/Di
16746084
FF8600
FF8602
FF8604
r/w
1
|
16746086
1
1
16746088
1
XXXXXXXX 1
16746090
FF8606
r
1
XXX 1
bitO
bitl
bit 2
FF8606
w
1
XXXXXXXX. 1
bitl
bit 2
bit 3
bit 4
bit 5
bit 6
bit 7
bit 8
16746093
FF8609
r/w
1XXXXXXXX1
16746095
FF860B
r/w
1XXXXXXXX1
16746097
FF860D
r/w
1XXXXXXXX1
reserved
reserved
reserved
Disk controller data access
DMA status (mode control)
_Error
_Sector count zero
_Data request inactive
DMA mode control
A0) WD1772
Al) registers
HDC/FDC register select
Sector count register select
0 reserved
Disable/_enable DMA
FDC/_HDC
Write/jread
DMA base and counter high
DMA base and counter mid
DMA base and counter low
B.3

<!-- source-page: 238 -->
## Page 238

The Concise Atari ST Reference Guide
Configuration Registers (one/_zero)
cont.
SOUND
PSG read data
16746596
FF8800
r
1XXXXXXXX1
I/O port B, Parallel i/f data
w
1XXXXXXXX1
PSG register select
reg#
8 bit 0
Channel A fine tune
4 bit
1
Channel A coarse tune
8 bit
2
Channel B fine tune
4 bit
3
Channel B coarse tune
8 bit
4
Channel C fine tune
4 bit
5
Channel C coarse tune
5 bit
6
Noise generator control
8 bit
7
Mixer control-I/O enable
5 bit
8
Channel A amplitude
5 bit 9
Channel B amplitude
5 bit
10
Channel C amplitude
8 bit
11
Envelope period fine tune
8 bit
12
Envel period coarse tune
4 bit 13
Envelope shape
14
I/O port A (output only)
15
I/O port B (Centronics O/P)
16746598
FF8802
w
1XXXXXXXX1
PSG write data, I/O port A
bitO
Floppy side 0/_side 1 select
bitl
Floppy _drive 0 select
bit 2
Floppy drive 1 select
bit 3
RS232 RTS
bit 4
RS232 DTR
bit 5
Centronics STROBE
bit 6
Generalpurpose output
Reserved
bit 7
r/w
1XXXXXXXX1
I/O port B, Par i/f data
B.4

<!-- source-page: 239 -->
## Page 239

Configuration Registers
Configuration Registers (one/zero)
cont.
Blitter
16747108
FF8A00
16747110
FF8A02
16747112
FF8A04
16747138
FF8A1E
16747140
FF8A20
16747142
FF8A22
16747144
FF8A24
16747146
FF8A26
16747148
FF8A28
16747150
FF8A2A
16747152
FF8A2C
16747154
FF8A2E
16747156
FF8A30
16747158
FF8A32
16747160
FF8A34
16747162
FF8A36
16747164
FF8A38
16747166
FF8A3A
16747167
FF8A3B
16747168
FF8A3C
16747169
FF8A3D
IxxxxxxxxxxxxxxxxI
IxxxxxxxxxxxxxxxxI
IxxxxxxxxxxxxxxxxI
Halftone RAM
16 x 16 pattern
mask
1xxxxxxxxxxxxxxxx1
1xxxxxxxxxxxxxxx. 1
1xxxxxxxxxxxxxxx. 1
1
XXXXXXXX 1
Source increment X
Source increment Y
\ Source address
1xxxxxxxxxxxxxxx. 1
1xxxxxxxxxxxxxxxx1
1xxxxxxxxxxxxxxxx1
1xxxxxxxxxxxxxxxx1
1xxxxxxxxxxxxxxx. 1
1xxxxxxxxxxxxxxx. 1
1
XXXXXXXX 1
/
Endmask 1
Endmask 2
Endmask 3
Destination increment X
Destination increment Y
\ Destination address
1XXXXXXXXXXXXXXX. 1
1XXXXXXXXXXXXXXXX1
1XXXXXXXXXXXXXXXX1
/
count x (words across)
count y (lines down)
1
XX 1
1
xxxxl
HOP halftone operation
OP logic operation
1XXX.XXXX 1
bit 0-3
bit 5
bit 6
bit 7
Halftone mask line
line number of halftone
pattern RAM
Smudge
HOG
Busy
1xx...xxxxl
bit 0-3
bit 6
bit 7
Source buffer skew
source skew shift
NFSR toggle
FXSR toggle
B.5

<!-- source-page: 240 -->
## Page 240

The Concise Atari ST Reference Guide
Configuration Registers (one/_zero)
cont.
MK68901
16775681
FFFA01
16775683
FFFA03
16775685
FFFA05
16775687
FFFA07
16775689
FFFA09
16775691
FFFA0B
16775693
FFFA0D
16775695
FFFA0F
16775697
FFFA11
16775699
FFFA13
16775701
FFFA15
16775703
FFFA17
16775705
FFFA19
16775707
FFFA1B
16775709
FFFA1D
16775711
FFFA1F
16775713
FFFA21
16775715
FFFA23
16775717
FFFA25
16775719
FFFA27
16775721
FFFA29
16775723
FFFA2B
16775725
FFFA2D
16775727
FFFA2F
MC6850
16776192
FFFC00
16776194
FFFC02
16776196
FFFC04
16776198
FFFC06
All unused bits read zero.
B.6
IXXXXXXXXI
bitO
bit 4
bit 5
bit 7
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXX I
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXX I
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXX I
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
IXXXXXXXXI
MFP general purpose I/O
Parallel port status
WD1772 active
Interrupt
Mono monitor
MFP active edge
MFP data direction
MFP interrupt enable A
MFP interrupt enable B
MFP interrupt pending A
MFP interrupt pending B
MFP intrpt in-service A
MFP intrpt in-service B
MFP interrupt mask A
MFP interrupt mask B
MFP vector base
MFP timer A control
MFP timer B control
MFP timers C & D control
MFP timer A data
MFP timer B data
MFP timer C data
MFP timer D data
MFP sync character
MFP USART control register
MFP receiver status
MFP transmitter status
MFP USART data
Keyboard ACIA control
Keyboard data
Midi ACIA control
Midi data

<!-- source-page: 241 -->
## Page 241

Escape Codes
Appendix C
Printer and terminal escape codes
Typical Epson printer codes
C.2
VT52 terminal escape codes
C.4
Printers
C.5
C.1

<!-- source-page: 242 -->
## Page 242

The Concise Atari ST Reference Guide
Typical Epson Printer Codes
Code
Ascii
Function
***** ESC code functions *****
Dec
Hex
Mnemo
Dec
Hex Ch
0
00
NUL
32
20
1
01
SOH
33
21
I
Combine print modes
2
02
STX
* for one
34
22
it
3
03
ETX
line only
35
23
#
4
04
EOT
36
24
$
5
05
ENQ
37
25
%
Select ROM/user charset
6
06
ACK
38
26
&
Define user characters
7
07
BEL
Bell
39
27
'
8
08
BS
Backspace
40
28
(
9
09
HT
Tab horizontal
41
29
)
10
0A
LF
Line feed
42
2A
*
Select graphics mode
11
OB
VT
Tab vertical
43
2B
+
12
0C
FF
Form feed
44
2C
13
0D
CR
Carriage Return
45
2D
-
Underline on/off
14
0E
SO
*Enlarged on
46
2E
15
OF
SI
Condensed on
47
2F
/
Select vert Tab channel
16
10
DLE
48
30
0
Set 1/8 inch LF
17
11
DC1 On-line printer
49
31
1
Set 7/72 inch LF
18
12
DC2 Condensed off
50
32
2
Set 1/6 inch LF
19
13
DC3 Off-line printer
51
33
3
Set n/216 inch LF
20
14
DC4 *Enlarged off
52
34
4
Italic on
21
15
NAK
53
35
5
Italic off
22
16
SYN
54
36
6
23
17
ETB
55
37
7
24
18
CAN Clear print buffer
56
38
8
Detect paper-out on
25
19
EM
Cut sheet feeder
57
39
9
Detect paper-out off
26
1A
SUB
58
3A
Copy ROM char to RAM
27
IB
ESC
59
3B
/
28
1C
FS
60
3C
<
*Unidirection print
29
ID
GS
61
3D
=
30
IE
RS
62
3E
>
31
IF
US
63
•
64
65
3F
40
41
?
@
A
Redefine graphic mode
Initialize printer
Set n/72 inch LF
32
20
Printab
66
42
B
Set vertical Tabs
127
7F
67
68
69
43
44
45
C
D
E
n Set form length
Set horizontal Tabs
Bold on
70
46
F
Bold off
C.2

<!-- source-page: 243 -->
## Page 243

Escape Codes
Typical Epson Printer Codes
cont.
***** ESC code functions *****
***** ESC code functions
*****
Dec
Hex Ch
Dec
Hex
Ch
71
47
G
Double strike on
110
6E
n
72
48
H
Double strike off
111
6F
0
73
49
I
112
70
P
Proportional on/off
74
4A
J
LF n/216inch
113
71
q
75
4B
K
60 dpi bitimage
120 dpi bitimage
114
72
r
76
4C
L
115
73
s
Half speed on/off
77
4D
M
Elite on
116
74
t
78
4E
N
Skip perforation on
117
75
u
79
4F
O
Skip perforation off
118
76
V
80
50
P
Pica on/Elite off
119
77
w
81
51
Q
Set right column
120
78
X
select draft/NLQ mode
82
52
R
Select character set
121
79
y
83
53
S
Super/subscript on
122
7A
z
84
54
T
Super/subscript off
123
7B
{
85
55
U
Unidirection on/off
124
7C
1
86
56
V
125
7D
}
87
57
w
Enlarged on/off
126
7E
88
58
X
127
7F
del
Cancel last character
89
59
Y
120 dpi bitimage-fast
90
5A
z
240 dpi bitimage
91
5B
[
92
5C
\
93
5D
]
94
5E
A
Set 9 pin bit image
95
5F
96
60
/
97
61
a
Set NLQ justify
98
62
b
Set vertical tabs channels
99
63
c
100
64
d
101
65
e
Set hor/ver Tab increment
102
66
f
Paperfeed/Tab execute
103
67
g
104
68
h
105
69
i
106
6A
j
107
6B
k
108
6C
1
Set left margin
109
6D
m
Special character generator
C.3

<!-- source-page: 244 -->
## Page 244

The Concise Atari ST Reference Guide
VT52 terminal escape codes
The following BIOS bconoutO functions simulate a VT52 terminal, with
extensions for colour, screen wrap etc.
Esc
Function
A
B
C
D
Cursor up
Cursor down
Cursor right
Cursor left
E
H
I
Clear screen
Home cursor
Cursor up
J
K
L
Erase to eop
Clear to eol
Insert line
M
Delete line
Y,r,c Cursor r,c
b,f
Cb
fgd colour f
bgd colour b
d
e
f
j
k
Erase to start
of page
Show cursor
Hide cursor
Save cursor
Restore cursor
1
0
P
q
Erase line
Erase to start
of line
Reverse video
Normal video
V
w
Wrap at end
of line
Discard end
of line
C.4
Comments
Up one line, no affect if at top
Down one line, no affect if at bottom
Right one position, no affect if at edge
Left one position, no affect if at edge
Clear screen and home cursor to column 0, row 0
Home cursor to column 0, row 0
Up one line, if at top scroll
Erase to end of page from and including cursor position
Clear to end of line from cursor position
Insert blank line with cursor at start of line.
Move current line down
Delete cursor line and move remaining lines up one,
put blank at bottom.
Position cursor at row r column c
Colour is the 4 lsb of colour byte
Colour is the 4 lsb of colour byte
Erase to start of page including the current cursor position
Show cursor
Hide cursor
Save thecursorposition
Restore cursor, home if no saved posn
Erase line and move cursor left edge
Erase to start of line from and including the cursor
Enter reverse video mode
Exit reverse video mode
Wrap at end of line and scroll up if necessary
Overprint line end character with the next character

<!-- source-page: 245 -->
## Page 245

Escape Codes
Printers
In general an Atari printer that is designed to work with the ST will provide
the most suitable path to trouble free computer/printer interfacing and the
production of hard copy printout and screen dumps. Where a printer from
another manufacturer is to be used, the following may be of use:
If screen dumps are required, the code IB 4C (27 76 dec) should be
recognized as 'double density bit image mode' for printing 960 dots/line at 120
dots/inch on 8" wide paper (the dump is virtually the same size as the monitor
screen display) or code IB 59 (2789dec) for the wider paper screen dumps.
It may reasonably be assumed that whatever word processor you employ, it
will provide the necessary print configuration file to make available the printers
facilities. Double clicking a non-executable file icon to print it's contents should
not cause problems as control codes are not sent within the text. The ST does
howeverprecede the file with the code to selectdraft or NLQ(nearletter quality)
print, i.e ESC,"x",n.
Some serial printers are restricted to 2400 and 600 baud operation, the ST
supports neither rate without recource to C or assembly language programming.
C.5

<!-- source-page: 246 -->
## Page 246

The Concise Atari ST Reference Guide
C.6

<!-- source-page: 247 -->
## Page 247

Keycode Definitions
Appendix D
Keycode definitions
Ascii codes
D.3
GSX compatible keyscan codes
D.4
VDI standard keyboard codes
D.5
Note that the keycodes returned do differ for the different international
keyboards.
D.1

<!-- source-page: 248 -->
## Page 248

The Concise Atari ST Reference Guide
ASCII codes
0 to 127
Dec
Ascii
Dec
Ascii
Dec
Ascii
Dec
Ascii
0
NUL
32
SPACE
64
@
96
>
1
SOH
33
j
65
A
97
a
2
STX
34
"
66
B
98
b
3
ETX
35
#
67
C
99
c
4
EOT
36
$
68
D
100
d
5
ENQ
37
%
69
E
101
e
6
ACK
38
&
70
F
102
f
7
BEL
39
'
71
G
103
g
8
BS
40
(
72
H
104
h
9
HT
41
)
73
I
105
i
10
LF
42
*
74
J
106
i
11
VT
43
+
75
K
107
k
12
FF
44
/
76
L
108
1
13
CR
45
-
77
M
109
m
14
SO
46
78
N
110
n
15
SI
47
/
79
O
111
0
16
DLE
48
0
80
P
112
P
17
DC1
49
1
81
Q
113
q
18
DC2
50
2
82
R
114
r
19
DC3
51
3
83
S
115
s
20
DC4
52
4
84
T
116
t
21
NAK
53
5
85
U
117
u
22
SYN
54
6
86
V
118
V
23
ETB
55
7
87
W
119
w
24
CAN
56
8
88
X
120
X
25
EM
57
9
89
Y
121
y
26
SUB
58
90
Z
122
z
27
ESC
59
/
91
[
123
{
28
FS
60
<
92
\
124
1
29
GS
61
=
93
]
125
}
30
RS
62
>
94
A
126
~
31
US
63
1
95
-
127
DEL
D.2

<!-- source-page: 249 -->
## Page 249

Keycode Definitions
GSX compatible keyscan codes
. Code
Keytop
. Code
Keytop
. Code
Keytop
Dec
Hex
Dec
Hex
Dec
Hex
1
01
ESC
38
26
L
75
4B
left arrow
2
02
1
39
27
/
76
4C
n.u
3
03
2
40
28
'
77
4D
right arrow
4
04
3
41
29
'
78
4E
kpd +
5
05
4
42
2A
left shift
79
4F
n.u
6
06
5
43
2B
\
80
50
down arrow
7
07
6
44
2C
Z
81
51
n.u
8
08
7
45
2D
X
82
52
INSERT
9
09
8
46
2E
c
83
53
DEL
10
0A
9
47
2F
V
84
54
n.u
to
11
0B
0
48
30
B
95
5F
n.u
12
oc
-
49
31
N
96
60
ISO key
13
0D
CR
50
32
M
97
61
UNDO
14
0E
BS
51
33
/
98
62
HELP
15
OF
TAB
52
34
99
63
kpd(
16
10
Q
53
35
/
100
64
kpd)
17
11
W
54
36
right shift
101
65
kpd/
18
12
E
55
37
n.u
102
66
kpd*
19
13
R
56
38
ALT
103
67
kpd 7
20
14
T
57
39
space bar
104
68
kpd 8
21
15
Y
58
3A
caps lock
105
69
kpd 9
22
16
U
59
3B
Fl
106
6A
kpd 4
23
17
I
60
3C
F2
107
6B
kpd 5
24
18
O
61
3D
F3
108
6C
kpd 6
25
19
P
62
3E
F4
109
6D
kpdl
26
1A
[
63
3F
F5
110
6E
kpd 2
27
IB
]
64
40
F6
111
6F
kpd 3
28
1C
RET
65
41
F7
112
70
kpdO
29
ID
CNTL
66
42
F8
113
71
kpd.
30
IE
A
67
43
F9
114
72
kpd ENTER
31
IF
S
68
44
F10
115
73
n.u
32
20
D
69
45
n.u
116
74
left_m/jstk_0
33
21
F
70
46
n.u
117
75
rt m/jstk_l
34
35
22
23
G
H
71
72
47
48
HOME
up arrow
UK Keyboard
36
24
j
73
49
n.u
43
2B
il
37
25
k
74
4A
kpd-
96
60
\
Returned highword lowbyte from the BDOS c_conin function
n.u = not used
xx_m/jstk_l=mouse/joystick button
D.3

<!-- source-page: 250 -->
## Page 250

The Concise Atari ST Reference Guide
GEM VDI standard keyboard codes
High Low Character
High Low Character
High Low Character
bvte bvte
bvte bvte
bvte bvte
03
00
Ctl 2
39
20
space
03
40
@
IE
01
Ctl A
02
21
!
IE
41
A
30
02
Ctl B
28
22
"
30
42
B
2E
03
Ctl C
2B/04 23
#
2E
43
C
20
04
Ctl D
05
24
$
20
44
D
12
05
Ctl E
06
25
%
12
45
E
21
06
Ctl F
08
26
&
21
46
F
22
07
Ctl G
28
27
'
22
47
G
23
08
Ctl H
OA
28
(
23
48
H
17
09
Ctl I
OB
29
)
17
49
I
24
OA
CtlJ
09
2A
*
24
4A
J
25
0B
Ctl K
OD
2B
+
25
4B
K
26
0C
Ctl L
33
2C
,
26
4C
L
32
0D
Ctl M
OC
2D
-
32
4D
M
31
OE
Ctl N
34
2E
.
31
4E
N
18
OF
Ctl O
35
2F
/
18
4F
O
19
10
Ctl P
OB
30
0
19
50
P
10
11
Ctl Q
02
31
1
10
51
Q
13
12
Ctl R
03
32
2
13
52
R
IF
13
Ctl S
04
33
3
IF
53
S
14
14
Ctl T
05
34
4
14
54
T
16
15
Ctl U
06
35
5
16
55
U
2F
16
Ctl V
07
36
6
2F
56
V
11
17
Ctl W
08
37
7
11
57
W
2D
18
Ctl X
09
38
8
2D
58
X
15
19
Ctl Y
OA
39
9
15
59
Y
2C
1A
Ctl Z
27
3A
:
2C
5A
Z
1A
IB
Ctl [
27
3B
;
1A
5B
[
2B
1C
Ctl \
33
3C
<
2B
5C
\
IB
ID
Ctl ]
OD
3D
=
IB
5D
]
07
IE
Ctl 6
34
3E
>
07
5E
A
OC
IF
Ctl -
35
3F
?
OC
5F
underscore
D.4

<!-- source-page: 251 -->
## Page 251

p
en
H
ro
n
n
o
a
ro
3
o
o
i-j
ro
a
a-
31
ro
>
3
en
H
od
O
OtOi—'OiMMMhJi-i(Oi—ii-i|—11-11-11—1|—i0J0JtOtO|NJi-itOtOK)i-itOK)0Ji-'fO
MNOaJO|>nuiU>->^aN,^'TiwoNOOoi-iMON<jni^vqw,SJ'-J,0offlOt-rf^
vjvjvqWvjvjvqvjvavgvj^jvg^jvavaoNaNONONONO-NONONONONaNaNONONaNON
|-dMrj^W>^0°^^Cjntl^0Jto^oiTllTirjncd>^000Vi0NCn4^0Jto^ o-j<
' —— Nv; X ^
< f! "[» i^^ o
3 B "" JC"-" "— yoq ^(D JL" tftt
-
a
'
w
r
nO'< p!
err
o
KJMi-ii-ii-iMMi-iWWK)tOtOi-'[.JK)WH[xJhJWMa)N]NjNjN]Nj\iN]N]oorrif
,T]0M^»flWOVD<»i-iM0NUl*iNgutN)Mt0Otr1O|TlOhl(tl]rjnffl>v00!> *"""< •
ro 5*
err
o
ro S
n
3"
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO 0'<
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
i
i
i
i
i
i
i
i
i
ii
i
r
i
i
i
i
i
i
i
i
i
i
i
i
i
i
i
i
i
i
i
<C^HCT3?30^0ZgrH^^^^OtTirrlOr)Ci3>^DOoN|CTNai^OJto^o
UI it^ OJ to
ONONONO^O^ON(JlUiaiCjnOlCjlUlOlOlOnCn(_ni*^4^i^.i^.*.OJOJOJOJOJKJi—ifO
'°h[<Mrjnro>VOCOV|ON(ii*'itiWMMO'TiMonwnijiD
5ffi
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO-0'<tfr
o
******* if^yiyitn^yiUiyiyiVlifliTliflijlHnixlhflhijhrjhrl^vvv
^^•i1>Tlfl'Tl>Tl,T|5J345'5'5J5'5'S'5'y^NO0ONj^Ui*.WMM!l>l!l-l
tO tO tO IO tO tO tO tO,'-h|'^lH^|,^|M^|,^>|l^N|hT>|'^|Hf> o
oo ni on oi 4-oj to h-%VtI V>flV*fl VnVn VdVfl
MVOtBNONOli^UMM
o
I
I
I
I
N^X^
o
m
<
g
</)
0)
Q.
0)
7T
CD
><
ex
o
0)
-t
Q.
o
o
a
CD
CO
o
o
13
ro
^<
n
o
a
ro
a
ro
o
3

<!-- source-page: 252 -->
## Page 252

The Concise Atari ST Reference Guide
GEM VDI standard keyboard codes
cont.
High Low Character
High Low Character
bvte bvte
bvte bvte
66
00
*F29
53
2E
Shift delete
67
00
*F30
72
00
*Ctl_ print screen
68
00
*F31
37
2A
* Print screen
69
00
*F32
01
IB
Escape
6A
00
*F33
0E
08
Backspace
6B
00
*F34
82
00
Alt -
6C
00
*F35
83
00
Alt =
6D
00
*F36
1C
0D
CR
6E
00
*F37
1C
0A
Ctl_ cr
6F
00
*F38
4C
35
Shift number pad 5
70
00
*F39
4A
2B
Number pad -
71
00
*F40
4E
2B
Number pad +
73
00
Ctl_ left arrow
OF
09
Tab
4D
00
Right arrow
OF
00
* Backtab
4D
36
Shft right arrow
4B
00
Left arrow
74
00
Ctl_ right arrow
4B
34
Shift left arrow
50
00
Down arrow
4F
00
*End
50
32
Shift down arrow
4F
31
* Shift end
48
00
up arrow
Shift up arrow
75
00
* Ctl end
48
38
51
00
* Page down
51
33
*Shift page down
76
00
*Ctl_ page down
49
00
* Page up
49
39
*Shift page up
84
00
*Ctl_ page up
77
00
Ctl_ home
47
00
Home
47
37
Shift home
52
00
Insert
52
30
Shift insert
53
00
Delete
' These scan codes are not supported by the Atari ST BIOS
D.6

<!-- source-page: 253 -->
## Page 253

/
54 /
55 /
567
57/
58/
597
5A/
SB/5C7
5D~
3B /3C /3D /3E /3F /40 /41
/42 /43 /44
/
01
02
33 04
05
06 07 08 09
OA
OB OC OD 29
OE
OF
10
11
12
13
14
15
16 17 18 19 1A 1E
C
52
2B
ro
1E= 1F'- 2()
2"
22i
2:S
2<-I 21i
2(5 2"7 2 3
24 60
2C 2D 2E 2F 30
31
32 33
34
35
36
38
39
3A
Keycode Definitions
62
61
52
48
47
4B 50
4D
63
64
65
66
67
68
69
4A
6A 6B 6C 4E
6D 6E 6F
72
70
71
D.7

<!-- source-page: 254 -->
## Page 254

The Concise Atari ST Reference Guide
D.8

<!-- source-page: 255 -->
## Page 255

Callable Functions
Appendix E
List of callable functions
BIOS (Trap #13)
E.2
XBIOS (Trap #14)
E.2
GEMDOS (Trap #1)
E.4
Extended BDOS (Trap #2)
E.5
GEM VDI
E.6
GEM AES
E.9
ikbd command set
E.12
Line-A routines
E.13
E.1

<!-- source-page: 256 -->
## Page 256

The Concise Atari ST Reference Guide
List of callable functions
BIOS calls (Trap #13)
. Code
Function
Pg. #
Dec
Hex
0
00
getmpb
Get and fill memory parameter block
3.4
1
01
bconstat
Return character-device input status
3.4
2
02
bconin
Input character to device, return when done
3.4
3
03
bconout
Output character to device, return when done3.4
4
04
rwabs
Read/write logical sectors from/to device
3.5
5
05
setexc
Get or set vector number
3.5
6
06
tickcal
Return system timer value (ms)
3.5
7
07
getbpb
Return pointer to BIOS parameter block
3.5
8
08
bcostat
Return character output device status
3.5
9
09
mediach
Check for media change
3.5
10
0A
drvmap
Get/set bit map and logical drives
3.6
11
0B
kbshft
Set keyboard shift bits
3.6
Callable from user mode, re-entrant to three levels
Device =
0_Printer,
parallel port
l_Aux,
RS232 port
2_Con,
screen
3_Midi
4_Keyboard
XBIOS calls (Trap #14)
. Code
Function
Pg. #
Dec
Hex
0
00
inimous
Initialize mousepackethandler
3.7
1
01
ssbrk
Reserve X bytes from top memory
3.7
2
02
_physbase Get screensphysicalbase address
3.7
3
03
Jogbase
Get screens logicalbase
3.8
4
04
getRez
Get screens current resolution
3.8
5
05
_setScreen Set screen logical location
3.8
6
06
_setPalette Set hardware palette registers
3.8
7
07
_setcolor
Set the palette number
3.8
8
08
_floprd
Read sectors from floppy disk
3.8
9
09
_flopwr
Write sectors to floppy disk
3.9
E.2

<!-- source-page: 257 -->
## Page 257

Callable Functions
XBIOS calls
(Trap #14)
cont.
. Code
Dec
Hex
Function
Pg.#
10
OA
_flopfmt
Format floppy disk
3.9
11
OB
getdsb
Get device status block pointer
3.9
12
OC
midiws
Write string to MIDI port
3.9
13
OD
_mfpint
Set MFP interrupt number
3.9
14
OE
iorec
Return pointer to serial device buffer record
3.10
15
OF
rsconf
"Configure"RS232"port"
~3T0
16
10
keytbl
Set/get pointer to keyboard translation table 3.10
17
11
_random
Return 24 bit pseudo random number
3.10
18
12
protobt
Prototype image boot sector
3.11
19
13
Jflopver
Verify sectors from floppy
3.11
20
14
scrdmp
Dumpscreen toprinter
21
15
cursconf
Get/set cursor blink/attributes
22
16
settime
Set keyboard time and date
23
17
gettime
Get time and date from keyboard
24
18
bioskeys
Restore keyboard translation tables
25
19
ikbdws
Write string to interrupt keyboard
26
1A
jdisint
Disable interrupt # on MK68901
27
IB
jenabint
Enable interrupt # on MK68901
28
1C
giaccess
Read/write sound chip register
29
ID
offgibit
Set port A bit to 0 atomically
3.11
3.11
3.11
3.11
3.12
3.12
3.12
3.12
3.12
3.12
30
IE
ongibit
Set port A bit to 1 atomically
3.12
31
IF
xbtimer
Set MFPtimers and control registers
3.12
32
20
dosound
Set pointer to sound command bytes
3.13
33
21
setprt
Set/get printer configuration byte
3.13
34
22
kbdvbase
Return pointer to keyboard structure
3.13
35
23
kbrate
Get/set keyboard repeat rate
36
24
_prtblk
Hard copy routine
37
25
vsync
Wait for next vblank
38
26
supexec
Execute in super mode
39
27
puntaes
Throw awayAES
64
40
blitmode
Get/set blitter status
Callable from user mode.
3.13
3.14
3.14
3.14
3.14
3.14
E.3

<!-- source-page: 258 -->
## Page 258

The Concise Atari ST Reference Guide
GEMDOS calls
(Trap #1)
.Code
Dec
Hex
0
00
p_term_o
1
01
c_conin
2
02
c_conout
3
03
c_auxin
4
04
c_auxout
5
05
c_prnout
6
06
c_rawio
7
07
c_rawcin
8
08
c_necin
9
09
c_conws
10
0A
c_conrs
11
0B
c_conis
14
0E
d_setdrv
16
10
c_conos
17
18
11
12
c_prnos
c_auxis
19
13
c_auxos
25
26
19
1A
d_getdrv
f_setdta
42
43
2A
2B
t_getdate
t_setdate
44
45
2C
2D
t_gettime
t_settime
47
48
2F
30
f_getdta
s_version
49
31
p_termres
54
36
d_free
57
39
d_create
58
3A
d_delete
59
60
3B
3C
d_setpath
f_create
61
62
3D
3E
f_open
f_close
63
3F
f_read
64
40
f_write
65
41
f_delete
66
42
f seek
67
43
f_attrib
69
45
f_dup
E.4
Function
Pg.#
Terminate process (use $4c)
3.15
Read character from standard input
3.15
Write character to standard output
3.15
Read character from aux device
3.15
Write character to aux device
3.15
Write character to standard print device
3.15
Raw input tostandardinput
3.16
Raw input from standard input
3.16
Read character from standard input -no echo 3.16
Write null terminated string to standard o/p 3.16
Read editted string from standard input
3.16
Check status of standard input
3.16
Set default drive
3.16
Check status ofstandard output
3.16
Check status standard print device
3.16
Check status standard aux device input
3.16
Check status standard aux device output
3.17
Get current drive
3.17
Set disk transfer address
3.17
Get date
3.17
Set date
3.17
Get time
3.17
Set time
3.17
Get disk transfer address
3.17
Get version number
3.17
Terminate and stay resident
3.17
Get drive free space
3.18
Create a subdirectory
3.18
Delete a subdirectory
3.18
Set current directory
3.18
Create a file
3.18
Open file
3.18
Close file
3.18
Read file
3.19
Write file
3.19
Delete file
3.19
Seekfilepointer
3.19
Get/Set file attribute
3.19
Duplicate file handle
3.19

<!-- source-page: 259 -->
## Page 259

Callable Functions
GEMDOS calls (Trap #1)
cont.
. Code
Dec
Hex
Function
Pg.#
70
46
f force
Force file handle
3.20
71
47
d_getpath Get current directory
3.20
72
48
m
alloc
Allocate memory
3.20
73
49
m
free
Free allocated memory
3.20
74
4A
m
shrink
Shrink size of allocated memory
3.20
75
4B
p_exec
Load or execute a process
3.20
76
4C
p_term
f sfirst
Terminate process
Search for first occurrence of filespec
3.21
78
4E
3.21
79
4F
f snext
Search for next occurrence of filespec
3.21
86
56
f rename
Rename a file
3.21
87
57
f_datime
Get/set file date and time stamp
3.22
32
20
smode
Set/get supervisor/user mode
3.23
Extended BDOS call
(Trap #2)
. Cotie
Function
Pg.i
Dec
Hex
0
00
System reset
System/program control
3.25
lib
73
VDI access
3.25
200
c8
AES access
3.25
201
c9
-2
fe
GDOS version test
3.25
E.5

<!-- source-page: 260 -->
## Page 260

The Concise Atari ST Reference Guide
GEM VDI functions
Op
Definition
code
*1
Openworkstation
* 2
Close workstation
3
Clear workstation
4
Update workstation
5
Escape code
1
Inquire address of character cells
2
Exit alpha mode
3
Enter alpha mode
4
Cursor up
5
Cursor down
6
Cursor right
7
Cursor left
8
Home cursor
9
Erase to screen end
10
Erase to line end
11
Direct cursor address
12
Output cursor addressable text
13
Reverse video on
14
Reverse video off
15
Inquire current alpha cursor address
16
Inquire tablet status
17
Hard copy
18
Place graphic cursor
19
Remove last graphic cursor
* 20
Form advance
*21
Output window
*22
Clear display list
*23
Output bit image file
*60
Select palette
*91
Inquire palette film types
*92
Inquire palette driver state
*93
Set palette driver state
*94
Save palette driver state
*95 Suppresspalettemessages
*96
Palette error inquire
*98
Update metafile extents
* 99
Write metafile item
*100 Change GEM VDI filename
*Not implemented on the Atari ST
E.6
) Use virtual
) workstation
Printer
Metafile
Screen
Plotter
Pg. #
X
X
X
X
4.5
X
X
X
X
4.9
X
X
X
X
4.9
X
X
X
X
4.9
X
X
X
X
4.27
X
X
4.27
X
X
4.27
X
4.27
X
4.27
X
4.27
X
4.27
X
4.27
X
4.28
X
4.28
X
4.28
X
4.28
X
4.28
X
4.28
X
4.28
X
4.29
X
4.29
X
4.29
X
4.29
X
X
4.30
X
X
4.30
X
X
4.30
X
X
4.30
X
4.30
vx
4.31
X
4.31
X
4.31
X
4.31
X
4.31
X
4.32
X
4.32
X
4.32
X
4.32

<!-- source-page: 261 -->
## Page 261

Callable Functions
GEM VDI functions
cont.
Op
Definition
Printer
Metafile
code
Screen
Plotter
Pg.#
6
Polyline
X
X
X
X
4.10
7
Polymarker
X
X
X
X
8
Text
X
X
X
X
9
Filled area
X
X
X
X
10
Cell array
X
X
X
X
11
Escape code
Generalized drawing primitives (GDP)
1
Bar
X
X
X
X
4.11
2
Arc
X
X
X
X
3
Pie
X
X
X
X
4
Circle
X
X
X
X
5
Ellipse
X
X
X
X
6
Elliptical arc
X
X
X
X
7
Elliptical pie
X
X
X
X
4.12
8
Rounded rectangle
X
X
X
X
9
Filled rounded rectangle
X
X
X
X
10
Justified graphics text
Set character height absolute mode
X
X
X
X
12
X
X
X
X
4.14
13
Set character baseline vector
X
X
14
Setcolourrepresentation
Set polyline linetype
X
X
4.13
15
X
X
X
X
16
Set polyline line width
X
X
17
Set polyline colour index
X
X
X
X
18
Set polymaker type
X
X
X
X
4.14
19
Set polymarker height
X
X
20
Set polymarker colour index
X
X
X
X
21
Set text face
X
X
X
X
22
Set text colour index
X
X
X
X
23
Set fill interior style
X
X
X
X
4.15
24
Set fill style index
X
X
X
X
4.15
25
Set fill colour index
X
X
X
X
4.15
26
Inquire colour representation
X
X
X
4.23
27
Inquire cell array
X
X
4.25
*28
Input locator
X
X
4.20
*29
Input valuator, request/sample
X
X
4.20
*30
Input choice, request/sample
X
X
4.21
*31
Input string
X
X
4.21
32
Set writing mode
X
X
X
4.13
*33
Set input mode
X
X
4.20
' Not implemented on the Atari ST
E.7

<!-- source-page: 262 -->
## Page 262

The Concise Atari ST Reference Guide
GEM VDI functions
cont.
Op
Definition
. Printer
Metafile
code
Screen
Plotter
Pg.#
35
Inquire current polyline attributes
36
Inquire current polymarker attributes
37
Inquire current fill area attributes
38
Inquire current graphic text attributes
39
Set graphic text alignment
100
Openvirtualscreen workstation
101
Close virtual screen workstation
102
Extended inquire function
103
Contour fill
104
Set fill perimeter visibility
105
Inquire pixel
106
Set grapn text special effects
107
Set character cell height, points mode
108
Set polyline and styles
109
Copy raster, opaque
110
Transform form
111
Set mouse form
112
Set user-defined fill pattern
113
Set user-defined linestyle
114
Fill rectangle
115
Inquire input mode
116
Inquire text extent
117
Inquire character cell width
118
Exchange timer interrupt vector
119
Load fonts
120
Unload fonts
121
Copy raster, transparent
122
Show cursor
123
Hide cursor
124
Sample mouse button state
125
Exchange button change vector
126
Exchange mouse movement vector
127
Exchange cursor change vector
128
Sample keyboard state information
129
Set dipping rectangle
130
Inquire facename and index
131
Inquire current face information
The standard range of VDI function output devices include a camera and a
tablet as well as the screen, printer, plotter and metafile; Only the screen is
implemented in the Atari ST.
E.8
X
X
X
X
4.23
X
X
X
X
4.23
X
X
X
X
4.23
X
X
X
X
4.24
X
X
X
X
4.15
X
4.9
X
4.9
X
X
X
X
X
4.22
4.10
X
X
X
X
4.15
4.17
X
X
X
4.15
X
X
X
X
4.14
X
X
X
X
4.13
X
4.17
X
4.17
X
4.18
X
X
X
4.15
X
X
4.13
X
X
4.10
X
4.25
X
X
X
4.24
X
X
X
X
4.24
X
4.18
X
4.9
X
4.9
X
4.17
X
4.18
X
4.18
X
X
4.18
X
4.18
X
4.19
X
4.19
X
4.19
X
X
X
4.9
X
X
X
4.24
X
X
X
X
4.25

<!-- source-page: 263 -->
## Page 263

Callable Functions
GEM AES function calls
Op# Description
Pg*
Application library routines
10
Initialise application
APPL INIT
5.6
11
Read message from pipe
APPL READ
5.6
12
Write message to pipe
APPL WRITE
5.6
13
14
Find another application
Playback GEM recording
APPL FIND
APPL TPLAY
5.6
5.7
15
Record GEM session
APPL TRECORD
5.7
19
Cleanup and exit
APPL EXIT
5.7
Timer event routines
20
Waiting for keyboard input EVNT KEY
5.8
21
Waiting for button input
EVNT BUTTON
5.8
22
Waiting for mouse input
EVNT MOUSE
5.8
23
Waiting for message input
EVNT MESAG
5.9
24
Waiting period
Waiting for multi-events
EVNT TIMER
5.9
25
EVNT MULTI
5.10
26
Get/set mouse clickrate
EVNT DCLICK
5.10
Menu library routines
30
Toggle applicatn menu bar
MENU BAR
5.12
31
Toggle menu check mark
MENU ICHECK
5.12
32
Toggle menu item able
MENU IENABLE
5.12
33
Toggle display video
MENU TNORMAL
5.12
34
Change item menu text
MENU TEXT
5.12
35
Put accessry's menu in desk MENU REGISTER
5.12
Object library routines
40
Add object to tree
OBJC ADD
5.18
41
Delete object from tree
OBJC DELETE
5.18
42
Draw an object or tree
OBJC DRAW
5.18
43
Find object under mouse
OBJC FIND
5.18
44
Compute object offset
OBJC OFFSET
5.18
45
Change object tree order
Edit objects text
OBJC ORDER
5.19
46
OBJC EDIT
5.19
47
Change objects state
OBJC CHANGE
5.19
E.9

<!-- source-page: 264 -->
## Page 264

The Concise Atari ST Reference Guide
GEM AES function calls
cont.
Op# Description
Form library routines
Pg#
50
Monitor user/form
FORM DO
5.20
51
Toggle dialog boxes
FORM DIAL
5.20
52
Display alert box
FORM ALERT
5.20
53
Display error box
FORM ERROR
5.20
54
Centre dialog box
FORM CENTER
5.20
Graphics library routines
70
Draw a rubber box
GRAF RUBBERBOX
5.24
71
Drag a box around
GRAF DRAGBOX
5.24
72
Draw movingbox
Draw expanding outline
GRAF MOVEBOX
5.24
73
GRAF GROWBOX
5.25
74
Draw shrinking outline
GRAF SHRINKBOX
5.25
75
Test for mouse inside
GRAF WATCHBOX
5.25
76
Slide box in parent
GRAF SLIDEBOX
5.25
77
Return screen handle
GRAF HANDLE
5.26
78
Redefine mouse form
GRAF MOUSE
5.26
79
Return mouse attributes
GRAF MKSTATE
5.26
Scrap library routines
80
Read clipboard directory
SCRP READ
5.27
81
Write directory to clipboard SCRP_WRITE
5.27
File selector routines
90
Display file selector box
Window library routines
100
Allocate full window
101
Open window to size
102
Close window
103
Deallocate window
104
Get window data
105
Set window data
106
Find mouse window
107
Update window
108
Calculate window data
E.10
FSEL INPUT
5.28
WIND CREATE
5.29
WIND OPEN
5.29
WIND CLOSE
5.29
WIND DELETE
5.29
WIND GET
5.30
WIND SET
5.30
WIND FIND
5.32
WIND UPDATE
5.32
WIND CALC
5.32

<!-- source-page: 265 -->
## Page 265

Callable Functions
GEM AES function calls
cont.
Op# Description
Pg #
Resource library routines
no
Load resource file
RSRC LOAD
5.35
in
Deallocate resource file
RSRC FREE
5.35
112
Get structure address
RSRC GADDR
5.35
113
Save structure index
RSRC SADDR
5.35
114
Convert charaters to pixels
RSRC OBFIX
5.35
Shell library routines
120
Find how created
SHEL READ
5.37
121
Exit AES or run other
SHEL WRITE
5.37
122
Get data
SHEL GET
5.37
123
Put data
SHEL PUT
5.37
124
Find filename path
SHEL FIND
5.37
125
Find parameter address
SHEL ENVRN
5.37
E.11

<!-- source-page: 266 -->
## Page 266

The Concise Atari ST Reference Guide
Intelligent keyboard (ikbd) command set
Code
Command
Function
Dec
Hex
Pg.#
128
80
Reset
Return keyboard to power-up status
6.3
1
01
without affecting the clock.
A break of 200ms also causes a reset
7
07
Set mouse button action
6.3
8
08
Set mouse relative position reporting
6.3
9
09
Set mouse absolute positioning
6.3
10
0A
Set mouse keycode mode
6.3
11
0B
Set mouse threshold
6.3
12
OC
Set mouse scale
6.3
13
0D
Interrogate mouse position
6.3
14
0E
Load mouse position
6.4
15
OF
Set Y = 0 at bottom
6.4
16
10
Set Y = 0 at top
6.4
17
11
Resume
6.4
18
12
Disable mouse
6.4
19
13
Pauseoutput
Set joystick event reporting
6.4
20
14
6.4
21
15
Set joystick interrogation mode
6.4
22
16
Joystick interrogation
6.4
23
17
Set joystick monitoring
6.4
24
18
Set fire button monitoring
6.4
25
19
Set joystick keycode mode
6.5
26
1A
Disable joysticks
6.5
27
IB
Set time of day clock
6.5
28
1C
Interrogate time of day clock
6.5
32
20
Memory load
6.5
33
21
Memory read
6.6
34
22
Controller execute
6.6
OR 80
Status inquiries
(OR 80H with command)
6.6
The status of the keyboard can be determined by interrogating the status
register in the configuration tables.
E.12

<!-- source-page: 267 -->
## Page 267

Callable Functions
Line-A routines
Dec
Hex
Line-A function
Pg.#
20480
A000
Initialization
7.3
20481
A001
Put pixel
7.3
20482
A002
Get pixel
7.3
20483
A003
Line
7.3
20484
A004
Horizontal line
7.3
20485
A005
Filled rectangle
7.4
20486
20487
A006
A007
Line_by_line filled polygon
BitBlt(including half tone source patterns)
7.4
7.5
20488
A008
TextBlt (all 16 BitBlt logic operations)
7.5
20489
A009
Show mouse
7.5
20490
A00A
Hide mouse
7.5
20491
A00B
Transform mouse
7.6
20492
AOOC
Undraw sprite
7.6
20493
AOOD
Draw sprite
7.6
20494
AOOE
Copy raster form
7.6
20495
AOOF
Contour fill
7.6
E.13

<!-- source-page: 268 -->
## Page 268

The Concise Atari ST Reference Guide
E.14

<!-- source-page: 269 -->
## Page 269

Parameter Blocks
Appendix F
Parameter blocks
System
System start-up block
Boot sector parameter block
Device drivers
F.2
F.2
Device driver
F.3
Device state block
F.3
Floppy parameter block
Sector buffer block
F.4
F.4
Program parameter blocks
Transient program area block
F.5
Load parameter block
Base page format
F.5
F.5
File header
F.6
Memory parameter block
GEM parameter blocks
VDI
F.6
Parameter block
F.7
Cntrl table
F.7
AES
Parameter block
F.8
Cntrl table
F.8
Global array block
Line-A variables
F.8
Line-A tables
F.9
Undocumented line-A variables
F.ll
Sprite definition block
F.12
Memory form definition block
Header blocks
F.12
Cartridge header block
Application header block
Run flag bits
F.13
F.13
F.13
F.1

<!-- source-page: 270 -->
## Page 270

The Concise Atari ST Reference Guide
System start-up block
0
$00
Reseth
2
$02
Vers
4
$04
Reseth
8
$08
Ostext
12
$0C
Endos
16
$10
Reseth
20
$14
Magic
24
$18
Date
System
Branch to reset handler
OS version number
System reset handler
Base of Operating system
End of OS memory used
Default shell
Verification number or zero
System build date
Pointers
Boot sector parameter block
0
$00
BRA.S
2
$02
OEM's space
8
$08
Vol ser #
11
$0B
BPS
13
$0D
SPCs
14
$0E
RES
16
$10
NFATS
17
$11
NDIRS
19
$13
NSECTS
21
$15
MEDIA
22
$16
SPF
24
$18
SPT
26
$1A
NSIDES
28
$1C
NHID
30
$1E
boot code
511
$1FE last word
512
$200
F.2
Branch to boot code
Reserved for OEMs use
24 bit volume serial number
Number of bytes/sector
Number of sectors/cluster
Number of reserved sectors
Number of file alocation tables
Number of directory entries
Number of sectors on media
Media descriptor - not used
Number of sectors/FAT
Number of sectors/track
Number of sides on media
Number of hidden sectors-not used
Start of code, if any ?
Used for checksum

<!-- source-page: 271 -->
## Page 271

Parameter Blocks
Device drivers
Each device has one driver (Device control block-DCB) that contains entry
points to routines and constants used by the systems to initialize the device's
state during a warm-start. The routines and constants are defined as follows:
Device d river
0
$00
BREAD
Read sector
4
$04
B WRITE
Write sector
8
$08
BINIT
Initialize drive (warm start)
12
$0C
BFORMAT
Format drive
16
$10
BINTR
Vblank call (time-out homing)
20
$14
BRDTRK
Read track
24
$18
BWRTRK
Write track
28
$1C
BXLATE
Logical to physical translate
CSV size allocation
32
$20
BCVSIZ
34
$22
BALVSIZ
ALV size allocation
38
$26
BDEFINFO
Default information block
42
$2A
Device drivers are stored in RAM in a device state block (DSB), the DSB
contains TOS specific data structures (the DPB and DPH) and device specific
information, such as the number of tracks, head seek rate. The DSB is allocated
during a warm-start.
Device state block
0
$00
DDPH
26
$1A
DDPB
42
$2A
DINFOSIZ
44
$2C
DPHYSDEV
46
$2E
DNTRACKS
48
$30
DSPT
50
$32
DNSIDES
52
$34
DSEEKRT
54
$36
Device parameter header
Disk parameter block
DSB size (not incl DDPH)
Device physical number
Number of tracks on device
Number of sectors/track
Number of sides/device
Floppy seek rate
F.3

<!-- source-page: 272 -->
## Page 272

The Concise Atari ST Reference Guide
Floppy parameter block
0
$00
Flock
Floppylockreturn address
Callers return address
4
$04
Cret
8
$08
Dmapn
DMA pointer
12
$0C
Obsolete
16
$10
Devno
Device number
18
$12
Secno
Sector number
20
$14
Trkno
Track number
22
$16
Sidno
Side number
24
$18
Secnt
Sector count
26
$la
Sector buffer block
0
$00
BNEXT
4
$04
BBUF
8
$08
BLRU
12
$0C
BFLAGS
14
$0E
BDEV
16
$10
BTRACK
18
$12
BSIDE
20
$14
BSSECT
22
$16
BESECT
24
$18
BPSECT
26
$1A
BSIZE
F.4
Next buffer or null
Size of buffer (512 bytes)
LRU replacement value
Valid/dirty flags
Device number
Track number
Side number
Start sector number
End sector number
Physical sector number

<!-- source-page: 273 -->
## Page 273

Parameter Blocks
Program parameter blocks
Transient program area block
Low TPA
Basepage
Text
Data
BSS
To maintain maximum
GEM DOS compatibility,
free unused memory and
lower top of stack (4A).
Determine memory
available and allocate it.
Application
user area
Load block
0
4
8
12
16
20
$00
$04
$08
$0C
$10
$14
22
$16
High TPA
Opened program fileaddress
Base address to load program
Program end address +1
Address of Base Page
Default user stack pointer
Loader control flags
0_load at bottom
l_load at top
Base page format block
0
$00
Low TPA
4
$04
Hi TPA
8
$08
Tbase
12
$0C
Tien
16
$10
Dbase
20
$14
Dlen
24
$18
Bbase
28
$1C
Blen
Base address of TPA
End of TPA + 1
Base address of text
Length of text
Base address of initialized data
Length of data
Base address of BSS uninitialized data
Length of BSS uninitialized data
F.5

<!-- source-page: 274 -->
## Page 274

The Concise Atari ST Reference Guide
Atari OS specific base page
32
$20
Length free memory after BSS
36
$24
Drive from which program loaded
Reserved by BDOS
37
$25
56
$38
Second parsed FCB
\ Command
\Set
92
$5C
First parsed FCB
/
line
1by
128
$80
Command tail and default
DMA buffer
/OS
$FF
end
GEMDOS specific base page
32
$20
DTA address pointer
36
$24
Parents Base Page pointer
40
$28
Reserved
44
$2C
Environ
Environment string pointer
128
$80
Cmdline
Command line image
File header
/
601AH data & BSS contiguous
0
$00
BRA.Sflag
\
else 601BH
2
$02
Bytes in text segment
6
$06
Bytes in data segment
10
$0A
Bytes in BSS
14
$0E
Bytes in symbol table
18
$12
Zero (reserved)
22
$16
Start of text segment & program execution
26
$1A
Zero if no relocation bits
File header extension
(If BSS and data not contiguous:- Not supported by Atari OS)
28
$1C
Start address of data segment
32
$20
Start address of BSS
36
$24
Memory parameter block
0
$00
Owner description
\
# bytes in block
I Memory
Start address of block
I descriptor
Next link MD
/
Roving pointer
Memory allocation list
Memory free list
F.6

<!-- source-page: 275 -->
## Page 275

Parameter Blocks
GEM parameter blocks
VDI parameter block
0
4
8
12
16
20
$00
contrl
$04
intin
$08
ptsin
$0C
intout
$10
ptsout
$14
VDI control table
0
$00
Op code
2
$02
L ptsin
4
$04
Ljptsout
6
$06
W
intin
8
$08
W
intout
10
$0A
12
$0C
14
$0E
Longword addresses
Control table pointer
I/P attribute table pointer
I/P points table pointer
O/P attribute table pointer
O/P points table pointer
Function op code
I/P coordinate
\
Size in
\
O/P coordinate / longwords
I
I/P attribute
\ Size in
I
O/P attribute
/ words
/
Subfunction identification number
Device handle
Op code dependent information
Table
sizes
F.7

<!-- source-page: 276 -->
## Page 276

The Concise Atari ST Reference Guide
AES parameter block
0
$00
cntrl
4
$04
global
8
$08
int in
12
$0C
int out
16
$10
addr in
20
$14
addr out
24
$18
AES control table
Longword addresses
Control table pointer
Global array pointer
I/P attribute table pointer
I/P points table pointer
O/P attribute table pointer
O/P points table pointer
$00
$02
$04
$06
10
$0A
Opcode
Function op code
WJntJn
I/P coordinate
\ Size in
\
Wjntjjut
O/P coordinate
/ words
I Table
L_addrjn
I/P attribute
\
Size in
I sizes
Ljzddrjsut
O/P attribute
/ longwords
/
AES global array
0
$00
version
2
$02
count
4
$04
id
6
$06
private
10
$0A
ptree
14
$0E
reserved
18
$12
reserved
22
$16
reserved
26
$1A
reserved
30
$1E
F.8
GEM AES version identification word
Maximum #concurrent applications allowed
Unique application identifier
Longword user data
Resource address tree pointer
\
I Zero

<!-- source-page: 277 -->
## Page 277

Parameter Blocks
Line-A variables
Line-A parameter table
Function
0
$00
2
$02
4
$04
8
$08
12
$0C
16
$10
20
$14
24
$18
26
$1A
28
$1C
30
$1E
32
$20
34
$22
36
$24
38
$26
40
$28
42
$2A
44
$2C
46
$2E
50
$32
52
$34
$36
54
$38
56
$3A
58
$3C
60
$3E
62
$40
64
$42
66
$44
68
Number ofvideo planes
\ Canproduce special
Number ofbytes/video line /
effects.
Pointer to Cntrl array
Pointer to Intin array
Pointer to Ptsin array
Pointer to Intout array
Pointer to Ptsout array
Bit planeJD
\ current
Bit plane_l
I colour
Bit planeJZ
I value
Bit plane_3
/
-1
VDI line style equivalent
Writing mode
0_replace
l_transparent
2_XORmode
3_inverse transparent
XI coordinate
Yl coordinate
X2 coordinate
Y2 coordinate
Pointer to current fill pattern
Fill pattern mask
Multi-plane fill pattern
0_current fill pattern is single plane
l_current fill pattern is multi-plane
Clipping flag 0_no clipping
Minimum x clipping value
Minimum y clipping value
Maximum x clipping value
Maximum y clipping value
Accumulator for textblt x dda, initialize to 8000H before each call
Textblt scale factor
Scale direction 0 down
F.9

<!-- source-page: 278 -->
## Page 278

The Concise Atari ST Reference Guide
Line-A parameter table
cont.
Function
70
$46
Font status
l_solid, 0_proportional or variable
X coordinate of character in font form
Y coordinate of character in font form (typically 0)
X coordinate of character on screen
Y coordinate of character on screen
Character width
Character height
Pointer to start of font data (font form)
Width of font form
Style bit 0_Thicken, bit l_lighten, bit 2_skew
bit 3_underline (ignored), bit 4_outline
Lighten text mask
Skew text mask
Text thickening additional width
Offset above character baseline for skew
Offset below character baseline for skew
Scaling flag 0_no scaling
Character rotation vector. 0_horizontal 900_vertically down etc.
.Text foregroundcolour
.Special effects buffer pointer
.Scaling buffer offset in above buffer
.Text background colour (RAM VDI only)
Copy raster form type flag (RAM VDI only)
0_opaque type, n-plane source to n-plane destination bitblt
write mode
<>0_transparent type single plane source to n-plane dest
VDI write mode
118
$76
Abort fill routine pointer (Function not available on disk based
versions of TOS)
72
$48
74
$4A
76
$4C
78
$4E
80
$50
82
$52
84
$54
88
$58
90
$5A
92
$5C
94
$5E
96
$60
98
$62
100
$64
102
$66
104
$68
106
$6A
108
$6C
112
$70
114
$72
116
$74
F.10

<!-- source-page: 279 -->
## Page 279

Parameter Blocks
Undocumented Line-A variables
The Line-A variables table contains other parameters that may be of use to
the programmer. I refer to these variables as 'undocumented' although Atari do
in fact list the variables in their reference material. These variables may change
although it is unlikely.
Function
-46
$D2
Pixel cell height. (Same as font form's height)
-44
$D4
Maximum number of cells across -1 (X)
-42
$D6
Maximum number of cells high -1 (Y)
-40
$D8
Byte offset next vertical cell. Screen width (byte)*Pixel cell height
-38
$DA
Physical colour index of background color.
-36
$DC
Physical colour index of foreground color.
-34
$DE
Current cursor address
-30
$E2
Byte offset from screen base to top of first cell
-28
$E4
Cursor position: cell x
-26
$E6
Cursor position: cell y
-24
$E8
Cursor flash interval (in frames)
-23
$E9
Cursor countdown timer
-22
$EA
Address of monospace font data. Each cell is 8 pixels wide and
byte aligned. The data format is defined in the VDIchapter.
The cells may be arbitrarily high.
-18
$EE
Last ascii code in font
-16
$F0
First ascii code in font
-14
$F2
Width of font form in bytes
-12
$F4
Maximum x pixel value
-10
$F6
Address of font offsettable (per VDI spec)
-6
$FA
Alpha text status byte
bit 0 cursor flash 0:disabled Lenabled
bit 1 flash state 0:off l:on
bit 2 cursor visibility Odnvisible Lvisible
bit 3 end of line 0:overwrite l:wrap
bit 4 reverse video 0:on l:off
bit 5 cursor position saved 0:false l:true
-04
$FC
Maximum y pixel value of the screen
F.11

<!-- source-page: 280 -->
## Page 280

The Concise Atari ST Reference Guide
Sprite definition block
0
$00
2
$02
4
$04
6
$06
8
$08
10
$0A
12
$0C
74
$4A
76
$4C
Format flag
X offset of hot-spot
Y offset of hot-spot
Format flag
Background
\ Colour
Foreground
/ table index
Interleaved
\ Background line 0
background/foreground
I Foreground line 0
image of 32 words
I
/ Foreground line 16
+ve
-ve
Colour
plotted
Fg
Bg
Fg
Bg
0
0
0
1
1
1
1
0
0
0
0
1
1
1
1
0
Transparent
Background
Foreground
Foreground
XOR screen
Memory form definition block (MFDB)
0
$00
Memory pointer
32-bit address of pixel 0,0
4
$04
Width
\ Raster area
8
$08
Height
/ dimensions
12
$0C
Word width
Pixel width/word size
16
$10
Format flag
l=standard, 0=device specific
20
$14
Memoryplanes
Number of planes in raster area
24
$18
\ Three
28
$1C
1 reserved
32
$20
/ words
36
$24
F.12

<!-- source-page: 281 -->
## Page 281

Parameter Blocks
Header blocks
Cartridge header block
Prefix to application header
252
$FC
Flag
#$ABCDEF42 program/data
or
#$FA52255Fdiagnostic
Application header block
0
$00
Next
Link to next application
4
$04
Flog/
Pointer to initialize code
init
or run flag (MSB)
8
$08
Run
Pointer to run code
12
$0C
Time
DOS-format
\
Time/date
14
$0E
Date
DOS-format
/ application created
16
$10
Size
Application size
20
$14
Name
Application name (NNNNNNNN.EEE)
Run flag bit set:
0,
Run before interrupt vectors and memory initialized
1,
Run before GEMDOS initialized
2,
unused
3,
Run before disk boot
4,
unused
5,
Application is a desk accessory
6,
Not a GEM application. No AES calls
7,
Requires command line parameters before execution
F.13

<!-- source-page: 282 -->
## Page 282

The Concise Atari ST Reference Guide
F.14

<!-- source-page: 283 -->
## Page 283

MC 68000 Instruction Summary
Appendix G
MC68000 instruction summary
Instruction summary
G.2
ABCD to ADD
G.2
ADDA to ANDX
G.3
AND to ANDI to SR
G.4
ASL to Bcc
G.5
BCHG to BTST
G.6
CHK to CMPI
G.7
CMPM to DBcc
G.8
DBT to DIVU
G.9
EOR to ILLEGAL
G.10
JMP to LINK
G.ll
LSL to MOVE to CCR
G.12
MOVE to SR to MOVEM
G.13
MOVEP to NEG
G.14
NEGX to ORI to SR
G.15
PEA to SR to ROXL
G.16
ROXR to SBCD
G.17
Sec to SUBQ
G.18
SUBX to TRAPV
G.19
TST to UNLK
G.20
Address Mode BASICequivalents
G.21
Allowable address mode types
G.22
Data storage
G.23
Data types
G.24
Byte, word and longword
G.24
BCD and BIT data types
G.24
Internal registers
G.25
Data registers
G.25
Address registers
G.25
Stack pointer
G.26
Program counter
G.26
Status register
G.26
User byte
G.26
System byte
G.27
Organization of addresses in memory
G.27
G.1

<!-- source-page: 284 -->
## Page 284

The Concise Atari ST Reference Guide
INSTRUCTION SUMMARY
Each Motorola MC68000 instruction is presented, many in terms of
equivalent BASIC Instructions or
assembler routines.
The
similes
are
for
clarification of the use of each instruction; there is no access to the data or address
registers (Dn or An respectively) or the condition codes from BASIC and
therefore the examples which make use of these registers, and most of the
effective address modes (ea), cannotbe takenliterally.
Instructions
ABCD: Add Binary Coded Decimal with Extend. Add two byte-sized binary
coded decimal numbers and the Extend bit; a dollar sign is used to indicate a
BCD number. Clear the extend bit and set the zero bit before performing this
instruction which is limited to byte-size data register operations; multibyte
additions are performed more easilyin memory.
BCD addition
DATA Register
Memory
Addition
MultibyteAddition
Byteonly
MOVE #4,CCR
$7
$27
ABCD -(A0),-(A1)
ABCD $_6
ABCD $16
ABCD D0,D1
ABCD -(A0),-(A1)
$13
$43
ABCD-(A0),-(A1)
Note that the z-flag is cleared if the result is non-zero, otherwise it is
unchanged and that in memory additions the data must be stored with the most
significantdigit lower in memory and the address pointers initiallyset to the byte
abovethe low order BCD digit in memory, as the only available addressingmode
is predecrement.
ADD: Add two integers, one of the integers must be the contents of a data
register.
LET Dn = Dn + ea
ADD ea,Dn
LET ea = ea + Dn
ADD Dn,ea
Use ADD ea,Dn where the destination is a data register.
Use ADDA where the destination is an address register.
Use ADDI or ADDQ where the source is immediate data.
G.2

<!-- source-page: 285 -->
## Page 285

MC 68000 Instruction Summary
ADDA: Add the contents of the effective address to the contents of the
destination address register.
LET An = An + ea
ADDA ea,An
ADDI: Add a constant value to the contents of the destination effective
address. Use ADDQ for speed and small integers.
LET ea = ea + 999
ADDI #999,ea
ADDQ: Add a constant in the range of 1 to 8 to the contents of the effective
address. Faster addition than ADDI.
LET ea = ea + 8
ADDQ #8,ea
ADDX: Add either register to register, or predecremented memory to
memory, with extend. Use of the extend bit enables multiprecision arithmetic to
be performed, the extend bit acting as a carry between successive operations.
Dataregister addition
Memory additions
Add two64 bitintegers
ADDX -(Ay),-(Ax)
DOjDl andD2_D3 Lo-Hi resply
Wliere X infers the Extend bit
ADD.L D0,D2 Low bits
LET Ay = Ay - 4
ADDX.LD1,D3 High bits
LET Ax = Ax - 4
POKE(Ax), PEEK(Ax) +
Memory addition
PEEK(Ay) + X
MOVE #4,CCR
ADDX.L -(A0),-(A1)
ADDX.L -(A0),-(A1) etc.
Note that the z-flag is cleared if the result is non-zero, otherwise it is
unchanged. For memory additions first clear the Extend bit and set the Zero flag.
The data must be stored with the most significant digit lower in memory and the
address pointers initially set the operand size above the low order digit in as the
only addressing mode is predecrement.
G.3

<!-- source-page: 286 -->
## Page 286

The Concise Atari ST Reference Guide
AND: AND the source operand to the destination operand. The source AND
data is normally used either (a) as a mask enabling a portion of the destination
operand to be examined (bits are masked by l's in the source); or (b) to clear bits
by setting the corresponding bit in the source to a zero.
LET ea = Dn && ea
AND Dn,ea
LET Dn = src && Dn
AND ea,Dn
If src = 3, then AND src keeps bits 0 and 1 in Dn only, the others are set to
zero.
Use AND ea,Dn where the destination is a data register.
Use ANDA where the destination is an address register.
Use ANDI where the source is immediate data.
ANDI: ANDI the immediate data to the destination effective address.
LET ea = data && ea
ANDI.W #512,D0
Keep bit9 ofword only
ANDI to CCR: ANDI the data to the condition code register.
LET CCR = 26 && CCR
ANDI #26,CCR
Normally bits can be tested via the condition codes without using the AND
function as a mask. Here it is used to zero a bit position where there is a zero in
the AND data; that is zero and carry (bits 0 and 2 in the CCR) are cleared.
ANDI to SR: ANDI the data to the status register is a privileged instruction
and attempted access while in user mode will trap to the privilege violation
exception vector.
LET SR = 63743 &&SR
ANDI #63743,SR
Set the interrupt mask level to zero and leave unchanged the condition code
and system flags.
G.4

<!-- source-page: 287 -->
## Page 287

MC 68000 Instruction Summary
ASL: Arithmetically Shift Left the bits of the operand. The last MSB shifted
sets the carry and extend bits; the LSB is set to zero each shift. The overflow bit is
set if the sign is changed during the shift and is used to flag a change of sign. The
instruction is used for fast multiplication of *2 and *4; other values should use
MULS
MSB
LSB
-
0
xra
LET ea = ea * 2
LETDy = Dy *(2ADx)
LET Dy = Dy *(2A5)
The carry bitis cleared if the shift count is zero.
ASL ea (shift 1)
ASL Dx,Dy (reg modulo 64)
ASL #5,Dy (shift 1 to 8)
ASR: Arithmetically Shift Right the bits of the operand. The MSB sign bit is
retained; the last LSB shifted is used to set the carry and extend bits. This
instruction can be used for rapid integer division by 2, 4, 8 of signed numbers;
use DIVS for other divisions.
. . _ _
. _ _
MSB
LSB
Sign
bit
t
LET ea = INT(ea/2)
LET Dy = INT(Dy/(2ADx)
LET Dy = INT(Dy/(2A5)
The carry bitis cleared if the shift count iszero.
Bcc: Branch on condition a two's complement displacement from the current
program counter position (Instruction address + 2) +126 to -128 for a short branch
or +32766 to -32768 for a word branch operation, the condition cc may be:
XTO
ASR ea (shift 1)
ASR Dx,Dy (reg modulo 64)
ASR #5,Dy (shift 1 to 8)
Conditions
Two's complement
arithmetic
EQ
Equal To
CS
Carry Set
GT
Greater Than
NE
Not Equal
CC
Carry Clear
LT
Less Than
MI
Minus
VS
Overflow
GE
Greater Than
PL
Plus
VC
No Overflow
or Equal to
HI
Higher Than
LE
Less Than or
LS
Lower Than or same
Equal to
IF Dn = 0 THEN GOTO yy
BEQ #14
IF Dn 0 THEN GOTO label
BGT label
G.5

<!-- source-page: 288 -->
## Page 288

The Concise Atari ST Reference Guide
BCHG: A bit is tested and its state reversed. If the bit was zero before the test;
that is clear, then the Zero flag is set, otherwise it is cleared.
IF BITn = 0 THEN set_Zflag:
ELSE clear_Zflag
BCHG #6,ea (data modulo 8)
LET BITn = 1 - BITn
BCHG Dn,ea (reg modulo 32)
BCLR: A bit is tested and then cleared. If the bit was zero before the test; that
is clear, then the Zero flag is set, otherwise it is cleared.
IF BITn = 0 THEN set_Zflag:
ELSEclear_Zflag
BCLR #6,ea (data modulo 8)
LET BITn = 0
BCLRDn,ea (reg modulo 32)
BRA: BRanch Always, a two's complement displacement branch either of
+126 to -128 bytes by a single word instruction or of +32766 to -32768bytes by a
two-word instruction from the current program counter position (instruction
address + 2).
GOTO label
BRA label
GOTO 1275
BRA #8
BSET: A bit is tested and then set. If the bit was zero before the test; that is
clear, then the Zero flag is set, otherwise it is cleared.
IF BITn = 0 THEN set_Zflag:
ELSE clear_Zflag
BSET #6,ea (data modulo 8)
LETBITn= 1 BSET
Dn,ea (reg modulo 32)
BSR: Branch to SubRoutine, either a two's complement displacement of +126
to -128 bytes by a single-word instruction, or of +32766 to -32768 bytes by a
two-word instruction, from the current program counter position (instruction
address +2). Return to the next instruction via an RTS from the subroutine.
GOSUB label
BSR label
GOSUB 1275
BSR #8
BTST: A bit is tested. If the bit was zero; that is clear, then the Zero flag is set,
otherwise the Zero flag is cleared.
IFBITn = 0 THEN set_Zflag:
BTST #6,ea (data modulo 8)
ELSE clear_Zflag
BTST Dn,ea (reg modulo 32)
G.6

<!-- source-page: 289 -->
## Page 289

MC 68000 Instruction Summary
CHK: Check a data register low-order word against the two's complement
upper bound of the source operand. If the register value is less than zero or
greater than the test value, then jump to the CHK Trap exception vector.
IFDn> eaOR
CHK ea,Dn
Dn < 0 THEN GOSUB chk_trap
CLR: Clear an operand sets all or part of a specified address or register to
zero.
LET ea = 0
CLR ea
MOVEQ #0,Dn is quicker than CLR.L Dn
SUBA.L An,An is quicker for memory applications
CMP: The compare instructions are used exclusively to set the condition code
registers for a subsequent conditional operation. The comparison is made by
subtracting the source operand from the destination operand and setting the
conditioncodesaccordingly; neitheroperand is altered by the instruction.
CMP ea,Dn
IF ea = Dn THEN GOTOloop
BEQ loop
UseCMPA when the destinationis an address register.
Use CMPI when the source is immediate data.
UseCMPMfor memory to memory comparisons.
CMPA: Subtract the source operand from the address register and set the
condition code flags accordingly. The comparison is based on a sign-extended
source if it is a word operand. The address register is not altered.
CMPA ea,Dn
CMPI: Subtract the immediate operand from the effective address operand
and set the condition code flags accordingly; neither operand is altered. Use TST
for comparingwith zero as it is much quicker.
CMPI #999,ea
G.7

<!-- source-page: 290 -->
## Page 290

The Concise Atari ST Reference Guide
CMPM: Subtract the contents of the memory address pointed to by the
source address register from the contents of the memory address pointed to by
the destination register and set the condition code flags accordingly. Increase the
value of both address registers by the size of the operand (1,2 or 4 byte word and
longword respectively).
The main use for this instruction is comparing strings
LETDn = length_string -1
loop
loop
IF PEEK (Ay) <> PEEK (Ax) THEN
Ay = Ay + s : Ax = Ax + s
GOTO not_same
same
ELSE
Ay = Ay + s : Ax = Ax + s
LET Dn = Dn -1
IF Dn = -1 THEN GOTO loop
same
not same
CMPM (Ay)+,(Ax)+
BNE not_same
DBRA Dn,loop
not same
Dn is the character count, s=operand size
DBcc: Test the condition and exit loop to the next instruction if the condition
is met. If the condition is not met, then decrement the low order 16 bits of the
count data register. If the count becomes -1, then exit loop and carry on with the
next instruction, otherwise branch the two's complement displacement of the
following word -32766 to +32768 from the current program counter position
(instruction address +2). The test may be one of the following:
Conditions
Two'scomplement
arithmetic
EQ
Equal To
CS
Carry Set
GT
Greater Than
NE
Not Equal
CC
Carry Clear
LT
Less Than
MI
Minus
VS
Overflow
GE
Greater Than
PL
Plus
VC
No Overflow
or Equal to
HI
Higher Than
LE
Less Than or
LS
Lower Than or same
Equal to
G.8
DBEQ D0,loop
(Equivalent)
BEQ pass
SUB #1,D0
BPL loop
pass

<!-- source-page: 291 -->
## Page 291

MC 68000 Instruction Summary
DBT: Always branches and is of little use.
DBRA: Sometimes written DBF, it makes the branch based on the data
register count only and branches when the count reaches -1. Therefore the count
should be initialised to the required count -1. If the loop is entered via a jump or
branch at the DBcc instruction, then the count is the required count and usefully
an initial zero count will cause an immediate exit from the loop.
DIVS: Sign Divide a 32-bit data register destination operand by a 16 bit
source operand and store the integer result in the lower 16 bits of the destination
register, the remainder is stored in the upper 16 bits of the destination and keeps
the dividend sign. Division by zero causes a jump to the Divide-by-Zero Trap
exception vector. On overflow, the result is larger than 16 bits, the V-flag is set
and the operation terminated without affecting either operand.
LET Dn = Dn / ea
DIVS ea,Dn
ASR ea is a fast signed divide by two
MOVEQ #2,D2
ASR D2,Dx is a quicker divide by four
Generally use DIVS and DIVU for division by a prime number, otherwise
think of an alternative as the division instruction, because of its general nature, is
not quick.
DIVU: Unsigned arithmetic divide of a 32-bit data register destination
operand by a 16-bit source operand. The integer result is stored in the lower 16
bits of the destination register and the remainder in the upper 16 bits. Division by
zero causes a jump to the Divide-By-Zero exception vector. On overflow the
result is larger than 16 bits, the V-flag is set and the operation terminated without
affecting either operand.
LET Dn = Dn / ea
DIVU ea,Dn
G.9

<!-- source-page: 292 -->
## Page 292

The Concise Atari ST Reference Guide
EOR: EOR the data register source operand to the contents of the destination
operand. The source EORdata is normally used to invert the state of a bit or bits.
LET ea = Dn AA ea
EOR Dn,ea
If Dn=3, then bits 0 and 1 in the effective address are inverted.
Use EORI where the source is immediate data.
There is no memory to data register operation.
EORI: EORI the immediate data to the destination effective address.
LET ea = data AA ea
EORI.B #16,D0
Invert bit4 of DO
EORI to CCR:EORI the immediate data to the condition code register.
LET CCR = 4 AA CCR
EORI #4,CCR
Toggle the Zerojlag
EORI to SR: EORI the immediate data to the status register. This is a
privileged instruction and attempted access while in user mode will cause a trap
to the privilege violation exception vector.
LET SR = 8192 AA SR
EORI #8192,SR
Togglethesupervisorbit
EXG: Exchange the longword contents of two registers. Referred to in many
BASICS as SWAP, which has a different meaning in the MC68000 instruction
code.
LET tmp=D0 : D0=D1 : Dl=tmp
EXG D0,D1
LET tmp=A0 : A0=A1 : Al=tmp
EXG A0,A1
LET tmp=D0 : D0=A0 :A0=tmp
EXG D0,A0
EXT: Sign-extend a data register contents, a byte to a word or a word to a
longword, to permit operations involvingmixed sizedata to take place.
EXTDn
ILLEGAL: The illegal instruction causes the processor to jump to the illegal
instruction trap exception process subroutine.
GOSUB Ill_Trap
ILLEGAL
G.10

<!-- source-page: 293 -->
## Page 293

MC 68000 Instruction Summary
]MPJSR: JMP and JSRare long forms of BRA and BSR, the main difference
being the jump instruction's ability to access any part of memory whereas the
branch instructions are limited to a relative +/-32K bytes jump.
JMP: Jump to a routine in memory specified by the effective address, either
absolute or relative to the current program counter position.
GOTO ea
JMP ea
JSR: Jump to a subroutine in memory specified by the effective address,
either absolute or relative to the current program counter position
GOSUB ea
JSR ea
LEA: Load Effective Address loads a calculated effective address into an
address register. The calculated address can be the sum of two registers, one
must be an address register, and a displacement which provides the addition of
two registers and a displacement without affecting either register, in a single
instruction.
LET An = Start_of_text_address
LEA text,An
LET An = Start_of_table
LEA tabl,An
LET AO = Al + D2 +64
LEA 64(Al .D2),A0
LINK: LINK enables a block of memory, part of the stack, to be temporarily
reserved for a specific purpose; that is an index table, a text string, an array etc.
and the space recovered when the requirement has passed.
DIM A(64)
LINK An,#-64
Saves a block of 64 bytes in memory. The original value of An is preserved on
the stack and will be recovered on UNLK. The current value of An is the start of
the data space which may be most easily accessed via indirect with displacement
or indirect with index addressing modes.
G.11

<!-- source-page: 294 -->
## Page 294

The Concise Atari ST Reference Guide
LSL: Logically Shift Left the bits of the operand. The MSB sets the carry and
extend bits, the LSB is set to zero.
The carry bit is cleared if
MSB
LSB
theshift count iszero.
IX/CI'
LET ea = ea * 2
LSL ea (shift 1)
LET Dy = Dy *(2ADx)
LSL Dx,Dy(reg modulo 64)
LETDy = Dy *(2A5)
LSL #5,Dy (shift 1 to 8)
LSR: LogicallyShift Right the bits of the operand. The MSB is set to zero and
the LSB sets the carry and extend bits.
iv/iod
I OD
The carry bit is clearedif
MOD
LOP
the shift count is zero
0
X70
LET ea = INT(ea/2)
LSR ea (shift 1)
LETDy = INT(Dy/(2ADx)
LSR Dx,Dy (reg modulo 64)
LETDy = INT(Dy/(2A5)
LSR #5,Dy (shift 1 to 8)
MOVE: Move the byte, word or longword contents of the source effective
address to the destination effective address.
MOVE ea,ea
LET Dl = DO
MOVE D0,D1
LET SP = SP-4 : POKE(SP),D7
MOVE D7,-(SP)
POKE(SP),D7 : LET SP = SP+4
MOVE (SP)+,D7
Use MOVEA where the destination is an address register.
MOVE from SR:Save the word contents of the status register in the effective
address register or memory location. ** Be careful as this instruction is privileged
in the MC68010 and MC68020 instruction sets, programers should try not to use it
in user state.
MOVE SR,ea
LET DO = PEEK_W(SR)
MOVE.W SR,D0
MOVE to CCR: Move the contents of the source operand WORD into the
condition code register. Only the low-order byte is used; the upper byte is
ignored.
MOVE ea,CCR
POKE_W(CCR),4
MOVE #4,CCR
Set the Zero flagandclear all others.
G.12

<!-- source-page: 295 -->
## Page 295

MC 68000 Instruction Summary
MOVE to SR: Move the contents of the source operand into the status
register. This is a privileged instruction and attempted access while in user mode
will cause a trap to the privilege violation exception vector.
MOVE ea,SR
POKE_W(SR),1792
MOVE #1792,SR
Clear allflags, set userstate,andset interrupt mask tolevelseven.
MOVE USP: Move the contents of the user stack pointer to or from the
specified address register. This is a privileged instruction and attempted access
while in user mode will cause a trap to the privilege violation exception vector.
LET A3 = USP
MOVE USP,A3
LET USP = A3
MOVE A3,USP
MOVEA: Move the contents of the source effective address to the destination
address register. Byte-sized operations are not permitted.
LET A3 = PEEK_W(192)
MOVEA.W 192,A3
LET AO = PEEK_L(4)
MOVEA.L 4,A0
MOVEM: Move multiple registers to or from memory which permits the
transfer of a blockof specified registers to and from memoryin a predetermined
sequence by one instruction.
LET A7=A7-4 : POKE_L(A7),D0
MOVEM.L #57344,-(A7)
LET A7=A7-4 : POKE_L(A7),Dl
LET A7=A7-4 : POKE_L(A7),D2
MOVEM.L (A7)+,#1860
Either of these instructions save registers DO, Dl and D2
MOVEM.L # 7,24(A7)
or
MOVEM.L #57344,-(A7)
and to recover the registers DO, Dl and D2either
MOVEM.L 24(A7),#7
or
MOVEM.L (A7)+,#7
** The predecrement mode of addressing values the registers in reverse order
for the register list mask (DO - bit 15, A7 - bit 0), permitting push-on, pull-off on a
last in-first out basis.
G.13

<!-- source-page: 296 -->
## Page 296

The Concise Atari ST Reference Guide
MOVEP: Move data to or from a data register and alternate bytes in memory,
enabling the MC68000 to interface with 8-bit peripheral devices. The data is
transferred on either the high half of the data bus D8-D15, even addresses, or the
low half D0-D7, odd addresses, to memory occupying alternate bytes in the
processor's memory map. The data is transferred in high-low order.
POKE_W(7+65536),Dn
MOVEP Dn,d(Ay)
LETDn = PEEK_W(7+65536)
MOVEP 7(Ay),Dn
This is the ONLY instruction that provides word and longword access at odd
addresses.
MOVEQ: Move sign-extended 32-bit immediate data in the range of +127 to
-128 to a data register. A fast means of loading small positive and negative
integers into a data register.
LET DO = 0
MOVEQ #0,D0
MULS: Multiply two signed 16-bit operands. Only the low-order 16-bits are
used from both operands for the multiplication, the result being the 32-bit
product in the destination data register.
MULS ea,Dn
ASL ea is a fast signed multiply by two.
MULU: Multiply two unsigned 16-bit operands. Only the low- order 16-bits
are used from both operands for the multiplication, the result being the 32-bit
product in the destination data register.
MULU ea,Dn
NBCD: Negate Decimal with Extend subtracts the destination byte-sized
operand and the extend bit from zero using decimal arithmetic.
NBCD ea
Extend bit clear, the ten's complement is produced.
Extend bit set, the one's complement is produced.
NEG: Negate subtracts the destination operand from zero, producing the
two's complement of a byte, word or longword operand.
NEGea
G.14

<!-- source-page: 297 -->
## Page 297

MC 68000 Instruction Summary
NEGX: Negate with extend subtracts the destination operand and the extend
bit from zero, producing the two's complement of a byte, word or longword
operand.
NEGX ea
NOP: No OPeration has no effect other than to increment the program
counter by 2. Its use is generally either for creating a space in code which may be
used later on for adding a subroutine call, for writing text etc. or for deleting
parts of code, especially test routines, without the need for recompiling.
NOP
NOT: Logically complement, producing the one's complement of the
operand.
NOTea
OR: Or the source to the contents of the destination data register. The source
OR data is normally used to set specific bits of an operand.
LET Dn = src I I Dn
OR ea,Dn
If src = 3, then OR src sets bits 0 and 1 in Dn; the other bits are left unchanged.
Use OR ea,Dn where the destination is a data register.
Use ORI where the source is immediate data.
ORI: ORI the immediate data to the destination effective address.
ORI.W #512,D0
LET ea = data I I ea
Setbit9 ofword, others unchanged
ORI to CCR: ORI the data to the condition code register.
LET CCR = 511 CCR
ORI #5,CCR
OR is used to set bit positions; that is Zero and Carry (Bits 0 and 2 in the
CCR) are set, the others are unchanged.
ORI to SR: ORI the data to the status register
LET SR = 1792 I I SR
ORI #1792,SR
Set the status register interrupt mask to level seven, all other conditions
unchanged. Thisis a privileged instruction and attemptedaccess from user mode
will cause a trap to the privilege violation exception process routine.
G.15

<!-- source-page: 298 -->
## Page 298

The Concise Atari ST Reference Guide
PEA: Push effective address pushes a longword-computed address onto the
current stack. It is useful for passing parameters to a subroutine which are
accessed via an address register indirect with displacement instruction, the
parameter maybe removedfromthe stackprior to return if necessary.
Access parameter
Tidy stack
sprog
PEA param
JSRsprog
MOVEA.L 4(SP),A0
MOVE.L (SP)+,(SP)
RTS
RESET: Reset external devices by asserting the reset line. There is no affect on
the processor other than an increase of two in the value of the program counter.
This is a privileged instruction and attempted access while in user mode will
cause a trap to the privilege violation exception vector.
RESET
ROL: ROtate without extend Left. The MSB is rotated to the LSB and the
carry; the other bits are shifted up one. The carry bit is set to the extend bit for a
shift count of zero
ROL ea (shift 1)
ROL Dx,Dy (reg modulo 64)
»4g
ROL #5,Dy (shift 1to 8)
ROR: ROtate without extend Right. The LSB is rotated to the MSB and the
carry; the other bits are shifted down one. The carry bit is set to the extend bit for
a shift count of zero.
CJ
,
•1—•
.
:
MSB
c
F
LSB
ROR ea (shift 1)
ROR Dx,Dy (reg modulo 64)
ROR #5,Dy (shift 1 to 8)
ROXL: ROtate with eXtend Left. The MSB is rotated to the extend bit and the
carry, the extend bit is rotated to the LSB and the other bits are shifted up one.
The carry bit is set to the extend
bit for a shift count of zero.
ROXL ea (shift 1)
ROXL Dx,Dy (reg modulo 64)
MSB
LSB
ROXL #5,Dy (shift 1 to 8)
x/c
G.16

<!-- source-page: 299 -->
## Page 299

MC 68000 Instruction Summary
ROXR: ROtate with eXtend Right. The LSB is rotated to the extend bit and
the carry, the extend bit is rotated to the MSB and the other bits are shifted down
one. The carry bit is set to the extend bit for a shift count of zero.
x/c
ROXR ea (shift 1)
ROXRDx,Dy (reg modulo 64)
MSB
LSB
ROXR #5'°y (shiftl to 8>
RTE: Return from Exception. The status register and the program counter are
pulled from the current (supervisor) stack. This instruction is privileged and
attempted access while in user mode will cause a trap, to the privilege violation
exception vector.
(SP)+,SR
RTE
(SP)+,PC
RTR: Return and Restore. The condition code and then the program counter
are pulled from the current stack.
(SP)+,CCR
RTR
(SP)+,PC
RTS: Return from Subroutine. The program counter is pulled from the
current stack.
(SP)+,PC
RTS
SBCD: Subtract Decimal with Extend. Subtrract a byte-sized binary coded
decimal number and the extend bit from the destination operand byte using
decimal arithmetic and store the result in the destination location.
BCD subtraction
Memory
Multibyte Subtraction
SBCD $ 7
SBCD $27
$_6
$16
MOVE #4,CCR
$ 1
$11
SBCD D0,D1
Note that the z-flag is cleared if the result is non-zero, otherwise it is
unchanged. For memory additions the data must be stored with the most
significant digit lower in memory and the address register pointers initially set to
the byte above the low-order BCD digit. The only memory addressing mode is
predecrement.
G.17

<!-- source-page: 300 -->
## Page 300

The Concise Atari ST Reference Guide
Sec: Set according to condition.The specifiedcondition is tested and the byte
specified set to all ones if true or all zeros if false.The condition may be:
Conditions
Two's complement
arithmetic
EQ
NE
MI
PL
HI
LS
Equal To
Not Equal
Minus
Plus
Higher Than
Lower Than
or same
CS
CC
VS
VC
T
F
Carry Set
Carry Clear
Overflow
No Overflow
True
False
GT
Greater Than
LT
Less Than
GE
Greater Than
or Equal to
LE
Less Than or
Equal to
Sec ea
STOP: Load the status register and Stop. The immediate operand is put into
the status register and the program counter advanced to the next instruction and
then stopped. Execution only resumes when a trace, interrupt or reset exception
occurs.
STOP #7
SUB: Subtract the source from the destination. One of the integers must be
the contents of a data register.
LET Dn = Dn - ea
LET ea = ea - Dn
SUB ea,Dn
SUB Dn,ea
Use SUB ea,Dn where the destination is a data register.
Use SUBA where the destination is an address register.
Use SUBI or SUBQ where the source is immediate data.
SUBA: Subtract the contents of the effective address from the contents of the
destination address register.
LET An = An - ea
SUBA ea,An
SUBI: Subtract a constant value from the contents of the destination effective
address. Use SUBQ for speed and small integers.
LET ea = ea - 999
SUBI #999,ea
SUBQ: Subtract a constant of from 1 to 8 from the contents of the effective
address. Faster subtraction than SUBI.
LET ea = ea
SUBQ #8,ea
G.18

<!-- source-page: 301 -->
## Page 301

MC 68000 Instruction Summary
SUBX: Subtract either register to register, or predecremented memory from
memory, with extend. The extend bit enables multiprecision arithmetic to be
performed, acting as a borrow between successive operations.
Dataregister subtractions
Memory subtractions
Subtract two 64 bitintegers
SUBX-(Ay),-(Ax)
D0_D1 andD2JD3 Lo-Hi resply
where X infers Extend bit
SUB.L D0,D2 Low bits
LET Ay = Ay - 4
SUBX.L D1,D3 High bits
LET Ax = Ax - 4
POKE(Ax),PEEK(Ax) -
Memory subtractions
PEEK(Ay) - X
MOVE #4,CCR
SUBX.L -(A0),-(A1)
SUBX.L -(A0),-(A1)
Note that the z-flag is cleared if the result is non-zero, otherwise it is
unchanged. For memory additions first clear the Extend bit and set the Zero flag.
The data must be stored with the most significant digit lower in memory and the
address pointers initially set the operand size above the low order digit.
Predecrement is the only memory addressing mode.
SWAP: Swap register halves exchanges the high-order word of a data
register with the low-order word. This instruction provides access to the
low-order byte of the high word.
Dn0-15<—>Dn 16-31
TAS: Test and set an operand, compares the operand byte with zero and sets
the condition codes accordingly. If the byte is zero, the Z_flag is set; if the MSB is
non-zero, then the N_flag is set. The MSB of the operand is then set.
TASea
TRAP: Trap. The processor commences execution at the relevant trap
exception vector address.
TRAP#n
TRAPV: Trap on Overflow. The processor commences execution at the trap
on overflow exception vector address.
TRAPV
G.19

<!-- source-page: 302 -->
## Page 302

The Concise Atari ST Reference Guide
TST: Test an operand. The operand is compared with zero and the condition
codes set accordingly.
TSTea
Use in preference to CMPI #0,ea
UNLK: Unlink. The stack pointer is loaded from the specified address
register; the address register is then loaded with the longword pulled from the
top of the stack and the linked space deallocated.
UNLK An
Key
&&
bitwise
AND
AA
bitwise
EOR
I I
bitwise
OR
G.20

<!-- source-page: 303 -->
## Page 303

MC 68000 Instruction Summary
Address mode
Assembler language and BASIC equivalents
Address Mode
Source
Data register
direct
Dn
MOVE.L D2,D0
LET DO = D2
Address register An
direct
Address register (An)
indirect
Address register (An)+
indirect with
postincrement
MOVE.L A0,D0
LET DO = AO
MOVE.L (A0),D0
LET D0,PEEK_L(A0)
MOVE.L (AO)+,D0
LET D0,PEEK_L(A0)
LET AO = AO + 4
Address register
indirect with
predecrement
^An)
MOVE.L -(AO),D0
LET AO = AO - 4
LET D0,PEEK_L(A0)
MOVE.L 9(A0),D0
LET DO = PEEK L(9 + AO)
Destination
MOVE.L #999,D0
LET DO = 999
MOVEA.L #999,A0
LET AO = 999
MOVE.L #999,(A0)
POKE_L (A0),999
MOVE.L #999,(A0)+
POKE_L (A0),999
LET AO = AO + 4
MOVE.L #999,-(A0)
LET AO = AO - 4
POKE_L (A0),999
MOVE.L #999,9(A0)
POKE_L(A0+9),999
Address register d(An)
indirect with displacement
Address register d(An.Ri)
indirect with index
MOVE.L 9(A0.D2),D0
MOVE.L #999,9(A0.D0)
LET D0=PEEK_L(9+A0+D2) POKE_L(A0+9+D0),999
Absolute short
$xxxx
ABS.S
Absolute long
$xxxxxx
ABS.L
Program counter d(PC)
with
displacement
Program counter d(PC.Ri)
with
index
Immediate
#$xxx
Imm
Notes
MOVE.L 1024,D0
LET DO = PEEK_L(1024)
MOVE.L 163840,D0
LET DO=PEEK_L(163840)
MOVE.L #999,1024
POKE_L(1024),999
MOVE.L #999,163840
POKE_L(163840),999
MOVE.L 9(PC),D0
LET D0=9 + Contents of
Program Counter
Not legal
MOVE.L 9(PC.D2),D0
LET D0=9+D2+Contents of
Program Counter
MOVE.L #65536,D0
LET DO = 65536
Register DO is used
for the destination
as an example; any
other valid effective
address may be used.
Not legal
Not legal
The source is defined
as immediate data
value 999; any other
valid effective
address may be used.
All equivalents have been defined as having longword operands, byte and
word-sized operands may also be used.
G.21

<!-- source-page: 304 -->
## Page 304

The Concise Atari ST Reference Guide
Allowable address mode types
Alt
Dat
Alt
Dat
Dat
Con
Con Con
All
Mem
Alt
Add Add Add Add Alt
Add
Add
Add
Mod Mdl Md2 Mdl Add Md2
Srce
Dest
Dest
Dest Srce
Dest
Dest Srce
Dn
X
X
X
X
X
X
An
X
X
(An)
X
X
X
X
X
X
X
X
X
X
(An)+
X
X
X
X
X
X
X
X
-(An)
X
X
X
X
X
X
X
X
d(An)
X
X
X
X
X
X
X
X
X
X
d(An.Ri)
X
X
X
X
X
X
X
X
X
X
ABS shrt
X
X
X
X
X
X
X
X
X
X
ABS long
X
X
X
X
X
X
X
X
X
X
d(PC)
X
X
X
X
X.
d(PC.Ri)
X
X
X
X
X
Imm
X
X
ADD
ADD
ADDI NBCE ADDC )AND BTST JMP
MOVI:m
ADDA AND ANDI NEG
SUBQ CHK
JSR
reg
MOVEM
CMP
OR
BCHG NEGX
DIVS
LEA
to
mem
CMPA SUB
BCLR NOT
DIVU
PEA
mem
to
MOVI
BSET ORI
reg
hiOVEA ASL
CLR
MOVI
SUB
ASR
CMPI Sec
toCCI I
SUBA ROXL EOR
MOVI
ROXK EORI SUBI
toSR
ROL
MOVI iTAS
ROR
TST
MULS
LSL
MOVI
MULt J
LSR
frSR
OR
Alt = Alterable
Mod = Mode
Mdl = Model
Mem = Memory Dat = Data
Md2 = Mode2
Add = Address
Con = Control
G.22
\ Types of addressing mode
I definitions used by Motorola
/ to describe allowable modes.

<!-- source-page: 305 -->
## Page 305

MC 68000 Instruction Summary
Data storage
The MC68000 accesses two internal locations for storage:
Internal
registers,
of
which
there
are
17, store
the
data
inside
the
microprocessor itself. They are very limited in the amount of data they can store,
but provide extremely fast access.
ST RAM/ROM, where data access is still quick, but not as fast as the internal
register data access.
EXTERNAL
DATA
REGISTERS
PROCESSOR
MEMORY
RAM
ADDRESS
REGISTERS
(Random
access memory)
PC
ROM
(READ ONLY
MEMORY)
SR
External data
storage
(Hard/floppy disk)
Atari ST
Internal memory
MC68000 processor
devices
internal register layout
G.23

<!-- source-page: 306 -->
## Page 306

The Concise Atari ST Reference Guide
Data types
The MC68000 microprocessor supports five different data types; some
instructions are limited to a specific data type, but mostly there is an allowable
range with the default of a word. Where choice is not implicit, it is defined in the
instruction word extension as either byte, word or longword.
Byte, Word and Longword data types
Word
|MSB
LSB]
HIGH ORDER BYTE
LOW ORDER BYTE
31
23
15
7
0
Byte
l
DRDERI
Longword-
HI MID ORDER BYTE
LOW BYTE
HIGH BYTE
LO MID ORDER BYTE
^
Lonoword
lsbJ
BCD and BIT data types
G.24
Bit data
MSB
LSB
Byte
|7| 61 5I4I 31 21 1 I 0
BCDO
BCD 1
MOST SIGNIFICANT LEAST SIGNIFICANT
BCD DIGIT
BCD DIGIT

<!-- source-page: 307 -->
## Page 307

MC 68000 Instruction Summary
Internal registers
The Motorola 68000 has seventeen 32-bit registers, a 24-bit program counter
and a 16-bit status register. Eight of the 32-bit registers (DO to D7) are used as
data registers for operations involving single bit, BCD (4-bit), byte (8-bit), word
(16-bit) and longword (32-bit) data. The remaining nine registers are split into
two: seven of them (A0 to A6) act as address registers, and two act as stack
pointers. Only one stack pointer may be accessed at a time, hence the convention
of calling both of them A7. The address register operations are based on words
and longwords only.
Data registers
Data storage of byte, word and longword is always performed in the part of
the data registers shown; unused parts of the register are not altered.
31
16
15
8
7
0
Bvte
Word
I
Lonaword
DO
D1
D2
D3
D4
D5
D6
D7
Eight data
registers
Address registers
The address registers are used as pointers to user stacks, as base address
registers and temporary storage for computed addresses that are not to affect the
Status Register. Address storage is always performed in the part of the address
register shown. When used as a destination operand, the entire address is
changed regardless of the operation size. Address registers do not support
byte-sized operations as either source or destination. Words are sign- extended to
longwords before an operation is performed.
Word
Lonqwon
A0
A1
A2
A3
A4
A5
A6
Seven
address
registers
G.25

<!-- source-page: 308 -->
## Page 308

The Concise Atari ST Reference Guide
Stack pointer
The user stack pointer typically saves subroutine returns when in user mode.
The supervisor stack pointer points to a stack that saves the status register
contents during trap and interrupt routines as well as the supervisor subroutine
returns. Only one of the stack pointers is addressable at a time, so they are both
called A7. Bytes pushed onto a stack are stored in the high order half of the word.
31
User stack pointer
Supervisor stack pointer
A7
A7
Two Stack
Pointers
Program counter
The program counter provides the MC68000 with an address range of 16
Megabytes. As instructions are based on word-sized operands, the counter must
always hold an even address. Attempts to address odd-numbered locations will
cause an error-trap.
31
23
oooooood
Status register
15
8
7
The status register is split into user and system bytes. The user byte is
evaluated for the condition codes used in the branching instructions. The codes
are affected by all instructions that alter the contents of the data registers or
memory, but not by changes to the address registers.
G.26
User byte
Condition codes
|x|x|x|4|312 1110
Not used
Bit 0 - Carry
Bit 1 - Overflow
Bit 2 - Zero
Bit 3 - Negative
Bit 4 - Extend

<!-- source-page: 309 -->
## Page 309

MC 68000 Instruction Summary
The unused bits in the status register are read as zero. They are reserved for
the MC68020 instruction set.
System byte
-^—r—,—,—, ,
,
| - |
Bits 8-10 Interrupt mask (0-7)
15|x 113| xIx[10| 9I8|
Bit13.
Supervisor state
Bit 15 -
Trace mode
x = not used
Interrupt
mask
Organization of addresses in memory
Byte
Longword
\
Byte
Low byte_
High byte"
Memory top
Any address
+3
+2
+1
-— Even address
7-0
15-8
23-16
31-24
For word and longword
memory operations, the high
byte is on a word boundary
(even address), the following
bytes are in order higher in memory.
By convention, system stacks
grow downwards in memory.
Word
Low byte
High bvte
+1
Even address
Stack
Memory bottom
G.27

<!-- source-page: 310 -->
## Page 310

The Concise Atari ST Reference Guide
G.28

<!-- source-page: 311 -->
## Page 311

MC 68000 Instruction Codes
Appendix H
MC68000 instruction codes
General
H.2
Instruction word parsing analysis
H.2
Instruction codes
H.4
Bit manipulation, move peripheral and immediate
instructions
H.4
Move byte instruction
H.5
Move longword instruction
H.5
Move word instruction
H.5
Miscellaneous instructions
H.6
Add Quick, subtract quick, set conditionally and
decrement instructions
H.7
Branch conditionally instructions
H.8
Conditional tests
H.8
Move quick instructions
H.9
OR, divide and subtract decimal instructions
H.9
Subtract and subtract extended instructions
H.9
Emulation instruction, type 1010
H.10
Compare, exclusive OR instructions
H.10
AND, multiply, add decimal, exchange instructions
H.ll
Add and add extended instructions
H.ll
Shift and rotate instructions
H.12
Emulation instructions, type 1111
H.13
Address modes
Encoding
H.14
H.1

<!-- source-page: 312 -->
## Page 312

The Concise Atari ST Reference Guide
Motorola MC68000 Coding
The Motorola MC68000 series of microprocessors rationalize instruction code
allocation by segmenting the 16-bit Operation Word into five smaller blocks, each
of which has a fairly consistent meaning.
Operation word instruction
1514131211 109
8
7
6
5
4
3
2
10
type
dmod
dreg
smod
sreg
Instruction Word Parsing Analysis
Type
15| 14| 13 13
The types 0 to 15 instruction codes (16 classes) are allocated as follows:
Type
Instructions Range
0
Bit manipulation, Move Peripheral and Immediate instructions
1
Move byte Instructions
2
Move longword instructions
3
Move word instructions
4
Miscellaneous instructions
5
Add Quick, Subtract Quick, Set conditionally and Decrement instrs.
6
Branch conditionally instructions
7
Move Quick instructions
8
OR, Divide and Subtract decimal instructions.
9
Subtract, Subtract extended instructions.
10
Unassigned
11
Compare, Exclusive OR instructions
12
AND, Multiply, Add decimal and Exchange instructions
13
Add, Add extended instructions
14
Shift and Rotate instructions
15
Unassigned
H.2

<!-- source-page: 313 -->
## Page 313

MC 68000 Instruction Codes
Dreg
11 10
9
Dreg has three main uses, normally holding the destination address in the
general move instruction, one of the two register numbers for use in the specified
instruction or embedded data for use in the add and subtract quick instructions.
Dreg only refers to a register in those instances where the instruction has two
register operands.
Dmod
8
7
6
Dmod has two main uses, specifying the effective address mode of the
destination operand in the general move instruction or, in most other cases it
defines the size of the operation to be performed.
Smod
5
4
3
Smod usually defines the effective address mode of the instruction, the
source operand for the move instruction.
Sreg
2
1
0
Sreg defines the effective address register, usually the source.
H.3

<!-- source-page: 314 -->
## Page 314

The Concise Atari ST Reference Guide
Instruction codes
Bit Manipulation,Move Peripheral and Immediate
Instructions - Type 0
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
BCHGDn,ea"~ "~Dn~" '"T"
""ea-
"ZaTaTtaTd "-""-"" A~-"~-"
BCHG data,ea
4
1
-eadataltadd
-
-
A -
-
BCLRDn,ea
Dn
6
-eadataltadd
-
-
A -
-
BCLRdata,ea
4
2
-eadataltadd
-
-
A -
-
BSET Dn,ea
Dn
7
-eadataltadd
-
-
A -
-
BSET data,ea
4
3
-eadataltadd
-
-
A -
-
BTST Dn,ea
Dn
4
-ea-
dataddmd2 -
-
A -
-
BTST data,ea
4
0
-ea-
dataddmd2 -
-
A -
-
MOVEP Dx,d(Ay) Dx
MOVEP d(Ay),Dx Dx
1 lx
1 Ox
1
1
Ay
Ay
-
ORI data,ea
ORI data,CCR
ORI data,SR
0
0
0
Oss
0
1
7
7
-ea-
4
4
dataltadd
-
A
A
A
A
A
A
0
0
AAA
AAA
ANDI data,ea
ANDI data,CCR
ANDI data,SR
1
1
1
Oss
0
1
7
7
-ea-
4
4
dataltadd
A
A
A
A
A
A
0
0
AAA
AAA
SUBI data,ea
2
Oss
-eadataltadd
A
A AAA
ADDI data,ea
3
Oss
-eadataltadd
A
A AAA
EORI data,ea
EORI data,CCR
EORI data,SR
5
5
5
Oss
0
1
7
7
-ea-
4
4
dataltadd
A
A
A
A
A
A
0
0
AAA
AAA
CMPI data,ea
6
Oss
-eadataltadd
-
A AAA
H.4

<!-- source-page: 315 -->
## Page 315

MC 68000 Instruction Codes
Move byte instruction - Type 1
Instruction
Syntax
Dreg
Dmod
Smod
Sreg
11-9
8-6
5-3
2-0
Address
Mode
Condition Coc
X
N
Z
V
C
MOVE.B ea,ea
source
destination
-ea-
-ea-
ALL*
dataltadd
-
A
A
0
0
*Address register direct mode is not permitted
Move longword instruction - Type 2
Instruction
Syntax
Dreg
11-9
Dmod
8-6
Smod
Sreg
5-3
2-0
Address
Mode
Condition Codes
X
N
Z
V
C
MOVE.L ea,ea
source
destination
-ea-
-ea-
ALL
dataltadd
-
A
A
0
0
Instruction
Syntax
MOVE.W ea,ea
source
destination
Move word instruction - Type 3
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
11-9
8-6
5-3
2-0
Mode
X N Z
V C
-ea-
-ea-
ALL
dataltadd
A
A
0
0
.
x Size
s s Size
Condition Codes
.
0 = Word
0 0 = Byte
u
= Undefined
1 = Longword
01= Word
A
= Affected
10= Longword
-
= Unaffected
.
ea
= Effective address
0
= Cleared
CCR = Condition code register
1
=Set
. SR = Status register
H.5

<!-- source-page: 316 -->
## Page 316

The Concise Atari ST Reference Guide
Miscellaneous instructions - Type 4
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
NEGXea"
0™
""6'sT"
""ea-""
""dataltadd "a A A A A
CLRea
1
Oss
-eadataltadd
-
0
1
0
0
NEGea
2
Oss
-eadataltadd
A
A
A
A
A
NOT ea
3
Oss
-eadataltadd
-
A
A
0
0
Dn
Dn
Dn
4
v
LINKAn,data
7
1
2
An
UNLK An
7
1
3
An
MOVEAn,USP
7
1
4
An
MOVEUSP,An
7
1
5
An
MOVE SR,ea
MOVE ea,CCR
MOVE ea,SR
0
2
3
3
3
3
-ea-
-ea-
-eadataltadd
-----
dataddmdl A A
A
A
A
dataddmdl A A
A
A
A
SWAP Dn
EXT.W Dn
EXT.L Dn
4
4
4
1
2
3
0
0
0
Dn
Dn
Dn
-
A
A
0
0
-
A
A
0
0
-
A
A
0
0
NBCD.B ea
PEAea
4
4
0
1
-ea-
-eadataltadd
A
u
A
u
A
conaddmdl -----
MOVEM list,ea
MOVEM ea,list
4
6
Olx
Olx
-ea-
-eaconaltadd -----
conaddmd2 -----
TSTea
TASea
5
'
5
Oss
3
-ea-
-eadataltadd
-
A
A
0
0
dataltadd
-
A
A
0
0
ILLEGAL
5
3
7
'
4
- - - - -
TRAP data
7
1
00 WW
- - - - -
H.6

<!-- source-page: 317 -->
## Page 317

MC 68000 Instruction Codes
Miscellaneous instructions - Type 4
cont.
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
RESET
7
1
6
0
NOP
7
1
6
1
STOP data
7
1
6
2
RTE
7
1
6
3
RTS
7
1
6
5
TRAPV
7
1
6
6
RTR
7
1
6
7
JSRea
7
2
-ea-
JMPea
7
3
-ea-
CHK.W ea,Dn
LEA.L ea,An
Dn
An
-ea-
-ea-
A
A
A
A
A
A
A
A
A
A
A
A
A
A
A
conaddmdl
conaddmdl
dataddmdl -
A
u
u
u
conaddmdl -----
Add Quick,Subtract Quick, Set conditionally, Decrement
instructions -Type 5
Instruction
Syntax
Dreg
11-9
Dmod
8-6
Smod
5-3
Sreg
2-0
Address
Condition Coc
Mode
X
N
Z
V
C
AddQ data,ea
SUBQ data,ea
data
data
Oss
1 s s
-ea-
-eaaltaddmod A
A
A
A
A
altaddmod A
A
A
A
A
Sccea
c
c cc 11
-eadataltadd -----
DBcc Dn,data
c
c
c
c 11
1
Dn
- - - - -
.
x Size
s s Size
Condition Codes
.
0 = Word
0 0 = Byte
u
= Undefined
1 = Longword
0 1= Word
A = Affected
10= Longword
-
= Unaffected
.
ea
= Effective address
0
= Cleared
CCR = Condition code register
1
=Set
. SR = Status register
cccc
= 4-bit Condition code
vvvv = 4-bit Vector address
H.7

<!-- source-page: 318 -->
## Page 318

The Concise Atari ST Reference Guide
Branch conditionally instruction - Type 6
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
Bcc data
c c c c
displacement (bits 0-7)
-----
BSRdata
0
1 displacement (bits 0-7)
-----
BRA data
0
0 displacement (bits 0-7)
Conditional tests for branch instructions
cc
Mnemonic
Condition
0
T
TRUE
1
F
FALSE
2
HI
HIGH
3
LS
LOW or SAME
4
CC
CARRY CLEAR
5
CS
CARRY SET
6
NE
NOT EQUAL
7
EQ
EQUAL
8
VC
OVERFLOW CLEAR
9
VS
OVERFLOW SET
10
PL
PLUS
11
MI
MINUS
12
GE
GREATER or EQUAL
13
LT
LESS THAN
14
GT
GREATER THAN
15
LE
LESS or EQUAL
There is no Branch TRUE BT or Branch FALSE BF, the codes are used by the
BSR and BRA instructions
x Size
s s Size
Condition Codes
.
0 =Word
00 = Byte
u
= Undefined
1 = Longword
01= Word
A
= Affected
10 = Longword
-
= Unaffected
.
ea
= Effective address
0
= Cleared
CCR = Condition code register
1
=Set
. SR = Status register
cccc
= 4-bit Condition code
H.8

<!-- source-page: 319 -->
## Page 319

MC 68000 Instruction Codes
Move Quick instruction - Type 7
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
MOVEQ"data"Dn"Dn
0
data"(bits"7-0)
™Ta"6"~6"
2's complement data value
Or, Divide, Subtract Decimal instructions - Type 8
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
ORea,Dn
Dn
Oss
"Tea""'
"daTaddmdr-""A"A~"6""6"
OR Dn,ea
Dn
1 s s
-eaaltmemadd -
A A 0
0
DIVU ea,Dn
Dn
3
-eadataddmdl -
A A A 0
DIVS ea,Dn
Dn
7
-eadataddmdl -
A A A 0
SBCD Dy,Dx
Dx
4
0
Dy
-
AuAuA
SBCD -(Ay),-(Ax) Ax
4
1
Ay
-
A u A u A
Subtract, Subtract Extended instructions - Type 9
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
SUBA"w"ea,An""An
3
"ea"
ALL
-----------------
SUBA.L ea,An
An
7
-ea-
ALL
SUB ea,Dn
Dn
Oss
-ea-
ALL
A A A A A
SUB Dn,ea
Dn
1 s s
-eaaltmemadd A A A A A
SUBX Dy,Dx
Dx
1 s s
0
Dy
-
A A A A A
SUBX -(Ay),-(Ax) Ax
1 s s
1
Ay
-
A A A A A
H.9

<!-- source-page: 320 -->
## Page 320

The Concise Atari ST Reference Guide
Emulation Instruction - Type 10 (#$A)
Line-A
Normally available for the implementation of user-written routines and
entered by ensuring four MSBof the op word or defined word constant are 1010
(10 dec), which will cause a trap to a user routine; other bits of op word may be
used for parameter passing. The ST uses this instruction for initializing and
operating the line-A functions on which GEM VDI and subsequently GEM AES
are based - so use with care.
Compare, Exclusive Or instructions - Type 11 (#$B)
Instruction
Syntax
Dreg
11-9
Dmod
8-6
Smod
Sreg
5-3
2-0
Address
Mode
Condition Codes
X
N
Z
V
C
CMPA ea,An
An
xll
-ea-
ALL
-
A
A
A
A
CMP ea,Dn
Dn
Oss
-ea-
ALL
-
A
A
A
A
CMPM -(Ay),-(Ax) Ax
1 ss
1
Ay
-
-
A
A
A
A
EOR Dn,ea
Dn
1 ss
-eadataltadd
-
A
A
0
0
x Size
s s Size
Condition Codes
.
0 = Word
0 0= Byte
u
= Undefined
1 = Longword
01= Word
A
= Affected
10 = Longword
-
= Unaffected
.
ea
= Effective address
0
= Cleared
CCR = Condition code register
1
=Set
. SR = Status register
H.10

<!-- source-page: 321 -->
## Page 321

MC 68000 Instruction Codes
And, Multiply, Add Decimal, and Exchange instructions -
Type 12 (#$C)
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
ANDea,Dn
Dn
Oss
-ea-
~~dalklLdmdl-~A~A~6"b"
AND Dn,ea
Dn
1 s s
-eaaltmemadd -
A A 0
0
MULU ea,Dn
Dn
3
-eadataddmdl -
A A 0
0
MULS ea,Dn
Dn
7
-eadataddmdl -
A A 0
0
ABCD Dy,Dx
Dx
4
0
Dy
-
A u A u A
ABCD -(Ay),-(Ax) Ax
4
1
Ay
-
A u A u A
EXGDDx,Dy
Dx
5
0
Dy
-
EXGAAxAy
Ax
5
1
Ay
-
-
-
-
-
-
EXGMDx,Ay
Dx
6
1
Ay
-
-----
Add, and Add Extended instructions - Type 13 (#$D)
Instruction
Dreg
Dmod
Smod
Sreg
Address
Condition Codes
Syntax
11-9
8-6
5-3
2-0
Mode
X N Z V C
ADDA.Wea,An
An"" T~
'"-ea.-""
ALL
------------------
ADDA.Lea,An
An
7
-ea-
ALL
-----
ADD ea,Dn
Dn
Oss
-ea-
ALL
A A A A A
ADD Dn,ea
Dn
1 s s
-eaaltmemadd A A A A A
ADDX Dy,Dx
Dx
1 s s
0
Dy
-
A A A A A
ADDX-(Ay),-(Ax)Ax
1 s s
1
Ay
-
A A A A A
H.11

<!-- source-page: 322 -->
## Page 322

The Concise Atari ST Reference Guide
Shift / Rotate instructions - Type 14 (#$E)
Instruction
Syntax
Dreg
11-9
Dmod
8-6
Smod
5-3
Sreg
2-0
Address
Condition Codes
Mode
X
N
Z
V
C
ASL Dx,Dy
ASL data,Dy
ASLea
Dx
count
0
1 ss
1 ss
7
4
0
-ea-
Dy
Dy
A
A
A
A
A
A
A
A
A
A
altmemadd A A
A
A
A
ASR Dx,Dy
ASR data,Dy
ASRea
Dx
count
0
Oss
Oss
3
4
0
-ea-
Dy
Dy
A
A
A
A
A
A
A
A
A
A
altmemadd A A
A
A
A
LSLDx,Dy
LSL data,Dy
LSLea
Dx
count
1
1 ss
1 s s
7
5
1
-ea-
Dy
Dy
A
A
A
0
A
A
A
0
altmemadd A A
A
0
A
A
A
LSR Dx,Dy
LSR data,Dy
LSRea
Dx
count
1
Oss
Oss
7
5
1
-ea-
Dy
Dy
A
A
A
0
A
A
A
0
altmemadd A A
A
0
A
A
A
ROL Dx,Dy
ROL data,Dy
ROLea
Dx
count
3
1 s s
1 s s
7
7
3
-ea-
Dy
Dy
-
A
A
0
-
A
A
0
altmemadd -
A
A
0
A
A
A
RORDx,Dy
ROR data,Dy
RORea
Dx
count
3
Oss
Oss
3
7
3
-ea-
Dy
Dy
-
A
A
0
-
A
A
0
altmemadd -
A
A
0
A
A
A
ROXL Dx,Dy
ROXL data,Dy
ROXL ea
Dx
count
2
1 s s
1 ss
7
6
2
-ea-
Dy
Dy
A
A
A
0
A
A
A
0
altmemadd A A
A
0
A
A
A
ROXR Dx,Dy
ROXR data,Dy
ROXR ea
Dx
count
2
1 ss
1 s s
7
6
2
-ea-
Dy
Dy
A
A
A
0
A
A
A
0
altmemadd A A
A
0
A
A
A
H.12

<!-- source-page: 323 -->
## Page 323

MC 68000 Instruction Codes
Emulation instruction - Type 15 (#$F)
Line-F
Normally available for the implementation of user-written routines, and
entered by ensuring four MSB of the op word or defined word constant are 1111
(15 dec), directing the trap service to a user routine. Other bits of op word may be
used for parameter passing.
This service trap is used by the MC68020 processor for passing co-processor
instructions. The ST uses it in processing the application environment services
(AES), so be careful.
x Size
s s Size
Condition Codes
.
0 = Word
0 0= Byte
u
= Undefined
1 = Longword
01= Word
A
= Affected
10= Longword
-
= Unaffected
.
ea
= Effective address
0
= Cleared
CCR = Condition code register
1
=Set
. SR = Status register
H.13

<!-- source-page: 324 -->
## Page 324

The Concise Atari ST Reference Guide
Address modes
Encoding
The range of addressing modes are coded consistently throughout the
MC68000 instruction set and may be summarized as follows:
Addressing mode
Syntax
Mode
Register
Extension
#
#
words
Data register direct
Dn
0
n
0
Address register direct
An
In
0
Address register indirect
(An)
2
n
0
Address register indirect
(An)+
3
n
0
with postincrement
Address register indirect
-(An)
4
n
0
with predecrement
Address register indirect
d(An)
5
n
1
with displacement
Address register indirect
d(An.Ri) 6
n
1
with index
Absolute sh
Absolute lo
Program co
displacemei
Program co
Immediate
n = Register number 0 to 7
ExtensionWord = Number of extension words following the op word due to this
address mode (source and destination ext. words are cumulative)
Mode # ==Dmod and Smod in instruction code tables
Register # ==Dreg and Sreg in instruction code tables
Absolute short
ABS.S
Absolute long
ABS.L
$xxxx
7
$xxxxxx 7
0
1
1
2
Program counter with
displacement
Program counter with index
d(PC)
7
d(PC.Ri) 7
2
3
1
1
Immediate
Imm
#$xxx
7
4
lor2
H.14

<!-- source-page: 325 -->
## Page 325

Error Codes
Appendix I
Error codes
BIOS error codes
1.2
GEMDOS error codes
1.3
Miscellaneous error codes
1.4
1.1

<!-- source-page: 326 -->
## Page 326

The Concise Atari ST Reference Guide
BIOS error codes
Error
code
0
-1
-2
Function
O'K
Error
Drive not ready
Comments
Successful operation
Not ready, not attached or busy
-3
Unknown command
Command not understoodby device
-4
CRC error
Soft error whilereadingsector
-5
Badrequest
Bad parameter, Cannotdo request
-6
Seek error
-7
Unknown media
-8
Sector not found
-9
-10
-11
-12
-13
-14
No paper
Write fault
Read fault
General error
Write protect
Media change
-15
Unknown device
-16
Bad sectors
-17
Insert disk
Drive could not seek
Foriegn media. Bad zero boot sector
Reserved
Read only or protected media
Media changed since last write or
the rd/wr op not done (file error)
BIOSdoesn't recognize device
Format yielded bad sectors
Disk not in drive (shell error)

<!-- source-page: 327 -->
## Page 327

Error Codes
GEMDOS error codes
Error PC DOS
code equivalent
Function
Supported
-32
1
Invalid function number
-33
2
File not found
-34
3
Path not found
-35
4
No handles left
(too many open files)
Not supported
-36
-37
-38
-39
5
6
7
8
Access denied
Insufficient memory
Invalid handle
-40
-41
-42
-43
9
10
11
12
** Insufficient memory
** Insufficient memory
Invalid memory block add
44
13
45
14
46
15
47
16
-48
-49
17
18
Invalid drive specified
** Invalid operation
No more files
The list of PC-DOS equivalent error codes supported may be found by
rurming the GEM demonstration program (Appendix L)-
1.3

<!-- source-page: 328 -->
## Page 328

The Concise Atari ST Reference Guide
1.4
Miscellaneous error codes
Error
Function
code
-64
Range error
-65
Internal error
-66
Invalidprogramload format
-67
Setblock failure due to growth restrictions

<!-- source-page: 329 -->
## Page 329

BASIC GEM
Appendix J
BASIC GEM
GEMSYS
J.2
VDISYS
J.2
SYSTAB
J.3
BASIC example
J.4
BASIC assembler
J.6
Hand coding
J.7
Coding chart
J.10
J.1

<!-- source-page: 330 -->
## Page 330

The Concise Atari ST Reference Guide
ST BASIC provides the programmer with direct access to parts of the
operating system AES and VDI interface.
GEMSYS
The AES control arrays are accessed through the AES parameter block (GB
pointer), the block provides pointersto the other supplementary AES parameter
blocks:
control table
global array
int_in table
int_out table
addr_in table
addr out table
+$0
\
+$4
I Data input and output
+$8
I as specified in the AES
+$C I traps and utility tables.
+$10 I Chapter 5
+$14 /
The tables are used by the programmer to input data, call the appropriate
GEM AES function, GEMSYS(n), and read any reply from the data placed in the
output tables by the function.
VDISYS
The VDI parameter blocks are directlyaccessible from BASIC:
\
I
I tables
I
/
The appropriate tables are loaded with data and the function called via
VDISYS(l), the (1) being a dummy argument. Any reply is read from the output
tables.
J.2
contrl
input
ptsin
input
ptsout
output
intin
input
intout
output
GEMSYS
I
v
GB —>
control
global
int_in
int_out
addr_in
addr out
\
I
I Indirect
I access
I
/
VDISYS
I
v
contrl
intin
intout
ptsin
ptsout

<!-- source-page: 331 -->
## Page 331

BASIC GEM
SYSTAB
STBASIC also provides access to a BASIC systemtable of the following read
only pointers and parameters:
Graphics resolution
+$0
l=high resolution
2=medium resolution
4=low resolution
Editor ghost line style
+$2
0=thickened
(Read/write)
l=intensity
2=skewed
3=underlined
4=outline
5=shadow
Edit AES handle
+$4
1
\
List AES handle
+$6
2
1 default
Output AES handle
+$8
3
1
Command AES handle
+$A
4
/
Edit open flag
+$C
\
List open flag
+$E
1 0=closed
Output open flag
+$10
1 l=open
Command openflag
Graphics buffer
+$12
/
+$14 Longword 32K buffer pointer
GEM flag
+$18 0_normal, l_off
The GEM flag is used to turn BASIC I/O off and increase the processing
speed of GEM based operations. With BASIC partially off, the I/O functions
involvingthe screen, mouse and keyboardare disabled,although disk I/O is still
enabled.
TheBASIC functions canbe re-enabled aftertheburst ofspeedfor userinput
Not all GEM and VDI functions are available through BASIC, some of the
BASIC housekeeping activities negate the effectof the functions.
J.3

<!-- source-page: 332 -->
## Page 332

The Concise Atari ST Reference Guide
Cautionary notes:
Ensure that evaluations of the graphic primitives take into account color.
Many experiments may appear not to work simply because the writing color is
the same as the screen backgound.
Characters are written to the screenstarting from the left-handedge and will
probably be obscured by the command screen border unless the programmer
moves it out of the way.
BASIC example
Use the mouse and the right button to draw a primitive, use the left button to
change the primitive. Note the effect on a primitive of crossing the left hand
screen edge.
10
start: CLEAR: a#=gb:int_out=PEEK(a#+12)
20
FULLW 2GLEARW 2
30
INPUT "GDP (1 to 9) ";gdp
40
IF gdp or gdp9 THEN GOTO start
50
POKE systab+24,1:
REM BASIC I/O off
60
POKE contrl,122:POKE contrl+2,0:POKE contrl+6,1
70
GOSUB curson
80
attribs: GEMSYS(79)
90
x=PEEK(int_out+2) :
REM x mouse
100
y=PEEK(int_out+4) :
REM y mouse
110
key=PEEK(inf_out+6):
REM button state nil_left_right
120
ON key+1 GOSUB showcurs, done, drawprim
130
GOTO attribs
140
done: POKE systab+24,0:GOTO start:
REM nasty return
150
drawprim:
REM
160
COLOR 1,(RND*15)+1,1,RND*25,2 :
REM random color
170
IF mouse=0 THEN GOTO 210
180
mouse=0
190
POKE contrl,!23:POKE contrl+2,0:POKE contrl+6,0
J.4

<!-- source-page: 333 -->
## Page 333

200
VDISYS(l):
REM hide cursor
210
POKE contrl,ll:in=0:xop=x+50:yop=y+50:rc=0
220
ptin=2:IF gdp=4 THEN ptin=3:xop=0:yop=0:rc=50
230
IF gdp=2 OR gdp=3 THEN ptin=4:xop=0:yop=0:in=2
240
POKE contrl+2,ptin
250
IF gdp=6 OR gdp=7 THEN xop=50:yop=20:in=2
260
IF gdp=5 THEN xop=60:yop=40
270
IF inO THEN POKE contrl+6,in
280
POKE contrl+10,gdp
290
POKE ptsin,x
300
POKE ptsin+2,y
310
POKE ptsin+4,xop
320
POKE ptsin+6,yop
330
REM IF ptin=2 THEN GOTO nxtin
340
POKE ptsin+8,rc
350
POKE ptsin+10,0
360
REM IF ptin=3 THEN GOTO nxtin
370
POKE ptsin+12,50
380
POKE ptsin+14,0
390
REM nxtin: IF in=0 THEN GOTO draw
400
POKE intin,(rnd*3600)
410
POKE intin+2,(rnd*3600)
420
draw: VDISYS(l)
430
RETURN
440
showcurs: IF mouse=l THEN RETURN
450
POKE contrl,122:POKE contrl+2,0:POKE contrl+6,0
460
curson: POKE intin,0: VDISYS(l)
470
mouse=l: RETURN
BASIC GEM
Look at the spelling of the variables, particularly contrl, if the program
crashes. Although BASIC access to the processor is normally in user mode, PEEK
and POKE instructions are performed in supervisor mode to provide access to all
parts of memory.
J.5

<!-- source-page: 334 -->
## Page 334

The Concise Atari ST Reference Guide
BASIC ASSEMBLER
There are many ways of producing a combined BASIC/assembler program
on the Atari STcomputer, the following demonstrates one of them:
First create the assembler subroutine of relocatable 68000 machine code that
canbesaved usinga BASIC programsimilar to thefollowing.
10
RESTORE
20
ZA$="12345678901234567890":
REM \Use either method to
30
ZB$=STRING$(100,"*"):
REM /create space for code
40
y=VARPTR(ZA$):
REM Somewhereto put code
50
DEFSEG=y:
REMSet up loop offset
60
FOR a=0 TO n
70
READ x:POKE a,x:
REM Put code into memory
80
NEXT a
90
BSAVE "progl.asm",y,n:
REMSave code to disk
100
STOP
200
DATA
REMByte sized data
The machine code will probably be loaded into a space created within the
main BASIC program by a dummy variable.Obviously,any number of different
machine code utilities can be loaded into the same space dependant upon
program state, or they may be stored in individual program spaces.
Parameters are passed to the machine code routine on the user stack which
contains an integer count of the number of parameters passed on top. The next
item on the stack is a longword pointer to the 8-byteper parameter array. String
variables use the array parameteras a pointer to the string.
J.6

<!-- source-page: 335 -->
## Page 335

BASIC GEM
Output can be placed in predefined variables and if correctly formatted, read
back by the BASIC program.
10
ZB$=STRING$(100,"*"):
20
ZR$="12345678":
30
y=VARPTR(ZB$):
40
ans=VARPTR(ZR$):
50
BLOAD"progl.asm",y:
100
CALLprogl(x,y,ans):
REM Space to load code
REM Space for reply
REM Position for code
REM Position of reply
REM Load code from disk
REM Call program code, passing parameters
REM x and y, returning data in the
REM variable ans
An alternative might be to compile the code within the BASIC program
proper if the machine code program length is quite short.
Hand coding
Many
programmers
had
their
first
contact
with
assembly
language
programming through hand coded 8-bit microprocessor routines embedded in
short BASIC programs. MC68000 code is slightly more complicated to assemble
than 8-bit code, but is still perfectly manageable.
Use tables of instruction types 0 to 15 (Appendix H), to generate the basic
code i.e:
4096 *type + 512 *dreg + 64 *dmod + 8 *smod + sreg
and the address mode encoding table (Pg H.14) to determine the effective
address (-ea-) values if required.
J.7

<!-- source-page: 336 -->
## Page 336

The Concise Atari ST Reference Guide
Example of a hand coded program
Project:
Version #:
Label
00
2
4
6
8
TO"
2
4
6
8
20
2
4
6
8
30"
2
4
6
8
J.8
MONITOR
2
Syntax
MOVE.W
MOVE.W
MOVE.W
TRAP
ADDA.W
EORI.W
MOVE.W
MOVE.W
MOVE.W
TRAP
ADDA.W
RTS
SCREEN INVERSION
Author:
Src
Mnm
14
N
N_
DO
N
14
N
Dest
Mnm
•(SP'
-1
•(SP
0
•I$E\
SP
6
_D0_
1
•(SP
•(SP
0
SP
6
type
4
13
4
13
dmod
|sreg
dreg
smod
14
4
14
4
Dec
value
16188
-1
1618$
0
7
20046
5708'
6
2624
1
16125;
1618?;
0
1618$
7
2004$
57084
6
2008$
Date:
DEC/85
Notes
GET OLD COLOUR
_SETCOLOR
(Pg 3.8)
TIDY STACK
TOGGLE COLOUR BIT C
SET NEW COLOUR
TIDY STACK
RETURN TO BASIC

<!-- source-page: 337 -->
## Page 337

BASIC GEM
Use this type of program to load the code into a file on disk:
10
restore:n=70
20
zb$=string$(100,"*")
30
y=varptr(zb$)
40
def seg = y
50
for a=0 to n step 2
60
read x:poke a,int(x/256):poke a+l,x mod 256
70
next a
80
bsave "b/w.asm",y,n+2
100
stop
210
data 16188,-1,16188,0,16188,7
220
data 20046,57084,6,2624,1
230
data 16128,16188,0,16188,7
240
data 20046,57084,6
250
data 20085
300
data 0,0,0,0,0,0,0,0,0,0,0,0,0
310
data 0,0,0,0,0,0,0,0,0,0,0,0,0
320
data 0,0,0,0,0,0,0,0,0,0,0,0,0
and to toggle the screen or border color, run the following BASIC program
which loads the file back from disk and executes it:
10
zb$=string$(100,"*")
20
y=varptr(zb$)
bload "xb/w.asm",y
30
40
call y
50
stop
The following brief notes may be useful in compiling programs in the above
manner:
Entry to machine code level from BASIC is in supervisor mode.
If you drop to user mode, be careful where you place your stack. Perhaps you
might like to use the following sequence of instructions that jump over your stack
or data to the beginning of the executable code. DATA 17402,4,24576+dis,...
Start
LEA4(P"Cpu
BTvrais
Text
or
stack
Program
code
Set A1 to start of text
dis = 2 + text length (must be even)
Start of program
Ifin difficulties with a BRAJ-ich orJuMP, surround with NOP's to make the
jump less sensitive to the count.
J.9

<!-- source-page: 338 -->
## Page 338

The Concise Atari ST Reference Guide
Project:
Author:
Version #:
Date:
Label
Syntax
Src
Mnm
Dest
Mnm
type
dmc
dreg
)d
|sreg
smod
Dec
value
Notes
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
0
2
4
6
8
J.10

<!-- source-page: 339 -->
## Page 339

Program Development Tools
Appendix K
Program development tools
Atari MC68000 assemblers
K.2
Seka
K.2
Hisoft
K.4
GST
K.5
Metacomco
K.6
Digital Research
Compatibility table
K.7
K.8
General assembler compatibility
K.9
Assembler directives compatibility
K.10
Assembler conversions
K.ll
General conversion chart
K.12
Basic calling procedure
Executable file size
K.14
K.15
C compilers
K.16
K.1

<!-- source-page: 340 -->
## Page 340

The Concise Atari ST Reference Guide
Atari MC68000 assemblers
There are a number of assemblers available for the Atari ST programmer,
they have small discrepancies in the assembly syntax used, no uniformity in the
library and utility files supplied or of the method of creating an executable
program.
This makes it difficult for the inexperienced programmer to type as source a
program listing created for another assembler, and to get it operational. What I
have tried to produce is an analysis of each assembler and a conversion chart that
may help in isolating fairly straightforward problems.
Where a published program uses a particular assembler specific facility
(special macros etc.) then translation will not always be possible by simple
substitution and there may be no easy solution. Hopefully the general assembler
compatibility chart will indicate whether there is the likelyhood of a conversion.
This guide is very much less than perfect, but it is an attempt at assisting
inexperienced programmers in a very difficult field.
The assemblers
Very few of the assemblers provide programming details of the Motorola
M68000 processor instruction set, or teach the user basic assembler language
programming. If the reader has not written assembly language programs before,
the brief overview of the language in Appendices G and H should help.
Seka
The
combined
editor/assembler/monitor/debugger is held
in
a very
compact 20K of code, this means that parts of the package are a bit weak.
Although two editors are supplied, a line editor and a screen editor, neither
performs block find and replace function. Use the Atari wordprocessor in non wp
mode for major or block changes in large files. What is likely to be more of a
significant problem is the limitation to a leading letter for label and symbol
names (the use of an underscore is very common in most libraries and the Atari
system variables). A possible solution would be to substitute a little used letter
for the leading underscore, say 'z'.
K.2

<!-- source-page: 341 -->
## Page 341

Program Development Tools
On the positive side, the Seka assembler generates absolute or relocatable
executable code directly, has limited macro and conditional capability, and is a
quick assembler for writing programs if you know what you are doing - some of
the runtime error messages are incomprehensible with no guide in the manual as
to what they are trying to tell you. It is very convenient having all the facilties in
one program, an assembly error leaves the editor at the erroneous line for
immediate correction and reassembly or the programmer may trace through the
code with the monitor/debugger. The editor also allows the programmer to type
the source code in free format; the assembled output listing is automatically
tabulated, but there is no way of simply listing the code to a printer in a tabulated
form which makes the source difficult to read when trying to debug program
logic errors. Source files entered in a tabulated form are occasionally detabulated
in parts of the assembly list file. The system for linking files is a bit messy and
very
non-standard
as
are
some
of
the
assembler
directives.
The
monitor/debugger allows the programmer to single/multiple step through a
program, examine registers, set breakpoints and provides all the necessary
facilities to aid program debugging. It is important to ensure that program files
are of even length; odd file lengths sometimes produce run-time errors not
discovered by the debugger, which makes the fault extremely difficult to locate.
The assembly syntax is pretty standard; labels must terminate in a colon, 'movea'
should be entered as 'move', the assembler correcting the syntax but strangely
'adda' is acceptable.
The 36 page manual limits the two examples to very simple TOS programs,
one of which includes macros. The manual has a lot of ground to cover which it
manages only at a fairly minimal level, i.e it does not provide enough information
regarding the cause of errors - an error in a macro is flagged as an illegal operand
in the calling code. The manual contains a very useful single page command
summary.
The package is very easy to use, although not as powerful as some of the
other packages in this appendix. As an assembler, it is complete with minimal
libraries of DOS calls equates and GEM array generators.
K.3

<!-- source-page: 342 -->
## Page 342

The Concise Atari ST Reference Guide
Hisoft
A combined editor/assemblerwith a seperate monitor/debugger. TheHisoft
assembler employs include files to ease the access to the GEM and TOS functions
and produces machine code directly. The include files require function
parameters to be explicitly placed in the parameter arrays as per the assembler
GEM example (Appendix L). Theassembler does not havea linkerfacility, which
makes that aspect a little unusual, and does not like labels followed only by
comments on the same line. The editor is a full feature program with the minor
omissionof displaying and handling only one fileat a time.
The package contains include files of equates for BDOS, BIOS, extended BIOS
calls, system variables and a GEM include file that provides program
initialisation, VDI and AES constant equates and parameter array initialisation.
The package does not provide details of the data (Chapters 3, 4 and 5) to be
placed in the arrays.
The monitor/debugger besides supporting the usual step, set breakpoints,
examine and modify registers and memory etc. enables the assembled program
to be run and debugged using seperate screens for the graphics and the monitor
output, a very useful feature.
The documentation is well written and provides a good introduction for the
beginner.
A very friendly package that could benefit from the use of a RAM disk to
hold all the files in memory at once. In a 512K machine, seperating the program
into two components does not appear to provide the optimum 'modus operandi'.
K.4

<!-- source-page: 343 -->
## Page 343

Program Development Tools
GST
The GST assembler package has a very good GEMbased editor that enables
up to four files to be worked on at the same time in multiple windows, copying
blocks from one to another with ease. The only possible complaintregarding the
editor could be the relatively slow loading of program and files and of cursor
movement up and down within the file.
The assembler can produce relocatable binary output suitable for the linker
or executable code directly from position independant source. The executable
code does not contain the standard Atari TOS file header preamble,which must
be added by the programmer if the file is to act as a stand aloneprogram. A very
useful list of the instruction mnemonics is provided, as is information on the
optimisation route taken in compiling code. The use of an underscore for the
leadingcharacter of a labelor symbol is not permitted,whichentails a degreeof
non compatibilty with the standard Atari ST notation for some system variables
and extended BIOS calls.
The assembly of source is slow by virtue of the many disc accesses, but the
use of RAM disc for compilation and the loading of all modules into memory
together will obtain reasonable speed. There is no uninitialised data (BSS)
directive which means that GEM program files held on disc are about IK larger
than necessary. Ifsome instruction sizes are not explicitly stated, a liberal supply
of warning messages are issued.
The GST linker is also supplied with the Metacomco macro assembler, it
enables other high level language modules written in Pascal, Assembler and C to
be linked together in a single program.
The library supplied contains macro definitions of conditional structures.
GEM and TOS libraries are not supplied.
The documentation consists of seperate index-less assembler, editor and
linker manuals, which are very well packaged in a ring binder, the manuals are
very detailed, but may be difficult for the inexperienced assembly language
programmer to read.
K.5

<!-- source-page: 344 -->
## Page 344

The Concise Atari ST Reference Guide
Metacomco
The screen editor is good but does not follow the normal GEM style of access,
although the user will very quickly adjust. The global 'find and replace' is
comparitively slow as the screen is re-written for each change.
The assembler is slow in comparison with the smaller assemblers evaluated
in this appendix and would benefit greatly from the use of RAM disk. Symbols
may be of up to thirty significant characters, but tabulated 'dc' data values on one
source line seperated by a comma and space are not permitted - the space may be
used to introduce a comment.
Metacomco supply the GST linker with their macro assembler which can
produce either a binary file suitable for the GST linker or a CP/M 68K object file
suitable for the DR link68 linker; which links to the complete DR set of GEM and
TOS libraries, but is undocumented.
The Metacomco assembler package is supplied with assembler source to the
GEM libraries and a monitor program. The monitor provides breakpoints, a trace
mode and register/memory change and examine facilities.
The assembler suite of programs can be batched using the Menu+ program
provided, It enables the sequence of edit, assemble, link and run to be controlled
by the menu file, which runs and loads each program producing the specified
outputs as requested and entering the next stage automatically via a pause, wait
or continue programmed instruction.
The documentation is concise and very well laid out, but gives no additional
explanation on assembly errors to that displayed on the screen during the
assembly phase.
K.6

<!-- source-page: 345 -->
## Page 345

Program Development Tools
Digital Research
The Digital Research package can use any editor/word processor that is
capable of producing an unformatted ASCII text file.
The assembler, which is a reasonable implementation of the Motorola
M68000 assembly language, has no macro facilities but optimises instructions and
branches to produce efficient code.
The DR LINK68 linker provides access to the DR GEM and TOSlibraries that
consist of accessory and application header files, GEMDOS, BIOS, XBIOS, VDI,
AES and floating point libraries.
Although the assembler, linker and relocator programs can be installed as
TTP (TOS Takes Parameters) files, the programs are much easier to run via the
Activenture Corp. batch program. The additional use of a RAM disk to hold the
files and programs produces a very reasonable response, eliminating much of the
disc access.
The development package was intended for software developers and not the
general public, as such it is written with a high degree of technical jargon.
Complete withno omissions, a veritable 'Warand Peace' Itprovides information
on
all
of
the
GEM
VDI
functions
and
makes
no
mention
of
those
not
implemented on the ST.
DR C language modules may also be linked with the assembled source and
DR libraries to produce executable programs.
The package is supplied with the DR symbolic interactive debugger 'SID'
enabling the program writer to test and debug M68000 executable code, either
from TOS or GEM, read/write/move blocks of memory, disassemble code or
produce a hex dump, examine the CPU state, trace, run or step through the code.
Atari have recently made available a new faster linker ALN to software
developers, which replaces both LINK 68 and RELMOD, the linker and relocation
package respectively.
K.7

<!-- source-page: 346 -->
## Page 346

The Concise Atari ST Reference Guide
Compatibility table
The analysis of each package necessarily concentrates on the flaws, looking
for inconsistences and omissions. What may not be apparent is how good in
absolute terms the packages are, any purchaser being able to justify the cost on
technical excellence alone.
It may be useful to give an indication as to the range of likely purchaser of
each package:
K_seka assembler:
Absolutebeginner - competent programmer: Veryfast program development
Hisoft devpak:
Absolute beginner - competent programmer: Fast program development,
with GEM and TOS bindings.
GST macro assembler:
Absolute beginner - expert: Full feature assembler capable of linking with
other high level language modules to form executable programs.
Metacomco assembler:
Competent programmer - expert: Full feature assembler with macros. DR's
linker may be used to provide access to the complete set of system libraries, and
GST's linker to link high level language modules into a combined language
program.
Digital Research assembler:
Software developer: Not available to the general public.
K.8

<!-- source-page: 347 -->
## Page 347

Program Development Tools
General assembler compatibility:
Not exhaustive, merely a guide to what facilities are available.
Function
Editor
multifile edit
screen/line
GEM
Assembler(i/p)
Output
-nohnk
Optimiser
Macros
conditional
Linker
Input
Submissions
Output
Libraries
GEM
TOS
Maths
Monitor
Debugger
Hisoft
assembler
GENST
No
screen
Yes
(•S)
Executable
or binary
Yes
Yes
Yes
LINKST
Yes-limited
yes-limited
No
MONST
Yes
m
No
Relocator progra
Symbols
Label) column 1
end
) column n
Directives
Comment) col 1
)
coin
Case (Symbols)
Quotes
16 signif
Space
Space or:
space
Selectable
Digital
Research
Can use an
wordproceisr
ASCII text.
AS68 (.S)
Binary file
Yes
No
Yes
Link68
Batch file
Yes-complejte
Yes-comple te
Yes
SID
symbolic
interactive
debug] er
RELMOD
Space or:
Colon
Optional
GST
assembler
Edit
Yes (4)
screen
Yes
(.ASM)
Binary file
or executable
(no file hea|der)
Yes
Yes
Yes
GST-LINK
Binary file
Control file
File-headei
reloc table
code
data
optsym
Metacomco
assembler
Kseka
assembler
Ed
No
screen
No
All-in-one package
No
Line & screen
No
(ASM)
See linker
Yes
Yes
Yes
Can use either
GST-LINK 01
DR's LINK68
& RELMOD
urograms
(GST-LINK
is supplied)
(.S)
Executable
Yes
Yes
Relocatable
mode
only
(odd format)
table
No
No
No
No
Notsupplied
Linker can
debug sym
in program
No"
Yes-source
No
No
Yes
Supplied
put as source
b
example
on disk
No
Yes-minimal
Yes-minimal
No
Yes
Yes
~Nc7
8 signif
Space or:
Colon
char Upto 30 char
Space or:
Colon
Colon
Colon
period
* or;
Significant
Sngle/ dbldSngle/ dble
'or;
; or space
Not_signif
Single
or;
or space
cfnt Selectable
Single/doublle
Not significant
Single/double
GSTassembler executable code must supply a TOSprogram header and be
written in positition-independant code before it can be run. The default file
extensions are given in brackets.
K.9

<!-- source-page: 348 -->
## Page 348

The Concise Atari ST Reference Guide
Assembler directives compatibility
Directive
Explanation
Hisoft
Digital
Research
GST
Metacomco Kseka
Include(i/t ') Insert external
file
Yes (.$)
No
Yes (.IN)
(.MAC)
Yes
Abs. code
via linke r
Text
Relocatable code
No
Yes
Section cod e Yes (def) 1Zode ==
Data
Initialised data
No
Yes
Yes
No
BSS
Uninitialised dat i DSBSS==
Yes
No
Yes
Data ==
even
Align to word
Yes ***
Yes
***
***
Yes & oc c
ORG odd •> Absolute sectic n
Yes
Yes
Yes
No
Yes
Common
Common region
No
Yes
Yes
No
No
RORG <ad ir> Adjust curr lc>cn
No
Yes
Yes
No
Offset
Define table via
a DS directive
No
Yes
Yes
Yes
No
OPT
Select addr mode Diff meaning Ignored
PC or Ab s
No
No
Globl
External label
Yes
Yes
No
No
Yes
Xref
External name
Yes
Yes
Yes
Yes
No
Xdef
Internal label
for external use
Yes
Yes
Yes
Yes
No
Module
Link module nan le
Yes
Yes
Comment
Include commen
in linker listing
s
Yes
Equ
Symbol
Yes
Yes
Yes
Yes
Yes& =
Equr
Register
Yes
Yes
Reg
Register list
Yes
Yes
Yes
Set
Temporary value
Yes
Uses Equ
Yes
DC
Constant
Yes
Yes
Yes
Yes
Yes
DS
Storage
Yes
Yes
Yes
Yes
DCB
Constant block
Yes
Yes
Blk==
RS
Yes
No
Conditiona Ls
Yes
Yes
Yes
Yes
Yes
IF eq,ne,gt
Yes
Yes
No
Yes
If,Else
ge,lt,le
IFB
String c,nc
Yes
Yes
Yes
Yes
No
Symbol d,n d
Yes
Yes
Yes
No
Library Sys
GEM/TOS GEM/TOS/FI5
None
None
Minimal
Macro
If,Else,For
While,Unti
Repeat,Cas 3
Sub nth arg
\n
Not
LnJ
\n
?n
Sub unique # nni i \@
applicab e
[.L]
\@
?o
Mask2
Ignored
Ignored
IDNT
Ignored
Ignored
*** DS £ind DC word and longwords automatica Uy align to boundaries
K.10

<!-- source-page: 349 -->
## Page 349

Program Development Tools
Assembler conversions
There are a number of assemblers available for the ST, each with different
characteristics, this -section is provided as an aid to translation of programs
presented from alternative sources.
One of the by-products of the compatibility information is that it provides the
opportunity of generating a subset of directives and instructions that are of 4
almostO universal applicability, but compatibility does tend to look at the lowest
common denominator.
All of these programs have other attributes which provide a significant
improvement in performance over the base standard, these improvements are not
always apparent to the casual user but very handy to have if required.
If you wish to write source for maximum compatibility with other
assemblers, the following should minimise the problems:
- Size all instructions (move, clr, lea etc. do not default)
- Size branches (avoids masses of GSTwarning messages)
- Avoid using reserved words for labels such as text, code etc.
- Use a semicolon for all comments (except Hisoft and DR which should use a
'*'\
- Do not tabulate DC data, added spaces do not travel well.
- Limit label and symbol lengths to eight characters.
- Use 'EQU' directive, not '='.
- After text and data sections, it is wise to ensure that the PC is on a word
boundary. Most programs use 'EVEN', some assemblers use 'DC and 'DS' with a
.W or a .L extension.
Sizing instructions is perhaps the most difficult factor to come to terms with.
I find it extremely difficult to ignore and not stop and read any warning
messages, and become a little irritated to find that a branch 'might be short' or
that LEA has not got a .L extension. All warnings should be significant or else
they will 1 allO be treated as superfluous information.
K.11

<!-- source-page: 350 -->
## Page 350

The Concise Atari ST Reference Guide
General conversion chart
FROM
To-Kseka
Hisoft
GST
Metacoma >DR
Comments
Macros
MACRO
MACRO A
n.a.
Program may use
?1
\1
[A]
\1
Expanc many labels that:
Kseka
?2
\2
[B]
\2
code
iot appear to have
?o
\@
[X]
\@
in full
iny function. They
vill probablybe
ireakpoints.
comment
/
*
^
Size Opcoc es Size
1
Opcodes
& branch
opcodes
blk
ds
ds
ds
ds
Macros
MACRO
MACRO A
n.a.
Places GEM data
?1
\1
[A]
Expanc directly into VDI
Hisoft
?2
\2
[B]
code
and AES arrays. Il
the source includes
?o
\@
[•L]
in full
comment
/
X-
Size Opcoc es Size
3EM calls, follow
:he example
Opcodes
blk
ds:
& branch
opcodes
n appendix L
Macros
MACRO
MACRO
MACRO A MACRO
n.a.
Seems to like all
?1
\1
[A]
\1
Expanc
code
instructions sized
GST
?2
\2
[B]
\2
or issues lots of
?o
\@
[•L]
\@
in full vfamingmessages,
-ibrary of conditio
comment
*
/
I
aal macros will
Opcodes
< ause problems,
lode has to belong
C
blk
ds
to a section.
Macros
MAUKUA MACRO
n.a.
(JEM library suppl e
?1
[A]
\l
Expand
code
s
Implementation is
Metacome )?2
[B]
\2
tandard but
?o
[•L]
\@
in full t:•anslation depends
an the availability
comment
*
/
Size
cifthe library used,
Opcodes
blk
branch
ds
(follow example
Appendix L)
code
Section C
TEXT Delete any period
data
Section D
BSS
c irective prefix.
Digital
zlabel
zlabel
Jabel ;•>Jo macro facilities
Research
xit a full set of
comment
(add
/
/
*
<jEM libraries. Loo <
at example appx L
Opcodes
to all
to see sheer powei
ind how difficult
labels)
blk
ds
1ranslation will be
K.12

<!-- source-page: 351 -->
## Page 351

Program Development Tools
The above table will help to eliminate some of the more straight-forward
program conversion problems, those that remain are likely to be due to the use of
assembler specificdirectives and or libraries (especiallylabel errors).
If a program is published, one assumes that any include file data will be
generally available and can either be appended as an include file or the code
integrated with the main program block of code.
Ifyour assembler doesnot haveVDI and AES libraries, then to useGEM you
will have to create the arrays and load the addresses as shown in the assembler
GEMexample appendix L
The chart islimited tosimple conversions. Once include files and global label
definitions areused, you will need toassemble theprogram, generate a list ofthe
missing external labels and hopefully find them in the examples Appendix Land
or the call listings Appendix E.
Numbers
The following shows the standard presentation of the various numeric types:
Octal
@nnn
n=0 to 7
Binary
%xxxxxxxx
x=0 or 1
Decimal
nnrm
n=0 to 9
Hexadecimal
$nnnn
n=0 to 9, a to f
K.13

<!-- source-page: 352 -->
## Page 352

The Concise Atari ST Reference Guide
Basic calling procedures
Basic calling procedures for simple source files assembled (and linked)
without libraries.
Kseka
SEKA>r
FILENAME> filename
SEKA> a
OPTIONS> v
Instruction to read source file from disc
File to read (default .S extension)
Instruction to assemble source
Option to view assembly on screen
SEKA> wo
FILENAME> filename
Instruction to write output program
File to write (default .PRG extension)
Hisoft Menu driven, place cursor over instruction and click
Option
> Assemble
Option dialog box
Binary filename xxxxx.prg
Listing option boxes (none/screen/printer/disc)
Assemble/cancel boxes
GST Menu driven, place cursor over instruction and click,OR double click the
TTP program file and enter the filename as the parameter:
ASM.PRG filename
LINK.PRG filename
to produce a list file and filename.BIN from a default
.ASM extension file
to produce a .MAPfileand filename.PRG from a
default .BIN extension file
Metacomco Theprogram files are installedas TosTakes Parameters(TTP),
double click and enter input file:
ASSEM.PRG filename
LINK.PRG filename
Assembles filename.asm to produce a GSTformat
output file
Produces a .MAP file and filename.PRG from a
default .BIN extension file
Digital Research The program files areinstalled asTOS Takes Parameters and
the file data entered into the parameter box.
AS68.PRGfilename.S
Produce binary file
LINK68.PRG filename.68K = filename.o
RELMOD.PRG filename
K.14
Produce relocatable file
Produce absolute file

<!-- source-page: 353 -->
## Page 353

Program Development Tools
Executable file sizes (bytes)
Natural compilations with no optimisation extensions called.
Program
Page # D.R
Seka
Hisoft
GST
Metacomcc
GEM error message
L7
777
-
-
-
781
Assembler GEM
L8-17
1651
1734
3170
3170
3016
3170
TOS colour demo
LI 6
145
162
246
246
235
248
TOS VT52 screen
L18-19 194
202
202
192
202
TOS sound program
L20-22 324
331
591
591
586
591
Line-A sprite program L25-26 296
314
394
394
374
392
The Metacomco file sizes are forfiles linked viathe GST tinker except for the
'GEM error message' which used the DR linker.
The Digital Research files are absolute files and therefore presumably nearer
the minimum possible size.
(a secondary figure is given which specifically sets all text and data sections
initialised to provide standard file size compilation comparisons, not all of the
test assemblers can handle an uninitialised section)
K.15

<!-- source-page: 354 -->
## Page 354

The Concise Atari ST Reference Guide
C compilers
Many C compilers have been developed for the ST range of computers,
enabling the ST programmer to produce modular, well documented, easily
maintained code that may be ported to other C systems with a minimum of
effort.
Although achieving the same end result, the C compilers differ considerably
in the way that they attain that result. I give three examples of the compilation
process:
Source text
1
Preprocessor
Intermediate file
Parser
Intermediate cocle file
Code generator
Assembler text
1
Assembler
Object file
1
Libraries
1
Link68
Executable program file
Relocator
Absolute program file
K.16
Resolve #define and
#include statements
Produce an intermediate
code file
Generate assembly
language source file
Create an object file
Link object file with
run-time library and
operating system files
Change the relocatable
information to absolute
data

<!-- source-page: 355 -->
## Page 355

GSTC compiler
Source text
I
Assembler text
C compiler
Assembler
Relocatable binary file
Libraries
Link68
Executable program file
Metacomco Lattice C
Source text
M
I
LCI compiler
Intermediate quad file
I
LC2 compiler
Binary file (GST or TOS format)
Libraries
Link68
Executable program file
Program Development Tools
Resolve #define and
#include statements,
produce assembly source
file.
Produce a relocatable
binary file
Link object file with
run-time library and
operating system files
Produce an intermediate
file of logical records
Produce either an object
file (DR linker or a
relocatable binary file
(GST linker)
Link object file with
run-time library and
operating system files
K.17

<!-- source-page: 356 -->
## Page 356

The Concise Atari ST Reference Guide
Those programmers who wish to program the Atari ST in C may find the
following brief notes helpful:
Unlike nearly allofthecommercial assemblers, theC compilers supplya full
setofGEM and system libraries. Commercial C compilers forthe Atari ST will in
general adhere to the GEM VDI and GEM AES function names used in this book,
usually only the first 8 characters being significant. The compilers diverge
considerably in use of parameter names, the calland parametersare therefore not
provided here to avoid confusion. The manual of the C compiler you are using
will provide a definitive list of the library routines available, interfaces, and the
required parameter size, sequence and annotation.
Many compilers will have additional features to greatly simplify the task of
writing GEM programs; but bear in mind that the use of these 'super C GEM
functions may put a restrainton programportability. A definite decision should
be made as to whether the programmer is writing portable code or simply
writing a program.
On a more general note; it is very much easier to develop programs on a 1
Meg disk drive, which makes the larger drive well worth the small additional
cost for those machines without the built-in drive.
K.18

<!-- source-page: 357 -->
## Page 357

Example Programs
Appendix L
Example assembler programs
GEM
Application and accessory header file
GEM demonstration program
GEM demonstration assembly program
OS
L.3
L.8
L.9
Display demonstration program
TOS header file
L.17
L.19
Character printing program
Sound demonstration program
ine-A
Line-A parameter table
Sprite demonstration
L.20
L.22
L.26
L.28
L.1

<!-- source-page: 358 -->
## Page 358

The Concise Atari ST Reference Guide
Example programs
General
The programs presented in this section illustrate some of the techniques
involved in accessing parts of the Atari ST operating system and also present
general purpose header/include files. The programs are written as shells to
which the programmer may add his/her own composition.
It is not the intention to provide 'state of the art' programs, merely
demonstrate access to the various parts of the operating system. Any attempt at
definitive programming would rapidly succumb to the passage of time and tend
to produce a book of listings. The main place to find quality programs will be the
computer magazines, where programs developed from this and other books will
appear as programmers quickly find new, smarter routes to access and use the
ROM routines.
Desktop accessories should be compiled as applications for debugging
purposes as it is not possible to execute an accessory.
Program conversion key
L.2
n.a
program not
suitable
for this assembler.
xxx
delete
this
line
*
use
; for Kseka,
GST
and Metacomco
comments

<!-- source-page: 359 -->
## Page 359

Example Programs
GEM
GEM application and accessory header file
Digital Research (and Metacomco in CP/M 68K object mode) application and
desk accessory files require a similar type of header source file construct to
provide access to the GEM VDI and AES libraries, either as the first file in theDR
link statement or as the beginning of a single block of assembler code.
Part of this file determines the size of memory the application requires and
returns the remainder to GEMDOS. Some Atari ST assemblers will provide
similar code as a header/initialisation file to permit the programmer to access the
VDI and AES functions through their own integral libraries.
* Digital Research
A
Hisoft
.
GST
Metacomco
Seka
*
*
n.a
n. a
n.a
text
* Text
segment
*
globl
main
*
Make
labels
*
.
xde f
globl _crystal
*
accessible
to
*
.
xde f
globl _ctrl_cnts
*
external
files
*
.
xde f
move .1
a.1, a 5
*
store stack
(a5)
*
move.l
#ustk,a7
*
set
local
stack
*
* Desk accessories
do
not
require the following lines of
code
* which size memory and return the unused memory to GEMDOS
move.1
4(a5),a5
move.l $c(a5),d0
add.l $14(a5),d0
add.l $lc(a5),d0
add.l #$100,dO
move.l dO,-(sp)
move.1 a5,-(sp)
move dO,-(sp)
move #$4a,-(sp)
trap
#1
add.l
#12,sp
* Main program call
* basepage address
*
* length of text
*
* length of
data
*
* length of
BSS
*
* basepage size
*
*
retained mem len
*
* memory to
modify
*
* dummy word
*
*
reallocate
to GEM*
*
function
number
*
* tidy stack
*
jsr _main
* main program code*
move.l #0,-(a7)
* return to GEMDOS
*
trap #1
* function call
*
L.3

<!-- source-page: 360 -->
## Page 360

The Concise Atari ST Reference Guide
* Digital Research
*
* GEMAES calls
link through _crystal
crystal:
move
1
4(a7) ,dl
*
address
of AES pblk*
move
w
#200, dO
*
GEMAES
function
#*
trap
#2
*
function
call
*
rts
*
return
*
bss
•
block storage
seg*
even
*
force even boundary*
ds.l
64
*
stk:
ds.l
data
even
1
*
*
*
Ctrl
cnts
Application manager
dc
b
0
1
0
dc
b
2
1
1
dc
b
2
1
1
do
b
0
1
1
dc
b
2
1
1
dc
b
1
1
1
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc.b
0,1,0
* Event manager
L.4
dc.b
dc.b
dc.b
dc.b
dc.b
0,1,0
3,5,0
5, 5, 0
0, 1, 1
2, 1, 0
dc. b
16,7,1
dc.b 2,1,0
dc. b
0,0,0
dc.b
0,0,0
dc. b
0,0,0
APPL_INI
10*
APPL_REAd
11*
APPL_WRIte
12 *
APPL_FINd
13*
APPLJTPLay
14*
APPL
TREcord...15*
APPL_EXIt
19*
EVNT_KEY
20*
EVNT_BUTton....21*
EVNT_MOUse
22*
EVNT_MESsage... 23 *
EVNT_TIMe
24*
EVNT_MULti
25*
EVNT
DCLick....26*
Hisoft
GST
Metacomco

<!-- source-page: 361 -->
## Page 361

* Digital Research
Menu manager
dc
b
1
1
1
dc
b
2
1
1
dc
b
2
1
1
dc
b
2
1
1
dc
b
1
1
2
dc
b
1
1
1
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc.b
0,0,0
Object manager
dc
b
2
1
1
dc
b
1
1
1
dc
b
6
1
1
dc
b
4
1
1
dc
b
1
3
1
dc
b
2
1
1
dc
b
4
2
1
dc
b
8
1
1
dc
b
0
0
0
dc
b
0
0
0
Form manager
*
MENU
BAR
. .30*
*
MENU
ICHeck.. . .31*
*
MENU
IENable. . .32*
*
MENU
TNOrmal. . .33*
*
MENU
TEXt
. .34*
*
MENU
REGister . .35*
OBJC_ADD
40*
OBJC_DELete.... 41*
OBJC_DRAw
42*
OBJC_FINd
43*
OBJC_OFFset....44*
OBJC_ORDer
45*
OBJC_EDIt
46*
OBJC_CHAnge. ...47*
dc.b
1
1
1
*
FORM
DO
. .50
dc.b
9
1
1
* FORM DIAlog.
. .51
dc.b
1
1
1
*
FORM
ALErt..
. .52
dc.b
1
1
0
*
FORM
ERRor..
. .53
dc.b
0
5
1
*
FORM
CENtre.
. .54
dc.b
0
0
0
*
dc.b
0
0
0
*
dc.b
0
0
0
*
dc.b
0
0
0
*
dc.b
0,0,0
Dialog manager
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
dc
b
0
0
0
Example Programs
GST
Metacomco
Seka
L.5

<!-- source-page: 362 -->
## Page 362

The Concise Atari ST Reference Guide
* Digital Research
*
* Graphics manager
Hisoft
GST
Metacomco
dc.b 4,3,0
* GRAF
RUBberbox.70*
dc.b 8,3,0
* GRAF DRAgbox...71*
dc.b
6,1,0
*
GRAF
MOVebox...72*
dc. b
8,1,0
*
GRAF
GROwbox...73*
dc.b 8,1,0
*
GRAF
SHRinkbox.74*
dc.b
4,1,1
*
GRAF
WATchbOX..75*
dc.b 3,1,1
* GRAF
SLIdebox..76*
dc. b
0,5,0
*
GRAF
HANdle. . . .77 *
dc. b
1,1,1
* GRAF
MOUse
78*
dc. b
0,5,0
* GRAF
MKState...79*
* Scrap manager
dc.b 0,1,1
*
SCRP
REAd...
. .80
dc.b
0, 1, 1
*
SCRP
WRIte..
. .81
dc.b 0,0,0
*
dc.b 0,0,0
*
dc.b 0,0,0
*
dc.b 0,0,0
*
dc.b 0,0,0
*
dc.b
0,0,0
*
dc.b 0,0,0
*
dc.b 0,0,0
*
File
selector manager
dc.b 0,2,2
dc.b 0,0,0
dc. b
0,0,0
dc.b 0,0,0
dc.b 0,0,0
dc.b
0,0,0
dc.b
0,0,0
dc.b
0,0,0
dc.b
0,0,0
dc.b
0,0,0
Window manager
L.6
*
FSEL
INPut.
.90*
dc. b
5,1,0
*
WIND
CREate.
.100*
dc. b
5,1,0
*
WIND
OPEn...
.101*
dc. b
1,1,0
*
WIND
CLOse..
.102*
dc. b
1,1,0
*
WIND
DELete.
.103*
dc. b 2,5,0
*
WIND
GET....
.104*
dc.b 6,1,0
*
WIND
SET ....
.105*
dc.b 2,1,0
*
WIND
FINd...
.106*
dc.b
1,1,0
*
WIND
UPDate.
.107*
dc.b 6,5,0
*
WIND
CALc...
.108*
dc.b 0,0,0
*
A

<!-- source-page: 363 -->
## Page 363

Example Programs
* Digital Research
*
Hisoft
GST
Metacomco
Seka
*
Resource
*
manager
dc.b
0,1,1
*
RSRC
LOAd
110*
dc.b 0,1,0
*
RSRC
FREe
111*
dc.b 2,1,0
*
RSRC_GADdress
112*
dc.b 2,1,1
*
RSRC_SADdress
113*
dc.b
1,1,1
*
RSRC_OBFix...
114*
dc.b 0,0,0
*
*
dc.b
0,0,0
*
*
dc.b
0,0,0
*
*
dc.b 0,0,0
*
*
dc.b 0,0,0
*
*
* Shell manager
dc.b
0, 1,2
*
SHEL
REAd
120*
dc.b 3,1,2
*
SHEL_WRIte. ...121*
dc.b
1,1,1
A
*
dc.b 1,1,1
*
*
dc.b
0, 1, 1
*
SHEL FINd
124*
dc.b
0, 1,2
*
SHEL_ENVrn... .125*
*
*
end
The object file is used as the first file in the link to produce an Atari ST
program file, say myprog, that accesses the DR GEM libraries i.e:
either DR
as68 -1 -u apstart.s
or Metacomco
assem.prg apstart.asm opt
j
followed by the linking of the main program file (see following example) to
the header and the DR library files.
Link68
[u] myprog.68=apstart myprog.o vdibind aesbind
Relmod myprog
Delete all temporary files, leaving either an application file myprog.prg
(which may be run by double clicking the icon in the directory listing) or an
accessory file which must be renamed myprog.acc. Reboot the system and run
the file by clicking the icon in the list of 'Desk' accessory files.
Remember to initially compile and run accessories as applications to debug
them.
L.7

<!-- source-page: 364 -->
## Page 364

The Concise Atari ST Reference Guide
GEM demonstration program
To use GEM directly, push the function parameters onto the stack in the
order given by the GEM VDI and GEM AES tables, ensuring that the correct size
of parameter is pushed.
The following program, which may be written in either DR or Metacomco
macro assembler but must use the DR link68 linker, lists in descending order the
TOS error codes in dialog boxes, the user stepping from one code to the next via
the mouse or the 'return' key.
* Digital Research
*
Hisoft
GST
Metacomco
Seka
*
*
n.a
n.a
n.a
* Demo GEM program
*
globl
main
*
*
. xdef
globl
form err
*
*
. xref
globl
appl ini
A
*
.
xref
globl _appl_exi
*
*
*
. xref
text
*
.
The
*
*
Metacomco
main:
*
.external
jsr
appl
ini
*
.symbol
*
*
.
names
move.w #63,d4
*
Error
start
#
*
.
are
loop:
move.w d4,temp
*
Save
it
*
.limited
move.w d4, -(sp)
*
Stack
it
*
. to
8
jsr
form err
*
What
is
it
*
characters
add.w #2,sp
*
Tidy
it
*
.
i .e
move.w temp,d4
*
Recover
it
*
dbra d4,loop
*
and next
*
form er
jsr
appl exi
*
Controlled exit
*
_appl_in
rts
*
_appl_ex
bss
*
temp:
ds.w
1
*
end
The file may be assembled using either
DR-
as68
-1
-u -p myprog.s
or
Metacomcoassem myprog.asm opt
j
Both programs are linked with the Digital Research link68 linker i.e:
link68
[s,u] myprog.6 8k=apstart,myprog.o,aesbind
and finally relocated by:
relmod myprog
L.8

<!-- source-page: 365 -->
## Page 365

Example Programs
GEM
demonstration
assembly
program
It is possible to write assembly language programs that do not use the DR
GEM bindings but simply access the functions via the Extended BDOS TRAP #2
calls. The following example shell shows a technique that will enable the
programmer to create a window, do some work in it, and then make a controlled
exit.
Note: Although the window is created with the sizing diamond and sliders,
no code has been written to handle the screen managers requests for change; if
these functions are activated they are ignored. If the cursor is active (as in this
program) and covers part of the foreground content of the screen when the
program is loaded, it will leave a hole when moved.
* Digital Research
*
Hisoft
*
* Assembler GEM program
* Size the
job and free back to GEMDOS
unused memory
text
move.l
a7,a5
*
curr
-
a5
move.l #ustk,a7
* set
local
stk
move.l 4(a5),a5
* get
base page
move.l $c(a5),d0
* text segment
add.l $14(a5),d0
* data
segment
add.l $lc(a5),d0
* uninitialized
add.l #5100,dO
move.1 dO,-(sp)
move.l a5,-(sp)
move dO,-(sp)
move #$4a,-(sp)
trap #1
add.l
#$c,sp
jsr start
move.1
#$0, -(sp)
trap #$1
* basepage
size
*
*free
unused mem
*
* tidy stack
*
ret
to
GEMDOS
* Technique for setting up VDI
& AES
arrays
* Initialize AES
arrays
start:
jsr ini_aes
*
*
section
c
Metacomco
.
code
L.9

<!-- source-page: 366 -->
## Page 366

The Concise Atari ST Reference Guide
* Digital Research
*
* Call
APPL_INI
(1st call)
*
appl_ini:
move.w #$a,control
move.w #$0,control+2
move.w #$l,control+4
move.w #50,control+6
jsr
aes
tst.w int_ou
bpl
graf_han
rts
*
* Call GRAF_HAN to get name of the currently opened window, pg 5.26
graf_han:
move.w #77,control
move.w #$0,control+2
move.w #$5,control+4
move.w #$0,control+6
jsr aes
move.w int_ou,handle
*
* Initialize VDI arrays
jsr ini_vdi
* Open virtual workstation
v_opnvwk:
move.w #100,contrl
move.w #0,contrl+2
move.w #11,contrl+6
move.w handle,contrl+12
* 11
input parameters
move.w #1,
move.w #1,
move.w
#1
move.w #1,
move.w #1,
move.w #1,
move.w #1,
move.w #1,
move.w #1|
move.w #1(
move.w #2,
jsr vdi
intin
intin+2
intin+4
intin+6
intin+8
intin+10
intin+12
intin+14
intin+16
intin+18
intin+20
*drive
id
*line type
*line
color
*marker type
♦marker color
*text
face
*text
color
♦interior fill
*fill
index
*fill
color
*NDC/RC
Hisoft
pg
5.6
* pg 4.9
Save virtual
screen workstation device
handle
move.w contrl+12,vhandl
*
tst.w contrl+12
*
beq appl_exi
*
L.10
GST
Metacomco

<!-- source-page: 367 -->
## Page 367

Example Programs
Digital Research
Hisoft
.
GST
* Test here
for screen resolution and number of colors available
* (even in mono).
Load appropriate resource
file using the AES
* RSRC_LOA call if necessary.
*
* Get
max possible size of window
max_wind:
move.w vhandl,int_in
move.w #7,int_in+2
jsr wind_get
tst.w int_ou
beq appl_exi
*
sizes
*
Calculate
work
area
of window
*
move.w #0,int_in
jsr wind_cal
tst-w int_ou
beq appl_exi
*
Calc new window bordered area
move.w #l,int_in
jsr wind_cal
tst.w int_ou
beq appl_exi
* Alloc space
for
full size window
wind_cre:
move.w #100,control
move.w #$5,control+2
move.w #$1,control+4
move.w #$0,control+6
*
move.w #$0fff,int_in
move.w int_ou+2,int_in+2
move.w int_ou+4,int_in+4
move.w int_ou+6,int_in+6
move.w int_ou+8,int_in+8
jsr aes
*
move.w int_ou,whandl
tst.w int_ou
beq appl_exi
* Open window at
last
*
wind_ope:
move.w #101,control
move.w #$5,control+2
move.w #$1,control+4
move.w #$0,control+6
edges
xl
yi
x2
y2
* pg 5.29
* pg 5.2 9
Metacomco
Seka
L.11

<!-- source-page: 368 -->
## Page 368

The Concise Atari ST Reference Guide
* Digital Research
*
Hisoft
.
*
* Absolute parameters
*
move.w whandl,int_in
*
move.w #0, int__in+2 * xl
*
move.w #0,int_in+4* yl
*
move.w #280,int_in+6
* x2
*
move.w #160,int_in+8
* y2
*
jsr
aes
*
tst.w int_ou
*
beq appl_exi
*
*
* Do
something on
the
screen,
this
is
where your program starts.
*
Set
screen parameters
*
vsf_inte:
move.w #23,contrl
move.w #0,contrl+2
move.w #l,contrl+6
move.w whandl,contrl+12
move.w #1,intin
jsr vdi
* Style
*
vsf_styl:
move.w #24,contrl
move.w #0,contrl+2
move.w #l,contrl+6
move.w whandl,contrl+12
move.w #1,intin
jsr
vdi
*
Colour
vsf_colo:
move.w #25,contrl
move.w #0,contrl+2
move.w #l,contrl+6
move.w whandl,contrl+12
*
move.w #1,intin
* black
jsr vdi
* Set mouse style
graf_mou:
move.w #78,control
move.w #$1,control+2
move.w #$1,control+4
move.w #$1,control+6
L12
* pg 4.15
pg 4.15
* pg 4.15
* pg 5.2 6
Metacomco

<!-- source-page: 369 -->
## Page 369

* Digital Research
move.w #$0,int_in
jsr
aes
tst.w int_ou
beq appl_exi
*
* Get position
of
window work area
*
where:
move.w whandl,int_in
move.w #4,int_in+2
* work area
jsr wind_get
tst. w int_ou
beq appl_exi
* Get
coordinates
within
work area
add.w #35,int_ou+2
add.w #35,int_ou+4
sub.w #50,int_ou+6
sub.w #50,int_ou+8
* Draw a shape
from those coords
*
v_rfbox:
move.w #11,contrl
move.w #2,contrl+2
move.w #0,contrl+6
move.w #9,contrl+10
move.w whandl,contrl+12
Hisoft
.
pg 4.12
* Absolute coords —
not window the reason for this patch
move.w int_ou+2,ptsin
*
move.w int_ou+4,ptsin+2
*
move.w int_ou+6,ptsin+4
*
move.w int_ou+8,ptsin+6
*
*
jsr
vdi
*
*
* Wait for a sign - about
1 minute
evnt_tim:
move.w #24,control*
move.w #$2,control+2
move.w #$1,control+4
move.w #$0,control+6
move.w #$ffff,int_in
move.w #$0000,int_in+2
jsr
aes
*Lo
•Hi
pg 5.9
End of program,
shut the
window in a controlled manner
Example Programs
Metacomco
L.13

<!-- source-page: 370 -->
## Page 370

The Concise Atari ST Reference Guide
Digital Research
*
Hisoft
Close v_scrn Stop o/p (Shut window down)
* pg 4.9
_clsvwk:
move.w #101,contrl
*
move.w #0,contrl+2
*
move.w #0,contrl+6
*
move.w vhandl,contrl+12
*
* Close
window
wind_clo:
move.w #102,control
move.w #$1,control+2
move.w #$1,control+4
move.w #50,control+6
*
move.w whandl,int_in
jsr aes
tst.w int_ou
beq appl_exi
*
* Deallocate
space and handle
*
wind_del:
move.w #103,control
move.w #S1,control+2
move.w #$1,control+4
move.w #50,control+6
•
move.w whandl,int_in
jsr
aes
tst.w int_ou
beq appl_exi
*
* Call APPL_EXI
(Last call)
*
appl_exi:
move.w #19,control
move.w #50,control+2
move.w #51,control+4
move.w #50,control+6
*
*
Subroutines
*
*
Get
window data
A
wind_get:
move.w #104,control
move.w #52,control+2
move.w #55,control+4
move.w #50,control+6
L.14
pg
5.29
* pg 5.2 9
* pg
5.7
pg 5.30
GST
Metacomco
Seka

<!-- source-page: 371 -->
## Page 371

* Digital Research
move.w vhandl,int_in
move.w #7,int_in+2
jsr
aes
rts
rem
out
Example Programs
Metacomco
Seka
* Calculate window work area based on
facilities:
title,
*
scroll
bar
etc.
wind_cal:
move.w #108, control
move.w #56,control+2
move.w #55,control+4
move.w #50,control+6
*
*
move.w #0,int_in
move.w #50fff,int_in+2
move.w int_ou+2,int_in+4
move.w int_ou+4,int_in+6
move.w int_ou+6,int_in+8
move.w int_ou+8,int_in+10
jsr
aes
rts
* VDI parameter block call
vdi:
rem out
edges
xl
yi
x2
*y2
move.l #contrl,pblock
move.l #pblock,dl
move.l
#115,dO
trap #52
rts
*
reset
AES parameter block call
move.l
#control,_c
move.l #_c,dl
move.l
#200,dO
trap #52
rts
Set
up
AES array
mi
aes:
move
1
♦control
c
move
1
#global,
c + 4
move
1
#int
in,
c+8
move
1
#int
ou,
c+12
move
1
#addr
in
c+16
move
1
#addr
ou
c+20
rts
pg 5.32
zc
#ZC
zc
zc + 4
zc+8
zc+12
zc+16
zc+20
zc
#zc
ZC
zc+4
zc+8
zc+12
zc+16
zc+20
L.15

<!-- source-page: 372 -->
## Page 372

The Concise Atari ST Reference Guide
* Digital Research
* Set
up VDI
array
Hisoft
Metacomco
ini
vdi:
move
1
#contrl,pblock
move
1
#intin,pblock+4
move
1 #ptsin,pblock+8
move
1
♦intout,pblock+12
move
1
#ptsout,pblock+16
rts
Make space
for the arrays. You must ensure these are large
enough to hold the array's data. Be especially careful regarding
the spelling of the array names.
'New TOS'
requires larger VDI
arrays
than previous versions of the OS.
bss
even
•
ds
1
256
ustk:
ds
1
1
pblock:
ds .1
5
contrl:
ds
w
12
intin:
ds
w
30
ptsin:
ds
w
30
intout:
ds
w
45
ptsout:
ds
w
12
handle:
ds
w
1
vhandl:
ds
w
1
whandl:
ds
w
1
_c:
ds
1
6
control:
ds
w
5
global:
ds
w
16
int
in:
ds
w
16
int_ou:
ds
w
7
addr_in:
ds
1
2
addr
ou:
ds
1
1
XXX
XXX
section
d
.
XXX
data
XXX
blk
blk
.
blk.l
.
blk.w
.
blk.w
.
blk.w
.
blk.w
.
blk.w
.
blk.w
.
blk.w
.
blk.w
.zc blk.
. blk.w
. blk.w
.
blk.w
.
blk.w
. blk.l
. blk.l
The program may be assembled and linked (if required) using the assembler
calling procedures outlined in Appendix_K
L.16

<!-- source-page: 373 -->
## Page 373

Example Programs
TOS
Display demonstration program
The following program shows a typical Atari TOS file, which simply inverts
the current mono display color for those programmers who,like myself, prefer
white on black or toggles the border of a color display.
Digital Research
Demo Atari TOS program
text
move.l
a7,a5
move.l #ustk,a7
*
move.1
4 (a5),a5
move.l
5c(a5),dO
add.l 514(a5),d0
add.l Slc(a5),d0
add.l #5100,dO
move.l dO,-(sp)
move.l a5,-(sp)
move dO,-(sp)
move #54a,-(sp)
*
trap #1
*
add.l #5c,sp
jsr start
*
move.l #50,-(sp)
*
trap #51
set
-
a7
free
unused
back
to
GEM
jump to prg
terminate
clr.1 -(sp)
move.w #32,
trap #1
move.1 dO,a1
move.w #-l,d0
jsr
newcol
eori
#l,d0
jsr newcol
(sp)
move.1 al,-(sp)
move.w #32,-(sp)
trap #1
move.l
#0,- (a7)
trap #1
* set
super
* get/set col
*
set
user
*
Hisoft
.
GST
Metacomco
Seka
section
c
code
L.17

<!-- source-page: 374 -->
## Page 374

The Concise Atari ST Reference Guide
* Digital Research
*
Hisoft
.
GST
Metacomco
Seka
newcol:
move.w dO,-(sp)
move.w #0,-(sp)
move.w #7,-(sp)
trap #14
add.w #6,sp
rts
bss
ds.l
2 0
ustk:
ds.l
1
end
* get
color
xxx
section d
Theabove programis assembled and linkedwithoutany otherfiles.
L.18
data
blk.l
blk.l

<!-- source-page: 375 -->
## Page 375

Example Programs
TOS header file
Thefollowing shows a typicalAtariTOS header file that may be incorporated
in a user-writtenprogram to provide access to the basepage offset variables.
************
***********
* Base page
format
initialised by
BDOS
****************
k*******
**********
ltpa
equ
0
htpa
equ
4
lcode
equ
8
codelen
equ 12
ldata
equ
16
datalen
equ 2 0
lbss
equ 24
bsslen
*
equ 28
*
either
*
GEMDOS
*env
*
equ
4 4
*
or
Ata ri
OS
freelen
equ
32
ldriv
equ 36
resvd
equ 37
fcb2
equ
56
fcbl
equ
92
*
common
t ail
command
equ
12
Low
TPA address
High TPA address
+
1
Text
segment
start
Length
of
text
segment
Initialized data
segment
start
Length of initialized data
BSS segment
start
Length of uninitialized data
* Environment string pntr
(GEMDOS)
* Free memory length after BSS
* Drive
from which program loaded
*
Reserved
* 2nd parsed fcb
*
1st
parsed fcb
Command tail
Although it is good practice to size the memory requirements of you
program and return the unused memory to GEMDOS, programs can be writte:
without if they return to the GEM desktop.
GEM allocates all the memory to the program, only if it multitasks or cal
and loads another program is there any real need to return spare memory.
L.19

<!-- source-page: 376 -->
## Page 376

The Concise Atari ST Reference Guide
Character printing program
This simple program demonstrates some of the methods available for
printing to the VT52 screen. The compiled program may be installed as:
A 'GEM program' - the busy bee cursor will appear in the display and leave a
hole when moved.
A 'TOS program' - with flashing cursor, the cursor may be hidden quite
easily by incorporating within the 'prdat' string the hide cursor escape code as
specified in Appendix C.
Digital Research
*
Hisoft
.
GST
Monochrome TOS VT52
screen print
program
(0,0 to 24,79)
(For colour,
set max
print
width
in 'prdat'
to 39)
*
xxx
section
c
text
* GEM BIOS type print
*
clr.l
d4
clr.l
d5
lea prdat,a4
move.b
(a4),d4
cloop:
adda.l
#l,a4
move.b
(a4),d5
move.w d5,-(sp)
move.w #2,-(sp)
move.w #3,-(sp)
trap #13
add.w #6,sp
dbra d4,cloop
*
* GEMDOS type print
*
lea mess,aO
move.l aO,-(sp)
move.w #9,-(sp)
trap
#1
add.w #6,sp
exlp:
dloop:
move.l
#200,dl
move.l
#-l,d0
dbra dO,dloop
dbra dl,exlp
move.l
#0,-(a7)
trap
#1
rts
L.20
*
Clear
d4
*
Clear
d5
*
Get
data
address
*
Data
count-1
*
Get
next
* Getchar byte
*
Stack
char.w
*
Send
to
console
*
Set
bconout 0
*
Call
it
* Tidy stack
* loop
for next
* GetASCII
string
*
Stack
it
*
set
conws 0
*
Call
it
* Tidy stack
*
Wait
*
GEM return
*
*
Return
Metacomco
Seka
.
code

<!-- source-page: 377 -->
## Page 377

Example Programs
Digital Research
data
even
Hisoft
.
GST
Metacomco
Seka
xxx
section
dl
xxx
XXX
.
xxx
.
xxx
xxx
* VT52 screen location character equivalents
*
*!
"
#
5
% S
'
(
)
*
+ ,-.
/0123456
*0, 1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
*789:;<
=
>?8ABC
DEFGHIJ
*23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42
*KLMNOPQRSTUVW
XYZ[\]
* 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61
*"
'abcdefghi
jklmno
* 62, 63, 64, 65, 66, 67, 68,69,70,71,72,73,74,75,76,77,78,79
* Data
string to print
(See Appendix C for codes)
prdat:dc.b
50
*
dc.b
27, 'E'
*
Clear
screen
dc.b
27, 'b' , 0
*
foregnd col white
dc.b
27, 'c' ,1
*
backgnd col black
dc.b
27, 'Y
0,0'
*
Set
cursor
at
0,0
dc.b
27, 'Y!!1,1'
A
Set
cursor
at
1,1
dc.b
27, 'b' ,1
*
foregnd col black
dc.b 27, 'C ,0
*
backgnd col
white
dc.b 27, 'Y8f24, 69 ' *
Set
curs
@
24,69
dc.b
27, 'p'
*
Inverse video
dc.b
27, ' I'
*
Up
1 line
dc.b
'hi
;t
*
Say something witty
dc.b 27, ' Y, 4'
*
set cursor
at
12,20
dc.b
27, 'q'
*
Reset
video
section
d2
Print null terminated string - uses ASCII
& control codes
dc.b
'hello'
dc.b
10,10,7
dc.b
'hello'
dc.b
10
dc.b
'hello'
dc.b
10,13
dc.b
'hello'
dc.b
0
end
* Alternative print
*
method
for
screen
* printing.
*
Text
*
linefeed
* carriage
return
*
and
a
bell
* End of
string
L.21

<!-- source-page: 378 -->
## Page 378

The Concise Atari ST Reference Guide
Sound demonstration program
This program provides a basic introduction to 'sound' programming on the
AtariST; whereexperimentation witheach of thesoundsprovided is perhaps the
bestapproach to understanding theeffects ofeach argument.
Takecare of the following general points:
Userstack: Make sure it is large enough. It grows down in memory and it can
overwrite the data area.
Timing: It is necessary to provide a delay before an exit back to GEMDOS,
TOS could reallocate the sound data bytesspace.
* Digital Research
*
* Experimental TOS sounds program
*
text
move.l
a7,a5
*
create
move.l
#ustk,a7
*
space
for
move.l
4(a5),a5
*
program
move.1 5c(a5),dO
add.l 514(a5),d0
add.l 51c(a5),d0
add.l #5100,dO
move.1 dO,-(sp)
move.1 a5,-(sp)
move dO,-(sp)
move #54a,-(sp)
trap
#1
*
add.l
#5c,sp
start
move.l
#soundl,al
*
it
jsr
dosound
*
move.l
#150,dl
*
15
sees
loopo
moveq #-l,d2
*
wait
for
loopi
dbra d2,loopi
*
finish
*
dbra dl,loopo
exit:
clr.l
-(sp)
*
GEMDOS
ret
trap #51
rts
L.22
Hisoft
.
GST
Metacomco
Seka
section
c

<!-- source-page: 379 -->
## Page 379

Digital Research
dosound:
move
1 al,-(sp)
move w #32,-(sp)
trap #14
add. * #6,sp
rts
*
bss
*
even
ds.l
64
ustk
ds.l
1
*
data
even
*
*
Bell
soundl:
*
dc.b 0,534
dc.b
1,0
dc.b 2,0
dc.b 3,0
dc.b
4,0
dc.b 5,0
dc.b
6,0
dc.b 7,5fe
dc.b 8,510
dc.b
9,0
dc.b
10,0
dc.b
11,0
dc.b 12,510
dc.b 13,9
*
dc.b 130,100
*
sound2:
dc.b 0,5fe
dc.b 1,0
dc.b 2,0
dc.b 3,0
dc.b
4,0
dc.b 5,0
dc.b
6,0
dc.b 7,5fe
dc.b
8, 11
dc.b
9,0
dc.b
10,0
dc.b
11,0
dc.b
12,0
dc.b
13,0
dc.b
130,20
sound pointer
* Large enough not
*
*
to overwrite data*
*\
chan
A
*
*/
2150
hz
*
*
\
chan
*
*
/
B
*
*\
channel
*
*/
C
*
*
noise
*
* enable A only
*
* enable A envelope*
*
B
off
*
*
C
off
*
*\Single attack
*
**envelope shape
*
*/
1
0
0
1
*
* delay
*
*
Siren
*\
chan
A
*
*/ 440 hz High note*
*
\ chan
*
*
/
B
*
*\
channel
*
*/
C
*
*
noise
*
* enable A only
*
* A amplitude
*
*
B
off
*
*
C
off
*
*\
no
*
*
Ienvelope
*
*/ shape
*
Example Programs
GST
Metacomco
Seka
XXX
section
dl
data
xxx
.
xxx
xxx
XXX
blk.l
blk.l
xxx
section d2
code
xxx
.
xxx
xxx
xxx
L.23

<!-- source-page: 380 -->
## Page 380

The Concise Atari ST Reference Guide
* Digital Research
dc.b 0,556
dc.b
1,1
dc.b 130,20
*\
chan
A
Low note
*
*/
187
hz
*
dc.b 0,Sfe,l,0,130,20
dc.b
0,556, 1, 1,130,20
*High note
*Low note
dc.b 8,0,9,0
dc.b
130,50
*
silence
*
A
s
B
off
gunshot
dc.b 0,0,1,0,2,0,3,0,4,0,5,0
dc.b
6,15
dc.b 7,199
dc. b
8,16
dc.b
9,16
dc. b
10,16
dc.b
11,0
dc.b
12, 16
dc.b
13,0
dc.b 130,25
dc. b
8,0,9,0
dc.b
130,50
* medium noise period
* enable noise chans
A,B
s C
*
\ using
*
*
Ienvelope
*
*
/
control
*
*\ envelope period
*
*/
*
* one cycle decay
*
*
silence
*
A
4
B
off
* explosion
dc.b
0,0,1,0,2,0,3,0,4,0,5,0
dc. b
6,10
dc.b
7, 199
dc. b
8,16
dc.b
9,16
dc.b
10, 16
dc.b
11,0
dc.b
12, 80
dc.b
13,0
dc.b
130,120
* noise period
*
* enable
noise
chans
A,B
&
C
* \ using
*
*
I envelope
*
*
/
control
*
*\ envelope period
*
*
i
*
* one
cycle
decay
*
nd
*
silence
dc.b
8,0,9,0,10,0*
A
B
s
C
off
dc.b
130,100
*
L.24
Metacomco

<!-- source-page: 381 -->
## Page 381

'
Digital Research
*
sound5:
*
whistle
dc.b
0,0,1,0,2,0,3,0,4,0,5,0,6,0
dc.b
7,254
* enable tone
A only
dc. b
8, 15
*
*
dc.b
9,0,10,0,11,0,12,0,13,0
*
dc.b
128,60
* Initial tempreg
*
dc.b
129,0,-2,40
* reg-step-end
*
dc.b
130,2
*
*
exit
list
dc.b
7,255,8,0
dc.b
255,0
end
off
return
Example Programs
Hisoft
.
GST
Metacomco
Seka
L.25

<!-- source-page: 382 -->
## Page 382

The Concise Atari ST Reference Guide
Line-A parameter table
The following isthecomplete list oftheLine-A equates andfunctions. Itmay
be used as a standard assembler headerfile to Line-A programs.
***********************************************
*
* Line-A parameter table
*
***********************************************
V_CEL_HT
V_CEL_MX
V_CEL_MY
V_CEL_WR
V_COL_BG
V_COL_FG
V_CUR_AD
V_CUR_OFF
V_CUR_CX
V_CUR_CY
V_CUR_CNT
V_CUR_TIM
V_FNT_AD
V_FNT_ND
V_FNT_ST
V_FNT_WR
V_X_MAX
V_OFF_AD
V_STATUS
V_Y_MAX
*
VPLANES
VWRAP
CONTRL
INTIN
PTSIN
INTOUT
PTSOUT
COLBITO
COLBIT1
COLBIT2
COLBIT3
LSTLIN
LNMASK
WMODE
*
XI
Yl
X2
Y2
*
PATPTR
PATMSK
MFILL
CLIP
L.26
equ
-46
equ
-44
equ
-42
equ -40
equ
-38
equ
-36
equ
-34
equ
-30
equ
-28
equ -26
equ
-24
equ
-23
equ -22
equ
-18
equ
-16
equ
-14
equ -12
equ
-10
equ -6
equ
-4
equ
0
equ
2
equ
4
equ
8
equ
12
equ
16
equ
20
equ
24
equ
26
equ
28
equ
30
equ
32
equ
34
equ
36
equ
38
equ
40
equ
42
equ
44
equ
46
equ
50
equ
52
equ
54
.w
.w
.w
.w
.w
.w
.L
.w
.w
.w
,B
.B
.L
.W
.w
.w
.w
.L
.w
,w
.w
.w
.L
.L
.L
.1
.L
.«
.W
.w
.w
.w
.w
.w
.w
.w
.w
.w
.L
.W
.W
.w
Pixel cell height
Max
cells
across
-1
Max cells high -1
Offset
to
next
cell
Background index color
Foreground index color
Current cursor address
Offset
to
1st
cell
X cursor position
Y cursor position
Cursor
flash interval
Cursor countdown timer
Font
address
Last
font
ASCII
code
1st
font
ASCII
code
Font
width
Max X pixel
scrn value
Font
offset
table
addr
Text status byte
Max Y pixel
scrn value
# video planes
# bytes/video
array pntrs
write
color
VDI
line style
Write mode
\
I coordinates
I
/
Curr fill
patt pntr
Len
fill patt mask
0_single plane
0_no clipping

<!-- source-page: 383 -->
## Page 383

Example Programs
XMINCL
YMINCL
XMAXCL
YMAXCL
XDDA
DDAINC
SCALDIR
*
MONO
SRCX
SRCY
DESTX
DESTY
DELX
DELY
FBASE
FWIDTH
STYLE
LITEMSK
SKEWMSK
WEIGHT
ROFF
LOFF
SCALE
CHUP
TEXTFG
SCRTCHP
SCRPT2
TEXTBG
COPYTRAN
SEEDABORT
equ
56
equ 58
equ
60
equ
62
equ
64
equ
66
equ
68
equ
70
equ 72
equ
74
equ 7 6
equ 78
equ
80
equ
82
equ
84
equ
88
equ
90
equ
92
equ
94
equ
96
equ
98
equ 100
equ 102
equ
104
equ
106
equ
108
equ
112
equ
114
equ 116
equ 118
.w
\
.w
1
Clipping
.w
1
values
.w
/
.w
txtblt
x
dda
accum
.w
txtblt
scale
factor
.w
0
down
.w
0_font monospaced
.w
\
Coords
of
char
.w
/
in
font
form
.w
\ Coords
of
char
.w
/ on
screen
.w
Char width
.w
Char height
.L
Font form pointer
.W
width
.w
style
,M
lighten text mask
.W
skew text
mask
.w
extra
text
width
.w
high offset skew
.w
low offset
skew
,w
0 no
scaling
.w
0
horiz
orientation
.w
Text
foreground color
.L
Text
effects buffer
,W
Offset
to
scale buffer
.W
Text background color
,w
Copy raster type
flag
.w
Abort
fill
routine ptr
***********************************************
*
Line-A function calls
***********************
init
putpix
getpix
abline
habline
rectfill
polyfill
bitblt
textblt
showcur
hidecur
chgcur
unsprite
drsprite
copyrstr
seedfill
****************
equ
5a000
equ
init+1
*
put pixel
equ
init+2
*
get
pixel
equ
init+3
*
draw
a
line
equ
init+4
*
horizontal
line
equ
init+5
*
draw filled rectangle
equ
init+6
*
draw
1 line poly fill
equ
init+7
*
bit
block transfer
equ
init+8
*
text
block
transfer
equ
init+9
*
show mouse
equ
init+10
*
hide mouse
equ
init+11
*
transform mouse
form
equ
init+12
*
undraw previous
sprit
equ
init+13
*
draw sprite
equ
init+14
*
copy raster form
equ
init+15
*
polygon
fill
L.27

<!-- source-page: 384 -->
## Page 384

The Concise Atari ST Reference Guide
Sprite demonstration
The following Line-A program is deliberately compressed to show the small
number of lines of assembler used to control sprites. The program produces an
alternate black and white sprite crossing a monochrome screen.
* Digital Research
Hisoft
GST
Metacomco
*
initialize
init:
.
* undraw sprite unsprite:
* draw sprite drsprite:
* Max
X pixel scrn val V_X_MAX:
*
xxx
section
c
. code
init
equ
5a000
unsprite
equ
init+12
drsprite
*
equ
init+13
V_X_MAX
equ
-12
text
start:
clr.l
-(sp)
*
Set
move.w #520,-(sp)
*
super
trap #1
*
mode
addq.l
#6,sp
*
move.l d0,stksv
*
save
stack
move.w #0,olda
*
versn
flag
move.l
#0,a2
*
dew init
*
Init
move.1
a2, d2
*
aline
bne
a2ok
*
registers
lea #-60(al),a2
*
move.w #-l,olda
*
*
a2ok:
move.l S34(a2),a3
*
draw addr
(4*13)
move.w #v_X_MAX(a 0)
a5* get max width
move.w #0, dO
*
init
x
move.w #50,dl
A
init
y
move.w #10,d2
*
scan
count
lea
sprit,aO
*
sprite add
lea save,a2
*
bg savearea
movea.l a0,a4
*
sprite col
adda.l
#6,a4
*
*
pointer
setcol:
move.w
(a4),d3
*
get color
bne
white
*
move.l
#500010001 , (a4)* black
bra loop
*
color
white: move.l
#0, (a4)
*
set
white
loop: movem.l d0-d2/a0- a4
- (sp)*sav r
tst.w olda
*
test
versn
beq new
*
jsr
(a3)
*
old versn
bra
cont
*
new:
dc.w drsprite
*
new
versn
cont: move.w #2000, dO
*
-60(al),a2
>
V
X
MAX(aO) ,a5
L.28
.*]
*]
*]
.*]
*]

<!-- source-page: 385 -->
## Page 385

Example Programs
* Digital Research
Hisoft
Metacomco
sprit
ghoul
dbra d0,wait
*
delay
*
lea save,a2
*
bg savarea
*
dew unsprite
*
*
movem.l
(sp)+
dO- d2/a0-a4*
unsave
r
*
add.w #l,dO
*
slide over
*
cmp.w a5,d0
*
screen
*
ble loop
*
*
move
w #0,d0
*
init
x
*
add.w #10,dl
*
drop
y
*
sub.w #l,d2
*
count
down
*
bne setcol
*
and again
*
move
1 stksv, -(sp)* back
*
move
w #520,- (sp)
*
to
*
trap
#1
*
user
*
addq
1 #6,sp
A
mode
*
move
w #0,-(sp)
*
back
*
trap
#1
*
to
GEM
*
data
*
xxx
section
d
even
*
xxx
.
xxx
dc.
•i
0,0
*
x,y
-*
dew -1
*
l_vdi,
-1
xor
dew
0
*
bg col
*
dc. w
0
*
fg col
*
dew 5ffff
*
dew 503c0
*
dew Sffff
dc. w 50ff0
*
dc. w 5ffff
dc. w 51ff8
*
dc. w 5ffff
dew 53ffc
*
dew 5ffff
dew S73ce
*
dew 5ff ff
dew 573ce
*
dc. w 5ffff
dc. w Sffff
*
dew 5ffff
dc. w 5ffff
*
dc. w 5ffff
dew 5fbdf
*
dew 5ffff
dew 5f81f
*
dew Sffff
dc. w Sffff
*
dc. w Sffff
dew S67e6
*
xxx
xxx
L.29
.*]
.*]
.*]
*]

<!-- source-page: 386 -->
## Page 386

The Concise Atari ST Reference Guide
Digital Research
dew Sffff
dew 5300c
dew Sffff
dew Slff8
dew Sffff
dew S0420
dew Sffff
dew 51818
bss
even
stksv : ds.l
1
save:
ds.b
7 4
olda :
ds.w
1
end
Hisoft
GST
xxx
xxx
section
d
.
xxx
Metacomco
Seka
data
xxx
blk.l
.
*1
blk.b
.
blk.w
.
*2
*1 There is no requirement to run this program in supervisor mode, these
lines of code may be omitted.
*2 Some versions of the disk based TOS incorrectly return the value of A2.
These lines of code are not required by ROMbased versions of the ST.
*3 Theuse of the following codeprovidesmorestablesprites:
MOVE #37,-(sp)
TRAP
#14
ADDQ #2,sp
* wait
for vblank
*
XBIOS
call
* tidy stack
The programmer might also contemplate hiding the busy-bee cursor.
L.30

<!-- source-page: 387 -->
## Page 387

Glossary
Appendix M
Glossary of abbreviations
M.1

<!-- source-page: 388 -->
## Page 388

The Concise Atari ST Reference Guide
ADE
ASCII decimal equivalent
AES
Application environment services
ACIA
Asynchronous communications interface adaptor
ANSI
American national standards institute
ASCII
Americanstandard codefor information interchange
AUX
Auxilary
BCD
Binary coded decimal
BDOS
Basic disk operating system
BIOS
Basic input/output system
BPB
BIOS parameter block
BSS
Block storage segment
CCP
Console command processor
CCR
Condition code register
CON
Console
CP/M
Control program for microcomputers
CPU
Central processing unit
CRC
Cyclic redundancy check
CTS
Clear to send
DCD
Data carrier detect
DIR
Directory
DMA
Direct memory access
DOS
Disk operating system
DPB
Disk parameter block
DS
Double sided
DTR
Data terminal ready
D/A
Digital to analogue
EPB
Exception parameter block
FAT
File allocation table
FCB
File control block
FDC
Floppy disk controller
FIFO
First in, first out register
GDOS
Graphics device operating system
GEM
Graphics environment manager
GIOS
Graphics input/output system
GP
General purpose
Grd
Ground
GSX
Graphic system extension
M.2

<!-- source-page: 389 -->
## Page 389

HDC
ID
ikbd
IPL
I/O
LPB
LSB
LST
MD
MFDB
MFP
MIDI
MS-DOS
MSB
NDC
Hard disk controller
Identification
Intelligent keyboard
Interrupt level
Input/output
Load parameter block
Least significant byte/bit
List
Memory descriptor
Memory form definition block
Multi function peripheral
Musical instruments digital interface
Microsoft disk operating system
Most significant bit
Normalized device coordinates
OEM
Other equipment manufacturer
OS
Operating system
OSC
Oscillator
PC
Program counter
PC-DOS
IBM personal computer operating system
pk-pk
Peak to peak
PSG
Programmable sound generator
RAM
Random access memory
RC
Raster coordinate
RF
Radio frequency
RGB
Red-green-blue
Ri
Ring
ROM
Read only memory
RSX
Resident system extension
RTE
Return from exception
RTS
Return from subroutine
Rx
Receive
Glossary
M.3

<!-- source-page: 390 -->
## Page 390

The Concise Atari ST Reference Guide
SASI
Shugart associates standard interface
SCSI
Small computer systems interface
SP
Stack pointer
SR
Status register
SS
Single sided
SSP
Supervisor stack pointer
TOS
The operating system
TPA
Transient program area
TTL
Transistor-transistor logic
Tx
Transmit
ULA
Uncommitted logicarray
USART
Universal synchronous/asynchronous receiver-transmitter
USP
User stack pointer
VBI
Vertical blank interrupt
VDI
Virtual device interface
VLSI
Very large scale integration
M.4

<!-- source-page: 391 -->
## Page 391

Schematic diagrams
Appendix N
Schematic diagrams
N.1

<!-- source-page: 392 -->
## Page 392

The Concise Atari ST Reference Guide
2.4576 Mhz
HD
4 Mhz
Reset
500
N.2
Atari ST schematic diagram
MC68901
Mono monitor
+gv
Opto isolator
coupler

<!-- source-page: 393 -->
## Page 393

MMU
4M
MADO
8M
16Mhz
MAD9
A21
D7
DO
wdat
rdat
latch
DO
DO
D7
D7
DO
DO
D7
D7
AO
D7
AO
DO
D7
DO
D7
*!-.
D7
DO
DO
D7
D7
373
244
IPL1
IPL2
8MHz
A1
DO
D15
A23
MC68000
AO
AO
AO
RAM
/
AO
DO
DO
\
DO
A9
D7
D7
D7
AO
AO
DO
DO
DO
A9
A9
D7
D7
D7
Shifter
'DO
D15
elk
16MHz
32MHz
R
G
,
A5
/
B
AO
Mono
A1
ROMO
ROM1
ROM2
ROM3
ROM4
6850CS
MFPcs
SNDcs
FCS
elk
D7
DO
A 9
D7
DO
D7
AO
DO
D7
A23
reset
FC2
FC1
FCO
_2MHz
500KHZ
GLUE
Schematic diagrams
AO
A9
A9
D7
D7
AO
DO
A9
D7
D7
ROM
DO
D7
AO
DO
A1
A15
ROM3
ROM4
uds
Ids
DO
D15
ROM port
AO
DO
D7
DC
D7
DO
D7
DO
D7
N.3

<!-- source-page: 394 -->
## Page 394

The Concise Atari ST Reference Guide
31
N.4
128K ROM cartridge
37
LDS
4 off 27256 ROM's
+5v
Vcc
A14
Vpp
0E
4
CE
3
ROM
D7
Low byte
DO
AO
$FB0000
t +5v
L3:
Vcc
A14
Vpp
0E
o
CE
3
ROM
D15
High byte
D8
AO
$FB0000
©
&
-9-Q.
33
+5v Ol
Vcc
A14
Vpp
CE
4
ROM
D7
Low byte
DO
AO
$FA0000
35
UDS
t +5v r^
v- Vcc
A14
Vpp
CE
4
ROM
D15
High byte
D8
AO
\
$FA0000
+§v
14
01 <
31 333537
7
6
5
4
10
14
13 8
9
11
3
15
12
12 10 8
6 4
2 0
(
13
11
9
7
5
3
1
see
ddddddddobbbbbbodooddddddddddobbbbddoddd
12 4
6
8
10
15
20
25
30
35
Data bus
Address bus
40

<!-- source-page: 395 -->
## Page 395

Index
Index

<!-- source-page: 396 -->
## Page 396

The Concise Atari ST Reference Guide
ACIA control/status register 1.28
Add and add extended instructions H.ll
Add Quick, subtract quick, set conditionally
and decrement instructions H.7
Address Mode BASIC equivalents G.21
Address modes encoding H.14
Address registers G.25
AES parameter block 5.3 F.8
AES parameter block sizes 5.5
Alerts 5.22
Allowable address mode types G.22
AND, multiply, add decimal, exchange
instructions H.ll
Animation 2.15
Application environment services (AES)2.5
Application header block F.13
Application interrupts A.3
Application library 5.6
Application programs 2.5
Ascii codes D.3
Assembler conversions K.ll
Assembler directives compatibility K.10
Atari MC68000 assemblers K.2
Atari Operating System 3.2
Atari ST block diagram 1.2
Atari ST console I/O 1.6
Atari ST Hardware
Attribute functions 4.13
Attribute table 4.4
B
Base page 2.21
Base page format F.5
BASIC assembler J.6
Basic calling procedure K.14
Basicdisk operating system (BDOS) 2.4
BASIC example J.4
BASIC GEM J.2
Basicinput/output system (BIOS) 2.4
BCD and BIT data types G.24
BIOS (Trap #13) E.2
BIOScalls (trap #13) 3.3
BIOS error codes 1.2
Bit image 4.33
Bit manipulation, move peripheral and
immediate instructions H.4
Bitblt 7.5
Bitblt table 7.10
Blitter access 8.3
Blitter configuration registers B.5
Blitter control/status 8.3
Blitter flow diagram 8.4
Blitter operation 8.2
Blitter parameter table 8.6
Bomb error codes A.6
Boot loader 2.34
Boot ROM 2.35
Boot sector parameter block F.2
Boot sectors 2.32
Branch conditionally instructions H.8
BUSY bit 8.3
Byte, word and longword G.24
C compilers K.16
Cartridge header block F.13
Cartridge software 2.31
Character printing program L.20
Clipping 8.2
clock/program control 2.42
Cntrl table F.7 F.8
Coding chart J.10
Color palette table 2.13
Colour changing 2.15
Colour fields 5.16
Colour generation 2.15
Colour monitor 1.6
Command modes 1.11
Commands 6.3
Communications overview 2.36
Compare, exclusive OR instructions H.10
Compatibility table K.8
Conditional tests H.8
Configuration registers 2.8 B.2

<!-- source-page: 397 -->
## Page 397

Contour fill 7.6
Control table 4.3 5.3
Control/status register functions 2.40
Controller execute 6.6
Copy raster 7.6
CP/M 68K format 2.22
CPU resources 2.9
Critical interrupt handlers 3.6
D
Data encoding i 4.33
Data packet functions 6.7
Data packets 6.2
Data registers G.25
Data storage G.23
Data structure types 5.36
Data types G.24
Device driver F.3
Device state block F.3
Digital Research assembler K.7
Direct memory access controller (DMA) 1.30
Direct memory access port (DMA) 1.11
Disable joysticks 6.5
Disable mouse 6.4
Display configuration registers B.2
DMA bus boot code 2.48
DMA interface 2.47
DMA/Disk configuration registers B.3
Draw sprite 7.6
Edit keys 5.21
Emulation instruction, type 1010H.10
Emulation instruction, type 1111 H.13
Endmasks 8.2
Envelope calculations 2.19
Error codes 1.2
Error processing state dump A.3
Escape functions 4.27
Escape functions implemented 4.27
Escape functions not implemented 4.30
Event library 5.8
Example assembler programs 1.2
Exception vectors A.2
Executable file size K.15
Extended BDOS(Trap #2) E.5
Extended BDOS calls (trap #2) 3.24
FDC instruction bytes 1.21
File formats 4.33
File header 4.33 F.6
File header format 2.22
File selector library 5.28
Filled rectangle 7.4
Floppy disk controller interface 1.10
Floppy disk interface 2.43
Floppy parameter block F.4
Font types 5.16
Form library 5.20
Format flag 7.7
Formatting a floppy disk 2.44
Index
GEM AES access 3.24
GEM AES components 5.5
GEM AES E.9
GEM AES function calls 5.2
GEM AES Libraries 5.6
GEM Application and accessory header file L.3
GEM BIOS 2.4
GEM demonstration assembly program L.9
GEM demonstration program L.8
GEM disk operating system (GEMDOS) 2.20
GEM draw 4.36
GEM parameter blocks F.7
GEM VDI access 3.24
GEM VDI calls 4.8
GEM VDI E.6
GEM VDI function calls 4.2
GEMDOS (Trap #1) E.4
GEMDOS calls (trap #1) 3.15

<!-- source-page: 398 -->
## Page 398

The Concise Atari ST Reference Guide
GEMDOS error codes 1.3
GEMSYS J.2
General assembler compatibility K.<
General conversion chart K.12
General drawing primitives 4.11
General hardware description 1.3
General housekeeping (Glue) 1.31
Get pixel 7.3
Global array 5.3
Global array block F.8
Glossary M.2
Graphic library 5.24
Graphics concept overview 2.10
GST assembler K.5
GSX compatible keyscan codes D.4
H
Hand coding J.7
Handles and coordinates 5.4
Hard disk partitioning 2.50
Hardware bound interrupts A.3
Header blocks F.13
Hide mouse 7.5
High resolution screen 2.12 2.13
Hisoft assembler K.4
HOG bit 8.3
Horizontal line 7.3
Icon selection 5.11
ikbd command set E.12
Implemented functions 2.35
Initialization pointers 7.2
Input functions 4.18
Input functions implemented 4.18
Input functions not implemented 4.20
Inquire functions 4.22
Instruction codes H.4
Instruction summary G.2
Instruction word parsing analysis H.2
Intelligent keyboard commands 6.2
Intelligent keyboard I/O (ikbd) 1.15
Intelligent keyboard interface 2.41
Internal registers G.25
Interrogate mouse position 6.3
Interrogate time of day clock 6.5
Interrupt Handler (VBI) 3.26
Interrupt handler overview 2.27
J
Joystick 2.41
Joystick interrogation 6.4
K
Keyboard 2.41
Keycode definitions D.2
Keycodes 6.2
Keystroke selection 5.11
Line 7.3
Line-A access 7.2
Line-A L.26
Line-A parameter blocks 7.7
Line-A parameter table L.26 7.8
Line-A routines 2.4 7.3 E.13
Line-A tables F.9
Line-A variables F.9
Line-by-line filled polygon 7.4
List of callable functions E.2
Load mouse position 6.4
Load parameter block F.5
Logic table 7.6
Low resolution screen 2.12 2.14

<!-- source-page: 399 -->
## Page 399

M
Main system & device subsystem diagram 1.4
MC68000 16-bit microprocessor (CPU) 1.19
MC68000 instruction codes H.2
MC68000 instruction summary G.2
MC6850 asynchronous communications
interface adaptor (ACIA) 1.27
MC6850configuration registers B.6
Medium resolution screen 2.12 2.14
Memory allocations 2.6
Memory configuration registers B.2
Memory definition block 7.7
Memory form definition block F.12
Memory load 6.5
Memory management unit (MMU) 1.30
Memory map 2.6
Memory model 2.21
Memory parameter block F.6
Memory read 6.6
Menu bar control 5.13
Menu library 5.12
Meta file Sub Op codes 4.35
Metacomco assembler K.6
MFP configuration registers 1.24
MFP hardware interrupts 1.24
Midi interface 2.39
Midi signal levels 1.13
Miscellaneous error codes 1.4
Miscellaneous instructions H.6
MK68901 configuration registers B.6
MK68901 multi-function processor (MFP)1.23
Monitor output 1.7
Monitor/TV output 1.6
Monochrome monitor 1.6
Mouse 2.41
Mouse/joystick interface 1.16
Move byte instruction H.5
Move longword instruction H.5
Move quick instructions H.9
Move word instruction H.5
Musical instruments digital interface (MIDI)
1.13
Index
N
Noise frequency calculations 2.18
O
Object library 5.14
Object library tables 5.15
Object tree 5.14
Operating system overview 2.3
OR, divide and subtract decimal instructions
H.9
Organization of addresses in memory G.27
Output functions 4.10
Output page 4.35
Overlap 8.2
Overview of screens 2.12
Parallel data I/O 2.17
Parallel port interface 2.38
Parallel printer interface 1.8
Parameter block sizes 4.5
Parameter blocks F.2
Pause output 6.4
Period/cycle 2.19
Peripheral device communications 2.36
Physical to logical screen transposition 2.13
Plug-in cartridge port 1.14
Points table 4.4
Port 0 1.16
Port 11.16
Power levels 1.17
Power supply 1.17
Printer and terminal escape codes C.2
Printers C.5
Processor device outlines 1.18
Program counter G.26
Program development tools K.2
Program parameter blocks F.5
Put pixel 7.3

<!-- source-page: 400 -->
## Page 400

The Concise Atari ST Reference Guide
R
Raster operations 4.16
Register usage 3.2
Relocation table 2.23
Reserved configuration register space B.3
Reset 6.3
Resource library 5.35
Resource mangement overview 2.9
Resume 6.4
RS232 interface 2.37
RS232 modem interface 1.9
RS232signal levels 1.9
Run flag bits F.13
Scrap library 5.27
Sector buffer block F.4
Seka assembler K.2
Set fire button 6.4
Set joystick event reporting 6.4
Set joystick interrogation mode 6.4
Set joystick keycode mode 6.5
Set joystick monitoring 6.4
Set mouse absolute positioning 6.3
Set mouse button action 6.3
Set mouse keycode mode 6.3
Set mouse relative position reporting 6.3
Set mouse scale 6.3
Set mouse threshold 6.3
Set time of day clock 6.5
Set y base position at top 6.4
Sey y base position 6.4
Shape 2.19
Shell library 5.37
Shift and rotate instructions H.12
Show mouse 7.5
Skew 8.2
Sound concept overview 2.16
Sound configuration registers 2.18
Sound configuration registers B.4
Sound control register 2.16
Sound demonstration program L.22
Sprite definition block 7.7 F.12
Sprite demonstration L.28
ST BIOS comparisons 2.27
ST disk system 2.26
ST file system 2.25
Stack pointer G.26
Status inquiries 6.6
Status register G.26
Subtract and subtract extended instructions H.9
Supervisor to user mode 3.23
Supervisor/user toggle 3.23
Symbol table 2.23
SYSTAB J.3
System byte G.27
System initialization 2.28
System interrupt functions 3.26
System start-up block F.2
System tables 2.7
System variables A.2 A.4
Television 1.6
Test for mode 3.23
Textblt 7.5
The operating system (TOS) overview 2.2
Tone frequency calculations 2.18
TOS Display demonstration program L.17
TOS header file L.19
Transform mouse 7.6
Transient program area block F.5
Trap #1 access 3.15
Trap #13 access 3.3
Trap #14 access 3.7
Traps 3.3
Typical AES application call 5.4
Typical Epson printer codes C.2

<!-- source-page: 401 -->
## Page 401

u
Undocumented line-A variables F.U
Undraw sprite 7.6
User byte G.26
User to supervisor mode 3.23
V
VDI parameter block F.7 4.3
VDI standard keyboard codes D.5
VDI style patterns 4.26
VDI text alignment 4.46
VDISYS J.2
Video controller (Shifter) 1.31
Virtual device interface (VDI) 2.4
VT52 terminal escape codes C.4
w
WD 1772A DMA channel interface 2.45
WD1772A floppy disk controller (FDC) 1.21
Window library 5.29
Window parts bit representation 5.30
Workstation function calls 4.8
XBIOS 2.4
XBIOS (Trap #14) E.2
XBIOScalls (trap #14) 3.7
YM2149 programmable sound generator (PSG)
1.29
Index

<!-- source-page: 402 -->
## Page 402

The Concise Atari ST Reference Guide

<!-- source-page: 1 -->
## Page 1

ATARI ST SERIES

Series Editor: Robin Bradbeer
Foreword by Jack Tramiel

THE CONCISE
ATARI ST 68000
PROGRAMMER'S
REFERENCE GUIDE

Katherine Peel
GLENTOP

Fully updated and revised to
cover Megas, Blitters
TOS in ROM, etc

<!-- source-page: 404 -->
## Page 404

THE CONCISE ATARI ST 68000
PROGRAMMER’S REFERENCE GUIDE

Katherine Peel

About the Atari ST Series
The Atari ST is one of the most significant new computers to be launched in recent years. Its performance and technical specifications are outstanding and comparable to machines several times the price. Moreover, it is a machine which appeals to the hobbyist and business user alike and the large amount of software available allows it to be used extensively in the home or office.

This series of books provides Atari ST owners with practical, down-to-earth information about their computers — from the introductory level through to advanced programming techniques and professional business uses.

About this book
The aim of this book is to provide the Atari ST user with a complete reference manual to the machine. It is designed to be used both as a quick reference manual and as a source of detailed technical material. Topics covered include machine code programming, details of GEM and the operating system. Much of the material included in the book has been taken directly from official Atari technical documentation and is unlikely to be found from any other source. The book will be an essential reference manual for every Atari ST owner.

About the author
Katherine Peel was formerly a senior systems analyst in industry, and now works as a freelance author. She has been a major contributor of reviews and technical articles to the “Your Computer” magazine for a number of years, providing in-depth authoritative reviews of the latest hardware.
