#include "m68k_backend.h"
#include "platform_binary_io.h"
#include "platform_common.h"
#include "generated/amiga_hunk_file_runtime.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    HUNK_UNIT = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_UNIT,
    HUNK_NAME = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_NAME,
    HUNK_CODE = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_CODE,
    HUNK_DATA = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DATA,
    HUNK_BSS = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_BSS,
    HUNK_RELOC32 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32,
    HUNK_RELOC16 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC16,
    HUNK_RELOC8 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC8,
    HUNK_EXT = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_EXT,
    HUNK_SYMBOL = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_SYMBOL,
    HUNK_DEBUG = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DEBUG,
    HUNK_END = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_END,
    HUNK_HEADER = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_HEADER,
    HUNK_BREAK = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_BREAK,
    HUNK_DREL32 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DREL32,
    HUNK_DREL16 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DREL16,
    HUNK_DREL8 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DREL8,
    HUNK_RELOC32SHORT = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32SHORT,
    HUNK_RELRELOC32 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELRELOC32,
    HUNK_ABSRELOC16 = AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_ABSRELOC16,
    HUNK_TYPE_ID_MASK = AMIGA_HUNK_FILE_HUNK_TYPE_WORD_VALUE_MASK,
    HUNK_SIZE_LONGS_MASK = AMIGA_HUNK_FILE_SIZE_LONGS_WORD_VALUE_MASK,
    HUNK_MEM_SHIFT = AMIGA_HUNK_FILE_HUNK_TYPE_WORD_CHIP_BIT
};

typedef M68kBinaryReader Reader;
typedef M68kBinaryWriter Writer;

static void platform_file_diag_error(M68kDiagSink diagnostics, const char *message) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, message);
}

static void platform_file_diag_errorf(M68kDiagSink diagnostics, const char *fmt, ...) {
    M68kDiag *diag;
    va_list args;
    if (diagnostics.list == NULL) return;
    if (diagnostics.list->count >= M68K_DIAG_LIST_CAPACITY) {
        diagnostics.list->dropped_count += 1U;
        return;
    }
    diag = &diagnostics.list->items[diagnostics.list->count++];
    memset(diag, 0, sizeof(*diag));
    diag->severity = M68K_DIAG_SEVERITY_ERROR;
    diag->code = M68K_DIAG_CODE_PLATFORM_FILE_FAILED;
    if (fmt == NULL) return;
    va_start(args, fmt);
    vsnprintf(diag->message, sizeof(diag->message), fmt, args);
    va_end(args);
}

typedef struct AmigaHunkPlatformData {
    char *unit_name;
    uint32_t header_count;
    uint32_t header_first_hunk;
    uint32_t header_last_hunk;
    uint32_t *header_size_words;
    uint32_t *header_mem_attrs;
    uint32_t *section_empty_reloc_masks;
} AmigaHunkPlatformData;

/* Basic IO and string helpers. */


static int read_bstr(Reader *reader, char **out_text) {
    uint32_t longs = 0;
    size_t bytes;
    unsigned char *raw = NULL;
    size_t trim;
    char *text;
    if (m68k_reader_read_u32be(reader, &longs) != 0) return -1;
    bytes = (size_t)longs * 4U;
    raw = (unsigned char *)malloc(bytes == 0U ? 1U : bytes);
    if (raw == NULL) return -1;
    if (m68k_reader_read_bytes(reader, raw, bytes) != 0) {
        free(raw);
        return -1;
    }
    trim = bytes;
    while (trim > 0U && raw[trim - 1U] == 0U) {
        --trim;
    }
    text = (char *)malloc(trim + 1U);
    if (text == NULL) {
        free(raw);
        return -1;
    }
    if (trim != 0U) {
        memcpy(text, raw, trim);
    }
    text[trim] = '\0';
    free(raw);
    *out_text = text;
    return 0;
}

static int writer_bstr(Writer *writer, const char *text) {
    size_t length = strlen(text);
    uint32_t longs = (uint32_t)((length + 3U) / 4U);
    size_t padded = (size_t)longs * 4U;
    static const unsigned char zeros[4] = {0U, 0U, 0U, 0U};
    if (m68k_writer_u32be(writer, longs) != 0) return -1;
    if (length != 0U && m68k_writer_bytes(writer, (const unsigned char *)text, length) != 0) return -1;
    if (padded > length && m68k_writer_bytes(writer, zeros, padded - length) != 0) return -1;
    return 0;
}

static int writer_padded_name(Writer *writer, const char *text) {
    size_t length = strlen(text);
    size_t padded = ((length + 3U) / 4U) * 4U;
    static const unsigned char zeros[4] = {0U, 0U, 0U, 0U};
    if (length != 0U && m68k_writer_bytes(writer, (const unsigned char *)text, length) != 0) return -1;
    if (padded > length && m68k_writer_bytes(writer, zeros, padded - length) != 0) return -1;
    return 0;
}

/* Generated metadata lookup helpers. */

static AmigaHunkFileRecordKind record_kind_from_wire_id(uint32_t wire_id) {
    const AmigaHunkFileRecordInfo *info = amiga_hunk_file_record_info_by_wire_id(wire_id);
    return (info != NULL) ? info->record_kind : AMIGA_HUNK_FILE_META_RECORD_KIND_NONE;
}

static AmigaHunkFileRecordRole record_role_from_wire_id(uint32_t wire_id) {
    const AmigaHunkFileRecordInfo *info = amiga_hunk_file_record_info_by_wire_id(wire_id);
    return (info != NULL) ? info->role : AMIGA_HUNK_FILE_META_RECORD_ROLE_UNKNOWN;
}

static AmigaHunkFileRecordKind interpret_record_kind(int is_executable, AmigaHunkFileRecordKind record_kind) {
    AmigaHunkFileContainerKind container_kind = is_executable
        ? AMIGA_HUNK_FILE_META_CONTAINER_KIND_EXECUTABLE
        : AMIGA_HUNK_FILE_META_CONTAINER_KIND_OBJECT;
    const AmigaHunkFileInterpretationRule *rule = amiga_hunk_file_interpretation_rule_lookup(container_kind, record_kind);
    return (rule != NULL) ? rule->interpreted_kind : record_kind;
}

static M68kSectionKind map_record_section_kind(AmigaHunkFileSectionKind section_kind) {
    if (section_kind == AMIGA_HUNK_FILE_META_SECTION_KIND_CODE) return M68K_SECTION_CODE;
    if (section_kind == AMIGA_HUNK_FILE_META_SECTION_KIND_DATA) return M68K_SECTION_DATA;
    return M68K_SECTION_BSS;
}

static M68kSectionKind map_hunk_kind(uint32_t hunk_type) {
    const AmigaHunkFileRecordInfo *info = amiga_hunk_file_record_info_by_wire_id(hunk_type);
    if (info == NULL) return M68K_SECTION_BSS;
    return map_record_section_kind(info->section_kind);
}

static uint32_t unmap_hunk_kind(M68kSectionKind kind) {
    AmigaHunkFileSectionKind wanted = (kind == M68K_SECTION_CODE)
        ? AMIGA_HUNK_FILE_META_SECTION_KIND_CODE
        : (kind == M68K_SECTION_DATA) ? AMIGA_HUNK_FILE_META_SECTION_KIND_DATA : AMIGA_HUNK_FILE_META_SECTION_KIND_BSS;
    const AmigaHunkFileRecordInfo *info = amiga_hunk_file_record_info_for_section_kind(wanted);
    if (info != NULL) return info->wire_id;
    return HUNK_BSS;
}

static M68kFixupKind map_relocation_mode_to_fixup_kind(AmigaHunkFileRelocationMode mode) {
    if (mode == AMIGA_HUNK_FILE_META_RELOCATION_MODE_ABSOLUTE) return M68K_FIXUP_ABS;
    if (mode == AMIGA_HUNK_FILE_META_RELOCATION_MODE_PC_RELATIVE) return M68K_FIXUP_PC_REL;
    return M68K_FIXUP_SECTION_REL;
}

static M68kFixupWidth map_width_bytes_to_fixup_width(unsigned width_bytes) {
    if (width_bytes == 1U) return M68K_FIXUP_WIDTH_8;
    if (width_bytes == 2U) return M68K_FIXUP_WIDTH_16;
    return M68K_FIXUP_WIDTH_32;
}

