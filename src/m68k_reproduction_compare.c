#include "m68k_reproduction_compare.h"

#include <stdlib.h>
#include <string.h>

void m68k_reproduction_compare_init_result(M68kReproductionCompareResult *result) {
  if (result == NULL) return;
  memset(result, 0, sizeof(*result));
  result->status_id = M68K_REPRO_COMPARE_STATUS_NOT_COMPARED;
  result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_NONE;
  result->diagnostic_id = M68K_REPRO_COMPARE_DIAG_NONE;
}

static uint32_t compare_size_to_u32(size_t value) {
  return value > UINT32_MAX ? UINT32_MAX : (uint32_t)value;
}

static void compare_set_first_diff(M68kReproductionCompareResult *result,
    size_t offset, const unsigned char *original_bytes, size_t original_size,
    const unsigned char *rebuilt_bytes, size_t rebuilt_size) {
  if (result->has_first_diff) return;
  result->has_first_diff = 1U;
  result->first_diff_offset = compare_size_to_u32(offset);
  result->first_diff_original_byte = offset < original_size ? original_bytes[offset] : 0U;
  result->first_diff_rebuilt_byte = offset < rebuilt_size ? rebuilt_bytes[offset] : 0U;
}

static void compare_add_range(M68kReproductionCompareResult *result, size_t start, size_t end,
    size_t original_size, size_t rebuilt_size) {
  M68kReproductionCompareRange *range;
  size_t original_end = end < original_size ? end : original_size;
  size_t rebuilt_end = end < rebuilt_size ? end : rebuilt_size;
  if (result->range_count >= M68K_REPRO_COMPARE_RANGE_CAPACITY) {
    result->range_overflow = 1U;
    result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_RANGE_OVERFLOW;
    return;
  }
  range = &result->ranges[result->range_count++];
  range->original_offset = compare_size_to_u32(start);
  range->rebuilt_offset = compare_size_to_u32(start);
  range->original_size = compare_size_to_u32(original_end > start ? original_end - start : 0U);
  range->rebuilt_size = compare_size_to_u32(rebuilt_end > start ? rebuilt_end - start : 0U);
}

static void compare_collect_byte_diffs(M68kReproductionCompareResult *result,
    const unsigned char *original_bytes, size_t original_size,
    const unsigned char *rebuilt_bytes, size_t rebuilt_size) {
  size_t max_size = original_size > rebuilt_size ? original_size : rebuilt_size;
  size_t offset = 0U;
  while (offset < max_size) {
    int different = offset >= original_size || offset >= rebuilt_size ||
      original_bytes[offset] != rebuilt_bytes[offset];
    if (!different) {
      ++offset;
      continue;
    }
    {
      size_t start = offset;
      compare_set_first_diff(result, offset, original_bytes, original_size, rebuilt_bytes, rebuilt_size);
      while (offset < max_size) {
        different = offset >= original_size || offset >= rebuilt_size ||
          original_bytes[offset] != rebuilt_bytes[offset];
        if (!different) break;
        ++offset;
      }
      compare_add_range(result, start, offset, original_size, rebuilt_size);
    }
  }
  if (original_size != rebuilt_size) result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_SIZE_DIFF;
}

static int objects_have_same_payload_semantics(const M68kObject *left, const M68kObject *right) {
  size_t index;
  if (left == NULL || right == NULL || left->section_count != right->section_count) return 0;
  for (index = 0U; index < left->section_count; ++index) {
    const M68kSection *a = &left->sections[index];
    const M68kSection *b = &right->sections[index];
    if (a->kind != b->kind || a->size != b->size || a->data_size != b->data_size ||
        a->platform_mem_type != b->platform_mem_type || a->platform_mem_attrs != b->platform_mem_attrs)
      return 0;
    if (a->data_size != 0U && (a->data == NULL || b->data == NULL ||
        memcmp(a->data, b->data, a->data_size) != 0))
      return 0;
  }
  return 1;
}

static const M68kSymbol *fixup_symbol_local(const M68kObject *object, const M68kFixup *fixup) {
  if (object == NULL || fixup == NULL || !fixup->has_symbol || fixup->symbol_index >= object->symbol_count)
    return NULL;
  return &object->symbols[fixup->symbol_index];
}

static int fixups_have_same_semantics(const M68kObject *left_object, const M68kFixup *left,
    const M68kObject *right_object, const M68kFixup *right) {
  const M68kSymbol *left_symbol;
  const M68kSymbol *right_symbol;
  const char *left_name;
  const char *right_name;
  if (left == NULL || right == NULL) return 0;
  if (left->section_index != right->section_index || left->offset != right->offset ||
      left->kind != right->kind || left->width != right->width || left->addend != right->addend ||
      left->has_target_section != right->has_target_section || left->has_symbol != right->has_symbol)
    return 0;
  if (left->has_target_section && left->target_section_index != right->target_section_index) return 0;
  if (!left->has_symbol) return 1;
  left_symbol = fixup_symbol_local(left_object, left);
  right_symbol = fixup_symbol_local(right_object, right);
  if (left_symbol == NULL || right_symbol == NULL) return 0;
  left_name = left_symbol->name != NULL ? left_symbol->name : "";
  right_name = right_symbol->name != NULL ? right_symbol->name : "";
  return left_symbol->binding == right_symbol->binding && left_symbol->defined == right_symbol->defined &&
    strcmp(left_name, right_name) == 0;
}

