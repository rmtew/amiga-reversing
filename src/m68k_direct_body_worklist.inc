typedef struct M68kTypedLocalCalleeState {
    uint32_t offset;
    uint8_t saved_mask;
    uint8_t preserved_mask;
    /* A direct body may name a caller argument only while A7 still has its
     * entry value. Frame setup, cleanup, or auto-indexing ends that proof. */
    uint8_t stack_entry_stable;
    uint32_t frame_id;
    /* Each address register either still denotes one entry ABI register, or
     * has been written by the callee.  This is deliberately identity-only:
     * it never guesses that a locally-created address is a caller input. */
    uint8_t entry_origin[8];
    /* A data register can carry one lossless longword copy of an entry pointer
     * value. It is otherwise unknown, so scalar Dn values never manufacture
     * pointer ABI inputs. */
    uint8_t data_origin[8];
    M68kLocalHardwareValues hardware;
  } M68kTypedLocalCalleeState;

typedef struct M68kLocalCalleeFrame {
  uint32_t parent, width;
  uint8_t origin;
} M68kLocalCalleeFrame;

typedef struct M68kLocalCalleeInputs {
  M68kTypedLocalCalleeState *states;
  size_t count, capacity, *index, index_capacity, transfers;
  M68kLocalCalleeFrame *frames;
  size_t frame_count, frame_capacity, *frame_index, frame_index_capacity;
  uint32_t *frame_scratch;
  size_t frame_scratch_capacity;
} M68kLocalCalleeInputs;

/* Origins form a must lattice: disagreement drops identity, never unions it.
 * Saved frames must agree exactly; intersecting them would hide an unmatched
 * push/pop path. The instruction transfers below remain the existing ones. */
static int local_callee_input_join(M68kTypedLocalCalleeState *dest,
    const M68kTypedLocalCalleeState *source) {
  M68kTypedLocalCalleeState old = *dest;
  uint8_t reg, kind;
  if (dest->saved_mask != source->saved_mask || dest->frame_id != source->frame_id) return -1;
  dest->preserved_mask &= source->preserved_mask;
  dest->stack_entry_stable &= source->stack_entry_stable;
  for (reg = 0U; reg < 8U; ++reg) {
    if (dest->entry_origin[reg] != source->entry_origin[reg]) dest->entry_origin[reg] = 0xffU;
    if (dest->data_origin[reg] != source->data_origin[reg]) dest->data_origin[reg] = 0xffU;
  }
  for (kind = 0U; kind < 2U; ++kind) {
    dest->hardware.known[kind] &= source->hardware.known[kind];
    for (reg = 0U; reg < 8U; ++reg) {
      uint32_t bit = (uint32_t)1U << reg;
      if (dest->hardware.ids[kind][reg] != source->hardware.ids[kind][reg])
        dest->hardware.known[kind] &= ~bit;
      if (!(dest->hardware.known[kind] & bit)) dest->hardware.ids[kind][reg] = 0U;
    }
  }
  return old.preserved_mask != dest->preserved_mask || old.stack_entry_stable != dest->stack_entry_stable ||
    memcmp(old.entry_origin, dest->entry_origin, sizeof(old.entry_origin)) != 0 ||
    memcmp(old.data_origin, dest->data_origin, sizeof(old.data_origin)) != 0 ||
    memcmp(&old.hardware, &dest->hardware, sizeof(old.hardware)) != 0;
}

static size_t local_callee_pc_hash(uint32_t offset, size_t capacity) {
  uint32_t hash = (offset ^ (offset >> 16U)) * UINT32_C(2654435761);
  return (size_t)hash & (capacity - 1U);
}

/* One sparse input state per reachable instruction, indexed by PC. No dense
 * per-node slot array, path enumeration, recursion or arbitrary visit cap. */
