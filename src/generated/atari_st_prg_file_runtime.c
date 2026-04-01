/* Generated Atari ST PRG file runtime metadata tables. Do not edit directly. */
#include "atari_st_prg_file_runtime.h"

const AtariStPrgFileRecordInfo ATARI_ST_PRG_FILE_RECORD_INFOS[] = {
    { ATARI_ST_PRG_FILE_META_RECORD_KIND_PRG_HEADER, 0u, ATARI_ST_PRG_FILE_META_RECORD_ROLE_CONTAINER_HEADER,
        ATARI_ST_PRG_FILE_META_SECTION_KIND_NONE },
    { ATARI_ST_PRG_FILE_META_RECORD_KIND_TEXT, 0u, ATARI_ST_PRG_FILE_META_RECORD_ROLE_SECTION_PAYLOAD,
        ATARI_ST_PRG_FILE_META_SECTION_KIND_CODE },
    { ATARI_ST_PRG_FILE_META_RECORD_KIND_DATA, 0u, ATARI_ST_PRG_FILE_META_RECORD_ROLE_SECTION_PAYLOAD,
        ATARI_ST_PRG_FILE_META_SECTION_KIND_DATA },
    { ATARI_ST_PRG_FILE_META_RECORD_KIND_SYMBOL_TABLE, 0u, ATARI_ST_PRG_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        ATARI_ST_PRG_FILE_META_SECTION_KIND_NONE },
    { ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM, 0u, ATARI_ST_PRG_FILE_META_RECORD_ROLE_CONTAINER_AUX,
        ATARI_ST_PRG_FILE_META_SECTION_KIND_NONE },
};
const size_t ATARI_ST_PRG_FILE_RECORD_INFO_COUNT = sizeof(ATARI_ST_PRG_FILE_RECORD_INFOS) / sizeof(ATARI_ST_PRG_FILE_RECORD_INFOS[0]);

const AtariStPrgFileInterpretationRule ATARI_ST_PRG_FILE_INTERPRETATION_RULES[] = {
    { 0 },
};
const size_t ATARI_ST_PRG_FILE_INTERPRETATION_RULE_COUNT = 0u;

const AtariStPrgFileRelocationKind ATARI_ST_PRG_FILE_RELOCATION_KINDS[] = {
    { ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM, 4u, ATARI_ST_PRG_FILE_META_RELOCATION_MODE_LOAD_BASE_RELATIVE },
};
const size_t ATARI_ST_PRG_FILE_RELOCATION_KIND_COUNT =
    sizeof(ATARI_ST_PRG_FILE_RELOCATION_KINDS) / sizeof(ATARI_ST_PRG_FILE_RELOCATION_KINDS[0]);

const AtariStPrgFileContainerItem ATARI_ST_PRG_FILE_CONTAINER_ITEMS[] = {
    { ATARI_ST_PRG_FILE_META_CONTAINER_KIND_PRG_EXECUTABLE, ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        ATARI_ST_PRG_FILE_META_RECORD_KIND_PRG_HEADER, 0u },
    { ATARI_ST_PRG_FILE_META_CONTAINER_KIND_PRG_EXECUTABLE, ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        ATARI_ST_PRG_FILE_META_RECORD_KIND_TEXT, 0u },
    { ATARI_ST_PRG_FILE_META_CONTAINER_KIND_PRG_EXECUTABLE, ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        ATARI_ST_PRG_FILE_META_RECORD_KIND_DATA, 0u },
    { ATARI_ST_PRG_FILE_META_CONTAINER_KIND_PRG_EXECUTABLE, ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        ATARI_ST_PRG_FILE_META_RECORD_KIND_SYMBOL_TABLE, 1u },
    { ATARI_ST_PRG_FILE_META_CONTAINER_KIND_PRG_EXECUTABLE, ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_RECORD,
        ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM, 1u },
};
const size_t ATARI_ST_PRG_FILE_CONTAINER_ITEM_COUNT =
    sizeof(ATARI_ST_PRG_FILE_CONTAINER_ITEMS) / sizeof(ATARI_ST_PRG_FILE_CONTAINER_ITEMS[0]);