static AmigaHunkFileRelocationMode fixup_kind_to_relocation_mode(M68kFixupKind kind) {
    if (kind == M68K_FIXUP_ABS) return AMIGA_HUNK_FILE_META_RELOCATION_MODE_ABSOLUTE;
    if (kind == M68K_FIXUP_PC_REL) return AMIGA_HUNK_FILE_META_RELOCATION_MODE_PC_RELATIVE;
    return AMIGA_HUNK_FILE_META_RELOCATION_MODE_DATA_RELATIVE;
}

static unsigned fixup_width_to_bytes(M68kFixupWidth width) {
    if (width == M68K_FIXUP_WIDTH_8) return 1U;
    if (width == M68K_FIXUP_WIDTH_16) return 2U;
    return 4U;
}

static int map_relocation_kind(int is_executable, uint32_t wire_id, M68kFixupKind *out_kind, M68kFixupWidth *out_width,
    int *out_short_counts) {
    const AmigaHunkFileRelocationKind *reloc;
    AmigaHunkFileRecordKind record_kind = interpret_record_kind(is_executable, record_kind_from_wire_id(wire_id));
    reloc = amiga_hunk_file_relocation_kind_lookup(record_kind);
    if (reloc == NULL) return -1;
    *out_kind = map_relocation_mode_to_fixup_kind(reloc->mode);
    *out_width = map_width_bytes_to_fixup_width(reloc->width_bytes);
    *out_short_counts = (record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32SHORT) ? 1 : 0;
    return 0;
}

static AmigaHunkFileExtVariant ext_variant_from_type(uint32_t ext_type) {
    const AmigaHunkFileExtVariantInfo *info = amiga_hunk_file_ext_variant_lookup(ext_type);
    if (info != NULL) return info->variant;
    return AMIGA_HUNK_FILE_META_EXT_VARIANT_NONE;
}

static const AmigaHunkFileExtReferenceKind *find_ext_reference_kind(uint32_t ext_type) {
    return amiga_hunk_file_ext_reference_kind_lookup(ext_type);
}

static int ext_type_to_fixup(uint32_t ext_type, M68kFixupKind *out_kind, M68kFixupWidth *out_width) {
    const AmigaHunkFileExtReferenceKind *info = find_ext_reference_kind(ext_type);
    if (info == NULL) return -1;
    *out_kind = map_relocation_mode_to_fixup_kind(info->mode);
    *out_width = map_width_bytes_to_fixup_width(info->width_bytes);
    return 0;
}

static int fixup_to_ext_type(const M68kFixup *fixup, uint32_t *out_ext_type) {
    AmigaHunkFileRelocationMode mode = fixup_kind_to_relocation_mode(fixup->kind);
    unsigned width_bytes = fixup_width_to_bytes(fixup->width);
    const AmigaHunkFileExtReferenceKind *info = amiga_hunk_file_ext_reference_kind_lookup_by_mode_width(mode, width_bytes);
    if (info != NULL) {
        *out_ext_type = info->ext_type;
        return 0;
    }
    return -1;
}

/* Object mutation helpers. */

static M68kObjectAddResult add_symbol(M68kObject *object, const char *name, M68kSymbolBinding binding, int defined,
    size_t section_index, uint32_t value);
static int find_symbol_index(const M68kObject *object, const char *name, M68kSymbolBinding binding, int defined,
    size_t *out_index);
static int add_fixup(M68kObject *object, size_t section_index, uint32_t offset, uint32_t target_section,
    M68kFixupKind kind, M68kFixupWidth width, AmigaHunkFileRecordKind record_kind, uint32_t record_wire_id,
    uint32_t block_index, uint32_t group_index);
static int add_symbol_fixup(M68kObject *object, size_t section_index, uint32_t offset, size_t symbol_index,
    M68kFixupKind kind, M68kFixupWidth width);
static int parse_symbol_block(Reader *reader, M68kObject *object, size_t section_index, M68kDiagSink diagnostics);
static int parse_debug_block(Reader *reader, M68kObject *object, size_t section_index, M68kDiagSink diagnostics);
static int parse_reloc_block(Reader *reader, M68kObject *object, size_t section_index, AmigaHunkFileRecordKind record_kind,
    uint32_t record_wire_id, uint32_t block_index, M68kFixupKind kind, M68kFixupWidth width, int short_counts,
    M68kDiagSink diagnostics);
static int parse_ext_block(Reader *reader, M68kObject *object, size_t section_index, M68kDiagSink diagnostics);
static int parse_section_body(Reader *reader, M68kObject *object, size_t section_index, int is_executable,
    M68kDiagSink diagnostics);
static int add_section_from_hunk(M68kObject *object, uint32_t raw_type, const char *section_name, uint32_t alloc_size,
    uint32_t mem_attrs, Reader *reader, int is_executable, M68kDiagSink diagnostics);
static int parse_hunk_executable(Reader *reader, M68kObject *object, M68kDiagSink diagnostics);
static int parse_hunk_object(Reader *reader, M68kObject *object, M68kDiagSink diagnostics);
static int amiga_hunk_read_buffer(const unsigned char *data, size_t size, M68kObject *out_object, M68kDiagSink diagnostics);
static int amiga_hunk_read_file(const char *path, M68kObject *out_object, M68kDiagSink diagnostics);
static int amiga_hunk_write_buffer(const M68kObject *object, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics);
static int amiga_hunk_write_file(const char *path, const M68kObject *object, M68kDiagSink diagnostics);

static int ensure_amiga_hunk_platform_data(M68kObject *object, AmigaHunkPlatformData **out_data) {
    AmigaHunkPlatformData *platform_data = (AmigaHunkPlatformData *)object->platform_data;
    if (platform_data == NULL) {
        platform_data = (AmigaHunkPlatformData *)m68k_object_alloc(object, sizeof(*platform_data));
        if (platform_data == NULL) return -1;
        memset(platform_data, 0, sizeof(*platform_data));
        object->platform_data = platform_data;
    }
    *out_data = platform_data;
    return 0;
}

const M68kBackend M68K_BACKEND_AMIGA_HUNK = {
    "amiga-hunk",
    amiga_hunk_read_file,
    amiga_hunk_read_buffer,
    amiga_hunk_write_buffer,
    amiga_hunk_write_file,
};

static int find_symbol_index(const M68kObject *object, const char *name, M68kSymbolBinding binding, int defined,
    size_t *out_index) {
    size_t i;
    for (i = 0; i < object->symbol_count; ++i) {
        const M68kSymbol *symbol = &object->symbols[i];
        if (symbol->binding == binding
            && symbol->defined == defined
            && strcmp(symbol->name != NULL ? symbol->name : "", name) == 0) {
            *out_index = i;
            return 0;
        }
    }
    return -1;
}

static M68kObjectAddResult add_symbol(M68kObject *object, const char *name, M68kSymbolBinding binding, int defined,
    size_t section_index, uint32_t value) {
    M68kObjectAddResult result = {0};
    M68kSymbol symbol;
    size_t existing_index = 0;
    if (find_symbol_index(object, name, binding, defined, &existing_index) == 0) {
        result.ok = 1U;
        result.index = existing_index;
        return result;
    }
    memset(&symbol, 0, sizeof(symbol));
    symbol.name = (char *)name;
    symbol.binding = binding;
    symbol.defined = defined;
    symbol.section_index = section_index;
    symbol.value = value;
    return m68k_object_add_symbol(object, &symbol);
}

static int add_fixup(M68kObject *object, size_t section_index, uint32_t offset, uint32_t target_section,
    M68kFixupKind kind, M68kFixupWidth width, AmigaHunkFileRecordKind record_kind, uint32_t record_wire_id,
    uint32_t block_index, uint32_t group_index) {
    M68kFixup fixup;
    memset(&fixup, 0, sizeof(fixup));
    fixup.section_index = section_index;
    fixup.offset = offset;
    fixup.kind = kind;
    fixup.width = width;
    fixup.target_section_index = target_section;
    fixup.has_target_section = 1;
    fixup.platform_relocation_record_kind = (uint32_t)record_kind;
    fixup.platform_relocation_record_wire_id = record_wire_id;
    fixup.platform_relocation_block_index = block_index;
    fixup.platform_relocation_group_index = group_index;
    return m68k_object_add_fixup(object, &fixup).ok ? 0 : -1;
}

