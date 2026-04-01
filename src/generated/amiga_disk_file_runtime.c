/* Generated Amiga disk file runtime metadata tables. Do not edit directly. */
#include "amiga_disk_file_runtime.h"

const AmigaDiskFileRecordInfo AMIGA_DISK_FILE_RECORD_INFOS[] = {
    { AMIGA_DISK_FILE_META_RECORD_KIND_BOOT_BLOCK, 1u, AMIGA_DISK_FILE_META_RECORD_ROLE_CONTAINER_HEADER,
        AMIGA_DISK_FILE_META_SECTION_KIND_NONE },
    { AMIGA_DISK_FILE_META_RECORD_KIND_ROOT_BLOCK, 2u, AMIGA_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        AMIGA_DISK_FILE_META_SECTION_KIND_NONE },
    { AMIGA_DISK_FILE_META_RECORD_KIND_FILE_HEADER_BLOCK, 3u, AMIGA_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        AMIGA_DISK_FILE_META_SECTION_KIND_NONE },
    { AMIGA_DISK_FILE_META_RECORD_KIND_DATA_BLOCK, 4u, AMIGA_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        AMIGA_DISK_FILE_META_SECTION_KIND_NONE },
    { AMIGA_DISK_FILE_META_RECORD_KIND_DIR_BLOCK, 5u, AMIGA_DISK_FILE_META_RECORD_ROLE_CONTAINER_AUX, AMIGA_DISK_FILE_META_SECTION_KIND_NONE
        },
};
const size_t AMIGA_DISK_FILE_RECORD_INFO_COUNT = sizeof(AMIGA_DISK_FILE_RECORD_INFOS) / sizeof(AMIGA_DISK_FILE_RECORD_INFOS[0]);

const AmigaDiskFileInterpretationRule AMIGA_DISK_FILE_INTERPRETATION_RULES[] = {
    { 0 },
};
const size_t AMIGA_DISK_FILE_INTERPRETATION_RULE_COUNT = 0u;

const AmigaDiskFileRelocationKind AMIGA_DISK_FILE_RELOCATION_KINDS[] = {
    { 0 },
};
const size_t AMIGA_DISK_FILE_RELOCATION_KIND_COUNT = 0u;

const AmigaDiskFileContainerItem AMIGA_DISK_FILE_CONTAINER_ITEMS[] = {
    { AMIGA_DISK_FILE_META_CONTAINER_KIND_ADF_DISK_IMAGE, AMIGA_DISK_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        AMIGA_DISK_FILE_META_RECORD_KIND_BOOT_BLOCK, 0u },
    { AMIGA_DISK_FILE_META_CONTAINER_KIND_ADF_DISK_IMAGE, AMIGA_DISK_FILE_META_CONTAINER_ITEM_KIND_GROUP,
        AMIGA_DISK_FILE_META_GROUP_KIND_FILESYSTEM_BLOCKS, 0u },
};
const size_t AMIGA_DISK_FILE_CONTAINER_ITEM_COUNT = sizeof(AMIGA_DISK_FILE_CONTAINER_ITEMS) / sizeof(AMIGA_DISK_FILE_CONTAINER_ITEMS[0]);

const AmigaDiskFileExtVariantInfo AMIGA_DISK_FILE_EXT_VARIANTS[] = {
    { 0 },
};
const size_t AMIGA_DISK_FILE_EXT_VARIANT_COUNT = 0u;

const AmigaDiskFileExtReferenceKind AMIGA_DISK_FILE_EXT_REFERENCE_KINDS[] = {
    { 0 },
};
const size_t AMIGA_DISK_FILE_EXT_REFERENCE_KIND_COUNT = 0u;

const AmigaDiskFileRecordInfo *amiga_disk_file_record_info_by_wire_id(unsigned wire_id) {
    (void)wire_id;
    switch (wire_id) {
    case 1u: return &AMIGA_DISK_FILE_RECORD_INFOS[0];
    case 2u: return &AMIGA_DISK_FILE_RECORD_INFOS[1];
    case 3u: return &AMIGA_DISK_FILE_RECORD_INFOS[2];
    case 4u: return &AMIGA_DISK_FILE_RECORD_INFOS[3];
    case 5u: return &AMIGA_DISK_FILE_RECORD_INFOS[4];
    default: return NULL;
    }
}

const AmigaDiskFileRecordInfo *amiga_disk_file_record_info_for_section_kind(AmigaDiskFileSectionKind section_kind) {
    (void)section_kind;
    switch (section_kind) {
    default: return NULL;
    }
}

const AmigaDiskFileRecordInfo *amiga_disk_file_record_info_by_record_kind(AmigaDiskFileRecordKind record_kind) {
    (void)record_kind;
    switch (record_kind) {
    case AMIGA_DISK_FILE_META_RECORD_KIND_BOOT_BLOCK: return &AMIGA_DISK_FILE_RECORD_INFOS[0];
    case AMIGA_DISK_FILE_META_RECORD_KIND_ROOT_BLOCK: return &AMIGA_DISK_FILE_RECORD_INFOS[1];
    case AMIGA_DISK_FILE_META_RECORD_KIND_FILE_HEADER_BLOCK: return &AMIGA_DISK_FILE_RECORD_INFOS[2];
    case AMIGA_DISK_FILE_META_RECORD_KIND_DATA_BLOCK: return &AMIGA_DISK_FILE_RECORD_INFOS[3];
    case AMIGA_DISK_FILE_META_RECORD_KIND_DIR_BLOCK: return &AMIGA_DISK_FILE_RECORD_INFOS[4];
    default: return NULL;
    }
}

const AmigaDiskFileInterpretationRule *amiga_disk_file_interpretation_rule_lookup(AmigaDiskFileContainerKind container_kind,
    AmigaDiskFileRecordKind record_kind) {
    (void)container_kind;
    (void)record_kind;
    switch (container_kind) {
    default: return NULL;
    }
}

const AmigaDiskFileRelocationKind *amiga_disk_file_relocation_kind_lookup(AmigaDiskFileRecordKind record_kind) {
    (void)record_kind;
    switch (record_kind) {
    default: return NULL;
    }
}

const AmigaDiskFileExtVariantInfo *amiga_disk_file_ext_variant_lookup(unsigned ext_type) {
    (void)ext_type;
    switch (ext_type) {
    default: return NULL;
    }
}

const AmigaDiskFileExtReferenceKind *amiga_disk_file_ext_reference_kind_lookup(unsigned ext_type) {
    (void)ext_type;
    switch (ext_type) {
    default: return NULL;
    }
}

const AmigaDiskFileExtReferenceKind *amiga_disk_file_ext_reference_kind_lookup_by_mode_width(AmigaDiskFileRelocationMode mode,
    unsigned width_bytes) {
    (void)mode;
    (void)width_bytes;
    switch (mode) {
    default: return NULL;
    }
}
