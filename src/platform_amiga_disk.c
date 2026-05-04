#include "platform_amiga_disk.h"
#include "platform_amiga_bootloader_analysis.h"
#include "generated/amiga_disk_file_runtime.h"
#include "m68k_ir_codec.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define AMIGA_DISK_ANALYSIS_ARENA_SIZE 16384U

static void disk_diag_error(M68kDiagSink diagnostics, const char *message) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_DISK_FAILED, message);
}

static int analysis_join_path(AmigaDiskAnalysis *analysis, const char *base, const char *name, char **out_path) {
    size_t base_len;
    size_t name_len;
    size_t total;
    char *path;
    Arena *arena = analysis != NULL ? analysis->arena : NULL;
    if (arena == NULL || base == NULL || name == NULL || out_path == NULL) return -1;
    base_len = strlen(base);
    name_len = strlen(name);
    total = base_len + name_len + (base_len != 0U ? 2U : 1U);
    path = (char *)arena_alloc(arena, total);
    if (path == NULL) return -1;
    if (base_len != 0U) {
        memcpy(path, base, base_len);
        path[base_len] = '/';
        memcpy(path + base_len + 1U, name, name_len + 1U);
    } else {
        memcpy(path, name, name_len + 1U);
    }
    *out_path = path;
    return 0;
}

static void *analysis_grow_array(AmigaDiskAnalysis *analysis, void *items, size_t count, size_t *capacity,
    size_t item_size) {
    size_t next_capacity;
    void *grown;
    Arena *arena = analysis != NULL ? analysis->arena : NULL;
    if (arena == NULL) return NULL;
    if (count < *capacity) return items;
    next_capacity = (*capacity == 0U) ? 4U : (*capacity * 2U);
    grown = arena_realloc_copy(arena, items, count * item_size, next_capacity * item_size);
    if (grown == NULL) return NULL;
    *capacity = next_capacity;
    return grown;
}

typedef struct DiskContext {
    const unsigned char *data;
    size_t size;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t root_block;
    uint8_t dos_flags;
    int is_ffs;
} DiskContext;

typedef enum AmigaDiskBlockUsageKind {
    AMIGA_DISK_BLOCK_USAGE_UNKNOWN = 0,
    AMIGA_DISK_BLOCK_USAGE_BOOT,
    AMIGA_DISK_BLOCK_USAGE_ROOT,
    AMIGA_DISK_BLOCK_USAGE_BITMAP,
    AMIGA_DISK_BLOCK_USAGE_DIR_HEADER,
    AMIGA_DISK_BLOCK_USAGE_FILE_HEADER,
    AMIGA_DISK_BLOCK_USAGE_DATA,
    AMIGA_DISK_BLOCK_USAGE_EXTENSION,
    AMIGA_DISK_BLOCK_USAGE_FREE,
    AMIGA_DISK_BLOCK_USAGE_ALLOCATED_ORPHAN
} AmigaDiskBlockUsageKind;

const char *amiga_disk_format_kind_name(AmigaDiskFormatKind kind) {
    switch (kind) {
        case AMIGA_DISK_FORMAT_DOS:
            return "dos";
        case AMIGA_DISK_FORMAT_NON_DOS:
            return "non-dos";
        case AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_POINTER:
            return "dos-invalid-root-pointer";
        case AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_BLOCK:
            return "dos-invalid-root-block";
        case AMIGA_DISK_FORMAT_NON_DOS_BLANK:
            return "non-dos-blank";
        case AMIGA_DISK_FORMAT_NON_DOS_BOOTABLE:
            return "non-dos-bootable";
        case AMIGA_DISK_FORMAT_DOS_CUSTOM_BOOT:
            return "dos-custom-boot";
        default:
            return "unknown";
    }
}

static uint32_t read_u32be(const unsigned char *data, size_t offset) {
    return ((uint32_t)data[offset] << 24)
        | ((uint32_t)data[offset + 1U] << 16)
        | ((uint32_t)data[offset + 2U] << 8)
        | (uint32_t)data[offset + 3U];
}

static uint32_t read_u16be(const unsigned char *data, size_t offset) {
    return ((uint32_t)data[offset] << 8) | (uint32_t)data[offset + 1U];
}

static int32_t read_s32be(const unsigned char *data, size_t offset) {
    return (int32_t)read_u32be(data, offset);
}

static uint8_t block_checksum_valid(const unsigned char *block, uint32_t block_size) {
    uint32_t total = 0;
    uint32_t i;
    for (i = 0; i < block_size / 4U; ++i) {
        total += read_u32be(block, (size_t)i * 4U);
    }
    return total == 0U ? 1U : 0U;
}

static uint32_t compute_boot_checksum(const unsigned char *data, uint32_t block_size) {
    uint32_t longword_count = (block_size * AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS) / 4U;
    uint64_t total = 0U;
    uint32_t i;
    for (i = 0; i < longword_count; ++i) {
        if (i == 1U) continue;
        total += read_u32be(data, (size_t)i * 4U);
        if (total > 0xFFFFFFFFULL) total = (total + 1U) & 0xFFFFFFFFULL;
    }
    return (uint32_t)(~total);
}

static double shannon_entropy(const unsigned char *data, size_t size) {
    uint32_t freq[256] = {0};
    size_t i;
    double entropy = 0.0;
    if (data == NULL || size == 0U) return 0.0;
    for (i = 0; i < size; ++i) freq[data[i]] += 1U;
    for (i = 0; i < 256U; ++i) {
        double probability;
        if (freq[i] == 0U) continue;
        probability = (double)freq[i] / (double)size;
        entropy -= probability * (log(probability) / log(2.0));
    }
    return floor(entropy * 100.0 + 0.5) / 100.0;
}

static int block_range_has_nonzero(const unsigned char *data, size_t start, size_t end) {
    size_t i;
    for (i = start; i < end; ++i) {
        if (data[i] != 0U) return 1;
    }
    return 0;
}

static int boot_block_has_code(const DiskContext *ctx) {
    size_t boot_block_bytes = (size_t)ctx->block_size * AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS;
    if (boot_block_bytes <= AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET + 4U) return 0;
    return block_range_has_nonzero(ctx->data, AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET + 4U, boot_block_bytes);
}

static int block_offset(const DiskContext *ctx, uint32_t block_index, size_t *out_offset) {
    if (block_index >= ctx->total_blocks) return -1;
    *out_offset = (size_t)block_index * ctx->block_size;
    if (*out_offset + ctx->block_size > ctx->size) return -1;
    return 0;
}

static int read_bcpl_name(const unsigned char *block, size_t len_offset, size_t max_length, char *out_name,
    size_t out_name_size) {
    uint8_t length = block[len_offset];
    if (length > max_length || (size_t)length + 1U > out_name_size) return -1;
    memcpy(out_name, block + len_offset + 1U, length);
    out_name[length] = '\0';
    return 0;
}

static int disk_has_valid_dos_filesystem(const DiskContext *ctx) {
    uint32_t root_block_index;
    size_t root_offset = 0U;
    const unsigned char *root_block;
    char volume_name[AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_MAX_LENGTH + 1U];
    if (ctx == NULL || ctx->data == NULL || ctx->size < AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET + 4U)
        return 0;
    if (memcmp(ctx->data + AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_MAGIC_OFFSET, "DOS", 3) != 0) return 0;
    root_block_index = read_u32be(ctx->data, AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET);
    if (block_offset(ctx, root_block_index, &root_offset) != 0) return 0;
    root_block = ctx->data + root_offset;
    return read_u32be(root_block, 0) == AMIGA_DISK_FILE_BLOCK_TYPE_T_HEADER &&
        read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_SEC_TYPE_OFFSET) ==
            AMIGA_DISK_FILE_CONSTRAINTS_SEC_TYPE_ROOT &&
        read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_SIZE_OFFSET) ==
            AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_ENTRIES &&
        read_bcpl_name(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_LEN_OFFSET,
            AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_MAX_LENGTH, volume_name, sizeof(volume_name)) == 0;
}

