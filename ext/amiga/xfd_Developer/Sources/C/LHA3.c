char version[] = "$VER: LHA3 2.0 (11.07.1999) by SDI";

/* Objectheader

	Name:		LHA3.c
	Description:	xfd external decruncher for =SB= files
	Author: 	SDI (stoecker@epost.de)
	Distribution:	PD

 2.0   11.07.99 : first version
*/

#include <libraries/xfdmaster.h>
#include <proto/exec.h>
#include <exec/memory.h>
#include <exec/execbase.h>
#include "SDI_compiler.h"

#define MAXMATCH	256
#define THRESHOLD	3
#define UCHAR_MAX	((1<<(sizeof(UBYTE)*8))-1)
#define NT		(USHRT_BIT + 3)
#define TBIT 		5
#define NC 		(UCHAR_MAX + MAXMATCH + 2 - THRESHOLD)
#define NPT		0x80
#define CHAR_BIT  	8
#define CBIT		9
#define USHRT_BIT	16

struct LhData {
  STRPTR 	inbuf;
  STRPTR 	outbuf;
  LONG		origsize;
  LONG		compsize;
  LONG		XFDerr;
  UWORD		blocksize;
  UWORD		bitbuf;
  UWORD		left[2 * NC - 1];
  UWORD		right[2 * NC - 1];
  UWORD		c_table[4096];
  UWORD		pt_table[256];
  UBYTE 	subbitbuf;
  UBYTE		bitcount;
  UBYTE		c_len[NC];
  UBYTE		pt_len[NPT];
  UBYTE		text[1 << 15];
};

/************** Here starts xfd stuff - the xfdSlave structure **********/

#define MASTER_VERS	39

typedef BOOL (*xfdFunc) ();

ASM(LONG) RecogLHA3(REG(a0, ULONG * buf), REG(a1, struct xfdRecogResult *rr),
 REG(d0, ULONG length));
ASM(ULONG) DecrunchLHA3(REG(a0, struct xfdBufferInfo * xbi),
 REG(a6, struct xfdMasterBase *xfdMasterBase));
ASM(LONG) ScanLHA3(REG(a0, ULONG *buf), REG(d0, ULONG size));
ASM(ULONG) VerifyLHA3(REG(a0, ULONG *buf), REG(d0, ULONG size));
static void decode(struct LhData *lhd);
static void read_pt_len(struct LhData *lhd, WORD nn, WORD nbit, WORD i_special);
static void read_c_len(struct LhData *lhd);
static UWORD decode_c_st1(struct LhData *lhd);
static UWORD decode_p_st1(struct LhData *lhd);
static void fillbuf(struct LhData *lhd, UBYTE n);			/* Shift bitbuf n bits left, read n bits */
static UWORD getbits(struct LhData *lhd, UBYTE n);
static void make_table(struct LhData *lhd, WORD nchar, UBYTE bitlen[], WORD tablebits, UWORD table[]);

struct xfdSlave FirstSlave = {
  0, XFDS_VERSION, MASTER_VERS, "Stefan Boberg's LhA3 Converter", XFDPFF_DATA|XFDPFF_RECOGLEN|XFDPFF_USERTARGET,
  0, (xfdFunc) RecogLHA3, (xfdFunc) DecrunchLHA3, (xfdFunc) ScanLHA3, (xfdFunc) VerifyLHA3, 0, 0, 12};

ASM(LONG) RecogLHA3(REG(a0, ULONG * buf), REG(a1, struct xfdRecogResult *rr),
REG(d0, ULONG length))
{
  if(*buf == 0x3D53423D)
  {
    rr->xfdrr_FinalTargetLen = rr->xfdrr_MinTargetLen = buf[1];
    rr->xfdrr_MinSourceLen = 12 + buf[2];
    return 1;
  }
  else
    return 0;
}

ASM(LONG) ScanLHA3(REG(a0, ULONG *buf), REG(d0, ULONG size))
{
  if(*buf == 0x3D53423D)
    return 1;
  else
    return 0;
}

ASM(ULONG) VerifyLHA3(REG(a0, ULONG *buf), REG(d0, ULONG size))
{
  if((buf[1] >= buf[2]) && (buf[2] + 12 <= size))
    return buf[2] + 12;
  return 0;
}

