#ifndef M68K_SIMULATOR_H
#define M68K_SIMULATOR_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "m68k_object.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_SIM_TARGET_LIMIT 32U
#define M68K_SIM_MEMORY_CELL_LIMIT 32U
#define M68K_SIM_MEMORY_WRITE_LIMIT 8U
#define M68K_SIM_CONCRETE_WRITE_RANGE_LIMIT 32U
#define M68K_SIM_CONTROL_REGISTER_LIMIT 32U

typedef enum M68kSimFlowKind {
  M68K_SIM_FLOW_NONE = 0,
  M68K_SIM_FLOW_SEQUENTIAL = 1,
  M68K_SIM_FLOW_BRANCH = 2,
  M68K_SIM_FLOW_JUMP = 3,
  M68K_SIM_FLOW_CALL = 4,
  M68K_SIM_FLOW_RETURN = 5,
  M68K_SIM_FLOW_TRAP = 6
} M68kSimFlowKind;

typedef enum M68kSimOperationType {
  M68K_SIM_OP_NONE = 0,
  M68K_SIM_OP_ADD = 1,
  M68K_SIM_OP_CLEAR = 2,
  M68K_SIM_OP_COMPARE = 3,
  M68K_SIM_OP_DBCC = 4,
  M68K_SIM_OP_MOVE = 5,
  M68K_SIM_OP_SET_COND = 6,
  M68K_SIM_OP_SUB = 7,
  M68K_SIM_OP_SWAP = 8,
  M68K_SIM_OP_TEST = 9,
  M68K_SIM_OP_PUSH_EA = 10,
  M68K_SIM_OP_LINK = 11,
  M68K_SIM_OP_UNLK = 12,
  M68K_SIM_OP_TEST_AND_SET = 13,
  M68K_SIM_OP_BIT_TEST = 14,
  M68K_SIM_OP_BIT_SET = 15,
  M68K_SIM_OP_BIT_CLEAR = 16,
  M68K_SIM_OP_BIT_CHANGE = 17,
  M68K_SIM_OP_MOVE_MULTIPLE = 18,
  M68K_SIM_OP_MOVE_PERIPHERAL = 19,
  M68K_SIM_OP_LOGIC_AND = 20,
  M68K_SIM_OP_LOGIC_OR = 21,
  M68K_SIM_OP_LOGIC_XOR = 22,
  M68K_SIM_OP_NEGATE = 23,
  M68K_SIM_OP_NOT = 24,
  M68K_SIM_OP_SIGN_EXTEND = 25,
  M68K_SIM_OP_SWAP_WORDS = 26,
  M68K_SIM_OP_SHIFT = 27,
  M68K_SIM_OP_ROTATE = 28,
  M68K_SIM_OP_ROTATE_EXTEND = 29,
  M68K_SIM_OP_TRAPV = 30,
  M68K_SIM_OP_PACK = 31,
  M68K_SIM_OP_UNPACK = 32,
  M68K_SIM_OP_MULTIPLY = 33,
  M68K_SIM_OP_DIVIDE = 34,
  M68K_SIM_OP_BOUNDS_CHECK = 35,
  M68K_SIM_OP_COMPARE_SWAP = 36,
  M68K_SIM_OP_BITFIELD_CHANGE = 37,
  M68K_SIM_OP_BITFIELD_CLEAR = 38,
  M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED = 39,
  M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED = 40,
  M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE = 41,
  M68K_SIM_OP_BITFIELD_INSERT = 42,
  M68K_SIM_OP_BITFIELD_SET = 43,
  M68K_SIM_OP_BITFIELD_TEST = 44,
  M68K_SIM_OP_ADD_EXTEND = 45,
  M68K_SIM_OP_SUB_EXTEND = 46,
  M68K_SIM_OP_NOP = 47
} M68kSimOperationType;

typedef enum M68kSimOperationClass {
  M68K_SIM_CLASS_NONE = 0,
  M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS = 1,
  M68K_SIM_CLASS_MULTI_REGISTER_TRANSFER = 2
} M68kSimOperationClass;

typedef enum M68kSimSpAction {
  M68K_SIM_SP_DECREMENT = 1,
  M68K_SIM_SP_INCREMENT = 2,
  M68K_SIM_SP_ADJUST = 3,
  M68K_SIM_SP_STORE_REG_TO_STACK = 4,
  M68K_SIM_SP_SAVE_TO_REG = 5,
  M68K_SIM_SP_LOAD_FROM_REG = 6,
  M68K_SIM_SP_LOAD_FROM_STACK_TO_REG = 7
} M68kSimSpAction;

