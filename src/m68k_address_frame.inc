/* Bounded annotated address-form changes, never numeric scanning or source-text
 * patches. The canonical review owns the entry-register precondition. */
typedef struct AddressFrameBinding {
  uint32_t section,offset;
  uint16_t region,site;
} AddressFrameBinding;
static int address_frame_order(const void *aa,const void *bb) {
  const AddressFrameBinding *a=aa,*b=bb;
  if(a->section!=b->section) return a->section<b->section ? -1 : 1;
  return a->offset<b->offset ? -1 : a->offset>b->offset ? 1 : 0;
}
static int address_frame_bindings(const M68kAnalysisPolicy *p,const M68kDecodeIR *decode,
    AddressFrameBinding *out,size_t *count) {
  *count=0;if(!p) return 1;
  for(size_t r=0;r<p->memory_region_count;r++) {
    if(p->memory_regions[r].address_frame_site_count) {
      char digest[65];
      if(!decode->section_count || m68k_platform_sha256_hex(decode->sections[0].data,decode->sections[0].size,digest) ||
          strcmp(digest,p->memory_regions[r].address_frame_input_sha256)) return 0;
    }
    for(size_t s=0;s<p->memory_regions[r].address_frame_site_count;s++) {
    const M68kAddressFrameSiteIR *site=&p->memory_regions[r].address_frame_sites[s];
    out[(*count)++]=(AddressFrameBinding){site->section_index,site->source_offset,(uint16_t)r,(uint16_t)s};
    }
  }
  qsort(out,*count,sizeof(*out),address_frame_order);
  for(size_t i=1;i<*count;i++) if(!address_frame_order(&out[i-1],&out[i])) return 0;
  return 1;
}
static int apply_address_frame(M68kRenderIRPreview *preview,const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate,const AddressFrameBinding *bindings,size_t count,
    M68kRenderPlannedInstruction *planned) {
  AddressFrameBinding key={(uint32_t)section->section_index,candidate->offset,0,0};
  const AddressFrameBinding *binding=bsearch(&key,bindings,count,sizeof(*bindings),address_frame_order);
  if(!binding) return 1;
#define FRAME_REFUSE(message) do {preview->memory_layout.reason=(message);return 0;} while(0)
  const M68kMemoryRegionIR *r=&preview->analysis_policy->memory_regions[binding->region];
  const M68kAddressFrameSiteIR *site=&r->address_frame_sites[binding->site];
  const M68kInstructionIR *original=&planned->instruction;
  uint32_t value,address;InstructionSpec spec;unsigned char encoded[32];
  if(candidate->byte_count!=8 || original->byte_count!=8 || original->operand_count!=2 ||
      original->mnemonic_id!=M68K_ASM_MNEMONIC_MOVE || original->size_suffix!='l' || site->operand_index!=1 ||
      !m68k_ir_operand_immediate_value(&original->operands[0],&value) ||
      m68k_instruction_operand_decoded_ea_shape(&original->operands[1])!=M68K_SIM_EA_SHAPE_ABSOLUTE_WORD ||
      !operand_absolute_offset_local(&original->operands[1],&address) ||
      candidate->offset>section->size || section->size-candidate->offset<8 ||
      memcmp(section->data+candidate->offset,site->expected_bytes,8))
    FRAME_REFUSE("address_frame_original_instruction_identity_or_form_refused");
  m68k_instruction_ir_to_spec(original,&spec);
  if(m68k_instruction_spec_assemble_bytes(&spec,encoded,sizeof(encoded))!=8 ||
      memcmp(encoded,site->expected_bytes,8)) FRAME_REFUSE("address_frame_original_encoding_refused");
  if(address<r->runtime_address || address-r->runtime_address>0x7fff ||
      address-r->runtime_address>=r->size || r->size-(address-r->runtime_address)<4)
    FRAME_REFUSE("address_frame_owner_or_displacement_refused");
  int typed=0;
  for(size_t qi=0;qi<preview->analysis_policy->target_equate_count;qi++) {
    const M68kAnalysisTargetEquate *q=&preview->analysis_policy->target_equates[qi];
    if(q->address_domain && (uint32_t)q->value==address && q->extent_bytes>=4 &&
        original->operands[1].symbol_ref.has_name &&
        !strcmp(q->name,original->operands[1].symbol_ref.name)) typed=1;
  }
  if(!typed) FRAME_REFUSE("address_frame_requires_explicit_runtime_symbol");
  planned->address_frame_region_index_plus_one=(uint16_t)(binding->region+1);
  planned->address_frame_operand_index=1;
  planned->address_frame_displacement=address-r->runtime_address;
  if(!preview->memory_layout_enabled || preview->memory_layout.addresses[binding->region]==r->runtime_address) return 1;
  M68kInstructionIR changed=planned->render_instruction;
  M68kOperandIR *dest=&changed.operands[1];
  dest->kind=M68K_ASM_OPERAND_EA;dest->value.kind=M68K_ASM_OPERAND_EA;
  dest->value.ea_mode=5;dest->value.ea_reg=r->address_frame_register;
  dest->value.value=planned->address_frame_displacement;
  dest->has_exact_render_value=0;dest->manual_representation_style_id=0;
  dest->symbol_ref=original->operands[1].symbol_ref;
  dest->symbol_ref.has_symbolic_addend=1;
  dest->symbol_ref.symbolic_addend_value=-(int32_t)r->runtime_address;
  snprintf(dest->symbol_ref.symbolic_addend_name,sizeof(dest->symbol_ref.symbolic_addend_name),"%s",r->name);
  M68kAsmOperandValue operands[4];for(size_t i=0;i<changed.operand_count;i++) operands[i]=changed.operands[i].value;
  changed.asm_form_index=m68k_asm_form_index_for_operands_id(changed.mnemonic_id,operands,
      changed.operand_count,changed.size_suffix,changed.target_cpu);
  if(changed.asm_form_index==M68K_ASM_FORM_NONE) FRAME_REFUSE("address_frame_generated_form_unavailable");
  m68k_instruction_ir_to_spec(&changed,&spec);
  if(m68k_instruction_spec_assemble_bytes(&spec,encoded,sizeof(encoded))!=8 ||
      memcmp(encoded+2,site->expected_bytes+2,4)) FRAME_REFUSE("address_frame_size_or_source_encoding_changed");
  /* Retain the canonical cell's symbol access: CELL-owner is an offset. Its
   * expected source reference must not disappear behind a replacement alias.
   * Opcode and extension above are generated; no target opcode constants. */
  planned->render_instruction=changed;planned->address_frame_active=1;
  return 1;
#undef FRAME_REFUSE
}
