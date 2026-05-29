#include "m68k_backend.h"
#include "m68k_assembler_policy.h"
#include "m68k_c_unit_test.h"
#include "m68k_reproduction_compare.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/atari_st_prg_file_runtime.h"

#include <stdlib.h>
#include <string.h>

static int add_compare_code_section(M68kObject *object, const unsigned char *payload, uint32_t size) {
  M68kSection section;
  memset(&section, 0, sizeof(section));
  section.kind = M68K_SECTION_CODE;
  section.size = size;
  section.data = (uint8_t *)payload;
  section.data_size = size;
  return m68k_object_add_section(object, &section).ok ? 0 : -1;
}

static int add_compare_section_fixup(M68kObject *object, uint32_t offset, uint32_t target_section,
    uint32_t record_kind, uint32_t wire_id, uint32_t block_index, uint32_t group_index) {
  M68kFixup fixup;
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 0U;
  fixup.offset = offset;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = target_section;
  fixup.has_target_section = 1;
  fixup.platform_relocation_record_kind = record_kind;
  fixup.platform_relocation_record_wire_id = wire_id;
  fixup.platform_relocation_block_index = block_index;
  fixup.platform_relocation_group_index = group_index;
  return m68k_object_add_fixup(object, &fixup).ok ? 0 : -1;
}

static int run_reproduction_compare_for_test(M68kReproductionCompareContext *context,
    M68kReproductionCompareResult *result) {
  Arena *arena = arena_create(4096U);
  int compare_result;
  if (arena == NULL) return -1;
  context->workflow_arena = arena;
  compare_result = m68k_reproduction_compare(context, result);
  context->workflow_arena = NULL;
  arena_destroy(arena);
  return compare_result;
}

static int test_container_metadata_tracks_overflow_separately(void) {
  M68kObject object;
  uint32_t i;
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  for (i = 0; i < M68K_CONTAINER_METADATA_CAPACITY + 1U; ++i) {
    m68k_object_add_container_layout(&object, M68K_CONTAINER_LAYOUT_AMIGA_HUNK_SECTION, 0U, i, 0U);
  }
  M68K_C_ASSERT_U32(M68K_CONTAINER_METADATA_CAPACITY, object.container_metadata.layout_count);
  M68K_C_ASSERT_U32(1U, object.container_metadata.layout_overflow);
  M68K_C_ASSERT_U32(0U, object.container_metadata.encoding_overflow);
  for (i = 0; i < M68K_CONTAINER_METADATA_CAPACITY + 1U; ++i) {
    m68k_object_add_container_encoding(&object, M68K_CONTAINER_ENCODING_AMIGA_HUNK_RECORD_WIRE_ID, 0U, i, 0U);
  }
  M68K_C_ASSERT_U32(M68K_CONTAINER_METADATA_CAPACITY, object.container_metadata.encoding_count);
  M68K_C_ASSERT_U32(1U, object.container_metadata.layout_overflow);
  M68K_C_ASSERT_U32(1U, object.container_metadata.encoding_overflow);
  m68k_object_destroy(&object);
  return 0;
}

static int test_no_container_metadata_uses_numeric_ids(void) {
  M68kObject object;
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  m68k_object_mark_no_container(&object);
  M68K_C_ASSERT_U32(1U, object.container_metadata.layout_count);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_NO_CONTAINER, object.container_metadata.layout[0].kind);
  M68K_C_ASSERT_U32(0U, object.container_metadata.layout[0].id);
  M68K_C_ASSERT_U32(1U, object.container_metadata.encoding_count);
  M68K_C_ASSERT_U32(M68K_CONTAINER_ENCODING_NO_CONTAINER, object.container_metadata.encoding[0].kind);
  M68K_C_ASSERT_U32(0U, object.container_metadata.encoding[0].id);
  m68k_object_destroy(&object);
  return 0;
}

