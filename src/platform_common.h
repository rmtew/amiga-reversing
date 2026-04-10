#ifndef PLATFORM_COMMON_H
#define PLATFORM_COMMON_H

#include <stdint.h>
#include <stddef.h>

static inline uint16_t m68k_read_u16be(const uint8_t *data) {
  return (uint16_t)(((uint16_t)data[0] << 8) | (uint16_t)data[1]);
}

static inline uint32_t m68k_read_u32be(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

void m68k_platform_set_error(char *error_buf, size_t error_buf_size, const char *message);
void m68k_platform_set_errorf(char *error_buf, size_t error_buf_size, const char *fmt, ...);
char *m68k_platform_dup_string(const char *text);
int m68k_platform_join_path(const char *base, const char *name, char **out_path);

#endif
