/*
 * appledouble.c
 * author: Eric Helgeson <erichelgeson@gmail.com>
 * date: April 2025
 */

#include "appledouble.h"
#include "logger.h"
#include <assert.h>
#include <ctype.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

#define DATA_FORK_ID 1
#define RESOURCE_FORK_ID 2
#define AS_MAGIC_AS 0x00051600  // AppleSingle magic number
#define AS_MAGIC_AD 0x00051607  // AppleDouble magic number

// Resource header structure
typedef struct {
    uint32_t data_offset;     // Offset to resource data from start of resource fork
    uint32_t map_offset;      // Offset to resource map from start of resource fork
    uint32_t data_length;     // Length of resource data section
    uint32_t map_length;      // Length of resource map section
} ResourceHeader;

// Resource type entry
typedef struct {
    ResType type;             // 4-byte resource type
    uint16_t count;           // Number of resources of this type - 1
    uint16_t type_offset;     // Offset from start of type list to resource list
} ResourceType;

// Resource reference entry
typedef struct {
    ResID id;                 // Resource ID
    uint16_t name_offset;     // Offset from start of name list or -1 if none
    uint8_t attributes;       // Resource attributes
    uint32_t data_offset;     // Offset from start of data to this resource's data
    uint32_t handle;          // Reserved for handle to resource
} ResourceRef;

// Entry in the AppleSingle/AppleDouble file
typedef struct {
    uint32_t id;
    uint32_t offset;
    uint32_t size;
} Entry;

// Main AppleSingle/AppleDouble handler structure
typedef struct {
    FILE *file;
    uint32_t magic;
    uint32_t version;
    unsigned int entry_count;
    Entry *entries;
} AppleSingleFile;

static int read_as_header(AppleSingleFile *const as_file);

// Helper functions for reading/writing big-endian values
static uint8_t read_uint8(const void *buffer, unsigned int offset) {
    const uint8_t *bytes = (const uint8_t *)buffer + offset;
    return bytes[0];
}

static uint16_t read_uint16_be(const void *buffer, unsigned int offset) {
    const uint8_t *bytes = (const uint8_t *)buffer + offset;
    return (bytes[0] << 8) | bytes[1];
}

static uint32_t read_uint32_be(const void *buffer, unsigned int offset) {
    const uint8_t *bytes = (const uint8_t *)buffer + offset;
    return (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3];
}

static void write_uint8(void *buffer, unsigned int offset, uint8_t value) {
    uint8_t *bytes = (uint8_t *)buffer + offset;
    bytes[0] = value;
}

static void write_uint16_be(void *buffer, unsigned int offset, uint16_t value) {
    uint8_t *bytes = (uint8_t *)buffer + offset;
    bytes[0] = (value >> 8) & 0xFF;
    bytes[1] = value & 0xFF;
}

static void write_uint32_be(void *buffer, unsigned int offset, uint32_t value) {
    uint8_t *bytes = (uint8_t *)buffer + offset;
    bytes[0] = (value >> 24) & 0xFF;
    bytes[1] = (value >> 16) & 0xFF;
    bytes[2] = (value >> 8) & 0xFF;
    bytes[3] = value & 0xFF;
}

// Free resources used by an AppleSingleFile
static void free_as_file(AppleSingleFile *const as_file) {
    if (as_file) {
        free(as_file->entries);
        as_file->entries = NULL;
        free(as_file);
    }
}

// Create a new AppleSingleFile structure
static AppleSingleFile *create_as_file(FILE *const file) {
    assert(file);

    AppleSingleFile *const as_file = malloc(sizeof (AppleSingleFile));
    assert(as_file);

    as_file->file = file;
    as_file->magic = 0;
    as_file->version = 0;
    as_file->entry_count = 0;
    as_file->entries = NULL;

    if (read_as_header(as_file)) {
        free_as_file(as_file);
        return NULL;
    }

    return as_file;
}