static int test_backend_definitions_expose_platform_ids(void) {
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_AMIGA_HUNK, M68K_BACKEND_AMIGA_HUNK.platform_kind);
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_ATARI_ST, M68K_BACKEND_ATARI_ST.platform_kind);
  M68K_C_ASSERT(m68k_backend_by_name(M68K_BACKEND_AMIGA_HUNK.name) == &M68K_BACKEND_AMIGA_HUNK);
  M68K_C_ASSERT(m68k_backend_by_name(M68K_BACKEND_ATARI_ST.name) == &M68K_BACKEND_ATARI_ST);
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_AMIGA_HUNK, m68k_backend_kind_by_name("amiga-hunk"));
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_ATARI_ST, m68k_backend_kind_by_name("atari-st"));
  M68K_C_ASSERT(m68k_raw_backend_by_name("amiga-raw") == &M68K_BACKEND_AMIGA_HUNK);
  M68K_C_ASSERT(m68k_raw_backend_by_name("atari-st-raw") == &M68K_BACKEND_ATARI_ST);
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_AMIGA_HUNK, m68k_backend_kind_by_platform_name("amiga-raw"));
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_ATARI_ST, m68k_backend_kind_by_platform_name("atari-st-raw"));
  return 0;
}

static int test_hunk_runtime_metadata_covers_reproduction_compare_categories(void) {
  const AmigaHunkFileRecordInfo *record;
  const AmigaHunkFileRelocationKind *reloc;
  const AmigaHunkFileExtVariantInfo *ext;
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_HEADER);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_HEADER, record->record_kind);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_ROLE_CONTAINER_HEADER, record->role);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_CODE);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_ROLE_SECTION_START, record->role);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_SECTION_KIND_CODE, record->section_kind);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DATA);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_SECTION_KIND_DATA, record->section_kind);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_BSS);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_SECTION_KIND_BSS, record->section_kind);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_END);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_ROLE_SECTION_TERMINATOR, record->role);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_SYMBOL);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_SYMBOL, record->record_kind);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_DEBUG);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DEBUG, record->record_kind);
  record = amiga_hunk_file_record_info_by_wire_id(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_EXT);
  M68K_C_ASSERT(record != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_EXT, record->record_kind);
  reloc = amiga_hunk_file_relocation_kind_lookup(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32);
  M68K_C_ASSERT(reloc != NULL);
  M68K_C_ASSERT_U32(4U, reloc->width_bytes);
  reloc = amiga_hunk_file_relocation_kind_lookup(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32SHORT);
  M68K_C_ASSERT(reloc != NULL);
  M68K_C_ASSERT_U32(4U, reloc->width_bytes);
  ext = amiga_hunk_file_ext_variant_lookup(AMIGA_HUNK_FILE_EXT_TYPE_EXT_DEF);
  M68K_C_ASSERT(ext != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_EXT_VARIANT_DEFINITION, ext->variant);
  ext = amiga_hunk_file_ext_variant_lookup(AMIGA_HUNK_FILE_EXT_TYPE_EXT_REF32);
  M68K_C_ASSERT(ext != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_EXT_VARIANT_REFERENCE, ext->variant);
  ext = amiga_hunk_file_ext_variant_lookup(AMIGA_HUNK_FILE_EXT_TYPE_EXT_COMMON);
  M68K_C_ASSERT(ext != NULL);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_EXT_VARIANT_COMMON_REFERENCE, ext->variant);
  return 0;
}

static int test_hunk_loader_records_payload_and_relocation_metadata(void) {
  static const unsigned char hunk[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x03, 0xE9,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xEC,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.read_buffer(hunk, sizeof(hunk), &object, m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(3U, object.container_metadata.layout_count);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_AMIGA_HUNK_CONTAINER, object.container_metadata.layout[0].kind);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_CONTAINER_KIND_EXECUTABLE, object.container_metadata.layout[0].id);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_AMIGA_HUNK_SECTION, object.container_metadata.layout[1].kind);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_FLAG_PAYLOAD, object.container_metadata.layout[1].flags);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_CODE, object.container_metadata.layout[1].id);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_AMIGA_HUNK_RELOCATION_BLOCK, object.container_metadata.layout[2].kind);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_FLAG_RELOCATION, object.container_metadata.layout[2].flags);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, object.container_metadata.layout[2].id);
  M68K_C_ASSERT_U32(3U, object.container_metadata.encoding_count);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_HEADER, object.container_metadata.encoding[0].id);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_CODE, object.container_metadata.encoding[1].id);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, object.container_metadata.encoding[2].id);
  m68k_object_destroy(&object);
  return 0;
}

