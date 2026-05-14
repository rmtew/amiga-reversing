#include "m68k_reproduction_compare.h"
#include "util_arena.h"

#include <string.h>

enum {
  M68K_REPRO_LAYOUT_UNKNOWN = 0,
  M68K_REPRO_LAYOUT_HEADER = 1,
  M68K_REPRO_LAYOUT_SECTION_HEADER = 2,
  M68K_REPRO_LAYOUT_SECTION_PAYLOAD = 3,
  M68K_REPRO_LAYOUT_SECTION_END = 4,
  M68K_REPRO_LAYOUT_RELOCATION = 5,
  M68K_REPRO_LAYOUT_SYMBOL_TABLE = 6,
  M68K_REPRO_LAYOUT_SYMBOL = 7,
  M68K_REPRO_LAYOUT_DEBUG = 8,
  M68K_REPRO_LAYOUT_EXTERNAL = 9
};

enum {
  M68K_REPRO_DIAG_ATARI_HEADER_FIELD_MISMATCH = 1,
  M68K_REPRO_DIAG_ATARI_RELOCATION_SIZE_MISMATCH = 2
};

enum {
  M68K_REPRO_ATARI_FIELD_TEXT_SIZE = 1,
  M68K_REPRO_ATARI_FIELD_DATA_SIZE = 2,
  M68K_REPRO_ATARI_FIELD_BSS_SIZE = 3,
  M68K_REPRO_ATARI_FIELD_SYMBOL_SIZE = 4,
  M68K_REPRO_ATARI_FIELD_SYMBOL_TABLE_TYPE = 5,
  M68K_REPRO_ATARI_FIELD_FLAGS = 6,
  M68K_REPRO_ATARI_FIELD_RELOCATION_FLAG = 7
};

#define ATARI_PRG_HEADER_SIZE 28U
#define ATARI_PRG_MAGIC 0x601AU
#define HUNK_TYPE_ID_MASK 0x1FFFFFFFU
#define HUNK_MEM_SHIFT 30U
#define HUNK_HEADER 1011U
#define HUNK_CODE 1001U
#define HUNK_DATA 1002U
#define HUNK_BSS 1003U
#define HUNK_SYMBOL 1008U
#define HUNK_DEBUG 1009U
#define HUNK_END 1010U
#define HUNK_EXT 1007U
#define HUNK_RELOC32SHORT 1020U

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

static uint16_t compare_u16be(const unsigned char *data, size_t offset) {
  return (uint16_t)(((uint16_t)data[offset] << 8) | data[offset + 1U]);
}

static uint32_t compare_u32be(const unsigned char *data, size_t offset) {
  return ((uint32_t)data[offset] << 24) | ((uint32_t)data[offset + 1U] << 16) |
    ((uint32_t)data[offset + 2U] << 8) | (uint32_t)data[offset + 3U];
}

static int compare_read_u32be(const unsigned char *data, size_t size, size_t *pos, uint32_t *out) {
  if (data == NULL || pos == NULL || out == NULL || *pos > size || size - *pos < 4U) return -1;
  *out = compare_u32be(data, *pos);
  *pos += 4U;
  return 0;
}

static int compare_skip(size_t size, size_t *pos, size_t count) {
  if (pos == NULL || *pos > size || count > size - *pos) return -1;
  *pos += count;
  return 0;
}

static void compare_add_layout(M68kReproductionCompareResult *result, uint32_t kind_id,
    size_t file_start, size_t file_end, int has_section_index, uint32_t section_index,
    uint32_t section_offset_start) {
  M68kReproductionCompareLayoutRange *range;
  if (result == NULL || file_end <= file_start) return;
  if (result->layout_count >= M68K_REPRO_COMPARE_LAYOUT_CAPACITY) {
    result->layout_overflow = 1U;
    result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_UNSUPPORTED_CONTAINER_SHAPE;
    return;
  }
  range = &result->layout[result->layout_count++];
  range->kind_id = kind_id;
  range->file_start = compare_size_to_u32(file_start);
  range->file_end = compare_size_to_u32(file_end);
  range->has_section_index = has_section_index ? 1U : 0U;
  range->section_index = section_index;
  range->section_offset_start = section_offset_start;
}