static uint32_t empty_reloc_mask_bit(AmigaHunkFileRecordKind record_kind) {
    switch (record_kind) {
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32: return 1u << 0;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC16: return 1u << 1;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC8: return 1u << 2;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL32: return 1u << 3;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL16: return 1u << 4;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL8: return 1u << 5;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELRELOC32: return 1u << 6;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_ABSRELOC16: return 1u << 7;
        case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32SHORT: return 1u << 8;
        default: return 0U;
    }
}

static void record_empty_internal_reloc(M68kObject *object, size_t section_index, AmigaHunkFileRecordKind record_kind) {
    AmigaHunkPlatformData *platform_data = (AmigaHunkPlatformData *)object->platform_data;
    uint32_t mask_bit = empty_reloc_mask_bit(record_kind);
    if (platform_data == NULL || platform_data->section_empty_reloc_masks == NULL || mask_bit == 0U) return;
    if (section_index >= object->section_count) return;
    platform_data->section_empty_reloc_masks[section_index] |= mask_bit;
}

static int add_symbol_fixup(M68kObject *object, size_t section_index, uint32_t offset, size_t symbol_index,
    M68kFixupKind kind, M68kFixupWidth width) {
    M68kFixup fixup;
    memset(&fixup, 0, sizeof(fixup));
    fixup.section_index = section_index;
    fixup.offset = offset;
    fixup.kind = kind;
    fixup.width = width;
    fixup.symbol_index = symbol_index;
    fixup.has_symbol = 1;
    return m68k_object_add_fixup(object, &fixup).ok ? 0 : -1;
}

static int parse_symbol_block(Reader *reader, M68kObject *object, size_t section_index, M68kDiagSink diagnostics) {
    uint32_t longs = 0;
    while (1) {
        char *name = NULL;
        uint32_t value = 0;
        if (m68k_reader_peek_u32be(reader, &longs) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_SYMBOL");
            return -1;
        }
        if (longs == 0U) {
            if (m68k_reader_read_u32be(reader, &longs) != 0) return -1;
            break;
        }
        if (read_bstr(reader, &name) != 0) {
            platform_file_diag_error(diagnostics, "Failed reading HUNK_SYMBOL name");
            return -1;
        }
        if (m68k_reader_read_u32be(reader, &value) != 0) {
            free(name);
            platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_SYMBOL value");
            return -1;
        }
        if (!add_symbol(object, name, M68K_SYMBOL_LOCAL, 1, section_index, value).ok) {
            free(name);
            platform_file_diag_error(diagnostics, "Failed adding symbol");
            return -1;
        }
        free(name);
    }
    return 0;
}

static int parse_debug_block(Reader *reader, M68kObject *object, size_t section_index, M68kDiagSink diagnostics) {
    uint32_t longs = 0;
    uint8_t *debug_data = NULL;
    if (m68k_reader_read_u32be(reader, &longs) != 0) {
        platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_DEBUG");
        return -1;
    }
    object->sections[section_index].debug_size = longs * 4U;
    if (object->sections[section_index].debug_size != 0U) {
        debug_data = (uint8_t *)malloc(object->sections[section_index].debug_size);
        if (debug_data == NULL) {
            platform_file_diag_error(diagnostics, "Out of memory reading HUNK_DEBUG payload");
            return -1;
        }
    }
    if (m68k_reader_read_bytes(reader, debug_data, (size_t)longs * 4U) != 0) {
        free(debug_data);
        platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_DEBUG payload");
        return -1;
    }
    if (m68k_object_set_section_debug_data(object, section_index, debug_data, object->sections[section_index].debug_size) != 0) {
        free(debug_data);
        platform_file_diag_error(diagnostics, "Out of memory storing HUNK_DEBUG payload");
        return -1;
    }
    free(debug_data);
    return 0;
}

static int parse_reloc_block(Reader *reader, M68kObject *object, size_t section_index, AmigaHunkFileRecordKind record_kind,
    uint32_t record_wire_id, uint32_t block_index, M68kFixupKind kind, M68kFixupWidth width, int short_counts,
    M68kDiagSink diagnostics) {
    uint32_t group_index = 0U;
    m68k_object_add_container_layout(object, M68K_CONTAINER_LAYOUT_AMIGA_HUNK_RELOCATION_BLOCK,
        M68K_CONTAINER_LAYOUT_FLAG_RELOCATION, (uint32_t)record_kind, (uint32_t)section_index);
    m68k_object_add_container_encoding(object, M68K_CONTAINER_ENCODING_AMIGA_HUNK_RELOCATION_WIRE_ID,
        M68K_CONTAINER_LAYOUT_FLAG_RELOCATION, record_wire_id, block_index);
    while (1) {
        uint32_t count = 0;
        uint32_t target = 0;
        uint32_t i;
        if (short_counts) {
            uint16_t short_count = 0;
            uint16_t short_target = 0;
            if (m68k_reader_read_u16be(reader, &short_count) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_RELOC32SHORT");
                return -1;
            }
            count = short_count;
            if (count == 0U) {
                record_empty_internal_reloc(object, section_index, record_kind);
                if ((reader->pos & 3U) != 0U) {
                    if (m68k_reader_skip(reader, 2U) != 0) {
                        platform_file_diag_error(diagnostics, "Unexpected EOF aligning HUNK_RELOC32SHORT");
                        return -1;
                    }
                }
                break;
            }
            if (m68k_reader_read_u16be(reader, &short_target) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_RELOC32SHORT target");
                return -1;
            }
            target = short_target;
        } else {
            if (m68k_reader_read_u32be(reader, &count) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in relocation block");
                return -1;
            }
            if (count == 0U) {
                record_empty_internal_reloc(object, section_index, record_kind);
                break;
            }
            if (m68k_reader_read_u32be(reader, &target) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in relocation target");
                return -1;
            }
        }
        if (count == 0U) break;
        ++group_index;
        for (i = 0; i < count; ++i) {
            uint32_t offset = 0;
            if (short_counts) {
                uint16_t short_offset = 0;
                if (m68k_reader_read_u16be(reader, &short_offset) != 0) {
                    platform_file_diag_error(diagnostics, "Unexpected EOF in short reloc offsets");
                    return -1;
                }
                offset = short_offset;
            } else {
                if (m68k_reader_read_u32be(reader, &offset) != 0) {
                    platform_file_diag_error(diagnostics, "Unexpected EOF in relocation offsets");
                    return -1;
                }
            }
            if (add_fixup(object, section_index, offset, target, kind, width, record_kind, record_wire_id,
                    block_index, group_index) != 0) {
                platform_file_diag_error(diagnostics, "Failed adding relocation");
                return -1;
            }
        }
    }
    return 0;
}

