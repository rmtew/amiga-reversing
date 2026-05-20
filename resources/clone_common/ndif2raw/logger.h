#pragma once

#include <stdio.h>
#include <stdbool.h>

extern bool logging_enabled;

void log_message(const char *format, ...);
