#ifndef M68K_BITSET_H
#define M68K_BITSET_H

#include <stdint.h>

static inline uint32_t m68k_bitset_u32_bit(uint8_t index) {
  return index < 32U ? (uint32_t)(1UL << index) : 0U;
}

static inline int m68k_bitset_u32_has(uint32_t bits, uint8_t index) {
  return (bits & m68k_bitset_u32_bit(index)) != 0U;
}

static inline void m68k_bitset_u32_set(uint32_t *bits, uint8_t index) {
  if (bits != NULL) *bits |= m68k_bitset_u32_bit(index);
}

static inline void m68k_bitset_u32_clear(uint32_t *bits, uint8_t index) {
  if (bits != NULL) *bits &= ~m68k_bitset_u32_bit(index);
}

#endif
