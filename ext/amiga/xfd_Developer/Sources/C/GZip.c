unsigned char version[] = "$VER: GZip 1.2 (22.02.1999) by SDI";

/* Objectheader

	Name:		GZip.c
	Description:	xfd external decruncher for GZip files
	Author: 	SDI (stoecker@epost.de)
	Distribution:	PD

 1.0   01.11.98 : first version
 1.1   07.12.98 : added buffer checking, reduced stack usage a lot
 1.2   22.02.99 : don't know why, but the return code was always true
*/

/* I made that client with files gzip.c, gzip.h, util.c, unzip.c and
   inflate.c of gzip source distribution. I changed the client to do
   mem to mem decrunching and generally made it an Amiga style source
   code (variable types, no global variables, AllocVec, ...). All
   the register variables got normal ones, as SAS should know better
   which variables should be in registers. The CRC table has been
   replaced by a CRC table calculation.
*/ 

#include <libraries/xfdmaster.h>
#include <proto/exec.h>
#include <exec/memory.h>
#include <exec/execbase.h>
#include "SDI_compiler.h"

/* gzip flag byte */
#define ASCII_FLAG   0x01 /* bit 0 set: file probably ascii text */
#define CONTINUATION 0x02 /* bit 1 set: continuation of multi-part gzip file */
#define EXTRA_FIELD  0x04 /* bit 2 set: extra field present */
#define ORIG_NAME    0x08 /* bit 3 set: original file name present */
#define COMMENT      0x10 /* bit 4 set: file comment present */
#define ENCRYPTED    0x20 /* bit 5 set: file is encrypted */
#define RESERVED     0xC0 /* bit 6,7:	reserved */

/* If BMAX needs to be larger than 16, then h and x[] should be ULONG. */
#define BMAX 16 	/* maximum bit length of any code (16 for explode) */
#define N_MAX 288	/* maximum number of codes in any set */

struct GZipData {
  struct ExecBase *	SysBase;
  UBYTE *		outbuf;
  UBYTE *		inbuf;
  ULONG 		outsize;
  ULONG 		insize;
  ULONG 		crc;
  ULONG 		XFDerr;

  ULONG 		outpos;
  ULONG 		inpos;
  ULONG 		bb;
  ULONG 		bk;

  ULONG			data1[320]; /* all functions */

  /* huft_build */
  ULONG			c[BMAX+1];		/* bit length count table */
  struct huft *		u[BMAX];		/* table stack */
  ULONG 		v[N_MAX];		/* values in order of bit length */
  ULONG 		x[BMAX+1];		/* bit offsets, then code stack */
};

#define BUFFEREXTEND	100

/************** Here starts xfd stuff - the xfdSlave structure **********/

#define MASTER_VERS	36

typedef BOOL (*xfdFunc) ();

ASM(LONG) RecogGZip(REG(a0, STRPTR buf), REG(d0, ULONG length));
ASM(BOOL) DecrunchGZip(REG(a0, struct xfdBufferInfo * xbi),
 REG(a6, struct xfdMasterBase *xfdMasterBase));
static BOOL decrunchZip(struct GZipData *);
static LONG huft_build(ULONG *, ULONG, ULONG, UWORD *, UWORD *,
 struct huft **, LONG *, struct GZipData *g);
static void huft_free(struct huft *, struct GZipData *g);
static LONG inflate_codes(struct huft *, struct huft *, LONG,
 LONG, struct GZipData *g);
static LONG inflate_stored(struct GZipData *g);
static LONG inflate_fixed(struct GZipData *g);
static LONG inflate_dynamic(struct GZipData *g);

struct xfdSlave FirstSlave = {
  0, XFDS_VERSION, MASTER_VERS, "GZip", XFDPFF_DATA, 0, 
  (xfdFunc) RecogGZip, (xfdFunc) DecrunchGZip, 0, 0, 0, 0, 4};

ASM(LONG) RecogGZip(REG(a0, STRPTR buf), REG(d0, ULONG length))
{
  return (*(buf++) == 0x1F && (*buf == 0x8B || *buf == 0x9E) && buf[1] == 8
  && !(buf[2] & (ENCRYPTED|CONTINUATION|RESERVED)));
}