static int append_extent(AmigaDiskAnalysis *analysis, AmigaDiskEntry *entry, uint32_t block_index, uint32_t image_offset,
    uint32_t byte_size) {
    AmigaDiskExtent *grown = (AmigaDiskExtent *)analysis_grow_array(analysis, entry->extents, entry->extent_count,
        &entry->extent_capacity, sizeof(*entry->extents));
    if (grown == NULL) return -1;
    entry->extents = grown;
    entry->extents[entry->extent_count].block_index = block_index;
    entry->extents[entry->extent_count].image_offset = image_offset;
    entry->extents[entry->extent_count].byte_size = byte_size;
    entry->extent_count += 1U;
    return 0;
}

static int append_extension_block(AmigaDiskAnalysis *analysis, AmigaDiskEntry *entry, uint32_t block_index) {
    uint32_t *grown = (uint32_t *)analysis_grow_array(analysis, entry->extension_blocks, entry->extension_block_count,
        &entry->extension_block_capacity, sizeof(*entry->extension_blocks));
    if (grown == NULL) return -1;
    entry->extension_blocks = grown;
    entry->extension_blocks[entry->extension_block_count] = block_index;
    entry->extension_block_count += 1U;
    return 0;
}

static int append_orphan_block(AmigaDiskAnalysis *analysis, uint32_t block_index) {
    uint32_t *grown = (uint32_t *)analysis_grow_array(analysis, analysis->orphan_blocks, analysis->orphan_block_count,
        &analysis->orphan_block_capacity, sizeof(*analysis->orphan_blocks));
    if (grown == NULL) return -1;
    analysis->orphan_blocks = grown;
    analysis->orphan_blocks[analysis->orphan_block_count] = block_index;
    analysis->orphan_block_count += 1U;
    return 0;
}

static int append_track_ascii_string(AmigaDiskAnalysis *analysis, AmigaDiskTrackInfo *track, uint32_t offset,
    const char *text, size_t text_len) {
    AmigaDiskAsciiString *grown;
    char *copy;
    if (track->ascii_string_count >= AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_MAX_TRACK_ASCII_STRINGS) return 0;
    grown = (AmigaDiskAsciiString *)analysis_grow_array(analysis, track->ascii_strings, track->ascii_string_count,
        &track->ascii_string_capacity, sizeof(*track->ascii_strings));
    if (grown == NULL) return -1;
    track->ascii_strings = grown;
    copy = (char *)arena_alloc(analysis->arena, text_len + 1U);
    if (copy == NULL) return -1;
    memcpy(copy, text, text_len);
    copy[text_len] = '\0';
    track->ascii_strings[track->ascii_string_count].offset = offset;
    track->ascii_strings[track->ascii_string_count].text = copy;
    track->ascii_string_count += 1U;
    return 0;
}

static int append_boot_ascii_string(AmigaDiskAnalysis *analysis, uint32_t offset, const char *text, size_t text_len) {
    AmigaDiskAsciiString *grown;
    char *copy;
    if (analysis->boot_ascii_string_count >= AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_MAX_BOOT_ASCII_STRINGS) return 0;
    grown = (AmigaDiskAsciiString *)analysis_grow_array(analysis, analysis->boot_ascii_strings,
        analysis->boot_ascii_string_count, &analysis->boot_ascii_string_capacity, sizeof(*analysis->boot_ascii_strings));
    if (grown == NULL) return -1;
    analysis->boot_ascii_strings = grown;
    copy = (char *)arena_alloc(analysis->arena, text_len + 1U);
    if (copy == NULL) return -1;
    memcpy(copy, text, text_len);
    copy[text_len] = '\0';
    analysis->boot_ascii_strings[analysis->boot_ascii_string_count].offset = offset;
    analysis->boot_ascii_strings[analysis->boot_ascii_string_count].text = copy;
    analysis->boot_ascii_string_count += 1U;
    return 0;
}

static int scan_ascii_strings(AmigaDiskAnalysis *analysis, AmigaDiskTrackInfo *track, const unsigned char *data,
    size_t size, uint32_t base_offset, uint32_t min_length) {
    size_t i;
    size_t start = 0U;
    size_t length = 0U;
    for (i = 0; i < size; ++i) {
        if (data[i] >= 0x20U && data[i] <= 0x7EU) {
            if (length == 0U) start = i;
            length += 1U;
            continue;
        }
        if (length >= min_length) {
            if (track != NULL) {
                if (append_track_ascii_string(analysis, track, (uint32_t)start, (const char *)(data + start), length) != 0)
                    return -1;
            } else if (append_boot_ascii_string(analysis, base_offset + (uint32_t)start, (const char *)(data + start), length) != 0) {
                return -1;
            }
        }
        length = 0U;
    }
    if (length >= min_length) {
        if (track != NULL) return append_track_ascii_string(analysis, track, (uint32_t)start, (const char *)(data + start), length);
        return append_boot_ascii_string(analysis, base_offset + (uint32_t)start, (const char *)(data + start), length);
    }
    return 0;
}

static int is_m68k_signature_word(uint32_t word) {
    switch (word) {
        case AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_M68K_SIGNATURE_RTS:
        case AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_M68K_SIGNATURE_RTE:
        case AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_M68K_SIGNATURE_NOP:
        case AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_M68K_SIGNATURE_STOP:
        case AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_M68K_SIGNATURE_JMP_ABS:
        case AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_M68K_SIGNATURE_JSR_ABS:
            return 1;
        default:
            return 0;
    }
}

static uint32_t count_m68k_signature_words(const unsigned char *data, size_t size) {
    uint32_t count = 0U;
    size_t i;
    for (i = 0; i + 1U < size; i += 2U) {
        if (is_m68k_signature_word(read_u16be(data, i))) count += 1U;
    }
    return count;
}

static int append_u32_array(AmigaDiskAnalysis *analysis, uint32_t **items, size_t *count, size_t *capacity, uint32_t value) {
    uint32_t *grown = (uint32_t *)analysis_grow_array(analysis, *items, *count, capacity, sizeof(**items));
    if (grown == NULL) return -1;
    *items = grown;
    (*items)[*count] = value;
    *count += 1U;
    return 0;
}

static int append_track_span(AmigaDiskAnalysis *analysis, uint32_t start_track, uint32_t end_track) {
    AmigaDiskTrackSpan *grown = (AmigaDiskTrackSpan *)analysis_grow_array(analysis, analysis->nonempty_track_spans,
        analysis->nonempty_track_span_count, &analysis->nonempty_track_span_capacity, sizeof(*analysis->nonempty_track_spans));
    if (grown == NULL) return -1;
    analysis->nonempty_track_spans = grown;
    analysis->nonempty_track_spans[analysis->nonempty_track_span_count].start_track = start_track;
    analysis->nonempty_track_spans[analysis->nonempty_track_span_count].end_track = end_track;
    analysis->nonempty_track_span_count += 1U;
    return 0;
}