const AtariStPrgFileExtVariantInfo ATARI_ST_PRG_FILE_EXT_VARIANTS[] = {
    { 0 },
};
const size_t ATARI_ST_PRG_FILE_EXT_VARIANT_COUNT = 0u;

const AtariStPrgFileExtReferenceKind ATARI_ST_PRG_FILE_EXT_REFERENCE_KINDS[] = {
    { 0 },
};
const size_t ATARI_ST_PRG_FILE_EXT_REFERENCE_KIND_COUNT = 0u;

const AtariStPrgFileRecordInfo *atari_st_prg_file_record_info_by_wire_id(unsigned wire_id) {
    (void)wire_id;
    switch (wire_id) {
    default: return NULL;
    }
}

const AtariStPrgFileRecordInfo *atari_st_prg_file_record_info_for_section_kind(AtariStPrgFileSectionKind section_kind) {
    (void)section_kind;
    switch (section_kind) {
    default: return NULL;
    }
}

const AtariStPrgFileRecordInfo *atari_st_prg_file_record_info_by_record_kind(AtariStPrgFileRecordKind record_kind) {
    (void)record_kind;
    switch (record_kind) {
    case ATARI_ST_PRG_FILE_META_RECORD_KIND_PRG_HEADER: return &ATARI_ST_PRG_FILE_RECORD_INFOS[0];
    case ATARI_ST_PRG_FILE_META_RECORD_KIND_TEXT: return &ATARI_ST_PRG_FILE_RECORD_INFOS[1];
    case ATARI_ST_PRG_FILE_META_RECORD_KIND_DATA: return &ATARI_ST_PRG_FILE_RECORD_INFOS[2];
    case ATARI_ST_PRG_FILE_META_RECORD_KIND_SYMBOL_TABLE: return &ATARI_ST_PRG_FILE_RECORD_INFOS[3];
    case ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM: return &ATARI_ST_PRG_FILE_RECORD_INFOS[4];
    default: return NULL;
    }
}

const AtariStPrgFileInterpretationRule *atari_st_prg_file_interpretation_rule_lookup(AtariStPrgFileContainerKind container_kind,
    AtariStPrgFileRecordKind record_kind) {
    (void)container_kind;
    (void)record_kind;
    switch (container_kind) {
    case ATARI_ST_PRG_FILE_META_CONTAINER_KIND_UNKNOWN:
        switch (record_kind) {
        case ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM: return &ATARI_ST_PRG_FILE_INTERPRETATION_RULES[0];
        default: return NULL;
        }
    default: return NULL;
    }
}

const AtariStPrgFileRelocationKind *atari_st_prg_file_relocation_kind_lookup(AtariStPrgFileRecordKind record_kind) {
    (void)record_kind;
    switch (record_kind) {
    case ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM: return &ATARI_ST_PRG_FILE_RELOCATION_KINDS[0];
    default: return NULL;
    }
}

const AtariStPrgFileExtVariantInfo *atari_st_prg_file_ext_variant_lookup(unsigned ext_type) {
    (void)ext_type;
    switch (ext_type) {
    default: return NULL;
    }
}

const AtariStPrgFileExtReferenceKind *atari_st_prg_file_ext_reference_kind_lookup(unsigned ext_type) {
    (void)ext_type;
    switch (ext_type) {
    default: return NULL;
    }
}

const AtariStPrgFileExtReferenceKind *atari_st_prg_file_ext_reference_kind_lookup_by_mode_width(AtariStPrgFileRelocationMode mode,
    unsigned width_bytes) {
    (void)mode;
    (void)width_bytes;
    switch (mode) {
    default: return NULL;
    }
}
