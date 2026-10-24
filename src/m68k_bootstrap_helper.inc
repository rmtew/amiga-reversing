/* Reviewed same-size entry references for a retained helper executing inside
 * its owned input. Whole-input identity and materialization are checked by
 * prepare_layout_bootstrap; this never scans constants or edits rendered text. */
static int bootstrap_source_helper_variant(M68kRenderIRPreview *preview,const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section,const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction,uint8_t bytes[4]) {
  const M68kBootstrapContractIR *c=preview->bootstrap_contract;
  if(!preview->bootstrap_source_helper || section->section_index || !c ||
      (candidate->offset!=c->helper_destination_source_offset && candidate->offset!=c->helper_jump_source_offset)) return 0;
#define HELPER_REFUSE(message) do {preview->memory_layout.reason=message;return -1;} while(0)
  int lea=candidate->offset==c->helper_destination_source_offset;
  uint32_t target=0;uint8_t address_register=0,reg=0;
  if(candidate->byte_count!=4 || instruction->mnemonic_id!=(lea ? M68K_ASM_MNEMONIC_LEA : M68K_ASM_MNEMONIC_JMP) ||
      instruction->operand_count!=(lea ? 2 : 1) ||
      !operand_absolute_offset_local(&instruction->operands[0],&target) || target!=c->helper_runtime_address ||
      instruction->operands[0].value.ea_mode!=7 || instruction->operands[0].value.ea_reg!=0 ||
      (lea && (!m68k_instruction_operand_direct_register(&instruction->operands[1],&address_register,&reg) ||
        !address_register || reg!=2))) HELPER_REFUSE("bootstrap_source_helper_entry_shape_refused");
  InstructionSpec spec;uint8_t original[4];
  m68k_instruction_ir_to_spec(instruction,&spec);
  if(m68k_instruction_spec_assemble_bytes(&spec,original,sizeof(original))!=4 ||
      memcmp(original,section->data+candidate->offset,4)) HELPER_REFUSE("bootstrap_source_helper_original_encoding_refused");
  M68kOperandIR *operand=&instruction->operands[0];
  operand->kind=M68K_ASM_OPERAND_EA;operand->value.kind=M68K_ASM_OPERAND_EA;
  operand->value.ea_mode=7;operand->value.ea_reg=2;operand->value.value=0;
  operand->has_exact_render_value=0;operand->manual_representation_style_id=0;
  M68kAsmOperandValue values[4];for(size_t i=0;i<instruction->operand_count;i++) values[i]=instruction->operands[i].value;
  instruction->asm_form_index=m68k_asm_form_index_for_operands_id(instruction->mnemonic_id,values,
      instruction->operand_count,instruction->size_suffix,instruction->target_cpu);
  if(instruction->asm_form_index==M68K_ASM_FORM_NONE) HELPER_REFUSE("bootstrap_source_helper_generated_form_unavailable");
  size_t relative=m68k_asm_operand_relative_base_offset(instruction->asm_form_index,values,instruction->operand_count,
      instruction->size_suffix,0,0);
  int64_t delta=(int64_t)c->helper_source_start-candidate->offset-(int64_t)relative;
  if(relative<2 || relative>=4 || delta<INT16_MIN || delta>INT16_MAX)
    HELPER_REFUSE("bootstrap_source_helper_relative_reach_refused");
  operand->value.value=(int32_t)delta;
  attach_operand_label_symbol(lookup,instruction,0,0,candidate->offset,0,c->helper_source_start);
  m68k_instruction_ir_to_spec(instruction,&spec);
  if(m68k_instruction_spec_assemble_bytes(&spec,bytes,4)!=4 || !memcmp(bytes,original,4))
    HELPER_REFUSE("bootstrap_source_helper_generated_encoding_refused");
  return 1;
#undef HELPER_REFUSE
}
