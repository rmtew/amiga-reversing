#include "platform_amiga_bootloader_analysis.h"
#include "m68k_ir_codec.h"

#include <string.h>

static void *bootloader_grow_array(AmigaDiskAnalysis *analysis, void *items, size_t count, size_t *capacity,
    size_t item_size) {
    size_t next_capacity;
    void *grown;
    Arena *arena = analysis != NULL ? analysis->arena : NULL;
    if (arena == NULL) return NULL;
    if (count < *capacity) return items;
    next_capacity = (*capacity == 0U) ? 4U : (*capacity * 2U);
    grown = arena_realloc_copy(arena, items, count * item_size, next_capacity * item_size);
    if (grown == NULL) return NULL;
    *capacity = next_capacity;
    return grown;
}

typedef struct BootloaderHardwareSymbol {
    uint32_t address;
    const char *name;
} BootloaderHardwareSymbol;

static const BootloaderHardwareSymbol g_bootloader_hardware_symbols[] = {
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DSKPT_OFFSET, "dskpt" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DSKPT_OFFSET + 2U, "dskpt" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DSKLEN_OFFSET, "dsklen" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DSKDAT_OFFSET, "dskdat" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DSKBYTR_OFFSET, "dskbytr" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DSKSYNC_OFFSET, "dsksync" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_DMACON_OFFSET, "dmacon" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_INTREQ_OFFSET, "intreq" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CUSTOM_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_ADKCON_OFFSET, "adkcon" },
    { AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CIA_B_BASE_ADDRESS + AMIGA_DISK_FILE_CONSTRAINTS_AMIGA_CIAPRB_OFFSET, "ciaprb" },
};

static const char *bootloader_hardware_symbol_name(uint32_t address) {
    size_t i;
    for (i = 0; i < sizeof(g_bootloader_hardware_symbols) / sizeof(g_bootloader_hardware_symbols[0]); ++i) {
        if (g_bootloader_hardware_symbols[i].address == address) return g_bootloader_hardware_symbols[i].name;
    }
    return NULL;
}

static int append_bootloader_hardware_access(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage,
    uint32_t instruction_addr, const char *access, uint32_t width_bits, uint32_t address, uint8_t has_value,
    uint32_t value) {
    AmigaDiskBootloaderHardwareAccess *grown;
    AmigaDiskBootloaderHardwareAccess *item;
    const char *symbol = bootloader_hardware_symbol_name(address);
    if (symbol == NULL) return 0;
    grown = (AmigaDiskBootloaderHardwareAccess *)bootloader_grow_array(analysis, stage->hardware_accesses,
        stage->hardware_access_count, &stage->hardware_access_capacity, sizeof(*stage->hardware_accesses));
    if (grown == NULL) return -1;
    stage->hardware_accesses = grown;
    item = &stage->hardware_accesses[stage->hardware_access_count];
    memset(item, 0, sizeof(*item));
    item->instruction_addr = instruction_addr;
    item->access = arena_strdup(analysis->arena, access);
    item->width_bits = width_bits;
    item->address = address;
    item->symbol = arena_strdup(analysis->arena, symbol);
    item->has_value = has_value;
    item->value = value;
    if (item->access == NULL || item->symbol == NULL) return -1;
    stage->hardware_access_count += 1U;
    return 0;
}

static int append_bootloader_setup_value(AmigaDiskAnalysis *analysis, uint32_t **items, size_t *count, size_t *capacity,
    uint32_t value) {
    uint32_t *grown = (uint32_t *)bootloader_grow_array(analysis, *items, *count, capacity, sizeof(**items));
    if (grown == NULL) return -1;
    *items = grown;
    (*items)[*count] = value;
    *count += 1U;
    return 0;
}

