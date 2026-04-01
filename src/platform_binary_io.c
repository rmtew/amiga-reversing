#include "platform_binary_io.h"

#include <stdlib.h>
#include <string.h>

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
    size_t needed = writer->size + extra;
    size_t next_capacity;
    unsigned char *grown;
    if (needed <= writer->capacity) return 0;
    next_capacity = (writer->capacity == 0U) ? 128U : writer->capacity * 2U;
    while (next_capacity < needed) next_capacity *= 2U;
    grown = (unsigned char *)realloc(writer->data, next_capacity);
    if (grown == NULL) return -1;
    writer->data = grown;
    writer->capacity = next_capacity;
    return 0;
}

int m68k_writer_u8(M68kBinaryWriter *writer, unsigned char value) {
    if (m68k_writer_reserve(writer, 1U) != 0) return -1;
    writer->data[writer->size++] = value;
    return 0;
}

int m68k_writer_u16be(M68kBinaryWriter *writer, uint16_t value) {
    if (m68k_writer_reserve(writer, 2U) != 0) return -1;
    writer->data[writer->size++] = (unsigned char)(value >> 8);
    writer->data[writer->size++] = (unsigned char)value;
    return 0;
}

int m68k_writer_u32be(M68kBinaryWriter *writer, uint32_t value) {
    if (m68k_writer_reserve(writer, 4U) != 0) return -1;
    writer->data[writer->size] = (unsigned char)(value >> 24);
    writer->data[writer->size + 1U] = (unsigned char)(value >> 16);
    writer->data[writer->size + 2U] = (unsigned char)(value >> 8);
    writer->data[writer->size + 3U] = (unsigned char)value;
    writer->size += 4U;
    return 0;
}

int m68k_writer_bytes(M68kBinaryWriter *writer, const unsigned char *data,
                      size_t size) {
    if (m68k_writer_reserve(writer, size) != 0) return -1;
    if (size != 0U) memcpy(writer->data + writer->size, data, size);
    writer->size += size;
    return 0;
}