typedef enum M68kSimAccessKind {
  M68K_SIM_ACCESS_NONE = 0,
  M68K_SIM_ACCESS_REGISTER_READ = 1,
  M68K_SIM_ACCESS_REGISTER_WRITE = 2,
  M68K_SIM_ACCESS_MEMORY_READ = 3,
  M68K_SIM_ACCESS_MEMORY_WRITE = 4,
  M68K_SIM_ACCESS_COMPUTE_ADDRESS = 5,
  M68K_SIM_ACCESS_IMMEDIATE = 6,
  M68K_SIM_ACCESS_BRANCH_TARGET = 7,
  M68K_SIM_ACCESS_REGISTER_LIST_READ = 8,
  M68K_SIM_ACCESS_REGISTER_LIST_WRITE = 9
} M68kSimAccessKind;

typedef enum M68kSimMultiTransferDirection {
  M68K_SIM_MULTI_NONE = 0,
  M68K_SIM_MULTI_REGISTER_TO_MEMORY = 1,
  M68K_SIM_MULTI_MEMORY_TO_REGISTER = 2
} M68kSimMultiTransferDirection;

typedef enum M68kSimMultiTransferAddressUpdate {
  M68K_SIM_MULTI_UPDATE_NONE = 0,
  M68K_SIM_MULTI_UPDATE_PREDECREMENT_IF_PREDEC = 1,
  M68K_SIM_MULTI_UPDATE_POSTINCREMENT_IF_POSTINC = 2
} M68kSimMultiTransferAddressUpdate;

typedef enum M68kSimMultiTransferRegIteration {
  M68K_SIM_MULTI_REG_ITERATION_NONE = 0,
  M68K_SIM_MULTI_REG_ITERATION_ASCENDING_MASK_BITS = 1
} M68kSimMultiTransferRegIteration;

typedef enum M68kSimMultiTransferSourceSnapshot {
  M68K_SIM_MULTI_SNAPSHOT_NONE = 0,
  M68K_SIM_MULTI_SNAPSHOT_BEFORE_WRITE = 1
} M68kSimMultiTransferSourceSnapshot;

typedef enum M68kSimStripedTransferDirection {
  M68K_SIM_STRIPED_NONE = 0,
  M68K_SIM_STRIPED_REGISTER_TO_MEMORY = 1,
  M68K_SIM_STRIPED_MEMORY_TO_REGISTER = 2
} M68kSimStripedTransferDirection;

typedef enum M68kSimOperandResultKind {
  M68K_SIM_RESULT_NONE = 0,
  M68K_SIM_RESULT_SCALAR = 1,
  M68K_SIM_RESULT_ADDRESS = 2,
  M68K_SIM_RESULT_CONTROL_TARGET = 3
} M68kSimOperandResultKind;

typedef enum M68kSimOperandWidthMode {
  M68K_SIM_WIDTH_NONE = 0,
  M68K_SIM_WIDTH_FIXED = 1,
  M68K_SIM_WIDTH_INSTRUCTION_SIZE = 2,
  M68K_SIM_WIDTH_FULL_REGISTER = 3
} M68kSimOperandWidthMode;

typedef enum M68kSimShiftDirection {
  M68K_SIM_SHIFT_DIR_NONE = 0,
  M68K_SIM_SHIFT_DIR_LEFT = 1,
  M68K_SIM_SHIFT_DIR_RIGHT = 2
} M68kSimShiftDirection;

typedef enum M68kSimShiftFillMode {
  M68K_SIM_SHIFT_FILL_NONE = 0,
  M68K_SIM_SHIFT_FILL_ZERO = 1,
  M68K_SIM_SHIFT_FILL_SIGN = 2,
  M68K_SIM_SHIFT_FILL_ROTATE = 3
} M68kSimShiftFillMode;

typedef enum M68kSimShiftCountSource {
  M68K_SIM_SHIFT_COUNT_NONE = 0,
  M68K_SIM_SHIFT_COUNT_OPERAND = 1,
  M68K_SIM_SHIFT_COUNT_IMPLICIT_ONE = 2
} M68kSimShiftCountSource;

