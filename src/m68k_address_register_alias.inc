/* Must-equality of current address-register values, independent of pointee
 * interpretation. Canonical representatives reuse the existing eight slots.
 * The meet is equivalence-relation intersection, never a may-alias union. */
static uint8_t typed_addr_alias_root(const M68kRenderTypedState *state, uint8_t reg) {
  uint8_t at = reg; uint16_t seen = 0U;
  while (at < 8U && m68k_bitset_u32_has(state->addr_reg_alias_known, at)) {
    if ((seen & (1U << at)) != 0U) return reg;
    seen |= (uint16_t)(1U << at);
    uint8_t next = state->addr_reg_alias_source[at];
    if (next >= 8U || next == at) return reg;
    at = next;
  }
  return at;
}

static int typed_state_addr_alias_equal(const M68kRenderTypedState *state, uint8_t left, uint8_t right) {
  return state && left < 8U && right < 8U && typed_addr_alias_root(state,left) == typed_addr_alias_root(state,right);
}

static void typed_addr_alias_roots(const M68kRenderTypedState *state, uint8_t roots[8]) {
  for (uint8_t i=0U;i<8U;++i) roots[i]=typed_addr_alias_root(state,i);
}

static void typed_addr_alias_store(M68kRenderTypedState *state, const uint8_t roots[8]) {
  state->addr_reg_alias_known=0U;
  memset(state->addr_reg_alias_source,0,sizeof(state->addr_reg_alias_source));
  for (uint8_t i=0U;i<8U;++i) for (uint8_t j=0U;j<i;++j) if (roots[i]==roots[j]) {
    m68k_bitset_u32_set(&state->addr_reg_alias_known,i);
    state->addr_reg_alias_source[i]=j;
    break;
  }
}

static void typed_state_clear_addr_alias_for_reg(M68kRenderTypedState *state, uint8_t reg) {
  uint8_t roots[8];
  if (!state || reg>=8U) return;
  typed_addr_alias_roots(state,roots);
  roots[reg]=(uint8_t)(8U+reg);
  typed_addr_alias_store(state,roots);
}

static int typed_addr_alias_meet(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  uint8_t left[8],right[8],roots[8],before[8];
  uint32_t before_known=dest->addr_reg_alias_known;
  memcpy(before,dest->addr_reg_alias_source,sizeof(before));
  typed_addr_alias_roots(dest,left);typed_addr_alias_roots(source,right);
  for(uint8_t i=0U;i<8U;++i) {
    roots[i]=i;
    for(uint8_t j=0U;j<i;++j) if(left[i]==left[j] && right[i]==right[j]) {roots[i]=roots[j];break;}
  }
  typed_addr_alias_store(dest,roots);
  return before_known!=dest->addr_reg_alias_known || memcmp(before,dest->addr_reg_alias_source,sizeof(before))!=0;
}

static void typed_addr_alias_transfer(M68kRenderTypedState *state, const M68kInstructionIR *instruction,
    const uint8_t before[8]) {
  const M68kSimFormMetadata *metadata=m68k_sim_metadata_for_instruction(instruction);
  uint8_t roots[8],source,dest;
  uint16_t writes=0U;
  size_t from,to;
  /* Calls use the existing summary-owned clobber/preservation path. */
  if (metadata && metadata->flow_kind==M68K_SIM_FLOW_CALL) return;
  if (!metadata) {state->addr_reg_alias_known=0U;memset(state->addr_reg_alias_source,0,8U);return;}
  memcpy(roots,before,sizeof(roots));
  for(size_t i=0U;i<instruction->operand_count && i<4U;++i)
    writes|=platform_operand_register_write_mask(instruction,i);
  if (instruction_may_update_stack_pointer_from_metadata(instruction)) writes |= UINT16_C(0x8000);
  for(uint8_t i=0U;i<8U;++i) if(writes & (1U<<(8U+i))) roots[i]=(uint8_t)(8U+i);
  if (instruction->size_suffix=='l' && instruction_move_operand_indices_from_metadata(instruction,&from,&to,NULL) &&
      operand_address_register_index_local(&instruction->operands[from],&source) &&
      operand_address_register_index_local(&instruction->operands[to],&dest)) roots[dest]=before[source];
  else if (metadata->operation_class==M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS && instruction->operand_count==2U &&
      operand_address_register_index_local(&instruction->operands[1],&dest)) {
    int16_t displacement;
    if(operand_is_address_memory_local(&instruction->operands[0],&source,&displacement) && !displacement)
      roots[dest]=before[source];
  } else if(metadata->operation_type==M68K_SIM_OP_SWAP && instruction->operand_count==2U &&
      operand_address_register_index_local(&instruction->operands[0],&source) &&
      operand_address_register_index_local(&instruction->operands[1],&dest)) {
    roots[dest]=before[source];roots[source]=before[dest];
  }
  typed_addr_alias_store(state,roots);
}