int amiga_disk_append_bootloader_read_setup(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage) {
    AmigaDiskBootloaderReadSetup *grown;
    AmigaDiskBootloaderReadSetup *setup;
    size_t i;
    if (!stage->has_disk_read) return 0;
    grown = (AmigaDiskBootloaderReadSetup *)bootloader_grow_array(analysis, stage->read_setups, stage->read_setup_count,
        &stage->read_setup_capacity, sizeof(*stage->read_setups));
    if (grown == NULL) return -1;
    stage->read_setups = grown;
    setup = &stage->read_setups[stage->read_setup_count];
    memset(setup, 0, sizeof(*setup));
    setup->instruction_addr = stage->instruction_addr;
    setup->has_buffer_addr = 1U;
    setup->buffer_addr = stage->base_addr;
    setup->has_dma_byte_length = 1U;
    setup->dma_byte_length = stage->byte_length;
    for (i = 0; i < stage->hardware_access_count; ++i) {
        const AmigaDiskBootloaderHardwareAccess *access = &stage->hardware_accesses[i];
        if (!access->has_value || strcmp(access->access, "write") != 0) continue;
        if (strcmp(access->symbol, "dmacon") == 0) {
            if (append_bootloader_setup_value(analysis, &setup->dmacon_values, &setup->dmacon_value_count,
                    &setup->dmacon_value_capacity, access->value) != 0) return -1;
            setup->instruction_addr = access->instruction_addr;
        } else if (strcmp(access->symbol, "adkcon") == 0) {
            if (append_bootloader_setup_value(analysis, &setup->adkcon_values, &setup->adkcon_value_count,
                    &setup->adkcon_value_capacity, access->value) != 0) return -1;
        } else if (strcmp(access->symbol, "dsksync") == 0) {
            setup->has_sync_word = 1U;
            setup->sync_word = access->value;
        } else if (strcmp(access->symbol, "dsklen") == 0) {
            setup->has_dsklen_value = 1U;
            setup->dsklen_value = access->value;
            setup->dsklen_dma_enabled =
                (access->value & AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DSKLEN_DMA_ENABLE_MASK) != 0U;
            setup->dsklen_write =
                (access->value & AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DSKLEN_WRITE_MASK) != 0U;
            setup->has_dsklen_dma_byte_length = 1U;
            setup->dsklen_dma_byte_length =
                (access->value & AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DSKLEN_LENGTH_MASK) *
                AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_DSKLEN_LENGTH_UNIT_BYTES;
        } else if (strcmp(access->symbol, "dskpt") == 0) {
            setup->has_buffer_addr = 1U;
            setup->buffer_addr = access->value;
        } else if (strcmp(access->symbol, "ciaprb") == 0) {
            if ((access->value & AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_CIAPRB_DRIVE0_SELECT_MASK) == 0U) {
                setup->has_drive = 1U;
                setup->drive = 0U;
            }
            setup->has_head = 1U;
            setup->head =
                (access->value & AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_CIAPRB_SIDE_BIT_MASK) != 0U ? 0U : 1U;
            if (!setup->has_cylinder) {
                setup->has_cylinder = 1U;
                setup->cylinder = AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_INITIAL_CYLINDER;
            }
            setup->has_track = 1U;
            setup->track = setup->cylinder * 2U + setup->head;
        }
    }
    if (!setup->has_head) {
        setup->has_head = 1U;
        setup->head = AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_INITIAL_HEAD;
    }
    if (!setup->has_cylinder) {
        setup->has_cylinder = 1U;
        setup->cylinder = AMIGA_DISK_FILE_CONSTRAINTS_BOOTLOADER_INITIAL_CYLINDER;
    }
    if (!setup->has_track) {
        setup->has_track = 1U;
        setup->track = setup->cylinder * 2U + setup->head;
    }
    stage->read_setup_count += 1U;
    return 0;
}

static uint32_t bootloader_instruction_width_bits(const M68kInstructionIR *instruction) {
    if (instruction->size_suffix == 'b') return 8U;
    if (instruction->size_suffix == 'l') return 32U;
    return 16U;
}

static int32_t sign_extend16(uint32_t value) {
    return (int32_t)(int16_t)(value & 0xFFFFU);
}

static int bootloader_operand_absolute_address(const M68kOperandIR *operand, const uint32_t *address_regs,
    uint32_t *out_address) {
    if (operand->kind == M68K_ASM_OPERAND_ABSL) {
        *out_address = operand->value.value;
        return 1;
    }
    if (operand->kind == M68K_ASM_OPERAND_EA) {
        if (operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U)) {
            *out_address = operand->value.value;
            return 1;
        }
        if (operand->value.ea_mode == 5U && operand->value.ea_reg < 8U && address_regs[operand->value.ea_reg] != 0U) {
            *out_address = (uint32_t)(address_regs[operand->value.ea_reg] + sign_extend16(operand->value.value));
            return 1;
        }
        if (operand->value.ea_mode == 2U && operand->value.ea_reg < 8U && address_regs[operand->value.ea_reg] != 0U) {
            *out_address = address_regs[operand->value.ea_reg];
            return 1;
        }
    }
    return 0;
}

