#include "json_builder.h"
#include "platform_amiga_disk.h"
#include "platform_atari_st_disk.h"
#include "platform_disk_lib.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void platform_disk_add_error(M68kDiagList *diagnostics, const char *message) {
    if (message == NULL || message[0] == '\0') message = "platform disk operation failed";
    m68k_diag_add(m68k_diag_sink(diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_DISK_FAILED, message);
}

static int inspect_amiga_disk_json(const AmigaDiskAnalysis *analysis, char **out_json) {
    JsonBuilder builder = {0};
    size_t i;
    if (json_builder_create(&builder) != 0) goto fail;
    if (json_builder_append(&builder, "{\"platform\":\"amiga-disk\",\"format_kind\":") != 0) goto fail;
    if (json_builder_append_json_string(&builder, amiga_disk_format_kind_name(analysis->format_kind)) != 0) goto fail;
    if (json_builder_appendf(&builder, ",\"root_block\":%u,\"is_dos\":%u,\"dos_flags\":%u,\"entry_count\":%zu,\"entries\":[",
            analysis->root_block, analysis->is_dos, analysis->dos_flags, analysis->entry_count) != 0) {
        goto fail;
    }
    for (i = 0; i < analysis->entry_count; ++i) {
        const AmigaDiskEntry *entry = &analysis->entries[i];
        size_t j;
        if (i != 0U && json_builder_append(&builder, ",") != 0) goto fail;
        if (json_builder_append(&builder, "{\"path\":") != 0) goto fail;
        if (json_builder_append_json_string(&builder, entry->path != NULL ? entry->path : "") != 0) goto fail;
        if (json_builder_appendf(&builder, ",\"kind\":%u,\"byte_size\":%u,\"header_block\":%u,\"extents\":[",
                (unsigned)entry->kind, entry->byte_size, entry->header_block) != 0) {
            goto fail;
        }
        for (j = 0; j < entry->extent_count; ++j) {
            const AmigaDiskExtent *extent = &entry->extents[j];
            if (j != 0U && json_builder_append(&builder, ",") != 0) goto fail;
            if (json_builder_appendf(&builder, "{\"block_index\":%u,\"image_offset\":%u,\"byte_size\":%u}",
                    extent->block_index, extent->image_offset, extent->byte_size) != 0) {
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
    if ((path != NULL ? amiga_disk_analyze_image(path, &analysis, diagnostics)
                      : amiga_disk_analyze_buffer(data, size, &analysis, diagnostics)) != 0) {
        amiga_disk_analysis_destroy(&analysis);
        return -1;
    }
    if (inspect_amiga_disk_json(&analysis, out_json) != 0) {
        platform_disk_add_error(diagnostics.list, "failed building inspect json");
        amiga_disk_analysis_destroy(&analysis);
        return -1;
    }
    amiga_disk_analysis_destroy(&analysis);
    return 0;
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
    if (_stricmp(platform_name, "amiga-disk") == 0 || _stricmp(platform_name, "amiga") == 0)
        return amiga_disk_inspect(path, data, size, out_json, diagnostics);
    if (_stricmp(platform_name, "atari-st-disk") == 0 || _stricmp(platform_name, "atari-st") == 0)
        return atari_st_disk_inspect(path, data, size, out_json, diagnostics);
    platform_disk_add_error(diagnostics.list, "unknown disk platform");
    return -1;
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

PLATFORM_DISK_API void platform_disk_free_json(char *json) {
    free(json);
}