static int parse_ext_block(Reader *reader, M68kObject *object, size_t section_index, M68kDiagSink diagnostics) {
    uint32_t tag = 0;
    while (1) {
        uint32_t ext_type = 0, name_longs = 0, count = 0, i;
        size_t name_bytes = 0, name_length = 0, symbol_index = 0;
        char *name = NULL;
        AmigaHunkFileExtVariant ext_variant;
        M68kFixupKind kind = M68K_FIXUP_ABS;
        M68kFixupWidth width = M68K_FIXUP_WIDTH_32;
        if (m68k_reader_read_u32be(reader, &tag) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_EXT");
            return -1;
        }
        if (tag == 0U) break;
        ext_type = tag >> 24;
        name_longs = tag & 0xFFFFFFU;
        ext_variant = ext_variant_from_type(ext_type);
        name_bytes = (size_t)name_longs * 4U;
        name = (char *)malloc(name_bytes + 1U);
        if (name == NULL) return -1;
        if (m68k_reader_read_bytes(reader, (unsigned char *)name, name_bytes) != 0) {
            free(name);
            platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_EXT name");
            return -1;
        }
        name_length = name_bytes;
        while (name_length > 0U && name[name_length - 1U] == '\0') {
            --name_length;
        }
        name[name_length] = '\0';
        if (ext_variant == AMIGA_HUNK_FILE_META_EXT_VARIANT_DEFINITION) {
            uint32_t value = 0;
            if (m68k_reader_read_u32be(reader, &value) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_EXT definition");
                free(name);
                return -1;
            }
            if (ext_type == AMIGA_HUNK_FILE_EXT_TYPE_EXT_DEF || ext_type == AMIGA_HUNK_FILE_EXT_TYPE_EXT_ABS) {
                if (!add_symbol(object, name, M68K_SYMBOL_GLOBAL, 1, section_index, value).ok) {
                    free(name);
                    platform_file_diag_error(diagnostics, "Failed adding HUNK_EXT definition");
                    return -1;
                }
            }
        } else if (ext_variant == AMIGA_HUNK_FILE_META_EXT_VARIANT_REFERENCE
            || ext_variant == AMIGA_HUNK_FILE_META_EXT_VARIANT_COMMON_REFERENCE) {
            if (ext_variant == AMIGA_HUNK_FILE_META_EXT_VARIANT_COMMON_REFERENCE) {
                if (m68k_reader_skip(reader, 4U) != 0) {
                    platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_EXT common size");
                    free(name);
                    return -1;
                }
            }
            if (m68k_reader_read_u32be(reader, &count) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_EXT count");
                free(name);
                return -1;
            }
            if (ext_type_to_fixup(ext_type, &kind, &width) != 0) {
                free(name);
                platform_file_diag_error(diagnostics, "Unsupported HUNK_EXT reference type");
                return -1;
            }
            M68kObjectAddResult symbol_result = add_symbol(object, name, M68K_SYMBOL_EXTERNAL, 0, 0U, 0U);
            if (!symbol_result.ok) {
                free(name);
                platform_file_diag_error(diagnostics, "Failed adding HUNK_EXT external symbol");
                return -1;
            }
            symbol_index = symbol_result.index;
            for (i = 0; i < count; ++i) {
                uint32_t offset = 0;
                if (m68k_reader_read_u32be(reader, &offset) != 0) {
                    platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_EXT refs");
                    free(name);
                    return -1;
                }
                if (add_symbol_fixup(object, section_index, offset, symbol_index, kind, width) != 0) {
                    free(name);
                    platform_file_diag_error(diagnostics, "Failed adding HUNK_EXT reference fixup");
                    return -1;
                }
            }
        } else {
            platform_file_diag_error(diagnostics, "Unsupported HUNK_EXT subtype");
            free(name);
            return -1;
        }
        free(name);
    }
    return 0;
}

/* Reader implementation. */

static int parse_section_body(Reader *reader, M68kObject *object, size_t section_index, int is_executable,
    M68kDiagSink diagnostics) {
    uint32_t relocation_block_index = 0U;
    while (reader->pos < reader->size) {
        uint32_t raw = 0;
        uint32_t hunk_id = 0;
        AmigaHunkFileRecordKind interpreted_kind;
        AmigaHunkFileRecordRole role;
        if (m68k_reader_peek_u32be(reader, &raw) != 0) return 0;
        hunk_id = raw & HUNK_TYPE_ID_MASK;
        interpreted_kind = interpret_record_kind(is_executable, record_kind_from_wire_id(hunk_id));
        role = record_role_from_wire_id(hunk_id);
        if (role == AMIGA_HUNK_FILE_META_RECORD_ROLE_SECTION_TERMINATOR) {
            if (m68k_reader_read_u32be(reader, &raw) != 0) return -1;
            return 0;
        }
        if (m68k_reader_read_u32be(reader, &raw) != 0) return -1;
        if (hunk_id == HUNK_SYMBOL) {
            if (parse_symbol_block(reader, object, section_index, diagnostics) != 0) return -1;
        } else if (hunk_id == HUNK_DEBUG) {
            if (parse_debug_block(reader, object, section_index, diagnostics) != 0) return -1;
        } else if (amiga_hunk_file_relocation_kind_lookup(interpreted_kind) != NULL) {
            M68kFixupKind kind;
            M68kFixupWidth width;
            int short_counts;
            if (map_relocation_kind(is_executable, hunk_id, &kind, &width, &short_counts) != 0) {
                platform_file_diag_error(diagnostics, "Unsupported relocation record");
                return -1;
            }
            ++relocation_block_index;
            if (parse_reloc_block(reader, object, section_index, interpreted_kind, hunk_id,
                    relocation_block_index, kind, width, short_counts, diagnostics) != 0) {
                return -1;
            }
        } else if (hunk_id == HUNK_EXT) {
            if (parse_ext_block(reader, object, section_index, diagnostics) != 0) return -1;
        } else if (role == AMIGA_HUNK_FILE_META_RECORD_ROLE_SECTION_START
            || hunk_id == HUNK_NAME
            || hunk_id == HUNK_UNIT) {
            reader->pos -= 4U;
            return 0;
        } else {
            uint32_t longs = 0;
            if (m68k_reader_read_u32be(reader, &longs) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in unknown hunk payload");
                return -1;
            }
            if (m68k_reader_skip(reader, (size_t)longs * 4U) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in unknown hunk payload");
                return -1;
            }
        }
    }
    return 0;
}

static int add_section_from_hunk(M68kObject *object, uint32_t raw_type, const char *section_name, uint32_t alloc_size,
    uint32_t mem_attrs, Reader *reader, int is_executable, M68kDiagSink diagnostics) {
    M68kSection section;
    uint32_t hunk_type = raw_type & HUNK_TYPE_ID_MASK;
    uint32_t mem_type = raw_type >> HUNK_MEM_SHIFT;
    uint32_t num_longs = 0;
    size_t section_index = 0;
    memset(&section, 0, sizeof(section));
    section.name = (char *)section_name;
    section.kind = map_hunk_kind(hunk_type);
    section.platform_mem_type = (uint8_t)mem_type;
    section.platform_mem_attrs = mem_attrs;
    if (mem_type == 3U && mem_attrs == 0U) {
        if (m68k_reader_read_u32be(reader, &section.platform_mem_attrs) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF in extended memory attrs");
            return -1;
        }
    }
    if (m68k_reader_read_u32be(reader, &num_longs) != 0) {
        platform_file_diag_error(diagnostics, "Unexpected EOF in section size");
        return -1;
    }
    if (hunk_type == HUNK_BSS) {
        section.size = (alloc_size != 0U) ? alloc_size : (num_longs * 4U);
    } else {
        section.data_size = num_longs * 4U;
        section.size = (alloc_size != 0U) ? alloc_size : section.data_size;
        if (section.data_size != 0U) {
            section.data = (uint8_t *)malloc(section.data_size);
            if (section.data == NULL) return -1;
            if (m68k_reader_read_bytes(reader, section.data, section.data_size) != 0) {
                free(section.data);
                platform_file_diag_error(diagnostics, "Unexpected EOF in section payload");
                return -1;
            }
        }
    }
    M68kObjectAddResult section_result = m68k_object_add_section(object, &section);
    if (!section_result.ok) {
        free(section.data);
        platform_file_diag_error(diagnostics, "Failed adding section");
        return -1;
    }
    section_index = section_result.index;
    m68k_object_add_container_layout(object, M68K_CONTAINER_LAYOUT_AMIGA_HUNK_SECTION,
        M68K_CONTAINER_LAYOUT_FLAG_PAYLOAD, (uint32_t)record_kind_from_wire_id(hunk_type), (uint32_t)section_index);
    m68k_object_add_container_encoding(object, M68K_CONTAINER_ENCODING_AMIGA_HUNK_RECORD_WIRE_ID,
        M68K_CONTAINER_LAYOUT_FLAG_PAYLOAD, hunk_type, raw_type);
    free(section.data);
    if (parse_section_body(reader, object, section_index, is_executable, diagnostics) != 0) return -1;
    return 0;
}