static uint32_t bootloader_width_mask(const M68kInstructionIR *instruction) {
    if (instruction->size_suffix == 'b') return 0xFFU;
    if (instruction->size_suffix == 'w') return 0xFFFFU;
    return 0xFFFFFFFFU;
}

static int bootloader_operand_data_reg_index(const M68kOperandIR *operand, uint8_t *out_reg) {
    if (operand->kind == M68K_ASM_OPERAND_DN && operand->value.reg < 8U) {
        *out_reg = operand->value.reg;
        return 1;
    }
    if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 0U && operand->value.ea_reg < 8U) {
        *out_reg = operand->value.ea_reg;
        return 1;
    }
    return 0;
}

static int bootloader_operand_postinc_addr_reg_index(const M68kOperandIR *operand, uint8_t *out_reg) {
    if (operand->kind == M68K_ASM_OPERAND_POSTINC && operand->value.ea_reg < 8U) {
        *out_reg = operand->value.ea_reg;
        return 1;
    }
    if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U && operand->value.ea_reg < 8U) {
        *out_reg = operand->value.ea_reg;
        return 1;
    }
    return 0;
}

static int bootloader_operand_immediate_value(const M68kOperandIR *operand, uint32_t *out_value) {
    if (operand->kind == M68K_ASM_OPERAND_IMM ||
        (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 4U)) {
        *out_value = operand->value.value;
        return 1;
    }
    return 0;
}

static int bootloader_operand_constant_value(const M68kOperandIR *operand, const uint8_t *data_reg_known,
    const uint32_t *data_regs, uint32_t *out_value) {
    uint8_t reg;
    if (bootloader_operand_immediate_value(operand, out_value)) return 1;
    if (bootloader_operand_data_reg_index(operand, &reg) && data_reg_known[reg]) {
        *out_value = data_regs[reg];
        return 1;
    }
    return 0;
}

static int bootloader_operand_direct_code_address(const AmigaDiskBootloaderStage *stage, const M68kInstructionIR *instruction,
    const M68kOperandIR *operand, uint32_t instruction_addr, const uint32_t *address_regs, uint32_t *out_address) {
    (void)stage;
    (void)instruction;
    if (operand->kind == M68K_ASM_OPERAND_LABEL) {
        *out_address = (uint32_t)((int32_t)instruction_addr + 2 + (int32_t)operand->value.value);
        return 1;
    }
    if (operand->kind == M68K_ASM_OPERAND_ABSL ||
        (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 1U)) {
        *out_address = operand->value.value;
        return 1;
    }
    if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 0U) {
        *out_address = operand->value.value & 0xFFFFU;
        return 1;
    }
    if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 2U) {
        *out_address = (uint32_t)((int32_t)instruction_addr + 2 + sign_extend16(operand->value.value));
        return 1;
    }
    return bootloader_operand_absolute_address(operand, address_regs, out_address);
}

static int bootloader_stage_offset_for_address(const AmigaDiskBootloaderStage *stage, uint32_t address, size_t *out_offset) {
    uint32_t relative;
    if (address < stage->base_addr) return 0;
    relative = address - stage->base_addr;
    if (relative >= stage->size || (relative & 1U) != 0U) return 0;
    *out_offset = relative;
    return 1;
}

static int bootloader_mnemonic_is_conditional_branch(uint8_t mnemonic_id) {
    return mnemonic_id >= M68K_ASM_MNEMONIC_BHI && mnemonic_id <= M68K_ASM_MNEMONIC_BLE;
}

static int bootloader_mnemonic_is_dbcc(uint8_t mnemonic_id) {
    return mnemonic_id >= M68K_ASM_MNEMONIC_DBT && mnemonic_id <= M68K_ASM_MNEMONIC_DBLE;
}

static int bootloader_mnemonic_ends_path(uint8_t mnemonic_id) {
    return mnemonic_id == M68K_ASM_MNEMONIC_RTS || mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
        mnemonic_id == M68K_ASM_MNEMONIC_RTR || mnemonic_id == M68K_ASM_MNEMONIC_STOP ||
        mnemonic_id == M68K_ASM_MNEMONIC_ILLEGAL;
}