static int test_hunk_loader_applies_executable_header_memory_flags_to_sections(void) {
  static const unsigned char hunk[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x40, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x03, 0xEB,
    0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  unsigned char *rebuilt = NULL;
  size_t rebuilt_size = 0U;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.read_buffer(hunk, sizeof(hunk), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(1U, (uint32_t)object.section_count);
  M68K_C_ASSERT_U32(M68K_SECTION_BSS, object.sections[0].kind);
  M68K_C_ASSERT_U32(8U, object.sections[0].size);
  M68K_C_ASSERT_U32(1U, object.sections[0].platform_mem_type);
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.write_buffer(&object, &rebuilt, &rebuilt_size,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(sizeof(hunk), (uint32_t)rebuilt_size);
  M68K_C_ASSERT(memcmp(hunk, rebuilt, sizeof(hunk)) == 0);
  free(rebuilt);
  m68k_object_destroy(&object);
  return 0;
}

static int test_hunk_writer_encodes_source_executable_memory_flags_in_header_table(void) {
  static const unsigned char expected[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x40, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x03, 0xEB,
    0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kSection section;
  M68kDiagList diagnostics;
  unsigned char *rebuilt = NULL;
  size_t rebuilt_size = 0U;
  m68k_diag_list_reset(&diagnostics);
  memset(&section, 0, sizeof(section));
  section.kind = M68K_SECTION_BSS;
  section.platform_mem_type = 1U;
  section.size = 8U;
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  M68K_C_ASSERT(m68k_object_add_section(&object, &section).ok);
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.write_buffer(&object, &rebuilt, &rebuilt_size,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(sizeof(expected), (uint32_t)rebuilt_size);
  M68K_C_ASSERT(memcmp(expected, rebuilt, sizeof(expected)) == 0);
  free(rebuilt);
  m68k_object_destroy(&object);
  return 0;
}

static int test_hunk_parser_result_survives_workflow_teardown(void) {
  static const unsigned char hunk[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x03, 0xE9,
    0x00, 0x00, 0x00, 0x01,
    0x4E, 0x75, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.read_buffer(hunk, sizeof(hunk), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(1U, (uint32_t)object.section_count);
  M68K_C_ASSERT(object.sections[0].data != NULL);
  M68K_C_ASSERT_U32(4U, object.sections[0].data_size);
  M68K_C_ASSERT_U32(0x4EU, object.sections[0].data[0]);
  M68K_C_ASSERT_U32(0x75U, object.sections[0].data[1]);
  m68k_object_destroy(&object);
  M68K_C_ASSERT(object.arena == NULL);
  M68K_C_ASSERT(object.sections == NULL);
  M68K_C_ASSERT_U32(0U, (uint32_t)object.section_count);
  return 0;
}

static int test_hunk_writer_preserves_trailing_hunk_end(void) {
  static const unsigned char hunk[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x03, 0xE9,
    0x00, 0x00, 0x00, 0x01,
    0x4E, 0x75, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xF2,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  unsigned char *rebuilt = NULL;
  size_t rebuilt_size = 0U;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.read_buffer(hunk, sizeof(hunk), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.write_buffer(&object, &rebuilt, &rebuilt_size,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(sizeof(hunk), (uint32_t)rebuilt_size);
  M68K_C_ASSERT(memcmp(hunk, rebuilt, sizeof(hunk)) == 0);
  free(rebuilt);
  m68k_object_destroy(&object);
  return 0;
}

static int test_hunk_loader_rejects_overlay_as_explicit_unsupported(void) {
  static const unsigned char hunk[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xE9,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xF5,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(-1, M68K_BACKEND_AMIGA_HUNK.read_buffer(hunk, sizeof(hunk), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_STR("Unsupported HUNK_OVERLAY record", m68k_diag_first_message(&diagnostics));
  m68k_object_destroy(&object);
  return 0;
}

static int test_ideal_assembler_policy_has_no_preservation_metadata(void) {
  M68kAssemblerPolicy policy;
  m68k_assembler_policy_init_ideal(&policy);
  M68K_C_ASSERT_U32(M68K_ASSEMBLER_POLICY_IDEAL, policy.kind);
  M68K_C_ASSERT_U32(0U, policy.flags);
  M68K_C_ASSERT_U32(0U, policy.hunk_relocation_record_count);
  return 0;
}

static int test_preservation_policy_derives_hunk_relocation_encoding_ids(void) {
  M68kObject object;
  M68kAssemblerPolicy policy;
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  m68k_object_add_container_layout(&object, M68K_CONTAINER_LAYOUT_AMIGA_HUNK_CONTAINER,
    M68K_CONTAINER_LAYOUT_FLAG_HEADER, AMIGA_HUNK_FILE_META_CONTAINER_KIND_EXECUTABLE, 0U);
  m68k_object_add_container_encoding(&object, M68K_CONTAINER_ENCODING_AMIGA_HUNK_RELOCATION_WIRE_ID,
    M68K_CONTAINER_LAYOUT_FLAG_RELOCATION, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32SHORT, 1U);

  m68k_assembler_policy_derive_preservation(&object, &policy);

  M68K_C_ASSERT_U32(M68K_ASSEMBLER_POLICY_PRESERVE_ORIGINAL, policy.kind);
  M68K_C_ASSERT_U32(M68K_PLATFORM_BACKEND_AMIGA_HUNK, policy.platform_backend_kind);
  M68K_C_ASSERT((policy.flags & M68K_ASSEMBLER_POLICY_PRESERVE_CONTAINER_LAYOUT) != 0U);
  M68K_C_ASSERT((policy.flags & M68K_ASSEMBLER_POLICY_PRESERVE_CONTAINER_ENCODING) != 0U);
  M68K_C_ASSERT((policy.flags & M68K_ASSEMBLER_POLICY_PRESERVE_HUNK_RELOCATION_ENCODING) != 0U);
  M68K_C_ASSERT_U32(1U, policy.hunk_relocation_record_count);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32SHORT, policy.hunk_relocation_record_wire_ids[0]);
  m68k_object_destroy(&object);
  return 0;
}

static int test_no_container_preservation_policy_does_not_claim_container_shape(void) {
  M68kObject object;
  M68kAssemblerPolicy policy;
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  m68k_object_mark_no_container(&object);

  m68k_assembler_policy_derive_preservation(&object, &policy);

  M68K_C_ASSERT_U32(M68K_ASSEMBLER_POLICY_PRESERVE_ORIGINAL, policy.kind);
  M68K_C_ASSERT_U32(0U, policy.flags);
  M68K_C_ASSERT_U32(0U, policy.hunk_relocation_record_count);
  m68k_object_destroy(&object);
  return 0;
}

static int test_hunk_writer_preserves_policy_allowed_relocation_record_grouping(void) {
  static const unsigned char hunk[] = {
    0x00, 0x00, 0x03, 0xF3,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x03, 0xE9,
    0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x04,
    0x00, 0x00, 0x03, 0xFC,
    0x00, 0x01, 0x00, 0x00,
    0x00, 0x00,
    0x00, 0x01, 0x00, 0x00,
    0x00, 0x04,
    0x00, 0x00,
    0x00, 0x00,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  unsigned char *rebuilt = NULL;
  size_t rebuilt_size = 0U;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.read_buffer(hunk, sizeof(hunk), &object, m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.write_buffer(&object, &rebuilt, &rebuilt_size,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(sizeof(hunk), (uint32_t)rebuilt_size);
  M68K_C_ASSERT(memcmp(hunk, rebuilt, sizeof(hunk)) == 0);
  free(rebuilt);
  m68k_object_destroy(&object);
  return 0;
}

static int test_reproduction_compare_raw_exact_and_grouped_mismatch(void) {
  static const unsigned char original[] = {1U, 2U, 3U, 4U, 5U, 6U};
  static const unsigned char rebuilt[] = {1U, 9U, 9U, 4U, 8U};
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  memset(&context, 0, sizeof(context));
  context.original_bytes = original;
  context.original_size = sizeof(original);
  context.rebuilt_bytes = original;
  context.rebuilt_size = sizeof(original);
  context.backend_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_FULL_FILE_EXACT, result.status_id);
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE, result.exactness_id);
  M68K_C_ASSERT_U32(0U, result.issue_group_flags);

  context.rebuilt_bytes = rebuilt;
  context.rebuilt_size = sizeof(rebuilt);
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_MISMATCH, result.status_id);
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_EXACTNESS_MISMATCH, result.exactness_id);
  M68K_C_ASSERT_U32(1U, result.has_first_diff);
  M68K_C_ASSERT_U32(1U, result.first_diff_offset);
  M68K_C_ASSERT_U32(2U, result.first_diff_original_byte);
  M68K_C_ASSERT_U32(9U, result.first_diff_rebuilt_byte);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_SIZE_DIFF) != 0U);
  M68K_C_ASSERT_U32(2U, result.range_count);
  M68K_C_ASSERT_U32(1U, result.ranges[0].original_offset);
  M68K_C_ASSERT_U32(2U, result.ranges[0].original_size);
  M68K_C_ASSERT_U32(4U, result.ranges[1].original_offset);
  M68K_C_ASSERT_U32(2U, result.ranges[1].original_size);
  M68K_C_ASSERT_U32(1U, result.ranges[1].rebuilt_size);
  return 0;
}

static int test_reproduction_compare_hunk_content_exact_container_difference(void) {
  static const unsigned char original_bytes[] = {0U, 0U, 3U, 0xF3U};
  static const unsigned char rebuilt_bytes[] = {0U, 0U, 3U, 0xE9U};
  static const unsigned char payload[] = {0x4EU, 0x75U, 0U, 0U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kSection section;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  memset(&section, 0, sizeof(section));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(payload);
  section.data = (uint8_t *)payload;
  section.data_size = sizeof(payload);
  M68K_C_ASSERT(m68k_object_add_section(&original_object, &section).ok);
  M68K_C_ASSERT(m68k_object_add_section(&rebuilt_object, &section).ok);
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT, result.status_id);
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_EXACTNESS_CONTENT, result.exactness_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF) == 0U);
  M68K_C_ASSERT_U32(1U, result.range_count);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

static int test_reproduction_compare_hunk_exact_match_reports_full_file_exact(void) {
  static const unsigned char bytes[] = {0U, 0U, 3U, 0xF3U};
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  memset(&context, 0, sizeof(context));
  context.original_bytes = bytes;
  context.original_size = sizeof(bytes);
  context.rebuilt_bytes = bytes;
  context.rebuilt_size = sizeof(bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_FULL_FILE_EXACT, result.status_id);
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE, result.exactness_id);
  M68K_C_ASSERT_U32(0U, result.issue_group_flags);
  return 0;
}

static int test_reproduction_compare_hunk_changed_fixup_set_blocks_content_exact(void) {
  static const unsigned char original_bytes[] = {0U, 0U, 3U, 0xF3U};
  static const unsigned char rebuilt_bytes[] = {0U, 0U, 3U, 0xE9U};
  static const unsigned char payload[] = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&original_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&rebuilt_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&original_object, 0U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&rebuilt_object, 4U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_MISMATCH, result.status_id);
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_EXACTNESS_MISMATCH, result.exactness_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_RELOCATION_DIFF) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF) == 0U);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

static int test_reproduction_compare_hunk_reordered_fixups_are_file_structure_issue(void) {
  static const unsigned char original_bytes[] = {0U, 0U, 3U, 0xF3U};
  static const unsigned char rebuilt_bytes[] = {0U, 0U, 3U, 0xE9U};
  static const unsigned char payload[] = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&original_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&rebuilt_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&original_object, 0U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&original_object, 4U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&rebuilt_object, 4U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&rebuilt_object, 0U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT, result.status_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ORDER_DIFF) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_RELOCATION_DIFF) == 0U);
  M68K_C_ASSERT_U32(2U, result.source_hint_count);
  M68K_C_ASSERT((result.source_hints[0].issue_group_flags &
    M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ORDER_DIFF) != 0U);
  M68K_C_ASSERT_U32(0U, result.source_hints[0].section_index);
  M68K_C_ASSERT_U32(0U, result.source_hints[0].offset);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

static int test_reproduction_compare_hunk_regrouped_fixups_reports_policy_divergence(void) {
  static const unsigned char original_bytes[] = {0U, 0U, 3U, 0xF3U};
  static const unsigned char rebuilt_bytes[] = {0U, 0U, 3U, 0xE9U};
  static const unsigned char payload[] = {0U, 0U, 0U, 0U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kAssemblerPolicy policy;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&original_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&rebuilt_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&original_object, 0U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 1U, 1U));
  M68K_C_ASSERT_INT(0, add_compare_section_fixup(&rebuilt_object, 0U, 0U,
    AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32, AMIGA_HUNK_FILE_HUNK_TYPE_HUNK_RELOC32, 2U, 2U));
  m68k_assembler_policy_init_ideal(&policy);
  policy.flags = M68K_ASSEMBLER_POLICY_PRESERVE_HUNK_RELOCATION_ENCODING;
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  context.assembler_policy = &policy;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT, result.status_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_GROUP_DIFF) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_POLICY_DIVERGENCE) != 0U);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