static int append_bootloader_stage(AmigaDiskAnalysis *analysis, const char *name, uint32_t base_addr, uint32_t entry_addr,
    uint32_t disk_offset, uint32_t byte_length, uint8_t has_disk_read) {
    AmigaDiskBootloaderStage *grown;
    char *name_copy;
    grown = (AmigaDiskBootloaderStage *)analysis_grow_array(analysis, analysis->bootloader_stages,
        analysis->bootloader_stage_count, &analysis->bootloader_stage_capacity, sizeof(*analysis->bootloader_stages));
    if (grown == NULL) return -1;
    analysis->bootloader_stages = grown;
    name_copy = arena_strdup(analysis->arena, name);
    if (name_copy == NULL) return -1;
    memset(&analysis->bootloader_stages[analysis->bootloader_stage_count], 0, sizeof(*analysis->bootloader_stages));
    analysis->bootloader_stages[analysis->bootloader_stage_count].name = name_copy;
    analysis->bootloader_stages[analysis->bootloader_stage_count].base_addr = base_addr;
    analysis->bootloader_stages[analysis->bootloader_stage_count].entry_addr = entry_addr;
    analysis->bootloader_stages[analysis->bootloader_stage_count].size = byte_length;
    analysis->bootloader_stages[analysis->bootloader_stage_count].disk_offset = disk_offset;
    analysis->bootloader_stages[analysis->bootloader_stage_count].byte_length = byte_length;
    analysis->bootloader_stages[analysis->bootloader_stage_count].instruction_addr =
        AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DEFAULT_LOAD_ADDRESS
        + AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_ENTRY_OFFSET;
    analysis->bootloader_stages[analysis->bootloader_stage_count].materialized = 1U;
    analysis->bootloader_stages[analysis->bootloader_stage_count].has_disk_read = has_disk_read;
    analysis->bootloader_stage_count += 1U;
    return 0;
}

static uint32_t sectors_per_track_for_image(const DiskContext *ctx) {
    if (ctx->total_blocks == 3520U) return AMIGA_DISK_FILE_CONSTRAINTS_HD_SECTORS_PER_TRACK;
    return AMIGA_DISK_FILE_CONSTRAINTS_DD_SECTORS_PER_TRACK;
}

static int populate_track_analysis(const DiskContext *ctx, AmigaDiskAnalysis *analysis) {
    uint32_t sectors_per_track = sectors_per_track_for_image(ctx);
    uint32_t track;
    uint8_t in_span = 0U;
    uint32_t span_start = 0U;
    analysis->track_size_bytes = ctx->block_size * sectors_per_track;
    if (analysis->track_size_bytes == 0U) return 0;
    analysis->total_tracks = ctx->total_blocks / sectors_per_track;
    for (track = 0; track < analysis->total_tracks; ++track) {
        size_t start = (size_t)track * analysis->track_size_bytes;
        size_t end = start + analysis->track_size_bytes;
        AmigaDiskTrackInfo *row;
        AmigaDiskTrackInfo *grown;
        if (end > ctx->size) break;
        grown = (AmigaDiskTrackInfo *)analysis_grow_array(analysis, analysis->tracks, analysis->track_count,
            &analysis->track_capacity, sizeof(*analysis->tracks));
        if (grown == NULL) return -1;
        analysis->tracks = grown;
        row = &analysis->tracks[analysis->track_count];
        memset(row, 0, sizeof(*row));
        row->track = track;
        row->cylinder = track / 2U;
        row->head = track % 2U;
        row->first_block = track * sectors_per_track;
        row->byte_offset = (uint32_t)start;
        row->byte_length = analysis->track_size_bytes;
        row->empty = !block_range_has_nonzero(ctx->data, start, end);
        row->entropy = shannon_entropy(ctx->data + start, analysis->track_size_bytes);
        row->m68k_pattern_count = count_m68k_signature_words(ctx->data + start, analysis->track_size_bytes);
        row->has_code = row->m68k_pattern_count >= AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_CODE_TRACK_MIN_PATTERN_HITS
            || (track == 0U && analysis->bootcode_has_code);
        if (scan_ascii_strings(analysis, row, ctx->data + start, analysis->track_size_bytes, 0U,
                AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_TRACK_ASCII_MIN_LENGTH) != 0) {
            return -1;
        }
        analysis->track_count += 1U;
        if (!row->empty) {
            analysis->non_empty_tracks += 1U;
            if (row->head == 0U) analysis->nonempty_head0_tracks += 1U;
            else analysis->nonempty_head1_tracks += 1U;
            if (row->has_code
                && append_u32_array(analysis, &analysis->candidate_code_tracks, &analysis->candidate_code_track_count,
                    &analysis->candidate_code_track_capacity, track) != 0) {
                return -1;
            }
            if ((uint32_t)(row->entropy * 10.0) >= AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_HIGH_ENTROPY_THRESHOLD_TENTHS
                && analysis->high_entropy_track_count < AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_MAX_HIGH_ENTROPY_TRACKS
                && append_u32_array(analysis, &analysis->high_entropy_tracks, &analysis->high_entropy_track_count,
                    &analysis->high_entropy_track_capacity, track) != 0) {
                return -1;
            }
            if (!in_span) {
                span_start = track;
                in_span = 1U;
            }
        } else if (in_span) {
            if (append_track_span(analysis, span_start, track - 1U) != 0) return -1;
            in_span = 0U;
        }
    }
    if (in_span && append_track_span(analysis, span_start, analysis->total_tracks - 1U) != 0) return -1;
    return 0;
}

static int populate_trackloader_analysis(const DiskContext *ctx, AmigaDiskAnalysis *analysis) {
    size_t bootcode_offset = AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET + 4U;
    size_t boot_block_bytes = (size_t)ctx->block_size * AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS;
    if (boot_block_bytes > bootcode_offset
        && scan_ascii_strings(analysis, NULL, ctx->data + bootcode_offset, boot_block_bytes - bootcode_offset,
            (uint32_t)bootcode_offset, AMIGA_DISK_FILE_CONSTRAINTS_NON_DOS_BOOT_ASCII_MIN_LENGTH) != 0) {
        return -1;
    }
    return 0;
}

static int append_decode_region_span(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderDecodeRegion *region,
    uint32_t start_track, uint32_t end_track, uint32_t start_byte_offset, uint32_t byte_length) {
    AmigaDiskRawTrackSourceSpan *grown;
    AmigaDiskRawTrackSourceSpan *span;
    grown = (AmigaDiskRawTrackSourceSpan *)analysis_grow_array(analysis, region->input_source_candidate_spans,
        region->input_source_candidate_span_count, &region->input_source_candidate_span_capacity,
        sizeof(*region->input_source_candidate_spans));
    if (grown == NULL) return -1;
    region->input_source_candidate_spans = grown;
    span = &region->input_source_candidate_spans[region->input_source_candidate_span_count];
    span->start_track = start_track;
    span->end_track = end_track;
    span->start_byte_offset = start_byte_offset;
    span->byte_length = byte_length;
    region->input_source_candidate_span_count += 1U;
    return 0;
}

