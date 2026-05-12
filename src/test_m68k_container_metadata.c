#include "m68k_backend.h"
#include "m68k_assembler_policy.h"
#include "m68k_c_unit_test.h"
#include "generated/amiga_hunk_file_runtime.h"

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

int m68k_c_container_metadata_tests(void) {
  static const M68kCTestCase cases[] = {
    {"container_metadata_tracks_overflow_separately", test_container_metadata_tracks_overflow_separately},
    {"no_container_metadata_uses_numeric_ids", test_no_container_metadata_uses_numeric_ids},
    {"hunk_loader_records_payload_and_relocation_metadata", test_hunk_loader_records_payload_and_relocation_metadata},
    {"ideal_assembler_policy_has_no_preservation_metadata", test_ideal_assembler_policy_has_no_preservation_metadata},
    {"preservation_policy_derives_hunk_relocation_encoding_ids",
      test_preservation_policy_derives_hunk_relocation_encoding_ids},
    {"no_container_preservation_policy_does_not_claim_container_shape",
      test_no_container_preservation_policy_does_not_claim_container_shape},
  };
  return m68k_c_test_run_suite("container_metadata", cases, sizeof(cases) / sizeof(cases[0]));
}