static void bootloader_update_address_registers(const M68kInstructionIR *instruction, uint32_t instruction_addr,
    uint32_t *address_regs, const uint8_t *data_reg_known, const uint32_t *data_regs) {
    uint32_t address;
    const M68kOperandIR *source;
    const M68kOperandIR *dest;
    uint8_t source_reg;
    if (instruction->operand_count < 2U) return;
    source = &instruction->operands[0];
    dest = &instruction->operands[1];
    if (dest->kind != M68K_ASM_OPERAND_AN || dest->value.reg >= 8U) return;
    if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA && instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA &&
        instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) {
        return;
    }
    if (source->kind == M68K_ASM_OPERAND_EA && source->value.ea_mode == 7U && source->value.ea_reg == 2U) {
        address_regs[dest->value.reg] = (uint32_t)((int32_t)instruction_addr + 2 + sign_extend16(source->value.value));
    } else if (bootloader_operand_absolute_address(source, address_regs, &address)) address_regs[dest->value.reg] = address;
    else if (bootloader_operand_data_reg_index(source, &source_reg) && data_reg_known[source_reg])
        address_regs[dest->value.reg] = data_regs[source_reg];
    else if (source->kind == M68K_ASM_OPERAND_IMM) address_regs[dest->value.reg] = source->value.value;
}

static void bootloader_update_data_registers(const M68kInstructionIR *instruction, uint8_t *data_reg_known,
    uint32_t *data_regs) {
    uint8_t dest_reg;
    uint32_t source_value;
    uint32_t mask = bootloader_width_mask(instruction);
    uint32_t old_value;
    if (instruction->operand_count == 0U) return;
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ && instruction->operand_count == 2U &&
        bootloader_operand_data_reg_index(&instruction->operands[1], &dest_reg) &&
        bootloader_operand_immediate_value(&instruction->operands[0], &source_value)) {
        data_regs[dest_reg] = (uint32_t)(int32_t)(int8_t)(source_value & 0xFFU);
        data_reg_known[dest_reg] = 1U;
        return;
    }
    if (instruction->operand_count < 2U || !bootloader_operand_data_reg_index(&instruction->operands[1], &dest_reg)) return;
    old_value = data_regs[dest_reg];
    switch (instruction->mnemonic_id) {
        case M68K_ASM_MNEMONIC_MOVE:
            if (bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value)) {
                data_regs[dest_reg] = (old_value & ~mask) | (source_value & mask);
                data_reg_known[dest_reg] = 1U;
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        case M68K_ASM_MNEMONIC_ADD:
        case M68K_ASM_MNEMONIC_ADDI:
        case M68K_ASM_MNEMONIC_ADDQ:
            if (data_reg_known[dest_reg] &&
                bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value)) {
                data_regs[dest_reg] = (old_value & ~mask) | ((old_value + source_value) & mask);
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        case M68K_ASM_MNEMONIC_SUB:
        case M68K_ASM_MNEMONIC_SUBI:
        case M68K_ASM_MNEMONIC_SUBQ:
            if (data_reg_known[dest_reg] &&
                bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value)) {
                data_regs[dest_reg] = (old_value & ~mask) | ((old_value - source_value) & mask);
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        case M68K_ASM_MNEMONIC_AND:
        case M68K_ASM_MNEMONIC_ANDI:
            if (data_reg_known[dest_reg] &&
                bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value)) {
                data_regs[dest_reg] = old_value & source_value & mask;
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        case M68K_ASM_MNEMONIC_OR:
        case M68K_ASM_MNEMONIC_ORI:
            if (data_reg_known[dest_reg] &&
                bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value)) {
                data_regs[dest_reg] = (old_value | source_value) & mask;
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        case M68K_ASM_MNEMONIC_LSL:
            if (data_reg_known[dest_reg] &&
                bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value) &&
                source_value < 32U) {
                data_regs[dest_reg] = (old_value << source_value) & mask;
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        case M68K_ASM_MNEMONIC_LSR:
            if (data_reg_known[dest_reg] &&
                bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &source_value) &&
                source_value < 32U) {
                data_regs[dest_reg] = (old_value & mask) >> source_value;
            } else {
                data_reg_known[dest_reg] = 0U;
            }
            break;
        default:
            break;
    }
}

