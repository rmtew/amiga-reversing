#include "m68k_backend.h"
#include "platform_atari_st.h"
#include "platform_binary_io.h"
#include "platform_common.h"
#include "generated/atari_st_prg_file_runtime.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef M68kBinaryReader Reader;

static void platform_file_diag_error(M68kDiagSink diagnostics, const char *message) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, message);
}

typedef struct AtariStPrgPlatformData {
    uint32_t symbol_table_type;
    uint32_t program_flags;
    uint16_t relocation_flag;
    uint8_t *symbol_table_data;
    uint32_t symbol_table_size;
} AtariStPrgPlatformData;

typedef M68kBinaryWriter Writer;
static int atari_relocation_flag_is_informational(void) {
    return ATARI_ST_PRG_FILE_CONSTRAINTS_RELOCATION_FLAG_IS_INFORMATIONAL_FOR_CLASSIC_PRG != 0u;
}

static int atari_allow_eof_terminated_relocation_stream(void) {
    return ATARI_ST_PRG_FILE_CONSTRAINTS_RELOCATION_STREAM_MAY_TERMINATE_AT_EOF_WITHOUT_ZERO_BYTE != 0u;
}

static int atari_allow_zero_only_padding_after_empty_relocations(void) {
    return ATARI_ST_PRG_FILE_CONSTRAINTS_ZERO_ONLY_TRAILING_PADDING_AFTER_EMPTY_RELOCATION_STREAM_IS_ALLOWED != 0u;
}

static const AtariStPrgFileRecordInfo *find_record_info(AtariStPrgFileRecordKind record_kind) {
    size_t i;
    for (i = 0; i < ATARI_ST_PRG_FILE_RECORD_INFO_COUNT; ++i) {
        if (ATARI_ST_PRG_FILE_RECORD_INFOS[i].record_kind == record_kind) return &ATARI_ST_PRG_FILE_RECORD_INFOS[i];
    }
    return NULL;
}

static const AtariStPrgFileRelocationKind *find_relocation_kind(AtariStPrgFileRecordKind record_kind) {
    size_t i;
    for (i = 0; i < ATARI_ST_PRG_FILE_RELOCATION_KIND_COUNT; ++i) {
        if (ATARI_ST_PRG_FILE_RELOCATION_KINDS[i].record_kind == record_kind) return &ATARI_ST_PRG_FILE_RELOCATION_KINDS[i];
    }
    return NULL;
}

static M68kSectionKind map_section_kind(AtariStPrgFileSectionKind section_kind) {
    switch (section_kind) {
    case ATARI_ST_PRG_FILE_META_SECTION_KIND_CODE:
        return M68K_SECTION_CODE;
    case ATARI_ST_PRG_FILE_META_SECTION_KIND_DATA:
        return M68K_SECTION_DATA;
    default:
        return M68K_SECTION_BSS;
    }
}

static M68kObjectAddResult add_named_section(M68kObject *object, const char *name,
    AtariStPrgFileRecordKind record_kind, uint32_t size, const unsigned char *data, uint32_t data_size) {
    M68kObjectAddResult result = {0};
    M68kSection section;
    const AtariStPrgFileRecordInfo *info = find_record_info(record_kind);
    if (info == NULL) return result;
    memset(&section, 0, sizeof(section));
    section.name = (char *)name;
    section.kind = map_section_kind(info->section_kind);
    section.size = size;
    section.data = (uint8_t *)data;
    section.data_size = data_size;
    return m68k_object_add_section(object, &section);
}

