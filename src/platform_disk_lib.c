#include "json_builder.h"
#include "platform_amiga_disk.h"
#include "platform_atari_st_disk.h"
#include "platform_common.h"
#include "platform_disk_lib.h"
#include "platform_file_lib.h"
#include "util_arena.h"
#include "generated/amiga_disk_file_runtime.h"
#include "generated/amiga_os_runtime.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <bcrypt.h>

#pragma comment(lib, "bcrypt.lib")

#define AMIGA_DISK_CONTENT_CLASSIFY_MAX_BYTES (1024U * 1024U)
#define PLATFORM_DISK_WORKFLOW_ARENA_SIZE 16384U

typedef enum PlatformDiskKind {
    PLATFORM_DISK_KIND_UNKNOWN = 0,
    PLATFORM_DISK_KIND_AMIGA,
    PLATFORM_DISK_KIND_ATARI_ST
} PlatformDiskKind;

typedef struct PlatformDiskName {
    const char *name;
    PlatformDiskKind kind;
} PlatformDiskName;

static const PlatformDiskName PLATFORM_DISK_NAMES[] = {
    {"amiga-disk", PLATFORM_DISK_KIND_AMIGA},
    {"amiga", PLATFORM_DISK_KIND_AMIGA},
    {"atari-st-disk", PLATFORM_DISK_KIND_ATARI_ST},
    {"atari-st", PLATFORM_DISK_KIND_ATARI_ST},
};

static PlatformDiskKind platform_disk_kind_from_name(const char *platform_name) {
    size_t index;
    if (platform_name == NULL || platform_name[0] == '\0') return PLATFORM_DISK_KIND_UNKNOWN;
    for (index = 0U; index < sizeof(PLATFORM_DISK_NAMES) / sizeof(PLATFORM_DISK_NAMES[0]); ++index) {
        if (_stricmp(platform_name, PLATFORM_DISK_NAMES[index].name) == 0) return PLATFORM_DISK_NAMES[index].kind;
    }
    return PLATFORM_DISK_KIND_UNKNOWN;
}

static int is_leap_year(uint32_t year) {
    return (year % 4U == 0U && year % 100U != 0U) || (year % 400U == 0U);
}

static uint32_t days_in_month(uint32_t year, uint32_t month) {
    static const uint8_t days[] = {31U, 28U, 31U, 30U, 31U, 30U, 31U, 31U, 30U, 31U, 30U, 31U};
    if (month == 2U && is_leap_year(year)) return 29U;
    return days[month - 1U];
}

static void amiga_date_to_iso(uint32_t days, uint32_t mins, uint32_t ticks, char out[20]) {
    uint32_t year = 1978U;
    uint32_t month = 1U;
    while (1) {
        uint32_t year_days = is_leap_year(year) ? 366U : 365U;
        if (days < year_days) break;
        days -= year_days;
        ++year;
    }
    while (1) {
        uint32_t month_days = days_in_month(year, month);
        if (days < month_days) break;
        days -= month_days;
        ++month;
    }
    snprintf(out, 20U, "%04u-%02u-%02u %02u:%02u:%02u", year, month, days + 1U, mins / 60U, mins % 60U,
        ticks / 50U);
}

static void amiga_protection_string(uint32_t protection, char out[9]) {
    static const char chars[] = "hsparwed";
    static const uint32_t masks[] = {0x80U, 0x40U, 0x20U, 0x10U, 0x08U, 0x04U, 0x02U, 0x01U};
    static const uint8_t set_means_present[] = {1U, 1U, 1U, 1U, 0U, 0U, 0U, 0U};
    size_t i;
    for (i = 0U; i < 8U; ++i) {
        int has_flag = (protection & masks[i]) != 0U;
        int present = set_means_present[i] ? has_flag : !has_flag;
        out[i] = present ? chars[i] : '-';
    }
    out[8] = '\0';
}

static const char *amiga_adf_variant_name(uint32_t image_size) {
    if (image_size == 901120U) return "DD";
    if (image_size == 1802240U) return "HD";
    return "unknown";
}

static uint32_t amiga_adf_sectors_per_track(uint32_t image_size) {
    if (image_size == 1802240U) return 22U;
    return 11U;
}

static void platform_disk_add_error(M68kDiagList *diagnostics, const char *message) {
    if (message == NULL || message[0] == '\0') message = "platform disk operation failed";
    m68k_diag_add(m68k_diag_sink(diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_DISK_FAILED, message);
}

static int disk_text_result_to_alloc(PlatformDiskTextResult *result, char **out_json) {
    const char *message;
    if (out_json == NULL) return -1;
    *out_json = NULL;
    if (result == NULL) {
        *out_json = m68k_platform_dup_string("platform disk operation failed");
        return -1;
    }
    if (m68k_diag_has_errors(&result->diagnostics) || result->text == NULL) {
        message = m68k_diag_first_message(&result->diagnostics);
        if (message == NULL || message[0] == '\0') message = "platform disk operation failed";
        *out_json = m68k_platform_dup_string(message);
        free(result->text);
        result->text = NULL;
        return -1;
    }
    *out_json = result->text;
    result->text = NULL;
    return 0;
}

static int read_file_to_arena(const char *path, Arena *arena, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics) {
    FILE *fp = NULL;
    int64_t file_size_signed = 0;
    unsigned char *buffer = NULL;
    size_t read_size = 0;
    if (path == NULL || arena == NULL || out_data == NULL || out_size == NULL) {
        platform_disk_add_error(diagnostics.list, "bad arguments");
        return -1;
    }
    fp = fopen(path, "rb");
    if (fp == NULL) {
        platform_disk_add_error(diagnostics.list, "could not open disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        platform_disk_add_error(diagnostics.list, "could not size disk image");
        return -1;
    }
    file_size_signed = (int64_t)ftell(fp);
    if (file_size_signed < 0) {
        fclose(fp);
        platform_disk_add_error(diagnostics.list, "could not size disk image");
        return -1;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        platform_disk_add_error(diagnostics.list, "could not rewind disk image");
        return -1;
    }
    buffer = (unsigned char *)arena_alloc(arena, (size_t)file_size_signed == 0U ? 1U : (size_t)file_size_signed);
    if (buffer == NULL) {
        fclose(fp);
        platform_disk_add_error(diagnostics.list, "out of memory");
        return -1;
    }
    read_size = fread(buffer, 1, (size_t)file_size_signed, fp);
    fclose(fp);
    if (read_size != (size_t)file_size_signed) {
        platform_disk_add_error(diagnostics.list, "could not read disk image");
        return -1;
    }
    *out_data = buffer;
    *out_size = (size_t)file_size_signed;
    return 0;
}

static int append_extent_bytes(const unsigned char *image, size_t image_size, uint32_t image_offset, uint32_t byte_size,
    unsigned char *out_data, size_t out_size, size_t *inout_pos) {
    if (image_offset > image_size || byte_size > image_size - image_offset) return -1;
    if (*inout_pos > out_size || byte_size > out_size - *inout_pos) return -1;
    if (byte_size != 0U) memcpy(out_data + *inout_pos, image + image_offset, byte_size);
    *inout_pos += byte_size;
    return 0;
}

static int extract_amiga_entry_payload_from_analysis_arena(const unsigned char *image, size_t image_size,
    const AmigaDiskEntry *entry, Arena *arena, unsigned char **out_data, size_t *out_size) {
    unsigned char *data;
    size_t pos = 0;
    size_t i;
    if (entry == NULL || arena == NULL || out_data == NULL || out_size == NULL) return -1;
    data = (unsigned char *)arena_alloc(arena, entry->byte_size != 0U ? entry->byte_size : 1U);
    if (data == NULL) return -1;
    for (i = 0; i < entry->extent_count; ++i) {
        const AmigaDiskExtent *extent = &entry->extents[i];
        if (append_extent_bytes(image, image_size, extent->image_offset, extent->byte_size, data, entry->byte_size,
                &pos) != 0) {
            return -1;
        }
    }
    *out_data = data;
    *out_size = pos;
    return 0;
}

static int sha1_hex8_text(const char *text, char out_hex[9]) {
    BCRYPT_ALG_HANDLE algorithm = NULL;
    BCRYPT_HASH_HANDLE hash = NULL;
    unsigned char digest[20];
    static const char hex[] = "0123456789abcdef";
    size_t text_len;
    size_t i;
    if (text == NULL || out_hex == NULL) return -1;
    text_len = strlen(text);
    out_hex[0] = '\0';
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA1_ALGORITHM, NULL, 0) != 0) goto fail;
    if (BCryptCreateHash(algorithm, &hash, NULL, 0, NULL, 0, 0) != 0) goto fail;
    if (BCryptHashData(hash, (PUCHAR)text, (ULONG)text_len, 0) != 0) goto fail;
    if (BCryptFinishHash(hash, digest, sizeof(digest), 0) != 0) goto fail;
    for (i = 0; i < 4U; ++i) {
        out_hex[i * 2U] = hex[digest[i] >> 4U];
        out_hex[i * 2U + 1U] = hex[digest[i] & 0x0FU];
    }
    out_hex[8] = '\0';
    BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    return 0;
fail:
    if (hash != NULL) BCryptDestroyHash(hash);
    if (algorithm != NULL) BCryptCloseAlgorithmProvider(algorithm, 0);
    return -1;
}