typedef enum M68kSimBoundsMode {
  M68K_SIM_BOUNDS_NONE = 0,
  M68K_SIM_BOUNDS_UPPER_ONLY = 1,
  M68K_SIM_BOUNDS_LOWER_UPPER_PAIR = 2
} M68kSimBoundsMode;

typedef enum M68kSimExceptionVectorSource {
  M68K_SIM_EXCEPTION_VECTOR_NONE = 0,
  M68K_SIM_EXCEPTION_VECTOR_FIXED = 1,
  M68K_SIM_EXCEPTION_VECTOR_TRAP_IMMEDIATE = 2
} M68kSimExceptionVectorSource;

typedef enum M68kSimExceptionTrigger {
  M68K_SIM_EXCEPTION_TRIGGER_NONE = 0,
  M68K_SIM_EXCEPTION_TRIGGER_ALWAYS = 1,
  M68K_SIM_EXCEPTION_TRIGGER_IF_OVERFLOW = 2,
  M68K_SIM_EXCEPTION_TRIGGER_IF_BOUNDS_FAIL = 3,
  M68K_SIM_EXCEPTION_TRIGGER_IF_USER_MODE = 4
} M68kSimExceptionTrigger;

typedef enum M68kSimExceptionPcSource {
  M68K_SIM_EXCEPTION_PC_CURRENT = 0,
  M68K_SIM_EXCEPTION_PC_NEXT = 1
} M68kSimExceptionPcSource;

typedef enum M68kSimExceptionAddressSource {
  M68K_SIM_EXCEPTION_ADDRESS_NONE = 0,
  M68K_SIM_EXCEPTION_ADDRESS_CURRENT_PC = 1
} M68kSimExceptionAddressSource;

typedef enum M68kSimExceptionStackedSrSource {
  M68K_SIM_EXCEPTION_STACKED_SR_CURRENT = 0,
  M68K_SIM_EXCEPTION_STACKED_SR_UPDATED_FLAGS = 1
} M68kSimExceptionStackedSrSource;

typedef enum M68kSimReturnRestoreKind {
  M68K_SIM_RETURN_RESTORE_NONE = 0,
  M68K_SIM_RETURN_RESTORE_PC_ONLY = 1,
  M68K_SIM_RETURN_RESTORE_CCR_THEN_PC = 2,
  M68K_SIM_RETURN_RESTORE_EXCEPTION_FRAME = 3
} M68kSimReturnRestoreKind;

typedef enum M68kSimExceptionFrameKind {
  M68K_SIM_EXCEPTION_FRAME_NONE = 0,
  M68K_SIM_EXCEPTION_FRAME_MC68000_GROUP_1_2 = 1,
  M68K_SIM_EXCEPTION_FRAME_FORMAT_0 = 2,
  M68K_SIM_EXCEPTION_FRAME_FORMAT_2 = 3
} M68kSimExceptionFrameKind;

typedef enum M68kSimExpectedOperandKind {
  M68K_SIM_EXPECT_ANY = 0,
  M68K_SIM_EXPECT_DN = 1,
  M68K_SIM_EXPECT_AN = 2,
  M68K_SIM_EXPECT_RN = 3,
  M68K_SIM_EXPECT_EA = 4,
  M68K_SIM_EXPECT_IND = 5,
  M68K_SIM_EXPECT_POSTINC = 6,
  M68K_SIM_EXPECT_PREDEC = 7,
  M68K_SIM_EXPECT_DISP = 8,
  M68K_SIM_EXPECT_INDEX = 9,
  M68K_SIM_EXPECT_ABSW = 10,
  M68K_SIM_EXPECT_ABSL = 11,
  M68K_SIM_EXPECT_PCDISP = 12,
  M68K_SIM_EXPECT_PCINDEX = 13,
  M68K_SIM_EXPECT_IMM = 14,
  M68K_SIM_EXPECT_LABEL = 15,
  M68K_SIM_EXPECT_CCR = 16,
  M68K_SIM_EXPECT_CTRL_REG = 17,
  M68K_SIM_EXPECT_SR = 18,
  M68K_SIM_EXPECT_USP = 19,
  M68K_SIM_EXPECT_REGLIST = 20
} M68kSimExpectedOperandKind;

