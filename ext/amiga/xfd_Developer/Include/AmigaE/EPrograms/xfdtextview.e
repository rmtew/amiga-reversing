/*

    Note: It seems that the scrollwin-module (class/sctext.m) is broken
          since E v3.3. All programs that use this module crash at the
          scrolltext.open()-call. I don't know why and there is nothing
          I can do to avoid this.
          I have included the old modules in EModules/class. So just
          copy sc.m and sctext.m to your module directory.

*/

/* show a textfile in a nice juicy scrolling window
** NEW from DII: XFD support added 12/4/96
**
** Modified to work with v38 xfdmaster-includes and added asl-support
** on 05.11.98 by Sven Steiniger.
*/

OPT PREPROCESS
OPT REG=5
OPT OSVERSION=36  -> For Asl.library, OpenLibrary, etc.

MODULE 'exec/memory',
       'asl','libraries/asl',
       'xfdmaster','libraries/xfdmaster',
       'utility/tagitem'
MODULE 'tools/file',
       'class/sctext'

RAISE "ASL"  IF AllocAslRequest()=NIL,
      "MEM"  IF XfdAllocObject()=NIL,
      "xfd"  IF XfdDecrunchBuffer()=FALSE


DEF bufferinfo=NIL:PTR TO xfdBufferInfo


PROC main() HANDLE
DEF aslreq=NIL:PTR TO filerequester,
    filename[256]:STRING,
    error[5]:ARRAY OF CHAR

  /* Open libraries.
  */
  IF (aslbase:=OpenLibrary(ASLNAME,36))=NIL THEN
    Throw("LIB",ASLNAME)
  IF (xfdmasterbase:=OpenLibrary(XFDM_NAME,XFDM_VERSION))=NIL THEN
    Throw("LIB",XFDM_NAME)

  /* Allocate resources.
  */
  StrCopy(filename, arg)
  bufferinfo:=XfdAllocObject(XFDOBJ_BUFFERINFO)
  aslreq:=AllocAslRequest(ASL_FILEREQUEST,
                          [ASLFR_INITIALFILE, filename,
                           TAG_DONE,0])

  IF FileLength(filename)<=0
    /* File doesn't exists, so open an asl-requester
    */
    IF AslRequest(aslreq,NIL)
      StrCopy(filename,aslreq.drawer)
      AddPart(filename,aslreq.file,StrMax(filename))
      SetStr(filename,StrLen(filename))
    ENDIF
  ENDIF

  /* now display the file contents
  */
  displayFile(filename)


EXCEPT DO

  /* Free resources
  */
  IF aslreq THEN FreeAslRequest(aslreq)
  IF bufferinfo THEN XfdFreeObject(bufferinfo)

  /* Close libraries
  */
  CloseLibrary(xfdmasterbase)
  CloseLibrary(aslbase)

  /* Print an error-description (if necessary)
  */
  IF exception

    error[4]:=0
    ^error:=exception
    WHILE error[]=0 DO error++

    WriteF('Error: ')
    SELECT exception
      CASE "MEM"  ; WriteF('Not enough memeory\n')
      CASE "OPEN" ; WriteF('Could not open file \s\n',exceptioninfo)
      CASE "LIB"  ; WriteF('Could not open \s\n',exceptioninfo)
      DEFAULT     ; WriteF('"\s": \s\n',error, IF exceptioninfo>1000 THEN exceptioninfo ELSE '??')
    ENDSELECT
  ENDIF

ENDPROC


/* Loads an displays an file
*/
PROC displayFile(name) HANDLE
DEF mem=NIL:PTR TO CHAR,
    length,
    listi=NIL:PTR TO LONG,
    cruncher:PTR TO CHAR
DEF title[60]:STRING,
    max_linelen=0,
    text,
    sc=NIL:PTR TO scrolltext


  /* Load file and make the contents an linked list of strings.
  */
  mem,length,cruncher:=readXFDTextFile(name)
  listi:=stringsinfile(mem,length,countstrings(mem,length))

  /* Find the maximum line length.
  */
  ForAll({text},listi,`(max_linelen:=Max(StrLen(text),max_linelen)))

  /* Now display the text.
  */
  StringF(title,'TextView 2.0 (\s)',cruncher)
  NEW sc.settext(listi,max_linelen)
  sc.open(title,20,20,300,150)

  /* Wait until window quits.
  */
  WHILE sc.handle()=FALSE DO Wait(-1)

EXCEPT DO

  END sc

  IF listi THEN DisposeLink(listi)
  freeXFDTextFile(mem)

  ReThrow()

ENDPROC


/* Reads an file and decrunchs it if necessary.
*/
PROC readXFDTextFile(name:PTR TO CHAR) HANDLE
DEF mem=NIL:PTR TO CHAR,
    length,
    cruncher

  mem,length:=readfile(name)
  cruncher:='ASCII'

  bufferinfo.xfdbi_SourceBuffer:=mem
  bufferinfo.xfdbi_SourceBufLen:=length
  bufferinfo.xfdbi_Flags       :=0

  IF XfdRecogBuffer(bufferinfo)

    IF bufferinfo.xfdbi_PackerFlags AND (XFDPFF_PASSWORD OR XFDPFF_KEY16 OR XFDPFF_KEY32)
      Throw("p/k", 'Password required.')
    ENDIF

    bufferinfo.xfdbi_TargetBufMemType:=MEMF_PUBLIC
    XfdDecrunchBuffer(bufferinfo)

    freefile(mem)

    mem      := bufferinfo.xfdbi_TargetBuffer
    cruncher := bufferinfo.xfdbi_PackerName

    /* Last element must be an '\n'. readfile() does this automatical
    ** but with xfd we must do it here. Problem: if decrunchbuffer is
    ** too small then the last character is lost.
    */
    length   := Min(bufferinfo.xfdbi_TargetBufSaveLen+1, bufferinfo.xfdbi_TargetBufLen)
    mem[length-1]:="\n"

  ENDIF

EXCEPT

  IF mem THEN freefile(mem)
  ReThrow()

ENDPROC mem,length,cruncher


/* Frees resources which are allocated by readXFDFile().
*/
PROC freeXFDTextFile(mem)

  IF mem
    IF mem=bufferinfo.xfdbi_TargetBuffer
      FreeMem(mem,bufferinfo.xfdbi_TargetBufLen)
      bufferinfo.xfdbi_TargetBuffer:=NIL
    ELSE
      freefile(mem)
    ENDIF
  ENDIF

ENDPROC


