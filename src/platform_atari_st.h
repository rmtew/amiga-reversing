#ifndef PLATFORM_ATARI_ST_H
#define PLATFORM_ATARI_ST_H

#include "m68k_object.h"

#include <stdint.h>

int m68k_atari_st_set_program_flags(M68kObject *object, uint32_t program_flags);
int m68k_atari_st_read_program_flags(const char *path, uint32_t *out_program_flags);
int m68k_atari_st_get_program_flags(const M68kObject *object, uint32_t *out_program_flags);

#endif
