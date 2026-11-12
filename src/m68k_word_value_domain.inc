/* One shared low-WORD domain. Larger joins retain agreeing bits and identical
 * bounds instead of enlarging finite candidate arrays. Different ranges lose
 * their bounds at joins; no numeric widening/convergence cap is added. */
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
  uint16_t symbol = dest->scalar_symbol_equate == source->scalar_symbol_equate ?
    dest->scalar_symbol_equate : 0U;
  int same_bounds = dest->has_bounds && source->has_bounds &&
    dest->lower_bound == source->lower_bound && dest->upper_bound == source->upper_bound;
  uint16_t lower = dest->lower_bound, upper = dest->upper_bound;
  if (dest->count && source->count) {
    M68kHardwareWordSet finite = *dest;
    uint8_t i;
    for (i = 0U; i < source->count; ++i)
      if (!hardware_word_set_add(&finite, source->values[i])) break;
    if (i == source->count) { finite.requires_input_contract = contract; finite.scalar_symbol_equate = finite.count == 1U ? symbol : 0U; *dest = finite; return; }
  }
  uint16_t am, av, bm, bv;
  hardware_word_known_bits(dest, &am, &av); hardware_word_known_bits(source, &bm, &bv);
  uint16_t mask = (uint16_t)(am & bm & (uint16_t)~(av ^ bv));
  hardware_word_from_bits(dest, mask, (uint16_t)(av & mask));
  /* Unequal incoming ranges lose their bounds, not an incoming path. Finite
   * joins retain the existing cap; no interval widening loop is introduced. */
  if (same_bounds && !dest->count) {
    dest->has_bounds = 1U; dest->lower_bound = lower; dest->upper_bound = upper;
  }
  dest->requires_input_contract = (dest->count || dest->known_bits_mask || dest->has_bounds) ? contract : 0U;
}

typedef struct HardwareWordInterval { uint32_t lower, upper; } HardwareWordInterval;

static unsigned hardware_word_split_bounds(uint16_t lower, uint16_t upper, HardwareWordInterval *parts) {
  if (lower <= upper) { parts[0] = (HardwareWordInterval){lower, upper}; return 1U; }
  parts[0] = (HardwareWordInterval){0U, upper};
  parts[1] = (HardwareWordInterval){lower, UINT16_MAX};
  return 2U;
}

static int hardware_word_in_parts(uint16_t value, const HardwareWordInterval *parts, unsigned count) {
  for (unsigned i = 0U; i < count; ++i)
    if (value >= parts[i].lower && value <= parts[i].upper) return 1;
  return 0;
}

/* Intersect actual compare edges before turning a small domain into values.
 * Modular bounds retain negative WORDs across guards in either order. This
 * uses only the existing packet, transfers and must-join invalidation paths. */
static int hardware_word_refine_bounds(M68kHardwareWordSet *set, uint16_t lower, uint16_t upper) {
  M68kHardwareWordSet result = {0};
  HardwareWordInterval incoming[2], predicate[2], intersections[4], parts[4];
  unsigned ni, np, n = 0U, count = 0U;
  uint16_t prior_mask = 0U, prior_value = 0U;
  uint16_t symbol = set->scalar_symbol_equate;
  if (set->requires_input_contract) { memset(set, 0, sizeof(*set)); symbol = 0U; }
  np = hardware_word_split_bounds(lower, upper, predicate);
  if (set->count) {
    for (uint8_t i = 0U; i < set->count; ++i)
      if (hardware_word_in_parts(set->values[i], predicate, np))
        (void)hardware_word_set_add(&result, set->values[i]);
    if (!result.count) return 0;
    result.scalar_symbol_equate = result.count == 1U ? symbol : 0U;
    *set = result; return 1;
  }
  hardware_word_known_bits(set, &prior_mask, &prior_value);
  ni = hardware_word_split_bounds(set->has_bounds ? set->lower_bound : 0U,
    set->has_bounds ? set->upper_bound : UINT16_MAX, incoming);
  for (unsigned i = 0U; i < ni; ++i) for (unsigned j = 0U; j < np; ++j) {
    uint32_t lo = incoming[i].lower > predicate[j].lower ? incoming[i].lower : predicate[j].lower;
    uint32_t hi = incoming[i].upper < predicate[j].upper ? incoming[i].upper : predicate[j].upper;
    if (lo <= hi) intersections[n++] = (HardwareWordInterval){lo, hi};
  }
  if (!n) return 0;
  for (unsigned i = 1U; i < n; ++i) {
    HardwareWordInterval v = intersections[i]; unsigned j = i;
    while (j && intersections[j - 1U].lower > v.lower) { intersections[j] = intersections[j - 1U]; --j; }
    intersections[j] = v;
  }
  for (unsigned i = 0U; i < n; ++i) {
    if (count && intersections[i].lower <= parts[count - 1U].upper + 1U) {
      if (intersections[i].upper > parts[count - 1U].upper) parts[count - 1U].upper = intersections[i].upper;
    } else parts[count++] = intersections[i];
  }
  uint32_t cardinality = 0U;
  uint16_t mask = UINT16_MAX, value = 0U;
  for (unsigned i = 0U; i < count; ++i) {
    uint16_t unknown = (uint16_t)(parts[i].lower ^ parts[i].upper);
    unknown |= unknown >> 1U; unknown |= unknown >> 2U; unknown |= unknown >> 4U; unknown |= unknown >> 8U;
    uint16_t pm = (uint16_t)~unknown, pv = (uint16_t)(parts[i].lower & pm);
    if (!i) { mask = pm; value = pv; }
    else { mask = (uint16_t)(mask & pm & (uint16_t)~(value ^ pv)); value &= mask; }
    cardinality += parts[i].upper - parts[i].lower + 1U;
  }
  if (((value ^ prior_value) & mask & prior_mask) != 0U) return 0;
  mask |= prior_mask; value = (uint16_t)((value | prior_value) & mask);
  if (cardinality <= M68K_HARDWARE_VALUE_LIMIT) {
    for (unsigned i = 0U; i < count; ++i) for (uint32_t v = parts[i].lower; v <= parts[i].upper; ++v)
      if (((uint16_t)v & mask) == value) (void)hardware_word_set_add(&result, (uint16_t)v);
    if (!result.count) return 0;
  } else {
    hardware_word_from_bits(&result, mask, value);
    if (result.count) {
      M68kHardwareWordSet filtered = {0};
      for (uint8_t i = 0U; i < result.count; ++i)
        if (hardware_word_in_parts(result.values[i], parts, count))
          (void)hardware_word_set_add(&filtered, result.values[i]);
      if (!filtered.count) return 0;
      result = filtered;
    } else {
      /* Two boundary-touching pieces form one modular interval. Other
       * disconnected intersections retain a conservative ordinary hull. */
      uint16_t lo = (uint16_t)parts[0].lower, hi = (uint16_t)parts[count - 1U].upper;
      if (count == 2U && !parts[0].lower && parts[1].upper == UINT16_MAX) {
        lo = (uint16_t)parts[1].lower; hi = (uint16_t)parts[0].upper;
      }
      if (lo != 0U || hi != UINT16_MAX) {
        result.has_bounds = 1U; result.lower_bound = lo; result.upper_bound = hi;
      }
    }
  }
  *set = result; return 1;
}
