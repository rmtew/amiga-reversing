unsigned char version[] = "$VER: UNIX-Compress 1.2 (04.08.1998) by SDI";

/* Objectheader

	Name:		UNIX-Compress.c
	Description:	xfd external decruncher for UNIX compress files
	Author:		SDI (stoecker@epost.de)
	Distribution:	PD

 1.0   22.12.97 : first version
 1.1   23.12.97 : added memory expansion
 1.2   04.08.98 : bug fix for block compress, added internal SysBase
*/

/* Because there is no way to find out the size of uncrunched file, this
   routine uses a destination buffer, which is 4 times as large as the
   source file. When there is not enough memory, the largest memory block
   is used.
   This does surely not cover all Compress files! So there may be some
   which cannot be decrunched. XPKERR_CORRUPTEDDATA should be reported for
   these. In this case the program tries to allocate the largest available
   memory block and restarts decrunching.

   Has anyone a better idea how to find out destination length?
*/

#include <libraries/xfdmaster.h>
#include <proto/exec.h>
#include <exec/memory.h>
#include "SDI_compiler.h"

#define MAXCODE(n)	(((ULONG) 1 << (n)) - 1)

#define BITS		   16
#define STACKSIZE	 8000
#define FIRST		  257		/* first free entry */
#define CLEAR		  256		/* table clear output code */
#define INIT_BITS	    9		/* initial number of bits/code */

/* Defines for third byte of header */
#define BIT_MASK	0x1f
#define BLOCK_MASK	0x80
#define LZW_RESERVED	0x60
	/* Masks 0x40 and 0x20 are free. I think 0x20 should mean that
	   there is a fourth header byte (for expansion). */

static UBYTE rmask[9] = {0x00, 0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7f, 0xff};

struct CompressData {
  UWORD  	block_compress;
  WORD		clear_flg;
  UWORD		n_bits;			/* number of bits/code */
  UWORD  	maxbits;		/* user settable max # bits/code */
  ULONG 	maxcode;		/* maximum code, given n_bits */
  ULONG 	maxmaxcode;
  LONG 		free_ent;
  LONG		offset;
  LONG		size;
  STRPTR	inptr;			/* current input pointer */
  STRPTR	inendptr;		/* end of input buffer */
  UWORD *	tab_prefixof;
  STRPTR 	tab_suffixof;
  STRPTR 	stack;
  UBYTE		buf[BITS];
};

/************** Here starts xfd stuff - the xfdSlave structure **********/

#define MASTER_VERS	36

typedef BOOL (*xfdFunc) ();

ASM(LONG) RecogCompress(REG(a0, STRPTR buf), REG(d0, ULONG length));
ASM(BOOL) DecrunchCompress(REG(a0, struct xfdBufferInfo * xbi),
 REG(a6, struct xfdMasterBase *xfdMasterBase));
static LONG decomp(struct CompressData *, STRPTR, ULONG, STRPTR, ULONG);
static LONG getcode(struct CompressData *);

struct xfdSlave FirstSlave = {
  0, XFDS_VERSION, MASTER_VERS, "UNIX Compress", XFDPFF_DATA, 0, 
  (xfdFunc) RecogCompress, (xfdFunc) DecrunchCompress, 0, 0, 0, 0, 4};

ASM(LONG) RecogCompress(REG(a0, STRPTR buf), REG(d0, ULONG length))
{
  if(*((UWORD *)buf) == 0x1F9D)
  {
    UBYTE mb = buf[2];
    if(mb & LZW_RESERVED)		/* Unknown format */
      return 0;
    if((mb & BIT_MASK) > BITS)		/* Too much bits */
      return 0;
    return 1;	/* Now should be a correct file */
  }
  return 0;
}