static int parse_hunk_executable(Reader *reader, M68kObject *object, M68kDiagSink diagnostics) {
    AmigaHunkPlatformData *platform_data = NULL;
    uint32_t value = 0, first_hunk = 0, last_hunk = 0, i, count;
    uint32_t *alloc_sizes = NULL;
    uint32_t *mem_attrs = NULL;
    uint32_t *header_size_words = NULL;

    object->platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
    m68k_object_add_container_layout(object, M68K_CONTAINER_LAYOUT_AMIGA_HUNK_CONTAINER,
        M68K_CONTAINER_LAYOUT_FLAG_HEADER, AMIGA_HUNK_FILE_META_CONTAINER_KIND_EXECUTABLE, 0U);
    m68k_object_add_container_encoding(object, M68K_CONTAINER_ENCODING_AMIGA_HUNK_RECORD_WIRE_ID,
        M68K_CONTAINER_LAYOUT_FLAG_HEADER, HUNK_HEADER, 0U);
    if (ensure_amiga_hunk_platform_data(object, &platform_data) != 0) {
        platform_file_diag_error(diagnostics, "Out of memory allocating Amiga hunk platform metadata");
        return -1;
    }
    do {
        if (m68k_reader_read_u32be(reader, &value) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_HEADER names");
            goto fail;
        }
        if (m68k_reader_skip(reader, (size_t)value * 4U) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_HEADER names");
            goto fail;
        }
    } while (value != 0U);

    if (m68k_reader_read_u32be(reader, &count) != 0
        || m68k_reader_read_u32be(reader, &first_hunk) != 0
        || m68k_reader_read_u32be(reader, &last_hunk) != 0) {
        platform_file_diag_error(diagnostics, "Unexpected EOF in HUNK_HEADER table");
        goto fail;
    }
    (void)count;
    count = last_hunk - first_hunk + 1U;
    alloc_sizes = (uint32_t *)calloc(count, sizeof(*alloc_sizes));
    mem_attrs = (uint32_t *)calloc(count, sizeof(*mem_attrs));
    header_size_words = (uint32_t *)calloc(count, sizeof(*header_size_words));
    if (alloc_sizes == NULL || mem_attrs == NULL || header_size_words == NULL) {
        platform_file_diag_error(diagnostics, "Out of memory allocating hunk table");
        goto fail;
    }
    platform_data->section_empty_reloc_masks = (uint32_t *)m68k_object_alloc(object,
        count * sizeof(*platform_data->section_empty_reloc_masks));
    if (platform_data->section_empty_reloc_masks == NULL) {
        platform_file_diag_error(diagnostics, "Out of memory allocating hunk metadata");
        goto fail;
    }
    memset(platform_data->section_empty_reloc_masks, 0, count * sizeof(*platform_data->section_empty_reloc_masks));
    for (i = 0; i < count; ++i) {
        if (m68k_reader_read_u32be(reader, &value) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF in hunk size table");
            goto fail;
        }
        header_size_words[i] = value;
        alloc_sizes[i] = (value & HUNK_SIZE_LONGS_MASK) * 4U;
        if ((value >> HUNK_MEM_SHIFT) == 3U) {
            if (m68k_reader_read_u32be(reader, &mem_attrs[i]) != 0) {
                platform_file_diag_error(diagnostics, "Unexpected EOF in extended mem attrs");
                goto fail;
            }
        }
    }
    for (i = 0; i < count; ++i) {
        if (m68k_reader_read_u32be(reader, &value) != 0) {
            platform_file_diag_error(diagnostics, "Unexpected EOF before executable section");
            goto fail;
        }
        if (add_section_from_hunk(object, value, "", alloc_sizes[i], mem_attrs[i], reader, 1, diagnostics) != 0) {
            goto fail;
        }
    }
    platform_data->header_count = count;
    platform_data->header_first_hunk = first_hunk;
    platform_data->header_last_hunk = last_hunk;
    platform_data->header_size_words = (uint32_t *)m68k_object_memdup(object, header_size_words, count * sizeof(*header_size_words));
    platform_data->header_mem_attrs = (uint32_t *)m68k_object_memdup(object, mem_attrs, count * sizeof(*mem_attrs));
    if (platform_data->header_size_words == NULL || platform_data->header_mem_attrs == NULL) {
        platform_file_diag_error(diagnostics, "Out of memory storing hunk metadata");
        goto fail;
    }
    free(alloc_sizes);
    free(mem_attrs);
    free(header_size_words);
    return 0;

fail:
    free(alloc_sizes);
    free(mem_attrs);
    free(header_size_words);
    return -1;
}

static int parse_hunk_object(Reader *reader, M68kObject *object, M68kDiagSink diagnostics) {
    AmigaHunkPlatformData *platform_data = NULL;
    object->platform_file_kind = M68K_PLATFORM_FILE_OBJECT;
    m68k_object_add_container_layout(object, M68K_CONTAINER_LAYOUT_AMIGA_HUNK_CONTAINER,
        M68K_CONTAINER_LAYOUT_FLAG_HEADER, AMIGA_HUNK_FILE_META_CONTAINER_KIND_OBJECT, 0U);
    m68k_object_add_container_encoding(object, M68K_CONTAINER_ENCODING_AMIGA_HUNK_RECORD_WIRE_ID,
        M68K_CONTAINER_LAYOUT_FLAG_HEADER, HUNK_UNIT, 0U);
    if (ensure_amiga_hunk_platform_data(object, &platform_data) != 0) {
        platform_file_diag_error(diagnostics, "Out of memory allocating Amiga hunk platform metadata");
        return -1;
    }
    while (reader->pos < reader->size) {
        char *unit_name = NULL;
        char *pending_name = NULL;
        uint32_t raw = 0;
        if (read_bstr(reader, &unit_name) != 0) {
            platform_file_diag_error(diagnostics, "Failed reading HUNK_UNIT name");
            return -1;
        }
        if (platform_data->unit_name == NULL) {
            platform_data->unit_name = unit_name;
            unit_name = NULL;
        }
        free(unit_name);
        while (reader->pos < reader->size) {
            uint32_t hunk_id = 0;
            if (m68k_reader_peek_u32be(reader, &raw) != 0) break;
            hunk_id = raw & HUNK_TYPE_ID_MASK;
            if (hunk_id == HUNK_UNIT) {
                if (m68k_reader_read_u32be(reader, &raw) != 0) {
                    free(pending_name);
                    return -1;
                }
                break;
            }
            if (m68k_reader_read_u32be(reader, &raw) != 0) {
                free(pending_name);
                return -1;
            }
            if (hunk_id == HUNK_NAME) {
                free(pending_name);
                pending_name = NULL;
                if (read_bstr(reader, &pending_name) != 0) {
                    platform_file_diag_error(diagnostics, "Failed reading HUNK_NAME");
                    return -1;
                }
            } else if (hunk_id == HUNK_CODE || hunk_id == HUNK_DATA || hunk_id == HUNK_BSS) {
                const char *section_name = (pending_name != NULL) ? pending_name : "";
                if (add_section_from_hunk(object, raw, section_name, 0U, 0U, reader, 0, diagnostics) != 0) {
                    free(pending_name);
                    return -1;
                }
                free(pending_name);
                pending_name = NULL;
            } else {
                platform_file_diag_errorf(diagnostics, "Unexpected top-level object hunk %u", hunk_id);
                free(pending_name);
                return -1;
            }
        }
        free(pending_name);
    }
    return 0;
}

static int amiga_hunk_read_buffer(const unsigned char *data, size_t size, M68kObject *out_object, M68kDiagSink diagnostics) {
    Reader reader;
    uint32_t magic = 0;

    if (out_object != NULL) out_object->platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
    reader.data = data;
    reader.size = size;
    reader.pos = 0U;
    if (m68k_reader_read_u32be(&reader, &magic) != 0) {
        platform_file_diag_error(diagnostics, "Input file is too small");
        return -1;
    }
    if (magic == HUNK_HEADER) {
        if (parse_hunk_executable(&reader, out_object, diagnostics) != 0) return -1;
    } else if (magic == HUNK_UNIT) {
        if (parse_hunk_object(&reader, out_object, diagnostics) != 0) return -1;
    } else {
        platform_file_diag_errorf(diagnostics, "Unsupported Amiga hunk magic %u", magic);
        return -1;
    }
    return 0;
}

static int amiga_hunk_read_file(const char *path, M68kObject *out_object, M68kDiagSink diagnostics) {
    FILE *fp = NULL;
    int64_t file_size_signed;
    unsigned char *data = NULL;
    size_t file_size;
    int result;

    fp = fopen(path, "rb");
    if (fp == NULL) {
        platform_file_diag_error(diagnostics, "Failed opening input file");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Failed seeking input file");
        return -1;
    }
    file_size_signed = (int64_t)ftell(fp);
    if (file_size_signed < 0) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Failed sizing input file");
        return -1;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Failed rewinding input file");
        return -1;
    }
    file_size = (size_t)file_size_signed;
    data = (unsigned char *)malloc(file_size == 0U ? 1U : file_size);
    if (data == NULL) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Out of memory reading file");
        return -1;
    }
    if (file_size != 0U && fread(data, 1, file_size, fp) != file_size) {
        free(data);
        fclose(fp);
        platform_file_diag_error(diagnostics, "Failed reading input file");
        return -1;
    }
    fclose(fp);
    result = amiga_hunk_read_buffer(data, file_size, out_object, diagnostics);
    free(data);
    return result;
}

