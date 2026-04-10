#include "json_builder.h"
#include "platform_amiga_disk.h"
#include "platform_atari_st_disk.h"
#include "platform_common.h"
#include "platform_disk_lib.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    char **out_json, char *error_buf, size_t error_buf_size) {
    AmigaDiskAnalysis analysis;
    char error[256];
    if ((path != NULL ? amiga_disk_analyze_image(path, &analysis, error, sizeof(error))
                      : amiga_disk_analyze_buffer(data, size, &analysis, error, sizeof(error))) != 0) {
        m68k_platform_set_error(error_buf, error_buf_size, error);
        amiga_disk_analysis_destroy(&analysis);
        return -1;
    }
    if (inspect_amiga_disk_json(&analysis, out_json) != 0) {
        m68k_platform_set_error(error_buf, error_buf_size, "failed building inspect json");
        amiga_disk_analysis_destroy(&analysis);
        return -1;
    }
    amiga_disk_analysis_destroy(&analysis);
    return 0;
}

static int atari_st_disk_inspect(const char *path, const unsigned char *data, size_t size,
    char **out_json, char *error_buf, size_t error_buf_size) {
    AtariStDiskAnalysis analysis;
    char error[256];
    if ((path != NULL ? atari_st_disk_analyze_image(path, &analysis, error, sizeof(error))
                      : atari_st_disk_analyze_buffer(data, size, &analysis, error, sizeof(error))) != 0) {
        m68k_platform_set_error(error_buf, error_buf_size, error);
        atari_st_disk_analysis_destroy(&analysis);
        return -1;
    }
    if (inspect_atari_st_disk_json(&analysis, out_json) != 0) {
        m68k_platform_set_error(error_buf, error_buf_size, "failed building inspect json");
        atari_st_disk_analysis_destroy(&analysis);
        return -1;
    }
    atari_st_disk_analysis_destroy(&analysis);
    return 0;
}

static int disk_inspect(const char *platform_name, const char *path, const unsigned char *data, size_t size,
    char **out_json, char *error_buf, size_t error_buf_size) {
    if (_stricmp(platform_name, "amiga-disk") == 0 || _stricmp(platform_name, "amiga") == 0)
        return amiga_disk_inspect(path, data, size, out_json, error_buf, error_buf_size);
    if (_stricmp(platform_name, "atari-st-disk") == 0 || _stricmp(platform_name, "atari-st") == 0)
        return atari_st_disk_inspect(path, data, size, out_json, error_buf, error_buf_size);
    m68k_platform_set_error(error_buf, error_buf_size, "unknown disk platform");
    return -1;
}

PLATFORM_DISK_API int platform_disk_inspect_path_json(const char *platform_name, const char *path, char **out_json,
    char *error_buf, size_t error_buf_size) {
    return disk_inspect(platform_name, path, NULL, 0, out_json, error_buf, error_buf_size);
}

PLATFORM_DISK_API int platform_disk_inspect_buffer_json(const char *platform_name, const unsigned char *data,
    size_t size, char **out_json, char *error_buf, size_t error_buf_size) {
    return disk_inspect(platform_name, NULL, data, size, out_json, error_buf, error_buf_size);
}

PLATFORM_DISK_API void platform_disk_free_json(char *json) {
    free(json);
}