ASM(BOOL) DecrunchGZip(REG(a0, struct xfdBufferInfo * xbi),
REG(a6, struct xfdMasterBase *xfdMasterBase))
{
  STRPTR inbuf, outbuf;
  ULONG flags, outsize;
  BOOL res = 0;
  struct ExecBase *SysBase;
  struct GZipData *g;

  SysBase = xfdMasterBase->xfdm_ExecBase;
  inbuf = (STRPTR) xbi->xfdbi_SourceBuffer;
  /* We need OS2.0 for AllocVec */
  if(SysBase->LibNode.lib_Version < 36)
  {
    xbi->xfdbi_Error = XFDERR_NOTSUPPORTED;
    return 0;
  }

  outsize = (*(inbuf + xbi->xfdbi_SourceBufLen-1)<<24) +
	    (*(inbuf + xbi->xfdbi_SourceBufLen-2)<<16) +
	    (*(inbuf + xbi->xfdbi_SourceBufLen-3)<<8)  +
	    *(inbuf + xbi->xfdbi_SourceBufLen-4) + BUFFEREXTEND;

  inbuf += 3;			/* skip header */
  flags = *(inbuf++);
  inbuf += 6;			/* skip time, extra flags, OS type */

  if(flags & EXTRA_FIELD)	/* skip extra field */
    inbuf += 2 + *inbuf + ((*(inbuf+1))<<8);

  if(flags & ORIG_NAME) 	/* skip file name */
  {
    while(*(inbuf++))
      ;
  }

  if(flags & COMMENT)
  {
    while(*(inbuf++))
      ;
  }

  if((g = (struct GZipData *) AllocMem(sizeof(struct GZipData), MEMF_CLEAR)))
  {
    g->XFDerr = XFDERR_NOMEMORY;

    if((outbuf = (STRPTR) AllocMem(outsize, xbi->xfdbi_TargetBufMemType)))
    {
      g->SysBase = SysBase;
      g->outbuf = outbuf;
      g->inbuf = inbuf;
      g->outsize = outsize;
      g->insize = xbi->xfdbi_SourceBufLen-(inbuf-
	       (STRPTR)xbi->xfdbi_SourceBuffer)-8;
      g->crc = (inbuf[g->insize+3]<<24)+(inbuf[g->insize+2]<<16)+
	    (inbuf[g->insize+1]<<8)+inbuf[g->insize];

      res = decrunchZip(g);

      if(res)
      {
        xbi->xfdbi_TargetBuffer = outbuf;
        xbi->xfdbi_TargetBufLen = outsize;
        xbi->xfdbi_TargetBufSaveLen = outsize - BUFFEREXTEND;
      }
      else
      {
        FreeMem(outbuf, outsize);
        xbi->xfdbi_Error = g->XFDerr;
      }
    }
    else
      xbi->xfdbi_Error = XFDERR_NOMEMORY;

    FreeMem(g, sizeof(struct GZipData));
  }
  else
    xbi->xfdbi_Error = XFDERR_NOMEMORY;

  return res;
}

#define SysBase g->SysBase

/* Huffman code lookup table entry--this entry is four bytes for machines
   that have 16-bit pointers (e.g. PC's in the small or medium model).
   Valid extra bits are 0..13.	e == 15 is EOB (end of block), e == 16
   means that v is a literal, 16 < e < 32 means that v is a pointer to
   the next table, which codes e - 16 bits, and lastly e == 99 indicates
   an unused code.  If a code with e == 99 is looked up, this implies an
   error in the data. */
struct huft {
  UBYTE e;		/* number of extra bits or operation */
  UBYTE b;		/* number of bits in this code or subcode */
  union {
    UWORD n;		/* literal, length base, or distance base */
    struct huft *t;	/* pointer to next level of table */
  } v;
};

/* Tables for deflate from PKZIP's appnote.txt. */
static ULONG border[] = {	/* Order of the bit length code lengths */
  16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15};
static UWORD cplens[] = {	/* Copy lengths for literal codes 257..285 */
  3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31,
  35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258, 0, 0};
static UWORD cplext[] = {	/* Extra bits for literal codes 257..285 */
  0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
  3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0, 99, 99}; /* 99==invalid */
static UWORD cpdist[] = {	/* Copy offsets for distance codes 0..29 */
  1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193,
  257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145,
  8193, 12289, 16385, 24577};
static UWORD cpdext[] = {	/* Extra bits for distance codes */
  0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
  7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13};

