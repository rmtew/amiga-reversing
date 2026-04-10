#include "platform_binary_io.h"

#include <stdlib.h>
#include <string.h>

#define M68K_WRITER_CHUNK_SIZE 1024U

typedef struct M68kBinaryWriterChunk {
    unsigned char *data;
    size_t used;
    size_t capacity;
    struct M68kBinaryWriterChunk *next;
} M68kBinaryWriterChunk;

struct M68kBinaryWriterState {
    M68kBinaryWriterChunk *head;
    M68kBinaryWriterChunk *tail;
};

int m68k_writer_create(M68kBinaryWriter *writer) {
    if (writer == NULL) return -1;
    memset(writer, 0, sizeof(*writer));
    writer->arena = arena_create(M68K_WRITER_CHUNK_SIZE);
    if (writer->arena == NULL) return -1;
    writer->state = (M68kBinaryWriterState *)arena_calloc(writer->arena, 1U, sizeof(*writer->state));
    if (writer->state == NULL) {
        arena_destroy(writer->arena);
        memset(writer, 0, sizeof(*writer));
        return -1;
    }
    return 0;
}

static M68kBinaryWriterChunk *append_chunk(M68kBinaryWriter *writer, size_t minimum_capacity) {
    M68kBinaryWriterChunk *chunk;
    size_t capacity = M68K_WRITER_CHUNK_SIZE;
    Arena *arena;
    if (writer == NULL || writer->arena == NULL || writer->state == NULL) return NULL;
    arena = writer->arena;
    if (capacity < minimum_capacity) capacity = minimum_capacity;
    chunk = (M68kBinaryWriterChunk *)arena_alloc(arena, sizeof(*chunk));
    if (chunk == NULL) return NULL;
    chunk->data = (unsigned char *)arena_alloc(arena, capacity);
    if (chunk->data == NULL) return NULL;
    chunk->used = 0U;
    chunk->capacity = capacity;
    chunk->next = NULL;
    if (writer->state->tail != NULL) writer->state->tail->next = chunk;
    else writer->state->head = chunk;
    writer->state->tail = chunk;
    return chunk;
}

static int append_bytes(M68kBinaryWriter *writer, const unsigned char *data, size_t size) {
    M68kBinaryWriterChunk *chunk;
    size_t remaining = size;
    const unsigned char *cursor = data;
    if (writer == NULL || writer->state == NULL) return -1;
    if (size == 0U) return 0;
    chunk = writer->state->tail;
    while (remaining != 0U) {
        size_t available;
        size_t to_copy;
        if (chunk == NULL || chunk->used == chunk->capacity) {
            chunk = append_chunk(writer, remaining);
            if (chunk == NULL) return -1;
        }
        available = chunk->capacity - chunk->used;
        to_copy = (remaining < available) ? remaining : available;
        memcpy(chunk->data + chunk->used, cursor, to_copy);
        chunk->used += to_copy;
        writer->size += to_copy;
        cursor += to_copy;
        remaining -= to_copy;
    }
    return 0;
}

int m68k_reader_read_u8(M68kBinaryReader *reader, unsigned char *out_value) {
    if (reader->pos + 1U > reader->size) return -1;
    *out_value = reader->data[reader->pos];
    reader->pos += 1U;
    return 0;
}

int m68k_reader_read_u16be(M68kBinaryReader *reader, uint16_t *out_value) {
    if (reader->pos + 2U > reader->size) return -1;
    *out_value = (uint16_t)(((uint16_t)reader->data[reader->pos] << 8)
        | (uint16_t)reader->data[reader->pos + 1U]);
    reader->pos += 2U;
    return 0;
}

int m68k_reader_read_u32be(M68kBinaryReader *reader, uint32_t *out_value) {
    if (reader->pos + 4U > reader->size) return -1;
    *out_value = ((uint32_t)reader->data[reader->pos] << 24)
        | ((uint32_t)reader->data[reader->pos + 1U] << 16)
        | ((uint32_t)reader->data[reader->pos + 2U] << 8)
        | (uint32_t)reader->data[reader->pos + 3U];
    reader->pos += 4U;
    return 0;
}

int m68k_reader_read_bytes(M68kBinaryReader *reader, unsigned char *dst,
                           size_t size) {
    if (reader->pos + size > reader->size) return -1;
    if (size != 0U) memcpy(dst, reader->data + reader->pos, size);
    reader->pos += size;
    return 0;
}

int m68k_reader_skip(M68kBinaryReader *reader, size_t size) {
    if (reader->pos + size > reader->size) return -1;
    reader->pos += size;
    return 0;
}

int m68k_reader_peek_u32be(M68kBinaryReader *reader, uint32_t *out_value) {
    size_t saved = reader->pos;
    if (m68k_reader_read_u32be(reader, out_value) != 0) return -1;
    reader->pos = saved;
    return 0;
}

int m68k_reader_remaining_is_all_zero(const M68kBinaryReader *reader) {
    size_t i;
    for (i = reader->pos; i < reader->size; ++i) {
        if (reader->data[i] != 0U) return 0;
    }
    return 1;
}

int m68k_writer_reserve(M68kBinaryWriter *writer, size_t extra) {
    M68kBinaryWriterChunk *chunk;
    if (writer == NULL || writer->state == NULL) return -1;
    chunk = writer->state->tail;
    if (chunk != NULL && chunk->capacity - chunk->used >= extra) return 0;
    return append_chunk(writer, extra) != NULL ? 0 : -1;
}

int m68k_writer_u8(M68kBinaryWriter *writer, unsigned char value) {
    return append_bytes(writer, &value, 1U);
}

int m68k_writer_u16be(M68kBinaryWriter *writer, uint16_t value) {
    unsigned char bytes[2];
    bytes[0] = (unsigned char)(value >> 8);
    bytes[1] = (unsigned char)value;
    return append_bytes(writer, bytes, sizeof(bytes));
}

int m68k_writer_u32be(M68kBinaryWriter *writer, uint32_t value) {
    unsigned char bytes[4];
    bytes[0] = (unsigned char)(value >> 24);
    bytes[1] = (unsigned char)(value >> 16);
    bytes[2] = (unsigned char)(value >> 8);
    bytes[3] = (unsigned char)value;
    return append_bytes(writer, bytes, sizeof(bytes));
}

int m68k_writer_bytes(M68kBinaryWriter *writer, const unsigned char *data,
                      size_t size) {
    return append_bytes(writer, data, size);
}

unsigned char *m68k_writer_build(const M68kBinaryWriter *writer) {
    M68kBinaryWriterChunk *chunk;
    unsigned char *data;
    size_t offset = 0U;
    if (writer == NULL) return NULL;
    data = (unsigned char *)malloc(writer->size == 0U ? 1U : writer->size);
    if (data == NULL) return NULL;
    for (chunk = writer->state != NULL ? writer->state->head : NULL; chunk != NULL; chunk = chunk->next) {
        if (chunk->used != 0U) {
            memcpy(data + offset, chunk->data, chunk->used);
            offset += chunk->used;
        }
    }
    return data;
}

void m68k_writer_destroy(M68kBinaryWriter *writer) {
    if (writer == NULL) return;
    arena_destroy(writer->arena);
    writer->size = 0U;
    writer->arena = NULL;
    writer->state = NULL;
}
