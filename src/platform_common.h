#ifndef PLATFORM_COMMON_H
#define PLATFORM_COMMON_H

#include <stddef.h>

void m68k_platform_set_error(char *error_buf, size_t error_buf_size, const char *message);
void m68k_platform_set_errorf(char *error_buf, size_t error_buf_size, const char *fmt, ...);
char *m68k_platform_dup_string(const char *text);
int m68k_platform_join_path(const char *base, const char *name, char **out_path);

#endif