/* Macros for inflate() bit peeking and grabbing.
   The usage is:
   
	NEEDBITS(j)
	x = b & mask_bits[j];
	DUMPBITS(j)

   where NEEDBITS makes sure that b has at least j bits in it, and
   DUMPBITS removes the bits from b.  The macros use the variable k
   for the number of bits in b.  Normally, b and k are register
   variables for speed, and are initialized at the beginning of a
   routine that uses these macros from a global bit buffer and count.

   If we assume that EOB will be the longest code, then we will never
   ask for bits with NEEDBITS that are beyond the end of the stream.
   So, NEEDBITS should not read any more bytes than are needed to
   meet the request.  Then no bytes need to be "returned" to the buffer
   at the end of the last block.

   However, this assumption is not true for fixed blocks--the EOB code
   is 7 bits, but the other literal/length codes can be 8 or 9 bits.
   (The EOB code is shorter than other codes because fixed blocks are
   generally short.  So, while a block always has an EOB, many other
   literal/length codes have a significantly lower probability of
   showing up at all.)	However, by making the first table have a
   lookup of seven bits, the EOB code will be found in that first
   lookup, and so will not require that too many bits be pulled from
   the stream.
 */

static UWORD mask_bits[] = {
    0x0000,
    0x0001, 0x0003, 0x0007, 0x000f, 0x001f, 0x003f, 0x007f, 0x00ff,
    0x01ff, 0x03ff, 0x07ff, 0x0fff, 0x1fff, 0x3fff, 0x7fff, 0xffff
};

#define NEXTBYTE()  (g->inbuf[g->inpos++])
#define NEEDBITS(n) {while(k<(n)){b|=((ULONG)NEXTBYTE())<<k;k+=8;}}
#define DUMPBITS(n) {b>>=(n);k-=(n);}

/*
   Huffman code decoding is performed using a multi-level table lookup.
   The fastest way to decode is to simply build a lookup table whose
   size is determined by the longest code.  However, the time it takes
   to build this table can also be a factor if the data being decoded
   is not very long.  The most common codes are necessarily the
   shortest codes, so those codes dominate the decoding time, and hence
   the speed.  The idea is you can have a shorter table that decodes the
   shorter, more probable codes, and then point to subsidiary tables for
   the longer codes.  The time it costs to decode the longer codes is
   then traded against the time it takes to make longer tables.

   This results of this trade are in the variables lbits and dbits
   below.  lbits is the number of bits the first level table for literal/
   length codes can decode in one step, and dbits is the same thing for
   the distance codes.	Subsequent tables are also less than or equal to
   those sizes.  These values may be adjusted either when all of the
   codes are shorter than that, in which case the longest code length in
   bits is used, or when the shortest code is *longer* than the requested
   table size, in which case the length of the shortest code in bits is
   used.

   There are two different values for the two tables, since they code a
   different number of possibilities each.  The literal/length table
   codes 286 possible values, or in a flat code, a little over eight
   bits.  The distance table codes 30 possible values, or a little less
   than five bits, flat.  The optimum values for speed end up being
   about one bit more than those, so lbits is 8+1 and dbits is 5+1.
   The optimum values may differ though from machine to machine, and
   possibly even between compilers.  Your mileage may vary.
 */

#define lbits 9;	/* bits in base literal/length lookup table */
#define dbits 6;	/* bits in base distance lookup table */

