#include "logger.h"
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>

bool logging_enabled = false;

void log_message(const char *format, ...) {
    if (!logging_enabled) {
        return;
    }

    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
}