static int test_reproduction_compare_hunk_unsupported_container_shape_is_distinct(void) {
  static const unsigned char original_bytes[] = {0U, 0U, 3U, 0xF3U};
  static const unsigned char rebuilt_bytes[] = {0U, 0U, 3U, 0xE9U};
  static const unsigned char payload[] = {0U, 0U, 0U, 0U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&original_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&rebuilt_object, payload, sizeof(payload)));
  original_object.container_metadata.encoding_overflow = 1U;
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT, result.status_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_UNSUPPORTED_CONTAINER_SHAPE) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_POLICY_DIVERGENCE) == 0U);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

static int test_reproduction_compare_reports_unsupported_shape_with_payload_mismatch(void) {
  static const unsigned char original_bytes[] = {0x00U, 0x01U};
  static const unsigned char rebuilt_bytes[] = {0x00U, 0x02U};
  static const unsigned char original_payload[] = {0x4EU, 0x75U};
  static const unsigned char rebuilt_payload[] = {0x4EU, 0x76U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&original_object, original_payload, sizeof(original_payload)));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&rebuilt_object, rebuilt_payload, sizeof(rebuilt_payload)));
  original_object.container_metadata.encoding_overflow = 1U;
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_MISMATCH, result.status_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_UNSUPPORTED_CONTAINER_SHAPE) != 0U);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

