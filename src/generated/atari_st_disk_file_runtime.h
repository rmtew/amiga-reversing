/* Generated Atari ST disk file runtime metadata. Do not edit directly. */
#ifndef ATARI_ST_DISK_FILE_RUNTIME_H
#define ATARI_ST_DISK_FILE_RUNTIME_H

#include <stddef.h>

/* record_tag */
#define ATARI_ST_DISK_FILE_RECORD_TAG_BOOT_SECTOR 1u
#define ATARI_ST_DISK_FILE_RECORD_TAG_FAT 2u
#define ATARI_ST_DISK_FILE_RECORD_TAG_ROOT_DIRECTORY 3u
#define ATARI_ST_DISK_FILE_RECORD_TAG_DATA_REGION 4u
#define ATARI_ST_DISK_FILE_RECORD_TAG_DIRECTORY_ENTRY 5u

/* dir_attr */
#define ATARI_ST_DISK_FILE_DIR_ATTR_READ_ONLY 1u
#define ATARI_ST_DISK_FILE_DIR_ATTR_HIDDEN 2u
#define ATARI_ST_DISK_FILE_DIR_ATTR_SYSTEM 4u
#define ATARI_ST_DISK_FILE_DIR_ATTR_VOLUME_LABEL 8u
#define ATARI_ST_DISK_FILE_DIR_ATTR_DIRECTORY 16u
#define ATARI_ST_DISK_FILE_DIR_ATTR_ARCHIVE 32u

/* fat_type */
#define ATARI_ST_DISK_FILE_FAT_TYPE_FAT12 12u

#define ATARI_ST_DISK_FILE_CONSTRAINTS_ROOT_DIRECTORY_ENTRY_BYTES 32u
#define ATARI_ST_DISK_FILE_CONSTRAINTS_CLUSTER_NUMBER_STARTS_AT 2u
#define ATARI_ST_DISK_FILE_CONSTRAINTS_VOLUME_LABEL_ENTRIES_LIVE_IN_ROOT_DIRECTORY 1u

/* dir_attr_word */
#define ATARI_ST_DISK_FILE_DIR_ATTR_WORD_READ_ONLY_BIT 0u
#define ATARI_ST_DISK_FILE_DIR_ATTR_WORD_HIDDEN_BIT 1u
#define ATARI_ST_DISK_FILE_DIR_ATTR_WORD_SYSTEM_BIT 2u
#define ATARI_ST_DISK_FILE_DIR_ATTR_WORD_VOLUME_LABEL_BIT 3u
#define ATARI_ST_DISK_FILE_DIR_ATTR_WORD_DIRECTORY_BIT 4u
#define ATARI_ST_DISK_FILE_DIR_ATTR_WORD_ARCHIVE_BIT 5u

/* BOOT_SECTOR fixed fields */
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_JUMP_OFFSET 0u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_JUMP_SIZE 3u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_OEM_OFFSET 3u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_OEM_SIZE 8u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_BYTES_PER_SECTOR_OFFSET 11u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_BYTES_PER_SECTOR_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_CLUSTER_OFFSET 13u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_CLUSTER_SIZE 1u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_RESERVED_SECTOR_COUNT_OFFSET 14u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_RESERVED_SECTOR_COUNT_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_FAT_COUNT_OFFSET 16u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_FAT_COUNT_SIZE 1u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_ROOT_ENTRY_COUNT_OFFSET 17u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_ROOT_ENTRY_COUNT_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_TOTAL_SECTORS_OFFSET 19u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_TOTAL_SECTORS_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_MEDIA_DESCRIPTOR_OFFSET 21u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_MEDIA_DESCRIPTOR_SIZE 1u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_FAT_OFFSET 22u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_FAT_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_TRACK_OFFSET 24u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SECTORS_PER_TRACK_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SIDE_COUNT_OFFSET 26u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_SIDE_COUNT_SIZE 2u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_HIDDEN_SECTOR_COUNT_OFFSET 28u
#define ATARI_ST_DISK_FILE_BOOT_SECTOR_FIELD_HIDDEN_SECTOR_COUNT_SIZE 2u

