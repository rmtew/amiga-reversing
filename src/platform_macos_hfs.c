#include "platform_macos_hfs.h"

#include <string.h>

#define HFS_MDB_OFFSET 1024U
#define HFS_SECTOR_SIZE 512U
#define HFS_ROOT_DIR_ID 2U
#define HFS_CATALOG_ROOT_PARENT_ID 1U
#define HFS_NODE_KIND_LEAF 0xFFU

static uint16_t read_u16be_at(const unsigned char *data, size_t offset) {
  return (uint16_t)(((uint16_t)data[offset] << 8) | (uint16_t)data[offset + 1U]);
}

static uint32_t read_u32be_at(const unsigned char *data, size_t offset) {
  return ((uint32_t)data[offset] << 24) | ((uint32_t)data[offset + 1U] << 16) |
    ((uint32_t)data[offset + 2U] << 8) | (uint32_t)data[offset + 3U];
}

static int range_fits(size_t offset, size_t length, size_t size) {
  return offset <= size && length <= size - offset;
}

static void copy_pascal_name(char *out, size_t out_size, const unsigned char *data, size_t offset,
    size_t max_length) {
  size_t length;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  length = data[offset];
  if (length > max_length) length = max_length;
  if (length >= out_size) length = out_size - 1U;
  if (length != 0U) memcpy(out, data + offset + 1U, length);
  out[length] = '\0';
}

static void copy_fourcc(char out[PLATFORM_MACOS_HFS_FOURCC_SIZE], const unsigned char *data, size_t offset) {
  memcpy(out, data + offset, 4U);
  out[4] = '\0';
}

static void read_extents(const unsigned char *data, size_t offset,
    PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT]) {
  size_t index;
  for (index = 0U; index < PLATFORM_MACOS_HFS_EXTENT_COUNT; ++index) {
    extents[index].start_block = read_u16be_at(data, offset + index * 4U);
    extents[index].block_count = read_u16be_at(data, offset + index * 4U + 2U);
  }
}

static int append_path_part(char *out, size_t out_size, size_t *used, const char *part) {
  size_t length;
  if (out == NULL || used == NULL || part == NULL) return -1;
  length = strlen(part);
  if (*used != 0U) {
    if (*used + 1U >= out_size) return -1;
    out[(*used)++] = '/';
  }
  if (length >= out_size - *used) return -1;
  memcpy(out + *used, part, length + 1U);
  *used += length;
  return 0;
}

static const PlatformMacosHFSDirectoryInfo *find_directory_by_cnid(
    const PlatformMacosHFSDirectoryInfo *directories, size_t directory_count, uint32_t cnid) {
  size_t index;
  for (index = 0U; index < directory_count; ++index) {
    if (directories[index].cnid == cnid) return &directories[index];
  }
  return NULL;
}

static int read_volume(const unsigned char *data, size_t size, PlatformMacosHFSVolume *out_volume) {
  if (data == NULL || out_volume == NULL || !range_fits(HFS_MDB_OFFSET, 162U, size)) return -1;
  if (data[HFS_MDB_OFFSET] != 'B' || data[HFS_MDB_OFFSET + 1U] != 'D') return -1;
  memset(out_volume, 0, sizeof(*out_volume));
  copy_pascal_name(out_volume->volume_name, sizeof(out_volume->volume_name), data, HFS_MDB_OFFSET + 36U, 27U);
  out_volume->allocation_block_count = read_u16be_at(data, HFS_MDB_OFFSET + 18U);
  out_volume->allocation_block_size = read_u32be_at(data, HFS_MDB_OFFSET + 20U);
  out_volume->allocation_start_offset = (uint32_t)read_u16be_at(data, HFS_MDB_OFFSET + 28U) * HFS_SECTOR_SIZE;
  out_volume->catalog_size = read_u32be_at(data, HFS_MDB_OFFSET + 146U);
  read_extents(data, HFS_MDB_OFFSET + 150U, out_volume->catalog_extents);
  return 0;
}