static int append_bootloader_decode_region(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage,
    const AmigaDiskBootloaderReadSetup *setup, const AmigaDiskRawTrackSourceSpan *span) {
    AmigaDiskBootloaderDecodeRegion *grown;
    AmigaDiskBootloaderDecodeRegion *region;
    grown = (AmigaDiskBootloaderDecodeRegion *)analysis_grow_array(analysis, stage->decode_regions,
        stage->decode_region_count, &stage->decode_region_capacity, sizeof(*stage->decode_regions));
    if (grown == NULL) return -1;
    stage->decode_regions = grown;
    region = &stage->decode_regions[stage->decode_region_count];
    memset(region, 0, sizeof(*region));
    region->instruction_addr = setup->instruction_addr;
    region->has_input_buffer_addr = setup->has_buffer_addr;
    region->input_buffer_addr = setup->buffer_addr;
    region->input_source_kind = arena_strdup(analysis->arena, "custom_track_dma_buffer");
    region->input_required_source_kind = arena_strdup(analysis->arena, "raw_custom_track_bytes");
    region->has_input_required_byte_length = setup->has_dsklen_dma_byte_length;
    region->input_required_byte_length = setup->dsklen_dma_byte_length;
    region->input_materializable = 1U;
    region->input_missing_reason = arena_strdup(analysis->arena, "custom_track_decode_mapping_unresolved");
    region->write_loop_addr = setup->has_buffer_scan_addr ? setup->buffer_scan_addr : setup->instruction_addr;
    if (region->input_source_kind == NULL || region->input_required_source_kind == NULL ||
        region->input_missing_reason == NULL) {
        return -1;
    }
    if (append_decode_region_span(analysis, region, span->start_track, span->end_track, span->start_byte_offset,
            span->byte_length) != 0) {
        return -1;
    }
    stage->decode_region_count += 1U;
    return 0;
}

static uint32_t raw_span_m68k_prefix_score(const unsigned char *data, size_t size, uint32_t start, uint32_t byte_length) {
    uint32_t offset = 2U;
    uint32_t score = 0U;
    uint32_t limit = byte_length < 256U ? byte_length : 256U;
    while (offset + 2U <= limit && (size_t)start + offset < size) {
        M68kDiagList diagnostics;
        M68kInstructionIR instruction;
        m68k_diag_list_reset(&diagnostics);
        instruction = m68k_ir_decode_one(data + start + offset, size - (size_t)start - offset, M68K_ASM_CPU_68000,
            m68k_diag_sink(&diagnostics));
        if (instruction.byte_count == 0U || offset + instruction.byte_count > limit) break;
        score += (uint32_t)instruction.byte_count;
        offset += (uint32_t)instruction.byte_count;
        if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS || instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
            instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTR) {
            break;
        }
    }
    return score;
}

static int find_best_raw_track_sync_span(const AmigaDiskAnalysis *analysis, const unsigned char *data, size_t size,
    const AmigaDiskBootloaderReadSetup *setup, AmigaDiskRawTrackSourceSpan *out_span) {
    uint32_t sync_word;
    unsigned char sync_hi;
    unsigned char sync_lo;
    size_t i;
    uint32_t best_score = 0U;
    uint32_t best_count = 0U;
    if (!setup->has_track || !setup->has_sync_word || !setup->has_dsklen_dma_byte_length ||
        setup->dsklen_dma_byte_length == 0U) {
        return 0;
    }
    sync_word = setup->sync_word & 0xFFFFU;
    sync_hi = (unsigned char)(sync_word >> 8);
    sync_lo = (unsigned char)(sync_word & 0xFFU);
    for (i = 0; i < analysis->track_count; ++i) {
        const AmigaDiskTrackInfo *track = &analysis->tracks[i];
        uint32_t offset;
        if (track->track != setup->track) continue;
        if ((size_t)track->byte_offset + track->byte_length > size || track->byte_length < 2U) continue;
        for (offset = 0U; offset + 1U < track->byte_length; ++offset) {
            uint32_t total_bytes = track->byte_length - offset;
            uint32_t end_track = track->track;
            size_t next_index = i + 1U;
            if (data[track->byte_offset + offset] != sync_hi || data[track->byte_offset + offset + 1U] != sync_lo)
                continue;
            while (total_bytes < setup->dsklen_dma_byte_length && next_index < analysis->track_count) {
                const AmigaDiskTrackInfo *next_track = &analysis->tracks[next_index];
                if (next_track->track != end_track + 1U) break;
                total_bytes += next_track->byte_length;
                end_track = next_track->track;
                next_index += 1U;
            }
            if (total_bytes < setup->dsklen_dma_byte_length) continue;
            {
                uint32_t start_byte_offset = track->byte_offset + offset;
                uint32_t score = raw_span_m68k_prefix_score(data, size, start_byte_offset,
                    setup->dsklen_dma_byte_length);
                if (score > best_score) {
                    best_score = score;
                    best_count = 1U;
                    out_span->start_track = track->track;
                    out_span->end_track = end_track;
                    out_span->start_byte_offset = start_byte_offset;
                    out_span->byte_length = total_bytes;
                } else if (score == best_score) {
                    best_count += 1U;
                }
            }
        }
    }
    return best_score != 0U && best_count == 1U;
}

static int populate_bootloader_decode_regions(const DiskContext *ctx, AmigaDiskAnalysis *analysis,
    AmigaDiskBootloaderStage *stage) {
    size_t i;
    for (i = 0; i < stage->read_setup_count; ++i) {
        const AmigaDiskBootloaderReadSetup *setup = &stage->read_setups[i];
        AmigaDiskRawTrackSourceSpan span;
        memset(&span, 0, sizeof(span));
        if (!find_best_raw_track_sync_span(analysis, ctx->data, ctx->size, setup, &span)) continue;
        if (append_bootloader_decode_region(analysis, stage, setup, &span) != 0) return -1;
    }
    return 0;
}

static int populate_bootloader_analysis(const DiskContext *ctx, AmigaDiskAnalysis *analysis) {
    size_t boot_block_bytes = (size_t)ctx->block_size * AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS;
    uint32_t bootcode_offset = AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET + 4U;
    uint32_t stage_end = 0U;
    uint32_t materialized_stage_end =
        analysis->track_size_bytes * AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_STAGE_MATERIALIZATION_TRACKS;
    size_t i;
    if (!analysis->bootcode_has_code || analysis->track_size_bytes == 0U) return 0;
    if (append_bootloader_stage(analysis, "boot", AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DEFAULT_LOAD_ADDRESS,
            AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DEFAULT_LOAD_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_ENTRY_OFFSET,
            bootcode_offset, analysis->bootcode_size, 0U) != 0) {
        return -1;
    }
    if (amiga_disk_analyze_bootloader_stage_bytes(analysis, &analysis->bootloader_stages[analysis->bootloader_stage_count - 1U],
            ctx->data + bootcode_offset, analysis->bootcode_size) != 0 ||
        amiga_disk_append_bootloader_read_setup(analysis, &analysis->bootloader_stages[analysis->bootloader_stage_count - 1U]) != 0) {
        return -1;
    }
    for (i = 0; i < analysis->nonempty_track_span_count; ++i) {
        const AmigaDiskTrackSpan *span = &analysis->nonempty_track_spans[i];
        if (span->start_track == 0U) {
            stage_end = (span->end_track + 1U) * analysis->track_size_bytes;
            break;
        }
    }
    if (stage_end > materialized_stage_end) stage_end = materialized_stage_end;
    if (stage_end <= boot_block_bytes || stage_end > ctx->size) return 0;
    if (disk_has_valid_dos_filesystem(ctx)) return 0;
    if (!block_range_has_nonzero(ctx->data, boot_block_bytes, stage_end)) return 0;
    if (append_bootloader_stage(analysis, "stage_1", AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_STAGE_DEFAULT_LOAD_ADDRESS,
            AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_STAGE_DEFAULT_LOAD_ADDRESS, (uint32_t)boot_block_bytes,
            stage_end - (uint32_t)boot_block_bytes, 1U) != 0) {
        return -1;
    }
    {
        AmigaDiskBootloaderStage *stage = &analysis->bootloader_stages[analysis->bootloader_stage_count - 1U];
        if (amiga_disk_analyze_bootloader_stage_bytes(analysis, stage,
                ctx->data + boot_block_bytes, stage_end - boot_block_bytes) != 0) {
            return -1;
        }
        if (stage->reachable_instruction_count == 0U) {
            analysis->bootloader_stage_count -= 1U;
            return 0;
        }
        if (amiga_disk_append_bootloader_read_setup(analysis, stage) != 0) return -1;
        if (populate_bootloader_decode_regions(ctx, analysis, stage) != 0) return -1;
    }
    return 0;
}

