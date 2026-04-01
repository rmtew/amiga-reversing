#include "platform_atari_st_disk.h"
#include "platform_common.h"
#include "generated/atari_st_disk_file_runtime.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct DiskContext {
    const unsigned char *data;
    size_t size;
    size_t logical_size;
    uint16_t bytes_per_sector;
    uint8_t sectors_per_cluster;
    uint16_t reserved_sector_count;
    uint8_t fat_count;
    uint16_t root_entry_count;
    uint16_t total_sectors;
    uint16_t sectors_per_fat;
    uint16_t sectors_per_track;
    uint16_t side_count;
    size_t fat_offset;
    size_t fat_size_bytes;
    size_t root_dir_offset;
    size_t root_dir_size_bytes;
    size_t data_region_offset;
    size_t cluster_size_bytes;
    uint16_t max_cluster_index;
} DiskContext;

static uint16_t read_u16le(const unsigned char *data, size_t offset) {
    return (uint16_t)((uint16_t)data[offset] | ((uint16_t)data[offset + 1U] << 8));
}

static uint32_t read_u32le(const unsigned char *data, size_t offset) {
    return (uint32_t)data[offset]
        | ((uint32_t)data[offset + 1U] << 8)
        | ((uint32_t)data[offset + 2U] << 16)
        | ((uint32_t)data[offset + 3U] << 24);
}

static int has_suffix_ci(const char *text, const char *suffix) {
    size_t text_len = strlen(text);
    size_t suffix_len = strlen(suffix);
    size_t i;
    if (suffix_len > text_len) return 0;
    text += text_len - suffix_len;
    for (i = 0; i < suffix_len; ++i) {
        if (toupper((unsigned char)text[i]) != toupper((unsigned char)suffix[i])) return 0;
    }
    return 1;
}

static int is_executable_candidate_name(const char *name) {
    return has_suffix_ci(name, ".PRG") || has_suffix_ci(name, ".TOS") || has_suffix_ci(name, ".TTP")
        || has_suffix_ci(name, ".APP");
}

static int append_extent(AtariStDiskEntry *entry, uint32_t image_offset, uint32_t byte_size, uint16_t cluster_index) {
AtariStDiskExtent *grown = (AtariStDiskExtent *)realloc( entry->extents, (entry->extent_count + 1U) * sizeof(*entry->extents));
    if (grown == NULL) return -1;
    entry->extents = grown;
    entry->extents[entry->extent_count].image_offset = image_offset;
    entry->extents[entry->extent_count].byte_size = byte_size;
    entry->extents[entry->extent_count].cluster_index = cluster_index;
    entry->extent_count += 1U;
    return 0;
}

static int add_entry(AtariStDiskAnalysis *analysis, const AtariStDiskEntry *entry) {
AtariStDiskEntry *grown = (AtariStDiskEntry *)realloc( analysis->entries, (analysis->entry_count + 1U) * sizeof(*analysis->entries));
    if (grown == NULL) return -1;
    analysis->entries = grown;
    analysis->entries[analysis->entry_count] = *entry;
    analysis->entry_count += 1U;
    return 0;
}

static int cluster_offset(const DiskContext *ctx, uint16_t cluster_index, size_t *out_offset) {
    if (cluster_index < 2U || cluster_index > ctx->max_cluster_index) return -1;
    *out_offset = ctx->data_region_offset + (size_t)(cluster_index - 2U) * ctx->cluster_size_bytes;
    if (*out_offset + ctx->cluster_size_bytes > ctx->logical_size) return -1;
    return 0;
}

static int fat12_next_cluster(const DiskContext *ctx, uint16_t cluster_index, uint16_t *out_next) {
    size_t entry_offset;
    uint16_t pair;
    if (cluster_index > ctx->max_cluster_index) return -1;
    entry_offset = ctx->fat_offset + ((size_t)cluster_index * 3U) / 2U;
    if (entry_offset + 2U > ctx->fat_offset + ctx->fat_size_bytes || entry_offset + 2U > ctx->size) return -1;
    pair = read_u16le(ctx->data, entry_offset);
    if ((cluster_index & 1U) == 0U) *out_next = (uint16_t)(pair & 0x0FFFU); else *out_next = (uint16_t)(pair >> 4);
    return 0;
}

