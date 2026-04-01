#include "json_builder.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int json_builder_reserve(JsonBuilder *builder, size_t extra) {
    size_t needed = builder->size + extra + 1U;
    size_t next_capacity;
    char *grown;
    if (needed <= builder->capacity) return 0;
    next_capacity = (builder->capacity == 0U) ? 256U : builder->capacity * 2U;
    while (next_capacity < needed) next_capacity *= 2U;
    grown = (char *)realloc(builder->data, next_capacity);
    if (grown == NULL) return -1;
    builder->data = grown;
    builder->capacity = next_capacity;
    return 0;
}

int json_builder_append(JsonBuilder *builder, const char *text) {
    size_t length = strlen(text);
    if (json_builder_reserve(builder, length) != 0) return -1;
    memcpy(builder->data + builder->size, text, length);
    builder->size += length;
    builder->data[builder->size] = '\0';
    return 0;
}

int json_builder_appendf(JsonBuilder *builder, const char *fmt, ...) {
    va_list args;
    va_list copy;
    int written;
    va_start(args, fmt);
    va_copy(copy, args);
    written = vsnprintf(NULL, 0, fmt, copy);
    va_end(copy);
    if (written < 0) {
        va_end(args);
        return -1;
    }
    if (json_builder_reserve(builder, (size_t)written) != 0) {
        va_end(args);
        return -1;
    }
    vsnprintf(builder->data + builder->size, builder->capacity - builder->size, fmt, args);
    builder->size += (size_t)written;
    va_end(args);
    return 0;
}

int json_builder_append_json_string(JsonBuilder *builder, const char *text) {
    const unsigned char *p = (const unsigned char *)text;
    if (json_builder_append(builder, "\"") != 0) return -1;
    while (*p != 0U) {
        if (*p == '\\' || *p == '"') {
            if (json_builder_appendf(builder, "\\%c", *p) != 0) return -1;
        } else if (*p < 0x20U) {
            if (json_builder_appendf(builder, "\\u%04X", *p) != 0) return -1;
        } else {
            if (json_builder_reserve(builder, 1U) != 0) return -1;
            builder->data[builder->size] = (char)*p;
            builder->size += 1U;
            builder->data[builder->size] = '\0';
        }
        ++p;
    }
    return json_builder_append(builder, "\"");
}

void json_builder_free(JsonBuilder *builder) {
    free(builder->data);
    builder->data = NULL;
    builder->size = 0U;
    builder->capacity = 0U;
}
