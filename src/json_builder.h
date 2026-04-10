#ifndef JSON_BUILDER_H
#define JSON_BUILDER_H

#include "util_arena.h"

#include <stddef.h>

typedef struct JsonBuilderState JsonBuilderState;

typedef struct JsonBuilder {
    size_t size;
    Arena *arena;
    JsonBuilderState *state;
} JsonBuilder;

int json_builder_create(JsonBuilder *builder);
int json_builder_append(JsonBuilder *builder, const char *text);
int json_builder_appendf(JsonBuilder *builder, const char *fmt, ...);
int json_builder_append_char(JsonBuilder *builder, char ch);
int json_builder_append_json_string(JsonBuilder *builder, const char *text);
char *json_builder_build(JsonBuilder *builder);
void json_builder_destroy(JsonBuilder *builder);

#endif