static LONG huft_build(ULONG *b, ULONG n, ULONG s, UWORD *d, UWORD *e, 
struct huft **t, LONG *m, struct GZipData *g)
/* b - code lengths in bits (all assumed <= BMAX) */
/* n - number of codes (assumed <= N_MAX) */
/* s - number of simple-valued codes (0..s-1) */
/* d - list of base values for non-simple codes */
/* e - list of extra bits for non-simple codes */
/* t - result: starting table */
/* m - maximum lookup bits, returns actual */
/* Given a list of code lengths and a maximum table size, make a set of
   tables to decode that set of codes.	Return zero on success, one if
   the given code set is incomplete (the tables are still built in this
   case), two if the input is invalid (all zero length codes or an
   oversubscribed set of lengths), and three if not enough memory. */
{
  ULONG a;		/* counter for codes of length k */
  ULONG f;		/* i repeats in table every f entries */
  LONG g2;		/* maximum code length */
  LONG h;		/* table level */
  ULONG i;		/* counter, current code */
  ULONG j;		/* counter */
  LONG k;		/* number of bits in current code */
  LONG l;		/* bits per table (returned in m) */
  ULONG *p;		/* pointer into c[], b[], or v[] */
  struct huft *q;	/* points to current table */
  struct huft r;	/* table entry for structure assignment */
  LONG w;		/* bits before this table == (l * h) */
  ULONG *xp;		/* pointer into x */
  LONG y;		/* number of dummy codes added */
  ULONG z;		/* number of entries in current table */

  /* Generate counts for each bit length */
  for(i = 0; i < BMAX+1; ++i)
    g->c[i] = 0;

  p = b; i = n;
  do {
    g->c[*p++]++;			/* assume all entries <= BMAX */
  } while (--i);
  if (g->c[0] == n)		/* null input--all zero length codes */
  {
    *t = (struct huft *)NULL;
    *m = 0;
    return 0;
  }

  /* Find minimum and maximum length, bound *m by those */
  l = *m;
  for (j = 1; j <= BMAX; j++)
    if (g->c[j])
      break;
  k = j;			/* minimum code length */
  if ((ULONG)l < j)
    l = j;
  for (i = BMAX; i; i--)
    if (g->c[i])
      break;
  g2 = i;			 /* maximum code length */
  if ((ULONG)l > i)
    l = i;
  *m = l;


  /* Adjust last length count to fill out codes, if needed */
  for (y = 1 << j; j < i; j++, y <<= 1)
    if((y -= g->c[j]) < 0)
      return 2; 		/* bad input: more codes than bits */
  if ((y -= g->c[i]) < 0)
    return 2;
  g->c[i] += y;


  /* Generate starting offsets into the value table for each length */
  g->x[1] = j = 0;
  p = g->c + 1;  xp = g->x + 2;
  while (--i) { 		/* note that i == g from above */
    *xp++ = (j += *p++);
  }


  /* Make a table of values in order of bit lengths */
  p = b;  i = 0;
  do {
    if ((j = *p++) != 0)
      g->v[g->x[j]++] = i;
  } while (++i < n);


  /* Generate the Huffman codes and for each, make the table entries */
  g->x[0] = i = 0; 		/* first Huffman code is zero */
  p = g->v;			/* grab values in bit order */
  h = -1;			/* no tables yet--level -1 */
  w = -l;			/* bits decoded == (l * h) */
  g->u[0] = (struct huft *)NULL;	/* just to keep compilers happy */
  q = (struct huft *)NULL;	/* ditto */
  z = 0;			/* ditto */

  /* go through the bit lengths (k already is bits in shortest code) */
  for (; k <= g2; k++)
  {
    a = g->c[k];
    while (a--)
    {
      /* here i is the Huffman code of length k bits for value *p */
      /* make tables up to required level */
      while (k > w + l)
      {
	h++;
	w += l; 		/* previous table always l bits */

	/* compute minimum size table less than or equal to l bits */
	z = (z = g2 - w) > (ULONG)l ? l : z;  /* upper limit on table size */
	if ((f = 1 << (j = k - w)) > a + 1)	/* try a k-w bit table */
	{			/* too few codes for k-w bit table */
	  f -= a + 1;		/* deduct codes from patterns left */
	  xp = g->c + k;
	  while (++j < z)	/* try smaller tables up to z bits */
	  {
	    if ((f <<= 1) <= *++xp)
	      break;		/* enough codes to use up j bits */
	    f -= *xp;		/* else deduct codes from patterns */
	  }
	}
	z = 1 << j;		/* table entries for j-bit table */

	/* allocate and link in new table */
	if(!(q = (struct huft *)AllocVec((z + 1)*sizeof(struct huft), MEMF_CLEAR)))
	{
	  if(h)
	    huft_free(g->u[0],g);
	  return 100;		/* not enough memory */
	}
	*t = q + 1;		/* link to list for huft_free() */
	*(t = &(q->v.t)) = (struct huft *)NULL;
	g->u[h] = ++q;		/* table starts after link */

	/* connect to last table, if there is one */
	if (h)
	{
	  g->x[h] = i;		/* save pattern for backing up */
	  r.b = (UBYTE)l;	/* bits to dump before this table */
	  r.e = (UBYTE)(16 + j); /* bits in this table */
	  r.v.t = q;		/* pointer to this table */
	  j = i >> (w - l);	/* (get around Turbo C bug) */
	  g->u[h-1][j] = r;	/* connect to last table */
	}
      }

      /* set up table entry in r */
      r.b = (UBYTE)(k - w);
      if (p >= g->v + n)
	r.e = 99;		/* out of values--invalid code */
      else if (*p < s)
      {
	r.e = (UBYTE)(*p < 256 ? 16 : 15); /* 256 is end-of-block code */
	r.v.n = (UWORD)(*p);	/* simple code is just the value */
	p++;			/* one compiler does not like *p++ */
      }
      else
      {
	r.e = (UBYTE)e[*p - s]; /* non-simple--look up in lists */
	r.v.n = d[*p++ - s];
      }

      /* fill code-like entries with r */
      f = 1 << (k - w);
      for (j = i >> w; j < z; j += f)
	q[j] = r;

      /* backwards increment the k-bit code i */
      for (j = 1 << (k - 1); i & j; j >>= 1)
	i ^= j;
      i ^= j;

      /* backup over finished tables */
      while ((i & ((1 << w) - 1)) != g->x[h])
      {
	h--;			/* don't need to update q */
	w -= l;
      }
    }
  }

  /* Return true (1) if we were given an incomplete table */
  return y != 0 && g2 != 1;
}