ASM(BOOL) DecrunchCompress(REG(a0, struct xfdBufferInfo * xbi),
REG(a6, struct xfdMasterBase *xfdMasterBase))
{
  struct CompressData cd;
  LONG ret = -XFDERR_NOMEMORY;
  ULONG maxmaxcode = 1<<((((STRPTR)xbi->xfdbi_SourceBuffer)[2])&BIT_MASK);
  struct ExecBase *SysBase;

  SysBase = xfdMasterBase->xfdm_ExecBase;

  if((cd.tab_prefixof = (UWORD *) AllocMem(sizeof(UWORD)*maxmaxcode, MEMF_ANY)))
  {
    if((cd.stack = (STRPTR) AllocMem(STACKSIZE, MEMF_ANY)))
    {
      if((cd.tab_suffixof = (STRPTR) AllocMem(maxmaxcode, MEMF_ANY)))
      {
        ULONG bufsize;

	bufsize = AvailMem(MEMF_LARGEST|xbi->xfdbi_TargetBufMemType);

        if((xbi->xfdbi_TargetBufLen = xbi->xfdbi_SourceBufLen<<2) > bufsize)
          xbi->xfdbi_TargetBufLen = bufsize;

        if((xbi->xfdbi_TargetBuffer = AllocMem(xbi->xfdbi_TargetBufLen,
        xbi->xfdbi_TargetBufMemType)))
        {
          if((ret = decomp(&cd, (STRPTR) xbi->xfdbi_SourceBuffer,
          xbi->xfdbi_SourceBufLen, (STRPTR) xbi->xfdbi_TargetBuffer,
          xbi->xfdbi_TargetBufLen)) > 0)
            xbi->xfdbi_TargetBufSaveLen = ret;
          else
          {
            FreeMem(xbi->xfdbi_TargetBuffer, xbi->xfdbi_TargetBufLen);
            if(bufsize != xbi->xfdbi_TargetBufLen)
            {
	      /* expand memory to full available and retry */
              xbi->xfdbi_TargetBufLen = AvailMem(MEMF_LARGEST|xbi->xfdbi_TargetBufMemType);
              if((xbi->xfdbi_TargetBuffer = AllocMem(xbi->xfdbi_TargetBufLen,
              xbi->xfdbi_TargetBufMemType)))
              {
                if((ret = decomp(&cd, (STRPTR) xbi->xfdbi_SourceBuffer,
                xbi->xfdbi_SourceBufLen, (STRPTR) xbi->xfdbi_TargetBuffer,
                xbi->xfdbi_TargetBufLen)) > 0)
                  xbi->xfdbi_TargetBufSaveLen = ret;
                else
                  FreeMem(xbi->xfdbi_TargetBuffer, xbi->xfdbi_TargetBufLen);
              }
            }
          }
        }

        FreeMem(cd.tab_suffixof, maxmaxcode);
      }
      FreeMem(cd.stack, STACKSIZE);
    }
    FreeMem(cd.tab_prefixof, sizeof(UWORD)*maxmaxcode);
  }

  if(ret <= 0)
  {
    xbi->xfdbi_TargetBufLen = xbi->xfdbi_TargetBufSaveLen = 0;
    xbi->xfdbi_TargetBuffer = 0;
    xbi->xfdbi_Error = -ret;
    return 0;
  }

  return (BOOL) ret;
}

/* Decompress. This routine adapts to the codes in the file building the
 * "string" table on-the-fly; requiring no table to be stored in the
 * compressed file.
 */

