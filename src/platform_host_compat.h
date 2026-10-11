#ifndef PLATFORM_HOST_COMPAT_H
#define PLATFORM_HOST_COMPAT_H
#ifndef _WIN32
#include <strings.h>
#include <stdlib.h>
static inline int _putenv_s(const char *name, const char *value) {
  return value[0] == '\0' ? unsetenv(name) : setenv(name, value, 1);
}
#define _stricmp strcasecmp
#define _strnicmp strncasecmp
#endif
#endif
