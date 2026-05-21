#ifndef PLATFORM_MACOS_HFS_H
#define PLATFORM_MACOS_HFS_H

#include <stddef.h>
#include <stdint.h>

#define PLATFORM_MACOS_HFS_NAME_SIZE 32U
#define PLATFORM_MACOS_HFS_PATH_SIZE 256U
#define PLATFORM_MACOS_HFS_FOURCC_SIZE 5U
#define PLATFORM_MACOS_HFS_EXTENT_COUNT 3U

typedef struct PlatformMacosHFSExtent {
  uint16_t start_block;
  uint16_t block_count;
} PlatformMacosHFSExtent;

typedef struct PlatformMacosHFSVolume {
  char volume_name[PLATFORM_MACOS_HFS_NAME_SIZE];
  uint16_t allocation_block_count;
  uint32_t allocation_block_size;
  uint32_t allocation_start_offset;
  uint32_t catalog_size;
  PlatformMacosHFSExtent catalog_extents[PLATFORM_MACOS_HFS_EXTENT_COUNT];
  uint16_t catalog_node_size;
} PlatformMacosHFSVolume;

typedef struct PlatformMacosHFSDirectoryInfo {
  uint32_t parent_id;
  char name[PLATFORM_MACOS_HFS_NAME_SIZE];
  uint32_t cnid;
  uint16_t valence;
} PlatformMacosHFSDirectoryInfo;

typedef struct PlatformMacosHFSFileInfo {
  uint32_t parent_id;
  char name[PLATFORM_MACOS_HFS_NAME_SIZE];
  uint32_t cnid;
  char file_type[PLATFORM_MACOS_HFS_FOURCC_SIZE];
  char creator[PLATFORM_MACOS_HFS_FOURCC_SIZE];
  uint32_t data_size;
  uint32_t resource_size;
  PlatformMacosHFSExtent data_extents[PLATFORM_MACOS_HFS_EXTENT_COUNT];
  PlatformMacosHFSExtent resource_extents[PLATFORM_MACOS_HFS_EXTENT_COUNT];
} PlatformMacosHFSFileInfo;

typedef struct PlatformMacosHFSCatalog {
  PlatformMacosHFSVolume volume;
  size_t directory_count;
  size_t file_count;
} PlatformMacosHFSCatalog;

int platform_macos_hfs_catalog_parse(const unsigned char *data, size_t size,
  PlatformMacosHFSCatalog *out_catalog, PlatformMacosHFSDirectoryInfo *directories,
  size_t directory_capacity, PlatformMacosHFSFileInfo *files,
  size_t file_capacity);
int platform_macos_hfs_file_path(const PlatformMacosHFSDirectoryInfo *directories,
  size_t directory_count, const PlatformMacosHFSFileInfo *file, char *out_path,
  size_t path_size);
int platform_macos_hfs_first_fork_extent_bounds(const PlatformMacosHFSVolume *volume,
  const PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT],
  uint32_t fork_size, uint32_t *out_offset, uint32_t *out_size);
int platform_macos_hfs_copy_fork(const unsigned char *image_data,
  size_t image_size, const PlatformMacosHFSVolume *volume,
  const PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT],
  uint32_t fork_size, unsigned char *out_data, size_t out_capacity);

#endif