static int fixups_have_same_container_shape(const M68kFixup *left, const M68kFixup *right) {
  return left->platform_relocation_record_kind == right->platform_relocation_record_kind &&
    left->platform_relocation_record_wire_id == right->platform_relocation_record_wire_id &&
    left->platform_relocation_block_index == right->platform_relocation_block_index &&
    left->platform_relocation_group_index == right->platform_relocation_group_index;
}

static uint32_t fixup_container_shape_diff_flags(size_t left_index, size_t right_index,
    const M68kFixup *left, const M68kFixup *right) {
  uint32_t flags = 0U;
  if (left_index != right_index) flags |= M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ORDER_DIFF;
  if (left->platform_relocation_record_kind != right->platform_relocation_record_kind ||
      left->platform_relocation_record_wire_id != right->platform_relocation_record_wire_id)
    flags |= M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ENCODING_DIFF;
  if (left->platform_relocation_block_index != right->platform_relocation_block_index ||
      left->platform_relocation_group_index != right->platform_relocation_group_index)
    flags |= M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_GROUP_DIFF;
  return flags;
}

static int objects_have_same_relocation_semantics(const M68kObject *left, const M68kObject *right,
    uint32_t *out_container_shape_flags) {
  uint8_t *used;
  size_t left_index;
  uint32_t container_shape_flags = 0U;
  if (out_container_shape_flags != NULL) *out_container_shape_flags = 0U;
  if (left == NULL || right == NULL || left->fixup_count != right->fixup_count) return 0;
  if (left->fixup_count == 0U) return 1;
  used = (uint8_t *)calloc(right->fixup_count, sizeof(*used));
  if (used == NULL) return 0;
  for (left_index = 0U; left_index < left->fixup_count; ++left_index) {
    size_t right_index;
    int matched = 0;
    for (right_index = 0U; right_index < right->fixup_count; ++right_index) {
      if (used[right_index]) continue;
      if (!fixups_have_same_semantics(left, &left->fixups[left_index], right, &right->fixups[right_index]))
        continue;
      used[right_index] = 1U;
      if (!fixups_have_same_container_shape(&left->fixups[left_index], &right->fixups[right_index])) {
        container_shape_flags |= fixup_container_shape_diff_flags(left_index, right_index,
          &left->fixups[left_index], &right->fixups[right_index]);
      } else if (left_index != right_index) {
        container_shape_flags |= M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ORDER_DIFF;
      }
      matched = 1;
      break;
    }
    if (!matched) {
      free(used);
      return 0;
    }
  }
  free(used);
  if (out_container_shape_flags != NULL) *out_container_shape_flags = container_shape_flags;
  return 1;
}

static int object_has_unsupported_container_shape(const M68kObject *object) {
  return object != NULL && (object->container_metadata.layout_overflow != 0U ||
    object->container_metadata.encoding_overflow != 0U);
}

int m68k_reproduction_compare(const M68kReproductionCompareContext *context,
    M68kReproductionCompareResult *result) {
  m68k_reproduction_compare_init_result(result);
  if (context == NULL || result == NULL || context->original_bytes == NULL ||
      context->rebuilt_bytes == NULL) {
    if (result != NULL) {
      result->status_id = M68K_REPRO_COMPARE_STATUS_INVALID_ARGUMENT;
      result->diagnostic_id = M68K_REPRO_COMPARE_DIAG_INVALID_ARGUMENT;
    }
    return -1;
  }
  result->status_id = M68K_REPRO_COMPARE_STATUS_MISMATCH;
  result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_MISMATCH;
  if (context->original_size == context->rebuilt_size &&
      (context->original_size == 0U ||
       memcmp(context->original_bytes, context->rebuilt_bytes, context->original_size) == 0)) {
    result->status_id = M68K_REPRO_COMPARE_STATUS_FULL_FILE_EXACT;
    result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE;
    return 0;
  }
  compare_collect_byte_diffs(result, context->original_bytes, context->original_size,
    context->rebuilt_bytes, context->rebuilt_size);
  result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF;
  if (context->backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
      objects_have_same_payload_semantics(context->original_object, context->rebuilt_object)) {
    uint32_t relocation_shape_flags = 0U;
    result->issue_group_flags &= ~M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF;
    if (!objects_have_same_relocation_semantics(context->original_object, context->rebuilt_object,
        &relocation_shape_flags)) {
      result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_RELOCATION_DIFF;
      return 0;
    }
    result->status_id = M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT;
    result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_CONTENT;
    result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF;
    result->issue_group_flags |= relocation_shape_flags;
    if (context->assembler_policy != NULL &&
        (context->assembler_policy->flags & M68K_ASSEMBLER_POLICY_PRESERVE_HUNK_RELOCATION_ENCODING) != 0U &&
        relocation_shape_flags != 0U)
      result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_POLICY_DIVERGENCE;
    if (object_has_unsupported_container_shape(context->original_object) ||
        object_has_unsupported_container_shape(context->rebuilt_object))
      result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_UNSUPPORTED_CONTAINER_SHAPE;
  }
  return 0;
}