static void huft_free(struct huft *t, struct GZipData *g) /* table to free */
/* Free the allocated tables built by huft_build(), which makes a linked
   list of the tables it made, with the links in a dummy first entry of
   each table. */
{
  struct huft *q;

  while(t)
  {
    q = (--t)->v.t;
    FreeVec(t);
    t = q;
  } 
}

static LONG inflate_codes(struct huft *tl, struct huft *td, LONG bl, LONG bd,
struct GZipData *g)
/* tl, td -literal/length and distance decoder tables */
/* bl, bd -number of bits decoded by tl[] and td[] */
/* inflate (decompress) the codes in a deflated (compressed) block.
   Return an error code or zero if it all goes ok. */
{
  ULONG e;		/* table entry flag/number of extra bits */
  ULONG n, d;		/* length and index for copy */
  struct huft *t;	/* pointer to table entry */
  ULONG ml, md; 	/* masks for bl and bd bits */
  ULONG b;		/* bit buffer */
  ULONG k;		/* number of bits in bit buffer */

  /* make local copies of globals */
  b = g->bb;		/* initialize bit buffer */
  k = g->bk;

  /* inflate the coded data */
  ml = mask_bits[bl];		/* precompute masks for speed */
  md = mask_bits[bd];
  for(;;)			/* do until end of block */
  {
    NEEDBITS((ULONG)bl)
    if ((e = (t = tl + ((ULONG)b & ml))->e) > 16)
      do {
	if (e == 99)
	  return 1;
	DUMPBITS(t->b)
	e -= 16;
	NEEDBITS(e)
      } while ((e = (t = t->v.t + ((ULONG)b & mask_bits[e]))->e) > 16);
    DUMPBITS(t->b)
    if(e == 16) 		/* then it's a literal */
    {
      if(g->outpos >= g->outsize)
        return 300;
      g->outbuf[g->outpos++] = (UBYTE)t->v.n;
    }
    else			/* it's an EOB or a length */
    {
      /* exit if end of block */
      if (e == 15)
	break;

      /* get length of block to copy */
      NEEDBITS(e)
      n = t->v.n + ((ULONG)b & mask_bits[e]);
      DUMPBITS(e);

      /* decode distance of block to copy */
      NEEDBITS((ULONG)bd)
      if ((e = (t = td + ((ULONG)b & md))->e) > 16)
	do {
	  if (e == 99)
	    return 1;
	  DUMPBITS(t->b)
	  e -= 16;
	  NEEDBITS(e)
	} while ((e = (t = t->v.t + ((ULONG)b & mask_bits[e]))->e) > 16);
      DUMPBITS(t->b)
      NEEDBITS(e)
      d = g->outpos - t->v.n - ((ULONG)b & mask_bits[e]);
      DUMPBITS(e)

      /* do the copy */
      if(g->outpos + n >= g->outsize)
        return 300;
      do {
	g->outbuf[g->outpos++] = g->outbuf[d++];
      } while(--n);
    }
  }

  /* restore the globals from the locals */
  g->bb = b;			/* restore global bit buffer */
  g->bk = k;

  /* done */
  return 0;
}