static int append_file_pointer_block_extents(const DiskContext *ctx, const unsigned char *block, uint32_t byte_size,
    uint32_t *remaining, AmigaDiskEntry *entry) {
    uint32_t high_seq = read_u32be(block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_HIGH_SEQ_OFFSET);
    uint32_t block_indices[AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT];
    uint32_t block_count = 0;
    uint32_t start_index;
    uint32_t i;

    if (high_seq > AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT) return -1;
    start_index = AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT - high_seq;
    for (i = start_index; i < AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT; ++i) {
        uint32_t block_index = read_u32be(block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCKS_OFFSET + (size_t)i * 4U);
        if (block_index == 0U) continue;
        block_indices[block_count] = block_index;
        block_count += 1U;
    }
    while (block_count > 0U) {
        uint32_t block_index = block_indices[block_count - 1U];
        size_t offset = 0;
        uint32_t extent_size;
        if (block_offset(ctx, block_index, &offset) != 0) return -1;
        extent_size = (*remaining > byte_size) ? byte_size : *remaining;
        if (append_extent((AmigaDiskAnalysis *)entry->owner, entry, block_index, (uint32_t)offset, extent_size) != 0) return -1;
        if (*remaining > extent_size) *remaining -= extent_size;
        else {
            *remaining = 0U;
            break;
        }
        block_count -= 1U;
    }
    return 0;
}

static int append_ffs_extents_from_extension_chain(const DiskContext *ctx, uint32_t extension_block_index, uint32_t byte_size,
    uint32_t *remaining, AmigaDiskEntry *entry) {
    uint32_t steps = 0;
    while (extension_block_index != 0U && *remaining > 0U) {
        const unsigned char *extension_block;
        size_t extension_offset = 0;
        if (block_offset(ctx, extension_block_index, &extension_offset) != 0) return -1;
        extension_block = ctx->data + extension_offset;
        if (read_u32be(extension_block, 0) != AMIGA_DISK_FILE_CONSTRAINTS_FILE_EXTENSION_TYPE) return -1;
        if (append_extension_block((AmigaDiskAnalysis *)entry->owner, entry, extension_block_index) != 0) return -1;
        if (append_file_pointer_block_extents(ctx, extension_block, byte_size, remaining, entry) != 0) return -1;
        extension_block_index = read_u32be(extension_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_EXTENSION_OFFSET);
        steps += 1U;
        if (steps > ctx->total_blocks) return -1;
    }
    return 0;
}

static int append_ofs_extents_from_pointer_block(const DiskContext *ctx, const unsigned char *block, uint32_t *remaining,
    AmigaDiskEntry *entry) {
    uint32_t high_seq = read_u32be(block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_HIGH_SEQ_OFFSET);
    uint32_t block_indices[AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT];
    uint32_t block_count = 0;
    uint32_t start_index;
    uint32_t i;

    if (high_seq > AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT) return -1;
    start_index = AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT - high_seq;
    for (i = start_index; i < AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCK_COUNT; ++i) {
        uint32_t block_index = read_u32be(block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATA_BLOCKS_OFFSET + (size_t)i * 4U);
        if (block_index == 0U) continue;
        block_indices[block_count] = block_index;
        block_count += 1U;
    }
    while (block_count > 0U) {
        uint32_t block_index = block_indices[block_count - 1U];
        const unsigned char *data_block;
        size_t block_base = 0;
        uint32_t data_size;
        if (block_offset(ctx, block_index, &block_base) != 0) return -1;
        data_block = ctx->data + block_base;
        data_size = read_u32be(data_block, AMIGA_DISK_FILE_CONSTRAINTS_OFS_DATA_SIZE_OFFSET);
        if (data_size > AMIGA_DISK_FILE_CONSTRAINTS_OFS_MAX_DATA_BYTES) return -1;
        if (append_extent((AmigaDiskAnalysis *)entry->owner, entry, block_index,
                (uint32_t)(block_base + AMIGA_DISK_FILE_CONSTRAINTS_OFS_DATA_OFFSET),
                (*remaining > data_size) ? data_size : *remaining) != 0) {
            return -1;
        }
        if (*remaining > data_size) *remaining -= data_size;
        else {
            *remaining = 0U;
            break;
        }
        block_count -= 1U;
    }
    return 0;
}

static int append_ofs_extents_from_extension_chain(const DiskContext *ctx, uint32_t extension_block_index, uint32_t *remaining,
    AmigaDiskEntry *entry) {
    uint32_t steps = 0;
    while (extension_block_index != 0U && *remaining > 0U) {
        const unsigned char *extension_block;
        size_t extension_offset = 0;
        if (block_offset(ctx, extension_block_index, &extension_offset) != 0) return -1;
        extension_block = ctx->data + extension_offset;
        if (read_u32be(extension_block, 0) != AMIGA_DISK_FILE_CONSTRAINTS_FILE_EXTENSION_TYPE) return -1;
        if (append_extension_block((AmigaDiskAnalysis *)entry->owner, entry, extension_block_index) != 0) return -1;
        if (append_ofs_extents_from_pointer_block(ctx, extension_block, remaining, entry) != 0) return -1;
        extension_block_index = read_u32be(extension_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_EXTENSION_OFFSET);
        steps += 1U;
        if (steps > ctx->total_blocks) return -1;
    }
    return 0;
}

static int append_ofs_extents_from_linked_chain(const DiskContext *ctx, uint32_t data_block, uint32_t *remaining,
    AmigaDiskEntry *entry) {
    uint32_t steps = 0;
    while (data_block != 0U && *remaining > 0U) {
        size_t block_base = 0;
        const unsigned char *block;
        uint32_t data_size;
        uint32_t next_data;
        if (block_offset(ctx, data_block, &block_base) != 0) return -1;
        block = ctx->data + block_base;
        data_size = read_u32be(block, AMIGA_DISK_FILE_CONSTRAINTS_OFS_DATA_SIZE_OFFSET);
        next_data = read_u32be(block, AMIGA_DISK_FILE_CONSTRAINTS_OFS_NEXT_DATA_OFFSET);
        if (data_size > AMIGA_DISK_FILE_CONSTRAINTS_OFS_MAX_DATA_BYTES) return -1;
        if (append_extent((AmigaDiskAnalysis *)entry->owner, entry, data_block,
                (uint32_t)(block_base + AMIGA_DISK_FILE_CONSTRAINTS_OFS_DATA_OFFSET),
                (*remaining > data_size) ? data_size : *remaining) != 0) {
            return -1;
        }
        if (*remaining > data_size) *remaining -= data_size;
        else {
            *remaining = 0U;
            break;
        }
        data_block = next_data;
        steps += 1U;
        if (steps > ctx->total_blocks) return -1;
    }
    return 0;
}

static int add_entry(AmigaDiskAnalysis *analysis, const AmigaDiskEntry *entry) {
    AmigaDiskEntry *grown = (AmigaDiskEntry *)analysis_grow_array(analysis, analysis->entries, analysis->entry_count,
        &analysis->entry_capacity, sizeof(*analysis->entries));
    if (grown == NULL) return -1;
    analysis->entries = grown;
    analysis->entries[analysis->entry_count] = *entry;
    analysis->entry_count += 1U;
    return 0;
}