static int add_reloc_fixup(M68kObject *object, uint32_t image_offset, uint32_t text_size, uint32_t data_size,
    const AtariStPrgFileRelocationKind *reloc_kind, size_t text_index, size_t data_index) {
    M68kFixup fixup;
    uint32_t target_image_offset = 0;
    const M68kSection *target_section = NULL;
    memset(&fixup, 0, sizeof(fixup));
    if (image_offset >= text_size + data_size) return -1;
    if (image_offset < text_size) {
        fixup.section_index = text_index;
        fixup.offset = image_offset;
    } else {
        fixup.section_index = data_index;
        fixup.offset = image_offset - text_size;
    }
    fixup.kind = M68K_FIXUP_ABS;
    if (reloc_kind->mode != ATARI_ST_PRG_FILE_META_RELOCATION_MODE_LOAD_BASE_RELATIVE) return -1;
    switch (reloc_kind->width_bytes) {
    case 1:
        fixup.width = M68K_FIXUP_WIDTH_8;
        break;
    case 2:
        fixup.width = M68K_FIXUP_WIDTH_16;
        break;
    case 4:
        fixup.width = M68K_FIXUP_WIDTH_32;
        break;
    default:
        return -1;
    }
    if (fixup.width == M68K_FIXUP_WIDTH_32) {
        if (fixup.section_index == text_index) target_section = &object->sections[text_index];
        else target_section = &object->sections[data_index];
        if (fixup.offset + 4U > target_section->data_size) return -1;
        target_image_offset = ((uint32_t)target_section->data[fixup.offset] << 24)
            | ((uint32_t)target_section->data[fixup.offset + 1U] << 16)
            | ((uint32_t)target_section->data[fixup.offset + 2U] << 8)
            | (uint32_t)target_section->data[fixup.offset + 3U];
        if (target_image_offset < text_size) {
            fixup.has_target_section = 1;
            fixup.target_section_index = text_index;
            fixup.addend = (int32_t)target_image_offset;
        } else if (target_image_offset < text_size + data_size) {
            fixup.has_target_section = 1;
            fixup.target_section_index = data_index;
            fixup.addend = (int32_t)(target_image_offset - text_size);
        }
    }
    return m68k_object_add_fixup(object, &fixup).ok ? 0 : -1;
}

static int parse_relocation_stream(Reader *reader, M68kObject *out_object, uint32_t text_size, uint32_t data_size,
    size_t text_index, size_t data_index, M68kDiagSink diagnostics) {
    uint32_t offset = 0;
    unsigned char delta = 0;
    const AtariStPrgFileRelocationKind *reloc_kind =
        find_relocation_kind(ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM);
    if (reloc_kind == NULL) {
        platform_file_diag_error(diagnostics, "Missing Atari relocation metadata");
        return -1;
    }
    if (m68k_reader_read_u32be(reader, &offset) != 0) {
        platform_file_diag_error(diagnostics, "Truncated Atari relocation stream");
        return -1;
    }
    if (offset == 0U) {
        if (m68k_reader_remaining_is_all_zero(reader)) return atari_allow_zero_only_padding_after_empty_relocations() ? 0 : -1;
        return 0;
    }
    if (add_reloc_fixup(out_object, offset, text_size, data_size, reloc_kind, text_index, data_index) != 0) {
        platform_file_diag_error(diagnostics, "Invalid Atari relocation offset");
        return -1;
    }
    for (;;) {
        if (m68k_reader_read_u8(reader, &delta) != 0) {
            if (atari_allow_eof_terminated_relocation_stream()) return 0;
            platform_file_diag_error(diagnostics, "Truncated Atari relocation stream");
            return -1;
        }
        if (delta == 0U) return 0;
        if (delta == 1U) {
            offset += 254U;
            continue;
        }
        offset += (uint32_t)delta;
        if (add_reloc_fixup(out_object, offset, text_size, data_size, reloc_kind, text_index, data_index) != 0) {
            platform_file_diag_error(diagnostics, "Invalid Atari relocation offset");
            return -1;
        }
    }
}

static AtariStPrgPlatformData *ensure_platform_data(M68kObject *object) {
    AtariStPrgPlatformData *platform_data;
    if (object == NULL) return NULL;
    platform_data = (AtariStPrgPlatformData *)object->platform_data;
    if (platform_data != NULL) return platform_data;
    platform_data = (AtariStPrgPlatformData *)m68k_object_alloc(object, sizeof(*platform_data));
    if (platform_data == NULL) return NULL;
    memset(platform_data, 0, sizeof(*platform_data));
    object->platform_data = platform_data;
    return platform_data;
}