/* negative values are error codes, positive value is resulting size */
static LONG decomp(struct CompressData *cd, STRPTR inbuf, ULONG insize,
STRPTR outbuf, ULONG outsize)
{
  LONG finchar, code, oldcode, incode, blockcomp;
  STRPTR outptr = outbuf, stackp = cd->stack,
  stack = cd->stack, outend = outbuf+outsize;

  cd->maxbits = inbuf[2];
  blockcomp = cd->block_compress = cd->maxbits & BLOCK_MASK;
  cd->maxbits &= BIT_MASK;
  cd->maxmaxcode = 1 << cd->maxbits;
  cd->maxcode = MAXCODE(cd->n_bits = INIT_BITS);
  cd->free_ent = ((cd->block_compress) ? FIRST : 256);
  cd->clear_flg = cd->offset = cd->size = 0;
  cd->inptr = inbuf+3;
  cd->inendptr = inbuf+insize;

  /* Initialize the first 256 entries in the table. */
  for(code = 255; code >= 0; code--)
  {
    cd->tab_prefixof[code] = 0;
    cd->tab_suffixof[code] = (UBYTE) code;
  }

  if((finchar = oldcode = getcode(cd)) == -1)	/* EOF already ? */
    return -XFDERR_CORRUPTEDDATA;		/* Get out of here */
  *(outptr++) = (UBYTE) finchar; /* first code must be 8 bits = UBYTE */

  while((code = getcode(cd)) > -1)
  {
    if((code == CLEAR) && blockcomp)
    {
      for(code = 255; code >= 0; code--)
	cd->tab_prefixof[code] = 0;
      cd->clear_flg = 1;
      cd->free_ent = FIRST - 1;
      if((code = getcode(cd)) == -1)
	break;					/* O, untimely death! */
    }
    incode = code;

    /* Special case for KwKwK string. */
    if(code >= cd->free_ent)
    {
      *stackp++ = finchar;
      code = oldcode;
    }

    /* Generate output characters in reverse order */
    while(code >= 256)
    {
      *stackp++ = cd->tab_suffixof[code];
      code = cd->tab_prefixof[code];
    }
    *stackp++ = finchar = cd->tab_suffixof[code];

    if(stackp - stack > outend - outptr) /* buffer was to short :-( */
      return -XFDERR_CORRUPTEDDATA;

    /* And put them out in forward order */
    do
    {
      *(outptr++) = *(--stackp);
    } while(stackp > stack);

    /* Generate the new entry. */
    if((code = cd->free_ent) < cd->maxmaxcode)
    {
      cd->tab_prefixof[code] = (UWORD) oldcode;
      cd->tab_suffixof[code] = finchar;
      cd->free_ent = code+1;
    }
    /* Remember previous code. */
    oldcode = incode;
  }
  return (outptr-outbuf);
}

/* Read one code from input. If EOF, return -1. */
static LONG getcode(struct CompressData *cd)
{
  LONG code, r_off, bits;
  UBYTE *bp = cd->buf;

  if(cd->clear_flg > 0 || cd->offset >= cd->size || cd->free_ent > cd->maxcode)
  {
    /*
     * If the next entry will be too big for the current code
     * size, then we must increase the size.  This implies reading
     * a new buffer full, too.
     */
    if(cd->free_ent > cd->maxcode)
    {
      if(++cd->n_bits == cd->maxbits)
	cd->maxcode = cd->maxmaxcode;	/* won't get any bigger now */
      else
	cd->maxcode = MAXCODE(cd->n_bits);
    }
    if(cd->clear_flg > 0)
    {
      cd->maxcode = MAXCODE(cd->n_bits = INIT_BITS);
      cd->clear_flg = 0;
    }

    if(cd->inendptr <= cd->inptr)
      return -1;			/* end of file */

    /* This reads maximum n_bits characters into buf */
    cd->size = 0;
    while(cd->size < cd->n_bits && cd->inptr < cd->inendptr)
      cd->buf[cd->size++] = *(cd->inptr++);

    cd->offset = 0;
    /* Round size down to integral number of codes */
    cd->size = (cd->size << 3) - (cd->n_bits - 1);
  }
  r_off = cd->offset;
  bits = cd->n_bits;

  /* Get to the first byte. */
  bp += (r_off >> 3);
  r_off &= 7;

  /* Get first part (low order bits) */
  code = (*bp++ >> r_off);
  bits -= (8 - r_off);
  r_off = 8 - r_off;			/* now, offset into code word */

  /* Get any 8 bit parts in the middle (<=1 for up to 16 bits). */
  if(bits >= 8)
  {
    code |= *bp++ << r_off;
    r_off += 8;
    bits -= 8;
  }

  /* high order bits. */
  code |= (*bp & rmask[bits]) << r_off;
  cd->offset += cd->n_bits;

  return code;
}