// Helper function to read data from file at specific offset
static int read_at_offset(FILE *const file, void *const buffer,
                          const size_t offset, const size_t count) {
    assert(file);
    assert(buffer);

    if (fseek(file, (long)offset, SEEK_SET) != 0) {
        return 1;
    }

    if (fread(buffer, count, 1, file) != 1) {
        return 1;
    }

    return 0;
}

// Add a new entry to the AppleSingleFile
static int add_entry(AppleSingleFile *const as_file, const uint32_t id,
                     const uint32_t size, const uint32_t offset) {
    assert(as_file);

    // Check if entry with this ID already exists
    for (unsigned int i = 0; i < as_file->entry_count; i++) {
        if (as_file->entries[i].id == id) {
            return 1;  // Entry already exists
        }
    }

    // Resize entries array
    Entry *const new_entries = realloc(as_file->entries, (as_file->entry_count + 1) * sizeof (Entry));
    assert(new_entries);

    as_file->entries = new_entries;
    as_file->entry_count++;

    // Set new entry values
    Entry *const entry = &as_file->entries[as_file->entry_count - 1];
    entry->id = id;
    entry->offset = offset;
    entry->size = size;

    return 0;
}

// Read and parse the AppleSingle/AppleDouble header
static int read_as_header(AppleSingleFile *const as_file) {
    assert(as_file);

    // Reset entries if they exist
    if (as_file->entry_count > 0) {
        free(as_file->entries);
        as_file->entry_count = 0;
        as_file->entries = NULL;
    }

    // Read header data
    uint8_t header[26];
    if (read_at_offset(as_file->file, header, 0, sizeof header)) {
        return 1;
    }

    // Check magic number
    as_file->magic = read_uint32_be(header, 0);
    if (as_file->magic != AS_MAGIC_AS && as_file->magic != AS_MAGIC_AD) {
        return 1;
    }

    // Check version
    as_file->version = read_uint32_be(header, 4);
    if (as_file->version != 0x00010000 && as_file->version != 0x00020000) {
        return 1;
    }

    // Read entries
    const uint16_t entry_count = read_uint16_be(header, 24);

    for (uint16_t i = 0; i < entry_count; i++) {
        uint8_t entry_data[12];
        if (read_at_offset(as_file->file, entry_data, 26 + 12 * i, sizeof entry_data)) {
            return 1;
        }

        const uint32_t id = read_uint32_be(entry_data, 0);
        const uint32_t offset = read_uint32_be(entry_data, 4);
        const uint32_t size = read_uint32_be(entry_data, 8);

        log_message("* Entry %u: id=%u, offset=%u, size=%u\n", i, id, offset, size);

        if (add_entry(as_file, id, size, offset)) {
            return 1;
        }
    }

    // Print file information
    log_message("magic: %08X\n", as_file->magic);
    log_message("version: %08X\n", as_file->version);
    log_message("entry count: %u\n", as_file->entry_count);
    log_message("entries:\n");

    if (logging_enabled) {
        // Print and display entry data
        for (unsigned int i = 0; i < as_file->entry_count; i++) {
            log_message("Entry %u: id=%u, offset=%u, size=%u\n",
                   i, as_file->entries[i].id, as_file->entries[i].offset, as_file->entries[i].size);

            // Read and print the entry data
            uint8_t *const data = malloc(as_file->entries[i].size);
            assert(data);

            if (read_at_offset(as_file->file, data, as_file->entries[i].offset, as_file->entries[i].size)) {
                fprintf(stderr, "Failed to read entry data\n");
                free(data);
                return 1;
            }

            log_message("Data: ");
            for (uint32_t j = 0; j < as_file->entries[i].size; j++) {
                // Print readable ASCII characters or a dot for non-printable
                if (isprint((unsigned char)data[j])) {
                    log_message("%c", data[j]);
                } else {
                    log_message(".");
                }
            }
            log_message("\n");
            free(data);
        }
    }

    return 0;
}

// Find an entry with the given ID
static Entry *find_entry(const AppleSingleFile *const as_file, const uint32_t id) {
    assert(as_file);

    for (unsigned int i = 0; i < as_file->entry_count; i++) {
        if (as_file->entries[i].id == id) {
            return &as_file->entries[i];
        }
    }

    return NULL;
}