static void mark_block_usage(uint8_t *usage, uint32_t total_blocks, uint32_t block_index, AmigaDiskBlockUsageKind kind) {
    if (usage == NULL || block_index >= total_blocks) return;
    usage[block_index] = (uint8_t)kind;
}

static int collect_bitmap_map(const DiskContext *ctx, const AmigaDiskAnalysis *analysis, uint8_t *bitmap_map,
    uint8_t *out_checksum_valid) {
    uint32_t i;
    if (bitmap_map == NULL || out_checksum_valid == NULL) return -1;
    memset(bitmap_map, 2, ctx->total_blocks);
    if (ctx->total_blocks > 0U) bitmap_map[0] = 0;
    if (ctx->total_blocks > 1U) bitmap_map[1] = 0;
    *out_checksum_valid = 1U;
    for (i = 0; i < analysis->root_bitmap_page_count; ++i) {
        uint32_t bm_block_num = analysis->root_bitmap_pages[i];
        size_t bm_offset = 0;
        const unsigned char *bm_block;
        size_t byte_index;
        if (block_offset(ctx, bm_block_num, &bm_offset) != 0) return -1;
        bm_block = ctx->data + bm_offset;
        if (!block_checksum_valid(bm_block, ctx->block_size)) *out_checksum_valid = 0U;
        for (byte_index = 4U; byte_index < ctx->block_size; ++byte_index) {
            unsigned byte_value = bm_block[byte_index];
            unsigned bit;
            for (bit = 0; bit < 8U; ++bit) {
                uint32_t block_index = 2U + (uint32_t)(byte_index - 4U) * 8U + bit;
                if (block_index >= ctx->total_blocks) break;
                bitmap_map[block_index] = (uint8_t)((byte_value & (1U << bit)) != 0U ? 1U : 0U);
            }
        }
    }
    return 0;
}

static int summarize_block_usage(const DiskContext *ctx, AmigaDiskAnalysis *analysis, M68kDiagSink diagnostics) {
    uint8_t *usage = NULL;
    uint8_t *bitmap_map = NULL;
    uint32_t i;
    if (ctx->total_blocks == 0U) return 0;
    usage = (uint8_t *)arena_alloc(analysis->arena, ctx->total_blocks);
    bitmap_map = (uint8_t *)arena_alloc(analysis->arena, ctx->total_blocks);
    if (usage == NULL || bitmap_map == NULL) {
        disk_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    memset(usage, AMIGA_DISK_BLOCK_USAGE_UNKNOWN, ctx->total_blocks);
    if (collect_bitmap_map(ctx, analysis, bitmap_map, &analysis->bitmap_checksum_valid) != 0) {
        disk_diag_error(diagnostics, "Invalid AmigaDOS bitmap");
        return -1;
    }
    mark_block_usage(usage, ctx->total_blocks, 0U, AMIGA_DISK_BLOCK_USAGE_BOOT);
    mark_block_usage(usage, ctx->total_blocks, 1U, AMIGA_DISK_BLOCK_USAGE_BOOT);
    mark_block_usage(usage, ctx->total_blocks, analysis->root_block, AMIGA_DISK_BLOCK_USAGE_ROOT);
    for (i = 0; i < analysis->root_bitmap_page_count; ++i) {
        mark_block_usage(usage, ctx->total_blocks, analysis->root_bitmap_pages[i], AMIGA_DISK_BLOCK_USAGE_BITMAP);
    }
    for (i = 0; i < analysis->entry_count; ++i) {
        const AmigaDiskEntry *entry = &analysis->entries[i];
        size_t j;
        if (entry->kind == AMIGA_DISK_ENTRY_DIRECTORY) {
            mark_block_usage(usage, ctx->total_blocks, entry->header_block, AMIGA_DISK_BLOCK_USAGE_DIR_HEADER);
        } else if (entry->kind == AMIGA_DISK_ENTRY_FILE) {
            mark_block_usage(usage, ctx->total_blocks, entry->header_block, AMIGA_DISK_BLOCK_USAGE_FILE_HEADER);
        }
        for (j = 0; j < entry->extent_count; ++j) {
            mark_block_usage(usage, ctx->total_blocks, entry->extents[j].block_index, AMIGA_DISK_BLOCK_USAGE_DATA);
        }
        for (j = 0; j < entry->extension_block_count; ++j) {
            mark_block_usage(usage, ctx->total_blocks, entry->extension_blocks[j], AMIGA_DISK_BLOCK_USAGE_EXTENSION);
        }
    }
    for (i = 0; i < ctx->total_blocks; ++i) {
        if (bitmap_map[i] == 1U) analysis->bitmap_free_blocks += 1U;
        else if (bitmap_map[i] == 0U) analysis->bitmap_allocated_blocks += 1U;
        if (bitmap_map[i] == 1U && usage[i] == AMIGA_DISK_BLOCK_USAGE_UNKNOWN) {
            usage[i] = AMIGA_DISK_BLOCK_USAGE_FREE;
        } else if (bitmap_map[i] == 0U && usage[i] == AMIGA_DISK_BLOCK_USAGE_UNKNOWN) {
            usage[i] = AMIGA_DISK_BLOCK_USAGE_ALLOCATED_ORPHAN;
            if (append_orphan_block(analysis, i) != 0) {
                disk_diag_error(diagnostics, "Out of memory");
                return -1;
            }
        }
        switch ((AmigaDiskBlockUsageKind)usage[i]) {
            case AMIGA_DISK_BLOCK_USAGE_BOOT:
                analysis->block_usage.boot += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_ROOT:
                analysis->block_usage.root += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_BITMAP:
                analysis->block_usage.bitmap += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_DIR_HEADER:
                analysis->block_usage.dir_header += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_FILE_HEADER:
                analysis->block_usage.file_header += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_DATA:
                analysis->block_usage.data += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_EXTENSION:
                analysis->block_usage.extension += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_FREE:
                analysis->block_usage.free_blocks += 1U;
                break;
            case AMIGA_DISK_BLOCK_USAGE_ALLOCATED_ORPHAN:
                analysis->block_usage.allocated_orphan += 1U;
                break;
            default:
                analysis->block_usage.unknown += 1U;
                break;
        }
    }
    analysis->bitmap_percent_used = ctx->total_blocks != 0U
        ? floor(((double)analysis->bitmap_allocated_blocks / (double)ctx->total_blocks) * 1000.0 + 0.5) / 10.0
        : 0.0;
    return 0;
}

static int build_file_extents_ffs(const DiskContext *ctx, const unsigned char *header_block, uint32_t byte_size,
    AmigaDiskEntry *entry) {
    uint32_t remaining = byte_size;
    uint32_t extension_block_index = read_u32be(header_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_EXTENSION_OFFSET);
    if (append_file_pointer_block_extents(ctx, header_block, ctx->block_size, &remaining, entry) != 0) return -1;
    if (append_ffs_extents_from_extension_chain(ctx, extension_block_index, ctx->block_size, &remaining, entry) != 0) return -1;
    return (remaining == 0U || byte_size == 0U) ? 0 : -1;
}

static int build_file_extents_ofs(const DiskContext *ctx, const unsigned char *header_block, uint32_t byte_size,
    AmigaDiskEntry *entry) {
    size_t initial_extent_count = entry->extent_count;
    uint32_t remaining = byte_size;
    uint32_t data_block = read_u32be(header_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_FIRST_DATA_OFFSET);
    uint32_t extension_block_index = read_u32be(header_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_EXTENSION_OFFSET);
    if (append_ofs_extents_from_pointer_block(ctx, header_block, &remaining, entry) != 0) return -1;
    if (append_ofs_extents_from_extension_chain(ctx, extension_block_index, &remaining, entry) != 0) return -1;
    if (entry->extent_count == initial_extent_count && append_ofs_extents_from_linked_chain(ctx, data_block, &remaining, entry) != 0)
        return -1;
    return (remaining == 0U || byte_size == 0U) ? 0 : -1;
}

static int build_file_extents(const DiskContext *ctx, const unsigned char *header_block, uint32_t byte_size,
    AmigaDiskEntry *entry) {
    if (byte_size == 0U) return 0;
    if (ctx->is_ffs) return build_file_extents_ffs(ctx, header_block, byte_size, entry);
    return build_file_extents_ofs(ctx, header_block, byte_size, entry);
}

static int parse_directory_block(const DiskContext *ctx, AmigaDiskAnalysis *analysis, uint32_t dir_block_index,
    const char *base_path, M68kDiagSink diagnostics) {
    const unsigned char *dir_block;
    size_t block_base = 0;
    uint32_t i;
    if (block_offset(ctx, dir_block_index, &block_base) != 0) {
        disk_diag_error(diagnostics, "Invalid AmigaDOS directory block");
        return -1;
    }
    dir_block = ctx->data + block_base;
    for (i = 0; i < AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_ENTRIES; ++i) {
        uint32_t entry_block_index = read_u32be(dir_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_OFFSET + (size_t)i * 4U);
        uint32_t steps = 0;
        while (entry_block_index != 0U) {
            size_t entry_base = 0;
            const unsigned char *entry_block;
            uint32_t sec_type;
            uint32_t next_chain;
            char name[AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_NAME_MAX_LENGTH + 1U];
            char comment[AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_COMMENT_MAX_LENGTH + 1U];
            AmigaDiskEntry entry;
            char *path = NULL;
            if (block_offset(ctx, entry_block_index, &entry_base) != 0) {
                disk_diag_error(diagnostics, "Invalid AmigaDOS file header block");
                return -1;
            }
            entry_block = ctx->data + entry_base;
            sec_type = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_SEC_TYPE_OFFSET);
            next_chain = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_HASH_CHAIN_OFFSET);
            if (read_bcpl_name(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_NAME_LEN_OFFSET,
                    AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_NAME_MAX_LENGTH, name, sizeof(name)) != 0) {
                disk_diag_error(diagnostics, "Invalid AmigaDOS entry name");
                return -1;
            }
            if (read_bcpl_name(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_COMMENT_LEN_OFFSET,
                    AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_COMMENT_MAX_LENGTH, comment, sizeof(comment)) != 0) {
                disk_diag_error(diagnostics, "Invalid AmigaDOS entry comment");
                return -1;
            }
            if (analysis_join_path(analysis, base_path, name, &path) != 0) {
                disk_diag_error(diagnostics, "Out of memory");
                return -1;
            }
            memset(&entry, 0, sizeof(entry));
            entry.name = arena_strdup(analysis->arena, name);
            entry.path = path;
            entry.comment = comment[0] != '\0' ? arena_strdup(analysis->arena, comment) : NULL;
            entry.owner = analysis;
            entry.header_block = entry_block_index;
            entry.protection = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_PROTECTION_OFFSET);
            entry.date_days = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATE_OFFSET);
            entry.date_mins = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATE_OFFSET + 4U);
            entry.date_ticks = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_DATE_OFFSET + 8U);
            entry.hash_chain = next_chain;
            entry.parent = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_PARENT_OFFSET);
            entry.checksum_valid = block_checksum_valid(entry_block, ctx->block_size);
            if (entry.name == NULL || (comment[0] != '\0' && entry.comment == NULL)) {
                disk_diag_error(diagnostics, "Out of memory");
                return -1;
            }
            if (sec_type == AMIGA_DISK_FILE_CONSTRAINTS_SEC_TYPE_USERDIR) {
                entry.kind = AMIGA_DISK_ENTRY_DIRECTORY;
            } else if (sec_type == AMIGA_DISK_FILE_CONSTRAINTS_SEC_TYPE_FILE) {
                entry.kind = AMIGA_DISK_ENTRY_FILE;
                entry.byte_size = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_BYTE_SIZE_OFFSET);
                if (build_file_extents(ctx, entry_block, entry.byte_size, &entry) != 0) {
                    entry.extents = NULL;
                    entry.extent_count = 0U;
                    entry.extent_capacity = 0U;
                }
            } else {
                entry_block_index = next_chain;
                steps += 1U;
                if (steps > ctx->total_blocks) {
                    disk_diag_error(diagnostics, "Invalid AmigaDOS hash chain");
                    return -1;
                }
                continue;
            }
            if (add_entry(analysis, &entry) != 0) {
                disk_diag_error(diagnostics, "Out of memory");
                return -1;
            }
            if (entry.kind == AMIGA_DISK_ENTRY_DIRECTORY
                && parse_directory_block(ctx, analysis, entry_block_index, entry.path, diagnostics) != 0) {
                return -1;
            }
            entry_block_index = next_chain;
            steps += 1U;
            if (steps > ctx->total_blocks) {
                disk_diag_error(diagnostics, "Invalid AmigaDOS hash chain");
                return -1;
            }
        }
    }
    return 0;
}

