/* Generated Atari ST OS runtime metadata from EmuTOS headers. Do not edit directly. */
#include "generated/atari_st_os_runtime.h"

#include <string.h>

static const AtariStOsCallInfo g_atari_st_os_calls[] = {
  { "GEMDOS", 1u, 0u, "Pterm0", "GEMDOS_Pterm0", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 1u, "Cconin", "GEMDOS_Cconin", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 2u, "Cconout", "GEMDOS_Cconout", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 3u, "Cauxin", "GEMDOS_Cauxin", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 4u, "Cauxout", "GEMDOS_Cauxout", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 5u, "Cprnout", "GEMDOS_Cprnout", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 6u, "Crawio", "GEMDOS_Crawio", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 7u, "Crawcin", "GEMDOS_Crawcin", "bdosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 8u, "Cnecin", "GEMDOS_Cnecin", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 9u, "Cconws", "GEMDOS_Cconws", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 10u, "Cconrs", "GEMDOS_Cconrs", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 11u, "Cconis", "GEMDOS_Cconis", "bdosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 14u, "Dsetdrv", "GEMDOS_Dsetdrv", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 15u, "Seedfill", "GEMDOS_Seedfill", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 16u, "Cconos", "GEMDOS_Cconos", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 17u, "Cprnos", "GEMDOS_Cprnos", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 18u, "Cauxis", "GEMDOS_Cauxis", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 19u, "Cauxos", "GEMDOS_Cauxos", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 20u, "Maddalt", "GEMDOS_Maddalt", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 21u, "Srealloc", "GEMDOS_Srealloc", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 25u, "Dgetdrv", "GEMDOS_Dgetdrv", "bdosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 26u, "Fsetdta", "GEMDOS_Fsetdta", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 32u, "Super", "GEMDOS_Super", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 42u, "Tgetdate", "GEMDOS_Tgetdate", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 43u, "Tsetdate", "GEMDOS_Tsetdate", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 44u, "Tgettime", "GEMDOS_Tgettime", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 45u, "Tsettime", "GEMDOS_Tsettime", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 47u, "Fgetdta", "GEMDOS_Fgetdta", "bdosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 48u, "Sversion", "GEMDOS_Sversion", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 49u, "Ptermres", "GEMDOS_Ptermres", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 54u, "Dfree", "GEMDOS_Dfree", "bdosbind.h", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 57u, "Dcreate", "GEMDOS_Dcreate", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 58u, "Ddelete", "GEMDOS_Ddelete", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 59u, "Dsetpath", "GEMDOS_Dsetpath", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 60u, "Fcreate", "GEMDOS_Fcreate", "bdosbind.h", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 61u, "Fopen", "GEMDOS_Fopen", "bdosbind.h", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 62u, "Fclose", "GEMDOS_Fclose", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 63u, "Fread", "GEMDOS_Fread", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 64u, "Fwrite", "GEMDOS_Fwrite", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 65u, "Fdelete", "GEMDOS_Fdelete", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 66u, "Fseek", "GEMDOS_Fseek", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 67u, "Fattrib", "GEMDOS_Fattrib", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 68u, "Mxalloc", "GEMDOS_Mxalloc", "bdosbind.h", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 69u, "Fdup", "GEMDOS_Fdup", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 70u, "Fforce", "GEMDOS_Fforce", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 71u, "Dgetpath", "GEMDOS_Dgetpath", "bdosbind.h", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 72u, "Malloc", "GEMDOS_Malloc", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 73u, "Mfree", "GEMDOS_Mfree", "bdosbind.h", 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 74u, "Mshrink", "GEMDOS_Mshrink", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 75u, "Pexec", "GEMDOS_Pexec", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 76u, "Pterm", "GEMDOS_Pterm", "status.txt", 0u, 0u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 78u, "Fsfirst", "GEMDOS_Fsfirst", "bdosbind.h", 0u, 0u, 2u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 79u, "Fsnext", "GEMDOS_Fsnext", "bdosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 86u, "Frename", "GEMDOS_Frename", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "GEMDOS", 1u, 87u, "Fdatime", "GEMDOS_Fdatime", "bdosbind.h", 0u, 0u, 3u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 0u, "Getmpb", "BIOS_Getmpb", "biosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "BIOS", 13u, 1u, "Bconstat", "BIOS_Bconstat", "biosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "BIOS", 13u, 2u, "Bconin", "BIOS_Bconin", "biosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 3u, "Bconout", "BIOS_Bconout", "biosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 4u, "Rwabs", "BIOS_Rwabs", "biosbind.h", 1u, 18u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 5u, "Setexc", "BIOS_Setexc", "biosbind.h", 1u, 8u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 6u, "Tickcal", "BIOS_Tickcal", "biosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 7u, "Getbpb", "BIOS_Getbpb", "biosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 8u, "Bcostat", "BIOS_Bcostat", "biosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 9u, "Mediach", "BIOS_Mediach", "biosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 10u, "Drvmap", "BIOS_Drvmap", "biosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "BIOS", 13u, 11u, "Kbshift", "BIOS_Kbshift", "biosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 0u, "Initmous", "XBIOS_Initmous", "xbiosbind.h", 1u, 12u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 1u, "Ssbrk", "XBIOS_Ssbrk", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 2u, "Physbase", "XBIOS_Physbase", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 3u, "Logbase", "XBIOS_Logbase", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 4u, "Getrez", "XBIOS_Getrez", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 5u, "Setscreen", "XBIOS_Setscreen", "xbiosbind.h", 1u, 14u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 6u, "Setpalette", "XBIOS_Setpalette", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 7u, "Setcolor", "XBIOS_Setcolor", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 8u, "Floprd", "XBIOS_Floprd", "xbiosbind.h", 1u, 20u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 9u, "Flopwr", "XBIOS_Flopwr", "xbiosbind.h", 1u, 20u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 10u, "Flopfmt", "XBIOS_Flopfmt", "xbiosbind.h", 1u, 26u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 12u, "Midiws", "XBIOS_Midiws", "xbiosbind.h", 1u, 8u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 13u, "Mfpint", "XBIOS_Mfpint", "xbiosbind.h", 1u, 8u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 14u, "Iorec", "XBIOS_Iorec", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 15u, "Rsconf", "XBIOS_Rsconf", "xbiosbind.h", 1u, 14u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 16u, "Keytbl", "XBIOS_Keytbl", "xbiosbind.h", 1u, 14u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 17u, "Random", "XBIOS_Random", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 18u, "Protobt", "XBIOS_Protobt", "xbiosbind.h", 1u, 14u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 19u, "Flopver", "XBIOS_Flopver", "xbiosbind.h", 1u, 20u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 20u, "Scrdmp", "XBIOS_Scrdmp", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 21u, "Cursconf", "XBIOS_Cursconf", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 22u, "Settime", "XBIOS_Settime", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 23u, "Gettime", "XBIOS_Gettime", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 24u, "Bioskeys", "XBIOS_Bioskeys", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 25u, "Ikbdws", "XBIOS_Ikbdws", "xbiosbind.h", 1u, 8u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 26u, "Jdisint", "XBIOS_Jdisint", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 27u, "Jenabint", "XBIOS_Jenabint", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 28u, "Giaccess", "XBIOS_Giaccess", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 29u, "Offgibit", "XBIOS_Offgibit", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 30u, "Ongibit", "XBIOS_Ongibit", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 31u, "Xbtimer", "XBIOS_Xbtimer", "xbiosbind.h", 1u, 12u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 32u, "Dosound", "XBIOS_Dosound", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 33u, "Setprt", "XBIOS_Setprt", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 34u, "Kbdvbase", "XBIOS_Kbdvbase", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 35u, "Kbrate", "XBIOS_Kbrate", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 36u, "Prtblk", "XBIOS_Prtblk", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 37u, "Vsync", "XBIOS_Vsync", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 38u, "Supexec", "XBIOS_Supexec", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 39u, "Puntaes", "XBIOS_Puntaes", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 64u, "Blitmode", "XBIOS_Blitmode", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 81u, "EgetShift", "XBIOS_EgetShift", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 83u, "EsetColor", "XBIOS_EsetColor", "xbiosbind.h", 1u, 6u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 88u, "VsetMode", "XBIOS_VsetMode", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 89u, "VgetMonitor", "XBIOS_VgetMonitor", "xbiosbind.h", 1u, 2u, 0u, ATARI_ST_OS_RETURN_WORD },
  { "XBIOS", 14u, 91u, "VgetSize", "XBIOS_VgetSize", "xbiosbind.h", 1u, 4u, 0u, ATARI_ST_OS_RETURN_LONG },
  { "XBIOS", 14u, 93u, "VsetRGB", "XBIOS_VsetRGB", "xbiosbind.h", 1u, 10u, 0u, ATARI_ST_OS_RETURN_VOID },
  { "XBIOS", 14u, 94u, "VgetRGB", "XBIOS_VgetRGB", "xbiosbind.h", 1u, 10u, 0u, ATARI_ST_OS_RETURN_VOID },
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