typedef struct BootloaderDecodeQueueItem {
    size_t offset;
    uint32_t runtime_addr;
    uint32_t address_regs[8];
    uint32_t data_regs[8];
    uint8_t data_reg_known[8];
    uint8_t has_code_alias;
    uint32_t code_alias_source_addr;
    uint32_t code_alias_dest_addr;
    uint32_t code_alias_length;
} BootloaderDecodeQueueItem;

static int append_bootloader_decode_queue_item(AmigaDiskAnalysis *analysis, BootloaderDecodeQueueItem **items,
    size_t *count, size_t *capacity, size_t offset, const uint32_t *address_regs, const uint8_t *data_reg_known,
    const uint32_t *data_regs, const BootloaderDecodeQueueItem *state) {
    BootloaderDecodeQueueItem *grown;
    if ((offset & 1U) != 0U) return 0;
    grown = (BootloaderDecodeQueueItem *)bootloader_grow_array(analysis, *items, *count, capacity, sizeof(**items));
    if (grown == NULL) return -1;
    *items = grown;
    (*items)[*count].offset = offset;
    (*items)[*count].runtime_addr = state != NULL ? state->runtime_addr : 0U;
    memcpy((*items)[*count].address_regs, address_regs, sizeof((*items)[*count].address_regs));
    memcpy((*items)[*count].data_regs, data_regs, sizeof((*items)[*count].data_regs));
    memcpy((*items)[*count].data_reg_known, data_reg_known, sizeof((*items)[*count].data_reg_known));
    (*items)[*count].has_code_alias = state != NULL ? state->has_code_alias : 0U;
    (*items)[*count].code_alias_source_addr = state != NULL ? state->code_alias_source_addr : 0U;
    (*items)[*count].code_alias_dest_addr = state != NULL ? state->code_alias_dest_addr : 0U;
    (*items)[*count].code_alias_length = state != NULL ? state->code_alias_length : 0U;
    *count += 1U;
    return 0;
}

static int bootloader_stage_offset_for_runtime_address(const AmigaDiskBootloaderStage *stage,
    const BootloaderDecodeQueueItem *state, uint32_t address, size_t *out_offset, uint32_t *out_runtime_addr) {
    if (bootloader_stage_offset_for_address(stage, address, out_offset)) {
        *out_runtime_addr = address;
        return 1;
    }
    if (state != NULL && state->has_code_alias &&
        address >= state->code_alias_dest_addr && address < state->code_alias_dest_addr + state->code_alias_length) {
        uint32_t source_addr = state->code_alias_source_addr + (address - state->code_alias_dest_addr);
        if (bootloader_stage_offset_for_address(stage, source_addr, out_offset)) {
            *out_runtime_addr = address;
            return 1;
        }
    }
    return 0;
}

static int enqueue_bootloader_code_address(AmigaDiskAnalysis *analysis, const AmigaDiskBootloaderStage *stage,
    BootloaderDecodeQueueItem **queue, size_t *queue_count, size_t *queue_capacity, uint32_t address,
    const uint32_t *address_regs, const uint8_t *data_reg_known, const uint32_t *data_regs,
    const BootloaderDecodeQueueItem *state) {
    size_t target_offset;
    uint32_t runtime_addr;
    BootloaderDecodeQueueItem queued_state;
    if (!bootloader_stage_offset_for_runtime_address(stage, state, address, &target_offset, &runtime_addr)) return 0;
    queued_state = state != NULL ? *state : (BootloaderDecodeQueueItem){0};
    queued_state.runtime_addr = runtime_addr;
    return append_bootloader_decode_queue_item(analysis, queue, queue_count, queue_capacity, target_offset, address_regs,
        data_reg_known, data_regs, &queued_state);
}

static int enqueue_bootloader_fallthrough(AmigaDiskAnalysis *analysis, const AmigaDiskBootloaderStage *stage,
    BootloaderDecodeQueueItem **queue, size_t *queue_count, size_t *queue_capacity, size_t offset,
    const M68kInstructionIR *instruction, const uint32_t *address_regs, const uint8_t *data_reg_known,
    const uint32_t *data_regs, const BootloaderDecodeQueueItem *state) {
    size_t next_offset = offset + instruction->byte_count;
    BootloaderDecodeQueueItem queued_state;
    if (next_offset >= stage->size) return 0;
    queued_state = state != NULL ? *state : (BootloaderDecodeQueueItem){0};
    queued_state.runtime_addr = (state != NULL && state->runtime_addr != 0U)
        ? state->runtime_addr + (uint32_t)instruction->byte_count
        : stage->base_addr + (uint32_t)next_offset;
    return append_bootloader_decode_queue_item(analysis, queue, queue_count, queue_capacity, next_offset, address_regs,
        data_reg_known, data_regs, &queued_state);
}

