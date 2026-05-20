#include "m68k_c_unit_test.h"
#include "generated/mac_os_runtime.h"

static int test_mac_os_record_lookup_exposes_source_offsets(void) {
  const MacOsRecordInfo *rect = mac_os_find_record("Rect");
  const MacOsRecordFieldInfo *right = mac_os_find_record_field("Rect", "right");
  const MacOsRecordFieldInfo *top_left = mac_os_find_record_field("Rect", "topLeft");
  const MacOsRecordInfo *event = mac_os_find_record("EventRecord");
  const MacOsRecordFieldInfo *where = mac_os_find_record_field("EventRecord", "where");
  const MacOsRecordInfo *volume = mac_os_find_record("HVolumeParam");
  const MacOsRecordFieldInfo *io_name_ptr = mac_os_find_record_field("HVolumeParam", "ioNamePtr");
  const MacOsRecordFieldInfo *finder_info = mac_os_find_record_field("HVolumeParam", "ioVFndrInfo");

  M68K_C_ASSERT(rect != NULL);
  M68K_C_ASSERT_U32(8U, rect->size);
  M68K_C_ASSERT_STR("ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a", rect->source_path);
  M68K_C_ASSERT_U32(490U, rect->line);
  M68K_C_ASSERT(right != NULL);
  M68K_C_ASSERT_U32(6U, right->offset);
  M68K_C_ASSERT_U32(2U, right->size);
  M68K_C_ASSERT(top_left != NULL);
  M68K_C_ASSERT_U32(0U, top_left->offset);
  M68K_C_ASSERT_U32(4U, top_left->size);

  M68K_C_ASSERT(event != NULL);
  M68K_C_ASSERT_U32(16U, event->size);
  M68K_C_ASSERT(where != NULL);
  M68K_C_ASSERT_U32(10U, where->offset);
  M68K_C_ASSERT_U32(4U, where->size);

  M68K_C_ASSERT(volume != NULL);
  M68K_C_ASSERT_U32(122U, volume->size);
  M68K_C_ASSERT(io_name_ptr != NULL);
  M68K_C_ASSERT_U32(18U, io_name_ptr->offset);
  M68K_C_ASSERT_U32(4U, io_name_ptr->size);
  M68K_C_ASSERT(finder_info != NULL);
  M68K_C_ASSERT_U32(90U, finder_info->offset);
  M68K_C_ASSERT_U32(32U, finder_info->size);
  return 0;
}

static int test_mac_os_call_lookup_distinguishes_opword_and_package_macro(void) {
  const MacOsCallInfo *get_resource = mac_os_find_call_by_opword(0xA9A0U);
  const MacOsCallInfo *wait_next_event = mac_os_find_call_by_name("_WaitNextEvent");
  const MacOsCallInfo *unload_seg = mac_os_find_call_by_opword(0xA9F1U);
  const MacOsCallInfo *hget_vinfo = mac_os_find_call_by_name("_PBHGetVInfoSync");
  const MacOsCallInfo *num_to_string = mac_os_find_call_by_name("_NumToString");

  M68K_C_ASSERT(get_resource != NULL);
  M68K_C_ASSERT_STR("_GetResource", get_resource->name);
  M68K_C_ASSERT_U32(MAC_OS_CALL_KIND_OPWORD, get_resource->kind);
  M68K_C_ASSERT_U32(0xA9A0U, get_resource->opword);
  M68K_C_ASSERT_STR("Resources", get_resource->family);

  M68K_C_ASSERT(wait_next_event != NULL);
  M68K_C_ASSERT_U32(0xA860U, wait_next_event->opword);
  M68K_C_ASSERT_STR("Events", wait_next_event->family);
  M68K_C_ASSERT(unload_seg != NULL);
  M68K_C_ASSERT_STR("_UnloadSeg", unload_seg->name);

  M68K_C_ASSERT(hget_vinfo != NULL);
  M68K_C_ASSERT_U32(0xA207U, hget_vinfo->opword);
  M68K_C_ASSERT_STR("A0", hget_vinfo->parameter_register);
  M68K_C_ASSERT_STR("D0", hget_vinfo->result_register);

  M68K_C_ASSERT(num_to_string != NULL);
  M68K_C_ASSERT_U32(MAC_OS_CALL_KIND_PACKAGE_MACRO, num_to_string->kind);
  M68K_C_ASSERT_U32(0U, num_to_string->opword);
  M68K_C_ASSERT_U32(0xA9EEU, num_to_string->package_word);
  M68K_C_ASSERT(mac_os_find_call_by_opword(0xA9EEU) == NULL);
  return 0;
}

int m68k_c_mac_os_runtime_tests(void) {
  static const M68kCTestCase cases[] = {
    {"mac_os_record_lookup_exposes_source_offsets", test_mac_os_record_lookup_exposes_source_offsets},
    {"mac_os_call_lookup_distinguishes_opword_and_package_macro",
      test_mac_os_call_lookup_distinguishes_opword_and_package_macro},
  };
  return m68k_c_test_run_suite("mac_os_runtime", cases, sizeof(cases) / sizeof(cases[0]));
}
