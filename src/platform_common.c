#include "platform_common.h"

#include <stdio.h>
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

int platform_amiga_format_global_base_slot_label(size_t section_index, char width_suffix, const char *base_name,
    char *buf, size_t buf_size) {
  const char *tail = base_name;
  size_t tail_index = 0U;
  char normalized[64];
  int written;
  if (buf == NULL || buf_size == 0U || base_name == NULL || base_name[0] == '\0') return 0;
  if (strcmp(base_name, "SysBase") == 0) tail = "ExecBase";
  while (tail[0] == '_' || tail[0] == '.') ++tail;
  while (tail[tail_index] != '\0' && tail_index + 1U < sizeof(normalized)) {
    char ch = tail[tail_index];
    normalized[tail_index] = (ch == '.' || ch == '-' || ch == ' ') ? '_' : ch;
    ++tail_index;
  }
  normalized[tail_index] = '\0';
  written = snprintf(buf, buf_size, "h%ud%c_%s", (unsigned)section_index, width_suffix, normalized);
  return written > 0 && (size_t)written < buf_size;
}

int platform_amiga_format_app_base_slot_name(const char *base_name, char *buf, size_t buf_size) {
  int written;
  if (buf == NULL || buf_size == 0U || base_name == NULL || base_name[0] == '\0') return 0;
  if (strcmp(base_name, "SysBase") == 0) {
    written = snprintf(buf, buf_size, "app_ExecBase");
  } else {
    written = snprintf(buf, buf_size, "app_%s", base_name);
  }
  return written > 0 && (size_t)written < buf_size;
}
