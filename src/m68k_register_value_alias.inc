/* Must-equality of full CPU register values, independent of pointee type.
 * D0..D7/A0..A7 use decoded write-mask order. Four-bit representatives fit
 * all sixteen architectural registers in the previous eight-byte relation.
 * A missing equality never establishes disjoint memory. */
static uint8_t typed_register_alias_root(const M68kRenderTypedState *state, uint8_t reg) {
  uint8_t at = reg;
  uint32_t seen = 0U;
  while (at < 16U && m68k_bitset_u32_has(state->register_alias_known, at)) {
    if (seen & (1U << at)) return reg;
    seen |= 1U << at;
    uint8_t next = (state->register_alias_sources[at / 2U] >> ((at % 2U) * 4U)) & 15U;
    if (next == at) return reg;
    at = next;
  }
  return at;
}

static int typed_state_addr_alias_equal(const M68kRenderTypedState *state, uint8_t left, uint8_t right) {
  return state && left < 8U && right < 8U &&
    typed_register_alias_root(state, left + 8U) == typed_register_alias_root(state, right + 8U);
}

static void typed_register_alias_roots(const M68kRenderTypedState *state, uint8_t roots[16]) {
  for (uint8_t i = 0U; i < 16U; ++i) roots[i] = typed_register_alias_root(state, i);
}

static void typed_register_alias_store(M68kRenderTypedState *state, const uint8_t roots[16]) {
  state->register_alias_known = 0U;
  memset(state->register_alias_sources, 0, sizeof(state->register_alias_sources));
  for (uint8_t i = 0U; i < 16U; ++i) for (uint8_t j = 0U; j < i; ++j) if (roots[i] == roots[j]) {
    m68k_bitset_u32_set(&state->register_alias_known, i);
    state->register_alias_sources[i / 2U] |= (uint8_t)(j << ((i % 2U) * 4U));
    break;
  }
}

static void typed_state_clear_register_alias(M68kRenderTypedState *state, uint8_t reg) {
  uint8_t roots[16];
  if (!state || reg >= 16U) return;
  typed_register_alias_roots(state, roots);
  roots[reg] = (uint8_t)(16U + reg);
  typed_register_alias_store(state, roots);
}

static void typed_state_clear_addr_alias_for_reg(M68kRenderTypedState *state, uint8_t reg) {
  if (reg < 8U) typed_state_clear_register_alias(state, reg + 8U);
}

static int typed_register_alias_meet(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  uint8_t left[16], right[16], roots[16], before[8];
  uint32_t before_known = dest->register_alias_known;
  memcpy(before, dest->register_alias_sources, sizeof(before));
  typed_register_alias_roots(dest, left);
  typed_register_alias_roots(source, right);
  for (uint8_t i = 0U; i < 16U; ++i) {
    roots[i] = i;
    for (uint8_t j = 0U; j < i; ++j)
      if (left[i] == left[j] && right[i] == right[j]) { roots[i] = roots[j]; break; }
  }
  typed_register_alias_store(dest, roots);
  return before_known != dest->register_alias_known ||
    memcmp(before, dest->register_alias_sources, sizeof(before)) != 0;
}

static int typed_register_alias_operand(const M68kOperandIR *operand, uint8_t *reg) {
  if (operand_is_data_register_local(operand, reg)) return 1;
  if (operand_address_register_index_local(operand, reg)) { *reg += 8U; return 1; }
  return 0;
}

static void typed_register_alias_transfer(M68kRenderTypedState *state, const M68kInstructionIR *instruction,
    const uint8_t before[16]) {
  const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(instruction);
  uint8_t roots[16], source, dest;
  uint16_t writes = 0U;
  size_t from, to;
  /* Calls use the existing summary-owned clobber/preservation path. */
  if (metadata && metadata->flow_kind == M68K_SIM_FLOW_CALL) return;
  if (!metadata) {
    state->register_alias_known = 0U;
    memset(state->register_alias_sources, 0, sizeof(state->register_alias_sources));
    return;
  }
  memcpy(roots, before, sizeof(roots));
  for (size_t i = 0U; i < instruction->operand_count && i < 4U; ++i)
    writes |= platform_operand_register_write_mask(instruction, i);
  if (instruction_may_update_stack_pointer_from_metadata(instruction)) writes |= UINT16_C(0x8000);
  for (uint8_t i = 0U; i < 16U; ++i) if (writes & (1U << i)) roots[i] = (uint8_t)(16U + i);
  if (instruction->size_suffix == 'l' && instruction_move_operand_indices_from_metadata(instruction, &from, &to, NULL) &&
      typed_register_alias_operand(&instruction->operands[from], &source) &&
      typed_register_alias_operand(&instruction->operands[to], &dest)) roots[dest] = before[source];
  else if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS && instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest)) {
    int16_t displacement;
    if (operand_is_address_memory_local(&instruction->operands[0], &source, &displacement) && !displacement)
      roots[dest + 8U] = before[source + 8U];
  } else if (metadata->operation_type == M68K_SIM_OP_SWAP && instruction->operand_count == 2U &&
      typed_register_alias_operand(&instruction->operands[0], &source) &&
      typed_register_alias_operand(&instruction->operands[1], &dest)) {
    roots[dest] = before[source]; roots[source] = before[dest];
  }
  typed_register_alias_store(state, roots);
}