typedef enum M68kSimEaAddressShape {
  M68K_SIM_EA_SHAPE_NONE = 0,
  M68K_SIM_EA_SHAPE_INDIRECT = 1,
  M68K_SIM_EA_SHAPE_POSTINCREMENT = 2,
  M68K_SIM_EA_SHAPE_PREDECREMENT = 3,
  M68K_SIM_EA_SHAPE_DISPLACEMENT = 4,
  M68K_SIM_EA_SHAPE_INDEX = 5,
  M68K_SIM_EA_SHAPE_ABSOLUTE_WORD = 6,
  M68K_SIM_EA_SHAPE_ABSOLUTE_LONG = 7,
  M68K_SIM_EA_SHAPE_PC_DISPLACEMENT = 8,
  M68K_SIM_EA_SHAPE_PC_INDEX = 9
} M68kSimEaAddressShape;

typedef enum M68kSimEaAddressFormula {
  M68K_SIM_EA_FORMULA_NONE = 0,
  M68K_SIM_EA_FORMULA_DECODED_EA = 1,
  M68K_SIM_EA_FORMULA_AN = 2,
  M68K_SIM_EA_FORMULA_AN_PLUS_DISP = 3,
  M68K_SIM_EA_FORMULA_AN_PLUS_DISP_PLUS_INDEX = 4,
  M68K_SIM_EA_FORMULA_ABSOLUTE_LITERAL = 5,
  M68K_SIM_EA_FORMULA_PC_PLUS_DISP = 6,
  M68K_SIM_EA_FORMULA_PC_PLUS_DISP_PLUS_INDEX = 7
} M68kSimEaAddressFormula;

typedef enum M68kSimEaRegisterUpdate {
  M68K_SIM_EA_UPDATE_NONE = 0,
  M68K_SIM_EA_UPDATE_POSTINCREMENT = 1,
  M68K_SIM_EA_UPDATE_PREDECREMENT = 2
} M68kSimEaRegisterUpdate;

typedef enum M68kSimEaIndexExtensionFormat {
  M68K_SIM_EA_INDEX_EXT_NONE = 0,
  M68K_SIM_EA_INDEX_EXT_BRIEF = 1
} M68kSimEaIndexExtensionFormat;

typedef enum M68kSimEaIndexRegisterClass {
  M68K_SIM_EA_INDEX_REG_NONE = 0,
  M68K_SIM_EA_INDEX_REG_DATA_OR_ADDRESS = 1
} M68kSimEaIndexRegisterClass;

typedef enum M68kSimEaIndexValueWidthSource {
  M68K_SIM_EA_INDEX_WIDTH_NONE = 0,
  M68K_SIM_EA_INDEX_WIDTH_EXTENSION_WORD = 1
} M68kSimEaIndexValueWidthSource;

typedef enum M68kSimEaIndexScaleSource {
  M68K_SIM_EA_INDEX_SCALE_NONE = 0,
  M68K_SIM_EA_INDEX_SCALE_EXTENSION_WORD = 1
} M68kSimEaIndexScaleSource;

typedef enum M68kSimEaIndexSignSource {
  M68K_SIM_EA_INDEX_SIGN_NONE = 0,
  M68K_SIM_EA_INDEX_SIGN_EXTENSION_WORD = 1
} M68kSimEaIndexSignSource;

typedef enum M68kSimEaDisplacementSource {
  M68K_SIM_EA_DISP_NONE = 0,
  M68K_SIM_EA_DISP_OPERAND_VALUE = 1
} M68kSimEaDisplacementSource;

typedef enum M68kSimEaBaseKind {
  M68K_SIM_EA_BASE_NONE = 0,
  M68K_SIM_EA_BASE_AN = 1,
  M68K_SIM_EA_BASE_PC = 2,
  M68K_SIM_EA_BASE_ABSOLUTE = 3
} M68kSimEaBaseKind;

typedef enum M68kSimValueKind {
  M68K_SIM_VALUE_UNKNOWN = 0,
  M68K_SIM_VALUE_CONSTANT = 1,
  M68K_SIM_VALUE_SECTION_PTR = 2,
  M68K_SIM_VALUE_TARGET_SET = 3,
  M68K_SIM_VALUE_TABLE_REGION = 4
} M68kSimValueKind;

typedef enum M68kSimProvenanceKind {
  M68K_SIM_PROV_NONE = 0,
  M68K_SIM_PROV_IMMEDIATE = 1,
  M68K_SIM_PROV_PC_REL = 2,
  M68K_SIM_PROV_REGISTER_COPY = 3,
  M68K_SIM_PROV_ADDRESS_ARITH = 4,
  M68K_SIM_PROV_MEMORY_LOAD = 5,
  M68K_SIM_PROV_TABLE_SCAN = 6
} M68kSimProvenanceKind;