// Convert a resource type to a sanitized printable string.
static const char *fourcc_str(const ResType type) {
    static char buf[5];

    buf[0] = (char)((type >> 24) & 0xFF);
    buf[1] = (char)((type >> 16) & 0xFF);
    buf[2] = (char)((type >> 8) & 0xFF);
    buf[3] = (char)(type & 0xFF);
    buf[4] = '\0';

    for (int i = 0; i < 4; i++) {
        if (!isprint((unsigned char)buf[i])) {
            buf[i] = '.';
        }
    }

    return buf;
}

// Read the resource fork header from an AppleSingle/AppleDouble file
static int read_resource_header(const AppleSingleFile *const as_file,
                                ResourceHeader *const header, size_t *const fork_offset) {
    assert(as_file);

    const Entry *resource_fork = find_entry(as_file, RESOURCE_FORK_ID);
    if (!resource_fork) {
        fprintf(stderr, "ERROR: no resource fork in AppleSingle/AppleDouble file\n");
        return 1;
    }

    uint8_t buffer[16];
    if (read_at_offset(as_file->file, buffer, resource_fork->offset, sizeof buffer)) {
        fprintf(stderr, "ERROR: failed to read resource header\n");
        return 1;
    }

    header->data_offset = read_uint32_be(buffer, 0);
    header->map_offset = read_uint32_be(buffer, 4);
    header->data_length = read_uint32_be(buffer, 8);
    header->map_length = read_uint32_be(buffer, 12);
    *fork_offset = resource_fork->offset;

    return 0;
}

// Find a resource by type and ID
static int find_resource(const AppleSingleFile *as_file, const ResType type, const ResID id,
                         size_t *const offset, uint32_t *const size) {
    assert(as_file);

    ResourceHeader header;
    size_t fork_base;
    if (read_resource_header(as_file, &header, &fork_base)) {
        return 1;
    }

    // Read the resource map header
    uint8_t map_header[28];
    if (read_at_offset(as_file->file, map_header,
                       fork_base + header.map_offset, sizeof map_header)) {
        return 1;
    }

    // Skip resource map header and attributes to get to the type list offset
    uint16_t type_list_offset = read_uint16_be(map_header, 24);
    // uint16_t name_list_offset = read_uint16_be(map_header, 26);

    // Read the type count
    uint8_t type_count_buffer[2];
    if (read_at_offset(as_file->file, type_count_buffer,
                       fork_base + header.map_offset + type_list_offset,
                       sizeof type_count_buffer)) {
        return 1;
    }

    // Number of types is stored as count+1
    const uint16_t type_count = read_uint16_be(type_count_buffer, 0) + 1;

    // Loop through each type to find our target
    for (uint16_t i = 0; i < type_count; i++) {
        uint8_t type_entry_buffer[8];
        size_t type_entry_offset = fork_base + header.map_offset +
                                   type_list_offset + 2U + ((size_t)i * 8U);

        if (read_at_offset(as_file->file, type_entry_buffer,
                           type_entry_offset, sizeof type_entry_buffer)) {
            return 1;
        }

        ResourceType type_entry;
        type_entry.type = read_uint32_be(type_entry_buffer, 0);
        type_entry.count = read_uint16_be(type_entry_buffer, 4) + 1;
        type_entry.type_offset = read_uint16_be(type_entry_buffer, 6);

        // Check if this is the type we're looking for
        if (type_entry.type == type) {
            // Calculate resource list offset
            size_t ref_list_offset = fork_base + header.map_offset +
                                     type_list_offset + type_entry.type_offset;

            // Loop through each resource of this type
            for (uint16_t j = 0; j < type_entry.count; j++) {
                uint8_t ref_buffer[12];
                if (read_at_offset(as_file->file, ref_buffer,
                                   ref_list_offset + ((size_t)j * 12U), sizeof ref_buffer)) {
                    return 1;
                }

                ResourceRef ref;
                ref.id = (ResID)read_uint16_be(ref_buffer, 0);
                ref.name_offset = read_uint16_be(ref_buffer, 2);
                ref.attributes = read_uint8(ref_buffer, 4);
                // The data offset is 3 bytes stored at offset 5
                ref.data_offset = (ref_buffer[5] << 16) |
                                  (ref_buffer[6] << 8) |
                                  (ref_buffer[7]);

                // Check if this is the ID we're looking for
                if (ref.id == id) {
                    // Found our resource! Get the size and offset
                    uint8_t res_data_header[4];
                    const size_t res_data_offset = fork_base + header.data_offset + ref.data_offset;
                    if (read_at_offset(as_file->file, res_data_header,
                                       res_data_offset, sizeof res_data_header)) {
                        return 1;
                    }

                    // First 4 bytes contain the resource data size
                    const uint32_t res_size = read_uint32_be(res_data_header, 0);

                    // Set the return values
                    *offset = res_data_offset + 4U; // Skip size bytes
                    *size = res_size;

                    return 0; // Success
                }
            }
        }
    }

    // Resource not found
    return 1;
}