static int test_atari_loader_records_header_and_eof_relocation_metadata(void) {
  static const unsigned char prg[] = {
    0x60, 0x1A,
    0x00, 0x00, 0x00, 0x08,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x07,
    0x00, 0x00, 0x12, 0x34,
    0xFF, 0xFF,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x04,
  };
  M68kObject object;
  M68kAssemblerPolicy policy;
  M68kDiagList diagnostics;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_ATARI_ST.read_buffer(prg, sizeof(prg), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_ATARI_ST_PRG_CONTAINER, object.container_metadata.layout[0].kind);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_ATARI_ST_PRG_HEADER, object.container_metadata.layout[1].kind);
  M68K_C_ASSERT_U32(M68K_CONTAINER_LAYOUT_ATARI_ST_PRG_RELOCATION_STREAM, object.container_metadata.layout[2].kind);
  M68K_C_ASSERT_U32(M68K_CONTAINER_ENCODING_ATARI_ST_PRG_HEADER_FIELD,
    object.container_metadata.encoding[0].kind);
  M68K_C_ASSERT_U32(ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_SYMBOL_TABLE_TYPE_OFFSET,
    object.container_metadata.encoding[0].id);
  M68K_C_ASSERT_U32(7U, object.container_metadata.encoding[0].aux);
  M68K_C_ASSERT_U32(M68K_CONTAINER_ENCODING_ATARI_ST_PRG_RELOCATION_TERMINATOR,
    object.container_metadata.encoding[3].kind);
  M68K_C_ASSERT_U32(M68K_ATARI_ST_PRG_RELOCATION_TERMINATOR_EOF,
    object.container_metadata.encoding[3].id);
  m68k_assembler_policy_derive_preservation(&object, &policy);
  M68K_C_ASSERT((policy.flags & M68K_ASSEMBLER_POLICY_PRESERVE_ATARI_ST_CONTAINER_ENCODING) != 0U);
  m68k_object_destroy(&object);
  return 0;
}

