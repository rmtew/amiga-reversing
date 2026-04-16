#include "platform_common.h"

#include <stdlib.h>
#include <string.h>

char *m68k_platform_dup_string(const char *text) {
  if (text == NULL) return NULL;
  size_t length = strlen(text) + 1U;
  char *copy = (char *)malloc(length);
  if (copy == NULL) return NULL;
  memcpy(copy, text, length);
  return copy;
}

int m68k_platform_join_path(const char *base, const char *name, char **out_path) {
  size_t base_len = strlen(base);
  size_t name_len = strlen(name);
  size_t total = base_len + name_len + (base_len != 0U ? 2U : 1U);
  char *path = (char *)malloc(total);
  if (path == NULL) return -1;
  if (base_len != 0U) {
    memcpy(path, base, base_len);
    path[base_len] = '/';
    memcpy(path + base_len + 1U, name, name_len + 1U);
  } else {
    memcpy(path, name, name_len + 1U);
  }
  *out_path = path;
  return 0;
}
