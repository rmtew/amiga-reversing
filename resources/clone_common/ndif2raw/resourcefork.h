#pragma once

#include <stdint.h>
#include <stdlib.h>

#if __has_include(<CoreServices/CoreServices.h>)
#include <CoreServices/CoreServices.h>
#else /* __has_include(<CoreServices/CoreServices.h>) */
typedef uint32_t ResType;  // 4-byte resource type identifier
typedef int16_t ResID;     // Resource ID number
#endif /* __has_include(<CoreServices/CoreServices.h>) */

uint8_t *read_resource_fork(const char *const filename, const ResType type, const ResID id, size_t *const size_out);
