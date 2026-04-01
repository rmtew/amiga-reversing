#include "platform_amiga_disk.h"
#include "platform_common.h"
#include "generated/amiga_disk_file_runtime.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct DiskContext {
    const unsigned char *data;
    size_t size;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t root_block;
    uint8_t dos_flags;
    int is_ffs;
} DiskContext;

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

static int append_extent(AmigaDiskEntry *entry, uint32_t block_index, uint32_t image_offset, uint32_t byte_size) {
    AmigaDiskExtent *grown = (AmigaDiskExtent *)realloc(entry->extents, (entry->extent_count + 1U) * sizeof(*entry->extents));
    if (grown == NULL) return -1;
    entry->extents = grown;
    entry->extents[entry->extent_count].block_index = block_index;
    entry->extents[entry->extent_count].image_offset = image_offset;
    entry->extents[entry->extent_count].byte_size = byte_size;
    entry->extent_count += 1U;
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
        if (append_extent(entry, block_index, (uint32_t)offset, extent_size) != 0) return -1;
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
        if (append_extent(entry, block_index,
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
        if (append_extent(entry, data_block,
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
    AmigaDiskEntry *grown = (AmigaDiskEntry *)realloc(analysis->entries, (analysis->entry_count + 1U) * sizeof(*analysis->entries));
    if (grown == NULL) return -1;
    analysis->entries = grown;
    analysis->entries[analysis->entry_count] = *entry;
    analysis->entry_count += 1U;
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
    const char *base_path, char *error_buf, size_t error_buf_size) {
    const unsigned char *dir_block;
    size_t block_base = 0;
    uint32_t i;
    if (block_offset(ctx, dir_block_index, &block_base) != 0) {
        m68k_platform_set_error(error_buf, error_buf_size, "Invalid AmigaDOS directory block");
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
            AmigaDiskEntry entry;
            char *path = NULL;
            if (block_offset(ctx, entry_block_index, &entry_base) != 0) {
                m68k_platform_set_error(error_buf, error_buf_size, "Invalid AmigaDOS file header block");
                return -1;
            }
            entry_block = ctx->data + entry_base;
            sec_type = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_SEC_TYPE_OFFSET);
            next_chain = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_HASH_CHAIN_OFFSET);
            if (read_bcpl_name(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_NAME_LEN_OFFSET,
                    AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_NAME_MAX_LENGTH, name, sizeof(name)) != 0) {
                m68k_platform_set_error(error_buf, error_buf_size, "Invalid AmigaDOS entry name");
                return -1;
            }
            if (m68k_platform_join_path(base_path, name, &path) != 0) {
                m68k_platform_set_error(error_buf, error_buf_size, "Out of memory");
                return -1;
            }
            memset(&entry, 0, sizeof(entry));
            entry.path = path;
            entry.header_block = entry_block_index;
            if (sec_type == AMIGA_DISK_FILE_CONSTRAINTS_SEC_TYPE_USERDIR) {
                entry.kind = AMIGA_DISK_ENTRY_DIRECTORY;
            } else if (sec_type == AMIGA_DISK_FILE_CONSTRAINTS_SEC_TYPE_FILE) {
                entry.kind = AMIGA_DISK_ENTRY_FILE;
                entry.byte_size = read_u32be(entry_block, AMIGA_DISK_FILE_CONSTRAINTS_FILE_HEADER_BYTE_SIZE_OFFSET);
                if (build_file_extents(ctx, entry_block, entry.byte_size, &entry) != 0) {
                    free(entry.extents);
                    entry.extents = NULL;
                    entry.extent_count = 0U;
                }
            } else {
                free(entry.path);
                entry_block_index = next_chain;
                steps += 1U;
                if (steps > ctx->total_blocks) {
                    m68k_platform_set_error(error_buf, error_buf_size, "Invalid AmigaDOS hash chain");
                    return -1;
                }
                continue;
            }
            if (add_entry(analysis, &entry) != 0) {
                free(entry.path);
                free(entry.extents);
                m68k_platform_set_error(error_buf, error_buf_size, "Out of memory");
                return -1;
            }
            if (entry.kind == AMIGA_DISK_ENTRY_DIRECTORY
                && parse_directory_block(ctx, analysis, entry_block_index, entry.path, error_buf, error_buf_size) != 0) {
                return -1;
            }
            entry_block_index = next_chain;
            steps += 1U;
            if (steps > ctx->total_blocks) {
                m68k_platform_set_error(error_buf, error_buf_size, "Invalid AmigaDOS hash chain");
                return -1;
            }
        }
    }
    return 0;
}

void amiga_disk_analysis_init(AmigaDiskAnalysis *analysis) {
    if (analysis == NULL) return;
    memset(analysis, 0, sizeof(*analysis));
}

void amiga_disk_analysis_free(AmigaDiskAnalysis *analysis) {
    size_t i;
    if (analysis == NULL) return;
    for (i = 0; i < analysis->entry_count; ++i) {
        free(analysis->entries[i].path);
        free(analysis->entries[i].extents);
    }
    free(analysis->entries);
    memset(analysis, 0, sizeof(*analysis));
}

int amiga_disk_analyze_buffer(const unsigned char *data, size_t size, AmigaDiskAnalysis *out_analysis, char *error_buf,
    size_t error_buf_size) {
    DiskContext ctx;
    size_t root_offset = 0;
    const unsigned char *root_block;
    char volume_name[AMIGA_DISK_FILE_CONSTRAINTS_ROOT_NAME_MAX_LENGTH + 1U];
    AmigaDiskEntry volume_entry;

    if (out_analysis == NULL) {
        m68k_platform_set_error(error_buf, error_buf_size, "Missing Amiga disk analysis output");
        return -1;
    }
    amiga_disk_analysis_init(out_analysis);
    memset(&ctx, 0, sizeof(ctx));

    if (data == NULL && size != 0U) {
        m68k_platform_set_error(error_buf, error_buf_size, "Missing Amiga disk image data");
        return -1;
    }

    ctx.data = data;
    ctx.size = size;
    ctx.block_size = AMIGA_DISK_FILE_CONSTRAINTS_BYTES_PER_SECTOR;
    if (ctx.block_size == 0U || ctx.size % ctx.block_size != 0U) {
        m68k_platform_set_error(error_buf, error_buf_size, "Invalid Amiga disk image size");
        return -1;
    }
    ctx.total_blocks = (uint32_t)(ctx.size / ctx.block_size);
    if (ctx.total_blocks < AMIGA_DISK_FILE_CONSTRAINTS_BOOT_BLOCK_SECTORS) {
        m68k_platform_set_error(error_buf, error_buf_size, "Truncated Amiga disk image");
        return -1;
    }

    out_analysis->image_size = (uint32_t)ctx.size;
    out_analysis->block_size = ctx.block_size;
    out_analysis->total_blocks = ctx.total_blocks;
    if (memcmp(data + AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_MAGIC_OFFSET, "DOS", 3) != 0) {
        out_analysis->format_kind = boot_block_has_code(&ctx)
            ? AMIGA_DISK_FORMAT_NON_DOS_BOOTABLE
            : AMIGA_DISK_FORMAT_NON_DOS_BLANK;
        return 0;
    }
    ctx.dos_flags = data[AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_FLAGS_OFFSET];
    ctx.is_ffs = (ctx.dos_flags & AMIGA_DISK_FILE_DOS_FLAGS_FFS) != 0U;
    ctx.root_block = read_u32be(data, AMIGA_DISK_FILE_BOOT_BLOCK_FIELD_ROOT_BLOCK_OFFSET);
    out_analysis->root_block = ctx.root_block;
    out_analysis->is_dos = 1U;
    out_analysis->dos_flags = ctx.dos_flags;
    if (block_offset(&ctx, ctx.root_block, &root_offset) != 0) {
        out_analysis->format_kind = boot_block_has_code(&ctx)
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
        out_analysis->format_kind = boot_block_has_code(&ctx)
            ? AMIGA_DISK_FORMAT_DOS_CUSTOM_BOOT
            : AMIGA_DISK_FORMAT_DOS_INVALID_ROOT_BLOCK;
        return 0;
    }

    out_analysis->format_kind = AMIGA_DISK_FORMAT_DOS;

    memset(&volume_entry, 0, sizeof(volume_entry));
    volume_entry.kind = AMIGA_DISK_ENTRY_VOLUME;
    volume_entry.header_block = ctx.root_block;
    volume_entry.path = m68k_platform_dup_string(volume_name);
    if (volume_entry.path == NULL || add_entry(out_analysis, &volume_entry) != 0) {
        free(volume_entry.path);
        amiga_disk_analysis_free(out_analysis);
        m68k_platform_set_error(error_buf, error_buf_size, "Out of memory");
        return -1;
    }

    if (parse_directory_block(&ctx, out_analysis, ctx.root_block, "", error_buf, error_buf_size) != 0) {
        amiga_disk_analysis_free(out_analysis);
        return -1;
    }
    return 0;
}

int amiga_disk_analyze_image(const char *path, AmigaDiskAnalysis *out_analysis, char *error_buf,
    size_t error_buf_size) {
    FILE *fp = NULL;
    int64_t file_size_signed = 0;
    unsigned char *buffer = NULL;
    size_t read_size = 0;
    int result;

    fp = fopen(path, "rb");
    if (fp == NULL) {
        m68k_platform_set_error(error_buf, error_buf_size, "Could not open Amiga disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not size Amiga disk image");
        return -1;
    }
    file_size_signed = (int64_t)ftell(fp);
    if (file_size_signed < 0) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not size Amiga disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        m68k_platform_set_error(error_buf, error_buf_size, "Could not rewind Amiga disk image");
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
        m68k_platform_set_error(error_buf, error_buf_size, "Could not read Amiga disk image");
        return -1;
    }
    result = amiga_disk_analyze_buffer(buffer, (size_t)file_size_signed, out_analysis, error_buf, error_buf_size);
    free(buffer);
    return result;
}
