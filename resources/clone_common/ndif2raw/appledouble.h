#pragma once

#include <stdint.h>
#include <stdlib.h>

#if __has_include(<CoreServices/CoreServices.h>)
#include <CoreServices/CoreServices.h>
#else /* __has_include(<CoreServices/CoreServices.h>) */
typedef uint32_t ResType;  // 4-byte resource type identifier
typedef int16_t ResID;     // Resource ID number
#endif /* __has_include(<CoreServices/CoreServices.h>) */

uint8_t *read_applesingle_data(const char *const filename, size_t *const size_out);
uint8_t *read_applesingle_resource(const char *const filename, const ResType type, const ResID id, size_t *const size_out);

/**
 * @brief Read a resource from a well-known location of an AppleDouble file.
 *
 * @param filename The name of the file to read from.
 * @param type The resource type to read.
 * @param id The resource ID to read.
 * @param size_out Pointer to store the size of the resource data.
 * @return Pointer to the resource data, or NULL if not found or an error occurred.
 */
uint8_t *read_appledouble_resource(const char *const filename, const ResType type, const ResID id, size_t *const size_out);