ASM(ULONG) DecrunchLHA3(REG(a0, struct xfdBufferInfo * xbi),
REG(a6, struct xfdMasterBase *xfdMasterBase))
{
  ULONG res = 0;
  struct ExecBase *SysBase;
  struct LhData *lhd;

  SysBase = xfdMasterBase->xfdm_ExecBase;

  if((lhd = (struct LhData *) AllocMem(sizeof(struct LhData), MEMF_CLEAR)))
  {
    lhd->outbuf = xbi->xfdbi_UserTargetBuf;
    lhd->inbuf = ((STRPTR) xbi->xfdbi_SourceBuffer)+12;
    lhd->origsize = xbi->xfdbi_TargetBufSaveLen;
    lhd->compsize = xbi->xfdbi_SourceBufLen-12;
    decode(lhd);
    if(!(xbi->xfdbi_Error = lhd->XFDerr))
      res = 1;

    FreeMem(lhd, sizeof(struct LhData));
  }
  else
    xbi->xfdbi_Error = XFDERR_NOMEMORY;

  return res;
}

static void decode(struct LhData *lhd)
{
  LONG i, j, k, c, dicsiz1, offset, count, loc, dicsiz;

  dicsiz = 1 << 15;
  for(i = 0; i < dicsiz; ++i)
    lhd->text[i] = ' ';
//  lhd->bitbuf = 0;
//  lhd->subbitbuf = 0;
//  lhd->bitcount = 0;
  fillbuf(lhd, 2 * CHAR_BIT);
//  lhd->blocksize = 0;
  dicsiz1 = dicsiz - 1;
  offset = 0x100 - 3;
  count = 0;
  loc = 0;
  while((count < lhd->origsize) && (!lhd->XFDerr))
  {
    c = decode_c_st1(lhd);
    if (c <= UCHAR_MAX)
    {
      *(lhd->outbuf++) = lhd->text[loc++] = c;
      if (loc == dicsiz)
        loc = 0;
      count++;
    }
    else
    {
      j = c - offset;
      i = (loc - decode_p_st1(lhd) - 1) & dicsiz1;
      count += j;
      for (k = 0; k < j; k++)
      {
        *(lhd->outbuf++) = c = lhd->text[(i + k) & dicsiz1];
        lhd->text[loc++] = c;
        if (loc == dicsiz)
          loc = 0;
      }
    }
  }
}

static void read_pt_len(struct LhData *lhd, WORD nn, WORD nbit, WORD i_special)
{
  WORD i, c, n;

  n = getbits(lhd, nbit);
  if (n == 0) {
    c = getbits(lhd, nbit);
    for (i = 0; i < nn; i++)
      lhd->pt_len[i] = 0;
    for (i = 0; i < 256; i++)
      lhd->pt_table[i] = c;
  }
  else {
    i = 0;
    while (i < n) {
      c = lhd->bitbuf >> (16 - 3);
      if (c == 7) {
        UWORD  mask = 1 << (16 - 4);
        while (mask & lhd->bitbuf) {
          mask >>= 1;
          c++;
        }
      }
      fillbuf(lhd, (c < 7) ? 3 : c - 3);
      lhd->pt_len[i++] = c;
      if (i == i_special) {
        c = getbits(lhd, 2);
        while (--c >= 0)
          lhd->pt_len[i++] = 0;
      }
    }
    while (i < nn)
      lhd->pt_len[i++] = 0;
    make_table(lhd, nn, lhd->pt_len, 8, lhd->pt_table);
  }
}

static void read_c_len(struct LhData *lhd)
{
  WORD i, c, n;

  n = getbits(lhd, CBIT);
  if (n == 0) {
    c = getbits(lhd, CBIT);
    for (i = 0; i < NC; i++)
      lhd->c_len[i] = 0;
    for (i = 0; i < 4096; i++)
      lhd->c_table[i] = c;
  } else {
    i = 0;
    while (i < n) {
      c = lhd->pt_table[lhd->bitbuf >> (16 - 8)];
      if (c >= NT) {
        UWORD  mask = 1 << (16 - 9);
        do {
          if (lhd->bitbuf & mask)
            c = lhd->right[c];
          else
            c = lhd->left[c];
          mask >>= 1;
        } while (c >= NT);
      }
      fillbuf(lhd, lhd->pt_len[c]);
      if (c <= 2) {
        if (c == 0)
          c = 1;
        else if (c == 1)
          c = getbits(lhd, 4) + 3;
        else
          c = getbits(lhd, CBIT) + 20;
        while (--c >= 0)
          lhd->c_len[i++] = 0;
      }
      else
        lhd->c_len[i++] = c - 2;
    }
    while (i < NC)
      lhd->c_len[i++] = 0;
    make_table(lhd, NC, lhd->c_len, 12, lhd->c_table);
  }
}