static int test_atari_writer_preserves_eof_relocation_terminator(void) {
  static const unsigned char prg[] = {
    0x60, 0x1A,
    0x00, 0x00, 0x00, 0x08,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x07,
    0x00, 0x00, 0x12, 0x34,
    0xFF, 0xFF,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x04,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  unsigned char *rebuilt = NULL;
  size_t rebuilt_size = 0U;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_ATARI_ST.read_buffer(prg, sizeof(prg), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_ATARI_ST.write_buffer(&object, &rebuilt, &rebuilt_size,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(sizeof(prg), (uint32_t)rebuilt_size);
  M68K_C_ASSERT(memcmp(prg, rebuilt, sizeof(prg)) == 0);
  free(rebuilt);
  m68k_object_destroy(&object);
  return 0;
}

static int test_reproduction_compare_atari_content_exact_reports_policy_divergence(void) {
  static const unsigned char original_bytes[] = {0x60U, 0x1AU, 0U, 1U};
  static const unsigned char rebuilt_bytes[] = {0x60U, 0x1AU, 0U, 2U};
  static const unsigned char payload[] = {0x4EU, 0x75U};
  M68kObject original_object;
  M68kObject rebuilt_object;
  M68kAssemblerPolicy policy;
  M68kReproductionCompareContext context;
  M68kReproductionCompareResult result;
  M68K_C_ASSERT_INT(0, m68k_object_create(&original_object));
  M68K_C_ASSERT_INT(0, m68k_object_create(&rebuilt_object));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&original_object, payload, sizeof(payload)));
  M68K_C_ASSERT_INT(0, add_compare_code_section(&rebuilt_object, payload, sizeof(payload)));
  m68k_assembler_policy_init_ideal(&policy);
  policy.flags = M68K_ASSEMBLER_POLICY_PRESERVE_ATARI_ST_CONTAINER_ENCODING;
  memset(&context, 0, sizeof(context));
  context.original_bytes = original_bytes;
  context.original_size = sizeof(original_bytes);
  context.rebuilt_bytes = rebuilt_bytes;
  context.rebuilt_size = sizeof(rebuilt_bytes);
  context.backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  context.assembler_policy = &policy;
  context.original_object = &original_object;
  context.rebuilt_object = &rebuilt_object;
  M68K_C_ASSERT_INT(0, run_reproduction_compare_for_test(&context, &result));
  M68K_C_ASSERT_U32(M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT, result.status_id);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_POLICY_DIVERGENCE) != 0U);
  M68K_C_ASSERT((result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF) != 0U);
  m68k_object_destroy(&rebuilt_object);
  m68k_object_destroy(&original_object);
  return 0;
}