static int local_callee_input_visit(M68kLocalCalleeInputs *inputs, M68kTypedLocalCalleeState *state) {
  size_t at;
  if (inputs->index_capacity) {
    at = local_callee_pc_hash(state->offset, inputs->index_capacity);
    while (inputs->index[at]) {
      M68kTypedLocalCalleeState *known = &inputs->states[inputs->index[at] - 1U];
      if (known->offset == state->offset) {
        int changed = local_callee_input_join(known, state);
        if (changed > 0) { *state = *known; ++inputs->transfers; }
        return changed;
      }
      at = (at + 1U) & (inputs->index_capacity - 1U);
    }
  }
  if (inputs->count >= inputs->index_capacity / 2U) {
    size_t capacity = inputs->index_capacity ? inputs->index_capacity * 2U : 32U;
    size_t *index;
    if (capacity < inputs->index_capacity || capacity > SIZE_MAX / sizeof(*index)) return -2;
    index = calloc(capacity, sizeof(*index));
    if (!index) return -2;
    for (size_t i = 0U; i < inputs->count; ++i) {
      at = local_callee_pc_hash(inputs->states[i].offset, capacity);
      while (index[at]) at = (at + 1U) & (capacity - 1U);
      index[at] = i + 1U;
    }
    free(inputs->index); inputs->index = index; inputs->index_capacity = capacity;
  }
  if (inputs->count == inputs->capacity) {
    size_t capacity = inputs->capacity ? inputs->capacity * 2U : 16U;
    M68kTypedLocalCalleeState *states;
    if (capacity < inputs->capacity || capacity > SIZE_MAX / sizeof(*states)) return -2;
    states = realloc(inputs->states, capacity * sizeof(*states));
    if (!states) return -2;
    inputs->states = states; inputs->capacity = capacity;
  }
  for (uint8_t kind = 0U; kind < 2U; ++kind)
    for (uint8_t reg = 0U; reg < 8U; ++reg)
      if (!(state->hardware.known[kind] & ((uint32_t)1U << reg))) state->hardware.ids[kind][reg] = 0U;
  at = local_callee_pc_hash(state->offset, inputs->index_capacity);
  while (inputs->index[at]) at = (at + 1U) & (inputs->index_capacity - 1U);
  inputs->states[inputs->count] = *state; inputs->index[at] = ++inputs->count;
  ++inputs->transfers;
  return 1;
}

static int local_callee_push(M68kTypedLocalCalleeState **work, size_t *count, size_t *capacity,
    const M68kTypedLocalCalleeState *state) {
  if (*count == *capacity) {
    size_t next = *capacity ? *capacity * 2U : 16U;
    M68kTypedLocalCalleeState *grown;
    if (next < *capacity || next > SIZE_MAX / sizeof(*grown)) return -1;
    grown = realloc(*work, next * sizeof(*grown));
    if (!grown) return -1;
    *work = grown; *capacity = next;
  }
  (*work)[(*count)++] = *state;
  return 0;
}

/* Immutable, interned frame chains store entry-value identities, not addresses.
 * Equivalent scalar and MOVEM layouts share a frame ID. Only used frames are
 * allocated; every PC keeps one small ID rather than a dense slot array. */
static size_t local_callee_frame_hash(uint32_t parent, uint32_t width, uint8_t origin, size_t capacity) {
  return local_callee_pc_hash(parent ^ (width * UINT32_C(2246822519)) ^ ((uint32_t)origin << 16U), capacity);
}