int amiga_disk_analysis_create(AmigaDiskAnalysis *analysis) {
    if (analysis == NULL) return -1;
    memset(analysis, 0, sizeof(*analysis));
    analysis->arena = arena_create(AMIGA_DISK_ANALYSIS_ARENA_SIZE);
    return analysis->arena != NULL ? 0 : -1;
}

static void populate_boot_info(const DiskContext *ctx, AmigaDiskAnalysis *analysis) {
    size_t boot_block_bytes = (size_t)ctx->block_size * AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS;
    size_t bootcode_offset = AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET + 4U;
    memcpy(analysis->boot_magic, ctx->data + AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_MAGIC_OFFSET, 3U);
    analysis->boot_magic[3] = '\0';
    analysis->dos_flags = ctx->data[AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_FLAGS_OFFSET];
    analysis->boot_checksum = read_u32be(ctx->data, AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_CHECKSUM_OFFSET);
    analysis->boot_expected_checksum = compute_boot_checksum(ctx->data, ctx->block_size);
    analysis->boot_checksum_valid = (analysis->boot_checksum == analysis->boot_expected_checksum) ? 1U : 0U;
    analysis->root_block = read_u32be(ctx->data, AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET);
    analysis->bootcode_size = boot_block_bytes > bootcode_offset ? (uint32_t)(boot_block_bytes - bootcode_offset) : 0U;
    analysis->bootcode_has_code = boot_block_has_code(ctx) ? 1U : 0U;
    analysis->bootcode_entropy = shannon_entropy(ctx->data + bootcode_offset, analysis->bootcode_size);
}

void amiga_disk_analysis_destroy(AmigaDiskAnalysis *analysis) {
    if (analysis == NULL) return;
    arena_destroy(analysis->arena);
    memset(analysis, 0, sizeof(*analysis));
}

