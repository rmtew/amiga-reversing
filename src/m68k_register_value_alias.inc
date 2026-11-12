/* Must-relations between held full CPU values: value = representative + delta
 * modulo 2^32. Representatives are live registers, never formal/guest addresses.
 * Missing relations never establish disjointness. Existing equality consumers
 * see only zero differences; LEA deltas do not become pointer/type classifiers. */
typedef struct M68kRegisterAliasSnapshot {
  uint8_t roots[16];
  uint32_t offsets[16];
} M68kRegisterAliasSnapshot;

static uint8_t typed_register_relative_root(const M68kRenderTypedState *state, uint8_t reg,
    uint32_t *offset) {
  uint8_t at = reg;
  uint32_t seen = 0U, delta = 0U;
  while (at < 16U && m68k_bitset_u32_has(state->register_alias_known, at)) {
    if (seen & (1U << at)) { *offset = 0U; return reg; }
    seen |= 1U << at;
    uint8_t next = (state->register_alias_sources[at / 2U] >> ((at % 2U) * 4U)) & 15U;
    if (next == at) { *offset = 0U; return reg; }
    delta += state->register_alias_offsets[at];
    at = next;
  }
  *offset = delta;
  return at;
}

static int typed_register_relative_difference(const M68kRenderTypedState *state,
    uint8_t left, uint8_t right, uint32_t *difference) {
  uint32_t a, b;
  if (!state || left >= 16U || right >= 16U ||
      typed_register_relative_root(state, left, &a) != typed_register_relative_root(state, right, &b)) return 0;
  *difference = a - b;
  return 1;
}

static uint8_t typed_register_alias_root(const M68kRenderTypedState *state, uint8_t reg) {
  uint32_t offset, other_offset;
  uint8_t root = typed_register_relative_root(state, reg, &offset);
  if (root == reg || !offset) return root;
  for (uint8_t i = root + 1U; i < reg; ++i)
    if (typed_register_relative_root(state, i, &other_offset) == root && other_offset == offset) return i;
  return reg;
}

static int typed_state_addr_alias_equal(const M68kRenderTypedState *state, uint8_t left, uint8_t right) {
  uint32_t difference;
  return left < 8U && right < 8U &&
    typed_register_relative_difference(state, left + 8U, right + 8U, &difference) && !difference;
}

static void typed_register_alias_snapshot(const M68kRenderTypedState *state, M68kRegisterAliasSnapshot *snapshot) {
  for (uint8_t i = 0U; i < 16U; ++i)
    snapshot->roots[i] = typed_register_relative_root(state, i, &snapshot->offsets[i]);
}

static void typed_register_alias_store(M68kRenderTypedState *state, const M68kRegisterAliasSnapshot *snapshot) {
  state->register_alias_known = 0U;
  memset(state->register_alias_sources, 0, sizeof(state->register_alias_sources));
  memset(state->register_alias_offsets, 0, sizeof(state->register_alias_offsets));
  for (uint8_t i = 0U; i < 16U; ++i) for (uint8_t j = 0U; j < i; ++j)
    if (snapshot->roots[i] == snapshot->roots[j]) {
      m68k_bitset_u32_set(&state->register_alias_known, i);
      state->register_alias_sources[i / 2U] |= (uint8_t)(j << ((i % 2U) * 4U));
      state->register_alias_offsets[i] = snapshot->offsets[i] - snapshot->offsets[j];
      break;
    }
}

static void typed_state_clear_register_alias(M68kRenderTypedState *state, uint8_t reg) {
  M68kRegisterAliasSnapshot snapshot;
  if (!state || reg >= 16U) return;
  typed_register_alias_snapshot(state, &snapshot);
  snapshot.roots[reg] = (uint8_t)(16U + reg);
  snapshot.offsets[reg] = 0U;
  typed_register_alias_store(state, &snapshot);
}

static void typed_state_clear_addr_alias_for_reg(M68kRenderTypedState *state, uint8_t reg) {
  if (reg < 8U) typed_state_clear_register_alias(state, reg + 8U);
}

