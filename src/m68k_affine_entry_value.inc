/* A value-component identity, not a pointer classifier: root + signed offset.
 * Root IDs belong to one proof context. Exact agreement is the must join;
 * incompatible roots/offsets become unknown. No numeric value creates a root. */
typedef struct M68kAffineEntryValue {
  uint32_t root;
  int32_t offset;
  uint8_t width;
} M68kAffineEntryValue;

typedef struct M68kAffineEntryContext {
  M68kAffineEntryValue *values;
  size_t count, capacity, *index, index_capacity;
  int failed;
} M68kAffineEntryContext;

static size_t affine_entry_hash(uint32_t root, int32_t offset, uint8_t width, size_t capacity) {
  uint32_t hash = root * UINT32_C(2654435761) ^ (uint32_t)offset * UINT32_C(2246822519) ^ width;
  return (size_t)(hash ^ (hash >> 16U)) & (capacity - 1U);
}

static uint32_t affine_entry_intern(M68kAffineEntryContext *context, uint32_t root,
    int64_t offset, uint8_t width) {
  size_t at;
  if (!context || !root || (width != 2U && width != 4U)) return 0U;
  if (width == 2U) offset = (int16_t)(uint16_t)offset;
  if (offset < INT32_MIN || offset > INT32_MAX) return 0U;
  if (context->index_capacity) {
    at = affine_entry_hash(root, (int32_t)offset, width, context->index_capacity);
    while (context->index[at]) {
      const M68kAffineEntryValue *value = &context->values[context->index[at] - 1U];
      if (value->root == root && value->offset == offset && value->width == width)
        return (uint32_t)context->index[at];
      at = (at + 1U) & (context->index_capacity - 1U);
    }
  }
  if (context->count == UINT32_MAX) goto failure;
  if (context->count >= context->index_capacity / 2U) {
    size_t capacity = context->index_capacity ? context->index_capacity * 2U : 32U;
    size_t *index;
    if (capacity < context->index_capacity || capacity > SIZE_MAX / sizeof(*index)) goto failure;
    index = calloc(capacity, sizeof(*index));
    if (!index) goto failure;
    for (size_t i = 0U; i < context->count; ++i) {
      const M68kAffineEntryValue *value = &context->values[i];
      at = affine_entry_hash(value->root, value->offset, value->width, capacity);
      while (index[at]) at = (at + 1U) & (capacity - 1U);
      index[at] = i + 1U;
    }
    free(context->index); context->index = index; context->index_capacity = capacity;
  }
  if (context->count == context->capacity) {
    size_t capacity = context->capacity ? context->capacity * 2U : 16U;
    M68kAffineEntryValue *values;
    if (capacity < context->capacity || capacity > SIZE_MAX / sizeof(*values)) goto failure;
    values = realloc(context->values, capacity * sizeof(*values));
    if (!values) goto failure;
    context->values = values; context->capacity = capacity;
  }
  at = affine_entry_hash(root, (int32_t)offset, width, context->index_capacity);
  while (context->index[at]) at = (at + 1U) & (context->index_capacity - 1U);
  context->values[context->count] = (M68kAffineEntryValue){root, (int32_t)offset, width};
  context->index[at] = ++context->count;
  return (uint32_t)context->count;
failure:
  context->failed = 1; return 0U;
}

static const M68kAffineEntryValue *affine_entry_value(const M68kAffineEntryContext *context, uint32_t id) {
  return context && id && id <= context->count ? &context->values[id - 1U] : NULL;
}

static uint32_t affine_entry_adjust(M68kAffineEntryContext *context, uint32_t id, int64_t delta) {
  const M68kAffineEntryValue *value = affine_entry_value(context, id);
  if (!value) return 0U;
  return affine_entry_intern(context, value->root, (int64_t)value->offset + delta, value->width);
}

static void affine_entry_destroy(M68kAffineEntryContext *context) {
  free(context->values); free(context->index); memset(context, 0, sizeof(*context));
}