/* Writer implementation. */

static int write_symbols_for_section(Writer *writer, const M68kObject *object, size_t section_index) {
    size_t i;
    int wrote = 0;
    for (i = 0; i < object->symbol_count; ++i) {
        const M68kSymbol *symbol = &object->symbols[i];
        if (!symbol->defined || symbol->section_index != section_index || symbol->binding != M68K_SYMBOL_LOCAL) continue;
        if (!wrote) {
            if (m68k_writer_u32be(writer, HUNK_SYMBOL) != 0) return -1;
            wrote = 1;
        }
        if (writer_bstr(writer, symbol->name != NULL ? symbol->name : "") != 0) return -1;
        if (m68k_writer_u32be(writer, symbol->value) != 0) return -1;
    }
    if (wrote && m68k_writer_u32be(writer, 0U) != 0) return -1;
    return 0;
}

static int write_ext_for_section(Writer *writer, const M68kObject *object, size_t section_index) {
    size_t i;
    size_t j;
    int wrote = 0;
    for (i = 0; i < object->symbol_count; ++i) {
        const M68kSymbol *symbol = &object->symbols[i];
        uint32_t ext_type = 0;
        uint32_t ref_count = 0;
        if (symbol->binding == M68K_SYMBOL_GLOBAL && symbol->defined && symbol->section_index == section_index) {
            const char *name = symbol->name != NULL ? symbol->name : "";
            size_t name_longs = (strlen(name) + 3U) / 4U;
            ext_type = AMIGA_HUNK_FILE_EXT_TYPE_EXT_DEF;
            if (!wrote) {
                if (m68k_writer_u32be(writer, HUNK_EXT) != 0) return -1;
                wrote = 1;
            }
            if (m68k_writer_u32be(writer, (ext_type << 24) | (uint32_t)name_longs) != 0)
                return -1;
            if (writer_padded_name(writer, name) != 0) return -1;
            if (m68k_writer_u32be(writer, symbol->value) != 0) return -1;
            continue;
        }
        if (!(symbol->binding == M68K_SYMBOL_EXTERNAL && !symbol->defined)) continue;
        for (j = 0; j < object->fixup_count; ++j) {
            const M68kFixup *fixup = &object->fixups[j];
            if (fixup->section_index == section_index && fixup->has_symbol && fixup->symbol_index == i) {
                ++ref_count;
            }
        }
        if (ref_count == 0U) continue;
        if (!wrote) {
            if (m68k_writer_u32be(writer, HUNK_EXT) != 0) return -1;
            wrote = 1;
        }
        if (ref_count > 0U) {
            const char *name = symbol->name != NULL ? symbol->name : "";
            size_t name_longs = (strlen(name) + 3U) / 4U;
            const M68kFixup *sample = NULL;
            for (j = 0; j < object->fixup_count; ++j) {
                const M68kFixup *fixup = &object->fixups[j];
                if (fixup->section_index == section_index && fixup->has_symbol && fixup->symbol_index == i) {
                    sample = fixup;
                    break;
                }
            }
            if (sample == NULL) return -1;
            if (fixup_to_ext_type(sample, &ext_type) != 0) return -1;
            if (m68k_writer_u32be(writer, (ext_type << 24) | (uint32_t)name_longs) != 0) return -1;
            if (writer_padded_name(writer, name) != 0) return -1;
            if (m68k_writer_u32be(writer, ref_count) != 0) return -1;
            for (j = 0; j < object->fixup_count; ++j) {
                const M68kFixup *fixup = &object->fixups[j];
                if (fixup->section_index == section_index && fixup->has_symbol && fixup->symbol_index == i) {
                    if (m68k_writer_u32be(writer, fixup->offset) != 0) return -1;
                }
            }
        }
    }
    if (wrote && m68k_writer_u32be(writer, 0U) != 0) return -1;
    return 0;
}

static int section_needs_mem_attrs(const M68kSection *section) {
    return section->platform_mem_type == AMIGA_HUNK_FILE_MEM_TYPE_CODE_EXTENDED;
}

static uint32_t section_type_word(const M68kSection *section) {
    return unmap_hunk_kind(section->kind) | ((uint32_t)section->platform_mem_type << HUNK_MEM_SHIFT);
}

static AmigaHunkFileRecordKind canonical_internal_reloc_record_kind_for_fixup(const M68kFixup *fixup) {
    if (!fixup->has_target_section) return AMIGA_HUNK_FILE_META_RECORD_KIND_NONE;
    if (fixup->kind == M68K_FIXUP_ABS && fixup->width == M68K_FIXUP_WIDTH_32) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32;
    if (fixup->kind == M68K_FIXUP_ABS && fixup->width == M68K_FIXUP_WIDTH_16) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_ABSRELOC16;
    if (fixup->kind == M68K_FIXUP_PC_REL && fixup->width == M68K_FIXUP_WIDTH_32) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELRELOC32;
    if (fixup->kind == M68K_FIXUP_PC_REL && fixup->width == M68K_FIXUP_WIDTH_16) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC16;
    if (fixup->kind == M68K_FIXUP_PC_REL && fixup->width == M68K_FIXUP_WIDTH_8) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC8;
    if (fixup->kind == M68K_FIXUP_SECTION_REL && fixup->width == M68K_FIXUP_WIDTH_32) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL32;
    if (fixup->kind == M68K_FIXUP_SECTION_REL && fixup->width == M68K_FIXUP_WIDTH_16) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL16;
    if (fixup->kind == M68K_FIXUP_SECTION_REL && fixup->width == M68K_FIXUP_WIDTH_8) return AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL8;
    return AMIGA_HUNK_FILE_META_RECORD_KIND_NONE;
}

static int fixup_matches_relocation_record_kind(const M68kFixup *fixup, AmigaHunkFileRecordKind record_kind) {
    const AmigaHunkFileRelocationKind *reloc = amiga_hunk_file_relocation_kind_lookup(record_kind);
    if (reloc == NULL) return 0;
    if (map_width_bytes_to_fixup_width(reloc->width_bytes) != fixup->width) return 0;
    return map_relocation_mode_to_fixup_kind(reloc->mode) == fixup->kind;
}

static AmigaHunkFileRecordKind internal_reloc_record_kind_for_fixup(const M68kFixup *fixup) {
    AmigaHunkFileRecordKind platform_kind = (AmigaHunkFileRecordKind)fixup->platform_relocation_record_kind;
    if (fixup->has_target_section && platform_kind != AMIGA_HUNK_FILE_META_RECORD_KIND_NONE
        && fixup_matches_relocation_record_kind(fixup, platform_kind)) {
        return platform_kind;
    }
    return canonical_internal_reloc_record_kind_for_fixup(fixup);
}

static int relocation_record_uses_short_counts(AmigaHunkFileRecordKind record_kind) {
    return record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32SHORT;
}

static int find_next_internal_reloc_for_section(const M68kObject *object, size_t section_index, size_t start,
    size_t *out_index) {
    size_t i;
    for (i = start; i < object->fixup_count; ++i) {
        const M68kFixup *fixup = &object->fixups[i];
        if (fixup->section_index == section_index
            && internal_reloc_record_kind_for_fixup(fixup) != AMIGA_HUNK_FILE_META_RECORD_KIND_NONE) {
            *out_index = i;
            return 1;
        }
    }
    return 0;
}

static int fixup_is_same_relocation_block(const M68kFixup *anchor, const M68kFixup *candidate,
    AmigaHunkFileRecordKind record_kind) {
    if (internal_reloc_record_kind_for_fixup(candidate) != record_kind) return 0;
    if (anchor->platform_relocation_block_index != 0U || candidate->platform_relocation_block_index != 0U) {
        return anchor->platform_relocation_block_index != 0U
            && anchor->platform_relocation_block_index == candidate->platform_relocation_block_index;
    }
    return 1;
}