static int typed_register_alias_meet(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  M68kRegisterAliasSnapshot left, right, result;
  uint8_t before[8]; uint32_t offsets[16], before_known = dest->register_alias_known;
  memcpy(before, dest->register_alias_sources, sizeof(before));
  memcpy(offsets, dest->register_alias_offsets, sizeof(offsets));
  typed_register_alias_snapshot(dest, &left);
  typed_register_alias_snapshot(source, &right);
  for (uint8_t i = 0U; i < 16U; ++i) {
    result.roots[i] = i; result.offsets[i] = 0U;
    for (uint8_t j = 0U; j < i; ++j)
      if (left.roots[i] == left.roots[j] && right.roots[i] == right.roots[j] &&
          left.offsets[i] - left.offsets[j] == right.offsets[i] - right.offsets[j]) {
        result.roots[i] = result.roots[j];
        result.offsets[i] = result.offsets[j] + left.offsets[i] - left.offsets[j];
        break;
      }
  }
  typed_register_alias_store(dest, &result);
  return before_known != dest->register_alias_known ||
    memcmp(before, dest->register_alias_sources, sizeof(before)) != 0 ||
    memcmp(offsets, dest->register_alias_offsets, sizeof(offsets)) != 0;
}

static int typed_register_alias_operand(const M68kOperandIR *operand, uint8_t *reg) {
  if (operand_is_data_register_local(operand, reg)) return 1;
  if (operand_address_register_index_local(operand, reg)) { *reg += 8U; return 1; }
  return 0;
}

/* No relation/predicate preservation promise is available for unmodelled
 * named-register effects. For example, a status write may switch active SP. */
static int typed_register_relation_opaque_effect(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata) {
  if (!metadata || metadata->flow_kind == M68K_SIM_FLOW_TRAP) return 1;
  for (size_t i = 0U; i < instruction->operand_count && i < 4U; ++i)
    if (metadata->operand_access_kinds[i] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        !platform_operand_register_write_mask(instruction, i)) return 1;
  return 0;
}

static void typed_register_alias_transfer(M68kRenderTypedState *state, const M68kInstructionIR *instruction,
    const M68kRegisterAliasSnapshot *before) {
  const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(instruction);
  M68kRegisterAliasSnapshot result = *before;
  uint8_t source, dest;
  uint16_t writes = 0U;
  size_t from, to;
  /* Calls use the existing summary-owned clobber/preservation path. */
  if (metadata && metadata->flow_kind == M68K_SIM_FLOW_CALL) return;
  if (typed_register_relation_opaque_effect(instruction, metadata)) {
    state->register_alias_known = 0U;
    memset(state->register_alias_sources, 0, sizeof(state->register_alias_sources));
    memset(state->register_alias_offsets, 0, sizeof(state->register_alias_offsets));
    return;
  }
  for (size_t i = 0U; i < instruction->operand_count && i < 4U; ++i) {
    uint16_t mask = platform_operand_register_write_mask(instruction, i);
    writes |= mask;
  }
  if (instruction_may_update_stack_pointer_from_metadata(instruction)) writes |= UINT16_C(0x8000);
  for (uint8_t i = 0U; i < 16U; ++i) if (writes & (1U << i)) {
    result.roots[i] = (uint8_t)(16U + i); result.offsets[i] = 0U;
  }
  if (instruction->size_suffix == 'l' && instruction_move_operand_indices_from_metadata(instruction, &from, &to, NULL) &&
      typed_register_alias_operand(&instruction->operands[from], &source) &&
      typed_register_alias_operand(&instruction->operands[to], &dest)) {
    result.roots[dest] = before->roots[source]; result.offsets[dest] = before->offsets[source];
  } else if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS && instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest)) {
    int16_t displacement;
    if (operand_is_address_memory_local(&instruction->operands[0], &source, &displacement)) {
      result.roots[dest + 8U] = before->roots[source + 8U];
      result.offsets[dest + 8U] = before->offsets[source + 8U] + (uint32_t)(int32_t)displacement;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_SWAP && instruction->operand_count == 2U &&
      typed_register_alias_operand(&instruction->operands[0], &source) &&
      typed_register_alias_operand(&instruction->operands[1], &dest)) {
    result.roots[dest] = before->roots[source]; result.offsets[dest] = before->offsets[source];
    result.roots[source] = before->roots[dest]; result.offsets[source] = before->offsets[dest];
  }
  typed_register_alias_store(state, &result);
}
