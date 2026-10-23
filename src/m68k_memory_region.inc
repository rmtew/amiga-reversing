#include "m68k_memory_region_proof.inc"
#include "m68k_memory_pointer_liveness.inc"
#include "m68k_memory_region_addresses.inc"
/* Native formal-memory projection. Included after the canonical artifact and
 * JSON codec definitions; it never scans rendered source or invents owners. */
static int memory_region_append_facts(JsonBuilder *b, const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r) {
  size_t i,j,count=0,open=0; const M68kRenderPlan *p=&a->source_plan;
  uint32_t source_section=0,source_offset=0;int mapped=mr_mapped_span(a,r,&source_section,&source_offset);
  if(r->source_mapped && mapped!=1) open++;
  if (json_builder_append(b,"{\"region_id\":") || json_builder_append_json_string(b,r->region_id) ||
      json_builder_append(b,",\"name\":") || json_builder_append_json_string(b,r->name) ||
      json_builder_appendf(b,",\"runtime_address\":%u,\"size\":%u,\"alignment\":%u,"
        "\"source_domain\":\"%s\",\"memory_class\":\"cpu_ram\","
        "\"lifetime\":\"persistent\",\"dma_access\":\"%s\",\"source_placement\":",
        r->runtime_address,r->size,r->alignment,r->source_mapped ? "mapped_source" : "runtime_only",r->dma_access ? "chip" : "none")) return -1;
  if(mapped==1) {
    if(json_builder_appendf(b,"{\"section_index\":%u,\"source_offset\":%u}",source_section,source_offset)) return -1;
  } else if(json_builder_append(b,"null")) return -1;
  if(r->region_kind || r->parent_region_id[0]) {
    static const char *kinds[]={"storage","image","workspace","display"};
    if(json_builder_append(b,",\"region_kind\":") || json_builder_append_json_string(b,kinds[r->region_kind]) ||
        json_builder_append(b,",\"parent_region_id\":") || json_builder_append_json_string(b,r->parent_region_id)) return -1;
  }
  if(json_builder_append(b,",\"overlapping_regions\":[")) return -1;
  size_t overlaps=0;
  for(i=0;i<a->policy.memory_region_count;i++) {
    const M68kMemoryRegionIR *other=&a->policy.memory_regions[i];
    if(other==r || !mr_overlaps(r->runtime_address,r->size,other->runtime_address,other->size)) continue;
    uint32_t start=r->runtime_address>other->runtime_address ? r->runtime_address : other->runtime_address;
    uint32_t end=r->runtime_address+r->size<other->runtime_address+other->size ?
      r->runtime_address+r->size : other->runtime_address+other->size;
    open++;
    if((overlaps++ && json_builder_append(b,",")) || json_builder_append(b,"{\"region_id\":") ||
        json_builder_append_json_string(b,other->region_id) ||
        json_builder_appendf(b,",\"runtime_address\":%u,\"size\":%u,\"region_offset\":%u,"
          "\"other_region_offset\":%u,\"obligation\":\"coordinated_source_placement\"}",
          start,end-start,start-r->runtime_address,start-other->runtime_address)) return -1;
  }
  if(json_builder_append(b,"],\"references\":[")) return -1;
  for(i=0;i<p->instruction_count;i++) {
    const M68kRenderPlannedInstruction *ins=&p->instructions[i];
    const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
    for(j=0;j<ins->instruction.operand_count;j++) {
      const M68kOperandIR *o=&ins->instruction.operands[j]; uint32_t address;
      int kind=mr_operand_address(a,ins,j,&address),absolute=kind==1,immediate=kind==2;
      unsigned width=m ? mr_access_width(&ins->instruction,m,(uint8_t)j) : 0;
      if(kind<0 && address==UINT32_MAX) {if(r->source_mapped) open++;continue;}
      if(!kind || !mr_overlaps(address,width,r->runtime_address,r->size)) continue;
      if(address<r->runtime_address || kind<0 || (kind==3 && m && m->operand_access_kinds[j]==M68K_SIM_ACCESS_COMPUTE_ADDRESS) || kind==4 || immediate || !m || ins->instruction.target_cpu!=M68K_ASM_CPU_68000 || o->kind==M68K_ASM_OPERAND_BF_EA || (m->operand_access_kinds[j]!=M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
          ((m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_READ && m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_WRITE) ||
           !mr_access_width(&ins->instruction,m,(uint8_t)j) || mr_access_width(&ins->instruction,m,(uint8_t)j)>r->size-(address-r->runtime_address)))) open++;
      if(count++ && json_builder_append(b,",")) return -1;
      if(json_builder_appendf(b,"{\"section_index\":%u,\"source_offset\":%u,\"operand_index\":%zu,"
        "\"address\":%u,\"region_offset\":%u,\"width\":%u,\"access_kind\":%u,"
        "\"encoding\":\"%s\",\"obligation\":\"%s\"",ins->source_section_index,ins->source_offset,j,
        address,address-r->runtime_address,m ? mr_access_width(&ins->instruction,m,(uint8_t)j) : 0,
        m ? m->operand_access_kinds[j] : 0,
        kind==3 ? "pc_displacement" : kind==4 ? "pc_index" : immediate ? "immediate" : o->value.ea_mode==7 && o->value.ea_reg==0 ? "absolute_word" : "absolute_long",
        immediate ? "ambiguous_scalar_or_pointer" : m && m->operand_access_kinds[j]==M68K_SIM_ACCESS_COMPUTE_ADDRESS ?
          "derived_pointer_accesses" : "direct_access_bounds")) return -1;
      if(m && m->operand_access_kinds[j]==M68K_SIM_ACCESS_COMPUTE_ADDRESS && absolute) {
        MRProofResult proof=mr_prove_root(a,r,ins,(uint8_t)j);
        if(proof.reason) open++;
        if(json_builder_appendf(b,",\"root_access_proof\":{\"source_offset\":%u,\"access_count\":%u,"
            "\"minimum_offset\":%u,\"maximum_end\":%u,\"states\":%u,\"status\":\"%s\",\"reason\":",
            proof.source_offset,proof.access_count,proof.minimum_offset,proof.maximum_end,proof.states,
            proof.reason ? "refused" : "closed") || (proof.reason ? json_builder_append_json_string(b,proof.reason) : json_builder_append(b,"null")) ||
            json_builder_append(b,"}")) return -1;
        MRFramePrefixResult frame=mr_frame_prefix(a,mr_owner(a,ins->source_offset),ins->source_offset);
        if(json_builder_appendf(b,",\"frame_prefix\":{\"entry_offset\":%u,\"stack_delta\":%d,\"minimum_delta\":%d,"
            "\"maximum_delta\":%d,\"states\":%u,\"paths\":%u,\"failure_offset\":%u,\"absolute_sp\":null,\"status\":\"%s\",\"reason\":",
            frame.entry,frame.delta,frame.minimum_delta,frame.maximum_delta,frame.states,frame.paths,frame.failure_offset,
            frame.reason ? "refused" : "modeled_relative_only") ||
            (frame.reason ? json_builder_append_json_string(b,frame.reason) : json_builder_append(b,"null")) || json_builder_append(b,"}")) return -1;
        MRLivenessResult live=mr_after_leaf_liveness(a,r,ins,(uint8_t)j);
        if(live.applicable) {
          if(json_builder_appendf(b,",\"after_leaf_liveness\":{\"leaf_offset\":%u,\"start_offset\":%u,\"states\":%u,"
              "\"overwrite_count\":%u,\"use_count\":%u,\"barrier_count\":%u,\"truncated\":%s,"
              "\"scope\":\"accepted_ordinary_control_flow_only\",\"relocation_closure\":false,"
              "\"interrupt_observers\":\"unmodeled\",\"frame_integrity\":\"unproved\",\"events\":[",
              live.leaf,live.start,live.states,live.deaths,live.uses,live.barriers,live.truncated ? "true" : "false")) return -1;
          for(unsigned event=0;event<live.event_count;event++) {
            if((event && json_builder_append(b,",")) ||
                json_builder_appendf(b,"{\"source_offset\":%u,\"kind\":",live.events[event].pc) ||
                json_builder_append_json_string(b,live.events[event].kind) || json_builder_append(b,"}")) return -1;
          }
          if(json_builder_append(b,"]}")) return -1;
        }
        if(proof.reason) {
          const M68kRenderPlannedInstruction *failed=mr_instruction(a,proof.source_offset);
          if(failed) {
            M68kRenderPolicy policy;m68k_render_policy_init_default(&policy);
            M68kIrRenderResult text=m68k_ir_render_one_at_with_policy(&failed->render_instruction,proof.source_offset,&policy,m68k_diag_sink(NULL));
            if(json_builder_append(b,",\"failure_instruction\":") || json_builder_append_json_string(b,text.text)) return -1;
          }
        }
      }
      if(json_builder_append(b,"}")) return -1;

    }
  }
  for(i=0;i<a->source_analysis.section_count;i++)
    for(j=0;j<a->source_analysis.sections[i].data_reference_count;j++) {
      uint32_t v=a->source_analysis.sections[i].data_references[j].raw_value;
      if(v>=r->runtime_address && v<r->runtime_address+r->size) open++;
    }
  return json_builder_appendf(b,"],\"reference_count\":%zu,\"unresolved_obligations\":%zu,\"proof_status\":\"%s\","
    "\"unknowns\":[\"Closure covers accepted native references and bounded pointer paths only.\","
    "\"Unclassified bytes, synthesized addresses and future callback changes remain outside this proof.\","
    "\"Absent references do not establish free memory; runtime allocation is required.\"]}",count,open,
    count && !open ? "accepted_references_closed" : "obligations_open");
}