static const M68kSection *find_first_section(const M68kObject *object, M68kSectionKind kind, size_t *out_index) {
    size_t i;
    for (i = 0; i < object->section_count; ++i) {
        if (object->sections[i].kind == kind) {
            if (out_index != NULL) {
                *out_index = i;
            }
            return &object->sections[i];
        }
    }
    return NULL;
}

static size_t count_sections(const M68kObject *object, M68kSectionKind kind) {
    size_t i;
    size_t count = 0;
    for (i = 0; i < object->section_count; ++i) {
        if (object->sections[i].kind == kind) ++count;
    }
    return count;
}

static int validate_writable_fixup(const M68kFixup *fixup, size_t text_index, uint32_t text_size, size_t data_index,
    uint32_t data_size, uint32_t *out_image_offset) {
    if (fixup->has_symbol) return -1;
    if (fixup->kind != M68K_FIXUP_ABS || fixup->width != M68K_FIXUP_WIDTH_32) return -1;
    if (fixup->section_index == text_index) {
        if (fixup->offset + 4U > text_size) return -1;
        *out_image_offset = fixup->offset;
        return 0;
    }
    if (fixup->section_index == data_index) {
        if (fixup->offset + 4U > data_size) return -1;
        *out_image_offset = text_size + fixup->offset;
        return 0;
    }
    return -1;
}

static int atari_fixup_is_ignorable_local_encoding(const M68kFixup *fixup) {
    if (fixup == NULL) return 0;
    if (fixup->has_symbol) return 0;
    if (!fixup->has_target_section) return 0;
    if (fixup->kind == M68K_FIXUP_ABS && fixup->width == M68K_FIXUP_WIDTH_32) return 0;
    return 1;
}

static int compare_u32(const void *lhs, const void *rhs) {
    uint32_t left = *(const uint32_t *)lhs;
    uint32_t right = *(const uint32_t *)rhs;
    if (left < right) return -1;
    if (left > right) return 1;
    return 0;
}

static int write_relocation_stream(Writer *writer, const M68kObject *object, size_t text_index, uint32_t text_size,
    size_t data_index, uint32_t data_size, M68kDiagSink diagnostics) {
    uint32_t *offsets = NULL;
    size_t offset_count = 0;
    size_t i;
    uint32_t previous = 0;
    for (i = 0; i < object->fixup_count; ++i) {
        uint32_t image_offset = 0;
        const M68kFixup *fixup = &object->fixups[i];
        if (fixup->section_index != text_index && fixup->section_index != data_index) continue;
        if (validate_writable_fixup(fixup, text_index, text_size, data_index, data_size, &image_offset) != 0) {
            if (atari_fixup_is_ignorable_local_encoding(fixup)) continue;
            free(offsets);
            m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
                "Atari ST writer supports only TEXT/DATA absolute 32-bit fixups (section=%" PRIuPTR
                " offset=%" PRIu32 " kind=%u width=%u has_target=%d has_symbol=%d)",
                fixup->section_index, fixup->offset, (unsigned int)fixup->kind, (unsigned int)fixup->width,
                fixup->has_target_section, fixup->has_symbol);
            return -1;
        }
        offsets = (uint32_t *)realloc(offsets, (offset_count + 1U) * sizeof(*offsets));
        if (offsets == NULL) {
            platform_file_diag_error(diagnostics, "Out of memory");
            return -1;
        }
        offsets[offset_count++] = image_offset;
    }
    if (offset_count == 0U) {
        free(offsets);
        return 0;
    }
    qsort(offsets, offset_count, sizeof(*offsets), compare_u32);
    if (m68k_writer_u32be(writer, offsets[0]) != 0) {
        free(offsets);
        return -1;
    }
    previous = offsets[0];
    for (i = 1; i < offset_count; ++i) {
        uint32_t delta = offsets[i] - previous;
        while (delta > 254U) {
            if (m68k_writer_u8(writer, 1U) != 0) {
                free(offsets);
                return -1;
            }
            delta -= 254U;
        }
        if (delta == 0U) {
            free(offsets);
            platform_file_diag_error(diagnostics, "Atari ST writer does not support duplicate relocation offsets");
            return -1;
        }
        if (m68k_writer_u8(writer, (unsigned char)delta) != 0) {
            free(offsets);
            return -1;
        }
        previous = offsets[i];
    }
    free(offsets);
    return m68k_writer_u8(writer, 0U);
}