static int safe_id_char(int ch) {
    return (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '.' ||
        ch == '_' || ch == '-';
}

static int append_amiga_entry_local_target_id_json_string(JsonBuilder *builder, const char *full_path) {
    char digest[9];
    char candidate[128];
    size_t candidate_len = 0U, start = 0U, end;
    const char *cursor;
    if (full_path == NULL || sha1_hex8_text(full_path, digest) != 0) return -1;
    for (cursor = full_path; *cursor != '\0' && candidate_len < sizeof(candidate) - 1U; ++cursor) {
        unsigned char ch = (unsigned char)*cursor;
        if (ch == '/') {
            if (candidate_len + 2U >= sizeof(candidate)) break;
            candidate[candidate_len++] = '_';
            candidate[candidate_len++] = '_';
        } else if (safe_id_char(ch)) {
            candidate[candidate_len++] = (char)(ch >= 'A' && ch <= 'Z' ? ch - 'A' + 'a' : ch);
        } else {
            candidate[candidate_len++] = '_';
        }
    }
    while (start < candidate_len && (candidate[start] == '.' || candidate[start] == '_' || candidate[start] == '-'))
        start += 1U;
    end = candidate_len;
    while (end > start && (candidate[end - 1U] == '.' || candidate[end - 1U] == '_' || candidate[end - 1U] == '-'))
        end -= 1U;
    if (json_builder_append(builder, "\"amiga_hunk_") != 0) return -1;
    if (end > start) {
        size_t base_len = end - start, suffix_len = 1U + 8U, emitted = 0U;
        size_t max_after_prefix = 69U, candidate_total = base_len + suffix_len;
        size_t candidate_limit = candidate_total > 71U ? 71U : candidate_total;
        if (candidate_limit > max_after_prefix) candidate_limit = max_after_prefix;
        while (emitted < base_len && emitted < candidate_limit) {
            if (json_builder_appendf(builder, "%c", candidate[start + emitted]) != 0) return -1;
            emitted += 1U;
        }
        if (emitted < candidate_limit && json_builder_append(builder, "_") != 0) return -1;
        if (emitted < candidate_limit) emitted += 1U;
        while (emitted < candidate_limit) {
            size_t digest_index = emitted - base_len - 1U;
            if (digest_index >= 8U) break;
            if (json_builder_appendf(builder, "%c", digest[digest_index]) != 0) return -1;
            emitted += 1U;
        }
    } else if (json_builder_append(builder, digest) != 0) {
        return -1;
    }
    return json_builder_append(builder, "\"");
}

static const char *json_skip_ws_disk(const char *cursor) {
    while (*cursor == ' ' || *cursor == '\t' || *cursor == '\r' || *cursor == '\n') ++cursor;
    return cursor;
}

static const char *json_find_key_disk(const char *json, const char *key) {
    size_t key_len = strlen(key);
    const char *cursor;
    if (json == NULL || key == NULL) return NULL;
    for (cursor = json; *cursor != '\0'; ++cursor) {
        if (*cursor != '"') continue;
        if (memcmp(cursor + 1, key, key_len) != 0 || cursor[key_len + 1U] != '"') continue;
        cursor += key_len + 2U;
        cursor = json_skip_ws_disk(cursor);
        if (*cursor == ':') return json_skip_ws_disk(cursor + 1);
    }
    return NULL;
}

static const char *json_value_end_disk(const char *value) {
    int depth = 0;
    int in_string = 0;
    int escaped = 0;
    const char *cursor = value;
    if (value == NULL) return NULL;
    if (*cursor == '"') {
        for (++cursor; *cursor != '\0'; ++cursor) {
            if (escaped) escaped = 0;
            else if (*cursor == '\\') escaped = 1;
            else if (*cursor == '"') return cursor + 1;
        }
        return NULL;
    }
    if (*cursor == '{' || *cursor == '[') {
        for (; *cursor != '\0'; ++cursor) {
            if (in_string) {
                if (escaped) escaped = 0;
                else if (*cursor == '\\') escaped = 1;
                else if (*cursor == '"') in_string = 0;
                continue;
            }
            if (*cursor == '"') in_string = 1;
            else if (*cursor == '{' || *cursor == '[') ++depth;
            else if (*cursor == '}' || *cursor == ']') {
                --depth;
                if (depth == 0) return cursor + 1;
            }
        }
        return NULL;
    }
    while (*cursor != '\0' && *cursor != ',' && *cursor != '}') ++cursor;
    return cursor;
}

static int append_json_field_value_or_null(JsonBuilder *builder, const char *json, const char *key) {
    const char *value = json_find_key_disk(json, key);
    const char *end = json_value_end_disk(value);
    if (value == NULL || end == NULL) return json_builder_append(builder, "null");
    return json_builder_appendf(builder, "%.*s", (int)(end - value), value);
}

static int json_string_field_equals(const char *json, const char *key, const char *expected) {
    const char *value = json_find_key_disk(json, key);
    size_t len = expected != NULL ? strlen(expected) : 0U;
    if (value == NULL || *value != '"' || expected == NULL) return 0;
    return strncmp(value + 1, expected, len) == 0 && value[len + 1U] == '"';
}

static int append_empty_target_metadata_arrays_json(JsonBuilder *builder) {
    if (json_builder_append(builder, ",\"custom_structs\":[],\"rsset_layout_regions\":[],\"seeded_entities\":[]") != 0)
        return -1;
    if (json_builder_append(builder, ",\"seeded_code_labels\":[],\"seeded_code_entrypoints\":[]") != 0) return -1;
    if (json_builder_append(builder, ",\"absolute_code_labels\":[],\"execution_views\":[]") != 0) return -1;
    return json_builder_append(builder, ",\"suppressed_seeded_items\":[]");
}

static int append_boot_entry_register_seeds_json(JsonBuilder *builder) {
    const char *exec_library = amiga_os_name(1U, AMIGA_OS_LIBRARY_ID_EXEC_LIBRARY);
    if (exec_library == NULL) exec_library = "exec.library";
    if (json_builder_append(builder, "[{\"entry_offset\":null,\"register\":\"A6\",\"kind\":\"library_base\"") != 0)
        return -1;
    if (json_builder_append(builder, ",\"library_name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, exec_library) != 0) return -1;
    if (json_builder_append(builder, ",\"struct_name\":\"LIB\",\"context_name\":null,\"note\":\"ExecBase\"}") != 0)
        return -1;
    if (json_builder_append(builder,
            ",{\"entry_offset\":null,\"register\":\"A1\",\"kind\":\"struct_ptr\",\"library_name\":null") != 0)
        return -1;
    if (json_builder_append(builder,
            ",\"struct_name\":\"IO\",\"context_name\":\"trackdisk.device\",\"note\":\"IOStdReq (open trackdisk.device)\"}]") != 0)
        return -1;
    return 0;
}

static int append_bootloader_local_target_id_json_string(JsonBuilder *builder, const char *stage_name,
    const char *suffix) {
    if (json_builder_append(builder, "\"amiga_raw_bootloader_") != 0) return -1;
    while (stage_name != NULL && *stage_name != '\0') {
        char ch = *stage_name++;
        if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '.' ||
            ch == '_' || ch == '-') {
            if (ch >= 'A' && ch <= 'Z') ch = (char)(ch - 'A' + 'a');
            if (json_builder_appendf(builder, "%c", ch) != 0) return -1;
        } else if (json_builder_append(builder, "_") != 0) {
            return -1;
        }
    }
    if (suffix != NULL && json_builder_append(builder, suffix) != 0) return -1;
    return json_builder_append(builder, "\"");
}

static int append_target_metadata_resident_json(JsonBuilder *builder, const char *inspect_json) {
    int32_t matchword = 0;
    const char *resident = json_find_key_disk(inspect_json, "resident");
    if (resident == NULL || strncmp(resident, "null", 4U) == 0) return json_builder_append(builder, "null");
    if (!amiga_os_find_constant_value_by_id(AMIGA_OS_SYMBOL_ID_RTC_MATCHWORD, &matchword)) return -1;
    if (json_builder_append(builder, "{\"matchword\":") != 0) return -1;
    if (json_builder_appendf(builder, "%d", (int)matchword) != 0) return -1;
    if (json_builder_append(builder, ",\"offset\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "offset") != 0) return -1;
    if (json_builder_append(builder, ",\"flags\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "flags") != 0) return -1;
    if (json_builder_append(builder, ",\"version\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "version") != 0) return -1;
    if (json_builder_append(builder, ",\"node_type_name\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "node_type_name") != 0) return -1;
    if (json_builder_append(builder, ",\"priority\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "priority") != 0) return -1;
    if (json_builder_append(builder, ",\"name\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "name") != 0) return -1;
    if (json_builder_append(builder, ",\"id_string\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "id_string") != 0) return -1;
    if (json_builder_append(builder, ",\"init_offset\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "init_offset") != 0) return -1;
    if (json_builder_append(builder, ",\"auto_init\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "auto_init") != 0) return -1;
    if (json_builder_append(builder, ",\"autoinit\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, resident, "autoinit") != 0) return -1;
    return json_builder_append(builder, "}");
}

static int append_import_target_json(JsonBuilder *builder, const char *inspect_json, const char *entry_path) {
    if (inspect_json == NULL || !json_string_field_equals(inspect_json, "file_kind", "executable"))
        return json_builder_append(builder, "null");
    if (json_builder_append(builder, "{\"target_type\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, inspect_json, "target_type") != 0) return -1;
    if (json_builder_append(builder, ",\"entry_path\":") != 0) return -1;
    if (json_builder_append_json_string(builder, entry_path != NULL ? entry_path : "") != 0) return -1;
    if (json_builder_append(builder, ",\"local_target_id\":") != 0) return -1;
    if (append_amiga_entry_local_target_id_json_string(builder, entry_path) != 0) return -1;
    if (json_builder_append(builder, ",\"target_metadata\":{\"target_type\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, inspect_json, "target_type") != 0) return -1;
    if (json_builder_append(builder, ",\"entry_register_seeds\":[],\"bootblock\":null,\"resident\":") != 0)
        return -1;
    if (append_target_metadata_resident_json(builder, inspect_json) != 0) return -1;
    if (json_builder_append(builder, ",\"library\":") != 0) return -1;
    if (append_json_field_value_or_null(builder, inspect_json, "library") != 0) return -1;
    if (append_empty_target_metadata_arrays_json(builder) != 0) return -1;
    if (json_builder_append(builder, "}}") != 0) return -1;
    return 0;
}

static int append_bootblock_import_target_json(JsonBuilder *builder, const AmigaDiskAnalysis *analysis,
    const char *fs_description) {
    uint32_t load_address = AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DEFAULT_LOAD_ADDRESS;
    uint32_t entry_offset = AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_ENTRY_OFFSET;
    uint32_t byte_size = analysis->bootcode_size + entry_offset;
    if (json_builder_append(builder,
            "{\"target_type\":\"bootblock\",\"entry_path\":\"bootblock\",\"local_target_id\":\"amiga_raw_bootblock\"") != 0)
        return -1;
    if (analysis->bootcode_has_code) {
        if (json_builder_append(builder, ",\"source\":{\"kind\":\"raw_binary\"") != 0)
            return -1;
        if (json_builder_appendf(builder,
                ",\"address_model\":\"local_offset\",\"byte_offset\":0,\"byte_size\":%u,\"load_address\":%u",
                byte_size, load_address) != 0)
            return -1;
        if (json_builder_appendf(builder, ",\"entrypoint\":%u,\"code_start_offset\":%u}", load_address + entry_offset,
                entry_offset) != 0)
            return -1;
    } else {
        if (json_builder_appendf(builder,
                ",\"source\":{\"kind\":\"asset_data\",\"byte_offset\":0,\"byte_size\":%u,\"load_address\":%u,"
                "\"role\":\"bootblock\"}",
                byte_size, load_address) != 0)
            return -1;
    }
    if (json_builder_append(builder, ",\"target_metadata\":{\"target_type\":\"bootblock\",\"entry_register_seeds\":") != 0)
        return -1;
    if (analysis->bootcode_has_code) {
        if (append_boot_entry_register_seeds_json(builder) != 0) return -1;
    } else if (json_builder_append(builder, "[]") != 0) {
        return -1;
    }
    if (json_builder_append(builder, ",\"bootblock\":{\"magic_ascii\":") != 0) return -1;
    if (json_builder_append_json_string(builder, analysis->boot_magic) != 0) return -1;
    if (json_builder_appendf(builder, ",\"flags_byte\":%u,\"fs_description\":", analysis->dos_flags) != 0) return -1;
    if (json_builder_append_json_string(builder, fs_description) != 0) return -1;
    if (json_builder_appendf(builder,
            ",\"checksum\":\"0x%08X\",\"checksum_valid\":%s,\"rootblock_ptr\":%u,\"bootcode_offset\":%u",
            analysis->boot_checksum, analysis->boot_checksum_valid ? "true" : "false", analysis->root_block,
            entry_offset) != 0)
        return -1;
    if (json_builder_appendf(builder,
            ",\"bootcode_size\":%u,\"load_address\":%u,\"entrypoint\":%u}",
            analysis->bootcode_size, load_address, load_address + entry_offset) != 0)
        return -1;
    if (json_builder_append(builder, ",\"resident\":null,\"library\":null") != 0) return -1;
    if (append_empty_target_metadata_arrays_json(builder) != 0) return -1;
    return json_builder_append(builder, "}}");
}

static int append_amiga_entry_content_json(JsonBuilder *builder, Arena *workflow_arena, const unsigned char *image,
    size_t image_size, const AmigaDiskEntry *entry) {
    ArenaMark mark;
    unsigned char *payload = NULL;
    size_t payload_size = 0U;
    char hash[65];
    int is_hunk = 0;
    int is_iff = 0;
    if (entry == NULL || entry->kind != AMIGA_DISK_ENTRY_FILE) return json_builder_append(builder, "null");
    mark = arena_mark(workflow_arena);
    if (entry->byte_size > AMIGA_DISK_CONTENT_CLASSIFY_MAX_BYTES ||
        extract_amiga_entry_payload_from_analysis_arena(image, image_size, entry, workflow_arena, &payload,
            &payload_size) != 0 ||
        m68k_platform_sha256_hex(payload, payload_size, hash) != 0) {
        arena_rewind(workflow_arena, mark);
        return json_builder_append(builder, "null");
    }
    is_hunk = payload_size >= 4U && payload[0] == 0x00U && payload[1] == 0x00U && payload[2] == 0x03U && payload[3] == 0xF3U;
    is_iff = payload_size >= 12U &&
        (memcmp(payload, "FORM", 4U) == 0 || memcmp(payload, "LIST", 4U) == 0 || memcmp(payload, "CAT ", 4U) == 0);
    if (json_builder_append(builder, "{\"kind\":") != 0) goto fail;
    if (is_hunk) {
        PlatformFileTextResult hunk_info = platform_file_inspect_buffer_json("amiga-hunk", payload, payload_size);
        int inspect_ok = !m68k_diag_has_errors(&hunk_info.diagnostics) && hunk_info.text != NULL;
        if (json_builder_append_json_string(builder, "amiga_hunk_executable") != 0) goto fail_hunk;
        if (json_builder_appendf(builder, ",\"size\":%zu,\"sha256\":", payload_size) != 0) goto fail_hunk;
        if (json_builder_append_json_string(builder, hash) != 0) goto fail_hunk;
        if (inspect_ok) {
            if (json_builder_appendf(builder, ",\"is_executable\":%s,\"hunk_count\":",
                    json_string_field_equals(hunk_info.text, "file_kind", "executable") ? "true" : "false") != 0)
                goto fail_hunk;
            if (append_json_field_value_or_null(builder, hunk_info.text, "section_count") != 0) goto fail_hunk;
            if (json_builder_append(builder, ",\"target_type\":") != 0) goto fail_hunk;
            if (append_json_field_value_or_null(builder, hunk_info.text, "target_type") != 0) goto fail_hunk;
            if (json_builder_append(builder, ",\"resident\":") != 0) goto fail_hunk;
            if (append_json_field_value_or_null(builder, hunk_info.text, "resident") != 0) goto fail_hunk;
            if (json_builder_append(builder, ",\"library\":") != 0) goto fail_hunk;
            if (append_json_field_value_or_null(builder, hunk_info.text, "library") != 0) goto fail_hunk;
            if (json_builder_append(builder, ",\"import_target\":") != 0) goto fail_hunk;
            if (append_import_target_json(builder, hunk_info.text, entry->path) != 0) goto fail_hunk;
        } else {
            if (json_builder_append(builder, ",\"is_executable\":false,\"hunk_count\":null") != 0) goto fail_hunk;
            if (json_builder_append(builder, ",\"target_type\":null,\"resident\":null,\"library\":null") != 0)
                goto fail_hunk;
            if (json_builder_append(builder, ",\"import_target\":null") != 0) goto fail_hunk;
        }
        if (json_builder_append(builder, "}") != 0) goto fail_hunk;
        platform_file_free_text(hunk_info.text);
        arena_rewind(workflow_arena, mark);
        return 0;
fail_hunk:
        platform_file_free_text(hunk_info.text);
        goto fail;
    }
    if (is_iff) {
        uint32_t total_size = ((uint32_t)payload[4] << 24U) | ((uint32_t)payload[5] << 16U) |
            ((uint32_t)payload[6] << 8U) | (uint32_t)payload[7];
        is_iff = total_size + 8U <= payload_size;
    }
    if (json_builder_append_json_string(builder, is_iff ? "iff_container" : "unknown") != 0) goto fail;
    if (json_builder_appendf(builder, ",\"size\":%zu,\"sha256\":", payload_size) != 0) goto fail;
    if (json_builder_append_json_string(builder, hash) != 0) goto fail;
    if (is_iff) {
        char group_id[5];
        char form_id[5];
        memcpy(group_id, payload, 4U);
        memcpy(form_id, payload + 8U, 4U);
        group_id[4] = '\0';
        form_id[4] = '\0';
        if (json_builder_append(builder, ",\"group_id\":") != 0) goto fail;
        if (json_builder_append_json_string(builder, group_id) != 0) goto fail;
        if (json_builder_append(builder, ",\"form_id\":") != 0) goto fail;
        if (json_builder_append_json_string(builder, form_id) != 0) goto fail;
    }
    if (json_builder_append(builder, "}") != 0) goto fail;
    arena_rewind(workflow_arena, mark);
    return 0;
fail:
    arena_rewind(workflow_arena, mark);
    return -1;
}

static int find_amiga_entry(const AmigaDiskAnalysis *analysis, const char *entry_path, const AmigaDiskEntry **out_entry) {
    size_t i;
    if (analysis == NULL || entry_path == NULL || out_entry == NULL) return -1;
    for (i = 0; i < analysis->entry_count; ++i) {
        const AmigaDiskEntry *entry = &analysis->entries[i];
        if (entry->kind == AMIGA_DISK_ENTRY_FILE && entry->path != NULL && _stricmp(entry->path, entry_path) == 0) {
            *out_entry = entry;
            return 0;
        }
    }
    return -1;
}

static int extract_amiga_entry_from_buffer(const unsigned char *image, size_t image_size, const char *entry_path,
    unsigned char **out_data, size_t *out_size, M68kDiagSink diagnostics) {
    AmigaDiskAnalysis analysis;
    const AmigaDiskEntry *entry = NULL;
    unsigned char *data = NULL;
    size_t pos = 0;
    size_t i;
    if (amiga_disk_analyze_buffer(image, image_size, &analysis, diagnostics) != 0) return -1;
    if (find_amiga_entry(&analysis, entry_path, &entry) != 0 || entry == NULL) {
        amiga_disk_analysis_destroy(&analysis);
        platform_disk_add_error(diagnostics.list, "disk entry not found");
        return -1;
    }
    data = (unsigned char *)malloc(entry->byte_size != 0U ? entry->byte_size : 1U);
    if (data == NULL) {
        amiga_disk_analysis_destroy(&analysis);
        platform_disk_add_error(diagnostics.list, "out of memory");
        return -1;
    }
    for (i = 0; i < entry->extent_count; ++i) {
        const AmigaDiskExtent *extent = &entry->extents[i];
        if (append_extent_bytes(image, image_size, extent->image_offset, extent->byte_size, data, entry->byte_size,
                &pos) != 0) {
            free(data);
            amiga_disk_analysis_destroy(&analysis);
            platform_disk_add_error(diagnostics.list, "invalid disk entry extent");
            return -1;
        }
    }
    amiga_disk_analysis_destroy(&analysis);
    *out_data = data;
    *out_size = pos;
    return 0;
}

static int find_atari_entry(const AtariStDiskAnalysis *analysis, const char *entry_path, const AtariStDiskEntry **out_entry) {
    size_t i;
    if (analysis == NULL || entry_path == NULL || out_entry == NULL) return -1;
    for (i = 0; i < analysis->entry_count; ++i) {
        const AtariStDiskEntry *entry = &analysis->entries[i];
        if (entry->kind == ATARI_ST_DISK_ENTRY_FILE && entry->path != NULL && _stricmp(entry->path, entry_path) == 0) {
            *out_entry = entry;
            return 0;
        }
    }
    return -1;
}

static const char *amiga_disk_entry_kind_name(AmigaDiskEntryKind kind) {
    switch (kind) {
        case AMIGA_DISK_ENTRY_FILE:
            return "file";
        case AMIGA_DISK_ENTRY_DIRECTORY:
            return "directory";
        case AMIGA_DISK_ENTRY_VOLUME:
            return "volume";
        default:
            return "unknown";
    }
}

static int extract_atari_entry_from_buffer(const unsigned char *image, size_t image_size, const char *entry_path,
    unsigned char **out_data, size_t *out_size, M68kDiagSink diagnostics) {
    AtariStDiskAnalysis analysis;
    const AtariStDiskEntry *entry = NULL;
    unsigned char *data = NULL;
    size_t pos = 0;
    size_t i;
    if (atari_st_disk_analyze_buffer(image, image_size, &analysis, diagnostics) != 0) return -1;
    if (find_atari_entry(&analysis, entry_path, &entry) != 0 || entry == NULL) {
        atari_st_disk_analysis_destroy(&analysis);
        platform_disk_add_error(diagnostics.list, "disk entry not found");
        return -1;
    }
    data = (unsigned char *)malloc(entry->file_size != 0U ? entry->file_size : 1U);
    if (data == NULL) {
        atari_st_disk_analysis_destroy(&analysis);
        platform_disk_add_error(diagnostics.list, "out of memory");
        return -1;
    }
    for (i = 0; i < entry->extent_count; ++i) {
        const AtariStDiskExtent *extent = &entry->extents[i];
        if (append_extent_bytes(image, image_size, extent->image_offset, extent->byte_size, data, entry->file_size,
                &pos) != 0) {
            free(data);
            atari_st_disk_analysis_destroy(&analysis);
            platform_disk_add_error(diagnostics.list, "invalid disk entry extent");
            return -1;
        }
    }
    atari_st_disk_analysis_destroy(&analysis);
    *out_data = data;
    *out_size = pos;
    return 0;
}

static int append_u32_json_array(JsonBuilder *builder, const uint32_t *items, size_t count) {
    size_t i;
    for (i = 0; i < count; ++i) {
        if (i != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_appendf(builder, "%u", items[i]) != 0) return -1;
    }
    return 0;
}

static int append_nullable_u32_json(JsonBuilder *builder, uint8_t has_value, uint32_t value) {
    if (!has_value) return json_builder_append(builder, "null");
    return json_builder_appendf(builder, "%u", value);
}

static int append_amiga_track_analysis_json(JsonBuilder *builder, const AmigaDiskAnalysis *analysis) {
    size_t i;
    size_t emitted = 0U;
    if (json_builder_appendf(builder,
            ",\"track_analysis\":{\"total_tracks\":%u,\"track_size_bytes\":%u,\"non_empty_tracks\":%u,\"tracks\":[",
            analysis->total_tracks, analysis->track_size_bytes, analysis->non_empty_tracks) != 0) {
        return -1;
    }
    for (i = 0; i < analysis->track_count; ++i) {
        const AmigaDiskTrackInfo *track = &analysis->tracks[i];
        size_t j;
        if (track->empty) continue;
        if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_appendf(builder,
                "{\"track\":%u,\"cylinder\":%u,\"head\":%u,\"first_block\":%u,\"byte_offset\":%u,\"byte_length\":%u",
                track->track, track->cylinder, track->head, track->first_block, track->byte_offset,
                track->byte_length) != 0) {
            return -1;
        }
        if (json_builder_appendf(builder,
                ",\"empty\":%s,\"entropy\":%.2f,\"m68k_pattern_count\":%u,\"has_code\":%s,\"ascii_strings\":[",
                track->empty ? "true" : "false", track->entropy, track->m68k_pattern_count,
                track->has_code ? "true" : "false") != 0) {
            return -1;
        }
        for (j = 0; j < track->ascii_string_count; ++j) {
            if (j != 0U && json_builder_append(builder, ",") != 0) return -1;
            if (json_builder_appendf(builder, "{\"offset\":%u,\"text\":", track->ascii_strings[j].offset) != 0)
                return -1;
            if (json_builder_append_json_string(builder, track->ascii_strings[j].text) != 0) return -1;
            if (json_builder_append(builder, "}") != 0) return -1;
        }
        if (json_builder_append(builder, "]}") != 0) return -1;
    }
    if (json_builder_append(builder, "],\"raw_sources\":[") != 0) return -1;
    emitted = 0U;
    for (i = 0; i < analysis->track_count; ++i) {
        const AmigaDiskTrackInfo *track = &analysis->tracks[i];
        if (track->empty) continue;
        if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_appendf(builder,
                "{\"track\":%u,\"cylinder\":%u,\"head\":%u,\"byte_offset\":%u,\"byte_length\":%u}",
                track->track, track->cylinder, track->head, track->byte_offset, track->byte_length) != 0) {
            return -1;
        }
    }
    return json_builder_append(builder, "]}");
}

static int append_amiga_trackloader_analysis_json(JsonBuilder *builder, const AmigaDiskAnalysis *analysis) {
    size_t i;
    if (json_builder_append(builder, ",\"trackloader_analysis\":{\"boot_ascii_strings\":[") != 0) return -1;
    for (i = 0; i < analysis->boot_ascii_string_count; ++i) {
        if (i != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_append_json_string(builder, analysis->boot_ascii_strings[i].text) != 0) return -1;
    }
    if (json_builder_append(builder, "],\"candidate_code_tracks\":[") != 0) return -1;
    if (append_u32_json_array(builder, analysis->candidate_code_tracks, analysis->candidate_code_track_count) != 0)
        return -1;
    if (json_builder_append(builder, "],\"high_entropy_tracks\":[") != 0) return -1;
    if (append_u32_json_array(builder, analysis->high_entropy_tracks, analysis->high_entropy_track_count) != 0)
        return -1;
    if (json_builder_append(builder, "],\"nonempty_track_spans\":[") != 0) return -1;
    for (i = 0; i < analysis->nonempty_track_span_count; ++i) {
        const AmigaDiskTrackSpan *span = &analysis->nonempty_track_spans[i];
        if (i != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_appendf(builder, "{\"start_track\":%u,\"end_track\":%u}", span->start_track,
                span->end_track) != 0) {
            return -1;
        }
    }
    return json_builder_appendf(builder,
        "],\"repeated_track_groups\":[],\"nonempty_head0_tracks\":%u,\"nonempty_head1_tracks\":%u}",
        analysis->nonempty_head0_tracks, analysis->nonempty_head1_tracks);
}

static int append_bootloader_stage_import_target_json(JsonBuilder *builder, const AmigaDiskBootloaderStage *stage) {
    if (stage == NULL || !stage->materialized || !stage->has_disk_read ||
        stage->kind == AMIGA_DISK_BOOTLOADER_STAGE_BOOT) {
        return json_builder_append(builder, "null");
    }
    if (json_builder_append(builder, "{\"target_type\":\"bootloader_stage\",\"entry_path\":\"bootloader/") != 0)
        return -1;
    if (json_builder_append(builder, stage->name) != 0) return -1;
    if (json_builder_append(builder, "\",\"local_target_id\":") != 0) return -1;
    if (append_bootloader_local_target_id_json_string(builder, stage->name, NULL) != 0) return -1;
    if (json_builder_append(builder, ",\"source\":{\"kind\":\"raw_binary\"") != 0)
        return -1;
    if (json_builder_appendf(builder,
            ",\"address_model\":\"runtime_absolute\",\"byte_offset\":%u,\"byte_size\":%u,\"load_address\":%u",
            stage->disk_offset, stage->size, stage->base_addr) != 0)
        return -1;
    if (json_builder_appendf(builder, ",\"entrypoint\":%u,\"code_start_offset\":0}", stage->entry_addr) != 0)
        return -1;
    if (json_builder_append(builder, ",\"target_metadata\":{\"target_type\":\"bootloader_stage\"") != 0) return -1;
    if (json_builder_append(builder, ",\"entry_register_seeds\":") != 0) return -1;
    if (stage->kind == AMIGA_DISK_BOOTLOADER_STAGE_MATERIALIZED_STAGE) {
        if (append_boot_entry_register_seeds_json(builder) != 0) return -1;
    } else if (json_builder_append(builder, "[]") != 0) {
        return -1;
    }
    if (json_builder_append(builder, ",\"bootblock\":null,\"resident\":null,\"library\":null") != 0) return -1;
    if (append_empty_target_metadata_arrays_json(builder) != 0) return -1;
    return json_builder_append(builder, "}}");
}

static int append_bootloader_raw_span_import_target_json(JsonBuilder *builder, const AmigaDiskBootloaderStage *stage,
    const AmigaDiskBootloaderDecodeRegion *region, size_t region_index) {
    const AmigaDiskRawTrackSourceSpan *span;
    uint32_t byte_size;
    char suffix[32];
    if (region == NULL || region->input_source_candidate_span_count != 1U ||
        !region->has_input_required_byte_length) {
        return json_builder_append(builder, "null");
    }
    span = &region->input_source_candidate_spans[0];
    byte_size = region->input_required_byte_length;
    snprintf(suffix, sizeof(suffix), "_raw_span_%u", (unsigned)region_index);
    if (json_builder_append(builder, "{\"target_type\":\"bootloader_raw_span\",\"entry_path\":\"bootloader/") != 0)
        return -1;
    if (json_builder_append(builder, stage->name) != 0) return -1;
    if (json_builder_appendf(builder, "/raw_span_%u\",\"local_target_id\":", (unsigned)region_index) != 0)
        return -1;
    if (append_bootloader_local_target_id_json_string(builder, stage->name, suffix) != 0) return -1;
    if (json_builder_append(builder, ",\"source\":{\"kind\":\"raw_binary\"") != 0)
        return -1;
    if (json_builder_appendf(builder,
            ",\"address_model\":\"local_offset\",\"byte_offset\":%u,\"byte_size\":%u,\"load_address\":0",
            span->start_byte_offset, byte_size) != 0)
        return -1;
    if (json_builder_append(builder, ",\"entrypoint\":0,\"code_start_offset\":0}") != 0) return -1;
    if (json_builder_append(builder,
            ",\"target_metadata\":{\"target_type\":\"bootloader_raw_span\",\"entry_register_seeds\":[]") != 0)
        return -1;
    if (json_builder_append(builder, ",\"bootblock\":null,\"resident\":null,\"library\":null") != 0) return -1;
    if (append_empty_target_metadata_arrays_json(builder) != 0) return -1;
    return json_builder_append(builder, "}}");
}

static int append_bootloader_decode_regions_json(JsonBuilder *builder, const AmigaDiskBootloaderStage *stage) {
    size_t region_index;
    if (json_builder_append(builder, ",\"decode_regions\":[") != 0) return -1;
    for (region_index = 0; region_index < stage->decode_region_count; ++region_index) {
        const AmigaDiskBootloaderDecodeRegion *region = &stage->decode_regions[region_index];
        const char *input_source_kind_name =
            amiga_disk_bootloader_decode_input_source_kind_name(region->input_source_kind);
        const char *input_required_source_kind_name =
            amiga_disk_bootloader_decode_required_source_kind_name(region->input_required_source_kind);
        const char *input_missing_reason_name =
            amiga_disk_bootloader_decode_input_missing_reason_name(region->input_missing_reason);
        size_t span_index;
        if (region_index != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_appendf(builder, "{\"instruction_addr\":%u,\"input_buffer_addr\":",
                region->instruction_addr) != 0)
            return -1;
        if (append_nullable_u32_json(builder, region->has_input_buffer_addr, region->input_buffer_addr) != 0) return -1;
        if (json_builder_append(builder, ",\"input_consumed_byte_offset\":") != 0) return -1;
        if (append_nullable_u32_json(builder, region->has_input_consumed_byte_offset,
                region->input_consumed_byte_offset) != 0)
            return -1;
        if (json_builder_append(builder, ",\"input_consumed_byte_length\":") != 0) return -1;
        if (append_nullable_u32_json(builder, region->has_input_consumed_byte_length,
                region->input_consumed_byte_length) != 0)
            return -1;
        if (json_builder_append(builder, ",\"checksum_gate_addr\":null,\"checksum_gate_kind\":null") != 0) return -1;
        if (json_builder_append(builder, ",\"input_source_kind\":") != 0) return -1;
        if (json_builder_append_json_string(builder, input_source_kind_name != NULL ? input_source_kind_name : "") != 0)
            return -1;
        if (json_builder_append(builder, ",\"input_required_source_kind\":") != 0) return -1;
        if (json_builder_append_json_string(builder,
                input_required_source_kind_name != NULL ? input_required_source_kind_name : "") != 0)
            return -1;
        if (json_builder_append(builder, ",\"input_source_candidates\":[],\"input_source_candidate_spans\":[") != 0)
            return -1;
        for (span_index = 0; span_index < region->input_source_candidate_span_count; ++span_index) {
            const AmigaDiskRawTrackSourceSpan *span = &region->input_source_candidate_spans[span_index];
            if (span_index != 0U && json_builder_append(builder, ",") != 0) return -1;
            if (json_builder_appendf(builder,
                    "{\"start_track\":%u,\"end_track\":%u,\"start_byte_offset\":%u,\"byte_length\":%u}",
                    span->start_track, span->end_track, span->start_byte_offset, span->byte_length) != 0)
                return -1;
        }
        if (json_builder_append(builder, "],\"input_required_byte_length\":") != 0) return -1;
        if (append_nullable_u32_json(builder, region->has_input_required_byte_length,
                region->input_required_byte_length) != 0)
            return -1;
        if (json_builder_appendf(builder,
                ",\"input_concrete_byte_count\":%u,\"input_complete\":%s,\"input_materializable\":%s",
                region->input_concrete_byte_count, region->input_complete ? "true" : "false",
                region->input_materializable ? "true" : "false") != 0)
            return -1;
        if (json_builder_append(builder, ",\"input_missing_reason\":") != 0) return -1;
        if (json_builder_append_json_string(builder,
                input_missing_reason_name != NULL ? input_missing_reason_name : "") != 0)
            return -1;
        if (json_builder_append(builder, ",\"output_base_addr\":") != 0) return -1;
        if (append_nullable_u32_json(builder, region->has_output_base_addr, region->output_base_addr) != 0) return -1;
        if (json_builder_append(builder, ",\"output_addr\":") != 0) return -1;
        if (append_nullable_u32_json(builder, region->has_output_addr, region->output_addr) != 0) return -1;
        if (json_builder_append(builder, ",\"byte_length\":") != 0) return -1;
        if (append_nullable_u32_json(builder, region->has_byte_length, region->byte_length) != 0) return -1;
        if (json_builder_appendf(builder, ",\"write_loop_addr\":%u,\"import_target\":",
                region->write_loop_addr) != 0)
            return -1;
        if (append_bootloader_raw_span_import_target_json(builder, stage, region, region_index) != 0) return -1;
        if (json_builder_append(builder, "}") != 0) return -1;
    }
    return json_builder_append(builder, "]");
}

static int append_amiga_bootloader_analysis_json(JsonBuilder *builder, const AmigaDiskAnalysis *analysis) {
    const char *stage_tail_json = ",\"derived_regions\":[],\"handoffs\":[],\"handoff_target\":null}";
    size_t i;
    if (json_builder_append(builder, ",\"bootloader_analysis\":{\"stages\":[") != 0) return -1;
    for (i = 0; i < analysis->bootloader_stage_count; ++i) {
        const AmigaDiskBootloaderStage *stage = &analysis->bootloader_stages[i];
        size_t access_index;
        size_t setup_index;
        if (i != 0U && json_builder_append(builder, ",") != 0) return -1;
        if (json_builder_append(builder, "{\"name\":") != 0) return -1;
        if (json_builder_append_json_string(builder, stage->name) != 0) return -1;
        if (json_builder_appendf(builder,
                ",\"base_addr\":%u,\"entry_addr\":%u,\"size\":%u,\"materialized\":%s,\"reachable_instruction_count\":%u",
                stage->base_addr, stage->entry_addr, stage->size, stage->materialized ? "true" : "false",
                stage->reachable_instruction_count) != 0) {
            return -1;
        }
        if (json_builder_append(builder, ",\"import_target\":") != 0) return -1;
        if (append_bootloader_stage_import_target_json(builder, stage) != 0) return -1;
        if (json_builder_append(builder, ",\"hardware_accesses\":[") != 0) return -1;
        for (access_index = 0; access_index < stage->hardware_access_count; ++access_index) {
            const AmigaDiskBootloaderHardwareAccess *access = &stage->hardware_accesses[access_index];
            if (access_index != 0U && json_builder_append(builder, ",") != 0) return -1;
            if (json_builder_appendf(builder, "{\"instruction_addr\":%u,\"access\":", access->instruction_addr) != 0)
                return -1;
            if (json_builder_append_json_string(builder, access->access) != 0) return -1;
            if (json_builder_appendf(builder, ",\"width_bits\":%u,\"address\":%u,\"symbol\":", access->width_bits,
                    access->address) != 0) {
                return -1;
            }
            if (json_builder_append_json_string(builder, access->symbol) != 0) return -1;
            if (access->has_value) {
                if (json_builder_appendf(builder, ",\"value\":%u}", access->value) != 0) return -1;
            } else if (json_builder_append(builder, ",\"value\":null}") != 0) {
                return -1;
            }
        }
        if (json_builder_append(builder, "],\"loads\":[],\"disk_reads\":[") != 0) return -1;
        if (stage->has_disk_read) {
            if (json_builder_appendf(builder,
                    "{\"instruction_addr\":%u,\"command_name\":\"CMD_READ\",\"source_kind\":\"logical_disk_offset\"",
                    stage->instruction_addr) != 0) {
                return -1;
            }
            if (json_builder_appendf(builder,
                    ",\"disk_offset\":%u,\"byte_length\":%u,\"destination_addr\":%u}",
                    stage->disk_offset, stage->byte_length, stage->base_addr) != 0) {
                return -1;
            }
        }
        if (json_builder_append(builder, "]") != 0) return -1;
        if (json_builder_append(builder, ",\"memory_copies\":[],\"read_setups\":[") != 0) return -1;
        for (setup_index = 0; setup_index < stage->read_setup_count; ++setup_index) {
            const AmigaDiskBootloaderReadSetup *setup = &stage->read_setups[setup_index];
            if (setup_index != 0U && json_builder_append(builder, ",") != 0) return -1;
            if (json_builder_appendf(builder, "{\"instruction_addr\":%u,\"buffer_addr\":", setup->instruction_addr) != 0)
                return -1;
            if (append_nullable_u32_json(builder, setup->has_buffer_addr, setup->buffer_addr) != 0) return -1;
            if (json_builder_append(builder, ",\"sync_word\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_sync_word, setup->sync_word) != 0) return -1;
            if (json_builder_append(builder, ",\"dsklen_value\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_dsklen_value, setup->dsklen_value) != 0) return -1;
            if (json_builder_append(builder, ",\"dsklen_dma_byte_length\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_dsklen_dma_byte_length, setup->dsklen_dma_byte_length) != 0)
                return -1;
            if (json_builder_appendf(builder, ",\"dsklen_dma_enabled\":%s,\"dsklen_write\":%s",
                    setup->dsklen_dma_enabled ? "true" : "false", setup->dsklen_write ? "true" : "false") != 0) {
                return -1;
            }
            if (json_builder_append(builder, ",\"dma_byte_length\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_dma_byte_length, setup->dma_byte_length) != 0) return -1;
            if (json_builder_append(builder, ",\"drive\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_drive, setup->drive) != 0) return -1;
            if (json_builder_append(builder, ",\"cylinder\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_cylinder, setup->cylinder) != 0) return -1;
            if (json_builder_append(builder, ",\"head\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_head, setup->head) != 0) return -1;
            if (json_builder_append(builder, ",\"track\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_track, setup->track) != 0) return -1;
            if (json_builder_append(builder, ",\"adkcon_values\":[") != 0) return -1;
            if (append_u32_json_array(builder, setup->adkcon_values, setup->adkcon_value_count) != 0) return -1;
            if (json_builder_append(builder, "],\"dmacon_values\":[") != 0) return -1;
            if (append_u32_json_array(builder, setup->dmacon_values, setup->dmacon_value_count) != 0) return -1;
            if (json_builder_append(builder, "],\"wait_loop_addr\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_wait_loop_addr, setup->wait_loop_addr) != 0) return -1;
            if (json_builder_append(builder, ",\"buffer_scan_addr\":") != 0) return -1;
            if (append_nullable_u32_json(builder, setup->has_buffer_scan_addr, setup->buffer_scan_addr) != 0) return -1;
            if (json_builder_append(builder, "}") != 0) return -1;
        }
        if (json_builder_append(builder, "],\"decode_outputs\":[]") != 0) return -1;
        if (append_bootloader_decode_regions_json(builder, stage) != 0) return -1;
        if (json_builder_append(builder, stage_tail_json) != 0) return -1;
    }
    if (json_builder_append(builder, "],\"memory_regions\":[],\"transfers\":[") != 0) return -1;
    {
        size_t transfer_index = 0U;
        for (i = 0; i < analysis->bootloader_stage_count; ++i) {
            const AmigaDiskBootloaderStage *stage = &analysis->bootloader_stages[i];
            if (!stage->has_disk_read) continue;
            if (transfer_index++ != 0U && json_builder_append(builder, ",") != 0) return -1;
            if (json_builder_append(builder, "{\"stage_name\":") != 0) return -1;
            if (json_builder_append_json_string(builder, stage->name) != 0) return -1;
            if (json_builder_appendf(builder,
                    ",\"transfer_kind\":\"disk_read\",\"source_kind\":\"logical_disk_offset\",\"destination_addr\":%u",
                    stage->base_addr) != 0) {
                return -1;
            }
            if (json_builder_appendf(builder,
                    ",\"byte_length\":%u,\"source_addr\":null,\"disk_offset\":%u,\"input_buffer_addr\":null",
                    stage->byte_length, stage->disk_offset) != 0) {
                return -1;
            }
            if (json_builder_append(builder,
                    ",\"output_addr\":null,\"target_addr\":null,\"start_track\":null,\"end_track\":null") != 0) {
                return -1;
            }
            if (json_builder_append(builder,
                    ",\"start_byte_offset\":null,\"checksum_gate_addr\":null,\"checksum_gate_kind\":null}") != 0) {
                return -1;
            }
        }
    }
    return json_builder_append(builder, "]}");
}

static int inspect_amiga_disk_json(const AmigaDiskAnalysis *analysis, Arena *workflow_arena,
    const unsigned char *image, size_t image_size, char **out_json) {
    JsonBuilder builder = {0};
    size_t i;
    const char *fs_type = "";
    const char *fs_description = "";
    const char *variant_name = amiga_adf_variant_name(analysis->image_size);
    uint32_t sectors_per_track = amiga_adf_sectors_per_track(analysis->image_size);
    if (analysis->is_dos) {
        switch (analysis->dos_flags) {
            case AMIGA_DISK_FILE_DOS_FLAGS_OFS:
                fs_type = "0";
                fs_description = "DOS\\0 - Original File System";
                break;
            case AMIGA_DISK_FILE_DOS_FLAGS_FFS:
                fs_type = "1";
                fs_description = "DOS\\1 - Fast File System";
                break;
            case AMIGA_DISK_FILE_DOS_FLAGS_INTL:
                fs_type = "2";
                fs_description = "DOS\\2 - International OFS";
                break;
            case AMIGA_DISK_FILE_DOS_FLAGS_FFS | AMIGA_DISK_FILE_DOS_FLAGS_INTL:
                fs_type = "3";
                fs_description = "DOS\\3 - International FFS";
                break;
            case AMIGA_DISK_FILE_DOS_FLAGS_DIRCACHE:
                fs_type = "4";
                fs_description = "DOS\\4 - Directory Cache OFS";
                break;
            case AMIGA_DISK_FILE_DOS_FLAGS_FFS | AMIGA_DISK_FILE_DOS_FLAGS_DIRCACHE:
                fs_type = "5";
                fs_description = "DOS\\5 - Directory Cache FFS";
                break;
            default:
                fs_type = "DOS";
                fs_description = "DOS - unknown flags";
                break;
        }
    }
    if (json_builder_create(&builder) != 0) goto fail;
    if (json_builder_append(&builder, "{\"platform\":\"amiga-disk\",\"format_kind\":") != 0) goto fail;
    if (json_builder_append_json_string(&builder, amiga_disk_format_kind_name(analysis->format_kind)) != 0) goto fail;
    if (json_builder_appendf(&builder,
            ",\"disk_info\":{\"size\":%u,\"variant\":", analysis->image_size) != 0) {
        goto fail;
    }
    if (json_builder_append_json_string(&builder, variant_name) != 0) goto fail;
    if (json_builder_appendf(&builder,
            ",\"total_sectors\":%u,\"sectors_per_track\":%u,\"is_dos\":%u}",
            analysis->total_blocks, sectors_per_track, analysis->is_dos) != 0) {
        goto fail;
    }
    if (json_builder_appendf(&builder,
            ",\"root_block\":%u,\"is_dos\":%u,\"dos_flags\":%u,\"boot_block\":{\"magic_ascii\":",
            analysis->root_block, analysis->is_dos, analysis->dos_flags) != 0) {
        goto fail;
    }
    if (json_builder_append_json_string(&builder, analysis->boot_magic) != 0) goto fail;
    if (json_builder_appendf(&builder,
            ",\"magic_bytes\":[%u,%u,%u],\"is_dos\":%u,\"flags_byte\":%u,\"fs_type\":",
            (unsigned)(unsigned char)analysis->boot_magic[0],
            (unsigned)(unsigned char)analysis->boot_magic[1],
            (unsigned)(unsigned char)analysis->boot_magic[2],
            analysis->is_dos, analysis->dos_flags) != 0) {
        goto fail;
    }
    if (json_builder_append_json_string(&builder, fs_type) != 0) goto fail;
    if (json_builder_append(&builder, ",\"fs_description\":") != 0) goto fail;
    if (json_builder_append_json_string(&builder, fs_description) != 0) goto fail;
    if (json_builder_appendf(&builder,
            ",\"checksum\":\"0x%08X\",\"expected_checksum\":\"0x%08X\",\"checksum_valid\":%u,\"rootblock_ptr\":%u",
            analysis->boot_checksum, analysis->boot_expected_checksum, analysis->boot_checksum_valid,
            analysis->root_block) != 0) {
        goto fail;
    }
    if (json_builder_appendf(&builder,
            ",\"bootcode_size\":%u,\"bootcode_has_code\":%u,\"bootcode_entropy\":%.2f,\"import_target\":",
            analysis->bootcode_size, analysis->bootcode_has_code, analysis->bootcode_entropy) != 0) {
        goto fail;
    }
    if (append_bootblock_import_target_json(&builder, analysis, fs_description) != 0) {
        goto fail;
    }
    if (json_builder_append(&builder, "}") != 0) {
        goto fail;
    }
    if (analysis->format_kind == AMIGA_DISK_FORMAT_DOS) {
        char root_date[20];
        char volume_date[20];
        char creation_date[20];
        amiga_date_to_iso(analysis->root_date_days, analysis->root_date_mins, analysis->root_date_ticks, root_date);
        amiga_date_to_iso(analysis->volume_date_days, analysis->volume_date_mins, analysis->volume_date_ticks, volume_date);
        amiga_date_to_iso(analysis->creation_date_days, analysis->creation_date_mins, analysis->creation_date_ticks,
            creation_date);
        if (json_builder_appendf(&builder,
                ",\"root\":{\"block_num\":%u,\"hash_table\":[",
                analysis->root_block) != 0) {
            goto fail;
        }
        for (i = 0; i < AMIGA_DISK_FILE_CONSTRAINTS_ROOT_HASH_TABLE_ENTRIES; ++i) {
            if (i != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "%u", analysis->root_hash_table[i]) != 0) goto fail;
        }
        if (json_builder_appendf(&builder,
                "],\"checksum_valid\":%u,\"bm_flag\":%d,\"bm_pages\":[",
                analysis->root_checksum_valid, analysis->root_bitmap_valid_flag) != 0) {
            goto fail;
        }
        for (i = 0; i < analysis->root_bitmap_page_count; ++i) {
            if (i != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "%u", analysis->root_bitmap_pages[i]) != 0) goto fail;
        }
        if (json_builder_append(&builder, "],\"volume_name\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, analysis->volume_name != NULL ? analysis->volume_name : "") != 0) goto fail;
        if (json_builder_appendf(&builder,
                ",\"root_date_days\":%u,\"root_date_mins\":%u,\"root_date_ticks\":%u",
                analysis->root_date_days, analysis->root_date_mins, analysis->root_date_ticks) != 0) {
            goto fail;
        }
        if (json_builder_append(&builder, ",\"root_date\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, root_date) != 0) goto fail;
        if (json_builder_appendf(&builder,
                ",\"volume_date_days\":%u,\"volume_date_mins\":%u,\"volume_date_ticks\":%u",
                analysis->volume_date_days, analysis->volume_date_mins, analysis->volume_date_ticks) != 0) {
            goto fail;
        }
        if (json_builder_append(&builder, ",\"volume_date\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, volume_date) != 0) goto fail;
        if (json_builder_appendf(&builder,
                ",\"creation_date_days\":%u,\"creation_date_mins\":%u,\"creation_date_ticks\":%u",
                analysis->creation_date_days, analysis->creation_date_mins, analysis->creation_date_ticks) != 0) {
            goto fail;
        }
        if (json_builder_append(&builder, ",\"creation_date\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, creation_date) != 0) goto fail;
        if (json_builder_append(&builder, "}") != 0) goto fail;
        if (json_builder_appendf(&builder,
                ",\"bitmap\":{\"checksum_valid\":%u,\"free_blocks\":%u,\"allocated_blocks\":%u,\"total_blocks\":%u,\"percent_used\":%.1f}",
                analysis->bitmap_checksum_valid, analysis->bitmap_free_blocks, analysis->bitmap_allocated_blocks,
                analysis->total_blocks, analysis->bitmap_percent_used) != 0) {
            goto fail;
        }
        if (json_builder_appendf(&builder,
                ",\"block_usage\":{\"summary\":{\"boot\":%u,\"root\":%u,\"bitmap\":%u,\"dir_header\":%u,\"file_header\":%u",
                analysis->block_usage.boot, analysis->block_usage.root, analysis->block_usage.bitmap,
                analysis->block_usage.dir_header, analysis->block_usage.file_header) != 0) {
            goto fail;
        }
        if (json_builder_appendf(&builder,
                ",\"data\":%u,\"extension\":%u,\"free\":%u,\"allocated_orphan\":%u,\"unknown\":%u},\"orphan_blocks\":[",
                analysis->block_usage.data, analysis->block_usage.extension, analysis->block_usage.free_blocks,
                analysis->block_usage.allocated_orphan, analysis->block_usage.unknown) != 0) {
            goto fail;
        }
        for (i = 0; i < analysis->orphan_block_count; ++i) {
            if (i != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "%u", analysis->orphan_blocks[i]) != 0) goto fail;
        }
        if (json_builder_append(&builder, "]}") != 0) goto fail;
    } else if (json_builder_append(&builder, ",\"root\":null") != 0) {
        goto fail;
    } else if (json_builder_append(&builder, ",\"bitmap\":null,\"block_usage\":null") != 0) {
        goto fail;
    }
    if (append_amiga_track_analysis_json(&builder, analysis) != 0) goto fail;
    if (append_amiga_trackloader_analysis_json(&builder, analysis) != 0) goto fail;
    if (append_amiga_bootloader_analysis_json(&builder, analysis) != 0) goto fail;
    if (json_builder_appendf(&builder, ",\"entry_count\":%zu,\"entries\":[", analysis->entry_count) != 0) goto fail;
    for (i = 0; i < analysis->entry_count; ++i) {
        const AmigaDiskEntry *entry = &analysis->entries[i];
        size_t j;
        char entry_date[20];
        char protection_text[9];
        amiga_date_to_iso(entry->date_days, entry->date_mins, entry->date_ticks, entry_date);
        amiga_protection_string(entry->protection, protection_text);
        if (i != 0U && json_builder_append(&builder, ",") != 0) goto fail;
        if (json_builder_append(&builder, "{\"path\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, entry->path != NULL ? entry->path : "") != 0) goto fail;
        if (json_builder_append(&builder, ",\"name\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, entry->name != NULL ? entry->name : "") != 0) goto fail;
        if (json_builder_append(&builder, ",\"kind_name\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, amiga_disk_entry_kind_name(entry->kind)) != 0) goto fail;
        if (json_builder_append(&builder, ",\"comment\":") != 0) goto fail;
        if (entry->comment != NULL) {
            if (json_builder_append_json_string(&builder, entry->comment) != 0) goto fail;
        } else if (json_builder_append(&builder, "null") != 0) {
            goto fail;
        }
        if (json_builder_appendf(&builder,
                ",\"kind\":%u,\"byte_size\":%u,\"header_block\":%u,\"protection_raw\":%u",
                (unsigned)entry->kind, entry->byte_size, entry->header_block, entry->protection) != 0) {
            goto fail;
        }
        if (json_builder_append(&builder, ",\"protection\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, protection_text) != 0) goto fail;
        if (json_builder_appendf(&builder,
                ",\"date_days\":%u,\"date_mins\":%u,\"date_ticks\":%u,\"hash_chain\":%u,\"parent\":%u,\"checksum_valid\":%u",
                entry->date_days, entry->date_mins, entry->date_ticks, entry->hash_chain, entry->parent,
                entry->checksum_valid) != 0) {
            goto fail;
        }
        if (json_builder_append(&builder, ",\"date\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, entry_date) != 0) goto fail;
        if (json_builder_append(&builder, ",\"extension_blocks\":[") != 0) goto fail;
        for (j = 0; j < entry->extension_block_count; ++j) {
            if (j != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "%u", entry->extension_blocks[j]) != 0) goto fail;
        }
        if (json_builder_append(&builder, "],\"data_blocks\":[") != 0) goto fail;
        for (j = 0; j < entry->extent_count; ++j) {
            if (j != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "%u", entry->extents[j].block_index) != 0) goto fail;
        }
        if (json_builder_append(&builder, "],\"extents\":[") != 0) goto fail;
        for (j = 0; j < entry->extent_count; ++j) {
            const AmigaDiskExtent *extent = &entry->extents[j];
            if (j != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "{\"block_index\":%u,\"image_offset\":%u,\"byte_size\":%u}",
                    extent->block_index, extent->image_offset, extent->byte_size) != 0) {
                goto fail;
            }
        }
        if (json_builder_append(&builder, "],\"content\":") != 0) goto fail;
        if (append_amiga_entry_content_json(&builder, workflow_arena, image, image_size, entry) != 0) goto fail;
        if (json_builder_append(&builder, "}") != 0) goto fail;
    }
    if (json_builder_append(&builder, "]}") != 0) goto fail;
    *out_json = json_builder_build(&builder);
    if (*out_json == NULL) goto fail;
    json_builder_destroy(&builder);
    return 0;

fail:
    json_builder_destroy(&builder);
    return -1;
}

static int inspect_atari_st_disk_json(const AtariStDiskAnalysis *analysis, char **out_json) {
    JsonBuilder builder = {0};
    size_t i;
    if (json_builder_create(&builder) != 0) goto fail;
    if (json_builder_append(&builder,
            "{\"platform\":\"atari-st-disk\",\"bytes_per_sector\":") != 0) {
        goto fail;
    }
    if (json_builder_appendf(&builder,
            "%u,\"sectors_per_cluster\":%u,\"fat_count\":%u,\"entry_count\":%zu,\"entries\":[",
            analysis->bytes_per_sector, analysis->sectors_per_cluster, analysis->fat_count, analysis->entry_count) != 0) {
        goto fail;
    }
    for (i = 0; i < analysis->entry_count; ++i) {
        const AtariStDiskEntry *entry = &analysis->entries[i];
        size_t j;
        if (i != 0U && json_builder_append(&builder, ",") != 0) goto fail;
        if (json_builder_append(&builder, "{\"path\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, entry->path != NULL ? entry->path : "") != 0) goto fail;
        if (json_builder_appendf(&builder,
                ",\"kind\":%u,\"file_size\":%u,\"first_cluster\":%u,\"attributes\":%u,\"is_executable_candidate\":%u,\"extents\":[",
                (unsigned)entry->kind, entry->file_size, entry->first_cluster, entry->attributes,
                entry->is_executable_candidate) != 0) {
            goto fail;
        }
        for (j = 0; j < entry->extent_count; ++j) {
            const AtariStDiskExtent *extent = &entry->extents[j];
            if (j != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "{\"cluster_index\":%u,\"image_offset\":%u,\"byte_size\":%u}",
                    extent->cluster_index, extent->image_offset, extent->byte_size) != 0) {
                goto fail;
            }
        }
        if (json_builder_append(&builder, "]}") != 0) goto fail;
    }
    if (json_builder_append(&builder, "]}") != 0) goto fail;
    *out_json = json_builder_build(&builder);
    if (*out_json == NULL) goto fail;
    json_builder_destroy(&builder);
    return 0;

fail:
    json_builder_destroy(&builder);
    return -1;
}

static int amiga_disk_inspect(const char *path, const unsigned char *data, size_t size,
    char **out_json, M68kDiagSink diagnostics) {
    AmigaDiskAnalysis analysis;
    Arena *workflow_arena = NULL;
    unsigned char *owned_data = NULL;
    size_t owned_size = 0U;
    int result = -1;
    workflow_arena = arena_create(PLATFORM_DISK_WORKFLOW_ARENA_SIZE);
    if (workflow_arena == NULL) {
        platform_disk_add_error(diagnostics.list, "out of memory");
        return -1;
    }
    if (path != NULL) {
        if (read_file_to_arena(path, workflow_arena, &owned_data, &owned_size, diagnostics) != 0) goto done;
        data = owned_data;
        size = owned_size;
    }
    if (amiga_disk_analyze_buffer(data, size, &analysis, diagnostics) != 0) {
        amiga_disk_analysis_destroy(&analysis);
        goto done;
    }
    if (inspect_amiga_disk_json(&analysis, workflow_arena, data, size, out_json) != 0) {
        platform_disk_add_error(diagnostics.list, "failed building inspect json");
        amiga_disk_analysis_destroy(&analysis);
        goto done;
    }
    amiga_disk_analysis_destroy(&analysis);
    result = 0;
done:
    arena_destroy(workflow_arena);
    return result;
}

static int atari_st_disk_inspect(const char *path, const unsigned char *data, size_t size,
    char **out_json, M68kDiagSink diagnostics) {
    AtariStDiskAnalysis analysis;
    if ((path != NULL ? atari_st_disk_analyze_image(path, &analysis, diagnostics)
                      : atari_st_disk_analyze_buffer(data, size, &analysis, diagnostics)) != 0) {
        atari_st_disk_analysis_destroy(&analysis);
        return -1;
    }
    if (inspect_atari_st_disk_json(&analysis, out_json) != 0) {
        platform_disk_add_error(diagnostics.list, "failed building inspect json");
        atari_st_disk_analysis_destroy(&analysis);
        return -1;
    }
    atari_st_disk_analysis_destroy(&analysis);
    return 0;
}

static int disk_inspect(const char *platform_name, const char *path, const unsigned char *data, size_t size,
    char **out_json, M68kDiagSink diagnostics) {
    switch (platform_disk_kind_from_name(platform_name)) {
        case PLATFORM_DISK_KIND_AMIGA:
            return amiga_disk_inspect(path, data, size, out_json, diagnostics);
        case PLATFORM_DISK_KIND_ATARI_ST:
            return atari_st_disk_inspect(path, data, size, out_json, diagnostics);
        default:
            platform_disk_add_error(diagnostics.list, "unknown disk platform");
            return -1;
    }
}

PLATFORM_DISK_API PlatformDiskTextResult platform_disk_inspect_path_json(const char *platform_name, const char *path) {
    PlatformDiskTextResult result;
    memset(&result, 0, sizeof(result));
    disk_inspect(platform_name, path, NULL, 0, &result.text, m68k_diag_sink(&result.diagnostics));
    return result;
}

PLATFORM_DISK_API PlatformDiskTextResult platform_disk_inspect_buffer_json(const char *platform_name,
    const unsigned char *data, size_t size) {
    PlatformDiskTextResult result;
    memset(&result, 0, sizeof(result));
    disk_inspect(platform_name, NULL, data, size, &result.text, m68k_diag_sink(&result.diagnostics));
    return result;
}

PLATFORM_DISK_API PlatformDiskBufferResult platform_disk_extract_entry_path(const char *platform_name, const char *path,
    const char *entry_path) {
    PlatformDiskBufferResult result;
    Arena *workflow_arena = NULL;
    unsigned char *image = NULL;
    size_t image_size = 0;
    memset(&result, 0, sizeof(result));
    workflow_arena = arena_create(PLATFORM_DISK_WORKFLOW_ARENA_SIZE);
    if (workflow_arena == NULL) {
        platform_disk_add_error(&result.diagnostics, "out of memory");
        return result;
    }
    if (read_file_to_arena(path, workflow_arena, &image, &image_size, m68k_diag_sink(&result.diagnostics)) != 0) {
        arena_destroy(workflow_arena);
        return result;
    }
    switch (platform_disk_kind_from_name(platform_name)) {
        case PLATFORM_DISK_KIND_AMIGA:
            extract_amiga_entry_from_buffer(image, image_size, entry_path, &result.data, &result.size,
                m68k_diag_sink(&result.diagnostics));
            break;
        case PLATFORM_DISK_KIND_ATARI_ST:
            extract_atari_entry_from_buffer(image, image_size, entry_path, &result.data, &result.size,
                m68k_diag_sink(&result.diagnostics));
            break;
        default:
            platform_disk_add_error(&result.diagnostics, "unknown disk platform");
            break;
    }
    arena_destroy(workflow_arena);
    return result;
}

PLATFORM_DISK_API int platform_disk_inspect_path_json_alloc(const char *platform_name, const char *path,
    char **out_json) {
    PlatformDiskTextResult result = platform_disk_inspect_path_json(platform_name, path);
    return disk_text_result_to_alloc(&result, out_json);
}

PLATFORM_DISK_API int platform_disk_extract_entry_path_bytes_alloc(const char *platform_name, const char *path,
    const char *entry_path, unsigned char **out_data, size_t *out_size, char **out_error) {
    PlatformDiskBufferResult result = platform_disk_extract_entry_path(platform_name, path, entry_path);
    const char *message;
    if (out_data == NULL || out_size == NULL) return -1;
    *out_data = NULL;
    *out_size = 0U;
    if (out_error != NULL) *out_error = NULL;
    if (m68k_diag_has_errors(&result.diagnostics) || result.data == NULL) {
        message = m68k_diag_first_message(&result.diagnostics);
        if (message == NULL || message[0] == '\0') message = "platform disk operation failed";
        if (out_error != NULL) *out_error = m68k_platform_dup_string(message);
        platform_disk_free_bytes(result.data);
        return -1;
    }
    *out_data = result.data;
    *out_size = result.size;
    return 0;
}

PLATFORM_DISK_API void platform_disk_free_text(char *text) {
    free(text);
}

PLATFORM_DISK_API void platform_disk_free_bytes(unsigned char *data) {
    free(data);
}