// Get resource data by type and ID
static void *get_resource(const AppleSingleFile *const as_file, const ResType type, const ResID id, size_t *const size_out) {
    assert(as_file);

    size_t offset;
    uint32_t res_size;
    if (find_resource(as_file, type, id, &offset, &res_size)) {
        return NULL;
    }

    void *const data = malloc(res_size);
    assert(data);

    // Read the resource data
    if (read_at_offset(as_file->file, data, offset, res_size)) {
        free(data);
        return NULL;
    }

    if (size_out) *size_out = res_size;
    return data;
}

static void print_resource_info(const AppleSingleFile *const as_file) {
    assert(as_file);

    ResourceHeader header;
    size_t fork_base;
    if (read_resource_header(as_file, &header, &fork_base)) {
        fprintf(stderr, "Couldn't read resource header\n");
        return;
    }

    log_message("Resource fork information:\n");
    log_message("  Data offset: %u\n", header.data_offset);
    log_message("  Map offset: %u\n", header.map_offset);
    log_message("  Data length: %u\n", header.data_length);
    log_message("  Map length: %u\n", header.map_length);

    // Read map header
    const size_t map_base = fork_base + header.map_offset;
    uint8_t map_header[28];
    if (read_at_offset(as_file->file, map_header, map_base, sizeof map_header)) {
        return;
    }

    const uint16_t type_list_offset = read_uint16_be(map_header, 24);

    // Read type count
    uint8_t type_count_buf[2];
    if (read_at_offset(as_file->file, type_count_buf,
                       map_base + type_list_offset, sizeof type_count_buf)) {
        return;
    }

    const uint16_t type_count = read_uint16_be(type_count_buf, 0) + 1;
    log_message("Resource types: %u\n", type_count);

    // Loop through types
    for (uint16_t i = 0; i < type_count; i++) {
        uint8_t type_entry_buf[8];
        const size_t type_entry_offset = map_base + type_list_offset + 2U + ((size_t)i * 8U);
        if (read_at_offset(as_file->file, type_entry_buf,
                           type_entry_offset, sizeof type_entry_buf)) {
            continue;
        }

        const ResType res_type = read_uint32_be(type_entry_buf, 0);
        const uint16_t res_count = read_uint16_be(type_entry_buf, 4) + 1;
        const uint16_t type_offset = read_uint16_be(type_entry_buf, 6);

        log_message("Type '%s' (%08X) - %u resources\n", fourcc_str(res_type), res_type, res_count);

        // Calculate reference list offset for this type
        const size_t ref_list_offset = map_base + type_list_offset + type_offset;

        // Loop through resources of this type
        for (uint16_t j = 0; j < res_count; j++) {
            uint8_t ref_buf[12];
            if (read_at_offset(as_file->file, ref_buf,
                               ref_list_offset + (j * 12), sizeof ref_buf)) {
                continue;
            }

            const ResID res_id = (int16_t)read_uint16_be(ref_buf, 0);
            const uint16_t name_offset = read_uint16_be(ref_buf, 2);
            const uint8_t attributes = ref_buf[4];
            const uint32_t data_offset = (ref_buf[5] << 16) | (ref_buf[6] << 8) | ref_buf[7];
            const uint16_t name_list_offset = read_uint16_be(map_header, 26);

            log_message("  ID: %d, Attributes: %02X, Data offset: %u",
                   res_id, attributes, data_offset);

            // Print resource name if available
            if (name_offset != 0xFFFF) {
                uint8_t name_length;
                if (read_at_offset(as_file->file, &name_length,
                                   map_base + name_list_offset + name_offset, sizeof name_length) == 0) {
                    char name[UINT8_MAX + 1];
                    if (read_at_offset(as_file->file, name,
                                       map_base + name_list_offset + name_offset + 1, name_length) == 0) {
                        name[name_length] = '\0'; // Null-terminate the name
                        log_message(" (name: %s)", name);
                    }
                }
            }

            log_message("\n");
        }
    }
}