static int atari_st_read_buffer(const unsigned char *data, size_t size, M68kObject *out_object, M68kDiagSink diagnostics) {
    Reader reader;
    uint16_t magic = 0, relocation_flag = 0;
    uint32_t text_size = 0, data_size = 0, bss_size = 0;
    uint32_t symbol_table_size = 0, symbol_table_type = 0, program_flags = 0;
    size_t text_index = 0;
    size_t data_index = 0;
    M68kSection section;
    M68kObjectAddResult section_result;
    AtariStPrgPlatformData *platform_data = NULL;

    if (out_object != NULL) out_object->platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
    reader.data = data;
    reader.size = size;
    reader.pos = 0U;

    if (m68k_reader_read_u16be(&reader, &magic) != 0 || magic != ATARI_ST_PRG_FILE_MAGIC_PRG) {
        platform_file_diag_error(diagnostics, "Invalid Atari ST PRG header");
        return -1;
    }
    if (m68k_reader_read_u32be(&reader, &text_size) != 0
        || m68k_reader_read_u32be(&reader, &data_size) != 0
        || m68k_reader_read_u32be(&reader, &bss_size) != 0
        || m68k_reader_read_u32be(&reader, &symbol_table_size) != 0
        || m68k_reader_read_u32be(&reader, &symbol_table_type) != 0
        || m68k_reader_read_u32be(&reader, &program_flags) != 0
        || m68k_reader_read_u16be(&reader, &relocation_flag) != 0) {
        platform_file_diag_error(diagnostics, "Truncated Atari ST PRG header");
        return -1;
    }
    platform_data = (AtariStPrgPlatformData *)m68k_object_alloc(out_object, sizeof(*platform_data));
    if (platform_data == NULL) {
        platform_file_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    memset(platform_data, 0, sizeof(*platform_data));
    platform_data->symbol_table_type = symbol_table_type;
    platform_data->program_flags = program_flags;
    platform_data->relocation_flag = relocation_flag;
    out_object->platform_data = platform_data;
    if (reader.pos + text_size + data_size + symbol_table_size > reader.size) {
        platform_file_diag_error(diagnostics, "Truncated Atari ST PRG sections");
        return -1;
    }

    out_object->platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
    section_result = add_named_section(out_object, "TEXT", ATARI_ST_PRG_FILE_META_RECORD_KIND_TEXT, text_size,
            data + reader.pos, text_size);
    if (!section_result.ok) {
        platform_file_diag_error(diagnostics, "Could not add TEXT section");
        return -1;
    }
    text_index = section_result.index;
    reader.pos += text_size;
    section_result = add_named_section(out_object, "DATA", ATARI_ST_PRG_FILE_META_RECORD_KIND_DATA, data_size,
            data + reader.pos, data_size);
    if (!section_result.ok) {
        platform_file_diag_error(diagnostics, "Could not add DATA section");
        return -1;
    }
    data_index = section_result.index;
    reader.pos += data_size;

    if (bss_size != 0U) {
        memset(&section, 0, sizeof(section));
        section.name = "BSS";
        section.kind = M68K_SECTION_BSS;
        section.size = bss_size;
        if (!m68k_object_add_section(out_object, &section).ok) {
            platform_file_diag_error(diagnostics, "Could not add BSS section");
            return -1;
        }
    }

    if (symbol_table_size != 0U) {
        platform_data->symbol_table_data = (uint8_t *)m68k_object_alloc(out_object, symbol_table_size);
        if (platform_data->symbol_table_data == NULL) {
            platform_file_diag_error(diagnostics, "Out of memory");
            return -1;
        }
        platform_data->symbol_table_size = symbol_table_size;
        if (m68k_reader_read_bytes(&reader, platform_data->symbol_table_data, symbol_table_size) != 0) {
            platform_file_diag_error(diagnostics, "Truncated Atari ST symbol table");
            return -1;
        }
    }
    if (reader.pos < reader.size || (!atari_relocation_flag_is_informational() && relocation_flag == 0u)) {
        if (parse_relocation_stream(&reader, out_object, text_size, data_size, text_index, data_index,
                diagnostics) != 0) return -1;
    }
    if (reader.pos != reader.size && !m68k_reader_remaining_is_all_zero(&reader)) {
        platform_file_diag_error(diagnostics, "Unexpected trailing Atari ST data");
        return -1;
    }

    return 0;
}

static int atari_st_read_file(const char *path, M68kObject *out_object, M68kDiagSink diagnostics) {
    FILE *fp = NULL;
    int64_t file_size_signed;
    size_t file_size;
    unsigned char *buffer = NULL;
    int result;

    fp = fopen(path, "rb");
    if (fp == NULL) {
        platform_file_diag_error(diagnostics, "Could not open Atari ST file");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Could not size Atari ST file");
        return -1;
    }
    file_size_signed = (int64_t)ftell(fp);
    if (file_size_signed < 0) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Could not size Atari ST file");
        return -1;
    }
    file_size = (size_t)file_size_signed;
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Could not rewind Atari ST file");
        return -1;
    }
    buffer = (unsigned char *)malloc(file_size == 0U ? 1U : file_size);
    if (buffer == NULL) {
        fclose(fp);
        platform_file_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    if (file_size != 0U && fread(buffer, 1, file_size, fp) != file_size) {
        free(buffer);
        fclose(fp);
        platform_file_diag_error(diagnostics, "Could not read Atari ST file");
        return -1;
    }
    fclose(fp);
    result = atari_st_read_buffer(buffer, file_size, out_object, diagnostics);
    free(buffer);
    return result;
}