static void bootloader_update_code_alias(const AmigaDiskBootloaderStage *stage, const M68kInstructionIR *instruction,
    BootloaderDecodeQueueItem *state, const uint32_t *address_regs, const uint8_t *data_reg_known,
    const uint32_t *data_regs) {
    uint8_t source_reg;
    uint8_t dest_reg;
    if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || instruction->size_suffix != 'l' ||
        instruction->operand_count < 2U) {
        return;
    }
    if (!bootloader_operand_postinc_addr_reg_index(&instruction->operands[0], &source_reg) ||
        !bootloader_operand_postinc_addr_reg_index(&instruction->operands[1], &dest_reg)) {
        return;
    }
    if (address_regs[source_reg] == 0U || address_regs[dest_reg] == 0U) return;
    state->has_code_alias = 1U;
    state->code_alias_source_addr = address_regs[source_reg];
    state->code_alias_dest_addr = address_regs[dest_reg];
    state->code_alias_length = data_reg_known[0] ? (data_regs[0] + 1U) * 4U : stage->size;
}

static int analyze_bootloader_instruction_accesses(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage,
    const M68kInstructionIR *instruction, uint32_t instruction_addr, const uint32_t *address_regs,
    const uint8_t *data_reg_known, const uint32_t *data_regs) {
    size_t operand_index;
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
        const M68kOperandIR *operand = &instruction->operands[operand_index];
        uint32_t address;
        const char *access = "read";
        uint8_t has_value = 0U;
        uint32_t value = 0U;
        if (!bootloader_operand_absolute_address(operand, address_regs, &address)) continue;
        if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && operand_index + 1U == instruction->operand_count) {
            access = "write";
            if (instruction->operands[0].kind == M68K_ASM_OPERAND_IMM) {
                has_value = 1U;
                value = instruction->operands[0].value.value;
            } else if (instruction->operands[0].kind == M68K_ASM_OPERAND_EA &&
                instruction->operands[0].value.ea_mode == 7U && instruction->operands[0].value.ea_reg == 4U) {
                has_value = 1U;
                value = instruction->operands[0].value.value;
            } else if (bootloader_operand_constant_value(&instruction->operands[0], data_reg_known, data_regs, &value)) {
                has_value = 1U;
            }
            if (instruction->size_suffix == 'b' && has_value) value &= 0xFFU;
            else if (instruction->size_suffix != 'l' && has_value) value &= 0xFFFFU;
        }
        if (append_bootloader_hardware_access(analysis, stage, instruction_addr, access,
                bootloader_instruction_width_bits(instruction), address, has_value, value) != 0) {
            return -1;
        }
    }
    return 0;
}

static int enqueue_bootloader_successors(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage,
    BootloaderDecodeQueueItem **queue, size_t *queue_count, size_t *queue_capacity, size_t offset,
    const M68kInstructionIR *instruction, const uint32_t *address_regs, const uint8_t *data_reg_known,
    const uint32_t *data_regs, const BootloaderDecodeQueueItem *state) {
    uint32_t instruction_addr = state != NULL && state->runtime_addr != 0U ? state->runtime_addr : stage->base_addr + (uint32_t)offset;
    uint32_t target_addr = 0U;
    if (bootloader_mnemonic_ends_path(instruction->mnemonic_id)) return 0;
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_BRA || instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
        bootloader_mnemonic_is_conditional_branch(instruction->mnemonic_id)) {
        if (instruction->operand_count != 0U &&
            bootloader_operand_direct_code_address(stage, instruction, &instruction->operands[0], instruction_addr,
                address_regs, &target_addr) &&
            enqueue_bootloader_code_address(analysis, stage, queue, queue_count, queue_capacity, target_addr, address_regs,
                data_reg_known, data_regs, state) != 0) {
            return -1;
        }
        if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_BRA) return 0;
        return enqueue_bootloader_fallthrough(analysis, stage, queue, queue_count, queue_capacity, offset, instruction,
            address_regs, data_reg_known, data_regs, state);
    }
    if (bootloader_mnemonic_is_dbcc(instruction->mnemonic_id)) {
        if (instruction->operand_count >= 2U &&
            bootloader_operand_direct_code_address(stage, instruction, &instruction->operands[1], instruction_addr,
                address_regs, &target_addr) &&
            enqueue_bootloader_code_address(analysis, stage, queue, queue_count, queue_capacity, target_addr, address_regs,
                data_reg_known, data_regs, state) != 0) {
            return -1;
        }
        return enqueue_bootloader_fallthrough(analysis, stage, queue, queue_count, queue_capacity, offset, instruction,
            address_regs, data_reg_known, data_regs, state);
    }
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP || instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR) {
        if (instruction->operand_count != 0U &&
            bootloader_operand_direct_code_address(stage, instruction, &instruction->operands[0], instruction_addr,
                address_regs, &target_addr) &&
            enqueue_bootloader_code_address(analysis, stage, queue, queue_count, queue_capacity, target_addr, address_regs,
                data_reg_known, data_regs, state) != 0) {
            return -1;
        }
        if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) return 0;
    }
    return enqueue_bootloader_fallthrough(analysis, stage, queue, queue_count, queue_capacity, offset, instruction,
        address_regs, data_reg_known, data_regs, state);
}

