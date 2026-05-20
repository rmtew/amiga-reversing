<!-- source-pdf: resources/platform_macos/docs/Inside_Macintosh_Volume_III_1985.pdf -->
<!-- source-pages: 290 -->

<!-- source-page: 1 -->
## Page 1

"
Apple® Inside Macintosh
Volume ill
Accounts
• • •

<!-- source-page: 2 -->
## Page 2

Inside Macintosh@
Volume III
....
......
Addison-Wesley Publishing Company, Inc.
Reading, Massachusetts
Menlo Park, California New York
Don Mills, Ontario
Wokingham, England
Amsterdam
Bonn
Sydney
Singapore Tokyo
Madrid
San Juan

<!-- source-page: 3 -->
## Page 3

Copyright© 1985 by Apple Computer, Inc.
All rights reserved. No part of this publication may be reproduced, stored in a
retrieval system, or transmitted, in any form or by any means, mechanical,
electronic, photocopying, recording, or otherwise, without prior written
permission of Apple Computer, Inc. Printed in the United States of America.
©Apple Computer, Inc., 1985
20525 Mariani A venue
Cupertino, CA 95014
(408) 996-1010
Apple, the Apple logo, LaserWriter, Lisa, Macintosh, the Macintosh logo, and
Mac Works are registered trademarks of Apple Computer, Inc.
MacDraw, MacPaint, and Mac Write are registered trademarks of Claris
Corporation.
Simultaneously published in the United States and Canada.
Written by Caroline Rose with Bradley Hacker, Robert Anders, Katie Withey,
Mark Metzler, Steve Chernicoff, Chris Espinosa, Andy Averill, Brent Davis, and
Brian Howard, assisted by Sandy Tompkins-Leffler and Louella Pizzuti. Special
thanks to Cary Clark and Scott Knaster.
This book was produced using the Apple Macintosh computer and the LaserWriter
printer.
ISBN 0-201-17733-1
KLMNOPQRST-MU-93210
11th printing, June 1990

<!-- source-page: 4 -->
## Page 4

Inside Macintosh
Volume III

<!-- source-page: 5 -->
## Page 5

WARRANTY INFORMATION
ALL IMPLIED WARRANTIES ON THIS MANUAL, INCLUDING IMPLIED
WARRANTIES OF MERCHANTAillLITY AND FITNESS FOR A
PARTICULAR PURPOSE, ARE LIMITED IN DURATION TO NINETY (90)
DAYS FROM THE DATE OF THE ORIGINAL RETAIL PURCHASE OF
THIS PRODUCT.
Even though Apple has reviewed this manual, APPLE MAKES NO WARRANTY OR
REPRESENTATION, EITHER EXPRESS OR IMPLIED, WITH RESPECT TO
THIS MANUAL, ITS QUALITY, ACCURACY, MERCHANTABILITY, OR
FITNESS FOR A PARTICULAR PURPOSE. AS A RESULT, THIS MANUAL
IS SOLD "AS IS," AND YOU, THE PURCHASER, ARE ASSUMING THE
ENTIRE RISK AS TO ITS QUALITY AND ACCURACY.
IN NO EVENT WILL APPLE BE LIABLE FOR DIRECT, INDIRECT,
SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES RESULTING
FROM ANY DEFECT OR INACCURACY IN THIS MANUAL, even if advised of
the possibility of such damages.
THE WARRANTY AND REMEDIES SET FORTH ABOVE ARE EXCLUSIVE
AND IN LIEU OF ALL OTHERS, ORAL OR WRITTEN, EXPRESS OR
IMPLIED. No Apple dealer, agent, or employee is authorized to make any modification,
extension, or addition lo this warranty.
Some stales do not allow the exclusion or limitation of implied warranties or liability for
incidental or consequential damages, so the above limitation or exclusion may not apply to you.
This warranty gives you specific legal rights, and you may also have other rights which vary
from state to state.

<!-- source-page: 6 -->
## Page 6

Contents
1
Preface
3
About Inside Macintosh
4
A Horse of a Different Color
5
The Structure of a Typical Chapter
5
Conventions
7
1 Finder Interface
9
About This Chapter
9
Signatures and File Types
15
2 The Macintosh Hardware
17
About This Chapter
17
Overview of the Hardware
18
The Video Interface
20
The Sound Generator
22
The sec
25
The Mouse
29
The Keyboard and Keypad
33
The Disk Interface
36
The Real-Time Clock
39
The VIA
42
System Startup
43
Summary
47
3 Summary
49
About This Chapter
50
Apple Talk Manager
65
Binary-Decimal Conversion Package
66
Control Manager
71
Desk Manager
73
Device Manager
80
Dialog Manager
85
Disk Driver
88
Disk Initialization Package
90
Event Manager, Operating System
94
Event Manager, Toolbox
98
File Manager
113
Font Manager
118
International Utilities Package

<!-- source-page: 7 -->
## Page 7

Inside Macintosh
124
Memory Manager
130
Menu Manager
134
Package Manager
135
Printing Manager
141
QuickDraw
154
Resource Manager
157
Scrap Manager
159
Segment Loader
161
Serial Drivers
165
Sound Driver
172
Standard File Package
176
System Error Handler
179
TextEdit
184
Utilities, Operating System
190
Utilities, Toolbox
193
Vertical Retrace Manager
195
Window Manager
201
Assembly Language
205
Appendix A: Result Codes
211
Appendix B: Routines That May Move or Purge Memory
215
Appendix C: System Traps
227
Appendix D: Global Variables
233
Glossary
261
Index

<!-- source-page: 8 -->
## Page 8

PREFACE
3
Aboutlnside Macintosh
3
The Language
4
What's in Each Volume
4
Version Numbers
4
A Horse of a Different Color
5
The Structure of a Typical Chapter
5
Conventions
Contents Ill-I

<!-- source-page: 9 -->
## Page 9

Inside Macintosh
III-2

<!-- source-page: 10 -->
## Page 10

Preface
ABOUT INSIDE MACINTOSH
Inside Macintosh is a three-volume set of manuals that tells you what you need to know to write
software for the Apple® Macintosh™ 128K, 512K, or XL (or a Lisa® running MacWorks™
XL). Although directed mainly toward programmers writing standard Macintosh applications,
Inside Macintosh also contains the information needed to write simple utility programs, desk
accessories, device drivers, or any other Macintosh software. It includes:
• the user interface guidelines for applications on the Macintosh
• a complete description of the routines available for your program to call (both those built
into the Macintosh and others on disk), along with related concepts and background
information
•a description of the Macintosh 128K and 512K hardware
It does not include information about:
• Programming in general.
• Getting started as a developer. For this, write to:
Developer Relations
Mail Stop 27-S
Apple Computer, Inc.
20525 Mariani A venue
Cupertino, CA 95014
•Any specific development system, except where indicated. You'll need to have additional
documentation for the development system you're using.
•The Standard Apple Numeric Environment (SANE), which your program can access to
perform extended-precision floating-point arithmetic and transcendental functions. This
environment is described in the Apple Numerics Manual.
You should already be familiar with the basic information that's in Macintosh, the owner's guide,
and have some experience using a standard Macintosh application (such as Mac Write™).
The Language
The routines you'll need to call are written in assembly language, but (with a few exceptions)
they're also accessible from high-level languages, such as Pascal on the Lisa Workshop
development system. Inside Macintosh documents the Lisa Pascal interfaces to the routines and
the symbolic names defined for assembly-language programmers using the Lisa Workshop; if
you're using a different development system, its documentation should tell you how to apply the
information presented here to that system.
Inside Macintosh is intended to serve the needs of both high-level language and assemblylanguage programmers. Every routine is shown in its Pascal form (if it has one), but assemblylanguage programmers are told how they can access the routines. Information of interest only to
assembly-language programmers is isolated and labeled so that other programmers can
conveniently skip it.
About Inside Macintosh III-3

<!-- source-page: 11 -->
## Page 11

Inside Macintosh
Familiarity with Lisa Pascal (or a similar high-level language) is recommended for all readers,
since it's used for most examples. Lisa Pascal is described in the documentation for the Lisa
Pascal Workshop.
What's in Each Volume
Inside Macintosh consists of three volumes. Volume I begins with the following information of
general interest:
• a "road map" to the software and the rest of the documentation
• the user interface guidelines
•an introduction to memory management (the least you need to know, with a complete
discussion following in Volume II)
•some general information for assembly-language programmers
It then describes the various parts of the User Interface Toolbox, the software in ROM that
helps you implement the standard Macintosh user interface in your application. This is followed
by descriptions of other, RAM-based software that's similar in function to the User Interface
Toolbox. (The software overview in the Road Map chapter gives further details.)
Volume II describes the Operating System, the software in ROM that does basic tasks such as
input and output, memory management, and interrupt handling. As in Volume I, some
functionally similar RAM-based software is then described.
Volume III discusses your program's interface with the Finder and then describes the Macintosh
128K and 512K hardware. A comprehensive summary of all the software is provided, followed
by some useful appendices and a glossary of all terms defined in Inside Macintosh.
Version Numbers
This edition of Inside Macintosh describes the following versions of the software:
•version 105 of the ROM in the Macintosh 128K or 512K
•version 112 of the ROM image installed by Mac Works in the Macintosh XL
• version 1.1 of the Lisa Pascal interfaces and the assembly-language definitions
Some of the RAM-based software is read from the file named System (usually kept in the System
Folder). This manual describes the software in the System file whose creation date is May 2,
1984.
A HORSE OF A DIFFERENT COLOR
On an innovative system like the Macintosh, programs don't look quite the way they do on other
systems. For example, instead of carrying out a sequence of steps in a predetermined order, your
program is driven primarily by user actions (such as clicking and typing) whose order cannot be
predicted.
Il/4 About Inside Macintosh

<!-- source-page: 12 -->
## Page 12

Preface
You'll probably find that many of your preconceptions about how to write applications don't
apply here. Because of this, and because of the sheer volume of information in Inside
Macintosh, it's essential that you read the Road Map chapter. It will help you get oriented and
figure out where to go next.
THE STRUCTURE OF A TYPICAL CHAPTER
Most chapters of Inside Macintosh have the same structure, as described below. Reading through
this now will save you a lot of time and effort later on. It contains important hints on how to find
what you're looking for within this vast amount of technical documentation.
Every chapter begins with a very brief description of its subject and a list of what you should
already know before reading that chapter. Then there's a section called, for example, "About the
Window Manager", which gives you more information about the subject, telling you what you
can do with it in general, elaborating on related user interface guidelines, and introducing
terminology that will be used in the chapter. This is followed by a series of sections describing
important related concepts and background information; unless they're noted to be for advanced
programmers only, you'll have to read them in order to understand how to use the routines
described later.
Before the routine descriptions themselves, there's a section called, for example, "Using the
Window Manager". It introduces you to the routines, telling you how they fit into the general
flow of an application program and, most important, giving you an idea of which ones you'll
need to use. Often you'll need only a few routines out of many to do basic operations; by reading
this section, you can save yourself the trouble of learning routines you'll never use.
Then, for the details about the routines, read on to the next section. It gives the calling sequence
for each routine and describes all the parameters, effects, side effects, and so on.
Following the routine descriptions, there may be some sections that won't be of interest to all
readers. Usually these contain information about advanced techniques, or behind the scenes
details for the curious.
For review and quick reference, each chapter ends with a summary of the subject matter,
including the entire Pascal interface and a separate section for assembly-language programmers.
CONVENTIONS
The following notations are used in Inside Macintosh to draw your attention to particular items of
information:
Note: A note that may be interesting or useful
Warning: A point you need to be cautious about
Assembly-language note: A note of interest to assembly-language programmers only
Conventions 111-5

<!-- source-page: 13 -->
## Page 13

Inside Macintosh
[Not in ROM]
Routines marked with this notation are not part of the Macintosh ROM. Depending on how
the interfaces have been set up on the development system you're using, these routines may or
may not be available. They're available to users of Lisa Pascal; other users should check the
documentation for their development system for more information. (For related information of
interest to assembly-language programmers, see chapter 4 of Volume I.)
III-6 Conventions

<!-- source-page: 14 -->
## Page 14

1 THE FINDER INTERFACE
9
About This Chapter
9
Signatures and File Types
10
Finder-Related Resources
10
Version Data
10
Icons and File References
11
Bundles
11
An Example
12
Formats of Finder-Related Resources
Contents III-7

<!-- source-page: 15 -->
## Page 15

Inside Macintosh
///-8

<!-- source-page: 16 -->
## Page 16

The Finder I nteiface
ABOUT THIS CHAPTER
This chapter describes the interface between a Macintosh application program and the Finder.
You should already be familiar with the details of the User Interface Toolbox and the Operating
System.
SIGNATURES AND FILE TYPES
Every application must have a unique signature by which the Finder can identify it The
signature can be any four-character sequence not being used for another application on any
currently mounted volume (except that it can't be one of the standard resource types). To ensure
uniqueness on all volumes, you must register your application's signature by writing to:
Macintosh Technical Support
Mail Stop 3-T
Apple Computer, Inc.
20525 Mariani A venue
Cupertino, CA 95014
Note: There's no need to register your own resource types, since they'll usually exist
only in your own applications or documents.
Signatures work together with tile types to enable the user to open or print a document (any file
created by an application) from the Finder. When the application creates a file, it sets the file's
creator and file type. Normally it sets the creator to its signature and the file type to a fourcharacter sequence that identifies files of that type. When the user asks the Finder to open or print
the file, the Finder starts up the application whose signature is the file's creator and passes the file
type to the application along with other identifying information, such as the file name. (More
information about this process is given in chapter 2 of Volume II.)
An application may create its own special type or types of files. Like signatures, file types must
be registered with Macintosh Technical Support to ensure uniqueness. When the user chooses
Open from an application's File menu, the application will display (via the Standard File Package)
the names of all files of a given type or types, regardless of which application created the files.
Having a unique file type for your application's special files ensures that only the names of those
files will be displayed for opening.
Note: Signatures and file types may be strange, unreadable combinations of characters;
they're never seen by end users of Macintosh.
Applications may also create existing types of files. There might, for example, be an application
that merges two Mac Write documents into a single document. In such cases, the application
should use the same file type as the original application uses for those files. It should also specify
the original application's signature as the file's creator; that way, when the user asks the Finder to
open or print the file, the Finder will call on the original application to perform the operation. To
learn the signature and file types used by an existing application, check with the application's
manufacturer.
Signatures and File Types Ill-9

<!-- source-page: 17 -->
## Page 17

Inside Macintosh
Files that consist only of text-a stream of characters, with Return characters at the ends of
paragraphs or short lines-should be given the standard file type TEXT'. This is the type that
Mac Write gives to text only files it creates, for example. If your application uses this file type, its
files will be accepted by MacWrite and it in turn will accept Mac Write text-only files (likewise for
any other application that deals with TEXT' files, such as MacTerminal). Your application can
give its own signature as the file's creator if it wants to be called to open or print the file when the
user requests this from the Finder.
For files that aren't to be opened or printed from the Finder, as may be the case for certain data
files created by the application, the creator should be set to '????' (and the file type to whatever is
appropriate).
FINDER-RELATED RESOURCES
To establish the proper interface with the Finder, every application's resource file must specify
the signature of the application along with data that provides version information. In addition,
there may be resources that provide information about icons and files related to the application.
All of these Finder-related resources are described below, followed by a comprehensive example
and (for interested programmers) the exact formats of the resources.
Version Data
Your application's resource file must contain a special resource that has the signature of the
application as its resource type. This resource is called the version data of the application. The
version data is typically a string that gives the name, version number, and date of the application,
but it can in fact be any data at all. The resource ID of the version data is 0 by convention.
Part of the process of installing an application on the Macintosh is to set the creator of the file that
contains the application. You set the creator to the application's signature, and the Finder copies
the corresponding version data into a resource file named Desktop. (The Finder doesn't display
this file on the Macintosh desktop, to ensure that the user won't tamper with it.)
Note: Additional, related resources may be copied into the Desktop file; see "Bundles"
below for more information.
Icons and File References
For each application, the Finder needs to know:
• the icon to be displayed for the application on the desktop, if different from the Finder's
default icon for applications (see Figure 1)
• if the application creates any files, the icon to be displayed for each type of file it creates, if
different from the Finder's default icon for documents
The Finder learns this information from resources called file references in the application's
resource file. Each file reference contains a file type and an ID number, called a local ID, that
identifies the icon to be displayed for that type of file. (The local ID is mapped to an actual
resource ID as described under "Bundles" below.)
Il/-10 Signatures and File Types

<!-- source-page: 18 -->
## Page 18

The Finder Interface
D
Application
Document
Figure 1. The Finder's Default Icons
The file type for the application itself is 'APPL'. This is the file type in the file reference that
designates the application's icon. You also specify it as the application's file type at the same time
that you specify its creator-when you install the application on the Macintosh.
The ID number in a file ref~rence corresponds not to a single icon but to an icon list in the
application's resource file. The icon list consists of two icons: the actual icon to be displayed on
the desktop, and a mask consisting of that icon's outline filled with black (see Figure 2) .
•
Icon
Mask
Figure 2. Icon and Mask
Bundles
A bundle in the application's resource file groups together all the Finder-related resources. It
specifies the following:
• the application's signature and the resource ID of its version data
• a mapping between the local IDs for icon lists (as specified in file references) and the actual
resource IDs of the icon lists in the resource file
• local IDs for the file references themselves and a mapping to their actual resource IDs
When you install the application on the Macintosh, you set its "bundle bit"; the first time the
Finder sees this, it copies the version data, bundle, icon lists, and file references from the
application's resource file into the Desktop file. If there are any resource ID conflicts between the
icon lists and file references in the application's resource file and those in Desktop, the Finder will
change those resource IDs in Desktop. The Finder does this same resource copying and ID
conflict resolution when you transfer an application to another volume.
Note: The local IDs are needed only for use by the Finder.
An Example
Suppose you've written an application named SampWriter. The user can create a unique type of
document from it, and you want a distinctive icon for both the application and its documents. The
application's signature, as recorded with Macintosh Technical Support, is 'SAMP'; the file type
assigned for its documents is 'SAMF'. You would include the following resources in the
application's resource file:
Finder-Related Resources Ill-11

<!-- source-page: 19 -->
## Page 19

Inside Macintosh
Resource
Version data with
resource type 'SAMP'
Icon list
Icon list
File reference
File reference
Bundle
Resource ID
0
128
129
130
131
132
Description
The string 'SampWriter Version 1--2/1/85'
The icon for the application
The icon's mask
The icon for documents
The icon's mask
File type 'APPL'
Local ID 0 for the icon list
File type 'SAMF'
Local ID 1 for the icon list
Signature 'SAMP'
Resource ID 0 for the version data
For icon lists, the mapping:
local ID 0 ---7 resource ID 128
local ID 1 ---7 resource ID 129
For file references, the mapping:
local ID 2 ---7 resource ID 130
local ID 3 ---7 resource ID 131
Note: See the documentation for the development system you're using for information
about how to include these resources in a resource file.
Formats of Finder-Related Resources
The resource type for an application's version data is the signature of the application, and the
resource ID is 0 by convention. The resource data can be anything at all; typically it's a string
giving the name, version number, and date of the application.
The resource type for an icon list is 'ICN#'. The resource data simply consists of the icons, 128
bytes each.
The resource type for a file reference is 'FREF. The resource data has the format shown below.
Number of bytes
4 bytes
2 bytes
Contents
File type
Local ID for icon list
The resource type for a bundle is 'BNDL'. The resource data has the format shown below. The
format is more general than needed for Finder-related purposes because bundles will be used in
other ways in the future.
l//-12 Finder-Related Resources

<!-- source-page: 20 -->
## Page 20

Number of bytes
4 bytes
2 bytes
2 bytes
Contents
Signature of the application
Resource ID of version data
Number of resource types in bundle minus 1
For each resource type:
4 bytes
Resource type
2 bytes
For each resource:
2 bytes
2 bytes
Number of resources of this type minus 1
Local ID
Actual resource ID
The Finder Jruerface
A bundle used for establishing the Finder interface contains the two resource types 'ICN#' and
'FREF'.
Finder-Related Resources JJJ-13

<!-- source-page: 21 -->
## Page 21

Inside Macintosh
l//-14

<!-- source-page: 22 -->
## Page 22

2 THE MACINTOSH HARDWARE
17
About This Chapter
17
Overview of the Hardware
18
The Video Interface
20
The Sound Generator
22
Diagram
22
The sec
25
Diagram
25
The Mouse
28
Diagram
29
The Keyboard and Keypad
30
Keyboard Communication Protocol
31
Keypad Communication Protocol
33
The Disk Interface
34
Controlling the Disk-State Control Lines
34
Reading from the Disk Registers
35
Writing to the Disk Registers
36
Explanations of the Disk Registers
36
The Real-Time Clock
37
Accessing the Clock Chip
38
The One-Second Interrupt
39
The VIA
39
VIA Register A
39
VIA Register B
40
The VIA Peripheral Control Register
40
The VIA Timers
41
VIA Interrupts
42
Other VIA Registers
42
System Startup
43
Summary
Contents Ill-15

<!-- source-page: 23 -->
## Page 23

Inside Macintosh
III-16

<!-- source-page: 24 -->
## Page 24

The Maciruosh Hardware
ABOUT THIS CHAPTER
This chapter provides a basic description of the hardware of the Macintosh 128K and 512K
computers. It gives you information that you'll need to connect other devices to the Macintosh
and to write device drivers or other low-level programs. It will help you figure out which
technical documents you'll need to design peripherals; in some cases, you'll have to obtain
detailed specifications from the manufacturers of the various interface chips.
-
This chapter is oriented toward assembly-language programmers. It assumes you're familiar with
the basic operation of microprocessor-based devices. Knowledge of the Macintosh Operating
System will also be helpful.
Warning: Only the Macintosh 128K and 512K are covered in this chapter. In particular,
note that the memory addresses and screen size are different on the Macintosh XL (and
may be different in future versions of the Macintosh). To maintain software compatibility
across the Macintosh line, and to allow for future changes to the hardware, you're strongly
advised to use the Toolbox and Operating System routines wherever possible.
To learn how your program can determine which hardware environment it's operating in, see the
description of the Environs procedure in chapter 13 of Volume II.
OVERVIEW OF THE HARDWARE
The Macintosh computer contains a Motorola MC68000 microprocessor clocked at 7.8336
megahertz, random access memory (RAM), read-only memory (ROM), and several chips that
enable it to communicate with external devices. There are five I/O devices: the video display; the
sound generator; a Synertek SY6522 Versatile Interface Adapter (VIA) for the mouse and
keyboard; a Zilog Z8530 Serial Communications Controller (SCC) for serial communication; and
an Apple custom chip, called the IWM ("Integrated Woz Machine") for disk control.
The Macintosh uses memory-mapped 1/0, which means that each device in the system is accessed
by reading or writing to specific locations in the address space of the computer. Each device
contains logic that recognizes when it's being accessed and responds in the appropriate manner.
The MC68000 can directly access 16 megabytes (Mb) of address space. In the Macintosh, this is
divided into four equal sections. The first four Mb are for RAM, the second four Mb are for
ROM, the third are for the SCC, and the last four are for the IWM and the VIA. Since each of the
devices within the blocks has far fewer than four Mb of individually addressable locations or
registers, the addresses within each block "wrap around" and are. repeated several times within the
block.
RAM is the "working memory" of the system. Its base address is address 0. The first 256 bytes
of RAM (addresses 0 through $FF) are used by the MC68000 as exception vectors; these are
the addresses of the routines that gain control when~ver an exception such as an interrupt or a trap
occurs. (The summary at the end of this chapter includes a list of all the exception vectors.)
RAM also contains the system and application heaps, the stack, and other information used by
applications. In addition, the following hardware devices share the use of RAM with the
MC68000:
Overview of the Hardware III-17

<!-- source-page: 25 -->
## Page 25

Inside Macintosh
•the video display, which reads the infonnation for the display from one of two screen
buffers
• the sound generator, which reads its infonnation from one of two sound buffers
• the disk speed controller, which shares its data space with the sound buffers
The MC68000 accesses to RAM are interleaved (alternated) with the video display's accesses
during the active portion of a screen scan line (video scanning is described in the next section).
The sound generator and disk speed controller are given the first access after each scan line. At
all other times, the MC68000 has unintenupted access to RAM, increasing the average RAM
access rate to about 6 megahertz (MHz).
ROM is the system's pennanent read-only memory. Its base address, $400000, is available as
the constant romStart and is also stored in the global variable ROMBase. ROM contains the
routines for the Toolbox and Operating System, and the various system traps. Since the ROM is
used exclusively by the MC68000, it's always accessed at the full processor rate of 7.83 MHz.
The address space reserved for the device 1/0 contains blocks devoted to each of the devices
within the computer. This region begins at address $800000 and continues to the highest address
at $FFFFFF.
Note: Since the VIA is involved in some way in almost every operation of the Macintosh,
the following sections frequently refer to the VIA and VIA-related constants. The VIA
itself is described later, and all the constants are listed in the summary at the end of this
chapter.
THE VIDEO INTERFACE
The video display is created by a moving electron beam that scans across the screen, turning on
and off as it scans in order to create black and white pixels. Each pixel is a square, approximately
1174 inch on a side.
To create a screen image, the electron beam starts at the top left comer of the screen (see
Figure 1). The beam scans horizontally across the screen from left to right, creating the top line
of graphics. When it reaches the last pixel on the right end of the top line it turns off, and
continues past the last pixel to the physical right edge of the screen. Then it flicks invisibly back
to the left edge and moves down one scan line. After tracing across the black border, it begins
displaying the data in the second scan line. The time between the display of the rightmost pixel
on one line and the leftmost pixel on the next is called the horizontal blanking interval. When
the electron beam reaches the last pixel of the last (342nd) line on the screen, it traces out to the
right edge and then flicks up to the top left corner, where it traces the left border and then begins
once again to display the top line. The time between the last pixel on the bottom line and the first
one on the top line is called the vertical blanking interval. At the beginning of the vertical
blanking interval, the VIA generates a vertical blanking interrupt.
The pixel clock rate (the frequency at which pixels are displayed) is 15.6672 MHz, or about .064
microseconds (µsec) per pixel. For each scan line, 512 pixels are drawn on the screen, requiring
32.68 µsec. The horizontal blanking interval takes the time of an additional 192 pixels, or 12.25
µsec. Thus, each full scan line takes 44.93 µsec, which means the horizontal scan rate is 22.25
kilohertz.
III-18 Over-view of the Hardware

<!-- source-page: 26 -->
## Page 26

vertical
blanking
ends here
horizontal
I blanking ends
there
512 pixels wide
The Macintosh Hardware
horizontal
blanking startsl
here
black
border
vertical
blanking
starts here
Figure 1. Video Scanning Pattern
A full screen display consists of 342 horizontal scan lines, occupying 15367 .65 µsec, or about
15.37 milliseconds (msec). The vertical blanking interval takes the time of an additional 28 scan
lines-1258.17 µsec, or about 1.26 msec. This means the full screen is redisplayed once every
16625.8 µsec. That's about 16.6 msec per frame, which means the vertical scan rate (the full
screen display frequency) is 60.15 hertz.
The video generator uses 21,888 bytes of RAM to compose a bit-mapped video image 512 pixels
wide by 342 pixels tall. Each bit in this range controls a single pixel in the image: A 0 bit is
white, and a 1 bit is black.
There are two screen buffers (areas of memory from which the video circuitry can read
information to create a screen display): the main buffer and the alternate buffer. The starting
addresses of the screen buffers depend on how much memory you have in your Macintosh. In a
Macintosh 128K, the main screen buffer starts at $1A700 and the alternate buffer starts at
$12700; for a 512K Macintosh, add $60000 to these numbers.
Warning: To be sure you don't use the wrong area of memory and to maintain
compatibility with future Macintosh systems, you should get the video base address and bit
map dimensions from screenBits (see chapter 6 of Volume I).
Each scan line of the screen displays the contents of 32 consecutive words of memory, each word
controlling 16 horizontally adjacent pixels. In each word, the high-order bit (bit 15) controls the
leftmost pixel and the low-order bit (bit 0) controls the rightmost pixel. The first word in each
scan line follows the last word on the line above it. The starting address of the screen is thus in
The Video Interface III-19

<!-- source-page: 27 -->
## Page 27

Inside Macintosh
the top left comer, and the addresses progress from there to the right and down, to the last byte in
the extreme bottom right corner.
Normally, the video display doesn't flicker when you read from or write to it, because the video
memory accesses are interleaved with the processor accesses. But if you're creating an animated
image by repeatedly drawing the graphics in quick succession, it may appear to flicker if the
electron beam displays it when your program hasn't finished updating it, showing some of the
new image and some of the old in the same frame.
One way to prevent flickering when you're updating the screen continuously is to use the vertical
and horizontal blanking signals to synchronize your updates to the scanning of video memory.
Small changes to your screen can be completed entirely during the interval between frames (the
first 1.26 msec following a vertical blanking interrupt), when nothing is being displayed on the
screen. When making larger changes, the trick is to keep your changes happening always ahead
of the spot being displayed by the electron beam, as it scans byte by byte through the video
memory. Changes you make in the memory already passed over by the scan spot won't appear
until the next frame. If you start changing your image when the vertical blanking interrupt occurs,
you have 1.26 msec of unrestricted access to the image. After that, you can change progressively
less and less of your image as it's scanned onto the screen, starting from the top (the lowest video
memory address). From vertical blanking interrupt, you have only 1.26 msec in which to change
the first (lowest address) screen location, but you have almost 16.6 msec to change the last
(highest address) screen location.
Another way to create smooth, flicker-free graphics, especially useful with changes that may take
more 16.6 msec, is to use the two screen buffers as alternate displays. If you draw into the one
that's currently not being displayed, and then switch the buffers during the next vertical blanking,
your graphics will change all at' once, producing a clean animation. (See chapter 11 of Volume II
to find out how to specify tasks to be performed during vertical blanking.)
If you want to use the alternate screen buffer, you'll have to specify this to the Segment Loader
(see chapter 2 of Volume II for details). To switch to the alternate screen buffer, clear the
following bit of VIA data register A (vBase+vBufA):
vPage2
.EQU
6
;O = alternate screen buffer
For example:
BCLR
#vPage2,vBase+vBufA
To switch back to the main buffer, set the same bit.
Warning: Whenever you change a bit in a VIA data register, be sure to leave the other
bits in the register unchanged.
Warning: The alternate screen buffer may not be supported in future versions of the
Macintosh.
THE SOUND GENERATOR
The Macintosh sound circuitry uses a series of values taken from an area of RAM to create a
changing waveform in the output signal. This signal drives a small speaker inside the Macintosh
III-20 The Video Interface

<!-- source-page: 28 -->
## Page 28

The Macintosh Hardware
and is connected to the external sound jack on the back of the computer. If a plug is inserted into
the external sound jack, the internal speaker is disabled. The external sound line can drive a load
of 600 or more ohms, such as the input of almost any audio amplifier, but not a directly
connected external speaker.
The sound generator may be turned on or off by writing 1 (off) or 0 (on) to the following bit of
VIA data register B (vBase+vBufB):
vSndEnb
.EQU
7
;O
sound enabled, 1 = disabled
For example:
BSET
#vSndEnb,vBase+vBufB
;turn off sound
By storing a range of values in the sound buffer, you can create the corresponding waveform in
the sound channel. The sound generator uses a form of pulse-width encoding to create sounds.
The sound circuitry reads one word in the sound buffer during each horizontal blanking interval
(including the "virtual" intervals during vertical blanking) and uses the high-order byte of the
word to generate a pulse of electricity whose duration (width) is proportional to the value in the
byte. Another circuit converts this pulse into a voltage that's attenuated (reduced) by a three-bit
value from the VIA. This reduction corresponds to the current setting of the volume level. To set
the volume directly, store a three-bit number in the low-order bits of VIA data register A
(vBase+vBufA). You can use the following constant to isolate the bits involved:
vSound
.EQU
7
;sound volume bits
Here's an example of how to set the sound level:
MOVE .B
ANDI.B
ORI.B
MOVE.B
vBase+vBufA,DO
#255-vSound,DO
#3,DO
DO,vBase+vBufA
;get current value of register A
;clear the sound bits
;set medium sound level
;put the data back
After attenuation, the sound signal is passed to the audio output line.
The sound circuitry scans the sound buffer at a fixed rate of 370 words per video frame, repeating
the full cycle 60.15 times per second. To create sounds with frequencies other than multiples of
the basic scan rate, you must store phase-shifted patterns into the sound buffer between each
scan. You can use the vertical and horizontal blanking signals (available in the VIA) to
synchronize your sound buffer updates to the buffer scan. You may find that it's much easier to
use the routines in the Sound Driver to do these functions.
Warning: The low-order byte of each word in the sound buffer is used to control the
speed of the motor in the disk drive. Don't store any information there, or you'll interfere
with the disk 110.
There are two sound buffers, just as there are two screen buffers. The address of the main sound
buffer is stored in the global variable SoundBase and is also available as the constant soundLow.
The main sound buffer is at $1FDOO in a 128K Macintosh, and the alternate buffer is at $1Al00;
for a 512K Macintosh, add $60000 to these values. Each sound buffer contains 370 words of
data. As when you want to use the alternate screen buffer, you'll have to specify to the Segment
Loader that you want the alternate buffer (see chapter 2 of Volume II for details). To select the
alternate sound buffer for output, clear the following bit of VIA data register A (vBase+vBufA):
The Sound Generator Ill-21

<!-- source-page: 29 -->
## Page 29

Inside Macintosh
vSndPg2
.EQU
3
;0 = alternate sound buffer
To return to the main buffer, set the same bit.
Warning: Be sure to switch back to the main sound buffer before doing a disk access, or
the disk won't work properly.
Warning: The alternate sound buffer may not be supported in future versions of the
Macintosh.
There's another way to generate a simple, square-wave tone of any frequency, using almost no
processor intervention. To do this, first load a constant value into all 370 sound buffer locations
(use $00's for minumum volume, $FFs for maximum volume). Next, load a value into the
VIA's timer 1 latches, and set the high-order two bits of the VIA's auxiliary control register
(vBase+vACR) for "square wave output" from timer 1. The timer will then count down from the
latched value at 1.2766 µsecJcount, over and over, inverting the vSndEnb bit of VIA register B
(vBase+vBuffi) after each count down. This takes the constant voltage being generated from the
sound buffer and turns it on and off, creating a square-wave sound whose period is
2 * 1.2766 µsec * timer l's latched value
Note: You may want to disable timer 1 interrupts during this process (bit 6 in the VIA's
interrupt enable register, which is at vBase+vIER).
To stop the square-wave sound, reset the high-order two bits of the auxiliary control register.
Note: See the SY6522 technical specifications for details of the VIA registers. See also
"Sound Driver Hardware" in chapter 8 of Volume II.
Diagram
Figure 2 shows a block diagram for the sound port
THE sec
The two serial ports are controlled by a Zilog Z8530 Serial Communications Controller
(SCC). The port known as SCC port A is the one with the modem icon on the back of the
Macintosh. SCC port B is the one with the printer icon.
Macintosh serial ports conform to the EIA standard RS422, which differs from the more common
RS232C standard. While RS232C modulates a signal with respect to a common ground ("singleended" transmission), RS422 modulates two signals against each other ("differential"
transmission). The RS232C receiver senses whether the received signal is sufficiently negative
with respect to ground to be a logic "l", whereas the RS422 receiver simply senses which line is
more negative than the other. This makes RS422 more immune to noise and interference, and
more versatile over longer distances. If you ground the positive side of each RS422 receiver and
leave unconnected the positive side of each transmitter, you've converted to EIA standard RS423,
which can be used to communicate with most RS232C devices over distances up to fifty feet or
so.
III-22 The Sound Generator

<!-- source-page: 30 -->
## Page 30

-
0
>. 41)
.._ n
~ ::J
41) (\')
CJ)
"O
-
<ti '<r
41) '<r
... -
°' 41)
-- c
"O -
... c
0
<ti
~ 0
~ n
41) c
c
41)
<( ~
0 n
The Macintosh Hardware
Sound 0
output
d'
connector
···
... -------,
Internal speaker
(disconnected when
sound output
connecter is used)
______ _,l ___ --2
6522 (VIA)
Sound/ disk-speed
buffer (in RAM)
PAOl---_.r.V7o7
1u_m_e_c_on~t~ro"""'."11
Alternate
PA1 i----~ (eight levels)
PA2r---+L~:::..:..=.....:.:..:.::.:.;.~
buffer PA3
High
(even)
byte
Low
(odd)
byte
Disk I~ ..... .,
Disk I~· ·· ·· ..  \.
Di sk I~ ...... \-..
O !sound
1 (Sound
2 (Sound
3 !s ound
I
I
I
D i sk k · · ........ ::}:::-,_
··:=:·.
· ::~
..
...
...
16E (Sound Disk I~ · ·· ··
..... .
16F (Sound Disk I
..... .
170 (Sound Disk
I ~·· · //
171 (Sound Disk 1~ ... /
Alternate buffer
O (Sound
1 (Sound
I
I
I
Disk 1-i· .. ·· ..
Disk I~· .. ···.>·.
:
.... _, --
1
1 SF (Sound Disk I
. .
170 (Sound Disk 1-i· · .. ··./
171 (Sound Disk I~ · · · .··
Sound On-off switch
reset
PB7
(square-wave
(timer 1)
generator)
Dig i ta 1-to-ana I og
convert or
Buffer
Words from
select
selected buffer
High
byte
Low
byte
Digital-to-analog
converter
To motor speed control
I ines for internal end
external disk drives
Figure 2. Diagram of Sound Port
The sec 111-21

<!-- source-page: 31 -->
## Page 31

Inside Macintosh
The serial inputs and outputs of the SCC are connected to the ports through differential line
drivers (26LS30) and receivers (26LS32). The line drivers can be put in high-impedance mode
between transmissions, to allow other devices to transmit over those lines. A driver is activated
by lowering the SCC's Request To Send (RTS) output for that port. Port A and port B are
identical except that port A (the modem port) has a higher interrupt priority, making it more
suitable for high-speed communication.
Figure 3 shows the DB-9 pinout for the SCC output jacks.
4
3
2
• • •
9
8
7
6
• • • •
1
Ground
2
+5 volts
3
Ground
4
Transmit data +
5
Transmit data -
6
+ 12 volts
7
Handshake/external clock
8
Receive data +
9
Receive data -
Figure 3. Pinout for SCC Output Jacks
Warning: Do not draw more than 100 milliamps at +12 volts, and 200 milliamps at +5
volts from all connectors combined.
Each port's input-only handshake line (pin 7) is connected to the SCC's Clear To Send (CTS)
input for that port, and is designed to accept an external device's Data Terminal Ready (DTR)
handshake signal. This line is also connected to the SCC's external synchronous clock (TRxC)
input for that port, so that an external device can perform high-speed synchronous data exchange.
Note that you can't use the line for receiving DTR if you're using it to receive a high-speed data
clock.
The handshake line is sensed by the Macintosh using the positive (noninverting) input of one of
the standard RS422 receivers (26LS32 chip), with the negative input grounded. The positive
input was chosen because this configuration is more immune to noise when no active device is
connected to pin 7.
Note: Because this is a differential receiver, any handshake or clock signal driving it must
be "bi-polar", alternating between a positive voltage and a negative voltage, with respect to
the internally grounded negative input. If a device tries to use ground (0 volts) as one of its
handshake logic levels, the Macintosh will receive that level as an indeterminate state, with
unpredictable results.
III-24 The sec

<!-- source-page: 32 -->
## Page 32

The Macintosh Hardware
The sec itself (at its PCLK pin) is clocked at 3.672 megahertz. The internal synchronous clock
(RTxC) pins for both ports are also connected to this 3.672 MHz clock. This is the clock that,
after dividing by 16, is normally fed to the SeC's internal baud-rate generator.
The sec chip generates level-1 processor interrupts during 110 over the serial lines. For more
information about SeC interrupts, see chapter 6 of Volume II.
The locations of the SCC control and data lines are given in the following table as offsets from
the constant sccWBase for writes, or sccRBase for reads. These base addresses are also available
in the global variables SCCWr and SCCRd. The SCC is on the upper byte of the data bus, so
y0u must use only even-addressed byte reads (a byte read of an odd SCC read address tries to
reset the entire SCC). When writing, however, you must use only odd-addressed byte writes (the
MC68000 puts your data on both bytes of the bus, so it works correctly). A word access to any
sec address will shift the phase of the computer's high-frequency timing by 128 nanoseconds
(system software adjusts it correctly during the system startup process).
Location
Contents
sccWBase+aData
Write data register A
sccRBase+aData
Read data register A
sec WBase+bData
Write data register B
sccRB ase+bData
Read data register B
sec WB ase+aCtl
Write control register A
sccRB ase+aCtl
Read control register A
sccWBase+bCtl
Write control register B
sccRBase+bCtl
Read control register B
Warning: Don't access the SCC chip more often than once every 2.2 µsec. The SCC
requires that much time to let its internal lines stabilize.
Refer to the technical specifications of the Zilog Z8530 for the detailed bit maps and control
methods (baud rates, protocols, and so on) of the sec.
Diagram
Figure 4 shows a circuit diagram for the serial ports.
THE MOUSE
The DB-9 connector labeled with the mouse icon connects to the Apple mouse (Apple II,
Apple III, Lisa, and Macintosh mice are electrically identical). The mouse generates four squarewave signals that describe the amount and direction of the mouse's travel. Interrupt-driven
routines in the Macintosh ROM convert this information into the corresponding motion of the
pointer on the screen. By turning an option called mouse scaling on or off in the Control Panel
desk accessory, the user can change the amount of screen pointer motion that corresponds to a
The Mouse 111-25

<!-- source-page: 33 -->
## Page 33

Inside Macintosh
8530 (SCC)
TxDA
RTSA
TxDB
RTSB
RXDA
CTSA
TRxCA
RxDB
CTSB
TRxCB
+5v
-5V
3.672
MHz
Op,+
Op,-
Io
Oo+
OED
Oo-
Slew-rate
'k:c control3
\!E
Mode
26LS32
OA
Oc
09
Oo
6522 (VIA)
PA7
RfI f1 lter
Rf I f 1 lter
Rf I f 1 lter
-=-
Rf I f 1 lter
Rflf1lter
RfI f1 lter
Rfl fl lter
Rf I f 1 I ter
RfI f 1 lter
TXD+ ~
TXD-
+5V
-=-
>--------,
RXD-
RXD+
HSK/CLK
TXD+
TXD-
+12V
+sv
-=-
RXD-
+12V
RXD+
HSK/CLK
R1
R2
Note:~=~
I
III-26 The Mouse
R1 + R2 = 40 to 60 ohm3
C = 1 50 to 300 pf
Figure 4. Diagram of Serial Ports

<!-- source-page: 34 -->
## Page 34

The Macintosh Hardware
given mouse motion, depending on how fast the mouse is moved; for more information about
mouse scaling, see the discussion of parameter RAM in chapter 13 of Volume II.
Note: The mouse is a relative-motion device; that is, it doesn't report where it is, only
how far and in which direction it's moving. So if you want to connect graphics tablets,
touch screens, light pens, or other absolute-position devices to the mouse port, you must
either convert their coordinates into motion information or install your own device-handling
routines.
The mouse operates by sending square-wave trains of information to the Macintosh that change
as the velocity and direction of motion change. The rubber-coated steel ball in the mouse contacts
two capstans, each connected to an interrupter wheel: Motion along the mouse's X axis rotates
one of the wheels and motion along the Y axis rotates the other wheel.
The Macintosh uses a scheme known as quadrature to detect which direction the mouse is moving
along each axis. There's a row of slots on an interrupter wheel, and two beams of infrared light
shine through the slots, each one aimed at a phototransistor detector. The detectors are offset just
enough so that, as the wheel turns, they produce two square-wave signals (called the interrupt
signal and the quadrature signal) 90 degrees out of phase. The quadrature signal precedes the
interrupt signal by 90 degrees when the wheel turns one way, and trails it when the wheel turns
the other way.
The interrupt signals, Xl and Yl, are connected to the SCC's DCDA and DCDB inputs,
respectively, while the quadrature signals, X2 and Y2, go to inputs of the VIA's data register B.
When the Macintosh is interrupted (from the SCC) by the rising edge of a mouse interrupt signal,
it checks the VIA for the state of the quadrature signal for that axis: If it's low, the mouse is
moving to the left (or down), and if it's high, the mouse is moving to the right (or up). When the
sec interrupts on the falling edge, a high quadrature level indicates motion to the left (or down)
and a low quadrature level indicates motion to the right (or up):
sec
VIA
Mouse
Mouse interrupt
Mouse quadrature
Motion direction in
XI (or Yl)
X2 (or Y2)
X (or Y) axis
Positive edge
Low
Left (or down)
High
Right (or up)
Negative edge
Low
Right (or up)
High
Left (or down)
Figure 5 shows the interrupt (YI) and quadrature (Y2) signals when the mouse is moved
downwards.
The switch on the mouse is a pushbutton that grounds pin 7 on the mouse connector when
pressed. The state of the button is checked by software during each vertical blanking interrupt.
The small delay between each check is sufficient to debounce the button. You can look directly at
the mouse button's state by examining the following bit of VIA data register B (vBase+vBufB):
vSW
.EQU
3
;O = mouse button is down
If the bit is clear, the mouse button is down. However, it's recommended that you let the
Operating System handle this for you through the event mechanism.
Figure 6 shows the DB-9 pinout for the mouse jack at the back of the Macintosh.
The Mouse Ill-27

<!-- source-page: 35 -->
## Page 35

Inside Macintosh
I positive-edge interrupt
I I negative-edge interrupt
v1JlJl_JL_
I
'
I
I
Y2 ___Il_j_fl__fl_
quadrature
levels
VIA
Date
reg.B
YZ bit 5
~--------x-2-1bit 4
X1
Figure 5. Mouse Mechanism
4
3
2
• • •
9
8
7
6
• • • •
1
Ground
2
+5 volts
3
Ground
4
Mouse X2 (VIA quadrature signal)
5
Mouse X1 (SCC interrupt s i gna I)
6
(not connected)
7
Mouse switch
8
Mouse Y2 (VIA quadrature signal)
9
Mouse Y1 (SCC interrupt s i gne I)
Figure 6. Pinout for Mouse Jack
motion
interrupts
sec
y 1 DCD B
X1 DCD A
Warning: Do not draw more than 200 milliamps at +5 volts from all connectors
combined.
Diagram
Figure 7 shows a circuit diagram for the mouse port
III-28 The Mouse

<!-- source-page: 36 -->
## Page 36

6522 (VIA)
PB3 Switch
RFI Filter
PB4
X2
RFI F1 lter
RFI Filter
27
27
PBS Y2
ohms
ohms
":"
8530 (SCC)
DCDA X1
27
27
DCD9 Y1
ohms
ohms
":"
Note:
The Macintosh Hardware
X2 CI)
X1
+SV
":"
3
2
Y2
Switch
Y1
R1
R2
~
I
R1 + R2 = 40 to 60 ohms
C = 150 to 300 pf
Figure 7. Diagram of Mouse Port
THE KEYBOARD AND KEYPAD
The Macintosh keyboard and numeric keypad each contain an Intel 8021 microprocessor that
scans the keys. The 8021 contains ROM and RAM, and is programmed to conform to the
interface protocol described below.
The keyboard plugs into the Macintosh through a four-wire RJ-11 telephone-style jack. If a
numeric keypad is installed in the system, the keyboard plugs into it and it in turn plugs into the
The Keyboard and Keypad III-29

<!-- source-page: 37 -->
## Page 37

Inside Macintosh
Macintosh. Figure 8 shows the pinout for the keyboard jack on the Macintosh, on the keyboard
itself, and on the numeric keypad.
1
Ground
2
Clock
3
Data
4
+5 volts
Figure 8. Pinout for Keyboard Jack
Warning: Do not draw more than 200 milliamps at +5 volts from all connectors
combined.
Keyboard Communication Protocol
The keyboard data line is bidirectional and is driven by whatever device is sending data. The
keyboard clock line is driven by the keyboard only. All data transfers are synchronous with the
keyboard clock. Each transmission consists of eight bits, with the highest-order bits first.
When sending data to the Macintosh, the keyboard clock transmits eight 330-µsec cycles (160
µsec low, 170 µsec high) on the normally high clock line. It places the data bit on the data line 40
µsec before the falling edge of the clock line and maintains it for 330 µsec. The data bit is
clocked into the Macintosh's VIA shift register on the rising edge of the keyboard clock cycle.
When the Macintosh sends data to the keyboard, the keyboard clock transmits eight 400-µsec
cycles (180 µsec low, 220 µsec high) on the clock line. On the falling edge of the keyboard clock
cycle, the Macintosh places the data bit on the data line and holds it there for 400 µsec. The
keyboard reads the data bit 80 µsec after the rising edge of the keyboard clock cycle.
Only the Macintosh can initiate communication over the keyboard lines. On power-up of either
the Macintosh or the keyboard, the Macintosh is in charge, and the external device is passive.
The Macintosh signals that it's ready to begin communication by pulling the keyboard data line
low. Upon detecting this, the keyboard starts clocking and the Macintosh sends a command.
The last bit of the command leaves the keyboard data line low; the Macintosh then indicates it's
ready to receive the keyboard's response by setting the data line high.
The first command the Macintosh sends out is the Model Number command. The keyboard's
response to this command is to reset itself and send back its model number to the Macintosh. If
no response is received for 112 second, the Macintosh tries the Model Number command again.
Once the Macintosh has successfully received a model number from the keyboard, normal
ll/-30 The Keyboard and Keypad

<!-- source-page: 38 -->
## Page 38

The Macintosh Hardware
operation can begin. The Macintosh sends the Inquiry command; the keyboard sends back a Key
Transition response if a key has been pressed or released. If no key transition has occurred after
1/4 second, the keyboard sends back a Null response to let the Macintosh know it's still there.
The Macintosh then sends the Inquiry command again. In normal operation, the Macintosh sends
out an Inquiry command every 1/4 second. If it receives no response within 1/2 second, it
assumes the keyboard is missing or needs resetting, so it begins again with the Model Number
command.
There are two other commands the Macintosh can send: the Instant command, which gets an
instant keyboard status without the 1/4-second timeout, and the Test command, to perform a
keyboard self-test. Here's a list of the commands that can be sent from the Macintosh to the
keyboard:
Command name
Inquiry
Instant
Model Number
Test
Value
$10
$14
$16
$36
Keyboard response
Key Transition code or Null ($7B)
Key Transition code or Null ($7B)
Bit 0:
1
Bits 1-3: keyboard model number, 1-8
Bits 4-6: next device number, 1-8
Bit 7:
1 if another device connected
ACK ($7D) or NAK ($77)
The Key Transition responses are sent out by the keyboard as a single byte: Bit 7 high means a
key-up transition, and bit 7 low means a key-down. Bit 0 is always high. The Key Transition
responses for key-down transitions on the keyboard are shown (in hexadecimal) in Figure 9.
Note that these response codes are different from the key codes returned by the keyboard driver
software. The keyboard driver strips off bit 7 of the response and shifts the result one bit to the
right, removing bit 0. For example, response code $33 becomes $19, and $2B becomes $15.
Keypad Communication Protocol
When a numeric keypad is used, it must be inserted between the keyboard and the Macintosh; that
is, the keypad cable plugs into the jack on the front of the Macintosh, and the keyboard cable
plugs into a jack on the numeric keypad. In this configuration, the timings and protocol for the
clock and data lines work a little differently: The keypad acts like a keyboard when
communicating with the Macintosh, and acts like a Macintosh when communicating over the
separate clock and data lines going to the keyboard. All commands from the Macintosh are now
received by the keypad instead of the keyboard, and only the keypad can communicate directly
with the keyboard.
When the Macintosh sends out an Inquiry command, one of two things may happen, depending
on the state of the keypad. If no key transitions have occurred on the keypad since the last
Inquiry, the keypad sends an Inquiry command to the keyboard and, later, retransmits the
keyboard's response back to the Macintosh. But if a key transition has occurred on the keypad,
the keypad responds to an Inquiry by sending back the Keypad response ($79) to the Macintosh.
In that case, the Macintosh immediately sends an Instant command, and this time the keypad
sends back its own Key Transition response. As with the keyboard, bit 7 high means key-up and
bit 7 low means key-down.
The Keyboard and Keypad III-31

<!-- source-page: 39 -->
## Page 39

Inside Macintosh
' 65
Tab
61
Cops Lock
A
S
D
F
G
H
J
K
73
01 03 05 07 OB 09 4D 51
§
Shift
71
65
-+I
61
~
73
~
A
s
01
03
\
z
71
OD OF
--.::
~
75
6F
D
05
c
13
space
63
U.S. keyboard
F
G
H
J
K
07 OB 09 4D
51
v
B
N
17 SB SD
space
69
L
4B 53 4F
I
1S
-,,...-
63
Return
49
+-
67
' 49 55
71
--.::
75
International keyboard (Greet Britain key caps shown)
Clear -
BJ
IE
OF 10 OD 05
7
8
9
~
33 37 39 1B
4
5
6
l!J
2D 2F 31
11
1
2
3
Enter
27 29 2B
0
.
25
03 19
Keypad (U.S. key caps shown)
Figure 9. Key-Down Transitions
The Key Transition responses for key-down transitions on the keypad are shown in Figure 9.
Again, note that these response codes are different from the key codes returned by the keyboard
driver software. The keyboard driver strips off bit 7 of the response and shifts the result one bit
to the right, removing bit 0.
111-32 The Keyboard and Keypad

<!-- source-page: 40 -->
## Page 40

The Macintosh Hardware
THE DISK INTERFACE
The Macintosh disk interface uses a design similar to that used on the Apple II and Apple III
computers, employing the Apple custom IWM chip. Another custom chip called the Analog
Signal Generator (ASG) reads the disk speed buffer in RAM and generates voltages that control
the disk speed. Together with the VIA, the IWM and the ASG generate all the signals necessary
to read, write, format, and eject the 3 1/2-inch disks used by the Macintosh.
The IWM controls four of the disk state-control lines (called CAO, CAI, CA2, and LSTRB),
chooses which drive (internal or external) to enable, and processes the disk's read-data and writedata signals. The VIA provides another disk state-control line called SEL.
A buffer in RAM (actually the low-order bytes of words in the sound buffer) is read by the ASG
to generate a pulse-width modulated signal that's used to control the speed of the disk motor.
The Macintosh Operating System uses this speed control to allow it to store more sectors of
information in the tracks closer to the edge of the disk by running the disk motor at slower
speeds.
Figure 10 shows the DB-19 pinout for the external disk jack at the back of the Macintosh.
9
8
7
6
54 32
• • • • • • • •
19 18 17 16 15 14 13 12
11
• • • • • • • • •
1
Ground
11
CAO
2
Ground
12
CA1
3
Ground
13
CA2
4
Ground
14
LSTRB
5
-12 volts
15
Write reque3t
6
+5 volts
16
SEL
7
+ 12 volts
17
External drive enable
8
+12volts
18
Read data
9
(not connected)
19
Write data
1 O
Motor 3peed contra I
Figure 10. Pinout for Disk Jack
Warning: This connector was designed for a Macintosh 3 1/2-inch disk drive, which
represents a load of 500 milliamps at +12 volts, 500 milliamps at +5 volts, and 0 milliamps
at-12 volts. If any other device uses this connector, it must not exceed these loads by
more than 100 milliamps at +12 volts, 200 milliamps at +5 volts, and 10 milliamps at-12
volts, including loads from all other connectors combined.
The Disk Interface III-33

<!-- source-page: 41 -->
## Page 41

Inside Macintosh
Controlling the Disk State-Control Lines
The IWM contains registers that can be used by the software to control the state-control lines
leading out to the disk. By reading or writing certain memory locations, you can tum these statecontrol lines on or off. Other locations set various IWM internal states. The locations are given
in the following table as offsets from the constant dBase, the base address of the IWM; this base
address is also available in a global variable named IWM. The IWM i~ on the lower byte of the
data bus, so use odd-addressed byte accesses only.
·
Location to
Location to
IWM line
turn line on
turn line off
Disk state-control lines:
CAO
dBase+phOH
dBase+phOL
CAI
dBase+phlH
dBase+phlL
CA2
dBase+ph2H
dBase+ph2L
LSTRB
dBase+ph3H
dBase+ph3L
Disk enable line:
ENABLE
dBase+motorOn
dBase+motorOff
IWM internal states:
SELECT
dBase+extDrive
dBase+intDrive
Q6
dBase+q6H
dBase+q6L
Q7
dBase+q7H
dBase+q7L
To tum one of the lines on or off, do any kind of memory byte access (read or write) to the
respective location.
The CAO, CAl, and CA2 lines are used along with the SEL line from the VIA to select from
among the registers and data signals in the disk drive. The LSfRB line is used when writing
control information to the disk registers (as described below), and the ENABLE line enables the
selected disk drive. SELECT is an IWM internal line that chooses which disk drive can be
enabled: On selects the external drive, and off selects the internal drive. The Q6 and Q7 lines are
used to set up the internal state of the IWM for reading disk register information, as well as for
reading or writing actual disk-storage data.
You can read information from several registers in the disk drive to find out whether the disk is
locked, whether a disk is in the drive, whether the head is at track 0, how many heads the drive
has, and whether there's a drive connected at all. In tum, you can write to some of these
registers to step the head, turn the motor on or off, and eject the disk.
Reading from the Disk Registers
Before you can read from any of the disk registers, you must set up the state of the IWM so that it
can pass the data through to the MC68000's memory space where you'll be able to read it. To do
that, you must first tum off Q7 by reading or writing dBase+q7L. Then tum on Q6 by accessing
dBase+q6H. After that, the IWM will be able to pass data from the disk's RD/SENSE line
through to you.
///-34 The Disk Interface

<!-- source-page: 42 -->
## Page 42

The Macintosh Hardware
Once you've set up the IWM for disk register access, you must next select which register you
want to read. To read one of the disk registers, first enable the drive you want to use (by
accessing dBase+intDrive or dBase+extDrive and then dBase+rnotorOn) and make sure LSTRB
is low. Then set CAO, CAI, CA2, and SEL to address the register you want. Once this is done,
you can read the disk register data bit in the high-order bit of dBase+q7L. After you've read the
data, you may read another disk register by again setting the proper values in CAO, CAl, CA2,
and SEL, and then reading dBase+q7L.
Warning: When you're finished reading data from the disk registers, it's important to
leave the IWM in a state that the Disk Driver will recognize. To be sure it's in a valid logic
state, always tum Q6 back off (by accessing dBase+q6L) after you've finished reading the
disk registers.
The following table shows how you must set the disk state-control lines to read from the various
disk registers and data signals:
State-control lines
Register
CA2 CAl
CAO
SEL
addressed
Information in register
0
0
0
0
DffiTN
Head step direction
0
0
0
1
CSTIN
Disk in place
0
0
1
0
STEP
Disk head stepping
0
0
1
1
WRTPRT
Disk locked
0
1
0
0
MOfORON
Disk motor running
0
1
0
1
TKO
Head at track 0
0
1
1
1
TACH
Tachometer
1
0
0
0
RDDATAO
Read data, lower head
1
0
0
1
RDDATAl
Read data, upper head
1
1
0
0
SIDES
Single- or double-sided drive
1
1
1
1
DRVIN
Drive installed
Writing to the Disk Registers
To write to a disk register, first be sure that LSTRB is off, then tum on CAO and CAL Next, set
SEL to 0. Set CAO and CAl to the proper values from the table below, then set CA2 to the value
you want to write to the disk register. Hold LSTRB high for at least one µsec but not more than
one msec (unless you're ejecting a disk) and bring it low again. Be sure that you don't change
CAO-CA2 or SEL while LSTRB is high, and that CAO and CAl are set high before changing
SEL.
The following table shows how you must set the disk state-control lines to write to the various
disk registers:
Control lines
CAl
CAO
SEL
0
0
0
0
1
0
1
0
0
1
1
0
Register
addressed
DIRTN
STEP
MOTORON
EJECT
Register function
Set stepping direction
Step disk head one track
Tum on/off disk motor
Eject the disk
The Disk Interface /II-35

<!-- source-page: 43 -->
## Page 43

Inside Macintosh
Explanations of the Disk Registers
The information written to or read from the various disk registers can be interpreted as follows:
• The DIRTN signal sets the direction of subsequent head stepping: 0 causes steps to go
toward the inside track (track 79), 1 causes them to go toward the outside track (track 0).
• CSTIN is 0 only when a disk is in the drive.
• Setting STEP to 0 steps the head one full track in the direction last set by DIRTN. When
the step is complete (about 12 msec), the disk drive sets STEP back to 1, and then you can
step again.
• WRTPRT is 0 whenever the disk is locked. Do not write to a disk unless WRTPRT is 1.
• MOTOR ON controls the state of the disk motor: 0 turns on the motor, and 1 turns it off.
The motor will run only if the drive is enabled and a disk is in place; otherwise, writing to
this line will have no effect.
• TKO goes to 0 only if the head is at track 0. This is valid beginning 12 msec after the step
that puts it at track 0.
•Writing 1 to EJECT ejects the disk from the drive. To eject a disk, you must hold LSTRB
high for at least 1/2 second.
• The current disk speed is available as a pulse train on T ACH. The TACH line produces 60
pulses for each rotation of the drive motor. The disk motor speed is controlled by the ASG
as it reads the disk speed RAM buffer.
• RDDA TAO and RD DAT A 1 carry the instantaneous data from the disk head.
• SIDES is always 0 on single-sided drives and 1 on double-sided drives.
• DRVIN is always 0 if the selected disk drive is physically connected to the Macintosh,
otherwise it floats to 1.
THE REAL-TIME CLOCK
The Macintosh real-time clock is a custom chip whose interface lines are available through the
VIA. The clock contains a four-byte counter that's incremented once each second, as well as a
line that can be used by the VIA to generate an interrupt once each second. It also contains 20
bytes of RAM that are powered by a battery when the Macintosh is turned off. These RAM
bytes, called parameter RAM, contain important data that needs to be preserved even when the
system power is not available. The Operating System maintains a copy of parameter RAM that
you can access in low memory. To find out how to use the values in parameter RAM, see chapter
13 of Volume Il.
111-36 The Disk Interface

<!-- source-page: 44 -->
## Page 44

The Macintosh Hardware
Accessing the Clock Chip
The clock is accessed through the following bits of VIA data register B (vBase+vBufB):
rTCData
rTCClk
rTCEnb
.EQU
.EQU
.EQU
0
1
2
;real-time clock serial data line
;real-ti.me clock data-clock line
;real-time clock serial enable
These three bits constitute a simple serial interface. The rTCData bit is a bidirectional serial data
line used to send command and data bytes back and forth. The rTCClk bit is a data-clock line,
always driven by the processor (you set it high or low yourself) that regulates the transmission of
the data and command bits. The rTCEnb bit is the serial enable line, which signals the real-time
clock that the processor is about to send it serial commands and data.
To access the clock chip, you must first enable its serial function. To do this, set the serial enable
line (rTCEnb) to 0. Keep the serial enable line ~ow during the entire transaction; if you set it to 1,
you'll abort the transfer.
Warning: Be sure you don't alter any of bits 3-7 of VIA data register B during clock
serial access.
A command can be either a write request or a read request. After the eight bits of a write request,
the clock will expect the next eight bits across the serial data line to be your data for storage into
one of the internal registers of the clock. After receiving the eight bits of a read request, the clock
will respond by putting eight bits of its data on the serial data line. Commands and data are
transferred serially in eight-bit groups over the serial data line, with the high-order bit first and the
low-order bit last.
To send a command to the clock, first set the rTCData bit of VIA data direction register B
(vBase+vDirB) so that the real-time clock's serial data line will be used for output to the clock.
Next, set the rTCClk bit of vBase+vBufB to 0, then set the rTCData bit to the value of the first
(high-order) bit of your data byte. Then raise (set to 1) the data-clock bit (rTCClk). Then lower
the data-clock, set the serial data line to the next bit, and raise the data-clock line again. After the
last bit of your command has been sent in this way, you can either continue by sending your data
byte in the same way (if your command was a write request) or switch to receiving a data byte
from the clock (if your command was a read request).
To receive a byte of data from the clock, you must first send a command that's a read request.
After you've clocked out the last bit of the command, clear the rTCData bit of the data direction
register so that the real-time clock's serial data line can be used for input from the clock; then
lower the data-clock bit (rTCClk) and read the first (high-order) bit of the clock's data byte on the
serial data line. Then raise the data-clock, lower it again, and read the next bit of data. Continue
this until all eight bits are read, then raise the serial enable line (rTCEnb }, disabling the data
transfer.
The following table lists the commands you can send to the clock. A 1 in the high-order bit
makes your command a read request; a 0 in the high-order bit makes your command a write
request. (In this table, "z" is the bit that determines read or write status, and bits marked "a" are
bits whose values depend on what parameter RAM byte you want to address.)
The Real-Time Clock lll-37

<!-- source-page: 45 -->
## Page 45

Inside Macintosh
Command byte
zOOOOOOl
z0000101
z0001001
zOOOl 101
00110001
00110101
z010aa01
zlaaaaOl
Register addressed by the command
Seconds register 0 (lowest-order byte)
Seconds register 1
Seconds register 2
Seconds register 3 (highest-order byte)
Test register (write only)
Write-protect register (write only)
RAM address 1 OOaa ($10-$13)
RAM address Oaaaa ($00-$0F)
Note that the last two bits of a command byte must always be 01.
If the high-order bit (bit 7) of the write-protect register is set, this prevents writing into any other
register on the clock chip (including parameter RAM). Clearing the bit allows you to change any
values in any registers on the chip. Don't try to read from this register; it's a write-only register.
The two highest-order bits (bits 7 and 6) of the test register are used as device control bits during
testing, and should always be set to 0 during normal operation. Setting them to anything else will
interfere with normal clock counting. Like the write-protect register, this is a write-only register;
don't try to read from it.
All clock data must be sent as full eight-bit bytes, even if only one or two bits are of interest. The
rest of the bits may not matter, but you must send them to the clock or the write will be aborted
when you raise the serial enable line.
It's important to use the proper sequence if you're writing to the clock's seconds registers. If you
write to a given seconds register, there's a chance that the clock may increment the data in the
next higher-order register during the write, causing unpredictable results. To avoid this
possibility, always write to the registers in low-to-high order. Similarly, the clock data may
increment during a read of all four time bytes, which could cause invalid data to be read. To
avoid this, always read the time twice (or until you get the same value twice).
Warning: When you've finished reading from the clock registers, always end by doing a
final write such as setting the write-protect bit. Failure to do this may leave the clock in a
state that will run down the battery more quickly than necessary.
The One-Second Interrupt
The clock also generates a VIA interrupt once each second (if this interrupt is enabled). The
enable status for this interrupt can be read from or written to bit 0 of the VlA's interrupt enable
register (vBase+vIER). When reading the enable register, a 1 bit indicates the interrupt is
enabled, and 0 means it's disabled. Writing $01 to the enable register disables the clock's onesecond interrupt (without affecting any other interrupts), while writing $81 enables it again. See
chapter 6 of Volume Il for more information about writing your own interrupt handlers.
Warning: Be sure when you write to bit 0 of the VIA's interrupt enable register that you
don't change any of the other bits.
111-38 The Real-Time Clock

<!-- source-page: 46 -->
## Page 46

The Macintosh Hardware
THE VIA
The Synertek SY6522 Versatile Interface Adapter (VIA) controls the keyboard, internal realtime clock, parts of the disk, sound, and mouse interfaces, and various internal Macintosh
signals. Its base address is available as the constant vBase and is also stored in a global variable
named VIA. The VIA is on the upper byte of the data bus, so use even-addressed byte accesses
only.
There are two parallel data registers within the VIA, called A and B, each with a data direction
register. There are also several event timers, a clocked shift register, and an interrupt flag register
with an interrupt enable register.
Normally you won't have to touch the direction registers, since the Operating System sets them
up for you at system startup. A 1 bit in a data direction register means the corresponding bit of
the respective data register will be used for output, while a 0 bit means it will be used for input.
Note: For more information on the registers and control structure of the VIA, consult the
technical specifications for the SY6522 chip.
VIA Register A
VIA data register A is at vBase+vBufA. The corresponding data direction register is at
vBase+vDirA.
Bit(s)
Name
Description
7
vSCCWReq
sec wait/request
6
vPage2
Alternate screen buffer
5
vHeadSel
Disk SEL line
4
vOverlay
ROM low-memory overlay
3
vSndPg2
Alternate sound buffer
0-2
vSound (mask)
Sound volume
The vSCCWReq bit can signal that the SCC has received a character (used to maintain serial
communications during disk accesses, when the CPU's interrupts from the SCC are disabled).
The vPage2 bit controls which screen buffer is being displayed, and the vHeadSel bit is the SEL
control line used by the disk interface. The vOverlay bit (used only during system startup) can be
used to place another image of ROM at the bottom of memory, where RAM usually is (RAM
moves to $600000). The sound buffer is selected by the vSndPg2 bit. Finally, the vSound bits
control the sound volume.
VIA Register B
VIA data register Bis at vBase+vBufB. The corresponding data direction register is at
vBase+vDirB.
The VIA III-39

<!-- source-page: 47 -->
## Page 47

Inside Macintosh
Bit
Name
Description
7
vSndEnb
Sound enable/disable
6
vH4
Horizontal blanking
5
vY2
MouseY2
4
vX2
MouseX2
3
vSW
Mouse switch
2
trCEnb
Real-time clock serial enable
1
trCClk
Real-time clock data-clock line
0
trCData
Real-time clock serial data
The vSndEnb bit turns the sound generator on or off, and the vH4 bit is set when the video beam
is in its horizontal blanking period. The vY2 and vX2 bits read the quadrature signals from the Y
(vertical) and X (horizontal) directions, respectively, of the mouse's motion lines. The vSW bit
reads the mouse switch. The trCEnb, trCClk, and trCData bits control and read the real-time
clock.
The VIA Peripheral Control Register
The VIA's peripheral control register, at vBase+vPCR, allows you to set some very low-level
parameters (such as positive-edge or negative-edge triggering) dealing with the keyboard data and
clock intenupts, the one-second real-time clock intenupt line, and the vertical blanking intenupt.
Bit(s)
5-7
4
1-3
0
Description
Keyboard data interrupt control
Keyboard clock interrupt control
One-second interrupt control
Vertical blanking interrupt control
The VIA Timers
The timers controlled by the VIA are called timer 1 and timer 2. Timer 1 is used to time various
events having to do with the Macintosh sound generator. Timer 2 is used by the Disk Driver to
time disk 1/0 events. If either timer isn't being used by the Operating System, you're free to use
it for your own purposes. When a timer counts down to 0, an intenupt will be generated if the
proper intenupt enable has been set. See chapter 6 of Volume II for information about writing
your own interrupt handlers.
To start one of the timers, store the appropriate values in the high- and low-order bytes of the
timer counter (or the timer 1 latches, for multiple use of the value). The counters and latches are
at the following locations:
III-40 The VIA

<!-- source-page: 48 -->
## Page 48

Location
vBase+vTlC
vBase+vTlCH
vBase+vTlL
vBase+vTlLH
vBase+vT2C
vBase+vT2CH
The Macintosh Hardware
Contents
Timer 1 counter (low-order byte)
Timer 1 counter (high-order byte)
Timer 1 latch (low-order byte)
Timer 1 latch (high-order byte)
Timer 2 counter (low-order byte)
Timer 2 counter (high-order byte)
Note: When setting a timer, it's not enough to simply store a full word to the high-order
address, because the high- and low-order bytes of the counters are not adjacent. You must
explicitly do two stores, one for the high-order byte and one for the low-order byte.
VIA Interrupts
The VIA (through its IRQ line) can cause a level-0 processor interrupt whenever one of the
following occurs: Timer 1 or timer 2 times out; the keyboard is clocking a bit in through its serial
port; the shift register for the keyboard serial interface has finished shifting in or out; the vertical
blanking interval is beginning; or the one-second clock has ticked. For more information on how
to use these interrupts, see chapter 6 of Volume II.
The interrupt flag register at vBase+vIFR contains flag bits that are set whenever the interrupt
corresponding to that bit has occurred. The Operating System uses these flags to determine
which device has caused an interrupt Bit 7 of the interrupt flag register is not really a flag: It
remains set (and the IRQ line to the processor is held low) as long as any enabled VIA interrupt is
occurring.
Bit
Interrupting device
7
IRQ (all enabled VIA interrupts)
6
Timer 1
5
Timer2
4
Keyboard clock
3
Keyboard data bit
2
Keyboard data ready
1
Vertical blanking interrupt
0
One-second interrupt
The interrupt enable register, at vBase+vIER, lets you enable or disable any of these interrupts.
If an interrupt is disabled, its bit in the interrupt flag register will continue to be set whenever that
interrupt occurs, but it won't affect the IRQ flag, nor will it interrupt the processor.
The bits in the interrupt enable register are arranged just like those in the interrupt flag register,
except for bit 7. When you write to the interrupt enable register, bit 7 is "enable/disable": If bit 7
is a 1, each 1 in bits 0-6 enables the corresponding interrupt; if bit 7 is a 0, each 1 in bits 0-6
disables that interrupt In either case, O's in bits 0-6 do not change the status of those interrupts.
Bit 7 is always read as a 1.
The VIA /II-41

<!-- source-page: 49 -->
## Page 49

Inside Macintosh
Other VIA Registers
The shift register, at vBase+vSR, contains the eight bits of data that have been shifted in or that
will be shifted out over the keyboard data line.
The auxiliary control register, at vBase+vACR, is described in the SY6522 documentation. It
controls various parameters having to do with the timers and the shift register.
SYSTEM STARTUP
When power is first supplied to the Macintosh, a carefully orchestrated sequence of events takes
place.
First, the processor is held in a wait state while a series of circuits gets the system ready for
operation. The VIA and IWM are initialized, and the mapping of ROM and RAM are altered
temporarily by setting the overlay bit in VIA data register A. This places the ROM starting at the
normal ROM location $400000, and a duplicate image of the same ROM starting at address 0
(where RAM normally is), while RAM is placed starting at $600000. Under this mapping, the
Macintosh software executes out of the normal ROM locations above $400000, but the MC68000
can obtain some critical low-memory vectors from the ROM image it finds at address 0.
Next, a memory test and several other system tests take place. After the system is fully tested and
initialized, the software clears the VIA's overlay bit, mapping the system RAM back where it
belongs, starting at address 0. Then the disk startup process begins.
First the internal disk is checked: If there's a disk inserted, the system attempts to read it. If no
disk is in the internal drive and there's an external drive with an inserted disk, the system will try
to read that one. Otherwise, the question-mark disk icon is displayed until a disk is inserted. If
the disk startup fails for some reason, the "sad Macintosh" icon is displayed and the Macintosh
goes into an endless loop until it's turned off again.
Once a readable disk has been inserted, the first two sectors (containing the system starrup
blocks) are read in and the normal disk load begins.
III-42 The VIA

<!-- source-page: 50 -->
## Page 50

The Macintosh Hardware
SUMMARY
Warning: This information applies only to the Macintosh 128K and 512K, not to the
Macintosh XL.
Constants
; VIA base addresses
vBase
.EQU
$EFE1FE
aVBufB
.EQU
vBase
aVBufA
.EQU
$EFFFFE
aVBufM
.EQU
aVBufB
aVIFR
.EQU
$EFFBFE
a VIER
.EQU
$EFFDFE
; Offsets from vBase
vBufB
.EQU
512*0
vDirB
.EQU
512*2
vDirA
.EQU
512*3
vTlC
.EQU
512*4
vTlCH
.EQU
512*5
vTlL
.EQU
512*6
vTlLH
.EQU
512*7
vT2C
.EQU
512*8
vT2CH
.EQU
512*9
vSR
.EQU
512*10
vACR
.EQU
512*11
vPCR
.EQU
512*12
vIFR
.EQU
512*13
vIER
.EQU
512*14
vBufA
.EQU
512*15
; VIA register A constants
vAOut
vAinit
vSound
.EQU
.EQU
.EQU
$7F
$7B
7
; VIA register A bit numbers
vSndPg2
vOverlay
vHeadSel
vPage2
vSCCWReq
.EQU
.EQU
.EQU
.EQU
.EQU
3
4
5
6
7
;main base for VIA chip (in variable VIA)
;register B base
;register A base
;register containing mouse signals
;interrupt flag register
;interrupt enabl e register
;register B (zero offset)
;register B direction register
;register A direction register
;timer 1 counter (low- order byte)
;timer 1 counter (high- order byte)
;timer 1 lat ch (low- order byte)
;timer 1 latch (high- order byte)
;timer 2 counter (l ow-order byte)
;timer 2 counter (high-order byte)
;shift register (keyboard)
;auxiliary control register
;peripheral control register
;interrupt flag register
;interrupt enable register
; regi ster A
;direction register A:
1 bits = outputs
;initial value for vBufA (medium volume)
;sound volume bits
;O = alternate sound buffer
;l = ROM overlay (system startup only)
;disk SEL control line
;O = alternate screen buffer
;SCC wait/request line
Summary 11/43

<!-- source-page: 51 -->
## Page 51

Inside Macintosh
; VIA register B
vBOut
.EQU
vBinit
.EQU
::onstants
$87
$07
;direction register B:
1 bits
;initial value for vBufB
outputs
; VIA register B bit numbers
rTCData
.EQU
0
rTCClk
.EQU
1
rTCEnb
.EQU
2
vsw
.EQU
3
vX2
.EQU
4
vY2
.EQU
5
vH4
.EQU
6
vSndEnb
.EQU
7
; sec base addresses
sccRBase
sccWBase
.EQU
.EQU
$9FFFF8
$BFFFF9
;real- time clock ser ial data line
;real- time clock data- clock l ine
;real- time clock serial enable
;0 = mouse button is down
;mouse X quadrature level
;mouse Y quadrature level
;l
horizontal blanking
;0 = sound enabled, 1 = disabled
;SCC base read address (in variable SCCRd)
;SCC base write address (in variable SCCWr)
; Offsets from SCC base addresses
aData
aCtl
bData
bCtl
; Bit
rxBF
txBE
.EQU
.EQU
.EQU
.EQU
numbers for
.EQU
.EQU
; IWM base address
dBase
.EQU
6
2
4
0
control
0
2
$DFE1FF
; Offsets from dBase
phOL
.EQU
512*0
phOH
.EQU
512*1
phlL
.EQU
512*2
phl H
.EQU
512*3
ph2L
.EQU
512*4
ph2H
.EQU
512*5
ph3L
.EQU
512*6
ph3H
.EQU
512*7
mtrOff
.EQU
512*8
mtrOn
.EQU
512*9
intDrive
.EQU
512*10
extorive
.EQU
512*11
q6L
.EQU
512*12
III-44 Summary
;channel A data in or out
;channel A control
;channel B data in or out
;channel B control
register RRO
;1
; 1
sec receive buffer full
sec send buffer empty
;IWM base address (in variable IWM)
;CAO off (0)
;CAO on (1)
;CAl off (0)
;CAl on (1)
;CA2 off (0)
;CA2 on (1)
;LSTRB off (low)
;LSTRB on (high)
;disk enable off
;disk enable on
;select internal drive
;select external drive
;Q6 off

<!-- source-page: 52 -->
## Page 52

q6H
q7L
q7H
. EQU
.EQU
.EQU
512*13
512*14
512*15
;Q6 on
;Q7 off
;Q7 on
The Macintosh Hardware
Screen and sound addresses for 512K Macintosh (will also work for
128K, since addresses wrap)
screenLow
soundLow
pwmBuffer
ovlyRAM
ovlyScreen
romStart
Variables
ROMBase
SoundBase
SCCRd
SCCWr
IWM
VIA
.EQU
$7A700
;top left corner of main screen buffer
.EQU
$7FDOO
;main sound buffer (in variable SoundBase)
.EQU
$7FD01
;main disk speed buffer
.EQU
$600000
;RAM start address when overlay
.EQU
$67A700
;screen start with overlay set
.EQU
$400000
;ROM start address
Base address of ROM
Address of main sound buffer
sec read base address
sec write base address
IWM base address
VIA base address
(in variable
is set
ROMBase)
Exception Vectors
Location
$00
$04
$08
$0C
$10
$14
$18
$1C
$20
$24
$28
$2C
$30-$3B
$3C
$40-$5F
Purpose
Reset: initial stack pointer (not a vector)
Reset: initial vector
Bus error
Address error
Illegal instruction
Divide by zero
CHK instruction
TRAPV instruction
Privilege violation
Trace interrupt
Line 1010 emulator
Line 1111 emulator
Unassigned (reserved)
Uninitialized interrupt
Unassigned (reserved)
Swnmary III-45

<!-- source-page: 53 -->
## Page 53

Inside Macintosh
Location
$60
$64
$68
$6C
$70
$74
$q8
$7C
$80-$BF
$CO-$FF
1//-46 Summary
Purpose
Spurious interrupt
VIA interrupt
sec interrupt
VIA+SCC vector (temporary)
Interrupt switch
Interrupt switch + VIA
Interrupt switch + SCC
Interrupt switch + VIA + SCC
TRAP instructions
Unassigned (reserved)

<!-- source-page: 54 -->
## Page 54

3 SUMMARY
49
About This Chapter
50
AppleTalk Manager
65
Binary-Decimal Conversion Package
66
Control Manager
71
Desk Manager
73
Device Manager
80
Dialog Manager
85
Disk Driver
88
Disk Initialization Package
90
Event Manager, Operating System
94
Event Manager, Toolbox
98
File Manager
113
Font Manager
118
International Utilities Package
124
Memory Manager
130
Menu Manager
134
Package Manager
135
Printing Manager
141
QuickDraw
154
Resource Manager
157
Scrap Manager
159
Segment Loader
161
Serial Drivers
165
Sound Driver
172
Standard File Package
176
System Error Handler
179
TextEdit
184
Utilities, Operating System
190
Utilities, Toolbox
193
Vertical Retrace Manager
195
Window Manager
201
Assembly Language
201
Miscellaneous Variables
201
Hardware
Contents JJJ-47

<!-- source-page: 55 -->
## Page 55

Inside Macintosh
III-48

<!-- source-page: 56 -->
## Page 56

Summary
ABOUT THIS CHAPTER
This chapter includes all the summaries that appear at the end of other chapters of Inside
Macintosh. The summaries are arranged in alphabetical order of the pan of the Toolbox or
Operating System being summarized.
Note: The summaries of the Event Managers are listed under "Event Manager, Operating
System" and "Event Manager, Toolbox". The Toolbox and Operating System Utilities are
listed similarly.
The last section of this chapter, "Assembly Language", contains information for assemblylanguage programmers only. It lists some miscellaneous global variables along with hardwarerelated definitions for the Macintosh 128K and 512K.
About This Chapter III-49

<!-- source-page: 57 -->
## Page 57

Inside Macintosh
APPLETALK MANAGER
Constants
CONST lapSize
20;
{ABusRecord size for ALAP}
ddpSize
26;
{ABusRecord size for DDP}
nbpSize
26;
{ABusRecord size for NBP}
atpSize
56;
{ABusRecord size for ATP}
Data Types
TYPE ABProtoType
(lapProto,ddpProto,nbpProto,atpProto);
ABRecHandle
ABRecPtr
ABusRecord
"ABRecPtr;
"ABusRecord;
RECORD
abOpcode:
abResult:
abUserReference:
ABCallType;
INTEGER;
LONGINT;
{type of call}
{result code }
{for your use}
CASE ABProtoType OF
lapProto:
(lapAddress:
lapReqCount:
LAPAdrBlock;
INTEGER;
{destination or source node ID}
{length of frame data or buffer
{ size in bytes }
lapActCount
INTEGER;
{number of frame dat a bytes }
{ actually received}
lapDataPtr :
Ptr);
{pointer to frame data or pointer
{ to buffer}
ddpProto :
(ddpType:
ddpSocket:
ddpAddress:
ddpReqCount:
ddpActCount:
ddpDataPtr :
ddpNodeID:
nbpProto:
(nbpEntityPtr:
nbpBufPtr:
nbpBufSize :
nbpDataField:
Byte;
Byte;
AddrBlock;
INTEGER;
INTEGER;
Ptr;
Byte) ;
{DDP protocol type}
{source or listening socket number}
{destination or source socket address }
{length of datagram data or buffer }
{ size in bytes}
{number of bytes actually received}
{pointer to buffer}
{original destination node ID}
EntityPtr;
Ptr;
INTEGER;
INTEGER;
{poi nter to entity name }
{pointer to buffer}
{buf fer size i n bytes }
{number of addresses or
{ socket number}
nbpAddress :
AddrBlock;
{socket address}
nbpRetransmitinfo: RetransType); {retransmission information }
III-50 AppleTalk Manager

<!-- source-page: 58 -->
## Page 58

Summary
atpProto:
END;
(atpSocket:
atpAddress:
atpReqCount:
atpDataPtr
atpRspBDSPtr:
atpBitMap:
atpTransID:
atpActCount:
atpUserData :
atpXO:
atpEOM:
atpTimeOut:
atpRetries:
atpNuroBufs :
atpNumRsp:
atpBDSSize:
atpRspUData:
atpRspBuf:
atpRspSize:
Byte;
AddrBlock;
INTEGER;
Ptr;
BDSPtr;
BitMapType;
INTEGER;
INTEGER;
LONGINT;
BOOLEAN;
BOOLF-AN;
Byte;
Byte;
Byte;
Byte;
Byte;
LONGINT;
Ptr;
INTEGER);
{listening or responding socket
{ number}
{destination or source socket
{ address}
{request size or buffer size}
{pointer to buffer}
{pointer to response BDS)
{transaction bit map}
{transaction ID)
{number of bytes actually received}
{user bytes }
{exactly-once f lag}
{end-of-message flag}
{retry timeout interval i n seconds}
{maximum number of retries}
{number of elements in response
{ BDS or number of response }
{ packets sent}
{number of response packets
{ received or sequence number }
{number of elements in response BDS}
{user bytes sent or received in }
{ transaction response)
{pointer to response message buffer}
{size of response message buffer}
ABCallType
(tLAPRead,tLAPWrite,tDDPRead,tDDPWrite, tNBPLookup,
tNBPConfirm, tNBPRegister,tATPSndRequest,
tATPGetRequest,tATPSdRsp, tATPAddRsp, t ATPRequest,
tATPResponse);
LAPAdrBlock
PACKED RECORD
dstNodeID:
srcNodeID:
lapProtType:
END;
Byte;
Byte;
ABByte
{destination node ID}
{source node ID}
{ALAP protocol t ype }
ABByte = 1 .. 127; {ALAP protocol type}
AddrBlock = PACKED RECORD
aNet:
aNode :
aSocket :
END;
"BDSType;
INTEGER;
Byte;
Byte
{network number}
{node ID}
{socket number }
BDSPtr
BDSType
ARRAY[0 .. 7] OF BDSElement; {response BDS }
AppleTalkManager JJJ-51

<!-- source-page: 59 -->
## Page 59

Inside Macintosh
BDSElement
RECORD
buffSize:
INTEGER;
buffPtr:
Ptr;
dataSize:
INTEGER;
userBytes: LONGINT
END;
{buffer size in bytes}
{pointer to buffer}
{number of bytes actually received}
{user bytes}
BitMapType
PACKED ARRAY [0 . . 7] OF BOOLEAN;
EntityPtr
EntityName
"EntityNarne;
RECORD
objStr:
Str32;
typeStr:
Str32;
zoneStr:
Str32
END;
Str32 = STRING[32];
RetransType =
{object}
{type}
{zone}
PACKED RECORD
retransinterval: Byte;
retransCount :
Byte
{retransmit interval in 8-tick units }
{total number of attempts }
END;
Routines [Not in ROM]
Opening and Closing AppleTalk
FUNCTION MPPOpen :
OSErr;
FUNCTION MPPClose : OSErr;
AppleTalk Link Access Protocol
FUNCTION LAPOpenProtocol
(theLAPType: ABByte; protoPtr: Ptr) : OSErr;
FUNCTION LAPCloseProtocol (theLAPType: ABByte) : OSErr;
FUNCTION LAPWrite (abRecord: ABRecHandle; async : BOOLEAN) : OSErr;
f-
abOpcode
{always tLAPWrite}
f-
abResult
{result code}
~
abUserReference
{for your use}
~
lapAddress.dstNodeID
{destination node ID}
~
lapAddress.lapProtType
{ ALAP protocol type}
~
lapReqCount
{length of frame data}
~
lapDataPtr
{pointer to frame data}
III-52 AppleTalk Manager

<!-- source-page: 60 -->
## Page 60

FUNCTION LAPRead (abRecord:
f-
abOpcode
f-
abResult
---7
abUserReference
f-
lapAddress.dstNodeID
f-
IapAddress.srcNodeID
---7
lapAddress.lapProtType
---7
lapReqCount
f-
lapActCount
---7
lapDataPtr
ABRecHandle; async: BOOLEAN)
OSErr;
{always tLAPRead}
{result code}
{for your use}
{destination node ID}
{source node ID}
{ ALAP protocol type}
{buffer size in bytes}
{number of frame data bytes actually received}
{pointer to buffer}
FUNCTION LAPRdCancel (abRecord: ABRecHandle)
OSErr;
Datagram Delivery Protocol
Summary
FUNCTION DDPOpenSocket
(VAR theSocket: Byte; sktListener: Ptr) : OSErr;
FUNCTION DDPCloseSocket (theSocket: Byte) : OSErr;
FUNCTION DDPWrite (abRecord: ABRecHandle; doChecksurn: BOOLEAN; async:
f-
f-
---7
---7
---7
---7
---7
---7
BOOLEAN) : OSErr;
ab Opcode
{always tDDPWrite}
abResult
{result code}
abU serReference
{for your use}
ddpType
ddpSocket
ddpAddress
ddpReqCount
ddpDataPtr
{DDP protocol type}
{source socket number}
{destination socket address}
{length of datagram data}
{pointer to buffer}
FUNCTION DDPRead (abRecord: ABRecHandle; retCksumErrs: BOOLEAN; async:
BOOLEAN) : OSErr;
f-
ab Opcode
f-
abResult
---7
abUserReference
f-
ddpType
---7
ddpSocket
f-
ddpAddress
---7
ddpReqCount
f-
ddpActCount
---7
ddpDataPtr
f-
ddpNodelD
{always tDDPRead}
{result code}
{for your use}
{DDP protocol type}
{listening socket number}
{source socket address}
{buffer size in bytes}
{number of bytes actually received}
{pointer to buffer}
{original destination node ID}
FUNCTION DDPRdCancel (abRecord: ABRecHandle) : OSErr;
AppleTalk Transaction Protocol
FUNCTION ATPLoad :
FUNCTION ATPUnload
FUNCTION ATPOpenSocket
FUNCTION ATPCloseSocket
OSErr;
OSErr;
(addrRcvd: AddrBlock; VAR atpSocket: Byte)
(atpSocket: Byte) : OSErr;
OSErr;
AppleTalk Manager JJ/-53

<!-- source-page: 61 -->
## Page 61

Inside Macintosh
FUNCTION ATPSndRequest (abRecord: ABRecHandle; async: BOOLEAN)
OSErr;
f-
abOpcode
{always tA1PSndRequest}
f-
abResult
{result code}
-7
abUserReference
{for your use}
-7
atpAddress
{destination socket address}
-7
atpReqCount
{request size in bytes}
-7
atpDataPtr
{pointer to buffer}
-7
atpRspBDSPtr
{pointer to response BDS}
-7
atpUserData
{user bytes}
-7
atpXO
{exactly-once flag}
f-
atpEOM
{end-of-message flag}
-7
atpTureOut
{retry timeout interval in seconds}
-7
atpRetries
{maximum number of retries}
-7
atpNumBufs
{number of elements in response BDS}
f-
atpNumRsp
{number of response packets actually received}
FUNCTION ATPRequest (abRecord: ABRecHandle; async: BOOLEAN)
: OSErr;
f-
abOpcode
{always tA1PRequest}
f-
abResult
{result code}
-7
abUserReference
{for your use}
-7
atpAddress
{destination socket address}
-7
atpReqCount
{request size in bytes}
-7
atpDataPtr
{pointer to buffer}
f-
atpActCount
{number of bytes actually received}
-7
atpUserData
{user bytes}
-7
atpXO
{exactly-once flag}
f-
atpEOM
{end-of-message flag}
-7
atpTmteOut
{retry timeout interval in seconds}
-7
atpRetries
{maximum number of retries}
f-
atpRspUData
{user bytes received in transaction response}
-7
atpRspBuf
{pointer to response message buffer}
-7
atpRspSize
{size of response message buffer}
FUNCTION ATPReqCancel (abRecord: ABRecHandle; as ync: BOOLEAN) : OSErr;
FUNCTION ATPGetRequest
f-
abOpcode
f-
abResult
-7
abUserReference
-7
atpSocket
f-
atpAddress
-7
atpReqCount
-7
atpDataPtr
f-
atpBitMap
f-
atpTransID
f-
atpActCount
f-
atpUserData
f-
atpXO
111-54 App/eTa/k Manager
(abRecord: ABRecHandle; async: BOOLEAN) : OSErr;
{always tATPGetRequest}
{result code}
{for your use}
{listening socket number}
{source socket address}
{buffer size in bytes}
{pointer to buffer}
{transaction bit map}
{transaction ID}
{number of bytes actually received}
{user bytes}
{exactly-once flag}

<!-- source-page: 62 -->
## Page 62

FUNCTION ATPSnd.Rsp (abRecord: ABRecHandle; async: BOOLEAN)
t-
abOpcode
{always tA1PSdRsp}
t-
abResult
{result code}
~
abUserReference
{for your use}
~
atpSocket
{responding socket number}
~
atpAddress
{destination socket address}
~
alpRspBDSPtr
{pointer to response BDS}
~
atpTransID
{transaction ID}
~
atpEOM
{end-of-message flag}
~
atpNumBufs
{number of response packets being sent}
~
atpBDSSize
{numberof elements in response BDS}
FUNCTION ATPAddRsp
t-
abOpcode
t-
abResult
(abRecord: ABRecHandle) : OSErr;
{always tA1PAddRsp}
~
abUserReference
~
atpSocket
~
atpAddress
~ atpReqCount
~
atpDataPtr
~
atpTransID
~
atpUserData
~
atpEOM
~
atpNumRsp
FUNCTION ATPResponse
t-
abOpcode
t-
ab Result
~
abU serReference
~ a1pSocket
~ atpAddress
~ atpTransID
{result code}
{for your use}
{responding socket number}
{destination socket address}
{buffer size in bytes}
{pointer to buffer}
{transaction ID}
{user bytes}
{end-of-message flag}
{sequence number}
(abRecord: ABRecHandle; async:
{always tA1PResponse}
{result code}
{for your use}
{responding socket number}
{destination socket address}
{transaction ID)
BOOLEAN)
~
atpRspUData
{user bytes sent in transaction response}
~
atpRspBuf
{pointer to response message buffer}
~
atpRspSize
{size of response message buffer}
FUNCTION ATPRspCancel (abRecord: ABRecHandle; async: BOOLEAN)
Name-Binding Protocol
FUNCTION NBPRegister (abRecord: ABRecHandle; async: BOOLEAN)
t-
abOpcode
{always tNBPRegister}
t-
abResult
{result code}
~
abUserReference
{for your use}
~ nbpEntityPtr
{pointer to entity name}
~ nbpBufPtr
{pointer to buffer}
~ nbpBufSize
{buffer size in bytes}
~ nbpAddress.aSocket
{socket address}
~ nbpRetransmitinfo
{retransmission information}
Summa.ry
OSErr;
OSErr;
OSErr;
OSErr;
AppleTalk Manager JJI-55

<!-- source-page: 63 -->
## Page 63

Inside Macintosh
FUNCTION NBPLookup (abRecord: ABRecHandle; async: BOOLEAN)
OSErr;
~
abOpcode
{always tNBPLook:up}
~
abResult
{result code}
~
abUserReference
{for your use}
~
nbpEntityPtr
{pointer to entity name}
~ nbpButPtr
{pointer to buffer}
~
nbpButSiz.e
{buffer size in bytes}
H
nbpDataField
{number of addresses received}
~ nbpRetransmitlnf o
{retransmission infonnation}
FUNCTION NBPExtract (theBuffer: Ptr; numinBuf: INTEGER; whichOne:
INTEGER; VAR abEntity: EntityName; VAR address:
AddrBlock) : OSErr;
FUNCTION NBPConfirm (abRecord: ABRecHandle; async: BOOLEAN) : OSErr;
~
abOpcode
{always tNBPConfirm}
~ abResult
{result code}
~
abUserReference
{for your use}
~ nbpEntityPtr
{pointer to entity name}
~
nbpDataField
{socketnumber}
~ nbpAddress
{socket address}
~ nbpRetransmitlnfo
{retransmission infonnation}
FUNCTION NBPRemove
(abEntity: EntityPtr) : OSErr;
FUNCTION NBPLoad :
OSErr;
FUNCTION NBPUnload : OSErr;
Miscellaneous Routines
FUNCTION GetNodeAddress (VAR myNode,myNet: INTEGER)
FUNCTION IsMPPOpen
BOOLEAN;
FUNCTION IsATPOpen
BOOLEAN;
Result Codes
Name
Value
atpBadRsp
-3107
atpLenErr
-3106
badATPSkt
-1099
badBuffNum
-1100
buf2Smal1Err
-3101
cbNotFound
- 1102
cksumErr
-3103
Meaning
Bad response from A TPRequest
ATP response message too large
ATP bad responding socket
ATP bad sequence number
ALAP frame too large for buffer
DDP datagram too large for buffer
ATP control block not found
DDP bad checksum
OSErr;
ddpLenErr
-92
DDP datagram or ALAP data length too big
111-56 AppleTalk Manager

<!-- source-page: 64 -->
## Page 64

Name
Value
ddpSktErr
-91
excessCollsns
-95
extractErr
-3104
lapProtErr
-94
nbpBuffOvr
-1024
nbpConfDiff
-1026
nbpDuplicate
-1027
nbpNISErr
- 1029
nbpNoConfirm
-1025
nbpNotFound
-1028
noBridgeErr
-93
noDataArea
-1104
no Err
0
noMPPError
- 3102
noRelErr
- 1101
noSendResp
- 1103
portlnUse
- 97
portNotCf
-98
readQErr
- 3105
recNotFnd
-3108
reqAborted
- 1105
reqFailed
-1096
sktClosedErr
-3109
tooManyReqs
- 1097
tooManySkts
- 1098
Summary
Meaning
DDP socket error: socket already active; not a well-known socket;
socket table full; all dynamic socket numbers in use
ALAP no CTS received after 32 RTS's, or line sensed in use 32
times (not necessarily caused by collisions)
NBP can't find tuple in buffer
ALAP error attaching/detaching ALAP protocol type: attach error
when ALAP protocol type is negative, not in range, already in table,
or when table is full; detach error when ALAP protocol type isn't in
table
NBP buffer overflow
NBP name confirmed for different socket
NBP duplicate name already exists
NBP names information socket error
NBP name not confirmed
NBP name not found
No bridge found
Too many outstanding ATP calls
No error
MPP driver not installed
ATP no release received
ATP AddRsp issued before ATPSndRsp
Driver Open error, port already in use
Driver Open error, port not configured for this connection
Socket or protocol type invalid or not found in table
ABRecord not found
Request aborted
ATPSndRequest failed: retry count exceeded
Asynchronous call aborted because socket was closed before call
was completed
ATP too many concurrent requests
ATP too many responding sockets
AppleTalk Manager 111-57

<!-- source-page: 65 -->
## Page 65

Inside Macintosh
Assembly-Language Information
Constants
; Serial port use types
useFree
useATalk
useASync
; Bit in
.EQU
.EQU
.EQU
PortBUse for
. atpLoadedBit
.EQU
0
1
2
.ATP
4
;unconfigured
;configured for AppleTalk
;configured for the Serial Driver
driver status
;set if .ATP driver is opened
; Unit numbers for AppleTalk drivers
mppUnitNurn
atpUnitNurn
; csCode values
writeLAP
detachPH
attachPH
writeDDP
closes kt
openSkt
.1,oadNBP
confinnName
lookupName
rernoveName
registerName
killNBP
unloadNBP
; csCode values
relRspCB
closeATPSkt
addResponse
sendResponse
getRequest
openATPSkt
sendRequest
relTCB
; ALAP header
lapDstAdr
lapSrcAdr
lap Type
.EQU
9
.EQU
10
for Control
.EQU
243
.EQU
244
.EQU
245
.EQU
246
.EQU
247
.EQU
248
.EQU
249
.EQU
250
.EQU
251
.EQU
252
.EQU
253
.EQU
254
.EQU
255
for Control
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
249
250
251
252
253
254
255
256
0
1
2
111-58 AppleTalk Manager
; .MPP driver
; .ATP driver
calls (MPP)
calls (ATP)
;destination node ID
;source node ID
;ALAP protocol type

<!-- source-page: 66 -->
## Page 66

; ALAP header size
lapHdSz
.EQU
3
; ALAP protocol type values
shortDDP
longDDP
i Long DDP
ddpHopCnt
ddpLength
.EQU
.EQU
header
.EQU
.EQU
ddpChecksum
.EQU
ddpDstNet
ddpSrcNet
ddpDstNode
ddpSrcNode
ddpDstSkt
ddpSrcSkt
ddpType
; DDP long
ddpHSzLong
i Short DDP
ddpLength
sDDPDstSkt
sDDPSrcSkt
sDDPType
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
header size
.EQU
header
.EQU
.EQU
.EQU
.EQU
; DDP short header size
ddpHSzShort
.EQU
1
2
0
0
2
4
6
8
9
10
11
12
;short DDP header
;long DDP header
;count of bridges passed (4
;datagram length (10 bits)
;checksum
;destination network number
;source network number
;destination node ID
;source node ID
;destination socket number
;source socket number
;DDP protocol type
ddpType+l
bits)
0
ddpCheckstun
sDDPDstSkt+l
sDDPSrcSkt+l
;datagram length
;destination socket number
;source socket number
;DDP protocol type
sDDPType+l
; Mask for datagram length
ddpLenMask
.EQU
$03FF
; Maximum size of DDP data
ddpMaxData
; ATP header
atpControl
atpBitMap
atpRespNo
atpTransID
atpUserData
.EQU
586
.EQU
0
.EQU
1
.EQU
1
.EQU
2
.EQU
4
;control information
;bit map
;sequence ntunber
;transaction ID
;user bytes
Summary
AppleTalkManager JJl-59

<!-- source-page: 67 -->
## Page 67

Inside Macintosh
; ATP header size
atpHdSz
.EQU
8
; DDP protocol type f or ATP packets
atp
.EQU
; ATP function code
atpReqCode
atpRspCode
atpRelCode
.EQU
.EQU
.EQU
3
$40
$80
$CO
;TReq packet
;TResp packet
;TRel packet
; ATPFlags control inf orrnation bits
sendChk
.EQU
0
;send-checksum bit
tidValid
.EQU
1
;transaction ID validity bit
atpSTSBit
.EQU
3
;send-transmission- stat us bit
atpEOMBit
.EQU
4
;end-of-message bit
atpXOBit
.EQU
5
;exactly-once bit
; Maximum number of ATP request packets
atpMaxNum
.EQU
8
; ATP buffer data structure
bdsBuffSz
bdsBuffAddr
bdsDataSz
bdsUserData
.EQU
.EQU
.EQU
.EQU
; BDS element size
bdsEntrySz
; NBP packet
nbpControl
nbpTCount
nbpID
nbpTuple
.EQU
.EQU
.EQU
.EQU
.EQU
0
2
6
8
12
0
0
1
2
;size of data to send or buffer size
;pointer to data or buffer
;number of bytes actually received
;user bytes
;packet type
;tuple count
;packet identifier
;start of first tuple
; DDP protocol type for NBP packets
nbp
.EQU
2
Il/-60 App/eTa/k Manager

<!-- source-page: 68 -->
## Page 68

; NBP packet types
brRq
lkUp
lkUpReply
; NBP tuple
tupleNet
tupleNode
tupleSkt
tupleEnum
tupleName
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
1
2
3
0
2
3
4
5
;broadcast request
;lookup request
;lookup reply
;network number
;node ID
;socket number
;used internally
;entity name
Summary
; Maximum number of tuples in NBP packet
tupleMax
.EQU
15
; NBP meta-characters
equals
.EQU
'='
;"wild-card" meta-character
star
.EQU
I* f
;"this zone" meta- character
; NBP names tabl e entry
ntLink
.EQU
0
;pointer to next entry
ntTuple
.EQU
4
;tuple
ntSocket
.EQU
7
;socket number
ntEntity
.EQU
9
;entity name
; NBP names information socket number
nis
.EQU
2
Routines
Link Access Protocol
WriteLAP function
~ 26
cs Code
word
;always writeLAP
~
30
wdsPointer
pointer
;write data structure
AttachPH function
~ 26
cs Code
word
;always attachPH
~ 28
protType
byte
;ALAP protocol type
~
30
handler
pointer
;protocol handler
AppleTalk Manager III-61

<!-- source-page: 69 -->
## Page 69

Inside Macintosh
DetachPH function
~ 26
csCode
word
;always detachPH
~ 28
protType
byte
;ALAP protocol type
Datagram Delivery Protocol
OpenSkt function
~ 26
csCode
word
;always openSkt
H
28
socket
byte
;socket number
~ 30
listener
pointer
;socket listener
CloseSkt function
~ 26
csCode
word
;always closeSkt
~ 28
socket
byte
;socket number
WriteDDP function
~ 26
csCode
word
;always writeDDP
~ 28
socket
byte
;socket number
~ 29
checksumFlag byte
;checksum flag
~ 30
wdsPointer
pointer
;write data structure
AppleTalk Transaction Protocol
OpenA TPSkt function
~ 26
csCode
word
;always openA TPSkt
H
28
atpSocket
byte
;socket number
~ 30
addrBlock
long word
;socket request specification
OoseA TPSkt function
~ 26
csCode
word
;always closeA TPSkt
~ 28
atpSocket
byte
;socket number
SendRequest function
~
18
user Data
long word
;user bytes
f-
22
reqTID
word
;transaction ID used in request
~ 26
csCode
word
;always sendRequest
f-
28
currBitMap
byte
;bit map
H
29
atpFlags
byte
;control information
~ 30
addrBlock
long word
;destination socket address
~ 34
reql.ength
word
;request size in bytes
~ 36
reqPointer
pointer
;pointer to request data
~ 40
bdsPointer
pointer
;pointer to response BDS
~ 44
numOIBuffs
byte
;number of responses expected
~ 45
timeOutVal
byte
;timeout interval
f-
46
numOfResps byte
;number of responses received
H
47
retryCount
byte
;number of retries
GetRequest function
f-
18
user Data
long word
;user bytes
~ 26
csCode
word
;always getRequest
~ 28
atpSocket
byte
;socket number
III-62 AppleTalk Manager

<!-- source-page: 70 -->
## Page 70

Swnmary
GetRequest function
~
18
user Data
long word
;user bytes
~ 26
cs Code
word
;always getRequest
~ 28
atpSocket
byte
;socket number
~ 29
atpFlags
byte
;control infonnation
~ 30
addrBlock
long word
;source of request
f-7
34
reqLength
word
;request buffer size
~ 36
reqPointer
pointer
;pointer to request buffer
~ 44
bitMap
byte
;bitmap
~ 46
trans ID
word
;transaction ID
SendResponse function
~ 18
user Data
long word
;user bytes from 1Rel
~ 26
csCode
word
;always sendResponse
~ 28
atpSocket
byte
;socket number
~ 29
atpFlags
byte
;control infonnation
~
30
addrBlock
long word
;response destination
~ 40
bdsPointer
pointer
;pointer to response BDS
~ 44
numOfBuffs
byte
;number of response packets being sent
~ 45
bdsSize
byte
;BDS size in elements
~ 46
trans ID
word
;transaction ID
Add.Response function
~ 18
user Data
long word
;user bytes
~ 26
csCode
word
;always addResponse
~ 28
atpSocket
byte
;socket number
~ 29
atpFlags
byte
;control infonnation
~ 30
addrBiock
long word
;response destination
~ 34
reqLength
word
;response size
~ 36
reqPointer
pointer
;pointer to response
~ 44
rspNum
byte
;sequence number
~ 46
trans ID
word
;transaction ID
RelTCB function
~ 26
csCode
word
;always relTCB
~ 30
addrBlock
long word
;destination of request
~ 46
trans ID
word
;transaction ID of request
RelRspCB function
~ 26
csCode
word
;always relRspCB
~ 28
atpSocket
byte
;socket number that request was received on
~ 30
addrBlock
long word
;source of request
~ 46
trans ID
word
;transaction ID of request
AppleTalk Manager Ill-63

<!-- source-page: 71 -->
## Page 71

Inside Macintosh
Name-Binding Protocol
RegisterName function
~ 26
csCode
word
;always registerName
~ 28
interval
byte
;retry interval
H
29
count
byte
;retry count
~ 30
ntQEIPtr
pointer
;names table element pointer
~ 34
verify Flag
byte
;set if verify needed
LookupName function
~ 26
cs Code
word
;always lookupName
~ 28
interval
byte
;retry interval
H
29
count
byte
;retry count
~ 30
entityPtr
pointer
;pointer to entity name
~ 34
retBuffPtr
pointer
;pointer to buffer
~
38
retBuffSize
word
;buffer size in bytes
~ 40
maxToGet
word
;matches to get
f-
42
numGotten
word
;matches found
ConfirmName function
~ 26
cs Code
word
;always confirmN ame
~
28
interval
byte
;retry interval
H
29
count
byte
;retry count
~ 30
entityPtr
pointer
;pointer to entity name
~ 34
confirmAddr
pointer
;entity address
f-
38
new Socket
byte
;socket number
RemoveName function
~ 26
cs Code
word
;always removeName
~ 30
entityPtr
pointer
;pointer to entity name
LoadNBP function
~ 26
cs Code
word
;always loadNBP
UnloadNBP function
~ 26
cs Code
word
;always unloadNBP
Variables
SPConfig
Use types for serial ports (byte)
PortBUse
ABusVars
(bits 0-3: current configuration of serial port B
bits 4-6: current configuration of serial port A)
Current availability of serial port B (byte)
(bit 7: 1 =not in use, 0 = in use
bits 0-3: current use of port bits
bits 4-6: driver-specific)
Pointer to AppleTalk variables
1//-64 AppleTalk Manager

<!-- source-page: 72 -->
## Page 72

BINARY-DECIMAL CONVERSION PACKAGE
Routines
PROCEDURE NumToString (theNum: LONGINT; VAR theString: Str255);
PROCEDURE StringToNum (theString: Str255; VAR theNum: LONGINT);
Assembly-Language Information
Constants
; Routine selectors
numToString
stringToNum
Routines
.EQU
.EQU
On entry
0
1
On exit
Summary
Name
NumToString
AO: ptr to theString (preceded by length byte)
AO: ptr to theString
DO: theNum (long)
StringToNum
AO: ptr to theString (preceded by length byte) DO: theNum (Jong)
Trap Macro Name
Pack?
Binary-Decimal Conversion Package III-65

<!-- source-page: 73 -->
## Page 73

Inside Macintosh
CONTROL MANAGER
Constants
CONST { Control definition IDs }
pushButProc
checkBoxProc
radioButProc
useWFont
scrollBarProc
O;
{simple button}
l;
{check box}
2;
{radio button}
8;
{add to above to use window's font }
16; {scroll bar}
{ Part codes
inButton
inCheckBox
inUpButton
inDownButton
inPageUp
inPageDown
in Thumb
10;
{simple button}
11;
{check box or radio button}
20;
{up arrow of a scroll bar}
21;
{down arrow of a scroll bar}
22;
{"page up" region of a scroll bar}
23;
{"page down" region of a scroll bar}
12 9; {thumb of a scroll bar}
{ Axis constraints for DragControl
noConstraint
hAxisOnly
vAxisOnly
0;
{no constraint}
l; {horizontal axis only}
2;
{vertical axis only}
{ Messages to control definition function
drawCntl
testCntl
calcCRgns
initCntl
dispCntl
posCntl
thumbCntl
dragCntl
autoTrack
Data Types
TYPE ControlHandle
ControlPtr
O; {draw the control (or control part)}
1; {test where mouse button was pressed}
2; {calculate control's region (or indicator's) }
3; {do any additional control initialization}
4; {take any additional disposal actions}
5; {reposition control's indicator and update it}
6; {calculate parameters for dragging indicator}
7; {drag control (or its indicator)}
8; {execute control's action procedure}
"ControlPtr;
"ControlRecord;
111-66 Control Manager

<!-- source-page: 74 -->
## Page 74

ControlRecord =
PACKED RECORD
nextControl:
contrl Owner:
contrlRect:
contrlVis:
contrlHilite:
contrlValue:
contrlMin:
contrlMax:
ControlHandle;
Wi ndowPtr;
Rect;
Byte;
Byte;
INTEGER;
INTEGER;
INTEGER;
Summary
{next control}
{control' s window}
{enclosing rectangle}
(255 if visible}
{highlight state}
contrlDefProc: Handle;
contrlData:
Handle;
{control ' s current setting}
{control' s minimum setting}
{control ' s maximum setting}
{control definition function}
{data used by contrlDefProc}
{default action procedure}
{control' s reference value}
{control ' s t itle}
contrlAct ion:
contrlRfCon :
contrlTitle:
END;
Routines
ProcPtr;
LONGINT;
Str 255
Initialization and Allocation
FUNCTION
NewControl
(theWi ndow : WindowPtr; boundsRect: Rect; title:
Str 255; visible: BOOLEAN; value: I NTEGER;
min,max: INTEGER; procID: INTEGER; refCon:
LONGINT) : ControlHandle;
FUNCTION
GetNewControl
(contr ol ID: INTEGER; theWindow: WindowPtr) :
ControlHandle;
PROCEDURE DisposeControl (theContr ol : Cont rol Handle);
PROCEDURE KillControls
(theWindow: WindowPtr);
Control Display
PROCEDURE SetCTitle
PROCEDURE GetCTitle
PROCEDURE HideControl
PROCEDURE ShowControl
PROCEDURE DrawContr ols
PROCEDURE Hili teCont rol
Mouse Location
(theControl: Cont r olHandle; title: Str255);
(theControl : ControlHandle; VAR title : Str255);
(theControl: ControlHandle) ;
(theControl : ControlHandle);
(theWindow : WindowPtr);
(theControl: ControlHandle; hiliteState:
INTEGER);
FUNCTION FindControl
(thePoint : Point; theWindow: WindowPtr; VAR
whichControl: ControlHandle) : INTEGER;
FUNCTION TrackControl
(theControl: ControlHandle; startPt: Point;
actionProc: ProcPtr) : INTEGER;
FUNCTION TestControl
(theControl: ControlHandle; thePoint : Point)
INTEGER;
Control Manager l//-67

<!-- source-page: 75 -->
## Page 75

Inside Macintosh
Control Movement and Sizing
PROCEDURE MoveControl
(theControl: ControlHandle; h,v: INTEGER);
PROCEDURE DragControl
(theControl: ControlHandle; startPt: Point;
limitRect,slopRect: Rect; axis: INTEGER);
PROCEDURE SizeControl
(theControl: ControlHandle; w,h: INTEGER);
Control Setting and Range
PROCEDURE SetCtlValue
(theControl: ControlHandle; theValue: INTEGER);
FUNCTION
GetCtlValue
(theControl: ControlHandle)
: INTEGER;
PROCEDURE SetCtlMin
(theControl: ControlHandle; minValue: INTEGER);
FUNCTION
GetCtlMin
(theControl: ControlHandle)
: INTEGER;
PROCEDURE SetCtlMax
(theControl: ControlHandle; maxValue INTEGER);
FUNCTION
GetCtlMax
(theControl: ControlHandle)
: INTEGER;
Miscellaneous Routines
PROCEDURE SetCRefCon
FUNCTION GetCRefCon
PROCEDURE SetCtlAction
FUNCTION
GetCtlAction
(theControl: ControlHandle; data: LONGINT);
(theControl: ControlHandle) : LONGINT;
(theControl: ControlHandle; actionProc ProcPtr);
(theControl: ControlHandle) : ProcPtr;
Action Procedure for TrackControl
If an indicator:
PROCEDURE MyAction;
If not an indicator:
PROCEDURE MyAction (theControl: ControlHandle;
partCode: INTEGER);
Control Definition Function
FUNCTION MyControl
(varCode: INTEGER; theControl: ControlHandle;
message: INTEGER; param: LONGINT) : LONGINT;
Assembly-Language Information
Constants
i Control definition IDs
pushButProc
.EQU
0
; simple button
checkBoxProc
.EQU
1
;check box
radioButProc
.EQU
2
;radio button
useWFont
.EQU
8
;add to above to use window's font
scrollBarProc
.EQU
16
;scroll bar
III-68 Control Manager

<!-- source-page: 76 -->
## Page 76

; Part codes
inButton
inCheckBox
inUpButton
inDownButton
inPageUp
inPageDown
in Thumb
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
10
;simple button
11
;check box or radio button
20
;up arrow of a scr oll bar
21
;down arrow of a scroll bar
22
;"page up" region of a scroll bar
23
;"page down" region of a scroll bar
129 ;thumb of a scroll bar
Summary
; Axis constraints for DragControl
noConstraint
hAxisOnly
vAxisOnly
.EQU
0
.EQU
1
.EQU
2
;no constraint
;horizontal axis only
;vertical axis only
; Messages to control definition function
drawCtlMsg
hitCtlMsg
calcCtlMsg
newCtlMsg
dispCtlMsg
posCtlMsg
thurnbCtlMsg
dragCtlMsg
trackCtlMsg
.EQU
0
.EQU
1
.EQU
2
.EQU
3
.EQU
4
.EQU
5
.EQU
6
.EQU
7
.EQU
8
;draw the control (or control part)
;test where mouse button was pressed
;calculate control's region (or indicator's)
;do any additional control initialization
;take any additional disposal actions
;reposition control's indicator and update it
;calculate parameters for dragging indicator
;drag control (or its indicator)
;execute control's action procedure
Control Record Data Structure
nextControl
contrlOwner
contrlRect
contrlVis
contrlHilite
contrlV alue
contrlMin
contrlMax
contrlDefHandle
contrlData
contrlAction
contrlRfCon
contrlTitle
contrlSize
Handle to next control in control list
Pointer to this control's window
Control's enclosing rectangle (8 bytes)
255 if control is visible (byte)
Highlight state (byte)
Control's current setting (word)
Control's minimum setting (word)
Control's maximum setting (word)
Handle to control definition function
Data used by control definition function (long)
Address of default action procedure
Control's reference value (long)
Handle to control's title {preceded by length byte)
Size in bytes of control record except contrlTitle field
Control Manager 111-69

<!-- source-page: 77 -->
## Page 77

Inside Macintosh
Special Macro Names
Pascal name
DisposeControl
GetCtlMax
GetCtlMin
SetCtlMax
SetCtlMin
Variables
Macro name
_ DisposControl
GetMaxCtl
-GetMinCtl
SetMaxCtl
SetMinCtl
DragHook
DragPattem
Address of procedure to execute during TrackControl and DragControl
Pattern of dragged region's outline (8 bytes)
/11-70 Control Manager

<!-- source-page: 78 -->
## Page 78

DESK MANAGER
Routines
Opening and Closing Desk Accessories
FUNCTION
OpenDeskAcc
(theAcc: Str255) : INTEGER;
PROCEDURE CloseDeskAcc (refNum: INTEGER);
Handling Events in Desk Accessorius
PROCEDURE SystemClick (theEvent: EventR•:!cord; theWindow: WindowPtr) ;
FUNCTION
SystemEdit
(editDnd: INTEGER) : BOOLEAN;
Performing Periodic Actions
PROCEDURE SystemTask;
Advanced Routines
FUNCTION
SystemEvent (theEvent: EventR•:!Cord)
PROCEDURE SystemMenu
(rnenuResult: LONGINT);
Assembly-Language Information
Constants
; Desk accessory flag
BOOLEAN;
Summary
dNeedTime
.EQU
5
;set if driver needs time for performing a
; periodi·: action
; Control routine messages
accEvent
.EQU
64
;handle a given event
accRun
.EQU
65
;take the periodic action, if any, for
; this desk accessory
accCursor
.EQU
66
;change cursor shape if appropriate;
; generate null event if window was
; created by Dialog Manager
accMenu
.EQU
67
;handle a given menu item
a cc Undo
.EQU
68
;handle the Undo command
Desk Manager 111-71

<!-- source-page: 79 -->
## Page 79

Inside Macintosh
accCut
accCopy
accPaste
accClear
.EQU
.EQU
.EQU
.EQU
70
71
72
73
;handle the Cut command
;handle the Copy command
;handle the Paste command
;handle the Clear command
Special Macro Names
Pascal name
SystemEdit
Variables
MBarEnable
SEvtEnb
Macro name
_SysEdit
Unique menu ID for active desk accessory, when menu bar belongs to the
accessory (word)
0 if SystemEvent should return FALSE (byte)
Ill-72 Desk Manager

<!-- source-page: 80 -->
## Page 80

DEVICE MANAGER
Constants
CONST { Values for requesting read/write access }
fsCurPerm
fsRdPerm
fsWrPerm
fsRd.WrPerm
0;
l;
2;
3;
{whatever is currently allowed}
{request to read only}
{request to write only}
{request to read and write}
{ Positioning modes
fsAtMark
fsFromStart
fsFrorrt1ark
rdVerify
0;
{at current position}
l;
{offset relative to beginning of medium}
3;
{offset relative to current position}
64;
{add to above for read-verify}
Data Types
TYPE ParamBlkType
(ioParam,fileParam,volumeParam,cntrlParam);
ParmBlkPtr
ParamBlockRec
qLink:
= AParamBlockRec;
RECORD
qType:
ioTrap :
ioCrndAddr:
ioCompletion:
ioResult:
ioNamePtr:
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{driver name}
Summary
ioVRefNum:
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
OF
{volume reference or drive number}
CASE ParamBlkType
ioParam:
(ioRefNum:
ioVersNum:
ioPermssn:
ioMisc:
ioBuffer:
ioReqCount:
ioActCount:
INTEGER;
SignedByte;
SignedByte;
Ptr;
Ptr;
LONGINT;
LONGINT;
ioPosMode:
INTEGER;
ioPosOffset: LONGINT);
fileParam:
. . . {used by File Manager}
volumeParam:
{driver reference number}
{not used}
{read/write permission}
{not used}
{pointer to data buffer}
{requested number of bytes}
{actual number of bytes}
{positioning mode}
{positioning offset}
. .. {used by File Manager}
Device Manager /11-73

<!-- source-page: 81 -->
## Page 81

Inside Macintosh
cntrlParam:
(ioCRefNum: INTEGER;
{driver reference number}
csCode:
INTEGER;
{type of Control or Status call}
csParam:
ARRAY[0 .. 10) OF INTEGER) {control or status information}
END;
DCtlHandle
DCtlPtr
DCtlEntry
"OCtlPtr;
"DCtlEntry;
RECORD
dCtlDriver :
Ptr;
{pointer t o ROM driver or handle t o l
{ RAM driver}
dCtlFlags:
dCtlQHdr :
dCtlPosition:
dCtlStorage:
dCtlRefNum:
dCtlCurTicks :
dCtlWindow:
dCtlDelay:
dCtlEMask:
dCtlMenu:
END;
INTEGER;
QHdr;
LONGINT;
Handle;
INTEGER;
LONGINT;
WindowPtr;
INTEGER;
INTEGER;
INTEGER
{flags}
{driver I /O queue header)
{byte position used by Read and
{ Write calls}
{handle to RAM driver ' s private
{ storage}
{driver reference number}
{used internally}
{pointer to driver ' s window}
{number of ticks between periodic
{ actions}
{desk accessory event mask}
{menu ID of menu associated with
{ driver}
High-Level Routines (Not in ROM]
FUNCTION OpenDriver
(name: Str255; VAR refNum: INTEGER)
: OSErr ;
FUNCTION CloseDriver
(refNum: INTEGER)
: OSErr;
FUNCTION FSRead
(refNum: INTEGER; VAR count: LONGINT; buffPtr:
: OSErr ;
FUNCTION FSWrite
(refNum: INTEGER; VAR count : LONGINT; buffPtr:
: OSErr;
FUNCTION Control
(refNum: INTEGER; csCode: INTEGER; csParamPtr:
: OSErr;
FUNCTION Status
(refNum: INTEGER; csCode : INTEGER; csParamPtr:
: OSErr;
FUNCTION Kill IO
(refNum: INTEGER)
: OSErr;
Low-Level Routines
FUNCTION PBOpen (paramBlock : ParmBlkPtr ; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
t--
16
ioResult
word
~ 18
ioNamePtr
point.er
t--
24
ioRefNum
word
~ Tl
ioPermssn
byte
111-74 Device Manager
Ptr)
Ptr)
Ptr )
Ptr)

<!-- source-page: 82 -->
## Page 82

Summary
FUNCTION PBClose (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
f--
16
ioResult
word
~ 24
ioRefNum
word
FUNCTION PBRead (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
f--
16
ioResult
word
~ 22
ioVRefNum
word
~ 24
ioRefNum
word
~ 32
ioBuffer
pointer
~ 36
ioReqCount
long word
f--
40
ioActCount
long word
~ 44
ioPosMode
word
H
46
ioPosOffset
long word
FUNCTION PBWrite (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
f--
16
ioResult
word
~ 22
ioVRefNum
word
~ 24
ioRefNum
word
~ 32
ioBuffer
pointer
~ 36
ioReqCount
long word
f--
40
ioActCount
long word
~ 44
ioPosMode
word
H
46
ioPosOffset
long word
FUNCTION PBControl (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
f--
16
ioResult
word
~ 22
ioVRefNum
word
~ 24
ioRefNum
word
~ 26
cs Code
word
~ 28
csParam
record
FUNCTION PBStatus (paramBlock : ParmBlkPtr; async : BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
f--
16
ioResult
word
~ 22
ioVRefNum
word
~ 24
ioRefNum
word
~ 26
cs Code
word
f--
28
csParam
record
FUNCTION PBKillIO (paramBlock : ParmBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
f--
16
ioResult
word
~ 24
ioRefNum
word
Device Manager ll!-75

<!-- source-page: 83 -->
## Page 83

Inside Macintosh
Accessing a Driver's Device Control Entry
FUNCTION GetDCtlEntry (refNum: INTEGER) : DCtlHandle;
[NotinROM]
Result Codes
Name
abortErr
badUnitErr
controlErr
dlnstErr
dRemovErr
no Err
notOpenErr
openErr
read Err
statusErr
unitEmpty Err
writErr
Value
-27
-21
-17
-26
-25
0
-28
-23
-19
-18
-22
-20
Meaning
1/0 request aborted by KillIO
Driver reference number doesn't match unit table
Driver can't respond to this Control call
Couldn't find driver in resource file
Attempt to remove an open driver
No error
Driver isn't open
Requested read/write permission doesn't match driver's
open permission
Driver can't respond to Read calls
Driver can't respond to this Status call
Driver reference number specifies NIL handle in unit table
Driver can't respond to Write calls
Assembly-Language Information
Constants
; Flags in trap words
asnycTrpBit
noQueueBit
.EQU
.EQU
10
9
;set for an asynchronous call
;set for irmnediate execution
; Values for requesting read/write access
fsCurPerm
fsRdPerm
fsWrPerm
fsRdWrPerm
.EQU
.EQU
.EQU
.EQU
; Positioning modes
fsAtMark
fsFromStart
fsFromMark
rdVerify
.EQU
.EQU
.EQU
.EQU
III-76 Device Manager
0
1
2
3
0
1
3
64
;whatever is currently allowed
;request to read only
;request to write only
;request to read and write
;at current position
;offset relative to beginning of medium
;offset relative to current position
;add to above for read-verify

<!-- source-page: 84 -->
## Page 84

Summary
; Driver flags
dReadEnable
dWritEnable
dCtlEnable
d.StatEnable
dNeedGood.Bye
dNeedTi.me
dNeedLock
.EQU
.EQU
.EQU
. EQU
.EQU
.EQU
.EQU
0
;set if driver can respond to Read calls
1
;set if driver can respond to Write calls
2
;set if driver can respond to Control calls
3
;set if driver can respond to Status calls
4
;set if driver needs to be called before the
; application heap is reinitialized
5
;set if driver needs time for performing a
; periodic action
6
;set if driver will be locked in memory as
soon as it's opened (always set for ROM
drivers)
; Device control entry flags
dOpened
.EQU
5
;set if driver is open
d.RAMBased
.EQU
6
;set if driver is RAM-based
drvrActive
.EQU
7
; set if driver is currently executing
; csCode values for driver control routine
accRun
.EQU
65
;take the periodic action, if any, for this
good.Bye
kill Code
; Low-order
aRdCmd
aWrCmd
.EQU
.EQU
byte
.EQU
.EQU
of
; driver
-1
;heap will be reinitialized,
; necessary
1
;handle the KillIO call
Device Manager traps
2
3
;Read call (trap $A002)
;Write cal l (trap $A003)
; Offsets from SCC base addresses
aData
.EQU
6
;channel A data in or out
aCtl
.EQU
2
;channel A control
bData
.EQU
4
;channel B data in or out
bCtl
.EQU
0
;channel B control
Standard Parameter Block Data Structure
qLink
qType
ioTrap
ioCmdAddr
ioCompletion
ioResult
ioVNPtr
ioVRefNum
ioDrvNum
Pointer to next queue entry
Queue type (word)
Routine trap (word)
Routine address
Address of completion routine
Result code (word)
Pointer to driver name (preceded by length hyte)
Volume reference number (word)
Drive number (word)
clean up if
Device Manager Ill-77

<!-- source-page: 85 -->
## Page 85

Inside Macintosh
Control and Status Parameter Block Data Structure
ioRefNum
cs Code
csParam
Driver reference number (word)
Type of Control or Status call (word)
Parameters for Control or Status call (22 bytes)
1/0 Parameter Block Data Structure
ioRefNum
ioPermssn
ioBuffer
ioReqCount
ioActCount
ioPosMode
ioPosOffset
Driver reference number (word)
Open permission (byte)
Pointer to data buffer
Requested number of bytes (long)
Actual number of bytes (long)
Positioning mode (word)
Positioning offset (long)
Device Driver Data Structure
drvrFlags
drvrDelay
drvrEMask
drvrMenu
drvrOpen
drvrPrime
drvrCtl
drvrStatus
drvrClose
drvrName
Flags (word)
Number of ticks between periodic actions (word)
Desk accessory event mask (word)
Menu ID of menu associated with driver (word)
Offset to open routine (word)
Offset to prime routine (word)
Offset to control routine (word)
Offset to status routine (word)
Offset to close routine (word)
Driver name (preceded by length byte)
Device Control Entry Data Structure
dCtlDriver
dCtlFlags
dCtlQueue
dCtlQHead
dCtlQTail
dCtlPosition
dCtlStorage
dCtlRefNum
dCtlWindow
dCtlDelay
dCtlEMask
dCtlMenu
Pointer to ROM driver or handle to RAM driver
Flags (word)
Queue flags: low-order byte is driver's version number (word)
Pointer to first entry in driver's 110 queue
Pointer to last entry in driver's 1/0 queue
Byte position used by Read and Write calls (long)
Handle to RAM driver's private storage
Driver's reference number (word)
Pointer to driver's window
Number of ticks between periodic actions (word)
Desk accessory event mask (word)
Menu ID of menu associated with driver (word)
Structure of Primary Interrupt Vector Table
auto Intl
autolnt2
Vector to level-I interrupt handler
Vector to level-2 interrupt handler
///-78 Device Manager

<!-- source-page: 86 -->
## Page 86

autolnt3
autolnt4
autolnt5
autolnt6
autolnt7
Vector to level-3 interrupt handler
Vector to level-4 interrupt handler
Vector to level-5 interrupt hand~(
Vector to level-6 interrupt handler
Vector to level-7 interrupt handler
Summary
Macro Names
Pascal name
PB Read
PB Write
PB Control
PB Status
PBKilllO
Macro name
Read
Write
Control
Status
KillIO
Routines for Writing Drivers
Routine
Fetch
Stash
IO Done
Variables
UTableBase
JFetch
JStash
TIO Done
LvllDT
Lvl2DT
VIA
ExtStsDT
SCCWr
SCCRd
Jump vector
JP etch
JStash
JIODone
On entry
Al: ptr to device
control entry
Al : ptr to device
control entry
DO: character to stash
Al: ptr to device
control entry
DO: result code (word)
Base address of unit table
Jump vector for Fetch function
Jump vector for Stash function
Jump vector for IODone function
On exit
DO: character fetched; bit 15=1
if last character in buffer
DO: bit 15= 1 if last character
requested
Level-1 secondary interrupt vector table (32 bytes)
Level-2 secondary interrupt vector table (32 bytes)
VIA base address
External/status interrupt vector table (16 bytes)
sec write base address
sec read base address
Device Manager Ill-79

<!-- source-page: 87 -->
## Page 87

\
\
' \
Inside Macintosh
DIALOG MANAGER
Constants
CONST
{ Item types
ctrl item
btnCtrl
chkCtrl
r adCtrl
resCtrl
stat Text
editText
i con Item
pici tem
user Item
itemDi sabl e
4;
O;
l;
2;
3;
8;
16;
32;
64 ;
0;
128;
{add to following four constants}
{standard but ton control}
{standard check box control}
{standard r adio button control}
{control defined in control t emplat e}
{static text}
{editabl e text
(dialog only) }
{icon}
{Qui ckDraw picture}
{appli cation- defined item (dialog only)}
{add to any of above to disable }
{ I tem numbers of OK and Cancel buttons }
ok
1;
cancel
2;
{ Resource IDs of alert icons
stopicon
0;
note I con
1;
cautionicon
2;
Data Types
TYPE Di al ogPtr
Di a l ogPeek
Wi ndowPt. r ;
"Dial ogRecord;
Di al ogRecord
RECORD
window :
items :
textH :
WindowRecor d;
Handle;
TEHandl e;
editFiel d: INTEGER;
edi tOpen:
INTEGER;
aDefitem:
INTEGER
END;
Di alogTHndl
DialogTPtr
III-80 Dialog Manager
"DialogTPtr;
"Dial ogTempl at e;
{dialog wi ndow}
{item list}
{current editText item}
{editText i tem number minus 1 )
{used internally}
{default button item number }

<!-- source-page: 88 -->
## Page 88

DialogTernplate
RECORD
boundsRect: Rect;
procID:
INTEGER;
visible:
fillerl:
BOOLEAN;
BOOLEAN;
goAwayFlag: BOOLEAN;
filler2:
BOOLEAN;
refCon:
itemsID :
title:
LONGINT;
INTEGER;
Str255
END;
AlertTHndl
AlertTPtr
Alert Template
"AlertTPtr;
"Alert Template;
RECORD
{becomes window ' s portRect}
{window definition ID}
{TRUE if visible}
{not used}
{TRUE if has go-away region}
{not used}
{window's reference value}
{resource ID of item list}
{window's title }
Summary
boundsRect: Rect;
iternsID:
INTEGER;
{becomes wi ndow's portRect}
{resource ID of item l ist}
StageList
Routines
Initialization
stages:
StageList {alert stage i nformat ion}
END:
PACKED RECORD
bolditm4 : 0 •. 1;
{default button item number minus 1 )
boxDrwn4: BOOLEAN;
{TRUE if alert box to be drawn }
sound4 :
0 .. 3
{sound number}
bolditm3: O •• 1;
boxDrwn3: BOOLEAN;
sound3:
0 .. 3
bolditm2: 0 .. 1;
boxDrwn2 : BOOLEAN;
sound2:
0 .. 3
bolditml: 0 . . 1;
boxDrwnl: BOOLEAN;
soundl :
O •• 3
END;
PROCEDURE InitDialogs
PROCEDURE ErrorSound
PROCEDURE SetDAFont
(resumeProc: ProcPtr);
(soundProc: ProcPtr);
(fontNum: INTEGER);
[NotinROM]
Creating and Disposing of Dialogs
FUNCTION
NewDialog
(dStorage: Ptr; boundsRect: Rect; title: Str255;
visible: BOOLEAN; procID: INTEGER; behind:
WindowPtr; goAwayFlag: BOOLEAN; refCon: LONGINT;
items: Handle) : DialogPtr;
Dialog Manager III-81

<!-- source-page: 89 -->
## Page 89

Inside Macintosh
FUNCTION
GetNewDialog
PROCEDURE CloseDialog
PROCEDURE DisposDialog
PROCEDURE CouldDialog
PROCEDURE FreeDialog
(dialogID: INTEGER; dStorage : Ptr; behind :
WindowPtr) : DialogPtr;
(theDialog: DialogPtr);
(theDialog: DialogPtr);
(dialogID: INTEGER);
(dialogID: INTEGER);
Handling Dialog Events
PROCEDURE ModalDialog
FUNCTION
IsDialogEvent
FUNCTION
DialogSelect
PROCEDURE DlgCut
PROCEDURE DlgCopy
PROCEDURE DlgPaste
PROCEDURE DlgDelete
PROCEDURE DrawDialog
Invoking Alerts
FUNCTION
Alert
FUNCTION
StopAlert
FUNCTION
NoteAlert
FUNCTION
CautionAlert
PROCEDURE CouldAlert
PROCEDURE FreeAlert
(filterProc: ProcPtr; VAR i temHit: INTEGER);
(theEvent: EventRecord) : BOOLEAN;
(theEvent: EventRecord; VAR theDialog:
DialogPtr; VAR itemHit: INTEGER) : BOOLEAN;
(theDialog: DialogPtr) ;
[Not in ROM]
(theDialog: DialogPtr);
[Not in ROM]
(theDialog: DialogPtr);
[Not in ROM]
(theDialog: DialogPtr);
[Not in ROM]
(theDialog: DialogPtr);
(alertID: INTEGER;
(alertID: INTEGER;
(alertID: INTEGER;
(alertID: INTEGER;
(alertID: INTEGER);
(alertID: INTEGER);
filterProc : ProcPtr)
filterProc : ProcPtr)
filterProc : ProcPtr)
filterProc : ProcPtr)
INTEGER;
INTEGER;
INTEGER;
INTEGER;
Manipulating Items in Dialogs and Alerts
PROCEDURE ParamText
PROCEDURE GetDitem
PROCEDURE SetDitem
PROCEDURE GetIText
PROCEDURE Set!Text
PROCEDURE SelIText
FUNCTION
GetAlrtStage
PROCEDURE ResetAlrtStage;
Userltem Procedure
(param0,paraml, param2,pararn3 : Str255);
(theDialog: DialogPtr; i temNo: INTEGER; VAR
item'£ype: INTEGER; VAR item: Handle; VAR box:
Rect);
(theDialog: DialogPtr; itemNo : INTEGER;
itemType: INTEGER; item: Handle; box: Rect);
(item: Handle; VAR text: Str255);
(item: Handle; text: Str255);
(theDialog: DialogPtr; itemNo: INTEGER;
strtSel,endSel: INTEGER);
INTEGER;
[Not in ROM]
[Not in ROM]
PROCEDURE Myitem (theWindow: WindowPtr; itemNo: INTEGER);
IJI-82 Dialog Manager

<!-- source-page: 90 -->
## Page 90

Sound Procedure
PROCEDURE MySound (sound.No : INTEGER) ;
FilterProc Function for Modal Dialogs and Alerts
FUNCTION MyFilter (theDialog: DialogPtr; VAR theEvent: EventRecord;
VAR itemHit: INTEGER) : BOOLEAN;
Assembly-Language Information
Constants
; Item types
ctrlitem
btnCtrl
chkCtrl
radCtrl
resCtrl
stat Text
edit Text
icon Item
picitem
user Item
itemDisable
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
4
0
1
2
3
8
16
32
64
0
128
;add to following four constants
; standard button control
;standard check box control
;standard radio button control
;control defined in control templat e
; static text
;editable text (dialog onl y)
;icon
;QuickDraw picture
;application-defined item (dialog only)
;add to any of above to disable
; Item numbers of OK and Cancel buttons
okButton
.EQU
1
cancelButton .EQU
2
; Resource IDs of alert icons
stop Icon
note Icon
cautionicon
.EQU
.EQU
.EQU
0
1
2
; Masks for stages word in alert template
volBits
alBit
okDismissal
.EQU
.EQU
.EQU
3
4
8
; sound number
;whether to draw box
;item number of default button minus 1
Summary
Dialog Manager I!I-83

<!-- source-page: 91 -->
## Page 91

Inside Macintosh
Dialog Record Data Structure
dWindow
items
teHandle
editField
aDefltem
dWindLen
Dialog window
Handle to dialog's item list
Handle to current edi(fext item
Item number of editText item minus 1 (word)
Item number of default button (word)
Size in bytes of dialog record
Dialog Template Data Structure
dBounds
dWindProc
dVisible
dGoAway
dRefCon
ditems
dTitle
Rectangle that becomes portRect of dialog window's grafPort (8 bytes)
Window definition ID (word)
Nonzero if dialog window is visible (word)
Nonzero if dialog window has a go-away region (word)
Dialog window's reference value (long)
Resource ID of dialog's item list (word)
Dialog window's title (preceded by length byte)
Alert Template Data Structure
aBounds
aitems
aStages
Rectangle that becomes portRect of alert window's grafPort (8 bytes)
Resource ID of alert's item list (word)
Stages word; information for alert stages
Item List Data Structure
dlgMaxlndex
itmHndl
itmRect
itmType
itmData
Variables
ResumeProc
DAStrings
DABeeper
DlgFont
A Count
AN umber
Number of items minus 1 (word)
Handie·or procedure pointer for this item
Display rectangle for this item (8 bytes)
Item type for this item (byte)
Length byte followed by data for this item (data must be even number of bytes)
Address of resume procedure
Handles to ParamText strings (16 bytes)
Address of current sound procedure
Font number for dialogs and alerts (word)
Stage number (0 through 3) of last alert (word)
Resource ID of last alert (word)
111-84 Dialog Manager

<!-- source-page: 92 -->
## Page 92

DISK DRIVER
Constants
CONST { Positioning modes
fsAtMark
fsFromStart
fsFrom\1ark
rdVerify
Data Types
TYPE DrvSts = RECORD
0;
{at current sector}
1;
{relative to first sect or}
3;
{relative to current sector}
64;
{add to above for read-verify}
track :
INTEGER;
{current track}
Summary
writeProt :
diskinPlace:
SignedByte;
SignedByte;
{bit 7=1 if volume is locked}
{disk in place}
installed:
sides:
qLink:
qType:
dQDrive :
dQRefNum:
dQFSID:
twoSideFmt:
needsFlush:
diskErrs:
END;
Routines [Not in ROM]
SignedByte;
SignedByte;
QElemPtr;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
SignedByte;
SignedByte;
INTEGER
{drive installed}
{bit 7=0 if single- sided drive }
{next queue entry}
{reserved for future use}
{drive number}
{driver reference number}
{file-system identifier}
{-1 if two-sided disk}
{reserved for future use}
{error count}
FUNCTION DiskEject
(drvNum: INTEGER) : OSErr;
FUNCTION SetTagBuffer (buffPtr: Ptr) : OSErr;
FUNCTION DriveStatus
(drvNum: INTEGER; VAR status : DrvSts)
OSErr;
Result Codes
Name
Value
Meaning
no Err
0
No error
nsDrvErr
-56
No such drive
paramErr
-50
Bad positioning information
wPrErr
-44
Volume is locked by a hardware setting
Disk Driver /1/-85

<!-- source-page: 93 -->
## Page 93

Inside Macintosh
Name
Value
Meaning
firstDskErr
-84
First of the range of low-level disk errors
sectNFErr
-81
Can't find sector
seekErr
-80
Drive error
spdAdjErr
-79
Can't correctly adjust disk speed
twoSideErr
- 78
Tried to read side 2 of a disk in a single-sided drive
initIWMErr
- 77
Can't initialize disk controller chip
tkOBadErr
- 76
Can't find track 0
cantStepErr
-75
Drive error
wrUnderrun
- 74
Write underrun occurred
badDBtSlp
-73
Bad data mark
badDCksum
-72
Bad data mark
noDtaMkErr
-71
Can't find data mark
badBtSlpErr
-70
Bad address mark
badCksmErr
-69
Bad address mark
dataVerErr
-68
Read-verify failed
noAdrMkErr
-67
Can't find an address mark
noNybErr
-66
Disk is probably blank
offLinErr
-65
No disk in drive
noDriveErr
-64
Drive isn't connected
lastDskErr
-64
Last of the range of low-level disk errors
Assembly-Language Information
Constants
; Positioning modes
fsAtMark
fsFr omStart
fsFromMark
rdVerif y
.EQU
.EQU
.EQU
.EQU
0
1
3
64
;at current sector
;relative to first sector
;relative to current sector
;add to above for read- verify
; csCode values for Control/Stat us calls
ejectCode
tgBuffCode
drvStsCode
.EQU
.EQU
.EQU
7
8
8
;Control call, DiskEject
;Control call, SetTagBuffer
;Status call, DriveStatus
Structure of Status Information
dsTrack
dsWriteProt
dsDisklnPlace
dslnstalled
dsSides
dsQLink
dsDQDrive
III-86 Disk Driver
Current track (word)
Bit 7=1 if volume is locked (byte)
Disk in place (byte)
Drive installed (byte)
Bit 7=0 if single-sided drive (byte)
Pointer to next queue entry
Drive number (word)

<!-- source-page: 94 -->
## Page 94

dsDQRefNum
dsDQFSID
dsTwoSideFmt
dsDiskErrs
Driver reference number (word)
File-system identifier (word)
-1 if two-sided disk (byte)
Error count (word)
Summary
Equivalent Device Manager Calls
Pascal routine
DiskEject
SetTagBuffer
DriveStatus
Variables
BuffgFNum
BuffgFFlag
BuffgFBkNum
BuffgDate
Can
Control with csCode=ejectCode
Control with csCode=tgBuffCode
Status with csCode=drvStsCode, status returned in csParam through
csParam+21
File tags buffer: file number (long)
File tags buffer: flags (word: bit 1=1 if resource fork)
File tags buffer: logical block number (word)
File tags buffer: date and time of last modification (long)
Disk Driver III-87
-

<!-- source-page: 95 -->
## Page 95

Inside Macintosh
DISK INITIALIZATION PACKAGE
Routines
PROCEDURE DILoad;
PROCEDURE DIUnload;
FUNCTION
DIBadMount
FUNCTION
DIFormat
FUNCTION
DIVerify
FUNCTION
DIZero
Result Codes
Name
Value
badMDBErr
-60
extFSErr
-58
firstDskErr
-84
ioErr
-36
lastDskErr
-64
memFul!Err
-108
no Err
0
noMacDskErr
-57
nsDrvErr
-56
paramErr
-50
vo!OnLinErr
-55
(where: Point; evtMessage: LONG INT)
(drvNum: INTEGER)
: OSErr;
(drvNum: INTEGER)
: OSErr;
(drvNum: INTEGER; volName : Str255)
Meaning
Bad master directory block
External file system
First of the range of low-level disk errors
1/0 error
Last of the range of low-level disk errors
Not enough room in heap zone
No error
Not a Macintosh disk
No such drive
Bad drive number
Volume already on-line
Assembly-Language Information
Constants
; Routine selectors
di Bad.Mount
.EQU
0
di Load
.EQU
2
di Unload
.EQU
4
diFormat
. EQU
6
di Verify
.EQU
8
di Zero
.EQU
10
l//-88 Disk Initialization Package
INTEGER;
OSErr;

<!-- source-page: 96 -->
## Page 96

Trap Macro Name
Paclc2
Summary
Disk Initialization Package III-89
'

<!-- source-page: 97 -->
## Page 97

Inside Macintosh
EVENT MANAGER, OPERATING SYSTEM
Constants
CONST { Event codes }
nullEvent
mouseDown
mouse Up
keyDown
keyUp
autoKey
updateEvt
diskEvt
activateEvt
networkEvt
driverEvt
applEvt
app2Evt
app3Evt
app4Evt
O;
1;
2;
3;
4;
5;
6;
7;
{null}
{mouse-down}
{mouse-up}
(key-down}
(key-up}
(auto-key}
(update; Toolbox only}
{disk-inserted}
8;
{activate; Toolbox onl y}
10;
{network}
11;
(device driver}
12;
(application-defined}
13;
(application-defined}
14;
(application- defined}
15;
{application- defined}
( Masks for keyboard event message }
charCodeMask
keyCodeMask
$000000FF;
$0000FFOO;
(character code}
{key code}
( Masks for forming event mask }
mDownMask
mUpMask
keyDownMask
keyUpMask
autoKeyMask
updateMask
diskMask
activMask
networkMask
driverMask
applMask
app2Mask
app3Mask
app4Mask
everyEvent
2;
4;
8;
16;
32;
64;
128;
256;
1024;
2048;
4096;
8192;
16384;
-32768;
-1;
{mouse-down}
{mouse-up}
{key- down}
(key-up}
(auto-key}
{update}
(disk-inserted}
{activate}
{network}
(device driver}
(application-de fined}
{application-defined}
{application-defined}
(application-defined}
{all event types}
III-90 Event Manager, Operating System

<!-- source-page: 98 -->
## Page 98

Summary
{ Modifier flags in event record }
activeFlag = l;
{set if window being activated}
btnState
128;
{set if mouse button up}
cmdKey
256;
{set if Command key down}
shif tKey
512;
{set if Shift key down}
alpha Lock
1024;
{set if Caps Lock key down }
optionKey
2048;
{set if Option key down}
{ Result codes returned by PostEvent }
{no error (event posted) }
noErr
O;
evtNotEnb =
1;
{event type not designated in system event mask }
Data Types
TYPE EventRecord = RECORD
what :
message:
when:
INTEGER;
LONGINT;
LONGINT;
where:
Point;
EvQEl =RECORD
modifiers: INTEGER
END;
{event code}
{event message}
{ticks since startup}
{mouse location }
{modifier flags }
qLink:
qType:
evtQWhat:
evtQMessage:
evtQWhen:
QElemPtr; {next queue entry}
INTEGER;
{queue type}
INTEGER;
{event code}
Routines
LONGINT;
LONGINT;
evtQWhere:
Point;
evtQModifiers: INTEGER
END;
Posting and Removing Events
{event message}
{ticks since startup}
{mouse location }
{modifier flags }
FUNCTION
PostEvent
(eventCode: INTEGER; eventMsg: LONGINT)
PROCEDURE FlushEvents (eventMask,stopMask: INTEGER);
Accessing Events
OSErr;
FUNCTION GetOSEvent
(eventMask: INTEGER; VAR theEvent : EventRecord )
BOOLEAN;
FUNCTION OSEventAvail (eventMask: INTEGER; VAR theEvent: EventRecord)
BOOLEAN;
Event Manager, Operating System /Il-9/

<!-- source-page: 99 -->
## Page 99

Inside Macintosh
Setting the System Event Mask
PROCEDURE SetEventMask (theMask: INTEGER) ;
[Not in ROM]
Directly Accessing the Event Queue
FUNCTION GetEvQHdr : QHdrPtr;
[Not in ROM]
Assembly-Language Information
Constants
; Event codes
nullEvt
mButDwnEvt
mButUpEvt
keyDwnEvt
keyUpEvt
autoKeyEvt
updatEvt
diskinsertEvt
acti vateEvt
networkEvt
ioDrvrEvt
applEvt
app2Evt
app3Evt
app4Evt
.EQU
.EQU
.EQU
. EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
0
1
2
3
4
5
6
7
8
10
11
12
13
14
15
;null
;mouse-down
;mouse-up
;key-down
; key-up
;auto-key
; update; Toolbox only
;disk-inserted
;activate; Toolbox only
;network
; device driver
;application- defined
;appl ication-defined
;application- defined
; appl ication-defined
; Modifier flags i n event record
activeFlag
.EQU
0
;set if window being activated
btnState
.EQU
2
; set if mouse button up
cm::l.Key
.EQU
3
;set if Comnand key down
shiftKey
.EQU
4
; set if Shift key down
alpha Lock
.EQU
5
; set if Caps Lock key down
opti onKey
.EQU
6
; set if Option key down
; Result codes returned by PostEvent
noErr
evtNotEnb
.EQU
.EQU
0
1
;no err or (event posted)
;event type not designat ed in system
; event mask
1//-92 Event Manager, Operating System

<!-- source-page: 100 -->
## Page 100

Event Record Data Structure
evtNum
evtMessage
evtTicks
evtMouse
evtMeta
evtMBut
evtBlkSize
Event code (word)
Event message (long)
Ticks since startup (long)
Mouse location (point; long)
State of modifier keys (byte)
State of mouse button (byte)
Size in bytes of event record
Event Queue Entry Data Structure
qLink
qType
evtQWhat
evtQMessage
evtQWhen
evtQWhere
evtQMeta
evtQMBut
evtQBlkSize
Routines
Trap macro
PostEvent
FlushEvents
GetOSEvent
and
OSEventA vail
Variables
SysEvtMask
EventQueue
Pointer to next queue entry
Queue type (word)
Event code (word)
Event message (long)
Ticks since startup (long)
Mouse location (point; long)
State of modifier keys (byte)
State of mouse button (byte)
Size in bytes of event queue entry
On entry
AO: eventCode (word)
DO: eventMsg (long)
DO: low word: eventMask
high word: stopMask
AO: ptr to event record
theEvent
DO: eventMask (word)
System event mask (word)
Event queue header (10 bytes)
On exit
DO: result code (word)
DO: 0 or event code (word)
DO: 0 if non-null event,
-1 if null event (byte)
Summary
Event Manager, Operating System 111-93

<!-- source-page: 101 -->
## Page 101

Inside Macintosh
EVENT MANAGER, TOOLBOX
Constants
CONST
{ Event codes
nullEvent
O;
{null}
mouseDown
1;
{mouse down}
mouseUp
2;
{mouse up}
keyDown
3;
{key- down}
keyUp
4;
{key-up}
autoKey
5;
{auto- key}
updateEvt
6;
{update}
diskEvt
7;
{disk-inserted}
activateEvt
8;
{activate}
networkEvt
10;
{network}
driverEvt
11;
{device driver}
applEvt
12;
{application- defined}
app2Evt
13;
{application- defined}
app3Evt
14;
{application- defined}
app4Evt
15;
{application- defined}
{ Masks for keyboard event message }
charCodeMask = $000000FF;
keyCodeMask
$0000FFOO;
{character code }
{key code}
{ Masks for forming event mask }
mDownMask
mUpMask
keyDownMask
keyUpMask
autoKeyMask
updateMask
diskMask
activMask
networkMask
driverMask
applMask
app2Mask
app3Mask
app4Mask
everyEvent
2;
4;
8;
16;
32;
64;
128;
256;
1024;
2048;
4096;
8192;
16384;
- 32768;
-1;
{mouse down}
{mouse up}
{key-down}
{key-up }
{auto-key}
{update}
{disk-inserted}
{activate}
{network}
{device driver}
{application-defi ned}
{application- defined}
{application- defined}
{appl ication- defined}
{all event types}
III-94 Event Manager, Toolbox

<!-- source-page: 102 -->
## Page 102

{ Modifier flags in event record }
activeFlag
1;
{set if window being act ivated}
btnState
128; {set if mouse button up}
cmd.Key
256;
{set if Command key down}
shift Key
512 ;
{set if Shift key down}
alpha Lock
1024; {set if Caps Lock key down}
optionKey
2048; {set if Option key down}
Data Types
TYPE EventRecord = RECORD
what:
message:
when:
INTEGER;
LONG INT;
LONG INT;
where:
Point;
modifiers: INTEGER
END;
{event code }
{event message }
{ticks since startup}
{mouse location}
{modifier flags}
KeyMap
PACKED ARRAY[0 .. 127] OF BOOLEAN;
Routines
Accessing Events
FUNCTION GetNextEvent (eventMask: INTEGER; VAR theEvent:
EventRecord) :
BOOLEAN;
FUNCTION EventAvail
(eventMask : INTEGER; VAR theEvent :
Reading the Mouse
PROCEDURE GetMouse
FUNCTION
Button :
FUNCTION
StillDown
EventRecord) : BOOLEAN;
(VAR mouseLoc: Point);
BOOLEAN;
BOOLEAN;
FUNCTION
WaitMouseUp : BOOLEAN;
Reading the Keyboard and Keypad
PROCEDURE GetKeys (VAR theKeys: KeyMap);
Miscellaneous Routines
FUNCTION TickCount
FUNCTION GetDblTime
FUNCTION GetCaretTime
LONG INT;
LONG INT;
[Not in ROM]
LONG INT;
[Not in ROM]
Summary
Event Manager, Toolbox 111-95

<!-- source-page: 103 -->
## Page 103

Inside Macintosh
Event Message in Event Record
Event type
Keyboard
Activate, update
Disk-inserted
Mouse-down,
mouse-up, null
Network
Device driver
Applicationdefined
Event message
Character code and key code in low-order word
Pointer to window
Drive number in low-order word, File Manager result code in highorder word
Undefined
Handle to parameter block
See chapter describing driver
Whatever you wish
Assembly-Language Information
Constants
; Event codes
nullEvt
mButDwnEvt
mButUpEvt
keyDwnEvt
keyUpEvt
autoKeyEvt
updatEvt
disklnsertEvt
activateEvt
net workEvt
ioDrvrEvt
applEvt
app2Evt
app3Evt
app4Evt
.EQU
.EQU
. EQU
. EQU
. EQU
.EQU
.EQU
.EQU
.EQU
.EQU
. EQU
. EQU
. EQU
. EQU
. EQU
0
1
2
3
4
5
6
7
8
10
11
12
13
1 4
15
;null
;mouse-down
;mouse-up
;key-down
;key-up
;auto-key
;update
;disk-inserted
;activate
;network
;device driver
;application-defined
;application-de fined
;application-defined
;application-defined
; Modifier flags in event record
activeFlag
.EQU
0
;set if window being activated
btnState
.EQU
2
; set if mouse button up
cmdKey
.EQU
3
;set if Command key down
shif tKey
. EQU
4
; set if Shift key down
alphaLock
.EQU
5
; set if Caps Lock key d own
optionKey
.EQU
6
;set if Option key down
111-96 Event Manager, Toolbox

<!-- source-page: 104 -->
## Page 104

Summary
; Journaling mechanism Control call
jPlayCtl
. EQU
16
;journal in playback mode
jRecordCtl
.EQU
17
;journal in recording mode
jcTickCount
.EQU
0
;journal code for TickCount
jcGetMouse
.EQU
1
;journal code for GetMouse
jcButton
.EQU
2
;journal code for Button
jcGetKeys
.EQU
3
;journal code for Get Keys
jcEvent
. EQU
4
;journal code for GetNextEvent and EventAvail
Event Record Data Structure
evtNum
evtMessage
evtTicks
evtMouse
evtMeta
evtMBut
evtBlkSize
Variables
KeyThresh
KeyRepThresh
Window List
ScrDmpEnb
Ticks
Double Time
CaretTime
JournalRef
Journal Flag
Event code (word)
Event message (long)
Ticks since startup (long)
Mouse location (point; long)
State of modifier keys (byte)
State of mouse button (byte)
Size in bytes of event record
Auto-key threshold (word)
Auto-key rate (word)
0 if using events but not windows (long)
0 if GetNextEvent shouldn't process Command-Shift-number
combinations (byte)
Current number of ticks since system startup (long)
Double-click interval in ticks (long)
Caret-blink interval in ticks (long)
Reference number of journaling device driver (word)
Journaling mode (word)
Event Manager, Toolbox III-97

<!-- source-page: 105 -->
## Page 105

Inside Macintosh
FILE MANAGER
Constants
CONST { Flags in file information used by the Finder I
fHasBundle
8192;
{set if file has a bundle}
finvisible
16384; {set if file's icon is invisible)
fTrash
- 3;
{file is in Trash window)
fDesktop
-2;
{file is on desktop)
fDisk
0;
{file is in disk window)
{ Values for requesting read/write access }
fsCurPerm
fsRdPerm
O;
1;
{whatever is currently allowed)
{request to read only}
fsWrPerm
fsRdWrPerm
2;
3;
{request to write only)
{request to read and write)
{ Positioning modes }
fsAtMark
O;
{at current mark}
fsFromStart
1;
{offset relative to beginning of file}
fsFromLEOF
2;
{offset relative to logical end-of-file}
fsFromMark
3;
{offset rel ative to current mark )
rdVerify
64;
{add to above for read- verify}
Data Types
TYPE Finf o = RECORD
fdType :
fdCreator :
fdFlags :
fdLocation :
fdFldr :
OSType;
OSType;
INTEGER;
Point ;
INTEGER
{file type}
{file's creator}
{flags}
{file ' s location }
{file's window}
END;
ParamBl kType
(ioParam, fileParam, volumeParam,cntrlParam);
ParmBl kPtr
AParamBlockRec;
ParamBlockRec
RECORD
qLink :
QEl emPtr;
qType:
INTEGER;
ioTrap:
INTEGER;
ioCrrdAddr:
Ptr;
ioCompletion: ProcPtr;
ioResult:
OSErr;
ioNamePtr:
ioVRefNum:
I//-98 File Manager
StringPtr;
INTEGER;
{next queue entry}
{queue type)
{routine trap}
{routine address}
{completion routine)
{result code}
{volume or file name)
{volume reference or drive number}

<!-- source-page: 106 -->
## Page 106

CASE ParamBlkType OF
ioParam:
Summary
(ioRefNum:
INTEGER;
{path reference number }
ioVersNum :
SignedByte; {version number}
ioPermssn:
SignedByte; {read/write permission}
ioMisc:
Ptr;
{miscellaneous}
ioBuffer:
Ptr;
{data buffer}
ioReqCount: LONGINT;
{requested number of bytes }
ioActCount: LONGINT;
{actual number of bytes }
ioPosMode:
INTEGER;
{positioning mode and newli ne character }
ioPosOffset: LONGINT);
{positioning offset}
fileParam:
(ioFRefNum:
INTEGER;
{path reference number }
ioFVersNum:
SignedByte; {version number}
fillerl:
SignedByte; {not used}
ioFDirindex: INTEGER;
{s equence number of file }
ioFlAttrib:
SignedByte; {file attributes}
ioFlVersNum: SignedByte {version number}
ioFlFndrinfo: Finfo ;
{information used by the Finder}
ioFlNum:
LONGINT;
{file number}
ioFlStBlk:
INTEGER;
{first allocation b l ock of data fork}
ioFlLgLen:
LONGINT;
{logical end- of- fil e of data fork}
ioFlPyLen:
LONGINT;
{physical end-o f - file of data fork}
ioFlRStBlk:
INTEGER;
{first allocation block of resource
ioFlRLgLen :
LONGINT;
ioFlRPyLen:
LONG INT;
ioFlCrDat:
LONG INT;
ioFlMdDat:
LONGINT);
volumeParam :
(filler2:
LONG INT;
ioVolindex:
INTEGER;
ioVCrDate:
LONG INT;
ioVLsBkUp:
LONG INT;
ioVAtrb:
INTEGER;
ioVNmFls:
INTEGER;
ioVDirSt:
INTEGER;
ioVBlLn:
INTEGER;
ioVNmAlBlks: INTEGER;
ioVAlBlkSiz: LONGINT;
ioVClpSiz:
LONGINT;
ioAlBlSt:
INTEGER;
ioVNxtFNum:
LONGINT;
ioVFrBlk:
INTEGER);
cntrlParam:
( fork}
{logical end-of- file of resource fork }
{physical end- of-fil e of resource }
{ fork}
{date and time of creation}
(date and time of last modification }
{not used}
(volume index}
{date and time of initia lizati on }
{date and time of last backup }
{bit 15=1 if volume locked}
{number of files in directory}
{first block of directory }
{length of directory i n blocks}
{number of allocation blocks}
{size of allocation blocks}
{number of bytes to allocate }
{first allocation block i n block map }
{next unused file number }
{number of unused allocation blocks}
{used by Devi ce Manager}
END;
File Manager III-99

<!-- source-page: 107 -->
## Page 107

Inside Macintosh
VCB
RECORD
qLink:
qType:
vcbFlags:
vcbSigWord:
vcbCrDate:
vcbLsBkUp:
vcbAtrb:
vcbNmFls:
vcbDirSt:
vcbBlLn:
vcbNrnBlks:
QElemPtr;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
{next queue entry}
{queue type}
{bit 15=1 if dirty}
{always $D2D7}
{date and time of initialization}
{date and time of last backup}
{volume attributes}
vcbAlBl kSiz: LONGINT;
{number of files in directory}
{first block of directory}
{length of directory in blocks}
{number of allocation blocks}
{size of allocation blocks}
{number of bytes to all ocate}
vcbClpSiz:
vcbAlBl St:
vcbNxtFNum:
vcbFreeBks:
vcbVN:
vcbDrvNum
vcbDRefNum:
vcbFSID:
vcbVRefNum:
vcbMAdr:
vcbBufAdr:
vcbMLen:
vcbDirindex:
vcbDirBlk:
END;
DrvQEl = RECORD
qLink:
qType:
dQDrive:
dQRefNum:
dQFSID:
dQDrvSize :
END;
LONGINT;
INTEGER;
LONGINT;
{first allocation block in block map }
{next unused file number}
INTEGER;
{number of unused allocation blocks}
STRING[27]; {volume name}
INTEGER;
{drive number}
INTEGER;
INTEGER;
INTEGER;
Ptr;
Ptr;
INTEGER;
INTEGER;
INTEGER
QElemPtr;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER
{driver reference number}
{file-system identifier}
{volume reference number}
{pointer to block map}
{pointer to volume buffer}
{number of bytes in block map}
{used internally)
{used internally}
{next queue entry}
{queue type}
{drive number}
{driver reference number}
{file-system identifier }
{number of logical blocks}
High-Level Routines [Not in ROM]
Accessing Volumes
FUNCTION GetVInfo
FUNCTION GetVRefNum
FUNCTION GetVol
FUNCTION SetVol
FUNCTION FlushVol
FUNCTION UnmountVol
FUNCTION Eject
///-]{)() File Manager
(drvNum: INTEGER; volName: StringPtr; VAR vRefNum:
INTEGER; VAR freeBytes: LONGINT) : OSErr;
(pathRefNum: INTEGER; VAR vRefNum: INTEGER) : OSErr;
(volName : StringPtr; VAR vRefNum: INTEGER) : OSErr;
(volName : StringPtr; vRefNum: INTEGER)
OSErr;
(volName: StringPtr; vRefNum: INTEGER)
OSErr;
(volName : StringPtr; vRefNum: INTEGER)
OSErr;
(volName : StringPtr; vRefNum: INTEGER)
OSErr;

<!-- source-page: 108 -->
## Page 108

Summary
Accessing Files
FUNCTION Create
(fileName: Str255; vRefNum: INTEGER; creator: OS Type;
fileType: OSType)
: OSErr;
FUNCTION FSOpen
(fileName: Str255; vRefNum: INTEGER; VAR refNum:
INTEGER)
: OSErr;
FUNCTION OpenRF
(fileName: Str255; vRefNum: INTEGER; VAR refNum:
INTEGER) : OSErr;
FUNCTION FSRead
(r efNum: INTEGER; VAR count: LONGINT; buffPtr: Ptr)
OSErr;
FUNCTION FSWrite
(refNum: INTEGER; VAR count: LONGINT; buffPtr: Ptr)
OSErr;
FUNCTION GetFPos
(refNum: INTEGER; VAR filePos: LONGINT) : OSErr;
FUNCTION SetFPos
(refNum: INTEGER; posMode: INTEGER; posOff: LONGINT)
OSErr;
FUNCTION GetEOF
(refNum: INTEGER; VAR l ogEOF: LONGINT) : OSErr;
FUNCTION SetEOF
(refNum: INTEGER; logEOF: LONGINT) : OSErr;
FUNCTION Allocate (refNum: INTEGER; VAR count: LONGINT) : OSErr;
FUNCTION FSClose
(r efNum: INTEGER) : OSErr;
Changing Information About Files
FUNCTION GetFinfo (f ileName: Str255; vRefNum : INTEGER; VAR fndrinfo:
Finfo) : OSErr;
FUNCTION SetFinfo (fileName: Str255; vRefNum: INTEGER; fndrinfo: Finfo):
OSErr;
FUNCTION SetFLock (fileName: Str255; vRefNum: INTEGER) : OSErr;
FUNCTION RstFLock (fileName : Str255; vRefNum: INTEGER) : OSErr;
FUNCTION Rename
(oldName: Str255; vRefNum: INTEGER; newName : Str255)
OSErr;
FUNCTION FSDelete (fileName: Str255; vRefNum: INTEGER) : OSErr;
Low-Level Routines
Initializing the File 1/0 Queue
PROCEDURE FinitQueue;
Accessing Volumes
FUNCTION PBMountVol (paramBlock: ParmBlkPtr)
OSErr;
t-
16
ioResult
word
H
22
ioVRefNum
word
File Manager III-JOI

<!-- source-page: 109 -->
## Page 109

Inside Macintosh
FUNCTION PBGetVInfo (paramBlock: ParmBlkPtr; async: BOOLEAN)
~ 12
ioCompletion
pointer
f-
16
ioResult
word
H
18
ioNamePtr
pointer
H
22
ioVRefNum
word
~ 28
ioVollndex
word
f-
30
ioVGDate
long word
f-
34
ioVLsBkUp
long word
f-
38
ioVAtrb
word
f-
40
ioVNmAs
word
f-
42
ioVDirSt
word
f-
44
ioVBILn
word
f-
46
ioVNmAIBlks
word
f-
48
io v AlBlkSiz
long word
f-
52
ioVClpSiz
long word
f-
56
ioAIBISt
word
f-
58
ioVNxtFNum
long word
f-
62
ioVFrBlk
word
FUNCTION PBGetVol (paramBlock: ParmBlkPtr; a sync: BOOLEAN)
~ 12
ioCompletion
pointer
f-
16
ioResult
word
f-
18
ioNamePtr
pointer
f-
22
ioVRefNum
word
FUNCTION PBSetVol (paramBlock: ParmBlkPtr; async : BOOLEAN)
~ 12
ioCompletion
pointer
f-
16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
FUNCTION PBFlushVol (paramBlock: ParmBlkPtr; async : BOOLEAN)
~ 12
ioCompletion
pointer
f-
16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
FUNCTION PBUrunountVol
f-
16
ioResult
~ 18
ioNamePtr
~ 22
ioVRefNum
(paramBlock: ParmBlkPtr)
word
pointer
word
FUNCTION PBOffLine (paramBlock: ParmBlkPtr)
~ 12
ioCompletion
pointer
f-
16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
III-102 File Manager
OSErr;
OSErr;
OSErr;
OSErr;
OSErr;
OSErr;

<!-- source-page: 110 -->
## Page 110

FUNCTION PBEject (paramBlock: ParmBlkPtr)
~ 12
~ 16
~ 18
~ 22
ioCompletion
ioResult
ioNamePt
ioVRetNum
Accessing Files
pointer
word
pointer
word
OSErr;
FUNCTION PBCreate (paramBlock : ParmBlkPtr; async: BOOLEAN)
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 26
ioFVersNum
byte
FUNCTION PBOpen (par amBlock:
~ 12
ioCompletion
~ 16
ioResult
~ 18
ioNamePtr
~ 22
ioVRetNum
~ 24
ioRefNum
~ 26
ioVersNum
~ 27
ioPennssn
~ 28
ioMisc
ParmBlkPtr;
pointer
word
pointer
word
word
byte
byte
pointer
async: BOOLEAN)
FUNCTION PBOpenRF (paramBlock: ParmBlkPtr; a sync: BOOLEAN)
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 24
ioRetNum
word
~ 26
ioVersNum
byte
~ 27
ioPennssn
byte
~ 28
ioMisc
pointer
FUNCTION PBRead (paramBlock: ParmBlkPtr; async: BOOLEAN)
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 24
ioRetNum
word
~ 32
ioBuffer
pointer
~ 36
ioReqCount
longword
~ 40
ioActCount
long word
~ 44
ioPosMode
word
H
46
ioPosOffset
long word
Summary
OSErr;
OSErr;
OSErr;
OSErr;
File Manager ll/-/03

<!-- source-page: 111 -->
## Page 111

Inside Macintosh
FUNCTION PBWrite (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7
24
ioRefNum
word
---7
32
ioBuffer
pointer
---7
36
ioReqCount
long word
t-
40
ioActCount
long word
---7
44
ioPosMode
word
H
46
ioPosOffset
long word
FUNCTION PBGetFPos (pararnBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7 24
ioRefNum
word
t-
36
ioReqCount
long word
t-
40
ioActCount
long word
t-
44
ioPosMode
word
t-
46
ioPosOffset
long word
FUNCTION PBSetFPos (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7
24
ioRefNum
word
---7
44
ioPosMode
word
H
46
ioPosOffset
long word
FUNCTION PBGetEOF (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7
24
ioRefNum
word
t-
28
ioMisc
long word
FUNCTION PBSetEOF (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7
24
ioRefNum
word
---7
28
ioMisc
long word
FUNCTION PBAllocate (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7 24
ioRefNum
word
---7
36
ioReqCount
long word
t-
40
ioActCount
long word
FUNCTION PBFlushFile (pararnBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
---7
12
ioCompletion
pointer
t-
16
ioResult
word
---7
24
ioRefNum
word
III-104 File Manager

<!-- source-page: 112 -->
## Page 112

Summary
FUNCTION PBClose (pararnBlock: PannBlkPtr; async : BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 24
ioRefNurn
word
Changing Information About Files
FUNCTION PBGetFinf o (pararnBlock: ParrnBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
~ 16
ioResult
word
H
18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 24
ioFRefNum
word
~ 26
ioFVersNum
byte
~ 28
ioFDirlndex
word
~ 30
ioFIAttrib
byte
~ 31
ioFIVersNurn
byte
~ 32
ioFIFndrlnfo
16 bytes
~ 48
ioFINum
long word
~ 52
ioFIStBlk
word
~ 54
ioFILgLen
long word
~ 58
ioFlPyLen
long word
~ 62
ioFIRStBlk
word
~ 64
ioFIRLgLen
long word
~ 68
ioFIRPyLen
long word
~ 72
ioFICrDat
long word
~ 76
ioFIMdDat
long word
FUNCTION PBSetFinfo (pararnBlock: PannBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 26
ioFVersNum
byte
~ 32
ioFIFndrlnfo
16 bytes
~ 72
ioFICIDat
long word
~ 76
ioFIMdDat
long word
FUNCTION PBSetFLock (pararnBlock: PannBlkPtr; async : BOOLEAN)
OSEr r;
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 26
ioFVersNum
byte
FUNCTION PBRstFLock (pararnBlock: PannBlkPtr; async: BOOLEAN)
OSErr;
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 26
ioFVersNum
byte
File Manager III-105

<!-- source-page: 113 -->
## Page 113

Inside Macintosh
FUNCTION PBSetFVers (paramBlock: ParmBlkPtr; async : BOOLEAN)
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNurn
word
~ 26
ioVersNurn
byte
~ 28
ioMisc
byte
FUNCTION PBRename (paramBlock : ParmBlkPtr; async: BOOLEAN)
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNurn
word
~ 26
ioVersNurn
byte
~ 28
ioMisc
pointer
FUNCTION PBDelete (paramBlock: ParmBlkPtr; async: BOOLEAN)
~ 12
ioCompletion
pointer
~ 16
ioResult
word
~ 18
ioNamePtr
pointer
~ 22
ioVRefNum
word
~ 26
ioFVersNurn
byte
Accessing Queues [Not in ROM]
FUNCTION GetFSQHdr
FUNCTION GetVCBQHdr
FUNCTION GetDrvQHdr
Result Codes
Name
Value
QHdrPtr;
QHdrPtr;
QHdrPtr;
Meaning
OSErr;
OSErr;
OSErr;
badMDBErr
-60
Master directory block is bad; must reinitialize volume
bdNamErr
- 37
Bad file name or volume name (perhaps zero-length)
dirFulErr
- 33
File directory full
dskFulErr
-34
All allocation blocks on the volume are full
dupFNErr
-48
A file with the specified name and version number already exists
eofErr
-39
Logical end-of-file reached during read operation
extFSErr
-58
External file system; file-system identifier is nonzero, or path
reference number is greater than 1024
fBsyErr
-47
One or more files are open
fLckdErr
-45
File locked
fntErr
-43
File not found
fnOpnErr
- 38
File not open
III-106 File Manager

<!-- source-page: 114 -->
## Page 114

Name
fsRnErr
gfpErr
ioErr
memFullErr
no Err
noMacDskErr
nsDrvErr
nsvErr
opWrErr
paramErr
permErr
posErr
rfNumErr
unfoErr
vol OftLinErr
vol OnLinErr
vLckdErr
wrPerrnErr
wPrErr
Value
-59
-52
-36
-108
0
-57
-56
-35
-49
-50
-54
-40
-51
-42
-53
-55
-46
-61
-44
Meaning
Problem during rename
Error during GetFPos
IJO error
Not enough room in heap zone
No error
Volume lacks Macintosh-format directory
Summary
Specified drive number doesn't match any number in the drive queue
Specified volume doesn't exist
The read/write permission of only one access path to a file can allow
writing
Parameters don't specify an existing volume, and there's no default
volume
Attempt to open locked file for writing
Attempt to position before start of file
Reference number specifies nonexistent access path
Too many files open
Volume not on-line
Specified volume is already mounted and on-line
Volume is locked by a software flag
Read/write permission doesn't allow writing
Volume is locked by a hardware setting
Assembly-Language Information
Constants
; Flags in file information used by the Finder
fHasBundle
finvisible
.EQU
.EQU
; Flags in trap words
asnycTrpBit
noQueueBit
.EQU
.EQU
13
14
10
9
;set if file has a bundle
;set if file's icon is invisible
;set for an asynchronous call
;set for immediate execution
File Manager III-107

<!-- source-page: 115 -->
## Page 115

Inside Macintosh
; Values for requesting read/write access
fsCurPerm
.EQU
fsRdPerrn
.EQU
fsWrPerm
.EQU
fsRdWrPerrn
.EQU
0
1
2
3
;whatever is currently allowed
;request to read only
;request to write only
;request to read and write
; Positioning modes
fsAtMark
.EQU
fsFromStart
.EQU
fsFrornLEOF
.EQU
fsFromMark
.EQU
rdVerify
.EQU
0
1
2
3
64
;at current mark
;offset relative to beginning of file
;offset relative to logical end-of-file
;offset relative to current mark
;add to above for read- verify
Structure of File Information Used by the Finder
fdType
fdCreator
fdFlags
fdLocation
fdFldr
File type (long)
File's creator (long)
Flags (word)
File's location (point; long)
File's window (word)
Standard Parameter Block Data Structure
qLink
qType
ioTrap
ioCmdAddr
ioCompletion
ioResult
ioFileName
ioVNPtr
ioVRefNum
ioDrvNum
Pointer to next queue entry
Queue type (word)
Routine trap (word)
Routine address
Address of completion routine
Result code (word)
Pointer to file name (preceded by length byte)
Pointer to volume name (preceded by length byte)
Volume reference number (word)
Drive number (word)
1/0 Parameter Block Data Structure
ioRefNum
ioFileType
ioPermssn
ioNewName
ioLEOF
ioOwnBuf
ioNewType
ioBuffer
ioReqCount
ioActCount
ioPosMode
Path reference number (word)
Version number (byte)
Read/write permission (byte)
Pointer to new file or volume name for Rename
Logical end-of-file for SetEOF (long)
Pointer to access path buffer
New version number for SetFilType (byte)
Pointer to data buffer
Requested number of bytes (long)
Actual number of bytes (long)
Positioning mode and newline character (word)
III-108 File Manager

<!-- source-page: 116 -->
## Page 116

ioPosOffset
ioQElSize
Positioning offset (long)
Size in bytes of IJO parameter block
Structure of File Information Parameter Block
ioRefNum
ioFileType
ioFDirlndex
ioFlAttrib
ioFFlType
ioFlUsrWds
ioFFlNum
ioFlStBlk
ioFlLgLen
ioFlPyLen
ioFlRStBlk
ioFlRLgLen
ioFlRPyLen
ioFlCrDat
ioFlMdDat
ioFQElSize
Path reference number (word)
Version number (byte)
Sequence number of file (word)
File attributes (byte)
Version number (byte)
Information used by the Finder ( 16 bytes)
File number (long)
First allocation block of data fork (word)
Logical end-of-file of data fork (long)
Physical end-of-file of data fork (long)
First allocation block of resource fork (word)
Logical end-of-file of resource fork (long)
Physical end-of-file of resource fork (long)
Date and time of creation (long)
Date and time of last modification (long)
Size in bytes of file information parameter block
Structure of Volume Information Parameter Block
ioVollndex
ioVCrDate
ioVLsBkUp
ioVAtrb
ioVNmFls
ioVDirSt
ioVBlLn
io VNmAlBlks
io V AlBlkSiz
ioVClpSiz
ioAlBlSt
ioVNxtFNum
ioVFrBlk
ioVQElSize
Volume index (word)
Date and time of initialization (long)
Date and time of last backup (long)
Volume attributes (word)
Number of files in directory (word)
First block of directory (word)
Length of directory in blocks (word)
Number of allocation blocks on volume (word)
Size of allocation blocks (long)
Number of bytes to allocate (long)
First allocation block in block map (word)
Next unused file number (long)
Number of unused allocation blocks (word)
Size in bytes of volume information parameter block
Volume Information Data Structure
drSigWord
drCrDate
drLsBkUp
drAtrb
drNmFls
drDirSt
drBlLn
drNmAlBlks
drAlBlkSiz
Always $D2D7 (word)
Date and time of initialization (long)
Date and time oflast backup (long)
Volume attributes (word)
Number of files in directory (word)
First block of directory (word)
Length of directory in blocks (word)
Number of allocation blocks on volume (word)
Size of allocation blocks (long)
Summary
File Manager Ill-109

<!-- source-page: 117 -->
## Page 117

Inside Macintosh
drOpSiz
drAlBlSt
drNxtFNum
drFreeBks
drVN
Number of bytes to allocate (long)
First allocation block in block map (word)
Next unused file number (long)
Number of unused allocation blocks (word)
Volume name preceded by length byte (28 bytes)
File Directory Entry Data Structure
fl Flags
flTyp
flUsrWds
f!FlNum
flStBlk
f!LgLen
flPyLen
flRStBlk
flRLgLen
flRPyLen
flCrDat
flMdDat
flNam
Bit 7=1 if entry used; bit 0= 1 if file locked (byte)
Version number (byte)
Information used by the Finder (16 bytes)
File number (long)
First allocation block of data fork (word)
Logical end-of-file of data fork (long)
Physical end-of-file of data fork (long)
First allocation block of resource fork (word)
Logical end-of-file of resource fork (long)
Physical end-of-file of resource fork (long)
Date and time file of creation (long)
Date and time of last modification (long)
File name preceded by length byte
Volume Control Block Data Structure
qLink
qType
vcbFlags
vcbSigWord
vcbCrDate
vcbLsBkUp
vcbAtrb
vcbNmFls
vcbDirSt
vcbBlLn
vcbNmBlks
vcbAIBlkSiz
vcbClpSiz
vcbAIBlSt
vcbNxtFNum
vcbFreeBks
vcbVN
vcbDrvNum
vcbDRefNum
vcbFSID
vcbVRefNum
vcbMAdr
vcbBufAdr
vcbMLen
Pointer to next queue entry
Queue type (word)
Bit 15=1 if volume control block is dirty (word)
Always $D2D7 (word)
Date and time of initialization (word)
Date and time of last backup (long)
Volume attributes (word)
Number of files in directory (word)
First block of directory (word)
Length of directory in blocks (word)
Number of allocation blocks on volume (word)
Size of allocation blocks (long)
Number of bytes to allocate (long)
First allocation block in block map (word)
Next unused file number (long)
Number of unused allocation blocks (word)
Volume name preceded by length byte (28 bytes)
Drive number of drive in which volume is mounted (word)
Driver reference number of driver for drive in which volume is mounted
(word)
File-system identifier (word)
Volume reference number (word)
Pointer to volume block map
Pointer to volume buffer
Number of bytes in volume block map (word)
III-110 File Manager

<!-- source-page: 118 -->
## Page 118

File Control Block Data Structure
fcbFINum
fcbMdRByt
fcbTypByt
fcbSBlk
fcbEOF
fcbPLen
fcbCrPs
fcbVPtr
fcbBfAdr
File number (long)
Flags (byte)
Version number (byte)
First allocation block of file (word)
Logical end-of-file (long)
Physical end-of-file (long)
Mark (long)
Pointer to volume control block (long)
Pointer to access path buffer (long)
Drive Queue Entry Data Structure
qLink
qType
dQDrive
dQRefNum
dQFSID
dQDrvSize
Pointer to next queue entry
Queue type (word)
Drive number (word)
Driver reference number (word)
File-system identifier (word)
Number of logical blocks (word)
Macro Names
Pascal name
FlnitQueue
PB Mount Vol
PBGetVInfo
PBGetVol
PBSetVol
PBFlushVol
PBUnmountVol
PBOffLine
PB Eject
PBCreate
PB Open
PBOpenRF
PB Read
PB Write
PBGetFPos
PBSetFPos
PBGetEOF
PBSetEOF
PB Allocate
PBFlushFile
PB Close
PBGetFlnfo
PBSetFlnfo
PBSetFLock
PBRstFLock
Macro name
_lnitQueue
Mount Vol
-GetVollnfo
-GetVol
Set Vol
Flush Vol
Unmount Vol
OffLine
_Eject
Create
Open
-OpenRF
Read
Write
GetFPos
SetFPos
GetEOF
SetEOF
Allocate
FlushFile
-Close
- GetFilelnfo
SetFilelnfo
- SetFilLock
RstFilLock
Summary
File Manager /11-111

<!-- source-page: 119 -->
## Page 119

Inside Macintosh
PBSetFVer.;
PB Rename
PB Delete
Variables
FSQHdr
VCBQHdr
DefVCBPtr
FCBSPtr
DrvQHdr
ToExtFS
_ SetFilType
Rename
Delete
File 1/0 queue header (10 bytes)
Volume-control-block queue header (10 bytes)
Pointer to default volume control block
Pointer to file-control-block buffer
Drive queue header (10 bytes)
Pointer to external file system
II/-112 File Manager

<!-- source-page: 120 -->
## Page 120

FONT MANAGER
Constants
CONST { Font numbers )
systemFont
O;
{system font)
applFont
1;
{application font)
new York
2;
geneva
3;
monaco
4;
venice
5;
london
6;
a t hens
7 ;
sanFran
8;
toronto
9;
cairo
11;
losAngeles
12;
times
20;
helvetica
21;
courier
22;
symbol
23;
taliesin
24;
{ Special characters
commandMark
checkMark
diamondMark
appl eMark
$11;
$12 ;
$13;
$14;
{ Font types )
propFont
fixedFont
fontWid
Data Types
$9000;
$BOOO ;
$ACBO;
{Command key symbol)
{check mark)
{diamond symbol)
{apple symbol)
{proportional font)
{fixed- width font)
{font width data)
{font number)
{font size)
{character style)
Summary
TYPE FMinput =
PACKED RECORD
family :
size:
face :
needBits:
device:
numer:
denom:
INTEGER;
INTEGER;
Style;
BOOLEAN;
INTEGER;
Point;
Point
{TRUE if drawing)
{device- specific information)
{numerators of scaling factor s}
{denominators of scaling factors}
END;
Font Manager III-113

<!-- source-page: 121 -->
## Page 121

Inside Macintosh
FMOutPtr = "FMOutput;
FMOutput =
PACKED RECORD
errNum:
fontHandle:
bold:
i talic:
ulOffset:
ulShadow:
ulThick:
shadow:
extra:
ascent:
descent :
widMax:
leading:
unused:
numer:
denom:
END;
INTEGER;
Handle;
Byte;
Byte;
Byte;
Byte;
Byte;
Byte;
SignedByte;
Byte;
Byte;
Byte;
SignedByte;
Byte;
Point;
Point
{not used}
{handle to font record}
{bold factor }
{italic factor}
{underline offset}
{underline shadow}
{underline thickness}
{shadow factor}
{width of style }
{ascent}
{descent}
{maximum character width}
{leading}
{not used}
{numerators of scaling factors}
{denominators of scaling factors}
FontRec =
Routines
RECORD
fontType:
INTEGER;
{font type}
firstChar:
INTEGER;
{ASCII code of first character }
lastChar:
INTEGER;
{ASCII code of last character}
widMax:
INTEGER;
{maximum character width}
kernMax:
INTEGER;
{negative of maximum character kern}
nDescent:
INTEGER;
{negative of descent}
fRectWidth:
INTEGER;
{width of font rectangle }
fRectHeight: INTEGER;
{height of font rectangle}
owTLoc:
INTEGER;
{offset to offset/width table}
ascent:
INTEGER;
{ascent}
descent:
INTEGER;
{descent}
leading:
INTEGER;
{leading}
rowWords :
INTEGER;
{row width of bit image I 2)
{ bitimage:
ARRAY[l. . rowWords,1. .fRectHeight] OF INTEGER;
{bit image}
{ locTable:
ARRAY [firstChar .. lastChar+2] OF INTEGER;
{location table}
{ owTable:
ARRAY[firstChar .. lastChar+2] OF INTEGER;
{offset/width table}
END;
Initializing the Font Manager
PROCEDURE InitFonts;
111-114 Font Manager

<!-- source-page: 122 -->
## Page 122

Getting Font Information
PROCEDURE GetFontNarne (fontNum: INTEGER; VAR theName: Str255);
PROCEDURE GetFNum
(fontName: Str255; VAR theNum: INTEGER);
FUNCTION
RealFont
(fontNum: INTEGER; size: I NTEGER) : BOOLEAN;
Keeping Fonts in Memory
PROCEDURE SetFontLock (l ockFlag : BOOLEAN) ;
Advanced Routine
FUNCTI ON FMSwapFont (inRec: FMinput) : FMOutPt r ;
Assembly-Language Information
Constants
; Font numbers
sysFont
.EQU
appl Font
.EQU
newYork
.EQU
geneva
.EQU
monaco
.EQU
venice
.EQU
london
.EQU
a thens
.EQU
sanFran
.EQU
toronto
.EQU
cairo
.EQU
losAngeles
.EQU
times
.EQU
helvetica
.EQU
courier
.EQU
symbol
.EQU
ta l ies in
.EQU
0
l
2
3
4
5
6
7
8
9
11
12
20
21
22
23
24
; system font
; appl ication font
i Special characters
commandMark
checl<Mark
diarnondMark
appleMark
i Font types
propFont
.EQU
.EQU
.EQU
.EQU
.EQU
$11
$12
$13
$14
; Command key symbol
;check mark
;diamond symbol
;apple symbol
$9000 ;proportional font
Summary
Font Manager III-115

<!-- source-page: 123 -->
## Page 123

Inside Macintosh
fixedFont
fontWid
.EQU
$BOOO ;fixed-width font
.EQU
$ACBO ; font width data
; Control and Status call code
fMgrCtll
.EQU
8
;code used to get and modify font
; characterization table
Font Input Record Data Structure
fminFamily
fmlnSize
fmlnFace
fmlnNeedBits
fmlnDevice
fmlnNumer
fmlnDenom
Font number (word)
Font size (word)
Character style (word)
Nonzero if drawing (byte)
Device-specific information (byte)
Numerators of scaling factors (point; long)
Denominators of scaling factors (point; long)
Font Output Record Data Structure
fmOutFontH
fmOutBold
fmOutltalic
fmOutUlOffset
fmOutUlShadow
fmOutUlThick
fmOutShadow
fmOutExtra
fmOutAscent
fmOutDescent
fmOutWidMax
fmOutLeading
fmOutNumer
fmOutDenom
Handle to font record
Bold factor (byte)
Italic factor (byte)
Underline offset (byte)
Underline shadow (byte)
Underline thickness (byte)
Shadow factor (byte)
Width of style (byte)
Ascent (byte)
Descent (byte)
Maximum character width (byte)
Leading (byte)
Numerators of scaling factors (point; long)
Denominators of scaling factors (point; long)
Font Record Data Structure
fFontType
fFirstChar
fLastChar
fWidMax
fK.ernMax
tNDescent
fFRectWidth
fFRectHeight
tOWfLoc
fAscent
fDescent
fLeading
Font type (word)
ASCII code of first character (word)
ASCII code of last character (word)
Maximum character width (word)
Negative of maximum character kem (word)
Negative of descent (word)
Width of font rectangle (word)
Height of font rectangle (word)
Offset to offset/width table (word)
Ascent (word)
Descent (word)
Leading (word)
///-116 Font Manager

<!-- source-page: 124 -->
## Page 124

fRowWords
Row width of bit image I 2 (word)
Special Macro Names
Pascal name
GetFontName
Variables
ApFontlD
FScaleDisable
ROMFontO
Macro name
GetFName
Font number of application font (word)
Nonzero to disable scaling (byte)
Handle to font record for system font
Summary
Font Manager Ill-117

<!-- source-page: 125 -->
## Page 125

Inside Macintosh
INTERNATIONAL UTILITIES PACKAGE
Constants
CONST { Masks for currency format }
currSymLead
16;
{set if currency symbol leads)
currNegSym
32;
{set if minus sign for negative)
currTrailingZ
64;
{set if trailing decimal zeroes)
currLeadingZ
128; {set if l eading integer zero)
{ Order of short date elements
rrdy = 0;
dmy = 1;
ymd = 2;
{ Masks for
{month day year)
{day month year)
{year month day)
short date format
dayLdingZ
32;
{set if leading zero for day}
mntLdingZ
64;
{set if leading zero for month}
century
128; {set if century included)
{ Masks for time format }
secLeadingZ
32;
{set if leading zero for seconds)
rninLeadingZ
64;
{set if leading zero for minutes}
hrLeadingZ
128; {set if leading zero for hours}
{ High-order byte of version information }
verUS
0;
verFrance
l;
verBritain
2;
verGermany
3;
veritaly
4;
verNetherlands
5;
verBelgiumLux
6;
verSweden
7;
verSpain
8;
verDenmark
9;
verPortugal
10;
verFrCanada
11;
verNorway
12;
verisrael
13;
verJapan
14;
verAustralia
15;
verArabia
16;
verFinland
17;
111-118 International Utilities Package

<!-- source-page: 126 -->
## Page 126

Summary
verFrSwiss
18;
verGrSwiss
19;
ver Greece
20;
veri celand
21;
verMalta
22;
verCyprus
23;
verTurkey
24;
verYugoslavia
25;
Data Types
TYPE IntlOHndl
IntlOPtr
"IntlOPtr;
"IntlORec;
IntlORec
PACKED RECORD
decirnalPt :
thousSep:
listSep:
currSyml:
currSym2:
currSym3:
currFmt:
dateOrder:
shrtDateFmt:
dateSep:
timeCycle:
timeFmt :
mornStr:
eveStr:
timeSep:
timelSuff :
time2Suff:
time3Suff :
time4Suff:
time5Suff:
time6Suff:
time7Suff:
time8Suff:
metricSys:
intlOVers:
END;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
{decimal point character}
{thousands separator}
{list separator}
{currency symbol}
Byte; {currency format }
Byte; {order of short date elements }
Byte; {short date format}
CHAR;
{date separator}
Byte; {0 if 24- hour cycle, 255 if 12- hour }
Byte; {time format}
PACKED ARRAY[ l . . 4] OF CHAR;
{trailing string for f irst 12-hour cycl e }
PACKED ARRAY[l .. 4] OF CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
CHAR;
{trailing string for last 12- hour cycle }
{time separator}
{trai ling string for 24- hour cycl e }
Byte;
(255 if metric, 0 if not }
INTEGER {version information }
International Utilities Package III-119

<!-- source-page: 127 -->
## Page 127

Inside Macintosh
IntllHndl = " IntllPtr;
IntllPtr = " IntllRec;
IntllRec
PACKED RECORD
days :
months:
ARRAY[l . . 7] OF STRING[15 ] ;
ARRAY [l . . 12] OF STRING[l5];
{day names}
{month names}
suppressDay: Byte;
lngDateFmt:
Byte;
dayLeadingO: Byte;
{0 for day name , 255 for none }
{order of long date elements }
{255 for leading 0 i n day number}
{length for abbreviating names}
ARRAY[l .. 4] OF CHAR;
{strings
ARRAY[l .. 4] OF CHAR;
{ for
}
ARRAY[l .. 4] OF CHAR;
{long}
ARRAY[l .. 4] OF CHAR;
{date }
ARRAY [l . . 4] OF CHAR;
{ format}
abbrLen :
stO:
stl :
st2:
st3:
st4:
intllVers:
localRtn:
END;
Byte;
PACKED
PACKED
PACKED
PACKED
PACKED
INTEGER; {version i nformation}
INTEGER
{routine for l ocalizing string
{ comparison; actually may be }
{ l onger than one integer }
DateForm = (shortDate, longDate , abbrevDate);
Routines
PROCEDURE
PROCEDURE
PROCEDURE
PROCEDURE
FUNCTION
FUNCTION
PROCEDURE
FUNCTION
FUNCTION
FUNCTION
FUNCTION
I UDateString
IUDatePString
IUTimeString
I UTimePString
IUMetric :
IUGetintl
IUSetintl
IUCompString
IUMagString
IUEqualString
IUMagIDString
(dateTime: LONGINT; form : DateForm; VAR result:
Str255);
(dateTime: LONGINT; form: DateForm; VAR result:
Str255; intlParam: Handle);
(dateTime: LONGINT; wantSeconds : BOOLEAN; VAR
result : Str255);
(dateTime: LONGINT; wantSeconds : BOOLEAN; VAR
result: Str255; intl Param : Hand l e);
BOOLEAN;
(theID: INTEGER) : Handle;
(refNurn: INTEGER; theI D: I NTEGER; intlParam:
Handle);
(aStr,bStr:
(aPtr, bPtr:
(aStr,bStr:
(aPtr,bPtr:
Str 255) : INTEGER;
[NotinROM]
Ptr; aLen,bLen: INTEGER)
: I NTEGER;
Str255) : INTEGER;
[NotinROM]
Ptr; aLen,bLen: I NTEGER)
: I NTEGER;
III-120 International Utilities Package

<!-- source-page: 128 -->
## Page 128

Assembly-Language Information
Constants
; Masks for currency format
currSymLead
.EQU
currNegSym
.EQU
currTrailingZ .EQU
currLeadingZ
.EQU
i Order of short date
mdy
dmy
yrrd
.EQU
.EQU
.EQU
16
;set if currency symbol leads
32
;set if minus sign for negative
64
;set if trail ing decimal zeroes
128
;set if leadi ng integer zero
elements
0
1
2
;month day year
;day month year
;year month day
; Masks for short date format
dayLdingZ
mntLdingZ
century
.EQU
.EQU
.EQU
32
;set if l eading zero for day
64
;set if l eading zero for month
128
;set if century included
; Masks for time format
secLeadingZ
.EQU
32
;set if leading zero for seconds
minLeadingZ
.EQU
64
;set if leading zero for minutes
hrLeadingZ
.EQU
128
;set if leading zero for hours
i High-order byte of version information
verUS
.EQU
0
verFrance
.EQU
1
verBritai n
.EQU
2
verGermany
.EQU
3
veritaly
.EQU
4
verNetherlands
.EQU
5
verBelgiumLux
.EQU
6
verSweden
.EQU
7
verSpain
.EQU
8
verDenmark
.EQU
9
verPortugal
.EQU
10
verFrCanada
.EQU
11
verNorway
.EQU
12
verisrael
.EQU
13
verJapan
.EQU
14
verAustralia
.EQU
15
verArabia
.EQU
16
verFinland
.EQU
17
verFrSwiss
.EQU
18
verGrSwiss
.EQU
19
Swnmary
International Utilities Package 111-121

<!-- source-page: 129 -->
## Page 129

Inside Macintosh
verGreece
.EQU
20
vericeland
.EQU
21
verMalta
.EQU
22
verCyprus
.EQU
23
verTurkey
.EQU
24
verYugoslavia
.EQU
25
; Date form for IUDateString and IUDatePString
shortDate
longDate
abbrevDate
.EQU
.EQU
.EQU
0
1
2
;short form of date
;long form of date
;abbreviated long form
; Routine selectors
iuDateString
.EQU
0
iuTimeString
.EQU
2
iuMetric
.EQU
4
iuGetintl
.EQU
6
iuSetintl
.EQU
8
iuMagString
.EQU
10
iuMagIDString .EQU
12
iuDatePString .EQU
14
iuTimePString .EQU
16
International Resource O Data Structure
decimalPt
thousSep
listSep
currSym
currFmt
dateOrder
shrtDateFmt
dateSep
timeCycle
timeFmt
momStr
eveStr
timeSep
timeSuff
metricSys
intlOVers
Decimal point character (byte)
Thousands separator (byte)
List separator (byte)
Currency symbol (3 bytes)
Currency format (byte)
Order of short date elements (byte)
Short date format (byte)
Date separator (byte)
0 if 24-hour cycle, 255 if 12-hour (byte)
Time format (byte)
Trailing string for first 12-hour cycle (long)
Trailing string for last 12-hour cycle (long)
Time separator (byte)
Trailing string for 24-hour cycle (8 bytes)
255 if metric, 0 if not (byte)
Version information (word)
International Resource 1 Data Structure
days
months
suppressDay
lngDateFmt
Day names (112 bytes)
Month names (192 bytes)
0 for day name, 255 for none (byte)
Order of long date elements (byte)
III-122 International Utilities Package

<!-- source-page: 130 -->
## Page 130

day LeadingO
abbrLen
stO
stl
st2
st3
st4
intll Vers
localRtn
255 for leading 0 in day number (byte)
Length for abbreviating names (byte)
Strings for long date format (longs)
Version information (word)
Comparison localization routine
Summary
Trap Macro Name
Pack6
International Utilities Package !II-123

<!-- source-page: 131 -->
## Page 131

Inside Macintosh
MEMORY MANAGER
Constants
CONST { Result codes }
memFullErr
rnemLockedErr
-108 ;
-117;
{not enough room in heap zone}
{block is locked}
rnemPurErr
rnemWZErr
nilHandleErr
-112;
-111;
-109;
{attempt to purge a locked block}
{attempt to operate on a free bl ock}
{NIL master pointer}
noErr
0;
{no error}
Data Types
TYPE SignedByte
Byte
- 128 .. 127;
Ptr
Handle
0 .. 255;
"SignedByte;
"Ptr;
Str255
StringPtr
StringHandle
STRING[255] ;
"Str255;
"StringPtr;
ProcPtr = Ptr;
Fixed = LONGINT;
Size
LONGINT;
THz
"Zone;
Zone
RECORD
bkLim:
Ptr;
purgePtr:
Ptr;
hFstFree:
Ptr;
zcbFree :
LONGINT;
gzProc:
ProcPtr;
moreMast :
INTEGER;
flags:
INTEGER;
cntRel:
INTEGER;
maxRel:
INTEGER;
cntNRel:
INTEGER;
maxNRel :
INTEGER;
cntEmpty:
INTEGER;
cntHandles :
INTEGER;
minCBFree :
LONGINT;
purgeProc:
ProcPtr;
sparePtr:
Ptr;
allocPtr:
Ptr;
heapData:
INTEGER
END;
III-124 Memory Manager
{zone trailer block}
{used internally}
{first free master pointer}
{number of free bytes}
{grow zone function}
{master pointers to allocate }
{used internally}
{not used}
{not used}
{not used}
{not used}
{not used}
{not used}
{not used}
{purge warning procedure}
{used internally}
{used internally}
{first usable byte in zone }

<!-- source-page: 132 -->
## Page 132

Routines
Initialization and Allocation
(startPtr: Ptr);
PROCEDURE InitApplZone;
PROCEDURE SetApplBase
PROCEDURE InitZone
(pGrowZone : ProcPtr; cMoreMasters : INTEGER;
limitPtr,startPtr: Ptr);
FUNCTION
GetApplLimit
PROCEDURE SetApplLimit
PROCEDURE MaxApplZone;
PROCEDURE MoreMasters;
Heap Zone Access
Ptr;
[Not in ROM]
(zoneLimit: Ptr);
[Not in ROM]
FUNCTION
GetZone :
THz;
PROCEDURE SetZone
(hz: THz);
FUNCTION
SystemZone
THz;
[NotinROM]
FUNCTION
ApplicZone : THz;
[NotinROM]
Allocating and Releasing Relocatable Blocks
FUNCTION
New Handle
(logicalSize: Size) : Handle;
PROCEDURE DisposHandle
(h: Handle);
FUNCTION
GetHandleSize (h: Handle)
Size;
PROCEDURE SetHandleSize (h: Handle; newSize: Size);
FUNCTION
HandleZone
(h: Handle)
: THz;
FUNCTION
RecoverHandle
(p: Ptr) : Handle;
PROCEDURE ReallocHandle
(h: Handle; logicalSize: Size);
Allocating and Releasing Nonrelocatable Blocks
FUNCTION
NewPtr
(logicalSize: Size)
: Ptr;
PROCEDURE DisposPtr (p: Ptr);
FUNCTION GetPtrSize (p: Ptr) : Size;
PROCEDURE SetPtrSize (p: Ptr; newSize: Size);
FUNCTION
PtrZone
(p: Ptr) : THz;
Freeing Space in the Heap
FUNCTION
FreeMem :
LONGINT;
FUNCTION
MaxMem
(VAR grow: Size)
: Size;
FUNCTION
CompactMem (cbNeeded: Size) : Size;
PROCEDURE ResrvMem
(cbNeeded: Size);
PROCEDURE PurgeMem
(cbNeeded: Size) ;
PROCEDURE EmptyHandle (h: Handle);
Summary
Memory Manager 111-125

<!-- source-page: 133 -->
## Page 133

Inside Macintosh
Properties of Relocatable Blocks
PROCEDURE HLock
PROCEDURE HUnlock
PROCEDURE HPurge
PROCEDURE HNoPurge
(h: Handle);
(h : Handle) ;
(h: Handle);
(h: Handle);
Grow Zone Operations
PROCEDURE SetGrowZone
(growZone: ProcPtr);
FUNCTION
GZSaveHnd :
Handle;
[NotinROM]
Miscellaneous Routines
PROCEDURE BlockMove
FUNCTION
TopMern :
PROCEDURE MoveHHi
FUNCTION MernError
(sourcePtr,destPtr: Ptr; byteCount : Size);
Ptr;
[Not in ROM]
(h: Handle);
[NotinROM]
OSErr;
[Not in ROM]
Grow Zone Function
FUNCTION MyGrowZone (cbNeeded: Size) : LONGINT;
Assembly-Language Information
Constants
; Values for tag byte of a block header
tyBkFree
tyBkNRel
tyBkRel
.EQU
.EQU
.EQU
0
1
2
;free block
;nonrelocatable block
;relocatable block
; Flags for the high-order byte of a mas ter pointer
lock
purge
resourc
; Result codes
memFullErr
mernLockedErr
memPurErr
memWZErr
nilHandleErr
noErr
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
///-126 Memory Manager
7
6
5
-108
-117
-112
-111
-109
0
;lock bit
;purge bit
;resource bit
;not enough room in heap zone
;block is locked
;attempt to purge a locked block
;attempt to operate on a free block
;NIL master pointer
;no error

<!-- source-page: 134 -->
## Page 134

Zone Record Data Structure
bk.Lim
hFstFree
zcbFree
gzProc
mAllocCnt
purgeProc
heapData
Pointer to zone trailer block
Pointer to first free master pointer
Number of free bytes (long)
Address of grow zone function
Master pointers to allocate (word)
Address of purge warning procedure
First usable byte in zone
Block Header Data Structure
tag BC
handle
blkData
Tag byte and physical block size (long)
Relocatable block: relative handle
Nonrelocatable block: zone pointer
First byte of block contents
Parameter Block Structure for lnitZone
startPtr
limitPtr
cMoreMasters
pGrowZone
Routines
Trap macro
_InitApplZone
_ SetApplBase
InitZone
_ SetApplLimit
MoreMasters
GetZone
SetZone
New Handle
_ DisposHandle
Pointer to first byte in zone
Pointer to first byte beyond end of zone
Number of master pointers for zone (word)
Address of grow zone function
On entry
AO: startPtr (ptr)
AO: ptr to parameter block
0 startPtr (ptr)
4 limitPtr (ptr)
8 cMoreMasters (word)
10 pGrowZone (ptr)
AO: zoneLimit (ptr)
AO: hz (ptr)
DO: logicalSize (long)
AO: h (handle)
On exit
DO: result code (word)
DO: result code (word)
DO: result code (word)
DO: result code (word)
AO: function result (ptr)
DO: result code (word)
DO: result code (word)
AO: function result (handle)
DO: result code (word)
DO: result code (word)
Summary
Memory Manager lll-127

<!-- source-page: 135 -->
## Page 135

Inside Macintosh
Trap macro
On entry
On exit
GetHandleSize
AO: h (handle)
DO: if >=0, function result (long)
if <0, result code (word)
_ SetHandleSize
AO: h (handle)
DO: result code (word)
DO: newSize (long)
HandleZone
AO: h (handle)
AO: function result (ptr)
DO: result code (word)
RecoverHandle
AO: p (ptr)
AO: function result (handle)
DO: unchanged
ReallocHandle
AO: h (handle)
DO: result code (word)
DO: logicalSize (long)
NewPtr
DO: logicalSize (long)
AO: function result (ptr)
DO: result code (word)
_DisposPtr
AO: p (ptr)
DO: result code (word)
GetPtrSize
AO: p (ptr)
DO: if >=0, function result (long)
if <0, result code (word)
SetPtrSize
AO: p (ptr)
DO: result code (word)
DO: newSize (long)
PtrZone
AO: p (ptr)
AO: function result (ptr)
DO: result code (word)
FreeMem
DO: function result (long)
MaxMem
DO: function result (long)
AO: grow (long)
_ CompactMem
DO: cbNeeded (long)
DO: function result (long)
ResrvMem
DO: cbNeeded (long)
DO: result code (word)
_PurgeMem
DO: cbNeeded (long)
DO: result code (word)
_Empty Handle
AO: h (handle)
AO: h (handle)
DO: result code (word)
HLock
AO: h (handle)
DO: result code (word)
HUnlock
AO: h (handle)
DO: result code (word)
_HPurge
AO: h (handle)
DO: result code (word)
_HNoPurge
AO: h (handle)
DO: result code (word)
SetGrowZone
AO: growZone (ptr)
DO: result code (word)
BlockMove
AO: sourcePtr (ptr)
DO: result code (word)
A 1: destPtr (ptr)
DO: byteCount (long)
///-128 Memory Manager

<!-- source-page: 136 -->
## Page 136

Variables
DefltStack
MinStack
MemTop
ScrnBase
BufPtr
CurrentA5
CurStackBase
ApplLimit
Heap End
ApplZone
SysZone
TheZone
GZRootHnd
Default space allotment for stack (long)
Minimum space allotment for stack (long)
Summary
Address of end of RAM (on Macintosh XL, end of RAM available to
applications)
Address of main screen buffer
Address of end of jump table
Address of boundary between application globals and application parameters
Address of base of stack; start of application globals
Application heap limit
Address of end of application heap zone
Address of application heap zone
Address of system heap zone
Address of current heap zone
Handle to relocatable block not to be moved by grow zone function
Memory Manager 1/1-129

<!-- source-page: 137 -->
## Page 137

Inside Macintosh
MENU MANAGER
Constants
CONST { Value indicating item has no mark }
noMark = 0;
{ Messages to menu definition procedure
{draw the menu}
mDrawMsg
mChooseMsg
mSizeMsg
O;
1;
2;
{tell which item was chosen and highlight i t}
{calculate the menu's dimensions}
{ Resource ID of standard menu definition procedure }
textMenuProc = O;
Data Types
TYPE MenuHandle
MenuPtr
Menuinfo
Routines
"MenuPtr;
"Menuinfo;
RECORD
menuID:
menuWidth:
menuHeight:
menuProc:
enableFlags:
menuData:
END;
Initialization and Allocation
INTEGER;
INTEGER;
INTEGER;
Handle;
LONGINT;
Str255
{menu ID}
{menu width in pixels}
{menu height in pixels}
{menu definition procedure}
{te l ls if menu or items are
{ enabled}
{menu title (and other data)}
PROCEDURE InitMenus;
FUNCTION
NewMenu
FUNCTION
GetMenu
PROCEDURE DisposeMenu
(menuID: INTEGER; menuTitle : Str255)
(resourceID: INTEGER) : MenuHandle;
(theMenu: MenuHandle);
MenuHandle;
Forming the Menus
PROCEDURE AppendMenu
PROCEDURE AddResMenu
PROCEDURE InsertResMenu
111-130 Menu Manager
(theMenu: MenuHandle; data : Str255);
(theMenu: MenuHandle; theType: ResType);
(theMenu : MenuHandle; theType : ResType;
afteritem: INTEGER);

<!-- source-page: 138 -->
## Page 138

Summary
Forming the Menu Bar
PROCEDURE InsertMenu
(theMenu: MenuHandle; beforeID: INTEGER);
PROCEDURE DrawMenuBar;
PROCEDURE DeleteMenu
(menuID : INTEGER);
PROCEDURE ClearMenuBar;
FUNCTION
GetNewMBar
(menuBarID : INTEGER)
FUNCTION
GetMenuBar : Handle;
PROCEDURE SetMenuBar
(menuList: Handle);
Choosing From a Menu
Handle ;
FUNCTION
MenuSelect (startPt: Point) : LONGI NT;
FUNCTION
MenuKey
(ch: CHAR)
: LONGINT;
PROCEDURE HiliteMenu (menuID : INTEGER);
Controlling the Appearance of Items
PROCEDURE Set Item
(theMenu: MenuHandle; item : INTEGER;
Str255 );
PROCEDURE Getitem
(theMenu: MenuHandle; item: INTEGER;
itemString : Str255);
PROCEDURE Disable Item (theMenu : MenuHandle; item: INTEGER);
PROCEDURE Enable Item
(theMenu: MenuHandle; item: INTEGER);
PROCEDURE Checkitem
(t heMenu : MenuHandle; item: INTEGER;
BOOLEAN);
PROCEDURE SetitemMark (theMenu: MenuHandle; item: INTEGER;
CHAR);
PROCEDURE GetitemMark (theMenu: MenuHandle; item: INTEGER;
markChar: CHAR);
PROCEDURE Setitemicon
(t heMenu : MenuHandle; item: INTEGER;
PROCEDURE Getitemicon (theMenu : MenuHandle; item : I NTEGER;
Byte);
PROCEDURE SetitemStyle (theMenu: MenuHandle; item: INTEGER;
Style);
PROCEDURE GetitemStyle (theMenu : MenuHandle; item: INTEGER;
Style);
Miscellaneous Routines
PROCEDURE CalcMenuSize (theMenu : MenuHandle) ;
FUNCTION
CountMitems
(theMenu: MenuHandle)
: INTEGER;
FUNCTION
GetMHandle
(menu ID : INTEGER)
: MenuHandle;
PROCEDURE FlashMenuBar (menu ID: INTEGER);
PROCEDURE SetMenuFlash (count: INTEGER);
itemString:
VAR
checked:
markChar:
VAR
icon : Byte);
VAR icon:
chStyle:
VAR chStyle:
Menu Manager 11/-131

<!-- source-page: 139 -->
## Page 139

Inside Macintosh
Meta-Characters for AppendMenu
Meta-character
or Return
/\
<
I
(
Usage
Separates multiple items
Followed by an icon number, adds that icon to the item
Followed by a character, marks the item with that character
Followed by B, I, U, 0, or S, sets the character style of the item
Followed by a character, associates a keyboard equivalent with the item
Disables the item
Menu Definition Procedure
PROCEDURE MyMenu
(message: INTEGER; theMenu: MenuHandle; VAR menuRect :
Rect; hitPt: Point; VAR whichitem: I NTEGER);
Assembly-Language Information
Constants
; Value indicating item has no mark
noMark
.EQU
0
; Messages to menu definition procedure
mDrawMsg
rrChooseMsg
mSizeMsg
.EQU
.EQU
.EQU
0
1
2
;draw the menu
;tell which item was chosen and highlight it
; calculate the menu·' s dimensions
; Resource ID of standard menu definition procedure
textMenuProc
.EQU
0
Menu Record Data Structure
menuID
menu Width
menuHeight
menuDetHandle
menuEnable
menuData
menuBlkSize
III-132 MenuManager
Menu ID (word)
Menu width in pixels (word)
Menu height in pixels (word)
Handle to menu definition procedure
Enable flags (long)
Menu title (preceded by length byte) followed by data defining the items
Size in bytes of menu record except menuData field

<!-- source-page: 140 -->
## Page 140

Summary
Special Macro Names
Pascal name
DisposeMenu
Getltemlcon
GetltemMark
GetltemStyle
GetMenu
Seti tern Icon
SetltemMark
SetltemStyle
SetMenuFlash
Variables
MenuList
MBarEnable
MenuHook
MBarHook
TheMenu
MenuFlash
MBarHook routine
On entry
On exit
Macro name
_DisposMenu
_ Getltmlcon
GetltmMark
_ GetltmStyle
GetRMenu
Setltmlcon
SetltmMark
_ SetltmSty le
SetMFlash
Handle to current menu list
Nonzero if menu bar belongs to a desk accessory (word)
Address of routine called repeatedly during MenuSelect
Address of routine called by MenuSelect before menu is drawn (see below)
Menu ID of currently highlighted menu (word)
Count for duration of menu item blinking (word)
stack: pointer to menu rectangle
DO: 0 to continue MenuSelect
1 to abort MenuSelect
MenuManager III-133

<!-- source-page: 141 -->
## Page 141

Inside Macintosh
PACKAGE MANAGER
Constants
CONST { Resource IDs for packages }
dskinit
2;
stdFile
3;
flPoint
4;
trFunc
5;
intUtil
6;
bdConv
7;
Routines
PROCEDURE I nitPack
PROCEDURE InitAllPacks;
{Di sk Initialization}
{Standard File}
{Floating-Point Arithmetic}
{Transcendental Functions }
{International Utilities}
{Binary-Decimal Conversion}
(packID : INTEGER);
Assembly-Language Information
Constants
; Resource IDs for packages
dskinit
.EQU
2
; Disk Initialization
stdFile
.EQU
3
;Standard File
flPoint
.EQU
4
;Floating-Point Arithmetic
trFunc
.EQU
5
;Transcendental Functions
intUtil
.EQU
6
;International Utilities
bdConv
.EQU
7
;Binary-Decimal Conversion
Trap Macros for Packages
Disk Initialization
Standard File
Floating-Point Arithmetic
Transcendental Functions
International Utilities
Binary-Decimal Conversion
III-134 PackageManager
Pack2
Pack3
Pack4
Pack5
-Pack6
Pack7
(synonym:
FP68K)
(synonym: .= Elems68K)

<!-- source-page: 142 -->
## Page 142

•
PRINTING MANAGER
Constants
CONST { Printing methods
bDraftLoop
bSpoolLoop
0;
l;
{draft printing}
{spool printing}
{ Printer specification in prStl field of print record }
bDevCitoh
bDevLaser
1;
3;
{Imagewriter printer}
{LaserWriter printer}
{ Maximum number of pages in a spool file
iPFMaxPgs = 128;
{ Result codes
no Err
iPrSavPFil
controlErr
iIOAbort
iMemFullErr
iPrAbort
O;
-1;
-17;
-27;
-108;
128;
{no error}
{saving spool file}
{unimplemented control instruction}
{I/0 abort error}
{not enough room in heap zone}
{application or user requested abort}
{ PrCtlCall parameters
iPrDevCtl
7;
{printer control}
lPrReset
$00010000;
{reset printer}
lPrLineFeed
$00030000;
{carriage return only}
lPrLFSixth
$0003FFFF;
{standard 1/6-inch line feed}
lPrPageEnd
$00020000;
{end page}
iPrBitsCtl
4;
{bit map printing}
lScreenBits
0;
{default for printer}
lPaintBits
1;
{square dots (72 by 72)}
iPrIOCtl
5;
{text streaming}
{ Printer Driver information }
sPrDrvr
iPrDrvrRef
'.Print';
-3;
{Printer Driver resource name}
{Printer Driver reference number}
Summary
Printing Manager lll-135

<!-- source-page: 143 -->
## Page 143

Inside Macintosh
Data Types
TYPE TPPrPort
TPrPort
"TPrPort;
RECORD
gPort: GrafPort;
{grafPort to draw in}
{more fields for internal use}
THPrint
TPPrint
TPrint
END;
"TPPrint;
"TPrint;
RECORD
iPrVersion :
prinfo:
rPaper:
prStl :
prinfoPT:
prXInfo:
prJob:
printX:
INTEGER;
{Printing Manager version}
TPrinfo;
{printer information subrecord}
Rect;
{paper rectangle}
TPrStl ;
{additional device information}
TPrinfo;
{used i nternally}
TPrXInfo; {additional device information}
TPrJob;
{job subrecord}
ARRAY[l .. 19) OF INTEGER
{not used}
END;
TPrinfo
RECORD
iDev:
INTEGER;
iVRes:
INTEGER;
iHRes:
INTEGER;
rPage: Rect
{used internally}
{vertical resolution of printer}
{horizontal resolution of printer}
{page rectangle}
END;
TPrJob =
RECORD
iFstPage:
iLstPage:
iCopies :
bJDocLoop :
fFromUsr:
pidleProc :
pFileName:
iFileVol :
INTEGER;
INTEGER;
INTEGER;
SignedByte;
BOOLEAN;
ProcPtr;
StringPtr;
INTEGER;
bFileVers : SignedByte;
bJobX:
SignedByte
END;
TPrStl =
RECORD
{first page to print}
{last page to print}
{number of copies}
{printing method}
{used internally}
{background procedure}
{spool file name }
{spool file volume reference number}
{spool file version number}
{used internal ly}
wDev: INTEGER;
{high byte specifies device}
{more fields for internal use}
END;
ll/-136 Printing Manager

<!-- source-page: 144 -->
## Page 144

Summary
TPrXInfo
RECORD
iRowBytes: INTEGER;
{used internally}
iBandV:
INTEGER;
{used internally}
iBand.H:
INTEGER;
{used internally}
iDevBytes: INTEGER;
{size of buffer}
{more fields for internal use}
END;
TPRect = "Rect;
TPrStatus = RECORD
iTotPages:
iCurPage:
iTotCopies:
iCurCopy:
iTotBands :
iCurBand:
fPgDirty:
fimaging:
hPrint:
pPrPort:
hPic:
END;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
BOOLEAN;
BOOLEAN;
THPrint;
TPPrPort;
PicHandle
{number of pages i n spool file}
{page being printed}
{number of copies requested}
{copy being printed}
{used internally}
{used internally}
{TRUE if started printing page}
{used internally}
(print record}
(printing grafPort}
(used internally}
Routines [Not in ROM]
Initialization and Termination
PROCEDURE PrOpen;
PROCEDURE PrClose;
Print Records and Dialogs
PROCEDURE PrintDefault
FUNCTION
PrValidate
FUNCTION
PrStlDial og
FUNCTION
PrJobDial og
PROCEDURE PrJobMerge
Printing
FUNCTION
PrOpenDoc
PROCEDURE PrOpenPage
PROCEDURE PrClosePage
PROCEDURE PrCloseDoc
PROCEDURE PrPicFile
(hPrint: THPrint);
(hPrint : THPrint)
BOOLEAN;
(hPrint: THPrint)
: BOOLEAN;
(hPrint: THPrint)
: BOOLEAN;
(hPrintSrc, hPrintDst: THPrint);
(hPrint: THPrint; pPrPort: TPPrPort; pIOBuf: Ptr)
TPPrPort;
(pPrPort: TPPrPort; pPageFrame: TPRect);
(pPrPort: TPPrPort);
(pPrPort : TPPrPort);
(hPrint: THPrint; pPrPort: TPPrPort; pIOBuf: Ptr;
pDevBuf : Ptr; VAR prStatus: TPrStatus) ;
Printing Manager III-137

<!-- source-page: 145 -->
## Page 145

Inside Macintosh
Error Handling
FUNCTION
PrError
INTEGER;
PROCEDURE PrSetError (iErr: INTEGER);
Low-Level Driver Access
PROCEDURE PrDrvrOpen;
PROCEDURE PrDrvrClose;
PROCEDURE PrCtlCall
FUNCTION
PrDrvrDCE
FUNCTION
PrDrvrVers :
(iWhichCtl : INTEGER; 1Paraml,1Param2,1Param3 :
LONGINT);
Handle;
INTEGER;
Assembly-Language Information
Constants
; Printing methods
bDraftLoop
bSpoolLoop
.EQU
.EQU
; Result codes
no Err
iPrSavPFil
controlErr
iIOAbort
iMernFullErr
iPrAbort
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
0
1
0
-1
-17
-27
-108
128
;draft printing
;spool printing
;no error
;saving spool file
;unimplemented control instruction
;I/O abort error
;not enough room in heap zone
;application or user requested abort
; Printer Driver Control call parameters
iPrDevCtl
.EQU
7
;printer control
lPrReset
.EQU
1
; reset printer
iPrLineFeed .EQU
3
; carriage return/paper advance
iPrLFSixth
.EQU
3
;standard 1/6-inch line feed
lPrPageEnd
.EQU
2
; end page
iPrBitsCtl
.EQU
4
;bit map printing
lScreenBits
.EQU
0
; default for printer
lPaintBits
.EQU
1
; square dots (72 by 72)
iPrIOCtl
.EQU
5
;text streaming
; Printer Driver information
iPrDrvrRef
.EQU
- 3
;Printer Driver reference number
III-138 Printing Manager

<!-- source-page: 146 -->
## Page 146

Printing Graf Port Data Structure
gPort
iPrPortSize
GrafPort to draw in (portRec bytes)
Size in bytes of printing grafPort
Print Record Data Structure
iPrVersion
prlnfo
rPaper
prStl
prXInfo
prJob
iPrintSize
Printing Manager version (word)
Printer information subrecord ( 14 bytes)
Paper rectangle (8 bytes)
Additional device information (8 bytes)
Additional device information (16 bytes)
Job subrecord (iPrJobSize bytes)
Size in bytes of print record
Structure of Printer Information Subrecord
iVRes
iHRes
rPage
Vertical resolution of printer (word)
Horizontal resolution of printer (word)
Page rectangle (8 bytes)
Structure of Job Subrecord
iFstPage
iLstPage
iCopies
bJDocLoop
pldleProc
pFileName
iFileVol
bFileVers
iPrJobSize
First page to print (word)
Last page to print (word)
Number of copies (word)
Printing method (byte)
Address of background procedure
Pointer to spool file name (preceded by length byte)
Spool file volume reference number (word)
Spool file version number (byte)
Size in bytes of job subrecord
Structure of PrXlnfo Subrecord
iDevBytes
Size of buffer (word)
Structure of Printer Status Record
iTotPages
iCurPage
iTotCopies
iCurCopy
fPgDirty
hPrint
pPrPort
iPrStatSize
Number of pages in spool file (word)
Page being printed (word)
Number of copies requested (word)
Copy being printed (word)
Nonzero if started printing page (byte)
Handle to print record
Pointer to printing grafPort
Size in bytes of printer status record
Summary
Printing Manager IJJ-139

<!-- source-page: 147 -->
## Page 147

Inside Macintosh
Variables
PrintErr
Result code from last Printing Manager routine (word)
///-140 Printing Manager

<!-- source-page: 148 -->
## Page 148

QUICKDRAW
Constants
CONST
{ Source transfer modes
srcCopy
0;
srcOr
l;
srcXor
2;
srcBic
3;
notSrcCopy
4;
notSrcOr
5;
notSrcXor
6;
notSrcBic
7;
{ Pattern transfer modes
pat Copy
8;
patOr
9;
patXor
10;
patBic
11;
notPatCopy
12;
notPatOr
13;
notPatXor
14;
notPatBic
15;
{ Standard colors for ForeColor and BackColor }
blackColor
33;
whiteColor
30;
redColor
205;
greenColor
341;
blueColor
409;
cyanColor
273;
magentaColor
137;
yellowColor
69;
{ Standard picture comments
picLParen
O;
picRParen
1;
Data Types
Summary
TYPE Styleitem
Style
(bold,italic, underline,outline,shadow, condense,extend);
SET OF Styleitem;
QuickDraw IIl-141

<!-- source-page: 149 -->
## Page 149

Inside Macintosh
VHSelect = (v, h) ;
Point
RECORD CASE INTEGER OF
O: (v: INTEGER;
{vertical coordinate}
h: INTEGER); {horizontal coordinate }
1: (vh: ARRAY[VHSelect] OF INTEGER)
END;
Rect
RECORD CASE INTEGER OF
0: (top:
left:
bottom:
right:
INTEGER;
INTEGER;
INTEGER;
INTEGER);
1: (topLeft:
Point;
botRight: Point)
END;
RgnHandle
RgnPtr
Region
BitMap
"RgnPtr;
"Region;
RECORD
rgnSize: INTEGER;
{size in bytes}
rgnBBox: Rect;
{enclosing rectangle}
{more data if not rectangular}
END;
RECORD
baseAddr: Ptr;
rowBytes: INTEGER;
bounds :
Rect
END;
{pointer to bit image}
{row width}
{boundary rectangle}
Pattern= PACKED ARRAY[0 .. 7] OF 0 .. 255;
Bits16
ARRAY[0 . . 15) OF INTEGER;
Cursor
RECORD
data:
Bitsl6;
mask:
Bits16;
hotspot: Point
END;
111-142 Quick.Draw
{cursor image}
{cursor mask}
{point aligned with mouse }

<!-- source-page: 150 -->
## Page 150

Summary
QDProcsPtr
"QDProcs;
QDProcs
RECORD
textProc:
Ptr;
{text drawing}
lineProc:
Ptr; {line drawing}
rectProc:
Ptr;
{rectangle drawing}
rRectProc:
Ptr;
{roundRect drawing}
ovalProc:
Ptr;
{oval drawing}
arcProc:
Ptr;
{arc/wedge drawing}
rgnProc:
Ptr;
{region drawing}
bitsProc:
Ptr; {bit transfer}
commentProc:
Ptr; {picture comment processing}
txMeasProc:
Ptr;
{text width measurement}
getPicProc:
Ptr;
{pi cture retrieval}
putPicProc :
Ptr
{picture saving}
END;
Graf Ptr
"Graf Port;
Graf Port
RECORD
device :
INTEGER;
{device- specific information}
portBits:
BitMap;
{grafPort's bit map}
portRect:
Rect;
{grafPort ' s rectangle}
visRgn:
RgnHandle;
{visible region}
clipRgn:
RgnHandle;
{clipping region}
bkPat:
Pattern;
{background pattern}
fillPat:
Pattern;
{fill pattern}
pnLoc:
Point;
{pen location}
pnSize:
Point;
{pen s ize}
pnMode:
INTEGER;
{pen's transfer mode}
pnPat:
Patt ern;
{pen pattern}
pnVis:
INTEGER;
{pen visibility }
txFont:
INTEGER;
{font number for text}
txFace:
Style;
{text 's character styl e }
txMode:
INTEGER;
{text ' s transfer mode}
txSize:
INTEGER;
{font size for text}
spExtra:
Fixed;
{extra space}
fgColor:
LONGINT;
{foreground color}
bkColor :
LONGINT;
{background color}
colrBit:
INTEGER;
{color bit}
patStretch:
INTEGER;
{used internally}
picSave:
Handle;
{picture being saved}
rgnSave:
Handle;
{region being saved}
polySave:
Handle;
{polygon being saved}
graf Procs :
QDProcsPt r
{low-level drawing routines }
END;
P icHandle = "P icPtr;
PicPtr
"Picture;
Picture
RECORD
picSize :
INTEGER;
{size in bytes}
picFrame:
Rect;
{picture frame}
{picture definition data}
END;
Quick.Draw 111-143

<!-- source-page: 151 -->
## Page 151

Inside Macintosh
PolyHandle = "PolyPtr;
PolyPtr
= "Polygon;
Polygon
=RECORD
polySize:
polyBBox:
polyPoints:
INTEGER;
{size in bytes }
Rect;
{enclosing rectangle}
ARRAY[0 .. 0] OF Point
END;
PenState =RECORD
pnLoc:
Point;
{pen location}
pnSize: Point;
{pen size}
pnMode:
INTEGER;
{pen's transfer model
pnPat:
Pattern
{pen pattern}
END;
Font Info =RECORD
ascent:
INTEGER;
{ascent}
descent: INTEGER;
{descent}
widMax:
INTEGER;
{maximum character width}
leading: INTEGER
{leading}
END;
GrafVerb = (frame,paint,erase,invert, fill);
Variables
VAR thePort :
GrafPtr;
{pointer to current grafPort}
white:
Pattern;
{all-white pattern}
black:
Pattern;
{all-black pattern}
gray:
Pattern;
{50% gray pattern}
l tGray:
Pattern;
{25% gray pattern}
dkGray:
Pattern;
{75% gray pattern}
arrow:
Cursor;
{standard arrow cursor}
screenBits : BitMap;
{the entire screen}
randSeed:
LONGINT;
{determines where Random sequence begins}
Routines
Graf Port Routines
PROCEDURE InitGraf
PROCEDURE OpenPort
PROCEDURE InitPort
PROCEDURE ClosePort
PROCEDURE SetPort
PROCEDURE GetPort
PROCEDURE GrafDevi ce
PROCEDURE SetPortBits
PROCEDURE PortSize
JJ/-144 QuickDraw
(globalPtr: Ptr);
(port: GrafPtr) ;
(port: GrafPtr) ;
(port: GrafPtr) ;
(port: GrafPtr) ;
(VAR port : GrafPtr);
(device : INTEGER);
(bm: BitMap) ;
(width,height: INTEGER);

<!-- source-page: 152 -->
## Page 152

PROCEDURE MovePortTo
(leftGlobal,topGlobal: INTEGER);
PROCEDURE SetOrigin
(h, v : INTEGER);
PROCEDURE Set Clip
(rgn: RgnHandle) ;
PROCEDURE Get Clip
(rgn: RgnHandl e);
PROCEDURE ClipRect
(r: Rect);
PROCEDURE BackPat
(pat : Pattern);
Cursor Handling
PROCEDURE InitCursor;
PROCEDURE SetCursor (crsr: Cursor ) ;
PROCEDURE HideCursor;
PROCEDURE ShowCursor;
PROCEDURE ObscureCursor;
Pen and Line Drawing
PROCEDURE HidePen;
PROCEDURE ShowPen;
PROCEDURE GetPen
PROCEDURE GetPenState
PROCEDURE SetPenState
PROCEDURE PenSize
PROCEDURE PenMode
PROCEDURE PenPat
PROCEDURE PenNorrnal;
PROCEDURE MoveTo
PROCEDURE Move
PROCEDURE LineTo
PROCEDURE Li ne
Text Drawing
PROCEDURE TextFont
PROCEDURE Text Face
PROCEDURE TextMode
PROCEDURE Text Size
PROCEDURE SpaceExtra
PROCEDURE DrawChar
PROCEDURE Drawstring
PROCEDURE DrawText
FUNCTION
CharWidth
FUNCTION
StringWidth
FUNCTION
Text Width
PROCEDURE GetFontinfo
(VAR pt: Point);
(VAR pnState : PenState) ;
(pnState: PenState);
(width, height : INTEGER);
(mode : INTEGER);
(pat: Pattern);
(h, v: INTEGER) ;
(dh,dv: INTEGER);
(h, v : INTEGER);
(dh, dv: INTEGER);
(font : INTEGER) ;
(face: Style);
(mode: INTEGER);
(size: INTEGER);
(extra: Fixed);
(ch: CHAR);
(s: Str255);
(textBuf: Ptr; firstByte,byteCount: INTEGER);
(ch: CHAR) : INTEGER;
(s: Str255) : I NTEGER;
(textBuf: Ptr; firstByte,byteCount : INTEGER)
INTEGER;
(VAR info: Fonti nfo);
Summary
Quick.Draw III-145

<!-- source-page: 153 -->
## Page 153

Inside Macintosh
Drawing in Color
PROCEDURE ForeColor (color: LONGINT);
PROCEDURE BackColor (color: LONGINT);
PROCEDURE ColorBi t
(whichBit: INTEGER);
Calculations with Rectangles
(VAR r : Rect; left, t op, right, bottom: INTEGER);
(VAR r : Rect; dh,dv: INTEGER);
(VAR r : Rect; dh, dv: INTEGER);
PROCEDURE SetRect
PROCEDURE OffsetRect
PROCEDURE InsetRect
FUNCTION
SectRect
PROCEDURE UnionRect
FUNCTION
PtinRect
PROCEDURE Pt2Rect
PROCEDURE PtToAngle
FUNCTION
EqualRect
FUNCTION
ErnptyRect
(srcl, src2: Rect; VAR dstRect : Rect) : BOOLEAN;
(srcl, src2 : Rect; VAR dstRect : Rect);
(pt: Point; r: Rect) : BOOLEAN;
(ptl, pt2 : Point; VAR dstRect: Rect);
(r: Rect; pt : Point; VAR angle: INTEGER);
(rectl,rect2: Rect) : BOOLEAN;
(r: Rect) : BOOLEAN;
Graphic Operations on Rectangles
PROCEDURE FrameRect
(r : Rect);
PROCEDURE PaintRect
(r: Rect);
PROCEDURE EraseRect
(r: Rect);
PROCEDURE InvertRect
(r: Rect) ;
PROCEDURE FillRect
(r: Rect; pat: Pattern);
Graphic Operations on Ovals
PROCEDURE FrameOval
(r: Rect);
PROCEDURE PaintOval
(r: Rect);
PROCEDURE EraseOval
(r: Rect);
PROCEDURE InvertOval
(r: Rect);
PROCEDURE FillOval
(r: Rect; pat: Pattern);
Graphic Operations on Rounded-Corner Rectangles
PROCEDURE FrameRoundRect
(r: Rect; ovalWidth, ovalHeight: INTEGER);
PROCEDURE PaintRoundRect
(r: Rect; ovalWidth, ovalHeight : INTEGER);
PROCEDURE EraseRoundRect
(r: Rect; ovalWidth, ovalHeight: INTEGER) ;
PROCEDURE InvertRoundRect
(r: Rect; ovalWidth,ovalHeight: INTEGER);
PROCEDURE FillRoundRect
(r: Rect; ovalWidth,ovalHeight: INTEGER;
Pattern);
1//-146 QuickDraw
pat:

<!-- source-page: 154 -->
## Page 154

Graphic Operations on Arcs and Wedges
PROCEDURE FrameArc
(r: Rect; startAngle,arcAngle :
PROCEDURE PaintArc
(r: Rect; startAngle, arcAngle:
PROCEDURE EraseArc
(r : Rect; startAngle, arcAngle :
PROCEDURE InvertArc (r: Rect; startAngl e , arcAngle :
PROCEDURE FillArc
(r: Rect; startAngle, arcAngle:
Pattern);
Calculations with Regions
FUNCTION
NewRgn :
RgnHandle;
(dstRgn : RgnHandle);
(rgn: RgnHandle );
(srcRgn, dstRgn: RgnHandl e ) ;
(rgn: RgnHandle);
Summary
INTEGER);
INTEGER);
INTEGER);
INTEGER);
INTEGER; pat :
PROCEDURE OpenRgn;
PROCEDURE CloseRgn
PROCEDURE DisposeRgn
PROCEDURE CopyRgn
PROCEDURE SetEmptyRgn
PROCEDURE SetRectRgn
PROCEDURE RectRgn
PROCEDURE OffsetRgn
PROCEDURE InsetRgn
PROCEDURE SectRgn
PROCEDURE UnionRgn
PROCEDURE Dif fRgn
PROCEDURE XorRgn
FUNCTION
PtinRgn
(rgn : RgnHandle; left, top,right,bottom: INTEGER);
(rgn: RgnHandl e; r: Rect);
FUNCTION
FUNCTION
FUNCTION
RectinRgn
EqualRgn
EmptyRgn
(rgn: RgnHandle; dh,dv: INTEGER) ;
(rgn : RgnHandle ; dh, dv : INTEGER);
(srcRgnA, srcRgnB, dstRgn: RgnHandle) ;
(srcRgnA, s r cRgnB, dstRgn : RgnHandle);
(srcRgnA, srcRgnB, dstRgn : RgnHandle);
(srcRgnA, srcRgnB, dstRgn : RgnHandle);
(pt : Point; rgn: RgnHandle) : BOOLEAN;
(r: Rect; rgn : RgnHandle) : BOOLEAN;
(rgnA, rgnB: RgnHandle) : BOOLEAN;
(rgn: RgnHandle) : BOOLEAN;
Graphic Operations on Regions
PROCEDURE FrameRgn
(rgn: RgnHandle) ;
PROCEDURE PaintRgn
(rgn: RgnHandle) ;
PROCEDURE EraseRgn
(rgn: RgnHandle) ;
PROCEDURE InvertRgn (rgn: RgnHandle) ;
PROCEDURE FillRgn
(rgn: RgnHandle; pat : Pattern);
Bit Transfer Operations
PROCEDURE ScrollRect
(r: Rect; dh, dv : INTEGER; updateRgn: RgnHandle);
PROCEDURE CopyBits
(srcBits, dstBits : BitMap; srcRect, dstRect: Rect ;
mode : INTEGER; maskRgn: RgnHandle);
QuickDraw 111-147

<!-- source-page: 155 -->
## Page 155

Inside Macintosh
Pictures
FUNCTION
OpenPicture
PROCEDURE PicComment
PROCEDURE ClosePicture;
PROCEDURE DrawPicture
PROCEDURE KillPicture
(picFrame: Rect) : PicHandle;
(kind, dataSize: INTEGER; dataHandle: Handle);
(myPicture: PicHandle; dstRect: Rect);
(myPicture: PicHandle);
Calculations with Polygons
FUNCTION
OpenPoly :
PROCEDURE ClosePoly;
PROCEDURE KillPoly
PROCEDURE OffsetPoly
PolyHandle;
(poly: PolyHandle);
(poly: PolyHandle; dh, dv: INTEGER);
Graphic Operations on Polygons
PROCEDURE FramePoly
PROCEDURE PaintPoly
PROCEDURE ErasePoly
PROCEDURE InvertPoly
PROCEDURE FillPoly
(poly: PolyHandle);
(poly: PolyHandle);
(poly: PolyHandle);
(poly: PolyHandle);
(poly: PolyHandle; pat: Pattern);
Calculations with Points
PROCEDURE AddPt
PROCEDURE SubPt
PROCEDURE SetPt
FUNCTION
EqualPt
PROCEDURE LocalToGlobal
PROCEDURE GlobalToLocal
(srcPt: Point; VAR dstPt: Point);
(srcPt: Point; VAR dstPt: Point);
(VAR pt: Point; h, v : INTEGER) ;
(ptl,pt2: Point) : BOOLEAN;
(VAR pt : Point) ;
(VAR pt: Point);
Miscellaneous Routines
FUNCTION
Random :
FUNCTION
GetPixel
PROCEDURE StuffHex
PROCEDURE ScalePt
PROCEDURE MapPt
PROCEDURE MapRect
PROCEDURE MapRgn
PROCEDURE MapPoly
III-148 QuickDraw
INTEGER;
(h,v: INTEGER) : BOOLEAN;
(thingPtr: Ptr; s: Str255);
(VAR pt: Point; srcRect,dstRect: Rect);
(VAR pt: Point; srcRect,dstRect: Rect);
(VAR r: Rect; srcRect,dstRect: Rect);
(rgn: RgnHandle; srcRect,dstRect: Rect);
(poly: PolyHandle; srcRect,dstRect: Rect);

<!-- source-page: 156 -->
## Page 156

Summary
Customizing QuickDraw Operations
PROCEDURE SetStdProcs
PROCEDURE StdText
PROCEDURE Std.Line
PROCEDURE StdRect
PROCEDURE StdRRect
PROCEDURE StdOval
PROCEDURE StdArc
PROCEDURE StdPoly
PROCEDURE StdRgn
PROCEDURE StdBits
PROCEDURE StdComment
FUNCTION
StdTxMeas
PROCEDURE StdGet Pic
PROCEDURE StdPutPic
(VAR procs: QDProcs);
(byteCount: INTEGER; textBuf: Ptr; nurner,denom:
Point);
(newPt: Point);
(verb: GrafVerb; r: Rect);
(verb : GrafVerb; r: Rect; ovalwidth,oval Height :
INTEGER);
(verb: GrafVerb; r: Rect);
(verb: GrafVerb; r : Rect; startAngle,arcAngle:
INTEGER);
(verb : GrafVerb; poly : PolyHandle );
(verb : Gr afVerb; rgn: RgnHandle);
(VAR srcBi ts: BitMap; VAR srcRect ,dstRect: Rect;
mode: INTEGER; maskRgn : RgnHandle);
(kind,dataSize: INTEGER; dataHandle: Handle);
(byteCount: INTEGER; textAddr: Ptr; VAR numer,
denom: Point; VAR info: Fontinfo) : INTEGER;
(dataPtr: Ptr; byteCount : INTEGER);
(dataPtr : Ptr; byteCount: INTEGER);
Assembly-Language Information
Constants
; Size in bytes of QuickDraw global vari ables
grafSi ze
.EQU
206
; Source transfer modes
srcCopy
.EQU
0
srcOr
.EQU
1
srcXor
.EQU
2
srcBic
.EQU
3
notSrcCopy
.EQU
4
notSrcOr
.EQU
5
notSrcXor
.EQU
6
notSrcBic
.EQU
7
; Pattern t r ansfer modes
patCopy
.EQU
8
pa tor
.EQU
9
patXor
.EQU
10
patBic
.EQU
11
notPatCopy
.EQU
12
notPatOr
.EQU
13
notPatXor
.EQU
14
notPatBic
.EQU
15
Quick.Draw llI-149

<!-- source-page: 157 -->
## Page 157

Inside Macintosh
; Standard colors for ForeColor and BackColor
blackColor
.EQU
33
whiteCol or
.EQU
30
redColor
.EQU
205
greenColor
.EQU
341
blueColor
.EQU
409
cyanColor
.EQU
273
magentaColor
.EQU
137
yellowCol or
.EQU
69
; Standard picture comments
picLParen
.EQU
0
picRParen
.EQU
1
; Character style
boldBit
.EQU
0
italicBit
.EQU
1
ulineBit
.EQU
2
outlineBit
.EQU
3
shadowBit
.EQU
4
condenseBit
.EQU
5
extendBit
.EQU
6
; Graphic operati ons
frame
.EQU
0
paint
. EQU
1
erase
.EQU
2
invert
.EQU
3
fill
.EQU
4
Point Data Structure
v
h
Vertical coordinate (word)
Horizontal coordinate (word)
Rectangle Data Structure
top
left
bottom
right
topLeft
botRight
III-150 QuickDraw
Vertical coordinate oftop left comer (word)
Horizontal coordinate of top left comer (word)
Vertical coordinate of bottom right comer (word)
Horizontal coordinate of bottom right comer (word)
Top left corner (point; long)
Bottom right comer (point; long)

<!-- source-page: 158 -->
## Page 158

Region Data Structure
rgnSize
rgnBBox
rgnData
Size in bytes (word)
Enclosing rectangle (8 bytes)
More data if not rectangular
Bit Map Data Structure
baseAddr
row Bytes
bounds
bitMapRec
Pointer to bit image
Row width (word)
Boundary rectangle (8 bytes)
Size in bytes of bit map data structure
Cursor Data Structure
data
mask
hotSpot
curs Rec
Cursor image (32 bytes)
Cursor mask (32 bytes)
Point aligned with mouse (long)
Size in bytes of cursor data structure
Structure of QDProcs Record
textProc
lineProc
rectProc
rRectProc
ovalProc
arcProc
polyProc
rgnProc
bitsProc
commentProc
txMeasProc
getPicProc
putPicProc
qdProcsRec
Address of text-drawing routine
Address of line-drawing routine
Address of rectangle-drawing routine
Address of roundRect-drawing routine
Address of oval-drawing routine
Address of arc/wedge-drawing routine
Address of polygon-drawing routine
Address of region-drawing routine
Address of bit-transfer routine
Address of routine for processing picture comments
Address of routine for measuring text width
Address of picture-retrieval routine
Address of picture-saving routine
Size in bytes of QDProcs record
Graf Port Data Structure
device
portBits
portBounds
portRect
visRgn
clipRgn
bkPat
fillPat
pnLoc
Font-specific information (word)
GrafPort's bit map (bitMapRec bytes)
Boundary rectangle of grafPort's bit map (8 bytes)
GrafPort's rectangle (8 bytes)
Handle to visible region
Handle to clipping region
Background pattern (8 bytes)
Fill pattern (8 bytes)
Pen location (point; long)
Summary
QuickDraw lll-151

<!-- source-page: 159 -->
## Page 159

Inside Macintosh
pnSize
pnMode
pnPat
pnVis
txFont
txFace
txMode
txSize
spExtra
fgColor
bkColor
colrBit
picSave
rgnSave
poly Save
grafProcs
portRec
Pen size (point; long)
Pen's transfer mode (word)
Pen pattern (8 bytes)
Pen visibility (word)
Font number for text (word)
Text's character style (word)
Text's transfer mode (word)
Font size for text (word)
Extra space (long)
Foreground color (long)
Background color (long)
Color bit (word)
Handle to picture being saved
Handle to region being saved
Handle to polygon being saved
Pointer to QDProcs record
Size in bytes of grafPort
Picture Data Structure
picSize
picFrame
picData
Size in bytes (word)
Picture frame (rectangle; 8 bytes)
Picture definition data
Polygon Data Structure
polySize
polyBBox
poly Points
Size in bytes (word)
Enclosing rectangle (8 bytes)
Polygon points
Pen State Data Structure
psLoc
psSize
psMode
psPat
psRec
Pen location (point; long)
Pen size (point; long)
Pen's transfer mode (word)
Pen pattern (8 bytes)
Size in bytes of pen state data structure
Font Information Data Structure
ascent
descent
widMax
leading
III-152 QuickDraw
Ascent (word)
Descent (word)
Maximum character width (word)
Leading (word)

<!-- source-page: 160 -->
## Page 160

Special Macro Names
Pascal name
SetPortBits
InvertRect
InvertRoundRect
DisposeRgn
SetRectRgn
OffsetRgn
InvertRgn
ClosePoly
Vari ables
RndSeed
Macro name
SetPBits
InverRect
InverRoundRect
=DisposRgn
_SetRecRgn
_OfSetRgn
_InverRgn
_ClosePgon
Random number seed (long)
Summary
Quick.Draw JJJ-153

<!-- source-page: 161 -->
## Page 161

Inside Macintosh
RESOURCE MANAGER
Constants
CONST
{ Masks for resource attributes
resSysHeap
64;
{set if read into system heap}
resPurgeable
32;
{set if purgeable }
res Locked
16;
{set if locked}
resProtected
8;
{set if protected}
resPreload
4;
{set if to be preloaded}
res Changed
2;
{set if to be written to resource file}
{ Resource Manager result codes }
resNotFound
resFNotFound
addResFailed
nnvResFailed
= - 192;
- 193;
- 194;
-196;
{resource not found )
{resource file not found)
{AddResource failed}
{RmveResource failed}
{ Masks for resource file attributes }
mapReadOnl y = 128;
mapCompact
64;
mapChanged
32;
Data Types
{set if file is read-only}
{set to compact file on update}
{set to write map on update}
TYPE ResType =PACKED ARRAY[l. .4) OF CHAR;
Routines
Initialization
FUNCTION
InitResources
PROCEDURE RsrcZoneinit;
INTEGER;
Opening and Closing Resource Files
PROCEDURE CreateResFile (fileName: Str255);
FUNCTION
OpenResFile
(fileName: Str255)
INTEGER;
PROCEDURE CloseResFile
(refNum: INTEGER);
III-154 Resource Manager

<!-- source-page: 162 -->
## Page 162

Checking for Errors
FUNCTION ResError : INTEGER;
Setting the Current Resource File
FUNCTION
CurResFile : INTEGER;
FUNCTION
HomeResFile (theResource: Handle)
PROCEDURE UseResFile
(refNum: INTEGER);
Getting Resource Types
FUNCTION
CountTypes : INTEGER;
INTEGER;
PROCEDURE GetindType
(VAR theType: ResType; index: INTEGER);
Getting and Disposing of Resources
PROCEDURE SetResLoad
(load: BOOLEAN);
FUNCTION
CountResources
(theType : Res Type)
: INTEGER;
FUNCTION
Get Ind.Resource
(theType: ResType; index: INTEGER)
FUNCTION
GetResource
(theType: ResType; theID: INTEGER)
Summary
: Handle;
: Handle;
FUNCTION
GetNamed.Resource (theType: ResType; name: Str255)
: Handle;
PROCEDURE Load.Resource
(theResource : Handle);
PROCEDURE ReleaseResource
(theResource: Handle);
PROCEDURE DetachResource
(theResource: Handle);
Getting Resource Information
FUNCTION
UniqueID
PROCEDURE GetResinfo
FUNCTION
GetResAttrs
FUNCTION
SizeResource
Modifying Resources
PROCEDURE SetResinfo
(theType: ResType) : INTEGER;
(theResource: Handle; VA~ theID: INTEGER; VAR
theType: ResType; VAR name: Str255);
(theResource: Handle)
INTEGER;
(theResource: Handl e) : LONGINT;
(theResource: Handle; theID : INTEGER; name:
Str255);
PROCEDURE SetResAttrs
PROCEDURE Changed.Resource
PROCEDURE Add.Resource
(theResource: Handle; attrs: INTEGER);
(theResource: Handle);
(theData: Handle; theType: ResType; theID:
PROCEDURE RmveResource
PROCEDURE UpdateResFile
PROCEDURE WriteResource
PROCEDURE SetResPurge
INTEGER; name: Str255);
(theResource: Handle);
(refNum: INTEGER);
(theResource: Handle);
(install: BOOLEAN);
Resource Manager JII-155

<!-- source-page: 163 -->
## Page 163

Inside Macintosh
Advanced Routines
FUNCTION
GetResFileAttrs (refNum: INTEGER) : INTEGER;
PROCEDURE SetResFileAtt rs (refNum: INTEGER; attrs: INTEGER);
Assembly-Language Information
Constants
; Resource attributes
resSysHeap
.EQU
6
;set if read into system heap
r esPurgeable
.EQU
5
; set if purgeable
res Locked
.EQU
4
;set if locked
resProtected
.EQU
3
;set if protected
resPreload
.EQU
2
;set if to be preloaded
resChanged
.EQU
1
;set if to be written to resource file
; Resource Manager result codes
resNotFound
.EQU
- 192
;resource not found
resFNotFound
.EQU
- 193
;resource file not found
addResFailed
.EQU
-194
;AddResource failed
rmvResFailed
.EQU
-196
;RmveResource failed
; Resource fil e attributes
mapReadOnly
mapCompact
mapChanged
.EQU
.EQU
.EQU
7
6
5
;set if fil e is read- only
;set to compact file on update
;set to write map on updat e
Special Macro Names
Pascal name
SizeResource
Variables
TopMapHndl
SysMapHndl
SysMap
CurMap
ResLoad
Res Err
ResErrProc
SysResName
Macro name
SizeRsrc
Handle to resource map of most recently opened resource file
Handle to map of system resource file
Reference number of system resource file (word)
Reference number of current resource file (word)
Current SetResLoad state (word)
Current value of ResError (word)
Address of resource error procedure
Name of system resource file (length byte followed by up to 19 characters)
III-156 Resource Manager

<!-- source-page: 164 -->
## Page 164

SCRAP MANAGER
Constants
CONST { Scrap Manager result codes }
noScrapErr
noTypeErr
Data Types
TYPE PScrapStuff
ScrapStuf f
-100;
- 102;
{desk scrap isn ' t initialized}
{no data of the requested type}
LONGINT;
{size of desk scrap}
Handle;
{handle to desk scrap}
Summary
"'ScrapStuff;
RECORD
scrapSize:
scrapHandle :
scrapCount:
scrapState :
scrapName:
INTEGER;
{count changed by ZeroScrap}
INTEGER;
{tells where desk scrap is}
StringPtr {scrap file name}
END;
Routines
Getting Desk Scrap Information
FUNCTION InfoScrap : PScrapStuff;
Keeping the Desk Scrap on the Disk
FUNCTION UnloadScrap
LONGINT;
FUNCTION LoadScrap :
LONGINT;
Writing to the Desk Scrap
FUNCTION ZeroScrap : LONGINT;
FUNCTION PutScrap
(length: LONGINT; theType: ResType; source: Ptr)
LONGINT;
Reading from the Desk Scrap
FUNCTION GetScrap (hDest : Handle; theType: ResType; VAR offset : LONGINT)
: LONGINT;
Scrap Manager JJJ-157

<!-- source-page: 165 -->
## Page 165

Inside Macintosh
Assembly-Language Information
Constants
; Scrap Manager result codes
noScrapErr
noTypeErr
.EQU
.EQU
-100
-102
;desk scrap isn't initialized
;no data of the requested type
Special Macro Names
Pascal name
LoadScrap
UnloadScrap
Variables
ScrapSize
ScrapHandle
ScrapCount
ScrapState
ScrapName
Macro name
_LodeScrap
_ UnlodeScrap
Size in bytes of desk scrap (long)
Handle to desk scrap in memory
Count changed by ZeroScrap (word)
Tells where desk scrap is (word)
Pointer to scrap file name (preceded by length byte)
III-158 Scrap Manager

<!-- source-page: 166 -->
## Page 166

SEGMENT LOADER
Constants
CONST { Message returned by CountAppleFiles
appOpen
appPrint
Data Types
0;
{open the document(s) l
1;
{print the document(s)}
TYPE AppFile =
RECORD
Routines
vRefNum: INTEGER; {volume reference number}
fType:
OSType;
{file type}
versNum: INTEGER; {version number}
fNarne:
Str255
{file name}
END;
Summary
PROCEDURE CountAppFiles (VAR message: INTEGER; VAR count: INTEGER);
(Not
in ROM]
PROCEDURE GetAppFiles
PROCEDURE ClrAppFil es
PROCEDURE GetAppParms
PROCEDURE UnloadSeg
PROCEDURE ExitToShell;
(index: INTEGER; VAR theFile: AppFile);
[Notin ROM]
(index: INTEGER) ;
[Not in ROM]
(VAR apName : Str255; VAR apRefNum: INTEGER; VAR
apPararn: Handle);
(routineAddr: Ptr);
Assembly-Language Information
Advanced Routines
Trap macro
Chain
Launch
_LoadSeg
On entry
(AO): pointer to application's file name {preceded by length byte)
4(AO): configuration of sound and screen buffers (word)
(AO): pointer to application's file name (preceded by length byte)
4(AO): configuration of sound and screen buffers (word)
stack: segment number (word)
Segment Loader II!-159

<!-- source-page: 167 -->
## Page 167

Inside Macintosh
Variables
AppPannHandle
CurApName
CurApRefNum
CurPageOption
CurJTOffset
FinderName
Handle to Finder information
Name of current application (length byte followed by up to 31 characters)
Reference number of current application's resource file (word)
Sound/screen buffer configuration passed to Chain or Launch (word)
Offset to jump table from location pointed to by AS (word)
Name of the Finder (length byte followed by up to 15 characters)
///-160 Segment Loader

<!-- source-page: 168 -->
## Page 168

Summary
SERIAL DRIVERS
Constants
CONST { Driver reset information }
baud300
380;
{300 baud}
baud600
189;
{600 baud}
baud1200
94;
{1200 baud}
baud1800
62;
{1800 baud}
baud2400
46;
{2400 baud}
baud3600
30;
{3600 baud}
baud4800
22;
{4800 baud}
baud7200
14;
{7200 baud}
baud9600
10;
{9600 baud}
baud19200
4;
{19200 baud}
baud57600
O;
{57600 baud}
stoplO
16384;
{1 stop bit}
stop15
-327 68;
{1.5 stop bits}
stop20
-16384;
{2 stop bits}
noParity
0;
{no parity}
oddParity
4096;
{odd parity}
evenParity
12288;
{even parity}
data5
O;
{5 data bits}
data6
2048;
{ 6 data bits}
data7
1024;
{7 data bits}
data8
3072;
{8 data bits}
{ Masks for errors
sWOverrunErr = l;
{set if software overrun error}
parityErr
16; {set if parity error}
hWOverrunErr = 32; {set if hardware overrun error}
frarningErr
64; {set if framing error}
{ Masks for changes that cause events to be posted }
ctsEvent
breakEvent
32;
{set if CTS change will cause event to be }
{ posted}
128;
{set if break status change will cause event
{ to be posted}
{ Indication that an XOff character was sent }
xOffWasSent = $80;
{ Result codes
O;
{no error}
no Err
openErr
-23;
{attempt to open RAM Serial Driver failed}
Serial Drivers JJJ-161

<!-- source-page: 169 -->
## Page 169

Inside Macintosh
Data Types
TYPE SPortSel
SerShk =
(sPortA, {modem port}
sPortB
{printer port});
PACKED RECORD
fXOn: Byte; {XOn/XOff output flow control
fCTS: Byte; {CTS hardware handshake flag}
xOn:
CHAR; {XOn character}
xOff : CHAR; {XOff character}
errs: Byte; {errors that cause abort}
flag}
evts : Byte; {status changes that cause events}
finX: Byte; {XOn/ XOff input flow control flag}
null: Byte
{not used}
END;
SerStaRec = PACKED RECORD
curnErrs :
Byte;
xOffSent: Byte;
rdPend:
Byte;
wrPend:
Byte;
ctsHold:
Byte;
xOffHol d: Byte
END;
Routines [Not in ROM]
{cumulative errors}
{XOff sent as input flow control}
{read pending flag }
{write pending flag}
{CTS flow control hold flag}
{XOff flow control hold flag}
Opening and Closing the RAM Serial Driver
FUNCTION
RAMSDOpen
(whichPort: SPortSel) : OSErr;
PROCEDURE RAMSDClose (whichPort: SPortSel);
Changing Serial Driver Information
FUNCTION SerReset
(refNum: INTEGER; serConfig: INTEGER) : OSErr;
FUNCTION SerSetBuf (refNum: INTEGER; serBPtr: Ptr; serBLen: INTEGER)
OSErr;
FUNCTION SerHShake (refNum: INTEGER; flags : SerShk)
: OSErr;
FUNCTION SerSetBrk (refNum: INTEGER)
OSErr;
FUNCTION SerClrBrk (refNum: INTEGER) : OSErr;
Getting Serial Driver Information
FUNCTI ON SerGetBuf (refNum: INTEGER; VAR count: LONGINT) : OSErr;
FUNCTION SerStatus (refNum: INTEGER; VAR serSta: SerStaRec) : OSErr;
l//-162 Serial Drivers

<!-- source-page: 170 -->
## Page 170

Advanced Control Calls (RAM Serial Driver)
cs Code
13
19
21
22
23
24
25
26
27
csParam
baudRate
char
Effect
Set baud rate (actual rate, as an integer)
Replace parity errors
Unconditionally set XOff for output flow control
Unconditionally clear XOff for input flow control
Send XOn for input flow control if XOff was sent last
Unconditionally send XOn for input flow control
Send XOff for input flow control if XOn was sent last
Unconditionally send XOff for input flow control
Reset SCC channel
Driver Names and Reference Numbers
Driver
Driver name
Reference number
Modem port input
.Aln
-6
Modem port output
.A Out
- 7
Printer port input
.Bin
-8
Printer port output
.BOut
- 9
Assembly-Language Information
Constants
; Re s ul t codes
.EQU
0
; no error
no Err
openErr
.EQU
-23
;att empt t o open RAM Seri al Driver failed
Structure of Control Information for SerHShake
shFXOn
shFCTS
shXOn
shXOff
shErrs
shEvts
shFinX
XOn!XOff output flow control flag (byte)
CTS hardware handshake flag (byte)
XOn character (byte)
XOff character (byte)
Errors that cause abort (byte)
Status changes that cause events (byte)
XOn/XOff input flow control flag (byte)
Summary
Serial Drivers lll-163

<!-- source-page: 171 -->
## Page 171

Inside Macintosh
Structure of Status Information for SerStatus
ssCumErrs
ssXOffSent
ssRdPend
ssWrPend
ssCTSHold
ssXOftHold
Cumulative errors (byte)
XOff sent as input flow control (byte)
Read pending flag (byte)
Write pending flag (byte)
CTS flow control hold flag (byte)
XOff flow control hold flag (byte)
Equivalent Device Manager Calls
Pascal routine
Call
SerReset
Control with csCode=8, csParam=serConfig
SerSetBuf
Control with csCode=8, csParam=serBPtr, csParam+4=serBLen
SerHShake
Control with csCode=lO, csParam through csParam+6=flags
SerSetBrk
Control with csCode=12
SerClrBrk
Control with csCode=l 1
SerGetBuf
Status with csCode=2; count returned in csParam
SerStatus
Status with csCode=8; serSta returned in csParam through csParam+S
///-164 Serial Drivers

<!-- source-page: 172 -->
## Page 172

SOUND DRIVER
Constants
CONST { Mode values for synthesizers }
swMode
ftMode
ffMode
-1;
1;
O;
Data Types
{square-wave synthesizer}
{four- tone synthesizer }
{free- form synthesizer}
TYPE
{ Free-form synthesizer }
FFSynthPtr
FFSynthRec
"'FFSynthRec;
RECORD
mode:
INTEGER;
count:
Fixed;
waveBytes: FreeWave
END;
{always ffMode}
{"sampling" factor }
{waveform description}
Free Wave
PACKED ARRAY[0 .. 30000] OF Byte;
{ Square-wave synthesizer
SWSynthPtr = "'SWSynthRec;
SWSynthRec = RECORD
mode:
triplets:
INTEGER;
{always swMode}
Tones
{sounds }
END;
Tones
ARRAY [ 0 .. 5000] OF Tone;
Tone
RECORD
count :
INTEGER;
{frequency}
amplitude: INTEGER;
{amplitude, 0- 255}
duration:
INTEGER
{duration in ticks}
END;
Four- tone synthesizer
FTSynthPtr
FTSynthRec
"'FTSynthRec;
RECORD
mode:
INTEGER;
sndRec: FTSndRecPtr
END;
{always ftMode}
{tones to play}
Summary
Sound.Driver JII-165

<!-- source-page: 173 -->
## Page 173

Inside Macintosh
FTSndRecPtr
"FTSoundRec;
FTSoundRec
RECORD
duration:
INTEGER;
{duration in ticks}
soundlRate:
Fixed;
{tone 1 cycle rate}
soundlPhase: LONGINT;
{tone 1 byte offset}
sound2Rate:
Fixed;
{tone 2 cycle rate}
sound2Phase: LONGINT;
{tone 2 byte offset}
sound3Rate:
Fixed;
{tone 3 cycle rate }
sound3Phase: LONGINT;
{tone 3 byte offset}
sound4Rate:
Fixed;
{tone 4 cycle rate}
sound4Phase: LONGINT;
{tone 4 byte offset}
soundlWave:
WavePtr;
{tone 1 waveform}
sound2Wave:
WavePtr;
{tone 2 waveform}
sound3Wave:
WavePtr;
{tone 3 waveform}
sound4Wave:
WavePtr
{tone 4 waveform}
END;
WavePtr = "Wave;
Wave
=PACKED ARRAY[0 . . 255) OF Byte;
Routines [Not in ROM]
PROCEDURE StartSound
(synthRec: Ptr; nurnBytes: LONGINT; completionRtn :
ProcPtr);
PROCEDURE StopSound;
FUNCTION
SoundDone :
BOOLEAN;
PROCEDURE GetSoundVol (VAR level: INTEGER);
PROCEDURE SetSoundVol (level: INTEGER);
Assembly-Language Information
Routines
Pascal name
StartSound
StopSound
SoundDone
GetSoundVol
SetSoundVol
Variables
SdVolume
SoundPtr
SoundLevel
CurPitch
Equivalent for assembly language
Call Write with ioRefNum=-4, ioBuffer=synthRec, ioReqCount=numBytes
Call KillIO and (for square-wave) set CurPitch to 0
Poll ioResult field of most recent Write call's parameter block
Get low-order three bits of variable SdVolume
Call this Pascal procedure from your program
Speaker volume (byte: low-order three bits only)
Pointer to four-tone record
Amplitude in 740-byte buffer (byte)
Value of count in square-wave synthesizer buffer (word)
III-166 Sound Driver

<!-- source-page: 174 -->
## Page 174

Summary
Sound Driver Values for Notes
The following table contains values for the rate field of a four-tone synthesizer and the count field
of a square-wave synthesizer. A just-tempered scale-in the key of C, as an example- is given
in the first four columns; you can use a just-tempered scale for perfect tuning in a particular key.
The last four columns give an equal-tempered scale, for applications that may use any key; this
scale is appropriate for most Macintosh sound applications. Following this table is a list of the
ratios used in calculating these values, and instructions on how to calculate them for a justtempered scale in any key.
Just-Tempered Scale
Equal-Tempered Scale
Rate for
Count for
Rate for
Count for
Four-Tone
Square-Wave
Four-Tone
Square-Wave
Note
Long
Fixed
Word
Integer
Long
Fixed
Word Integer
3 octaves below middle C
c
612B
0.37956
5CBA
23738
604C
0.37616
5092
23954
C#
667C
0.40033
57EB
22507
6606
0.39853
5851
22609
Db
67A6
0.40488
56EF
22255
D
6051
0.42702
5260
21101
6C17
0.42223
535C
21340
Ebb
6E8F
0.43187
5180
20864
D#
71DF
0.44481
4F21
20257
7284
0.44733
4EAF
20143
Eb
749A
0.45547
4046
19782
E
7976
0.47446
4A2F
18991
7953
0.47392
4A44
19012
F
818F
0.50609
458C
17804
808A
0.50211
4619
17945
F#
88A5
0.53377
41FO
16880
882F
0.53197
422A
16938
Gb
8A32
0.53983
4133
16691
G
91Cl
0.56935
3DD1
15825
9048
0.56360
3E73
15987
G#
9704
0.59308
3B58
15192
98DC
0.59711
3AF2
15090
Ab
9B79
0.60732
39F4
14836
A
A1F3
0.63261
37A3
14243
A1F3
0.63261
37A3
14243
Bbb
A3CA
0.63980
3703
14083
A#
AAOC
0.66425
34FD
13565
AB94
0.67023
3484
13444
Bb
ACBF
0.67479
3429
13353
B
B631
0.71169
3174
12660
B5C8
0.71008
3191
12689
2 octaves below middle C
c
C257
0.75914
2E5D
11869
C097
0.75230
2EC9
11977
C#
CCF8
0.80066
2BF6
11254
CCOB
0.79704
2C29
11305
Db
CF4C
0.80975
2B77
11127
D
DAA2
0.85403
2936
10550
D82D
0.84444
29AE
10670
Ebb
DDlD
0.86372
28CO
10432
D#
E3BE
0.88962
2790
10128
E508
0.89465
2757
10071
Eb
E935
0.91096
26A3
9891
E
F2ED
0.94893
2517
9495
F2A6
0.94785
2522
9506
F
1031E
1.01218
22C6
8902
10114
1.00421
230C
8972
F#
1114A
1.06754
20F8
8440
11050
1.06392
2115
8469
Gb
11465
1.07967
2099
8345
G
12382
1.13870
1EE9
7913
12090
1.12720
1F3A
7994
Sound Driver Il/-167

<!-- source-page: 175 -->
## Page 175

Inside Macintosh
Note
Long
Fixed
Word
Integer
Long
Fixed
Word Integer
2 octaves below middle C
G#
12FA8
1.18616
lDAC
7596
131B8
1.19421
1079
7545
Ab
136Fl
1.21461
lCFA
7418
A
143E6
1.26523
lBDl
7121
143E6
1.26523
lBDl
7121
Bbb
14794
1.27960
1B81
7041
A#
15418
1.32849
1A7E
6782
15729
1.34047
1A42
6722
Bb
1597E
1.34958
1Al4
6676
B
16C63
1.42339
18BA
6330
16B90
1.42017
18C8
6344
1 octave below middle C
c
184AE
1.51828
172F
5935
1812F
1.50462
1764
5988
C#
199EF
1.60130
15FB
5627
19816
1.59409
1614
5652
Db
19E97
1.61949
15BC
5564
D
1B543
1.70805
149B
5275
1B05A
1.68887
1407
5335
Ebb
1BA3B
1.72746
1460
5216
D#
1C77B
1.77922
13C8
5064
lCAlO
1.78931
13AC
5036
Eb
1D26A
1.82193
1351
4945
E
1E5D9
1.89784
128C
4748
1E54D
1.89571
1291
4753
F
20630
2.02437
1163
4451
20228
2.00842
1186
4486
F#
22294
2.13507
107C
4220
220BB
2.12785
108A
4234
Gb
228C9
2.15932
1040
4173
G
24704
2.27740
F74
3956
2411F
2.25438
F9D
3997
G#
25F4F
2.37230
ED6
3798
26370
2.38843
EBC
3772
Ab
26DE3
2.42924
E7D
3709
A
287CC
2.53046
DE9
3561
287CC
2.53046
DE9
3561
Bbb
28F28
2.55920
DCl
3521
A#
2A830
2.65698
D3F
3391
2AE51
2.68092
021
3361
Bb
2B2FC
2.69916
DOA
3338
B
2D8C6
2.84677
C5D
3165
20721
2.84035
C64
3172
Middle C
c
3095B
3.03654
B97
2967
3025D
3.00923
BB2
2994
C#
333DE
3.20261
AFD
2813
3302C
3.18817
BOA
2826
Db
33D2E
3.23898
ADE
2782
D
36A87
3.41612
A4E
2638
360B5
3.37776
A6C
2668
Ebb
37476
3.45493
A30
2608
D#
38EF7
3.55846
9E4
2532
39420
3.57861
906
2518
Eb
3A4D4
3.64386
9A9
2473
E
3CBB2
3.79568
946
2374
3CA99
3.79140
949
2377
F
40C7A
4.04874
8Bl
2225
40450
4.01685
8C3
2243
F#
44528
4.27014
83E
2110
44176
4.25571
845
2117
Gb
45193
4.31865
826
2086
G
48E09
4.55482
7BA
1978
4823E
4.50876
7CE
1998
G#
4BE9F
4.74461
76B
1899
4C6El
4.77687
75E
1886
Ab
4DBC5
4.85847
73F
1855
A
50F98
5.06091
6F4
1780
50F98
5.06091
6F4
1780
III-168 SoundDriver

<!-- source-page: 176 -->
## Page 176

Summary
Note
Long
Fixed
Word
Integer
Long
Fixed
Word Integer
Middle C
Bbb
51E4F
5.11839
6EO
1760
A#
55060
5.31396
6AO
1696
55CA2
5.36185
690
1680
Bb
565F8
5.39832
685
1669
B
5B18B
5.69353
62F
1583
5AE41
5.68068
632
1586
1 octave above middle C
c
612B7
6.07310
sec
1484
604BB
6.01848
5D9
1497
C#
667BD
6.40523
57F
1407
66059
6.37636
585
1413
Db
67A5C
6.47797
56F
1391
D
6D50D
6.83223
527
1319
6C169
6.75551
536
1334
Ebb
6E8EB
6.90984
518
1304
D#
71DEE
7.11691
4F2
1266
7283F
7.15721
4EB
1259
Eb
749A8
7.28772
4D4
1236
E
79764
7.59137
4A3
1187
79533
7.58281
4A4
1188
F
818F3
8.09746
459
1113
808Al
8.03371
462
1122.
F#
88A51
8.54030
41F
1055
882EC
8.51141
423
1059
Gb
8A326
8.63730
413
1043
G
91C12
9.10965
3DD
989
9047D
9.01753
3E7
999
G#
97D3D
9.48921
3B6
950
98DC2
9.55374
3AF
943
Ab
9B78B
9.71696
39F
927
A
AlF30
10.12183
37A
890
A1F30
10.12183
37A
890
Bbb
A3C9F
10.23680
370
880
A#
AAOBF 10.62791
350
848
AB945
10.72371
348
840
Bb
ACBEF 10.79662
343
835
B
B6316
11.38705
317
791
B5C83
11.36137
319
793
2 octaves above middle C
c
C256D
12.14619
2E6
742
C0976
12.03696
2ED
749
C#
CCF79 12.81044
2BF
703
CCOBl
12.75270
2C3
707
Db
CF4B9 12.95595
2B7
695
D
DAAlB
13.66447
293
659
D82D2
13.51102
29B
667
Ebb
DD1D6
13.81967
28C
652
D#
E3BDC 14.23383
279
633
E507E
14.31442
275
629
Eb
E9350
14.57544
26A
618
E
F2EC8
15.18274
251
593
F2A65
15.16560
252
594
F
1031E7
16.19493
22C
556
101141
16.06740
231
561
F#
1114Al
17.08058
210
528
1105D8
17.02283
211
529
Gb
11464C
17.27460
20A
522
G
123824
18.21930
lEF
495
1208F9
18.03505
LF4
500
G#
12FA7B
18.97844
IDB
475
131B83
19.10747
1D8
472
Ab
136F15 19.43391
lDO
464
A
143E61
20.24367
lBD
445
143E61
20.24367
lBD
445
Bbb
147930 20.47359
1B8
440
A#
15417F 21.25584
1A8
424
15728A
21.44742
1A4
420
Bb
15970E 21.59323
lAl
417
B
16C620
22.77412
18C
396
16B906
22.72275
180
397
Sound Driver III-169

<!-- source-page: 177 -->
## Page 177

Inside Macintosh
Note
Long
Fixed
3 octaves above middle C
C
184ADA 24.29239
C#
199EF2 25.62088
Db
19E971 25.91188
D
1B5436
27.32895
Ebb
1BA3AC
27 .63934
D#
1C77B8
28.46765
Eb
1D26AO 29.15088
E
1E5D91
30.36549
F
2063CE
32.38986
F#
222943 34.16118
Gb
228C97
34.54918
G
247047
36.43858
G#
25F4F5
37.95686
Ab
26DE2A 38.86783
A
287CC1
40.48732
Bbb
28F27A
40.94717
A#
2A82FE 42.51169
Bb
2B2FBD 43.18648
B
2D8C59
45.54823
Word
173
160
15C
14A
146
13D
135
129
116
108
105
F7
ED
E8
DF
DC
D4
DI
C6
Integer
Long
Fixed
Word Integer
371
1812EB
24.07390
352
198163
25.50542
348
330
1B05A5
27 .02205
326
317
lCAOFD
28.62886
309
297
1E54CB
30.33122
278
202283
32.13481
264
220BAF
34.04564
261
247
2411F2
36.07010
237
263706
38.21494
232
223
287CC1
40.48732
220
212
2AE513
42.89482
209
198
2D720B
45.44548
176
161
14D
13B
129
118
109
FA
EC
DF
D2
C6
374
353
333
315
297
280
265
250
236
223
210
198
The following table gives the ratios used in calculating the above values. It shows the
relationship between the notes making up the just-tempered scale in the key of C; should you
need to implement a just-tempered scale in some other key, you can do so as follows: First get
the value of the root note in the proper octave in the equal-tempered scale (from the above table).
Then use the following table to determine the values of the intervals for the other notes in the key
by multiplying the ratio by the root note.
Chromatic
interval
0
1
2
3
4
5
6
7
Note
c
C#
Db
D
D
Ebb
D#
Eb
E
F
F#
Gb
G
III-170 Sowui Driver
Just-tempered
frequency ratio
1.00000
1.05469
1.06667
1.11111
1.12500
1.13778
1.17188
1.20000
1.25000
1.33333
1.40625
1.42222
1.50000
Equal-tempered
frequency ratio
1.00000
1.05946'
1.12246
1.18921
1.25992
1.33484
1.41421
1.49831
Interval type
Unison
Minor second as chromatic
semitone
Minor second as diatonic
semitone
Major second as minor tone
Major second as major tone
Diminished third
Augmented second
Minor third
Major third
Fourth
Tritone as augmented fourth
Tritone as diminished fifth
Fifth

<!-- source-page: 178 -->
## Page 178

Summary
Chromatic
Just-tempered
Equal-tempered
interval
Note
frequency ratio
frequency ratio
Interval type
8
G#
1.56250
1.58740
Augmented fifth
Ab
1.60000
Minor sixth
9
A
1.66667
1.68179
Major sixth
Bbb
1.68560
Diminished seventh
10
A#
1.75000
1.78180
Augmented sixth
Bb
1.77778
Minor seventh
11
B
1.87500
1.88775
Major seventh
12
c
2.00000
2.00000
Octave
Sound Driver ll!-171

<!-- source-page: 179 -->
## Page 179

Inside Macintosh
STANDARD FILE PACKAGE
Constants
CONST { SFPutFile dialog template · Io )
putDlgID = - 3999;
{ Item numbers of enabled items in SFPutFile di alog )
put Save
= l;
{Save button)
put Cancel = 2;
{Cancel button)
putEject
= 5;
{Eject button)
putDrive
= 6;
{Drive button)
put Name
= 7;
{editText item for file name )
{ SFGetFile dialog template ID )
getDlgID = - 4000;
{ Item numbers of enabled items i n SFGetFile dialog )
get Open
= l;
{Open button)
get Cancel = 3;
{Cancel butt on)
getEject
= 5;
{Eject button)
getDrive
= 6;
{Drive button)
getNmList = 7;
{useritem for file name list)
get Scroll = 8;
{useritem for scroll bar)
Data Types
TYPE SFReply = RECORD
good:
BOOLEAN;
copy :
BOOLEAN;
fType:
OSType;
vRefNum: INTEGER;
version:
fName:
END;
INTEGER;
STRING[63]
{FALSE if ignore corranand)
{not used)
{file type or not used )
{volume reference number)
{file's version number)
{file name)
SFTypeList = ARRAY[0 .. 3] OF OSType;
111-172 Standard File Package

<!-- source-page: 180 -->
## Page 180

Summary
Routines
PROCEDURE SFPutFile
(where: Point; prompt: Str255; origName : Str255;
dlgHook: ProcPtr; VAR reply : SFReply);
PROCEDURE SFPPutFile
(where : Point; prompt: Str255; origName : Str255;
dlgHook: ProcPtr; VAR reply: SFReply; dl gID :
INTEGER; filterProc: ProcPtr);
PROCEDURE SFGetFile
(where: Point; prompt: Str255; fileFilter : ProcPtr;
numTypes : INTEGER; typeList : SFTypeList; dl gHook :
ProcPtr; VAR reply : SFReply);
PROCEDURE SFPGetFile
(where: Point; prompt: Str255; fileFilter : ProcPtr;
numTypes: INTEGER; typeList: SFTypeList; dlgHook :
ProcPtr; VAR reply: SFReply; dlgID : INTEGER;
filterProc: ProcPtr);
DlgHook Function
FUNCTION MyDlg (item: INTEGER; theDialog: DialogPtr)
I NTEGER;
FileFilter Function
FUNCTION MyFileFilter (paramBlock: ParmBlkPtr)
BOOLEAN;
Standard SFPutFile Items
Item number
Item
Standard display rectangle
Save button
(12,74)(82,92)
2
Cancel button
(114,74)(184,92)
3
Prompt string (statText)
( 12, 12)( 184,28)
4
Userltem for disk name
(209, 16)(295,34)
5
Eject button
(21 7 ,43 )(287 ,61)
6
Drive button
(217,74)(287,92)
7
EditText item for file name
( 14,34)(182,50)
8
Userltem for dotted line
(200, 16)(201,88)
Standard File Package llI-173

<!-- source-page: 181 -->
## Page 181

Inside Macintosh
Resource IDs of SFPutFile Alerts
Alert
Disk not found
System error
Existing file
Locked disk
Resource ID
-3994
-3995
-3996
-3997
Standard SFGetFile Items
Item number
Item
1
Open button
2
Invisible button
3
Cancel button
4
U serltem for disk name
5
Eject button
6
Drive button
7
Userltem for file name list
8
Userltem for scroll bar
9
Userltem for dotted line
10
Invisible text (statText)
Assembly-Language Information
Constants
; SFPutFile dialog template ID
putDlgID
.EQU
-3999
Standard display rectangle
( 152,28)(232,46)
(1152,59)(1232,77)
( 152,90)(232, 108)
(248,28)(344,46)
(256,59)(336,77)
(256,90)(336, 108)
( 12, 11)(125' 125)
(124,11)(140,125)
(244,20)(245,116)
(1044,20)(1145,116)
; Item numbers of enabled items in SFPutFile dialog
put Save
.EQU
1
;Save button
put Cancel
.EQU
2
;Cancel button
putEject
.EQU
5
;Eject button
putDrive
.EQU
6
;Drive button
put Name
.EQU
7
;edit Text item for file name
; SFGetFile dialog template ID
getDlgID
.EQU
-4000
III-174 Standard File Package

<!-- source-page: 182 -->
## Page 182

; I tem number s of enabled items in SFGetFile dialog
get Open
.EQU
1
;Open button
get Cancel
.EQU
3
;Cancel button
getEject
.EQU
5
;Eject button
getDrive
.EQU
6
;Drive button
getNmList
.EQU
7
;useritem for file name list
get Scroll
.EQU
8
;useritem for scroll bar
; Routine selectors
sfPutFile
.EQU
1
sfGetFile
.EQU
2
sf PPutFile
.EQU
3
sf PGetFile
.EQU
4
Reply Record Data Structure
rGood
trype
rVolume
rVersion
rName
0 if ignore command (byte)
File type (long)
Volume reference number (word)
File's version number (word)
File name (length byte followed by up to 63 characters)
Trap Macro Name
Pack3
Variables
Summary
SFSaveDisk
Negative of volume reference number used by Standard File Package (word)
Standard File Package Ill-175

<!-- source-page: 183 -->
## Page 183

Inside Macintosh
SYSTEM ERROR HANDLER
Routines
PROCEDURE SysError (errorCode: INTEGER);
User Alerts
ID
Explanation
1
Bus error: Invalid memory reference; happens only on a Macintosh XL
2
Address error: Word or long-word reference made to an odd address
3
Illegal instruction: The MC68000 received an instruction it didn't recognize.
4
:zero divide: Signed Divide (DIVS) or Unsigned Divide (DIVU) instruction with a
divisor of 0 was executed.
5
Check exception: Check Register Against Bounds (CHK) instruction was executed
and failed. Pascal "value out of range" errors are usually reported in this way.
6
TrapV exception: Trap On Overflow (TRAPV) instruction was executed and failed.
7
Privilege violation: Macintosh always runs in supervisor mode; perhaps an erroneous
Return From Execution (RTE) instruction was executed.
8
Trace exception: The trace bit in the status register is set.
9
Line 1010 exception: The 1010 trap dispatcher has failed.
10
Line 1111 exception: Unimplemented instruction
11
Miscellaneous exception: All other MC68000 exceptions
12
Unimplemented core routine: An unimplemented trap number was encountered.
13
Spurious interrupt: The interrupt vector table entry for a particular level of interrupt is
NIL; usually occurs with level 4, 5, 6, or 7 interrupts.
14
1/0 system error: The File Manager is attempting to dequeue an entry from an 1/0
request queue that has a bad queue type field; perhaps the queue entry is unlocked. Or,
the dCtlQHead field was NIL during a Fetch or Stash call. Or, a needed device control
entry has been purged.
15
Segment Loader error: A GetResource call to read a segment into memory failed.
16
Floating point error: The halt bit in the floating-point environment word was set.
17-24 Can't load package: A GetResource call to read a package into memory failed.
25
Can't allocate requested memory block in the heap
26
Segment Loader error: A GetResource call to read 'CODE' resource 0 into memory
failed; usually indicates a nonexecutable file.
///-176 System Error Handler

<!-- source-page: 184 -->
## Page 184

Summary
27
File map destroyed: A logical block number was found that's greater than the number
of the last logical block on the volume or less than the logical block number of the first
allocation block on the volume.
28
Stack overflow error: The stack has expanded into the heap.
30
"Please insert the disk:" File Manager alert
41
The file named "Finder" can't be found on the disk.
100
Can't mount system startup volume. The system couldn't read the system resource file
into memory.
32767 "Sorry, a system error occurred": Default alert message
System Startup Alerts
"Welcome to Macintosh"
"Disassembler installed"
"MacsBug installed"
"Warning-this startup disk is not usable"
Assembly-Language Information
Constants
; System error IDs
dsBusError
.EQU
1
;bus error
dsAddressErr
. EQU
2
;address error
dsilli nstErr
. EQU
3
;illegal instruction
dsZeroDivErr
.EQU
4
; zero divide
dsChkErr
.EQU
5
; check exception
dsOvf lowErr
. EQU
6
;trapV exception
dsPri vErr
.EQU
7
;pr ivilege violation
dsTraceErr
. EQU
8
;trace exception
dsLineAErr
.EQU
9
;line 1010 exception
dsLineFErr
.EQU
10
; l ine 1111 exception
dsMi scErr
.EQU
11
;miscell aneous exception
dsCoreErr
. EQU
12
;unimplemented core routi ne
dsirqErr
.EQU
13
;spurious inter rupt
dsIOCoreErr
.EQU
14
;I/O system error
dsLoadEr r
.EQU
15
;Segment Loader error
dsFPErr
.EQU
16
;floating point error
dsNoPackErr
.EQU
17
;can ' t load package 0
dsNoPkl
.EQU
18
;can ' t l oad package 1
dsNoPk2
.EQU
19
;can ' t load package 2
dsNoPk3
.EQU
20
;can't load package 3
dsNoPk4
.EQU
21
; can't load package 4
dsNoPkS
.EQU
22
; can ' t load package 5
dsNoPk6
.EQU
23
;can ' t load package 6
System Error Handler /11-177

<!-- source-page: 185 -->
## Page 185

Inside Macintosh
dsNoPk7
dsMernFullErr
dsBad.Launch
dsFSErr
dsStkNHeap
dsReinsert
dsSysErr
Routines
Trap macro
_SysError
Variables
DSErrCode
DSAlertTab
DSAlertRect
.EQU
24
;can ' t load package 7
.EQU
25
;can ' t allocate requested block
.EQU
26
;Segment Loader error
.EQU
27
;file map destroyed
.EQU
28
;stack overflow error
.EQU
30
;"Please insert the disk:"
.EQU
32767
;undifferentiated system error
On entry
On exit
DO: errorCode (word)
All registers changed
Current system error ID (word)
Pointer to system error alert table in use
Rectangle enclosing system error alert (8 bytes)
l//-178 System Error Handler

<!-- source-page: 186 -->
## Page 186

TEXTEDIT
Constants
CONST { Text justification
teJustLeft
O;
teJustCenter
l;
teJustRight
-1;
Data Types
TYPE TEHandle = "TEPtr;
TEPtr
= "TERec;
TERec = RECORD
destRect:
Rect;
{destination rectangle}
viewRect:
Rect;
{view rectangle}
selRect:
Rect;
{used from assembly language}
lineHeight
INTEGER;
{for l ine spacing
fontAscent: INTEGER;
{caret/highlighting position}
selPoint:
Point;
{used from assembly language}
selStart:
INTEGER;
{start of selection range}
selEnd:
INTEGER;
{end of selection range
active:
INTEGER;
{used internally}
word.Break :
ProcPtr;
{for word break routine}
cli kLoop:
ProcPtr;
{for click loop routine}
clickTime:
LONGINT;
{used internally}
clickLoc:
INTEGER;
{used internally}
caretTime :
LONGINT;
{used internally}
caretState : INTEGER;
{used internally}
just:
INTEGER;
{justification of text}
teLength :
INTEGER;
{length of text}
hText:
Handle;
{text to be edited}
recalBack:
INTEGER;
{used internally}
recalLines: INTEGER;
{used internally}
clikStuff :
INTEGER;
{used internally}
Summary
crOnly:
INTEGER;
{if <0 , new line at Return only}
txFont:
INTEGER;
{text font}
txFace:
Style;
{character style}
txMode :
INTEGER;
{pen mode}
txSize:
INTEGER;
{font size}
inPort:
Graf Pt r;
{ graf Port}
highHook:
ProcPtr;
{used from assembly language}
caretHook:
ProcPtr;
{used from assembly language}
nLines:
INTEGER;
{number of lines }
lineStarts: ARRAY[0 .. 16000) OF INTEGER
{positions of line starts}
END;
TextEdit J!I-179

<!-- source-page: 187 -->
## Page 187

Inside Macintosh
Chars Handle = "'CharsPtr;
CharsPtr
= "'Chars;
Chars
=PACKED ARRAY[O • • 32000] OF CHAR;
Routines
Initialization and Allocation
PROCEDURE TEinit;
FUNCTION
TENew
(destRect,viewRect: Rect)
TEHandle;
PROCEDURE TEDispose (hTE: TEHandle);
Accessing the Text of an Edit Record
PROCEDURE TESetText (text: Ptr; length: LONGINT; hTE : TEHandle) ;
FUNCTION
TEGetText (hTE: TEHandle) : CharsHandle;
Insertion Point and Selection Range
PROCEDURE TEidle
(hTE: TEHandle);
PROCEDURE TEClick
(pt: Point; extend: BOOLEAN; hTE : TEHandle);
PROCEDURE TESetSelect
(selStart, selEnd: LONGINT; hTE: TEHandle);
PROCEDURE TEActivate
(hTE: TEHandle);
PROCEDURE TEDeactivate
(hTE: TEHandle);
Editing
PROCEDURE TEKey
PROCEDURE TECut
PROCEDURE TECopy
PROCEDURE TEPaste
PROCEDURE TEDelete
PROCEDURE TEinsert
(key: CHAR; hTE: TEHandl e );
(hTE: TEHandle);
(hTE : TEHandle);
(hTE : TEHandle);
(hTE: TEHandle) ;
(text: Ptr; length: LONGINT; hTE: TEHandle);
Text Display and Scrolling
PROCEDURE TESetJust
PROCEDURE TEUpdate
PROCEDURE TextBox
(just : INTEGER; hTE: TEHandle);
(rUpdate: Rect; hTE: TEHandle);
(text: Ptr; length: LONGINT; box: Rect; just :
INTEGER);
PROCEDURE TEScroll
(dh, dv: INTEGER; hTE: TEHandle);
III-180 TextEdit

<!-- source-page: 188 -->
## Page 188

Scrap Handling [Not in ROM]
FUNCTION
TEFrornScrap
OSErr;
FUNCTION
TEToScrap
OSErr;
FUNCTION
TEScrapHandle
Handle;
FUNCTION
TEGetScrapLen
LONGINT;
PROCEDURE TESetScrapLen
(l ength: LONGINT);
Advanced Routines
PROCEDURE SetWord.Br eak (wBrkProc: ProcPtr; hTE : TEHandle);
PROCEDURE SetClikLoop
(clikProc : ProcPtr; hTE: TEHandle);
PROCEDURE TECal Text
(hTE: TEHandl e);
Word Break Routine
Summary
[Not in ROM]
[Not in ROM]
FUNCTION MyWord.Break (text : Ptr; charPos: INTEGER)
BOOLEAN;
Click Loop Routine
FUNCTION MyClikLoop : BOOLEAN;
Assembly-Language Information
Constants
; Text justification
teJustLeft
teJustCenter
teJustRight
.EQU
.EQU
.EQU
0
1
-1
Edit Record Data Structure
teDestRect
teViewRect
teSelRect
teLineHite
teAscent
teSelPoint
teSelStart
teSe!End
teWordBreak
teClikProc
teJust
Destination rectangle (8 bytes)
View rectangle (8 bytes)
Selection rectangle (8 bytes)
For line spacing (word)
Caret/highlighting position (word)
Point selected with mouse (long)
Start of selection range (word)
End of selection range (word)
Address of word break routine (see below)
Address of click loop routine (see below)
Justification of text (word)
TextEdit l!!-181

<!-- source-page: 189 -->
## Page 189

Inside Macintosh
teLength
teTextH
teCROnly
teFont
teFace
tcMode
teSize
teGrafPort
teHiHook
teCarHook
teNLines
teLines
teRecSize
Length of text (word)
Handle to text
If <0, new line at Return only (byte)
Text font (word)
Character style (word)
Pen mode (word)
Font size (word)
Pointer to grafPort
Address of text highlighting routine (see below)
Address of routine to draw caret (see below)
Number of lines (word)
Positions of line starts (teNLines*2 bytes)
Size in bytes of edit record except teLines field
Word break routine
On entry
On exit
Click loop routine
On exit
AO:
pointer to text
DO:
character position (word)
Z condition code: 0 to break at specified character
1 not to break there
DO:
1
D2:
must be preserved
Text highlighting routine
On entry
A3:
pointer to locked edit record
Caret drawing routine
On entry
Variables
TEScrpHandle
TEScrpLength
TERecal
IBDoText
TERecal routine
On entry
On exit
III-182 TextEdit
A3:
pointer to locked edit record
Handle to TextEdit scrap
Size in bytes ofTextEdit scrap (word)
Address of routine to recalculate line starts (see below)
Address of multi-purpose routine (see below)
A3:
pointer to locked edit record
D7:
change in length of edit record (word)
D2:
line start of line containing first character to be redrawn (word)
D3:
position of first character to be redrawn (word)
D4:
position oflast character to be redrawn (word)

<!-- source-page: 190 -->
## Page 190

TEDoText routine
On entry
On exit
A3:
pointer to locked edit record
D3:
position of first character to be redrawn (word)
D4:
position of last character to be redrawn (word)
D7:
(word)
0 to hit-test a character
1 to highlight selection range
- 1 to display text
- 2 to position pen to draw caret
AO:
pointer to current grafPort
DO: if hit-testing, character position or-1 for none (word)
Summary
TextEdit Ill-183

<!-- source-page: 191 -->
## Page 191

Inside Macintosh
UTILITIES, OPERATING SYSTEM
Constants
CONST { Values returned by Environs procedure
macXLMachine
macMachine
{ Result codes
clkRdErr
clkWrErr
memFullErr
memWZErr
nilHandleErr
no Err
prinitErr
prWrErr
qErr
Data Types
0;
l;
}
-85;
- 86;
-108;
-111;
- 109;
0;
-88;
-87;
-1;
{Macintosh XL}
{Macintosh 128K or 512K}
{unable to read clock}
{time written did not verify}
{not enough room in heap zone}
{attempt to operate on a free block}
{NIL master pointer}
{no error}
{validity status is not $A8}
{parameter RAM written did not verify}
{entry not in specified queue}
TYPE OSType = PACKED ARRAY [ 1 .. 4] OF CHAR;
OSErr = INTEGER;
SysPPtr
SysParmType
"SysParmType;
RECORD
valid:
Byte;
aTalkA:
Byte;
aTalkB:
Byte;
conf ig:
Byte;
portA:
INTEGER;
portB :
I NTEGER;
alarm:
LONGINT;
font :
INTEGER;
kbdPrint: INTEGER;
volClik:
INTEGER;
{validity status }
{AppleTalk node ID hint for modem port}
{AppleTalk node ID hint for printer port}
{use types for serial ports}
{modem port configuration}
{printer port configuration}
{alarm setting}
{application font number minus 1}
{auto- key settings, printer connection}
{speaker volume, double-click, caret blink}
misc:
INTEGER
{mouse scaling, startup disk, menu blink)
END;
QHdrPtr
QHdr
"QHdr;
RECORD
qFlags:
INTEGER;
qHead:
QElemPtr;
qTail :
QElemPtr
END;
III-184 Utilities, Operating System
{queue flags }
{first queue entry)
{last queue entry}

<!-- source-page: 192 -->
## Page 192

Summary
QTypes
(durrunyType,
vType,
ioQType ,
drvQType,
evType,
fsQType);
{vertical retrace queue type}
{file I/0 or driver I/O queue type } .
{drive queue type}
{event queue type}
{volume-control-block queue type}
QElemPtr = "QElem;
QEl em
RECORD
CASE QTypes OF
vType:
ioQType:
drvQType:
evType:
fsQType:
(vblQElem :
(ioQElem:
(drvQElem:
(evQElem:
(vcbQElem:
END;
DateTimeRec =
RECORD
VBLTask);
ParamBlockRec) ;
DrvQEl);
EvQEl);
VCB)
(1904 to 2040}
year:
month:
day:
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER
(1 to 12 for January to December}
{l to 31}
Routines
hour:
minute:
second:
dayOfWeek:
END;
Pointer and Handle Manipulation
FUNCTION HandToHand
(VAR theHndl:
FUNCTION PtrToHand
(srcPtr: Ptr;
OSErr;
FUNCTION PtrToXHand (srcPtr: Ptr;
OSErr;
(0 to 23}
(0 to 59}
{O to 59}
{l to 7 for Sunday to Saturday}
Handl e)
: OSErr;
VAR dstHndl: Handle; size : LONG INT)
dstHndl: Handle; size: LONGINT)
:
FUNCTION HandAndHand (aHndl , bHndl: Handle) : OSErr;
FUNCTION PtrAndHand (pntr: Ptr; hndl: Handle; size : LONGINT)
OSErr;
String Comparison
FUNCTION
EqualString (aStr,bStr: Str255; caseSens , diacSens: BOOLEAN)
BOOLEAN;
PROCEDURE UprString
(VAR theString: Str255; diacSens : BOOLEAN);
Utilities, Operating System /1/-185

<!-- source-page: 193 -->
## Page 193

Inside Macintosh
Date and Time Operations
FUNCTION
Read.DateTime
PROCEDURE GetDateTime
(VAR secs: LONGINT) : OSErr;
(VAR secs: LONG INT) ;
[Not in ROM]
FUNCTION
SetDateTime
PROCEDURE Date2Secs
PROCEDURE Secs2Date
PROCEDURE GetTime
PROCEDURE SetTime
(secs: LONGINT) : OSErr;
(date: DateTimeRec; VAR secs: LONGINT);
(secs: LONGINT; VAR date: DateTimeRec);
(VAR date: DateTimeRec) ;
[Not in ROM]
(date: DateTimeRec);
[NotinROM]
Parameter RAM Operations
FUNCTION InitUtil :
OSErr;
FUNCTION GetSysPPtr
SysPPt r;
[Not in ROM]
FUNCTION WriteParam
OSErr;
Queue Manipulation
PROCEDURE Enqueue (qEntry: QElemPtr; theQueue: QHdrPtr);
FUNCTION
Dequeue (qEntry: QElemPtr; theQueue: QHdrPtr) : OSErr;
Trap Dispatch Table Utilities
PROCEDURE SetTrapAddress (trapAddr: LONGINT; trapNum : INTEGER);
FUNCTION
GetTrapAddress (trapNum: INTEGER) : LONGINT;
Miscellaneous Utilities
PROCEDURE Delay
PROCEDURE SysBeep
PROCEDURE Environs
PROCEDURE Restart;
PROCEDURE SetUpA5;
PROCEDURE RestoreA5;
(numTicks: LONGINT; VAR finalTic ks: LONGINT) ;
(duration: INTEGER);
(VAR rom,rnachine: INTEGER);
[NotinROM]
[Not in ROM]
[Not in ROM]
[Not in ROM]
Default Parameter RAM Values
Parameter
Validity status
Node ID hint for modem port
Node ID hint for printer port
Use types for serial ports
Modem port configuration
Default value
$A8
0
0
0 (both ports)
9600 baud, 8 data bits, 2 stop bits, no parity
///-186 Utilities, Operating System

<!-- source-page: 194 -->
## Page 194

Parameter
Printer port configuration
Alarm setting
Application font number minus 1
Auto-key threshold
Auto-key rate
Printer connection
Speaker volume
Double-click time
Caret-blink time
Mouse scaling
Preferred system startup disk
Menu blink
Default value
Same as for modem port
0 (midnight, January 1, 1904)
2 (Geneva)
6 (24 ticks)
3 (6 ticks)
0 (printer port)
3 (medium)
8 (32 ticks)
8 (32 ticks)
1 (on)
0 (internal drive)
3
Assembly-Language Information
Constants
; Result codes
clkRdErr
.EQU
-85
;unable to read clock
clkWrErr
.EQU
- 86
;time written did not verify
memFullErr
.EQU
-108
;not enough room in heap zone
memWZErr
.EQU
-111
;attempt to operate on a free
nilHandleErr
.EQU
-109
;NIL master pointer
no Err
.EQU
0
;no error
prinitEr r
.EQU
-88
;validity status is not $A8
prWrErr
.EQU
-87
;parameter RAM written did not
qErr
.EQU
-1
;entry not in specified queue
; Queue types
vType
.EQU
1
;vertical retrace queue type
block
verify
ioQType
.EQU
2
;file I/0 or driver I/0 queue type
drvQType
.EQU
3
;drive queue type
evType
.EQU
4
;event queue type
fsQType
.EQU
5
;volume-control- block queue type
Queue Data Structure
qFlags
qHead
qTail
Queue flags (word)
Pointer to first queue entry
Pointer to last queue entry
Summary
Utilities, Operating System III-187

<!-- source-page: 195 -->
## Page 195

Inside Macintosh
Date/Time Record Data Structure
dtYear
dtMonth
dtDay
dtHour
dtMinute
dtSecond
dtDayOfWeek
Routines
Trap macro
HandToHand
_PuToHand
PuToXHand
_ HandAndHand
_ PtrAndHand
_CmpString
_UprString
_ ReadDateTime
SetDateTime
Date2Secs
Secs2Date
InitUtil
WriteParam
1904 to 2040 (word)
1 to 12 for January to December (word)
1 to 31 (word)
0 to 23 (word)
0 to 59 (word)
0 to 59 (word)
1 to 7 for Sunday to Saturday (word)
On entry
AO: theHndl (handle)
AO: srcPtr (ptr)
DO: size (long)
AO: srcPtr (ptr)
A 1: dstHndl (handle)
DO: size (long)
AO: aHndl (handle)
Al: bHndl (handle)
AO: pntr (ptr)
A 1: hndl (handle)
DO: size (long)
On exit
AO: theHndl (handle)
DO: result code(word)
AO: dstHndl (handle)
DO: result code (word)
AO: dstHndl (handle)
DO: result code (word)
AO: bHndl (handle)
DO: result code (word)
AO: hndl (handle)
DO: result code (word)
_CmpString ,MARKS sets bit 9, for diacSens=FALSE
_CmpString ,CASE sets bit 10, for caseSens=TRUE
_CmpString ,MARKS,CASE sets bits 9 and 10
AO: ptr to first string
DO: 0 if equal, I if
Al: ptr to second string
not equal (long)
DO: high word: length of
first string
low word: length of
second string
_UprString ,MARKS sets bit 9, for diacSens=FALSE
AO: ptr to string
AO: ptr to string
DO: length of string (word)
AO: ptr to long word secs
DO: secs (long)
AO: ptr to date/time record
DO: secs (long)
AO: SysParam (ptr)
DO: MinusOne (long)
AO: ptr to long word secs
DO: result code (word)
DO: result code (word)
DO: secs (long)
AO: ptr to date/time record
DO: result code (word)
DO: result code (word)
III-188 Utilities, Operating System

<!-- source-page: 196 -->
## Page 196

Trap macro
_Enqueue
_Dequeue
On entry
AO: qEntry (ptr)
Al: theQueue (ptr)
AO: qEntry (ptr)
A 1: theQueue (ptr)
On exit
Al: theQueue (ptr)
A 1: theQueue (ptr)
DO: result code (word)
_ GetTrapAddress
_ SetTrapAddress
DO: trapNum (word)
AO: trapAddr (address)
DO: trapNum (word)
AO: address of routine
_Delay
_SysBeep
Variables
SysParam
SPValid
SPATalkA
SPATalkB
SPConfig
SPPortA
SPPortB
SP Alarm
SPFont
SPKbd
SPPrint
SPVolCtl
SPClikCaret
SPMisc2
CrsrThresh
Time
AO: numTicks (long)
stack: duration (word)
DO: finalTicks (long)
Low-memory copy of parameter RAM (20 bytes)
Validity status (byte)
AppleTalk node ID hint for modem port (byte)
AppleTalk node ID hint for printer port (byte)
Use types for serial ports (byte)
Modem port configuration (word)
Printer port configuration (word)
Alarm setting (long)
Application font number minus 1 (word)
Auto-key threshold and rate (byte)
Printer connection (byte)
Speaker volume (byte)
Double-click and caret-blink times (byte)
Mouse scaling, system startup disk, menu blink (byte)
Mouse-scaling threshold (word)
Seconds since midnight, January 1, 1904 (long)
Summary
Utilities, Operating System IIl-189

<!-- source-page: 197 -->
## Page 197

Inside Macintosh
UTILITIES, TOOLBOX
Constants
CONST { Resource ID of standard pattern list )
sysPatListID = O;
{ Resource IDs of standard cursors
1;
{to select text )
2;
{to draw graphics)
iBeamCursor
crossCursor
plusCursor
watchCursor
3;
{to select cells in structured documents)
4;
{to indicate a long wait)
Data Types
TYPE Int64Bit =
RECORD
hiLong: LONGINT;
loLong: LONG INT
END;
CursPtr
"Cursor;
CursHandle
"CursPt r;
PatPtr
"Pattern;
PatHandle
"PatPtr;
Routines
Fixed-Point Arithmetic
FUNCTION Fi xRatio (nurner,denom: INTEGER)
FUNCTION Fi xMul
(a, b: Fixed) : Fixed;
FUNCTION FixRound (x: Fixed) : INTEGER;
String Manipulation
Fixed;
FUNCTION
NewString
PROCEDURE SetString
FUNCTION
GetString
PROCEDURE GetindString
(theString: Str255) : StringHandle;
(h: StringHandle; theString: Str255);
(stringID: INTEGER) : StringHandle;
III-190 Utilities, Toolbox
(VAR theString: Str255; strListID: INTEGER;
index: INTEGER) ;
[Not in ROM]

<!-- source-page: 198 -->
## Page 198

Byte Manipulation
FUNCTION
Munger
(h: Handle; offset: LONGINT; ptrl: Ptr; lenl:
LONGINT; ptr2: Ptr; len2: LONGINT) : LONGINT;
PROCEDURE Pack.Bits
(VAR srcPtr,dstPtr: Ptr; srcBytes: INTEGER);
PROCEDURE UnpackBits (VAR srcPtr,dstPtr: Ptr; dstBytes: INTEGER);
Bit Manipulation
FUNCTION
BitTst (bytePtr: Ptr; bitNum: LONG INT)
: BOOLEAN;
PROCEDURE BitSet (bytePtr: Ptr; bitNum: LONGINT);
PROCEDURE BitClr (bytePtr: Ptr; bitNum: LONGINT);
Logical Operations
FUNCTION BitAnd
FUNCTION BitOr
FUNCTION BitXor
FUNCTION BitNot
FUNCTION BitShift
(valuel,value2: LONGINT)
LONGINT;
(valuel,value2: LONGINT)
LONGINT;
(valuel, value2: LONGINT)
LONGINT;
(value: LONGINT) : LONGINT;
(value: LONGINT; count: INTEGER) : LONGINT;
Other Operations on Long Integers
FUNCTION
HiWord
(x: LONGINT) : INTEGER;
FUNCTION
LoWord
(x: LONGINT) : INTEGER;
PROCEDURE LongMul (a,b: LONGINT; VAR dest: Int64Bit);
Graphics Utilities
Summary
PROCEDURE ScreenRes
FUNCTION Geticon
PROCEDURE Ploticon
FUNCTION GetPattern
PROCEDURE GetindPattern
(VAR scrnHRes, scrnVRes : INTEGER) ;
[Not in ROM]
(iconID: INTEGER) : Handle;
FUNCTION GetCursor
PROCEDURE ShieldCursor
FUNCTION
GetPicture
(theRect: Rect; thereon: Handle);
(patID: INTEGER) : PatHandle;
(VAR thePattern: Pattern; patListID: INTEGER;
index: INTEGER) ;
[Not in ROM]
(cursorID: INTEGER) : CursHandle;
(shieldRect: Rect; offsetPt: Point);
(picID: INTEGER) : PicHandle;
Miscellaneous Utilities
FUNCTION DeltaPoint
(ptA,ptB: Point) : LONGINT;
FUNCTION SlopeFromAngle (angle: INTEGER) : Fixed;
FUNCTION AngleFromSlope (slope: Fixed) : INTEGER;
Utilities, Toolbox III-191

<!-- source-page: 199 -->
## Page 199

Inside Macintosh
Assembly-Language Information
Constants
; Resource ID of standard pattern list
sysPatListID
.EQU
0
; Resource IDs of standard cursors
iBeamCursor
.EQU
1
;to select text
crossCursor
.EQU
2
;to draw graphics
plusCursor
. EQU
3
;to select cells in structured
watchCursor
.EQU
4
;to indicate a l ong wait
Variables
ScrVRes
ScrHRes
Pixels per inch vertically (word)
Pixels per inch horizontally (word)
111-192 Utilities, Toolbox
documents

<!-- source-page: 200 -->
## Page 200

VERTICAL RETRACE MANAGER
Constants
CONST { Result codes
{no error}
noErr
= 0;
qErr
= -1;
vTypErr = -2;
{task entry isn ' t in the queue}
{qType field isn't ORD(vType)}
Data Types
TYPE VBLTask = RECORD
Routines
qLink:
QElernPtr;
qType :
INTEGER;
vblAddr:
ProcPtr;
vblCount: INTEGER;
vblPhase: INTEGER
END;
{next queue entry}
{queue type}
{pointer to task}
{task frequency}
{task phase}
FUNCTION VInstall
FUNCTION VRemove
FUNCTION GetVBLQHdr
(vblTaskPtr: QElemPtr)
(vblTaskPtr: QElemPtr)
QHdrPtr;
[Not in ROM]
OSErr;
OSErr;
Assembly-Language Information
Constants
Summary
inVBL
.EQU
6
;set if Vertical Retrace Manager is executing a task
; Result codes
noErr
.EQU
qErr
.EQU
vTypErr .EQU
0
;no error
-1
;task entry isn ' t in the queue
- 2
;qType field isn't vType
Structure of Vertical Retrace Queue Entry
qLink
qType
vblAddr
vblCount
vblPhase
Pointer to next queue entry
Queue type (word)
Address of task
Task frequency (word)
Task phase (word)
Vertical Retrace Manager lll-193

<!-- source-page: 201 -->
## Page 201

Inside Macinwsh
Routines
Trap macro
Vlnstall
VRemove
Variables
VBLQueue
On entry
On exit
AO: vblTaskPtr (ptr)
DO: result code (word)
AO: vblTaskPtr (ptr)
DO: result code (word)
Vertical retrace queue header ( 10 bytes)
IIJ-1<)4. Vertical Retrace Manager

<!-- source-page: 202 -->
## Page 202

WINDOW MANAGER
Constants
CONST { Window definition IDs }
documentProc
c!BoxProc
plainDBox
altDBoxProc
noGrowDocProc
rDocProc
0;
1;
2 ;
3;
{standard document window}
{alert box or modal dialog box}
{plain box}
{plain box with shadow}
4;
{document window without s i ze box }
16; {rounded- corner window}
{ Window class, in windowKind field of window re cord }
{dialog or alert window}
Summary
dialogKind
userKind
2;
8;
{window created directly by the applicati on}
{ Values returned by FindWindow
inDesk
0;
{none of the following}
inMenuBar
l;
{in menu bar}
inSysWindow
2;
{in system window}
inContent
3;
{in content region (except grow, if active ) }
inDrag
4;
{in drag region}
inGrow
5;
{in grow region (active window only) }
inGoAway
6;
{in go- away region (active wi ndow only) }
{ Axis constraints for DragGrayRgn
noConstraint
hAxisOnly
vAxisOnly
O;
1;
2;
{no constraint}
{horizontal axis only}
{vertical axis only}
{ Messages to window definition function
wDraw
O;
{draw window frame}
wHit
l;
{tell what region mouse button was pressed i n}
wCalcRgns
2;
{calculate strucRgn and contRgn}
wNew
3;
{do any additional window initializat i on}
wDispose
4;
{take any additional disposal actions }
wGrow
5;
{draw window's grow image}
wDrawGicon
6;
{draw size box in content region}
{ Values returned by window definition function's hit routine }
wNoHit
O;
{none of t he following}
winContent
1;
{in content region (except grow, if active) }
winDrag
2;
{in drag region}
winGrow
3;
{in grow region (active window only ) }
winGoAway
4;
{in go-away region (active window only) }
Window Manager JII-195

<!-- source-page: 203 -->
## Page 203

Inside Macintosh
{ Resource ID of desktop pattern }
deskPatID = 16;
Data Types
TYPE WindowPtr
WindowPeek
GrafPtr;
"WindowRecord;
WindowRecord
Routines
RECORD
port:
windowKind:
visible:
hilited:
goAwayFlag:
spareFlag:
strucRgn:
contRgn:
updateRgn:
windowDefProc:
dataHandle:
titleHandle :
titleWidth:
controlList:
nextWindow:
windowPic:
refCon:
END;
Initialization and Allocation
Graf Port;
INTEGER;
BOOLEAN;
BOOLEAN;
BOOLEAN;
BOOLEAN;
RgnHandle;
RgnHandle;
RgnHandle;
Handle;
Handle;
StringHandle;
INTEGER;
ControlHandle;
WindowPeek;
PicHandle;
LONG INT
(VAR wPort: GrafPtr);
{window' s grafPort}
{window class}
{TRUE if visible}
{TRUE if highlighted}
{TRUE if has go-away region }
{reserved f or future use}
{structure region}
{content region}
{update region}
{window definition function}
{data used by windowDefProc}
{window's title}
{width of title in pixels}
{window's control l ist}
{next window in window l ist}
{picture for drawing window}
{window's reference value}
PROCEDURE InitWindows;
PROCEDURE GetWMgrPort
FUNCTION
NewWindow
(wStorage : Ptr; boundsRect: Rect; title : Str255;
visible: BOOLEAN; procID: INTEGER; behind:
WindowPtr; goAwayFlag: BOOLEAN; refCon:
LONGINT) : WindowPtr;
FUNCTION
GetNewWindow
(windowID: INTEGER; wStorage: Ptr; behind:
WindowPtr) : WindowPtr;
PROCEDURE CloseWindow
(theWindow: WindowPtr);
PROCEDURE DisposeWindow
(theWindow: WindowPtr);
III-196 Window Manager

<!-- source-page: 204 -->
## Page 204

Summary
Window Display
PROCEDURE SetWTitle
(theWindow: WindowPtr; title: Str255);
PROCEDURE GetWTitle
(theWindow: WindowPtr; VAR titl e : Str255) ;
PROCEDURE Select Window
(theWindow: WindowPtr);
PROCEDURE Hide Window
(t heWi ndow: WindowPtr) ;
PROCEDURE ShowWindow
(theWindow: WindowPtr);
PROCEDURE ShowHide
(theWindow: WindowPtr; showFlag: BOOLEAN) ;
PROCEDURE HiliteWindow
(theWindow: WindowPtr; fHilite: BOOLEAN) ;
PROCEDURE BringToFront
(theWindow: WindowPtr) ;
PROCEDURE SendBehind
(theWindow,behindWindow: WindowPtr);
FUNCTION
Front Window :
WindowPtr;
PROCEDURE Dr awGrowicon
(theWindow : Wi ndowPtr) ;
Mouse Location
FUNCTION FindWindow
(thePt: Point ; VAR whichWindow: WindowPtr ) :
INTEGER;
FUNCTION TrackGoAway (theWindow: WindowPtr; thePt : Point ) : BOOLEAN;
Window Movement and Sizing
PROCEDURE Move Window (theWindow: WindowPtr; hGlobal, vGloba l : INTEGER;
front : BOOLEAN) ;
PROCEDURE DragWi ndow (theWindow: WindowPtr; startPt : Point ; boundsRect :
Rect);
FUNCTION
GrowWindow (theWindow : WindowPtr; startPt : Point ; sizeRect :
Rect)
: LONGINT;
PROCEDURE Size Window (theWi ndow: WindowPtr; w, h: INTEGER; f Update:
BOOLEAN);
Update Region Maintenance
PROCEDURE I nvalRect
PROCEDURE InvalRgn
PROCEDURE ValidRect
PROCEDURE ValidRgn
PROCEDURE BeginUpdate
PROCEDURE EndUpdate
(badRect : Rect) ;
(badRgn : RgnHandle) ;
(goodRect : Rect );
(goodRgn : RgnHandle);
(theWindow : WindowPtr);
(theWindow: WindowPtr);
Miscellaneous Routines
PROCEDURE SetWRefCon
FUNCTION
GetWRefCon
PROCEDURE SetWindowPic
FUNCTION
GetWindowPic
FUNCTION
PinRect
(theWindow: WindowPtr; data : LONGINT) ;
(theWindow: WindowPtr) : LONGINT;
(theWindow: WindowPtr; pie: Pi cHandl e ) ;
(theWindow: WindowPtr) : PicHandle;
(theRect : Rect; thePt: Point) : LONGI NT;
Window Manager lll-197

<!-- source-page: 205 -->
## Page 205

Inside Macintosh
FUNCTION
DragGrayRgn
(theRgn: RgnHandle; startPt: Point; limitRect,
slopRect: Rect; axis: INTEGER; actionProc:
ProcPtr) : LONGINT;
Low-Level Routines
FUNCTION
CheckUpdate
PROCEDURE ClipAbove
PROCEDURE SaveOld
PROCEDURE DrawNew
PROCEDURE PaintOne
PROCEDURE PaintBehind
PROCEDURE CalcVis
PROCEDURE CalcVisBehind
(VAR theEvent: EventRecord)
BOOLEAN;
(window: WindowPeek);
(window: WindowPeek);
(window: WindowPeek; update: BOOLEAN);
(window: WindowPeek; clobberedRgn: RgnHandle);
(startWindow: WindowPeek; clobberedRgn:
RgnHandle) ;
(window: WindowPeek);
(startWindow: WindowPeek; clobberedRgn:
RgnHandle) ;
Diameters of Curvature for Rounded-Corner Windows
Window definition ID
rDocProc
rDocProc + 1
rDocProc + 2
rDocProc + 3
rDocProc + 4
rDocProc + 5
rDocProc + 6
rDocProc + 7
Diameters of curvature
16, 16
4,4
6, 6
8, 8
10, 10
12, 12
20, 20
24,24
Window Definition Function
FUNCTION MyWindow (varCode: INTEGER; theWindow: WindowPtr; message :
INTEGER; param: LONGINT) : LONGINT;
Assembly-Language Information
Constants
; Window definition IDs
doctunentProc
dBoxProc
plainDBox
.EQU
0
.EQU
1
.EQU
2
III-198 Window Manager
;standard document window
;alert box or modal dialog box
;plain box

<!-- source-page: 206 -->
## Page 206

Summary
altDBoxProc
noGrowDocProc
rDocProc
.EQU
3
.EQU
4
;plain box with shadow
;document window without size box
.EQU
16 ;rounded-comer window
; Window class, in windowKind field of window record
dialogKind
user Kind
.EQU 2
.EQU 8
;dialog or alert window
;window created directly by the application
; Values returned by FindWindow
inDesk
.EQU
0
;none of the following
inMenuBar
.EQU
1
;in menu bar
inSysWindow
.EQU
2
; in system window
inContent
.EQU
3
; in content region (except grow, if active)
inDrag
.EQU
4
;in drag region
inGrow
.EQU 5
;in grow region (active window only)
inGoAway
.EQU
6
;in go-away region (active window only)
; Axis constraints for DragGrayRgn
noConstraint
hAxisOnly
vAxisOnly
.EQU 0
.EQU 1
.EQU 2
;no constraint
;horizontal axis only
;vertical axis only
; Messages to window definition function
wDrawMsg
.EQU
0
;draw window frame
wHitMsg
.EQU
1
;tell what region mouse button was pressed
wCalcRgnMsg
.EQU
2
;calculate strucRgn and contRgn
winitMsg
.EQU
3
; do any additional window initialization
wDisposeMsg
.EQU
4
;take any additional disposal actions
wGrowMsg
.EQU
5
;draw window's grow image
wGiconMsg
.EQU
6
;draw size box in content region
; Value returned by window definition function's hit routine
wNoHit
.EQU
0
;none of the following
winContent
.EQU
1
; in content region (except grow, if active)
winDrag
.EQU
2
; in drag region
winGrow
.EQU
3
; in grow region (active window only)
winGoAway
.EQU
4
;in go-away region (active window only)
; Resource ID of desktop pattern
deskPatID
.EQU 16
Window Record Data Structure
window Port
window Kind
wVisible
wHilited
Window's grafPort (portRec bytes)
Window class (word)
Nonzero if window is visible (byte)
Nonzero if window is highlighted (byte)
in
Window Manager III-199

<!-- source-page: 207 -->
## Page 207

Inside Macintosh
wGoAway
structRgn
contRgn
updateRgn
window Def
wDataHandle
wTitleHandle
wTitle Width
wControlList
next Window
window Pie
wRefCon
window Size
Nonzero if window has go-away region (byte)
Handle to structure region of window
Handle to content region of window
Handle to update region of window
Handle to window definition function
Handle to data used by window definition function
Handle to window's title (preceded by length byte)
Width of title in pixels (word)
Handle to window's control list
Pointer to next window in window list
Picture handle for drawing window
Window's reference value (long)
Size in bytes of window record
Special Macro Names
Pascal name
Cale VisBehind
Dispose Window
Drag Gray Rgn
Variables
Window List
Save Update
Paint White
Cur Activate
CurDeactive
GrayRgn
DeskPattem
DeskHook
WMgrPort
Ghost Window
DragHook
DragPattem
OldStructure
OldContent
SaveVisRgn
Macro name
CalcVBehind
_ Dispos Window
_DragGrayRgn or, after setting the global variable DragPattem,
_ DragTheRgn
Pointer to first window in window list
Flag for whether to generate update events (word)
Flag for whether to paint window white before update event (word)
Pointer to window to receive activate event
Pointer to window to receive deactivate event
Handle to region drawn as desktop
Pattern with which desktop is painted (8 bytes)
Address of procedure for painting desktop or responding to clicks on desktop
Pointer to Window Manager port
Pointer to window never to be considered frontmost
Address of procedure to execute during TrackGoAway, Drag Window,
GrowWindow, and DragGrayRgn
Pattern of dragged region's outline (8 bytes)
Handle to saved structure region
Handle to saved content region
Handle to saved visRgn
l//-200 Window Manager

<!-- source-page: 208 -->
## Page 208

Swnmary
ASSEMBLY LANGUAGE
Variables
OneOne
Minus One
Lo3Bytes
Scratch20
Scratch8
ToolScratch
Appl Scratch
ROMBase
RAMBase
CurrentA5
Hardware
$00010001
$FFFFFFFF
$00FFFFFF
20-byte scratch area
8-byte scratch area
8-byte scratch area
12-byte scratch area reserved for use by applications
Base address of ROM
Trap dispatch table's base address for routines in RAM
Address of boundary between application globals and application parameters
Warning: This information applies only to the Macintosh 128K and 512K, not to the
Macintosh XL.
Constants
; VIA base addresses
vBase
.EQU
$EFE1FE
aVBufB
.EQU
vBase
aVBufA
.EQU
$EFFFFE
aVBufM
.EQU
aVBufB
aVIFR
.EQU
$EFFBFE
a VIER
.EQU
$EFFDFE
; Offsets from vBase
vBufB
.EQU
512*0
vDirB
.EQU
512*2
vDirA
.EQU
512*3
vTlC
.EQU
512*4
vTlCH
.EQU
512*5
vTlL
.EQU
512*6
vTlLH
.EQU
512*7
vT2C
.EQU
512*8
vT2CH
.EQU
512*9
vSR
.EQU
512*10
vACR
.EQU
512*11
vPCR
.EQU
512*12
vIFR
.EQU
512*13
;main base for VIA chip {in variable VIA)
; register B base
;register A base
;register containing mouse signals
;interrupt flag register
;interrupt enable register
;register B {zero offset)
;register B direction register
;register A direction register
;timer 1 counter {low-order byte)
; timer 1 counter {high-order byte)
;timer 1 latch {low-order byte)
;timer 1 latch (high-order byte)
;timer 2 counter {low- order byte)
;timer 2 counter {high-order byte)
;shift register {keyboard)
;auxil iary control register
;peripheral control register
;interrupt flag register
Assembly I..Anguage JJJ-201

<!-- source-page: 209 -->
## Page 209

Inside Macintosh
vIER
vBufA
.EQU
.EQU
512*14
512*15
; VIA register A constants
vAOut
vAinit
vSound
.EQU
.EQU
.EQU
$7F
$7B
7
; VIA register A bit numbers
vSnd.Pg2
.EQU
3
vOverlay
.EQU
4
vHeadSel
.EQU
5
vPage2
.EQU
6
vSCCWReq
.EQU
7
; VIA register B constants
vBOut
.EQU
$87
vBinit
.EQU
$07
; VIA register B bit numbers
rTCData
.EQU
0
rTCClk
.EQU
1
rTCEnb
.EQU
2
vSW
.EQU
3
vX2
.EQU
4
vY2
.EQU
5
vH4
.EQU
6
vSndEnb
.EQU
7
; sec base addresses
sccRBase
sccWBase
.EQU
.EQU
$9FFFF8
$BFFFF9
;interrupt enable register
;register A
;direction register A:
1 bits = outputs
;initial value for vBufA (medium volume)
;sound volume bits
;0 = alternate sound buffer
;1 = ROM overlay (system startup only)
;disk SEL control line
;0 = alternate screen buffer
;SCC wait/request line
;direction register B:
1 bits
;initial value for vBufB
;real-time clock serial data line
;real-time clock data-clock line
;real-time clock serial enable
;O = mouse button is down
;mouse X quadrature level
;mouse Y quadrature level
;1
horizontal blanking
;0 = sound enabled, 1 = disabled
outputs
;SCC base read address (in variable SCCRd)
;SCC base write address (in variable SCCWr)
; Off sets from SCC base addresses
aData
aCtl
bData
bCtl
; Bit
rxBF
txBE
.EQU
.EQU
.EQU
.EQU
numbers for
.EQU
.EQU
6
2
4
0
control
0
2
III-202 Assembly Language
;channel A data in or out
;channel A control
;channel B data in or out
; channe l B control
register RRO
;1
;l
sec receive buffer full
sec send buffer empty

<!-- source-page: 210 -->
## Page 210

; IWM base address
c!Base
.EQU
$DFE1FF
;IWM base address (in variable IWM)
; Offsets from c!Base
phOL
.EQU
512*0
;CAO off (0)
phOH
.EQU
512*1
;CAO on (1)
phlL
.EQU
512*2
;CAl off (0)
phlH
.EQU
512*3
;CAl on (1)
ph2L
.EQU
512*4
;CA2 off (0)
ph2H
.EQU
512*5
;CA2 on (1)
ph3L
.EQU
512*6
; LSTRB off (low)
ph3H
.EQU
512*7
;LSTRB on (high)
mtrOf f
.EQU
512*8
;disk enable off
mtrOn
.EQU
512*9
;disk enable on
intDrive
.EQU
512*10
;select internal drive
extDrive
.EQU
512*11
;select external drive
q6L
.EQU
512*12
;Q6 off
q6H
.EQU
512*13
;Q6 on
q7L
.EQU
512*14
;Q7 off
q7H
.EQU
512*15
;Q7 on
Screen and sound addresses for 512K Macintosh (will also work for
128K, since addresses wrap)
screenLow
.EQU
$7A700
;top left corner of main screen buffer
Swnmary
sound.Low
.EQU
$7FDOO
;main sound buffer (in variable Sounc!Base)
pwmBuffer
ovlyRAM
ovlyScreen
romStart
Variables
ROMBase
SoundBase
SCCRd
SCCWr
IWM
VIA
.EQU
$7FD01
;main disk speed buffer
.EQU
$600000
;RAM start address
.EQU
$67A700
;screen start with
.EQU
$400000
;ROM start address
Base address of ROM
Address of main sound buffer
sec read base address
sec write base address
IWM base address
VIA base address
when overlay
overlay set
(in variable
i s set
ROMBase)
Exception Vectors
Location
$00
$04
$08
Purpose
Reset: initial stack pointer (not a vector)
Reset: initial vector
Bus error
Assembly Language JJJ-203

<!-- source-page: 211 -->
## Page 211

Inside Macintosh
Location
$0C
$10
$14
$18
$1C
$20
$24
$28
$2C
$30-$3B
$3C
$40-$5F
$60
$64
$68
$6C
$70
$74
$78
$7C
$80-$BF
$CO-$FF
Purpose
Address error
Illegal instruction
Divide by zero
CHK instruction
TRAPV instruction
Privilege violation
Trace interrupt
Line 1010 emulator
Line 1111 emulator
Unassigned (reserved)
Uninitialized interrupt
Unassigned (reserved)
Spurious interrupt
VIA interrupt
sec interrupt
VIA+SCC vector (temporary)
Interrupt switch
Interrupt switch + VIA
Interrupt switch + SCC
Interrupt switch + VIA + SCC
TRAP instructions
Unassigned (reserved)
III-204 Assembly Language

<!-- source-page: 212 -->
## Page 212

APPENDIX A: RESULT CODES
This appendix lists all the result codes returned by the Macintosh system software. They're
ordered by value, for convenience when debugging; the names you should actually use in your
program are also listed.
The result codes are grouped roughly according to the lowest level at which the error may occur.
This doesn't mean that only routines at that level may cause those errors; higher-level software
may yield the same result codes. For example, an Operating System Utility routine that calls the
Memory Manager may return one of the Memory Manager result codes. Where a different or
more specific meaning is appropriate in a different context, that meaning is also listed.
Value
0
Name
no Err
Meaning
No error
Operating System Event Manager Error
1
evtNotEnb
Printing Manager Errors
128
- 1
Queuing Errors
- 1
- 2
iPrAbort
iPrSavPFil
qErr
vTypErr
Device Manager Errors
-17
-18
-19
-20
-21
-22
-23
-25
-26
controlErr
statusErr
readErr
writErr
badUnitErr
unitEmptyErr
openErr
dRemovErr
dlnstErr
Event type not designated in system event mask
Application or user requested abort
Saving spool file
Entry not in queue
QType field of entry in vertical retrace queue isn't vType
(in Pascal, ORD(vType))
Driver can't respond to this Control call
Unimplemented control instruction (Printing Manager)
Driver can't respond to this Status call
Driver can't respond to Read calls
Driver can't respond to Write calls
Driver reference number doesn't match unit table
Driver reference number specifies NIL handle in unit table
Requested read/write permission doesn't match driver's
open permission
Attempt to open RAM Serial Driver failed
Attempt to remove an open driver
Couldn't find driver in resource file
Result Codes 111-205

<!-- source-page: 213 -->
## Page 213

Inside Macintosh
-27
-28
abortErr
iIOAbort
notOpenErr
File Manager Errors
- 33
dirFulErr
-34
dskFulErr
- 35
nsvErr
-36
ioErr
-37
bdNamErr
-38
fnOpnErr
-39
eofErr
-40
posErr
-42
tmfoErr
-43
fnfErr
-44
wPrErr
-45
fLckdErr
-46
vLckdErr
-47
fBsyErr
-48
dupFNErr
-49
opWrErr
-50
paramErr
-51
rfNumErr
- 52
gfpErr
-53
volOffLinErr
-54
pennErr
- 55
volOnLinErr
- 56
nsDrvErr
-57
noMacDskErr
-58
extFSErr
III-206 Result Codes
UO request aborted by KillIO
UO abort error (Printing Manager)
Driver isn't open
File directory full
All allocation blocks on the volume are full
Specified volume doesn't exist
UO error
Bad file name or volume name (perhaps zero-length)
File not open
Logical end-of-file reached during read operation
Attempt to position before start of file
Too many files open
File not found
Volume is locked by a hardware setting
File is locked
Volume is locked by a software flag
File is busy; one or more files are open
File with specified name and version number already exists
The read/write permission of only one access path to a file
can allow writing
Error in parameter list
Parameters don't specify an existing volume, and there's
no default volume (File Manager)
Bad positioning information (Disk Driver)
Bad drive number (Disk Initialization Package)
Path reference number specifies nonexistent access path
Error during GetFPos
Volume not on-line
Attempt to open locked file for writing
Specified volume is already mounted and on-line
No such drive; specified drive number doesn't match any
number in the drive queue
Not a Macintosh disk; volume lacks Macintosh-format
directory
External file system; file-system identifier is nonzero, or
path reference number is greater than 1024

<!-- source-page: 214 -->
## Page 214

-59
-60
-61
fsRnErr
badMDBErr
wrPermErr
Low-Level Disk Errors
-64
noDriveErr
-65
offLinErr
-66
noNybErr
-67
noAdrMkErr
-68
dataVerErr
-69
badCksmErr
-70
badBtSlpErr
-71
noDtaMkErr
-72
badDCksum
-73
badDBtSlp
-74
wrUnderrun
-75
cantStepErr
-76
tkOBadErr
-77
initIWMErr
- 78
twoSideErr
-79
spdAdjErr
-80
seekErr
- 81
sectNFErr
Result Codes
Problem during rename
Bad master directory block; must reinitialize volume
Read/write permission doesn't allow writing
Drive isn't connected
No disk in drive
Disk is probably blank
Can't find an address mark
Read-verify failed
Bad address mark
Bad address mark
Can't find a data mark
Bad data mark
Bad data mark
Write underrun occurred
Drive error
Can't find track 0
Can't initialize disk controller chip
Tried to read side 2 of a disk in a single-sided drive
Can't correctly adjust disk speed
Drive error
Can't find sector
Also, to check for any low-level disk error:
-84
-64
firstDskErr
lastDskErr
Clock Chip Errors
-85
clkRdErr
-86
clkWrErr
-87
prWrErr
-88
prlnitErr
First of the range of low-level disk errors
Last of the range of low-level disk errors
Unable to read clock
Time written did not verify
Parameter RAM written did not verify
Validity status is not $A8
Result Codes III-207

<!-- source-page: 215 -->
## Page 215

Inside Macintosh
AppleTalk Manager Errors
-91
-92
-93
-94
-95
-97
-98
ddpSktErr
ddpLenErr
noBridgeErr
lapProtErr
excessCollsns
portlnUse
portNotCf
Scrap Manager Errors
-100
-102
noScrapErr
noTypeErr
Memory Manager Errors
- 108
memFullErr
iMemFullErr
- 109
nilHandleErr
- 111
memWZErr
-112
memPurErr
-117
memLockedErr
Resource Manager Errors
-192
-193
- 194
-196
resNotFound
resFNotFound
addResFailed
rmvResFailed
Additional AppleTalk Manager Errors
-1024
nbpBuffOvr
- 1025
nbpNoConfirm
-1026
nbpConfDiff
-1027
nbpDuplicate
-1028
nbpNotFound
III-208 Result Codes
DDP socket error: socket already active; not a well-known
socket; socket table full; all dynamic socket numbers in use
DDP datagram or ALAP data length too big
No bridge found
ALAP error attaching/detaching ALAP protocol type:
attach error when ALAP protocol type is negative, not in
range, or already in table, or when table is full; detach
error when ALAP protocol type isn't in table
ALAP no CTS received after 32 RTS's, or line sensed in
use 32 times (not necessarily caused by collisions)
Driver Open error, port already in use
Driver Open error, port not configured for this connection
Desk scrap isn't initialized
No data of the requested type
Not enough room in heap zone
Not enough room in heap zone (Printing Manager)
NIL master pointer
Attempt to operate on a free block
Attempt to purge a locked block
Block is locked
Resource not found
Resource file not found
AddResource failed
RmveResource failed
NBP buffer overflow
NBP name not confirmed
NBP name confirmed for different socket
NBP duplicate name already exists
NBP name not found

<!-- source-page: 216 -->
## Page 216

Result Codes
-1029
nbpNISErr
NBP names information socket error
-1096
reqFailed
ATPSndRequest failed: retry count exceeded
-1097
tooManyReqs
ATP too many concurrent requests
-1098
tooManySkts
ATP too many responding sockets
-1099
badATPSkt
ATP bad responding socket
-1100
badBuffNum
ATP bad sequence number
-1101
noRelErr
ATP no release received
-1102
cbNotFound
ATP control block not found
-1103
noSendResp
ATP AddRsp issued before A TPSndRsp
-1104
noDataArea
Too many outstanding ATP calls
-1105
reqAborted
Request aborted
-3101
buf2SmallErr
ALAP frame too large for buffer
DDP datagram too large for buffer
-3102
noMPPError
MPP driver not installed
-3103
cksumErr
DDP bad checksum
-3104
extractErr
NBP can't find tuple in buffer
-3105
readQErr
Socket or protocol type invalid or not found in table
-3106
atpLenErr
ATP response message too large
-3107
atpBadRsp
Bad response from A TPRequest
- 3108
recNotFnd
ABRecord not found
-3109
sktClosedErr
Asynchronous call aborted because socket was closed
before call was completed
Result Codes ///-209

<!-- source-page: 217 -->
## Page 217

Inside Macintosh
III-210

<!-- source-page: 218 -->
## Page 218

APPENDIX B: ROUTINES THAT MAY MOVE OR PURGE
MEMORY
This appendix lists all the routines that may move or purge blocks in the heap. As described in
chapter 1 of Volume II, calling these routines may cause problems if a handle has been
dereferenced. None of these routines may be called from within an interrupt, such as in a
completion routine or a VBL task.
The Pascal name of each routine is shown, except for a few cases where there's no Pascal
interface corresponding to a particular trap; in those cases, the trap macro name is shown instead
(without its initial underscore character).
AddResMenu
Alert
AppendMenu
ATPAddRsp
A TPCloseSocket
A TPGetRequest
ATPLoad
A TPOpenSocket
A TPReqCancel
ATPRequest
ATPResponse
A TPRspCancel
A TPSndRequest
ATPSndRsp
ATPUnload
BeginUpdate
BringToFront
Button
CalcMenuSize
CalcVis
Cale VisBehind
CautionAlert
Chain
ChangedResource
Char Width
Checkltem
Check Update
ClipAbove
ClipRect
CloseDialog
ClosePicture
ClosePoly
ClosePort
CloseResFile
CloseRgn
Close Window
CompactMem
Control
Copy Bits
CopyRgn
CouldAlert
CouldDialog
CreateResFile
DDPCloseSocket
DDPOpenSocket
DDPRdCancel
DDPRead
DDPWrite
DialogSelect
DIBadMount
DiffRgn
DIFonnat
DILoad
DiskEject
DisposDialog
DisposeControl
DisposeMenu
DisposeRgn
Dispose Window
DisposHandle
DisposPtr
DIUnload
DIVerify
DI.Zero
DlgCopy
DlgCut
Dig Delete
DlgPaste
Drag Control
DragGray Rgn
Drag Window
DrawChar
Draw Dialog
DrawGrow Icon
DrawMenuBar
Draw New
Draw Picture
DrawString
DrawText
DriveStatus
Drvrlnstall
DrvrRemove
Eject
Empty Handle
End Update
EraseArc
EraseOval
ErasePoly
EraseRect
EraseRgn
EraseRoundRect
EventAvail
ExitToShell
Fill Arc
Fill Oval
Fill Poly
FillRect
FillRgn
FillRoundRect
FindControl
FlashMenuBar
Flush Vol
FMSwapFont
Frame Arc
FrameOval
FramePoly
FrameRect
FrameRgn
FrameRoundRect
FreeAlert
FreeDialog
FreeMem
GetClip
GetCursor
Routines That May Move or Purge Memory III-211

<!-- source-page: 219 -->
## Page 219

Inside Macintosh
GetDCtlEntry
GetDitem
GetFNum
GetFontlnfo
GetFontN ame
Getlcon
GetlndPattem
GetlndResource
GetlndString
GetKeys
GetMenu
GetMenuBar
GetMouse
GetN amedResource
GetNewControl
GetNewDialog
GetNewMBar
GetNewWindow
GetNextEvent
GetPattem
GetPicture
GetResource
GetScrap
GetString
Grow Window
HandAndHand
HandToHand
HideControl
Hide Window
HiliteControl
HiliteMenu
Hilite Window
InitAllPacks
InitApplZone
InitFonts
InitMenus
InitPack
InitPort
InitResources
lnitWindows
InitZone
lnsertMenu
InsertResMenu
InsetRgn
InvalRect
InvalRgn
InvertArc
InvertOval
InvertPoly
InvertRect
InvertRgn
InvertRoundRect
IUCompString
IUDatePString
IUDateString
IUEqualString
IUGetlntl
IUMagIDString
IUMagString
IUMetric
IUSetlntl
IUTimePString
IUTimeString
Kill Controls
KillPicture
KillPoly
LAPCloseProtocol
LAPOpenProtocol
LAPRdCancel
LAPRead
LAPWrite
Launch
Line
LineTo
LoadResource
LoadScrap
LoadSeg
MapRgn
Menu Key
MenuSelect
ModalDialog
MoreMasters
MoveControl
MoveHHi
Move Window
MPPClose
MPPOpen
Munger
NBPConfirm
NBPExtract
NBPLoad
NBPLookup
NBPRegister
NBPRemove
NBPUnload
NewControl
New Dialog
New Handle
New Menu
NewPtr
NewRgn
NewString
New Window
NoteAlert
11/-212 Routines That May Move or Purge Memory
NumToString
OpenDeskAcc
OpenPicture
OpenPoly
OpenPort
OpenResFile
OpenRgn
PaintArc
PaintBehind
PaintOne
PaintOval
PaintPoly
PaintRect
PaintRgn
PaintRoundRect
ParamText
PB Control
PB Eject
PBFlushVol
PBMountVol
PBOffLine
PB Open
PBOpenRF
PB Status
PicComment
Plotlcon
PrClose
PrCloseDoc
PrClosePage
PrCtlCall
PrDrvrDCE
PrDrvrVers
PrintDefault
PrJobDialog
PrJobMerge
PIO pen
PrOpenDoc
PrOpenPage
PrPicFile
PrStlDialog
PrValidate
PtrAndHand
PtrToHand
PtI'foXHand
PurgeMem
PutScrap
RAMSDClose
RAMSOOpen
RealFont
ReallocHandle
RecoverHandle
RectRgn

<!-- source-page: 220 -->
## Page 220

ReleaseResource
ResrvMem
Restart
RmveResource
RsrcZonelnit
SaveOld
ScrollRect
SectRgn
SelectWindow
SellText
SendBehind
SerClrBrk
SerGetBrk
SerHShake
Ser Reset
SerSetBrk
SerSetBuf
Ser Status
SetApplBase
SetClip
SetCTitle
SetCtlMax
SetCtlMin
SetCtlValue
SetDitem
SetEm pty Rgn
SetFontLock
SetHandleSize
Seti tern
Setltemlcon
SetltemMark
SetltemStyle
SetlText
SetPtrSize
SetRectRgn
SetReslnfo
SetString
SetTagBuffer
SetWTitle
SFGetFile
SFPGetFile
SFPPutFile
SFPutFile
ShowControl
Show Hide
Show Window
SizeControl
Size Window
StartSound
Status
StdArc
StdBits
Std Comment
StdLine
StdOval
StdPoly
StdPutPic
StdRect
StdRgn
StdRRect
StdText
StdTxMeas
Still Down
StopAlert
StopSound
StringToNum
String Width
SysBeep
SysError
SystemClick
SystemEdit
System Menu
Routines That May Move or Purge Memory
TEActivate
TECalText
TEClick
TECopy
TECut
TEDeactivate
TEDelete
TED is pose
TEFromScrap
TEGetText
TEidle
TEI nit
TEinsert
TE Key
TENew
TEPaste
TEScroll
TESetJust
TESetSelect
TESetText
TestControl
TEToScrap
TEUpdate
TextBox
Text Width
TickCount
TrackControl
TrackGoAway
UnionRgn
UnloadScrap
UnloadSeg
ValidRect
ValidRgn
WaitMouseUp
XorRgn
ZeroScrap
Routines That May Move or Purge Memory III-213

<!-- source-page: 221 -->
## Page 221

Inside Macintosh
111-214

<!-- source-page: 222 -->
## Page 222

APPENDIX C: SYSTEM TRAPS
This appendix lists the trap macros for the Toolbox and Operating System routines and their
corresponding trap word values in hexadecimal. The "Name" column gives the trap macro name
(without its initial underscore character). In those cases where the name of the equivalent Pascal
call is different, the Pascal name appears indented under the main entry. The routines in
Macintosh packages are listed under the macros they invoke after pushing a routine selector onto
the stack; the routine selector follows the Pascal routine name in parentheses.
There are two tables: The first is ordered alphabetically by name; the second is ordered
numerically by trap number, for use when debugging. (The trap number is the last two digits of
the trap word unless the trap word begins with A9, in which case the trap number is 1 followed
by the last two digits of the trap word.)
Note: The Operating System Utility routines GetTrapAddress and SetTrapAddress take a trap
number as a parameter, not a trap word.
Warning: Traps that aren't currently used by the system are reserved for future use.
Name
Trap word
Name
T rap word
AddDrive
A04E
ChangedResource
A9AA
(internal use only)
CharWidth
A88D
AddPt
A87E
Checkltem
A945
AddResMenu
A94D
Check Update
A911
AddResource
A9AB
ClearMenuBar
A934
Alert
A985
ClipAbove
A90B
Allocate
AOlO
ClipRect
A87B
PB Allocate
Close
AOOl
AngleFromSlope
A8C4
PBClose
AppendMenu
A933
CloseDeskAcc
A9B7
BackColor
A863
CloseDialog
A982
BackPat
A87C
ClosePgon
A8CC
Begin Update
A922
ClosePoly
BitAnd
A858
ClosePicture
A8F4
BitClr
A85F
ClosePort
A87D
BitNot
A85A
CloseResFile
A99A
BitOr
A85B
CloseRgn
A8DB
BitSet
A85E
Close Window
A92D
BitShift
A85C
CmpString
A03C
BitTst
A85D
Equal String
BitXor
A859
ColorBit
A864
BlockMove
A02E
CompactMem
A04C
BringToFront
A920
Control
A004
Button
A974
PB Control
CalcMenuSize
A948
Copy Bits
A8EC
CalcVBehind
A90A
CopyRgn
A8DC
Cale VisBehind
CouldAlert
A989
CalcVis
A909
CouldDialog
A979
CautionAlert
A988
CountMitems
A950
Chain
A9F3
CountResources
A99C
System Traps Il/-215

<!-- source-page: 223 -->
## Page 223

Inside Macintosh
Nam e
Trap word
Name
Trap word
CountTypes
A99E
EndUpdate
A923
Create
A008
Enqueue
A96F
PB Create
Equal.Pt
A881
CreateResFile
A9Bl
EqualRect
A8A6
CurResFile
A994
EqualRgn
A8E3
Date2Secs
A9C7
Erase Arc
A8CO
Delay
A03B
EraseOval
A8B9
Delete
A009
ErasePoly
A8C8
PB Delete
EraseRect
A8A3
DeleteMenu
A936
EraseRgn
A8D4
DeltaPoint
A94F
EraseRoundRect
A8B2
Dequeue
A96E
ErrorSound
A98C
DetachResource
A992
EventAvail
A971
DialogSelect
A980
ExitToShell
A9F4
DiffRgn
A8E6
FillArc
A8C2
Disableltem
A93A
Fill Oval
A8BB
DisposControl
A955
FillPoly
A8CA
DisposeControl
FillRect
A8A5
DisposDialog
A983
FillRgn
A8D6
DisposHandle
A023
FillRoundRect
A8B4
DisposMenu
A932
FindControl
A96C
DisposeMenu
FindWindow
A92C
DisposPtr
AOIF
FixMul
A868
DisposRgn
A8D9
FixRatio
A869
DisposeRgn
FixRound
A86C
DisposWindow
A914
FlashMenuBar
A94C
Dispose Window
FlushEvents
A032
DragControl
A967
FlushFile
A045
DragGray Rgn
A905
PBFlushFile
DragTheRgn
A926
Flush Vol
A013
Drag Window
A925
PB Flush Vol
DrawChar
A883
FMSwapFont
A901
DrawControls
A969
ForeColor
A862
Draw Dialog
A981
FP68K
A9EB
DrawGrowlcon
A904
Frame Arc
A8BE
DrawMenuBar
A937
FrameOval
A8B7
Draw New
A90F
FramePoly
A8C6
Draw Picture
A8F6
FrameRect
ASAI
Draw String
A884
FrameRgn
A8D2
DrawText
A885
FrameRoundRect
A8BO
Drvrlnstall
A03D
FreeAlert
A98A
(internal use only)
FreeDialog
A97A
DrvrRemove
A03E
FreeMem
AOIC
(internal use only)
Front Window
A924
Eject
A017
GetA ppParms
A9F5
PB Eject
GetClip
A87A
Elems68K
A9EC
GetCRefCon
A95A
Empty Handle
A02B
GetCTitle
A95E
EmptyRect
A8AE
GetCtlAction
A96A
EmptyRgn
A8E2
GetCtlValue
A960
Enableltem
A939
GetCursor
A9B9
III-216 System Traps

<!-- source-page: 224 -->
## Page 224

System Traps
Name
Trap word
Name
Trap word
GetDitem
A98D
GetScrap
A9FD
GetEOF
AOll
GetString
A9BA
PBGetEOF
GetTrapAddress
AI46
GetFilelnfo
AOOC
Get Vol
A014
PBGetFinfo
PBGetVol
GetFName
A8FF
GetVollnfo
A007
GetFontName
PBGetVInfo
GetFNum
A900
GetWindowPic
A92F
GetFontlnfo
A88B
GetWMgrPort
A910
GetFPos
A018
GetWRefCon
A917
PBGetFPos
GetWTitle
A919
GetHandleSize
A025
GetZone
Al IA
Getlcon
A9BB
GlobalToLocal
A871
GetlndResource
A99D
GrafDevice
A872
GetlndType
A99F
Grow Window
A92B
Getltem
A946
HandAndHand
A9E4
GetIText
A990
HandleZone
AI26
Getltmlcon
A93F
HandToHand
A9El
Getltemlcon
HideControl
A958
GetltmMark
A943
HideCursor
A852
GetltemMark
HidePen
A896
GetltmStyle
A941
Hide Window
A916
GetltemStyle
HiliteControl
A95D
GetKeys
A976
HiliteMenu
A938
GetMaxCtl
A962
Hilite Window
A9IC
GetCtlMax
HiWord
A86A
GetMenuBar
A93B
HLock
A029
GetMHandle
A949
HNoPurge
A04A
GetMinCtl
A961
HomeResFile
A9A4
GetCtlMin
HPurge
A049
GetMouse
A972
HUnlock
A02A
GetN amedResource
A9Al
Info Scrap
A9F9
GetNewControl
A9BE
InitAllPacks
A9E6
GetNewDialog
A97C
InitApplZone
A02C
GetNewMBar
A9CO
InitCursor
A850
GetNewWindow
A9BD
InitDialogs
A97B
GetNextEvent
A970
lnitFonts
A8FE
GetOSEvent
A031
InitGraf
A86E
GetPattem
A9B8
lnitMenus
A930
GetPen
A89A
InitPack
A9E5
GetPenState
A898
InitPort
A86D
GetPicture
A9BC
lnitQueue
A016
GetPixel
A865
FinitQueue
GetPort
A874
InitResources
A995
GetPtrSize
A021
InitUtil
A03F
GetResAttrs
A9A6
!nit Windows
A912
GetResFileAttrs
A9F6
InitZone
A019
GetReslnfo
A9A8
lnsertMenu
A935
GetResource
A9AO
InsertResMenu
A951
GetRMenu
A9BF
InsetRect
A8A9
GetMenu
InsetRgn
A8El
System Traps III-217

<!-- source-page: 225 -->
## Page 225

Inside Macintosh
Name
Trap word
Name
Trap word
InvalRect
A928
New Window
A913
InvalRgn
A927
NoteAlert
A987
InverRect
A8A4
ObscureCursor
A856
lnvertRect
Offiine
A035
InverRgn
A8D5
PBOffline
InvertRgn
OffsetPoly
A8CE
InverRoundRect
A8B3
OffsetRect
A8A8
InvertRoundRect
OfsetRgn
A8EO
InvertArc
A8Cl
OffsetRgn
InvertOval
A8BA
Open
AOOO
InvertPoly
A8C9
PB Open
lsDialogEvent
A97F
OpenDeskAcc
A9B6
KillControls
A956
OpenPicture
A8F3
KillIO
A006
OpenPoly
A8CB
PBKillIO
OpenPort
A86F
KillPicture
A8F5
OpenResFile
A997
KillPoly
A8CD
OpenRF
AOOA
Launch
A9F2
PBOpenRF
Line
A892
OpenRgn
A8DA
LineTo
A891
OSEventA vail
A030
LoadResource
A9A2
PackO
A9E7
LoadSeg
A9FO
(reserved for future use)
LocalToGlobal
A870
Packl
A9E8
LodeScrap
A9FB
(reserved for future use)
Load Scrap
Pack2
A9E9
LongMul
A867
DIBadMount (0)
Lo Word
A86B
DIFormat
(6)
MapPoly
A8FC
DILoad
(2)
MapPt
A8F9
DIUnload
(4)
MapRect
A8FA
DNerify
(8)
MapRgn
A8FB
DIZ.ero
(10)
MaxMem
AllD
Pack3
A9EA
MenuKey
A93E
SFGetFile
(2)
MenuSelect
A93D
SFPGetFile (4)
Modal Dialog
A991
SFPPutFile (3)
MoreMasters
A036
SFPutFile
(1)
Mount Vol
AOOF
Pack4
A9EB
PBMountVol
Pack5
A9EC
Move
A894
Pack6
A9ED
MoveControl
A959
IUDatePString (14)
MovePortTo
A877
IUDateString
(0)
MoveTo
A893
IUGetlntl
(6)
Move Window
A91B
IUMagIDString (12)
Munger
A9EO
IUMagString
(10)
NewControl
A954
IV Metric
(4)
New Dialog
A97D
IUSetlntl
(8)
New Handle
Al22
IUTimePString (16)
New Menu
A931
IUTimeString
(2)
NewPtr
AllE
Pack7
A9EE
NewRgn
A8D8
NumToString (0)
NewString
A906
StringToNum
(1)
II/-218 System Traps

<!-- source-page: 226 -->
## Page 226

System Traps
Name
Trap word
Name
Trap word
PackBits
A8CF
ScrollRect
A8EF
PaintArc
A8BF
Secs2Date
A9C6
PaintBehind
A90D
SectRect
A8AA
PaintOne
A90C
SectRgn
A8E4
PaintOval
A8B8
Select Window
A91F
PaintPoly
A8C7
SeIIText
A97E
PaintRect
A8A2
SendBehind
A921
PaintRgn
A8D3
SetAppBase
A057
PaintRoundRect
A8Bl
SetApplBase
ParamText
A98B
SetA ppl Limit
A02D
PenMode
A89C
SetClip
A879
PenNonnal
A89E
SetCRefCon
A95B
PenPat
A89D
SetCTitle
A95F
PenSize
A89B
SetCtlAction
A96B
PicComment
A8F2
SetCtIValue
A963
PinRect
A94E
SetCursor
A851
Plotlcon
A94B
SetDateTime
A03A
PortSize
A876
SetDitem
A98E
PostEvent
A02F
SetEmptyRgn
A8DD
Pt2Rect
A8AC
SetEOF
A012
PtlnRect
A8AD
PBSetEOF
PtlnRgn
A8E8
SetFilelnfo
AOOD
PtrAndHand
A9EF
PBSetFinfo
PtrToHand
A9E3
SetFiILock
A041
PtrToXHand
A9E2
PBSetFLock
PtrZone
A148
SetFiIType
A043
PtToAngle
A8C3
PBSetFVers
PurgeMem
A04D
SetFontLock
A903
PutScrap
A9FE
SetFPos
A044
Random
A861
PBSetFPos
RDrvrlnstall
A04F
SetGrowZone
A04B
(internal use only)
SetHandleSize
A024
Read
A002
Setltem
A947
PB Read
SetIText
A98F
ReadDateTime
A039
Setltmlcon
A940
Real Font
A902
Setltemlcon
ReallocHandle
A027
SetltmMark
A944
RecoverHandle
A128
SetltemMark
RectlnRgn
A8E9
SetltmStyle
A942
RectRgn
A8DF
SetltemStyle
ReleaseResource
A9A3
SetMaxCtl
A965
Rename
AOOB
SetCtlMax
PB Rename
SetMenuBar
A93C
ResError
A9AF
SetMFlash
A94A
ResrvMem
A040
SetMenuFlash
RmveResource
A9AD
SetMinCtl
A964
RsrcZonelnit
A996
SetCtlMin
RstFilLock
A042
SetOrigin
A878
PBRstFLock
SetPBits
A875
SaveOld
A90E
SetPortBits
ScalePt
A8F8
SetPenState
A899
System Traps III-219

<!-- source-page: 227 -->
## Page 227

Inside Macintosh
Name
Trap word
Name
Trap word
SetPort
A873
SubPt
A87F
SetPt
A880
Sys Beep
A9C8
SetPtrSize
A020
SysEdit
A9C2
SetRecRgn
A8DE
SystemEdit
SetRectRgn
SysError
A9C9
SetRect
A8A7
System Click
A9B3
SetResAttrs
A9A7
SystemEvent
A9B2
SetResFileAttrs
A9F7
SystemMenu
A9B5
SetReslnfo
A9A9
System Task
A9B4
SetResLoad
A99B
TEActivate
A9D8
SetResPurge
A993
TECalText
A9DO
SetStdProcs
A8EA
TEClick
A9D4
SetString
A907
TECopy
A9D5
SetTrapAddress
A047
TECut
A9D6
SetVol
A015
TEDeactivate
A9D9
PBSetVol
TEDelete
A9D7
SetWindowPic
A92E
TEDispose
A9CD
SetWRefCon
A918
TEGetText
A9CB
SetWTitle
A91A
TEidle
A9DA
SetZone
AOlB
TEinit
A9CC
ShieldCursor
A855
TEinsert
A9DE
ShowControl
A957
TE Key
A9DC
ShowCursor
A853
TENew
A9D2
Show Hide
A908
TEPaste
A9DB
Show Pen
A897
TEScroll
A9DD
Show Window
A915
TESetJust
A9DF
SizeControl
A95C
TESetSelect
A9Dl
SizeRsrc
A9A5
TESetText
A9CF
SizeResource
TestControl
A966
Size Window
A91D
TEUpdate
A9D3
SlopeFromAngle
A8BC
TextBox
A9CE
SpaceExtra
A88E
TextFace
A888
Status
A005
TextFont
A887
PB Status
TextMode
A889
StdArc
A8BD
TextSize
A88A
StdBits
A8EB
Text Width
A886
StdComment
A8Fl
TickCount
A975
StdGetPic
A8EE
TrackControl
A968
StdLine
A890
TrackGoAway
A91E
Std Oval
A8B6
UnionRect
A8AB
StdPoly
A8C5
UnionRgn
A8E5
Std.PutPic
A8FO
UniquelD
A9Cl
StdRect
A8AO
UnloadSeg
A9Fl
StdRgn
A8Dl
UnlodeScrap
A9FA
StdRRect
A8AF
UnloadScrap
StdText
A882
Unmount Vol
AOOE
StdTxMeas
A8ED
PB Unmount Vol
StillDown
A973
UnpackBits
ABDO
StopAlert
A986
UpdateResFile
A999
String Width
A88C
UprString
A054
StuffHex
A866
UseResFile
A998
III-220 System Traps

<!-- source-page: 228 -->
## Page 228

Name
ValidRect
ValidRgn
Vlnstall
VRemove
WaitMouseUp
Trap word
AOOO
AOOl
A002
A003
A004
A005
A006
A007
A008
A009
AOOA
AOOB
AOOC
AOOD
AOOE
AOOF
AOIO
AOl 1
A012
A013
Trap word
A92A
A929
A033
A034
A977
Name
Open
PB Open
Close
PB Close
Read
PB Read
Write
PB Write
Control
PBControl
Status
PB Status
KillIO
PBKillIO
GetVollnfo
PBGetVInfo
Create
PBCreate
Delete
PB Delete
OpenRF
PBOpenRF
Rename
PB Rename
GetFilelnfo
PBGetlnfo
SetFilelnfo
PBSetFinfo
UnmountVol
PB Unmount Vol
Mount Vol
PBMountVol
Allocate
PB Allocate
GetEOF
PBGetEOF
SetEOF
PBSetEOF
Flush Vol
PBFlushVol
Name
Write
PB Write
WriteParam
W riteResource
XorRgn
ZeroScrap
Trap word
A014
A015
A016
A017
A018
A019
Al1A
AOlB
AOIC
AIID
A11E
AOIF
A020
A021
A122
A023
A024
A025
A126
A027
Al28
A029
A02A
A02B
A02C
A02D
A02E
A02F
A030
A031
A032
A033
A034
A035
A036
System Traps
Trap word
A003
A038
A9BO
A8E7
A9FC
Name
Get Vol
PBGetVol
Set Vol
PB Set Vol
InitQueue
Eject
PB Eject
GetFPos
PBGetFPos
InitZone
GetZone
SetZone
FreeMem
MaxMem
NewPtr
DisposPtr
SetPtrSize
GetPtrSize
NewHandle
DisposHandle
SetHandleSize
GetHandleSize
HandleZone
ReallocHandle
Recover Handle
HLock
HUnlock
Empty Handle
InitApplZone
SetApplLirnit
BlockMove
PostEvent
OSEventA vail
GetOSEvent
FlushEvents
Vlnstall
VRemove
Offline
PBOffline
MoreMasters
System Traps I-221

<!-- source-page: 229 -->
## Page 229

Inside Macintosh
Trap word
Name
Trap word
Name
A038
WriteParam
A861
Random
A039
ReadDateTime
A862
ForeColor
A03A
SetDateTime
A863
BackColor
A03B
Delay
A864
ColorBit
A03C
CmpString
A865
GetPixel
Equal String
A866
StuffHex
A03D
Drvrlnstall
A867
LongMul
(internal use only)
A868
FixMul
A03E
DrvrRemove
A869
FixRatio
(internal use only)
A86A
HiWord
A03F
InitUtil
A86B
Lo Word
A040
ResrvMem
A86C
Fix Round
A041
SetFilLock
A86D
InitPort
PBSetFLock
A86E
InitGraf
A042
RstFilLock
A86F
OpenPort
PBRstFLock
A870
LocalToGlobal
A043
SetFilType
A871
GlobalToLocal
PBSetFVers
A872
GrafDevice
A044
SetFPos
A873
SetPort
PBSetFPos
A874
GetPort
A045
FlushFile
A875
SetPBits
PBFlushFile
SetPortBits
A146
GetTrapAddress
A876
PortSize
A047
SetTrapAddress
A877
MovePortTo
A148
PtrZone
A878
SetOrigin
A049
HPurge
A879
SetClip
A04A
HNoPurge
A87A
GetClip
A04B
SetGrowZone
A87B
ClipRect
A04C
CompactMem
A87C
BackPat
A04D
PurgeMem
A87D
ClosePort
A04E
AddDrive
A87E
AddPt
(internal use only)
A87F
SubPt
A04F
RDrvrlnstall
A880
SetPt
(internal use only)
A881
EqualPt
A850
InitCursor
A882
StdText
A851
SetCursor
A883
DrawChar
A852
HideCursor
A884
Draw String
A853
ShowCursor
A885
DrawText
A054
UprString
A886
Text Width
A855
ShieldCursor
A887
TextFont
A856
ObscureCursor
A888
TextFace
A057
SetAppBase
A889
TextMode
SetApplBase
A88A
TextSize
A858
BitAnd
A88B
GetFontlnfo
A859
BitXor
A88C
String Width
A85A
BitNot
A88D
CharWidth
A85B
BitOr
A88E
SpaceExtra
A85C
BitShift
A890
StdLine
A85D
BitTst
A891
Line To
A85E
BitSet
A892
Line
A85F
BitClr
A893
MoveTo
III-222 System Traps

<!-- source-page: 230 -->
## Page 230

System Traps
Trap word
Name
Trap word
Name
A894
Move
A8C8
ErasePoly
A896
HidePen
A8C9
InvertPoly
A897
Show Pen
A8CA
Fill Poly
A898
GetPenState
A8CB
OpenPoly
A899
SetPenState
A8CC
ClosePgon
A89A
GetPen
ClosePoly
A89B
PenSize
A8CD
KillPoly
A89C
PenMode
A8CE
OffsetPoly
A89D
PenPat
A8CF
PackBits
A89E
PenNormal
A8DO
UnpackBits
A8AO
StdRect
A8Dl
StdRgn
A8Al
FrameRect
A8D2
FrameRgn
A8A2
PaintRect
A8D3
PaintRgn
A8A3
EraseRect
A8D4
EraseRgn
A8A4
InverRect
A8D5
InverRgn
InvertRect
InvertRgn
A8A5
FillRect
A8D6
FillRgn
A8A6
EqualRect
A8D8
NewRgn
A8A7
SetRect
A8D9
DisposRgn
A8A8
OffsetRect
DisposeRgn
A8A9
InsetRect
A8DA
OpenRgn
A8AA
SectRect
A8DB
CloseRgn
A8AB
UnionRect
A8DC
CopyRgn
A8AC
Pt2Rect
A8DD
SetEmptyRgn
ASAD
PtinRect
A8DE
SetRecRgn
A8AE
EmptyRect
A8DF
SetRectRgn
A8AF
StdRRect
RectRgn
A8BO
FrameRoundRect
A8EO
OfsetRgn
A8Bl
PaintRoundRect
OffsetRgn
A8B2
EraseRoundRect
A8El
InsetRgn
A8B3
InverRoundRect
A8E2
EmptyRgn
InvertRoundRect
A8E3
EqualRgn
A8B4
FillRoundRect
A8E4
SectRgn
A8B6
Std Oval
A8E5
UnionRgn
A8B7
FrameOval
A8E6
DiffRgn
A8B8
PaintOval
A8E7
XorRgn
A8B9
EraseOval
A8E8
PtlnRgn
A8BA
InvertOval
A8E9
RectlnRgn
A8BB
Fill Oval
A8EA
SetStdProcs
A8BC
SlopeFromAngle
A8EB
StdBits
A8BD
StdArc
A8EC
Copy Bits
A8BE
FrameArc
A8ED
StdTxMeas
A8BF
PaintArc
A8EE
StdGetPic
A8CO
Erase Arc
A8EF
ScrollRect
A8Cl
InvertArc
A8FO
StdPutPic
A8C2
FillArc
A8Fl
StdComment
A8C3
PtToAngle
A8F2
PicComment
A8C4
AngleFromSlope
A8F3
OpenPicture
A8C5
StdPoly
A8F4
ClosePicture
A8C6
FramePoly
A8F5
KillPicture
A8C7
PaintPoly
A8F6
DrawPicture
System Traps lll-223

<!-- source-page: 231 -->
## Page 231

Inside Macintosh
Trap word
Name
Trap word
Name
A8F8
SealePt
A929
ValidRgn
A8F9
MapPt
A92A
ValidReet
A8FA
MapReet
A92B
Grow Window
A8FB
MapRgn
A92C
Find Window
A8FC
MapPoly
A92D
Close Window
A8FE
InitFonts
A92E
Set Window Pie
A8FF
GetFName
A92F
GetWindowPie
GetFontName
A930
InitMenus
A900
GetFNum
A931
New Menu
A901
FMSwapFont
A932
DisposMenu
A902
RealFont
DisposeMenu
A903
SetFontLoek
A933
AppendMenu
A904
DrawGrowlcon
A934
ClearMenuBar
A905
Drag Gray Rgn
A935
InsertMenu
A906
NewString
A936
DeleteMenu
A907
SetString
A937
DrawMenuBar
A908
Show Hide
A938
HiliteMenu
A909
Cale Vis
A939
Enable Item
A90A
Cale VBehind
A93A
Disableltem
Cale VisBehind
A93B
GetMenuBar
A90B
Clip Above
A93C
SetMenuBar
A90C
PaintOne
A93D
MenuSeleet
A90D
PaintBehind
A93E
MenuKey
A90E
SaveOld
A93F
Getltmleon
A90F
Draw New
Getltemlcon
A910
GetWMgrPort
A940
Setltmleon
A911
Check Update
Setltemlcon
A912
InitWindows
A941
GetltmStyle
A913
New Window
GetltemSty le
A914
Dispos Window
A942
SetltrnStyle
Dispose Window
SetltemStyle
A915
Show Window
A943
GetltrnMark
A916
Hide Window
GetltemMark
A917
GetWRefCon
A944
SetltrnMark
A918
SetWRefCon
SetltemMark
A919
GetWfitle
A945
Cheekltem
A91A
SetWfitle
A946
Ge ti tern
A91B
Move Window
A947
Setltem
A91C
Hilite Window
A948
CaleMenuSize
A91D
Size Window
A949
GetMHandle
A91E
TraekGoAway
A94A
Set.MFlash
A91F
SeleetWindow
SetMenuFlash
A920
BringToFront
A94B
Plotleon
A921
SendBehind
A94C
FlashMenuBar
A922
BeginUpdate
A94D
AddResMenu
A923
EndUpdate
A94E
PinReet
A924
Front Window
A94F
DeltaPoint
A925
Drag Window
A950
CountMltems
A926
DragTheRgn
A951
InsertResMenu
A927
InvalRgn
A954
NewControl
A928
InvalRect
III-224 System Traps

<!-- source-page: 232 -->
## Page 232

System Traps
Trap word
Name
Trap word
Name
A955
DisposControl
A986
StopAlert
DisposeControl
A987
NoteAlert
A956
KillControls
A988
CautionAlert
A957
ShowControl
A989
CouldAlert
A958
HideControl
A98A
Free Alert
A959
MoveControl
A98B
ParamText
A95A
GetCRefCon
A98C
ErrorSound
A95B
SetCRefCon
A98D
GetDitem
A95C
SizeControl
A98E
SetDitem
A95D
HiliteControl
A98F
SetIText
A95E
GetCTitle
A990
GetlText
A95F
SetCTitle
A991
Modal Dialog
A960
GetCtlValue
A992
DetachResource
A961
GetMinCtl
A993
SetResPurge
GetCtlMin
A994
CurResFile
A962
GetMaxCtl
A995
InitResources
GetCtlMax
A996
RsrcZonelnit
A963
SetCtlValue
A997
OpenResFile
A964
SetMinCtl
A998
UseResFile
SetCtlMin
A999
UpdateResFile
A965
SetMaxCtl
A99A
CloseResFile
SetCtlMax
A99B
SetResLoad
A966
TestControl
A99C
CountResources
A967
DragControl
A99D
GetlndResource
A968
TrackControl
A99E
CountTypes
A969
DrawControls
A99F
GetlndType
A96A
GetCtlAction
A9AO
GetResource
A96B
SetCtlAction
A9Al
GetNamedResource
A96C
FindControl
A9A2
LoadResource
A96E
Dequeue
A9A3
ReleaseResource
A96F
Enqueue
A9A4
HomeResFile
A970
GetNextEvent
A9A5
Size Rs re
A97 1
EventAvail
SizeResource
A972
GetMouse
A9A6
GetResAttrs
A973
Still Down
A9A7
SetResAttrs
A974
Button
A9A8
GetReslnfo
A975
TickCount
A9A9
SetReslnfo
A976
GetKeys
A9AA
ChangedResource
A977
WaitMouseUp
A9AB
AddResource
A979
CouldDialog
A9AD
RmveResource
A97A
FreeDialog
A9AF
ResError
A97B
InitDialogs
A9BO
W riteResource
A97C
GetNewDialog
A9Bl
CreateResFile
A97D
New Dialog
A9B2
SystemEvent
A97E
SelIText
A9B3
SystemClick
A97F
IsDialogEvent
A9B4
System Task
A980
DialogSelect
A9B5
SystemMenu
A981
Draw Dialog
A9B6
OpenDeskAcc
A982
CloseDialog
A9B7
CloseDeskAcc
A983
DisposDialog
A9B8
GetPattem
A985
Alert
A9B9
GetCursor
System Traps 111-225

<!-- source-page: 233 -->
## Page 233

Inside Macintosh
Trap word
Name
Trap word
Name
A9BA
GetString
A9E9
Pack2
A9BB
Ge ti con
DIBadMount (0)
A9BC
GetPicture
DILoad
(2)
A9BD
GetNewWindow
DIUnload
(4)
A9BE
GetNewControl
DIFormat
(6)
A9BF
GetRMenu
DIVerify
(8)
GetMenu
DIZero
(10)
A9CO
GetNewMBar
A9EA
Pack3
A9Cl
UniqueID
SFPutFile
(1)
A9C2
SysEdit
SFGetFile
(2)
SystemEdit
SFPPutFile (3)
A9C6
Secs2Date
SFPGetFile (4)
A9C7
Date2Secs
A9EB
Pack4
A9C8
SysBeep
(synonym: FP68K)
A9C9
Sys Error
A9EC
Pack5
A9CB
TEGetText
(synonym: Elems68K)
A9CC
TEinit
A9ED
Pack6
A9CD
TEDispose
IUDateString
(0)
A9CE
TextBox
IUTimeString
(2)
A9CF
TESetText
IUMetric
(4)
A9DO
TECalText
IUDGetlntl
(6)
A9Dl
TESetSelect
IUSetlntl
(8)
A9D2
TENew
IUMagString
(10)
A9D3
TEUpdate
IUMagIDString (12)
A9D4
TEClick
IUDatePString (14)
A9D5
TECopy
IUTimeP String ( 16)
A9D6
TECut
A9EE
Pack7
A9D7
TEDelete
NumToString (0)
A9D8
TEActivate
StringToNum (I)
A9D9
TEDeactivate
A9EF
PtrAndHand
A9DA
TEI die
A9FO
LoadSeg
A9DB
TEPaste
A9Fl
UnloadSeg
A9DC
TE Key
A9F2
Launch
A9DD
TEScroll
A9F3
Chain
A9DE
TEinsert
A9F4
ExitToShell
A9DF
TESetJust
A9F5
GetAppPanns
A9EO
Munger
A9F6
GetResFileAttrs
A9El
HandToHand
A9F7
SetResFileAttrs
A9E2
PtrToXHand
A9F9
InfoScrap
A9E3
PtrToHand
A9FA
UnlodeScrap
A9E4
HandAndHand
UnloadScrap
A9E5
InitPack
A9FB
LodeScrap
A9E6
InitAllPacks
Load Scrap
A9E7
PackO
A9FC
Zero Scrap
(reserved for future use)
A9FD
GetScrap
A9E8
Pack!
A9FE
PutScrap
(reserved for future use)
///-226 System Traps

<!-- source-page: 234 -->
## Page 234

APPENDIX D: GLOBAL VARIABLES
This appendix gives an alphabetical list of all system global variables described in Inside
Macintosh, along with their locations in memory.
Name
Location
Contents
ABusVars
$208
Pointer to AppleTalk variables
A Count
$A9A
Stage number (0 through 3) of last alert (word)
AN umber
$A98
Resource ID of last alert (word)
ApFontID
$984
Font number of application font (word)
ApplLimit
$130
Application heap limit
ApplScratch
$A78
12-byte scratch area reserved for use by applications
ApplZone
$2AA
Address of application heap zone
AppParmHandle
$AEC
Handle to Finder information
BufPtr
$10C
Address of end of jump table
BufrgDate
$304
File tags buffer: date and time of last modification (long)
BuITgFBkNum
$302
File tags buffer: logical block number (word)
BuITgFFlg
$300
File tags buffer: flags (word: bit l=l if resource fork)
BufrgFNum
$2FC
File tags buffer: file number (long)
CaretTime
$2F4
Caret-blink interval in ticks (long)
CrsrThresh
$8EC
Mouse-scaling threshold (word)
Cur Activate
$A64
Pointer to window to receive activate event
CurApName
$910
Name of current application (length byte followed by up to 31
characters)
CurApRefNum
$900
Reference number of current application's resource file (word)
CurDeactive
$A68
Pointer to window to receive deactivate event
CurJTOffset
$934
Offset to jump table from location pointed to by A5 (word)
CurMap
$A5A
Reference number of current resource file (word)
CurPageOption
$936
Sound/screen buffer configuration passed to Chain or Launch
(word)
CurPitch
$280
Value of count in square-wave synthesizer buffer (word)
CurrentA5
$904
Address of boundary between application globals and application
parameters
CurStackBase
$908
Address of base of stack; start of application globals
DABeeper
$A9C
Address of current sound procedure
DAStrings
$AAO
Handles to ParamText strings (16 bytes)
Global Variables /II-227

<!-- source-page: 235 -->
## Page 235

Inside Macintosh
Name
Location
Contents
DefltStack
$322
Default space allotment for stack (long)
DefVCBPtr
$352
Pointer to default volume control block
DeskHook
$A6C
Address of procedure for painting desktop or responding to
clicks on desktop
DeskPattern
$A3C
Pattern with which desktop is painted (8 bytes)
DlgFont
$APA
Font number for dialogs and alerts (word)
Double Time
$2FO
Double-click interval in ticks (long)
DragHook
$9F6
Address of procedure to execute during TrackGoAway,
DragWindow, GrowWindow, DragGrayRgn, TrackControl, and
Drag Control
DragPattem
$A34
Pattern of dragged region's outline (8 bytes)
DrvQHdr
$308
Drive queue header (10 bytes)
DSAlertRect
$3F8
Rectangle enclosing system error alert (8 bytes)
DSAlertTab
$2BA
Pointer to system error alert table in use
DSErrCode
$APO
Current system error ID (word)
EventQueue
$14A
Event queue header (10 bytes)
ExtStsDT
$2BE
External/status interrupt vector table (16 bytes)
FCBSPtr
$34E
Pointer to file-control-block buffer
FinderName
$2EO
Name of the Finder (length byte followed by up to 15 characters)
FScaleDisable
$A63
Nonzero to disable font scaling (byte)
FSQHdr
$360
File I/O queue header ( 10 bytes)
Ghost Window
$A84
Pointer to window never to be considered frontmost
GrayRgn
$9EE
Handle to region drawn as desktop
GZRootHnd
$328
Handle to relocatable block not to be moved by grow zone
function
Heap End
$114
Address of end of application heap zone
JFetch
$8F4
Jump vector for Fetch function
TIO Done
$8FC
Jump vector for IODone function
JournalFlag
$8DE
Journaling mode (word)
JoumalRef
$8E8
Reference number of journaling device driver (word)
JStash
$8F8
Jump vector for Stash function
Key RepThresh
$190
Auto-key rate (word)
KeyThresh
$18E
Auto-key threshold (word)
Lo3Bytes
$31A
$00FFFFFF
LvllDT
$192
Level-I secondary interrupt vector table (32 bytes)
III-228 Global Variables

<!-- source-page: 236 -->
## Page 236

Name
Lvl2DT
MBarEnable
MBarHook
MemTop
MenuFlash
MenuHook
MenuList
MinStack
MinusOne
OldContent
OldStructure
OneOne
Paint White
PortBUse
PrintErr
RAMBase
Res Err
ResErrProc
ResLoad
ResumeProc
RndSeed
ROMBase
RO:MFontO
Save Update
SaveVisRgn
SCCRd
SCCWr
ScrapCount
ScrapHandle
ScrapName
ScrapSize
ScrapState
Location
$1B2 '
$A20
$A2C
$108
$A24
$A30
$A1C
$31E
$A06
$9EA
$9E6
$A02
$9DC
$291
$944
$2B2
$A60
$AF2
$ASE
$A8C
$156
$2AE
$980
$9DA
$9F2
$108
$1DC
$968
$964
$96C
$960
$96A
Global. Variables
Contents
Level-2 secondary interrupt vector table (32 bytes)
Unique menu ID for active desk accessory, when menu bar
belongs to the accessory (word)
Address of routine called by MenuSelect before menu is drawn
Address of end of RAM (on Macintosh XL, end of RAM
available to applications)
Count for duration of menu item blinking (word)
Address of routine called during MenuSelect
Handle to current menu list
Minimum space allotment for stack (long)
$FFFFFFFF
Handle to saved content region
Handle to saved structure region
$00010001
Flag for whether to paint window white before update event
(word)
Current availability of serial port B (byte)
Result code from last Printing Manager routine (word)
Trap dispatch table's base address for routines in RAM
Current value of ResError (word)
Address of resource error procedure
Current SetResLoad state (word)
Address of resume procedure
Random number seed (long)
Base address of ROM
Handle to font record for system font
Flag for whether to generate update events (word)
Handle to saved visRgn
sec read base address
sec write base address
Count changed by ZeroScrap (word)
Handle to desk scrap in memory
Pointer to scrap file name (preceded by length byte)
Size in bytes of desk scrap (long)
Tells where desk scrap is (word)
Global Variables III-229

<!-- source-page: 237 -->
## Page 237

Inside Macintosh
Name
Location
Scratch8
$9FA
Scratch20
$1E4
ScrDmpEnb
$2F8
ScrHRes
$104
ScmBase
$824
ScrVRes
$102
SdVolume
$260
SEvtEnb
$15C
SFSaveDisk
$214
SoundBase
$266
Sound.Level
$27F
SoundPtr
$262
SP Alarm
$200
SPATalkA
$1F9
SPATalkB
$1FA
SPClikCaret
$209
SPConfig
$1FB
SP Font
$204
SPKbd
$206
SPMisc2
$20B
SPPortA
$1FC
SPPortB
$1FE
SPPrint
$207
SPValid
$1F8
SPVolCtl
$208
SysEvtMask
$144
SysMap
$A58
SysMapHndl
$A54
SysParam
$1F8
SysResName
$ADS
SysZone
$2A6
TEDoText
$A70
III-230 Global Variables
Contents
8-byte scratch area
20-byte scratch area
0 if GetNextEvent shouldn't process Command-Shift-number
combinations (byte)
Pixels per inch horizontally (word)
Address of main screen buffer
Pixels per inch vertically (word)
Current speaker volume (byte: low-order three bits only)
0 if SystemEvent should return FALSE (byte)
Negative of volume reference number used by Standard File
Package (word)
Pointer to free-form synthesizer buffer
Amplitude in 740-byte buffer (byte)
Pointer to four-tone record
Alarm setting (long)
AppleTalk node ID hint for modem port (byte)
AppleTalk node ID hint for printer port (byte)
Double-click and caret-blink times (byte)
Use types for serial ports (byte)
Application font number minus 1 (word)
Auto-key threshold and rate (byte)
Mouse scaling, system startup disk, menu blink (byte)
Modem port configuration (word)
Printer port configuration (word)
Printer connection (byte)
Validity status (byte)
Speaker volume setting in parameter RAM (byte)
System event mask (word)
Reference number of system resource file (word)
Handle to map of system resource file
Low-memory copy of parameter RAM (20 bytes)
Name of system resource file (length byte followed by up to 19
characters)
Address of system heap zone
Address of TextEdit multi-purpose routine

<!-- source-page: 238 -->
## Page 238

Name
TERecal
TEScrpHandle
TEScrpLength
TheMenu
TheZone
Ticks
Time
ToExtFS
Tool Scratch
TopMapHndl
UTableBase
VBLQueue
VCBQHdr
VIA
Window List
WMgrPort
Location
$A74
$AB4
$ABO
$A26
$118
$16A
$20C
$3F2
$9CE
$A50
$11C
$160
$356
$IDA
$9D6
$9DE
Global Variables
Contents
Address of routine to recalculate line starts for TextEdit
Handle to TextEdit scrap
Size in bytes ofTextEdit scrap (long)
Menu ID of currently highlighted menu (word)
Address of current heap zone
Current number of ticks since system startup (long)
Seconds since midnight, January 1, 1904 (long)
Pointer to external file system
8-byte scratch area
Handle to resource map of most recently opened resource file
Base address of unit table
Vertical retrace queue header (10 bytes)
Volume-control-block queue header (10 bytes)
VIA base address
Pointer to first window in window list; 0 if using events but not
windows
Pointer to Window Manager port
Global Variables l/l-231

<!-- source-page: 239 -->
## Page 239

Inside Macintosh
111-232

<!-- source-page: 240 -->
## Page 240

GLOSSARY
access path: A description of the route that the File Manager follows to access a file; created
when a file is opened.
access path buffer: Memory used by the File Manager to transfer data between an application
and a file.
action procedure: A procedure, used by the Control Manager function TrackControl, that
defines an action to be performed repeatedly for as long as the mouse button is held down.
activate event: An event generated by the Window Manager when a window changes from
active to inactive or vice versa.
active control: A control that will respond to the user's actions with the mouse.
active window: The frontmost window on the desktop.
address mark: In a sector, information that's used internally by the Disk Driver, including
information it uses to determine the position of the sector on the disk.
ALAP: See AppleTalk Link Access Protocol.
ALAP frame: A packet of data transmitted and received by ALAP.
ALAP protocol type: An identifier used to match particular kinds of packets with a particular
protocol handler.
alert: A warning or report of an error, in the form of an alert box, sound from the Macintosh's
speaker, or both.
alert box: A box that appears on the screen to give a warning or report an error during a
Macintosh application.
alert template: A resource that contains information from which the Dialog Manager can create
an alert.
alert window: The window in which an alert box is displayed.
alias: A different name for the same entity.
allocate: To reserve an area of memory for use.
allocation block: Volume space composed of an integral number of logical blocks.
amplitude: The maximum vertical distance of a periodic wave from the horizontal line about
which the wave oscillates.
AppleTalk address: A socket's number and its node ID number.
Glossary 111-233

<!-- source-page: 241 -->
## Page 241

Inside Macintosh
AppleTalk Link Access Protocol (ALAP): The lowest-level protocol in the AppleTalk
architecture, managing node-to-node delivery of frames on a single AppleTalk network.
AppleTalk Manager: An interface to a pair of RAM device drivers that enable programs to
send and receive information via an AppleTalk network.
AppleTalk Transaction Protocol (ATP): An AppleTalk protocol that's a DDP client. It
allows one ATP client to request another ATP client to perform some activity and report the
activity's result as a response to the requesting socket with guaranteed delivery.
application font: The font your application will use unless you specify otherwise-Geneva,
by default.
application heap: The portion of the heap available to the running application program and the
Toolbox.
application heap limit: The boundary between the space available for the application heap and
the space available for the stack.
application heap zone: The heap zone initially provided by the Memory Manager for use by
the application program and the Toolbox; initially equivalent to the application heap, but may be
subdivided into two or more independent heap zones.
application parameters: Thirty-two bytes of memory, located above the application globals,
reserved for system use. The first application parameter is the address of the first QuickDraw
global variable.
application space: Memory that's available for dynamic allocation by applications.
application window: A window created as the result of something done by the application,
either directly or indirectly (as through the Dialog Manager).
ascent: The vertical distance from a font's base line to its ascent line.
ascent line: A horizontal line that coincides with the tops of the tallest characters in a font.
asynchronous communication: A method of data transmission where the receiving and
sending devices don't share a common timer, and no timing data is transmitted.
asynchronous execution: After calling a routine asynchronously, an application is free to
perform other tasks until the routine is completed.
at-least-once transaction: An ATP transaction in which the requested operation is performed
at least once, and possibly several times.
ATP: See AppleTalk Transaction Protocol.
auto-key event: An event generated repeatedly when the user presses and holds down a
character key on the keyboard or keypad.
auto-key rate: The rate at which a character key repeats after it's begun to do so.
///-234 Glossary

<!-- source-page: 242 -->
## Page 242

Glossary
auto-key threshold: The length of time a character key must be held down before it begins to
repeat.
background procedure: A procedure passed to the Printing Manager to be run during idle
times in the printing process.
base line: A horizontal line that coincides with the bottom of each character in a font, excluding
descenders (such as the tail of a "p").
baud rate: The measure of the total number of bits sent over a transmission line per second.
Binary-Decimal Conversion Package: A Macintosh package for converting integers to
decimal strings and vice versa.
bit image: A collection of bits in memory that have a rectilinear representation. The screen is a
visible bit image.
bit map: A set of bits that represent the position and state of a corresponding set of items; in
QuickDraw, a pointer to a bit image, the row width of that image, and its boundary rectangle.
block: A group regarded as a unit; usually refers to data or memory in which data is stored. See
allocation block and memory block.
block contents: The area that's available for use in a memory block.
block device: A device that reads and writes blocks of bytes at a time. It can read or write any
accessible block on demand.
block header: The internal "housekeeping" information maintained by the Memory Manager at
the beginning of each block in a heap zone.
block map: Same as volume allocation block map.
boundary rectangle: A rectangle, defined as part of a QuickDraw bit map, that encloses the
active area of the bit image and imposes a coordinate system on it. Its top left comer is always
aligned around the first bit in the bit image.
break: The condition resulting when a device maintains its transmission line in the space state
for at least one frame.
bridge: An intelligent link between two or more AppleTalk networks.
broadcast service: An ALAP service in which a frame is sent to all nodes on an AppleTaJk
network.
bundle: A resource that maps local IDs of resources to their actual resource IDs; used to provide
mappings for file references and icon lists needed by the Finder.
button: A standard Macintosh control that causes some immediate or continuous action when
clicked or pressed with the mouse. See also radio button.
Glossary 111-235

<!-- source-page: 243 -->
## Page 243

Inside Macintosh
caret: A generic term meaning a symbol that indicates where something should be inserted in
text. The specific symbol used is a vertical bar ( I ).
caret-blink time: The interval between blinks of the caret that marks an insertion point
character code: An integer representing the character that a key or combination of keys on the
keyboard or keypad stands for.
character device: A device that reads or writes a stream of characters, one at a time. It can
neither skip characters nor go back to a previous character.
character image: An arrangement of bits that defines a character in a font.
character key: A key that generates a keyboard event when pressed; any key except Shift, Caps
Lock, Command, or Option.
character offset: The horizontal separation between a character rectangle and a font rectangle.
character origin: The point on a base line used as a reference location for drawing a character.
character position: An index into an array containing text, starting at 0 for the first character.
character rectangle: A rectangle enclosing an entire character image. Its sides are defined by
the image width and the font height.
character style: A set of stylistic variations, such as bold, italic, and underline. The empty set
indicates plain text (no stylistic variations).
character width: The distance to move the pen from one character's origin to the next
character's origin.
check box: A standard Macintosh control that displays a setting, either checked (on) or
unchecked (oft). Clicking inside a check box reverses its setting.
clipping: Limiting drawing to within the bounds of a particular area.
clipping region: Same as clipRgn.
clipRgn: The region to which an application limits drawing in a grafPort.
clock chip: A special chip in which are stored parameter RAM and the current setting for the
date and time. This chip is powered by a battery when the system is off, thus preserving the
information.
close routine: The part of a device driver's code that implements Device Manager Close calls.
closed driver: A device driver that cannot be read from or written to.
closed file: A file without an access path. Closed files cannot be read from or written to.
compaction: The process of moving allocated blocks within a heap zone in order to collect the
free space into a single block.
III-236 Glossary

<!-- source-page: 244 -->
## Page 244

Glossary
completion routine: Any application-defined code to be executed when an asynchronous call
to a routine is completed.
content region: The area of a window that the application draws in.
control: An object in a window on the Macintosh screen with which the user, using the mouse,
can cause instant action with visible results or change settings to modify a future action.
control definition function: A function called by the Control Manager when it needs to
perform type-dependent operations on a particular type of control, such as drawing the control.
control definition ID: A number passed to control-creation routines to indicate the type of
control. It consists of the control definition function's resource ID and a variation code.
control information: Information transmitted by an application to a device driver. It may
select modes of operation, start or stop processes, enable buffers, choose protocols, and so on.
control list: A list of all the controls associated with a given window.
Control Manager: The part of the Toolbox that provides routines for creating and manipulating
controls (such as buttons, check boxes, and scroll bars).
control record: The internal representation of a control, where the Control Manager stores all
the information it needs for its operations on that control.
control routine: The part of a device driver's code that implements Device Manager Control
and KilllO calls.
control template: A resource that contains information from which the Control Manager can
create a control.
coordinate plane: A two-dimensional grid. In QuickDraw, the grid coordinates are integers
ranging from -32767 to 32767, and all grid lines are infinitely thin.
current heap zone: The heap zone currently under attention, to which most Memory Manager
operations implicitly apply.
current resource file: The last resource file opened, unless you specify otherwise with a
Resource Manager routine.
cursor: A 16-by-16 bit image that appears on the screen and is controlled by the mouse; called
the "pointer'' in Macintosh user manuals.
cursor level: A value, initialized by InitCursor, that keeps track of the number of times the
cursor has been hidden.
data bits: Data communications bits that encode transmitted characters.
data buffer: Heap space containing information to be written to a file or device driver from an
application, or read from a file or device driver to an application.
data fork: The part of a file that contains data accessed via the File Manager.
Glossary III-237

<!-- source-page: 245 -->
## Page 245

Inside Macintosh
data mark: In a sector, information that primarily contains data from an application.
datagram: A packet of data transmitted by DDP.
Datagram Delivery Protocol (DDP): An AppleTalk protocol that's an ALAP client,
managing socket-to-socket delivery of datagrams over AppleTalk internets.
date/time record: An alternate representation of the date and time (which is stored on the clock
chip in seconds since midnight, January 1, 1904).
DDP: See Datagram Delivery Protocol.
default button: In an alert box or modal dialog, the button whose effect will occur if the user
presses Return or Enter. In an alert box, it's boldly outlined; in a modal dialog, it's boldly
outlined or the OK button.
default volume: A volume that will receive I/O during a File Manager routine call, whenever no
other volume is specified.
dereference: To refer to a block by its master pointer instead of its handle.
descent: The vertical distance from a font's base line to its descent line.
descent line: A horizontal line that coincides with the bottoms of the characters in a font that
extend furthest below the base line.
desk accessory: A "mini-application", implemented as a device driver, that can be run at the
same time as a Macintosh application.
Desk Manager: The part of the Toolbox that supports the use of desk accessories from an
application.
desk scrap: The place where data is stored when it's cut (or copied) and pasted among
applications and desk accessories.
desktop: The screen as a surface for doing work on the Macintosh.
Desktop file: A resource file in which the Finder stores the version data, bundle, icons, and file
references for each application on the volume.
destination rectangle: In TextEdit, the rectangle in which the text is drawn.
device: A part of the Macintosh, or a piece of external equipment, that can transfer information
into or out of the Macintosh.
device control entry: A 40-byte relocatable block of heap space that tells the Device Manager
the location of a driver's routines, the location of a driver's 110 queue, and other information.
device driver: A program that controls the exchange of information between an application and
a device.
device driver event: An event generated by one of the Macintosh's device drivers.
111-238 Glossary

<!-- source-page: 246 -->
## Page 246

Glossary
Device Manager: The part of the Operating System that supports device I/O.
dial: A control with a moving indicator that displays a quantitative setting or value. Depending
on the type of dial, the user may be able to change the setting by dragging the indicator with the
mouse.
dialog: Same as dialog box.
dialog box: A box that a Macintosh application displays to request information it needs to
complete a command, or to report that it's waiting for a process to complete.
Dialog Manager: The part of the Toolbox that provides routines for implementing dialogs and
alerts.
dialog record: The internal representation of a dialog, where the Dialog Manager stores all the
information it needs for its operations on that dialog.
dialog template: A resource that contains information from which the Dialog Manager can
create a dialog.
dialog window: The window in which a dialog box is displayed.
dimmed: Drawn in gray rather than black
disabled: A disabled menu item or menu is one that cannot be chosen; the menu item or menu
title appears dimmed. A disabled item in a dialog or alert box has no effect when clicked.
Disk Driver: The device driver that controls data storage and retrieval on 3 1/2-inch disks.
Disk Initialization Package: A Macintosh package for initializing and naming new disks;
called by the Standard File Package.
disk-inserted event: An event generated when the user inserts a disk in a disk drive or takes
any other action that requires a volume to be mounted.
display rectangle: A rectangle that determines where an item is displayed within a dialog or
alert box.
document window: The standard Macintosh window for presenting a document.
double-click time: The greatest interval between a mouse-up and mouse-down event that
would qualify two mouse clicks as a double-click.
draft printing: Printing a document immediately as it's drawn in the printing grafPort.
drag region: A region in a window frame. Dragging inside this region moves the window to a
new location and makes it the active window unless the Command key was down.
drive number: A number used to identify a disk drive. The internal drive is number 1, the
external drive is number 2, and any additional drives will have larger numbers.
drive queue: A list of disk drives connected to the Macintosh.
Glossary IIJ-239

<!-- source-page: 247 -->
## Page 247

Inside Macintosh
driver name: A sequence of up to 255 printing characters used to refer to an open device driver.
Driver names always begin with a period (.).
driver 1/0 queue: A queue containing the parameter blocks of all UO requests for one device
driver.
driver reference number: A number from - 1 to -32 that uniquely identifies an individual
device driver.
edit record: A complete editing environment in TextEdit, which includes the text to be edited,
the grafPort and rectangle in which to display the text, the arrangement of the text within the
rectangle, and other editing and display information.
empty handle: A handle that points to a NIL master pointer, signifying that the underlying
relocatable block has been purged.
empty shape: A shape that contains no bits, such as one defined by only a single point.
end-of-file: See logical end-of-file or physical end-of-file.
entity name: An identifier for an entity, of the form object:type@zone.
event: A notification to an application of some occurrence that the application may want to
respond to.
event code: An integer representing a particular type of event.
Event Manager: See Toolbox Event Manager or Operating System Event Manager.
event mask: A parameter passed to an Event Manager routine to specify which types of events
the routine should apply to.
event message: A field of an event record containing information specific to the particular type
of event.
event queue: The Operating System Event Manager's list of pending events.
event record: The internal representation of an event, through which your program learns all
pertinent information about that event.
exactly-once transaction: An ATP transaction in which the requested operation is performed
only once.
exception: An error or abnormal condition detected by the processor in the course of program
execution; includes interrupts and traps.
exception vector: One of 64 vectors in low memory that point to the routines that are to get
control in the event of an exception.
external reference: A reference to a routine or variable defined in a separate compilation or
assembly.
III-240 Glossary

<!-- source-page: 248 -->
## Page 248

Glossary
file: A named, ordered sequence of bytes; a principal means by which data is stored and
transmitted on the Macintosh.
file control block: A fixed-length data structure, contained in the file-control-block buffer,
where information about an access path is stored.
file-control-block buffer: A nonrelocatable block in the system heap that contains one file
control block for each access path.
file directory: The part of a volume that contains descriptions and locations of all the files on
the volume.
file I/O queue: A queue containing parameter blocks for all 1/0 requests to the File Manager.
File Manager: The part of the Operating System that supports file 1/0.
file name: A sequence of up to 255 printing characters, excluding colons (:),that identifies a
file.
file number: A unique number assigned to a file, which the File Manager uses to distinguish it
from other files on the volume. A file number specifies the file's entry in a file directory.
file reference: A resource that provides the Finder with file and icon information about an
application.
file tags: Information associated with each logical block, designed to allow reconstruction of
files on a volume whose directory or other file-access information has been destroyed.
file tags buffer: A location in memory where file tags are read from and written to.
file type: A four-character sequence, specified when a file is created, that identifies the type of
file.
Finder information: Information that the Finder provides to an application upon starting it up,
telling it which documents to open or print.
fixed-point number: A signed 32-bit quantity containing an integer part in the high-order
word and a fractional part in the low-order word.
fixed-width font: A font whose characters all have the same width.
Floating-Point Arithmetic Package: A Macintosh package that supports extended-precision
arithmetic according to IEEE Standard 754.
font: The complete set of characters of one typeface.
font characterization table: A table of parameters in a device driver that specifies how best to
adapt fonts to that device.
font height: The vertical distance from a font's ascent line to its descent line.
Glossary ///-241

<!-- source-page: 249 -->
## Page 249

Inside Macintosh
Font Manager: The part of the Toolbox that supports the use of various character fonts for
QuickDraw when it draws text.
font number: The number by which you identify a font to QuickDraw or the Font Manager.
font record: A data structure that contains all the information describing a font.
font rectangle: The smallest rectangle enclosing all the character images in a font, if the images
were all superimposed over the same character origin.
font size: The size of a font in points; equivalent to the distance between the ascent line of one
line of text and the ascent line of the next line of single-spaced text.
fork: One of the two parts of a file; see data fork and resource fork.
four-tone record: A data structure describing the tones produced by a four-tone synthesizer.
four-tone synthesizer: The part of the Sound Driver used to make simple harmonic tones,
with up to four "voices" producing sound simultaneously.
frame: The time elapsed from the start bit to the last stop bit during serial communication.
frame check sequence: A 16-bit value generated by the AppleTalk hardware, used by the
receiving node to detect transmission errors.
frame header: Information at the beginning of a packet.
frame pointer: A pointer to the end of the local variables within a routine's stack frame, held in
an address register and manipulated with the LINK and UNLK instructions.
frame trailer: Information at the end of an ALAP frame.
framed shape: A shape that's drawn outlined and hollow.
framing error: The condition resulting when a device doesn't receive a stop bit when expected.
free block: A memory block containing space available for allocation.
free-form synthesizer: The part of the Sound Driver used to make complex music and
speech.
frequency: The number of cycles per second (also called hertz) at which a wave oscillates.
full-duplex communication: A method of data transmission where two devices transmit data
simultaneously.
global coordinate system: The coordinate system based on the top left comer of the bit image
being at (0,0).
go-away region: A region in a window frame. Clicking inside this region of the active
window makes the window close or disappear.
l//-242 Glossary

<!-- source-page: 250 -->
## Page 250

Glossary
grafPort: A complete drawing environment, including such elements as a bit map, a subset
of it in which to draw, a character font, patterns for drawing and erasing, and other pen
characteristics.
grow image: The image pulled around when the user drags inside the grow region; whatever is
appropriate to show that the window's size will change.
grow region: A window region, usually within the content region, where dragging changes the
size of an active window.
grow zone function: A function supplied by the application program to help the Memory
Manager create free space within a heap zone.
handle: A pointer to a master pointer, which designates a relocatable block in the heap by double
indirection.
hardware overrun error: The condition that occurs when the SCC's buffer becomes full.
heap: The area of memory in which space is dynamically allocated and released on demand,
using the Memory Manager.
heap zone: An area of memory initialized by the Memory Manager for heap allocation,
highlight: To display an object on the screen in a distinctive visual way, such as inverting it.
horizontal blanking interval: The time between the display of the rightmost pixel on one line
and the leftmost pixel on the next line.
hotSpot: The point in a cursor that's aligned with the mouse location.
icon: A 32-by-32 bit image that graphically represents an object, concept, or message.
icon list: A resource consisting of a list of icons.
icon number: A digit from 1 to 255 to which the Menu Manager adds 256 to get the resource
ID of an icon associated with a menu item.
image width: The width of a character image.
inactive control: A control that won't respond to the user's actions with the mouse. An
inactive control is highlighted in some special way, such as dimmed.
inactive window: Any window that isn't the frontmost window on the desktop.
indicator: The moving part of a dial that displays its current setting.
input driver: A device driver that receives serial data via a serial port and transfers it to an
application.
insertion point: An empty selection range; the character position where text will be inserted
(usually marked with a blinking caret).
Glossary III-243

<!-- source-page: 251 -->
## Page 251

Inside Macintosh
interface routine: A routine called from Pascal whose purpose is to trap to a certain Toolbox
or Operating System routine.
International Utilities Package: A Macintosh package that gives you access to countrydependent information such as the formats for numbers, currency, dates, and times.
internet: An interconnected group of AppleTalk networks.
internet address: The AppleTalk address and network number of a socket.
interrupt: An exception that's signaled to the processor by a device, to notify the processor of a
change in condition of the device, such as the completion of an 1/0 request.
interrupt handler: A routine that services interrupts.
interrupt priority level: A number identifying the importance of the interrupt. It indicates
which device is interrupting, and which interrupt handler should be executed.
interrupt vector: A pointer to an interrupt handler.
invert: To highlight by changing white pixels to black and vice versa.
invisible control: A control that's not drawn in its window.
invisible window: A window that's not drawn in its plane on the desktop.
1/0 queue: See driver 1/0 queue or file 1/0 queue.
1/0 request: A request for input from or output to a file or device driver; caused by calling a
File Manager or Device Manager routine asynchronously.
item: In dialog and alert boxes, a control, icon, picture, or piece of text, each displayed inside its
own display rectangle. See also menu item.
item list: A list of information about all the items in a dialog or alert box.
item number: The index, starting from 1, of an item in an item list.
IWM: "Integrated Woz Machine"; the custom chip that controls the 3 1/2-inch disk drives.
job dialog: A dialog that sets information about one printing job; associated with the Print
command.
journal code: A code passed by a Toolbox Event Manager routine in its Control call to the
journaling device driver, to designate which routine is making the Control call.
journaling mechanism: A mechanism that allows you to feed the Toolbox Event Manager
events from some source other than the user.
jump table: A table that contains one entry for every routine in an application and is the means
by which the loading and unloading of segments is implemented.
I//-244 Glossary

<!-- source-page: 252 -->
## Page 252

Glossary
justification: The horizontal placement of lines of text relative to the edges of the rectangle in
which the text is drawn.
kern: To draw part of a character so that it overlaps an adjacent character.
key code: An integer representing a key on the keyboard or keypad, without reference to the
character that the key stands for.
key-down event: An event generated when the user presses a character key on the keyboard or
keypad.
key-up event: An event generated when the user releases a character key on the keyboard or
keypad.
keyboard configuration: A resource that defines a particular keyboard layout by associating a
character code with each key or combination of keys on the keyboard or keypad.
keyboard equivalent: The combination of the Command key and another key, used to invoke
a menu item from the keyboard.
keyboard event: An event generated when the user presses, releases, or holds down a
character key on the keyboard or keypad; any key-down, key-up, or auto-key event.
leading: The amount of blank vertical space between the descent line of one line of text and the
ascent line of the next line of single-spaced text.
ligature: A character that combines two letters.
list separator: The character that separates numbers, as when a list of numbers is entered by the
user.
local coordinate system: The coordinate system local to a grafPort, imposed by the boundary
rectangle defined in its bit map.
local ID: A number that refers to an icon list or file reference in an application's resource file and
is mapped to an actual resource ID by a bundle.
location table: An array of words (one for each character in a font) that specifies the location of
each character's image in the font's bit image.
lock: To temporarily prevent a relocatable block from being moved during heap compaction.
lock bit: A bit in the master pointer to a relocatable block that indicates whether the block is
currently locked.
locked file: A file whose data cannot be changed.
locked volume: A volume whose data cannot be changed. Volumes can be locked by either a
software flag or a hardware setting.
logical block: Volume space composed of 512 consecutive bytes of standard information and
an additional number of bytes of information specific to the Disk Driver.
Glossary III-245

<!-- source-page: 253 -->
## Page 253

Inside Macintosh
logical end-of-file: The position of one byte past the last byte in a file; equal to the actual
number of bytes in the file.
logical size: The number of bytes in a memory block's contents.
magnitude: The vertical distance between any given point on a wave and the horizontal line
about which the wave oscillates.
main event loop: In a standard Macintosh application program, a loop that repeatedly calls the
Toolbox Event Manager to get events and then responds to them as appropriate.
main segment: The segment containing the main program.
mark: The position of the next byte in a file that will be read or written.
mark state: The state of a transmission line indicating a binary 1.
master directory block: Part of the data structure of a volume; contains the volume
information and the volume allocation block map.
master pointer: A single pointer to a relocatable block, maintained by the Memory Manager
and updated whenever the block is moved, purged, or reallocated. All handles to a relocatable
block refer to it by double indirection through the master pointer.
memory block: An area of contiguous memory within a heap zone.
Memory Manager: The part of the Operating System that dynamically allocates and releases
memory space in the heap.
menu: A list of menu items that appears when the user points to a menu title in the menu bar and
presses the mouse button. Dragging through the menu and releasing over an enabled menu item
chooses that item.
menu bar: The horizontal strip at the top of the Macintosh screen that contains the menu titles of
all menus in the menu list.
menu definition procedure: A procedure called by the Menu Manager when it needs to
perform type-dependent operations on a particular type of menu, such as drawing the menu.
menu ID: A number in the menu record that identifies the menu.
menu item: A choice in a menu, usually a command to the current application.
menu item number: The index, starting from 1, of a menu item in a menu.
menu list: A list containing menu handles for all menus in the menu bar, along with information
on the position of each menu.
Menu Manager: The part of the Toolbox that deals with setting up menus and letting the user
choose from them.
///-246 Glossary

<!-- source-page: 254 -->
## Page 254

Glossary
menu record: The internal representation of a menu, where the Menu Manager stores all the
information it needs for its operations on that menu.
menu title: A word or phrase in the menu bar that designates one menu.
missing symbol: A character to be drawn in case of a request to draw a character that's
missing from a particular font.
modal dialog: A dialog that requires the user to respond before doing any other work on the
desktop.
modeless dialog: A dialog that allows the user to work elsewhere on the desktop before
responding.
modifier key: A key (Shift, Caps Lock, Option, or Command) that generates no keyboard
events of its own, but changes the meaning of other keys or mouse actions.
mounted volume: A volume that previously was inserted into a disk drive and had descriptive
information read from it by the File Manager.
mouse-down event: An event generated when the user presses the mouse button.
mouse scaling: A feature that causes the cursor to move twice as far during a mouse stroke
than it would have otherwise, provided the change in the cursor's position exceeds the mousescaling threshold within one tick after the mouse is moved.
mouse-scaling threshold: A number of pixels which, if exceeded by the sum of the
horizontal and vertical changes in the cursor position during one tick of mouse movement, causes
mouse scaling to occur (if that feature is turned on); normally six pixels.
mouse-up event: An event generated when the user releases the mouse button.
Name-Binding Protocol (NBP): An AppleTalk protocol that's a DDP client, used to convert
entity names to their internet socket addresses.
name lookup: An NBP operation that allows clients to obtain the internet addresses of entities
from their names.
names directory: The union of all name tables in an internet.
names information socket: The socket in a node used to implement NBP (always socket
number 2).
names table: A list of each entity's name and internet address in a node.
NBP: See Name-Binding Protocol.
NBP tuple: An entity name and an internet address.
network event: An event generated by the AppleTalk Manager.
network number: An identifier for an AppleTalk network.
Glossary III-247

<!-- source-page: 255 -->
## Page 255

Inside Macintosh
network-visible entity: A named socket client on an internet.
newline character: Any character, but usually Return (ASCII code $00), that indicates the end
of a sequence of bytes.
newline mode: A mode of reading data where the end of the data is indicated by a newline
character (and not by a specific byte count).
node: A device that's attached to and communicates via an AppleTalk network.
node ID: A number, dynamically assigned, that identifies a node.
nonbreaking space: The character with ASCII code $CA; drawn as a space the same width as
a digit, but interpreted as a nonblank character for the purposes of word wraparound and
selection.
nonrelocatable block: A block whose location in the heap is fixed and can't be moved during
heap compaction.
null event: An event reported when there are no other events to report.
off-line volume: A mounted volume with all but 94 bytes of its descriptive information
released.
offset/width table: An array of words that specifies the character offsets and character widths
of all characters in a font.
on-line volume: A mounted volume with its volume buffer and descriptive information
contained in memory.
open driver: A driver that can be read from and written to.
open file: A file with an access path. Open files can be read from and written to.
open permission: Information about a file that indicates whether the file can be read from,
written to, or both.
open routine: The part of a device driver's code that implements Device Manager Open calls.
Operating System: The lowest-level software in the Macintosh. It does basic tasks such as
1/0, memory management, and interrupt handling.
Operating System Event Manager: The part of the Operating System that reports hardwarerelated events such as mouse-button presses and keystrokes.
Operating System Utilities: Operating System routines that perform miscellaneous tasks such
as getting the date and time, finding out the user's preferred speaker volume and other
preferences, and doing simple string comparison.
output driver: A device driver that receives data via a serial port and transfers it to an
application.
III-248 Glossary

<!-- source-page: 256 -->
## Page 256

Glossary
overrun error: See hardware overrun error and software overrun error.
package: A set of routines and data types that's stored as a resource and brought into memory
only when needed.
Package Manager: The part of the Toolbox that lets you access Macintosh RAM-based
packages.
page rectangle: The rectangle marking the boundaries of a printed page image. The boundary
rectangle, portRect, and clipRgn of the printing graf?ort are set to this rectangle.
palette: A collection of small symbols, usually enclosed in rectangles, that represent operations
and can be selected by the user.
pane: An independently scrollable area of a window, for showing a different part of the same
document
panel: An area of a window that shows a different interpretation of the same part of a document.
paper rectangle: The rectangle marking the boundaries of the physical sheet of paper on which
a page is printed.
parameter block: A data structure used to transfer information between applications and certain
Operating System routines.
parameter RAM: In the clock chip, 20 bytes where settings such as those made with the
Control Panel desk accessory are preserved.
parity bit: A data communications bit used to verify that data bits received by a device match the
data bits transmitted by another device.
parity error: The condition resulting when the parity bit received by a device isn't what was
expected.
part code: An integer between 1 and 253 that stands for a particular part of a control (possibly
the entire control).
path reference number: A number that uniquely identifies an individual access path; assigned
when the access path is created.
pattern: An 8-by-8 bit image, used to define a repeating design (such as stripes) or tone (such
as gray).
pattern transfer mode: One of eight transfer modes for drawing lines or shapes with a pattern.
period: The time elapsed during one complete cycle of a wave.
phase: Some fraction of a wave cycle (measured from a fixed point on the wave).
physical end-of-file: The position of one byte past the last allocation block of a file; equal to 1
more than the maximum number of bytes the file can contain.
Glossary Ill-249

<!-- source-page: 257 -->
## Page 257

Inside Macintosh
physical size: The actual number of bytes a memory block occupies within its heap zone.
picture: A saved sequence of QuickDraw drawing commands (and, optionally, picture
comments) that you can play back later with a single procedure call; also, the image resulting from
these commands.
picture comments: Data stored in the definition of a picture that doesn't affect the picture's
appearance but may be used to provide additional information about the picture when it's played
back.
picture frame: A rectangle, defined as part of a picture, that surrounds the picture and gives a
frame of reference for scaling when the picture is played back.
pixel: The visual representation of a bit on the screen (white if the bit is 0, black if it's 1).
plane: The front-to-back position of a window on the desktop.
point: The intersection of a horizontal grid line and a vertical grid line on the coordinate plane,
defined by a horizontal and a vertical coordinate; also, a typographical term meaning
approximately 1172 inch.
polygon: A sequence of connected lines, defined by QuickDraw line-drawing commands.
port: See grafPort.
portBits: The bit map of a grafPort.
portRect: A rectangle, defined as part of a grafPort, that encloses a subset of the bit map for use
by the grafPort.
post: To place an event in the event queue for later processing.
prime routine: The part of a device driver's code that implements Device Manager Read and
Write calls.
print record: A record containing all the information needed by the Printing Manager to
perform a particular printing job.
Printer Driver: The device driver for the currently installed printer.
printer resource file: A file containing all the resources needed to run the Printing Manager
with a particular printer.
printing grafPort: A special grafPort customized for printing instead of drawing on the screen.
Printing Manager: The routines and data types that enable applications to communicate with
the Printer Driver to print on any variety of printer via the same interface.
processor priority: Bits 8-10 of the MC68000's status register, indicating which interrupts
will be processed and which will be ignored.
1//-250 Glossary

<!-- source-page: 258 -->
## Page 258

Glossary
proportional font: A font whose characters all have character widths that are proportional to
their image width.
protocol: A well-defined set of communications rules.
protocol handler: A software process in a node that recognizes different kinds of frames by
their ALAP type and services them.
protocol handler table: A list of the protocol handlers for a node.
purge: To remove a relocatable block from the heap, leaving its master pointer allocated but set
to NIL.
purge bit: A bit in the master pointer to a relocatable block that indicates whether the block is
currently purgeable.
purge warning procedure: A procedure associated with a particular heap zone that's called
whenever a block is purged from that zone.
purgeable block: A relocatable block that can be purged from the heap.
queue: A list of identically structured entries linked together by pointers.
QuickDraw: The part of the Toolbox that performs all graphic operations on the Macintosh
screen.
radio button: A standard Macintosh control that displays a setting, either on or off, and is part
of a group in which only one button can be on at a time.
RAM: The Macintosh's random access memory, which contains exception vectors, buffers used
by hardware devices, the system and application heaps, the stack, and other information used by
applications.
read/write permission: Information associated with an access path that indicates whether the
file can be read from, written to, both read from and written to, or whatever the file's open
permission allows.
reallocate: To allocate new space in the heap for a purged block, updating its master pointer to
point to its new location.
reference number: A number greater than 0, returned by the Resource Manager when a
resource file is opened, by which you can refer to that file. In Resource Manager routines that
expect a reference number, 0 represents the system resource file.
reference value: In a window record or control record, a 32-bit field that an application
program may store into and access for any purpose.
region: An arbitrary area or set of areas on the Quick.Draw coordinate plane. The outline of a
region should be one or more closed loops.
register-based routine: A Toolbox or Operating System routine that receives its parameters
and returns its results, if any, in registers.
Glossary lll-251

<!-- source-page: 259 -->
## Page 259

Inside Macintosh
relative handle: A handle to a relocatable block expressed as the offset of its master pointer
within the heap zone, rather than as the absolute memory address of the master pointer.
release: To free an allocated area of memory, making it available for reuse.
release timer: A timer for determining when an exactly-once response buffer can be released.
relocatable block: A block that can be moved within the heap during compaction.
resource: Data or code stored in a resource file and managed by the Resource Manager.
resource attribute: One of several characteristics, specified by bits in a resource reference, that
determine how the resource should be dealt with.
resource data: In a resource file, the data that comprises a resource.
resource file: The resource fork of a file.
resource fork: The part of a file that contains data used by an application (such as menus,
fonts, and icons). The resource fork of an application file also contains the application code
itself.
resource header: At the beginning of a resource file, data that gives the offsets to and lengths
of the resource data and resource map.
resource ID: A number that, together with the resource type, identifies a resource in a resource
file. Every resource has an ID number.
Resource Manager: The part of the Toolbox that reads and writes resources.
resource map: In a resource file, data that is read into memory when the file is opened and that,
given a resource specification, leads to the corresponding resource data.
resource name: A string that, together with the resource type, identifies a resource in a
resource file. A resource may or may not have a name.
resource reference: In a resource map, an entry that identifies a resource and contains either an
offset to its resource data in the resource file or a handle to the data if it's already been read into
memory.
resource specification: A resource type and either a resource ID or a resource name.
resource type: The type of a resource in a resource file, designated by a sequence of four
characters (such as 'MENU' for a menu).
response BDS: A data structure used to pass response information to the ATP module.
result code: An integer indicating whether a routine completed its task successfully or was
prevented by some error condition (or other special condition, such as reaching the end of a file).
resume procedure: A procedure within an application that allows the application to recover
from system errors.
Ill-252 Glossary

<!-- source-page: 260 -->
## Page 260

Glossary
retry count: The maximum number of retransmissions for an NBP or ATP packet.
retry interval: The time between retransmissions of a packet by NBP or ATP.
ROM: The Macintosh's permanent read-only memory, which contains the routines for the
Toolbox and Operating System, and the various system traps.
routine selector: An integer that's pushed onto the stack before the _PackN macro is invoked,
to identify which routine to execute. (N is the resource ID of a package; all macros for calling
routines in the package expand to invoke _PackN.)
routing table: A table in a bridge that contains routing information.
Routing Table Maintenance Protocol (RTMP): An AppleTalk protocol that's used
internally by AppleTalk to maintain tables for routing datagrams through an internet.
row width: The number of bytes in each row of a bit image.
RTMP: See Routing Table Maintenance Protocol.
RTMP socket: The socket in a node used to implement RTMP.
R TMP stub: The RTI\1P code in a nonbridge node.
scaling factor: A value, given as a fraction, that specifies the amount a character should be
stretched or shrunk before it's drawn.
SCC: See Serial Communications Controller.
scrap: A place where cut or copied data is stored.
scrap file: The file containing the desk scrap (usually named "Clipboard File").
Scrap Manager: The part of the Toolbox that enables cutting and pasting between applications,
desk accessories, or an application and a desk accessory.
screen buffer: A block of memory from which the video display reads the information to be
displayed.
sector: Disk space composed of 512 consecutive bytes of standard information and 12 bytes of
file tags.
segment: One of several parts into which the code of an application may be divided. Not all
segments need to be in memory at the same time.
Segment Loader: The part of the Operating System that loads the code of an application into
memory, either as a single unit or divided into dynamically loaded segments.
selection range: The series of characters (inversely highlighted), or the character position
(marked with a blinking caret), at which the next editing operation will occur.
Glossary III-253

<!-- source-page: 261 -->
## Page 261

Inside Macintosh
sequence number: A number from 0 to 7, assigned to an ATP response datagram to indicate
its ordering within the response.
Serial Communications Controller (SCC): The chip that handles serial I/O through the
modem and printer ports.
serial data: Data communicated over a single-path communication line, one bit at a time.
Serial Driver: A device driver that controls communication, via serial ports, between
applications and serial peripheral devices.
signature: A four-character sequence that uniquely identifies an application to the Finder.
socket: A logical entity within the node of a network.
socket client: A software process in a node that owns a socket.
socket listener: The portion of a socket client that receives and services datagrams addressed to
that socket.
socket number: An identifier for a socket.
socket table: A listing of all the socket listeners for each active socket in a node.
software overrun error: The condition that occurs when an input driver's buffer becomes
full.
solid shape: A shape that's filled in with any pattern.
sound buffer: A block of memory from which the sound generator reads the information to
create an audio waveform.
Sound Driver: The device driver that controls sound generation in an application.
sound procedure: A procedure associated with an alert that will emit one of up to four sounds
from the Macintosh's speaker. Its integer parameter ranges from 0 to 3 and specifies which
sound.
source transfer mode: One of eight transfer modes for drawing text or transferring any bit
image between two bit maps.
space state: The state of a transmission line indicating a binary 0.
spool printing: Writing a representation of a document's printed image to disk or to memory,
and then printing it (as opposed to immediate draft printing).
square-wave synthesizer: The part of the Sound Driver used to produce less harmonic
sounds than the four-tone synthesizer, such as beeps.
stack: The area of memory in which space is allocated and released in LIFO (last-in-first-out)
order.
111-254 Glossary

<!-- source-page: 262 -->
## Page 262

Glossary
stack-based routine: A Toolbox or Operating System routine that receives its parameters and
returns its results, if any, on the stack.
stack frame: The area of the stack used by a routine for its parameters, return address, local
variables, and temporary storage.
stage: Every alert has four stages, corresponding to consecutive occurrences of the alert, and a
different response may be specified for each stage.
Standard File Package: A Macintosh package for presenting the standard user interface when
a file is to be saved or opened.
start bit: A serial data communications bit that signals that the next bits transmitted are data bits.
status information: Information transmitted to an application by a device driver. It may
indicate the current mode of operation, the readiness of the device, the occurrence of errors, and
so on.
status routine: The part of a device driver's code that implements Device Manager Status calls.
stop bit: A serial data communications bit that signals the end of data bits.
structure region: An entire window; its complete "structure".
style: See character style.
style dialog: A dialog that sets options affecting the page dimensions; associated with the Page
Setup command.
synchronous execution: After calling a routine synchronously, an application cannot continue
execution until the routine is completed.
synthesizer: See free-form, four-tone, or square-wave synthesizer.
synthesizer buffer: A description of the sound to be generated by a synthesizer.
system error alert: An alert box displayed by the System Error Handler.
system error alert table: A resource that determines the appearance and function of system
error alerts.
System Error Handler: The part of the Operating System that assumes control when a fatal
system error occurs.
system error ID: An ID number that appears in a system error alert to identify the error.
system event mask: A global event mask that controls which types of events get posted into
the event queue.
system font: The font that the system uses (in menus, for example). Its name is Chicago.
system font size: The size of text drawn by the system in the system font; 12 points.
Glossary III-255

<!-- source-page: 263 -->
## Page 263

Inside Macintosh
system heap: The portion of the heap reserved for use by the Operating System.
system heap zone: The heap zone provided by the Memory Manager for use by the Operating
System; equivalent to the system heap.
system resource: A resource in the system resource file.
system resource file: A resource file containing standard resources, accessed if a requested
resource wasn't found in any of the other resource files that were searched.
system startup information: Certain configurable system parameters that are stored in the first
two logical blocks of a volume and read in at system startup.
system window: A window in which a desk accessory is displayed.
TextEdit: The part of the Toolbox that supports the basic text entry and editing capabilities of a
standard Macintosh application.
TextEdit scrap: The place where certain TextEdit routines store the characters most recently cut
or copied from text
thousands separator: The character that separates every three digits to the left of the decimal
point.
thumb: The Control Manager's term for the scroll box (the indicator of a scroll bar).
tick: A sixtieth of a second.
Toolbox: Same as User Interface Toolbox.
Toolbox Event Manager: The part of the Toolbox that allows your application program to
monitor the user's actions with the mouse, keyboard, and keypad.
Toolbox Utilities: The part of the Toolbox that performs generally useful operations such as
fixed-point arithmetic, string manipulation, and logical operations on bits.
track: Disk space composed of 8 to 12 consecutive sectors. A track corresponds to one ring of
constant radius around the disk.
transaction: A request-response communication between two ATP clients. See transaction
request and transaction response.
transaction ID: An identifier assigned to a transaction.
transaction request: The initial part of a transaction in which one socket client asks another to
perform an operation and return a response.
transaction response: The concluding part of a transaction in which one socket client returns
requested information or simply confirms that a requested operation was performed.
Transcendental Functions Package: A Macintosh package that contains trigonometric,
logarithmic, exponential, and financial functions, as well as a random number generator.
///-256 Glossary

<!-- source-page: 264 -->
## Page 264

Glossary
transfer mode: A specification of which Boolean operation QuickDraw should perform when
drawing or when transfening a bit image from one bit map to another.
trap dispatch table: A table in RAM containing the addresses of all Toolbox and Operating
System routines in encoded form.
trap dispatcher: The part of the Operating System that examines a trap word to determine what
operation it stands for, looks up the address of the corresponding routine in the trap dispatch
table, and jumps to the routine.
trap macro: A macro that assembles into a trap word, used for calling a Toolbox or Operating
System routine from assembly language.
trap number: The identifying number of a Toolbox or Operating System routine; an index into
the trap dispatch table.
trap word: An unimplemented instruction representing a call to a Toolbox or Operating System
routine.
unimplemented instruction: An instruction word that doesn't correspond to any valid
machine-language instruction but instead causes a trap.
unit number: The number of each device driver's entry in the unit table.
unit table: A 128-byte nonrelocatable block containing a handle to the device control entry for
each device driver.
unlock: To allow a relocatable block to be moved during heap compaction.
unmounted volume: A volume that hasn't been inserted into a disk drive and had descriptive
information read from it, or a volume that previously was mounted and has since had the memory
used by it released.
unpurgeable block: A relocatable block that can't be purged from the heap.
update event: An event generated by the Window Manager when a window's contents need to
be redrawn.
update region: A window region consisting of all areas of the content region that have to be
redrawn.
user bytes: Four bytes in an ATP header provided for use by A TP's clients.
User Interface Toolbox: The software in the Macintosh ROM that helps you implement the
standard Macintosh user interface in your application.
validity status: A number stored in parameter RAM designating whether the last attempt to
write there was successful. (The number is $A8 if so.)
variation code: The part of a window or control definition ID that distinguishes closely related
types of windows or controls.
Glossary 1//-257

<!-- source-page: 265 -->
## Page 265

Inside Macintosh
VBL task: A task performed during the vertical retrace interrupt.
vector table: A table of interrupt vectors in low memory.
version data: In an application's resource file, a resource that has the application's signature as
its resource type; typically a string that gives the name, version number, and date of the
application.
version number: A number from 0 to 255 used to distinguish between files with the same
name.
Versatile Interface Adapter (VIA): The chip that handles most of the Macintosh's 1/0 and
interrupts.
vertical blanking interrupt: See vertical retrace interrupt.
vertical blanking interval: The time between the display of the last pixel on the bottom line of
the screen and the first one on the top line.
vertical retrace interrupt: An interrupt generated 60 times a second by the Macintosh video
circuitry while the beam of the display tube returns from the bottom of the screen to the top; also
known as vertical blanking interrupt.
Vertical Retrace Manager: The part of the Operating System that schedules and executes tasks
during the vertical retrace interrupt.
vertical retrace queue: A list of the tasks to be executed during the vertical retrace interrupt.
VIA: See Versatile Interface Adapter.
view rectangle: In TextEdit, the rectangle in which the text is visible.
visible control: A control that's drawn in its window (but may be completely overlapped by
another window or other object on the screen).
visible window: A window that's drawn in its plane on the desktop (but may be completely
overlapped by another window or object on the screen).
visRgn: The region of a gratPort, manipulated by the Window Manager, that's actually visible
on the screen.
volume: A piece of storage medium formatted to contain files; usually a disk or part of a disk.
A 400K-byte 3 1/2-inch Macintosh disk is one volume.
volume allocation block map: A list of 12-bit entries, one for each allocation block, that
indicate whether the block is currently allocated to a file, whether it's free for use, or which block
is next in the file. Block maps exist both on volumes and in memory.
volume attributes: Information contained on volumes and in memory indicating whether the
volume is locked, whether it's busy (in memory only), and whether the volume control block
matches the volume information (in memory only).
ll/-258 Glossary

<!-- source-page: 266 -->
## Page 266

Glossary
volume buffer: Memory used initially to load the master directory block, and used thereafter
for reading from files that are opened without an access path buffer.
volume control block: A nonrelocatable block that contains volume-specific information,
including the volume information from the master directory block.
volume-control-block queue: A list of the volume control blocks for all mounted volumes.
volume index: A number identifying a mounted volume listed in the volume-control-block
queue. The first volume in the queue has an index of l, and so on.
volume information: Volume-specific information contained on a volume, including the
volume name and the number of files on the volume.
volume name: A sequence of up to 27 printing characters that identifies a volume; followed by
a colon(:) in File Manager routine calls, to distinguish it from a file name.
volume reference number: A unique number assigned to a volume as it's mounted, used to
refer to the volume.
waveform: The physical shape of a wave.
waveform description: A sequence of bytes describing a waveform.
wavelength: The horizontal extent of one complete cycle of a wave.
window: An object on the desktop that presents information, such as a document or a message.
window class: In a window record, an indication of whether a window is a system window, a
dialog or alert window, or a window created directly by the application.
window definition function: A function called by the Window Manager when it needs to
perform certain type-dependent operations on a particular type of window, such as drawing the
window frame.
window definition ID: A number passed to window-creation routines to indicate the type of
window. It consists of the window definition function's resource ID and a variation code.
window frame: The structure region of a window minus its content region.
window list: A list of all windows ordered according to their front-to-back positions on the
desktop.
Window Manager: The part of the Toolbox that provides routines for creating and
manipulating windows.
Window Manager port: A grafPort that has the entire screen as its portRect and is used by the
Window Manager to draw window frames.
window record: The internal representation of a window, where the Window Manager stores
all the information it needs for its operations on that window.
Glossary III-259

<!-- source-page: 267 -->
## Page 267

Inside Macintosh
window template: A resource that contains information from which the Window Manager can
create a window.
word: In TextEdit, any series of printing characters, excluding spaces (ASCII code $20) but
including nonbreaking spaces (ASCII code $CA).
word wraparound: Keeping words from being split between lines when text is drawn.
write data structure: A data structure used to pass information to the ALAP or DDP modules.
zone: An arbitrary subset of AppleTalk networks in an internet. See also heap zone.
zone header: The internal "housekeeping" information maintained by the Memory Manager at
the beginning of each heap zone.
zone pointer: A pointer to a zone record.
zone record: A data structure representing a heap zone.
zone trailer: A minimum-size free block marking the end of a heap zone.
III-260 Glossary

<!-- source-page: 268 -->
## Page 268

INDEX
A
ABByte data type 11-276
ABCallType data type 11-274
ABProtoType data type II-274
ABRecHandle data type II-274
ABRecPtr data type II-274
ABusRecord data type 11-274
ALAP parameters 11-276
ATP parameters II-287
DDP parameters 11-281
NBP parameters 11-298
ABusVars global variable II-328
access path 11-83
access path buffer II-84
ACount global variable 1-423
action procedure 1-316, 324, 328
in control definition function 1-332
activate event 1-244, 279
event message 1-252
active
control I-313
window 1-46, 270, 284
AddPt procedure 1-193
AddrBlock data type 11-281
AddResMenu procedure I-353
AddResource procedure 1-124
AddResponse function 11-318
address mark II-211
ALAP See AppleTalk Link Access Protocol
ALAP frame II-264
ALAP protocol type 11-264
alert 1-401, 409
guidelines 1-68
alert box 1-401
Alert function I-418
alert stages 1-409
alert template 1-403, 424
resource format 1-426
alert window 1-402
AlertTemplate data type 1-424
AlertTHndl data type 1-425
AlertTPtr data type 1-425
alias 11-266
Allocate function
high-level 11-94
low-level 11-113
allocated block 11-10
allocation block 11-79
amplitude of a wave 11-223
AngleFromSlope function 1-476
ANumber global variable 1-423
ApFontID global variable 1-219
AppendMenu procedure 1-352
AppFile data type 11-58
Apple menu 1-54
AppleTalk address 11-265
AppleTalk Link Access Protocol 11-263
assembly language II-306
data reception JI-325
Pascal 11-276
AppleTalk Manager 1-13; 11-261, 271
assembly language 11-304
Pascal 11-273
AppleTalk Transaction Protocol 11-266, 267
assembly language 11-312
Pascal 11-287
application font I-219
application heap 1-74; II-9
limit II-17, 29
application parameters 11-20
application space 11-20
application window 1-270
ApplicZone function 11-32
App!Limit global variable 11-19, 21, 29
AppIScratch global variable 1-85
AppIZone global variable II-19, 21, 32
AppParmHandle global variable II-57
a1rnw cursor 1-163, 167
arrow global variable 1-147, 163
ascent of a font 1-228
in TextEdit 1-378
ASCII codes 1-247
assembly language 1-83
asynchronous communication II-245
asynchronous execution
AppleTalk Manager II-273
Device Manager 11-180
File Manager 11-97
at-least-once transaction II-266
ATP See AppleTalk Transaction Protocol
ATPAddRsp function 11-295
ATPCloseSocket function 11-291
ATPGetRequest function II-293
ATPLoad function 11-290
ATPOpenSocket function 11-290
ATPReqCancel function 11-293
ATPRequest function 11-292
JJl-261

<!-- source-page: 269 -->
## Page 269

Inside Macintosh
ATPResponse function 11-296
ATPRspCancel function II-296
ATPSndRequest function 11-291
ATPSndRsp function 11-294
ATPUnload function 11-290
AttachPH function 11-308
auto-key event 1-244, 246
auto-key rate 1-246; 11-371
auto-key threshold 1-246; II-371
auto-pop bit 1-89
automatic scrolling 1-48
in TextEdit 1-380
B
BackColor procedure 1-174
background procedure Il-153
BackPat procedure 1-167
base line 1-227
baud rate 11-246, 251, 254
BDSElement data type II-288
BDSPtr data type II-288
BDSType data type 11-288
BeginUpdate procedure 1-292
Binary-Decimal Conversion Package 1-12,
487
bitimage 1-143
bit manipulation 1-470
bit map
AppleTalk Manager 11-268
printing 11-164
QuickDraw I-144
BitAnd function 1-471
BitClr procedure 1-471
BitMap data type 1-144
BitMapType data type 11-287
BitNot function I-471
BitOr function 1-471
Bits16 data type 1-146
BitSet procedure 1-471
BitShift function I-472
BitTst function 1-471
BitXor function 1-471
black global variable 1-162
block (file) See allocation block
block (memory) I-73; II-10
block contents II-10
block device 11-175
block header II-10
structure 11-24
block map II-122
III-262
BlockMove procedure 11-44
boot blocks See system startup information
boundary rectangle 1-144
break 11-246
bridge II-265
BringToFront procedure 1-286
broadcast service 11-264
ButPtr global variable 11-19, 21
BuffgDate global variable II-212
BuffgFBkNum global variable 11-212
BuffgFFlag global variable 11-212
BuffgFNum global variable 11-212
bundle 11-85; IIl-11
resource format III-12
Button function 1-259
button type of control 1-311, 404
Byte data type 1-78
c
CalcMenuSize procedure 1-361
CalcVBehind procedure 1-297
Cale Vis procedure 1-297
CalcVisBehind procedure 1-297
caret 1-376, 379
caret-blink time I-260; 11-371
CaretTime global variable 1-260
CautionAlert function 1-420
Chain procedure 11-59
ChangedResource procedure I-123
character codes 1-246
character device II-17 5
character image 1-227
character keys 1-33, 246
character offset 1-228
character origin 1-228
character position I-375
character rectangle 1-228
character set 1-247
character style 1-151
of menu items 1-348, 360
character width 1-173, 228
Chars data type 1-384
CharsHandle data type 1-384
CharsPtr data type 1-384
CharWidth function 1-173
check box 1-312, 404
check mark in a menu I-347, 358
Checkltem procedure 1-358
CheckUpdate function I-296
ClearMenuBar procedure 1-354

<!-- source-page: 270 -->
## Page 270

click See mouse-down event
click loop routine 1-380
ClipAbove procedure 1-296
Clipboard I-58 See also scrap
clipping region of a grafPort I-149
ClipRect procedure 1-167
clipRgn of a grafPort 1-149
clock chip 11-369
hardware 111-36
close box See go-away region
Close command 1-56
Close function, high-level
Device Manager 11-178
File Manager 11-94
Close function, low-level
Device Manager II-184
File Manager 11-114
close routine
of a desk accessory 1-446
of a driver 11-187, 193
CloseATPSkt function 11-316
closed device driver 11-176
closed file 11-83
CloseDeskAcc procedure 1-440
CloseDialog procedure 1-413
CloseDriver function Il-178
ClosePgon procedure I-190
ClosePicture procedure 1-189
ClosePoly procedure I-190
ClosePort procedure I-164
CloseResFile procedure I-115
CloseRgn procedure I-182
CloseSkt function 11-312
CloseWindow procedure I-283
ClrAppFiles procedure II-58
CmpString function II-377
color drawing 1-158, 173
ColorBit procedure I-174
Command-key equivalent See keyboard
equivalent
Command-period II-154
Command-Shift-number I-258
commands 1-51, 341
compaction, heap 1-74; 11-12, 39
CompactMem function II-39
completion routine
Device Manager II-180, 181
File Manager 11-97, 99
Sound Driver II-231
ConfirmName function II-323
content region of a window 1-271
control 1-65, 311
defining your own 1-328
in a dialog/alert I-404
control definition function 1-314, 328
control definition ID I-315, 328
Control function
high-level II-179
low-level II-186
control information 11-176
control list 1-274, 317
Control Manager 1-11, 309
routines 1-319
control record 1-316
control routine
of a desk accessory I-446
of a driver 11-187, 194
control template 1-315
resource format 1-332
ControlHandle data type 1-317
ControlPtr data type 1-317
ControlRecord data type 1-317
coordinate plane I-138
CopyBits procedure I-188
CopyRgn procedure 1-183
CouldAlert procedure 1-420
CouldDialog procedure I-415
CountAppFiles procedure II-57
CountMitems function 1-361
CountResources function 1-118
CountTypes function 1-117
Create function
high-level 11-90
low-level II-107
CreateResFile procedure 1-114
creator of a file III-9
CrsrThresh global variable 11-372
Cur Activate global variable 1-280
CurApName global variable II-58
CurApRefNum global variable 11-58
CurDeactive global variable 1-280
CurJTOffset global variable II-62
CurMap global variable I-117
CurPageOption global variable II-60
CurPitch global variable 11-226, 232
current heap zone 11-10, 31
Index
current resource file 1-105, 116
CurrentA5 global variable 1-95; 11-19, 21,
386
CurResFile function I-116
CursHandle data type 1-474
III-263

<!-- source-page: 271 -->
## Page 271

Inside Macintosh
cursor 1-146
QuickDraw routines 1-167
standard cursors I-147, 474
utility routines 1-474
Cursor data type I-146
cursor level 1-167
CursPtr data type I-474
CurStackBase global variable 11-19, 21, 358
cut and paste 1-59
D
intelligent 1-63
in TextEdit 1-385
DABeeper global variable 1-411
DAStrings global array 1-421
data bits 11-245
data buffer 11-83, 176
data fork 1-105; 11-81
data mark 11-211
datagram 11-265
loss recovery 11-268
Datagram Delivery Protocol 11-265
assembly language 11-308
Pascal II-281
date operations 11-377
Date2Secs procedure 11-379
DateForm data type 1-504
date/time record 11-377
DateTimeRec data type II-378
DCtlEntry data type 11-190
DCtlHandle data type II-190
DCtlPtrdata type 11-190
DDP See Datagram Delivery Protocol
DDPCloseSocket function 11-282
DDPOpenSocket function 11-282
DDPRdCancel function 11-284
DDPRead function 11-283
DDPWrite function 11-283
default button
in an alert I-69, 401, 424
in a dialog 1-67, 400, 407
default volume 11-80
getting See GetVol function
setting See SetVol function
DefltStack global variable 11-17
DefVCBPtr global variable 11-126
Delay procedure 11-384
Delete function
high-level 11-97
low-level 11-119
JJJ-264
DeleteMenu procedure 1-354
DeltaPoint function I-475
Dequeue function II-383
dereferencing a handle 11-14
descent of a font I-228
desk accessory 1-437
writing your own 1-443
Desk Manager I-12, 435
routines 1-440
desk scrap 1-453
data types I-454
format I-462
routines 1-457
DeskHook global variable I-282, 288
DeskPattem global variable I-282
desktop 1-32, 269
Desktop file III-10
destination rectangle I-374
DetachPH function II-308
DetachResource procedure 1-120
device 11-175
device control entry II-189
device driver 1-13; II-175
for a desk accessory 1-443
structure 11-187
writing your own Il-193
device driver event 1-244
Device Manager I-13; II-173
Device Manager routines 11-177
device control entry access Il-190
high-level II-178
low-level Il-180
for writing drivers Il-194
dial 1-312
dialog box 1-66, 399
Dialog Manager I-12, 397
routines 1-411
dialog pointer I-407
dialog record I-403, 407
dialog template 1-402, 403
resource format 1-425
dialog window 1-401
DialogPeek data type 1-408
DialogPtr data type 1-407
DialogRecord data type I-408
DialogSelect function I-417
DialogTemplate data type 1-423
DialogTHndl data type 1-424
DialogTPtr data type 1-424
DIBadMount function II-396
DiffRgn procedure I-1 84
DIFormat function Il-398

<!-- source-page: 272 -->
## Page 272

DILoad procedure II-396
dimmed
control 1-313
menu item 1-342, 343
menu title 1-342
disabled
dialog/alert item 1-405
menu 1-342, 358
menu item 1-349, 358
Disableltem procedure 1-358
discontinuous selection 1-40
Disk Driver 1-13; 11-209
Device Manager calls 11-213
routines 11-214
Disk Initialization Package 1-13; 11-393
routines 11-396
disk-inserted event 1-244
event message I-252
responding to 1-257
disk interface ill-33
disk-switch dialog Il-80
DiskEject function 11-214
dispatch table See trap dispatch table
display rectangle 1-406
DisposControl procedure 1-321
DisposDialog procedure 1-415
DisposeControl procedure 1-321
DisposeMenu procedure 1-352
DisposeRgn procedure 1-182
DisposeWindow procedure 1-284
DisposHandle procedure 1-76, 80; 11-33
DisposMenu procedure 1-352
DisposPtr procedure 1-75, 79; 11-36
DisposRgn procedure 1-182
DisposWindow procedure 1-284
DIUnload procedure 11-396
DIVerify function 11-398
DIZero function 11-399
dkGray global variable 1-162
DlgCopy procedure 1-418
DlgCut procedure 1-418
DlgDelete procedure 1-418
DlgFont global variable 1-412
DlgHook function
SFGetFile 1-526
SFPutFile 1-522
DlgPaste procedure 1-418
document window 1-269
double-click 1-37, 255
double-click time 1-260; II-371
DoubleTime global variable 1-260
draft printing 11-151, 153
drag region of a window 1-271, 289
DragControl procedure 1-325
DragGrayRgn function 1-294
DragHook global variable
Control Manager 1-324, 326
Index
Window Manager 1-288, 289, 290, 295
DragPattem global variable
Control Manager 1-324, 326
Window Manager 1-295
DragTheRgn function 1-295
DragWindow procedure 1-289
DrawChar procedure 1-172
DrawControls procedure 1-322
DrawDialog procedure 1-418
DrawGrowlcon procedure 1-287
drawing 1-155
color 1-158, 173
DrawMenuBar procedure 1-354
DrawNew procedure 1-296
DrawPicture procedure 1-190
DrawString procedure 1-172
DrawText procedure 1-172
drive number 11-80
drive queue 11-127
driver See device driver
driver 110 queue 11-180, 191
driver name 11-176
driver reference number 11-176
DriveStatus function 11-215
DrvQEl data type 11-127
DrvQHdr global variable Il-128
DrvSts data type II-215
DSAlertRect global variable 11-362
DSAlertTab global variable 11-359, 362
DSErrCode global variable 11-362
E
Edit menu 1-58
and desk accessories 1-441, 447
edit record 1-374
Eject function
high-level 11-90
low-level 11-107
Elems68K See Transcendental Functions
Package
empty handle 1-76; Il-14, 40
Empty Handle procedure 11-40
EmptyRect function 1-176
EmptyRgn function 1-186
111-265

<!-- source-page: 273 -->
## Page 273

Inside Macintosh
enabled
dialog/alert item 1-405
menu 1-358
menu item I-358
Enableltem procedure 1-358
end-of-file II-81
end-of-message flag 11-270
EndUpdate procedure 1-293
Enqueue procedure 11-382
entity name II-265, 298
EntityName data type II-298
Environs procedure 11-385
EntityPtr data type 11-298
equal-tempered scale 11-237
EqualPt function 1-193
EqualRect function 1-176
EqualRgn function 1-185
EqualString function 11-377
EraseArc procedure I-180
EraseOval procedure 1-178
ErasePoly procedure I-192
EraseRect procedure 1-177
EraseRgn procedure 1-186
EraseRoundRect procedure 1-179
error number See result code
ErrorSound procedure 1-411
event 1-243
priority 1-245
event code 1-249
Event Manager, Operating System 1-13; 11-65
routines 11-68
Event Manager, Toolbox 1-11, 241
routines 1-257
event mask 1-253
event message 1-249
event queue 1-243
structure II-70
event record 1-249
event types 1-244
EventAvail function 1-259
EventQueue global variable Il-71
EventRecord data type 1-249
EvQEl data type 11-71
exactly-once transaction 11-266
example program I-13
exception 11-195
exception vector III-17
ExitToShell procedure 11-59
exponential functions 11-407
extended selection I-39
in TextEdit 1-384
external file system 11-128
III-266
external reference 1-95
ExtStsDT global variable 11-199
F
FCBSPtr global variable II-127
Fetch function 11-194
FFSynthPtr data type II-228
FFSynthRec data type II-228
file II-79, 81
file control block II-126
file-control-block buffer 11-126
file creator III-9
file directory II-79, 122
file icon 11-85; Ill-10
file 1/0 queue II-97, 124
File Manager 1-13; 11-77
File Manager routines
high-level II-88
low-level 11-97
for queue access II-125, 126, 128
File menu 1-55
file name II-81
file number 11-122
file reference III-10
resource format III-12
file tags 11-212
file tags buffer 11-212
file type III-9
fileFilter function 1-524
FillArc procedure 1-181
FillOval procedure 1-178
FillPoly procedure 1-192
Fi II Re ct procedure 1-1 77
FillRgn procedure 1-187
FillRoundRect procedure 1-179
filterProc function 1-415
financial functions 11-407
FindControl function I-323
Finder information 11-55
Finder interface II-55, 84; III-7
FinderName global variable II-59
FindWindow function I-287
Flnfo data type 11-84
FinitQueue procedure 11-103
Fixed data type I-79
fixed-point
arithmetic I-467
numbers 1-79
fixed-width font 1-228
FixMul function I-467

<!-- source-page: 274 -->
## Page 274

FixRatio function 1-467
FixRound function 1-467
FlashMenuBar procedure 1-361
Floating-Point Arithmetic Package 1-13; 11-403
FlushEvents procedure 11-69
FlushFile function 11-114
FlushVol function
high-level 11-89
low-level 11-105
FMlnput data type 1-224
FMOutPtr data type 1-227
FMOutput data type 1-227
FMSwapFont function 1-223
folder 11-85
font 1-60, 151, 217
characters 1-220
format 1-227
resource format 1-234
resource ID 1-234
font characterization table 1-225
font height 1-228
Font Manager 1-11, 215
communication with QuickDraw 1-224
routines 1-222
Font menu 1-60, 353
font number 1-217, 219
font record 1-230
font rectangle 1-228
font scaling 1-220
font size 1-153, 217
Fontinfo data type 1-173
FontRec data type 1-231
FontSize menu 1-61
ForeColor procedure 1-173
fork 1-105; 11-81
four-tone record 11-227
four-tone synthesizer 11-223, 226
FP68K See Floating-Point Arithmetic Package
frame
ALAP 11-264
picture 1-158
serial communication 11-246
stack 1-96; 11-17
window 1-271
frame check sequence 11-265
frame header 11-264
frame pointer (stack) 1-96
frame trailer 11-264
FrameArc procedure 1-180
FrameOval procedure 1-177
FramePoly procedure 1-192
FrameRect procedure 1-17 6
FrameRgn procedure 1-186
FrameRoundRect procedure 1-178
framing error 11-246
free-form synthesizer 11-223, 228
free memory block 11-10
FreeAlert procedure 1-420
FreeDialog procedure 1-415
FreeMem function 11-38
Free Wave data type 11-228
frequency of a wave II-223
FrontWindow function 1-286
FScaleDisable global variable 1-222
FSClose function 11-94
FSDelete function II-97
FSOpen function 11-91
FSQHdr global variable 11-125
FSRead function
Device Manager II-178
File Manager 11-92
FSWrite function
Device Manager 11-179
File Manager 11-92
FI'SndRecPtr data type 11-227
FI'SoundRec data type 11-227
FI'SynthPtr data type 11-227
FI'SynthRec data type 11-227
full-duplex communication 11-245
G
GetAlrtStage function 1-422
GetAppFiles procedure 11-58
GetApplLimit function 11-29
GetAppParms procedure II-58
GetCaretTime function 1-260
GetClip procedure 1-167
GetCRefCon function 1-327
GetCTitle procedure 1-321
GetCtlAction function 1-328
GetCtlMax function 1-327
GetCtlMin function 1-327
GetCtlValue function 1-326
GetCursor function 1-474
GetDateTime procedure 11-378
GetDblTime function 1-260
GetDCtlEntry function 11-190
GetDltem procedure 1-421
GetDrvQHdr function 11-128
GetEOF function
high-level 11-93
low-level 11-112
Index
III-267

<!-- source-page: 275 -->
## Page 275

Inside Macintosh
GetEvQHdr function 11-71
GetFilelnfo function
high-level II-95
low-level 11-115
GetFinfo function II-95
GetFName procedure 1-223
GetFNum procedure 1-223
GetFontlnfo procedure 1-173
GetFontName procedure 1-223
GetFPos function
high-level II-92
low-level 11-111
GetFSQHdr function 11-125
GetHandleSize function 11-33
Getlcon function 1-473
GetlndPattern procedure 1-473
GetlndResource function 1-118
GetlndString procedure 1-468
GetlndType procedure 1-117
Getltem procedure 1-358
Getltemlcon procedure 1-360
GetltemMark procedure 1-359
GetltemStyle procedure 1-360
GetlText procedure I-422
Getltmlcon procedure 1-360
GetltmMark procedure 1-359
GetltmStyle procedure I-360
GetKeys procedure 1-259
GetMaxCtl function I-327
GetMenu function 1-351
GetMenuBar function I-355
GetMHandle function I-361
GetMinCtl function 1-327
GetMouse procedure 1-259
GetNamedResource function 1-119
GetNewControl function 1-321
GetNewDialog function I-413
GetNewMBar function 1-354
GetNewWindow function 1-283
GetNextEvent function 1-257
GetNodeAddress function II-303
GetOSEvent function II-69
GetPattem function 1-473
GetPen procedure 1-169
GetPenState procedure 1-169
GetPicture function 1-475
GetPixel function 1-195
GetPort procedure 1-165
GetPtrSize function II-37
GetRequest function 11-317
GetResAttrs function 1-121
///-268
GetResFileAttrs function 1-127
GetReslnfo procedure 1-121
GetResource function 1-119
GetRMenu function 1-351
GetScrap function 1-469
GetSoundVol procedure II-232
GetString function 1-468
GetSysPPtr function 11-381
GetTime procedure 11-380
GetTrapAddress function 11-384
GetVBLQHdr function II-352
GetVCBQHdr function 11-126
GetVInfo function II-89
GetVol function
high-level 11-89
low-level ll-104
GetVollnfo function
high-level 11-89
low-level 11-104
GetVRefNum function II-89
GetWindowPic function 1-293
GetWMgrPort procedure 1-282
GetWRefCon function 1-293
GetWTitle procedure 1-284
GetZone function 11-31
GhostWindow global variable 1-287
global coordinates I-155
global variables
list III-227
QuickDraw 1-138, 162
GlobalToLocal procedure 1-193
go-away region of a window 1-271, 288
GrafDevice procedure 1-165
grafPort 1-147
routines 1-162
GrafPort data type 1-148
GrafPtr data type 1-148
GrafVerb data type 1-198
gray global variable I-162
GrayRgn global variable I-282, 296
grow image of a window 1-289
grow region of a window I-272, 289
grow zone function 11-14, 42
GrowWindow function 1-289
GZRootHnd global variable 11-43
GZSaveHnd function 11-43
H
HandAndHand function 11-375

<!-- source-page: 276 -->
## Page 276

handle 1-75, 78; II-12
dereferencing 11-14
empty 11-40
manipulation 11-374
Handle data type 1-78
HandleZone function 11-34
HandToHand function 11-374
hardware 111-15
hardware overrun error II-246
heap 1-12, 23; 11-9, 17
compaction I-74; 11-12, 39
creating on the stack 11-45
zone 11-9, 22
HeapEnd global variable 11-19, 21
HideControl procedure 1-322
HideCursor procedure 1-168
HidePen procedure 1-168
HideWindow procedure 1-283
highlighted 1-31
control 1-313
menu title 1-357
window 1-270
HiliteControl procedure 1-322
HiliteMenu procedure 1-357
HiliteWindow procedure 1-286
HiWord function 1-472
HLock procedure 11-41
HNoPurge procedure II-42
HomeResFile function 1-117
horizontal blanking interval III-18
hotSpot of a cursor 1-146
HPurge procedure 11-41
HUnlock procedure 11-41
icon 1-32
in a dialog/alert 1-404
for a file 11-85; III-10
in a menu 1-347, 359
utility routines 1-473
icon list III-11
resource format 1-476; III-12
icon number 1-347
image width 1-228
inactive
control I-313
window 1-46, 270
indicator of a dial 1-312
lnfoScrap function 1-457
InitAUPacks procedure 1-484
lnitApplZone procedure II-28
Ini tCursor procedure 1-167
lnitDialogs procedure 1-411
lnitFonts procedure I-222
Ini tGraf procedure 1-162
lnitMenus procedure 1-351
lnitPack procedure 1-484
lnitPort procedure 1-164
InitQueue procedure 11-103
InitResources function 1-114
InitUtil function 11-380
InitWindows procedure I-281
InitZone procedure 11-29
input driver 11-246
insertion point 1-41, 375
lnsertMenu procedure 1-353
lnsertResMenu procedure 1-353
lnsetRect procedure 1-175
InsetRgn procedure 1-184
lnt64Bit data type 1-472
interface routine 1-95
Index
international resources 1-495
International Utilities Package 1-12, 493
routines 1-504
internet 11-265
internet address 11-265, 314
interrupt 11-195
level-1 (VIA) II-197; III-38
level-2 (SCC) 11-198
level-3 11-196
vertical retrace 11-349
interrupt handler 11-195
writing your own 11-200
interrupt priority level 11-196
interrupt vector 11-196
IntlOHndl data type 1-496
IntlOPtr data type I-496
IntlORec data type 1-497
lntllHndl data type 1-500
lntllPtr data type 1-500
IntllRec data type 1-500
InvalRect procedure 1-291
lnvalRgn procedure 1-291
lnverRect procedure 1-177
lnverRgn procedure 1-186
lnverRoundRect procedure 1-179
lnvertArc procedure 1-181
InvertOval procedure 1-178
InvertPol y procedure 1-192
InvertRect procedure 1-177
InvertRgn procedure I-186
InvertRoundRect procedure 1-179
///-269

<!-- source-page: 277 -->
## Page 277

Inside Macintosh
invisible
control 1-316
dialog/alert item 1-406
file icon 11-85
window 1-274
IODone function 11-195
1/0 queue See driver 1/0 queue or file 1/0
queue
1/0 request 11-97, 180
lsATPOpen function 11-304
lsDialogEvent function 1-416
lsMPPOpen function II-304
item
dialog/alert 1-403
menu I-341
item list 1-403
resource fonnat 1-427
item number
dialog/alert I-406
menu 1-350
item type 1-404
IUCompString function I-506
IUDatePString procedure 1-505
IUDateString procedure 1-504
IUEqua!String function 1-506
IUGetlntl function 1-505
IUMaglDString function 1-507
IUMagString function 1-506
IUMetric function 1-505
IUSetlntl procedure 1-506
IUTimePString procedure 1-505
IUTimeString procedure 1-505
IWM Ill-17
IWM global variable III-34
J
JFetch global variable 11-194
JIODone global variable 11-195
job dialog 11-149
job subrecord II-150
journal code 1-262
Journa!Flag global variable 1-261
journaling mechanism 1-261
Journa!Ref global variable 1-261
JStash global variable 11-195
jump table 11-60
jump vector 11-194
just-tempered scale 11-237
justification 1-376
setting 1-387
///-270
K
kerning 1-152, 228
key codes 1-250
key-down event 1-244
responding to 1-256
key-up event I-244, 254
keyboard 1-33
hardware Ill-29
keyboard configuration 1-248
keyboard equivalent 1-343
meta-chai:acter 1-348
responding to I-356
standard equivalents 1-53
keyboard event 1-244, 246
event message 1-250
responding to 1-256
keyboard touch See auto-key threshold
KeyMap data type 1-260
keypad 1-35
hardware III-29
KeyRepThresh global variable 1-246
KeyThresh global variable 1-246
KiIIControls procedure 1-321
KillIO function
high-level 11-179
low-level 11-187
KillPicture procedure 1-190
KillPoly procedure 1-191
L
LAPAdrBlock data type 11-276
LAPCloseProtocol function 11-277
LAPOpenProtocol function 11-277
LAPRdCancel function 11-279
LAPRead function 11-278
LAPWrite function 11-277
Launch procedure 11-60
leading 1-228
ligatures 1-501
line height 1-378
Line procedure 1-171
LineTo procedure 1-170
list separator 1-497
Lo3Bytes global variable 1-85; 11-25
LoadNBP function 11-324
LoadResource procedure 1-119
LoadScrap function 1-458
LoadSeg procedure 11-60
local coordinates 1-153

<!-- source-page: 278 -->
## Page 278

local ID III-10
LocalToGlobal procedure 1-193
location table 1-231
lock bit 11-25
locked block 1-76; 11-10
locked file 11-84
locked volume II-80
locking a block 1-76; 11-41
LodeScrap function 1-458
logarithmic functions 11-407
logical block II-119
logical end-of-file 11-81
logical operations 1-471
logical size of a block 11-22
LongMul procedure 1-472
LookupName function 11-323
LoWord function 1-472
ltGray global variable 1-162
LvllDT global variable 11-197
Lvl2DT global variable 11-198
M
magnitude of a wave 11-223
main event loop 1-16
main segment 11-55
MapPoly procedure 1-197
MapPt procedure 1-196
MapRect procedure 1-196
MapRgn procedure 1-196
mark
in a file 11-82
in a menu 1-347, 359
mark state 11-245
master directory block 11-120
master pointer 1-75; 11-12
allocation 11-22, 31
structure 11-25
MaxApp!Zone procedure 11-30
MaxMem function 11-38
MBarEnable global variable 1-356, 446
MBarHook global variable 1-356
MemError function 11-44
memory block 1-73; II-10
memory management II-7
introduction 1-71
Memory Manager 1-12; 11-7
routines II-27
memory organization 11-19
MemTop global variable II-19, 21, 44
menu 1-341
defining your own I-362
guidelines I-51
resource format 1-364
standard menus 1-54, 342
menu bar 1-341
resource format 1-365
menu definition procedure 1-344, 362
menu ID I-344
menu item 1-341
blinking 1-361; 11-371
menu item number I-350
menu list 1-345
Menu Manager I-12, 339
routines 1-351
menu record 1-344
menu title I-341
MenuFlash global variable 1-361
MenuHandle data type I-345
MenuHook global variable 1-356
Menulnfo data type 1-345
MenuKey function I-356
MenuList global variable 1-346
MenuPtr data type I-345
MenuSelect function I-355
meta-characters
AppleTalk Manager 11-266, 320
Menu Manager 1-346
MinStack global variable 11-17
MinusOne global variable I-85
missing symbol 1-152, 220, 230
modal dialog box I-67, 400, 415
ModalDialog procedure 1-415
modeless dialog box 1-67, 400, 416
modes 1-28
modifier flags 1-252
modifier keys 1-34, 246
flags in event record 1-252
MoreMasters procedure 11-31
mounted volume 11-79
MountVol function II-103
mouse 1-36
hardware III-25
mouse-down event 1-244
responding to 1-255
mouse scaling 11-372
mouse-scaling threshold 11-372
mouse-up event 1-244
responding to 1-255
Move procedure 1-170
MoveControl procedure I-325
Index
III-271

<!-- source-page: 279 -->
## Page 279

Inside Macintosh
MoveHHi procedure II-44
MovePortTo procedure 1-166
MoveTo procedure 1-170
MoveWindow procedure 1-289
MPP II-271
MPPClose function II-275
MPPOpen function II-275
Munger function 1-468
N
Name-Binding Protocol 11-266
assembly language II-319
Pascal II-298
name lookup II-266
names directory 11-266
names information socket ll-266
names table 11-266, 321
NBP See Name-Binding Protocol
NBP tuple 11-266
NBPConfirm function 11-301
NBPExtract function 11-300
NBPLoad function 11-301
NBPLookup function 11-300
NBPRegister function 11-299
NBPRemove function 11-301
NBPUnJoad function 11-301
network event I-244; 11-275
network number 11-265
network-visible entity 11-265
New command 1-56
NewControl function 1-319
NewDialog function 1-412
NewHandle function 1-76, 80; 11-32
newline character II-84
newline mode 11-84
NewMenu function 1-351
NewPtr function 1-75, 79; 11-36
NewRgn function 1-181
NewString function 1-468
NewWindow function 1-282
node 11-263
node ID 11-263
nonbreaking space 1-246
nonrelocatable block 1-75; 11-10
allocating 11-36
releasing 11-36
NoteAlert function 1-420
null event 1-245
NumToString procedure 1-489
III-272
0
ObscureCursor procedure 1-168
off-line volume II-80
OftLine function 11-106
OffsetPoly procedure 1-191
OffsetRect procedure 1-174
OffsetRgn procedure 1-183
offset/width table 1-231
OfsetRgn procedure 1-18 3
OldContent global variable 1-296
OldStructure global variable 1-296
on-line volume 11-80
OneOne global variable 1-85
Open command 1-56
open device driver 11-176
open file 11-83
Open function, high-level
Device Manager 11-178
File Manager II-91
Open function, low-level
Device Manager 11-184
File Manager 11-108
open permission 11-83
open routine
of a desk accessory 1-445
of a driver Il-187, 193
OpenA TPSkt function 11-315
OpenDeskAcc function 1-440
OpenDriver function II-178
OpenPicture function 1-189
OpenPoly function 1-190
OpenPort procedure 1-163
OpenResFile function 1-115
OpenRF function
high-level II-91
low-level II-109
OpenRgn procedure 1-181
OpenSkt function 11-311
Operating System 1-9
queues 11-372
Operating System Event Manager 1-13; 11-65
routines Il-68
Operating System Utilities 1-13; 11-367
routines 11-374
OSErr data type 11-373
OSEventA vail function 11-70
OSType data type II-373
output driver 11-246
overrun error See hardware overrun error or
software overrun error
owned resources 1-109

<!-- source-page: 280 -->
## Page 280

p
Pack2 See Disk Initialization Package
Pack3 See Standard File Package
Pack4 See Floating-Point Arithmetic Package
Pack5 See Transcendental Functions Package
Pack6 See International Utilities Package
Pack? See Binary-Decimal Conversion
Package
Package Manager I-12, 481
packages I-12, 483
PackBits procedure 1-470
page rectangle 11-150
Page Setup command I-57
PaintArc procedure I-180
PaintBehind procedure 1-297
PaintOne procedure I-296
PaintOval procedure I-178
PaintPoly procedure I-192
PaintRect procedure I-177
PaintRgn procedure 1-186
PaintRoundRect procedure I-179
PaintWhite global variable 1-297
palette I-32
pane I-49
panel I-50
paper rectangle 11-150
ParamBlkType data type 11-98, 181
ParamBlockRec data type 11-98, 181
driver I/O queue entry II-191
file I/O queue entry 11-124
parameter block 1-93; II-97, 180
parameter RAM II-369
default values 11-370
routines II-380
ParamText procedure I-421
parity bit II-245
parity error II-246
ParmBlkPtr data type 11-98, 181
part code 1-315, 330
path reference number 11-83
PatHandle data type 1-473
PatPtr data type 1-473
pattern I-145, 473
Pattern data type I-146
pattern list 1-473
resource format 1-476
pattern transfer mode 1-157
PBAllocate function 11-113
PBClose function
Device Manager 11-184
File Manager Il-114
PBControl function Il-186
PBCreate function 11-107
PBDelete function 11-119
PBEject function 11-107
PBFlushFile function II-114
PBFlushVol function II-105
PBGetEOF function II-112
PBGetFinfo function 11-115
PBGetFPos function II-111
PBGetVInfo function 11-104
PBGetVol function 11-104
PBKillIO function II-187
PBMountVol function 11-103
PBOffLine function II-106
PBOpen function
Device Manager 11-184
File Manager 11-108
PBOpenRF function II-109
PBRead function
Device Manager II-185
File Manager 11-110
PBRename function 11-118
PBRstFLock function 11-117
PBSetEOF function 11-112
PBSetFlnfo function 11-116
PBSetFLock function 11-116
PBSetFPos function 11-111
PBSetFVers function 11-117
PBSetVol function II-105
PBStatus function 11-186
PBUnmountVol function 11-106
PBWrite function
Device Manager 11-185
File Manager 11-110
pen characteristics I-150
PenMode procedure 1-169
PenNormal procedure 1-170
PenPat procedure I-170
PenSize procedure 1-169
PenState data type 1-169
period of a wave 11-223
phase of a wave cycle 11-223
physical end-of-file 11-81
physical size of a block 11-23
PicComment procedure 1-189
PicHandle data type 1-159
PicPtr data type 1-159
picture 1-158
QuickDraw routines I-189
utility routine I-475
picture comments I-159
Picture data type I-159
Index
lll-273

<!-- source-page: 281 -->
## Page 281

Inside Macintosh
picture frame I-158
PinRect function 1-293
pixel I-139, 143
Plotlcon procedure 1-473
point (coordinate plane) 1-139
routines 1-193
point (font size) 1-61, 153, 217
Point data type 1-139
pointer (to memory) 1-75, 78; 11-11
manipulation II-374
type coercion I-79
pointer (on screen) 1-36, 37 See also cursor
polygon 1-159
routines 1-190
Polygon data type 1-159
PolyHandle data type 1-160
PolyPtr data type 1-160
portBits of a grafPort 1-148
PortBUse global variable II-305
portRect of a grafPort 1-149
PortSize procedure I-165
post an event 1-243
PostEvent function 11-68
PrClose procedure 11-157
PrCloseDoc procedure 11-160
PrClosePage procedure 11-160
PrCtlCall procedure 11-163
PrDrvrClose procedure II-163
PrDrvrDCE function II-163
PrDrvrOpen procedure 11-163
PrDrvrVers function II-1 63
PrError function 11-161
prime routine of a driver JI-187, 193
Print command 1-57
print dialogs II-148
print record 11-148
PrintDefault procedure 11-158
Printer Driver 1-13; 11-147, 162
printer information subrecord 11-150
printer resource file 11-147
PrintErr global variable 11-161
printing grafPort II-147
Printing Manager 1-13; 11-145
routines 11-157
printing methods 11-153
low-level IJ-164
private scraps 1-461
PrJobDialog function 11-158
PrJobMerge procedure Il-159
processor priority 11-196
ProcPtr data type 1-78
///-274
PrOpen procedure 11-157
PrOpenDoc function Il-159
PrOpenPage procedure II-159
proportional font 1-228
protocol 11-263
protocol handler II-264
writing your own ll-324, 326
protocol handler table 11-264
PrPicFile procedure II-160
PrSetError procedure II-161
PrSt!Dialog function II-158
PrValidate function II-158
PScrapStuff data type 1-457
Pt2Rect procedure l-175
PtlnRect function l-175
PtinRgn function 1-185
Ptr data type I-78
PtrAndHand function II-376
PtrToHand function Il-375
PtrToXHand function II-375
PtrZone function 11-38
PtToAngle procedure I-175
purge bit II-25
purge warning procedure 11-23
purgeable block I-76; II-10, 41
PurgeMem procedure II-40
purging a block 1-76; II-14, 40
PutScrap function 1-459
a
QDProcs data type 1-197
QDProcsPtr data type 1-197
QE!em data type 11-373
QElemPtr data type 11-373
QHdr data type 11-372
QHdrPtr data type II-373
QTypes data type II-373
queue 11-373
drive 11-127
driver 1/0 11-180, 191
file 110 II-97, 124
manipulation ll-382
vertical retrace II-350, 352
volume-control-block II-125
QuickDraw 1-11, 135
communication with Font Manager I-224
routines 1-162
Quit command 1-57

<!-- source-page: 282 -->
## Page 282

R
radio button 1-312, 404
RAM III-17
RAM Serial Driver 1-13; II-246
advanced Control calls II-254
Device Manager calls II-248
routines 11-249
RAMBase global variable 1-87
RAMSDClose procedure 11-250
RAMSDOpen function 11-249
Random function 1-194
random number generator 1-194; II-407
randSeed global variable 1-163, 194
Read function, high-level
Device Manager 11-178
File Manager 11-92
Read function, low-level
Device Manager 11-185
File Manager 11-110
ReadDateTime function 11-378
ReadPacket function 11-327
ReadRest function 11-327
read/write permission Il-83
RealFont function 1-223
reallocating a block 1-76; 11-14
ReallocHandle procedure II-35
RecoverHandle function II-35
Rect data type 1-141
rectangle 1-140
routines 1-174
RectlnRgn function 1-185
RectRgn procedure 1-183
reference number of a resource file 1-105
reference value
control 1-316
window 1-274
region 1-141
routines I-181
Region data type 1-142
register-based routines 1-90, 93
register-saving conventions I-94
RegisterName function II-322
relative handle 11-24
release timer 11-270
ReleaseResource procedure 1-120
relocatable block 1-75; II-10
allocating 11-32
releasing 11-33
RelRspCB function 11-319
RelTCB function II-319
RemoveNarne function 11-324
Rename function
high-level 11-96
low-level 11-118
ResErr global variable 1-116
ResError function l-116
ResErrProc global variable J-116
ResetAlrtStage procedure 1-423
ResLoad global variable I-118
resource 1-103
within a resource 1-127
resource attributes 1-111
getting I-121
setting 1-122
resource data 1-106
resource file 1-105
attributes 1-126
current 1-105, 116
format 1-128
resource fork 1-105; II-8 1
resource header 1-128
resource ID 1-108
of fonts I-234
of owned resources I-109
Resource Manager 1-9, 101
routines I-113
resource map 1-106
resource name 1-110
resource reference 1-110
format I-130
resource specification 1-103, 107
resource type 1-103
list 1-107
response BDS 11-288, 314
ResrvMem procedure 11-39
Restart procedure Il-385
RestoreA5 procedure 11-386
ResType data type 1-107
result code I-116; 11-27, 374
assembly language 1-94
list III-205
resume procedure 1-411 ; 11-35 8
ResumeProc global variable 1-411
RetransType data type 11-298
retry count 11-266
retry interval 11-266
Revert to Saved command 1-57
RgnHandle data type 1-142
RgnPtr data type 1-142
RmveResource procedure J-124
RndSeed global variable 1-195
ROM III-18
Index
III-275

<!-- source-page: 283 -->
## Page 283

Inside Macintosh
ROM Serial Driver 1-13; 11-246
Device Manager calls 11-248
routines 11-250
ROMBase global variable 1-87; 11-383; III-18
ROMFontO global variable I-233
routine selector 1-483
routing table II-265
Routing Table Maintenance Protocol II-265
row width 1-143
RsrcZonelnit procedure 1-114
RstFilLock function
high-level II-96
low-level II-117
RstFLock function 11-96
RTMP II-265
RTMP socket II-265
RTMP stub II-265
$
sample program 1-13
SANE II-405
Save As command 1-57
Save command 1-57
SaveOld procedure 1-296
SaveUpdate global variable 1-297
SaveVisRgn global variable 1-293
ScalePt procedure 1-195
scaling t::ictors 1-218
sec m-22
sec interrupts 11-198
SCCRd global variable 11-199; III-25
SCCWr global variable 11-199; III-25
scrap
between applications 1-453
in TextEdit 1-373, 388
scrap file 1-453
Scrap Manager 1-12, 451
routines 1-457
ScrapCount global variable 1-457
ScrapHandle global variable 1-457
ScrapName global variable 1-457
ScrapSize global variable 1-457
ScrapState global variable 1-457
ScrapStuff data type 1-457
Scratch8 global variable 1-85
Scratch20 global variable 1-85
ScrDmpEnb global variable 1-258
screen buffer III-18, 19
screenBits global variable 1-145, 163
ScreenRes procedure 1-473
Ill-276
ScrHRes global variable 1-473
ScrnBase global variable 11-19, 21
scroll bar 1-47, 312
updating 1-291
ScrollRect procedure 1-187
ScrVRes global variable 1-473
SdVolume global variable 11-232
Secs2Date procedure 11-380
sector 11-211
SectRect function 1-175
SectRgn procedure 1-184
segment II-55
Segment Loader 1-12; II-53
routines ll-57
selection range 1-375
SelectWindow procedure 1-284
SeIIText procedure 1-422
SendBehind procedure 1-286
SendRequest function 11-316
SendResponse function 11-317
sequence number of a datagram 11-266
SerClrBrk function 11-253
SerGetBuf function II-253
SerHShake function 11-251
serial communication II-245
hardware III-22
Serial Communications Controller ITI-22
serial data 11-245
Serial Drivers 1-13; 11-243
advanced Control calls 11-254
Device Manager calls II-248
routines 11-249
SerReset function 11-250
SerSetBrk function 11-252
SerSetBuf function 11-251
SerShk data type 11-252
SerStaRec data type 11-253
SerStatus function 11-253
SetAppBase procedure 11-28
SetApplBase procedure 11-28
SetApplLimit procedure 11-30
SetClikLoop procedure J-390
SetCli p procedure 1-166
SetCRefCon procedure 1-327
SetCTitle procedure I-321
SetCtlAction procedure 1-328
SetCtlMax procedure 1-327
SetCtlMin procedure 1-326
SetCtlValue procedure 1-326
SetCursor procedure 1-167
SetDAFont procedure I-412
SetDateTime function 11-379

<!-- source-page: 284 -->
## Page 284

SetDitem procedure 1-421
SetEmptyRgn procedure 1-183
SetEOF function
high-level II-93
low-level 11-112
SetEventMask procedure 11-70
SetFilelnfo function
high-level II-95
low-level II-116
SetFilLock function
high-level II-95
low-level 11-116
SetFilType function 11-117
SetFinfo function 11-95
SetFLock function 11-95
SetFontLock procedure 1-223
SetFPos function
high-level II-93
low-level II-111
SetGrowZone procedure 11-42
SetHandleSize procedure II-34
Setltem procedure 1-357
Setltemlcon procedure 1-359
SetltemMark procedure 1-359
SetltemStyle procedure 1-360
SetlText procedure 1-422
Setltmlcon procedure 1-359
SetitmMark procedure 1-359
SetltmStyle procedure 1-360
SetMaxCtl procedure 1-327
SetMenuBar procedure I-355
SetMenuFlash procedure 1-361
SetMFlash procedure I-361
SetMinCtl procedure I-326
SetOrigin procedure l-166
SetPBits procedure 1-165
SetPenState procedure 1-169
SetPort procedure 1-165
SetPortBits procedure I-165
SetPt procedure I-193
SetPtrSize procedure II-37
SetRecRgn procedure I-183
SetRect procedure 1-174
SetRectRgn procedure 1-183
SetResAttrs procedure 1-122
SetResFileAttrs procedure 1-127
SetReslnfo procedure I-122
SetResLoad procedure 1-118
SetResPurge procedure 1-126
SetSoundVol procedure 11-233
SetStdProcs procedure 1-198
SetString procedure I-468
SetTagBuffer function II-214
SetTime procedure 11-380
SetTrapAddress procedure II-384
SetUpA5 procedure 11-386
SetVol function
high-level II-89
low-level 11-105
SetWindowPic procedure 1-293
SetWordBreak procedure 1-390
SetWRefCon procedure 1-293
SetWTitle procedure I-284
SetZone procedure 11-31
SEvtEnb global variable 1-443
SFGetFile procedure 1-523
SFPGetFile procedure 1-526
SFPPutFile procedure I-523
SFPutFile procedure 1-519
SFReply data type I-519
SFSaveDisk global variable 1-519
SFTypeList data type 1-523
ShieldCursor procedure 1-474
ShowControl procedure 1-322
ShowCursor procedure I-168
ShowHide procedure I-285
ShowPen procedure I-168
ShowWindow procedure I-285
signature III-9
SignedByte data type 1-78
size
of parameters 1-90
of variables 1-85
size box I-287 See also grow region
size correction 11-24
Size data type 11-18
SizeControl procedure 1-326
SizeResource function 1-121
SizeRsrc function 1-121
SizeWindow procedure 1-290
SlopeFromAngle function 1-475
socket 11-265
socket client II-265
socket listener 11-265
writing your own JI-324, 329
socket number II-265
socket table 11-265
software overrun error II-246
sound buffer II-233; III-18, 21
Sound Driver 1-13; II-221
hardware II-233
routines 11-231
sound generator 11-223; III-20
sound procedure 1-409, 411, 425
Index
lll-277

<!-- source-page: 285 -->
## Page 285

Inside Macintosh
SoundBase global variable Ill-21
SoundDone function 11-232
SoundLevel global variable II-234
SoundPtr global variable II-227
source transfer mode 1-157
space state II-246
SpaceExtra procedure 1-172
SP Alarm global variable See parameter RAM
SPATalkA global variable See parameter
RAM
SPATalkB global variable See parameter
RAM
SPClikCaret global variable See parameter
RAM
SPConfig global variable II-305
speaker volume 11-232, 371
SPFont global variable See parameter RAM
SPKbd global variable See parameter RAM
split bar 1-49
SPMisc2 global variable See parameter RAM
spool printing 11-151, 153
SPortSel data type II-249
SPPortA global variable See parameter RAM
SPPortB global variable See parameter RAM
SPPrint global variable See parameter RAM
SPYalid global variable See parameter RAM
SPVolCtl global variable See parameter RAM
square-wave synthesizer II-223, 225
stack 1-73; 11-17
stack-based routines 1-90
stack frame 1-96; 11-17
StageList data type 1-424
stages of an alert 1-409
Standard File Package 1-12, 515
routines 1-519
start bit II-245
StartSound procedure II-231
Stash function 11-195
Status function
high-level 11-179
low-level 11-186
status information 11-176
status routine of a driver 11-187, 194
StdArc procedure 1-199
StdBits procedure 1-199
StdComment procedure 1-199
StdGetPic procedure 1-200
StdLine procedure 1-198
StdOval procedure I-199
StdPoly procedure 1-199
StdPutPic procedure 1-200
StdRect procedure 1-198
///-278
StdRgn procedure 1-199
StdRRect procedure 1-198
StdText procedure 1-198
StdTxMeas function 1-199
StillDown function 1-259
stop bit 11-245
StopAlert function 1-419
StopSound procedure 11-232
Str32 data type 11-298
Str255 data type 1-78
string comparison 1-501, 506; 11-376
string list I-468
resource format 1-476
string manipulation 1-468
StringHandle data type 1-78
StringPtr data type I-78
StringToNum procedure I-490
StringWidth function 1-173
structure region ofa window 1-271
StuffHex procedure 1-195
style See character style
Style data type 1-152
style dialog II-149
Style menu 1-61
Styleltem data type 1-152
SubPt procedure 1-193
SWSynthPtr data type 11-225
SWSynthRec data type II-225
synchronous execution
AppleTalk Manager 11-273
Device Manager II-180
File Manager 11-97
synthesizer buffer 11-225
SysBeep procedure ll-385
SysEdit function 1-441
SysError procedure 11-362
SysEvtMask global variable II-70
SysMap global variable 1-114
SysMapHndl global variable 1-114
SysParam global variable 11-369
SysParmType data type II-370
SysPPtr data type 11-370
SysResName global variable 1-114
system error alert 11-357
system error alert table 11-357, 359
System Error Handler 1-13; 11-18, 355
routine II-362
system error ID II-357
system event mask 1-254; II-70
system font 1-219
system font size 1-219
system heap 1-74; II-9

<!-- source-page: 286 -->
## Page 286

system resource 1-103
system resource file 1-103
system startup information 11-120
system traps III-215
system window 1-270, 438
SystemClick procedure 1-441
SystemEdit function 1-441
SystemEvent function 1-442
SystemMenu procedure 1-443
SystemTask procedure 1-442, 444; 11-189
SystemZone function 11-32
SysZone global variable II-19, 21, 32
T
tag byte 11-24
TEActivate procedure 1-385
TECalText procedure 1-390
TEC!ick procedure 1-384
TECopy procedure 1-386
TECut procedure 1-385
TEDeactivate procedure 1-385
TEDelete procedure 1-387
TEDispose procedure 1-383
TEDoText global variable 1-391
TEFromScrap function 1-389
TEGetScrapLen function 1-389
TEGetText function 1-384
TEHandle data type 1-374
TEldle procedure 1-384
TElnit procedure 1-383
TElnsert procedure 1-387
TEKey procedure 1-385
TENew function 1-383
TEPaste procedure 1-386
TEPtr data type 1-374
TERec data type 1-377
TERecal global variable 1-391
TEScrapHandle function 1-389
TEScroll procedure 1-388
TEScrpHandle global variable 1-389
TEScrpLength global variable 1-389
TESetJust procedure 1-387
TESetScrapLen procedure 1-390
TESetSelect procedure 1-385
TESetText procedure 1-383
TestControl function 1-325
TEToScrap function 1-389
TEUpdate procedure 1-387
text characteristics 1-151
text in a dialog/alert 1-404, 408
text streaming 11-165
TextBox procedure 1-388
TextEdit 1-12, 371
routines 1-383
scrap 1-373, 388
TextFace procedure I-171
TextFont procedure 1-171
TextMode procedure 1-171
TextSize procedure I-171
TextWidth function 1-173
TheMenu global variable 1-357
thePort global variable 1-162, 165
TheZone global variable 11-31
thousands separator I-497
THPrint data type II-149
thumb 1-312
THz data type 11-22
tick I-246
TickCount function 1-260
Ticks global variable I-260; II-198
Time global variable 11-198, 369, 378
time operations 11-377
ToExtFS global variable II-128
toggled command 1-53, 357
Tone data type II-225
Tones data type 11-225
Toolbox 1-9
Toolbox Event Manager 1-11, 241
routines 1-257
Toolbox Utilities 1-12, 465
routines 1-467
ToolScratch global variable I-85
TopMapHndl global variable 1-115
TopMem function II-44
TPPrint data type 11-149
TPPrPort data type 11-147
TPrlnfo data type 11-150
TPrint data type II-149
TPrJob data type 11-151
TPrPort data type Il-147
TPrStatus data type 11-161
TPrStl data type II-152
TPrXInfo data type II-152
track on a disk 11-211
TrackControl function 1-323
TrackGoAway function 1-288
transaction 11-266
transaction ID 11-266
transaction release II-270
transaction request II-266
transaction response 11-266
Index
III-279

<!-- source-page: 287 -->
## Page 287

Inside Macintosh
Transcendental Functions Package 1-13;
11-403, 407
transfer mode 1-156
trap dispatch table 1-87
routines 11-383
trap dispatcher I-89
trap macro I-88, 90
list III-215
trap number I-89, 384
trap word 1-88
TRel See transaction release
TReq See transaction request
TResp See transaction response
trigonometric functions II-407
type coercion I-79
type size See font size
u
Undo command 1-59
unimplemented instruction 1-88
UnionRect procedure I-175
UnionRgn procedure 1-184
UniqueID function 1-121
unit number 11-191
unit table 11-191
UnloadNBP function 11-324
UnloadScrap function I-458
UnloadSeg procedure 11-59
unlocked block I-76; 11-10
unlocking a block I-76; 11-41
UnlodeScrap function I-458
unmounted volume II-79
UnmountVol function
high-level 11-90
low-level II-106
UnpackBits procedure 1-470
unpurgeable block 1-76; 11-10, 42
update event 1-244, 278
event message 1-252
update region of a window 1-272
maintenance I-291
UpdateResFile procedure 1-125
UprString procedure 11-377
use type 11-305
user bytes 11-266
user interface guidelines 1-23
User Interface Toolbox 1-9
UseResFile procedure I-117
userltem in a dialog 1-404, 405
installing I-421
///-280
UTableBase global variable II-192
Utilities, Operating System 1-13; 11-307
routines 11-374
Utilities, Toolbox 1-12, 465
routines 1-467
v
validity status 11-370
ValidRect procedure 1-292
ValidRgn procedure I-292
variation code
control I-328
window 1-298
VBL interrupt See vertical blanking interrupt
VBL task II-350
VBLQueue global variable II-352
VBLTask data type 11-350
VCB data type 11-125
VCBQHdr global variable Il-126
vector Il-196
vector table II-196
Versatile Interface Adapter III-39
version data III-10
version number of a file 11-81
vertical blanking interrupt 11-349; 111-18
vertical blanking interval III-18
vertical retrace interrupt I-13; II-349
Vertical Retrace Manager I-13; II-347
routines 11-351
vertical retrace queue II-350, 352
VHSelectdata type I-139
VIA III-39
VIA global variable I-198; III-39
VIA interrupts II-197; III-38, 41
videointerface III-18
view rectangle I-374
Vlnstall function 11-351
visible
control 1-316
window I-274
visRgn of a grafPort 1-149
volume (on a disk) 11-79
volume (speaker) 11-232, 371
volume allocation block map II-122
volume attributes 11-121
volume buffer 11-79
volume control block 11-125
volume-control-block queue II-125
volume index 11-102
volume information II-121

<!-- source-page: 288 -->
## Page 288

volume name II-79
volume reference number 11-79
VRemove function 11-351
w
WaitMouseUp function 1-259
Wave data type 11-227
waveform 11-223
waveform description II-224
wavelength 11-223
WavePtr data type II-227
white global variable 1-162
window 1-44, 269
closing 1-45, 283
defining your own 1-297
moving 1-46, 289
opening 1-45, 282
resource format 1-302
sizing 1-47, 289
splitting 1-49
window class
1-274, 276
window definition function 1-272, 298
window definition ID 1-273, 298
window frame 1-271
window list 1-274, 277
Window Manager 1-11, 267
routines 1-281
Window Manager port 1-271, 282
window pointer 1-275
window record 1-274, 276
window template 1-274
resource format 1-302
WindowList global variable 1-255, 277
WindowPeek data type I-275
WindowPtr data type 1-275
Window Record data type 1-276
WMgrPort global variable I-282
word 1-42
in TextEdit 1-373
word break routine 1-380
word wraparound 1-373
write data structure II-306
Write function, high-level
Device Manager 11-179
File Manager 11-92
Write function, low-level
Device Manager 11-185
File Manager 11-110
WriteDDP function II-312
WriteLAP function 11-307
WriteParam function 11-382
WriteResource procedure 1-125
x
XorRgn procedure 1-185
y
z
ZeroScrap function 1-458
zone
AppleTalk Manager II-266
Memory Manager See heap zone
Zone data type II-22
zone header 11-22
zone pointer 11-22
zone record II-22
zone trailer 11-22
Index
1//-281

<!-- source-page: 289 -->
## Page 289

Inside Macintosh
Welcome to the world of programming for the Macintosh®. No other personal computer has been as
eJ;lthusiastically received by the programming community, as the large-and growing-body of Macintosh
software attests. Inside Macintosh provides the guidelines and technical information that you'll need to
develop Macintosh programs, but many other resources can help speed and simplify your software
development efforts.
Development Languages
You won't have to look far to find a development language that suits your specific requirements. A
growing family of Macintosh languages will serve your development needs whether your expertise is in
Pascal, C, Assembler, FORTH, FORTRAN, COBOL, BASIC, Lisp, Modula-2, or one of many others.
And the information in Inside Macintosh can be applied to any of the Macintosh languages.
The Certified Developer Program
If your primary business is developing software products for commercial markets, we strongly suggest that
you investigate the Apple Certified Developer Program. This program helps developers produce and bring
Macintosh products to market by providing them with support programs, services, and information.
Among them are
•Technical Support: Apple's Developer Technical Support Group offers fast answers by way of
AppleLink® or MCI electronic mail.
• Macintosh Technical Notes: This is a bimonthly package of supplemental technical information.
• AppleLink: Through this electronic service, you can get answers to your technical questions and
current information on Apple and third-party products and programs.
• Certified Developer Mailings: These monthly mailings keep you informed about Apple's
products, development tools, and technical and company directions.
• The Information Exchange: This information, available in printed and HyperCard® stack form,
lists company-sponsored programs and services available to you and your company.
• Outside Apple: This monthly newsletter informs you of developer-oriented Apple groups, programs,
and events.
You must meet certain criteria to get Certified Developer status. You can get an information package and
application by writing to
APDA
Developer Programs
Apple Computer, Inc.
20525 Mariani A venue, MIS 51-W
Cupertino, CA 95014
The Apple Programmer's and Developer's Association, APDA™, provides technical documentation and
products for all programmers and developers who work on Apple equipment. It provides material that is
unavailable elsewhere (including preliminary documentation of new Apple products). APDA also sells
compilers and other tools from both Apple and third-party sources. For information on joining, write to
Technical Notes
APDA
290 SW 43rd Street
Renton, WA 98055
(206) 251-6548
Published bimonthly by Developer Technical Support, these notes answer frequently asked questions
through examples and sample code and provide updates, additions, and corrections to the Inside Macintosh
books. They are available through the Certified Developer Program, APDA, and major electronic
information services.

<!-- source-page: 290 -->
## Page 290

Apple® Inside Macintosh
> $19-95 FPT
USA
The Official
Publication from
Apple Computer, Inc.
Volume ill
\X-Titcen by the people at Apple Computer, Inside Macintosh is the definitive source of information
for programmers writing application programs, desk accessories, device drivers, and otl1er
software for any of the computers in the Apple Macintosh® family. It includes:
• Guidelines for designing a user interface that conforms to the Macintosh standard.
• Descriptions of more tl1an 1,200 ROM- and disk-based routines.
• A description of the Macintosh hardware.
Inside Macintosh is your guide to creating software for the Macintosh, whatever programming
language you use. It describes tl1e Pascal interfaces to the routines and, wherever applicable, gives
special information for programming in assembly language. (If you're using a high-level language
other than Pascal, your development system documentation should teU you how to apply the
information in Inside Macintosh.) A typical chapter describes a related set of routines, such as the
Window Manager, and provides:
• Key concepts and backgrow1d information.
• Hints on which routines you need to learn about and how they fit into your program.
• A detailed description of each routine.
Inside Macintosh consists of sLx volumes. This volume, Volume III, contains:
• A discussion of your program's interface with the Macintosh Finder.'"
• A description of the Macintosh 128K and 512K computers.
• Summaries of all the Managers and otl1er software described in volumes I, II, and Ill.
Volume I contains important introductory material and describes the QuickDraw graphics package
and important Managers such as the Resource, Font, and Menu Managers. Volume II complements
Volume I in describing the Managers that perform such basic routines as file and device 110,
memory management, and interrupt handling. Volume IV discusses the changes introduced by tl1e
Macintosh 512K Enhanced and Macintosh Plus computers, including the Hierarchical File System
and tl1e SCSI port. Volume V discusses tl1e changes inu·oduced by the Macintosh SE and Macintosh II
computers, including color, NuBus'" slots, and the Apple Desktop Bus:· Inside Macintosh X-Ref
provides a single index to Inside Macintosh and otl1er Macintosh tedmical books.
About the cover: This design represent5 a new look for the original edition of Inside Macintosh,
Volume ffl, and tl1e other books in the Apple Technical Library. The contents have not been
changed.
Printed in U.SA.
Apple Computer, Inc.
20525 Mariani Avenue
Cupertino, CA 95014
( 408) 996-1010
1lX 171-576
Addison-Wesley Publishing Company, Inc.
51995
9 780201 177336
ISBN 0-201-17733-1
