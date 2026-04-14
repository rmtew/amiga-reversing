/* Generated Atari ST OS runtime metadata from EmuTOS headers. Do not edit directly. */
#include "generated/atari_st_os_runtime.h"

#include <string.h>

static const AtariStOsCallInfo g_atari_st_os_calls[] = {
  { "GEMDOS", 1u, 0u, "Pterm0", "p_term0", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 1u, "Cconin", "c_conin", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 2u, "Cconout", "c_conout", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 3u, "Cauxin", "c_auxin", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 4u, "Cauxout", "c_auxout", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 5u, "Cprnout", "c_prnout", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 6u, "Crawio", "c_rawio", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 7u, "Crawcin", "c_rawcin", "bdosbind.h", "GEMDOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 8u, "Cnecin", "c_necin", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 9u, "Cconws", "c_conws", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 10u, "Cconrs", "c_conrs", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 11u, "Cconis", "c_conis", "bdosbind.h", "GEMDOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 14u, "Dsetdrv", "d_setdrv", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 15u, "Seedfill", "GEMDOS_Seedfill", "status.txt", NULL, 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 16u, "Cconos", "c_conos", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 17u, "Cprnos", "c_prnos", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 18u, "Cauxis", "c_auxis", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 19u, "Cauxos", "c_auxos", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 20u, "Maddalt", "m_addalt", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 21u, "Srealloc", "GEMDOS_Srealloc", "bdosbind.h", NULL, 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 25u, "Dgetdrv", "d_getdrv", "bdosbind.h", "GEMDOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 26u, "Fsetdta", "f_setdta", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 32u, "Super", "super", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 42u, "Tgetdate", "t_getdate", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 43u, "Tsetdate", "t_setdate", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 44u, "Tgettime", "t_gettime", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 45u, "Tsettime", "t_settime", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 47u, "Fgetdta", "f_getdta", "bdosbind.h", "GEMDOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 48u, "Sversion", "s_version", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 49u, "Ptermres", "p_termres", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 54u, "Dfree", "d_free", "bdosbind.h", "GEMDOS.I", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 57u, "Dcreate", "d_create", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 58u, "Ddelete", "d_delete", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 59u, "Dsetpath", "d_setpath", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 60u, "Fcreate", "f_create", "bdosbind.h", "GEMDOS.I", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 61u, "Fopen", "f_open", "bdosbind.h", "GEMDOS.I", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 62u, "Fclose", "f_close", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 63u, "Fread", "f_read", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 64u, "Fwrite", "f_write", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 65u, "Fdelete", "f_delete", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 66u, "Fseek", "f_seek", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 67u, "Fattrib", "f_attrib", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 68u, "Mxalloc", "m_xalloc", "bdosbind.h", "GEMDOS.I", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 69u, "Fdup", "f_dup", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 70u, "Fforce", "f_force", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 71u, "Dgetpath", "d_getpath", "bdosbind.h", "GEMDOS.I", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 72u, "Malloc", "m_alloc", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 73u, "Mfree", "m_free", "bdosbind.h", "GEMDOS.I", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 74u, "Mshrink", "m_shrink", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 75u, "Pexec", "p_exec", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 76u, "Pterm", "p_term", "status.txt", "GEMDOS.I", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 78u, "Fsfirst", "f_sfirst", "bdosbind.h", "GEMDOS.I", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 79u, "Fsnext", "f_snext", "bdosbind.h", "GEMDOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 86u, "Frename", "f_rename", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 87u, "Fdatime", "f_datime", "bdosbind.h", "GEMDOS.I", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 0u, "Getmpb", "getmpb", "biosbind.h", "BIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "BIOS", 13u, 1u, "Bconstat", "bconstat", "biosbind.h", "BIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "BIOS", 13u, 2u, "Bconin", "bconin", "biosbind.h", "BIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 3u, "Bconout", "bconout", "biosbind.h", "BIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 4u, "Rwabs", "rwabs", "biosbind.h", "BIOS.I", 1u, 18u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 5u, "Setexc", "setexc", "biosbind.h", "BIOS.I", 1u, 8u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 6u, "Tickcal", "tickcal", "biosbind.h", "BIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 7u, "Getbpb", "getbpb", "biosbind.h", "BIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 8u, "Bcostat", "bcostat", "biosbind.h", "BIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 9u, "Mediach", "mediach", "biosbind.h", "BIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 10u, "Drvmap", "drvmap", "biosbind.h", "BIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 11u, "Kbshift", "kbshift", "biosbind.h", "BIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 0u, "Initmous", "initmous", "xbiosbind.h", "XBIOS.I", 1u, 12u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 1u, "Ssbrk", "ssbrk", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 2u, "Physbase", "physbase", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 3u, "Logbase", "logbase", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 4u, "Getrez", "getrez", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 5u, "Setscreen", "vsetscreen", "xbiosbind.h", "XBIOS.I", 1u, 14u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 6u, "Setpalette", "setpalette", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 7u, "Setcolor", "setcolor", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 8u, "Floprd", "floprd", "xbiosbind.h", "XBIOS.I", 1u, 20u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 9u, "Flopwr", "flopwr", "xbiosbind.h", "XBIOS.I", 1u, 20u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 10u, "Flopfmt", "flopfmt", "xbiosbind.h", "XBIOS.I", 1u, 26u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 12u, "Midiws", "midiws", "xbiosbind.h", "XBIOS.I", 1u, 8u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 13u, "Mfpint", "mfpint", "xbiosbind.h", "XBIOS.I", 1u, 8u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 14u, "Iorec", "iorec", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 15u, "Rsconf", "rsconf", "xbiosbind.h", "XBIOS.I", 1u, 14u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 16u, "Keytbl", "keytbl", "xbiosbind.h", "XBIOS.I", 1u, 14u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 17u, "Random", "random", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 18u, "Protobt", "protobt", "xbiosbind.h", "XBIOS.I", 1u, 14u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 19u, "Flopver", "flopver", "xbiosbind.h", "XBIOS.I", 1u, 20u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 20u, "Scrdmp", "scrdmp", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 21u, "Cursconf", "cursconf", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 22u, "Settime", "settime", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 23u, "Gettime", "gettime", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 24u, "Bioskeys", "bioskeys", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 25u, "Ikbdws", "ikbdws", "xbiosbind.h", "XBIOS.I", 1u, 8u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 26u, "Jdisint", "jdisint", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 27u, "Jenabint", "jenabint", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 28u, "Giaccess", "giaccess", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 29u, "Offgibit", "offgibit", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 30u, "Ongibit", "ongibit", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 31u, "Xbtimer", "xbtimer", "xbiosbind.h", "XBIOS.I", 1u, 12u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 32u, "Dosound", "dosound", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 33u, "Setprt", "setprt", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 34u, "Kbdvbase", "kbdvbase", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 35u, "Kbrate", "kbrate", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 36u, "Prtblk", "prtblk", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 37u, "Vsync", "vsync", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 38u, "Supexec", "supexec", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 39u, "Puntaes", "puntaes", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 64u, "Blitmode", "blitmode", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 81u, "EgetShift", "egetshift", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 83u, "EsetColor", "esetcolor", "xbiosbind.h", "XBIOS.I", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 88u, "VsetMode", "vsetmode", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 89u, "VgetMonitor", "mon_type", "xbiosbind.h", "XBIOS.I", 1u, 2u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 91u, "VgetSize", "vgetsize", "xbiosbind.h", "XBIOS.I", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 93u, "VsetRGB", "vsetrgb", "xbiosbind.h", "XBIOS.I", 1u, 10u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 94u, "VgetRGB", "vgetrgb", "xbiosbind.h", "XBIOS.I", 1u, 10u, 0u, ATARI_ST_OS_RETURN_VOID },
};

const AtariStOsCallInfo *atari_st_os_find_call(uint8_t trap_vector, uint16_t opcode) {
  size_t low = 0U;
  size_t high = ATARI_ST_OS_CALL_COUNT;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    const AtariStOsCallInfo *entry = &g_atari_st_os_calls[mid];
    if (trap_vector == entry->trap_vector) {
      if (opcode == entry->opcode) return entry;
      if (opcode < entry->opcode) high = mid;
      else low = mid + 1U;
      continue;
    }
    if (trap_vector < entry->trap_vector) high = mid;
    else low = mid + 1U;
  }
  return NULL;
}

const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_name(const char *symbol_name) {
  size_t index;
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  for (index = 0U; index < ATARI_ST_OS_CALL_COUNT; ++index) {
    const AtariStOsCallInfo *entry = &g_atari_st_os_calls[index];
    if (strcmp(symbol_name, entry->symbol_name) == 0) return entry;
  }
  return NULL;
}

const char *atari_st_os_find_symbol_include(const char *symbol_name) {
  const AtariStOsCallInfo *entry = atari_st_os_find_call_by_symbol_name(symbol_name);
  return (entry != NULL && entry->include_path != NULL && entry->include_path[0] != '\0') ? entry->include_path : NULL;
}