typedef enum M68kSimCcrFormula {
  M68K_SIM_CCR_FORMULA_NONE = 0,
  M68K_SIM_CCR_FORMULA_ADD_DECIMAL_FLAGS = 1,
  M68K_SIM_CCR_FORMULA_ADD_FLAGS = 2,
  M68K_SIM_CCR_FORMULA_BIT_TEST_FLAGS = 3,
  M68K_SIM_CCR_FORMULA_BITFIELD_FLAGS = 4,
  M68K_SIM_CCR_FORMULA_BOUNDS_CHECK_FLAGS = 5,
  M68K_SIM_CCR_FORMULA_CLEAR_FLAGS = 6,
  M68K_SIM_CCR_FORMULA_DIVIDE_FLAGS = 7,
  M68K_SIM_CCR_FORMULA_MOVE_FLAGS = 8,
  M68K_SIM_CCR_FORMULA_MULTIPLY_FLAGS = 9,
  M68K_SIM_CCR_FORMULA_ROTATE_EXTEND_FLAGS = 10,
  M68K_SIM_CCR_FORMULA_ROTATE_FLAGS = 11,
  M68K_SIM_CCR_FORMULA_SHIFT_FLAGS = 12,
  M68K_SIM_CCR_FORMULA_SUB_DECIMAL_FLAGS = 13,
  M68K_SIM_CCR_FORMULA_SUB_FLAGS = 14,
  M68K_SIM_CCR_FORMULA_TEST_FLAGS = 15,
  M68K_SIM_CCR_FORMULA_WRITE_CCR = 16,
  M68K_SIM_CCR_FORMULA_WRITE_SR = 17
} M68kSimCcrFormula;

typedef struct M68kSimSpEffectDef {
  uint8_t action;
  int16_t bytes;
  const char *reg;
  const char *operand;
} M68kSimSpEffectDef;

typedef struct M68kSimFormMetadata {
  uint8_t operation_type;
  uint8_t operation_class;
  uint8_t flow_kind;
  uint8_t flow_conditional;
  uint8_t has_compute_formula;
  uint8_t ccr_formula;
  uint8_t operand_access_kinds[4];
  uint8_t operand_expected_kinds[4];
  uint8_t operand_ea_address_formulas[4];
  uint8_t operand_ea_register_updates[4];
  uint8_t operand_ea_index_extension_formats[4];
  uint8_t operand_ea_index_register_classes[4];
  uint8_t operand_ea_index_value_width_sources[4];
  uint8_t operand_ea_index_scale_sources[4];
  uint8_t operand_ea_index_sign_sources[4];
  uint8_t operand_ea_displacement_sources[4];
  uint8_t operand_ea_address_shapes[4];
  uint8_t operand_ea_base_kinds[4];
  uint8_t operand_ea_uses_displacement[4];
  uint8_t operand_ea_uses_index[4];
  uint8_t operand_ea_pc_base_bias_bytes[4];
  uint8_t operand_ea_address_literal_width_bytes[4];
  uint8_t operand_result_kinds[4];
  uint8_t operand_width_modes[4];
  uint8_t operand_widths[4];
  uint16_t sp_effect_start;
  uint8_t sp_effect_count;
  uint8_t source_operand_index;
  uint8_t dest_operand_index;
  uint8_t target_operand_index;
  uint8_t condition_code;
  uint8_t reglist_operand_index;
  uint8_t address_operand_index;
  uint8_t multi_transfer_direction;
  uint8_t multi_transfer_address_update;
  uint8_t multi_transfer_reg_iteration;
  uint8_t multi_transfer_source_snapshot;
  uint8_t striped_reg_operand_index;
  uint8_t striped_address_operand_index;
  uint8_t striped_direction;
  uint8_t striped_stride;
  uint8_t striped_big_endian;
  uint8_t unary_sign_extend_source_bits;
  uint8_t shift_direction;
  uint8_t shift_fill_mode;
  uint8_t shift_count_source;
  uint8_t shift_count_modulus;
  uint8_t shift_rotate_extra_bits;
  uint8_t numeric_is_signed;
  uint8_t bounds_mode;
  uint8_t bounds_trap_on_fail;
  uint8_t exception_vector_source;
  uint8_t exception_trigger;
  uint8_t exception_pc_source;
  uint8_t exception_address_source;
  uint8_t exception_stacked_sr_source;
  uint8_t return_restore_kind;
  uint8_t return_stack_adjust_operand_index;
  uint8_t exception_vector;
} M68kSimFormMetadata;