static void compare_add_diagnostic(M68kReproductionCompareResult *result, uint32_t kind_id,
    uint32_t field_id, uint32_t original_value, uint32_t rebuilt_value) {
  M68kReproductionCompareDiagnostic *diagnostic;
  if (result == NULL) return;
  if (result->diagnostic_count >= M68K_REPRO_COMPARE_DIAGNOSTIC_CAPACITY) {
    result->diagnostic_overflow = 1U;
    return;
  }
  diagnostic = &result->diagnostics[result->diagnostic_count++];
  diagnostic->kind_id = kind_id;
  diagnostic->field_id = field_id;
  diagnostic->original_value = original_value;
  diagnostic->rebuilt_value = rebuilt_value;
}

static int hunk_relocation_long_type(uint32_t hunk_id) {
  return hunk_id == 1004U || hunk_id == 1005U || hunk_id == 1006U || hunk_id == 1015U ||
    hunk_id == 1016U || hunk_id == 1017U || hunk_id == 1021U || hunk_id == 1022U;
}

static int hunk_section_type(uint32_t hunk_id) {
  return hunk_id == HUNK_CODE || hunk_id == HUNK_DATA || hunk_id == HUNK_BSS;
}

static int hunk_ext_definition_type(uint32_t type) {
  return type == 0U || type == 1U || type == 2U || type == 3U;
}

