#ifndef PLATFORM_DISK_LIB_H
#define PLATFORM_DISK_LIB_H

#include <stddef.h>

#ifdef _WIN32
#define PLATFORM_DISK_API __declspec(dllexport)
#else
#define PLATFORM_DISK_API
#endif

PLATFORM_DISK_API int platform_disk_inspect_path_json(const char *platform_name, const char *path, char **out_json,
    char *error_buf, size_t error_buf_size);
PLATFORM_DISK_API int platform_disk_inspect_buffer_json(const char *platform_name, const unsigned char *data,
    size_t size, char **out_json, char *error_buf, size_t error_buf_size);
PLATFORM_DISK_API void platform_disk_free_json(char *json);

#endif