typedef enum M68kSimMetadataStatus {
  M68K_SIM_METADATA_OK = 0,
  M68K_SIM_METADATA_GENERATED_SEMANTICS_MISSING = 1,
  M68K_SIM_METADATA_FORM_NOT_FOUND = 2
} M68kSimMetadataStatus;

typedef enum M68kSimSemanticStatus {
  M68K_SIM_SEMANTICS_AVAILABLE = 1,
  M68K_SIM_SEMANTICS_GENERATED_SEMANTICS_MISSING = 2,
  M68K_SIM_SEMANTICS_INTENTIONALLY_UNSUPPORTED = 3
} M68kSimSemanticStatus;

enum {
  M68K_SIM_FORM_LOOKUP_NONE = 0xFFFFu
};

typedef struct M68kSimExceptionFrameDef {
  uint8_t frame_kind;
  uint8_t format_code;
  uint8_t frame_size_bytes;
  uint8_t reserved;
} M68kSimExceptionFrameDef;

typedef struct M68kSimExceptionFrameRule {
  uint8_t vector_start;
  uint8_t vector_end;
  uint32_t cpu_mask;
  uint8_t frame_kind;
} M68kSimExceptionFrameRule;

typedef struct M68kSimFormLookup {
  M68kFormId canonical_form_id;
  uint16_t asm_form_index;
  uint8_t semantic_status;
  uint8_t reserved;
  M68kSimFormMetadata metadata;
} M68kSimFormLookup;

typedef struct M68kSimTargetSet {
  size_t count;
  uint32_t targets[M68K_SIM_TARGET_LIMIT];
} M68kSimTargetSet;

typedef struct M68kSimValue {
  uint8_t kind;
  uint8_t section_index;
  uint8_t provenance;
  uint8_t reserved;
  uint32_t value;
  uint32_t table_start;
  uint32_t table_end;
  uint32_t table_stride;
  M68kSimTargetSet target_set;
} M68kSimValue;

typedef struct M68kSimCpuState {
  M68kSimValue d[8];
  M68kSimValue a[8];
  M68kSimValue c[M68K_SIM_CONTROL_REGISTER_LIMIT];
  uint32_t pc;
  uint16_t sr;
  uint8_t sr_known;
  uint8_t reserved0;
} M68kSimCpuState;

typedef struct M68kSimAccess {
  uint8_t kind;
  uint8_t width;
  uint8_t section_index;
  uint8_t reserved;
  uint32_t offset;
} M68kSimAccess;

typedef struct M68kSimMemoryCell {
  uint8_t width;
  uint8_t section_index;
  uint8_t reserved0;
  uint8_t reserved1;
  uint32_t offset;
  M68kSimValue value;
} M68kSimMemoryCell;

typedef struct M68kSimMemoryState {
  size_t cell_count;
  M68kSimMemoryCell cells[M68K_SIM_MEMORY_CELL_LIMIT];
} M68kSimMemoryState;

typedef struct M68kSimStepResult {
  M68kSimCpuState next_state;
  M68kSimTargetSet control_targets;
  M68kSimTargetSet discovered_labels;
  M68kSimAccess accesses[8];
  size_t access_count;
  M68kSimMemoryCell memory_writes[M68K_SIM_MEMORY_WRITE_LIMIT];
  size_t memory_write_count;
  int defines_condition_codes;
  int stops_fallthrough;
} M68kSimStepResult;

typedef struct M68kSimConcreteState {
  uint32_t d[8];
  uint32_t a[8];
  uint32_t c[M68K_SIM_CONTROL_REGISTER_LIMIT];
  uint32_t pc;
  uint16_t sr;
} M68kSimConcreteState;

typedef struct M68kSimConcreteWriteRange {
  uint32_t start;
  uint32_t end;
} M68kSimConcreteWriteRange;

typedef struct M68kSimConcreteWriteTrace {
  uint32_t memory_write_start;
  uint32_t memory_write_end;
  size_t memory_write_count;
  size_t memory_write_range_count;
  uint8_t memory_write_range_overflow;
  uint8_t reserved[7];
  M68kSimConcreteWriteRange memory_write_ranges[M68K_SIM_CONCRETE_WRITE_RANGE_LIMIT];
} M68kSimConcreteWriteTrace;