static UWORD decode_c_st1(struct LhData *lhd)
{
  UWORD  j, mask;

  if (lhd->blocksize == 0) {
    lhd->blocksize = getbits(lhd, 16);
    read_pt_len(lhd, NT, TBIT, 3);
    read_c_len(lhd);
    read_pt_len(lhd, 16, 5, -1);
  }
  lhd->blocksize--;
  j = lhd->c_table[lhd->bitbuf >> 4];
  if (j < NC)
    fillbuf(lhd, lhd->c_len[j]);
  else {
    fillbuf(lhd, 12);
    mask = 1 << (16 - 1);
    do {
      if (lhd->bitbuf & mask)
        j = lhd->right[j];
      else
        j = lhd->left[j];
      mask >>= 1;
    } while (j >= NC);
    fillbuf(lhd, lhd->c_len[j] - 12);
  }
  return j;
}

static UWORD decode_p_st1(struct LhData *lhd)
{
  UWORD  j, mask;

  j = lhd->pt_table[lhd->bitbuf >> (16 - 8)];
  if (j < 16)
    fillbuf(lhd, lhd->pt_len[j]);
  else {
    fillbuf(lhd, 8);
    mask = 1 << (16 - 1);
    do {
      if (lhd->bitbuf & mask)
        j = lhd->right[j];
      else
        j = lhd->left[j];
      mask >>= 1;
    } while (j >= 16);
    fillbuf(lhd, lhd->pt_len[j] - 8);
  }
  if (j != 0)
    j = (1 << (j - 1)) + getbits(lhd, j - 1);
  return j;
}

static void fillbuf(struct LhData *lhd, UBYTE n)     /* Shift lhd->bitbuf n bits lhd->left, read n bits */
{
  while (n > lhd->bitcount) {
    n -= lhd->bitcount;
    lhd->bitbuf = (lhd->bitbuf << lhd->bitcount) + (lhd->subbitbuf >> (CHAR_BIT - lhd->bitcount));
    if (lhd->compsize != 0) {
      lhd->compsize--;
      lhd->subbitbuf = (UBYTE) *(lhd->inbuf++);
    }
    else
      lhd->subbitbuf = 0;
    lhd->bitcount = CHAR_BIT;
  }
  lhd->bitcount -= n;
  lhd->bitbuf = (lhd->bitbuf << n) + (lhd->subbitbuf >> (CHAR_BIT - n));
  lhd->subbitbuf <<= n;
}

static UWORD getbits(struct LhData *lhd, UBYTE n)
{
  UWORD  x;

  x = lhd->bitbuf >> (2 * CHAR_BIT - n);
  fillbuf(lhd, n);
  return x;
}

static void make_table(struct LhData *lhd, WORD nchar, UBYTE bitlen[], WORD tablebits, UWORD table[])
{
  UWORD  count[17]; /* count of bitlen */
  UWORD  weight[17];  /* 0x10000ul >> bitlen */
  UWORD  start[17]; /* first code of bitlen */
  UWORD  total;
  ULONG    i;
  LONG             j, k, l, m, n, avail;
  UWORD *p;

  if(lhd->XFDerr)
    return;

  avail = nchar;

  /* initialize */
  for (i = 1; i <= 16; i++) {
    count[i] = 0;
    weight[i] = 1 << (16 - i);
  }

  /* count */
  for (i = 0; i < nchar; i++)
    count[bitlen[i]]++;

  /* calculate first code */
  total = 0;
  for (i = 1; i <= 16; i++) {
    start[i] = total;
    total += weight[i] * count[i];
  }
  if ((total & 0xffff) != 0)
  {
    lhd->XFDerr = XFDERR_CORRUPTEDDATA;
    return;
  }

  /* shift data for make table. */
  m = 16 - tablebits;
  for (i = 1; i <= tablebits; i++) {
    start[i] >>= m;
    weight[i] >>= m;
  }

  /* initialize */
  j = start[tablebits + 1] >> m;
  k = 1 << tablebits;
  if (j != 0)
    for (i = j; i < k; i++)
      table[i] = 0;

  /* create table and tree */
  for (j = 0; j < nchar; j++) {
    k = bitlen[j];
    if (k == 0)
      continue;
    l = start[k] + weight[k];
    if (k <= tablebits) {
      /* code in table */
      for (i = start[k]; i < l; i++)
        table[i] = j;
    }
    else {
      /* code not in table */
      p = &table[(i = start[k]) >> m];
      i <<= tablebits;
      n = k - tablebits;
      /* make tree (n length) */
      while (--n >= 0) {
        if (*p == 0) {
          lhd->right[avail] = lhd->left[avail] = 0;
          *p = avail++;
        }
        if (i & 0x8000)
          p = &lhd->right[*p];
        else
          p = &lhd->left[*p];
        i <<= 1;
      }
      *p = j;
    }
    start[k] = l;
  }
}

