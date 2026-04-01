/* Generated Atari ST PRG file runtime metadata. Do not edit directly. */
#ifndef ATARI_ST_PRG_FILE_RUNTIME_H
#define ATARI_ST_PRG_FILE_RUNTIME_H

#include <stddef.h>

/* magic */
#define ATARI_ST_PRG_FILE_MAGIC_PRG 24602u

/* section_kind */
#define ATARI_ST_PRG_FILE_SECTION_KIND_TEXT 1u
#define ATARI_ST_PRG_FILE_SECTION_KIND_DATA 2u
#define ATARI_ST_PRG_FILE_SECTION_KIND_BSS 3u

#define ATARI_ST_PRG_FILE_CONSTRAINTS_BSS_IS_NOT_STORED_IN_FILE 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_TEXT_AND_DATA_ARE_STORED_CONTIGUOUSLY 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_RELOCATIONS_APPLY_WITHIN_LOADED_TEXT_PLUS_DATA_IMAGE 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_RELOCATION_FLAG_IS_INFORMATIONAL_FOR_CLASSIC_PRG 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_RELOCATION_STREAM_MAY_TERMINATE_AT_EOF_WITHOUT_ZERO_BYTE 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_ZERO_ONLY_TRAILING_PADDING_AFTER_EMPTY_RELOCATION_STREAM_IS_ALLOWED 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_SYMBOL_TABLE_IS_OPTIONAL_FOR_PARSING 1u
#define ATARI_ST_PRG_FILE_CONSTRAINTS_RELOCATION_STREAM_IS_OPTIONAL_FOR_PARSING 1u

/* PRG_HEADER fixed fields */
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_MAGIC_OFFSET 0u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_MAGIC_SIZE 2u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_TEXT_SIZE_OFFSET 2u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_TEXT_SIZE_SIZE 4u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_DATA_SIZE_OFFSET 6u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_DATA_SIZE_SIZE 4u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_BSS_SIZE_OFFSET 10u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_BSS_SIZE_SIZE 4u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_SYMBOL_TABLE_SIZE_OFFSET 14u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_SYMBOL_TABLE_SIZE_SIZE 4u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_SYMBOL_TABLE_TYPE_OFFSET 18u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_SYMBOL_TABLE_TYPE_SIZE 4u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_PROGRAM_FLAGS_OFFSET 22u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_PROGRAM_FLAGS_SIZE 4u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_RELOCATION_FLAG_OFFSET 26u
#define ATARI_ST_PRG_FILE_PRG_HEADER_FIELD_RELOCATION_FLAG_SIZE 2u

/* RELOCATION_STREAM fixed fields */
#define ATARI_ST_PRG_FILE_RELOCATION_STREAM_FIELD_INITIAL_OFFSET_OFFSET 0u
#define ATARI_ST_PRG_FILE_RELOCATION_STREAM_FIELD_INITIAL_OFFSET_SIZE 4u

typedef enum AtariStPrgFileRecordKind {
    ATARI_ST_PRG_FILE_META_RECORD_KIND_NONE = 0,
    ATARI_ST_PRG_FILE_META_RECORD_KIND_PRG_HEADER = 1,
    ATARI_ST_PRG_FILE_META_RECORD_KIND_TEXT = 2,
    ATARI_ST_PRG_FILE_META_RECORD_KIND_DATA = 3,
    ATARI_ST_PRG_FILE_META_RECORD_KIND_SYMBOL_TABLE = 4,
    ATARI_ST_PRG_FILE_META_RECORD_KIND_RELOCATION_STREAM = 5,
} AtariStPrgFileRecordKind;

typedef enum AtariStPrgFileRecordRole {
    ATARI_ST_PRG_FILE_META_RECORD_ROLE_UNKNOWN = 0,
    ATARI_ST_PRG_FILE_META_RECORD_ROLE_CONTAINER_AUX = 1,
    ATARI_ST_PRG_FILE_META_RECORD_ROLE_CONTAINER_HEADER = 2,
    ATARI_ST_PRG_FILE_META_RECORD_ROLE_SECTION_PAYLOAD = 3,
} AtariStPrgFileRecordRole;

typedef enum AtariStPrgFileSectionKind {
    ATARI_ST_PRG_FILE_META_SECTION_KIND_NONE = 0,
    ATARI_ST_PRG_FILE_META_SECTION_KIND_CODE = 1,
    ATARI_ST_PRG_FILE_META_SECTION_KIND_DATA = 2,
} AtariStPrgFileSectionKind;

typedef enum AtariStPrgFileRelocationMode {
    ATARI_ST_PRG_FILE_META_RELOCATION_MODE_NONE = 0,
    ATARI_ST_PRG_FILE_META_RELOCATION_MODE_LOAD_BASE_RELATIVE = 1,
} AtariStPrgFileRelocationMode;

typedef enum AtariStPrgFileContainerKind {
    ATARI_ST_PRG_FILE_META_CONTAINER_KIND_UNKNOWN = 0,
    ATARI_ST_PRG_FILE_META_CONTAINER_KIND_PRG_EXECUTABLE = 1,
} AtariStPrgFileContainerKind;