int amiga_disk_analyze_buffer(const unsigned char *data, size_t size, AmigaDiskAnalysis *out_analysis, M68kDiagSink diagnostics) {
    DiskContext ctx;
    size_t root_offset = 0;
    const unsigned char *root_block;
    char volume_name[AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_MAX_LENGTH + 1U];
    AmigaDiskEntry volume_entry;

    if (out_analysis == NULL) {
        disk_diag_error(diagnostics, "Missing Amiga disk analysis output");
        return -1;
    }
    if (amiga_disk_analysis_create(out_analysis) != 0) {
        disk_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    memset(&ctx, 0, sizeof(ctx));

    if (data == NULL && size != 0U) {
        disk_diag_error(diagnostics, "Missing Amiga disk image data");
        return -1;
    }

    ctx.data = data;
    ctx.size = size;
    ctx.block_size = AMIGA_DISK_FILE_CONSTRAINTS_BYTES_PER_SECTOR;
    if (ctx.block_size == 0U || ctx.size % ctx.block_size != 0U) {
        disk_diag_error(diagnostics, "Invalid Amiga disk image size");
        return -1;
    }
    ctx.total_blocks = (uint32_t)(ctx.size / ctx.block_size);
    if (ctx.total_blocks < AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS) {
        disk_diag_error(diagnostics, "Truncated Amiga disk image");
        return -1;
    }

    out_analysis->image_size = (uint32_t)ctx.size;
    out_analysis->block_size = ctx.block_size;
    out_analysis->total_blocks = ctx.total_blocks;
    populate_boot_info(&ctx, out_analysis);
    if (populate_track_analysis(&ctx, out_analysis) != 0
        || populate_trackloader_analysis(&ctx, out_analysis) != 0
        || populate_bootloader_analysis(&ctx, out_analysis) != 0) {
        amiga_disk_analysis_destroy(out_analysis);
        disk_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    if (memcmp(data + AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_MAGIC_OFFSET, "DOS", 3) != 0) {
        out_analysis->format_kind = out_analysis->bootcode_has_code
            ? AMIGA_DISK_FORMAT_NON_DOS_BOOTABLE
            : AMIGA_DISK_FORMAT_NON_DOS_BLANK;
        return 0;
    }
    ctx.dos_flags = data[AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_FLAGS_OFFSET];
    ctx.is_ffs = (ctx.dos_flags & AMIGA_DISK_FILE_DOS_FLAGS_FFS) != 0U;
    ctx.root_block = read_u32be(data, AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET);
    out_analysis->is_dos = 1U;
    if (block_offset(&ctx, ctx.root_block, &root_offset) != 0) {
        out_analysis->format_kind = out_analysis->bootcode_has_code
            ? AMIGA_DISK_FORMAT_DOS_CUSTOM_BOOT
            : AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_POINTER;
        return 0;
    }
    root_block = data + root_offset;
    if (read_u32be(root_block, 0) != AMIGA_DISK_FILE_BLOCK_TYPE_T_HEADER
        || read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_SEC_TYPE_OFFSET) != AMIGA_DISK_FILE_CONSTRAINTS_SEC_TYPE_ROOT
        || read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_SIZE_OFFSET)
            != AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_ENTRIES
        || read_bcpl_name(
            root_block,
            AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_LEN_OFFSET,
            AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_MAX_LENGTH,
            volume_name,
            sizeof(volume_name)
        ) != 0) {
        out_analysis->format_kind = out_analysis->bootcode_has_code
            ? AMIGA_DISK_FORMAT_DOS_CUSTOM_BOOT
            : AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_BLOCK;
        return 0;
    }

    out_analysis->format_kind = AMIGA_DISK_FORMAT_DOS;
    {
        uint32_t i;
        out_analysis->root_checksum_valid = block_checksum_valid(root_block, ctx.block_size);
        out_analysis->root_bitmap_valid_flag = read_s32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_BITMAP_VALID_FLAG_OFFSET);
        out_analysis->root_date_days = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_DATE_OFFSET);
        out_analysis->root_date_mins = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_DATE_OFFSET + 4U);
        out_analysis->root_date_ticks = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_DATE_OFFSET + 8U);
        out_analysis->volume_date_days = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_VOLUME_DATE_OFFSET);
        out_analysis->volume_date_mins = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_VOLUME_DATE_OFFSET + 4U);
        out_analysis->volume_date_ticks = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_VOLUME_DATE_OFFSET + 8U);
        out_analysis->creation_date_days = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_CREATION_DATE_OFFSET);
        out_analysis->creation_date_mins = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_CREATION_DATE_OFFSET + 4U);
        out_analysis->creation_date_ticks = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_CREATION_DATE_OFFSET + 8U);
        for (i = 0; i < AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_ENTRIES; ++i) {
            out_analysis->root_hash_table[i] = read_u32be(root_block,
                AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_OFFSET + (size_t)i * 4U);
        }
        for (i = 0; i < AMIGA_DISK_FILE_CONSTRAINTS_ROOT_BITMAP_PAGES_COUNT; ++i) {
            uint32_t page = read_u32be(root_block, AMIGA_DISK_FILE_CONSTRAINTS_ROOT_BITMAP_PAGES_OFFSET + (size_t)i * 4U);
            if (page != 0U) {
                out_analysis->root_bitmap_pages[out_analysis->root_bitmap_page_count] = page;
                out_analysis->root_bitmap_page_count += 1U;
            }
        }
    }

    memset(&volume_entry, 0, sizeof(volume_entry));
    volume_entry.kind = AMIGA_DISK_ENTRY_VOLUME;
    volume_entry.header_block = ctx.root_block;
    volume_entry.owner = out_analysis;
    volume_entry.path = arena_strdup(out_analysis->arena, volume_name);
    volume_entry.name = volume_entry.path;
    out_analysis->volume_name = volume_entry.path;
    if (volume_entry.path == NULL || add_entry(out_analysis, &volume_entry) != 0) {
        amiga_disk_analysis_destroy(out_analysis);
        disk_diag_error(diagnostics, "Out of memory");
        return -1;
    }

    if (parse_directory_block(&ctx, out_analysis, ctx.root_block, "", diagnostics) != 0) {
        amiga_disk_analysis_destroy(out_analysis);
        return -1;
    }
    if (summarize_block_usage(&ctx, out_analysis, diagnostics) != 0) {
        amiga_disk_analysis_destroy(out_analysis);
        return -1;
    }
    return 0;
}

int amiga_disk_analyze_image(const char *path, AmigaDiskAnalysis *out_analysis, M68kDiagSink diagnostics) {
    FILE *fp = NULL;
    int64_t file_size_signed = 0;
    unsigned char *buffer = NULL;
    size_t read_size = 0;
    int result;

    fp = fopen(path, "rb");
    if (fp == NULL) {
        disk_diag_error(diagnostics, "Could not open Amiga disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        disk_diag_error(diagnostics, "Could not size Amiga disk image");
        return -1;
    }
    file_size_signed = (int64_t)ftell(fp);
    if (file_size_signed < 0) {
        fclose(fp);
        disk_diag_error(diagnostics, "Could not size Amiga disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        disk_diag_error(diagnostics, "Could not rewind Amiga disk image");
        return -1;
    }
    buffer = (unsigned char *)malloc((size_t)file_size_signed == 0U ? 1U : (size_t)file_size_signed);
    if (buffer == NULL) {
        fclose(fp);
        disk_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    read_size = fread(buffer, 1, (size_t)file_size_signed, fp);
    fclose(fp);
    if (read_size != (size_t)file_size_signed) {
        free(buffer);
        disk_diag_error(diagnostics, "Could not read Amiga disk image");
        return -1;
    }
    result = amiga_disk_analyze_buffer(buffer, (size_t)file_size_signed, out_analysis, diagnostics);
    free(buffer);
    return result;
}