/* DIRECTORY_ENTRY fixed fields */
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_NAME_RAW_OFFSET 0u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_NAME_RAW_SIZE 8u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_EXT_RAW_OFFSET 8u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_EXT_RAW_SIZE 3u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_ATTRIBUTES_OFFSET 11u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_ATTRIBUTES_SIZE 1u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_RESERVED_OFFSET 12u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_RESERVED_SIZE 10u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_TIME_WORD_OFFSET 22u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_TIME_WORD_SIZE 2u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_DATE_WORD_OFFSET 24u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_DATE_WORD_SIZE 2u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_FIRST_CLUSTER_OFFSET 26u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_FIRST_CLUSTER_SIZE 2u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_FILE_SIZE_OFFSET 28u
#define ATARI_ST_DISK_FILE_DIRECTORY_ENTRY_FIELD_FILE_SIZE_SIZE 4u

typedef enum AtariStDiskFileRecordKind {
    ATARI_ST_DISK_FILE_META_RECORD_KIND_NONE = 0,
    ATARI_ST_DISK_FILE_META_RECORD_KIND_BOOT_SECTOR = 1,
    ATARI_ST_DISK_FILE_META_RECORD_KIND_FAT = 2,
    ATARI_ST_DISK_FILE_META_RECORD_KIND_ROOT_DIRECTORY = 3,
    ATARI_ST_DISK_FILE_META_RECORD_KIND_DATA_REGION = 4,
    ATARI_ST_DISK_FILE_META_RECORD_KIND_DIRECTORY_ENTRY = 5,
} AtariStDiskFileRecordKind;

typedef enum AtariStDiskFileRecordRole {
    ATARI_ST_DISK_FILE_META_RECORD_ROLE_UNKNOWN = 0,
    ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX = 1,
    ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_HEADER = 2,
} AtariStDiskFileRecordRole;

typedef enum AtariStDiskFileSectionKind {
    ATARI_ST_DISK_FILE_META_SECTION_KIND_NONE = 0,
} AtariStDiskFileSectionKind;

typedef enum AtariStDiskFileRelocationMode {
    ATARI_ST_DISK_FILE_META_RELOCATION_MODE_NONE = 0,
} AtariStDiskFileRelocationMode;

typedef enum AtariStDiskFileContainerKind {
    ATARI_ST_DISK_FILE_META_CONTAINER_KIND_UNKNOWN = 0,
    ATARI_ST_DISK_FILE_META_CONTAINER_KIND_ST_DISK_IMAGE = 1,
} AtariStDiskFileContainerKind;

typedef enum AtariStDiskFileGroupKind {
    ATARI_ST_DISK_FILE_META_GROUP_KIND_NONE = 0,
    ATARI_ST_DISK_FILE_META_GROUP_KIND_FILESYSTEM_REGIONS = 1,
} AtariStDiskFileGroupKind;

typedef enum AtariStDiskFileContainerItemKind {
    ATARI_ST_DISK_FILE_META_CONTAINER_ITEM_KIND_NONE = 0,
    ATARI_ST_DISK_FILE_META_CONTAINER_ITEM_KIND_RECORD = 1,
    ATARI_ST_DISK_FILE_META_CONTAINER_ITEM_KIND_GROUP = 2,
} AtariStDiskFileContainerItemKind;

typedef enum AtariStDiskFileExtVariant {
    ATARI_ST_DISK_FILE_META_EXT_VARIANT_NONE = 0,
} AtariStDiskFileExtVariant;

typedef struct AtariStDiskFileRecordInfo {
    AtariStDiskFileRecordKind record_kind;
    unsigned wire_id;
    AtariStDiskFileRecordRole role;
    AtariStDiskFileSectionKind section_kind;
} AtariStDiskFileRecordInfo;