static int fixup_is_same_relocation_group(const M68kFixup *anchor, const M68kFixup *candidate,
    AmigaHunkFileRecordKind record_kind) {
    if (!fixup_is_same_relocation_block(anchor, candidate, record_kind)) return 0;
    if (anchor->platform_relocation_group_index != 0U || candidate->platform_relocation_group_index != 0U) {
        return anchor->platform_relocation_group_index != 0U
            && anchor->platform_relocation_group_index == candidate->platform_relocation_group_index;
    }
    return anchor->target_section_index == candidate->target_section_index;
}

static int count_internal_reloc_group(const M68kObject *object, size_t section_index, size_t group_start,
    AmigaHunkFileRecordKind record_kind, size_t *out_count, size_t *out_next_index) {
    const M68kFixup *anchor = &object->fixups[group_start];
    size_t cursor = group_start;
    size_t index = 0U;
    size_t count = 0U;
    while (find_next_internal_reloc_for_section(object, section_index, cursor, &index)) {
        const M68kFixup *candidate = &object->fixups[index];
        if (!fixup_is_same_relocation_group(anchor, candidate, record_kind)) {
            *out_count = count;
            *out_next_index = index;
            return 0;
        }
        ++count;
        cursor = index + 1U;
    }
    *out_count = count;
    *out_next_index = object->fixup_count;
    return 0;
}

static int write_internal_reloc_group(Writer *writer, const M68kObject *object, size_t section_index,
    size_t group_start, AmigaHunkFileRecordKind record_kind, size_t count) {
    const M68kFixup *anchor = &object->fixups[group_start];
    int short_counts = relocation_record_uses_short_counts(record_kind);
    size_t cursor = group_start;
    size_t index = 0U;
    size_t written = 0U;
    if (short_counts) {
        if (count > UINT16_MAX || anchor->target_section_index > UINT16_MAX) return -1;
        if (m68k_writer_u16be(writer, (uint16_t)count) != 0
            || m68k_writer_u16be(writer, (uint16_t)anchor->target_section_index) != 0) {
            return -1;
        }
    } else {
        if (count > UINT32_MAX || anchor->target_section_index > UINT32_MAX) return -1;
        if (m68k_writer_u32be(writer, (uint32_t)count) != 0
            || m68k_writer_u32be(writer, (uint32_t)anchor->target_section_index) != 0) {
            return -1;
        }
    }
    while (written < count && find_next_internal_reloc_for_section(object, section_index, cursor, &index)) {
        const M68kFixup *fixup = &object->fixups[index];
        if (!fixup_is_same_relocation_group(anchor, fixup, record_kind)) return -1;
        if (short_counts) {
            if (fixup->offset > UINT16_MAX) return -1;
            if (m68k_writer_u16be(writer, (uint16_t)fixup->offset) != 0) return -1;
        } else {
            if (m68k_writer_u32be(writer, fixup->offset) != 0) return -1;
        }
        ++written;
        cursor = index + 1U;
    }
    return written == count ? 0 : -1;
}

static int write_internal_reloc_terminator(Writer *writer, AmigaHunkFileRecordKind record_kind) {
    if (relocation_record_uses_short_counts(record_kind)) {
        if (m68k_writer_u16be(writer, 0U) != 0) return -1;
        if ((writer->size & 3U) != 0U && m68k_writer_u16be(writer, 0U) != 0) return -1;
        return 0;
    }
    return m68k_writer_u32be(writer, 0U);
}

static int write_empty_internal_reloc_block(Writer *writer, AmigaHunkFileRecordKind record_kind) {
    const AmigaHunkFileRecordInfo *record_info = amiga_hunk_file_record_info_by_record_kind(record_kind);
    if (record_info == NULL || record_info->wire_id == 0U) return -1;
    if (m68k_writer_u32be(writer, record_info->wire_id) != 0) return -1;
    return write_internal_reloc_terminator(writer, record_kind);
}

static int section_has_internal_reloc_kind(const M68kObject *object, size_t section_index,
    AmigaHunkFileRecordKind record_kind) {
    size_t i;
    for (i = 0; i < object->fixup_count; ++i) {
        const M68kFixup *fixup = &object->fixups[i];
        if (fixup->section_index == section_index
            && internal_reloc_record_kind_for_fixup(fixup) == record_kind) {
            return 1;
        }
    }
    return 0;
}

static int write_preserved_internal_relocs_for_section(Writer *writer, const M68kObject *object,
    size_t section_index) {
    size_t cursor = 0U;
    size_t block_start = 0U;
    while (find_next_internal_reloc_for_section(object, section_index, cursor, &block_start)) {
        const M68kFixup *block_anchor = &object->fixups[block_start];
        AmigaHunkFileRecordKind record_kind = internal_reloc_record_kind_for_fixup(block_anchor);
        const AmigaHunkFileRecordInfo *record_info = amiga_hunk_file_record_info_by_record_kind(record_kind);
        uint32_t wire_id = block_anchor->platform_relocation_record_wire_id != 0U
            ? block_anchor->platform_relocation_record_wire_id
            : (record_info != NULL ? record_info->wire_id : 0U);
        size_t group_start = block_start;
        if (wire_id == 0U) return -1;
        if (m68k_writer_u32be(writer, wire_id) != 0) return -1;
        while (group_start < object->fixup_count) {
            size_t count = 0U;
            size_t next_index = object->fixup_count;
            const M68kFixup *group_anchor = &object->fixups[group_start];
            if (!fixup_is_same_relocation_block(block_anchor, group_anchor, record_kind)) break;
            if (count_internal_reloc_group(object, section_index, group_start, record_kind, &count,
                    &next_index) != 0 || count == 0U) {
                return -1;
            }
            if (write_internal_reloc_group(writer, object, section_index, group_start, record_kind, count) != 0)
                return -1;
            group_start = next_index;
        }
        if (write_internal_reloc_terminator(writer, record_kind) != 0) return -1;
        cursor = group_start;
    }
    return 0;
}

static int write_empty_internal_relocs_for_section(Writer *writer, const M68kObject *object, size_t section_index) {
    static const AmigaHunkFileRecordKind RECORD_KINDS[] = {
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC16,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC8,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL32,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL16,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL8,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELRELOC32,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_ABSRELOC16,
        AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32SHORT,
    };
    const AmigaHunkPlatformData *platform_data = (const AmigaHunkPlatformData *)object->platform_data;
    size_t i;
    for (i = 0; i < sizeof(RECORD_KINDS) / sizeof(RECORD_KINDS[0]); ++i) {
        int preserve_empty = 0;
        if (platform_data != NULL && platform_data->section_empty_reloc_masks != NULL && section_index < object->section_count) {
            preserve_empty = (platform_data->section_empty_reloc_masks[section_index] & empty_reloc_mask_bit(RECORD_KINDS[i])) != 0U;
        }
        if (!preserve_empty || section_has_internal_reloc_kind(object, section_index, RECORD_KINDS[i])) continue;
        if (write_empty_internal_reloc_block(writer, RECORD_KINDS[i]) != 0)
            return -1;
    }
    return 0;
}

static int write_internal_relocs_for_section(Writer *writer, const M68kObject *object, size_t section_index) {
    if (write_preserved_internal_relocs_for_section(writer, object, section_index) != 0) return -1;
    return write_empty_internal_relocs_for_section(writer, object, section_index);
}

static int write_section_payload(Writer *writer, const M68kSection *section) {
    if (section->kind == M68K_SECTION_BSS) return m68k_writer_u32be(writer, section->size / 4U);
    if (m68k_writer_u32be(writer, section->data_size / 4U) != 0) return -1;
    return m68k_writer_bytes(writer, section->data, section->data_size);
}

static int write_debug_for_section(Writer *writer, const M68kSection *section) {
    if (section->debug_size == 0U) return 0;
    if (m68k_writer_u32be(writer, HUNK_DEBUG) != 0) return -1;
    if (m68k_writer_u32be(writer, section->debug_size / 4U) != 0) return -1;
    return m68k_writer_bytes(writer, section->debug_data, section->debug_size);
}

static int write_section_metadata(Writer *writer, const M68kObject *object, size_t section_index) {
    if (write_internal_relocs_for_section(writer, object, section_index) != 0) return -1;
    if (write_ext_for_section(writer, object, section_index) != 0) return -1;
    if (write_symbols_for_section(writer, object, section_index) != 0) return -1;
    if (write_debug_for_section(writer, &object->sections[section_index]) != 0) return -1;
    return m68k_writer_u32be(writer, HUNK_END);
}

