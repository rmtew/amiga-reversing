#ifndef PLATFORM_AMIGA_BOOTLOADER_ANALYSIS_H
#define PLATFORM_AMIGA_BOOTLOADER_ANALYSIS_H

#include "platform_amiga_disk.h"

int amiga_disk_analyze_bootloader_stage_bytes(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage,
    const unsigned char *data, size_t size);
int amiga_disk_append_bootloader_read_setup(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage);

#endif