int platform_file_facts_v2_listing_artifact_memory_regions_json_alloc(
    PlatformFileListingArtifact *a, char **out_text) {
  JsonBuilder b={0}; size_t i;
  if (!a || !out_text) return -1;
  *out_text=NULL;
  if(json_builder_create(&b) || json_builder_append(&b,"{\"items\":[")) goto fail;
  for(i=0;i<a->policy.memory_region_count;i++) {
    if((i && json_builder_append(&b,",")) || memory_region_append_facts(&b,a,&a->policy.memory_regions[i])) goto fail;
  }
  if(json_builder_appendf(&b,"],\"total\":%u,\"scope\":\"canonical_native_memory_regions\"}",a->policy.memory_region_count)) goto fail;
  *out_text=json_builder_build(&b); json_builder_destroy(&b); return *out_text ? 0 : -1;
fail: json_builder_destroy(&b); return -1;
}

int platform_file_facts_v2_listing_artifact_memory_layouts_json_alloc(
    PlatformFileListingArtifact *a,char **out_text) {
  JsonBuilder b={0};
  if(!a || !out_text) return -1;
  *out_text=NULL;
  if(json_builder_create(&b) || json_builder_append(&b,"{\"items\":[")) goto failed;
  for(size_t li=0;li<a->policy.memory_layout_count;li++) {
    const M68kMemoryLayoutIR *layout=&a->policy.memory_layouts[li];M68kResolvedMemoryLayout resolved;
    int rc=m68k_memory_layout_resolve(&a->policy,layout,&resolved);
    if((li && json_builder_append(&b,",")) || json_builder_append(&b,"{\"layout_id\":") ||
        json_builder_append_json_string(&b,layout->layout_id) ||
        json_builder_appendf(&b,",\"chip_bytes\":%u,\"status\":\"%s\",\"export_ready\":false,\"reason\":",
          layout->chip_bytes,rc ? "refused" : "placement_valid") ||
        (resolved.reason ? json_builder_append_json_string(&b,resolved.reason) : json_builder_append(&b,"null")) ||
        json_builder_appendf(&b,",\"failed_region_index\":%d,\"regions\":[",resolved.failed_region)) goto failed;
    if(!rc) for(size_t i=0;i<a->policy.memory_region_count;i++) {
      const M68kMemoryRegionIR *r=&a->policy.memory_regions[i];
      static const char *kinds[]={"storage","image","workspace","display"};
      if((i && json_builder_append(&b,",")) || json_builder_append(&b,"{\"region_id\":") ||
          json_builder_append_json_string(&b,r->region_id) || json_builder_append(&b,",\"base_symbol\":") ||
          json_builder_append_json_string(&b,r->name) || json_builder_append(&b,",\"region_kind\":") ||
          json_builder_append_json_string(&b,r->region_kind<=3 ? kinds[r->region_kind] : "unknown") ||
          json_builder_append(&b,",\"parent_region_id\":") || json_builder_append_json_string(&b,r->parent_region_id) ||
          json_builder_appendf(&b,",\"original_address\":%u,\"runtime_address\":%u,\"size\":%u,\"parent_offset\":%u}",
            r->runtime_address,resolved.addresses[i],r->size,resolved.parents[i]>=0 ?
            r->runtime_address-a->policy.memory_regions[resolved.parents[i]].runtime_address : 0)) goto failed;
    }
    if(json_builder_append(&b,"]}")) goto failed;
  }
  if(json_builder_appendf(&b,"],\"total\":%u,\"scope\":\"canonical_fixed_layout_placement_only\"}",a->policy.memory_layout_count)) goto failed;
  *out_text=json_builder_build(&b);json_builder_destroy(&b);return *out_text ? 0 : -1;
failed:json_builder_destroy(&b);return -1;
}

