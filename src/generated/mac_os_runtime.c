/* Generated Classic Mac OS runtime metadata from MPW includes. Do not edit directly. */
#include "generated/mac_os_runtime.h"

#include <string.h>

static const MacOsRecordInfo g_mac_os_records[] = {
  { "Point", 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 483u, 487u, 0u, 2u },
  { "Rect", 8u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 490u, 499u, 2u, 6u },
  { "EventRecord", 16u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 131u, 138u, 8u, 5u },
  { "HVolumeParam", 122u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 841u, 875u, 13u, 32u },
  { "QDGlobals", 206u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1307u, 1319u, 45u, 10u },
  { "WindowRecord", 156u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 516u, 535u, 55u, 17u },
  { "DCtlEntry", 40u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 144u, 157u, 72u, 11u },
  { "SysEnvRec", 16u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 705u, 716u, 83u, 9u },
};

static const MacOsRecordFieldInfo g_mac_os_record_fields[] = {
  { "Point", "v", "1", "ds.w", 0u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 484u },
  { "Point", "h", "1", "ds.w", 2u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 485u },
  { "Rect", "top", "1", "ds.w", 0u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 491u },
  { "Rect", "left", "1", "ds.w", 2u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 492u },
  { "Rect", "bottom", "1", "ds.w", 4u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 493u },
  { "Rect", "right", "1", "ds.w", 6u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 494u },
  { "Rect", "topLeft", "Point", "ds", 0u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 496u },
  { "Rect", "botRight", "Point", "ds", 4u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", 497u },
  { "EventRecord", "what", "1", "ds.w", 0u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 132u },
  { "EventRecord", "message", "1", "ds.l", 2u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 133u },
  { "EventRecord", "when", "1", "ds.l", 6u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 134u },
  { "EventRecord", "where", "Point", "ds", 10u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 135u },
  { "EventRecord", "modifiers", "1", "ds.w", 14u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 136u },
  { "HVolumeParam", "qLink", "1", "ds.l", 0u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 842u },
  { "HVolumeParam", "qType", "1", "ds.w", 4u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 843u },
  { "HVolumeParam", "ioTrap", "1", "ds.w", 6u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 844u },
  { "HVolumeParam", "ioCmdAddr", "1", "ds.l", 8u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 845u },
  { "HVolumeParam", "ioCompletion", "1", "ds.l", 12u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 846u },
  { "HVolumeParam", "ioResult", "1", "ds.w", 16u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 847u },
  { "HVolumeParam", "ioNamePtr", "1", "ds.l", 18u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 848u },
  { "HVolumeParam", "ioVRefNum", "1", "ds.w", 22u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 849u },
  { "HVolumeParam", "filler2", "1", "ds.l", 24u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 850u },
  { "HVolumeParam", "ioVolIndex", "1", "ds.w", 28u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 851u },
  { "HVolumeParam", "ioVCrDate", "1", "ds.l", 30u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 852u },
  { "HVolumeParam", "ioVLsMod", "1", "ds.l", 34u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 853u },
  { "HVolumeParam", "ioVAtrb", "1", "ds.w", 38u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 854u },
  { "HVolumeParam", "ioVNmFls", "1", "ds.w", 40u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 855u },
  { "HVolumeParam", "ioVBitMap", "1", "ds.w", 42u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 856u },
  { "HVolumeParam", "ioAllocPtr", "1", "ds.w", 44u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 857u },
  { "HVolumeParam", "ioVNmAlBlks", "1", "ds.w", 46u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 858u },
  { "HVolumeParam", "ioVAlBlkSiz", "1", "ds.l", 48u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 859u },
  { "HVolumeParam", "ioVClpSiz", "1", "ds.l", 52u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 860u },
  { "HVolumeParam", "ioAlBlSt", "1", "ds.w", 56u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 861u },
  { "HVolumeParam", "ioVNxtCNID", "1", "ds.l", 58u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 862u },
  { "HVolumeParam", "ioVFrBlk", "1", "ds.w", 62u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 863u },
  { "HVolumeParam", "ioVSigWord", "1", "ds.w", 64u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 864u },
  { "HVolumeParam", "ioVDrvInfo", "1", "ds.w", 66u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 865u },
  { "HVolumeParam", "ioVDRefNum", "1", "ds.w", 68u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 866u },
  { "HVolumeParam", "ioVFSID", "1", "ds.w", 70u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 867u },
  { "HVolumeParam", "ioVBkUp", "1", "ds.l", 72u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 868u },
  { "HVolumeParam", "ioVSeqNum", "1", "ds.w", 76u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 869u },
  { "HVolumeParam", "ioVWrCnt", "1", "ds.l", 78u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 870u },
  { "HVolumeParam", "ioVFilCnt", "1", "ds.l", 82u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 871u },
  { "HVolumeParam", "ioVDirCnt", "1", "ds.l", 86u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 872u },
  { "HVolumeParam", "ioVFndrInfo", "8", "ds.l", 90u, 32u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 873u },
  { "QDGlobals", "privates", "76", "ds.b", 0u, 76u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1308u },
  { "QDGlobals", "randSeed", "1", "ds.l", 76u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1309u },
  { "QDGlobals", "screenBits", "BitMap", "ds", 80u, 14u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1310u },
  { "QDGlobals", "arrow", "Cursor", "ds", 94u, 68u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1311u },
  { "QDGlobals", "dkGray", "Pattern", "ds", 162u, 8u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1312u },
  { "QDGlobals", "ltGray", "Pattern", "ds", 170u, 8u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1313u },
  { "QDGlobals", "gray", "Pattern", "ds", 178u, 8u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1314u },
  { "QDGlobals", "black", "Pattern", "ds", 186u, 8u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1315u },
  { "QDGlobals", "white", "Pattern", "ds", 194u, 8u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1316u },
  { "QDGlobals", "thePort", "1", "ds.l", 202u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Quickdraw.a", 1317u },
  { "WindowRecord", "port", "GrafPort", "ds", 0u, 108u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 517u },
  { "WindowRecord", "windowKind", "1", "ds.w", 108u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 518u },
  { "WindowRecord", "visible", "1", "ds.b", 110u, 1u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 519u },
  { "WindowRecord", "hilited", "1", "ds.b", 111u, 1u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 520u },
  { "WindowRecord", "goAwayFlag", "1", "ds.b", 112u, 1u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 521u },
  { "WindowRecord", "spareFlag", "1", "ds.b", 113u, 1u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 522u },
  { "WindowRecord", "strucRgn", "1", "ds.l", 114u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 523u },
  { "WindowRecord", "contRgn", "1", "ds.l", 118u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 524u },
  { "WindowRecord", "updateRgn", "1", "ds.l", 122u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 525u },
  { "WindowRecord", "windowDefProc", "1", "ds.l", 126u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 526u },
  { "WindowRecord", "dataHandle", "1", "ds.l", 130u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 527u },
  { "WindowRecord", "titleHandle", "1", "ds.l", 134u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 528u },
  { "WindowRecord", "titleWidth", "1", "ds.w", 138u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 529u },
  { "WindowRecord", "controlList", "1", "ds.l", 140u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 530u },
  { "WindowRecord", "nextWindow", "1", "ds.l", 144u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 531u },
  { "WindowRecord", "windowPic", "1", "ds.l", 148u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 532u },
  { "WindowRecord", "refCon", "1", "ds.l", 152u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacWindows.a", 533u },
  { "DCtlEntry", "dCtlDriver", "1", "ds.l", 0u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 145u },
  { "DCtlEntry", "dCtlFlags", "1", "ds.w", 4u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 146u },
  { "DCtlEntry", "dCtlQHdr", "QHdr", "ds", 6u, 10u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 147u },
  { "DCtlEntry", "dCtlPosition", "1", "ds.l", 16u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 148u },
  { "DCtlEntry", "dCtlStorage", "1", "ds.l", 20u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 149u },
  { "DCtlEntry", "dCtlRefNum", "1", "ds.w", 24u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 150u },
  { "DCtlEntry", "dCtlCurTicks", "1", "ds.l", 26u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 151u },
  { "DCtlEntry", "dCtlWindow", "1", "ds.l", 30u, 4u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 152u },
  { "DCtlEntry", "dCtlDelay", "1", "ds.w", 34u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 153u },
  { "DCtlEntry", "dCtlEMask", "1", "ds.w", 36u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 154u },
  { "DCtlEntry", "dCtlMenu", "1", "ds.w", 38u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Devices.a", 155u },
  { "SysEnvRec", "environsVersion", "1", "ds.w", 0u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 706u },
  { "SysEnvRec", "machineType", "1", "ds.w", 2u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 707u },
  { "SysEnvRec", "systemVersion", "1", "ds.w", 4u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 708u },
  { "SysEnvRec", "processor", "1", "ds.w", 6u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 709u },
  { "SysEnvRec", "hasFPU", "1", "ds.b", 8u, 1u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 710u },
  { "SysEnvRec", "hasColorQD", "1", "ds.b", 9u, 1u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 711u },
  { "SysEnvRec", "keyBoardType", "1", "ds.w", 10u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 712u },
  { "SysEnvRec", "atDrvrVersNum", "1", "ds.w", 12u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 713u },
  { "SysEnvRec", "sysVRefNum", "1", "ds.w", 14u, 2u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/OSUtils.a", 714u },
};

static const MacOsCallInfo g_mac_os_calls[] = {
  { "_GetResource", "Resources", MAC_OS_CALL_KIND_OPWORD, 43424u, 0u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Resources.a", 425u, "EXTERN_API( Handle ) GetResource( ResType theType, short theID) ONEWORDINLINE(0xA9A0);", "ext/macos_includes/mpw_gm/Interfaces/CIncludes/Resources.h", 396u, NULL, NULL },
  { "_WaitNextEvent", "Events", MAC_OS_CALL_KIND_OPWORD, 43104u, 0u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a", 475u, "EXTERN_API( Boolean ) WaitNextEvent( EventMask eventMask, EventRecord * theEvent, UInt32 sleep, RgnHandle mouseRgn) /* can be NULL */ ONEWORDINLINE(0xA860);", "ext/macos_includes/mpw_gm/Interfaces/CIncludes/Events.h", 530u, NULL, NULL },
  { "_UnloadSeg", "SegmentLoader", MAC_OS_CALL_KIND_OPWORD, 43505u, 0u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/SegLoad.a", 134u, "EXTERN_API( void ) UnloadSeg(void * routineAddr) ONEWORDINLINE(0xA9F1);", "ext/macos_includes/mpw_gm/Interfaces/CIncludes/SegLoad.h", 163u, NULL, NULL },
  { "_PBHGetVInfoSync", "FileManager", MAC_OS_CALL_KIND_OPWORD, 41479u, 0u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a", 3671u, "EXTERN_API( OSErr ) PBHGetVInfoSync(HParmBlkPtr paramBlock) ONEWORDINLINE(0xA207);", "ext/macos_includes/mpw_gm/Interfaces/CIncludes/Files.h", 3049u, "A0", "D0" },
  { "_NumToString", "NumberFormatting", MAC_OS_CALL_KIND_PACKAGE_MACRO, 0u, 43502u, "ext/macos_includes/mpw_gm/Interfaces/AIncludes/NumberFormatting.a", 136u, "EXTERN_API( void ) NumToString( long theNum, Str255 theString);", "ext/macos_includes/mpw_gm/Interfaces/CIncludes/NumberFormatting.h", 170u, NULL, NULL },
};

const MacOsRecordInfo *mac_os_find_record(const char *name) {
  size_t index;
  if (name == NULL) return NULL;
  for (index = 0U; index < MAC_OS_RECORD_COUNT; ++index) {
    if (strcmp(g_mac_os_records[index].name, name) == 0) return &g_mac_os_records[index];
  }
  return NULL;
}

const MacOsRecordFieldInfo *mac_os_find_record_field(const char *record_name, const char *field_name) {
  size_t index;
  if (record_name == NULL || field_name == NULL) return NULL;
  for (index = 0U; index < sizeof(g_mac_os_record_fields) / sizeof(g_mac_os_record_fields[0]); ++index) {
    const MacOsRecordFieldInfo *field = &g_mac_os_record_fields[index];
    if (strcmp(field->record_name, record_name) == 0 && strcmp(field->name, field_name) == 0) return field;
  }
  return NULL;
}

const MacOsCallInfo *mac_os_find_call_by_name(const char *name) {
  size_t index;
  if (name == NULL) return NULL;
  for (index = 0U; index < MAC_OS_CALL_COUNT; ++index) {
    if (strcmp(g_mac_os_calls[index].name, name) == 0) return &g_mac_os_calls[index];
  }
  return NULL;
}

const MacOsCallInfo *mac_os_find_call_by_opword(uint16_t opword) {
  size_t index;
  for (index = 0U; index < MAC_OS_CALL_COUNT; ++index) {
    if (g_mac_os_calls[index].kind == MAC_OS_CALL_KIND_OPWORD && g_mac_os_calls[index].opword == opword) return &g_mac_os_calls[index];
  }
  return NULL;
}
