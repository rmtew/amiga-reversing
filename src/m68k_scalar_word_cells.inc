/* Local scalar WORD definitions in the existing canonical sparse cells. These
 * bits are neither pointer intent nor a cross-program writer summary. Register
 * values and indexed consumers still use the shared finite WORD abstraction. */
typedef struct M68kScalarWordTransfer {
  uint32_t storage_id;
  uint16_t value, mask;
  uint8_t read_register, has_read;
  M68kHardwareWordSet read_values;
} M68kScalarWordTransfer;

static uint32_t scalar_word_cell_id(M68kRenderLookup *lookup,const M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform,size_t section,const M68kOperandIR *operand,int create,int *changed) {
  uint8_t kind;size_t owner;int32_t delta;uint32_t address;
  if(!typed_storage_key_for_lookup_memory_operand(lookup,state,platform,section,operand,
      create ? M68K_SIM_ACCESS_MEMORY_WRITE : M68K_SIM_ACCESS_MEMORY_READ,&kind,&owner,&delta,&address) ||
      (kind!=M68K_RENDER_TYPED_STORAGE_APP_SLOT && kind!=M68K_RENDER_TYPED_STORAGE_ABSOLUTE) ||
      typed_storage_write_is_hardware(lookup,platform,operand,1U)) return 0U;
  if(kind==M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
    uint8_t reg;int16_t displacement;
    if(!operand_is_address_memory_local(operand,&reg,&displacement) || reg>=8U ||
        (!m68k_bitset_u32_has(platform->address_app_base_known,reg) &&
         !(state->app_addr_regs[reg].known &&
           state->app_addr_regs[reg].base_evidence_kind==M68K_APP_SLOT_BASE_REGISTER_STATE)))return 0U;
  }
  uint32_t id=typed_memory_storage_id(lookup,kind,owner,delta,address);
  if(create) {
    int added=0;
    M68kRenderTypedStorageSlot *slot=typed_storage_reserve_identity(lookup,kind,owner,delta,address,&added);
    if(!slot) {lookup->source_domain_error=1U;return 0U;}
    if(!slot->scalar_word_cell) {slot->scalar_word_cell=1U;added=1;}
    if(added && changed)*changed=1;
    id=typed_memory_storage_id(lookup,kind,owner,delta,address);
  }
  return id && lookup->typed_storage_slots[id-1U].scalar_word_cell ? id : 0U;
}

static M68kHardwareWordSet scalar_word_values(uint16_t value,uint16_t mask) {
  M68kHardwareWordSet result={0};uint16_t free_bits=(uint16_t)~mask,bits=free_bits;
  unsigned count=0;while(bits) {bits&=(uint16_t)(bits-1U);++count;}
  if((1U<<count)>M68K_HARDWARE_VALUE_LIMIT)return result;
  uint16_t subset=free_bits;
  for(;;) {
    if(!hardware_word_set_add(&result,(uint16_t)((value&mask)|subset)))return (M68kHardwareWordSet){0};
    if(!subset)break;
    subset=(uint16_t)((subset-1U)&free_bits);
  }
  return result;
}

static M68kHardwareWordSet scalar_word_operand(M68kRenderLookup *lookup,const M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform,size_t section,const M68kOperandIR *operand) {
  M68kHardwareWordSet result=hardware_operand_word_values(platform,operand);
  if(result.count)return result;
  uint32_t id=scalar_word_cell_id(lookup,state,platform,section,operand,0,NULL);
  const M68kRenderTypedBaseSlot *cell=typed_state_memory_cell(state,id);
  return cell && cell->scalar_word_mask ? scalar_word_values(cell->scalar_word_value,cell->scalar_word_mask) : result;
}

static M68kScalarWordTransfer scalar_word_prepare(M68kRenderLookup *lookup,
    const M68kRenderTypedState *state,const M68kRenderPlatformState *platform,size_t section,
    const M68kInstructionIR *instruction,int discover,int *changed) {
  M68kScalarWordTransfer result={0};
  const M68kSimFormMetadata *meta=m68k_sim_metadata_for_instruction(instruction);
  uint8_t width,count,reg,address;
  if(!meta)return result;
  size_t source=meta->source_operand_index,dest=meta->dest_operand_index;
  int move=meta->operation_type==M68K_SIM_OP_MOVE && instruction->operand_count==2U;
  if(move && source<instruction->operand_count && dest<instruction->operand_count &&
      m68k_sim_operand_width_bytes(instruction,(uint8_t)source)==2U &&
      platform_operand_memory_access(instruction,source)==M68K_SIM_ACCESS_MEMORY_READ &&
      m68k_instruction_operand_direct_register(&instruction->operands[dest],&address,&reg) && !address) {
    result.read_values=scalar_word_operand(lookup,state,platform,section,&instruction->operands[source]);
    result.has_read=result.read_values.count!=0U;result.read_register=reg;
  }
  if(dest>=instruction->operand_count ||
      platform_operand_memory_access(instruction,dest)!=M68K_SIM_ACCESS_MEMORY_WRITE ||
      !platform_operand_memory_span(instruction,dest,&width,&count,NULL) || width!=2U || count!=1U)return result;
  uint32_t immediate=0U;
  int masked=meta->operation_type==M68K_SIM_OP_LOGIC_AND && source<instruction->operand_count &&
      m68k_ir_operand_immediate_value(&instruction->operands[source],&immediate) && (uint16_t)~immediate;
  result.storage_id=scalar_word_cell_id(lookup,state,platform,section,&instruction->operands[dest],
    masked && discover,changed);
  if(!result.storage_id)return result;
  if(masked) {
    const M68kRenderTypedBaseSlot *old=typed_state_memory_cell(state,result.storage_id);
    result.mask=(uint16_t)~immediate;
    if(old) {result.mask|=old->scalar_word_mask;result.value=old->scalar_word_value&(uint16_t)immediate;}
  } else if(meta->operation_type==M68K_SIM_OP_CLEAR)result.mask=UINT16_MAX;
  else if(move) {
    M68kHardwareWordSet values=scalar_word_operand(lookup,state,platform,section,&instruction->operands[source]);
    if(values.count && !values.requires_input_contract) {
      result.mask=UINT16_MAX;result.value=values.values[0];
      for(size_t i=1;i<values.count;++i)result.mask&=(uint16_t)~(result.value^values.values[i]);
    }
  }
  result.value&=result.mask;
  return result;
}

