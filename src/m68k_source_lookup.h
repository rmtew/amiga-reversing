#ifndef M68K_SOURCE_LOOKUP_H
#define M68K_SOURCE_LOOKUP_H

#include <stddef.h>
#include <stdint.h>

typedef struct M68kSourceLookupResult {
    uint8_t ok;
    uint8_t defined;
    uint8_t is_constant;
    uint32_t value;
    size_t symbol_id;
    size_t section_index;
} M68kSourceLookupResult;

typedef struct M68kSourceConstantResult {
    uint8_t ok;
    uint32_t value;
} M68kSourceConstantResult;

#endif
