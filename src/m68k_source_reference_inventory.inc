/* Frozen reference inventory only. Coordinates and operand extents come from
 * the native plan/generated encoder. This JSON does not admit runtime fixups. */
static int append_source_reference_expression(JsonBuilder *b,const PlatformFileListingArtifact *a,
    const M68kRenderPlannedExpression *e) {
    if(json_builder_appendf(b,
        "{\"source_section_index\":%u,\"source_offset\":%u,\"kind\":%u,\"outcome\":%u,"
        "\"operand_index\":%u,\"logical_address\":%u,\"pointer_width\":%u,\"pointer_address_domain\":%u,"
        "\"has_target\":%s,\"target_section_index\":%u,\"target_offset\":%u,"
        "\"has_base_target\":%s,\"base_section_index\":%u,\"base_offset\":%u,\"addend\":%d,\"reason\":",
        e->source_section_index,e->source_offset,e->kind,e->outcome,e->operand_index,e->logical_address,
        e->pointer_width,e->pointer_address_domain,e->has_target ? "true":"false",
        e->target_section_index,e->target_offset,e->has_base_target ? "true":"false",
        e->base_section_index,e->base_offset,e->addend) ||
        json_builder_append_json_string(b,e->reason) || json_builder_append(b,",\"target_symbol\":") ||
        json_builder_append_json_string(b,e->target_symbol)) return -1;
    if(e->kind==M68K_RENDER_PLANNED_EXPRESSION_INSTRUCTION_OPERAND) {
      const M68kRenderPlannedInstruction *ins=m68k_render_plan_find_instruction(&a->source_plan,
          e->source_section_index,e->source_offset);
      if(ins && e->operand_index<ins->instruction.operand_count) {
        InstructionSpec spec;unsigned char encoded[32];uint32_t absolute=0,immediate=0;
        const M68kOperandIR *o=&ins->instruction.operands[e->operand_index];
        M68kOperandIR normalized=*o;
        m68k_instruction_operand_to_asm_value(o,&normalized.value);normalized.kind=normalized.value.kind;
        m68k_instruction_ir_to_spec(&ins->instruction,&spec);
        size_t width=0,offset=0;
        int span_valid=!m68k_asm_operand_extension_span(spec.asm_form_index,spec.operands,
            spec.operand_count,spec.size_suffix,e->operand_index,&offset,&width);
        size_t n=m68k_instruction_spec_assemble_bytes(&spec,encoded,sizeof(encoded));
        int matches=n && n==ins->instruction.byte_count && e->source_section_index<a->object.section_count &&
            e->source_offset<=a->object.sections[e->source_section_index].data_size &&
            n<=a->object.sections[e->source_section_index].data_size-e->source_offset &&
            !memcmp(encoded,a->object.sections[e->source_section_index].data+e->source_offset,n);
        if(json_builder_appendf(b,",\"instruction_field\":{\"instruction_bytes\":%u,\"extension_offset\":%zu,"
            "\"extension_bytes\":%zu,\"extension_span_valid\":%s,\"ea_shape\":%u,\"absolute\":%s,\"immediate\":%s,"
            "\"original_encoder_matches\":%s}",ins->instruction.byte_count,offset,width,
            span_valid ? "true":"false",m68k_instruction_operand_decoded_ea_shape(&normalized),
            m68k_asm_operand_absolute_value(o->kind,&o->value,&absolute) ? "true":"false",
            m68k_ir_operand_immediate_value(o,&immediate) ? "true":"false",matches ? "true":"false")) return -1;
      }
    }
    return json_builder_append(b,"}");
}
