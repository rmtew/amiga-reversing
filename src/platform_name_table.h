#ifndef PLATFORM_NAME_TABLE_H
#define PLATFORM_NAME_TABLE_H

#include <stddef.h>
#include <stdint.h>

uint16_t platform_name_id_from_table(const char *const *names, size_t count, const char *name);

#endif
