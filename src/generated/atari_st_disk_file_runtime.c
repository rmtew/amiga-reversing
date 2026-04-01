/* Generated Atari ST disk file runtime metadata tables. Do not edit directly. */
#include "atari_st_disk_file_runtime.h"

const AtariStDiskFileRecordInfo ATARI_ST_DISK_FILE_RECORD_INFOS[] = {
    { ATARI_ST_DISK_FILE_META_RECORD_KIND_BOOT_SECTOR, 1u, ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_HEADER,
        ATARI_ST_DISK_FILE_META_SECTION_KIND_NONE },
    { ATARI_ST_DISK_FILE_META_RECORD_KIND_FAT, 2u, ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        ATARI_ST_DISK_FILE_META_SECTION_KIND_NONE },
    { ATARI_ST_DISK_FILE_META_RECORD_KIND_ROOT_DIRECTORY, 3u, ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        ATARI_ST_DISK_FILE_META_SECTION_KIND_NONE },
    { ATARI_ST_DISK_FILE_META_RECORD_KIND_DATA_REGION, 4u, ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        ATARI_ST_DISK_FILE_META_SECTION_KIND_NONE },
    { ATARI_ST_DISK_FILE_META_RECORD_KIND_DIRECTORY_ENTRY, 5u, ATARI_ST_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        ATARI_ST_DISK_FILE_META_SECTION_KIND_NONE },
};
const size_t ATARI_ST_DISK_FILE_RECORD_INFO_COUNT = sizeof(ATARI_ST_DISK_FILE_RECORD_INFOS) / sizeof(ATARI_ST_DISK_FILE_RECORD_INFOS[0]);

const AtariStDiskFileInterpretationRule ATARI_ST_DISK_FILE_INTERPRETATION_RULES[] = {
    { 0 },
};
const size_t ATARI_ST_DISK_FILE_INTERPRETATION_RULE_COUNT = 0u;

const AtariStDiskFileRelocationKind ATARI_ST_DISK_FILE_RELOCATION_KINDS[] = {
    { 0 },
};
const size_t ATARI_ST_DISK_FILE_RELOCATION_KIND_COUNT = 0u;

const AtariStDiskFileContainerItem ATARI_ST_DISK_FILE_CONTAINER_ITEMS[] = {
    { ATARI_ST_DISK_FILE_META_CONTAINER_KIND_ST_DISK_IMAGE, ATARI_ST_DISK_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        ATARI_ST_DISK_FILE_META_RECORD_KIND_BOOT_SECTOR, 0u },
    { ATARI_ST_DISK_FILE_META_CONTAINER_KIND_ST_DISK_IMAGE, ATARI_ST_DISK_FILE_META_CONTAINER_ITEM_KIND_GROUP,
        ATARI_ST_DISK_FILE_META_GROUP_KIND_FILESYSTEM_REGIONS, 0u },
};
const size_t ATARI_ST_DISK_FILE_CONTAINER_ITEM_COUNT =
    sizeof(ATARI_ST_DISK_FILE_CONTAINER_ITEMS) / sizeof(ATARI_ST_DISK_FILE_CONTAINER_ITEMS[0]);

const AtariStDiskFileExtVariantInfo ATARI_ST_DISK_FILE_EXT_VARIANTS[] = {
    { 0 },
};
const size_t ATARI_ST_DISK_FILE_EXT_VARIANT_COUNT = 0u;

const AtariStDiskFileExtReferenceKind ATARI_ST_DISK_FILE_EXT_REFERENCE_KINDS[] = {
    { 0 },
};
const size_t ATARI_ST_DISK_FILE_EXT_REFERENCE_KIND_COUNT = 0u;

const AtariStDiskFileRecordInfo *atari_st_disk_file_record_info_by_wire_id(unsigned wire_id) {
    (void)wire_id;
    switch (wire_id) {
    case 1u: return &ATARI_ST_DISK_FILE_RECORD_INFOS[0];
    case 2u: return &ATARI_ST_DISK_FILE_RECORD_INFOS[1];
    case 3u: return &ATARI_ST_DISK_FILE_RECORD_INFOS[2];
    case 4u: return &ATARI_ST_DISK_FILE_RECORD_INFOS[3];
    case 5u: return &ATARI_ST_DISK_FILE_RECORD_INFOS[4];
    default: return NULL;
    }
}

const AtariStDiskFileRecordInfo *atari_st_disk_file_record_info_for_section_kind(AtariStDiskFileSectionKind section_kind) {
    (void)section_kind;
    switch (section_kind) {
    default: return NULL;
    }
}

const AtariStDiskFileRecordInfo *atari_st_disk_file_record_info_by_record_kind(AtariStDiskFileRecordKind record_kind) {
    (void)record_kind;
    switch (record_kind) {
    case ATARI_ST_DISK_FILE_META_RECORD_KIND_BOOT_SECTOR: return &ATARI_ST_DISK_FILE_RECORD_INFOS[0];
    case ATARI_ST_DISK_FILE_META_RECORD_KIND_FAT: return &ATARI_ST_DISK_FILE_RECORD_INFOS[1];
    case ATARI_ST_DISK_FILE_META_RECORD_KIND_ROOT_DIRECTORY: return &ATARI_ST_DISK_FILE_RECORD_INFOS[2];
    case ATARI_ST_DISK_FILE_META_RECORD_KIND_DATA_REGION: return &ATARI_ST_DISK_FILE_RECORD_INFOS[3];
    case ATARI_ST_DISK_FILE_META_RECORD_KIND_DIRECTORY_ENTRY: return &ATARI_ST_DISK_FILE_RECORD_INFOS[4];
    default: return NULL;
    }
}

const AtariStDiskFileInterpretationRule *atari_st_disk_file_interpretation_rule_lookup(AtariStDiskFileContainerKind container_kind,
    AtariStDiskFileRecordKind record_kind) {
    (void)container_kind;
    (void)record_kind;
    switch (container_kind) {
    default: return NULL;
    }
}

const AtariStDiskFileRelocationKind *atari_st_disk_file_relocation_kind_lookup(AtariStDiskFileRecordKind record_kind) {
    (void)record_kind;
    switch (record_kind) {
    default: return NULL;
    }
}

const AtariStDiskFileExtVariantInfo *atari_st_disk_file_ext_variant_lookup(unsigned ext_type) {
    (void)ext_type;
    switch (ext_type) {
    default: return NULL;
    }
}

const AtariStDiskFileExtReferenceKind *atari_st_disk_file_ext_reference_kind_lookup(unsigned ext_type) {
    (void)ext_type;
    switch (ext_type) {
    default: return NULL;
    }
}

const AtariStDiskFileExtReferenceKind *atari_st_disk_file_ext_reference_kind_lookup_by_mode_width(AtariStDiskFileRelocationMode mode,
    unsigned width_bytes) {
    (void)mode;
    (void)width_bytes;
    switch (mode) {
    default: return NULL;
    }
}