int platform_file_facts_v2_listing_artifact_memory_region_plan_json_alloc(
    PlatformFileListingArtifact *a,const char *id,uint32_t destination,uint32_t memory_class,char **out_text) {
  JsonBuilder b={0}; const M68kMemoryRegionIR *r=NULL; size_t i,j,rewrites=0,open=0;
  const char *refusal=NULL;
  uint32_t source_section=0,source_offset=0,reservation_size=0;
  if(!a || !id || !out_text) return -1;
  *out_text=NULL;
  for(i=0;i<a->policy.memory_region_count;i++) if(!strcmp(a->policy.memory_regions[i].region_id,id)) r=&a->policy.memory_regions[i];
  if(!r) return -1;
  reservation_size=(r->size+7U)&~7U;
  if(r->source_mapped && mr_mapped_span(a,r,&source_section,&source_offset)!=1) refusal="unresolved_source_mapping";
  if(destination % r->alignment || destination % 8U) refusal="reservation_alignment";
  else if(destination==r->runtime_address) refusal="unchanged_placement";
  else if(r->dma_access && memory_class!=1U) refusal="chip_dma_required";
  else if(!((memory_class==1U && reservation_size<=0x7f000U && destination>=0x1000U && destination<=0x80000U-reservation_size) ||
      (memory_class==2U && reservation_size<=0x80000U && destination>=0xc00000U && destination<=0xc80000U-reservation_size))) refusal="outside_supported_a500_memory";
  for(i=0;i<a->policy.memory_region_count;i++) {
    const M68kMemoryRegionIR *other=&a->policy.memory_regions[i];
    if(destination < other->runtime_address+other->size && other->runtime_address < destination+reservation_size) refusal="persistent_region_overlap";
    /* The single-region builder cannot preserve a shared source identity by
     * moving just one owner, even when all its direct references are closed. */
    if(other!=r && mr_overlaps(r->runtime_address,r->size,other->runtime_address,other->size)) open++;
  }
  for(i=0;i<a->policy.target_equate_count;i++) {
    const M68kAnalysisTargetEquate *owner=&a->policy.target_equates[i];
    if(owner->address_domain && owner->extent_bytes &&
        mr_overlaps(destination,reservation_size,(uint32_t)owner->value,owner->extent_bytes))
      refusal="runtime_equate_overlap";
  }
  for(i=0;i<a->source_analysis.section_count;i++) {
    const M68kSectionAnalysisIR *section=&a->source_analysis.sections[i];
    for(j=0;j<section->runtime_view_count;j++) {
      const M68kRuntimeViewIR *view=&section->runtime_views[j];
      if(view->materialized && destination < (uint64_t)view->runtime_address+view->size && view->runtime_address < (uint64_t)destination+reservation_size)
        refusal="runtime_materialization_overlap";
    }
    for(j=0;j<section->data_reference_count;j++) {
      uint32_t value=section->data_references[j].raw_value;
      if(value>=r->runtime_address && value<r->runtime_address+r->size) open++;
      if(value>=destination && value<destination+reservation_size) refusal="existing_destination_data_reference";
    }
  }
  if(json_builder_create(&b) || json_builder_append(&b,"{\"region_id\":") || json_builder_append_json_string(&b,id) ||
      json_builder_appendf(&b,",\"destination\":%u,\"memory_class\":\"%s\",\"reservation\":\"exec_allocabs\","
        "\"reservation_size\":%u,\"rewrite_ledger\":[",destination,memory_class==1U ? "chip" : memory_class==2U ? "slow" : "unsupported",reservation_size)) goto fail;
  for(i=0;i<a->source_plan.instruction_count;i++) {
    const M68kRenderPlannedInstruction *ins=&a->source_plan.instructions[i];
    const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
    M68kInstructionIR changed=ins->instruction; InstructionSpec spec; unsigned char old[32],bytes[32];
    uint32_t region_offset=0,operand_index=0;size_t matched=0,n;
    for(j=0;j<ins->instruction.operand_count;j++) {
      const M68kOperandIR *o=&ins->instruction.operands[j];uint32_t v;
      int kind=mr_operand_address(a,ins,j,&v),immediate=kind==2;
      unsigned width=m ? mr_access_width(&ins->instruction,m,(uint8_t)j) : 0;
      if(!kind) continue;
      if(kind<0 && v==UINT32_MAX) {if(r->source_mapped) open++;continue;}
      if(mr_overlaps(v,width,destination,reservation_size)) refusal="existing_destination_reference";
      if(!mr_overlaps(v,width,r->runtime_address,r->size)) continue;
      ++matched;region_offset=v-r->runtime_address;operand_index=(uint32_t)j;
      if(v<r->runtime_address || kind<0 || (kind==3 && m && m->operand_access_kinds[j]==M68K_SIM_ACCESS_COMPUTE_ADDRESS) || kind==4 || immediate || !m || ins->instruction.target_cpu!=M68K_ASM_CPU_68000 || o->kind==M68K_ASM_OPERAND_BF_EA) { ++open;continue; }
      if(m->operand_access_kinds[j]==M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
        MRProofResult proof=mr_prove_root(a,r,ins,(uint8_t)j);
        if(proof.reason) { ++open;continue; }
      } else
      if(m->operand_access_kinds[j]!=M68K_SIM_ACCESS_COMPUTE_ADDRESS && m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_READ && m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_WRITE) { ++open;continue; }
      if(mr_access_width(&ins->instruction,m,(uint8_t)j)==0 ||
          mr_access_width(&ins->instruction,m,(uint8_t)j)>r->size-region_offset) { ++open;continue; }
      if(o->value.ea_mode==7U && o->value.ea_reg==0U && destination+region_offset>0x7fffU && destination+region_offset<0xffff8000U) { refusal="absolute_word_encoding_overflow";continue; }
      if(kind==3) {
        uint32_t pc;
        if(mr_source_address(a,ins->source_section_index,ins->source_offset,&pc)!=1) { refusal="unresolved_instruction_mapping";continue; }
        InstructionSpec original_spec;m68k_instruction_ir_to_spec(&ins->instruction,&original_spec);
        size_t bias=m68k_asm_operand_relative_base_offset(original_spec.asm_form_index,original_spec.operands,
            original_spec.operand_count,original_spec.size_suffix,j,0);
        if((int64_t)pc+bias+(int32_t)m68k_sign_extend32(o->value.value,16U)!=v) { refusal="pc_reference_identity_mismatch";continue; }
        int64_t delta=(int64_t)destination+region_offset-pc-bias;
        if(delta<INT16_MIN || delta>INT16_MAX) { refusal="pc_displacement_encoding_overflow";continue; }
        changed.operands[j].value.value=(uint32_t)delta;
      } else changed.operands[j].value.value=destination+region_offset;
      memset(&changed.operands[j].symbol_ref,0,sizeof(changed.operands[j].symbol_ref));
    }
    if(!matched) continue;
    if(matched!=1) {open++;continue;}
    if(changed.operands[operand_index].value.value==ins->instruction.operands[operand_index].value.value) continue;
    if(ins->source_section_index!=0 || a->object.section_count!=1) { refusal="unsupported_source_container";continue; }
    m68k_instruction_ir_to_spec(&ins->instruction,&spec);
    n=m68k_instruction_spec_assemble_bytes(&spec,old,sizeof(old));
    if(n!=ins->instruction.byte_count || ins->source_offset>a->object.sections[0].data_size || n>a->object.sections[0].data_size-ins->source_offset ||
        memcmp(old,a->object.sections[0].data+ins->source_offset,n)) { refusal="original_instruction_encoding_mismatch";continue; }
    m68k_instruction_ir_to_spec(&changed,&spec);
    if(m68k_instruction_spec_assemble_bytes(&spec,bytes,sizeof(bytes))!=n) { refusal="instruction_extent_changed";continue; }
    if(rewrites++ && json_builder_append(&b,",")) goto fail;
    if(json_builder_appendf(&b,"{\"section_index\":0,\"source_offset\":%u,\"operand_index\":%u,\"region_offset\":%u,\"before\":\"",ins->source_offset,operand_index,region_offset)) goto fail;
    for(j=0;j<n;j++) if(json_builder_appendf(&b,"%02x",old[j])) goto fail;
    if(json_builder_append(&b,"\",\"after\":\"")) goto fail;
    for(j=0;j<n;j++) if(json_builder_appendf(&b,"%02x",bytes[j])) goto fail;
    if(json_builder_append(&b,"\"}")) goto fail;
  }
  if(json_builder_append(&b,"],\"initialization\":")) goto fail;
  if(r->source_mapped && !refusal) {
    if(json_builder_appendf(&b,"{\"section_index\":%u,\"source_offset\":%u,\"bytes\":\"",source_section,source_offset)) goto fail;
    for(i=0;i<r->size;i++) if(json_builder_appendf(&b,"%02x",a->object.sections[source_section].data[source_offset+i])) goto fail;
    if(json_builder_append(&b,"\"}")) goto fail;
  } else if(json_builder_append(&b,"null")) goto fail;
  if(!refusal) for(i=0;i<a->policy.memory_region_count;i++) {
    const M68kMemoryRegionIR *other=&a->policy.memory_regions[i];
    if(other!=r && mr_overlaps(r->runtime_address,r->size,other->runtime_address,other->size)) {
      refusal="overlapping_source_regions";break;
    }
  }
  if(open && !refusal) refusal="unresolved_reference_or_access_closure";
  if(!rewrites && !refusal) refusal="no_supported_references";
  if(json_builder_appendf(&b,",\"rewrite_count\":%zu,\"unresolved_obligations\":%zu,\"status\":\"%s\",\"refusal\":",rewrites,open,refusal ? "refused" : "ready") ||
      (refusal ? json_builder_append_json_string(&b,refusal) : json_builder_append(&b,"null")) ||
      json_builder_append(&b,",\"scope\":\"accepted native references and bounded pointer paths only; fixed instruction extents; original code placement\","
        "\"runtime_evidence\":null,\"scenario_coverage\":null}")) goto fail;
  *out_text=json_builder_build(&b);json_builder_destroy(&b);return *out_text ? 0 : -1;
fail:json_builder_destroy(&b);return -1;
}