static int write_section_record(Writer *writer, const M68kObject *object, size_t section_index, int include_name) {
    const M68kSection *section = &object->sections[section_index];
    if (include_name) {
        if (m68k_writer_u32be(writer, HUNK_NAME) != 0
            || writer_bstr(writer, section->name != NULL ? section->name : "") != 0) {
            return -1;
        }
    }
    if (m68k_writer_u32be(writer, section_type_word(section)) != 0) return -1;
    if (section_needs_mem_attrs(section) && m68k_writer_u32be(writer, section->platform_mem_attrs) != 0) return -1;
    if (write_section_payload(writer, section) != 0) return -1;
    return write_section_metadata(writer, object, section_index);
}

static int fixup_is_writable_internal_reloc(const M68kFixup *fixup) {
    return internal_reloc_record_kind_for_fixup(fixup) != AMIGA_HUNK_FILE_META_RECORD_KIND_NONE;
}

static int fixup_is_writable_ext_reference(const M68kFixup *fixup) {
    uint32_t ext_type = 0;
    return fixup->has_symbol && fixup_to_ext_type(fixup, &ext_type) == 0;
}

static int validate_writable_object(const M68kObject *object, M68kDiagSink diagnostics) {
    size_t i;
    for (i = 0; i < object->section_count; ++i) {
        const M68kSection *section = &object->sections[i];
        if ((section->size & 3U) != 0U || (section->data_size & 3U) != 0U) {
            char message[160];
            snprintf(message, sizeof(message),
                "Current Amiga hunk writer requires longword-aligned section sizes; section %u size=%u data_size=%u",
                (unsigned)i, (unsigned)section->size, (unsigned)section->data_size);
            platform_file_diag_error(diagnostics, message);
            return -1;
        }
        if ((section->debug_size & 3U) != 0U) {
            platform_file_diag_error(diagnostics, "Current Amiga hunk writer requires longword-aligned HUNK_DEBUG payloads");
            return -1;
        }
        if (section->debug_size != 0U && section->debug_data == NULL) {
            platform_file_diag_error(diagnostics, "Current Amiga hunk writer requires HUNK_DEBUG payload bytes");
            return -1;
        }
    }
    for (i = 0; i < object->fixup_count; ++i) {
        const M68kFixup *fixup = &object->fixups[i];
        if (fixup->has_target_section && !fixup_is_writable_internal_reloc(fixup)) {
            platform_file_diag_error(diagnostics, "Current Amiga hunk writer cannot encode this internal relocation fixup");
            return -1;
        }
        if (fixup->has_symbol && !fixup_is_writable_ext_reference(fixup)) {
            platform_file_diag_error(diagnostics, "Current Amiga hunk writer cannot encode this EXT reference fixup");
            return -1;
        }
        if (fixup->has_target_section || fixup->has_symbol) continue;
        platform_file_diag_error(diagnostics, "Current Amiga hunk writer requires fixups to target a section or symbol");
        return -1;
    }
    return 0;
}

static int amiga_hunk_write_buffer(const M68kObject *object, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics) {
    Writer writer;
    unsigned char *writer_data = NULL;
    size_t i;

    if (out_data == NULL || out_size == NULL) {
        platform_file_diag_error(diagnostics, "Bad Amiga hunk writer arguments");
        return -1;
    }
    *out_data = NULL;
    *out_size = 0U;
    if (object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE
        && object->platform_file_kind != M68K_PLATFORM_FILE_OBJECT) {
        platform_file_diag_error(diagnostics, "Unsupported Amiga hunk object kind");
        return -1;
    }
    if (validate_writable_object(object, diagnostics) != 0) return -1;
    if (m68k_writer_create(&writer) != 0) {
        platform_file_diag_error(diagnostics, "Out of memory writing Amiga hunk file");
        return -1;
    }

    if (object->platform_file_kind == M68K_PLATFORM_FILE_EXECUTABLE) {
        const AmigaHunkPlatformData *platform_data = (const AmigaHunkPlatformData *)object->platform_data;
        uint32_t header_count = (uint32_t)object->section_count;
        uint32_t header_first_hunk = 0U;
        uint32_t header_last_hunk = (uint32_t)(object->section_count == 0U ? 0U : object->section_count - 1U);
        uint32_t header_write_count = (platform_data != NULL && platform_data->header_count == object->section_count)
            ? platform_data->header_count
            : header_count;
        uint32_t header_write_first = (platform_data != NULL && platform_data->header_count == object->section_count)
            ? platform_data->header_first_hunk
            : header_first_hunk;
        uint32_t header_write_last = (platform_data != NULL && platform_data->header_count == object->section_count)
            ? platform_data->header_last_hunk
            : header_last_hunk;
        if (m68k_writer_u32be(&writer, HUNK_HEADER) != 0
            || m68k_writer_u32be(&writer, 0U) != 0
            || m68k_writer_u32be(&writer, header_write_count) != 0
            || m68k_writer_u32be(&writer, header_write_first) != 0
            || m68k_writer_u32be(&writer, header_write_last) != 0) {
            goto oom;
        }
        for (i = 0; i < object->section_count; ++i) {
            uint32_t size_longs = object->sections[i].size / 4U;
            uint32_t raw_size = size_longs | ((uint32_t)object->sections[i].platform_mem_type << HUNK_MEM_SHIFT);
            if (platform_data != NULL && platform_data->header_count == object->section_count
                && platform_data->header_size_words != NULL) {
                raw_size = platform_data->header_size_words[i];
            }
            if (m68k_writer_u32be(&writer, raw_size) != 0) {
                goto oom;
            }
            if (object->sections[i].platform_mem_type == 3U) {
                uint32_t mem_attrs = object->sections[i].platform_mem_attrs;
                if (platform_data != NULL && platform_data->header_count == object->section_count
                    && platform_data->header_mem_attrs != NULL) {
                    mem_attrs = platform_data->header_mem_attrs[i];
                }
                if (m68k_writer_u32be(&writer, mem_attrs) != 0) {
                    goto oom;
                }
            }
        }
        for (i = 0; i < object->section_count; ++i) {
            if (write_section_record(&writer, object, i, 0) != 0) {
                goto oom;
            }
        }
    } else {
        const AmigaHunkPlatformData *platform_data = (const AmigaHunkPlatformData *)object->platform_data;
        const char *unit_name = (platform_data != NULL && platform_data->unit_name != NULL) ? platform_data->unit_name : "";
        if (m68k_writer_u32be(&writer, HUNK_UNIT) != 0 || writer_bstr(&writer, unit_name) != 0) {
            goto oom;
        }
        for (i = 0; i < object->section_count; ++i) {
            if (write_section_record(&writer, object, i, 1) != 0) {
                goto oom;
            }
        }
    }

    writer_data = m68k_writer_build(&writer);
    if (writer.size != 0U && writer_data == NULL) {
        m68k_writer_destroy(&writer);
        platform_file_diag_error(diagnostics, "Out of memory writing Amiga hunk file");
        return -1;
    }
    *out_data = writer_data;
    *out_size = writer.size;
    m68k_writer_destroy(&writer);
    return 0;

oom:
    m68k_writer_destroy(&writer);
    platform_file_diag_error(diagnostics, "Out of memory writing Amiga hunk file");
    return -1;
}

static int amiga_hunk_write_file(const char *path, const M68kObject *object, M68kDiagSink diagnostics) {
    FILE *fp = NULL;
    unsigned char *writer_data = NULL;
    size_t writer_size = 0U;
    if (amiga_hunk_write_buffer(object, &writer_data, &writer_size, diagnostics) != 0) return -1;
    fp = fopen(path, "wb");
    if (fp == NULL) {
        free(writer_data);
        platform_file_diag_error(diagnostics, "Failed opening output file");
        return -1;
    }
    if (writer_size != 0U && fwrite(writer_data, 1, writer_size, fp) != writer_size) {
        fclose(fp);
        free(writer_data);
        platform_file_diag_error(diagnostics, "Failed writing output file");
        return -1;
    }
    fclose(fp);
    free(writer_data);
    return 0;
}

