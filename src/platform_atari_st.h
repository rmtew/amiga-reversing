#ifndef PLATFORM_ATARI_ST_H
#define PLATFORM_ATARI_ST_H

#include "m68k_object.h"

#include <stdint.h>

int m68k_atari_st_set_program_flags(M68kObject *object, uint32_t program_flags);
int m68k_atari_st_read_program_flags(const char *path, uint32_t *out_program_flags);
int m68k_atari_st_get_program_flags(const M68kObject *object, uint32_t *out_program_flags);
int m68k_atari_st_set_relocation_flag(M68kObject *object, uint16_t relocation_flag);
int m68k_atari_st_get_relocation_flag(const M68kObject *object, uint16_t *out_relocation_flag);
int m68k_atari_st_set_raw_symbol_table(M68kObject *object, uint32_t symbol_table_type, const uint8_t *data,
    uint32_t size);
int m68k_atari_st_get_raw_symbol_table(const M68kObject *object, uint32_t *out_symbol_table_type,
    const uint8_t **out_data, uint32_t *out_size);
int m68k_atari_st_set_raw_relocation_stream(M68kObject *object, const uint8_t *data, uint32_t size);
int m68k_atari_st_get_raw_relocation_stream(const M68kObject *object, const uint8_t **out_data,
    uint32_t *out_size);

#endif
