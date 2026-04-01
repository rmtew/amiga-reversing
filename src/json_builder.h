#ifndef JSON_BUILDER_H
#define JSON_BUILDER_H

#include <stddef.h>

typedef struct JsonBuilder {
    char *data;
    size_t size;
    size_t capacity;
} JsonBuilder;

int json_builder_reserve(JsonBuilder *builder, size_t extra);
int json_builder_append(JsonBuilder *builder, const char *text);
int json_builder_appendf(JsonBuilder *builder, const char *fmt, ...);
int json_builder_append_json_string(JsonBuilder *builder, const char *text);
void json_builder_free(JsonBuilder *builder);

#endif