static LONG inflate_stored(struct GZipData *g)
/* "decompress" an inflated type 0 (stored) block. */
{
  ULONG n;	/* number of bytes in block */
  ULONG b;	/* bit buffer */
  ULONG k;	/* number of bits in bit buffer */

  /* make local copies of globals */
  b = g->bb;			/* initialize bit buffer */
  k = g->bk;

  /* go to byte boundary */
  n = k & 7;
  DUMPBITS(n);

  /* get the length and its complement */
  NEEDBITS(16)
  n = ((ULONG)b & 0xffff);
  DUMPBITS(16)
  NEEDBITS(16)
  if(n != (ULONG)((~b) & 0xffff))
    return 1;			/* error in compressed data */
  DUMPBITS(16)

  /* read and output the compressed data */
  if(g->outpos + n >= g->outsize)
    return 300;
  while (n--)
  {
    NEEDBITS(8)
    g->outbuf[g->outpos++] = (UBYTE)b;
    DUMPBITS(8)
  }

  /* restore the globals from the locals */
  g->bb = b;			/* restore global bit buffer */
  g->bk = k;
  return 0;
}

static LONG inflate_fixed(struct GZipData *g)
/* decompress an inflated type 1 (fixed Huffman codes) block.  We should
   either replace this with a custom decoder, or at least precompute the
   Huffman tables. */
{
  LONG i;		/* temporary variable */
  struct huft *tl;	/* literal/length code table */
  struct huft *td;	/* distance code table */
  LONG bl;		/* lookup bits for tl */
  LONG bd;		/* lookup bits for td */
  ULONG *l;	 	/* length list for huft_build, we need 288 ULONG's */

  l = g->data1;

  /* set up literal table */
  for (i = 0; i < 144; i++)
    l[i] = 8;
  for (; i < 256; i++)
    l[i] = 9;
  for (; i < 280; i++)
    l[i] = 7;
  for (; i < 288; i++)		/* make a complete, but wrong code set */
    l[i] = 8;
  bl = 7;
  if((i = huft_build(l, 288, 257, cplens, cplext, &tl, &bl,g)) != 0)
    return i;

  /* set up distance table */
  for (i = 0; i < 30; i++)	/* make an incomplete code set */
    l[i] = 5;
  bd = 5;
  if((i = huft_build(l, 30, 0, cpdist, cpdext, &td, &bd,g)) > 1)
  {
    huft_free(tl,g);
    return i;
  }

  /* decompress until an end-of-block code */
  i = inflate_codes(tl, td, bl, bd,g);

  /* free the decoding tables, return */
  huft_free(tl,g);
  huft_free(td,g);
  return i;
}