typedef enum AtariStPrgFileGroupKind {
    ATARI_ST_PRG_FILE_META_GROUP_KIND_NONE = 0,
    ATARI_ST_PRG_FILE_META_GROUP_KIND_LOADED_IMAGE = 1,
} AtariStPrgFileGroupKind;

typedef enum AtariStPrgFileContainerItemKind {
    ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_NONE = 0,
    ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_RECORD = 1,
    ATARI_ST_PRG_FILE_META_CONTAINER_ITEM_KIND_GROUP = 2,
} AtariStPrgFileContainerItemKind;

typedef enum AtariStPrgFileExtVariant {
    ATARI_ST_PRG_FILE_META_EXT_VARIANT_NONE = 0,
} AtariStPrgFileExtVariant;

typedef struct AtariStPrgFileRecordInfo {
    AtariStPrgFileRecordKind record_kind;
    unsigned wire_id;
    AtariStPrgFileRecordRole role;
    AtariStPrgFileSectionKind section_kind;
} AtariStPrgFileRecordInfo;

typedef struct AtariStPrgFileInterpretationRule {
    AtariStPrgFileContainerKind container_kind;
    AtariStPrgFileRecordKind record_kind;
    AtariStPrgFileRecordKind interpreted_kind;
} AtariStPrgFileInterpretationRule;

typedef struct AtariStPrgFileRelocationKind {
    AtariStPrgFileRecordKind record_kind;
    unsigned width_bytes;
    AtariStPrgFileRelocationMode mode;
} AtariStPrgFileRelocationKind;

typedef struct AtariStPrgFileContainerItem {
    AtariStPrgFileContainerKind container_kind;
    AtariStPrgFileContainerItemKind item_kind;
    unsigned item_id;
    unsigned optional;
} AtariStPrgFileContainerItem;

typedef struct AtariStPrgFileExtVariantInfo {
    unsigned ext_type;
    AtariStPrgFileExtVariant variant;
} AtariStPrgFileExtVariantInfo;

typedef struct AtariStPrgFileExtReferenceKind {
    unsigned ext_type;
    unsigned width_bytes;
    AtariStPrgFileRelocationMode mode;
} AtariStPrgFileExtReferenceKind;

extern const AtariStPrgFileRecordInfo ATARI_ST_PRG_FILE_RECORD_INFOS[];
extern const size_t ATARI_ST_PRG_FILE_RECORD_INFO_COUNT;

extern const AtariStPrgFileInterpretationRule ATARI_ST_PRG_FILE_INTERPRETATION_RULES[];
extern const size_t ATARI_ST_PRG_FILE_INTERPRETATION_RULE_COUNT;

extern const AtariStPrgFileRelocationKind ATARI_ST_PRG_FILE_RELOCATION_KINDS[];
extern const size_t ATARI_ST_PRG_FILE_RELOCATION_KIND_COUNT;

extern const AtariStPrgFileContainerItem ATARI_ST_PRG_FILE_CONTAINER_ITEMS[];
extern const size_t ATARI_ST_PRG_FILE_CONTAINER_ITEM_COUNT;

extern const AtariStPrgFileExtVariantInfo ATARI_ST_PRG_FILE_EXT_VARIANTS[];
extern const size_t ATARI_ST_PRG_FILE_EXT_VARIANT_COUNT;

extern const AtariStPrgFileExtReferenceKind ATARI_ST_PRG_FILE_EXT_REFERENCE_KINDS[];
extern const size_t ATARI_ST_PRG_FILE_EXT_REFERENCE_KIND_COUNT;

const AtariStPrgFileRecordInfo *atari_st_prg_file_record_info_by_wire_id(unsigned wire_id);
const AtariStPrgFileRecordInfo *atari_st_prg_file_record_info_by_record_kind(AtariStPrgFileRecordKind record_kind);
const AtariStPrgFileRecordInfo *atari_st_prg_file_record_info_for_section_kind(AtariStPrgFileSectionKind section_kind);
const AtariStPrgFileInterpretationRule *atari_st_prg_file_interpretation_rule_lookup(AtariStPrgFileContainerKind container_kind,
    AtariStPrgFileRecordKind record_kind);
const AtariStPrgFileRelocationKind *atari_st_prg_file_relocation_kind_lookup(AtariStPrgFileRecordKind record_kind);
const AtariStPrgFileExtVariantInfo *atari_st_prg_file_ext_variant_lookup(unsigned ext_type);
const AtariStPrgFileExtReferenceKind *atari_st_prg_file_ext_reference_kind_lookup(unsigned ext_type);
const AtariStPrgFileExtReferenceKind *atari_st_prg_file_ext_reference_kind_lookup_by_mode_width(AtariStPrgFileRelocationMode mode,
    unsigned width_bytes);

#endif /* ATARI_ST_PRG_FILE_RUNTIME_H */