static int build_cluster_extents(const DiskContext *ctx, uint16_t first_cluster, uint32_t file_size,
    int walk_full_chain, AtariStDiskEntry *entry) {
    uint16_t cluster = first_cluster;
    uint16_t step_count = 0;
    uint32_t remaining = file_size;
    if (first_cluster == 0U || (!walk_full_chain && file_size == 0U)) return 0;
    while (cluster >= 2U && cluster < 0x0FF8U) {
        size_t offset = 0;
        uint32_t extent_size = (walk_full_chain || remaining > ctx->cluster_size_bytes || file_size == 0U)
            ? (uint32_t)ctx->cluster_size_bytes
            : remaining;
        uint16_t next = 0;
        if (cluster_offset(ctx, cluster, &offset) != 0) return -1;
        if (append_extent(entry, (uint32_t)offset, extent_size, cluster) != 0) return -1;
        if (remaining > extent_size) remaining -= extent_size; else remaining = 0U;
        if (fat12_next_cluster(ctx, cluster, &next) != 0) return -1;
        cluster = next;
        step_count += 1U;
        if (step_count > ctx->max_cluster_index) return -1;
        if (!walk_full_chain && remaining == 0U && file_size != 0U) break;
    }
    return 0;
}

static int build_directory_buffer(const DiskContext *ctx, uint16_t first_cluster, unsigned char **out_data,
    size_t *out_size) {
    uint16_t cluster = first_cluster;
    uint16_t step_count = 0;
    unsigned char *buffer = NULL;
    size_t size = 0;
    if (first_cluster < 2U) return -1;
    while (cluster >= 2U && cluster < 0x0FF8U) {
        size_t offset = 0;
        uint16_t next = 0;
        unsigned char *grown;
        if (cluster_offset(ctx, cluster, &offset) != 0) {
            free(buffer);
            return -1;
        }
        grown = (unsigned char *)realloc(buffer, size + ctx->cluster_size_bytes);
        if (grown == NULL) {
            free(buffer);
            return -1;
        }
        buffer = grown;
        memcpy(buffer + size, ctx->data + offset, ctx->cluster_size_bytes);
        size += ctx->cluster_size_bytes;
        if (fat12_next_cluster(ctx, cluster, &next) != 0) {
            free(buffer);
            return -1;
        }
        cluster = next;
        step_count += 1U;
        if (step_count > ctx->max_cluster_index) {
            free(buffer);
            return -1;
        }
    }
    *out_data = buffer;
    *out_size = size;
    return 0;
}

static void trim_space(char *text) {
    size_t length = strlen(text);
    while (length > 0U && text[length - 1U] == ' ') {
        text[length - 1U] = '\0';
        --length;
    }
}

static int format_entry_name(const unsigned char *entry_data, char *out_name, size_t out_name_size) {
    char name[9];
    char ext[4];
    size_t i;
    if (out_name_size < 2U) return -1;
    for (i = 0; i < 8U; ++i) {
        name[i] = (char)entry_data[i];
    }
    name[8] = '\0';
    for (i = 0; i < 3U; ++i) {
        ext[i] = (char)entry_data[8U + i];
    }
    ext[3] = '\0';
    trim_space(name);
    trim_space(ext);
    if (name[0] == '\0') return -1;
    if (ext[0] != '\0') snprintf(out_name, out_name_size, "%s.%s", name, ext); else snprintf(out_name, out_name_size, "%s", name);
    return 0;
}

