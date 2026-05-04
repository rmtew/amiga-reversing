If you need additionally include files, use fd2pragma utility. It can be
found in Aminet under name dev/misc/fd2pragma.lha.

It is able to produce stub libraries, lvo, proto and pragma files and a lot
of other stuff.

The inline files in directory inline will work with GCC and VBCC.
The pragma files will work with SAS, Maxon, Storm, Dice and Aztec compiler.
The proto files will work with all of these compilers!

Most of these files were automatically created with fd2pragma (2.139 or
better):
fd2pragma SPECIAL   6 INFILE SFD/xfdmaster_lib.sfd TO C/pragma
fd2pragma SPECIAL  18 INFILE SFD/xfdmaster_lib.sfd TO AmigaE/EModules/
fd2pragma SPECIAL  40 INFILE SFD/xfdmaster_lib.sfd TO C/inline
fd2pragma SPECIAL  38 INFILE SFD/xfdmaster_lib.sfd TO C/proto
fd2pragma SPECIAL  70 INFILE SFD/xfdmaster_lib.sfd TO C/inline
fd2pragma SPECIAL  23 INFILE SFD/xfdmaster_lib.sfd TO ASM/lvo
fd2pragma SPECIAL 110 INFILE SFD/xfdmaster_lib.sfd TO FD COMMENT
fd2pragma SPECIAL 111 INFILE SFD/xfdmaster_lib.sfd TO C/clib COMMENT COPYRIGHT "Dirk Stöcker and Georg Hörmann"

For GCC you may delete the pragma directory.
For all the other C compilers you may delete the inline directory,
but use pragma instead. Do not rename pragma to pragmas or change
the file names! When pragma does not exist, please create it.

Always call files in proto directory instead of clib, inline or pragma
directory! This makes usage of different compilers possible.

You need not to modify any of the include files or change their names!


Dirk Stöcker <stoecker@epost.de>

7th August 2002