static int first_extent_bounds(const PlatformMacosHFSVolume *volume,
    const PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT], uint32_t byte_size,
    uint32_t *out_offset, uint32_t *out_size) {
  uint32_t extent_size;
  uint32_t offset;
  size_t extent_size_wide;
  size_t offset_wide;
  if (volume == NULL || extents == NULL || extents[0].block_count == 0U || volume->allocation_block_size == 0U)
    return -1;
  offset_wide = (size_t)volume->allocation_start_offset +
    (size_t)extents[0].start_block * (size_t)volume->allocation_block_size;
  extent_size_wide = (size_t)extents[0].block_count * (size_t)volume->allocation_block_size;
  if (offset_wide > UINT32_MAX || extent_size_wide > UINT32_MAX) return -1;
  offset = (uint32_t)offset_wide;
  extent_size = (uint32_t)extent_size_wide;
  if (byte_size > extent_size) return -1;
  if (out_offset != NULL) *out_offset = offset;
  if (out_size != NULL) *out_size = byte_size;
  return 0;
}

static int parse_catalog_key(const unsigned char *node, size_t node_size, size_t offset,
    uint32_t *out_parent_id, char out_name[PLATFORM_MACOS_HFS_NAME_SIZE], size_t *out_data_offset) {
  size_t key_length;
  size_t data_offset;
  if (!range_fits(offset, 7U, node_size)) return -1;
  key_length = node[offset];
  data_offset = offset + key_length + 1U;
  if ((data_offset & 1U) != 0U) ++data_offset;
  if (!range_fits(data_offset, 2U, node_size)) return -1;
  *out_parent_id = read_u32be_at(node, offset + 2U);
  copy_pascal_name(out_name, PLATFORM_MACOS_HFS_NAME_SIZE, node, offset + 6U, 31U);
  *out_data_offset = data_offset;
  return 0;
}

static int read_catalog_node_size(const unsigned char *catalog, size_t catalog_size, uint16_t *out_node_size) {
  uint16_t record_count;
  uint16_t first_record;
  if (catalog == NULL || out_node_size == NULL || !range_fits(0U, HFS_SECTOR_SIZE, catalog_size)) return -1;
  record_count = read_u16be_at(catalog, 10U);
  if (record_count == 0U) return -1;
  first_record = read_u16be_at(catalog, HFS_SECTOR_SIZE - 2U);
  if (!range_fits(first_record + 18U, 2U, HFS_SECTOR_SIZE)) return -1;
  *out_node_size = read_u16be_at(catalog, first_record + 18U);
  return *out_node_size != 0U ? 0 : -1;
}

static int parse_catalog_leaf_record(const unsigned char *node, size_t node_size, size_t offset,
    PlatformMacosHFSDirectoryInfo *directories, size_t directory_capacity,
    PlatformMacosHFSFileInfo *files, size_t file_capacity, PlatformMacosHFSCatalog *catalog) {
  uint32_t parent_id;
  char name[PLATFORM_MACOS_HFS_NAME_SIZE];
  size_t data_offset;
  uint16_t record_type;
  if (parse_catalog_key(node, node_size, offset, &parent_id, name, &data_offset) != 0) return -1;
  record_type = read_u16be_at(node, data_offset);
  if (record_type == 0x0100U) {
    PlatformMacosHFSDirectoryInfo directory;
    if (!range_fits(data_offset, 10U, node_size)) return -1;
    memset(&directory, 0, sizeof(directory));
    directory.parent_id = parent_id;
    memcpy(directory.name, name, sizeof(directory.name));
    directory.valence = read_u16be_at(node, data_offset + 4U);
    directory.cnid = read_u32be_at(node, data_offset + 6U);
    if (directories != NULL && catalog->directory_count < directory_capacity) {
      directories[catalog->directory_count] = directory;
    }
    ++catalog->directory_count;
  } else if (record_type == 0x0200U) {
    PlatformMacosHFSFileInfo file;
    if (!range_fits(data_offset, 98U, node_size)) return -1;
    memset(&file, 0, sizeof(file));
    file.parent_id = parent_id;
    memcpy(file.name, name, sizeof(file.name));
    copy_fourcc(file.file_type, node, data_offset + 4U);
    copy_fourcc(file.creator, node, data_offset + 8U);
    file.cnid = read_u32be_at(node, data_offset + 20U);
    file.data_size = read_u32be_at(node, data_offset + 26U);
    file.resource_size = read_u32be_at(node, data_offset + 36U);
    read_extents(node, data_offset + 74U, file.data_extents);
    read_extents(node, data_offset + 86U, file.resource_extents);
    if (files != NULL && catalog->file_count < file_capacity) files[catalog->file_count] = file;
    ++catalog->file_count;
  }
  return 0;
}