typedef struct AtariStDiskFileInterpretationRule {
    AtariStDiskFileContainerKind container_kind;
    AtariStDiskFileRecordKind record_kind;
    AtariStDiskFileRecordKind interpreted_kind;
} AtariStDiskFileInterpretationRule;

typedef struct AtariStDiskFileRelocationKind {
    AtariStDiskFileRecordKind record_kind;
    unsigned width_bytes;
    AtariStDiskFileRelocationMode mode;
} AtariStDiskFileRelocationKind;

typedef struct AtariStDiskFileContainerItem {
    AtariStDiskFileContainerKind container_kind;
    AtariStDiskFileContainerItemKind item_kind;
    unsigned item_id;
    unsigned optional;
} AtariStDiskFileContainerItem;

typedef struct AtariStDiskFileExtVariantInfo {
    unsigned ext_type;
    AtariStDiskFileExtVariant variant;
} AtariStDiskFileExtVariantInfo;

typedef struct AtariStDiskFileExtReferenceKind {
    unsigned ext_type;
    unsigned width_bytes;
    AtariStDiskFileRelocationMode mode;
} AtariStDiskFileExtReferenceKind;

extern const AtariStDiskFileRecordInfo ATARI_ST_DISK_FILE_RECORD_INFOS[];
extern const size_t ATARI_ST_DISK_FILE_RECORD_INFO_COUNT;

extern const AtariStDiskFileInterpretationRule ATARI_ST_DISK_FILE_INTERPRETATION_RULES[];
extern const size_t ATARI_ST_DISK_FILE_INTERPRETATION_RULE_COUNT;

extern const AtariStDiskFileRelocationKind ATARI_ST_DISK_FILE_RELOCATION_KINDS[];
extern const size_t ATARI_ST_DISK_FILE_RELOCATION_KIND_COUNT;

extern const AtariStDiskFileContainerItem ATARI_ST_DISK_FILE_CONTAINER_ITEMS[];
extern const size_t ATARI_ST_DISK_FILE_CONTAINER_ITEM_COUNT;

extern const AtariStDiskFileExtVariantInfo ATARI_ST_DISK_FILE_EXT_VARIANTS[];
extern const size_t ATARI_ST_DISK_FILE_EXT_VARIANT_COUNT;

extern const AtariStDiskFileExtReferenceKind ATARI_ST_DISK_FILE_EXT_REFERENCE_KINDS[];
extern const size_t ATARI_ST_DISK_FILE_EXT_REFERENCE_KIND_COUNT;

const AtariStDiskFileRecordInfo *atari_st_disk_file_record_info_by_wire_id(unsigned wire_id);
const AtariStDiskFileRecordInfo *atari_st_disk_file_record_info_by_record_kind(AtariStDiskFileRecordKind record_kind);
const AtariStDiskFileRecordInfo *atari_st_disk_file_record_info_for_section_kind(AtariStDiskFileSectionKind section_kind);
const AtariStDiskFileInterpretationRule *atari_st_disk_file_interpretation_rule_lookup(AtariStDiskFileContainerKind container_kind,
    AtariStDiskFileRecordKind record_kind);
const AtariStDiskFileRelocationKind *atari_st_disk_file_relocation_kind_lookup(AtariStDiskFileRecordKind record_kind);
const AtariStDiskFileExtVariantInfo *atari_st_disk_file_ext_variant_lookup(unsigned ext_type);
const AtariStDiskFileExtReferenceKind *atari_st_disk_file_ext_reference_kind_lookup(unsigned ext_type);
const AtariStDiskFileExtReferenceKind *atari_st_disk_file_ext_reference_kind_lookup_by_mode_width(AtariStDiskFileRelocationMode mode,
    unsigned width_bytes);

#endif /* ATARI_ST_DISK_FILE_RUNTIME_H */
