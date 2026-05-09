#ifndef PLATFORM_AMIGA_DISK_H
#define PLATFORM_AMIGA_DISK_H

#include "generated/amiga_disk_file_runtime.h"
#include "m68k_diagnostics.h"
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
    char *name;
    char *path;
    char *comment;
    AmigaDiskAnalysis *owner;
    AmigaDiskEntryKind kind;
    uint32_t byte_size;
    uint32_t header_block;
    uint32_t protection;
    uint32_t date_days;
    uint32_t date_mins;
    uint32_t date_ticks;
    uint32_t hash_chain;
    uint32_t parent;
    uint8_t checksum_valid;
    AmigaDiskExtent *extents;
    size_t extent_count;
    size_t extent_capacity;
    uint32_t *extension_blocks;
    size_t extension_block_count;
    size_t extension_block_capacity;
} AmigaDiskEntry;

typedef struct AmigaDiskBlockUsageSummary {
    uint32_t boot;
    uint32_t root;
    uint32_t bitmap;
    uint32_t dir_header;
    uint32_t file_header;
    uint32_t data;
    uint32_t extension;
    uint32_t free_blocks;
    uint32_t allocated_orphan;
    uint32_t unknown;
} AmigaDiskBlockUsageSummary;

typedef struct AmigaDiskAsciiString {
    uint32_t offset;
    char *text;
} AmigaDiskAsciiString;

typedef struct AmigaDiskTrackInfo {
    uint32_t track;
    uint32_t cylinder;
    uint32_t head;
    uint32_t first_block;
    uint32_t byte_offset;
    uint32_t byte_length;
    uint8_t empty;
    double entropy;
    uint32_t m68k_pattern_count;
    uint8_t has_code;
    AmigaDiskAsciiString *ascii_strings;
    size_t ascii_string_count;
    size_t ascii_string_capacity;
} AmigaDiskTrackInfo;

typedef struct AmigaDiskTrackSpan {
    uint32_t start_track;
    uint32_t end_track;
} AmigaDiskTrackSpan;

typedef struct AmigaDiskBootloaderStage {
    char *name;
    uint32_t base_addr;
    uint32_t entry_addr;
    uint32_t size;
    uint32_t disk_offset;
    uint32_t byte_length;
    uint32_t instruction_addr;
    uint32_t reachable_instruction_count;
    uint8_t materialized;
    uint8_t has_disk_read;
    struct AmigaDiskBootloaderHardwareAccess *hardware_accesses;
    size_t hardware_access_count;
    size_t hardware_access_capacity;
    struct AmigaDiskBootloaderReadSetup *read_setups;
    size_t read_setup_count;
    size_t read_setup_capacity;
    struct AmigaDiskBootloaderDecodeRegion *decode_regions;
    size_t decode_region_count;
    size_t decode_region_capacity;
} AmigaDiskBootloaderStage;

typedef struct AmigaDiskRawTrackSourceSpan {
    uint32_t start_track;
    uint32_t end_track;
    uint32_t start_byte_offset;
    uint32_t byte_length;
} AmigaDiskRawTrackSourceSpan;

typedef enum AmigaDiskBootloaderHardwareAccessKind {
    AMIGA_DISK_BOOTLOADER_HARDWARE_ACCESS_READ = 1,
    AMIGA_DISK_BOOTLOADER_HARDWARE_ACCESS_WRITE = 2
} AmigaDiskBootloaderHardwareAccessKind;

typedef struct AmigaDiskBootloaderHardwareAccess {
    uint32_t instruction_addr;
    uint8_t access_kind;
    char *access;
    uint32_t width_bits;
    uint32_t address;
    uint16_t symbol_id;
    char *symbol;
    uint8_t has_value;
    uint32_t value;
} AmigaDiskBootloaderHardwareAccess;

typedef struct AmigaDiskBootloaderReadSetup {
    uint32_t instruction_addr;
    uint8_t has_buffer_addr;
    uint32_t buffer_addr;
    uint8_t has_sync_word;
    uint32_t sync_word;
    uint8_t has_dsklen_value;
    uint32_t dsklen_value;
    uint8_t has_dsklen_dma_byte_length;
    uint32_t dsklen_dma_byte_length;
    uint8_t dsklen_dma_enabled;
    uint8_t dsklen_write;
    uint8_t has_dma_byte_length;
    uint32_t dma_byte_length;
    uint8_t has_drive;
    uint32_t drive;
    uint8_t has_cylinder;
    uint32_t cylinder;
    uint8_t has_head;
    uint32_t head;
    uint8_t has_track;
    uint32_t track;
    uint32_t *adkcon_values;
    size_t adkcon_value_count;
    size_t adkcon_value_capacity;
    uint32_t *dmacon_values;
    size_t dmacon_value_count;
    size_t dmacon_value_capacity;
    uint8_t has_wait_loop_addr;
    uint32_t wait_loop_addr;
    uint8_t has_buffer_scan_addr;
    uint32_t buffer_scan_addr;
} AmigaDiskBootloaderReadSetup;