int platform_macos_hfs_catalog_parse(const unsigned char *data, size_t size,
    PlatformMacosHFSCatalog *out_catalog, PlatformMacosHFSDirectoryInfo *directories,
    size_t directory_capacity, PlatformMacosHFSFileInfo *files,
    size_t file_capacity) {
  PlatformMacosHFSCatalog catalog;
  uint32_t catalog_offset;
  uint32_t catalog_size;
  size_t node_offset;
  if (out_catalog == NULL || read_volume(data, size, &catalog.volume) != 0) return -1;
  catalog.directory_count = 0U;
  catalog.file_count = 0U;
  if (first_extent_bounds(&catalog.volume, catalog.volume.catalog_extents, catalog.volume.catalog_size,
      &catalog_offset, &catalog_size) != 0 || !range_fits(catalog_offset, catalog_size, size)) {
    return -1;
  }
  if (read_catalog_node_size(data + catalog_offset, catalog_size, &catalog.volume.catalog_node_size) != 0) return -1;
  for (node_offset = 0U; node_offset + catalog.volume.catalog_node_size <= catalog_size;
       node_offset += catalog.volume.catalog_node_size) {
    const unsigned char *node = data + catalog_offset + node_offset;
    uint16_t record_count;
    uint16_t record_index;
    if (node[8] != HFS_NODE_KIND_LEAF) continue;
    record_count = read_u16be_at(node, 10U);
    for (record_index = 0U; record_index < record_count; ++record_index) {
      uint16_t record_offset = read_u16be_at(node,
        (size_t)catalog.volume.catalog_node_size - 2U * ((size_t)record_index + 1U));
      if (parse_catalog_leaf_record(node, catalog.volume.catalog_node_size, record_offset, directories,
          directory_capacity, files, file_capacity, &catalog) != 0) {
        return -1;
      }
    }
  }
  *out_catalog = catalog;
  return 0;
}

int platform_macos_hfs_file_path(const PlatformMacosHFSDirectoryInfo *directories,
    size_t directory_count, const PlatformMacosHFSFileInfo *file, char *out_path,
    size_t path_size) {
  const PlatformMacosHFSDirectoryInfo *chain[32];
  size_t chain_count = 0U;
  size_t used = 0U;
  uint32_t current_id;
  if (file == NULL || out_path == NULL || path_size == 0U) return -1;
  out_path[0] = '\0';
  current_id = file->parent_id;
  while (current_id != HFS_CATALOG_ROOT_PARENT_ID && current_id != HFS_ROOT_DIR_ID) {
    const PlatformMacosHFSDirectoryInfo *directory = find_directory_by_cnid(directories, directory_count, current_id);
    if (directory == NULL || chain_count >= sizeof(chain) / sizeof(chain[0])) return -1;
    chain[chain_count++] = directory;
    current_id = directory->parent_id;
  }
  while (chain_count != 0U) {
    --chain_count;
    if (append_path_part(out_path, path_size, &used, chain[chain_count]->name) != 0) return -1;
  }
  return append_path_part(out_path, path_size, &used, file->name);
}

int platform_macos_hfs_first_fork_extent_bounds(const PlatformMacosHFSVolume *volume,
    const PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT],
    uint32_t fork_size, uint32_t *out_offset, uint32_t *out_size) {
  return first_extent_bounds(volume, extents, fork_size, out_offset, out_size);
}

int platform_macos_hfs_copy_fork(const unsigned char *image_data,
    size_t image_size, const PlatformMacosHFSVolume *volume,
    const PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT],
    uint32_t fork_size, unsigned char *out_data, size_t out_capacity) {
  size_t index;
  size_t remaining = fork_size;
  size_t written = 0U;
  if (image_data == NULL || volume == NULL || extents == NULL ||
      (fork_size != 0U && out_data == NULL) || out_capacity < fork_size ||
      volume->allocation_block_size == 0U) {
    return -1;
  }
  for (index = 0U; index < PLATFORM_MACOS_HFS_EXTENT_COUNT && remaining != 0U; ++index) {
    size_t extent_offset;
    size_t extent_size;
    size_t copy_size;
    if (extents[index].block_count == 0U) continue;
    extent_offset = (size_t)volume->allocation_start_offset +
      (size_t)extents[index].start_block * (size_t)volume->allocation_block_size;
    extent_size = (size_t)extents[index].block_count * (size_t)volume->allocation_block_size;
    copy_size = extent_size < remaining ? extent_size : remaining;
    if (!range_fits(extent_offset, copy_size, image_size)) return -1;
    memcpy(out_data + written, image_data + extent_offset, copy_size);
    written += copy_size;
    remaining -= copy_size;
  }
  return remaining == 0U ? 0 : 1;
}