static uint32_t local_callee_frame_intern(M68kLocalCalleeInputs *inputs,
    uint32_t parent, uint32_t width, uint8_t origin) {
  size_t at;
  if (origin == 0xffU && parent && inputs->frames[parent - 1U].origin == 0xffU &&
      inputs->frames[parent - 1U].width <= UINT32_MAX - width) {
    width += inputs->frames[parent - 1U].width;
    parent = inputs->frames[parent - 1U].parent;
  }
  if (inputs->frame_index_capacity) {
    at = local_callee_frame_hash(parent, width, origin, inputs->frame_index_capacity);
    while (inputs->frame_index[at]) {
      const M68kLocalCalleeFrame *f = &inputs->frames[inputs->frame_index[at] - 1U];
      if (f->parent == parent && f->width == width && f->origin == origin)
        return (uint32_t)inputs->frame_index[at];
      at = (at + 1U) & (inputs->frame_index_capacity - 1U);
    }
  }
  if (inputs->frame_count >= UINT32_MAX) return 0U;
  if (inputs->frame_count >= inputs->frame_index_capacity / 2U) {
    size_t capacity = inputs->frame_index_capacity ? inputs->frame_index_capacity * 2U : 32U;
    size_t *index;
    if (capacity < inputs->frame_index_capacity || capacity > SIZE_MAX / sizeof(*index)) return 0U;
    index = calloc(capacity, sizeof(*index)); if (!index) return 0U;
    for (size_t i = 0U; i < inputs->frame_count; ++i) {
      const M68kLocalCalleeFrame *f = &inputs->frames[i];
      at = local_callee_frame_hash(f->parent, f->width, f->origin, capacity);
      while (index[at]) at = (at + 1U) & (capacity - 1U);
      index[at] = i + 1U;
    }
    free(inputs->frame_index); inputs->frame_index = index; inputs->frame_index_capacity = capacity;
  }
  if (inputs->frame_count == inputs->frame_capacity) {
    size_t capacity = inputs->frame_capacity ? inputs->frame_capacity * 2U : 16U;
    M68kLocalCalleeFrame *frames;
    if (capacity < inputs->frame_capacity || capacity > SIZE_MAX / sizeof(*frames)) return 0U;
    frames = realloc(inputs->frames, capacity * sizeof(*frames)); if (!frames) return 0U;
    inputs->frames = frames; inputs->frame_capacity = capacity;
  }
  at = local_callee_frame_hash(parent, width, origin, inputs->frame_index_capacity);
  while (inputs->frame_index[at]) at = (at + 1U) & (inputs->frame_index_capacity - 1U);
  inputs->frames[inputs->frame_count].parent = parent; inputs->frames[inputs->frame_count].width = width;
  inputs->frames[inputs->frame_count].origin = origin;
  inputs->frame_index[at] = ++inputs->frame_count;
  return (uint32_t)inputs->frame_count;
}

static int local_callee_frame_pop(M68kLocalCalleeInputs *inputs, uint32_t *id, uint32_t width, uint8_t *origin) {
  uint32_t left = width;
  *origin = 0xffU;
  if (*id && width == 4U && inputs->frames[*id - 1U].width == 4U)
    *origin = inputs->frames[*id - 1U].origin;
  while (left) {
    M68kLocalCalleeFrame f;
    if (!*id) return -1; /* Do not read an unowned caller/return slot. */
    f = inputs->frames[*id - 1U];
    if (f.width <= left) { left -= f.width; *id = f.parent; }
    else {
      *id = local_callee_frame_intern(inputs, f.parent, f.width - left, 0xffU);
      if (!*id) return -2;
      left = 0U;
    }
  }
  return 0;
}

static void local_callee_frame_saved_mask(const M68kLocalCalleeInputs *inputs, M68kTypedLocalCalleeState *state) {
  uint32_t id = state->frame_id;
  state->saved_mask = 0U;
  while (id) {
    const M68kLocalCalleeFrame *f = &inputs->frames[id - 1U];
    if (f->width == 4U && f->origin < 8U) state->saved_mask |= (uint8_t)(1U << f->origin);
    id = f->parent;
  }
}

static int local_callee_frame_write(M68kLocalCalleeInputs *inputs, M68kTypedLocalCalleeState *state,
    int32_t displacement, uint8_t width) {
  uint32_t id = state->frame_id, rebuilt = 0U;
  size_t count = 0U;
  int64_t offset = 0;
  if (inputs->frame_count > inputs->frame_scratch_capacity) {
    uint32_t *scratch;
    if (inputs->frame_count > SIZE_MAX / sizeof(*scratch)) return -2;
    scratch = realloc(inputs->frame_scratch, inputs->frame_count * sizeof(*scratch));
    if (!scratch) return -2;
    inputs->frame_scratch = scratch; inputs->frame_scratch_capacity = inputs->frame_count;
  }
  while (id) { inputs->frame_scratch[count++] = id; id = inputs->frames[id - 1U].parent; }
  /* Widths can denote an opaque local allocation chunk. Compute physical
   * positions once, then rebuild bottom-up without C recursion. */
  for (size_t i = 0U; i < count; ++i) offset += inputs->frames[inputs->frame_scratch[i] - 1U].width;
  while (count) {
    M68kLocalCalleeFrame f = inputs->frames[inputs->frame_scratch[--count] - 1U];
    offset -= f.width;
    if (!width || (offset < (int64_t)displacement + width && displacement < offset + f.width)) f.origin = 0xffU;
    rebuilt = local_callee_frame_intern(inputs, rebuilt, f.width, f.origin);
    if (!rebuilt) return -2;
  }
  state->frame_id = rebuilt; local_callee_frame_saved_mask(inputs, state); return 0;
}

