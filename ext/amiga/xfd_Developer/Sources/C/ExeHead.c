/* Objectheader

	Name:		ExeHead.c
	Version:	$VER: ExeHead.c 1.5 (22.02.1999)
	Description:	Exe C header for xfd externals testing
	Author:		SDI
	Distribution:	PD

 1.0   22.12.97 : first version
 1.1   04.06.98 : little bugfix
 1.2   04.08.98 : added SysBase
 1.3   31.10.98 : SysBase passed to client in pseudo-master-base
 1.4   07.12.98 : added error output
 1.5   22.02.99 : added V39 auto allocation feature
*/

#include <proto/dos.h>
#include <proto/exec.h>
#include <libraries/xfdmaster.h>
#include <exec/memory.h>

#ifdef __MAXON__
  #define __asm
#endif

#define PARAM "FROM/A,TO"

typedef BOOL __asm (*RecogFunc) (register __a0 STRPTR,
	 register __d0 ULONG, register __a1 struct xfdRecogResult *);
typedef BOOL __asm (*DecrunchFunc) (register __a0 struct xfdBufferInfo *,
register __a6 struct xfdMasterBase *);

struct DosLibrary *DOSBase = 0;
struct ExecBase   *SysBase = 0;
extern struct xfdSlave FirstSlave;

/* NOTE: The methods used in this program do not cover all the
   xfdmaster.library methods, so this file is no replace for xfdmaster.
   It is for tests only! */

LONG main(void)
{
  STRPTR args[2];
  LONG ret = RETURN_FAIL;
  struct RDArgs *rda;

  SysBase = (*((struct ExecBase **) 4));

  if(!(DOSBase = (struct DosLibrary *) OpenLibrary("dos.library", 37)))
    return ret;

  args[1] = 0;

  if((rda = ReadArgs(PARAM, (LONG *) &args, 0)))
  {
    ULONG fh;

    if((fh = Open(args[0], MODE_OLDFILE)))
    {
      struct FileInfoBlock *fib;

      if((fib = (struct FileInfoBlock *) AllocDosObject(DOS_FIB, 0)))
      {
        if((ExamineFH(fh, fib)))
        {
	  ULONG insize;
	  STRPTR inbuf;

          insize = fib->fib_Size;
          if((inbuf = (STRPTR) AllocMem(insize, MEMF_ANY)))
          {
            if(Read(fh, inbuf, insize) == insize)
            {
              struct xfdSlave *slave = &FirstSlave;
              struct xfdRecogResult rr;
              ret = 0;

	      while(slave)
	      {
		if(slave->xfds_MinBufferSize <= insize &&
		((RecogFunc)slave->xfds_RecogBuffer)(inbuf, insize, &rr))
		{
		  /* We do use xfdBufferInfo only local, so it is ok not
		     to get it with xfdmaster functions. */
		  struct xfdBufferInfo xbi;
		  struct xfdMasterBase xb;

		  /* We set only these fields, which are accessed by the
		     slaves. When test slaves access more than these fields,
		     we need to init these new fields as well!!! */
		  xbi.xfdbi_SourceBuffer = inbuf;
		  xbi.xfdbi_SourceBufLen = insize;
		  xbi.xfdbi_TargetBufMemType = MEMF_ANY;
		  xbi.xfdbi_Error = 0;
		  xbi.xfdbi_Flags = 0;
		  xb.xfdm_ExecBase = SysBase;

		  Printf("Type is '%s'\n", slave->xfds_PackerName);

		  /* V39 feature of minimum sourcelen check is not supplied! */

		  if((slave->xfds_PackerFlags & XFDPFF_USERTARGET) &&
		  rr.xfdrr_MinTargetLen != -1)
		  {
		    if((xbi.xfdbi_UserTargetBuf = AllocMem(rr.xfdrr_MinTargetLen, MEMF_ANY)))
		    {
		      xbi.xfdbi_Flags |= XFDFF_MASTERALLOC|XFDPFF_USERTARGET;
		      xbi.xfdbi_UserTargetBufLen = 
		      xbi.xfdbi_TargetBufLen = rr.xfdrr_MinTargetLen;
		      xbi.xfdbi_TargetBufSaveLen = rr.xfdrr_FinalTargetLen;
		      xbi.xfdbi_TargetBuffer = xbi.xfdbi_UserTargetBuf;
		    }
		    else
		      ret = XFDERR_NOMEMORY;
		  }

		  if(!ret)
		  {
		    if(((DecrunchFunc) slave->xfds_DecrunchBuffer)(&xbi, &xb))
		    {
		      if(args[1])
		      {
		        ULONG destfh;

	                if((destfh = Open(args[1], MODE_NEWFILE)))
	                {
	                  if(Write(destfh, xbi.xfdbi_TargetBuffer,
	                  xbi.xfdbi_TargetBufSaveLen) != xbi.xfdbi_TargetBufSaveLen)
	                    ret = RETURN_ERROR;
	                  Close(destfh);
	                }
	                else
	                  ret = RETURN_ERROR;
	              }
	              FreeMem(xbi.xfdbi_TargetBuffer, xbi.xfdbi_TargetBufLen);
		    }
		    else
		    {
		      if(xbi.xfdbi_Flags & XFDFF_MASTERALLOC)
		        FreeMem(xbi.xfdbi_UserTargetBuf, xbi.xfdbi_UserTargetBufLen);
	              ret = -xbi.xfdbi_Error;
	              Printf("Error %ld\n", xbi.xfdbi_Error);
	            }
	          }
	          slave = 0;
		} /* RecogFunc */
		else
		  slave = slave->xfds_Next;
	      } /* while */
	    } /* Read */
            FreeMem(inbuf, insize);
          } /* AllocMem(inbuf, insize) */
        } /* Examine */
        FreeDosObject(DOS_FIB, fib);
      } /* AllocDosObject */
      Close(fh);
    } /* Open */
    FreeArgs(rda);
  } /* ReadArgs */

  CloseLibrary((struct Library *) DOSBase);

  return ret;
}
