#include "platform_name_table.h"

#include <string.h>

uint16_t platform_name_id_from_table(const char *const *names, size_t count, const char *name) {
  size_t index;
  if (count == 0U) return 0U;
  if (names == NULL || name == NULL || name[0] == '\0') return (uint16_t)(count - 1U);
  for (index = 0U; index + 1U < count; ++index) {
    if (names[index] != NULL && strcmp(names[index], name) == 0) return (uint16_t)index;
  }
  return (uint16_t)(count - 1U);
}