static int local_callee_stack_transfer(M68kLocalCalleeInputs *inputs, M68kTypedLocalCalleeState *state,
    const M68kStackRegisterTransfer *transfer, const uint8_t before[16]) {
  if (transfer->direction == M68K_STACK_TRANSFER_PUSH) {
    if (!transfer->register_mask) {
      state->frame_id = local_callee_frame_intern(inputs, state->frame_id, transfer->width, 0xffU);
      if (!state->frame_id) return -2;
    } else for (int bit = 15; bit >= 0; --bit) if (transfer->register_mask & (1U << bit)) {
      state->frame_id = local_callee_frame_intern(inputs, state->frame_id, transfer->width,
        transfer->width == 4U ? before[bit] : 0xffU);
      if (!state->frame_id) return -2;
    }
  } else {
    for (uint8_t bit = 0U; bit < 16U; ++bit) if ((transfer->register_mask & (1U << bit)) ||
        (!transfer->register_mask && bit == 0U)) {
      uint8_t origin;
      int result = local_callee_frame_pop(inputs, &state->frame_id, transfer->width, &origin);
      if (result) return result;
      if (transfer->register_mask) {
        if (bit < 8U) state->data_origin[bit] = origin;
        else {
          state->entry_origin[bit - 8U] = origin;
          if (origin == bit - 8U) state->preserved_mask |= (uint8_t)(1U << (bit - 8U));
          else state->preserved_mask &= (uint8_t)~(1U << (bit - 8U));
        }
      }
    }
  }
  local_callee_frame_saved_mask(inputs, state); return 0;
}

/* Compact entry identities consume the same admitted register ABI/result
 * contract as typed values. They do not infer types, stack/tuple bindings or
 * values from a numeric address. Result sources always use the precall state. */
static int local_callee_identity_location(const M68kFunctionSummaryAbiLocation *location,
    uint8_t *ordinal) {
  uint8_t kind, reg;
  if (location->kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
      location->width != 4U || location->register_count != 1U) return 0;
  kind = location->registers[0].register_kind;
  reg = location->registers[0].register_index;
  if (reg >= 8U || (kind != M68K_ANALYSIS_REGISTER_ADDRESS && kind != M68K_ANALYSIS_REGISTER_DATA)) return 0;
  *ordinal = reg + (kind == M68K_ANALYSIS_REGISTER_ADDRESS ? 8U : 0U);
  return 1;
}

static void local_callee_identity_call(M68kTypedLocalCalleeState *state,
    const M68kAnalysisFunctionSummary *summary, const uint8_t before[16]) {
  for (uint8_t reg = 0U; reg < 8U; ++reg) {
    if (function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_ADDRESS, reg) !=
        M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) state->entry_origin[reg] = 0xffU;
    if (function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_DATA, reg) !=
        M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) state->data_origin[reg] = 0xffU;
  }
  if (!summary || summary->effects_invalid || summary->result_contract_invalid) return;
  for (size_t i = 0U; i < summary->result_count; ++i) {
    const M68kAnalysisFunctionSummaryResult *result = &summary->results[i];
    const M68kAnalysisFunctionSummaryInput *input;
    uint8_t source, dest;
    if (result->kind != M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT ||
        result->input_index >= summary->input_count) continue;
    input = &summary->inputs[result->input_index];
    /* A conditional struct-typed input needs the full typed caller check;
     * this compact bit-identity adapter admits only untyped ABI identity. */
    if (input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_ABI_POINTER ||
        !local_callee_identity_location(&input->location, &source) ||
        !local_callee_identity_location(&result->location, &dest)) continue;
    if (dest < 8U) state->data_origin[dest] = before[source];
    else state->entry_origin[dest - 8U] = before[source];
  }
}
