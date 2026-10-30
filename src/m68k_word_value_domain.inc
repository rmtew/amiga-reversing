/* One shared low-WORD domain. Larger joins retain only agreeing bits instead
 * of enlarging finite candidate arrays. Each non-finite join can only lose
 * known bits, so cyclic joins have finite height without numeric range caps. */
static void hardware_word_known_bits(const M68kHardwareWordSet *set, uint16_t *mask, uint16_t *value) {
  if (!set->count) { *mask = set->known_bits_mask; *value = set->known_bits_value; return; }
  uint16_t all = UINT16_MAX, any = 0U;
  for (uint8_t i = 0U; i < set->count; ++i) { all &= set->values[i]; any |= set->values[i]; }
  *mask = (uint16_t)~(all ^ any); *value = all;
}

static void hardware_word_from_bits(M68kHardwareWordSet *set, uint16_t mask, uint16_t value) {
  memset(set, 0, sizeof(*set));
  if (!mask) return;
  uint16_t free = (uint16_t)~mask, bits = free;
  unsigned count = 0U;
  while (bits) { bits &= (uint16_t)(bits - 1U); ++count; }
  value &= mask;
  if ((1U << count) <= M68K_HARDWARE_VALUE_LIMIT) {
    uint16_t choice = free;
    for (;;) {
      (void)hardware_word_set_add(set, (uint16_t)(value | choice));
      if (!choice) break;
      choice = (uint16_t)((choice - 1U) & free);
    }
  } else { set->known_bits_mask = mask; set->known_bits_value = value; }
}

static void hardware_word_set_merge(M68kHardwareWordSet *dest, const M68kHardwareWordSet *source) {
  uint8_t contract = dest->requires_input_contract | source->requires_input_contract;
  if (dest->count && source->count) {
    M68kHardwareWordSet finite = *dest;
    uint8_t i;
    for (i = 0U; i < source->count; ++i)
      if (!hardware_word_set_add(&finite, source->values[i])) break;
    if (i == source->count) { finite.requires_input_contract = contract; *dest = finite; return; }
  }
  uint16_t am, av, bm, bv;
  hardware_word_known_bits(dest, &am, &av); hardware_word_known_bits(source, &bm, &bv);
  uint16_t mask = (uint16_t)(am & bm & (uint16_t)~(av ^ bv));
  hardware_word_from_bits(dest, mask, (uint16_t)(av & mask));
  dest->requires_input_contract = (dest->count || dest->known_bits_mask) ? contract : 0U;
}
