<!-- source-pdf: resources/platform_atari_st/docs/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.ocr.pdf -->
<!-- source-pages: 356 -->

<!-- source-page: 1 -->
## Page 1

COMPUTE!’s
Technical Reference Guide
AIARI ST
VOLUME ONE
Sheldon Leemon
A practical tutorial and reference to the Virtual
Device Interface, the ST’s graphics routines.
Includes practical program examples written
in C, machine language, and BASIC. For the
intermediate-to-advanced-level Atari ST
programmer.
A COMPUTE! Books Publication

<!-- source-page: 2 -->
## Page 2

COMPUTE!’s
Technical Reference Guide
ATARI ST
VOLUME ONE: VDI
Sheldon Leemon
COMPUTE Publications, Inc. fab¢
Re Re ume iwiegoz
ABC P ublis! hing Compan
Greensboro, North Carolina

<!-- source-page: 3 -->
## Page 3

Copyright 1987, COMPUTE! Publications, Inc. All rights reserved.
Reproduction or translation of any part of this work beyond that permitted by
Sections 107 and 108 of the United States Copyright Act without the permission of
the copyright owner is unlawful.
Printed in the United States of America
10987654321
ISBN 0-87455-093-9
The author and publisher have made every effort in the preparation of this book to insure the accuracy of the programs and information. However, the information and programs in this book are
sold without warranty, either express or implied. Neither the author nor COMPUTE! Publications,
Inc. will be liable for any damages caused or alleged to be caused directly, indirectly, incidentally,
or consequentially by the programs or information in this book.
The opinions expressed in this book are solely those of the author and are not necessarily those of
COMPUTE! Publications, Inc.
COMPUTE! Publications, Inc., Post Office Box 5406, Greensboro, NC 27403, (919)
275-9809, is part of ABC Consumer Magazines, Inc., one of the ABC Publishing Companies, and is not associated with any manufacturer of personal computers. Atari, ST,
ST BASIC, 520ST, 1040ST, and TOS are trademarks or registered trademarks of Atari
Corporation. GEM is a trademark of Digital Research, Inc.

<!-- source-page: 4 -->
## Page 4

Contents
Foreword
20... 0. eee eee
cette etnies
v
1. VDI and the GEM Graphics Environment
............
1
2. Setting Up the Graphics Environment
..............
11
3. Drawing Points and Lines ..........
0...
c eee eeeues
39
4. Color and Other Graphics Settings .................
67
5S. Filled Shapes
2.0... 0. cece
ees
91
6. Drawing and Manipulating Image Blocks ...........
117
Es
141
8. Input Functions
©... 0.0...
173
Appendices
A. VDI Function Reference
........ 0.0.0.0
c cee eee
193
B. Extended Keyboard Codes
.............0.0.00000.
317
C. VDI Font Files...
00... cee
eee 323
D. System Characters
.. 0.0.0...
e ec cce eee eeeee 329
Index by Function Name ............
00.0 cc eee eees
337
Index by Opcode
... 0... kee
eens
339
Index
2... cnt
eee eas
341

<!-- source-page: 5 -->
## Page 5

oa

<!-- source-page: 6 -->
## Page 6

Foreword
The Atari ST is a powerful personal computer. So powerful, in
fact, that using it to best effect can be a difficult task—even if
you have all the available Atari documentation. That’s why
you'll find COMPUTE!’s Technical Reference Guide, Atari ST
Volume One: The VDI so valuable. Clear and concise, with program examples at every turn, it’s the most complete guide to
programming graphics on the Atari ST.
Filled with programs written in C, machine language, and
BASIC, this reference guide and tutorial covers everything you
need to access program the advanced graphics capabilities of
the ST’s Virtual Device Interface, or VDI.
The first sections explain—in plain English, not jargonfilled computerspeak—VDI and GEM and how to set up a
graphics environment using VDI functions. Later chapters illustrate how to use VDI functions to draw points and lines, fill
areas, and move shapes around the screen.
Program after program shows you how to get your own
ST creations to do what you want them to do. You'll see how
to read the mouse pointer and other input devices with VDI
functions.
COMPUTE!’s Technical Reference Guide, Atari ST Volume
One: The VDI devotes an entire chapter to text on the ST—
after all, text on this computer is just another form of graphics.
Demonstration programs show how to align and rotate
graphic text strings and discussions on how letters are formed.
The latter half of this book is a complete reference to VDI
functions. You will find everything you need to know about
each function in one place—a summary of each function, its
opcode, C binding, and more. We’ve even included two indices to the VDI functions, so finding the right function is easier
and faster.
COMPUTE! Books is the leading publisher of programs
and information for the Atari ST. COMPUTE!’s Technical Reference Guide, Atari ST Volume One: The VDI is yet another example of the high quality you’ve come to expect in any guide
to personal computing from COMPUTE!.

<!-- source-page: 7 -->
## Page 7

Se

<!-- source-page: 8 -->
## Page 8

a
Chapter 1
*
‘VDI and the GEM
¥
Graphics
Environment
"i
A
=
ia
a
|
-_

<!-- source-page: 9 -->
## Page 9

7

<!-- source-page: 10 -->
## Page 10

When WE think of the Graphics Environment Manager (GEM) operating system, the first thing that comes to
mind is the mouse-driven user interface, with its drop-down
menus and icons. But there is another side to GEM which is of
considerable interest to programmers. This part of GEM is
known as the Virtual Device Interface, or VDI.
The function of the VDI, as its name suggests, is to provide a uniform, device-independent graphics interface that allows a programmer to design graphics output for a program
without necessarily knowing the operational details about the
computer on which the program is run, or about the hardware
device (screen, printer, plotter, and so on) used to produce the
output. This interface is based on previous graphics software
interfaces and on the work of a computer industry standards
committee. If you keep in mind that it was written as an attempt to be a generalized standard for all kinds of computers,
and was not written specifically to support the graphics capabilities of the ST, you may better understand the reasoning
behind its implementation.
The VDI implements this device-independent interface in
two ways. First, it supplies a wide array of basic graphics functions. These functions include drawing primitives (the fundamental commands used to draw line figures and filled shapes);
attribute settings that control aspects of the figures such as the
color, size, and shape; and inquiry commands that enable the
program to determine specific information about the graphics
environment. They even include input functions that enable
the programmer to accept input from the user via the mouse
pointer, alphanumeric keys, cursor keys, and function keys.
The VDI also provides the means by which device-specific
driver programs may be added to the system. These devicedriver programs act as translators. The VDI routes the generalized output commands to the device driver, and the device
driver converts these commands into the hardware-specific
codes used to create the appropriate output on that particular
device.

<!-- source-page: 11 -->
## Page 11

CHAPTER 1
On the Atari ST computers, the part of the VDI that implements the basic graphic functions on the display screen is
—_
included in the Tramiel Operating System (TOS) ROMs. The part
of the VDI that enables the use of disk-loaded fonts and device drivers, however, is not included as part of the current
~—
TOS ROMs and must itself be loaded from disk before these
functions can be accessed. This part, known as the GDOS
(Graphics Device Operating System), is contained in a
file
—
called GDOS.PRG, which must be included in the AUTO
folder on the system disk used to start the computer if device
drivers or software-loaded fonts are to be used. In addition,
that disk should contain a text file called ASSIGN.SYS, which
provides information about the location of the various devicedriver and text-font files that are available.
This books deals with only the VDI portion of GEM, but
the reader should be cautioned that the VDI does not operate
in isolation from the AES, the Application Environment Services
which form the other half of GEM. Unless you take the appropriate precautions, for example, the graphics functions presented here are quite capable of writing over the menu bar
and window borders that are managed by the AES. Also, there
is a certain amount of overlap between the two, particularly in
the area of the VDI input functions. In a program where you
use the AES input functions, you should be careful not to mix
in VDI calls that will confuse them.
Using the VDI
You can think of the VDI as a collection of subroutines that you
call from your program. In order to pass data to these subroutines and receive data from them, you must allocate storage
space in memory for a number of data arrays. The VDI uses
information from five different arrays, each of which is made
up of a number of 16-bit (two-byte) values. These arrays are:
Array name __ Size
Function
aaa
contrl
12 words
Control parameters
intin
0-256 words
Input parameters
ptsin
0-256 words
_Input coordinates
intout
0-256 words
Output parameters
ptsout
0-256 words
Output coordinates

<!-- source-page: 12 -->
## Page 12

VDI and the GEM Graphics Environment
The array contrl consists of 12 elements, each two bytes in
length. The information stored in each of the first seven of
these elements is as follows:
Address
Element
Control parameter
contrl
contrl(0)
Command Opcode (operation code)
contrl+2
contrl(1)
Number of coordinate points in ptsin array
contrl+4
contrl(2)
Number of coordinate points in ptsout array
contrl+6
contrl(3)
Number of input parameters in intin array
contrl+8
contrl(4)
Number of output parameters in intout array
contrl+10
contrl(5)
Sub-function ID number
contrl+12
contrl(6)
Device handle (identification number)
The first element of the contrl array is used to pass the
opcode. Since all of the VDI routines have a common entry
point, there has to be some way to let the VDI know what
command you want executed. Therefore, each command is
given an identification number called an opcode. A few commands are further broken down into several sub-functions. In
order to specify which of these sub-functions you wish to use,
a sub-function ID number can be passed in contrl(5). Since the
VDI can send output to several devices, you must also identify
the device you wish to use by placing its handle in contrl(6).
The handle is a device identification number which the system
assigns when you successfully open the device. (Opening a
graphics device like the screen for output will be covered later.)
The remaining four elements are used to indicate what
portion of the other parameter arrays are used by a particular
call. Of these, two are set aside for the input arrays ptsin and
intin, in which you pass information to the function, and two
are used for ptsout and intout, in which the function passes
information back to you.
The reason you must specify the size of these arrays is
that the number of values passed varies from function to function and can even vary from different calls to the same function. The line drawing command, for example, can draw lines
between a number of points at once. Therefore, in order to
communicate how many lines are to be drawn, you must specify the number of coordinate pairs that you have placed in the
ptsin array before calling that command. The number of points
is placed in contrl(1). This number is equal to half the length
of the array, since each point must be described by both a horizontal and a
vertical coordinate. In a similar fashion, the
number of points passed back in the ptsout array from the

<!-- source-page: 13 -->
## Page 13

CHAPTER 1
VDI command itself is stored in contrl(2). Contrl(3) and
Contrl(4) are used to store the length of the intin and intout
arrays, respectively.
Elements contrl(7)-contrl(11) aren’t used for every command, but, when they are, they pass information that is specific to the command.
Assembly Language VDI Calls
If you're programming at the machine language level, you
must explicitly reserve memory space for each of these arrays,
and put the proper values in each of the memory locations
before calling the command. The first step is reserving space
for each of the data arrays:
contrl:
.ds.w
12
intin:
.ds.w
128
ptsin:
.ds.w
128
intout:
.ds.w
128
ptsout:
.ds.w
128
Since all of the arrays but contrl use a variable number of
elements, depending on the particular call, it’s best to allocate
128 words to each of them, which should be sufficient for
most purposes. If you find that you need more elements, you
may, of course, allocate additional space.
In addition to allocating data-array space, you must also
define a VDI parameter block. This parameter block contains
the beginning address of each of the five data arrays:
vpb:
 .de.l
contrl,intin,ptsin,intout,ptsout
Next, you must place any input parameters into their correct place in the data arrays. For example, to execute the Clear
Workstation command that clears the screen, you would transfer the following values:
move #3, contrl
;Move the Clear Workstation
sopcode (3) to contrl(0).
move #0, contrl+2
;Move the length of ptsin
jatray (0) to contrl(1).
move #0, contrl+6
;Move the length of intin
zarray (0) to contrl(3).
move gh, contrl+12
;Move the graphics handle
jto contr1(6).

<!-- source-page: 14 -->
## Page 14

VDI and the GEM Graphics Environment
Now you're ready to call the VDI. First, place the address
of the VDI parameter block into register dl. Next, move the
VDI identifier code (115 or $78) into register dO. Finally, call
the VDI with a trap 2 instruction. This initiates a softwaregenerated exception (similar to a hardware interrupt) that
causes execution of an exception-handler routine. In this case,
the routine executed is the one whose address is pointed to by
the long word beginning at location 136 ($88). This routine is
the one used to handle all GEM VDI and AES calls. (AES calls
are identified by placing a value of 200 or $C8 into register
d0.) The sequence for making a VDI call looks like this:
move.
#vpb,d1
;Move address of VDI
jparameter block to d1.
moveq.l
#73,d0
;Move VDI identifier
($73) into dO
trap #2
;Call GEM entry point.
Please note that the procedures outlined above just cover
the steps required to make the VDI call itself. Before you get
to that stage, you must take some preparatory steps to set up
both the program environment (for example, allocating stack
space) and the graphics environment (for example, opening a
GEM output workstation). These steps will be outlined in the
next chapter and illustrated in an example program.
ST BASIC VDI Calls
The fundamental strategy for making VDI calls from ST
BASIC is similar to that used when making such calls from assembly language programs, with the exception that BASIC
takes care of much of the preparatory work.
Since the BASIC interpreter program must use VDI calls,
it already has set aside memory for the data arrays contrl,
ptsin, intin, ptsout, and intout. BASIC assigns the starting address of each of these arrays to a reserved variable of the same
name. Thus, the starting address of the contrl array is found in
the variable named contrl, the starting address of ptsin in the
variable ptsin, and so on. By using the PEEK and POKE commands, you may access the various elements of these data arrays. Remember that each element is two bytes long, so you
must multiply the element number by two to get the proper
offset for the POKE statement. The following short program
shows how to clear the screen with the the Clear Workstation

<!-- source-page: 15 -->
## Page 15

CHAPTER 1
call from BASIC. If you type it in and run it, you'll see that
Clear Workstation erases everything on the screen, including
window borders and the menu title bar.
10 REM POKE contri(0) with Clear Workstation opcode (3)
15 POKE contr1,3
20 REM POKE contrl(1) with length of ptsin array (0)
25 POKE contrl+ 2,0
30 REM POKE contrl(3) with length of intin array (0)
35 POKE contrl+6,0
40 VDISYS(1)
Although this program is similar to the assembly language
version shown above, you'll notice a couple of differences.
First, we didn’t have to POKE a value for the graphics handle
into contrl(6) (contrl+ 12). That’s because we’re using the
same display device as BASIC, and BASIC has already put the
graphics handle there for us. The second difference is the use
of the VDISYS call. The BASIC statement VDISYS(1)—the one
being a dummy value that could be any number—performs
the same tasks as the three lines of assembly code that place
the address of the parameter block into register d1 and the
VDI identifier code into proper values in the dO register, and
then execute the TRAP #2 statement.
The original version of ST BASIC contains several built-in
commands that perform the same functions as VDI calls without the hassle of POKEs. Although not released at the time of
this writing, the revised MCC BASIC promises to include even
more graphics commands. Nevertheless, BASIC programmers
can still benefit from learning about the VDI. A familiarity
with the structure and function of the VDI calls gives a better
understanding of how the BASIC graphics commands work
and how they interact. Even the enhanced version of BASIC
does not include keywords for all of the VDI functions. Learning how to access VDI calls directly from ST BASIC provides
the means for using all of the tools provided by the GEM VDI,
not just those that have been implemented by BASIC.
Calling the VDI Routines from C
It’s much easier to make VDI function calls from C than from
either assembly language or BASIC. That’s because C compiler
packages for the ST include one or more function libraries
8

<!-- source-page: 16 -->
## Page 16

VDI and the GEM Graphics Environment
known as GEM bindings. These bindings are object-code library
files that define a separate, named function for each VDI call.
When the C program is linked to the proper library files, it can
call VDI functions as if they were part of the C language.
You still must allocate storage space for the data arrays,
by making the following global array declarations at the beginning of this program:
int contri[12],
intin[128],
ptsin[128],
intout[128],
ptsout[128];
But you're not responsible for placing data directly into
these arrays. Instead, input parameters are passed to the binding functions as part of the function call. For example, you
could execute the Clear Workstation call from C with the following call:
v_clrwk(handle);
The function defined as v_clrwk in the library takes the
parameter handle that is passed to it and puts it in contrl(6). It
also puts a zero in contrl(1) and (3), and places the command
opcode (3) in control(0). It then loads registers d0 and d1 with
the proper values, and executes a TRAP #2 instruction. In
short, it takes over all of the repetitive steps associated with
making VDI calls, allowing the programmer to concentrate on
the essential aspects of the function.
Because it’s easy to make GEM calls from C, and because
the language produces programs that are relatively small in
size and quick in execution for a high-level language, it has
become the language of choice for software development on
the ST. Therefore, most of the examples in this book will be
written in C. On occasion, however, we will include assembly
language and BASIC examples as well, to show how the C examples may be translated to these other environments. We
will use the C function names as they appear in the official
Digital Research GEM bindings, since they have been adopted
by the manufacturers of other C compilers as well.
The C programs in this book are designed to work specifically with the Alcyon C compiler (the one officially supported
by Atari) and with Megamax C, which also provides a very

<!-- source-page: 17 -->
## Page 17

CHAPTER 1
complete development environment. For these compilers, the
int data type refers to a 16-bit word of data. Some other compilers, such as the Lattice C compiler, use a 32-bit integer as
the default data type. You should substitute “short” for each
reference to “‘int’’ when compiling the programs in this book
with such compilers. For the sake of simplicity, we have not
used the portability macros such as WORD, which use the C
preprocessor to define a 16-bit data type that will be valid for
any compiler, but you're free to do so if you find it more
convenient.
10

<!-- source-page: 18 -->
## Page 18

Chapter 2
Setting Up the
Graphics
Environment

<!-- source-page: 20 -->
## Page 20

Before you can begin using VDI calls, you must
first prepare a graphics output environment by opening a
GEM workstation. When you open a workstation, the GDOS
loads a device driver file (if necessary), initializes the output
device, reserves environment space for storing graphics
settings associated with that workstation, and returns a device
identification number, or handle, which is used to identify the
output device when making VDI calls. For graphics output devices other than the display screen, the call to use is Open
Workstation, which opens a physical device workstation. The
C format for this call is
int input[12];
int output[57]
int handle;
v_openwk(input, &handle, output)
The array, input, consists of twelve words of data that
you pass to the VDI. The first of these, the Device ID number,
is used to let the GDOS know what device driver file it must
load from disk. As explained in the previous chapter, the
ROM part of the VDI doesn’t know how to talk to any graphics output device except the computer’s own display screen. In
order to communicate with any other device, the GDOS must
first load a device driver file to translate its graphics commands into a format that the output device recognizes.
Loading the device driver is the job of the Open Workstation command, but in order for it to successfully perform
that task, several conditions must be satisfied. First, the GDOS
extensions must have been loaded into computer memory by
running the GDOS.PRG program. This should be done by including that file in the AUTO folder on the boot disk. At the
time the GDOS.PRG program is run, there must be a
file
called ASSIGN.SYS in the root directory of that disk. This is a
text file that tells the GDOS what drivers’ IDs are available,
what the driver files are called, and what text-font files are
13

<!-- source-page: 21 -->
## Page 21

CHAPTER 2
available for that graphics device. The format for each entry in
the assign.sys file is
ID_number(flag) filename
(fontfilename)
where ID_number is the device ID number, flag is an optional
letter that can be added to the ID number to give special loading instructions for the driver, filename is the name of the actual file containing the device driver, and fontfilename is the
name of an optional font file that the device can load with the
vst_load_font call. If there is more than one font file available
for the device, additional font files may be listed below the ID
line, one filename per line.
Although technically you’re free to assign any ID number
from 0 to 32767 to any device, it’s recommended that you use
numbers in the following ranges for these devices:
Device
ID Range
Display Screen
01-10
Plotter
11-20
Printer
21-30
Metafile
31-40
Camera
41-50
Tablet
51-60
The two flags that can be added to the device number are
the letters r and p. An r indicates that the driver is resident,
which means that it’s loaded at the time the GDOS is booted
and stays in RAM until the computer is reset. A p signifies
that the driver is maintained permanently in ROM, like the
screen driver that is contained in the Operating System ROM.
If neither of the flags follows the ID number, it is assumed
that the device driver file will be loaded when the physical
workstation is opened. A typical entry in the assign.sys file
looks like this:
21 fx80.sys
EPSHSS14.FNT
This describes a device driver file for the Epson FX-80
printer. The printer ID number is 21, the driver itself is contained in a
file called fx80.sys, and there is one text font available for use by this driver, in a
file called epshss14.fnt (a
single-height, single-width font 14 points high).
When opening a workstation for this device, the device
14

<!-- source-page: 22 -->
## Page 22

Setting Up the Graphics Environment
number would be given as the first input parameter (intin(0)).
The rest of the input array parameters are used to specify the
initial default graphics settings for the workstation, and will be
discussed more fully later on.
The other two parameters associated with the Open
Workstation call, handle and output, are used by the function
to return information about the workstation that was just
opened. The most important item is the workstation ID number, or handle, that is returned in the variable handle. This ID
must be included as part of the input to all of the other VDI
functions, to indicate the device to which graphics output is to
be sent. If the VDI can’t open the device, it returns a handle
number of zero. Up to 16 workstations may be open at one
time, and it is possible to open more than one physical workstation for devices other than the display screen.
In addition to supplying the handle, v_opnwk fills the array output with 57 items of information about the workstation
that was just opened. All of the input and output parameters
will be covered in the discussion of virtual workstations, below.
Virtual Workstations
The Open Workstation call is used for all devices except the
display screen. The display device has a unique role in the
GEM system. It’s the primary means of communicating with
the user, so it’s the one graphics device that has to be open almost all the time.
The display device is the only device for which there is a
device driver built into the TOS ROMs. And since it has to be
shared by the Desktop, application programs, and desk accessories, it’s the only graphics device that must display information from more than one program at a time.
In order to allow multiple users to access a single display,
GEM uses pseudo-devices called virtual screen workstations.
Once a physical workstation has been opened, the physical
device can be subdivided into one or more virtual workstations,
each of which has complete access to the display screen. Each
virtual workstation maintains its own set of graphics settings,
so that if one application makes a change that affects how its
drawing takes place, that change will not affect the other
workstations as well. In fact, a single application can open
more than one virtual screen workstation at a time.
15

<!-- source-page: 23 -->
## Page 23

CHAPTER 2
The format of the Open Virtual Screen Workstation function is identical to that of the Open Workstation function:
--
int input[12];
int output[57]
int handle;
_—
v—openvwk(input, &handle, output)
Input array. The input array consists of twelve words of
—
data that you pass to the VDI to specify the initial default
graphics settings for the workstation. It should be noted that
unless you load the GDOS extensions with the GDOS.PRG
program, or have a version of the TOS ROMs with the GDOS
built in, none of these input values will affect the initial workstation settings, which will always be set to their default values. We'll only briefly mention these settings here, since most
duplicate the function of individual graphics setting commands
that will be discussed at length in the chapters on line drawing, filled shapes, and color. They are
Element
Contents
Comparable VDI function
input[0]
Device ID number
input{1]
Line drawing pattern
vsl_type
input(2]
Line pen number
vsl_color
input[3]
Marker type
vsm_type
input[4]
Marker pen number
vsl_color
input[5]
Text font
vst_font
input[6]
Text pen number
vst_color
input[7]
Fill pattern type
vsf_interior
input(8]
—_—*Filll pattern index
vsf_style
input[9]
Fill pen number
vsf_color
input[10]}_
NDC to RC transformation flag
The first and last of these parameters require a
little further
—
explanation. The first, Device ID number, is used somewhat
differently for virtual screen workstations. That’s because on
the ST there isn’t one standard type of screen display device
~~
that’s always used. Instead, the user is allowed to choose from
three different types of displays. The monochrome screen offers
a resolution of 640 X 400 pixels, but only two colors (black
—
and white). The color monitor uses either
a medium resolution
mode of 640 X 200 pixels, with
a maximum of 4 colors on
screen at once, or a low-resolution mode of 320 * 200 pixels,
16
—

<!-- source-page: 24 -->
## Page 24

Setting Up the Graphics Environment
with a maximum of 16 colors. In either color mode, each color
may be selected from any of the 512 available.
While your program cannot dictate which of the three displays is to be used, it should be able to load a
set of text fonts
that is appropriate for the current display. Therefore, in the
assign.sys file, there are several IDs assigned to the screen device. These assignments, which are specific to the Atari version of GEM only, are
Device Number
Screen Type
01
Default
02
Lo-res color
03
Medium-res color
04
Hi-res monochrome
05-10
Reserved for Atari expansion
Therefore, a typical assign.sys file is shown in Program 2-1.
Program 2-1. Typical assign.sys
path = c:\drivers
;Optional path designation for
jdevice driver and font files
Olp screen.sys
iThe default setting, provided
for compatibility with pre-GDOS
japplications
02p screen.sys
;Using device ID 2 makes available
LOWRES10.FNT
;these lo-res fonts only
LOWRES14.FNT
LOWRES18.FNT
03p screen.sys
;Using device ID 3 makes available
MEDRESI0.FNT _
;these medium-res fonts only
MEDRES14.FNT
MEDRES18.FNT
04p screen.sys
;Using device ID 4 makes available
HIRES10.FNT
ithese hi-res fonts only
HIRES14.FNT
HIRES18.FNT
21 f£x80.sys
;Epson printer driver and fonts
EPSHSS10.FNT
EPSHSS20.FNT
EPSHSS28.FNT
31 meta.sys
j;Meta-file driver
17

<!-- source-page: 25 -->
## Page 25

CHAPTER 2
As you can see, an optional path statement may be used
to designate a path name for the device drive and text-font
files. This path specification must be given at the beginning of
the file, before any device ID assignments are made. The pathname can only be 64 characters long. It doesn’t matter
whether the names are entered in upper- or lowercase letters.
Next come the device IDs for the screen drivers. A filename of
screen.sys is given for each entry so it will conform to the
standard format, but the GDOS doesn’t try to read in a device
driver file of that name because the p
flag after the device
number tells it that this driver is permanently installed in
ROM. A device number of 1 is used to specify the default
screen driver. This indicates that you don’t care about matching the disk-based text fonts to the screen resolution. Device
numbers 2, 3, and 4 are used for the low, medium, and highresolution screens, respectively. In order to open the virtual
workstation with the proper ID, however, you first must determine what display is in use. You can use the XBIOS (Extended
Basic Input/Output System) command 4 to determine the current screen resolution. From C, you can use getrez,
a macro
defined in the file “osbinds.h”, to call this function. To find
the proper ID number, use the statement
ID = getrez() + 2;
Since getrez returns the number 0
for lo-res,
1 for mediumres, and 2
for hi-res, all you have to do is add 2 to the value
returned to get the right ID number. Assembly language programmers can perform the getrez call using the following code:
move.w
#4,—(sp)
* push command number on the stack
trap
#14
* call XBIOS
addq.l
#2,sp
* pop command number off the stack
The resolution will be returned in register dO.
The last Open Virtual Workstation input parameter, the
Normalized Device Coordinate (NDC) to Raster Coordinate
(RC) transformation flag, allows you to specify which coordinate system you'll use for drawing. The RC system is the one
used most commonly on microcomputers. Under this system,
the screen is divided into rows and columns of dots, which
represent every point that can be plotted on the display
screen. The dots in the top row have a
vertical, or y, coordinate of zero.The vertical coordinate number increases as you
18

<!-- source-page: 26 -->
## Page 26

Setting Up the Graphics Environment
move toward the bottom row of the screen, which has a y coordinate of 199 on the color screen and 399 on the monochrome display. Likewise, the leftmost column has a
horizontal or x coordinate of zero, which increases as you
move toward the rightmost column, where the x coordinate is
639 on medium- or high-resolution displays, and/or 319 on
low-resolution displays. (See Figure 2-1.)
But the GDOS also supports another system known as
Normalized Device Coordinates (NDC). Since almost every
graphics output device has a different maximum horizontal
and vertical resolution, it’s difficult to write a single program
that will work with many different types of devices. That’s
where the NDC system comes in. It attempts to offer the programmer a system in which graphics drawn on one computer
screen or printer will look the same when drawn on other
computers screens or printers of varying resolutions. When
you use NDC coordinates, you send all of your graphics output to an imaginary display that is 32,768 pixels wide by
32,768 pixels high. These pixels are grouped differently than
they are under the Raster Coordinate system, since the vertical
axis starts at the bottom of the screen (0) and moves up to the
top row (32767). As in the RC system, the left-hand column is
zero, and x coordinate numbers increase as you move the
rightmost column (32767). (See Figure 2-2.)
Figure 2-1.
Figure 2-2.
Raster Coordinate (RC) System
Normalized Device Coordinate
(NDC) System
8,8
633,6
0, 32767
32767, 32767
8,199
639,193
0,8
32767,8
19

<!-- source-page: 27 -->
## Page 27

CHAPTER 2
The GDOS takes the graphics output that you send to this
enormous display and scales it down in proportion to the
more modest dimensions of your actual output device. For example, let’s say that you order the VDI to draw a box whose
upper left corner is at point 8192,24576 and whose lower right
corner is at point 24576,8192 in the NDC system. This box
follows the outline of the display, a quarter of the way in from
each edge. If you’re using the ST’s medium-res color screen
for your display, GDOS transforms the normalized coordinates
to raster coordinates, and draws a box from 160,50 to 480,150.
But if you’re using the lo-res screen, the box would go from
80,50 to 240,150, and in hi-res it would go from 160,100 to
480,300. This means that with one command, you can create
the same size box on each of the ST’s three display screens.
You may find, however, that normalized coordinates may
not be as useful as they may seem at first. For one thing, they
slow down all of the graphics operations. Even though the ST
computers are fast, they still aren’t so fast that the extra step
of translating normalized coordinates to raster coordinates
can’t cause some appreciable delay in complex drawing operations. Secondly, the disparity between the resolution of the
normalized display and that of real-world graphics devices is
so great that something is bound to be lost in the translation.
With only
1 RC pixel for every 8000 NDC pixels, there is no
way that very complex drawings can be accurately reproduced
on screens of varying resolutions. Realistically, most ST programmers will want to write applications specifically for the
ST and will want to know exactly where every pixel will be
drawn. So while NDCs are a nice idea, the RC system will
probably still be the one used most often, at least until that
computer with the 32,768 X 32,768-pixel display comes along.
The handle. Handles pass a
lot of information when they
are called. The most important item is the workstation ID
number, or handle, that is returned in the variable handle.
This ID is included as part of the input to all of the other VDI
functions, to indicate the device to which the graphics output
is to be sent. For v_opnvwk only, handle is used as both an
input and an output parameter. In order to get back the new
handle for your virtual workstation, you should first pass the
handle of the screen device that GEM has already opened.
20

<!-- source-page: 28 -->
## Page 28

Setting Up the Graphics Environment
You can get this handle by using the call
int handle,
charw, charh,
boxw, boxh;
handle = graf_handle(&charw, &charh, &boxw, &boxh);
Again, note that unless you load the GDOS extension by
running the GDOS.PRG program, this step really doesn’t
accomplish anything, since it appears that the input value
placed in handle is ignored by the TOS ROMs. But even if you
aren't running GDOS.PRG from the AUTO folder of your boot
disk, it pays to follow the GEM guidelines, since, otherwise,
your program will not work on computers that do have the
GDOS resident. Besides, this call returns some interesting
information about the size of the default text font. The width
and height of the actual characters are returned in charw and
charh, while the width and height of the text box, the cell in
which each character is placed, are returned in boxw and
boxh. We'll go deeper into the formation of text characters in
the chapter that deals with text.
Output array. In addition to supplying a handle for your
new workstation, the v_opnwk and v_opnvwk calls fill the
array Output with 57 varieties of information about the workstation that was just opened. This information is really provided to aid in creating more portable GEM programs that
may be run on other types of computers and on all kinds of
output devices, but it is still of interest to the programmer who
works exclusively with the ST screen device. Information
given about the workstation includes:
output[0]
| Maximum horizontal coordinate value (in points or
pixels)
output[1]
Maximum vertical coordinate value (in points or pixels)
output[2]
Device Coordinate units flag
(1 = device doesn’t support precise scaling)
output[3]
Width of one pixel in microns (1/1000 millimeter)
For display screens, horizontal component of aspect ratio
output[4]
Height of one pixel in microns (1/1000 millimeter)
For display screens, vertical component of aspect ratio
output[5]
Number of text font heights
(0 = continuous scaling)
output(6]
| Number of line patterns
output[7]
| Number of line widths
(0 = continuous scaling)
21

<!-- source-page: 29 -->
## Page 29

CHAPTER 2
output[8}
output[9]
output[10]
output[11]
output[12]
output[13]
output[14]
output[15]
to
output[24]
output[25]
to
output[34]
output[35]
output[36]
output[37]
22
Number of marker patterns
Number of marker sizes
(0 = continuous scaling)
Number of text fonts supported by the device
Number of pattern fill styles
Number of crosshatch fill styles
Number of drawing-pen colors available
(the number of colors that can be displayed by the device at the same time)
Number of Generalized Drawing Primitives (GDPs)
(how many of the 10 basic drawing commands are
supported)
This part of the array holds a sequential list of code
numbers for the first 10 GDPs supported.
Each element holds one of the following code numbers:
1 = Filled Rectangle or Bar (v_bar)
= Circle Segment or Arc (v_arc)
= Filled Pie Slice (v_pieslice)
= Filled Circle (v_circle)
= Filled Ellipse (v_ellipse)
Elliptical Arc (v_ellarc)
= Filled Elliptical Pie Slice (v_elipie)
= Rounded Rectangle (v_rbox)
= Filled Rounded Rectangle (v_rfbox)
10 = Justified Graphics Text (v_justified)
—1 = End of list
This part of the array holds a sequential list of code
numbers showing what category of graphics operation is
performed by of each of the supported GDPs. This indicates what kind of graphics settings affects each of the
supported commands. Each element holds one of the following code numbers:
Line drawing
Marker drawing
Graphics text
Filled area
= no setting
Color availability flag
0 = device is not capable of color output
1 = device is capable of color output
Text rotation availability flag
Q = device is not capable of text rotation
1 = device is capable of text rotation
Area fill availability flag
0 = device is not capable of area fill operations
1 = device is capable of area fill operations
WON ATAWN
ll
i=)
1
2
3
4

<!-- source-page: 30 -->
## Page 30

Setting Up the Graphics Environment
output[38]
output[39]
output[40]
output[41]
output[42]
output[43]
output[44]
output[45]
output[46]
output[47]
output[48]
output[49]
output[50]
output[51]
output[52]
output[53]
output[54]
output[55]
output[56]
Cell array function availability flag
0 = device can not perform the cell array function
1 = device can perform the cell array function
Total number of color choices available in the palette
0 = more than 32,767 colors available
1 = monochrome
2-32767 = actual number of colors available
Input devices available for the locator function
1 = keyboard only
2 = keyboard and other device (such as mouse)
Input devices available for the valuator function
1 = keyboard
2 = other device
Input devices available for the choice function
1 = function keys on keyboard
2 = some other keypad
Input devices available for the string input function
1 = keyboard
Workstation type
output only
input only
input and output
reserved for future use
metafile output
hie
td
da
PON
©
Minimum character width
Minimum character height
Maximum character width
Maximum character height
Minimum line width
0
Maximum line width
0
Minimum marker width
Minimum marker height
Maximum marker width
Maximum marker height
The first two elements of the array give the maximum
horizontal and vertical coordinates, assuming that the coordinates start at point 0,0. For the ST monochrome screen the
horizontal value is 639 and the vertical value is 399, indicating
a resolution of 640 X 400 pixels. The horizontal value for the
color medium-res screen is 639, and for the lo-res screen it’s
319. The vertical value for both color screens is 199. Element 2
23

<!-- source-page: 31 -->
## Page 31

CHAPTER 2
contains a
flag indicating whether the device is capable of precise scaling or only approximate values like a film recorder.
This flag is set to 0, indicating precise scaling, for all ST
screens.
The next two elements contain the width and height of
one pixel in microns (a micron equals 1/1000 millimeter).
While such measurements are more accurate for printers and
plotters than display screens which vary considerably from
unit to unit and model to model, they can be used to determine the aspect ratio, which is the ratio of the width to the
height. For the hi-res screen the pixel width value is 372. The
medium-res width is 169, while the lo-res width is twice that,
or 338. The pixel height is 372 in all three modes. Thus, while
the hi-res pixels are square, and the lo-res ones almost so, the
medium-res pixels are less than half as wide as they are tall.
The aspect ratio comes in handy when you try to draw boxes
that look square and circles that look round on the screen.
Since each pixel in medium-res is tall and skinny, a box that is
100 pixels wide by 100 pixels high will appear to be tall and
skinny as well. In order to get the box to look square, you
must multiply the width by the aspect ratio (work_out[3]/
work_out[4]) to get the height. In medium-res mode, a box
that is 100 pixels wide should only be 45 pixels high if it is to
appear square. The VDI does this kind of scaling for you automatically when it draws a
circle using one of the circle
functions.
The next 9 values and the last 12 give some information
about the kinds of graphics settings available. The VDI is capable of drawing text in a number of different sizes (or
heights, to be more precise), and element 5
tells exactly how
many are available (on the ST the default number is 3 in all
resolution modes).
Elements 45 and 46 give the minimum text character size
(5 pixels wide by 4 pixels high on the ST), and elements 47
and 48 give the maximum text character size (7 pixels wide by
13 pixels high).
Element 6 tells how many types of patterned lines can be
drawn. (On the ST this value is 7.) Lines can be drawn one
pixel wide or several pixels wide, and the number of available
line widths are stored in element 7. On the ST, this value is 0,
indicating that line widths may be continuously scaled from
the minimum value to the maximum (though even numbers
24

<!-- source-page: 32 -->
## Page 32

Setting Up the Graphics Environment
will be rounded down to the next lower odd value). Element
49 gives the minimum line width (1 pixel), while element 51
holds the maximum line width (40 pixels on the ST).
The next two values give the number of marker types and
sizes. Markers are graphics objects that can look like a dot, a
diamond, an asterisk, or other shapes, and the number of
marker types indicates the number of shapes available. (On
the ST, the standard set of six shapes can be used.) On the ST,
these markers can be drawn in any of eight sizes. Elements 53
and 54 give the minimum marker size (15 pixels wide by 11
pixels tall), and elements 55 and 56 hold the maximum marker
size (120 pixels wide by 88 pixels tall).
Element 10 shows the number of text fonts that are resident. On the ST, only one system font is available unless you
load additional fonts from disk.
The next two values show the number of pattern types
available for filling shapes with colored patterns. On the ST
there are 24 pattern fill types and 12 crosshatch styles.
Finally, element 13 shows the number of drawing pens
that are available. This number corresponds with the number
of hardware color registers used for a particular mode and determines the maximum number of different colors that can be
displayed on screen at one time. On the ST this value is 2 for
the monochrome screen, 4 for the medium-res color screen,
and 16 for the lo-res color screen. Since each of the ST’s three
display screens has a different maximum number of colors that
it can display, the value found in element 13 can be used to
determine what display mode is in use. Element 13 should not
be confused with element 39, which holds the total number of
colors available. For both of the color modes, this value is 512,
which means that any of the drawing pens (color registers)
can hold any of 512 possible values at one time. For the
monochrome screen, this value is 2, since only black and
white are displayed.
Next comes information about the types of basic drawing
operations that may be performed. For historical reasons having to do with the older graphics systems from which the VDI
evolved, these operations are known as Generalized Drawing
Primitives (GDPs). Element 14 shows how many of the ten
GDPs are supported. (On the ST, all ten are supported.) Elements 15-24 contain a
list of the code numbers for the supported operations. Since the ST supports all ten, these elements
25

<!-- source-page: 33 -->
## Page 33

CHAPTER 2
hold the numbers
1 through 10. Elements 25 to 34 contain a
list of code numbers showing the type of drawing operation
(line drawing, area fill, text, and so on) performed by each of
the ten operations. The operation type of a graphics output
function determines which group of graphics settings will affect it. On the ST, the values for these elements are
Element
Code
Function
Element
Code
Type
15
1
Filled Bar
25
3
Fill
16
2
Arc
26
0
Line
17
3
Filled Pie
27
3
Fill
18
4
Filled Circle
28
3
Fill
19
5
Filled Ellipse
29
3
Fill
20
6
Elliptical Arc
30
0
Line
21
7
Filled Elliptical Pie
31
3
Fill
22
8
Rounded Rectangle
32
0
Line
23
9
Filled Rounded Rectangle
33
3
Fill
24
10
—— Justified Text
34
2
Text
The next four values are flags that indicate whether the
device supports a certain VDI function or not. Zero in one of
these elements means that the device doesn’t support the
function, while
1 indicates that it does. The flag in element 35
indicates whether the device supports color output. This flag
shows a 1
for either resolution of color display, and a 0 for the
monochrome screen. The next flag shows whether text rotation is available. (It is on the ST, though we will see later on
that text characters may only be turned in 90 degree increments.) The flag in element 37 shows whether the device supports area filling. (All ST screens do.) Finally, element 38
indicates whether the device supports the Cell Array function,
in which a rectangular area of the drawing surface may be
broken down into smaller rectangular color zones. The ST
screens do noi support this function.
In addition to all of the output functions, the VDI supports a number of input functions as well, which allow a program to receive feedback from the user. You can tell whether a
particular device supports these functions by looking at the
value in element 44, which tells whether it supports input
and/or output functions. On the ST, the virtual screen workstation includes the keyboard and mouse as well as the screen,
and therefore supports both input and output.
Elements 40-43 give information about the hardware devices used for the input functions. Element 40 specifies the input devices available for the locator function, which allows the
26

<!-- source-page: 34 -->
## Page 34

Setting Up the Graphics Environment
user to choose a point on the screen. On the ST, the value
here is 2, which indicates that either the keyboard or the
mouse may be used for this function. Element 41 shows the
input devices available for the valuator function, which allows
the user to move a value setting higher or lower within the
range of 1-100. On the ST, this value is 1, which means that
the keyboard (and more specifically, the arrow and shift keys)
are used for this function. Element 42 deals with the hardware
device used for the choice function, which lets the user select
from a number of options. The value here on the ST is 1,
which indicates that the ten function keys are used to return a
number from
1 to 10, indicating the choice that was selected.
Element 43 indicates what device is available for text character
string input. On the ST the value here is 1, indicating the keyboard (the only choice, actually) as the device used.
Extended Inquire
The VDI includes another function that can supply your program with all of the same information that is returned by the
Open Workstation calls, plus a number of additional facts
about the graphics environment. This function is called Extended Inquire, and it uses the following format:
int handle, flag, output[57];
vq—extnd(handle, flag, output);
where handle is the workstation ID number, output is a pointer
to the array where the information is returned, and flag indicates whether you want the function to return the same output
values as the Open Workstation calls (flag = 0), or the extended information (flag =
1). When you request the extended
information, the values returned in the output array have the
following meanings:
output [0]
Screen type
0 = no screen
1 = separate character and graphics controllers
using separate screens
2 = separate character and graphics controllers
sharing a common screen
3 = common character and graphics controller
using separate graphics memory storage
4 = common character and graphics controller
using common graphics memory storage
27

<!-- source-page: 35 -->
## Page 35

CHAPTER 2
output [1]
output [2]
output [3]
output [4]
output [5]
output [6]
output [7]
output [8]
output [9]
output [10]
output [11]
output [12]
output [13]
output [14]
output [15]
output [16]
output [17]
output [18]
Number of available background colors
Number of graphics text special effects
Raster scaling flag
0 = scaling not supported
1 = scaling supported
Number of color planes used for raster (number of
bits per pixel)
Color register lookup table flag
0 = lookup table not supported
1 = lookup table supported
Number of 16 X 16 raster operations per second
Contour fill flag
0 = contour fill not supported
1 = contour fill supported
Text rotation flag
0 = text rotation not supported
1
=
text may be rotated in 90 degree steps
2
=
text may be rotated any angle
Number of drawing modes
Input modes flag
0 = no input modes supported
1
= request mode supported
2 = sample and request modes supported
Text alignment flag
0 = text alignment not supported
1 = text alignment supported
Inking flag (for plotters)
0 = device cannot ink
1 = device can ink
Rubberbanding flag
no rubberbanding
1
= rubberband lines only
2
= rubberband lines and rectangles
Maximum vertices in ptsin (for Polyline, Polymarker,
and Area Fill)
Maximum size of intin
Number of mouse buttons
Is line pattern used for wide lines?
0 = no patterned drawing of wide lines
1 = wide lines can be drawn with patterns
Drawing modes for wide lines
output[19]-[56]
Reserved for future use
On the ST, output [0] always shows the screen type to be
4, since graphics and text are bitmapped on the same screen in
both color and monochrome modes. The number of available
28

<!-- source-page: 36 -->
## Page 36

Setting Up the Graphics Environment
background colors shown in output [1] is
1 for monochrome
systems and 512 for color systems. The number of graphics
text special effects reported in output [2] on the ST is 31. Output[3] shows that raster scaling is not supported. Output [4]
shows that there is one color plane in monochrome mode, two
color planes in medium-res mode, and four color planes in lores mode; this means that the monchrome screen can only display 2 colors at one time, while medium-res can display 4,
and lo-res 16. Output [5] shows that a color-lookup table is
not supported in monochome mode, but is supported in the
color modes. (The color lookup table, which assigns VDI color
index numbers to hardware color registers, is discussed in
Chapter 3.)
The performance factor in output [6] shows that 1000
16 X 16 pixel raster operations can be performed in one second on the ST. Output [7] shows that the ST has flood-fill
capability. Text characters may be rotated in 90 degree increments, according to the value in output [8]. There are four
drawing modes available on the ST, as shown by output [9].
The GEM input pseudodevices work in both sample and request mode on the ST, per output [10]. Output [11] shows that
text may be aligned. Output [12] shows that the screen device
cannot ink, and output [13] shows that it cannot draw rubberband lines.
The maximum number of vertices for the Polyline, Polymark, or Area Fill functions is 128 on the ST, according to output [14]. (This means that the maximum size of the ptsin array
should be 256.) There is no maximum size for the intin array,
though, according to output [15]. Output [16] shows that the
ST mouse has two buttons. Output [17] and output [18] show
that wide lines cannot be drawn with line patterns and that
they have no special writing modes.
Other Workstation Functions
The Clear Workstation function initializes the device to a state
in which there is no graphics output. For the screen, this means
setting every pixel to the background color. For a printer or
plotter, the print buffer is cleared and a form feed is sent to
advance to a new page. This function is performed automatically whenever a physical (but not a virtual) workstation is
29

<!-- source-page: 37 -->
## Page 37

CHAPTER 2
opened. The format for the C version of this function is
v—clrwk(handle);
where handle is the graphics handle for the workstation.
Another function, Update Workstation, can be used with
devices like printers, which don’t execute graphics commands
as soon as the program sends them, but accumulates data in a
buffer first. This function is used to immediately execute any
commands that are waiting in the buffer. It has no effect on a
device like the screen, which always executes output commands immediately. The
C command looks like this:
v_updwk(handle)
The final two workstation commands are Close Workstation
and Close Virtual Screen Workstation. These de-allocate the
workspace used to keep track of the device settings, and prevent further output to the device. You should always remember to close any devices that you have opened before exiting
your program. The syntax for these functions is
v—clswk(handle);
and
v—clsvwk(handle);
A C Program Shell
Since most of the subsequent example programs use virtually
the same program code to initialize the graphics environment,
it would be repetitive to include the text of that code in every
example. Instead, we include the steps necessary to open the
screen device and get its identification handle below, in the
form of a short program shell, Program 2-3. All Program 2-3
does is open the virtual workstation, call a function named
demo, wait for somebody to press a mouse button (to give the
viewer time to see the graphics display), and close the workstation. Since the function demo is not defined in this program, it will not link properly unless you add that function
yourself. The way we'll do that in our examples is to use the C
#include operator to include the file work.c at the beginning of
most of our sample programs, and name the main function of
the sample program demo( ). For example, to create a program
that does absolutely nothing but wait for a mouse button
30

<!-- source-page: 38 -->
## Page 38

Setting Up the Graphics Environment
press, you could define an empty function for demo( ), as
shown in Program 2-2.
Program 2-2, dummy.c
*#include
"“work.c"
demo
() (>
Keeping the initialization code in a reusable file will
shorten our sample listings substantially, and will save you a
lot of retyping. But be sure that the file work.c is stored where
your compiler can find it, either in the same disk and directory
as your standard header files or in the same disk and directory
as the source code file.
Program 2-3. shell.c
/* Global
variables
--
For
VDI
bindings,
etc.
x%/
int contrif12],
intinli2e81,
ptsin£i2si,
intoutl12983,
ptsoutl1281;
int handle;
int work_inli2],
work _outt{S71];5
/&
Initialization
starts here
%/
maind
€
int
x,
nul,
button=@;
/*&
Initialize the GEM application
%&/
appl _initd);
/&
Initialize input
array,
get
the physical
workstation handle,
and
open
the Virtual
Screen Workstation
&/
for
(x=8,
work_inli@I=23
x<183;
work_in€x++]=1)3
handle
= graf_handle(&mul,
&nul,
&nul,
&nul);
v_opnvwk
(work_in,
&handle,
work_out);
v_clirwk (handle);
/% perform the graphics demos
&/
demo ()3;
/%
Wait
until
the mouse button
is pushed,
then close the virtual
workstation,
and
exit
from
the application
&/
while (button==9) vq_mouse (handle, &button, &nul, &nul)
3
v_icisvwk (handle) 3
appl _exit();
31

<!-- source-page: 39 -->
## Page 39

CHAPTER 2
Program 2-3 has a few function calls that haven’t been
discussed yet. For example, the first and last commands used
are appl_init() and appl_exit( ). These are non-VDI GEM
functions that are used at the beginning and end of every
GEM program, the former to initialize the application and the
latter to exit from it. Also, we used the vq_mouse function to
check for a mouse button press. This is
a VDI input function,
and we will discuss it in more detail in Chapter 8. The rest of
the program, however, should be familiar from the material
covered above.
After you compile and link the sample programs (and use
the relmod utility if you are using Alcyon C), you'll end up
with a GEM program whose name ends in .PRG. When you
run this program, the mouse pointer will be visible, and may
disrupt part of the drawing when you move it. To avoid this,
you can either be careful not to move the pointer, and just
click a button when you wish to exit, or you can rename the
program with the extender .TOS. When you run a TOS program, the mouse pointer becomes invisible, and the screen is
cleared automatically. Later, in the chapter on input commands, you'll see how to make the mouse pointer invisible
before using graphics commands. You can then modify the
shell program to incorporate this feature.
An Assembly Language Program Shell
Setting up a bare-bones assembly language program is more
involved than just translating the corresponding shell.c program. For one thing, C programs usually link in a startup file
at the beginning of the program to take care of such maintenance chores as allocating a chunk of RAM for a program stack,
setting the stack pointer to the address of that stack, and returning any unused RAM to the pool of free memory. Programs
written in Alcyon C
link in the file appstart.o or gemstart.o at
the beginning to take care of these tasks.Megamax C programs
get the necessary code from a library module called init.o, the
source code for which is supplied in a file called init.c (which
uses the inline assembly commands). But assembly language
programmers must provide the equivalent functions for each
of their programs themselves.
The other problem is that not all assemblers have a
.include directive, so we won't be able to include the text of our
32

<!-- source-page: 40 -->
## Page 40

Setting Up the Graphics Environment
shell program in each of our demo programs. Instead, we'll assemble the shell program separately, and link the resulting object file with the demo program object files. Since our shell
program refers to the demo subroutine in the demo program
file, and the demo programs refer to the VDI data arrays defined in the shell program, we’ll use the .xdef and .xref
directives to help resolve these external references. The .xref
directive tells the assembler that the symbol is defined in another object file, while the .xdef tells it that this symbol will be
used by another object file. All of the assembly language examples in this book have been created with the assembler that
comes as part of the Alcyon C compiler, so bear in mind that
the assembler directives used may be slightly different than
those of other assemblers.
Program 2-4 is the assembler shell program, shell.s.
Program 2-4. shell.s
REXSSAREREAEAAE ARES AAE ERA
AER EERE TAKES ERE SARA A KER
E EERE EERE CEEEES
*
*
*
Shell
program
to
be
linked
with
all
assembly
language programs.
%
x
‘
RERERETRAAERS REAR ATES ARRAS ATER AAS T AEE ARES EAE
E TARE TARR ORE EERE
xa% Program equates
bpadr
=
4
&
Stack
offset
to base page address
codelen
=
12
&
Base page offset
to Code segment
length
datalen
=
20
*
Base page offset
to Data segment
length
bsslen
=
28
&
Base page offset
to BSS
segment
length
stk
=
$490
*
size
of
our
stack
(1K)
bp
=
$190
t
size
of
base page
setblk
=
4a
® command
number
of
SETBLOCK function
aescode
=
%c8
% command
number
for
AES call
vdicode
=
$73
& command number
of
vdi
call
242%
External
references
xref
demo
%
import
the external
demo subroutine
-xdef
vdi
®& export
the
vdi
subroutine call,
.xdef
vakhnd
&
the virtual
workstation handle,
-xdef
contr1S
&
and
all
of
the
VDI
data arrays
xdef
contrlii
-xdef
contri2
xdef
contri’
-xdef
contrl4
.xdef
contrlsS
«xdeaf
contrlds
-xdef
contri?
-xdef
contris
«xdef
contrlg9
«xdef
contrilg
.xdeFf
contrlil
-xdef
intin
-xdef
intout
-xdef
ptsin
.xdeft
ptsout
33

<!-- source-page: 41 -->
## Page 41

CHAPTER 2
*&8 Program starts here.
Get
base page address
in
a5
etext
move. 1
a7,a5
*
save
a7
so
we can
get
the base page address
move.1
bpadr(a5),a5
&
a5
= basepage address
S%% Calculate the
total
amount
of
wihemory used
by
882
our program
(including stack
space)
in
dg
*
&
total
memory used
=
move. 1
codelen(a5),d@
£
length
of
code segment
add.1
datalen(a5),d@
£*
+
length
of
data segment
add.1
baslen(aS) ,dd
¥
+
length
of
uninitialized
storage segment
add.1
Hatk+bp, dd
&
+
(size
of
the base page
+
our
stack)
#k% Calculate the address
of
our
stack
&&&
and
move
it
to the stack
pointer
(a7)
3
&
stack
address
=
move.l
d@,di
x
size
of
program memory
add.1
aS,di
x
+ program’s base address,
and.1
#-2,d1
%
pick
off
odd
bit
to make sure that
the
tg
®
stack
starts
on
a
word boundary
(it
must).
move.l1
di,a7
*
set
stack
pointer
to
our
stack
%
3
which
is
stk
bytes above
end
of
BSS
#&%
Use
the GEMDOS SETBLOCK call
to reserve the
area
of
memory
$8 actually used
for
the program
and
stack,
and release the
&&%
rest
back
to the free memory
pool.
trap
#1
add.1l
#12,sp
call
GEMDOS
and clear
our
arguments
off
the stack.
move.l
d,-—(sp)
*
push
the size
of
program memory
&
(first SETBLOCK parameter)
on
the stack.
move.1
a5,-(sp)
%
push
the beginning
address
of
the
s
* program memory area
(2nd SETBLOCK parameter).
clr.w
—(sp)
%
clear
a dummy place-holder
word
move
#$4a,-(sp)
&
finally,
push
the GEMDOS command
number
*
%
for
the SETBLOCK function
*
x
&e8
Initialize the application
with appl_init
move.1
#9,resvi
% clear
global
variables
move.1
#2, reav2
move.1
#8,resvs
move.1
#0, resv4
move
#18, contr1@
*
command
= appl_init
move
#8,contrit
%
no integer
input parameters
move
#1,contr1i2
%
1
integer
output parameter
move
#2, contr13
&%
no address
input parameters
move
#3, contrl4
*
no address output parameters
isr
aes
%
do
the call
&8%
Get
the physical
screen
device handle from graf_handle
move
#77, contr1s
& command
= graf_handle
move
#9,contrli
*
no integer
input parameters
move
#5, contr12
«5S
integer
output parameters
move
#8, contr1lsS
*
no address
input parameters
move
#8,contr14
%
no address output parameters
*
jsr
aes
do the call
&&k
Open
the Virtual
Screen Workstation
(v_opnvwk)
move
#199, contr1ld
® opcode
to contrl (8)
move
#8,contril
&
no points
in ptsin
34

<!-- source-page: 42 -->
## Page 42

Setting Up the Graphics Environment
move
#11,contr1s
€
11
integers
in
intin
move
intout,contrlé
&
physical
workstation
handle
to contr
(6)
movea.l1
#intin,ad
move
#9,da
initloop:
move.w
#1, (aB)+
®
intin(@)~-intin(9)
=
1
dbra
d8,initloop
move
#2, intin+29
&
intin(19)
=
2
(Raster Coordinates)
isr
vdi
move
contrlé,vwkhnd
*
save virtual
workstation
handle
*4%
Clear
Virtual
Workstation
move
#3,contr1d
*®
clear
work
opcode
move
#08,contrili
*%
nothing
in
ptsin
move
#9,contrls
®
nothing
in
intin
isr
vdi
sx&
Do
our
demo program
jisr
demo
&&%
Wait
for
a mouse button
push
(vq_mouse)
wait:
move
#124, contr1@
*
opcode
for
Query Mouse Button
(vq_mouse)
move
#9,contril
move
#1,contrl2
*
x,y coordinates
of
mouse returned
in ptsout
move
#2, contris
move
#1,contri4
%
button
status returned
in
intout
move
vwkhnd, contrld
jsr
vdi
&%
check
the button
cmpi
#6, intout
x
if
=
8,
no button
pushed
beq
wait
%
so try again
$%*
Close Virtual
Screen Workstation
(v_clsvwk)
move
#191, contr1d
%
opcode
to contrl (8)
move
#9, contril
*
no points
in ptsin
move
#9,contrl3
*%
no integers
in
intin
move
vekhnd,contrlS
*
virtual
workstation handle
isr
vdi
#8 Finish
the application
(appl_exit)
move
#19, contr1d
* opcode
to contri (@)
move
#1, contri2
&
1
integer returned
in
inout
move
#8,contril
move
#8, contri
move
#8, contri4
isr
aes
e&%
Exit
back
to DOS
move.1
#8, (a7)
*
Push command number
for
terminate program
trap
Ri
*%
call
GEMDOS.
Bye bye!
35

<!-- source-page: 43 -->
## Page 43

CHAPTER 2
Lt $
Make AES function
call
LES
(after
setting parameters)
move.
1
#apb,dl
move.w
#aescode,
de
trap
#2
rts
&&%
Make
VDI
function
call
Su%
(after
setting parameters)
vdis
move.
#vpb,d1
move.w
#vdicode,
dg
trap
#2
rts
&*% Storage space
-data
«even
contrls
contri@s
-ds.w
contril
-ds.w
contrl2:
.ds.w
contrl3:
-ds.w
contrl14:
~ds.w
contrl15:
-ds.w
contrié:
-ds.w
contri7:
-ds.w
contrl18:
.ds.w
contrid?:
-ds.w
contrl11g:
-ds.w0
contrlilis
-ds.w
global:
version:
-ds.w
counts
-ds.w
id:
.ds.w
private:
ds.
tree:
-ds.1
resvis:
-ds.1
resv2:
.ds.i
resv3:
-ds.1
resv4;
-ds.1
intin:
-ds.w
intouts
-ds.w
addrin:
-ds.w
addrout:
-ds.w
ptsin:
-ds.w
ptsout:
-ds.w
vwkhnd
-ds.w
ft
for
AES
and
VDI
call
parameters
he
ee et eb
et te ee ee
a
128
®
intin
and
intout
used
by both
also
128
128
128
128
128
*&&
The AES
and
VDI
parameter
blocks hold pointers
kkk
to the starting
address
of
each
of
the
data arrays
apb:
-dce.l contril,global,intin,intout,
addrin, addrout
vph:
.dce.1
contrl,intin,ptsin,intout,ptsout
-end
36

<!-- source-page: 44 -->
## Page 44

Setting Up the Graphics Environment
The first part of Program 2-4 requires a bit of explanation.
When GEM starts an application program (but not a desk accessory), it allocates all of the system memory to that program.
Therefore, if the program wishes to use the system memorymanagement calls, or any of the AES calls that themselves allocate memory, it must first de-allocate all of the memory it
isn’t actually using at startup time. The way to do this is with
the XBIOS function, SETBLOCK. SETBLOCK is used to reserve
a specific area of memory for the program, and return the remaining RAM area to the Operating System’s free memory
pool. In order to execute this command, you must pass the
starting address of the area that you wish to reserve and the
size of the area. Please remember that it’s only necessary to
free memory when you start an application program, not a
desk accessory.
Finding the starting address of program memory isn’t too
difficult, since when you start the program, the second word
on the stack points to that location. Finding the size of the
program requires a
little more knowledge of how program
storage space is allocated. The memory area in which a program resides is known as the Transient Program Area (TPA).
At the beginning of the TPA is a 256-byte segment
known as the basepage. The basepage contains information
about the size and address of each program segment, as well
as the command line that is passed to the program. (These are
the extra characters you type in when you run a Tos Takes Parameters program whose name ends in .TTP.) After the
basepage comes the actual program code, followed by the data
area, and then the BSS (Block Storage Segment), which is used
to store uninitialized data. So to find the total size of the program area, we take a look in the basepage to find the size of
the code, and add that to the size of the data and BSS segments, along with the size of the basepage itself. Since we
need a stack area for the program, it makes sense to add the
size of the stack to the end of the program and reserve the
combined program and stack area together. Once we calculate
this area, we can set the stack pointer to the top of program
memory and make the SETBLOCK call. Once that’s done, we
can get on with whatever it is that our program does.
In order to assemble the shell.s program with the Alcyon
assembler, we invoke the as68 assembler with the following
command:
37

<!-- source-page: 45 -->
## Page 45

CHAPTER 2
as68 -u -l shell.s
This creates an object file called shell.o. Since this program does not contain the demo subroutine, it won’t link and
run properly. In order to get it to function, the least you must
do is to create another object module that contains that subroutine. An example of this is Program 2-5, dummy.s.
Program 2-5. dummy.s
SRTATTAAEEKERKK
EASA EERE TERETE
x
Dummy.s
--
a do-nothing
demo
SRARTEKTAEAEK
TARTAR TATE S ERE
-xdef
demo
etext
demo:
rts
-end
Assemble this file in the same way to create the dummy.o
file. Next, use the linker to join the two object modules. The
command line to use is
link68 [u] dummy.68k=shell,dummy
This creates the dummy.68k, a relocatable program module that must be modified to ran under GEMDOS, using the
relmod program:
relmod dummy
This produces the dummy.prg program file that can be executed from the desktop. This program just waits until the
user presses a mouse button, and then ends. When you substitute the graphics demo subroutines from the programs in subsequent chapters for the dummy demo routine, the program
will draw the graphics demonstration, and then waits for the
user to press the mouse button.
As with the C example programs, you may find that the
mouse pointer image disrupts the picture when you move it
for the first time, because it saves and restores the original
background image that appeared before your drawing was displayed. The solution is to either rename the program with a
.TOS extender or modify the shell program to turn off the
mouse pointer before drawing, as we will demonstrate in a
later chapter.
38

<!-- source-page: 46 -->
## Page 46

Chapter 3
Drawing Points
and Lines

<!-- source-page: 47 -->
## Page 47

2
—
-

<!-- source-page: 48 -->
## Page 48

The simplest kind of drawing that you can do
is to color in one spot on the screen at a time. The GEM VDI
provides an extremely flexible graphics type called a marker
which is used to perform this function. At its simplest, the
marker function does just what its name suggests—it marks a
single dot. But the extent of this function doesn’t stop there.
The basic marker routine, Polymarker, can be used to mark a
number of points at once. The C language format for this
function is
int handle, count, points[ COUNT*2];
v_pmarker(handle, count, points);
where handle is the ID number for the graphics workstation,
count is the number of points to mark, and points is an array
of integers which holds the x and y coordinates for each of
those points. Since each point has two coordinates, there are
twice as many elements in the points array as there are actual
points to mark. Program 3-1 is a brief program that uses the
Polymarker function to draw 64 dots in an 8 X
8
grid.
Program 3-1. pmark1l.c
/ESEKEEAAESSARASTTK
EERE AKER
EKER
EEE SEE,
‘%
a/
/t
x/
/%
PMARK1.C
-- Demonstrates use
of
the
a/
/%
Polymarker
function
to draw
a series
s/
/*t
of
points
on
the screen.
x/
/%
%/
*
xs
/EEKCESEELERESSEEAKAESAETERERE
AR RES ETERS
EE EERE,
#include
"shell.c"
demo ()
€
int
points
(1281;
/*
max
of
64 points
%/
int
x ,y3
for
(y=@;y<8;y++)
/*
for
each
row
&/
for
(x=83x<8yx++)
/%
for
each column
*/
<
pointsl (16%y)+(28x)1=
199
+
(x84);
/&
set points
&/
pointsl (16ky)+(28x)+1]
=
198 +lye4))
}
41

<!-- source-page: 49 -->
## Page 49

CHAPTER 3
3
v_pmarker (handle,
64,
points);
/&*
draw
all
of
points
&/
/%
End
of
Pmarki.c
€/
In addition to drawing dots, the Polymarker function can
be used to draw several other marker shapes as well. In our
example program, single points were drawn on the screen because when we opened the virtual screen workstation, we
specified marker type
1 (a single point) as our default marker
type in work_in[3]. But, as we saw from the information returned by the v_openvwk call in work_out[8], there are six
marker types available for use on the ST screen. These are as
follows.
Marker
Shape
Number
1
Point
2
Plus sign
3
Star
4
Square
5
Diagonal Cross
6
Diamond
To change the type of marker currently used for drawing,
we use the Set Polymarker Type command. In C, the format
for this command is
int handle, markerno, type_set;
type_set = vsm_type(handle, markerno);
where handle is the workstation ID number, markerno is the
marker shape number of the symbol you want to use, and
type__set is the marker shape number of the symbol that was
actually set. If you request a marker type that isn’t available
(for example, a number greater than 6 when using the screen
device), the VDI sets the star symbol as the current marker
ty pe
In addition to using a number of different marker shapes,
you may also specify the size, or to be more specific, the
height, of the marker you wish to use. The only exception to
this is the point marker type, which is always exactly one
pixel in size. As we have seen from the values returned by
v—openvwk in work_out[9] and work_out(53]-[56], the ST
screen offers eight different marker sizes, ranging from 15
pixels wide by 11 high to 120 pixels wide by 88 high. Since
42

<!-- source-page: 50 -->
## Page 50

Drawing Points and Lines
the biggest marker size is eight times as large as the smallest,
it stands to reason that each larger marker size is 15 pixels
wider and 11 pixels taller than the last. The C language format
of the Set Polymarker Height command is
int handle, height;
height_set = vsm_height(handle, height);
where height is the marker height that you’re requesting, and
height_set is the height of the marker that is actually set. If we
request a marker height that isn’t available, the VDI sets the
height to the next smaller height that’s supported. Since we
know the exact sizes of markers that are available on the ST
screen, we know that the height requested should be an even
multiple of 11 no greater than 88. If we did not know the size
of the markers available on another device, however, they
could be determined by repeatedly trying a height that is
1
less than the tallest known height, and seeing what value is
returned in height_set.
The final marker attribute that can be changed is the color
in which it is drawn, assuming, of course, that the program is
being run on a color monitor. With
a monochrome monitor,
the background is usually all white, and all drawing is done in
black. But on the color monitor, you can have up to four different colors on screen at one time in medium-resolution mode,
and up to sixteen different colors in low-resolution mode.
Color selection is controlled by sixteen hardware registers. You
may think of these as pens, each filled with a different color of
ink. By default, you draw with pen 1, which, unless you change
it, contains black ‘‘ink.” That default drawing pen was set by
placing a 1 in work_in[4] at the time the virtual workstation
was opened. To draw in another color, you must choose another pen with the Set Polymarker Color Index command,
int color_set,handle, pen;
pen_set = vsm_color(handle, pen);
where pen is the number of the drawing pen (hardware color
register) that you wish to use, and Pen_set shows the actual
drawing pen that was selected—which may differ from the
one you requested if you asked for an invalid pen number.
We'll discuss the default colors of the drawing pens, as well as
how to change those colors, in the next chapter.
Program 3-2 shows the five sizable marker types in five
43

<!-- source-page: 51 -->
## Page 51

CHAPTER 3
different sizes. If you have a color monitor, some of them will
appear in different colors as well:
—
Program 3-2. pmark?2.c
/RMEERERCRETER
EASE
E EERE RER ERE SARE ESSER ERR ES/
/t
a/
/*t
‘/
/*
PMARK2.C
-- Demonstrates use
of
%/
/*%
different
sizes
and
shapes
a/
_
/t
of
markers.
s/
/t
‘/
‘tk
s/
/RSEEKEREAKAEAR
SESE
A ASAE REESE REE RE,
#include
"“shell.c"”
demo‘)
£
int
points
(23;
int
x,y3
for
(y=8,points{1]=3;y<Ssy++)
/&
for
each
row
&/
4
vsm_height (handle,
1i+¢y#11))3;
/&
set
marker
height
4&/
vsm_color (handle, y+1);5
/*®
set
color
&/
points(il+=(11ky);
7&
set
points
*/
for
(x=, points(@1=(8+t
(y#B) )/23x<Spx++)
€
vem_typethandle,
2+x);
/%
change marker
shape
%/
if
(x>P) points(O@1+=(12eCy+1))3
v_pmarker (handie,
1,
points);
/*
draw marker
*/
3
3
/*
End
of
Pmark2.c
&/
You may have noticed something peculiar about the size
and positioning of the markers on the display. In order to line
them up with the left edge of the screen, it was necessary to
offset them a number of pixels from the left. That’s because
the x,y coordinate given for a marker that’s bigger than a single
point specifies the center point of that marker, not its upper
left corner. Therefore,
a marker placed at 0,0 would have both
its top half and its left half cut off by the edge of the screen.
Another thing you may have noticed is that we didn’t
have to horizontally space the markers an even multiple of 15
pixels apart. That’s because the marker size measurement is
for the marker’s cell, which includes not only the actual area
filled by the marker, but also some blank space around the
44
—_

<!-- source-page: 52 -->
## Page 52

Drawing Points and Lines
border of the marker. For example, in the 11-pixel-high plussign marker (number 2), the horizontal line is actually only 9
pixels long, not 15, and the vertical line is 7 pixels high, not
11 (Figure 3-1). The rest of the cell is taken up by blank
pixels, distributed evenly on all four sides of the marker. To
find the actual drawing width of any marker, divide the height
by 11; multiply the result by 8; then add 1. To find the drawing height, divide the height by 11; multiply that result by 6;
then add 1. The mathematical formulas are:
Drawing width =
( (height / 11) * 8) + 1
Drawing height =
( (height / 11) * 6) + 1
Figure 3-1. Polymarker 2,
11 Pixels High
If you need to know during the course of a program just
what the current Polymarker settings are, you can use the VDI
function called Inquire Current Polymarker Attributes. The
format of the C command is:
int handle,
settings[4];
vqm_attributes(handle, settings);
The function returns the current polymarker settings in
the four elements of the settings array. Element 0 contains the
current marker type, element 1 contains the pen number, element 2 holds the drawing mode (we'll explain that one in the
45

<!-- source-page: 53 -->
## Page 53

CHAPTER 3
next chapter as well), and element 3 contains the current
polymarker height.
Lines
The next step up in complexity from marking points on the
screen is drawing straight lines. As with markers, the principal
VDI line-drawing command allows you to draw several of
these at the same time. For that reason, it’s called Polyline.
The C syntax for this call is
int handle, count, points| COUNT*2];
v—pline(handle, count, points);
where count is the number of endpoints that will be joined,
and points is an array that contains the x and y coordinates for
each of these points (in the format x,y,x1,y1,x2,y2, and so on).
Since each point is described by two coordinates, there are
twice as many elements in the points array as there are points.
Although it takes two points to describe a line, the endpoint of
one line is always the beginning point of the next, except for
the first line. Therefore, the number of lines drawn by a Polyline command is always one less than the number of points.
Anytime you use the Polyline command to draw a closed
polygon, the first point and the last point will be the same. So,
in order to draw a square with Polyline, you need five coordinate pairs in the points array, with the first and last pair being
exactly the same.
Program 3-3 is
a sample program that demonstrates use
of the Polyline command.
Program 3-3. plinel.c
[gh EERE RSE ESERENASEESASTESEEESESEERS NREL SERS
/
/*
%/
/t
PLINE!L.C
-- Demonstrates use
of
the
x/
/t
Polyline function
to draw
a series
“/
/t
of
connected
lines.
%/
/t
&/
/*
a/
AERATKKARASTERAAEKAEAERE
SARTRE ERATE KEE EE /
*#include
"shell.c"
#define REPS
15
/* number
of
spirals
&/
define NEXT pointslindex++]
/*
set
next
point
&/
#define STEP
12
/%
space between
lines
&/
demo
()
t
46

<!-- source-page: 54 -->
## Page 54

Drawing Points and Lines
int
index=9,
Cs
Xsy,sxstep, ystep,dx,dy,
points({@sREPS+2);
if
(work_out(@]
== 639)dx=STEP;
/€
set
full
horiz
step
%/
else
dx
= STEP/2;
7% except
for
lo-res
&/
if
(work_outli]
== 399)dy=STEP;
/*
set
full
vert
step
%/
else
dy
=
STEP/2;
/*% except
for
color
&/
xstep
= work_out(OI]—-dx;
/*
set
horiz
line
length
&/
ystep
= work_out[ij-dy;
/*%
set
vert
line
length
*/
NEXT
=
x
= dx/2;
/%
set
first
point
4%/
NEXT
=
y
=
dy/23
/%
For
each repetition
of
the spiral...
&/
for
(c=#83c<REPS;
c++)
€
NEXT
=
(x+=xstep);
/%
set
four
x,y coords
&/
NEXT
=
y3
NEXT
=
x3
NEXT
=
(y+=ystep) 3
NEXT
=
(x-=(xstep-adx))3
NEXT
=
y3
NEXT
=
x3
NEXT
=
(y-=(ystep—=dy));
ystep
—=dy;
7%
& change the
line
lengths
&/
xstep
-—=dx}3
3
4%
draw
all
of
the
lines
&/
v_pline(handle,
48REPS+1,
points);
3
4%
End
of
Plinet.c
%/
As you can see, Program 3-3 adapts itself to any type of
monitor by reading the horizontal and vertical resolution from
work_out[0] and work_out[1], and scaling the length of the
lines and the size of the space between lines accordingly. Notice also how the use of macro definitions like NEXT, STEP,
and REPS saves a
lot of typing and allows us to easily vary
the size between the ‘‘squirals” and repetitions (though if you
want more than 15 repetitions you will have to increase the
size of the ptsin array in the shell program). These macro definitions also have value as program documentation.
Patterned Lines
In addition to solid lines, the VDI also lets you draw patterned
lines composed of dots and/or dashes. In order to draw these,
we must set the line-drawing pattern with the Set Polyline
47

<!-- source-page: 55 -->
## Page 55

CHAPTER 3
Line Type command. The C
syntax for this routine is
int handle, pattern;
pattern_set = vsl_type(handle, pattern_no);
where pattern_no is the number of any of the seven available
line-drawing patterns. The number of the pattern that was actually set is returned in the variable pattern_set.
The line-drawing pattern is composed of 16 pixels lined up
in a row. Each pixel is either colored in with the line-drawin
color (on), or colored in with the background color (off). These
patterns can be represented by a single 16-bit binary (base 2)
number. For example, a pattern in which an “on” pixel alternates with an “off” pixel can be represented by the binary
number 1010101010101010, which has a decimal value of
43690. The Atari ST screen driver supports seven types of
line-drawing patterns (as we saw from the value returned in
work_out[6] when we opened the virtual screen workstation).
These are (see Figure 3-2)
Pattern
Number
Binary value
Pattern
1
1111111111111111
Solid line
2
1111111111110000
Long dash
3
1110000011100000
Dotted line
4
1111111000111000
Dash-dot
5
1111111110000000
Dashed line
6
1111000110011000
Dash-dot-dot
7
User-defined style (must be set with vsl_udsty call
before vsl_type call)
The reason that we get a solid line as our default pattern
is because we placed a
1 representing pattern number 1 in
work_in[3] when we opened our virtual workstation, thus requesting the solid line as our default. As long as the GDOS
extension is installed, however, it’s possible to specify another
value as the default. If the GDOS extension is not installed,
the default line type will be the solid line, regardless of the
value you put in work_in[3]. Another point to note about
these line-drawing patterns is that the VDI makes no attempt
to scale them according to the screen display used, so the pattern may look fatter or thinner depending on whether you are
in lo-res, medium-res, or hi-res mode. And, since the horizontal resolution varies significantly from the vertical resolution,
the pattern of a dotted line that is drawn horizontally looks
quite different from that of the same line drawn vertically.
48

<!-- source-page: 56 -->
## Page 56

Drawing Points and Lines
Figure 3-2. The Six GEM VDI Line-Drawing Patterns
: ISS SESSeeee
=
fn
‘2
86nn
‘ SESE
‘=
=
En
Although the VDI supplies six preset line patterns for the
sake of convenience, it also provides for a user-defined style,
which allows you to choose any of the 65,536 possible combinations of lit and unlit pixels for the line-drawing pattern.
Before we select pattern 7, however, we should first tell the
VDI which pattern it represents. We do this by calling the Set
User-Defined Line Pattern function. In C, this function appears
in the following format:
int handle, pattern;
vsl_udsty (handle, pattern);
where pattern is a 16-bit number representing the 16 pixels of
the line-drawing pattern. As stated above, the way to translate
the on/off patterns into a 16-digit base-2 number is by writing
a
1 for every lit pixel and a 0 for every unlit pixel. In binary
math, the rightmost digit has a value of 1, and each subsequent
digit has a value that is twice that of the digit to its right.
Therefore, the binary number 1010 has a decimal value of 10:
Binary digits
1010
Decimal value of each digit
8020
8+0+2+0 = 10
49

<!-- source-page: 57 -->
## Page 57

CHAPTER 3
Line Color
On ST systems that have a color monitor, you can specify
which drawing pen will be used for line drawing, and thus
control the color of the line that is drawn. On the monochrome system, you're limited to pen 0 (white) or pen
1
(black). The VDI command for selecting the pen is Set
Polyline Color Index, which corresponds to the following C
function:
int handle, pen_number
set_color = vsl_color(handle, pen_number);
where pen—number is the number of the drawing pen to use.
The pen number is referred to in the GEM literature as the
color index, since it represents an offset from the beginning of
the color lookup table. Pen 0 is the background color, and pen
1 is the default foreground color (black), which we set with
work_in[2] when we opened the virtual workstation. If you select a color higher than the number of colors available, pen
1
will be set. We'll discuss the other color defaults and how to
change them in the next chapter.
Program 3-4 demonstrates the use of the line-drawing
pattern settings and the color settings with the Polyline
command.
Program 3-4. pline2.c
/RARECRARTEREREK
SAREE
A EKER ERE RRR
RER EKER EE /
/%
s/
/t
x/
/*%
PLINE2.C
-— Demonstrates patterned
x/
/t
line drawing
and
color selection
“/
/t
a/
‘
“/
/k
a/
ARREARS
KARAS R TEASER EEE,
#include
"shell.c"
define
REPS
4
/@ number
of
polygons
to
draw
&/
#define STEP
15
/* distance between
them
*/
demo()
€
int
index=,
Cy
XoVs
xmax,xmin,
ymax, ymin,dx,dy,
points{18];
if
(work_out(@]
== 4639)dx
= STEPK2;
/&*
full
horiz
step
%&/
else
dx
= STEP;
7%
axcept
lo-res
&/
if
(work_outli]
== 399)dy
= STEPK3;
/&
full
vert
step
&/
else
dy
=
(STEP&3)/2;
/7* except
for
color
&/
50

<!-- source-page: 58 -->
## Page 58

Drawing Points and Lines
xmax
xmin
ymax
ymin
work _outl@J—(3kdx)
5
/*
set
initial
margins
%/
3kdx;
work _outlt];
a;
/%
Set user-defined
line drawing pattern
%/
7%
OxAAAA
=
1918191919191919 binary
&/
vsl_udsty (handle,
@xAAAA);
for
(c=8;c<REPS;c++)
/*
for
gach
polygon
*/
€
pointsl€12]=points(i4]
=
xmin;
/%&
set points
%/
points(@1=points(1@]=points(16]
=(
xmintedx);
pointsliJepoints(3J=points([17]
=
ymin;
points(S)=pointsl15]
=
(ymint=dy);
pointsl4I=pointsl(6]
=
xmax;
points{€2J=points(8}
=
(xmax-=dx);
pointsl(9]=points(i1]
=
ymax;
points(€723=pointsli3]
=
(ymax—-=dy);
xmint=dx;
/k
shorten offsets
&/
xmax —=dx
5
vsl_color (handle,
1+c);
/*
change colors
&/
vsl_type(handle, t+(c&k2));
/&
change
line pattern
&/
v_Pline(handle,
9,
points);
/
draw
the polygon
&/
3
>
/*%
End
of
Pline2.c
&/
Line Width
In Program 3-4, the lines that were drawn were all 1 pixel wide.
But as you can see by the values returned in work_out[7],
work_out[49], and work_out[51] when we opened the virtual
workstation, the ST display driver can draw lines in any width
from 1 pixel to 40 pixels. The function used to specify the
width of the lines that the VDI draws is Set Polyline Line
Width, which in C looks like this:
width_set = vsl_width(handle, width)
where width is the line width in pixels. In order to keep everything symmetrical, the VDI only uses odd-numbered line
widths. If you request a line width that’s unavailable, either
because it’s larger than the maximum width or because it’s an
even number, the VDI will set the width to the next lower
available width. The actual line width that was set by the call
is returned in the variable width_set.
Although most of the line-drawing settings can be used
together, patterned lines cannot be drawn on the ST screen if
their width is set to a value greater than one pixel. Whenever
51

<!-- source-page: 59 -->
## Page 59

CHAPTER 3
you use thicker lines, they are drawn as solid lines, regardless
of the current line-pattern setting.
Line End Styles
The final line-drawing setting is a fairly obscure function that
allows you to designate the end style for the line. By default,
the ends of a line are squared off, but by using the Set
Polyline End Styles command, you may instruct the VDI to
round off either end of the line, or to place an arrow head at
either end of the line. The arrow head is positioned so that its
tip is placed at the last point of the line. Although the GEM
literature states that the rounded end is drawn so that the center of the rounded line is positioned at the end of the line,
experience on the ST shows otherwise. The rounding is added
on to the end of the line, increasing its length by about half its
thickness. While arrows can be used with any width of line,
the rounding is not really noticeable unless you are drawing a
line that is thicker than five pixels. The syntax of the C command used to set the end styles is
int handle, begin_style, end_style;
vsl_ends(handle, begin_style, end_style);
where begin_style and end_style contain a number code from
0 to 2, indicating what style will be used to draw the beginning and end of the line. The number 0 represents a squaredoff end,
1 indicates that an arrow is to be drawn, and a 2
means that the end should be rounded off. If an invalid number is given for either of these, the squared-end style is selected by default.
Program 3-5 shows the use of thickened lines, and of the
two stylized types of endpoints.
Program 3-5. pline3.c
/RERTEREEKEREAEE
EKER ESTERASE REAR
E/
/*
a/
/%
s/
/t
PLINES.C
-- Demonstrates drawing
a/
/%
lines
of
various widths
and
end styles
x/
/t
x/
/&
a/
/t
x/
/ERRECEERAERSEAKE
EERE EKER EA SESE EKER ERE EERE EES
#include
"shell.c"
#define
REPS
5
/* number
of
wide
lines
to draw
%/
52

<!-- source-page: 60 -->
## Page 60

Drawing Points and Lines
demo ()
€
int
index=@,
cs
xmax,xmin, ymax,dy,
points([é];
points(i]
=
12;
/*
set margins
and offsets
*/
dy
=
31;
xmax
=
work _out(@J+16;
ymax
= work_outlil+i19;
xmin
=
(-28dy);
/&
make beginning
of
line rounded,
end w/arrowhead
&/
vsl_ends(handle,2,1);
for
(c=8;c<REPS;c++)
/&
for
each
line
%/
€
points([@]
= points(2]
=
(xmax-=(dy+4));
/&%
set
points
&/
points(4]
=
(
xmin+=(28dyt+18)
)3;
points(3]
=
points(€S53=
(
ymax—-=(dy+198)
);
vsl_width(handie,
(dy-=6
)
>;
/%
change width
%/
vsl_color (handie,ct1)3
/@ change colors
%/
v_pline(handle,
3,
points);
/%
draw
it
&/
3
3
/*
End
of
Pline3.c
&/
If you ever need to find out from your program what the
current line-drawing settings are, you can use the function Inquire Current Polyline Attributes (though this is fairly inefficient, as you should be able to keep track of the settings in
the program without having to inquire). The C format for this
call is
int handle, settings[4];
vql_attributes(handle, settings);
where settings is the address of the array in which the function
stores the current line-drawing settings. After the call has been
successfully completed, the following information can be
found in the various elements of the array:
Element
Setting
[0]
Line pattern
[1]
Line-drawing pen
[2]
Draw mode
[3]
Line width
The function also returns the beginning end style and the
ending end style in intout(3} and intout[4], respectively. These
53

<!-- source-page: 61 -->
## Page 61

CHAPTER 3
values are not transferred to the settings array by the C function bindings.
Line-Drawing GDPs
There are some other VDI functions that draw figures using
lines, and these functions share the same line-drawing settings
as Polyline. For reasons having to do with the older graphics
systems from which they evolved, they’re referred to as Generalized Drawing Primitives, or GDPs, for short. The only
practical programming difference between GDPs and any
other drawing function is that they all have the same opcode,
so assembly language and BASIC programmers will have to
remember to set both the opcode in contrl(0) and the subfunction ID in contrl(5) before calling one of these functions. C
programmers will not have to worry about this, since the
bindings take care of this detail for them. The line-drawing
GDPs allow you to draw circles, or any part of a circle; ellipses, or any part of an ellipse; and rounded rectangles.
The first of these functions is called Arc, and it allows you
to draw any segment of a
circle. The C function call is
int handle, x, y, radius, begin_angle, end_angle;
v—arc(handle, x, y, radius, begin_angle, end_angle);
where x and y are the coordinates for the center point of the
circle, radius is its radius, and begin_angle and end_angle give
the starting and ending points of the arc.
In order to know which beginning and ending angles to
specify to draw a particular segment of the circle, we have to
understand how the VDI refers to angles. The interior angles
of a circle add up to 360 degrees, and since the VDI thinks in
tenths of a degree, the points on a
circle go from 0 to 3600.
The VDI designates the rightmost point on the circle (the three
o’clock position) as 0 or as 3600, depending on whether it’s
used as the starting angle or ending angle. All drawing proceeds in a counterclockwise direction, so the topmost point is
designated 900, the leftmost as 1800, and the bottom-most as
2700 (Figure 3-3).
54
—_—

<!-- source-page: 62 -->
## Page 62

Drawing Points and Lines
Figure 3-3. Drawing Angles
388
1808
3600
2708
Thus, to draw the top right quarter of a circle whose center point is at 100,100, and whose radius is 50 pixels, you use
the command:
v—arc(handle, 100, 100, 50, 0, 900);
To draw a complete circle, you need only to specify 0 as the
starting angle, and 3600 as the ending angle.
Keep in mind that the VDI adjusts the vertical radius of
the circle for the aspect ratio of the display screen (the ratio of
the width of each pixel to its height), so it always appears to
be round. If it did not make this kind of adjustment, a
circle
that appears round on the low-resolution screen would look
tall and thin on the medium-resolution screen. To find the effective vertical radius of the circle, multiply the radius by the
value that was in output[3] after you opened the workstation,
and divide the result by the value that was in output[4]. Thus,
the box that contains a
circle with radius r
is r units wide and
(r * work_out[3] / work_out[4]) units high. An almost identical function allows you to draw any segment of an ellipse. The
only difference between a
circle and an ellipse is that the vertical radius of a circle is automatically calculated to scale from
55

<!-- source-page: 63 -->
## Page 63

CHAPTER 3
the horizontal radius that you supply, so that it always appears to be round, while you supply both the horizontal and
vertical radius values for the ellipse, so that it may be oval in
shape. The C
call for the Elliptical Arc function is:
int x, y, xradius, yradius, begin_angle, end_angle;
v—ellarc(handle, x, y, xradius, yradius, begin_angle, end_angle);
All of the parameters for this call are the same as those used
by Arc, except, instead of a single radius, there are variables
for both the horizontal (xradius) and vertical (yradius) radii.
The final line-drawing function is called Rounded Rectangle. As its name suggests, it’s used to draw rectangles whose
corners are rounded. GEM applications often use rounded
boxes in dialogs as push buttons, as they give the program a
more polished look than do boxes with square corners. Since
you cannot control the amount of rounding, however, you'll
find that some of the smaller rounded boxes look more like
circles.
One thing to note about rounded rectangles is that they’re
affected by line-drawing settings like line width and pattern,
but not by end styles, since, properly speaking, they have neither beginning nor ending points. The C syntax for the
rounded rectangle function is
int handle, sides[4]
v_tbox(handle, sides);
where sides is an array that gives the coordinates for the four
sides of the box. The elements of this array are:
Element
Position
[0]
Left Edge
{1]
Top Edge
[3]
Right Edge
[4]
Bottom Edge
Program 3-6 demonstrates the use of the line-drawing
GDPs, and shows how they are affected by the various linedrawing settings.
56

<!-- source-page: 64 -->
## Page 64

Drawing Points and Lines
Program 3-6. gdplinel.c
/ERTEERATTELECARECEAE
REESE RARER
EERE /
/t
/%
/*
/t
/%
/%
/%
a/
%/
GDPPLINEi.C
-- Demonstrates use
of
the
s/
line-drawing
GDP functions,
and
how
s/
they
are affected
by
line settings.
%/
s/
s/
/RRSEAESSAAERESARERKKAARE
TEASE SELES ESSER RREAEE/
#include
“shell.c"
#define STEP
18
7%
space between
lines
&/
int
dx,
dy;
demo ()
¢
if
(work_out(@]
== 639)dx=STEP;
/%#
set
full
horiz
step
%/
else
dx
= STEP/2;
/%
except
for
lo-res
t/
if
(work_outCld
== 399)dy=STEP;
/%
set
full
vert
step
*/
else
dy
=
STEP/2;
/®& except
for
color
&t/
showarc
()
3
/&
do circle demo
&/
showellarc();
/&
do ellipse demo
%/
showr box
4)
3
/%
do rounded rectangle demo
s/
>
showarc
()
€
/
}
int
c}
vsl_width (handle,dx);
/®
set
wide
line
&/
for
(c™lge<8yc++)
€
vel_color (handle,c);
/® change color
%t/
% draw concentric semi-circles
%/
v_arc (handle, 178dx, 20&dy, ck (dx+dy) +dx+dy, 8, 1998) 3
3
showel larc ()
>
int
cs;
vel_width (handle, 1);
/&
line width
to
1
&/
vsl_udsty (handle, @xAS5A5);
/® define
line pattern
7
&/
for
(cmlpc<iOsc++)
vsl_color (handle,c)3
/%&
change color
%/
vel _type(handle,c);
/*
change
line pattern
&/
/%
give
last ellipse arrow heads
%/
if
(c>8)
vsl_endsthandle,1,1)4
v_@llarc (handle, 48%dx, 20%dy, dx tc, dy&c#2,9, 3600)
5
3
showr box
()
int c,pointsl4];
57

<!-- source-page: 65 -->
## Page 65

CHAPTER 3
vsl_type(handle,
3);
for
(cmOpc<Syc++)
€
vsl_width (handle,c%2)3;
/&
set
width
«/
vsl_color (handle,c)}
7%
and color
&/
points(@I=(c+1) &dx+(3ke);
pointsl
i J= (c+22) &dy+c}
points£2J=work_out(@I]—(c+26)
&dx—(3kC) 3
points(3J=work_outlij—(c+1)
&dy—c}
v_irbox (handle, points) 3
3
}
/*
End
of
Plinet.c
%/
Assembly Language Example
Though the principles of using the VDI line-drawing functions
are the same in assembly language as in C, the assembly language programmer does have to move the input parameters
directly into the VDI data arrays. In order to illustrate this process, compare the assembly language version of the GDP lines
program (Program 3-7) with Program 3-6. By comparing the
two versions, assembly language programmers should get a
better idea of how to translate the other C sample programs to
assembly language.
You may notice that in some of the assembly language
VDI calls, we didn’t bother to set all of the contrl and intin
values if we knew that they were set correctly during previous
calls. Generally speaking, the VDI will not disturb your input
parameter arrays, so once you put the workstation id handle in
contrl6, for example, you can assume that it will still be there
for subsequent VDI calls. Keep in mind, though, that as we
have set things up here, the VDI and AES share the contrl array, so if your program uses AES calls, you should be aware of
the possibility for interference from that quarter. Also, since
the process of calling the VDI uses registers d0 and d1, you
must preserve the contents of those registers if you want them
to survive between GEM calls. In general, you should assume
that the ST system will use the first couple of data and address registers, and not place values that you wish to preserve
between system calls in those registers.
58

<!-- source-page: 66 -->
## Page 66

Drawing Points and Lines
Program 3-7. gdplines.s
EECECKESELTSASAASARKSSSAKRSEKE
RSAC
ESTE EEE
+ 9
x
*
bs
GDPLINES.S
-- assembly version
of
%
*
GDP
line drawing
demo
’
s
x
x
x
x
:
RESKAETTTAATAR
TESA
TEEE RRA TR EATER
EASE SE
-xdef
demo
»xref
vwkhnd
-xref
contrigs
-xref
contrli
-xref
contr12
xref
contrls
-xref
contrl4
-xref
contrisS
«xref
contrié
xref
contrl7
«xref
contrla
«xref
contrl9?
xref
contrlig
«xref
contrilt
xref
intin
«xref
intout
.xref
ptsin
-xref
ptsout
«text
demor
move
dx, dB
move
dy,di
cmp
#639, intout
&£
if
high-res
or
med-res
bne
skipi
add
d8,de
& double
dx
move
dS, dx
skipis
cmp
#399, intout+2
*&
if
high-res
bne
skip2
add
di,dt
move
di,dy
&
double
dy
skip2:
jar
showarc
%
do
arc
demo
jsr
showel1
%
do ellipse demo
imp
showr box
&
do rounded rectangle demo
&2% Showarc
subroutine
showarc:
a%%
Set
line width
move
#16,contr1@
&« opcode
for
line width
move
#1,contril
&
1
point
in ptsin
move
#2,contr13
%
no
integer parameters
in
intin
move
dx, ptsin
move
#2, ptsin+2
&%
set
width
to
dx
isr
vdi
move
#6,d4
%
loop counter
59

<!-- source-page: 67 -->
## Page 67

CHAPTER 3
arc:
skx
Set
line color
move
#17, contr1d
move
#2,contri1i
move
#1,contris
move
d4,intin
jer
vdi
&%%
Draw
arc
move
#11, contr1s
move
#4, contrli
move
#2,contris
move
#2, contrl1S
move
#O,intin
move
#1890, intin+2
lea
ptsin (PC) ,ad
move
#7,d8
iloop:
move
4B, (ad) +
dbra
dg,iloop
move
dx, d@
move
d3,di
move
dy,d2
aulu
#17,da
move
d@,ptsin
add
d2,di
move
d4,d0
addq
#2,d9
mulu
d@,di
move
di, ptsinti2
mulu
#28,d2
move
d2,ptsin+2
isr
vdi
dbra
d4,arc
rts
&2%
Showell
subroutine
showell:
sk&
Set
line width
move
move
move
move
move
isr
Sex
Set
move
move
move
move
isr
move
60
#16, contr1d
#1,contril
#8, contrlsS
#1, ptsin
#8, ptsin+2
vdi
#113, contris
#9,contril
#1,contr1s
em
opcode
for
line color
no points
in
ptsin
1
integer parameter
in
intin
line color
opcode
for
GDP
4 points
in ptsin
2
integer parameters
in
intin
GDP
ID
for
arc
&
starting
& ending
angle
&
zero out ptsin(G)-(7)
*
get
dx
and
save
a copy
&
x
coord
of
circle center
&
dl
=dx+dy
%
dO
=
d4+2
*
radius
of
circle
to
di
®
y coord
of
circle center
% opcode
for
line width
*%
1
point
in ptsin
%
no integer parameters
in
intin
&
set
width
back
to
1
user-defined
line pattern
%
opcode
for
line width
%
no point
in ptsin
3
1
integer parameter
in
intin
#$ASAS,intin
* dotted
line
vdi
48,04
*
loop counter

<!-- source-page: 68 -->
## Page 68

Drawing Points and Lines
ell:
axk
Set
line color
#17,contrl®
% opcode
for
line color
*
contrli
and contrl3
set
by
last
vdi
call
move
move
isr
d4,intin
vdi
aaa
Set
line type
#15,contr19
*€ opcode
for
line pattern
move
& contrli,
isr
cmp
bne
move
move
move
move
move
isr
skips:
*
line color
contri3
and
intin
are still
set correctly
from
last
call
vdi
#1,d4
skips
#198,contrl@
&
#2, contril
x
#2,contr1ls
x
#i,intin
#i,intine?
*
vdi
33%
Draw ellarc
move
move
#1i,contr1®
%
#2,contrli
x
*
2
integer parameters
in
move
move
move
move
move
move
aove
fulu
move
move
addq
mulu
move
mulu
add
move
mulu
move
isr
dbra
rts
8&8 Rounded rectangle demo
#64,contr15
x
#9,intin
#3609, intint+2
dx,d@
3@,di
dy,d2
d2,d3
448,09
d9,ptsin
d4,d8
#1,d9
d8,d1
di, ptsin+4
d8,d3
d3,d3
d3,ptaint+s
#29,d2
d2, ptsint2
vdi
d4,ell
opcode
for
set
end styles
no points
in ptsin
2
ints
in
intsin
arrows
at
both
ends
opcode
for
GDP
2 points
in ptsin
intin,
same
as
last
call
GDP
ID
for
ellarc
%
mo
7
starting
&
get
dx
and
get
dy
and
x
coord
of
dv
= d4+1
times
dx
xradius
of
yradius
of
y coord
of
ending angle
Save
a copy
save
a copy
ellipse
ellipse
ellipse
ellipse center
61

<!-- source-page: 69 -->
## Page 69

CHAPTER 3
showrbox:
ake
Set
line type
®
opcode
for
line pattern
%
no points
in
ptsin
*
1
integer parameter
in
intin
%
line pattern
3
*
set
counter
a
move
#15, contr1d
move
#8,contril
move
#1, contr13
move
#3,intin
jer
vdi
move
#4,d4
rbox:
$k
Set
line color
move
#17, contr1@
*
move
#8,contril
s
move
#1, contril3
move
d4,intin
jsr
vdi
asx
Set
line width
%
opcode
for
x
no points
&%
1
integer
®
line color
% opcode
for
x
1
point
in
%
no
integer
line color
in ptsin
Parameter
in
intin
line width
ptsin
parameters
in
intin
move
#16, contr1?
move
#1,contrli
move
#8, contrlsS
move
d4,d05
add
d3,d5
move
d35,ptsin
move
#9, ptsin+2
jsr
vdi
&
set
width
to
2
tc
#%%
Draw rounded rectangle
move
move
x
move
move
move
move
move
move
move
addq
mulu
subq
mulu
add
move
move
add
mulu
add
move
move
addq
mulu
add
mulu
sub
move
62
#11, contrl1d
#2,contril
#8, contr1lS
#8,contrlS
dx, de
dB,dt
dy,d2
d2,d3
d4,d5
#1,0d5
d5,d@
#1,d5
43,05
d3,da
d9,ptsin
d4,0@
922,09
d@,d2
d4,d2
d2,ptsint+2
d1,d2
#4,d8
d@,di
di,d3
#64,d2
d5,d2
d2,ptsint4
% opcode
for
GDP
*
2 points
in
ptsin
&
@ integer parameters
in
intin
*
GDP
ID
for
rounded rectangle
%
get
dx
and
save
a copy
®
get
dy
and
save
a copy
%
copy the counter
Bs
ct+t
®
(c+1) &dx
dS
=
3%c
&
first
x
of
box
d@=c
+
22
times
dy
&%
first
y
of
bax
put
dx
in
d2
d@
= c+26
times
dx
+
34c
screen
max
- offset
second
x
point
owe
oe

<!-- source-page: 70 -->
## Page 70

Drawing Points and Lines
move
d4,d9
Sd@=ac
addq
#1,dd
&
+1
mulu
d3,da
&
times
dy
add
d4,d¢
+e
mulu
#48,d3
&
max
y
sub
d8,d3
&
-offset
move
d3,ptsint+&
*%
second
y coord
jsr
vdi
dbra
d4,rbox
rts
a%%%
data section
-data
-even
dxs
-dc.w
s
dy:
-dc.w
t]
.end
Line-Drawing VDI Calls and BASIC
ST BASIC doesn’t support VDI Marker commands, and it supports some, but not all, of the line-drawing functions. It is
quite possible, however, to access the remaining functions
with VDISYS(1) calls. Of the line-drawing functions that we
have discussed, ST BASIC fully supports arcs and elliptical
arcs. The syntax for these commands is very similar to that of
the C functions:
CIRCLE x, y, radius [,start angle, end angle]
ELLIPSE x, y, xradius, yradius [,start angle, end angle]
where the input parameter values are the same used by
v—arc( ) and v_ellarc( ). ST Basic does not support the
rounded rectangle function with its own keyword.
Of the line-drawing settings, ST BASIC supports the set
line-drawing color function:
COLOR text color, fill color, line drawing color, fill style, fill
index
The third input parameter of this command is used to set the
line-drawing color. ST BASIC does not contain commands for
setting line width or end styles. While the first ST BASIC does
63

<!-- source-page: 71 -->
## Page 71

CHAPTER 3
not allow you to set the line-drawing pattern, it appears that
the upgraded BASIC will contain
a LINEPAT command:
LINEPAT pattern number, user-defined style
where pattern number is the pattern chosen, and user-defined
style is the 16-bit pattern value that is set with vsl_udsty( ).
Likewise, though the first ST BASIC only allows you to draw
one line at a time using the LINEF command, the new BASIC
will probably offer the MAT DRAW or MAT LINEF command:
MAT LINEF points, array
where points is the number of vertices, and array is the name
of a data array holding the x and y coordinates for those
vertices.
Program 3-8 shows the use of the VDISYS( ) command to
make direct calls to the VDI functions from BASIC. Note particularly that the settings you make using these functions, such
as line width and drawing pattern, do have an effect on the
output of keyword commands such as LINEF and CIRCLE.
Program 3-8. lines.bas
1989
fullw
2:
clearw
2
118
res
=
peek (systab)
111
if
(res<4)
then
xmax
=
639 else xmax
=
319
112
if
(res>1)
then
ymax
=
199 else ymax
= 399
128
REM
Set polymarker
Height
138
poke contr1,19
:REM opcode
for
set
pmarker
height
148
poke contril+2,
1
:REM number
of
points
in
ptsin
158
poke contri+és,
@
:REM nothing
in
intin
array
168
poke ptsin,®
178
poke ptsin+2,77
:REM height
of
marker
1868
vdisys(1)
198
REM
208
for
x=@
to
4
218
REM
228
REM
Set Polymarker
color
238
poke contrl,28
:REM opcode
246
poke contrl1+2,¢
238
poke contri+é,i
269
poke intin,x+1
278
vdisys(1)
288
REM
Set Polymarker
type
298
poke contr1,18
308
poke contrl+2,2
318
poke contr1+é6,1t
328
poke
intin, 2+x
339
vdisys (1)
348
REM Draw Polymarker
358
poke contri,7
36a
poke contrl1+2,1
378
poke contr1+é6,@
38s
poke ptsin, 618x+3¢
398
poke ptsin+2, ymax/4
409
vdisys(1)
419
REM
64

<!-- source-page: 72 -->
## Page 72

Drawing Points and Lines
426
430
44@
450
4698
478
480
490
Soo
Sig
520
53a
549
550
368
57a
560
5928
688
618
628
630
648
658
668
678
689
699
708
719
726
73a
74D
758
766
778
788
798
890
819
828
825
827
836
849
856
next
REM
for
x
=
6
to
§
REM
REM Set
line drawing pattern
poke contrl1,15
poke contr1+2,9
poke contrl+é4,1
poke intin,x+2
vdisys (i)
REM
REM Draw Rbox
poke contri,1i1
poke contrl+2,2
poke contri+é,8
poke contrli+18,8
poke ptsin, 19+(188x)
poke ptsint2,
ymax /2+(7%x)
poke ptsin+4, (xmax/2)—(198x)
poke ptsin+é, ymax-20— (78x)
vdisys(1)
REM
next
x
REM
REM
Set
End
Styles
poke contrl, 198
poke contri+2,8
poke contr1+é6,2
poke intin,1
poke intin+2,2
vdisys(1)
REM
for
x
= @to
3
REM
Set
Line Width
poke contri,16
poke contri+2,t
poke contrl+é,a
poke ptsin, 15-(¢(x*5)
poke ptsint+2,2
vdisys (8)
REM
color
1,8,x+2
REM
linef xmax—-60-(49%x)
, 58, xmax—-S8—(298x) , ymax-76
rem
next
x
65

<!-- source-page: 74 -->
## Page 74

Chapter 4
Color and Other
Graphics Settings
aaa ea ea

<!-- source-page: 75 -->
## Page 75

A
al

<!-- source-page: 76 -->
## Page 76

Now that you've had a
little experience using some
of the output functions, let’s take a look at some of the settings
that can affect graphics output, regardless of the output function used. These include color settings, drawing modes, and
clipping rectangles.
Color Settings
In the previous chapter, we discussed how to change the color
of the line or marker being drawn, but we didn’t explain how
you could select a particular color like red or green. In order to
do so, we must examine the way in which different colored
dots are displayed on the ST’s color screen.
On the monochrome ST, the display system is very simple. Each dot on the screen is represented by a single binary
digit (bit) of memory. Screen memory is organized in such a
way that the first byte represents the 8 dots in the top left corner of the screen, and each succeeding byte represents the
next 8 dots to the right. Since each line contains 640 dots
across, the first 80 bytes fill up the top line, and the next byte
is used to represent the first 8 dots on the second line. There
are 400 lines of 80 bytes each on the monochrome screen,
which means that 32,000 bytes of screen memory are used to
represent the 256,000 dots on screen. (See Figure 4-1.)
Figure 4-1. Monochrome Screen Memory
1116181
oe
eee
69

<!-- source-page: 77 -->
## Page 77

CHAPTER 4
Each bit of screen memory can hold either the number 0
or 1. On a monochrome system, only one bit is needed to represent a screen dot or pixel (picture element), because each dot
on the screen is either white (off) or black (on). But with a
color ST system, things are somewhat different. In medium-res
mode, any dot can be one of four colors. Two binary digits are
used to yield four possible combinations:
-e OO
RP OF
©
WNe
©
In lo-res mode, any dot can be
1 of 16 colors, so four bits
are required to describe a single pixel. Color screen memory is
organized in much the same way as monochrome screen memory, except, instead of single bits, groups of bits are used to
represent each screen dot. Thus, in medium resolution the first
byte of screen memory is used to depict the four pixels at the
top left corner of the screen. The two high-order bits specify
the color in the first dot, the next two the color in the following dot, and so on. Since there are 640 dots per row, each row
requires 160 bytes of screen memory. But since there are only
200 rows of dots, 32,000 bytes of screen memory are still sufficient to display all of the dots on the screen. In low resolution, each byte describes only two dots of color. There are only
320 dots per line in this mode, however, so 160 bytes describe
all of the dots in each line in this mode also. (See Figure 4-2.)
Figure 4-2. Low-Resolution Screen Memory
iti
8181
ree
|
V
fofif2{3[4]s]e]7]s]9]iel
ss) 12]13]14 [15]
Hardware color registers
70

<!-- source-page: 78 -->
## Page 78

Color and Other Graphics Settings
In monochrome mode, each bit pattern can represent a
specific color, because there are only a
total of two colors
available. But the ST is capable of displaying 512 different colors on an RGB color monitor or television set. Clearly, in color
mode each set of bits cannot represent a particular color, using
a code where 0 represents white,
1 stands for black, and so
on. Instead, the number stored in the memory location that
corresponds to a screen dot location refers to a hardware color
register.
Color Registers
The color registers may be thought of as a set of 16 pens, each
of which may be filled with ink that is colored in any of the
512 shades supported by the ST. Register 0 always holds the
color we think of as the background color (which defaults to
white on the ST). When you wish to use another color to draw
a line or a point, you specify the pen (color register) that will
be used to draw it. Whatever color “ink” it currently contains
is the color that the pen will draw onscreen.
Unlike ink, however, the color of a dot that you have
drawn onscreen can change after you have drawn it. When
the display memory for a screen dot holds the number of a
particular pen, that dot is displayed in whatever color is in the
pen at any given moment, not in the color that was in the pen
at the time the dot was drawn. This means that if you use pen
1 to draw a
line, and that pen contains the default color black,
the line will be black. But if you change the color in pen 1
to
green after you’ve drawn the line, the line you drew and everything else on the screen that was drawn with pen 1
will instantly become green.
The two factors that determine which colors are assigned
to the figures that you draw on the screen, therefore, are the
pen you used for the drawing and the color currently contained in that pen.
As we’ve seen above, you can choose a different pen for
drawing markers and lines by using the vsm_color and
vsl_color calls. And we will see later that you may also select
another pen for graphic text with the vst_color call, and one
for filled shapes with vsf_color.
In BASIC, all but the marker pen are set with the same
command, COLOR. If you do not specify a pen before drawing, you'll get the default drawing pen that is specified in the
71

<!-- source-page: 79 -->
## Page 79

CHAPTER 4
work_in array at the time that the virtual screen workstation
was opened (usually color 1, which has a default value of
black). You should be aware that the GEM VDI drawing pens
(referred to in the GEM literature as the color index) do not
correspond numerically to the ST color registers. GEM uses a
complex scheme for mapping drawing pens to hardware registers, so that drawing pen
1 corresponds to color register 15,
pens 3, 4, and 5 correspond to registers 2, 4, and 6; pens 6, 7,
and 8 correspond to registers 3, 5, and 7, and so forth. GEM
uses a lookup table to match color index values to hardware
registers. The complete correspondence is mapped out in Table 4-2.
In addition to determining which color register will be
used for drawing, we must also determine the color that the
register contains. Colors are chosen by mixing various levels of
the colors red, green, and blue. Each color register holds one
of eight color levels for each of these colors, which means that
there are 512 (8 X
8 X 8) possible colors to choose from.
The VDI call to set a color register to a particular shade is
Set Color Representation. The C language syntax for this call
is
int handle, pen, rgb[3];
vs_color(handle, pen, rgb);
where pen is the number of the drawing pen whose color you
wish to change, and rgb is a pointer to an array holding color
levels for red, green, and blue. The first element of this array
(rgb[0}) holds the red value; the second holds the green value;
and the third holds the blue value. Since GEM is written to be
non—computer-specific, these color values are expressed in
tenths of a percent of color saturation, meaning the color level
values range from 0 to 1000. With only eight color levels supported by the hardware, it should be obvious that many rgb
values will display in the same color. Table 4-1 shows the
relationships between the color value that you request (with
the vs_color call), the actual value that is set, and the hardware color register level to which that value corresponds.
72

<!-- source-page: 80 -->
## Page 80

Color and Other Graphics Settings
Table 4-1. Color Values and Register Values
Requested
Actual
Hardware Register
Value
Value
Color Level
0-70
0
0
71-213
142
1
214-356
285
2
357-499
428
3
500-642
571
4
643-785
714
5
786-928
857
6
929 and up
= 1000
7
Since there are 512 possible combinations, it’s nearly impossible to describe each one or to explain exactly how to find
a particular shade. In general, however, the higher the color
level, the brighter the color; the lower the level, the darker the
color. Whether the color displayed by a register tends toward
red, green, or blue depends on which value has the highest
brightness level. If all three values are equal, the color will be
black, white, or a shade of gray.
Mixing Colors
Thus, if rgb contains all zeros, the pen will be set to black,
while a setting of straight 1000s will set it to white. You can
lighten a shade by increasing the value of the two other colors
in equal proportions. A setting of 1000,0,0 selects bright red as
the pen color, while 1000,428,428 sets
a much paler red. To
darken the original red color, you can lower the red setting to
714 while keeping the other two at 0.
When you're unsure of what colors to mix, it may help to
start with the nearest primary color mixture and experiment
from there. These are the red, green, and blue values for these
mixtures:
Color
Red
Green
Blue
Black
0
0
0
Blue
0
0
1000
Green
0
1000
0
Cyan
0
1000
1000
Red
1000
0
0
Purple
1000
0
1000
Yellow
1000
1000
0
White
1000
1000
1000
73

<!-- source-page: 81 -->
## Page 81

CHAPTER 4
You can use the Control Panel desk accessory to get instant
feedback on what color levels to use for a particular color.
When you use it to mix colors using different levels of red,
green, and blue, the panel displays these color levels as numbers from 0 to 7. Using Table 4-1, you can translate these hardware levels into the corresponding numbers used by the VDI.
If you do not change the colors of any of the color registers, the default VDI color palette will be used. Table 4-2 gives
the default values for each of the VDI color pens. Next to each
-
pen number in square brackets is the number of the corresponding hardware color register. In square brackets, next to the VDI
red, green, and blue color values for each of the registers, are
the corresponding hardware color levels. The table illustrates
the 16-color low-resolution mode, but the 4-color mode is similar, with the exception that pen 1 maps to color register 3 in
medium-resolution mode.
Table 4-2. Default Values of VDI Color Pens
Pen [Reg]
Red
Green
Blue
Color
i
(|
1000 [7]
1000[7]
1000 [7]
White
1
[15]
0 [0]
0 [0]
0 [0]
Black
2
[1]
1000 [7]
0 [0]
0 [0]
Red
3
[2]
0 [0]
1000 [7]
0 [0]
Green
4
[4]
0 [0]
0 [0]
1000[7]
Blue
5
[6]
0[0}
1000[7)
1000[7]
Cyan
6
=
[3]
1000 [7]
1000 [7}
0 [0]
Yellow
7
~~
[5]
1000 [7]
0[0)
 1000[7]
Magenta
8
= [7]
714 [5]
714 [5]
714 [5]
| Low White
9
[8]
428 [3]
428 [3]
428 [3]
Gray
10
[9]
1000 [7]
428 [3]
428 [3]
Light Red
11
= [10]
428 [3]
1000 [7]
428 [3]
Light Green
12
[12]
428 [3]
428 [3]
1000[7]
Light Blue
13
[14
428 [3]
1000(7]
1000[7]
Light Cyan
14
[11]
 1000[7]
1000[7]
 428[3}
Light Yellow
15
[13]
 1000[7]
428 [3]
1000 [7]
Light Magenta
The VDI pen numbers are followed by the corresponding hardware color register
numbers, in square brackets. The VDI color levels are followed by the corresponding
hardware register color levels, shown in square brackets.
Locating Color Information
It is often useful to be able to find out which color is contained in a particular color register. For one thing, GEM does
not reset the color palette when your application ends and the
74

<!-- source-page: 82 -->
## Page 82

Color and Other Graphics Settings
user returns to the Desktop. So, in order to restore the user’s
color preferences when you end your application, you've got
to have some way of knowing what those settings were when
your program started. The VDI call used to learn the settings
for a particular register is Inquire Color Representation, whose
C language format is
int handle, pen, flag, rgb[3];
vq—color(handle, pen, flag, rgb);
where pen is the color register number, and rgb is an array
where the red, green, and blue color levels will be returned (in
elements 0, 1, and 2, respectively). The flag setting allows you
to select whether you wish to learn the setting that was requested when the vs_color call was made or the actual value
that was set.
As we stated above, there are 1000 different VDI settings,
but only eight possible hardware settings, so a wide range of
VDI settings correspond to the same hardware setting. For example, if you set all the values in rgb[0]-[3] to 650 and call
vs—color, then a color level of 714 (corresponding to a hardware level of 5) will be set for each. If you request a value of
700 or 750, you'll still get a setting of 714. The flag setting determines whether the color level values that you get are the
values that were requested or the values that were actually set.
If you set the flag to
1 before calling vq—color, you get the actual color settings (714 in each case). But if you set the flag to
0, you get the value that was requested, not the one that was
set (650, 700, or 750). You should also note that if an invalid
pen number is requested,
a —1
is returned in rgb{0].
Another handy bit of information to have is the pen color
used to draw a given dot on the screen. The function Get Pixel
returns not only that information, but the color register that
corresponds to that pen setting as well. The C language version of this call is
int handle, x, y, pixel, pen;
v—get_pixel(handle, x, y, &pixel, &pen);
where x and y are the coordinates of the point, pixel is the
variable in which the hardware color register number is returned, and pen is the variable in which the pen number is
returned.
75

<!-- source-page: 83 -->
## Page 83

CHAPTER 4
Program 4-1 shows how to change the color that is contained in each of the drawing pens. This program works correctly only on a color monitor, since the principles it illustrates
are not applicable to the monochrome screen.
In Program 4-1 each of the bars initially appears in the
~
color gray; each set of three bars, though, is drawn using a
different drawing pen. When we change the color of each of
the pens in turn, the colored line appears to move. Note how
_—
we saved the initial color values before we changed the pen
colors, and restored them after we were done. This insures
that when the program ends, you will find the desktop colors
just as you set them.
Program 4-1. color1.c
/SEKETKEKAKEECERERERE
REAR AKERS RETA
REREEA ERE E EES
/t
as
/%
o/
/*
Color1.C
-- Demonstrates drawing
in
s/
/t
different
pen colors,
and changing
the
&/
/&
colors contained
in those pens
x/
/%
&/
‘t
s/
SHEEEKSEAASAEKERASAKTESKS
KERR AAAS
ER EKER EE,
#include
"shell.c"
#define REPS
3S
7% number
of
wide lines
to draw
&/
demo ()
t
int
index=¢,
b,c,
xmax,dx,mid,
points(4),
rgb[3I,
hewcol (3),
pall33(33;
long
d3
rgb(@l=rgblil=rgbl2]=571;
/*
grey values
%/
/7*
Save original
color palette
%/
for
(c#93c<33 c++) vq_color (handle,cti,1,pal+c)};
xmax
= work_out (OI;
dx
= xmax/2@3
/%
acale lines
to horizontal
resolution
%/
mid
= xmax/m2;3
/&
find midpoint
of
screen
&/
~~
points£€3]
= work _outCilJ—
12)
points[Li]
=
12;
/&
set
top
and bottom
of
lines
&/
vsl_width (handle,
dx
)3;
/&* change width
&/
for
(c=O8sc<REPS3c++)
/%*
draw horizontal
lines
line
&/
€
vel _color (handle,c+1);
/% change pens
%/
vs_color (handle,c+i,rgb)3;
/*
set
pen color
to grey
%/
76
—_

<!-- source-page: 84 -->
## Page 84

Color and Other Graphics Settings
points(9]
= points([2]
=
(xmax—-=(dx&2))3;
/&
set points
%/
v_Plinethandle,
2,
points);
/&
draw
it
38/
points[S]
= points([2]
=
(mid+=(dx#2));
/%
set points
&/
v_plinethandle,
2,
points);
/%&
draw
it
&/
>
for
(b=@3b<73;6++)
/&
for
each primary color mixture...
&/
c
newcoll(@]
=
1968
&
(b&1);
newcollil]
=
368
&
(bR2)4
Nnewcoll(2})
=
258
&
(b&4);
for
(cmO@yc<33c++)
/& cycle color
through
3 sets
of
bars
%/
€
if
(c%See@)
ve_color (handle,3,rgb)
5
else vs_color (handle,c%3,rgb)3;
/*
old
bar
back
to grey
%/
vs_color (handle,c%3+1,newcol )
3
/%
set
new bar
&/
for
(d=83d<S9GIG;d++);
/&% waste some time
&%/
}
+
/& Restore original
color pallete
%/
for
(c#O@30<33 c++) ve_color (handle,c+1,pal+c)};
>
/% End
of Colori.c
£/
Drawing Modes
We’ve seen that when we draw a
dot of color on the screen,
what actually happens is that the screen memory representing
that dot is changed to reflect the number of the color register
that produces that color. In effect, the new drawing replaces
whatever had previously appeared in that spot on the screen.
It’s also possible for drawing operations to interact with
existing screen graphics, rather than to replace them. For example, a dotted line is partly made up of 1
bits (the graphics
object), and partly of 0 bits (the color mask). The line part is
normally drawn in whatever color is in the line drawing pen.
But how are the spaces between the lines drawn? Will they be
drawn using the background color, or will they not be drawn
at all, so that whatever display was on the screen before the
line was drawn will show through?
The VDI allows you to select from four different drawing
modes that determine how the graphics object (the
1 bits in
the pattern) and the color mask (the 0
bits in the pattern) will
affect the existing display. The drawing mode (or writing
mode, as it is sometimes called) is significant because many
GEM graphics types are made up of bit patterns containing
both 0 and 1
bits. Patterned lines, large markers, filled shapes,
77

<!-- source-page: 85 -->
## Page 85

CHAPTER 4
and graphics text all consist of graphics patterns that are partly
colored images and partly space surrounding those images.
_
The VDI writing mode affects all of these different types of
graphics renderings. Once you set a new writing mode, it
stays in effect until you explicitly change it again.
~-
Replace mode. The default writing mode is called the Replace mode. In Replace mode, the part of the image that consists of 1 bits is drawn with whatever color is in the relevant
drawing pen (the line drawing pen, the marker pen, the text
pen, or the fill pen). The part of the image that consists of 0
bits (the color mask) is drawn in the background color, found
in pen 0. As its name suggests, Replace mode replaces whatever color was already there with the drawing color and the
background color.
Transparent mode. The second mode is called Transparent mode. As with Replace mode, drawings that are made in
this mode depict the graphics object (1 bits) in the color of the
current drawing pen. But Transparent mode drawings leave
the color mask portion (0 bits) alone, so that whatever color
was there previously still shows through in the blank spaces
around the image. Patterned images drawn in Transparent
mode look different from those drawn in Replace mode, with
the former looking as if they had been stenciled onto the existing image. Solid images look the same when drawn in either
mode, however, since they are made up entirely of 1
bits.
Reverse Transparent mode. The opposite of Transparent
mode is Reverse Transparent. In this mode, only the color
mask portion (made up of 0
bits) is drawn, using the current
drawing pen. The part of the screen which corresponds to the
object portion of the image (the
1 bits) is left alone. Reverse
Transparent mode can be used to draw graphics text in inverse
video, where the space surrounding the letters, rather than the
letters themselves, are rendered in the color of the current text
drawing pen.
XOR mode. In the final drawing mode, neither the cur-
—
rent foreground drawing pen nor the background pen (pen 0)
is used to color the object or its color mask. This mode is known
as XOR mode. It’s name comes from the logical operation
-.-
eXclusive OR, by which the colors on screen are complemented.
To complement the color of a pixel, you invert the bits of
its color register number, changing all of the ones to zeros,
~
and all of the zeros to ones. For example, if a dot was drawn
78

<!-- source-page: 86 -->
## Page 86

Color and Other Graphics Settings
with the color in register 3, and you were in 16-color mode,
the binary representation for that dot would be 0011. The
complement of that number would be 1100, or 12 decimal.
Therefore, when drawing in XOR mode, every time the object
part of the image (the
1 bits) coincided with a portion on the
screen that had been drawn with color register 3, that part of
the display would be changed to the color in register 12.
For those of you who don’t normally think in binary
numbers, another way of looking at the process is to take the
highest possible color register number and subtract the color
register number of the existing color. What you’re left with is
the register number of the new color. In the above example,
the highest number is 15 (since the 16-color mode counts from
0 to 15). If you subtract 3 from 15, you are left with 12. If
you're using the 4-color mode, 3 would be the highest register
number, so 3 minus 3 would leave you with color register 0.
Remember, the XOR mode complements the hardware
color register number, not the VDI drawing pen number. You
may use Table 4-2 to match the VDI pen numbers to their
hardware register equivalents, which appear next to them in
square brackets.
Like Transparent mode, XOR mode only affects the area
of the screen display corresponding to the 1
bits of the object
image. But XOR mode has some unique properties all its own.
For example, if you use the Transparent mode to draw a green
line on a portion of the screen that is already colored green,
your line changes nothing, and it will not show up at all. By
its very nature, however, a line drawn in XOR will always
show up, since it changes whatever was on screen to another
color.
Another interesting property of XOR mode is that while
using it once always changes the picture, using it twice in a
row restores the original colors. This makes XOR mode handy
for drawing lines that will have to be erased later. It also lends
itself to use in animation, where the background must be restored after the object is moved.
Set Writing Mode. The VDI function call that is used to
set one of these drawing modes is called Set Writing Mode.
The C format for this function is
int handle, mode, mode_set
mode_set = vswr_mode(handle, mode);
79

<!-- source-page: 87 -->
## Page 87

CHAPTER 4
where mode is the drawing mode that you're requesting, and
mode_set contains the number of the drawing mode that was
actually set. The numbers assigned to the different writing
modes are
Number
Mode
Replace
Transparent
XOR
Reverse Transparent
PWN
re
Drawmode Demonstration
Program 4-2 demonstrates the different writing modes by
drawing dotted lines and text in each of the four modes.
In order to show the full effect of the different modes,
half of the background screen is left as background color, and
half is changed to the color in pen 3 (green). On that background, we draw black patterned lines using line pattern 5
(dashed), and graphics text. Though the text commands will
not be covered until a later chapter, we included text in this
example because it clearly illustrates the differences between
the drawing modes.
In Replace mode, the line appears in black (the drawing
pen color) and white (the background color). The Replace
mode text appears as black letters on a white background.
In Transparent mode, the line appears in black, but the
spaces between the lines are left alone, so they appear in
white on the white background and green in that part of the
screen. Only the black letters of the text are drawn.
In XOR mode, the part of the line that is drawn in black
in the other two modes is drawn in the complement of whatever color it’s drawn on. The complement of white is always
black, but the complement of green in lo-res mode is different
from what it is in medium-res mode. In medium-res, red
(color register 1) is the complement of green (color register 2).
But in lo-res, light cyan (color register 13) is its complement.
As in transparent mode, the background is left alone in the
spaces between the image patterns, or around the letters. Finally, in Reverse Transparent mode, the spaces that were ordinarily blank in the dotted line are drawn in, in black, while
the line itself is left in the background color. Similarly, the
80

<!-- source-page: 88 -->
## Page 88

Color and Other Graphics Settings
“frame” around the letters is colored in, in black, while the
letter shapes themselves are filled with whatever color happened to be there already.
Program 4-2. drawmode.c
/RRECETEREETERA TERE R EATER
EERE RARER EKER EEE EET
/t
%/
/k
s/
/&
Drawmode.C
-—- Demonstrates drawing
/
/t
mode
for patterned
lines
and graphics
*/
/t
text.
x/
/t
x/
/%
s/
AERTS
AA RESTS SASSER
ER KERR EEE EE /
#include
“shell.c"
demo ()
€
int
c,
xmax, ymax, dx, dy,
points(4];
xmax
= work_out(d];
ymax
= work_out(lid;
dx
= xmax/20;
/%
set
x
offset
as fraction
of
screen
width
&%/
dy
= ymax/20;
/%
set
y offset
as fraction
of
screen height
&/
pointel3S]
=
(ymax
—-=
12);
points(i}
=
123;
/*
y values
of
lines
&/
vsl_width (handle,
dx
)3
/*%
use wide
lines
%/
vsl_color (handie,3)3
/&
lines are green
%/
for
(eomBsce<i2s;e++)
/*&
draw
a block
of
green
lines
%/
€
points(S]
= points(2]
=
(xmax—-mdx);
/8
set
points
&/
v_pline (handle,
2,
points);
/%
draw
it
&/
>
vsl_type(handle,35);
/% dotted
line
s/
vsl_width (handle,1);
/&
of
normal
width
&/
val_color (handle,2);
/% color
is
red
%/
points(@]
=
16;
/%
x»
for
line
left
&/
points(2]
= work_out(@J-16;
/&
for
line right
%/
for
(cmigc<Szc++)
/%
draw lines
and
text
in
each
mode
*%/
€
pointsCild
= points(3]
=
(ymax
-= dy);
/%
set points
%/
vewr _mode (handie,c);
v_Plinethandle,
2,
points);
/%
draw
it
£/
fwitch(c)
/&
pick
appropriate text,
and print
it
&/
¢
case
i:
v_gtext (handle,
work_out{91/7,
Cymax-=dy),
"This
is the Replace drawing
mode")
5
break;
case
2:
v_gtext (handle,
work_out[@1/7,
Cymax-=dy),
“This
is the Transparent mode");
break;
case
3:
vigtext (handle,
work_out£91/7,
{ymax-=dy),
81

<!-- source-page: 89 -->
## Page 89

CHAPTER 4
“This
is the
XOR drawing mode");
break;
case
4:
vigtext (handle,
work_out(#1/7,
Cymax-=dy),
“This
is Reverse Transparent mode");
}
ymax-=(2idy);
/®
space between
lines
%/
3
+
/& End
of
Drawmode.c
&/
Program 4-3 is the same Drawmode program written in
assembly language.
Program 4-3. drawmode.s
ERITEASACTETAAEK
AKER TAKER
ERE REET ES
%
%
x
s
DRAWMODE.S
-- assembly version
of
t
s
drawing
mode program
*
%
t
%
®
*
s
ERSAKESTESAS
SAKES R EERE REARS
AREK
-xdef
demo
-xref
vwkhnd
»xref
contris
»xref
contrit
«xref contrl2
-xref
contrls
»xref contrl4
«xref
contrlsS
=xref
contrlé
«xref contrl7
xref
contria
»xref
contrl1?
xref
contrlis
xref
contriili
xref
intin
xref
intout
-xref
ptsin
-xref
ptsout
etext
demo:
move
intout, xmax
move
intout+2, ymax
move
dx, dd
move
dy,di
cmp
#639, xmax
%
if
high-res
or
med-res
bne
skipi
add
dd, dB
& double
dx
move
d®,dx
skipis
cmp
#399, ymax
%
if high-res
bne
skip2
add
di,di
move
di,dy
% double
dy
82

<!-- source-page: 90 -->
## Page 90

Color and Other Graphics Settings
skip2s
a&S Set
line width
move
move
move
move
move
isr
eae Set
move
move
move
move
jsr
2%
set
move
move
sub
move
move
move
move
blocks
sub
move
move
#16, contr1a
#i,contrii
#6,contris
dx,ptsin
#9, ptsin+2
vdi
line color
#17,contr1g¢
42, contrit
#1,contrls
#3,intin
vdi
points
4&8
#12, ptsint+2
ymax ,d&
#12,da%
dd, ptsint+d
dd, ymax
xmax, dS
#11,d4
dx,dS
d5,ptsin
d3,ptsint+4
s%%
Draw the
lines
move
move
move
isr
dbra
e4%
Set
move
move
move
move
jsr
x%%
Set
move
move
jsr
ak
Set
move
move
move
move
move
isr
#6,contrl1ld
#2,contrli
#9, contr13
vdi
d4,block
line type
#15, contr1ld
#2@,contril
#1,contris
#5,intin
vdi
line color
#17, contrid
#2,intin
vdi
line width
#16, contr1g
#1,contrl1
#3, contr1s
#i,ptsin
#8, ptsin+2
vdi
% opcode
for
line width
&
1
point
in ptsin
&
no
integer parameters
in
intin
*
set
width
to
dx
opcode
for
line color
no points
in ptain
1
integer parameter
in
intin
Mh
&
line color green
®
set
top
and bottom
of
block
&
loop counter
% decrement xposition
of
line
Sopcode
for polyline
Snumber
of
points
in ptsin
*
no integer parameters
in
intin
opcode
for
line pattern
no points
in
ptsin
1
integer parameter
in
intin
5
Mad
®
line pattern
5
-- dotted
line
*% opcode
for
line color
*®
line color
is
red
opcode
for
line width
1
point
in ptsin
no
integer
parameters
in
intin
Cw
ad
%
set
width
to
li
83

<!-- source-page: 91 -->
## Page 91

CHAPTER 4
SE
set
points
£6%
move
xmax,d@
move
d%, dd
divu
87,06
sub
#16,d
move
dS, ptsint4
move
ymax
, d5
move
43,04
modes:
&4% Change drawing modes
move
#32, contrle
move
#8,contril
move
#i,contris
move
d4,4d8
addq
#1,d8
move
d8,intin
jer
vdi
move
#16,ptsin
gub
dy,d3
sub
dy, dS
move
d3,ptsin+2
move
d5,ptsin+6
sa
Draw dotted
lines
move
#6, contrigd
move
#2,contril
move
#2, contrls
isr
vdi
St Print graphics text
move
#8, contri1g
move
*#1,contrit
move
#33, contris
sub
dy,dsS
move
d3,ptsin+2
move
¢6,ptsin
move
#32,dd
movea.l
*#intin,al
movea.l
#t1,ad
move
d4,d1
mulu
W33,d1
add
di,ad
texts:
clr.w
di
move.b
(ad)+,d1
move.w
di, (ald+
dora
dd, text
jsr
vdi
dbra
64, modes
rts
SkEx
data section
»data
.even
84
&
set
left
and right
for
dotted
line
&
loop counter
xae
&
Opcode
for
set
writing
mode
& decrement
y
of
dotted
line
Sopcode
for polyline
Snumber
of
points
in ptsin
&
no integer parameters
in
intin
% opcode
for
gtext
%
1
point
in ptsin
&
33 characters
in string,
including
null
&
Set position
for
text
33 characters
address
of
destination
Calc
address
of
source string
ee
move
a
letter
from source...
to word-aligned destination...
until
all
done.
7
& print
text
®
next
drawing mode

<!-- source-page: 92 -->
## Page 92

Color and Other Graphics Settings
dxs
-de.
dys:
dc.
16
1g
$32 characters
tis
-dc.b
*This
is the Replace Drawing Mode’,@
t2:
~dc.b
*This
is the Transparent
Mode
'.
t3s
-dce.b
*This
is the
XOR Drawing Mode
*,@
t4
-de.b
*This
is Reverse Transparent
*,9
-bas
xmax?
-ds.w
i
ymax
.ds.w
1
eend
Clipping
Another function that affects all types of graphics output is
known as clipping. Clipping is used to confine graphics output
to a designated rectangular portion of the screen. If part of the
graphics output you’re trying to draw lies inside of the clipping rectangle and part lies outside the rectangle, the part that
is inside will be drawn, while the part that is outside won't.
By setting a clipping rectangle that is as large as the entire
display, you can insure that no part of your graphics output
will be ‘“drawn” on memory that does not belong to the
screen display. This can prevent nasty system crashes, since
when drawing operations affect program memory, unpredictable (and usually unpleasant) results occur. Clipping is also
extremely helpful for updating GEM windows. Not only can it
insure that you confine your drawing to the interior of the
window, it can also enable you to redraw only the portion of
the window that has been uncovered after having been covered by another window.
Like all good things, clipping has its price. When clipping
is on, the VDI must examine every point before it’s drawn, in
order to make sure that it lies within the rectangle. This extra
burden can slow down graphics output. For this reason, when
a workstation is first opened, clipping is turned off. To turn it
on, you must use the Set Clipping Rectangle function, the C
version of which looks like this:
int handle, flag, points[4);
vs—clip(handle, flag, points);
where flag is used to indicate whether you want to turn clipping on (flag =
1 or greater) or to turn clipping off (flag = 0).
Points is a pointer to an array that holds the x and y coordinates of the four sides of the clipping rectangle. Points[0]
85

<!-- source-page: 93 -->
## Page 93

CHAPTER 4
holds the coordinate of the left side, points[1] the top,
points[2] the right side, and points(3] the bottom.
The sample program (Program 4-4) demonstrates the use
of clipping. It draws a series of concentric circles, the first of
which lies within the clipping rectangle. The remaining circles
are clipped at the top and bottom.
Program 4-4, clip.c
/ESKERETERSERERSKARE
TAKARA
ETERS EE,
/t
as
/t
s/
/t
CLIP.C
-- Demonstrates use
of
the
x/
4%
clipping rectangle.
x/
‘kt
a/
/t
&/
SERETETACATATAKAAE
SEARS ETERS AEA
RE SEEKS
#include
“shell.c”
#define STEP
1¢
demo ()
€
int
c,
dx,dy,
C¥sFr-s
points(4];
if
(work _out(@J
==
639) dx=STEP;
/*
set
full
horiz
step
&%/
else
dx
= STEP/2;
/*%
except
for
lo-res
*/
if
(work_outC1J]
== 399)dy=STEP:;
/*
set
full
vert
step
%/
else
dy
=
STEP/2;
7%
except
for
color
&/
vsl_width (handle,dx);
/*%
set
wide
line
&/
cy
=
26%dy;
/*
set
a clipping rectangle
*/
r=
2
&lidxtdy);
/*%
that’s
as wide
as the screen
£/
points(@]=¢;
/&
but
not
very
tall
*/
points(2J=work_out(@];
points{tJ=cy-r;
points(3)=cy+r;
vs_clipthandle,i, points);
/%
draw concentric circles
&/
for
(c@igc<i4sc++)
vsl_color (handle,c);
/&*
change drawing
pen
#/
viarc (handle, 328dx, 208dy, (c+1) &(dxt+tdy) ,8,3690);
/*
draw
"em
%/
}
3
/*%
End
of
Clip.c
*/
86

<!-- source-page: 94 -->
## Page 94

Color and Other Graphics Settings
NDC Example
So far, all of our sample programs have used the ST’s own
Raster Coordinate system. But as we saw in Chapter 2, the
GEM VDI also supports a non-device-specific format called
Normalized Device Coordinates. The type of coordinate system you choose, Raster or Normalized, is another setting decision that affects all subsequent drawing functions. Sample
Program 4-5 opens two workstations, one using Raster Coordinates and the other using Normalized Device Coordinates.
It then draws a box containing a
circle, using each type of coordinate system. Note that several workstations can be open at
once, each with its own set of graphics settings.
By looking at the functions showrc and shownorm, we
can examine some of the differences between the two coordinate systems. In the raster coordinate system, we have to scale
the horizontal and vertical coordinates for the center point of
the circle, and the radius value, according to the maximum
screen resolution.
In NDC mode, we use the same fixed values regardless of
the screen resolution, and the VDI does the scaling for us. Notice how we must scale the vertical height of the box according to the aspect ratio of each pixel. That’s because the VDI
scales the circle in order to make it appear round. We use the
values in work_out[3]-[4] to find the aspect ratio. Interestingly
enough, we not only have to scale the vertical dimension of
the NDC box according to the aspect ratio of each pixel, but
we also have to scale it according to the aspect ratio of the
screen. That’s because in NDC mode, the VDI not only compensates for the fact that each pixel may not be as wide as it is
tall, but also for the fact that there may not be an even number of rows and columns. Another point worth mentioning is
that we did not have to change the line drawing pen to get
the second figure to appear in black, since the NDC workstation uses its own line drawing pen which is separate from
the one used by the RC workstation. This program also demonstrates the rounding error that can occur when we use Normalized coordinates. In the color modes, the circle on the right
extends one dot past the border of the box.
As discussed earlier Program 4-5 requires that GDOS be
in the AUTO folder of the disk used when starting your system.
87

<!-- source-page: 95 -->
## Page 95

CHAPTER 4
Program 4-5. ndc.c
/EREESERTTASAAREERE
CREE A ATES
SERERERREEREEE/
/t
%/
/t
x/
/t
NDC.C
-- Demonstrates use
of
the
%/
/t
normalized coordinate system
s/
/t%
along
with
raster coordinates
xs
/%
s/
/t
s/
/ERAESSETEAASEEKEERESES
SEEKERS SERRA
S EER EES/
#include
"shell.c"
#define STEP
19
int
dx,
dy,handlel,points(141;
demo ()
€
if
(work_out(9]
== 639)dx=STEP;
/*
set
full
horiz
step
*%/
else
dx
= STEP/2;
/% except
for
lo-res
£/
if
(work_outCild
== 399)dy=STEP;
/&
set
full
vert
step
%/
else
dy
=
STEP/2;
/& except
for
color
&/
showrc();
/t
de
re
circle demo
t/
showndc ()
5
/%
do
nde
demo
&/
>
showrc
()
int
cx,cy,r3
long
ri;
cx
@
168dx;
/%&
horiz
coordinate
of
circle center
*/
cy
=
20kdy;
/®
vertical
coordinate
of
center
%/
rom
rl
=
12
8
dx3
/®
circle radius
&/
vsl_width (handle,dx);
/%
set
wide
line
%/
vsl_color (handle,2);
/%
change color
%/
viarc (handle,cx,cy,r,9,3698);
/$
draw circle
&/
points(@l=points($)=points(8)=cx-r;
/&
x
for
box
left
£/
points€2J=points(4]=points(iGlecx+r;
/*
x
for
box
right
&/
rl
=
(ritwork_out{3J/work_out£4]);
/% scale
box
height
&/
points(51]=points{7I]=points(iijJ=cy+ri3;
/*®
y
for
box
bottom
&/
pointsl1I]=points(33=points(9J=cy-r i;
/t
y
for
box
top
&/
v_pline(handle,6,points);
/&
draw
box
&/
showndc
()
€
int
nul,x;3
/*
Initialize
input
array,
get
the physical
workstation handle,
and
open
the Virtual
Screen Workstation
with normalized coordst/
for
(x= work_inCi@J=@3
x<18;
work_intx++J]=1);
handleil
= graf_handle(&nul,
&nul,
&nul,
&mul)s;
viopnvwk
(work_in,
&handlel,
work_out)3;
/% perform the graphics demos
%/
shownorm() 5
88

<!-- source-page: 96 -->
## Page 96

Color and Other Graphics Settings
/*% close the NDC virtual
screen workstation
*/
v_icl svwk (handlel)
3;
}
shownorm()
€
int
cx, cy,r3
long
ri3
cx
= 24575;
/*
x
for
center
&/
cy
=
16363;
/8
y
for
center
&/
emri= 6144;
/* radius
%/
vsl_width (handlei,312);
/%
set
wide
line
t/
viarc (handlal,cx,cy,r,@,3698);
/*
draw circle
*%/
points(Sl=points(Slepoints(Bjacx-r};
/*&
x
for
box
left
#/
pointsl2Zi=points(4lspointsl[iOlecx+rs/%
x
for
box
right
%/
ri
= (r18dx
864) / (dys49);
7%
scale
for width/height
&/
rl
=
(riswork_outC33/work_out(43);
/8 scale
for
aspect ratio
%/
points(S1=points(7IJ=points{illecy-ris;
/%
y
for
box
bottom
&/
points(iJepoints(3l=points(9lecy+ri;
/*
y
for
box
top
k/
v_Pline(handle1,6,points)};
/*&
End
of
NDC.c
&/
BASIC Graphics Settings
None of the generalized graphics settings that we have been
talking about in this chapter have keyword support in the first
version of ST BASIC. Although the revised version has not appeared at the time of this writing, there are indications that
this version will include the command DRAWMODE to set the
drawing mode. The form for this command is
DRAWMODE mode
where mode is the mode number from 1
to 4 (these correspond
to the mode numbers used by vswr_mode). It may also include the commands RGB to set the color registers, and ASK
RGB to read them. The syntax for these are
RGB register, red, green, blue
ASK RGB register, red, green, blue
where register is the color register number, and red, green, and
blue are either the values for the new settings (RGB) or variables to hold the existing settings (ASK RGB). Note that these
settings reflect the hardware registers, not the VDI pens. This
means that the register numbers will differ from the pen numbers used in the COLOR command, and that the red, green,
and blue values will be in the range 0-7, not 0-1000.
89

<!-- source-page: 97 -->
## Page 97

CHAPTER 4
Even without these new commands, however, it is still
possible to use the VDI setting commands with the old POKE,
VDISYS(0) method. Program 4-6 demonstrates the BASIC
translation of the Drawmode program.
Program 4-6. drawmode.bas
18
fullw
2:
clearw
2
2a
res
=
peek (systab)
36
if
(res<4)
then
xmax
= 639 else xmax
= 319
48
if
(res>1)
then
ymax
=
199 else ymax
=
399
So
dx
= xmax/2@8:
dy
© ymax/23
32
REM
Initialize text
strings
34
textS(i)="This
is the Replace Drawing Mode"
3S
text$(2Z)="This
is the Transparent
Mode"
56
text$(3)="This
is the
XOR Drawing
Mode”
37
text#(4)="This
is Reverse Transparent
.
68
REM Set
Line Width
78
poke contrl,16
8a
poke contrl+2,1
98
poke contri+6,9
10@
poke ptsin,dx:
REM width
=
dx
118
poke ptsin+2,8
129
vdisys (9)
139
REM
Set
line color
149
color
1,9,3
1359
REM
169
for
x
=
3
to
14
178
linef
xmax—(x dx), 12, xmax~(x8dx),
ymax- (48dy)
18@
next
x
199
REM
Set
line drawing pattern
289
poke contri1,is
219
poke contrl+2,8
228
poke contri+é,i
238
poke intin,S
2498
vdisys(1)
250
REM
Set drawing color
269
coler
1,8@,2
278
REM
Set
Line Width
288
poke contri,16
298
poke contr1+2,1
388
poke contr1+é,¢
318
poke ptsin,1:
REM width
=
1
328
poke ptsin+2,2
33g
vdisys(@)
348
REM
338
for
xsi
to
4
366
REM change drawing modes
378
poke contrl,32
3ag
poke contrl+2,@
398
poke contr1+6,1
4o9
poke
intin,x
418
vdisys (a)
426
REM
430
linef
16, ymax—((xt1) &3kdy) ,xman—(28dx),
ymax—( (x41) 838dy)
445
gotoxy (xmax/319)€5 ,18—-
(4 %4)
4350
print
text#(x)
469
next
x
90

<!-- source-page: 98 -->
## Page 98

Chapter 5
Filled Shapes

<!-- source-page: 100 -->
## Page 100

In addition
to line drawing routines that create
the outlines of a figure, the GEM VDI also provides a group of
output routines that create shapes whose interiors are filled
with a solid color or with a pattern of colors. Patterned fills
provide a means of distinguishing the interior of one shape
from another on monochrome systems. For example, if you're
drawing a pie chart on a monchrome screen, all of the wedges
will look the same if you try to fill them with different solid
colors. By filling them with different crosshatch patterns you
can make them visually distinct on both monochrome and
color systems. Like the line drawing routines, the fill routines
share a number of common graphics settings that can be used
to select the color, the fill pattern, and whether or not the figure is outlined in a solid color.
Filled Rectangle
The simplest of the filled figures is the rectangle. This shape is
created with the VDI command Fill Rectangle, whose function
is to quickly fill a rectangular area on the screen. (This command may not work with other output devices.) The C language version of this function is
int handle, sides[4];
vr—recfl(handle, sides);
where sides is an array that contains the coordinates for each
side of the box. The values for the left and right sides are held
in sides[0] and sides[2], and sides[1] and sides[3] contain the
location of the top and bottom.
Pattern Fills
Although drawing a
filled box may seem a very straightforward
operation, the VDI provides a number of fill settings that allow
you to vary the results significantly. The first of these are the
fill pattern settings. GEM provides the ST screen display device with five different general types of fill patterns, which are
referred to in the GEM literature as fill interior styles.
93

<!-- source-page: 101 -->
## Page 101

CHAPTER 5
The Hollow fill pattern fills the interior of the figure with
the current background color. The Solid style fills the shape
with the currently selected fill color. The Pattern style superimposes one of a number of different drawing patterns on the
fill area. These include dot patterns of varying density, horizontal and diagonal checkerboards, and herringbone patterns.
The Hatch pattern fills the area with one of a number of different crosshatch patterns. These are made up of horizontal,
vertical, or diagonal lines, either alone or in combination. Finally, the user-defined style allows you to display a pattern
that you create yourself, using an array of 16 words to represent a 16 X 16 pattern of dots.
When you open your virtual workstation, you specify a
default pattern type in the variable work_in[7]. (We’ve been
setting it to 1, Solid.) To change the pattern type from this default, you must choose another with the command Set Fill Interior Style. The syntax for this call is
int handle, pattern_type
type_set = vsf_interior(handle, pattern_type);
where pattern_type is
a number that corresponds to one of the
five fill types:
0
Hollow
1
Solid
2
Pattern
3
Hatch
4
User-Defined
The number of the pattern type that the VDI actually sets is
returned in the variable type_set. If you choose a pattern_type
that isn’t available, the type will be set to 0, Hollow.
As we mentioned above, two of these pattern types contain a number of different patterns with similar characterstics.
The Pattern style is made up of 24 different dot patterns, and
the Hatch type has 12 different type of crosshatch line patterns. Whenever you choose the Pattern or Hatch styles, the
actual fill pattern that is used will be determined by the setting of the Fill Style Index, that selects one of these subpatterns. When you open the virtual screen workstation, you
designate the default value for this index in the variable
work_in[8] (provided that the GDOS extension is loaded).
Thereafter, you can select
a new subpattern with the function
Set Fill Style Index, which, in C, looks like this:
94

<!-- source-page: 102 -->
## Page 102

Filled Shapes
int handle, pattern_index;
index_set = vsf_style(handle, pattern_index);
where pattern_index is the index number for the subpattern.
For Hatch patterns on the ST screen, index numbers from 1 to
12 produce different crosshatch designs, and for Pattern type
fills, index numbers from 1 to 24 produce unique results. The
number of the index that was actually set by the VDI is returned in the variable index_set. If the index requested is not
available, an index of 1 is set.
A few things should be noted about the fill patterns. First,
patterns always repeat at even 16-dot intervals, starting with
the top left corner of the screen. Thus, if you start a pattern fill
at column 8, the left side of your filled pattern will start with
the “middle” of the pattern, not with its leftmost side. Second,
the pattern index has no effect whatever on pattern types other
than Hatch or Pattern (that is Hollow, Solid, or User-Defined).
Finally, note that subpattern 8 of the Pattern style is a solid
color fill, just like that obtained by using the the Solid style.
Program 5-1 uses the Filled Bar function (which is very
similar to Rectangle Fill) to show each of the preset fill types,
and the subpatterns for the Hatch and Pattern types.
In the output from Program 5-1, the top row of boxes are
filled with the Hollow, Solid, and user-defined fill patterns.
(Since we have not specified our own fill pattern, the default
user pattern, the Atari logo, is the one that appears.) The next
two rows contain boxes that are filled with the 24 different
Pattern style fills. The final row of boxes displays the 12
Hatch type fill patterns. For the benefit of assembly language
programmers, Program 5-2 is a translation of fillpat.c
Program 5-1. fillpat.c
/ERRREEEEREAESSATATAE
KERR ES SEERA EERE REESE
/%
%/
/*
x/
/%
FILLPAT.C
-- Shows the various fill
“/
/t&
Patterns that
are available
x/
/%
ss
/*
s/
/ERERERESERSETAERERE
RESET RAEE EERE ER ERSTE /
#include
"shell.c”
demo ()
{
int xstep,dx, ystep,dy, scrh,scrw,c,d;
95

<!-- source-page: 103 -->
## Page 103

CHAPTER 5
/*%
int points(4];
scrw
* work_out(9];
/s
get
screen width
£/
scrh
= work_outCil;
/%
get
screen height
&/
xstep
= scrw/i2;
/@ each block
1/12 width
%/
ystep
= scrh/4;
/&
and
1/4 height
£/
dx
= xstep/5;
/&
with
some space
in between
%/
dy
= ystep/5;
points(OI= points(1I]=9;
pointsl2)=x stept4—dx;
pointslSI=ystep-dy;
vsf_interior (handle,@)};
v_bar (handle,points);
/%
draw Hollow block
&/
points(21=xsteps8-dx,
points(O@I=xsteps4;
vsf_interior (handle, 1)4
v_bar (handle,points);
/*
draw Solid block
*/
points(2J=xstepti2—dx;
points(@l=xsteprs8;
vsf_interior (handle, 4)3
v_bar (handle,points);
/* draw User-defined
(atari)
blocks/
for
(d™i3d<4;d++)
/&%
for
next
three rows
&/
for
(cmOzc<i2s3c++)
/&@
12 coluans
in
each
row
%/
<
points(@l=xsteptc;
/8
set
block coordinates
%/
points(2J=sx
steps (c+1)—dxy
pointeslil=ysteptd;
points(3)=#ysteps(d+1)
-dy;
if
(d<3)
vef_interior (handle,2);
/®
set
Pattern
style
%/
else vsf_interior (handle,3);
if
(d==2)
vef
style (handle,c+13)3
else vsf_style(handle,ctl);
7%
& sub-pattern
%/
y-bar (handle, points) 5
/¢
draw block
%/
}
End
of
Fillpat.c
&/
Program 5-2. fillpat.s
EEKTERAET TAKARA
EEREAES EKER
EEE RRR ARE KEES
*
8
x
’
*
*
*
s ESERTERARAAEKA
EASA
RERE RES ERR TAREE
x
*
FILLPAT.S
-- assembly version
of
%
the fill-pattern
demo
bs
*
t
x
x
-xdef
demo
«xref
vwkhnd
-xref
contrlgd
-xref
contrli
xref
contrl2
xref
contrls
exref
contrl4
»xref
contris
96

<!-- source-page: 104 -->
## Page 104

Filled Shapes
xref
contrld
-xref
contr17
-xref
contrls
«xref
contrl?
xref
contrl1ld
«xref
contrlil
«xref
intin
»xref
intout
«xref
ptsin
xref
ptsout
8
if
high-res
or med-res
& double
dx
and xstep
&%
if
high-res
& double
dx
and ystep
ss
Set
Interior
Fill
Style
to Hollow
‘
%
opcode
for
interior
style
&
no points
in ptsin
&
#111
style only
in
intin
& Hollow fill
style
emi,
yi
=
@
&
x2
= xsteps4—dx
%
y2
= ystep-dy
&
opcode
for
GDP
% subcode for
Bar
&%
2 corners
of
box
in ptsin
&%
no integer parameters
in
intin
draw filled
box
% opcode
for
interior
atyle
&
no points
in ptsin
&
#111
style only
in
intin
& Solid
fill
style
etext
demo:
cmp
#639, intout
bne
lowx
asl
dx
asl
xstep
lowx:
cmp
#399, intout+2
bne
lowy
asl
dy
asl
ystep
lowy:
move
#23, contr1¢
move
#9, contrii
move
#1,contris
move
#9, intin
isr
vdi
4%
Draw filled
box
sub
dé, de
move
dd, ptsin
move
dg, ptsin+2
move
xstep,
dd
move
gx,di
asl
82,08
sub
di,de@
move
dd, ptsin+4
move
ystep,da
move
dy,di
sub
3d1,d8
move
d@, ptsin+6
move
#11, contrigs
move
#i,contriS
move
#2,contril
move
#8, contrlsS
isr
vdi
88%
Set
Interior
Fill
Style
to Solid
move
#23, contrigs
move
#8, contrit
move
#1, contri
move
#i,intin
isr
vdi
Sx
Draw filled
box
move
xstep,dd
move
dx,di
asl
42,48
97

<!-- source-page: 105 -->
## Page 105

CHAPTER 5
move
asl
sub
move
nove
move
move
move
isr
ant Set
move
move
move
move
jer
d8,ptsin
#1,d8
di,d@
dd, ptsint+4
#11,contrls
#1,contr13
#2,contrii
#8, contrils3
vdi
#23, contrilgs
#8, contril
#1,contris
#4,intin
vdi
383
Draw filled
box
move
move
asi
move
add
move
add
sub
move
move
aove
ove
move
jer
move
rows
move
move
sub
move
move
@mulu
sub
move
subq
move
mulu
move
bars
move
sub
ea%
Set
move
move
move
move
emp
bne
move
pattern:
jsr
98
xetep,ds
dx,di
#2,dd
48,02
d@,de
d8,ptsin
d2,d0
di,d@
dd, ptsin+4
#11,contr1g
#1,contr15S
#2,contril
#8, contr13
vdi
42,05
#11,04
44,07
63,07
ystep,de
dy,di
d7,d@
di,d@
dd, ptsints
#1,d7
ystep,d@
d7,d0
d8, ptsint+2
#12,d6
d4,d6
#23, contr1gd
#2,contrii
#1,contrls
#2,intin
#9,d5
pattern:
#3,intin
vdi
t
b
3
s
ee
oe
7
*
x
x
x
*
*
*
set
x1
= xstepe4
set
x2
= xsteps8—-dx
opcode
for
GDP
subcode
for
Bar
2 cornerea
of
box
in ptsin
no integer parameters
in
intin
draw filled
box
Interior
Fill
Style
to User-defined
opcode
for
interior
style
ho points
in ptsin
fill
style only
in
intin
User-defined
#111
style
set
x1
= xstepsg
set
x2
= xstepki12—dx
opcode
for
GDP
subcode
for
Bar
2 corners
of
box
in ptsin
no
integer parameters
in
intin
draw filled
box
loop counter
d
loop
counter
c
d+i1
is
in
d7
set
y2
of
box
= ysteps(d+1)-dy
set
yl
= ystepsd
etl
is
in
dé
Interior
Fill
Style
to Pattern
or
Hatch
opcode
for
interior
style
no points
in
ptsin
fill
style only
in
intin
Pattern
fill
style
last
row
is Hatch
fill
style

<!-- source-page: 106 -->
## Page 106

Filled Shapes
uae
Set
Fill
Style
Index
move
#24,contr1S
*
opcode
for
set
index
* contrll
and contrl3
set correctly
from previous call
move
dé,intin
*
use
inner
counter
for
index
cmp
#1,05
&
add
12
to
index
for middle row
bne
notmid
add
#12, intin
notmid:
isr
vdi
*x&
Draw filled
box
move
xsteap,
dd
mulu
dé, da
sub
dx, d@
move
d@,ptsin+4
®
set
x2
move
xstep,dd
subq
#1i,dé
mulu
dé,d8
move
d8,ptsin
*
set
xi
move
#11,contri®
% opcode
for
GDP
move
#1, contrls
*
subcode
for
Bar
move
#2,contrli
*
2 corners
of
box
in ptsin
move
#2,contr1lS
a
no
integer parameters
in
intin
jsr
vdi
&%
draw filled
box
dbra
d4,bar
dbra
d5,row
rts
$ae%
data section
-data
-even
dxe
.dc.w
5
&
1/68 screen width
dy:
-dce.w
19
&
1/28 screen height
xstep:
-dc.w
26
&
1/12 screen width
ystep:
-dc.w
49
31/4 screen height
-end
User-Defined Pattern Fill
The one pattern that we have not discussed so far is the userdefined fill pattern. When the user-defined line pattern is selected, we must also tell the VDI what the pattern looks like.
This is done in much the same way as we set up the image for
the user-defined line pattern. Like the line pattern, each fill
pattern is 16 dots wide, which means that each line can be described with a single 16-bit number. While the line pattern is
only 1 line high, however, each fill pattern is 16 lines tall.
99

<!-- source-page: 107 -->
## Page 107

CHAPTER 5
This means that it takes the equivalent of 16 line pattern descriptions, stacked one on top of the other, to describe a
fill
pattern. These sixteen 16-bit descriptions are placed in an array, and the address of the array is used to specify the pattern.
In order to determine the values to be placed in this array,
binary digits are used to represent each line of filled dots
(ones) and unfilled dots (zeros). Just writing out the pattern as
binary digits may help you visualize it. For example, let’s look
at a pattern that draws the letters LOVE in a block, with the
first two letters on top of the last two.
O0Q00000000000000 = 0 X CONN
0011000001111000 = 0 X 3078
0041000011001100 = 0 X 30CC
0011000011001100 = 0 X 30CC
0011000011001100 = 0 X 30CC
0014000011001100 = 0 X 30CC
0041141001114000 = 0 X 3E78
O0000C0000000000 = 0 X C000
01100911011111100 = 0 X 646FC
0110011011000000 = 0 X 66C0
0110011011000000 = 0 X 66C0
0041001011111000 = 0 X 32F8
0001141011000000 =0 X IECO
00001110141000000 = 0 X CECO
0000041011111100 = 0 X 04FC
Q000000000000000 = 0 X 0000
By drawing the pattern using zeros and ones, and converting those binary numbers to hexadecimal, we get the data
needed for setting up our user-defined fill pattern. Once we
have this data, we can use the VDI call. Set User-Defined Fill
Pattern, to establish it as the pattern to be used when we
choose fill style 4. The C language format for this call is
int handle, bit_planes, pattern[16*bit_planes];
vsf_udpat(handle, pattern, bit_planes);
where pattern is a pointer to our data array, and bit_planes is a
number used to indicate how may colors are in our pattern.
For plain two-color patterns such as the one in our example
above, there are 16 elements in the pattern array, and the
bit_planes variable should contain a one. A complete example
program showing the use of our LOVE fill pattern can be
found in the section discussing the Filled Rounded Rectangle
GDP, below.
100

<!-- source-page: 108 -->
## Page 108

Filled Shapes
If you forget to set a user-defined pattern before chosing
interior fill style 4 with the vsf_interior call, you will get the
default user-defined pattern, which on the ST just happens to
be the Atari logo. An example of this pattern can be seen in
the output of the fillpat.c program, above.
Multicolor Pattern Fill
It’s also possible to set the user-defined fill pattern to produce
a multicolored pattern. Such a
fill pattern is much more complex than the standard two-color fill.
In order to understand how multicolor fill patterns work,
we must first discuss the concept of color bit planes. When we
talked about color formation previously, we noted that when
each dot on the screen can only be displayed in one of 2 colors, you only need one binary digit (bit) to represent that dot,
since a one or a zero covers the whole range of possiblities.
But if you want to display that dot in any one of 4 colors, you
need two bits to represent it. Each time you double the number of possible colors, you need one more bit to represent the
dot. Thus, in order to get 8 colors, you need three bits per dot,
and to get 16 colors you need four bits per dot.
When you know that you’re going to have a fixed number
of colors, like the 4 or 16 colors provided on the ST, it’s easy
to say that each byte of display memory will be interpreted as
four contiguous pairs of bits, or two 4-bit chunks.
GEM was not designed for a particular system, however,
so it had to be made as flexible as possible. If, for example, if
GEM was used as the operating system on a computer that
displays eight colors on screen at a time, it would be very
awkward to say that each byte of display memory holds the
information for 2% dots. Therefore, for the purpose of mullticolor pattern fills, color bits are grouped by what are called bit
planes. In such a grouping, the color bits for a single dots are
split up so they aren’t contiguous the way they are in ST display memory. Instead, all of the least-significant bits are in
one block, followed by a block of the next most-significant
bits, and so on. To construct the group of bits necessary to
make up the dot in the top, left corner of the picture, you must
take the most-significant (leftmost) bit of the first byte of the
first block, and join it with the leftmost bits of the first byte of
each of the other blocks. Figure 5-1 shows how this works.
101

<!-- source-page: 109 -->
## Page 109

CHAPTER 5
Figure 5-1. Arrangement of an Image by Bit-Planes
UPPER
LEFT
DOT
TAKES
COLOR
FROM
REGISTER
6
1016
8
|
1
\ fe
1
Plane
3
Plane
2
Plane
1
Planeé
The color bit plane model is used when setting up data
arrays for multicolor pattern fills. Each time you wish to double the number of colors available in the fill pattern, you must
add another 16-word group onto the end of the pattern array.
The first 16-word group is bit plane zero, the second is bitplane one, and so on. The total number of 16-word bit planes
should be passed to the function in the variable bit_planes.
Take, for example, the case of the following fill pattern array:
int pattern []={
OxFFFF, OxFFFF,
OxFFFF, 0xFFFF,
OxFFFF, OxFFFF,
OxFFFF, 0xFFFF,
0x0000, 0x0000,
0x0000, 0x0000,
0x0000, 0x0000,
0x0000, 0x0000,
OxFFFF, OxFFFF,
OxFFFF, OxFFFF,
0x0000, 0x0000,
0x0000, 0x0000,
OxFFFF, 0xFFFF,
OxFFFF, OxFFFF,
0x0000, 0x0000,
0x0000, 0x0000,
}
102

<!-- source-page: 110 -->
## Page 110

Filled Shapes
The top four words of each bit plane are made up of all
ones, so the first four lines will have a one in each bit position.
This corresponds to the binary number 11, or or decimal number 3, which means that they will be drawn in with the color
in color register 3. The next four words have ones in the least
significant bit plane but a zero in the most significant bit, so
they’re drawn by color register 1. The next four words have the
zero in the least significant bit and the one in the most significant bit, so they are in color register 2. And the last four words
have zeros in both bit places, so they are background color.
Please note that the numbers formed by joining together
the bit planes refer to color registers and not VDI pen numbers. The correspondence between the color registers and the
VDI drawing pens (also known as the color index) can be
found in Table 4-2. Also note that when using multicolor pattern fills, your pattern array must have the same number of bit
planes as the display (for example, two for medium resolution
and four for low resolution). If the bit_planes value of your
vsf_udpat call does not agree with the actual number of bit
planes used by the display, the call will fail and your pattern
will not be installed. Finally, keep in mind that when you use
the multicolor fill capability of the VDI, each bit plane is combined with the existing picture according to the writing mode,
so if you use a mode other than the default Replace mode,
things can get extremely complicated.
Program 5-3 shows the use of a four-color fill pattern.
The program works on a monochrome monitor also, but you
won't get the multicolor effect. The program displays a
fill pattern that is composed of squares of color 0, 1, 2, and 3. If you
run the program in low resolution, you'll notice that color 3 is
shown as yellow, whereas it is black in medium resolution.
That’s because these colors refer to the hardware registers, not
to the VDI pen colors. Even though VDI pen 1 defaults to
black in both modes, lo-res uses color register 15 for black,
while medium-res uses color register 3. We used the vq_extnd
call to find out how may bit-planes our display uses. This
value is returned in work_out[4].
103

<!-- source-page: 111 -->
## Page 111

CHAPTER 5
Program 5-3. colorpat.c
/ERSEEETETAA
AKA RE REESE EEE EASE
E EERE EEE /
*/
/t
a/
/t%
COLORPAT.C
-- Shows the use
of
the
&/
/t
multicolor
pattern
fill
s/
/t
x/
/k
“/
SESRESERATEARARE
AEE
KE SESSA RARER RRR
E EEE REE
#inciude
“shell.c"
int
colpat(41](i6]
=
¢€
OxOOFF, OxOOFF,
Ox@OFF, OxOOFF,
Ox9OFF, OxOOFF,
OxOGFF,
OxOOFF,
Ox 0699, Oxo,
x08, BxO0e9,
@xFFFF, @xFFFF,
OxFFFF, OxFFFF,
Ox DOOD,
Sx PIO,
Dx BID,
Bx BIAS,
OxBHOB,
BxGIIS,
OxOO8S,
Px8SAG,
@x 2898, Oxe00,
GxIBOG,
Oxnoeea,
Ox899S, Sxoe0e,
Ox 2096,
Bxnoea,
33
Ox OOFF,
Ox OBFF ,
Ox OOFF,
OxQOFF,
Ox BOOS,
Bx BIOS,
OxFFFF,
OxF FFF,
9x BIOS,
Ox ISOS,
Ox BOee,
Ox BOOS,
Ox 9800,
2x BOOS,
Ox BOOS,
Ox B@ae,
Ox OFF,
@xQOrF,
@xOGFF,
OxOOFF,
2x B8O0,
Ox B200,
OxFFFF,
@xFFFF,
Ox PGs,
Bx GOO,
Ox GBS,
Bx BOI,
Bx DIOS,
Bx WIV,
Bx POSe,
Ox BOI,
int
sides
C4]
=
{( 9,8,9,8,3;
demo ()
€
int xstep,ystep,scrh,scrw,cs
scrw
=
work out(@l;
/%
scrh
= work_outl1];
/£
xstep
= scrw/3;
yetep
= scrh/3;
/t
/%
7%
four-color
fill
pattern
&/
get
screen width
¢/
get
screen height
*/
@ach
block
1/3 width
&/
and
1/3 height
&/
vq_extnd (handle,
1,
work_out);
vsf_udpat (handle,colpat,
work_out(4]
d3
/8
set
our
fill
pattern
vsef_interior (handle, 4);
for
(c=@3c0<33c0++)
€
sides(Ol=sides[2];
sidesCiJ
= sides(3];
sides(2]+=xstep;
sides(3]+=ystep;
vr recfl (handle,sides);
/%
draw filled
boxes
&/
}
/&%
End
of
Colorpat.
104
c
&/
/&
find number
of
bit
planes
£/
/%
and
use
it
£&/
s/

<!-- source-page: 112 -->
## Page 112

Filled Shapes
Fill Color and Outlining
There are two more settings that affect fill operations. The first
changes the pen number of the foreground color drawn by
these operations. (As you may remember, the default fill color
was set to the value in work_in{9] at the time the virtual
workstation was opened.) This function is called Set Fill Color
Index, and its syntax should be familiar to you by now, because it’s virtually identical to that of the calls used to set the
marker and line colors:
int handle, pen;
pen_set = vsf_color(handle, pen)
where pen is the number of the drawing pen which you are
requesting as the fill color, and pen_set is the variable in
which the function returns the number of the pen that was actually set.
The final setting is used to determine whether or not the
filled shapes created by the various VDI calls will be drawn
with a solid outline around them. The Set Fill Perimeter Visibility call is the one used to change this setting, and it can be
called like this:
int handle, visibility_flag;
visibility_set = vsf_perimeter(handle, visibility_flag);
where visibility_flag is a value used to indicate whether you
want a visible outline around the fill area, and visibility_set is
a variable in which the actual setting is returned. In both
cases, a Zero value indicates no outlining, and a value of one
(or any other nonzero value) specifies that a visible outline
will be drawn. It should be noted that this particular setting
does not affect the Fill Rectangle (vr_recfl) function, which always draws the rectangle without an outline.
Settings Inquiry
As with the marker and line settings, the current status of the
fill settings can be determined with a single VDI call. The
name of this function is Inquire Current Fill Area Attributes,
and it’s called like this:
int handle, settings[4]
vqf_attributes(handle, settings);
105

<!-- source-page: 113 -->
## Page 113

CHAPTER 5
where settings is a pointer to the array in which the function
returns the information about the fill settings. The contents of
the array are interpreted as follows:
Element
Setting
settings[0] _ fill pattern type
settings(1]
_ fill color pen
settings[2]
fill pattern index
settings[3]
current draw mode
Filled Shape Generalized Drawing Primitives (GDPs)
The VDI supplies a number of GDPs which can be used to
create a wide variety of filled shapes. The simplest is Bar,
which is used to draw a rectangle. This may seem to be wasteful redundancy, since a wide polyline or a rectangle fill each
produce a
filled box, but Bar is just a
little bit different.
A wide
polyline, for example, can be used for a solid box, but it cannot be filled with a pattern, and it uses the line settings rather
than the fill settings. The rectangle fill function is designed to
speedily clear a rectangular area of the screen only (not other
graphics output devices), thus it doesn’t use the outline setting. The bar function, however, can be used by any device,
and it does support outlining. (As its name suggests, it’s very
handy for bar graphs.)
While we’re on the subject of overlapping functions, you
should note that if you set the fill pattern to Hollow, the
drawing mode to Transparent, and turn on perimeter visibility,
then the Bar function can be used to draw just the frame of a
box, as you might do with Polyline.
The syntax for the C language version of Bar is
int handle, sides[4];
v—bar(handle, sides);
where sides is a pointer to an array that holds the location of
each of the four sides of the rectangle. The location of the left
and right sides are in side[0] and side[2], while the top and
bottom are in side{1] and side([3], respectively.
The filled shape equivalent of the line drawing Rounded
Rectangle function is called Filled Rounded Rectangle. As with
the bar function above, all you have to do to draw a
filled
rounded rectangle is point to an array that contains the coordinates of the top left and bottom right corners of the rectangle:
106

<!-- source-page: 114 -->
## Page 114

Filled Shapes
int handle, sides[4];
v_rfbox(handle, sides);
Program 5-4 uses the Filled Rounded Rectangle function
to demonstrate the user-defined fill pattern option. The
rounded boxes are filled with the LOVE pattern discussed in
the section on user-defined fills, above.
Notice how laying new boxes on top of the existing ones
changes the color of the pattern, but not its placement. That’s
because the pattern is always aligned starting with the top left
corner of the screen.
Program 5-4. userfill.c
/OERTREEELERE RET ELEERE TES EKER EERE REESE EERE EEE /
/t
us
/t
s/
7%
USERFILL.C
-- Shows
the use
of
the
%/
/t
user-defined
#111
pattern
s/
/t
“/
/t
a/
este tii
i iit sii
i
tess its iisissccserrititititt
tt ¥4
include
“shell.c”
int
lovepat(i6é]
=
¢
9x 9O99,
Bx3078,
Bx3GCC,
BX3GCC,
/*
“love”
Fill
pattern
%/
@X3GCC,
SX3GCC,
SX3E78,
Bxsoad,
BX66FC,
BX66CH,
BX46CO,
OX32FS,
OX1ECS,
SXPECM,
SX@4FC,
Bxeeas,
3
int points
(43
£4]
=
¢
3,3,18,18,
/%
array
of corners
for
boxes
&/
7,1,12,29,
1,9,29,13,
14,19,13,28,
5
demo ()
{
int
xstep, ystep,scrh,scrw,c,d;
int
sides{4];
scrw
@ work
out(@};
/%
get
screen width
&/
scrh
* work_outCil;
/&%
get
screen height
%/
xstep
= scrw/20;
/® wach block
1/28 width
&/
ystep
= scrh/29;
/&
and
1/2@ height
&/
vef_udpat (handle, lovepat,
1);
/%
set
out
fill
pattern
#/
vsf_interior (handle, 4);
/®&
and
use
it
*/
for
(d=@yd<43d++)
/%
for
4 boxes
%/
€
for
(csOsc<23c+t+)
/*
for
2 sets
of corners
&/
€
sides(ce2J=points(difct2]txstep;
/*
set
block coordinates
a/
sides(c42+1l=points(d](ct2+1]kystep;
3
107

<!-- source-page: 115 -->
## Page 115

CHAPTER 5
if
(d==1)
vsf_perimeter (handle,@);
/% outline only
ist
box
&/
vsf_color (handle,d+1);
/%
change
fill
color
«#/
virfbox (handle,sides);
/®
draw rounded rectangle
%/
}
}
/% End
of
Userfill.c
&/
The final four filled shape GDPs allow you draw filled
circles, ellipses, or pie-shaped wedges of either. The filled circle and the circular pie functions correct the vertical radius for
the aspect ratio of the display screen, so the figures that they
draw appear to be round even on displays like the mediumres color screen, which has tall, skinny pixels. The filled ellipse and elliptical pie functions use whatever horiztonal and
vertical radius that you specify.
The calling sequence for the Circle function is
int handle, x, y, radius;
v—circle(handle, x, y, radius);
where x and y describe the center point of the circle, and radius is the radius measured horizontally. (The vertical radius is
adjusted—it automatically corrected to compensate for the aspect ratio of the screen.)
The syntax of the C version of the Ellipse call is
int handle, x, y, xradius, yradius;
v—ellipse(handle, x, y, xradius, yradius);
where x and y specify the center point of the ellipse, and
xradius and yradius describe the horizontal and vertical radii.
The format for the Pie call is
int handle, x, y, radius, beginangle, endangle;
v_pieslice(handle, x, y, radius, beginangle, endangle);
where x and y are the coordinates for the midpoint of the circle, radius is its radius measured horizontally (the vertical radius is adjusted for the aspect ratio), and beginangle and
endangle mark the starting and ending points for the enclosed
arc. As with the v_arc call, these angles are measured in
1/10s of a degree, starting at the rightmost point of the circle
as zero degrees, and moving counterclockwise, so that the topmost point is at 900, the leftmost at 1800, and so on. The
function draws the arc of the circle described by beginangle
and endangle, connects each end of the arc to the midpoint,
108

<!-- source-page: 116 -->
## Page 116

Filled Shapes
and fills the resulting shape according to the current fill pattern, fill color, and writing mode.
The syntax for the Elliptical Pie function is very similar:
int handle, x, y, xradius, yradius, beginangle,endangle;
v—ellpie(handle, x, y, xradius, yradius, beginangle, endgangle);
The only difference is that you must supply values for both
the horizontal and vertical radii of the ellipse.
Program 5-5 uses the GDP Ellipse command. It also demonstrates a very important point to remember. Pattern fills are
drawn according to the current writing mode, just like patterned lines are. As you can see from the display created by
Program 5-5, the oval drawn in Replace mode (lower left) obscures its portion of the green block completely. The ellipses
drawn in Transparent and Reverse Transparent modes (top left
and top right) let the green block show through everywhere
the fill color was not drawn. And the ellipse drawn in XOR
mode is filled with a different color inside the block than it is
outside the block, since it merely complements the existing
colors.
Program 5-5. fillmode.c
/ESRELESEAATSESAKSTASLERESSEESESS
REE RERREREEES
/%
&/
/t
a/
‘st
FILLMODE.C
-- Demonstrates effect
of
&/
/t
the writing
aode
on filled shapes
%/
/t
&/
/t%
a/
/ECTTEKTACEAESAASASTEKSAAATASSSSRAAEESEREEES
EEE,
#include "shell.c"
demo
()
¢
int c,cx,cy,hr,vr,scrh,scrwy
long
rij;
int pointel4)};
scrw
= work_out(@]y;
/8% get
screen width
%/
scrh
© work_outlil;
/% get screen height
%/
vr
= points£1]
= scrh/4;
/%
set
box
corners,
%/
hr
= points
(@]
= scrw/4)
/8 ovals midpoints
*/
points£2]
= scrw-hr;
points(3)]
= scrh-vry3
vsf_color (handle,3);
/&% green
box
&/
v_bar (handle, points) 3
vaf_color (handle, 2);
/&
£4111
in
red
&/
vef_interior (handle,2)3
/%
Pattern style
%/
vef _style(handle, 12);
/& sub-pattern
12
&/
109

<!-- source-page: 117 -->
## Page 117

CHAPTER 5
for
(cmOzpc<4yc++)
€
if
(¢<2)
cx
=
hry
/8& horiz
coordinate
of
oval
center
%/
else
cx
= scrw-hr};
if
(c
&
1)
cy
= vry
/® vertical
coordinate
of
center
%/
else
cy
= scrh-vr}
vewr _mode(handle,ctl))
/&% change writing mode
%/
v_ellipse(handle,cx,cy,hr,vr,8,
3688);
/&
draw ellipse
%/
}
/*% Efd of Fillmode.c
$/
Area Fill
The next function is the filled shape analog of the Polyline
function. The Filled Area call takes an arbitrary number of
points that you specify, connects them, and fills the resulting
figure using the current fill settings. The shape that you create
may cross over itself in one or more places, like a figure 8; the
function will fill some of the loops, but may leave some adjacent loops unfilled.
The sytnax for the Filled Area call is
int handle, count, points[2*COUNT];
v__fillarea(handle, count, points);
where count holds the number of vertices to be connected, and
points is a pointer to an array of x and y coordinates for those
points. Since each point has a horizontal and vertical component, the array contains twice as many elements as there are
points. Note that in order to insure that the points describe an
enclosed shape, this function connects the last point in the list
to the first point. Thus, it only requires four points to describe
a filled rectangle, while Polyline requires five points to draw
the outline of that box. The function will not draw a figure
that only has one point. If the shape has no area to fill, it is
represented by a single dot if visible outlining is turned on,
and is not drawn at all if outlining is turned off.
Program 5-6 shows how to create a complex filled polygon using the v_fillarea command. Note that where the shape
crosses itself so that there are two or more adjacent enclosed
spaces, the interior ones are left unfilled so that they appear to
be “outside’”’ the polygon.
110

<!-- source-page: 118 -->
## Page 118

Filled Shapes
Program 5-6. areafill.c
rg
LAESESRESESSSERSRESESRESEERUSE ORE SR EER ESEES/
x
/t
/t
a/
1%
AREAFILL.C -- Shows the use
of
the
s/
/%
area
fill
command
s/
/t
a/
/t
s/
SESRATETAAEAEKTAATAAKAKAEREKAREKE
EATER
EEE
SE /
include
"shell.c"
int points
£16]
=
¢
1,2,16,2,7,9,12, 28,
/* vertices
for
polygon
t/
6,90,9,19,18,14,
24,16,
33
demo ()
€
int
xstep, ystep,scrh,scrw,c,ds
int sides{16];
scrw
= work _out(@];
/%
get
screen width
&/
scrh
* work_outCil;
/&
get
screen height
£/
xstep
= scrw/28;
/&
each block
1/28 width
&/
ystep
=
scrh/20;3
7%
and
1/26 height
%/
vsf _interior (handle, 4);
/& Atari-fuji
fill
pattern
£/
for
(c=Bz3e<8yc0++)
/%
for
7 sets
of
corners
t/
€
sides(ct2Jepoints(ct2]txstep;
/8
set
x&y coordinates
%/
sides(ck2+1J=points(c8#2+1]tystep;
3
vsf_color (handle,2)3;
/*
red
#ill
color
&/
v_fillarea(handle,8,sides);
/%
draw filled polygon
%/
/%
End
of
Areafill.c
&/
Flood Fill
The last of the shape filling commands is a general-purpose
flood fill. Unlike the previous commands that we've discussed,
a flood fill (or contour fill, as it is sometimes called) does not
first draw a shape and then fill it in. Rather, it colors in an existing enclosed area. The color and pattern with which it fills
the area depend on the fill color and pattern settings.
111

<!-- source-page: 119 -->
## Page 119

CHAPTER 5
Flood filling operates in one of two modes. In outline
mode, the entire area enclosed by a border of the outline pen
color is filled. Filling begins at a point which you specify and
moves outward in all directions. As it does so, every horizontally and vertically adjacent pixel which is not colored with
the pen designated in the call as the outline color is filled according to the fill color and pattern. The fill pattern stops
spreading at each point where it encounters a pixel colored by
the outline or contour pen. If the area to be filled is not completely surrounded by a border of that outline color, the fill
will “leak” out, and the entire display area (or clipping rectangle) will be filled.
In color mode, all adjacent pixels of the same color are
filled. You designate the point at which filling begins, and whatever pen was used to color that point becomes the color which
the fill routine displaces. As the fill moves outward, every horizontally and vertically adjacent pixel which is colored with
the displacement pen is filled. The fill stops spreading at each
point where a pixel drawn in another pen color is encountered.
The syntax for the Contour Fill call is
int handle, x, y, pen;
v—contourfill(handle, x, y, pen);
where x and y specify the point at which filling begins, and
pen specifies the outline pen number for outline mode. If the
value for pen is negative, the color replace mode is used, and
the fill replaces adjacent pixels that are drawn in the same pen
color as the point x,y.
Program 5-7 demonstrates both modes of contour filling.
First, a frame is created out of two wide rounded boxes. Next,
the enclosed spaces are filled in outline mode. Finally, the
frame itself is filled using color mode.
Program 5-7, flood.c
/ERETEATESERACERSAR
TERESA EAE
EER ERE EKER EKE/
/*%
as
/t
a/
/t
FLOOD.C
-- Demonstrates two different
t/
/t
kinds
of
flood
fill
using
the
xs
/t
v_contour fill
command
a/
/*
/
/ETSETKACETTATERAAEKEERSS
SATA TERER ARATE
TE EEKS
#include
"shell.c"
int
points
€23
(4)
=
¢
1,6,19,12,
/&
array
of
corners
for
boxes
*/
112

<!-- source-page: 120 -->
## Page 120

Filled Shapes
6,1,13,19,
+3
demo ()
c
int
xstep, ystep, scrh,scrw,c,d3
int
sides(4];
scrw
=
work out(@];
/%
get
screen width
&/
scrh
= work_outfil;
/%
get
screen height
«/
xstep
= scrw/28;
/%
each
step
1/28 width
%/
ystep
= scrh/26;
7%
and
1/28 height
&/
vsl_width(handle,9);
/%&
wide
lines
for
boxes
&/
wsf_color (handle,
2);
/&
£111
color
=
red
%&/
vef_interior (handle,2);
/%
use patterned
fill
&/
vsf_stylethandle,
19);
for
(d=O3d<23d++)
/&
for
2 boxes
&/
€
for
(cmB30<230++)
/t
for
2
sets
of
corners
%/
€
sides(ck2I=points(dilce2}kxstep;
/k
set
box
coordinates
%/
sides(c&2+1J=points(di€ct2+11]%ystep;
}
virbox (handle,sides);
/%
draw rounded rectangle
*/
3
for
(d=@3d<2; d++)
/%
for
2 boxes,
fill
at opposite corners
&/
€
v_contour fill (handle, points({dI[Sikxstep+19,
points(djilCiltystep+i9,i);
vicontourfill
(handle, points(dI£2]&xstep-1d,
points(d]£31tystep-18,1)3
>
vef_color (handle,3);
/%
change fill
color
to green
*/
vef_style(handia,
16);
/&
change fill
pattern
for
mono systems
%/
v_contour fill (handle, xstep, 7%ystep,—1);
/*®
£111
outline
of
boxes
%/
3
/t
End
of
Flood.c
&/
BASIC Fill Commands
The first release of ST BASIC contains a number of keyword
commands that correspond to the filled shape commands that
we've covered in this chapter. The COLOR command can be
used to set not only the fill color but also the fill style and index. There is also direct support for the GDPs that drew filled
circles, ellipses, pie slices, and elliptical pies. The BASIC command PCIRCLE creates a
filled circle or pie slice, while the
command PELLIPSE outputs a
filled ellipse or elliptical pie
slice. Finally, the FILL command supports the contour fill
function.
113

<!-- source-page: 121 -->
## Page 121

CHAPTER 5
Although not yet released at the time of this writing, the
planned revision of ST BASIC appears to offer even more support for the filled shape functions. Area filling is supported in
two formats:
AREA x,y; x1,y1; x2,y2,..... xn,yn
MAT AREA count, array( )
In the first, the keyword AREA is followed by a minimum
of 3 coordinate pairs separated by semicolons. These coordinates specify the area to be filled. In the second format, you
place the coordinates in an array, and then specify the number
of points to be drawn and the name of the array.
The Bar command is supported by a variation of the
BOX command:
BOX FILL x1,y1;x2,y2
where the first set of coordinates specifies the upper left corner of the box, and the second specifies the lower right corner.
Finally, the new ST BASIC supports the user-defined fill pattern with the command PATTERN:
PATTERN planes, array
where planes is the number of bit planes, and array is the
name of the array which holds that number of 16 two-byte
values.
Of course, you can still access all of these functions using
the POKE and VDISYS commands. Program 5-8 shows how
to use some of the unsupported functions, such as v__rfbox.
Program 5-8. fill.bas
192
fullw
2:
clearw
2
119d
res
= peek (systah)
128
if
(res<4)
then
scrw
= 639 else
scrw
=
319
138
if
(res>1)
then
scrh
=
199 else scrh
= 399
146
xstep
= scrw/28:
ystep
= scrh/20
158
REM
Set User-defined
Fill
Pattern
168
poke contrl1,112
:REM opcode
for
udpat
172
poke contri+2,
3
:REM
no points
in ptsin
188
poke contri+é,
16
:REM
16 words
of
pattern
data
in
intin
array
196
for
x=8
to
15
288
read
d:
poke intin+(2%x),d
212
next
x
228
vdisys(1)
238
REM
248
for
d=@#
to
3
258
if
d<>1l
then
goto 348:
REM outline only first
box
268
REM
278
REM Set perimeter outline visibility
288
poke contrl,194
:REM opcode
114

<!-- source-page: 122 -->
## Page 122

Filled Shapes
299
388
319
328
330
3408
356
368
378
380
396
490
418
428
436
449
4350
469
478
480
498
588
51g
520
S38
548
350
578
poke contrl+2,9
poke contrl1+é6,1
poke
intin,@
vdisys (1)
REM
REM Set
Fill
Color
and
interior
fill
style
COLOR
1,d+1,1,4
REM
REM Draw Filled Rounded Rectangle
poke contri,ii
:REM opcode
for
GDP
poke contrl1+18,9
:REM sub-opcode
for
rfbox
poke contrl+2,2
:REM
2 corners
in ptsin
poke contri+é6,@
for
c=@
to
1
read
x,y
poke ptsint+(c84),xkxstep
poke ptsin+(ct4+2), ,ytystep
next
c
vdisys(1)
REM
next
d
REM
DATA
8, 12408, 12492, 12492, 12492, 12492, 15992,8
DATA 26364, 26304, 26304, 13848, 7872, 3776, 1788, 8
REM
DATA 4,5,16,16
DATA 7,3,12,18
DATA 1,9, 18,13
DATA 14,18,13,18
115

<!-- source-page: 124 -->
## Page 124

Chapter 6
Drawing and
Manipulating
Image Blocks
.

<!-- source-page: 126 -->
## Page 126

So far, we’ve seen how the VDI provides functions to
draw images point by point or with lines and geometric
shapes. But perhaps the most powerful of the VDI drawing
functions are the raster functions that move and manipulate
an entire block of pixels at once. This type of operation, often
referred to as a Bit BLiT (Bit BLock Transfer), allows you to
draw and animate images on the display screen. On the original ST models, the bit manipulation is performed entirely in
software. Atari has been working on hardware support, however, in the form of a blitter chip, a device that greatly speeds
up such operations. By the time you read this, this hardware
upgrade and new TOS ROMs that support its use may already
be available.
The VDI raster operations are extremely flexible. The
blocks of memory that they move may be located in the
screen display area or in the program’s data storage space.
They can copy images that have the same number of colors as
the current display mode or place two-color images into a
multicolor display. The images may be reproduced exactly, or
they may be combined in a number of different interesting
ways with existing images. All of the image or only a selected
portion of it may be moved.
The one thing that all raster operations have in common
is the format used to describe the bit image. Before the VDI
can perform the memory manipulation necessary to move images on the screen, it needs several key pieces of information.
These include the starting memory location of the image data,
the width and height of the image in pixels, the number of
words of data necessary to store the image, the format of the
bit image, and the number of color planes used. Since in GEM
parlance a bit image is known as a raster form, the data structure in which this information is stored is called
a Memory
Form Definition Block (MFDB). It consists of ten, 16-bit words
of information, laid out as follows:
119

<!-- source-page: 127 -->
## Page 127

CHAPTER 6
Word
Contents
1
High half of the beginning address of the image data
Low half of the beginning address of the image data
Raster image width in pixels
Raster image height in lines
Raster image width in words
Image format flag
0 = ST specific format
1 = Standard GEM format
Number of color bit planes
Reserved for future use
Reserved for future use
Reserved for future use
Ant WN
OoOwoon
The C language definition for this data structure is
typedef struct fdbstr
{
int *fd_addr; /* pointer to image data area */
int fd_w; /* image width in pixels */
int fd_h; /* image height in pixels */
int fd_wdwidth; /* image width in words */
int fd_stand; /* standard format flag */
int fd_nplanes; /* number of color bit planes */
int fd_rl1, fd_r2, fd_r3; /* reserved for future use */
}FDB;
This definition may be found in some versions of the
header file Obdefs.h or in another header file that comes with
your C compiler. Our definition uses the variable type int to
describe a 16-bit value, but for compilers that use a 32-bitwide int, the variable type would have to be changed to short
(or WORD, if that term has been defined by a portability macro).
The first member of this structure, fd_addr, is a pointer to
the integer array that holds the actual shape data for the image. As an address pointer, it’s a 32-bit value. Some versions
of the structure definition make the first element a pointer to a
char, but since the image data is always an even number of
words long, it’s more convenient to use a pointer to int. We'll
discuss the size and format requirements of the image data
block that this value points to a
little bit later on. If the value
stored in fd_addr is zero, rather than an actual address, it’s a
signal for the VDI to use screen display memory for the image
block. In such a case, the VDI ignores the rest of the values in
the memory form definition block. It uses the beginning address of screen memory for the first value, and the width,
120

<!-- source-page: 128 -->
## Page 128

Drawing and Manipulating Image Blocks
height, and number of bit-planes for the current display
screen. The format flag is set to show that the display is in STspecific format.
The next two members, fd_w and fd_h, specify the width
and height of the image in pixels. Though the actual image
data block is made up of word-length values, and thus must
be an even-multiple-of-16 pixels wide, the image itself does
not have to occupy all of that width. For example, you can describe an image that’s 26 pixels wide, even though you must
use 32 bits of data to do it. If the rightmost portion of the image only uses a part of the last word on each line, like the example above which only uses 10 bits of the last word, it’s
known as a fringe. Images that are not an even-multiple-of-
16-bits wide tend to be drawn a
bit more slowly than images
that are an even-number-of-words wide, since the VDI is always forced to do bit manipulation on them to mask out the
unwanted bits.
The next member of the structure, fd_wdwidth, is used to
store the number of words of image data per line. If the width
is not an even multiple of 16 pixels, you’ve got to round it up
to the next highest even multiple and then divide by 16 to get
this value.
Next in the structure comes fd_stand, a flag that shows
whether the image data is arranged in standard GEM format,
or the machine-specific format of the host computer’s display
circuitry. A value of 1 means that it is in the standard format,
while a value of 0 means that it is arranged in the format of
the ST display memory.
The last significant item in this data structure is
fd_nplanes. This item is used to store the number of color bit
planes used by the image. As we have explained earlier, one
bit plane is needed for a monochrome (actually, 2-color) image, two bit planes are needed for a 4-color image, and four
are required for a 16-color image. Since each of the ST’s display modes uses a different number of bit planes, your application should determine how many planes are in the current
screen and proceed accordingly. The vq_extnd function can be
used to determine the number of planes in the display; this
value is returned in work_out[4] when you use the call to retrieve the Extended Inquire information.
The most important piece of information needed to draw
bit images, though, is the actual image shape data. GEM al-
121

<!-- source-page: 129 -->
## Page 129

CHAPTER 6
lows this image data to be stored in one of two different formats, The first, the machine-specific format, is the fastest and
easiest for the VDI to use, since it conforms to the internal
configuration of the ST’s own display memory. The second,
the GEM standard format, is offered for purposes of portability. Since the VDI offers a function for converting an image
from one format to the other, you can create an image in the
GEM standard format, and then convert it to the machinespecific format of the host computer, without having any idea
what the display memory layout of that computer is like. If
you plan to write software only for the ST, though, you'll
probably have no need for the standard format.
By now, both formats for image data storage should be
fairly familiar to you. We discussed the ST display memory
scheme, in Chapter 4, as an interleaved bit-map. This means
that color information is stored in adjacent bits in the same
byte of memory. In the 4-color mode, the first byte of each
line describes the four colored dots at the extreme left of that
line. Each adjacent bit pair stores
a number from 0
to 3, indicating the color register used to color that dot. The most significant two bits describe the leftmost dot, and each less
significant bit pair describes the next dot to the right. In the
16-color mode, the first byte of each line describes first two
colored dots on the line. Each nybble (four-bit group) stores a
number from 0 to 15, indicating the color register used to
draw the dot. The high-order nybble describes the leftmost
dot, and the low order nybble holds the information for the
dot to its right.
Standard GEM image format is like the format used to
store multicolored fill patterns, that we described in Chapter 5.
In standard format, each bit of color information is in a separate data block called a bit-plane. A 4-color image has two
separate bit planes, and a 16-color image contains four bit
planes. Each plane contains a different bit of color data for the
same dot. For example, the most significant (leftmost) bit of
the first word of each line of data in each bit plane contains
information about the first dot in the top line of the picture.
The bit in plane 0, the first plane, contains the least significant
bit of information, and the bits in each succeeding plane contain the next most significant bit of information. Putting the
122

<!-- source-page: 130 -->
## Page 130

Drawing and Manipulating Image Blocks
bits from the various planes together forms the number that
gives the color data for that dot. (See Figure 5-1.)
Note that a two-color (monochrome) image has one bit
plane in standard format, just as it does in the ST-specific format, since each dot has only one bit of associated color data.
This means that for monochrome images, the standard format
is exactly the same as the ST-specific format.
Copy Raster Opaque
The first of the VDI raster functions is called Copy Raster
Opaque. Its name comes from the fact that this function copies
the same number of bit planes from the source memory area
as there is in the destination area, so that the former can be
copied pixel by pixel to the latter. The source image can’t be
rotated or scaled in size with this function, though you can
use this function to move the image data from the screen to
memory, where you can manipulate it more easily. The C syntax for this call is
int handle, mode, points([8];
struct fdbstr *srcMFDB, *destMFDB;
vro_cpyfm(handle, mode, points, srcMFDB, destMFDB);
where the value mode indicates the writing mode used for the
operation. Despite its name, this function does not necessarily
perform a straight copy of the source image. Rather, it can
combine an image with the existing destination image in a
number of interesting ways. These writing modes are similar
to the general drawing mode set by the vswr_mode( ) call, but
they are set separately and are more comprehensive. They include the old standbys like Replace and XOR mode, and also
add new combinations, some more useful than others. The following chart shows the 16 different combinations available
with the vro_copyfm( ) call. The logic operations are described
using the symbol S to refer to the source image, D
to refer to
the starting destination image, and D1 to refer to the resulting
destination image. Some of the more useful modes also have a
plain-language description that explains more clearly what
they do.
123

<!-- source-page: 131 -->
## Page 131

CHAPTER 6
Mode _ Logic Operation
Description
Number
0
D1 =0
Clear destination block
1
D1 =SANDD
2
D1 = S AND (NOT D)
3
D1 =S5S
Replace mode
4
D1 = (NOT S) AND D
Erase mode
5
Di =D
Destination unchanged
6
D1 =
S$ XORD
XOR mode
7
D1 =SORD
Transparent mode
8
D1 = NOT (S OR D)
9
D1 = NOT (S XOR D)
10
D1 = NOT D
11
D1 = S OR (NOT D)
12
D1 = NOTS
13
D1 = (NOT S) OR D
Reverse transparent mode
14
D1 = NOT (S AND D)
15
D1 =1
Fill destination block
As you can see, some of these operations are almost useless. For example, number 0 blanks the destination rectangle
to the background color, while number 15 fills it with all ones,
in effect changing it to pen color 1. Either of the operations
could be performed more effectively with vr_recfl( ). Mode
number 5
literally does nothing, leaving the destination unchanged, while mode number 10 merely reverses every bit in
the destination, without regard to the source image.
The points parameter in the vro_copyfm( ) call is a
pointer to an array of coordinates that describe two rectangles.
Since the vro_copyfm( ) call can be used to move only a portion of the total image described in the MFDB, these rectangles
describe the portion of the source MFDB from which the image is copied and the portion of the destination MFDB to
which it is copied. The elements of the points array are
Element
Description
points[0]
Left edge of source rectangle
points[1]
_ Top edge of source rectangle
points[2]
Right edge of source rectangle
points[3]__
Bottom edge of source rectangle
points[4]
Left edge of destination rectangle
points[5]
Top edge of destination rectangle
points[6]
Right edge of destination rectangle
points[7]
Bottom edge of destination rectangle
124

<!-- source-page: 132 -->
## Page 132

Drawing and Manipulating Image Blocks
These points describe an offset from the upper left corner
of the form. Though the entire source and destination forms
need not be the same size, the source and destination rectangles that you describe should be. If they are not, unpredictable
results may occur. (At best, the size of the source rectangle
will be used.) You should also take care to make sure that the
rectangles you describe do not exceed the width or height of
the form as a whole.
The final two parameters are pointers to the source and
destination MFDBs. Both of these MFDBs must use image data
that is in ST-specific format. Standard-format MFDBs should
be converted to ST-specific format prior to this call with the
Transform Form (vr_trnfm) call. It is possible for the source
and destination forms to be one and the same. For example,
you can define a form which uses the display screen for its
image data (by setting fd_addr to zero) and use this call to
move an image from one part of the display to another part.
It’s even possible to move an image from a source rectangle
that overlaps with the destination rectangle. In such a case,
the VDI copies in whatever direction is necessary to preserve
the source image, so that the destination doesn’t corrupt the
source before the copy is complete.
Program 6-1 demonstrates the use of the Copy Raster
Opaque function. It first draws a happy face, using the normal
VDI drawing commands. It then uses vfo_copyfm( ) to move
that image from the screen to a memory form. Finally, it fills
the screen with a patterned background, and then uses
vro_copyfm to move the image back to the screen, using each
of the 16 drawing modes.
Program 6-1 illustrates the various copy modes more
clearly than any description of them. The mode numbers
progress from the top left corner (0) to the bottom right corner
(15). The face in the top right corner, which was copied using
mode number 3, Replace, shows the image that was originally
drawn on the screen, as it appeared (briefly) before we filled
the screen with the pattern. If you have a color display, you
will notice that the results in lo-res mode are slightly different
from those in medium-res mode. If you add more colors to the
picture, the results get even harder to predict. That’s because
the logical operations which combine the two images are performed separately on each bit plane.
125

<!-- source-page: 133 -->
## Page 133

CHAPTER 6
Program 6-1. copymode.c
/ESEEERTEREEARREEA
EERE RARER RARER EEE,
/%
/%
/%
‘t
/t
‘t
/t
a/
“/
COPYMODE.C
-- Demonstrates copying
%/
modes offered
by the Copy Raster
x/
Opaque function.
a/
&/
x/
SEGKERERET EAA
S ERE E ERATE EERE KERR EERE EEK,
#include
"shell.c”
Hdefine WHITE
9
*#define BLACK
1
#define RED
2
#define GREEN
3
demo ()
€
/t
126
struct
fdbstr
€
int
timage;
/*
memory pointer
&/
int
width;
/t
form width
in pixels
&/
int
height;
/%
form height
&/
int
wordw;
4%
form width
in words
&/
int
flag;
/&
form flag
&/
int
planes;
/*
number
of
color
planes
&£/
int
rl,
r2,
r3;
}srcMFDB,
destMFDB;
int
imagedat(i@99];
/&%
buffer
for
destMFBD
itrage data
*/
int
points(8@];
int xstep,ystep,
xres,yres,
scrh,scrw,
Cyd,
mode;
scrw
=
work_out[@];
/%
find
screen
width
%/
scrh
=
work_out{il;
/&
and height
%/
xetep
= scrw/4;
/*®
set
x
and
y
step
increments
%&/
ystep
= scrh/4;
/%
to
1/4 screen width
and
height
%/
Draw
a happy
face with
VDI
drawing commands
%/
vsf_interior (handle, 1);
v_ellipse (handle, (xstep-18)/2, (ystep-18) /2, (xstep-16) /2,
Cystep—16)
/2,3, 3689);
vsf _color (handle,
GREEN) ;
v_e@llipse (handle, (xstep—-18) /4, (ystep-19) /3, (xstep-12) /8,
Cystep-12)
/8,8, 3409);
vef_color (handle, WHITE);
viellipse (handle, (xstep-19) /4, (ystep-18) /3, (xstep-12) /14,
(ystep-12) /16,8, 3689) ;
vsf_color (handle, RED) ;
v_@llipse (handle, 3% (xstep-18) /4, (ystep-18) /3, (xstep-12) /8,
(ystep-12)/8,8, 3689);
vef_color (handle, WHITE);
v_ellipse (handle, 3% (xstep-18) /4, (ystep-1@) /3,
(xstep—12)/16, (ystep—12) /16,8, 3698) ;
vel_color (handle, WHITE) ;
vel _width (handle,5)
3;
v_ellarc (handle, (xstep—19)/2, (ystep-18)/2,
(xetep-12)/3, (ystep-12) /3, 2198, 3308)
;

<!-- source-page: 134 -->
## Page 134

Drawing and Manipulating Image Blocks
/%&
Use vq_extnd
to
find
x
and
y resolution,
#
of
bit
planes
&/
vq_extnd (handle, 1,work_out);
if
(¢(
work_out(4]
==
4)
xres=1;
else xres=2;
if
(work_out(4]==
1)
yres=2;
else yres=1;
/%
Set
up
a source
form using screen
data,
and
a destination
form using
a memory buffer
*/
srcMFDB.image
=
@L;
/t
use screen
data
for srcMFDB
&t/
destMFDB.image
=
imagedat;
destMFDB.width
= S@txres;
destMFDB. height
= S5@tyres;
destMFDB.wordw
= 3%xres;
destMFDB.flag
=
@;
/& ST-specific
form
%/
destMFDB.planes
= work_out(4];
points(9)=points(4I]=pointsl(1IJ=points([53=98;
points(2}=points(61=xstep—-19;
points(31=pointst(7 l=-ystep-12;
/%
Copy the happy
face
from the screen
to the memory
form
*/
vro_cpyfm(handle,3,points,&srcMFDB,
&destMFDB) ;
7%
Flood
the whole screen
with
a cross-hatch pattern
&/
points(23=
scrw;
points{3]
=
scrh;
vaf_interior (handle,
3);
vsf_stylethandle,3);
vsf_color (handle,
BLACK);
vr_recfl (handle, points) ;
/%
copy
the
form back
from memory
to the screen,
using
each
of
the
14 copy modes
&/
points([2]
= xstep-18;
points(€3]
=
ystep—-18;
points[{4]
= xsteps3;
for (c=mode=6;
<4; ++c)
<
points(Sl=ystepkc+5;
points(7J=ysteps
(c+1) -5;
for (d=95
d< 4; ++d)
<
points(43=xstepkd+5;
pointsl4éJ=xsteps(d+1)—S;
vro_cpyfm(handle,
modet++, points, &destMFDB, &srcMFDB) ;
}
/%
End
of
Copymode.c
%&/
There are many uses for the vro_copyfm( ) call. It can be
used to move around large areas of the screen display, as when
you scroll the contents of a window. It can be used for stamping images on the screen, or for saving predrawn images from
the screen to
a memory buffer, where they may be manipu-
127

<!-- source-page: 135 -->
## Page 135

CHAPTER 6
lated and redrawn. It can even be used for animating color
shapes, by drawing the shape, erasing it, and moving it.
The XOR mode is particularly useful for this type of animation. As was mentioned in the discussion of the writing
modes, an XOR drawing operation is by definition reversible,
since reversing the bit patterns the first time changes the color,
while reversing them a second time restores them to their
original pattern. Therefore, to move an image that was drawn
with an XOR operation, you need only to draw it with an XOR
to the same spot to erase it, and then draw it with an XOR to
the new spot to make it move. While this course of action is
convenient, it isn’t exactly without flaw. As we have seen, the
color that an XOR image takes depends on the color of the background on which it’s drawn, and, if the background is multicolored, the image will be, too. If the image is moved over a
very complex colored background, therefore, it will change
color as it moves. And if there’s more than one image moving
at the same time, these images will change colors yet again
when they pass over one another. Because of the complexity
of the combinations of the various bit-planes in a multicolor
image, these color changes can be unpredictable. Yet, despite
these limitations, the XOR drawing operation can be effective
for animation in many situations. An example of animation
using the XOR mode can be found at the end of this chapter,
in the section dealing with the vrt_copyfm( ) command.
Transform Form
The advantage of using the standard form for image data storage is that it allows you to render an image without knowing
the specifics of the display memory layout used by the target
computer. But since vro_cpyfm and vrt_copyfm both require
that the source and destination forms be in machine-specific
format, you've got to have a way of converting to that format.
Converting forms back and forth between standard and
machine-specific formats is the function of the VDI routine
named Transform Form. It moves the source form to the destination form, converting it to the opposite type (indicated by
the fd_stand flag of the source form) along the way. The function may be called like this:
128

<!-- source-page: 136 -->
## Page 136

Drawing and Manipulating Image Blocks
int handle;
struct fdbstr *srcMFDB, *desMFDB;
vr_trn_fm(handle, srcMFDB, desMFDB);
where srcMFDB is a pointer to the source MFDB, and desMFDB
is a pointer to the destination MFDB. Note that the source and
destination form definition blocks may be the same. In such a
case, the form is said to be transformed in place. While this is
fine for small images, the process can be very slow for larger
ones on machines like the ST, where the machine-specific layout is very different from that of the standard format. So, if
speed is a consideration, it would pay to set up a destination
block separate from the source.
Program 6-2 uses a color image that’s stored in the standard format. In fact, it’s almost the same image data that was
used in the Colorpat program for the four-color pattern fill.
The only real difference between the data format used by
color pattern fills and standard forms is that the former is only
one word (16 bits) wide by 16 lines high, while size of the latter is not so restricted (our example is 32 bits wide). Since the
image is not very large, we performed the transformation to
the ST-specific form in place, before using the vro_copyfm(
)
command to draw the image.
Notice that by providing enough data for the largest number of bit planes in use (4), we can use the same image data
for all three resolution modes. The modes that need less data
only use the number of planes that they need, and so have
roughly the same form as the lo-res image, if less color detail.
But because of the difference in the number and size of pixels
in each mode, the image will not appear in the same size and
aspect ratio in the various modes. Therefore, you'll probably
want to supply different image data for each of the three
modes, even if using the standard format. If not, your images
will turn out like the icons on the Desktop—tall and skinny in
medium resolution, and much larger in low resolution than in
high resolution.
129

<!-- source-page: 137 -->
## Page 137

CHAPTER 6
Program 6-2. stdform.c
SERTAAKAERARAA
TERETE TEETER ERE E EEE E RES
/*
x/
/%
s/
/t
STDFORM.C
-- Demonstrates the use
a/
/%
of
standard
image data format,
and
a/
/t
the Transform Form function.
x/
/t
a/
/%
a/
/EREEEKAAATAAE
EERSTE ERATE AERA
ERE EE ES /
#include
“shell.c"
int
imagedat(]
=
¢
SxOGFF,
OxOGFF,
SxO@OFF,
Sx OFF, OxGOFF,
Ox VWOFF,
OxOOFF,
Ox@OFF,
OxO@FF,
OxOGFF,OxGSFF,
GxGerr,
OxDOFF,
BxOOFF,
SxOOFF,
OxDOFF,OxOOFF,
Ox OIFF,
OXxOOFF,
Ox@OFF,
OxO@OFF,
OxSOFF,OxOGFF,
@xOOFF,
Ox9GOS, 2x9BWS, BxOO9S, Ox09GG, Ox9BGG, ox200B,
BxBIOS, Ox99SS, OxVOOS, OxBIGG, Gxgeee, Gxoaed,
OxFFFF, OxFFFF, @xFFFF, OxFFFF,@xFFFF,
OxFFFF,
OxFFFF, OxFFFF, @xFFFF, @xFFFF,@xFFFF, 8xFFFF,
Ox OBIS,
DxOWOS, Wx,
OxSGGE, Srosee,
Ox soa,
GxBIOS,
DxBIWOS, DKW, OxAGOE,
Sx GOOG,
Sx Ggae,
BxBIOD,
DPxWIS,
OWxBOSS,
Bx OSI, SxGGQs,
Oxgoae,
BxBIOD,
OxAIOS, DOW,
Px SWSS,
Ax GBI,
Sxgeas,
Ox BIB,
DPxOWOS,
BxGIGO,
Sx SSIS,
Sx OGaG,
Mxseee,
BxBIOO,
BDxGIOP,
DxWWIO,
BxSOIS, GxGIqG,
Sx GIs,
OxBIOD,
BDxGWWO,
WxOISP,
Bx GOST, Oxgead,
Sxaeae,
GxGGOG,
GxDDGG,
AxOGDO,
Ox WIS,
Gx GOOD,
BxdOIs,
+5
demo ()
€
struct
fdbstr
€
int
timage;
/& memory pointer
«/
int
width;
/%
form width
in pixels
&/
int
height;
7%
form height
&/
int
wordw;
/*
form width
in words
%/
int
flag;
/%
form flag
&/
int
planes;
/& number
of
color planes
¢/
int
ri,
r2,
r3}3
}srcMFDB, screen;
int points[6];
int
step,scrh,scrw,cy}
scrw
=
work _out(91/32;
/&
find
screen width
gserh
=
work_outl(ijl/163
/*
and height
%/
step
=
(scrw
<
scrh)
7?
scerw
:
scrh;
/&
Use vq_extnd
to
find
#
of
bit
planes
t/
vq_extnd (handle, 1,work_out)3;
/*&
Set
up
a destination
form using
screen
data,
and
a source
form using
a memory buffer
&/
Ox OOFF ,
Ox OOFF,
OxOOFF,
Sx OOFF,
Ox S998,
8x SSG,
OxFFFF,
OxFFFF,
GxO085,
GxGSas,
Ox BOBS,
Ox seee,
Ox SISO,
Sudo,
Ox BOOo,
Ox OOOO,
%/
Ox OFF,
Ox9QFF,
Ox QOFF,
OxOOFF,
2x 9990,
oxeee,
@xFFFF,
OxFFFF,
Bx BOIS,
Bx BWBO,
Ox S829,
Bx BWOS,
Ox BIVe,
Sxoaed,
Sx ooea,
Ox BVO,
screen.image
=
OL;
/*
use screen
data
for srcMFDB
¢/
130

<!-- source-page: 138 -->
## Page 138

Drawing and Manipulating Image Blocks
ercMFDB.image
=
imagedat;
srcMFDB.width
=
32,
srcMFDB. height
=
16;
srcMFDB.wordw
=
2;
srcMFDB.flag
=
1;
/% standard
form
%/
srcMFDB.planes
= work _out[4];
vr _trnfm (handle, &ercMFDB, &ercMFDB);
/&
in Place transform
%/
/*
set
up
initial
screen points
for
the image
%t/
points(@1=points(41=points[1)]=points(5]=9;
points(2Zi=points(63=313
pointsl33=pointsl71=153
/*
Copy the colored
box
from the menaory form
to the screen
repeatedly
in
a diagonal
line
&/
for (c#8;c<stepj3ct+)
€
vro_cpyfa(handle,3,points,&ercMFDB,
&screen) 3
Points£5]+=16;
points(7I]+=16;
pointsl[4j+"32;3
pointsl4J+=32;
/&
End
of
stdform.c
%/
Copy Raster Transparent
The last raster function is Copy Raster Transparent. This operation copies a source form that only has one bit plane of image data into a destination form that can have several color
planes. Since a single bit plane image requires the least
amount of image data, this is
a very economical way of placing an image on the screen. In fact, it’s the method used by
GEM for drawing icons on the screen. Since this call allows
you to specify the pen color that will be used to draw both the
foreground (one bits) and the background (zero bits), the image can be drawn in any color combination that you wish. The
C language syntax for this call is
int handle, mode, points[8],pens[2];
struct fdbstr *srcMFDB, *destMFDB;
vrt_cpyfm(handle, mode, points, srcMFDB, destMFDB, pens);
The mode value used for this call is the same as that
used by vswr_mode( ), not the more complex one used by
vro_cpyfm( ). As you may recall, the four writing modes are:
131

<!-- source-page: 139 -->
## Page 139

CHAPTER 6
Mode
Description
Replace
a
Transparent
XOR
Reverse Transparent
hm ON
The parameters srcMFDB and destMFDB are pointers to
the source and destination forms. The source form must contain only a single bit plane, and it’s irrelevant whether it’s in
~
standard or ST-specific format, since both are the same for a
monochrome image. The destination format may contain 1, 2,
or 4 bit-planes, and should be in ST-specific format. A screen
form, the most common destination, is already in that format.
The points array is the same as that used by vro_cpyfm( ).
The first four elements describe size and position of the source
rectangle, and the last four describe the destination rectangle.
The rectangles are offset from the top left corner of the forms,
and the source and destination rectangles should be the same
size.
The value that pens points to is an array which holds two
pen numbers. The first, pens[0], contains the pen number of
the foreground color which will be drawn wherever there is a
one bit in the source image. The other, pens{1], contains the
pen number of the background color which is drawn wherever
there is a zero bit in the source image. Note that these are the
VDI pen numbers (color index), not the actual hardware register numbers formed by the various bit combinations. These
colors will be translated to the appropriate bit combinations
when the single plane image is expanded to the number of
planes used by the screen. The resulting expanded image is
then combined with the destination image, bit plane by bit
plane, according to the logic operation chosen.
Program 6-3 copies a predefined image to the screen,
-
using the XOR mode. It demonstrates a simple form of
animation.
Notice that in order to have the image appear in the same
size and aspect ratio in all three resolution modes, we had to
provide three different arrays of image data. This is admittedly
a lot of data to type in by hand. Fortunately, some of the
-
painting programs available for the ST, such as Neochrome
and DEGAS Elite, allow you first to create an image by drawing with the mouse and then to save that image to a
text file
in the form of C source code. This source code file is in the
132
_

<!-- source-page: 140 -->
## Page 140

Drawing and Manipulating Image Blocks
form of an initialized array that can be merged into your program file.
You may have noticed the use of the XBIOS call Vsync.
This is used to combat the flickering that can occur when you
move an image on screen while the display is being redrawn.
The Vsync call pauses the program until the the vertical retrace interval occurs. That’s when the video beam reaches the
bottom of the picture and shuts off until it gets back up to the
top. This allows you to change the image in display memory
when the display is not being changed.
Program 6-3. copytran.c
/RRTETTAESAAAKSS
SKEET TEAK ETARERERE TEESE /
/t
a/
/%
“/
/%
COPYTRAN.C
-—- Demonstrates the Copy
%/
/t
Tranparent
function,
including
some
a/
/t%
animation using
the
XOR copy mode.
%/
/t
s/
/%
&/
/ECTATACTERACTAKTATAATTERASAEEKEKATAE
EKER EET E/
#include
"shell.c”
#include <osbind.h>
tHdefine WHITE
@
#define BLACK
1
#define RED
2
define GREEN
3
struct
fdbstr
€
int
timage;
/%
int
width;
/*t
int
height:
/%
int
wordw;
‘*t
int
flag;
/t
int
planes;
/t
int
ri,
r2,
r3;
}screen,view£2);
/&
int colors(23={BLACK,
WHI
demo ()
€
int points(81;
int scrh,scrw,
c,d,@3
scrw
=
work_outl@;
scrh
=
work_outlil;
/&
put
a patterned block
points[8]
= scrws3/8;
points(1)
= scrh#5/8;
memory pointer
%/
form width
in
pixels
&/
form height
*/
form width
in
words
%/
form
flag
%/
number
of
color
planes
%/
forms
for
the screen,
and
2 views
of
the
image
%/
TE};
/*
XOR does use colors,
but
you
still
must
set
up
the array
*/
/&%
find
screen width
&/
7%
and height
&/
in mid-screen
%/
133

<!-- source-page: 141 -->
## Page 141

CHAPTER 6
points(2]= scrwt5/@;
points(3]
= scrh&7/8;
vsf_interior (handle,
3);
vef _style(handle,3)3
vsf_color (handle,
GREEN);
v_bar
(handle, points);
/t
initialize
bug creature forms according
to resolution
%/
switch
(work _outfC13])
/&
find
out
how many colors
%/
€
case
2:
inithi();
/*
if
2 colors,
use hi-res
&/
break;
case
4:
initmed();
/%
if
4 colors,
use med-res
%/
break}
case
16:
initlod);
/*&
if
16 colors,
use
lo-res
&/
3
/&
Set
up
one
form using
screen
data,
and
2 using
image data
from
an
array
t/
screen.image
=
GL;
/*
use screen
data
for
this
form
&/
view[91.flag
= viewlil.flag
=
8;
/*
views are ST-specific
form
t/
view([9].planes
= viewl1].planes
=
13;
/%
only
1
plane
%/
/%*
set
initial
locations
for
source
and
dest.
rectangles
&/
points(@i= points(4]
= pointsli]
=
B;
points{[2}= points(6]
= viewl8].width—-1;
points(€3]= viewl@].height-1;
points(3J3= scrhk3/4;
pointel7J=
(scrh83/4)
+ viewl£S).height—-1;
/t
draw the first
bug
in
XOR mode
&/
vrt_cpyfm(handle,3,points,&viewl9],
&screen, colors);
/*
copy
and erase the view forms
to the screen,
alternately using
XOR mode to animate them
%/
for (c#O83ct<scrw/73ct+)
/* repeat
across the screen
%/
for (de@3 d<2;3d++)
7% alternate image each
time
*/
¢
for
(esf;e<1988G;e++);
/%
add
a delay
so
we can
see
*/
Veync ()3
/%
sync
with vertical
retrace
to minimize flicker
%/
7% erase the
last
one
t/
vrt_cpyfm(handle,3,points,&viewld],
&screen,colors) ;
points(41+=3;
/*
move
it horizontally
%/
points(61+=3;
/*
and
draw the next
one
%/
vrt_cpyfmthandle,3,points,&viewl£d*1],
&screen, colors);
+
/*%
end
of
d
loop
&/
}
/t
end
of
c
loop
&/
3
/&
end
of
demo()
&/
7 Support routines
to initialize form data,
depending
on
the resolution
mode
in
effect
t/
initlo()
€
134

<!-- source-page: 142 -->
## Page 142

Drawing and Manipulating Image Blocks
static
int
lo_image(21[46]
=¢{
Ox 8830,
Ox BIB,
OxOOiF,
@xCOFF,
Ox ESES,
Ox 3FE7,
BxO3FF,
@xBOFC,
@x@877,
Ox B38,
Ox GBoe,
Sx 9380,
OxBoea,
Ox 8836,
OxBGiF,
OxSOFF,
Ox @3E3,
@x7FE7,
OxC3FF,
@x@GFC,
@xO077,
Ox GO3a,
@x@e108,
Bn BIAS,
3
8x BCS,
Ox bea,
OxF BOS,
@xFF@S,
@xC7C7,
OxCFFC,
@xFFCS,
@x SFOs,
OxEESS,
@xOCIo,
Ox8o00,
Gx B10,
BxBeee,
Ox bCO8S,
OxFeao,
OxF FO,
@xC7CB8,
@xCFFE,
@xFFC3,
Ox 3FOo,
OxEEQa,
Ox OCB,
Ox ieee,
Ox 6999
Dx BBic,
Ox BOBS,
Ox DOF,
@xCOFF,
Ox 7FEB,
OxO3FF,
Ox OFS,
Ox BOFF,
Ox OB38,
Ox BO3B,
Sx POCW,
Ox@o1C,
Ox @8Ge,
Bx BO3F,
Ox OOFF,
@x 3FEB,
Oxb3FF,
SxCere,
Ox OFF,
Ox @O3a,
Ox @B3B,
@x BBA,
Ox 388s,
Ox bSSe,
OxFCas,
OxFFO3,
@xD7FE,
OxFFCO,
Ox
1 FOS,
OxFFao,
Mx BCWS,
x 8C8O,
OxB32e,
@x3000,
Ox bOO0,
SxFCOS,
OxFFRO,
@xD7FC,
@xFFCS,
@x1F 93,
OxFFOS,
Mx OCWS,
OxSCee,
2x 3899,
Viewl(O].image
= lo_image[@j;
viewlil.image
=
lo_image[1};
viewl(@l].width
= viewLll.width
=
32;
view(@)]. height
= viewL1il).height
=
23;
view£Sl].wordw
= viewLil.wordw
=
2;
3
initmed()
€
static
int
med_image(23(923
=
¢
Sx BSSG,
Gx Boao,
Ox BBOo,
Gx GVWOS,
Ox B92,
@xBOOO,
OxF OOS,
BxF GOS,
OxFCOF,
Bx SFFF,
Ox OFFF,
9x OOOF,
Ox Ger,
Ox BOOS,
Dx GBA,
OxGIOG,
Gx BOG,
Ox OBOe,
Bx BOOS,
Ox SOS,
Gx BOB,
Bx DISS,
OxSOaF,
Ox BOOS,
Ox BAOo,
x BOBO,
Ix GOO,
Ox OF OS,
Ox O3FS,
Bx OSC,
BxBS3C,
Ox OSFF,
Ox OFFF,
OxFFFF,
OxFFFF,
OxFCOF,
@xFCCF,
OxFCSF,
@xFFFF,
OxFFFF,
OxFFCS,
OxFFFS,
OxFFFF,
OxSP3F,
Ox OFOo,
Ox
BF Os,
Ox
OF oa,
@x3C8o,
OxF ooo,
oxCoge,
Ox 9909,
Ox O3Fo,
Ox@F3C,
@xOB3C,
Ox @BFo,
Ox OFCS,
Ox 3CRe,
Ox 3CBB,
@xFFCO,
OxFFEB,
@xFFFF,
OxFFFF,
OxFOSF,
OxF 33F,
OxFOFF,
OxFFFF,
OxFFFF,
@x@3FF,
Ox@FFF,
OxFFFF,
@xFCFC,
Gx OOFe,
Ix GOFS,
Ox OOFG,
OxGO3C,
Sx OOF,
OxBOO3,
Ox 9099,
Ox GFCR,
@x3CFS,
@x3Ce2,
Gx OWBO,
Ox BESO,
@x9eee,
@xGOoe,
@xBOVo,
Ox VIS,
Ox OOF,
OxBOOF,
OxF@SF,
@xFFFC,
@xFFFO,
OxF OSS,
OxF OSS,
@x 06GB,
Ox VOB,
Bx OOOO,
Gx BOO,
Ix GOS,
@x OBB,
Ox GGaG,
@x 98oe,
Ox 2908,
@xF Soo,
Ix BIO,
Ox BOOS,
Ox GOOG,
OxnBooG,
135

<!-- source-page: 143 -->
## Page 143

CHAPTER 6
Ox 2900,
Bx BOI8,
Bx BOOS,
Ox BOOG,
Ox BOF,
@xOFFF,
Ox3FFF,
Ox3COF,
OxF OOF,
BxuF OOS,
ax Baa,
Ox 9806,
Ox B99,
Ox G02,
Bx BOO,
Gx BOs,
Ox BGO,
Ox BOOS,
Bx BAGe,
3;
Dx OSFF,
OxGFFF,
OxFFFF,
@xFFFF,
OxFCOF,
SxFCCF,
OxFC3F,
OxFFFF,
OxFFFF,
OxF FCS,
OxFFFS,
OxFFFF,
Ox3F3F,
Ox OFS,
2x
DF OS,
Ox @Faa,
@xO3C2,
Ox BOF,
@xGO3c,
@xFFC@,
OxFFFS,
OxFFFF,
SxFFFF,
OxFO3F ,
OxF33F,
OxFOFF,
OxFFFF,
OxFFFF,
DrOSFF,
OxGFFF,
OxFFFF,
@xFCFC,
Ox BOFe,
Ox OOFo,
oxGare,
OxO3Co,
Sx
OF Oo,
@x3Caa,
Ox BIDS,
Bx WIAs,
Bx IIIA,
Sx BIO,
Ox FOO,
QxFFFO,
@xFFFC,
SxFOsc,
Ox
OOF,
Ox BOF,
Ox BOOS,
ax 899d,
Ox BIOS,
Gx BBOS,
@x9B9E,
8x 9082,
Sx OOGS,
Px BIW,
Sx B9aa
viewl@J].image
= med_image[9];
viewELil.image
= med_imagel1];
viewl
Si) .width
= viewLil.width
=
64;
viewl(
Ol] height
=
viewLil. height
=
23;
view[9}.wordw
= viewlLiJ.wordw
=
4;
}
inithi ©
€
static
int hi_image(21(@xBS3
=¢{
Ox BBS,
Ox BOOo,
Gx BOIS,
Bx BOBO,
Ox BAO,
Bx BOI,
Bx BDI,
Ox BBS,
Dx B@WOS,
9x BOBO,
Ox BIBS,
Sx BOBS,
oxF ooo,
Ox FSO,
OxF OSS,
OxF IIS,
OxFCOF,
Sx FCOF,
Ox 3FFF,
OxSFFF,
Ox GFFF,
Ox GFFF ,
Ox BOF,
Ox OOF ,
Ox OBOF ,
Ox BOIF ,
Sx OBO,
Ox BBO,
Ox BIBS,
Ox BOIS,
Ox BIOS,
Ix OBOS,
Ox OOOe,
@x Bog,
8x G38S,
Bx BBS,
136
x
OF OO,
Ox
GF ag,
OxO3FS,
Ox O3FS,
SxGO3sc,
@xSO3sc,
Ox PSI3c,
@xOO3IC,
OxO3FF,
Ox@3FF,
Ox OFFF,
OxOFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxFCOF,
@xFCOF,
@xFCCF,
@xFCCF,
SxF CSF,
OxFC3F,
OxFFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxF FCS,
OxFFCS,
OxFFFS,
OxFFFO,
OxEFFF,
OxFFFF,
Ox3F3F,
OxSF3F,
Sx
OF Oo,
OxOF as,
@x BFS,
Ox OOFe,
Ox BFCS,
Sx OFCS,
Ox 3C@O,
8x 3CB6,
Sx ICS,
8x 3cee,
@xFFCS,
SxFFCS,
OxFFFS,
OxFFFS,
@xFFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxuFOsF,
OxFOSF,
OxF33F,
OxF33F,
OxF OFF,
OxFOFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxO3FF,
Ox O3FF,
OxOFFF,
OxOFFF,
OxFFFF,
@xFFFF,
@xFCFC,
@xFCFC,
Ox BVFS,
OxIOFo,
PxrOBOo,
Ox Bae,
Ox B92,
Bx BOSE,
Gx BOWS,
Ox FIIs,
Dux BWOO,
Sx BVO,
Bx DIS,
Bx BIBS,
Ox BSS,
Bx BBS,
Ox DOOr,
Ox BIGF
,
Bx BOSF ,
Ox QGOF
,
OxF OIF,
OxFO3F,
OxFFFC,
@xFFFC,
Ox FFFS,
OxFFFS,
Bx FSIS,
OxF aa,
Bx FOS,
Ox FOSS,
Bx BIS,
Ox DIOS,
Ix BIS,
Bx BOOS,
Ox BIS,
Ox DIS,
Dx BIS,
Ox BOOP,
Bx WIIWS,
Ox BOOS,

<!-- source-page: 144 -->
## Page 144

Drawing and Manipulating Image Blocks
Ox BBOG,
@xGO99,
@x BOBO,
Bx BIBS,
@x9Goe,
Ox 8900,
@xBOOG,
Ox98Go,
Ox GOOF,
OxOOOF,
2x BOOS,
Gx BSS,
Ox 880g,
2x BSS,
Sx OS82,
®xo9ag,
8x oa00,
Ox OOO,
Ox OOO,
Ox BBS,
Ox BOOS,
Ox B929,
Ox 9228S,
2x OO09,
Bx BIBS,
Ox BOIS,
Ox GIar,
OnODOF ,
OxOFFF,
OxOFFF,
Ox3FFF,
Ox3FFF,
Ox 3COF,
Ox 3COF,
OxFQOrF,
OxF OOF,
OxFaas,
Ox
F SOO,
Sx BBO,
Sx BIIS,
ax 0088,
Ox B98,
Ox BOOB,
2x 9BOS,
Ox BIGQ,
Ox BOOS,
2x 9009,
OxGOoo,
Ox BOOS,
8x 9989,
Gx OBOo,
Cxdoee,
Sx SBOO,
Sx BSOe,
Ox BOO,
SxBOOO,
Dx BOOS,
45
Ox
OF ao,
Ox OFag,
Ox GFOS,
OxOFos,
@x3C8¢,
Ox 3C8S,
SxF Ooo,
OxF OOS,
Sx CIO,
Sx CB29,
Ox BBIQo,
Bx 8080,
OxOSFe,
Ox O3Fs,
Sx OF3C,
Ox OF3C,
8x OO3c,
Ox BOSC,
OxO3FF,
OX OSFF,
Sx OFFF,
Sx OFFF,
@xFFFF,
@xF FFF,
OxFFFF,
OxFFFF,
OxFCOF,
OxFCOF,
OxFCCF,
@xFCCF,
@xFCSF,
@xFCSF,
OxFFFF,
OxFFFF,
OxFFFF,
Sx FFFF,
Sx FFCS,
OxFFCS,
OxFFFS,
OxFFFS,
OxFFFF,
OxFFFF,
OxFFFF,
Ox 3F3F,
Ox 3F3F,
Ox OFA,
Ox
OF OS,
BX SFOS,
Sx OF OS,
Ox
OF OO,
Bx
BF BS,
Bx O3CO,
Ox O3CS,
Ox OOF,
Ox BOF,
OxBO3c,
Bx SO3c,
OxOOFa,
Ox BOF,
Ox 9OFa,
Ox 0OFS,
Sx@C3c,
Ox BOSC,
On OWOr,
Bx DIO,
Ox BOOS,
Ox GVO3,
Ox GWOo,
Sx BOSe,
Ox OFCe,
Ox GFCS,
@x3CFO,
Ox 3CrFe,
Ox3Cae,
8x 3C9S,
OxFFCe,
OxFFCO,
OxFFFS,
SxFFFS,
OxFFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxFOSF,
Ox FOF,
OxF33F,
OxF33F,
OxFOFF,
OxFOFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxO3FF,
OxO3FF,
Ox OFFF,
Ox OFFF,
OxFFFF,
OxFFFF,
OxFFFF,
OxFCFC,
@xFCFC,
Ox BOFS,
Ox DOF a,
Ox OOF S,
Ox OOF So,
Ox OFS,
Bx SOFC,
Ox B3ce,
Ox B3Co,
Ox GFao,
Ox OFA,
Ox 3COO,
Sx 309,
Ox BIG,
Ox BSOe,
Ox BOW,
Ox BIAS,
Sx BOBO,
Ox IGG,
Bx BOBS,
Bx SBBS,
OxF ORS,
SxF OOS,
Du BIOS,
Gx BHI,
Bx BSI,
Bx GSAS,
Ox SIO,
Fx BBS,
Ox BIOS,
Fx BIB,
Bx O29,
Dx DSO,
Ix BOI,
Ix SBI,
Bx VWOG,
Ox OS29,
Sx OOo,
Sx 9OSO,
OxF@Ad,
Ox
F S28,
OxFFFA,
OxFFF,
OxFFFC,
OxFFFC,
SxFO3c,
OxFOSc,
OXF OOF,
OxF Or,
Ox OBar,
BK OOO,
Ox IBIAS,
Dx GISS,
Ox GIO,
Sx BOSS,
Bx 9850,
Ox G208,
Bx DDB,
Ox BIO,
OxBIIO,
Bx BOOS,
Ox BIOS,
Ox BOOS,
Bx BIB,
Ox o20e,
Bx PBS,
Gx BOIS,
8x 98S,
Ox BVO,
Gx BOSD
viewl(9l].image
= hi_imagel[@];
viewlLil.image
= hi_image(1};
viewl@).width
= viewLll].width
=
64;
view(@] height
= viewLil. height
=
46;
view @].wordw
= viewli}.wordw
=
4;
3
/&
End
of
Copytran.c
&/
137

<!-- source-page: 145 -->
## Page 145

CHAPTER 6
Raster Operations In BASIC
The original version of ST BASIC did not contain any keyword support for raster operations. The revised version is
slated to include the commands SSHAPE and GSHAPE. These
commands function much like the GET and PUT statements in
Microsoft BASIC. To move an image from the screen to a
memory array, you use the command SSHAPE, whose syntax is
SSHAPE x1,y1;x2,y2, array%()
where x1,y1, and x2,y2 are the coordinates for the top left and
bottom right corners of the image rectangle. The array%() parameter is an integer array that has been DIMensioned so
it is
large enough to contain the image information. For each bit
plane, you'll need one word of data for every 16 bits of width,
times the number of lines of height. Let’s take the example of
a rectangle that goes from 32,56 to 194,98. Since this rectangle
is 163 pixels wide (194—32-+1), the smallest number of words
that can hold a
line of data is 11 (11*16 = 176). There are 43
lines of data (9856+
1), so each bit plane requires 473 words
of data. There are two bit planes in medium-res and four bit
planes in lo-res, so these modes require 946 or 1892 words of
data, respectively. To these size requirements you must add a
few words in which to store the layout of the image. (At the
time of this writing the exact number is not known, but 10
words should give you a comfortable margin.) Remember to
DIMension the array to the correct size before you use SSHAPE.
To copy the image that you’ve saved from the array to
the screen, you must use the GSHAPE command. The syntax
for this command is
GSHAPE x1,y1,array%()
where the point x1,y1 describes the upper left corner of the
image, and array%() is the name of the array that’s used to
store the image. The size of the image is also taken from the
array in which the data is stored.
As with the VDI raster commands, images that are copied
to the screen with GSHAPE may be combined with the existing screen image in several ways. The command used to set
the drawing mode also determines the copy mode for the image. This command is DRAWMODE mode, where mode is a
number from 1
to 4:
138

<!-- source-page: 146 -->
## Page 146

Drawing and Manipulating Image Blocks
Mode ___—i Description
Number
1
Replace
2
Transparent
3
XOR
4
Reverse Transparent
139

<!-- source-page: 147 -->
## Page 147

-_—

<!-- source-page: 148 -->
## Page 148

Chapter 7
Text

<!-- source-page: 150 -->
## Page 150

We normally don’t think of the text that appears on a computer screen as graphics, but there is actually
very little difference between text and any other kind of
graphics that can be displayed on the ST computers. Since the
graphics display is bitmapped, text characters must be drawn
on the screen dot-by-dot, just like any other kind of image.
That’s why the most common kind of text rendering under the
VDI is called graphics text.
You will find that graphics settings like the clipping rectangle and the drawing mode, which apply to all graphics output, affect graphics text just as they do any other drawing
operation. In addition, there is a collection of settings that apply only to graphics text. These allow you to control the color,
typeface, size, rotation, and positioning of graphics text.
There are many advantages to using this system of text
rendering on a computer. Characters may be placed anywhere
on the screen, graphics and text may be mixed freely, and different sizes and styles of lettering may be used at the same
time. It’s even possible to use some of the refinements common to the printing world, like proportional fonts and microspace justification.
There are performance tradeoffs, however, with using a
bitmapped screen for text, rather than a character display. Text
rendering is a bit slower than with a character display, and
may be noticeably slower when a whole screen full of text is
being scrolled, for instance. This is particularly true when the
characters are not positioned so that the image data for each
falls within even byte boundaries, as is the case with a proportional font. When the left half of a character falls within one
byte of screen memory, and the right half within another, the
VDI must shift the image data twice before writing it to the
screen.
Another drawback of the graphics text functions is that,
although they give you complete control over the placement
and appearance of text output, they require you to place each
line of text on the screen individually. Since such complete
143

<!-- source-page: 151 -->
## Page 151

CHAPTER 7
control is not always necessary (or even desirable, given the
performance penalty for text that does not fall within even
byte boundaries), the VDI also provides a more traditional text
mode called alphanumeric mode.
The alphanumeric mode behaves like a conventional text
terminal, in which characters, in a fixed type style and size,
are printed one after the other in fixed positions on the screen.
It allows you to output text conveniently, without worrying
you about all the details of its position and appearance. The
alphanumeric mode also supports many of the features of text
display terminals, such as cursor movement and absolute positioning, reverse video, and selective erasure.
While this book deals only with the VDI functions of the
GEM operating system, you should be aware that other portions of the ST system software also offer text support. The
AES portion of GEM contains some functions that deal with
text manipulation and input, and GEMDOS and the ST BIOS
both contain support for a text console device. C programmers
should note that the standard C text functions such as printf( )
may also be used.
Graphics Text and Text Alignment
The basic function for the display of text is called Text, and it’s
used like this:
int handle, x, y;
char *string;
v_gtext(handle, x, y, string);
where x and y are the text placement coordinates, and string is
a pointer to a null-terminated character string. This is an array
of ASCII character values, ending with a character whose
ASCII value is 0.
Just saying that x and y are the text placement coordinates, however, doesn’t really answer the question of where
the text will appear on the screen.
Since a
line of text may cover an area containing thousands of pixels, we must have some way of determining which
point the placement coordinates describe. The GEM VDI recognizes several parts of the text display as significant, and allows you to align your text display with any of these points.
In order to understand how text alignment works, you
must be familiar with the parts of the character display. Each
144

<!-- source-page: 152 -->
## Page 152

Text
text character occupies a space known as a
cell. This includes
not only the image data for the character, but also some blank
space surrounding the character. The top and bottom of the
cell are delimited by imaginary lines called the top and bottom
lines. Toward the lower part of the cell, there’s an imaginary
line called the baseline. This line marks the bottom of most
characters, such as the letter 0. Some characters, like the letters
p and y, extend below the baseline, down to what is called the
descent line. The upper boundary for most of the lowercase letters is called the half line. The capital letters, and some lowercase letters like b, extend upwards past the half line, to what is
known as the ascent line. Note that there may or may not be
some blank space between the ascent line and top line, or descent line and bottom line, depending on the particular typeface. In the standard Atari system font, for example, characters
extend to the top and the bottom of the cell. The various vertical alignment points are illustrated in Figure 7-1.
Figure 7-1. Vertical Alignment of Text
Aliannent
Alignment
Delta
Delta
“
ony
Top
Line
Ascent
Line
Half
Line
IPaANAIOTO
=D OD
[sven ex
[  4sonez
|
Base
Line
Descent
Line
Bottom
Line
Char.
Width
Cell
_|
Width
Left-
_
Rightjustified
justified
Centered
In addition to the vertical alignment points described
above, a string of text has three significant horizontal alignment points. You may line up the string so that its left side,
right side, or center is even with the text placement point. The
VDI call used to select the horizontal and vertical alignment
points is Set Graphics Text Alignment. The C syntax for this
call is
int handle, halign, valign, hset, vset
vst_alignment(handle, halign, valign, &hset, &vset);
145

<!-- source-page: 153 -->
## Page 153

CHAPTER 7
where halign and valign show the horizontal and vertical
alignment points that you wish to set. Since every device does
not support this type of alignment, the actual alignment points
that were set by the call are returned in the variables hset and
uset. The values in these variables are a numeric code that
specifies the alignment points. For the vertical point, the possible values are:
Number
Description
0
Baseline (default)
Half line
Ascent line
Bottom line
Descent line
Top line
OA PWN
The possible horizontal alignment points are:
Number
Description
0
Left justified (default)
1
Centered
2
Right justified
By default, when you specify an x and y position for text
in your v_gtext( ) call, that point defines the baseline position
for the left side of the first character in your string. If the
alignment is changed, however, that point can just as well
specify the top right corner of the last character in the string,
or the half line of the center of the string. Program 7-1 shows
the effect of the alignment settings on text placement. It draws
a horizontal and vertical line, and shows the possible placement of text strings whose placement coordinates are the same
as those of the lines.
Program 7-1. align.c
/ERKCTEETETACTRSKA
TEETER EKER
SEE ERE REE ER EEE EES
/t
%/
‘t
s
/t
ALIGN.C
-- Demonstrates alignment
s/
/%
of
graphics text
strings.
x/
/t
‘/
t
%/
/&
“/
/ECTATAEKATATAEKKESATAATAKKACARASESAEASEK
ATES
#include
“shell.c"
char
thstringli=
‘
"Left
justified",
"Centered",
“Right Justified"
146

<!-- source-page: 154 -->
## Page 154

Text
3
char tvstringl
I=
€
"Base",
“Half*,
"Ascent",
"Bottom",
"Descent",
"Top"
4
demo ()
¢
int
c,
xmax , yaax,x, y, dx, dy, hset, vaeet, points(S]};
xmax
= work _outC@];
/% screen width
&/
ymax
= work_outf€il;
/&
screen height
%/
dy= (ymax +1) /2582;
/¢t
line height
&/
y=323
x=";
/&
set default
x
and
y
%/
for
(c=O3c<33c++)
/&
for
each horizontal
position
%/
€
/& Change Horiz.
alignment
and print
text
&/
vet_alignment (handle,c,@, &hset, &vset)
v_gtext (handle, xmax/2, yt=dy,hatring(c1);
?
for
(c=O3c<63c++)
/&
for
each vertical
position
&/
€
7% Change Vert.
alignment
and print
text
%/
vst alignment (handie,9,c,
&hset, &vseet);
v_gtext (handle, x, ymax%3/4, vatring(<o1)3
/*%
add
string
length
to
x
position
&/
vqt_extent
(handle, vstring(cl, points) 3
x+=(points[2]+8) ;
3
vsl_color (handle, 2);
/&
Draw vertical
alignment
line
&/
pointsl1I=points(TJ=ymaxt3/4)3
points(81=9;
points(2]=x+16;
v_plinethandle,2,points))
/%
Draw horizontal
alignment
line
%/
points(@]=points(2]=xmax/2}3
points{£1J=9;
points(3)]=y+16;
vipline (handle, 2,points);
3
/&%
End
of
Align.c
t/
Microspace Justification
Some word processors allow you to stretch out a line of text to
fill a certain line length on the paper by adding (or removing)
minute spaces between characters or words. This feature, often
referred to as microspace justification, is one of the more sophisticated text functions offered by the VDI. The name of this
147

<!-- source-page: 155 -->
## Page 155

CHAPTER 7
function is Justified Graphics Text, and its calling sequence is
as follows:
int x, y, length, word_space, char_space;
char *space;
v_justified(handle, x, y, string, length, word_space, char_space);
The string parameter points to the null-terminated character string to be printed, and the x and y parameters specify the
display location, just as with the v_gtext( ) call. The length
value specifies the size of the screen area used to display the
text string (in whichever coordinate system, raster or normalized, that’s currently in use). The final two parameters,
word_space and char_space, are flags that tell the function
how to manipulate the string to achieve the desired length.
The v_justified function can adjust the space between characters in a word, the space between words in a
line, or both.
Setting either of the flags to
1 tells the function to adjust the
spacing between the elements named, while setting either to 0
means that the spacing will not be affected for that element. If
both of these values are set to 0, no justification is performed,
and the text string is printed with the same spacing as would
be used by v_gtext( ).
An example of justified text can be found in Program 7-2,
rotext.c, in the section on rotated text, below.
Sizing a Text String
When printing graphics text, the programmer has total responsibility for the placement of the string. One of these duties includes making sure that the text string fits on the display
screen. In order to do this, however, you must know how
much size the text will occupy on the display. With monospaced fonts (like the standard ST font), each character cell is
the same width, so you can multiply the width of each character by the number of characters to find out the total length of
the string.
But GEM provides for proportionally spaced fonts as well.
In a proportionally spaced font, a wide letter like the w occupies a wider cell than a narrow letter like the
I, so there isn’t a
lot of extra white space on either side of the narrow letter.
While this will make the text look more attractive, it makes it
much harder to keep track of the overall length of the string.
148

<!-- source-page: 156 -->
## Page 156

Text
The VDI does supply a function that lets you discover the
the width of a particular character. It’s called Inquire Character
Cell Width, and its calling sequence goes like this:
int handle, char, cellw, ldelta, rdelta,status;
status = vqt_width(handle, char, &cellw, &ldelta, &rdelta);
where char is the ASCII value of the character in question, and
cellw is the variable in which the width of the character cell
(including spacing to the left and right of the character) is returned. The width of the blank space to the left and right of
the character within the cell is stored in the variables Idelta
and rdelta, Note that the width returned by this function does
not account for any space added to the character because of
special effects. Another function, vqt_fontinfo( ), returns information about the change in character width caused by special
effects. Figure 7-1 shows the parts of the character cell.
Though it’s possible to figure out the width of the line by
adding the widths of the individual characters, there’s an easier way to find it. The VDI provides a function which returns
the size that a given text string drawn in the current font
would occupy. This function is Inquire Text Extent. It’s used
like this:
int handle, points[8];
char *string;
vqt_extent(handle, string, points);
where string is a pointer to a null-terminated text string, and
points is a pointer to an array which holds the coordinates for
the four corner points of the smallest box that completely contains the text string. The first two elements give the x and y
coordinates of the lower left corner of the text box.
The next two elements give the coordinates of the lower
right corner. The third pair gives the location of the upper
right corner. The last two give the x and y position of the upper left corner of the text box. When we refer to the lower left
corner of the text box, we mean relative to a horizontal line of
text. The reason that the VDI specifies all four corner points
(instead of just two opposite corners, like most other graphics
functions using rectangular areas) is that GEM provides for the
display of text that has been rotated at angles other than right
angles (though on the ST, only 90-degree rotation is supported).
149

<!-- source-page: 157 -->
## Page 157

CHAPTER 7
Regardless of whether the virtual workstation uses raster
or normalized coordinates, the points of the text box are given
_
in a coordinate system which, like the normalized coordinate
system, has it origin in the lower left corner. A text string that
has not been rotated has its lower left corner (point 1) at the
~
origin. One that has been rotated 90 degrees has its upper left
corner (point 4) at the origin. Figure 7-2 shows the reference
points described by the vqt_extent(
) function.
—_
Figure 7-2. Rotating Text
2
vaJ6a
3
4
With the first version of the TOS ROMs, when the text
string is rotated 270 degrees, the coordinates for the first point
(point[0] and point[1}) are not returned correctly by this function. Since the text box is always at right angles on the ST,
_
however, you can use points 2 and 4 to describe the four sides
of the text box.
Character Rotation
As we've mentioned before, one of the text settings that the
VDI supports is character rotation. The full name of the VDI
function is Set Character Baseline Vector. Normally the baseline for a character is horizontal, and extends from left to right.
Another way of saying this is that the baseline vector is zero
degrees. But GEM provides for rotation of the baseline as well.
150
_

<!-- source-page: 158 -->
## Page 158

Text
In the case of the ST screen display, this rotation is in 90-
degree increments only. This means that besides displaying
the text normally, you can display text sideways or upside
down and backwards as well. The syntax for the call used to
make this setting is
int handle, angle, angle_set;
angle_set = vst_rotation(handle, angle);
where angle is the angle requested. Since not every angle is
supported (on the ST screen, only even multiples of 90 degrees are available), the function returns the angle that was actually set in the variable angle_set. Remember, the VDI
expresses angles in tenths of a degree (0-3600), starting with
the rightmost point on the circle and moving counterclockwise.
Program 7-2 displays four text strings, rotated at right angles to one another. It also shows an example of justified text.
Since pixels on the color screen tend to be taller than they are
wide, particularly in medium-resolution mode, somewhat narrower spacing makes the text look more natural when turned
sideways. The program also uses the vqt_extent function to
determine the normal length of the string in order to shorten it
somewhat.
Program 7-2. rotext.c
/EREATAATAATTAAAAATS
SASH AASATTARAAEREREE REESE /
/%
&/
/t
“/
/t
ROTEXT.C
-- Demonstrates rotation
x/
/%
of
graphics text
strings.
x/
/&
%s
‘t
a/
/t
a/
/EREREAEKESAATARS
TERCERA SERRE ETRE REE EES /
#include
"shell.c"
demo ()
€
int midh,midv,len,box(@1;
midh
=
work _out£91/23
midv
= work_outli11/2;
vigtext (handle, midh+8,midv,"2 Degrae Rotation”);
vst_color (handle, 4)3
vet_rotation (handle, 1898);
v_gtext (handle, midh—-8,midv,"188 Degree Rotation");
vst _color (handle,3);
vst_rotation (handle, 989);
151

<!-- source-page: 159 -->
## Page 159

CHAPTER 7
vat_extent (handle, "98 Degree" ,box) 3;
len
= box(3]-8;
v_justified
(handle, midh,midv—146,"99 Degree",len,i,1)3
vet_color (handle, 2);
vst_rotation (handle, 278) ;
vqt_extent (handle, "278
Degree", box);
len
= boxl463-8;
v_justi fied (handle, midh,midv+i6é,
"2798 Degree",len,1,1)3
3
/%
End
of
Rotext.c
&/
Text Color
Just as with lines, markers, and filled shapes, graphics text has
it own individually selectable color setting. The text color default is determined by the value placed in work_in[6] when
the virtual workstation is open (which defaults to color 1,
black, if the GDOS extension is not loaded). Afterwards, you
may change the color index with the function Set Graphic
Text Color Index, whose format is
int handle, pen, pen_set;
pen_set = vst_color(handle, pen);
where pen is the VDI pen color (color index) requested. Since
each resolution mode has a different number of pens available, not every pen can be selected from every mode. Therefore, the function returns the number of the pen that was
actually set in the variable pen_-set.
Special Effects
Another feature that the VDI has borrowed from the word
processing and printing fields is called special effects. These
days, most word processing programs allow you to add emphasis to certain parts of your text by making characters appear in boldface, italics, or underlined type. In the same
manner, the VDI can alter the image data of text characters according to a mathematical formula in order to change their appearance. The effects supported are Thickened characters
(boldface), Light text (such as you see in a menu item that’s
been grayed out), Skewed text (italic)
, Underlined text, and
Outlined Characters. These effects may be used individually or
combined with one another. Since the new characters are altered versions of the originals, they may not always be as legi-
152
—

<!-- source-page: 160 -->
## Page 160

Text
ble. Also, you should keep in mind that adding effects can
change the width spacing of characters. For this reason, you
should try to print a whole line of text at a time if you’re
using special effects, so the VDI can adjust the spacing. Otherwise, you may find that the new text that you put down
erases part of the existing text.
The function used to make these changes to the standard
character set is called Set Graphic Text Special Effects. The C
syntax for this call is
int handle, effects, effects_set;
effects_set = vst_effects(handle, effects);
where effects is a flag byte showing which of five different effects are set on or off. (GEM actually provides for six effects,
but only five are supported on the ST display.) Because not
every effect is available on every device, the function returns
the settings it actually puts into effect in the variable
effects_set.
The effects flag byte has six significant bits (five on the
ST), each of which controls a different effect. For example, the
first bit, Thickened, controls whether or not text will be
printed in boldface. The decimal value of the first bit (bit 0) is
1, so adding a
1
to the effects flag turns on bold printing.
Since each effect has a different bit, the effects can be easily added to one another. For example, an effects value of 9
means that both underlining (8) and boldface (1) are turned
on. Of course, the VDI manipulates the character image each
time it adds an effect, so too many effects may detract from
the appearance of your text. The effects that are controlled by
the various flag bits are described in the chart below.
Value
Effect
1
Thickened (bold)
2
Light intensity (grayed or ghosted)
4
Skewed (italicized)
8
Underlined
16
Outlined
32
Shadowed (not available on ST)
As we mentioned above, adding special effects to a text
font can change the width of the characters. Most of the functions that give you information about the width of the characters in the current font do not take special effects into account.
To find out how the width of the current font has been altered
unRwnrok
153

<!-- source-page: 161 -->
## Page 161

CHAPTER 7
by special effects, use the vq_fontinfo function, which is detailed a bit later on in the chapter.
Program 7-3 demonstrates the use of special effects with
graphics text. It produces two columns of text, one of which
shows each effect separately, and one of which shows each
new effect added to the previous ones.
Program 7-3. effects.c
/ERTEEARTATATAAR
ATA TAAET AAAS LAER
AREER AES /
‘*
&/
/t
a/
/t
EFFECTS.C
-- Demonstrates graphics
s/
/%
text
special
effects.
“/
/t
%/
/t
x/
/t
a/
/ESEATTKTATEAK ERECTA S TARE REET EES
#include
"shell.c"
#define vqt_fontinfo vqt_font_info
/&
for
Megamax
only!!!
8/
char
&string(li=
€
"Thickened",
"Lightened",
"Skewed",
“Underlined”,
"Qutlined”
3
demo()
€
int
c, maxc,minc,
nul height,
y=24,effectse=¢,distances(5]};
/&
find
out
default
font
height
and double
it
8/
vat_fontinfo (handle, &minc, &maxc, distances, &nul ,&mul)}
height=2tdistances[41+1;
vst_height (handle,
height,
&nul,
&nul,
&mul,
&nul)y;
/% Print
two columns
of
plain
text
&/
v_gtext (handle, 16, y+=(height+=8),"Plain")s
vigtext (handle, 188,y,"Plain"),;
for
(c=®yc<Spco++)
/&
for
each horizontal
position
&/
€
/%
show each effect separately
%/
vst_effects (handle, 1<<c)}
vst_color (handle,ct+1)3
v_gtext (handle, 16, y+=height, string£c]);
/%t
show each effect
added
to the
last
%/
vst_effects
(handle, effaectst=(1<<c))})
vst_color (handla,c+i);
vigtext (handie, 188, y,string£o1);
3
}
/& End
of
Effects.c
4/
154

<!-- source-page: 162 -->
## Page 162

Text
Setting Character Height
One of the most significant variables that you can change
through the text settings is the size of the text characters. The
default character set on the ST may be printed in any one of
six sizes, and additional disk-based fonts come in many sizes
as well. You'll find that the VDI scales up each character set,
so that it can print in both the original size and a version
that’s twice as large.
The VDI function that is used to change the size of the
current text font measures font size in terms of the height of
each character. This height is determined in one of two ways.
The first is in absolute pixel height, as measured by the current raster or normalized coordinate system. The VDI function
used to set character size on this basis is called Set Character
Height, Absolute Mode. This function is called by a C program like this:
int handle, height, char_width, char_height,
cell_width, cell_height;
vst_height(handle, height, &char_width, &char_height,
&cell_width, &cell_height);
where height is the pixel height of the character set, as measured from the baseline to the top of the character cell.
If the character height that you request isn’t available, the
VDI sets the next smallest available height. The height of the
actual character font that was set is returned in the variable
char_height, and the height of the entire character cell for that
font is returned in the variable cell_height. Likewise, the width
of the font that was set is returned in char_width, and the
width of the character cell is returned in cell_width. For
monospaced fonts, the widths returned apply to every character in the set. For proportional fonts, the character and cell
widths returned are those of the widest character in the set.
The VDI also allows you to set the character height in
terms of printer points. The point is
a common measurement
of the height of type fonts, and is equal to 1/72 inch. When
point sizes are used to set the character height, the height of
the entire cell is measured, not just that of the character. The
function used to set character height on the basis of point size
is called Set Character Cell Height, Points Mode. Its C syntax
looks like this:
155

<!-- source-page: 163 -->
## Page 163

CHAPTER 7
int handle, point, char_height, char_width,
cell_height, cell_width, point_set;
point_set = vst_point(handle, point, &char_width,
&char_height, &cell_width, &cell_height);
where point is the point size of the character font requested.
This function, like the absolute mode function, returns the size
of the character and the character cell in pixel units on the
correct coordinate scale. These measurements are returned in
the variables char_height, char_width, cell_height, and
cell_width. If the function is unable to set a font of the size requested, it sets the next smallest available font size. The point
size of the font that was actually set is returned in the variable
point_set.
On the ST, the default system font may be printed in the
following sizes:
Points
Char_height
Char_width
Cell_height
Cell_Width
20
27
14
32
16
18
13
14
16
16
16
9
10
12
12
10
13
7
16
8
9
6
7
8
8
8
4
5
6
6
The three larger fonts are just enlargements of the three
smaller fonts. The ten-point font (16 X 8
cell) is the default
font on the monochrome screen, while the nine-point font (8
X
8 cell) is the default for both color modes. The eight-point
font (6 X 6
cell) is used for the lettering that appears under
icons on the GEM Desktop.
Using Disk-Based Fonts
One of the most important features added by the GDOS extensions that you load by running GDOS.PRG is the ability to
use disk-based fonts in addition to the normal system font. In
order to access these fonts, several requirements must be met.
First, the GDOS extensions must be loaded. (A message like
Atari GDOS ver. 1.1 resident will appear on the screen if the
GDOS has been successfully loaded.) Next, there must be one
or more font files on the disk from which you load the GDOS
(typically the disk that you boot up with runs this program
from the AUTO folder). These font files may be included with
156
—

<!-- source-page: 164 -->
## Page 164

Text
software that you have purchased, or you may create them
yourself with a font-creation program like the one supplied
with DEGAS Elite. Finally, your startup disk must have a
file in
the root directory called assign.sys. This file lists the filename
of each font that’s available for each screen resolution mode.
Complete details of the format of this assign.sys file appear in
Chapter 2.
Once these three conditions have been met, you may load
the additional fonts from disk with the call Load Fonts. Keep
in mind that fonts take up a certain amount of memory space,
and that if you load several sizes of a given font, particularly
large sizes, that font may occupy as much as 32K of memory
or more. You call Load Fonts like this:
int handle, select, fonts_added;
fonts_added = vst_load_fonts(handle, select);
The select parameter is reserved for future use, and should
be set to 0. Currently, it’s not possible to select which fonts
you wish to load—it’s an all-or-nothing proposition. When
you use the vst_load_fonts() function, all of the fonts that are
specified in the assign.sys file for use by the device pointed to
by handle are loaded in at once. The number of additional
fonts that have been made available to the system is returned
in the variable fonts_added. If fonts have already been loaded,
nothing will happen if you try to load them again during the
execution of the same application, and a 0 will be returned in
fonts_added.
Once you’ve loaded the disk-based fonts, you’ll naturally
want to know which ones are available. The VDI function Inquire Face Name and Index returns information about a font’s
name and ID number. The format for this function is
int handle, font_num, font_id;
char name{32];
font_id = vqt_name(handle, font_num, name);
where font_num is a number that’s assigned to each font when
it is loaded into the system. Since the system font reserves for
itself font_num 1 (and font_id 1), numbering of disk-based
fonts begins with 2. The variable fonts_added contains the total number of fonts loaded by the vst_load_fonts( ) call, so
the number that you pass in font_num should always be a
value between 1 and fonts_added +
1. Two items of information are returned by this function. The first is the name of
157

<!-- source-page: 165 -->
## Page 165

CHAPTER 7
the font, which is returned in the string pointed to by name.
This string contains
a maximum of 32 ASCII characters, the
first 16 of which contain the name of the font, and the last 16
of which contain a modifier that describes the style and thickness of the characters. The other item is the font ID number.
This is an identifier which is contained in the first two bytes of
the font file, and which should be unique for every font
named in your assign.sys file. You will need to know this
number in order to set this font as the current typeface.
Set Text Face
Once you know the name and font IDs of all of the available
fonts, you may set one of them as the current text font. The
VDI call used for this function is Set Text Face, and it’s called
like this:
int handle, font—id, font_set;
font_set = vst_font(handle, font_id);
where font_id is the unique number contained in the first two
bytes of the font file, which identifies this font. If the system
can’t load the font number that you requested, you can find
out about it by checking the variable font_set, in which the
font_id number of the text font that was actually set is
returned.
Unload Fonts
If you’ve used the vst_load_fonts function to load in a number of disk-based fonts, you should call the Unload Fonts
function before your program ends, to let the VDI know that
you are no longer using them. If you don’t, the system may
crash when the next application tries to load them. It may also
be desirable at times to call this function before the program
ends, since if no other process (like a desk accessory) is using
the fonts, the VDI frees up the memory that the software fonts
occupied. The Unload Fonts function may be called like this:
int handle, select;
vst_unload_fonts(handle, select);
where the select parameter should be set to 0. At some point
in the future, this parameter may be used to selectively unload
fonts, but, for now, all fonts are unloaded at the same time,
just as they are all loaded at the same time.
158

<!-- source-page: 166 -->
## Page 166

Text
Program 7-4 shows all of the text fonts available in the
system, in all of the point sizes. (This program requires that
gdos.prog and assign.sys be present; see above and chapter 2
for more details.)
Program 7-4, diskfont.c
/ERKEREARETEKE
SEATS
EEE R EERE E TERETE EER EES /
/*%
a/
/t
s/
/%
DISKFONT.C
-~ Demonstrates use
of
x/
/t
additional
text
fonts
loaded
from
a/
st
disk.
«/
/*
x/
/ERSTRETEEKATASERSAAASERE
ARTES KA AREER EEE EE EEE S
#include <osbind.h>
/* Global
variables
--
For
VDI
bindings,
etc.
&/
int contrili2i,
intin£1261,
ptsin(1283,
intout£128),
Ptsoutli26);
int handle;
int work_in(12],
work _outlS7];
/*
Initialization
starts here
«&/
main()
€
int
x,
nul,
button=¢,
addfonts,c,d,id,askd,recd,y,
charh, charw,cellh,cellw,
points(4];
char name(32],
string(6@i;
/&t
Initialize the GEM application
%/
appl_init4);
/&
Initialize
input
array,
get
the physical
workstation handle,
and
open
the Virtual
Screen Workstation
*/
for
(x=1,
work_inliOJ=2s
x<193;
work_inlx++J=1)35
work_in€®J]=Getrez
()+2;
handle
= graf_handle(&nul,
&nmul,
&nul,
&nuUl)3;
vVopnvwk
(work_in,
&handle,
work_out);
v_clrwk (handle) 3
/*%
Set Clipping Rectangle
%/
points(9IJ=pointsl11=9;
Points(2)=work_out(@1;
pointsl3I=work_out(l1];
ve_clip (handlie,1i,points) ;
/*
Load
fonts
and
display
each point
size
t/
159

<!-- source-page: 167 -->
## Page 167

CHAPTER 7
addfonts
= vst_load_fonts(handle,9@);
for
(c=isc<addfonts+2;c++)
€
id
= vqt_name(handle,c,name) ;
Print# ("\OS3SE\O33b1%d
system font(s),
%d
disk
fonts\n",
work_outli9), addfonts) ;
printf ("\Font
%d,
°%s’,
ID
= ZANDISb3\N",c, name, id);
recd=999;
askd™=i988;
y=24;
vat_font (handle,id);
while (askd>srecd)
€
askd=recd—1;
recd=vst _point (handle, askd, &charw, &charh, &cellw, &celih);
yt= (charh+8) 3
sprintf (string, "%d
PTS.
%dx%d
CHAR
%dx%d
CELL",
recd,charw, charh,cellw,celih);
if
(askd>=recd) v_gtext (handle,9,y, string);
3
7*%
wait
until
user
clicks the mouse button
*/
while (button==9) vq_mouse (handle, &button, &nul,&nul);
for (d=9; d< 39890; d++) button=8;
3
/&
Unload
fonts,
close the virtual
workstation,
and
exit
from the application
&/
vst_unload_fonts(handle,@);
v_clsvwk (handle);
appl
_ exit;
3
/&
end
of
Diskfont.c
&/
Text Face Information and Text Setting
A couple of inquiry functions round out the set of VDI text
functions. The first is called Inquire Current Face Information,
and it supplies information about the current text font, such as
the minimum and maximum values of the ASCII characters
for which there is image data, the maximum character width,
the number of pixels added to that width by special effects,
and the spacing between the various vertical alignment points
(bottom, descent line, baseline, half line, ascent line, and top).
The format for this call is
int handle, minc, maxc, maxwidth,
effects[3], distances[5];
vqt_fontinfo(handle, &minc, &maxc, distances,
maxwidth, effects);
160

<!-- source-page: 168 -->
## Page 168

Text
Note that in early versions of the bindings, this function is
incorrectly referred to as vqt_font_info( ). In particular,
Megamax C owners may discover that the linker can’t find the
function vqt_fontinfo( ). If this is the case, you use the
statement
#define vqt_fontinfo vqt_font_info
at the beginning of the program, as was done in Program 7-3,
effects.c, above. Corrected versions of the bindings should be
available from Megamax, as well.
This call returns the ASCII value of the first character for
which there is image data in the character set in the variable
minc, and the ASCII value of the last character in maxc. The
variable maxwidth holds the maximum cell width, special effects not included. The effects array contains information about
the adjustments that you must make to the character width to
compensate for the current special effects. The contents of this
array are interpreted as follows:
Element
Description
0
Total increase in character width due to effects
1
Left offset
2
Right offset
Figure 7-3. Right and Left Offset of Characters with Effects
wae
Left Offset
Right Offset
161

<!-- source-page: 169 -->
## Page 169

CHAPTER 7
The distances array contains information about the distances of the various vertical alignment points from the baseline. The organization of this array is shown below.
Element
Description
Bottom line to baseline
Descent line to baseline
Half line to baseline
Ascent line to baseline
Top line to baseline
PON
©
The other inquiry function is called Inquire Current
Graphic Text Attributes. It returns a wide variety of information about the current graphics text settings. This function
is called as follows:
int handle, attributes[10];
vqt_attributes(handle, attributes);
where attributes is a pointer to an array of integers. The contents of that array is as follows:
Element
Description
0
Current text face
Text pen color
Angle of rotation (0-2700)
Horizontal alignment
Vertical alignment
Writing mode
Character width (in pixels)
Character height (in pixels)
Cell width (in pixels)
Cell height (in pixels)
WOON
AGT
WN re
Escapes and Alphanumeric Mode
The Escape function is used to access those capabilities of an
output device which are peculiar to that device. In the case of
the screen device, one of these capabilities is to print text in
what is known as alphanumeric mode. This mode emulates
the old-fashioned alphanumeric terminal display by dividing
the screen into 25 imaginary rows and 80 imaginary columns
(40 in lo res). These rows and columns define cells into which
a text character may be placed. The alpha text functions ignore
all of the current graphics text settings, and print characters
only in the default size of the system text font, with no special
effects, and no baseline rotation.
162

<!-- source-page: 170 -->
## Page 170

Text
In alpha mode, a visible text cursor appears on the screen
as a solid blinking box which marks the cell in which the next
text character will be written. All of the normal rules of screen
display scrolling apply. When a character is written to the last
column in a row, the cursor moves down to the first column
of the next row. (This wrap-around feature does not work correctly on 40-column screens.) When a character is written to
the last column in the bottom row, all of the lines are scrolled
up, and the cursor moves the first column of the blank line
.
that’s inserted at the bottom of the page.
Some computers have separate graphics and character display modes. If you wish to use alphanumeric mode output
with such computers, you must first switch their screen displays to character mode. The VDI function call used for this
purpose is Enter Alpha Mode. The format for calling this function is
int handle;
v—enter_cur(handle);
On the ST, there is only one display “mode’’—bitmapped
graphics in varying resolutions. Therefore, graphics text and
alphanumeric text may be mixed on the same display, and you
aren't required to set alpha mode with the v_enter_cur( ) call
before using the alphanumeric output function. You may wish
to do so, however, because this call clears the screen and turns
on the text cursor, two functions which would otherwise have
to be performed separately. The VDI also provides an Exit Alpha Mode command, whose syntax is
int handle ;
v—exit_cur(handle);
On the ST, this call clears the screen and turns off the text
cursor. If you don’t use this command before your program
exits, at least turn off the cursor, or else you'll see it flashing
on the Desktop.
The sole means of writing text to the screen in alphanumeric mode is a function called Output Cursor Addressable
Text. The v_curtext(
) function outputs text relative to the current cursor position, and wraps text from the end of one line
to the beginning of the next. The format for this call is
int handle;
char ‘string;
v—curtext(handle, string);
163

<!-- source-page: 171 -->
## Page 171

CHAPTER 7
where string is a pointer to a null-terminated string of text
characters.
Cursor Movement Functions
Since alpha text is output relative to the current cursor position, the VDI provides a number of functions that may be
used to change this position. The most powerful of these is
Direct Cursor Address, which allows you to position the
cursor at an absolute row and column position on the screen.
The way you call this function is
int handle, row, column;
vs—_curaddress(handle, row, column);
where row is
a row number from
1 to 25, and column is a column number from
1 to 80 (40 for low resolution). Any number outside the range of the cursor will set the cursor at the
available position closest to that number. Setting the cursor to
the top left position on the screen is a special case that gets its
own function. It’s called Home Cursor, and looks like this:
int handle;
v—curhome(handle);
In addition to absolute cursor positioning, you may move
the cursor relative to its current position in any direction with
the calls Cursor Up, Cursor Down, Cursor Right, and Cursor
Left. These calls look like the following:
int handle;
v—curup(handle);
v__curdown(handle);
v—curright(handle);
v—curleft(handle);
Finally, the VDI provides a call which your program can
use to discover the current cursor position. It’s called Inquire
Current Alpha Cursor Address, and is called like this
int handle, row, column;
vq—curaddress(handle, &row, &column);
where row and column are the variables in which the cursor
position is returned.
164

<!-- source-page: 172 -->
## Page 172

Text
Other Alphanumeric Text Functions
In addition to cursor-positioning commands, the VDI provides
a few other miscellaneous alphanumeric text commands.
These include two commands to erase text from the current
cursor position to the end of the line, or to the end of the
screen. These calls are Erase to End of Line, and Erase to End
of Screen, and their syntax is
int handle;
v—eeol(handle);
v—eeos(handle);
The VDI also provides for inverse video, in which the
foreground and background colors of the text are reversed. To
start printing in inverse video, the call is Reverse Video On,
and to resume normal printing, the call is Reverse Video Off.
The functions look like this:
int handle;
v_rvon(handle);
v_tvoff(handle);
The last of the VDI alpha text functions is called Inquire
Addressable Character Cells. When GEM is used on systems
where the screen format is unknown, this function allows you
to find out how may rows and columns are available. Its C
syntax is
int handle, rows, columns;
vq—chcelis(handle, &rows, &columns);
Terminal Emulation Functions
Unlike graphics text, which will output any character for
which there is image data, alphanumeric text emulates a display terminal, and treats the ASCII characters from 0 to 31 as
nonprinting control characters. This means that it will interpret
the ASCII character 13 as a carriage return, an instruction to
move the cursor to the beginning of the line, rather than as a
character that should be printed. On the ST system, the BIOS
console device emulates
a DEC VT-52 terminal. Since this is
the device that’s used for alphanumeric mode text, you'll find
that the strings output by v_curtext(
) respond to VT-52 escape codes, as well as the VDI control functions. These escape
165

<!-- source-page: 173 -->
## Page 173

CHAPTER 7
sequences are codes that begin with the ASCII character 27
(ESC), followed by one or more text characters. The VT-52
codes to which v_curtext( ) responds are
ESC A
ESC B
ESC C
ESC D
ESC E
ESC H
ESC
I
ESC J
ESC K
ESC L
ESC M
ESC Y
(row + 32)
(column + 32)
ESC b
(register)
ESC ¢
(register)
ESC d
ESC e
ESC f
ESC
j
ESC k
ESC 1
ESC o
ESC p
ESC q
ESC v
ESC w
Cursor Up
Cursor Down
Cursor Right
Cursor Left
Clear Screen and Home Cursor
Home Cursor
Cursor Up (scrolls screen down if at top line)
Clear to End of Screen
Clear to End of Line
Insert Line
Delete Line
Position Cursor at Row, Column (starts with 0)
Select Foreground (Character) Color
Select Background Color
Clear to Beginning of Screen
Cursor On
Cursor Off
Save Cursor Position
Move Cursor to Saved Position
Clear line
Clear from Beginning of Line
Reverse Video On
Reverse Video Off
Line Wrap On
Line Wrap Off
In addition to the escape codes, the ST terminal emulation
also responds to the following ASCII control codes:
-
08
Backspace
09
Tab
10-12
Linefeed
13
Carriage Return
166

<!-- source-page: 174 -->
## Page 174

Text
Program 7-5 shows the various features of alphanumeric
text mode.
Program 7-5. alphmode.c
/EREKKEKERTASAE
AREER RELEASE KERR
RE EEE /
/t%
x/
/%
ALPHMODE.C
-- Demonstrates
the alpha-
a/
/%
numeric
“Escape”
text
mode.
/
/*t
x/
/t
a/
/RSTTECATATA TARA TAKERS TAKA
EERE ESS
#include
"shell.c"
demo
()
€
int
rows,
columns,
nul,
button=03
vienter_cur (handle);
/*
clear
screen
and
turn
on cursor
%/
vicurtext
(handle,
"This
is
a test");
/*%
move cursor
to
19,18,
turn reverse video
on,
and print
«£/
vs_curaddress (handle, 10,19);
viurvon (handle);
vicurtext
(handle,
"\This
is
inverse video\r\n");
virvoff (handle);
/*
Show how text
wraps around
to the next
line
%/
vicurtext
(handle,
"This
is
the next
line.
It
is
a very
long
line.
Far
too
long
to appear
on
one
line.
Don’t
you think?")3;
/*
Mix
in
some graphic
text
to show
that
you can
£/
vst_rotation (handle, 188@);
v_gtext (handle,
508,58, ""This
is gtext\n\8s3p");
/*
Show that v_gtext()
doesn’t
move the cursor
%/
vicurtext
(handle,
"
The cursor
doesn’t
move. ")5
/%
Show VT-52 commands
%/
vicurtext (handle,
"\@33B\933BWe also obey VT-52 commands\r\n");
v_curtext (handle,
"Including\@33b2foreground
and
\@3Scibackground color \833b3\G33cH") ;
7%
Show number
of
cells using
C function printf)
&/
vqg_chcellsthandle,
&rows,
&columns);
printf ("\r\n\nRows=%d,
Columns=%d\n", rows, columns)
3
while (button==9) vq_mouse (handle, &button, &nul, &nul)
3
v_exit_cur (handle);
}
/*%
End
of
Alphmode.c
%&/
167

<!-- source-page: 175 -->
## Page 175

CHAPTER 7
BASIC Text Functions
ST BASIC supports the traditional BASIC text output function,
PRINT. It also includes the command GOTOXY, which is used
to position text in the output window. The only one of the
VDI text commands that is supported directly by BASIC is
vst_color( ). The text color is set by the first parameter of the
COLOR command.
It is possible to control the text settings by making direct
calls to the appropriate VDI functions. Since PRINT calls
v—gtext( ) to do the actual printing, these settings will affect
PRINTed text. You should note, however, that these settings
may not work properly with the PRINT function. Take the
case shown in Program 7-6.
Note that after the baseline has been rotated, the text
printed with v_gtext( ) is displayed upside down with characters going from right to left. But the PRINTed text is upside
down, with the characters going from left to right as usual.
That's because PRINT outputs each character in the text string
separately with v_gtext( ), as a one-character string, positioning each one to the right of the previous one. Another result
of this can be seen in the part of the program that PRINTs a
text string after the character height has been increased. The
large characters are written so closely together that they partially cover each other. That’s because BASIC writes out one
character at a time and spaces them as it would small characters, since PRINT doesn’t know about the size change. That's
why you'll most likely have to call Graphics Text directly with
VDISYS( ). As Program 7-6 demonstrates, you must POKE
each character of the string to the intin array, which makes
this method of printing much more cumbersome than PRINT.
Still, in order to achieve some text effects, it may be necessary.
Please note that since PRINT uses v_gtext( ), it prints all
ASCII characters from 0 to 255. This means that it does not
respond to any of the terminal emulation escape codes or
cursor-positioning codes, as do most BASIC PRINT statements.
Program 7-6. text.bas
198
fullw
2:
clearw
2
~
116
res
= peek (systab)
129
if
(res<4)
then
xmax
=
639 else xmax
=
319
138
if
(res>1)
then
ymax
=
199 else ymax
=
399
149
REM
Set
Text Baseline Rotation
i3¢@
poke contrl,13
:REM opcode
for
set baseline vector
168

<!-- source-page: 176 -->
## Page 176

Text
168
poke contrl+2,
@
:REM
no points
in ptsin
1798
poke contril+é,
1
sREM angle
in
intin
array
188
poke
intin, 188d
199
vdisys(1)
288
REM
216
color
2
:REM
red
text
228
gotoxy
146,12
2368
print
"This
is upside down."
249
color
3
:REM green
text
258
REM graphics text
26a
poke contrl1,8
:REM opcode
for graphics text
278
poke contrl+2,1
:REM alignment
point
for
text
in ptsin
288
a$="This
is
also upside down.”
298
poke contri+é6,len(a$)
=REM length
of
string
38d
poke ptsin,
xmax%3/4
318
poke ptsint2, ymax/2
328
for
c=i
to
len(a$)
338
poke intin-2+
(2%), asc (mid$(a%,c,1))
348
next
c
356
vdisys(1)
368
REM Reset
Text
Baseline Rotation
378
poke contri,i13
:REM opcode
for
set
baseline vector
388
poke contrl+2,
@
s:REM
no points
in
ptsin
398
poke contri+é,
1
:REM angle
in
intin
array
490
poke
intin,d
419
vdisys(1)
426
color
t£
:REM back
to black
436
REM
set
Text
Height,
Points
mode
449
poke contrl],i197
=REM opcode
for
set
height
456
poke contri+2,@
:REM
no ptsin
468
poke contrl+6,1
:REM height
in
intin
479
poke intin,
298
48a
vdisys(1)
496
print
"This
is big"
5oo
REM
set
Text
Height,
Points
mode
51d
poke contri1,167
:REM opcode
for
set
height
S28
poke contrl+2,@
:REM
no ptsin
538
poke contrl+é,1
:REM height
in
intin
54d
if
(res=1)
then
poke intin,1@ else poke
intin,9?
55g
vdisys(1)
368
print
“back
to
normal”
Using Graphic Text from Assembly Language
The conversion of the C function v_gtext( ) to assembly language is a
little trickier. That’s because the C language
bindings take care of the drudgery of moving each character of
the string into the intin array. When programming in assembly
language
, you must take care of this detail yourself. In addition, you must convert each 8-bit character to 16 bits, with the
character information in the low-order bits. Program 7-7 demonstrates printing strings with the Graphics Text function.
169

<!-- source-page: 177 -->
## Page 177

CHAPTER 7
Program 7-7. text.s
KERR
KEEA AAA K EERE ARERR AREER EEE
EE RE
x
*
s
x
TEXT.S
—~ assembly language
x
‘
graphics
text
demo
bs
*
x
*
%
3
t
x
®
EUSTACE
KEE
TERRE REE ERE
EEE ES
-xdef
demo
«xref
vwkhnd
»xref
contrls
«xref
contrlil
«xref
contri2
»xref
contrl3
»xref
contrl4
»xref
contrisS
«xref
contrlé
»xref
contrl7
«xref
contri8s
-xref
contrl?
xref
contr119
»xref
contrlil
-xref
intin
»xref
intout
»xref
ptsin
xref
ptsout
»text
demo:
move
intout+2, ymax
move
dy,di
cmp
#399, ymax
&
if
high-res
bne
skip
add
di,di
move
di,dy
%
double
dy
skips
move
424,05
& starting vertical
position
move
#24,d6
& starting horizontal
position
movea.l
#msg,a4
&
save text
pointer
address
in
a4
move
#3,0d4
*®
loop counter
next:
44%
Set
text
color
move
#22,contr1S
* opcode
for
text
color
move
#2,contr1i
&
no points
in ptsin
move
#1,contrls
&%
1
integer parameter
in
intin
move
#4,d1
sub
d4,d1
move
di,intin
&
set
color
from
loop counter
jsr
vdi
R88 Frint graphics text
move
#8, contr1@
&
opcode
for
gtext
move
#i1,contrit
®
1
point
in
ptsin
add
dy,dS
*
advance
y
170

<!-- source-page: 178 -->
## Page 178

Text
move
d3, ptsin+2
&
set
y
text position
_.
move
dé, ptsin
&
set
x
text position
move
#81,dd
& maximum no.
of
characters
move
d8,d2
&
save
a copy
movea.l
#intin,al
&
address
of
destination
in
al
_—_
movea.1
(a4) +,a9
% address
of
source
in
a@
text:
clriw
di
move.b
(a8) +,d1
%
move
a
letter
from source...
move.w
di, (ale
&
to word-aligned destination...
—
dbeq
dd, text
&
until
all
done.
sub
d6,d2
&
how many characters..
move
d2,contris
&
@
of
characters
in
string
isr
vdi
& print
text
dbra
d4, next
3
next
text
string
rts
S683
data section
dy:
.dc.w
16
&
Text
lines
tis
dc.b
"This
is the First
Line
of
Text.’,@
t2:
ede.b
*This
is the Second
Line
of
Text.’,8
tS:
-dc.b
"This
is the Third
Line
of
Text.’,@
t4
-dc.b
*This
is the Last
Line
of
Text.
Qver
and out.’,9
msgs
-dce.1l t1,t2,t3,t4
bss
ymax
.ds.w
1
.eand
171

<!-- source-page: 180 -->
## Page 180

Chapter 8
Input Functions

<!-- source-page: 181 -->
## Page 181

So far 9 we've concentrated on the output functions of
the VDI, those related to drawing on the screen. But the VDI
screen device encompasses the ST keyboard and mouse as
well, just as the GEMDOS console device includes both the
screen and keyboard. The VDI provides functions that directly
report the status of physical devices, like the mouse pointer
and mouse buttons, and some special keys on the keyboard. It
also implements several logical devices that return information
from the user to the program in a manner that’s a
little more
independent of the actual hardware on which the GEM operating system is running.
The VDI input functions provide only the bare-bones type
of input that you normally associate with computers that lack
the elaborate user interface that the ST provides. That’s because the AES portion of GEM provides much more sophisticated facilities for interacting with the user than we associate
with the ST.
An important point to remember is that the VDI input
functions may not be compatible with those of the AES. Most
of the time, you'll find that the VDI input functions don’t
work properly when used in conjunction with the input functions of the AES. Therefore, if you want to use the AES input
facilities, which provide all of the power of the VDI functions
and much more, you'll have to abandon the VDI functions
presented below. You may find, however, that (at least in earlier versions of the ST Operating System), the AES functions
are somewhat slow to respond, and may not be as reliable as
those of the VDI. For some demanding applications, you may
find it desirable to substitute the more basic services of the
VDI for the AES input functions. And, for TOS programs that
don’t need the windowing, icon, and menu services provided
by the AES, you may find the VDI input functions adequate
for your input needs, and simpler than writing
a GEM type
program.
175

<!-- source-page: 182 -->
## Page 182

So far,
we've concentrated on the output functions of
the VDI, those related to drawing on the screen. But the VDI
screen device encompasses the ST keyboard and mouse as
well, just as the GEMDOS console device includes both the
screen and keyboard. The VDI provides functions that directly
report the status of physical devices, like the mouse pointer
and mouse buttons, and some special keys on the keyboard. It
also implements several logical devices that return information
from the user to the program in a manner that’s a little more
independent of the actual hardware on which the GEM operating system is running.
The VDI input functions provide only the bare-bones type
of input that you normally associate with computers that lack
the elaborate user interface that the ST provides. That’s because the AES portion of GEM provides much more sophisticated facilities for interacting with the user than we associate
with the ST.
An important point to remember is that the VDI input
functions may not be compatible with those of the AES. Most
of the time, you'll find that the VDI input functions don’t
work properly when used in conjunction with the input functions of the AES. Therefore, if you want to use the AES input
facilities, which provide all of the power of the VDI functions
and much more, you'll have to abandon the VDI functions
presented below. You may find, however, that (at least in earlier versions of the ST Operating System), the AES functions
are somewhat slow to respond, and may not be as reliable as
those of the VDI. For some demanding applications, you may
find it desirable to substitute the more basic services of the
VDI for the AES input functions. And, for TOS programs that
don’t need the windowing, icon, and menu services provided
by the AES, you may find the VDI input functions adequate
for your input needs, and simpler than writing
a GEM type
program.
175

<!-- source-page: 183 -->
## Page 183

CHAPTER 8
Physical Devices
The physical devices to which the VDI gives the most direct
support is the mouse and its onscreen alter ego, the mouse
pointer. One important mouse function that we have already
encountered in the shell program is called Sample Mouse Button State. This function not only lets you know whether the
left and/or right mouse button is currently being pressed, but
also the exact location of the mouse pointer on screen. The C
language syntax for this function is
int handle, button, x, y;
vq—mouse(handle, &button, &x, &y);
where button is the variable in which the function returns the
current button status code, and x and y
are the variables in
which the function returns the onscreen coordinates of the
mouse pointer (which usually looks like an arrow, or a busy
bee). The button status code uses the least significant bit to
record the status of the left mouse button, and next most significant bit for the right mouse button. These bits contain a
1
if the button is pressed, and a
0
if the button is up. Therefore,
the possible button codes are
Code
Meaning
0
Neither button pressed
1
Left button only pressed
2
Right button only pressed
3
Both buttons pressed
If you only wait until the button code is no longer 0,
you'll never see a code of 3, since the user will always push
down one button a
fraction of a second before the other, even
if he’s certain that he’s pushing them both down at the exact
same moment. Therefore, you'll have to test the button status
several times in a row after the initial push if you want to detect the condition where both butons are pressed at once.
The other point to note about this function is that the x
and y coordinates that are returned for the mouse pointer refer
to the hot spot or action point of the pointer. That’s the part of
the pointer which is considered to be its location on the
screen, even when the pointer is considerably larger than a
single point. On the arrow shaped pointer, the hot spot is located at the very tip of the arrow, while the bee’s hot spot is
at its very center.
176

<!-- source-page: 184 -->
## Page 184

Input Functions
The Pointer
While the mouse pointer is normally shaped like an arrow (or
a bee when they system is busy accessing a disk or the like),
the VDI allows you to change the pointer to any 16 X 16 image. The function provided for this purpose is called Set
Mouse Form, and it’s called like this:
int handle, pointerdata[37];
vsc_form(handle, pointerdata);
where pointerdata is a pointer to an array of 37 integers that
provides information about the mouse pointer. This information includes the foreground and background colors for the
pointer, the coordinates of the hot spot, the shape of the
mouse pointer, and a mask which allows you to specify
whether the zero bits in the 16 X 16 block are transparent
(don’t replace existing background with a new color), or
opaque (replace existing background with pointer background
color). The layout of this array is
Element
Description
x coordinate of hot spot
y coordinate of hot spot
Reserved for future use (must be set to 1)
Background pen (usually 0)
Foreground pen (usually 1)
5-20
16 words of color mask data
21-36
16 words of image data
Bm ON
©
The x and y coordinates of the hot spot are measured from
the top, left corner of the 16 X 16 pixel block. The image data
block is arranged exactly the same way as the 16 X 16 pattern
fill block. Each line of the image is represented by one 16-bit
word, with the most significant bit of the word representing
the leftmost dot, and the least significant bit, the rightmost
dot. Each bit position that’s filled with a
1 is colored with the
foreground pen, and each bit position that holds a 0
is colored
either in the background color, or whatever color is displayed
by the existing background, depending on the color mask.
_
The color mask is used to define the shape of the pointer,
without regard to color information. Those bit positions containing a
1 are considered to be “‘inside’’ the pointer, and
whether or not the image data contains a
1 bit, this part of the
pointer will be colored in, either by the foreground pen or the
177

<!-- source-page: 185 -->
## Page 185

CHAPTER 8
background pen. Those bit positions containing a 0 are considered to be “outside” the pointer image, or transparent, and the
corresponding image data bit positions that contain 0 will be
represented on screen by whatever background data happens
to be there.
Having a two-color pointer is very important since you
want to make sure the pointer is always visible. Even though
the normal system pointers like the arrow appear to be black
only, there is actually a thin white line around the outside.
This makes it possible for you to see the arrow, even when it’s
in front of a black background. The sample program mousebox.c
(Program 8-1) creates a custom two-color pointer that shows
up as red and green on a color monitor.
The vsc_form( ) function is very similar to the AES function graf_mouse( ). That function allows you to choose from
several default pointer shapes, such as the arrow, the bee, the
pointing hand, and open hand, the I-beam text cursor, and
crosshairs.
In addition to the ability to change the appearance of the
mouse pointer, the VDI provides functions that allow you to
determine whether it will be visible on screen or not. The
function used to turn the pointer off is called Hide Cursor, and
its C language syntax is
int handle;
v—hide_c(handle);
The reverse function, used to turn the pointer back on is
called Show Cursor, and it’s called like this:
int handle, reset;
v_show_c(handle, reset);
In order to understand the reset flag of the Show Cursor
function, you must first understand the interaction between
this function and Hide Cursor. Every time you use the Hide
Cursor function, the VDI makes a note of it, and hides the
cursor down one level farther. So if you call Hide Cursor five
times in a row, you must call Show Cursor five times before it
becomes visible again—the first four times, Show Cursor just
decreases the level at which the pointer is hidden. It is possible to override this system with the reset flag, however. If you
call Show Cursor with the reset flag set to 0, the number of
previous Hide Cursor calls is ignored, and the mouse pointer
178

<!-- source-page: 186 -->
## Page 186

Input Functions
is brought to the top, no matter how far down it was hidden.
If the reset flag is set to 1, however, the function behaves normally, and depends on the number of Hide Cursor calls performed previously.
In our previous sample programs, we’ve seen just how
important it is to turn the mouse pointer off before you do any
drawing. In the shell program that forms the heart of most of
our demonstration programs, we didn’t turn off the mouse
pointer before clearing the screen, and as a
result, the old
background is saved behind the pointer. That means that
when you move the pointer, the old background is restored,
erasing our newly cleared screen in the area of the cursor
block along with anything that we drew on it as well. The solution to this problem is to hide the mouse pointer before undertaking any graphics operation, including one so simple as
clearing the screen, and restoring it only when you’re certain
that graphics output has stopped. An example of this practice
may be seen in the drawline(
) function of mousebox.c, Program 8-1.
Special Keys
The final physical device function that the VDI provides is
used to check the status of some of the special keys on the ST
keyboard. The Sample Keyboard State Information function
returns information which lets you know whether the Control,
Alt, and/or Shift keys are currently pressed. The format for
this call is
int handle, key
vq—key_s(handle, &key);
where key is a flag indicating the status of the various keys. Bit
0 gives the status of the right Shift key; bit 1 gives that of the
left Shift key; bit
2 gives that of the Control key; and bit 3
gives that of the Alt key. If the key is pressed, there will be a
1 in the corresponding bit position, if not, there will be a 0.
The values of the various bit positions are as follows:
Bit
Value
Key
0
1
right Shift
1
2
left Shift
2
4
Control
3
8
Alt
179

<!-- source-page: 187 -->
## Page 187

CHAPTER 8
Logical Devices
In addition to the physical device functions, the VDI implements some logical input devices. These logical devices provide very specialized input facilities in
a device-independent
manner. They are provided mostly for purposes of portability,
since there are much better ways to get input in an ST-specific
environment. The four logical devices are the Locator, Valuator, Choice, and String devices. The functions performed by
these devices will be detailed below.
The logical devices operate in one of two modes. In Request mode, the functions do not return until a specific terminating input event occurs. In sample mode, the functions
return the current status of the device as soon as they are
called.
Before using any of the logical devices, you should specify
whether you want it to operate in sample mode or request
mode. Set Input Mode is the function used, its format looks
like this:
int handle, ldevice mode;
vsin_mode(handle, Idevice, mode);
where [device is the logical device code, and mode is a flag
showing whether that device should be set to request or sample mode. The logical devices are
Number
Device
1
Locator
2
Valuator
3
Choice
4
String
The possible modes are:
Number
Mode
1
Request
2
Sample
You may discover the current mode status of any logical
device with the function Inquire Input Mode. The syntax for
this function is
int handle, ldevice, mode;
vqin_mode(handle, Idevice, &mode);
180

<!-- source-page: 188 -->
## Page 188

Input Functions
where [device is the logical device number, and mode is the
variable in which the current operating mode is returned. With
the current version of the ST operating system, however, this
function actually returns the mode number minus one.
Locator Device
The locator device allows the user to specify a point on the
display screen. In the request mode, it turns the mouse pointer
on, allows the user to move it with the mouse, or with the
ALT-arrow key mouse substitutes, until a mouse button or the
appropriate key is pressed. The function returns the x and y
position of the mouse pointer, a code that indicates what the
terminating event was, and then turns off the mouse pointer.
The C syntax for the function Input Locator, Request Mode is
int handle, x, y, x1, yl, term;
vrq—locator(handle, x, y, &x1, &y1, &term);
where x and y specify the starting position for the mouse
pointer, x1 and y/1 are the variables in which its ending position is recorded, and term is the variable in which the terminating event is returned. The termination code is 32 for the
left mouse button, 33 for the right mouse button, or the ASCII
value of the key that was pressed to end the function. Note
that with the current version of the operating system, this
function tends to return immediately as if the left mouse button was pressed. The solution to this problem is to call it twice
in a row, and ignore the results of the first call.
When the locator device is used in sample mode, the
mouse pointer is not automatically turned on, so, if it isn’t
showing, you should turn it on with v_show_c( ). The C syntax for Input Locator, Sample Mode is
int handle, x, y, x1, y1, term, status;
status = vsm_locator(handle, x, y, &x1, &y1, &term);
The status variable is used to return a status code that
tells whether a mouse button or key was pressed, and if the
position of the mouse pointer changed. The least significant
bit of this code tells whether there was a position change, and
the next bit tells whether a key was pressed. The possible
code values are:
181

<!-- source-page: 189 -->
## Page 189

CHAPTER 8
Status
Description
0
No key pressed, no position change
1
No key pressed, position changed
2
Key pressed, no position change
3
Key pressed and position changed
String Device
The string device is used to input a string of text characters
from the user. In the request mode, this function collects characters until the Return key is pressed, or until the maximum
number of characters have filled the buffer. The syntax for Input String, Request Mode is
int handle, max_len, echo, xy[2];
char string[max_len];
vrq_string(handle, max_len, echo, xy, &string);
where max_len is the maximum buffer length, echo is a code
that specifies whether or not the characters should be echoed
to the screen as they are typed in (1=yes, 0=no), xy is an array that holds the x and y coordinates for the echoed characters, and string is a pointer to the string of characters that the
user enters. In the current version of the ST operating system,
echoing of characters (which is not a required feature of the
function), isn’t supported.
It’s also possible to use this device in sample mode. In
this mode, the function checks the keyboard once. If there are
no keystrokes waiting, the call simply returns. If there are keystrokes, the function keeps collecting them until there aren’t
any more, the buffer is full, or a carriage return is entered. The
syntax for this call is
int handle, max_len, echo, status, xy[2];
char string[max_len];
status = vsm_string(handle, max_len, echo, xy, &string);
where status is the length of the string gathered.
The string function returns the ASCII code for each character that’s entered on the keyboard. Some key combinations,
however, have no ASCII value. The function keys, the ALT
key combinations, and the HELP keys are all examples of key
presses without ASCII equivalents. And in some cases, two or
more combinations have the same ASCII value. For example,
the numbers on the keypad are not distinguishable from the
182

<!-- source-page: 190 -->
## Page 190

Input Functions
numbers on the top row of the keyboard by ASCII value
alone. When you wish to get more information about the key
presses other than the ASCII character, you may use a negative number of max_len. When you do so, the buffer size will
be set to the absolute value of the number specified, and the
values returned in the intout array will consist of two-byte
keycodes, based on the VDI standard keyboard definition. In
most cases, the first byte consists of a code that corresponds to
a particular key on the keyboard, and the second byte is the
ASCII code produced. The full set of keycodes may be found
in Appendix B. Since the C language bindings only copy the
second byte of each word to the string array, you must read
the intout[] array directly to find the full keycode value for
each character.
Program 8-1 uses the String device in sample mode to
check for the user pressing the ESC key, which ends the program. It also illustrates many of the other functions discussed
above. It displays a custom two-color mouse pointer (red and
green on color systems), it reads the mouse with vq_mouse( ),
and it hides the mouse pointer before drawing.
Program 8-1. mousebox.c
/ERERERREREAE
TSAR ERARER SECRET EERE
EE EERE KEE,/
/t
“/
/t
“ss
/%
MOUSEBOX.C
-- Demonstrates use
of
the
x/
‘*%
input functions.
“/
/t
“/
/t
%/
/*
%/
JERRERRRARESESARAEEEKERE
EEE
SERRE REE EEE,
#include
"shell.c"
#define
XOR
3
#define REPLACE
1
/t
Data
for
our
own custom two-color
pointer
%/
int
pointer([37]
=
€
8,8,1,
/&
x
and
y
of
hot
spot
&/
3,2,
/* background
and foreground
pens
%/
/*
16 words
of
color
mask
data
%/
@xFC7E,
OxFC7E,
@xCC66,
BxCCb6,
@xCCS6,
OxFC7E,
SxFC7E,
IxOaae,
@xFC7E,
GxFC7E,
@xCC66,
OxCCb6,
@xCC66,
OxFC7E,
OxFC7E,
Ox OOo,
/*%
16 words
of
image data
%/
183

<!-- source-page: 191 -->
## Page 191

CHAPTER 8
@xFC7E, @xFC7E, OxCC44, @xCC44, @xCC66, OxFC7E, OxFC7E, @x800o,
OxOIOO, BOOS, OxPIWS, OxOOIS, OxGWIS, PxSGOO, BxGWO, Bxgaee,
+5
demo (>
€
int
mousex,
mousey,
buttons=@,
notdone=1;
int
color,
maxcolor,
fill=i,
pointsl193,;
maxcolor=color=work_outCi3]3;
/&
find highest available color
%t/
/*%
make cursor visible
in monochrome also
t/
if (work_outl11>208)
pointer (31=0;
v_hide_c(handle@);
/&
hide the mouse
&/
puts ("\33EDrag the mouse
to draw boxes. \n");
puts ("Press
"ESC"
to quit.\n")3;
vec_form(handlie,pointer);
/#
install
our
new pointer
&/
v_show_c(handie);
/%
show the mouse again
%/
vsin_mode(handle,4,2);
/*
set
string
device to sample mode
%/
vsl_type(handle, 3);
/%
used dotted
line
&/
vsf_interior (handlie,2);
/& Dotted patterns
%/
while (notdone)
<
while(
(buttons=99
)
&& notdone)
/&
wait
for button
push
4%/
€
vq_mouse (handle,
&buttons,
S&mousex,
kmousey) 3
notdone=testkeys();
/&
and check
for
ESC
&/
3
vewr _mode (handle,
XOR);
/& drawmode
to
XOR
for
"rubber
band’
points(83=points({2)=points(41=points[61=points(8]=mousex};
pointslil=pointsl3]=potnts(5J]=pointel7]=points(9]=mousey;
drawline(points);
/* draw initial
point
%/
whilet
(buttons!=3)
&& notdone)
/%
while button
is held
%/
€
vqg_mouse (handle,
&buttons,
S&mousex,
kmousey) :
notdone=testkeys();
/8
is
it
moved,
or
ESC pushed?
%/
if(
(mousex!=points(£2])
1!
(mousey! =points[7})
)
<
drawline(points);
/& erase
old
line
&/
pointsl21=pointsl
4) =mousex }
pointelS)=pointsl7l=mousey;
drawline(points);
/%
and draw new one
&t/
3/%&
end
of
if
position changedt/
3
/%
end
of
while button
is pressedt/
drawline (points);
/% erase
last
line
%/
vewr_mode(handlie,
REPLACE);
/&
set drawmode back
%/
if
(color==maxcolor)color=13;
/8& advance color
%/
vef_color (handle, color++);
if
(fill==25)fill=1;
/*%
and
fill
style
&t/
vsf _style(thandle, fill++);
pointsl(2J={pointsl4];
points(3)=points(S};
v_hide_c (handle);
v_bar (handle, points);
/& draw the filled
box
&/
v_show_c (handle);
3}
/%&
end
of
main while
£/
puts ("\33EThat’s it--Press
a mouse button
to exit.\n");
184
a/

<!-- source-page: 192 -->
## Page 192

Input Functions
+
/&
end
of
main()
£/
int testkeys()
/® check
keyboard
for
ESC
key
£/
€
char
string
(273
int
status;
status=vem_string(handle,
-1,8,&string, &string);
if Cintout(Sl==<9x11B)
return(S);
/*
code
for
ESC
%/
else return(1);
}
drawline (points)
int
tpoints;
¢<
v_hide_c (handle);
v_plinethandle,5,points);
/& draw
initial
point
%/
v_show_c (handle);
}
/%
End
of
Mousebox.c
&/
Choice and Valuator Devices
The two remaining logical devices, the Choice and Valuator
devices, are not required VDI functions and are not implemented for the screen device in the current version of the ST
operating system. We’ll describe these functions briefly, for the
sake of completeness.
The choice device allows the user to choose one of several
options, usually by pressing one of the function keys. In request mode, it waits for one of the keys to be pressed. If it’s a
function key that’s pressed, its value (1-10) is returned, and if
not, the default value is returned. The syntax of Input Choice,
Request Mode is
int handle, default, choice;
vrq—choice (handle, default, &choice);
where default is an initial choice value that you supply, and
choice is the variable in which the user’s choice is returned. In
sample mode, the choice and a
status value are returned. The
syntax for Input Choice, Sample Mode is
int handle, status, choice;
status = vsm_—choice(handle, &choice);
If the user was pressing a function key during the call,
status will contain a
1 and choice will indicate the function key
pressed. If not, both contain a
0.
The valuator device allows the user to choose a number
between 1 and 100. Typically, the user strikes the up and
185

<!-- source-page: 193 -->
## Page 193

CHAPTER 8
down arrow keys to increase or decrease the default value. In
request mode, the function takes input until the terminating
——
character is struck. The syntax for this mode is
int handle, default, value, term;
vrq—valuator(handle, default, &value, &term);
—
where default is an initial value supplied by the programmer,
value is the variable in which the final value is returned, and
term is the variable in which the terminating character is
returned.
In sample mode, the function checks if the increment or
decrement conditions exist during the call, and if they are
present, it changes the value accordingly. The syntax for Input
Valuator, Sample Mode is
int handle, default, value, term, status;
vsm_valuator(handle, default, &value, &term, &status);
The status variable will contain a
1 if the valuator
changed during the call, and the value variable will contain
the new value. Status will contain a 2 if another key was
pressed, and the term variable will contain the value of this
character. If neither event occurs, status will contain a
0.
Vector Exchange Routines
The fundamental GEM input functions are performed on an
interrupt basis. This means the operating system watches for
certain input events, and calls the appropriate service routine
when such an event occurs. For example, when the mouse is
moved, it calls a routine that updates the position of the
mouse pointer on the screen.
Since an application program sometimes wishes to perform actions that are synchronized with one of these input
—
events, the VDI supplies
a number of vector exchange routines.
These provide a means of “patching in” your own machine
language routines that will be called before the system inter-
—
rupt service routine when the event occurs. For example, if
you wanted your program to do something every time the
user pushed the mouse button, you could point the mouse
-
button interrupt vector at your routine, and have your routine
call the normal mouse button routine when it was done.
The VDI provides interrupt-vector exchange routines for
~~
four input events. These are
186
—

<!-- source-page: 194 -->
## Page 194

Input Functions
Mouse movement. The mouse movement routine is
called every time that the mouse moves to a new location. If
the application program grabs the mouse movement vector, it
gains control after the x and y address coordinates have been
calculated, but before the VDI is informed for the new position, and before the mouse pointer is actually redrawn on the
screen. At that point, the x coordinate of the mouse pointer is
in register dO, and the y coordinate is in d1.
Mouse pointer redraw (cursor change). This routine is
called each time the cursor needs to be redrawn. If this vector
points to an applications service routine, the application gains
control before the redraw actually occurs. This means that the
application can take over the task of drawing the cursor, or
just perform some action every time that a redraw is scheduled. At the point the application gains control, the x coordinate of the mouse pointer is in register dO, and the y
coordinate in dl.
Mouse button press. The button press routine is called
each time the state of the mouse buttons change (that is, a
button is pressed or released). If this vector is diverted to the
application, it receives control after the button press has been
decoded, but before GEM learns of the press. At that point,
register dO contains a code that indicates the mouse button
status. This code is the same as that used by the Sample
Mouse Button State function:
Code
Meaning
0
Neither button pressed
1
Left button only pressed
2
Right button only pressed
3
Both buttons pressed
Timer tick. This routine is called every time the system
clock advances one step (or tick). This allows the application
to take some action on a fixed, periodic basis. The frequency
of these tick events in milliseconds is returned by the vector
exchange routine.
The mechanics of intercepting a vector is fairly simple.
First, you must write
a machine language routine that will be
called every time the event happens. This routine should preserve all registers in the state in which it found them. When
it’s called, all interrupts are disabled, and the application code
should not enable interrupts. Since the service routines are
187

<!-- source-page: 195 -->
## Page 195

CHAPTER 8
called by GEM with a JSR instruction, your routine should end
with a RTS instruction (or JMP to the normal system routine,
which itself ends in a RTS).
Note that when your code is executed, the machine is in
supervisor mode, and its state is such that it’s unlikely that
~—
you can successfully make any OS calls from within your
code. Although the ST BIOS is supposed to be reentrant up to
three levels, you may find that this really isn’t true. The upshot is that you're limited in the kind of tasks that you may
perform by patching into these vectors. Nonetheless, you may
find some legitimate uses for the vector exchange routines. For
example, the mouse movement routines can be used to alter
the rate of change, so as to create a slow motion mode for a
drawing program. By monitoring the mouse buttons, you can
get a good fix on button activity if the higher-level routines
get confused, as they sometimes do. And using the vector exchange to constantly update mouse x and y position variables
saves you from calling vq_mouse constantly from your code.
Once you’ve written the additional (or replacement) routine, you need to point the system to your new routine. You
do this by calling one of the Vector Exchange routines. These
routines all have pretty much the same syntax:
int scr_handle;
unsigned int ticklen;
long oldv, newv;
/* Exchange Button Change Vector */
vex_butv(scr_handle, &newv, &oldv);
/* Exchange Mouse Movement Vector */
vex_motv(scr_handle, &newv, &oldv);
/* Exchange Cursor Change Vector */
vex_curv(scr_handle, &newv, &oldv);
vex_timv(scr_handle, &newv, &oldv, &ticklen);
/* Exchange Timer Interrupt Vector */
where &newv is a pointer to your new machine language routine, and oldv is a variable in which the address of the old system event routine is stored. You should save this address,
~
since in most cases your machine language routine will want
to call the old routine to perform the normal system function,
either with a JSR from your routine, or by ending your routine
188
—_

<!-- source-page: 196 -->
## Page 196

Input Functions
with a JMP to the old one. You'll also need this address to restore the vector when you are through with it. This can be
done with a
call of the form:
int scr_handle;
long oldv, dummy;
vex_butv(scr_handle,oldv, &dummy);
where oldv is the variable in which you stored the old vector,
and dummy is a dummy variable that’s used as a place-holder.
Practical experience has shown that in all of the above
routines, the handle to use the variable scr_handle is not the
VDI virtual workstation device handle that we've been using
all along. Instead, it’s the physical screen device handle, the
value returned by the AES call graf_handle( ).
BASIC Input Functions
ST BASIC supports the common BASIC input functions, like
INPUT, and it also implements the INP command, which allows you input a byte stream though a TOS device. Using device 2, the console device which consists of the keyboard and
the display screen, you can read individual keys, one at a
time. (Device 4, labeled keyboard, is used to send codes to the
intelligent keyboard controller.) This function is comparable to
the BIOS routines, however, not the VDI, and so the ASCII
codes for the keys are returned, not the VDI keycodes.
The first version of ST BASIC does not incorporate any of
the VDI functions for reading the keyboard, mouse pointer position, or mouse buttons. The proposed revision to ST BASIC
includes functions such as ASK MOUSE, which returns the
position of the mouse pointer and the button status, just like
vq—mouse( ). But with the original version of ST BASIC (and
to the extent the new one doesn’t cover the full range of VDI
input commands), you will have to resort to making VDI calls
with VDISYS(1) for these functions.
Program 8-2 is a BASIC translation of the mousebox.c,
Program 8-1, which was discussed earlier in this chapter. It allows the user to draw filled boxes by dragging a mouse button, and checks the keyboard for the ESC key, which ends the
program. You will note, however, that in this version you
have to wait for the mouse to stop moving before you see the
dotted outline of the box.
189

<!-- source-page: 197 -->
## Page 197

CHAPTER 8
©
Program 8-2. mousebox.bas
199
119
12
139
146
159
1698
178
189
199
2088
219
229
238
248
2359
269
278
289
298
338
312
329
338
34g
358
36d
378
388
398
486
418
429
4308
449
45a
469
478
480
496
300
318
528
S38
540
350
569
578
58a
598
489
618
628
638
649
658
668
678
68a
699
788
718
728
738
190
fullw
2:
clearw
2
res
=
peek (systab)
maxcolor
= restres
filltypezi:
fillcol=1
REM
set
string device
to sample mode
poke contr1,33:
REM opcode
for
set
input
mode
poke contr1+2,@9:
poke contri+é6,2
poke intin,4:
poke intin+2,2
vdisys(1)
REM
set
line type
poke contr1,15:
REM opcode
for
set
line type
poke contrl1+2,@:poke contrl+é, 1
poke intin,S
vdisys(1)
done
=
@
gotoxy
1,1:?"Drag mouse
to draw boxes"
print
"
Press ESC
to quit”
while
(done=@)
:REM until
escape
key
is pressed
while
(¢(
(buttons=8)
AND
(done=@) >
gosub MOUSEKEYS
wend
if
(done=1)
then
goto LOOP
poke
intin,
3:
gosub
MODE
for
x=9
to
16 step
4
poke ptsin+x,
mousex
poke ptsin+x+2,mousey
next
while(
(buttons>@)
AND
(done=@) >
gosub MOUSEKEYS
if
(done=1)
then
goto CHECK
gosub DRAWLINE
poke ptsin+4,mousex;s
poke ptsin+8, mousex
poke ptsin+19,mousey:
poke ptsint+14, mousey
gosub DRAWLINE
CHECK:
wend
if
(done=1)
then
goto LOOP
gosub
HIDE
gosub PLINE
poke intin,t:
gosub
MODE
if
(filltype=25)
then filltype=1
if
(#illcol=maxcolor)
then fillcol=1
color
1,
fillcol,
1,
filltype,
2
Ffilltype=filltype+ti:s
fillcol=fillcol+t
poke ptsin+4, mousex
poke ptsin+té, mousey
REM
do Bar
poke contrl,1i:
poke contrl+1@,1
poke contrl+2,2:poke contr1+6,@
vdisys(1)
gosub
SHOW
LOOP:
wend
END
REM
SHOW:
poke contrl,i22:
goto CURSOR
HIDE:
poke contrl1,123
CURSOR:
poke contr1+2,8:poke contrl+6,9
vdisys(1)
return
PLINE:
poke contrl,6:
REM pline opcode
poke contr1+2,5:
poke contri1+6,@
vdisys(i)
return
REM
DRAWLINE:
gosub
HIDE:
gosub PLINE:
gosub
SHOW:
return

<!-- source-page: 198 -->
## Page 198

Input Functions
748
7358
769
778
788
798
800
618
820
830
84a
850
878
ese
895
988
918
REM
MOUSEKEYS:
poke contr1,124s
REM mouse inquiry
poke contri+2,8:poke contri+é,9
vdisys (1)
mousex=peek (ptsout): mousey=peek
(pt sout+2)
buttons=peek (intout)
KEYS:
poke contri1,31
poke contrl1+2, lipoke contrl+6,2
poke intin, 65535:REM
—1
vdisys(1)
if
(peek (intout)=283)
then
done=1
return
REM
MODE:
poke contrl,32
poke contri+2,@
poke contri+é6,1
vdisys(1)
return
191

<!-- source-page: 200 -->
## Page 200

Appendix A
VDI Function
Reference

<!-- source-page: 202 -->
## Page 202

v—opnwk
Open Workstation
v_opnwk( )
Opcode= 1
This function opens a workstation that’s used to communicate with a physical output device and to keep track of its graphics settings. The VDI communicates with the device by means of a device driver that translates the VDI
commands to device-specific commands. When the workstation is opened,
the device driver designated by the ASSIGN.SYS file is read in, so this
driver must be present and the GDOS must be loaded in order for this command to work. The Open Workstation command allows you to make initial
settings for a number of graphics output functions. The function returns the
VDI device handle, along with a lot of information about the output capabilities of the device. The device is cleared upon opening.
Devices required for
All
C binding
int handle, work_in[12], work_out(57];
v—opnwk(work_in, &handle, work_out);
Inputs
contrl(0] =
1
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3} = 11
Number of input integers in intin
The initial graphics output settings for the workstation are specified by
the contents of the intin array (which the bindings take from work_in[ ]).
work_in[0]
intin(0]
Device ID number (from ASSIGN.SYS
file)
work_in{1]
intin{1]
Line drawing pattern [vsl_type( )]
work_in[2]
intin[2]
Line pen number [vsl_color( )]
work_in[3}
intin[3]
Marker type [vsm_type( )]
work_in[4]
intin{4]
Marker pen number [vsm_color( )]
work_in[5}
intin[5]
Text font [vst_font( )]
work_in[6}
intin[6]
Text pen number [vst—color( )]
work_in[7]}
intin[7]
Fill pattern type [vsf_interior( )]
work_inj8]
intin(8]
Fill pattern index [vsf_style( )]
work_in(9]
intin[9]
Fill pen number [vsf_color( )]
work_in[10]
—_intin[10]
NDC to RC transformation flag
0 = Use Normalized Device
Coordinates
1 = Reserved for future use
2 = Use Raster Coordinate system
195

<!-- source-page: 203 -->
## Page 203

v—opnwk
Results
contrl[2] =
6
Number of points in ptsout
contrl[4] = 45
Number of output integers in intout
handle
contrl[6] = n
The device handle for this device
(0 if device was not opened)
The results returned in the intout and ptsout arrays given a wide range
of information about the output capabilities of the device.
work_out[0]
_—_intout[0]
Max. horizontal coordinate value (in
pixels)
work_out[1]
—_intout[1]
Max. vertical coordinate value (in pixels)
work_out[2]
—_ intout[2]
Device Coordinate units flag
(1 = device doesn’t support precise
scaling)
work_out[3]
—_intout[3]
Width of one pixel in microns
(1/1000’s of a millimeter)
For display screens, horizontal component of
aspect ratio
work_out[4]
— intout[4]
Height of one pixel in microns
For display screens, vertical component of
aspect ratio
work_out[5]
— intout[5]
Number of text font heights
(0 = continuous scaling)
work_out[6]
—_intout[6]
Number of line types.
work_out[7]
_ intout[7]
Number of line widths
(0 = continuous scaling)
work_out[8]
—_ intout/8]
Number of marker patterns
work_out[9]
_intout[9]
Number of marker sizes
(0 = continuous scaling)
work_out{10]
— intout[10]
Number of text fonts supported by the
device
work_out[11]
 intout[11]
Number of pattern fill styles
work_out[12}
— intout[12]
Number of crosshatch fill styles
work_out[{13]
intout[13]
Number of drawing pen colors available
(the number of colors that can be displayed by the device at the same time)
work_out[14]
 intout[14]
Number of Generalized Drawing
Primitives
(GDPs)—how many of the 10 basic drawing commands are supported
work_out[15]
 intout[15]
to
to
work.out[24]
 intout[24]
This part of the array holds a sequential
list of code numbers for the first 10 GDPs
supported. Each element holds one of the
following code numbers:
1 = Filled rectangle or bar (v_bar)
2 = Circle segment or arc (v—arc)
3 = Filled pie slice (v_pieslice)
196

<!-- source-page: 204 -->
## Page 204

v—opnwk
work_out[25]
to
work_out[34]
work_out[35]
work_out[36]
work_out[37]
work_out[38]
work_out[39}
work_out[40]
work_out[41]
work_out[42]
Filled circle (v_circle)
Filled ellipse (v_ellipse)
Elliptical arc (v_ellarc)
Filled elliptical pie slice (v_ellpie)
Rounded rectangle (v_rbox)
= Filled rounded rectangle (v_rfbox)
10 = Justified graphics text (v_justified)
—1 = End of list
WOON DAL
intout[25}
This part of the array holds a sequential
to
list of code numbers showing what cateintout[34]
gory of graphics operation is performed
by each of the supported GDPs. This indicates what kind of graphics settings affects
each of the supported commands. Each element holds one of the following code
numbers:
0 = Line drawing
1 = Marker drawing
2 = Graphics text
3 = Filled area
4 = No setting
intout[35]
Color availability flag
0 = Device is not capable of color output
1 = Device is capable of color output
intout[36]
Text rotation availability flag
0 = Device is not capable of text rotation
1 = Device is capable of text rotation
intout(37]
Area fill availability flag
0 = Device is not capable of area fill operations
1 = Device is capable of area fill operations
intout[38]
Cell array function availability flag
0 = Device cannot perform the cell array function
1 = Device can perform the cell array function
intout(39]
Total number of color choices available in
the palette
0 = More than 32767 colors available
1 = Monochrome
2—32767 = Actual number of colors available
intout[40]
Input devices available for the locator
function
1 = Keyboard only
2 = Keyboard and other device (such as mouse)
intout[41]}
Input devices available for the valuator
function
1 = Keyboard
2 = Other device
intout[42]
Input devices available for the choice
function
1 = Function keys on keyboard
2 = Some other key pad
197

<!-- source-page: 205 -->
## Page 205

v—opnwk
work_out[43]
 intout[43]
Input devices available for the string input
function
1 = Keyboard
work_out[44]
intout[44]
Workstation type
0 = Output only
Input only
1=
2 = Input and output
3 = Reserved for future use
4 = Metafile output
work_out[45]
_ ptsout[0
Minimum character width
work_out[46]
 ptsout[1
Minimum character height
work_out[47]
 ptsout[2
Maximum character width
work_out[48]
 ptsout[3
Maximum character height
work_out[49]
_ ptsout[4
Minimum line width
work_out[50]
— ptsout[5
0
work_out[51]
— ptsout[6
Maximum line width
work_out[52]
 ptsout(7]
0
work_out(53]
— ptsout[8
Minimum marker width
work_out[54]
 ptsout[9
Minimum marker height
work_out[55]
_ ptsout[11]
Maximum marker width
work_out{56]
ptsout[12}
Maximum marker height
See also
v—clswk( ), v_opnvwk( ), v_clsvwk( ), vq—extend
198

<!-- source-page: 206 -->
## Page 206

v_clswk
Close Workstation
v_clswk( )
Opcode=2
This call is used to terminate output to the graphics device and to release its
environment space. If any information remains in a buffer (for a printer or
metafile), it’s written out at the time the device is closed.
Devices required for
All
C binding
int handle;
v_clswk(handle);
Inputs
contrl[0] = 2
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3} =
0
Number of input integers in intin
handle
contrl(6] = n
The workstation device handle
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
v—opnwk( ), v_opnvwk( ), v_clsvwk( )
199

<!-- source-page: 207 -->
## Page 207

v—_clrwk
Clear Workstation
v_clrwk( )
Opcode=3
This function performs device-specific initialization. For a screen, it clears
the screen; for a printer, it erases printer buffer data and sends a form feed,
and so forth. No graphics output occurs with any device. The functions provided by this call are also performed by Open Workstation.
Devices required for
All
C binding
int handle;
v—clrwk( );
Inputs
contrl[0] = 3
Opcode
contrl[1] = 0
Number of points in ptsin
contr][3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contr][2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
v_opnwk( );
200

<!-- source-page: 208 -->
## Page 208

v—updwk
Update Workstation
v—updwk( )
Opcode=4
This command is used to flush the output buffers of devices like printers,
plotters and the metafile, causing the preceding graphics commands to be
executed immediately. It has no effect on the screen device.
Devices required for
All
C binding
int handle;
v_updwk(handle);
Inputs
contrl[0] = 4
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
0
Number of output integers in intout
201

<!-- source-page: 209 -->
## Page 209

vq—chcells
ESC 1: Inquire Addressable Alpha Cells
vq—chcells( )
Decades
unction=
This escape provides information about the number of horizontal and vertical character cell positions at which the alphanumeric cursor may be
positioned.
Devices required for
All
C binding
int handle, row, columns;
vq—chcells(handle, &row, &columns);
Inputs
contrl[0] = 5
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] =
1
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contri[2] = 0
Number of points in ptsout
contrl[4] =
2
Number of output integers in intout
intout[0]
Number of rows on the screen
(—1 means no cursor addressing)
intout[1]
Number of columns on the screen
(~1 means no cursor addressing)
202

<!-- source-page: 210 -->
## Page 210

vq—exit_cur
ESC 2: Exit Alpha Mode
vq—exit_.cur( )
ech
unction=
This escape would cause the screen device to exit alphanumeric mode and
enter graphics mode if the two modes were separate on the ST. Since they
are not, it clears the screen and turns off the visible cursor.
Devices required for
Screen, Metafile
C binding
int handle;
vq—exit_cur(handle);
Inputs
contrl[0] = 5
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
contrl[5] =
2
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
203

<!-- source-page: 211 -->
## Page 211

v—enter_cur
ESC 3: Enter Alpha Mode
v—enter—cur( )
Opcode=5
Function=3
This escape would cause the screen device to exit graphics mode and enter
alphanumeric mode if the two modes were separate on the ST. Since they
are not, it clears the screen and turns on the visible cursor, which is positioned in the top left corner.
Devices required for
Screen, Metafile
C binding
int handle;
v—enter_cur(handle);
Inputs
contrl[0] = 5
contrl[1] = 0
contrl[3] = 0
contr][5] = 3
handle
contrl[6] = n
Results
contrl(2] = 0
contrl[4] = 0
204
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
Number of points in ptsout
Number of output integers in intout

<!-- source-page: 212 -->
## Page 212

v_curup
ESC 4: Alpha Cursor Up
v_curup(
)
Opcode
=5
Function=4
This escape moves the alpha cursor up one row, unless it’s already at the
top row on the screen.
Devices required for
Screen
C binding
int handle;
v__curup(handle);
Inputs
contrl[0] =
5
Opcode
contrl[1} = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 4
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl(2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
205

<!-- source-page: 213 -->
## Page 213

v—curdown
ESC 5: Alpha Cursor Down
v_curdown( )
Opcode=5
Function=5
This escape moves the alpha cursor one row down, unless it’s already at the
bottom row on the screen.
Devices required for
Screen
C binding
int handle;
v—curdown(handle);
Inputs
contrl[0] = 5
Opcode
contr][1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] =
5
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contr][2] = 0
Number of points in ptsout
contri[4] = 0
Number of output integers in intout
206

<!-- source-page: 214 -->
## Page 214

v_curright
ESC 6: Alpha Cursor Right
v_curright(
)
Opcode=5
Function=6
This escape moves the alpha cursor one column to the right, unless its already at the rightmost column on the screen.
Devices required for
Screen
C binding
int handle;
v—curright(handle);
Inputs
contrl[(0] =
5
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 6
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[{2] = 0
Number of points in ptsout
contrl[4]
=
0
Number of output integers in intout
207

<!-- source-page: 215 -->
## Page 215

v—curleft
ESC 7: Alpha Cursor Left
v—curleft( )
Opcode=5
Function=7
This escape moves the alpha cursor one column to the left, unless it’s already at the leftmost column on the screen.
Devices required for
Screen
C binding
int handle;
v—curleft(handle);
Inputs
contrl[0] = 5
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] =
7
Function ID
handle
contri[6] = n
The (virtual) workstation device handle
Results
contrl[2} = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
208

<!-- source-page: 216 -->
## Page 216

y—_curhome
ESC 8: Home Alpha Cursor
v_curhome( )
Devices required for
Screen
C binding
int handle;
v_curhome(handle);
Inputs
handle
Results
contrl[0] = 5
contrl[1] = 0
contrl[3] = 0
contrl[5] = 8
contrl[6] =n
contr][2] = 0
contri[4] = 0
Opcode=5
Function=8
This escape moves the alpha cursor to the top left position on the screen.
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
Number of points in ptsout
Number of output integers in intout
209

<!-- source-page: 217 -->
## Page 217

v—eeos
ESC 9: Erase To End of Screen
v—eeos( )
Opcode=5
Function=9
This escape clears the screen from the current cursor position to the end of
the screen without moving the cursor.
Devices required for
Screen
C binding
int handle;
v_eeos(handle);
Inputs
contrl[0] = 5
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
conitrl[5] =
9
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contr][2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
210

<!-- source-page: 218 -->
## Page 218

v—eeol
v__eeol( )
7
ESC 10: Erase To End of Line
Opcode=5
Function = 10
This escape clears the screen from the current cursor position to the end of
the line without moving the cursor.
Devices required for
Screen
C binding
int handle;
v_eeol(handle);
Inputs
contrl[0] = 5
contrl[1] = 0
contrl[3] = 0
contrl(5] = 10
handle
contrl[6] = n
Results
contrl[2] = 0
contrl[4] =
0
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
Number of points in ptsout
Number of output integers in intout
211

<!-- source-page: 219 -->
## Page 219

vs—curaddress
ESC 11: Direct Cursor Address
vs_curaddress
Opcode=5
Function=11
This escape moves the cursor directly to any position on the screen. If the
specified position is outside the range of the screen, the cursor moves to the
position on the screen closest to that specified.
Devices required for
Screen
C binding
int handle, row, column;
v—curaddress(handle, row, column);
Inputs
contr][0] = 5
Opcode
contr][1] = 0
Number of points in ptsin
contrl[3] = 2
Number of input integers in intin
contri[5] = 11
~~ Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
row
intin[0]
Row number (1 to maximum of 80 or 40)
column
intin[1}
Column number (1 to 25)
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
212
_

<!-- source-page: 220 -->
## Page 220

v—curtext
v_curtext
ESC 12: Output Alpha Text
Opcode=5
Function= 12
This escape displays a string of text at the current cursor position, and
moves the cursor to the character following the end of the string.
Devices required for
Screen
C binding
int handle;
char *string;
v—curtext(handle, string);
Inputs
handle
string
Results
contrl(0]
contri[1}
contrl[3]
contrl[5]
contrl[6]
intin[0)-[n]
wu
awd
Ses oWw
nN
Opcode
Number of points in ptsin
Number of characters in string
Function ID
The (virtual) workstation device handle
Text string, formatted as 8-bit ASCII characters, with each character set within a
16-bit word
. The first byte of each word
is 0, and the second contains the character
code,
Number of points in ptsout
Number of output integers in intout
213

<!-- source-page: 221 -->
## Page 221

v—rvon
ESC 13: Reverse Video On
v_rvon( )
Opcode=5
Function= 13
This escape causes all subsequent text output to be displayed in reverse
-
video.
Devices required for
Screen
C binding
int handle;
v_rvon(handle);
Inputs
contrl(O] =
5
contrl[1] =
0
contrl[3] = 0
contrl[5] = 13
handle
contrl(6] = n
Results
contr][2] = 0
contr][4] = 0
214
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
Number of points in ptsout
Number of output integers in intout

<!-- source-page: 222 -->
## Page 222

v_rvoff
ESC 14: Reverse Video On
v_rvoff( )
Opcode=5
Function= 14
This escape causes all subsequent text output to be displayed in normal
video.
Devices required for
Screen
C binding
int handle;
v_rvof(handle);
Inputs
contrl[0] = 5
contri[1] = 0
contrl[3}] = 0
contrl(5] = 14
handle
contrl[6] = n
Results
contrl[2] = 0
contrl[4] = 0
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
Number of points in ptsout
Number of output integers in intout
215

<!-- source-page: 223 -->
## Page 223

vq—curaddress
ESC 15: Inquire Cursor Address
vq—curaddress
Opcode=5
Function= 15
This escape returns the current row and column position of the cursor on
the screen.
Devices required for
Screen
C binding
int handle, row, column;
v_curaddress(handle, &row, &column);
Inputs
contri[0] = 5
Opcode
contri[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 15
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] = 0
Number of points in ptsout
contr][4] = 2
Number of output integers in intout
row
intout[0]
Row number (1 to maximum of 80 or 40)
column
intout[1]
Column number (1 to 25)
216
a

<!-- source-page: 224 -->
## Page 224

vq—tabstatus
ESC 16: Inquire Tablet Status
vq—tabstatus( )
Opcode=5
Function= 16
This escape returns the availability of a graphics tablet.
Devices required for
All
C binding
int handle, status;
status = vq_tabstatus(handle);
Inputs
contrl[0] = 5
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 16
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contri[2] = 0
Number of points in ptsout
contri[4] =
1
Number of output integers in intout
status
intout[0]
Tablet status
0 = tablet not available
1 = tablet available
217

<!-- source-page: 225 -->
## Page 225

v—hardcopy
ESC 17: Hard Copy
v_hardcopy( )
Rees
unction =
This escape copies the physical screen to a printer or other hardcopy device.
Devices required for
All
C binding
int handle;
v_hardcopy(handle);
Inputs
contrl[0] = 5
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 17
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2} = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
218

<!-- source-page: 226 -->
## Page 226

v—_dspcur
ESC 18: Place Graphic Cursor
v—dspcur( )
Opcode=5
Function=18
This escape places a graphics cursor at the position indicated.
Devices required for
Screen
C binding
int handle, x, y;
v—dspcur(handle, x, y);
Inputs
handle
x
y
Results
contrl[0| = 5
contrl{1] =
1
contr][3] = 0
contrl[5] = 18
contrl[6] = n
ptsin(0]
ptsin[1]
contr][2] = 0
contrl[4] = 0
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
X coordinate of pixel location where
cursor is to be placed
Y coordinate of pixel location where
cursor is to be placed
Number of points in ptsout
Number of output integers in intout
219

<!-- source-page: 227 -->
## Page 227

v—rmcur
ESC 19: Remove Graphics Cursor
v_rmceur( )
Opcode=5
Function=19
This escape removes the graphics cursor placed on the screen by the last
Place Graphics Cursor call.
Devices required for
Screen
C binding
int handle;
v—rmceur(handle);
Inputs
contrl[0] = 5
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 19
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
0
Number of output integers in intout
220

<!-- source-page: 228 -->
## Page 228

v_form_adv
ESC 20: Form Advance
v_form_adv( )
Opcode=5
Function= 20
Like the Clear Workstation command, this escape sends a form feed command to the printer, but unlike that command, it does not discard the information stored in the print buffer.
Devices required for
Printer
C binding
int handle;
v_form_adv(handle);
Inputs
contr][0] = 5
Opcode
contrl[1] = 0
Number of points in ptsin
contr][3] = 0
Number of input integers in intin
contrl[5] = 20
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contr][2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
221

<!-- source-page: 229 -->
## Page 229

v_output_window
ESC 21: Output Window
v_output_window( )
Opcode=5
Function=21
This escape enables the application to send any designated rectangular
screen area to the printer.
Devices required for
Printer
C binding
int handle, points[4];
v_output_window(handle, points);
Inputs
handle
points[0]
points[1}
points[2]
points[3]
Results
222
contrl(0]
contrl[1]
contrl[3]
contrl[5]
contrl[6]
ptsin(0]
ptsin[1]
ptsin[2]
ptsin[3]
contrl(2]
contrl[4]
0
0
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
X coordinate of left edge of rectangle
¥ coordinate of top edge of rectangle
X coordinate of right edge of rectangle
Y coordinate of bottom edge of rectangle
Number of points in ptsout
Number of output integers in intout

<!-- source-page: 230 -->
## Page 230

v—clear_disp_list
ESC 22: Clear Display List
v_clear_disp_list
Opcode=5
Function = 22
This escape permits the application to request that the printer display list be
cleared.
Devices required for
Printer
C binding
int handle;
v—clear_disp_list(handle)
Inputs
handle
Results
contrl(0]
contrl[1]
contrl[3]
contrl(5]
contr][6] =
Iu
dl
5
0
0
22
n
contrl[2] = 0
contrl[4] = 0
Opcode
Number of points in PTSIN
Length of INTIN array
Function ID
The (virtual) workstation device handle
Number of points in ptsout
Number of output integers in intout
223

<!-- source-page: 231 -->
## Page 231

v_bit_image
ESC 23: Output Bit Image File
v_bit_image( )
Opcode=5
Function= 23
This escape allows the application to print out a bit image file that is stored
in the special VDI screen file format. It provides several page placement and
image scaling options.
Devices required for
Printer
C binding
int handle, aspect, scaling, num_pts, points| ];
char *filename;
v—bit_image(handle, filename, aspect, scaling, num_pts, points);
Inputs
contrl[(0} =
5
Opcode
contrl[1] =
0
No points in ptsin means take rectangle
information from the bit image file.
1
One point in ptsin means use this point as
the upper left corner, and calculate the
lower left from info in the file.
2
Use these points to define the rectangle.
contrl[3] = n
Length of file name + 2
contrl([5] = 23
Function ID
handle
contrl[6] =n
The (virtual) workstation device handle
aspect
intin(0}
Aspect ratio flag:
0 = Ignore aspect ratio
1 = Preserve pixel aspect ratio
2 = Preserve page aspect ratio
scaling
intin[1]
Sealing flag:
0 = Uniform scaling
1 = Separate scaling
filename
intin(2]—[n]
Filename character string, with one character per 16-bit word.
points[0]
ptsin[0]
X position of left edge (optional)
points[1]
ptsin[1]
Y position of top edge (optional)
points[2]
ptsin[2]
X position of right edge (optional)
points[3]
ptsin[3]
Y position of bottom edge (optional)
Results
contr][2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
224

<!-- source-page: 232 -->
## Page 232

v—pline
Polyline
v__pline( )
Opcode=6
This function is used to draw lines between two or more consecutive points,
The points may be the same, in which case a single point is drawn. The last
point is not automatically connected to the first, so in order to draw a box,
five points are required—the last of which should be same as the first.
The output of this function is affected by the general graphics settings
and the line settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Line color (vsl_color)
Line type (vsl_type)
Line width (vsl_width)
Line end style (vsl_ends)
Devices required for
All
C Binding
int handle, num_pts, pointsf ];
v_pline(handle, num_pts, points);
Inputs
contr][0] = 6
Opcode
num__pts
contrl[1] =n
Number of pairs of x,y coordinate line
points to draw
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
points[0]
ptsin(0]
X coordinate of the first point
points[1}
ptsin(1]
Y coordinate of the first point
points[2n—2]
 ptsin[2n—2]
X coordinate of the last point
points[2n—1]
 ptsin[2n—1]
Y coordinate of the last point
Results
contrl[2] =
0
Number of points in ptsout
contri[4] =
0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsl_color( ), Line type (vsl_type)
vslL_width( ), vsl_ends(
)
225

<!-- source-page: 233 -->
## Page 233

v_pmarker
Polymarker
v_pmarker(
)
Opcode=7
This function draws marker, graphics shapes that range from a single point
to box, star and cross shapes.
-—
The output of this function is affected by the general graphics settings
and the marker settings:
Writing mode (vswr_mode)
——
Clipping rectangle (vs_clip)
Marker color (vsm_color)
Marker type (vsm_type)
Marker height (vsm_height)
Devices required for
All
C Binding
int handle, num_pts, points{ ];
v—pmarker(handle, num_pts, points);
Inputs
contrl/0] =
7
Opcode
num_pts
contrl[1] =n
Number of pairs of x,y coordinate points
for marker points to draw
contrl[3] = 0
Number of input integers in intin
handle
contri[6] = n
The (virtual) workstation device handle
points[0}
ptsin(0]
X coordinate of the first point
points(1]}
ptsin[1}
Y coordinate of the first point
points[2n—2]
 ptsin[2n—2]
X coordinate of the last point
points[2n—1)
 ptsin{2n—1)
Y coordinate of the last point
Results
contr][2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
7
See also
vswr_mode( ), vs_clip( ), vsm_color( ), vsm_type( ), vsm_height( )
=
226
—_

<!-- source-page: 234 -->
## Page 234

v_gtext
Text
v—gtext( )
Opcode=8
This function outputs graphics text. No escape characters are recognized by
this function, and even non-printing ASCII characters are drawn if there is
image data for them in the current character set. Text rendering is affected
by the general graphics settings and the text settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Text color (vst_color)
Text font (vst_font)
Text size (vst_height or vst_point)
Baseline rotation (vst_rotation)
Alignment (vst_alignment)
Special effects (vst_effects)
Devices required for
All
C Binding
int handle, x, y;
char *string
v—gtext(handle, x, y, string);
Inputs
contrl[0] =
8
Opcode
contrl[1] =
1
Number of points in ptsin
contrl[3] = n
Number of characters in string
handle
contrl[6] = n
The (virtual) workstation device handle
x
ptsin(0]
X coordinate of the text alignment point
y
ptsin[1]
Y coordinate of the text alignment point
string[0]
intin[0]
First character of text string. Though each
character is an eight-bit value in the C
format, the bindings position each of
these bytes in a separate word in the intin
array. Each member of intin has a high
byte of 0 and a low byte that contains the
ASCII character.
string[n]
intin[n]
Last character of text string.
ptsin[0]
X-coordinate (in NDC/RC units) of position where the text string is to be placed.
ptsin[1]
Y-coordinate (in NDC/RC units) of position where the text string is to be placed.
227

<!-- source-page: 235 -->
## Page 235

v_gtext
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vst_color( ), vst_font( ), vst_height( ),
_
vst_point( ), vst_rotation( ), vst_alignment( ), vst_effects( )
228

<!-- source-page: 236 -->
## Page 236

v__fillarea
Filled Area
v_fillarea(
)
Opcode=9
This function draws a
filled polygon whose shape is outlined by a
series of
points. This polygon may be complex; its lines may cross each other, creating a number of sub-polygons, some of which are filled, others of which are
not. In order to insure that the figure is enclosed, the last point is automatically connected to the first. If the points of the figure are the same, a single
point is displayed if fill outlining is turned on. The rendering of the filled
figure is affected by the general graphics settings and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs—clip)
Fill color (vsf_color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, num_pts, points| ];
v_fillarea (handle, num_pts, points);
Inputs
contrl[0] =
9
Opcode
num_pts
contrl{1] = n
Number of pairs of x,y coordinate points
in ptsin for the polygon
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
points[0]
ptsin(0]
X coordinate of the first point
points[1]
ptsin[1]
Y coordinate of the first point
points[2n—2]
 ptsin{2n—2]
X coordinate of the last point
points[2n—1]
 ptsin{2n—1]
Y coordinate of the last point
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
0
Number of output integers in intout
See also
vswr_mode( ), vs—clip( ), vsf—color( ), vsf_interior( ),
vsf_style( ), vsf_perimeter( ), vq_extend( ) ()
229

<!-- source-page: 237 -->
## Page 237

v_hbar
GDP 1: Bar
v_bar( )
Opcode=11
Function=1
This function draws a filled rectangle. The rendering of the filled figure is affected by the general graphics settings and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf_color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, points[4];
v_bar(handle, points);
Inputs
contrl[0] = 11
 Opcode
contrl[1] = 2
Number of pairs of x,y coordinate points
in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] =
1
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
points[0]
ptsin[0]
X Coordinate of the left edge
points[1]
ptsin[1]
Y Coordinate of the top edge
points[2]
ptsin[2]
X Coordinate of the right edge
points[3]
ptsin{3]
Y Coordinate of the bottom edge
Results
contrl[2] = 0
Number of points in ptsout
contr][4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs—clip( ), vsf_color( ), vsf_interior( ),
vsf_style( ), vsf_perimeter( ) ()
230

<!-- source-page: 238 -->
## Page 238

V—arc
GDP 2: Arc
v_arc( )
Opcode=11
Function =2
Arc draws an arc between any two points on a
circle. Points on the circle are
measured in tenths of a degree, starting at the rightmost point on the circle
and moving counterclockwise. It’s possible to draw an entire circle by specifying the same starting and ending points. This function takes the horizontal
radius parameter that’s passed to it and scales the vertical radius according
to the aspect ratio of the monitor, so the circle looks round.
The output of this function is affected by the general graphics settings
and the line settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Line color (vsl_color)
Line type (vsl_type)
Line width (vsl_width)
Line end style (vsl_ends)
Devices required for
All
C Binding
int handle, x, y, radius, beginangle, endangle;
v—arc(handle, x, y, radius, beginangle, endangle);
Inputs
contrl[0] = 11
Opcode
contrl[1] =
4
Number of points in ptsin
contrl[3] =
2
Number of input integers in intin
contrl[5] =
2
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
beginangle
intin[0]
Starting angle of the arc (0-3600)
endangle
intin{1}
Ending angle of the arc (0-3600)
x
ptsin[0}
X coordinate of center point of arc
y
ptsin[1]
Y coordinate of center point of arc
ptsin[2]
0
ptsin[3}
0
ptsin[4]
0
ptsin[5]
0
radius
ptsin[6]
Horizontal radius of the arc (the vertical
radius is scaled)
ptsin{7]
0
231

<!-- source-page: 239 -->
## Page 239

V—arc
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsl_color( ), Line type (vsl_type)
vsl_width( ), vsl_ends( )
232

<!-- source-page: 240 -->
## Page 240

v—pie
GDP 3: Pie
v_pie( )
Opcode= 11
Function=3
Pie is the filled equivalent of Arc. It draws an arc between any two points
on a
circle, connects the endpoint of that arc to the center of the circle, and
fills the resulting pie wedge with the current fill color and pattern. Points on
the circle are measured in tenths of a degree, starting at the rightmost point
on the circle and moving counterclockwise. This function takes the horizontal radius parameter that’s passed to it and scales the vertical radius according to the aspect ratio of the monitor, so the circle looks round.
The way in which the filled figure is drawn depends on the general
graphics settings and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs—clip)
Fill color (vsf—color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, x, y, radius, beginangle, endangle;
v—pie(handle, x, y, radius, beginangle, endangle);
Inputs
contrl[0] = 11
Opcode
contrl[1] = 4
Number of points in ptsin
contrl[3] = 2
Number of input integers in intin
contrl[5] =
3
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
beginangle
intin(0]
Starting angle of the arc (0-3600)
endangle
intin{1]
Ending angle of the arc (0-3600)
x
ptsin[0]
X coordinate of center point of arc
y
ptsin{[1]
Y coordinate of center point of arc
ptsin(2]
0
ptsin[3]
0
ptsin[4]
0
ptsin[5]
0
radius
ptsin[6]
Horizontal radius of the arc
(the vertical radius is scaled)
ptsin[7]
0
233

<!-- source-page: 241 -->
## Page 241

v__pie
Results
contr][2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsf_color( ), vsf_interior( ),
vsf_style( ), vsf_perimeter( )
234

<!-- source-page: 242 -->
## Page 242

v—_circle
GDP 4: Circle
v_circle( )
Opcode= 11
Function=4
The Circle function draws a
filled circle of a given horizontal radius and
center point. This function scales the vertical radius according to the aspect
ratio of the monitor, so the circle looks round.
The way in which the filled circle is drawn depends on the general
graphics settings and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf—color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, x, y, radius;
v—circle(handle, x, y, radius);
Inputs
contrl[(0] = 11
Opcode
contrl[1] = 3
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 4
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
x
ptsin[0]
X coordinate of center point of circle
y
ptsin(1]}
Y coordinate of center point of circle
ptsin[2]
0
ptsin{3]
0
radius
ptsin[4]
Horizontal radius of the circle
,
(the vertical radius is scaled)
ptsin[5]
0
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsf—color( ), vsf—interior( ),
vsf_style( ), vsf_perimeter( ) ()
235

<!-- source-page: 243 -->
## Page 243

v—ellipse
GDP 5: Ellipse
v—ellipse( )
Ppcode = -
unction=
The Ellipse function draws a
filled ellipse of a given horizontal and vertical
radius and center point. The way in which the filled ellipse is drawn is affected by the general graphics settings and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf_color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, x, y, xradius, yradius;
v—ellipse(handle, x, y, radius, yradius);
Inputs
contrl[0] = 11
Opcode
contrl[i] =
2
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
contrl[5] =
5
Function ID
handle
contri[6] = n
The (virtual) workstation device handle
x
ptsin(0]
X coordinate of center point of ellipse
y
ptsin{1}
Y coordinate of center point of ellipse
xradius
ptsin(2]
Horizontal radius of the ellipse
yradius
ptsin[3]
Vertical radius of the ellipse
Results
»
 contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsf_color( ), vsf_interior( ),
vsf_style( ), vsf_perimeter(
)
236

<!-- source-page: 244 -->
## Page 244

v_ellarc
GDP 6: Elliptical Arc
v_ellarc( )
Opcode= 11
Function=6
Elliptical Arc draws an arc between any two points on an ellipse. Points on
the ellipse are measured in tenths of a degree, starting at the rightmost point
on the circle and moving counterclockwise. It’s possible to draw an entire ellipse by specifying the same point for both the beginning and end. The output of this function is affected by the general graphics settings, and the line
settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Line color (vsl_color)
Line type (vsl_type)
Line width (vsl_width)
Line end style (vsl_ends)
Devices required for
All
C Binding
int handle, x, y, xradius, yradius, beginangle, endangle;
v—arc(handle, x, y, xradius, yradius, beginangle, endangle);
Inputs
contrl[0] = 11
Opcode
contrl[1] =
2
Number of points in ptsin
contrl[3] =
2
Number of input integers in intin
contrl(5] =
6
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
beginangle
intin(0]
Starting angle of the arc (0-3600)
endangle
intin{1]
Ending angle of the arc (0-3600)
x
ptsin(0]
X coordinate of center point of arc
y
ptsin(1}
Y coordinate of center point of arc
xradius
ptsin[2}
Horizontal radius of the arc
yradius
ptsin{3]
Vertical radius of the arc
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr—mode( ), vs_clip( ), vsl_color( ), Line type (vsl_type)
vslL_width( ), vsl_ends( )
237

<!-- source-page: 245 -->
## Page 245

v_ellpie
GDP 7: Elliptical Pie
v—ellpie( )
pecs’ = y
unction=
Elliptical Pie is the filled equivalent of Elliptical Arc. It draws an arc between
any two points on an ellipse, connects the endpoint of that arc to the center
of the ellipse, and fills the resulting pie wedge with the current fill color and
pattern. Points on the ellipse are measured in tenths of a degree, starting at
the rightmost point on the ellipse and moving counterclockwise. The way in
which the filled figure is drawn depends on the general graphics settings
and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf_color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, x, y, radius, yradius, beginangle, endangle;
v_pie(handle, x, y, radius, yradius, beginangle, endangle);
Inputs
contri[(0] = 11
Opcode
contr][1] =
2
Number of points in ptsin
contrl[3] =
2
Number of input integers in intin
contrl[5] =
7
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
beginangle
intin(0]
Starting angle of the arc (0-3600)
endangle
intin(1]
Ending angle of the arc (0-3600)
x
ptsin(0]
X coordinate of center point of arc
ptsin{1]
Y coordinate of center point of arc
xradius
ptsin(2]
Horizontal radius of the arc
yradius
ptsin[3]
Vertical radius of the arc
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
0
Number of output integers in intout
See also
vswr_mode( ), vs—clip( ), vsf—color( ), vsf_interior‘( ),
vsf_style( ), vsf_perimeter( )
238

<!-- source-page: 246 -->
## Page 246

v_rbox
GDP 8: Rounded Rectangle
v_rbox( )
Opcode=11
Function=8
This function draws a rectangle with rounded corners. The output of this
function is affected by the general graphics settings and the line settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Line color (vsl_color)
Line type (vsl_type)
Line width (vsl_width)
Line end style (vsl_ends)
Devices required for
All
C Binding
int handle, points[4];
v_tbox(handle, points);
Inputs
contrl{0] = 11
contrl[1] = 2
contrl[3] =
0
contrl[5] =
8
handle
contrl[6] = n
points[0]
ptsin{0]
points[1]
ptsin[1]
points[2]
ptsin(2]
points[3]
ptsin[3]
Results
contrl[2] = 0
contrl(4] = 0
See also
Opcode
Number of points in ptsin
Number of input integers in intin
Function ID
The (virtual) workstation device handle
X Coordinate of the left edge
Y Coordinate of the top edge
X Coordinate of the right edge
Y Coordinate of the bottom edge
Number of points in ptsout
Number of output integers in intout
vswr_mode( ), vs_clip( ), vsl_color( ), Line type (vsl_type)
vsl_width( ), vsl_ends(
)
239

<!-- source-page: 247 -->
## Page 247

v_tfbox
GDP 9: Filled Rounded Rectangle
v_rfbox( )
Opcode= 11
Function=9
This function draws a
filled rectangle with rounded corners. The appearance
of the rectangle is affected by the general graphics settings and the fill
settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf—color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Fill perimeter outline (vsf_perimeter)
Devices required for
All
C Binding
int handle, points[4];
v_rfbox(handle, points);
Inputs
contrl(0] = 11
Opcode
contrl[1] = 2
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
contrl[5] = 9
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
points(0]
ptsin[0]
X Coordinate of the left edge
points[1]
ptsin(1]
Y Coordinate of the top edge
points[2]
ptsin[2]
X Coordinate of the right edge
points[3]
ptsin{3]
Y Coordinate of the bottom edge
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsf_color( ), vsf_interior‘( ),
vsf_style( ), vsf_perimeter(
)
240

<!-- source-page: 248 -->
## Page 248

v_justified
GDP 10: Justified Graphics Text
v_justified( )
Opcode=11
Function=10
This function outputs a line of graphics text that is both right and left justified. Pixel spaces are added or removed between characters and/or words,
causing the string to be printed in the specified width. No escape characters
are recognized by this function, and even non-printing ASCII characters are
drawn if there is image data for them in the current character set. Text rendering is affected by the general graphics settings and the text settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Text color (vst—color)
Text font (vst_font)
Text size (vst_height or vst_point)
Baseline rotation (vst_rotation)
Alignment (vst_alignment)
Special effects (vst_effects)
Devices required for
All
C Binding
int handle, x, y, length, word_space, char_space;
char *string
v_gtext(handle, x, y, string, length, word_space, char_space);
Inputs
contrl[0] = 11
Opcode
contrl[1] =
2
Number of points in ptsin
contrl[3] = n+2 Number of characters in string plus two
contrl[5] = 10
Function ID
handle
contrl[6] = n
The (virtual) workstation device handle
x
ptsin[0]
X coordinate of the text alignment point
y
ptsin{1]
Y coordinate of the text alignment point
length
ptsin[2]
Requested length of string
ptsin(3]
0
word_space
_intin(0]
Interword spacing flag
0 = Don’t modify spacing
1 = Modify spacing
char_space
intin(1]
Intercharacter spacing flag
0 = Don’t modify spacing
1= Modify spacing
string[0]
intin[2]
First character of text string. Though each
character is an eight-bit value in the C
format, the bindings position each of
these bytes in a separate word in the intin
array. Each member of intin has a high
byte of 0 and a low byte that contains the
ASCII character.
241

<!-- source-page: 249 -->
## Page 249

v__justified
string[n]
intin[n+ 2]
Last character of text string.
Results
contr](2]
0
Number of points in ptsout
contrl[4]
0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vst-color)), vst_font( ), vst_height( ),
vst_point( }, vst_rotation( ), vst_alignment( ), vst_effects(
)
242

<!-- source-page: 250 -->
## Page 250

vst_height
Set Character Height, Absolute Mode
vst_height( )
Opcode= 12
This function sets the graphics text character height, as measured from the
baseline to the top of the character cell, in terms of an absolute pixel value.
It returns information about the height and width of the characters and the
character cell. For proportional fonts, the width returned is that of the widest
character and character cell in the font. If the font height requested is not
available, the VDI selects the next smallest available font size.
Devices required for
All
C Binding
int handle, height, char_width, char_height, cell_width, cell_height;
v_height (handle, height, char_width, char_height,
cell_width, cell_height);
Inputs
contrl[(0] = 12
 Opcode
contrl[1} =
1
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
ptsin{0]
0
height
ptsin{1]}
Requested character height, in pixels
Results
contrl[2] =
2
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
char_width
ptsout(0]
Character width in pixels
char_height
_ ptsout[0]
Character height in pixels
cell_width
ptsout[0]
Cell width in pixels
cell_height
ptsout[0]
Cell height in pixels
See also
vst_points( )
243

<!-- source-page: 251 -->
## Page 251

yst_rotation
Set Character Baseline Vector
vst_rotation( )
Opcode= 13
This function rotates the baseline of graphics text so that subsequent text
characters are printed upside down or up and down rather than left to right.
The Atari ST computers only support rotation of text in increments of 90-
degree angles.
Devices required for
Metafiles
C Binding
int handle, angle, angle_set;
angle_set = vst_rotation(handle, angle);
Inputs
contrl[0] = 13
Opcode
contrl{1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
angle
intin[O] n
The requested angle of rotation
(0, 900, 1800 and 2700 are valid)
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
angle_set
intout(0] n
Angle of rotation for baseline selected
See also
v_gtext( ), v_justified( )
244

<!-- source-page: 252 -->
## Page 252

vs—color
Set Color Representation
vs—color( )
Opcode= 14
This function is used to change the color in the hardware color register
that’s associated with VDI drawing pens (color index). It lets you assign a
Red, Blue, and Green color value to create a particular shade for any VDI
drawing pen (color index). Since the hi-res monitor only supports black and
white, this function does nothing when it is called on a monochrome system.
Devices required for
All
C Binding
int handle, pen, rgb[3];
vs_color(handle, pen, rgb);
Inputs
contrl[0] = 14
Opcode
contrl[i] = 0
Number of points in ptsin
contrl[3] = 4
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
pen
intin(0]
The VDI pen (color index) number associated with the hardware color register to
be changed. Note that pen numbers do
not correspond directly to color register
numbers (for example, pen 7 is not the
same as color register 7). The relationship
between the two is shown in the chart below. For medium-resolution mode, only
pens 0-3 are valid, and pen
1 corresponds
to register 3, as shown in parentheses.
Pen
Register
Default
Number
Number
Color
0
0
White
1
15 (*3M)
Black
2
1
Red
3
2
Green
4
4
Blue
5
6
Cyan
6
3
Yellow
7
5
Low White
9
8
Gray
10
9
Light Red
11
10
Light Green
12
12
Light Blue
13
14
Light Cyan
14
11
Light Yellow
15
13
Light Magenta
245

<!-- source-page: 253 -->
## Page 253

vs—color
rgb[0]
intin[1]
The Red color-brightness value (0-1000)
rgb(1]
intin(2]
The Blue brightness value (0-1000)
rgb[2}
intin[3]
The Green brightness value (0-1000)
Although the VDI uses color levels from
0-1000, currently, the ST hardware supports eight brightness values for each
—
color, 0-7. So the VDI maps its values to
the actual hardware values as follows:
Requested
Actual Value
§ Hardware Register
Value
Set
Color Level
0-70
0
0
71-213
142
1
214-356
285
2
357-499
428
3
500-642
571
4
643-785
714
5
786-928
857
6
929 and up
1000
7
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vsl_color( ), vsf_color( ), vsm—color( ), vst_color(
)
246
—

<!-- source-page: 254 -->
## Page 254

vsl_type
Set Polyline Linetype
vsl_type( )
Opcode= 15
This function sets a line pattern that is used by subsequent line-drawing
routines. It can install one of six preset patterns or an arbitrary 16-bit pattern
set by the programmer. If the pattern number requested is unavailable, pattern 1, a solid line, will be set. Note that patterned lines are unavailable
when the vsl_width(
) function is used to set a line width greater than 1.
These thicker lines always appear as solid.
Devices required for
All
C Binding
int handle, type, type_set;
type_set = vsl_type(handle, type);
Inputs
contrl[0] = 15
 Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
type
intin[0]
Line pattern type
1 = Solid
2 = Long dash
3 = Dot
4 = Dash, dot
5 = Dash
6 = Dash, dot, dot
7 = User-defined
Pattern 7 installs the pattern that has been
set with the Set User-Defined Line Style
Pattern function (vsl_udsty). If no pattern
has been set, the function uses the default
style, a solid line. For an illustration of the
various bit patterns, see Figure 5-2.
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
type_set
intout(0]
See also
vsl_udsty( )
247

<!-- source-page: 255 -->
## Page 255

vsL_width
Set Polyline Line Width
vsL_width( )
Opcode= 16
This command sets the width of the lines produced by subsequent linedrawing operations. On the ST, the line width may be any odd number
from
1 through 39. Requests for even numbers will cause the next-lowest
odd-numbered width to be set. Note that when lines wider than one pixel
are being used, the current line pattern will be ignored, and a solid line will
be drawn.
Devices required for
Metafiles
C Binding
int handle, width, width_set;
width_set = vsl_width(handle, width);
Inputs
contrl[0] = 16
Opcode
contrl[1] =
1
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
width
ptsin[0]
Requested line width in pixels
ptsin{1]
0
Results
contrl[2] =
1
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
width_set
ptsout(0]
Line width that was actually set
ptsout[1]
0
248

<!-- source-page: 256 -->
## Page 256

vsL_color
Set Polyline Color Index
7
vsl_color( )
Opcode=
17
This function sets the hardware color register that will be used for future
line-drawing operations. Note that the color index (pen) number does not
correspond exactly to the color register number. The VDI uses a lookup table
to match the color index to a color register for the color screen. On the
monochrome screen, color 0 is white, the background color; and 1
is black,
__
the foreground color. If the color that was requested is not available, color
index
1 (black) will be selected.
Devices required for
All
C Binding
int handle, color, color_set
color_set = vsl_color(handle, color);
Inputs
conirl[0] = 17
Opcode
contrl[1}] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] =n
The (virtual) workstation device handle
color
intin[0]
The requested color index (pen) number
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
color_set
intout[0]
The color index that was actually set
—
249

<!-- source-page: 257 -->
## Page 257

vsm_type
Set Polymarker Type
vsm.__type( )
Opcode= 18
This function sets the marker shape that will be used by subsequent polymarker operations. There are six preset marker shapes. The first of these, the
dot, is always one pixel in size, and cannot be scaled the way the others
can. If the marker that is requested is unavailable, marker number 3, the asterisk, is selected.
Devices required for
All
C Binding
int handle, shape, shape_set
shape._set = vsm_type(handle, shape);
Inputs
contrl{(0] = 18
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
shape
intin(0]
The marker shape that’s requested
1 = Dot (.)
2 = Plus (+)
3 = Asterisk (*)
4 = Square ([])
5 = Diagonal Cross (X)
6 = Diamond (<>)
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
shape_set
intout[0]
The marker shape that was actually set
250

<!-- source-page: 258 -->
## Page 258

vsm_height
Set Polymarker Height
vsm_height( )
Opcode= 19
This function sets the size of the polymarker shapes 2-6 (shape 1
is always
one pixel in size), There are eight marker sizes available on the ST screen,
ranging from 15 X 11 to 120 X 88. Each of the marker heights set by this
function is an even multiple of 11 (11, 22, 33, and so on). If the requested
height is not available, the next smallest available height is set. Though the
function returns both the height and width of the marker that was actually
set, the C bindings only return the height.
Devices required for
Metafiles
C Binding
int handle, height, height_set;
height_set = vsm_height(handle, height);
Inputs
contrl[(0] = 19
Opcode
contrl{1] =
1
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl(6] = n
The (virtual) workstation device handle
ptsin(0]
0
height
ptsin{1]}
The requested polymarker height
Results
contrl[2] =
1
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
ptsout[0]
Width of the selected polymarker
height_set
ptsout[0]
Height of the selected polymarker
251

<!-- source-page: 259 -->
## Page 259

vsm_—color
Set Polymarker Color Index
vsm_color( )
Opcode= 20
This function sets the hardware color register that will be used for future
polymarker operations, Note that the color index (pen) number does not correspond exactly to the color register number. The VDI uses a lookup table to
match the color index to a color register for the color screen. On the monochrome screen, color 0 is white, the background color; and 1 is black, the
foreground color. If the color that was requested is not available, color index
1 (black) will be selected.
Devices required for
Metafiles
C Binding
int handle, color, color_set
color_set = vsm_—color(handle, color);
Inputs
contrl[0] = 20
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
color
intin(0]
The requested color index (pen) number
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
color_set
intout[0]
The color index that was actually set
252

<!-- source-page: 260 -->
## Page 260

vst_font
Set Text Face
vst_font( )
Opcode=
21
This function selects the font that will be used for subsequent graphics text
output. Font 1 is a built-in system font. All others are disk-based, and must
be loaded using the Load Face operation. The font that you request in this
function is identified by a font index number which you may determine by
using the Inquire Face Name function. Note that in order to use disk-based
fonts on the current version of the ST, the GDOS extension must first be
loaded.
Devices required for
All
C Binding
int handle, fontID, font_set;
font_set = vst_font(handle, fontID);
Inputs
contrl[0] = 21
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
fontID
intin[0]
Font ID number of the font requested
(determined from call vqt_font)
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
font_set
intout[0]
Font ID number that was actually set
See also
vqt_name(
)
253

<!-- source-page: 261 -->
## Page 261

vst_color
Set Graphics Text Color Index
vst_color( )
Opcode
= 22
This function sets the hardware color register that will be used for future
graphics text operations. Note that the color index (pen) number does not
correspond exactly to the color register number. The VDI uses a lookup table
to match the color index to a color register for the color screen. On the
monochrome screen, color 0 is white, the background color; and
1 is black,
the foreground color. If the color that was requested is not available, color
—
index
1 (black) will be selected.
Devices required for
All
C Binding
int handle, color, color_set
color_set = vst_color(handle, color);
Inputs
contrl[(0] = 20
Opcode
contrl[1} =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
color
intin[0]
The requested color index (pen) number
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
color_set
intout[0]
The color index that was actually set
254
—

<!-- source-page: 262 -->
## Page 262

vsf_interior
Set Fill Interior style
vsf_interior( )
Opcode=23
This command determines the type of pattern used for filled-shape output
functions. If the pattern style requested is unavailable, fill style 0 (hollow)
is set.
Devices required for
All
C Binding
int handle, pattern, pattern_set;
pattern_set = vsf_interior(handle, pattern);
Inputs
contrl[0 ]
3
Opcode
contrl[1]
2
0
Number of points in ptsin
1
n
contrl[3]
Number of input integers in intin
handle
contrl/6] =
The (virtual) workstation device handle
pattern
intin[0]
The style of fill pattern requested
0 = Hollow
(Background color, pen 0)
1 = Solid
(Foreground color, fill pen)
2 = Pattern (Dotted)
3 = Crosshatch
4 = User-defined style
User-defined fill style must first be set
with vsf_udpat( ). If no user-defined pattern has been set the default Atari-logo
pattern is used.
Results
contrl(2]
Number of points in ptsout
contrl[4]
Number of output integers in intout
pattern_set
intout[0]
The style of fill pattern actually set
See also
vsf_style( )
255

<!-- source-page: 263 -->
## Page 263

vsf_style
Set Fill Style Index
vsf_style( )
Opcode=24
This function is used to choose a particular fill pattern from those available
for a given fill type. This fill pattern will be used for all subsequent fill operations. Only the Pattern (Dotted) and Crosshatch fill styles offer
a number of
patterns to choose from, so the general pattern style must be set to either of
those in order for this command to have any effect. On the ST screen, the
Pattern (Dotted) fill contains 24 different subpatterns, while the Hatch fill
includes 12.
Devices required for
All
C Binding
int handle, index, index_set;
index_set = vsf_style(handle, index);
Inputs
contrl[0] = 24
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
index
intin[0]
The requested fill index
1-24 for Pattern, 1-12 for Hatch
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
index_set
intout[0]
The fill index actually set
See also
vsf_interior, vsf_color
256

<!-- source-page: 264 -->
## Page 264

vsf_color
Set Fill Color Index
vsf_color( )
Opcode = 25
This function sets the hardware color register that will be used for future fill
operations. Note that the color index (pen) number does not correspond exactly to the color register number. The VDI uses a lookup table to match the
color index to a color register for the color screen. On the monochrome
screen, color 0 is white, the background color; and
1 is black, the foreground
color. If the color that was requested is not available, color index
1 (black)
will be selected.
Devices required for
All
C Binding
int handle, color, color_set
color_set = vsf_color(handle, color);
Inputs
contrl[(0] = 25
Opcode
contrl{1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
color
intin(0]
The requested color index (pen) number
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
color_set
intout[0}
The color index that was actually set
257

<!-- source-page: 265 -->
## Page 265

vq—color
Inquire Color Representation
vq—color( )
Opcode= 26
This function returns either the actual RGB values for a color index (pen), or
the value that was requested when the index was set by vs_color( ). If an
invalid index is selected, a value of —1 is returned in intout(0). This value is
not returned by the C binding.
Devices required for
—_-
Screen, Printer, Metafile
C Binding
int handle, color, flag, rgb[3];
vq—color(handle, color, flag, rgb);
Inputs
contrl[0] = 26
Opcode
contrl][1] = 0
Number of points in ptsin
contr][3] = 2
Number of input integers in intin
handle
contri[6] = n
The (virtual) workstation device handle
index
intin(0]
Color index requested
flag
intin(1]
Inquiry mode flag
0 = Return color value requested
1 = Return color value actually set
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 4
Number of output integers in intout
intout[0]
Color index used
rgb[0}
intout[1]
Red level (0-1000)
rbg{1]
intout[2]
Green level (0-1000)
rgb[2]
intout[3]
Blue level (0-1000)
See also
vs—color( )
258
—_

<!-- source-page: 266 -->
## Page 266

vrq—locator
Input locator, request mode
vrq—locator( )
Opcode= 28
This function waits for a terminating event, such as a keypress or mouse
button press, and returns the position of the mouse pointer. The mouse
pointer is shown at the beginning of this function; it remains visible and follows the mouse until the terminating event, at which time it is hidden. The
ALT-arrow key combination may be used to move the mouse pointer. This
mode of the locator function is chosen by first setting the device to request
mode with the vsin_mode(
) function.
Devices required for
Screen
C Binding
int handle, x, y, x1, y1, term;
vrq_locator(handle, x, y, &x1, &y1, &term);
Inputs
contri[0] = 28
Opcode
contrl{1} =
1
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
x
ptsin[0]
Starting x position of the mouse pointer
y
ptsin[1]
Starting y position of the mouse pointer
Results
contrl[2] =
1
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
term
intout(0]
Terminating event. If a keypress, the
ASCII value of the key pressed. If a button press, 32 for the left button, 33 for the
right button.
x1
ptsout(0]
Ending x position of the mouse pointer
yl
ptsout[1]
Ending y position of the mouse pointer
See also
vsin_mode( ), vsm_locator( )
259

<!-- source-page: 267 -->
## Page 267

vsm_locator
Input Locator, Sample Mode
vsm_locator( )
Opcode=
28
This function returns the current position of the mouse pointer. The mouse
pointer is not shown by this function, so v_show_c(
) may be used to do so.
This mode of the locator function is chosen by first setting the device to
sample mode with the vsin_mode( ) function.
Devices required for
Screen
C Binding
int handle, x, y, x1, y1, term, status;
status = vsm_tocator(handle, x, y, &x1, &y1, &term);
Inputs
contrl[(0] = 28
Opcode
contr][1] =
1
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
x
ptsin[0]
Starting x position of the mouse pointer
y
ptsinj1]
Starting y position of the mouse pointer
Results
contrl[2] =
Number of points in ptsout
1
if mouse pointer coordinates changed
0
if coordinates didn’t change
contr][4] =
Number of output integers in intout
1
if terminating event occurred
0
if no mouse button- or keypress occurred
status
A value that shows if terminating event
occurred and/or if mouse moved. The
binding makes this value equal to contr][2]
| (contrl[4] << 1), so that bit 0 is set if the
mouse moved, and bit
1 is set if a terminating event occurred.
term
intout[0]
Terminating event. If a keypress, the
ASCII value of the key pressed. If a button press, 32 for the left button, 33 for the
right button.
x1
ptsout[0]
Ending x position of the mouse pointer
yl
ptsout{1]
Ending y position of the mouse pointer
See also
vsin_mode( ), vrq_tocator( )
260

<!-- source-page: 268 -->
## Page 268

vrq—valuator
Input Valuator, Request Mode
vrq—valuator( )
Opcode=
29
This function implements a logical device that allows the user to return a
numerical value from 1 to 100. In request mode, the up- and down-arrow
keys are used to increase or decrease the starting value until a terminating
key is pressed. This mode of the valuator function is chosen by first setting
the device to request mode with the vsin_mode(
) function. This function is
not implemented in the current version of the TOS ROMs.
Devices required for
None
C Binding
int handle, begin_value, end_value, term;
vrq_valuator(handle, begin_value, &end_value, &term);
Inputs
contrl[0] = 29
 Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
conirl[6] = n
The (virtual) workstation device handle
begin_value
_intin[0]
The starting valuator value
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 2
Number of output integers in intout
end_value
intout[0]
The value set by the user at time of
termination
term
intout[1]
The ASCII value of the terminating key
See also
vsin_mode( ), vsm—valuator{( )
261

<!-- source-page: 269 -->
## Page 269

vsm__valuator
Input Valuator, Sample Mode
vsm_valuator( )
Opcode= 29
-
This function implements a logical device that allows the user to return a
numerical value from
1 to 100. In sample mode, the function checks
whether the up- or down-arrow keys are currently pressed, thereby increasing or decreasing the starting value. This mode of the valuator function is
chosen by first setting the device to sample mode with the vsin_mode( )
function. This function is not implemented in the current version of the TOS
ROMs.
Devices required for
None
C Binding
int handle, begin_value, end_value, term, status;
vsm__valuator(handle, begin_value, &end_value, &term, &status);
Inputs
contrl[0] = 29
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
begin_value
_intin[0}
The starting valuator value
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
Number of output integers in intout
0
if no value change and no terminator
1
if value changed
2
if terminating keypress occurred
end_value
intout[0]
The value set by the user (if changed)
term
intout[1]
The ASCII value of the terminating key,
if any
See also
vsin_mode( ), vrq_valuator(
)
262
—_

<!-- source-page: 270 -->
## Page 270

vrq—choice
Input Choice, Request Mode
vrq—choice( )
Opcode=
30
This function implements a logical device that allows the user to choose a
number from 1 to 10 via the function keys. In request mode, this function
waits until a key is pressed, and, if a function key is pressed, it returns the
key number. If the terminating event is not a function keypress, the default
choice number is returned. This mode of the choice function is chosen by
first setting the device to request mode with the vsin_mode(
) function. This
function is not implemented in the current version of the TOS ROMs.
Devices required for
None
C Binding
int handle, begin_choice, end_choice;
vrq—choice(handle, begin_choice, &end_choice);
Inputs
contrl[0] = 30
Opcode
contrl{1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] =n
The (virtual) workstation device handle
begin_choice
_ intin[0]
The default choice number
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
end_value
intout[0)
The choice number
See also
vsin_mode( ), vsm_choice( )
263

<!-- source-page: 271 -->
## Page 271

vsm_choice
Input Choice, Sample Mode
vsm_choice( )
Opcode=
30
This function implements a logical device that allows the user to choose a
number from
1 to 10 via the function keys. In sample mode, this function
checks the keyboard, and returns a choice number if one of the function
keys is pressed. This mode of the choice function is chosen by first setting
the device to sample mode with the vsin_mode( ) function. This function is
not implemented in the current version of the TOS ROMs.
Devices required for
None
C Binding
int handle, choice;
vsm_choice(handle, &choice);
Inputs
contrl[0] = 30
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl(2] = 0
Number of points in ptsout
contrl[4] =
Number of output integers in intout
if no function key is pressed
1
if function key is pressed
choice
intout[0]
The function key pressed (if any)
See also
vsin_mode( ), vrq—choice(
)
264

<!-- source-page: 272 -->
## Page 272

vrq—string
Input String, Request Mode
vrq—string( )
Opcode=
31
This function allows the user to enter a string of text characters. In request
mode, each keypress adds an ASCII character (or a 16-bit keycode value) to
the end of the string until the Return key is pressed or the maximum string
length is reached. This mode of the choice function is chosen by first setting
the device to request mode with the vsin_mode(
) function.
Devices required for
Screen
C Binding
int handle, max_length, echo_mode, echo_xy[2];
char string{max_length];
vrq—string(handle, max_length, echo_mode, echo_xy, &string);
Inputs
contrl[0] = 31
Opcode
contri{1] =
1
Number of points in ptsin
contrl[3] =
2
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
max_iength
_intin{0]
The maximum string length. If this length
is specified as a negative number, the absolute value of that number is used as the
length, and the 16-bit keycode value for
each keypress is placed in the string, instead of its 8-bit ASCII value.
echo_mode
intin{1]
Echo mode flag
0 = no echo
1 = echo characters to screen as they
are entered, starting at position echo_xy
(not supported on ST)
echo_xy[0]
ptsin[0]
X coordinate of start of echo text
echo_xy[1]
ptsin(1]
Y coordinate of start of echo text
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = n
Number of string characters in intout
string[0]
intout[0]
First character of text string. Each 8-bit
ASCII value is positioned in the low byte
of a 16-bit intout word. (The high byte is
always zero.) If max_length is negative,
indicating that 16-bit keycodes are to be
used instead of 8-bit ASCII characters, the
C bindings still only copy the low byte of
each character to string. In order to read
the full 16-bit value of each character,
therefore, you must read each one directly
from the intout array:
265

<!-- source-page: 273 -->
## Page 273

vrq_string
string[n— 1]
intout{n— 2]
Last character of text string
See also
vsin_mode( ), vsm_string( )
266

<!-- source-page: 274 -->
## Page 274

vsm_string
Input String, Sample Mode
vsm_string( )
Opcode=31
This function allows the user to enter a string of text characters. In sample
mode, the function tests to see if any key is pressed. If any has been, each
keypress adds an ASCII character (or a 16-bit keycode value) to the end of
the string, until the Return key is pressed, the maximum string length is
reached, or no more keys are pressed. This mode of the choice function is
chosen by first setting the device to sample mode with the vsin_mode( )
function.
Devices required for
Screen
C Binding
int handle, max_length, echo_mode, status, echo_xy[2];
char string[max_length];
status = vsm_string(handle, max_length, echo_mode, echo_xy, &string);
Inputs
contrl[(0] = 31
Opcode
contrl{1] =
1
Number of points in ptsin
contrl[3] =
2
Number of input integers in intin
handle
contrl[6} = n
The (virtual) workstation device handle
max_length
_intin{0}
The maximum string length. If this length
is specified as a negative number, the absolute value of that number is used as the
length, and the 16-bit keycode value for
each keypress is placed in the string, instead of its 8-bit ASCII vlaue.
echo__mode
intin{1]
Echo mode flag
0 = no echo
1 = echo characters to screen as they
are entered, starting at position
echo_xy (not supported on ST)
echo_xy[0]
ptsin[0]
X coordinate of start of echo text
echo_xy[1]
ptsin[1]
Y coordinate of start of echo text
Results
contrl[2] =
0
Number of points in ptsout
status
contrl[4] =n
Number of string characters in intout
0 = keypress data is available
>0 = number of characters gathered
string{0]
intout[0]
First character of text string (if any). Each
8-bit ASCII value is positioned in the low
byte of a 16-bit intout word. (The high
byte is always zero.) If max_length is negative, indicating that 16-bit keycodes are
to be used instead of 8-bit ASCII characters, the C bindings still only copy the
267

<!-- source-page: 275 -->
## Page 275

vsm__string
low byte of each character to string. In order to read the full 16-bit value of each
character, therefore, you must read each
one directly from the intout array
string[n — 1]
intout[n— 1]
Last character of text string
See also
vsin_mode( ), vrq_string(
)
268

<!-- source-page: 276 -->
## Page 276

vswr_mode
Set Writing Mode
vswr—mode( )
Opcode= 32
This function sets the writing mode, which affects how all subsequent drawing operations will be performed. Not only may a VDI drawing operation replace an existing background picture, but it may also be combined with that
background in various ways. Four drawing modes are supported: Replace,
Transparent, Exclusive OR (XOR), and Reverse Transparent. The writing
mode affects marker, line, fill, and graphics-text operations.
Devices required for
Screen, Printer, Metafile
C Binding
int handle, mode, mode_set;
mode_set = vswr_mode(handle, mode);
Inputs
contrl[0] = 32
Opcode
contri{1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
mode
intin(0]
Writing mode requested
1 = Replace
Both the
1 and the 0 bits in the
graphics object replace the background (1’s with current foreground
color, 0’s with color 0).
2 = Transparent
Only the
1 bits in the graphics object
replace the background (with current
foreground color)
3 = XOR
The 1 bits in the graphics object are
colored with the complement of the
current background color
4 = Reverse Transparent
Only the 0
bits in the graphics object
replace the background (with current
foreground color)
If number requested is out of range, number 1 (Replace) is selected.
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
mode_set
intout[0}
Writing mode actually selected
269

<!-- source-page: 277 -->
## Page 277

vsin_mode
Set Input Mode
vsin_mode( )
Opcode=
33
This function is used to set any of the four logical input devices (string, valuator, locator, or choice) to request or sample mode. The proper mode
should be set before using any of these devices. This function returns the
mode that was actually set in inout[0], but the C bindings do not make this
information available in a C variable.
Devices required for
Screen
C Binding
int handle, device, mode;
vsin_mode(handle, device, mode);
Inputs
contrl[0] = 33.
Opcode
contrl[{1] = 0
Number of points in ptsin
contrl[3] = 2
Number of input integers in intin
handle
contri[6] = n
The (virtual) workstation device handle
device
intin[0]
Logical input device
1 = Locator
2 = Valuator
3 = Choice
4 = String
mode
intin{1]
Input mode for that device
1 = Request
2 = Sample
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
intout[0]
Input mode selected
270

<!-- source-page: 278 -->
## Page 278

vql_attributes
Inquire Current Polyline Attributes
vql_attributes(
)
Opcode
= 35
This function returns information about the settings that affect line-drawing
operations, including line-drawing pattern, line width, color, end styles and
writing mode. The C binding does not return the information about the end
styles (intout[3]~inout(4]) in a C variable.
Devices required for
All
C Binding
int handle, settings[4];
vql_attributes(handle, settings);
Inputs
contrl[0] = 35
Opcode
contrl{1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2} =
1
Number of points in ptsout
contrl[4] = 5
Number of output integers in intout
settings[0]
intout[0]
Line type setting
settings[1]
intout[1]
Line-drawing pen (color index)
settings{2]
intout[2}
Writing mode
intout[3]
End style of first point of line
intout[4]
End style of last point of line
settings[3]
ptsout(0]
Line width setting
ptsout[1]
0
See also
vsl_type( ), vsl_width( ), vsl_color( ), vsl_ends( ), vswr_mode{ )
271

<!-- source-page: 279 -->
## Page 279

vqm_attributes
Inquire Current Polymarker Attribute
vqm_attributes( )
Opcode=
36
This function returns information about the settings that affect marker drawing operations, including marker type, marker height, marker width, marker
color, and writing mode. The C binding does not return the information
about the marker width (ptsout[0]) in a C variable.
Devices required for
All
C Binding
int handle, settings[4];
vqm_attributes(handle, settings);
Inputs
contrl(0] = 36
Opcode
contrl[1] = 0
Number of points in ptsin
contr][3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] =
1
Number of points in ptsout
contrl[4] =
3
Number of output integers in intout
settings[0]
intout[0]
Marker type setting
settings[1]
intout[1]
Marker drawing pen (color index)
settings[2]
intout[2]
Writing mode
settings(3]
ptsout(1]
Marker height setting (in pixels)
See also
vsm_type( ), vsm_height( ), vsm_color( ), vswr_mode( )
272

<!-- source-page: 280 -->
## Page 280

vqf_attributes
Inquire Current Fill Area Attributes
vqf_attributes( )
Opcode
= 37
This function returns information about the settings that affect area fill operations, including interior style, fill style index, fill color, perimeter outlining,
and writing mode. The C binding does not return the information about perimeter outlining (intout[4]) in a C variable.
Devices required for
All
C Binding
int handle, settings[4];
vqf_attributes(handle, settings);
Inputs
contri[0] = 37
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
5
Number of output integers in intout
settings[0]
intout[0]
Area fill interior style setting
settings(1]
intout[1]
Area fill drawing pen (color index)
settings[2]
intout[2]
Area fill style index
settings[3]
intout[3]
Writing mode
intout[4]
Perimeter outlining status
See also
vsf_interior( ), vsf_style( ), vsf_color( ), vsf_perimeter( ), vswr_mode( )
273

<!-- source-page: 281 -->
## Page 281

vqt_attributes
Inquire Current Graphics Text Attributes
vqt_attributes( )
Opcode
= 38
This function returns information about the settings that affect graphics-text
operations, including current text face, color, baseline rotation, alignment,
character and cell size, and writing mode.
Devices required for
All
C Binding
int handle, settings(10];
vqt_attributes(handle, settings);
Inputs
contrl[0] = 38
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] =
2
Number of points in ptsout
contrl[4] =
6
Number of output integers in intout
settings[0]
intout(0]
Current graphics-text face (font id)
settings(1]
intout[1]
Graphics-text pen (color index)
settings(2]
intout[2]
Angle of rotation of text baseline
(in tenths of degrees, 0-3600)
settings[3]
intout[3]
Horizontal alignment setting
settings[4]
intout[4]
Vertical alignment setting
settings[5]
intout[5]
Writing mode
settings|[6]
ptsout[0]
Character width
settings[7]
ptsout[1]
Character height
settings(8]
ptsout[2]
Character cell width
settings[9]
ptsout[3]
Character cell heigth
See also
vst_font( ), vst_height( ), vst_point( ), vst_color( ), vsl_alignment,
vst_rotation, vswr_mode( }
274

<!-- source-page: 282 -->
## Page 282

vst_alignment
Set Graphics Text Alignment
vst_alignment
Opcode=39
This function controls the horizontal and vertical alignment points for
graphics text. The horizontal alignment determines whether the text string
will be centered or left- or right-justified. The vertical alignment determines
whether the y coordinate of the text placement point refers to the character
baseline, half line, ascent line, bottom line, descent line, or top line. The default alignment makes the graphics-text position the baseline of the leftmost
character in the string.
Devices required for
All
C Binding
int handle, halign, valign, hresult, vresult;
vst_alignment(handle, halign, valign, &hresult, &vresult);
Inputs
contrl{0] = 39
Opcode
contri{1] = 0
Number of points in ptsin
contrl[3] =
2
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
halign
intin(0]
The horizontal alignment requested
0 = Left-justified (default)
1 = Centered
2 = Right-justified
valign
intin(1]
The vertical alignment requested
0 = Baseline (default)
1 = Half line
2 = Ascent line
3 = Bottom line
4 = Descent line
5 = Top line
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
2
Number of output integers in intout
hresult
intout[0]
The horizontal alignment actually set
vresult
intout[1]
The vertical alignment actually set
275

<!-- source-page: 283 -->
## Page 283

v—opnvwk
Open Virtual Workstation
v_opnywk( )
Opcode= 100
This function opens a
virtual workstation that allows the application to
share the physical screen device with other tasks. Each virtual workstation
has access to the full screen, but its graphics settings are maintained separately from all of the others. The screen device drivers are part of the TOS
ROMs, so they do not have to be loaded in from disk when a virtual workstation is opened. But if you wish to use disk-loaded fonts with your virtual
workstation, they must be properly identified in the ASSIGN.SYS file, and
the GDOS must be loaded. Like Open Workstation, this command allows
you to make initial settings for a number of graphics output functions. But
note that, unlike Open Workstation, the handle parameter does double duty
for this call. As an input, it should be set to the value of the current screen
device handle, which can be found by using the AES call graf_handle( ).
Upon return from this call, the handle parameter contains the virtual workstation’s device handle.
Devices required for
Screen
C Binding
int handle, work_in[12], work_out[57];
v—opnwk(work_in, &handle, work_out);
Inputs
contrl[0] = 100
Opcode
contri[1] = 0
Number of points in ptsin
contrl[3] = 11
Number of input integers in intin
handle
contrl[6] = n
The physical screen device handle
(obtained from graf_handle(
) call)
The initial graphics output settings for the virtual workstation are specified by the contents of the intin array (which the bindings take from
work_in] ]).
work_in{0]
intin(0]
Screen Device ID (from ASSIGN.SYS file)
01
Default screen
02
Lo-res color
03
Medium-res color
04
Hi-res monochrome
05-10 Reserved for Atari expansion
work_in[1]
intin{1]
Line drawing pattern [vsl_type( )]
work_in[2]
intin[2]
Line pen number [vsl_color( )]
work_in[3]
intin{3]
Marker type [vsm_type( )]
work_in[4]
intin(4]
Marker pen number [vsm_color{( )|
work_in[5]
intin[5]
Text font [vst_font( )]
work_in[6]
intin[6]
Text pen number [vst_color( )]
work_in{7]
intin[7]
Fill pattern type [vsf_interior( )]
work_in[8]
intin[8]
Fill pattern index [vsf_style( )]
276

<!-- source-page: 284 -->
## Page 284

v—opnvwk
work_in[9]
work_in[10]
Results
handle
intin[9]
intin[10]
contrl[2]
contrl[4]
contrl[6]
tow
dl
6
45
n
Fill pen number [vsf_color( )]
NDC to RC transformation flag
0 = Use Normalized Device
Coordinates
1 = Reserved for future use
2 = Use Raster Coordinate system
Number of points in ptsout
Number of output integers in intout
The device handle for this device
(0 if device was not opened)
The results returned in the intout and ptsout arrays give a wide range of
information about the output capabilities of the device.
work_out(0]
work_out[1]
work_out[2]
work_out[3]
work_out[4]
work_out[5]
work_out[6]
work_out[7]
work_out[8]
work_out{9]
work_out{10]
intout(0]
intout[1]
intout[2]
intout[3]
intout[4]
intout[5]
intout[6]
intout{7]
intout([8]
intout(9]
intout[10]
Maximum horizontal coordinate value (in
pixels)
(medium-res & hi-res = 639, lo-res =
319)
Maximum Max. vertical coordinate value
(in pixels)
(hi-res = 399, medium-res & lo-res =
199)
Device Coordinate units flag
(1 = device doesn’t support precise
scaling)
All ST screens return 0, showing that they
support precise scaling
Width of one pixel in microns
(1/1000’s of a millimeter)
For display screens, horizontal component
of aspect ratio. The values returned are:
hi-res = 372, medium-res = 169, lo-res
= 338
Height of one pixel in microns
For display screens, vertical component of
aspect ratio. All screens return 372.
Number of text font heights
(0 = continuous scaling)
There are 3 text heights in the system
font, each of which can be printed double
high.
Number of line patterns (7)
Number of line widths
(All screens return 0—continuous scaling)
Number of marker patterns (6)
Number of marker sizes (8)
(0 = continuous scaling)
Number of text fonts supported by the
device
Only one system font is available in ROM
277

<!-- source-page: 285 -->
## Page 285

v_opnvwk
work_out[11]
work_out[12]
work_out[13]
work_out[14]
work_out[15]
to
work_out[24]
work_out[25]
to
work_out[34]
work_out[35]
278
intout[11]
intout[12]
intout[13]
intout[14]
intout(15]
to
intout(24]
intout[25}
to
intout[34]
intout[35]
Number of pattern fill styles (24)
Number of crosshatch fill styles (12)
Number of drawing pen colors available
(the number of colors that can be displayed by the device at the same time)
hi-res = 2, medium-res = 4, lo-res = 16
Number of Generalized Drawing
Primitives
(GDPs)—how many of the 10 basic drawing commands are supported (all 10 on
the ST)
This part of the array holds a sequential
list of code numbers for the first 10 GDPs
supported. Each element holds one of the
following code numbers:
1 = Filled Rectangle or Bar (v_bar)—fill
2 = Circle Segment or Arc (v_arc)—line
Filled Pie Slice (v_pieslice)—fill
Filled Circle (v_circle)—fill
= Filled Ellipse (v_ellipse)fill
= Elliptical Are (v_ellarc)—line
Filled Elliptical Pie (v_ellpie)—fill
Rounded Rectangle (v_rbox)—line
= Filled Rounded Rectangle
(v_rfbox)—fill
Justified Text (v_justified)—text
End of list
I
ll
WOON
AD GS
W
10
This part of the array holds a sequential
list of code numbers showing what category of graphics operation is performed
by of each of the supported GDPs. This
indicates what kind of graphics settings
affects each of the supported commands.
Each element holds one of the following
code numbers:
0 = Line drawing
1 = Marker drawing
2 = Graphics text
3 = Filled area
4 = No setting
The graphics category for each function
on the ST can be found in the table of
functions, above, at the end of each entry.
Color availability flag
0 = Device is not capable of color output
1 = Device is capable of color output
ST shows 0 for mono screen,
1 for
color

<!-- source-page: 286 -->
## Page 286

v—opnywk
work_out{36]
work_out[37]
work_out[38]
work__out[39]
work_out[40]
work_out[41]
work_out[42]
work_out[43]
work_out[44]
work_out[45]
work_out[46]
work_out[47]
intout(36]
intout[37]
intout[38]
intout[39]
intout[40]
intout[41]
intout[42]
intout[43]
intout[44]
ptsout(0]
ptsout[1]
ptsout[2]
Text rotation availability flag
0 = Device is not capable of text rotation
1 = Device is capable of text rotation
ST shows 1
for all res modes
Area fill availability flag
0 = Device isn’t capable of area fill
1 = Device is capable of area fill
ST shows 1
for all res modes
Cell array function availability flag
0 = Device can’t perform cell array
function
1 = Device can perform cell array
function
ST shows 0
for all res modes
Total number of color choices available in
the palette
0 = More than 32767 colors available
1 = Monochrome
2~-32767 = Actual number of colors
available
ST hi-res =
2, medium-res & lo-res
= 512
Input devices available for the locator
function
1 = Keyboard only
2 = Keyboard and mouse
ST shows 2
for all res modes
Input devices available for the valuator
function
1 = Keyboard
2 = Other device
ST shows 1
for all res modes
Input devices available for the choice
function
1 = Function keys on keyboard
2 = Some other key pad
ST shows 1
for all res modes
Input devices available for the string input
function
1 = keyboard
ST shows 1
for all res modes
Workstation type
Output only
Input only
Input and output
Reserved for future use
Metafile output
ST shows 2
for all res modes
Minimum character width (5)
Minimum character height (4)
Maximum character width (7)
WNP
O
tu
wt
dd
279

<!-- source-page: 287 -->
## Page 287

v—opnvwk
work_out[48]
_ ptsout[3]
Maximum character height (13)
work_out[49]
_ ptsout[4]
Minimum line width (1)
work_out[50]
— ptsout[5]
0
work_out[51]
— ptsout[6]
Maximum line width (40)
work_out[52]
 ptsout[7]
0
work_out[53]
 ptsout[8]
Minimum marker width (15)
work_out[54]_—_
ptsout[9]
Minimum marker height (11)
work_out[55]_—_
ptsout[11]
Maximum marker width (120)
work_out[56]
 ptsout[12]
Maximum marker height (88)
_—
See also
v—clswk( ), v_opnwk( ), v_clsvwk( )
280
7

<!-- source-page: 288 -->
## Page 288

v—clsvwk
Close Virtual Workstation
v—clsvwk( )
Opcode= 101
This call is used to terminate output to a virtual workstation and release its
environment space.
Devices required for
Screen
C Binding
int handle;
v_clsvwk(handle);
Inputs
contrl[0] = 101
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3} =
0
Number of input integers in intin
handle
contrl[6] = n
The workstation device handle
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
v—opnvwk( ), v_opnwk{( ), v_clswk( )
281

<!-- source-page: 289 -->
## Page 289

vq—extnd
Extended Inquire
vq—extnd( )
Opcode= 102
This function returns either the same information about about a graphics
output device as the Open Workstation and Open Virtual Workstation calls,
or some additional information about the device’s output capabilities.
Devices required for
All
C Binding
int handle, info_flag, work_out[57];
v_opnwk(work_in, info_flag, work_out);
Inputs
contrl[0] = 102
Opcode
contrl{1} =
0
Number of points in ptsin
contrl(3} =
1
Number of input integers in intin
contrl[6] = n
The (virtual) workstation device handle
info_flag
intin{0}
Type of information flag
0 = Open Workstation values
1 = Extended Inquire values
Results
contrl[2]
6
Number of points in ptsout
contr][4]
45
Number of output integers in intout
The results returned in the intout and ptsout arrays give a wide range of
information about the output capabilities of the device. If info_flag was set
to 0, these values are the same as those returned by the Open Workstation
or Open Virtual Workstation calls. (See v_opnwk(
) and v_opnvwk(
) for
more details.) If info_flag is set to 1, the following information is returned.
Note that 6 points and 45 integers are always returned, even though many
of these values are undefined when the information type flag is set for Extended Inquire.
work_out[0]
— intout[0]
Type of screen display
0 = This device doesn’t have a screen
1 = Separate alphanumeric and graphics
controllers, and separate display
screens
2 = Separate alpha and graphics controllers, with a common display screen.
3 = Common alpha and graphics controller, with separate display memory.
4 = Common alpha and graphics controller, common display memory. (The
ST display is this type.)
work_out{1]
—_intout[1]
Number of background colors available
(on the ST, the same as number of colors
in palette—512 in color,
1 in
monochrome.)
282

<!-- source-page: 290 -->
## Page 290

vq—extnd
work_out[2]
work_out[3]
work_out/[4]
work_out(5]
work_out[6]
work_out[7]
work_out[8]
work_out[9]
work_out[10]
work_out[11]
work_out[12]
work_out{13]
work_out{14]
work_out[15]
intout[2]
intout[3]
intout|[4]
intout[5]
intout[6]
intout[7]
intout[8]
intout[9]
intout[10]
intout[11]
intout{12]
intout[13]
intout[14]
intout(15]
Number of text special effects supported
(31 on the ST, since 5 effects can be combined in that many ways).
Raster scaling availability flag
0 = Scaling of rasters not supported
(as is the case on the ST)
1 = Raster scaling supported
Number of color bit planes
(monochrome= 1, medium-res=2, lores=4)
Color palette lookup table flag
0 = Lookup table supported (as on color
screens, where VDI drawing pen index numbers are different from hardware color register numbers)
1 = Lookup table not supported (as on ST
monchrome screen)
Performance factor, the number of 16
16 raster operations that can be performed
per second (1000 for machines without
blitter chip)
Contour fill capability flag
0 = Contour fill not supported
(All ST screens support contour fill, and
return a value of 1)
Character baseline rotation flag
0 = text characters cannot be rotated
1 = characters can be rotated in 90—degree increments only (all ST screens)
2 = Characters can be rotated at any
angle
Number of writing modes available (4)
Highest input mode available
0 = no input
1 = request mode
2 = sample mode (all ST screens)
Text alignment capability flag
(all ST screens =
1, text can be
aligned)
Inking capability flag
(all ST screens = 0, device can’t ink)
Rubberband line capability flag
0 = no rubberband lines (all ST
screens)
1 = rubberband lines only
2 = rubberband lines and rectangles
Maximum number of points for Polyline,
Polymarker, or Filled Area (128)
Maximum number of integers in intin
(all ST screens = —1, no maximum)
283

<!-- source-page: 291 -->
## Page 291

vq—extnd
work_out[16]
work_out[17]
work_out[18]
work_out[19]
to
work_out[44]
work_out[45]
to
work_out[56]
See also
intout[16}
intout[17]
intout[18]
intout[19]
to
intout[44]
ptsout(0]
to
ptsout[11]
v—opnwk( ), v_opnvwk( )
284
Number of mouse buttons (2)
Wide line pattern capability flag
0 = No patterns for wide lines
(all ST screens)
1 = wide lines can use line pattern
Drawing modes for wide lines (0)
Reserved for future use
Reserved for future use

<!-- source-page: 292 -->
## Page 292

v—contourfill
Contour Fill
v—contourfill
Opcode= 103
This function is used to fill an enclosed polygon with the current fill pattern
and color. Filling proceeds in one of two modes. In outline mode, the fill
spreads from an initial point in all directions, until it comes to an outline of a
given color. In color mode, the fill spreads from the initial point until it reaches
a color other than that contained in the initial point. The way in which the
polygon is filled is affected by the general graphics settings and the fill settings:
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf_color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
Devices required for
Metafiles
C Binding
int handle, x, y, pen;
v—contourfill(handle, x, y, pen)
Inputs
contrl[0] = 103
Opcode
contrl(1] =
1
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
pen
intin[0]
Color index for polygon outline. If this
value is negative, color mode is used
rather than outline mode.
x
ptsin[0}
Horizontal coordinate of initial point
y
ptsin{1]}
Vertical coordinate of initial point
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsf_color( ), vsf_interior( ), vsf_style( )
285

<!-- source-page: 293 -->
## Page 293

vsf_perimeter
Set Perimeter Fill Visibility
vsf_perimeter( )
Opcode= 104
This funtion is used to turn fill outlining on or off. When perimeter visibility
is on, a filled-shape drawing operation outlines the filled shape with a solid
line drawn in the current fill color.
Devices required for
All
C Binding
int handle, vis_flag;
vis_set = vsf_perimeter(handle, vis_flag);
Inputs
contrl[0] = 104
Opcode
contrl[1} = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] =n
The (virtual) workstation device handle
vis_flag
intin[0]
Visibility flag
0 = no outline drawn
1 = outline is visible
Results
contrl[2] =
0
Number of points in ptsout
contri[4] =
1
Number of output integers in intout
vis_set
intout[0]
Visibility mode selected
286

<!-- source-page: 294 -->
## Page 294

v_get_pixel
Get Pixel
v_get_pixel( )
Opcode= 105
This function returns the VDI color index and the ST color register number
_
for a particular point on the screen.
Devices required for
None
C Binding
int handle, x, y, register, pen;
v—get_pixel(handle, x, y, register, pen);
Inputs
contrl[0] = 105
Opcode
contrl[1] =
1
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
x
ptsin[0]
Horizontal coordinate of point
y
ptsin[1}
Vertical coordinate of point
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
2
Number of output integers in intout
register
intout[0]
Actual hardware color register used to
color the point.
pen
intout[1]
VDI drawing pen (color index) used to
color the point
See also
vs—color( )
—_
287

<!-- source-page: 295 -->
## Page 295

vst_effects
Set Graphics Text Set Special Effects
vst_effects( )
Opcode= 106
This function is used to designate which special effects will be used for printing
graphics text. Text can be rendered as thickened (bold), light intensity (grayed
or ghosted), skewed (italics), underlined, outlined, or any combination of these
effects.
Devices required for
All
C Binding
int handle, effects, effects_set;
effects_set = vst_effects(handle, effects);
Inputs
contrl[0] = 106
Opcode
contrl[1] = 0
Number of points in ptsin
contr][3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
effects
intin[0}
Special effects setting. Each effect is described in a different bit of this word. Possible effects are:
Bit
Value
Effect
0
1
Thickened (bold)
1
2
Light intensity (ghosted/grayed)
2
4
 Skewed (italics)
3
8
Underlined
4
16
Outlined
5
32
Shadow (not supported on ST)
To combine effects, add the value of the
desired effects together (for example, a
value of 10 indicates Underline (8) and
light intensity (2) will be used together).
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
effects_set
intout([0]
Effects actually selected
288

<!-- source-page: 296 -->
## Page 296

vst_point
Set Character Cell Height, Points Mode
vst_point( )
Opcode= 107
This command is used to set the character size of graphics text using points,
a printing measurement equal to 1/72 inch. The character height requested
encompasses the entire character cell, which may include some blank space
at the top and bottom of the character. Since all point sizes will not be available for any given font, the VDI tries to match the requested size with the
next smallest available font size. The function returns information about the
point size selected and the character size and cell size in pixels.
Devices required for
All
C Binding
int handle, point, charw, charh, cellw, cellh, point_set;
point_set = vst_point(handle, point, &charw, &charh, &cellw, &celih);
Inputs
contrl[0] = 107
Opcode
contrl[1] = 0
Number of points in ptsin
contrl(3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
points
intin[0}
Character cell height (in points)
Results
contrl[2] =
2
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
point_set
intout[0]
Cell height selected (in points)
charw
ptsout(0]
Character width selected (in pixels)
charh
ptsout[1]
Character height selected (in pixels)
cellw
ptsout[2]
Cell width selected (in pixels)
cellh
ptsout([3]
Cell height selected (in pixels)
See also
vst_height( )
289

<!-- source-page: 297 -->
## Page 297

vsL_ends
Set Polyline End Styles
vsl_ends( )
Opcode= 108
This function is used to specify how the ends of lines produced by the linedrawing functions will appear. Either end of a line—or both ends—may be
squared off (the default), rounded, or have an arrowhead attached. Note that
rounding off the end of line really only affects lines that are more than a few
pixels wide. If the style requested by this call is not available, the squared end
style (0) is selected.
Devices required for
All
C Binding
int handle, begin, end;
vsl_ends(handle, begin, end);
Inputs
contrl[0] = 108
Opcode
contr][1] = 0
Number of points in ptsin
contrl[3] = 2
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
begin
intin[0]
End style for the beginning point
end
intin{1]
End style for the endpoint of the line
0 = Squared (default)
1 = Arrow
2 = Rounded
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
290

<!-- source-page: 298 -->
## Page 298

vro_cpyfm
Copy Raster, Opaque
vro_cpyfm( )
Opcode= 109
This function is used to copy a rectangular image from one area of memory
to another. The source area, the destination area, or both may in display
memory. The source area may overlap the destination area; this function
will copy in the correct direction for preserving the source image. The image
may be copied exactly, or it may be combined in various ways with existing
image data in the destination area.
The VDI uses a data structure called
a Memory Form Definition Block
(MFDB) to describe the source and destination memory areas. This data
structure contains information about the memory location of image data, the
size of the image in pixels and memory words, the number of color planes,
and format of the image, either standard (each color bit plane separate), or
ST-specific (color planes interleaved into one large bit plane). For the purposes of this function, the source and destination forms must both be in STspecific format.
Devices required for
Screen
C Binding
int handle, mode, points(8];
struct fdbstr
{
int
*fd_addr;
/* pointer to image data area */
int
fd_w;
/* image width in pixels */
int
fd_h;
/* image height in pixels */
int
fd_wdwidth;
/* image width in words */
int
fd_stand;
/* standard format flag */
int
fd_nplanes;
/* number of color bit planes */
int
fd_rt, fd_r2, fd_r3;
/* reserved for future use */
}source, destination;
vro_cpyfm (handle, mode, points, &source, &destination);
Inputs
contrl[(0] = 109
Opcode
contrl[1}] = 4
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
&source
contri(7-8]
Long-word address of source MFDB
&destination
—_contrl[9-10]
Long-word address of destination MFDB
mode
intin[0]
Logic operation used to combine the
source image with the desination. The
logic operations are described below,
using the symbol S
to refer to the source
image, D to refer to the starting destination image, and D1 to refer to the resulting destination image:
291

<!-- source-page: 299 -->
## Page 299

vro_cpyfm
Mode No.
WOON AOS WNHH ©
points[0}
points[1]
points[2]
points[3]
points[4}
points[5]
points[6]
points[7]
Results
292
Logic Operation
Description
D1 =
Clear destination block (all 0’s)
_
D1 = S ANDD
D1 = S AND (NOT D)
D1 =
Replace mode
D1 = (NOT S) AND D_sErase mode
—
D1 =D
Destination unchanged
D1 = S XORD
XOR mode
D1 =SORD
Transparent mode
D1 = NOT (S OR D)
~
D1 = NOT (S XOR D)
D1 = NOTD
D1 = S OR (NOT D)
D1 = NOTS
D1 = (NOT S) ORD
Reverse transparent mode
D1 = NOR (S AND D)
D1 =
1
Fill destination block (all 1’s)
ptsin[0]
Left edge of source rectangle
ptsin[1]
Top edge of source rectangle
ptsin[2]
Right edge of source rectangle
ptsin[3}
Bottom edge of source rectangle
ptsin[4]
Left edge of destination rectangle
ptsin{5]
Top edge of destination rectangle
ptsin[6]
Right edge of destination rectangle
ptsin[7]
Bottom edge of destination rectangle
contrl[2] = 0
Number of points in ptsout
contrl{[4] = 0
Number of output integers in intout

<!-- source-page: 300 -->
## Page 300

vr_trn_fm
Transform Form
vr__trn_fm( )
Opcode= 110
This function is used to change
a Memory Form Definition Block whose image data is in standard format (each color bit plane separate) to ST-specific
format (all color bit planes interleaved), or vice versa.
The function converts the number of bit planes specified in the source
form to the opposite format of that specified in the source form. It changes
the format flag in the destination form, but does not change any other fields
of the destination form. Note that the source and destination forms may be
the same (known as an in-place transformation). Transforming a large form
in place may be significantly slower than using two separate forms.
Devices required for
Screen
C Binding
int handle;
struct fdbstr
{
int
*fd_addr;
/* pointer to image data area */
int
fd_w;
/* image width in pixels */
int
fd_h;
/* image height in pixels */
int
fd_wdwidth;
/* image width in words */
int
fd_stand;
/* standard format flag */
int
fd_nplanes;
/* number of color bit planes */
int
fd_rl, fd_r2, fd_r3;
/* reserved for future use */
}source, destination;
vr_trnfm(handle, &source, &destination)
Inputs
contrl[0] = 110
Opcode
contrl[1] =
Number of points in ptsin
contr][3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
&source
contri[7-8]
Long-word address of source MFDB
&destination
—_contr1[9-10]
Long-word address of destination MFDB
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
293

<!-- source-page: 301 -->
## Page 301

vsc_form
Set Mouse Form
vsc_form(
)
Opcode=111
This function is used to change the shape of the mouse pointer that appears
on screen. It lets you to define the portion of the 16 X 16 pixel area to be
drawn in the foreground color, the background color, and a transparent area
through which the existing background may be seen.
You must supply two arrays of image data. The first, called the mask,
defines the opaque area of the the pointer without regard to color information. The second is the image data itself. Bit positions within the mask
that contain a
1 are considered to be inside the pointer. If the corresponding
image data bit also contains a 1, that pixel will be colored in using the foreground color. If the corresponding image data bit contains a
0, that pixel will
be color in using the background color. Mask bit positions that contain a 0
are considered to the outside the pointer image, or transparent, and if the
corresponding image data bit contains a 0, these pixles will be represented
on screen by whatever background data happens to be there.
You must also define a hot spot for the pointer. Although the mouse
pointer may be up to 16 X 16 pixels in size, the VDI always considers it to
be located at a single point on screen. The hot spot is the one pixel within
the mouse pointer which is considered to be its true location. For example,
the tip of the arrow-shaped mouse pointer is its hot spot, so, to activate an
icon, you must position the tip of the arrow on it when you press the mouse
button.
Devices required for
Screen
C Binding
int handle, pt_data[37];
vsc_form(handle, pt_data);
Inputs
contrl[0] = 111
Opcode
contrl/1] = 0
Number of points in ptsin
contrl[3] = 37.
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
pt_data(0]
intin[0}
X coordinate of hot spot
pt_data[1]
intin[1}
Y coordinate of hot spot
pt_data[2]
intin[2}
Reserved for future use (must be 1)
pt_data[3}
intin[3]
Background pen (usually 0)
pt_data[4]
intin[4]
Foreground pen (usually 1)
ptdata[5-20]
intin[5-20]
16 words of mask data
pt_data[21-36] intin[21-36]
16 words of image data. Each word represents a line of 16 pixels, with the first
word being the top line, the second being
the second, and so on. The least-significant bit in each word represents the
rightmost pixel, and the most-signficant
bit in each word, the leftmost.
294

<!-- source-page: 302 -->
## Page 302

vse_form
Results
contr][2] = 0
contrl[4] = 0
Number of points in ptsout
Number of output integers in intout
295

<!-- source-page: 303 -->
## Page 303

vsf_udpat
Set User-Defined Fill Pattern
vsf_udpat( )
Opcode= 112
This function is used to supply the image data for the user-defined fill pattern, style 4 of vsf_interior( ). This fill pattern is
a 16 X 16 pixel image,
either monochrome or multicolor. For
a monochrome fill pattern, 16 words
of image data are used to describe the image on 16 lines. Each bit represents
either a pixel of foreground color (1) or background color (0). The foreground color used is the current fill color.
To describe a multicolor fill pattern, you must use 16 words of image
data for each color bit plane. Each plane contains a single bit of color information for each pixel, and in order to obtain complete color information for
a single pixel, you must combine the values for each corresponding bit in all
of the planes. For example, to find the color of the top, left pixel, you must
combine the first bit of each bit plane. The first bit plane contains all of the
least-significant bits, and each subsequent plane holds the next most significant bit.
Devices required for
Screen, Printer, Metafile
C Binding
int handle, planes, pat_dat[16*PLANES];
vsf_udpat(handle, pat_dat, planes);
Inputs
contrl[0] = 112
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 16 Number of input integers in intin
(16 * number of planes)
handle
contr][6] =n
The (virtual) workstation device handle
planes
The number of color bit planes
(contr][3]/16)
pat_dat[0]
intin[0}
to
to
pat_dat(15]
intin{15]
First bit plane of fill pattern
pat—dat[n—15] intin[n—15]
to
to
pat_dat[n]
intin[n]
Last bit plane of fill pattern
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vsf_interior( )
296

<!-- source-page: 304 -->
## Page 304

vsl_udsty
Set User-Defined Line Style
vsl_udsty( )
Opcode= 113
This function is used to supply the image data for the user-defined line pattern, pattern 7 of vsl_type( ). The line pattern data takes the form of a single
16-bit word, each bit of which represents a pixel drawn in either the foreground color (1) or background color (0).
Devices required for
Screen, Metafile
C Binding
int handle, pattern;
vsl_udsty(handle, pattern);
Inputs
contrl[0] = 113
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
pattern
intin[0]
The line drawing pattern, expressed as a
16-bit word of image data
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
vsl_type( )
297

<!-- source-page: 305 -->
## Page 305

vr_recfl
Fill Rectangle
vr_recfl( )
Opcode= 114
This function draws a rectangle filled with the current fill pattern and color.
The rendering of the filled figure is affected by the general graphics settings
and the fill settings, except for perimeter outlining (the rectangle created by
vr_recfl( ) is never outlined):
Writing mode (vswr_mode)
Clipping rectangle (vs_clip)
Fill color (vsf—color)
Fill interior style (vsf_interior)
Fill style index (vsf_style)
This command is most often used to clear large rectangular areas on the
screen quickly.
Devices required for
Screen, Metafile
C Binding
int handle, points[4];
vr_recfl(handle, points);
Inputs
contrl[0] = 114
Opcode
contrl{1] =
2
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl(6] = n
The (virtual) workstation device handle
points[0}
ptsin(0]
Left coordinate of the rectangle
points{1]
ptsin{1]
Top coordinate of the rectangle
points[2]
ptsin[2}
Right coordinate of the rectangle
points[3]
ptsin[3]
Bottom coordinate of the rectangle
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
See also
vswr_mode( ), vs_clip( ), vsf_color( ), vsf_interior( ), vsf_style( )
298
—

<!-- source-page: 306 -->
## Page 306

vqin_mode
Inquire Input Mode
vqin_mode( )
Opcode= 115
This function is used to determine the input mode used by one of the logical
input devices (locator, string, valuator, or choice).
Devices required for
Screen
C Binding
int handle, device, mode;
vqin_mode(handle, device, &mode);
Inputs
contrl[0] = 115
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
device
intin{0]
Logical device to check
1 = Locator
2 = Valuator
3 = Choice
4 = String
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
mode
intout[0]
Input mode of device
1 = Request
2 = Sample
See also
vsin_mode( )
299

<!-- source-page: 307 -->
## Page 307

vqt_extent
Inquire Text Extent
vqt_extent( )
Opcode= 116
Devices required for
Screen, Printer, Plotter
C Binding
int handle, points[8];
char string;
vqt_extent(handle, &string, points);
Inputs
contrl(0] = 116
Opcode
contrl[i] = 0
Number of points in ptsin
contri[3] =
s
Number of characters in text string
handle
contrl[6] = n
The (virtual) workstation device handle
string[0]
intin[0]
First character of text string. Text is formatted with one character per memory
word, with each character occupying the
low byte of the word.
string[s]
intin{s]
Last character of text string
Results
contrl[2] = 4
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
points[0]
ptsout[0]
Horizontal offset of point 1
points[1]
ptsout[1]
Vertical offset of point 1
points[2]
ptsout[2]
Horizontal offset of point 2
points{3]
ptsout[3}
Vertical offset of point 2
points[4]
ptsout[4]
Horizontal offset of point 3
points[5]
ptsout[5]
Vertical offset of point 3
points(6]
ptsout/6]
Horizontal offset of point 4
points(7]
ptsout{7]
Vertical offset of point 4
Points 1, 2, 3, and 4 refer to the bottom left, bottom right, top right, and
top left corners of the text string, respectively. Point
1 is located at the origin
for text strings that are rotated 0 degrees, point 2 is located at the origin for
strings that are rotated 270 degrees, point 3 is located at the origin for
strings that are rotated 180 degrees, and point 4 is at the origin when the
string is rotated 90 degrees. (See Figure 7-2.)
300
—

<!-- source-page: 308 -->
## Page 308

vqt_width
Inquire Character Cell Width
vqt_width( )
Opcode= 117
This function can be used to learn the character cell width of a particular
character in the current text font (without making allowance for special effects or baseline rotation). The character cell may include some of the blank
space surrounding the character.
Devices required for
All
C Binding
int handle, char, cellw, left_offset, right_offset, status;
status = vqt_width(handle, char, &cellw, &left_offset, &right_offset);
Inputs
contrl[0] = 117
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
char
intin[0]
Character whose width is inquired, formatted so ASCII value is in the low byte
of the word.
Results
contrl[2] = 3
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
status
intout[0]
Character about which information is returned (—1 if character requested was not
available)
cellw
ptsout(0]
Width of the character cell (in pixels)
ptsout{1]
0
left_offset
ptsout[2]
Offset of the left side of the character
from the left edge of the character cell
ptsout([3]
0
right_offset
ptsout(4]
Offset of the right side of the character
from the right edge of the character cell
ptsout[5]
0
301

<!-- source-page: 309 -->
## Page 309

vex_timv
Exchange Timer Interrupt Vector
vex_timv( )
Opcode= 118
This function allows you to add your own machine-language program to the
ST timer interrupt handler that executes every fixed period known as a timer
tick. Your routine should preserve all registers, should not call any nonreentrant ROM routines, and should end with an RTS instruction. The function returns the address of the normal entry point of the system timer
routine, so that your routine may call that routine when it is finished.
Devices required for
Screen
C Binding
int handle, tick-length;
int *new_addr, *old_addr
vex_timv(handle, new_addr, old_addr, &tick_length);
Inputs
contrl[0] = 118
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] =
The physical screen device handle (obtained from graf_handle(
) call)
new_addr
contrl[7-8]
Long-word address of the user’s timer
routine
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
old_addr
contrl[9~10]
Long-word address of the normal system
timer routine
tick_length
intout(0]
Length of time between timer ticks
(in milliseconds)
302
—_—

<!-- source-page: 310 -->
## Page 310

vst_load_fonts
Load Fonts
vst_load__fonts(
)
Opcode= 119
This function is used to load disk-based text fonts. In order to load diskbased fonts on the ST, the GDOS extension (GDOS.PRG) must be loaded,
usually by placing the program in the AUTO folder of the disk with which
the system is started. Furthermore, the filenames of the fonts that available
for each device driver must be listed in a
file called ASSIGN.SYS, located in
the top directory of the boot disk. Fonts cannot be loaded selectively; all
available fonts will be loaded at the same time.
Devices required for
Screen
C Binding
int handle, select, fonts_loaded;
fonts_loaded = vst_load_fonts(handle, select);
Inputs
contrl[(0] = 119
Opcode
conirl[1] = 0
Number of points in ptsin
contri[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
select
intin{O] = 0
Reserved for future use, set to 0
(may be used to selectively load fonts in a
future version of GEM)
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
fonts_loaded
_intout[0]
Number of new fonts made available
See also
vst_unload_fonts( }
303

<!-- source-page: 311 -->
## Page 311

vst_unload_fonts
Unload Fonts
vst_unload_fonts( )
Opcode= 120
_
This function is used to terminate the availability of disk-loaded fonts to a
particular device. If no other workstation is using those fonts, this function
also frees up the memory taken up by those fonts. You should unload diskbased fonts whenever you are through using them.
Devices required for
Screen
C Binding
int handle, select;
vst_unload_fonts(handle, select);
Inputs
contrl[0] = 120
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
select
intin[0] = 0
Reserved for future use, set to 0
(may be used to selectively load fonts in a
future version of GEM)
Results
contrl[2] = 0
Number of points in ptsout
See also
vst_load_fonts( )
304
_

<!-- source-page: 312 -->
## Page 312

vrt_cpyfm
Copy Raster, Transparent
vrt_cpyfm( )
Opcode= 121
This function is used to copy a single-plane rectangular bit image to a destination memory area (usually in screen memory) that can be made up of
several color bit planes. The VDI uses a data structure called
a Memory
Form Definition Block (MFDB) to describe the source and destination memory areas. This data structure contains information about the memory location of image data, the size of the image in pixels and memory words, the
number of color planes, and format of the image, either standard (each color
bit plane separate), or ST-specific (color planes interleaved into one large bit
plane). For the purposes of this function, the source and destination forms
must both be in ST-specific format.
The call lets you specify the pen color that will be used to draw both
the foreground (one bits) and the background (zero bits), so the image can
be drawn in any color combination that you wish. The image may be copied
directly, or combined in various ways with the existing image data in the
destination area. Note that the writing modes used to combine the image are
not the same ones used by vro_cpyfm( ), but rather the more limited set offered by vswr_mode( ).
Devices required for
Screen
C Binding
int handle, mode, points[8], pens(2];
struct fdbstr
{
int
*fd_addr;
/* pointer to image data area */
int
fd_w;
/* image width in pixels */
int
fd_h;
/* image height in pixels */
int
fd_wdwidth;
/* image width in words */
int
fd_stand;
/* standard format flag */
int
fd_nplanes;
/* number of color bit planes */
int
fd_rl, fd_r2, fd_r3;
/* reserved for future use */
}source, destination;
vrt_copyfm(handle, mode, points, source, destination, pens);
Inputs
contrl[0] = 121
Opcode
contrl[1] = 4
Number of points in ptsin
contrl[3] = 3
Number of input integers in intin
handle
contrl[6] =n
The (virtual) workstation device handle
source
contrl[7-8]
Long-word address of the source Memory
Form Definition Block (MFDB)
destination
contrl[9-10]
Long-word address of the destination
Memory
Form Definition Block (MFDB)
mode
intin(0]
The mode that determines how the source
combines with the destination:
305

<!-- source-page: 313 -->
## Page 313

vrt_cpyfm
pen(0}
pen{1]
points[0]
points[1]
points[2]
points[3]
points[4]
points[5}
points[6]
points[7]
Results
See also
vro_cprfm( )
306
intin{1]
intin[2]
ptsin[0]
ptsin(1]
ptsin[2]
ptsin[3]
ptsin[4]
ptsin[5]
ptsin[6]
ptsin[7]
contrl[2] = 0
contrl[4] = 0
= Replace
= Transparent
= XOR
4 = Reverse Transparent
The VDI pen color (index) for the
1 bits in
the image data (foreground).
The VDI pen color (index) for the 0 bits in
the image data (background)
Left edge of source rectangle
Top edge of source rectangle
Right edge of source rectangle
Bottom edge of source rectangle
Left edge of destination rectangle
Top edge of destination rectangle
Right edge of destination rectangle
Bottom edge of destination rectangle
WN
Number of points in ptsout
Number of output integers in intout

<!-- source-page: 314 -->
## Page 314

v_show__c
Show Mouse Pointer
v_show_c( )
Opcode= 122
This function is used to display the mouse pointer, which tracks the movement of the mouse on screen. Whether or not a call to this function actually
displays the pointer depends on how many times Hide Mouse Pointer
(v_hide_c) has been called previously. Each time v_hide_c(
) is called,
pointer visibility is pushed down one level further. Therefore, if v_hide_c( )
is called twice, v_show_c( ) must also be called twice before the pointer becomes visible. This function provides a reset flag, however, which resets the
counter that keeps track of how many times the pointer has been hidden. By
using this flag, you may specify that the pointer become visible regardless of
the level at which it was hidden.
Devices required for
Screen
C Binding
int handle, reset;
v_show—c(handle, reset);
Inputs
contrl[0] = 122
Opcode
contrl[{1] = 0
Number of points in ptsin
contrl[{3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
reset
intin(0]
Reset flag
0 = Reset counter, and display
pointer regardless of number of
times hidden
<> 0 = Move pointer visibility up one
level, and display if only hidden
once.
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
v_hide_c(
)
307

<!-- source-page: 315 -->
## Page 315

v_hide_c
Hide Mouse Pointer
v—hide_c( )
Opcode= 123
This function removes the mouse pointer that tracks the mouse movements
on the screen. Each time this function is called, a counter increments the
level at which the pointer is hidden, so that an equal number of v_show_c( )
calls must be made before the pointer becomes visible again.
Devices required for
Screen
C Binding
int handle;
v_hide_c(handle);
Inputs
contrl[0] = 123
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
See also
v—show_c( )
308

<!-- source-page: 316 -->
## Page 316

vq—mouse
Sample Mouse Button State
vq—mouse( )
Opcode= 124
This function is used to discover if either or both mouse buttons are currently being pressed. It also returns the current screen position of the mouse
pointer.
Devices required for
Screen, Plotter
C Binding
int handle, button, x, y;
vq—mouse(handle, &button, &x, &y);
Inputs
contrl[(0] = 124
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contri[6] = n
The (virtual) workstation device handle
Results
contrl[2] =
1
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
button
intout(0]
Mouse button status:
0 = No buttons pressed
1 = Left button pressed
2 = Right button pressed
3 = Both buttons pressed
x
ptsout[0]
Horizontal position of the mouse pointer
y
ptsout(1]
Vertical position of the mouse pointer
309

<!-- source-page: 317 -->
## Page 317

vex_butv
Exchange Button Change Vector
vex_butv( )
Opcode= 125
This function allows you to add your own machine language program to the
ST mouse button interrupt handler that executes every time that a mouse
button is pressed. Your routine should preserve all registers, should not call
any non-reentrant ROM routines, and should end with an RTS instruction.
At the point that your program executes, the mouse button status is contained in register DO, represented in the same manner as in vq_mouse( ).
The function returns the address of the normal entry point of the system
timer routine, so that your routine may call that routine when it is finished.
Devices required for
Screen
C Binding
int handle;
int *new_addr, *old_addr
vex__timv(handle, new_addr, old_addr);
Inputs
contrl[0] = 125
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The physical screen device handle
(obtained from graf_handle(
) call)
new_addr
contrl{7—8]
Long-word address of the user’s mouse
button routine.
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
6
Number of output integers in intout
old_addr
contrl[9-10]
Long-word address of the normal system
mouse button routine.
310

<!-- source-page: 318 -->
## Page 318

vex__motv
Exchange Mouse Movement Vector
vex_motv( )
Opcode= 126
This function allows you to add your own machine language program to the
ST mouse movement interrupt handler that executes every time that the
mouse changes position. At the time your program executes, register DO
contains the horizontal position of the mouse, and the D1 contains the vertical position. Your routine should preserve all registers, should not call any
non-reentrant ROM routines, and should end with an RTS instruction. The
function returns the address of the normal entry point of the system timer
routine, so that your routine may call that routine when it is finished.
Devices required for
Screen
C Binding
int handle;
int *new_addr, *old_addr
vex_motv(handle, new_addr, old_addr);
Inputs
contrl[0] = 126
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The physical screen device handle
{obtained from graf_handle( ) call)
new_addr
contrl[7—8]
Long-word address of the user’s mouse
movement routine.
Results
contrli[2] = 0
Number of points in ptsout
contrl[4] =
0
Number of output integers in intout
old_addr
contrl{9~10}
Long-word address of the normal system
mouse movement routine.
311

<!-- source-page: 319 -->
## Page 319

vex_curyv
Exchange Cursor Change Vector
vex_curv( )
Opcode= 127
:
This function allows you to add your own machine language program to the
ST mouse pointer interrupt handler that executes every time that the mouse
pointer is to be redrawn. At the point at which your code executes, the hori-
~
zontal position of the mouse pointer is stored in register DO, and its vertical
poisiton in register D1. Your routine should preserve all registers, should not
call any non-reentrant ROM routines, and should end with an RTS instruction. The function returns the address of the normal entry point of the system timer routine, so that your routine may call that routine when it is
finished.
Devices required for
Screen
C Binding
int handle;
int *new_addr, *old_addr
vex_curv(handle, new_addr, old_addr);
Inputs
contrl[0] = 127
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The physical screen device handle
(obtained from graf_handle( ) call)
new_addr
contrl[7-8]
Long-word address of the user’s mouse
pointer routine.
Results
contrl[2] =
0
Number of points in ptsout
contr][4] = 0
Number of output integers in intout
old_addr
contr][9-10]
Long-word address of the normal system
mouse pointer redraw routine.
312

<!-- source-page: 320 -->
## Page 320

vq—key_s
Sample Keyboard State Information
vq—key—s()
Opcode= 128
This function is used to learn whether or not the Control, Left Shift, Right
Shift, and/or Alt keys are currently being pressed.
Devices required for
Screen
C Binding
int handle, key;
vq—key_s(handle, &key);
Inputs
contrl(0] = 128
Opcode
contrl[1] = 0
Number of points in ptsin
contrl[3] =
0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] =
0
Number of points in ptsout
contrl[4] =
1
Number of output integers in intout
key
intout[0]
Keypress status
The status for each key is returned in one
of the four low bits of this word. Bits are
assigned as follows:
Bit
Value
Key
0
1
Right Shift
1
2
Left Shift
2
4
Control
3
8
Alt
’
Aone bit in any of these places means the
key is pressed. For example, a value of 10
means that both the Alt key (8) and the
Left Shift (2) are pressed.
313

<!-- source-page: 321 -->
## Page 321

vs—clip
Set Clipping Rectangle
vs__clip( )
Opcode= 129
This function is used to turn clipping on and off. When clipping is on, output of all of the VDI graphics functions is restricted to a particular rectangular area. Output directed to areas outside of that rectangle is ignored.
Clipping is particularly useful for confining output to the within the boundaries of
a window.
Devices required for
Screen, Printer, Metafile
C Binding
int handle, clip_flag, points[4];
vs_clip (handle, clip_flag, points);
Inputs
contrl[0] = 129
Opcode
contrl[1] = 2
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] =n
The (virtual) workstation device handle
clip_flag
intin(0}
Clipping Flag
0 = clipping off
<> 0 = clipping on
points[0]
ptsin[0]
Left edge of clipping rectangle
points[1]
ptsin[1]
Top edge of clipping rectangle
points[2]
ptsin[2]
Right edge of clipping rectangle
points[3}
ptsin[3]
Bottom edge of clipping rectangle
Results
contrl{2] = 0
Number of points in ptsout
contrl[4] = 0
Number of output integers in intout
314

<!-- source-page: 322 -->
## Page 322

vqt_name
Inquire
Face Name and Index
vqt_name( )
Opcode= 130
This function returns a character string containing the name and style information about a text font. It also returns the font ID number, which is needed
to set this font as the current graphics text font (with a call to vst_font).
Devices required for
Screen, Printer, Plotter
C Binding
int handle, number, id;
char name{[32];
id = vqt_name (handle, number, name);
Inputs
contrl[(0] = 130
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] =
1
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
number
intin[0]
Font number. Font numbers are arbitrary
numbers that range from
1 (the system
font) to the maximum number of fonts.
They are assigned in numeric order of ID
numbers, so if there are three fonts with
ID numbers of 1, 50, and 12, the font with
ID number 1 will have a font number of
1, ID 12 will be font 2, and ID 50 will be
font 3.
Results
contrl[2] = 0
Number of points in ptsout
contrl[4] = 33.
Number of output integers in intout
id
intout[0]
Font ID number. This number is actually
part of the font information itself, and is
assigned when the font is created. It is
needed to set this font as the current
graphics text font when calling vst_font( ).
name{0-31]
intout[1-32]
The text name string. This string is formatted so that each character is set into a
separate 16-bit member of the intout array, with the ASCII value of the character
in the low byte, and a zero in the high
byte. The first 16 characters of the string
contain the name of the fonts, and the last
16 describe its thickness and style (such as
whether this is a bold or italic variation).
See also
vst_font(
)
315

<!-- source-page: 323 -->
## Page 323

vqt_font_info
Inquire Current Face Information
vqt__font_info( )
Opcode= 131
This function returns information about the size of the current graphics text
font, including information about the size changes brought about by special
effects.
Devices required for
All
C Binding
int handle, minchar, maxchar, maxwidth, distances[5], effects[3];
vqt_font_info(handle, &minchar, &maxchar, distanches, &maxwidth,
effects);
Note: Some versions of the Alcyon and Megamax bindings assign this function the name vqt_fontinfo( ), instead of vqt_font_info( ).
Inputs
contrl[0] = 131
Opcode
contrl[1] =
0
Number of points in ptsin
contrl[3] = 0
Number of input integers in intin
handle
contrl[6] = n
The (virtual) workstation device handle
Results
contrl[2] = 5
Number of points in ptsout
contrl[4] = 2
Number of output integers in intout
minchar
intout[0]
The ASCII character number of the first
character in this type face.
maxchar
intout[1]
The ASCII character number of the last
character in this type face.
maxwidth
ptsout(0]
The maximum character cell width in this
type face, not including special effects.
distances(0]
ptsout(1]
The distance from the baseline to the bottom line.
effects[0]
ptsout[2]
The total increase in character width due
to current special effects.
distances[1]
ptsout[3]
The distance from the baseline to the descent line.
effects[1]
ptsout[4]
The increase in character width on the left
due to current special effects.
distances{2]
ptsout{5]
The distance from the baseline to the half
line.
effects(2]
ptsout[6]
The increase in character width on the
right due to current special effects.
distances[3]
ptsout[7]
The distance from the baseline to the ascent line.
ptsout[8]
0
distances[4]
ptsout[9]
The distance from the baseline to the top
line.
316

<!-- source-page: 324 -->
## Page 324

Appendix B
Extended Keyboard
Codes
y
—
——/
—
aoe
my
7
2
j

<!-- source-page: 325 -->
## Page 325

oe

<!-- source-page: 326 -->
## Page 326

The VDI string input functions (vrq_string and
vsm_string) may return a two-byte value for every key
pressed, rather than a simple one-byte ASCII code. The first
byte of this keycode is generally a unique key identifier that
refers to the physical key struck, regardless of shift key combinations. The second byte is usually the ASCII value of the
key combination, which does depend on the state of the shift
keys (Shift, Control, and Alt). The following table shows the
keycodes, as 4-digit hexadecimal numbers, for all key and shift
combinations..
Main Keyboard
Unshifted
Shift
CTRL
ALT
a
1E61
A
1E41
1E01
1E00
b
3062
B
3042
3002
3000
c
2E63
C
2E43
2E03
2E00
d
2064
D
2044
2004
2000
e
1265
E
1245
1205
1200
f
2166
F
2146
2106
2100
g
2267
G
= 2247
2207
2200
h
2368
H
= 2348
2308
2300
i
1769
I
1749
1709
1700
j
246A
J
244A
240A
2400
k
256B
K
254B
250B
2500
l
266C
L
264C
260C
2600
m
326D
M
324D
320D
3200
n
316E
N
 314E
310E
3100
ra)
186F
O
 184F
180F
1800
P
1970
P
1950
1910
1900
q
1071
Q
1051
1011
1000
r
1372
R
1352
1312
1300
_
s
1F73
S
1F53
1F13
1F00
t
1474
T
1454
1414
1400
u
1675
UU
1655
1615
1600
v
2F76
VV
so2F56
2F16
2F00
—_
Ww
1177
W
1157
1117
1100
x
2D78
X
2D58
2D18
2D00
y
1579
Y
1559
1519
1500
—
Zz
2C7A
Z
2C5SA
2C1A
2C00
—
319

<!-- source-page: 327 -->
## Page 327

Appendix B
1
0231
!
0221
0211
7800
2
0332
@
0340
0300
7900
3
0433
#
0423
0413
7A00
4
0534
$
0524
0514
7B00
5
0635
%
0625
0615
7C00
6
0736
”
O75E
O71E
7D00
7
0837
&
0826
0817
7E00
8
0938
*
092A
0918
7F00
9
0A39
(
0A28
0A19
8000
0
0B30
)
0B29
0B10
8100
-
0C2D
—
 OC5F
OC1F
8200
=
0D3D
+
O0D2B
0D1D
8300
‘
2960
297E
2900
2960
\
2B5C
2B7C
2B1C
2B5C
[
1A5B
{
1A7B
1A1B
1A5B
]
1B5D
}
1B7D
1B1D
1B5D
;
273B
:
273A
271B
273B
;
273B
:
273A
271B
273B
2827
"2822
2807
2827
,
332C
<
 333C
330C
332C
.
342E
>
343E
340E
342E
/
352F
?
353F
350F
352F
Space
3920
3920
3900
3920
Ese
011B
011B
011B
011B
Backspace
OE08
OE08
0E08
O0E08
Delete
537F
537F
531F
537F
Return
1C0D
1C0D
1C0A
1C0D
Tab
OFO9
OFO9
OFO9
OFO9
Cursor Pad
Unshifted
Shift
CTRL
ALT
Help
6200
6200
6200
(screen print)
Undo
6100
6100
6100
6100
Insert
5200
5230
5200
(left mouse button)
Clr/Home
4700
4737
7700
(right mouse button)
Up-Arrow
4800
4838
4800
(move mouse up)
Dn-Arrow
5000
5032
5000
(move mouse dn)
Rt-Arrow
4B00
4B34
7300
(move mouse rt)
Lft-Arrow
4D00
4D36
7400
(move mouse Ift)
320

<!-- source-page: 328 -->
## Page 328

Extended Keyboard Codes
Numeric Pad
Unshifted
6328
6429
652F
662A
4A2D
4E2B
712E
nter
720D
7030
6D31
6E32
6F33
6A34
6B35
6C36
6737
6838
6939
mo
+
I
WONAUBRWNRe
Ot:
Shift
6328
6429
652F
662A
4A2D
4E2B
712E
720D
7030
6D31
6E32
6F33
6A34
6B35
6C36
6737
6838
6939
Function Keys
Unshifted
Fl
3B00
F2.
3C00
F3
3D00
F4
3E00
F5
3F00
Fé
4000
F7
4100
F8
4200
F9
4300
F10
4400
Shift
5400
5500
5600
5700
5800
5900
5A00
5B00
5C00
5D00
CTRL
6308
6409
650F
660A
4A1F
4E0B
710E
720A
7010
6D11
6E00
6F13
6A14
6B15
6CIE
6717
6818
6919
CTRL
3B00
3C00
3D00
3E00
3F00
4000
4100
4200
4300
4400
ALT
6328
6429
652F
662A
4A2D
4E2B
712E
720D
7030
6D31
6E32
6F33
6A34
6B35
6C36
6737
6838
6939
ALT
3B00
3C00
3D00
3E00
3F00
4000
4100
4200
4300
4400
321

<!-- source-page: 330 -->
## Page 330

Appendix C
VDI Font Files

<!-- source-page: 332 -->
## Page 332

Font files
for VDI disk-based fonts are divided into
four sections. The first, called the font header, contains information about the font such as first and last character in the
font, font size, font name, and so on. The font header is 87
bytes long, and is laid out in the following format:
Byte
Number
Description
0-1
-3
2
4-35
36-37
38-39
40-41
42-43
44-45
46-47
48-49
50-51
52-53
54-55
56-57
58-59
Font ID. This value is used by the vst_font( ) function to
make this the current graphics text font. It’s one of the
values returned by the vqt_name( ) function.
Font size (in points).
Font name and style information. This is a 32-character
text string, with each character occupying the low byte of
its own 16-bit word. The first 16 characters give the name
of the font, while the last 16 describe special characteristics, such as thickness and style. This text string is one of
the values returned by vqt_name( ).
First character. The ASCII value of the first character in
the font. This value is returned by vqt_font_info( ).
Last character. The ASCII value of the last character in the
font. This value is returned by vqt_font_info( ).
Top line distance. The distance in pixels from the baseline
to the top line. This value is returned by vqt_font_info( ).
Ascent line distance. The distance in pixels from the baseline to the ascent line. This value is returned by
vqt_font_info( ).
Half line distance. The distance in pixels from the baseline
to the half line. This value is returned by vqt_font_info( ).
Descent line distance. The distance in pixels from the
baseline to the descent line. This value is returned by
vqt_font_info( ).
Bottom Distance. The distance from the baseline to the
bottom line. This value is returned by vqt_font—info( ).
Character Width. The width of the widest character in the
font.
Cell Width. The width of the widest character cell in the
font. This value is returned by vqt_font_info( ).
Left offset. The number of pixels added to left side of
character by special effects. This value is returned by
vqt_font_info( ).
Right Offset. The number of pixels added to right side of
character by special effects. This value is returned by
vqt_font_info( ).
Thickening width. The number of pixels added to the
width of a character by the thickening special effect.
325

<!-- source-page: 333 -->
## Page 333

Appendix C
60-61
Underline size. The width in pixels of the line used to underline a character.
62-63
Lightening mask. The 16-bit mask used to remove pixels
from the character for the lightening special effect. The
pattern 0 X 5555, which removes every other pixel, is the
one most commonly used for this purpose.
64-65
Skewing mask. A 16-bit mask used to determine how to
shift the character’s image data for skewing (italics). The
pattern 0 X 5555 is the one most commonly used for this
purpose.
66-67
Font flags. Each flag occupies one bit:
Bit
Value
Description
0
1
Set to 1 if this is the default system font
1
2
Set to
1 if there’s a horizontal offset table
2
4
 Byte-orientation flag. Set to
1 if data is in
high-byte, low-byte order used by 6800
processor
3
8
Set to
1 if this is
a mono-spaced font.
68-71
Horizontal offset table pointer. The number of bytes from
the beginning of the file to the horizontal offset table.
72-75
Character offset table pointer. The number of bytes from
the beginning of the file to the character offset table.
76-79
Font data pointer. The number of bytes from the beginning the file to the start of font image data.
80-81
Form width. The number of bytes required to hold the
combined widths of all of the characters in the font (total
character widths divided by 8).
82-83
Form height. Same as the font height in pixels.
84-87
Pointer to the next font. These four bytes are placeholders for a pointer to the next font which is set by the
device driver.
Character table offset. The next section is called the character offset table. This table contains the offset for the characters’ image data from the beginning of the image data table.
This offset is equal to the sum of the widths of all of the preceding characters. For example, let’s say the first character in
the font has an ASCII value of 32. Its offset is the first entry in
the offset table, which always has a value of zero. If that character is 4 pixels wide, the second entry, for character 33, will
be four. The width of character 33 will be added to four to obtain the value for the third entry, which covers character 34.
You can find the width of any individual character by subtracting its offset from that of the following character. That
326

<!-- source-page: 334 -->
## Page 334

VDI Font Files
means that there will have to be one more entry in the table
than there are characters, since you need to subtract the offset
for the last character from that of the following one. Note that
this table is necessary even for fonts whose characters all have
the same widths (called mono-spaced fonts).
Horizontal offset table. The third section is an optional
horizontal offset table. This table contains one entry per character, showing the additional number of pixel spaces (positive
or negative) that should be added before the character is output. A bit in the flag word of the header table indicates
whether or not there is a horizontal offset table.
Actual image data. The final section is the actual image
data for the characters in the font. Character data is formatted
with all of the data for each scan line of all of the characters
following one after the other. The data for the first line of the
first character is followed by the data for the first line of the
second character, and so on. Each scan line starts on a word
boundary, but within a scan line the characters are not byteor word-aligned, That means that if each character is six bits
wide, the first character uses the first six bits in the first byte,
and the second character uses the last two bits of the first byte
and the first four bits of the next byte. Only at the end of the
scan line is padding added to make the next scan line start on
a word boundary.
Important Note
The few disk-based fonts that were available for examination
at the time of this writing were arranged in the Intel format
used by the IBM version of GEM. This means that 16-bit values are formatted with the low byte first and the high byte
second, and 32-bit values are stored with the least significant
byte first, followed by increasingly significant bytes. For example, in the font header, if the 16-bit font ID has a value of
2, the number appears in the header with the two-byte followed by the-zero byte.
327

<!-- source-page: 336 -->
## Page 336

Appendix D
System Characters

<!-- source-page: 337 -->
## Page 337

eed

<!-- source-page: 338 -->
## Page 338

This appendix includes all the system font.
The font supports all characters from 0 through 255.
0
¢*
G
»
7 i
9%
10 R
ud
12 5
C
13%
14 4
15 [ky
26
@
a7
&
23
£
29
"9
30
31 ¥
32
Space
33
|
34
(WN
35
#
36
§
37
44
45
46
47

<!-- source-page: 339 -->
## Page 339

Appendix D
52
66 B
so p
o4
A
53
§
67 [
81
[J
95
54
§
68 [
82 R
0
*
55
FF
69 E
83 §
97
@
56
6
70 F
84 T
2
b
57
J
7G
85
[J
9
£€
58
4
72
H
86
YJ
100
59
3
73
87 Wl
101 B
60
<
74
J
ss ¥
102 F
61
=
7K
39 ¥
103 g
62
>
76
L
0 -
i04 h
63?
77M
a
[
105
|
64
78
W
92
5
106
J
6
f
79
J
93
]
107 K
332

<!-- source-page: 340 -->
## Page 340

System Characters
7
108
]
122
£
136
7
109
fff
123
4
137
7
110
f
124
|
138
111
Q
125
}
139
112
p
126
™
140
113
g
127
&
141
114
128
C
142
15
§
129
ij
143
116
f
130
é
144
117
U
31
@
145
_
118
Y
32
@
146
_
119
Wl
33
@
147
_
120 K
4
148
_
121
Uj
135
C
149
m>
=)
ror
:
re
Fe
rm
=
ax
=e
o>
or
150
151
152
153
154
155
156
157
158
159
160
161
162
163
iid
Lt |
—-—
TD
+c
rr
fF
oO.
ony,
ou,
[
333

<!-- source-page: 341 -->
## Page 341

Appendix D
164
165
166
167
168
169
170
171
172
173
174
175
176
177
334
io
iT
= 7)
=?
om |
a)
c-
ae
R
or
182
183
184
185
186
187
188
189
190
191
o
=
=
FF
|
192
193
194
195
196
197
198
199
200
201
202
203
204
205
bal
zx
=
£&
=
206
207
208
209
210
211
212
213
214
215
216
217
218
219
—-
32
F&F
W27F
=
EF
HY
e&
a
--
e — oe
|

<!-- source-page: 342 -->
## Page 342

System Characters
220
4
234
O
248
221
§
235
&
249
222
A
236
ff
250
223
237
251
224
&
238
&
252
25
ff
239
f]
253
2
T
240
=
254
227
4
241
+
255
228
242
>
229
243
<
_
230
UU
244
_
231
T
245
|
7
232
0
246
=
233
G
247
=
335

<!-- source-page: 344 -->
## Page 344

Index by Function
Function
v_arc()
v_bar( )
v—bit_image( )
v—circle( )
v—clear_disp_iist
v_clrwk( )
v—clsvwk( )
v_clswk( )
v__contourfill
v_curdown( )
v—curhome(
)
v—curleft( )
v—curright(
)
v—curtext
v—curup( )
v—dspcur( )
v—eeol(
)
v_eeos(
)
v—ellarc( )
v_ellipse(
)
v—ellpie(
)
v—enter_cur(
)
vex_butv( )
vex_curv(
)
vex_motv( )
vex_timv(
)
v_fillarea(
)
v—_form_adv( )
v—get_pixel( )
v—gtext( )
v_—hardcopy( )
v—hide_c(
)
v_justified()
v._opnvwk( )
v—opnwk(
)
v_output_window(
)
v_pie( )
v_pline( )
v—pmarker( )
vq—chcells( )
vq—color( )
vq—curaddress
vq—exit_cur( )
vq—extnd(
)
vqf_attributes( )
vqin_mode( )
vq—key_s()
vql_attributes( }
vqm_attributes(
)
vq_mouse(
)
100
Function
Number
2
1
23
4
22
ray
oiled
WNUIAOCWLN
AN
OO
UI
20
17
10
Pages
22, 54-55, 231-32
22, 107, 230
224
22, 108, 235
223
6, 7-8, 9, 30, 200
30, 281
30, 199
112, 285
164, 206
164, 209
164, 208
164, 207
163-64,
165, 213
164, 205
219
165, 211
165, 210
22, 56, 237
22, 108, 236
22, 109, 238
163, 204
188, 189, 310
188, 312
188, 311
188, 302
110, 229
221
75, 287
144, 168, 227-28
218
178, 308
22, 148, 241-42
16, 20, 21, 42, 276-80
13, 15, 21, 195-98
222
233-34
46, 225
41, 226
165, 202
75, 258
164, 216
163, 203
27, 282-84
105, 273
180, 299
179, 313
53, 271
45, 272
32, 176, 309
337

<!-- source-page: 345 -->
## Page 345

Function
vq—tabstatus( )
vqt_attributes( )
vqt_extent( )
vqt_fontinfo( )
vqt..name( )
vqt_width( )
v_rbox( )
v_rfbox( )
v—imcur( )
vro_cpyfm( )
vrq—choice( )
vrq_locator( )
vrq—string( )
vrq_valuator( )
vr_recfl( )
vrt_cpyfm()
vr_trnfm( }
v_tvoff()
v_rvon( )
vsc_form( )
vs_clip( )
vs—color( )
vs—curaddress
vsf_color( )
vsf_interior(
)
vsf_perimeter( )
vsf_style( )
vsf_udpat( )
v_show_c( )
vsin_mode( )
vsl_color( )
vsl_ends( )
vsl_type( )
vsl_udsty( )
vsl_width( )
vsm_choice( )
vsm_—color( )
vsm_height( )
vsm_locator( )
vsm__string( )
vsm_type( )
vsm_valuator( )
vst_alignment
vst_color(
)
vst_effects( )
vst_font( )
vst_height( )
vst_load__fonts(
)
vst_point( )
vst_rotation(
)
vst_unload_fonts( )
vswr_mode( )
v_updwk( )
338
Opcode
5
38
116
131
130
117
11
11
5
109
30
28
31
29
114
121
110
Function
Number
16
14
13
11
Pages
217
162, 274
149, 300
149, 160-62, 316
-
157, 315
149, 301
22, 56, 239
22, 107, 240
—
220
123-28,
132, 291-92
185, 263
181, 259
182, 265-66
186, 261
93, 124, 298
128, 131-33, 305-06
125, 129, 293
165, 215
165, 214
177, 294-95
85, 314
72, 245-46
164, 212
16, 105, 257
16, 94, 255
105, 286
16, 95, 256
100, 103, 296
178, 307
180, 270
16, 50, 71, 249
52, 290
16, 48, 247
49, 297
51, 248
185, 264
43, 71, 252
43, 251
181, 260
182-83, 267-68
16, 42, 250
186, 262
145-46, 275
16, 152, 168, 254
153, 288
16, 58, 253
155, 243
157, 303
156, 289
151, 244
158, 304
79, 123, 131, 269
30, 210

<!-- source-page: 346 -->
## Page 346

Index by Opcode
Function
v_opnwk( )
v_clswk( )
v—clrwk( )
v_updwk( )
vq—chcells( )
vq__exit_cur( )
v—enter_cur(
)
v_—curup( )
v_curdown(
)
v_curright( )
v_curleft( )
v—curhome( )
v_eeos( )
v_eeol )
vs__curaddress
v_curtext
v_rvon()
v_rvoff( )
vq_curaddress
vq_tabstatus(
)
v—hardcopy( )
v—dspcur(
)
v—rmcur( )
v_form_adv( )
v_output_window(
)
v_clear_disp_list
v_bit_image( )
v_pline( )
v_pmarker( )
v_gtext( )
v_fillarea( )
v_bar( )
v—arc( )
v_pie( )
v—circle( )
v_ellipse( )
v—ellarc(
)
v_ellpie(
)
v_rbox( )
v_rfbox( )
v_justified( )
vst_height( )
vst_rotation(
)
vs_color(
)
vsl_type( )
vsl_width( )
vsl_color( )
vsm_type( )
vsm_height( )
vsm__color( }
Opcode
OONAUUAUAATAAGGAAITaqaaqnaiarwaaaiwagj»n
Uwe WN
Function
Number
WON
DA TP WN
ran COON
AGT EWNPH
Pages
13, 15, 21, 195-98
30, 199
6, 7-8, 9,
30, 200
30, 210
165, 202
163, 203
163, 204
164, 205
164, 206
164, 207
164, 208
164, 209
165, 210
165, 211
164, 212
163-64,
165, 213
165, 214
165, 215
164, 216
217
218
219
220
221
222
223
224
46, 225
41, 226
144, 168, 227-28
110, 229
22, 107, 230
22, 54-55, 231-32
233-34
22, 108, 235
22, 108, 236
22, 56, 237
22, 109, 238
22, 56, 239
22, 107, 240
22, 148, 241-42
155, 243
151, 244
72, 245-46
16, 48, 247
51, 248
16, 50, 71, 249
16, 42, 250
43, 251
43, 71, 252
339

<!-- source-page: 347 -->
## Page 347

Function
vst_font( )
vst_color( )
vsf_interior( )
vsf_style( )
vsf_color( )
vq—color( )
vrq—locator( )
vsm_locator( )
vrq—valuator( )
vsm_valuator( )
vrq—choice( )
vsm_choice( )
vrq-string( )
vsm_string( )
vswr_mode( )
vsin_mode( )
vql_attributes( )
vqm__attributes( )
vqf_attributes(
)
vqt_attributes( )
vst_alignment
v—_opnvwk( )
v_clsvwk( )
vq—extnd(
)
v—contourfill
vsf_perimeter(
)
v_get_pixel( )
vst_effects( )
vst_point( )
vsl_ends( )
vro_cpyfm( )
vr_trn—fm( )
vsc_form( )
vsf_udpat( )
vsl_udsty( )
vr_recfl( )
vqin_mode{( )
vqt—extent( }
vqt_width{ )
vex_timv(
)
vst_load_fonts( )
vst_unload_fonts( )
vrt_cpyfm()
v_show_c( )
v—hide_c( )
vq—mouse( )
vex_butv( )
vex_motv( )
vex_curv( )
vq—key_s( )
vs_clip( )
vqt_name( )
vqt_font_info( }
340
Function
Number
Pages
16, 58, 253
16, 152, 168, 254
16, 94, 255
16, 95, 256
16, 105, 257
75, 258
181, 259
181, 260
—
186, 261
186, 262
185, 263
185, 264
182, 265-66
182-83, 267-68
79, 123, 131, 269
180, 270
53, 271
45, 272
105, 273
162, 274
145-46, 275
16, 20, 21, 42, 276-80
30, 281
27, 282-84
112, 285
105, 286
75, 287
153, 288
156, 289
52, 290
123-28,
132, 291-92
125, 129, 293
177, 294-95
100, 103, 296
49, 297
93, 124, 298
180, 299
149, 300
149, 301
188, 302
157, 303
158, 304
128, 131-33, 305-06
178, 307
-
178, 308
32, 176, 309
188, 189, 310
188, 311
188, 312
179, 313
85, 314
157, 315
149, 160-62,
316

<!-- source-page: 348 -->
## Page 348

Index
absolute pixel height 155
action point of the pointer 176
actual image data 327
AES 4
Alcyon C 9
“align.c’’ program listing 146-47
alphanumeric mode 144, 162-67
“alphmode.c” program listing 167
alt key 179
application environment services. See
AES
AREA 114
area fill 110~11
“areafill.c’’ program listing 111
ascent line 145
ASK MOUSE 189
ASK RGB 89
aspect ratio 24
assembly language program shell 32-38
ASSIGN.SYS 4, 13
“assign.sys”’ program listing 17
attribute settings 3
AUTO folder 4
baseline 145
basepage 37
bindings, GEM 9
bit blit 119
bit block transfer 119
bit image 119
bit planes 101-03
blitter chip 119
block storage segment. See BSS
bottom lines 145
BOX 114
BSS 37
C program shell 30-32
cell 44, 145
character height 155-56
character rotation 150-52
character table offset 326-27
choice device 180, 185-86
circle 54
CIRCLE 63
“clip.c” program listing 86
clipping 85-86
COLOR 63, 113, 168
“colorl.c’’ program listing 76-77
color bit planes 101-02
color information, locating 74-77
color mask 77, 78
color monitor 16
color pens, default values table 74
color register and color values table 73
color registers 71-73
color settings 69-77
color value and register values table 73
“colorpat.c’’ program listing 104
colors, mixing 73-74
contr] array 5-6
control key 179
copy raster opaque 123-28
copy raster transparent 131-37
“copymode.c” program listing 126-27
“copytran.c” program listing 133-37
cursor movement functions 164
DEC VT-52 terminal 165
descent line 145
device 4 189
device driver file 13-14
device identification number 5, 13-14
Digital Research GEM bindings 9
“diskfont.c” program listing 159-60
display device 15
display device numbers 17-18
drawing modes 77-85
drawing operation 26
DRAWMODE 89, 138-39
“drawmode.bas” program listing 90
“drawmode.c” program listing 81-82
“drawmode.s” program listing 82-85
“dummy.c’” program listing 31
“dummy.s’” program listing 38
“effects.c’’ program listing 154
ellipse 54
ELLIPSE 63
escape function 162-66
extended basic input/output system.
See XBIOS
extended inquire 27-29
extended keyboard codes 319-21
FILL 113
fill color 105-15
fill commands, BASIC 113-15
fill settings inquiry 105-06
“fill.bas” program listing 114-15
filled shape generalized drawing
primitives (GDPs) 106-10
“fillmode.c’’ program listing 109-10
“fillpat.c’” program listing 95-96
“fillpat.s” program listing 96-99
flood fill 111-13
“flood.c’” program listing 112-13
font file, VDI 325-27
font header 325-26
341

<!-- source-page: 349 -->
## Page 349

fonts, text
setting 158
unloading 158-59
using disk-based 156-58
fringe 121
function reference, VDI 195-316
GDOS 4, 13, 87
GDOS extensions 156
GDOS.PRG 4, 13
GDP 22, 25, 54
“gdplinel.c’” program listing 57-58
“gdplines.s” program listing 59-63
GDPs 106
GEM 3
GEM standard format 122
GEM workstation 13
opening 13
generalized drawing primitives. See
GDP
GET 138
getrez 18
GOTOXY 158
graphics device operating system.
See GDOS
graphics environment manager operating system. See GEM
graphics object 77, 78
graphics settings, BASIC 89-90
graphics text 143-62
graphics text from assembly language
169-71
GSHAPE 138
half line 145
handle 15, 20
hatch pattern fill 94
hollow fill pattern 94, 106
horizontal offset table 327
hot spot 176
INP 189
INPUT 189
input array 16-21
input functions, BASIC 189
input functions, VDI 3, 175-89
inquiry commands 3
interleaved bit-map 122
interrupt basis 186
intin 5
intout 5
inverse video 78
keyboard 189
keyboard codes, extended 319-21
Lattice C 10
line-drawing, assembly language 58
line-drawing GDPs 54
line-drawing, ST BASIC 63-64
LINEF 64
342
LINEPAT 64
lines 46-58
color 50-51
end styles 52-54
patterned 47-49
width 51
“lines.bas” program listing 64-65
locator device 180, 181-82
logical input device 180-86
machine-specific format 122
marker 41-46
~~
marker types 42
MAT DRAW 64
MAT LINEF 64
MCC BASIC 8
Megamax C 9
memory form definition block. See
MFDB
MFDB 119-21
micron 24
microspace justification 147~48
monochrome screen 16
mono-spaced fonts 327
mouse 176
mouse button press 187
mouse movement routine 187
mouse ponter 176-79
mouse pointer redraw 187
“mousebox.bas” program listing
190-91
“mousebox.c” program listing 183-85
multicolor pattern fill 101-05
NDC 18, 87-89
“ndc.c’”’ program listing 88-89
normalized device coordinate. See NDC
nybble 122
opcode 5
outlining 105-15
output 15
output array 21-27
PATTERN 114
pattern fills 93-104
pattern type fill 94
—
PCIRCLE 113
PELLIPSE 113
physical screen device handle 189
physical workstation 29
a
pixel 48
“plinel.c”’ program listing 46-47
“pline2.c” program listing 50-51
“pline3.c” program listing 52-53
“pmark1.c’’ program listing 41-42
“pmark2.c” program listing 44
point 155
primitives 3
a
PRINT 168

<!-- source-page: 350 -->
## Page 350

printer points 155
proportionally spaced fonts 148
pseudo-devices 15
ptsin 5
ptsout 5
PUT 138
raster coordinate system. See RC system
raster form 119
raster functions 119-37
raster operations in BASIC 138-39
RC system 18-20
rectangle, filled 93
request mode 78, 180
reverse transparent mode 78
rotating text figure 150
rotext.c program listing 151-52
sample mode 180
set writing mode 79-80
SETBLOCK 37
shell 30
“shell.c’’ program listing 31
“shell.s’” program listing 33-36
shift key 179
solid pattern fill 94
SSHAPE 138
“stdform.c” program listing 130-31
string device 180, 182-83
sub-function ID number 5
system characters 331-35
system clock 187
terminal emulation 165-66
text 143
text alignment 144-47
text color 152
text functions, BASIC 168
text string, sizing 148-50
text types 152-54
“text.bas” program listing 16-69
“text.s” program listing 170-71
timer tick routine 187
top lines 145
TOS 4
TOS takes parameters. See TTP
TPA 37
Tramiel operating system (TOS) 4
transform form 128-31
transient program area. See TPA
transparent mode 78, 106
transparent opaque 177
TTP 37
user-defined pattern fill 94, 99-101
“aserfill.c’’ program listing 107-08
valuator device 180, 185-86
VDI 3
arrays 4-7
using 4-6
VDI calls
assembly language 6-7
ST BASIC 7-8
VDI function reference 195-316
VDI routines, calling from C 8-10
VDISYS 8, 189
vector exchange routines 188-89
virtual device interface. See VDI
virtual screen workstations 15-27
Vsync 133
VT-52 escape codes 165-66
workstation settings 16
workstation ID number 20
writing modes 131-32
XBIOS 18
XOR mode 78-79, 128
343

<!-- source-page: 352 -->
## Page 352

COMPUTE! Books
Ask your retailer for these COMPUTE! Books or order directly from
COMPUTE!.
Call toll free (in US) 1-800-346-6767 (in NY 212-887-8525) or write COM-
PUTE! Books, P.O. Box 5038, F.D.R. Station, New York, NY 10150.
Quantity
Title
Price’
Total
COMPUTEI’s ST Artist (070-X)
18.95
——— COMPUTE!’s First Book of the Atari ST (020-3)
16.95 ___
—__—— COMPUTE!’s Kids and the Atari ST (038-6)
14.95
_
—___ COMPUTEI’s ST Applications Guide:
19.95 ___
Programming in C (078-5)
———— COMPUTE!’s St Applications (067-Xx)
16.95
——~ COMPUTE!’s ST Programmer’s Guide (023-8)
17.95 ___
—_—.
The Elementary Atari ST (024-6)
18.95 _
—__—— ._ Elementary St BASIC (034-3)
14.95
_
—~-~—
Introduction to Sound and Graphics
16.95 _
on the Atari ST (035-1)
—__—._ Learning C: Programming Graphics on the
$18.95
Amiga and Atari ST (064-5)
“Add $2.00 per book for shipping and handling.
Outside US add $5.00 air mail or $2.00 surface mail.
NC residents add 5% sales tax.
NY residents add 8.25% sales tax
Shipping & handling: $2.00/book
Total payment
All orders must be prepaid (check, charge, or money order).
All payments must be in US funds.
01 Payment enclosed.
Charge
Visa
OMasterCard
O American Express
Acct. No
Exp. Date
(Required)
Name
Address
City
State
Zip
“Allow 4-5 weeks for delivery.
Prices and availability subject to change.
Current catalog available upon request.

<!-- source-page: 354 -->
## Page 354

|
|
|
|
NO POSTAGE
NECESSARY
IF MAILED
IN THE
UNITED STATES
ee
BUSINESS REPLY MAIL
—a
FIRSTCLASS
PERMIT NO. 7551
DES MOINES, IA
aiineaiieeameuees
POSTAGE WILL BE PAID BY ADDRESSEE
REE!
COMPUTE!’s Atari ST
ea ats
Disk & Magazine
—
PO. Box 10775
Des Moines, IA 50347-0775
NEW
FOR ATARI ST USERS
COMPUTE!’s ATARI ST
DISK & MAGAZINE
Only COMPUTE!’s Atari ST Disk &
Magazine gives you all this and more
in each big issue:
TOP QUALITY PROGRAMS: Application programs for home and business.
Utilities. Games. Educational programs for
the youngsters.
All
are already on
an
enclosed disk and ready to run. For example: a typical disk might contain an elaborate adventure game written in BASIC, a
programming utility written in machine
language, a dazzling graphics
demo in compiled Pascal, and a
useful home or business application written in Forth or C.
NEOCHROME OF THE
MONTH: What are computer
artists doing with the Atari ST?
Each issue contains
a Neochrome picture file—ready to
load and admire.
REGULAR COLUMNS:
If
you’re a programmer—or would
like to be—you’ll love our columns on ST programming techniques and
the C language. Or check out our column
on the latest events and happenings
throughout the ST community. Or send
your questions and helpful hints to our
Reader's Feedback column.
REVIEWS: Honest evaluations of the
latest, best software and hardware for the
Atari ST.
NEWS & PRODUCTS: A comprehensive listing
of
all the new software and
peripherals for your ST.
AND MORE: Interviews with
ST newsmakers, reports on the
latest industry trade shows, and
overviews
of significant new
product introductions.
Don’t miss a single big issue. Subscribe to COMPUTE!’ Atari ST
Disk & Magazine now through
this special money-saving offer.
Return coupon above or call
1-800-247-5470 (in lowa
1-800-532-1272).
COMPUTE! Publications, Inc.
Part of ABC Consumer Magazines, Inc
One of the ABC Publishing Companies
RETURN COUPON ABOVE TO ENJOY
CHARTER SUBSCRIPTION PRIVILEGES

<!-- source-page: 355 -->
## Page 355

@
@
CHARTER SUBSCRIPTION FORM
C) Payment enclosed
[] Charge my VISA/MasterCard
[ YES!
Sign me up for six
Credit Card #
Exp. Date
issues (a full year’s
:
subscription) atthe
Signature
special introductory
erates
price of just $59.95.
Isave more than $17
—adaress
off the newsstand
price.
City
State
Zip
Outside U.S.A., please add $6 (U.S.) per year for postage.
CLIP THIS
AND SAVE |
Here's your chance to cash in with big
savings on COMPUTE!5 Atari ST Disk &
Magazine—the exciting new publication
devoted exclusively to the special needs
and interests of Atari ST users like you.
» Neochrome Art
rexly-to-lond pict
Lee Noet
cee
Every other month, COMPUTE!'’s
Atari ST Disk & Magazine brings you exciting new action-packed programs
already on disk! Just load and you’re
ready to run.
You can depend on getting at least
five new programs in each issue—highquality applications, educational, home finance, utility, and game programs you
and the entire family will use, enjoy, and
profit from all year long.
And here's even more good news.
Subscribe now to COMPUTE!’ Atari ST
Disk & Magazine and take advantage of
big Charter Subscription savings. Get a
full year’s subscription for just $59.95.
You save over $17 off the newsstand
price.
No other publication gives you more
for your Atari ST than COMPUTE!5 Atari
ST
Disk & Magazine. So sign up now by
using the coupon above—or call 1-800-
247-5470 (in lowa 1-800-532-1272).

<!-- source-page: 356 -->
## Page 356

The Complete VDI Reference
If you're going to design and write software for the Atari ST in
BASIC, machine language, or C—and take advantage of alll
the advanced features the computer has to offer—you need
COMPUTE!’s Technical Reference Guide, Atari ST Volume
One: The VDI.
The first in a series of three reference guides for the Atari
ST personal computer, this book has everything you need to
create sophisticated, professional-looking graphics. Here’s
just a sample of what you'll find inside:
* A complete easy-to-use VDI (Virtual Design Interface) function reference section.
* Numerous sample programs which demonstrate exactly
how to implement VDI function calls from C, machine language, and BASIC.
¢ Drawing and manipulating image blocks.
* How fo
fill shapes and draw points and lines.
* How font files are organized.
* Three indices that make finding the right information easy
and quick,
* A complete listing of extended keyboard codes.
Written in a clear and concise style by the noted ST
author Sheldon Leemon, COMPUTE!’s Technical Reference
Guide, Atari ST Volume One: The VDI is for every intermediate-to-advanced-level BASIC, C, and machine language
programmer who wants to tap the true potential of this powerful computer.
COMPUTE!’s Technical Reference Guide, Atari ST Volume
One: The VDI
is the complete tutorial and reference guide to
Q vital part of all ST software development.
ISBN 0-87455-093-9
$18.95