static int hunk_ext_reference_type(uint32_t type) {
  return type == 129U || type == 130U || type == 131U || type == 132U || type == 133U ||
    type == 134U || type == 135U || type == 136U || type == 137U || type == 138U || type == 139U;
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

static void compare_add_source_hint(M68kReproductionCompareResult *result, uint32_t issue_group_flags,
    const M68kFixup *fixup) {
  M68kReproductionCompareSourceHint *hint;
  if (result == NULL || fixup == NULL || issue_group_flags == 0U) return;
  if (result->source_hint_count >= M68K_REPRO_COMPARE_SOURCE_HINT_CAPACITY) {
    result->source_hint_overflow = 1U;
    return;
  }
  hint = &result->source_hints[result->source_hint_count++];
  hint->issue_group_flags = issue_group_flags;
  hint->section_index = compare_size_to_u32(fixup->section_index);
  hint->offset = fixup->offset;
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

static int compare_skip_hunk_symbol_block(const unsigned char *data, size_t size, size_t *pos) {
  uint32_t name_longs;
  do {
    if (compare_read_u32be(data, size, pos, &name_longs) != 0) return -1;
    if (name_longs == 0U) return 0;
    if (compare_skip(size, pos, (size_t)name_longs * 4U + 4U) != 0) return -1;
  } while (1);
}

static int compare_skip_hunk_relocation_block(const unsigned char *data, size_t size, size_t *pos,
    int short_counts) {
  if (short_counts) {
    do {
      uint16_t count, target;
      if (*pos > size || size - *pos < 2U) return -1;
      count = compare_u16be(data, *pos);
      *pos += 2U;
      if (count == 0U) break;
      if (*pos > size || size - *pos < 2U) return -1;
      target = compare_u16be(data, *pos);
      (void)target;
      *pos += 2U;
      if (compare_skip(size, pos, (size_t)count * 2U) != 0) return -1;
    } while (1);
    return (*pos & 3U) != 0U ? compare_skip(size, pos, 2U) : 0;
  }
  do {
    uint32_t count, target;
    if (compare_read_u32be(data, size, pos, &count) != 0) return -1;
    if (count == 0U) return 0;
    if (compare_read_u32be(data, size, pos, &target) != 0) return -1;
    (void)target;
    if (compare_skip(size, pos, (size_t)count * 4U) != 0) return -1;
  } while (1);
}

static int compare_skip_hunk_ext_block(const unsigned char *data, size_t size, size_t *pos) {
  do {
    uint32_t tag, ext_type, name_longs;
    if (compare_read_u32be(data, size, pos, &tag) != 0) return -1;
    if (tag == 0U) return 0;
    ext_type = tag >> 24;
    name_longs = tag & 0xFFFFFFU;
    if (compare_skip(size, pos, (size_t)name_longs * 4U) != 0) return -1;
    if (hunk_ext_definition_type(ext_type)) {
      if (compare_skip(size, pos, 4U) != 0) return -1;
    } else if (hunk_ext_reference_type(ext_type)) {
      uint32_t count;
      if (ext_type == 130U || ext_type == 137U) {
        if (compare_skip(size, pos, 4U) != 0) return -1;
      }
      if (compare_read_u32be(data, size, pos, &count) != 0) return -1;
      if (compare_skip(size, pos, (size_t)count * 4U) != 0) return -1;
    }
  } while (1);
}

static void compare_collect_amiga_hunk_layout(M68kReproductionCompareResult *result,
    const unsigned char *data, size_t size) {
  size_t pos = 4U, header_end, section_index;
  uint32_t table_size, first_hunk, last_hunk, count;
  uint32_t header_mem_attrs[M68K_REPRO_COMPARE_LAYOUT_CAPACITY];
  if (size < 4U || compare_u32be(data, 0U) != HUNK_HEADER) {
    compare_add_layout(result, M68K_REPRO_LAYOUT_UNKNOWN, 0U, size, 0, 0U, 0U);
    return;
  }
  do {
    uint32_t longs;
    if (compare_read_u32be(data, size, &pos, &longs) != 0) goto malformed;
    if (compare_skip(size, &pos, (size_t)longs * 4U) != 0) goto malformed;
    if (longs == 0U) break;
  } while (1);
  if (compare_read_u32be(data, size, &pos, &table_size) != 0 ||
      compare_read_u32be(data, size, &pos, &first_hunk) != 0 ||
      compare_read_u32be(data, size, &pos, &last_hunk) != 0) goto malformed;
  count = last_hunk >= first_hunk ? last_hunk - first_hunk + 1U : table_size;
  if (count > M68K_REPRO_COMPARE_LAYOUT_CAPACITY) count = M68K_REPRO_COMPARE_LAYOUT_CAPACITY;
  for (section_index = 0U; section_index < count; ++section_index) {
    uint32_t size_word;
    header_mem_attrs[section_index] = 0U;
    if (compare_read_u32be(data, size, &pos, &size_word) != 0) goto malformed;
    if ((size_word >> HUNK_MEM_SHIFT) == 3U &&
        compare_read_u32be(data, size, &pos, &header_mem_attrs[section_index]) != 0) goto malformed;
  }
  header_end = pos;
  compare_add_layout(result, M68K_REPRO_LAYOUT_HEADER, 0U, header_end, 0, 0U, 0U);
  for (section_index = 0U; section_index < count && pos < size; ++section_index) {
    size_t section_start = pos, payload_start, payload_end;
    uint32_t raw_type, hunk_id, mem_type, size_longs;
    if (compare_read_u32be(data, size, &pos, &raw_type) != 0) goto malformed;
    hunk_id = raw_type & HUNK_TYPE_ID_MASK;
    if (!hunk_section_type(hunk_id)) {
      compare_add_layout(result, M68K_REPRO_LAYOUT_UNKNOWN, section_start, size, 0, 0U, 0U);
      return;
    }
    mem_type = raw_type >> HUNK_MEM_SHIFT;
    if (mem_type == 3U && header_mem_attrs[section_index] == 0U && compare_skip(size, &pos, 4U) != 0) goto malformed;
    if (compare_read_u32be(data, size, &pos, &size_longs) != 0) goto malformed;
    payload_start = pos;
    if (hunk_id == HUNK_CODE || hunk_id == HUNK_DATA) {
      if (compare_skip(size, &pos, (size_t)size_longs * 4U) != 0) goto malformed;
    }
    payload_end = pos;
    compare_add_layout(result, M68K_REPRO_LAYOUT_SECTION_HEADER, section_start, payload_start, 1,
      (uint32_t)section_index, 0U);
    if (payload_end > payload_start) {
      compare_add_layout(result, M68K_REPRO_LAYOUT_SECTION_PAYLOAD, payload_start, payload_end, 1,
        (uint32_t)section_index, 0U);
    }
    while (pos < size) {
      size_t record_start = pos;
      uint32_t raw, record_id, kind = M68K_REPRO_LAYOUT_UNKNOWN;
      if (compare_read_u32be(data, size, &pos, &raw) != 0) goto malformed;
      record_id = raw & HUNK_TYPE_ID_MASK;
      if (record_id == HUNK_END) {
        compare_add_layout(result, M68K_REPRO_LAYOUT_SECTION_END, record_start, pos, 1, (uint32_t)section_index, 0U);
        break;
      }
      if (record_id == HUNK_SYMBOL) {
        if (compare_skip_hunk_symbol_block(data, size, &pos) != 0) goto malformed;
        kind = M68K_REPRO_LAYOUT_SYMBOL;
      } else if (record_id == HUNK_DEBUG) {
        uint32_t longs;
        if (compare_read_u32be(data, size, &pos, &longs) != 0 ||
            compare_skip(size, &pos, (size_t)longs * 4U) != 0) goto malformed;
        kind = M68K_REPRO_LAYOUT_DEBUG;
      } else if (hunk_relocation_long_type(record_id) || record_id == HUNK_RELOC32SHORT) {
        if (compare_skip_hunk_relocation_block(data, size, &pos, record_id == HUNK_RELOC32SHORT) != 0) goto malformed;
        kind = M68K_REPRO_LAYOUT_RELOCATION;
      } else if (record_id == HUNK_EXT) {
        if (compare_skip_hunk_ext_block(data, size, &pos) != 0) goto malformed;
        kind = M68K_REPRO_LAYOUT_EXTERNAL;
      } else {
        uint32_t longs;
        if (compare_read_u32be(data, size, &pos, &longs) != 0 ||
            compare_skip(size, &pos, (size_t)longs * 4U) != 0) goto malformed;
      }
      compare_add_layout(result, kind, record_start, pos, 1, (uint32_t)section_index, 0U);
    }
  }
  return;
malformed:
  compare_add_layout(result, M68K_REPRO_LAYOUT_UNKNOWN, pos < size ? pos : 0U, size, 0, 0U, 0U);
}

static uint32_t compare_atari_field(const unsigned char *data, uint32_t field_id) {
  switch (field_id) {
  case M68K_REPRO_ATARI_FIELD_TEXT_SIZE: return compare_u32be(data, 2U);
  case M68K_REPRO_ATARI_FIELD_DATA_SIZE: return compare_u32be(data, 6U);
  case M68K_REPRO_ATARI_FIELD_BSS_SIZE: return compare_u32be(data, 10U);
  case M68K_REPRO_ATARI_FIELD_SYMBOL_SIZE: return compare_u32be(data, 14U);
  case M68K_REPRO_ATARI_FIELD_SYMBOL_TABLE_TYPE: return compare_u32be(data, 18U);
  case M68K_REPRO_ATARI_FIELD_FLAGS: return compare_u32be(data, 22U);
  case M68K_REPRO_ATARI_FIELD_RELOCATION_FLAG: return compare_u16be(data, 26U);
  default: return 0U;
  }
}

static size_t compare_atari_relocation_offset(const unsigned char *data, size_t size) {
  uint32_t text_size, data_size, symbol_size;
  if (size < ATARI_PRG_HEADER_SIZE || compare_u16be(data, 0U) != ATARI_PRG_MAGIC) return size;
  text_size = compare_u32be(data, 2U);
  data_size = compare_u32be(data, 6U);
  symbol_size = compare_u32be(data, 14U);
  return (size_t)ATARI_PRG_HEADER_SIZE + text_size + data_size + symbol_size;
}

static void compare_collect_atari_layout(M68kReproductionCompareResult *result,
    const unsigned char *data, size_t size) {
  size_t text_size, data_size, symbol_size, pos;
  if (size < ATARI_PRG_HEADER_SIZE || compare_u16be(data, 0U) != ATARI_PRG_MAGIC) {
    compare_add_layout(result, M68K_REPRO_LAYOUT_UNKNOWN, 0U, size, 0, 0U, 0U);
    return;
  }
  text_size = compare_u32be(data, 2U);
  data_size = compare_u32be(data, 6U);
  symbol_size = compare_u32be(data, 14U);
  compare_add_layout(result, M68K_REPRO_LAYOUT_HEADER, 0U, ATARI_PRG_HEADER_SIZE, 0, 0U, 0U);
  pos = ATARI_PRG_HEADER_SIZE;
  if (text_size != 0U) compare_add_layout(result, M68K_REPRO_LAYOUT_SECTION_PAYLOAD, pos, pos + text_size, 1, 0U, 0U);
  pos += text_size;
  if (data_size != 0U) compare_add_layout(result, M68K_REPRO_LAYOUT_SECTION_PAYLOAD, pos, pos + data_size, 1, 1U, 0U);
  pos += data_size;
  if (symbol_size != 0U) compare_add_layout(result, M68K_REPRO_LAYOUT_SYMBOL_TABLE, pos, pos + symbol_size, 0, 0U, 0U);
  pos += symbol_size;
  if (pos < size) compare_add_layout(result, M68K_REPRO_LAYOUT_RELOCATION, pos, size, 0, 0U, 0U);
}

static void compare_collect_atari_diagnostics(M68kReproductionCompareResult *result,
    const unsigned char *original_bytes, size_t original_size,
    const unsigned char *rebuilt_bytes, size_t rebuilt_size) {
  uint32_t field_id;
  size_t original_reloc_offset, rebuilt_reloc_offset, original_reloc_size, rebuilt_reloc_size;
  if (original_size < ATARI_PRG_HEADER_SIZE || rebuilt_size < ATARI_PRG_HEADER_SIZE ||
      compare_u16be(original_bytes, 0U) != ATARI_PRG_MAGIC || compare_u16be(rebuilt_bytes, 0U) != ATARI_PRG_MAGIC)
    return;
  for (field_id = M68K_REPRO_ATARI_FIELD_TEXT_SIZE; field_id <= M68K_REPRO_ATARI_FIELD_RELOCATION_FLAG; ++field_id) {
    uint32_t original_value = compare_atari_field(original_bytes, field_id);
    uint32_t rebuilt_value = compare_atari_field(rebuilt_bytes, field_id);
    if (original_value != rebuilt_value) {
      compare_add_diagnostic(result, M68K_REPRO_DIAG_ATARI_HEADER_FIELD_MISMATCH, field_id,
        original_value, rebuilt_value);
    }
  }
  original_reloc_offset = compare_atari_relocation_offset(original_bytes, original_size);
  rebuilt_reloc_offset = compare_atari_relocation_offset(rebuilt_bytes, rebuilt_size);
  original_reloc_size = original_size > original_reloc_offset ? original_size - original_reloc_offset : 0U;
  rebuilt_reloc_size = rebuilt_size > rebuilt_reloc_offset ? rebuilt_size - rebuilt_reloc_offset : 0U;
  if (original_reloc_size != rebuilt_reloc_size) {
    compare_add_diagnostic(result, M68K_REPRO_DIAG_ATARI_RELOCATION_SIZE_MISMATCH, 0U,
      compare_size_to_u32(original_reloc_size), compare_size_to_u32(rebuilt_reloc_size));
  }
}

static void compare_collect_container_layout(M68kReproductionCompareResult *result,
    M68kPlatformBackendKind backend_kind, const unsigned char *data, size_t size) {
  if (backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST) {
    compare_collect_atari_layout(result, data, size);
  } else if (backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    compare_collect_amiga_hunk_layout(result, data, size);
  }
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

static int objects_have_same_relocation_semantics(Arena *workflow_arena, const M68kObject *left,
    const M68kObject *right, uint32_t *out_container_shape_flags,
    M68kReproductionCompareResult *result) {
  ArenaMark scratch_mark;
  uint8_t *used;
  size_t left_index;
  uint32_t container_shape_flags = 0U;
  if (out_container_shape_flags != NULL) *out_container_shape_flags = 0U;
  if (left == NULL || right == NULL || left->fixup_count != right->fixup_count) return 0;
  if (left->fixup_count == 0U) return 1;
  if (workflow_arena == NULL) return 0;
  scratch_mark = arena_mark(workflow_arena);
  used = (uint8_t *)arena_calloc(workflow_arena, right->fixup_count, sizeof(*used));
  if (used == NULL) {
    arena_rewind(workflow_arena, scratch_mark);
    return 0;
  }
  for (left_index = 0U; left_index < left->fixup_count; ++left_index) {
    size_t right_index;
    int matched = 0;
    for (right_index = 0U; right_index < right->fixup_count; ++right_index) {
      if (used[right_index]) continue;
      if (!fixups_have_same_semantics(left, &left->fixups[left_index], right, &right->fixups[right_index]))
        continue;
      used[right_index] = 1U;
      {
        uint32_t fixup_shape_flags = 0U;
        if (!fixups_have_same_container_shape(&left->fixups[left_index], &right->fixups[right_index])) {
          fixup_shape_flags = fixup_container_shape_diff_flags(left_index, right_index,
            &left->fixups[left_index], &right->fixups[right_index]);
        } else if (left_index != right_index) {
          fixup_shape_flags = M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ORDER_DIFF;
        }
        container_shape_flags |= fixup_shape_flags;
        compare_add_source_hint(result, fixup_shape_flags, &left->fixups[left_index]);
      }
      matched = 1;
      break;
    }
    if (!matched) {
      arena_rewind(workflow_arena, scratch_mark);
      return 0;
    }
  }
  arena_rewind(workflow_arena, scratch_mark);
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
      context->rebuilt_bytes == NULL || context->workflow_arena == NULL) {
    if (result != NULL) {
      result->status_id = M68K_REPRO_COMPARE_STATUS_INVALID_ARGUMENT;
      result->diagnostic_id = M68K_REPRO_COMPARE_DIAG_INVALID_ARGUMENT;
    }
    return -1;
  }
  result->status_id = M68K_REPRO_COMPARE_STATUS_MISMATCH;
  result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_MISMATCH;
  compare_collect_container_layout(result, context->backend_kind, context->original_bytes, context->original_size);
  if (context->original_size == context->rebuilt_size &&
      (context->original_size == 0U ||
       memcmp(context->original_bytes, context->rebuilt_bytes, context->original_size) == 0)) {
    result->status_id = M68K_REPRO_COMPARE_STATUS_FULL_FILE_EXACT;
    result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE;
    return 0;
  }
  compare_collect_byte_diffs(result, context->original_bytes, context->original_size,
    context->rebuilt_bytes, context->rebuilt_size);
  if (context->backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST) {
    compare_collect_atari_diagnostics(result, context->original_bytes, context->original_size,
      context->rebuilt_bytes, context->rebuilt_size);
  }
  result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF;
  if (object_has_unsupported_container_shape(context->original_object) ||
      object_has_unsupported_container_shape(context->rebuilt_object))
    result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_UNSUPPORTED_CONTAINER_SHAPE;
  if ((context->backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
       context->backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST) &&
      objects_have_same_payload_semantics(context->original_object, context->rebuilt_object)) {
    uint32_t relocation_shape_flags = 0U;
    result->issue_group_flags &= ~M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF;
    if (!objects_have_same_relocation_semantics(context->workflow_arena, context->original_object,
        context->rebuilt_object, &relocation_shape_flags, result)) {
      result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_RELOCATION_DIFF;
      return 0;
    }
    result->status_id = M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT;
    result->exactness_id = M68K_REPRO_COMPARE_EXACTNESS_CONTENT;
    result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF;
    result->issue_group_flags |= relocation_shape_flags;
    if (context->assembler_policy != NULL &&
        (((context->assembler_policy->flags & M68K_ASSEMBLER_POLICY_PRESERVE_HUNK_RELOCATION_ENCODING) != 0U &&
          relocation_shape_flags != 0U) ||
         (context->assembler_policy->flags & M68K_ASSEMBLER_POLICY_PRESERVE_ATARI_ST_CONTAINER_ENCODING) != 0U))
      result->issue_group_flags |= M68K_REPRO_COMPARE_ISSUE_POLICY_DIVERGENCE;
  }
  return 0;
}