int m68k_c_container_metadata_tests(void) {
  static const M68kCTestCase cases[] = {
    {"container_metadata_tracks_overflow_separately", test_container_metadata_tracks_overflow_separately},
    {"no_container_metadata_uses_numeric_ids", test_no_container_metadata_uses_numeric_ids},
    {"backend_definitions_expose_platform_ids", test_backend_definitions_expose_platform_ids},
    {"hunk_runtime_metadata_covers_reproduction_compare_categories",
      test_hunk_runtime_metadata_covers_reproduction_compare_categories},
    {"hunk_loader_records_payload_and_relocation_metadata", test_hunk_loader_records_payload_and_relocation_metadata},
    {"hunk_loader_applies_executable_header_memory_flags_to_sections",
      test_hunk_loader_applies_executable_header_memory_flags_to_sections},
    {"hunk_writer_encodes_source_executable_memory_flags_in_header_table",
      test_hunk_writer_encodes_source_executable_memory_flags_in_header_table},
    {"hunk_parser_result_survives_workflow_teardown", test_hunk_parser_result_survives_workflow_teardown},
    {"hunk_writer_preserves_trailing_hunk_end", test_hunk_writer_preserves_trailing_hunk_end},
    {"hunk_loader_rejects_overlay_as_explicit_unsupported",
      test_hunk_loader_rejects_overlay_as_explicit_unsupported},
    {"ideal_assembler_policy_has_no_preservation_metadata", test_ideal_assembler_policy_has_no_preservation_metadata},
    {"preservation_policy_derives_hunk_relocation_encoding_ids",
      test_preservation_policy_derives_hunk_relocation_encoding_ids},
    {"no_container_preservation_policy_does_not_claim_container_shape",
      test_no_container_preservation_policy_does_not_claim_container_shape},
    {"hunk_writer_preserves_policy_allowed_relocation_record_grouping",
      test_hunk_writer_preserves_policy_allowed_relocation_record_grouping},
    {"reproduction_compare_raw_exact_and_grouped_mismatch",
      test_reproduction_compare_raw_exact_and_grouped_mismatch},
    {"reproduction_compare_hunk_content_exact_container_difference",
      test_reproduction_compare_hunk_content_exact_container_difference},
    {"reproduction_compare_hunk_exact_match_reports_full_file_exact",
      test_reproduction_compare_hunk_exact_match_reports_full_file_exact},
    {"reproduction_compare_hunk_changed_fixup_set_blocks_content_exact",
      test_reproduction_compare_hunk_changed_fixup_set_blocks_content_exact},
    {"reproduction_compare_hunk_reordered_fixups_are_file_structure_issue",
      test_reproduction_compare_hunk_reordered_fixups_are_file_structure_issue},
    {"reproduction_compare_hunk_regrouped_fixups_reports_policy_divergence",
      test_reproduction_compare_hunk_regrouped_fixups_reports_policy_divergence},
    {"reproduction_compare_hunk_unsupported_container_shape_is_distinct",
      test_reproduction_compare_hunk_unsupported_container_shape_is_distinct},
    {"reproduction_compare_reports_unsupported_shape_with_payload_mismatch",
      test_reproduction_compare_reports_unsupported_shape_with_payload_mismatch},
    {"atari_loader_records_header_and_eof_relocation_metadata",
      test_atari_loader_records_header_and_eof_relocation_metadata},
    {"atari_writer_preserves_eof_relocation_terminator",
      test_atari_writer_preserves_eof_relocation_terminator},
    {"reproduction_compare_atari_content_exact_reports_policy_divergence",
      test_reproduction_compare_atari_content_exact_reports_policy_divergence},
  };
  return m68k_c_test_run_suite("container_metadata", cases, sizeof(cases) / sizeof(cases[0]));
}
