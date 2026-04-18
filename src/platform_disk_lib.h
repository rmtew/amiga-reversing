#ifndef PLATFORM_DISK_LIB_H
#define PLATFORM_DISK_LIB_H

#include "m68k_diagnostics.h"

#include <stddef.h>

#ifdef _WIN32
#define PLATFORM_DISK_API __declspec(dllexport)
#else
#define PLATFORM_DISK_API
#endif

typedef struct PlatformDiskTextResult {
    char *text;
    M68kDiagList diagnostics;
} PlatformDiskTextResult;

typedef struct PlatformDiskBufferResult {
    unsigned char *data;
    size_t size;
    M68kDiagList diagnostics;
} PlatformDiskBufferResult;

PLATFORM_DISK_API PlatformDiskTextResult platform_disk_inspect_path_json(const char *platform_name, const char *path);
PLATFORM_DISK_API PlatformDiskTextResult platform_disk_inspect_buffer_json(const char *platform_name,
    const unsigned char *data, size_t size);
PLATFORM_DISK_API PlatformDiskBufferResult platform_disk_extract_entry_path(const char *platform_name, const char *path,
    const char *entry_path);
PLATFORM_DISK_API int platform_disk_inspect_path_json_alloc(const char *platform_name, const char *path,
    char **out_json);
PLATFORM_DISK_API int platform_disk_extract_entry_path_bytes_alloc(const char *platform_name, const char *path,
    const char *entry_path, unsigned char **out_data, size_t *out_size, char **out_error);
PLATFORM_DISK_API void platform_disk_free_text(char *text);
PLATFORM_DISK_API void platform_disk_free_bytes(unsigned char *data);

#endif