static void scalar_word_commit(M68kRenderTypedState *state,const M68kScalarWordTransfer *transfer) {
  if(!transfer->storage_id || !transfer->mask)return;
  size_t i=0U;
  while(i<state->base_slot_count && state->base_slots[i].storage_id!=transfer->storage_id)++i;
  if(i==state->base_slot_count) {
    if(i==M68K_RENDER_TYPED_BASE_SLOT_LIMIT)return;
    ++state->base_slot_count;memset(&state->base_slots[i],0,sizeof(state->base_slots[i]));
    state->base_slots[i].known=1U;state->base_slots[i].base_reg=UINT8_MAX;
    state->base_slots[i].storage_id=transfer->storage_id;
  }
  state->base_slots[i].scalar_word_mask=transfer->mask;
  state->base_slots[i].scalar_word_value=transfer->value;
}

/* Scratch-only sparse packets for the independent WORD solve. Only live cells
 * allocate entries; no second retained per-node slot/state array is added. */
typedef struct M68kScalarWordPacket {
  size_t count;
  struct {uint32_t id;uint16_t value,mask;} cells[];
} M68kScalarWordPacket;

static void scalar_word_packet_unpack(M68kRenderTypedState *state,const M68kScalarWordPacket *packet) {
  if(!packet)return;
  for(size_t i=0U;i<packet->count && i<M68K_RENDER_TYPED_BASE_SLOT_LIMIT;++i) {
    M68kRenderTypedBaseSlot *slot=&state->base_slots[state->base_slot_count++];
    slot->known=1U;slot->base_reg=UINT8_MAX;slot->storage_id=packet->cells[i].id;
    slot->scalar_word_value=packet->cells[i].value;slot->scalar_word_mask=packet->cells[i].mask;
  }
}

static int scalar_word_packet_equal(const M68kScalarWordPacket *packet,const M68kRenderTypedState *state) {
  size_t count=0U;
  for(size_t i=0U;i<state->base_slot_count;++i) {
    const M68kRenderTypedBaseSlot *slot=&state->base_slots[i];
    if(!slot->known || !slot->storage_id || !slot->scalar_word_mask)continue;
    if(!packet || count>=packet->count)return 0;
    size_t j=0U;
    while(j<packet->count && packet->cells[j].id!=slot->storage_id)++j;
    if(j==packet->count || packet->cells[j].value!=slot->scalar_word_value ||
        packet->cells[j].mask!=slot->scalar_word_mask)return 0;
    ++count;
  }
  return count==(packet ? packet->count : 0U);
}

static int scalar_word_packet_store(Arena *arena,M68kScalarWordPacket **output,const M68kRenderTypedState *state) {
  size_t count=0U;
  for(size_t i=0U;i<state->base_slot_count;++i)
    count+=state->base_slots[i].known && state->base_slots[i].storage_id && state->base_slots[i].scalar_word_mask;
  if(!count) {*output=NULL;return 1;}
  M68kScalarWordPacket *packet=arena_alloc(arena,sizeof(*packet)+count*sizeof(packet->cells[0]));
  if(!packet)return 0;
  packet->count=count;count=0U;
  for(size_t i=0U;i<state->base_slot_count;++i) {
    const M68kRenderTypedBaseSlot *slot=&state->base_slots[i];
    if(!slot->known || !slot->storage_id || !slot->scalar_word_mask)continue;
    packet->cells[count].id=slot->storage_id;packet->cells[count].value=slot->scalar_word_value;
    packet->cells[count++].mask=slot->scalar_word_mask;
  }
  *output=packet;return 1;
}

static void scalar_word_note_writes(M68kRenderTypedState *state,const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform,size_t section,const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *meta=m68k_sim_metadata_for_instruction(instruction);
  if(!meta || meta->flow_kind==M68K_SIM_FLOW_CALL || meta->flow_kind==M68K_SIM_FLOW_TRAP || meta->sp_effect_count) {
    typed_state_forget_memory_cells(state);return;
  }
  for(size_t i=0U;i<instruction->operand_count && i<4U;++i) {
    if(platform_operand_memory_access(instruction,i)!=M68K_SIM_ACCESS_MEMORY_WRITE)continue;
    uint8_t span=0U;
    (void)platform_operand_memory_span(instruction,i,NULL,NULL,&span);
    typed_state_note_storage_write(state,lookup,platform,section,instruction,i,span);
  }
}