typedef struct AmigaDiskBootloaderDecodeRegion {
    uint32_t instruction_addr;
    uint8_t has_input_buffer_addr;
    uint32_t input_buffer_addr;
    uint8_t has_input_consumed_byte_offset;
    uint32_t input_consumed_byte_offset;
    uint8_t has_input_consumed_byte_length;
    uint32_t input_consumed_byte_length;
    char *input_source_kind;
    char *input_required_source_kind;
    AmigaDiskRawTrackSourceSpan *input_source_candidate_spans;
    size_t input_source_candidate_span_count;
    size_t input_source_candidate_span_capacity;
    uint8_t has_input_required_byte_length;
    uint32_t input_required_byte_length;
    uint32_t input_concrete_byte_count;
    uint8_t input_complete;
    uint8_t input_materializable;
    char *input_missing_reason;
    uint8_t has_output_base_addr;
    uint32_t output_base_addr;
    uint8_t has_output_addr;
    uint32_t output_addr;
    uint8_t has_byte_length;
    uint32_t byte_length;
    uint32_t write_loop_addr;
} AmigaDiskBootloaderDecodeRegion;

struct AmigaDiskAnalysis {
    uint32_t image_size;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t root_block;
    char *volume_name;
    uint32_t root_hash_table[AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_ENTRIES];
    uint32_t root_bitmap_pages[AMIGA_DISK_FILE_CONSTRAINTS_ROOT_BITMAP_PAGES_COUNT];
    uint32_t root_bitmap_page_count;
    int32_t root_bitmap_valid_flag;
    uint32_t root_date_days;
    uint32_t root_date_mins;
    uint32_t root_date_ticks;
    uint32_t volume_date_days;
    uint32_t volume_date_mins;
    uint32_t volume_date_ticks;
    uint32_t creation_date_days;
    uint32_t creation_date_mins;
    uint32_t creation_date_ticks;
    uint8_t root_checksum_valid;
    uint8_t bitmap_checksum_valid;
    uint32_t bitmap_free_blocks;
    uint32_t bitmap_allocated_blocks;
    double bitmap_percent_used;
    AmigaDiskBlockUsageSummary block_usage;
    uint32_t *orphan_blocks;
    size_t orphan_block_count;
    size_t orphan_block_capacity;
    char boot_magic[4];
    uint32_t boot_checksum;
    uint32_t boot_expected_checksum;
    uint32_t bootcode_size;
    double bootcode_entropy;
    AmigaDiskFormatKind format_kind;
    uint8_t is_dos;
    uint8_t dos_flags;
    uint8_t boot_checksum_valid;
    uint8_t bootcode_has_code;
    uint32_t track_size_bytes;
    uint32_t total_tracks;
    uint32_t non_empty_tracks;
    AmigaDiskTrackInfo *tracks;
    size_t track_count;
    size_t track_capacity;
    AmigaDiskAsciiString *boot_ascii_strings;
    size_t boot_ascii_string_count;
    size_t boot_ascii_string_capacity;
    uint32_t *candidate_code_tracks;
    size_t candidate_code_track_count;
    size_t candidate_code_track_capacity;
    uint32_t *high_entropy_tracks;
    size_t high_entropy_track_count;
    size_t high_entropy_track_capacity;
    AmigaDiskTrackSpan *nonempty_track_spans;
    size_t nonempty_track_span_count;
    size_t nonempty_track_span_capacity;
    uint32_t nonempty_head0_tracks;
    uint32_t nonempty_head1_tracks;
    AmigaDiskBootloaderStage *bootloader_stages;
    size_t bootloader_stage_count;
    size_t bootloader_stage_capacity;
    AmigaDiskEntry *entries;
    size_t entry_count;
    size_t entry_capacity;
    Arena *arena;
};

const char *amiga_disk_format_kind_name(AmigaDiskFormatKind kind);
int amiga_disk_analysis_create(AmigaDiskAnalysis *analysis);
void amiga_disk_analysis_destroy(AmigaDiskAnalysis *analysis);
int amiga_disk_analyze_image(const char *path, AmigaDiskAnalysis *out_analysis, M68kDiagSink diagnostics);
int amiga_disk_analyze_buffer(const unsigned char *data, size_t size, AmigaDiskAnalysis *out_analysis,
    M68kDiagSink diagnostics);

#endif
