(*
(* Copyright © 1994 by Georg Hörmann
** All Rights Reserved
**
** Amiga Oberon Interface Module:
** $VER: XFDmaster.mod 34.1 (14.05.95)
** converted from orginal includes by Bert Jahn
** Copyright © 1995 by Bert Jahn
**
** Only the for "lib-using" needed types & constants are exported
** if you want to write a sublib (make this sense in Oberon ??) you have to
** change this file and export all you need
**
** 02.03.95 initial
** 14.05.95 new type "SpecialPtr" (bj)
*)
*)

MODULE XFDmaster;

IMPORT
  e * := Exec;

CONST
  xfdmasterName  * = "xfdmaster.library";
  includeVersion * = 34;
  maxSpecialLen  * = 18;

TYPE
  BufferInfoPtr    * = UNTRACED POINTER TO BufferInfo;
  SegmentInfoPtr   * = UNTRACED POINTER TO SegmentInfo;
  ForemanPtr         = UNTRACED POINTER TO Foreman;
  SlavePtr           = UNTRACED POINTER TO Slave;
  XFDmasterBasePtr   = UNTRACED POINTER TO XFDmasterBase;
  SpecialPtr       * = UNTRACED POINTER TO ARRAY maxSpecialLen OF CHAR;

(* Buffer Info *)
TYPE
  BufferInfo * = STRUCT
    sourceBuffer      * : e.APTR;
    sourceBufLen      * : e.ULONG;
    slave               : SlavePtr;
    packerName        - : e.LSTRPTR;
    packerFlags       - : SET;
    error             - : e.UWORD;
    targetBuffer      - : e.APTR;
    targetBufMemType  * : LONGSET;
    targetBufLen      - : e.ULONG;
    targetBufSaveLen  - : e.ULONG;
    decrAddress       - : e.ULONG;
    jmpAddress        - : e.ULONG;
    special           * : SpecialPtr;
  END;

(* Segment Info *)
TYPE
  SegmentInfo * = STRUCT
    segList     * : e.BPTR;
    slave         : SlavePtr;
    packerName  - : e.LSTRPTR;
    packerFlags - : SET;
    error       - : e.UWORD;
    special     * : SpecialPtr;
    relMode     * : e.UWORD;
    reserved0     : e.UWORD;
  END;

(* Error Codes *)
CONST
  errOk               * = 0;
  errNoMemory         * = 1;
  errNoSlave          * = 2;
  errNotSupported     * = 3;
  errUnknown          * = 4;
  errNoSource         * = 5;
  errWrongPassword    * = 6;
  errBadHunk          * = 7;
  errCorruptedData    * = 8;
  errMissingResource  * = 9;
  errUndefiniedHunk   * = 1000H;
  errNoHunkHeader     * = 1001H;
  errBadExtType       * = 1002H;
  errBufferTruncated  * = 1003H;
  errWrongHunkAmount  * = 1004H;
  errUnsupportedHunk  * = 2000H;
  errBadRelMode       * = 2001H;

(* Relocation Modes *)
CONST
  relDefault   * = 0;
  relForceChip * = 1;
  relForceFast * = 2;

(* Packer Flags *)
CONST
  reloc    * = 0;
  addr     * = 1;
  data     * = 2;
  password * = 4;
  relmode  * = 5;

(* Forman *)
TYPE
  Foreman = STRUCT
    security   : e.ULONG;
    id         : e.ULONG;
    version    : e.UWORD;
    reserved   : e.UWORD;
    next       : ForemanPtr;
    segList    : e.BPTR;
    firstSlave : SlavePtr;
  END;
CONST
  id       = 58464446H;
  fVersion = 1;

(* Slave *)
TYPE
  Slave = STRUCT
    next            : SlavePtr;
    version         : e.UWORD;
    masterVersion   : e.UWORD;
    packerName      : e.LSTRPTR;
    maxSpecialLen   : e.UWORD;
    recogBuffer     : e.PROC;
    decrunchBuffer  : e.PROC;
    recogSegment    : e.PROC;
    decrunchSegment : e.PROC;
  END;
CONST
  sVersion = 1;

(* Library Base *)
TYPE
  XFDmasterBase = STRUCT (libNode : e.Library)
    segList      : e.BPTR;
    dosBase      : e.LibraryPtr;
    firstSlave   : SlavePtr;
    firstForeman : ForemanPtr;
  END;


(* $StackChk- $RangeChk- $NilChk- $OvflChk- $ReturnChk- $CaseChk- *)

VAR
  base - : XFDmasterBasePtr;

PROCEDURE AllocBufferInfo      *{base,-30}()                                 : BufferInfoPtr;
PROCEDURE FreeBufferInfo       *{base,-36}(bufferinfo  {9}: BufferInfoPtr);
PROCEDURE AllocSegmentInfo     *{base,-42}()                                 : SegmentInfoPtr;
PROCEDURE FreeSegmentInfo      *{base,-48}(segmentinfo {9}: SegmentInfoPtr);
PROCEDURE RecogBuffer          *{base,-54}(bufferinfo  {8}: BufferInfoPtr)   : BOOLEAN;
PROCEDURE DecrunchBuffer       *{base,-60}(bufferinfo  {8}: BufferInfoPtr)   : BOOLEAN;
PROCEDURE RecogSegment         *{base,-66}(segmentinfo {8}: SegmentInfoPtr)  : BOOLEAN;
PROCEDURE DecrunchSegment      *{base,-72}(segmentinfo {8}: SegmentInfoPtr)  : BOOLEAN;
PROCEDURE GetErrorText         *{base,-78}(error       {0}: e.UWORD)         : e.LSTRPTR;
PROCEDURE TestHunkStructure    *{base,-84}(length      {0}: e.ULONG;
                                           buffer      {8}: e.APTR)          : BOOLEAN;
PROCEDURE TestHunkStructureNew *{base,-90}(length      {0}: e.ULONG;
                                           buffer      {8}: e.APTR)          : e.UWORD;
PROCEDURE Relocate             *{base,-96}(length      {0}: e.ULONG;
                                           mode        {1}: e.UWORD;
                                           buffer      {8}: e.APTR;
                                           VAR result  {9}: e.BPTR)          : e.UWORD;

BEGIN
  base := e.OpenLibrary(xfdmasterName,includeVersion);
CLOSE
  IF base # NIL THEN e.CloseLibrary(base); END;
END XFDmaster.