uint8_t *read_applesingle_data(const char *const filename, size_t *const size_out) {
    FILE *const file = fopen(filename, "rb");

    if (!file) {
        perror("fopen");
        return NULL;
    }

    AppleSingleFile *const as_file = create_as_file(file);

    if (!as_file) {
        fprintf(stderr, "ERROR: could not read AppleSingle/AppleDouble header\n");
        fclose(file);
        return NULL;
    }

    const Entry *const data_fork = find_entry(as_file, DATA_FORK_ID);

    if (!data_fork) {
        fprintf(stderr, "ERROR: no data fork in purported AppleSingle file\n");
        free_as_file(as_file);
        fclose(file);
        return NULL;
    }

    uint8_t *const data = malloc(data_fork->size);
    assert(data);

    read_at_offset(file, data, data_fork->offset, data_fork->size);
    if (size_out) *size_out = data_fork->size;

    free_as_file(as_file);
    fclose(file);

    return data;
}

static uint8_t *_read_applesingle_resource(FILE *const file, const ResType type, const ResID id, size_t *const size_out) {
    assert(file);
    AppleSingleFile *const as_file = create_as_file(file);

    if (!as_file) {
        fprintf(stderr, "ERROR: could not read AppleSingle/AppleDouble header\n");
        return NULL;
    }

    if (logging_enabled) {
        print_resource_info(as_file);
    }

    size_t size;
    uint8_t *const data = get_resource(as_file, type, id, &size);

    if (data) {
        log_message("Found resource with type '%s' and ID %u; size: %zu bytes\n",
           fourcc_str(type), id, size);

        if (size_out) *size_out = size;
    } else {
        fprintf(stderr, "ERROR: resource with type '%s' and ID %u not found\n",
           fourcc_str(type), id);
    }

    free_as_file(as_file);
    return data;
}

uint8_t *read_applesingle_resource(const char *const filename, const ResType type, const ResID id, size_t *const size_out) {
    FILE *const file = fopen(filename, "rb");

    if (!file) {
        perror("fopen");
        return NULL;
    }

    uint8_t *const data = _read_applesingle_resource(file, type, id, size_out);
    fclose(file);

    return data;
}

uint8_t *read_appledouble_resource(const char *const filename, const ResType type, const ResID id, size_t *const size_out) {
    char rsrc_filename[PATH_MAX];
    const char *const slash = strrchr(filename, '/');
    const char *const basename = slash ? slash + 1 : filename;
    const size_t dir_len = slash ? (size_t)(slash - filename + 1) : 0;

    snprintf(rsrc_filename, sizeof rsrc_filename, "%.*s._%s", (int)dir_len, filename, basename);
    FILE *file = fopen(rsrc_filename, "rb");

    if (!file) {
        snprintf(rsrc_filename, sizeof rsrc_filename, "%s.rsrc", filename);
        file = fopen(rsrc_filename, "rb");
    }

    if (!file) {
        fprintf(stderr, "ERROR: failed to find a AppleDouble sidecar file\n");
        return NULL;
    }

    uint8_t *const data = _read_applesingle_resource(file, type, id, size_out);
    fclose(file);

    return data;
}