int m68k_atari_st_set_program_flags(M68kObject *object, uint32_t program_flags) {
    AtariStPrgPlatformData *platform_data = ensure_platform_data(object);
    if (platform_data == NULL) return -1;
    platform_data->program_flags = program_flags;
    return 0;
}

int m68k_atari_st_read_program_flags(const char *path, uint32_t *out_program_flags) {
    FILE *fp;
    uint8_t header[28];
    if (path == NULL || out_program_flags == NULL) return -1;
    fp = fopen(path, "rb");
    if (fp == NULL) return -1;
    if (fread(header, 1, sizeof(header), fp) != sizeof(header)) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    if (m68k_read_u16be(header) != ATARI_ST_PRG_FILE_MAGIC_PRG) return -1;
    *out_program_flags = m68k_read_u32be(header + 22U);
    return 0;
}

int m68k_atari_st_get_program_flags(const M68kObject *object, uint32_t *out_program_flags) {
    const AtariStPrgPlatformData *platform_data;
    if (object == NULL || out_program_flags == NULL || object->platform_data == NULL) return -1;
    platform_data = (const AtariStPrgPlatformData *)object->platform_data;
    *out_program_flags = platform_data->program_flags;
    return 0;
}

static int atari_st_write_file(const char *path, const M68kObject *object, M68kDiagSink diagnostics) {
    const AtariStPrgPlatformData *platform_data = (const AtariStPrgPlatformData *)object->platform_data;
    const M68kSection *text_section;
    const M68kSection *data_section;
    const M68kSection *bss_section;
    size_t text_index = 0;
    size_t data_index = 0;
    size_t bss_index = 0;
    Writer writer;
    FILE *fp = NULL;
    unsigned char *writer_data = NULL;
    uint32_t symbol_table_type = 0;
    uint32_t program_flags = 0;
    uint16_t relocation_flag = 0;
    if (object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) {
        platform_file_diag_error(diagnostics, "Atari ST writer requires executable object");
        return -1;
    }
    text_section = find_first_section(object, M68K_SECTION_CODE, &text_index);
    data_section = find_first_section(object, M68K_SECTION_DATA, &data_index);
    bss_section = find_first_section(object, M68K_SECTION_BSS, &bss_index);
    if (text_section == NULL || data_section == NULL) {
        platform_file_diag_error(diagnostics, "Atari ST writer requires one TEXT and one DATA section");
        return -1;
    }
    if (count_sections(object, M68K_SECTION_CODE) != 1U || count_sections(object, M68K_SECTION_DATA) != 1U) {
        platform_file_diag_error(diagnostics, "Atari ST writer requires a single TEXT and single DATA section");
        return -1;
    }
    if (m68k_writer_create(&writer) != 0) {
        platform_file_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    if (text_section->size != text_section->data_size || data_section->size != data_section->data_size) {
        platform_file_diag_error(diagnostics, "Atari ST writer requires TEXT/DATA sections without extra allocation");
        return -1;
    }
    if (platform_data != NULL) {
        symbol_table_type = platform_data->symbol_table_type;
        program_flags = platform_data->program_flags;
        relocation_flag = platform_data->relocation_flag;
    }
    if (m68k_writer_u16be(&writer, ATARI_ST_PRG_FILE_MAGIC_PRG) != 0
        || m68k_writer_u32be(&writer, text_section->data_size) != 0
        || m68k_writer_u32be(&writer, data_section->data_size) != 0
        || m68k_writer_u32be(&writer, (bss_section != NULL) ? bss_section->size : 0U) != 0
        || m68k_writer_u32be(&writer, (platform_data != NULL) ? platform_data->symbol_table_size : 0U) != 0
        || m68k_writer_u32be(&writer, symbol_table_type) != 0
        || m68k_writer_u32be(&writer, program_flags) != 0
        || m68k_writer_u16be(&writer, relocation_flag) != 0
        || m68k_writer_bytes(&writer, text_section->data, text_section->data_size) != 0
        || m68k_writer_bytes(&writer, data_section->data, data_section->data_size) != 0
        || ((platform_data != NULL) && platform_data->symbol_table_size != 0U
            && m68k_writer_bytes(&writer, platform_data->symbol_table_data, platform_data->symbol_table_size) != 0)) {
        m68k_writer_destroy(&writer);
        platform_file_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    if (write_relocation_stream(&writer, object, text_index, text_section->data_size, data_index, data_section->data_size,
            diagnostics) != 0) {
        m68k_writer_destroy(&writer);
        return -1;
    }
    fp = fopen(path, "wb");
    if (fp == NULL) {
        m68k_writer_destroy(&writer);
        platform_file_diag_error(diagnostics, "Could not open Atari ST output file");
        return -1;
    }
    writer_data = m68k_writer_build(&writer);
    if (writer.size != 0U && writer_data == NULL) {
        fclose(fp);
        m68k_writer_destroy(&writer);
        platform_file_diag_error(diagnostics, "Out of memory");
        return -1;
    }
    if (fwrite(writer_data, 1, writer.size, fp) != writer.size) {
        fclose(fp);
        free(writer_data);
        m68k_writer_destroy(&writer);
        platform_file_diag_error(diagnostics, "Could not write Atari ST output file");
        return -1;
    }
    fclose(fp);
    free(writer_data);
    m68k_writer_destroy(&writer);
    (void)bss_index;
    return 0;
}

const M68kBackend M68K_BACKEND_ATARI_ST = {
    "atari-st",
    atari_st_read_file,
    atari_st_read_buffer,
    atari_st_write_file,
};

const M68kBackend *m68k_backend_by_name(const char *name) {
    if (name == NULL) return NULL;
    if (strcmp(name, M68K_BACKEND_AMIGA_HUNK.name) == 0) return &M68K_BACKEND_AMIGA_HUNK;
    if (strcmp(name, M68K_BACKEND_ATARI_ST.name) == 0) return &M68K_BACKEND_ATARI_ST;
    return NULL;
}
