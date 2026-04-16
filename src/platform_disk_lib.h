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

PLATFORM_DISK_API PlatformDiskTextResult platform_disk_inspect_path_json(const char *platform_name, const char *path);
PLATFORM_DISK_API PlatformDiskTextResult platform_disk_inspect_buffer_json(const char *platform_name,
    const unsigned char *data, size_t size);
PLATFORM_DISK_API void platform_disk_free_json(char *json);

#endif