typedef int (*M68kSimConcreteExternalWriteAllowedFn)(void *user, uint32_t address, uint8_t width);
typedef int (*M68kSimConcreteExternalReadFn)(void *user, uint32_t address, uint8_t width, uint32_t *out_value);

typedef struct M68kSimConcreteMemoryPolicy {
  M68kSimConcreteExternalWriteAllowedFn external_write_allowed;
  M68kSimConcreteExternalReadFn external_read;
  void *user;
} M68kSimConcreteMemoryPolicy;

typedef enum M68kSimConcreteRunStopReason {
  M68K_SIM_CONCRETE_RUN_STOP_NONE = 0,
  M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE = 1,
  M68K_SIM_CONCRETE_RUN_STOP_PC_OUT_OF_RANGE = 2,
  M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT = 3,
  M68K_SIM_CONCRETE_RUN_STOP_DECODE_ERROR = 4,
  M68K_SIM_CONCRETE_RUN_STOP_SIMULATION_ERROR = 5,
  M68K_SIM_CONCRETE_RUN_STOP_BAD_ARGUMENT = 6
} M68kSimConcreteRunStopReason;

typedef struct M68kSimConcreteRunTraceResult {
  size_t step_count;
  uint32_t start_pc;
  uint32_t stop_pc;
  uint32_t memory_write_start;
  uint32_t memory_write_end;
  size_t memory_write_count;
  size_t memory_write_range_count;
  uint8_t memory_write_range_overflow;
  uint8_t reserved[7];
  M68kSimConcreteWriteRange memory_write_ranges[M68K_SIM_CONCRETE_WRITE_RANGE_LIMIT];
  M68kSimConcreteRunStopReason stop_reason;
  M68kDiagList diagnostics;
} M68kSimConcreteRunTraceResult;

void m68k_sim_target_set_init(M68kSimTargetSet *set);
int m68k_sim_target_set_add(M68kSimTargetSet *set, uint32_t target);
void m68k_sim_value_init_unknown(M68kSimValue *value);
void m68k_sim_cpu_state_init_unknown(M68kSimCpuState *state);
int m68k_sim_cpu_state_equal(const M68kSimCpuState *lhs, const M68kSimCpuState *rhs);
int m68k_sim_cpu_state_join(M68kSimCpuState *dst, const M68kSimCpuState *src);
void m68k_sim_memory_state_init(M68kSimMemoryState *state);
int m68k_sim_memory_state_equal(const M68kSimMemoryState *lhs, const M68kSimMemoryState *rhs);
int m68k_sim_memory_state_join(M68kSimMemoryState *dst, const M68kSimMemoryState *src);
int m68k_sim_memory_state_seed_same_section_fixups(const M68kObject *object, size_t section_index,
  const M68kSection *section, M68kSimMemoryState *state);
const M68kSimFormMetadata *m68k_sim_metadata_for_instruction(const M68kInstructionIR *instruction);
M68kSimMetadataStatus m68k_sim_metadata_for_canonical_form_id(M68kFormId form_id,
  const M68kSimFormMetadata **out_metadata);
int m68k_simulate_step(const M68kObject *object, size_t section_index, const M68kSection *section, uint32_t offset,
  const M68kInstructionIR *instruction, const M68kSimCpuState *state, M68kSimStepResult *out_result);
int m68k_simulate_step_with_memory(const M68kObject *object, size_t section_index, const M68kSection *section,
  uint32_t offset, const M68kInstructionIR *instruction, const M68kSimCpuState *state,
  const M68kSimMemoryState *memory_state, M68kSimStepResult *out_result);
int m68k_simulate_step_concrete(const M68kInstructionIR *instruction, uint8_t target_cpu,
    const uint8_t *code, size_t code_size, uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state,
    M68kSimConcreteWriteTrace *write_trace, const M68kSimConcreteMemoryPolicy *memory_policy,
    M68kDiagSink diagnostics);
int m68k_simulate_run_concrete(uint8_t target_cpu, uint8_t *memory, size_t memory_size,
    M68kSimConcreteState *io_state, size_t max_steps, uint32_t stop_pc_start, uint32_t stop_pc_end,
    const M68kSimConcreteMemoryPolicy *memory_policy, M68kSimConcreteRunTraceResult *out_result);

#endif