static int parse_directory_entries(const DiskContext *ctx, AtariStDiskAnalysis *analysis, const unsigned char *dir_data,
    size_t dir_size, const char *base_path, char *error_buf, size_t error_buf_size) {
    size_t entry_size = 32U;
    size_t offset;
    for (offset = 0; offset + entry_size <= dir_size; offset += entry_size) {
        const unsigned char *entry_data = dir_data + offset;
        unsigned char first = entry_data[0];
        uint8_t attributes;
        char name[13];
        AtariStDiskEntry entry;
        char *path = NULL;
        if (first == 0x00U) return 0;
        if (first == 0xE5U) continue;
        attributes = entry_data[ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_ATTRIBUTES_OFFSET];
        if ((attributes & 0x0FU) == 0x0FU) continue;
        if (format_entry_name(entry_data, name, sizeof(name)) != 0) continue;
        if ((attributes & ATARI_ST_DISK_FILE_DIR_ATTR_DIRECTORY) != 0U && (!strcmp(name, ".") || !strcmp(name, ".."))) continue;
        if (m68k_platform_join_path(base_path, name, &path) != 0) {
            m68k_platform_set_error(error_buf, error_buf_size, "Out of memory");
            return -1;
        }
        memset(&entry, 0, sizeof(entry));
        entry.path = path;
        entry.attributes = attributes;
entry.first_cluster = read_u16le( entry_data, ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_FIRST_CLUSTER_OFFSET);
        entry.file_size = read_u32le(entry_data, ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_FILE_SIZE_OFFSET);
        if ((attributes & ATARI_ST_DISK_FILE_DIR_ATTR_VOLUME_LABEL) != 0U) {
            entry.kind = ATARI_ST_DISK_ENTRY_VOLUME_LABEL;
        } else if ((attributes & ATARI_ST_DISK_FILE_DIR_ATTR_DIRECTORY) != 0U) {
            entry.kind = ATARI_ST_DISK_ENTRY_DIRECTORY;
        } else {
            entry.kind = ATARI_ST_DISK_ENTRY_FILE;
            entry.is_executable_candidate = (uint8_t)(is_executable_candidate_name(name) ? 1U : 0U);
        }
        if ((entry.kind == ATARI_ST_DISK_ENTRY_FILE || entry.kind == ATARI_ST_DISK_ENTRY_DIRECTORY)
            && entry.first_cluster >= 2U) {
            int walk_full_chain = (entry.kind == ATARI_ST_DISK_ENTRY_DIRECTORY);
            if (build_cluster_extents(ctx, entry.first_cluster, entry.file_size, walk_full_chain, &entry) != 0) {
                free(entry.path);
                free(entry.extents);
                m68k_platform_set_error(error_buf, error_buf_size, "Invalid FAT12 cluster chain");
                return -1;
            }
        }
        if (add_entry(analysis, &entry) != 0) {
            free(entry.path);
            free(entry.extents);
            m68k_platform_set_error(error_buf, error_buf_size, "Out of memory");
            return -1;
        }
        if (entry.kind == ATARI_ST_DISK_ENTRY_DIRECTORY && entry.first_cluster >= 2U) {
            unsigned char *subdir_data = NULL;
            size_t subdir_size = 0;
            if (build_directory_buffer(ctx, entry.first_cluster, &subdir_data, &subdir_size) != 0) {
                m68k_platform_set_error(error_buf, error_buf_size, "Invalid FAT12 directory chain");
                return -1;
            }
            if (parse_directory_entries(ctx, analysis, subdir_data, subdir_size, entry.path, error_buf, error_buf_size) != 0) {
                free(subdir_data);
                return -1;
            }
            free(subdir_data);
        }
    }
    return 0;
}

void atari_st_disk_analysis_init(AtariStDiskAnalysis *analysis) {
    if (analysis == NULL) return;
    memset(analysis, 0, sizeof(*analysis));
}

void atari_st_disk_analysis_free(AtariStDiskAnalysis *analysis) {
    size_t i;
    if (analysis == NULL) return;
    for (i = 0; i < analysis->entry_count; ++i) {
        free(analysis->entries[i].path);
        free(analysis->entries[i].extents);
    }
    free(analysis->entries);
    memset(analysis, 0, sizeof(*analysis));
}

