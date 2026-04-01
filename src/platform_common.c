#include "platform_common.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void m68k_platform_set_error(char *error_buf, size_t error_buf_size, const char *message) {
  if (error_buf != NULL && error_buf_size != 0U) snprintf(error_buf, error_buf_size, "%s", message);
}

void m68k_platform_set_errorf(char *error_buf, size_t error_buf_size, const char *fmt, ...) {
  if (error_buf != NULL && error_buf_size != 0U) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(error_buf, error_buf_size, fmt, args);
    va_end(args);
  }
}

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
