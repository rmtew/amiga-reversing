#ifndef PLATFORM_ATARI_ST_DISK_H
#define PLATFORM_ATARI_ST_DISK_H

#include <stddef.h>
#include <stdint.h>

typedef enum AtariStDiskEntryKind {
    ATARI_ST_DISK_ENTRY_FILE = 1,
    ATARI_ST_DISK_ENTRY_DIRECTORY = 2,
    ATARI_ST_DISK_ENTRY_VOLUME_LABEL = 3
} AtariStDiskEntryKind;

typedef struct AtariStDiskExtent {
    uint32_t image_offset;
    uint32_t byte_size;
    uint16_t cluster_index;
} AtariStDiskExtent;

typedef struct AtariStDiskEntry {
    char *path;
    AtariStDiskEntryKind kind;
    uint32_t file_size;
    uint16_t first_cluster;
    uint8_t attributes;
    uint8_t is_executable_candidate;
    AtariStDiskExtent *extents;
    size_t extent_count;
} AtariStDiskEntry;

typedef struct AtariStDiskAnalysis {
    uint32_t image_size;
    uint16_t bytes_per_sector;
    uint8_t sectors_per_cluster;
    uint16_t reserved_sector_count;
    uint8_t fat_count;
    uint16_t root_entry_count;
    uint16_t total_sectors;
    uint16_t sectors_per_fat;
    uint16_t sectors_per_track;
    uint16_t side_count;
    AtariStDiskEntry *entries;
    size_t entry_count;
} AtariStDiskAnalysis;

void atari_st_disk_analysis_init(AtariStDiskAnalysis *analysis);
void atari_st_disk_analysis_free(AtariStDiskAnalysis *analysis);
int atari_st_disk_analyze_image(const char *path, AtariStDiskAnalysis *out_analysis, char *error_buf,
    size_t error_buf_size);
int atari_st_disk_analyze_buffer(const unsigned char *data, size_t size, AtariStDiskAnalysis *out_analysis,
    char *error_buf, size_t error_buf_size);

#endif
