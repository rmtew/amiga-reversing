#include "m68k_c_unit_test.h"
#include "platform_macos_hfs.h"

#include <string.h>

static void put_u16(unsigned char *data, size_t offset, uint16_t value) {
  data[offset] = (unsigned char)(value >> 8);
  data[offset + 1U] = (unsigned char)value;
}

static void put_u32(unsigned char *data, size_t offset, uint32_t value) {
  data[offset] = (unsigned char)(value >> 24);
  data[offset + 1U] = (unsigned char)(value >> 16);
  data[offset + 2U] = (unsigned char)(value >> 8);
  data[offset + 3U] = (unsigned char)value;
}

static void put_name_key(unsigned char *node, size_t offset, uint32_t parent_id, const char *name) {
  size_t length = strlen(name);
  node[offset] = (unsigned char)(6U + length);
  put_u32(node, offset + 2U, parent_id);
  node[offset + 6U] = (unsigned char)length;
  memcpy(node + offset + 7U, name, length);
}

static void put_extent(unsigned char *data, size_t offset, uint16_t start, uint16_t count) {
  put_u16(data, offset, start);
  put_u16(data, offset + 2U, count);
}

static size_t make_hfs_volume(unsigned char *data, size_t data_size) {
  const size_t mdb = 1024U;
  const size_t catalog_offset = 2048U;
  const size_t header_record = 14U;
  const size_t leaf_offset = catalog_offset + 512U;
  const size_t directory_record = 14U;
  const size_t directory_data = 26U;
  const size_t file_record = 80U;
  const size_t file_data = 90U;
  if (data_size < 3072U) return 0U;
  memset(data, 0, data_size);
  data[mdb] = 'B';
  data[mdb + 1U] = 'D';
  put_u16(data, mdb + 18U, 16U);
  put_u32(data, mdb + 20U, 512U);
  put_u16(data, mdb + 28U, 4U);
  data[mdb + 36U] = 6U;
  memcpy(data + mdb + 37U, "MPW-GM", 6U);
  put_u32(data, mdb + 146U, 1024U);
  put_extent(data, mdb + 150U, 0U, 2U);

  put_u16(data, catalog_offset + 10U, 1U);
  put_u16(data, catalog_offset + 512U - 2U, (uint16_t)header_record);
  put_u16(data, catalog_offset + header_record + 18U, 512U);

  data[leaf_offset + 8U] = 0xFFU;
  put_u16(data, leaf_offset + 10U, 2U);
  put_name_key(data + leaf_offset, directory_record, 2U, "Tools");
  put_u16(data, leaf_offset + directory_data, 0x0100U);
  put_u16(data, leaf_offset + directory_data + 4U, 1U);
  put_u32(data, leaf_offset + directory_data + 6U, 42U);

  put_name_key(data + leaf_offset, file_record, 42U, "Asm");
  put_u16(data, leaf_offset + file_data, 0x0200U);
  memcpy(data + leaf_offset + file_data + 4U, "MPST", 4U);
  memcpy(data + leaf_offset + file_data + 8U, "MPS ", 4U);
  put_u32(data, leaf_offset + file_data + 20U, 2310U);
  put_u32(data, leaf_offset + file_data + 26U, 128U);
  put_u32(data, leaf_offset + file_data + 36U, 256U);
  put_extent(data, leaf_offset + file_data + 74U, 2U, 1U);
  put_extent(data, leaf_offset + file_data + 86U, 3U, 1U);
  put_u16(data, leaf_offset + 512U - 2U, (uint16_t)directory_record);
  put_u16(data, leaf_offset + 512U - 4U, (uint16_t)file_record);
  return 3072U;
}

static int test_hfs_catalog_reports_file_and_fork_metadata(void) {
  unsigned char data[4096];
  PlatformMacosHFSCatalog catalog;
  PlatformMacosHFSDirectoryInfo directories[4];
  PlatformMacosHFSFileInfo files[4];
  char path[PLATFORM_MACOS_HFS_PATH_SIZE];
  uint32_t fork_offset = 0U;
  uint32_t fork_size = 0U;
  size_t size = make_hfs_volume(data, sizeof(data));
  M68K_C_ASSERT(size != 0U);
  M68K_C_ASSERT_INT(0, platform_macos_hfs_catalog_parse(data, size, &catalog, directories, 4U, files, 4U));
  M68K_C_ASSERT_STR("MPW-GM", catalog.volume.volume_name);
  M68K_C_ASSERT_U32(512U, catalog.volume.allocation_block_size);
  M68K_C_ASSERT_U32(2048U, catalog.volume.allocation_start_offset);
  M68K_C_ASSERT_U32(512U, catalog.volume.catalog_node_size);
  M68K_C_ASSERT_U32(1U, catalog.directory_count);
  M68K_C_ASSERT_U32(1U, catalog.file_count);
  M68K_C_ASSERT_U32(42U, directories[0].cnid);
  M68K_C_ASSERT_STR("Tools", directories[0].name);
  M68K_C_ASSERT_U32(2310U, files[0].cnid);
  M68K_C_ASSERT_STR("Asm", files[0].name);
  M68K_C_ASSERT_STR("MPST", files[0].file_type);
  M68K_C_ASSERT_STR("MPS ", files[0].creator);
  M68K_C_ASSERT_U32(128U, files[0].data_size);
  M68K_C_ASSERT_U32(256U, files[0].resource_size);
  M68K_C_ASSERT_INT(0, platform_macos_hfs_file_path(directories, catalog.directory_count, &files[0], path,
    sizeof(path)));
  M68K_C_ASSERT_STR("Tools/Asm", path);
  M68K_C_ASSERT_INT(0, platform_macos_hfs_first_fork_extent_bounds(&catalog.volume, files[0].resource_extents,
    files[0].resource_size, &fork_offset, &fork_size));
  M68K_C_ASSERT_U32(3584U, fork_offset);
  M68K_C_ASSERT_U32(256U, fork_size);
  return 0;
}

static int test_hfs_rejects_missing_mdb_signature(void) {
  unsigned char data[4096];
  PlatformMacosHFSCatalog catalog;
  size_t size = make_hfs_volume(data, sizeof(data));
  M68K_C_ASSERT(size != 0U);
  data[1024U] = 0U;
  M68K_C_ASSERT_INT(-1, platform_macos_hfs_catalog_parse(data, size, &catalog, NULL, 0U, NULL, 0U));
  return 0;
}

int m68k_c_platform_macos_hfs_tests(void) {
  static const M68kCTestCase cases[] = {
    {"hfs_catalog_reports_file_and_fork_metadata", test_hfs_catalog_reports_file_and_fork_metadata},
    {"hfs_rejects_missing_mdb_signature", test_hfs_rejects_missing_mdb_signature},
  };
  return m68k_c_test_run_suite("platform_macos_hfs", cases, sizeof(cases) / sizeof(cases[0]));
}
