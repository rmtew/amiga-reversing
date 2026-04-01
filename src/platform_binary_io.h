#ifndef PLATFORM_BINARY_IO_H
#define PLATFORM_BINARY_IO_H

#include <stddef.h>
#include <stdint.h>

typedef struct M68kBinaryReader {
    const unsigned char *data;
    size_t size;
    size_t pos;
} M68kBinaryReader;

typedef struct M68kBinaryWriter {
    unsigned char *data;
    size_t size;
    size_t capacity;
} M68kBinaryWriter;

int m68k_reader_read_u8(M68kBinaryReader *reader, unsigned char *out_value);
int m68k_reader_read_u16be(M68kBinaryReader *reader, uint16_t *out_value);
int m68k_reader_read_u32be(M68kBinaryReader *reader, uint32_t *out_value);
int m68k_reader_read_bytes(M68kBinaryReader *reader, unsigned char *dst,
                           size_t size);
int m68k_reader_skip(M68kBinaryReader *reader, size_t size);
int m68k_reader_peek_u32be(M68kBinaryReader *reader, uint32_t *out_value);
int m68k_reader_remaining_is_all_zero(const M68kBinaryReader *reader);

int m68k_writer_reserve(M68kBinaryWriter *writer, size_t extra);
int m68k_writer_u8(M68kBinaryWriter *writer, unsigned char value);
int m68k_writer_u16be(M68kBinaryWriter *writer, uint16_t value);
int m68k_writer_u32be(M68kBinaryWriter *writer, uint32_t value);
int m68k_writer_bytes(M68kBinaryWriter *writer, const unsigned char *data,
                      size_t size);

#endif
