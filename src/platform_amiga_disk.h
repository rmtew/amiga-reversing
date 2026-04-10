#ifndef PLATFORM_AMIGA_DISK_H
#define PLATFORM_AMIGA_DISK_H

#include "util_arena.h"

#include <stddef.h>
#include <stdint.h>

typedef struct AmigaDiskAnalysis AmigaDiskAnalysis;

typedef enum AmigaDiskEntryKind {
    AMIGA_DISK_ENTRY_FILE = 1,
    AMIGA_DISK_ENTRY_DIRECTORY = 2,
    AMIGA_DISK_ENTRY_VOLUME = 3
} AmigaDiskEntryKind;

typedef enum AmigaDiskFormatKind {
    AMIGA_DISK_FORMAT_UNKNOWN = 0,
    AMIGA_DISK_FORMAT_DOS = 1,
    AMIGA_DISK_FORMAT_NON_DOS = 2,
    AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_POINTER = 3,
    AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_BLOCK = 4,
    AMIGA_DISK_FORMAT_NON_DOS_BLANK = 5,
    AMIGA_DISK_FORMAT_NON_DOS_BOOTABLE = 6,
    AMIGA_DISK_FORMAT_DOS_CUSTOM_BOOT = 7
} AmigaDiskFormatKind;

typedef struct AmigaDiskExtent {
    uint32_t block_index;
    uint32_t image_offset;
    uint32_t byte_size;
} AmigaDiskExtent;

typedef struct AmigaDiskEntry {
    char *path;
    AmigaDiskAnalysis *owner;
    AmigaDiskEntryKind kind;
    uint32_t byte_size;
    uint32_t header_block;
    AmigaDiskExtent *extents;
    size_t extent_count;
    size_t extent_capacity;
} AmigaDiskEntry;

struct AmigaDiskAnalysis {
    uint32_t image_size;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t root_block;
    AmigaDiskFormatKind format_kind;
    uint8_t is_dos;
    uint8_t dos_flags;
    AmigaDiskEntry *entries;
    size_t entry_count;
    size_t entry_capacity;
    Arena *arena;
};

const char *amiga_disk_format_kind_name(AmigaDiskFormatKind kind);
int amiga_disk_analysis_create(AmigaDiskAnalysis *analysis);
void amiga_disk_analysis_destroy(AmigaDiskAnalysis *analysis);
int amiga_disk_analyze_image(const char *path, AmigaDiskAnalysis *out_analysis, char *error_buf, size_t error_buf_size);
int amiga_disk_analyze_buffer(const unsigned char *data, size_t size, AmigaDiskAnalysis *out_analysis, char *error_buf,
    size_t error_buf_size);

#endif