static LONG inflate_dynamic(struct GZipData *g)
/* decompress an inflated type 2 (dynamic Huffman codes) block. */
{
  LONG i;		/* temporary variables */
  ULONG j;
  ULONG l;		/* last length */
  ULONG m;		/* mask for bit lengths table */
  ULONG n;		/* number of lengths to get */
  struct huft *tl;	/* literal/length code table */
  struct huft *td;	/* distance code table */
  LONG bl;		/* lookup bits for tl */
  LONG bd;		/* lookup bits for td */
  ULONG nb;		/* number of bit length codes */
  ULONG nl;		/* number of literal/length codes */
  ULONG nd;		/* number of distance codes */
  ULONG *ll;		/* literal/length and distance code lengths, we need 286+30 ULONG's */
  ULONG b;		/* bit buffer */
  ULONG k;		/* number of bits in bit buffer */
  LONG err;

  ll = g->data1;

  /* make local bit buffer */
  b = g->bb;
  k = g->bk;

  /* read in table lengths */
  NEEDBITS(5)
  nl = 257 + ((ULONG)b & 0x1f); /* number of literal/length codes */
  DUMPBITS(5)
  NEEDBITS(5)
  nd = 1 + ((ULONG)b & 0x1f);	/* number of distance codes */
  DUMPBITS(5)
  NEEDBITS(4)
  nb = 4 + ((ULONG)b & 0xf);	/* number of bit length codes */
  DUMPBITS(4)
  if (nl > 286 || nd > 30)
    return 1;			/* bad lengths */

  /* read in bit-length-code lengths */
  for (j = 0; j < nb; j++)
  {
    NEEDBITS(3)
    ll[border[j]] = (ULONG)b & 7;
    DUMPBITS(3)
  }
  for (; j < 19; j++)
    ll[border[j]] = 0;

  /* build decoding table for trees--single level, 7 bit lookup */
  bl = 7;
  if ((i = huft_build(ll, 19, 19, NULL, NULL, &tl, &bl,g)) != 0)
  {
    if (i == 1)
      huft_free(tl,g);
    return i;			/* incomplete code set */
  }

  /* read in literal and distance code lengths */
  n = nl + nd;
  m = mask_bits[bl];
  i = l = 0;
  err = 0;
  while ((ULONG)i < n)
  {
    NEEDBITS((ULONG)bl)
    j = (td = tl + ((ULONG)b & m))->b;
    DUMPBITS(j)
    j = td->v.n;
    if (j < 16) 		/* length of code in bits (0..15) */
      ll[i++] = l = j;		/* save last length in l */
    else if (j == 16)		/* repeat last length 3 to 6 times */
    {
      NEEDBITS(2)
      j = 3 + ((ULONG)b & 3);
      DUMPBITS(2)
      if ((ULONG)i + j > n)
      {
        err = 1; break;
      }
      while (j--)
	ll[i++] = l;
    }
    else if (j == 17)		/* 3 to 10 zero length codes */
    {
      NEEDBITS(3)
      j = 3 + ((ULONG)b & 7);
      DUMPBITS(3)
      if((ULONG)i + j > n)
      {
        err = 1; break;
      }
      while (j--)
	ll[i++] = 0;
      l = 0;
    }
    else			/* j == 18: 11 to 138 zero length codes */
    {
      NEEDBITS(7)
      j = 11 + ((ULONG)b & 0x7f);
      DUMPBITS(7)
      if((ULONG)i + j > n)
      {
        err = 1; break;
      }
      while (j--)
	ll[i++] = 0;
      l = 0;
    }
  }

  /* free decoding table for trees */
  huft_free(tl,g);

  if(err)
    return err;

  /* restore the global bit buffer */
  g->bb = b;
  g->bk = k;

  /* build the decoding tables for literal/length and distance codes */
  bl = lbits;
  if((i = huft_build(ll, nl, 257, cplens, cplext, &tl, &bl,g)) != 0)
  {
    if(i == 1)
      huft_free(tl,g);
    return i;			/* incomplete code set */
  }
  bd = dbits;
  if((i = huft_build(ll + nl, nd, 0, cpdist, cpdext, &td, &bd,g)) != 0)
  {
    if(i == 1)
      huft_free(td,g);
    huft_free(tl,g);
    return i;			/* incomplete code set */
  }

  /* decompress until an end-of-block code */
  err = inflate_codes(tl, td, bl, bd, g);

  /* free the decoding tables, return */
  huft_free(tl,g);
  huft_free(td,g);
  return err;
}

static BOOL decrunchZip(struct GZipData *g)
{
  LONG e;	/* last block flag */
  LONG t;	/* block type */
  ULONG b;	/* bit buffer */
  ULONG k;	/* number of bits in bit buffer */

  g->XFDerr = XFDERR_CORRUPTEDDATA;
  /* decompress until the last block */
  do
  {
    b = g->bb; k = g->bk;
    NEEDBITS(1) e = (LONG)b & 1; DUMPBITS(1)
    NEEDBITS(2) t = (LONG)b & 3; DUMPBITS(2)
    g->bb = b; g->bk = k;

    /* inflate that block type */
    switch(t)
    {
    case 0: t = inflate_stored(g); break;
    case 1: t = inflate_fixed(g); break;
    case 2: t = inflate_dynamic(g); break;
    };

    if(t)
    {
      if(t == 300)
        g->XFDerr = XFDERR_BUFFERTRUNCATED;
      else if(t == 100)
	g->XFDerr = XFDERR_NOMEMORY;
      return 0;
    }
  } while(!e);

  /* calculate crc value */
  {
    ULONG *buf; /* 256 entries */
    STRPTR p;

    buf = g->data1;

    for(e = 0; e < 256; ++e)
    {
      k = 2*e;
      for(t = b = 0; t < 8; ++t)
      {
        k >>= 1;
        b = ((k ^ b) & 1) ? (b >> 1) ^ 0xEDB88320 : b >> 1;
      }
      buf[e] = b;
    }

    b = 0xFFFFFFFF;
    e = g->outsize-BUFFEREXTEND;
    p = g->outbuf;
  
    while(e--)
      b = buf[(b ^ *(p++)) & 0xFF] ^ (b >> 8);
  }

  if(~b == g->crc)
    return 1;
  else
    return 0;
}