int atari_st_disk_analyze_buffer(const unsigned char *data, size_t size, AtariStDiskAnalysis *out_analysis,
    char *error_buf, size_t error_buf_size) {
    DiskContext ctx;
    size_t root_dir_sectors;
    size_t total_size;

    if (out_analysis == NULL) {
        m68k_platform_set_error(error_buf, error_buf_size, "Missing Atari ST disk analysis output");
        return -1;
    }
    atari_st_disk_analysis_init(out_analysis);
    memset(&ctx, 0, sizeof(ctx));

    if (data == NULL && size != 0U) {
        m68k_platform_set_error(error_buf, error_buf_size, "Missing Atari ST disk image data");
        return -1;
    }
    if (size < 512U) {
        m68k_platform_set_error(error_buf, error_buf_size, "Truncated Atari ST disk image");
        return -1;
    }

    ctx.data = data;
    ctx.size = size;
    ctx.bytes_per_sector = read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_BYTES_PER_SECTOR_OFFSET);
    ctx.sectors_per_cluster = data[ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_CLUSTER_OFFSET];
    ctx.reserved_sector_count =
        read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_RESERVED_SECTOR_COUNT_OFFSET);
    ctx.fat_count = data[ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_FAT_COUNT_OFFSET];
    ctx.root_entry_count = read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_ROOT_ENTRY_COUNT_OFFSET);
    ctx.total_sectors = read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_TOTAL_SECTORS_OFFSET);
    ctx.sectors_per_fat = read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_FAT_OFFSET);
    ctx.sectors_per_track = read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_TRACK_OFFSET);
    ctx.side_count = read_u16le(data, ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SIDE_COUNT_OFFSET);

    if (ctx.bytes_per_sector == 0U
        || ctx.sectors_per_cluster == 0U
        || ctx.fat_count == 0U
        || ctx.sectors_per_fat == 0U) {
        m68k_platform_set_error(error_buf, error_buf_size, "Invalid Atari ST BPB");
        return -1;
    }

    ctx.cluster_size_bytes = (size_t)ctx.bytes_per_sector * (size_t)ctx.sectors_per_cluster;
    root_dir_sectors = ((size_t)ctx.root_entry_count * 32U + (size_t)ctx.bytes_per_sector - 1U) / (size_t)ctx.bytes_per_sector;
    ctx.fat_offset = (size_t)ctx.reserved_sector_count * (size_t)ctx.bytes_per_sector;
    ctx.fat_size_bytes = (size_t)ctx.sectors_per_fat * (size_t)ctx.bytes_per_sector;
    ctx.root_dir_offset = ctx.fat_offset + (size_t)ctx.fat_count * ctx.fat_size_bytes;
    ctx.root_dir_size_bytes = root_dir_sectors * (size_t)ctx.bytes_per_sector;
    ctx.data_region_offset = ctx.root_dir_offset + ctx.root_dir_size_bytes;
    total_size = (size_t)ctx.total_sectors * (size_t)ctx.bytes_per_sector;
    ctx.logical_size = total_size;

    if (ctx.total_sectors == 0U || total_size > ctx.size || ctx.root_dir_offset + ctx.root_dir_size_bytes > ctx.size
        || ctx.data_region_offset > ctx.size) {
        m68k_platform_set_error(error_buf, error_buf_size, "Invalid Atari ST disk layout");
        return -1;
    }

    if (ctx.cluster_size_bytes == 0U
        || (ctx.logical_size - ctx.data_region_offset) / ctx.cluster_size_bytes + 1U > 0xFFFFU) {
        m68k_platform_set_error(error_buf, error_buf_size, "Unsupported Atari ST cluster geometry");
        return -1;
    }
    ctx.max_cluster_index = (uint16_t)(1U + (ctx.logical_size - ctx.data_region_offset) / ctx.cluster_size_bytes);

    out_analysis->image_size = (uint32_t)ctx.size;
    out_analysis->bytes_per_sector = ctx.bytes_per_sector;
    out_analysis->sectors_per_cluster = ctx.sectors_per_cluster;
    out_analysis->reserved_sector_count = ctx.reserved_sector_count;
    out_analysis->fat_count = ctx.fat_count;
    out_analysis->root_entry_count = ctx.root_entry_count;
    out_analysis->total_sectors = ctx.total_sectors;
    out_analysis->sectors_per_fat = ctx.sectors_per_fat;
    out_analysis->sectors_per_track = ctx.sectors_per_track;
    out_analysis->side_count = ctx.side_count;

    if (parse_directory_entries(&ctx, out_analysis, data + ctx.root_dir_offset, ctx.root_dir_size_bytes,
            "", error_buf, error_buf_size) != 0) {
        atari_st_disk_analysis_free(out_analysis);
        return -1;
    }
    return 0;
}

int atari_st_disk_analyze_image(const char *path, AtariStDiskAnalysis *out_analysis, char *error_buf,
    size_t error_buf_size) {
    FILE *fp = NULL;
    int64_t file_size_signed = 0;
    unsigned char *buffer = NULL;
    size_t read_size = 0;
    int result;

    fp = fopen(path, "rb");
    if (fp == NULL) {
        m68k_platform_set_error(error_buf, error_buf_size, "Could not open Atari ST disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not size Atari ST disk image");
        return -1;
    }
    file_size_signed = (int64_t)ftell(fp);
    if (file_size_signed < 0) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not size Atari ST disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not rewind Atari ST disk image");
        return -1;
    }
    buffer = (unsigned char *)malloc((size_t)file_size_signed == 0U ? 1U : (size_t)file_size_signed);
    if (buffer == NULL) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Out of memory");
        return -1;
    }
    read_size = fread(buffer, 1, (size_t)file_size_signed, fp);
    fclose(fp);
    if (read_size != (size_t)file_size_signed) {
        free(buffer);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not read Atari ST disk image");
        return -1;
    }
    result = atari_st_disk_analyze_buffer(buffer, (size_t)file_size_signed, out_analysis, error_buf, error_buf_size);
    free(buffer);
    return result;
}
