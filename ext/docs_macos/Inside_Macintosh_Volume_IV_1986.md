<!-- source-pdf: resources/platform_macos/docs/Inside_Macintosh_Volume_IV_1986.pdf -->
<!-- source-pages: 334 -->

<!-- source-page: 1 -->
## Page 1

Apple® Inside Macintosh Volume IV

Supplements Inside Macintosh, volumes I through III, with information about the Macintosh® Plus and Macintosh 512K Enhanced computers

<!-- source-page: 2 -->
## Page 2

Inside Macintosh®
Volume IV
... ....
Addison-Wesley Publishing Company, Inc.
Reading, Massachusetts Menlo Park, California New York Don Mills, Ontario
Wokingham, England Amsterdam Bonn Sydney Singapore Tokyo Madrid San Juan

<!-- source-page: 3 -->
## Page 3

S APPLE COMPUTER, INC.
Copyright© 1986 by Apple Computer, Inc.
All rights reserved. No part of this publication may be reproduced, stored in a retrieval system, or
transmitted, in any fonn or by any means, electronic, mechanical, photocopying, recording, or
otherwise, without prior written pennission of Apple Computer, Inc. Printed in the United States
of America.
Apple, the Apple logo, AppleTalk, HyperCard, LaserWriter, Lisa, Macintosh, Mac Works, and
SANE are registered trademarks of Apple Computer, Inc.
APDA and Finder are trademarks of Apple Computer, Inc.
MacDraw, MacPaint, and Mac Write are registered trademarks of Claris Corporation.
Simultaneously published in the United States and Canada.
This book was produced using the Apple Macintosh computer and the LaserWriter printer.
ISBN 0-201-05409-4
FGHU-MU-898
Sixth Printing, August 1988

<!-- source-page: 4 -->
## Page 4

Inside Macintosh
Volume IV

<!-- source-page: 5 -->
## Page 5

WARRANTY INFORMATION
ALL IMPLIED WARRANTIES ON THIS MANUAL, INCLUDING IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE, ARE LIMITED IN DURATION TO NINETY (90) DAYS FROM THE
DATE OF THE ORIGINAL RETAIL PURCHASE OF THIS PRODUCT.
Even though Apple has reviewed this manual, APPLE MAKES NO WARRANTY OR
REPRESENTATION, EITHER EXPRESS OR IMPLIED, WITH RESPECT TO
THIS MANUAL, ITS QUALITY, ACCURACY, MERCHANTABILITY, OR
FITNESS FOR A PARTICULAR PURPOSE. AS A RESULT, THIS MANUAL IS
SOLD "AS IS," AND YOU, THE PURCHASER, ARE ASSUMING THE ENTIRE
RISK AS TO ITS QUALITY AND ACCURACY.
IN NO EVENT WILL APPLE BE LIABLE FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES RESULTING FROM ANY
DEFECT OR INACCURACY IN THIS MANUAL, even if advised of the possibility of
such damages.
THE WARRANTY AND REMEDIES SET FORTH ABOVE ARE EXCLUSIVE AND
IN LIEU OF ALL OTHERS, ORAL OR WRITTEN, EXPRESS OR IMPLIED. No
Apple dealer, agent, or employee is authorized to make any modification, extension, or addition to
this warranty.
Some states do no allow the exclusion or limitation of implied warranties or liability for incidental or
consequential damages, so the above limitation or exclusion may not apply to you. This warranty
gives you specific legal rights, and you may also have other rights which vary from state to state.

<!-- source-page: 6 -->
## Page 6

Contents

ix Preface
xi About Inside Macintosh Volume IV

1 The Macintosh User Interface Guidelines
3 About This Chapter
3 Arrow Keys
7 Reserved Command Key Combinations
7 Window Zooming
10 Standard Close Dialog

2 Using Assembly Language
13 The Trap Dispatch Table
13 Format of the Trap Words

3 The Resource Manager
15 Resource Manager Routines
17 Resource Types
18 Checking For Errors
18 ROM Resources
21 Summary of the Resource Manager

4 QuickDraw
23 QuickDraw Routines
26 Summary of QuickDraw

5 The Font Manager
29 About the Font Manager
29 Fonts and Their Families
31 Font Manager Routines
33 Communication Between QuickDraw and the Font Manager
34 Font Manager Data Structures
42 Font and Font Family Resources
45 Summary of the Font Manager

6 The Window Manager
50 Window Manager Routines
51 Summary of the Window Manager

7 The Control Manager
53 Control Manager Routines
53 The Control Definition Function
54 Summary of the Control Manager

8 The Menu Manager
55 Menu Manager Routines
56 The Menu Definition Procedure
56 Summary of the Menu Manager

<!-- source-page: 7 -->
## Page 7

Inside Macintosh
57
9 TextEdit
57
TextEdit Routines
58
Default Click Loop Routine
58
Summary of TextEdit
59
10 The Dialog Manager
59
Dialog Manager Routines
60
Summary of the Dialog Manager
61
11 The Scrap Manager
63
12 Toolbox Utilities
63
Toolbox Utility Routines
66
Summary of the Toolbox Utilities
67
13 The Package Manager
68
Summary of the Package Manager
69
14 The Binary-Decimal Conversion Package
71
15 The Standard File Package
73
Using the Standard File Package
7 4
Creating Your Own Dialog Box
76
Summary of the Standard File Package
77
16 The Memory Manager
77
Memory Manager Routines
80
Error Reporting
81
Summary of the Memory Manager
83
17 The Segment Loader
85
18 The Operating System Event Manager
85
Summary of the Operating System Event Manager
87
19 The File Manager
89
About This Chapter
89
About the File Manager
96
Using the File Manager
104
Information Used by the Finder
106
High-Level File Manager Routines
115
Low-Level File Manager Routines
159
Data Organization on Volumes
17 4
Data Structures in Memory
182
Using an External File System
183
Summary of the File Manager
213
20 The Device Manager
215
About the Device Manager
216
The Chooser
222
Summary of the Device Manager
W-vi Contents

<!-- source-page: 8 -->
## Page 8

223
21 The Disk Driver
223
Advanced Control Calls
224
Summary of the Disk Driver
225
22 The Serial Driver
226
Advanced Control Calls
227
Summary of the Serial Driver
229
23 The AppleTalk Manager
231
24 The System Error Handler
233
25 The Operating System Utilities
233
Operating System Utility Routines
236
Summary of the Operating System Utilities
239
26 The Disk Initialization Package
241
Summary of the Disk Initialization Package
243
27 The Finder Interface
243
The Desktop File
245
28 The Macintosh Plus Hardware
245
Overview of the Hardware
247
The Video Interface
247
The Sound Generator
248
TheSCC
250
The Keyboard
250
The Floppy Disk Interface
251
The Real-Time Clock
251
The SCSI Interface
254
Summary
255
29 The System Resource File
256
Initialization Resources
259
30 The List Manager Package
261
About This Chapter
261
About the List Manager Package
262
List Records
266
Cell Selection Algorithm
268
Using the List Manager Package
269
List Manager Package Routines
27 6
Defining Your Own Lists
278
Summary of the List Manager Package
Contents
Contents IV-vii

<!-- source-page: 9 -->
## Page 9

Inside Macintosh
283
31 The SCSI Manager
285
About This Chapter
285
About the SCSI lVJan~ger
286
Using the SCSI Manager
289
SCSI Manager Routines
292
Writing a Driver for an SCSI Block Device
294
Summary of the SCSI Manager
297
32 The Time Manager
299
About This Chapter
299
About the Time Manager
299
Using the Time Manager
300
Time Manager Routines
301
Summary of the Time Manager
303
Appendix A: Routines That May Move or Purge Memory
305
Appendix B: System Traps
309
Appendix C: GJobal Variables
311
Glossary
319
Index
IV-viii Contents

<!-- source-page: 10 -->
## Page 10

PREFACE
x1
About Inside Macintosh Volume N
xi
The Language
xi
Version Numbers
xxn
Compatibility
xxn
Conventions
Preface IV-ix

<!-- source-page: 11 -->
## Page 11

Inside Macintosh
JV-x

<!-- source-page: 12 -->
## Page 12

Preface
ABOUT INSIDE MACINTOSH VOLUME IV
The first three volumes of Inside Macintosh provide information you'll need to write
software for any of the Apple® Macintosh® family. This volume, Volume IV, is a
companion to the first three volumes that gives specific information on writing software to
take advantage of the features of the Macintosh Plus and the Macintosh 512 enhanced. A
familiarity with the material presented in the first three volumes is assumed, since most of
the information presented in Volume N consists of changes and additions to that original
material.
Practically every chapter in the first three volumes has a corresponding chapter in Volume
N that describes new routines, modified data structures, additional error codes, and so on.
Most of these chapters are "delta" documents that present only the new information. In the
case of the File Manager chapter, the changes are so extensive that the chapter has been
completely rewritten. Finally, four additional chapters-"The System Resource File",
"The List Manager", "The SCSI Manager", and "The Time Manager"-introduce entirely
new material.
The Language
The routines you'll need to call are written in assembly language, but (with a few
exceptions) they're also accessible from high-level languages, such as Pascal on the Lisa
·Workshop development system. Inside Macintosh documents the Lisa Pascal interfaces to
the routines and the symbolic names defined for assembly-language programmers using the
Lisa Workshop; if you 're using a different development system, its documentation should
tell you how to apply the information presented here to that system.
Inside Macintosh is intended to serve the needs of both high-level language and assemblylanguage programmers. Every routine is shown in its Pascal form (if it has one), but
assembly-language programmers are told how they can access the routines. Information of
interest only to assembly-language programmers is set apart and labeled so that other
programmers can conveniently skip it.
Familiarity with Lisa Pascal (or a similar high-level language) is recommended for all
readers, since it's used for most examples. Lisa Pascal is described in the documentation
for the Lisa Pascal Workshop.
Version Numbers
This edition of Inside Macintosh Volume IV describes the following versions of the
software:
•version 117 ($75) of the ROM in the Macintosh Plus and Macintosh 512K enhanced
• version 2.0 of the Lisa Pascal interfaces and the assembly-language definitions
About Inside Macintosh Volume IV xi
I

<!-- source-page: 13 -->
## Page 13

Inside Macintosh
Some of the RAM-based software is read from the file named System (usually kept in the
System Folder). This manual describes the software in the System file version 3.2 whose
creation date is June 4, 1986. In certain cases, a feature can be found in earlier versions of
the System file; these cases are noted as they come up.
Compatibility
Version 117 ($75) of the ROM, also known as the 128K ROM, is provided on the
Macintosh 512K enhanced and Macintosh Plus.
Note: A partially upgraded Macintosh 512K is identical to the Macintosh 512K
enhanced, while a completely upgraded Macintosh 512K includes all the features of
the Macintosh Plus.
Version 105 ($69) of the ROM (the version described in the first three volumes of Inside
Macintosh), also known as the 64K ROM, is provided on the Macintosh 128K and 512K.
Most applications written for the 64K ROM run without modification on machines
equipped with the 128K ROM. Applications that use the routines and data structures found
in the 128K ROM, however, may not function on machines equipped with the 64K ROM.
Programmers may wish to determine which version of the ROM is installed in order to take
advantage of the features of the 128K ROM whenever possible. You can do this by
checking the ROM version number returned by the Operating System Utility procedure
Environs; if the version number is greater than or equal to 117 ($7 5), it's safe to use the
routines and data structures described in this volume.
Assembly-language note: A faster way of determining whether the 128K ROM
is present is to examine the global variable Rom85 (a word); it's positive (that is, the
high-order bit is 0) if the 128K ROM is installed.
Conventions
The following notations are used in Volume IV to draw your attention to particular items of
information:
64K ROM note: A note, found only in chapter 19 of this volume, that points out
some difference between the 64K ROM and 128K ROM.
Note: A note that may be interesting or useful.
Warning: A point you need to be cautious about.
Assembly-language note: A note of interest to assembly-language programmers
only.
xii About Inside Macintosh Volume IV

<!-- source-page: 14 -->
## Page 14

Prefa,ce
[Not in ROM]
Routines marked with this notation are not part of the Macintosh ROM. Depending
on how the interfaces have been set up on the development system you 're using,
these routines may or may not be available. They 're available to users of Lisa Pascal;
other users should check the documentation for their development system for more
information. (For related information of interest to assembly-language programmers,
see chapter 4 of Volume I and chapter 2 of this volume.)
About Inside Macintosh Volume W xiii
I

<!-- source-page: 15 -->
## Page 15

1 THE MACINTOSH USER INTERFACE GUIDELINES
3
About This Chapter
3
Arrow Keys
3
Appropriate Uses for the Arrow Keys
4
Moving the Insertion Point With Arrow Keys
4
Moving the Insertion Point in Empty Documents
4
Modifier Keys With Arrow Keys
5
Making a Selection With Arrow Keys
6
Extending or Shrinking a Selection
6
Collapsing a Selection
7
Reserved Command Key Combinations
7
Window Zooming
10
Effects of Dragging and Sizing
10
Standard Cose Dialog
11
Close Box Specifications
Contents W-1

<!-- source-page: 16 -->
## Page 16

The Macintosh User Interface Guidelines
ABOUT THIS CHAPTER
This chapter describes the following new features of the Macintosh user interface:
• the Macintosh Plus arrow keys
• an updated list of reserved Command key combinations
• the new window zooming feature
• a new standard Close dialog box
ARROW KEYS
The Macintosh Plus keyboard includes four arrow keys: Up Arrow, Down Arrow, Left
Arrow, and Right Arrow.
Figure 1. Macintosh Plus Arrow Keys
Appropriate Uses for the Arrow Keys
The arrow keys do not replace the mouse. They can be used in addition to the mouse as a
shortcut for moving the insertion point and (under some circumstances) for making
selections. The following rules are the minimum guidelines for the use of arrow keys,
leaving application programmers relatively free to expand on them where things are left
undefined. Extensions necessary for a particular application should be done in the spirit of
the Macintosh user interface.
It's up to you to decide whether it's worth the effort to create arrow key shortcuts for
mouse functions. Many users find that remembering a key combination on the order of
Command-Shift-Left Arrow is more trouble than it's worth and would rather use a mouse
anyway~ In other situ~tions, it's more convenient to use the keyboard. Some people have
difficqlty using a mouse and appreciate ~ing able to use the keyboard instead.
f·,·
Arrow Keys IV-3

<!-- source-page: 17 -->
## Page 17

Inside Macintosh
You should make use of the arrow keys only where it's appropriate to the application.
Applications that deal with text or arrays (word processors, spreadsheets, and data bases,
for example) have an insertion point. This insertion point can always be moved by the
mouse and, with the new keyboard, with the arrow keys as well.
As a general rule, arrow keys are used to move the insertion point and to expand or shrink
selections. Arrow keys are never used to duplicate the function of the scroll bars or to
move the pointer. In a graphics application, the arrow keys should not be used to move a
selected object.
Moving the Insertion Point With Arrow Keys
The Left Arrow and Right Arrow keys move the insertion point one character left and right,
respectively.
Up Arrow and Down Arrow move the insertion point up and down one line, respectively.
The horizontal screen position should be maintained in terms of screen pixels but not
necessarily in terms of characters, because the insertion point moves to the nearest character
boundary on the new line. (Character boundaries seldom line up vertically when
proportional fonts are used.) During successive movements up or down, you should keep
track of the original horizontal screen position; otherwise, accumulated round-off errors
might cause the insertion point to move a significant distance from the original horizontal
position as it moves from line to line.
Moving the Insertion Point in Empty Documents
Various text-editing programs treat empty documents in different ways. Some assume that
an empty document contains no characters, in which case clicking at the bottom of a blank
screen causes the insertion point to appear at the top. In this situation, Down Arrow cannot
move the insertion point into the blank space (because there are no characters there).
Other applications treat an empty document as a page of space characters, in which case
clicking at the bottom of a blank screen puts the insertion point where the user clicked and
lets the user type characters there, overwriting the spaces. Down Arrow moves the
insertion point straight down through the spaces.
Whichever paradigm you choose for your application, be consistent.
Modifier Keys Wdh Arrow Keys
Holding down the Command key while pressing an arrow key should move the insertion
point to the appropriate edge of the window. If the insertion point is already at the edge of
the window, the document should be scrolled one windowful in the appropriate direction
and the insertion point should move to the same edge of the new windowfµl.
Command-Up Arrow moves to the top of the window, Command-Down Arrow to the
bottom, Command-Left Arrow to the left edge, and Command-Right Arrow to the right
edge.
IV-4 Arrow Keys

<!-- source-page: 18 -->
## Page 18

The Macintosh User Interface Guidelines
The Option key is reserved as a "semantic modifier" key. The application determines what
the semantic units are. For example, in a word processor, where the basic semantic unit is
the character and the next larger unit is the word, Option-Left Arrow and Option-Right
Arrow might move the insertion point to the beginning and end, respectively, of a word.
(Movement of the insertion point by word boundaries should use the same definition of
"word" that the application uses for double clicking.) The next larger semantic unit could
be defined as the sentence, in which case Option-Left Arrow and Option-Right Arrow
would move the insertion point to the beginning or end of a sentence. In a programming
language editor, where the basic semantic unit is the token and the next larger one might be
the line, Option-Left Arrow and Option-Right Arrow might move the insertion point left
and right to the beginning and end of the line, respectively.
In an application (such as a spreadsheet) that represents itself as an array, the basic
semantic unit would be the cell. Option-Left Arrow would designate the cell to the left of
the currently active cell as the new active cell, and so on. Using modifier keys with arrow
keys doesn't do anything to the data; Option-Left Arrow just moves the selection to the
next cell to the left.
Though the use of multiple modifier key combinations (such as Command-Option-Left
Arrow) is discouraged, it's fine to use the Shift key with any one of the other modifier keys
for making a selection (see "Making a Selection With Arrow Keys" below). Keep in mind
that if multiple keys must be pressed simultaneously, they should be fairly close
together--otherwise many people won't be able to use that combination.
Making a Selection With Arrow Keys
To use arrow keys to make a selection, the user holds down Shift while pressing an arrow
key. Application programs that depend (as TextEdit does) on the numeric keypad should
not use these Shift-arrow key combinations because the ASCII codes for the four
Shift-arrow key combinations are the same as those for the keypad's+,*,/, and= keys.
If the use of Shift-arrow for making selections is more important to your application than
the numeric keypad, the following paragraphs describe how it should work.
After a Shift-arrow key combination has been pressed, the insertion point moves and the
range over which it moves becomes selected. If both the Shift key and another modifier
key are held down, the insertion point moves (as defined for the particular modifier key)
and the range over which the insertion point moves becomes selected For example,
Shift-Left Arrow selects the character to the left of the insertion point, Command-Shift-
Left Arrow selects from the insertion point to the left edge of the window, and Option-
Shift-Left Arrow selects the whole word that contains the character to the left of the
insertion point (just like double clicking on a word).
A selection made using the mouse is no different from one made using arrow keys. A
selection started with the mouse can be extended using Shift and Left Arrow or Right
Arrow.
The two ends of a selected range have different characteristics and different names. The
place where the insertion point was when selection was started is called the anchor point.
The place to which the insertion point moves to complete the selection is called the active
end. Once selection begins, the anchor point cannot be moved except by beginning a new
selection. To extend or shrink a selection, the user moves the active end as specified here.
As the active end moves, it can cross over the anchor point.
Arrow Keys IV-5

<!-- source-page: 19 -->
## Page 19

Inside Macintosh
In a text application, pressing Shift and either Left Arrow or Right Arrow selects a single
character. Assuming that Left Arrow key was used, the anchor point of the selection is on
the right side of the selection, the active end on the left. Each subsequent Shift-Left Arrow
adds another character to the left side of the selection. A Shift-Right Arrow at this point
shrinks the selection. Figure 2 summarizes these actions.
1. Insertion point is within a word:
2. Shift-.._ is pressed:
3. another Shift-.._:
4. Shift-.. :
5. three more times Shift-.. :
weird
WZrd
&rd
WZrd
wotm
Figure 2. Selecting With Shift-Arrow Keys
In a text application, pressing Option-Shift and either Left Arrow or Right Arrow selects
the entire word containing the character to the left of the insertion point. Assuming
Left Arrow was used, the anchor point is at the right end of the word, the active end at the
left. Each subsequent Option-Shift-Left Arrow adds another word to the left end of the
selection, as shown in Figure 3.
1. Insertion point is within a word:
another wtjrd
2. Option-Shift-._ is pressed:
3. another Option-Shift-._:
another word
Figure 3. Selecting With Option-Shift-Arrow Keys
Pressing Command-Shift-Left Arrow selects the area from the insertion point to the left
edge of the window. The anchor point is at the right end of the selection, the active end is
at the left. Each subsequent Command-Shift-Left Arrow moves the document one
windowful left and extends the selection to the left edge of the new window.
Extending or Shrinking a Selection
To use arrow keys to extend or shrink a selection, the user holds down the Shift key (plus
any defined modifiers) while pressing an arrow key. The arrow key moves the insertion
point at the active end of the selection.
Collapsing a Selection
When a block of text is selected, pressing either Left Arrow or Right Arrow deselects the
range. If Left Arrow is pressed, the insertion point is left at the beginning of the previous
selection; if Right Arrow, at the end of the previous selection.
IV-6 Arrow Keys

<!-- source-page: 20 -->
## Page 20

The Macintosh User Interface Guidelines
RESERVED COMMAND KEY COMBINATIONS
There are several menu items, particularly in the File and Edit menus, that commonly have
keyboard equivalents. For consistency, several of those keyboard equivalents should be
used only for the commands listed below and should never be used for any other purpose.
Desk accessories, which are accessible from all applications, assume that these Commandkey combinations have the meanings listed here.
File Menu
Command-N (New)
Command-0 (Open)
Command-S (Save)
Command-Q (Quit)
Edit Menu
Command-Z (Undo)
Command-X (Cut)
Command-C (Copy)
Command-V (Paste)
The keyboard equivalents in the Style menu (listed below) are less strictly reserved.
Applications that have Style menus shouldn't use these keyboard equivalents for any other
purpose, but applications that have no Style menus can use them for other purposes if
needed. Remember that you risk confusing users if a given key combination means
different things in different applications.
Style Menu
Command-P (Plain)
Command-B (Bold)
Command-I (Italic)
Command-U (Underline)
WINDOW ZOOMING
The more open documents on a desktop, the more difficult it is for the user to locate, select,
and resize the one to be worked on. The 128K ROM includes a feature, known as window
zooming, that allows users-with a single mouse click-to toggle the active window
between its standard size and location and a predefined size and location.
The initial size and placement of a window is known as its standard state. The application
program can supply values for the standard state; otherwise the full screen (minus a few
border pixels) is assumed (see Figure 4). The standard state should be the most useful size
and location for normal operations within the program-usually it's the full screen.
Window Zooming IV-7

<!-- source-page: 21 -->
## Page 21

Inside Macintosh
File
Edit
Search
Format Font
Style
Document
Zoom-Window box
File Edit
Search
Format Font
Style
Document
Figure 4. Window in Standard State
Size box
""{);'
~
The user cannot change the standard state, but the application can change it within context
For example, a word processor might define a size that's wide enough to display a
document whose width is as specified in Page Setup. If the user invokes Page Setup to
specify a wider or narrower document, the application might then change the standard state
to reflect that change.
Your application can also supply initial values for the second window state, known as the
user state. If you don't supply initial values, the user state is identical to the standard state
until the user moves or resizes the window. When the standard state and user state are
different (Figure 5 shows a hypothetical user state), clicking in the zoom-window box acts
as a toggle between the two states.
IV-8 Window Zooming

<!-- source-page: 22 -->
## Page 22

The Macintosh User Interface Guidelines
Figure 5. Window in User State
Application developers are encouraged to take advantage of the zooµi-window feature;
details on using this feature are provided in chapter 6 of this volume. You should not
change the shape of the zoom-window box or change the interpretation of clicking on the
the zoom-window box (shown in Figure 6). You should add no other elements to the title
bar. Except in the zoom-window box and in the close box, clicking within the title bar
should have no effect.
•••••••••••
•
• •
•
• •
•
• •
•
• •
•
• •
••••••• •
•
•
•
•
•
•
•••••••••••
Before being
clicked
• ••••••••••
• • •
• ••••
• ••••
•
•
•••• • •••
•
•
•••••
• • • • •
• • •
• ••••••••••
Being clicked
Figure 6. Zoom-Window Box Details
Window Zooming W-9

<!-- source-page: 23 -->
## Page 23

Inside Macintosh
Effects of Dragging and Sizing
Explicit dragging or resizing of the window is handled in the normal way (see "Changing
the Size of a Window" in chapter 2 of Volume I), regardless of the presence or absence of
the zoom-window feature. The effect of dragging or resizing depends on the state of the
window and the degree of movement. A change, either in position or size, of seven pixels
or less is insignificant. A change of more than seven pixels is a "significant change".
If dragging or resizing occur when the window is in the standard state, a small change in
the size or location of the window does not change the state, nor does it change the
application-defined values for the size and location of the standard state. It does, of course,
change the size or location of the window. A significant change in the size or location of
the window switches the window to the user state and sets the values for the size and
location of that state to those of the window.
If dragging or resizing occur when the window is in the user state, a cp.ange in size or
location that leaves the window within seven pixels of the size and location specified as the
standard state changes the state to the s~dard state, leaving the size and location of the
user state unchanged. Any other change in size or location in the user state leaves the
window in the user state and sets the values for the size and location of that state to those of
the window.
STANOARD CLOSE DIALOG
When a user chooses Close or Quit from the File menu, and the active document has been
changed, the Close dialog box appears, asking "Save changes before closing?" A great
deal of work can be lost if a user mistakenly clicks the "No" button instead of "Cancel".
This is especially important to Switcher users, who often move from one application to
another and become less aware of subtle differences between applications. To avoid
confusion, all applications should use the same standard Close dialog. As shown in Figure
7, dialogs can have multiple lines of text.
Saue changes to "Memo to
Elizabeth"?
€ Yes »
11:,'JJI
(
No~'~' )
( Cancel )
Figure 7. A Standard Close Dialog
IV-10 Standard Close Dialog

<!-- source-page: 24 -->
## Page 24

The Macintosh User Interface Guidelines
Close Box Specifications
"Yes" and "No", the two direct responses to the question "Save changes before closing?"
are placed together on the left side of the box. "Yes", the default button, is boldly outlined.
"Cancel", which cancels the close command, is to the right, separate from "Yes" and
"No".
After the user selects Close from the File menu, the text of the question in the Close box is
generally "Save changes before closing?" However, if the user sees this dialog after
choosing "Quit", the text would instead be "Save changes before quitting?" If the
application supports multiple windows, the text could be "Save changes to [document
name] before closing window?" The box should always look the same and appear in the
same place on the screen.
The box itself is 120 pixels high by 238 pixels wide. Its standard location is
(100,120)(220,358) but other locations may be apprdpriate.
Here are the other coordinates for the standard close box (assuming standard location):
the text
(12,20)(45,223)
the word "yes"
(58,25)(76,99)
the word "no"
(86,25)(104,99)
the word "cancel" (86,141)(104,215)
If you must devise a close box different from the one described here, maintain the general
arrangement of the buttons and remember that the user's safest choice should be the default
button and that the most dangerous choice should be the most difficult to make happen.
Standard Close Dialog W-11

<!-- source-page: 25 -->
## Page 25

2
USING ASSEMBLY LANGUAGE
In the 128K ROM, Toolbox and Operating System traps have separate trap dispatch tables.
It's possible for a Toolbox trap and an Operating System trap to have the same trap
number.
THE TRAP DISPATCH TABLE
In the 64K ROM, references to both Toolbox and Operating System routines are made
through a single trap dispatch table. For compactness, entries in that table are encoded into
one word each. The high-order bit of each entry tells whether the routine resides in ROM
(0) or RAM (1). The remaining 15 bits give the offset of the routine relative to a base
address. For routines in ROM, this base address is the beginning of the ROM; for routines
in RAM, it's the beginning of the system heap. The two base addresses are kept in a pair
of global variables named ROMBase and RAMBase. Using 15-bit unsigned word offsets,
the range of locations that the trap dispatch table can address is limited to 64K bytes. Also,
the interleaving of Operating System and Toolbox trap numbers limits the total number of
traps to 512 and means that no two traps can be represented by the same number.
In the 128K ROM, the Toolbox and Operating System traps have separate dispatch tables.
Instead of a packed format, entries in these dispatch tables are stored as full long-word
addresses so the dispatcher makes no distinction between ROM and RAM addresses. The
Operating System dispatch table consists of 256 long words, from address $400 through
$7FF; this replaces the old dispatch table of 512 words. The Toolbox table consists of 512
long words, from address $COO through $13FF.
Warning: The format of the trap dispatch tables may be different in future versions
of Macintosh system software. If it's absolutely necessary that you manipulate the
trap dispatch tables, use the Operating System Utility routines NGetTrapAddress and
NSetTrapAddress (or with the 64K ROM, GetTrapAddress and SetTrapAddress);
they're described in chapter 25 of this volume.
FORMAT OF TRAP WORDS
As described in chapter 4 of Volume I, a trap word begins with the hexadecimal digit $A
(binary 1010); the rest of the word identifies the routine you're calling, along with
additional information pertaining to the call.
Figure 1 shows the format of Toolbox and Operating System trap words. Bit 11 of the trap
word determines how the remainder of the word will be interpreted; usually it's 0 for
Operating System calls and 1 for Toolbox calls, though there are certain exceptions.
FormatofTrap Words W-13

<!-- source-page: 26 -->
## Page 26

Inside Macintosh
Toolbox Trap Word (Bit 11=1)
15 14 13 12 11 10 9
8
trap number
I I
reserved for future use
l___= auto-pop bit
Operating System Trap Word (Bit 11 = 0)
0
15 14 13 12 11 10 9
8
7
0
I 1 I 0 I 1 I 0 I 0 I flags I I
trap number
I
L set if trap dispatcher
doesn't preserve AO
(routine passes it back)
Figure 1. Toolbox and Operating System Trap Words
In the 64K ROM, an Operating System trap and a Toolbox trap cannot have the same trap
number; the GetTrapAddress and SetTrapAddress routines do not distinguish between
Toolbox and Operating System traps.
Since each group has its own dispatch table in the 128K ROM, there can be a Toolbox trap
and an Operating System trap with the same trap number. Two new routines-
NGetTrapAddress and NSetTrapAddress-have been added; they use bits 9 and 10 of their
trap word for specifying the group to which a routine belongs.
IV-14 Format of Trap Words'

<!-- source-page: 27 -->
## Page 27

3 THE RESOURCE MANAGER
The speed and efficiency of the Resource Manager have been significantly enhanced in the
128K ROM. Nine routines have been added; seven are functional counterparts of 64K
ROM routines but search only the current resource file, and two routines are new.
Additional standard resource types have been defined, two new result codes have been
added, and the reporting of error conditions has been improved.
RESOURCE MANAGER ROUTINES
FUNCTION Count1Types : INTEGER;
Countl Types is the same as CountTypes except that it returns the number of resource types
in the current resource file only.
PROCEDURE GetlindType (VAR theType: ResType; index: INTEGER);
Assembly-language note: The macro you invoke to call GetllndType from
assembly language is named _GetllxType.
GetllndType is the same as GetIndType except that it searches the current resource file
only. Given an index ranging from 1 to Count1Types (above), GetllndType returns a
resource type in theType. Called repeatedly over the entire range for the index, it returns all
the resource types in the current resource file. If the given index isn't in the range from 1
to Countl Types, GetllndType returns four NUL characters (ASCII code 0).
FUNCTION Count1Resources (theType: ResType) : INTEGER;
Count1Resources is the same as CountResources except that it returns the total number of
resources of the given type in the current resource file only.
FUNCTION GetlindResource (theType: ResType; index: INTEGER)
Handle;
Assembly-language note: The macro you invoke to call Get1IndResource from
assembly language is named _Get1IxResource.
Get1IndResource is the same as GetIndResource except that it searches the current resource
file only. Given an index ranging from 1 to Count1Resources(theType), GetlindResource
returns a handle to a resource of the given type (see Count1Resources, above). Called
Resource Manager Routines IV-15

<!-- source-page: 28 -->
## Page 28

Inside Macintosh
repeatedly over the entire range for the index, it returns handles to all resources of the given
type in the current resource file.
FUNCTION Get1Resource (theType: ResType; theID: INTEGER} : Handle;
Get1Resource is the same as GetR.esource except that it searches the current resource file
only.
FUNCTION Get1NamedResource (theType: ResType; name: Str255} :
Handle;
Get1NamedResource is the same as GetNamedResource except that it searches the current
resource file only.
FUNCTION Unique1ID (theType: ResType} : INTEGER;
Unique1ID is the same as UniqueID except that the ID number it returns is unique only
with respect to resources in the current resource file.
FUNCTION MaxSizeRsrc (theResource: Handle} : LONGINT;
MaxSizeRsrc is similar to SizeResource except that it does not cause the disk to be read;
instead it determines the size (in bytes) of the resource from the offsets found in the
resource map.
Since MaxSizeRsrc does not read from the disk, it returns only the maximum size of the
resource. In other words, you can count on the resource not being larger than the number
of bytes reported by MaxSizeRsrc; it's possible, however, that the resource is actually
smaller than the resource map indicates (because the file has not yet been compacted). If
called after UpdateResFile, MaxSizeRsrc will return the correct size of the resource.
Advanced Routines
FUNCTION RsrcMapEntry (theResource: Handle} : LONGINT;
RsrcMapEntry provides a way to access the resource references in the resource map.
Given a handle to a resource, RsrcMapEntry returns the offset of the resource's reference
from the beginning of the resource map. (For more information on resource references and
the structure of a resource map, see the section "Format of a Resource File" in the Resource
Manager chapter.) If it doesn't find the resource, RsrcMapEntry returns NIL and the
ResError function will return the result code resNotFound. If you pass it a NIL handle,
RsrcMapEntry will return garbage but ResError will return the result code noErr.
Warning: Since routines are provided for opening, accessing, and changing
resources, there's really no reason to access resources directly. To avoid damaging
the resource file, you should be extremely careful if you use RsrcMapEntry.
IV-16 Resource Manager Routines

<!-- source-page: 29 -->
## Page 29

The Resource Man11ger
FUNCTION OpenRFPerm (fileName: Str255; vRefNum: INTEGER;
permission: Byte) : INTEGER;
OpenRFPenn is similar to OpenResFile except that it allows you to specify the read/write
pennission of the resource file the first time it is opened; OpenRFPenn also lets you specify
in vRefNum the directory or volume on which the file is located (see chapter 19 of this
volume for more details on directories). Permission can have any of the values that you
would pass to the File Manager; these values are given in "Low-Level File Manager
Routines" in chapter 19 of this volume.
OpenRFPerm, like OpenResFile, will not open the specified file twice; it simply returns the
reference number already assigned to the file. In other words, OpenRFPerm cannot be
used to open a second access path to a resource file nor can it be used to change the
permission of an already open file. Since OpenRFPerm gives no indication of whether the
file was already open, there's no way to tell whether the file's open permission is what you
specified or what was specified by an earlier call.
'
Note: The shared read/write permission described in chapter 19 of this volume has
no effect with OpenRFPerm since the Resource Manager is unable to deal with a
portion of a resource file.
RESOURCE TYPES
The following standard resource types have been defined (System file version 3.0 or later):
Resource type
'CACH'
'FMTR'
'FOND'
'NFNT'
'PRER'
'PRES'
'PTCH'
'RDEV'
'ROvr'
'ROv#'
'bmap'
'ctab'
'insc'
Meaning
RAM cache code
3 1/2-inch disk formatting code
Font family record
128K ROM font
Device type for Chooser
Device type for Chooser
ROM patch code
Device type for Chooser
Code for overriding ROM resources
List of ROM resources to override
Bit maps used by the Control Panel
Used by the Control Panel
Installer script
Uppercase and lowercase letters are distinguished in resource types. You can use any fourcharacter sequence, except those listed above, those already reserved in chapter 5 of
Volume 1, and those sequences consisting entirely of lowercase letters (reserved by
Apple), for resource types specific to your application. There's no need to register your
resource types with Apple since they'll only be used by your application.
Resource Types IV-17

<!-- source-page: 30 -->
## Page 30

Inside Macintosh
CHECKING FOR ERRORS
In the 64K ROM, some error conditions resulting from certain Resource Manager routines
are not reported by the ResError function. Two additional result codes are defined in the
128K ROM version of the Resource Manager:
CONST resAttrErr = 198;
{attribute does not permit operation}
mapReadErr = 199;
{map does not permit operation}
In the 128K ROM, the following error conditions ate reported by ResError:
• The OpenResFile function checks to see that the information in the resource map is
internally consistent; if it isn't, ResError returns mapReadError.
• The CloseResFile procedure calls UpdateResFile. If UpdateResFile returns a nonzero
result code, that result code will be returned by CloseResFile.
• If you provide an index to GetIndResource (or Get1IndResource) that's either 0 or
negative, the ResError function will return the result code resNotFound.
• If you call DetachResource to detach a resource whose resChanged attribute has been
set, ResError will return the result code resAttrErr.
• If you call SetResInfo but the resProtected attribute is set, ResError will return the
result code resAttrErr.
• If you call ChangedResource but the resProtected attribute for the modified resource is
set, the ResError function will return the result code resAttrErr.
• If you call UpdateResFile but the mapRead.Only attribute for the resource file is set
(described in the "Advanced Routines" section of the Resource Manager chapter),
ResError will return the result code mapRea.dErr.
Warning: If you call the GetResource and Get1Resource functions with a resource
type that isn't in any open resource file, they return NIL but the ResError function
will return the result code noErr. With these calls, you must check that the handle
returned is nonzero.
ROM RESOURCES
The information presented in this section is useful only to assembly-language
programmers.
With the 64K ROM, many of the system resources are stored in the system resource file.
With the 128K ROM, the following system resources are stored in ROM:
W-18 ROM Resources

<!-- source-page: 31 -->
## Page 31

Type
ID
'CURS'
1
'CURS'
2
iCURS'
3
'CURS'
4
'DRVR'
2
'DRVR'
3
'DRVR'
4
'DRVR'
9
'DRVR'
A
'FONT'
0
'FONT'
C
'MDEF'
0
'PACK'
4
'PACK'
5
'PACK'
7
'SERD'
0
'WDEF'
0
Description
IBeamCursor
CrossCursor
Plus Cursor
WatchCursor
Printer Driver shell (.Print)
Sound Driver (.Sound)
Disk Driver (.Sony)
AppleTalk driver (.MPP)
Apple Talk driver (.ATP)
Name of system font
System font
Default menu definition procedure
Floating-Point Aritlunetic Package
Transcendental Functions Package
Binary-Decimal Conversion Package
Serial Driver
·
Default window definition function
The Resource Manager
Note: The Sound Driver, Disk Driver, and Serial Driver are in the 64K ROM, but
are not stored as resources.
When the Macintosh is turned on, a call is made to the InitResources function. The
Resource Manager creates a special heap zone within the system heap, and builds a
resource map that points to the ROM resources.
In order to use the ROM resources in your calls to the Resource Manager, the ROM map
must be inserted in front of the map for the system resource file prior to making the call.
The global variable RomMapInsert is used for this purpose; it tells the Resource Manager to
insert the ROM map for the next call only. An adjacent global variable, TmpResLoad, is
also useful; when RomMapInsert is TRUE, TmpResLoad determines whether the value of
the global variable ResLoad is taken to be TRUE or FALSE (overriding the actual value of
ResLoad) for the next call only. Figure 1 shows these two variables.
RomMapInsert (byte) I TmpResLoad (byte)
Figure 1. RomMapInsert and TmpResLoad
Two global constants, each a word in length, are provided for setting these variables in
tandem: mapTrue inserts the ROM map with SetResLoad(TRUE) and mapFalse inserts the
ROM map with SetResLoad(FALSE). As noted, both RomMapInsert and TmpResLoad
are cleared after each Resource Manager call.
Note: There is no real resource file associated with the ROM resources; the ROM
map has a path reference number of 1 (an illegal path reference number). There are
two ways to determine if a handle references a ROM resource. First, you can set up
TmpResLoad and RomMapInsert and call HomeResFile; if 1 is returned, the handle
is to a ROM resource. Second, you can dereference the handle and see if the master
pointer points into the ROM space by comparing it to the global variable ROMBase.
ROM Resources IV-19

<!-- source-page: 32 -->
## Page 32

Inside Macintosh
Overriding ROM Resources
This section explains how to override ROM resources.
Warning: As with intercepting system traps using the SetTrapAddress procedure,
you should override ROM resources only if it's absolutely necessary and you
understand the situation completely.
You can override some of the ROM resources, such as 'CURS' resources, simply by
putting the substitute resource in your application's resource fork. Other ROM resources
however, such 'DRVR' and 'PACK' resources, cannot be overridden in this way because
they are already referenced and in use when your application is launched.
Whenever InitResource is called, the ROM map is rebuilt. (Do not use InitResources to
rebuild the ROM map.) Each time the ROM map is rebuilt, the Resource Manager looks in
the system resource file for a 'ROvr' resource 0. If it finds such a resource, it loads it into
memory and jumps to this resource via a JSR instruction. The code in the 'ROvr' resource
looks in the system resource file for all resources of type 'ROv#' whose version word
matches the version word of the ROM (see Figure 2). For example, to override a resource
in the 128K ROM, the version must be $75.
version number of ROM (word)
number of resources - 1 (word)
resource type ( 4 bytes)
resource ID (word)
resource type (4 bytes)
resource ID (word)
7
]
Figure 2. Structure of an 'ROv#' Resource
To override ROM resources in this way, you'll first need a copy of an 'ROvr' resource;
you can obtain one by writing to:
Developer Technical Support
Mail Stop 3-T
Apple Computer, Inc.
20525 Mariani Avenue
Cupertino, CA 95014
You'll then need to create an 'ROv#' resource listing the resources you want to override.
IV-20 ROM Resources

<!-- source-page: 33 -->
## Page 33

The Resource Manager
SUMMARY OF THE RESOURCE MANAGER
Constants
CONST { Resource Manager result codes }
resAttrErr
mapReadErr
Routines
-198;
-199;
FUNCTION
Count1Types :
PROCEDURE GetlindType
FUNCTION
Count1Resources
FUNCTION
GetlindResource
FUNCTION
Get1Resource
FUNCTION
Get1NamedResource
FUNCTION
Unique1ID
FUNCTION
MaxSizeRsrc
FUNCTION
RsrcMapEntry
FUNCTION
OpenRFPerm
{attribute inconsistent with operation}
{map inconsistent with operation}
INTEGER;
(VAR theType: ResType; index: INTEGER);
(theType: ResType) : INTEGER;
(theType: ResType; index: INTEGER)
Handle;
(theType: ResType; theID: INTEGER)
Handle;
(theType: ResType; name: Str255)
Handle;
(theType: ResType) : INTEGER;
(theResource: Handle) : LONG!NT;
(theResource: Handle) : LONGINT;
(fileName: Str255; vRefNum: INTEGER;
permission: Byte) : INTEGER;
Assembly-Language Information
Constants
; Resource Manager result codes
resAttrErr
mapReadErr
.EQU
.EQU
-198
;attribute inconsistent with operation
-199
;map inconsistent with operation
; Values for setting RomMapInsert and TmpResLoad
mapTrue
mapFalse
.EQU
.EQU
$FFFF
$FF00
;insert ROM map with TmpResLoad set to TRUE
;insert ROM map with TmpResLoad set to FALSE
Special Macro Names
Pascal name
GetllndType
Getlln~esource
Macro name
_GetllxType
_Getll~esource
Summary of the Resource Manager W-21

<!-- source-page: 34 -->
## Page 34

Inside Macintosh
Variables
RomMapInsert
Flag for whether to insert map to the ROM resources (byte)
TmpResLoad
Temporary SetResLoad state for calls using RomMapInsert (byte)
IV-22 Summary of the Resource Manager

<!-- source-page: 35 -->
## Page 35

4 QUICKDRAW
The performance of QuickDraw in the 128K ROM has been enhanced considerably. New
capabilities have been added, and a number of bugs in the 64K ROM version have been
fixed. In conjunction with the Font Manager, QuickDraw supports font families, fractional
character widths, and the disabling of font scaling; these features are described in chapter 5
of this volume.
The 128K ROM version of QuickDraw supports all eight transfer modes for text drawing,
instead of just srcOr, srcBic, and scrXor.
The size of a picture is a long word with a range of over four gigabytes. To get the size of
a picture, use GetHandleSize instead of looking at the picSize field, which for compatibility
contains the low 16 bits of the real size. Old code will work fine for pictures up to 327 67
bytes. To check whether you have run out of memory during picture creation, test
EmptyRect(picFrame); it returns TRUE if you have.
The following bugs have been fixed:
• RectInRgn used to return TRUE occasionally when the rectangle intersected the
region's enclosing rectangle but not the actual region.
• SectRgn, DiffRgn, U nionRgn, XorRgn, and FrameRgn used to cause a stack
overflow for regions with more than 25 rectangles in one scan line. Since this is no
longer true, the warning on page I-186 regarding undefined results no longer applies.
• PtToAngle didn't work correctly when the angle was 90 and the aspect ratio was a
power of two.
•In some cases where the Copy Bits source bitmap overlapped its destination, the
transfer would destroy the source bitmap before it was used.
• If you tried to draw a long piece of shadowed text with a tall font, QuickDraw would
cause a stack overflow if there wasn't enough stack space for the required off-screen
buffer. Now it detects the potential stack overflow and recurses on the left and right
halves of the text.
• DrawText did not work correctly in pictures if the character count was greater
than 255.
QUICKDRAW ROUTINES
The SeedFill and CalcMask procedures operate on a portion of a bitmap. In both routines,
srcPtr and dstPtr point to the beginning of the data to be filled or calculated, not to the
beginning of the bitmap; both parameters must point to word boundaries in memory.
SrcRow and dstRow specify the row width in bytes (in other words, the row Bytes field of
the BitMap record) of the source and destination bitmaps respectively. Height and words
QuickDraw Routines W-23

<!-- source-page: 36 -->
## Page 36

Inside Macintosh
determine the number of bits to be filled or calculated; words is the width of the rectangle in
words and height is the height of the rectangle in pixels. Figure 1 illustrates the use of
these parameters.
srcRow
+----- dstRow ---
+-words-+
srcPtr -+---+ D T
leight
~words-+
dstPtr ___ 0 T
right
source bitmap
destination bitmap
Figure 1. Parameters Used by SeedFill and CalcMask
PROCEDURE SeedFill (srcPtr,dstPtr: Ptr; srcRow,dstRow,height,
words,seedH,seedV: INTEGER);
Given a source bit image, SeedFill computes a destination bit image with l's only in the
pixels where paint can leak from the starting seed point, like the MacPaint paint-bucket
tool. SeedH and seedV specify horizontal and vertical off sets, in pixels, from the
beginning of the data pointed to by dstPtr, determining how far into the destination bit
image filling should begin. Calls to SeedFill are not clipped to the current port and are not
stored into QuickDraw pictures.
PROCEDURE CalcMask (srcPtr,dstPtr: Ptr; srcRow,dstRow,height,
words: INTEGER);
Given a source bit image, CalcMask computes a destination bit image with 1 's only in the
pixels where paint could not leak from any of the outer edges, like the MacPaint lasso tool.
Calls to CalcMask are not clipped to the current port and are not stored into QuickDraw
pictures.
PROCEDURE CopyMask (srcBits,maskBits,dstBits: BitMap; srcRect,
maskRect,dstRect: Rect);
Copy Mask is a new version of the Copy Bits procedure; it transfers a bit image from the
source bitmap to the destination bitmap only where the corresponding bit of the mask
rectangle is a 1. (Note that the mask is specified as a rectangle instead of as a handle to a
region.) It can be used along with CalcMask to implement the lasso copy as in MacPaint;
it's also useful for drawing icons. Copy Mask doesn't check for overlap between the
source and destination bitmaps, doesn't stretch the bit image, and doesn't store into
QuickDraw pictures. Copy Mask does, however, respect the current port's visRgn and
clipRgn if dstBits is the portBits of the current grafPort.
W-24 QuickDraw Routines

<!-- source-page: 37 -->
## Page 37

QuickDraw
PROCEDURE MeasureText (count: INTEGER; textAddr,charLocs: Ptr);
This procedure is designed to improve performance in specialized applications such as
word processors by providing an array version of the Text Width function; it's like calling
Text Width repeatedly for a given set of characters. TextAddr points to an arbitrary piece of
text in memory, and count specifies how many characters are to be measured.
MeasureText moves along the string and, for each character, computes the distance from
TextAddr to the right edge of the character. CharLocs should point to an array of count + 1
integers. Upon return, the first element in the array will always contain O; the other
elements will contain pixel positions on the screen for all of the specified characters.
Note: Measure Text only works with text displayed on the screen; since it doesn't go
through the Quick:Draw procedure StdText, it can't be used to measure text to be
printed.
Advanced Routine
The function GetMaskTable, accessible only from assembly language, returns in register
AO a pointer to a ROM table containing the following useful masks:
.WORD $0000,$8000,$COOO,$EOOO
;Table of 16 right masks
.WORD $FOOO,$F800,$FCOO,$FEOO
.WORD $FF00,$FF80,$FFCO,$FFEO
.WORD $FFF0,$FFF8,$FFFC,$FFFE
.WORD $FFFF,$7FFF,$3FFF,$1FFF
;Table of 16 left masks
.WORD $0FFF,$07FF,$03FF,$01FF
.WORD $00FF,$007F,$003F,$001F
.WORD $000F,$0007,$0003,$0001
.WORD $8000,$4000,$2000,$1000
;Table of 16 bit masks
.WORD $0800,$0400,$0200,$0100
.WORD $0080,$0040,$0020,$0010
.WORD $0008,$0004,$0002,$0001
QuickDraw Routines IV-25

<!-- source-page: 38 -->
## Page 38

Inside Macintosh
SUMMARY OF QUICKDRAW
RoutJnes
PROCEDURE Seed.Fill
(srcPtr,dstPtr: Ptr; .srcRow,dstRow,height,words,
seedH,seedV: INTEGER);
PROCEDURE CalcMask
(srcPtr,ds~Ptr: Ptr; srcRow,dstRow,height,words:
INTEGER);
PROCEDURE CopyMask
(srcBits,maskBits,dstBits: BitMap; srcRect,
maskRect,dstRect: Rect);
PROCEDURE MeasureText (count: INTEGER; textAddr,charLocs: Ptr);
Assembly-Language Information
Routine
Trap macro
_GetMaskTable
On entry
W-26 Summary of QuickDraw
On exit
AO: ptr to mask table in ROM

<!-- source-page: 39 -->
## Page 39

5 THE FONT MANAGER
29
About the Font Manager
29
Fonts and Their Familie~
30
About Names and Numbers
31
Font Manager Routines
33
Comiilunication Between QµickDraw and the Font Manager
33
Font Scaling
33
Fractional Character Widths
34
Font Manager Data Stru~s
35
Font Records
36
Family Records
41
Global Width Tables
42
Font and Font Family Resources
43
Family Record Format
44
Restrictions on the 'FONT' Type
45
Summary of the Font Mana~er
Contents JV-27

<!-- source-page: 40 -->
## Page 40

Inside Macintosh
IV-28
I!
II

<!-- source-page: 41 -->
## Page 41

The Font Manager
ABOUT THE FONT MANAGER
The Font Manager has been significantly improved by the addition of new data structures,
most notably the family record. Containing additional typographic information about a
font, the family record allows more fonts, fractional character widths (that is, character
widths expressed as fixed-point numbers rather than simple integers) for greater precision
on high-resolution devices such as the LaserWriter, and the option of disabling font scaling
for improved speed and legibility.
The addition of the family record and its related data structures is transparent to most
existing applications and is of interest only to advanced programmers designing specialized
fonts for the LaserWriter or writing their own font editors.
Most programmers will simply want to take advantage of the new features. Two routines,
SetFractEnable and SetFScaleDisable, are provided for this purpose; they're described in
"Font Manager Routines" below.
FONTS AND THEIR FAMILIES
In the 64K ROM version of the Font Manager, font is defined as the complete set of
characters of one typeface; it doesn't include the size of the characters, and usually doesn't
include any stylistic variations. In other words, fonts are defined in the plain style and
stylistic variations, such as bold and italic, are applied to them. For example, Times plain
(or roman) defines the font, while Times italic is a stylistic variation applied to that font.
In the 128K ROM version, the definition of a font is broadened to include stylistic
variations. That is, a separate font can be defined for certain stylistic variations of a
typeface. The set of available fonts for a given typeface is known as a font family.
This allows QuickDraw to use an actual font instead of modifying a plain font, thereby
improving speed and readability. For example, suppose the user of a word processor
selects a phrase in 12-point Times Roman and chooses the italic style from a menu.
QuickDraw asks for an italic Times and, assuming that the proper resources are available,
the Font Manager returns a 12-point Times Italic font QuickDraw could then draw the
phrase from an actual italic font rather than having to slant the plain font.
Note: The standard stylistic variations will still be performed by QuickDraw when
they're not available as actual fonts.
Information about fonts and their families is stored as resources in resource files; the Font
Manager calls the Resource Manager to read them into memory. Fonts are stored as
resources of type 'FONT' or 'NFNT'. Fonts known to the system are stored in the system
resource file; you may also define your own fonts and include them in your application's
resource file or even in the resource file for a document. The information about a font
family is stored as a resource of type 'FOND'; this includes the resource IDs of all the fonts
in the family, as shown in Figure 1.
Fonts and Their Families IV-29

<!-- source-page: 42 -->
## Page 42

Inside Macintosh
FOND
FONT
resource
resource
resource ID
resource ID
NFNT
resource
resource ID
NFNT
resource
Figure 1. Font Manager Resources
The 'NFNT' resource is new to the 128K ROM version of the Font Manager; it has the
same format as the 'FONT' resource and allows for many more fonts. An 'NFNT'
resource type can also be used to mask all but plain fonts from appearing in a font menu.
In this way, the system resource file can contain Times, Times Italic, Times Bold, and
Times Bold Italic, yet only Times will appear on the Font Menu. (The user would need to
choose Italic from the Style menu.)
The 64K ROM can only handle 'FONT' resources; it ignores resources of type 'NFNT'
and 'FOND'.
Warning: If you're creating a font, be sure to read the section "Restrictions on the
'FONT' type" below for information on maintaining compatibility with the 64K
RO Ms.
It's crucial that all new fonts have a corresponding 'FOND' resource. A minimal 'FOND'
resource can be made for a font by using the Font/DA Mover (version 3.0 or later) to copy
the font into a different file that has no font with the same name.
Note: A 'FOND' resource created this way does not contain any optional tables, but
it does contain the font association table (described below) that maps family numbers
and font sizes into resource IDs.
Warning: Be aware that when a 'FOND' is present, the Font Manager uses it
exclusively to determine which fonts are available. Fonts should be added to or
deleted from the System file with a tool like the Font/DA Mover, which correctly
updates the 'FOND' as well as the 'FONT'.
The Font Manager uses these resources to build two data structures in the application heap.
The font record contains information about a font and the family record contains
information about a font family.
About Names and Numbers
In the 64K ROM version of the Font Manager, a font is identified by its font number,
which is always between 0 and 255. Each font also has a name that's used to identify it in
menus. Font families are identified by a family number and a family name. Since existing
routines rely on passing and returning the font number in Font Manager routines, the
W-30 Fonts and Their Families

<!-- source-page: 43 -->
## Page 43

The Font Manager
family number must be the same as the font number, and the family name must be the same
as the font name. Family numbers 0 through 127 are reserved for use by Apple; numbers
128 through 255 are assigned by Apple for fonts created by software developers.
Assembly-language note: You can determine the system family number and size
by reading the global variables SysFontFam and SysFontSiz, respectively. This is
highly recommended, especially if your application is intended to run on Macintoshes
that are localized for non-English-speaking countries, as the localization process may
change the system font
You can get the family number of the application font from the global variable
ApFontID. You can substitute a different family number in this variable but the
application font is reset to its default value (it's stored in parameter RAM) whenever a
new application is launched.
Since font numbers only range from 0 to 255, only font families with family numbers in
this range are recognized by the 64K ROM version of the Font Manager. All fonts with
family numbers from 0 through 255 are stored as resources of type 'FONT', so that the
64K ROM's version of the Font Manager can recognize them.
It's very important that all new fonts and font families be registered with Apple to avoid
conflict To register the name of a font family, write to:
Developer Technical Support
Mail Stop 3-T
Apple Computer, Inc.
20525 Mariani Avenue
Cupertino, CA 95014
When there's a conflict, font families may be renumbered by the Font/DA Mover. For
instance, when the Font/DA Mover moves a font or font family into a file in which there's
already a font (or font family) with that number (but with a different name), the new font
(or font family) is renumbered. For this reason, you should always call GetFNum to
verify the number of a font you want to access.
FONT MANAGER ROUTINES
To improve the speed and readability of text display in your application, use the
SetFractEnable and SetFScaleDisable procedures to enable fractional character widths and
disable font scaling. Certain applications do not work properly when fractional character
widths are used and font scaling is disabled, so these features are turned off by default.
The FontMetrics function is much like QuickDraw's GetFontInfo function except that it
returns fixed-point values, letting you draw characters in more precise locations on the
screen.
Font Manager Routines W-31

<!-- source-page: 44 -->
## Page 44

Inside Macintosh
If there's a 'FOND' resource associated with the most recently drawn font, making the font
resource purgeable or unpurgeable with the SetFontLock procedure will make the 'FOND'
resource resource purgeable or unpurgeable as well.
PROCEDURE FontMetrics (VAR theMetrics: FMetricRec);
FontMetrics is similar to the QuickDraw procedure GetFontInfo except that it returns fixedpoint values for greater accuracy in high-resolution printing.
The FMetricRec data structure is defined as follows:
TYPE FMetricRec =
RECORD
ascent:
descent:
leading:
widMax:
wTabHandle:
END;
Fixed;
Fixed;
Fixed;
Fixed;
Handle;
{ascent}
{descent}
{leading}
{maximum character width}
{handle to global width table}
Ascent, descent, leading, and widMax are identical in function to their counterparts in
GetFontInfo. WTabHandle is a handle to the global width table (described below).
PROCEDURE SetFractEnable (fractEnable: BOOLEAN) [NotinROM]
SetFractEnable lets you enable or disable fractional character widths. If fractEnable is
TRUE, fractional character widths are enabled; if it's FALSE, the Font Manager uses
integer widths. To ensure compatibility with existing applications, fractional character
widths are disabled by default.
Assembly-language note: From assembly language, you can change the value of
the global variable FractEnable.
PROCEDURE SetFScaleDisable (fontScaleDisable: BOOLEAN);
SetFScaleDisable lets you disable or enable font scaling. If fontScaleDisable is TRUE,
font scaling is disabled and the Font Manager returns an unscaled font with more space
around the characters; if it's FALSE, the Font Manager scales fonts. To ensure
compatibility with existing applications, the Font Manager defaults to scaling fonts.
Assembly-language note: All programmers should use the SetFScaleDisable
procedure to disable and enable font scaling. In particular, setting the global variable
FScaleDisable is insufficient.
IV-32 Font Manager Routines

<!-- source-page: 45 -->
## Page 45

COMMUNICATION BETWEEN QUICKDRAW
AND THE FONT MANAGER
The Font Manager
The basic structure of the font input and output records passed between QuickDraw and the
Font Manager is unchanged.
Note: Advanced programmers who use the FMSwapFont function should be aware
that the Font Manager may attach optional tables to the font output record it returns.
The information QuickDraw passes to the Font Manager includes the font or family
number, the font size, and the scaling factors QuickDraw wants to use; the search for an
appropriate font is as follows.
The Font Manager first looks for a 'FOND' resource matching the ID of the requested font
or font family. If it finds one, it searches the family record's font association table (detailed
below) for a an 'NFNT' or 'FONT' resource matching the requested style and size. If it
can match the size but not the style, it returns a font that matches as many properties as
possible, giving priority first to italic, then to bold. Quickdraw must then add any needed
stylistic variations (using the information passed in the bold, italic, ulOffset, ulShadow,
ulThick, and shadow fields of the font output record).
If the Font Manager can't find a 'FOND' resource, it looks for a 'FONT' resource with the
requested font number and size. (It doesn't look for a 'NFNT' resource since these occur
only in conjunction with 'FOND' resources.)
If the Font Manager cannot find a font for a particular style, the Font Manager and
QuickDraw derive a font (as in the 64K ROM version).
Font Scaling
If the Font Manager can't find a font of the requested size and font scaling is enabled, it
follows the standard scaling algorithm (described in chapter 7 of Volume I) with one
exception: If it can't find a font that's double or half the requested size, it looks for the font
that's closest to the request size, either larger or smaller.
If it can't find a font of the requested size and font scaling is disabled, the Font Manager
looks for a smaller font closest to the requested size and returns with it with the widths for
the requested size. Thus, QuickDraw draws the smaller font with the spacing of the larger,
requested font. This is generally preferable to font scaling since it's faster and more
readable. Also, it accurately mirrors the word spacing and line breaks that the document
will have when printed, especially if fractional character widths are used.
Fractional Character Widths
The use of fractional character widths allows more accurate character placement on highresolution output devices such as the LaserWriter. It also enables character placement on
the screen to match more closely that on the LaserWriter (although QuickDraw cannot
actually draw a letter 3.5 pixels wide, for instance). The Font Manager will, how~ver,
Communication Between Quick.Draw and the Font Manager IV-33

<!-- source-page: 46 -->
## Page 46

Inside Macintosh
~tore the locations of characters more accurately than any particular screen can display.
Given exact widths for characters, words, and lines, the LaserWriter can print faster and
give better spacing. A price must be paid, however; since screen characters, are made up of
whole pixels, ·spacing between characters and words will be uneven as the fractional parts
are rounded off. The extent of the distortion depends on the font size relative to the screen
resolution.
The Font Manager communicates fractional character widths Quickpraw via the global
width table, a data structure allocated in the system heap. The Forit Manager gathers the
width data for this· table from one of three data structures.
Warning: You should always obtain character widths from the global width table
since you ccµi't really know where the Font Manager obtained the width information
from. A h~dle to the global width table is returned by the FontMetrics procedure.
First, it looks for a font character-width table in the font record. In this table, the actual
widths of each character in the font are stored in a 16-bit fixed-point format with an integer
p~ in the high-order byte and a fractional part in the low-order byte.
If it doesn't find this table, it looks in the family record for a family character-width table.
For each font in the family, this table contains the fractional widths for every character as if
a hypothetical one-point font; the actual values for the characters are calculated by
multiplying these widths by the font size. The widths in this table are stored in a 16-bit
fixed-point format with an integer part in the high-order 4 bits and a fractional part in the
low-order 12 bits.
If no family character-width table is found, the global character widths are derived from the
integer widths contained in the offset/width table in the font record (described in chapter 7
of Volume I).
To use fractional character widths effectively, an application must get accurate widths for
the characters, either by using the QuickDraw function TextWidth or by looking in the
global width table.
Warning: Applications that derive their own character widths may not function
properly when fractional widths are enabled.
FONT MANAGER DATA STRUCTURES
This section describes the data structures that define fonts and font fa.mi.Hes; you need to
read it only if you're going to define your own fonts or write your own font editor. Most
of the information in this section is useful only to assembly-language programmers.
Figure 2 shows some of the relationships between the various data structures used by the
Font Manager. Handles are shown as dotted lines; the one pointer is shown by a solid line.
W-34 Font Manager Data Structures

<!-- source-page: 47 -->
## Page 47

The Font Manager
font record
..... )
font record
~
width table
~ ..........
font record
width table
FMOutRec
!
i,_
:•u
i :
!:: i i
i !
! : ...
L .......
............................................
fontHandle
...........................................
·1
width table I
i
I
FMlnRec
..
width list
~ ....
i
. (up to 12 handles)
! !
....____.,
widthPtr
7
j
: .................. w fdth T abHand I e
lastFOND
r-l ..... :-:-:-:-::-:-:-::-:-: ....
i
. .................. J
family record
........................ w i dthL i stHand
system heap
low memory
application heap
Figure 2. Font Manager Data Structures
Font records and fantlly records, the structures from which global width tables are derived,
are kept in· the application heap. Global ·width tables, which are used constantly, are kept in
the system heap.
· · -
Font Records
To maintain compatibility with existing applications, the order of the field~ in the font
record remains unchanged; two variable-length arrays are added at the end of the record,
however, to implement fractional character wi~ths.
·
Additional constants have been defined for use in the fontType field; it can now contain any
of the following values:
-
CONST propFont
$9000;
{proportional font}
prpFntH
$9001;
{ with height table}
prpFntW
$9002;
{ with width table}
prpFntHW
$9003;
{ with h~ight & width tables}
fixedFont
$B000;
{fixed-width font}
fxdFntH
$B001;
{ with height table}
fxdFntW
$B002;
{ with width table}
fxdFntHW
$B003;
{ with height & width tables~
fontWid
$ACBO;
{~ont width data: 64K ROM only}
Font Manager Data Structures W-35

<!-- source-page: 48 -->
## Page 48

Inside Macintosh
The low-order two bits of the fontType field tell whether the two optional tables are
present. If bit 0 is set, there's an image-height table; if bit 1 is set, there's a character width
table.
The optional character-width table immediately follows the offset/width table; it's a
variable-length array specifying the fixed-point character widths for each character in the
font. Each entry is a word in length. For compactness, a special 16-bit fixed-point format
is used with an unsigned integer part in the high-order byte and a fractional part in the loworder byte.
The optional image-height table, which speeds the drawing of characters, may also be
appended after the character-width table; it's a variable-length array specifying the image
height of each character in the font. Each entry is a word in length; the high-order byte is
the offset of the first non-white row in the character; the low-order byte is the number of
rows that must be drawn. The image height is the height of the character image and is less
than or equal to the font height; it's used in conjunction with QuickDraw for improved
character plotting. Most font resources don't contain this table; it's typically generated by
the Font Manager when the font is swapped in.
Note: The 64K ROM version of the Resource Manager limits the total space
occupied by the bit image, location table, offset/width table, and character-width and
image-height tables to 32K bytes. For this reason, the practical limit on the font size
of a full font is about 40 points.
Family Records
A family record defines a font family; the information is loaded from the 'FOND' resource.
Assembly-language note: The global variable LastFOND is a handle to the last
family record used. You can read the contents of the family record by using this handle.
You should not alter the contents of this record
The data type for a family record is as follows:
TYPE FarnRec =
RECORD
ffFlags:
ffFamID:
ffFirstChar:
ffLastChar:
ffAscent:
ffDescent:
ffLeading:
ffWidMax:
ffWTabOff:
ffKernOff:
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
IV-36 Font Manager Data Structures
{flags for family}
{family ID number}
{ASCII code of the first character}
{ASCII code of the last character}
{maximum ascent for 1-pt.font}
{maximum descent for 1-pt.font}
{maximum leading for 1-pt.font}
{maximum width for 1-pt.font}
{offset to width table}
{offset to kerning table}

<!-- source-page: 49 -->
## Page 49

ffStylOff:
ffProperty:
ffintl:
ffVersion:
ffAssoc:
ffWidthTab:
ffStyTab:
ffKernTab:
END;
LONGINT;
ARRAY[l. .9]
ARRAY [l. .2]
INTEGER;
FontAssoc;}
WidTable;}
StyleTable; }
KernTable;}
The Font Manager
{offset to style-mapping table}
OF INTEGER; {style property info}
OF INTEGER; {reserved}
{version number}
{font association table}
{width table}
{style-mapping table}
{kerning table}
Note: The variable-length arrays appear as comments because they're not valid
Pascal syntax; they're used only as conceptual aids.
The ftFlags field defines general characteristics of the font family, as follows:
Bit
Meaning
0
Set if there's an image-height table
1
Set if there's a character-width table
2-11
Reserved (should be zero)
12
Set to ignore FractEnable when deciding whether to use fixed-point values for
stylistic variations (see bit 13), clear to treat FractEnable as usual
13
Set to use integer extra width for stylistic variations, clear to compute fixedpoint extra width from the family style-mapping table when FractEnable is
TRUE
14
Set if family fractional-width table is not used, clear if table is used
15
Set for fixed-width font, clear for proportional font
The values in the ffAscent, ffDescent, ffLeading, and ffWid.Max describe the maximum
dimensions of the family as they would be for a hypothetical one-point font to be scaled up.
They use a special 16-bit fixed-point format with an integer part in the high-order 4 bits and
a fractional part in the low-order 12 bits. The FontMetrics procedure calculates the true
values by multiplying this number by the actual point size.
The ftWTabOff, ff.KernOff, and ffStylOff fields are offsets from the top of the record to
the start of the width table, kerning table, and style-mapping table, respectively; if any of
these fields is zero, the corresponding table does not exist.
Font Manager Data Structures IV-37

<!-- source-page: 50 -->
## Page 50

Inside Macintosh
The ffProperty field is the family style-property table, shown in Figure 3.
extra width for Plain text -set to 0 (word)
extra width for Bold text (word)
extra width for Italic text (word)
extra width for Under I i ne text (word)
extra width for Outline text (word)
extra width for Shadow text (word)
extra width for Condensed text (word)
extra width for Extended text (word)
not used - set to O (word)
Figure 3. Family Style-Property Table
Each entry is a 16-bit fixed-point number with a signed integer part in the high-order 4 bits
and a fractional part in the low-order 12 bits. These numbers are used to calculate the
amount of extra width for special stylistic variations; each of these values is multiplied by
the point size of the font actually being used. If the font already exists for a given style, the
value in its field is ignored.
The ffAssoc field contains the font association table. This table, shown in Figure 4, is
used to match a given font size and style combination with the resource ID of an actual
font.
number of entries - 1 (word)
first FONT entry (6 bytes)
second FONT entry (6 bytes)
7
]
Figure 4. Font Association Table
Note: In order to reduce search time, the Font Manager requires that the entries be
sorted according to the fontSize field, with the smallest sizes first. If multiple fonts
from the same family, the plain (roman) fonts come first. The Font Manager is
optimized to look first for 'NFNT' resources, then 'FONT' resources.
Each entry in the font association table has the format shown in Figure 5.
IV-38 Font Manager Data Structures

<!-- source-page: 51 -->
## Page 51

font size (word)
font style (word)
resource ID of associated
FONT resource (word)
Figure 5. Font Association Table Entry
The Font Manager
The font association table is followed by the family character-width table. As shown in
Figure 6, this table is actually a number of width tables (since a font family may include
numerous styles).
number of width tables - 1 (word)
style code (word)
first width table
style code (word)
second width tab I e
~
~
Figure 6. Family Character-Width Table
Each character-width table is preceded by a style code; the low-order byte of this word
specifies stylistic variations (see Figure 7). The widths in each table are for a hypothetical
one-point font; the actual values for the characters are calculated by multiplying these
widths by the font size. The widths in this table are stored in a 16-bit fixed-point format
with an unsigned integer part in the high-order 4 bits and a fractional part in the low-order
12 bits.
7
6
5
4
3
2
1
0
*
1 for Bold style selected
._ __ 1 for Italic style selected
....._ ____ 1 for Under I ine sty I e selected
-- 1 for Outline style selected
---- 1 for Shadow style selected
----- 1 for Condensed style selected
------- 1 for Extended style selected
* reserved for use by the Font Manager
Figure 7. Style Codes
Font Manager Data Structures W-39

<!-- source-page: 52 -->
## Page 52

In.side Macintosh
The style-mapping table and its associated tables are used by the LaserWriter driver and are
described in In.side LaserWriter.
The kerning table, like the family character-width table, is actually a number of kerning
tables (see Figure 8).
number of kerning tab I es -1 (word)
first kerning table
second kerning table
~
I
Figure 8. Kerning Table
Each kerning table is preceded by a style code; stored in the low-order byte of the word,
this style information has the same format shown in Figure 7 above. The number of entries
in the table follows the style word (see Figure 9).
style code (word)
number of entries (word)
first kerning pair entry (4 bytes)
second kerning pair entry (4 bytes)
7
]
Figure 9. Structure of a Kerning Table
The entries in each kerning table (shown in Figure 10) consist of a pair of characters
followed by a kerning offset for a hypothetical one-point font. This value, represented by
an integer part in the high-order 4 bits and a fractional part in the low-order 12 bits, is
multiplied by the size of the font to obtain the actual offset.
first character of kerning pair (byte)
second character of kerning pair (byte)
kerning offset (word)
Figure 10. Kerning Table Entry
IV 40 Font Manager Data Structures

<!-- source-page: 53 -->
## Page 53

The Font Manager
Global Width Tables
The Font Manager communicates fractional character widths to QuickDraw via a global
width table, a data structure allocated in the system heap. A handle to the global width
table is returned by the FontMetrics procedure. The format of the global width table is
follows:
TYPE
WidthTable =
RECORD
tabData:
tabFont:
sExtra:
style:
fID:
fSize:
face:
device:
inNumer:
inDenom:
aFID:
fHand:
usedFam:
aFace:
vOutput:
hOutput:
vFactor:
hFactor:
aSize:
tabSize:
END;
ARRAY[l .. 256] OF Fixed; {character widths}
Handle;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
Point;
Point;
INTEGER;
handle;
BOOLEAN;
Byte;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER
{font record u~ed to build table}
{space extra used for table}
{extra due to style}
{font family ID}
{font size request}
{style (face) request}
{device requested}
{numerators of scaling factors}
{denominators of scaling factors}
{actual font family ID for table}
{family record used to build table}
{used fixed-point family widths}
{actual face produced}
{vertical factor for expanding }
{ characters}
{horizontal factor for expanding
{ characters}
{not used}
{horizontal factor for increasing
{ character widths}
{actual size of actual font used}
{total size of table}
TabData is an array containing a character width for each of the 255 possible characters in a
font, plus one long word for the font's missing symbol. The widths are stored in the
standard 32-bit fixed-point format. If a character is missing, its entry contains the width of
the missing symbol.· (For efficiency, the Font Manager will store up to 12 recently used
global width tables.) InNumer and inDenom contain the vertical and horizontal scaling
factors copied from th~ font input record.
Scaling is effected in two ways: by expanding characters of the chosen font and by
artificially increasing the widths of the chosen font in the width table. HOutput and
vOutput give the factors by which characters are to be expanded horizontally and vertically.
HFactor is the factor by which the widths of the chosen font, after stylistic variations, have
been increased. (VFactor is not used.) Thus, multiplying hOutput and vOutput by hFactor
and vFactor gives the true font scaling; the product of hOutput and an entry in the width
table is that character's true scaled width. HOutput,vOutput, hFactor, and vFactor are all
16-bit fixed-point numbers, with an integer part in the high-order byte and a fractional part
in the low-order qyte. ·
Font Manager Data Structures IV41

<!-- source-page: 54 -->
## Page 54

Inside Macintosh
If font scaling has been enabled, hFactor and vFactor both have a value of 1. In any case,
hOutput, vOutput, hFactor, and vFactor are adjusted so that the values of hFactor and
vFactor lie between 1 and 2, ~eluding 1.
Assembly-languag~ note: A handle to the global width table is contained in the
global variable WidthTabHandle. A poiq.ter to the table i~ contained in the global
variable WidthPtr; it's reliable imm.ediatdy after a call to FMSwapFont but, like all
pointers, may become invalicl after a call to the Meniocy Map.ager.
.
The global variable WidthLis~d is a handle to a list of handles to up to l2 recentlyused width tables. You can ·scan this list, looking for width t!ibles thai match the family
number, size, and style of the font you wish to measure. If you reach a width handle
that's equal to -1, that width table is invalid, and you inust ~~an FMSwapFont call
to get a valid one. When you reach a handle that's zero, you've reached the end of the
list.
You should not use the global width table when special internationaj. interface software
is being used to accommodate non-Roman alphabets. You can recognize such software
by looking at the global variable IntlSpec; if it's greater than 0, special international
software is installed. If your application. uses non-Roman alphabets, write to
Developer Technical Support
Mail Stop 3-T
Apple Computer, Inc.
20525 Mariani Avenue
Cupertino, CA 95014
for the latest version of the International Utilities Package, which will be e~tended to
handle non-Roman alphabets.
FONT AND FONT FAMILY RESOURCES
The various sizes 9f a font are each stored as separate resources. The resource type for a
font is either 'FOW:f! or 'NFNT'; the two have identical formats:
·
Number ~f bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
Contents
FontType field of font record
FirsiChar field of font record
LastChar field of font record
WidMax field of font record
KernMax field of font record
NDescent field of font record
FRectWidth field of font record
FRectHeight field of font record
OW1Loc field of font record
Ascent field of font record
Descent field of font record
IV-42 Font and Font Family Resources

<!-- source-page: 55 -->
## Page 55

Number ot bytes
2 bytes
2 bytes
n bytes
mbytes
m bytes
m bytes
m bytes
Contents
Leading field of font record
Row Words field of font record
Bit image of font
.
n = 2 * rowWords * fRectHeight
Location table of font
m = 2 * (lastChar-firstChar+3)
Offset/width table of font
m = 2 * .(lastChar.:....firstChar+3)
Optional character-width table of font
m = 2 * (lastChar-fitstCh_ar+3)
Optional image-height table of font
m = 2 * (lastChar-firstChar+3)
The Font Mana,ger
The resource type 'FRSV' is reserved by the Font Manager; it identifies fonts used by the
system. Fonts whose resource IDs are contained in a 'FRSV' resource 1 will not be
removed from the system resource file by the Font/DA Mover. The format of a 'FRSV'
resource is as follows:
Number of bytes
Contents
2 bytes
Number of font resource IDs
n * 2 bytes
n font resource IDs
Family Record Format
A font family is stored as a resource of type 'FOND'; it consists of the following:
Number of bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
2 bytes
4 bytes
4 bytes
4 bytes
24 bytes
6 bytes
m bytes
n bytes
p bytes
q bytes
Contents
FOND Flags field of family record
FONDFamID field of family record
FONDFirst field of family record
FOND Last field of family record
FOND Ascent field of family record
FOND Descent field of family record
FONDLeading field of family record
FONDWidMax field of family record
FONJ:)WTabOff of family record
FONDKemOff of family record
FONDStylOff of family record
FONpProperty field of fafuily record
FOND Intl field of family record
.
FONDAs~pc field of family record (variable length)
FONDWidTable field of family record (variable length)
FONDStylTab field of family record (variable length)
FOND Kem tab field of family record (variable length)
Font and Font Family Resources IV43

<!-- source-page: 56 -->
## Page 56

Inside Macintosh
Restrictions on the 'FONr Type
For backward compatibility, all 'FONT' resources that are part of a 'FOND' have certain
restrictions:
1. The font name and family name must be identical.
2. The font number and family number must be identical since the Font Manager
interprets a family number as a font number.
3. The resource ID of the font must be the same number that would be produced
by concatenating the font number and the font size (as described in chapter 7 of
Volume I).
These restrictions ensure that both the 64K ROM and 128K ROM versions of the Font
Manager will associate the family number and point size with the proper corresponding font
resource ID, whether or not there's a family resource. 'NFNT' resources are not bound by
these restrictions (but neither will they be found by the 64K ROM version of the Font
Manager).
W-44 Font and Font Family Resources

<!-- source-page: 57 -->
## Page 57

The Font Manager
SUMMARY OF THE FONT MANAGER
Constants
CONST { Font types
propFont
prpFntH
prpFntW
prpFntHW
fixedFont
fxdFntH
fxdFntW
fxdFntHW
fontWid
}
$9000;
$9001;
$9002;
$9003;
$B000;
$B001;
$B002;
$B003;
$ACBO;
{proportional font}
{ with height table}
{ with width table}
{ with height & width tables}
{fixed-width font}
{ with height table}
{ with width table}
{ with height & width tables}
{font width data: 64K ROM only}
Data Types
FMetricRec
RECORD
ascent:
descent:
leading:
widMax:
wTabHandle:
END;
FamRec =
RECORD
Fixed;
Fixed;
Fixed;
Fixed;
Handle
ffFlags:
INTEGER;
ffFamID:
INTEGER;
ffFirstChar: INTEGER;
ffLastChar: INTEGER;
ffAscent:
INTEGER;
ffDescent:
INTEGER;
ffLeading:
INTEGER;
ffWidMax:
INTEGER;
ffWTabOff:
LONGINT;
ffKernOff:
LONGINT;
ffStylOff:
LONGINT;
ffProperty: ARRAY[l .. 9]
ffintl:
ARRAY[l .. 2]
ffVersion:
ffAssoc:
ffWidthTab:
ffStyTab:
ffKernTab:
END;
INTEGER;
FontAssoc;}
WidTable;}
StyleTable; }
KernTable;}
{ascent}
{descent}
{leading}
{maximum character width}
{handle to font width table}
{flags for family}
{family ID number}
{ASCII code of the first character}
{ASCII code of the last character}
{maximum ascent for 1-pt.font}
{maximum descent for 1-pt.font}
{maximum leading for 1-pt.font}
{maximum width for 1-pt.font}
{offset to width table}
{offset to kerning table}
{offset to style-mapping table}
OF INTEGER; {style property info}
OF INTEGER; {reserved}
{version number}
{font association table}
{width table}
{style-mapping table}
{kerning table}
Summary of the Font Manager IV-45

<!-- source-page: 58 -->
## Page 58

Inside Macintosh
WidthTable =
RECORD
tabData:
tabFont:
sExtra:
style:
fID:
fSize:
face:
device:
inNumer:
inDenom:
aFID:
fHand:
usedFam:
aFace:
vOutput:
hOutput:
vFactor:
hFactor:
aSize:
tabSize:
END;
Routines
ARRAY [ 1. . 256]
Handle;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
Point;
Point;
INTEGER;
handle;
BOOLEAN;
Byte;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER
OF Fixed; { character widths}
{font record used to build table}
{space extra used for table}
{extra due to style}
{font family ID}
{font size request}
{style (face) request}
{device requested}
{numerators of scaling factors}
{denominators of scaling factors}
{actual font family ID for table}
{family record used to build table}
{used fixed-point family widths}
{actual face produced)
{vertical factor for expanding )
{ characters}
{horizontal factor for expanding
{ characters)
{not used}
{horizontal factor for increasing
{ character widths)
{size of actual font used)
{total size of table)
PROCEDURE FontMetrics (VAR theMetrics: FMetricRec);
PROCEDURE SetFScaleDisable(fontScaleDisable: BOOLEAN);
PROCEDURE SetFractEnable (fractEnable: BOOLEAN);
[Not in ROM]
Assembly-Language Information
Constants
; Font types
propFont
prpFntH
prpFntW
prpFntHW
fixedFont
fxdFntH
fxdFntW
fxdFntHW
fontWid
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
$9000
$9001
$9002
$9003
$BOOO
$B001
$B002
$B003
$ACBO
IV-46 Summary of the Font Manager
;proportional font
with height table
with width table
with height & width tables
;fixed-width font
with height table
with width table
with height & width tables
;font width data

<!-- source-page: 59 -->
## Page 59

Font Metric Record Data Structure
ascent
descent
leading
widMax
wTabHandle
Ascent (word)
Descent (word)
Leading (word)
Maximum character width (word)
Handle to global width table (long)
Font Record ('FONT or 'NFNT') Data Structure
fFontType
fFirstChar
fLastChar
fWidMax
f.KernMax
fNDescent
fFRectWidth
fFRectHeight
fOWTLoc
fAscent
fDescent
fLeading
fRowWords
Font type (word)
ASCII code of first character (word)
ASCII code of last character (word)
Maximum character width (word)
Negative of maximum character kern (word)
Negative of descent (word)
Width of font rectangle (word)
Height of font rectangle (word)
Offset to offset/width table (word)
Ascent (word)
Descent (word)
Leading (word)
Row width of bit image I 2 (word)
Family Record ('FOND') Data Structure
fond.Flags
fondFamID
fondFirst
fondLast
fondAscent
fondDescent
fondLeading
fondWidMax
fondWTabOff
fondKernOff
fondStylOff
fondProperty
fondintl
fondAssoc
fondWidTab
fondStylTab
fondKemtab
Flags for family (word)
Family ID number (word)
ASCII code of first character (word)
ASCII code of last character (word)
Maximum ascent expressed for 1 pt. font (word)
Maximum descent expressed for 1 pt. font (word)
Maximum leading expressed for 1 pt. font (word)
Maximum widMax expressed for 1 pt. font (word)
Off set to width table (long)
Offset to kerning table (long)
Offset to style-mapping table (long)
Style property info (12 words)
Reserved (3 words)
Font association Table (variable length)
Optional character-width table (variable length)
Style-mapping table (variable length)
Kerning table (variable length)
The Font Manager
Summary of the Font Manager IV-47

<!-- source-page: 60 -->
## Page 60

Inside Macintosh
Global Width Table Data Structure
widTabData
widTabFont
widthSExtra
widthStyle
widthFID
widthFSize
widthFace
widthDevice
inNumer
inDenom
widthAFID
widthFHand
widthUsedFam
widthAFace
width VOutput
widthHOutput
width VF actor
widthHFactor
widthASize
widTabSize
Character widths ( 1024 bytes)
Font handle used to build table (long)
Space extra used for table (long)
Extra due to style (long)
Font family ID (word)
Font size request (word)
Style (face) request (word)
Device requested (word)
Numerators of scaling factors (long)
Denominators of scaling factors (long)
Actual font family ID for table (word)
Font family handle for table (long)
Used fixed point family widths? (boolean)
Actual face produced (byte)
Not used (word)
Horizontal factor for increasing character widths (word)
Vertical scale output value (word)
Horizontal scale output value (word)
Actual size of actual font used (word)
Total size of table (word)
Global Variables
ApFontID
FractEnable
IntlSpec
WidthListHand
WidthPtr
WidthTabHandle
SysFontFam
SysFontSiz
LastFOND
Font number of application font (word)
Nonzero to enable fractional widths (byte)
International software installed if greater than 0 (long)
Handle to a list of handles to recently-used width tables
Pointer to global width table
Handle to global width table
If nonzero, the font number to use for system font (byte)
If nonzero, the size of the system font (byte)
Handle to last family record used
IV-48 Summary of the Font Manager

<!-- source-page: 61 -->
## Page 61

6 THE WINDOW MANAGER
A new variation of the window definition function implements a feature known as window
zooming; a description of window zooming is found in chapter 1 of this volume.
If you 're using the standard document window, you can implement a zoom-window box
by specifying a window definition function with a resource ID of 0 and a variation code of
8 when you call either the NewWindow or GetNewWindow functions. Two fields in the
window record, dataHandle and spareFlag, are used only when variation code 8 is
specified (otherwise they're not used).
DataHandle contains a handle to two rectangles that specify the standard and user states of
the window:
TYPE WStateData
RECORD;
userState: Rect;
stdState: Rect
END;
If you wish, your application can access both states. You might want to provide initial
values for the user state. Or you might want to save and restore all windows to the same
state the next time your application is launched. To do this, you would save the two states
and determine which of the two is current. The next time the application is launched, you
would then create the window using the saved current state, and set the user and standard
states to their previous values, after the GetNewWindow or NewWindow call.
SpareFlag is TRUE if zooming has been requested (that is, if a variation code of 8 has been
specified).
If you create a custom window, you can give your window definition function any
variation code you wish. If you want to implement zooming in the custom window, you
must supply values for WStateData.
When there's a mouse-down event in the zoom-window box and your application calls the
FindWindow function, the integer returned will be one of the following predefined
constants:
CONST inZoomin
= 7;
{in zoom box for zooming in}
inZoomOut = 8;
{in zoom box for zooming out}
InZoom.In and inZoomOut both indicate that the mouse button was pressed in the zoomwindow box of the window. FindWindow returns inZoomIn when the window is in the
standard state (and will be zoomed in), and inZoomOut when it's in the user state (and will
be zoomed out).
If either of these constants are returned by FindWindow, call the TrackBox function
(described below) to handle the highlighting of the zoom-window box and to determine
whether the mouse is inside the box when the button is released. If TrackBox returns
TRUE, call the Zoom Window procedure (described below) to resize the window
appropriately.
The Window Manager IV-49

<!-- source-page: 62 -->
## Page 62

Inside Macintosh
Advanced programmers: Two additional constants have been defined for your window
definition function to return in response to a wHit message:
CONST winZoomin
= 5;
{in zoom box for zooming in}
winZoomOut = 6;
{in zoom box for zooming out}
WINDOW MANAGER ROUTINES
FUNCTION TrackBox (theWindow: WindowPtr; thePt: Point; partCode:
INTEGER) : BOOLEAN;
When there's a mouse-down event in the zoom-window box of the Window, the application
sl;iould call TrackBox with thePt equal to the point where the mouse button was pressed (in
global coordinates, as stored in the where field of the event record). The partCode
.
parameter contains the constant (either iHZoomln or inZoomOut) reiumed by FindWindow.
TrackB6x keeps control until the mouse button is released; it highlights the zoom-window
box irt the same way as a window's close box is highlighted. When the mouse button is
released, TrackBox unhighlights the zoom-window box and returns TRUE if the mouse is
inside the zoom-window box or FALSE if it's outside the box (in which case the
application should do nothing).
PROCEDURE ZoomWindow (theWindow: WindowPtr; partCode: INTEGER;
front: BOOLEAN);
Call Zoom Window after a call to TrackBox that returiis '.ffi..UE. The partCode parameter
contairts the constant (either inZoomIn or inZoqmOut) ryturned by FindWindow. The
window will be zoomed either out or in, depending on the stl;te of the window specified by
partCode. If the window is already irt the state specified by partCode, Zoom Window does
nothing. If the front parameter is TRUE, the window will be brought to the front;
otherwise, the window is left where it is. (This means a window can be zoomed without
necessarily becoming the active window.)
For best results, call the QuickDraw ~focedtire EraseRect with the portRect field of
the Window's gra:fPort before calling Zoom Window.
Warning: Using the QuickDraw procedure SetPort, set thePort to the window's
port before calling Zoom Window.
Note: ZoomWindow is in no way tied to the TrackBox function and cohldjust as
easily be called in response to a selection from a menu.
IV-50 Window Manager Routines

<!-- source-page: 63 -->
## Page 63

SUMMARY OF THE WINDOW MANAGER
Constants
CONST { Additional values returned by FindWindow
inZoomin
inZoomOut
7;
8;
{ip zoom box for zooming in}
{in zoom box for zooming out}
The Window Mana.ger
{ Values returned by window definition function's hit routine }
winZoomin =
5;
winZoomOut = 6;
{in zoom box for zooming in}
{in zoom box for zooming out}
Data Types
TYPE WStateData
Routines
RECORD;
userState: Rect;
{user state}
stdState:
Rect
{standard state}
END;
FUNCTION
TrackBox
(theWindow: WindowPtr; thePt: Point; partCode:
INTEGER)
: BOOLEAN;
PROCEDURE ZoomWindow
(theWindow: WindowPtr; partCode: INTEGER; front:
BOOLEAN);
Assembly-Language Information
Constants
; Additional val.ues returned by FindWindow
inZoomin
inZoomOut
.EQU
.EQU
7
8
;in zoom box for zooming in
;in zoom box for zooming out
; Values returned by window definition function's hit routine
winZoomin
winZoomOut
.EQU
.EQU
5
6
;in zoom box for zooming in
;in zoom box for zooming out
Summary of the Window Manager IV-51

<!-- source-page: 64 -->
## Page 64

Inside Macintosh
Window Record Data Structure
window Port
window Kind
wVisible
wHilited
wGoAway
wZoom
structRgn
contRgn
updateRgn
window Def
wDataHandle
wTitleHandle
wTitleWidth
wControlList
next Window
windowPic
wRefCon
window Size
Window's grafPort (portRec bytes)
Window class (word)
Nonzero if window is visible (byte)
Nonzero if window is highlighted (byte)
Nonzero if window has go-away region (byte)
Nonzero if window has a zoom-window box (byte)
Handle to structure region of window
Handle to content region of window
Handle to update region of window
Handle to window definition function
Handle to standard and user window states
Handle to window's title (preceded by length)
Width of title in pixels (word)
Handle to window's control list
Pointer to next window in window list
Picture handle for drawing window
Window's reference value (long)
Size in bytes of window record
Window State Data Structure
userState
stdState
Window's user state (rectangle; 8 bytes)
Window's standard state (rectangle; 8 bytes)
IV-52 Summary of the Window Manager

<!-- source-page: 65 -->
## Page 65

7 THE CONTROL MANAGER
Two new routines, UpdtControl and Draw 1 Control, have been added to the Control
Manager. In addition, there's a new control definition function that supports multiple lines
of text in controls.
CONTROL MANAGER ROUTINES
PROCEDURE UpdtControl (theWindow: WindowPtr; updateRgn: RgnHandle);
UpdtControl is a faster version of the DrawControls procedure. Instead of drawing all of
the controls in the Window, UpdtControl draws only the controls that are in the specified
update region. UpdtControl is called in response to an update event, and is usually
bracketed by calls to the Window Manager procedures Begin Update and EndUpdate.
UpdateRgn should be set to the visRgn of the Window's port (for more details, see the
BeginUpdate procedure in the Window Manager chapter).
Note: In general, controls are in a dialog box and are automatically drawn by the
DrawDialog procedure.
PROCEDURE Draw1Control (theControl: ControlHandle);
Drawl Control draws the specified control if it's visible within the window.
THE CONTROL DEFINITION FUNCTION
A new version of the control definition function (version 4 or greater) in the 128K ROM
allows buttons, check boxes, and radio buttons to have multiple lines of text in their titles.
When specifying the title with either NewControl or SetCTitle, simply separate the lines
with the ASCII character code $OD (carriage return). You can also use a version of the
Resource Editor that supports the 128K ROM to specify multi.line titles.
Note: This feature will work with the 64K ROM if the new version of the control
definition function is in the system resource file.
If the control is a button, each line is horizontally centered and separated from the
neighboring lines by the font's leading. (Since the height of each line is equal to the ascent
plus descent plus leading of the font used, be sure to make the total height of the enclosing
rectangle greater than the number of lines times this height.)
If the control is a check box or a radio button, the text is left-justified and the check box or
button is vertically centered within the enclosing rectangle, cntrlRect.
The Control Definition Function IV-53

<!-- source-page: 66 -->
## Page 66

Inside Macintosh
SUMMARY OF THE CONTROL MANAGER
Routine
PROCEDURE UpdtControl
(theWindow: WindowPtr; updateRgn: RgnHandle);
PROCEDURE Draw1Control (theControl: ControlHandle);
IV-54 Summary of the Control Manager

<!-- source-page: 67 -->
## Page 67

8 THE MENU MANAGER
The AddResMenu and InsertResMenu procedures have been modified to work with the
font family resource type ('FOND'). If you call either routine for a resource of type
'FONT', they first add all instances of type 'FOND' and then all instances of type 'FONT'.
The Menu Manager ignores resources of type 'NFNT'. Both routines, before adding a
new item to the menu, first check to see that an item with the same name is not already in
the menu. If an item with the same name is already there, the new item is not added. This
prevents duplication and gives items of type 'FOND' precedence over items of type
'FONT'.
AddResMenu and InsertResMenu both sort the items alphabetically as they're placed in the
menu; the order of items already in the menu, however, is unaffected. Neither routine
enables the items.
Note: If the name of your desk accessory appears not to have been sorted and is
inserted at the end of the Apple menu, the name is missing the leading null character.
Two new routines, InsMenuItem and DelMenuItem, let you insert and delete individual
items from an existing menu. Use of these routines is discouraged except in certain
situations where the user expects a menu to change (such as list of open windows).
Warning: Menu resources should never be marked as purgeable. If a Menu
Manager routine tries to access a menu that's been purged, a system error (ID 84)
will occur.
Note: In the 64K ROM version of the Menu Manager, if the user attempted to pull
down an empty menu (one with no items), an unsightly empty menu of arbitrary size
was displayed. In the 128K ROM version, the menu title is highlighted but the menu
is not pulled down at all.
MENU MANAGER ROUTINES
PROCEDURE InsMenuItem (theMenu: MenuHandle; itemString: Str255;
afteritem: INTEGER);
InsMenuItem inserts an item or items into the given menu where specified by the afterltem
parameter. If afterltem is 0, the items are inserted before the first menu item; if it's the item
number of an item in the menu, they're inserted after that item; if it's equal to or greater
than the last item number, they're appended to the menu.
The contents of itemString are parsed as in the AppendMenu procedure. Multiple items are
inserted in the reverse of their order in itemString.
Menu Manager Routines IV-55

<!-- source-page: 68 -->
## Page 68

Inside Macintosh
PROCEDURE DelMenuItem (theMenu: MenuHandle; item: INTEGER);
DelMenuItem deletes the specified item from the given menu.
Note: DelMenuItem is intended for maintaining dynamic menus (such as a list of
open windows). It should not be used for disabling items; you should use
Disableltem instead.
THE MENU DEFINITION PROCEDURE
This section describes changes to the default menu definition procedure ('MDEF'
resource O); some of the information presented in this section is accessible only through
assembly language.
Note: These features will work with the 64K ROM if the new menu definition
procedure is in the system resource file.
Variable Size Fonts
Menus are displayed in the system font. Since the system font and font size can now be
changed, the menu definition procedure calls the QuickDraw procedure GetFontInfo for the
system font to determine the height of menu items
Scrolling Menus
The default menu definition procedure allows longer menus by implementing automatic
scrolling. If the entire menu cannot be drawn on screen, dragging the cursor below the last
displayed item will cause the items in the menu to scroll up. Similarly, if items have been
scrolled past the top of the menu, dragging the cursor into the highlighted portion of the
menu bar will cause the menu to scroll back down. The maximum number of items that
can be drawn on the standard Macintosh screen with this new menu definition function
is 19 (instead of 20).
Warning: You should not disable any menu items in a menu containing more
than 31 items because the enableFlags field of the MenuinfoRec can only
handle 31 items.
SUMMARY OF THE MENU MANAGER
Routines
PROCEDURE InsMenuItem (theMenu: MenuHandle; itemString: Str255;
afteritem: INTEGER);
PROCEDURE DelMenuItem (theMenu: MenuHandle; item: INTEGER);
IV-56 Summary of the Menu Mana.ger

<!-- source-page: 69 -->
## Page 69

9 TEXTEDIT
Automatic scrolling of text (when the user is making a selection and drags the cursor out of
the view rectangle) is now supported by TextEdit.
To enable and disable automatic scrolling, call the procedure TEAuto View. TESelView
will, if automatic scrolling is enabled, automatically scroll the selection range into view.
TEPinScroll scrolls text within the view rectangle but stops when the last line comes into
view.
Note: When enabled, automatic scrolling can occur in response to TESelView,
TEKey, TEPaste, TEDelete, and TESetSelect.
When used with the System file version 3.0 or later, TextEdit also automatically supports
the movement of the insertion point with the Macintosh Plus arrow keys; this is described
in chapter 1 of this volume.
Warning: Command-arrow key combinations are not supported by TextEdit and
must be handled by your application. Selection expansion must also be handled by
your application.
TEXTEDIT ROUTINES
PROCEDURE TESelView (hTE: TEHandle);
If automatic scrolling has been enabled (by a call to TEAutoView, described below),
TESelView makes sure that the selection range is visible, scrolling it into the view rectangle
if necessary. If automatic scrolling is disabled, TESelView does nothing.
Note: The top left of the insertion is scrolled into view; if text is being displayed in a
rectangle that's not tall enough, automatic scrolling could cause the text to jump up
and down at times.
PROCEDURE TEPinScroll (dh,dv: INTEGER; hTE: TEHandle);
TEPinScroll is similar to TEScroll except that it stops scrolling when the last line scrolls
into the view rectangle.
PROCEDURE TEAutoView ,(auto: BOOLEAN; hTE: TEHandle);
TEAuto View enables and disables automatic scrolling of text in the edit record specified by
hTe. If the auto parameter is FALSE, automatic scrolling is disabled and calling
TESelView has no effect.
TextEdit Routines W-57

<!-- source-page: 70 -->
## Page 70

Inside Macintosh
DEFAULT CLICK LOOP ROUTINE
TextEdit now installs a default click loop routine in the edit record that supports automatic
scrolling; you still need, however, to update the scroll bars. If automatic scrolling is
enabled, this routine checks to see if the mouse has been dragged out of the view rectangle;
if it has, the routine scrolls the text using TEPinScroll. The amount by which the text is
scrolled, whether horizontally or vertically, is determined by the lineHeight field of the edit
record,.
SUMMARY OF TEXTEDIT
Routines
PROCEDURE TESelView
(hTE: TEHandle);
PROCEDURE TEPinScroll (dh,dv: INTEGER; hTE: TEHandle);
PROCEDURE TEAutoView
(auto: BOOLEAN; hTE: TEHandle);
IV-58 Summary of TextEdit

<!-- source-page: 71 -->
## Page 71

10 THE DIALOG MANAGER
Four routines-HideDItem, ShowDItem, Find.Dltem, and UpdtDialog-have been added
to the Dialog Manager.
Advanced programmers: The standard filterProc function called by ModalDialog now
returns 1 in itemHit and a function result of TRUE only if the first item is enabled.
Automatic scrolling is supported in editText items.
DIALOG MANAGER ROUTINES
PROCEDURE HideDItem (theDialog: DialogPtr; itemNo: INTEGER);
HideDItem hides the item numbered itemNo in the given dialog's item list by giving the
item a display rectangle that's off the screen. (Specifically, if the left coordinate of the
item's display rectangle is less than 8192, ShowDItem adds 16384 to both the left and right
coordinates the rectangle.) If the item is already hidden (that is, if the left coordinate is
greater than 8192), HideDItem does nothing,
HideDItem calls the EraseRect procedure on the item's enclosing rectangle and adds the
rectangle that contained the item (not necessarily the item's display rectangle) to the update
region. If the specified item is an active editText item, the item is first deactivated (by
calling TEDeactivate ).
·
Note: If you have items that are close to each other, be aware that the Dialog
Manager draws outside of the enclosing rectangle by 3 pixels for editText items and
by 4 pixels for a default button.
An item that's been hidden by HideDItem can be redisplayeq by the ShowDItem procedure.
Note: To create a hidden item in a dialog item list, simply add 16384 to the left and
right coordinates of the display rectangle.
PROCEDURE ShowDItem (theDialog: DialogPtr; itemNo: INTEGER);
ShowDItem redisplays the item numbered itemNo, previously hidden by HideDItem, by
giving the item the display rectangle it h<J.d prior to the HideDItem call. (Specifically, if the
left coordinate of the item's display rectangle is greater than 8192, ShowDItem subtracts
163 84 from both the left and right coordinates the rect<J.Ilgle.) If the item is already visible
(that is, if the left coordinate is less than 8192), ShowDItem does nothing.
ShowDItem adds the rectangle that contained the item (not necessarily the item's display
rectangle) to the update region so that it will be drawn. If the item becomes the only
editText item, ShowDItem activates it (by calling TEActivate).
Dialog Manager Routines IV-59

<!-- source-page: 72 -->
## Page 72

Inside Macintosh
FUNCTION FindDItem (theDialog: DialogPtr; thePt: Point) : INTEGER;
FindDItem returns the item number of the item containing the point specified, in local
coordinates, by thePt. If the point doesn't lie within the item's rectangle, FindDItem
returns -1. If there are overlapping items, it returns the item number of the first item in the
list containing the point. FindDItem is useful for changing the cursor when it's over a
particular item.
Note: FindDItem will return the item number of disabled items as well.
PROCEDURE UpdtDialog (theDialog: DialogPtr; updateRgn:
RgnHandle);
UpdtDialog is a faster version of the DrawDialog procedure. Instead of drawing the entire
contents of the given dialog box, UpdtDialog draws only the items that are in a specified
update region. UpdtDialog is called in response to an update event, and is usually
bracketed by calls to the Window Manager procedures Begin Update and EndUpdate.
UpdateRgn should be set to the visRgn of the Window's port. (For more details, see the
BeginUpdate procedure in chapter9 of Volume I.)
SUMMARY OF THE DIALOG MANAGER
Routines
PROCEDURE HideDItem
PROCEDURE ShowDItem
FUNCTION
FindDItem
PROCEDURE UpdtDialog
(theDialog: DialogPtr; itemNo: INTEGER);
(theDialog: DialogPtr; itemNo: INTEGER);
(theDialog: DialogPtr; thePt: Point) : INTEGER;
(theDialog: DialogPtr; updateRgn: RgnHandle);
W-60 Swnmary of the Dialog Manager

<!-- source-page: 73 -->
## Page 73

11 THE SCRAP MANAGER
The desk scrap is now written on the system startup volume (that is, the volume that
contains the currently open System file) rather than the default volume. With hierarchical
volumes, the scrap file is placed in the folder containing the currently open System file and
Finder.
In addition, the GetScrap and PutScrap functions will never return the result code
noScrapErr; if the scrap has not been initialized, the ZeroScrap function will be called. The
InfoScrap function also calls ZeroScrap if the scrap is uninitialized.
The Scrap Manager IV-61

<!-- source-page: 74 -->
## Page 74

Inside Macintosh
IV-62

<!-- source-page: 75 -->
## Page 75

12 TOOLBOX UTILITIES
A new fixed-point type, Fract, has been defined. Useful in graphics software, the Fract
type allows accurate representation of small numbers (between -2 and 2). Like the type
Fixed, a Fract number is a 32-bit quantity, but its implicit binary point is to the right of bit
30 of the number; that is, a Fract number has 2 integer bits and 30 fraction bits. As with
the type Fixed, a number is negated by taking its two's complement. Thus Fract values
range between -2 and 2-(2-30), inclusive. Figure 1 shows the weight of each binary place
of a Fract number.
15
-2
15
1
1
2
1
4
high-order word
I ow-order word
Figure 1. A Fract Number
0
In the 128K ROM, all fixed-point functions (that is, functions with Fixed or Fract
arguments or results) handle boundary cases uniformly. Results are rounded by adding
half a unit in magnitude in the last place of the stored precision and then chopping toward
zero. Overflows are set to the maximum representable value with the correct sign (typically
$80000000 for negative results and $7FFFFFFF for positive results). Division by zero in
any of the four divide routines results in $80000000 if the numerator is negative and
$7FFFFFFF otherwise; thus the special case 0/0 yields $7FFFFFFF.
Warning: Some applications may depend on spurious values returned by the 64K
ROM: FixRatio and FixMul overflowed unpredictably, FixRatio returned $80000001
when a negative number was divided by 0, and FixRound malfunctioned with negative
arguments.
TOOLBOX UTILITY ROUTINES
The 128K ROM version of the Toolbox Utilities supports fifteen new fixed-point
functions. Pascal typing will allow any of the operand combinations suggested here
without redefinition of the function.
Toolbox Utility Routines IV-63

<!-- source-page: 76 -->
## Page 76

Inside Macintosh
Arithmetic Operations
FUNCTION FracMul (x,y: Fract) : Fract;
FracMul returns x * y. Note that FracMul effects "type* Fract -> type":
Fract
*
Fract
->
LONGINT
*
Fract
->
Fract
*
LONGINT ->
Fixed
*
Fract
->
Fract
*
Fixed
->
FUNCTION FixDiv (x,y: Fixed) : Fixed;
Fract
LONG INT
LONG INT
Fixed
Fixed
FixDiv returns x I y. Note that FixDiv effects "type I type -> Fixed" and
"type I Fixed -> type":
Fixed
I
LONGINT
I
Fract
I
LONGINT
I
Fract
I
Fixed
->
LONGINT ->
Fract
->
Fixed
->
Fixed
->
FUNCTION FracDiv (x,y: Fract) : Fract;
Fixed
Fixed
Fixed
LONG INT
Fract
FracDiv returns x I y. Note that FracDiv effects "type I type -> Fract" and
"type I Fract -> type":
Fract
I
LONGINT
I
Fixed
I
LONGINT
I
Fixed
I
Fract
->
LONGINT ->
Fixed
->
Fract
->
Fract
->
FUNCTION FracSqrt (x: Fract) : Fract;
Fract
Fract
Fract
LONG INT
Fixed
FracSqrt returns the square root of x, with x interpreted as unsigned in the range 0 through
4-(2-30), inclusive: That is, bit 15 in Figure 1 has weight 2 rather than -2. The result, too,
is unsigned in the range 0 through 2, inclusive.
FUNCTION FracCos (x: Fixed) : Fract;
FUNCTION FracSin (x: Fixed) : Fract;
FracCos and FracSin return the cosine and sine of their radian arguments, respectively.
The hexadecimal value O.C910 (which is FixATan2(1,l)) is the approximation to rc/4 used
for argument reduction. Thus, FracCos and FracSin are nearly periodic, but with period
2*P instead of 2*rc, where P=3.1416015625 and re, of course, is 3.14159265 ....
W-64 Toolbox Utilities Routines

<!-- source-page: 77 -->
## Page 77

Toolbox Utilities
FUNCTION FixATan2 (x,y: LONGINT) : Fixed;
FixA Tan2 returns the arctangent of y I x in radians. Note that FixATan2 effects
"arctan(type I type)-> Fixed":
arctan(LONGINT I LONGINT) ->
arctan(Fixed I Fixed)
arctan(Fract I Fract)
Conversion Functions
->
->
Fixed
Fixed
Fixed
FUNCTION Long2Fix (x: LONGINT)
: Fixed;
FUNCTION Fix2Long (x: Fixed)
LONGINT;
FUNCTION Fix2Frac (x: Fixed) : Fract;
FUNCTION Frac2Fix (x: Fract) : Fixed;
Long2Fix, Fix2Long, Fix2Frac, and Frac2Fix convert between fixed-point types.
FUNCTION Fix2X
FUNCTION X2Fix
FUNCTION Frac2X
FUNCTION X2Frac
(x: Fixed) : Extended;
(x: Extended) : Fixed;
(x: Fract) : Extended;
(x: Extended) : Fract;
Fix2X, X2Fix, Frac2X, and X2Frac convert between Fixed and Fract and the Extended
floating-point type. These functions do not set floating-point exception flags.
Examples
Examples of the use of these fixed-point functions are provided below; all numbers are
decimal unless otherwise noted.
Function
Result
Comment
FixDiv
(X2Fix(l. 95), X2Fix(l.30))
$00018000
1.5 = 01.10 bin
FracDiv
(X2Frac(l.95), X2Frac (1.30))
$60000000
1.5 = 01.10 bin
FracMul
(X2Frac (1.50), X2Frac(l.30))
$7CCCCCCD
1.95 rounded
FracSqrt (X2Frac (1. 96))
$5999999A
1. 4 rounded
FracSin
(X2Fix(3.1416015625))
$00000000
0
FracCos
(X2Fix(3.1416015625))
$C0000000
-1
Fix2Long (X2Fix(l. 75))
$00000002
2
Fix2Frac (X2Fix(l. 75))
$70000000
1. 75 = 01.11 bin
Frac2Fix (X2Frac (1. 75))
$0001COOO
1. 75 = 01.11 bin
FixATan2 (X2Fix(l.00), X2Fix(l.00))
$0000C910
0.C910 hex=
X2Fix (1t/ 4)
FixDiv
(X2Fix(-l.95), X2Fix (1. 30))
$FFFE8000
-1. 5
FracDiv
(X2Frac (-1. 95), X2Frac ( 1. 30) ) $A0000000
-1.5
FracMul
(X2Frac (-1. 50) , X2Frac ( 1. 30) ) $83333333
-1. 95 rounded
FracSin
(X2Fix(-3.1416015625))
$00000000
0
FracCos
(X2Fix(-3.1416015625))
$COOOOOOO
-1
Fix2Long (X2Fix(-1. 75))
$FFFFFFFE
-2
Fix2Frac (X2Fix(-1. 75))
$90000000
-1. 75
Frac2Fix (X2Frac (-1. 75))
$FFFE4000
-1. 75
FixATan2 (X2Fix(-1.00), X2Fix(-1.00))
$FFFDA4DO
-3*X2Fix(1t/4)
3*0.C910 hex
Toolbox Utility Routines IV-65

<!-- source-page: 78 -->
## Page 78

Inside Macintosh
SUMMARY OF THE TOOLBOX UTILITIES
Routines
Arithmetic Operations
FUl'j'{::TION FracMul
(x,y : Fract) : Fract;
FUNCTION FixDiv
(x,y: Fixed) : Fixed;
li'UNCTION FracDiv
(x,y: Fr act) : Fract;
FUNC'l'ION FracSqrt
(x: Fr act)
Fract;
FUNCTION :FracCos
(x: Fixed) : Fract;
FUNCTION FracSin
(x: Fixed) : Fract;
FUNCTION FixATan2
(x,y: LONG INT) : Fixed;
Conversion Functions
FUNCTION Long2Fix
FUNCTION Fix2Long
FUNCTION Fix2Frac
FUNCTION Frac2Fix
FUNCTION Fix2X
FUNCTION X2Fix
FUNCTION Frac2X
FUNCTION X2Frac
(x: LONGINT)
: Fixed;
(x: Fixed)
LONGIN'!';
(x: Fixed) : Fract;
(x: Fract) : Fixed;
(x: Fixed) : Extended;
(x: Extended) : Fixed;
(x: Fract) : Extended;
(x: Extended) : Fract;
W-66 Summary of the Toolbox Utilities

<!-- source-page: 79 -->
## Page 79

13 THE PACKAGE MANAGER
The following Macintosh packages, previously stored only in the system resource file, are
now also found in the 128K ROM:
• The Binary-Decimal Conversion Package, for converting integers to decimal strings
and vice versa.
•The Floating-Point Arithmetic Package, which supports extended-precision arithmetic
according to IEEE Standard 7 54.
• The Transcendentµ.! Functions Package, which contains trigonometric, logarithmic,
exponential, and financial functions, as well as a random number generator.
For compatibility with the 64K ROM, the above resources are still stored in the system
resource file. The system resource file contains the following additional packages as well:
• The List Manager Package, for creating, displaying, and manipulating lists.
• The Standard File Package, for presenting the standard user interface when a file is to
be saved or opened.
• The Disk Initialization Package, for initializing and naming new disks.
•The International Utilities Package, for accessing country-dependent information such
as tbe formats for numbers, currency, dates, and times.
Packages have the resource type 'PACK' and the following resource IDs:
CONST listMgr
0;
dskinit -
2;
stdFile
3;
flPoint
4;
trFunct
5;
intUtil
6;
bdConv
7;
{List Manager}
{Disk Initialization}
{Standard File}
{Floating-Point Arithmetic}
{Transcendental Functions}
{International Utilities}
{Binary-Decimal Conversion}
The Package Manager has been extended to allow for eight additional packages. All
packages are reserved for use by Apple.
The Package Manager IV-67

<!-- source-page: 80 -->
## Page 80

Inside Macintosh
SUMMARY OF THE PACKAGE MANAGER
Constants
CONST { Resource IDs for packages }
listMgr
0;
{List Manager}
dskinit
2;
{Disk Initialization}
stdFile
3;
{Standard File}
flPoint
4;
{Floating-Point Arithmetic}
trFunct
5;
{Transcendental Functions}
intUtil
6;
{International Utilities}
bdConv
7;
{Binary-Decimal Conversion}
Assembly-Language Information
Constants
; Resource IDs for packages
listMgr
.EQU
0
dskinit
.EQU
2
stdFile
.EQU
3
flPoint
.EQU
4
trFunct
.EQU
5
intUtil
.EQU
6
bdConv
.EQU
7
Trap Macros for Packages
List Manager
Disk hritialization
Standard File
Floating-Point Arithmetic
Transcendental Functions
International Utilities
Binary-Decimal Conversion
;List Manager
;Disk Initialization
;Standard File
;Floating-Point Arithmetic
;Transcendental Functions
;International Utilities
;Binary-Decimal Conversion
_PackO
_Paclc2
_Pack3
_Pack4
_Pack5
_Pack6
_Pack?
(synonym: _FP68K)
(synonym: _Elems68K)
IV-68 Swnmary of the Package Manager

<!-- source-page: 81 -->
## Page 81

14 THE BINARY-DECIMAL CONVERSION PACKAGE
Three new routines have been added to the Binary-Decimal Conversion Package. These
routines supplement the Floating-Point Arithmetic and Transcendental Functions Packages
in providing the the Standard Apple Numeric Environment (SANE) for the Macintosh.
Detailed documentation for these new routines is included with the rest of the SANE
documentation in the Apple Numerics Manual-in particular, see the chapter
"Conversions" in Part I and the three chapters "Conversions", "Numeric Scanner and
Formatter", and "Examples" in Part III.
The new routines, two numeric scanners and a numeric formatter, are intended for
programmers with special needs beyond what their development language provides. For
example, developers of programming languages can use these routines to implement the
floating-point l/O routines-such as read and write for Pascal or scanf and printf for
C-that are appropriate for their particular languages. The scanners can be used for
scanning numbers embedded in text and for numbers received character by character. The
scanners differ only in that one accepts a pointer to a Pascal strings (with an initial length
byte) as input, while the other accepts a pointer to the first character of a character stream.
The sc~ers convert ASCII string representations of numbers into SANE decimal records.
The formatter converts SANE decimal records into ASCII string representations. The
Floating-Point Arithmetic Package converts between this decimal record format and the
SANE binary data formats.
The three routines handle the usual number representations, like -1.234 and 5e-7,
throughout the range and precision of the extended data format. They also handle the
special NaN, infinity, and signed-zero representations specified by the IEEE Floating-Point
Standard.
The Binary-Decimal Conversion Package IV-69

<!-- source-page: 82 -->
## Page 82

Inside Macintosh
IV-70

<!-- source-page: 83 -->
## Page 83

15 THE STANDARD FILE PACKAGE
The Standard File Package has been modified to work with the hierarchical file system.
(This chapter assumes some familiarity with the new material presented in chapter 19 of
this volume.) Since a volume's files are no longer necessarily contained in a single flat
directory, the Standard File Package must provide some way for the user to select a file
that's contained in a folder (or subdirectory). It must also provide the user with a way of
indicating the directory into which a particular file should be saved.
The dialog box displayed in response to the SFGetFile procedure shows the names of
folders (if any) as well as files. Files and folders are distinguished by miniature icons
preceding their names. Notice that there are two types of mini-icons for files-one for
applications and another for documents. Figure 1 shows the files and folders contained on
a sample desktop.
I c::> the disk I
Cl apps
D checklist
Clim
Cl romance
Cl serious things
O special
Cl status
Cl System Folder
Cl utilities
c::> the disk
(
E jec t
)
(
UrhlC~
)
(
Open ~)
(
Cancel
)
Figure 1. Open Dialog (at the Desktop Level)
To view the files and folders contained in a particular folder, the user must open the folder
by clicking it and then clicking the Open button, or by double-clicking on the folder name;
this causes the contents of the folder to be displayed. Figure 2 shows the contents of the
sample folder special.
The Standard File Package IV-71

<!-- source-page: 84 -->
## Page 84

Inside Macintosh
I a special I
CJ glossy
~
CJ leftouers
CJ threat
G=> the disk
(
)
(
)
(
Open ~ J
[
Cancel
J
Figure 2. Open Dialog (at a Folder Level)
A current directory button above the list shows the name of the directory whose files and
folders are displayed in the list below. If the contents of the desktop (or root directory) are
being displayed, the button will show the name of the volume next to either a 3 1/2-inch
disk mini-icon or a hard disk mini-icon (as in Figure 1). If the contents of a particular
folder (or subdirectory) are being displayed, the button will show the name of that folder
next to an open folder mini-icon (as in Figure 2 for instance).
Assembly-language note: The global variable SFSaveDisk always contains the
negative of the volume reference number (never a working directory reference
number) of the volume to use. If the hierarchical version of the File Manager is
running, the global variable CurDirStore contains the directory ID of whatever
directory (including the root) was last opened (regardless of whether a document was
actually opened or saved). With the 64K ROM version of the File Manager,
CurDirStore is not needed and is set to 0.
The current directory button provides a way of moving back up through the hierarchical
directory structure of a volume. If the user is at the level of a particular folder (or
subdirectory), clicking on the button causes a list to pop down. This list gives the path
from the current directory back up to the root directory. The rules for displaying and
selecting items from this "pop down" list are identical to those for items in a menu. To
change levels, select the desired folder and the files and folders at that level will be
displayed.
When the user chooses Save As, or Save when the document is untitled, the SFPutFile
dialog box contains a list of files and folders similar to the list displayed in response to the
Open command. This allows the user to specify the directory into which the file should be
placed. A current directory button above the list lets the user move about in the hierarchical
structure. File names in the list are dimmed (but displayed, so that the user can see what
other files are in the directory). Figure 3 shows an example.
IV-72 The Standard File Package

<!-- source-page: 85 -->
## Page 85

I~ the disk I
D opps
D < lu~ckH~t
Dim
D pn~f<H •~
D romance
D serious things
Soue document os:
glossy
The Standa,rd File Package
~the disk
(
E:j•~c1 J
(
Uril}<~ J
(
Saue ~)
( Cancel )
Figure 3. Save Dialog Box (at the Desktop Level)
In both dialog boxes, the Drive, Eject, and Open/Save buttons function as they always
have, although their positions have changed. The Save button is always dimmed if the
current volume is locked.
Note: No new buttons have been added, so programmers need not worry about
interference with controls they've added. The new dialog boxes, however, are larger
than the old boxes; the Standard File Package does its best to position nonstandard
dialogs in a visible and pleasing position. (Additional details are provided below in
the section "Creating Your Own Dialog Box".)
When the user dismisses the dialog, whether by Cancel or Save or Open, the directory
currently displayed is set to be the working directory (in other words, a call is made to the
File Manager function OpenWD).
USING THE STANDARD FILE PACKAGE
No new routines have been added to the Standard File Package. Applications that use the
Standard File Package properly need no modification to operate on machines equipped with
the 128K ROM. The specification of a directory in the SFGetFile and SFPutFile
procedures is transparent, due to the fact that working directory reference numbers can
always be used in place of volume reference numbers. (The relationship between volume
reference numbers and working directory reference numbers is described in detail in the
File Manager chapter.) If the user specifies that a given file be opened from or saved to a
particular subdirectory, the vRefNum field of the reply record you pass with these routines
will be filled with a working directory reference number instead of a volume reference
number.
Warning: Programmers who have written their own "standard file" routines or who
rely on SFReply.vRefNum being a volume reference number may find that their
applications are not compatible with the 128K ROM version of the File Manager.
Using the Standa,rd File Package IV-73

<!-- source-page: 86 -->
## Page 86

Inside Macintosh
Using the Keyboard
The Standard File Package lets you use a variety of keyboard keys to respond to its
dialogs. The following special keys (or key sequences) are defined:
Key Sequence
Up Arrow
Down Arrow
Command-Up Arrow
Command-Down Arrow
Command-Shift-1
Command-Shift-2
Tab
Return
Enter
Action
Scrolls up (backward) through displayed list
Scrolls down (forward) through displayed list
Closes the current directory
9}J~ns the selected directory
Ejects disk in internal drive
Ejects disk in external drive
Equivalent to Drive button
Equivalent to either Open or Save button
Same as Return
Note: The Up Arrow and Down Arrow keys are available on the standard
Macintosh Plus keyboard, and on the optional numeric keypad for the Macintosh
128K and 512K, as well as on the Macintosh XL keypad. (See chapter 1 of this
volume for details on using the arrow keys.) In addition, with the SFGetFile dialog
the user can type characters to locate files in the list; each time a character is typed,
the list selects and displays the first file whose initial character matches the typed
character.
CREATING YOUR OWN DIALOG BOX
This section is for advanced programmers who want to create their own dialog boxes rather
than use the standard SFPutFile and SFGetFile dialogs.
Warning: Future compatibility is not guaranteed if you don't use the standard
dialogs.
The addition of the file name list to the SFPutFile dialog, as well as the addition of current
directory buttons to both SFPutFile and SFGetFile, requires that the dialog boxes for each
call be made larg~r ~d the items in the box moved down. Although new dialog templates
and item lists are provided, the Standard File Package also needs an algorithm for
transforming old or nonstandard dialog templates and item lists.
To maintain compatibility with existing applications, the Standard File Package uses only
the existing dialog items. In SFPutFile, a userltem for the new file name list replaces the
dotted line in item number 8. In SFGetFile, the scroll bar userltem in item number 8 is no
lpnger used. For both SFPutFile and SFGetFile, the information for the current directory
button and the scroll bars is maintained internally.
The Standard File Package determines if a dialog needs to be transformed by looking at the
width of item number 8 (the dotted line or scroll bar) as specified in the item's rectangle. If
the width of item number 8 specifies either a dotted line (a width of 1) or a scroll bar (a
width of 16), the dialog will be transformed.
W-74 Creating Your Own Dialog Box

<!-- source-page: 87 -->
## Page 87

The Standard File Package
Note: ff a dialog needs to be transformed, the box is enlarged to make room for
both the scrolling list and the current directory button. All of the items are moved
down to their original position relative to the bottom of the box, and the scrolling list
and current directory button are added. The dialog is then centered on the screen. ff
it overlaps the menu bar, it's moved down. If it extends below or to the right of the
screen, it's repositioned to make the entire dialog visible. In the case of certain
unusual dialogs, the bottom of the dialog may not be visible.
To create nonstandard dialogs that will not be transformed (in other words, ones in which
you leave room for the list and current directory button), simply set item number 8 to the
desired size and location of your file name list, including scroll bars (for SFPutFile), and
set item number 8 to have a width other than 16 (for SFGetFile). The scroll bar is placed
within the specified file name list's rectangle.
The DlgHook Function
In the old Standard File Package, a dlgHook routine could not accurately monitor what file
was being opened, since it could not detect a double-click. In the new Standard File
Package, double-clicks on files are interpreted as clicks on the Open button (item
number 1), allowing the dlgHook to intercept ttles to be opeqed. With folders, however,
both clicks on the Open button and double-clicks are passed to the hook as "fake" item
number 103.
A new fake item number 102 is generated by a click in the current directory button; it
causes the ftle list to be pulled down and tracke4.
To redisplay the file list in GetFile (which you might do if your dialog box contains radio
buttons that let you choose different file types to be displayed), change item number 100 (a
null event) into item number 101 (which means redisplay the list) from within the dialog
hook.
Note: Disk-inserted events are handled internally; they are not (and never have
been) returned as "fake" item number 100. Item number 100 is returned only when
no event has taken place.
Before the dlgHook routine is called, information for the selected file or folder is stuffed in
the reply record (which can be examined on null events). ff no file or folder is selected,
fNatne and ffype are both NIL. ff a file is selected, fName will not be NIL and will
contain the file name. ff a folder is selected, ffype will not be NIL and will contain the
dirID. This is done before the dialog hook is called, regardless of which event is being
returned.
Creating Your Own Dialog Box IV-75

<!-- source-page: 88 -->
## Page 88

Inside Macintosh
Three of the new Standard File Package alerts display an OK button instead of a Cancel
button:
Alert
Disk not found
System error
Locked disk
Resource ID
-3994
-3995
-3997
Also, the text of the alert number-3994 (previously "Can't find that disk.") has been
changed to "Bad character in name, or can't find that disk." This reflects the fact that this
alert is generated if there's a colon in the name.
With nonhierarchical volumes, SFGetFile passes the fileFilter function the file information
it gets by calling the File Manager function GetFileinfo. With hierarchical volumes, it gets
this information from the GetCatlnfo function. SFPutFile does not support a fileFilter
function.
SUMMARY OF THE STANDARD FILE PACKAGE
Variables
CurDirStore
SFSaveDisk
Directory ID of directory last opened (long)
Negative of volume reference number (word)
IV-76 Summary of the Standard File Package

<!-- source-page: 89 -->
## Page 89

16 THE MEMORY MANAGER
Many existing Memory Manager routines have been improved; most of these improvements
are transparent to the programmer.
SetHandleSize is smarter about finding free space below, as well as above, the relocatable
block.
Routines have been provided for the setting and clearing of handle flags.
MEMORY MANAGER ROUTINES
Two Memory Manager routines-MaxApplZ.one and MoveHHi-that were not in the 64K
ROM (but were available in the Lisa Pascal interfaces) have been added to the 128K ROM.
Assembly-language note: The calling information for MaxApplZone and
MoveHHi is as follows:
Trap macro
On exit
Trap macro
On entry
On exit
_MaxApplZ.one
DO: result code (word)
_Movelllii
AO: h (handle)
DO: result code (word)
FUNCTION MaxBlock : LONGINT;
Trap macro
_MaxBlock
_MaxBlock ,SYS
(applies to system heap)
On exit
DO: function result (word)
MaxBlock returns the maximum contiguous space in bytes that could be obtained by
compacting the current zone (without actually doing the compaction).
Memory Manager Routines IV-77

<!-- source-page: 90 -->
## Page 90

Inside Macintosh
PROCEDURE PurgeSpace (VAR total,contig: LONGINT);
Trap macro
_PurgeSpace
_PurgeSpace ,SYS
(applies to system heap)
On exit
AO: contig (long word)
DO: total (long word)
PurgeSpace returns in total the total amount of space in bytes that could be obtained by a
general purge (without actually doing the purge); this amount includes space that is already
free. The maximum contiguous space in bytes (including already free space) that could be
obtained by a purge is returned in contig.
FUNCTION StackSpace : LONGINT;
Trap macro
On exit
_StackSpace
DO: function result (word)
StackSpace returns the current amount of stack space between the current stack pointer and
the application heap (at the instant of return from the trap).
Advanced Routine
FUNCTION NewEmptyHandle : Handle;
Trap macro
On exit
_New Empty Handle
_NewEmptyHandle ,SYS
AO: function result (handle)
DO: result code (word)
(applies to system heap)
NewEmptyHandle is similar in function to New Handle except that it does not allocate any
space; the handle returned is empty (in other words, it points to a NIL master pointer).
NewEmptyHandle is used extensively by the Resource Manager; you may not need to use
it.
Properties of Relocatable Blocks
The master pointer associated with each handle contains flags for use by the Memory
Manager. Routines are provided for setting and clearing each of these flags, as well as for
saving and restoring the entire byte.
IV-78 Memory Manager Routines

<!-- source-page: 91 -->
## Page 91

The Memory Manager
Warning: Failure to use these routines virtually guarantees incompatibility with
future versions of the Macintosh. You should not set and clear these flags directly.
The HLock and HUnlock procedures lock and unlock a given relocatable block by setting
and clearing the lock flag. The HPurge and HNoPurge mark a given relocatable block as
purgeable or unpurgeable by setting and clearing the purge flag.
A third flag, the resource flag, is used internally by the Resource Manager .. The HSetRBit
and HClrRBit procedures set and clear this flag.
The HSetState and HGetState routines let you save and restore the state of the flags byte.
PROCEDURE HSetRBit (h: Handle);
Trap macro
_HSetRBit
On entry
AO: h (handle)
On exit
DO: result code (word)
HSetRBit sets the resource flag of a relocatable block's master pointer.
PROCEDURE HClrRBit (h: Handle);
Trap macro
On entry
On exit
_HClrRBit
AO: h (handle)
DO: result code (word)
HClrRBit clears the resource flag of a relocatable block's master pointer.
FUNCTION HGetState (h: Handle) : SignedByte;
Trap macro
On entry
On exit
_HGetState
AO: h (handle)
DO: flags (byte)
HGetState returns the byte that contains the flags of the master pointer for the given handle;
it's used in conjunction with HSetState to save and restore the state of the flags contained in
this byte. You can save this byte, change the state of any of the flags (using the routines
described above), and then restore their original state by passing the byte back to the
HSetState procedure (described below).
Memory Manager Routines IV-79

<!-- source-page: 92 -->
## Page 92

Inside Macintosh
PROCEDURE HSetState (h: Handle; flags: SignedByte};
Trap macro
On entry
On exit
_HSetState
AO: h (handle)
DO: flags (byte)
DO: result code (word)
HSetState is used in conjunction with HGetState; it sets the byte that contains the flags of
the master pointer for the given handle to the byte specified by flags.
ERROR REPORTING
All Memory Manager routines (including the RecoverHandle function) return a result code
that you can examine by calling the MemError function.
Assembly-language note: The trap _RecoverHandle doesn't return a result code
in register DO. The result code of the most recent call, however, is always stored in
the global variable MemErr.
IV-80 E"or Reporting

<!-- source-page: 93 -->
## Page 93

The Memory Mana.ger
SUMMARY OF THE MEMORY MANAGER
Constants
CONST { Result codes }
memROZErr
=
-99;
Routines
FUNCTION
MaxBlock :
PROCEDURE PurgeSpace
FUNCTION
StackSpace
FUNCTION
NewEmptyHandle
PROCEDURE HSetRBit
PROCEDURE HClrRBit
FUNCTION
HGetState
PROCEDURE HSetState
{operation on a read-only zone}
LONGINT;
(VAR total,contig: LONGINT);
LONGINT;
Handle;
(h: Handle) ;
(h: Handle) ;
(h: Handle)
SignedByte;
(h: Handle; flags: SignedByte);
Assembly-Language Information
Constants
; Result codes
memROZErr
.EQU
-99
;operation on a read-only zone
Routines
Trap macro
_MaxApplZone
_MoveHHi
_Max.Block
_PurgeSpace
_StackSpace
_New Empty Handle
On entry
AO: h (handle)
On exit
DO: result code (word)
DO: result code (word)
DO: function result (word)
AO: contig (long)
DO: total (long)
DO: function result (word)
AO: function result (word)
Summary of the Memory Manager IV-81

<!-- source-page: 94 -->
## Page 94

Inside Macintosh
Trap macro
On entry
On exit
_HSetRBit
AO: h (handle)
DO: result code (word)
_HClrRBit
AO: h (handle)
DO: result code (word)
_HGetState
AO: h (handle)
DO: function result (byte)
_HSetState
AO: h (handle)
DO: result code (word)
DO: flags (byte)
Variables
MemErr
Current value of MemError (word)
IV-82 Summary of the Memory Manager

<!-- source-page: 95 -->
## Page 95

17 THE SEGMENT LOADER
Advanced programmers: The LoadSeg procedure has been modified to help reduce heap
fragmentation. If the code segment to be loaded is unlocked (that is, if it's not in memory
and its resLoeked attribute is clear, or if it is in memory and is unlocked), LoadSeg calls the
Memory Manager procedure MoveHHi to move the segment toward the top of the current
heap zone.
To maintain C01Dpatibility with the 64K ROM, your code segments should be locked in the
resource file. they will, however, be unlocked when they're unloaded and may float up in
the heap; subsequent loading may then cause heap fragmentation.
If your application will never run on a 64K ROM machine, all segments except the main
segment ('CODE' resource 1) can be unlocked in the resource file. Your application's
initialization routine must call the Memory Manager procedure MaxApplZ.One, however;
otherwise the heap zone will grow incrementally and calls to MoveHHi may leave your
segments scattered throughout the heap.
The Segment Loader W-83

<!-- source-page: 96 -->
## Page 96

18 THE OPERATING SYSTEM EVENT MANAGER
A new routine, PPostEvent, posts application-defined events into the event queue and
returns a pointer to the created queue element.
FUNCTION PPostEvent (eventCode: INTEGER; eventMsg: LONGINT; VAR qEl:
Trap macro
On entry
On exit
EvQEl) : OSErr);
_PPostEvent
AO: eventCode (word)
DO: eventMsg (long word)
AO: pointer to event queue entry
PPostEvent is identical to PostEvent except that it returns a pointer to the created queue
entry.
SUMMARY OF THE OPERATING SYSTEM EVENT MANAGER
Routines
FUNCTION PPostEvent (eventCode: INTEGER; eventMsg: LONGINT; VAR qEl:
EvQEl) : OSErr);
Assembly-Language Information
Routines
Trap macro
_PPostEvent
On entry
AO: eventCode (word)
DO: eventMsg Qong)
On exit
AO: ptr to event queue entry
The Operating System Event Manager IV-85

<!-- source-page: 97 -->
## Page 97

19
THE FILE MANAGER
89 About This Chapter
89 About the File Manager
89
Volumes and the File Directory
90
About Names
91
About Directories
92
About Volumes
93
About Files
96 Using the File Manager
96
Hierarchical Routines
98
Working Directories
99
Pathnames
100
Specifying Volumes, Directories, and Files
101
Indexing
101
Accessing Files
102
Accessing Volumes
103
Advanced Routines
104 Information Used by the Finder
104
Flat Volumes
105
Hierarchical Volumes
106 High-Level File Manager Routines
107
Accessing Volumes
109
Accessing Files
112
Creating and Deleting Files
113
Changing Information About Files
115 Low-Level File Manager Routines
116
Parameter Blocks
120
IOParam Variant (ParamBlockRec and HParamBlockRec)
122
FileParam Variant (ParamBlockRec and HParamBlockRec)
123
VolumeParam Variant (ParamBlockRec)
123
VolumeParam Variant (HParamBlockRec)
125
CinfoPBRec
127
CMovePBRec
127
WDPBRec
127
Routine Descriptions
128
Initializing the File I/O Queue
128
Accessing Volumes
135
Accessing Files
145
Creating and Deleting Files and Directories
148
Changing Information About Files and Directories
155
Hierarchical Directory Routines
158
Working Directory Routines
159 Data Organization on Volumes
160
Flat Directory Volumes
161
Volume Information
162
Volume Allocation Block Map
163
Flat File Directory
Contents IV-87

<!-- source-page: 98 -->
## Page 98

Inside Macintosh
164
Hierarchical Directory Volumes
166
Volume Information
167
Volume Bit Map
168
B*-Trees
170
Extents Tree File
171
Catalog Tree File
174 Data Structures in Memory
175
The File 1/0 Queue
176
Volume Control Blocks
178
File Control Blocks
181
The Drive Queue
182 Using an External File System
183 Summary of the File Manager
W-88 Contents

<!-- source-page: 99 -->
## Page 99

The File Manager
ABOUT THIS CHAPTER
This chapter describes the File Manager, the part of the Operating System that controls the
exchange of information between a Macintosh application and files. The File Manager
allows you to create and access any number of files containing whatever information you
choose.
The changes to the File Manager are so extensive that the chapter has been completely
rewritten. For most programmers, the changes are transparent and require no modification
of code. All operations on the 64K ROM version of the File Manager are supported.
ABOUT THE FILE MANAGER
The File Manager is the part of the Operating System that handles communication between
an application and files on block devices such as disk drives. (Block devices are discussed
in the Device Manager chapter.) Files are a principal means by which data is stored and
transmitted on the Macintosh. A tile is a named, ordered sequence of bytes. The File
Manager contains routines used to read from and write to files.
Volumes and the File Directory
A volume is a piece of storage medium, such as a disk, formatted to contain files. A
volume can be an entire disk or only part of a disk. A 3 1/2-inch Macintosh disk is one
volume. Specialized memory devices, such as hard disks and file servers, can contain
many volumes. The size of a volume also varies from one type of device to another.
Macintosh volumes are formatted into chunks known as logical blocks, each able to
contain up to 512 bytes. Files are stored in allocation blocks, which are multiples of
logical blocks.
Each volume has a file directory containing information about the files on the volume.
With small volumes (containing only a few dozen files), a "flat" file directory organized as
a simple, unsorted list of file names is sufficient. Volumes initialized by the 64K ROM
have such a flat file directory.
64K ROM note: The 128K ROM version of the File Manager supports all
operations on flat file directories.
With the introduction of larger storage devices (several megabytes per volume) containing a
large number of files (thousands per volume), the flat file directory proves inadequate,
since an exhaustive, linear search of all the files is so time-consuming. A major feature of
the 128K ROM version of the File Manager is the implementation of a hierarchical file
directory (sometimes referred to as the tile catalog), that significantly speeds up access to
large volumes.
The hierarchical file directory allows a volume to be divided into smaller units known as
directories. Directories can contain files as well as other directories. Directories
contained within directories are also known as subdirectories.
About the File Manager IV-89

<!-- source-page: 100 -->
## Page 100

Inside Macintosh
The hierarchical directory structure is equivalent to the user's perceived desktop hierarchy,
where folders contain files or additional folders. In the 64K ROM version of the File
Manager, however, this desktop hierarchy was essentially an illusion maintained
completely by the Finder (at considerable expense). The introduction of an actual
hierarchical directory containing subdirectories greatly enhances the performance of the
Finder by relieving it of this task.
Figure 1 illustrates these two ways of organizing the files on a volume.
flat file directory
hierarchical file directory
Figure 1. Flat and Hierarchical Directories
About Names
Volumes, directories, and files all have names. A volume name consists of any sequence
of 1to27 printing characters, excluding colons(:). File names and directory names consist
of any sequence of 1 to 31 printing characters, excluding colons. Y riu can use uppercase
and lowercase letters when naming things, but the File Manager ignores case when
comparing names (it doesn't ignore diacritical marks).
64K ROM note: The 64K ROM version of the File Manager allows file names of
up to 255 characters. File names should be constrained to 31 characters, however, to
maintain compatibility with the 128K ROM version of the File Manager. The 64K
ROM version of the File Manager also allows the specification of a version number
to distinguish between different files with the same name. Version numbers are
generally set to 0, though, because the Resource Manager, Segment Loader, and
Standard File Package won ?t operate on files with nonzero version numbers, and the
Finder ignores version numbers.
W-90 Abo'Ut the File Mano.ger

<!-- source-page: 101 -->
## Page 101

The File Manager
About Directories
A few terms are needed to describe the relationships between directories on a hierarchical
volume. Figure 2 shows what looks to be an upside-down tree; it's a sample hierarchical
volume.
root directory
w
MyDisl<
~
item F?:i
I ;s••ponb
Finder
System. ,;•mily
Template
dO
11
MecWrite
Empty Fa Ider
Letter3
Db
Dad
Geri
Figure 2. A Hierarchical Volume
All of the volume's files stem from the directory labeled My Disk; this is the root
directory and is none other than the volume itself. The name of the root directory of a
volume is the same as the volume name.
Note: The volume name, constrained to 27 characters, is the sole exception to the
rule that directory names can be up to 31 characters long.
Each directory, including the root directory, is a distinct, addressable entity. Each directory
has its own set of offspring (possibly an empty set), which is those files or directories
contained in it. For instance, the directory Letters has the files Dad and Geri as offspring,
while the root directory contains the file Mac Write and the directories System Folder and
Empty Folder. Borrowing a term from physics, the number of offspring is known as the
directory's valence; for instance, the valence of the directory Correspondence is 2.
Similarly, for a given file or directory, the directory immediately above it is known as its
parent. The root directory is the only directory that doesn't have a parent.
About the File Manager W-91

<!-- source-page: 102 -->
## Page 102

Inside Macintosh
When created, every directory is given a directory ID that's unique (and assigned
sequentially) for any given volume. The root directory always has a directory ID of 2. In
Figure 2, for instance, the directory Empty Folder has a directory ID of 26. The directory
ID of a given offspring's parent is known as its parent ID; for example, the parent ID of
the file Template is 21.
About Volumes
A volume can be mounted or unmounted. When a volume is mounted, the File Manager
reads descriptive information about the volume into memory. For each mounted volume,
part of this information is placed in a data structure known as a volume control block
(described in detail in the section "Data Structures in Memory").
Ejectable volumes (such as the 3 1/2-inch disks) are mounted when they're inserted into a
disk drive; nonejectable volumes (such as those on hard disks) are always mounted. Only
mounted volumes are known to the File Manager, and an application can access
information on mounted volumes only. When a volume is unmounted, the File Manager
releases the information stored in the volume control block.
A mounted volume can be on-line or off-line. A mounted volume is on-line as long as the
volume buffer and all the descriptive information read from the volume when it was
mounted remain in memory (about lK to 1.5K bytes); it becomes off-line when all but
the volume control block is released. You can access information on on-line volumes
immediately, but off-line volumes must be placed on-line before their information can be
accessed. When an application ejects a 3 1/2-inch disk from a drive, the File Manager
automatically places the volume off-line. Whenever the File Manager needs to access a
mounted volume that's been placed off-line and ejected, the dialog box shown in Figure 3
is displayed, and the File Manager waits until the user inserts the disk named volName into
a drive.
r···+
lgjlgj
Please insert the disk:
't. .... .:
uolName
Figure 3. Disk-Switch Dialog
Note: This dialog is actually a system error alert, as described in the System Error
Handler chapter.
Mounted volumes share a common set of volume buffers, which is temporary storage
space in the heap used when reading or writing information on the volume. The number of
volumes that may be mounted at any time is limited only by the number of drives attached
and available memory.
W-92 About the File Manager

<!-- source-page: 103 -->
## Page 103

The File Mana,ger
64K ROM note: In the 64K ROM version of the File Manager, each mounted
volume was assigned its own volume buffer.
To prevent unauthorized writing to a volume, volumes can be locked. Locking a volume
involves either setting a software flag on the volume or changing some part of the volume
physically (for example, sliding a tab from one position to another on a 3 1/2-inch disk).
Locking a volume ensures that none of the data on the volume can be changed.
Each volume has a name that you can use to identify it On-line volumes in disk drives can
also be accessed via the drive number of the drive on which the volume is mounted; the
internal drive is number 1, the external drive is number 2, and any additional drives
connected to the Macintosh will have larger numbers. In most routines, however, you '11
identify a volume by its volume reference number, which is assigned to a volume
when it's mounted. When accessing an on-line volume, you should always use the volume
reference number or the volume name rather than a drive number, because the volume may
have been ejected or placed off-line. Whenever possible, use the volume reference number
(to avoid confusion between volumes with the same name).
Note: In the case of specialized storage devices (such as hard disks) containing
several volumes, only the first on-line volume can be accessed using the drive
number of the device.
About Files
A file is a finite sequence of numbered bytes. Any byte or group of bytes in the sequence
can be accessed individually. A byte within a file is identified by its position within the
ordered sequence.
There are two parts, or forks, to a file: the data fork and the resource fork. Normally
the resource fork of an application file contains the resources used by the application, such
as menus, fonts, and icons, and also the application code itself. The data fork can contain
anything an application wants to store there. Information stored in resource forks should
always be accessed via the Resource Manager. Information in data forks can only be
accessed via the File Manager. For simplicity, "file" will be used instead of "data fork" in
this chapter.
The size of a file is limited only by the size of the volume it's on. Space is allocated to a
file in allocation blocks (multiples of 512 bytes). Two numbers are used to describe the
size of a file. The physical end-of-tile is the number of bytes currently allocated to the
file; it's 1 greater than the number of the last byte in its last allocation block (since the first
byte is byte number 0). The logical end-of-tile is the number of those allocated bytes
that currently contain data; it's 1 greater than the number of the last byte in the file that
contains data. For example, given an allocation block size of two logical blocks (that is,
1024 bytes), a file with 50 bytes of data has a logical end-of-file of 50 and a physical endof-file of 1024 (see Figure 4).
About the File Mana,ger IV-93

<!-- source-page: 104 -->
## Page 104

Inside Macintosh
logical
physical
end-of-file
end-of-file
If Ix Ix 1~1 x Ix Ix Ix 1~1 x Ix Ix 1~1~.....---1 .-.I"~:!
byte O
byte 50
byte 1024
Figure 4. Logical and Physical End-of-File
The File Manager maintains a current position marker, called the mark, to keep track of
where it is in the file during a read or write operation. The mark is the number of the next
byte that will be read or written; each time a byte is read or written, the mark is moved.
When, during a write operation, the mark reaches the number of the last byte currently
allocated to the file, another allocation block is added to the file.
You can read bytes from and write bytes to a file either singly or in sequences of unlimited
length. You can specify where each read or write operation should begin by setting the
mark; if you don't, the operation begins at the byte where the mark currently points. You
can find the current position of the mark by calling GetFPos. You can set the mark before
the read or write operation with SetFPos; you can also set it in the Read or Write call itself.
You can move the logical end-of-file to adjust the size of the file (such as after a resource
file has been compacted); when the logical end-of-file is moved to a position more than one
allocation block short of the current physical end-of-file, the unneeded allocation block will
be deleted from the file. You can also increase the size of a file by moving the logical-endfile past the physical end-of-file.
A file can be open or closed. An application can perform only certain operations, such as
reading and writing, on open files; other operations, such as deleting, can be performed
only on closed files.
Your application can lock a file to prevent unauthorized writing to it. Locking a file
ensures that none of the data in it can be changed; this is the same as the user-accessible
lock maintained by the Finder.
When a file is opened, the File Manager reads useful information about the file from its
volume and stores it in a data structure known as a file control block. The contents of
the file control block (described in detail in the section "Data Structures in Memory") are
used frequently and can be obtained with the function GetFilelnfo.
When a file is opened, the File Manager creates an access path, a description of the route
to be followed when accessing the file. The access path specifies the volume on which the
file is located and the location of the file on the volume. Every access path is assigned a
unique path reference number (a number greater than 0) that's used to refer to it. A file
can have multiple access paths open; each access path is separate from all other access paths
to the file.
IV-94 AbouJ the File Manager

<!-- source-page: 105 -->
## Page 105

The File Manager
Each file has open permission information, which indicates whether data can be written
to it or not. When you open a file, you request permission to read or write via an access
path. You can request permission to read only, write only (rarely done), or both read and
write. There are two types of read/write permission-exclusive and shared. Applications
will generally want to request exclusive read/write permission. If an access path requests
and is granted exclusive read/write permission, no other access path will be granted
permission to write (whether write only, exclusive read/write, or shared read/write).
A second type of read/write permission allows multiple access paths to be open for writing.
If you'll be using only a portion, or range, of a file, you can request shared read/write
permission. With shared read/write permission, the application must see to it that the file's
data integrity is preserved. Before writing to a particular range of bytes, you need to "lock"
it so that other access paths cannot write to that range at the same time. In the meantime,
other access paths opened with shared read/write access can lock and write to other parts of
the file.
The shared read/write permission has no utility on a single Macintosh; this permission is
intended for, and will be passed by, external file systems, where multiple read/write
operations are performed.
Note: If an access path is open with shared read/write permission, no access path
can be granted exclusive read/write access.
64K ROM note: Shared read/write permission is not implemented in the 64K
ROM version of the File Manager.
If the file's open permission doesn't allow I/O as requested, a result code indicating the
error is returned.
Each access path can move its own mark and read at the position it indicates. All access
paths to the same file share common logical and physical end-of-file markers.
When an application requests that data be read from a file, the File Manager reads the data
from the file and transfers it to the application's data buffer. Any part of the data that can
be transferred in entire 512-byte blocks is transferred directly. Any part of the data
composed of fewer than 512 bytes is also read from the file in one 512-byte block, but
placed in temporary storage space in memory. Then, only the bytes containing the
requested data are transferred to the application.
When an application writes data to a file, the File Manager transfers the data from the
application's data buffer and writes it to the file. Any part of the data that can be transferred
in entire 512-byte blocks is written directly. Any part of the data composed of fewer than
512 bytes is placed in temporary storage space in memory until 512 bytes have
accumulated; then the entire block is written all at once.
Note: Advanced programmers: The File Manager can also read a continuous stream
of characters or a line of characters. In the first case, you ask the File Manager to
read a specific number of bytes: When that many have been read or when the mark
has reached the logical end-of-file, the read operation terminates. In the second case,
called newline mode, the read will terminate when either of the above conditions is
met or when a specified character, the newline character, is read. The newline
character is usually Return (ASCII code $OD), but it can be any character.
Information about newline mode is associated with each access path to a file, and can
differ from one access path to another.
About the File Manager W-95

<!-- source-page: 106 -->
## Page 106

Inside Macintosh
Normally the temporary space in memory used for all reading and writing is the volume
buffer, but an application can specify that an access path buffer be used instead for a
particular access path (see Figure 5).
access path buffer
file "A"
appl icatioris
volume buffer
data buffer
file "B"
access path buffer
Figure 5. Buffers for-Transferring Data
Warning: You must lock any access path buffers of files in relocatable blocks, so
their location doesn't change while the file is open.
USING THE FILE MANAGER
This section outlines the routines provided by the File Manager and explains some basic
concepts needed to use them. The actual routines are presented later in the chapter.
The File Manager is automatically initialized each time the system starts up.
You can call most File Manager routines via three different methods: high-level Pascal
calls, low-level Pascal calls, and assembly language. The high-level Pascal calls are
designed for Pascal programmers interested in using the File Manager in a simple manner;
they provide adequate file I/O and don't require much special knowledge to use. The lowlevel Pascal and assembly-language calls are designed for advanced Pascal programmers
and assembly-language programmers interested in using the File Manager to its fullest
capacity; they require some special knowledge to be used most effectively.
Note: The names used to refer to File Manager routines in text (as opposed to in
particular routine descriptions) are actually the assembly-language macro names for
the low-level routines, but the Pascal routine names are very similar.
Hierarchical Routines
Many new routines are introduced in the hierarchical version of the File Manager; they can
be divided into two groups. These routines are used primarily by the File Manager itself.
W-96 Using the File Manager

<!-- source-page: 107 -->
## Page 107

The File Manager
Routines in the first group are slight extensions of certain basic File Manager routines that
allow the specification of a directory ID in addition to the other parameters; in certain cases
they set or obtain additional information. These specialized routines have the same names
as their general-purpose counterparts, but preceded by the letter "H". For instance, the
routine HOpen is identical to the Open call except that it allows the specification of a
directory ID. The routines in this first group are: HOpen, HOpenRF, HRename, HCreate,
HDelete, HGetFilelnfo, HSetFilelnfo, and HGetVlnfo. The calls in this group will work
with the 64K ROM version of the File Manager, but most applications will never need to
use them.
The second group of hierarchical routines consists of calls that perform operations unique
to the hierarchical file directory. The routines in this group are: SetVollnfo, LockRng,
UnlockRng, DirCreate, QetCatlnfo, SetCatlnfo, CatMove, OpenWD, CloseWD,
GetWDInfo, and GetFCBinfo.
Warning: Using any of the routines in this second group on a Macintosh equipped
only with th~ 64K ROM version of the File Manager will result in a system error.
Using them on a flat volume will have no effect on "folders" and will result in File
Manager errors.
In general, you will want your application to be independent of any particular version of the
File Manager. The benefits of the hierarchical file system are transparent to your
application and do not require use of the hierarchical routines. You may, however, want to
use the hierarchical routines under certain circumstances. One way of determining whether
the hierarchical version of the File Manager is present is to check which version of the
ROM is running by calling the Operating System Utilities procedure Environs.
RAM-based hierarchical versions of the File Manager may also be encountered, however; a
better way of determining which version of the File Manager is running is to examine the
contents of the global variable FSFCBLen. Located at address $3F6, this variable is a
word (two bytes) in length; it contains a positive value if the hierarchical version of the File
Manager is active or -1 if the 64K ROM version of the File Manager is running. You
could test the value of this global variable in the following way:
CONST FSFCBLen = $3F6; {address of global variable}
VAR HFS:
AINTEGER;
HFS := POINTER(FSFCBLen);
IF HFSA > 0
THEN
BEGIN
{we're running under the hierarchical version}
END;
ELSE
BEGIN
{we're running under the 64K ROM version}
END;
'
Even after determining that the hierarchical version is running, you'll still need to check that
a mounted volume is hierarchical by calling the HGetVInfo function.
Using the File Manager W-97

<!-- source-page: 108 -->
## Page 108

Inside Macintosh
As~embly .. Iang_uage note: You can tell whether a Macintosh is equipped with the
64K ROM version or the hierarchical version of the File Manager by examining the
contents of the global variable FSFCBLen; if the 64K ROM version is running,
FSFCBLen will contain -1. You can determine if a mounted volume is flat or
hierarchical by calling the HGetVInfo function.
Working Directories
It's useful to look at the relationship between the 64K ROM and 128K ROM versions of
the File Manager. In the 64K ROM version, the entire volume is a single directory (you
could consider it a barren.root directory). It would seem that existing applications, when
introduced on a machine equipped with the 128K ROM version of the File Manager,
would be unable to handle the specification of which directory a file is in, since they only
exchange volume reference numbers and file names with the Finder and the File Manager.
The 128K ROM version, however, introduces the notion of a working directory to
allow existing applications to operate with the hierarchical file system.
When the File Manager makes a particular directory a working directory (using the function
OpenWD), it stores the directory ID, as well as the volume reference number of the volume
on which the directory is located, in a wo~king directory control block. The File
Manager then returns a unique working directory reference number which you can
use in subsequent calls to refer to that directory.
Directories can be seen as mini-volumes. (The root directory is, in fact, just another minivolume; it contains only the files and directories immediately below it in the tree structure.)
A working directory reference number is just like a volume reference number for a
directory. It's a temporary reference number that specifies where a file is located on a
hierarchical volume.
This relationship allows the hierarchical file system to be compatible with existing
applications. A working directory reference number can be used in place of a volume
reference number in any File Manager call. When you provide a working directory
reference number, the File Manager uses it to determine which directory a file is in, as well
as which volume the directory and file are on.
An example of the use of working directories is a situation where the Finder opens a
document. With the 64K ROM version of the File Manager, when the Finder launches the
application that handles the document, it has only to pass tjle volume reference number and
file name of the document. With the 128K ROM version, the Finder makes the directory
containing the file a working directory, and passes the application a working directory
reference number instead of the volume reference number. Upon being launched, the
application opens the file, passing the File Manager the working directory reference number
received from the Finder.
Warning: The possibility of incompatibility arises for programmers who (despite
numeroµs warnings) have written code that accesses and manipulates low-level data
structures directly (such as volume control blocks and file control blocks).
Programmers in this category will want to study the sections "Data Organization on
Volumes" and "Data Structures in Memory".
IV-98 Using the File Manager

<!-- source-page: 109 -->
## Page 109

The File Manager
Pathnames
The 128K ROM version of the File Manager also permits the specification of files (and
directories) using concatenations of volume names, directory names, and file names.
Separated by colons, these concatenations of names are known as pathnames.
A full pathname always begins with the name of the root directory; it names the path
from the root to a given file or directory, and includes each of the directories visited on that
path (see Figure 2). For instance, a full pathname to the file Geri is:
MyDisk:Correspondence:Letters:Family:Geri
A full pathname is a complete and unambiguous identification of a file or directory. You
should avoid using full pathnames; they are cumbersome to enter and it takes longer to
process them.
Another type of identification is a partial pathname, which describes the path to a file or
directory starting from a given directory. When using a partial pathname, you must also
specify the directory from which the partial pathname begins; this is discussed below.
64K ROM note: In the 64K ROM version of the File Manager, the combination of
volume name followed by the file name constitutes a full pathname. A file name
alone constitutes a partial pathname; the directory from which this partial pathname
begins (the root directory) is specified by the volume reference number.
To distinguish them from full pathnames, partial pathnames must begin with a colon,
except in the case where the partial pathname contains only one name. (This exception is
needed to maintain compatibility with 64K ROM version of the File Manager, where the
only partial pathnames-file names-do not begin with a colon.) For the file Geri in
Figure 2, a valid partial pathname, starting from the directory Letters, would be:
:Family:Geri
The above pathname begins at the directory Letters and moves down the tree to the file
Status. It's also possible to move up the tree by using consecutive colons(::). This
notation indicates, for instance, that the name following a double colon is an offspring of
the current location's parent, rather than an offspring of the directory preceding the double
colon. In Figure 2, for example, the file Letter Form can be specified by the full pathname
MyDisk:Correspondence:Letters:Family:::Template
where the consecutive colons signify a move up the tree from Family to Letters and finally
to Correspondence.
If a full pathname consists of only one name (the volume name), the pathname must end in
a colon. For pathnames to other directories, if the last name is followed by a colon, the
colon is ignored. Multiname pathnames describing a file should not end in a colon.
To summarize, if the first character of a pathname is a colon, or if the pathname contains no
colons, it must be a partial pathname; otherwise, it's a full pathname.
Warning: While there's no limit to the number of levels of subdirectories allowed,
it may not always be possible in the case of a large volume to specify every file and
Using the File Manager IV-99

<!-- source-page: 110 -->
## Page 110

Inside Macintosh
directory with a full pathname, since character strings are limited to 255 characters.
In such cases, you can obtain the directory ID of a subdirectory somewhere along the
path and use it with a partial pathname to specify the desired file or directory.
Specifying Volumes, Directories, and Files
A volume can be specified explicitly by its name, its volume reference number, or its drive
number, and implicitly by a working directory reference number or a full pathname. The
File Manager searches for volume specifications in the following order:
1. It looks for a volume name. (Remember, it must be followed by a colon. )
2. If the name specified is NIL or an improper name, the File Manager looks for either a
volume reference number, a drive number, or a working directory reference number.
With routines that operate on a volume, such as mounting or ejecting, if you don't provide
any of these specifications, the File Manager assumes you want to perform the operation on
the default volume. Initially, the volume used to start up the application is set as the
default volume, but an application can designate any mounted volume as the default
volume.
With routines that access files (or directories), if no directory is specified and the volume
reference number passed is zero, the File Manager assumes that the file or directory is
located in the default directory. Initially, the default directory is set to the root directory
of the volume used to start up the application, but an application can designate any directory
as the default directory.
To access a file or directory, you need to specify its name, the directory it's in, and which
volume it's on. There are a number of ways of doing this:
• Full pathname. A full pathname completely specifies a file or directory. Since the first
name in a full pathname (the name of the root directory) is always the name of the
volume, no separate volume specification is needed. In fact, a full pathname will
override an explicit volume specification. (This specification runs the risk of
ambiguity since there could be two mounted volumes with the same name.)
• Volume reference number and partial pathname. This is the most common type of
specification, since it's the only form of specification in the 64K ROM version of the
File Manager. The volume reference number specifies the volume as well as the
directory (the root) to be used with the partial pathname (the file name).
• Directory ID and partial pathname. Another way to specify a file or directory is to use
the directory ID of any directory in the catalog along with a partial pathname from that
directory. Since neither the directory ID nor the partial pathname indicates the name of
the volume, a separate volume specification is also needed.
• Working directory reference number and partial pathname. This is the most common
type of specification in the 128K ROM version of the File Manager. It's similar to the
previous one; it does not, however, require a separate volume specification. The
working directory reference number is used to obtain both the directory ID (to be used
with the partial pathname) and the volume reference number.
W-100 Using the File Manager

<!-- source-page: 111 -->
## Page 111

The File Manager
If both a directory ID and a working directory reference number are specified, the directory
ID is used to identify the directory on the volume indicated by the working directory
reference number. In other words, a directory ID specified by the caller will override the
directory ref erred to by the working directory reference number.
Advanced programmers: If the File Manager doesn't find a given file in the directory
specified, it looks in the directory containing the currently open System file (obtained from
the global variable BootDrive ), provided it's on the volume specified by the call. If the file
isn't found there, the File Manager looks in the folder, on the volume specified by the call,
whose directory ID is returned in the vcbFndrlnfo field by the HGetVlnfo function.
Warning: It's important to be aware of this search path. You can't assume that a
given file is located in the directory that you specified when accessing it.
Indexing
In most of the File Manager routines, you '11 be referring to a particular file, directory, or
volume by its name or some sort of reference number. With a routine such as GetFilelnfo,
however, you may want to make the same call repeatedly for all files in a given directory
without specifying each file individually. Such routines provide a parameter where you can
simply specify an index number. In the first iteration of the GetFilelnfo function, for
example, you would pass an index of 1 and get information about the first file in a given
directory. In the second iteration you would pass an index of 2, and so on.
It's possible to determine how many files are contained in a given directory and thereby
specify the number of iterations for a GetFilelnfo indexing loop. The presence of
subdirectories, however, complicates the situation. A faster and more reliable technique is
to begin with an index of 1 and continue until the result code fnfErr (file not found) is
returned.
The routines that allow you to provide an index are: GetVollnfo, GetFilelnfo, GetCatlnfo,
GetWDInfo, and GetFCBinfo. Respectively, they provide information about mounted
volumes, files in a given directory, files and directories in a given directory, working
directories, and file control blocks.
On flat volumes, programmers can use the function GetFilelnfo to index through all the
files on a volume. On hierarchical volumes, files can be in subdirectories, which may
themselves contain other subdirectories and files. With such volumes, you should instead
use GetCatlnfo since it returns information about both files and directories.
Advanced programmers: While it's questionable whether an application would want to
index through all the files on a hierarchical volume (since such a volume may contain a
large number of files), you may want to index through a particular directory or portion of
the tree structure. You can use GetCatlnfo in a recursive way to do this. While indexing
through the initial directory, if a subdirectory is found, you need to interrupt the indexing
of the initial directory and index through the subdirectory.
Accessing Files
To create a new, empty file, call Create. Create allows you to set some of the information
stored on the volume about the file. DirCreate allows you to create directories.
Using the File Manager IV-101

<!-- source-page: 112 -->
## Page 112

Inside Macintosh
To open a file, call Open. The File Manager creates an access path and returns a path
reference number that you'll use every time you want to refer to it Before you open a file,
you may want to call the Standard File Package, which presents the standard interface
through which the user can specify the file to be opened. The Standard File Package will
return the name of the file, the volume reference number or working directory reference
number, and additional information. (ff the user inserts an unmounted volume into a drive,
the Standard File Package will automatically call the Disk Initialization Package to attempt
to mount it.)
After opening a file, you can transfer data from it to an application's data buffer with Read,
and send data from an application's data buffer to the file with Write. If you've opened a
file with shared read/write permission, you need to call LockRng before writing to it in
order to prevent another access path from writing to the same portion of the file. When
you're done writing, call UnlockRng to release that portion of the file.
You can't use Write on a file whose open permission only allows reading, or on a file on a
locked volume. In addition, you can't write to a range that's been locked by another access
path with the LockRng call.
You can specify the byte position of the mark before calling Read or Write by calling
SetFPos. GetFPos returns the byte position of the mark.
Once you've completed whatever reading and writing you want to do, call Close to close
the file. Close writes the contents of the file's access path buffer to the volume and deletes
the access path. You can remove a closed file (both forks) from a volume by calling
Delete.
Applications will normally use the Resource Manager to open resource forks and change
the information contained within, but programmers writing unusual applications (such as a
disk-copying utility) might want to use the File Manager to open resource forks. This is
done by calling OpenRF. As with Open, the File Manager creates an access path and
returns a path reference number that you'll use every time you want to refer to this resource
fork.
Accessing Volumes
When the Toolbox Event Manager function GetNextEvent receives a disk-inserted event, it
calls the Desk Manager function SystemEvent. SystemEvent calls the File Manager
function MountVol, which attempts to mount the volume on the disk. GetNextEvent then
returns the disk-inserted event: The low-order word of the event message contains the
number of the drive, and the high-order word contains the result code of the attempted
mounting. If the result code indicates that an error occurred, you '11 need to call the Disk
Initialization Package to allow the user to initialize or eject the volume.
Note: Applications that rely on the Operating System Event Manager function
GetOSEvent to learn about events (and don't call GetNextEvent) must explicitly call
Mount Vol to mount volumes.
After a volume has been mounted, your application can call GetVollnfo, which will return
the name of the volume, the amount of unused space on the volume, and a volume
reference number that you can use to refer to that volume. The volume reference number is
also returned by Mount Vol.
IV-102 Using the File Manager

<!-- source-page: 113 -->
## Page 113

The File Manager
To minimize the amount of memory used by mounted volumes, an application can unmount
or place off-line any volumes that aren't currently being used. To unmount a volume, call
Unmount Vol, which flushes a volume (by calling Flush Vol) and releases all of the memory
used for it. To place a volume off-line, call OffLine, which flushes a volume and releases
all of the memory used for it except for the volume control block. Off-line volumes are
placed on-line by the File Manager as needed, but your application must remount any
unmounted volumes it wants to access. The File Manager itself may place volumes off-line
during its normal operation.
To protect against power loss or unexpected disk ejection, you should periodically call
Flush Vol (probably after each time you close a file), which writes the contents of the
volume buffer and all access path buffers (if any) to the volume and updates the descriptive
information contained on the volume.
Whenever your application is finished with a disk, or when the user chooses Eject from a
menu, call Eject. Eject calls Flush Vol, places the volume off-line, and then physically
ejects the volume from its drive.
If you would like all File Manager calls to apply to one volume, you can specify that
volume as the default. You can use SetVol to set the default volume to any mounted
volume, and Get Vol to learn the name and volume reference number of the default volume.
The preceding paragraphs covered the basic File Manager routines. The remainder of this
section describes some less commonly used routines.
Advanced Routines
Normally, volume initialization and naming is handled by the Standard File Package, which
calls the Disk Initialization Package. If you want to initialize a volume explicitly or erase all
files from a volume, you can call the Disk Initialization Package directly. When you want
to change the name of a volume, call the File Manager function Rename.
Whenever a disk has been reconstructed in an attempt to salvage lost files (because its
directory or other file-access information.has been destroyed), the logical end-of-file of
each file will probably be equal to its physical end-of-file, regardless of where the actual
logical end-of-file is. The first time an application attempts to read from a file on a
reconstructed volume, it will blindly pass the correct logical end-of-file and read
misinformation until it reaches the new, incorrect logical end-of-file. To prevent this from
happening, an application should always maintain an independent record of the logical
end-of-file of each file it uses. To determine the File Manager's conception of the size of a
file, or to find out how many bytes have yet to be read from it, call GetEOF, which returns
the logical end-of-file. You can change the length of a file by calling SetEOF.
Allocation blocks are automatically added to and deleted from a file as necessary. If this
happens to a number of files alternately, each of the files will be contained in allocation
blocks scattered throughout the volume, which increases the time required to access
those files. To prevent such fragmentation of files, you can allocate a number of
contiguous allocation blocks to an open file by calling Allocate or AllocContig.
Using the File Manager N-103

<!-- source-page: 114 -->
## Page 114

Inside Macintosh
Instead of calling Flush Vol, an unusual application might call FlushFile. FlushFile forces
the contents of a file's volume buffer and access path buffer (if any) to be written to its
volume. FlushFile doesn't update the descriptive information contained on the volume, so
the volume information won't be correct until you call Flush Vol.
To get information about a file in a given directory (such as its name and creation date), call
GetFilelnfo; you can change this information by calling SetFilelnfo. On hierarchical
volumes, you can get information about both files and directories by calling GetCatinfo;
you can change this information with SetCatlnfo. Changing the name of a file is
accomplished by calling Rename. You can lock a file by calling SetFilLock; to unlock a
file, call RstFilLock. Given a path reference number, you can get the volume reference
number of the volume containing that file by calling either GetVRefNum or GetFCBinfo
(described in the section "Data Structures in Memory").
64K ROM note: You can change the version number of a file by calling
SetFilType.
To make a particular directory a working directory, call Open WD; you can remove a
working directory with CloseWD. To get information about a working directory (from its
working directory control block), call GetWDInfo.
INFORMATION USED BY THE FINDER
The file directory (whether hierarchical or flat) lists information about all the files and
directories on a volume. This information is returned by the GetFilelnf o and GetCatlnfo
functions.
Flat Volumes
On flat volumes, all of the information used by the Finder is contained in a data structure of
type Flnfo. (This data structure is also used with hierarchical volumes, along with
additional structures described below.) The Flnfo data type is defmed as follows:
TYPE Finfo = RECORD
fdType:
fdCreator:
fdFlags:
fdLocation:
fdFldr:
END;
OS Type;
OS Type;
INTEGER;
Point;
INTEGER
{file type}
{file's creator}
{flags}
{file's location}
{file's window}
Normally an application need only set the file type and creator when a file is created, and
the Finder will manipulate the other fields. (File type and creator are discussed in the
Finder Interface chapter.)
JV-104 Information Used by the Finder

<!-- source-page: 115 -->
## Page 115

The File Manager
FdFlags indicates whether the file's icon is invisible, whether the file has a bundle, and
other characteristics used internally by the Finder:
Bit
Meaning
0
Set if file is on desktop (hierarchical volumes only)
13
Set if file has a bundle
14
Set if file's icon is invisible
Masks for these three bits are available as predefined constants:
CONST fOnDesk
1;
{set if file is on desktop (hierarchical
{ volumes only) }
fHasBundle
finvisible
8192;
{set if file has a bundle}
16384; {set if file's icon is invisible}
For more information about bundles, see the Finder Interface chapter.
FdLocation contains the location of the file's icon in its window, given in the local
coordinate system of the window; it's used by the Finder to position the icon. FdFldr
indicates the window in which the file's icon will appear, and may contain one of the
following values:
CONST fTrash
fDesktop
fDisk
-3; {file is in Trash window}
-2; {file is on desktop}
0; {file is in disk window}
64K ROM note: The fdFldr field of Finfo is not used with hierarchical volumes.
Hierarchical Volumes
On hierarchical volumes, in add.ition to the Flnfo record, the following information about
files is maintained for the Finder:
TYPE FXInf o = RECORD
fdiconID:
fdUnused:
fdComment:
fdPutAway:
END;
INTEGER;
{icon ID}
ARRAY[l .. 4] OF INTEGER; {reserved}
INTEGER;
{comment ID}
LONGINT;
{home directory ID}
On hierarchical volumes, the following information about directories is maintained for the
Finder:
Dinfo = RECORD
frRect:
Rect;
frFlags:
INTEGER;
frLocation: Point;
frView:
INTEGER;
END;
{folder's rectangle}
{flags}
{folder's location}
{folder's view}
Information Used by the Finder IV-105

<!-- source-page: 116 -->
## Page 116

Inside Macintosh
DXInfo =RECORD
frScroll:
frOpenChain:
frUnused:
frComment:
frPutAway:
END;
Point;
LONGINT;
INTEGER;
INTEGER;
LONGINT;
{scroll position}
{directory ID chain of
{ open folders}
{reserved}
{comment ID}
{directory ID}
When a file (or folder) is moved to the desktop on a hierarchical volume, it's actually
moved to the root level of the file directory. (This permits all the desktop icons to be
enumerated by one simple scan of the root.) The fOnDesk bit of fdFlags is set.
FDPutA way (or frPutA way for directories) contains the directory ID of the folder that
originally contained the file (or folder); this allows the file (or folder) to be returned there
·from the desktop.
HIGH-LEVEL FILE MANAGER ROUTINES
This section describes all the high-level Pascal routines of the File Manager. For
information on calling the low-level Pascal and assembly-language routines, see the next
section.
When ~cessiilg a voiume other than the default volume, you must identify it by its volume
name, its volume reference number, the drive number of its drive, or a working directory
reference number. The parameter volName is a pointer, of type StringPtr, to the volume
name. DrvNum is an integer that contains the drive number, and vRefNum is an integer
that can contain either the volume reference number or a working directory reference
number.
Note: VolName is declared as type StringPtr instead of type STRING to allow you
to pass NIL in routines where the parameter is optional.
Warning: Before you pass a parameter of type StringPtr to a File Manager routine,
be sure that memory has been allocated for the variable. For example, the following
statements will ensure that memory is allocated for the variable myStr:
VAR myStr: Str255;
result := GetVol(@myStr,myRefNum)
FileName can contain either the file name alone or both the volume name and file name.
Note: The high-level File Manager routines will work only with files having a
version number of 0.
You can't specify an access path buffer when calling high-level Pascal routines.
All high-level File Manager routines return an integer result code of type OSErr as their
function result. Each routine description lists all of the applicable result codes, along with a
short description of what the result code means. Lengthier explanations of all the result
codes can be found in the summary at the end of this chapter.
IV-106 High-Level File Manager Routines

<!-- source-page: 117 -->
## Page 117

The File Manager
Accessing Volumes
FUNCTION GetVInfo (drvNum: INTEGER; volName: StringPtr; VAR
vRefNum: INTEGER; VAR freeBytes: LONGINT) : OSErr;
[Not
in ROM]
GetVInfo returns the name, reference number, and available space (in bytes), in volName,
vRefNum, and freeBytes, for the volume in the drive specified by drvNum.
Result codes
no Err
nsvErr
paramErr
No error
No default volume
Bad drive number
FUNCTION GetVRefNum (pathRefNum: INTEGER; VAR vRefNum: INTEGER) :
OSErr;
[Not in ROM]
Given a path reference number in pathRefNum, GetVRefNum returns the volume reference
number in vRefNum.
Result codes
ho Err
rfNumEtr
No error
Bad reference number
FUNCTION GetVol (volName: StringPtr; VAR vRefNum: INTEGER) : OSErr;
[Not in ROM]
Get Vol returns the name of the default volume in volName and its volume reference
number in vRefNum.
Result codes
no Err
nsvErr
No error
No such volume
FUNCTION SetVol (volName: StringPtr; vRefNum: INTEGER) : OSErr;
[Not in ROM]
Set Vol sets the default volume to the mounted volume specified by volName or vRefNum.
Result codes
no Err
bdNamErr
nsvErr
paramErr
No error
Bad volume name
No such volume
No default volume
High-Level File Manager Routines IV-107

<!-- source-page: 118 -->
## Page 118

Inside Macintosh
FUNCTION FlushVol (volName: StringPtr; vRefNum: INTEGER) : OSErr;
[Not in ROM]
On the volume specified by volName or vRefNum, Flush Vol writes the contents of the
associated volume buffer and descriptive information about the volume (if they've changed
since the last time Flush Vol was called).
Result codes
no Err
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
No error
Bad volume name
External file system
I/O error
No such drive
No such volume
No default volume
FUNCTION UnmountVol (volName: StringPtr; vRefNum: INTEGER) : OSErr;
[Not in ROM]
UnmountVol unmounts the volume specified by volName or vRefNum, by calling
Flush Vol to flush the volume buffer, closing all open files on the volume, and releasing the
memory used for the volume.
Warning: Don't unmount the startup volume.
Result codes
no Err
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
No error
Bad volume name
External file system
I/O error
No such drive
No such volume
No default volume
FUNCTION Eject (volName: StringPtr; vRefNum: INTEGER) : OSErr;
[Not in ROM]
Eject flushes the volume specified by volName or vRefNum, places it off-line, and then
ejects the volume.
Result codes
no Err
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
No error
Bad volume name
External file system
I/O error
No such drive
No such volume
No default volume
W-108 High-Level File Manager Routines

<!-- source-page: 119 -->
## Page 119

The File Manager
Accessing Files
FUNCTION FSOpen (fileName: Str255; vRefNum: INTEGER; VAR refNum:
INTEGER) : OSErr;
[Not in ROM]
FSOpen creates an access path to the file having the name fileName on the volume specified
by vRefNum. A path reference number is returned in refNum. The access path's
read/write permission is set to whatever the file's open permission allows.
Note: There's no guarantee that any bytes have been written until Flush Vol is
called.
Result codes
no Err
bdNamErr
extFSErr
fnfErr
ioErr
nsvErr
opWrErr
tmfoErr
No error
Bad file name
External file system
File not found
I/Oerror
No such volume
File already open for writing
Too many files open
FUNCTION OpenRF (fileName: Str255; vRefNum: INTEGER; VAR refNum:
INTEGER) : OSErr;
[Not in ROM]
OpenRF is similar to FSOpen; the only difference is that OpenRF opens the resource fork
of the specified file rather than the data fork. A path reference number is returned in
refNum. The access path's read/write permission is set to whatever the file's open
permission allows.
Note: Normally you should access a file's resource fork through the routines of the
Resource Manager rather than the File Manager. OpenRF doesn't read the resource
map into memory; it's really only useful for block-level operations such as copying
files.
Result codes
no Err
bdNamErr
extFSErr
fnfErr
ioErr
nsvErr
opWrErr
tmfoErr
No error
Bad file name
External file system
File not found
I/Oerror
No such volume
File already open for writing
Too many files open
FUNCTION FSRead (refNum: INTEGER; VAR count: LONGINT; buffPtr: Ptr}
: OSErr;
[NotinROM]
FSRead attempts to read the number of bytes specified by the count parameter from the
open file whose access path is specified by refNum, and transfer them to the data buffer
pointed to by buffPtr. The read operation begins at the current mark, so you might want to
High-Level File Manager Routines IV-109

<!-- source-page: 120 -->
## Page 120

Inside Macintosh
precede this with a call to SetFPos. If you try to read past the logical end-of-file, FSRead
moves the mark to the end-of-file and returns eofErr as its function result. After the read is
completed, the number of bytes actually read is returned in the count parameter.
Result codes
no Err
eofErr
extFSErr
fnOpnErr
ioErr
paramErr
rfNumErr
No error
End-of-file
External file system
File not open
1/0 error
Negative count
Bad reference number
FUNCTION FSWrite (refNum: INTEGER; VAR count: LONGINT; buffPtr:
Ptr) : OSErr;
[Not in ROM]
FSWrite takes the number of bytes specified by the count parameter from the buffer pointed
to by buffPtr and attempts to write them to the open file whose access path is specified by
refNum. The write operation begins at the current mark, so you might want to precede this
with a call to SetFPos. After the write is completed, the number of bytes actually written is
returned in the count parameter.
Result codes
no Err
dskFulErr
tLckdErr
fnOpnErr
ioErr
paramErr
rfNumErr
vLckdErr
wPrErr
wrPermErr
No error
Disk full
File locked
File not open
IJO error
Negative count
Bad reference number
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
FUNCTION GetFPos (refNum: INTEGER; VAR filePos: LONGINT)
: OSErr;
[Not in ROM]
GetFPos returns, in filePos, the mark of the open file whose access path is specified by
refNum.
Result codes
no Err
extFSErr
fnOpnErr
ioErr
rfNumErr
No error
External file system
File not open
IJO error
Bad reference number
FUNCTION SetFPos (refNum: INTEGER; posMode: INTEGER; posOff:
LONGINT)
: OSErr;
[NotinROM]
SetFPos sets the mark of the open file whose access path is specified by refNum to the
position specified by posMode and posOff (except when posMode is equal to fsAtMark, in
IV-110 High-Level File Manager Routines

<!-- source-page: 121 -->
## Page 121

The File Manager
which case posOff is ignored). PosMode indicates how to position the mark; it must
contain one of the following values:
CONST fsAtMark
0;
{at current mark}
fsFromStart
1;
{set mark relative to beginning of file}
fsFromLEOF
2;
{set mark relative to logical end-of-file}
fsFromMark
3;
{set mark relative to current mark}
If you specify fsAtMark, posOffset is ignored and the mark is left wherever it's currently
positioned. If you choose to set the mark (relative to either the beginning of the file, the
logical end-of-file, or the current mark), posOffset specifies the byte offset from the chosen
point (either positive or negative) where the mark should be set. If you try to set the mark
past the logical end-of-file, SetFPos moves the mark to the end-of-file and returns eofErr as
its function result.
Result codes
no Err
eofErr
extFSErr
fnOpnErr
ioErr
posErr
rfNumErr
No error
End-of-file
External file system
File not open
I/Oerror
Attempt to position before start of file
Bad reference number
FUNCTION GetEOF (refNum: INTEGER; VAR logEOF: LONGINT)
: OSErr;
[Not in ROM]
GetEOF returns, in logEOF, the logical end-of-file of the open file whose access path is
specified by refNum.
Result codes
no Err
extFSErr
fnOpnErr
ioErr
rfNumErr
No error
External file system
File not open
I/Oerror
Bad reference number
FUNCTION SetEOF (refNum: INTEGER; logEOF: LONGINT)
: OSErr;
[Not in
ROM]
SetEOF sets the logical end-of-file of the open file whose access path is specified by
refNum to the position specified by logEOF. If you attempt to set the logical end-of-file
beyond the physical end-of-file, the physical end-of-file is set to one byte beyond the end
of the next free allocation block; if there isn't enough space on the volume, no change is
made, and SetEOF returns dskFulErr as its function result. If logEOF is 0, all space
occupied by the file on the volume is released.
Result codes
noErr
dskFulErr
extFSErr
fLckdErr
fnOpnErr
ioErr
rfNumErr
No error
Disk full
External file system
File locked
File not open
I/Oerror
Bad reference number
High-Level File Manager Routines W-111

<!-- source-page: 122 -->
## Page 122

Inside Macintosh
vLckdErr
wPrErr
wrPennErr
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
FUNCTION Allocate (refNum: INTEGER; VAR count: LONGINT) : OSErr;
[Not in ROM]
Allocate adds the number of bytes specified by the count parameter to the open file whose
access path is specified by refNum, and sets the physical end-of-file to one byte beyond the
last block allocated. The number of bytes actually allocated is rounded up to the nearest
multiple of the allocation block size, and returned in the count parameter. If there isn't
enough empty space on the volume to satisfy the allocation request, Allocate allocates the
rest of the space on the volume and returns dskFulErr as its function result.
Result codes
noErr
dskFulErr
tLckdErr
fnOpnErr
ioErr
rfNumErr
vLckdErr
wPrErr
wrPennErr
No error
Disk full
File locked
File not open
l/O error
Bad reference number
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
FUNCTION FSClose (refNum: INTEGER) : OSErr;
[NotinROM]
FSClose removes the access path specified by refNum, writes the contents of the volume
buffer to the volume, and updates the file's entry in the file directory.
Note: There's no guarantee that any bytes have been written until Flush Vol is
called.
Result codes
noErr
extFSErr
fnfErr
fnOpnErr
ioErr
nsvErr
rfNumErr
Creating and Deleting Files
No error
External file system
File not found
File not open
l/O error
No such volume
Bad reference number
FUNCTION Create (fileName: Str255; vRefNum: INTEGER; creator:
OS Type; f ileType : OS Type) : OS Err;
[Not in ROM]
Create creates a new file (both forks) with the specified name, file type, and creator on the
specified volume. (File type and creator are discussed in the Finder Interface chapter.) The
new file is unlocked and empty. The date and time of its creation and last modification are
set to the current date and time.
W-112 High-Level File Manager Routines

<!-- source-page: 123 -->
## Page 123

Result codes
no Err
bdNamErr
dupFNErr
dirFulErr
extFSErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Bad file name
Duplicate file name and version
File directory full
External file system
1/0 error
No such volume
Software volume lock
Hardware volume lock
The File Maruzger
FUNCTION FSDelete (fileName: Str255; vRefNum: INTEGER)
: OSErr;
[Not in ROM]
FSDelete removes the closed file having the name fileName from the specified volume.
Note: This function will delete both forks of a file.
Result codes
noErr
bdNamErr
extFSErr
fBsyErr
fLckdErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Bad file name
External file system
File busy
File locked
File not found
l/Oerror
No such volume
Software volume lock
Hardware volume lock
Changing Information About Files
All of the routines described in this section affect both forks of the file, and don't require
the file to be open.
FUNCTION GetFinfo (fileName: Str255; vRefNum: INTEGER; VAR
fndrinfo: Finfo) : OS Err;
[Not in ROM]
For the file having the name fileName on the specified volume, GetFinfo returns
information used by the Finder in fndrlnfo (see the section "Information Used by the
Finder").
Result codes
no Err
bdNamErr
extFSErr
fnfErr
ioErr
nsvErr
paramErr
No error
Bad file name
External file system
File not found
l/Oerror
No such volume
No default volume
High-Level File MaruzgerRoutines IV-113

<!-- source-page: 124 -->
## Page 124

Inside Macintosh
FUNCTION SetFinfo (fileName: Str255; vRefNum: INTEGER; fndr!nfo:
Finfo) : OSErr;
[Not in ROM]
For the file having the name fileName on the specified volume, SetFInfo sets information
used by the Finder to fndrlnfo (see the section "Information Used by the Finder").
Result codes
no Err
extFSErr
fLckdErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
External file system
File locked
File not found
IJO error
No such volume
Software volume lock
Hardware volume lock
FUNCTION SetFLock (fileName: Str255; vRefNum: INTEGER)
: OSErr;
[Not in ROM]
SetFLock locks the file having the name fileName on the specified volume. Access paths
currently in use aren't affected.
Result codes
no Err
extFSErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
External file system
File not found
1/0 error
No such volume
Software volume lock
Hardware volume lock
FUNCTION RstFLock (fileName: Str255; vRefNum: INTEGER)
: OSErr;
[Not in ROM]
RstFLock unlocks the file having the name fileName on the specified volume. Access
paths currently in use aren't affected.
Result codes
no Err
extFSErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
External file system
File not found
IJO error
No such volume
Software volume lock
Hardware volume lock
FUNCTION Rename (oldName: Str255; vRefNum: INTEGER; newName:
Str255) : OSErr;
[NotinROM]
Given a file name in oldName, Rename changes the name of the file to newName. Access
paths currently in use aren't affected. Given a volume name in oldName or a volume
reference number in vRetNum, Rename changes the name of the specified volume to
new Name.
IV-114 High-Level File Manager Routines

<!-- source-page: 125 -->
## Page 125

The File Manager
Warning: If you 're renaming a volume, be sure that both names end with a colon.
Result codes
noErr
bdNamErr
dirFulErr
dupFNErr
extFSErr
tLckdErr
fnfErr
fsRnErr
ioErr
nsvErr
paramErr
vLckdErr
wPrErr
No error
Bad file name
Directory full
Duplicate file name
External file system
File locked
File not found
Problem during rename
IJO error
No such volume
No default volume
Software volume lock
Hardware volume lock
LOW-LEVEL f=ILE MANAGER ROUTINES
This section contains information for programmers using the low-level Pascal or assemblylanguage routines of the File Manager, and describes them in detail.
Most low-level File Manager routines can be executed either synchronously (meaning
that the application can't continue until the routine is completed) or asynchronously
(meaning that the application is free to perform other tasks while the routine is executing).
Some, however, can only be executed synchronously because they use the Memory
Manager to allocate and release memory.
When an application calls a File Manager routine asynchronously, an 1/0 request is
placed in the file 1/0 queue, and control returns to the calling program-possibly
even before the actual I/O is completed. Requests are taken from the queue one at a time,
and processed; meanwhile, the calling program is free to work on other things.
The calling program may specify a completion routine to be executed at the end of an
asynchronous pperation.
At any time, you can clear all queued File Manager calls except the current one by using the
InitQueue procedure. InitQueue is especially useful when an error occurs and you no
longer want queued calls to be executed.
Low-Level File Manager Routines IV-115

<!-- source-page: 126 -->
## Page 126

Inside Macintosh
Parameter Blocks
Routine parameters passed by an application to the File Manager and returned by the File
Manager to an application are contained in a parameter block, which is a data structure in
the heap or stack. When there are a number of parameters to be passed to, or returned
from, a routine, the parameters are grouped together in a block and a pointer to the block is
passed instead.
Most low-level calls to the File Manager are of the form
FUNCTION PBCallName (paramBlock: PtrToParamBlk; async: BOOLEAN)
OSErr;
PBCallName is the name of the routine. ParamBlock points to the parameter block
containing the parameters for the routine; its data type depends on the type of parameter
block. If async is TRUE, the call is executed asynchronously; otherwise the call is
executed synchronously. The routine returns an integer result code of type OSErr. Each
routine description lists all of the applicable result codes, along with a short description of
what the result code means. Lengthier explanations of all the result codes can be found in
the summary at the end of this chapter.
Assembly-language note: When you call a File Manager routine, AO must point
to a parameter block containing the parameters for the routine. If you want the
routine to be executed asynchronously, set bit 10 of the routine trap word. You can
do this by supplying the word ASYNC as the second argument to the routine macro.
For example:
_Read
'ASYNC
You can set or test bit 10 of a trap word by using the global constant asyncTrpBit.
(This syntax applies to the Lisa Workshop Assembler; programmers using another
development system should consult its documentation for the proper syntax.)
All File Manager routines except lnitQueue return a result code in DO.
There are many parameters used in the File Manager routines. To group them all together
in a single parameter block would be unmanageable, so several different parameter block
records have been defined. Figure 6 gives an overview of the various parameter blocks.
IV-116 Low-Level File Manager Routines

<!-- source-page: 127 -->
## Page 127

ParamBlkType =
(ioParam,fileParam,
volumeParam,cntrlParam);
ParmBlkPtr =
AParamBlockRec;
ParamBlockRec
RECORD
qLink:
QElemPtr;
qType:
INTEGER;
ioTrap:
INTEGER;
ioCmdAddr:
Ptr;
ioCompletion:
ProcPtr;
ioResult:
OSErr;
ioNamePtr:
StringPtr;
ioVRefNum:
INTEGER;
CASE ParamBlkType OF
ioParam:
(ioRefNum:
ioVersNum:
ioPermssn:
ioMisc:
ioBuffer:
ioReqCount:
ioActCount:
ioPosMode:
ioPosOffset:
fileParam:
(ioFRefNum:
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
ioFlVersNum:
ioFlFndrinfo:
ioFlNum:
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
volumeParam:
(filler2:
ioVolindex:
ioVCrDate:
ioVLsBkUp:
ioVAtrb:
ioVNmFls
ioVDirSt:
ioVBlLn:
ioVNmAlBlks:
ioVAlBlkSiz:
ioVClpSiz:
ioAlBlSt:
ioVNxtFNum:
ioVFrBlk:
cntrlParam:
INTEGER;
SignedByte;
SignedByte;
Ptr;
Ptr;
LONGINT;
LONGINT;
INTEGER;
LONGINT);
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
LONGINT);
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER);
{used by Device Manager}
END;
CMovePBPtr
CMovePBRec
qLink:
= ACMovePBRec;
RECORD
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
fillerl:
ioNewName:
filler2:
ioNewDirID:
fillerJ:
ioDirID:
END;
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
LONGINT;
StringPtr;
LONGINT;
LONGINT;
ARRAY (1. .2]
OF LONGINT;
LONGINT);
HParmBlkPtr =
AffParamBlockRec
HParamBlockRec
RECORD
qLink:
QElemPtr;
qType:
INTEGER;
ioTrap:
INTEGER;
ioCmdAddr:
Ptr;
ioCompletion:
ProcPtr;
ioResult:
OSErr;
ioNamePtr:
StringPtr;
ioVRefNum:
INTEGER;
CASE ParamBlkType OF
ioParam:
(ioRefNum:
ioVersNum:
ioPermssn:
ioMisc:
ioBuffer:
ioReqCount:
ioActCount:
ioPosMode:
ioPosOffset:
fileParam:
(ioFRefNum:
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
ioFlVersNum:
ioFlFndrinfo:
ioDirID:
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
volumeParam:
(filler2:
ioVolindex:
ioVCrDate:
ioVLsMod:
ioVAtrb:
ioVNmFls:
ioVBitMap:
ioAllocPtr:
ioVNmAlBlks:
ioVAlBlkSiz:
ioVClpSiz:
ioAlBlSt:
ioVNxtCNID:
ioVFrBlk:
ioVSigWord:
ioVDrvinfo:
ioVDRefNum:
ioVFSID:
ioVBkUp:
ioVSeqNum:
ioVWrCnt
ioVFilCnt:
ioVDirCnt:
ioVFndrinfo:
END;
INTEGER;
SignedByte;
SignedByte;
Ptr;
Ptr;
LONGINT;
LONGINT;
INTEGER;
LONGINT);
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
LONGINT);
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
ARRAY (1. .8]
OF LONGINT) ;
WDPBPtr = AWDPBRec;
WDPBRec
RECORD
qLink:
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
fillerl:
ioWDindex:
ioWDProcID:
ioWDVRefNum:
filler2:
ioWDDirID:
END;
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
INTEGER;
ARRAY[l.. 7]
OF INTEGER;
LONGINT);
The File Manager
CinfoType
Cinf oPBPtr
CinfoPBRec
= (hfileinfo,dirinfo);
= AcinfoPBRec;
= RECORD
qLink:
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
ioFRefNum:
ioFVersNum
fillerl:
ioFDirindex:
ioFlAttrib:
filler2:
OF
CASE CinfoType
hFileinfo:
(ioFlFndrinfo:
ioDirID:
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
ioFlBkDat:
ioFlXFndrinfo:
ioFlParID:
ioFlClpSiz:
dirinfo:
( ioDrUsrWds:
ioDrDirID:
ioDrNmFls:
filler3:
ioDrCrDat:
ioDrMdDat:
ioDrBkDat:
ioDrFndrinfo:
ioDrParID:
END;
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
LONGINT;
LONGINT;
Finfo;
LONGINT;
LONGINT);
ARRAY (1. .8]
OF INTEGER;
LONGINT;
INTEGER;
ARRAY (1. .9]
OF INTEGER;
LONGINT;
LONGINT;
LONGINT;
ARRAY (1. .8]
OF INTEGER;
LONGINT);
FCBPBPtr = AFCBPBRec
FCBPBRec = RECORD
qLink:
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
ioRefNum:
filler:
ioFCBindx:
ioFCBFlNm:
ioFCBFlags:
ioFCBStBlk:
ioFCBEOF:
ioFCBPLen:
ioFCBCrPs:
ioFCBVRefNum:
ioFCBClpSiz:
ioFCBParID:
END;
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
Figure 6. File Manager Parameter Block Records
Low-Level File Manager Routines IV-117

<!-- source-page: 128 -->
## Page 128

Inside Macintosh
ParamBlockRec is the record used by all routines in the 64K ROM version of the File
Manager; these routines include general 1/0 operations, as well as access to information
about files and volumes. The RAM-based version of the File Manager provides additional
calls that are slight extensions of certain basic routines, allowing you to take advantage of
the hierarchical file directory. For instance, HOpen is an extension of the Open call that lets
you use a directory ID and a pathname to specify the file to be opened. These hierarchical
routines use the record HParamBlockRec, which, as you can see from Figure 6, is a
superset of ParamBlockRec.
Assembly-language note: The hierarchical extensions of certain basic File
Manager routines are actually not new calls. For instance, _Open and _HOpen both
trap to the same routine. The trap word generated by the _HOpen macro is the same
as the trap word that would be generated by invoking the _Open macro with bit 9 set.
(Note that this is the same bit used in the Device Manager to indicate that a particular
call should be executed immediately.) The setting of this bit tells the File Manager to
expect a larger parameter block containing the additional fields (such as a directory
ID) needed to handle a hierarchical directory volume. You can set or test bit 9 of a
trap word by using the global contstant hfsBit.
Three parameter block records-CInfoPBRec, CMovePBRec, and WDPBRec-are used
by routines that deal specifically with the hierarchical file directory. These routines work
only with the 128K ROM version of the File Manager.
Finally, the record FCBPBRec is used by a single routine, PBGetFCBInfo, to gain access
to the contents of a file's file control block; this routine also works only with the 128K
ROM version of the File Manager.
Assembly-language note: You can invoke each of the routines that deal
specifically with the hierarchical file directory with a macro that has the same name as
the routine preceded by an underscore. These macros, however, aren't trap macros
themselves; instead they expand to invoke the trap macro _HFSDispatch. The File
Manager determines which routine to execute from the routine selector, an integer
that's placed in register DO. The routine selectors are as follows:
Routine
Call number
OpenWD
1
CloseWD
2
CatMove
5
DirCreate
6
GetWDInfo
7
GetFCBinfo
8
GetCatlnfo
9
SetCatlnfo
10
SetVollnfo
11
LockRng
16
U nlockRng
17
Warning: Using these routines on a Macintosh equipped only with the 64K ROM
will result in a system error.
W-118 Low-Level File Manager Routines

<!-- source-page: 129 -->
## Page 129

The File Manager
Three of the records-ParamBlockRec, HParamBlockRec, and CinfoPBRec-have CASE
statements that separate some of their parameters into functional subsections (also known
as variants of the record). The other records-CMovePBRec, WDPBRec, and
FCBPBRec-are not divided in this way.
All of the parameter block records used by the File Manager begin with eight fields of
standard information:
qLink:
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive number, }
{ or working directory reference number}
The first four fields in each parameter block are handled entirely by the File Manager, and
most programmers needn't be concerned with them; programmers who are interested in
them should see the section "Data Structures in Memory".
IOCompletion contains a pointer to a completion routine to be executed at the end of an
asynchronous call; it should be NIL for asynchronous calls with no completion routine,
and is automatically set to NIL for all synchronous calls.
Warning: Completion routines are executed at the interrupt level and must preserve
all registers other than AO, Al, and DO-D2. Your completion routine must not make
any calls to the Memory Manager, directly or indirectly, and can't depend on handles
to unlocked blocks being valid. If it uses application globals, it must also ensure that
register AS contains the address of the boundary between the application globals and
the application parameters; for details, see SetUpAS and RestoreAS in the Operating
System Utilities chapter.
When your completion routine is called, register AO points to the parameter block of the
asynchronous call and register DO contains the result code.
Routines that are executed asynchronously return control to the calling program with the
result code noErr as soon as the call is placed in the file I/O queue. This isn't an indication
of successful call completion, but simply indicates that the call was successfully queued.
To determine when the call is actually completed, you can poll the ioResult field; this field
is set to 1 when the call is made, and receives the actual result code upon completion of the
call. Completion routines are executed after the result code is placed in ioResult.
Low-Level File Manager Routines W-119

<!-- source-page: 130 -->
## Page 130

Inside Macintosh
IONamePtr points to a pathname (i.e. it does not itself contain the characters. It can be
either a full or partial pathname. In other words, it can be a volume name (that is, the name
of the root directory), a file name, or a concatenation of directory and file names. If
ioNamePtr is NIL or points to an improper pathname, an error is returned. For routines
that access directories, if a directory ID is specified, ioNamePtr can be NIL.
Note: Although ioNamePtr can be a full pathname, you should not require users to
enter full pathnames.
IOVRefNum contains either a volume reference number, a drive number, or a working
directory reference number.
The remainder of the parameters are presented below, organized by parameter block
records.
IOParam Variant (ParamBlockRec and HParamBlockRec)
The ioParam variants of ParamBlockRec and HParamBlockRec are identical; the fields are
presented below.
ioParam:
(ioRefNum:
ioVersNum:
ioPermssn:
ioMisc:
ioBuffer:
ioReqCount:
ioActCount:
ioPosMode:
ioPosOffset:
INTEGER;
SignedByte;
SignedByte;
Ptr;
Ptr;
LONGINT;
LONGINT;
INTEGER;
LONGINT);
{path reference number}
{version number}
{read/write permission}
{miscellaneous}
{data buffer}
{requested number of bytes}
{actual number of bytes}
{positioning mode and newline
{positioning offset}
character}
For routines that access open files, the File Manager determines which file to access by
using the path reference number in ioRefNum.
64K ROM note: The 64K ROM version of the File Manager also allows the
specification of a version number to distinguish between different files with the same
name. Version numbers are generally set to 0, though, because the Resource
Manager, Segment Loader, and Standard File Package won't operate on files with
nonzero version numbers, and the Finder ignores version numbers.
IOPermssn requests permission to read or write via an access path, and must contain one of
the following values:
CONST
fsCurPerm
fsRdPerm
fsWrPerm
fsRdWrPerm
fsRdWrShPerm =
0;
1;
2;
3;
4;
{whatever is currently allowed}
{request for read permission only}
{request for write permission}
{request for exclusive read/write }
{ permission}
{request for shared read/write permission}
W-120 Low-Level File Manager Routines

<!-- source-page: 131 -->
## Page 131

The File Manager
This request is compared with the open permission of the file. If the open permission
doesn't allow I/0 as requested, a result code indicating the error is returned.
Warning: To ensure data integrity be sure to lock the portion of the file you'll be
using if you specify shared write permission.
The content of ioMisc depends on the routine called. It contains either a new logical endof-file, a new version number, a pointer to an access path buffer, or a pointer to a new
pathname. Since ioMisc is of type Ptr, you'll need to perform type coercion to correctly
interpret the value of ioMisc when it contains an end-of-file (a LONGINT) or version
number (a SignedByte).
IOBuffer points to a data buffer into which data is written by Read calls and from which
data is read by Write calls. IOReqCount specifies the requested number of bytes to be
read, written, or allocated. IOActCount contains the number of bytes actually read,
written, or allocated.
IOPosMode and ioPosOffset specify the position of the mark for Read, Write, LockRng,
UnlockRng, and SetFPos calls. IOPosMode contains the positioning mode; bits 0 and 1
indicate how to position the mark, and you can use the following predefined constants to
set or test their value:
CONST fsAtMark
fsFromStart
fsFromLEOF
fsFromMark
0;
1;
2;
3;
{at current mark}
{set mark relative to beginning of file)
{set mark relative to logical end-of-file}
{set mark relative to current mark}
If you specify fsAtMark, ioPosOffset is ignored and the operation begins wherever the
mark is currently positioned. If you choose to set the mark (relative to either the beginning
of the file, the logical end-of-file, or the current mark), ioPosOffset must specify the byte
offset from the chosen point (either positive or negative) where the operation should begin.
Note: Advanced programmers: Bit 7 of ioPosMode is the newline flag; it's set if
read operations should terminate at a newline character. The ASCII code of the
newline character is specified in the high-order byte of ioPosMode. If the newline
flag is set, the data will be read one byte at a time until the newline character is
encountered, ioReqCount bytes have been read, or the end-of-file is reached. If the
newline flag is clear, the data will be read one byte at a time until ioReqCount bytes
have been read or the end-of-file is reached.
To have the File Manager verify that all data written to a volume exactly matches the data in
memory, make a Read call right after the Write call. The parameters for a read-verify
operation are the same as for a standard Read call, except that the following constant must
be added to the positioning mode:
CONST
rdVerify = 64;
{read-verify mode}
The result code ioErr is returned if any of the data doesn't match.
Low-Level File Manager Routines W-121

<!-- source-page: 132 -->
## Page 132

Inside Macintosh
FileParam Variant ( ParamBlockRec and HParamBlockRec)
The fileParam variants of ParamBlockRec and HParamBlockRec are identical, with one
exception: The field ioDirID in HParamBlockRec 1.s called ioFlNum in ParamBlockRec.
The fields of the fileParam variant of HParamBlockRec are as follows:
fileParam:
(ioFRefNumi
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
ioFlVers:Num:
ioFlFndrinfo:
ioDirID:
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
LONGINT);
{path reference number}
{version number}
{not used}
{index}
{file attributes}
{version number}
{information used by the Finder}
{directory ID or file number}
{first allocation block of data fork}
{logical end-of-file of data fork}
{physical end-of-file of data fork}
{first allocation block of resource fork}
{logical end-of-file of resource fork}
{physical end-of-file of resource fork}
{date apd time of creation}
{date and time of last modification}
IOFDirlndex can be used with the PBGetFInfo and PBHGetFInfo to index through the
files in a given directory.
Warning: When used with GetFilelnfo, ioFDirlndex will index only the files in a
directory. To index both files and directories, you can use ioFDirlndex with
PBGetCatInfo.
IOFlAttrib contains the following file attributes:
Bit
Meaning
0
Set if file is locked
2
Set if resource fork is open
3
Set if data fork is open
4
Set if a directory
7
Set if file (either fork) is open
When passed to a routine, ioDirID contains a directory ID; it can be used to refer to a
directory or, in conjuction with a partial pathname from that directory, to other files and
directories. If both a directory ID and a working directory reference number are provided,
the directory ID is used to identify the directory on the volume indicated by the working
directory reference number. In other words, a directory ID specified by the caller will
override the working directory referred to by the working directory reference number. If
you don't want this to happen, you can set ioDirID to 0. (If no directory is specified
through a working directory reference number, the root directory ID will be used.)
When returned from a routine, ioDirID contains the file number of a file; most
programmers needn't be concerned with file numbers, but those interested can read the
sectioll "Data Organization on Volumes".
IV-122 Low-Level File Manager Routines

<!-- source-page: 133 -->
## Page 133

The File Manager
IOFlStBlk and ioFlRStBlk contain 0 if the file's data or resource fork is empty,
respectively; they're used only with flat volumes. The date and time in the ioFlCrDat and
ioFlMdDat fields are specified in seconds since midnight, January 1, 1904.
VolumeParam Variant {ParamBlockRec)
When you call GetVollnfo, you '11 use the volumeParam variant of ParamBlockRec:
volumeParam:
(filler2:
ioVolindex:
ioVCrDate:
ioVLsBkUp:
ioVAtrb:
ioVNmFls:
ioVDirSt:
ioVBlLn:
ioVNmAlBlks:
ioVAlBlkSiz:
ioVClpSiz:
ioAlBlSt:
ioVNxtFNum:
ioVFrBlk:
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER);
{not used}
{index}
{date and time of initialization}
{~ate and time of last modification}
{volume attributes}
{number of files in root directory}
{first block of directory}
{length of directory in blocks}
{number of allocation blocks}
{size of allocation blocks}
{number of bytes to allocate}
{first block in volume block map}
{next unused file number}
{number of unused allocation blocks}
IOVollndex can be used to index through all the mounted volumes; using an index of 1
accesses the first volume mounted, and so on. (For more information on indexing, see the
section "Indexip.g" above.)
IOVLsBkUp contains the date and time the volume infoimation was last modified (this is
not necessarily when it was flushed). (This field is not modified when information is
written to a file.)
Note: The name ioVLsBkUp is actually a misnomer; this field has always contained
the date and time of the last modification to the volume, not the last backup.
Most programmers needn't be concerned with the remaining parameters, but interested
programmers can read the section "Data Organization on Volumes".
VolumeParam Variant {HParamBlockRec)
When you call HGetVInfo and SetVollnfo, you'll use the volumeParam variant of
HParamBlockRec. This is a superset of the volumeParam variant of ParamBlockRec; the
names and functions of certain fields have been changed, and new fields have been added:
volumeParam:
(filler2:
ioVolindex:
ioVCrDate:
ioVLsMod:
ioVAtrb:
ioVNmFls:
ioVBitMap:
ioAllocPtr:
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
{not used}
{index}
{date and time of initialization}
{date and time of last modification}
{volume attributes}
{number of files in root directory}
{first block of volume bit map}
{block at which next new file starts}
Low-Level File Manager Routines IV-123

<!-- source-page: 134 -->
## Page 134

Inside Macintosh
ioVNmAlBlks:
ioVAlBlkSiz:
ioVClpSiz:
ioAlBlSt:
ioVNxtCNID:
ioVFrBlk:
ioVSigWord:
ioVDrvinfo:
ioVDRefNum:
ioVFSID:
ioVBkUp:
ioVSeqNum:
ioVWrCnt
ioVFilCnt:
ioVDirCnt:
ioVFndrinfo:
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
ARRAY [1.. 8]
{number of allocation blocks}
{size of allocation blocks}
{number of bytes to allocate}
{first block in volume block map}
{next unused file number}
{number of unused allocation blocks}
{volume signature}
{drive number}
{driver reference number}
{file system handling this volume}
{date and time of last backup}
{used internally}
{volume write count}
{number of files on volume}
{number of directories on volume}
OF LONGINT); {information used by the }
{ Finder}
IOVollndex can be used to index through all the mounted volumes; using an index of 1
accesses the first volume mounted, and so on. (For more information on indexing, see the
section "Indexing" above.)
IOVLsMod contains the date and time the volume information was last modified (this is not
necessarily when it was flushed). (This field is not modified when information is written
to a file.)
Note: IOVLsMod replaces the field ioVLsBkUp in ParamBlockRec. The name
ioVLsBkUp was actually a misnomer; this field has always contained the date and
time of the last modification, not the last backup. Another field, io VBkUp, contains
the date and time of the last backup.
IOVClpSiz can be used to set the volume clump size in bytes; it's used for files that don't
have a clump size defined as part of their file information in the catalog. To promote file
contiguity and avoid fragmentation, space is allocated to a file not in allocation blocks but in
clumps. A clump is a group of contiguous allocation blocks. The clump size is always a
multiple of the allocation block size; it's the minimum number of bytes to allocate each time
the Allocate function is called or the end-of-file is reached during the Write routine.
IOVSigWord contains a signature word identifying the type of volume; it's $D2D7 for flat
directory volumes and $4244 for hierarchical directory volumes. The drive number of the
drive containing the volume is returned in ioDrvlnfo. For on-line volumes, ioVDRefNum
returns the reference number of the 1/0 driver for the drive identified by ioDrvlnfo.
IOVFSID is the file-system identifier. It indicates which file system is servicing the
volume; it's 0 for File Manager volumes and nonzero for volumes handled by an external
file system.
IOVBkUp specifies the date and time the volume was last backed up (it's 0 if never
backed up).
IOVNmFls contains the number of fUes in the root directory. IOVFilCnt contains the total
number of files on the volume, while io VDirCnt contains the total number of directories
(not including the root directory).
IV-124 Low-Level File Manager Routines

<!-- source-page: 135 -->
## Page 135

The File Manager
Most programmers needn't be concerned with the other parameters, but interested
programmers can read the section "Data Organization on Volumes".
CInfoPBRec
The routines GetCatlnfo and SetCatlnfo are used for getting and setting information about
the files and directories within a directory. With files, you'll use the following 19
additional fields after the standard eight fields in the parameter block record CInfoPBRec:
ioFRefNum:
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
filler2:
hFileinfo:
(ioFlFndrinfo:
ioDirID:
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
ioFlBkDat:
ioFlXFndrinfo:
ioFlParID:
ioFlClpSiz:
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
LONGINT;
LONGINT;
FXInfo;
LONGINT;
LONGINT);
{path reference number}
{version number}
{not used}
{index}
{file attributes}
{not used}
{information used by the Finder}
{directory ID or file number}
{first allocation block of data fork}
{logical end-of-file of data fork}
{physical end-of-file of data fork}
{first allocation block of resource }
{ fork}
{logical end-of-file of resource fork}
{physical end-of-file of resource fork}
{date and time of creation}
{date and time of last modification}
{date and time of last backup}
{additional information used by the }
{ Finder}
{file's parent directory ID (integer)}
{file's clump size}
IOFDirlndex can be used with the function PBGetCatInfo to index through the files and
directories in a given directory. For each iteration of the function, you can determine
whether it's a file or a directory by testing bit 4 (the fifth least significant bit) of ioFlAttrib.
You can test for a directory by using the Toolbox Utilities BitTst function in the following
manner (remember, the Toolbox Utilities routines reverse the standard 68000 notation):
BitTst(@myCinfoRec.ioFlAttrib,3)
IOFlAttrib contains the following attributes:
Bit
Meaning
0
Set if file is locked
2
Set if resource fork is open
3
Set if data fork is open
4
Set if a directory
7
Set if file (either fork) is open
When passed to a routine, ioDirID contains a directory ID; it can be used to refer to a
directory or, in conjuction with a partial pathname from that directory, to other files and
directories. If both a directory ID and a working directory reference number are provided,
Low-Level File Manager Routines W-125

<!-- source-page: 136 -->
## Page 136

Inside Macintosh
the directory ID is used to identify the directory on the volume indicated by the working
directory reference number. In other words, a directory ID specified by the caller will
override the working directory referred to by the working directory reference number. If
you don't want this to happen, you can set ioDirID to 0. (If no directory is specified
through a working directory reference number, the root directory ID will be used)
Warning: With files, ioDirID returns the file number of the file; when indexing
with GetCatlnfo, you '11 need to reset this field for each iteration.
IOFlStBlk and ioARStBlk contain 0 if the file's data or resource fork is empty,
respectively; they're used only with flat volumes. The date and time in the ioFlCrDat,
ioFlMdDat, and ioFlBkDat fields are specified in seconds since midnight, January 1, 1904.
IOFlParID contains the directory ID of the file's parent. IOFlClpSiz is the clump size to be
used when writing the file; if it's 0, the volume's clump size is used when the file is
opened.
With directories, you'll use the following 14 additional fields after the standard eight fields
in the parameter block record CinfoPBRec:
ioFRefNum:
ioFVersNum
fillerl:
ioFDirindex:
ioFlAttrib:
filler2:
dirinfo:
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
(ioDrUsrWds:
Dinfo;
ioDrDirID:
LONGINT;
ioDrNmFls:
INTEGER;
filler3:
ARRAY[l .. 9]
ioDrCrDat:
LONG INT;
ioDrMdDat:
LONG INT;
ioDrBkDat:
LONG INT;
ioDrFndrinfo: DXInfo;
ioDrParID:
LONGINT);
{file reference number}
{version number}
{not used}
{index}
{file attributes}
{not used}
{information used by the Finder}
{directory ID}
{number of files in directory}
OF INTEGER; {not used}
{date and time of creation}
{date and time of last modification}
{date and time of last backup}
{additional information used by the
{ Finder}
{directory's parent directory ID }
{ (integer) }
IOFDirindex can be used with the function PBGetCatInfo to index through the files and
directories in a given directory. For each iteration of the function, you can determine
whether it's a file or a directory by testing bit 4 of ioFlAttrib.
When passed to a routine, ioDrDirID contains a directory ID; it can be used to refer to a
directory or, in conjuction with a partial pathname from that directory, to other files and
directories. If both a directory ID and a working directory reference number are provided,
the directory ID is used to identify the directory on the volume indicated by the working
directory reference number. In other words, a directory ID specified by the caller will
override the working directory referred to by the working directory reference number. If
you don't want this to happen, you can set ioDirID to 0. (If no directory is specified
through a working directory reference number, the root directory ID will be used)
With directories, ioDrDirID returns the directory ID of the directory.
IV-126 Low-Level File Manager Routines

<!-- source-page: 137 -->
## Page 137

The File Manager
IODrNmFls is the number of files and directories contained in this directory (the valence of
the directory).
The date and time in the ioDrCrDat, ioDrMdDat, and ioDrBkDat fields are specified in
seconds since midnight, January 1, 1904.
IODrParID contains the directory ID of the directory's parent.
CMovePBRec
When you call CatMove to move files or directories into a different directory, you'll use the
following six additional fields after the standard eight fields in the parameter block record
CMovePBRec:
fillerl:
LONGINT;
{not used}
ioNewName:
StringPtr; {name of new directory}
filler2:
LONGINT;
{not used}
ioNewDirID:
LONGINT;
{directory ID of new directory}
filler3:
ARRAY[l .. 2] OF LONGINT; {not used}
ioDirID:
LONGINT);
{directory ID of current directory}
IONewName and ioNewDirID specify the name and directory ID of the directory to which
the file or directory is to be moved. IODirID (used in conjuntion with the ioVRefNum and
ioNamePtr) specifies the current directory ID of the file or directory to be moved.
WDPBRec
When you call the routines that open, close, and get information about working directories,
you'll use the following six additional fields after the standard eight fields in the parameter
block record WDPBRec:
fillerl:
INTEGER;
{not used}
ioWDindex:
INTEGER;
{index}
ioWDProcID:
LONGINT;
{working directory user identifier}
ioWDVRefNum: INTEGER;
{working directory's volume reference number}
filler2:
ARRAY [l .. 7] OF INTEGER;
{not used}
ioWDDirID:
LONG INT);
{working directory's directory ID}
IOWDindex can be used with the function PBGetWDInfo to index through the current
working directories.
IOWDProcID is an identifier that's used to distinguish between working directories set up
by different users; you should use the application's signature (discussed in the Finder
Interface chapter) as the ioWDProcID.
Routine Descriptions
Each routine description includes the low-level Pascal form of the call and the routine's
assembly-language macro. A list of the parameter block fields used by the call is also
given.
Low-Level File Manager Routines W-127

<!-- source-page: 138 -->
## Page 138

Inside Macintosh
Assembly-language note: The field names given in these descriptions are those
found in the Pascal parameter block records; see the summary at the end of this
chapter for the names of the corresponding assembly-language offsets. (The names
for some offsets differ from their Pascal equivalents, and in certain cases more than
one name for the same offset is provided.)
The number next to each parameter name indicates the byte offset of the parameter from the
start of the parameter block pointed to by register AO; only assembly-language
programmers need be concerned with it. An arrow next to each parameter name indicates
whether it's an input, output, or input/output parameter:
Arrow
Meaning
->
<-
< - >
Parameter is passed to the routine
Parameter is returned by the routine
Parameter is passed to and returned by the routine
Warning: You must pass something (even if it's NIL) for each of the parameters
shown for a particular routine; if you don't, the File Manager may use garbage that's
sitting at a particular off set.
Initializing the File 1/0 Queue
PROCEDURE FinitQueue;
Trap macro
_InitQueue
FInitQueue clears all queued File Manager calls except the current one.
Accessing Volumes
To get the volume reference number of a volume, given the path reference number of a file
on that volume, both Pascal and assembly-language programmers can call the high-level
File Manager function GetVRetNum. Assembly-language programmers may prefer calling
the function GetFCBinfo (described below in the section "Data Structures in Memory").
FUNCTION PBMountVol (paramBlock: ParmBlkPtr) : OSErr;
Trap macro
_Mount Vol
Parameter block
<-
16
<->
22
ioResult
ioVRetNum
word
word
PBMountVol mounts the volume in the drive specified by ioVRetNum, and returns a
volume reference number in io VRetNum. If there are no volumes already mounted, this
volume becomes the default volume. PBMountVol is always executed synchronously.
W-128 Low-Level File Manager Routines

<!-- source-page: 139 -->
## Page 139

The File Mana,ger
Note: When mounting hierarchical volumes, PBMountVol opens two files needed
for maintaining file directory and file mapping information. PBMountVol can fail if
there are no access paths available for these two files; it will return tmfoErr as its
function result.
Result codes
no Err
badMDBErr
extFSErr
ioErr
memFullErr
noMacDskErr
nsDrvErr
paramErr
tmfoErr
volOnLinErr
No error
Bad master directory block
External file system
I/0 error
Not enough room in heap zone
Not a Macintosh disk
No such drive
Bad drive number
Too many files open
Volume already on-line
FUNCTION PBGetVInfo (paramBlock: ParmBlkPtr; async: BOOLEAN}
OSErr;
Trap macro
_GetVolInfo
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
->
28
ioVollndex
word
<-
30
ioVCrDate
longword
<-
34
ioVLsBkUp
longword
<-
38
ioVAtrb
word
<-
40
ioVNmFls
word
<-
42
ioVDirSt
word
<-
44
ioVBlLn
word
<-
46
io VNmAlBlks word
<-
48
ioVAlBlkSiz
longword
<-
52
ioVClpSiz
longword
<-
56
ioAlBlSt
word
<-
58
ioVNxtFNum longword
<-
62
ioVFrBlk
word
PB Get Vlnf o returns information about the specified volume. If io Vollndex is positive, the
File Manager attempts to use it to find the volume; for instance, if io Vollndex is 2, the File
Manager will attempt to access the second mounted volume. If io Vollndex is negative, the
File Manager uses ioNamePtr and ioVRefNum in the standard way (described in the
section "Specifying Volumes, Directories, and Files") to determine which volume. If
io Vollndex is 0, the File Manager attempts to access the volume by using io VRefNum
only. The volume reference number is returned in ioVRefNum, and a pointer to the
volume name is returned in ioNamePtr (unless ioNamePtr is NIL).
If a working directory reference number is passed in io VRefNum (or if the default directory
is a subdirectory), the number of files and directories in the specified directory (the
directory's valence) will be returned in ioVNmFls. Also, the volume reference number
won't be returned; ioVRefNum will still contain the working directory reference number.
Low-Level File Manager Routines IV-129

<!-- source-page: 140 -->
## Page 140

Inside Macintosh
Warning: ~OVNmAlBlks and ioVFrBlks, which are actually unsigned integers, are
clipped to 317 44 ($7 COO) regardless of the size of the volume.
Result codes
noErr
No error
nsvErr
paramErr
No such volume
No default volume
FUNCTION P~HGetVInfo (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HGetVInfo
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
->
28
ioVollndex
word
<-
30
ioVCrDate
longword
<-
34
ioVLsMod
longword
<-
38
ioVAtrb
word
<-
40
ioVNmFls
word
<-
42
ioVBitMap
word
<-
44
io V AllocPtr
word
<-
46
io VNmAlBlks word
<-
48
io V AlBlk:Siz
longword
<-
52
ioVClpSiz
longword
<-
56
ioAlBlSt
word
<-
58
ioVNxtFNum longword
<-
62
ioVFrBlk
word
<-
64
ioVSigWord
word
<-
66
ioVDivlnfo
word
<-
68
ioVDRefNum word
<-
70
ioVFSID
word
<-
72
ioVBkUp
longword
<-
76
ioVSeqNum
word
<-
78
ioVWrCnt
long word
<-
82
ioVFilCnt
longword
<-
86
ioVDirCnt
longword
<-
90
ioVFndrlnfo
32 bytes
PBHGetVInfo is similar in function to PBGetVInfo but returns a larger parameter block.
In addition, PBHGetVInfo always returns the volume reference number in ioVRefNum
(regardless of what was passed in). Also, ioVNmAlBlks and ioVFrBlks are not clipped as
they are by PEGetVInfo.
Result codes
noErr
nsvErr
paramErr
No error
No su~h volume
No default volume
IV-130 Low-Level File Manager Routines

<!-- source-page: 141 -->
## Page 141

The File Manager
FUNCTION PBSetVInfo (paramBlock; HParmBlkPtr; async: BOOLEAN)
:
OSErr;
Trap macro
_SetVollnfo
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
-:>
22
ioVRefNum
word
->
30
ioVCrDate
long word
->
34
ioVLsMod
fongword
->
38
ioVAtrb
word
->
52
ioVClpSiz
long word
->
72
ioVBkUp
longword
->
76
ioVSeqNum
word
->
90
ioVFndrlnfo
32 bytes
PBSetVInfo lets you modify information about volumes. A pointer to a new name for the
volume can be specified in ioNamePtr. The date and time of the volume's creation and
modification can be set with ioVCrDate and ioVLsMod respectively. Only bit 15 of
io V Atrb can be changed; setting it locks the volume.
Note: The volume cannot be specified by name; you must use either the volume
reference number or the drive number.
Warning: PBSetVInfo operates only with the hierarchical version of the File
Manager; if used on a Macintosh equipped only with the 64K ROM version of the
File Manager, it will generate a system error.
Result codes
no Err
nsvErr
paramErr
No error
No such volume
No default volume
FUNCTION PBGetVol (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_Get Vol
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<-
22
ioVRefNum
word
PBGetVol returns a pointer to the name of the default volume in ioNamePtr (unless
ioN amePtr is NIL) and its volume reference number in io VRefNum. If a default directory
was set with a previous PBSetVol call, a pointer to its name will be returned in ioNamePtr
and its working directory reference number in io VRefNum.
Result codes
no Err
nsvErr
No error
No default volume
Low-Level File Manager Routines IV-131

<!-- source-page: 142 -->
## Page 142

Inside Macintosh
FUNCTION PBHGetVol (paramBlock: WDPBPtr; async: BOOLEAN)
OSErr;
Trap macro
_HGetVol
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<-
22
ioVRefNum
word
<-
28
ioWDProcID
longword
<-
32
ioWDVRefNum word
<-
48
ioWDDirID
long word
PBHGetVol returns the default volume and directory last set by either a PBSetVol or a
PBHSetVol call. The reference number of the default volume is returned in io VRefNum.
Warning: IOVRefNum will return a working directory reference number (instead
of the volume reference number) if, in the last call to PBSetVol or PBHSetVol, a
working directory reference number was passed in this field.
The volume reference number of the volume on which the default directory exists is
returned in ioWDVRefNum. The directory ID of the default directory is returned in
ioWDDirID.
Result codes
no Err
nsvErr
No error
No default volume
FUNCTION PBSetVol (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_SetVol
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
OSErr;
PBSetVol sets the default volume to the mounted volume specified by ioNamePtr or
ioVRefNum. On hierarchical volumes, PBSetVol also sets the root directory as the default
directory.
Result codes
noErr
bdNamErr
nsvErr
paramErr
No error
Bad volume name
No such volume
No default volume
W-132 Low-Level File Manager Routines

<!-- source-page: 143 -->
## Page 143

The File Manager
FUNCTION PBHSetVol (paramBlock: WDPBPtr; async: BOOLEAN) : OSErr;
Trap macro
_HSetVol
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRetNum
word
->
48
ioWDDirID
longword
PBHSetVol sets both the default volume and the default directory. The default directory to
be used can be specified by either a volume reference number or a working directory
reference number in ioVRetNum, a directory ID in ioWDDirID, or a pointer to a pathname
(possibly NIL) in ioNamePtr.
Note: Both the default volume and the default directory are used in calls made with
no volume name and a volume reference number of zero.
Result codes
no Err
nsvErr
No error
No default volume
FUNCTION PBFlushVol (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_Flush Vol
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRetNum
word
On the volume specified by ioNamePtr or io VRetNum, PB Flush Vol writes descriptive
information about the volume, the contents of the associated volume buffer, and all access
path buffers for the volume (if they've changed since the last time PBFlush Vol was called).
Note: The date and time of the last modification to the volume are set when the
modification is made, not when the volume is flushed.
Result codes
no Err
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
No error
Bad volume name
External file system
1/0 error
No such drive
No such volume
No default volume
Low-Level File Manager Routines IV-133

<!-- source-page: 144 -->
## Page 144

Inside Macintosh
FUNCTION PBUnmountVol (paramBlock: ParmBlkPtr)
Trap macro
_UnmountVol
Parameter block
<-
16
->
18
->
22
ioResult
ioNamePtr
ioVRefNum
word
pointer
word
OSErr;
PBUnmountVol unmounts the volume specified by ioNamePtr or io VRefNum, by calling
PB Flush Vol to flush the volume, closing all open files on the volume, and releasing the
memory used for the volume. PBUnmountVol is always executed synchronously.
Warning: Don't unmount the startup volume.
Note: Unmounting a volume does not close working directories; to release the
memory allocated to a working directory, call PBCloseWD.
Result codes
noErr
No error
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
Bad volume name
External file system
I/O error
No such drive
No such volume
No default volume
FUNCTION PBOffLine (paramBlock: ParmBlkPtr)
Trap macro
_OffLine
Parameter block
->
12
ioCompletion pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
OSErr;
PBOftLine places off-line the volume specified by ioNamePtr or ioVRefNum, by calling
PBFlush Vol to flush the volume and releasing all the memory used for the volume except
for the volume control block. PBOffLine is always executed synchronously.
Result codes
noErr
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
No error
Bad volume name
External file system
I/O error
No such drive
No such volume
No default volume
IV-134 Low-Level File Manager Routines

<!-- source-page: 145 -->
## Page 145

The File Manager
FUNCTION PBEject (paramBlock: ParmBlkPtr)
OSErr;
Trap macro
_Eject
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
PBEject flushes the volume specified by ioNamePtr or ioVRefNum, places it off-line, and
then ejects the volume.
Assembly-language note: You may invoke the macro _Eject asynchronously;
the first part of the call is executed synchronously, and the actual ejection is executed
asynchronous! y.
Result codes
noErr
No error
Accessing Files
bdNamErr
extFSErr
ioErr
nsDrvErr
nsvErr
paramErr
Bad volume name
External file system
1/0 error
No such drive
No such volume
No default volume
FUNCTION PBOpen (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_Open
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioRefNum
word
->
26
ioVersNum
byte
->
27
ioPermssn
byte
->
28
ioMisc
pointer
OSErr;
PBOpen creates an access path to the file having the name pointed to by ioNamePtr (and on
flat volumes, the version number io VersNum) on the volume specified by io VRefNum. A
path reference number is returned in ioRefNum.
IOMisc either points to a portion of memory (522 bytes) to be used as the access path's
buffer, or is NIL if you want the volume buffer to be used instead.
Warning: All access paths to a single file that's opened multiple times should share
the same buffer so that they will read and write the same data.
Low-Level File Manager Routines IV-135

<!-- source-page: 146 -->
## Page 146

Inside Macintosh
IOPermssn specifies the path's read/write permission. A path can be opened for writing
even if it accesses a file on a locked volume, and an error won't be returned until a
PBWrite, PBSetEOF, or PBAllocate call is made.
If you attempt to open a locked file for writing, PBOpen will return permErr as its function
result. If you request exclusive read/write permission but another access path already has
write permission (whether write only, exclusive read/write, or shared read/write), PBOpen
will return the reference number of the existing access path in ioRefNum and op WrErr as
its function result. Similarly, if you request shared read/write permission but another
access path already has exclusive read/write permission, PBOpen will return the reference
number of the access path in ioRefNum and op WrErr as its function result.
Result codes
no Err
bdNamErr
extFSErr
fnfErr
ioErr
nsvErr
opWrErr
permErr
tmfoErr
No error
Bad file name
External file system
File not found
I/O error
No such volume
File already open for writing
Attempt to open locked file for writing
Too many files open
FUNCTION PBHOpen (paramBlock: HParmBlkPtr; async: BOOLEAN)
Trap macro
_HOpen
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioRefNum
word
->
27
ioPermssn
byte
->
28
ioMisc
pointer
->
48
ioDirID
longword
PBHOpen is identical to PBOpen except that it accepts a directory ID in ioDirID.
Result codes
no Err
bdNamErr
dirNFErr
extFSErr
fnfErr
ioErr
nsvErr
opWrErr
permErr
tmfoErr
No error
Bad file name
Directory not found or incomplete pathname
External file system
File not found
I/0 error
No such volume
File already open for writing
Attempt to open locked file for writing
Too many files open
W-136 Low-Level File Manager Routines
OSErr;

<!-- source-page: 147 -->
## Page 147

The File Manager
FUNCTION PBOpenRF (paramBlock: ParmBlkPtr; async: BOOLEAN) : OSErr;
Trap macro
_OpenRF
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioRefNum
word
->
26
ioVersNum
byte
->
27
ioPermssn
byte
->
28
ioMisc
pointer
PBOpenRF is identical to PBOpen, except that it opens the file's resource fork instead of
its data fork.
Note: Normally you should access a file's resource fork through the routines of the
Resource Manager rather than the File Manager. PBOpenRF doesn't read the
resource map into memory; it's really only useful for block-level operations such as
copying files.
Result codes
noErr
No error
bdNamErr
extFSErr
fnfErr
ioErr
nsvErr
opWrErr
permErr
tmfoErr
Bad file name
External file system
File not found
I/O error
No such volume
File already open for writing
Attempt to open locked file for writing
Too many files open
FUNCTION PBHOpenRF (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HOpenRF
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioRefNum
word
->
27
ioPermssn
byte
->
28
ioMisc
pointer
->
48
ioDirID
longword
PBHOpenRF is identical to PBOpenRF except that it accepts a directory ID in ioDirID.
Low-Level File Manager Routines IV-137

<!-- source-page: 148 -->
## Page 148

Inside Macintosh
Result codes
noEiT
No error
bdNamErr
clirNFErr
extFSErr
fnfEiT
ioErr
nsvErr
opWrErr
pennErr
tmfoErr
Bad file name
:pirectory not found or incomplete pathname
~xteinal file system
File not found
I/O error
No such volume
File already open for writing
Attempt to open locked file for writing
Too many files open
FUNCTION PBLockRange (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_LockRng
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
36
ioReqCount
long word
->
44
ioPosMode
word
->
46
ioPosOff set
long word
On a file opened with a shared read/write permission, PBLockRange is used in conjunction
with PBRead and PBWrite to lock a certain portion of the file. PBLockRange uses the
same parameters as both PBRead and PBWrite; by calling it immediately before PBRead,
you can use the information present in the parameter block for the PBRead call.
When you're finished with the data (typically after a call to PBWrite), be sure to call
PBUnlockRange to free up that portion of the file for subsequent PBRead calls.
Warning: PBLockRange operates only with the hierarchical version of the File
Manager; if used on a Macintosh equipped only with the 64K ROM version of the
File Manager, it will generate a system error.
Result codes
noErr
eofErr
extFSErr
fnOpnErr
ioErr
paramErr
rfNumErr
No error
End-of-file
External file system
File not open
I/O error
Negative ioReqCount
Bad reference number
W-138 Low-Level File Manager Routines

<!-- source-page: 149 -->
## Page 149

The File Manager
FUNCTION PBUnlockRange (paramBlock: ParmBlkPtr; async: BOOLEAN) :
OSErr;
Trap macro
_UnlockRng
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
36
ioReqCount
longword
->
44
ioPosMode
word
->
46
ioPosOff set
longword
PBUnlockRange is used in conjunction with PBRead and PBWrite to unlock a certain
portion of a file that you locked with PBLockRange.
Warning: PBUnlockRange operates only with the hierarchical version of the File
Manager; if used on a Macintosh equipped only with the 64K ROM version of the
File Manager, it will generate a system error.
Result codes
noErr
No error
End-of-file
External file system
File not open
I/Oerror
eofErr
extFSErr
fnOpnErr
ioErr
paramErr
rfNumErr
Negative ioReqCount
Bad reference number
FUNCTION PBRead (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_Read
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
32
ioBqffer
pointer
->
36
ioReqCount
longword
<-
40
ioActCount
longword
->
44
ioPosMode
word
<->
46
ioPosOff set
longword
OSErr;
PBRead attempts to read ioReqCount bytes from the open file whose access path is
specified by ioRefNum, and transfer them to the data buffer pointed to by ioBuffer. The
position of the mark is specified by ioPosMode and ioPosOffset. If you try to read past the
Low-Level File Manager Routines W-139

<!-- source-page: 150 -->
## Page 150

Inside Macintosh
logical end-of-file, PBRead moves the mark to the end-of-file and returns eofErr as its
function result. After the read is completed, the mark is returned in ioPosOffset and the
number of bytes actually read is returned in ioActCount.
Result codes
noErr
No error
End-of-file
External file system
File not open
eotErr
extFSErr
fnOpnErr
ioErr
paramErr
rfNumErr
1/0 error
Negative ioReqCount
Bad reference number
FUNCTION PBWrite (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_Write
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
32
ioBuffer
pointer
->
36
ioReqCount
longword
<-
40
ioActCount
longword
->
44
ioPosMode
word
<->
46
ioPosOff set
longword
OSErr;
PBWrite takes ioReqCount bytes from the buffer pointed to by ioBuffer and attempts to
write them to the open file whose access path is specified by ioRefNum. The position of
the mark is specified by ioPosMode and ioPosOffset. After the write is completed, the
mark is returned in ioPosOffset and the number of bytes actually written is returned in
ioActCount.
Result codes
noErr
dskFulErr
fLckdErr
fnOpnErr
ioErr
paramErr
posErr
rfNumErr
vLckdErr
wPrErr
wrPermErr
No error
Disk full
File locked
File not open
1/0 error
Negative ioReqCount
Attempt to position before start of file
Bad reference number
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
W-140 Low-Level File Manager Routines

<!-- source-page: 151 -->
## Page 151

The File Manager
FUNCTION PBGetFPos (paramBlock: ParmBlkPtr; async: BOOLEAN}
:
OSErr;
Trap macro
_GetFPos
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
<-
36
ioReqCount
longword
<-
40
ioActCount
longword
<-
44
ioPosMode
word
<-
46
ioPosOff set
longword
PBGetFPos returns, in ioPosOff set, the mark of the open file whose access path is
specified by ioRefNum. It sets ioReqCount, ioActCount, and ioPosMode to 0.
Result codes
no Err
extFSErr
fnOpnErr
gfpErr
ioErr
rfNumErr
No error
External file system
File not open
Error during GetFPos
l/O error
Bad reference number
FUNCTION PBSetFPos (paramBlock: ParmBlkPtr; async: BOOLEAN}
Trap macro
_SetFPos
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
44
ioPosMode
word
<->
46
ioPosOff set
longword
OSErr;
PBSetFPos sets the mark of the open file whose access path is specified by ioRefNum to
the position specified by ioPosMode and ioPosOffset. The position at which the mark is
actually set is returned in ioPosOffset. If you try to set the mark past the logical end-offile, PBSetFPos moves the mark to the end-of-file and returns eofErr as its function result.
Result codes
no Err
eofErr
extFSErr
fnOpnErr
ioErr
posErr
rfNumErr
No error
End-of-file
External file system
File not open
l/O error
Attempt to position before start of file
Bad reference number
Low-Level File Manager Routines IV-141

<!-- source-page: 152 -->
## Page 152

Inside Macintosh
FUNCTION PBGetEOF (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_GetEOF
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
<-
28
ioMisc
longword
PBGetEOF returns, in ioMisc, the logical end-of-file of the open file whose access path is
specified by ioRefNum.
Result codes
no Err
extFSErr
fnOpnErr
ioErr
rfNumErr
No error
External file system
File not open
1/0 error
Bad reference number
FUNCTION PBSetEOF (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_SetEOF
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
28
ioMisc
longword
OSErr;
PBSetEOF sets the logical end-of-file of the open file, whose access path is specified by
ioRefNum, to ioMisc. If you attempt to set the logical end-of-file beyond the physical endof-file, another allocation block is added to the file; if there isn't enough space on the
volume, no change is made, and PBSetEOF returns dskFulErr as its function result. If
ioMisc is 0, all space occupied by the file on the volume is released.
Result codes
no Err
dskFulErr
extFSErr
fLckdErr
fnOpnErr
ioErr
rfNumErr
vLckdErr
wPrErr
wrPermErr
No error
Disk full
External file system
File locked
File not open
1/0 error
Bad reference number
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
W-142 Low-Level File Manager Routines

<!-- source-page: 153 -->
## Page 153

The File Manager
FUNCTION PBAllocate (paramBlock: ParmBlkPtr; async: BOOLEAN) :
OSErr;
Trap macro
_Allocate
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
-> 24
ioRefNum
word
->
36
ioReqCount
long word
<-
40
ioActCount
longword
PBAllocate adds ioReqCount bytes to the open file whose access path is specified by
ioRetNum, and sets the physical end-of-file to one byte beyond the last block allocated.
The number of bytes actually allocated is rounded up to the nearest multiple of the
allocation block size, and returned in ioActCount. If there isn't enough empty space on
the volume to satisfy the allocation request, PBAllocate allocates the rest of the space on the
volume and returns dskFulErr as its function result.
Note: Even if the total number of requested bytes is unavailable, PBAllocate will
allocate whatever space, contiguous or not, is available. To force the allocation of
the entire requested space as a contiguous piece, call PBAllocContig instead.
Result codes
noErr
No error
Disk full
dskFulErr
tLckdErr
fnOpnErr
ioErr
rfNumErr
vLckdErr
wPrErr
wrPermErr
File locked
File not open
l/Oerror
Bad reference number
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
FUNCTION PBAllocContig (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_AllocContig
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
36
ioReqCount
longword
<-
40
ioActCount
longword
PBAllocContig is identical to PBAllocate except that if there isn't enough contiguous empty
space on the volume to satisfy the allocation request, PBAllocContig will do nothing and
will return dskFulErr as its function result. If you want to allocate whatever space is
available, even when the entire request cannot be filled as a contiguous piece, call
PBAllocate instead.
Low-Level File Manager Routines IV-143

<!-- source-page: 154 -->
## Page 154

Inside Macintosh
Result codes
noErr
dskFulErr
tLckdErr
fnOpnErr
ioErr
rfNumErr
vLckdErr
wPrErr
wrPermErr
No error
Disk full
File locked
File not open
1/0 error
Bad reference number
Software volume lock
Hardware volume lock
Read/write permission doesn't allow writing
FUNCTION PBFlushFile (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_FlushFile
Parameter block
->
12
<-
16
->
24
ioCompletion pointer
ioResult
word
ioRefNum
word
PBFlushFile writes the contents of the access path buffer indicated by ioRefNum to the
volume, and updates the file's entry in the file directory (or in the file catalog, in the case of
hierarchical volumes).
Warning: Some information stored on the volume won't be correct until
PB Flush Vol is called.
Result codes
noErr
extFSErr
fnfErr
fnOpnErr
ioErr
nsvErr
rfNumErr
No error
External file system
File not found
File not open
1/0 error
No such volume
Bad reference number
FUNCTION PBClose (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_Close
Parameter block
->
12
<-
16
->
24
ioCompletion pointer
ioResult
word
ioRefNum
word
OSErr;
PBClose writes the contents of the access path buffer specified by ioRefNum to the volume
and removes the access path.
Warning: Some information stored on the volume won't be correct until
PB Flush Vol is called.
W-144 Low-Level File Manager Routines

<!-- source-page: 155 -->
## Page 155

Result codes
no Err
extFSErr
fnfErr
fnOpnErr
ioErr
nsvErr
rfNumErr
No error
External file system
File not found
File not open
I/O error
No such volume
Bad reference number
Creating and Deleting Files and Directories
The File Manager
FUNCTION PBCreate (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_Create
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
PBCreate creates a new file (both forks) having the name pointed to by ioNamePtr (and on
flat volumes, the version number io VersNum) on the volume specified by io VRefNum.
The new file is unlocked and empty. The date and time of its creation and last modification
are set to the current date and time. If the file created isn't temporary (that is, if it will exist
after the application terminates), the application should call PBSetFInfo (after PBCreate) to
fill in the information needed by the Finder.
Assembly-language note: If a desk accessory creates a file, it should always
create it in the directory containing the system folder. The working directory
reference number for this directory is stored in the global variable BootDrive; you can
pass it in ioVRefNum.
Result codes
noErr
bdNamErr
dupFNErr
dirFulErr
extFSErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Bad file name
Duplicate file name and version
File directory full
External file system
I/O error
No such volume
Software volume lock
Hardware volume lock
Low-Level File Manager Routines IV-145

<!-- source-page: 156 -->
## Page 156

Inside Macintosh
FUNCTION PBHCreate (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HCreate
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNa.IilePtr
pointer
->
22
ioVRefNum
word
->
48
ioDirID
longword
PBHCreate is identical to PBCreate except that it accepts a directory ID in ioDirID.
Note: To create a directory instead of a file, call PBDirCreate.
Result codes
no Err
bdNamErr
dupFNErr
dirFulErr
dirNFErr
extFSErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Bad file name
Duplicate file name and version
File directory full
Directory not found or incomplete pathname
External file system
I/O error
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBDirCreate (paramBlock: HParmBlkPtr; async: BOOLEAN):
OSErr;
Trap macro
_DirCr~ate
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<->
48
ioDirID
long word
PBDirCreate is identical to PBHCreate except that it creates a new directory instead of a
file. You can specify the parent of the directory to be created in ioDirID; if it's 0, the new
directory will be placed in the root directory. The directory ID of the new directory is
returned in ioDirlD.
Warning: PBDirCreate operates only with l:he hierarchical version of the File
Manager; if used on a Macintosh equipped only with the 64K ROM version of the
File Manager, it will generate a system error.
W-146 Low-Level File Manager Routines

<!-- source-page: 157 -->
## Page 157

The File Manager
Result codes
noErr
bdNamErr
dupFNErr
dirFulErr
dirNFErr
extFSErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Bad file name
Duplicate file name and version
File directory full
Directory not found or incomplete pathname
External file system
I/O error
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBDelete (paramBlock: ParmBlkPtr; async: BOOLEAN)
Trap macro
_Delete
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
OSErr;
PBDelete.removes the closed file having the name pointed to by ioNamePtr (and on flat
volumes, the version number ioVersNum) from the volume pointed to by ioVRefNum.
PBHDelete can be used to delete an empty directory as well.
Note: This function will delete both forks of the file.
Result codes
no Err
bdNamErr
extFSErr
fBsyErr
fLckdErr
fnfErr
nsvErr
ioErr
vLckdErr
wPrErr
No error
Bad file name
External file system
File busy, directory not empty, or working directory
control block open
File locked
File not found
No such volume
I/O error
Software volume lock
Hardware volume lock
FUNCTION PBHDelete (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HDelete
Parameter block
->
12
<-
16
->
18
->
22
->
48
ioCompletion
ioResult
ioNamePtr
ioVRefNum
ioDirID
pointer
word
pointer
word
longword
Low-Level File Manager Routines IV-147

<!-- source-page: 158 -->
## Page 158

Inside Macintosh
PBHDelete is identical to PBDelete except that it accepts a directory ID in ioDirlD.
PBHDelete can be used to delete an empty directory as well.
Result codes
noErr
No error
bdNamErr
dirNFErr
extFSErr
fBsyErr
fLckdErr
fnfErr
nsvErr
ioErr
vLckdErr
wPrErr
Bad file name
Directory not found or incomplete pathname
External file system
File busy, directory not empty, or working directory
control block open
File locked
File not found
No such volume
l/Oerror
Software volume lock
Hardware volume lock
Changing Information About Files and Directories
FUNCTION PBGetFInfo (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_ GetFilelnfo
Parameter block
->
12
ioCompletion pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioFRefNum
word
->
26
ioFVersNum byte
->
28
ioFDirlndex
word
<-
30
ioFIAttrib
byte
<-
31
ioFIVersNum byte
<-
32
ioFlFndrlnfo 16 bytes
<-
48
ioFlNum
longword
<-
52
ioFIStBlk
word
<-
54
ioFILgLen
longword
<-
58
ioFIPyLen
long word
<-
62
ioFIRStBlk
word
<-
64
ioFIRLgLen
longword
<-
68
ioFIRPyLen
longword
<-
72
ioFIODat
longword
<-
76
ioFIMdDat
longword
PBGetFInfo returns information about the specified file. If ioFDirlndex is positive, the
File Manager returns information about the file whose directory index is ioFDirlndex on the
volume specified by io VRefNum. (See the section "Data Organization on Volumes" if
you're interested in using this method.)
Note: If a working directory reference number is specified in io VRefNum, the File
Manager returns information about the file whose directory index is ioFDirlndex in
the specified directory.
IV-148 Low-Level File Manager Routines

<!-- source-page: 159 -->
## Page 159

The File Manager
If ioFDirlndex is negative or 0, the File Manager returns inf onnation about the file having
the name pointed to by ioNamePtr (and on flat volumes, the version number ioFVersNum)
on the volume specified by io VRefNum. If the file is open, the reference number of the
first access path found is returned in ioFRefNum, and the name of the file is returned in
ioNamePtr (unless ioNamePtr is NIL).
Result codes
noErr
No error
bdNamErr
extFSErr
fnfErr
ioErr
nsvErr
paramErr
Bad file name
External file system
File not found
1/0 error
No such volume
No default volume
FUNCTION PBHGetFInfo (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HGetFileInfo
Parameter block
->
12
ioCompletion pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioFRefNum
word
->
28
ioFDirlndex
word
<-
30
ioFlAttrib
byte
<-
32
ioFlFndrlnfo 16 bytes
<->
48
ioDirID
longword
<-
52
ioFlStBlk
word
<-
54
ioFlLgLen
longword
<-
58
ioFlPyLen
longword
<-
62
ioFlRStBlk
word
<-
64
ioFlRLgLen
longword
<-
68
ioFlRPyLen
longword
<-
72
ioFlCrDat
longword
<-
76
ioFlMdDat
long word
PBHGetFInfo is identical to PBGetFInfo except that it accepts a directory ID in ioDirID.
Result codes
noErr
bdNamErr
dirNFErr
extFSErr
fnfErr
ioErr
nsvErr
paramErr
No error
Bad file name
Directory not found or incomplete pathname
External file system
File not found
1/0 error
No such volume
No default volume
Low-Level File Manager Routines IV-149

<!-- source-page: 160 -->
## Page 160

Inside Macintosh
FUNCTION PBSetFInfo (paramBlock: ParmBlkPtr; async: BOOLEAN}
OSErr;
Trap macro
_SetFilelnf o
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
->
32
ioFlFndrlnfo
16 bytes
->
72
ioFlCrDat
longword
->
76
ioFlMdDat
longword
PBSetFInfo sets information (including the date and time of creation and modification, and
information needed by the Finder) about the file having the name pointed to by ioNamePtr
(and on flat volumes, the version number ioFVersNum) on the volume specified by
ioVRefNum. You should call PBGetFInfo just before PBSetFInfo, so the current
information is present in the parameter block.
Result codes
noErr
No error
bdNamErr
extFSErr
tLckdErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
Bad file name
External file system
File locked
File not found
J/Oerror
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBHSetFInfo (paramBlock: HParmBlkPtr; async: BOOLEAN}
OSErr;
Trap macro
_HSetFileInfo
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
32
ioFlFndrlnfo
16 bytes
->
48
ioDirID
longword
->
72
ioFlCrDat
longword
->
76
ioFlMdDat
longword
PBHSetFInfo is identical to PBSetFInfo except that it accepts a directory ID in ioDirID.
W-150 Low-Level File Manager Routines

<!-- source-page: 161 -->
## Page 161

The File Manager
Result codes
noErr
No error
bdNamErr
dirNFErr
extFSErr
fLckdErr
f nfErr
ioErr
nsvErr
vLckdErr
wPrErr
Bad file name
Directory not found or incomplete pathname
External file system
File locked
File not found
l/Oerror
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBSetFLock (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_SetFilLock
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
PBSetFLock locks the file having the name pointed to by ioNamePtr (and on flat volumes,
the version number ioFVersNum) on the volume specified by ioVRefNum. Access paths
currently in use aren't affected.
Result codes
noErr
No error
extFSErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
External file system
File not found
l/Oerror
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBHSetFLock (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HSetFLock
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
-> 22
ioVRefNum
word
-> 48
ioDirID
longword
PBHSetFLock is identical to PBSetFLock except that it accepts a directory ID in ioDirID.
Low-Level File Manager Routines W-151

<!-- source-page: 162 -->
## Page 162

Inside Macintosh
Result codes
noErr
dirNFErr
extFSErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Directory not found or incomplete pathname
External file system
File not found
1/0 error
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBRstFLock (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_RstFilLock
Parameter block
->
12
ioCompletion pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
PBRstFLock unlocks the file having the name pointed to by ioNamePtr (and on flat
volumes, the version number ioFV ersNum) on the volume specified by io VRefNum.
Access paths currently in use aren't affected.
Result codes
noErr
extFSErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
External file system
File not found
l/Oerror
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBHRstFLock (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HR.stFLock
Parameter block
->
12
ioCompletion pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
48
ioDirID
longword
PBHR.stFLock is identical to PBRstFLock except that it accepts a directory ID in ioDirID.
IV-152 Low-Level File Manager Routines

<!-- source-page: 163 -->
## Page 163

The File Manager
Result codes
noErr
dirNFErr
extFSErr
fnfErr
ioErr
nsvErr
vLckdErr
wPrErr
No error
Directory not found or incomplete pathname
External file system
File not found
I/0 error
No such volume
Software volume lock
Hardware volume lock
FUNCTION PBSetFVers (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_SetFilType
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioVersNum
byte
->
28
ioMisc
byte
PBSetFV ers has no effect on hierarchical volumes. On flat volumes, PBSetFV ers changes
the version number of the file having the name pointed to by ioNamePtr and version
numberioVersNum, on the volume specified by ioVRefNum, to the version number stored
in the high-order byte of ioMisc. Access paths currently in use aren't affected.
Result codes
no Err
bd.NamErr
dupFNErr
extFSErr
fLckdErr
fnfErr
nsvErr
No error
Bad file name
Duplicate file name and version
External file system
File locked
File not found
No such volume
I/O error
No default volume
Software volume lock
Hardware volume lock
ioErr
paramErr
vLckdErr
wPrErr
wrgVolTypErr Attempt to perform hierarchical operation on a flat
volume
FUNCTION PBRename (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_Rename
Parameter block
->
12
<-
16
->
18
->
22
->
26
->
28
ioCompletion
ioResult
ioNamePtr
ioVRefNum
ioVersNum
ioMisc
pointer
word
pointer
word
byte
pointer
Low-Level File Manager Routines N-153

<!-- source-page: 164 -->
## Page 164

Inside Macintosh
Given a pointer to a file name in ioNarnePtr (l:Jlld on flat volumes, a version number in
ioVersNum), PBRename changes the name of the file to the name pointed to by ioMisc. (If
the name ,pointed to by ioNamePtr contains one or more colons, so must the name pointed
to by ioMist.) Access paths currently in use aren't affected. Given a pointer to a volume
nanie ii1 ioNamePtr or a vdluine reference number in io VRefNum, it changes the name of
the vo1tii:ne to the name pointed to by ioMisc. If a volume to be renamed is specified by its
volume reference number, ioNamePtr can be NIL.
Warning: If a volume to be renamed is specified by its volume name, be sure that it
ends with a colon, or Rename will consider it a file name.
Result codes
no Err
bdNamErr
dirFulErr
dupFNErr
extFSErr
tLckdErr
fnfErr
fsRnErr
ioErr
nsvErr
paramErr
vLckdErr
wPrErr
No error
Bad file name
File directory full
Duplicate file name and version
External file system
File locked
File not found
Problem during rename
I/O error
No such volume
No default volume
Software volume lock
Hardware volume lock
FUNCTION PBHRename (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
Trap macro
_HRename
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
28
ioMisc
pointer
->
48
ioDirID
long word
PBHRename is identical to PBRename except that it accepts a directory ID in ioDirID and
can be used to rename directories as well as files and volumes. Given a pointer to the name
of a file or directory in ioNamePtr, PBHRename changes it to the name pointed to by
ioMisc. Given a pointer to a volume name in ioNamePtr or a volume reference number in
ioVRefNum, it changes the name of the volume to the name pointed to by ioMisc.
Warning: PBHRename cannot be used to change the directory a file is in.
Result codes
no Err
bdNamErr
dirFulErr
dirNFErr
ciupFNErr
extFSErr
tLckdErr
No error
Bad tile name
File directory full
Directory not found or incomplete pathname
Duplicate file name and version
External file system
File locked
W-154 Low-Level File Manager Routines

<!-- source-page: 165 -->
## Page 165

fnfErr
fsRnErr
ioErr
nsvErr
paramErr
vLckdErr
wPrErr
Hierarchical Directory Routines
File not found
Problem during rename
I/O error
No such volume
No default volume
Software volume lock
Hardware volume lock
The File Manager
Warning: The routines described in this section operate only with the hierarchical
version of the File Manager; if used on a Macintosh equipped only with the 64K
ROM version of the File Manager, they will generate a system error.
FUNCTION PBGetCatInfo (paramBlock: CinfoPBPtr; async: BOOLEAN):
OSErr;
Trap macro
_ GetCatinfo
Parameter block
Files:
Directories:
->
12
ioCompletion pointer
->
12
ioCompletion pointer
<-
16
ioResult
word
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
22
ioVRefNum
word
<-
24
ioFRetNum
word
<-
24
ioFRefNum
word
->
28
ioFDirlndex
word
->
28
ioFDirlndex
word
<-
30
ioFIAttrib
byte
<-
30
ioFIAttrib
byte
<-
32
ioFlFndrlnfo
16 bytes
<-
32
ioDrUsrWds
16 bytes
<->
48
ioDirID
long word
<->
48
ioDrDirID
long word
<-
52
ioFlStBlk
word
<-
52
ioDrNmFls
word
<-
54
ioFILgLen
long word
<-
58
ioflPyLen
long word
<-
62
ioFIRStBlk
word
<-
64
ioFIRLgLen
long word
<-
68
ioFIRPyLen
longword
<-
72
ioFlCrDat
longword
<-
72
ioDrCrDat
long word
<-
76
ioFlMdDat
longword
<-
76
ioDrMdDat
long word
<-
80
ioFlBkDat
long word
<-
80
ioDrBkDat
long word
<-
84
ioFlXFndrlnfo 16 bytes
<-
84
ioDrFndrlnfo
16 bytes
<-
100 ioFlParID
long word
<-
100 ioDrParID
long word
<-
104 ioFlClpSiz
longword
PBGetCatInfo gets information about the files and directories in a file catalog. To
determine whether the information is for a file or a directory, test bit 4 of ioFIAttrib, as
described in the section "CInfoPBRec". The information that's returned for files is shown
in the left column, and the corresponding information for directories is shown in the right
column.
If ioFDirlndex is positive, the File Manager returns information about the file or directory
whose directory index is ioFDirlndex in the directory specified by ioVRefNum (this will be
the root directory if a volume reference number is provided).
Low-Level File Manager Routines IV-155

<!-- source-page: 166 -->
## Page 166

Inside Macintosh
If ioFDirindex is 0, the File Manager returns information about the file or directory
specified by ioNamePtr, in the directory specified by io VRefNum (again, this will be the
root directory if a volume reference number is provided).
If ioFDirindex is negative, the File Manager ignores ioNamePtr and returns information
about the directory specified by ioDirID.
With files, PBGetCatInfo is similar to PBHGetFileinfo but returns some additional
information. If the file is open, the reference number of the first access path found is
returned in ioFRefNum, and the name of the file is returned in ioNamePtr (unless
ioNamePtr is NIL).
Result codes
noErr
bdNamErr
dirNFErr
extFSErr
fnfErr
ioErr
nsvErr
paramErr
No error
Bad file name
Directory not found or incomplete pathname
External file system
File not found
J/O error
No such volume
No default volume
FUNCTION PBSetCatInfo (paramBlock: CinfoPBPtr; async: BOOLEAN)
OSErr;
Trap macro
_SetCatinfo
Parameter block
Files:
Directories:
->
12
ioCompletion pointer
->
12
ioCompletion pointer
<-
16
ioResult
word
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
22
ioVRefNum
word
->
30
ioFIAttrib
byte
->
30
ioFIAttrib
byte
->
32
ioFIFndrlnfo
16 bytes
->
32
ioDrUsrWds
16 bytes
->
48
ioDirID
longword
->
48
ioDrDirID
longword
->
72
ioFICrDat
longword
->
72
ioDrCrDat
longword
->
76
ioFIMdDat
longword
->
76
ioDrMdDat
longword
->
80
ioFIBkDat
longword
->
80
ioDrBkDat
longword
->
84
ioFIXFndrlnfo 16 bytes
->
84
ioDrFndrlnfo
16 bytes
->
104 ioFIClpSiz
longword
PBSetCatInfo sets information about the files and directories in a catalog. With files, it's
similar to PBHSetFilelnfo but lets you set some additional information. The information
that can be set for files is shown in the left column, and the corresponding information for
directories is shown in the right column.
IV-156 Low-Level File Manager Routines

<!-- source-page: 167 -->
## Page 167

Result codes
no Err
bdNamErr
dirNFErr
extFSErr
fnfErr
ioErr
nsvErr
paramErr
The File Manager
No error
Bad file name
Directory not found or incomplete pathname
External file system
File not found
1/0 error
No such volume
No default volume
FUNCTION PBCatMove (paramBlock: CMovePBPtr; async: BOOLEAN)
OSErr;
Trap macro
_CatMove
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
28
ioNewName
pointer
->
36
ioNewDirID
longword
->
48
ioDirID
longword
PBCatMove moves files or directories from one directory to another. The name of the file
or directory to be moved is pointed to by ioN amePtr; io VRefNum contains either the
volume reference number or working directory reference number. A directory ID can be
specified in ioDirID. The name and directory ID of the directory to which the file or
directory is to be moved are specified by ioNewName and ioNewDirlD.
PBCatMove is strictly a file catalog operation; it does not actually change the location of the
file or directory on the disk. PBCatMove cannot move a file or directory to another volume
(that is, io VRefNum is used in specifying both the source and the destination). It also
cannot be used to rename files or directories; for that, use PBHR.ename.
Result codes
no Err
badMovErr
bdNamErr
dupFNErr
fnfErr
ioErr
nsvErr
paramErr
vLckdErr
wPrErr
No error
Attempt to move into offspring
Bad file name or attempt to move into a file
Duplicate file name and version
File not found
1/0 error
No such volume
No default volume
Software volume lock
Hardware volume lock
Low-Level File Manager Routines W-157

<!-- source-page: 168 -->
## Page 168

Inside Macintosh
Working Directory Routines
Warning: The routines described in this section operate only with the hierarchical
version of the File Manager; if used on a Macintosh equipped only with the 64K
ROM version of the File Manager, they will generate a system error.
FUNCTION PBOpenWD (paramBlock: WDPBPtr; async: BOOLEAN)
OSErr;
Trap macro
_OpenWD
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18"
ioNamePtr
pointer
<->
22
ioVRetNum
word
->
28
ioWDProcID
longword
->
48
ioWDDirID
longword
PBOpenWD takes the directory specified by ioVRetNum, ioWDDirlD, and ioWDProcID
and makes it a working directory. (You can also specify the directory using a combination
of partial pathname and directory ID.) It returns a working directory reference number in
io VRetNum that can be used in subsequent calls.
If a given directory has already been made a working directory using the same
ioWDProcID, no new working directory will be opened; instead, the existing working
directory reference number will be returned. If a given directory was already made a
working directory using a different ioWDProclD, a new working directory reference
number is returned.
Result codes
no Err
tmwdoErr
No error
Too many working directories open
FUNCTION PBCloseWD (paramBlock: WDPBPtr; async: BOOLEAN)
Trap macro
_CloseWD
Parameter block
->
12
<-
16
->
22
ioCompletion
pointer
ioResult
word
ioVRetNum
word
OSErr;
PB Close WD releases the working directory whose working directory reference number is
specified in io VRetNum.
Note: If a volume reference number is specified in ioVRetNum, PBCloseWD does
nothing.
Result codes
no Err
nsvErr
No error
No such volume
W-158 Low-Level File Manager Routines

<!-- source-page: 169 -->
## Page 169

The File Manager
FUNCTION PBGetWDInfo (paramBlock: WDPBPtr; async: BOOLEAN) : OSErr;
Trap macro
_GetWDinfo
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
->
26
ioWDindex
word
<->
28
ioWDProcID
long word
<->
32
ioWDVRefNum word
<-
48
ioWDDirID
long word
PBGetWDInfo returns information about the specified working directory. The working
directory can be specified either by its working directory reference number in io VRefNum
(in which case ioWDindex should be 0), or by its index number in ioWDindex. In the
latter case, if ioVRefNum is nonzero, it's interpreted as a volume specification (volume
reference number or drive number), and only working directories on that volume are
indexed.
IOWDVRefNum always returns the volume reference number. IOVRefNum returns a
working directory reference number when a working directory reference number is passed
in that field; otherwise, it returns a volume reference number. The volume name is returned
in ioNamePtr.
If IOWDProcID is nonzero, only working directories with that identifier are indexed;
otherwise all working directories are indexed.
Result codes
no Err
nsvErr
No error
No such volume
DATA ORGANIZATION ON VOLUMES
This section explains how information is organized on volumes. Most of the information is
accessible only through assembly language, but may be of interest to some advanced Pascal
programmers.
The File Manager communicates with device drivers that read and write data via block-level
requests to devices containing Macintosh-initialized volumes. (Macintosh-initialized
volumes are volumes initialized by the Disk Initialization Package.) The actual type of
volume and device is unimportant to the File Manager; the only requirements are that the
volume was initialized by the Disk Initialization Package and that the device driver is able to
communicate via block-level requests.
Data Organization on Volumes IV-159

<!-- source-page: 170 -->
## Page 170

Inside Macintosh
The 3 1/2-inch built-in and optional external drives are accessed via the Disk Driver. The
Hard Disk 20 is accessed via the Hard Disk 20 Driver. If you want to use the File Manager
to access files on Macintosh-initialized volumes on other types of devices, you must write a
device driver that can read and write data via block-level requests to the device on which the
volume will be mounted. If you want to access files on volumes not initialized by the
Macintosh, you must write your own external file system (see the section "Using an
External File System").
The information on all block-formatted volumes is organized in logical blocks and
allocation blocks. Logical blocks contain a number of bytes of standard information (512
bytes on Macintosh-initialized volumes), and an additional number of bytes of information
specific to the device driver (12 bytes on Macintosh-initialized volumes; for details, see the
Disk Driver chapter). Allocation blocks are composed of any integral number of logical
blocks, and are simply a means of grouping logical blocks together in more convenient
parcels. The allocation block size is a volume parameter whose value is set when the
volume is initialized; it cannot be changed unless the volume is reinitialized.
The remainder of this section applies only to Macintosh-initialized volumes; the information
may be different in future versions of Macintosh system software. There are two types of
Macintosh-initialized volumes-flat directory volumes and hierarchical directory volumes.
Other volumes must be accessed via an external file system, and the information on them
must be organized by an external initializing program.
Flat Directory Volumes
A flat directory volume contains system startup information in logical blocks 0 and 1
(see Figure 7) that's read in at system startup. This information consists of certain
configurable system parameters, such as the capacity of the event queue, the initial size of
the system heap, and the number of open files allowed. The development system you 're
using may include a utility program for modifying the system startup blocks on a volume.
Logical block 2 of the volume begins the master directory block. The master directory
block contains volume information and the volume allocation block map, which
records whether each block on the volume is unused or what part of a file it contains data
from.
IV-160 Data Organization on Volumes

<!-- source-page: 171 -->
## Page 171

logical block 0
logical block 1
system startup
information
............ -------------
.
volume information
logical block 2 .......................................................................................... .
············ ···········
block map
···········
logical block 3 ......................................................................................... .
unused
........... · 1-------=-""""'..;;;...o:=..-------t
logical block 4
file directory
logical block n .......................................................................................... .
unused
........... · 1---------------t
Ji cal block n + 1
7
file contents
gical block 799
............ ....__ ___________ __,
The File Manczger
zero if not a startup disk
master di rectory b I ock
al location block 2
al location block m
Figure 7. A 400K Volume With lK Allocation Blocks
The master directory "block" always occupies two blocks-the Disk Initialization Package
varies the allocation block size as necessary to achieve this constraint.
The file directory begins in the next logical block following the block map; it contains
descriptions and locations of all the files on the volume. The rest of the logical blocks on
the volume contain files or garbage (such as parts of deleted files). The exact format of the
volume information, volume allocation block map, and file directory is explained in the
following sections.
Volume Information
The volume information is contained in the first 64 bytes of the master directory block (see
Figure 8). This information is written on the volume when it's initialized, and modified
thereafter by the File Manager.
Data Organization on Volumes IV-161

<!-- source-page: 172 -->
## Page 172

Inside Macintosh
byte 0
2
6
10
12
14
16
18
20
24
28
30
34
36
37
drSigWord (word)
drCrDate (I ong word)
drLsBkUp (I ong word)
drAtrb (word)
drNmFls (word)
drD i rSt (word)
drBILen (word)
drNmAIBlks (word)
drAIBlkSiz (long word)
drClpSiz (long word)
drAIBISt (word)
drNxtfNum (I ong word)
i;lrFreeBks (word)
drVN (byte)
drVN + 1 (bytes)
always $D2D7
date and time of initialization
date and time of last modification
volume attributes
number of f i I es in di rectory
first block of directory
length of directory in blocks
number of allocation blocks
al location block size
number of bytes to a 11 ocate
first al location block in block map
next unused file number
number of unused al location blocks
I ength of vo I ume name
characters of vo I ume name
Figure 8. Volume Information on Flat Directory Volumes
DrAtrb contains the volume attributes, as follows:
8it
Meaning
7
Set if volume is locked by hardware
15
Set if volume is locked by software
DrClpSiz contains the minimum nuJllber of bytes to allocate each time the Allocate function
is called, to minimize fragmentation of files; it's always a multiple of the allocation block
size. DrNxtFNum contains the next unused file number (see the "File Directory" section
below for an explanation of file numbers).
Volume Allocatiop Block Map
The volume allocation block map represents every allocation block on the volume with a
12-bit entry indicating whether the block is unused or allocated to a file. It begins in the
master directory block at the byte following the volume information, and continues for as
many logical blocks as needed.
IV-162 Data Organization on Volumes

<!-- source-page: 173 -->
## Page 173

The File Manager
The first entry in the block map is for block number 2; the block map doesn't contain
entries for the system startup blocks. Each entry specifies whether the block is unused,
whether it's the last block in the file, or which allocation block is next in the file:
Entry
0
1
2-4095
Meaning
Block is unused
Block is the last block of the file
Number of next block in the file
For instance, assume that there's one file on the volume, stored in allocation blocks 8, 11,
12, and 17; the first 16 entries of the block map would read
0 0 0 0 0 0 11 0 0 12 17 0 0 0 0 1
The first allocation block on a volume typically follows the file directory. It's numbered 2
because of the special meaning of numbers 0 and 1.
Note: As explained below, it's possible to begin the allocation blocks immediately
following the master directory block and place the file directory somewhere within
the allocation blocks. In this case, the allocation blocks occupied by the file directory
must be marked with $FFF's in the allocation block map.
Flat file Directory
The file directory contains an entry for each file. Each entry lists information about one file
on the volume, including its name and location. Each file is listed by its own unique file
m,1mber, which the File Manager uses to distinguish it from other files on the volume.
A file directory entry contains 51 bytes plus one byte for each character in the file name. If
th(( file names average 20 characters, a directory can hold seven file entries per logical
block. Entries are always an integral number of words and don't cross logical block
boundaries. The le11gth of a file directory depends on the maximum number of files the
volume can contain; for example, on a 400K volume the file directory occupies 12 logical
blocks.
The file directory conventionally follows the block map and precedes the allocation blocks,
but a volume-initializing program could actually place the file directory anywhere within the
allocation blocks as long as the blocks occupied by the file directory are marked with
$FFF' s in the block map.
The format of a file directory entry is shown in Figure 9.
Data Organization on Volumes IV-163

<!-- source-page: 174 -->
## Page 174

Inside Macintosh
byte O
1
2
18
22
24
28
32
34
38
42
46
50
51
flFlags (byte)
flTyp (byte)
flUsrWds (16 bytes)
flFINum (long word)
f I StB I k (word)
fllglen (long word)
flPylen (long word)
flRStBlk (word)
flRLgLen (long word)
f I RPylen (I ong word)
f I Croat (I ong word)
flMdDat (long word)
flNam (byte)
fl Nam+ 1 (bytes)
bit 7=1 if entry used; bit O = 1 if file locked
version number
information used by the Finder
file number
first al location block of data fork
logical end-of-file of data fork
physical end-of-file of data fork
first al location block of resource fork
logical end-of-file of resource fork
physical end-of-file of resource fork
date and time of creation
date and time of last modification
length of file name
characters of f i I e name
Figure 9. A File Directory Entry
FlStBlk and flRStBlk are 0 if the data or resource fork doesn't exist. FlCrDat and flMdDat
are given in seconds since midnight, January 1, 1904.
Each time a new file is created, an entry for the new file is placed in the file directory. Each
time a file is deleted, its entry in the file directory is cleared, and all blocks used by that file
on the volume are released.
Hierarchical· Directory Volumes
A hierarchical directory volume contains system startup information in logical blocks
0 and 1 (see Figure 10) that's read in at system startup. This information is similar to the
system startup information for flat directory volumes; it consists of certain configurable
system parameters, such as the capacity of the event queue, the initial size of the system
heap, and the number of open files allowed.
IV-164 Data Organization on Volumes

<!-- source-page: 175 -->
## Page 175

logical block 0
logical block 1
system startup
information
············1--------------t
logical block 2
volume information
············i--------------4
logical block 3
· · · · · · · · · · · ·7 .. · · · .. · · · volume bit map · · · ·· · · · · · 7
logical block n .......................................................................................... .
unused
············1--------------t
logical block n + 1
file contents
logical block 1599
············"--------------'
The File Manager
zero if not a startup disk
volume information block
al location block 2
al location block m
Figure 10. An 800K Volume With lK Allocation Blocks
Logical block 2 of the volume (also known as the volume information block) contains
the volume information. This volume information is a superset of the volume
information found on flat directory volumes. Logical block 3 of the volume begins the
volume bit map, which records whether each block on the volume is used or unused.
The rest of the logical blocks on the volume contain files or garbage (such as parts of
deleted files).
The volume bit map on hierarchical directory volumes replaces the volume allocation block
map used on flat directory volumes. While the bit map does handle volume space
management (as does the block map), it does not handle file mapping. A separate file,
known as the extents tree file, performs this function. Finally, a file known as the
catalog tree file is responsible for maintaining the hierarchical directory structure; it
corresponds in function to the file directory found on flat directory volumes.
The exact format of the volume information, volume bit map, extents tree file, and catalog
tree file is explained in the following sections. The discussion of the extents tree and
catalog tree files is preceded by a short introduction to a data structure known as a B*-tree
that's used to organize and access the information in these files.
Data Organization on Volwnes IV-165

<!-- source-page: 176 -->
## Page 176

Inside Macintosh
Volume Information
The volume information is contained in the first 104 bytes of the volume information block
(see Figure 11). This information is written on the volume when it's initialized, and
modified thereafter by the File Manager.
byte 0
2
6
10
12
14
16
18
20
24
28
30
34
36
37
64
68
70
74
78
82
84
88
92
124
126
128
130
134
146
150
drSigWord (word)
drCrDate (I ong word)
drLsMod (long word)
dr A trb (word)
drNmFls (word)
drVBMSt (word)
drAI locPtr (word)
drNmAIBlks (word)
drAIBlkSiz (long word)
drClpSiz (long word)
drAIBISt (word)
drNxtCN ID (I ong word)
drFreeBks (word)
drVN (byte)
drVN + 1 (bytes)
drVolBkUp (long word)
drVSeq Num (word)
drWrCnt (I ong word)
drXTClpSiz (long word)
drCTC I pS i z (I ong word)
drNmRtDirs (word)
drFi ICnt (long word)
drD i rent (I ong word)
drfndrlnfo (32 bytes)
drVCS i ze (word)
drVCBMS i ze (word)
drCtlCSize (word)
drXTFISize (long word)
drXTExtRec (12 bytes)
drCTFISize (long word)
drCTE xtRec (12 bytes)
always $4244
date and time of initialization
date and time of last modification
vo I ume attributes
number of files in directory
first block of volume bit map
used i nterna 11 y
number of al location blocks
allocation block size
default clump size
first block in bit map
next unused directory ID or file number
number of unused a 11 ocat ion b I ocks
length of volume name
characters of vo I ume name
date and time of last backup
used i nterna 11 y
volume write count
clump size of extents tree file
clump size of catalog tree file
number of directories in root
number of files on volume
number of directories on volume
information used by the Finder
used internally
used i nterna 11 y
used internally
I ength of extents tree (LE OF and PE OF)
extent record for extents tree
length of catalog tree (LEOF and PEOF)
first extent record for catalog tree
Figure 11. Volume Information on Hierarchical Directory Volumes
IV-166 Data Organization on Volumes

<!-- source-page: 177 -->
## Page 177

The File Manager
64K ROM note: The volume information on a flat directory volume is a subset of
the hierarchical volume information. The flat directory volume information contains
only the fields up to and including drVN+ 1. In addition, the names of several fields
have been changed in the hierarchical volume information to reflect their new
function: drLsBkUp, drDirSt, drBlLn, and drNxtFNum have been changed to
drLsMod, drVBMSt, drAllocPtr, and drNxtCNID respectively. All of the offsets of
the flat directory volume information, however, have been preserved to maintain
compatibility.
DrLsMod contains the date and time that the volume was last modified (this is not
necessarily when it was flushed).
64K ROM note: DrLsMod replaces the field drLsBkUp from flat directory
volumes. The name drLsBkUp was actually a misnomer; this field has always
contained the date and time of the last modification, not the last backup. Another
field, drVolBkUp, contains the date and time of the last backup.
DrVBMSt replaces the field drDirSt; it contains the number of the first block in the volume
bitmap.
DrAtrb contains the volume attributes, as follows:
Bit
Meaning
7
Set if volume is locked by hardware
15
Set if volume is locked by software
DrClpSiz contains the default clump size for the volume. To promote file contiguity and
avoid fragmentation, space is allocated to a file not in allocation blocks but in clumps. A
clump is a group of contiguous allocation blocks. The clump size is always a multiple of
the allocation block size; it's the minimum number of bytes to allocate each time the
Allocate function is called or the end-of-file is reached during the Write routine. A clump
size can be set when a particular file is opened, and can also be changed subsequently. If
no clump size is specified, the value found in drClpSiz will be used.
DrNxtCNID replaces the field drNxtFNum; it's either the next file number or the next
directory ID to be assigned.
Warning: The format of the volume information may be different in future versions
of Macintosh system software.
Volume Bit Map
The flat directory file system uses the volume allocation block map to provide both volume
space management and file mapping; the hierarchical file system instead uses a volume bit
map. The block map contains a 12-bit entry for each allocation block. If an entry is 0, the
corresponding allocation block is unused. If an allocation block is allocated to a file, its
block map entry is nonzero, and can be used to find the next allocation block used by that
file.
Data Organization on Volwnes IV-167

<!-- source-page: 178 -->
## Page 178

lnJide Macintosh
The File Manager keeps the entire block map in memory. The size of the block map is
obviously a function of the number of allocation blocks on the volume. Similarly, the
number of allocation blocks depends on the allocation block size. For larger volumes, the
allocation block size must be increased in order to keep the block map to a reasonable size.
A tradeoff occurs between waste of space and speed of file access in this situation.
Obviously, the use of large allocation blocks can waste disk space, particularly with small
files. On the other hand, using smaller allocation blocks increases the size of the block
map; this means the entire block map cannot be kept in memory at one time, resulting in a
time-consuming sector-caching scheme.
The hierarchical file system discards the block map concept entirely, and instead uses a
structure known as the volume bit map. The bit map has one bit for each allocation
block on the volume; if a particular block is in use, its bit is set.
With extremely large volumes, the same space/time tradeoff can become an issue. In
general, it's desirable to set the allocation block size such that the entire bit map can be kept
in memory at all times.
B*-Trees
This section describes the B*-tree implementation used in the extents tree and catalog tree
files. The data structures described in this section are accessible only through assembly
language; an understanding of the B*-tree data structure is also assumed.
The nodes of a B*-tree contain records; each record consists of certain information (either
pointers or data) and a key associated with that information (see Figure 12). A basic
feature of the B*-tree is that data is stored only in the leaf nodes. The internal nodes (also
known as index nodes) contain pointers to other nodes; they provide an index, used in
conjunction with a search key, for accessing the data records stored in the leaf nodes.
key length
key
data or pointer
(1 byte)
(up to 255 bytes)
(limited only by size of node)
Figure 12. A B*-Tree Node Record
Within each node, the records are maintained so that their keys are in ascending order.
Figure 13 shows a sample B*-tree; hypothetical keys have been inserted to illustrate the
structure of the tree and the relationship between index and leaf nodes.
IV-168 Data Organization on Volumes

<!-- source-page: 179 -->
## Page 179

.._ index nodes
I
The File Manager
15 data
19 data
23 data 25 data
....,,,,_
/
leaf nodes
Figure 13. A Sample B*-Tree
When a data record is needed, thy kyy of the desired record (the search key) is provided.
The search begins at the root node (which is an index node, unless the tree has only one
level), moving from on.e record to the next until the record with the highest key that's less
than or equal to the search key is reached. The pointer of that record leads to another node,
one level down in the tree. This process continues until a leaf node is reached; its records
are examined until the desired key is found. (The desired key may not be found; in this
case, the search stops when a key larger than the search key is reached.) Figure 14 shows
a sample B*-tree search path; the arrows indicate the path to the second record in the
second leaf node.
I search key ~ 15 I~
l 8 l pointer j 1 s I pointer I
\
8 I pointer I 13 I pointer I I 1 s I pointer I 23 I pointer I
~
8 I data I 10 I data l l 13 I data l 15 I data I l 16 I data I 19 I data 11 23 I data I 25 I data I
Figure 14. A Sample B*-Tree Search Path
All nodes in the B*-tree are of the same fixed size; the structure of a node is shown in
Figure 15.
Data Organization on Volumes IV-169

<!-- source-page: 180 -->
## Page 180

Inside Macintosh
node
descriptor
records
record
offsets {
ndFLi nk (I ong word)
ndBLink (long word)
ndType (byte)
ndleve I (byte)
ndNRecs (word)
IL
~
record 0
~
record 1
IL
I'
free space
offset to free space
1--
offset to record 1
I---
offset to record 0
Figure 15. Structure of a B*-Tree Node
Each node begins with the node descriptor. NDNRecs contains the number of records
currently in the node. NDType indicates the type of node; it contains $FF if it's a leaf node
and 0 if it's an index node. NDLevel indicates the level of the node in the tree; leaf nodes
are always at level 1, the first level of index nodes above them are at level 2, and so on.
NDBLink and ndFLink: are used only with leaf nodes as a way of quickly moving through
the data records; for each leaf node, they contain pointers to the previous and subsequent
leaf nodes respectively.
The records in a node can be of variable length; for this reason, offsets to the beginning of
each record are needed. The records begin after the field ndNRecs; they're followed by the
unused space. The off sets to the records begin at the end of the node and work backwards;
they're followed by an offset to the unused space.
Extents Tree File
File mapping information (or the location of a file's data on the volume) is contained in the
extents tree file. A file extent is a series of contiguous allocation blocks. Ideally, a file
would be stored in a single extent. Except in the case of preallocated or small files,
however, the contents of a particular file are usually stored in more than one extent on
different parts of a given volume. The extents tree file, organized as a B*-tree, records the
volume location and size of the various extents that comprise a file.
W-170 Data Organization on Volwnes

<!-- source-page: 181 -->
## Page 181

The File Manager
Each extent on a volume is identified by an extent descriptor; each descriptor consists of
the number of the first allocation block of the extent followed by the length of the extent in
blocks (see Figure 16).
number of extent's first al location block (word)
number of al location blocks in extent (word)
= ...
Figure 16. Extent Descriptor
The extent descriptors are stored in extent records in the leaf nodes of the tree. Each
extent record consists of a key followed by three extent descriptors. The extent records are
kept sorted by the key, which has the format shown in Figure 18.
byte O
1
2
6
xkrKeylen (byte)
xkrFkType (byte)
::ii::krFNum (long word)
xkrFABN (word)
key I ength in bytes
$00 for data fork; $FF for resource fork
file number
al location block number within file
Figure 17. Extents Key
Catalog Tree File
The catalog tree file corresponds in function to the flat file directory found on volumes
formatted by the 64K ROM. Whereas a flat file directory contains entries for files only, the
catalog tree file contains three types of records-file records, directory records, and thread
records. (Threads can be viewed as the branches connecting the nodes of a catalog tree.)
The catalog tree file is organized as a B *-tree; all three types of records are stored in the leaf
nodes. The index nodes contain the index records used to search through the tree.
The catalog tree records consist of a key followed by the file, directory, or thread record.
The records are kept sorted by key. The exact format of the key is shown in Figure 18.
byte 0
1
2
6
ckrKeylen (byte)
key length in bytes
ckrResrv1 (byte)
used i nterna 11 y
ckrPar ID (I ong word)
parent ID
ckrCName (bytes)
file or directory name
Figure 18. Catalog Key
Data Organization on Volumes W-171

<!-- source-page: 182 -->
## Page 182

Inside Macintosh
A file record is a superset of the file directory entry found on volumes formatted by the
64K ROM; its contents are shown in Figure 19.
byte O
1
2
3
4
20
24
26
30
34
36
40
44
48
52
56
72
74
86
98
cdrType (byte)
cdrResrv2 (byte)
f i I Flags (byte)
f i ITyp (byte)
fi IUsrWds (16 bytes)
fi IFINum (long word)
fi IStBlk (word)
fi llglen (long word)
f i I Pylen (I ong word)
fi IRStBlk (word)
f i I Rlglen (I ong word)
f i I RPylen (I ong word)
fi ICrDat (long word)
f i IMdDat (long word)
fi IBkDat (long word)
fi IFndrlnfo (16 bytes)
f i IClpSize (word)
f i IExtRec (12 bytes)
f i I RE xtRec (12 bytes)
f i I Resrv (I ong word)
always 2 for file records
used internally
bit 7=1 if record used; bit O = 1 if file locked
file type
information used by the Finder
file number
first al location block of data fork
logical end-of-file of data fork
physical end-of-file of data fork
first al location block of resource fork
I og i ca I end-of-f i I e of resource fork
physical end-of-file of resource fork
date and ti me of creation
date and time of last modification
date and time of last backup
additional information used by the Finder
file clump size
first extent record for data fork
first extent record for resource fork
used internally
Figure 19. File Record
A directory record records information about a single directory; the format of a directory
record is shown in Figure 20.
IV-172 Data Organization on Volumes

<!-- source-page: 183 -->
## Page 183

byte 0
1
2
4
6
10
14
18
22
38
54
cdrType (byte)
cdrResrv2 (byte)
di rF I ags (word)
dirVal (word)
dirDirlD (long word)
dirCrDat (long word)
di rMdDat (I ong word)
dirBkDat (long word)
di rUsr Info (16 bytes)
di rFndr Info (16 bytes)
di rResrv (16 bytes)
a I ways 1 for di rectory records
used internally
flags
valence
directory ID
date and time of creation
The File Manager
date and time of last modification
date and time of last backup
information used by the Finder
additional information used by the Finder
used internally
Figure 20. Directory Record
Thread records are used in conjunction with directory records to provide a link between a
given directory and its parent. For any given directory, the records describing all of its
offspring are stored contiguously. A thread record precedes each set of offspring; it
contains the directory ID and name of the parent and provides a path to the parent's
directory record. The format of a thread record is shown in Figure 21.
byte O
cdrType (byte)
always 3 for thread records
1
cdrResrv2 (byte)
used internally
2
thdResrv (8 bytes)
used internally
10
thdParlD (long word)
parent ID of associated di rectory
14
thdCName (bytes)
name of associated directory
Figure 21. Thread Record
Data Organization on Volumes IV-173

<!-- source-page: 184 -->
## Page 184

Inside Macintosh
A portion of a sample tree, along with the corresponding file, directory, and thread records,
is shown in Figure 22.
<0> MyVol
dirlD = 1
di rectory record
<1>
parentlD = O
thread record
name = MyVol
<1 >FBI
file record
' ' '
<1> Mail
dirlD = 35
di rectory record
<1> IRS
file record
' ' '
Jody
Bob
<35>
parentlD = 1
thread record
name = Mail
<35> Bob
file record
' ' '
<35> Jody
' ' '
file record
Figure 22. Sample Tree, with Catalog Tree Records
DATA STRUCTURES IN MEMORY
This section describes the memory data structures used by the File Manager and any
external file system that accesses files on Macintosh-initialized volumes. Some of this data
is accessible only through assembly language.
IV-174 Data Structures in Memory

<!-- source-page: 185 -->
## Page 185

The File Manager
The data structures in memory used by the File Manager and all external file systems
include:
• the file I/O queue, listing all asynchronous routines awaiting execution (including the
currently executing routine, if any)
• the volume-control-block queue, listing information about each mounted volume
• a copy of the volume bit map for each on-line volume (volume allocation block map
for flat directory volumes)
• the file-control-block buffer, listing information about each access path
•volume buffers (one for each on-line volume)
• optional access path buffers (one for each access path)
• the drive queue, listing information about each drive connected to the Macintosh
The File 1/0 Queue
The file I/O queue is a standard Operating System queue (described in the Operating
System Utilities chapter) that contains parameter blocks for all asynchronous routines
awaiting execution. Each time a routine is called, an entry is placed in the queue; each time
a routine is completed, its entry is removed from the queue.
Each entry in the file I/O queue consists of a parameter block for the routine that was called.
Most of the fields of this parameter block contain information needed by the specific File
Manager routines; these fields are explained above in the section "Low-Level File Manager
Routines". The first four fields of the parameter block, shown below, are used by the File
Manager in processing the I/O requests in the queue.
TYPE ParamBlockRec = RECORD
qLink:
qType:
ioTrap:
ioCmd.Addr:
END;
QElemPtr;
INTEGER;
INTEGER;
Ptr;
{next queue entry}
{queue type}
{routine trap}
{routine address}
{rest of block}
QLink points to the next entry in the queue, and qType indicates the queue type, which
must always be ORD(ioQType). IOTrap and ioCrndAddr contain the trap word and
address of the File Manager routine that was called.
You can get a pointer to the header of the file I/O queue by calling the File Manager
function GetFSQHdr.
FUNCTION GetFSQHdr : QHdrPtr;
[NotinROM]
GetFSQHdr returns a pointer to the header of the file I/O queue.
Data Structures in Memory IV-175

<!-- source-page: 186 -->
## Page 186

Inside Macintosh
Assembly-language note: The global variable FSQHdr contains the header of
the file I/O queue.
Volume Control Blocks
Each time a volume is mounted, its volume information is read from it and is used to build
a new volume control block in the volume-control-block queue (unless an ejected
or off-line volume is being remounted). A copy of the volume block map is also read from
the volume and placed in the system heap, and a volume buffer is created in the system
heap.
The volume-control-block queue is a standard Operating System queue that's maintained in
the system heap. It contains a volume control block for each mounted volume. A volume
control block is a 178-byte nonrelocatable block that contains volume-specific information.
It has the following structure:
TYPE VCB =
RECORD
qLink:
QElemPtr;
qType:
INTEGER;
vcbFlags:
INTEGER;
vcbSigWord:
INTEGER;
vcbCrDate:
LONGINT;
vcbLsMod:
LONGINT;
vcbAtrb:
INTEGER;
vcbNmFls:
INTEGER;
vcbVBMSt:
INTEGER;
vcbAllocPtr: INTEGER;
vcbNmAlBlks: INTEGER;
vcbAlBlkSiz: LONGINT;
vcbClpSiz:
LONGINT;
vcbAlBlSt:
INTEGER;
vcbNxtCNID:
LONGINT;
vcbFreeBks:
INTEGER;
vcbVN:
STRING[27];
vcbDrvNum:
INTEGER;
vcbDRefNum:
INTEGER;
vcbFSID:
INTEGER;
vcbVRefNum:
INTEGER;
vcbMAdr:
Ptr;
vcbBufAdr:
Ptr;
vcbMLen:
INTEGER;
vcbDirindex: INTEGER;
vcbDirBlk:
INTEGER;
vcbVolBkUp:
LONG INT;
vcbVSeqNum:
INTEGER;
vcbWrCnt:
LONGINT;
vcbXTClpSiz: LONGINT;
vcbCTClpSiz: LONGINT;
vcbNmRtDirs: INTEGER;
vcbFilCnt:
LONGINT;
vcbDirCnt:
LONGINT;
IV-176 Data Structures in Memory
{next queue entry}
{queue type}
{bit 15=1 if dirty}
{$4244 for hierarchical, $D2D7 for flat}
{date and time of initialization}
{date and time of last modification}
{volume attributes}
{number of files in directory}
{first block of volume bit map}
{used internally}
{number of allocation blocks}
{allocation block size}
{default clump size}
{first block in block map}
{next unused directory ID or file number}
{number of unused allocation blocks}
{volume name}
{drive number}
{driver reference number}
{file-system identifier}
{volume reference number}
{pointer to block map}
{pointer to volume buffer}
{number of bytes in block map}
{used internally}
{used internally}
{date and time of last backup}
{used internally}
{volume write count}
{clump size of extents tree file}
{clump size of catalog tree file}
{number of directories in root}
{number of files on volume}
{number of directories on volume}

<!-- source-page: 187 -->
## Page 187

vcbFndrinfo: ARRAY[l .. 8]
vcbVCSize:
vcbVBMCSiz:
vcbCtlCSiz:
vcbXTAlBks:
vcbCTAlBks:
vcbXTRef:
vcbCTRef:
vcbCtlBuf:
vcbDirIDM:
vcbOffsM:
END;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
Ptr;
LONGINT;
INTEGER
The File Manager
OF LONGINT;
{information used by the }
{ Finder}
{used internally}
{used internally}
{used internally}
{size in blocks of extents tree file}
{size in blocks of catalog tree file}
{path reference number for extents tree
{ file}
{path reference number for catalog tree
{ file}
{pointer to extents and catalog tree
{ caches}
{directory last searched}
{offspring index at last search}
64K ROM note: A volume control block created for a flat volume is a subset of
the above structure. It's actually smaller and contains only the fields up to and
including vcbDirBlk. In addition, the names of several fields have been changed to
reflect the fact that they contain different information on hierarchical volumes:
vcbLsBkUp, vcbDirSt, vcbBlLn, vcbNmBlks, and vcbNxtFNum have been
changed to vcbLsMod, vcb VBMSt, vcbAllocPtr, vcbNmAIBlks, and vcbNxtCNID
respectively.
QLink points to the next entry in the queue, and qType indicates the queue type, which
must always be ORD(fsQType). Bit 15 ofvcbFlags is set if the volume information has
been changed by a routine call since the volume was last affected by a Flush Vol call.
VCBLsMod contains the date and time that the volume was last modified (this is not
necessarily when it was flushed).
64K ROM note: VCBLsMod replaces the field vcbLsBkUp from flat directory
volumes. The name vcbLsBkUp was actually a misnomer; this field has always
contained the date and time of the last modification, not the last backup. Another
field, vcb VolBkUp, contains the date and time of the last backup.
VCBAtrb contains the volume attributes, as follows:
Bit
Meaning
0-4
Set if inconsistencies were found between the volume information and the file
directory when the volume was mounted
6
Set if volume is busy (one or more files are open)
7
Set if volume is locked by hardware
15
Set if volume is locked by software
VCBVBMSt contains the number of the first block in the volume bit map; on flat volumes,
it contains the first block of the file directory. VCBNmAIBlks contains the number of
allocation blocks on the volume, and vcbFreeBks specifies how many of those blocks are
unused. VCBAIBlSt is used only with flat volumes; it contains the number of the first
block in the block map.
Data Structures in Memory IV-177

<!-- source-page: 188 -->
## Page 188

Inside Macintosh
VCBDrvNum contains the drive number of the drive on which the volume is mounted;
vcbDRefNum contains the driver reference number of the driver used to access the volume.
When a mounted volume is placed off-line, vcbDryNum is cleared. When a volume is
ejected, vcbDrvNum is cleared and vcbDRefNum is set to the negative of vcbDrvNum
(becoming a positive number). VCBFSID identifies the file system handling the volume;
it's 0 for volumes handled by the File Manager, and nonzero for volumes handled by other
file systems.
When a volume is placed off-line, its buffer and bit map (or block map, in the case of flat
directory volumes) are released. Whert a volume is unmounted, its volume control block is
removed from the volume-control-block queue.
You can get a pointer to the header of the volume-control-block queue by calling the File
Manager function GetVCBQHdr.
FUNCTION GetVCBQHdr : QHdrPtr;
[Not in ROM]
GetVCBQHdr returns a pointer to the header of the volume-control-block queue.
Assembly-language note: The global variable VCBQHdr contains the header of
the volume-control-block-queue. The default volµme's volume control block is
pointed to by the global variable DefVCBPtr.
File Control Blocks
Each time a file is opened, the file's directory entry is used to build a file control block
in the file-control-block buffer, which contains information about all access paths.
The file-control-block-buffer is a nonrelocatable block in the system heap; the first word
contains the length of the buffer.
The number of file tontrol blocks is contained in the system startup information on a
volume. With the 64K ROM, the standard number is 12 file control blocks on a Macintosh
128K and 4~ file control blocks on the Macintosh 512K. With the 128K ROM, there's a
standard of 40 file control blocks per volume.
Each open fork of a file requires one access path. Two access paths are used for the
system and application resource files (whose resource forks are always open). On
hierarchical directory volumes, two access paths are also needed for the extents and catalog
trees. You should keep such files in mind when calculating the number of files that can be
opened by your applicatfon.
Note: The size of the file-control-block buffer is determined by the system startup
information stored on a volume.
You can get information from the file control block allocated for an open file by calling the
File Manager function PBGetFCBInfo. When you call PBGetFCBInfo, you'll use the
IV-178 Data Structures in Memory

<!-- source-page: 189 -->
## Page 189

The File Manager
following 12 additional fields after the standard eight fields in the parameter block record
FCBPBRec:
ioRefNum:
INTEGER;
filler:
IN~EGER;
{path reference number}
{not used}
ioFCBindx:
LONGINT;
{FCB index}
ioFCBFlNm:
LONGINT;
{file number}
{flags}
ioFCBFlags:
INTEGER;
ioFCBStBlk:
INTEGER;
ioFCBEOF:
LONGINT;
{first allocation block of file}
{logical end-of-file}
ioFCBPLen:
LONGINT;
{physical end-of-file}
ioFCBCrPs:
LONGINT;
{mark}
ioFCBVRefNum: INTEGER;
ioFCBClpSiz: LONGINT;
ioFCBParID:
LONG INT;
{volume reference number}
{file clump size}
{parent directory ID}
FUNCTION PBGetFCBInfo (paramBlock: FCBPBPtr; async: BOOLEAN)
OSErr;
Trap macro
_GetFCBinfo
Parameter block
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
<->
24
ioRefNum
word
->
28
ioFCBindx
long word
<-
32
ioFCBFlNm
long word
<-
36
ioFCBFlags
word
<-
38
ioFCBStBlk
word
<-
40
ioFCBEOF
longword
<-
44
ioFCBPLen
long word
<-
48
ioFCBCrPs
longword
<-
52
ioFCBVRefNum word
<-
54
ioFCBClpSiz
long word
<-
58
ioFCBParID
long word
P.BGetFCBinfo returns information about the specified open file. If ioFCBindx is
positive, the File Manager returns inf ormatioh about the file whose file number is
ioFCBindx on the volume specified by ioVRefNum (which may contain a drive number,
volume reference number~ or working directory reference number). If io VRefNum is 0, all
open files are indexed; otherwise, only open files on the specified volume are indexed.
If ioFCBindx is 0, the File Manager returns information about the file whose access path is
specified by ioRefNum.
Assembly-language note: The global variable FCBSPtr points to the length
word of the file-control-block buffer.
Data Structures in Memory lV-179

<!-- source-page: 190 -->
## Page 190

Inside Macintosh
Each file control block contains 94 bytes of information about an access path; Figure 23
shows its structure (using the assembly-language offsets).
byte O
4
5
6
8
12
16
20
24
28
30
34
38
50
54
58
62
fcbF I Num (I ong word)
fcbMdRByt (byte)
fcbTypByt (byte)
fcbSBlk (word)
f cbE OF (I ong word)
f cbPLen (I ong word)
fcbCrPs (long word)
fcbVPtr (pointer)
fcbBfAdr (pointer)
fcbFIPos (word)
fcbClmpSize (long word)
fcbBTCBPtr (long word)
fcbExtRec (12 bytes)
f cbFType (I ong word)
fcbCatPos (long word)
fcbDirlD (long word)
fcbCName (bytes)
file number
flags
version number
first al location block of file
logical end-of-file
physical end-of-file
mark
pointer to vo I ume contro I b I ock
pointer to access path buffer
used internally
file clump size
pointer to B*-tree control block
first three file extents
file's finder type bytes
used internally
file's parent ID
name of open file
Figure 23. A File Control Block
64K ROM note: The structure of a file control block in the 64K ROM version of
the File Manager is a subset of the above structure. The old file control block
contained only the fields up to and including fcbFlPos.
FCBMdRByt (which corresponds to ioFCBFlags in the parameter block for
PBGetFCBInfo) contains flags that describe the status of the file, as follows:
Bit
Meaning
0
Set if data can be written to the file
1
Set if the entry describes a resource fork
7
Set if the file has been changed since it was last flushed
W-180 Data Structures in Memory

<!-- source-page: 191 -->
## Page 191

The File Manager
Warning: The size and structure of a file control block may be different in future
versions of Macintosh system software.
The Drive Queue
Disk drives connected to the Macintosh are opened when the system starts up, and
information describing each is placed in the drive queue. This is a standard Operating
System queue, and each entry in it has the following structure:
TYPE DrvQEl = RECORD
qLink:
qType:
dQDrive:
dQRefNum:
dQFSID:
dQDrvSz:
dQDrvSz2:
END;
QElemPtr;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
{next queue entry}
{queue type}
{drive number}
{driver reference number}
{file-system identifier}
{number of logical blocks}
{ on drive}
{additional field to handle}
{ large drive size}
QLink points to the next entry in the queue. If qType is 0, this means the number of logical
blocks on the drive is contained in the dQDrvSz field alone. If qType is 1, both dQDrvSz
and dQDrvSz2 are used to store the number of blocks; dqDrvSz2 contains the high-order
word of this number and dQDrvSz contains the low-order word.
DQDrive contains the drive number of the drive on which the volume is mounted;
dQRefNum contains the driver reference number of the driver controlling the device on
which the volume is mounted. DQFSID identifies the file system handling the volume in
the drive; it's 0 for volumes handled by the File Manager, and nonzero for volumes
handled by other file systems.
Four bytes of flags precede each drive queue entry; they're accessible only from assembly
language.
Assembly-language note: These bytes contain the following:
Byte
Contents
0
Bit 7=1 if volume is locked
1
0 if no disk in drive; 1 or 2 if disk in drive; 8 if nonejectable disk in drive;
$FC-$FF if disk was ejected within last 1.5 seconds; $48 if disk in drive
is nonejectable but driver wants a call
2
Used internally during system startup
3
Bit 7 =0 if disk is single-sided
You can get a pointer to the header of the drive queue by calling the File Manager function
GetDrvQHdr.
Data Structures in Memory IV-181

<!-- source-page: 192 -->
## Page 192

Inside Macintosh
FUNCTION GetDrvQHdr : QHdrPtr;
[NotinROM]
GetDrvQHdr returns a pointer to the header of the drive queue.
Assembly-language note: The global variable DrvQHdr contains the header of
the drive queue.
The drive queue can support any number of drives, limited only by memory space.
USING AN EXTERNAL FILE SYSTEM
Due to the complexity of writing an external file system for the 128K ROM version of the
File Manager, this subject is covered in a separate document. To receive a copy, write to:
Developer Technical Support
Mail Stop 3-T
Apple Computer, Inc.
20525 Mariani Avenue
Cupertino, CA 95014
W-182 Using an External File System

<!-- source-page: 193 -->
## Page 193

The File Manager
SUMMARY OF THE FILE MANAGER
Constants
CONST { Flags in file information used by the Finder }
fOnDesk
1;
{set if file is on desktop (hierarchical }
{ volumes only) }
fHasBundle
8192;
{set if file has a bundle}
finvisible
16384;
{set if file's icon is invisible}
fTrash
-3;
{file is in Trash window}
fDesktop
-2;
{file is on desktop}
fDisk
0;
{file is in disk window}
{ Values for requesting read/write permission}
fsCurPerm
0;
{whatever is currently allowed}
fsRdPerm
1;
{request for read permission only}
fsWrPerm
2;
{request for write permission only}
fsRdWrPerm
3;
{request for exclusive read/write permission}
fsRdWrShPerm
4;
{request for shared read/write permission}
{ Positioning modes
fsAtMark
fsFromStart
fsFromLEOF
fsFromMark
rdVerify
0;
{at current mark}
1;
{set mark relative to beginning of file}
2;
{set mark relative to logical end-of-file}
3;
{set mark relative to current mark}
64; {add to above for read-verify}
Data Types
TYPE Finf o = RECORD
fdType:
fdCreator:
fdFlags:
fdLocation:
fdFldr:
END;
OS Type;
OSType;
INTEGER;
Point;
INTEGER
{file type}
{file's creator}
{flags}
{file's location}
{file's window}
FXInfo = RECORD
fdiconID:
INTEGER; {icon ID}
fdUnused:
ARRAY[l .. 4] OF INTEGER; {reserved}
fdComment:
INTEGER; {comment ID}
fdPutAway:
LONGINT; {home directory ID}
END;
Summary of the File Manager IV-183

<!-- source-page: 194 -->
## Page 194

Inside Macintosh
Dinfo =RECORD
frRect:
Rect;
frFlags:
INTEGER;
{folder's rectangle}
{flags}
frLocation: Point;
frView:
INTEGER;
{folder's location}
{folder's view}
END;
DXInfo =RECORD
frScroll:
Point;
frOpenChain: LONGINT;
{scroll position}
{directory ID chain of open }
{ folders}
frUnused:
frComment:
frPutAway:
INTEGER;
INTEGER;
LONGINT;
{reserved}
{comment ID}
{directory ID}
END;
ParamBlkType
(ioParam,fileParam,volumeParam,cntrlParam);
ParmBlkPtr
AParamBlockRec;
ParamBlockRec
RECORD
qLink:
QElemPtr;
qType:
INTEGER;
ioTrap:
INTEGER;
ioCmdAddr:
Ptr;
ioCompletion: ProcPtr;
ioResult:
OSErr;
ioNamePtr:
StringPtr;
ioVRefNum:
INTEGER;
CASE ParamBlkType OF
ioParam:
(ioRefNum:
ioVersNum:
ioPermssn:
ioMisc:
ioBuffer:
ioReqCount:
ioActCount:
ioPosMode:
ioPosOffset:
fileParam:
(ioFRefNum:
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
ioFlVersNum:
ioFlFndrinfo:
ioFlNum:
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
INTEGER;
SignedByte;
SignedByte;
Ptr;
Ptr;
LONGINT;
LONGINT;
INTEGER;
LONGINT);
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
W-184 Summary of the File Manager
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive }
{ number, or working directory }
{ reference number}
{path reference number}
{version number}
{read/write permission}
{miscellaneous}
{data buffer}
{requested number.of bytes}
{actual number of bytes}
{positioning mode and newline
{ character}
{positioning offset}
{path reference number}
{version number}
{not used}
{directory index}
{file attributes}
{version number}
{information used by the Finder}
{file number}
{first allocation block of data fork}
{logical end-of-file of data fork}
{physical end-of-file of data fork}
{first allocation block of resource
{ fork}
{logical end-of-file of resource fork}

<!-- source-page: 195 -->
## Page 195

ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
volumeParam:
(filler2:
ioVolindex:
ioVCrDate:
ioVLsBkUp:
ioVAtrb:
ioVNmFls
ioVDirSt:
ioVBlLn:
ioVNmAlBlks:
ioVAlBlkSiz:
ioVClpSiz:
ioAlBlSt:
ioVNxtFNum:
ioVFrBlk:
cntrlParam:
LONGINT;
LONGINT;
LONGINT);
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER);
The File Manager
{physical end-of-file of resource
{ fork}
{date and time of creation}
{date and time of last modification}
{not used}
{volume index}
{date and time of initialization}
{date and time of last modification}
{volume attributes}
{number of files in directory}
{first block of directory}
{length of directory in blocks}
{number of allocation blocks}
{size of allocation blocks}
{number of bytes to allocate}
{first block in block map}
{next unused file number}
{nurnber of unused allocation blocks}
{used by Device Manager}
END;
HParmBlkPtr
HParamBlockRec
qLink:
= "HParamBlockRec;
=RECORD
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
CASE ParamBlkType OF
ioParam:
(ioRefNum:
ioVersNum:
ioPermssn:
ioMisc:
ioBuffer:
ioReqCount:
ioActCount:
ioPosMode:
INTEGER;
SignedByte;
SignedByte;
Ptr;
Ptr;
LONGINT;
LONGINT;
INTEGER;
ioPosOffset:
LONGINT);
fileParam:
(ioFRefNum:
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
ioFlVersNum:
ioFlFndrinfo:
ioDirID:
ioFlStBlk:
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
Finfo;
LONGINT;
INTEGER;
{queue link}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive }
{ number, or working directory }
{ reference number}
{path reference number}
{version number}
{read/write permission}
{miscellaneous}
{data buffer}
{requested number of bytes}
{actual number of bytes}
{positioning mode and newline
{ character}
{positioning offset}
{path reference number}
{version number}
{not used}
{directory index}
{file attributes}
{version number}
{information used by the Finder}
{directory ID or file number}
{first allocation block of data fork}
Summary of the File Manager W-185

<!-- source-page: 196 -->
## Page 196

Inside Macintosh
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
ioFlCrDat:
ioFlMdDat:
volumeParam:
(filler2:
ioVolindex:
ioVCrDate:
ioVLsMod:
ioVAtrb:
ioVNrnFls:
ioVBitMap:
ioAllocPtr:
ioVNmAlBlks:
ioVAlBlkSiz:
ioVClpSiz:
ioAlBlSt:
ioVNxtCNID:
ioVFrBlk:
idVSigWord:
ioVDrvinfo:
ioVDRefNum:
ioVFSID:
ioVBkUp:
ioVSeqNum:
ioVWrCnt
ioVFilCnt:
ioVDirCnt:
ioVFndrinfo:
END;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
LONGINT);
LONGINT;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
ARRAY [1.. 8]
{logical end-of-file of data fork}
{physical end-of-file of data fork}
{first allocation block of resource
{ fork}
{logical end-of-file of resource fork}
{physical end-of-file of resource
{ fork}
{date and time of creation}
{date and time of last modification}
{not used}
{volume index}
{date and time of initialization}
{date and time of last modification)
{volume attributes}
{number of files in directory}
{first block of volume bitmap}
{u$ed internally}
{number of allocation blocks}
{size of ailocation blocks}
{default clump size}
{first block in volume block map}
{next unused node ID}
{number of unused allocation blocks)
{volume signature}
{drive number}
{driver reference number}
{file-system identifier}
{date and time of last backup}
{used internally}
{volume write count}
{number of files on volume}
{number of directories on volume}
OF LONGINT);
{information used by
{ the Finder}
Cinf oType
(hfileinfo,dirinfo);
Cinf oPBPtr
Cinf oPBRec
qLink:
"CinfoPBRec;
RECORD
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
ioFRefNum:
ioFVersNum:
fillerl:
ioFDirindex:
ioFlAttrib:
filler2:
QElemPtr;
INTEGER;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
INTEGER;
SignedByte;
SignedByte;
INTEGER;
SignedByte;
SignedByte;
W-186 Summary of the File Manager
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive }
{ number, or working directory
{ reference number}
{file reference number}
{version number}
{not used}
{directory index}
{file attributes}
{not used}

<!-- source-page: 197 -->
## Page 197

CASE CinfoType OF
hFileinfo:
(ioFlFndrinfo: Finfo;
ioDirID:
LONGINT;
ioFlStBlk:
ioFlLgLen:
ioFlPyLen:
ioFlRStBlk:
ioFlRLgLen:
ioFlRPyLen:
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
ioFlCrDat:
LONGINT;
ioFlMdJ:)at:
LONGINT;
ioFlBkDat:
LONGINT;
ioFlXFndrinfo: FXInfo;
ioFlParID:
ioFlClpSiz:
dirinfo:
(ioDrUsrWds:
ioDrDirID:
ioDrNmFls:
filler3:
ioDrCrDat:
ioDrMdDat:
ioDrBkDat:
ioDrFndrinfo:
ioDrParID:
END;
LONGINT;
LONGINT);
Dinfo;
LONGINT;
INTEGER;
ARRAY [1.. 9]
LONGINT;
LONGINT;
LONGINT;
DXIpfo;
LONGINT);
CMovePBPtr
CMovePBRec
qLink:
"CMovePBRec;
RECORD
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
fillerl:
ioNewName:
filler2:
ioNewDirID:
filler3:
ioDirID:
END;
QElemPtr;
INTEG~R;
INTEGER;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
LONGINT;
StringPtr;
LONGINT;
LONGINT;
ARRAY[l. .2]
LONGINT);
The File Manager
{information used by the Finder}
{directory ID or file number}
{first allocation block of data fork}
{logical end-of-file of data fork}
{physical end-of-file of data fork}
{first allocation block of resource
{ fork}
{logical end-of-file of resource fork}
{physical end-of-file of resource
{ fork}
{date and time of creation}
{date and time of last modification}
{date and time of last back-up}
{additional information used by the }
{ Finder}
{file parent directory ID (integer)}
{file's clump size}
{information used by the }
{ Finder}
{directory ID}
{number of files in directoryl
OF
I~'.l;'Jl:GER;
{date and time of creation}
{date and time of last modification}
{date and time of last back-µp}
{additional information used by the
{ Finder}
{directory's parent directory ID}
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive }
{ number, or working directory }
{ reference number}
{not used}
{name of new directory}
{not used}
{directory ID of new directory}
OF LONGINT;
{not used}
{directory ID of current directory}
Summary of the File Manager IV-187

<!-- source-page: 198 -->
## Page 198

Inside Macintosh
WDPBPtr = AWDPBRec;
WDPBRec = RECORD
qLink:
QElemPtr;
INTEGER;
INTEGER;
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
filler!:
ioWDinc;lex:
ioWDProcID:
ioWDVRefNum:
filler2:
ioWDDi~ID:
END;
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
INTEGER;
ARRAY [1.. 7]
LONGINT);
AFCBPBRec;
RECORD
QElemPtr;
INTEGER;
INTEGER;
FCBPBPtr
FCBPBRec
qLink:
qType:
ioTrap:
ioCmdAddr:
ioCompletion:
ioResult:
ioNamePtr:
ioVRefNum:
ioRefNum:
filler:
ioFCBindx:
ioFCBFlNm:
ioFCBFlags:
ioFCBStBlk:
ioFCBEOF:
ioFCBPLen:
ioFCBCrPs:
ioFCBVRefNum:
ioFCBClpSiz:
ioFCBParID:
END;
VCB = RECORD
Ptr;
ProcPtr;
OSErr;
StringPtr;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive }
{ number, or working directory }
{ reference number}
{not used}
{working directory index}
{working directory user identifier}
{working directory's volume }
{ reference number}
OF INTEGER;
{not used}
{working directory's directory ID}
{next queue entry}
{queue type}
{routine trap}
{routine address}
{completion routine}
{result code}
{pathname}
{volume reference number, drive }
{ number, or working directory
{ reference number}
{path reference number}
{not used}
{FCB index}
{file number}
{flags }
{first allocation block of file}
{logical end-of-file}
{physical end-of-file}
{mark}
{volume reference number}
{file's clump size}
{parent directory ID}
qLink:
qType:
vcbFlags:
vcbSigWord:
QElemPtr;
INTEGER;
INTEGER;
INTEGER;
{next queue entry}
{queue type}
{bit 15=1 if dirty}
{$4244 for hierarchical,
{$D2D7 for flat}
vcbCrDate:
vcbLsMod:
vcbAtrb:
vcbNmFls:
LONGINT;
LONGINT;
INTEGER;
INTEGER;
W-188 Summary of the File Manager
{date and time of initialization}
{date and time of last }
{ modification}
{volume attributes}
{number of files in directory}
(

<!-- source-page: 199 -->
## Page 199

vcbVBMSt:
vcbAllocPtr:
vcbNrnAlBlks:
vcbAlBlkSiz:
vcbClpSiz:
vcbAlBlSt:
vcbNxtCNID:
vcbFreeBks:
vcbVN:
vcbDrvNum:
vcbDRefNum:
vcbFSID:
vcbVRefNum:
vcbMAdr:
vcbBufAdr:
vcbMLen:
vcbDirindex:
vcbDirBlk:
vcbVolBkUp:
vcbVSeqNum:
vcbWrCnt:
vcbXTClpSiz:
vcbCTClpSiz:
vcbNmRtDirs:
vcbFilCnt:
vcbDirCnt:
vcbFndrinfo:
vcbVCSize:
vcbVBMCSiz:
vcbCtlCSiz:
vcbXTAlBlks:
INTEGER;
INTEGER;
INTEGER;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
INTEGER;
STRING[27];
INTEGER;
INTEGER;
INTEGER;
INTEGER;
Ptr;
Ptr;
INTEGER;
INTEGER;
INTEGER;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
LONGINT;
INTEGER;
LONGINT;
LONGINT;
ARRAY [1.. 8}
INTEGER;
INTEGER;
INTEGER;
INTEGER;
vcbCTAlBlks: INTEGER;
vcbXTRef:
vcbCTRef:
vcbCtlBuf:
vcbDirIDM:
vcbOffsM:
END;
DrvQEl = RECORD
qLink:
qType:
dQDrive:
dQRefNum:
dQFSID:
dQDrvSz:
dQDrvSz2:
END;
INTEGER;
INTEGER;
Ptr;
LONGINT;
INTEGER
QElemPtr;
INTEGER;
INTEGER;
INTEGER;
INTEGER;
INTEGER
INTEGER
The File Manager
{first block of volume bit map}
{used internally}
{number of allocation blocks}
{allocation block size}
{default clump size}
{first block in bit map}
{next unused node ID}
{number of unused allocation
{ blocks}
{volume name}
{drive number}
{driver reference number}
{file-system identifier}
{volume reference number}
{pointer to block map}
{pointer to volume buffer}
{number of bytes in block map}
{used internally}
{used internally}
{date and time of last backup}
{used internally}
{volume write count}
{clump size of extents tree file}
{clump size of catalog tree file)
{number of directories in root}
{number of files on volume}
{number of directories on volume}
OF LONGINT; {information used }
{ by the Finder}
{used internally}
{used internally}
{used internally}
{size in blocks of extents tree
{ file}
{size in blocks of catalog tree
{ file}
{path reference number for
{ extents tree file}
{path reference number for
{ catalog tree file}
{pointer to extents and catalog
{ caches}
{directory last searched}
{offspring index at last search}
{next queue entry}
{queue type}
{drive number}
{driver reference number}
{file-system identifier}
{number of logical blocks}
{additional field to handle
{ large drive}
Summary of the File Manager IV-189

<!-- source-page: 200 -->
## Page 200

Inside Macintosh
High-Level Routines [Not in ROM]
Accessing Volumes
FUNCTION GetVInfo
FUNCTION GetVRefNum
FUNCTION GetVol
FUNCTION SetVol
FUNCTION FlushVol
FUNCTION UnmountVol
FUNCTION Eject
Accessing Files
FUNCTION FSOpen
FUNCTION Open RF
FUNCTION FSRead
FUNCTION FSWrite
FUNCTION GetFPos
FUNCTION SetFPos
FUNCTION GetEOF
FUNCTION SetEOF
FUNCTION Allocate
FUNCTION FSClose
(drvNum: INTEGER; volName: StringPtr; VAR vRefNum:
INTEGER; VAR freeBytes: LONGINT)
: OSErr;
(pathRefNum: INTEGER; VAR vRefNum: INTEGER)
:
OSErr;
(volName:
(volName:
(volName:
(volName:
(volName:
StringPtr;
StringPtr;
StringPtr;
StringPtr;
StringPtr;
VAR vRefNum: INTEGER)
: OSErr;
vRefNum: INTEGER)
OSErr;
vRefNum: INTEGER)
OSErr;
vRefNum: INTEGER)
OSErr;
vRefNum: INTEGER)
OSErr;
(fileName: Str255; vRefNum: INTEGER; VAR refNum:
INTEGER)
: OSErr;
(fileName: Str255; vRefNum: INTEGER; VAR refNum:
INTEGER)
: OSErr;
(refNum: INTEGER; VAR count: LONGINT; buffPtr: Ptr)
: OSErr;
(refNum: INTEGER; VAR count: LONGINT; buffPtr: Ptr)
: OSErr;
(refNum: INTEGER; VAR filePos: LONGINT)
: OSErr;
(refNum: INTEGER; posMode: INTEGER; posOff:
LONGINT)
: OSErr;
(refNum: INTEGER; VAR logEOF: LONGINT)
: OSErr;
(refNum: INTEGER; logEOF: LONGINT)
: OSErr;
(refNum: INTEGER; VAR count: LONGINT)
: OSErr;
(refNum: INTEGER) : OSErr;
Creating and Deleting Files
FUNCTION Create
FUNCTION FSDelete
(fileName: Str255; vRefNum: INTEGER; creator:
OSType; fileType: OSType) : OSErr;
(fileName: Str255; vRefNum: INTEGER)
: OSErr;
Changing Information About Files
FUNCTION GetFinfo
(fileName:
Finfo) :
FUNCTION SetFinfo
(fileName:
Finfo) :
FUNCTION SetFLock
(fileName:
FUNCTION RstFLock
(fileName:
FUNCTION Rename
(oldName:
Str255) :
W-190 Summa.ry of the File Manager
Str255;
OSErr;
Str255;
OSErr;
Str255;
Str255;
Str255;
OSErr;
vRefNum: INTEGER; VAR fndrinfo:
vRefNum: INTEGER; fndrinfo:
vRefNum: INTEGER)
: OSErr;
vRefNum: INTEGER)
: OSErr;
vRefNum: INTEGER; newName:

<!-- source-page: 201 -->
## Page 201

The File Manager
Low-Level Routines
Initializing the File 1/0 Queue
PROCEDURE FinitQueue;
FUNCTION PBMountVol (paramBlock: ParmBlkPtr)
OSErr;
<-
16
ioResult
word
<->
22
ioVRef:Num
word
Accessing Volumes
FUNCTION PBGetVInfo (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
<->
22
ioVRef:Num
word
->
28
ioVollndex
word
<-
30
ioVCrDate
longword
<-
34
ioVLsBkUp
longword
<-
38
ioVAtrb
word
<-
40
ioVNmFJ.s
word
<-
42
ioVDirSt
word
<-
44
ioVBILn
word
<-
46
io VNmAIBlks
word
<-
48
io V AIBlkSiz
longword
<-
52
ioVOpSiz
longword
<-
56
ioAIBlSt
word
<-
58
ioVNxtFNum
longword
<-
62
ioVFrBlk.
word
FUNCTION PBHGetVInfo (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
<->
22
ioVRef:Num
word
->
28
ioVollndex
word
<-
30
ioVCrDate
longword
<-
34
ioVLsMod
longword
<-
38
ioVAtrb
word
<-
40
ioVNmF1s
word
<-
42
ioVBitMap
word
<-
44
io V AllocPtr
word
<-
46
ioVNmAIBlks
word
<-
48
io V AIBlk.Siz
longword
<-
52
ioVOpSiz
longword
<-
56
ioAIBlSt
word
<-
58
ioVNxtFNum
longword
<-
62
ioVFrBlk.
word
<-
64
ioVSigWord
word
<-
66
ioVDivlnfo
word
<-
68
ioVDRef:Num
word
<-
70
ioVFSID
word
<-
72
ioVBkUp
longword
Summary of the File Manager IV-191

<!-- source-page: 202 -->
## Page 202

Inside Macintosh
<-
76
ioVSeqNum
word
<-
78
ioVWrCnt
longword
<-
82
ioVFilCnt
longword
<-
86
ioVDirCnt
longword
<-
90
io VFndrlnfo
32 bytes
FUNCTION PBSetVInfo (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
30
ioVCrDate
longword
->
34
ioVLsMod
longword
->
38
ioVAtib
word
->
52
ioVClpSiz
longword
->
72
ioVBkUp
longword
->
76
ioVSeqNum
word
->
90
io VFndrlnfo
32 bytes
FUNCTION PBGetVol (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<-
22
ioVRefNum
word
FUNCTION PBHGetVol (paramBlock: WDPBPtr; async: BOOLEAN): OsErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<-
22
ioVRefNum
word
<-
28
ioWDProcID
longword
<-
32
ioWDVRefNum word
<-
48
ioWDDirID
longword
FUNCTION PBSetVol (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
FUNCTION PBHSetVol (paramBlock: WDPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
48
ioWDDirID
longword
FUNCTION PBFlushVol (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
W-192 Summary of the File Manager

<!-- source-page: 203 -->
## Page 203

The File Manager
FUNCTION PBUnmountVol (paramBlock: ParmBlkPtr)
OSErr;
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
io VRefNum
word
FUNCTION PBOf fLine (paramBlock: ParmBlkPtr)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
FUNCTION PBEject (paramBlock: ParmBlkPtr)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
Accessing Files
FUNCTION PBOpen (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
io VRefNum
word
<-
24
ioRefNum
word
->
26
ioVersNum
byte
->
27
ioPermssn
byte
->
28
ioMisc
pointer
FUNCTION PBHOpen (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioRefNum
word
->
27
ioPermssn
byte
->
28
ioMisc
pointer
->
48
ioDirID
longword
FUNCTION PBOpenRF (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioRefNum
word
->
26
ioVersNum
byte
->
27
ioPermssn
byte
->
28
ioMisc
pointer
Summary of the File Manager IV-193

<!-- source-page: 204 -->
## Page 204

Inside Macintosh
FUNCTION PBHOpenRF
->
12
<-
16
->
18
->
22
<-
24
->
27
->
28
->
48
(paramBlock:
ioCompletion
ioResult
ioNamePtr
ioVRefNum
ioRefNum
ioPennssn
ioMisc
ioDirID
HParmBlkPtr; async: BOOLEAN)
pointer
word
pointer
word
word
byte
pointer
long word
FUNCTION PBLockRange (paramBlock: ParmBlkPtr; async: BOOLEAN)
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
36
ioReqCount
long word
->
44
ioPosMode
word
->
46
ioPosOffset
long word
OSErr;
OSErr;
FUNCTION PBUnlockRange (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
36
ioReqCount
long word
->
44
ioPosMode
word
->
46
ioPosOffset
long word
FUNCTION PBRead (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
32
ioBuffer
pointer
->
36
ioReqCount
long word
<-
40
ioActCount
long word
->
44
ioPosMode
word
<->
46
ioPosOffset
long word
FUNCTION PBWrite (paramBlock: parmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
poipter
<-
16
ioResult
word
->
24
ioRefNum
word
->
32
ioBuffer
pointer
->
36
ioReqCount
long word
<-
40
ioActCount
long word
->
44
ioPosMode
word
<->
46
ioPosOffset
long word
FUNCTION PBGetFPos (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletioq
pointer
<-
16
ioResult
worci
->
24
ioRefNum
word
<-
36
ioReqCount
longword
<-
40
ioActCount
long word
<-
44
ioPosMode
word
<-
46
ioPosOffset
longword
IV-194 Summary of the File Manager

<!-- source-page: 205 -->
## Page 205

The File Manager
FUNCTION PBSetFPos (paramBlock: ParmBlkPtr; async: BOOLEAN)
: OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
44
ioPosMode
word
<->
46
ioPosO:ffset
longword
FUNCTION PBGetEOF (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResUlt
word
->
24
ioRefNum
word
<-
28
ioMisc
longword
FUNCTION PBSetEOF (paramj3lock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
28
ioMisc
longword
FUNCTION PBAllocate (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
->
36
ioReqCount
longword
<-
40
ioActCount
longword
FUNCTION PBAllocContig (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNurn
word
->
36
ioReqCount
longword
<-
40
ioActCount
longword
FUNCTION PBFlushFile (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
FUNCTION
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
24
ioRefNum
word
PBClose (paramBlock:
->
12
ioCompletion
<-
16
ioResult
->
24
ioRefNum
ParmBlkPtr; async: BOOLEAN)
pointer
word
word
Creating and Deleting Files and Directories
FUNCTION PBCreate (paramBlock: ParmBlkPtr; async: BOOLEAN)
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
OSErr;
OSErr;
Swnmary of the File Manager IV-195

<!-- source-page: 206 -->
## Page 206

Inside Macintosh
FUNCTION PBHCreate (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRetNum
word
->
48
ioDirID
long word
FUNCTION PBDirCreate (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRetNum
word
<->
48
ioDirID
longword
FUNCTION PBDelete (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
pyte
FUNCTION PBHDelete (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
48
ioDirID
longword
Changing Information About Files and Directories
FUNCTION PBGetFInfo (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioFRefNum
word
->
26
ioFVersNum
byte
->
28
ioFDirlndex
word
<-
3o
ioFIAttrib
byte
<-
31
ioFIVersNum
byte
<-
32
ioFIFndrinfo
16 bytes
<-
48
ioFINum
long word
<-
52
ioFlStBlk
word
<-
54
ioFILgLen
longword
<-
58
ioFIPyLen
longword
<-
62
ioFlRStBlk
word
<-
64
ioFlRLgLen
longword
<-
68
ioFIRPyLen
longword
<-
72
ioFICrDat
longword
<-
76
ioAMdDat
longword
IV-196 Summary of the File Manager

<!-- source-page: 207 -->
## Page 207

The File Manager
FUNCTION PBHGetFinf o (paramBlock: HParmBlkPtr; async: BOOLEAN)
: OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioFRefNum
word
->
28
ioFDirlndex
word
<-
30
ioFIAttrib
byte
<-
32
ioFIFndrlnfo
16 bytes
<->
48
ioDirID
longword
<-
52
ioFlStBlk
word
<-
54
ioALgLen
longword
<-
58
ioFIPyLen
longword
<-
62
ioFlRStBlk
word
<-
64
ioARLgLen
longword
<-
68
ioFlRPyLen
longword
<-
72
ioFlCrDat
longword
<-
76
ioFlMdDat
longword
FUNCTION PBSetFInfo (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
->
32
ioFIFndrlnfo
16 bytes
->
72
ioFlCrDat
long word
->
76
ioFlMdDat
long word
FUNCTION PBHSetFInfo (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
32
ioFIFndrlnfo
16 bytes
->
48
ioDirID
longword
->
72
ioFlCrDat
longword
->
76
ioFlMdDat
longword
FUNCTION PBSetFLock (paramBlock: ParmBlkPt r; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
FUNCTION PBHSetFLock (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
48
ioDirID
longword
Swnmary of the File Manager IV-197

<!-- source-page: 208 -->
## Page 208

Inside Macintosh
FUNCTION PBRstFLock (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioFVersNum
byte
FUNCTION PBHRstFLock (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
io VRefNum
word
->
48
ioDirID
long word
FUNCTION PBSetFVers (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioVersNum
byte
->
28
ioMisc
byte
FUNCTION PBRename (paramBlock: ParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
26
ioVersNum
byte
->
28
ioMisc
pointer
FUNCTION PBHRename (paramBlock: HParmBlkPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
28
ioMisc
pointer
->
48
ioDirID
longword
Hierarchical Directory Routines
FUNCTION PBGetCatInfo (paramBlock: CinfoPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
<-
24
ioFRefNum
word
->
28
ioFDirlndex
word
<-
30
ioFlAttrib
byte
<-
32
ioFlFndrlnfo
16 bytes
<-
32
ioDrUsrWds
16 bytes
<->
48
ioDirID
longword
<->
48
ioDrDirID
longword
<-
52
ioFlStBlk
word
W-198 Summary of the File Manager

<!-- source-page: 209 -->
## Page 209

The File Manager
<-
52
ioDrNmFls
word
<-
54
ioF1LgLen
longword
<-
58
ioAPyLen
longword
<-
62
ioARStBlk
word
<-
64
ioARLgLen
longword
<-
68
ioFlRPyLen
longword
<-
72
ioFl.CrDat
longword
<-
72
ioDrCrDat
longword
<-
76
ioAMdDat
longword
<-
76
ioDrMdDat
longword
<-
80
ioFIBkDat
longword
<-
80
ioDrBkDat
longword
<-
84
ioFl.XFndrlnfo
16 bytes
<-
84
ioDrFndrlnfo
16 bytes
<-
100 ioFJParID
longword
<-
100 ioDrParID
longword
<-
104 ioFl.ClpSiz
longword
FUNCTION PBSetCatInfo (paramBlock: CinfoPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
28
ioFDirlndex
word
->
30
ioFl.Attrib
byte
->
32
ioFl.Fndrlnfo
16 bytes
->
32
ioDrUsrWds
16 bytes
->
48
ioDirID
longword
->
48
ioDrDirID
longword
->
72
ioFl.CrDat
longword
->
72
ioDrCrDat
longword
->
76
ioAMdDat
long word
->
76
ioDrMdDat
long word
->
80
ioFIBkDat
longword
->
80
ioDrBkDat
longword
->
84
ioFl.XFndrlnfo
16 bytes
->
84
ioDrFndrlnfo
16 bytes
->
104 ioFl.ClpSiz
longword
FUNCTION PBCatMove (paramBlock: CMovePBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
->
22
ioVRefNum
word
->
28
ioNewName
pointer
->
36
ioNewDirID
long word
->
48
ioDirlD
long word
Surrunary of the File Manager IV-199

<!-- source-page: 210 -->
## Page 210

Inside Macintosh
Working Directory Routines
FUNCTION PBOpenWD (paramBlock: WDPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
->
28
ioWDProcID
longword
->
48
ioWDDirID
longword
FUNCTION PBCloseWD (paramBlock: WDPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
->
22
ioVRefNum
word
FUNCTION PBGetWDInfo (paramBlock: WDPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
->
26
ioWDindex
word
<->
28
ioWDProcID
longword
<->
32
ioWDVRefNum word
<-
48
ioWDDirID
long word
Advanced Routines
FUNCTION GetFSQHdr
QHdrPtr;
[Not in ROM]
FUNCTION GetVCBQHdr
QHdrPtr;
[Not in ROM]
FUNCTION GetDrvQHdr
QHdrPtr;
[Not in ROM]
FUNCTION PBGetFCBInfo (paramBlock: FCBPBPtr; async: BOOLEAN)
OSErr;
->
12
ioCompletion
pointer
<-
16
ioResult
word
<-
18
ioNamePtr
pointer
<->
22
ioVRefNum
word
<->
24
ioRefNum
word
->
28
ioFCBindx
longword
<-
32
ioFCBFlNm
long word
<-
36
ioFCBFlags
word
<-
38
ioFCBStBlk
word
<-
40
ioFCBEOF
longword
<-
44
ioFCBPLen
longword
<-
48
ioFCBCrPs
longword
<-
52
ioFCBVRefNum
word
<-
54
ioFCBClpSiz
longword
<-
58
ioFCBParID
longword
W-200 Summary of the File Manager

<!-- source-page: 211 -->
## Page 211

The File Manager
Result Codes
Name
Value
Meaning
badMDBErr
-60
badMovErr
-122
bdNamErr
-37
dirFulErr
-33
dirNFErr
-120
dskFulErr
-34
dupFNErr
-48
eofErr
-39
extFSErr
-58
fBsyErr
-47
fLckdErr
-45
fnfErr
-43
fnOpnErr
-38
fsDSIntErr
-127
fsRnErr
-59
gfpErr
-52
ioErr
-36
memFullErr
-108
no Err
0
noMacDskErr -57
nsDrvErr
-56
nsvErr
-35
opWrErr
-49
paramErr
-50
permErr
-54
posErr
-40
rfNumErr
-51
tmfoErr
-42
tmwdoErr
-121
volOffLinErr
-53
volOnLinErr
-55
vLckdErr
-46
wrgVolTypErr -123
wrPermErr
-61
wPrErr
-44
Master directory block is bad; must reinitialize volume
Attempted to move into off spring
Bad file name or volume name (perhaps zero-length); attempt to
move into a file
File directory full
Directory not found
All allocation blocks on the volume are full
A file with the specified name and version number already exists
Logical end-of-file reached during read operation
External file system; file-system identifier is nonzero, or path
reference number is greater than 1024
File is busy; one or more files are open; directory not empty or
working directory control block is open
File locked
File not found
File not open
Internal file system error
Problem during rename
Error during GetFPos
I/O error
Not enough room in heap zone
No error
Volume lacks Macintosh-format directory
Specified drive number doesn't match any number in the drive
queue
Specified volume doesn't exist
The read/write permission of only one access path to a file can
allow writing
Parameters don't specify an existing volume, and there's no
default volume
Attempt to open locked file for writing
Attempt to position before start of file
Reference number specifies nonexistent access path
Too many files open
Too many working directories open
Volume not on-line
Specified volume is already mounted and on-line
Volume is locked by a software flag
Attempt to do hierarchical operation on nonhierarchical volume
Ryad/write permission doesn't allow writing
Volume is locked by a hardware setting
Summary of the File Manager IV-201

<!-- source-page: 212 -->
## Page 212

Inside Macintosh
Assembly-Langu~~e Information
Constants
; Flags in file information used by the Finder
fOnDesk
.EQU
1
;set if file is on desktop (hierarchical
; volumes only)
fHasBundle
.EQU
13
;set if file has a bundle
finvisible
.EQU
14
;set if file's icon is invisible
fTrash
.EQU
-3 ;file is in Trash window
fDesktop
.EQU
-2
;fiJ,e is on desktop
fDisk
.EQU
b
;file is in disk window
; Flags in trap words
?tSnycTrpBit
.EQU
10
;set for an asynchronous call
; Values for requesting read/write permission
fsCurPerm
.EQU
0
;what~ver is currently allowed
;requ~st for read permission only
;request for write permission only
fsRdPerm
.EQU
1
fsWrPerm
. EQU
2
fsRdWrPerm
.EQU
3
;request for exclusive read/write permission
;request for shared read/write permission
fsRdWrShPerm
.EQU
4
; Positioning modes
fsAtMark
fsFromStart
fsFromLEOF
fsFromMark
rdVerify
.EQU
.EQU
.EQU
.EQU
.EQU
0
; at current mark
1
;s~t mark relative to beginning of file
2
;set mark relative to logical end-of-file
3
;set mark relative to current mark
64
;add to above for read-verify
Structure of File Information Used by the Finder
fdType
fdCreator
fdFlags
fdLocation
fdFldr
fdlconID
fdUnused
fdCornment
fd?utAway
File type (long)
File's creator (long)
Flags (word)
File's location (point; long)
File's window (word)
File's icon ID (word)
R.¢§ervw (8 bytes)
Pile's comment ID (word)
File's home directory ID (long word)
Structure of Directory Information Used by the Finder
frRect
frFlags
frLocation
Folder's rectangle (8 bytes)
Flags (word)
Folder's location (point; long)
W-202 Swnmary of the File Manager

<!-- source-page: 213 -->
## Page 213

fr View
frScroll
frOpenChain
frUnused
frComment
frPutAway
Folder's view (word)
Folder's scroll position (point; long)
Directory ID chain of open folders (long word)
Reserved (word)
Folder's comment ID (word)
Folders's home directory ID (long word)
The File Manager
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
Pointer to pathname (preceded by length byte)
Pointer to volume name (preceded by length byte)
Volume reference number or working directory reference number (word)
Drive number (word)
Structure of 1/0 Parameter Block
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
ioPosOff set
ioQElSize
Path reference number (word)
Version number (byte)
Read/write permission (byte)
Pointer to new pathname (preceded by length byte)
Logical end-of-file for SetEOF (long)
Pointer to access path buffer
New version number for SetFilType (byte)
Pointer to data buffer
Requested number of bytes (long)
Actual number of bytes (long)
Positioning mode and newline character (word)
Positioning offset (long)
Size in bytes of 1/0 parameter block
Structure of File Parameter Block
ioRefNum
ioFileType
ioFDirlndex
ioFlAttrib
ioFFlType
ioFlUsrWds
ioDirID
ioFFlNum
ioFlStBlk
ioFlLgLen
Path reference number (word)
Version number (byte)
Directory index (word)
File attributes (byte)
Version number (byte)
.
Information used by the Finder (16 bytes)
Directory ID (long)
File number (long)
First allocation block of data fork (word)
Logical end-of-file of data fork (long)
Summary of the File Manager IV-203

<!-- source-page: 214 -->
## Page 214

Inside Macintosh
ioFIPyLen
ioFIRStBlk
ioFIRLgLen
ioFIRPyLen
ioFlCrDat
ioFIMdDat
ioFQElSize
Physical end-of-file of data fork (long)
First allocation block of resource fork (word)
Logical end-of-file of resource fork (long)
Physical end-of-file of resource fork (long)
Date and time of creation (long)
Date and time of last modification (long)
Size in bytes of file information parameter block
Structure of Volume Information Parameter Block (Flat Directory)
ioVollndex
ioVCrDate
ioVLsBkUp
ioVAtrb
ioVNmFls
ioVDirSt
ioVBILn
io VNmAIBlks
io V AIBlkSiz
ioVClpSiz
ioAIBlSt
ioVNxtFNum
ioVFrBlk
ioVQElSize
Volume index (word)
Date and time of initialization (long)
Date and time of last modification (long)
Volume attributes; bit 15=1 if volume locked (word)
Number of files in directory (word)
First block of directory (word)
Length of directory in blocks (word)
Number of allocation blocks on volume (word)
Size of allocation blocks (long)
Number of bytes to allocate (long)
First block in block map (word)
Next unused file number (long)
Number of unused allocation blocks (word)
Size in bytes of volume information parameter block
Structure of Volume Information Parameter Block (Hierarchical Directory)
ioVollndex
ioVCrDate
ioVLsMod
ioVAtrb
ioVNmFls
ioVCBVBMSt
io VNmAIBlks
io V AIBlkSiz
ioVClpSiz
ioAIBlSt
ioVNxtCNID
ioVFrBlk
ioVSigWord
ioVDrvlnfo
ioVDRetNum
ioVFSID
ioVBkUp
ioVWrCnt
ioVFilCnt
ioVDirCnt
ioVFndrlnfo
ioHVQEISize
Volume index (word)
Date and time of initialization (long)
Date and time of last modification (long)
Volume attributes (word)
Number of files in directory (word)
First block of volume bit map (word)
Number of allocation blocks (word)
Size of allocation blocks (long)
Default clump size (long)
First block in block map (word)
Next unused node ID (long)
Number of unused allocation blocks (word)
Volume signature (word)
Drive number (word)
Driver reference number (word)
File-system identifier (word)
Date and time of last backup (long)
Volume write count (long)
Number of files on volume (long)
Number of directories on volume (long)
Information used by the Finder (32 bytes)
Size in bytes of hierarchical volume information parameter block
W-204 Summary of the File Manager

<!-- source-page: 215 -->
## Page 215

Structure of Catalog Information Parameter Block (Files)
ioRefNum
ioFileType
ioFDirlndex
ioFIAttrib
ioFIUsrWds
ioFFINum
ioFlStBlk
ioFILgLen
ioFIPyLen
ioFIRStBlk
ioFIRLgLen
ioFIRPyLen
ioFICrDat
ioFIMdDat
ioFIB.kDat
ioFIXFndrinfo
ioFIParID
ioFIClpSiz
Path reference number (word)
Version number (byte)
Directory index (word)
File attributes
Information used by the Finder (16 bytes)
File number (long)
First allocation block of data fork (word)
Logical end-of-file of data fork (long)
Physical end-of-file of data fork (long)
First allocation block of resource fork (word)
Logical end-of-file of resource fork (long)
Physical end-of-file of resource fork (long)
Date and time of creation (long)
Date and time of last modification (long)
Date and time of last backup (long)
Additional information used by the Finder (16 bytes)
File parent directory ID (long)
File's clump size (long)
Structure of Catalog Information Parameter Block (Directories)
ioRefNum
ioFDirlndex
ioFIAttrib
ioDrUsrWds
ioDrDirID
ioDrNmFls
ioDrCrDat
ioDrMdDat
ioDrB.kDat
ioDrFndrinfo
ioDrParID
Path reference number (word)
Catalog index (word)
File attributes
Information used by the Finder (16 bytes)
Directory ID (long)
Number of files in directory (word)
Date and time of creation (long)
Date and time of last modification (long)
Date and time of last backup (long)
Additional information used by the Finder (16 bytes)
Directory's parent directory ID (long)
Structure of Catalog Move Parameter Block
The File Manager
ioNewName
ioNewDirID
ioDirID
Pointer to name of new directory (preceded by length byte)
Directory ID of new directory (long)
Directory ID of current directory (long)
Structure of Working Directory Parameter Block
ioWDlndex
ioWDProcID
ioWDVRefNum
ioWDDirID
Working directory index (word)
Working directory's user identifier (long)
Working directory's volume reference number (word)
Working directory's directory ID (long)
Summary of the File Manager IV-205

<!-- source-page: 216 -->
## Page 216

Inside Macintosh
Structure of File Control Block Information Parameter Block
ioFCBindx
ioFCBFlNm
ioFCBFlags
ioFCBStBlk
ioFCBEOF
ioFCBPLen
ioFCBCrPs
ioFCBVRefNum
ioFCBClpSiz
ioFCBParID
FCB index (long)
File number (long)
Flags (word)
First allocation block of file (word)
Logical end-of-file (long)
Physical end-of-file (long)
Mark (long)
Volume reference number (word)
File's clump size (long)
Parent directory ID (long)
Volume Information Data Structure (Flat Directory)
drSigWord
drCrDate
drLsBkUp
drAtrb
drNmFls
drDirSt
drBlLn
drNmAlBlks
drAlBlkSiz
drClpSiz
drAlBlSt
drNxtFNum
drFreeBks
drVN
Always $D2D7 (word)
Date and time of initialization (long)
Date and time of last modification (long)
Volume attributes (word)
Number of files in directory (word)
First block of directory (word)
Length of directory in blocks (word)
Number of allocation blocks (word)
Allocation block size (long)
Number of bytes to allocate (long)
First allocation block in block map (word)
Next unused file number (long)
Number of unused allocation blocks (word)
Volume name preceded by length byte (28 bytes)
Volume Information Data Structure (Hierarchical Directory)
drSigWord
drCrDate
drLsMod
drAtrb
drNmFls
drVBMSt
drNmAlBlks
drAlBlkSiz
drClpSiz
drAlBlSt
drNxtCNID
drFreeBks
drVN
drVolBkUp
drWrCnt
drXTClpSiz
drCTClpSize
Always $4244 (word)
Date and time of initialization (long)
Date and time of last modification (long)
Volume attributes (word)
Number of files in directory (word)
First block of volume bit map (word)
Number of allocation blocks (word)
Allocation block size (long)
Default clump size (long)
First block in block map (word)
Next unused directory ID (long)
Number of unused allocation blocks (word)
Volume name (28 bytes)
Date and time of last backup (long)
Volume write count (long)
Clump size of extents tree file (long)
Clump size of catalog tree file (long)
IV-206 Summary of the File Manager

<!-- source-page: 217 -->
## Page 217

drNmRtDirs
drFilCnt
drDirCnt
drFndrlnfo
drXTFlSize
drXTExtRec
drCTFISize
drCTExtRec
Number of directories in root (word)
Number of files on volume (long)
Number of directories on volume (long)
Information used by the Finder (32 bytes)
Length of extents tree (LEOF and PEOF) (long)
Extent record for extents tree file (12 bytes)
Length of catalog tree file (LEOF and PEOF) (long)
First extent record for catalog tree file (12 bytes)
File Directory Entry Data Structure (Flat Directory)
flFlags
flTyp
flUsrWds
flFINum
flStBlk
flLgLen
flPyLen
flRStBlk
flRLgLen
flRPyLen
flCrDat
flMdDat
flNam
Bit 7=1 if entry used; bit 0=1 if file locked (byte)
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
Extents Key Data Structure (Hierarchical Directory)
xkrKeyLen
xkrFkType
xkrFNum
xkrFABN
Key length (byte)
$00 for data fork; $FF for resource fork (byte)
File number (long)
Allocation block number within file (word)
Catalog Key Data Structure (Hierarchical Directory)
ckrKeyLen
ckrParID
ckrCName
Key length (byte)
Parent ID (long)
File or directory name preceded by length byte
File Record Data Structure (Hierarchical Directory)
cdrType
filFlags
filTyp
filUsrWds
filFlNum
filStBlk
filLgLen
filPyLen
filRStBlk
Always 2 for file records (byte)
Bit 7=1 if entry used; bit 0=1 if file locked (byte)
Version number (byte)
Information used by the Finder (16 bytes)
File number (long)
First allocation block of data fork (word)
Logical end-of-file of data fork (long)
Physical end-of-file of data fork (long)
First allocation block of resource fork (word)
The File Manager
Summary of the File Manager W-207

<!-- source-page: 218 -->
## Page 218

Inside Macintosh
filRLgLen
filRPyLen
filCrDat
filMd.Dat
filBk:Dat
filFndrinfo
filClpSize
filExtRec
filRExtRec
Logical end-of-file of resource fork (long)
Physical end-of-file of resource fork (long)
Date and time of creation (long)
Date and time of last modification (long)
Date and time of last backup (long)
Additional information used by the Finder (16 bytes)
File's clump size (word)
First extent record for data fork (12 bytes)
First extent record for resource fork (12 bytes)
Directory Record Data Structure (Hierarchical Directory)
cdrType
dirFlags
dirVal
dirDirID
dirCrDat
dirMd.Dat
dirBk:Dat
dirUsrlnfo
dirFndr Info
Always 1 for directory records (byte)
Flags (word)
Valence (word)
Directory ID (long)
Date and time of creation (long)
Date and time of last modification (long)
Date and time of last backup (long)
Information used by the Finder (16 bytes)
Additional information used by the Finder (16 bytes)
Thread Record Data Structure (Hierarchical Directory)
cdrType
thdParID
thdCName
Always 3 for thread records (byte)
Parent ID of associated directory (long)
Name of associated directory preceded by length byte
Volume Control Block Data Structure (Flat Directory)
qLink
qType
vcbFlags
vcbSigWord
vcbCrDate
vcbLsBkUp
vcbAtrb
vcbNmFls
vcbDirSt
vcbBILn
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
Pointer to next queue entry
Queue type (word)
Bit 15=1 if volume control block is dirty (word)
Always $D2D7 (word)
Date and time of initialization (word)
Date and time of last modification (long)
Volume attributes (word)
Number of files in directory (word)
First block of directory (word)
Length of directory in blocks (word)
Number of allocation blocks (word)
Allocation block size (long)
Number of bytes to allocate (long)
First allocation block in block map (word)
Next unused file number (long)
Number of unused allocation blocks (word)
Volume name preceded by length byte (28 bytes)
Drive number (word)
Driver reference number (word)
File-system identifier (word)
IV-208 Summary of the File Manager

<!-- source-page: 219 -->
## Page 219

vcbVRefNum
vcbMAdr
vcbBufAdr
vcbMLen
Volume reference number (word)
Pointer to block map
Pointer to volume buffer
Number of bytes in block map (word)
The File Manager
Volume Control Block Data Structure (Hierarchical Directory)
qLink
qType
vcbFlags
vcbSigWord
vcbCrDate
vcbLsMod
vcbAtrb
vcbNmFls
vcbVBMSt
vcbNmAlBlks
vcbAlBlkSiz
vcbClpSiz
vcbAlBlSt
vcbNxtCNID
vcbFreeBks
vcbVN
vcbDrvNum
vcbDRefNum
vcbFSID
vcbVRefNum
vcbMAdr
vcbBufAdr
vcbMLen
vcbVolBkUp
vcbVSeqNum
vcbWrCnt
vcbXTClpSiz
vcbCTClpSiz
vcbNmRtDirs
vcbFilCnt
vcbDirCnt
vcbFndrlnfo
vcbXTAlBks
vcbCTAlBks
vcbXTRef
vcbCTRef
vcbCtlBuf
vcbDirIDM
vcbOffsM
Pointer to next queue entry
Queue type (word)
Bit 15=1 if volume control block is dirty (word)
$4244 for hierarchical, $D2D7 for flat (word)
Date and time of initialization (word)
Date and time of last modification (long)
Volume attributes (word)
Number of files in directory (word)
First block of volume bit map (word)
Number of allocation blocks (word)
Allocation block size (long)
Default clump size (long)
First block in bit map (word)
Next unused node ID (long)
Number of unused allocation blocks (word)
Volume name preceded by length byte (28 bytes)
Drive number (word)
Driver reference number (word)
File-system identifier (word)
Volume reference number (word)
Pointer to block map
Pointer to volume buffet
Number of bytes in block map (word)
Date and time of last backup (long)
Index of volume in backup set (word)
Volume write count (long)
Clump size of extents tree file (long)
Clump size of catalog tree file (long)
Number of directories in root (word)
Number of files on volume (long)
Number of directories on volume (long)
Information used by the Finder (32 bytes)
Size in blocks of extents tree file (word)
Size in blocks of catalog tree file (word)
Path reference number for extents tree file (word)
Path reference number for catalog tree file (word)
Pointer to extents and catalog tree caches (long)
Directory last searched (long)
Offspring index at last search (word)
Summary of the File Manager W-209

<!-- source-page: 220 -->
## Page 220

Inside Macintosh
File Control Block Data Structure (Flat Directory)
fcbFlNum
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
Pointer to volume conttol block (long)
Pointer to access path buffer (long)
File Control Block Data Structure (Hierarchical Directory)
fcbFINum
fcbMdRByt
fcbTypByt
fcbSBlk
fcbEOF
fcbPLen
fcbCrPs
fcbVPtr
fcbBfAdr
fcbClnlpSize
fcbBTCBPtr
fcbExtRec
fcbFType
fcbDirID
fcbCName
File number (long)
Flags (byte)
Version number (byte)
First allocation block of file (word)
Logical end-of-file (long)
Physical end-of-file (long)
Mark (long)
Pointer to volume control block (long)
Pointer to access path buffer (long)
File's clump size (long)
Pointer to B*-tree control block (long)
First three file extents (12 bytes)
File's four Finder type bytes (long)
File's parent ID (long)
Name of open file, preceded by length byte (32 bytes)
Drive Queue Entry Data Structure
qLink
qType
dQDrive
dQRefNum
dQFSID
dQDrvSz
dQDrvSz2
Macro Names
Pascal name
FinitQueue
PBMountVol
PBGetVInfo
PBHGetVInfo
PBSetVInfo
Pointer to next queue entry
Queue type (word)
Drive number (word)
Driver reference number (word)
File-system identifier (word)
Number of logical blocks on drive (word)
Additional field to handle large drive size (word)
Macro name
_lnitQueue
_MountVol
_GetVolInfo
_HGetVInfo
_SetVollnfo
W-210 Summary of the File Manager

<!-- source-page: 221 -->
## Page 221

Pascal name
Macro name
PBGetVc;>l
_GetVol
PBHGetVol
_HGetVol
PBSetVol
_SetVol
PBHSetVol
"'-HSetVol
PB Flush Vol
-'-Flush Vol
PBUnmountVol _UnmountVol
PBOfftine
_OffLine
PB Eject
_Eject
PBOpen
_Open
PBHOpen
_HOpen
PBOpenRF
_OpeilRF .
PBHOpenru<
_HOpenRF
PBLockRange
_Lock:Rng
PBUnlockllange _ UnlockRng
PB Read
_Read
PBWrite
_Write
PBGetFPos
_ OetFPos
PBSetFPos
_SetFPos
PBGetEOF
_GetEOF
PBSetEOF
_SetEOF
PB Allocate
Allocate
PBAllocContig =AllocContig
PBFlushFile
_FlushFile
PB Close
_Close
PBCreate
_Create
PBHCreate
_HCreate
PBDirCreate
_DirCreate
PBGetFInfo
_ GetFilelnfo
PBHGetFInfo
_HGetFileInfo
PBSetFInfo
_SetFileInfo
PBHSetFInfo
_HSetFileInfo
PBSetFLock
_SetFilLock
PBHSetFLock
_HSetFLock
PBRstFLock
RstFilLock
PBHRstFLock
=HRstFLock
PBSetFVers
_SetFilType
PBRename
_Rename .
PBHRenarhe
HRertame
PBDelete
=Delete
PBHDelete
_HDelete
PBGetCatInfo
_GetCatlnfo
PBSetCatInfo
_SetCatlnfo
PBCatMove
_CatMove
PBOpenWD
_OpenWD
PBCloseWD
_CloseWD
PBGetWDInfo
_GetWDinfo
PBGetFCBInfo _GetFCBinfo
The File Manager
Summary of the File Manager IV-211

<!-- source-page: 222 -->
## Page 222

Inside Macintosh
Special Macro Name
_HFSDispatch
Variables
BootDrive
FSQHdr
VCBQHdr
DefVCBPtr
FCBSPtr
DrvQHdr
ToExtFS
FSFCBLen
Working directory reference number for system startup volume (word)
File I/O queue header (10 bytes)
Volume-control-block queue header ( 10 bytes)
Pointer to default volume control block
Pointer to file-control-block buffer
Drive queue header (10 bytes)
Pointer to external file system
Size of a file control biock; on 64K ROM contains-1 (word)
IV-212 Summary of the File Manager

<!-- source-page: 223 -->
## Page 223

20
THE DEVICE MANAGER
215
About the Device Manager
216
The Chooser
217
The Device Package
217
Communication with the Chooser
218
The NewSelMsg Parameter
218
The FileListMsg Parameter
218
The GetSelMsg Parameter
218
The SelectMsg Parameter
219
The DeselectMsg Parameter
219
The TerminateMsg Parameter
219
The ButtonMsg Parameter
219
Operation of the Chooser
221
Writing a Device Driver to Run Under Chooser
222
Summary of the Device Manager
Contents IV-213

<!-- source-page: 224 -->
## Page 224

Inside Macintosh
IV-214

<!-- source-page: 225 -->
## Page 225

The Device Manager
ABOUTTHEDE~CEMANAGER
While no new routines have been added to the Device Manager, the handling of the existing
routines has been significantly improved.
When an Open call is made, installed drivers are searched first (before resources) to avoid
replacing a current driver; this search is done by name so be sure that your driver's name is
in the driver header. All drivers, exclusive of desk accessories, must have a name that
begins with a period; otherwise, the Open call is passed on to the File Manager.
If a driver is already open, Open calls will not be sent to the driver's open routine,
preserving its device control entry. A desk accessory will, however, receive another call
(certain desk accessories count on this).
If a driver fails to open because of a resource load problem, the Open call terminates with
the appropriate error code instead of being passed on to the File Manager (which would
usually return the result code fnfErr). If a driver returns a negative result code in register
DO from an Open call, the result code is passed back and the driver is not opened. If a
driver returns the result code closeErr in register DO from a Close call, this result code is
passed back and the driver is not closed.
Open, Close, Read, Write, Control, and Status return all results in the ioResult field as well
as in register DO. A KillIO call is passed to the driver only if it's open and enabled for
Control calls.
The number of device control entries in the 128K ROM has been increased from 32 to 48.
The unit table is now a 192-byte nonrelocatable block containing 48 four-byte entries; the
standard unit table assignments are as follows:
Unit Number
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
12-26
27-31
32-39
40-47
Device
Reserved
Hard disk driver: Macintosh XL internal or Hard Disk 20 external
.Print driver
.Sound driver
.Sony driver
Modem port asynchronous driver input (.Ain)
Modem port asynchronous driver output (.AOut)
Printer port asynchronous driver input (.Bln)
Printer port asynchronous driver output (.BOut)
AppleTalk .MPP driver
AppleTalk .ATP driver
Reserved
Desk accessories in System file
Desk accessories in application files
SCSI drivers 0-7
Reserved
About the Device Manager W-215

<!-- source-page: 226 -->
## Page 226

Inside Macintosh
THE CHOOSER
The Chooser is a desk accessory that provides a standard interface to help solicit and accept
specific choices from the user. It allows new device drivers to prompt the user for choices
such as which serial port to use, which AppleTalk zone to communicate with, and which
LaserWriter to use.
The Chooser relies heavily on the List Manager for creating, displaying, and manipulating
possible user selections. The List Manager is described in chapter 30 of this volume.
Under the Chooser, each device is represented by a device resource tile in the system
folder on the user's system startup disk. (This is an extension of the concept of printer
resource files, described in chapter 5 of volume II.) The Chooser accepts three types of
device resource files to identify different kinds of devices:
File type
'PRES'
'PRER'
'RDEV'
Device type
Serial printer
Non-serial printer
Other device
The creator of each file is left undefined, allowing each device to have its own icon.
In addition to any actual driver code, each device resource file of type 'PRER' or 'RDEV'
contains a set of resources that tell the Chooser how to handle the device. These resources
include:
Resource type
Resource ID
Description
'PACK'
-4096
Device package (described below)
'STR I
-4096
Type name for AppleTalk devices
'GNRL'
-4096
NBP timeout and retry information for
'STR I
-4093
AppleTalk devices
Left button title
'STR I
-4092
Right button title
'STR I
-4091
String for Chooser to use to label the list
'BNDL'
when choosing the device
Icon information
'STR I
-4090
Reserved for use by the Chooser
Warning: You should give your device type a distinctive icon, since this may be
the only way that devices are identified in the Chooser's screen display.
Device resource files of type 'PRES' (serial printers) contain only the driver code, without
any of the resources listed above. The configuration of such devices is implemented
entirely by the Chooser.
IV-216 The Chooser

<!-- source-page: 227 -->
## Page 227

The Device Manager
The Device Package
The device package is usually written in assembly language, but may be written partially in
Pascal. The assembly-language structure of the 'PACK' -4096 resource is as follows:
Offset (hex)
0
2
4
8
A c
10
Word
BRA.S to offset $10
Device ID (word)
'PACK' (long word)
$FOOO (-4096)
Version (word)
Flags (long word)
Start of driver code
The device ID is an integer that identifies the device. The version word differentiates
versions of the driver code. The flags field contains the following information:
Bit
31
30-29
28
27
26
25
24
23-17
16
15
14
13
12
11
10-0
Meaning
Set if an AppleTalk device
Reserved (clear to 0)
Set if device package can have multiple instances selected at once
Set if device package uses left button
Set if device package uses right button
Set if no saved zone name
Set if device package uses actual zone names
Reserved (clear to 0)
Set if device package accepts the newSel message
Set if device package accepts the fillList message
Set if device package accepts the getSel message
Set if device package accepts the select message
Set if device package accepts the deselect message
Set if device package accepts the terminate message
Reserved (clear to 0)
Communication with the Chooser
The Chooser communicates with device packages as if they were the following function:
FUNCTION Device (message,caller: INTEGER; objName,zoneName:
StringPtr; pl,p2: LONGINT}
: OSErr;
The message parameter identifies the operation to be performed. It has one of the
following values:
CONST
newSelMsg
fillListMsg
getSelMsg
selectMsg
12;
{new user selections have been made}
13; {fill the list with choices to be made}
14;
{mark one or more choices as selected}
15;
{a choice has actually been made}
The Chooser IV-217

<!-- source-page: 228 -->
## Page 228

Inside Macintosh
deselectMsg
16;
{a choice has been cancelled)
terminateMsg = 17; {lets device package clean up}
buttonMsg
19; {tells driver a button has been selected}
The device package should always return noErr, except with select and deselect; with these
messages, a result code other than noErr prevents selection or deselection from occurring.
The device package must ignore any other messages in the range 0 .. 127 and return noErr.
If the message is selectMsg or deselectMsg, it may not call the List Manager.
The caller parameter identifies the caller as the Chooser, with a value of 1. Values in the
range 0 .. 127 are reserved; values outside this range may be used by applications.
For Apple Talk devices, the zoneName parameter is a pointer to a string of qp to 32
characters containing the name of the Apple Talk zone in which the devices ban be found.
If the Chooser is being used with the local zone and bit 24 of the Flags field of the
'PACK' -4096 resource is clear, the string value is '*'; otherwise it's the actual zone
name.
The p 1 parameter is a handle to a List Manager list of choices for a particular device; this
device list must be filled by the device package in response to the fillListMsg message.
Other details of the Chooser messages and their parameters are given below.
The NewSelMsg Parameter
The Chooser sends the newSel message (instead of the select or deselect message) only to
device packages that allow multiple selections, when the user changes the selection.
The objName and p2 parameters are not used.
The FilllistMsg Parameter
When the Chooser sends the fillList message, the device package should fill a List Manager
list filled with choices for a particular device; the p 1 parameter is a handle to this list.
The objName and p2 parameters are not used.
The GetSelMsg Parameter
When the Chooser sends the getSel messige the device package should mark one or more
choices in the given list as ctitrently selected, by a call to LSetSelect.
The objName and p2 parameters are not used.
The SelectMsg Parameter
The Chooser sends the select message whenever a particular choice has become selected,
but only to device packages that do not allow multiple selections. The device package may
not call the List Manager.
IV-218 The Chooser

<!-- source-page: 229 -->
## Page 229

The Device Manager
If the device accepts fillList messages, objName is undefined. Otherwise, the objName
parameter is a pointer to a string of up to 32 characters containing the name of the device.
If the device accepts fillList messages, p2 gives the row number of the list that has become
selected; otherwise (if the device is an Apple Talk device) p2 gives the AddrBlock value for
the address of the AppleTalk device that has just become selected.
The DeselectMsg Parameter
The Chooser sends the deselect message whenever a particular choice has become
deselected, but only to device packages that do not allow multiple selections. The device
package may not call the List Manager.
If the device accepts fillList messages, objName is undefined. Otherwise, the objName
parameter is a pointer to a string of up to 32 characters containing the name of the device.
If the device accepts fillList messages, p2 gives the row number of the list that has become
desel~cted; otherwise (if the device is an AppleTalk device) p2 gives the AddrBlock value
for the address of the AppleTalk device that has just become deselected.
The TerminateMsg Parameter
The Chooser sends the terminate message when the user selects a different device icon,
closes the Chooser window, or changes zones. It allows the device package to perform
cleanup tasks, if necessary. The device package should not dispose of the device list.
The objName and p2 parameters are not used.
The ButtonMsg Parameter
The Chooser sends the button message when a button in the Chooser display has been
clicked.
·
The low-order byte of the p2 parameter has a value of 1 if the left button has been clicked
and 2 if the right button has been clicked.
The objName parameter is not used.
Operation of the Chooser
When the Chooser is first selected from the desk accessory menu, it searches the system
folder of the startup disk for device resource files-that is, resource files of type 'PRER',
'PRES', or 'RDEV'. For each one that it finds, it opens the file, fetches the device's icon,
The Chooser N-219

<!-- source-page: 230 -->
## Page 230

Inside Macintosh
fetches the flags long word from the device package, and closes the file. The Chooser then
takes the following actions for each device, based on the information just retrieved:
•It displays the device's icon in the Chooser's window.
• If the device is an AppleTalk device and AppleTalk is not connected, the Chooser
grays the device's icon.
When the user selects a device icon that is not grayed, the Chooser reopens the
corresponding device resource file. It then does the following:
• If the device is type 'PRER' or 'PRES', it sets the current printer type to that device.
•It labels the device's list box with the string in the resource 'STR' with an ID of
-4091.
• If the device is a local printer, the Chooser fills its list box with the two icons for the
printer port and modem port serial drivers. Later it will record the user's choice in low
memory and parameter RAM.
• If the device accepts fillList messages, the Chooser calls the device package, which
should fill column 0 of the list pointed to by pl with the names (without length bytes)
of all available devices in the zone.
• If the device is an AppleTalk device that does not accept fillList messages, the Chooser
initiates an asyncqronous routine that interrogates the current AppleTalk zone for all
devices of the type specified in the device's resource 'STR '-4096. The NBP retry
interval and count are taken from the 'GNRL' resource -4096; the format of this
resource consists one byte for the interval followed by another byte for the count. As
responses arrive, the Chooser updates the list box.
• To determine which list choices should be currently selected, the Chooser calls the
device with the getSel message. The device code should respond by inspecting the list
and setting the selected/unselected state of each entry. The Chooser may make this call
frequently; for example, each time a new response to the AppleTalk zone interrogation
arrives. Hence the device should alter only those entries that need changing. This
procedure is not used with serial printers; for them, the Chooser just accesses low
memory.
• The Chooser checks the flag in the 'PACK' -4096 resource that indicates whether
multiple devices can be active at once, and sets List Manager bits accordingly.
Whenever the user selects or deselects a device, the Chooser will call the device
package with th~ appropriate message (if it's accepted). For packages that do not
accept multiple active devices, this is the select or deselect message; otherwise it's the
newSel message. The device code should implement both mounting and unmounting
the device, if approp:riate, and recording the user's selections on disk, preferably in the
device resource file (which is the current resource file).
When the Chooser is deactivated, it calls the UpdateResFile procedure on the device
resource file and flushes the system startup volu~e.
IV-220 The Chooser

<!-- source-page: 231 -->
## Page 231

The Device Manager
When the user chooses a different device type icon or closes the Chooser, the Chooser will
call the device with the terminate message (if it's accepted). This allows device packages to
clean up, if necessary. After this check, the Chooser closes the device resource file (if the
device is not the current printer) and flushes the system startup volume.
Writing a Device Driver to Run Under Chooser
The code section of a driver running under chooser is contained in the 'PACK' -4096
resource, as explained earlier. The driver structure remains as described in chapter 6 of
Volume II.
Device packages initially have no data space allocated. There are two ways to acquire data
space for a device package:
• Use the List Manager
• Create a resource
These options are discussed below.
The best method is to call the Lis~ Manager. The Chooser uses column 0 of the device list
to store the names displayed in the list box. If the device package currently in use does not
accept fillList messages, column 1 stores the four-byte AppleTalk internet addresses of the
entities in the list. Therefore, the device package can use column 1 and higher (if it accepts
fillList) or column 2 and higher to store data private to itself. The standard List Manager
calls can be used to add these columns, place data in them, and retrieve data stored there.
There are several restrictions on data storage in List Manager cells. The list is disposed
whenever:
• the user changes device types.
• the user changes the current zone.
• the device package does not accept fillList messages, and a new response to the
AppleTalk zone interrogation arrives. The device package will be called with the
getSel message immediately afterwards.
When either of the first two situations occurs, the device package is called with the
terminate message before the list is disposed.
Another way to get storage space is to create a resource in the device's file. This file is
always the current resource file when the package is called; therefore it can issue
GetResource calls to get a handle to its storage.
It is important for most device packages to record which devices have been chosen. To do
this, the recommended method is to create a resource in the resource file. This resource can
be of any type; it fact, it's advantageous to provide your own resource type so that no other
program will try to access it. If you choose to use a standard resource type, you should
use only resource IDs in the range-4080 to-4065.
The Chooser IV-221

<!-- source-page: 232 -->
## Page 232

Inside Macintosh
SUMMARY OF THE DEVICE MANAGER
Constants
CONST
{Chooser message values}
Routines
newSelMsg
fillListMsg
getSelMsg
selectMsg
deselectMsg
terminateMsg
buttonMsg
{caller values}
chooserID = 1;
12; {new user selections have been made}
13; {fill the list with choices to be made}
14; {mark one or more choices as selected}
15; {a choice has actually been made}
16; {a choice has been cancelled}
17; {lets device package clean up}
19; {tells driver a button has been selected}
{caller value for the Chooser}
FUNCTION Device (message,caller: INTEGER; objName,zoneName:
StringPtr; pl,p2: LONGINT) : OSErr;
Assembly-Language Information
Constants
; Chooser message values
newSel
fillList
getSel
select
deselect
terminate
button
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
.EQU
; Caller values
chooser ID
.EQU
12
13
14
15
16
17
19
1
;new user selections have been made
;fill the list with choices to be made
;mark one or more choices as selected
;a choice has actually been made
;a choice has been cancelled
;lets device package clean up
;tells driver a button has been selected
;caller value for the Chooser
Device Package Data Structure
Byte
0
2
4
8
A c
10
Value
BRA.S to offset $10
Device ID (word)
'PACK' (long word)
$FOOO (-4096)
Version (word)
Flags (long word)
Start of driver code
W-222 Summary of the Device Manager

<!-- source-page: 233 -->
## Page 233

21
THE DISK DRIVER
The Disk Driver has been extended to support the double-sided 3 1/2-inch drive and the
Apple Hard Disk 20™ drive; support for the single-sided 3 1/2-inch drive is of course
maintained. A second Hard Disk 20 drive, an external double-sided drive, or an external
single-sided drive can also be connected through the pass-through connector of a Hard
Disk 20.
The Disk Driver's name remains '.Sony' and the reference number for 3 1/2-inch drives
(both single-sided and double-sided) is still -5. The drive numbers for the 3 1/2-inch
drives-I for the internal drive and 2 for the external drive-are also unchanged.
The Hard Disk 20 has a reference number of -2 and drive numbers of 3 and 4. The Hard
Disk 20 returns 20 tag bytes per sector instead of the 12 bytes returned by the 3 1/2-inch
drives.
The new Disk Driver ignores KillIO calls; as before, you cannot make immediate calls to
this driver. Read-verify mode is still supported for 3 1/2-inch drives, but has no effect on
hard disk drives. A new track cache feature speeds the disk access on 3 1/2-inch drives; an
advance control call (described below) let you control this feature.
The DiskEject function, if used with a hard disk drive, returns the Device Manager result
code controlErr; at the next Disk Driver vertical retrace task, a disk-in-place event is
reposted for that drive.
Assembly-language note: The additional eight bytes of tag data for the Hard
Disk 20 are stored in the global variable TFSTagData.
ADVANCED CONTROL CALLS
This section describes several advanced control calls used by the Operating System; you
will probably have no need to use them.
csCode = 5
This call verifies that the disk in the drive specified by ioRefNum in the parameter block
data structure (including hard disks) is correctly formatted.
csCode = 6
csParam = integer
This call formats the disk in the drive specified by ioRefNum in the parameter block data
structure. With the Hard Disk 20, it zeros all blocks. A csParam value of 1 causes it to
Advanced Control Calls W-223

<!-- source-page: 234 -->
## Page 234

Inside Macintosh
format a single-sided 3 1/2-inch disk in a double-sided drive; otherwise, the value of
csParam should be 0.
Warning: Use this call with care. It's normally used only by the Disk Initialization
Package.
csCode = 9
csParam = integer
This call controls the track cache feature. The high-order byte of csParam is nonzero to
enable the cache feature and 0 to disable it. The low-order byte of csParam is 1 to install
the cache, -1 to remove it, and 0 to do neither. The cache is located in the system heap; the
driver will relinquish cache space, if necessary, when the GrowZone function is called for
the system heap.
csCode = 21
csParam = ptr (long)
This call works only with the Hard Disk 20; it returns a pointer to an icon data structure
whose format is identical to that of an 'ICN#' resource. The drive number must be in
ioRefNum in the parameter block data structure.
SUMMARY OF THE DISK DRIVER
Advanced Control Calls
csCode csParam
Effect
5
Verifies disk formatting
6
integer
Formats a disk
9
integer
Controls track cache feature
21
ptr (long)
Fetches hard disk icon
Assembly-Language lnfonnation
Variables
TFSTagData
Additional 8 bytes of Hard Disk 20 tag data
W-224 Summary of the Disk Driver

<!-- source-page: 235 -->
## Page 235

22 THE SERIAL DRIVER
In the 128K ROM, a single new Serial priver replaces the RAM and ROM Serial Drivers.
Note: The new Serial Driver has a version number of 2. The old ROM driver had a
version number of 0, and the old RAM driver a version number of 1.
For best results, include the RAM Serial Drivers as resources of type 'SERD' in the
resource fork of your application and continue to use RAMSDOpen and RAMSDClose. If
the 128K ROM is present, the new driver is automatically substituted.
The new Serial Driver verifies that the serial port is qo:rrectly configured and free; if not, the
result code portNotCf or portInUse is returned. When opened, the Serial Driver defaults to
hardware handshake on (as did the old ROM driver).
The Data Terminal Ready (DTR) line in the RS232 interface is now automatically asserted
when the Serial Driver is opened; DTR is negated when it is closed. Control calls let you
explicitly set the state of this line, as well as use it to automatically control the input data
flow from an external device.
New advanced control calls let you control the DTR line, set certain control options, and
modify the translation of parity error default characters; they're described below.
All control and status calls may be immediate. (For information about immediate calls, see
chapter 6 of Volume II.)
·
The following bugs have been fixed:
• The procedure RAMSDClose preserves mouse interrupts during its execution.
• The execution of break and close routines is now synchronized to the current
transmission.
·
• Incoming clock pulses on the CTS line are now detected; if they're present, CTS
interrupts are disabled.
• If you open only the input channel of a driver, the Open routine checks to see if the
necessary variables have been initialized and exits if they have not.
The Serial Driver IV-225

<!-- source-page: 236 -->
## Page 236

Inside Macintosh
ADVANCED-CONTROL CALLS
This section describes several new advanced control calls. Control calls to the Serial Driver
should be made to the output character channel driver.
csCode = 14
csPara:m through csParam+ 7 = serShk
This call is identical to a control call with csCode=lO (the Serf{Shake function, described
in the chapter 9 of Volume II) with the additional specification of the DTR handshake
option in the eighth byte of its flags parameter (the null field of the SerShk record). You
ciµi enable DTR input flow control by setting this pyte to a nonzero value. This works
s~etrically to hardware handshake output control.
csCode = 16
csParam = byte
This call sets miscellaneous control options. Bits 0-6 should be set to 0 for future options.
Bit 7, if set to 1, will cause DTR to be left unchiµiged when the driver is closed (rather than
the normal procedure of negating DTR). This may be used for modem control to prevent
the modem from hanging up just because the driver is being closed (such as when the user
temporarily exits ~e terminal program).
csCode = 17
This call asserts DTR.
csCode = 18
This call negates DTR.
csCode = 20
csParam =char csParam+l =alt char
Thi~ call is an extension of call 19, which would simply clear bit 7 of an incoming character
whe~ it matched the replacement character. After this call is made, all incoming characters
with parity errors will be replaced by the character specified by the ASCII co4e in csParam.
If csParam is 0, no character replacement will be done. If an incoming character is the same
as the replacement character specified in csParam, it will be replaced instead ~Y the seco~d
ch~~t~r specified in csParam+ 1.
-
Note; With this call, the null character (ASCII $00) can be used as the alternate
character brit ~ot as the first replacement.
IV-226 Advanced Control Calls

<!-- source-page: 237 -->
## Page 237

The Serial Driver
SUMMARY OF THE SERIAL DRIVER
Constants
CONST
{ Indication that DTR is negated }
dtrNegated = $40;
{ Result codes }
portInUse
-97
f driver Open error, port already in use}
portNotCf
-98
{driver Open error, port not configured for
{ this connection}
mernFullErr
-108; {not enough room in heap zone}
Data Typ~s
Ser$hk
PACKED RECORD
fXOn:
fGTS:
xOn:
xQff;
errs:
evts:
finX;
fDTR:
END;
Byte;
Byte;
CHAR;
CHAR;
Byte;
Byte;
Byte;
Byte
{XOn/XOff output flow control flag}
{CTS hardware hqndshake f!ag}
{XOn character}
{XOff character}
{er~or$ that cause abort}
{status changes that cause events}
{XOn/XOff input flow control flag}
{DTR input flow control flag}
Aclv~ced Control Calls
cs Code
14
16
17
18
20
csParam
serShk
byte
2 chars
Effect
Set handshake parameters
Set miscellaneous control options
Asserts DTR
NegatesDTR
Replace parity errors, with alternate replacement character
Summary of the Serial Driver IV-227

<!-- source-page: 238 -->
## Page 238

Inside Macintosh
Assembly-Language lnfonnation
Constants
; Result codes
portInUse
.EQU
-97
;driver Open error, port already in use
portNotCf
.EQU
-98
;driver Open error, port not configured for
; this connection
memFullErr
.EQU
-108
;not enough room in heap zone
Structure of Control lnformatiQn for SerHShake
shFXOn
shFCTS
shXOn
shXOff
sh Errs
shEvts
shFinX
shDTR
XOn/XOff output flow control flag (byte)
CTS hardware handsh~e flag (byte)
XOn character (byte)
XOff character (byte)
Errors that cause abort (byte)
Status changes that cause events (byte)
XOn/XOff input flow control flag (byte)
DTR control flag (byte)
W-228 Summary of the Serial Driver

<!-- source-page: 239 -->
## Page 239

23 THE APPLETALK MANAGER
The two AppleTalk: device drivers, named .MPP and .ATP, are included in the 128K
ROM. The AppleTalk: Manager, however (the interface to the drivers), is not in ROM;
your application must link to the appropriate object files.
On the Macintosh Plus, you need only open the .MPP driver, this will also load the .ATP
driver and NBP code automatically. Since, in the 128K ROM, device drivers return errors,
it's no longer necessary to check whether port B is free and configured for AppleTalk. If
port B isn't available, the .MPP driver won't open and the result code portInUse or
portNotCf will be returned.
Assembly-language note: When called from assembly language, the Datagram
Delivery Protocol (DDP) allows 14 (instead of 12) open sockets.
The AppleTalk Manager IV-229

<!-- source-page: 240 -->
## Page 240

24 THE SYSTEM ERROR HANDLER
A new system error, user alert ID 84, has been added. This error results when the Menu
Manager tries to access a menu that's been purged.
The System Error Handler IV-231

<!-- source-page: 241 -->
## Page 241

Inside Macintosh
IVi232

<!-- source-page: 242 -->
## Page 242

25 THE OPERATING SYSTEM UTILITIES
Because in the 128K ROM there can be both an Operating System trap and a Toolbox trap
for any given trap number (for details, see the Using Assembly Language chapter), two
variants of GetTrapAddress and SetTrapAddress have been added. These new routines,
NGetTrapAddress and NSetTrapAddress, require you to specify whether the given trap
number refers to an Operating System trap or a Toolbox trap; the following data type is
defined for this purpose:
TYPE TrapType =
(OSTrap,ToolTrap);
The RelString function fills the need for a full-magnitude, language-independent string
comparison, particularly in the hierarchical file system, where entries are sorted in
alphabetical order. Whereas the EqualString function compares two strings only for
equality, RelString compares two strings and returns a value indicating whether the the first
string is less than, equal to, or greater than the second string.
You can use the existing routine Environs to determine whether the 128K ROM is in use; a
description of this procedure is provided below.
OPERATING SYSTEM UTILITY ROUTINES
Assembly-language note: To use GetTrapAddress and SetTrapAddress with
128K ROM routines, set bit 9 of the trap word to indicate the new trap numbering.
The state of bit 10 then determines whether the intended trap is a Toolbox or
Operating System trap. You can set these two bits with the arguments NEW OS and
NEWTOOL.
Of course, the 64K ROM versions of GetTrapAddress and SetTrapAddress will fail
if applied to traps that exist only in the 128K ROM.
The NGetTrapAddress and NSetTrapAddress routines list the possible permutations
of arguments. (The syntax shown applies to the Lisa Workshop Assembler;
programmers using another development system should consult its documentation
for the proper syntax.)
Operating System Utility Routines IV-233

<!-- source-page: 243 -->
## Page 243

Inside Macintosh
FUNCTION NGetTrapAddress (trapNum: INTEGER; tType: TrapType) :
LONG INT;
[Not in ROM]
NGetTrapAddress is identical to GetTrapAddress except that it requires you to specify in
tType whether the given routine is an Operating System or a Toolbox trap.
Trap macro
On entry
On exit
_GetTrapAddress .~wos
_GetTrapAddress ,NEWTOOL
DO: trapNum (word)
AO: address of routine
(bit 9 set, bit 10 clear)
(bit 9 set, bit 10 set)
PROCEDURE NSetTrapAddress (trapAddr: Longint; trapNum: INTEGER;
tType: TrapType);
[Not in ROM]
NSetTrapAddress is identical to SetTrapAddress except that it requires you to specify in
tType whether the given routine is an Operating System or a Toolbox trap.
Trap macro
On entry
_SetTrapAddress ,NEWOS
_SetTrapAddress ,NEWTOOL
AO: trapAddr (address)
DO: trapNum (word)
(bit 9 set, bit 10 clear)
(bit 9 set, bit 10 set)
FUNCTION RelString (aStr,bStr: Str255; caseSens,diacSens: BOOLEAN)
: INTEGER;
RelString is similar to EqualString except that it indicates whether the first string is less
than, equal to, or greater than the second string by returping either -1, 0, or 1 respectively.
Trap macro
On entry
On exit
_RelString
_RelString ,MARKS
_RelString ,CASE
_RelString ,MARKS,CASE
(sets bit 9, for diacSens=FALSE)
(sets bit 10, for caseSens=TRUE)
(sets bits 9 and 10)
AO: pointer to first character of first string
Al: pointer to first character of second string
DO: high-order word: length of first string
low-order word: length of second string
DO: -1 if first string less than second, 0 if equal, 1 if first string
greater than second (long word)
IV-234 Operating System Utility Routines

<!-- source-page: 244 -->
## Page 244

The Operating System Utilities
RelString follows the sort order described in chapter 19 of Volume I except for the
reordering of the following ligatures:
lE falls between A and a
re falls between A and B
CE falls between 0 and o
re falls between ¢ and P
B falls between s and T
If diacSens is FALSE, diacritical marks are ignored; RelString strips diacriticals according
to the following table:
A <-
A,A,A.,A
c <-
<;
E <-
E
N <-
:N
0
<-
g,6,0
u <-
u
a
<-
a, a., a, a., a, 1l, !
c
<-
~
e
<-
e, e, e, e
i
<-
f, l, 1, r
n
<-
ii
0
<-
6, o, o, o, 6, ¢, Q
u
<-
u, u, fi, ii
y
<-
y
Note: This stripping is identical to that performed by the UprString procedure when
the diacSens parameter is FALSE.
If caseSens is FALSE, the comparison is not case-sensitive; RelString performs a
conversion from lower-case to upper-case characters according to the following table:
A <-
a
... <-
z <-
z
A. <-
a.
A <-
a
A <-
a
A <-
A
lE <-
re
<; <-
~
E <-
e
:N <-
ii
0 <-
0
6 <-
6
0 <-
¢
CE <-
re
u <-
ii
Note: This conversion is identical to that performed by the UprString procedure.
Operating System Utility Routines IV-235

<!-- source-page: 245 -->
## Page 245

Inside Macintosh
PROCEDURE Environs (VAR rom, machine: INTEGER)
[Not in ROM]
In the rom parameter, Environs returns the current ROM version number (for a Macintosh
XL, the version number of the ROM image installed by Mac Works). To use the 128K
ROM information described in this volume, the version number should be greater than or
equal to 117 ($7 5). In the machine parameter, Environs returns an indication of which
machine is in use, as follows:
CONST macXLMachine
macMachine
O;
l;
{Macintosh XL}
{Macintosh 128K, 512K, 512K upgraded, }
{ 512K enhanced, or Macintosh Plus}
Note: The machine parameter does not distinguish between the Macintosh 128K,
512K, 512K upgraded, 512K enhanced, and Macintosh Plus.
Assembly-language note: From assembly language, you can get this
information from the word that's at an offset of 8 from the beginning of ROM (which
is stored in the global variable ROMBase ). The format of this word is $00xx for the
Macintosh 128K, 512K, 512K enhanced, or Macintosh Plus, and $xxFF for the
Macintosh XL, where xx is the ROM version number. (The ROM version number
will always be between $01 and $FE.)
SUMMARY OF THE OPERATING SYSTEM UTILITIES
Constants
CONST {Values returned by the Environs procedure}
macXLMachine
0;
macMachine
= 1;
Data Types
{Macintosh XL}
{Macintosh 128K, 512K, 512K upgraded,
{ 512K enhanced, or Macintosh Plus}
TYPE TrapType
(OSTrap,ToolTrap);
Routines
FUNCTION
NGetTrapAddress
(trapNum: INTEGER; tType: TrapType) :
Longint;
[Not in ROM]
(trapAddr: Longint; trapNum: INTEGER; tType:
TrapType) ;
[Not in ROM]
PROCEDURE NSetTrapAddress
FUNCTION
RelString
(aStr,bStr: Str255; caseSens,diacSens:
BOOLEAN)
: INTEGER;
PROCEDURE Environs
(VAR rom, machine: INTEGER)
[Not in ROM]
IV-236 Summary of the Operating System Utilities

<!-- source-page: 246 -->
## Page 246

The Operating System Utilities
Assembly-Language Information
Routines
Trap macro
On entry
On exit
_GetTrapAddress
_GetTrapAddress ,NEWOS
(bit 9 set, bit 10 clear)
_GetTrapAddress ,NEWTOOL
(bit 9 set, bit 10 set)
DO: trapNum (word)
AO: address of routine
_SetTrapAddress
_SetTrapAddress ,NEWOS
(bit 9 set, bit 10 clear)
_SetTrapAddress ,NEWTOOL
(bit 9 set, bit 10 set)
AO: trapAddr (address)
DO: trapNum (word)
_RelString
_RelString ,MARKS
Variables
ROMBase
(sets bit 9, for diacSens=FALSE)
_RelString ,CASE
(sets bit 10, for caseSens=TRUE)
_RelString ,MARKS.CASE
(sets bits 9 and 10)
AO: ptr to first string
DO: -1 if first less than second,
A 1: ptr to second string
0 if equal, 1 if first greater
DO: high word: length of
than second (long)
first string
low word: length of
second string
Base address of ROM
Summary of the Operating System Utilities IV-237

<!-- source-page: 247 -->
## Page 247

Inside Macintosh
IV-238

<!-- source-page: 248 -->
## Page 248

26 THE DISK INITIALIZATION PACKAGE
This chapter describes the Disk Initialization Package found in the system resource file.
The package and its resources together occupy about 5.3K bytes.
The Disk Initialization Package initializes disks, formatting the disk medium and placing the
appropriate file directory structure on the disk. Earlier versions of the Disk Initialization
Package format a 3 1/2-inch disk on a single side only, creating a 400K-byte volume and
placing a flat file directory on the disk. The new version of the Disk Initialization Package
can format the 3 1/2-inch disks on either one or both sides, creating 400K or SOOK
volumes respectively. It will format other devices (such as hard disks) as well; the size of
volumes is determined by the driver for the particular device.
When the 12SK ROM version of the File Manager is present, all volumes except the 400K,
single-sided disks are automatically given hierarchical file directories. (Even the 400K
disks can be given a hierarchical directory by holding down the option key.) If the 128K
version of the File Manager is not present, all volumes are given flat file directories.
The DIFormat function formats disks in single-sided disk drives as 400K volumes and
disks in double-sided drives as SOOK volumes; the size of all other volumes is determined
by the driver for the particular device.
The DIZero function places a flat file directory on disks in single-sided disk drives and a
hierarchical file directory on disks in double-sided drives as SOOK volumes. With all other
devices, the type of directory placed on a volume is determined by the driver for the
particular device.
The DIBadMount function is called with the result code returned by Mount Vol as a
parameter. Based on the value of this result code, on the type of drive containing the disk,
and on the disk itself, DIBadMount decides what messages and buttons to display in its
dialog box.
The dialog displayed by DIBadMount gets its messages and buttons from a dialog item list
('DITL' resource-6047). The new dialog item list contains messages and buttons for
responding to all situations, but it's possible that a new Disk Initialization Package might
run into an old dialog item list. The new Disk Initialization Package determines which item
list it's using, and makes certain choices as to the best buttons and messages to display.
If the user places a double-sided disk into a single-sided drive, MountVol returns ioErr. If
there's a new item list, the message "This is a two-sided disk!" is displayed; if there's an
old item list, the message "This disk is unreadable:" is used instead.
If the user tries to erase or format a disk that's write-protected, and there's a new item list,
the messages "Initialization failed!" and "This disk is write-protected!" will be displayed.
If there's an old item list, the second message is omitted.
If the user tries to erase or format a disk that's not ejectable, and there's a new item list, the
Eject button that's normally displayed is replaced by a Cancel button.
The Disk Initialization Package IV-239

<!-- source-page: 249 -->
## Page 249

Inside Macintosh
If the user tries to erase or format a disk in a double-sided drive, and there's a new item
list, three buttons are displayed: Eject, One-sided, and Two-sided. If an old version of the
item list is present, only two buttons are displayed: Eject and Initialize. If the user chooses
the Initialize button, the disk is formatted as an SOOK volume (and if the hierarchical
version of the File Manager is present, a hierarchical file directory is written).
If the user tries to erase or format a disk in a single-sided drive, only two buttons are
displayed (regardless of which version of the Disk Initialization Package or item list is
present): Eject and Initialize. If the user chooses the Initialize button, the disk is formatted
as a 400K, flat volume. With other types of devices, the user can choose to eject the
volume or format it with a size determined by the driver.
When the result code noErr is passed, DIBadMount can be used to reformat a valid,
mounted volume without changing its name. This can be used, for instance, to change the
format of a disk in a double-sided drive from single-sided to double-sided. If there's a new
item list, your application can specify its own message using the Dialog Manager
procedure ParamText; the message can be up to three lines long. The message is stored as
the string ""0". (Because the TextEdit procedure TextBox is used to display statText
items, word wraparound is done automatically.) If there's an old item list, the message
"Initialize this disk?" is displayed instead.
Warning: If your application uses this call, it must call DILoad before ejecting the
system disk. This will prevent accidental formatting of the system disk.
Note: The volume to be reformatted must be mounted when DIBadMount is called.
Formatting Hierarchical Volumes
The Disk Initialization Package must set certain volume characteristics when placing a
hierarchical file directory on a volume. Default values for these volume characteristics are
stored in the 128K ROM; this section is for advanced programmers who want to substitute
their own values. The record containing the default values, if defined in Pascal, would
look like this:
TYPE HFSDefaults =
PACKED RECORD
sigWord:
ARRAY[l .. 2] OF CHAR;
{signature word}
abSize:
LONGINT;
{allocation block size in bytes}
clpSize:
LONGINT;
{clump size in bytes}
nxFreeFN:
LONGINT;
{next free file number}
btClpSize: LONGINT;
{B*-Tree clump size in bytes}
rsrvl:
INTEGER;
{reserved}
rsrv2:
INTEGER;
{reserved}
rsrv3:
INTEGER;
{reserved}
END;
W-240 The Disk Initialization Packa,ge

<!-- source-page: 250 -->
## Page 250

The default values for these fields are as follows:
Field
sigWord
abSize
clpSize
nxFreeFN
btClpSize
Default value
'BD'
0
4 * abSize
16
0
The Disk Initialization Package
To supply your own values for these fields, create a similar, nonrelocatable record
containing the desired values and place a pointer to it in the global variable FmtDefaults.
To restore the system defaults, simply clear FmtDefaults.
The sigWord must equal 'BD' (meaning "big disk") for the volume to be recognized as a
hierarchical volume. If the specified allocation block size is 0, the allocation block size is
calculated according to the size of the volume:
abSize = (1 + (volSize in blocks I 64K)) * 512 bytes
If the specified B*-tree clump size is 0, the clump size for both the catalog and extent trees
is calculated according to the size of the volume:
btClpSize = (volSize in blocks)/128 * 512bytes
SUMMARY OF THE DISK INITIALIZATION PACKAGE
Variables
FmtDefaults
Pointer to substitute values for hierarchical volume characteristics
Summary of the Disk Initialization Package IV-241

<!-- source-page: 251 -->
## Page 251

27 THE FINDER INTERFACE
The Finder has been modified to work with the hierarchical file system. In the 64K ROM,
the user's perceived desktop hierarchy of folders and files is essentially an illusion
maintained (at great expense) by the Finder. In the 128K ROM version of the File
Manager, this hierarchy is recorded in the file directory itself, relieving the Finder of the
task of maintaining this information.
THE DESKTOP FILE
Most of the information used by the Finder is kept in a resource file named Desktop. (The
Finder doesn't display this file on the Macintosh desktop, to ensure that the user won't
tamper with it.) On flat volumes, file and folder information is kept in resources known as
file opjects (resources of type 'FOBJ'). On hierarchical volumes, the only dynamic file
object data remaining in the Desktop file are the Get Info comments. The other information
about files and folders is maintained by the File Manager; for more details, see the section
"Information Used by the Finder" in chapter 19 of this volume.
With flat volumes, the Finder enumerates the entire volume; this means that it can always
locate a particular application by scanning through all the file objects in memory. With
hierarchical volumes, however, the Finder searches only open folders, so there's no
guarantee that it will see the application. A new data structure, called the application
list, is kept in the Desktop file for launching applications from their documents in the
hierarchical file system. For each application in the list, an entry is maintained that includes
the name and signature of the application, as well as the directory ID of the folder
containing it.
Whenever an ~pplication is moved or renamed, its old entry in the list is removed, and a
new entry is added to the top of the list. The list is rebuilt when the desktop is rebuilt; this
makes the rebuilding process much slower since the entire volume must be scanned.
Note: The user has control over the search order in the sense that the most recently
moved or added applications will be at the top of the list and will be matched f~st
The Desktop File IV-243

<!-- source-page: 252 -->
## Page 252

28 THE MACINTOSH PLUS HARDWARE
This chapter describes the hardware features of the Macintosh Plus. Two of these
features-the 800K internal disk drive and the 128K ROM-are also found in the
Macintosh 512K enhanced. This chapter covers only the new features and does not repeat
information already covered in chapter 2 of Volume ill.
Note: A partially upgraded Macintosh 512K is identical to the Macintosh 512K
enhanced, while a completely upgraded Macintosh 512K includes all the features of
the Macintosh Plus.
This chapter is oriented toward assembly-language programmers and assumes you're
familiar with the basic operation of microprocessor-based devices. Knowledge of the
Macintosh Operating System will also be helpful. To learn how your program can
determine the hardware environment in which it's operating, see the description of the
Environs procedure in chapter 25 of this volume.
Warning: Memory sizes, addresses and other data specific to the Macintosh Plus
are presented in this chapter. To maintain software compatibility across the
Macintosh line, and to allow for future changes to the hardware, you 're strongly
advised to use the Toolbox and Operating System routines wherever provided. In
particular, use the low-memory global variables to reference hardware; never use
absolute addresses.
OVERVIEW OF THE HARDWARE
Features of the Macintosh 512K enhanced (not found in the Macintosh 128K and 512K)
are:
• 800K internal disk drive
• 128KROM
Features of the Macintosh Plus are:
• 800K internal disk drive
• 128KROM
• SCSI high-speed peripheral port
• lMb RAM, expandable to 2Mb, 2.SMb, or 4Mb.
• 2 Mini-8 connectors for serial ports, replacing the 2 DB-9 connectors
found on the Macintosh 128K, 512K, and 512K enhanced.
• keyboard with built-in cursor keys and numeric keypad
Overview of the Hardware IV-245

<!-- source-page: 253 -->
## Page 253

Inside Macintosh
The Macintosh Plus contains the Motorola MC68000 microprocessor clocked at 7.S336
megahertz, random access memory (RAM), read-only memory (ROM), and several chips
that enable it to communicate with external devices. In addition to the five I/O devices
found in the Macintosh 12SK, 512K, and 512K enhanced (the video display, sound
generator, VIA, SCC and IWM), the Macintosh Plus contains a NCR 53SO Small
Computer Standard Interface (SCSI) chip for high-speed parallel communication with
devices such as hard disks.
In the Macintosh Plus, the 16 Mb of addressable space is divided into four equal sections.
The first four megabytes are for RAM, the second four megabytes are for ROM and SCSI,
the third are for the SCC, and the last four are for the IWM and the VIA. Since the devices
within each block may have far fewer than four megabytes of individually addressable
locations or registers, the addressing for a device may "wrap around" (a particular register
appears at several different addresses) within its block.
RAM
The Macintosh Plus RAM is provided in four packages known as Single In-line Memory
Modules (SIMMs). Each SIMM contains eight surface-mounted Dynamic RAM (DRAM)
chips on a small printed circuit board with electrical "finger" contacts along one edge.
Various RAM configurations are possible depending on whether two or four SIMMs are
used and on the density of the DRAM chips that are plugged into the SIMMs:
• If the SIMMs contain 256K-bit DRAM chips, two SIMMs will provide 512K bytes of
RAM, or four SIMMs will provide lMb of RAM (this is the standard configuration).
• If the SIMMs contain lM-bit DRAM chips, two SIMMs will provide 2Mb of RAM,
or four SIMMs will provide 4Mb of RAM.
• If two of the SIMMs contain lM-bit DRAM chips, and two of the SIMMs contain
256K-bit DRAM chips, then these four SIMMs will provide 2.5Mb of RAM. For this
configuration, the lM-bit SIMMs must be placed in the sockets closest to the 6SOOO
CPU.
Warning: Other configurations, such as a single SIMM or a pair of SIMMs
containing DRAMs of different density, are not allowed. If only two SIMMs are
installed, they must be placed in the sockets closest to the MC6SOOO.
The SIMMs can be changed by simply releasing one and snapping in another. However,
there are also two resistors on the Macintosh Plus logic board (in the area labelled "RAM
SIZE") which tell the electronics how much RAM is installed. If two SIMMs are plugged
in, resistor R9 (labeled "ONE ROW") must be installed; if four SIMMs are plugged in, this
resistor must be removed. Resistor RS (labelled "256K BIT'') must be installed if all of the
SIMMs contain 256K-bit DRAM chips. If either two or four of the SIMMs contain lM-bit
chips, resistor RS must be removed.
Each time you turn on the Macintosh Plus, system software does a memory test and
determines how much RAM is present in the machine. This information is stored in the
global variable MemTop, which contains the address (plus one) of the last byte in RAM.
W-246 Overview of the Hardware

<!-- source-page: 254 -->
## Page 254

The Macintosh Plus Hardware
ROM
The Macintosh Plus contains two 512K-bit (64K x 8) ROM chips, providing 128K bytes
of ROM. This is the largest size of ROM that can be installed in a Macintosh 128K, 512K,
or 512K enhanced. The Macintosh Plus ROM sockets, however, can accept ROM chips of
up to lM-bit (128K x 8) in size. A configuration of two lM-bit ROM chips would provide
256K bytes of ROM.
THE VIDEO INTERFACE
The starting addresses of the screen buffers depend on the amount of memory present in
the machine. The following table shows the starting address of the main and the alternate
screen buff er for various memory configurations of the Macintosh Plus:
System
Main Screen
Alternate
Macintosh Plus, lMb
$FA700
$F2700
Macintosh Plus, 2Mb
$1FA700
$1F2700
Macintosh Plus, 2.5Mb
$27A700
$272700
Macintosh Plus, 4Mb
$3FA700
$3F2700
Warning: To ensure that software will run on Macintoshes of different memory
size, as well as on future Macintoshes, use the address stored in the global variable
ScrnBase. Also, the alternate screen buffer may not be available in future versions of
the Macintosh and may not be found in some software configurations of current
Macintoshes.
THE SOUND GENERATOR
The starting addresses of the sound buffers depend on the amount of memory present in the
machine. The following table shows the starting address of the main and the alternate
sound buffer for various memory configurations of the Macintosh Plus:
System
Macintosh Plus, lMb
Macintosh Plus, 2Mb
Macintosh Plus, 2.5Mb
Macintosh Plus, 4Mb
Main Sound
$FFDOO
$1FFDOO
$27FDOO
$3FFDOO
Alternate
$FA100
$1FA100
$27A100
$3FA100
The Sound Generator IV-247

<!-- source-page: 255 -->
## Page 255

Inside Macintosh
Warning: To ensure that software will run on Macintoshes of different memory
size, as well as future Macintoshes, use the address stored in the global variable
Sound.Base. Also, the alternate sound buffer may not be available in future versions
of the Macintosh and may not be found in some software configurations of current
Macintoshes.
THESCC
The Macintosh Plus uses two Mini-8 connectors for the two serial ports, replacing the two
DB-9 connectors used for the serial ports on the Macintosh 128K, 512K, and 512K
enhanced.
The Mini-8 connectors provide an output handshake signal, but do not provide the +5
volts and+ 12 volts found on the Macintosh 128K, 512K, and 512K enhanced serial
ports.
The output handshake signal for each Macintosh Plus serial port originates at the SCC's
Data Terminal Ready (DTR) output for that port, and is driven by an RS423 line driver.
Other signals provided include input handshake/external clock, Transmit Data + and -,
and Receive Data+ and-.
Figure 1 shows the Mini-8 pinout for the SCC serial connectors.
1
Output handshake
2
Input handshake I external clock
3
Transmit data -
4
Ground
5
Receive data -
6
Transmit data +
7
(not connected)
8
Receive data +
Figure 1. Pinout for SCC Serial Connectors
Diagram
Figure 2 shows a circuit diagram for the Macintosh Plus serial ports.
W-248 TheSCC

<!-- source-page: 256 -->
## Page 256

RTxCA
3.672 MHz
112 of 26LS32
0
I+
RFI Filter
Rx DA
I-
RFI Filter
CTSA
0
RFI Filter
TRxCA
1/2 of 9636A (or 3488A)
DTRA
I
o-
RFI Filter
W/REQA
6522 (VIA)
W/REQs---PA7 ----
112 of 26LS30
I
o-
RFI Filter
TxD9
O+
RTS9
OE
RFI Filter
Slew-rate Not
+5v 'kc controls connected
-5V 'vf E
Mode
PCLK
":"
RTxC9
3.672 MHz
1/2 of 26LS32
0
I+
RFI Filter
RxD9
I-
RFI Filter
CTS9
RFI Filter
TRxC9
1/2 of 9636A (or 3488A)
The Macintosh Plus Hardware
TXDA-
TXDA+
RXDA+
HSKiA
HSKoA
Note:
A1
R2
~=~
:he
TXDs-
TXDs+
RXD9+
RXDs-
HSKis
(A1+A2 = 40 to 60 ohms,
C = 150 to 300 pF)
DTR9
I
o-
RFI F1lter~---H_SK_o_.9.__ ___
___.
+12V 'kc
Wave
-12V \EE
Shape L-1\. '" -
----
.......,;....__.....,. 10K _
Figure 2. Circuit Diagram for the Macintosh Plus Serial Ports
The sec IV-249

<!-- source-page: 257 -->
## Page 257

Inside Macintosh
THE KEYBOARD
The Macintosh Plus keyboard, which includes a built-in numeric keypad, contains a
microprocessor that scans the keys. The microprocessor contains ROM and RAM, and is
programmed to conform to the same keyboard interface protocol described in chapter 2 of
Volume III.
The Macintosh Plus keyboard reproduces all of the key-down transitions produced by the
keyboard and optional keypad us~d by the Macintosh 128K, 512K, and 512K enhanced;
the Macintosh Plus keyboard is also completely compatible with these other machines. If a
key transition occurs for a key that used to be on the optional keypad in lowercase, the
Macintosh Plus keyboard still responds to an Inquiry command by sending back the
Keypad response ($79) to the Macintosh Plus. If a key transition occurs for an key that
used to be on the optional keypad in uppercase, the Macintosh Plus keyboard responds to
an Inquiry command by sending back the Shift Key-down Transition response ($71),
followed by the Keypad response ($79). The responses for key-down transitions on the
Macintosh Plus are shown (in hexadecimal) in Figure 3.
'
65.
Shift
71
Ootion
75
space
63
U.S. end International Keyboard
+
18 •
11
Figure 3. Key-Down Transitions
THE FLOPPY DISK INTERFACE
Clear =
OF
11
7
8
33 37
4
5
2D 2F
1
2
27 29
0
25
I
"'
18 05
g
-
39 1D
6
+
31
OD
3
Enter
28 .
03 19
The Macintosh Plus has an internal double-sided disk drive; an external double-sided drive
or the older single-sided drive, can be attached as well.
Note: The external double-sided drive can be attached to a Macintosh 512K through
the back of a Hard Disk 20. The Hard Disk 20 start-up software contains a device
driver for this drive and the hierarchical (128K ROM) version of the File Manager.
W-250 The Floppy Disk Interface

<!-- source-page: 258 -->
## Page 258

The Macintosh Plus Hardware
The double-sided drive can format, read, and write both SOOK double-sided disks and
400K single-sided disks. The operation of the drive with double-sided disks differs from
that on single-sided disks. With double-sided disks, a single mechanism positions two
read/write heads-one above the disk and one below-so that the drive can access two
tracks simultaneously-one on the top side, and a second, directly beneath the first, on the
bottom side. This lets the drive read or write two complete tracks of information before it
has to move the heads, significantly reducing access time. For 400K disks, the doublesided drive restricts itself to one side of the disk.
Warning: Applications (for instance, copy protection schemes) should never
interfere with, or depend on, disk speed control. The double-sided drive controls its
own motor speed, ignoring the speed signal (PWM) from the Analog Signal
Generator (ASG).
THE REAL-TIME CLOCK
The Macintosh Plus real-time clock is a new custom chip. The commands described in
chapter 2 of Volume ill for accessing the Macintosh 512K clock chip are also used to
access the new chip. The new chip includes additional parameter RAM that's reserved by
Apple. The parameter RAM information provided in chapter 13 of Volume II, as well as
the descriptions of the routines used for accessing that information, apply for the new clock
chip as well.
THE SCSI INTERFACE
The NCR 5380 Small Computer Stan.dard Interface (SCSI) chip controls a highspeed parallel port for communicating with up to seven SCSI peripherals (such as hard
disks, streaming tapes, and high speed printers). The Macintosh Plus SCSI port can be
used to implement all of the protocols, arbitration, interconnections, etc. of the SCSI
interface as defined by the ANSI X3T9.2 committee.
The Macintosh Plus SCSI port differs from the ANSI X3T9.2 standard in two ways.
First, it uses a DB-25 connector instead of the standard 50-pin ribbon connector. An Apple
adapter cable, however, can be used to convert the DB-25 connector to the standard 50-pin
connector. Second, power for termination resistors is not provided at the SCSI connector
nor is a termination resistor provided in the Macintosh Plus SCSI circuitry.
Warning: Do not connect an RS232 device to the SCSI port. The SCSI interface is
designed to use standard TTL logic levels of 0 and +5 volts; RS232 devices may
impose levels of-25 and +25 volts on some lines, thereby causing damage to the
logic board.
The SCSI Interface IV-251

<!-- source-page: 259 -->
## Page 259

Inside Macintosh
The NCR 5380 interrupt signal is not connected to the processor, but the progress of a
SCSI operation may be determined at any time by examining the contents of various status
registers in the NCR 5380. SCSI data transfers are performed by the MC68000; pseudo-
DMA mode operations can assert the NCR 5380 DMA Acknowledge (DACK) signal by
reading or writing to the appropriate address (see table below). Approximate transfer rates
are 142K bytes per second for nonblind transfers and 312K bytes per second for blind
transfers. (With nonblind transfers, each byte transferred is polled, or checked.)
Figure 4 shows the DB-25 pinout for the SCSI connector at the back of the Macintosh
Plus.
8
7
6
5
4
3
2
• • • • • • •
25 24 23 22 21 20 19 18 17 16 15 14
• • • • • • • • • • • •
1
REQ
14
Ground
2
MSG
15
CID
3
1/0
16
Ground
4
RST
17
ATN
5
ACK
18
Ground
6
BSY
19
SEL
7
Ground
20
DBP
8
DBO
21
DB1
9
Ground
22
DB2
10
DB3
23
DB4
11
DBS
24
Ground
12
DBS
25
(not connected)
13
DB7
Figure 4. Pinout for SCSI Connector
The locations of the NCR 5380 control and data registers are given in the following table as
offsets from the constant scsiWr for write operations, or scsiRd for read operations. These
base addresses are not available in global variables; instead of using absolute addresses,
you should use the routines provided by the SCSI Manager (covered in chapter 31 of this
volume).
IV-252 The SCSI Interface

<!-- source-page: 260 -->
## Page 260

The Macintosh Plus Hardware
Read and write operations must be made in bytes. Read operations must be to even
addresses and write operations must be to odd addresses; otherwise an undefined operation
will result.
The address of each register is computed as follows:
$580drn
where r represents the register number (from 0 through 7),
n determines whether it a read or write operation
(0 for reads, or 1 for writes), and
d determines whether the DACK signal to the NCR 5380 is asserted.
(0 for not asserted, 1 is for asserted)
Here's an example of the address expressed in binary:
0101 1000 0000 OOdO Orn OOOn
Note: Asserting the DACK signal applies only to write operations to the output data
register and read operations from the input data register.
Symbolic
Location
scsiWr+sODR +dackWr
scsiRd+sIDR +dackRd
scsiWr+sODR
scsiWr+sICR
scsiWr+sMR
scsiWr+sTCR
scsiWr+sSER
scsiWr+sDMAtx
scsiWr+sTDMArx
scsiWr+sIDMArx
scsiRd+sCDR
scsiRd+sICR
scsiRd+sMR
scsiRd+sTCR
scsiRd+sCSR
scsiRd+sBSR
scsiRd+sIDR
scsiRd+sRESET
Memory
Location
$580201
$580260
$580001
$580011
$580021
$580031
$580041
$580051
$580061
$580071
$580000
$580010
$580020
$580030
$580040
$580050
$580060
$580070
NCR 5380 Internal Register
Output Data Register with DACK
Current SCSI Data with DACK
Output Data Register
Initiator Command Register
Mode Register
Target Command Register
Select Enable Register
Start DMA Send
Start DMA Target Receive
Start DMA Initiator Receive
Current SCSI Data
Initiator Command Register
Mode Registor
Target Command Register
Current SCSI Bus Status
Bus and Status Register
Input Data Register
Reset Parity/Interrupt
Note: For more information on the registers and control structure of the SCSI,
consult the technical specifications for the NCR 5380 chip.
The SCSI Interface W-253

<!-- source-page: 261 -->
## Page 261

Inside Macintosh
SUMMARY
Constants
; SCSI base addresses
scsiRd
scsiWr
.EQU
.EQU
$580000
$580001
; SCSI offsets for DACK
dackRd
dackWr
.EQU
.EQU
$200
$200
;base address for read operations
;base address for write operations
;for use with sOCR and sIDR
;for use with sOCR and sIDR
; SCSI offsets to NCR 5380 register
sCDR
sOCR
sICR
sMR
sTCR
sCSR
sSER
sBSR
sDMAtx
sIDR
sTDMArx
sRESET
sIDMArx
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
.EQU
.EQU
IV-254 Summary
$00
$00
$10
$20
$30
$40
$40
$50
$50
$60
$60
$70
$70
;Current SCSI Read Data (read)
;Output Data Register (write)
;Initiator Command Register (read/write)
;Mode Register (read/write)
;Target Command Register (read/write)
;Current SCSI Bus Status (read)
;Select Enable Register (write)
;Bus & Status Register (read)
;DMA Transmit Start (write)
;Data input register (read)
;Start Target OMA receive (write)
;Reset Parity/Interrupt (read)
;Start Initiator DMA receive (write)

<!-- source-page: 262 -->
## Page 262

29 THE SYSTEM RESOURCE FILE
This chapter describes the contents of the System file version 3.2 whose creation date is
June 4, 1986.
The System file, also known as the system resource file, contains standard resources that
are shared by all applications, and are used by the Macintosh Toolbox and Operating
System as well. This file can be modified by the user with the Installer and Font/DA
Mover programs.
Warning: You should not add resources to, or delete resources from, the system
resource file directly.
Note: Some of the resources in the system resource file are also contained in the
128K ROM; they're duplicated in the system resource file for compatibility with
machines not equipped with the 128K ROM. Other resources are put in the system
resource file because they are too large to be put in ROM.
The system resource file contains the standard Macintosh packages and the resources they
use (or own):
• the List Manager Package ('PACK' resource 0), and the standard list definition
procedure ('LDEF' resource 0)
• the Disk Initialization Package ('PACK' resource 2), and code (resource type
'FMTR') used in formatting disks
•the Standard File Package ('PACK' resource 3), and resources used to create its alerts
and dialogs (resource types 'ALRT', 'DITL', and 'DLOG')
•the Floating-Point Arithmetic Package ('PACK' resource 4)
• the Transcendental Functions Package ('PACK' resource 5)
• the International Utilities Package ('PACK' resource 6)
•the Binary-Decimal Conversion Package ('PACK' resource 7)
Certain device drivers (including desk accessories) and the resources they use (or own) are
also found in the system resource file; these resources include:
• the .PRINT driver ('DRVR' resource 2) that communicates between the Printing
Manager and the printer
• the .MPP and .ATP drivers ('DRVR' resources 9 and 10 respectively) used by
Apple Talk
•the Control Panel desk accessory ('DRVR' resource 15) and the bit maps (resource
type 'bmap') and windows (resource type 'WIND') used in displaying its various
options
The System Resource File W-255

<!-- source-page: 263 -->
## Page 263

Inside Macintosh
•the Chooser desk accessory ('DRVR' resource 16), and the dialogs, icons, list
definition procedures, and strings (resource types 'DITL', 'DLOG', 'ICON', and
'LDEF') that it uses (or owns)
Other general resources contained in the system resource file include:
• standard definition procedures for creating windows, menus, controls, lists, and so on
• system fonts and font families (resource types 'FONT' and 'FOND')
• system icons
• code for patching bugs in ROM routines (resource type 'PTCH')
• initialization resources (described below) used during system startup
INITIALIZATION RESOURCES
The system resource file contains initialization resources (resource type 'INIT') used
during system startup. A mechanism has been provided so that applications can supply
code to be executed during system startup without adding resources of type 'INIT' to the
system resource file. Instead of putting your code in the system resource file, you should
create a separate file with a file type of 'INIT' (or for Chooser devices, file type 'RDEV').
A special initialization resource in the system resource file, 'INIT' resource 31, searches
the System Folder of the system startup volume for files of type 'INIT' or 'RDEV'. When
it finds one, it opens the file (with ResLoad set to FALSE) and uses GetIndResource (with
ResLoad set to TRUE) to find all resources in that file of type 'INIT'. It calls each
resource it finds. After calling the last resource, it closes the file, and continues searching
for other files of type 'INIT' or 'RDEV'.
Warning: If you do not want your 'INIT' resources to be released, be sure to call
the Resource Manager procedure DetachResource.
Note: The order in which your 'INIT' resources are called depends on the order in
which your 'INIT' and 'RDEV' files are opened, and on the order of the 'INIT'
resources within these files; these orders are not predictable.
Assembly-language note: The 'INIT' resource 31 saves all registers and places
the handle to your 'INIT' resource in register AO.
The System Startup Environment
This section discusses the organization of the Macintosh Plus RAM at the time your 'INIT'
files are loaded (see Figure 1); most the information presented here is useful only to
assembly-language programmers.
W-256 Initialization Resowces

<!-- source-page: 264 -->
## Page 264

high memory
static al location
room for
static al location
system startup b I ocks
system startup stack (SK)
~-----------------
application heap
system heap
system g I oba Is
low memory
The System Resource File
f- (MemTop)
f- (BufPtr)
f- (MemTop)/2 + 1 K
f- (MemTop)/2
f- ( Appllimit)
f- (HeapE nd)
f- (ApplZone)
f- (Sys Zone)
Figure 1. Macintosh Plus RAM at System Startup
The global variables, shown in parentheses, contain the addresses of the indicated areas.
The application heap limit (stored in the global variable ApplLimit) is set to 8K below the
beginning of the boot stack to protect the stack.
Static allocation off the address contained in the global variable BufPtr is useful when a
large amount of space is needed which will never be deallocated (once space is allocated, it
may not be deallocated unless no one has allocated space below). An 'INIT' resource may
obtain permanent space by moving BufPtr down, but no further than the location of the
boot blocks (MemTop/2 + lK). (If it's necessary to allocate space below MemTop/2 +
lK, contact Developer Technical Support for details.) It may also use the application zone
for temporary heap memory.
Warning: An 'INIT' resource that wants to grow the system heap should be aware
that its associated resource map is open in the application heap at the time.
To avoid their being deallocated when the application heap is initialized, vertical retrace
tasks, AppleTalk listeners, and RAM-based drivers (and their storage) should be placed in
the system heap or in statically allocated space.
Initialization Resources W-257

<!-- source-page: 265 -->
## Page 265

30
THE LIST MANAGER PACKAGE
261
About This Chapter
261
About the List Manager Package
261
Appearance of Lists
262
Drawing Lists
262
List Records
263
The List Record Data Structure
266
The LClikLoop Field
266
Cell Selection Algorithm
268
Using the List Manager Package
269
List Manager Package Routines
270
Creating and Disposing of Lists
271
Adding and Deleting Rows and Columns
4,72
Operations on Cells
273
Mouse Location
27 4
Accessing Cells
27 5
List Display
276
Defining Your Own Lists
27 6
the List Definition Procedure
277
The Initialize Routine
277
The Draw Routine
277
The Highlight Routine
277
The Close Routine
278
Summary of the List Manager Package
Contents W-259

<!-- source-page: 266 -->
## Page 266

Inside Macintosh
IV-260

<!-- source-page: 267 -->
## Page 267

The List Manager Package
ABOUT THIS CHAPTER
This chapter describes the List Manager Package, which lets you create, display, and
manipulate lists.
You should already be familiar with:
• resources, as discussed in the Resource Manager chapter
•the basic concepts and structures behind Quick:Draw, particularly points, rectangles,
and grafPorts
• the Toolbox Event Manager and the Window Manager
• packages in general, as described in the Package Manager chapter
Warning: Early versions of the system resource file may not contain the List
Manager Package.
ABOUT THE LIST MANAGER PACKAGE
The List Manager Package is a tool for storing and updating elements of data within a list
and for displaying the list in a rectangle within a window. It handles all hit-testing,
selection, and scrolling of list elements within that list. In its simplest form, the List
Manager Package can be used to display a "text-only" list of names; with some additional
effort, it can be used to display an array of images and text.
A list element is simply a group of consecutive bytes of data, so it can be used to store
anything-a name, the bits of an icon, or the resource ID of an icon. There's no specific
restriction on the size of a list element, but the total size of a list cannot exceed 32K bytes.
Appearance of Lists
A list is drawn in a window. When you create a list, you need to supply a pointer to the
window to be used; the grafPort of this window becomes the port in which drawing is
done.
You must also supply a rectangle in which to display the list. You specify whether the list
should use scroll bars and a size box. If you request scroll bars, they're drawn outside the
rectangle (but within the window). If you request a size box, the List Manager leaves room
for one but does not draw it; to draw the size box, see the Window Manager procedure
DrawGrow Icon. The rectangle can take up the entire area of the content region (except for
the space needed by scroll bars, if any), or it can occupy only a small portion of the content
region.
About the List Manager Package IV-261

<!-- source-page: 268 -->
## Page 268

Inside Macintosh
List elements are displayed in cells; an element can be seen as the contents of a cell. Cells
provide the basic structure of a list, and may or may not contain list elements. While list
elements (the actual data) may vary in length, the cells in which they're displayed must be
the same size for any given list. You can specify the horizontal and vertical size of a cell
when you create a list; if either dimension is unspecified, the List Manager calculates a
default dimension.
The dimensions of a list are always specified as a number of rows and columns of cells.
When you create a list, you can specify the number of cells it is to contain initially; if you
don't, it's created with no cells. To add cells to an empty list, you call routines that add
entire rows or columns of cells at a time. For instance, to add a single column of 15 cells
to an empty list, you would first call a routine to add one column, followed by a routine
adding 15 rows.
All cells are initially empty. Once you've added the rows and columns of a list, you can set
the values of the cells. At some later point, you can also add empty rows and columns to a
list that already contains data
Drawing Lists
The List Manager provides a drawing mode that you can set either on or off. When the
drawing mode is on, all routines that affect the contents of cells, the number of rows or
columns, the size of the window, or which cells are visible within the rectangle will cause
drawing to happen.
In certain cases, such as the insertion or setting of many cells (typically when the list is
created), drawing is either unsightly or slow. In these cases, you'll want to set the drawing
mode to off; when the action is completed, you can set the drawing mode back to on.
The appearance and behavior of a list is determined by a routine called its list definition
procedure, which is stored as a resource in a resource file. The List Manager calls the
definition procedure to perform any additional list initialization (such as the allocation of
storage space for the application), to draw a cell, to invert the highlight state of a cell, and
to dispose of any data it may have allocated.
The system resource file includes a list definition procedure for a standard text-only list. If
you'd like another type of list, you '11 have to write a list definition procedure, as described
later in the section "Defining Your Own Lists".
LIST RECORDS
The List Manager maintains all the information it requires for its operations on a particular
list in a list record. A list record includes:
• A pointer to the ~a:tPort used by the list; it's set to the port of the window specified
when the list is created.
•The rectangle, given in the window's local coordinates, in which the list is to be
displayed.
W-262 List Records

<!-- source-page: 269 -->
## Page 269

The List Manager Packnge
• A rectangle that specifies, by row and column, the dimensions of the list.
• A rectangle that determines, by row and column, which cells are currently visible.
• A handle to the list definition procedure, which actually performs the drawing of the
cells.
• The size of a cell.
• A field containing flags that control the selection process.
The list record also contains a handle to the cell data. The data is stored as a contiguous
block of data in list order (cells O .. n of row 0, cells O .. n of row 1, and so on). The cell
data is locked down only while it's being searched.
The last field of the list record is an array of integers containing the offset of each cell's data
within the contiguous block of cell data. The high-order bit of an array element is set if the
corresponding cell is selected; the remaining 15 bits contain the offset. This provides the
maximum total data size of 32K, and an overhead of one word per cell.
Warning: Since a variety of routines are provided for accessing cell data, you should
never need to directly access the array of offsets or the data itself.
The List Record Data Structure
The exact data structure of a list record is as follows:
TYPE Cell = Point;
DataArray
DataPtr
DataHandle
PACKED ARRAY [0 .. 32000] OF CHAR;
"DataArray;
"DataPtr;
ListRec =
RECORD
rView:
port:
indent:
cellSize:
visible:
vScroll:
hScroll:
selFlags:
lActive:
lReserved:
listFlags:
clikTime:
clikLoc:
mouseLoc:
lClikLoop:
lastClick:
refCon:
listDefProc:
Rect;
{list's display rectangle}
GrafPtr;
{list's grafPort}
Point;
{indent distance}
Point;
{cell size}
Rect;
{boundary of visible cells}
ControlHandle;
{vertical scroll bar}
ControlHandle;
{horizontal scroll bar}
SignedByte;
{selection flags}
BOOLEAN;
{TRUE if active}
SignedByte;
{reserved}
SignedByte;
{automatic scrolling flags}
LONGINT;
{time of last click}
Point;
{position of last click}
Point;
{current mouse location}
·Ptr;
{routine for LClick}
Cell;
{last cell clicked}
LONGINT;
{list's reference value}
Handle;
{list definition procedure}
List Records IV-263

<!-- source-page: 270 -->
## Page 270

Inside Macintosh
userHandle:
dataBounds:
cells:
maxindex:
cellArray:
END;
Handle;
Rect;
DataHandle;
INTEGER;
ARRAY [1.. l]
ListPtr
= AListRec;
ListHandle = AListPtr;
{additional storage}
{boundary of cells allocated}
{cell data}
{used internally}
OF INTEGER
{offsets to data}
RView is the rectangle, given in the local coordinates of the grafPort, in which the list is
displayed. Room for scroll bars is not included in this rectangle. If the list has scroll bars
and is to fill the entire window, rView should be 15 points smaller in each dimension than
the grafPort.
Port is the grafPort used by the list; it's set to the port of the window specified when the list
is created. Indent is the distance in pixels that the list definition procedure should indent
from the topLeft of the cell when drawing the contents. The default value for indent is 0,
but it can be set by the list definition procedure.
CellSize is the size of a cell in pixels. If it's not specified when the list is created, a default
cell size is set. CellSize.v is set to the ascent plus descent plus leading of the port's font,
and cellSize.h is set to
(rView.right - rView.left) DIV (dataBounds.right - dataBounds.left)
A cell is a box in which a list element is displayed. Cells are identified by their column and
row numbers. In Figure l, for instance, the highlighted cell is in column 1, row 2.
Cells are declared as points, using the Point data type simply as a way of specifying the
column and row number of a cell. Similarly, visible and dataBounds use the Rect data type
to specify a rectangular set of cells as two diagonally opposite cell coordinates (rather than
two diagonally opposite points in the local coordinates of a grafPort).
DataBounds is the boundary of the cells currently allocated, specified by row and column.
The list in Figure 1 (assuming the entire list is visible) has seventeen rows and five
columns of cells. DataBounds for this list can be represented, using the QuickDraw
rectangle notation (left,top)(right,bottom), as (0,0)(5,17). Notice that the column and row
specified for the bottom right of dataBounds are 1 greater in each dimension than the
column and row number of the bottom right cell. Thus, you can test to see if a cell is a
valid cell within the boundary of a list using the statement:
IF PtinRect(c,myListAA.dataBounds) THEN ...
The visible rectangle reflects which cells are currently within the visible part of the list; it's
calculated by the List Manager according to the values you specify for rView, dataBounds,
and cellSize when you create the list. (Visible.topLeft is the row and column of the top left
visible cell; visible.botRight is 1 greater in both dimensions than the row and column of the
bottom right visible cell.) For example, if only four cells-row 2, column 0; row 2,
column 1; row 3, column 0; and row 3, column 1-are visible, the visible rectangle is
(0,2)(2,4). You can test to see if a cell is visible using the statement:
IF PtinRect(c,myListAA.visible) THEN ...
IV-264 List Records

<!-- source-page: 271 -->
## Page 271

D
Cell 0,0
Cell 0,1
Cell 0,2
Cell 0,3
Cell 0,4
Cell 0,5
Cell 0,6
Cell 0,7
Cell 0,8
Cell 0,9
Cell 0,10
Cell0,11
Cell0,12
Cell0,13
Cell 0, 14
Cell 0,15
Cell0,16
Cell 1,0
Cell 1,1
Cell 1 .. ~
Cell 1,3
Cell 1,4
Cell 1,5
Cell 1,6
Cell 1,7
Cell 1,8
Cell 1,9
Cell 1,10
Cell 1, 11
Cell 1,12
Cell 1,13
Cell 1,14
Cell 1,15
Cell 1,16
A Sample
Cell 2,0
Cell 2,1
Cell 2,2
"
Cell 2,3
Cell 2,4
Cell 2,5
Cell 2,6
Cell 2,7
Cell 2,8
Cell 2,9
Cell 2, 10
Cell 2, 11
Cell 2, 12
Cell2,13
Cell 2,14
Cell 2,15
Cell 2, 16
Cell 3,0
Cell 3,1
Cell 3,2
Cell 3 ,3
Cell 3,4
Cell 3,5
Cell 3,6
Cell 3,7
Cell 3,8
Cell 3,9
Cell 3, 10
Cell 3, 11
Cell3,12
Cell 3, 13
Cell3,14
Cell3,15
Cell3,16
Figure 1. A Sample List
The List Manager Package
Cell 4,0
Cell 4, 1
Cell 4,2
Cell 4,3
Cell 4,4
Cell 4,5
Cell 4,6
Cell 4, 7
Cell 4,8
Cell 4,9
Cell 4,10
Cell 4, 11
Cell 4,12
Cell 4, 13
Cell4,14
Cell4,15
Cell 4,16
SelFlags contains selection flags for the List Manager. It's initialized to O; with this setting,
the List Manager selects cells according to the Macintosh User Interface Guidelines. The
meaning of these flags is explained below in the section "Cell Selection Algorithm". The
listFlags field contains automatic scrolling flags; the List Manager sets these flags
automatically when you specify scroll bars. There are predefined constants that let you set
or test the status of the corresponding bits:
CONST lDoVAutoscroll = 2; {set to allow automatic vertical scrolling}
lDoHAutoscroll = l; {set to allow automatic horizontal }
{ scrolling}
ClikLoc is the position of the last mouse click in local coordinates; you can use it in the list
definition procedure to get the position within the cell. LClikLoop is a pointer to the
routine to be called during the LClick function, as described later. LastClick contains the
cell coordinates of the last cell clicked in.
RefCon is the list's reference value field, which the application may store into and access
for any purpose. In addition, the application may use the field userHandle to store a handle
to an additional storage area.
CellArray contains offsets to the cell data. For each list element, this includes the bit
indicating whether the cell is selected or not.
List Records IV-265

<!-- source-page: 272 -->
## Page 272

In.side Macintosh
The LClikloop Field
The lClikLoop field of a list record lets you specify a routine that will be called repeatedly
(by the LClick function, described below) as long as the mouse button is held down within
the rView rectangle or its scroll bars.
Note: The LClick function performs automatic scrolling if the mouse is dragged outside
the visible rectangle, so there's no need to write a list click loop routine to do automatic
scrolling.
The list click loop routine has no parameters and returns a Boolean value. You could
declare a list click loop routine named MyClikLoop like this:
FUNCT!ON MyClikLoop : BOOLEAN;
The function should return TRUE. You must put a pointer to your list click loop routine in
the lClikLoop field of the list record so that the List Manager will call your routine.
Warning: Returning FALSE from your list click loop routine tells the LClick function
that the mouse button has been released, which aborts LClick.
Assembly-language note: Your routine should set register DO to 1; returning 0
in register DO aborts LClick. For your convenience, register D5 contains the current
mouse location.
CELL SELECTION ALGORITHM
The default algorithm used by the List Manager for user selection of cells follows the
techniques described in the Macintosh User Interface Guidelines, as summarized below.
1. If neither the Shift nor the Command key is held down, a click causes all current
selections to be deselected, and the cell receiving the click to be selected. While the
mouse button is held down and the mouse moved around, only the cell under the
cursor is selected.
2. If the Shift key is held down, then as long as the mouse button is down, the List
Manager expands and shrinks a selected rectangle that's defined by the mouse
location and the "anchor". When the mouse is first pressed, the List Manager
calculates the smallest rectangle that encloses all selected cells. If the click is above or
to the left of this rectangle (or on the top left corner), the bottom right corner of the
rectangle becomes the anchor; otherwise the top left corner becomes the anchor. (If
no cells are selected, the clicked cell is used as the anchor.)
IV-266 Cell Selection Algorithm

<!-- source-page: 273 -->
## Page 273

The List Manager Package
3. If the Command key is held down, then while the mouse button is down, all cells that
the mouse passes over are either selected or deselected. Like FatBits in MacPaint, if
the initial cell was off, cells are turned on; otherwise they're turned off.
The selFlags byte, initialized to 0 by the List Manager, contains flags that let you change
the way selections work. Each flag is specified by a bit, as illustrated in Figure 2.
7
6
5
4
3
2
1
0
"'
1 to not high I ight empty eel Is
~--1 for Shift to use sense of first cell
-----1 to not grow selections as rectangles
--- 1 to not extend Shift se I ect ions
1 to turn off multiple selections with click
1 for dregg i ng without Shi ft key
1 if only one selection at a time
"' reserved for use by the Li st Manager
Figure 2. Selection flags
The List Manager provides a predefined constant for each flag, in which the bit
corresponding to that flag is set.
CONST lOnlyOne
lExtendDrag
lNoDisjoint
lNoExtend
lNoRect
-128;
64;
32;
16;
8;
lUseSense
4;
lNoNilHilite = 2;
{set if only one selection at a time}
{set for dragging without Shift key}
{set to turn off multiple selections with
{ click}
{set to not extend Shift selections}
{set to not expand selections as }
{ rectangles}
{set for Shift to use sense of first cell}
{set to not highlight empty cells}
Setting one or more of bits 5-7 modifies the selection algorithm in the following ways:
• If you set the lOnlyOne bit, only one cell can be selected at a time.
• If you set the lNoDisjoint bit, multiple cells can be selected, but everything is
deselected when the mouse button is pressed (even if the Shift or Command keys are
held down).
• If you set the lExtendDrag bit, clicking and dragging selects all cells in its path. (It
works best if you also set lNoDisjoint, lNoRect; lUseSense, and lNoExtend.)
Cell Selection Algorithm IV-267

<!-- source-page: 274 -->
## Page 274

Inside Macintosh
Bits 2-4 affect Shift selection. If all three are set, Shift selection works exactly like
Command selection.
• If you set the lNoRect bit, Shift selections are not dragged out as rectangles, but
instead select everything they pass over. They use the anchor point, but do not shrink
selections when you back over them.
• If you set the lNoExtend bit, the click is used as the anchor point for Shift selections,
and current selections are ignored.
• If you set the lU seSense bit, the cell that's clicked determines whether cells are turned
off or on.
Bit 1, the lNoNilHilite bit, determines whether or not empty cells can be selected. If you
set this bit, cells not containing data cannot be selected (that is, the list definition procedure
isn't called to highlight empty cells).
Note: For the convenience of your application's user, remember to conform to the
Macintosh User Interface Guidelines for selection.
USING THE LIST MANAGER PACKAGE
The List Manager Package is automatically read into memory from the system resource file
when one of its routines is called; it occupies a total of about 5K bytes.
Before using the List Manager, you must initialize QuickDraw, the Font Manager, the
Window Manager, the Menu Manager, and TextEdit, in that order.
Before creating a list, you must create a window in which the drawing will take place. To
create a new list, call the LNew function. When you're done using a list, you should
dispose of its data with LDispose. Before you dispose of the list, make sure you dispose
of any data that you may have stored in the userHandle or refCon fields of the list record.
To change the size of a list's cells, call LCellSize.
The procedure LDoDraw controls whether operations performed on cells by List Manager
routines cause drawing on the screen.
To add rows or columns to the list, call LAddRow and LAddColumn. To delete rows or
columns, call LDelRow and LDelColumn. These routines do all necessary updating of the
screen if you've set drawing on with LDoDraw.
To assign a value to a cell, call the procedure LSetCell. To append data to a cell, you can
call LAddToCell; to clear the contents of a cell, call LClrCell. To get a cell's data, call
LGetCell. The new value of a cell is displayed if you've set drawing on.
Warning: If you add or delete rows or columns, change the data in a cell, or call a
routine that may move or purge memory, pointers (to a cell's data) obtained by earlier
calls to the List Manager may no longer be valid.
IV-268 Using the List Manager Packa.ge

<!-- source-page: 275 -->
## Page 275

The List Manager Package
To select or deselect a cell, call LSetSelect. To determine whether or not a cell is selected,
call LGetSelect. LGetSelect can also be used to find the next selected cell in the list.
The Window Manager NewWindow or GetNewWindow call generates an update event for
the entire window. Call LUpdate in response to the update event, and all visible cells in the
update region will be drawn (or redrawn). When you change the value or selection of a cell
from your program, it's redisplayed only if drawing is on. If drawing is off, you can call
the procedure LDraw to display the contents of the cell.
If a mouse-down event occurs within the list's window, call LClick. This routine tracks
the mouse, selecting cells and scrolling the display as necessary. The result of LClick is a
Boolean value that is TRUE if a double-click occurred. You can discover which cell
received the double-click by calling LLastClick.
If an activate or deactivate event occurs for the window containing the list, you should call
the procedure LActivate. This routine highlights the selected cells and scroll bars as
necessary.
If the window containing the list has a size box (and you want the list to grow along with
the window), call the Window Manager routines GrowWindow and Size Window as usual,
then call LSize with the new size of the list. The list is automatically expanded to fill the
new area and the scroll bars are updated accordingly. The drawing mode does not affect
the updating of scroll bars in LSize.
You can find a cell with specified contents by calling LSearch. The default search routine
is the International Utilities Package function IUMagIDString, but you can pass LSearch
another search routine if you wish. Given a cell, you can call LNextCell to find the next
cell in the list.
You can find the local coordinates of a given cell by calling LRect. To scroll the list, call
LScroll. You can call LAutoScroll to make sure that the first selected cell is visible. It
automatically places the first selected cell in the top left comer of the visible rectangle.
All the data in a list is stored as a single block. You can find the off set of a particular cell's
data using LFind.
LIST MANAGER PACKAGE ROUTINES
Assembly-language note: You can invoke each of the List Manager routines
with a macro that has the same name as the routine preceded by an underscore.
These macros expand to invoke to trap macro _Pack 0. The package determines
which routine to execute from a routine selector, an integer that's passed to it in a
word on the stack. The routine selectors are as follows:
!Activate
.EQU
lAddColumn .EQU
lAddRow
. EQU
lAddToCell . EQU
0
4
8
12
lAutoScroll .EQU
16
lCellSize
.EQU
20
!Click
. EQU
2 4
lClrCell
.EQU
28
List Manager Package Routines W-269

<!-- source-page: 276 -->
## Page 276

Inside Macintosh
lDelColumn .EQU
32
lNew
.EQU
68
lDelRow
.EQU
36
lNextCell
.EQU
72
lDispose
.EQU
40
lRect
.EQU
76
lDoDraw
.EQU
44
lScroll
.EQU
80
lDraw
.EQU
48
lSearch
.EQU
84
lFind
.EQU
52
lSetCell
.EQU
88
lGetCell
.EQU
56
lSetSelect .EQU
92
lGetSelect .EQU
60
lSize
.EQU
96
lLastClick .EQU
64
lUpdate
.EQU
100
Creating and Disposing of Lists
FUNCTION LNew (rView,dataBounds: Rect; cSize: Point; theProc:
INTEGER; theWindow: WindowPtr; drawit,hasGrow,
scrollHoriz,scrollVert: BOOLEAN)
: ListHandle;
Call LNew to create a new list. It returns a handle to the new list. The list's grafPort is set
to the Window's port. If drawlt is FALSE, the list is not displayed.
RView specifies, in the local coordinates of the Window, the rectangle in which the list will
be displayed. (Remember that this doesn't include space for scroll bars. If the list,
including scroll bars, is to fill the entire window, rView should be 15 points smaller in each
dimension than the Window's portRect.)
DataBounds is the rectangle for specifying the initial array dimensions of the list. For
example to preallocate space for a list that's 5 cells across by 10 cells down, you should set
dataBounds to (0,0)(5,10). If you want to allocate the space for a one-column list, set
dataBounds to (0,0)(1,0) and use LAddRow.
CSize.h and cSize.v are the desired height and width of each cell in pixels; if they're not
specified, a default cell size is calculated (as described above).
TheProc is the resource ID of your list definition procedure; for a text-only list, pass 0 and
the default list definition procedure (about 150 bytes in size) will be used. The list
definition procedure is called to initialize itself after all other list record fields have been
initialized; thus, it can use any of the values in the list record (or set particular fields, such
as the indent distance).
If hasGrow is TRUE, the scroll bars are sized so that there's room for a size box in the
standard position. It's up to the program to display the size box (using the Window
Manager procedure DrawGrowIcon). If scrollHoriz is TRUE, a horizontal scroll bar is
placed immediately below rView and all horizontal scrolling functions are implemented. If
scroll Vert is TRUE, a vertical scroll bar is placed immediately to the right of rView and all
vertical scrolling functions are implemented.
The visible rectangle is set to contain as many cells of cSize (or the default) as will fit into
rView. If the cells do not fit exactly into rView, the visible rectangle is rounded up to the
nearest cell. Scrolling will always allow all cells to be fully displayed. The selection flags
are set to 0, and the active flag is set to TRUE.
Note: Scrolling looks best if rView is a multiple of cSize.v in height.
IV-270 List Manager Packlzge Routines

<!-- source-page: 277 -->
## Page 277

The List Manager Package
PROCEDURE LDispose (lHandle: ListHandle);
Call LDispose when you are through using a list. It issues a close call to the list definition
procedure, and calls the Memory Manager procedure DisposHandle for the data handle, the
Control Manager procedure DisposeControl for both scroll bars (if they're there), and
DisposHandle for the list record.
Note: Calling LDispose is much faster than deleting one row at a time.
Adding and Deleting Rows and Columns
FUNCTION LAddColumn (count,colNum: INTEGER; lHandle: ListHandle)
INTEGER;
LAddColumn inserts into the given list the number of columns specified by the count
parameter, starting at the column specified by colNum. Column numbers that are greater
than or equal to colNum are increased by count. If colNum is not within dataBounds, new
last columns are added. The number of the first added column is returned and
dataBounds.right is increased by count. All cells added are empty. If there are no cells
(because dataBounds.top = dataBounds.bottom), no cells are added, but dataBounds is still
extended. If drawing is on and the added columns (which are empty) are visible, the list
and its scroll bars are updated.
FUNCTION LAddRow (count,rowNum: INTEGER; lHandle: ListHandle) :
INTEGER;
LAddRow inserts the number of rows specified by the count parameter, starting at the row
specified by rowNum. Row numbers that are greater than or equal to rowNum are
increased by count. If rowNum is not within dataBounds, new last rows are added. The
number of the first added row is returned, and dataBounds.bottom is increased by count.
All cells added are empty. If there are no cells (because dataBounds.left =
dataBounds.right), no cells are added, but dataBounds is still extended. If drawing is on
and the added rows (which are empty) are visible, the list and its scroll bars are updated.
PROCEDURE LDelColumn (count,colNum: INTEGER; lHandle: ListHandle);
LDelColumn deletes the number of columns specified by the count parameter, starting with
the column specified by colNum. Column numbers that are greater than colNuin are
decreased by count. If colNum is not within dataBounds, nothing is done.
DataBounds.right is decreased by count. If drawing is on and the deleted columns were
visible, the list and its scroll bars are updated.
If count is 0, or
colNum = dataBounds.left AND count > = dataBounds.right - dataBounds.left
all the data in the list is quickly deleted, dataBounds.right is set to dataBounds.left, and the
number of rows is left unchanged.
List Manager Package Routines IV-271

<!-- source-page: 278 -->
## Page 278

Inside Macintosh
PROCEDURE LDelRow (count,rowNum: INTEGER; lHandle: ListHandle);
LDelRow deletes the number of rows specified by the count parameter, starting with the
row specified by rowNum. Row numbers that are greater than rowNum are decreased by
count. If rowNum is not within dataBounds, nothing is done. DataBounds.bottom is
decreased by count. If drawing is on and the deleted rows were visible, the list and its
scroll bars are updated.
If count is 0, or
rowNum = dataBounds.top AND count > = dataBounds.bottom - dataBounds.top
all the data in the list is quickly deleted, dataBounds.bottom is set to dataBounds.top, and
the number of columns is left unchanged.
Operations on Cells
PROCEDURE LAddToCell (dataPtr: Ptr; dataLen: INTEGER; theCell:
Cell; lHandle: ListHandle);
LAddToCell appends the data pointed to by dataPtr and of length dataLen to the cell
specified by theCell in !Handle. If drawing is off, you must turn drawing on and call
LDraw (or LUpdate) to display the cell's new value.
PROCEDURE LClrCell (theCell: Cell; lHandle: ListHandle);
LClrCell clears the contents of the specified cell (by setting the length to 0). If theCell is
not a valid cell, nothing is done. If drawing is off, you must turn drawing on and call
LDraw to display the cell's new value (or simply call the Window Manager procedure
InvalRect).
PROCEDURE LGetCell (dataPtr: Ptr; VAR dataLen: INTEGER; theCell:
Cell; lHandle: ListHandle);
Given a cell in theCell, LGetCell copies the cell's data to the location specified by dataPtr;
dataLen is the maximum number of bytes allowed. If the data is longer than dataLen, only
dataLen bytes are copied into the location specified by dataPtr. If the data is shorter than
dataLen, dataLen is set to the true length of the cell's data.
PROCEDURE LSetCell (dataPtr: Ptr; dataLen: INTEGER; theCell: Cell;
lHandle: ListHandle);
LSetCell places the data pointed to by dataPtr and of length dataLen into the specified cell.
It replaces any data that was already in the cell. If dataLen is 0, this is equivalent to
LClrCell. If theCell is not a valid cell, nothing is done. If drawing is off, you must turn
drawing on and call LDraw (or LUpdate) to display the cell's new value.
W-272 List Manager Package Routines

<!-- source-page: 279 -->
## Page 279

The List Manager Package
PROCEDURE LCellSize (cSize: Point; lHandle: ListHandle);
LCellSize sets the cellSize field in the list record to cSize and updates the visible rectangle
to contain cells of this size. This command should be used only before any cells have been
drawn.
FUNCTION LGetSelect (next: BOOLEAN; VAR theCell: Cell; lHandle:
ListHandle) : BOOLEAN;
If next is FALSE, LGetSelect returns TRUE if the specified cell is selected, or FALSE if
not. If next is TRUE, LGetSelect returns in c the cell coordinates of the next selected cell
in the row that is greater than or equal to theCell. If there are no more cells in the row. it
returns in theCell the cell coordinates of the next selected cell in the next row. If there are
no more rows, FALSE is returned.
PROCEDURE LSetSelect (setit: BOOLEAN; theCell: Cell; lHandle:
ListHandle) ;
If setlt is TRUE, LSetSelect selects the cell and redraws if it is visible and was previously
unselected If setlt is FALSE, it deselects the cell and redraws if necessary.
Mouse Location
FUNCTION LClick (pt: Point; modifiers: INTEGER; lHandle: ListHandle)
: BOOLEAN;
Call LClick when there is a mouse-down event in the destination rectangle or its scroll bars.
Pt is the mouse location in local coordinates. Modifiers is the modifiers word from the
event record. LHandle is the list to be tracked. The result is TRUE if a double-click
occurred (and the two clicks took place within the same cell).
LClick keeps control until the mouse is released; each time through its inner loop, it calls
the routine whose pointer is in the lClikLoop field of the list record.
If the mouse is in the visible rectangle, cells are selected according to the state of the
modifiers and the selection flags. If the mouse was in the cells but is dragged outside the
list's rectangle, the list is auto-scrolled. If the mouse was in a control, the control's
definition procedure is called to track the mouse. To discover which cell was clicked in,
use the LtastClick function.
FUNCTION LLastClick (lHandle: ListHandle) : Cell;
LLastClick returns the cell coordinates of the last cell clicked in. If no cell has been clicked
in since LNew, the value returned (for both integers) is negative.
Note: The value returned by this call is not the last cell double-clicked in, or the last cell
selected, but merely the last cell clicked in.
List Manager Package Routines W-273

<!-- source-page: 280 -->
## Page 280

Inside Macintosh
Accessing Cells
PROCEDURE LFind (VAR offset,len: INTEGER; theCell: Cell; lHandle:
ListHandle);
Given a cell in theCell,,LFind returns the offset and the length in bytes of the cell's data. If
an invalid cell is specified, offset and len are set to -1. A similar procedure, LGetCell, is
more convenient to use from Pascal.
FUNCTION LNextCell (hNext,vNext: BOOLEAN; VAR theCell: Cell;
lHandle: ListHandle) : BOOLEAN;
Given a cell in theCell, LNextCell returns in theCell the next cell in the list. If both hNext
and vNext are TRUE, theCell is first advanced to the next cell in the row. If there are no
more cells in the row, theCell is set to the first cell in the next row. If there are no more
rows, FALSE is returned. If only hNext is TRUE, theCell is advanced within the current
row. If only vNext is TRUE, theCell is advanced within the current column. FALSE is
returned if there are no remaining cells in the row or column.
PROCEDURE LRect (VAR cellRect: Rect; theCell: Cell; l~andle:
ListHandle);
LRect returns in cellRect the local (QuickDraw) coordinates of the cell specified by theCell.
If an invalid cell is specified, (0,0)(0,0) is returned in cellRect.
FUNCTION LSearch (dataPtr: Ptr; dataLen: INTEGER; searchProc: Ptr;
VAR theCell: Cell; lHandle! ListHandle) : BOOLEAN;
LSearch searches for the first cell greater than or equal to theCell that contains the specified
data. If a cell containing matching data is found, the function result TRUE is returned, and
the cell coordinates are returned in theCell. If searchProc is NIL, the International Utilities
Package function IUMagIDString is called to compare the specified data with the contents
of each cell. If searchProc is not NIL, the routine pointed to by searchProc is called.
Note: Your searchProc should have the same parameters as the IUMagIDString
function.
PROCEDURE LSize (listWidth,listHeight: INTEGER; lHandle:
ListHandle);
You '11 usually call LSize immediately after the Window Manager procedure Size Window.
It causes the bottom right of the list to be adjusted so that the list is the width and height
indicated by list Width and listHeight. The contents of the list anQ. the scroll bars are
adjusted and redrawn as necessary. The values of list Width and listHeigp.t do not include
the scroll bars; for a list that entirely fills the window, listWidth and listHeight should be 15
fewer pixels than the portRect if both scroll bars are present.
W-274 List Manager Packtige Routines

<!-- source-page: 281 -->
## Page 281

The List Manager Package
List Display
PROCEDURE LDraw (theCell: Cell; lHandle: ListHandle);
Call LDraw after updating a cell's data or selection status. (You can achieve the same result
by invalidating the cell's rectangle and calling LUpdate in response to the update event.)
The List Manager makes its grafPort the current port, sets the clipping region to the cell's
rectangle, and calls the list definition procedure to draw the cell. It restores the clipping
region and port before exiting.
PROCEDURE LDoDraw (drawit: BOOLEAN; lHandle: ListHandle);
LDoDraw sets the List Manager's drawing mode to the state specified by drawlt. If draw It
is TRUE, changes made by most List Manager calls will cause some sort of drawing to
take place. If draw It is FALSE, all cell drawing is disabled. (Two exceptions: The scroll
bars are still updated after LSize, and the scroll arrows are still highlighted if the user clicks
them.)
The recommended use ofLDoDraw is to disable drawing while you're building a list (that
is, adding rows or columns, setting or changing cell values, or setting default selections).
Once you've finished building the list, you should then re-enable drawing. In general,
drawing should be on while you 're in your event loop and dispatching events to the List
Manager.
PROCEDURE LScroll (dCols,dRows: INTEGER; lHandle: ListHandle);
LScroll scrolls the given list by the number of columns and rows specified in dCols and
dRows, either positively (down and to the right) or negatively (up and to the left).
Scrolling is pinned to the list's dataBounds. If drawing is on, LScroll does all necessary
updating of the screen.
PROCEDURE LAutoScroll (lHandle: ListHandle);
Fof the given list, LAutoScroll scrolls the list until the first selected cell is visible. It
automatic3.lly places the first selected cell in the top left corner of the visible rectangle.
PROCEDURE LUpdate (theRgn: RgnHandle; lHandle: ListHandle);
LUpdate should be called in response to an update event. TheRgn should be set to the
visRgn of the list's port (for more details, see the Begin Update procedure in the Window
Manager chapter). It redraws any visible cells in !Handle that intersect theRgn. It also
redraws the controls, if necessary.
List Manager Package Routines W-275

<!-- source-page: 282 -->
## Page 282

Inside Macintosh
PROCEDURE LActivate (act: BOOLEAN; lHandle: ListHandle};
Call LActivate to activate or deactivate the list specified by lHandle (in response to an
activate event in the window containing the list). The act parameter should be set to TRUE
to activate the list, or FALSE to deactivate the list. LActivate highlights or unhighlights the
selections, and shows or hides the scroll bars (but not the size box, if any).
DEFINING YOUR OWN LISTS
The List Manager calls a list definition procedure to perform any additional list initialization
(such as the allocation of storage space for the application), to draw a cell, to invert the
highlight state of a cell, and to dispose of any data it may have allocated. The system
resource file includes a default list definition procedure for a standard text-only list; you
may, however, wish to define your own type of list with special features.
To define your own type of list, you write a list definition procedure and store it in a
resource file as a resource of type 'LDEF'. The standard list definition procedure has a
resource ID of 0; your definition procedure should have a different ID.
When you create a list, you provide the resource ID of the list definition procedure to be
used. The List Manager calls the Resource Manager to access the list definition procedure
with the given resource ID. The Resource Manager reads the list definition procedure into
memory and returns a handle to it. The List Manager then stores this handle in the
listDefProc field of the list record.
The List Definition Procedure
The list definition procedure is usually written in assembly language, but may be written in
Pascal.
Assembly-language note: The procedure's entry point must be at the beginning.
You may choose any name you wish for your list definition procedure. Here's how you
would declare one named MyList:
PROCEDURE MyList (lMessage: INTEGER; lSelect: BOOLEAN; lRect: Rect;
lCell: Cell; lDataOffset,lDataLen: INTEGER; lHandle:
ListHandle);
The !Message parameter identifies the operation to be performed. It has one of the
following values:
CONST linitMsg
lDrawMsg
lHiliteMsg
lCloseMsg
O;
{do any additional list initialization}
1;
{draw the cell }
2;
{invert cell's highlight state}
3;
{take any additional disposal action}
W-276 Defining Your Own Lists

<!-- source-page: 283 -->
## Page 283

The List Manager Package
LSelect is used for both the drawing and highlighting operations; it's TRUE if the cell
should be selected.
LRect indicates the rectangle in which a cell should be drawn. LDataOffset is the offset
into the cell data of the cell to be drawn or highlighted; lDataLen is the length in bytes of
that cell's data. LHandle is the handle to the list record.
The routines that perform these operations are described below.
Note: "Routine" here doesn't necessarily mean a procedure or function. While it's
a good idea to set these up as subfunctions within the list definition procedure,
you 're not required to do so.
The Initialize Routine
The list definition procedure is called by the LNew function with an initMsg message after
all list initialization has been completed. Since all default settings have been stored in the
list record, this routine is a good place to change any of these settings. This routine can
also be used to allocate any private storage needed by the list definition procedure.
The Draw Routine
The list defmition procedure receives a lDrawMsg message when a cell needs to be drawn.
The !Select parameter is TRUE if the given cell should be selected.
LRect is the rectangle in which the cell should be drawn. The draw routine sets the
clipping region of the list's window to this rectangle.
LDataOffset is the offset into the cell data of the cell to be drawn; lDataLen is the length of
that cell's data in bytes.
The Highlight Routine
The definition procedure receives a lHiliteMsg message when a cell's data is visible and its
highlight state needs to be inverted (from selected to deselected or vice versa). This routine
is provided for the extra speed usually gained by using an invert operation instead of a
combination of the draw and highlight operations.
The parameters for this routine are identical to those for the lDrawMsg routine. If you want
(for instance, if highlighting is more complicated than mere inversion), you can simply call
your lDrawMsg routine when you get a lHiliteMsg message.
The Close Routine
The definition procedure receives a lCloseMsg message in response to a LDispose call. If
any private storage was allocated by the definition procedure, this routine should dispose
of it.
Defining Your Own Lists IV-277

<!-- source-page: 284 -->
## Page 284

Inside Macintosh
SUMMARY OF THE LIST MANAGER PACKAGE
Constants
CONST { Masks for automatic scrolling }
lDoVAutoscroll
lDoHAutoscroll
2
{set to allow automatic vertical scrolling}
1
{set to allow automatic horizontal scrolling)
{ Masks for selection flags
lOnlyOne
lExtendDrag
lNoDisjoint
lNoExtend
!No Re ct
-128;
64;
32;
16;
8;
{set if only one selection at a time}
{set for dragging without Shift key}
{set to turn off multiple selections with
{ click}
{set to not extend Shift selections}
lUseSense
4;
lNoNilHilite = 2;
{set to not grow selections as rectangles}
{set for Shift to use sense of first cell}
{set to not highlight empty cells}
{ Messages to list definition procedure }
linitMsg
0;
lDrawMsg
1;
lHili teMsg = 2;
lCloseMsg = 3;
Data Types
TYPE Cell = Point;
{initialize list, set defaults, allocate space}
{draw the indicated cell data}
{invert (select/deselect) the state of a cell}
{dispose of list and any associated data}
DataArray
DataPtr
DataHandle
PACKED ARRAY (0 .. 32000] OF CHAR;
"DataArray;
"DataPtr;
ListRec =
RECORD
rView:
port:
indent:
cellSize:
visible:
vScroll:
hScroll:
selFlags:
!Active:
!Reserved:
listFlags:
clikTime:
clikLoc:
mouseLoc:
lClikLoop:
Rect;
{list's display rectangle}
GrafPtr;
{list's grafPort}
Point;
{indent distance}
Point;
{cell size}
Rect;
{boundary of visible cells}
ControlHandle; {vertical scroll bar}
ControlHandle;
{horizontal scroll bar}
SignedByte;
{selection flags}
BOOLEAN;
{TRUE if active}
SignedByte;
{reserved)
SignedByte;
{automatic scrolling flags)
LONGINT;
{time of last click}
Point;
{position of last click}
Point;
{current mouse location}
Ptr;
{routine for LClick}
W-278 Summary of the List Manager Package

<!-- source-page: 285 -->
## Page 285

lastClick:
refCon:
listDefProc:
userHandle:
dataBounds:
cells:
maxindex:
cellArray:
END;
Cell;
LONGINT;
Handle;
Handle;
Rect;
DataHandle;
INTEGER;
ARRAY [l. .1]
The List Manager Package
{last cell clicked}
{list's reference value}
{list definition procedure}
{additional storage}
{boundary of cells allocated}
{cell data}
{used internally}
OF INTEGER
{offsets to data}
ListPtr
ListHandle
"ListRec;
"ListPtr;
Routines
Creating and Disposing of Lists
FUNCTION
LNew
(rView,dataBounds: Rect; cSize: Point; theProc:
INTEGER; theWindow: WindowPtr; drawit,
hasGrow,scrollHoriz,scrollVert: BOOLEAN)
:
ListHandle;
PROCEDURE LDispose
(lHandle: ListHandle);
Adding and Deleting Rows and Columns
FUNCTION
LAddColumn
FUNCTION
LAddRow
PROCEDURE LDelColumn
PROCEDURE LDelRow
Operations on Cells
PROCEDURE LAddToCell
PROCEDURE LClrCell
PROCEDURE LGetCell
PROCEDURE LSetCell
PROCEDURE LCellSize
FUNCTION
LGetSelect
PROCEDURE LSetSelect
Mouse Location
(count,colNum: INTEGER; lHandle: ListHandle)
INTEGER;
(count,rowNum: INTEGER; lHandle: ListHandle)
INTEGER;
(count,colNum: INTEGER; lHandle: ListHandle);
(count,rowNum: INTEGER; lHandle: ListHandle);
(dataPtr: Ptr; dataLen: INTEGER; theCell: Cell;
lHandle: ListHandle);
(theCell: Cell; lHandle: ListHandle);
(dataPtr: Ptr; VAR dataLen: INTEGER; theCell:
Cell; lHandle: ListHandle);
(dataPtr: Ptr; dataLen: INTEGER; theCell: Cell;
lHandle: ListHandle);
(cSize: Point; lHandle: ListHandle );
(next: BOOLEAN; VAR theCell: Cell; lHandle:
ListHandle) : BOOLEAN;
(setit: BOOLEAN; theCell: Cell; lHandle:
ListHandle) ;
FUNCTION LClick
(pt: Point; modifiers: INTEGER; lHandle:
ListHandle) : BOOLEAN;
FUNCTION LLastClick
(lHandle: ListHandle) : Cell;
Summary of the List Manager Package IV-279

<!-- source-page: 286 -->
## Page 286

Inside Macintosh
Accessing Cells
PROCEDURE LFind
(VAR offset,len: INTEGER; theCell: Cell; lHandle:
ListHandle);
FUNCTION
LNextCell
(hNext,vNext: BOOLEAN; VAR theCell: Cell; lHandle:
ListHandle) : BOOLEAN
PROCEDURE LRect
(VAR cellRect: Rect; theCell: Cell; lHandle:
ListHandle);
FUNCTION
LSearch
(dataPtr: Ptr; dataLen: INTEGER; searchProc: Ptr;
VAR theCell: Cell; lHandle: ListHandle) : BOOLEAN;
PROCEDURE LSize
(listWidth,listHeight: INTEGER; lHandle:
List Display
PROCEDURE LDraw
PROCEDURE LDoDraw
PROCEDURE LScroll
PROCEDURE LAutoScroll
PROCEDURE LUpdate
PROCEDURE LActivate
ListHandle);
(theCell: Cell; lHandle: ListHandle);
(drawit: BOOLEAN; lHandle: ListHandle);
(dCols,dRows: INTEGER; !Handle: ListHandle);
(lHandle: ListHandle);
(theRgn: RgnHandle; lHandle: ListHandle);
(act: BOOLEAN; lHandle: ListHandle);
List Definition Procedure
PROCEDURE MyListDef (!Message: INTEGER; lSelect: BOOLEAN; lRect: Rect;
lCell: Cell; lDataOffset,lDataLen: INTEGER;
lHandle: ListHandle);
Assembly-Language Information
Constants
; Automatic scrolling flags
lDoVAutoscroll
.EQU
lDoHAutoscroll
.EQU
; Selection flags
lOnlyOne
.EQU
lExtendDrag
.EQU
lNoDisjoint
.EQU
lNoExtend
.EQU
lNoRect
.EQU
lUseSense
.EQU
lNoNilHilite
.EQU
1
0
7
6
5
4
3
2
1
;set to allow automatic vertical scrolling
;set to allow automatic horizontal scrolling
;set if only one selection at a time
;set for dragging without Shift key
;set to turn off multiple selections with
; click
;set to not extend Shift selections
;set to not grow selections as rectangles
;set for Shift to use sense of first cell
;set to not highlight empty cells
IV-280 Summary of the List Manager Package

<!-- source-page: 287 -->
## Page 287

The List Manager Package
; Messages to list definition procedure
linitMsg
lDrawMsg
lHiliteMsg
lCloseMsg
.EQU
0
.EQU
1
.EQU
2
.EQU
3
;initialize list, set defaults, allocate space
;draw the indicated cell data
;invert (select/deselect) the state of a cell
;dispose of list and any associated data
Routine selectors
(Note:
You can invoke each of the List Manager routines with a macro
that has the same name as the routine preceded by an underscore.)
lActivate
.EQU
0
lAddColumn
.EQU
4
lAddRow
.EQU
8
lAddToCell
.EQU
12
lAutoScroll
.EQU
16
lCellSize
.EQU
20
lClick
.EQU
24
lClrCell
.EQU
28
lDelColurnn
.EQU
32
lDelRow
.EQU
36
lDispose
.EQU
40
lDoDraw
.EQU
44
lDraw
.EQU
48
lFind
.EQU
52
lGetCell
.EQU
56
lGetSelect
.EQU
60
lLastClick
.EQU
64
lNew
.EQU
68
lNextCell
.EQU
72
lRect
.EQU
76
lScroll
.EQU
80
lSearch
.EQU
84
lSetCell
.EQU
88
lSetSelect
.EQU
92
lSize
.EQU
96
lUpdate
.EQU
100
List Record Data Structure
rView
port
indent
cellSize
visible
vScroll
hScroll
selFlags
!Active
clikTime
clikLoc
mouseLoc
lClikLoop
List's display rectangle (rectangle; 8 bytes)
List's gratPort (portRec bytes)
Indent distance (point; long)
Cell size (point; long)
Boundary of visible cells (rectangle; 8 bytes)
Handle to vertical scroll bar
Handle to horizontal scroll bar
Selection flags (byte)
Nonzero if active (byte)
Time of last click (long)
Position of last click (point; long)
Current mouse location (point; long)
Pointer to routine to be called during LClick
Summary of the List Manager Package W-281

<!-- source-page: 288 -->
## Page 288

Inside Macintosh
lastClick
ref Con
listDefHandle
user Handle
dataBounds
cells
max.Index
cellArray
'
Last cell clicked (point; long)
Reference value (long)
Handle to list definition procedure
Handle t6 usef storage
Boundary of ~ells allocated (rectangle; 8 bytes)
Handle to cell data
U &ed internally (word)
Offsets to cells
Trap Macro Name
_PackO
(Note:. Ybu can invoke each,of the List Manager routines with a macro that has the same
nartie ii.s the routine preceded by an tinderscore.)
IV-282 Summary of the List Manager Package

<!-- source-page: 289 -->
## Page 289

31
THE SCSI MANAGER
285
About This Chapter
285
About the SCSI Manager
286
Using the SCSI Manager
286
Describing the Operation to be Performed
288
Example
289
SCSI Manager Routines
292
Writing a Driver for an SCSI Block Device
294
Summary of the SCSI Manager
Contents W-283

<!-- source-page: 290 -->
## Page 290

f nsitk .M(lCjntosh

<!-- source-page: 291 -->
## Page 291

The SCSI Manager
ABOUT THIS CHAPTER
This chapter describes the SCSI Manager, the part of the Operating System that controls the
exchange of information between a Macintosh and peripheral devices connected through the
Small Computer Standard Interface (Scsn.
The SCSI Manager is the Macintosh implementation of an SCSI bus and its attached
devices. This chapter describes the routines and data structures you'll use to communicate
between a Macintosh and peripherals over an SCSI bus. It also explains how to write an
SCSI device driver that's capable of perfonning the Macintosh system startup.
This chapter provides information needed to connect a device to the MaCintosh via an SCSI
bus; it is not intended as a guide to designing an SCSI device. A familiarity with the
American National Standard Committee (ANSC) documentation for SCSI, specifically the
ANSC X3T9.2/82-2 draft proposal, is assumed; the information provided in the draft
proposal will not be repeated in this chapter.
You should also already be familiar with:
• the use of devices and device drivers, as described in the Device Manager chapter
• sectors and file tags, as described in the Disk Driver chapter
• any documentation provided with the particular SCSI device you want to connect to
the Macintosh
ABOUT THE SCSI MANAGER
The Small Computer Standard Interface (SCSI) is a specification of mechanical,
electrical, and functional standards for connecting small computers with intelligent
peripherals such as hard disks, printers, and optical disks. The SCSI Manager is the part
of the Operating System that provides routines and data structures for communicating
between a Macintosh and peripheral devices according to this industry-standard interface.
Up to eight devices can be connected, in a daisy-chain configuration, to an SCSI bus.
When two SCSI devices communicate with each other, one acts as the initiator and the
other as the target. The initiator asks the target to perform a certain operation, such as
reading a block of data. An SCSI device typically has a fixed role as an initiator or target;
for instance, the Macintosh acts as initiator to a variety of peripherals acting as targets.
There may also be intelligent peripherals capable of acting as initiators. Multiple initiators
(as well as multiple targets) are allowed on an SCSI bus, but only one Macintosh can be
connected to an SCSI bus at a time.
Each device on the bus has a unique ID, an integer from 0 to 7. The Macintosh always has
an ID of7; peripheral devices should choose another number.
At any given time, the Apple SCSI bus is in one of eight phases. When no SCSI device is
actively using the bus, the bus is in the bus free phase.
About the SCSI Manager W-285

<!-- source-page: 292 -->
## Page 292

Inside Macintosh
Since multiple initiators are possible, an initiator must first gain control of the bus; this
process is called the arbitration phase.
Note: If more than one initiator arbitrates for use of the bus at the same time, the
initiator with the higher ID gains control first. Once an initiator (regardless of ID)
gains control of the bus, no other device can interrupt that session.
Once the initiator has gained control of the bus, it selects the target device that will be asked
to perform a certain operation; this phase, known as the selection phase, includes an
acknowledgement from the target that it has been selected. In the event that the target
suspends (or disconnects) the communication, an optional phase, known as the
reselection phase, lets the target reconnect to the initiator.
In the command phase, the initiator tells the target what operation to perform. The data
phase follows; this is when the actual transfer of data between initiator and target takes
place. When the operation is completed, the target sends two completion bytes. The first
byte contains status information and the second contains a message; they constitute the
status phase and message phase respectively.
A typical communication might involve a Macintosh requesting a block of data to be read
from a hard disk connected via an SCSI bus. The Macintosh waits for a bus free phase to
occur and then arbitrates for use of the bus. It selects the hard disk as target and sends the
command for the read operation. The hard disk transfers the requested data back to the
Macintosh, completing the session by sending the status and message bytes.
USING THE SCSI MANAGER
The SCSI Manager is automatically initialized when the system starts up. To gain control
of the SCSI bus, call SCSIGet. To select a target device to perform an operation (such as
reading or writing data), call SCSISelect. The SCSICmd function tells the target device
what operation to perform.
To transfer data from the target device to the Macintosh, you can call SCSIR.ead;
SCSIWrite transfers data from the Macintosh to the target device. The read and write
operations can be performed without polling and waiting for the /R.EQ line on each data
byte by calling SCSIR.Blind and SCSIWBlind, respectively. All four read/write functions
require a transfer instruction block telling the SCSI Manager what to do with the data bytes
transferred during the data phase.
The SCSIComplete function gives the current command a specified number of ticks to
complete and then returns the status and message bytes.
You can obtain a bit map of the SCSI control and status bits by calling SCSIStat. To reset
the SCSI bus (typically when a device has left it in a suspended phase), call SCSIR.eset.
Describing the Operation to be Performed
You tell the SCSI Manager what operation to petform by passing a pointer to a command
descriptor block; the SCSI command structure is outlined in the ANSC document
X3T9.2/82-2.
W-286 Using the SCSI Manager

<!-- source-page: 293 -->
## Page 293

The SCSI Manager
When the command to be performed involves a transfer of data (such as a read or write
operation), you also need to pass a pointer to a transfer instruction block, which tells
the SCSI Manager what to do with the data bytes transferred during the data phase. A
transfer instruction block contains a pseudo-program consisting of a variable number of
instructions; it's similar to a subroutine except that the instructions are provided and
interpreted by the SCSI Manager itself. The instructions are of a fixed size and have the
following structure:
TYPE SCSIInstr
RECORD
scOpcode: INTEGER; {operation code}
scParaml: LONGINT; {first parameter}
scPararn2: LONGINT
{second parameter}
END;
Eight instructions are available; their operation codes are specified with the following
predefined constants:
CONST scinc
scNoinc
scAdd
scMove
scLoop
scNOp
scStop
scComp
1; {SC INC instruction}
2; {SCNOINC instruction}
3; {SCADD instruction}
4; {SCMOVE instruction}
5; {SCLOOP instruction}
6; {SCNOP instruction}
7; {SCSTOP instruction}
8; {SCCOMP instruction}
A description of the instructions is given below.
opcode = seine
paraml = buffer
param2 = count
The SCINC instruction moves count data bytes to or from buffer, incrementing buffer by
count when done.
opcode = scNolnc
paraml = buffer
param2 = count
The SCNOINC instruction moves count data bytes to or from buffer, leaving buffer
unmodified.
opcode = scAdd
paraml = addr
param2 = value
The SCADD instruction adds the given value to the address in addr. (The addition is
performed as an MC68000 long operation.)
opcode = scMove
paraml = addrl
param2 = addr2
The SCMOVE instruction moves the value pointed at by addrl to the location pointed to by
addr2. (The move is an MC68000 long operation.)
Using the SCSI Manager IV-287

<!-- source-page: 294 -->
## Page 294

Inside Macintosh
opcode = scLoop
paraml = relAddr
param2 = count
The SCLOOP instruction decrements count by 1. If the result is greater than 0, pseudoprogram execution resumes at the current address+relAddr. If the result is 0, pseudoprogram execution resumes at the next instruction. RelAddr should be a signed multiple of
the instruction size (10 bytes). For example, to loop to the immediately preceding
instruction, the relAddr field would contain-10. To loop forward by three instructions, it
would contain 30.
opcode = scNOp
paraml =NIL
param2 =NIL
The SCNOP instruction does nothing.
opcode = scStop
paraml =NIL
param2 =NIL
The SCSTOP instruction terminates the pseudo-program execution, returning to the calling
SCSI Manager routine.
opcode = scComp
paraml = addr
param2 = count
The SCCOMP instruction is used only with a read command. Beginning at addr, it
compares incoming data bytes with memory, incrementing addr by count when done. If
the bytes do not compare equally, an error is returned to the read command.
Example
This example gives a transfer instruction block for a transfer of six 512-byte blocks of data
from or to address $67B50.
SCINC
$67BSO
512
SCLOOP
-10
6
SCSTOP
IV-288 Using the SCSI Manager

<!-- source-page: 295 -->
## Page 295

The SCSI Manager
SCSI MANAGER ROUTINES
Assembly-language note: Unlike most other Operating System routines, the SCSI
Manager routines are stack-based. You can invoke each of the SCSI routines with a
macro that has the same name as the routine preceded by an underscore. These macros,
however, aren't trap macros themselves; instead they expand to invoke the trap macro
_SCSIDispatch. The SCSI Manager determines which routine to execute from the
routine selector, an integer that's passed to it in a word on the stack. The routine
selectors are as follows:
scsiReset
.EQU
0
scsiGet
.EQU
1
scsiSelect
.EQU
2
scsiCmd
.EQU
3
scsiComplete
.EQU
4
scsiRead
.EQU
5
scsiWrite
.EQU
6
scsiRBlind
.EQU
8
scsiWBlind
.EQU
9
scsiStat
.EQU
10
Most of the SCSI Manager routines return an integer result code of type OSErr. Each
routine lists all of the applicable result codes, along with a short description of what the
result code means. Lengthier explanations of all the result codes can be found in the
summary at the end of this chapter.
Warning: The error codes returned by SCSI Manager routines typically indicate
only that a given operation failed. To determine the actual cause of the failure, you
need to send another SCSI command asking the device what went wrong.
FUNCTION SCSIReset : OSErr;
SCSIReset resets the SCSI bus.
Result codes
no Err
commErr
FUNCTION SCSIGet : OSErr;
No error
Breakdown in SCSI protocols
SCSIGet arbitrates for use of the SCSI bus.
Result codes
no Err
commErr
No error
Breakdown in SCSI protocols
SCSI Manager Routines N-289

<!-- source-page: 296 -->
## Page 296

Inside Macintosh
FUNCTION SCSISelect (targetID: INTEGER) : OSErr;
SCSISelect selects the device whose ID is in targetID.
Result codes
noErr
No error
commErr
Breakdown in SCSI protocols
FUNCTION SCSICmd (buffer: Ptr; count: IN+EGER) : OSErr;
SCSICmd sends the command pointed to by buffer to the selected target device. The size
pf the command in bytes is specified i~ cpunt.
Result codes
noErr
commErr
phaseErr
No error
Breakdown in SCSI protocols
Phase error
•
.l;
F~CTION SCSIRead (tibPtr: Ptr)
OSErr;
SCSIRea.d transfers data from the target to the initiator, as specified in the transfer
instruction block pointed to by tibPtr.
Result codes
no Err
badPannsErr
commErr
compare Err
phaseErr
No error
Unrecognized instruction in transfer instruction block
Breakdown in SCSI protocols
Data comparison error (with scComp command in
transfer instruction block)
Phase error
FUNCTION SCSIRBlind (tibPtr: Ptr) : OSErr;
SCSIRBlind is functionally identical to SCSIRead, but does not poll and wait for the /REQ
line on each data byte. Rather, the /REQ line is polled only for the first byte transferred by
each SCINC, SCNOJNC, or SCCOMP instruction. For in:,tance, given the following
transfer instruction block
SCINC
$67B50
512
SCLOOP
-10
6
SCSTOP
SCSIRBlind polls an4 waits only for the first byte of each 512-byte block transferred.
Result codes
no Err
badPannsErr
commErr
compareErr
phaseErr
IV-290 SCSI Manager Routines
No error
Unrecognized instruction
Breakdown in SCSI protocols
Data comparison error
Phase error

<!-- source-page: 297 -->
## Page 297

The SCSI Manager
FUNCTION SCSIWrite (tibPtr: Ptr) : OSErr;
SCSIWrite transfers data from the initiator to the target, as specified in the command
descriptor block pointed to by tibPtr.
Result codes
no Err
badParmsErr
commErr
phaseErr
No error
Unrecognized instruction
Breakdown in SCSI protocols
Phase error
FUNCTION SCSIWBlind (tibPtr: Ptr) : OSErr;
SCSIWBlind is functionally identical to SCSIWrite, but does not poll and wait for the
JREQ line on each data byte. As with SCSIRBlind, SCSIWBlind polls the JREQ line only
for the first byte transferred by each SCINC, SCNOINC, or SCCOMP instruction.
Result codes
no Err
badParmsErr
commErr
phaseErr
No error
Unrecognized instruction
Breakdown in SCSI protocols
Phase error
FUNCTION SCSIComplete (VAR stat,message: INTEGER; wait: LONGINT)
OSErr;
SCSI Complete gives the current command wait number of ticks to complete; the two
completion bytes are returned in stat and message.
Result codes
noErr
commErr
phaseErr
No error
Breakdown in SCSI protocols
Phase error
FUNCTION SCSIStat : INTEGER;
This function returns a bit map of SCSI control and status bits; these bits are shown in
Figure 1. See the NCR 5380 SCSI chip documentation for a description of these signals.
(Bits 0-9 are complements of the SCSI bus standar4 ~ignals.)
15
8
7
0
END DMA PTY INT
PHS BSY ATN ACK RST BSY REQ MSG CID 1/0 SEL DBP
OMA REQ ERR REQ MAT EBR
.
Figure 1. SCSI Control and Status Bits
Result codes
noErr
commErr
phase Err
No error
Breakdown in SCSI protocols
Phase error
SCSI Manager Routines IV-291

<!-- source-page: 298 -->
## Page 298

Inside Macintosh
WRITING A DRIVER FOR AN SCSI BLOCK DEVICE
Device drivers are usually written in assembly language. The structure of a device driver is
described in the Device Manager chapter. This section presents additional information to
enable SCSI block devices to perform the Macintosh system startup.
For each attached SCSI device, the ROM attempts to read in its driver prior to system
startup. In order to be loaded, the device must place two data structures in the first two
physical blocks. A driver descriptor map must be put at the start of physical block O; it
identifies the various device drivers available for loading (see Figure 2). The drivers can
then be located anywhere else on the device and can be as large as necessary.
first
[
driver
descriptor
sbSig (word)
sbBlkSize (word)
sbBlkCount (long word)
sbDevType (word)
sbDevlD (word)
sbData (long word)
sbDrvrCount (word)
ddBlock (long word)
ddS i ze (word)
ddType (word)
always $4552
block size of device
number of blocks on device
device type
device ID
not used
driver descriptor count
first block of driver
driver size in blocks
system type (1 for Macintosh
Plus)
Figure 2. Driver Descriptor Map
A second data structure, the device partition map, must be put at the start of physical
block 1; it describes the allocation of blocks on the device for different partitions and/or
operating systems (see Figure 3).
first
[
partition
pdSig (word)
pdStart (long word)
pdS i ze (I ong word)
pdFSID (long word)
a I ways $5453
start i no b I ock address
number of blocks
file system ID ("TFS1" for
Macintosh Plus)
Figure 3. Device Partition Map
Since there's no field in the device partition map for specifying the number of partitions,
you need to signal the end of the map with a partition whose pdStart, pdSize, and pdFSID
fields are set to 0.
IV-292 Writing a Driver for an SCSI Block Device

<!-- source-page: 299 -->
## Page 299

The SCSI Manager
The system startup procedure takes the following steps:
1. It attempts to select the first target device on the bus by its ID, beginning with the
device, if any, having an ID of 6.
2. It reads the first 256 bytes of physical block 0, checking for the signature indicating a
valid driver descriptor map ($4552). It then reads the device partition map from
physical block 1 and checks for the proper signature ($5453).
3. It searches the driver descriptor map for a driver for the Macintosh.
4. It reads the driver from the indicated physical blocks into the system heap, using
standard SCSI read commands. It checks for a proper driver signature.
5. It calls the driver to install itself, and passes a pointer to the device partition map for
examination by the driver.
6. It performs steps 1 through 5 for all other SCSI devices on the bus.
Note: During system startup, the SCSI Manager may call SCSIReset after your
driver has been loaded.
Since the driver is called to install itself, it must contain code to set up its own entry in the
unit table and to call its own Open routine. An example of how to do this can be obtained
from
Developer Technical Support.
Mail Stop 3-T
Apple Computer, Inc.
20525 Mariani Avenue
Cupertino, CA 95014
Writing a Driver for an SCSI Block Device W-293

<!-- source-page: 300 -->
## Page 300

Inside Macintosh
SUMMARY OF THE SCSI MANAGER
Constants
CONST { Transfer instruction operation codes
scinc
1;
{SCINC instruction}
scNoinc
2;
{ SCNOINC instruction}
scAdd
3;
{SCADD instruction}
scMove
4;
{SCMOVE instruction}
scLoop
5;
{SCLOOP instruction}
scNop
6;
{SCNOP instruction}
scStop
7;
{SCSTOP instruction}
scComp
8;
{ SCCOMP instruction}
{ SCSI Manager result codes }
scBadParmsErr
scCommErr
scCompareErr
scPhaseErr
Data Types
4;
{unrecognized instruction in transfer }
{ instruction block}
2;
{breakdown in SCSI protocols:
usually no
{ device connected or bus not terminated}
6;
{data comparison error during read (with }
{ SCCOMP instruction in transfer }
{ instruction block) }
5;
{phase error:
target and initiator not in
{ agreement as to type of information to }
{ transfer},
TYPE SCSIInstr
RECORD
Routines
FUNCTION
FUNCTION
FUNCTION
FUNCTION
FUNCTION
FUNCTION
FUNCTION
FUNCTION
FUNCTION
FUNCTION
scOpcode: INTEGER;
scParaml: LONG INT;
scParam2: LONGINT
{operation code}
{first parameter}
{second parameter}
END;
SCSIReset
SCSIGet :
SCSI Select
SCSICmd
SCSIRead
SCSIRBlind
SCSIWrite
SCSIWBlind
SCSIComplete
SCSIStat :
OSErr;
OSErr;
(targetID: INTEGER)
: OSErr;
(buffer: Ptr; count: INTEGER)
OSErr;
(tibPtr: Ptr) : OSErr;
(tibPtr: Ptr) : OSErr;
(tibPtr: Ptr ) : OS Err;
(tibPtr: Ptr) : OSErr;
(VAR stat,message: INTEGER; wait: LONGINT)
OSErr;
INTEGER;
IV-294 Summary of the SCSI Manager

<!-- source-page: 301 -->
## Page 301

The SCSI Manager
Assembly-Language Information
Constants
; Transfer instruction operation codes
scinc
.EQU
1
;SCINC instruction
scNoinc .EQU
2
;SCNOINC instruction
scAdd
.EQU
3
;SCADD instruction
scMove
.EQU
4
;SCMOVE instruction
scLoop
.EQU
5
;SCLOOP instruction
scNOp
.EQU
6
;SCNOP instruction
scstop
.EQU
7
;SCSTOP instruction
scComp
.EQU
8
;SCCOMP instruction
Routine selectors
(Note:
You can invoke each of the SCSI Manager routines with a macro
that has the same name as the routine preceded by an underscore.)
scsiReset
.EQU
scsiGet
.EQU
scsiSelect
.EQU
scsiCmd
.EQU
scsiComplete
.EQU
scsiRead
.EQU
scsiWrite
.EQU
scsiRBlind
.EQU
scsiWBlind
.EQU
scsiStat
.EQU
; SCSI Manager result
scBadParmsErr
.EQU
scCommErr
.EQU
scCompareErr
.EQU
scPhaseErr
.EQU
Trap Macro Name
_SCSIDispatch
0
1
2
3
4
5
6
8
9
10
codes
4
2
6
5
;unrecognized instruction in transfer
; instruction block
;breakdown in SCSI protocols:
usually no
; device connected or bus not terminated
;data comparison error during read (with
; scComp command in transfer instruction
; block)
;phase error:
target and initiator not in
agreement as to type of information to
; transfer
(Note: You can invoke each of the SCSI Manager routines with a macro that has the same
name as the routine preceded by an underscore.)
Summary of the SCSI Manager IV-295

<!-- source-page: 302 -->
## Page 302

Inside Macintosh

<!-- source-page: 303 -->
## Page 303

32
THE TIME MANAGER
299
About This Chapter
299
About the Time Manager
299
Using the Time Manager
300
Time Manager Routines
301
Summary of the Time Manager
Contents IV-297

<!-- source-page: 304 -->
## Page 304

Inside Macintosh
IV-298

<!-- source-page: 305 -->
## Page 305

The Time Manager
ABOUT THIS CHAPTER
This chapter describes the Time Manager, the part of the Operating System that lets you
schedule a routine to be executed after a given number of milliseconds have elapsed.
ABOUT THE TIME MANAGER
The Time Manager provides the user with an asynchronous "wakeup" service with 1-
millisecond accuracy; it can have any number of outstanding wakeup requests. The Time
Manager is independent of clock speed or interrupts, and should be used in place of cyclecounting timing loops.
An application can add any number of tasks for the Ti.me Manager to schedule. These tasks
can perform any desired action so long as they don't rllfilce any calls to the Memory·
Manager, directly or indirectly, and don't depend on ttKtifiles to unlocked blocks being
valid. They must preserve all registers other than AO-A3 and DO-D3. If they use
application globals, they must also ensure that register A5 contains the address of the
boundary between the application globals and the application parameters; for details, see
SetUpA5 and RestoreA5 in chapter 13.
Note: To perform periodic actions that do allocate aiitl release memory, you can use
the Desk Manager procedure SystemTask.
Information describing each Time Manager task is contained in the Time Manager queue;
you need only supply a pointer to the routine to be executed. The Time Manager queue is a
standard Macinto~h queue, as described in the Operating System Utilities chapter. Each
entry in the Tinie Manager queue has the following structure:
TYPE TMTask = RECORD
qLink:
QElemPtr;
qType:
INTEGER;
tmAddr:
ProcPtr;
tmCount: INTEGER
END;
USING THE TIME MANAGER
{next queue entry}
{queue type}
{pointer to routine}
{reserved}
The Time Manager is automatically initialized when the system starts up. Since the "sleep"
time for a given task can be as small as 1 millisecond, you need to install a queue element in
the Time Manager queue before actually making the wakeup request; to do this, call
InsTime. To make the actual wakeup request, call PrimeTime. When you 're done, call
RmvTinie to remove the element from the queue.
Using the Time Manager IV-299

<!-- source-page: 306 -->
## Page 306

Inside Macintosh
TIME MANAGER ROUTINES
PROCEDURE InsTirne (trnTaskPtr: QElernPtr);
Trap macro
On entry
On exit
_Ins Time
AO: tmTaskPtr (pointer)
DO: result code (word)
InsTime adds the task specified by tmTaskPtr to the Time Manager queue. InsTime returns
one of the result codes listed below.
Result codes
noErr
No error
PROCEDURE PrimeTirne (trnTaskPtr,count: LONGINT);
Trap macro
On entry
On exit
_Prime Time
AO: tmTaskPtr (pointer)
DO: count (long word)
DO: result code ( word)
PrimeTime schedules the routine specified by tmTaskPtr to be executed 8fter count
milliseconds have elapsed. The queue element must already be inserted into the queue by a
call to InsTime before making the PrimeTime call. The PrimeTime routine returns
immediately, and the specified routine will be executed after count milliseconds have
elapsed.
Result codes
noErr
No error
PROCEDURE RrnvTirne (trnTaskPtr: QElernPtr);
Trap macro
On entry
On exit
_RmvTime
AO: tmTaskPtr (pointer)
DO: result code (word)
RmvTime removes the task specified by tmTaskPtr from the Time Manager queue.
RmvTime returns one of the result codes listed below.
Result codes
noErr
No error
IV-300 Time Manager Routines

<!-- source-page: 307 -->
## Page 307

SUMMARY OF THE TIME MANAGER
Data Types
TYPE TMTask = RECORD
qLink:
qType:
tmAddr:
tmCount:
QElemPtr; {next queue entry}
INTEGER;
{queue type}
ProcPtr;
{pointer to task}
INTEGER
{reserved}
END;
Routines
PROCEDURE InsTime
PROCEDURE RmvTime
PROCEDURE PrimeTime
(tmTaskPtr: QElemPtr);
(tmTaskPtr: QElemPtr);
(tmTaskPtr,count: LONGINT);
Assembly-Language Information
Routines
Trap macro
_Ins Time
_RmvTime
_Prime Time
On entry
AO: tmTaskPtr (ptr)
AO: tmTaskPtr (ptr)
AO: tmTaskPtr (ptr)
DO: count (long)
On exit
DO: result code (word)
DO: result code (word)
DO: result code (word)
Structure of Time Manager Queue Entry
qLink
qType
tmAddr
tmCount
Pointer to next queue entry
Queue type (word)
Pointer to task
Reserved (word)
The Time Manager
Summary of the Time Manager IV-301

<!-- source-page: 308 -->
## Page 308

IV-302

<!-- source-page: 309 -->
## Page 309

APPENDIX A: ROUTINES THAT MAY MOVE
OR PURGE MEMORY
This appendix lists all the new routines that may move or purge blocks in the heap. As
described in chapter 1 of Volume II, calling these routines may cause problems if a handle
has been dereferenced. None of these routines may be called from within an intenupt,
such as in a completion routine or a VBL task.
DelMenuItem
Drawl Control
FindDItem
FontMetrics
CietllndR.esource
CietlindType
CietlNamedR.esource
CietlResource
HideDItem
InsMenuItem
Measure Text
MoveHHi
New Empty Handle
OpenRFPerm
PStr2Dec
Dec2Str
CStr2Dec
ShowDItem
TEAutoView
TEPinScroll
TESelView
TrackBox
UpdtControl
UpdtDialog
Zoom Window
Routines That May Move or Purge Memory IV-303

<!-- source-page: 310 -->
## Page 310

Inside Macintosh
_,;.-··
W-304

<!-- source-page: 311 -->
## Page 311

APPENDIX B: SYSTEM TRAPS
This appendix lists the trap macros for the new Toolbox and Operating System routines and
their corresponding trap word values in hexadecimal. The "Name" column gives the trap
macro name (without its initial underscore character). In those cases where the name of the
equivalent Pascal call is different, the Pascal name appears indented under the main entry.
The routines in Macintosh packages are listed under the macros they invoke after pushing a
routine selector onto the stack; the routine selector follows the Pascal routine name in
parentheses.
There are two tables: The first is ordered alphabetically by name; the second is ordered
numerically by trap number, for use when debugging. (The trap number is the last two
digits of the trap word unless the trap word begins with A9, in which case the trap number
is 1 followed by the last two digits of the trap word.)
Warning: Traps that aren't currently used by the system are reserved for future
use.
Name
Trap word
Name
Trap word
CalcMask
A838
CatMove
(5)
Copy Mask
A817
DirCreate
(6)
Count1Resources
A80D
GetWDInfo
(7)
Countl Types
A81C
GetFCBinfo
(8)
DelMenuItem
A952
GetCatlnfo
(9)
Drawl Control
A96D
SetCatlnfo
(10)
FindDItem
A984
SetVollnfo
(11)
Fix2Frac
A841
LockRng
(16)
Fix2Long
A840
UnlockRng
(17)
Fix2X
A843
HGetState
A069
FixATan2
A818
HideDItem
A827
FixDiv
A84D
HSetRBit
A067
FontMetrics
A835
HSetState
A06A
Frac2Fix
A842
InsMenuItem
A826
Frac2X
A845
Long2Fix
A83F
FracCos
A847
MaxApplZ.one
A063
FracDiv
A84B
MaxBlock
A061
FracMul
A84A
MaxSizeRsrc
A821
FracSin
A848
Measure Text
A837
FracSqrt
A849
MoveHHi
A064
GetllxR.esource
A80E
New Empty Handle
A066
GetllndR.esource
OpenRFPerm
A9C4
GetllxType
A80F
PackO
A9E7
GetlindType
LActivate
(0)
GetlNamedR.esource
A820
LAddColumn
(4)
Get1Resource
A81F
LAddR.ow
(8)
HClrRBit
A068
LAddToCell
(12)
HFSDispatch
A260
LAutoScroll
(16)
OpenWD
(1)
LCellSize
(20)
CloseWD
(2)
LClick
(24)
System Traps IV-305

<!-- source-page: 312 -->
## Page 312

Inside Macintosh
Name
Trap word
Name
TralJ worcll
LClrCell
(28)
StackSpace
A065
LDelColumn
(32)
TEAutoView
A813
LDelRow
(36)
TEPinScroll
A812
LDispose
(40)
TES el View
A811
LDoDraw
(44)
TrackBox
A83B
LDraw
(48)
Unique1ID
A810
LFind
(52)
UpdtControl
A953
LGetCell
(56)
UpdtDialog
A978
LGetSelect
(60)
X2Fix
A844
LLastClick
(64)
X2Frac
A846
LNew
(68)
Zoom Window
A83A
LNextCell
(72)
LRect
(76)
LScroll
(80)
Trap word
Name
LSearch (84)
LSetCell
(88)
A050
RelString
LSetSelect
(92)
A067
HSetRBit
LSize
(96)
A068
HClrRBit
LUpdate
(100)
A069
HGetState
Pack7
A9EE
A06A
HSetState
PStr2Dec
(2)
A061
MaxBlock
Dec2Str
(3)
A062
PurgeSpace
CStr2Dec
(4)
A063
MaxAppJZone
Pack8
A816
A064
MoveHHi
Pack9
A82B
A065
StackSpace
PacklO
A82C
A066
NewEmptyHandle
Packll
A82D
A12F
PPostEvent
Pack12
A82E
A260
HFSDispatch
Pack13
A82F
OpenWD
(1)
Pack14
A830
CloseWD
(2)
Pack15
A831
CatMove
(5)
(Pack 8-Pack 15 reserved for future use)
DirCreate
(6)
PPostEvent
A12F
GetWDInfo
(7)
PurgeSpace
A062
GetFCBinfo (8)
RelString
A050
GeiCatlnfo
(9)
RsrcMapEntry
A9C5
SetCatlnfo
(10)
SCSIDispatch
A815
SetVollnfo
(11)
SCSIReset
(0)
LockRng
(16)
SCSI Get
(1)
UnlockRng
(17)
SCSISelect
(2)
A80D
Countl Resources
SCSICmd
(3)
A80E
GetllxResource
SCSI Complete (4)
Getl IndResource
SCSIRead
(5)
A80F
GetllxType
SCSIWrite
(6)
GetllndType
SCSIInstall
(7)
A810
Unique1ID
SCSIRBlind
(8)
A81C
Count1Types
SCSIWBlind
(9)
A81F
Getl Resource
SCSIStat
(10)
A811
TES el View
SeedFill
A839
A812
TEPinScroll
SetFScaleDisable
A834
A813
TEAutoView
ShowDItem
A828
IV-306 System Traps

<!-- source-page: 313 -->
## Page 313

System Traps
Trap word
Name
Trap word
Name
A815
SCSIDispatch
AS47
FracCos
SCSIReset
(0)
AS48
FracSin
SCSI Get
(1)
AS49
FracSqrt
SCSISelect
(2)
A84A
FracMul
SCSICmd
(3)
A84B
FracDiv
SCSIComplete (4)
A84D
FixDiv
SCSIRead
(5)
A952
DelMenuItem
SCSIWrite
(6)
A953
UpdtControl
SCSIInstall
(7)
A96D
Drawl Control
SCSIRBlind
(8)
A978
UpdtDialog
S~SIWBlind (9)
A984
FindDItem
SCSIStat
(10)
A9C4
OpenRFPerm
A816
Pack8
A9C5
RsrcMapEntry
A817
Copy Mask
A9E7
PackO
A818
FixATan2
LActivate
(0)
A820
Get1NamedResource
LAddColumn (4)
A821
MaxSizeRsrc
LAddRow
(8)
A82B
Pack9
LAddToCell
(12)
A82C
PacklO
LAutoScroll
(16)
A82D
Packll
LCellSize
(20)
A82E
Pack12
LClick
(24)
A82F
Pack13
LClrCell
(28)
A830
Pack14
LDelColumn (32)
A831
Pack15
LDelRow
(36)
A834
SetFScaleDisable
LDispose
(40)
A835
FontMetrics
LDoDraw
(44)
A826
InsMenuItem
LDraw
(48)
A827
HideDItem
LFind
(52)
A828
ShowDItem
LGetCell
(56)
A836
GetMaskTable
LGetSelect
(60)
A837
Measure Text
LLastClick
(64)
A838
Cale Mask
LNew
(68)
A839
SeedFill
LNextCell
(72)
A83A
Zoom Window
LRect
(76)
A83B
TrackBox
LScroll
(80)
A83F
Long2Fix
LSearch
(84)
A840
Fix2Long
LSetCell
(88)
A841
Fix2Frac
LSetSelect
(92)
A842
Frac2Fix
LSize
(96)
A843
Fix2X
LUpdate
(100)
A844
X2Fix
A9EE
Pack7
A845
Frac2X
PStr2Dec
(2)
A846
X2Frac
Dec2Str
(3)
CStriDec
(4)
System Traps IV-307

<!-- source-page: 314 -->
## Page 314

Inside Macinwsh
IV-308

<!-- source-page: 315 -->
## Page 315

APPENDIX C: GLOBAL VARIABLES
This appendix gives an alphabetical list of all system global variables described in this
volume, along with their locations in memory.
Name
Location
Contents
ApFontID
$984
Font number of application font (word)
BootDrive
$210
Working directory reference number for system
startup volume (word)
CurDirStore
$398
Directory ID of directory last opened (long)
DetVCBPtr
$352
Pointer to default volume control block
DrvQHdr
$308
Drive queue header (10 bytes)
FCBSPtr
$34E
Pointer to file-control-block buffer
FractEnable
$BF4
Nonzero to enable fractional widths (byte)
FSFCBLen
$3F6
Size of a file control block; on 64K ROM, it
contains-I (word)
FSQHdr
$360
File 1/0 queue header (10 bytes)
IntlSpec
$BAO
International software installed if not equal to -1
(long)
LastFOND
$BC2
Handle to last family record used
MemErr
$220
Current value of MemError (word)
ROMBase
$2AE
Base address of ROM
RomMapInsert
$B9E
Flag for whether to insert map to the ROM
resources (byte)
SFSaveDisk
$214
Negative of volume reference number, used by
Standard File Package (word)
SysFontFam
$BA6
If nonzero, the font number to use for system font
(word)
SysFontSize
$BA8
If nonzero, the size of the system font (word)
TmpResLoad
$B9F
Temporary SetResLoad state for calls using
ToExtFS
$3F2
ROMMaplnsert (byte)
Pointer to external file system
VCBQHdr
$356
Volume-control-block queue header (10 bytes)
WidthListHand
$8E4
Handle to a list of handles to recently-used width
tables
WidthPtr
$B10
Pointer to global width table
WidthTabHandle
$B2A
Handle to global width table
Global Variables IV-309

<!-- source-page: 316 -->
## Page 316

Inside Macintosh
JV;.3}0

<!-- source-page: 317 -->
## Page 317

GLOSSARY
access path: A description of the route that the File Manager follows to access a file;
created when a file is opened
access path buffer: Memory used by the File Manager to transfer data between an
application and a file.
active end: In a selection, the location to which the insertion point moves to complete the
selection.
allocation block: Volume space composed of multiples of logical blocks.
anchor point: In a selection, the location of the insertion point when the selection was
started.
application list: A data structure, kept in the Desktop file, for launching applications
from their documents in the hierarchical file system. For each application in the list, an
entry is maintained that includes the name and signature of the application, as well as the
directory ID of the folder containing it
arbitration phase: The phase in which an initiator attempts to gain control of the bus.
asynchronous execution: After calling a routine asynchronously, an application is free
to perform other tasks until the routine is completed.
block map: Same as volume allocation block map.
bus free phase: The phase in which no SCSI device is actively using the bus.
catalog tree file: A file that maintains the relationships between the files and directories
on a hierarchical directory volume. It corresponds to the file directory on a flat directory
volume.
cell: The basic component of a list from a structural point of view; a cell is a box in which
a list element is displayed.
Chooser: A desk accessory that provides a standard interface for device drivers to solicit
and accept specific choices from the user.
closed file: A file without an access path. Closed files cannot be read from or written to.
clump: A group of contiguous allocation blocks. Space is allocated to a new file in
clumps to promote file contiguity and avoid fragmentation.
clump size: The number of allocation blocks to be allocated to a new file.
command phase: The phase in which the SCSI initiator tells the target what operation to
perform.
Glossary W-311

<!-- source-page: 318 -->
## Page 318

Inside Macintosh
completion routine: Any application-defined code to be executed when an
asynchronous call to a routine is completed.
data buffer: Heap space containing information to be written to a file or device driver
from an application, or read from a file or device driver to an application.
data fork: The part of a file that contains data accessed via the File Manager.
data phase: The phase in which the actual transfer of data between an SCSI initiator and
target takes place.
default directory: A directory that will be used in File Manager routines whenever no
other directory is specified. It may be the root directory, in which case the default directory
is equivalent to the default volume.
default volume: A volume that will receive I/O during a File Manager routine call,
whenever no other volume is specified.
device partition map: A data structure that must be placed at the start of physical block
1 of an SCSI device to enable it to perform Macintosh system startup. It describes the
allocation of blocks on the device.
device resource file: An extension of the printer resource file, this file contains all the
resources needed by the Chooser for operating a particular device (including the device
driver code).
directory: A subdivision of a volume that can contain files as well as other directories;
equivalent to a folder.
directory ID: A unique number assigned to a directory, which the File Manager uses to
distinguish it from other directories on the volume. (It's functionally equivalent to the file
number assigned to a file; in fact, both directory IDs and file numbers are assigned from the
same set of numbers.)
drive number: A number used to identify a disk drive. The internal drive is number 1,
the external drive is number 2, and any additional drives will have larger numbers.
drive queue: A list of disk drives connected to the Macintosh.
driver descriptor map: A data structure that must be placed at the start of physical
block 0 of an SCSI device to enable it to perform Macintosh system startup. It identifies
the various device drivers on the device.
end-of-file: See logical end-of-file or physical end-of-file.
extent: A series of contiguous allocation blocks.
extent descriptor: A description of an extent, consisting of the number of the first
allocation block of the extent followed by the length of the extent in blocks.
extent record: A data record, stored in the leaf nodes of the extents tree file, that
contains three extent descriptors and a key identifying the record.
extents tree file: A file that contains the locations of the files on a volume.
W-312 Glossary

<!-- source-page: 319 -->
## Page 319

Glossary
family record: A data structure, derived from a family resource, that contains all the
information describing a font family.
file: A named, ordered sequence of bytes; a principal means by which data is stored and
transmitted on the Macintosh.
file catalog: A hierarchical file directory.
file control block: A fixed-length data structure, contained in the file-control-block
buffer, where information about an access path is stored.
file-control-block buffer: A nonrelocatable block in the system heap that contains one
file control block for each access path.
file directory: The part of a volume that contains descriptions and locations of all the
files and directories on the volume. There are two types of file directories: hierarchical file
directories and flat file directories.
file 1/0 queue: A queue containing parameter blocks for all 1/0 requests to the File
Manager.
file number: A unique number assigned to a file, which the File Manager uses to
distinguish it from other files on the volume. A file number specifies the file's entry in a
file directory.
font: A complete set of characters of one typeface, which may be restricted to a particular
size and style, or may comprise multiple sizes, or multiple sizes and styles, as in the
context of menus.
font family: A group of fonts of one basic design but with variations like weight and
slant.
font record: A data structure, derived from a font resource, that contains all the
information describing a font.
fork: One of the two parts of a file; see data fork and resource fork.
full pathname: A pathname beginning from the root directory.
global width table: A data structure in the system heap used by the Font Manager to
communicate fractional character widths to QuickDraw.
initiator device: An SCSI device that initiates a communication by asking another
device (known as the target device) to perform a certain operation.
1/0 request: A request for input from or output to a file or device driver; caused by
calling a File Manager or Device Manager routine asynchronously.
list definition procedure: A procedure called by the List Manager that determines the
appearance and behavior of a list.
Glossary IV-313

<!-- source-page: 320 -->
## Page 320

Inside Macintosh
list element: The basic component of a list from a logical point of view, a list element is
simply bytes of data. In a list of names, for instance, the name Melvin might be a list
,
element.
List Manager: The part of the Operating System that provides routines for creating,
displaying, and manipulating lists.
list record: The internal represen~tion of a list., where the List Manager stores all the
information it requires for its operations on that list.
locked file: A file whose data cannot be changed.
locked volume: A volume whose data cannot be changed. Volumes can be locked by
either a software flag or a mechanical setting.
logical block: Volume space composed of 512 consecutive bytes of standard
information and an additional number of bytes of information specific to the disk driver.
logical end-of-fil~: The position of one byte past the iast byte in a file; equal to the
actual number of bytes in the file.
mark: A marker used by the File Marlager to keep track of where it is during a read or
write operation.
master directory block: Part of the data structure of a flat directory volume; contains
the voltime information and the volume allocation block map.
messake phase: The phase in which the target sends one byte of message information
back to the initiator.
mounted volume: A volume that has been inserted into a disk drive and has had
descriptive information read from it by the File Manager.
newline character: Any character, but usually Return (ASCII code $OD), that indicates
the end of a sequence of bytes.
newline mode: A mode of reading data where the end of the data is indicated by a
newline character (and not by a specific byte count).
off-line volume: A mounted volume with all but the volume control block released.
offspring: For a given directory, the set of files and directories for which it is the parent.
on-iine volume: A mounted volume with its volume buffer and descriptive information
contained in memory.
open file: A file with an access path. Open files can be read from and written to.
open permission: Information about a file that indicates whether the file can be read
from, written to, or both.
parameter block: A data structure used to transfer information between applications and
certain Operating System routines.
W-314 Glossary

<!-- source-page: 321 -->
## Page 321

Glossary
parent: For a given file or directory, the directory immediately above it in the tree.
parent ID: The directory ID of the directory containing a file or directory.
partial pathname: A pathname beginning from any directory other than the root
directory.
pathname: A series of concatenated directory and file names that identifies a given file or
directory. See also partial pathname and full pathname.
path reference number: A number that uniquely identifies an individual access path;
assigned when the access path is created.
physical end-of-file: The position of one byte past the last allocation block of a file;
equal to 1 more than the maximum number of bytes the file can contain without growing.
reselection phase: An optional phase in which the SCSI initiator allows a target device
to reconnect itself to the initiator.
resource fork: The part of a file that contains data used by an application (such as
menus, fonts, and icons). The resource fork of an application file also contains the
application code itself.
root directory: The directory at the base of a file catalog.
routine selector: For routines that expand to the same macro, an integer that's pushed
onto the stack or placed into a register before the macro is invoked, to identify which
routi11e to execute. For instance, all SCSI routines expand to invoke the trap macro
_SC~IDispatch; each routine has a selector that's passed to the SCSI Manager in a word on
the stack before _SCSIDispatch is invoked.
SCSI: See Small Computer Standard Interface.
SCSI Manager: The part of the Operating System that controls the exchange of
information between a Macintosh and peripheral devices connected through the Small
Computer Standard Interface (SCSI).
selection phase: The phase in which the initiator selects the target devi~e that will be
asked to perform a certain operation.
Small Computer Standard Interface (SCSI): A specification of mechanical,
electrical, and functional standards for connecting small computers. with intelligent
peripherals such as hard disks, printers, and optical disks.
status phase: The phase in which the SCSI target sends one byte of status information
back to the initiator.
subdirectory: Any directory other than the root directory.
synchronous execution: After calling a routine synchronously, an application cannot
continue execution until the routine is completed.
Glossary IV-315

<!-- source-page: 322 -->
## Page 322

Inside Macintosh
Time Manager: The part of the Operating System that lets you schedule a routine to be
executed after a given number of milliseconds have elapsed.
target.device: An SCSI device (typically an intelligent peripheral) that receives a request
from an initiator device to perform a certain operation.
unmounted volume: A volume that hasn't been inserted into a disk drive and had
descriptive information read from it, or a volume that previously was mounted and has
since had the memory used by it released.
valence: The number of offspring for a given directory.
volume: A piece of storage medium formatted to contain files; usually a disk or part of a
disk. A 3 1/2-inch Macintosh disk is one volume.
volume allocation block map: A list of 12-bit entries, one for each allocation block,
that indicate whether the block is currently allocated to a file, whether it's free for use, or
which block is next in the file. Block maps exist both on flat directory volumes and in
memory.
volume attributes: Information contained on volumes and in memory indicating
whether the volume is locked, whether it's busy (in memory only), and whether the
volume control block matches the volume information (in memory only).
volume bit map: A data structure containing a sequence of bits, one bit for each
allocation block, that indicate whether the block is allocated or free for use. Volume bit
maps exist both on hierarchical directory volumes and in memory.
volume buff er: Memory used initially to load the master directory block, and used
thereafter for reading from files that are opened without an access path buffer.
volume control block: A nonrelocatable block that contains volume-specific
information.
volume-control-block queue: A list of the volume control blocks for all mounted
volumes.
volume information: Volume-specific information contained on a volume, including
the volume name and the number of files on the volume.
volume information block: Part of the data structure of a hierarchical directory
volume; it contains the volume information.
volume reference number: A unique number assigned to a volume as it's mounted,
used to refer to the volume.
working direct9ry: An alternative way of referring to a directory. When opened as a
working directory, a directory is given t:t. working directory reference number that's used to
refer to it in File Manager calls.
'
working directory control block: A data structure that contains the directory ID of a
working directory, as well as the volume reference number of the volume on which the
directory is located.
W-316 Glossary

<!-- source-page: 323 -->
## Page 323

Glossary
working directory reference number: A temporary reference number used to
identify a working directory. It can be used in place of the volume reference number in all
File Manager calls; the File Manager uses it to get the directory ID and volume reference
number from the working directory control block.
Glossary W-317

<!-- source-page: 324 -->
## Page 324

Inside Macintosh
IV-318

<!-- source-page: 325 -->
## Page 325

INDEX
A
access path IV-94
access path buffer IV-96
active end IV-5
Allocate function
high-level IV-112
low-level IV-143
allocation block IV-89
AllocContig function IV-143
anchorpoint IV-5
ApFontID global variable IV-31
AppleTalk Manager IV-229
application list IV-243
ApplLimit global variable IV-257
arbitration phase IV-286
arrow keys IV-3, 57
asynchronous execution, File
Manager IV-115
assembly language IV-13
automatic scrolling in TextEdit IV-57
B
B*-tree IV-168
Binary-Decimal Conversion Package IV-69
block (file) See allocation block
block map IV-162
boot blocks See system startup infonnation
BufPtr global variable IV-257
bus free phase IV-285
c
CalcMask procedure IV-24
catalog tree file IV-171
CatMove function IV-157
Chooser IV-216
communication with IV-217
operation of IV-219
writing a driver to run under IV-221
CInfoPBPtr data type IV-117
CInfoPBRec data type IV-125
ClnfoType data type IV-117
CMovePBPtr data type IV-117
CMovePBRec data type IV-127
click loop routine
List Manager IV-266
TextEdit IV-58
clock chip IV-251
Close function
high-level IV-112
low-level IV-144
closed file IV-94
CloseWD function IV-158
clump IV-124, 167
clump size IV-124, 167
Command-key combination See keyboard
equivalent
command phase IV-286
completion routine
File Manager IV-115
control, multiple lines of text in IV-53
control definition function IV-53
Control Manager IV-53
routines IV-53
CopyMask procedure IV-24
Count1Resources function IV-15
Countl Types function IV-15
Create function
high-level IV-112
low-level IV-145
CurDirStore global variable IV-72
current directory button IV-72
D
data buffer IV-95
data forte IV-93
data phase IV-286
Data Tenninal Ready line IV-225, 248
default directory IV-100
default volume IV-100
getting See GetVol function
setting See SetVol function
DefVCBPtr global variable IV-178
Delete function
high-level IV-113
low-level IV-147
DelMenuItem procedure IV-56
Index IV-319

<!-- source-page: 326 -->
## Page 326

In.side Macintosh
desk scrap IV-61
Desktop file IV-243
device control entry IV-215
device ID IV-217
Device Manager IV-213
device package IV-217
device partition map IV-292
dialog box
Oose IV-10
creating your own IV-74
Dialog Manager IV-59
routines IV-59
Dlnfo data type IV-105
DirCreate function IV-146
directory IV-89
directory ID IV-92
directory name IV-90
directory record IV-172
Disk Driver IV-223
advanced Control calls IV"."223
Disk Initialization Package IV-239
dispatch table See trap dispatch table
DlgHook function IV-75
DRAM See Dynamic RAM chips
Drawl Control procedure IV-53
drive number IV-93
drive queue IV-181
driver descriptor map IV-292
DrvQEl data type IV-181
DrvQHdr global variable IV-182
D1R See Data Tenninal Ready line
DXInfo data type IV-106
Dynamic RAM chips IV-246
E
Eject function
high-level IV-108
low-level IV-135
end-of-file IV-93
Environs procedure IV-236
error reporting
Memory Manager IV-80
Resource Manager IV-18
Event Manager, Operating System IV-85
routines IV-85
extent IV-170
extent descriptor IV-171
extent record IV-171
extents tree file IV-170
external file system IV-182
W-320 Index
F
family number IV-30
family record IV-36
family resource IV-43
FamRec data type IV-36
FCBPBPtr data type IV-117
FCBPBRec data type IV-179
FCBSPtr global variable IV-179
file IV-89, 93
file catalog See hierarchical file directory
file control block IV-94, 178
file-control-block buffer IV-178
file directory IV-89
file icon IV-105
file 1/0 queue IV-115, 175
File Manager IV-89
File Manager routines
high-level IV-106
low-level IV-115
for queue access IV-176, 178, 181
file name IV-90
file number IV-163
file record IV-172
FindDItem function IV-60
Finder infonnation IV-104
Finder Interface IV-243
Flnfo data type IV-104
FInitQueue procedure IV-128
FixA Tan2 function IV-65
FixDiv function IV-64
Fix2Frac function IV-65
Fix2Long function IV-65
Fix2X function IV-65
flat file directory IV-89, 163
FlushFile function IV-144
Flush Vol function
high-level IV-108
low-level IV-133
FMetric data type IV-32
FmtDefaults global variable IV-241
folder IV -105
font IV-29
variable size IV-56
Font/DAMover IV-31
font family IV-29
Font Manager IV-27
communication with QuickDraw IV-33
data structures IV-34
routines IV-31
fontnumber IV-30
font record IV-35

<!-- source-page: 327 -->
## Page 327

font resource IV-42
font scaling IV-33
FontMetrics procedure IV-32
fork IV-93
formatting hierarchical volumes IV-240
FracCos function IV-64
FracDiv function IV-64
FracMul function IV-64
FracSin function IV-64
FracSqrt function IV-64
FractEnable global variable IV-32
fractional character widths IV-33
Frac2Fix function IV-65
Frac2X function IV-65
FScaleDisable global variable IV-32
FSClose function IV-112
FSDelete function IV-113
FSFCBLen global variable IV-97
FSOpen function IV-109
FSQHdr global variable IV-176
FSRead function IV-109
FSWrite function IV-110
full pathname IV-99
FXInfo data type IV-105
G
GetCatlnfo function IV-155
GetDrvQHdr function IV-181
GetEOF function
high-level IV-111
low-level IV-142
GetFCBinfo function IV-179
GetFilelnfo function
high-level IV-113
low-level IV-148
GetFInfo function IV-113
GetFPos function
high-level IV-110
low-level IV-141
GetFSQHdr function IV-175
GetMaskTable function IV-25
Get1IndResource function IV-15
GetllndType procedure IV-15
Get1NamedResource function IV-15
Get1Resource function IV-16
GetTrapAddress function IV-234
GetVCBQHdrfunction IV-178
GetVInfo function IV-107
GetVol function
high-level IV-107
low-level IV-131
GetVollnfo function
high-level IV-107
low-level IV-129
GetVRefNum function IV-107
GetWDInfo function IV-159
global variables, list of IV-309
global width table IV-41
H
Hard Disk 20 IV-223
hardware IV-245
HOrRBit procedure IV-79
HCreate function IV-146
HDelete function IV-147
HFSDispatch trap macro IV-118
HGetFilelnfo function IV-149
HGetState function IV-79
HGetVInfo function IV-130
HGetVol function IV-132
HideDItem procedure IV-59
hierarchical file directory IV -89
HOpen function IV-136
HOpenRF function IV-137
HParamBlkPtr data type IV-117
HParmBlockRec data type IV-118
FileParam variant IV-122
IOParam variant IV-120
VolumeParam variant IV-123
HR.ename function IV-154
HR.stFLock function IV-152
HSetFilelnfo function IV-150
HSetFLock function IV-151
HSetRBit procedure IV-79
HSetState procedure IV-80
HSetVol function IV-133
HSetVollnfo function IV-131
I, J
indexing IV-101
initialization resources IV-256
initiator device IV-285
InitQueue procedure IV-128
lnsMenultem procedure IV-55
InsTime procedure IV-300
Index
Index IV-321 II

<!-- source-page: 328 -->
## Page 328

Inside Macintosh
IntlSpec global variable IV-42
1/0 queue See file I/0 queue
1/0 request IV-115
K
keyboard IV-250
keyboard equivalent, reserved IV-7
key-down transitions IV-250
keypad IV-250
L
LActivate procedure IV-276
LAddColumn function IV-271
LAddRow function IV-271
LAddToCell procedure IV-272
LAutoScroll procedure IV-275
LCellSize procedure IV-273
LClick function IV-273
LClrCell procedure IV-272
LDelColumn procedure IV-271
LDelRow procedure IV-272
LDispose procedure IV-271
LDoDrawprocedure IV-275
LDraw procedure IV-275
LFind procedure IV-274
LGetCell procedure IV-272
LGetSelect fupction IV-273
list IV-261
cell selection IV-266
defining your own IV-276
drawing IV-262
element IV-261
ListManagerPackage IV-259
routines IV-269
list record IV-262
ListHandle data type IV-264
ListPtr data type IV-264
ListRec data type IV-263
LLastClick function IV-273
LNew function IV-270
LNextCell function IV-274
LoadSeg procedure IV-83
locked file IV-94
locked volume IV-93
LockRng function IV-138
logical block IV-89, 160
logical end-of-file IV-93
Long2Fix function IV-65
W-322 Index
LRect procedure IV-274
LScroll procedure IV-275
LSearch function IV-274
LSetCell procedure IV-272
LSetSelect procedure IV-273
LSize procedure IV-274
LUpdate procedure IV-275
M
mark, in a file IV-94
master directory block IV-160
Max:ApplZoqe procedure IV-77, 83
MaxBlock fupction IV-77
Max:SizeRsrc function IV-16
MeasureText procedure IV-'.45
MemErr global variable IV-80
Memory Manager IV-77
routines IV-77
menu scrolling IV-56
menu definition procedure IV-56
menu ID I-344
Menu Manager IV-55
routines IV-55
message phase IV-286
Mini-8 connector IV-248
mounted volume IV-92
MountVol function IV-128
MoveHHi procedure IV-77, 83
N
NewEmptyHandle function IV-78
newline character IV-95
newline mode IV-95
NGetTrapAddress function IV-234
NSetTrapAddress procedure IV-234
numeric fonnatter IV-69
numeric scanner IV-69
0
off-line volume IV-92
OffLine function IV-134
offset/width table IV-34
offspring, of a directory IV-91
on-line volume IV-92
open file IV-94

<!-- source-page: 329 -->
## Page 329

Open function
high-level IV-109
low-level IV-135
open permission IV-95
OpenRF function
high-level IV-109
low-Jevel IV-137
QpenRFPerm function IV-17
qpenWD function IV-158
Operating System Event Manager IV-85
Operating Systerp. Utilities IV-233
routines IV-233
p
Pack 0 See List Manager Package
Pack 2 See Disk Initialization Package
Pack 3 See Standard File Package
Pack 7 See Binary-Decirp.al Conversion
Package
Package Manager IV-67
packages IV-67
ParamBlk.Type data type IV-117
ParamBlockRec data type IV-118
file I/O queue entry IV-175
FileParam variant IV-122
IOParam variant IV-120
Y olumeParam variant IV-123
parameter block IV-116
parameterRAM IV-251
parent directory IV-91
parent ID IV-92
ParmBlk.Ptr data type IV-117
partial pathname IV-99
path ref~rence number IV-94
pathname IV-99
PBAllocate function IV-143
PBAllocContig function IV-143
PBCatMove function IV-157
PBOose function IV-144
PBCloseWD function IV-158
PBCreate function IV-145
PBDelete function IV-147
PBDirCreate function IV-146
PBEject function IV-135
PBFlushFile function IV-144
PBFlushVol function IV-133
PBGetCatInfo function IV-155
PBGetEOF function IV-142
PBGetFCBInfo function IV-179
PBGetFInfo function IV-148
PBGetFPos function IV-141
PBGetVInfo function IV-129
PBGetVol function IV-131
PBGetWDInfo function IV-159
PBHCreate function IV-146
PBHDeletefunction IV-147
PBHGetFInfo function IV-149
PBHGetVInfo function IV-130
PBHGetVol function IV-132
PBHOpen function IV-136
PBHOpenRF function IV-137
PBHRename function IV-154
PBHRstFLock function IV-152
PBHSetFInfo function IV-150
PBHSetFLock function IV-151
PBHSetVol function IV-133
PBLockRange function IV-138
PBMountVol function IV-128
PBOffLine function IV-134
PBOpen function IV-135
PBOpenRF function IV-137
PBOpenWD function IV-158
PBRead function IV-139
PBRename function IV-153
PBRstFLock function IV-152
PBSetCatInfo function IV-156
PBSetEOF function IV-142
PB~~!Elnfo function IV-150
PBSetFLock function IV-151
PBSetFPos function IV-141
PBSetFVers function IV-153
PBSetVInfo function IV-131
PBSetVol function IV-132
PBUnlockRange function IV-139
PBUnmountVol function IV-134
PBWrite function IV-140
physical end-of-file IV-93
PrimeTime procedure IV-300
PurgeSpace procedure IV-78
a
queue
drive IV-181
file 1/0 IV-115, 175
Time Manager IV-299
volume-control-block IV-176
QuickDraw IV-23
Index
£Ommunication with Font Manager IV-33
foutines IV-23
Index IV-323
II

<!-- source-page: 330 -->
## Page 330

Inside Macintosh
R
RAM IV-246
Read function
high-level IV-H)<)
low-level IV-139
read/write pennission IV-95
relocatable blocks, properties of IV-78
RelString function IV-234
Rename function
high-level IV-114
low-level IV-153
reselection phase IV-286
resource fork IV-93
Resource Manager IV-15
routines IV-15
resource type list IV -17
result code
Resource Manager IV-18
RmvTime procedure IV-300
ROM IV-247
ROM resource IV-18
list IV-19
map IV-19
oveniding IV-20
ROM Serial Driver IV-225
advanced Control calls IV-226
ROMBase global variable IV-236
ROMMaplnsert global variable IV-19
root directory IV-91
routine selector
File Manager IV-118
List Manager IV-269
SCSI Manager IV-289
RsrcMapEntry function IV-16
RstFilLock function
high-level IV-114
low-level IV-152
RstFLock function IV-114
s
SANE IV-69
sec IV-248
Scrap Manager IV-61
screen buffer IV-24 7
SCSI See Small Computer Standard Interface
SCSI Manager IV-283
routines IV-289
writing a driver IV-292
SCSICmd function IV-290
SCSIComplete function IV-291
W-324 Index
SCSIGet function IV-289
SCSIInstr data type IV-287
SCSIRBlind function IV-290
SCSIRead function IV-290
SCSIReset function IV-289
SCSISelect function IV-290
SCSIStat function IV-291
SCSIWBlind function IV-291
SCSIWrite function IV-291
SeedFill procedure IV-24
Segment Loader IV-83
selection phase IV-286
Serial Communications Controller IV-248
Serial Driver IV-225
advanced Control calls IV-226
serial port IV-225,
SetCatlnfo function IV-156
SetEOF function
high-level IV-111
low-level IV-142
SetFileinfo function
high-level IV-114
low-level IV-150
SetFilLock function
high-level IV-114
low-level IV-151
SetFilType function IV-153
SetFinfo function IV-114
SetFLock function IV-114
SetFPos function
high-level IV-110
low-level IV-141
SetFractEnable IV-32
SetFScaleDisable procedure IV-32
SetTrapAddress procedure IV-234
SetVol function
high-level IV-107
low-level IV-132
SFSaveDisk global variable IV-72
ShowDItem procedure IV-59
SIMM See Single In-Line Memory Module
Single In-Line Memory Module IV-246
Small Computer Standarq Interface IV-251,
285
socket IV-229
sound buffer IV-247
sound generator IV-247
StackSpace function IV-78
Standard File Package IV-71
status phase IV-286
subdirectory IV-89
synchronous execution, File Manager IV-115

<!-- source-page: 331 -->
## Page 331

SysFontFam global variable IV-31
SysFontSiz global variable IV-31
System Error Handler IV-231
System file N-255
system font IV-31
system font size IV-31
System Resource File IV-255
system startup
environment IV-256
infonnation N-160, 164
system traps IV-305
T
tagbyte IV-223
target device N-285
TEAutoView procedure IV-57
TEPinScroll procedure IV-57
TESelView procedure N-57
TextEdit IV-57
routines IV-57
1FSTagData N-223
thread record N-173
Time Manager IV-297
routines N-300
TmpResLoad global variable N-19
TMTask data type N-299
Toolbox Utilities N-63
routines IV-63
track cache IV-224
TrackBox function IV-50
transfer instruction block IV-287
trap dispatch table N-13
trap macro list IV-305
trap number IV-13
trap word IV-13
TrapType data type N-233
u
Unique lID function IV-16
unit number IV-215
unit table IV-215
UnlockRng function IV-139
unmounted volume IV-92
UnmountVol function
high-level IV-108
low-level IV-134
UpdtControl procedure IV-53
UpdtDialog procedure IV-60
user interface guidelines 1-23
Utilities, Operating System IV-233
routines IV-233
Utilities, Toolbox IV-63
routines N-63
v
valence of a directory N-91
VCB data type IV-176
VCBQHdr global variable IV-178
version number of a file IV-90
video interface IV-247
volume (on a disk) IV-89
volume allocation block map IV-162
volume attributes N-162
volume biunap IV-167
volume buffer IV-92
volume control block N-92, 176
volume-control-block queue IV-176
volume infonnation IV-161, 166
volume infonnation block IV-165
volume name N-90
volume reference number N-93, 98
w
WDPBPtr data type IV-117
WDPBRec data type IV-127
WidthListHand global variable N-42
WidthPtr global variable IV-42
WidthTabHandle global variable IV-42
WidthTable data type IV-41
window
standard state N-7
user state IV-8
zooming IV-7, 49
window definition function IV-49
Window Manager N-49
routines N-50
worldng directory N-98
Index
working directory control block IV-98
worldng directory reference number N-98
Write function
high-level N-110
low-level N-140
WStateData data type N-49
Index IV-325
I

<!-- source-page: 332 -->
## Page 332

Inside Macintosh
X,Y
X2Fix function IV-65
X2Frac function IV-65
IV-326 Index
z
zoom window box IV-8
ZoomWindowprocedure IV-50

<!-- source-page: 333 -->
## Page 333

Inside Macintosh
Welcome to the world of programming for the Macintosh®. No other personal computer has been as
enthusiastically received by the programming community, as the large-and growing-body of Macintosh
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
• Technical Support: Apple's Developer Technical Support Group offers fast answers by way of
AppleLink® or MCI electronic mail.
• Macintosh Technical Notes: This is a bimonthly package of supplemental technical information.
• AppleLink: Through this electronic service, you can get answers to your technical questions and
current information on Apple and third-party products and programs.
•Certified Developer Mailings: These monthly mailings keep you informed about Apple's
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
20525 Mariani Avenue, MIS 51-W
Cupertino, CA 95014
The Apple Programmer's and Developer's Association, APDA TM, provides technical documentation and
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

<!-- source-page: 334 -->
## Page 334

@
Apple® Inside Macintosh
> $24· 95 FPT
USA
Tbe Official
Publication from
Apple Computer, Inc.
VolumeN
Inside Macintosh, Volume N, is a companion to the first three volumes of Inside Macintosh and
describes the features of the Macintosh® Plus and Macintosh 512K Enhanced computers.
Written by the people at Apple Computer, Inside Macintosh is the definitive source of information
for programmers writing application programs, desk accessories, device drivers, and other
software for any of the computers in the Apple Macintosh family. It includes:
• Guidelines for designing a user interface that conforms to the Macintosh standard.
• Descriptions of more than 1,200 ROM- and disk-based routines.
• A description of the Macintosh hardware.
Inside Macintosh is your guide to ,creating software for the Macintosh. It describes the Pascal
interfaces to the routines and, wherever applicable, gives special information for programming in
assembly language. (If you're using a high-level language other than Pascal, your development
system documentation should tell you how to apply the information in Inside Macintosh.)A typical
chapter describes a related set of routines, such as the Window Manager, and provides key concepts
and background information, hints on which routines you need to learn about and how they fit into
your program, and a detailed description of each routine.
Inside Macintosh consists of six volumes. This volume, Volume IY, contains descriptions of hundreds
of changes and additions to the original set of programming tools, including:
• An in-depth discussion of the Hierarchical File System.
• Details on the interface to the Small Computer Standard Interface (SCSI) port.
• Information on disk I/O for the SOOK disk drive and the Hard Disk 20.
• A description of the Macintosh Plus and Macintosh 512K Enhanced hardware.
Volume I contains important introductory material and describes the QuickDraw graphics package
and important Managers such as the Resource, Font, and Menu Managers. Volume II complements
Volume I in describing the Managers that perform such basic routines as file and device I/O,
memory management, and interrupt handling. Volume III discusses your program's interface with
the Finder·~ describes the Macintosh 128K and 512K computers, and provides summaries of the
software described in volumes I through III. Volume V discusses the changes introduced by the
Macintosh SE and II computers, including color, NuBus'" slots, and the Apple Desktop Bus·~ Inside
Macintosh X-Ref provides a single index to Inside Macintosh and other Macintosh technical books.
About the cover: This design represents a new look for the original edition of Inside Macintosh,
Volume N, and the other books in the Apple Technical Library. The contents have not been changed.
Apple Computer, Inc.
· 20525 Mariani Avenue
Cupertino, CA 95014
( 408) 9%-1010
TIX 171-576
Addison-Wesley Publishing Company, Inc.
Printed in USA.
52495
9 780201 054095
ISBN 0-201-05409-4