int amiga_disk_analyze_bootloader_stage_bytes(AmigaDiskAnalysis *analysis, AmigaDiskBootloaderStage *stage,
    const unsigned char *data, size_t size) {
    BootloaderDecodeQueueItem *queue = NULL;
    size_t queue_count = 0U;
    size_t queue_capacity = 0U;
    size_t queue_index = 0U;
    uint8_t *visited;
    size_t entry_offset = 0U;
    uint32_t zero_regs[8] = {0};
    uint8_t zero_known[8] = {0};
    BootloaderDecodeQueueItem initial_state = {0};
    if (size == 0U) return 0;
    visited = (uint8_t *)arena_alloc(analysis->arena, size);
    if (visited == NULL) return -1;
    memset(visited, 0, size);
    if (!bootloader_stage_offset_for_address(stage, stage->entry_addr, &entry_offset)) entry_offset = 0U;
    initial_state.runtime_addr = stage->entry_addr;
    if (append_bootloader_decode_queue_item(analysis, &queue, &queue_count, &queue_capacity, entry_offset, zero_regs,
            zero_known, zero_regs, &initial_state) != 0) return -1;
    while (queue_index < queue_count) {
        BootloaderDecodeQueueItem item = queue[queue_index++];
        M68kDiagList diagnostics;
        M68kInstructionIR instruction;
        uint32_t address_regs[8];
        uint32_t data_regs[8];
        uint8_t data_reg_known[8];
        if (item.offset + 2U > size || visited[item.offset]) continue;
        memcpy(address_regs, item.address_regs, sizeof(address_regs));
        memcpy(data_regs, item.data_regs, sizeof(data_regs));
        memcpy(data_reg_known, item.data_reg_known, sizeof(data_reg_known));
        m68k_diag_list_reset(&diagnostics);
        instruction = m68k_ir_decode_one(data + item.offset, size - item.offset, M68K_ASM_CPU_68000, m68k_diag_sink(&diagnostics));
        if (instruction.byte_count == 0U || item.offset + instruction.byte_count > size) continue;
        visited[item.offset] = 1U;
        stage->reachable_instruction_count += 1U;
        bootloader_update_address_registers(&instruction,
            item.runtime_addr != 0U ? item.runtime_addr : stage->base_addr + (uint32_t)item.offset,
            address_regs, data_reg_known, data_regs);
        if (analyze_bootloader_instruction_accesses(analysis, stage, &instruction,
                item.runtime_addr != 0U ? item.runtime_addr : stage->base_addr + (uint32_t)item.offset,
                address_regs, data_reg_known, data_regs) != 0) {
            return -1;
        }
        bootloader_update_code_alias(stage, &instruction, &item, address_regs, data_reg_known, data_regs);
        bootloader_update_data_registers(&instruction, data_reg_known, data_regs);
        if (enqueue_bootloader_successors(analysis, stage, &queue, &queue_count, &queue_capacity, item.offset, &instruction,
                address_regs, data_reg_known, data_regs, &item) != 0) {
            return -1;
        }
    }
    return 0;
}


