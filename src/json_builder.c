#include "json_builder.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define JSON_BUILDER_CHUNK_SIZE 1024U
#define JSON_BUILDER_FORMAT_STACK_SIZE 256U

typedef struct JsonBuilderChunk {
    char *data;
    size_t used;
    size_t capacity;
    struct JsonBuilderChunk *next;
} JsonBuilderChunk;

struct JsonBuilderState {
    JsonBuilderChunk *head;
    JsonBuilderChunk *tail;
};

int json_builder_create(JsonBuilder *builder) {
    if (builder == NULL) return -1;
    memset(builder, 0, sizeof(*builder));
    builder->arena = arena_create(JSON_BUILDER_CHUNK_SIZE);
    if (builder->arena == NULL) return -1;
    builder->state = (JsonBuilderState *)arena_calloc(builder->arena, 1U, sizeof(*builder->state));
    if (builder->state == NULL) {
        arena_destroy(builder->arena);
        memset(builder, 0, sizeof(*builder));
        return -1;
    }
    return 0;
}

static JsonBuilderChunk *append_chunk(JsonBuilder *builder, size_t minimum_capacity) {
    JsonBuilderChunk *chunk;
    size_t capacity = JSON_BUILDER_CHUNK_SIZE;
    Arena *arena;
    if (builder == NULL || builder->arena == NULL || builder->state == NULL) return NULL;
    arena = builder->arena;
    if (capacity < minimum_capacity) capacity = minimum_capacity;
    chunk = (JsonBuilderChunk *)arena_alloc(arena, sizeof(*chunk));
    if (chunk == NULL) return NULL;
    chunk->data = (char *)arena_alloc(arena, capacity);
    if (chunk->data == NULL) return NULL;
    chunk->used = 0U;
    chunk->capacity = capacity;
    chunk->next = NULL;
    if (builder->state->tail != NULL) builder->state->tail->next = chunk;
    else builder->state->head = chunk;
    builder->state->tail = chunk;
    return chunk;
}

static int append_bytes(JsonBuilder *builder, const char *data, size_t length) {
    JsonBuilderChunk *chunk;
    size_t remaining = length;
    const char *cursor = data;
    if (builder == NULL || builder->state == NULL) return -1;
    if (length == 0U) return 0;
    chunk = builder->state->tail;
    while (remaining != 0U) {
        size_t available;
        size_t to_copy;
        if (chunk == NULL || chunk->used == chunk->capacity) {
            chunk = append_chunk(builder, remaining);
            if (chunk == NULL) return -1;
        }
        available = chunk->capacity - chunk->used;
        to_copy = (remaining < available) ? remaining : available;
        memcpy(chunk->data + chunk->used, cursor, to_copy);
        chunk->used += to_copy;
        builder->size += to_copy;
        cursor += to_copy;
        remaining -= to_copy;
    }
    return 0;
}

static int json_builder_appendfv(JsonBuilder *builder, const char *fmt, va_list args) {
    char stack_buffer[JSON_BUILDER_FORMAT_STACK_SIZE];
    char *heap_buffer = NULL;
    char *buffer = stack_buffer;
    M68kAllocator heap_allocator = m68k_allocator_heap();
    va_list copy;
    int written;
    size_t length;
    va_copy(copy, args);
    written = vsnprintf(stack_buffer, sizeof(stack_buffer), fmt, copy);
    va_end(copy);
    if (written < 0) return -1;
    length = (size_t)written;
    if (length >= sizeof(stack_buffer)) {
        heap_buffer = (char *)m68k_allocator_alloc(heap_allocator, length + 1U);
        if (heap_buffer == NULL) return -1;
        va_copy(copy, args);
        written = vsnprintf(heap_buffer, length + 1U, fmt, copy);
        va_end(copy);
        if (written < 0) {
            m68k_allocator_free(heap_allocator, heap_buffer);
            return -1;
        }
        buffer = heap_buffer;
    }
    if (append_bytes(builder, buffer, length) != 0) {
        m68k_allocator_free(heap_allocator, heap_buffer);
        return -1;
    }
    m68k_allocator_free(heap_allocator, heap_buffer);
    return 0;
}

int json_builder_append(JsonBuilder *builder, const char *text) {
    return append_bytes(builder, text, strlen(text));
}

int json_builder_append_builder(JsonBuilder *builder, const JsonBuilder *source) {
    const JsonBuilderChunk *chunk;
    if (builder == NULL || source == NULL || source->state == NULL) return -1;
    for (chunk = source->state->head; chunk != NULL; chunk = chunk->next) {
        if (append_bytes(builder, chunk->data, chunk->used) != 0) return -1;
    }
    return 0;
}

int json_builder_append_char(JsonBuilder *builder, char ch) {
    return append_bytes(builder, &ch, 1U);
}

int json_builder_appendf(JsonBuilder *builder, const char *fmt, ...) {
    va_list args;
    int result;
    va_start(args, fmt);
    result = json_builder_appendfv(builder, fmt, args);
    va_end(args);
    return result;
}

int json_builder_append_json_string(JsonBuilder *builder, const char *text) {
    const unsigned char *p = (const unsigned char *)text;
    const unsigned char *span_start = p;
    if (json_builder_append(builder, "\"") != 0) return -1;
    while (*p != 0U) {
        if (*p == '\\' || *p == '"') {
            char escaped[2];
            if (p > span_start && append_bytes(builder, (const char *)span_start, (size_t)(p - span_start)) != 0)
                return -1;
            escaped[0] = '\\';
            escaped[1] = (char)*p;
            if (append_bytes(builder, escaped, sizeof(escaped)) != 0) return -1;
            ++p;
            span_start = p;
            continue;
        } else if (*p < 0x20U) {
            if (p > span_start && append_bytes(builder, (const char *)span_start, (size_t)(p - span_start)) != 0)
                return -1;
            if (json_builder_appendf(builder, "\\u%04X", *p) != 0) return -1;
            ++p;
            span_start = p;
            continue;
        }
        ++p;
    }
    if (p > span_start && append_bytes(builder, (const char *)span_start, (size_t)(p - span_start)) != 0) return -1;
    return json_builder_append(builder, "\"");
}

static char *json_builder_copy_text(JsonBuilder *builder, char *data) {
    JsonBuilderChunk *chunk;
    size_t offset = 0U;
    if (builder == NULL) return NULL;
    if (data == NULL) return NULL;
    for (chunk = builder->state != NULL ? builder->state->head : NULL; chunk != NULL; chunk = chunk->next) {
        if (chunk->used != 0U) {
            memcpy(data + offset, chunk->data, chunk->used);
            offset += chunk->used;
        }
    }
    data[offset] = '\0';
    return data;
}

char *json_builder_build(JsonBuilder *builder) {
    M68kAllocator heap_allocator = m68k_allocator_heap();
    if (builder == NULL || builder->size == (size_t)-1) return NULL;
    return json_builder_copy_text(builder, (char *)m68k_allocator_alloc(heap_allocator, builder->size + 1U));
}

char *json_builder_build_arena(JsonBuilder *builder, Arena *arena) {
    M68kAllocator arena_allocator = m68k_allocator_arena(arena);
    if (builder == NULL || arena == NULL || builder->size == (size_t)-1) return NULL;
    return json_builder_copy_text(builder, (char *)m68k_allocator_alloc(arena_allocator, builder->size + 1U));
}

void json_builder_destroy(JsonBuilder *builder) {
    if (builder == NULL) return;
    arena_destroy(builder->arena);
    builder->size = 0U;
    builder->arena = NULL;
    builder->state = NULL;
}
